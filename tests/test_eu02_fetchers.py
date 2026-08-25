import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from openubem.acquisition.bdtopo_fetcher import CRS84, classify_bdtopo_use, ingest_bdtopo
from openubem.acquisition.osm_fetcher import ingest_buildings
from openubem.acquisition.bologna_fetcher import classify_bologna_ctc, classify_bologna_rifter, ingest_bologna, ingest_bologna_ctc
from openubem.acquisition.footprint_schema import SCHEMA_COLUMNS, validate_schema


def _write(gdf, path):
    gdf.to_file(path, driver="GeoJSON")
    return path


def test_bdtopo_offline_slice_uses_crs84_and_frozen_schema(tmp_path):
    path = _write(gpd.GeoDataFrame({
        "cleabs": ["a", "b"], "usage_1": ["Résidentiel", "Indifférencié"],
        "usage_2": [None, "Résidentiel"], "nombre_d_etages": [3, 4], "hauteur": [10.2, 13.0],
        "date_d_apparition": ["1980-01-01", "2001-05-02"], "nombre_de_logements": [4, 5],
    }, geometry=[box(0, 0, 10, 10), box(20, 0, 30, 10)], crs="EPSG:3857"), tmp_path / "fr.geojson")
    result = ingest_bdtopo(slice_path=path)
    assert CRS84 == "CRS:84"
    assert list(result.columns) == SCHEMA_COLUMNS
    assert str(result.levels.dtype) == str(result.year_built.dtype) == "Int64"
    validate_schema(result)


def test_bologna_ctc_offline_slice_supports_export_field_aliases(tmp_path):
    path = _write(gpd.GeoDataFrame({
        "codice_ogg": ["a", "b"], "descrizion": ["Edificio generico", "Chiesa"],
        "altezza_gr": [None, 12.5], "quota_gron": [20.0, 20.0], "quota_pied": [8.0, 7.0], "volume": [100, 200],
    }, geometry=[box(0, 0, 10, 10), box(20, 0, 30, 10)], crs="EPSG:3857"), tmp_path / "it.geojson")
    result = ingest_bologna_ctc(slice_path=path)
    assert list(result.columns) == SCHEMA_COLUMNS
    assert result.height_m.tolist() == [12.0, 12.5]
    assert result.levels.isna().all() and result.year_built.isna().all()
    validate_schema(result)


def test_bdtopo_classification_honours_usage_2_residential(tmp_path):
    residential = "R\u00e9sidentiel"
    commercial = "Commercial et services"
    path = _write(gpd.GeoDataFrame({
        "cleabs": ["a", "b"], "usage_1": [residential, commercial],
        "usage_2": [None, residential], "nombre_d_etages": [3, 4], "hauteur": [10.2, 13.0],
        "date_d_apparition": ["1980-01-01", "2001-05-02"],
    }, geometry=[box(0, 0, 10, 10), box(20, 0, 30, 10)], crs="EPSG:3857"), tmp_path / "fr-class.geojson")
    assert classify_bdtopo_use(ingest_bdtopo(slice_path=path)).tolist() == ["residential", "residential"]


def test_bologna_cadastral_slice_is_the_final_building_unit(tmp_path):
    path = _write(gpd.GeoDataFrame({
        "codfab": [101, 102], "tipologia": ["Edificio generico", None],
        "foglio": [201, 201], "mappale": ["1", "2"],
    }, geometry=[box(0, 0, 10, 10), box(20, 0, 30, 10)], crs="EPSG:3857"), tmp_path / "rifter.geojson")
    result = ingest_bologna(slice_path=path)
    assert result.osm_id.tolist() == ["101", "102"]
    assert result.levels.isna().all() and result.year_built.isna().all()
    validate_schema(result)
    assert classify_bologna_rifter(result).tolist() == ["residential", "residential"]


