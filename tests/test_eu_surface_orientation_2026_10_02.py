from __future__ import annotations

from openubem.idf.surface_orientation import (
    _newell,
    check_interzone_pairs,
    measure_outdoor_walls,
    normalise_surface_orientation,
)


class Obj:
    def __init__(self, **fields):
        self.__dict__.update(fields)
        self.coords = [tuple(c) for c in fields.get("coords", [])]

    def setcoords(self, coords):
        self.coords = [tuple(c) for c in coords]


class Idf:
    def __init__(self, surfaces, windows=()):
        self.idfobjects = {
            "BUILDINGSURFACE:DETAILED": list(surfaces),
            "FENESTRATIONSURFACE:DETAILED": list(windows),
        }


def _surf(name, kind, zone, coords, obc="Outdoors", obj=""):
    return Obj(
        Name=name, Surface_Type=kind, Zone_Name=zone, Outside_Boundary_Condition=obc,
        Outside_Boundary_Condition_Object=obj, coords=coords,
    )


def _box(zone, x0, y0, z0, w, d, h, ccw, floor_obc=("Outdoors", ""), roof_kind="Roof", roof_obc=("Outdoors", "")):
    x1, y1, z1 = x0 + w, y0 + d, z0 + h
    ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if not ccw:
        ring = ring[::-1]
    surfaces = [
        _surf(f"{zone}_f", "Floor", zone, [(x, y, z0) for x, y in ring], *floor_obc),
        _surf(f"{zone}_r", roof_kind, zone, [(x, y, z1) for x, y in ring], *roof_obc),
    ]
    for i in range(4):
        (xa, ya), (xb, yb) = ring[i], ring[(i + 1) % 4]
        surfaces.append(_surf(f"{zone}_w{i}", "Wall", zone, [(xa, ya, z1), (xa, ya, z0), (xb, yb, z0), (xb, yb, z1)]))
    return surfaces


def _check_box(idf, zone):
    by = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
    assert _newell(by[f"{zone}_f"].coords)[2] < 0
    assert _newell(by[f"{zone}_r"].coords)[2] > 0
    assert measure_outdoor_walls(idf) == {"inward": 0, "outward": 4, "unclear": 0}


def test_ccw_box_and_cw_box_both_come_out_right():
    for ccw in (True, False):
        idf = Idf(_box("Z", 0, 0, 0, 10, 6, 3, ccw))
        res = normalise_surface_orientation(idf)
        _check_box(idf, "Z")
        assert res["WALL"]["reversed"] + res["WALL"]["kept"] == 4
        assert res["WALL"]["fallback"] == 0


