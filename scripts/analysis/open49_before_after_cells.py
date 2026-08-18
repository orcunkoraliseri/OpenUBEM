"""OPEN-49 T04 — before/after on the twelve cells' semantic-stage Unknown-row draws.

Re-runs step1 (load cached 01_buildings.gpkg) -> classify -> climate zone ->
enrich_semantics for each of the twelve adopted cells. It does NOT simulate
(no EnergyPlus, no cluster). It measures the change in Step-2.2 semantic
enrichment INPUTS only (the eight fields from Fact 3: four PDE columns +
four scalar setpoints) for OpenUBEMUnknown rows, comparing whichever code is
on disk at openubem/semantic/__init__.py at the time of each `--mode raw`
invocation against the other invocation.

No EUI claim may be made from this script's output — floor area and energy
are not touched here. The +/-300 kWh/m2 figure belongs to OPEN-49's original
measurement and is not re-derived by this script.

Usage (two raw passes, one per code version on disk, then finalize):
    .venv/Scripts/python.exe scripts/analysis/open49_before_after_cells.py \
        --mode raw --label before --out <scratch>/open49_raw_before.parquet
    .venv/Scripts/python.exe scripts/analysis/open49_before_after_cells.py \
        --mode raw --label after --out <scratch>/open49_raw_after.parquet
    .venv/Scripts/python.exe scripts/analysis/open49_before_after_cells.py \
        --mode finalize --before <scratch>/open49_raw_before.parquet \
        --after <scratch>/open49_raw_after.parquet \
        --out openubem/outputs/comparisons/open49_before_after_cells.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

CELLS_DIR = Path("docs/docs_VALIDATION/validations/overAll/results/phaseE")
CELL_NAMES = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
PDE_COLS = ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person", "wwr"]
SCALAR_COLS = ["heating_setpoint_c", "cooling_setpoint_c", "heating_setback_c", "cooling_setup_c"]
ALL_COLS = PDE_COLS + SCALAR_COLS
MOVING_CELLS = {"nyc_centre", "austin_centre", "la_centre", "la_urban"}


def run_cell(cell: str) -> pd.DataFrame | None:
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    gpkg_path = CELLS_DIR / cell / "01_buildings.gpkg"
    if not gpkg_path.exists():
        print(f"SKIP {cell}: {gpkg_path} missing")
        return None
    gdf_raw = gpd.read_file(str(gpkg_path))
    gdf_raw2 = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_raw2["levels"] = gdf_raw2["levels"].astype("Int64")

    bc = BuildingClassifier()
    gdf_26 = bc.classify(gdf_raw2)

    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(
        zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB)
    )
    gdf_29["epw_path"] = "N/A_open49_t04_semantic_only"
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values,
        categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )

    gdf_57, _ = enrich_semantics(gdf_29, random_seed=42)
    out = gdf_57[["osm_id", "archetype_id"] + ALL_COLS].copy()
    out["cell"] = cell
    return out


def cmd_raw(label: str, out_path: str) -> None:
    frames = []
    for cell in CELL_NAMES:
        df = run_cell(cell)
        if df is None:
            frames.append(pd.DataFrame({"cell": [cell], "osm_id": [None], "archetype_id": [None],
                                          **{c: [np.nan] for c in ALL_COLS}}))
            continue
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined["label"] = label
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(out_path, index=False)
    print(f"wrote {len(combined)} rows -> {out_path}")


def cmd_finalize(before_path: str, after_path: str, out_path: str) -> None:
    before = pd.read_parquet(before_path)
    after = pd.read_parquet(after_path)

    rows = []
    for cell in CELL_NAMES:
        b = before[before["cell"] == cell]
        a = after[after["cell"] == cell]
        if b["osm_id"].isna().all() or a["osm_id"].isna().all():
            rows.append({"cell": cell, "status": "SKIPPED_MISSING_GPKG", "moving_cell": cell in MOVING_CELLS})
            continue

        b_unk = b[b["archetype_id"] == "OpenUBEMUnknown"]
        a_unk = a[a["archetype_id"] == "OpenUBEMUnknown"]

        row = {
            "cell": cell,
            "status": "OK",
            "moving_cell": cell in MOVING_CELLS,
            "n_unknown_before": len(b_unk),
            "n_unknown_after": len(a_unk),
        }
        for col in ALL_COLS:
            bv = b_unk[col].to_numpy(dtype=float)
            av = a_unk[col].to_numpy(dtype=float)
            row[f"{col}_min_before"] = float(np.min(bv)) if len(bv) else np.nan
            row[f"{col}_mean_before"] = float(np.mean(bv)) if len(bv) else np.nan
            row[f"{col}_max_before"] = float(np.max(bv)) if len(bv) else np.nan
            row[f"{col}_min_after"] = float(np.min(av)) if len(av) else np.nan
            row[f"{col}_mean_after"] = float(np.mean(av)) if len(av) else np.nan
            row[f"{col}_max_after"] = float(np.max(av)) if len(av) else np.nan

        merged = b_unk[["osm_id", "wwr"]].merge(
            a_unk[["osm_id", "wwr"]], on="osm_id", suffixes=("_before", "_after")
        )
        n_changed = int((merged["wwr_before"] - merged["wwr_after"]).abs().gt(0.01).sum())
        row["n_wwr_changed_gt_0.01"] = n_changed
        row["n_unknown_matched_by_osm_id"] = len(merged)

        rows.append(row)

    out_df = pd.DataFrame(rows)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"wrote {len(out_df)} cell rows -> {out_path}")
    print(out_df[["cell", "status", "moving_cell", "n_unknown_before", "n_wwr_changed_gt_0.01"]].to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["raw", "finalize"])
    ap.add_argument("--label", choices=["before", "after"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--before")
    ap.add_argument("--after")
    args = ap.parse_args()

    if args.mode == "raw":
        if not args.label:
            raise SystemExit("--label required for --mode raw")
        cmd_raw(args.label, args.out)
    else:
        if not args.before or not args.after:
            raise SystemExit("--before and --after required for --mode finalize")
        cmd_finalize(args.before, args.after, args.out)


if __name__ == "__main__":
    main()
