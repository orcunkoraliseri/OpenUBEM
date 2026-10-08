from __future__ import annotations

import pytest
from shapely.geometry import box

import openubem.geometry.european_residential as er
from openubem.geometry.european_residential import (
    DWELLING_DENSITY_REFUSAL_TOKEN,
    EuropeanFloorAllocation,
    generate_european_building_dwelling_layout,
)
from scripts.run_eu_s2_campaign import (
    _drop_sliver_surfaces,
    _mirror_interzone_pairs,
    _mirror_interzone_pairs_stats,
)


class _Surface:
    def __init__(self, name, partner, coords):
        self.Name = name
        self.Outside_Boundary_Condition = "Surface"
        self.Outside_Boundary_Condition_Object = partner
        self._coords = [tuple(p) for p in coords]

    @property
    def coords(self):
        return list(self._coords)

    def setcoords(self, coords):
        self._coords = [tuple(p) for p in coords]


class _Idf:
    def __init__(self, surfaces):
        self.idfobjects = {"BUILDINGSURFACE:DETAILED": surfaces}


def _pair(first, second):
    a = _Surface("A ceiling", "B floor", first)
    b = _Surface("B floor", "A ceiling", second)
    return a, b, _Idf([a, b])


SQUARE = [(0.0, 0.0, 3.0), (10.0, 0.0, 3.0), (10.0, 10.0, 3.0), (0.0, 10.0, 3.0)]


def test_near_duplicate_on_one_side_comes_out_as_exact_reverses():
    with_dup = [SQUARE[0], (10.0, 0.0002, 3.0), SQUARE[1], SQUARE[2], SQUARE[3]]
    a, b, idf = _pair(with_dup, list(reversed(SQUARE)))
    assert _mirror_interzone_pairs(idf) == 1
    assert a.coords == SQUARE
    assert b.coords == list(reversed(a.coords))


def test_pair_that_does_not_cover_the_same_polygon_is_untouched():
    smaller = [(0.0, 0.0, 3.0), (5.0, 0.0, 3.0), (5.0, 10.0, 3.0), (0.0, 10.0, 3.0)]
    dup = [SQUARE[0], (10.0, 0.0002, 3.0), SQUARE[1], SQUARE[2], SQUARE[3]]
    a, b, idf = _pair(dup, list(reversed(smaller)))
    before = (a.coords, b.coords)
    stats = _mirror_interzone_pairs_stats(idf)
    assert stats["pairs_skipped_coverage"] == 1 and stats["pairs_rewritten"] == 0
    assert (a.coords, b.coords) == before


def test_clean_pair_is_left_byte_identical():
    a, b, idf = _pair(SQUARE, list(reversed(SQUARE)))
    assert _mirror_interzone_pairs(idf) == 0
    assert a.coords == SQUARE and b.coords == list(reversed(SQUARE))


def _allocations(count, storeys=1):
    return tuple(EuropeanFloorAllocation(i, count, 400.0, 0.0) for i in range(storeys))


def test_density_above_twelve_is_cut_or_refused_by_check_never_by_density_token():
    layout = generate_european_building_dwelling_layout(box(0, 0, 20, 20), floor_allocations=_allocations(14))
    assert layout.fallback_reason != DWELLING_DENSITY_REFUSAL_TOKEN
    if layout.dwelling_layout_emitted:
        assert layout.storey_groups
    else:
        assert str(layout.fallback_reason).startswith("NOCORE_CHECK_FAILED_")


def test_density_refusal_still_returned_outside_nocore(monkeypatch):
    monkeypatch.setattr(er, "EUROPEAN_LAYOUT_REGIME", "ruled")
    layout = generate_european_building_dwelling_layout(box(0, 0, 20, 20), floor_allocations=_allocations(14))
    assert not layout.dwelling_layout_emitted
    assert layout.fallback_reason == DWELLING_DENSITY_REFUSAL_TOKEN


class _Fen:
    def __init__(self, host):
        self.Building_Surface_Name = host


class _RemovableIdf:
    def __init__(self, surfaces, fens=()):
        self.idfobjects = {"BUILDINGSURFACE:DETAILED": list(surfaces), "FENESTRATIONSURFACE:DETAILED": list(fens)}

    def removeidfobject(self, obj):
        for lst in self.idfobjects.values():
            if obj in lst:
                lst.remove(obj)


def _square(side, z=3.0):
    return [(0.0, 0.0, z), (side, 0.0, z), (side, side, z), (0.0, side, z)]


def test_sliver_pair_is_removed_on_both_sides_with_its_window():
    big = _Surface("Big wall", "", _square(10.0))
    big.Outside_Boundary_Condition = "Outdoors"
    sa = _Surface("Sliver A", "Sliver B", _square(0.05))
    sb = _Surface("Sliver B", "Sliver A", list(reversed(_square(0.05))))
    fen = _Fen("Sliver A")
    keep_fen = _Fen("Big wall")
    idf = _RemovableIdf([big, sa, sb], [fen, keep_fen])
    removed, area = _drop_sliver_surfaces(idf)
    assert removed == 2 and area == pytest.approx(0.005)
    assert idf.idfobjects["BUILDINGSURFACE:DETAILED"] == [big]
    assert idf.idfobjects["FENESTRATIONSURFACE:DETAILED"] == [keep_fen]


def test_surface_of_two_hundredths_square_metre_is_kept():
    side = 0.02 ** 0.5
    a = _Surface("A", "B", _square(side))
    b = _Surface("B", "A", list(reversed(_square(side))))
    idf = _RemovableIdf([a, b])
    assert _drop_sliver_surfaces(idf) == (0, 0.0)
    assert idf.idfobjects["BUILDINGSURFACE:DETAILED"] == [a, b]


def test_building_with_slivers_over_total_budget_keeps_everything():
    surfaces = []
    for i in range(40):
        side = 0.09
        surfaces.append(_Surface(f"S{i}a", f"S{i}b", _square(side)))
        surfaces.append(_Surface(f"S{i}b", f"S{i}a", list(reversed(_square(side)))))
    idf = _RemovableIdf(surfaces)
    assert _drop_sliver_surfaces(idf) == (0, 0.0)
    assert len(idf.idfobjects["BUILDINGSURFACE:DETAILED"]) == 80



from shapely.geometry import Polygon as _T04Polygon

import openubem.geometry.european_nocore as _t04_nc


def _t04_checks(plate, flats, k):
    rec = {"drawn_per_floor": k}
    _t04_nc.run_checks(rec, flats, plate)
    return rec["checks"], rec["verdict"]


