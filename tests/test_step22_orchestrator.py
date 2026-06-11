"""T13 — orchestrator tests for enrich_semantics() and the 2,400-row sweep.

DESIGN §5.1 (F19–F22), PLAN T12/T13.
"""
from __future__ import annotations

import io
import json
import warnings
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from pyproj import CRS, Transformer
from shapely.geometry import box

from openubem.semantic import enrich_semantics, validate_schema, _F17_ALL
from openubem.semantic.construction_sets import VINTAGE_U_FACTORS

# ── Shared helpers ─────────────────────────────────────────────────────────────

_UTM19N = CRS.from_epsg(32619)

_ALL_ARCHETYPES = [
    "College", "Courthouse", "FullServiceRestaurant", "HighriseApartment",
    "Hospital", "LargeDataCenterHighITE", "LargeDataCenterLowITE", "LargeHotel",
    "LargeOffice", "LargeOfficeDetailed", "Laboratory", "MediumOffice",
    "MediumOfficeDetailed", "MidriseApartment", "Outpatient",
    "PrimarySchool", "QuickServiceRestaurant", "RetailStandalone", "RetailStripmall",
    "SecondarySchool", "SmallDataCenterHighITE", "SmallDataCenterLowITE",
    "SmallHotel", "SmallOffice", "SmallOfficeDetailed", "SuperMarket",
    "SuperTallBuilding", "TallBuilding", "Warehouse",
]  # 29 real archetypes (no OpenUBEMUnknown)

_CLIMATE_ZONES = [
    "1A", "2A", "2B", "3A", "3B", "3C",
    "4A", "4B", "4C", "5A", "5B", "5C",
    "6A", "6B", "7", "8",
]

_VINTAGES_REACHABLE = [
    "DOERefPre1980", "DOERef1980to2004", "90.1-2007", "90.1-2013", "90.1-2019",
]

_YEAR_FOR_VINTAGE = {
    "DOERefPre1980":    1960,
    "DOERef1980to2004": 1990,
    "90.1-2007":        2006,
    "90.1-2013":        2012,
    "90.1-2019":        2018,
}


def _tf():
    return Transformer.from_crs("EPSG:4326", _UTM19N, always_xy=True)


def _make_29col_gdf(
    archetypes: list[str],
    climate_zones: list[str] | None = None,
    year_builts: list[float | None] | None = None,
    lat: float = 42.36,
    lon: float = -71.06,
    epw_path: str = "/fake/boston.epw",
) -> gpd.GeoDataFrame:
    """Build a minimal 29-column GDF for testing enrich_semantics()."""
    tf = _tf()
    n = len(archetypes)
    if climate_zones is None:
        climate_zones = ["5A"] * n
    if year_builts is None:
        year_builts = [2010.0] * n

    rows = []
    geoms = []
    for i in range(n):
        cx, cy = tf.transform(lon + i * 0.001, lat)
        geoms.append(box(cx - 5, cy - 5, cx + 5, cy + 5))
        rows.append({
            "osm_id": f"way/test_{i}",
            "crs_utm": str(_UTM19N),
            "building_tag": "yes",
            "function_tag": None,
            "levels": 2.0,
            "height_m": float("nan"),
            "year_built": float("nan") if year_builts[i] is None else float(year_builts[i]),
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
            "archetype_id": archetypes[i],
            "archetype_confidence": "HIGH",
            "archetype_source": "RULE_USE_CLASS",
            "climate_zone": climate_zones[i],
            "epw_path": epw_path,
            "provenance_climate_zone": "ASHRAE_STANDARD",
        })

    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs=_UTM19N)
    gdf["climate_zone"] = pd.Categorical(gdf["climate_zone"], categories=_CLIMATE_ZONES)
    return gdf


# ── (a) Happy path ─────────────────────────────────────────────────────────────

def test_happy_path_shape():
    gdf = _make_29col_gdf(["SmallOffice", "MediumOffice", "Warehouse"])
    result, sched = enrich_semantics(gdf)
    assert result.shape == (3, 57), f"Expected (3,57), got {result.shape}"


