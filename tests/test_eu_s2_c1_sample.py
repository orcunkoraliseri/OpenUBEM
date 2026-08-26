import pandas as pd
import pytest

from scripts.form_eu_s2_c1_sample import (
    AGE_ORDER,
    CENSUS_PATH,
    HIGH_COMPLETENESS,
    TYPE_ORDER,
    eligible_c1_inputs,
    form_c1_sample,
)


def test_c1a_forms_the_ruled_31_row_sample_with_all_eligible_sfh_rows():
    census = pd.read_csv(CENSUS_PATH)
    sample, summary = form_c1_sample(census)

    assert len(sample) == 31
    assert sample.building_id.is_unique
    assert sample.completeness_band.eq(HIGH_COMPLETENESS).all()
    assert summary["decision"] == "D-EU-04-S2-C = C1A (31-row correction)"
    assert summary["building_type_counts"] == {
        "AB": 8, "MFH": 8, "TH": 8, "SFH": 7
    }
    assert summary["age_counts_by_type"] == {
        "AB": {"OLD_PRE_1945": 4, "NEW_POST_1945": 4},
        "MFH": {"OLD_PRE_1945": 4, "NEW_POST_1945": 4},
        "TH": {"OLD_PRE_1945": 4, "NEW_POST_1945": 4},
        "SFH": {"OLD_PRE_1945": 6, "NEW_POST_1945": 1},
    }
    assert sample.loc[sample.building_type.eq("SFH"), "age_band"].value_counts().to_dict() == {
        "OLD_PRE_1945": 6, "NEW_POST_1945": 1
    }


def test_c1_candidate_pool_does_not_depend_on_geometry_outcomes():
    census = pd.read_csv(CENSUS_PATH)
    baseline = eligible_c1_inputs(census)
    altered = census.copy()
    altered["shape_class"] = "ALTERED"
    altered["layout_status_measured"] = "DWELLING_LAYOUT_EMITTED"
    altered["layout_reason_measured"] = "ALTERED"
    rerun = eligible_c1_inputs(altered)

    assert list(rerun.building_id) == list(baseline.building_id)
    assert set(rerun.building_type) == set(TYPE_ORDER)


def test_c1_refuses_non_high_completeness_eligible_rows():
    census = pd.read_csv(CENSUS_PATH)
    row = census.loc[census["layout_ready"]].index[0]
    census.loc[row, "completeness_band"] = "LOW_OR_INCOMPLETE_MAPPING_INPUTS"

    with pytest.raises(ValueError, match="non-high-completeness"):
        form_c1_sample(census)
