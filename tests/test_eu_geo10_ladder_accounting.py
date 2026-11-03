"""`GEO-10` — sample-group scale and stability, scored on retained artefacts only.

MVP §4.8, Table 4: *"Run 4, 12, 32, then 96 buildings — every attempted building accounted for
before neighbourhood scale."* The gate is an **accounting** gate, not a physics one: what it asserts
is that no building was attempted and then silently dropped, and that no failed run carries a number.

Nothing here simulates. Every assertion reads a manifest that a promoted campaign already produced,
so this can never re-run a cell, move an `idf_sha256`, or need EnergyPlus.

🔴 **Two honest deviations from Table 4's literal text, asserted rather than glossed:**

1. The third rung is **31**, not 32 — the frozen `S2` C1A sample is 31 high-completeness observed
   buildings (`AB`/`MFH`/`TH` 8 each, `SFH` 7). Quoting `GEO-10` as "4 / 12 / 32 / 96" would be
   wrong, so the count is pinned here and a change to it must break this test.
2. `S0`'s four are **synthetic** typology fixtures, not observed buildings. Table 4's ladder counts
   observed buildings from `S1` onward; `S0` is the smoke rung and is labelled as such.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from openubem.idf.european_box import S0_ARCHETYPE_IDS

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "openubem/outputs/eu_evidence/EU-04"
S1_MANIFEST = EVIDENCE / "s1_smoke_manifest.csv"
S2_MANIFEST = EVIDENCE / "s2_campaign_v3_manifest.csv"
S3_MANIFEST = EVIDENCE / "s3/s3_campaign_manifest.csv"

S1_EXPECTED = 12
S2_EXPECTED = 31
S3_EXPECTED = 96

S1_LAYOUT_OUTCOMES = {
    "DWELLING_LAYOUT_EMITTED", "FALLBACK_PENDING_LAYOUT", "REFUSED_BY_LAYOUT_CONTRACT",
}
S2_GEOMETRY_OUTCOMES = {"DWELLING_LAYOUT_EMITTED", "FALLBACK_PENDING_LAYOUT"}

requires_evidence = pytest.mark.skipif(
    not (S1_MANIFEST.exists() and S2_MANIFEST.exists() and S3_MANIFEST.exists()),
    reason="retained EU-04 ladder manifests are not present",
)


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


@requires_evidence
def test_s0_rung_is_four_synthetic_typology_fixtures():
    assert len(S0_ARCHETYPE_IDS) == 4
    assert len(set(S0_ARCHETYPE_IDS)) == 4


@requires_evidence
def test_ladder_rungs_are_the_measured_sizes_not_table_4_s_literal_text():
    """The third rung is 31, not 32. Pinned so it cannot be quoted as 32."""
    assert len(_read(S1_MANIFEST)) == S1_EXPECTED
    assert len(_read(S2_MANIFEST)) == S2_EXPECTED
    assert len(_read(S3_MANIFEST)) == S3_EXPECTED
    assert S2_EXPECTED != 32


@requires_evidence
def test_ladder_is_strictly_increasing():
    sizes = [len(S0_ARCHETYPE_IDS), S1_EXPECTED, S2_EXPECTED, S3_EXPECTED]
    assert sizes == sorted(sizes)
    assert len(set(sizes)) == len(sizes)


@pytest.mark.parametrize("path", [S1_MANIFEST, S2_MANIFEST, S3_MANIFEST])
@requires_evidence
def test_every_attempted_building_appears_exactly_once(path: Path):
    frame = _read(path)
    assert frame["building_id"].nunique() == len(frame)
    assert not frame["building_id"].isna().any()


@requires_evidence
def test_s1_every_building_carries_a_named_layout_and_energyplus_outcome():
    frame = _read(S1_MANIFEST)
    assert set(frame["layout_status"]) <= S1_LAYOUT_OUTCOMES
    assert not frame["layout_status"].isna().any()
    assert not frame["eplus_status"].isna().any()
    assert (frame["eplus_status"] == "EPLUS_COMPLETED").sum() == S1_EXPECTED


@requires_evidence
def test_s1_refusals_are_named_not_blank():
    """A refusal without a reason token is an unaccounted building, not an accounted one."""
    frame = _read(S1_MANIFEST)
    refused = frame[frame["layout_status"] == "REFUSED_BY_LAYOUT_CONTRACT"]
    assert len(refused) == 8
    assert not refused["layout_reason"].isna().any()
    assert (refused["layout_reason"].astype(str).str.strip() != "").all()


@requires_evidence
def test_s2_every_building_carries_a_geometry_outcome_and_a_return_code():
    frame = _read(S2_MANIFEST)
    assert set(frame["geometry_outcome"]) <= S2_GEOMETRY_OUTCOMES
    assert not frame["geometry_outcome"].isna().any()
    assert (frame["eplus_return_code"] == 0).sum() == S2_EXPECTED
    assert frame["fatal_errors"].sum() == 0
    assert frame["severe_errors"].sum() == 0


@requires_evidence
def test_s3_partitioned_and_massing_split_is_the_promoted_one():
    """`D-EU-23` mixed mode: both axes must be printable from the manifest alone."""
    frame = _read(S3_MANIFEST)
    modes = frame["layout_mode"].value_counts().to_dict()
    assert modes.get("DWELLING_LAYOUT_EMITTED") == 12
    assert modes.get("FALLBACK_PENDING_LAYOUT") == 84
    assert sum(modes.values()) == S3_EXPECTED


@requires_evidence
def test_s3_the_one_fatal_is_classified_and_not_hidden():
    frame = _read(S3_MANIFEST)
    fatal = frame[frame["fatal_errors"] > 0]
    assert len(fatal) == 1
    assert (fatal["eplus_return_code"] != 0).all()
    assert (frame["eplus_return_code"] == 0).sum() == 95


@requires_evidence
def test_s3_the_failed_run_carries_no_energy_number():
    """The accounting that matters: a failed building must be present and numberless."""
    frame = _read(S3_MANIFEST)
    fatal = frame[frame["fatal_errors"] > 0]
    assert fatal["heating_kwh"].isna().all()
    assert fatal["eui_kwh_m2"].isna().all()
    accepted = frame[frame["fatal_errors"] == 0]
    assert not accepted["heating_kwh"].isna().any()
    assert not accepted["eui_kwh_m2"].isna().any()


@requires_evidence
def test_s3_every_accepted_building_carries_its_idf_and_weather_digests():
    frame = _read(S3_MANIFEST)
    for column in ("idf_sha256", "weather_sha256"):
        assert not frame[column].isna().any()
        assert frame[column].astype(str).str.len().eq(64).all()
    assert frame["idf_sha256"].nunique() == S3_EXPECTED


@requires_evidence
def test_no_ladder_stage_silently_drops_a_building():
    """The GEO-10 acceptance sentence, asserted directly on all three observed rungs."""
    for path, expected, outcome_column in (
        (S1_MANIFEST, S1_EXPECTED, "layout_status"),
        (S2_MANIFEST, S2_EXPECTED, "geometry_outcome"),
        (S3_MANIFEST, S3_EXPECTED, "layout_mode"),
    ):
        frame = _read(path)
        accounted = frame[outcome_column].notna() & (
            frame[outcome_column].astype(str).str.strip() != ""
        )
        assert int(accounted.sum()) == expected, path.name