def test_t04_wrapped_bulge_wall_comes_out_as_two_rectangles():
    plate = box(0, 0, 20, 10)
    left = _T04Polygon([(0, 0), (10, 0), (11, 5), (10, 10), (0, 10)])
    right = _T04Polygon([(10, 0), (20, 0), (20, 10), (10, 10), (11, 5)])
    checks, verdict = _t04_checks(plate, [left, right], 2)
    assert checks["C13"]["value"] == 1
    _, live, new_checks, new_verdict = _t04_nc.improve_cut_nocore(plate, [left, right], checks, verdict, 2)
    assert new_checks["C13"]["value"] == 0
    assert new_verdict == "PASS"
    assert sorted(round(f.area, 3) for f in live) == [100.0, 100.0]
    assert all(abs(f.area - f.minimum_rotated_rectangle.area) < 1e-6 for f in live)
    assert live[0].union(live[1]).symmetric_difference(plate).area < 1e-6


def test_t04_wing_bend_wall_on_l_plate_is_left_untouched():
    plate = _T04Polygon([(0, 0), (20, 0), (20, 10), (10, 10), (10, 20), (0, 20)])
    upper = _T04Polygon([(0, 12), (4, 10), (10, 10), (10, 20), (0, 20)])
    lower = _T04Polygon([(0, 0), (20, 0), (20, 10), (10, 10), (4, 10), (0, 12)])
    flats = [upper, lower]
    checks, verdict = _t04_checks(plate, flats, 2)
    assert checks["C13"]["value"] == 0
    assert list(_t04_nc._straighten_candidates(plate, flats, _t04_nc._plate_reflex_points(plate))) == []
    result = _t04_nc.improve_cut_nocore(plate, flats, checks, verdict, 2)
    assert result[1] is flats and result[2] is checks


def test_t04_clean_cut_comes_back_byte_identical():
    plate = box(0, 0, 20, 10)
    flats = [box(0, 0, 10, 10), box(10, 0, 20, 10)]
    checks, verdict = _t04_checks(plate, flats, 2)
    result = _t04_nc.improve_cut_nocore(plate, flats, checks, verdict, 2)
    assert result[0] is plate and result[1] is flats and result[2] is checks and result[3] == verdict


def test_t04_unbalanced_straight_wall_is_slid_towards_equal_areas():
    plate = box(0, 0, 20, 10)
    flats = [box(0, 0, 4, 10), box(4, 0, 20, 10)]
    checks, verdict = _t04_checks(plate, flats, 2)
    _, live, new_checks, _ = _t04_nc.improve_cut_nocore(plate, flats, checks, verdict, 2)
    assert float(new_checks["C12"]["show"]) > float(checks["C12"]["show"])
    assert sum(f.area for f in live) == pytest.approx(200.0)
    assert all(abs(f.area - f.minimum_rotated_rectangle.area) < 1e-6 for f in live)


def test_t04_worsening_step_is_never_accepted():
    plate = box(0, 0, 20, 10)
    flats = [box(0, 0, 10, 10), box(10, 0, 20, 10)]
    checks, verdict = _t04_checks(plate, flats, 2)
    old = {"checks": checks, "spread": 1.0}
    worse = {"checks": dict(checks, C11={"pass": False, "show": "x"}), "spread": 1.0}
    assert not _t04_nc._strictly_better(old, worse)
    assert not _t04_nc._strictly_better(old, old)


def test_t05_prepare_only_ids_filters_the_row_loop(tmp_path, monkeypatch):
    import json
    import scripts.run_eu_s2_district_campaign as dc

    class _Gdf:
        crs = "EPSG:32630"

        def __len__(self):
            return 3

    weather = dc.ROOT / "pyproject.toml"
    archetypes = tmp_path / "arch.json"
    archetypes.write_text(json.dumps({"records": []}), encoding="utf-8")
    rows = [{"building_id": "a"}, {"building_id": "b"}, {"building_id": "c"}]
    seen = []

    def fake_geometry(model_row, records):
        seen.append(model_row["building_id"])
        raise ValueError("stop")

    monkeypatch.setattr(dc.gpd, "read_file", lambda *_a, **_k: _Gdf())
    monkeypatch.setattr(dc, "_registry_weather", lambda *_a, **_k: (weather, "sha"))
    monkeypatch.setattr(dc, "_mapped_rows", lambda *_a, **_k: (rows, dc._ExclusionCounter()))
    monkeypatch.setattr(dc, "compute_district_median_residential_height_m", lambda *_a, **_k: 10.0)
    monkeypatch.setattr(dc, "_geometry", fake_geometry)
    summary = dc.prepare(
        "ES-MAD-BERRUGUETE", archetypes, weather, None, tmp_path / "out", False, frozenset({"b"})
    )
    assert len(seen) == 1
    assert summary["blocker_exclusions"] == {"idf_build:stop": 1} or sum(summary["blocker_exclusions"].values()) == 1


import copy as _copy

from scripts.run_eu_s2_campaign import _clean_surface_rings, _repair_interzone_pairs


class _Wall:
    def __init__(self, name, partner, coords, zone, obc="Surface", surface_type="Floor"):
        self.Name = name
        self.Outside_Boundary_Condition = obc
        self.Outside_Boundary_Condition_Object = partner
        self.Zone_Name = zone
        self.Surface_Type = surface_type
        self.Sun_Exposure = "NoSun"
        self.Wind_Exposure = "NoWind"
        self._coords = [tuple(p) for p in coords]

    @property
    def coords(self):
        return list(self._coords)

    def setcoords(self, coords):
        self._coords = [tuple(p) for p in coords]


class _CopyIdf:
    def __init__(self, surfaces):
        self.idfobjects = {"BUILDINGSURFACE:DETAILED": list(surfaces), "FENESTRATIONSURFACE:DETAILED": []}

    def copyidfobject(self, obj):
        clone = _copy.copy(obj)
        self.idfobjects["BUILDINGSURFACE:DETAILED"].append(clone)
        return clone

    def removeidfobject(self, obj):
        self.idfobjects["BUILDINGSURFACE:DETAILED"].remove(obj)


def _rect(y_max, z=3.0, x_max=10.0):
    return [(0.0, 0.0, z), (x_max, 0.0, z), (x_max, y_max, z), (0.0, y_max, z)]


def test_t04d_extra_vertex_pair_is_mirrored_to_the_larger_ring():
    bulged = [SQUARE[0], (0.5, -0.0018, 3.0), SQUARE[1], SQUARE[2], SQUARE[3]]
    a = _Wall("A", "B", SQUARE, "Z1")
    b = _Wall("B", "A", list(reversed(bulged)), "Z2")
    idf = _CopyIdf([a, b])
    stats, unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_near_same_mirrored"] == 1 and stats["pairs_still_skipped"] == 0 and not unresolved
    assert b.coords == list(reversed(a.coords))
    assert len(a.coords) == 5


