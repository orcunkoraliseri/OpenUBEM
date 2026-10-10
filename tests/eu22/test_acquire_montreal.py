import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.eu22 import acquire_montreal as am  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
FID = {"A_big": 100, "A_small": 101, "B1": 102, "B2": 103, "B3": 104, "C": 105, "D_nolot": 106, "E": 107, "F": 108, "G": 109, "H": 110, "K": 111}


@pytest.fixture(scope="module")
def built():
    roofs = gpd.read_file(FIX / "montreal_roofs_fixture.geojson").set_index("fid")
    roll = gpd.read_file(FIX / "montreal_roll_fixture.geojson")
    clean, rep, lots = am.build_clean_buildings(roofs, roll)
    return clean.set_index("osm_id"), rep, lots


def ids(built, name):
    prefix = f"CA-MTL-{FID[name]}-"
    return [i for i in built[0].index if i.startswith(prefix)]


def row(built, name):
    own = ids(built, name)
    assert len(own) == 1, (name, own)
    return built[0].loc[own[0]]


def test_split_sums_to_lot_count_and_matches_hand_computation(built):
    clean, _, _ = built
    assert [int(row(built, n).observed_dwellings) for n in ("A_big", "A_small")] == [4, 2]
    assert [int(row(built, n).observed_dwellings) for n in ("B1", "B2", "B3")] == [2, 2, 1]
    assert int(clean.loc[[ids(built, n)[0] for n in ("A_big", "A_small")], "observed_dwellings"].sum()) == 6
    assert int(clean.loc[[ids(built, n)[0] for n in ("B1", "B2", "B3")], "observed_dwellings"].sum()) == 5
    assert row(built, "A_big").dwellings_source == "observed_split"
    assert row(built, "F").dwellings_source == "observed"


def test_largest_remainder_each_at_least_one():
    assert am.split_largest_remainder(6, [200.0, 100.0]) == [4, 2]
    assert am.split_largest_remainder(5, [100.0, 100.0, 100.0]) == [2, 2, 1]
    assert am.split_largest_remainder(2, [1.0, 1.0, 1.0]) == [1, 1, 1]
    assert sum(am.split_largest_remainder(17, [3.0, 9.0, 5.0, 1.0])) == 17


def test_multi_unit_lot_aggregation(built):
    r = row(built, "B1")
    assert int(r.levels) == 3
    assert int(r.year_built) == 1950


def test_null_markers_minus_one_and_9999(built):
    r = row(built, "C")
    assert pd.isna(r.levels) and pd.isna(r.year_built) and pd.isna(r.observed_dwellings)
    assert r.dwellings_source == "missing"
    assert r.use_class == "residential"
    assert pd.isna(am.clean_count(-1)) and pd.isna(am.clean_count(0)) and am.clean_count(3) == 3
    assert pd.isna(am.clean_year(9999)) and pd.isna(am.clean_year(1599)) and am.clean_year(1600) == 1600


def test_year_before_1600_missing_1600_kept(built):
    assert int(row(built, "H").year_built) == 1600
    assert pd.isna(row(built, "K").year_built)
    assert row(built, "K").provenance_year_built == "MTL_ROLE_MISSING"
    assert row(built, "H").provenance_year_built == "MTL_ROLE_OBSERVED"


def test_centroid_in_no_lot_has_empty_attributes(built):
    r = row(built, "D_nolot")
    assert pd.isna(r.levels) and pd.isna(r.year_built) and pd.isna(r.observed_dwellings)
    assert r.use_class == "unknown" and pd.isna(r.lot_id)
    assert built[1]["buildings_with_no_lot"] == 1


def test_use_class_and_type_tags(built):
    assert row(built, "E").use_class == "non_residential"
    assert row(built, "A_big").building_tag == ""
    assert row(built, "F").building_tag == "terrace" and row(built, "G").building_tag == "terrace"
    assert row(built, "H").building_tag == "detached"


def test_lot_report(built):
    assert built[1]["lots_with_several_buildings"] == 2


