"""T06 — tests for climate_zone.py §3A/§3B against the real bundled GPKG.

DESIGN §5.1 (F14) + §5.2 (F15):
- 8 known-city fixtures
- Boston Harbor nearest_fallback + HEURISTIC
- Suffolk/Middlesex county-line pair
- open-ocean abort
- schema-gate negative tests
"""
from __future__ import annotations

import json

import geopandas as gpd
import pytest
from pyproj import CRS, Transformer
from shapely.geometry import box

from openubem.acquisition.climate_zone import (
    _validate_input_schema,
    _join_points,
    assign_climate_zones,
)

# Pre-defined UTM CRS instances used in parametrize list
_UTM6N  = CRS.from_epsg(32606)   # Fairbanks Alaska
_UTM10N = CRS.from_epsg(32610)   # San Francisco
_UTM12N = CRS.from_epsg(32612)   # Denver / Phoenix
_UTM15N = CRS.from_epsg(32615)   # Chicago / Duluth
_UTM17N = CRS.from_epsg(32617)   # Miami / SE US
_UTM19N = CRS.from_epsg(32619)   # Boston / NE US


def _make_gdf_at(lat: float, lon: float, utm_crs: CRS, osm_id: str = "way/test_1") -> gpd.GeoDataFrame:
    """Build minimal 26-column GDF with a 10x10m square at the given WGS84 coordinate."""
    tf = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
    cx, cy = tf.transform(lon, lat)
    geom = box(cx - 5, cy - 5, cx + 5, cy + 5)
    return _make_26col_gdf([osm_id], [geom], utm_crs)


def _make_26col_gdf(
    osm_ids: list[str],
    geoms: list,
    utm_crs: CRS,
) -> gpd.GeoDataFrame:
    """Build a minimal 26-column GDF in the given UTM CRS."""
    from openubem.semantic.building_classifier import _OUTPUT_SCHEMA_COLUMNS
    rows = []
    for osm_id in osm_ids:
        rows.append({
            "osm_id": osm_id,
            "crs_utm": str(utm_crs),
            "building_tag": "yes",
            "function_tag": None,
            "levels": 2.0,
            "height_m": float("nan"),
            "year_built": float("nan"),
            "postcode": None,
            "underground": False,
            "roof_shape": None,
            "roof_height_m": float("nan"),
            "footprint_area_m2": 100.0,
            "perimeter_m": 40.0,
            "surplus_tags": "{}",
            "provenance_levels": "OSM",
            "provenance_height_m": "NONE",
            "provenance_year_built": "NONE",
            "provenance_building_tag": "OSM",
            "provenance_function_tag": "NONE",
            "provenance_postcode": "NONE",
            "provenance_geometry": "OSM",
            "data_quality_flag": "",
            "archetype_id": "SmallOffice",
            "archetype_confidence": "HIGH",
            "archetype_source": "RULE_USE_CLASS",
        })
    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs=utm_crs)
    # _OUTPUT_SCHEMA_COLUMNS includes "geometry" as first element.
    # Select all columns to enforce exact ordering (GeoDataFrame preserves geometry).
    gdf = gdf[_OUTPUT_SCHEMA_COLUMNS]
    return gdf


# ── Known-city fixtures (F14) ──────────────────────────────────────────────────

@pytest.mark.parametrize("city,lat,lon,utm_crs,expected_zone", [
    ("Miami",         25.7617, -80.1918,  _UTM17N, "1A"),
    ("Phoenix",       33.4484, -112.0740, _UTM12N, "2B"),
    ("SanFrancisco",  37.7749, -122.4194, _UTM10N, "3C"),
    ("Boston",        42.3601, -71.0589,  _UTM19N, "5A"),
    ("Chicago",       41.8781, -87.6298,  _UTM15N, "5A"),
    ("Denver",        39.7392, -104.9903, _UTM12N, "5B"),
    ("Duluth",        46.7867, -92.1005,  _UTM15N, "7"),
    ("Fairbanks",     64.8401, -147.7200, _UTM6N,  "8"),
])
def test_known_city_zone(city, lat, lon, utm_crs, expected_zone):
    gdf = _make_gdf_at(lat, lon, utm_crs, f"way/{city}")
    result = assign_climate_zones(gdf)
    assert len(result) == 1, f"{city}: expected 1 row"
    row = result.iloc[0]
    assert row["climate_zone"] == expected_zone, (
        f"{city}: expected {expected_zone}, got {row['climate_zone']}"
    )
    assert row["provenance_climate_zone"] in ("ASHRAE_STANDARD", "HEURISTIC")
    assert row["state"] is not None and len(str(row["state"])) == 2


