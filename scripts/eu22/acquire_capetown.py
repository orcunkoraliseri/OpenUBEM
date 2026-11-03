from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests  # noqa: E402
from openubem.acquisition.footprint_schema import finalize_footprints  # noqa: E402
from scripts.eu22.acquire_yerevan import ROAD_CLASSES, choose_blocks, street_blocks  # noqa: E402,F401

SITE = "ZA-CPT-WOODSTOCK"
SOURCE = "CPT_LIDAR_2023"
EXPECTED_CRS = "EPSG:32734"
SRC_WGS = "EPSG:4326"
SERVICE = "https://citymaps.capetown.gov.za/agsext/rest/services/Theme_Based"
FOOTPRINT_LAYER_NAME = "2D Building Footprints Low Detail"
SUBURB_LAYER_NAME = "Official Suburb"
HERITAGE_LAYER_NAMES = ("Heritage Inventory Objects", "Heritage Inventory", "Heritage Audit Areas")
OVERPASS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter")
OSM_GRID = 6
USER_AGENT = "OpenUBEM-research/1.0 (orcunkoral.oseri@concordia.ca)"
PAGE_SIZE = 2000
NAMED_SUBURBS = ("WOODSTOCK", "SALT RIVER", "OBSERVATORY")
MIN_HEIGHT_M = 2.0
STOREY_M = 3.0
LOW, HIGH = 500, 1000
SURVEY_YEAR = 2010
DISTRICT_NAME = "WOODSTOCK"
ROAD_BUFFER_M = 400.0
ROAD_GRID = 3
RES_BUILDING_TAGS = ("house", "terrace", "apartments", "residential", "semidetached_house", "detached")
GENERIC_BUILDING_TAGS = ("yes", "")
OTHER_USE_KEYS = (
    "amenity", "shop", "office", "tourism", "leisure", "industrial", "craft", "man_made", "healthcare",
    "military", "emergency", "public_transport", "railway", "power", "historic",
)
CROSSWALK = {"residential": "residential", "non_residential": "non_residential", "unknown": "unknown"}
EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-22" / SITE
EU02 = ROOT / "openubem" / "outputs" / "eu02" / SITE
RAW = EVIDENCE / "raw"
LICENCES = EVIDENCE / "licences"
RAW_FOOT = RAW / "cct_footprints"
RAW_SUB = RAW / "cct_suburbs"
RAW_HER = RAW / "cct_heritage"
RAW_OSM = RAW / "osm"
RAW_HIGHWAYS = RAW / "osm_highways"


def storeys_from_height(height) -> float:
    if height is None or pd.isna(height):
        return np.nan
    return float(max(1, int(round(float(height) / STOREY_M))))


PERIOD_PARTS = {"early": (0, 32), "mid": (33, 66), "late": (67, 99), "early-mid": (0, 66)}
LABEL_RE = re.compile(
    r"^(?:(?P<part>early-mid|early|mid|late)\s+)?(?P<a>\d+)(?:st|nd|rd|th)(?:\s*-\s*(?P<b>\d+)(?:st|nd|rd|th))?\s+century$"
)


def label_year(label, survey_year: int = SURVEY_YEAR) -> int | None:
    text = re.sub(r"\bC\b", "Century", re.sub(r"\s+", " ", _clean(label)), flags=re.IGNORECASE).lower()
    m = LABEL_RE.match(text)
    if not m:
        return None
    first = (int(m.group("a")) - 1) * 100
    if m.group("b"):
        if m.group("part"):
            return None
        start, end = first, (int(m.group("b")) - 1) * 100 + 99
    elif m.group("part"):
        lo, hi = PERIOD_PARTS[m.group("part")]
        start, end = first + lo, first + hi
    else:
        return None
    if start > survey_year:
        return None
    return (start + end) // 2


def paginate(fetch_page, page_size: int = PAGE_SIZE, max_pages: int = 10000) -> list[dict]:
    pages = []
    offset = 0
    for _ in range(max_pages):
        page = fetch_page(offset, page_size)
        pages.append(page)
        n = len(page.get("features", []))
        if n < page_size and not page.get("exceededTransferLimit", False):
            return pages
        if n == 0:
            return pages
        offset += n
    raise RuntimeError("pagination did not terminate")


def _get(url: str, params: dict | None = None, *, timeout: int = 400, data: bytes | None = None) -> bytes:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as exc:
            last = exc
            sys.stderr.write(f"request failed ({attempt + 1}/4) {url[:120]}: {type(exc).__name__}: {exc}\n")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"giving up on {url[:160]}: {last}")