def test_t04d_one_side_larger_remainder_under_a_hundredth_is_dropped():
    a = _Wall("A", "B", _rect(10.0), "Z1")
    b = _Wall("B", "A", list(reversed(_rect(9.9945))), "Z2")
    idf = _CopyIdf([a, b])
    stats, unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_split"] == 1 and stats["remainder_dropped"] == 1 and stats["remainder_adiabatic"] == 0
    assert len(idf.idfobjects["BUILDINGSURFACE:DETAILED"]) == 2
    assert b.coords == list(reversed(a.coords)) and not unresolved


def test_t04d_one_side_larger_remainder_becomes_adiabatic():
    a = _Wall("A", "B", _rect(10.0), "Z1")
    b = _Wall("B", "A", list(reversed(_rect(9.9))), "Z2")
    idf = _CopyIdf([a, b])
    stats, _unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_split"] == 1 and stats["remainder_adiabatic"] == 1
    assert stats["adiabatic_area_m2"] == pytest.approx(0.95, abs=1e-6)
    piece = idf.idfobjects["BUILDINGSURFACE:DETAILED"][-1]
    assert piece.Outside_Boundary_Condition == "Adiabatic" and piece.Outside_Boundary_Condition_Object == ""
    assert b.coords == list(reversed(a.coords))


def test_t04d_one_side_larger_remainder_is_paired_with_an_opposite_surface_of_another_zone():
    a = _Wall("A", "B", _rect(10.0), "Z1")
    b = _Wall("B", "A", list(reversed(_rect(9.9))), "Z2")
    strip = [(0.0, 9.905, 3.0), (10.0, 9.905, 3.0), (10.0, 10.0, 3.0), (0.0, 10.0, 3.0)]
    other = _Wall("C", "", list(reversed(strip)), "Z3", obc="Outdoors", surface_type="Roof")
    idf = _CopyIdf([a, b, other])
    stats, _unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_split"] == 1 and stats["remainder_paired"] == 1 and stats["remainder_adiabatic"] == 0
    piece = idf.idfobjects["BUILDINGSURFACE:DETAILED"][-1]
    assert piece.Outside_Boundary_Condition == "Surface" and piece.Outside_Boundary_Condition_Object == "C"
    assert other.Outside_Boundary_Condition == "Surface" and other.Outside_Boundary_Condition_Object == piece.Name
    assert other.coords == list(reversed(piece.coords))


def test_t04d_pair_over_the_adiabatic_cap_is_left_unchanged():
    a = _Wall("A", "B", _rect(10.0), "Z1")
    b = _Wall("B", "A", list(reversed(_rect(9.5))), "Z2")
    before = (a.coords, b.coords)
    idf = _CopyIdf([a, b])
    stats, unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_still_skipped"] == 1 and stats["pairs_split"] == 0 and unresolved == {"A", "B"}
    assert (a.coords, b.coords) == before and len(idf.idfobjects["BUILDINGSURFACE:DETAILED"]) == 2


def test_t04d_floor_ring_with_a_doubled_vertex_comes_out_without_it():
    ring = [SQUARE[0], SQUARE[1], SQUARE[1], SQUARE[2], SQUARE[3]]
    floor = _Wall("F", "", ring, "Z1", obc="Ground")
    kept = _Wall("K", "", ring, "Z1", obc="Ground")
    idf = _CopyIdf([floor, kept])
    assert _clean_surface_rings(idf, frozenset({"K"})) == 1
    assert floor.coords == SQUARE and len(kept.coords) == 5


def _roof_donor():
    class _Roof(_Wall):
        Construction_Name = "ROOF_CONS"

    donor = _Roof("R0", "", [(50.0, 50.0, 6.0), (60.0, 50.0, 6.0), (60.0, 60.0, 6.0)], "Z9", obc="Outdoors", surface_type="Roof")
    return donor


def test_t04f_ceiling_remainder_with_nothing_above_becomes_a_roof_with_the_copied_construction():
    a = _Wall("A", "B", _rect(10.0), "Z1", surface_type="Ceiling")
    b = _Wall("B", "A", list(reversed(_rect(9.9))), "Z2", surface_type="Floor")
    idf = _CopyIdf([a, b, _roof_donor()])
    stats, _unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_split"] == 1 and stats["remainder_outdoors"] == 1 and stats["remainder_adiabatic"] == 0
    assert stats["outdoors_area_m2"] == pytest.approx(0.95, abs=1e-6)
    piece = idf.idfobjects["BUILDINGSURFACE:DETAILED"][-1]
    assert piece.Surface_Type == "Roof" and piece.Outside_Boundary_Condition == "Outdoors"
    assert piece.Sun_Exposure == "SunExposed" and piece.Wind_Exposure == "WindExposed"
    assert piece.Construction_Name == "ROOF_CONS"


def test_t04f_ceiling_remainder_with_a_surface_above_stays_adiabatic():
    a = _Wall("A", "B", _rect(10.0), "Z1", surface_type="Ceiling")
    b = _Wall("B", "A", list(reversed(_rect(9.9))), "Z2", surface_type="Floor")
    above = [(0.0, 9.0, 3.0), (10.0, 9.0, 3.0), (10.0, 10.0, 3.0), (0.0, 10.0, 3.0)]
    other = _Wall("C", "", list(reversed(above)), "Z3", obc="Adiabatic", surface_type="Floor")
    idf = _CopyIdf([a, b, other, _roof_donor()])
    stats, _unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_split"] == 1 and stats["remainder_outdoors"] == 0
    assert stats["remainder_paired"] + stats["remainder_adiabatic"] == 1


def test_t04f_building_with_sixty_slivers_totalling_two_tenths_has_them_dropped():
    surfaces = []
    for i in range(30):
        side = (0.2 / 60) ** 0.5
        surfaces.append(_Surface(f"S{i}a", f"S{i}b", _square(side)))
        surfaces.append(_Surface(f"S{i}b", f"S{i}a", list(reversed(_square(side)))))
    idf = _RemovableIdf(surfaces)
    removed, area = _drop_sliver_surfaces(idf)
    assert removed == 60 and area == pytest.approx(0.2)
    assert idf.idfobjects["BUILDINGSURFACE:DETAILED"] == []


def test_t04f_pair_with_symmetric_difference_exactly_a_hundredth_is_mirrored():
    a = _Wall("A", "B", _rect(10.0), "Z1")
    b = _Wall("B", "A", list(reversed(_rect(9.999, x_max=10.0))), "Z2")
    a.setcoords(_rect(10.0, x_max=1.0))
    b.setcoords(list(reversed(_rect(9.99, x_max=1.0))))
    idf = _CopyIdf([a, b])
    stats, unresolved = _repair_interzone_pairs(idf)
    assert stats["pairs_near_same_mirrored"] == 1 and stats["pairs_still_skipped"] == 0 and not unresolved
    assert b.coords == list(reversed(a.coords))


