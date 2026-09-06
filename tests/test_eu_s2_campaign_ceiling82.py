"""Unit coverage for `PLAN_eu-82pct-ceiling-2026-09-05.md` (D-EU-101, Step 2).

One test module, appended to per task as the plan's tasks land. Covers T01,
T02 (corrected #2 2026-09-05, period-set intersection), T03 (redesigned
2026-09-05, storey-ladder type classification), T04, and T08 (`FINDING 253`
construction reverse-order-mismatch fix).
"""
from __future__ import annotations

import hashlib
import json

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

import scripts.run_eu_s2_district_campaign as campaign_mod
from scripts.run_eu_s2_campaign import _assign_envelope_constructions, build_idf_for_building
from scripts.run_eu_s2_district_campaign import (
    DISTRICTS,
    ES_SIDECAR,
    GB_EPC,
    GB_EPC_BANDS,
    GB_EPC_YEARS,
    ROOT,
    _gb_age_decision,
    _gb_age_decision_multi,
    _gb_rows,
    _gb_sap_floor_storeys,
    _geometry,
    _mapped_rows,
    _valid_storeys,
)
from openubem.acquisition.catastro_inspire_fetcher import parse_catastro_building_part
from openubem.semantic.european_archetype_mapping import (
    apply_attribute_sidecar,
    derive_bdtopo_building_type,
)

MANIFEST = ROOT / "openubem/outputs/eu02/GB-LDN-STDUNSTANS/02_residential_manifest.gpkg"
RECORDS_PATH = ROOT / "openubem/data/construction/tabula_archetypes_gb.json"


def _cert_numbers_by_osm_id() -> dict[str, list[str]]:
    cert = pd.read_csv(GB_EPC)
    return (
        cert.assign(osm_id=cert["osm_id"].astype(str))
        .groupby("osm_id")["certificateNumber"]
        .apply(lambda s: [str(x) for x in s.dropna()])
        .to_dict()
    )


def _london_no_storey_ids_by_tag() -> dict[str, list[str]]:
    """Replays the pipeline's own age-band gate (pre-T01, unmodified) to name
    every London footprint that reaches the storey check with no observed
    storeys -- the population T01's `sap_floor_dimensions` fallback targets.
    """
    gdf = gpd.read_file(MANIFEST)
    cert = pd.read_csv(GB_EPC)
    cert = cert.dropna(subset=["age_band", "osm_id", "registrationDate"]).copy()
    cert["registrationDate"] = pd.to_datetime(cert["registrationDate"], errors="coerce")
    latest = cert.sort_values(
        ["osm_id", "registrationDate", "certificateNumber"], kind="stable"
    ).drop_duplicates("osm_id", keep="last")
    bands = latest.set_index(latest["osm_id"].astype(str))["age_band"].astype(str).to_dict()
    years: dict[str, set[int]] = {}
    side = pd.read_csv(GB_EPC_YEARS)
    for key, group in side.groupby(side["osm_id"].astype(str)):
        years[key] = {int(v) for v in group["construction_year"]}
    by_tag: dict[str, list[str]] = {"house": [], "terrace": [], "apartments": []}
    for _, item in gdf.iterrows():
        building_id = str(item.osm_id)
        first, _age_label, _prov = _gb_age_decision(bands.get(building_id), years.get(building_id, set()))
        if first is None:
            continue
        tag = str(item.building_tag).casefold()
        if tag not in by_tag:
            continue
        if _valid_storeys(item) is None:
            by_tag[tag].append(building_id)
    return by_tag


@pytest.fixture(scope="module")
def london_no_storey_by_tag() -> dict[str, list[str]]:
    return _london_no_storey_ids_by_tag()


