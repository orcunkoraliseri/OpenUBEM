from __future__ import annotations

import pytest

from openubem.idf.degenerate_surfaces import drop_degenerate_surfaces

geomeppy = pytest.importorskip("geomeppy")


def _idf():
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF
    from io import StringIO

    from scripts.run_eu_s2_campaign import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(StringIO("Version,9.4;"))


def _surface(idf, name, zone, kind, pts, boundary="Outdoors", obj=""):
    s = idf.newidfobject("BUILDINGSURFACE:DETAILED")
    s.Name = name
    s.Surface_Type = kind
    s.Construction_Name = "C"
    s.Zone_Name = zone
    s.Outside_Boundary_Condition = boundary
    s.Outside_Boundary_Condition_Object = obj
    s.Sun_Exposure = "NoSun"
    s.Wind_Exposure = "NoWind"
    s.setcoords(pts)
    return s


def _window(idf, name, host, pts):
    w = idf.newidfobject("FENESTRATIONSURFACE:DETAILED")
    w.Name = name
    w.Surface_Type = "Window"
    w.Construction_Name = "W"
    w.Building_Surface_Name = host
    w.setcoords(pts)
    return w


WALL = [(0, 0, 0), (4, 0, 0), (4, 0, 3), (0, 0, 3)]
SLIVER = [(0, 0, 0), (0.005, 0, 0), (0.005, 0, 3), (0, 0, 3)]


def _events(pts):
    from openubem.idf.degenerate_surfaces import energyplus_events

    return energyplus_events(pts)


def test_quad_with_two_short_edges_gives_one_event():
    assert _events(SLIVER) == 1


def test_triangle_with_two_short_edges_gives_two_events():
    from openubem.idf.degenerate_surfaces import _coincident_events

    pts, events = _coincident_events([(0, 0, 0), (0.005, 0, 0), (0.005, 0, 0.009)])
    assert len(pts) == 3
    assert events == 2


def test_surface_that_becomes_collinear_gives_one_event():
    assert _events([(0, 0, 0), (500, 0, 0), (1000, 0, 4e-7)]) == 1


def test_valid_triangle_with_short_edge_untouched():
    idf = _idf()
    _surface(idf, "T", "Z1", "Wall", [(0, 0, 0), (0.02, 0, 0), (0.01, 0, 3)])
    before = idf.idfstr()
    report = drop_degenerate_surfaces(idf)
    assert report["n_degenerate"] == 0
    assert report["n_events"] == 0
    assert idf.idfstr() == before


def test_flagged_window_deleted_host_kept():
    idf = _idf()
    _surface(idf, "H", "Z1", "Wall", WALL)
    _window(idf, "W9", "H", [(0, 0, 0), (0.009, 0, 0), (0.009, 0, 2), (0, 0, 2)])
    _window(idf, "WOK", "H", [(1, 0, 1), (2, 0, 1), (2, 0, 2), (1, 0, 2)])
    report = drop_degenerate_surfaces(idf)
    assert [str(s.Name) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]] == ["H"]
    assert [str(w.Name) for w in idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]] == ["WOK"]
    assert report["windows_deleted"] == ["W9"]
    assert report["n_events"] == 1


def test_degenerate_wall_pair_deleted_with_its_window():
    idf = _idf()
    _surface(idf, "A", "Z1", "Wall", SLIVER, "Surface", "B")
    _surface(idf, "B", "Z2", "Wall", list(reversed(SLIVER)), "Surface", "A")
    _surface(idf, "OK", "Z1", "Wall", WALL)
    _window(idf, "WA", "A", [(0, 0, 0), (0.005, 0, 0), (0.005, 0, 0.005)])
    report = drop_degenerate_surfaces(idf)
    assert [str(s.Name) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]] == ["OK"]
    assert len(idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]) == 0
    assert report["partner_not_degenerate"] == []
    assert {r["partner_deleted"] for r in report["surfaces"] if r["kind"] == "surface"} == {"y"}


def test_degenerate_wall_with_valid_partner_is_kept():
    idf = _idf()
    _surface(idf, "A", "Z1", "Wall", SLIVER, "Surface", "B")
    _surface(idf, "B", "Z2", "Wall", WALL, "Surface", "A")
    before = idf.idfstr()
    report = drop_degenerate_surfaces(idf)
    assert report["partner_not_degenerate"] == [("A", "B")]
    assert report["n_deleted"] == 0
    assert idf.idfstr() == before


