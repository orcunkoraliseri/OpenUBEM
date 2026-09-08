from __future__ import annotations

from collections import Counter

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

import openubem.geometry.european_residential as european_residential
import scripts.run_eu_s2_district_campaign as campaign_mod
from openubem.geometry.european_nocore import MAX_FLAT_ASPECT, cut_storey_nocore
from openubem.geometry.european_residential import (
    EuropeanBuildingDwellingLayout,
    generate_european_nocore_storey_layout,
)
from scripts.run_eu_s2_district_campaign import DISTRICTS, ROOT, _ExclusionCounter, _geometry

# ---------------------------------------------------------------------------
# T01 -- per-storey refusal reason threaded through `_geometry`, and the new
# per-building `_ExclusionCounter` behind `excluded_buildings.csv`.
# ---------------------------------------------------------------------------


def test_t01_geometry_threads_layout_reason_into_manifest_fallback_reason(monkeypatch):
    layout = EuropeanBuildingDwellingLayout(
        storey_groups=(), dwelling_layout_emitted=False,
        fallback_reason="NOCORE_CHECK_FAILED_C11",
        observed_max_per_floor=1, scheme_by_storey=(), fallback_reason_by_storey=(),
    )
    monkeypatch.setattr(campaign_mod, "generate_european_building_dwelling_layout", lambda *a, **k: layout)
    row = pd.Series({
        "building_id": "test/synthetic-1", "geometry": box(0, 0, 10, 10),
        "levels": 3, "observed_dwellings": 4, "building_type": "AB", "archetype_id": "ES.AB.01.Gen",
    })
    zones, outcome = _geometry(row, [])
    assert outcome == "FALLBACK_PENDING_LAYOUT"
    assert outcome.layout_reason == "NOCORE_CHECK_FAILED_C11"
    fallback_reason = (
        next((z["fallback_reason"] for z in zones if z.get("fallback_reason")), "")
        or (outcome.layout_reason or "")
    )
    assert fallback_reason == "NOCORE_CHECK_FAILED_C11"


def test_t01_excluded_buildings_csv_matches_histogram(tmp_path):
    counter = _ExclusionCounter()
    counter.log("way/900", "base_mapping", "MISSING_OBSERVED_STOREY_COUNT")
    counter.log("way/901", "idf_build", "IDF_ASSEMBLY_FAILED_RuntimeError", detail="boom")
    out_csv = tmp_path / "excluded_buildings.csv"
    pd.DataFrame(counter.records, columns=["building_id", "stage", "blocker", "detail"]).to_csv(out_csv, index=False)
    written = pd.read_csv(out_csv, keep_default_na=False)
    assert len(written) == 2
    assert dict(Counter(written["blocker"])) == dict(counter)
    row = written[written["building_id"] == "way/900"].iloc[0]
    assert row["stage"] == "base_mapping" and row["blocker"] == "MISSING_OBSERVED_STOREY_COUNT" and row["detail"] == ""
    row2 = written[written["building_id"] == "way/901"].iloc[0]
    assert row2["stage"] == "idf_build" and row2["detail"] == "boom"


# ---------------------------------------------------------------------------
# T02 -- D-EU-111 best-effort tier.
# ---------------------------------------------------------------------------

_C11_ONLY_FOOTPRINT = box(0, 0, 60, 5)
_C11_ONLY_DWELLING_COUNT = 3


def test_t02_case1_best_effort_emits_with_conserved_area():
    layout = generate_european_nocore_storey_layout(_C11_ONLY_FOOTPRINT, dwelling_count=_C11_ONLY_DWELLING_COUNT)
    assert layout.dwelling_layout_emitted is True
    assert layout.fallback_reason == "NOCORE_BEST_EFFORT_C11"
    assert len(layout.dwelling_polygons) == _C11_ONLY_DWELLING_COUNT
    total_area = sum(p.area for p in layout.dwelling_polygons)
    assert abs(total_area - _C11_ONLY_FOOTPRINT.area) / _C11_ONLY_FOOTPRINT.area <= 0.0001
    assert layout.partition_audit is not None


