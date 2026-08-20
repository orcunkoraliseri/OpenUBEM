"""OPEN-03 -- load-density elasticity runner (PLAN_vintage-elasticity-2026-08-19.md T01).

Copied from scripts/analysis/open03_untrimmed_layout_assign_sample_2026-08-19.py
with three changes: (1) sample restricted to the 20 osm_ids where
floor_area_disagree_gt10 == False and osm_id != "way/425993511", read from the
existing baseline join CSV instead of recomputed by percentile; (2) a --scale
argument that multiplies gdf_sample["lighting_w_m2"] and
gdf_sample["equipment_w_m2"] immediately before run_step3; (3) outputs written
under openubem/outputs/open03_elasticity/<scale>/<cell>/ instead of scratchpad/.
"""
from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

FIXTURE_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
BASELINE_JOIN_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open03_untrimmed_sample_join.csv"
ELASTICITY_ROOT = REPO / "openubem" / "outputs" / "open03_elasticity"


def select_20_sample() -> pd.DataFrame:
    df = pd.read_csv(BASELINE_JOIN_CSV, dtype={"osm_id": str})
    df = df[(df["floor_area_disagree_gt10"] == False) & (df["osm_id"] != "way/425993511")].copy()
    cols = ["cell", "osm_id", "footprint_area_m2", "levels", "archetype_id",
            "auto_total_eui_kwh_m2", "auto_floor_area_m2", "percentile_slot"]
    return df[cols].reset_index(drop=True)