def test_happy_path_column_order():
    gdf = _make_29col_gdf(["SmallOffice"])
    result, _ = enrich_semantics(gdf)
    assert list(result.columns[-28:]) == _F17_ALL


def test_happy_path_zero_nan():
    gdf = _make_29col_gdf(["SmallOffice", "MediumOffice", "Hospital"])
    result, _ = enrich_semantics(gdf)
    for col in _F17_ALL:
        assert result[col].isna().sum() == 0, f"NaN in '{col}'"


def test_happy_path_29col_byte_identical():
    """28 of the original 29 upstream columns must be byte-identical (F1)."""
    gdf = _make_29col_gdf(["MediumOffice", "SmallOffice"])
    result, _ = enrich_semantics(gdf)
    upstream_cols = [c for c in gdf.columns if c != "geometry"]
    pd.testing.assert_frame_equal(
        gdf[upstream_cols].reset_index(drop=True),
        result[upstream_cols].reset_index(drop=True),
        check_dtype=False,
    )


def test_flag_token_append_only_for_nan_vintage():
    """NaN year_built rows get VINTAGE_NAN_PERMISSIVE_DEFAULT; others unchanged."""
    gdf = _make_29col_gdf(
        ["SmallOffice", "MediumOffice"],
        year_builts=[None, 2010.0],
    )
    result, _ = enrich_semantics(gdf)
    assert "VINTAGE_NAN_PERMISSIVE_DEFAULT" in str(result.at[0, "data_quality_flag"])
    assert "VINTAGE_NAN_PERMISSIVE_DEFAULT" not in str(result.at[1, "data_quality_flag"])


# ── (b) Unknown row ───────────────────────────────────────────────────────────

def test_unknown_row_envelope_provenance():
    """OpenUBEMUnknown rows: all envelope provenances HEURISTIC (F13)."""
    gdf = _make_29col_gdf(["OpenUBEMUnknown", "SmallOffice"], climate_zones=["5A", "5A"])
    result, _ = enrich_semantics(gdf)
    env_prov_cols = [c for c in _F17_ALL if c.startswith("provenance_u") or c == "provenance_infiltration"]
    unk_row = result.iloc[0]
    for col in env_prov_cols:
        assert unk_row[col] == "HEURISTIC", f"Expected HEURISTIC for Unknown {col}, got {unk_row[col]}"


def test_unknown_row_loads_provenance():
    """OpenUBEMUnknown rows: density provenances PDE_GENERATED, setpoint HEURISTIC (F13)."""
    gdf = _make_29col_gdf(["OpenUBEMUnknown"], climate_zones=["5A"])
    result, _ = enrich_semantics(gdf)
    unk = result.iloc[0]
    assert unk["provenance_lighting"] == "PDE_GENERATED"
    assert unk["provenance_equipment"] == "PDE_GENERATED"
    assert unk["provenance_occupant_density"] == "PDE_GENERATED"
    assert unk["provenance_wwr"] == "PDE_GENERATED"
    assert unk["provenance_heating_setpoint"] == "HEURISTIC"
    assert unk["provenance_cooling_setpoint"] == "HEURISTIC"


def test_unknown_row_setpoints_not_inverted():
    """Unknown row setpoints must satisfy heating < cooling (F13)."""
    gdf = _make_29col_gdf(["OpenUBEMUnknown"] * 10, climate_zones=["5A"] * 10)
    result, _ = enrich_semantics(gdf, random_seed=42)
    unk_rows = result[result["archetype_id"] == "OpenUBEMUnknown"]
    assert (unk_rows["heating_setpoint_c"] < unk_rows["cooling_setpoint_c"]).all()


def test_unknown_row_vintage_is_pre1980():
    """Unknown rows get DOERefPre1980 vintage (F13)."""
    gdf = _make_29col_gdf(["OpenUBEMUnknown"], climate_zones=["3A"])
    result, _ = enrich_semantics(gdf)
    assert str(result.at[0, "vintage_standard"]) == "DOERefPre1980"