def test_t04g_spike_ring_comes_out_without_the_spike():
    from scripts.run_eu_s2_campaign import _clean_ring_3d

    base = 440155.0
    ring = [
        (base, 4479250.0, 0.0),
        (base + 10.0, 4479250.0, 0.0),
        (base + 10.0, 4479260.0, 0.0),
        (base + 10.5, 4479262.0, 0.0),
        (base + 10.0, 4479260.0, 0.0),
        (base, 4479260.0, 0.0),
    ]
    out = _clean_ring_3d(ring)
    assert (base + 10.5, 4479262.0, 0.0) not in out and len(out) == 4
    n = len(out)
    for i in range(n):
        a, b = out[i], out[(i + 1) % n]
        assert sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5 >= 0.01 or n < 3


def test_t04g_dwelling_only_zones_reach_match_after_intersect_match_fails(monkeypatch):
    from pathlib import Path

    from geomeppy import IDF
    from shapely.geometry import Polygon

    from openubem.config import ENERGYPLUS_IDD_PATH, FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M
    from openubem.geometry.zoning import build_zones
    from openubem.idf.surfaces import extrude_geometry

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except Exception:
        pass
    template = Path(__file__).parent.parent / "openubem" / "idf" / "templates" / "commercial_base.idf"
    calls = {"match": 0}
    original_match = IDF.match

    def _boom(self, *a, **k):
        raise ZeroDivisionError("simulated")

    def _counting_match(self, *a, **k):
        calls["match"] += 1
        return original_match(self, *a, **k)

    monkeypatch.setattr(IDF, "intersect_match", _boom)
    monkeypatch.setattr(IDF, "match", _counting_match)
    zones = build_zones("way/1", Polygon([(0, 0), (20, 0), (20, 10), (0, 10)]), "LargeOffice", 2,
                        "one_zone_per_floor", FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
    idf = IDF(str(template))
    extrude_geometry(idf, zones, [])
    assert calls["match"] == 1
    assert len(idf.idfobjects["ZONE"]) == 2


def test_t04h_doubled_spike_ring_cleans_to_eight_and_reaches_the_surface():
    from types import SimpleNamespace

    from scripts.run_eu_s2_campaign import _clean_ring_3d, _clean_surface_rings

    pts = [
        (440158.502, 4479250.530), (440158.894, 4479251.911), (440159.287, 4479253.297),
        (440159.287, 4479253.297), (440160.517, 4479257.630), (440149.865, 4479260.652),
        (440150.012, 4479260.416), (440149.330, 4479260.044), (440150.201, 4479258.660),
        (440150.823, 4479259.066), (440155.885, 4479250.600), (440155.221, 4479250.206),
        (440155.991, 4479248.945), (440155.991, 4479248.945), (440155.221, 4479250.206),
        (440155.885, 4479250.600),
    ]
    ring = [(x, y, 0.0) for x, y in pts]
    assert len(_clean_ring_3d(ring)) == 8

    class Surf:
        Name = "S1"

        def __init__(self):
            self.coords = list(ring)

        def setcoords(self, c):
            self.coords = list(c)

    surf = Surf()
    idf = SimpleNamespace(idfobjects={"BUILDINGSURFACE:DETAILED": [surf]})
    assert _clean_surface_rings(idf, frozenset()) == 1
    assert len(surf.coords) == 8


from scripts.run_eu_s2_campaign import (
    _hidden_overlaps,
    _ring_area_m2,
    _pair_hidden_outdoor_surfaces,
    _surface_records_from_idf,
    hidden_outdoor_area,
)


class _HiddenFen:
    def __init__(self, host, coords):
        self.Building_Surface_Name = host
        self._coords = [tuple(p) for p in coords]

    @property
    def coords(self):
        return list(self._coords)


class _HiddenIdf:
    def __init__(self, surfaces, fens=()):
        self.idfobjects = {"BUILDINGSURFACE:DETAILED": list(surfaces), "FENESTRATIONSURFACE:DETAILED": list(fens)}

    def copyidfobject(self, obj):
        clone = _copy.copy(obj)
        self.idfobjects["BUILDINGSURFACE:DETAILED"].append(clone)
        return clone

    def removeidfobject(self, obj):
        for items in self.idfobjects.values():
            if obj in items:
                items.remove(obj)


def _wall_at_x(x, y0, y1, facing):
    ring = [(x, y0, 0.0), (x, y1, 0.0), (x, y1, 3.0), (x, y0, 3.0)]
    return ring if facing > 0 else list(reversed(ring))


def _hidden_total(idf):
    return sum(_hidden_overlaps(_surface_records_from_idf(idf)).values())


def _outdoors(name, coords, zone, obc="Outdoors", surface_type="Wall"):
    return _Wall(name, "", coords, zone, obc=obc, surface_type=surface_type)


def test_t06c_shared_wall_outdoors_on_both_sides_is_paired_by_exact_mirror_and_remainder_stays_outdoors():
    a = _outdoors("A", _wall_at_x(10.0, 0.0, 10.0, 1), "Z1")
    b = _outdoors("B", _wall_at_x(10.0, 0.0, 5.0, -1), "Z2")
    idf = _HiddenIdf([a, b])
    assert _hidden_total(idf) == pytest.approx(30.0)
    stats = _pair_hidden_outdoor_surfaces(idf)
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    paired = [s for s in surfaces if s.Outside_Boundary_Condition == "Surface"]
    outside = [s for s in surfaces if s.Outside_Boundary_Condition == "Outdoors"]
    assert stats["pieces_paired"] == 1 and len(paired) == 2 and len(outside) == 1
    by_name = {s.Name: s for s in surfaces}
    first, second = paired
    assert by_name[first.Outside_Boundary_Condition_Object] is second
    assert second.coords == list(reversed(first.coords))
    assert sum(_ring_area_m2(s.coords) for s in outside) == pytest.approx(15.0)
    assert _hidden_total(idf) == pytest.approx(0.0, abs=1e-6)


def test_t06c_window_on_the_shared_wall_is_deleted_and_window_elsewhere_is_kept():
    a = _outdoors("A", _wall_at_x(10.0, 0.0, 10.0, 1), "Z1")
    b = _outdoors("B", _wall_at_x(10.0, 0.0, 5.0, -1), "Z2")
    inside = _HiddenFen("A", [(10.0, 1.0, 1.0), (10.0, 2.0, 1.0), (10.0, 2.0, 2.0), (10.0, 1.0, 2.0)])
    outside = _HiddenFen("A", [(10.0, 7.0, 1.0), (10.0, 8.0, 1.0), (10.0, 8.0, 2.0), (10.0, 7.0, 2.0)])
    idf = _HiddenIdf([a, b], [inside, outside])
    stats = _pair_hidden_outdoor_surfaces(idf)
    assert stats["windows_deleted"] == 1 and stats["window_area_m2"] == pytest.approx(1.0)
    remaining = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert remaining == [outside]
    host = next(s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"] if str(s.Name) == outside.Building_Surface_Name)
    assert host.Outside_Boundary_Condition == "Outdoors"


def test_t06c_ceiling_with_a_floor_above_only_on_half_is_half_paired_and_half_kept():
    ceiling = _outdoors("C", [(0.0, 0.0, 3.0), (10.0, 0.0, 3.0), (10.0, 10.0, 3.0), (0.0, 10.0, 3.0)], "Z1", surface_type="Ceiling")
    floor = _outdoors("F", list(reversed([(0.0, 0.0, 3.0), (5.0, 0.0, 3.0), (5.0, 10.0, 3.0), (0.0, 10.0, 3.0)])), "Z2", obc="Adiabatic", surface_type="Floor")
    idf = _HiddenIdf([ceiling, floor])
    _pair_hidden_outdoor_surfaces(idf)
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    paired = [s for s in surfaces if s.Outside_Boundary_Condition == "Surface"]
    kept = [s for s in surfaces if s.Outside_Boundary_Condition == "Outdoors"]
    assert len(paired) == 2 and len(kept) == 1
    assert sum(_ring_area_m2(s.coords) for s in paired) == pytest.approx(100.0)
    assert _ring_area_m2(kept[0].coords) == pytest.approx(50.0)
    assert {s.Surface_Type for s in paired} == {"Ceiling", "Floor"}
    assert _hidden_total(idf) == pytest.approx(0.0, abs=1e-6)


def test_t06c_wall_with_nothing_across_is_left_untouched():
    a = _outdoors("A", _wall_at_x(10.0, 0.0, 10.0, 1), "Z1")
    far = _outdoors("B", _wall_at_x(20.0, 0.0, 10.0, -1), "Z2")
    idf = _HiddenIdf([a, far])
    before = [(s.Name, s.coords, s.Outside_Boundary_Condition) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]]
    stats = _pair_hidden_outdoor_surfaces(idf)
    after = [(s.Name, s.coords, s.Outside_Boundary_Condition) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]]
    assert stats["pairs_split"] == 0 and before == after