def test_t01_no_storey_population_matches_measured_current_pool(london_no_storey_by_tag):
    # Report §2.2 measured 33 house/terrace + 14 apartments = 47, against the
    # pre-b2 age gate. b2 (FINDING 256, already shipped/uncommitted in this
    # working tree) resolves more age bands first, so more footprints now
    # reach the storey check: 36 house/terrace (35 house + 1 terrace) + 16
    # apartments = 52. +3 house/terrace over the report's 33 is 9.1%, inside
    # hard rule 6's 10% ceiling; recorded here rather than silently accepted.
    house_terrace = london_no_storey_by_tag["house"] + london_no_storey_by_tag["terrace"]
    apartments = london_no_storey_by_tag["apartments"]
    assert len(house_terrace) == 36
    assert len(apartments) == 16


def test_t01_house_and_terrace_no_storey_ids_all_resolve_via_sap_floor_dimensions(london_no_storey_by_tag):
    cert_numbers = _cert_numbers_by_osm_id()
    house_terrace = london_no_storey_by_tag["house"] + london_no_storey_by_tag["terrace"]
    resolved = [
        bid for bid in house_terrace
        if _gb_sap_floor_storeys(cert_numbers.get(bid, [])) is not None
    ]
    assert len(resolved) == len(house_terrace) == 36


def test_t01_apartment_no_storey_ids_never_resolve(london_no_storey_by_tag):
    gdf = gpd.read_file(MANIFEST)
    records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))["records"]
    rows, exclusions = _gb_rows(gdf, records)
    recovered_ids = {r["building_id"] for r in rows if r.get("storey_provenance") == "SAP_FLOOR_DIMENSIONS"}
    apartments = set(london_no_storey_by_tag["apartments"])
    assert not (apartments & recovered_ids)
    assert len(apartments) == 16
    # NOTE (T02 corrected #2, 2026-09-05): this was `== 16` under plain T01
    # (single-latest-certificate band). Under the corrected period-set
    # intersection, the age-band gate's population shifts (some previously
    # no-storey apartments are excluded earlier as period-ambiguous or
    # disjoint; others newly reach the storey gate that did not before,
    # having previously failed at the age gate under the old single-band
    # logic) -- measured net 11 apartments now reach
    # `MISSING_OBSERVED_STOREY_COUNT`. See the T02 progress-log entry.
    assert exclusions["MISSING_OBSERVED_STOREY_COUNT"] == 11


def test_t01_full_gb_rows_recovers_exactly_36_with_provenance_tag():
    gdf = gpd.read_file(MANIFEST)
    records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))["records"]
    rows, exclusions = _gb_rows(gdf, records)
    recovered = [r for r in rows if r.get("storey_provenance") == "SAP_FLOOR_DIMENSIONS"]
    # NOTE (T02 corrected #2 + T03, 2026-09-05): this was `== 36` under plain
    # T01. The corrected period-set intersection (T02) changes which
    # footprints reach the storey gate at all (some previously-resolved
    # single-band footprints are now excluded earlier as genuinely
    # conflicting across a building's several certificates; some previously
    # period-ambiguous footprints now resolve and newly reach the storey
    # gate) -- measured net 30, all `house`-tagged. See the T02 progress-log
    # entry for the gained/lost breakdown against the T01 baseline.
    assert len(recovered) == 30
    assert {r["building_tag"] for r in recovered} <= {"house", "terrace"}
    # NOTE (T02 corrected #2 + T03, 2026-09-05): this was `len(rows) == 455`
    # after T01 alone. Measured fact, recorded per hard rule 6 rather than
    # silently rewritten to match without comment: pooling every certificate's
    # band per footprint (already-approved, out of T02's own scope) both gains
    # (period-set intersection resolves real straddles the old single-band
    # logic could not) and loses (genuinely conflicting bands across a
    # building's separate flats, previously masked by "keep only the latest
    # certificate", are now correctly flagged disjoint) -- gross +71 / -78
    # against the T01 baseline of 455 (net -7), plus T03's own +3, giving 451.
    # See the plan's §8 T02 and T03 progress-log entries for the full
    # measured breakdown.
    assert len(rows) == 451
    assert exclusions["MISSING_OBSERVED_STOREY_COUNT"] == 11
    disjoint_total = sum(v for k, v in exclusions.items() if k.startswith("PERIOD_STRADDLE_DISJOINT_BANDS"))
    assert disjoint_total == 159


