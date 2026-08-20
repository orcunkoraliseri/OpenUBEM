"""W06/W07 of PLAN_ten-tasks-2026-08-18-night.md -- the fleet error taxonomy nobody has taken.

Every previous fleet-wide error census in this project ran against the E02 harvest, which an
external sweep emptied on 2026-08-17. Run 2 (open48_refleet) left 8,160 eplusout.err files on
local disk, and its inputs are frozen -- so anything found here is re-derivable and, unlike
E02, re-runnable.

W06: census every "** Warning **" / "** Severe **" family across all 8,160 files.
W07: OPEN-09 specifically -- the heat-balance / warmup non-convergence rate fleet-wide. That
     item's "cosmetic" verdict rests on a 2026-08-06 test on a small population and has never
     been checked against a whole fleet.

No causal claim is made from a rate. Where a correlation is reported it is reported with the
population it was computed on.

Emits openubem/outputs/comparisons/open09_fleet_err_taxonomy.csv (families)
  and openubem/outputs/comparisons/open09_fleet_err_perbuilding.csv (one row per building).
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
RESULTS = Path(__file__).resolve().parents[2] / "docs/validations/overAll/results/open48_refleet"
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

# Family key: the message stem, with numbers and quoted names collapsed so that
# "Temperature (high) out of bounds (200.66] for zone=..." and its 4,000 siblings
# land in one bucket.
_MSG = re.compile(r"\*\*\s*(Warning|Severe)\s*\*\*\s*(.{0,90})")
_NUM = re.compile(r"[-+]?\d[\d.,eE+-]*")
_QUOTED = re.compile(r'"[^"]*"')

_CONVERGE = re.compile(r"Inside surface heat balance did not converge")
_WARMUP = re.compile(r"Warmup convergence|did not converge after|Warmup: 0 Warning")
_VOLSTUB = re.compile(r"Zone Volume set to 10\.0 m3")
_OOB = re.compile(r"Temperature \((?:low|high)\) out of bounds")


def _family(msg: str) -> str:
    m = _QUOTED.sub('"X"', msg)
    m = _NUM.sub("N", m)
    return " ".join(m.split())[:80]


def main() -> int:
    status = {}
    for cell in CELLS:
        p = RESULTS / cell / "05_results.csv"
        if p.exists():
            df = pd.read_csv(p)
            for oid, st in zip(df["osm_id"], df["simulation_status"]):
                status[(cell, oid.replace("/", "_"))] = st

    families: Counter = Counter()
    fam_buildings: dict[str, set] = {}
    rows = []
    scanned = 0

    for cell in CELLS:
        d = BASE / cell / "sim_out"
        if not d.exists():
            print(f"MISSING {d}")
            continue
        for run in sorted(d.iterdir()):
            err = run / "eplusout.err"
            if not err.exists():
                continue
            scanned += 1
            txt = err.read_text(encoding="utf-8", errors="replace")
            local = set()
            for sev, msg in _MSG.findall(txt):
                key = f"{sev}|{_family(msg)}"
                families[key] += 1
                local.add(key)
            for k in local:
                fam_buildings.setdefault(k, set()).add((cell, run.name))
            rows.append({
                "cell": cell, "stem": run.name,
                "status": status.get((cell, run.name), "?"),
                "n_converge_warnings": len(_CONVERGE.findall(txt)),
                "n_vol_stub": len(_VOLSTUB.findall(txt)),
                "n_temp_out_of_bounds": len(_OOB.findall(txt)),
                "completed": "EnergyPlus Completed Successfully" in txt,
                "n_severe_lines": txt.count("** Severe"),
                "bytes": err.stat().st_size,
            })

    per = pd.DataFrame(rows)
    fam = pd.DataFrame(
        [{"severity": k.split("|", 1)[0], "family": k.split("|", 1)[1],
          "occurrences": v, "buildings": len(fam_buildings.get(k, ()))}
         for k, v in families.items()]
    ).sort_values("buildings", ascending=False)

    OUT.mkdir(parents=True, exist_ok=True)
    fam.to_csv(OUT / "open09_fleet_err_taxonomy.csv", index=False)
    per.to_csv(OUT / "open09_fleet_err_perbuilding.csv", index=False)

    print(f"scanned {scanned} eplusout.err files across {per['cell'].nunique()} cells")
    print(f"distinct message families: {len(fam)}")

    print("\n=== W06: families present in the most buildings (top 20) ===")
    with pd.option_context("display.width", 220, "display.max_colwidth", 82):
        print(fam.head(20).to_string(index=False))

    print("\n=== W06: families that are UNIVERSAL (every building) ===")
    uni = fam[fam["buildings"] == scanned]
    print(uni.to_string(index=False) if not uni.empty else "  none")

    print("\n=== W07: OPEN-09 -- heat-balance non-convergence, fleet-wide ===")
    per["has_converge"] = per["n_converge_warnings"] > 0
    print(f"buildings with >=1 non-convergence warning: "
          f"{int(per['has_converge'].sum())} / {len(per)} "
          f"({100.0*per['has_converge'].mean():.2f} %)")
    print("\nper cell:")
    print(per.groupby("cell")["has_converge"].agg(["sum", "count", "mean"]).to_string())
    print("\nwarning count distribution over buildings that have any:")
    print(per.loc[per["has_converge"], "n_converge_warnings"].describe().to_string())

    print("\n--- does non-convergence coincide with failure? "
          "(reported as a contingency, not a cause) ---")
    per["failed"] = per["status"] != "success"
    print(pd.crosstab(per["has_converge"], per["failed"]).to_string())

    print(f"\nwrote {OUT / 'open09_fleet_err_taxonomy.csv'}")
    print(f"wrote {OUT / 'open09_fleet_err_perbuilding.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