# ── Boston Harbor nearest_fallback (F15 / C1-updated) ─────────────────────────

def test_boston_harbor_nearest_fallback():
    """(42.45, -70.80) is a Tier-1 miss within 5 km of Plymouth County.

    C1 (DESIGN line 62): a run whose ALL points miss Tier-1 aborts with zero_tier1_matches
    even when Tier-2 would resolve them.  nearest_fallback is only reachable in a MIXED run
    (tested by test_mixed_tier1_tier2_still_passes).
    """
    lat, lon = 42.45, -70.80
    gdf = _make_gdf_at(lat, lon, _UTM19N, "way/harbor")
    with pytest.raises(RuntimeError) as exc_info:
        assign_climate_zones(gdf)
    payload = json.loads(str(exc_info.value))
    assert payload["event"] == "zero_tier1_matches"


# ── Suffolk / Middlesex county-line pair (F15) ─────────────────────────────────

def test_suffolk_middlesex_pair():
    """Two points either side of the Suffolk/Middlesex line -> different county_geoid, same zone 5A."""
    tf = Transformer.from_crs("EPSG:4326", _UTM19N, always_xy=True)

    # Suffolk County (Boston proper) ~ 42.35, -71.06
    cx1, cy1 = tf.transform(-71.065, 42.353)
    geom1 = box(cx1 - 5, cy1 - 5, cx1 + 5, cy1 + 5)

    # Middlesex County (Cambridge) ~ 42.37, -71.10
    cx2, cy2 = tf.transform(-71.10, 42.37)
    geom2 = box(cx2 - 5, cy2 - 5, cx2 + 5, cy2 + 5)

    gdf = _make_26col_gdf(["way/suffolk", "way/middlesex"], [geom1, geom2], _UTM19N)
    result = assign_climate_zones(gdf)

    assert len(result) == 2
    assert all(result["climate_zone"] == "5A"), f"Zones: {result['climate_zone'].tolist()}"
    assert result.iloc[0]["county_geoid"] != result.iloc[1]["county_geoid"], (
        "Expected different county_geoid for Suffolk vs Middlesex"
    )


# ── Open-ocean abort (F15) ────────────────────────────────────────────────────

def test_open_ocean_abort():
    """A point in mid-Atlantic (> 5 km from any US county) raises RuntimeError.

    With C1 applied, all-Tier-1-miss now raises zero_tier1_matches BEFORE Tier 2.
    """
    lat, lon = 35.0, -40.0
    utm_28 = CRS.from_epsg(32628)
    tf = Transformer.from_crs("EPSG:4326", utm_28, always_xy=True)
    cx, cy = tf.transform(lon, lat)
    geom = box(cx - 5, cy - 5, cx + 5, cy + 5)
    gdf = _make_26col_gdf(["way/ocean"], [geom], utm_28)
    with pytest.raises(RuntimeError) as exc_info:
        assign_climate_zones(gdf)
    payload = json.loads(str(exc_info.value))
    assert payload["event"] in ("unmatched_buildings", "zero_tier1_matches")


# ── C1 — zero_tier1_matches abort (DESIGN line 62, F5) ───────────────────────

