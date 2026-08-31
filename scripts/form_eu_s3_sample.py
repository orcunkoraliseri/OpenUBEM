"""Form the ruled EU-04 `S3` 96-building binational sample.

Authority: ``D-EU-23`` ruled 2026-08-27, **Option G1** -- *"S3 sample formation
proceeds at N=96 using the mixed-mode architecture established in S2
(dwelling-partitioned where the EU-04 contract emits; one_zone_per_floor
fallback where geometric/partition audit boundaries apply). Both layout mode
and simulation mode axes must be printed explicitly in all S3 acceptance
panels."*

The selection rule is pre-registered here and reads **inputs only**:

1. The population is every ``layout_ready`` row of the two ruled `S3` sites
   whose age band resolves -- a type, an observed year and an observed
   dwelling count, all present.
2. The frame is 16 cells: 2 countries x 4 TABULA types x 2 age bands.
3. Each cell takes its lowest-``building_id`` rows up to a base quota of 6
   (16 x 6 = 96).
4. Any shortfall is redistributed by a single deterministic round-robin over
   the cells in ``(country, type, age)`` order, one row at a time, from cells
   that still hold unselected rows.
5. If 96 cannot be reached, the script **fails closed** and reports the
   deficit rather than shrinking the sample silently.

``D-EU-04-H`` is binding throughout: neither the layout outcome nor any
simulation result is an input to any step above.  Both are carried into the
manifest as independent measured columns.

Usage:  .venv/Scripts/python.exe scripts/form_eu_s3_sample.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "openubem/outputs/eu_evidence/EU-04/s3"
CENSUS_PATH = OUT / "s3_scope_measurement.csv"
SAMPLE_PATH = OUT / "s3_sample.csv"
SUMMARY_PATH = OUT / "s3_sample_summary.json"

COUNTRY_ORDER = ("ES", "FR")
TYPE_ORDER = ("AB", "MFH", "TH", "SFH")
AGE_ORDER = ("OLD_PRE_1945", "NEW_POST_1945")
TARGET = 96
BASE_QUOTA = 6
SELECTION_BASIS = "LADDER_INPUTS_ONLY_COUNTRY_TYPE_AGE_CELLS_BUILDING_ID_ORDER"

#: Recorded in every artefact so the two axes can never be collapsed into one.
LAYOUT_AXIS = "layout_status_measured"
SIMULATION_AXIS = "simulation_mode_expected"


def _as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    values = series.astype(str).str.strip().str.lower()
    if not values.isin({"true", "false"}).all():
        raise ValueError("layout_ready must contain only boolean values")
    return values.eq("true")


def eligible_population(census: pd.DataFrame) -> pd.DataFrame:
    """The `S3` frame, read from mapping inputs alone."""
    required = {
        "building_id", "country_stock_code", "building_type", "year_built",
        "archetype_id", "layout_ready", "age_band", LAYOUT_AXIS, SIMULATION_AXIS,
    }
    missing = required.difference(census.columns)
    if missing:
        raise ValueError(f"S3 census is missing required columns: {sorted(missing)}")
    eligible = census.loc[
        _as_bool(census["layout_ready"])
        & census["country_stock_code"].isin(COUNTRY_ORDER)
        & census["building_type"].isin(TYPE_ORDER)
        & census["age_band"].isin(AGE_ORDER)
    ].copy()
    if eligible["building_id"].duplicated().any():
        raise ValueError("S3 eligibility has duplicate building_id values")
    return eligible.sort_values("building_id", kind="stable")


def _cells() -> list[tuple[str, str, str]]:
    return [
        (country, building_type, age)
        for country in COUNTRY_ORDER
        for building_type in TYPE_ORDER
        for age in AGE_ORDER
    ]


def form_s3_sample(census: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Select the ruled 96, or fail closed with the deficit named."""
    eligible = eligible_population(census)
    pools = {
        cell: eligible.loc[
            (eligible["country_stock_code"] == cell[0])
            & (eligible["building_type"] == cell[1])
            & (eligible["age_band"] == cell[2])
        ]
        for cell in _cells()
    }

    taken: dict[tuple[str, str, str], int] = {
        cell: min(BASE_QUOTA, len(pool)) for cell, pool in pools.items()
    }
    base_total = sum(taken.values())

    # Deterministic round-robin over the same fixed cell order, one row at a
    # time, until the target is met or every pool is exhausted.
    while sum(taken.values()) < TARGET:
        progressed = False
        for cell in _cells():
            if sum(taken.values()) >= TARGET:
                break
            if taken[cell] < len(pools[cell]):
                taken[cell] += 1
                progressed = True
        if not progressed:
            break

    selected_total = sum(taken.values())
    if selected_total != TARGET:
        raise ValueError(
            f"S3 cannot form its ruled {TARGET}: the eligible corpus yields "
            f"{selected_total} across {len(pools)} cells "
            f"({ {'|'.join(cell): len(pool) for cell, pool in pools.items()} })"
        )

    frames = []
    for cell in _cells():
        chunk = pools[cell].head(taken[cell]).copy()
        chunk["s3_cell"] = "|".join(cell)
        chunk["s3_cell_base_quota"] = BASE_QUOTA
        chunk["s3_cell_selected"] = taken[cell]
        chunk["s3_selection_basis"] = SELECTION_BASIS
        frames.append(chunk)
    sample = pd.concat(frames, ignore_index=True)
    if len(sample) != TARGET or sample["building_id"].duplicated().any():
        raise ValueError(f"S3 must yield exactly {TARGET} unique rows")

    summary = {
        "decision": "D-EU-23 = G1 (96 buildings, mixed mode, both axes printed)",
        "sample_kind": "BINATIONAL_MIXED_MODE_PILOT_SAMPLE",
        "sample_rows": int(len(sample)),
        "target": TARGET,
        "base_quota_per_cell": BASE_QUOTA,
        "rows_from_base_quota": int(base_total),
        "rows_from_shortfall_redistribution": int(selected_total - base_total),
        "selection_basis": (
            "country x type x age cells, lowest building_id first, shortfall redistributed by a "
            "fixed round-robin; layout and EnergyPlus outcomes are excluded from selection "
            "(D-EU-04-H)"
        ),
        "country_counts": {
            country: int((sample["country_stock_code"] == country).sum())
            for country in COUNTRY_ORDER
        },
        "building_type_counts": {
            building_type: int((sample["building_type"] == building_type).sum())
            for building_type in TYPE_ORDER
        },
        "age_counts": {
            age: int((sample["age_band"] == age).sum()) for age in AGE_ORDER
        },
        "cell_allocation": {
            "|".join(cell): {"eligible": int(len(pools[cell])), "selected": int(taken[cell])}
            for cell in _cells()
        },
        # The two axes D-EU-23 G1 requires to be printed separately.
        "layout_mode_axis": {
            str(key): int(value) for key, value in sample[LAYOUT_AXIS].value_counts().items()
        },
        "simulation_mode_axis": {
            str(key): int(value) for key, value in sample[SIMULATION_AXIS].value_counts().items()
        },
        "layout_mode_axis_by_country": {
            country: {
                str(key): int(value)
                for key, value in sample.loc[
                    sample["country_stock_code"] == country, LAYOUT_AXIS
                ]
                .value_counts()
                .items()
            }
            for country in COUNTRY_ORDER
        },
        "type_provenance_counts": {
            str(key): int(value) for key, value in sample["type_provenance"].value_counts().items()
        },
        "dwellings_provenance_counts": {
            str(key): int(value)
            for key, value in sample["dwellings_provenance"].value_counts().items()
        },
        "axis_note": (
            "layout_mode_axis and simulation_mode_axis are reported separately and must never be "
            "collapsed: a building that falls back to one_zone_per_floor is a dwelling-layout "
            "refusal AND a valid mixed-mode S3 member."
        ),
    }
    return sample, summary


def main() -> None:
    census = pd.read_csv(CENSUS_PATH)
    sample, summary = form_s3_sample(census)
    OUT.mkdir(parents=True, exist_ok=True)
    sample.to_csv(SAMPLE_PATH, index=False)
    summary["source_census_sha256"] = hashlib.sha256(CENSUS_PATH.read_bytes()).hexdigest()
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote {SAMPLE_PATH} ({len(sample)} rows)")


if __name__ == "__main__":
    main()
