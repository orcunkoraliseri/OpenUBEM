"""OPEN-42 T01: build open42_placeholder_trace.csv from the raw stage artifacts.
Measurement only. Reads phaseE (E-R3-3, pre-elevator) stage files on disk; writes
nothing back into those directories.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
PHASEE_ELEVRB = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE_elevrb"
AUDIT_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open01_denominator_audit.csv"

STEMS = {
    "la_rural": [
        "way_472960972", "way_472961034", "way_472961088",
        "way_472961091", "way_472961171",
    ],
    "la_urban": ["way_402215469"],
}

rows = []

for cell, stems in STEMS.items():
    # Stage 1 — acquisition (01_buildings.gpkg)
    gdf = gpd.read_file(str(PHASEE / cell / "01_buildings.gpkg"))
    gdf["stem"] = gdf["osm_id"].astype(str).str.replace("/", "_", regex=False)
    gdf["polygon_area_m2"] = gdf.geometry.area
    sub1 = gdf[gdf["stem"].isin(stems)]
    for _, r in sub1.iterrows():
        rows.append({
            "stem": r["stem"], "cell": cell, "stage": "1_acquisition",
            "source_file": "docs/docs_VALIDATION/validations/overAll/results/phaseE/"
                            f"{cell}/01_buildings.gpkg",
            "footprint_area_m2": r["footprint_area_m2"],
            "polygon_area_m2": r["polygon_area_m2"],
            "note": f"real OSM-derived footprint; levels={r['levels']}; "
                    "geometry.area (EPSG:32611) matches stored footprint_area_m2 exactly",
        })

    # Stage "2/3" — no persisted manifest artifact between Stage 1 and Stage 4/5 for this
    # pipeline run; enrichment happens in-memory inside scripts/validation/v12_cell_pipeline.py
    # (_build_enriched_gdf). Reported as untraced-to-a-file, not skipped.
    for stem in stems:
        rows.append({
            "stem": stem, "cell": cell, "stage": "2_3_enrichment_idf",
            "source_file": "NONE FOUND ON DISK (03_manifest.parquet does not exist for this cell)",
            "footprint_area_m2": "",
            "polygon_area_m2": "",
            "note": "no persisted Stage-2/3 artifact; enrichment + IDF build run in-memory "
                    "inside scripts/validation/v12_cell_pipeline.py in the same process that "
                    "writes 04_simulation_manifest.parquet and 05_results",
        })

    # Stage 4 — simulation manifest (04_simulation_manifest.parquet), both phaseE and phaseE_elevrb
    for label, base in [("phaseE", PHASEE), ("phaseE_elevrb", PHASEE_ELEVRB)]:
        sim_mf = pd.read_parquet(base / cell / "04_simulation_manifest.parquet")
        sim_mf["stem"] = sim_mf["osm_id"].astype(str).str.replace("/", "_", regex=False)
        sub4 = sim_mf[sim_mf["stem"].isin(stems)]
        for _, r in sub4.iterrows():
            rows.append({
                "stem": r["stem"], "cell": cell, "stage": f"4_sim_manifest_{label}",
                "source_file": f"docs/docs_VALIDATION/validations/overAll/results/{label}/"
                                f"{cell}/04_simulation_manifest.parquet",
                "footprint_area_m2": "",
                "polygon_area_m2": "",
                "note": f"no footprint_area_m2 column in this file; status={r['status']}, "
                        f"n_severe={r['n_severe']}",
            })

    # Stage 5 — results (05_results.csv), both phaseE and phaseE_elevrb
    for label, base in [("phaseE", PHASEE), ("phaseE_elevrb", PHASEE_ELEVRB)]:
        res = pd.read_csv(base / cell / "05_results.csv")
        res["stem"] = res["osm_id"].astype(str).str.replace("/", "_", regex=False)
        sub5 = res[res["stem"].isin(stems)]
        for _, r in sub5.iterrows():
            rows.append({
                "stem": r["stem"], "cell": cell, "stage": f"5_results_{label}",
                "source_file": f"docs/docs_VALIDATION/validations/overAll/results/{label}/"
                                f"{cell}/05_results.csv",
                "footprint_area_m2": r["footprint_area_m2"],
                "polygon_area_m2": "",
                "note": f"WRITER: scripts/validation/v12_cell_pipeline.py:659 "
                        f"(_build_enriched_gdf default, never overwritten because "
                        f"simulation_status={r['simulation_status']} != success); "
                        f"total_eui_kwh_m2={r['total_eui_kwh_m2']}",
            })

    # Stage 5 — E02 harvest audit (open01_denominator_audit.csv, auto mode) — separate diagnostic
    # simulation campaign (40,800 runs), not the adopted single-run baseline.
    audit = pd.read_csv(AUDIT_CSV)
    sub_audit = audit[(audit["cell"] == cell) & (audit["mode"] == "auto") & (audit["stem"].isin(stems))]
    for _, r in sub_audit.iterrows():
        rows.append({
            "stem": r["stem"], "cell": cell, "stage": "5_results_E02_harvest_auto",
            "source_file": "openubem/outputs/comparisons/open01_denominator_audit.csv",
            "footprint_area_m2": r["footprint_area_m2"],
            "polygon_area_m2": "",
            "note": f"separate E02 diagnostic campaign (40,800 runs, not the adopted baseline); "
                    f"area_multiplier_aware_m2(simulated)={r['area_multiplier_aware_m2']}, "
                    f"error_factor={r['error_factor']}",
        })

out = pd.DataFrame(rows)
out_path = ROOT / "openubem" / "outputs" / "comparisons" / "open42_placeholder_trace.csv"
out.to_csv(out_path, index=False)
print(f"wrote {out_path} ({len(out)} rows)")
print(out.to_string())