def test_t02_zero_bands_delegates_to_gb_age_decision_with_none():
    for years in (set(), {2019}, {2008, 2019}):
        assert _gb_age_decision_multi([], years) == _gb_age_decision(None, years)


@pytest.mark.parametrize(
    "band,years",
    [
        ("E", set()),
        ("D", set()),
        (None, {2019}),
        (None, {2008, 2019}),
        ("K", {2009}),
        ("B", {2013}),
    ],
)
def test_t02_one_known_band_is_byte_identical_to_gb_age_decision(band, years):
    bands = [] if band is None else [band, band]
    assert _gb_age_decision_multi(bands, years) == _gb_age_decision(band, years)


def test_t02_two_overlapping_synthetic_bands_resolve_to_one_period(monkeypatch):
    # Both synthetic bands' own endpoint-year periods are singletons here
    # (neither straddles a TABULA period boundary on its own), so this mainly
    # exercises that two singleton period-sets intersecting to the same value
    # resolve -- the report's real J|K case below is the genuine 2-periods-
    # per-band exercise of the intersection logic.
    monkeypatch.setitem(campaign_mod.GB_EPC_BANDS, "X1", (1965, 1975))
    monkeypatch.setitem(campaign_mod.GB_EPC_BANDS, "X2", (1968, 1980))
    result = _gb_age_decision_multi(["X1", "X2"], set())
    assert result == ("GB.04", "X1|X2", "EPC_MULTI_CERTIFICATE_BAND_INTERSECTION")


def test_t02_report_line117_worked_example_real_j_k_bands_resolve_to_gb07():
    # Report §1.3(iii) line 117's own worked example: band J touches
    # {GB.06, GB.07} and band K touches {GB.07, GB.08} -- their period-sets
    # share exactly GB.07, resolving even with zero observed years.
    assert _gb_age_decision_multi(["J", "K"], set()) == ("GB.07", "J|K", "EPC_MULTI_CERTIFICATE_BAND_INTERSECTION")


def test_t02_two_disjoint_real_bands_stay_unresolved():
    assert _gb_age_decision_multi(["C", "G"], set()) == (None, "PERIOD_STRADDLE_DISJOINT_BANDS_C|G", "")


def test_t02_two_bands_sharing_two_periods_ambiguous_then_year_narrows(monkeypatch):
    # No two of the real 12 GB_EPC_BANDS share an identical two-period set
    # (each period boundary is crossed by exactly one band), so exercising
    # the >=2-periods-remain-after-band-intersection branch needs synthetic
    # bands: X3 and X4 both touch exactly {GB.04, GB.05} (crossing the
    # 1980/1981 boundary at different points) -- ambiguous on bands alone,
    # resolved once an observed year within GB.04 narrows the intersection.
    monkeypatch.setitem(campaign_mod.GB_EPC_BANDS, "X3", (1965, 1985))
    monkeypatch.setitem(campaign_mod.GB_EPC_BANDS, "X4", (1975, 1990))
    assert _gb_age_decision_multi(["X3", "X4"], set()) == (None, "PERIOD_STRADDLE_AMBIGUOUS_X3|X4", "")
    assert _gb_age_decision_multi(["X3", "X4"], {1978}) == ("GB.04", "X3|X4", "EPC_MULTI_CERTIFICATE_BAND_INTERSECTION")


