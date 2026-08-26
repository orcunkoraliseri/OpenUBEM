"""Form the ruled EU-04 S2 C1A high-completeness operational sample.

The C1A correction selects 31 mapping-ready Lyon observations by input data
only: eight rows each for AB/MFH/TH and all seven SFH rows, balanced four
old/four new where the retained corpus permits. Layout and EnergyPlus outcomes
are deliberately not inputs to selection; the already measured layout columns
are carried into the manifest as independent observation results.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CENSUS_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_scope_measurement.csv"
OUT_DIR = ROOT / "openubem/outputs/eu_evidence/EU-04"
SAMPLE_PATH = OUT_DIR / "s2_c1_high_completeness_sample.csv"
SUMMARY_PATH = OUT_DIR / "s2_c1_high_completeness_sample_summary.json"

TYPE_ORDER = ("AB", "MFH", "TH", "SFH")
AGE_ORDER = ("OLD_PRE_1945", "NEW_POST_1945")
HIGH_COMPLETENESS = "HIGH_MAPPING_INPUT_COMPLETENESS"
TYPE_QUOTAS = {"AB": 8, "MFH": 8, "TH": 8, "SFH": 7}


def _as_bool(series: pd.Series) -> pd.Series:
    """Accept CSV booleans without treating arbitrary non-empty strings as true."""
    if series.dtype == bool:
        return series
    values = series.astype(str).str.strip().str.lower()
    if not values.isin({"true", "false"}).all():
        raise ValueError("layout_ready must contain only boolean values")
    return values.eq("true")


def eligible_c1_inputs(census: pd.DataFrame) -> pd.DataFrame:
    """Return the C1 candidate pool without reading geometry-outcome columns."""
    required = {
        "building_id", "building_type", "year_built", "archetype_id",
        "layout_ready", "completeness_band", "age_band",
    }
    missing = required.difference(census.columns)
    if missing:
        raise ValueError(f"C1 census is missing required columns: {sorted(missing)}")

    eligible = census.loc[
        _as_bool(census["layout_ready"])
        & census["building_type"].isin(TYPE_ORDER)
        & census["age_band"].isin(AGE_ORDER)
    ].copy()
    if not eligible["completeness_band"].eq(HIGH_COMPLETENESS).all():
        raise ValueError("C1 eligibility contains a non-high-completeness row")
    if eligible["building_id"].duplicated().any():
        raise ValueError("C1 eligibility has duplicate building_id values")
    return eligible


def form_c1_sample(census: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Select the ruled C1 sample, or fail closed when its exact quotas cannot form."""
    eligible = eligible_c1_inputs(census)

    selections: list[pd.DataFrame] = []
    allocation: dict[str, dict[str, int]] = {}
    for building_type in TYPE_ORDER:
        typed = eligible.loc[eligible["building_type"] == building_type].sort_values("building_id")
        by_age = {
            age: typed.loc[typed["age_band"] == age].sort_values("building_id")
            for age in AGE_ORDER
        }
        quota = TYPE_QUOTAS[building_type]
        if len(typed) < quota:
            raise ValueError(
                f"C1A cannot form its ruled quota: requires {quota} {building_type} rows, found {len(typed)}"
            )

        initial = [by_age[age].head(4) for age in AGE_ORDER]
        selected = pd.concat(initial, ignore_index=False)
        selected = selected.loc[~selected["building_id"].duplicated()].copy()
        if len(selected) < quota:
            remaining = typed.loc[~typed["building_id"].isin(selected["building_id"])]
            selected = pd.concat([selected, remaining.head(quota - len(selected))], ignore_index=False)
        if len(selected) != quota:
            raise ValueError(f"C1A did not form {quota} {building_type} rows")

        selected = selected.sort_values(["age_band", "building_id"]).copy()
        selected["s2_c1_type_quota"] = quota
        selected["s2_c1_selection_basis"] = "MAPPING_READY_INPUTS_ONLY_BUILDING_ID_ORDER"
        selections.append(selected)
        allocation[building_type] = {
            age: int((selected["age_band"] == age).sum()) for age in AGE_ORDER
        }

    sample = pd.concat(selections, ignore_index=True)
    if len(sample) != sum(TYPE_QUOTAS.values()) or sample["building_id"].duplicated().any():
        raise ValueError("C1A must yield exactly 31 unique rows")
    if not sample["completeness_band"].eq(HIGH_COMPLETENESS).all():
        raise ValueError("C1 output contains a non-high-completeness row")

    geometry_columns = [
        column for column in ("shape_class", "layout_status_measured", "layout_reason_measured")
        if column in sample.columns
    ]
    if len(geometry_columns) != 3:
        raise ValueError("C1 manifest must retain independent geometry-result columns")

    summary = {
        "decision": "D-EU-04-S2-C = C1A (31-row correction)",
        "sample_kind": "HIGH_COMPLETENESS_OPERATIONAL_SAMPLE",
        "sample_rows": int(len(sample)),
        "building_type_counts": {
            building_type: int((sample["building_type"] == building_type).sum())
            for building_type in TYPE_ORDER
        },
        "age_counts_by_type": allocation,
        "all_rows_high_mapping_input_completeness": True,
        "selection_basis": "mapping-ready inputs and building_id order only; layout and EnergyPlus outcomes excluded",
        "geometry_result_columns": geometry_columns,
        "known_stock_exception": "SFH has 6 OLD_PRE_1945 and 1 NEW_POST_1945 eligible/selected rows; the operational sample is therefore 31 rows, not 32.",
        "interpretation": "This is a high-completeness operational sample, not a comparison of high versus low input completeness.",
    }
    return sample, summary


def main() -> None:
    census = pd.read_csv(CENSUS_PATH)
    sample, summary = form_c1_sample(census)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample.to_csv(SAMPLE_PATH, index=False)
    summary["source_census_sha256"] = hashlib.sha256(CENSUS_PATH.read_bytes()).hexdigest()
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote {SAMPLE_PATH} ({len(sample)} rows)")


if __name__ == "__main__":
    main()
