from __future__ import annotations

import math

import pytest

from openubem.idf.european_windows import (
    add_tabula_windows,
    is_convex,
    polygon_area,
    window_record,
)

FALLBACK_ID = "ES.ME.MFH.05.Gen.ReEx.001.001"
NORMAL_ID = "ES.ME.AB.01.Gen.ReEx.001.001"


class FakeObj:
    def __init__(self, kind, **fields):
        self.kind = kind
        self.__dict__.update(fields)
        self.coords = fields.get("coords", [])

    def setcoords(self, coords):
        self.coords = [tuple(c) for c in coords]


class FakeIdf:
    def __init__(self, walls):
        self.idfobjects = {
            "BUILDINGSURFACE:DETAILED": walls,
            "FENESTRATIONSURFACE:DETAILED": [],
            "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM": [],
            "CONSTRUCTION": [],
        }

    def newidfobject(self, kind, **fields):
        obj = FakeObj(kind, **fields)
        self.idfobjects.setdefault(kind, []).append(obj)
        return obj


def wall(name, coords, obc="Outdoors", surface_type="Wall"):
    return FakeObj(
        "BUILDINGSURFACE:DETAILED", Name=name, Surface_Type=surface_type,
        Outside_Boundary_Condition=obc, coords=[tuple(c) for c in coords],
    )


def rect(width=10.0, height=3.0):
    return [(0, 0, height), (0, 0, 0), (width, 0, 0), (width, 0, height)]


def synthetic_record(share):
    return {
        "archetype_id": "TEST", "share": share, "u": 2.0, "shgc": 0.6, "fallback": False,
    }


def inside(point, polygon):
    centre = tuple(sum(p[k] for p in polygon) / len(polygon) for k in range(3))
    return all(
        min(p[k] for p in polygon) - 1e-9 <= point[k] <= max(p[k] for p in polygon) + 1e-9
        for k in range(3)
    ) and centre is not None


def normal(points):
    nx = ny = nz = 0.0
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx / length, ny / length, nz / length)


def test_rectangle_share_area_and_normal():
    w = wall("W1", rect())
    idf = FakeIdf([w])
    info = add_tabula_windows(idf, synthetic_record(0.2))
    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert len(fen) == 1
    assert fen[0].Name == "W1_Win"
    assert fen[0].Building_Surface_Name == "W1"
    assert abs(polygon_area(fen[0].coords) - 0.2 * polygon_area(w.coords)) < 1e-6
    assert all(inside(p, w.coords) for p in fen[0].coords)
    for a, b in zip(normal(fen[0].coords), normal(w.coords)):
        assert abs(a - b) < 1e-9
    assert info["walls_with_window"] == 1
    assert abs(info["share_achieved"] - 0.2) < 1e-9


def test_triangle_wall():
    tri = [(0, 0, 4), (0, 0, 0), (6, 0, 0)]
    w = wall("T1", tri)
    idf = FakeIdf([w])
    add_tabula_windows(idf, synthetic_record(0.25))
    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"][0]
    assert len(fen.coords) == 3
    assert abs(polygon_area(fen.coords) - 0.25 * polygon_area(tri)) < 1e-6
    assert all(inside(p, tri) for p in fen.coords)
    for a, b in zip(normal(fen.coords), normal(tri)):
        assert abs(a - b) < 1e-9


def test_adiabatic_surface_ground_walls_get_no_window():
    walls = [
        wall("A", rect(), obc="Adiabatic"),
        wall("S", rect(), obc="Surface"),
        wall("G", rect(), obc="Ground"),
        wall("R", rect(), surface_type="Roof"),
    ]
    idf = FakeIdf(walls)
    info = add_tabula_windows(idf, synthetic_record(0.2))
    assert idf.idfobjects["FENESTRATIONSURFACE:DETAILED"] == []
    assert idf.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"] == []
    assert info["walls_with_window"] == 0


def test_fallback_archetype_values():
    fb = window_record(FALLBACK_ID)
    normal_rec = window_record(NORMAL_ID)
    assert fb["fallback"] is True
    assert normal_rec["fallback"] is False
    assert 0.0 < fb["share"] < 1.0
    assert fb["n_donors"] > 0


def test_u_and_shgc_formulas():
    import json
    from openubem.idf.european_windows import ARCHETYPE_DIR

    records = json.loads((ARCHETYPE_DIR / "tabula_archetypes_es.json").read_text(encoding="utf-8"))["records"]
    rec = next(r for r in records if r["archetype_id"] == NORMAL_ID)
    wr = window_record(NORMAL_ID)
    expected_share = sum(rec["geometry"]["a_window_components_m2"]) / (
        sum(rec["geometry"]["a_window_components_m2"]) + sum(rec["geometry"]["a_wall_components_m2"])
    )
    assert abs(wr["share"] - expected_share) < 1e-12
    assert abs(wr["u"] - (rec["u_window_w_m2k"] + rec["delta_u_tb_w_m2k"]) * rec["f_red_temp"]) < 1e-12
    assert wr["shgc"] == rec["g_gl_window"]
    idf = FakeIdf([wall("W", rect())])
    info = add_tabula_windows(idf, rec)
    material = idf.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"][0]
    assert abs(material.UFactor - wr["u"]) < 1e-12
    assert material.Solar_Heat_Gain_Coefficient == rec["g_gl_window"]
    assert material.Visible_Transmittance == min(1.0, rec["g_gl_window"])
    assert info["fallback"] is False


def test_nonconvex_wall_is_skipped_with_reason():
    l_shape = [(0, 0, 0), (6, 0, 0), (6, 0, 1), (1, 0, 1), (1, 0, 3), (0, 0, 3)]
    chevron = [(0, 0, 0), (4, 0, 0), (4, 0, 3), (2, 0, 1), ]
    assert not is_convex(chevron)
    idf = FakeIdf([wall("L", l_shape), wall("C", chevron), wall("OK", rect())])
    info = add_tabula_windows(idf, synthetic_record(0.2))
    assert info["walls_with_window"] == 1
    assert info["walls_skipped"] == 2
    assert "more_than_4_vertices" in info["skip_reasons"]
    assert "not_convex" in info["skip_reasons"]


def test_u_limit_asserted():
    idf = FakeIdf([wall("W", rect())])
    bad = {"archetype_id": "X", "share": 0.2, "u": 7.5, "shgc": 0.6, "fallback": False}
    with pytest.raises(ValueError):
        add_tabula_windows(idf, bad)
