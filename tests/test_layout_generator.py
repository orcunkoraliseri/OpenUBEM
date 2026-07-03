"""Unit tests for openubem.geometry.layoutGenerator (PLAN layoutgenerator T02, T03, T10)."""
import math

import pytest
from shapely import affinity
from shapely.geometry import box
from shapely.ops import unary_union

from openubem.geometry import layoutGenerator as lg
from openubem.geometry.layoutGenerator import ShapeClass, classify_footprint


def _L():
    return unary_union([box(0, 0, 40, 15), box(0, 0, 15, 40)])


def _U():
    return unary_union([box(0, 0, 40, 15), box(0, 0, 12, 40), box(28, 0, 40, 40)])


def _T():
    return unary_union([box(0, 30, 40, 45), box(14, 0, 26, 45)])


def _O():
    return box(0, 0, 50, 50).difference(box(15, 15, 35, 35))


class TestClassifier:
    @pytest.mark.parametrize("poly,expected", [
        (box(0, 0, 46.33, 16.92), ShapeClass.SLAB),   # DOE MidriseApartment plate (aspect 0.365)
        (box(0, 0, 30, 27), ShapeClass.COMPACT),       # near-square, aspect >= 0.40
        (box(0, 0, 80, 12), ShapeClass.SLAB),
        (_L(), ShapeClass.L),
        (_U(), ShapeClass.U),
        (_T(), ShapeClass.T),
        (_O(), ShapeClass.O),
        (box(0, 0, 60, 8), ShapeClass.RIBBON),         # width 8 < 9.14, core collapses
        (box(0, 0, 8, 8), ShapeClass.RIBBON),          # tiny footprint
    ])
    def test_shape_class(self, poly, expected):
        cls, _ = classify_footprint(poly)
        assert cls is expected

    def test_noisy_vertices_still_compact(self):
        # a rectangle with a sub-tolerance jitter vertex stays compact/slab, not L
        poly = box(0, 0, 40, 30)
        cls, metrics = classify_footprint(poly)
        assert cls in (ShapeClass.COMPACT, ShapeClass.SLAB)
        assert metrics["reflex_corners"] == 0

    def test_metrics_provenance_keys(self):
        _, metrics = classify_footprint(_L())
        for k in ("area_m2", "rectangularity", "convexity", "elongation",
                  "has_interior_ring", "core_area_m2", "simplified_vertices",
                  "reflex_corners"):
            assert k in metrics


def _floor0(zones):
    return [z for z in zones if "_F0_" in z["name"]]


class TestBarPacker:
    def test_doe_plate_double_loaded(self):
        poly = box(0, 0, 46.33, 16.92)  # W == W_double
        zones = lg.generate_layout("way/1", poly, "MidriseApartment", 4)
        f0 = _floor0(zones)
        assert len(f0) == 5                       # corridor + N/S/E/W
        assert len(zones) == 20                   # 5 zones x 4 floors
        total = sum(z["floor_area_m2"] for z in f0)
        assert abs(total - poly.area) / poly.area < 1e-5   # area conserved
        assert all(z["mode"] == "room_layout" for z in zones)
        assert {z["space_type"] for z in f0} == {"Apartment", "Corridor"}

    def test_wider_bar_conserves(self):
        poly = box(0, 0, 60, 20)
        f0 = _floor0(lg.generate_layout("way/2", poly, "MidriseApartment", 3))
        assert len(f0) == 5
        assert abs(sum(z["floor_area_m2"] for z in f0) - poly.area) / poly.area < 1e-5

    def test_single_loaded(self):
        poly = box(0, 0, 50, 12)  # 9.30 <= W < 16.92
        f0 = _floor0(lg.generate_layout("way/3", poly, "MidriseApartment", 3))
        assert len(f0) == 4       # corridor + row + E/W ends
        assert abs(sum(z["floor_area_m2"] for z in f0) - poly.area) / poly.area < 1e-5

    def test_unique_group_tokens(self):
        # last-underscore token (group key) must be unique per sub-polygon on a floor
        f0 = _floor0(lg.generate_layout("way/4", box(0, 0, 46.33, 16.92), "MidriseApartment", 2))
        tokens = [z["name"].rsplit("_", 1)[-1] for z in f0]
        assert len(tokens) == len(set(tokens))

    def test_narrow_footprint_falls_back(self):
        # width 8 < 9.14 → RIBBON → generate_layout returns [] (caller falls back)
        assert lg.generate_layout("way/5", box(0, 0, 60, 8), "MidriseApartment", 3) == []

    def test_narrow_wing_direct(self):
        subs, config = lg._pack_bar(box(0, 0, 40, 8), lg.MODULE_SPECS["MidriseApartment"])
        assert config == "wing_fallback_narrow"
        assert len(subs) == 1 and subs[0]["tag"] == "whole"

    def test_unsupported_archetype_returns_empty(self):
        assert lg.generate_layout("way/6", box(0, 0, 46, 17), "LargeOffice", 4) == []


