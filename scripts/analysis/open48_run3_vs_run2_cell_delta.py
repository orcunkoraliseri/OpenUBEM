"""T05 of PLAN_open-48-third-fleet-run-2026-08-18.md.

Run 3 vs run 2, per cell, on the frozen OSM input (code is the only variable).

Run 3 cannot be aggregated as a fleet: five of twelve cells stopped, and four of the
five that passed did so by dropping the buildings OPEN-55 affected. What survives is a
per-cell comparison, and it is only clean where the cell has no Unknown buildings for
OPEN-55 to touch.

Three guards, each of which changed the answer when it was added:
  1. Only `simulation_status == "success"` rows count. Failed rows carry NaN EUI but a
     real floor area, so including them silently deflates the weighted mean.
  2. Only buildings that succeeded in BOTH runs count, so a delta never reflects a
     difference in which buildings were dropped.
  3. `delta_known` repeats the comparison with every Unknown building removed from both
     runs, so the OPEN-55 contamination is excluded by construction rather than assumed
     to be small.

Emits openubem/outputs/comparisons/open48_run3_vs_run2_cell_delta.csv.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

BASE = Path(tempfile.gettempdir()) / "ubem_validation"
RUN2 = "open48_refleet"
RUN3 = "open48_refleet3"
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"

CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]


def _load(run: str, cell: str) -> pd.DataFrame | None:
    p = BASE / run / cell / "results" / "05_results.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["floor_area_m2"] = df["footprint_area_m2"] * df["levels"].clip(lower=1)
    return df


def _weighted_eui(df: pd.DataFrame) -> float:
    """Floor-area-weighted EUI over successful rows only (open43 arithmetic)."""
    succ = df[(df["simulation_status"] == "success") & df["total_eui_kwh_m2"].notna()]
    fa = succ["floor_area_m2"].sum()
    if not fa:
        return float("nan")
    return float((succ["total_eui_kwh_m2"] * succ["floor_area_m2"]).sum() / fa)


def main() -> int:
    rows = []
    for cell in CELLS:
        d2, d3 = _load(RUN2, cell), _load(RUN3, cell)
        rec: dict[str, object] = {"cell": cell}
        if d3 is None:
            rec["status"] = "no run-3 results (cell stopped or died)"
            rows.append(rec)
            continue
        if d2 is None:
            rec["status"] = "no run-2 results"
            rows.append(rec)
            continue

        ok2 = set(d2.loc[d2["simulation_status"] == "success", "osm_id"])
        ok3 = set(d3.loc[d3["simulation_status"] == "success", "osm_id"])
        common = ok2 & ok3
        unk = set(d3.loc[d3["archetype_id"] == "OpenUBEMUnknown", "osm_id"])

        c2 = d2[d2["osm_id"].isin(common)].sort_values("osm_id").reset_index(drop=True)
        c3 = d3[d3["osm_id"].isin(common)].sort_values("osm_id").reset_index(drop=True)
        k2 = c2[~c2["osm_id"].isin(unk)]
        k3 = c3[~c3["osm_id"].isin(unk)]

        e2c, e3c = _weighted_eui(c2), _weighted_eui(c3)
        e2k, e3k = _weighted_eui(k2), _weighted_eui(k3)
        rec.update({
            "status": "compared",
            "n_run2_success": len(ok2),
            "n_run3_success": len(ok3),
            "n_common": len(common),
            "n_unknown_run3": len(unk),
            "n_unknown_in_common": len(unk & common),
            "eui_run2_common": round(e2c, 4),
            "eui_run3_common": round(e3c, 4),
            "delta_common": round(e3c - e2c, 4),
            "eui_run2_known": round(e2k, 4),
            "eui_run3_known": round(e3k, 4),
            "delta_known": round(e3k - e2k, 4),
            "n_changed_buildings": int(
                (~c2["total_eui_kwh_m2"].round(6).eq(c3["total_eui_kwh_m2"].round(6))).sum()
            ),
        })
        rows.append(rec)

    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open48_run3_vs_run2_cell_delta.csv"
    out.to_csv(dest, index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(out.to_string(index=False))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
