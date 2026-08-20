"""T02 of PLAN_gap-decomposition-2026-08-19.md.

The OPEN-59 bounds screen, structurally copied from OPEN-55 SS3
(docs/docs_ACTIVE/openings/extra/INVESTIGATION_open-55_pde-bounds-datacenter.md SS3), but
run over all four Unknown-building PDE columns instead of equipment alone.

For the 290 `OpenUBEMUnknown` buildings in the frozen `nyc_suburban` seeded GDF used by
the OPEN-55 acceptance test (run `open48_refleet3_t02a4`), regenerate the deterministic
per-building PDE draw using the exact production functions
(`openubem.semantic._build_unknown_loads` / `_per_building_rng` /
`_get_cross_archetype_loads`, openubem/semantic/__init__.py:223-321,490-493) and compare
each drawn value against that column's *screened* donor-table bounds (the same bounds the
draw itself was taken from, openubem/semantic/__init__.py:259-276).

Reads only (frozen GDF + IDF manifest already on disk; no cluster, no re-simulation).
Writes:
  - openubem/outputs/comparisons/open59_pde_bounds_screen.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

IDF_MANIFEST = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet3_t02a4"
    r"\nyc_suburban\step3\03_idf_manifest.parquet"
)
OUT_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open59_pde_bounds_screen.csv"


def main() -> None:
    from openubem.semantic import (
        _UNKNOWN_DONOR_EXCLUDE,
        _UNKNOWN_DONOR_EXCLUDE_OCCUPANCY,
        _get_cross_archetype_loads,
        _per_building_rng,
    )

    manifest = pd.read_parquet(IDF_MANIFEST)
    unk = manifest.loc[manifest["archetype_id"] == "OpenUBEMUnknown", "osm_id"]
    print(f"[T02] source manifest: {IDF_MANIFEST}")
    print(f"[T02] Unknown buildings found: {len(unk)}")

    real_loads = _get_cross_archetype_loads()
    donor_default = real_loads.loc[~real_loads.index.isin(_UNKNOWN_DONOR_EXCLUDE)]
    donor_occupancy = real_loads.loc[~real_loads.index.isin(_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY)]

    pde_cols = ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person", "wwr"]
    pool_for_col = {
        "lighting_w_m2": donor_default,
        "equipment_w_m2": donor_default,
        "occupant_m2_per_person": donor_occupancy,
        "wwr": donor_default,
    }

    bounds = {}
    for col in pde_cols:
        pool = pool_for_col[col]
        bounds[col] = (float(pool[col].min()), float(pool[col].max()))

    draws = {col: [] for col in pde_cols}
    for osm_id in unk:
        row_rng = _per_building_rng(osm_id)
        for col in pde_cols:
            lo, hi = bounds[col]
            draws[col].append(row_rng.uniform(lo, hi))

    rows = []
    for col in pde_cols:
        arr = np.array(draws[col])
        lo, hi = bounds[col]
        n_below = int((arr < lo).sum())
        n_above = int((arr > hi).sum())
        n_oob = n_below + n_above
        if n_oob:
            excursions = np.concatenate([lo - arr[arr < lo], arr[arr > hi] - hi])
            worst = float(excursions.max())
        else:
            worst = 0.0
        rows.append({
            "column": col,
            "donor_min": lo,
            "donor_max": hi,
            "drawn_min": float(arr.min()),
            "drawn_median": float(np.median(arr)),
            "drawn_max": float(arr.max()),
            "n": len(arr),
            "n_out_of_bounds": n_oob,
            "n_below": n_below,
            "n_above": n_above,
            "worst_excursion": worst,
        })
        print(f"[T02] {col}: donor=[{lo:.4f}, {hi:.4f}]  drawn=[{arr.min():.4f}, "
              f"median={np.median(arr):.4f}, {arr.max():.4f}]  out_of_bounds={n_oob}/{len(arr)}")

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    n_cols_with_oob = int((df["n_out_of_bounds"] > 0).sum())
    print(f"[T02] columns with any out-of-bounds draw: {n_cols_with_oob}/{len(pde_cols)}")
    if n_cols_with_oob:
        print(f"[T02] offending columns: {df.loc[df['n_out_of_bounds'] > 0, 'column'].tolist()}")
    print(f"[T02] wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
