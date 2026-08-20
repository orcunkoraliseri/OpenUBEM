"""T04 of PLAN_ten-items-2026-08-18-late.md, second half -- the mechanism, and its control.

The six OPEN-42 buildings' EnergyPlus runs report

    ** Warning ** Indicated Zone Volume <= 0.0 for Zone=...
    **   ~~~   ** The calculated Zone Volume was=-1376.24
    **   ~~~   ** The simulation will continue with the Zone Volume set to 10.0 m3.

A NEGATIVE computed volume, replaced by a 10 m3 stub. A zone with thousands of square
metres of surface and the air mass of a broom cupboard has almost no thermal capacitance,
so any heat-balance residual swings its air temperature by hundreds of degrees in one
timestep -- which is exactly the observed failure.

A prior pass established that the 10 m3 fallback ALSO occurs on buildings that succeed, so
the fallback alone is not sufficient. This census tests the sharper claim: it is the
fallback *scaled by how large the zone actually is* that separates failures from successes.
Every la_rural and la_urban run of run 2 is scanned -- 767 buildings, the six included.

Emits openubem/outputs/comparisons/open42_zone_volume_census.csv.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
RESULTS = Path(__file__).resolve().parents[2] / "docs/validations/overAll/results/open48_refleet"
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"
CELLS = ["la_rural", "la_urban"]

_VOL_RX = re.compile(r"The calculated Zone Volume was=\s*(-?[\d.eE+]+)")
_STUB_RX = re.compile(r"Zone Volume set to 10\.0 m3")
_FATAL_RX = re.compile(r"Temperature \((?:low|high)\) out of bounds")


def main() -> int:
    res = pd.concat(
        [pd.read_csv(RESULTS / c / "05_results.csv").assign(cell=c) for c in CELLS],
        ignore_index=True,
    )
    res["stem"] = res["osm_id"].str.replace("/", "_", regex=False)
    status = dict(zip(res["stem"], res["simulation_status"]))

    rows = []
    for cell in CELLS:
        for d in sorted((BASE / cell / "sim_out").iterdir()):
            err = d / "eplusout.err"
            if not err.exists():
                continue
            txt = err.read_text(encoding="utf-8", errors="replace")
            vols = [float(v) for v in _VOL_RX.findall(txt)]
            rows.append({
                "cell": cell,
                "stem": d.name,
                "status": status.get(d.name, "?"),
                "n_zone_volume_stubs": len(_STUB_RX.findall(txt)),
                "n_negative_volume": sum(1 for v in vols if v < 0),
                "min_calculated_volume": min(vols) if vols else None,
                "temp_out_of_bounds": bool(_FATAL_RX.search(txt)),
            })

    df = pd.DataFrame(rows)
    df["failed"] = df["status"] != "success"
    df["has_stub"] = df["n_zone_volume_stubs"] > 0
    df["has_negative"] = df["n_negative_volume"] > 0

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open42_zone_volume_census.csv"
    df.to_csv(dest, index=False)

    print(f"scanned {len(df)} buildings across {CELLS}\n")
    print("--- the 10 m3 stub alone (prior pass said this does not separate) ---")
    print(pd.crosstab(df["has_stub"], df["failed"]).to_string())
    print("\n--- a NEGATIVE calculated volume ---")
    print(pd.crosstab(df["has_negative"], df["failed"]).to_string())
    print("\n--- magnitude of the negative volume, failures vs successes ---")
    neg = df[df["has_negative"]]
    if not neg.empty:
        print(neg.groupby("failed")["min_calculated_volume"].describe().to_string())
    print("\n--- the failures ---")
    print(df[df["failed"]][
        ["cell", "stem", "status", "n_zone_volume_stubs", "n_negative_volume",
         "min_calculated_volume", "temp_out_of_bounds"]].to_string(index=False))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
