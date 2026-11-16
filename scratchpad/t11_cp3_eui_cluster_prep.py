"""T11.6 CP-3 EUI do-no-harm -- cluster A/B escalation (LOCAL prep half).

The vintage-bin field-diff (t11_cp3_eui_field_diff.py) found MATERIAL
divergence (168/738 nyc_centre rows) between Phase-A and Phase-C(knn)
year_built fills -- the plan's own escalation trigger. This script builds
the two IDF fleets (Phase-A-imputed vs Phase-C-imputed year_built, everything
else common-mode) LOCALLY (no cluster compute here -- IDF generation is pure
geometry/eppy, no EnergyPlus), reusing the production pipeline functions
(`step2_classify_enrich`/`step3_generate` from `scripts/validation/
v12_cell_pipeline.py`, which wrap `openubem.semantic.enrich_semantics` /
`openubem.idf.builder.run_step3` -- REUSED, not reimplemented) so cluster
submission (a separate step, sbatch fire-and-forget) has real IDFs to run.

No live-network calls: the raw building set is the already-committed
`01_buildings.gpkg` (not step1_fetch) and the EPW is the already-cached
local file (not a fresh station lookup).

Report-only / zero-fitted-params: nothing here is fed back into any imputer
setting. Simulates ONLY the rows where the vintage bin actually diverges
(minimises cluster footprint, mirrors the T09-CC precedent's "simulate the
held-out block only").
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from t11_cp3_leaderboard import load_pooled  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "validation"))
from v12_cell_pipeline import step2_classify_enrich, step3_generate  # noqa: E402

from openubem import config
from openubem.semantic.imputation import ImputeConfig, impute_missing
from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS

SEED = 42
WINNING_METHOD = "knn"
GATE_CELL = "nyc_centre"
REPO = Path(__file__).resolve().parents[1]
NYC_GPKG = REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE" / GATE_CELL / "01_buildings.gpkg"
NYC_EPW = Path.home() / ".openubem" / "epw" / "USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053_TMYx.2011-2025.epw"
WORK = Path(__file__).parent / "t11cc_work"


def build_variant_frames():
    pooled = load_pooled()
    cfg_a = ImputeConfig(enabled_tiers=("spatial", "statistical"))
    gdf_a_pool = impute_missing(pooled, cfg=cfg_a, targets=["year_built"], rng=np.random.default_rng(SEED))

    orig_method = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
    try:
        config.IMPUTE_ML_METHOD_BY_TARGET["year_built"] = WINNING_METHOD
        cfg_c = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
        gdf_c_pool = impute_missing(pooled, cfg=cfg_c, targets=["year_built"], rng=np.random.default_rng(SEED))
    finally:
        config.IMPUTE_ML_METHOD_BY_TARGET.clear()
        config.IMPUTE_ML_METHOD_BY_TARGET.update(orig_method)

    yb_a = gdf_a_pool.set_index("osm_id")["year_built"]
    prov_a = gdf_a_pool.set_index("osm_id")["provenance_year_built"]
    yb_c = gdf_c_pool.set_index("osm_id")["year_built"]
    prov_c = gdf_c_pool.set_index("osm_id")["provenance_year_built"]

    # Reload nyc_centre FRESH (native CRS, untouched geometry, exact committed
    # column order) -- splice ONLY year_built/provenance_year_built by osm_id.
    # This is stronger common-mode isolation than reusing the pooled/reprojected
    # frame: geometry is byte-identical to the committed source, not reprojected.
    nyc_raw = gpd.read_file(NYC_GPKG)
    assert set(nyc_raw.columns) == set(_INPUT_SCHEMA_COLUMNS), "nyc_centre schema drifted from classifier's expected input"
    nyc_raw = nyc_raw[_INPUT_SCHEMA_COLUMNS]  # classifier requires this exact column ORDER; content unchanged

    nyc_a = nyc_raw.copy()
    nyc_a["year_built"] = nyc_a["osm_id"].map(yb_a)
    nyc_a["provenance_year_built"] = nyc_a["osm_id"].map(prov_a)

    nyc_c = nyc_raw.copy()
    nyc_c["year_built"] = nyc_c["osm_id"].map(yb_c)
    nyc_c["provenance_year_built"] = nyc_c["osm_id"].map(prov_c)

    assert nyc_a["year_built"].notna().all() and nyc_c["year_built"].notna().all()
    n_diff_raw = int((nyc_a["year_built"].to_numpy() != nyc_c["year_built"].to_numpy()).sum())
    print(f"nyc_centre reload: n={len(nyc_raw)}, raw year_built differs on {n_diff_raw} rows (A vs C)")
    return nyc_a, nyc_c


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    assert NYC_EPW.exists(), f"NYC EPW not cached locally: {NYC_EPW}"

    nyc_a, nyc_c = build_variant_frames()

    (WORK / "phaseA").mkdir(parents=True, exist_ok=True)
    (WORK / "phaseC").mkdir(parents=True, exist_ok=True)

    print("\n--- Stage 2: classify + enrich (Phase-A branch, full cell) ---")
    gdf57_a, sched_a = step2_classify_enrich(nyc_a, NYC_EPW, WORK / "phaseA", "nyc_centre_phaseA")
    print("\n--- Stage 2: classify + enrich (Phase-C/knn branch, full cell) ---")
    gdf57_c, sched_c = step2_classify_enrich(nyc_c, NYC_EPW, WORK / "phaseC", "nyc_centre_phaseC")

    assert list(gdf57_a["osm_id"]) == list(gdf57_c["osm_id"]), "row order diverged between branches"

    # ── common-mode check across every column NOT derived from vintage ──────
    vintage_derived_hint = ("vintage", "u_value", "u_factor", "u_factor_roof",
                             "u_factor_wall", "u_factor_window", "envelope")
    suspect_cols = [c for c in gdf57_a.columns if any(h in c.lower() for h in vintage_derived_hint)]
    print(f"\nvintage/envelope-derived columns detected: {suspect_cols}")

    diff_cols = []
    for c in gdf57_a.columns:
        if c in ("year_built", "provenance_year_built", "data_quality_flag") or c in suspect_cols:
            continue
        a_vals, c_vals = gdf57_a[c], gdf57_c[c]
        try:
            if pd.api.types.is_numeric_dtype(a_vals) and pd.api.types.is_numeric_dtype(c_vals):
                same = np.allclose(
                    pd.to_numeric(a_vals, errors="coerce").to_numpy(dtype=float),
                    pd.to_numeric(c_vals, errors="coerce").to_numpy(dtype=float),
                    equal_nan=True,
                )
            elif c == "geometry":
                same = a_vals.geom_equals_exact(c_vals, tolerance=1e-9).all()
            else:
                same = a_vals.astype(str).equals(c_vals.astype(str))
        except Exception as exc:
            same = False
            print(f"  [warn] column {c!r} comparison raised {exc!r}; treating as differing")
        if not same:
            diff_cols.append(c)
    print(f"non-vintage columns that differ between Phase-A/Phase-C branches: {diff_cols}")

    # ── diverging rows (the only ones worth simulating) ──────────────────────
    n_diverge_yb = int((gdf57_a["year_built"].to_numpy() != gdf57_c["year_built"].to_numpy()).sum())
    diverge_cols_present = [c for c in suspect_cols if c in gdf57_a.columns]
    if diverge_cols_present:
        div_mask = np.zeros(len(gdf57_a), dtype=bool)
        for c in diverge_cols_present:
            a_v = gdf57_a[c].astype(str).to_numpy()
            c_v = gdf57_c[c].astype(str).to_numpy()
            div_mask |= (a_v != c_v)
    else:
        div_mask = gdf57_a["year_built"].to_numpy() != gdf57_c["year_built"].to_numpy()
    n_diverge = int(div_mask.sum())
    print(f"\nraw year_built differs on {n_diverge_yb} rows; EUI-relevant (vintage/envelope) divergence on {n_diverge} rows")

    diverge_osm_ids = gdf57_a.loc[div_mask, "osm_id"].tolist()
    (WORK / "diverge_osm_ids.txt").write_text("\n".join(diverge_osm_ids), encoding="utf-8")
    print(f"wrote {len(diverge_osm_ids)} diverging osm_ids -> {WORK / 'diverge_osm_ids.txt'}")

    if n_diverge == 0:
        print("\nRESULT: zero EUI-relevant divergence after full enrichment -- contradicts the earlier "
              "standalone vintage-bin check; STOPPING (no cluster escalation, no IDFs built).")
        return

    sub_a = gdf57_a.loc[div_mask].reset_index(drop=True)
    sub_c = gdf57_c.loc[div_mask].reset_index(drop=True)

    print(f"\n--- Stage 3: IDF generation for {len(sub_a)} diverging buildings (Phase-A) ---")
    manifest_a = step3_generate(sub_a, sched_a, WORK / "phaseA" / "step3")
    print(f"\n--- Stage 3: IDF generation for {len(sub_c)} diverging buildings (Phase-C/knn) ---")
    manifest_c = step3_generate(sub_c, sched_c, WORK / "phaseC" / "step3")

    ok_a = (manifest_a["generation_status"] == "success").sum()
    ok_c = (manifest_c["generation_status"] == "success").sum()
    print(f"\nIDF generation: A {ok_a}/{len(manifest_a)} success, C {ok_c}/{len(manifest_c)} success")

    manifest_a.to_parquet(WORK / "manifest_a.parquet")
    manifest_c.to_parquet(WORK / "manifest_c.parquet")
    print(f"\nWrote manifests to {WORK}")


if __name__ == "__main__":
    main()