def _london_straddle_ids_pre_t02() -> list[str]:
    """The London footprints excluded as `PERIOD_STRADDLE_*` under the
    pre-T02, single-latest-certificate-band logic (`_gb_age_decision`
    directly, unmodified by T02) -- the population T02's "How to test"
    calls the 355 (measured here, on the current post-b2/T01 working tree:
    347; see T01's own note on the report's pre-b2 47 vs the live 52 for the
    same kind of drift)."""
    gdf = gpd.read_file(MANIFEST)
    cert = pd.read_csv(GB_EPC)
    cert = cert.dropna(subset=["age_band", "osm_id", "registrationDate"]).copy()
    cert["registrationDate"] = pd.to_datetime(cert["registrationDate"], errors="coerce")
    latest = cert.sort_values(
        ["osm_id", "registrationDate", "certificateNumber"], kind="stable"
    ).drop_duplicates("osm_id", keep="last")
    bands_single = latest.set_index(latest["osm_id"].astype(str))["age_band"].astype(str).to_dict()
    years: dict[str, set[int]] = {}
    side = pd.read_csv(GB_EPC_YEARS)
    for key, group in side.groupby(side["osm_id"].astype(str)):
        years[key] = {int(v) for v in group["construction_year"]}
    straddles = []
    for _, item in gdf.iterrows():
        bid = str(item.osm_id)
        first, age_label, _prov = _gb_age_decision(bands_single.get(bid), years.get(bid, set()))
        if first is None and str(age_label).startswith("PERIOD_STRADDLE_"):
            straddles.append(bid)
    return straddles


def test_t02_replay_real_straddle_population_resolves_77_of_347():
    """T02 corrected #2 "How to test": replay the real straddle population.
    Report §1.3(iii) predicts 86 resolved of 355 at the raw age-decision
    level. Measured (2026-09-05, period-set intersection): of the current
    347-strong single-band straddle population, 77 resolve -- close to the
    report's figure but not the number hard rule 6's tolerance is checked
    against (the plan's "how to test" explicitly says to measure the delta
    against London's full `prepare()` total after T01, not this raw count
    against 355 directly, since b2 already recovered some of these and the
    355/347 populations differ). See
    `test_t01_full_gb_rows_recovers_exactly_36_with_provenance_tag` and the
    T02 progress-log entry for the full-pipeline marginal-gain comparison
    (+71 measured vs +69 predicted net of b2, 2.9% over -- within tolerance)."""
    straddle_ids = _london_straddle_ids_pre_t02()
    assert len(straddle_ids) == 347
    cert = pd.read_csv(GB_EPC)
    cert = cert.dropna(subset=["age_band", "osm_id", "registrationDate"]).copy()
    bands_all = (
        cert.assign(osm_id=cert["osm_id"].astype(str))
        .groupby("osm_id")["age_band"]
        .apply(lambda s: sorted({str(v) for v in s}))
        .to_dict()
    )
    years: dict[str, set[int]] = {}
    side = pd.read_csv(GB_EPC_YEARS)
    for key, group in side.groupby(side["osm_id"].astype(str)):
        years[key] = {int(v) for v in group["construction_year"]}
    resolved = [
        bid for bid in straddle_ids
        if _gb_age_decision_multi(bands_all.get(bid, []), years.get(bid, set()))[0] is not None
    ]
    assert len(resolved) == 77


T03_NAMED_RESIDENTIAL_IDS = {
    "way/1058438116": 2, "way/1058438118": 2, "way/1058438120": 2,
    "way/554859559": 2, "way/190348379": 4, "way/204487525": 7,
}
T03_RESOLVED_IDS = {"way/1058438116", "way/1058438118"}
T03_BLOCKED_BY_T02_AGE_GATE_IDS = {"way/1058438120", "way/554859559", "way/190348379", "way/204487525"}


def test_t03_named_ids_have_the_reports_storey_counts():
    gdf = gpd.read_file(MANIFEST)
    gdf_idx = gdf.set_index(gdf["osm_id"].astype(str))
    for bid, expected_storeys in T03_NAMED_RESIDENTIAL_IDS.items():
        assert str(gdf_idx.loc[bid].building_tag).casefold() == "residential"
        assert _valid_storeys(gdf_idx.loc[bid]) == expected_storeys


def test_t03_two_resolvable_two_storey_ids_classify_th_by_adjacency():
    records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))["records"]
    gdf = gpd.read_file(MANIFEST)
    rows, _exclusions = _gb_rows(gdf, records)
    rows_by_id = {r["building_id"]: r for r in rows}
    for bid in T03_RESOLVED_IDS:
        assert rows_by_id[bid]["building_type"] == "TH"
        assert rows_by_id[bid]["levels"] == 2


