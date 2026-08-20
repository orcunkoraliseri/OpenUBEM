"""T13 of PLAN_twenty-items-2026-08-19.md -- re-derive OPEN-09's non-convergence
population and rate on run-4 (open48_refleet4) artifacts.

Run 4 is the first fleet run since the OPEN-55 Unknown-donor screen and the
OPEN-35 storey-imputation change, both of which touch buildings that could
overlap OPEN-09's population. This script does not re-run anything -- it
scans the .err files already on disk under
%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4/<cell>/sim_out/<stem>/eplusout.err.

Anchors (must reproduce or the join is wrong, not the register):
  - the 10 X03 control buildings (la_centre way_427817687/way_428015178,
    la_suburban way_442633387/way_442634081/way_442634778,
    la_rural way_472961043/way_472961089/way_472961090/way_472961093/way_472961164)
    carried 150 baseline / 150 treated warnings (15/15 each) on run 2.
  - the 6 OPEN-56/OPEN-42 face-(ii) Warehouse fatal buildings
    (la_rural way_472960972/way_472961034/way_472961088/way_472961091/way_472961171,
    la_urban way_402215469).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RUN4 = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

_CONVERGE = re.compile(r"Inside surface heat balance did not converge")

X03_TEN = {
    ("la_centre", "way_427817687"), ("la_centre", "way_428015178"),
    ("la_suburban", "way_442633387"), ("la_suburban", "way_442634081"),
    ("la_suburban", "way_442634778"),
    ("la_rural", "way_472961043"), ("la_rural", "way_472961089"),
    ("la_rural", "way_472961090"), ("la_rural", "way_472961093"),
    ("la_rural", "way_472961164"),
}
SIX_WAREHOUSE = {
    ("la_rural", "way_472960972"), ("la_rural", "way_472961034"),
    ("la_rural", "way_472961088"), ("la_rural", "way_472961091"),
    ("la_rural", "way_472961171"), ("la_urban", "way_402215469"),
}


def main() -> int:
    rows = []
    status = {}
    for cell in CELLS:
        rp = RUN4 / cell / "results" / "05_results.csv"
        if rp.exists():
            df = pd.read_csv(rp)
            for oid, st in zip(df["osm_id"], df["simulation_status"]):
                status[(cell, oid.replace("/", "_"))] = st

    scanned = 0
    for cell in CELLS:
        d = RUN4 / cell / "sim_out"
        if not d.exists():
            print(f"MISSING {d}")
            continue
        for run in sorted(d.iterdir()):
            err = run / "eplusout.err"
            if not err.exists():
                continue
            scanned += 1
            txt = err.read_text(encoding="utf-8", errors="replace")
            n = len(_CONVERGE.findall(txt))
            rows.append({
                "cell": cell, "stem": run.name,
                "status": status.get((cell, run.name), "?"),
                "n_converge_warnings": n,
                "completed": "EnergyPlus Completed Successfully" in txt,
                "n_severe_lines": txt.count("** Severe"),
                "n_fatal_lines": txt.count("Fatal"),
            })

    per = pd.DataFrame(rows)
    per["has_converge"] = per["n_converge_warnings"] > 0
    OUT.mkdir(parents=True, exist_ok=True)
    per.to_csv(OUT / "open09_run4_perbuilding.csv", index=False)

    print(f"scanned {scanned} run-4 eplusout.err files (expect 8160)")
    print(f"buildings with >=1 non-convergence warning: {int(per['has_converge'].sum())} / "
          f"{len(per)} ({100.0*per['has_converge'].mean():.4f} %)")
    print("\nper cell (n_with, n_total, rate):")
    print(per.groupby("cell")["has_converge"].agg(["sum", "count", "mean"]).to_string())

    print("\n=== X03 anchor: the 10 control buildings, run-4 warning counts ===")
    per["key"] = list(zip(per["cell"], per["stem"]))
    ten = per[per["key"].isin(X03_TEN)]
    print(ten[["cell", "stem", "n_converge_warnings", "status", "completed"]].to_string(index=False))
    print(f"found {len(ten)} / 10 of the X03 population in run 4")
    print(f"sum n_converge_warnings over the 10: {ten['n_converge_warnings'].sum()} (run-2 anchor: 150)")

    print("\n=== the 6 OPEN-56/OPEN-42 face-(ii) Warehouse fatal buildings, run-4 status ===")
    six = per[per["key"].isin(SIX_WAREHOUSE)]
    print(six[["cell", "stem", "status", "completed", "n_severe_lines", "n_fatal_lines",
               "n_converge_warnings"]].to_string(index=False))
    found_six = set(six["key"])
    missing_six = SIX_WAREHOUSE - found_six
    print(f"found {len(six)} / 6; missing from run-4 sim_out entirely: {sorted(missing_six)}")

    print("\n=== 16-building overlap check ===")
    sixteen = X03_TEN | SIX_WAREHOUSE
    present16 = per[per["key"].isin(sixteen)]
    print(f"of the 16-building union, {len(present16)} appear in run-4 sim_out; "
          f"{len(sixteen) - len(present16)} missing.")
    still_nonconverge = present16[present16["has_converge"]]
    print(f"of those present, {len(still_nonconverge)} still carry >=1 non-convergence warning in run-4.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
