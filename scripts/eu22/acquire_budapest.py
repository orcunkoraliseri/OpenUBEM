from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import pandas as pd
import requests
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests  # noqa: E402
from openubem.acquisition.footprint_schema import finalize_footprints  # noqa: E402
from openubem.acquisition.osm_fetcher import _flatten_tags  # noqa: E402

SITE = "HU-BUD-ERZSEBETVAROS"
CC = "HU"
EXPECTED_CRS = "EPSG:32634"
OVERPASS = "https://overpass-api.de/api/interpreter"
USER_AGENT = "OpenUBEM-research/1.0 (orcunkoral.oseri@concordia.ca)"
DISTRICT_REL = 1606102
DISTRICT_NAME = "VII. kerület"
EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-22" / SITE
RAW = EVIDENCE / "raw"
LICENCES = EVIDENCE / "licences"
EU02 = ROOT / "openubem" / "outputs" / "eu02" / SITE
OSM_RAW = RAW / "osm_overpass"
ADMIN_RAW = RAW / "osm_overpass_admin"
KSH_RAW = RAW / "ksh_census2011_budapest"
KSH_URL = "https://www.ksh.hu/docs/hun/xftp/idoszaki/nepsz2011/nepsz_03_01_2011.pdf"
KSH_PDF = KSH_RAW / "nepsz_03_01_2011.pdf"
KSH_TEXT = KSH_RAW / "nepsz_03_01_2011.txt"
LICENCE = "ODbL 1.0, OpenStreetMap contributors (footprints, storeys, year); CC BY 4.0, KSH (Census 2011 table 3.3.2.1)"
CENSUS_UNIT_ID = "HU-BUD-VII"
OLDEST_CLASS_YEAR = 1944
CENSUS_PERIODS = [
    ("before 1946", "1946 előtt", OLDEST_CLASS_YEAR),
    ("1946-1960", "1946–1960", (1946 + 1960) // 2),
    ("1961-1970", "1961–1970", (1961 + 1970) // 2),
    ("1971-1980", "1971–1980", (1971 + 1980) // 2),
    ("1981-1990", "1981–1990", (1981 + 1990) // 2),
    ("1991-2000", "1991–2000", (1991 + 2000) // 2),
    ("2001-2005", "2001–2005", (2001 + 2005) // 2),
    ("2006-2011", "2006–2011", (2006 + 2011) // 2),
]
PERIOD_YEARS = {label: year for label, _, year in CENSUS_PERIODS}
MIN_YEAR, MAX_YEAR = 1500, 2026
LOW, HIGH = 500, 1000
BBOX_BUFFER_DEG = 0.004


def overpass_post(query: str, dest: Path, *, retries: int = 8) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last = ""
    for attempt in range(retries):
        try:
            response = requests.post(OVERPASS, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=600)
            if response.status_code == 200:
                dest.write_bytes(response.content)
                return dest
            last = f"HTTP {response.status_code}: {response.text[:300]}"
        except requests.RequestException as exc:
            last = f"{type(exc).__name__}: {exc}"
        print(f"{dest.name} attempt={attempt} {last}", file=sys.stderr)
        time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"{dest.name}: {last}")


def relation_polygon(payload: dict) -> Polygon:
    element = payload["elements"][0]
    outer, inner = [], []
    for member in element["members"]:
        if member["type"] != "way" or "geometry" not in member:
            continue
        line = LineString([(p["lon"], p["lat"]) for p in member["geometry"]])
        (inner if member.get("role") == "inner" else outer).append(line)
    outer_poly = unary_union(list(polygonize(unary_union(outer))))
    if outer_poly.is_empty:
        raise ValueError("Relation outer ways do not close into a polygon")
    inner_poly = unary_union(list(polygonize(unary_union(inner)))) if inner else None
    return outer_poly.difference(inner_poly) if inner_poly is not None and not inner_poly.is_empty else outer_poly


def plain_year(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not re.fullmatch(r"\d{4}", text):
        return None
    year = int(text)
    return year if MIN_YEAR <= year <= MAX_YEAR else None


def map_osm_frame(raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    frame = _flatten_tags(raw)
    start = frame["start_date"] if "start_date" in frame.columns else pd.Series([None] * len(frame), index=frame.index)
    frame["year_built"] = pd.array([plain_year(v) for v in start], dtype="Int64")
    return frame


def parse_census_page(page: str) -> dict[str, int]:
    tokens_by_line = []
    for line in page.splitlines():
        tokens = re.findall(r"\d{1,3}(?: \d{3})*|–", line)
        tokens_by_line.append([0 if t == "–" else int(t.replace(" ", "")) for t in tokens])
    page_tokens = {n for tokens in tokens_by_line for n in tokens}
    windows: dict[tuple, int] = {}
    for tokens in tokens_by_line:
        for i in range(len(tokens) - len(CENSUS_PERIODS) + 1):
            window = tuple(tokens[i : i + len(CENSUS_PERIODS)])
            if sum(window) in page_tokens and sum(window) > 0:
                windows[window] = windows.get(window, 0) + 1
    repeated = [w for w, n in windows.items() if n >= 3]
    if not repeated:
        raise ValueError("No repeated 8-column total row found on the district page")
    best = max(repeated, key=sum)
    return {label: int(value) for (label, _, _), value in zip(CENSUS_PERIODS, best)}


def census_page_for(text: str, district: str = DISTRICT_NAME) -> str:
    pattern = re.compile(r"(?<![XVI])" + re.escape(district))
    hits = [p for p in text.split("\f") if pattern.search(p) and "1946 előtt" in p and "3.3.2.1" in p]
    if len(hits) != 1:
        raise ValueError(f"Expected exactly one table 3.3.2.1 construction-year page for {district}, found {len(hits)}")
    return hits[0]


def attach_census(frame: gpd.GeoDataFrame, district_geom, counts: dict[str, int]) -> gpd.GeoDataFrame:
    out = frame.copy()
    inside = out.geometry.representative_point().within(district_geom)
    payload = json.dumps(counts, ensure_ascii=False)
    out["census_unit_id"] = [CENSUS_UNIT_ID if i else "" for i in inside]
    out["census_period_counts"] = [payload if i else "" for i in inside]
    return out


def residential_crosswalk() -> dict[str, str]:
    table = json.loads((ROOT / "openubem" / "data" / "osm_to_use_class.json").read_text(encoding="utf-8"))["tag_to_use_class"]
    return {tag: ("residential" if use == "residential" else "non_residential") for tag, use in table.items()}


def select_units(residential_in_district: int) -> dict:
    steps = [{"unit": f"{DISTRICT_NAME} (OSM relation {DISTRICT_REL})", "residential": residential_in_district, "running_total": residential_in_district}]
    if LOW <= residential_in_district <= HIGH:
        return {"mode": "whole_district", "units": [s["unit"] for s in steps], "steps": steps, "total": residential_in_district}
    return {"mode": "out_of_range", "units": [], "steps": steps, "total": residential_in_district}


def coverage(res: gpd.GeoDataFrame) -> dict:
    n = len(res)
    pct = lambda s: round(100.0 * float(s) / n, 2) if n else 0.0
    levels = res["levels"].notna()
    height = res["height_m"].notna() & (res["height_m"] > 0)
    year = res["year_built"].notna()
    tags = res["building_tag"].value_counts().to_dict()
    return {
        "n": n,
        "storeys_rung_1_osm_building_levels": {"count": int(levels.sum()), "pct": pct(levels.sum())},
        "storeys_rung_2_urban_atlas_height_2012": {"count": 0, "pct": 0.0, "status": "skipped: download needs an EU Login / API token"},
        "storeys_rung_3_osm_height_tag_over_3": {"count": int((~levels & height).sum()), "pct": pct((~levels & height).sum())},
        "storeys_left_for_neighbour_imputation": {"count": int((~levels & ~height).sum()), "pct": pct((~levels & ~height).sum())},
        "height_tag_any": {"count": int(height.sum()), "pct": pct(height.sum())},
        "year_osm_start_date_plain_year": {"count": int(year.sum()), "pct": pct(year.sum())},
        "year_left_for_census_period": {"count": int((~year).sum()), "pct": pct((~year).sum())},
        "census_unit_id_non_null": {"count": int((res["census_unit_id"] != "").sum()), "pct": pct((res["census_unit_id"] != "").sum())},
        "building_tag_counts": {str(k): int(v) for k, v in tags.items()},
        "type_from_tag": {"count": int(res["building_tag"].isin(["apartments", "detached", "terrace"]).sum()), "pct": pct(res["building_tag"].isin(["apartments", "detached", "terrace"]).sum())},
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def page_text(url: str) -> tuple[int, str]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
    body = re.sub(r"<style.*?</style>|<script.*?</script>", "", response.text, flags=re.S)
    return response.status_code, html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))).strip()


def write_licences(downloaded_at: str, osm_base: str) -> None:
    LICENCES.mkdir(parents=True, exist_ok=True)
    sources = {
        "OSM_ODbL.txt": [
            ("https://www.openstreetmap.org/copyright", 5000),
            ("https://opendatacommons.org/licenses/odbl/summary/", 5000),
        ],
        "KSH_census2011.txt": [("https://www.ksh.hu/copyright", 6000)],
        "KSH_census2022_terms.txt": [("https://nepszamlalas2022.ksh.hu/felhasznalasi-feltetelek", 6000)],
    }
    heads = {
        "OSM_ODbL.txt": [f"source: OpenStreetMap buildings and district boundary through Overpass API {OVERPASS}", f"overpass data timestamp (osm_base): {osm_base}", "required attribution: © OpenStreetMap contributors, ODbL 1.0"],
        "KSH_census2011.txt": [f"source: {KSH_URL}", "table: 3.3.2.1 occupied dwellings by construction year, Budapest districts, Census 2011", "licence statement of ksh.hu content: CC BY 4.0 (page below)", "required attribution: Source: KSH, Census 2011"],
        "KSH_census2022_terms.txt": ["source: https://nepszamlalas2022.ksh.hu (only consulted; no table from it is used, see acquisition_report.json census_2022_check)", "licence statement: CC BY 4.0 (page below)"],
    }
    for name, urls in sources.items():
        lines = [f"download date: {downloaded_at}"] + heads[name] + [""]
        for url, limit in urls:
            status, text = page_text(url)
            lines += [f"licence page: {url} (HTTP {status})", text[:limit], ""]
        (LICENCES / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    copernicus = [
        f"download date: {downloaded_at}",
        "source: Copernicus Urban Atlas Building Block Height 2012 (raster 10 m), https://land.copernicus.eu/en/products/urban-atlas/building-height-2012",
        "status: NOT DOWNLOADED. The CLMS download API answers 401 Unauthorized without a token (raw/copernicus_urban_atlas_building_height_2012/anonymous_api_probe.txt); the documentation (clms_api_download_docs.html) requires 'Authorization: Bearer' on every download call.",
    ]
    (LICENCES / "COPERNICUS_UA_BUILDING_HEIGHT_2012_not_downloaded.txt").write_text("\n".join(copernicus) + "\n", encoding="utf-8")


def osm_base_of(path: Path) -> str:
    head = path.read_bytes()[:4000].decode("utf-8", errors="replace")
    match = re.search(r'osm_base="([^"]+)"', head)
    return match.group(1) if match else ""


def run(refresh: bool = False) -> dict:
    downloaded_at = datetime.now(timezone.utc).isoformat()
    boundary_json = ADMIN_RAW / "district_VII_rel1606102.json"
    if refresh or not boundary_json.exists():
        overpass_post(f"[out:json][timeout:120];rel({DISTRICT_REL});out geom;", boundary_json)
    probe_sub = ADMIN_RAW / "subunits_inside_VII.json"
    if refresh or not probe_sub.exists():
        overpass_post(f"[out:json][timeout:120];rel({DISTRICT_REL});map_to_area->.a;rel(area.a)[\"boundary\"=\"administrative\"];out tags;", probe_sub)
    probe_name = ADMIN_RAW / "name_search_belso_kulso_erzsebetvaros.json"
    if refresh or not probe_name.exists():
        overpass_post("[out:json][timeout:120];rel[\"name\"~\"Bels.*Erzs|K.ls.*Erzs\"](47.40,18.95,47.60,19.25);out tags;", probe_name)
    payload = json.loads(boundary_json.read_text(encoding="utf-8"))
    district = relation_polygon(payload)
    west, south, east, north = district.bounds
    bbox = (south - BBOX_BUFFER_DEG, west - BBOX_BUFFER_DEG, north + BBOX_BUFFER_DEG, east + BBOX_BUFFER_DEG)
    xml_path = OSM_RAW / "buildings_district_VII_bbox.osm"
    if refresh or not xml_path.exists():
        s, w, n, e = bbox
        overpass_post(f"[out:xml][timeout:600][bbox:{s:.6f},{w:.6f},{n:.6f},{e:.6f}];(way[\"building\"];rel[\"building\"];);(._;>;);out;", xml_path)
    if refresh or not KSH_PDF.exists():
        KSH_RAW.mkdir(parents=True, exist_ok=True)
        response = requests.get(KSH_URL, headers={"User-Agent": USER_AGENT}, timeout=300)
        response.raise_for_status()
        KSH_PDF.write_bytes(response.content)
    if refresh or not KSH_TEXT.exists():
        exe = shutil.which("pdftotext")
        if exe is None:
            raise RuntimeError("pdftotext not found on PATH")
        subprocess.run([exe, "-layout", "-enc", "UTF-8", str(KSH_PDF), str(KSH_TEXT)], check=True)
    osm_base = osm_base_of(xml_path)
    write_licences(downloaded_at, osm_base)

    counts = parse_census_page(census_page_for(KSH_TEXT.read_text(encoding="utf-8")))
    raw = ox.features.features_from_xml(xml_path, tags={"building": True})
    frame = map_osm_frame(raw)
    clean = finalize_footprints(frame, source="OSM", output_dir=EU02)
    if clean.crs.to_string() != EXPECTED_CRS:
        raise ValueError(f"CRS {clean.crs} != {EXPECTED_CRS}")
    district_utm = gpd.GeoSeries([district], crs="EPSG:4326").to_crs(clean.crs).iloc[0]
    clean = attach_census(clean, district_utm, counts)

    boundary = gpd.GeoDataFrame({"site": [SITE], "units": [f"{DISTRICT_NAME} OSM relation {DISTRICT_REL}"]}, geometry=[district], crs="EPSG:4326")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    boundary_path = EVIDENCE / "boundary.geojson"
    boundary.to_file(boundary_path, driver="GeoJSON")
    sha = sha256_file(boundary_path)
    (EVIDENCE / "boundary.sha256").write_text(sha + "\n", encoding="utf-8")
    clipped = clip_to_boundary(clean, boundary_path, verify_sha256=sha)
    residential, excluded, split_counts = split_residential(clipped, residential_crosswalk(), class_column="building_tag")
    selection = select_units(int(len(residential)))
    report = {
        "site": SITE, "retrieved_at_utc": downloaded_at, "osm_base_timestamp": osm_base, "crs": clean.crs.to_string(), "licence": LICENCE,
        "n_osm_features_parsed": int(len(raw)), "n_clean": int(len(clean)), "n_clipped": int(len(clipped)), "split_counts": split_counts,
        "subunits": selection, "coverage_residential": coverage(residential), "period_years": PERIOD_YEARS,
        "census_table": {"url": KSH_URL, "file": str(KSH_PDF.relative_to(ROOT)), "sha256": sha256_file(KSH_PDF), "table": "3.3.2.1", "unit": DISTRICT_NAME, "census_unit_id": CENSUS_UNIT_ID, "period_counts": counts, "total_dwellings": sum(counts.values()), "labels_source": {label: src for label, src, _ in CENSUS_PERIODS}},
        "census_2022_check": "Census 2022 database (nepszamlalas2022.ksh.hu/api/index/V67/hu) offers construction period (CL_EPEV_POC1) only at district-of-country (járás/Budapest district, WBL001) and county/settlement-type level; the static tables (nsz2022-1.3.3.xlsx) are county level without construction period. No table by smaller area than district VII exists, so Census 2011 table 3.3.2.1 is used.",
        "urban_atlas_height_2012": "skipped: CLMS download API returns 401 Unauthorized without an EU Login token",
        "osm_sub_units": "OSM has no Belső-/Külső-Erzsébetváros boundary; only relation 3229918 (Erzsébetváros, admin_level 10) lies inside relation 1606102 (VII. kerület, admin_level 9). See raw/osm_overpass_admin/subunits_inside_VII.json and name_search_belso_kulso_erzsebetvaros.json.",
        "boundary_sha256": sha, "raw_sha256": {"osm_xml": sha256_file(xml_path), "district_json": sha256_file(boundary_json)},
        "residential_rule": "building_tag in openubem/data/osm_to_use_class.json tag_to_use_class with value residential (same crosswalk as Madrid and London); 'yes' and empty tags are unknown and excluded",
    }
    if selection["mode"] == "whole_district":
        write_manifests(residential, excluded, split_counts, EU02, neighbourhood_id=SITE, source_endpoint=OVERPASS, licence=LICENCE, source_layer="OpenStreetMap building features, relation 1606102")
    (EVIDENCE / "acquisition_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    report = run(refresh=parser.parse_args(argv).refresh)
    print(json.dumps({k: report[k] for k in ("n_osm_features_parsed", "n_clean", "n_clipped", "split_counts", "subunits", "coverage_residential")}, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