def test_bologna_ctc_catalogue_crosswalk_is_complete_and_fail_closed(tmp_path):
    values = [
        None, "Baracca", "Cabina ENEL", "Campanile", "Carcere", "Chiesa",
        "Chiosco alimentari", "Chiosco fiori", "Chiosco gelati", "Chiosco giornali",
        "Cimitero", "Collegamento in quota", "Edificio ad uso agricolo",
        "Edificio diroccato", "Edificio generico", "Edificio per centrale termica",
        "Edificio scolastico", "Edificio sportivo", "In costruzione", "Mura storiche",
        "Ospedale", "Parcheggio multipiano", "Portico", "Serra", "Servizi", "Silos",
        "Stabilimento industriale", "Stazione di rifornimento", "Studentato", "Tettoia/pensilina",
    ]
    path = _write(gpd.GeoDataFrame({
        "codice_ogg": list(range(len(values))), "descrizion": values,
    }, geometry=[box(i * 20, 0, i * 20 + 10, 10) for i in range(len(values))], crs="EPSG:3857"), tmp_path / "ctc-catalogue.geojson")
    classified = classify_bologna_ctc(ingest_bologna_ctc(slice_path=path))
    assert classified.tolist().count("residential") == 1
    assert classified.tolist().count("non_residential") == 29


def test_bologna_rifter_live_typology_aliases_are_explicit_exclusions(tmp_path):
    path = _write(gpd.GeoDataFrame({
        "codfab": [1, 2, 3, 4],
        "tipologia": ["Edificio generico", "Cabina ENEL", "Mura storiche", "Stazione di rifornimento"],
    }, geometry=[box(i * 20, 0, i * 20 + 10, 10) for i in range(4)], crs="EPSG:3857"), tmp_path / "rifter_aliases.geojson")
    result = ingest_bologna(slice_path=path)
    assert classify_bologna_rifter(result).tolist() == ["residential", "non_residential", "non_residential", "non_residential"]


def test_documented_dispatch_reaches_bologna_adapter(tmp_path):
    path = _write(gpd.GeoDataFrame({"codfab": [101], "tipologia": ["Edificio generico"]}, geometry=[box(0, 0, 10, 10)], crs="EPSG:3857"), tmp_path / "rifter.geojson")
    result = ingest_buildings(bbox=(1, 0, 1, 0), source="bologna", source_options={"slice_path": path})
    assert result.osm_id.tolist() == ["101"]


def test_bdtopo_year_parse_recovers_real_date_shapes_and_pre_1677_years(tmp_path):
    """Verify exact year extraction for real BD TOPO date formats (Z suffix, pre-1677)."""
    dates = ["1998-01-01Z", "1820-01-01Z", "1580-01-01Z", "2010-06-15Z"]
    path = _write(gpd.GeoDataFrame({
        "cleabs": [f"fr_{i}" for i in range(len(dates))],
        "usage_1": ["Résidentiel"] * len(dates),
        "nombre_d_etages": [3] * len(dates),
        "hauteur": [10.0] * len(dates),
        "date_d_apparition": dates,
        "nombre_de_logements": [4] * len(dates),
    }, geometry=[box(i * 20, 0, i * 20 + 10, 10) for i in range(len(dates))], crs="EPSG:3857"), tmp_path / "fr-years.geojson")
    result = ingest_bdtopo(slice_path=path)
    assert result.year_built.tolist() == [1998, 1820, 1580, 2010]
    assert result.year_built.notna().all()
    validate_schema(result)


def test_bdtopo_retains_all_years_when_source_dates_present(tmp_path):
    """Assert zero silent year loss when input source dates are all valid."""
    dates = ["1998-01-01Z", "1820-01-01Z", "1580-01-01Z", "2010-06-15Z", "1900-01-01Z", "1750-01-01Z"]
    path = _write(gpd.GeoDataFrame({
        "cleabs": [f"b_{i}" for i in range(len(dates))],
        "usage_1": ["Résidentiel"] * len(dates),
        "nombre_d_etages": [2] * len(dates),
        "hauteur": [8.0] * len(dates),
        "date_d_apparition": dates,
        "nombre_de_logements": [1] * len(dates),
    }, geometry=[box(i * 15, 0, i * 15 + 10, 10) for i in range(len(dates))], crs="EPSG:3857"), tmp_path / "fr-retained.geojson")
    result = ingest_bdtopo(slice_path=path)
    assert len(result) == len(dates)
    assert result.year_built.notna().sum() == len(dates)
    assert result.year_built.isna().sum() == 0

