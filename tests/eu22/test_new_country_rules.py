import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from openubem.idf.european_windows import COUNTRY_FILES
from openubem.semantic import new_country_rules as ncr
from openubem.semantic.construction_sets import _TABULA_PERIODS, tabula_period
from openubem.semantic.european_archetype_mapping import EU02_SITE_COUNTRY, map_observed_building_to_tabula
from scripts import run_eu_s2_district_campaign as campaign

ROOT = Path(__file__).resolve().parents[2]
AT_RECORDS = json.loads((ROOT / "openubem/data/construction/tabula_archetypes_at.json").read_text(encoding="utf-8"))["records"]
PERIOD_YEARS = {"Vor 1919": 1918, "1919 bis 1944": 1931, "1945 bis 1960": 1952}
SITE = "AT-VIE-RUDOLFSHEIM"
SEVEN = {
    "AT-VIE-RUDOLFSHEIM": ("AT", "at", "EPSG:32633"),
    "KR-SEO-MAPO": ("KR", "kr", "EPSG:32652"),
    "CA-MTL-PLATEAU": ("CA", "ca", "EPSG:32618"),
    "FI-HEL-KALLIO": ("FI", "fi", "EPSG:32635"),
    "ZA-CPT-WOODSTOCK": ("ZA", "za", "EPSG:32734"),
    "HU-BUD-ERZSEBETVAROS": ("HU", "hu", "EPSG:32634"),
    "AM-EVN-NORNORK": ("AM", "am", "EPSG:32638"),
}


def counts(**kw):
    return json.dumps({k.replace("_", " "): v for k, v in kw.items()})


def row(**kw):
    base = {
        "osm_id": "b", "building_tag": "", "levels": float("nan"), "height_m": float("nan"),
        "year_built": float("nan"), "provenance_year_built": "X_MISSING", "provenance_height_m": "X_MISSING",
        "census_period_counts": counts(Vor_1919=5, **{"1919_bis_1944": 2}),
    }
    base.update(kw)
    return pd.Series(base)


def test_dominant_period_rungs():
    assert ncr.dominant_period({"Vor 1919": 5, "1919 bis 1944": 2}, PERIOD_YEARS) == (1918, "Vor 1919")
    year, label = ncr.dominant_period({"Vor 1919": 4, "1919 bis 1944": 4, "1945 bis 1960": 1}, PERIOD_YEARS)
    assert year is None and label == "CENSUS_UNIT_PERIOD_TIE_Vor_1919_1919_bis_1944"
    assert ncr.dominant_period({"Vor 1919": 0}, PERIOD_YEARS) == (None, "CENSUS_UNIT_NO_PERIOD_DATA")
    assert ncr.dominant_period({"Keine Angabe": 9}, PERIOD_YEARS) == (None, "UNMAPPABLE_PERIOD_Keine_Angabe")


def test_year_rungs():
    assert ncr.resolve_year(row(year_built=1962.0, provenance_year_built="X_OBSERVED"), PERIOD_YEARS) == (1962, "", "")
    assert ncr.resolve_year(row(), PERIOD_YEARS) == (1918, ncr.CENSUS_PERIOD_PROVENANCE, "")
    tie = row(census_period_counts=counts(Vor_1919=3, **{"1919_bis_1944": 3}))
    assert ncr.resolve_year(tie, PERIOD_YEARS)[0] is None
    assert ncr.resolve_year(tie, PERIOD_YEARS)[2].startswith("CENSUS_UNIT_PERIOD_TIE_")
    assert ncr.resolve_year(row(census_period_counts=None), PERIOD_YEARS)[2] == ncr.MISSING_CENSUS_UNIT_DATA
    assert ncr.resolve_year(row(year_built=1962.0, provenance_year_built="X_MISSING", census_period_counts=""), PERIOD_YEARS)[0] is None


def test_storey_rungs():
    assert ncr.resolve_storeys(row(levels=4.0)) == (4, "")
    assert ncr.resolve_storeys(row(height_m=10.4, provenance_height_m="X_MEASURED")) == (3, ncr.HEIGHT_STOREY_PROVENANCE)
    assert ncr.resolve_storeys(row(height_m=1.0, provenance_height_m="X_MEASURED")) == (1, ncr.HEIGHT_STOREY_PROVENANCE)
    assert ncr.resolve_storeys(row(height_m=10.4, provenance_height_m="X_MISSING")) == (None, "")
    assert ncr.resolve_storeys(row(levels=2.5)) == (None, "")
    assert ncr.resolve_storeys(row(levels=4.0, height_m=30.0, provenance_height_m="X_MEASURED")) == (4, "")