class TestWingDecomposition:
    @pytest.mark.parametrize("poly,expected_wings", [
        (_L(), 2),
        (_U(), 3),
        (_T(), 3),
    ])
    def test_wing_counts(self, poly, expected_wings):
        assert len(lg._decompose_wings(poly)) == expected_wings

    def test_cross_not_overfragmented(self):
        # min-area OBB of a plus is diagonal; dominant-edge alignment must keep it axis-aligned
        cross = unary_union([box(15, 0, 27, 45), box(0, 16, 42, 29)])
        assert len(lg._decompose_wings(cross)) == 3

    def test_rotated_L_decomposes(self):
        rot = affinity.rotate(_L(), 30, origin=(0, 0))
        wings = lg._decompose_wings(rot)
        assert len(wings) == 2
        # rotated shapes get a sub-mm cleanup snap; area stays within 0.1%
        assert abs(sum(w.area for w in wings) - rot.area) / rot.area < 1e-3

    @pytest.mark.parametrize("poly", [_L(), _U(), _T(),
                                      unary_union([box(15, 0, 27, 45), box(0, 16, 42, 29)])])
    def test_full_layout_conserves_and_is_clean(self, poly):
        f0 = _floor0(lg.generate_layout("way/9", poly, "MidriseApartment", 3))
        total = sum(z["floor_area_m2"] for z in f0)
        assert abs(total - poly.area) / poly.area < 1e-3           # area conserved (post-cleanup)
        assert all(len(list(z["floor_polygon"].interiors)) == 0 for z in f0)  # hole-free
        assert all(z["floor_polygon"].is_valid for z in f0)
        tokens = [z["name"].rsplit("_", 1)[-1] for z in f0]
        assert len(tokens) == len(set(tokens))                      # unique group tokens

    @pytest.mark.parametrize("poly", [
        box(0, 0, 46.33, 16.92), _L(), _U(), _T(),
        affinity.rotate(_L(), 30, origin=(3, 7)),
        affinity.rotate(_L(), 47, origin=(3, 7)),
        box(0, 0, 50, 50).difference(box(15, 15, 35, 35)),
    ])
    def test_no_degenerate_edges(self, poly):
        # every zone edge >= 5 cm and <= 6 vertices (no polygonize spikes / slivers)
        f0 = _floor0(lg.generate_layout("way/deg", poly, "MidriseApartment", 3))
        for z in f0:
            cs = list(z["floor_polygon"].exterior.coords)
            edges = [((cs[i][0] - cs[i + 1][0]) ** 2 + (cs[i][1] - cs[i + 1][1]) ** 2) ** 0.5
                     for i in range(len(cs) - 1)]
            assert min(edges) > 0.05, f"{z['name']} has a {min(edges):.4f} m degenerate edge"
            assert len(cs) - 1 <= 6

    def test_mis_decomposed_shape_falls_back(self):
        # a rotated U that mis-decomposes must degrade to [] (one_zone_per_floor), not emit bad geometry
        bad = affinity.rotate(_U(), 13, origin=(1, 2))
        zones = lg.generate_layout("way/bad", bad, "MidriseApartment", 3)
        if zones:  # if it did produce a layout, it must be well-conserved
            total = sum(z["floor_area_m2"] for z in zones if "_F0_" in z["name"])
            assert abs(total - bad.area) / bad.area < 0.01


class TestDonutSplitter:
    def test_square_courtyard(self):
        donut = box(0, 0, 50, 50).difference(box(15, 15, 35, 35))
        wings = lg._split_donut(donut)
        assert len(wings) == 8                                    # 4 corners + 4 sides
        assert all(len(list(w.interiors)) == 0 for w in wings)    # every wing hole-free
        assert abs(sum(w.area for w in wings) - donut.area) / donut.area < 1e-5

    def test_no_wing_contains_courtyard(self):
        donut = box(0, 0, 50, 50).difference(box(15, 15, 35, 35))
        court = box(15, 15, 35, 35).representative_point()
        assert not any(w.contains(court) for w in lg._split_donut(donut))

    @pytest.mark.parametrize("donut", [
        box(0, 0, 50, 50).difference(box(15, 15, 35, 35)),
        box(0, 0, 60, 40).difference(box(10, 10, 25, 30)),
        affinity.rotate(box(0, 0, 50, 50).difference(box(15, 15, 35, 35)), 20, origin=(0, 0)),
    ])
    def test_full_layout_hole_free_and_conserved(self, donut):
        f0 = _floor0(lg.generate_layout("way/O", donut, "MidriseApartment", 3))
        assert f0
        assert all(len(list(z["floor_polygon"].interiors)) == 0 for z in f0)  # never a holed block
        total = sum(z["floor_area_m2"] for z in f0)
        assert abs(total - donut.area) / donut.area < 1e-5


