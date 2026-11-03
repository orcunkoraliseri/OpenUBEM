"""FLEET-07b (techtransfer block-7 plan) -- rebuild the 7 scenario cells with archetype,
log every measure status.

Copy of the FLEET-06a builder logic (`scripts/analysis/fleet06a_campaign_2026-09-18.py`,
never modified) with the FLEET-07b changes from
`docs/docs_DONE/TechTransfer/implementation/PLAN_techtransfer-block7-fleet07-2026-09-26.md`
section 6:

- `archetype` (the building's `archetype_id` from
  `openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv`, ruling R3) is passed
  to every `apply_cell()` call, so `lighting_power_density` is in scope for the archetypes
  `measures.json` lists.
- Output goes to `fleet07_campaign_2026-09-26\\<cell>\\`, never into the FLEET-06a tree.
- `measure_status.csv`: one row per (stem, cell, measure_id) with the columns
  `stem, cell, measure_id, status, n_applied`, `n_applied` being whichever of
  `n_lowered` / `n_applied` / `n_tightened` the measure's own report dict carries.
- `manifest_changed.csv`: `building_id, cell_name, output_idf_path, geo_cell, epw_name`,
  only the (stem, cell) pairs where at least one measure in that cell has `n_applied > 0`.
  `epw_name` is the basename of the geographic cell's single EPW
  (`fleet06a_rebuild_2026-09-18/<geo_cell>/02a_climate_epw.parquet`, `epw_path` column,
  one unique value per geo cell -- same source fleet06b_local_run_2026-09-18.py uses).

Only the 7 non-baseline cells are built. `baseline` is untouched by any measure and is not
regenerated here (FLEET-06a's baseline copy already matches the adopted figure).

No EnergyPlus run happens anywhere in this script.

Usage: py fleet07_campaign_2026-09-26.py
"""
from __future__ import annotations

import csv
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

TEMP = Path(os.environ["TEMP"])
T08_CSV = REPO / "openubem" / "outputs" / "comparisons" / "t08_restated_fleet_eui_2026-09-10.csv"
REBUILD_BASE = TEMP / "ubem_validation" / "fleet06a_rebuild_2026-09-18"
OUTPUT_ROOT = TEMP / "ubem_validation" / "fleet07_campaign_2026-09-26"
MEASURE_STATUS_PATH = OUTPUT_ROOT / "measure_status.csv"
MANIFEST_CHANGED_PATH = OUTPUT_ROOT / "manifest_changed.csv"
MAX_WORKERS = 20

GEO_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

N_KEY_BY_MEASURE = {
    "lighting_power_density": "n_lowered",
    "thermostat_setback": "n_applied",
    "infiltration_tightening": "n_tightened",
}


def _build_epw_name_map() -> dict[str, str]:
    import pandas as pd

    cell_epw_name: dict[str, str] = {}
    for cell in GEO_CELLS:
        p = REBUILD_BASE / cell / "02a_climate_epw.parquet"
        df = pd.read_parquet(p)
        uniq = df["epw_path"].unique()
        if len(uniq) != 1:
            raise SystemExit(f"STOP: {cell} has {len(uniq)} distinct epw_path values, expected 1: {uniq}")
        cell_epw_name[cell] = Path(str(uniq[0])).name
    return cell_epw_name


def _load_population() -> "list[tuple[str, str, str]]":
    rows = []
    with open(T08_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row["stem"], row["cell"], row["archetype_id"]))
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
    stem, cell_geog, archetype, cell_spec = args
    from openubem.scenarios.campaign import Cell, apply_cell
    fresh_path = REBUILD_BASE / cell_geog / "step3" / "idfs" / f"{stem}.idf"
    idf_rows = []
    status_rows = []
    if not fresh_path.exists():
        return stem, idf_rows, status_rows, f"MISSING_FRESH:{fresh_path}"
    for cell_name, measure_ids in cell_spec:
        cell = Cell(name=cell_name, measure_ids=tuple(measure_ids))
        idf = GeomIDF(str(fresh_path))
        reports = apply_cell(idf, cell, enabled=True, archetype=archetype)
        cell_n_applied_total = 0
        for measure_id, report in zip(measure_ids, reports):
            n_key = N_KEY_BY_MEASURE[measure_id]
            n_applied = report.get(n_key, 0)
            cell_n_applied_total += n_applied
            status_rows.append((stem, cell_name, measure_id, report["status"], n_applied))
        out_dir = OUTPUT_ROOT / cell_name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{stem}.idf"
        idf.saveas(str(out_path))
        idf_rows.append((stem, cell_name, str(out_path), cell_n_applied_total))
    return stem, idf_rows, status_rows, None


def main() -> int:
    from openubem.scenarios.campaign import build_full_factorial_campaign

    cells = build_full_factorial_campaign()
    non_baseline = [c for c in cells if c.name != "baseline"]
    cell_spec = [(c.name, list(c.measure_ids)) for c in non_baseline]
    print(f"non-baseline cells ({len(non_baseline)}): {[c.name for c in non_baseline]}")

    cell_epw_name = _build_epw_name_map()

    population = _load_population()
    print(f"population: {len(population)}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    tasks = [(stem, cell_geog, archetype, cell_spec) for stem, cell_geog, archetype in population]
    geo_of_stem = {stem: cell_geog for stem, cell_geog, _archetype in population}

    t0 = time.time()
    done = 0
    missing_fresh = []
    status_rows_all = []
    changed_rows = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS, initializer=_init_worker) as ex:
        futures = {ex.submit(_build_building, t): t[0] for t in tasks}
        for fut in as_completed(futures):
            stem, idf_rows, status_rows, err = fut.result()
            if err:
                missing_fresh.append(err)
            status_rows_all.extend(status_rows)
            geo_cell = geo_of_stem[stem]
            epw_name = cell_epw_name[geo_cell]
            for stem_r, cell_name, out_path, cell_n_applied_total in idf_rows:
                if cell_n_applied_total > 0:
                    changed_rows.append((stem_r, cell_name, out_path, geo_cell, epw_name))
            done += 1
            if done % 500 == 0:
                elapsed = time.time() - t0
                print(f"  {done}/{len(tasks)} buildings done (+{elapsed:.0f}s)", flush=True)

    elapsed = time.time() - t0
    print(f"generation done in {elapsed:.0f}s")
    if missing_fresh:
        print(f"MISSING fresh IDFs: {len(missing_fresh)}")
        for m in missing_fresh[:20]:
            print(" ", m)

    with open(MEASURE_STATUS_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stem", "cell", "measure_id", "status", "n_applied"])
        for row in status_rows_all:
            w.writerow(row)
    print(f"measure_status rows: {len(status_rows_all)}")
    print(f"Written to {MEASURE_STATUS_PATH}")

    with open(MANIFEST_CHANGED_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["building_id", "cell_name", "output_idf_path", "geo_cell", "epw_name"])
        for row in changed_rows:
            w.writerow(row)
    print(f"manifest_changed rows: {len(changed_rows)}")
    print(f"Written to {MANIFEST_CHANGED_PATH}")

    total_idfs = len(population) * len(non_baseline) - len(missing_fresh)
    print(f"TOTAL IDFs written: {total_idfs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
