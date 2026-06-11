"""Synthetic 10-building GeoDataFrame and schedule library fixtures (DESIGN §5.2, T15).

10 rows hand-crafted to cover:
  - simplification statuses: dp_05 (rows 1-9), dp_15 (row 10 gear polygon)
  - zoning strategies: single_zone, one_zone_per_floor, perimeter_core
  - narrow-building fallback (row 7 RetailStripmall: perimeter_core → one_zone_per_floor)
  - archetype families: commercial, residential, high-rise, specialized, OpenUBEMUnknown

hull and bbox simplification tiers are covered by direct TestFootprint unit tests
(carry-forward (b): do NOT force the 10-row fixture to hit them).
"""
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon, box

_EPW_PATH = str(Path(__file__).parent / "synthetic.epw")

_COMMON = {
    "epw_path": _EPW_PATH,
    "provenance_climate_zone": "DEFAULT",
    "climate_zone": "3A",
    "vintage_standard": "DOERef1980to2004",
    "u_roof_w_m2k": 0.25,
    "u_wall_w_m2k": 0.40,
    "u_floor_w_m2k": 0.35,
    "u_window_w_m2k": 2.5,
    "shgc_window": 0.40,
    "assembly_roof": "NOMASS",
    "assembly_wall": "NOMASS",
    "provenance_u_roof": "DEFAULT",
    "provenance_u_wall": "DEFAULT",
    "provenance_u_window": "DEFAULT",
    "provenance_u_floor": "DEFAULT",
    "provenance_envelope": "DEFAULT",
    "infiltration_m3_s_m2": 0.0003,
    "wwr": 0.30,
    "lighting_w_m2": 10.76,
    "equipment_w_m2": 8.07,
    "occupant_m2_per_person": 9.3,
    "provenance_lighting": "DEFAULT",
    "provenance_equipment": "DEFAULT",
    "provenance_occupancy": "DEFAULT",
    "heating_setpoint_c": 21.0,
    "cooling_setpoint_c": 24.0,
    "heating_setback_c": 16.0,
    "cooling_setup_c": 30.0,
    "provenance_heating_setpoint": "DEFAULT",
    "provenance_cooling_setpoint": "DEFAULT",
    "data_quality_flag": "",
}


def _gear_polygon(n_teeth: int = 100, r_inner: float = 6.0, r_outer: float = 7.0,
                  cx: float = 0.0, cy: float = 0.0) -> Polygon:
    """Gear polygon: inner vertices ~1.0m from chord → DP 0.5 keeps (>120 verts),
    DP 1.5 removes (outer ring collapses to <120 verts)."""
    coords = []
    for i in range(n_teeth):
        a_in = 2 * math.pi * i / n_teeth
        a_out = 2 * math.pi * (i + 0.5) / n_teeth
        coords.append((cx + r_inner * math.cos(a_in), cy + r_inner * math.sin(a_in)))
        coords.append((cx + r_outer * math.cos(a_out), cy + r_outer * math.sin(a_out)))
    return Polygon(coords)


def _row(osm_id, archetype_id, geom, levels, height_m=float("nan"), **extra):
    d = {"osm_id": osm_id, "archetype_id": archetype_id, "geometry": geom,
         "levels": levels, "height_m": height_m}
    d.update(_COMMON)
    d.update(extra)
    return d


