"""Tests for openubem.geometry.zoning (T06)."""
import pytest
from shapely.geometry import Polygon

from openubem.geometry.zoning import build_zones, decide_zoning_strategy


def _square(side: float) -> Polygon:
    return Polygon([(0, 0), (side, 0), (side, side), (0, side)])


class TestZoning:
    # --- decide_zoning_strategy: 6 rules ---

    def test_rule1_one_floor_small_area(self):
        # num_floors==1 always → single_zone regardless of footprint
        assert decide_zoning_strategy("MediumOffice", 200.0, 1) == "single_zone"

    def test_rule1_one_floor_large_area(self):
        assert decide_zoning_strategy("MediumOffice", 2000.0, 1) == "single_zone"

    def test_rule1_one_floor_unknown(self):
        assert decide_zoning_strategy("OpenUBEMUnknown", 1000.0, 1) == "single_zone"

    def test_multi_floor_small_area_office(self):
        # footprint<500, multi-floor, non-residential → one_zone_per_floor (was single_zone before fix)
        assert decide_zoning_strategy("MediumOffice", 300.0, 4) == "one_zone_per_floor"

    def test_multi_floor_small_area_one_floor_still_single(self):
        # same footprint, but 1 floor → single_zone
        assert decide_zoning_strategy("MediumOffice", 300.0, 1) == "single_zone"

    def test_midrise_apartment_multi_floor(self):
        # MidriseApartment is in _ONE_PER_FLOOR → one_zone_per_floor
        assert decide_zoning_strategy("MidriseApartment", 300.0, 3) == "one_zone_per_floor"

    def test_midrise_apartment_large_footprint(self):
        # even large footprint, MidriseApartment stays one_zone_per_floor
        assert decide_zoning_strategy("MidriseApartment", 800.0, 5) == "one_zone_per_floor"

    def test_highrise_apartment(self):
        assert decide_zoning_strategy("HighriseApartment", 900.0, 8) == "one_zone_per_floor"

    def test_tall_building(self):
        assert decide_zoning_strategy("TallBuilding", 1000.0, 25) == "one_zone_per_floor"

    def test_supertall_building(self):
        assert decide_zoning_strategy("SuperTallBuilding", 1500.0, 45) == "one_zone_per_floor"

    def test_perimeter_core_large_commercial(self):
        # footprint>=500, non-residential, not in _ONE_PER_FLOOR → perimeter_core
        assert decide_zoning_strategy("MediumOffice", 1500.0, 5) == "perimeter_core"

    def test_perimeter_core_large_commercial_2_floors(self):
        assert decide_zoning_strategy("LargeOffice", 800.0, 2) == "perimeter_core"

    def test_unknown_archetype_multi_floor_routes_one_per_floor(self):
        # OpenUBEMUnknown with multi-floor → one_zone_per_floor (excluded from perimeter_core)
        assert decide_zoning_strategy("OpenUBEMUnknown", 1000.0, 5) == "one_zone_per_floor"

    def test_small_office_multi_floor_small_area(self):
        # was single_zone before fix; now one_zone_per_floor
        assert decide_zoning_strategy("SmallOffice", 300.0, 3) == "one_zone_per_floor"

    # --- build_zones ---

    def test_single_zone_produces_one_dict(self):
        sq = _square(10.0)
        zones = build_zones("b1", sq, "SmallOffice", 1, "single_zone")
        assert len(zones) == 1
        assert zones[0]["name"] == "b1_F0_whole"
        assert abs(zones[0]["z_floor"]) < 1e-9
        assert abs(zones[0]["height_m"] - 3.5) < 1e-9

    def test_one_zone_per_floor_produces_n_dicts(self):
        sq = _square(20.0)
        zones = build_zones("b2", sq, "MidriseApartment", 5, "one_zone_per_floor")
        assert len(zones) == 5
        names = [z["name"] for z in zones]
        assert names == [f"b2_F{i}_whole" for i in range(5)]

    def test_perimeter_core_30x30_5floors(self):
        sq = _square(30.0)
        zones = build_zones("b3", sq, "MediumOffice", 5, "perimeter_core")
        # R7: build_zones returns ONE core/perim placeholder; extrude_geometry expands it.
        assert len(zones) == 1
        assert zones[0]["mode"] == "core/perim"
        assert zones[0]["num_floors"] == 5

    def test_perimeter_core_narrow_fallback(self):
        # 7×7 square — buffer(-4.57) gives empty core → falls back to one_zone_per_floor
        sq = _square(7.0)
        zones = build_zones("b4", sq, "MediumOffice", 5, "perimeter_core")
        # After fallback: 5 zones with _whole suffix
        assert len(zones) == 5
        assert all("_whole" in z["name"] for z in zones)

    def test_perimeter_core_placeholder_fields(self):
        # R7: build_zones returns ONE placeholder; extrude_geometry expands it.
        sq = _square(30.0)
        zones = build_zones("b5", sq, "MediumOffice", 5, "perimeter_core")
        assert len(zones) == 1
        z = zones[0]
        assert z["mode"] == "core/perim"
        assert z["num_floors"] == 5
        assert "perim_depth_m" in z
        assert z["archetype_id"] == "MediumOffice"

    def test_zone_dict_has_archetype_id(self):
        sq = _square(20.0)
        zones = build_zones("b6", sq, "Warehouse", 3, "one_zone_per_floor")
        for z in zones:
            assert z["archetype_id"] == "Warehouse"

    def test_perimeter_core_z_coords(self):
        sq = _square(30.0)
        zones = build_zones("b7", sq, "MediumOffice", 3, "perimeter_core", floor_to_floor_m=3.0)
        # R7: placeholder carries floor_to_floor height.
        assert len(zones) == 1
        assert abs(zones[0]["height_m"] - 3.0) < 1e-9

    def test_one_zone_per_floor_z_stacking(self):
        sq = _square(20.0)
        zones = build_zones("b8", sq, "MidriseApartment", 3, "one_zone_per_floor")
        assert abs(zones[0]["z_floor"]) < 1e-9
        assert abs(zones[1]["z_floor"] - 3.5) < 1e-9
        assert abs(zones[2]["z_floor"] - 7.0) < 1e-9

    def test_single_zone_height_is_full_building(self):
        sq = _square(10.0)
        zones = build_zones("b9", sq, "SmallOffice", 4, "single_zone")
        assert abs(zones[0]["height_m"] - 14.0) < 1e-9

    def test_unknown_archetype_route(self):
        sq = _square(10.0)
        zones = build_zones("b10", sq, "OpenUBEMUnknown", 1, "single_zone")
        assert len(zones) == 1
        assert zones[0]["archetype_id"] == "OpenUBEMUnknown"
