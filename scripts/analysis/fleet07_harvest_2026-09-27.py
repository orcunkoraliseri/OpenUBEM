"""FLEET-07d harvest (PLAN_techtransfer-block7-fleet07-2026-09-26.md, Task FLEET-07d).

Copied from scripts/analysis/fleet06c_harvest_2026-09-24.py and adapted so each case's
simulation folder is picked per-row: fleet07_out_2026-09-26/out/<cell>/<stem> if that
(cell, stem) pair is in manifest_changed.csv, otherwise the untouched
fleet06b_local_2026-09-18/out/<cell>/<stem> (unchanged IDFs give unchanged results).

Baseline is never harvested here: it is reused as-is from fleet06c_harvest_2026-09-24/baseline/
by the table script. Only the 7 non-baseline scenario cells run through this script.

Geo cells run in a 12-way process pool per scenario cell, never a serial loop.
"""
from __future__ import annotations

import argparse
import gzip
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

from scripts.validation.v12_cell_pipeline import step2_classify_enrich  # noqa: E402

T08_CSV = REPO / "openubem" / "outputs" / "comparisons" / "t08_restated_fleet_eui_2026-09-10.csv"
REBUILD_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet06a_rebuild_2026-09-18")
FLEET07_OUT_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet07_out_2026-09-26\out")
FLEET06B_OUT_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet06b_local_2026-09-18\out")
HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet07_harvest_2026-09-26")
STEP2_CACHE_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet06c_harvest_2026-09-24")
MANIFEST_CHANGED_CSV = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet07_campaign_2026-09-26\manifest_changed.csv"
)
GZ_TMP_ROOT = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\467deb4d-0d3b-4adf-a81a-df3c021b2cce\scratchpad\gz_tmp_fleet07"
)

ALL_CELLS = [
    "lighting",
    "setback",
    "infiltration",
    "lighting+setback",
    "lighting+infiltration",
    "setback+infiltration",
    "lighting+setback+infiltration",
]

ALL_GEO = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

_SUCCESS_MARKER = "EnergyPlus Completed Successfully"
_FATAL_MARKER = "EnergyPlus Terminated--Fatal Error Detected"


def _osm_to_stem(osm_id: str) -> str:
    return osm_id.replace("/", "_", 1)


def _load_changed_stems(scenario_cell: str) -> set[str]:
    df = pd.read_csv(MANIFEST_CHANGED_CSV, usecols=["building_id", "cell_name"])
    return set(df.loc[df["cell_name"] == scenario_cell, "building_id"])


def _classify_folder(work_dir: Path) -> dict:
    end_file = work_dir / "eplusout.end"
    if not work_dir.exists() or not end_file.exists():
        return {"status": "failed_crash", "error_summary": "eplusout.end missing"}
    end_text = end_file.read_text(errors="replace")
    if _FATAL_MARKER in end_text:
        return {"status": "failed_fatal", "error_summary": "fatal marker in eplusout.end"}
    if _SUCCESS_MARKER in end_text:
        if (work_dir / "eplusout.sql").exists() or (work_dir / "eplusout.sql.gz").exists():
            return {"status": "success", "error_summary": ""}
        return {"status": "failed_crash", "error_summary": "eplusout.sql missing despite success marker"}
    return {"status": "failed_crash", "error_summary": "unrecognised eplusout.end content"}


def _resolve_sql_path(stem: str, work_dir: Path, gz_tmp_dir: Path):
    sql = work_dir / "eplusout.sql"
    if sql.exists():
        return sql, None
    sqlgz = work_dir / "eplusout.sql.gz"
    if sqlgz.exists():
        gz_tmp_dir.mkdir(parents=True, exist_ok=True)
        dest = gz_tmp_dir / f"{stem}.sql"
        with gzip.open(sqlgz, "rb") as src, open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)
        return dest, dest
    return None, None