def test_t06c_wall_across_a_surface_already_paired_becomes_adiabatic_never_outdoors():
    a = _outdoors("A", _wall_at_x(10.0, 0.0, 10.0, 1), "Z1")
    b = _Wall("B", "C", _wall_at_x(10.0, 0.0, 10.0, -1), "Z2", obc="Surface", surface_type="Wall")
    c = _Wall("C", "B", _wall_at_x(10.0, 0.0, 10.0, 1), "Z3", obc="Surface", surface_type="Wall")
    idf = _HiddenIdf([a, b, c])
    stats = _pair_hidden_outdoor_surfaces(idf)
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    assert stats["pieces_adiabatic"] == 1
    assert [s.Outside_Boundary_Condition for s in surfaces if s.Zone_Name == "Z1"] == ["Adiabatic"]
    assert b in surfaces and c in surfaces


def test_t06c_hidden_outdoor_area_reads_an_idf_file(tmp_path):
    def block(name, zone, coords, obc):
        rows = [f"{name},", "wall,", "C,", f"{zone},", ",", f"{obc},", ",", "SunExposed,", "WindExposed,", "autocalculate,", "autocalculate,"]
        rows += [f"{v}," for p in coords for v in p]
        rows[-1] = rows[-1][:-1] + ";"
        return "BUILDINGSURFACE:DETAILED,\n" + "\n".join(f"    {r}   !- f" for r in rows) + "\n\n"

    text = block("A", "Z1", _wall_at_x(10.0, 0.0, 10.0, 1), "outdoors") + block("B", "Z2", _wall_at_x(10.0, 0.0, 5.0, -1), "outdoors")
    path = tmp_path / "x.idf"
    path.write_text(text)
    result = hidden_outdoor_area(path)
    assert result["hidden_outdoor_m2"] == pytest.approx(30.0)
    assert result["hidden_ground_m2"] == 0.0 and result["surface_count"] == 2
    assert result["outdoor_wall_m2"] == pytest.approx(45.0)


from scripts.run_eu_s2_campaign import (
    _clip_zone_horizontals_to_own_polygon,
    _storey_floor_overlap,
    _storeys_overlap,
    zone_floor_overlap,
)


def _strip(x0, x1, z=0.0, y1=10.0):
    return [(x0, 0.0, z), (x0, y1, z), (x1, y1, z), (x1, 0.0, z)]


def _flat_idf(rings_by_zone, surface_type="Floor"):
    surfaces = [
        _Wall(f"{zone} {surface_type} {i}", "", ring, zone, obc="Ground", surface_type=surface_type)
        for zone, rings in rings_by_zone.items()
        for i, ring in enumerate(rings)
    ]
    return _CopyIdf(surfaces)


def test_t06e_two_flats_whose_floors_share_area_trip_the_overlap_check():
    idf = _flat_idf({"Z1": [_strip(0.0, 10.0)], "Z2": [_strip(0.0, 10.0)]})
    stats = _storey_floor_overlap(_surface_records_from_idf(idf))
    assert stats["floor_sum_m2"] == pytest.approx(200.0) and stats["floor_union_m2"] == pytest.approx(100.0)
    assert _storeys_overlap(idf) is True


def test_t06e_disjoint_flats_do_not_trip_the_overlap_check_and_the_clip_leaves_them_alone():
    idf = _flat_idf({"Z1": [_strip(0.0, 5.0)], "Z2": [_strip(5.0, 10.0)]})
    before = [s.coords for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]]
    assert _storeys_overlap(idf) is False
    stats = _clip_zone_horizontals_to_own_polygon(idf, {"Z1": box(0, 0, 5, 10), "Z2": box(5, 0, 10, 10)})
    assert stats["surfaces_clipped"] == 0
    assert [s.coords for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]] == before


def test_t06e_clip_makes_overlapping_floor_pieces_disjoint_and_their_union_the_footprint():
    idf = _flat_idf({"Z1": [_strip(0.0, 10.0)], "Z2": [_strip(0.0, 10.0)]})
    stats = _clip_zone_horizontals_to_own_polygon(idf, {"Z1": box(0, 0, 5, 10), "Z2": box(5, 0, 10, 10)})
    assert stats["surfaces_clipped"] == 2
    result = _storey_floor_overlap(_surface_records_from_idf(idf))
    assert result["floor_sum_m2"] == pytest.approx(100.0)
    assert result["floor_union_m2"] == pytest.approx(100.0)
    assert result["overlap_pairs"] == 0
    assert _storeys_overlap(idf) is False


