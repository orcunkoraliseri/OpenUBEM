from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString
from shapely.ops import linemerge, polygonize, unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests  # noqa: E402

SITE = "AM-EVN-NORNORK"
COUNTRY = "AM"
EXPECTED_CRS = "EPSG:32638"
DISTRICT_REL = 13404220
EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-22" / SITE
RAW = EVIDENCE / "raw"
LICENCES = EVIDENCE / "licences"
EU02 = ROOT / "openubem" / "outputs" / "eu02" / SITE
ARMSTAT_TABLES = EVIDENCE / "armstat_tables.csv"
ARMSTAT_URL = "https://armstat.am/file/article/bnakfond_2021_1.pdf"
ARMSTAT_HOME = "https://armstat.am/en/"
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
USER_AGENT = "OpenUBEM-research/1.0 (orcunkoral.oseri@concordia.ca)"
BBOX_BUFFER_DEG = 0.004
ROAD_CLASSES = "motorway|trunk|primary|secondary|tertiary|residential|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link"
RESIDENTIAL_TAGS = {"house", "terrace", "apartments", "residential", "semidetached_house", "detached"}
PRIVATE_HOUSE_TAGS = {"house", "terrace", "semidetached_house", "detached"}
UNTAGGED = {"yes", ""}
LOW, HIGH = 500, 1000
NO_PERIOD_PRIVATE = "NO_PERIOD_SOURCE_PRIVATE_HOUSE"
CROSSWALK = {"residential": "residential", "non_residential": "non_residential", "unknown": "unknown"}
PERIOD_LABELS = ["up to 1950", "1951-1970", "1971-1980", "1981-1990", "1991-2000", "2001-2010", "2011+"]
PERIOD_YEARS = {
    "up to 1950": 1950,
    "1951-1970": (1951 + 1970) // 2,
    "1971-1980": (1971 + 1980) // 2,
    "1981-1990": (1981 + 1990) // 2,
    "1991-2000": (1991 + 2000) // 2,
    "2001-2010": (2001 + 2010) // 2,
    "2011+": 2011,
}
PERIOD_TABLE_ID = "period_by_district"
CROSSED_TABLE_ID = "period_by_storey_band"
CENSUS_UNIT_ROW = "Nor Nork"


def overpass(query: str, rounds: int = 6, endpoints: list[str] | None = None, session=None, sleep=time.sleep) -> bytes:
    session = session or requests
    errors: list[str] = []
    for attempt in range(rounds):
        for endpoint in endpoints or ENDPOINTS:
            try:
                response = session.post(endpoint, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=900)
            except requests.RequestException as error:
                errors.append(f"{endpoint}: {error!r}"[:300])
                print(errors[-1], file=sys.stderr)
                continue
            head = response.content[:400].decode("utf-8", "replace").replace("\n", " ")
            ok_head = head.lstrip().startswith(("{", "<?xml", "<osm"))
            if response.status_code == 200 and ok_head and "rate_limited" not in head and "runtime error" not in head:
                return response.content
            errors.append(f"{endpoint}: HTTP {response.status_code} {head}"[:300])
            print(errors[-1], file=sys.stderr)
        sleep(15 * (attempt + 1))
    raise RuntimeError("Overpass failed on every endpoint: " + " | ".join(errors[-3:]))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def boundary_polygon(element: dict):
    lines = []
    for member in element["members"]:
        if member.get("type") == "way" and member.get("role") in ("outer", "") and member.get("geometry"):
            lines.append(LineString([(p["lon"], p["lat"]) for p in member["geometry"]]))
    polygons = list(polygonize(linemerge(unary_union(lines))))
    if not polygons:
        raise ValueError("district relation does not close into a polygon")
    return unary_union(polygons)


