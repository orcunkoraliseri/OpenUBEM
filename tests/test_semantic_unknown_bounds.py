"""OPEN-55 — pins ruling B+, the Unknown PDE donor screen (2026-08-19).

Before T01, an OpenUBEMUnknown building's `equipment_w_m2` was drawn uniformly
over the full 29-archetype table, `[2.58, 5381.96]` — with a uniform draw the
maximum sets the centre, so half of all Unknown buildings carried a load
above ~2,690 W/m². That is what stopped five cells of run 3, and below the
crash threshold it silently biased the fleet figure rather than failing.

Ruling B+ (`extra/PROPOSAL_open-55_unknown-pde-bounds.md` §7/§7A) excludes,
from the Unknown PDE donor pool, on every PDE column: the four data centres,
`Laboratory`, and both restaurants. `Warehouse` is excluded additionally, on
the occupancy column only (its 464.52 m²/person is otherwise the new ceiling
once the data centres are gone).

This file pins:
  1. the exclusion sets themselves, against the ruling;
  2. that the screen is wired into `_build_unknown_loads`'s bounds/median
     construction (white-box, via a recording fake RNG) — not merely that an
     equivalent filter, computed independently in this test, would agree;
  3. that OPEN-49's per-building reproducibility and cell-independence
     properties survive T01 unchanged;
  4. the empty-pool guard;
  5. a non-vacuity probe — widen the exclusion set to empty and confirm the
     ceiling reverts to the unscreened 5381.96, proving the assertions above
     are load-bearing rather than trivially true.
"""
from __future__ import annotations

import decimal

import numpy as np
import pytest

import openubem.semantic as sem
from openubem.semantic import (
    _UNKNOWN_DONOR_EXCLUDE,
    _UNKNOWN_DONOR_EXCLUDE_OCCUPANCY,
    _get_cross_archetype_loads,
    enrich_semantics,
)
from tests.test_step22_orchestrator import _make_29col_gdf

_PDE_COLS = ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person", "wwr"]
_SCALAR_COLS = [
    "heating_setpoint_c", "cooling_setpoint_c", "heating_setback_c", "cooling_setup_c",
]
_ALL_COLS = _PDE_COLS + _SCALAR_COLS


class _RecordingRNG:
    """Stands in for `_per_building_rng`'s return value. Records every
    `(lo, hi)` pair `_build_unknown_loads` calls `.uniform` with, keyed by
    call order (== `pde_cols` order), instead of actually drawing — so the
    production `bounds` dict is observed directly, not re-derived."""

    def __init__(self):
        self.calls: list[tuple[float, float]] = []

    def uniform(self, lo, hi):
        self.calls.append((float(lo), float(hi)))
        return lo


def _capture_bounds(monkeypatch, exclude=None, exclude_occ=None) -> dict[str, tuple[float, float]]:
    """Run `_build_unknown_loads` on a single Unknown row with a recording
    fake RNG and return the bounds it actually used, per PDE column."""
    if exclude is not None:
        monkeypatch.setattr(sem, "_UNKNOWN_DONOR_EXCLUDE", exclude)
    if exclude_occ is not None:
        monkeypatch.setattr(sem, "_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY", exclude_occ)

    gdf = _make_29col_gdf(["OpenUBEMUnknown"])
    unk_mask = gdf["archetype_id"] == "OpenUBEMUnknown"
    recorder = _RecordingRNG()
    monkeypatch.setattr(sem, "_per_building_rng", lambda osm_id: recorder)

    real_loads = _get_cross_archetype_loads()
    sem._build_unknown_loads(gdf, unk_mask, real_loads, rng=None)

    assert len(recorder.calls) == len(_PDE_COLS)
    return dict(zip(_PDE_COLS, recorder.calls))


def _round_half_up(lo: float, hi: float) -> str:
    """Decimal, round-half-up midpoint at 2dp — matches how §7A's table was
    computed. Plain float arithmetic on (2.58 + 16.15) / 2 lands one ULP
    below .365 (9.364999999999998) and rounds down under Python's
    round-half-to-even `round()`; going through the archetypes' own decimal
    string representation avoids that artifact."""
    mid = (decimal.Decimal(str(lo)) + decimal.Decimal(str(hi))) / 2
    return str(mid.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP))


# ── 1. exclusion sets match the ruling ──────────────────────────────────────


def test_exclusion_sets_match_ruling_b_plus():
    assert _UNKNOWN_DONOR_EXCLUDE == {
        "SmallDataCenterLowITE", "SmallDataCenterHighITE",
        "LargeDataCenterLowITE", "LargeDataCenterHighITE",
        "Laboratory", "FullServiceRestaurant", "QuickServiceRestaurant",
    }
    assert _UNKNOWN_DONOR_EXCLUDE_OCCUPANCY == _UNKNOWN_DONOR_EXCLUDE | {"Warehouse"}