def test_t06e_clip_keeps_z_and_winding_of_the_clipped_floor():
    ring = list(reversed(_strip(0.0, 10.0, z=6.0)))
    idf = _flat_idf({"Z1": [ring]})
    _clip_zone_horizontals_to_own_polygon(idf, {"Z1": box(0, 0, 4, 10)})
    out = idf.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords
    assert {p[2] for p in out} == {6.0}
    assert Polygon_ccw(out) is Polygon_ccw(ring)


def Polygon_ccw(ring):
    from shapely.geometry import Polygon

    return Polygon([(p[0], p[1]) for p in ring]).exterior.is_ccw


def test_t06e_clip_drops_a_piece_outside_its_own_polygon_and_unpairs_the_partner():
    floor = _Wall("F", "C", _strip(0.0, 10.0), "Z2", obc="Surface", surface_type="Floor")
    ceiling = _Wall("C", "F", list(reversed(_strip(0.0, 10.0))), "Z1", obc="Surface", surface_type="Ceiling")
    idf = _CopyIdf([floor, ceiling])
    stats = _clip_zone_horizontals_to_own_polygon(idf, {"Z1": box(0, 0, 5, 10), "Z2": box(20, 0, 30, 10)})
    assert stats["pieces_dropped"] == 1
    names = [s.Name for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]]
    assert names == ["C"]
    assert ceiling.Outside_Boundary_Condition == "Outdoors" and ceiling.Outside_Boundary_Condition_Object == ""
    assert ceiling.Surface_Type == "Roof"


def test_t06e_clip_splits_a_floor_that_falls_into_two_parts_of_its_own_polygon():
    from shapely.geometry import MultiPolygon

    idf = _flat_idf({"Z1": [_strip(0.0, 10.0)]})
    own = MultiPolygon([box(0, 0, 3, 10), box(6, 0, 9, 10)]).buffer(0)
    stats = _clip_zone_horizontals_to_own_polygon(idf, {"Z1": own})
    assert stats["pieces_added"] == 1
    assert sum(_ring_area_m2(s.coords) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]) == pytest.approx(60.0)


def test_t06e_floor_overlap_reads_an_idf_file(tmp_path):
    def block(name, zone, coords):
        rows = [f"{name},", "floor,", "C,", f"{zone},", ",", "ground,", ",", "NoSun,", "NoWind,", "autocalculate,", "autocalculate,"]
        rows += [f"{v}," for p in coords for v in p]
        rows[-1] = rows[-1][:-1] + ";"
        return "BUILDINGSURFACE:DETAILED,\n" + "\n".join(f"    {r}   !- f" for r in rows) + "\n\n"

    path = tmp_path / "x.idf"
    path.write_text(block("A", "Z1", _strip(0.0, 10.0)) + block("B", "Z2", _strip(5.0, 15.0)))
    result = zone_floor_overlap(path)
    assert result["floor_sum_m2"] == pytest.approx(200.0)
    assert result["floor_union_m2"] == pytest.approx(150.0)
    assert result["overlap_pairs"] == 1


def _t06e_build(tmp_path):
    from shapely.geometry import box as _box

    from openubem.geometry.european_residential import (
        allocate_european_dwellings,
        european_building_layout_to_zone_specs,
    )
    from scripts.run_eu_s2_campaign import WEATHER_PATH, build_idf_for_building, load_fr_record
    import pandas as pd

    footprint = _box(0.0, 0.0, 20.0, 20.0)
    allocation = allocate_european_dwellings(
        archetype_id="FR.N.AB.08.Gen.ReEx.001.001", building_type="AB", n_apartment=8, n_storey=2,
        plate_area_m2=float(footprint.area),
    )
    layout = generate_european_building_dwelling_layout(footprint, floor_allocations=allocation.floor_allocations)
    zones = european_building_layout_to_zone_specs(layout, building_id="t06e", height_m=3.0)
    record = load_fr_record("FR.N.AB.08.Gen.ReEx.001.001")
    path = build_idf_for_building(pd.Series({"building_id": "t06e"}), record, zones, tmp_path, epw_path=WEATHER_PATH)
    return path, zones


def test_t06e_build_with_disjoint_flats_emits_the_flats_and_no_overlap(tmp_path):
    path, zones = _t06e_build(tmp_path)
    result = zone_floor_overlap(path)
    assert result["floor_sum_m2"] <= 1.01 * result["floor_union_m2"]
    assert not any(z.get("generation_status_note") == "room_layout_overlap_fallback" for z in zones)
    assert any("_dwelling_" in z["name"] for z in zones)


def test_t06e_build_falls_back_to_one_zone_per_floor_when_the_overlap_check_fires(tmp_path, monkeypatch):
    import scripts.run_eu_s2_campaign as rc

    real = rc._storeys_overlap
    state = {"fired": False}

    def fire_once(idf):
        if not state["fired"]:
            state["fired"] = True
            return True
        return real(idf)

    monkeypatch.setattr(rc, "_storeys_overlap", fire_once)
    path, zones = _t06e_build(tmp_path)
    assert state["fired"]
    assert all(z["name"].endswith("_whole") for z in zones)
    assert all(z.get("generation_status_note") == "room_layout_overlap_fallback" for z in zones)
    result = zone_floor_overlap(path)
    assert result["floor_sum_m2"] <= 1.01 * result["floor_union_m2"]


def test_t06e_clip_unpairs_a_surface_whose_partner_was_clipped_even_when_the_partner_points_elsewhere():
    ceiling = _Wall("C1", "F3", list(reversed(_strip(0.0, 5.0, z=3.0))), "Z1", obc="Surface", surface_type="Ceiling")
    floor = _Wall("F3", "C2", _strip(0.0, 10.0, z=3.0), "Z2", obc="Surface", surface_type="Floor")
    other = _Wall("C2", "F3", list(reversed(_strip(0.0, 10.0, z=3.0))), "Z3", obc="Surface", surface_type="Ceiling")
    idf = _CopyIdf([ceiling, floor, other])
    _clip_zone_horizontals_to_own_polygon(idf, {"Z2": box(0, 0, 5, 10)})
    assert all(s.Outside_Boundary_Condition == "Outdoors" for s in (ceiling, floor, other))


def _t06e_geo_idf():
    import io

    from geomeppy import IDF

    from openubem.config import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except Exception:
        pass
    return IDF(io.StringIO("VERSION,23.1;"))


def _t06e_zone(floor, label, x0, x1, h=3.0):
    from shapely.geometry import box as _box

    coords = [(x0, 0.0), (x1, 0.0), (x1, 10.0), (x0, 10.0)]
    return {
        "name": f"b_F{floor}_dwelling_{label}", "coords_m": coords, "height_m": h,
        "floor_polygon": _box(x0, 0.0, x1, 10.0),
    }


