"""The `S3` selection rule must read inputs only, and fail closed (`D-EU-23` G1)."""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.form_eu_s3_sample import (
    BASE_QUOTA,
    COUNTRY_ORDER,
    TARGET,
    TYPE_ORDER,
    eligible_population,
    form_s3_sample,
)


AGE_ORDER = ("OLD_PRE_1945", "NEW_POST_1945")


def _census(per_cell: dict[tuple[str, str, str], int], *, outcome_bias: bool = False) -> pd.DataFrame:
    """Build a synthetic census with ``per_cell`` eligible rows in each cell.

    When ``outcome_bias`` is set, the *lowest* building_id in every cell is the
    one that falls back -- so a selector that quietly preferred emitting
    buildings would produce a different sample and the test would catch it.
    """
    rows = []
    counter = 0
    for (country, building_type, age), count in per_cell.items():
        for index in range(count):
            counter += 1
            emitted = (index > 0) if outcome_bias else True
            rows.append(
                {
                    "building_id": f"b{counter:04d}",
                    "neighbourhood_id": f"{country}-SITE",
                    "country_stock_code": country,
                    "building_type": building_type,
                    "year_built": 1900 if age == AGE_ORDER[0] else 1980,
                    "archetype_id": f"{country}.{building_type}.001",
                    "mapping_status": "MAPPED_LAYOUT_READY",
                    "layout_ready": True,
                    "age_band": age,
                    "type_provenance": "OBSERVED_TAG",
                    "dwellings_provenance": "CATASTRO_INSPIRE_BU_OBSERVED",
                    "layout_status_measured": (
                        "DWELLING_LAYOUT_EMITTED" if emitted else "FALLBACK_PENDING_LAYOUT"
                    ),
                    "simulation_mode_expected": (
                        "EUROPEAN_DWELLING_LAYOUT" if emitted else "FALLBACK_ONE_ZONE_PER_FLOOR"
                    ),
                }
            )
    return pd.DataFrame(rows)


def _uniform(count: int) -> dict[tuple[str, str, str], int]:
    return {
        (country, building_type, age): count
        for country in COUNTRY_ORDER
        for building_type in TYPE_ORDER
        for age in AGE_ORDER
    }


def test_a_full_corpus_takes_the_base_quota_from_every_cell():
    sample, summary = form_s3_sample(_census(_uniform(10)))

    assert len(sample) == TARGET
    assert summary["rows_from_base_quota"] == TARGET
    assert summary["rows_from_shortfall_redistribution"] == 0
    assert set(summary["cell_allocation"]) == {
        f"{country}|{building_type}|{age}"
        for country in COUNTRY_ORDER
        for building_type in TYPE_ORDER
        for age in AGE_ORDER
    }
    assert all(cell["selected"] == BASE_QUOTA for cell in summary["cell_allocation"].values())


def test_a_thin_cell_is_topped_up_from_the_others_and_the_deficit_is_reported():
    pools = _uniform(20)
    pools[("FR", "SFH", "NEW_POST_1945")] = 1  # the measured Lyon SFH ceiling
    sample, summary = form_s3_sample(_census(pools))

    assert len(sample) == TARGET
    assert summary["cell_allocation"]["FR|SFH|NEW_POST_1945"]["selected"] == 1
    assert summary["rows_from_base_quota"] == TARGET - BASE_QUOTA + 1
    assert summary["rows_from_shortfall_redistribution"] == BASE_QUOTA - 1


def test_selection_never_reads_the_layout_outcome():
    pools = _uniform(10)
    unbiased, _ = form_s3_sample(_census(pools))
    biased, _ = form_s3_sample(_census(pools, outcome_bias=True))

    assert list(unbiased["building_id"]) == list(biased["building_id"])


def test_both_axes_are_printed_and_never_collapsed():
    pools = _uniform(10)
    _, summary = form_s3_sample(_census(pools, outcome_bias=True))

    assert summary["layout_mode_axis"]["DWELLING_LAYOUT_EMITTED"] > 0
    assert summary["layout_mode_axis"]["FALLBACK_PENDING_LAYOUT"] == 16
    assert summary["simulation_mode_axis"]["FALLBACK_ONE_ZONE_PER_FLOOR"] == 16
    assert set(summary["layout_mode_axis_by_country"]) == set(COUNTRY_ORDER)


def test_a_corpus_that_cannot_reach_96_fails_closed_rather_than_shrinking():
    with pytest.raises(ValueError, match="cannot form its ruled 96"):
        form_s3_sample(_census(_uniform(5)))


def test_rows_that_are_not_layout_ready_are_not_eligible():
    census = _census(_uniform(10))
    census.loc[census.index[:20], "layout_ready"] = False

    assert len(eligible_population(census)) == len(census) - 20
