import pandas as pd
import pytest

from openubem.microclimate.epw_hourly import read_epw_hourly
from openubem.microclimate.window import (
    AnnualEnergyPlusWindowRefusedError,
    select_window,
)

SYNTHETIC_EPW = "tests/fixtures/synthetic.epw"


@pytest.fixture(scope="module")
def epw_df():
    return read_epw_hourly(SYNTHETIC_EPW)


def test_hottest_week_length_and_contiguity(epw_df):
    window = select_window(epw_df, mode="hottest_week")
    assert len(window) == 168
    diffs = window.to_series().diff().dropna()
    assert (diffs == pd.Timedelta(hours=1)).all()


def test_hottest_week_maximises_mean_dry_bulb(epw_df):
    window = select_window(epw_df, mode="hottest_week")
    selected_mean = epw_df.loc[window, "dry_bulb_c"].mean()
    rolling = epw_df["dry_bulb_c"].rolling(window=168).mean().dropna()
    assert selected_mean == pytest.approx(rolling.max(), abs=1e-9)
    assert selected_mean >= rolling.max() - 1e-9


def test_hottest_week_deterministic_across_10_calls(epw_df):
    results = [select_window(epw_df, mode="hottest_week") for _ in range(10)]
    for r in results[1:]:
        assert r.equals(results[0])


def test_annual_returns_full_index(epw_df):
    window = select_window(epw_df, mode="annual", wall_temp_tier="empirical")
    assert len(window) == len(epw_df)
    assert window.equals(epw_df.index)


def test_annual_with_energyplus_tier_refused_by_default(epw_df):
    with pytest.raises(AnnualEnergyPlusWindowRefusedError):
        select_window(epw_df, mode="annual", wall_temp_tier="energyplus")


def test_annual_with_energyplus_tier_allowed_with_override(epw_df):
    window = select_window(
        epw_df, mode="annual", wall_temp_tier="energyplus", override_annual_energyplus=True
    )
    assert len(window) == len(epw_df)


def test_design_hours_resolves_known_rows(epw_df):
    first_ts = epw_df.index[0]
    hours = [(first_ts.month, first_ts.day, first_ts.hour)]
    window = select_window(epw_df, mode="design_hours", design_hours=hours)
    assert len(window) == 1
    assert window[0] == first_ts


def test_design_hours_missing_raises(epw_df):
    with pytest.raises(ValueError):
        select_window(epw_df, mode="design_hours", design_hours=[(2, 30, 12)])


def test_design_hours_requires_argument(epw_df):
    with pytest.raises(ValueError):
        select_window(epw_df, mode="design_hours")


def test_unknown_mode_raises(epw_df):
    with pytest.raises(ValueError):
        select_window(epw_df, mode="not_a_mode")