def test_t03_remaining_four_named_ids_are_blocked_upstream_by_t02_not_by_type():
    """T03 REDESIGNED "How to test" names 6 ids (report §7); this repo's real
    EPC data shows 4 of them carry multiple, genuinely conflicting
    certificates once every certificate's band is pooled per footprint
    (T02's already-approved `bands_all_by_osm_id`, out of T03's scope), so
    they are excluded at the age-decision gate before ever reaching T03's
    tag dispatch -- not a defect in the storey-ladder classification itself.
    Measured (2026-09-05): only 2/6 resolve end-to-end; hard rule 6 STOP
    recorded in the T03 progress-log entry (predicted +6, measured +2 via
    the report's own named population, 66.7% short)."""
    records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))["records"]
    gdf = gpd.read_file(MANIFEST)
    rows, exclusions = _gb_rows(gdf, records)
    rows_by_id = {r["building_id"]: r for r in rows}
    for bid in T03_BLOCKED_BY_T02_AGE_GATE_IDS:
        assert bid not in rows_by_id
    cert = pd.read_csv(GB_EPC)
    cert2 = cert.dropna(subset=["age_band", "osm_id", "registrationDate"]).copy()
    bands_all = (
        cert2.assign(osm_id=cert2["osm_id"].astype(str))
        .groupby("osm_id")["age_band"]
        .apply(lambda s: sorted({str(v) for v in s}))
        .to_dict()
    )
    for bid in T03_BLOCKED_BY_T02_AGE_GATE_IDS:
        first, age_label, _prov = _gb_age_decision_multi(bands_all.get(bid, []), set())
        assert first is None
        assert str(age_label).startswith("PERIOD_STRADDLE_DISJOINT_BANDS_")


LYON_MFH_IDS = {
    "BATIMENT0000000240879980_part0",
    "BATIMENT0000000240881074_part0",
    "BATIMENT0000000240881193_part0",
}
MADRID_AB_IDS = {"way/224012143"}


@pytest.mark.parametrize(
    "dwellings,storeys,expected",
    [(13, 4, "MFH"), (14, 4, "MFH"), (13, 5, "AB"), (14, 9, "AB"), (13, 1, "MFH")],
)
def test_t04_13_14_dwelling_storey_partition(dwellings, storeys, expected):
    building_type, exclusion = derive_bdtopo_building_type(dwellings, storeys, is_attached=False)
    assert (building_type, exclusion) == (expected, None)


def _mapped_rows_by_id(district: str) -> dict[str, dict]:
    manifest = ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    records_path = ROOT / f"openubem/data/construction/tabula_archetypes_{DISTRICTS[district]['country'].lower()}.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))["records"]
    rows, _exclusions = _mapped_rows(district, gdf, records)
    return {r["building_id"]: r for r in rows}


def test_t04_real_lyon_13_14_gap_ids_resolve_exactly_as_predicted():
    rows_by_id = _mapped_rows_by_id("FR-LYO-HAUTCOEURPENTES")
    for bid in LYON_MFH_IDS:
        assert rows_by_id[bid]["building_type"] == "MFH"
        assert rows_by_id[bid]["type_provenance"] == "DERIVED_BDTOPO_TWO_SIGNAL"


def test_t04_real_madrid_13_14_gap_id_resolves_to_ab():
    rows_by_id = _mapped_rows_by_id("ES-MAD-BERRUGUETE")
    for bid in MADRID_AB_IDS:
        assert rows_by_id[bid]["building_type"] == "AB"
        assert rows_by_id[bid]["type_provenance"] == "DERIVED_BDTOPO_TWO_SIGNAL"


