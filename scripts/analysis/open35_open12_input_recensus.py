"""W08/W09 of PLAN_ten-tasks-2026-08-18-night.md -- re-derive two input-coverage figures
that this register has been quoting since 2026-08-05/06, on a fleet that still exists.

Both figures were measured on the pre-Phase-E fleet. Run 2 (open48_refleet) carries its own
Stage-1 `01_buildings.gpkg` for all twelve cells, frozen and re-runnable, so the same
questions can be asked of a corpus that is still on disk.

W08 -- OPEN-35: buildings with NEITHER `levels` NOR `height_m`, and how many are persisted at
       levels = 1.0. Register figure: 2,611 / 8,160 = 32.00 %.
W09 -- OPEN-12 / OPEN-14: the `height_m` null fraction per cell. Register figure:
       2,806 / 8,160 = 34.39 % fleet-wide, and 100.00 % for nyc_rural / austin_rural /
       nyc_suburban in the tracked Stage-1 files.

If a figure reproduces, that is a result and is reported as one. Nothing is adjudicated here:
where the new number differs from the old, both are recorded side by side, per the register's
own rule.

Emits openubem/outputs/comparisons/open35_open12_input_recensus.csv.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
RESULTS = Path(__file__).resolve().parents[2] / "docs/validations/overAll/results/open48_refleet"
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

REGISTER = {                      # figures this pass is re-deriving, quoted for comparison
    "open35_neither_levels_nor_height": (2611, 8160, "32.00 %", "2026-08-06, N06/T04(d)"),
    "open12_height_null": (2806, 8160, "34.39 %", "2026-08-06, N06"),
}


def main() -> int:
    rows = []
    for cell in CELLS:
        gp = BASE / cell / "01_buildings.gpkg"
        if not gp.exists():
            print(f"MISSING {gp}")
            continue
        g = gpd.read_file(gp)
        n = len(g)
        has_levels = g["levels"].notna() if "levels" in g.columns else pd.Series([False] * n)
        has_height = g["height_m"].notna() if "height_m" in g.columns else pd.Series([False] * n)
        neither = (~has_levels) & (~has_height)

        rec = {
            "cell": cell,
            "n_buildings": n,
            "levels_null": int((~has_levels).sum()),
            "height_null": int((~has_height).sum()),
            "neither": int(neither.sum()),
            "height_null_pct": round(100.0 * (~has_height).mean(), 4),
            "neither_pct": round(100.0 * neither.mean(), 4),
            "height_present_but_zero": int((g["height_m"] == 0).sum())
            if "height_m" in g.columns else 0,
        }

        res = RESULTS / cell / "05_results.csv"
        if res.exists():
            r = pd.read_csv(res)
            if "levels" in r.columns:
                ids = set(g.loc[neither, "osm_id"]) if "osm_id" in g.columns else set()
                sub = r[r["osm_id"].isin(ids)]
                rec["neither_persisted_at_levels_1"] = int((sub["levels"] == 1.0).sum())
                rec["neither_in_results"] = len(sub)
        rows.append(rec)

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open35_open12_input_recensus.csv"
    df.to_csv(dest, index=False)

    with pd.option_context("display.width", 240, "display.max_columns", 40):
        print(df.to_string(index=False))

    tot = int(df["n_buildings"].sum())
    print(f"\nfleet total: {tot} buildings across {len(df)} cells")

    for key, col in (("open35_neither_levels_nor_height", "neither"),
                     ("open12_height_null", "height_null")):
        num, den, pct, prov = REGISTER[key]
        got = int(df[col].sum())
        print(f"\n--- {key} ---")
        print(f"  register ({prov}): {num} / {den} = {pct}")
        print(f"  re-derived on run 2 : {got} / {tot} = {100.0*got/tot:.2f} %")
        print(f"  {'REPRODUCES' if got == num else 'DIFFERS -- both figures stand, neither adjudicated'}")

    if "neither_persisted_at_levels_1" in df.columns:
        a, b = int(df["neither_persisted_at_levels_1"].sum()), int(df["neither_in_results"].sum())
        print(f"\n--- OPEN-35's mechanism: of the {b} 'neither' buildings that reach the results "
              f"file, {a} are persisted at levels = 1.0 ({100.0*a/b:.2f} %) ---" if b else "")

    print("\n--- OPEN-12's named cells ---")
    print(df[df["cell"].isin(["nyc_rural", "austin_rural", "nyc_suburban"])]
          [["cell", "n_buildings", "height_null", "height_null_pct"]].to_string(index=False))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