def test_zero_tier1_matches_abort():
    """C1 (a): every point misses Tier-1 but is within 5 km of a county must abort
    with zero_tier1_matches BEFORE running Tier 2.

    Uses the Plymouth offshore coord (42.45, -70.80) which is within 5 km of a county
    (Tier-2 resolvable), alongside a second point that is also Tier-1 miss.
    With C1 applied the entire run aborts because ALL points miss Tier-1.
    """
    # Both points are offshore near Plymouth — Tier-1 miss, Tier-2 would resolve them
    coords = [(42.45, -70.80), (42.43, -70.82)]
    tf = Transformer.from_crs("EPSG:4326", _UTM19N, always_xy=True)
    geoms = []
    osm_ids = []
    for i, (lat, lon) in enumerate(coords):
        cx, cy = tf.transform(lon, lat)
        geoms.append(box(cx - 5, cy - 5, cx + 5, cy + 5))
        osm_ids.append(f"way/offshore_{i}")
    gdf = _make_26col_gdf(osm_ids, geoms, _UTM19N)
    with pytest.raises(RuntimeError) as exc_info:
        assign_climate_zones(gdf)
    payload = json.loads(str(exc_info.value))
    assert payload["event"] == "zero_tier1_matches", (
        f"Expected zero_tier1_matches, got {payload['event']}"
    )


def test_mixed_tier1_tier2_still_passes():
    """C1 (b): a mixed run (some Tier-1, some Tier-2) must still succeed.

    One on-land Boston point (Tier-1 hit) + one Plymouth offshore point (Tier-2 hit).
    With C1 applied the zero_tier1_matches guard must NOT fire because ≥1 Tier-1 match exists.
    """
    tf = Transformer.from_crs("EPSG:4326", _UTM19N, always_xy=True)

    # Tier-1 point: downtown Boston (definitely within a county polygon)
    cx1, cy1 = tf.transform(-71.06, 42.36)
    geom1 = box(cx1 - 5, cy1 - 5, cx1 + 5, cy1 + 5)

    # Tier-2 point: offshore Plymouth (Tier-1 miss, within 5 km of Plymouth County)
    cx2, cy2 = tf.transform(-70.80, 42.45)
    geom2 = box(cx2 - 5, cy2 - 5, cx2 + 5, cy2 + 5)

    gdf = _make_26col_gdf(["way/boston", "way/harbor"], [geom1, geom2], _UTM19N)
    result = assign_climate_zones(gdf)

    assert len(result) == 2
    boston_row = result.iloc[0]
    harbor_row = result.iloc[1]
    assert boston_row["provenance_climate_zone"] == "ASHRAE_STANDARD"
    assert boston_row["climate_zone_method"] == "county_within"
    assert harbor_row["provenance_climate_zone"] == "HEURISTIC"
    assert harbor_row["climate_zone_method"] == "nearest_fallback"


# ── Schema gate — negative tests (P7) ─────────────────────────────────────────

def test_gate_missing_column():
    gdf = _make_gdf_at(42.36, -71.06, _UTM19N)
    gdf = gdf.drop(columns=["archetype_id"])
    with pytest.raises(ValueError, match="missing columns"):
        _validate_input_schema(gdf)


def test_gate_bad_archetype_token():
    gdf = _make_gdf_at(42.36, -71.06, _UTM19N).copy()
    gdf["archetype_id"] = "NotAValidType"
    with pytest.raises(ValueError, match="archetype_id"):
        _validate_input_schema(gdf)


def test_gate_extra_column():
    gdf = _make_gdf_at(42.36, -71.06, _UTM19N).copy()
    gdf["extra_column"] = 0
    with pytest.raises(ValueError, match="unexpected extra columns"):
        _validate_input_schema(gdf)


def test_gate_valid_passes():
    gdf = _make_gdf_at(42.36, -71.06, _UTM19N)
    _validate_input_schema(gdf)  # should not raise


# ── _join_points produces EPSG:4326 GeoSeries ─────────────────────────────────

def test_join_points_crs():
    gdf = _make_gdf_at(42.36, -71.06, _UTM19N)
    pts = _join_points(gdf)
    assert pts.crs.to_epsg() == 4326
    pt = pts.iloc[0]
    assert 42.35 < pt.y < 42.37
    assert -71.07 < pt.x < -71.05