def test_window_follows_its_wall():
    idf = Idf(_box("Z", 0, 0, 0, 10, 6, 3, True))
    wall = next(s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"] if s.Name == "Z_w0")
    win_pts = [(p[0] + (0.0), p[1], p[2]) for p in wall.coords]
    win = Obj(Name="Z_w0_Win", Building_Surface_Name="Z_w0", coords=win_pts)
    idf.idfobjects["FENESTRATIONSURFACE:DETAILED"].append(win)
    res = normalise_surface_orientation(idf)
    n_wall, n_win = _newell(wall.coords), _newell(win.coords)
    assert sum(a * b for a, b in zip(n_wall, n_win)) > 0
    assert res["windows_reversed"] + res["windows_kept"] == 1


def test_interzone_floor_ceiling_pair_stays_opposite():
    low = _box("L", 0, 0, 0, 10, 6, 3, True, roof_kind="Ceiling", roof_obc=("Surface", "U_f"))
    up = _box("U", 0, 0, 3, 10, 6, 3, True, floor_obc=("Surface", "L_r"))
    for s in low:
        if s.Name == "L_r":
            s.Outside_Boundary_Condition_Object = "U_f"
    idf = Idf(low + up)
    res = normalise_surface_orientation(idf)
    assert res["interzone_pairs"] == 1
    assert res["interzone_opposite"] == 1
    assert res["interzone_bad"] == []
    assert check_interzone_pairs(idf)["interzone_opposite"] == 1


def test_geometry_unchanged_only_order():
    idf = Idf(_box("Z", 0, 0, 0, 10, 6, 3, True))
    before = {s.Name: frozenset(s.coords) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
    normalise_surface_orientation(idf)
    after = {s.Name: frozenset(s.coords) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
    assert before == after


def test_pair_rules_one_and_two_restore_opposite_normals(monkeypatch):
    from openubem.idf import surface_orientation as so

    def build():
        a = _box("A", 0, 0, 0, 5, 5, 3, True)
        b = _box("B", 5, 0, 0, 5, 5, 3, True)
        wa = next(s for s in a if s.Name == "A_w1")
        wb = next(s for s in b if s.Name == "B_w3")
        wa.Outside_Boundary_Condition, wa.Outside_Boundary_Condition_Object = "Surface", "B_w3"
        wb.Outside_Boundary_Condition, wb.Outside_Boundary_Condition_Object = "Surface", "A_w1"
        return Idf(a + b)

    real = so._wall_probe

    def forced(mode):
        def probe(pts, polys, centre):
            facing, how, margin = real(pts, polys, centre)
            return facing, "fallback" if mode(pts) else how, margin
        return probe

    idf = build()
    monkeypatch.setattr(so, "_wall_probe", forced(lambda pts: min(p[0] for p in pts) == 5.0))
    res = so.normalise_surface_orientation(idf)
    assert res["interzone_opposite"] == res["interzone_pairs"] == 1
    assert res["pair_rule3"] == []

    idf = build()
    monkeypatch.setattr(so, "_wall_probe", forced(lambda pts: True))
    res = so.normalise_surface_orientation(idf)
    assert res["interzone_opposite"] == res["interzone_pairs"] == 1


_U_FLOOR = [(0, 0, 0), (10, 0, 0), (10, 5, 0), (6, 5, 0), (6, 3, 0), (4, 3, 0), (4, 5, 0), (0, 5, 0)]


def _wall_pts(x0, x1, y=5.0, up=True):
    pts = [(x0, y, 3), (x0, y, 0), (x1, y, 0), (x1, y, 3)]
    return pts if up else pts[::-1]


def test_vote_decides_when_the_centre_probe_is_ambiguous():
    from openubem.idf import surface_orientation as so

    pts = _wall_pts(0, 10)
    n = _newell(pts)
    assert n[1] != 0
    ux, uy = 0.0, n[1] / abs(n[1])
    cx, cy = 5.0, 5.0
    assert not so._inside((cx + 0.2 * ux, cy + 0.2 * uy), _U_FLOOR)
    assert not so._inside((cx - 0.2 * ux, cy - 0.2 * uy), _U_FLOOR)
    facing, how, _ = so._wall_probe(pts, [_U_FLOOR], (5.0, 2.5))
    assert how == "vote"
    flipped = so._wall_probe(pts[::-1], [_U_FLOOR], (5.0, 2.5))
    assert flipped[1] == "vote"
    assert {facing, flipped[0]} == {"outward", "inward"}


def test_sliver_floor_does_not_decide():
    from openubem.idf import surface_orientation as so

    sliver = [(4.95, 5.0, 0), (5.05, 5.0, 0), (5.05, 5.1, 0), (4.95, 5.1, 0)]
    pts = _wall_pts(4.6, 5.4)
    facing, how, _ = so._wall_probe(pts, [_U_FLOOR, sliver], (5.0, 2.5))
    assert (facing, how) == so._wall_probe(pts, [_U_FLOOR], (5.0, 2.5))[:2]
    assert how == "fallback"


def test_pair_rule_four_stronger_vote_wins(monkeypatch):
    from openubem.idf import surface_orientation as so

    a = _box("A", 0, 0, 0, 5, 5, 3, True)
    b = _box("B", 5, 0, 0, 5, 5, 3, True)
    wa = next(s for s in a if s.Name == "A_w1")
    wb = next(s for s in b if s.Name == "B_w3")
    wa.Outside_Boundary_Condition, wa.Outside_Boundary_Condition_Object = "Surface", "B_w3"
    wb.Outside_Boundary_Condition, wb.Outside_Boundary_Condition_Object = "Surface", "A_w1"
    idf = Idf(a + b)
    real = so._wall_probe

    key_a, key_b = tuple(wa.coords), tuple(wb.coords)

    def probe(pts, polys, centre):
        facing, how, margin = real(pts, polys, centre)
        if tuple(pts) == key_a:
            return facing, "vote", 10
        if tuple(pts) == key_b:
            return ("inward" if facing == "outward" else "outward"), "edge", 0
        return facing, how, margin

    monkeypatch.setattr(so, "_wall_probe", probe)
    n_before = _newell(wa.coords)
    res = so.normalise_surface_orientation(idf)
    assert res["pair_rule4"] == 1
    assert res["pair_rule3"] == []
    assert res["interzone_opposite"] == res["interzone_pairs"] == 1
    assert _newell(wa.coords) == n_before
    assert _newell(wa.coords)[0] > 0
    assert _newell(wb.coords)[0] < 0