LYON_WALL = [
    (642730.621, 5070166.19, 15.0),
    (642730.6174760149, 5070166.186497075, 12.0),
    (642729.115, 5070164.693, 12.0),
    (642729.115, 5070164.693, 15.0),
]
LYON_OFFSET = (642000.0, 5070000.0)


def _newell3(pts):
    o = pts[0]
    q = [tuple(c - d for c, d in zip(p, o)) for p in pts]
    n = [0.0, 0.0, 0.0]
    for i in range(len(q)):
        a, b = q[i], q[(i + 1) % len(q)]
        n[0] += a[1] * b[2] - a[2] * b[1]
        n[1] += a[2] * b[0] - a[0] * b[2]
        n[2] += a[0] * b[1] - a[1] * b[0]
    return n


def _lyon_idf():
    idf = _idf()
    zone = idf.newidfobject("ZONE")
    zone.Name = "Z1"
    _surface(idf, "A", "Z1", "Wall", LYON_WALL, "Surface", "B")
    _surface(idf, "B", "Z2", "Wall", list(reversed(LYON_WALL)), "Surface", "A")
    _window(idf, "WA", "A", [(642730.0, 5070165.6, 13.0), (642729.5, 5070165.1, 13.0), (642729.5, 5070165.1, 14.0), (642730.0, 5070165.6, 14.0)])
    return idf


def test_utm_wall_flagged_before_shift_and_not_after():
    from openubem.idf.local_origin import shift_to_local_origin

    idf = _lyon_idf()
    assert drop_degenerate_surfaces(idf, apply=False)["n_degenerate"] >= 1
    shifted = shift_to_local_origin(idf, *LYON_OFFSET)
    assert drop_degenerate_surfaces(shifted, apply=False)["n_events_total"] == 0


def test_shift_keeps_areas_normals_and_pair_opposition():
    from openubem.idf.local_origin import shift_to_local_origin

    idf = _lyon_idf()
    before = {
        str(s.Name): _newell3([tuple(float(c) for c in p) for p in s.coords])
        for kind in ("BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED")
        for s in idf.idfobjects[kind]
    }
    shifted = shift_to_local_origin(idf, *LYON_OFFSET)
    for kind in ("BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED"):
        for s in shifted.idfobjects[kind]:
            pts = [tuple(float(c) for c in p) for p in s.coords]
            n = _newell3(pts)
            b = before[str(s.Name)]
            area_a = 0.5 * sum(c * c for c in n) ** 0.5
            area_b = 0.5 * sum(c * c for c in b) ** 0.5
            assert abs(area_a - area_b) < 1e-6
            la = sum(c * c for c in n) ** 0.5
            lb = sum(c * c for c in b) ** 0.5
            assert all(abs(x / la - y / lb) < 1e-9 for x, y in zip(n, b))
            assert all(p[2] in (12.0, 13.0, 14.0, 15.0) for p in pts)
    na = _newell3([tuple(float(c) for c in p) for p in shifted.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords])
    nb = _newell3([tuple(float(c) for c in p) for p in shifted.idfobjects["BUILDINGSURFACE:DETAILED"][1].coords])
    assert sum(x * y for x, y in zip(na, nb)) < 0


def test_window_and_host_shift_by_the_same_amount():
    from openubem.idf.local_origin import shift_to_local_origin

    idf = _lyon_idf()
    host_before = [tuple(float(c) for c in p) for p in idf.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords]
    win_before = [tuple(float(c) for c in p) for p in idf.idfobjects["FENESTRATIONSURFACE:DETAILED"][0].coords]
    shifted = shift_to_local_origin(idf, *LYON_OFFSET)
    host = [tuple(float(c) for c in p) for p in shifted.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords]
    win = [tuple(float(c) for c in p) for p in shifted.idfobjects["FENESTRATIONSURFACE:DETAILED"][0].coords]
    for old, new in ((host_before, host), (win_before, win)):
        for o, n in zip(old, new):
            assert abs((o[0] - n[0]) - LYON_OFFSET[0]) < 1e-6
            assert abs((o[1] - n[1]) - LYON_OFFSET[1]) < 1e-6
            assert o[2] == n[2]
