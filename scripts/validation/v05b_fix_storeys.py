"""V05b: Fix storey-count metadata, regenerate counterpart IDFs, simulate on cluster.

Three modes:
  --fix-storeys   : derive correct storey counts from IDF geometry, write corrected
                    ref_inventory.csv (adds storeys_heuristic column), re-run V04.
  --submit        : pack corrected counterpart IDFs + EPW -> fleets/val2d/ and sbatch.
  --report        : fetch results + regenerate roundtrip_report.csv/.md (both storeys columns).
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

REF_DIR = REPO / "docs" / "validations" / "Level 2 DOE round-trip" / "00.BaselineBuildings_NUs"
OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"
INVENTORY_CSV = OUT_BASE / "ref_inventory.csv"
INVENTORY_CORRECTED_CSV = OUT_BASE / "ref_inventory_corrected.csv"
COUNTERPARTS_DIR_2D = OUT_BASE / "counterparts_2d"
MAPPING_CSV = OUT_BASE / "mapping.csv"
RESULTS_DIR = REPO / "docs" / "validations" / "overAll" / "results"
REF_EUI_PARQUET = OUT_BASE / "reference_eui.parquet"
REPORT_CSV = RESULTS_DIR / "roundtrip_report.csv"
REPORT_MD = RESULTS_DIR / "roundtrip_report.md"
JOB_ID_FILE = OUT_BASE / "val2d_job_id.txt"

REMOTE = "o_iseri@speed.encs.concordia.ca"
REMOTE_BASE = "/speed-scratch/o_iseri/openubem"
REMOTE_FLEET = f"{REMOTE_BASE}/fleets/val2d"
REMOTE_SBATCH = f"{REMOTE_BASE}/scripts/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"

THROTTLE = 32
TIME_LIMIT = "01:30:00"
GJ_TO_KWH = 1e9 / 3.6e6
FUEL_COLS = ["Electricity", "Natural Gas", "Additional Fuel", "District Cooling",
             "District Heating", "District Heating Water", "District Heating Steam", "Steam", "Water"]

DOE_PROTOTYPE_STOREYS: dict[str, int] = {
    "ApartmentHighRise": 10,
    "ApartmentMidRise": 4,
    "DataCenterLargeHighITE": 1,
    "DataCenterLargeLowITE": 1,
    "Hospital": 5,
    "HotelLarge": 6,
    "HotelSmall": 4,
    "OfficeLarge": 12,
    "OfficeMedium": 3,
    "OfficeSmall": 1,
    "OutPatientHealthCare": 3,
    "RestaurantFastFood": 1,
    "RestaurantSitDown": 1,
    "RetailStandalone": 1,
    "RetailStripmall": 1,
    "Warehouse": 1,
    "Laboratory": 5,
    "SmallDataCenterHighITE": 1,
    "SmallDataCenterLowITE": 1,
    "Supermarket": 1,
    "SuperTallBuilding": 72,
    "TallBuilding": 38,
    "College": 4,
}


def _parse_idf(idf_path: Path) -> list[list[str]]:
    txt = idf_path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.split("!")[0].strip() for ln in txt.splitlines()]
    clean = " ".join(l for l in lines if l)
    return [[f.strip() for f in o.strip().split(",")] for o in clean.split(";") if o.strip()]


def _derive_storeys(objects: list[list[str]], btype: str) -> tuple[int, str]:
    zone_names = [f[1] for f in objects if f[0].upper() == "ZONE" and len(f) > 1]

    pat_flr_suffix = re.compile(r"_Flr_(\d+)", re.IGNORECASE)
    floor_nums_flr = set()
    for zn in zone_names:
        m = pat_flr_suffix.search(zn)
        if m:
            floor_nums_flr.add(int(m.group(1)))
    if floor_nums_flr:
        return max(floor_nums_flr), f"_Flr_N zone names; max={max(floor_nums_flr)}"

    pat_flr_compact = re.compile(r"Flr(\d+)", re.IGNORECASE)
    floor_nums_compact = set()
    for zn in zone_names:
        m = pat_flr_compact.search(zn)
        if m:
            floor_nums_compact.add(int(m.group(1)))
    if floor_nums_compact:
        return max(floor_nums_compact), f"FlrN zone names; max={max(floor_nums_compact)}"

    pat_fprefix = re.compile(r"^F(\d+)\s", re.IGNORECASE)
    floor_nums_fp = set()
    for zn in zone_names:
        m = pat_fprefix.match(zn)
        if m:
            floor_nums_fp.add(int(m.group(1)))
    if floor_nums_fp:
        return max(floor_nums_fp), f"F{{N}} zone prefix; max={max(floor_nums_fp)}"

    pat_floor_word = re.compile(r"Floor (\d+)", re.IGNORECASE)
    floor_nums_fw = set()
    for zn in zone_names:
        m = pat_floor_word.search(zn)
        if m:
            floor_nums_fw.add(int(m.group(1)))
    if floor_nums_fw:
        return max(floor_nums_fw), f"'Floor N' zone names; max={max(floor_nums_fw)}"

    pat_fn = re.compile(r"_F(\d+)", re.IGNORECASE)
    floor_nums_fn = set()
    for zn in zone_names:
        m = pat_fn.search(zn)
        if m:
            floor_nums_fn.add(int(m.group(1)))
    if floor_nums_fn:
        return max(floor_nums_fn), f"_FN zone names; max={max(floor_nums_fn)}"

    if btype in DOE_PROTOTYPE_STOREYS:
        n = DOE_PROTOTYPE_STOREYS[btype]
        return n, f"documented DOE prototype (no explicit floor in zone names)"

    return 1, "fallback=1 (no floor pattern found)"


def fix_storeys() -> None:
    inv = pd.read_csv(INVENTORY_CSV)
    print(f"[V05b-fix] Loaded inventory: {len(inv)} rows")

    corrected_rows = []
    conflicts = []

    for _, row in inv.iterrows():
        fname = str(row["filename"])
        btype = str(row["building_type"])
        heuristic_storeys = int(row["storeys"])

        idf_path = REF_DIR / fname
        if not idf_path.exists():
            corrected_rows.append({**row.to_dict(), "storeys_heuristic": heuristic_storeys, "storeys_derived": heuristic_storeys, "storeys_method": "file_not_found"})
            continue

        objects = _parse_idf(idf_path)
        geom_storeys, method = _derive_storeys(objects, btype)

        doc_storeys = DOE_PROTOTYPE_STOREYS.get(btype)
        if doc_storeys is not None and "documented DOE" not in method:
            if geom_storeys != doc_storeys:
                conflicts.append({
                    "building_type": btype,
                    "filename": fname,
                    "geometry_derived": geom_storeys,
                    "documented": doc_storeys,
                    "method": method,
                })

        new_row = row.to_dict()
        new_row["storeys_heuristic"] = heuristic_storeys
        new_row["storeys"] = geom_storeys
        new_row["storeys_derived"] = geom_storeys
        new_row["storeys_method"] = method
        corrected_rows.append(new_row)

        marker = " **CHANGED**" if geom_storeys != heuristic_storeys else ""
        print(f"  {btype:<35} heur={heuristic_storeys:>4}  derived={geom_storeys:>4}  [{method}]{marker}")

    if conflicts:
        print("\n[V05b-fix] CONFLICTS between geometry-derived and documented storey counts:")
        for c in conflicts:
            print(f"  {c['building_type']}: geometry={c['geometry_derived']} vs documented={c['documented']} (method: {c['method']})")
        print("\n[V05b-fix] STOP — conflicts detected. Manager must rule.")
        sys.exit(3)

    cols = ["filename", "version", "building_type", "vintage", "conditioned_floor_area_m2",
            "storeys", "storeys_heuristic", "storeys_derived", "storeys_method",
            "has_hvactemplate", "smoke_status"]
    corrected_df = pd.DataFrame(corrected_rows)[cols]
    corrected_df.to_csv(INVENTORY_CORRECTED_CSV, index=False)
    corrected_df.to_csv(RESULTS_DIR / "ref_inventory.csv", index=False)
    print(f"\n[V05b-fix] Corrected inventory written: {INVENTORY_CORRECTED_CSV}")
    print(f"[V05b-fix] Copy written: {RESULTS_DIR / 'ref_inventory.csv'}")

    changed = [(r["building_type"], r["storeys_heuristic"], r["storeys"]) for r in corrected_rows
               if r["storeys_heuristic"] != r["storeys"]]
    print(f"\n[V05b-fix] {len(changed)} buildings with corrected storey count:")
    for btype, h, c in changed:
        print(f"  {btype:<35} {h} -> {c}")

    _run_v04_corrected()


def _run_v04_corrected() -> None:
    print("\n[V05b-fix] Running V04 counterpart generation with corrected storeys...")
    import math
    import warnings

    import geopandas as gpd
    import numpy as np
    from shapely.geometry import Polygon

    inv = pd.read_csv(INVENTORY_CORRECTED_CSV)

    ARCHETYPE_MAP: dict[str, str] = {
        "OfficeMedium": "MediumOffice",
        "OfficeLarge": "LargeOffice",
        "OfficeSmall": "SmallOffice",
        "ApartmentHighRise": "HighriseApartment",
        "ApartmentMidRise": "MidriseApartment",
        "TallBuilding": "TallBuilding",
        "SuperTallBuilding": "SuperTallBuilding",
        "College": "College",
        "OutPatientHealthCare": "Outpatient",
        "Hospital": "Hospital",
        "RestaurantFastFood": "QuickServiceRestaurant",
        "RestaurantSitDown": "FullServiceRestaurant",
        "RetailStandalone": "RetailStandalone",
        "RetailStripmall": "RetailStripmall",
        "Warehouse": "Warehouse",
        "HotelSmall": "SmallHotel",
        "HotelLarge": "LargeHotel",
        "SchoolPrimary": "PrimarySchool",
        "SchoolSecondary": "SecondarySchool",
        "Supermarket": "SuperMarket",
        "Laboratory": "Laboratory",
        "SmallDataCenterHighITE": "SmallDataCenterHighITE",
        "SmallDataCenterLowITE": "SmallDataCenterLowITE",
        "DataCenterLargeHighITE": "LargeDataCenterHighITE",
        "DataCenterLargeLowITE": "LargeDataCenterLowITE",
    }

    NOT_MAPPED_50PCT = {
        "ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled",
        "ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled",
        "ASHRAE901_Warehouse_STD2022_Buffalo_50pct_downscaled",
    }
    NOT_MAPPED_BTYPES = {
        "AttachedHouse+CZ6A+IECC+2024",
        "DetachedHouse+CZ6A+IECC+2024",
        "MT5_HPE_NV_ECW_LED Small_Retail",
        "HighRise_ST15",
        "HighRise_ST20",
    }

    BUFFALO_LAT = 42.94
    BUFFALO_LON = -78.73
    BUFFALO_CZ = "6A"
    epw_path = (OUT_BASE / "epw_path.txt").read_text().strip()

    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    build_rows = []
    ref_stems = []
    osm_counter = 91001

    for _, row in inv.iterrows():
        fname = str(row["filename"])
        stem = fname.replace(".idf", "")
        btype = str(row["building_type"])
        floor_area = float(row["conditioned_floor_area_m2"])
        storeys = int(row["storeys"])

        if stem in NOT_MAPPED_50PCT:
            continue
        if btype in NOT_MAPPED_BTYPES:
            continue
        if btype not in ARCHETYPE_MAP:
            continue

        archetype_id = ARCHETYPE_MAP[btype]
        storeys = max(1, storeys)
        footprint_area = floor_area / storeys
        side = math.sqrt(footprint_area)
        perimeter = 4 * side
        height_m = storeys * 3.5
        geom = Polygon([(0, 0), (side, 0), (side, side), (0, side)])

        syn_row = {
            "geometry": geom,
            "osm_id": osm_counter,
            "crs_utm": "EPSG:32617",
            "building_tag": "yes",
            "function_tag": pd.NA,
            "levels": pd.array([storeys], dtype="Int64")[0],
            "height_m": float(height_m),
            "year_built": pd.array([2019], dtype="Int64")[0],
            "postcode": pd.NA,
            "underground": pd.array([0], dtype="Int64")[0],
            "roof_shape": "flat",
            "roof_height_m": float(height_m),
            "footprint_area_m2": float(footprint_area),
            "perimeter_m": float(perimeter),
            "surplus_tags": "{}",
            "provenance_levels": "SYNTHETIC",
            "provenance_height_m": "SYNTHETIC",
            "provenance_year_built": "SYNTHETIC",
            "provenance_building_tag": "SYNTHETIC",
            "provenance_function_tag": "SYNTHETIC",
            "provenance_postcode": "SYNTHETIC",
            "provenance_geometry": "SYNTHETIC",
            "data_quality_flag": "",
            "archetype_id": archetype_id,
            "archetype_confidence": 1.0,
            "archetype_source": "VALIDATION_FORCED",
            "climate_zone": BUFFALO_CZ,
            "epw_path": epw_path,
            "provenance_climate_zone": "ASHRAE_STANDARD",
        }
        build_rows.append(syn_row)
        ref_stems.append(stem)
        osm_counter += 1

    schema_cols = [
        "geometry", "osm_id", "crs_utm", "building_tag", "function_tag", "levels", "height_m",
        "year_built", "postcode", "underground", "roof_shape", "roof_height_m",
        "footprint_area_m2", "perimeter_m", "surplus_tags",
        "provenance_levels", "provenance_height_m", "provenance_year_built",
        "provenance_building_tag", "provenance_function_tag", "provenance_postcode",
        "provenance_geometry", "data_quality_flag",
        "archetype_id", "archetype_confidence", "archetype_source",
        "climate_zone", "epw_path", "provenance_climate_zone",
    ]

    gdf_raw = gpd.GeoDataFrame(build_rows, crs="EPSG:32617")[schema_cols]
    gdf_raw["levels"] = gdf_raw["levels"].astype("Int64")
    gdf_raw["year_built"] = gdf_raw["year_built"].astype("Int64")
    gdf_raw["underground"] = gdf_raw["underground"].astype("Int64")
    gdf_raw["climate_zone"] = pd.Categorical(gdf_raw["climate_zone"], categories=_CLIMATE_ZONE_VOCAB)
    gdf_raw["provenance_climate_zone"] = pd.Categorical(
        gdf_raw["provenance_climate_zone"], categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )

    print(f"[V05b-fix] Enriching {len(gdf_raw)} buildings...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf_enriched, schedule_lib = enrich_semantics(gdf_raw, random_seed=42)

    COUNTERPARTS_DIR_2D.mkdir(parents=True, exist_ok=True)
    from openubem.idf.builder import run_step3
    print(f"[V05b-fix] Generating IDFs -> {COUNTERPARTS_DIR_2D}")
    manifest = run_step3(gdf_enriched, schedule_lib, COUNTERPARTS_DIR_2D)
    success = (manifest["generation_status"] == "success").sum()
    print(f"[V05b-fix] {success}/{len(manifest)} IDFs generated")

    fail_mask = manifest["generation_status"] != "success"
    if fail_mask.any():
        print("[V05b-fix] FAILURES:")
        print(manifest[fail_mask][["osm_id", "archetype_id", "generation_status"]].to_string())
        sys.exit(1)

    idf_dir = COUNTERPARTS_DIR_2D / "idfs"
    for osm_id, stem in zip(gdf_enriched["osm_id"], ref_stems):
        src = idf_dir / f"{osm_id}.idf"
        dst = idf_dir / f"{stem}_counterpart.idf"
        if src.exists() and not dst.exists():
            src.rename(dst)

    manifest["ref_stem"] = ref_stems
    manifest["ref_filename"] = [s + ".idf" for s in ref_stems]
    manifest.to_parquet(COUNTERPARTS_DIR_2D / "03_idf_manifest.parquet", index=False)
    print(f"[V05b-fix] Manifest written: {COUNTERPARTS_DIR_2D / '03_idf_manifest.parquet'}")
    print("[V05b-fix] Counterpart generation DONE")


def _ssh(cmd: str, check: bool = True, timeout: int = 60) -> str:
    result = subprocess.run(
        ["ssh", REMOTE, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout, check=check,
    )
    return result.stdout.strip()


def submit() -> None:
    manifest = pd.read_parquet(COUNTERPARTS_DIR_2D / "03_idf_manifest.parquet")
    idf_dir = COUNTERPARTS_DIR_2D / "idfs"
    stems = [str(r["ref_stem"]) for _, r in manifest.iterrows() if r["generation_status"] == "success"]
    n = len(stems)
    print(f"[V05b-submit] {n} counterpart IDFs to submit to fleets/val2d/")

    wx_dir = OUT_BASE / "weather"
    fleet_lst = OUT_BASE / "fleet_val2d.lst"
    idf_names = [s + "_counterpart" for s in stems]
    fleet_lst.write_bytes(("\n".join(idf_names) + "\n").encode("utf-8"))

    tarball = OUT_BASE / "val2d.tar.gz"
    print(f"[V05b-submit] Packing tarball: {tarball}")
    with tarfile.open(tarball, "w:gz") as tf:
        for name in idf_names:
            src = idf_dir / f"{name}.idf"
            if src.exists():
                tf.add(src, arcname=f"idfs/{name}.idf")
        tf.add(wx_dir, arcname="weather")
        tf.add(fleet_lst, arcname="fleet.lst")

    _ssh(f"mkdir -p {REMOTE_FLEET}")
    subprocess.run(["scp", str(tarball), f"{REMOTE}:{REMOTE_FLEET}/val2d.tar.gz"], check=True)
    _ssh(f"cd {REMOTE_FLEET} && tar -xzf val2d.tar.gz && rm val2d.tar.gz")
    subprocess.run(["scp", str(SBATCH_LOCAL), f"{REMOTE}:{REMOTE_BASE}/scripts/submit_fleet.sbatch"], check=True)

    sbatch_out = subprocess.run(
        ["ssh", REMOTE,
         f"bash -lc 'sbatch --array=1-{n}%{THROTTLE} --time={TIME_LIMIT} "
         f"--export=FLEET_DIR={REMOTE_FLEET} {REMOTE_SBATCH}'"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"[V05b-submit] sbatch output: {sbatch_out}")
    job_id = sbatch_out.split()[-1]
    JOB_ID_FILE.write_text(job_id)
    print(f"[V05b-submit] Job ID: {job_id}")
    print(f"[V05b-submit] Monitor: ssh {REMOTE} \"bash -lc 'squeue -j {job_id}'\"")
    print("[V05b-submit] DONE")


def _poll_jobs(job_id: str, interval_s: int = 90) -> None:
    while True:
        time.sleep(interval_s)
        out = _ssh(f"squeue -j {job_id} --noheader 2>/dev/null | wc -l", check=False)
        pending = int(out.strip()) if out.strip().isdigit() else 0
        print(f"  [poll] squeue: {pending} tasks still queued/running")
        if pending == 0:
            break
    print("[V05b-poll] All tasks left the queue.")


def _query_eui(sql_path: Path, floor_area: float) -> dict[str, float] | None:
    if not sql_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        rows = conn.execute("""
            SELECT RowName, ColumnName, CAST(Value AS REAL)
            FROM TabularDataWithStrings
            WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
              AND TableName = 'End Uses'
              AND Units = 'GJ'
        """).fetchall()
        conn.close()
    except Exception:
        return None

    totals: dict[str, float] = {}
    for row_name, col_name, val in rows:
        if col_name not in FUEL_COLS:
            continue
        totals[row_name] = totals.get(row_name, 0.0) + (val or 0.0)

    def _eui(rn: str) -> float:
        return totals.get(rn, 0.0) * GJ_TO_KWH / floor_area

    heat = _eui("Heating")
    cool = _eui("Cooling")
    light = _eui("Interior Lighting")
    equip = _eui("Interior Equipment")
    known = {"Heating", "Cooling", "Interior Lighting", "Interior Equipment"}
    other = sum(v for k, v in totals.items() if k not in known) * GJ_TO_KWH / floor_area
    total = heat + cool + light + equip + other
    return {"heat": heat, "cool": cool, "light": light, "equip": equip, "other": other, "total": total}


def _diagnose_failed(name: str, out_dir: Path) -> str:
    err_path = out_dir / "eplusout.err"
    if not err_path.exists():
        return "no_err_file"
    txt = err_path.read_text(errors="replace")
    tail = txt[-3000:]
    if "CalcHeatBalanceInsideSurf" in txt or "Temperature out of bounds" in txt:
        return "thermal_runaway"
    if "Severe" in txt or "Fatal" in txt:
        lines = [l for l in txt.splitlines() if "** Severe" in l or "** Fatal" in l]
        return "; ".join(lines[-3:])
    return "unknown_failure"


def report(job_id: str, poll: bool = False) -> None:
    if poll and job_id:
        _poll_jobs(job_id)

    val2d_out = OUT_BASE / "val2d_out"
    val2d_out.mkdir(parents=True, exist_ok=True)

    fleet_lst_text = _ssh(f"cat {REMOTE_FLEET}/fleet.lst", check=False)
    stems = [l.strip() for l in fleet_lst_text.splitlines() if l.strip()]
    n = len(stems)
    print(f"[V05b-report] Fetching {n} results from cluster (fleets/val2d/)...")

    success_count, failed = 0, []
    for i, name in enumerate(stems, 1):
        bdir = val2d_out / name
        bdir.mkdir(exist_ok=True)
        for f in ("eplusout.sql", "eplusout.err", "eplusout.end"):
            subprocess.run(
                ["scp", "-q",
                 f"{REMOTE}:{REMOTE_FLEET}/out/{name}/{f}",
                 str(bdir / f)],
                capture_output=True, text=True, timeout=120,
            )
        end_path = bdir / "eplusout.end"
        if end_path.exists() and "Completed Successfully" in end_path.read_text(errors="replace"):
            success_count += 1
        else:
            failed.append(name)
            diag = _diagnose_failed(name, bdir)
            print(f"  FAILED: {name} -- {diag}")
        if i % 5 == 0 or i == n:
            print(f"  fetched {i}/{n}  success={success_count}  fail={len(failed)}")

    print(f"\n[V05b-report] Fetch: {success_count}/{n} success  {len(failed)} failed")

    if failed and job_id:
        sacct = _ssh(f"sacct -j {job_id} --format=JobID,JobName,State,ExitCode --noheader 2>&1 | head -60", check=False)
        print(f"\nsacct summary:\n{sacct}")

    inv_corrected = pd.read_csv(INVENTORY_CORRECTED_CSV)
    inv_orig = pd.read_csv(INVENTORY_CSV)
    mapping = pd.read_csv(MAPPING_CSV)
    ref_eui = pd.read_parquet(REF_EUI_PARQUET)
    manifest = pd.read_parquet(COUNTERPARTS_DIR_2D / "03_idf_manifest.parquet")

    ref_eui_idx = ref_eui.set_index("filename")
    inv_corr_idx = inv_corrected.set_index("filename")
    inv_orig_idx = inv_orig.set_index("filename")

    report_rows = []
    for _, mrow in manifest.iterrows():
        ref_stem = str(mrow["ref_stem"])
        ref_fname = ref_stem + ".idf"
        counter_name = ref_stem + "_counterpart"
        archetype = str(mrow["archetype_id"])

        inv_row_map = mapping[mapping["filename"] == ref_fname]
        if inv_row_map.empty:
            continue
        openuben_arch = inv_row_map.iloc[0]["openuben_archetype"]
        if openuben_arch == "NOT_MAPPED":
            continue

        if ref_fname in inv_corr_idx.index:
            floor_area = float(inv_corr_idx.loc[ref_fname, "conditioned_floor_area_m2"])
            storeys_corrected = int(inv_corr_idx.loc[ref_fname, "storeys"])
            storeys_heuristic = int(inv_corr_idx.loc[ref_fname, "storeys_heuristic"])
        else:
            floor_area = 1000.0
            storeys_corrected = 1
            storeys_heuristic = 1

        bdir = val2d_out / counter_name
        sql_path = bdir / "eplusout.sql"
        end_path = bdir / "eplusout.end"
        status = "failed"
        if end_path.exists() and "Completed Successfully" in end_path.read_text(errors="replace"):
            status = "success"

        if status == "failed":
            diag = _diagnose_failed(counter_name, bdir)
        else:
            diag = ""

        counter_eui = _query_eui(sql_path, floor_area) if status == "success" else None

        ref_total = float(ref_eui_idx.loc[ref_fname, "total_site_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_heat = float(ref_eui_idx.loc[ref_fname, "heating_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_cool = float(ref_eui_idx.loc[ref_fname, "cooling_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_light = float(ref_eui_idx.loc[ref_fname, "lighting_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_equip = float(ref_eui_idx.loc[ref_fname, "equipment_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None

        dev_pct = None
        verdict = "N/A"
        if counter_eui and ref_total:
            dev_pct = (counter_eui["total"] - ref_total) / ref_total * 100
            verdict = "PASS" if abs(dev_pct) <= 5.0 else "FAIL"
        elif status == "failed":
            verdict = "N/A"

        report_rows.append({
            "ref_filename": ref_fname,
            "openuben_archetype": openuben_arch,
            "storeys_heuristic": storeys_heuristic,
            "storeys_corrected": storeys_corrected,
            "ref_total_eui": ref_total,
            "counter_total_eui": counter_eui["total"] if counter_eui else None,
            "dev_pct": round(dev_pct, 2) if dev_pct is not None else None,
            "verdict_5pct": verdict,
            "ref_heat": ref_heat, "counter_heat": counter_eui["heat"] if counter_eui else None,
            "ref_cool": ref_cool, "counter_cool": counter_eui["cool"] if counter_eui else None,
            "ref_light": ref_light, "counter_light": counter_eui["light"] if counter_eui else None,
            "ref_equip": ref_equip, "counter_equip": counter_eui["equip"] if counter_eui else None,
            "counter_status": status,
            "failure_diag": diag,
        })

    report_df = pd.DataFrame(report_rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(REPORT_CSV, index=False)
    report_df.to_csv(OUT_BASE / "roundtrip_report_2d.csv", index=False)
    print(f"\n[V05b-report] Report CSV: {REPORT_CSV}")

    n_mapped = len(report_df)
    n_pass = (report_df["verdict_5pct"] == "PASS").sum()
    n_fail = (report_df["verdict_5pct"] == "FAIL").sum()
    n_na = (report_df["verdict_5pct"] == "N/A").sum()
    print(f"[V05b-report] {n_pass}/{n_mapped} PASS  {n_fail} FAIL  {n_na} N/A")

    md_lines = [
        "# Level-2 DOE Round-Trip Report (V05b — corrected storeys)",
        "",
        f"n_pass / n_mapped = **{n_pass} / {n_mapped}**  (+-5% gate, report-only per V-R5-5)",
        "",
        "Storeys_heuristic = original `_floor_count_from_zones` value (buggy for DOE prototypes).",
        "Storeys_corrected = geometry-derived from IDF zone names / documented DOE prototype counts.",
        "",
        "| Archetype | Stry_h | Stry_c | Ref EUI | OUB EUI | Dev% | Verdict | Ref-H | Ctr-H | Ref-C | Ctr-C | Ref-L | Ctr-L | Ref-E | Ctr-E |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in report_df.sort_values("openuben_archetype").iterrows():
        def _fmt(v):
            return f"{v:.1f}" if v is not None and str(v) != "nan" else "--"
        md_lines.append(
            f"| {r['openuben_archetype']} | {r['storeys_heuristic']} | {r['storeys_corrected']} | "
            f"{_fmt(r['ref_total_eui'])} | {_fmt(r['counter_total_eui'])} | "
            f"{_fmt(r['dev_pct'])} | {r['verdict_5pct']} | "
            f"{_fmt(r['ref_heat'])} | {_fmt(r['counter_heat'])} | "
            f"{_fmt(r['ref_cool'])} | {_fmt(r['counter_cool'])} | "
            f"{_fmt(r['ref_light'])} | {_fmt(r['counter_light'])} | "
            f"{_fmt(r['ref_equip'])} | {_fmt(r['counter_equip'])} |"
        )
    md_lines += [
        "",
        f"**Summary:** {n_pass}/{n_mapped} PASS, {n_fail} FAIL, {n_na} N/A",
        "",
        "N/A rows = simulation failed; see failure_diag column in CSV.",
    ]

    REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[V05b-report] Report MD: {REPORT_MD}")

    if len(report_df) > 0 and "dev_pct" in report_df.columns:
        top_dev = report_df.dropna(subset=["dev_pct"]).nlargest(5, "dev_pct")
        print("\n[V05b-report] Top positive deviations:")
        print(top_dev[["openuben_archetype", "storeys_corrected", "ref_total_eui", "counter_total_eui", "dev_pct", "verdict_5pct"]].to_string(index=False))
        top_neg = report_df.dropna(subset=["dev_pct"]).nsmallest(5, "dev_pct")
        print("\n[V05b-report] Top negative deviations:")
        print(top_neg[["openuben_archetype", "storeys_corrected", "ref_total_eui", "counter_total_eui", "dev_pct", "verdict_5pct"]].to_string(index=False))

    if n_na > 0:
        na_rows = report_df[report_df["verdict_5pct"] == "N/A"]
        print("\n[V05b-report] N/A (failed) counterparts:")
        print(na_rows[["openuben_archetype", "storeys_corrected", "counter_status", "failure_diag"]].to_string(index=False))

    print("[V05b-report] DONE")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix-storeys", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--poll", action="store_true", help="Poll until job finishes before fetching")
    parser.add_argument("--job-id", default="")
    args = parser.parse_args()

    if not any([args.fix_storeys, args.submit, args.report]):
        parser.print_help()
        sys.exit(1)

    if args.fix_storeys:
        fix_storeys()

    if args.submit:
        submit()

    if args.report:
        job_id = args.job_id
        if not job_id and JOB_ID_FILE.exists():
            job_id = JOB_ID_FILE.read_text().strip()
        report(job_id, poll=args.poll)


if __name__ == "__main__":
    main()