def test_t02_case2_hard_check_failure_still_refuses(monkeypatch):
    real_plate, real_live, real_checks, _verdict = cut_storey_nocore(_C11_ONLY_FOOTPRINT, _C11_ONLY_DWELLING_COUNT)
    fake_checks = {k: dict(v) for k, v in real_checks.items()}
    fake_checks["C5"]["pass"] = False

    def fake_cut(footprint, dwelling_count):
        return real_plate, real_live, fake_checks, "FAIL"

    monkeypatch.setattr(european_residential, "cut_storey_nocore", fake_cut)
    layout = generate_european_nocore_storey_layout(_C11_ONLY_FOOTPRINT, dwelling_count=_C11_ONLY_DWELLING_COUNT)
    assert layout.dwelling_layout_emitted is False
    assert "C5" in layout.fallback_reason


def test_t02_case3_max_flat_aspect_unchanged_and_c11_fails():
    assert MAX_FLAT_ASPECT == 2.5
    _plate, _live, checks, _verdict = cut_storey_nocore(_C11_ONLY_FOOTPRINT, _C11_ONLY_DWELLING_COUNT)
    assert checks["C11"]["pass"] is False


def test_t02_case4_geometry_outcome_token_is_best_effort():
    row = pd.Series({
        "building_id": "test/synthetic-2", "geometry": _C11_ONLY_FOOTPRINT,
        "levels": 1, "observed_dwellings": _C11_ONLY_DWELLING_COUNT,
        "building_type": "AB", "archetype_id": "ES.AB.01.Gen",
    })
    zones, outcome = _geometry(row, [])
    assert outcome == "DWELLING_LAYOUT_EMITTED_BEST_EFFORT"
    assert outcome.layout_reason == "NOCORE_BEST_EFFORT_C11"


# ---------------------------------------------------------------------------
# T02 dry measurement: the 289 rule-refused ids, layout function only, no IDF,
# no EnergyPlus (T02 "How to test"). ES/FR/GB replay the real, offline
# `_gb_rows`/`_mapped_rows` base mapping; IT (Bologna) cannot -- its base
# mapping makes two live HTTP calls -- so it is approximated from the
# already-cached `_delta_2026-09-07` archetype/period assignment plus a
# storey count derived from that tree's own recorded floor area, both local.
# ---------------------------------------------------------------------------

_DEBUG_CSV = ROOT / "docs/docs_ACTIVE/europeanLocations/debugs/undivided_buildings_all_districts_2026-09-08.csv"
_DISTRICT_LABELS = {
    "Madrid": "ES-MAD-BERRUGUETE", "Lyon": "FR-LYO-HAUTCOEURPENTES",
    "London": "GB-LDN-STDUNSTANS", "Bologna": "IT-BOL-GALVANI2",
}


def _dry_run_base_rows(district: str, gdf: gpd.GeoDataFrame, records: list[dict]) -> dict[str, dict]:
    if district == "GB-LDN-STDUNSTANS":
        rows, _ = campaign_mod._gb_rows(gdf, records)
        recovered, _ = campaign_mod._gb_terrace_recovery_rows(gdf, records, rows)
        rows = rows + recovered
    else:
        rows, _ = campaign_mod._mapped_rows(district, gdf, records)
    return {str(r["building_id"]): r for r in rows}