def test_t04_lyon_and_madrid_mapped_rows_gain_exactly_38():
    """T04 "How to test": measured against the report's predicted +38
    (3 Lyon MFH, 34 Lyon AB, 1 Madrid AB). `_mapped_rows` (the real `prepare()`
    call path, sidecar included for Madrid) gains exactly 37 for Lyon and
    exactly 1 for Madrid -- 0% disagreement from the prediction. Madrid's own
    baseline shifted again after T04 (1018 -> 1181) once T07b's Catastro
    `GetBuildingPartByParcel` fetch recovered all 163 previously-missing
    storey counts and stacked on top; the Lyon/Madrid *gain* this test pins
    (+37/+1) is unaffected, only Madrid's post-T04 total."""
    lyon = _mapped_rows_by_id("FR-LYO-HAUTCOEURPENTES")
    madrid = _mapped_rows_by_id("ES-MAD-BERRUGUETE")
    assert len(lyon) == 510
    assert len(madrid) == 1181
    lyon_gap_types = {bid: lyon[bid]["building_type"] for bid in LYON_MFH_IDS}
    assert set(lyon_gap_types.values()) == {"MFH"}
    assert madrid["way/224012143"]["building_type"] == "AB"


T05_NAMED_IDS = {
    "FR-LYO-HAUTCOEURPENTES": ["BATIMENT0000000240880367_part0"],
    "ES-MAD-BERRUGUETE": ["way/311968163", "way/333138113", "way/432405737"],
}


def _build_idf_for_named_id(district: str, building_id: str, tmp_path):
    manifest = ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    country = DISTRICTS[district]["country"]
    records_path = ROOT / f"openubem/data/construction/tabula_archetypes_{country.lower()}.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))["records"]
    rows, _exclusions = _mapped_rows(district, gdf, records)
    row = pd.Series({r["building_id"]: r for r in rows}[building_id])
    stem = hashlib.sha256(str(row.building_id).encode()).hexdigest()[:16]
    model_row = row.copy()
    model_row["building_id"] = stem
    zones, outcome = _geometry(model_row, records)
    record = next(r for r in records if r["archetype_id"] == row["archetype_id"])
    build_idf_for_building(model_row, record, zones, tmp_path / stem)
    return zones, outcome


@pytest.mark.parametrize(
    "district,building_id",
    [(d, bid) for d, ids in T05_NAMED_IDS.items() for bid in ids],
)
def test_t05_four_named_zero_raw_mismatch_ids_no_longer_raise(district, building_id, tmp_path):
    """T05 "How to test": report §4.3's 4 named ids all reach the identical
    tolerated state (raw mismatches == 0, `did_reroute` True, one residual
    near-duplicate vertex) that the old asymmetric gate discarded. Measured
    (2026-09-05): all 4/4 now build without raising, tagged
    `near_duplicate_vertex_tolerated_box` -- 0% disagreement from the
    report's predicted +4."""
    zones, _outcome = _build_idf_for_named_id(district, building_id, tmp_path)
    fallback_reasons = {z.get("fallback_reason") for z in zones if z.get("fallback_reason")}
    assert fallback_reasons == {"near_duplicate_vertex_tolerated_box"}


def test_t05_gate_widened_to_ignore_did_reroute_term():
    """Locks the exact condition change: the asymmetric `not did_reroute`
    term is gone, so a `did_reroute=True, mismatched=[]` state -- which the
    old gate discarded -- is now tolerated the same as `did_reroute=False`."""
    import inspect
    from scripts import run_eu_s2_campaign
    source = inspect.getsource(run_eu_s2_campaign)
    assert "if not mismatched:" in source
    assert "if not did_reroute and not mismatched:" not in source


T06_TIE_SECTIONS = {1287, 1266}


def _bologna_mapped_rows():
    # `prepare()` dispatches IT-BOL-GALVANI2 to `_it_rows` (ISTAT census-section
    # mapping), not the generic `_mapped_rows` (run_eu_s2_district_campaign.py:493).
    manifest = ROOT / "openubem/outputs/eu02/IT-BOL-GALVANI2/02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    records_path = ROOT / "openubem/data/construction/tabula_archetypes_it.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))["records"]
    return campaign_mod._it_rows(gdf, records)