def test_crs_is_utm_18n_and_schema(built):
    clean = built[0]
    assert clean.crs.to_string() == "EPSG:32618"
    assert clean["crs_utm"].unique().tolist() == ["EPSG:32618"]
    for col in ("observed_dwellings", "dwellings_source"):
        assert col in clean.columns


def test_split_residential_on_fixture(built):
    from openubem.acquisition.boundary_clip import split_residential

    clean = built[0].reset_index()
    res, exc, counts = split_residential(clean, am.CROSSWALK, class_column="use_class")
    assert counts["residential"] == 10 and counts["non_residential"] == 1 and counts["unknown"] == 1
    assert counts["total"] == len(clean) == 12


def _three_lot_case():
    from shapely.geometry import box

    crs = "EPSG:2950"
    x0, y0 = 296000.0, 5041000.0
    roof = gpd.GeoDataFrame({"fid": [900]}, geometry=[box(x0, y0, x0 + 30, y0 + 10)], crs=crs).set_index("fid")
    lots = [box(x0 + 10 * i - (2 if i == 0 else 0), y0 - 2, x0 + 10 * (i + 1) + (2 if i == 2 else 0), y0 + 12) for i in range(3)]
    rows = [
        {"ID_UEV": f"T{i}", "ETAGE_HORS_SOL": 2 + i, "NOMBRE_LOGEMENT": 2 + i, "ANNEE_CONSTRUCTION": 1900 + 10 * i,
         "CODE_UTILISATION": "1000", "LIBELLE_UTILISATION": "Logement"}
        for i in range(3)
    ]
    roll = gpd.GeoDataFrame(rows, geometry=lots, crs=crs)
    return roof, roll, lots


def test_roof_over_three_lots_gives_three_buildings_with_own_attributes():
    roof, roll, _ = _three_lot_case()
    clean, rep, _ = am.build_clean_buildings(roof, roll)
    assert len(clean) == 3
    assert clean["footprint_area_m2"].sum() == pytest.approx(float(roof.geometry.area.iloc[0]), rel=0.005)
    assert sorted(clean["levels"].astype(int).tolist()) == [2, 3, 4]
    assert sorted(clean["year_built"].astype(int).tolist()) == [1900, 1910, 1920]
    assert sorted(clean["observed_dwellings"].astype(int).tolist()) == [2, 3, 4]
    assert (clean["provenance_geometry"] == "MTL_BATIMENT2D_SPLIT_BY_LOT").all()
    assert all(i.startswith("CA-MTL-900-LOT") for i in clean["osm_id"])
    assert rep["roofs_cut_into_several_buildings"] == 1


def test_small_pieces_dropped_and_site_dwellings_within_ten_percent_of_roll():
    from shapely.geometry import box

    roof, roll, lots = _three_lot_case()
    x0, y0 = 296000.0, 5041000.0
    sliver = box(x0 + 30.0, y0, x0 + 31.0, y0 + 10.0)
    roof = gpd.GeoDataFrame({"fid": [900]}, geometry=[box(x0, y0, x0 + 31, y0 + 10)], crs=roof.crs).set_index("fid")
    roll = roll.copy()
    roll.loc[len(roll)] = {"ID_UEV": "T3", "ETAGE_HORS_SOL": 1, "NOMBRE_LOGEMENT": 1, "ANNEE_CONSTRUCTION": 1990,
                           "CODE_UTILISATION": "1000", "LIBELLE_UTILISATION": "Logement", "geometry": box(x0 + 30.0, y0 - 2, x0 + 32.0, y0 + 12)}
    roll = gpd.GeoDataFrame(roll, geometry="geometry", crs="EPSG:2950")
    clean, rep, lots_u = am.build_clean_buildings(roof, roll)
    assert rep["pieces_dropped_under_min_area"] == 1
    assert rep["n_pieces"] == 3
    assert rep["pieces_dropped_area_m2"] == pytest.approx(sliver.area, rel=0.01)
    res = clean[clean["use_class"] == "residential"]
    agree = am.dwelling_agreement(res, lots_u, box(x0 - 5, y0 - 5, x0 + 40, y0 + 15))
    assert agree["roll_dwellings_in_boundary_lots"] == 10
    assert abs(agree["site_vs_roll_ratio"] - 1.0) <= 0.10