def _get_step2_table(geo_cell: str) -> gpd.GeoDataFrame:
    geo_dir = REBUILD_ROOT / geo_cell
    step2_dir = STEP2_CACHE_ROOT / "_step2" / geo_cell
    cached = step2_dir / "02_enriched.gpkg"
    if cached.exists():
        return gpd.read_file(cached)

    gdf_raw = gpd.read_file(geo_dir / "01_buildings.gpkg")
    climate_sidecar = pd.read_parquet(geo_dir / "02a_climate_epw.parquet")
    epw_paths = climate_sidecar["epw_path"].unique()
    if len(epw_paths) != 1:
        raise ValueError(
            f"{geo_cell}: expected exactly 1 unique epw_path in 02a_climate_epw.parquet, "
            f"got {len(epw_paths)}: {list(epw_paths)}"
        )
    epw_path = Path(epw_paths[0])

    step2_dir.mkdir(parents=True, exist_ok=True)
    gdf_57, _schedule_library = step2_classify_enrich(gdf_raw, epw_path, step2_dir, geo_cell)

    idf_manifest = pd.read_parquet(geo_dir / "step3" / "03_idf_manifest.parquet")
    step2_ids = gdf_57[["osm_id", "archetype_id"]].astype({"osm_id": str})
    idf_ids = idf_manifest[["osm_id", "archetype_id"]].astype({"osm_id": str})
    merged = step2_ids.merge(idf_ids, on="osm_id", suffixes=("_step2", "_idf"))
    n_shared = len(merged)
    n_mismatch = int((merged["archetype_id_step2"] != merged["archetype_id_idf"]).sum())
    print(f"[FLEET-07d] step2 guard {geo_cell}: shared osm_id={n_shared}, mismatched archetype_id={n_mismatch}")
    if n_shared == 0 or n_mismatch > 0:
        raise ValueError(
            f"{geo_cell}: archetype_id guard failed: {n_mismatch}/{n_shared} shared osm_id mismatched "
            "between step2_classify_enrich() rebuild and 03_idf_manifest.parquet"
        )

    gdf_57.to_file(str(cached), driver="GPKG")
    return gdf_57


