from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

import scripts.run_eu_s2_district_campaign as campaign_mod
from scripts.run_eu_s2_district_campaign import ROOT, _gb_rows, _gb_terrace_recovery_rows

RECORDS = json.loads(
    (ROOT / "openubem/data/construction/tabula_archetypes_gb.json").read_text(encoding="utf-8")
)["records"]


def _write_epc_csvs(
    tmp_path, monkeypatch, years: dict[str, int], certs: list[tuple[str, str, str]] = (),
) -> None:
    epc = tmp_path / "gb_epc_certificates.csv"
    pd.DataFrame(
        [
            {
                "osm_id": osm_id, "certificateNumber": cert_number, "age_band": age_band,
                "registrationDate": "2020-01-01",
            }
            for osm_id, cert_number, age_band in certs
        ],
        columns=["osm_id", "certificateNumber", "age_band", "registrationDate"],
    ).to_csv(epc, index=False)
    monkeypatch.setattr(campaign_mod, "GB_EPC", epc)
    epc_years = tmp_path / "gb_epc_construction_year_sidecar.csv"
    pd.DataFrame(
        {"osm_id": list(years.keys()), "construction_year": list(years.values())}
    ).to_csv(epc_years, index=False)
    monkeypatch.setattr(campaign_mod, "GB_EPC_YEARS", epc_years)


def _row(osm_id: str, tag: str, levels, geometry) -> dict:
    return {"osm_id": osm_id, "building_tag": tag, "levels": levels, "geometry": geometry}


def test_t05_age_inheritance_succeeds_with_one_consistent_prepared_neighbour(tmp_path, monkeypatch):
    _write_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1975})
    gdf = gpd.GeoDataFrame(
        [
            _row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _row("way/E1", "terrace", 3, box(1, 0, 2, 1)),
        ],
        crs="EPSG:2154",
    )
    base_rows, base_exclusions = _gb_rows(gdf, RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    assert base_exclusions["MISSING_OBSERVED_EPC_AGE_BAND"] == 1

    recovered, exclusions = _gb_terrace_recovery_rows(gdf, RECORDS, base_rows)

    assert len(recovered) == 1
    row = recovered[0]
    assert row["building_id"] == "way/E1"
    assert row["construction_period_provenance"] == "INFERRED_TERRACE_NEIGHBOUR_AGE"
    assert row["storey_provenance"] == ""
    assert sum(exclusions.values()) == 0


def test_t05_age_inheritance_refuses_when_prepared_neighbours_span_two_periods(tmp_path, monkeypatch):
    _write_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1930, "way/P2": 2015})
    gdf = gpd.GeoDataFrame(
        [
            _row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _row("way/P2", "terrace", 3, box(2, 0, 3, 1)),
            _row("way/E1", "terrace", 3, box(0.5, 1, 2.5, 2)),
        ],
        crs="EPSG:2154",
    )
    base_rows, _base_exclusions = _gb_rows(gdf, RECORDS)
    assert {r["building_id"] for r in base_rows} == {"way/P1", "way/P2"}

    recovered, exclusions = _gb_terrace_recovery_rows(gdf, RECORDS, base_rows)

    assert recovered == []
    assert exclusions["MISSING_OBSERVED_EPC_AGE_BAND_NEIGHBOURS_DISAGREE"] == 1


def test_t05_age_inheritance_refuses_with_no_prepared_neighbour(tmp_path, monkeypatch):
    _write_epc_csvs(tmp_path, monkeypatch, {})
    gdf = gpd.GeoDataFrame(
        [_row("way/E1", "terrace", 3, box(50, 50, 51, 51))],
        crs="EPSG:2154",
    )
    base_rows, _base_exclusions = _gb_rows(gdf, RECORDS)
    assert base_rows == []

    recovered, exclusions = _gb_terrace_recovery_rows(gdf, RECORDS, base_rows)

    assert recovered == []
    assert exclusions["MISSING_OBSERVED_EPC_AGE_BAND_NO_PREPARED_NEIGHBOUR"] == 1


