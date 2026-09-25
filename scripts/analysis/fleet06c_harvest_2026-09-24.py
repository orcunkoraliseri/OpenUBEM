"""FLEET-06c harvest (PLAN_techtransfer-block6-2026-09-18.md, Task FLEET-06 FLEET-06c,
amended by section 2g): run openubem.results.aggregate_results() once per
(scenario cell, geographic cell) pair over the FLEET-06b local EnergyPlus output tree,
writing <root>/<scenario_cell>/<geo_cell>/05_results.* with the unmodified 70-column
Step-5 schema. Geo cells run in a 12-way process pool, never a serial loop.
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
OUT_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet06b_local_2026-09-18\out")
HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\fleet06c_harvest_2026-09-24")
GZ_TMP_ROOT = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\ab6f94ef-176e-417c-9bf5-1b01c74e7a0c\scratchpad\gz_tmp"
)

ALL_CELLS = [
    "baseline",
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
    """Amendment 2g-1: rebuild the 57-col Step-2 table via step2_classify_enrich()
    (scripts/validation/v12_cell_pipeline.py:225) on the rebuild's 01_buildings.gpkg,
    guard archetype_id against 03_idf_manifest.parquet, cache under
    <root>/_step2/<geo_cell>/02_enriched.gpkg and reuse across all 8 scenario cells.
    """
    geo_dir = REBUILD_ROOT / geo_cell
    step2_dir = HARVEST_ROOT / "_step2" / geo_cell
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
    print(f"[FLEET-06c] step2 guard {geo_cell}: shared osm_id={n_shared}, mismatched archetype_id={n_mismatch}")
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

    out_cell_dir = OUT_ROOT / scenario_cell
    gz_tmp_dir = GZ_TMP_ROOT / scenario_cell / geo_cell

    sim_rows = []
    decompressed_paths: list[Path] = []

    for _, idf_row in idf_manifest.iterrows():
        osm_id = str(idf_row["osm_id"])
        stem = _osm_to_stem(osm_id)
        work_dir = out_cell_dir / stem
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
        except FileNotFoundError:
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

    total_kwh = None
    total_area = None
    if "total_eui_kwh_m2" in results_gdf.columns and "floor_area_m2" in results_gdf.columns:
        valid = results_gdf[results_gdf["total_eui_kwh_m2"].notna() & results_gdf["floor_area_m2"].notna()]
        total_kwh = float((valid["total_eui_kwh_m2"] * valid["floor_area_m2"]).sum())
        total_area = float(valid["floor_area_m2"].sum())

    csv_total_kwh = None
    csv_total_area = None
    if "total_eui_kwh_m2" in results_gdf.columns:
        t08_sub = t08[t08["cell"] == geo_cell][["stem", "floor_area_m2"]].copy()
        t08_sub["_stem"] = t08_sub["stem"]
        results_stem = results_gdf["osm_id"].astype(str).map(_osm_to_stem)
        merged = pd.DataFrame({
            "_stem": results_stem,
            "total_eui_kwh_m2": results_gdf["total_eui_kwh_m2"].values,
        }).merge(t08_sub, on="_stem", how="inner")
        merged = merged[merged["total_eui_kwh_m2"].notna() & merged["floor_area_m2"].notna()]
        csv_total_kwh = float((merged["total_eui_kwh_m2"] * merged["floor_area_m2"]).sum())
        csv_total_area = float(merged["floor_area_m2"].sum())

    return {
        "scenario_cell": scenario_cell,
        "geo_cell": geo_cell,
        "rows_written": n_rows,
        "rows_expected": n_success_pop,
        "n_columns_incl_geometry": n_cols_incl_geom,
        "schema_sidecar_present": schema_path.exists(),
        "n_non_success": n_non_success,
        "total_kwh": total_kwh,
        "total_area_m2": total_area,
        "csv_total_kwh": csv_total_kwh,
        "csv_total_area_m2": csv_total_area,
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
                    print(f"[FLEET-06c] FAILED {res['scenario_cell']}/{res['geo_cell']}: {res['error']}")
                else:
                    print(
                        f"[FLEET-06c] {res['scenario_cell']}/{res['geo_cell']}: "
                        f"rows={res['rows_written']}/{res['rows_expected']} "
                        f"cols={res['n_columns_incl_geometry']} "
                        f"non_success={res['n_non_success']} "
                        f"wall={res['wall_s']:.1f}s"
                    )
        wall_cell = time.monotonic() - t_cell0
        print(f"[FLEET-06c] scenario cell '{scenario_cell}' done in {wall_cell:.1f}s ({len(tasks)} geo cells, "
              f"{len(tasks)}-way pool)")


if __name__ == "__main__":
    main()
