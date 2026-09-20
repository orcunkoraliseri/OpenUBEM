"""FLEET-06a (techtransfer block-6 plan) -- build the 65,112-row scenario manifest.

Combines two already-prepared IDF sources into the full-factorial campaign's on-disk
manifest, per `PLAN_techtransfer-block6-2026-09-18.md`'s FLEET-06a correction:

- `baseline` cell: the existing 2026-09-09 T07 IDFs, fetched unmodified from Speed
  (`fleet06a_fetch_baseline_2026-09-18` step, scp/rsync only) -- zero PV, zero measures,
  matches the adopted 153.95 kWh/m2 / 8,139-building figure by construction. Not run
  through `run_campaign()` at all; copied into the manifest as-is.
- The 7 non-baseline cells: built from the fresh, today's-code IDFs produced by
  `scripts/analysis/fleet06a_rebuild_2026-09-18.py` (PV_INJECTION_ENABLED=True baked in),
  with `openubem.scenarios.campaign.apply_cell()` (the same unmodified function
  `run_campaign()` itself calls) applying each cell's measures.

Population is the 8,139 T08-successful building IDs
(`openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv`, columns `stem`,
`cell` -- `cell` here is the geographic cell, used only to locate each building's fresh
rebuilt IDF under the right `fleet06a_rebuild_2026-09-18/<cell>/step3/idfs/` folder).

No EnergyPlus run happens anywhere in this script.

Usage: py fleet06a_campaign_2026-09-18.py
"""
from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

T08_CSV = REPO / "openubem" / "outputs" / "comparisons" / "t08_restated_fleet_eui_2026-09-10.csv"
REBUILD_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "fleet06a_rebuild_2026-09-18"
BASELINE_DIR = Path(tempfile.gettempdir()) / "ubem_validation" / "fleet06a_2026-09-18" / "baseline_idfs"
OUTPUT_ROOT = Path(tempfile.gettempdir()) / "ubem_validation" / "fleet06a_campaign_2026-09-18"
MANIFEST_PATH = OUTPUT_ROOT / "manifest_65112.csv"
MAX_WORKERS = 20


def _load_population() -> "list[tuple[str, str]]":
    rows = []
    with open(T08_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row["stem"], row["cell"]))
    return rows


def _init_worker() -> None:
    global GeomIDF
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF as _GeomIDF
    from openubem import config
    GeomIDF = _GeomIDF
    try:
        GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass


def _build_building(args):
    stem, cell_geog, cell_spec = args
    from openubem.scenarios.campaign import Cell, apply_cell
    fresh_path = REBUILD_BASE / cell_geog / "step3" / "idfs" / f"{stem}.idf"
    rows = []
    if not fresh_path.exists():
        return stem, [], f"MISSING_FRESH:{fresh_path}"
    for cell_name, measure_ids in cell_spec:
        cell = Cell(name=cell_name, measure_ids=tuple(measure_ids))
        idf = GeomIDF(str(fresh_path))
        apply_cell(idf, cell, enabled=True)
        out_dir = OUTPUT_ROOT / cell_name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{stem}.idf"
        idf.saveas(str(out_path))
        rows.append((stem, cell_name, str(out_path)))
    return stem, rows, None


def main() -> int:
    from openubem.scenarios.campaign import build_full_factorial_campaign

    cells = build_full_factorial_campaign()
    non_baseline = [c for c in cells if c.name != "baseline"]
    cell_spec = [(c.name, list(c.measure_ids)) for c in non_baseline]
    print(f"non-baseline cells ({len(non_baseline)}): {[c.name for c in non_baseline]}")

    population = _load_population()
    print(f"population: {len(population)}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    baseline_dir = OUTPUT_ROOT / "baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows: "list[tuple[str, str, str]]" = []
    missing_baseline = []
    for stem, cell_geog in population:
        src = BASELINE_DIR / f"{stem}.idf"
        if not src.exists():
            missing_baseline.append(stem)
            continue
        dst = baseline_dir / f"{stem}.idf"
        shutil.copy2(src, dst)
        manifest_rows.append((stem, "baseline", str(dst)))
    print(f"baseline cell: {len(manifest_rows)} copied, {len(missing_baseline)} missing")
    if missing_baseline:
        print(f"MISSING baseline stems ({len(missing_baseline)}, first 20): {missing_baseline[:20]}")

    tasks = [(stem, cell_geog, cell_spec) for stem, cell_geog in population]
    t0 = time.time()
    done = 0
    missing_fresh = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS, initializer=_init_worker) as ex:
        futures = {ex.submit(_build_building, t): t[0] for t in tasks}
        for fut in as_completed(futures):
            stem, rows, err = fut.result()
            if err:
                missing_fresh.append(err)
            manifest_rows.extend(rows)
            done += 1
            if done % 500 == 0:
                elapsed = time.time() - t0
                print(f"  {done}/{len(tasks)} buildings done (+{elapsed:.0f}s)", flush=True)

    elapsed = time.time() - t0
    print(f"non-baseline generation done in {elapsed:.0f}s")
    if missing_fresh:
        print(f"MISSING fresh IDFs: {len(missing_fresh)}")
        for m in missing_fresh[:20]:
            print(" ", m)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["building_id", "cell_name", "output_idf_path"])
        for row in manifest_rows:
            w.writerow(row)

    print(f"TOTAL manifest rows: {len(manifest_rows)}")
    print(f"Manifest written to {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