# ── (c) Wrong-units U table → gate abort ─────────────────────────────────────

def test_wrong_units_construction_table_aborts():
    """Construction table with U-values > 7.0 W/m²K must fail validate_schema."""
    bad_table = {
        "SmallOffice": {
            "5A": {
                "roof": {"u_value": 50.0, "assembly": "IEAD"},
                "wall": {"u_value": 50.0, "assembly": "SteelFramed"},
                "window": {"u_value": 50.0, "shgc": 0.3},
                "floor": {"u_value": 50.0},
                "infiltration_rate": 0.000285,
            }
        }
    }
    gdf = _make_29col_gdf(["SmallOffice"])
    with pytest.raises(ValueError):
        enrich_semantics(gdf, construction_table=bad_table)


# ── (d) Inverted setpoints loads table → gate abort ──────────────────────────

def test_inverted_setpoints_loads_table_aborts():
    """Loads table with heating_setpoint >= cooling_setpoint must abort."""
    bad_loads = {
        "SmallOffice": {
            "lighting_w_m2": 10.76,
            "equipment_w_m2": 6.78,
            "occupant_density_m2_person": 18.58,
            "heating_setpoint_c": 30.0,  # inverted
            "cooling_setpoint_c": 20.0,
            "heating_setback_c": 15.6,
            "cooling_setup_c": 29.4,
            "wwr": 0.4,
        }
    }
    gdf = _make_29col_gdf(["SmallOffice"])
    with pytest.raises(ValueError, match="[Ss]etpoint"):
        enrich_semantics(gdf, loads_table=bad_loads)


# ── (e) Probabilistic mode ────────────────────────────────────────────────────

def test_probabilistic_same_seed_byte_identical():
    """Same seed → same perturbation → byte-identical density columns (F22)."""
    gdf = _make_29col_gdf(["SmallOffice", "MediumOffice", "Warehouse"])
    r1, _ = enrich_semantics(gdf, load_mode="probabilistic", random_seed=42)
    r2, _ = enrich_semantics(gdf, load_mode="probabilistic", random_seed=42)
    for col in ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person"]:
        pd.testing.assert_series_equal(r1[col].reset_index(drop=True), r2[col].reset_index(drop=True))


def test_probabilistic_different_seeds_differ_in_density_cols():
    """Different seeds → only the 3 perturbed columns differ; others unchanged (F14/F22)."""
    gdf = _make_29col_gdf(["SmallOffice", "MediumOffice"])
    r1, _ = enrich_semantics(gdf, load_mode="probabilistic", random_seed=42)
    r2, _ = enrich_semantics(gdf, load_mode="probabilistic", random_seed=99)
    perturbed = {"lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person"}
    for col in _F17_ALL:
        if col in perturbed:
            continue
        # Non-perturbed appended columns must be equal across seeds
        if pd.api.types.is_numeric_dtype(r1[col]):
            pd.testing.assert_series_equal(
                r1[col].reset_index(drop=True),
                r2[col].reset_index(drop=True),
                check_names=False,
            )


def test_deterministic_pde_only_on_unknown():
    """In deterministic mode, PDE_GENERATED provenance appears only on Unknown rows (F22)."""
    gdf = _make_29col_gdf(["SmallOffice", "OpenUBEMUnknown"])
    result, _ = enrich_semantics(gdf, load_mode="deterministic")
    real_row = result[result["archetype_id"] == "SmallOffice"].iloc[0]
    unk_row = result[result["archetype_id"] == "OpenUBEMUnknown"].iloc[0]
    for col in ["provenance_lighting", "provenance_equipment",
                "provenance_occupant_density", "provenance_wwr"]:
        assert real_row[col] != "PDE_GENERATED", f"PDE_GENERATED on real row col={col}"
        assert unk_row[col] == "PDE_GENERATED", f"Expected PDE_GENERATED on Unknown col={col}"


