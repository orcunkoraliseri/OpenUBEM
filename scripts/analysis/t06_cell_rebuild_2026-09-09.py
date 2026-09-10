"""T06 (accuracy-restatement plan) -- rebuild fleet inputs + IDFs for one cell.

Runs ONLY Steps 1-3 of the existing v12_cell_pipeline harness (frozen-input load,
classify+enrich, IDF generation) on today's code. Never ships to the Speed cluster,
never submits or polls a SLURM array, never runs EnergyPlus -- CP-2 (director
sign-off) gates everything past this point (plan Sec 6 T06/T07, Sec 7).

Step 1's raw population is seeded from the byte-frozen evidence copy at
evidence/open48_refleet/<cell>/01_buildings.gpkg (the same input run 4 itself
used -- v12_cell_pipeline.step1_fetch only re-fetches from OSM live when no
cached 01_buildings.gpkg exists in the work dir, and CLAUDE.md forbids live
network fetches for this local step; run-4's own local temp caches have since
been purged by normal OS temp cleanup, so this evidence/ copy is the only
surviving frozen source and its row counts already reconcile to 8,160 -- see
t06 fleet rebuild orchestrator).

Usage: py t06_cell_rebuild_2026-09-09.py <cell_name> <output_subdir>
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from scripts.validation.v12_cell_pipeline import (  # noqa: E402
    CELL_CONFIGS,
    resolve_epw,
    step1_fetch,
    step2_classify_enrich,
    step3_generate,
)

EVIDENCE = REPO / "evidence" / "open48_refleet"


def main() -> int:
    cell_name = sys.argv[1]
    output_subdir = sys.argv[2]

    cfg_cell = CELL_CONFIGS[cell_name]
    lat, lon, radius_m = cfg_cell["lat"], cfg_cell["lon"], cfg_cell["radius_m"]

    import tempfile
    work_base = Path(tempfile.gettempdir()) / "ubem_validation" / output_subdir / cell_name
    work_base.mkdir(parents=True, exist_ok=True)
    step3_dir = work_base / "step3"

    seed_src = EVIDENCE / cell_name / "01_buildings.gpkg"
    seed_dst = work_base / "01_buildings.gpkg"
    if not seed_dst.exists():
        if not seed_src.exists():
            print(f"[{cell_name}] FATAL: no frozen seed at {seed_src}", flush=True)
            return 2
        shutil.copy2(seed_src, seed_dst)
        print(f"[{cell_name}] seeded 01_buildings.gpkg from evidence/ (frozen, no live fetch)", flush=True)

    t0 = time.monotonic()
    epw_path, epw_station_name = resolve_epw(lat, lon, work_base / "weather")

    gdf_raw = step1_fetch(lat, lon, radius_m, work_base)
    n_raw = len(gdf_raw)
    print(f"[{cell_name}] Step1 raw: {n_raw}", flush=True)

    gdf_57, schedule_library = step2_classify_enrich(gdf_raw, epw_path, work_base, cell_name)
    n_enriched = len(gdf_57)
    print(f"[{cell_name}] Step2 enriched: {n_enriched}", flush=True)

    stale_manifest = step3_dir / "03_idf_manifest.parquet"
    if stale_manifest.exists():
        stale_manifest.unlink()
        print(f"[{cell_name}] cleared stale manifest for fresh regen", flush=True)

    idf_manifest = step3_generate(gdf_57, schedule_library, step3_dir)
    n_manifest = len(idf_manifest)
    status_counts = idf_manifest["generation_status"].value_counts().to_dict()
    n_success = int(status_counts.get("success", 0))
    elapsed = time.monotonic() - t0

    summary = {
        "cell": cell_name,
        "n_raw": n_raw,
        "n_enriched": n_enriched,
        "n_manifest": n_manifest,
        "n_idf_success": n_success,
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "epw_station": epw_station_name,
        "elapsed_s": elapsed,
        "step3_dir": str(step3_dir),
    }
    (work_base / "t06_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[{cell_name}] DONE raw={n_raw} enriched={n_enriched} idf_success={n_success}/{n_manifest} "
          f"({elapsed:.1f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
