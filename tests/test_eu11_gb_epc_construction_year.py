from scripts.run_eu_s2_district_campaign import _gb_age_decision


def test_non_straddling_band_unchanged():
    assert _gb_age_decision("E", set()) == ("GB.04", "E", "")


def test_straddling_band_no_year():
    assert _gb_age_decision("D", set()) == (None, "PERIOD_STRADDLE_D_GB.03_GB.04", "")


def test_no_band_single_period_year_b1():
    assert _gb_age_decision(None, {2019}) == ("GB.08", "", "EPC_OBSERVED_CONSTRUCTION_YEAR")


def test_no_band_years_spanning_two_periods():
    assert _gb_age_decision(None, {2008, 2019}) == (None, "MISSING_OBSERVED_EPC_AGE_BAND", "")


def test_straddle_plus_in_band_year_b2():
    assert _gb_age_decision("K", {2009}) == ("GB.07", "K", "EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE")


def test_straddle_plus_contradicting_year():
    assert _gb_age_decision("B", {2013}) == (None, "PERIOD_STRADDLE_B_GB.01_GB.02", "")
