"""T03/T04 of PLAN_ten-items-2026-08-18-late.md.

Tests one prediction, recorded in that plan's section 1 before the measurement was made:
OPEN-11's six "inverted-geometry" buildings and OPEN-42 face (ii)'s six placeholder-
200.0 m2 Warehouses are the same six osm_ids, i.e. two items tracked separately since
2026-08-06 and 2026-08-11 describe one population.

Also re-derives OPEN-42's two faces from the live artifacts and asks which of the two
candidate predictors of failure -- the no_floors flag or the placeholder footprint --
actually separates the failing Warehouses, since 37 of 38 carry the flag and only 6
carry the placeholder, so they cannot both be the cause.

Emits openubem/outputs/comparisons/open11_open42_six_buildings.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "docs" / "validations" / "overAll" / "results"
OUT = ROOT / "openubem" / "outputs" / "comparisons"

CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

OPEN11_SIX = {
    "way/472960972", "way/472961034", "way/472961088",
    "way/472961091", "way/472961171", "way/402215469",
}
PLACEHOLDER_M2 = 200.0


def _load(run: str) -> pd.DataFrame:
    frames = []
    for cell in CELLS:
        p = RESULTS / run / cell / "05_results.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        df["cell"] = cell
        frames.append(df)
    if not frames:
        raise SystemExit(f"no result files under {RESULTS / run}")
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    run = "open48_refleet"
    df = _load(run)
    print(f"run={run}  rows={len(df)}  cells={df['cell'].nunique()}")

    placeholder = set(df.loc[df["footprint_area_m2"].round(6) == PLACEHOLDER_M2, "osm_id"])
    print(f"\n--- T03: the six-building identity ---")
    print(f"OPEN-11 six           : {len(OPEN11_SIX)}")
    print(f"footprint == 200.0 m2 : {len(placeholder)}")
    print(f"intersection          : {len(OPEN11_SIX & placeholder)}")
    print(f"only in OPEN-11       : {sorted(OPEN11_SIX - placeholder)}")
    print(f"only in placeholder   : {sorted(placeholder - OPEN11_SIX)}")
    print(f"IDENTITY HOLDS        : {OPEN11_SIX == placeholder}")

    six = df[df["osm_id"].isin(OPEN11_SIX)]
    cols = [c for c in ["cell", "osm_id", "archetype_id", "data_quality_flag",
                        "footprint_area_m2", "levels", "levels_source", "height_m",
                        "simulation_status", "total_eui_kwh_m2"] if c in df.columns]
    print("\n--- the six, as the live run records them ---")
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(six[cols].sort_values(["cell", "osm_id"]).to_string(index=False))

    print("\n--- T04: OPEN-42 faces re-derived ---")
    wh = df[df["archetype_id"] == "Warehouse"]
    fail = df["simulation_status"] != "success"
    print(f"Warehouses: {len(wh)}  failures among them: {int((wh['simulation_status'] != 'success').sum())}")
    print(f"fleet failures: {int(fail.sum())} of {len(df)}")

    flag_col = "data_quality_flag" if "data_quality_flag" in df.columns else None
    if flag_col:
        nf = df[flag_col].astype(str).str.contains("no_floors", na=False)
        print("\ncrosstab: no_floors x failed (whole fleet)")
        print(pd.crosstab(nf, fail).to_string())
        print("\ncrosstab: no_floors x failed (Warehouses only)")
        whm = df["archetype_id"] == "Warehouse"
        print(pd.crosstab(nf[whm], fail[whm]).to_string())

    ph = df["osm_id"].isin(placeholder)
    print("\ncrosstab: placeholder-200 x failed (whole fleet)")
    print(pd.crosstab(ph, fail).to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open11_open42_six_buildings.csv"
    six[cols].sort_values(["cell", "osm_id"]).to_csv(dest, index=False)
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
