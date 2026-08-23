"""Load and reconcile the copied Step 8 TABULA parameter-table fixtures.

The source tables are supplied by callers as a directory so this module has no
dependency on the parent repository.  It deliberately performs reconciliation
only; registry generation and boundary-condition joins belong to later work.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


_TABLE_FILENAMES = {
    "es": "archetype_parameters_es.csv",
    "uk": "archetype_parameters_uk.csv",
    "it": "archetype_parameters_it.csv",
}

_EXPECTED_ROW_COUNTS = {"es": 24, "uk": 36, "it": 42}
_EXPECTED_CONSTRUCTION_YEAR_CLASSES = {
    "es": {"ES.01", "ES.02", "ES.03", "ES.04", "ES.05", "ES.06"},
    "uk": {"GB.01", "GB.02", "GB.03", "GB.04", "GB.05", "GB.06", "GB.07", "GB.08"},
    "it": {"IT.01", "IT.02", "IT.03", "IT.04", "IT.05", "IT.06", "IT.07", "IT.08"},
}
_EXPECTED_CLIMATE_REGIONS = {
    "es": {"ES.ME"},
    "uk": {"GB.Temperate"},
    "it": {"IT.MidClim"},
}
_EXPECTED_BOUNDARY_CONDITIONS = {"EU.SUH", "EU.MUH"}


def load_parent_tables(step8_outputs_dir: Path) -> dict[str, pd.DataFrame]:
    """Read the three parent parameter tables, ignoring trailing ``#`` comments."""
    base_dir = Path(step8_outputs_dir)
    return {
        fold: pd.read_csv(base_dir / filename, comment="#")
        for fold, filename in _TABLE_FILENAMES.items()
    }


def assert_parent_invariants(tables: dict[str, pd.DataFrame]) -> dict:
    """Evaluate Walkthrough §9.3.1 invariants and return their observed values.

    A ``ValueError`` is raised if any parent-table invariant is violated.  The
    returned mapping contains only observed source-table values and booleans;
    it does not create or infer any registry parameter.
    """
    expected_folds = set(_TABLE_FILENAMES)
    if set(tables) != expected_folds:
        raise ValueError(
            f"Expected parent table folds {sorted(expected_folds)}, got {sorted(tables)}"
        )

    observed = {
        "row_counts": {},
        "boundary_conditions": {},
        "number_building_variant_is_one": {},
        "building_variant_suffix": {},
        "construction_year_classes": {},
        "phi_int_is_three": {},
        "climate_regions": {},
        "gb_building_codes_start_gb_eng": None,
        "es_test_region_absent": None,
    }
    failures: list[str] = []

    for fold, table in tables.items():
        row_count = len(table)
        observed["row_counts"][fold] = row_count
        if row_count != _EXPECTED_ROW_COUNTS[fold]:
            failures.append(
                f"rows({fold})={row_count}, expected {_EXPECTED_ROW_COUNTS[fold]}"
            )

        boundary_conditions = sorted(table["Code_BoundaryCond"].dropna().unique().tolist())
        observed["boundary_conditions"][fold] = boundary_conditions
        if set(boundary_conditions) != _EXPECTED_BOUNDARY_CONDITIONS:
            failures.append(
                f"Code_BoundaryCond({fold})={boundary_conditions}, "
                f"expected {sorted(_EXPECTED_BOUNDARY_CONDITIONS)}"
            )

        variants_are_one = bool(table["Number_BuildingVariant"].eq(1).all())
        observed["number_building_variant_is_one"][fold] = variants_are_one
        if not variants_are_one:
            failures.append(f"Number_BuildingVariant is not 1 on every {fold} row")

        suffixes_match = bool(
            table["Code_BuildingVariant"].astype("string").str.endswith(".001").fillna(False).all()
        )
        observed["building_variant_suffix"][fold] = suffixes_match
        if not suffixes_match:
            failures.append(f"Code_BuildingVariant does not end in .001 on every {fold} row")

        construction_year_classes = sorted(
            table["Code_ConstructionYearClass"].dropna().unique().tolist()
        )
        observed["construction_year_classes"][fold] = construction_year_classes
        if set(construction_year_classes) != _EXPECTED_CONSTRUCTION_YEAR_CLASSES[fold]:
            failures.append(
                f"Code_ConstructionYearClass({fold})={construction_year_classes}, "
                f"expected {sorted(_EXPECTED_CONSTRUCTION_YEAR_CLASSES[fold])}"
            )

        phi_int_is_three = bool(table["phi_int"].eq(3).all())
        observed["phi_int_is_three"][fold] = phi_int_is_three
        if not phi_int_is_three:
            failures.append(f"phi_int is not 3 on every {fold} row")

        climate_regions = sorted(table["Code_ClimateRegion"].dropna().unique().tolist())
        observed["climate_regions"][fold] = climate_regions
        if set(climate_regions) != _EXPECTED_CLIMATE_REGIONS[fold]:
            failures.append(
                f"Code_ClimateRegion({fold})={climate_regions}, "
                f"expected {sorted(_EXPECTED_CLIMATE_REGIONS[fold])}"
            )

    gb_prefixes_match = bool(
        tables["uk"]["Code_Building"].astype("string").str.startswith("GB.ENG.").fillna(False).all()
    )
    observed["gb_building_codes_start_gb_eng"] = gb_prefixes_match
    if not gb_prefixes_match:
        failures.append("Code_Building does not start with GB.ENG. on every GB row")

    es_test_region_absent = not tables["es"]["Code_Building"].astype("string").str.contains(
        "ES.TestRegion", regex=False, na=False
    ).any()
    observed["es_test_region_absent"] = bool(es_test_region_absent)
    if not es_test_region_absent:
        failures.append("ES.TestRegion appears in an ES row")

    if failures:
        raise ValueError("Parent table invariant failure: " + "; ".join(failures))
    return observed
