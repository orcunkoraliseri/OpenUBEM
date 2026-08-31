"""EU-14B T01 acceptance tests.

`scripts/emit_eu11_layout_sidecars.py` once wrote
``updated_outcomes.get(str(b), "")`` for every manifest row: any mismatch
between the rows the emitter recomputed and the rows already on disk silently
blanked ``geometry_outcome`` fleet-wide. This happened for real against the
Bologna (``IT-BOL-GALVANI2``) manifest because the emitter's district dispatch
routed Bologna through the generic ``_mapped_rows`` codepath instead of the
ISTAT census-section cascade (``_it_rows``) that actually produced its rows,
so it recomputed zero matching rows and blanked all 1,204.

These tests exercise ``safe_update_manifest_columns`` -- the function that
replaced the direct assignment -- in isolation, against a copy of the real
Bologna manifest, without touching the checked-in file.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from scripts.emit_eu11_layout_sidecars import ManifestSafetyError, safe_update_manifest_columns

ROOT = Path(__file__).resolve().parents[2]
BOLOGNA_MANIFEST = (
    ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / "IT-BOL-GALVANI2"
    / "it_bol_galvani2_manifest.csv"
)


@pytest.fixture()
def manifest_copy(tmp_path: Path) -> Path:
    if not BOLOGNA_MANIFEST.exists():
        pytest.skip("Bologna EU-11 manifest not present in this environment")
    dest = tmp_path / "it_bol_galvani2_manifest.csv"
    shutil.copy2(BOLOGNA_MANIFEST, dest)
    return dest


def test_t01_legitimate_update_is_written_and_other_columns_stay_byte_identical(manifest_copy):
    original_df = pd.read_csv(manifest_copy)
    original_bytes = manifest_copy.read_bytes()
    bids = original_df["building_id"].astype(str).tolist()

    updates = {bid: "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT" for bid in bids}
    layout_updates = {bid: f"openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/layouts/{bid}.json" for bid in bids}

    new_df = safe_update_manifest_columns(
        manifest_copy,
        column_updates={"geometry_outcome": updates, "layout_json": layout_updates},
    )

    assert manifest_copy.read_bytes() != original_bytes
    assert len(new_df) == len(original_df)
    assert set(new_df["building_id"].astype(str)) == set(bids)
    assert (new_df["geometry_outcome"] == "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT").all()
    assert (new_df["layout_json"] != "").all()

    owned = {"geometry_outcome", "layout_json"}
    for col in original_df.columns:
        if col in owned:
            continue
        pd.testing.assert_series_equal(
            new_df[col].reset_index(drop=True),
            original_df[col].reset_index(drop=True),
            check_names=False,
        )


def test_t01_partial_update_never_touches_unmatched_rows(manifest_copy):
    original_df = pd.read_csv(manifest_copy)
    bids = original_df["building_id"].astype(str).tolist()
    subset = bids[:5]

    new_df = safe_update_manifest_columns(
        manifest_copy,
        column_updates={"geometry_outcome": {bid: "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT" for bid in subset}},
    )

    untouched = new_df[~new_df["building_id"].astype(str).isin(subset)]
    original_untouched = original_df[~original_df["building_id"].astype(str).isin(subset)]
    pd.testing.assert_series_equal(
        untouched["geometry_outcome"].reset_index(drop=True),
        original_untouched["geometry_outcome"].reset_index(drop=True),
        check_names=False,
    )


def test_t01_zero_matched_rows_no_longer_blanks_the_manifest(manifest_copy):
    """The exact historical failure mode: the row-recompute step matches
    nothing (as happened when Bologna was routed through _mapped_rows), so
    the update dict is empty. The manifest must come back untouched, not
    blanked."""
    original_df = pd.read_csv(manifest_copy)
    original_bytes = manifest_copy.read_bytes()

    new_df = safe_update_manifest_columns(
        manifest_copy,
        column_updates={"geometry_outcome": {}, "layout_json": {}},
    )

    assert manifest_copy.read_bytes() == original_bytes
    pd.testing.assert_series_equal(
        new_df["geometry_outcome"].reset_index(drop=True),
        original_df["geometry_outcome"].reset_index(drop=True),
        check_names=False,
    )
    assert new_df["geometry_outcome"].notna().all()
    assert (new_df["geometry_outcome"].astype(str).str.strip() != "").all()


def test_t01_malformed_row_referencing_unknown_building_id_aborts_without_writing(manifest_copy):
    original_bytes = manifest_copy.read_bytes()

    with pytest.raises(ManifestSafetyError):
        safe_update_manifest_columns(
            manifest_copy,
            column_updates={"geometry_outcome": {"NOT_A_REAL_BUILDING_ID": "DWELLING_LAYOUT_EMITTED"}},
        )

    assert manifest_copy.read_bytes() == original_bytes


def test_t01_computed_blank_value_for_a_matched_row_aborts_without_writing(manifest_copy):
    original_df = pd.read_csv(manifest_copy)
    original_bytes = manifest_copy.read_bytes()
    bid = str(original_df["building_id"].iloc[0])
    assert not pd.isna(original_df["geometry_outcome"].iloc[0])
    assert str(original_df["geometry_outcome"].iloc[0]).strip() != ""

    with pytest.raises(ManifestSafetyError):
        safe_update_manifest_columns(
            manifest_copy,
            column_updates={"geometry_outcome": {bid: ""}},
        )

    assert manifest_copy.read_bytes() == original_bytes