def _dry_run_bologna_rows(ids: set[str], gdf: gpd.GeoDataFrame) -> dict[str, dict]:
    delta = pd.read_csv(
        ROOT / "openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_delta_2026-09-07/prepared_buildings.csv",
        dtype={"building_id": str},
    )
    delta_by_id = {r.building_id: r for r in delta.itertuples()}
    geom_by_id = {str(v): g for v, g in zip(gdf["osm_id"].astype(str), gdf.geometry)}
    by_id: dict[str, dict] = {}
    for bid in ids:
        drow = delta_by_id.get(bid)
        footprint = geom_by_id.get(bid)
        if drow is None or footprint is None or footprint.area <= 0:
            continue
        n_storey = max(1, round(drow.floor_area_m2 / footprint.area))
        by_id[bid] = {
            "building_id": bid, "geometry": footprint, "levels": n_storey,
            "observed_dwellings": None, "building_type": drow.building_type,
            "archetype_id": drow.archetype_id, "age_band": drow.age_band,
        }
    return by_id


def _dry_run_building_layout(row: pd.Series, records: list[dict]):
    from openubem.geometry.european_residential import (
        allocate_european_dwellings,
        generate_european_building_dwelling_layout,
    )

    footprint = row.geometry
    n_storey = campaign_mod._valid_storeys(row)
    if n_storey is None:
        raise ValueError("MISSING_OBSERVED_STOREY_COUNT")
    dwellings = row.get("observed_dwellings")
    is_observed = pd.notna(dwellings) and float(dwellings).is_integer() and float(dwellings) > 0
    if is_observed:
        dwellings_val = int(dwellings)
    else:
        btype = row["building_type"]
        if btype in ("SFH", "TH"):
            dwellings_val = 1
        else:
            rec = next((x for x in records if x["archetype_id"] == row["archetype_id"]), None)
            n_apt = rec.get("n_apartment") if rec else 10.0
            dwellings_val = max(1, round(float(n_apt))) if pd.notna(n_apt) else 10
    allocation = allocate_european_dwellings(
        archetype_id=row["archetype_id"], building_type=row["building_type"],
        n_apartment=dwellings_val, n_storey=n_storey, plate_area_m2=float(footprint.area),
    )
    return generate_european_building_dwelling_layout(footprint, floor_allocations=allocation.floor_allocations)


