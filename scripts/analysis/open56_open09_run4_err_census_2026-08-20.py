"""T03 (amended) of PLAN_ten-live-items-2026-08-20-evening.md -- fleet .err census on the
adopted run (run 4, open48_refleet4).

Two measurements, one scan:
  - OPEN-56: "Indicated Zone Volume <= 0.0" volume-stub warning, fleet-wide on run 4. OPEN-56's
    "8,160 / 8,160 = 100.00 %" stub rate has only ever been derived on run-2 corpora (and on 70-
    and 16-building intervention samples) -- never on the adopted run's full corpus.
  - OPEN-09: "Inside surface heat balance did not converge" warning population, as an independent
    reproduction of extra/MEASUREMENT_open-09_run4-rederivation.md (T13, 2026-08-19), which
    reported 16 / 8,160 (0.1961 %), identical to run 2, cell for cell: la_centre 2, la_rural 10,
    la_suburban 3, la_urban 1, others 0. This is a confirmation, not a new measurement -- it must
    reproduce that population exactly or the join/corpus is suspect (C9).

Also censuses ** Severe ** and **  Fatal  ** (two-space form, E-LA-21) lines per building, using
the shared whitespace-tolerant matchers in openubem/results/err_parse.py rather than a literal
one-space substring check (the OPEN-45 defect).

NOT CheckWarmupConvergence -- that string has 0 occurrences in the auto corpus
(open29_eight_defect_adjudication_2026-08-19.csv, row E-LA-18). See the plan's T03 AMENDED block.

Read-only. No EnergyPlus invoked. Emits
openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv (one row per building).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from openubem.results.err_parse import SEVERE_RE, FATAL_RE  # noqa: E402

RUN4 = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"
CENSUS_CSV = OUT / "open61_census_fleet.csv"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

_VOLSTUB = re.compile(r"Indicated Zone Volume <= 0\.0")
_CONVERGE = re.compile(r"Inside surface heat balance did not converge")

EXPECTED_OPEN09_CELLS = {
    "la_centre": 2, "la_rural": 10, "la_suburban": 3, "la_urban": 1,
}


def main() -> int:
    status = {}
    for cell in CELLS:
        rp = RUN4 / cell / "results" / "05_results.csv"
        if rp.exists():
            df = pd.read_csv(rp)
            for oid, st in zip(df["osm_id"], df["simulation_status"]):
                status[(cell, str(oid).replace("/", "_"))] = st

    archetype = {}
    if CENSUS_CSV.exists():
        cdf = pd.read_csv(CENSUS_CSV, usecols=["cell", "osm_id", "archetype_id"])
        for cell, oid, arch in zip(cdf["cell"], cdf["osm_id"], cdf["archetype_id"]):
            archetype[(cell, str(oid).replace("/", "_"))] = arch

    rows = []
    short_cells = {}
    for cell in CELLS:
        d = RUN4 / cell / "sim_out"
        if not d.exists():
            short_cells[cell] = 0
            continue
        n = 0
        for run in sorted(d.iterdir()):
            err = run / "eplusout.err"
            if not err.exists():
                continue
            n += 1
            txt = err.read_text(encoding="utf-8", errors="replace")
            n_volstub = len(_VOLSTUB.findall(txt))
            n_converge = len(_CONVERGE.findall(txt))
            n_severe = len(SEVERE_RE.findall(txt))
            n_fatal = len(FATAL_RE.findall(txt))
            rows.append({
                "cell": cell,
                "stem": run.name,
                "osm_id": run.name.replace("_", "/", 1),
                "archetype_id": archetype.get((cell, run.name), ""),
                "status": status.get((cell, run.name), "?"),
                "n_volstub": n_volstub,
                "has_volstub": n_volstub > 0,
                "n_converge": n_converge,
                "has_converge": n_converge > 0,
                "n_severe": n_severe,
                "has_severe": n_severe > 0,
                "n_fatal": n_fatal,
                "has_fatal": n_fatal > 0,
            })
        expected = {
            "nyc_centre": 738, "nyc_urban": 1779, "nyc_suburban": 1589, "nyc_rural": 198,
            "la_centre": 226, "la_urban": 618, "la_suburban": 1343, "la_rural": 149,
            "austin_centre": 413, "austin_urban": 425, "austin_suburban": 437, "austin_rural": 245,
        }.get(cell)
        if expected is not None and n != expected:
            short_cells[cell] = n

    per = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "open56_open09_run4_err_census_2026-08-20.csv"
    per.to_csv(out_path, index=False)

    n_total = len(per)
    print(f"C7: .err files scanned = {n_total} (expect 8160)")
    if short_cells:
        print(f"C7: SHORT cells = {short_cells}")

    n_volstub_bldg = int(per["has_volstub"].sum())
    print(f"\nC8: OPEN-56 volume-stub -- run 4: {n_volstub_bldg} / {n_total} "
          f"({100.0 * n_volstub_bldg / n_total:.4f} %); run 2 (prior): 8160 / 8160 (100.00 %)")

    n_converge_bldg = int(per["has_converge"].sum())
    by_cell = per[per["has_converge"]].groupby("cell").size().to_dict()
    print(f"\nC9: OPEN-09 non-convergence -- run 4: {n_converge_bldg} / {n_total}, by cell: {by_cell}")
    reproduced = (n_converge_bldg == 16) and all(
        by_cell.get(c, 0) == n for c, n in EXPECTED_OPEN09_CELLS.items()
    ) and all(by_cell.get(c, 0) == 0 for c in CELLS if c not in EXPECTED_OPEN09_CELLS)
    print(f"C9: reproduces expected 16 / cell-split exactly = {reproduced}")
    if not reproduced:
        print("C9 FAILED -- diff by osm_id (capped 20):")
        print(per[per["has_converge"]][["cell", "osm_id"]].head(20).to_string(index=False))

    n_severe_bldg = int(per["has_severe"].sum())
    n_fatal_bldg = int(per["has_fatal"].sum())
    n_nonsuccess = sum(1 for v in status.values() if v != "success")
    print(f"\nSevere: {n_severe_bldg} / {n_total} buildings carry >=1 ** Severe ** line")
    print(f"Fatal (two-space): {n_fatal_bldg} / {n_total} buildings carry >=1 **  Fatal  ** line")
    print(f"C10: run-4 05_results.csv non-success rows = {n_nonsuccess}")
    print(f"C10: fatal buildings ({n_fatal_bldg}) <= non-success rows ({n_nonsuccess}) = "
          f"{n_fatal_bldg <= n_nonsuccess}")

    print("\nper-cell (n_volstub, n_converge, n_severe, n_fatal, n_total):")
    print(per.groupby("cell")[["has_volstub", "has_converge", "has_severe", "has_fatal"]]
          .sum().join(per.groupby("cell").size().rename("n_total")).to_string())

    print("\nper-archetype (n_volstub, n_converge, n_severe, n_fatal, n_total), unjoined blank excluded:")
    joined = per[per["archetype_id"] != ""]
    print(joined.groupby("archetype_id")[["has_volstub", "has_converge", "has_severe", "has_fatal"]]
          .sum().join(joined.groupby("archetype_id").size().rename("n_total")).to_string())
    print(f"\nunjoined (no archetype match): {int((per['archetype_id'] == '').sum())} / {n_total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