def test_t06_tie_break_picks_the_older_key():
    e_counts_g = {"E12": 5, "E13": 5, "E14": 2}
    ties_g = [k for k, v in e_counts_g.items() if v == max(e_counts_g.values())]
    assert min(ties_g, key=lambda k: int(k[1:])) == "E12"


def test_t06_sections_1287_1266_recover_exactly_12():
    """T06 "How to test": report §6 names sections 1287/1266 as exact ties,
    owner ruling breaks toward the older cohort. Measured (2026-09-05):
    live Bologna `_mapped_rows` rerun recovers exactly 12 buildings across
    the two named sections -- 0% disagreement from the report's predicted
    +12."""
    rows, _exclusions = _bologna_mapped_rows()
    tie_section_rows = [r for r in rows if r.get("census_section") in T06_TIE_SECTIONS]
    assert len(tie_section_rows) == 12
    for r in tie_section_rows:
        assert r["construction_period_provenance"] == "IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD"


T07B_MULTI_PART_GML = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
                       xmlns:gml="http://www.opengis.net/gml/3.2"
                       xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-ext2d/2.0"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <wfs:member>
    <bu:BuildingPart gml:id="ES.SDGC.BU.0089801VK4708G.1">
      <bu:numberOfFloorsAboveGround>3</bu:numberOfFloorsAboveGround>
      <bu:numberOfFloorsBelowGround>1</bu:numberOfFloorsBelowGround>
    </bu:BuildingPart>
  </wfs:member>
  <wfs:member>
    <bu:BuildingPart gml:id="ES.SDGC.BU.0089801VK4708G.2">
      <bu:numberOfFloorsAboveGround>7</bu:numberOfFloorsAboveGround>
      <bu:numberOfFloorsBelowGround>0</bu:numberOfFloorsBelowGround>
    </bu:BuildingPart>
  </wfs:member>
  <wfs:member>
    <bu:BuildingPart gml:id="ES.SDGC.BU.0089801VK4708G.3">
      <bu:numberOfFloorsAboveGround xsi:nil="true" nilReason="unknown"/>
      <bu:numberOfFloorsBelowGround>0</bu:numberOfFloorsBelowGround>
    </bu:BuildingPart>
  </wfs:member>
  <wfs:member>
    <bu:BuildingPart gml:id="ES.SDGC.BU.0089801VK4708G.4">
      <bu:numberOfFloorsAboveGround>0</bu:numberOfFloorsAboveGround>
      <bu:numberOfFloorsBelowGround>1</bu:numberOfFloorsBelowGround>
    </bu:BuildingPart>
  </wfs:member>
</wfs:FeatureCollection>
"""

T07B_ALL_NIL_GML = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
                       xmlns:gml="http://www.opengis.net/gml/3.2"
                       xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-ext2d/2.0"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <wfs:member>
    <bu:BuildingPart gml:id="ES.SDGC.BU.9999999AA0000A.1">
      <bu:numberOfFloorsAboveGround xsi:nil="true" nilReason="unknown"/>
    </bu:BuildingPart>
  </wfs:member>
</wfs:FeatureCollection>
"""


def test_t07b_parse_catastro_building_part_picks_the_max_non_nil_value():
    """T07a's real parcel (0089801VK4708G) returned 4 `BuildingPart` features;
    the tallest occupied part (here, part 2) drives the type ladder, and a
    nil part (part 3, a garage/basement per T07's policy) must not win a max()
    against a real value nor crash the parse."""
    assert parse_catastro_building_part(T07B_MULTI_PART_GML) == 7


def test_t07b_parse_catastro_building_part_returns_none_when_every_part_is_nil():
    assert parse_catastro_building_part(T07B_ALL_NIL_GML) is None


def _t07b_manifest() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"osm_id": ["way/1", "way/2"], "levels": [4.0, 4.0]},
        geometry=[
            Polygon([(-3.0, 40.0), (-2.999, 40.0), (-2.999, 40.001), (-3.0, 40.001)]),
            Polygon([(-3.0, 41.0), (-2.999, 41.0), (-2.999, 41.001), (-3.0, 41.001)]),
        ],
        crs=4326,
    )


