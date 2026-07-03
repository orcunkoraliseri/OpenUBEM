"""Room-layout extrusion + interior boundary-condition tests (PLAN layoutgenerator T09/T10).

Geometry-level gate: each sub-polygon extrudes as its own N-storey block, intersect_match
pairs corridor<->unit walls as Surface, and courtyard-facing walls stay Outdoors. Asserts
zero mismatched interzone pairs (the mismatch gate must not reroute) — the proxy for
'no EnergyPlus geometry Fatal'. An actual E+ run is the LIVE_SMOKE / cluster tier (T12/T14).
"""
from pathlib import Path

import pytest
from geomeppy import IDF
from shapely.geometry import box
from shapely.ops import unary_union

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.surfaces import extrude_geometry, find_mismatched_interzone_pairs
from openubem.geometry.layoutGenerator import generate_layout

_TPL = str(Path(__file__).parent.parent / "openubem" / "idf" / "templates" / "commercial_base.idf")


def _fresh_idf() -> IDF:
    from eppy.modeleditor import IDDAlreadySetError
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_TPL)


def _build(poly, floors=3):
    idf = _fresh_idf()
    zones = generate_layout("bldg", poly, "MidriseApartment", floors)
    extrude_geometry(idf, zones, [])
    return idf, zones


def _bc_counts(idf):
    counts = {}
    for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        b = s.Outside_Boundary_Condition.lower()
        counts[b] = counts.get(b, 0) + 1
    return counts


_L = unary_union([box(0, 0, 40, 15), box(0, 0, 15, 40)])
_O = box(0, 0, 50, 50).difference(box(15, 15, 35, 35))
_BAR = box(0, 0, 46.33, 16.92)


class TestRoomLayoutExtrusion:
    @pytest.mark.parametrize("poly,tag", [(_BAR, "bar"), (_L, "L"), (_O, "courtyard")])
    def test_no_mismatched_interzone_pairs(self, poly, tag):
        # zero mismatched pairs => mismatch gate won't reroute => E+-valid interzone geometry
        idf, _ = _build(poly)
        assert find_mismatched_interzone_pairs(idf) == []

    @pytest.mark.parametrize("poly", [_BAR, _L, _O])
    def test_all_zones_extruded(self, poly):
        _, zones = _build(poly)
        assert zones and all(z.get("extruded") for z in zones)

    def test_corridor_unit_surface_pairs_exist(self):
        # interior corridor<->unit walls must be coupled Surface pairs
        idf, _ = _build(_BAR)
        assert _bc_counts(idf).get("surface", 0) > 0

    def test_courtyard_walls_outdoors_and_hole_free(self):
        idf, zones = _build(_O)
        # no extruded block carries an interior ring (the donut Fatal root cause)
        assert all(len(list(z["floor_polygon"].interiors)) == 0 for z in zones)
        # courtyard-facing + outer-envelope walls remain Outdoors (unpaired)
        assert _bc_counts(idf).get("outdoors", 0) > 0

    def test_ground_slabs_present(self):
        idf, _ = _build(_BAR)
        assert _bc_counts(idf).get("ground", 0) > 0   # ground-floor slabs kept as 'ground'