def _harvest_one(scenario_cell: str, geo_cell: str) -> dict:
    t0 = time.monotonic()

    t08 = pd.read_csv(T08_CSV)
    population = set(t08.loc[t08["cell"] == geo_cell, "stem"])

    geo_dir = REBUILD_ROOT / geo_cell
    idf_manifest = pd.read_parquet(geo_dir / "step3" / "03_idf_manifest.parquet")
    idf_manifest = idf_manifest.copy()
    idf_manifest["_stem"] = idf_manifest["osm_id"].astype(str).map(_osm_to_stem)
    idf_manifest = idf_manifest[idf_manifest["_stem"].isin(population)].drop(columns=["_stem"]).reset_index(drop=True)

    climate_path = geo_dir / "02a_climate_epw.parquet"

    step2_gdf = _get_step2_table(geo_cell)
    step2_stem = step2_gdf["osm_id"].astype(str).map(_osm_to_stem)
    enriched_gdf = step2_gdf[step2_stem.isin(population)].reset_index(drop=True)

    changed_stems = _load_changed_stems(scenario_cell)
    gz_tmp_dir = GZ_TMP_ROOT / scenario_cell / geo_cell

    sim_rows = []
    decompressed_paths: list[Path] = []
    n_from_fleet07 = 0
    n_from_fleet06b = 0

    for _, idf_row in idf_manifest.iterrows():
        osm_id = str(idf_row["osm_id"])
        stem = _osm_to_stem(osm_id)
        if stem in changed_stems:
            work_dir = FLEET07_OUT_ROOT / scenario_cell / stem
            n_from_fleet07 += 1
        else:
            work_dir = FLEET06B_OUT_ROOT / scenario_cell / stem
            n_from_fleet06b += 1
        cls = _classify_folder(work_dir)
        status = cls["status"]

        sql_path = None
        csv_path = None

        if status == "success":
            sql_path, tmp_path = _resolve_sql_path(stem, work_dir, gz_tmp_dir)
            if tmp_path is not None:
                decompressed_paths.append(tmp_path)
            csv_file = work_dir / "eplusout.csv"
            csv_path = csv_file if csv_file.exists() else None
            if sql_path is None:
                status = "failed_crash"
                cls["error_summary"] = "sql resolve failed"

        sim_rows.append({
            "osm_id": osm_id,
            "status": status,
            "sql_path": str(sql_path) if sql_path else None,
            "csv_path": str(csv_path) if csv_path else None,
            "error_msg": cls.get("error_summary", ""),
        })

    sim_manifest = pd.DataFrame(sim_rows)

    from openubem.results import aggregate_results

    output_dir = HARVEST_ROOT / scenario_cell / geo_cell
    output_dir.mkdir(parents=True, exist_ok=True)

    results_gdf = aggregate_results(
        sim_manifest,
        idf_manifest,
        enriched_gdf,
        output_dir,
        climate_sidecar=climate_path,
        make_figures=False,
        export_html=False,
        ep_version="23.1.0",
    )

    for p in decompressed_paths:
        try:
            p.unlink()
        except (FileNotFoundError, PermissionError):
            pass
    try:
        if gz_tmp_dir.exists():
            gz_tmp_dir.rmdir()
    except OSError:
        pass

    wall_s = time.monotonic() - t0

    n_rows = len(results_gdf)
    n_cols_incl_geom = len(results_gdf.columns)
    schema_path = output_dir / "05_results.schema.json"
    n_success_pop = int(len(population))

    if "simulation_status" in results_gdf.columns:
        n_non_success = int((~results_gdf["simulation_status"].isin({"success", "success_cached"})).sum())
    else:
        n_non_success = None

    return {
        "scenario_cell": scenario_cell,
        "geo_cell": geo_cell,
        "rows_written": n_rows,
        "rows_expected": n_success_pop,
        "n_columns_incl_geometry": n_cols_incl_geom,
        "schema_sidecar_present": schema_path.exists(),
        "n_non_success": n_non_success,
        "n_from_fleet07": n_from_fleet07,
        "n_from_fleet06b": n_from_fleet06b,
        "wall_s": wall_s,
        "output_dir": str(output_dir),
    }


def _worker(args):
    scenario_cell, geo_cell = args
    try:
        return _harvest_one(scenario_cell, geo_cell)
    except Exception as exc:
        return {"scenario_cell": scenario_cell, "geo_cell": geo_cell, "error": repr(exc)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cells", nargs="+", default=ALL_CELLS)
    parser.add_argument("--geo", nargs="+", default=ALL_GEO)
    args = parser.parse_args()

    for scenario_cell in args.cells:
        tasks = [(scenario_cell, geo_cell) for geo_cell in args.geo]
        results = []
        t_cell0 = time.monotonic()
        with ProcessPoolExecutor(max_workers=len(tasks)) as pool:
            futures = {pool.submit(_worker, t): t for t in tasks}
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
                if "error" in res:
                    print(f"[FLEET-07d] FAILED {res['scenario_cell']}/{res['geo_cell']}: {res['error']}")
                else:
                    print(
                        f"[FLEET-07d] {res['scenario_cell']}/{res['geo_cell']}: "
                        f"rows={res['rows_written']}/{res['rows_expected']} "
                        f"cols={res['n_columns_incl_geometry']} "
                        f"non_success={res['n_non_success']} "
                        f"fleet07={res['n_from_fleet07']} fleet06b={res['n_from_fleet06b']} "
                        f"wall={res['wall_s']:.1f}s"
                    )
        wall_cell = time.monotonic() - t_cell0
        print(f"[FLEET-07d] scenario cell '{scenario_cell}' done in {wall_cell:.1f}s ({len(tasks)} geo cells, "
              f"{len(tasks)}-way pool)")


if __name__ == "__main__":
    main()