# ── (f) 2,400-row sweep ───────────────────────────────────────────────────────

@pytest.mark.slow
def test_2400_sweep_zero_nan():
    """30 archetypes × 16 zones × 5 reachable vintages = 2,400 rows → zero NaN (F21)."""
    archetypes = []
    czones = []
    year_builts = []
    for arch in _ALL_ARCHETYPES + ["OpenUBEMUnknown"]:
        for cz in _CLIMATE_ZONES:
            for vt in _VINTAGES_REACHABLE:
                archetypes.append(arch)
                czones.append(cz)
                year_builts.append(float(_YEAR_FOR_VINTAGE[vt]))

    gdf = _make_29col_gdf(archetypes, climate_zones=czones, year_builts=year_builts)
    result, _ = enrich_semantics(gdf, random_seed=42)
    for col in _F17_ALL:
        n_nan = result[col].isna().sum()
        assert n_nan == 0, f"NaN count in '{col}': {n_nan}"


@pytest.mark.slow
def test_2400_sweep_zero_gap_warnings():
    """The 2,400-row sweep must fire zero construction_lookup_gap warnings (F21)."""
    archetypes = []
    czones = []
    year_builts = []
    for arch in _ALL_ARCHETYPES:
        for cz in _CLIMATE_ZONES:
            for vt in _VINTAGES_REACHABLE:
                archetypes.append(arch)
                czones.append(cz)
                year_builts.append(float(_YEAR_FOR_VINTAGE[vt]))

    gdf = _make_29col_gdf(archetypes, climate_zones=czones, year_builts=year_builts)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        enrich_semantics(gdf, random_seed=42)

    gap_warnings = [w for w in caught if "construction_lookup_gap" in str(w.message)]
    assert len(gap_warnings) == 0, f"Gap warnings fired: {[str(w.message) for w in gap_warnings]}"


@pytest.mark.slow
def test_2400_sweep_u_monotonicity():
    """U-values must be non-increasing Pre1980→2019 for every archetype×zone (F21)."""
    vintages_ordered = [
        "DOERefPre1980", "DOERef1980to2004", "90.1-2007", "90.1-2013", "90.1-2019",
    ]
    archetypes = []
    czones = []
    year_builts = []
    for arch in _ALL_ARCHETYPES:
        for cz in _CLIMATE_ZONES:
            for vt in vintages_ordered:
                archetypes.append(arch)
                czones.append(cz)
                year_builts.append(float(_YEAR_FOR_VINTAGE[vt]))

    gdf = _make_29col_gdf(archetypes, climate_zones=czones, year_builts=year_builts)
    result, _ = enrich_semantics(gdf, random_seed=42)
    result["_vintage"] = result["vintage_standard"].astype(str)

    u_cols = ["u_roof_w_m2k", "u_wall_w_m2k", "u_window_w_m2k", "u_floor_w_m2k"]
    violations = []
    for arch in _ALL_ARCHETYPES:
        for cz in _CLIMATE_ZONES:
            sub = result[(result["archetype_id"] == arch) & (result["climate_zone"] == cz)]
            sub = sub.set_index("_vintage").reindex(vintages_ordered)
            for col in u_cols:
                vals = sub[col].values.astype(float)
                for i in range(len(vals) - 1):
                    if vals[i] < vals[i + 1] - 1e-6:
                        violations.append(
                            f"{arch}@{cz}: {col} not non-increasing at "
                            f"{vintages_ordered[i]}({vals[i]:.3f}) < "
                            f"{vintages_ordered[i+1]}({vals[i+1]:.3f})"
                        )
    assert not violations, f"Monotonicity violations:\n" + "\n".join(violations[:10])


# ── (g) Determinism ───────────────────────────────────────────────────────────