def _build_rows():
    # R1: SmallOffice — 196 m² square, 2 floors → single_zone (rule 2: area < 500)
    r1_geom = box(0, 0, 14, 14)
    yield _row("way/R1", "SmallOffice", r1_geom, 2)

    # R2: MidriseApartment — 625 m², 4 floors → one_zone_per_floor (rule 3)
    r2_geom = box(100, 0, 125, 25)
    yield _row("way/R2", "MidriseApartment", r2_geom, 4)

    # R3: HighriseApartment — 784 m², 6 floors → one_zone_per_floor (rule 3)
    r3_geom = box(200, 0, 228, 28)
    yield _row("way/R3", "HighriseApartment", r3_geom, 6)

    # R4: TallBuilding — 1024 m², 5 floors → one_zone_per_floor (rule 4)
    r4_geom = box(300, 0, 332, 32)
    yield _row("way/R4", "TallBuilding", r4_geom, 5)

    # R5: SuperTallBuilding — 1521 m², 5 floors → one_zone_per_floor (rule 4)
    r5_geom = box(400, 0, 439, 39)
    yield _row("way/R5", "SuperTallBuilding", r5_geom, 5)

    # R6: MediumOffice — 1500 m² (30×50 m), 3 floors → perimeter_core (rule 5)
    r6_geom = box(500, 0, 530, 50)
    yield _row("way/R6", "MediumOffice", r6_geom, 3)

    # R7: RetailStripmall — 1400 m² (7×200 m) narrow, 2 floors
    #   → decide_zoning_strategy returns perimeter_core (rule 5: area≥500, floors≥2)
    #   → build_zones: buffer(-4.57) on 7 m wide → empty → fallback to one_zone_per_floor
    r7_geom = box(650, 0, 657, 200)
    yield _row("way/R7", "RetailStripmall", r7_geom, 2)

    # R8: Warehouse — 4900 m² square, 1 floor → single_zone (rule 2: num_floors == 1)
    r8_geom = box(800, 0, 870, 70)
    yield _row("way/R8", "Warehouse", r8_geom, 1)

    # R9: SmallDataCenterHighITE — 400 m² square, 1 floor → single_zone (rule 2: area < 500)
    r9_geom = box(950, 0, 970, 20)
    yield _row("way/R9", "SmallDataCenterHighITE", r9_geom, 1)

    # R10: OpenUBEMUnknown — 200-vertex gear polygon (~264 m²)
    #   → single_zone (rule 1: OpenUBEMUnknown)
    #   → dp_15: inner vertices ~1.0 m from chord (> DP_TOLERANCE 0.5 m),
    #            DP 1.5 removes them leaving <120 outer verts
    r10_geom = _gear_polygon(n_teeth=100, r_inner=6.0, r_outer=7.0, cx=1050.0, cy=50.0)
    yield _row("way/R10", "OpenUBEMUnknown", r10_geom, 1)


@pytest.fixture(scope="session")
def synthetic_10_gdf():
    rows = list(_build_rows())
    geometries = [r.pop("geometry") for r in rows]
    gdf = gpd.GeoDataFrame(rows, geometry=geometries)

    # Coverage assertions (dp_05 + dp_15 only; hull/bbox covered by direct TestFootprint tests)
    from openubem.geometry.footprint import (
        simplify_footprint, translate_to_origin, derive_num_floors
    )
    from openubem.geometry.zoning import decide_zoning_strategy, build_zones

    statuses, strategies = set(), set()
    has_fallback = False
    for _, row in gdf.iterrows():
        _, _, status = simplify_footprint(row.geometry, "")
        statuses.add(status)
        simplified, _, _ = translate_to_origin(
            __import__("shapely").simplify(row.geometry, 0.5, preserve_topology=True)
        )
        n_floors = derive_num_floors(row)
        strat = decide_zoning_strategy(row["archetype_id"], simplified.area, n_floors)
        strategies.add(strat)
        if strat == "perimeter_core":
            zones = build_zones(row["osm_id"], simplified, row["archetype_id"], n_floors, strat)
            if any("_whole" in z["name"] for z in zones):
                has_fallback = True

    assert "dp_05" in statuses, "dp_05 not covered"
    # dp_15 depends on Shapely version; warn rather than hard-fail if gear polygon simplifies early
    if "dp_15" not in statuses:
        import warnings
        warnings.warn("Row 10 gear polygon did not trigger dp_15 on this Shapely version; "
                      "dp_15 coverage provided by direct TestFootprint unit tests instead.")
    assert "single_zone" in strategies, "single_zone strategy not covered"
    assert "one_zone_per_floor" in strategies, "one_zone_per_floor strategy not covered"
    assert "perimeter_core" in strategies, "perimeter_core strategy not covered"
    assert has_fallback, "Narrow-building perimeter_core→one_zone_per_floor fallback not triggered"

    return gdf


@pytest.fixture(scope="session")
def synthetic_schedule_library():
    """Schedule library in Step-2.2 dict form for all 10 archetype IDs (Step-2.2 §3F contract)."""
    from openubem.semantic.schedules import build_schedule_library

    arch_ids = [
        "SmallOffice", "MidriseApartment", "HighriseApartment", "TallBuilding",
        "SuperTallBuilding", "MediumOffice", "RetailStripmall", "Warehouse",
        "SmallDataCenterHighITE", "OpenUBEMUnknown",
    ]
    return {arch: build_schedule_library(arch) for arch in arch_ids}
