"""Acquire and clip Vienna (AT-VIE-RUDOLFSHEIM): FMZK outlines + Baukoerpermodell heights + Gebaeudeinfo points."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests  # noqa: E402
from openubem.acquisition.footprint_schema import SCHEMA_COLUMNS, finalize_footprints, serialize  # noqa: E402

SITE_ID = "AT-VIE-RUDOLFSHEIM"
COUNTRY = "AT"
SOURCE_CRS = "EPSG:31256"
UTM_CRS = "EPSG:32633"
DISTRICT_BEZNR = 15
EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-22" / SITE_ID
RAW = EVIDENCE / "raw"
LICENCES = EVIDENCE / "licences"
OUT_DIR = ROOT / "openubem" / "outputs" / "eu02" / SITE_ID
WFS_BASE = "https://data.wien.gv.at/daten/geo?service=WFS&version=1.1.0&request=GetFeature&outputFormat=json&srsName=EPSG:31256"
ATTRIBUTION = "Datenquelle: Stadt Wien - data.wien.gv.at"
LICENCE = "CC BY 4.0"
LAYERS = {
    "ZAEHLBEZIRKOGD": "OBJECTID_NONE",
    "FMZKGEBOGD": "SE_SDO_ROWID",
    "FMZKBKMOGD": "SE_SDO_ROWID",
    "GEBAEUDEINFOOGD": "OBJECTID",
}
PAGE = 5000
YEAR_MIN, YEAR_MAX = 1500, 2016
CENSUS_COLUMNS = ["census_unit_id", "census_period_counts"]


def fetch_layer(layer: str, bbox: tuple[float, float, float, float] | None, *, cql: str | None = None, session=None) -> dict:
    session = session or requests
    sort = LAYERS[layer]
    features: list[dict] = []
    start = 0
    while True:
        url = f"{WFS_BASE}&typeName=ogdwien:{layer}&maxFeatures={PAGE}&startIndex={start}"
        if sort != "OBJECTID_NONE":
            url += f"&sortBy={sort}"
        if bbox is not None:
            url += "&bbox=" + ",".join(f"{v:.2f}" for v in bbox) + ",EPSG:31256"
        if cql is not None:
            url += "&cql_filter=" + cql
        for attempt in range(4):
            response = session.get(url, timeout=300)
            if response.status_code == 200:
                break
            print(f"{layer} start={start} attempt={attempt} HTTP {response.status_code}: {response.text[:300]}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"{layer}: HTTP {response.status_code} {response.text[:300]}")
        page = response.json()
        batch = page["features"]
        features.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE
    return {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::31256"}}, "features": features}


def save_raw(layer: str, collection: dict) -> Path:
    folder = RAW / layer
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{layer}.geojson"
    path.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
    return path


def read_collection(collection: dict | Path | str) -> gpd.GeoDataFrame:
    if isinstance(collection, (str, Path)):
        collection = json.loads(Path(collection).read_text(encoding="utf-8"))
    if not collection["features"]:
        return gpd.GeoDataFrame(geometry=[], crs=SOURCE_CRS)
    gdf = gpd.GeoDataFrame.from_features(collection["features"], crs=SOURCE_CRS)
    return gdf.to_crs(UTM_CRS)


RESIDENTIAL_LABELS = {"Wohnnutzung"}
UNKNOWN_LABELS = {"", "keine Angabe"}
CROSSWALK = {"Wohnnutzung": "residential", "": "unknown", "keine Angabe": "unknown", "*": "non_residential"}
CENSUS_PERIODS = [
    ("OBJ_BAUP_1", "Vor 1919", 1918),
    ("OBJ_BAUP_2", "1919 bis 1944", (1919 + 1944) // 2),
    ("OBJ_BAUP_3", "1945 bis 1960", (1945 + 1960) // 2),
    ("OBJ_BAUP_4", "1961 bis 1970", (1961 + 1970) // 2),
    ("OBJ_BAUP_5", "1971 bis 1980", (1971 + 1980) // 2),
    ("OBJ_BAUP_6", "1981 bis 1990", (1981 + 1990) // 2),
    ("OBJ_BAUP_7", "1991 bis 2000", (1991 + 2000) // 2),
    ("OBJ_BAUP_8", "2001 bis 2005", (2001 + 2005) // 2),
    ("OBJ_BAUP_9", "2006 bis 2011", (2006 + 2011) // 2),
    ("OBJ_BAUP_10", "2012 und spaeter", 2012),
]
PERIOD_YEARS = {label: year for _, label, year in CENSUS_PERIODS}
CATALOGUE = "https://www.data.gv.at/katalog/datasets/"
DATASETS = {
    "ZAEHLBEZIRKOGD": "ae8d7db5-98e9-4f86-bbec-9babfa2a4f03",
    "FMZKGEBOGD": "7cf0da04-1f77-4321-929e-78172c74aa0b",
    "FMZKBKMOGD": "76c2e577-268f-4a93-bccd-7d5b43b14efd",
    "GEBAEUDEINFOOGD": "7a8aae59-71a4-4500-b38b-bdf15c7f627f",
    "RZ2023_GEBAEUDE_ZAEHLBEZIRKE": "28185052-3df4-46ae-8c97-8b47221c6487",
}
CENSUS_URL = "https://go.gv.at/l9ogdvie4032023"


def _int_or_none(value):
    if value is None:
        return None
    try:
        if isinstance(value, float) and np.isnan(value):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def point_year(baujahr, l_bauj) -> int | None:
    year = _int_or_none(baujahr)
    if year is not None and YEAR_MIN <= year <= YEAR_MAX:
        return year
    match = re.fullmatch(r"\s*(\d{4})\s*", str(l_bauj)) if l_bauj is not None else None
    if match and YEAR_MIN <= int(match.group(1)) <= YEAR_MAX:
        return int(match.group(1))
    return None


def aggregate_points(points: pd.DataFrame) -> dict:
    n = len(points)
    storeys = [s for s in (_int_or_none(v) for v in points["GESCH_ANZ"]) if s is not None and s > 0]
    years = [y for y in (point_year(b, l) for b, l in zip(points["BAUJAHR"], points["L_BAUJ"])) if y is not None]
    year, tie = None, False
    if years:
        counts = pd.Series(years).value_counts()
        top = counts[counts == counts.max()]
        if len(top) == 1:
            year = int(top.index[0])
        else:
            tie = True
    uses = [str(u) if u is not None else "" for u in points["L_NUTZUNG"]]
    residential = [u for u in uses if u in RESIDENTIAL_LABELS]
    if n and 2 * len(residential) >= n:
        label = sorted(pd.Series(residential).mode())[0]
    else:
        named = [u for u in uses if u not in UNKNOWN_LABELS] or uses
        label = sorted(pd.Series(named).mode())[0] if named else ""
    return {"levels": max(storeys) if storeys else None, "year_built": year, "year_tie": tie, "function_tag": label, "n_points": n}


def dissolve_buildings(geb: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    rows = []
    for geb_id, group in geb.groupby("BW_GEB_ID", sort=True):
        geoms = [g if g.is_valid else g.buffer(0) for g in group.geometry]
        merged = unary_union(geoms)
        parts = list(merged.geoms) if isinstance(merged, MultiPolygon) else [merged]
        parts = [p for p in parts if isinstance(p, Polygon) and not p.is_empty]
        parts.sort(key=lambda p: -p.area)
        multi = len(parts) > 1
        for number, part in enumerate(parts, start=1):
            rows.append({"bw_geb_id": int(geb_id), "part": number if multi else 0, "n_parts": len(parts), "geometry": part})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=geb.crs)


def body_heights(bkm: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    bodies = bkm[bkm["BW_GEB_ID"].notna()].copy()
    bodies["body_height"] = pd.to_numeric(bodies["O_KOTE"], errors="coerce") - pd.to_numeric(bodies["HOEHE_DGM"], errors="coerce")
    return bodies[bodies["body_height"] > 0].copy()


def assign_heights(buildings: gpd.GeoDataFrame, bodies: gpd.GeoDataFrame) -> pd.Series:
    by_id = {int(k): g for k, g in bodies.groupby("BW_GEB_ID")}
    heights = []
    for row in buildings.itertuples():
        group = by_id.get(row.bw_geb_id)
        if group is None:
            heights.append(np.nan)
        elif row.n_parts > 1:
            inside = group[group.geometry.centroid.within(row.geometry.buffer(1e-6))]
            heights.append(float(inside["body_height"].max()) if len(inside) else np.nan)
        else:
            heights.append(float(group["body_height"].max()))
    return pd.Series(heights, index=buildings.index, dtype="float64")


def build_rows(geb: gpd.GeoDataFrame, bkm: gpd.GeoDataFrame, info: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    stats: dict = {"geb_polygons": int(len(geb)), "geb_polygons_without_bw_geb_id": int(geb["BW_GEB_ID"].isna().sum())}
    buildings = dissolve_buildings(geb[geb["BW_GEB_ID"].notna()])
    stats["buildings_dissolved"] = int(buildings["bw_geb_id"].nunique())
    stats["footprint_parts"] = int(len(buildings))
    buildings["height_m"] = assign_heights(buildings, body_heights(bkm))
    buildings = buildings.reset_index(drop=True)
    joined = gpd.sjoin(info, buildings[["geometry"]], how="left", predicate="intersects")
    joined = joined[~joined.index.duplicated(keep="first")]
    stats["points_total"] = int(len(info))
    stats["points_dropped_outside_footprints"] = int(joined["index_right"].isna().sum())
    matched = joined[joined["index_right"].notna()].copy()
    matched["index_right"] = matched["index_right"].astype(int)
    per_building = {int(k): aggregate_points(g) for k, g in matched.groupby("index_right")}
    counts = pd.Series([per_building.get(i, {}).get("n_points", 0) for i in buildings.index], dtype=int)
    stats["buildings_with_0_points"] = int((counts == 0).sum())
    stats["buildings_with_1_point"] = int((counts == 1).sum())
    stats["buildings_with_2plus_points"] = int((counts >= 2).sum())
    stats["year_ties"] = int(sum(1 for v in per_building.values() if v["year_tie"]))
    empty = {"levels": None, "year_built": None, "year_tie": False, "function_tag": "", "n_points": 0}
    out = []
    for i, row in buildings.iterrows():
        agg = per_building.get(i, empty)
        out.append({
            "geometry": row.geometry, "osm_id": f"AT-VIE-{row.bw_geb_id}" + (f"_p{row.part}" if row.part else ""),
            "crs_utm": UTM_CRS, "building_tag": "", "function_tag": agg["function_tag"], "levels": agg["levels"],
            "height_m": row.height_m, "year_built": agg["year_built"], "postcode": "", "underground": 0, "roof_shape": "",
            "roof_height_m": np.nan, "footprint_area_m2": row.geometry.area, "perimeter_m": row.geometry.length,
            "surplus_tags": json.dumps({"BW_GEB_ID": int(row.bw_geb_id), "n_points": agg["n_points"], "year_tie": bool(agg["year_tie"])}, sort_keys=True),
            "provenance_levels": "", "provenance_height_m": "", "provenance_year_built": "", "provenance_building_tag": "",
            "provenance_function_tag": "", "provenance_postcode": "", "provenance_geometry": "", "data_quality_flag": "",
        })
    frame = gpd.GeoDataFrame(out, geometry="geometry", crs=geb.crs)
    return frame[SCHEMA_COLUMNS], stats


def finalize_vienna(frame: gpd.GeoDataFrame, output_dir: Path | None = None) -> gpd.GeoDataFrame:
    frame = frame.copy()
    frame["levels"] = pd.to_numeric(frame["levels"], errors="coerce").astype("Int64")
    frame["year_built"] = pd.to_numeric(frame["year_built"], errors="coerce").astype("Int64")
    out = finalize_footprints(frame, source="VIENNA_GEBAEUDEINFO", output_dir=None).copy()
    if str(out.crs).upper() != UTM_CRS:
        raise ValueError(f"expected {UTM_CRS}, got {out.crs}")
    out["provenance_height_m"] = out["height_m"].map(lambda v: "VIENNA_BKM_MISSING" if pd.isna(v) else "VIENNA_BKM_MEASURED")
    resolved = out["provenance_geometry"].str.endswith("_OVERLAP_RESOLVED")
    out["provenance_geometry"] = np.where(resolved, "VIENNA_FMZK_GEB_OVERLAP_RESOLVED", "VIENNA_FMZK_GEB")
    out["data_quality_flag"] = out["data_quality_flag"].map(lambda s: ",".join(t for t in s.split(",") if t and t != "no_building_tag"))
    if output_dir is not None:
        serialize(out, output_dir)
    return out


def read_census(path: Path | str) -> dict[str, dict[str, int]]:
    table = pd.read_csv(path, sep=";", skiprows=1, encoding="latin1", dtype=str)
    result: dict[str, dict[str, int]] = {}
    for _, row in table.iterrows():
        result[str(row["SUB_DISTRICT_CODE"])[1:]] = {label: int(row[column]) for column, label, _ in CENSUS_PERIODS}
    return result


def attach_census(frame: gpd.GeoDataFrame, units: gpd.GeoDataFrame, census: dict[str, dict[str, int]]) -> gpd.GeoDataFrame:
    points = gpd.GeoDataFrame(geometry=frame.geometry.representative_point(), crs=frame.crs)
    joined = gpd.sjoin(points, units[["ZBEZ", "geometry"]], how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    out = frame.copy()
    unit = joined["ZBEZ"].reindex(out.index)
    out["census_unit_id"] = unit.where(unit.notna(), "").astype(str)
    out["census_period_counts"] = out["census_unit_id"].map(lambda u: json.dumps(census[u], ensure_ascii=False) if u in census else "")
    return out


def rank_units(frame: gpd.GeoDataFrame, units: gpd.GeoDataFrame) -> pd.DataFrame:
    classes = frame["function_tag"].map(lambda t: CROSSWALK.get(t, CROSSWALK["*"]))
    pts = gpd.GeoDataFrame({"residential": (classes == "residential").values}, geometry=frame.geometry.representative_point().values, crs=frame.crs)
    joined = gpd.sjoin(pts, units[["ZBEZ", "geometry"]], how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    counts = joined[joined["residential"]].groupby("ZBEZ").size()
    table = pd.DataFrame({"ZBEZ": units["ZBEZ"].values, "area_km2": units.geometry.area.values / 1e6})
    table["residential"] = table["ZBEZ"].map(counts).fillna(0).astype(int)
    table["per_km2"] = table["residential"] / table["area_km2"]
    return table.sort_values("per_km2", ascending=False).reset_index(drop=True)


def choose_units(ranking: pd.DataFrame, units: gpd.GeoDataFrame) -> tuple[list[str], list[str]]:
    total = int(ranking["residential"].sum())
    notes = [f"district_total_residential={total}"]
    if 500 <= total <= 1000:
        return list(ranking["ZBEZ"]), notes + ["whole 15th district used"]
    if total < 500:
        raise RuntimeError(f"district holds only {total} residential buildings (<500); plan has no rule for this")
    first = ranking.iloc[0]
    chosen = [first["ZBEZ"]]
    count = int(first["residential"])
    notes.append(f"first ranked {first['ZBEZ']} -> {count}")
    if count > 1000:
        raise RuntimeError(f"first-ranked unit {first['ZBEZ']} alone holds {count} (>1000); plan has no rule for this")
    geom = units.set_index("ZBEZ").geometry
    centre = geom[first["ZBEZ"]].centroid
    by_unit = ranking.set_index("ZBEZ")["residential"]
    while count < 500:
        union = unary_union([geom[u] for u in chosen])
        candidates = [u for u in geom.index if u not in chosen and geom[u].intersection(union).length > 1.0]
        if not candidates:
            raise RuntimeError(f"no touching unit left with {count} buildings")
        nxt = min(candidates, key=lambda u: geom[u].centroid.distance(centre))
        if count + int(by_unit[nxt]) > 1000:
            raise RuntimeError(f"adding {nxt} would pass 1000 ({count}+{int(by_unit[nxt])}); plan says never pass 1000")
        chosen.append(nxt)
        count += int(by_unit[nxt])
        notes.append(f"added {nxt} -> {count}")
    return chosen, notes


def write_licences(downloaded_at: str) -> None:
    LICENCES.mkdir(parents=True, exist_ok=True)
    deed = requests.get("https://creativecommons.org/licenses/by/4.0/deed.de", timeout=60)
    deed_text = re.sub(r"\s+", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", " ", deed.text, flags=re.S)).strip()[:6000]
    for source, dataset_id in DATASETS.items():
        meta = requests.get(f"https://www.data.gv.at/api/hub/search/datasets/{dataset_id}", timeout=60).json()["result"]
        licences = sorted({(d.get("license") or {}).get("resource", "") for d in meta.get("distributions", [])} - {""})
        data_url = CENSUS_URL if source.startswith("RZ2023") else f"{WFS_BASE}&typeName=ogdwien:{source}"
        text = [
            f"source: {source}",
            f"catalogue page: {CATALOGUE}{dataset_id}",
            f"catalogue title: {meta.get('title', {}).get('de')}",
            f"catalogue modified: {meta.get('modified')}",
            f"download date: {downloaded_at}",
            f"data URL: {data_url}",
            f"licence declared in catalogue distributions: {', '.join(licences) or 'none declared'}",
            f"required attribution: {ATTRIBUTION}",
            "",
            "licence deed text (https://creativecommons.org/licenses/by/4.0/deed.de, fetched at download time):",
            deed_text,
        ]
        (LICENCES / f"{source}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def coverage(frame: gpd.GeoDataFrame) -> dict:
    n = len(frame)
    share = lambda mask: round(float(mask.sum()) / n, 4) if n else 0.0
    return {
        "storeys": {"non_null_share": share(frame["levels"].notna()), "source": "VIENNA_GEBAEUDEINFO_OBSERVED"},
        "height": {"non_null_share": share(frame["height_m"].notna()), "source": "VIENNA_BKM_MEASURED"},
        "year": {"non_null_share": share(frame["year_built"].notna()), "source": "VIENNA_GEBAEUDEINFO_OBSERVED"},
        "census_unit": {"non_null_share": share(frame["census_unit_id"] != ""), "source": "RZ2023 Gebaeude Zaehlbezirke (CSV)"},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="re-download the raw layers")
    args = parser.parse_args()
    now = datetime.now(timezone.utc).isoformat()
    paths = {name: RAW / name / f"{name}.geojson" for name in ("ZAEHLBEZIRKOGD", "FMZKGEBOGD", "FMZKBKMOGD", "GEBAEUDEINFOOGD")}
    census_dir = RAW / "RZ2023_GEBAEUDE_ZAEHLBEZIRKE"
    census_path = census_dir / "vie-403-2023.csv"
    if args.download or not all(p.exists() for p in paths.values()):
        units_raw = fetch_layer("ZAEHLBEZIRKOGD", None, cql=f"BEZNR={DISTRICT_BEZNR}")
        save_raw("ZAEHLBEZIRKOGD", units_raw)
        minx, miny, maxx, maxy = gpd.GeoDataFrame.from_features(units_raw["features"], crs=SOURCE_CRS).total_bounds
        bbox = (minx - 50, miny - 50, maxx + 50, maxy + 50)
        for layer in ("FMZKGEBOGD", "FMZKBKMOGD", "GEBAEUDEINFOOGD"):
            save_raw(layer, fetch_layer(layer, bbox))
    if not census_path.exists():
        census_dir.mkdir(parents=True, exist_ok=True)
        response = requests.get(CENSUS_URL, timeout=120)
        response.raise_for_status()
        census_path.write_bytes(response.content)
    write_licences(now)

    units = read_collection(paths["ZAEHLBEZIRKOGD"])
    units = units[units["BEZNR"] == DISTRICT_BEZNR].reset_index(drop=True)
    geb, bkm, info = (read_collection(paths[n]) for n in ("FMZKGEBOGD", "FMZKBKMOGD", "GEBAEUDEINFOOGD"))
    frame, stats = build_rows(geb, bkm, info)
    district = unary_union(list(units.geometry))
    frame = frame[frame.geometry.representative_point().within(district)].reset_index(drop=True)
    stats["parts_in_district"] = int(len(frame))
    clean = finalize_vienna(frame, OUT_DIR)
    stats["after_cleaning"] = int(len(clean))
    census = read_census(census_path)
    clean = attach_census(clean, units, census)
    ranking = rank_units(clean, units)
    chosen, notes = choose_units(ranking, units)
    shape = unary_union([g for z, g in zip(units["ZBEZ"], units.geometry) if z in chosen])
    boundary = gpd.GeoDataFrame({"site_id": [SITE_ID], "units": [",".join(chosen)]}, geometry=[shape], crs=units.crs)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    boundary_path = EVIDENCE / "boundary.gpkg"
    boundary.to_file(boundary_path, layer="boundary", driver="GPKG")
    clipped = clip_to_boundary(clean, boundary_path, verify_sha256=sha256_file(boundary_path))
    residential, excluded, counts = split_residential(clipped, CROSSWALK, class_column="function_tag")
    write_manifests(residential, excluded, counts, OUT_DIR, neighbourhood_id=SITE_ID, source_endpoint=WFS_BASE, licence=f"{LICENCE} ({ATTRIBUTION})", source_layer="ogdwien:FMZKGEBOGD + FMZKBKMOGD + GEBAEUDEINFOOGD")
    report = {
        "site_id": SITE_ID, "retrieved_at_utc": now, "units_ranking": ranking.round(3).to_dict(orient="records"),
        "units_used": chosen, "selection_notes": notes, "residential_count": int(len(residential)), "exclusion_counts": counts,
        "coverage_residential": coverage(residential), "build_stats": stats, "period_years": PERIOD_YEARS,
        "census_table": {"url": CENSUS_URL, "file": str(census_path.relative_to(ROOT)), "sha256": sha256_file(census_path), "reference_date": "2023-10-31", "period_columns": {c: l for c, l, _ in CENSUS_PERIODS}},
        "boundary_sha256": sha256_file(boundary_path),
        "licence_files": sorted(p.name for p in LICENCES.glob("*.txt")),
        "raw_sha256": {n: sha256_file(p) for n, p in paths.items()},
    }
    (EVIDENCE / "acquisition_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("units_used", "selection_notes", "residential_count", "exclusion_counts", "coverage_residential")}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
