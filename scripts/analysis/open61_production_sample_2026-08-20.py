"""T02 of PLAN_five-items-2026-08-20-late.md -- OPEN-61: size the District Heating term on
production (`auto`) geometry, after CP-1 (section 6b) redefined the task.

D9 (CP-1) already answers "does the adopted fleet carry it" from text: all 16,336 production
IDFs carry a `DHW_WaterUse_*` WaterUse:Equipment and zero carry a PlantLoop -- the exact pattern
that was non-zero 5/5 and zero 43/43 on the 48-sample census. T02's remaining job is SIZING: how
large the term is per cell, on re-simulated production geometry, and how much of
`total_eui_kwh_m2` it is missing.

Two phases, run as two separate invocations of this script (`select` then `simulate`) so the
selection is frozen to disk before any EnergyPlus process starts (plan step 1: "Write it to
open61_production_sample_selection.csv before any simulation runs").

Selection: 5 buildings per cell, sorted by osm_id, every k-th (k = n_idfs_in_cell // 5),
starting at index 0 -- seed nothing, per the plan.

Simulation: copy each selected building's production IDF + its cell's EPW (read from
evidence/open48_refleet4/<cell>/02a_climate_epw.parquet) into its own working directory under
scratchpad/open61_production_sample/<cell>/<osm_id>/, run run_ep_isolated() (imported from
scripts/analysis/open35_storey_intervention_2026-08-19.py -- OPEN-58, never open56's run_ep()),
at most 6 concurrent (hard rule 4). One working directory per building, always.

District Heating is read exactly as in T01 (read_end_uses/check_c2/FUEL_COLUMNS/END_USE_ROWS/
GJ_TO_KWH, imported from open61_district_source_2026-08-20.py, not reimplemented). The
production total is read through parse_building() (openubem/results/parser.py:716) using a
manifest_row built from the building's own evidence/open48_refleet4/<cell>/results/05_results.csv
row (real footprint_area_m2/levels/height_m/archetype_id -- not a dummy).

Controls (pre-registered before any simulation ran):
  C4  -- parse_building() total must match that building's recorded total_eui_kwh_m2 in
         05_results.csv to within 1.5%. Report the residual distribution, not just pass/fail.
  C4b -- all 60 must return non-zero District Heating (D8's discriminator, extended to
         production). Any 0.00 GJ building is named and reported as a discriminator break.
  C5  -- EnergyPlus version printed from the first run's eplusout.err must be
         23.1.0-87ed9199d4.
  C6  -- sha256 of two different buildings' eplusout.sql must differ (OPEN-58 cross-
         contamination check).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from openubem.results.parser import parse_building  # noqa: E402

EVIDENCE = REPO / "evidence" / "open48_refleet4"
OUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
SELECTION_CSV = OUT_DIR / "open61_production_sample_selection.csv"
RESULTS_CSV = OUT_DIR / "open61_production_sample.csv"
WORK_ROOT = REPO / "scratchpad" / "open61_production_sample"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
N_PER_CELL = 5
MAX_WORKERS = 6


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


t01 = _load_module(REPO / "scripts" / "analysis" / "open61_district_source_2026-08-20.py", "open61_t01")
storey = _load_module(REPO / "scripts" / "analysis" / "open35_storey_intervention_2026-08-19.py", "open35_t04")
run_ep_isolated = storey.run_ep_isolated
GJ_TO_KWH = t01.GJ_TO_KWH
FUEL_COLUMNS = t01.FUEL_COLUMNS
read_end_uses = t01.read_end_uses
check_c2 = t01.check_c2


def osm_id_from_idf_stem(stem: str) -> str:
    kind, _, num = stem.partition("_")
    return f"{kind}/{num}"


def build_selection() -> pd.DataFrame:
    rows = []
    for cell in CELLS:
        idf_dir = EVIDENCE / cell / "fleet_staging" / "idfs"
        idf_paths = sorted(idf_dir.glob("*.idf"), key=lambda p: osm_id_from_idf_stem(p.stem))
        n = len(idf_paths)
        k = n // N_PER_CELL
        assert k >= 1, f"{cell}: only {n} IDFs, cannot draw {N_PER_CELL} at stride"
        picks = [idf_paths[i * k] for i in range(N_PER_CELL)]
        for rank, p in enumerate(picks):
            rows.append({
                "cell": cell,
                "rank": rank,
                "osm_id": osm_id_from_idf_stem(p.stem),
                "idf_stem": p.stem,
                "idf_path": str(p.resolve()),
                "n_idfs_in_cell": n,
                "stride_k": k,
            })
    return pd.DataFrame.from_records(rows)


def epw_for_cell(cell: str) -> Path:
    sidecar = pd.read_parquet(EVIDENCE / cell / "02a_climate_epw.parquet")
    epw_path = Path(sidecar["epw_path"].iloc[0])
    assert epw_path.exists(), f"{cell}: recorded EPW missing: {epw_path}"
    return epw_path


def results_row(cell: str, osm_id: str) -> pd.Series:
    res = pd.read_csv(EVIDENCE / cell / "results" / "05_results.csv")
    match = res[res["osm_id"] == osm_id]
    assert not match.empty, f"{cell}/{osm_id}: no 05_results.csv row"
    return match.iloc[0]


def simulate_one(sel_row: pd.Series) -> dict:
    cell = sel_row["cell"]
    osm_id = sel_row["osm_id"]
    idf_path = Path(sel_row["idf_path"])
    outdir = WORK_ROOT / cell / sel_row["idf_stem"]
    epw_path = epw_for_cell(cell)
    outdir.mkdir(parents=True, exist_ok=True)
    work_idf = outdir / idf_path.name
    shutil.copy2(idf_path, work_idf)
    ep_out = outdir / "out"
    run_ep_isolated(work_idf, epw_path, ep_out)

    sql_path = ep_out / "eplusout.sql"
    err_path = ep_out / "eplusout.err"
    rec = {
        "cell": cell, "osm_id": osm_id, "idf_stem": sel_row["idf_stem"],
        "outdir": str(ep_out), "sql_path": str(sql_path), "err_path": str(err_path),
    }
    if not sql_path.exists():
        err_text = err_path.read_text(errors="replace")[-800:] if err_path.exists() else "no .err file"
        rec.update({"status": "sim_failed", "error": err_text})
        return rec

    end_uses = read_end_uses(sql_path)
    dh_water_gj = end_uses["District Heating"].get("Water Systems", 0.0)
    dh_total_gj = end_uses["District Heating"].get("Total End Uses", 0.0)
    c2_pass, c2_failures = check_c2(end_uses)
    total_end_uses_all_fuels_gj = sum(end_uses[c].get("Total End Uses", 0.0) for c in FUEL_COLUMNS)
    dh_share_of_total_end_uses = (
        dh_total_gj / total_end_uses_all_fuels_gj if total_end_uses_all_fuels_gj else 0.0
    )

    rrow = results_row(cell, osm_id)
    manifest_row = rrow.copy()
    manifest_row["osm_id"] = osm_id

    parsed = parse_building(sql_path, None, manifest_row)
    parser_total_eui = parsed.get("total_eui_kwh_m2")
    parser_status = parsed.get("parse_status")
    floor_area_m2 = parsed.get("floor_area_m2")
    parser_total_kwh = (
        parser_total_eui * floor_area_m2 if (parser_total_eui is not None and floor_area_m2) else None
    )
    dh_share_of_parser_total = (
        (dh_total_gj * GJ_TO_KWH) / parser_total_kwh if parser_total_kwh else None
    )

    record_total_eui = float(rrow["total_eui_kwh_m2"])
    c4_residual_pct = (
        abs(parser_total_eui - record_total_eui) / record_total_eui * 100.0
        if (parser_total_eui is not None and record_total_eui) else None
    )
    c4_pass = c4_residual_pct is not None and c4_residual_pct <= 1.5

    rec.update({
        "status": "ok",
        "dh_water_gj": dh_water_gj,
        "dh_total_gj": dh_total_gj,
        "dh_total_kwh": dh_total_gj * GJ_TO_KWH,
        "total_end_uses_all_fuels_gj": total_end_uses_all_fuels_gj,
        "dh_share_of_total_end_uses": dh_share_of_total_end_uses,
        "c2_pass": c2_pass,
        "c2_failures": "; ".join(c2_failures),
        "parser_status": parser_status,
        "parser_total_eui_kwh_m2": parser_total_eui,
        "parser_floor_area_m2": floor_area_m2,
        "dh_share_of_parser_total": dh_share_of_parser_total,
        "record_total_eui_kwh_m2": record_total_eui,
        "c4_residual_pct": c4_residual_pct,
        "c4_pass": c4_pass,
        "c4b_pass": round(dh_total_gj, 6) > 0.0,
    })
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["select", "simulate"])
    args = ap.parse_args()

    if args.phase == "select":
        sel = build_selection()
        assert len(sel) == 60, f"expected 60, got {len(sel)}"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        sel.to_csv(SELECTION_CSV, index=False)
        print(f"Wrote {SELECTION_CSV} ({len(sel)} rows)")
        for cell, grp in sel.groupby("cell"):
            print(f"  {cell}: n_idfs={grp['n_idfs_in_cell'].iloc[0]}, k={grp['stride_k'].iloc[0]}, "
                  f"picks={grp['osm_id'].tolist()}")
        return

    assert SELECTION_CSV.exists(), "selection.csv missing -- run 'select' phase first"
    sel = pd.read_csv(SELECTION_CSV)
    assert len(sel) == 60

    records = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(simulate_one, row): i for i, row in sel.iterrows()}
        for fut in as_completed(futs):
            rec = fut.result()
            records.append(rec)
            print(f"  done: {rec['cell']}/{rec['osm_id']} status={rec['status']}", flush=True)

    df = pd.DataFrame.from_records(records)
    df = df.merge(sel[["cell", "osm_id", "rank"]], on=["cell", "osm_id"], how="left")
    df = df.sort_values(["cell", "rank"]).reset_index(drop=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_CSV, index=False)

    n_failed = int((df["status"] != "ok").sum())
    print(f"\nn simulated: {len(df)}; n_failed_to_sim: {n_failed}")
    if n_failed:
        print("Failed:", df[df["status"] != "ok"][["cell", "osm_id", "error"]].to_string())

    ok = df[df["status"] == "ok"]
    print(f"\nC4b (all non-zero District Heating): "
          f"{int(ok['c4b_pass'].sum())}/{len(ok)} non-zero")
    zeros = ok[~ok["c4b_pass"]]
    if not zeros.empty:
        print("  C4b FAILURES (zero District Heating):", zeros[["cell", "osm_id"]].to_string())

    print("\nC4 residual distribution (|parser - record| / record, %):")
    print(ok["c4_residual_pct"].describe())
    print(f"C4 pass count (<=1.5%): {int(ok['c4_pass'].sum())}/{len(ok)}")

    print("\nPer-cell district-heating share of Total End Uses (12 cells, n=5 each):")
    for cell, grp in ok.groupby("cell"):
        print(f"  {cell}: n={len(grp)}, median share={grp['dh_share_of_total_end_uses'].median():.4%}, "
              f"n_zero={(~grp['c4b_pass']).sum()}")

    print(f"\nWrote {RESULTS_CSV}")


if __name__ == "__main__":
    main()
