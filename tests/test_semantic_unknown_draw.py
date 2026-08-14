"""OPEN-49 — pins the coupled-draw defect in Step 2.2 Unknown-row PDE generation.

Two independent routes couple every OpenUBEMUnknown building's drawn loads to
cell membership that has nothing to do with that building:

  route 1 (Fact 1, openubem/semantic/__init__.py:228-232) — one vectorised
  `rng.uniform(lo, hi, size=n)` block is sized by the Unknown count `n`.
  Reclassifying an unrelated building changes `n` and reshuffles the whole
  block, moving every other Unknown building's draw.

  route 2 (Fact 2, same lines, `real_loads` at :340) — `lo, hi` are the
  min/max of the archetypes PRESENT in the cell. Changing which archetype an
  unrelated identified building carries changes the bounds every Unknown
  building draws from, even when `n` does not change.

On today's (pre-T02) code both tests below FAIL: the four PDE columns of the
four originally-Unknown rows move when an unrelated building is reclassified.
"""
from __future__ import annotations

import numpy as np

from openubem.semantic import enrich_semantics
from tests.test_step22_orchestrator import _make_29col_gdf

_PDE_COLS = ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person", "wwr"]

_UNKNOWN_ROWS = [2, 3, 4, 5]
_BASE_ARCHETYPES = [
    "SmallOffice", "MediumOffice",
    "OpenUBEMUnknown", "OpenUBEMUnknown", "OpenUBEMUnknown", "OpenUBEMUnknown",
]


def _baseline_gdf():
    return _make_29col_gdf(_BASE_ARCHETYPES)


def _run(gdf, seed=42):
    result, _ = enrich_semantics(gdf, random_seed=seed)
    return result


def _diff_report(base, other, cols):
    lines = []
    for col in cols:
        d = base[col].to_numpy(dtype=float) - other[col].to_numpy(dtype=float)
        lines.append(f"  {col}: max|delta|={np.max(np.abs(d)):.6g}  per-row deltas={d.tolist()}")
    return "\n".join(lines)


def test_route1_block_size_couples_unknown_draws():
    """Fact 1. Flip one IDENTIFIED building (row 1, MediumOffice) to Unknown.
    n_unknown: 4 -> 5. The four originally-Unknown rows (2,3,4,5) must not move.
    """
    base = _run(_baseline_gdf())
    base_pde = base.loc[_UNKNOWN_ROWS, _PDE_COLS]

    modified_archetypes = list(_BASE_ARCHETYPES)
    modified_archetypes[1] = "OpenUBEMUnknown"
    mod = _run(_make_29col_gdf(modified_archetypes))
    mod_pde = mod.loc[_UNKNOWN_ROWS, _PDE_COLS]

    report = _diff_report(base_pde, mod_pde, _PDE_COLS)
    assert np.allclose(
        base_pde.to_numpy(dtype=float), mod_pde.to_numpy(dtype=float), atol=1e-9
    ), (
        "route 1 (block size): the four originally-Unknown rows' PDE columns "
        "moved when an unrelated building was reclassified to Unknown "
        f"(n changed 4 -> 5). Per-column drift:\n{report}"
    )


def test_route2_present_archetype_bounds_couple_unknown_draws():
    """Fact 2. Flip one IDENTIFIED building's archetype (row 0, SmallOffice ->
    LargeDataCenterHighITE), n_unknown unchanged at 4. The four Unknown rows
    must not move.
    """
    base = _run(_baseline_gdf())
    base_pde = base.loc[_UNKNOWN_ROWS, _PDE_COLS]

    modified_archetypes = list(_BASE_ARCHETYPES)
    modified_archetypes[0] = "LargeDataCenterHighITE"
    mod = _run(_make_29col_gdf(modified_archetypes))
    mod_pde = mod.loc[_UNKNOWN_ROWS, _PDE_COLS]

    report = _diff_report(base_pde, mod_pde, _PDE_COLS)
    assert np.allclose(
        base_pde.to_numpy(dtype=float), mod_pde.to_numpy(dtype=float), atol=1e-9
    ), (
        "route 2 (present-archetype bounds): the four Unknown rows' PDE "
        "columns moved when an unrelated identified building's archetype "
        "changed (present-archetype set changed, Unknown count unchanged). "
        f"Per-column drift:\n{report}"
    )