def _text(value) -> str:
    if value is None or value is pd.NA or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def classify_use(building_tag, function_tag, in_landuse_residential: bool) -> tuple[str, str]:
    tag = _text(building_tag).lower()
    function = _text(function_tag)
    if tag in RESIDENTIAL_TAGS:
        return "residential", "osm_residential_tag"
    if tag in UNTAGGED and function == "":
        if in_landuse_residential:
            return "residential", "untagged_in_landuse_residential"
        return "unknown", "untagged_outside_landuse_residential"
    return "non_residential", "osm_other_tag"


def storey_band(levels) -> str | None:
    if levels is None or levels is pd.NA or (isinstance(levels, float) and pd.isna(levels)):
        return None
    n = int(levels)
    if n <= 0:
        return None
    if n <= 5:
        return str(n)
    return "6-8" if n <= 8 else "9+"


def read_armstat_tables(path: Path | str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["count"] = int(row["count"])
    return rows


def period_counts(rows: list[dict], unit_row: str, band: str | None = None) -> tuple[dict[str, int], str]:
    if band is not None:
        in_band = {r["category"]: r["count"] for r in rows if r["table_id"] == CROSSED_TABLE_ID and r["district_row"] == unit_row and r["storey_band"] == band}
        if in_band and sum(in_band.values()) > 0:
            return {label: in_band.get(label, 0) for label in PERIOD_LABELS}, "storey_band"
    flat = {r["category"]: r["count"] for r in rows if r["table_id"] == PERIOD_TABLE_ID and r["district_row"] == unit_row}
    missing = [label for label in PERIOD_LABELS if label not in flat]
    if missing:
        raise ValueError(f"period table misses {missing} for {unit_row}")
    return {label: flat[label] for label in PERIOD_LABELS}, "district"


def is_private_house(building_tag, levels) -> bool:
    tag = _text(building_tag).lower()
    if tag in PRIVATE_HOUSE_TAGS:
        return True
    return tag != "apartments" and storey_band(levels) in ("1", "2")


def attach_period_source(frame: gpd.GeoDataFrame, rows: list[dict], unit_row: str = CENSUS_UNIT_ROW) -> gpd.GeoDataFrame:
    out = frame.copy()
    ids, payloads, reasons, scopes = [], [], [], []
    cache: dict = {}
    for tag, levels in zip(out["building_tag"], out["levels"]):
        if is_private_house(tag, levels):
            ids.append(SITE)
            payloads.append("")
            reasons.append(NO_PERIOD_PRIVATE)
            scopes.append("")
            continue
        band = storey_band(levels)
        if band not in cache:
            cache[band] = period_counts(rows, unit_row, band)
        counts, scope = cache[band]
        ids.append(SITE)
        payloads.append(json.dumps(counts, ensure_ascii=False))
        reasons.append("")
        scopes.append(scope)
    out["census_unit_id"] = ids
    out["census_period_counts"] = payloads
    out["period_exclusion_reason"] = reasons
    out["period_scope"] = scopes
    return out


def street_blocks(roads: gpd.GeoDataFrame, district_buffered) -> gpd.GeoDataFrame:
    faces = [p for p in polygonize(unary_union(list(roads.geometry))) if p.intersects(district_buffered)]
    return gpd.GeoDataFrame({"block_id": [f"B{i:04d}" for i in range(len(faces))]}, geometry=faces, crs=roads.crs)


def choose_blocks(blocks: gpd.GeoDataFrame, residential: gpd.GeoDataFrame, district_geom, *, low: int = LOW, high: int = HIGH) -> dict:
    points = residential.geometry.representative_point()
    blocks = blocks.copy()
    blocks["inside"] = blocks.geometry.intersection(district_geom).area / blocks.geometry.area
    blocks["n_res"] = [int(points.within(g).sum()) for g in blocks.geometry]
    blocks["area_km2"] = blocks.geometry.area / 1e6
    blocks["density"] = blocks["n_res"] / blocks["area_km2"]
    cand = blocks[(blocks["inside"] >= 0.5) & (blocks["n_res"] > 0)].sort_values("density", ascending=False).reset_index(drop=True)
    if cand.empty:
        raise ValueError("No street block holds residential buildings")
    first = cand.iloc[0]
    chosen, total, union, skipped, steps = [first.block_id], int(first.n_res), first.geometry, [], []
    if total > high:
        raise ValueError(f"First block {first.block_id} holds {total} > {high}")
    pool = blocks
    while total < low:
        rest = pool[~pool.block_id.isin(chosen + skipped)]
        near = rest[rest.geometry.apply(lambda g: g.intersects(union.buffer(1.0)))].copy()
        if near.empty:
            raise ValueError(f"Only {total} residential buildings reachable")
        near["dist"] = near.geometry.centroid.distance(first.geometry.centroid)
        pick = near.sort_values("dist").iloc[0]
        if total + int(pick.n_res) > high:
            skipped.append(pick.block_id)
            continue
        chosen.append(pick.block_id)
        total += int(pick.n_res)
        union = union.union(pick.geometry)
        steps.append({"added": pick.block_id, "residential": int(pick.n_res), "running_total": total})
    ranking = [
        {"block_id": r.block_id, "residential": int(r.n_res), "area_km2": round(float(r.area_km2), 5), "per_km2": round(float(r.density), 1)}
        for r in cand.head(25).itertuples()
    ]
    return {"chosen": chosen, "total": total, "ranking_top25": ranking, "expansion_steps": steps, "skipped_over_cap": skipped, "boundary_geom": union}


def raw_paths() -> dict[str, Path]:
    return {
        "boundary": RAW / "osm_boundary" / f"relation_{DISTRICT_REL}.json",
        "buildings": RAW / "osm_buildings" / "buildings.osm",
        "landuse": RAW / "osm_landuse" / "landuse_residential.osm",
        "roads": RAW / "osm_roads" / "roads.json",
    }


def download(refresh: bool) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    paths = raw_paths()
    if refresh or not paths["boundary"].exists():
        paths["boundary"].parent.mkdir(parents=True, exist_ok=True)
        paths["boundary"].write_bytes(overpass(f"[out:json][timeout:120];rel({DISTRICT_REL});out geom;"))
    element = json.loads(paths["boundary"].read_text(encoding="utf-8"))["elements"][0]
    west, south, east, north = boundary_polygon(element).bounds
    box = f"{south - BBOX_BUFFER_DEG:.6f},{west - BBOX_BUFFER_DEG:.6f},{north + BBOX_BUFFER_DEG:.6f},{east + BBOX_BUFFER_DEG:.6f}"
    queries = {
        "buildings": f'[out:xml][timeout:900][bbox:{box}];(way["building"];rel["building"];);(._;>;);out meta;',
        "landuse": f'[out:xml][timeout:900][bbox:{box}];(way["landuse"="residential"];rel["landuse"="residential"];);(._;>;);out meta;',
        "roads": f'[out:json][timeout:900][bbox:{box}];way["highway"~"^({ROAD_CLASSES})$"];out geom;',
    }
    for name, query in queries.items():
        if refresh or not paths[name].exists():
            paths[name].parent.mkdir(parents=True, exist_ok=True)
            paths[name].write_bytes(overpass(query))
    return {"retrieved_at_utc": now, "bbox_s_w_n_e": box, "paths": paths}


def write_licences(now: str) -> None:
    LICENCES.mkdir(parents=True, exist_ok=True)
    sources = ["https://opendatacommons.org/licenses/odbl/1-0/", "https://www.openstreetmap.org/copyright"]
    parts = [f"retrieved_at_utc: {now}"]
    for url in sources:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        parts += ["", f"source: {url}", f"http_status: {response.status_code}", response.text]
    (LICENCES / "osm_odbl.txt").write_text("\n".join(parts) + "\n", encoding="utf-8")
    home = requests.get(ARMSTAT_HOME, headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", home.text))
    start = text.find("Official Website of Statistical Committee RA")
    footer = text[start:start + 330] if start >= 0 else "FOOTER NOT FOUND"
    (LICENCES / "armstat_terms.txt").write_text(
        "\n".join([
            f"retrieved_at_utc: {now}", f"source: {ARMSTAT_HOME}", f"http_status: {home.status_code}",
            "document: " + ARMSTAT_URL, "terms found on the site (page footer, verbatim):", footer,
        ]) + "\n", encoding="utf-8")


def coverage(res: gpd.GeoDataFrame) -> dict:
    n = len(res)
    pct = lambda s: round(100.0 * float(s) / n, 2) if n else 0.0
    from_height = res["levels"].isna() & res["height_m"].notna()
    to_impute = res["levels"].isna() & res["height_m"].isna()
    return {
        "n": n,
        "storeys_observed": int(res["levels"].notna().sum()), "storeys_observed_pct": pct(res["levels"].notna().sum()),
        "storeys_from_height": int(from_height.sum()), "storeys_from_height_pct": pct(from_height.sum()),
        "storeys_to_impute_from_neighbours": int(to_impute.sum()), "storeys_to_impute_pct": pct(to_impute.sum()),
        "height_observed": int(res["height_m"].notna().sum()), "height_observed_pct": pct(res["height_m"].notna().sum()),
        "year_observed": int(res["year_built"].notna().sum()), "year_observed_pct": pct(res["year_built"].notna().sum()),
        "census_unit_assigned": int((res["census_unit_id"] != "").sum()), "census_unit_pct": pct((res["census_unit_id"] != "").sum()),
        "period_counts_attached": int((res["census_period_counts"] != "").sum()), "period_counts_pct": pct((res["census_period_counts"] != "").sum()),
    }


def run(refresh: bool = False) -> dict:
    import osmnx as ox
    from openubem.acquisition.osm_fetcher import ingest_buildings

    info = download(refresh)
    paths = info["paths"]
    if refresh or not (LICENCES / "osm_odbl.txt").exists() or not (LICENCES / "armstat_terms.txt").exists():
        write_licences(info["retrieved_at_utc"])
    district_wgs = boundary_polygon(json.loads(paths["boundary"].read_text(encoding="utf-8"))["elements"][0])
    clean = ingest_buildings(osm_path=paths["buildings"], output_dir=EU02)
    if clean.crs.to_string() != EXPECTED_CRS:
        raise ValueError(f"CRS {clean.crs} != {EXPECTED_CRS}")
    landuse = ox.features.features_from_xml(paths["landuse"], tags={"landuse": "residential"})
    landuse = landuse[landuse.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].to_crs(clean.crs)
    landuse_union = landuse.geometry.union_all()
    district = gpd.GeoSeries([district_wgs], crs="EPSG:4326").to_crs(clean.crs).iloc[0]
    points = clean.geometry.representative_point()
    in_landuse = points.within(landuse_union).values
    uses = [classify_use(b, f, i) for b, f, i in zip(clean["building_tag"], clean["function_tag"], in_landuse)]
    clean = clean.copy()
    clean["use_class"] = [u for u, _ in uses]
    clean["use_route"] = [r for _, r in uses]
    clean = attach_period_source(clean, read_armstat_tables(ARMSTAT_TABLES))
    in_district = points.within(district).values
    res_mask = (clean["use_class"] == "residential").values
    private_mask = (clean["period_exclusion_reason"] == NO_PERIOD_PRIVATE).values
    eligible = clean[res_mask & ~private_mask]
    district_residential = int((res_mask & ~private_mask & in_district).sum())
    selection = {"mode": "whole_district", "district_residential_with_period_source": district_residential,
                 "district_residential_all": int((res_mask & in_district).sum())}
    boundary_geom = district
    if not (LOW <= district_residential <= HIGH):
        features = [
            {"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": [(p["lon"], p["lat"]) for p in w["geometry"]]}}
            for w in json.loads(paths["roads"].read_text(encoding="utf-8"))["elements"] if w.get("geometry")
        ]
        roads = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326").to_crs(clean.crs)
        picked = choose_blocks(street_blocks(roads, district.buffer(300)), eligible, district)
        boundary_geom = picked.pop("boundary_geom")
        selection = {**selection, "mode": "street_blocks", **picked}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    boundary = gpd.GeoDataFrame({"site": [SITE], "mode": [selection["mode"]]}, geometry=[boundary_geom], crs=clean.crs).to_crs("EPSG:4326")
    boundary_path = EVIDENCE / "boundary.geojson"
    boundary.to_file(boundary_path, driver="GeoJSON")
    sha = sha256_file(boundary_path)
    (EVIDENCE / "boundary.sha256").write_text(sha + "\n", encoding="utf-8")
    clipped = clip_to_boundary(clean, boundary_path, verify_sha256=sha)
    private_in_clip = (clipped["period_exclusion_reason"] == NO_PERIOD_PRIVATE) & (clipped["use_class"] == "residential")
    clipped["use_class"] = clipped["use_class"].where(~private_in_clip, "non_residential")
    residential, excluded, counts = split_residential(clipped, CROSSWALK, class_column="use_class")
    residential = residential.drop(columns=["use_class"])
    excluded = excluded.drop(columns=["use_class"])
    write_manifests(
        residential, excluded, counts, EU02, neighbourhood_id=SITE, source_endpoint=",".join(ENDPOINTS),
        licence="ODbL 1.0 OpenStreetMap contributors; Armstat RA Housing Stock and Communal Economy 2020",
        source_layer="OSM building + landuse=residential; Armstat bnakfond_2021_1",
    )
    report = {
        "site": SITE, "crs": clean.crs.to_string(), "retrieved_at_utc": info["retrieved_at_utc"], "bbox_s_w_n_e": info["bbox_s_w_n_e"],
        "district": {"osm_relation": DISTRICT_REL, "admin_level": 5, "name": "Nor Nork", "area_km2": round(district.area / 1e6, 3)},
        "n_downloaded_buildings": int(len(clean)), "landuse_residential_polygons": int(len(landuse)),
        "use_route_counts_district": {k: int(v) for k, v in clean.loc[in_district, "use_route"].value_counts().items()},
        "use_route_counts_manifest": {k: int(v) for k, v in residential["use_route"].value_counts().items()},
        "selection": selection, "split_counts": counts,
        "private_house_excluded_in_selection": int(private_in_clip.sum()), "private_house_exclusion_reason": NO_PERIOD_PRIVATE,
        "boundary_area_km2": round(boundary_geom.area / 1e6, 3), "boundary_sha256": sha,
        "coverage_residential": coverage(residential),
        "period_years": PERIOD_YEARS,
        "census_unit": {"census_unit_id": SITE, "unit": "Nor Nork administrative district of Yerevan", "scope": "district totals (no storey-band by period table exists)"},
        "armstat": {"url": ARMSTAT_URL, "pdf_sha256": sha256_file(RAW / "armstat" / "bnakfond_2021_1.pdf"), "tables_csv": str(ARMSTAT_TABLES.relative_to(ROOT)), "tables_csv_sha256": sha256_file(ARMSTAT_TABLES)},
        "licence_files": sorted(p.name for p in LICENCES.glob("*.txt")),
        "raw_sha256": {n: sha256_file(pth) for n, pth in paths.items()},
        "fields_used": {"storeys": "OSM building:levels", "height": "OSM height", "year": "none (OSM start_date absent)", "type": "OSM building tag", "period": "Armstat table, district totals"},
    }
    (EVIDENCE / "acquisition_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + chr(10), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    result = run(parser.parse_args(argv).refresh)
    keep = ("use_route_counts_district", "use_route_counts_manifest", "split_counts", "private_house_excluded_in_selection", "boundary_area_km2", "coverage_residential")
    print(json.dumps({k: result[k] for k in keep}, default=str))
    print(json.dumps({k: v for k, v in result["selection"].items() if k not in ("chosen", "ranking_top25")}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
