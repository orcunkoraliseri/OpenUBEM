"""Tests for openubem.viz.geometry_extract (T01).

Fixture: tests/fixtures/viz/Restaurant_QuickServiceRestaurant_90.1-2013.idf,
a small real DOE-prototype IDF (18 BuildingSurface:Detailed, 4
FenestrationSurface:Detailed -- 3 windows + 1 fenestration-typed door, no
standalone Window/Door/Shading objects), copied verbatim from
docs/docs_DONE/scheduleDigitization/sources/.
"""
import os

import pytest

from openubem.viz.geometry_extract import (
    _parse_fen_vertices,
    collect_geometry,
    parse_idf,
)

_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "viz",
    "Restaurant_QuickServiceRestaurant_90.1-2013.idf",
)


@pytest.fixture(scope="module")
def geometry():
    return collect_geometry(_FIXTURE)


@pytest.fixture(scope="module")
def idf_data():
    return parse_idf(_FIXTURE)


class TestCollectGeometry:
    def test_faces_and_subwin_nonempty_and_disjoint(self, geometry):
        faces = geometry["faces"]
        subwin = geometry["subwin"]
        assert len(faces) > 0
        assert len(subwin) > 0
        # Category vocabularies never overlap: faces holds opaque/interior
        # surfaces, subwin holds only windows/doors.
        face_categories = {rec[2] for rec in faces}
        subwin_categories = {rec[2] for rec in subwin}
        assert face_categories.isdisjoint({"window", "door"})
        assert subwin_categories <= {"window", "door"}

    def test_every_record_has_nonempty_surf_name(self, geometry):
        for rec in geometry["faces"]:
            assert len(rec) == 5
            surf_name = rec[4]
            assert isinstance(surf_name, str)
            assert surf_name.strip() != ""
        for rec in geometry["subwin"]:
            assert len(rec) == 5
            surf_name = rec[4]
            assert isinstance(surf_name, str)
            assert surf_name.strip() != ""

    def test_counts_match_source_idf_object_counts(self, geometry, idf_data):
        n_bsd = len(idf_data.get("BUILDINGSURFACE:DETAILED", []))
        n_fen = len(idf_data.get("FENESTRATIONSURFACE:DETAILED", []))
        assert n_bsd == 18
        assert n_fen == 4
        # Every BuildingSurface:Detailed becomes exactly one faces record
        # (fixture has no degenerate/short surfaces).
        assert len(geometry["faces"]) == n_bsd
        # Every FenestrationSurface:Detailed becomes exactly one subwin
        # record (all 4 sit on exterior walls in this fixture).
        assert len(geometry["subwin"]) == n_fen

    def test_golden_vertex_roundtrip_dining_wall_east(self, geometry):
        """Dining_Wall_East: Relative coords, Zone 'Dining' origin (0,0,0),
        building small enough that recentring never triggers -- so world
        vertices equal the raw IDF vertex block exactly. Golden values read
        directly from the fixture's BuildingSurface:Detailed block (the same
        values visualizer_adapter._parse_bsd_vertices would produce for an
        untranslated zone, since dx=dy=dz=0 makes the offset a no-op).
        """
        assert geometry["recentre_offset"] == (0.0, 0.0, 0.0)
        match = [rec for rec in geometry["faces"] if rec[4] == "Dining_Wall_East"]
        assert len(match) == 1
        _, zone_name, category, verts, surf_name = match[0]
        assert zone_name == "Dining"
        assert category == "wall"
        golden = [
            (15.2428, 0.0000, 3.0488),
            (15.2428, 0.0000, 0.0000),
            (15.2428, 7.6214, 0.0000),
            (15.2428, 7.6214, 3.0488),
        ]
        assert len(verts) == len(golden)
        for (vx, vy, vz), (gx, gy, gz) in zip(verts, golden):
            assert vx == pytest.approx(gx, abs=1e-6)
            assert vy == pytest.approx(gy, abs=1e-6)
            assert vz == pytest.approx(gz, abs=1e-6)

    def test_parse_fen_vertices_literal_autocalculate_num_vertices(self):
        """Regression test for the T02-discovered bug: real IDFs from this
        pipeline's builder write "autocalculate" as literal text (not a blank
        field) for FenestrationSurface:Detailed's Number-of-Vertices. Field
        shape below is copied from a real nyc_centre pilot building
        (way/42500728, wall 0001's window) with values otherwise unchanged.
        """
        fen_fields = [
            "Block way_42500728_whole Storey 0 Wall 0001 window",  # Name
            "Window",                    # Surface Type
            "Window_Construction",       # Construction Name
            "Block way_42500728_whole Storey 0 Wall 0001",  # Building Surface Name
            "",                          # Outside Boundary Condition Object
            "autocalculate",             # View Factor to Ground
            "",                          # Frame and Divider Name
            "1.0",                       # Multiplier
            "autocalculate",             # Number of Vertices (literal text, not blank)
            "4.938211759872443", "-31.83255", "2.45",
            "4.938211759872443", "-31.83255", "1.0499999999999998",
            "-25.46151", "-15.50516", "1.0499999999999998",
            "-25.46151", "-15.50516", "2.45",
        ]
        verts = _parse_fen_vertices(fen_fields, 0.0, 0.0, 0.0)
        assert len(verts) == 4
        assert verts[0] == pytest.approx((4.938211759872443, -31.83255, 2.45))
        assert verts[2] == pytest.approx((-25.46151, -15.50516, 1.0499999999999998))