def test_t07b_apply_attribute_sidecar_levels_overlay_only_touches_matched_rows():
    sidecar = pd.DataFrame(
        [
            {
                "building_id": "way/1",
                "year_built": 1966,
                "n_dwellings": 18,
                "levels": 7,
                "provenance_levels": "CATASTRO_BUILDINGPART_OBSERVED",
            },
            {
                "building_id": "way/2",
                "year_built": 1970,
                "n_dwellings": 10,
                "levels": None,
                "provenance_levels": None,
            },
        ]
    )

    merged = apply_attribute_sidecar(_t07b_manifest(), sidecar)

    row1 = merged.set_index("osm_id").loc["way/1"]
    row2 = merged.set_index("osm_id").loc["way/2"]
    assert row1["levels"] == 7
    assert row1["provenance_levels"] == "CATASTRO_BUILDINGPART_OBSERVED"
    # way/2's sidecar row carries no levels value, so the manifest's own
    # pre-existing value (4.0) must survive untouched, not be blanked out.
    assert row2["levels"] == 4.0
    assert pd.isna(row2["provenance_levels"])


def test_t07b_apply_attribute_sidecar_tolerates_a_sidecar_without_levels_columns():
    sidecar = pd.DataFrame(
        [{"building_id": "way/1", "year_built": 1966, "n_dwellings": 18}]
    )

    merged = apply_attribute_sidecar(_t07b_manifest(), sidecar)

    assert merged.set_index("osm_id").loc["way/1", "levels"] == 4.0


class _T08MockSurface:
    def __init__(self, surface_type: str, obc: str):
        self.Surface_Type = surface_type
        self.Outside_Boundary_Condition = obc
        self.Construction_Name = None


class _T08MockIDF:
    def __init__(self, surfaces: list[_T08MockSurface]):
        self.idfobjects = {"BUILDINGSURFACE:DETAILED": surfaces}


def test_t08_interzone_roof_surface_gets_floor_construction():
    """FINDING 253: a ROOF surface whose Outside_Boundary_Condition is
    "Surface" (interzone-paired with a shorter neighbour's FLOOR) must get
    floor_construction, matching its partner, not roof_construction."""
    surf = _T08MockSurface("ROOF", "Surface")
    idf = _T08MockIDF([surf])

    _assign_envelope_constructions(idf, "EU_wall_Construction", "EU_roof_Construction", "EU_floor_Construction")

    assert surf.Construction_Name == "EU_floor_Construction"


def test_t08_interzone_roofceiling_surface_gets_floor_construction():
    surf = _T08MockSurface("ROOFCEILING", "surface")  # lower-case OBC, matches .strip().upper()
    idf = _T08MockIDF([surf])

    _assign_envelope_constructions(idf, "EU_wall_Construction", "EU_roof_Construction", "EU_floor_Construction")

    assert surf.Construction_Name == "EU_floor_Construction"


def test_t08_true_exterior_roof_still_gets_roof_construction():
    """A genuine exterior ROOF (Outside_Boundary_Condition == Outdoors) is
    unaffected by the FINDING 253 fix."""
    surf = _T08MockSurface("ROOF", "Outdoors")
    idf = _T08MockIDF([surf])

    _assign_envelope_constructions(idf, "EU_wall_Construction", "EU_roof_Construction", "EU_floor_Construction")

    assert surf.Construction_Name == "EU_roof_Construction"


def test_t08_wall_floor_ceiling_branches_unchanged():
    wall = _T08MockSurface("WALL", "Outdoors")
    floor = _T08MockSurface("FLOOR", "Ground")
    ceiling = _T08MockSurface("CEILING", "Surface")
    idf = _T08MockIDF([wall, floor, ceiling])

    _assign_envelope_constructions(idf, "EU_wall_Construction", "EU_roof_Construction", "EU_floor_Construction")

    assert wall.Construction_Name == "EU_wall_Construction"
    assert floor.Construction_Name == "EU_floor_Construction"
    assert ceiling.Construction_Name == "EU_floor_Construction"
