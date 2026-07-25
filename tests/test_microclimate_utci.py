from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openubem.microclimate import utci
from openubem.microclimate.utci import (
    FLAG_TA,
    FLAG_TMRT,
    FLAG_VAPOUR,
    FLAG_WIND,
    UTCI_CLASSES,
    UTCI_NODATA_CLASS,
    classify_stress,
    municipal_risk_tier,
    utci_approx,
)

FIXTURE = Path(__file__).parent / "fixtures" / "utci_reference_table.csv"


def test_reference_table_atol_1e6():
    """§4.5 / CP-1 gate: exact vs an independent transcription of the same official polynomial."""
    df = pd.read_csv(FIXTURE)
    computed, flags = utci_approx(
        df["ta_c"].to_numpy(), df["tmrt_c"].to_numpy(), df["va10_ms"].to_numpy(), df["e_kpa"].to_numpy()
    )
    assert (flags == 0).all(), "reference rows must all be in-domain (no clamping)"
    err = np.abs(computed - df["utci_expected_c"].to_numpy())
    assert err.max() < 1e-6, f"max abs error {err.max():.3e} at row {int(err.argmax())}"


def test_reference_row_count():
    df = pd.read_csv(FIXTURE)
    assert len(df) >= 12


def test_kpa_to_hpa_conversion_pinned():
    """§4.4: the internal kPa->hPa conversion happens exactly once, at e_kpa*10."""
    ta, tmrt, va = 20.0, 20.0, 2.0
    for e_kpa in (0.5, 1.0, 2.339, 4.9):
        utci_c, _flags = utci_approx(ta, tmrt, va, e_kpa)
        offset = utci._brode_polynomial_offset(np.array(ta), np.array(va), np.array(0.0), np.array(e_kpa * 10.0))
        assert utci_c == pytest.approx(ta + offset, abs=1e-9)


def test_flags_fire_independently():
    ta, flags = utci_approx(ta_c=-60.0, tmrt_c=-60.0, va10_ms=2.0, e_kpa=1.0)
    assert bool(flags & FLAG_TA)
    assert not bool(flags & FLAG_TMRT)
    assert not bool(flags & FLAG_WIND)
    assert not bool(flags & FLAG_VAPOUR)

    _, flags = utci_approx(ta_c=20.0, tmrt_c=120.0, va10_ms=2.0, e_kpa=1.0)
    assert bool(flags & FLAG_TMRT) and not bool(flags & FLAG_TA)

    _, flags = utci_approx(ta_c=20.0, tmrt_c=20.0, va10_ms=0.1, e_kpa=1.0)
    assert bool(flags & FLAG_WIND) and not bool(flags & FLAG_TA)

    _, flags = utci_approx(ta_c=20.0, tmrt_c=20.0, va10_ms=2.0, e_kpa=10.0)
    assert bool(flags & FLAG_VAPOUR) and not bool(flags & FLAG_WIND)


def test_combined_out_of_bounds_sets_multiple_bits():
    _, flags = utci_approx(ta_c=200.0, tmrt_c=200.0, va10_ms=-5.0, e_kpa=99.0)
    assert bool(flags & FLAG_TA)
    assert bool(flags & FLAG_WIND)
    assert bool(flags & FLAG_VAPOUR)


def test_output_finite_for_absurd_inputs():
    utci_c, flags = utci_approx(ta_c=200.0, tmrt_c=200.0, va10_ms=-5.0, e_kpa=300.0)
    assert np.isfinite(utci_c).all()
    assert flags != 0


def test_wind_clamp_fires_below_0p5():
    _, flags = utci_approx(ta_c=25.0, tmrt_c=25.0, va10_ms=0.2, e_kpa=1.0)
    assert bool(flags & FLAG_WIND)


def test_reference_table_smoke_u05_table4_unverified():
    # unverified -- see PLAN §4.5. Loose smoke check only, never the gate.
    cases = [
        (28.0, 28.0, 0.6, 1.5, 19.6),
        (32.0, 40.0, 1.0, 2.0, 41.2),
    ]
    for ta, tmrt, va, e, expected in cases:
        computed, _flags = utci_approx(ta, tmrt, va, e)
        assert abs(float(computed) - expected) < 15.0  # deliberately loose: unverified source


def test_utci_approx_vectorised():
    ta = np.array([-20.0, 0.0, 20.0, 40.0])
    computed, flags = utci_approx(ta, ta, 0.5, 1.0)
    assert computed.shape == ta.shape
    assert flags.shape == ta.shape


# ── T07 — classify_stress / municipal_risk_tier ────────────────────────────────────────────

def test_class_boundaries_from_both_sides():
    for c in UTCI_CLASSES:
        if np.isfinite(c["min"]):
            below = classify_stress(np.array([c["min"] - 0.01]))[0]
            at = classify_stress(np.array([c["min"]]))[0]
            assert at == c["index"]
            assert below == c["index"] - 1


def test_classes_contiguous_no_gaps_no_overlap():
    mins = sorted(c["min"] for c in UTCI_CLASSES)
    maxs = sorted(c["max"] for c in UTCI_CLASSES)
    for i in range(len(UTCI_CLASSES) - 1):
        assert mins[i + 1] == maxs[i]


def test_ten_classes_ten_unique_colours():
    assert len(UTCI_CLASSES) == 10
    assert len({c["hex"] for c in UTCI_CLASSES}) == 10


def test_nan_maps_to_nodata_class():
    out = classify_stress(np.array([np.nan, 20.0]))
    assert out[0] == UTCI_NODATA_CLASS
    assert out[1] == 5  # 9..26 -> "No thermal stress"


def test_municipal_tiers_four_and_monotone():
    from openubem.microclimate.utci import MUNICIPAL_TIERS
    assert len(MUNICIPAL_TIERS) == 4
    assert municipal_risk_tier(np.array([10.0]))[0] == 0
    assert municipal_risk_tier(np.array([27.0]))[0] == 1
    assert municipal_risk_tier(np.array([35.0]))[0] == 2
    assert municipal_risk_tier(np.array([50.0]))[0] == 3