def main():
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    from openubem.idf.builder import run_step3
    from openubem.simulation.parallel import SimTask
    from openubem.simulation.runner import run_energyplus, classify_outcome
    from openubem.results.parser import parse_building

    sys.path.insert(0, str(REPO / "scripts" / "validation"))
    from v12_cell_pipeline import CELL_CONFIGS

    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    args = parser.parse_args()
    scale = args.scale

    OUT_DIR = ELASTICITY_ROOT / str(scale)
    EUI_CSV = OUT_DIR / "open03_elasticity_sample_eui.csv"
    JOIN_CSV = OUT_DIR / "open03_elasticity_sample_join.csv"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stations = load_stations()

    import os
    cells_all = sorted(CELL_CONFIGS.keys())
    smoke_cells = os.environ.get("OPEN03_SMOKE_CELLS")
    if smoke_cells:
        cells_all = [c for c in cells_all if c in set(smoke_cells.split(","))]

    sample_df = select_20_sample()
    sample_df = sample_df[sample_df["cell"].isin(cells_all)].reset_index(drop=True)
    smoke_slots = os.environ.get("OPEN03_SMOKE_SLOTS")
    if smoke_slots:
        keep = {int(s) for s in smoke_slots.split(",")}
        sample_df = sample_df[sample_df["percentile_slot"].isin(keep)].reset_index(drop=True)
    cells = sorted(sample_df["cell"].unique().tolist())
    print(f"cells ({len(cells)}): {cells}")
    print(f"T01: sample rows={len(sample_df)}, distinct cells={sample_df['cell'].nunique()}")
    print(sample_df.groupby('cell').size().to_string())

    # T01 membership check: every sampled osm_id present in that cell's gpkg.
    membership_ok = 0
    for cell in cells:
        gpkg = FIXTURE_ROOT / cell / "01_buildings.gpkg"
        gdf_ids = set(gpd.read_file(str(gpkg), columns=["osm_id"])["osm_id"].astype(str))
        sub = sample_df[sample_df["cell"] == cell]
        membership_ok += sub["osm_id"].astype(str).isin(gdf_ids).sum()
    print(f"T01: osm_id membership ok = {membership_ok} / {len(sample_df)}")

    result_rows = []
    t_start = time.time()
    for cell in cells:
        cfg = CELL_CONFIGS[cell]
        cell_sample = sample_df[sample_df["cell"] == cell].copy()
        targets = set(cell_sample["osm_id"].astype(str))
        print(f"\n=== cell={cell} targets={sorted(targets)} ===")

        cell_dir = OUT_DIR / cell
        weather_dir = cell_dir / "weather"
        weather_dir.mkdir(parents=True, exist_ok=True)

        try:
            station, dist_km = resolve_station(cfg["lat"], cfg["lon"], stations)
            epw_path = fetch_epw(station, output_dir=weather_dir)

            gpkg = FIXTURE_ROOT / cell / "01_buildings.gpkg"
            gdf_raw = gpd.read_file(str(gpkg))
            gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
            gdf_in["levels"] = gdf_in["levels"].astype("Int64")
            gdf_26 = BuildingClassifier().classify(gdf_in)

            zone_df = assign_climate_zones(gdf_26)
            gdf_29 = gdf_26.copy()
            gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
            gdf_29["epw_path"] = str(epw_path)
            gdf_29["provenance_climate_zone"] = pd.Categorical(zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"])
            gdf_57, schedule_library = enrich_semantics(gdf_29)

            gdf_sample = gdf_57[gdf_57["osm_id"].astype(str).isin(targets)].copy()
            print(f"cell={cell}: gdf_sample rows={len(gdf_sample)}")

            gdf_sample["lighting_w_m2"] = gdf_sample["lighting_w_m2"] * scale
            gdf_sample["equipment_w_m2"] = gdf_sample["equipment_w_m2"] * scale

            step3_dir = cell_dir / "step3_layout_assign"
            step3_dir.mkdir(parents=True, exist_ok=True)
            manifest = run_step3(gdf_sample, schedule_library, step3_dir, n_jobs=4,
                                  resolution_mode="layout_assign", trim_outputs=False)
        except Exception:
            err = traceback.format_exc()[-800:]
            print(f"cell={cell}: FATAL during build stage: {err}")
            for _, srow in cell_sample.iterrows():
                result_rows.append({
                    "cell": cell, "osm_id": srow["osm_id"], "percentile_slot": srow["percentile_slot"],
                    "footprint_area_m2": srow["footprint_area_m2"], "levels": srow["levels"],
                    "archetype_id": srow["archetype_id"],
                    "auto_total_eui_kwh_m2": srow["auto_total_eui_kwh_m2"],
                    "auto_floor_area_m2": srow["auto_floor_area_m2"],
                    "parse_status": "failed_build_stage",
                    "sim_outcome": "",
                    "total_eui_kwh_m2": None, "floor_area_m2": None, "num_zones": None,
                    "sql_size_bytes": None,
                    "error_summary": err.splitlines()[-1] if err else "unknown build error",
                })
            continue

        manifest = manifest.set_index("osm_id", drop=False)
        gdf_sample_idx = gdf_sample.set_index(gdf_sample["osm_id"].astype(str))

        for _, srow in cell_sample.iterrows():
            osm_id = str(srow["osm_id"])
            safe_id = osm_id.replace("/", "_").replace(":", "_").replace(" ", "_")
            base_row = {
                "cell": cell, "osm_id": osm_id, "percentile_slot": srow["percentile_slot"],
                "footprint_area_m2": srow["footprint_area_m2"], "levels": srow["levels"],
                "archetype_id": srow["archetype_id"],
                "auto_total_eui_kwh_m2": srow["auto_total_eui_kwh_m2"],
                "auto_floor_area_m2": srow["auto_floor_area_m2"],
            }
            if osm_id not in manifest.index:
                base_row.update({
                    "parse_status": "failed_no_manifest_row", "sim_outcome": "",
                    "total_eui_kwh_m2": None, "floor_area_m2": None, "num_zones": None,
                    "sql_size_bytes": None, "error_summary": "osm_id absent from run_step3 manifest",
                })
                result_rows.append(base_row)
                continue

            mrow = manifest.loc[osm_id]
            if isinstance(mrow, pd.DataFrame):
                mrow = mrow.iloc[0]

            if not mrow.get("idf_path"):
                base_row.update({
                    "parse_status": "failed_idf_build", "sim_outcome": "",
                    "total_eui_kwh_m2": None, "floor_area_m2": None, "num_zones": None,
                    "sql_size_bytes": None,
                    "error_summary": f"generation_status={mrow.get('generation_status', '')}",
                })
                result_rows.append(base_row)
                print(f"  osm_id={osm_id} parse_status=failed_idf_build")
                continue

            try:
                run_dir = cell_dir / "sim" / safe_id
                run_dir.mkdir(parents=True, exist_ok=True)
                task = SimTask(osm_id=osm_id, idf_path=str(mrow["idf_path"]), epw_path=str(epw_path), work_dir=str(run_dir))
                raw = run_energyplus(task)
                outcome = classify_outcome(raw, run_dir)
                sim_status = outcome.get("status", "")

                sql_path = run_dir / "eplusout.sql"
                sql_size = sql_path.stat().st_size if sql_path.exists() else 0

                grow = gdf_sample_idx.loc[osm_id]
                if isinstance(grow, pd.DataFrame):
                    grow = grow.iloc[0]

                manifest_row = pd.Series({
                    "osm_id": osm_id,
                    "num_zones": mrow.get("num_zones", 1),
                    "data_quality_flag": mrow.get("data_quality_flag", ""),
                    "resolution_mode": mrow.get("resolution_mode", "layout_assign"),
                    "footprint_area_m2": float(grow["footprint_area_m2"]),
                    "levels": grow.get("levels"),
                    "height_m": grow.get("height_m"),
                    "archetype_source": grow.get("archetype_source"),
                })
                pres = parse_building(sql_path if sql_path.exists() else None, None, manifest_row)

                base_row.update({
                    "parse_status": pres.get("parse_status", ""),
                    "sim_outcome": sim_status,
                    "total_eui_kwh_m2": pres.get("total_eui_kwh_m2"),
                    "floor_area_m2": pres.get("floor_area_m2"),
                    "num_zones": mrow.get("num_zones", None),
                    "sql_size_bytes": sql_size,
                    "error_summary": (pres.get("error_summary") or outcome.get("error_summary") or "")[:300],
                })
            except Exception:
                err = traceback.format_exc()[-500:]
                base_row.update({
                    "parse_status": "failed_exception", "sim_outcome": "",
                    "total_eui_kwh_m2": None, "floor_area_m2": None, "num_zones": None,
                    "sql_size_bytes": None, "error_summary": err.splitlines()[-1] if err else "unknown exception",
                })
            result_rows.append(base_row)
            print(f"  osm_id={osm_id} parse_status={base_row['parse_status']} "
                  f"eui={base_row['total_eui_kwh_m2']} sql_bytes={base_row['sql_size_bytes']}")

    elapsed = time.time() - t_start
    print(f"\nTotal build+sim+parse wall clock: {elapsed:.1f}s")

    eui_df = pd.DataFrame(result_rows)
    eui_df.to_csv(EUI_CSV, index=False)
    print(f"\nWrote {EUI_CSV} rows={len(eui_df)}")

    # ---- T02 summary ----
    n_success = (eui_df["parse_status"] == "success").sum()
    n_fail = len(eui_df) - n_success
    print(f"\nT02: parse success={n_success} fail={n_fail} of {len(eui_df)}")
    if n_fail:
        print("T02 failure reasons:")
        fails = eui_df[eui_df["parse_status"] != "success"]
        for _, r in fails.iterrows():
            print(f"  osm_id={r['osm_id']} cell={r['cell']} status={r['parse_status']} reason={r['error_summary']}")

    # ---- T03 join + gap ----
    ok = eui_df[eui_df["parse_status"] == "success"].copy()
    ok["gap_pct"] = (ok["total_eui_kwh_m2"] - ok["auto_total_eui_kwh_m2"]) / ok["auto_total_eui_kwh_m2"] * 100.0
    ok["floor_area_disagree_pct"] = (
        (ok["floor_area_m2"] - ok["auto_floor_area_m2"]).abs() / ok["auto_floor_area_m2"] * 100.0
    )
    ok["floor_area_disagree_gt10"] = ok["floor_area_disagree_pct"] > 10.0
    ok.to_csv(JOIN_CSV, index=False)
    print(f"Wrote {JOIN_CSV} rows={len(ok)}")

    if len(ok):
        pooled_gap = (ok["total_eui_kwh_m2"].sum() - ok["auto_total_eui_kwh_m2"].sum()) / ok["auto_total_eui_kwh_m2"].sum() * 100.0
        # pooled using true energy/area (Sigma energy / Sigma area) for both sides
        la_energy = (ok["total_eui_kwh_m2"] * ok["floor_area_m2"]).sum()
        la_area = ok["floor_area_m2"].sum()
        auto_energy = (ok["auto_total_eui_kwh_m2"] * ok["auto_floor_area_m2"]).sum()
        auto_area = ok["auto_floor_area_m2"].sum()
        pooled_eui_gap_pct = (la_energy / la_area - auto_energy / auto_area) / (auto_energy / auto_area) * 100.0
        median_gap = ok["gap_pct"].median()

        restricted = ok[~ok["floor_area_disagree_gt10"]]
        if len(restricted):
            r_la_energy = (restricted["total_eui_kwh_m2"] * restricted["floor_area_m2"]).sum()
            r_la_area = restricted["floor_area_m2"].sum()
            r_auto_energy = (restricted["auto_total_eui_kwh_m2"] * restricted["auto_floor_area_m2"]).sum()
            r_auto_area = restricted["auto_floor_area_m2"].sum()
            restricted_gap_pct = (r_la_energy / r_la_area - r_auto_energy / r_auto_area) / (r_auto_energy / r_auto_area) * 100.0
        else:
            restricted_gap_pct = float("nan")

        mean_sql = ok["sql_size_bytes"].mean()
        max_sql = ok["sql_size_bytes"].max()
        implied_full_fleet_gb = mean_sql * 8160 / (1024 ** 3)

        print(f"\nT03: pooled EUI gap (Sigma energy / Sigma area, both sides) = {pooled_eui_gap_pct:.3f}%")
        print(f"T03: median per-building gap_pct = {median_gap:.3f}%")
        print(f"T03: n with floor_area_disagree>10% = {int(ok['floor_area_disagree_gt10'].sum())} / {len(ok)}")
        print(f"T03: pooled gap restricted to floor_area_disagree<=10% (n={len(restricted)}) = {restricted_gap_pct:.3f}%")
        print(f"T03: mean sql_size_bytes = {mean_sql:.0f}  max sql_size_bytes = {max_sql:.0f}")
        print(f"T03: implied full-fleet (8160 buildings) disk cost at mean size = {implied_full_fleet_gb:.2f} GB")

        # ---- T04: OPEN-18 slice -- small buildings (10th/35th slots), cold cells (NYC) ----
        nyc_cells = {"nyc_urban", "nyc_suburban", "nyc_rural", "nyc_centre"}
        slice_df = ok[(ok["cell"].isin(nyc_cells)) & (ok["percentile_slot"].isin([10, 35]))]
        rest_df = ok[~((ok["cell"].isin(nyc_cells)) & (ok["percentile_slot"].isin([10, 35])))]
        print(f"\nT04: slice n={len(slice_df)} (small buildings, cold NYC cells)")
        if len(slice_df) >= 5:
            s_la_energy = (slice_df["total_eui_kwh_m2"] * slice_df["floor_area_m2"]).sum()
            s_la_area = slice_df["floor_area_m2"].sum()
            s_auto_energy = (slice_df["auto_total_eui_kwh_m2"] * slice_df["auto_floor_area_m2"]).sum()
            s_auto_area = slice_df["auto_floor_area_m2"].sum()
            slice_gap_pct = (s_la_energy / s_la_area - s_auto_energy / s_auto_area) / (s_auto_energy / s_auto_area) * 100.0
            slice_median_gap = slice_df["gap_pct"].median()
            print(f"T04: slice (n={len(slice_df)}) pooled gap = {slice_gap_pct:.3f}%  median gap = {slice_median_gap:.3f}%")
            if len(rest_df):
                rest_la_energy = (rest_df["total_eui_kwh_m2"] * rest_df["floor_area_m2"]).sum()
                rest_la_area = rest_df["floor_area_m2"].sum()
                rest_auto_energy = (rest_df["auto_total_eui_kwh_m2"] * rest_df["auto_floor_area_m2"]).sum()
                rest_auto_area = rest_df["auto_floor_area_m2"].sum()
                rest_gap_pct = (rest_la_energy / rest_la_area - rest_auto_energy / rest_auto_area) / (rest_auto_energy / rest_auto_area) * 100.0
                print(f"T04: rest of sample (n={len(rest_df)}) pooled gap = {rest_gap_pct:.3f}%")
        else:
            print(f"T04: slice n={len(slice_df)} < 5 -- too small to support a conclusion, stopping there.")
    else:
        print("T03/T04: zero successful parses -- no gap statistics computable.")

    print("\nDONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
