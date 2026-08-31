"""EU-13B T01/T02/T03/T04/T07 acceptance tests.

Scope note: only Madrid, Lyon and London side-cars are asserted against --
``IT-BOL-GALVANI2`` is excluded from this task's re-emit (its layout-binding
fix is ``EU-14B`` T01) and its side-cars still describe the pre-EU-13B
geometry, so it is intentionally not part of the conservation population
here.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from shapely.geometry import Polygon, box

from openubem.geometry.european_residential import (
    RULED_GRID_MAX_DWELLINGS_PER_FLOOR,
    EuropeanFloorAllocation,
    allocate_european_dwellings,
    audit_european_floor_partition,
    classify_building_morphology,
    european_building_layout_to_zone_specs,
    fit_quadrilateral_domain,
    generate_european_building_dwelling_layout,
    generate_european_grid_layout,
    regularize_footprint_orthogonal,
)

ROOT = Path(__file__).resolve().parents[2]
EU13B_DISTRICTS = ("ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS")


def _sidecar_paths() -> list[Path]:
    paths: list[Path] = []
    for district in EU13B_DISTRICTS:
        layouts_dir = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / district / "layouts"
        paths.extend(sorted(layouts_dir.rglob("*.json")))
    return paths


SIDECARS = _sidecar_paths()


# --- T01: conservation ------------------------------------------------------


@pytest.mark.skipif(not SIDECARS, reason="EU-11 side-cars not present in this environment")
def test_t01_emitted_zone_count_conserves_declared_total():
    checked = 0
    failures = []
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not str(data.get("geometry_outcome", "")).startswith("DWELLING_LAYOUT_EMITTED"):
            continue
        checked += 1
        # A storey group spanning multiple physical floors (a single dwelling
        # extruded across them, e.g. a multi-storey SFH/TH) repeats the same
        # zone name once per physical floor entry for the viewer's per-floor
        # slicing, so conservation is over *distinct* zone names, not a sum
        # of each floor's zone-list length.
        zone_names = {zone["name"] for floor in data["floors"] for zone in floor["zones"]}
        emitted = len(zone_names)
        if emitted != data["dwellings_total"]:
            failures.append((path.name, emitted, data["dwellings_total"]))
    assert checked > 0
    assert failures == [], f"{len(failures)}/{checked} side-cars do not conserve: {failures[:5]}"


@pytest.mark.skipif(not SIDECARS, reason="EU-11 side-cars not present in this environment")
def test_t02_no_storey_exceeds_the_ruled_grid_ceiling():
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not str(data.get("geometry_outcome", "")).startswith("DWELLING_LAYOUT_EMITTED"):
            continue
        for floor in data["floors"]:
            assert len(floor["zones"]) <= RULED_GRID_MAX_DWELLINGS_PER_FLOOR, path.name


@pytest.mark.skipif(not SIDECARS, reason="EU-11 side-cars not present in this environment")
def test_t02_density_exceeded_reason_present_in_fallbacks():
    seen_reason = False
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("fallback_reason") == "DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8":
            seen_reason = True
            assert data.get("observed_max_per_floor", 0) > RULED_GRID_MAX_DWELLINGS_PER_FLOOR
    assert seen_reason, "expected at least one DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8 fallback in the fleet"


@pytest.mark.parametrize("seed", range(20))
def test_t01_property_random_totals_conserve_exactly(seed):
    rng = random.Random(seed)
    n_total = rng.randint(1, 400)
    n_floors = rng.randint(1, 30)
    allocation = allocate_european_dwellings(
        archetype_id="x", building_type="MFH", n_apartment=n_total, n_storey=n_floors, plate_area_m2=500.0,
    )
    assert sum(fa.dwelling_count for fa in allocation.floor_allocations) == allocation.dwelling_count


def test_t01_way_51781396_like_case_gives_69_not_85():
    footprint = box(0, 0, 20, 15.6)  # ~312 m^2, matches EXAMPLE building 8's plate area
    allocation = allocate_european_dwellings(
        archetype_id="x", building_type="AB", n_apartment=69, n_storey=17, plate_area_m2=footprint.area,
    )
    building_layout = generate_european_building_dwelling_layout(footprint, floor_allocations=allocation.floor_allocations)
    assert building_layout.dwelling_layout_emitted
    zones = european_building_layout_to_zone_specs(building_layout, building_id="way/test51781396", height_m=3.0)
    # EU-15 T05: the list can also carry the carved, unconditioned
    # circulation zone (conditioned=False) alongside the 69 dwellings --
    # this test's own scope is dwelling-count conservation, so it filters
    # to conditioned zones rather than the raw list length.
    dwelling_zones = [z for z in zones if z.get("conditioned") is not False]
    assert len(dwelling_zones) == 69


# --- T03: footprint regularization ------------------------------------------


@pytest.mark.parametrize(
    "name,polygon",
    [
        ("rectangle", box(0, 0, 20, 12)),
        ("l_shape", Polygon([(0, 0), (20, 0), (20, 8), (10, 8), (10, 15), (0, 15)])),
        ("u_shape", Polygon([(0, 0), (20, 0), (20, 15), (14, 15), (14, 6), (6, 6), (6, 15), (0, 15)])),
        ("cross", Polygon([(10, 0), (20, 0), (20, 10), (30, 10), (30, 20), (20, 20), (20, 30), (10, 30), (10, 20), (0, 20), (0, 10), (10, 10)])),
        ("notched", Polygon([(0, 0), (20, 0), (20, 12), (11, 12), (11, 11), (10, 11), (10, 12), (0, 12)])),
    ],
)
def test_t03_golden_regularization_preserves_area_and_quad(name, polygon):
    result = regularize_footprint_orthogonal(polygon)
    assert result.vertices_regularized == 4
    assert result.plate_area_delta_fraction < 0.02, f"{name}: {result.plate_area_delta_fraction}"
    assert result.regularized_polygon.exterior.is_ccw


def test_t03_fit_quadrilateral_domain_imports_nothing_from_partitioner():
    import inspect

    from openubem.geometry import european_residential as module

    source = inspect.getsource(module.fit_quadrilateral_domain)
    for forbidden in ("generate_european_grid_layout", "generate_european_dwelling_layout", "classify_building_morphology"):
        assert forbidden not in source
    source2 = inspect.getsource(module.regularize_footprint_orthogonal)
    for forbidden in ("generate_european_grid_layout", "generate_european_dwelling_layout", "classify_building_morphology"):
        assert forbidden not in source2


# --- T04: ruled grid ---------------------------------------------------------


@pytest.mark.parametrize(
    "count,expected_grid",
    [(1, "ruled_grid_1x1"), (2, "ruled_grid_2x1"), (3, "ruled_grid_2x2"), (4, "ruled_grid_2x2"),
     (5, "ruled_grid_3x2"), (6, "ruled_grid_3x2"), (7, "ruled_grid_4x2"), (8, "ruled_grid_4x2")],
)
def test_t04_density_grid_mapping_and_area_conservation(count, expected_grid):
    plate = fit_quadrilateral_domain(box(0, 0, 24, 16))
    result = generate_european_grid_layout(plate, dwelling_count=count)
    assert result.dwelling_layout_emitted
    assert result.grid == expected_grid
    assert len(result.dwelling_polygons) == count
    assert result.partition_audit.passed


def test_t04_2x2_corner_units_have_two_exterior_facades():
    plate = fit_quadrilateral_domain(box(0, 0, 20, 20))
    result = generate_european_grid_layout(plate, dwelling_count=4)
    plate_boundary = plate.boundary
    for polygon in result.dwelling_polygons:
        exterior_edges = 0
        coords = list(polygon.exterior.coords)[:-1]
        for i in range(len(coords)):
            a, b = coords[i], coords[(i + 1) % len(coords)]
            midpoint = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            from shapely.geometry import Point
            if Point(midpoint).distance(plate_boundary) < 1e-6:
                exterior_edges += 1
        assert exterior_edges >= 2


def test_t04_3x2_middle_units_have_one_exterior_facade():
    plate = fit_quadrilateral_domain(box(0, 0, 30, 15))
    result = generate_european_grid_layout(plate, dwelling_count=6)
    assert len(result.dwelling_polygons) == 6
    # Sort by centroid x: columns are [0,1] left, [2,3] middle, [4,5] right.
    ordered = sorted(result.dwelling_polygons, key=lambda p: p.centroid.x)
    middle = ordered[2:4]
    for polygon in middle:
        contact = polygon.boundary.intersection(plate.boundary.buffer(1e-6)).length
        assert contact < polygon.length * 0.4


def test_t04_relation_3730743_like_building_is_refused_not_approximated():
    footprint = box(0, 0, 55, 34)  # ~1870 m^2, matches EXAMPLE building 12's plate area
    allocation = allocate_european_dwellings(
        archetype_id="x", building_type="AB", n_apartment=156, n_storey=5, plate_area_m2=footprint.area,
    )
    building_layout = generate_european_building_dwelling_layout(footprint, floor_allocations=allocation.floor_allocations)
    assert not building_layout.dwelling_layout_emitted
    assert building_layout.fallback_reason == "DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8"


# --- T05: morphological branching -------------------------------------------


def test_t05_slab_routes_to_linear_gallery():
    slab = box(0, 0, 60, 10)
    assert classify_building_morphology(slab).route == "i_shape_linear_gallery"


def test_t05_l_shape_routes_to_decomposition():
    L = Polygon([(0, 0), (20, 0), (20, 8), (10, 8), (10, 15), (0, 15)])
    assert classify_building_morphology(L).route == "l_shape_decomposition"


def test_t05_point_block_route_for_compact_convex_plate():
    plate = box(0, 0, 18, 14)
    assert classify_building_morphology(plate).route == "point_block_grid"


def test_t05_gis_digitization_noise_does_not_falsely_trigger_l_shape():
    # A near-rectangular plate with a sub-metre jaggy vertex from GIS noise
    # must not be routed away from the ruled point-block grid.
    noisy = Polygon([(0, 0), (20, 0), (20, 14), (20.05, 14.02), (10, 14), (0, 14)])
    route = classify_building_morphology(noisy).route
    assert route == "point_block_grid"


# --- T07: habitability retry and pop-up header ------------------------------


@pytest.mark.skipif(not SIDECARS, reason="EU-11 side-cars not present in this environment")
def test_t07b_unconditioned_core_flag_is_now_carved_per_d_eu_39():
    # D-EU-39 (2026-08-30) resolved D-EU-36's carve-vs-add half as CARVE
    # (EU-15 T05): has_unconditioned_core is no longer hardcoded False --
    # it is true wherever at least one storey carried and emitted the
    # unconditioned stair core / corridor spine.
    core_true = 0
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("has_unconditioned_core"):
            core_true += 1
            gross = data.get("gross_footprint_area_m2")
            conditioned = data.get("conditioned_floor_area_m2")
            assert gross is not None and conditioned is not None and conditioned < gross, path.name
    assert core_true > 0