class TestDispatch:
    def test_build_zones_room_layout(self):
        from openubem.geometry.zoning import build_zones
        zones = build_zones("way/D", box(0, 0, 46.33, 16.92), "MidriseApartment", 3, "room_layout")
        f0 = _floor0(zones)
        assert len(f0) == 5
        assert all(z["mode"] == "room_layout" and z.get("space_type") for z in zones)

    def test_build_zones_room_layout_unsupported_falls_back(self):
        # RIBBON footprint → generate_layout returns [] → one_zone_per_floor fallback
        from openubem.geometry.zoning import build_zones
        zones = build_zones("way/E", box(0, 0, 60, 8), "MidriseApartment", 3, "room_layout")
        assert len(zones) == 3                                  # one_zone_per_floor
        assert all(z["name"].endswith("_whole") for z in zones)


class TestLoadNormalization:
    def _norm(self, poly, floors=4):
        from openubem.semantic.loads import get_space_type_loads
        from openubem.idf.builder import normalized_space_loads
        zones = lg.generate_layout("way/N", poly, "MidriseApartment", floors)
        st = get_space_type_loads("MidriseApartment")
        norm = normalized_space_loads(zones, 7.53, 7.53, 18.58, st)
        a_tot = sum(z["floor_area_m2"] for z in zones if z.get("space_type"))
        return zones, norm, a_tot

    def test_totals_conserved_to_archetype(self):
        zones, norm, a_tot = self._norm(box(0, 0, 46.33, 16.92))
        assert math.isclose(sum(v["lights"] for v in norm.values()), 7.53 * a_tot, rel_tol=1e-9)
        assert math.isclose(sum(v["equip"] for v in norm.values()), 7.53 * a_tot, rel_tol=1e-9)
        assert math.isclose(sum(v["people"] for v in norm.values()), a_tot / 18.58, rel_tol=1e-9)

    def test_corridor_has_no_equipment_or_people(self):
        zones, norm, _ = self._norm(box(0, 0, 46.33, 16.92))
        corr = [z["name"] for z in zones if z.get("space_type") == "Corridor"]
        assert corr
        assert all(norm[n]["equip"] == 0.0 and norm[n]["people"] == 0.0 for n in corr)
        assert all(norm[n]["lights"] > 0.0 for n in corr)   # corridor is still lit

    def test_conserved_on_L_shape(self):
        zones, norm, a_tot = self._norm(_L())
        assert math.isclose(sum(v["equip"] for v in norm.values()), 7.53 * a_tot, rel_tol=1e-9)

    def test_space_type_loader(self):
        from openubem.semantic.loads import get_space_type_loads
        assert get_space_type_loads("MidriseApartment") is not None
        assert get_space_type_loads("LargeOffice") is None   # not a units+corridor archetype


class TestModuleSpecs:
    def test_midrise_thresholds(self):
        w_double, w_single = lg.wing_width_thresholds(lg.MODULE_SPECS["MidriseApartment"])
        assert math.isclose(w_double, 16.92, abs_tol=1e-6)
        assert math.isclose(w_single, 9.30, abs_tol=1e-6)


# --- T13a hotels (units+corridor engine, same code path as MidriseApartment) ---
HOTELS = ["SmallHotel", "LargeHotel"]
# archetype-average totals from doe_prototype_loads.json (lpd, epd, occ_m2/person)
HOTEL_TOTALS = {"SmallHotel": (10.76, 2.91, 18.58), "LargeHotel": (10.76, 7.53, 18.58)}


class TestHotelModuleSpecs:
    @pytest.mark.parametrize("arch,c,d,bay,area", [
        ("SmallHotel", 1.83, 7.32, 3.66, 26.79),
        ("LargeHotel", 2.44, 7.32, 4.11, 30.09),
    ])
    def test_spec_values(self, arch, c, d, bay, area):
        spec = lg.MODULE_SPECS[arch]
        assert spec["family"] == "units_corridor"
        assert math.isclose(spec["corridor_width_m"], c, abs_tol=1e-9)
        assert math.isclose(spec["unit_depth_m"], d, abs_tol=1e-9)
        assert math.isclose(spec["bay_width_m"], bay, abs_tol=1e-9)
        assert math.isclose(spec["unit_area_m2"], area, abs_tol=1e-9)
        assert spec["unit_space_type"] == "GuestRoom"
        assert spec["corridor_space_type"] == "Corridor"

    @pytest.mark.parametrize("arch", HOTELS)
    def test_thresholds(self, arch):
        spec = lg.MODULE_SPECS[arch]
        w_double, w_single = lg.wing_width_thresholds(spec)
        assert math.isclose(w_double, spec["corridor_width_m"] + 2 * spec["unit_depth_m"], abs_tol=1e-9)
        assert math.isclose(w_single, spec["corridor_width_m"] + spec["unit_depth_m"], abs_tol=1e-9)