# ── 2. bounds/median wired into _build_unknown_loads ────────────────────────


def test_screened_equipment_bounds(monkeypatch):
    bounds = _capture_bounds(monkeypatch)
    lo, hi = bounds["equipment_w_m2"]
    assert (round(lo, 2), round(hi, 2)) == (2.58, 16.15)


def test_screened_equipment_uniform_median(monkeypatch):
    bounds = _capture_bounds(monkeypatch)
    lo, hi = bounds["equipment_w_m2"]
    assert _round_half_up(lo, hi) == "9.37"


def test_screened_occupancy_bounds_exclude_warehouse(monkeypatch):
    bounds = _capture_bounds(monkeypatch)
    occ_lo, occ_hi = bounds["occupant_m2_per_person"]
    assert (round(occ_lo, 2), round(occ_hi, 2)) == (4.65, 51.10)


def test_unscreened_default_pool_still_carries_warehouse_on_other_columns(monkeypatch):
    # The occupancy-only extra exclusion (Warehouse) must not leak onto the
    # other three PDE columns, which use `_UNKNOWN_DONOR_EXCLUDE` alone.
    real_loads = _get_cross_archetype_loads()
    default_pool = real_loads.loc[~real_loads.index.isin(_UNKNOWN_DONOR_EXCLUDE)]
    assert "Warehouse" in default_pool.index
    occ_pool = real_loads.loc[~real_loads.index.isin(_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY)]
    assert "Warehouse" not in occ_pool.index
    # If occupancy used the default (non-occupancy) exclude set, Warehouse's
    # 464.52 m²/person would be the ceiling instead of 51.10.
    assert round(float(default_pool["occupant_m2_per_person"].max()), 2) == 464.52


# ── 3. OPEN-49 properties survive T01 ────────────────────────────────────────


def test_reproducibility_bit_identical():
    gdf = _make_29col_gdf(["OpenUBEMUnknown", "OpenUBEMUnknown"])
    r1, _ = enrich_semantics(gdf, random_seed=42)
    r2, _ = enrich_semantics(gdf, random_seed=42)
    assert np.array_equal(
        r1[_ALL_COLS].to_numpy(dtype=float), r2[_ALL_COLS].to_numpy(dtype=float)
    )


def test_different_osm_id_gives_different_draw():
    gdf = _make_29col_gdf(["OpenUBEMUnknown", "OpenUBEMUnknown"])
    result, _ = enrich_semantics(gdf, random_seed=42)
    row0 = result.loc[0, _PDE_COLS].to_numpy(dtype=float)
    row1 = result.loc[1, _PDE_COLS].to_numpy(dtype=float)
    assert not np.allclose(row0, row1)


def test_cell_independence_preserved_under_screen():
    """Same osm_id (rows 2, 3) must draw identically whether the frame also
    contains ordinary offices, or now-excluded archetypes (data centre,
    Laboratory). This is OPEN-49's route-2 property; T01 must not
    reintroduce a dependence on which archetypes are present in the cell."""
    base = _make_29col_gdf(
        ["SmallOffice", "MediumOffice", "OpenUBEMUnknown", "OpenUBEMUnknown"]
    )
    r1, _ = enrich_semantics(base, random_seed=42)

    modified = _make_29col_gdf(
        ["LargeDataCenterHighITE", "Laboratory", "OpenUBEMUnknown", "OpenUBEMUnknown"]
    )
    r2, _ = enrich_semantics(modified, random_seed=42)

    a = r1.loc[[2, 3], _ALL_COLS].to_numpy(dtype=float)
    b = r2.loc[[2, 3], _ALL_COLS].to_numpy(dtype=float)
    assert np.allclose(a, b, atol=1e-9)


# ── 4. empty-pool guard ──────────────────────────────────────────────────────


def test_guard_raises_if_screen_would_empty_the_pool(monkeypatch):
    real_loads = _get_cross_archetype_loads()
    all_archetypes = set(real_loads.index)
    with pytest.raises(ValueError):
        _capture_bounds(monkeypatch, exclude=all_archetypes)


# ── 5. non-vacuity probe ─────────────────────────────────────────────────────


def test_non_vacuity_probe_widening_exclusion_to_empty_restores_unscreened_ceiling(
    monkeypatch,
):
    bounds = _capture_bounds(monkeypatch, exclude=set(), exclude_occ=set())
    lo, hi = bounds["equipment_w_m2"]
    assert round(hi, 2) == 5381.96