def find_layer(layer_name: str) -> tuple[str, int]:
    root = json.loads(_get(f"{SERVICE}?f=json"))
    names = sorted(s["name"] for s in root["services"] if s["type"] == "MapServer" and "ODP_SPLIT" in s["name"])
    hits = []
    for svc in names:
        meta = json.loads(_get(f"{SERVICE.rsplit('/Theme_Based', 1)[0]}/{svc}/MapServer?f=json"))
        for lyr in meta.get("layers", []):
            if lyr["name"] == layer_name:
                hits.append((svc, lyr["id"]))
    if not hits:
        raise ValueError(f"layer {layer_name!r} not found")
    return hits[0]


def layer_url(layer_name: str) -> str:
    svc, lid = find_layer(layer_name)
    return f"{SERVICE.rsplit('/Theme_Based', 1)[0]}/{svc}/MapServer/{lid}"


def _query(url: str, where: str, bbox, offset: int, count: int) -> dict:
    params = {
        "where": where, "outFields": "*", "returnGeometry": "true", "f": "geojson",
        "orderByFields": "OBJECTID", "returnZ": "false", "outSR": "4326", "resultOffset": offset, "resultRecordCount": count,
    }
    if bbox is not None:
        params.update({
            "geometry": ",".join(f"{v:.6f}" for v in bbox), "geometryType": "esriGeometryEnvelope",
            "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
        })
    return json.loads(_get(url + "/query", params))


def _save_pages(pages: list[dict], folder: Path, stem: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(pages):
        (folder / f"{stem}_{i:04d}.geojson").write_text(json.dumps(page), encoding="utf-8")


def read_pages(folder: Path, stem: str) -> gpd.GeoDataFrame:
    files = sorted(folder.glob(f"{stem}_*.geojson"))
    frames = [gpd.read_file(f) for f in files]
    frames = [f for f in frames if len(f)]
    if not frames:
        return gpd.GeoDataFrame(geometry=[], crs=SRC_WGS)
    out = pd.concat(frames, ignore_index=True)
    return gpd.GeoDataFrame(out, geometry="geometry", crs=SRC_WGS)


def study_bbox(suburbs: gpd.GeoDataFrame, names=NAMED_SUBURBS, buffer_m: float = 150.0) -> tuple[float, float, float, float]:
    utm = suburbs.to_crs(EXPECTED_CRS)
    named = utm[utm["OFC_SBRB_NAME"].isin(names)]
    if len(named) != len(names):
        raise ValueError(f"suburbs found: {sorted(named['OFC_SBRB_NAME'])}")
    box = gpd.GeoSeries([named.union_all().buffer(buffer_m)], crs=EXPECTED_CRS).to_crs(SRC_WGS).total_bounds
    return tuple(float(v) for v in box)


def overpass_query(bbox) -> str:
    s, w, n, e = bbox[1], bbox[0], bbox[3], bbox[2]
    box = f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}"
    return (
        "[out:xml][timeout:180];("
        f'way["building"]({box});relation["building"]({box});'
        f'way["landuse"="residential"]({box});relation["landuse"="residential"]({box});'
        ");(._;>;);out;"
    )


def osm_tiles(bbox, n: int = OSM_GRID) -> list[tuple[float, float, float, float]]:
    xs = np.linspace(bbox[0], bbox[2], n + 1)
    ys = np.linspace(bbox[1], bbox[3], n + 1)
    return [(float(xs[i]), float(ys[j]), float(xs[i + 1]), float(ys[j + 1])) for j in range(n) for i in range(n)]