@pytest.mark.parametrize(
    "storeys,attached,expected",
    [(1, True, "TH"), (2, True, "TH"), (1, False, "SFH"), (2, False, "SFH"), (3, False, "MFH"), (4, True, "MFH"),
     (5, False, "AB"), (9, True, "AB")],
)
def test_storey_rule_type(storeys, attached, expected):
    assert ncr.storey_rule_type(storeys, attached) == expected
    assert ncr.resolve_type(row(), storeys, attached) == (expected, ncr.STOREY_RULE_PROVENANCE)


def test_type_tag_and_two_signal():
    assert ncr.resolve_type(row(building_tag="apartments"), 2, False) == ("AB", "OBSERVED_TAG")
    assert ncr.resolve_type(row(building_tag="detached"), 6, True) == ("SFH", "OBSERVED_TAG")
    assert ncr.resolve_type(row(building_tag="terrace"), 6, False) == ("TH", "OBSERVED_TAG")
    assert ncr.resolve_type(row(observed_dwellings=1.0), 2, True) == ("TH", "DERIVED_BDTOPO_TWO_SIGNAL")
    assert ncr.resolve_type(row(observed_dwellings=6.0), 3, False) == ("MFH", "DERIVED_BDTOPO_TWO_SIGNAL")
    assert ncr.resolve_type(row(observed_dwellings=40.0), 6, False) == ("AB", "DERIVED_BDTOPO_TWO_SIGNAL")
    assert ncr.resolve_type(row(observed_dwellings=40.0), 3, False) == ("MFH", ncr.STOREY_RULE_PROVENANCE)


def square(x, y, w=10.0):
    return box(600000 + x, 5340000 + y, 600000 + x + w, 5340000 + y + w)


def synthetic_gdf():
    rows = [
        dict(osm_id="a_obs", geometry=square(0, 0), levels=2.0, year_built=1962.0, provenance_year_built="V_OBSERVED"),
        dict(osm_id="b_touch", geometry=square(10, 0), levels=2.0, year_built=1962.0, provenance_year_built="V_OBSERVED"),
        dict(osm_id="c_census", geometry=square(100, 0), levels=6.0),
        dict(osm_id="d_tie", geometry=square(200, 0), levels=3.0,
             census_period_counts=counts(Vor_1919=3, **{"1919_bis_1944": 3})),
        dict(osm_id="e_height", geometry=square(300, 0), height_m=10.4, provenance_height_m="V_MEASURED"),
        dict(osm_id="f_nostorey", geometry=square(10, 10), census_period_counts=counts(Vor_1919=9)),
        dict(osm_id="g_far_nostorey", geometry=square(1000, 1000), census_period_counts=counts(Vor_1919=9)),
    ]
    frame = pd.DataFrame(rows)
    frame["building_tag"] = ""
    frame["provenance_year_built"] = frame["provenance_year_built"].fillna("V_MISSING")
    frame["provenance_height_m"] = frame.get("provenance_height_m", pd.Series(dtype=object)).fillna("V_MISSING")
    frame["census_period_counts"] = frame["census_period_counts"].fillna(counts(Vor_1919=5, **{"1919_bis_1944": 2}))
    return gpd.GeoDataFrame(frame, geometry="geometry", crs="EPSG:32633")


def test_new_country_rows_end_to_end():
    gdf = synthetic_gdf()
    rows, exclusions = ncr.new_country_rows(SITE, gdf, AT_RECORDS, PERIOD_YEARS)
    by_id = {r["building_id"]: r for r in rows}
    assert set(by_id) == {"a_obs", "b_touch", "c_census", "e_height"}
    assert by_id["a_obs"]["building_type"] == "TH" and by_id["a_obs"]["is_attached"] is True
    assert by_id["a_obs"]["year_built"] == 1962 and by_id["a_obs"]["construction_period_provenance"] == ""
    assert by_id["a_obs"]["age_band"] == "AT.04"
    assert by_id["c_census"]["year_built"] == 1918 and by_id["c_census"]["building_type"] == "AB"
    assert by_id["c_census"]["construction_period_provenance"] == ncr.CENSUS_PERIOD_PROVENANCE
    assert by_id["e_height"]["levels"] == 3 and by_id["e_height"]["storey_provenance"] == ncr.HEIGHT_STOREY_PROVENANCE
    assert by_id["e_height"]["building_type"] == "MFH" and by_id["e_height"]["is_attached"] is False
    assert all(r["archetype_id"].startswith("AT.") for r in rows)
    blockers = {x["building_id"]: x["blocker"] for x in exclusions.records}
    assert blockers["d_tie"].startswith("CENSUS_UNIT_PERIOD_TIE_")
    assert blockers["f_nostorey"] == ncr.MISSING_OBSERVED_STOREY_COUNT
    assert blockers["g_far_nostorey"] == ncr.MISSING_OBSERVED_STOREY_COUNT
    assert sum(exclusions.values()) == 3