def _t06e_extrude(function, zones):
    import openubem.idf.surfaces as surfaces

    idf = _t06e_geo_idf()
    zones = sorted(zones, key=surfaces._group_key)
    function(idf, zones, (ValueError, RuntimeError))
    return idf, zones


def _t06e_snapshot(idf):
    return sorted(
        (s.Name, s.Zone_Name, s.Surface_Type, s.Outside_Boundary_Condition, tuple(tuple(p) for p in s.coords))
        for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    )


def _t06e_zone_floors(idf, name):
    return [s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"] if s.Zone_Name == name and s.Surface_Type.upper() == "FLOOR"]


def test_t06e_per_storey_extrusion_of_a_constant_outline_group_is_identical_to_the_frozen_function():
    import openubem.idf.surfaces as surfaces
    from scripts.run_eu_s2_campaign import _extrude_zone_groups_per_storey

    def make():
        return [_t06e_zone(f, label, 4.0 * label, 4.0 * label + 4.0) for f in range(3) for label in range(2)]

    frozen, _ = _t06e_extrude(surfaces._extrude_zone_groups, make())
    new, _ = _t06e_extrude(_extrude_zone_groups_per_storey, make())
    assert _t06e_snapshot(new) == _t06e_snapshot(frozen)
    assert len(_t06e_snapshot(new)) > 0


def test_t06e_per_storey_extrusion_follows_each_storeys_own_flat_outline_and_never_puts_ground_above_z0():
    from scripts.run_eu_s2_campaign import _extrude_zone_groups_per_storey

    zones = [_t06e_zone(f, label, 4.0 * label, 4.0 * label + 4.0) for f in range(4) for label in range(3)]
    zones += [_t06e_zone(f, 0, 0.0, 6.0) for f in (4, 5)] + [_t06e_zone(f, 1, 6.0, 12.0) for f in (4, 5)]
    idf, ordered = _t06e_extrude(_extrude_zone_groups_per_storey, zones)
    for zone in ordered:
        floors = _t06e_zone_floors(idf, zone["name"])
        assert len(floors) == 1
        assert _ring_area_m2(floors[0].coords) == pytest.approx(zone["floor_polygon"].area)
        xs = sorted({round(p[0], 6) for p in floors[0].coords})
        assert xs == sorted({round(c[0], 6) for c in zone["coords_m"]})
        floor_index = int(zone["name"].split("_F")[1].split("_")[0])
        assert {round(p[2], 6) for p in floors[0].coords} == {floor_index * 3.0}
        if floor_index > 0:
            assert floors[0].Outside_Boundary_Condition.lower() != "ground"
    assert all(
        s.Outside_Boundary_Condition.lower() != "ground" or {round(p[2], 6) for p in s.coords} == {0.0}
        for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    )


def test_t06e_label_present_on_two_upper_storeys_only_sits_at_two_to_four_storey_heights():
    from scripts.run_eu_s2_campaign import _extrude_zone_groups_per_storey

    zones = [_t06e_zone(2, 0, 0.0, 5.0), _t06e_zone(3, 0, 0.0, 5.0)]
    idf, _ = _t06e_extrude(_extrude_zone_groups_per_storey, zones)
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    zs = [p[2] for s in surfaces for p in s.coords]
    assert min(zs) == pytest.approx(6.0) and max(zs) == pytest.approx(12.0)
    assert {round(p[2], 6) for s in _t06e_zone_floors(idf, "b_F2_dwelling_0") for p in s.coords} == {6.0}
    assert {round(p[2], 6) for s in _t06e_zone_floors(idf, "b_F3_dwelling_0") for p in s.coords} == {9.0}


def test_t06e_build_restores_the_frozen_extrusion_function_also_when_the_build_raises(tmp_path, monkeypatch):
    import openubem.idf.surfaces as surfaces
    import scripts.run_eu_s2_campaign as rc

    original = surfaces._extrude_zone_groups
    path, _ = _t06e_build(tmp_path)
    assert surfaces._extrude_zone_groups is original

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(rc, "extrude_geometry", boom)
    with pytest.raises(RuntimeError):
        _t06e_build(tmp_path / "again")
    assert surfaces._extrude_zone_groups is original


from scripts.run_eu_s2_campaign import _remove_degenerate_surfaces, ep_geometry_preflight


def _t06f_sq(x0, x1, y1, z=3.0):
    return [(x0, 0.0, z), (x1, 0.0, z), (x1, y1, z), (x0, y1, z)]


def test_t06f_collinear_three_vertex_roof_is_dropped_with_its_partner():
    line = [(0.0, 0.0, 3.0), (5.0, 0.0, 3.0), (10.0, 0.0, 3.0)]
    big = _Surface("Big", "", _t06f_sq(0.0, 10.0, 10.0))
    big.Outside_Boundary_Condition = "Outdoors"
    ra = _Surface("Roof A", "Roof B", line)
    rb = _Surface("Roof B", "Roof A", list(reversed(line)))
    idf = _RemovableIdf([big, ra, rb])
    assert ep_geometry_preflight(idf)
    removed, _ = _remove_degenerate_surfaces(idf)
    assert removed == 2
    assert idf.idfobjects["BUILDINGSURFACE:DETAILED"] == [big]
    assert ep_geometry_preflight(idf) == []


def test_t06f_five_vertex_side_with_a_three_millimetre_pair_matches_its_four_vertex_partner():
    a_ring = [(0.0, 0.0, 3.0), (1.5, 0.0, 3.0), (1.5, 0.5, 3.0), (1.5, 0.503, 3.0), (0.0, 0.503, 3.0)]
    b_ring = [(0.0, 0.0, 3.0), (1.5, 0.0, 3.0), (1.5, 0.5, 3.0), (0.0, 0.503, 3.0)]
    a = _Surface("A", "B", a_ring)
    b = _Surface("B", "A", list(reversed(b_ring)))
    idf = _RemovableIdf([a, b])
    _remove_degenerate_surfaces(idf)
    assert ep_geometry_preflight(idf) == []
    assert len(a.coords) == len(b.coords) == 4


def test_t06f_clean_pair_is_byte_identical_and_preflight_is_empty():
    a = _Surface("A", "B", _t06f_sq(0.0, 10.0, 10.0))
    b = _Surface("B", "A", list(reversed(_t06f_sq(0.0, 10.0, 10.0))))
    idf = _RemovableIdf([a, b])
    before = (a.coords, b.coords)
    assert ep_geometry_preflight(idf) == []
    assert _remove_degenerate_surfaces(idf) == (0, 0.0)
    assert (a.coords, b.coords) == before


def test_t06f_missing_partner_is_flagged():
    a = _Surface("A", "Nowhere", _t06f_sq(0.0, 10.0, 10.0))
    assert ep_geometry_preflight(_RemovableIdf([a])) == [("A", "NO_PARTNER")]


from scripts.run_eu_s2_campaign import _fix_horizontal_orientation, _pair_hidden_outdoor_surfaces


def _t06g_toy(flip_roof, flip_floor):
    sq = _t06f_sq(0.0, 10.0, 10.0)
    ground = _Wall("G1", "", list(sq[:1] + sq[1:]), "Z1", obc="Ground", surface_type="Floor")
    ground.setcoords([(x, y, 0.0) for x, y, _z in sq])
    roof_ring = list(reversed(sq))
    floor_ring = list(sq)
    if flip_roof:
        roof_ring = list(reversed(roof_ring))
    if flip_floor:
        floor_ring = list(reversed(floor_ring))
    roof = _Wall("R1", "", roof_ring, "Z1", obc="Outdoors", surface_type="Roof")
    floor2 = _Wall("F2", "", floor_ring, "Z2", obc="Outdoors", surface_type="Floor")
    top = _Wall("R2", "", [(x, y, 6.0) for x, y, _z in reversed(sq)], "Z2", obc="Outdoors", surface_type="Roof")
    return _CopyIdf([ground, roof, floor2, top])


def _t06g_outdoor_horizontals_at_3(idf):
    return [
        s.Name for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        if abs(s.coords[0][2] - 3.0) < 1e-6 and str(s.Outside_Boundary_Condition).upper() == "OUTDOORS"
    ]


def test_t06g_flipped_roof_and_flipped_floor_become_a_pair_never_outdoors_and_preflight_clears():
    idf = _t06g_toy(flip_roof=True, flip_floor=False)
    assert ("R1", "EXPOSED_BETWEEN_ZONES") in ep_geometry_preflight(idf)
    assert _fix_horizontal_orientation(idf) == 1
    _pair_hidden_outdoor_surfaces(idf)
    assert _t06g_outdoor_horizontals_at_3(idf) == []
    assert [t for t in ep_geometry_preflight(idf) if t[1] == "EXPOSED_BETWEEN_ZONES"] == []

    idf = _t06g_toy(flip_roof=False, flip_floor=True)
    assert ("F2", "EXPOSED_BETWEEN_ZONES") in ep_geometry_preflight(idf)
    assert _fix_horizontal_orientation(idf) == 1
    _pair_hidden_outdoor_surfaces(idf)
    assert _t06g_outdoor_horizontals_at_3(idf) == []
    assert [t for t in ep_geometry_preflight(idf) if t[1] == "EXPOSED_BETWEEN_ZONES"] == []


def test_t06g_preflight_flags_flipped_toy_before_and_not_after_and_clean_toy_is_byte_identical():
    idf = _t06g_toy(flip_roof=True, flip_floor=True)
    assert any(t[1] == "EXPOSED_BETWEEN_ZONES" for t in ep_geometry_preflight(idf))
    _fix_horizontal_orientation(idf)
    _pair_hidden_outdoor_surfaces(idf)
    assert [t for t in ep_geometry_preflight(idf) if t[1] == "EXPOSED_BETWEEN_ZONES"] == []

    clean = _t06g_toy(flip_roof=False, flip_floor=False)
    before = [s.coords for s in clean.idfobjects["BUILDINGSURFACE:DETAILED"]]
    assert _fix_horizontal_orientation(clean) == 0
    assert [s.coords for s in clean.idfobjects["BUILDINGSURFACE:DETAILED"]] == before


def test_flat_count_follows_floor_area_and_slivers_are_imputed():
    import pandas as pd
    from scripts.run_eu_s2_district_campaign import (
        _catastro_dwelling_overrides,
        _dwellings_for,
        _records,
    )

    records = _records("IT")
    row = pd.Series({
        "geometry": box(0, 0, 10, 15), "levels": 3, "building_type": "AB",
        "archetype_id": "IT.MidClim.AB.05.Gen.ReEx.001.001", "observed_dwellings": None,
    })
    assert _dwellings_for(row, records) == (7, "area_imputed")
    sidecar = pd.DataFrame({
        "building_id": ["a", "b", "c", "d"],
        "catastro_local_id": ["X", "Y", "Y", "Z"],
        "n_dwellings": [78.0, 40.0, 40.0, 12.0],
        "overlap_area_m2": [0.3, 100.0, 300.0, 200.0],
    })
    overrides = _catastro_dwelling_overrides(sidecar)
    assert overrides["a"] == (None, "area_imputed")
    assert overrides["b"] == (10.0, "observed_split")
    assert overrides["c"] == (30.0, "observed_split")
    assert overrides["d"] == (12.0, "observed")
    sliver = pd.Series({**row.to_dict(), "observed_dwellings": overrides["a"][0]})
    assert _dwellings_for(sliver, records)[1] == "area_imputed"


def _stacked_zones(counts, plate=None):
    from openubem.geometry.european_residential import european_building_layout_to_zone_specs

    plate = plate or box(0, 0, 20, 12)
    allocations = tuple(EuropeanFloorAllocation(i, c, plate.area, 0.0) for i, c in enumerate(counts))
    layout = generate_european_building_dwelling_layout(plate, floor_allocations=allocations)
    assert layout.dwelling_layout_emitted
    return plate, european_building_layout_to_zone_specs(layout, building_id="b", height_m=3.0)


def test_one_flat_on_four_storeys_gives_four_zones_each_one_storey_tall_with_the_plate_floor():
    plate, zones = _stacked_zones((1, 0, 0, 0))
    assert len(zones) == 4
    assert sorted(z["name"] for z in zones) == [f"b_F{i}_dwelling_0" for i in range(4)]
    for zone in zones:
        assert zone["height_m"] == pytest.approx(3.0)
        assert zone["storey_span"] == 1
        assert zone["floor_polygon"].area == pytest.approx(plate.area, rel=1e-6)


def test_three_flats_on_four_storeys_has_every_storey_index():
    _plate, zones = _stacked_zones((1, 1, 1, 0))
    assert {int(z["name"].split("_F")[1].split("_")[0]) for z in zones} == {0, 1, 2, 3}
    assert all(z["storey_span"] == 1 and z["height_m"] == pytest.approx(3.0) for z in zones)


def test_extruder_refuses_a_zone_that_spans_two_storeys():
    from scripts.run_eu_s2_campaign import _extrude_zone_groups_per_storey

    ring = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    zone = {
        "name": "b_F0_dwelling_0", "coords_m": ring, "floor_polygon": box(0, 0, 10, 10),
        "height_m": 6.0, "storey_span": 2,
    }
    with pytest.raises(AssertionError):
        _extrude_zone_groups_per_storey(None, [zone], Exception)
