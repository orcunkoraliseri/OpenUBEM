"""B08b: rebuild both layout_assign viewers from REAL BuildingIDF.build() output
(post-B08b code, D8's re-centring applied), overwriting
figures/{nyc,la}_suburban_layout_assign_viewer.html in place --
PLAN_storey-matching_implementation.md B08b.

Same mechanism as b05f_rebuild_layout_assign_viewers.py (real Step-2 + Step-3
pipeline with resolution_mode="layout_assign", fed to export_viewer() directly
-- never the void A4-bis fast_scale_idf_text() generator, E-LA-30). Unlike
B05f this script does NOT also build a "before" pipeline scene: B08a already
established a genuine post-B05/pre-B08b reference exists on disk (the files
this task archives to figures/before_B08b/ before overwriting), so there is
no need to rebuild that state a second time here.

The archived "before" files (figures/before_B05/*_BEFORE_B05.html and
figures/before_B08b/*_BEFORE_B08b.html) are NEVER touched by this script.
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

from openubem.viz.viewer_export import export_viewer

sys.path.insert(0, str(REPO / "scripts" / "cluster"))
from t19_layout_assign_full_sweep import run_step2, run_step3_mode, CELL_CONFIGS  # noqa: E402

REPO_OUT = REPO / "openubem" / "outputs"
FIG_DIR = (
    REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner"
    / "debug" / "storey-Matching" / "figures"
)
PHASED_RESULTS = REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
T19_EUI_CSV = REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner" / "results" / "t19_layout_assign_eui.csv"

CELLS = ["nyc_suburban", "la_suburban"]
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_b08b_work"


def build_cell_manifest(cell: str, work_base: Path) -> tuple[pd.DataFrame, gpd.GeoDataFrame, Path]:
    cfg = CELL_CONFIGS[cell]
    fixture_dir = PHASED_RESULTS / cell
    buildings_path = fixture_dir / "01_buildings.gpkg"
    gdf_raw = gpd.read_file(str(buildings_path))

    gdf_57, schedule_library, epw_path = run_step2(gdf_raw, cell, cfg, work_base)
    manifest = run_step3_mode(gdf_57, schedule_library, cell, "layout_assign", work_base, n_jobs=6)
    return manifest, gdf_raw, epw_path


def build_and_export(cell: str, out_dir: Path) -> dict:
    work_base = WORK_BASE / "after_B08b"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {cell} / after_B08b ===")
    t0 = time.monotonic()
    manifest, gdf_raw, _epw = build_cell_manifest(cell, work_base)
    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"  Step 3: {n_ok}/{len(manifest)} success in {time.monotonic()-t0:.1f}s")

    mdf = manifest[manifest["generation_status"] == "success"][["osm_id", "idf_path"]].copy()

    df_res = pd.read_csv(T19_EUI_CSV)
    rdf_cell = df_res[df_res["cell"] == cell].copy()

    run_id = f"{cell}_layout_assign_after_B08b"
    res = export_viewer(mdf, gdf_raw, rdf_cell, run_id=run_id, out_dir=out_dir)
    print(f"  export_viewer: {res['n_buildings']} buildings, {res['size_bytes']/1e6:.2f} MB -> {res['html_path']}")
    return {"cell": cell, "variant": "after_B08b", "n_manifest": len(manifest), "n_success": n_ok, **res}


def main():
    out_tmp = WORK_BASE / "viewer_html"
    out_tmp.mkdir(parents=True, exist_ok=True)

    export_records = []
    for cell in CELLS:
        rec = build_and_export(cell, out_dir=out_tmp)
        export_records.append(rec)
        src = Path(rec["html_path"])
        dst_flat = REPO_OUT / f"{cell}_layout_assign_viewer.html"
        dst_arc = FIG_DIR / f"{cell}_layout_assign_viewer.html"
        shutil.copy2(src, dst_flat)
        shutil.copy2(src, dst_arc)
        print(f"  Overwrote {dst_flat} ({dst_flat.stat().st_size} bytes)")
        print(f"  Overwrote {dst_arc} ({dst_arc.stat().st_size} bytes)")

    df = pd.DataFrame(export_records)
    out_csv = FIG_DIR / "b08b_viewer_rebuild_summary.csv"
    df.to_csv(out_csv, index=False)
    df.to_csv(REPO_OUT / "comparisons" / "b08b_viewer_rebuild_summary.csv", index=False)
    print(f"\nWrote {out_csv}")
    print("DONE")


if __name__ == "__main__":
    main()