def test_neighbour_route_recovers_storeys_only():
    gdf = synthetic_gdf()
    rows, _ = ncr.new_country_rows(SITE, gdf, AT_RECORDS, PERIOD_YEARS)
    original = campaign.load_period_years
    campaign.load_period_years = lambda district: PERIOD_YEARS
    try:
        recovered, refused = campaign._impute_new_country_rows(SITE, gdf, AT_RECORDS, rows)
    finally:
        campaign.load_period_years = original
    by_id = {r["building_id"]: r for r in recovered}
    assert "d_tie" not in by_id
    touching = by_id["f_nostorey"]
    assert touching["levels"] == 2 and touching["storey_provenance"] == "IMPUTED_NEIGHBOUR_TOUCHING"
    assert touching["imputation_provenance"] == "IMPUTED_NEIGHBOUR_TOUCHING"
    assert touching["building_type"] == "SFH" or touching["building_type"] == "TH"
    far = by_id["g_far_nostorey"]
    assert far["storey_provenance"] == "IMPUTED_DISTRICT_MODE"
    assert sum(refused.values()) == 0


def test_registration_of_the_seven_sites():
    for site, (country, fold, crs) in SEVEN.items():
        assert EU02_SITE_COUNTRY[site] == country
        assert campaign.DISTRICTS[site] == {"country": country, "fold": fold, "crs": crs}
        assert COUNTRY_FILES[country] == fold
        with pytest.raises(ValueError) as caught:
            map_observed_building_to_tabula(
                pd.Series({"osm_id": ""}), neighbourhood_id=site, country_stock_code=country, records=[]
            )
        assert "Unsupported" not in str(caught.value)
    assert ncr.NEW_COUNTRIES == {c for c, _, _ in SEVEN.values()}
    with pytest.raises(ValueError, match="Unsupported country_stock_code"):
        map_observed_building_to_tabula(pd.Series({"osm_id": "x"}), neighbourhood_id="n", country_stock_code="XX", records=[])


def test_period_tables_for_new_countries():
    assert tabula_period("AT", 1918) == "AT.01" and tabula_period("AT", 2012) == "AT.08"
    assert tabula_period("HU", 1944) == "HU.01" and tabula_period("HU", 2006) == "HU.05"
    for old in ("ES", "FR", "GB", "IT"):
        assert old in _TABULA_PERIODS
    assert set(_TABULA_PERIODS) == {"ES", "GB", "IT", "FR", "AT", "HU", "FI", "CA", "KR", "ZA", "AM"}


def test_unregistered_period_table_fails_loudly(monkeypatch):
    monkeypatch.setitem(ncr.EU02_SITE_COUNTRY, "XX-SEO-MAPO", "XX")
    monkeypatch.setattr(ncr, "NEW_COUNTRIES", ncr.NEW_COUNTRIES | {"XX"})
    with pytest.raises(ValueError, match="No TABULA construction periods"):
        ncr.new_country_rows("XX-SEO-MAPO", synthetic_gdf(), [], PERIOD_YEARS)


HU_RECORDS = json.loads((ROOT / "openubem/data/construction/tabula_archetypes_hu.json").read_text(encoding="utf-8"))["records"]


@pytest.mark.parametrize(
    "building_type,year,archetype_id,provenance",
    [
        ("TH", 1950, "HU.N.SFH.02.Gen.ReEx.001.001", "TABULA_TYPE_SUBSTITUTE_SFH_FOR_TH"),
        ("AB", 1995, "HU.N.MFH.04.Gen.ReEx.001.001", "TABULA_TYPE_SUBSTITUTE_MFH_FOR_AB"),
        ("AB", 1960, "HU.N.AB.01-03.Gen.SyAv.001.001", ""),
    ],
)
def test_hu_type_substitute_rule(building_type, year, archetype_id, provenance):
    item = row(osm_id="x")
    built, blocker, _ = ncr.build_row(
        item, country="HU", records=HU_RECORDS, year=year, year_provenance="",
        storeys={"TH": 2, "AB": 5}[building_type], storey_provenance="", is_attached=building_type == "TH",
    )
    assert blocker == ""
    assert built["archetype_id"] == archetype_id
    assert built["archetype_provenance"] == provenance