def test_t05_storey_inheritance_succeeds_with_one_consistent_prepared_neighbour(tmp_path, monkeypatch):
    _write_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1975, "way/E1": 1975})
    gdf = gpd.GeoDataFrame(
        [
            _row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _row("way/E1", "terrace", float("nan"), box(1, 0, 2, 1)),
        ],
        crs="EPSG:2154",
    )
    base_rows, base_exclusions = _gb_rows(gdf, RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    assert base_exclusions["MISSING_OBSERVED_STOREY_COUNT"] == 1

    recovered, exclusions = _gb_terrace_recovery_rows(gdf, RECORDS, base_rows)

    assert len(recovered) == 1
    row = recovered[0]
    assert row["building_id"] == "way/E1"
    assert row["storey_provenance"] == "INFERRED_TERRACE_NEIGHBOUR_STOREYS"
    assert row["levels"] == 3
    assert sum(exclusions.values()) == 0


def test_t05b_straddle_admitted_when_neighbour_period_inside_straddle_set(tmp_path, monkeypatch):
    _write_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1955}, certs=[("way/E1", "cert-1", "D")])
    gdf = gpd.GeoDataFrame(
        [
            _row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _row("way/E1", "terrace", 3, box(1, 0, 2, 1)),
        ],
        crs="EPSG:2154",
    )
    base_rows, base_exclusions = _gb_rows(gdf, RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    assert base_exclusions["PERIOD_STRADDLE_D_GB.03_GB.04"] == 1

    recovered, exclusions = _gb_terrace_recovery_rows(gdf, RECORDS, base_rows)

    assert len(recovered) == 1
    row = recovered[0]
    assert row["building_id"] == "way/E1"
    assert row["construction_period_provenance"] == "INFERRED_TERRACE_NEIGHBOUR_PERIOD_WITHIN_STRADDLE"
    assert sum(exclusions.values()) == 0


def test_t05b_straddle_refused_when_neighbour_period_outside_straddle_set(tmp_path, monkeypatch):
    _write_epc_csvs(tmp_path, monkeypatch, {"way/P1": 1930}, certs=[("way/E1", "cert-1", "D")])
    gdf = gpd.GeoDataFrame(
        [
            _row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _row("way/E1", "terrace", 3, box(1, 0, 2, 1)),
        ],
        crs="EPSG:2154",
    )
    base_rows, base_exclusions = _gb_rows(gdf, RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    assert base_exclusions["PERIOD_STRADDLE_D_GB.03_GB.04"] == 1

    recovered, exclusions = _gb_terrace_recovery_rows(gdf, RECORDS, base_rows)

    assert recovered == []
    assert exclusions["PERIOD_STRADDLE_D_GB.03_GB.04_NEIGHBOUR_OUTSIDE_STRADDLE"] == 1


def test_t05b_disjoint_bands_row_is_never_admitted_by_this_path(tmp_path, monkeypatch):
    _write_epc_csvs(
        tmp_path, monkeypatch, {"way/P1": 1975},
        certs=[("way/E1", "cert-1", "C"), ("way/E1", "cert-2", "G")],
    )
    gdf = gpd.GeoDataFrame(
        [
            _row("way/P1", "terrace", 3, box(0, 0, 1, 1)),
            _row("way/E1", "terrace", 3, box(1, 0, 2, 1)),
        ],
        crs="EPSG:2154",
    )
    base_rows, base_exclusions = _gb_rows(gdf, RECORDS)
    assert [r["building_id"] for r in base_rows] == ["way/P1"]
    assert base_exclusions["PERIOD_STRADDLE_DISJOINT_BANDS_C|G"] == 1

    recovered, exclusions = _gb_terrace_recovery_rows(gdf, RECORDS, base_rows)

    assert recovered == []
    assert sum(exclusions.values()) == 0