def _measure_best_effort_dry_run() -> dict[str, dict]:
    debug = pd.read_csv(_DEBUG_CSV, dtype={"building_id": str})
    rule_refused = debug[debug["defect_class"].str.startswith("undivided_rule_")]
    results: dict[str, dict] = {}
    for label, district in _DISTRICT_LABELS.items():
        ids = set(rule_refused.loc[rule_refused["district"] == label, "building_id"])
        cfg = DISTRICTS[district]
        records = campaign_mod._records(cfg["country"])
        gdf = gpd.read_file(ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg")
        by_id = (
            _dry_run_bologna_rows(ids, gdf) if district == "IT-BOL-GALVANI2"
            else _dry_run_base_rows(district, gdf, records)
        )
        emitted_best_effort = 0
        still_refused = 0
        not_found = 0
        audit_passed = 0
        audit_failed = 0
        reasons: Counter = Counter()
        for bid in sorted(ids):
            row_data = by_id.get(bid)
            if row_data is None:
                not_found += 1
                reasons["NOT_FOUND_IN_BASE_ROWS"] += 1
                continue
            row = pd.Series(row_data)
            try:
                _zones, outcome = _geometry(row, records)
            except ValueError as exc:
                still_refused += 1
                reasons[str(exc)] += 1
                continue
            if outcome.startswith("DWELLING_LAYOUT_EMITTED_BEST_EFFORT"):
                emitted_best_effort += 1
                # 4J ask (director amendment 13:05): what the pre-amendment
                # `passed`-gated branch would have thrown away, report-only.
                building_layout = _dry_run_building_layout(row, records)
                if all(
                    group.layout.partition_audit is not None and group.layout.partition_audit.passed
                    for group in building_layout.storey_groups
                    if group.layout.fallback_reason and group.layout.fallback_reason.startswith("NOCORE_BEST_EFFORT_")
                ):
                    audit_passed += 1
                else:
                    audit_failed += 1
            else:
                still_refused += 1
                reasons[outcome.layout_reason or str(outcome)] += 1
        results[district] = {
            "n": len(ids), "emitted_best_effort": emitted_best_effort,
            "still_refused": still_refused, "not_found": not_found,
            "audit_passed": audit_passed, "audit_failed": audit_failed,
            "reasons": dict(sorted(reasons.items())),
        }
    return results


def test_t02_dry_run_best_effort_measurement():
    results = _measure_best_effort_dry_run()
    for district, row in results.items():
        assert row["emitted_best_effort"] + row["still_refused"] + row["not_found"] == row["n"]
        assert row["audit_passed"] + row["audit_failed"] == row["emitted_best_effort"]
        print(
            f"{district}: n={row['n']} emitted_best_effort={row['emitted_best_effort']} "
            f"(audit_passed={row['audit_passed']} audit_failed={row['audit_failed']}) "
            f"still_refused={row['still_refused']} not_found={row['not_found']} reasons={row['reasons']}"
        )


# ---------------------------------------------------------------------------
# T04 -- D-EU-112 neighbour imputation for the never-simulated.
# ---------------------------------------------------------------------------

_ORACLE_CSV = ROOT / "docs/docs_ACTIVE/europeanLocations/debugs/never_simulated_buildings_all_districts_2026-09-08.csv"


def _write_gb_epc_csvs(tmp_path, monkeypatch, years: dict, certs: list = ()) -> None:
    epc = tmp_path / "gb_epc_certificates.csv"
    pd.DataFrame(
        [
            {"osm_id": osm_id, "certificateNumber": cert_number, "age_band": age_band, "registrationDate": "2020-01-01"}
            for osm_id, cert_number, age_band in certs
        ],
        columns=["osm_id", "certificateNumber", "age_band", "registrationDate"],
    ).to_csv(epc, index=False)
    monkeypatch.setattr(campaign_mod, "GB_EPC", epc)
    epc_years = tmp_path / "gb_epc_construction_year_sidecar.csv"
    pd.DataFrame({"osm_id": list(years.keys()), "construction_year": list(years.values())}).to_csv(epc_years, index=False)
    monkeypatch.setattr(campaign_mod, "GB_EPC_YEARS", epc_years)


def _gb_row(osm_id: str, tag: str, levels, geometry) -> dict:
    return {"osm_id": osm_id, "building_tag": tag, "levels": levels, "geometry": geometry}


_GB_RECORDS = campaign_mod._records("GB")


def test_t04_case1_touching_neighbours_agree_rung1(tmp_path, monkeypatch):
    _write_gb_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1975})
    gdf = gpd.GeoDataFrame(
        [_gb_row("way/P1", "terrace", 3, box(0, 0, 1, 1)), _gb_row("way/E1", "terrace", 3, box(1, 0, 2, 1))],
        crs="EPSG:2154",
    )
    base_rows, base_exclusions = campaign_mod._gb_rows(gdf, _GB_RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    recovered, exclusions = campaign_mod.impute_from_neighbours(gdf, base_rows, _GB_RECORDS, "GB-LDN-STDUNSTANS")
    assert [r["building_id"] for r in recovered] == ["way/E1"]
    assert recovered[0]["imputation_provenance"] == "IMPUTED_NEIGHBOUR_TOUCHING"
    assert recovered[0]["age_band"] == "GB.04"


def test_t04_case2_nearest_within_30m_rung2(tmp_path, monkeypatch):
    _write_gb_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1975})
    gdf = gpd.GeoDataFrame(
        [_gb_row("way/P1", "terrace", 3, box(0, 0, 1, 1)), _gb_row("way/E1", "terrace", 3, box(20, 0, 21, 1))],
        crs="EPSG:2154",
    )
    base_rows, _ = campaign_mod._gb_rows(gdf, _GB_RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    recovered, exclusions = campaign_mod.impute_from_neighbours(gdf, base_rows, _GB_RECORDS, "GB-LDN-STDUNSTANS")
    assert [r["building_id"] for r in recovered] == ["way/E1"]
    assert recovered[0]["imputation_provenance"].startswith("IMPUTED_NEIGHBOUR_NEAREST_")
    assert recovered[0]["age_band"] == "GB.04"


def test_t04_case3_isolated_rung3_district_mode(tmp_path, monkeypatch):
    _write_gb_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1975, "way/P2": 1978})
    gdf = gpd.GeoDataFrame(
        [
            _gb_row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _gb_row("way/P2", "terrace", 3, box(1, 0, 2, 1)),
            _gb_row("way/E1", "terrace", 3, box(1000, 1000, 1001, 1001)),
        ],
        crs="EPSG:2154",
    )
    base_rows, _ = campaign_mod._gb_rows(gdf, _GB_RECORDS)
    assert sorted(r["building_id"] for r in base_rows) == ["way/P1", "way/P2"]
    recovered, exclusions = campaign_mod.impute_from_neighbours(gdf, base_rows, _GB_RECORDS, "GB-LDN-STDUNSTANS")
    assert [r["building_id"] for r in recovered] == ["way/E1"]
    assert recovered[0]["imputation_provenance"] == "IMPUTED_DISTRICT_MODE"
    assert recovered[0]["age_band"] == "GB.04"


