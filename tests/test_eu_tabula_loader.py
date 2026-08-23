"""Reconciliation checks for the copied Step 8 TABULA parameter tables."""

from __future__ import annotations

from pathlib import Path

import pytest

from openubem.data.construction.tabula_reconcile import (
    assert_parent_invariants,
    load_parent_tables,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "eu" / "step8_outputs"
FOLDS = ("es", "uk", "it")
EXPECTED_ROW_COUNTS = {"es": 24, "uk": 36, "it": 42}
EXPECTED_CONSTRUCTION_YEAR_CLASSES = {
    "es": {"ES.01", "ES.02", "ES.03", "ES.04", "ES.05", "ES.06"},
    "uk": {"GB.01", "GB.02", "GB.03", "GB.04", "GB.05", "GB.06", "GB.07", "GB.08"},
    "it": {"IT.01", "IT.02", "IT.03", "IT.04", "IT.05", "IT.06", "IT.07", "IT.08"},
}
EXPECTED_CLIMATE_REGIONS = {
    "es": {"ES.ME"},
    "uk": {"GB.Temperate"},
    "it": {"IT.MidClim"},
}


@pytest.fixture(scope="module")
def tables():
    return load_parent_tables(FIXTURE_DIR)


@pytest.fixture(scope="module")
def observed(tables):
    return assert_parent_invariants(tables)


@pytest.mark.parametrize("fold", FOLDS)
def test_row_counts(observed, fold):
    assert observed["row_counts"][fold] == EXPECTED_ROW_COUNTS[fold]


@pytest.mark.parametrize("fold", FOLDS)
def test_boundary_condition_set(observed, fold):
    assert set(observed["boundary_conditions"][fold]) == {"EU.SUH", "EU.MUH"}


@pytest.mark.parametrize("fold", FOLDS)
def test_number_building_variant_is_one(observed, fold):
    assert observed["number_building_variant_is_one"][fold]


@pytest.mark.parametrize("fold", FOLDS)
def test_existing_state_building_variant_suffix(observed, fold):
    assert observed["building_variant_suffix"][fold]


@pytest.mark.parametrize("fold", FOLDS)
def test_construction_year_classes(observed, fold):
    assert set(observed["construction_year_classes"][fold]) == EXPECTED_CONSTRUCTION_YEAR_CLASSES[fold]


@pytest.mark.parametrize("fold", FOLDS)
def test_phi_int_is_three(observed, fold):
    assert observed["phi_int_is_three"][fold]


@pytest.mark.parametrize("fold", FOLDS)
def test_climate_regions(observed, fold):
    assert set(observed["climate_regions"][fold]) == EXPECTED_CLIMATE_REGIONS[fold]


def test_gb_building_codes_start_with_england_prefix(observed):
    assert observed["gb_building_codes_start_gb_eng"]


def test_es_test_region_is_absent(observed):
    assert observed["es_test_region_absent"]


def test_non_eu_boundary_condition_is_refused(tables):
    contaminated = {fold: table.copy() for fold, table in tables.items()}
    contaminated["es"].loc[0, "Code_BoundaryCond"] = "ES.SUH"

    with pytest.raises(ValueError, match="Code_BoundaryCond"):
        assert_parent_invariants(contaminated)
