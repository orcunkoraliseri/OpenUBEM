"""B05f: rebuild both layout_assign viewers from REAL BuildingIDF.build() output
(post-B05 code), overwriting figures/{nyc,la}_suburban_layout_assign_viewer.html
in place -- PLAN_storey-matching_implementation.md B05f.

Per the CP-B audit (E-LA-30): a4_bis_generate_layout_assign_viewer.py's
fast_scale_idf_text() is a measured content no-op on all 25 baseline
prototypes (case-sensitive class-name gate + one-coordinate-per-line
assumption, neither of which matches this library's IDF text), so every
building in the old A4-bis viewer scenes was the raw S=1 prototype. This
script does NOT reuse that generator. It runs the two headline cells
(nyc_suburban, la_suburban) through the real Step-2 + Step-3 pipeline with
resolution_mode="layout_assign" and feeds the resulting IDFs to export_viewer()
directly -- the same mechanism T19's fleet sweep uses, not a reimplementation.

Also (cheap, since Step 3 alone needs no EnergyPlus) builds a PRE-B05 pipeline
scene for the same two cells by monkeypatching layout_assigner.scale_baseline_idf
back to its pre-B05 body for that pass only (same technique as
b05e_measure_energy_delta.py) -- so the overlap re-measurement can report a
genuine pre-B05 pipeline number instead of citing the void fast_scale_idf_text()
baseline (E-LA-30's own instruction: do not compare against 4,043/98.24% or
4,003/97.17%).

The archived "before" files at figures/before_B05/*_BEFORE_B05.html are NEVER
touched by this script -- they are irreplaceable (E-LA-28 discovery artifacts)
and are a separate thing from the "pre-B05 pipeline" scene this script builds
fresh under a different filename.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

from openubem.geometry import layout_assigner
from openubem.viz.viewer_export import export_viewer

sys.path.insert(0, str(REPO / "scripts" / "cluster"))
from t19_layout_assign_full_sweep import run_step2, run_step3_mode, CELL_CONFIGS  # noqa: E402

# Same pre-B05 replica used by b05e_measure_energy_delta.py -- kept in sync by
# hand (both files quote the current scale_baseline_idf() body verbatim minus
# the new Zone Origin loop).
def _scale_baseline_idf_pre_b05(idf, scale_factor_dict):
    planar_k = scale_factor_dict["planar_scale_factor"]
    area_s = scale_factor_dict["area_scale_ratio"]
    for cls in layout_assigner._GEOMETRY_SURFACE_CLASSES:
        for surf in idf.idfobjects.get(cls, []):
            scaled_coords = [(x * planar_k, y * planar_k, z) for x, y, z in surf.coords]
            surf.setcoords(scaled_coords)
    for cls, x_field, y_field in layout_assigner._GEOMETRY_POINT_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            x_val, y_val = getattr(obj, x_field), getattr(obj, y_field)
            if not layout_assigner._is_blank_or_autosize(x_val):
                setattr(obj, x_field, float(x_val) * planar_k)
            if not layout_assigner._is_blank_or_autosize(y_val):
                setattr(obj, y_field, float(y_val) * planar_k)
    for cls, method_field, value_field, absolute_method in layout_assigner._ABSOLUTE_LOAD_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(getattr(obj, method_field, "")).strip() != absolute_method:
                continue
            val = getattr(obj, value_field)
            if layout_assigner._is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)
    for cls, value_field in layout_assigner._UNCONDITIONAL_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            val = getattr(obj, value_field)
            if layout_assigner._is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)
    for cls, obj_name, value_field, s1_value in layout_assigner._NAMED_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(obj.Name).strip() != obj_name:
                continue
            val = getattr(obj, value_field)
            if not layout_assigner._is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, s1_value * area_s)
    return idf


REPO_OUT = REPO / "openubem" / "outputs"
FIG_DIR = (
    REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner"
    / "debug" / "storey-Matching" / "figures"
)
PHASED_RESULTS = REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
T19_EUI_CSV = REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner" / "results" / "t19_layout_assign_eui.csv"

CELLS = ["nyc_suburban", "la_suburban"]
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_b05f_work"


def build_cell_manifest(cell: str, work_base: Path, pre_b05: bool) -> tuple[pd.DataFrame, gpd.GeoDataFrame, Path]:
    cfg = CELL_CONFIGS[cell]
    fixture_dir = PHASED_RESULTS / cell
    buildings_path = fixture_dir / "01_buildings.gpkg"
    gdf_raw = gpd.read_file(str(buildings_path))

    gdf_57, schedule_library, epw_path = run_step2(gdf_raw, cell, cfg, work_base)

    real_fn = layout_assigner.scale_baseline_idf
    if pre_b05:
        layout_assigner.scale_baseline_idf = _scale_baseline_idf_pre_b05
    try:
        manifest = run_step3_mode(gdf_57, schedule_library, cell, "layout_assign", work_base, n_jobs=6)
    finally:
        layout_assigner.scale_baseline_idf = real_fn

    return manifest, gdf_raw, epw_path


def build_and_export(cell: str, variant: str, pre_b05: bool, out_dir: Path) -> dict:
    work_base = WORK_BASE / variant
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {cell} / {variant} (pre_b05={pre_b05}) ===")
    t0 = time.monotonic()
    manifest, gdf_raw, _epw = build_cell_manifest(cell, work_base, pre_b05=pre_b05)
    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"  Step 3: {n_ok}/{len(manifest)} success in {time.monotonic()-t0:.1f}s")

    mdf = manifest[manifest["generation_status"] == "success"][["osm_id", "idf_path"]].copy()

    df_res = pd.read_csv(T19_EUI_CSV)
    rdf_cell = df_res[df_res["cell"] == cell].copy()

    run_id = f"{cell}_layout_assign_{variant}"
    res = export_viewer(mdf, gdf_raw, rdf_cell, run_id=run_id, out_dir=out_dir)
    print(f"  export_viewer: {res['n_buildings']} buildings, {res['size_bytes']/1e6:.2f} MB -> {res['html_path']}")
    return {"cell": cell, "variant": variant, "n_manifest": len(manifest), "n_success": n_ok, **res}


def main():
    out_tmp = WORK_BASE / "viewer_html"
    out_tmp.mkdir(parents=True, exist_ok=True)

    export_records = []
    for cell in CELLS:
        # --- AFTER (post-B05, current production code) -- this is the artifact
        # that overwrites figures/{cell}_layout_assign_viewer.html in place.
        rec_after = build_and_export(cell, "after_B05", pre_b05=False, out_dir=out_tmp)
        export_records.append(rec_after)
        src = Path(rec_after["html_path"])
        dst_flat = REPO_OUT / f"{cell}_layout_assign_viewer.html"
        dst_arc = FIG_DIR / f"{cell}_layout_assign_viewer.html"
        shutil.copy2(src, dst_flat)
        shutil.copy2(src, dst_arc)
        print(f"  Overwrote {dst_flat} ({dst_flat.stat().st_size} bytes)")
        print(f"  Overwrote {dst_arc} ({dst_arc.stat().st_size} bytes)")

        # --- PRE-B05 pipeline (cheap: IDF generation only, no EnergyPlus) --
        # kept under a NEW filename, never touching figures/before_B05/.
        rec_before = build_and_export(cell, "pre_B05_pipeline", pre_b05=True, out_dir=out_tmp)
        export_records.append(rec_before)
        dst_pre_arc = FIG_DIR / f"{cell}_layout_assign_pre_B05_pipeline_viewer.html"
        shutil.copy2(Path(rec_before["html_path"]), dst_pre_arc)
        print(f"  Wrote NEW pre-B05-pipeline reference scene: {dst_pre_arc} ({dst_pre_arc.stat().st_size} bytes)")

    df = pd.DataFrame(export_records)
    out_csv = FIG_DIR / "b05f_viewer_rebuild_summary.csv"
    df.to_csv(out_csv, index=False)
    df.to_csv(REPO_OUT / "comparisons" / "b05f_viewer_rebuild_summary.csv", index=False)
    print(f"\nWrote {out_csv}")


if __name__ == "__main__":
    main()