def test_t04_case4_gb_straddle_neighbour_outside_set_falls_to_older_band(tmp_path, monkeypatch):
    _write_gb_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1970}, certs=[("way/E1", "CERT1", "C")])
    gdf = gpd.GeoDataFrame(
        [
            _gb_row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _gb_row("way/E1", "terrace", 2, box(1000, 1000, 1001, 1001)),
        ],
        crs="EPSG:2154",
    )
    base_rows, base_exclusions = campaign_mod._gb_rows(gdf, _GB_RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    assert any(k.startswith("PERIOD_STRADDLE_C_GB.02_GB.03") for k in base_exclusions)
    recovered, exclusions = campaign_mod.impute_from_neighbours(gdf, base_rows, _GB_RECORDS, "GB-LDN-STDUNSTANS")
    assert [r["building_id"] for r in recovered] == ["way/E1"]
    assert recovered[0]["imputation_provenance"] == "IMPUTED_NEIGHBOUR_STRADDLE_OLDER_BAND"
    assert recovered[0]["age_band"] == "GB.02"


def test_t04_gb_straddle_containment_helper_unit():
    assert campaign_mod._gb_straddle_containment("GB.02", "IMPUTED_DISTRICT_MODE", ("GB.02", "GB.03")) == ("GB.02", "IMPUTED_DISTRICT_MODE")
    assert campaign_mod._gb_straddle_containment("GB.05", "IMPUTED_DISTRICT_MODE", ("GB.02", "GB.03")) == ("GB.02", "IMPUTED_NEIGHBOUR_STRADDLE_OLDER_BAND")
    assert campaign_mod._gb_straddle_containment(None, "", ("GB.02", "GB.03")) == (None, "")
    assert campaign_mod._gb_straddle_containment("GB.05", "IMPUTED_DISTRICT_MODE", None) == ("GB.05", "IMPUTED_DISTRICT_MODE")


# ---------------------------------------------------------------------------
# T04 oracle check: the 585-row director-built CSV. ES/FR/GB replay the real,
# offline `_mapped_rows`/`_gb_rows`; IT (Bologna) cannot call the live-HTTP
# `_it_rows` inside a test (CLAUDE.md: no live-network integration tests), so
# its base rows are approximated the same way the T02 dry-run measurement
# already approximates Bologna: from the cached `_delta_2026-09-07`
# archetype/period assignment, with `year_built` re-derived as the first year
# of that row's own TABULA period (`_TABULA_PERIODS`, read-only) -- any year
# in that bucket selects the identical archetype.
# ---------------------------------------------------------------------------


def _bologna_base_rows_offline(gdf: gpd.GeoDataFrame) -> list[dict]:
    from openubem.semantic.construction_sets import _TABULA_PERIODS

    period_year = {code: (first if first > 0 else min(last, 1899)) for first, last, code in _TABULA_PERIODS["IT"]}
    delta = pd.read_csv(
        ROOT / "openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_delta_2026-09-07/prepared_buildings.csv",
        dtype={"building_id": str},
    )
    geom_by_id = {str(v): g for v, g in zip(gdf["osm_id"].astype(str), gdf.geometry)}
    rows = []
    for r in delta.itertuples():
        bid = str(r.building_id)
        geom = geom_by_id.get(bid)
        if geom is None or not isinstance(r.age_band, str) or r.age_band not in period_year:
            continue
        rows.append({
            "building_id": bid, "osm_id": bid, "geometry": geom,
            "building_type": r.building_type, "archetype_id": r.archetype_id,
            "age_band": r.age_band, "year_built": period_year[r.age_band],
        })
    return rows


def _district_base_rows(district: str, gdf: gpd.GeoDataFrame, records: list) -> list[dict]:
    if district == "GB-LDN-STDUNSTANS":
        rows, _ = campaign_mod._gb_rows(gdf, records)
        return rows
    if district == "IT-BOL-GALVANI2":
        return _bologna_base_rows_offline(gdf)
    rows, _ = campaign_mod._mapped_rows(district, gdf, records)
    return rows


def _run_impute_all_districts() -> dict[str, tuple[list[dict], Counter, list[dict]]]:
    results = {}
    for district in DISTRICTS:
        cfg = DISTRICTS[district]
        records = campaign_mod._records(cfg["country"])
        gdf = gpd.read_file(ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg")
        base_rows = _district_base_rows(district, gdf, records)
        recovered, exclusions = campaign_mod.impute_from_neighbours(gdf, base_rows, records, district)
        results[district] = (recovered, exclusions, base_rows)
    return results


def test_t04_oracle_agreement_touching_and_nearest():
    oracle = pd.read_csv(_ORACLE_CSV, dtype={"building_id": str})
    check_rows = oracle[
        (oracle["imputation_source"] == "touching_prepared_neighbours_agree")
        | (oracle["imputation_source"].str.startswith("nearest_prepared_neighbour_", na=False))
    ]
    assert len(check_rows) > 0
    all_results = _run_impute_all_districts()
    matches = 0
    disagreements: list[tuple] = []
    for district, (recovered, _exclusions, _base_rows) in all_results.items():
        recovered_by_id = {str(r["building_id"]): r for r in recovered}
        sub = check_rows[check_rows["district"] == district]
        for row in sub.itertuples():
            bid = row.building_id
            got = recovered_by_id.get(bid)
            expected = row.proposed_imputed_age_band
            if got is None:
                disagreements.append((district, bid, expected, "NOT_RECOVERED"))
                continue
            actual = got.get("age_band")
            if actual == expected:
                matches += 1
            else:
                disagreements.append((district, bid, expected, actual))
    print(f"T04 oracle: {matches} matches, {len(disagreements)} disagreements of {len(check_rows)} checked")
    for item in disagreements:
        print("  disagreement:", item)
    assert matches + len(disagreements) == len(check_rows)


def test_t04_recovered_vs_585():
    oracle = pd.read_csv(_ORACLE_CSV, dtype={"building_id": str})
    assert len(oracle) == 585
    all_results = _run_impute_all_districts()
    total_585 = 0
    total_recovered = 0
    for district, (recovered, exclusions, base_rows) in all_results.items():
        ids_585 = set(oracle.loc[oracle["district"] == district, "building_id"])
        recovered_ids = {str(r["building_id"]) for r in recovered}
        base_ids = {str(r["building_id"]) for r in base_rows}
        recovered_of_585 = len(ids_585 & recovered_ids)
        already_prepared_of_585 = len(ids_585 & base_ids)
        residual_585 = ids_585 - recovered_ids - base_ids
        total_585 += len(ids_585)
        total_recovered += recovered_of_585
        print(
            f"T04 recovered-vs-585 {district}: n_585={len(ids_585)} recovered={recovered_of_585} "
            f"already_in_base={already_prepared_of_585} residual={len(residual_585)} "
            f"residual_blockers={dict(sorted(exclusions.items()))}"
        )
    print(f"T04 recovered-vs-585 fleet: {total_recovered} of {total_585}")
    assert total_585 == 585


def test_t04_impute_from_neighbours_accounts_for_every_candidate():
    """Dependency 5: every candidate `impute_from_neighbours` is handed (every
    `gdf` row the base mapping excluded) must end up either recovered or
    logged in the returned exclusions -- never silently dropped, or
    `excluded_buildings.csv` (T01) stops correctly recording what remains
    excluded and why. Regression guard for the gap `_gb_impute_rows` measured
    on London: a candidate whose own period *was* independently resolvable
    but only through the multi-certificate `PERIOD_STRADDLE_DISJOINT_BANDS_*`
    / `_AMBIGUOUS_*` shape (`_gb_age_decision_multi`) fell through both of
    `_gb_terrace_recovery_rows`'s loops (its `_gb_parse_straddle_periods`
    regex only recognises the single-certificate `PERIOD_STRADDLE_<band>_..`
    shape) without ever being logged.
    """
    for district in DISTRICTS:
        cfg = DISTRICTS[district]
        records = campaign_mod._records(cfg["country"])
        gdf = gpd.read_file(ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg")
        base_rows = _district_base_rows(district, gdf, records)
        base_ids = {str(r["building_id"]) for r in base_rows}
        candidate_ids = set(gdf["osm_id"].astype(str)) - base_ids
        recovered, exclusions = campaign_mod.impute_from_neighbours(gdf, base_rows, records, district)
        recovered_ids = {str(r["building_id"]) for r in recovered}
        excluded_ids = {rec["building_id"] for rec in exclusions.records}
        assert not (recovered_ids & excluded_ids), f"{district}: recovered and excluded overlap"
        missing = candidate_ids - recovered_ids - excluded_ids
        assert not missing, f"{district}: {len(missing)} candidates neither recovered nor logged: {sorted(missing)[:5]}"


# ---------------------------------------------------------------------------
# T05 -- one re-emission, four districts in parallel, delta by hash. Small
# checker (dependency decision 5 / T05 "How to test") that reads the
# `_delta_2026-09-07` baseline and the `_recut_2026-09-08` re-emission and
# prints the six gates G1-G6, each as "N of M", per district.
# ---------------------------------------------------------------------------

_STOCK_2026_09_08 = {
    "ES-MAD-BERRUGUETE": 1_194,
    "FR-LYO-HAUTCOEURPENTES": 530,
    "GB-LDN-STDUNSTANS": 1_242,
    "IT-BOL-GALVANI2": 1_220,
}

# T02 progress-log entry (2026-09-08), dry-run measurement over the 289
# rule-refused ids, `emitted_best_effort` column -- the gain G2 checks for.
_T02_DRY_RUN_GAIN = {
    "ES-MAD-BERRUGUETE": 52,
    "FR-LYO-HAUTCOEURPENTES": 12,
    "GB-LDN-STDUNSTANS": 5,
    "IT-BOL-GALVANI2": 135,
}

_DIVIDED_TOKENS = {"DWELLING_LAYOUT_EMITTED", "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT"}


def _t05_recut_gates(district: str) -> list[str]:
    baseline_dir = campaign_mod.EVIDENCE / f"{district}_delta_2026-09-07"
    recut_dir = campaign_mod.EVIDENCE / f"{district}_recut_2026-09-08"
    baseline = pd.read_csv(
        baseline_dir / "prepared_buildings.csv", dtype={"building_id": str}, keep_default_na=False
    )
    recut = pd.read_csv(
        recut_dir / "prepared_buildings.csv", dtype={"building_id": str}, keep_default_na=False
    )
    simulate = pd.read_csv(recut_dir / "recut_simulate_list.csv", dtype={"building_id": str})
    fleet_lines = [l for l in (recut_dir / "fleet.lst").read_text(encoding="utf-8").splitlines() if l]

    baseline_by_id = baseline.set_index("building_id")
    recut_by_id = recut.set_index("building_id")

    baseline_divided = baseline[baseline["geometry_outcome"].isin(_DIVIDED_TOKENS)]
    g1_m = len(baseline_divided)
    g1_n = 0
    for bid, row in baseline_divided.set_index("building_id").iterrows():
        if bid in recut_by_id.index:
            rrow = recut_by_id.loc[bid]
            if isinstance(rrow, pd.DataFrame):
                rrow = rrow.iloc[0]
            if rrow["geometry_outcome"] == row["geometry_outcome"]:
                g1_n += 1
    lines = [f"G1 regression ({district}): {g1_n} of {g1_m}"]

    recut_divided_n = int(recut["geometry_outcome"].str.startswith("DWELLING_LAYOUT_EMITTED").sum())
    g2_m = g1_m + _T02_DRY_RUN_GAIN[district]
    lines.append(
        f"G2 divided count ({district}): {recut_divided_n} of {g2_m} expected minimum "
        f"({'PASS' if recut_divided_n >= g2_m else 'FAIL'})"
    )

    new_only = recut[~recut["building_id"].isin(baseline_by_id.index)]
    g3_m = len(new_only)
    g3_n = int((new_only["imputation_provenance"].astype(str).str.len() > 0).sum())
    lines.append(f"G3 imputed rows ({district}): {g3_n} of {g3_m}")

    fallback_rows = recut[recut["geometry_outcome"].str.startswith("FALLBACK_PENDING_LAYOUT")]
    g4_m = len(fallback_rows)
    g4_n = int((fallback_rows["fallback_reason"].astype(str).str.len() > 0).sum())
    lines.append(f"G4 side-car reason coverage ({district}): {g4_n} of {g4_m}")

    idf_dir = recut_dir / "idfs"
    staged = sum(1 for stem in fleet_lines if (idf_dir / f"{stem}.idf").exists())
    g5_equal = len(fleet_lines) == len(simulate) == staged
    stock = _STOCK_2026_09_08[district]
    lines.append(
        f"G5 fleet/simulate/staged ({district}): fleet.lst={len(fleet_lines)}, "
        f"recut_simulate_list={len(simulate)}, idfs_staged={staged} "
        f"({'equal' if g5_equal else 'MISMATCH'}); population_prepared {len(recut)} of {stock}"
    )

    simulate_ids = set(simulate["building_id"].astype(str))
    unchanged = recut[
        (~recut["building_id"].isin(simulate_ids)) & recut["building_id"].isin(baseline_by_id.index)
    ]
    g6_m = len(unchanged)
    g6_n = 0
    for _, row in unchanged.iterrows():
        brow = baseline_by_id.loc[row["building_id"]]
        if isinstance(brow, pd.DataFrame):
            brow = brow.iloc[0]
        if brow["conditioned_floor_area_m2"] == row["conditioned_floor_area_m2"]:
            g6_n += 1
    lines.append(f"G6 unchanged-hash area byte-identical ({district}): {g6_n} of {g6_m}")

    return lines


@pytest.mark.parametrize("district", list(DISTRICTS))
def test_t05_recut_gates(district):
    recut_dir = campaign_mod.EVIDENCE / f"{district}_recut_2026-09-08"
    if not (recut_dir / "prepared_buildings.csv").exists():
        pytest.skip(f"{district}_recut_2026-09-08 not prepared yet")
    lines = _t05_recut_gates(district)
    assert len(lines) == 6
    for line in lines:
        print(line)