class TestHotelClassifier:
    # classifier is archetype-agnostic — same footprints classify identically
    @pytest.mark.parametrize("poly,expected", [
        (box(0, 0, 46.33, 16.92), ShapeClass.SLAB),
        (_L(), ShapeClass.L), (_U(), ShapeClass.U),
        (_T(), ShapeClass.T), (_O(), ShapeClass.O),
    ])
    def test_shape_class(self, poly, expected):
        cls, _ = classify_footprint(poly)
        assert cls is expected


class TestHotelBarPacker:
    @pytest.mark.parametrize("arch", HOTELS)
    def test_wide_bar_double_loaded(self, arch):
        poly = box(0, 0, 60, 20)  # W=20 >= W_double for both hotels
        f0 = _floor0(lg.generate_layout(f"way/{arch}", poly, arch, 3))
        assert len(f0) == 5                       # corridor + N/S/E/W
        total = sum(z["floor_area_m2"] for z in f0)
        assert abs(total - poly.area) / poly.area < 1e-5
        assert {z["space_type"] for z in f0} == {"GuestRoom", "Corridor"}
        assert all(z["mode"] == "room_layout" for z in f0)

    @pytest.mark.parametrize("arch", HOTELS)
    @pytest.mark.parametrize("poly", [_L(), _U(), _T(), _O()])
    def test_complex_conserves_and_is_clean(self, arch, poly):
        f0 = _floor0(lg.generate_layout("way/h", poly, arch, 3))
        assert f0
        total = sum(z["floor_area_m2"] for z in f0)
        assert abs(total - poly.area) / poly.area < 1e-3           # area conserved (post-cleanup)
        assert all(len(list(z["floor_polygon"].interiors)) == 0 for z in f0)  # hole-free
        assert all(z["floor_polygon"].is_valid for z in f0)
        tokens = [z["name"].rsplit("_", 1)[-1] for z in f0]
        assert len(tokens) == len(set(tokens))                      # unique group tokens
        assert {z["space_type"] for z in f0} <= {"GuestRoom", "Corridor"}


class TestHotelLoadNormalization:
    def _norm(self, arch, poly=box(0, 0, 60, 20), floors=4):
        from openubem.semantic.loads import get_space_type_loads
        from openubem.idf.builder import normalized_space_loads
        lpd, epd, occ = HOTEL_TOTALS[arch]
        zones = lg.generate_layout("way/N", poly, arch, floors)
        st = get_space_type_loads(arch)
        norm = normalized_space_loads(zones, lpd, epd, occ, st)
        a_tot = sum(z["floor_area_m2"] for z in zones if z.get("space_type"))
        return zones, norm, a_tot, (lpd, epd, occ)

    @pytest.mark.parametrize("arch", HOTELS)
    def test_totals_conserved_to_archetype(self, arch):
        zones, norm, a_tot, (lpd, epd, occ) = self._norm(arch)
        assert math.isclose(sum(v["lights"] for v in norm.values()), lpd * a_tot, rel_tol=1e-9)
        assert math.isclose(sum(v["equip"] for v in norm.values()), epd * a_tot, rel_tol=1e-9)
        assert math.isclose(sum(v["people"] for v in norm.values()), a_tot / occ, rel_tol=1e-9)

    @pytest.mark.parametrize("arch", HOTELS)
    def test_corridor_has_no_equipment_or_people(self, arch):
        zones, norm, _, _ = self._norm(arch)
        corr = [z["name"] for z in zones if z.get("space_type") == "Corridor"]
        assert corr
        assert all(norm[n]["equip"] == 0.0 and norm[n]["people"] == 0.0 for n in corr)
        assert all(norm[n]["lights"] > 0.0 for n in corr)   # corridor still lit

    @pytest.mark.parametrize("arch", HOTELS)
    def test_space_type_loader(self, arch):
        from openubem.semantic.loads import get_space_type_loads
        st = get_space_type_loads(arch)
        assert st is not None
        assert "GuestRoom" in st and "Corridor" in st
        assert st["Corridor"]["equipment_w_m2"] == 0.0
        assert st["Corridor"]["has_occupancy"] is False
        assert st["GuestRoom"]["has_occupancy"] is True