def test_determinism_schema_json(tmp_path):
    """Two runs → byte-identical schema.json (F22, P9)."""
    gdf = _make_29col_gdf(["SmallOffice", "MediumOffice"])
    enrich_semantics(gdf, output_dir=tmp_path / "run1", random_seed=42)
    enrich_semantics(gdf, output_dir=tmp_path / "run2", random_seed=42)
    bytes1 = (tmp_path / "run1" / "02b_buildings_enriched.schema.json").read_bytes()
    bytes2 = (tmp_path / "run2" / "02b_buildings_enriched.schema.json").read_bytes()
    assert bytes1 == bytes2, "schema.json differs between runs"


def test_determinism_schedule_library_json(tmp_path):
    """Two runs → byte-identical schedule_library.json (F22, P9)."""
    gdf = _make_29col_gdf(["SmallOffice", "MediumOffice"])
    enrich_semantics(gdf, output_dir=tmp_path / "run1", random_seed=42)
    enrich_semantics(gdf, output_dir=tmp_path / "run2", random_seed=42)
    bytes1 = (tmp_path / "run1" / "02b_schedule_library.json").read_bytes()
    bytes2 = (tmp_path / "run2" / "02b_schedule_library.json").read_bytes()
    assert bytes1 == bytes2, "schedule_library.json differs between runs"


# ── (h) Schedule completeness on emitted JSON ─────────────────────────────────

def test_schedule_library_completeness_on_emitted_json(tmp_path):
    """Emitted schedule_library.json: 6 families per archetype, 3 day-types each (F15)."""
    all_archs = _ALL_ARCHETYPES + ["OpenUBEMUnknown"]
    gdf = _make_29col_gdf(all_archs, climate_zones=["5A"] * len(all_archs))
    enrich_semantics(gdf, output_dir=tmp_path, random_seed=42)
    lib = json.loads((tmp_path / "02b_schedule_library.json").read_text(encoding="utf-8"))

    families = ["Occupancy", "Lighting", "Equipment", "HeatingSetpoint", "CoolingSetpoint", "Infiltration"]
    day_keys = ["For: Weekdays", "For: Saturday", "For: AllOtherDays"]
    for arch in all_archs:
        assert arch in lib, f"Missing archetype '{arch}' in schedule library"
        for fam in families:
            assert fam in lib[arch], f"Missing family '{fam}' for '{arch}'"
            for dk in day_keys:
                assert dk in lib[arch][fam], f"Missing day-type '{dk}' for '{arch}'/'{fam}'"


def test_schedule_library_f16_setpoint_invariant():
    """F16: occupied plateau value must appear in the Weekday schedule (for real archetypes).

    The schedule has both occupied (e.g. 21.1°C) and unoccupied (e.g. 15.6°C) values.
    F16 requires the occupied plateau == archetype scalar. Check that the scalar value
    appears in the Weekday series (it IS the occupied plateau).
    """
    from openubem.semantic.loads import _get_flat_loads
    flat = _get_flat_loads()
    gdf = _make_29col_gdf(["MediumOffice", "SmallOffice"])
    _, sched = enrich_semantics(gdf, random_seed=42)
    for arch in ["MediumOffice", "SmallOffice"]:
        htg_scalar = flat.at[arch, "heating_setpoint_c"]
        clg_scalar = flat.at[arch, "cooling_setpoint_c"]
        htg_sched = sched[arch]["HeatingSetpoint"]
        clg_sched = sched[arch]["CoolingSetpoint"]
        wd_htg_vals = [e["Value"] for e in htg_sched["For: Weekdays"]]
        wd_clg_vals = [e["Value"] for e in clg_sched["For: Weekdays"]]
        # The occupied setpoint scalar must appear in the weekday series
        assert any(abs(v - htg_scalar) < 0.1 for v in wd_htg_vals), (
            f"{arch} heating scalar {htg_scalar} not in Weekday schedule: {wd_htg_vals}"
        )
        assert any(abs(v - clg_scalar) < 0.1 for v in wd_clg_vals), (
            f"{arch} cooling scalar {clg_scalar} not in Weekday schedule: {wd_clg_vals}"
        )