def download_osm() -> dict:
    RAW_OSM.mkdir(parents=True, exist_ok=True)
    suburbs = read_pages(RAW_SUB, "suburb_page")
    bbox = study_bbox(suburbs)
    log = {"bbox_wgs84": bbox, "tiles": []}
    for k, tile in enumerate(osm_tiles(bbox)):
        target = RAW_OSM / f"overpass_t6_{k:02d}.osm"
        if target.exists() and target.stat().st_size > 0:
            continue
        query = overpass_query(tile)
        (RAW_OSM / f"overpass_t6_{k:02d}_query.txt").write_text(query, encoding="utf-8")
        body = None
        for endpoint in OVERPASS:
            try:
                body = _get(endpoint, timeout=900, data=urllib.parse.urlencode({"data": query}).encode())
                log["tiles"].append({"tile": k, "endpoint": endpoint, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
                break
            except RuntimeError as exc:
                sys.stderr.write(f"tile {k} failed on {endpoint}: {exc}\n")
        if body is None:
            raise RuntimeError(f"tile {k} failed on every endpoint")
        target.write_bytes(body)
    (EVIDENCE / "download_osm_log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    return log


def district_geometry(suburbs: gpd.GeoDataFrame, name: str = DISTRICT_NAME):
    utm = suburbs.to_crs(EXPECTED_CRS)
    hit = utm[utm["OFC_SBRB_NAME"] == name]
    if hit.empty:
        raise ValueError(f"suburb {name!r} not found")
    return hit.union_all()


def highway_query(bbox) -> str:
    s, w, n, e = bbox[1], bbox[0], bbox[3], bbox[2]
    return f'[out:json][timeout:180];way["highway"~"^({ROAD_CLASSES})$"]({s:.6f},{w:.6f},{n:.6f},{e:.6f});out geom;'


def download_highways() -> dict:
    RAW_HIGHWAYS.mkdir(parents=True, exist_ok=True)
    suburbs = read_pages(RAW_SUB, "suburb_page")
    area = gpd.GeoSeries([district_geometry(suburbs).buffer(ROAD_BUFFER_M)], crs=EXPECTED_CRS).to_crs(SRC_WGS)
    bbox = tuple(float(v) for v in area.total_bounds)
    log = {"bbox_wgs84": bbox, "road_classes": ROAD_CLASSES, "tiles": []}
    for k, tile in enumerate(osm_tiles(bbox, ROAD_GRID)):
        target = RAW_HIGHWAYS / f"highways_t{ROAD_GRID}_{k:02d}.json"
        query = highway_query(tile)
        (RAW_HIGHWAYS / f"highways_t{ROAD_GRID}_{k:02d}_query.txt").write_text(query, encoding="utf-8")
        if target.exists() and target.stat().st_size > 0:
            continue
        body = None
        for endpoint in OVERPASS:
            try:
                body = _get(endpoint, timeout=900, data=urllib.parse.urlencode({"data": query}).encode())
                if not body.lstrip().startswith(b"{"):
                    raise RuntimeError(body[:200].decode("utf-8", "replace"))
                log["tiles"].append({"tile": k, "endpoint": endpoint, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
                break
            except RuntimeError as exc:
                body = None
                sys.stderr.write(f"highway tile {k} failed on {endpoint}: {exc}\n")
        if body is None:
            raise RuntimeError(f"highway tile {k} failed on every endpoint")
        target.write_bytes(body)
    (RAW_HIGHWAYS / "download_log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    return log


def read_highways(folder: Path = RAW_HIGHWAYS) -> gpd.GeoDataFrame:
    from shapely.geometry import LineString

    seen, lines = set(), []
    for f in sorted(Path(folder).glob("highways_t*_[0-9][0-9].json")):
        for el in json.loads(f.read_text(encoding="utf-8")).get("elements", []):
            if el.get("type") != "way" or el["id"] in seen or len(el.get("geometry") or []) < 2:
                continue
            seen.add(el["id"])
            lines.append(LineString([(p["lon"], p["lat"]) for p in el["geometry"]]))
    if not lines:
        raise FileNotFoundError(f"no highway ways in {folder}")
    return gpd.GeoDataFrame(geometry=lines, crs=SRC_WGS).to_crs(EXPECTED_CRS)


def download() -> dict:
    for d in (RAW_FOOT, RAW_SUB, RAW_HER, RAW_OSM, LICENCES):
        d.mkdir(parents=True, exist_ok=True)
    log = {}
    sub_url = layer_url(SUBURB_LAYER_NAME)
    sub_pages = paginate(lambda o, c: _query(sub_url, "1=1", None, o, c))
    _save_pages(sub_pages, RAW_SUB, "suburb_page")
    suburbs = read_pages(RAW_SUB, "suburb_page")
    bbox = study_bbox(suburbs)
    log["bbox_wgs84"] = bbox
    foot_url = layer_url(FOOTPRINT_LAYER_NAME)
    log["footprint_layer"] = foot_url
    foot_pages = paginate(lambda o, c: _query(foot_url, "1=1", bbox, o, c))
    _save_pages(foot_pages, RAW_FOOT, "footprints_page")
    log["footprint_pages"] = len(foot_pages)
    log["footprint_features"] = int(sum(len(p["features"]) for p in foot_pages))
    for name in HERITAGE_LAYER_NAMES:
        url = layer_url(name)
        pages = paginate(lambda o, c, u=url: _query(u, "1=1", bbox, o, c))
        _save_pages(pages, RAW_HER, re.sub(r"\W+", "_", name.lower()))
        log[f"heritage_{name}"] = int(sum(len(p["features"]) for p in pages))
    (EVIDENCE / "download_log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    return log


def footprint_frame(raw: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    missing = {"OBJECTID", "BLD_HGHT", "DATA_SRC", "ACQS_PRD", "ACQS_MTHD"} - set(raw.columns)
    if missing:
        raise ValueError(f"footprint layer misses fields: {sorted(missing)}")
    n_raw = len(raw)
    raw = raw.drop_duplicates(subset="OBJECTID").to_crs(EXPECTED_CRS).reset_index(drop=True)
    height = pd.to_numeric(raw["BLD_HGHT"], errors="coerce")
    shed = height < MIN_HEIGHT_M
    rep = {
        "features_downloaded": int(n_raw),
        "features_unique_objectid": int(len(raw)),
        "dropped_height_under_2m": int(shed.sum()),
        "height_missing": int(height.isna().sum()),
    }
    raw = raw.loc[~shed].reset_index(drop=True)
    height = height.loc[~shed].reset_index(drop=True)
    out = gpd.GeoDataFrame(geometry=raw.geometry, crs=raw.crs)
    out["osm_id"] = raw["OBJECTID"].map(lambda v: f"ZA-CPT-{int(v)}")
    out["building_tag"] = ""
    out["function_tag"] = ""
    out["levels"] = pd.array([storeys_from_height(h) for h in height], dtype="float64").astype("Int64")
    out["height_m"] = height.astype("float64").values
    out["year_built"] = pd.array([pd.NA] * len(out), dtype="Int64")
    out["postcode"] = None
    out["underground"] = pd.array([0] * len(out), dtype="Int64")
    out["roof_shape"] = ""
    out["roof_height_m"] = np.nan
    out["surplus_tags"] = [
        json.dumps({"DATA_SRC": str(a), "ACQS_PRD": str(b), "ACQS_MTHD": str(c)}) for a, b, c in zip(raw["DATA_SRC"], raw["ACQS_PRD"], raw["ACQS_MTHD"])
    ]
    return out, rep


def load_osm(folder: Path) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    import osmnx as ox

    frames = []
    for f in sorted(Path(folder).glob("overpass_t6_*.osm")):
        try:
            g = ox.features.features_from_xml(str(f), tags={"building": True, "landuse": "residential"})
        except ox._errors.InsufficientResponseError:
            continue
        frames.append(g.reset_index())
    if not frames:
        raise FileNotFoundError(f"no overpass tiles in {folder}")
    feats = pd.concat(frames, ignore_index=True)
    feats = feats.drop_duplicates(subset=["element_type", "osmid"])
    feats = gpd.GeoDataFrame(feats, geometry="geometry", crs=SRC_WGS)
    feats = feats[feats.geometry.type.isin(["Polygon", "MultiPolygon"])].to_crs(EXPECTED_CRS).reset_index(drop=True)
    for col in ("building", "landuse", "start_date") + OTHER_USE_KEYS:
        if col not in feats.columns:
            feats[col] = None
    buildings = feats[feats["building"].notna()].reset_index(drop=True)
    landuse = feats[(feats["landuse"] == "residential") & feats["building"].isna()].reset_index(drop=True)
    return buildings, landuse


def _clean(value) -> str:
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value).strip()


def match_osm(fp: gpd.GeoDataFrame, osm_b: gpd.GeoDataFrame, min_cover: float = 0.5) -> pd.Series:
    idx = pd.Series(-1, index=fp.index, dtype="int64")
    if osm_b.empty:
        return idx
    tree = osm_b.sindex
    geoms = osm_b.geometry.values
    for i, g in zip(fp.index, fp.geometry.values):
        best, best_a = -1, 0.0
        for h in tree.query(g, predicate="intersects"):
            a = g.intersection(geoms[h]).area
            if a > best_a:
                best, best_a = int(h), a
        if best >= 0 and best_a >= min_cover * g.area:
            idx.at[i] = best
    return idx


def classify_use(fp: gpd.GeoDataFrame, osm_b: gpd.GeoDataFrame, landuse: gpd.GeoDataFrame) -> pd.DataFrame:
    match = match_osm(fp, osm_b)
    pts = fp.geometry.representative_point()
    in_res = pd.Series(False, index=fp.index)
    if len(landuse):
        zone = landuse.union_all()
        in_res = pts.within(zone)
    rows = []
    for i in fp.index:
        m = int(match.at[i])
        tag = _clean(osm_b.at[m, "building"]) if m >= 0 else ""
        other = m >= 0 and any(_clean(osm_b.at[m, k]) for k in OTHER_USE_KEYS)
        if tag in RES_BUILDING_TAGS:
            cls, route = "residential", "osm_residential_tag"
        elif tag in GENERIC_BUILDING_TAGS and not other and bool(in_res.at[i]):
            cls, route = "residential", "landuse_residential_untagged"
        elif m >= 0 and (tag not in GENERIC_BUILDING_TAGS or other):
            cls, route = "non_residential", "osm_other_use"
        else:
            cls, route = "non_residential", "no_residential_evidence"
        rows.append({"use_class": cls, "route": route, "osm_building": tag, "osm_index": m,
                     "start_date": _clean(osm_b.at[m, "start_date"]) if m >= 0 else ""})
    return pd.DataFrame(rows, index=fp.index)


def build_clean_buildings(raw: gpd.GeoDataFrame, osm_b: gpd.GeoDataFrame, landuse: gpd.GeoDataFrame, output_dir=None):
    mapped, rep = footprint_frame(raw)
    use = classify_use(mapped, osm_b, landuse)
    mapped["building_tag"] = [t if (t in RES_BUILDING_TAGS and c == "residential") else "" for t, c in zip(use["osm_building"], use["use_class"])]
    mapped["function_tag"] = use["route"].values
    clean = finalize_footprints(mapped, source=SOURCE, output_dir=output_dir)
    meta = use.set_index(mapped["osm_id"])
    clean = clean.copy()
    clean["use_class"] = meta["use_class"].reindex(clean["osm_id"]).values
    clean["route"] = meta["route"].reindex(clean["osm_id"]).values
    clean["osm_start_date"] = meta["start_date"].reindex(clean["osm_id"]).values
    clean["provenance_levels"] = np.where(clean["levels"].notna(), f"{SOURCE}_HEIGHT_DERIVED", f"{SOURCE}_MISSING")
    rep["kept_after_shared_cleaner"] = int(len(clean))
    rep["dropped_by_shared_cleaner"] = int(rep["features_unique_objectid"] - rep["dropped_height_under_2m"] - len(clean))
    return clean, rep


def choose_subunits(suburbs: gpd.GeoDataFrame, residential: gpd.GeoDataFrame, names=NAMED_SUBURBS, *, low: int = LOW, high: int = HIGH) -> dict:
    sub = suburbs.to_crs(residential.crs)
    sub = sub[sub["OFC_SBRB_NAME"].isin(names)].copy()
    points = residential.geometry.representative_point()
    sub["n_res"] = [int(points.within(g).sum()) for g in sub.geometry]
    sub["area_km2"] = sub.geometry.area / 1e6
    sub["density"] = sub["n_res"] / sub["area_km2"]
    cand = sub[sub["n_res"] > 0].sort_values("density", ascending=False).reset_index(drop=True)
    ranking = [
        {"suburb": r.OFC_SBRB_NAME, "residential": int(r.n_res), "area_km2": round(float(r.area_km2), 4), "per_km2": round(float(r.density), 1)}
        for r in cand.itertuples()
    ]
    first = cand.iloc[0]
    chosen, total, steps, skipped = [first.OFC_SBRB_NAME], int(first.n_res), [], []
    union = first.geometry
    out = {"ranking": ranking, "named_total": int(sub["n_res"].sum())}
    if total > high:
        out.update({"chosen": chosen, "total": total, "status": "FIRST_SUBURB_OVER_CAP", "boundary_geom": union})
        return out
    while total < low:
        rest = cand[~cand["OFC_SBRB_NAME"].isin(chosen + skipped)]
        near = rest[rest.geometry.apply(lambda g: g.intersects(union.buffer(1.0)))].copy()
        if near.empty:
            out.update({"chosen": chosen, "total": total, "status": "NO_TOUCHING_SUBURB_LEFT", "boundary_geom": union})
            return out
        near["dist"] = near.geometry.centroid.distance(first.geometry.centroid)
        pick = near.sort_values("dist").iloc[0]
        if total + int(pick.n_res) > high:
            skipped.append(pick.OFC_SBRB_NAME)
            continue
        chosen.append(pick.OFC_SBRB_NAME)
        total += int(pick.n_res)
        union = union.union(pick.geometry)
        steps.append({"added": pick.OFC_SBRB_NAME, "residential": int(pick.n_res), "running_total": total})
    out.update({"chosen": chosen, "total": total, "status": "OK", "expansion_steps": steps, "skipped_over_cap": skipped, "boundary_geom": union})
    return out


def parse_start_year(value) -> float:
    m = re.match(r"^\s*(\d{4})", _clean(value))
    if not m:
        return np.nan
    year = int(m.group(1))
    return float(year) if 1600 <= year <= 2026 else np.nan


def heritage_site(buildings: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame, prefix: str = "HERITAGE:") -> pd.DataFrame:
    out = pd.DataFrame({"site": "", "label": ""}, index=buildings.index)
    if polygons.empty:
        return out
    polys = polygons.to_crs(buildings.crs)
    polys = polys[polys["PRD"].notna() & (polys["PRD"].astype(str).str.strip() != "")].copy()
    polys["_a"] = polys.geometry.area
    polys = polys.sort_values("_a").reset_index(drop=True)
    tree = polys.sindex
    for i, pt in zip(buildings.index, buildings.geometry.representative_point()):
        hits = tree.query(pt, predicate="within")
        if len(hits):
            row = polys.iloc[int(sorted(hits)[0])]
            out.at[i, "site"] = f"{prefix}{int(row['OBJECTID'])}"
            out.at[i, "label"] = str(row["PRD"]).strip()
    return out


def heritage_period(buildings: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame) -> pd.Series:
    return heritage_site(buildings, polygons)["label"].astype(object)


def own_heritage(buildings: gpd.GeoDataFrame, inventory: gpd.GeoDataFrame, objects: gpd.GeoDataFrame) -> pd.DataFrame:
    a = heritage_site(buildings, inventory)
    b = heritage_site(buildings, objects, prefix="HERITAGE:OBJ")
    miss = a["site"] == ""
    a.loc[miss] = b.loc[miss]
    return a


def street_block_ids(buildings: gpd.GeoDataFrame, blocks: gpd.GeoDataFrame) -> pd.Series:
    pts = gpd.GeoDataFrame(geometry=buildings.geometry.representative_point(), index=buildings.index, crs=buildings.crs)
    joined = gpd.sjoin(pts, blocks[["block_id", "geometry"]].to_crs(buildings.crs), predicate="within", how="left")
    joined = joined[~joined.index.duplicated(keep="first")]
    return joined["block_id"].reindex(buildings.index)


def attach_census(frame: gpd.GeoDataFrame, own: pd.DataFrame, block_id: pd.Series, count_mask: pd.Series) -> gpd.GeoDataFrame:
    block_counts: dict[str, dict[str, int]] = {}
    for i in frame.index[count_mask.reindex(frame.index).fillna(False).astype(bool)]:
        label, block = own.at[i, "label"], block_id.at[i]
        if label != "" and pd.notna(block):
            bucket = block_counts.setdefault(str(block), {})
            bucket[label] = bucket.get(label, 0) + 1
    ids, payloads = [], []
    for i in frame.index:
        label, block = own.at[i, "label"], block_id.at[i]
        if label != "":
            ids.append(own.at[i, "site"])
            payloads.append(json.dumps({label: 1}, ensure_ascii=False))
        elif pd.notna(block):
            ids.append(f"BLOCK:{block}")
            payloads.append(json.dumps(block_counts.get(str(block), {}), ensure_ascii=False, sort_keys=True))
        else:
            ids.append("")
            payloads.append("")
    out = frame.copy()
    out["census_unit_id"] = ids
    out["census_period_counts"] = payloads
    out["heritage_period"] = own["label"].reindex(frame.index).values
    return out


def period_years_for(frame: pd.DataFrame, survey_year: int = SURVEY_YEAR) -> tuple[dict[str, int], list[str]]:
    labels = set()
    for payload in frame["census_period_counts"]:
        if payload:
            labels.update(json.loads(payload))
    years = {label: label_year(label, survey_year) for label in sorted(labels)}
    return {k: v for k, v in years.items() if v is not None}, sorted(k for k, v in years.items() if v is None)


def year_split(frame: pd.DataFrame, period_years: dict[str, int]) -> dict:
    from openubem.semantic.new_country_rules import dominant_period

    n = len(frame)
    out = {"n": int(n), "own_label": 0, "own_label_without_year": 0, "block_label": 0, "none": 0, "none_reasons": {}}
    for uid, payload in zip(frame["census_unit_id"], frame["census_period_counts"]):
        if uid.startswith("HERITAGE:"):
            label = next(iter(json.loads(payload)))
            if label in period_years:
                out["own_label"] += 1
                continue
            out["own_label_without_year"] += 1
            out["none"] += 1
            out["none_reasons"]["OWN_LABEL_HAS_NO_YEAR"] = out["none_reasons"].get("OWN_LABEL_HAS_NO_YEAR", 0) + 1
            continue
        if uid.startswith("BLOCK:"):
            year, why = dominant_period(json.loads(payload), period_years)
            if year is not None:
                out["block_label"] += 1
                continue
        else:
            why = "NO_BLOCK"
        out["none"] += 1
        key = why if why.startswith(("CENSUS_UNIT_NO_PERIOD_DATA", "UNMAPPABLE", "NO_BLOCK")) else "CENSUS_UNIT_PERIOD_TIE"
        out["none_reasons"][key] = out["none_reasons"].get(key, 0) + 1
    for k in ("own_label", "block_label", "none"):
        out[k + "_pct"] = round(100.0 * out[k] / n, 2) if n else 0.0
    return out


def year_coverage(res: gpd.GeoDataFrame, inventory: gpd.GeoDataFrame, objects: gpd.GeoDataFrame) -> dict:
    n = len(res)
    h_inv = heritage_period(res, inventory)
    h_obj = heritage_period(res, objects)
    osm_year = res["osm_start_date"].map(parse_start_year)
    a = (h_inv != "") | (h_obj != "")
    b = osm_year.notna()
    pct = lambda s: round(100.0 * float(s) / n, 2) if n else 0.0
    return {
        "n_residential": int(n),
        "a_heritage_inventory_period": int((h_inv != "").sum()), "a_heritage_inventory_period_pct": pct((h_inv != "").sum()),
        "a_heritage_objects_period": int((h_obj != "").sum()), "a_heritage_objects_period_pct": pct((h_obj != "").sum()),
        "a_heritage_any_period": int(a.sum()), "a_heritage_any_period_pct": pct(a.sum()),
        "b_osm_start_date_year": int(b.sum()), "b_osm_start_date_year_pct": pct(b.sum()),
        "c_other_open_source": 0, "c_other_open_source_pct": 0.0,
        "any_source": int((a | b).sum()), "any_source_pct": pct((a | b).sum()),
        "best_single_source_pct": max(pct(a.sum()), pct(b.sum())),
        "heritage_period_values": h_inv.where(h_inv != "", h_obj).loc[a].value_counts().to_dict(),
    }


def coverage(res: gpd.GeoDataFrame) -> dict:
    n = len(res)
    pct = lambda s: round(100.0 * float(s) / n, 2) if n else 0.0
    return {
        "n": n,
        "storeys_from_height": int(res["levels"].notna().sum()), "storeys_pct": pct(res["levels"].notna().sum()),
        "height_observed": int(res["height_m"].notna().sum()), "height_pct": pct(res["height_m"].notna().sum()),
        "year_observed": int(res["year_built"].notna().sum()), "year_pct": pct(res["year_built"].notna().sum()),
    }


def blocks_used(picked: dict) -> list[dict]:
    first = picked["ranking_top25"][0]
    used = [{"block_id": first["block_id"], "residential": first["residential"], "running_total": first["residential"]}]
    used += [{"block_id": st["added"], "residential": st["residential"], "running_total": st["running_total"]} for st in picked["expansion_steps"]]
    return used


def run() -> dict:
    suburbs = read_pages(RAW_SUB, "suburb_page")
    raw = read_pages(RAW_FOOT, "footprints_page")
    osm_b, landuse = load_osm(RAW_OSM)
    clean, rep = build_clean_buildings(raw, osm_b, landuse, output_dir=EU02)
    if clean.crs.to_string() != EXPECTED_CRS:
        raise ValueError(f"CRS {clean.crs} != {EXPECTED_CRS}")
    inventory = read_pages(RAW_HER, "heritage_inventory")
    objects = read_pages(RAW_HER, "heritage_inventory_objects")
    res_all = clean[clean["use_class"] == "residential"]
    sel = choose_subunits(suburbs, res_all)
    named = suburbs.to_crs(clean.crs)
    named_union = named[named["OFC_SBRB_NAME"].isin(NAMED_SUBURBS)].union_all()
    cover_named = year_coverage(res_all[res_all.geometry.representative_point().within(named_union)], inventory, objects)
    report = {
        "site": SITE, "crs": clean.crs.to_string(),
        "licence_footprints": (LICENCES / "CCT_footprints_use_limitation.txt").read_text(encoding="utf-8").split("\n\n", 1)[-1].strip(),
        "footprint_build": rep, "route_counts_all_downloaded": res_all["route"].value_counts().to_dict(),
        "subunits": {k: v for k, v in sel.items() if k != "boundary_geom"}, "year_coverage_three_named_suburbs": cover_named,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    report_path = EVIDENCE / "acquisition_report.json"
    if sel["status"] != "FIRST_SUBURB_OVER_CAP":
        report["stopped"] = sel["status"]
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        return report
    district = district_geometry(suburbs, sel["chosen"][0])
    roads = read_highways()
    blocks = street_blocks(roads, district.buffer(300))
    picked = choose_blocks(blocks, res_all, district)
    chosen_blocks = blocks[blocks["block_id"].isin(picked["chosen"])].copy()
    inside = chosen_blocks.geometry.intersection(district).area / chosen_blocks.geometry.area
    boundary_geom = picked["boundary_geom"]
    selection = {
        "mode": "street_blocks_inside_named_suburb", "district": sel["chosen"][0], "district_residential": int(sel["total"]),
        "road_classes": ROAD_CLASSES, "highway_ways": int(len(roads)), "blocks_built": int(len(blocks)),
        "blocks_used": blocks_used(picked), "total": int(picked["total"]), "skipped_over_cap": picked["skipped_over_cap"],
        "share_inside_district": {b: round(float(v), 3) for b, v in zip(chosen_blocks["block_id"], inside)},
        "ranking_top25": picked["ranking_top25"], "boundary_area_km2": round(boundary_geom.area / 1e6, 4),
    }
    own = own_heritage(clean, inventory, objects)
    block_id = street_block_ids(clean, chosen_blocks)
    clean_census = attach_census(clean, own, block_id, clean["use_class"] == "residential")
    boundary = gpd.GeoDataFrame({"site": [SITE], "units": [",".join(picked["chosen"])]}, geometry=[boundary_geom], crs=clean.crs)
    boundary_path = EVIDENCE / "boundary.geojson"
    boundary.to_file(boundary_path, driver="GeoJSON")
    sha = hashlib.sha256(boundary_path.read_bytes()).hexdigest()
    (EVIDENCE / "boundary.sha256").write_text(sha + "\n", encoding="utf-8")
    clipped = clip_to_boundary(clean_census, boundary_path, verify_sha256=sha)
    residential, excluded, counts = split_residential(clipped, CROSSWALK, class_column="use_class")
    residential = residential.copy()
    write_manifests(
        residential, excluded, counts, EU02, neighbourhood_id=SITE, source_endpoint=f"{SERVICE}/ODP_SPLIT_12/MapServer/11",
        licence="City of Cape Town: no named licence, metadata use limitation in licences/CCT_footprints_use_limitation.txt; OSM ODbL 1.0",
        source_layer=FOOTPRINT_LAYER_NAME,
    )
    period_years, no_year = period_years_for(residential)
    report.update({
        "selection": selection, "n_clean": int(len(clean)), "n_clipped": int(len(clipped)), "split_counts": counts,
        "boundary_sha256": sha,
        "route_counts_site_residential": residential["route"].value_counts().to_dict(),
        "coverage_residential": coverage(residential), "year_coverage_site": year_coverage(residential, inventory, objects),
        "period_years": period_years, "labels_without_year": no_year, "survey_year": SURVEY_YEAR,
        "census_unit_kinds": {k: int(residential["census_unit_id"].str.startswith(k).sum()) for k in ("HERITAGE:", "BLOCK:")},
        "year_split": year_split(residential, period_years),
        "storey_distribution": {str(k): int(v) for k, v in residential["levels"].value_counts(dropna=False).sort_index().items()},
        "building_tag_counts": residential["building_tag"].value_counts().to_dict(),
    })
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["download", "osm", "highways", "build"])
    args = ap.parse_args(argv)
    if args.stage == "download":
        print(json.dumps(download(), default=str))
        return 0
    if args.stage == "osm":
        print(json.dumps(download_osm(), default=str))
        return 0
    if args.stage == "highways":
        print(json.dumps(download_highways(), default=str))
        return 0
    report = run()
    keys = ("n_clean", "n_clipped", "split_counts", "coverage_residential", "census_unit_kinds", "year_split", "period_years", "labels_without_year", "stopped")
    print(json.dumps({k: report[k] for k in keys if k in report}, default=str))
    print(json.dumps({k: v for k, v in report.get("selection", {}).items() if k != "ranking_top25"}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
