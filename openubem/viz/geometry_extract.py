"""IDF -> raw 3D geometry extraction, standalone (T01).

Ported from the sibling `idf_reader` repo's `idf_to_sketchup.py::collect_geometry`
plus the low-level IDF-vertex parsers it depends on (`visualizer_adapter.py`).
Behaviour is preserved exactly (same GlobalGeometryRules handling, zone-origin
offsets, LOD-N/LOD-B split via `faces`/`subwin`, neighbour-aware window push-out
clamp, merged-neighbourhood sub-surface repair, recentring), with one additive
change: every `faces`/`subwin` record now carries the EnergyPlus object's own
`Name` field as a 5th tuple element -- the stable per-surface feature ID used by
downstream CityJSON attribute binding (T05) and browser picking (T09).

One bug fix relative to the ported source, found live during T02's real-pilot
spike: `_parse_fen_vertices`'s fallback branch (taken when the primary integer
scan for "Number of Vertices" comes up empty) did not skip the literal string
"autocalculate" when it appears as the Number-of-Vertices field value itself
(only blank values were skipped) -- so on this pipeline's real IDFs, which
write "autocalculate" as text rather than leaving the field blank, the
fallback scan hit that token first and aborted, silently dropping every
FenestrationSurface:Detailed (0/738 buildings showed any window/door geometry
on the nyc_centre pilot before this fix). See T02 progress-log entry.

NOT ported (out of scope for this module):
  - matplotlib painter's-order workarounds (`visualizer_adapter` rendering code)
  - the SketchUp Ruby emitter (`idf_to_sketchup._emit_ruby` and friends)
  - zone-multiplier floor expansion (`idf_to_sketchup._expand_floor_multipliers`
    and its helpers) -- a "pure visual post-process" for the Ruby/COLLADA full-
    floor export that would synthesize floor geometry not literally present in
    the IDF; out of scope per the faithful-to-model rule (PLAN_3dviz_implementation.md
    Sec 2.4) and not needed by any T01/T02 consumer. `collect_geometry` here has
    no `expand_multipliers` parameter as a result -- see T01 progress-log entry.
"""

from __future__ import annotations

import os
import re

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:  # pragma: no cover - numpy is a hard project dependency
    _HAS_NUMPY = False

# ---------------------------------------------------------------------------
# IDF tokenizer (ported from idf_reader/idf_parser.py::parse_idf)
# ---------------------------------------------------------------------------


def parse_idf(file_path: str) -> dict[str, list[list[str]]]:
    """Parse an EnergyPlus IDF file into a dict of object-type -> field lists.

    Args:
        file_path: Absolute path to the .idf file.

    Returns:
        Dict keyed by upper-cased object type; each value is a list of objects,
        each object a list of its field values (strings, type name stripped).

    Raises:
        FileNotFoundError: If file_path does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"IDF file not found: {file_path}")

    idf_data: dict[str, list[list[str]]] = {}

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    content = re.sub(r"!.*", "", content)
    raw_objects = content.split(";")

    for obj in raw_objects:
        clean_obj = obj.strip()
        if not clean_obj:
            continue
        fields = [f.strip() for f in clean_obj.split(",")]
        if not fields:
            continue
        obj_type = fields[0].upper()
        obj_values = fields[1:] if len(fields) > 1 else []
        idf_data.setdefault(obj_type, []).append(obj_values)

    return idf_data


# ---------------------------------------------------------------------------
# Constants (ported from idf_to_sketchup.py)
# ---------------------------------------------------------------------------

# Re-centre geometry when its XY centroid sits far from the origin (big
# baked-in world coordinates hurt CAD/WebGL precision). Mirrors
# visualizer_adapter/idf_to_sketchup behaviour.
_RECENTRE_THRESHOLD = 50.0  # metres

# Outward push for window/door faces so they do not z-fight the parent wall.
# Pushed along the parent wall's outward normal (see collect_geometry), so the
# direction is correct per-facade regardless of where the building sits.
_WIN_OFFSET = 0.15  # metres

_BUILDING_RE = re.compile(r"^(B\d+)_", re.IGNORECASE)

# Category keys collect_geometry can emit (colour/style assignment is T10's
# job, not this module's -- kept here only as the counts-dict vocabulary).
_CATEGORY_KEYS = (
    "wall", "roof", "floor", "interior", "slab",
    "window", "door", "shading", "ground", "label",
)

# Known EnergyPlus 8.x boundary condition keywords at field[4]
_BOUNDARY_KEYWORDS = {
    "outdoors", "ground", "surface", "zone", "othersidecoefficients",
    "othersideconditionsmodel", "adiabatic", "foundation",
}


# ---------------------------------------------------------------------------
# Low-level IDF-vertex parsers (ported from visualizer_adapter.py)
# ---------------------------------------------------------------------------


def _safe_float(val: str, default: float = 0.0) -> float:
    """Parse float from an IDF field string; return default on failure."""
    try:
        return float(val.strip()) if val and val.strip() else default
    except ValueError:
        return default


def _is_relative_coords(idf_data: dict) -> bool:
    """Return True when GlobalGeometryRules uses a Relative coordinate system."""
    ggr_list = idf_data.get("GLOBALGEOMETRYRULES", [])
    if not ggr_list:
        return True  # EnergyPlus default is Relative
    ggr = ggr_list[0]
    # values[0]=StartingVertex, [1]=Direction, [2]=CoordinateSystem
    if len(ggr) >= 3:
        return ggr[2].strip().lower() != "absolute"
    return True


def _build_zone_origins(idf_data: dict) -> dict[str, tuple[float, float, float]]:
    """Build zone-name -> (dx, dy, dz) origin lookup."""
    origins: dict[str, tuple[float, float, float]] = {}
    for zone in idf_data.get("ZONE", []):
        if not zone:
            continue
        # values: 0=Name, 1=DirRelNorth, 2=X_Origin, 3=Y_Origin, 4=Z_Origin
        name = zone[0]
        dx = _safe_float(zone[2]) if len(zone) > 2 else 0.0
        dy = _safe_float(zone[3]) if len(zone) > 3 else 0.0
        dz = _safe_float(zone[4]) if len(zone) > 4 else 0.0
        origins[name] = (dx, dy, dz)
    return origins


def _bsd_offsets(fields: list[str]) -> tuple[int, int, int, int]:
    """Detect field layout for BuildingSurface:Detailed objects.

    EnergyPlus 9+ added a 'Space Name' field at index 4, shifting all
    subsequent fields by one position. EnergyPlus 8.x files do not have this
    field so boundary conditions start at index 4 instead of 5.

    Returns:
        (zone_idx, boundary_idx, num_vertices_idx, vertex_start_idx).
    """
    if len(fields) > 4 and fields[4].strip().lower() in _BOUNDARY_KEYWORDS:
        return 3, 4, 9, 10   # 8.x layout (no Space Name)
    return 3, 5, 10, 11      # 9+ layout (Space Name at field[4])


def _parse_bsd_vertices(
    fields: list[str],
    dx: float,
    dy: float,
    dz: float,
    num_v_idx: int = 10,
    vertex_start: int = 11,
) -> list[tuple[float, float, float]]:
    """Extract world-space vertex list from a BuildingSurface:Detailed record."""
    try:
        raw_count = fields[num_v_idx].strip().lower()
        if raw_count in ("", "autocalculate"):
            raw_floats = [v for v in fields[vertex_start:] if v.strip()]
            num_v = len(raw_floats) // 3
        else:
            num_v = int(raw_count)
            raw_floats = [
                v for v in fields[vertex_start:vertex_start + num_v * 3]
                if v.strip()
            ]
        raw = [float(v) for v in raw_floats]
        return [
            (raw[i] + dx, raw[i + 1] + dy, raw[i + 2] + dz)
            for i in range(0, num_v * 3, 3)
        ]
    except (ValueError, IndexError):
        return []


def _parse_fen_vertices(
    fields: list[str],
    dx: float,
    dy: float,
    dz: float,
) -> list[tuple[float, float, float]]:
    """Extract world-space vertex list from a FenestrationSurface:Detailed record.

    IDF values (after object-type stripped), 0-indexed:
      0  Name
      1  Surface Type (Window / Door ...)
      2  Construction Name
      3  Building Surface Name    <- parent wall
      4  Outside Boundary Condition Object
      5  View Factor to Ground
      6  Frame and Divider Name
      7  Multiplier
      8  Number of Vertices       <- parse from here
      9+ X1, Y1, Z1, X2, Y2, Z2, ...
    """
    try:
        nv_idx = None
        num_v = None
        vs_idx = None
        for k in range(5, min(12, len(fields))):
            val = fields[k].strip().lower()
            if not val or val == "autocalculate":
                continue
            try:
                candidate = int(val)
                if 3 <= candidate <= 120:
                    nv_idx = k
                    num_v = candidate
                    vs_idx = k + 1
                    break
            except ValueError:
                pass
        if nv_idx is None:
            raw_candidates = []
            for v in fields[8:]:
                v = v.strip()
                # Skip the (blank OR literal 'autocalculate') Number-of-Vertices
                # slot itself -- real-world IDFs from this pipeline's builder
                # write "autocalculate" as text, not a blank field, which the
                # original ported fallback did not skip (T01 bug fix, T02
                # discovery: this silently dropped 100% of fenestration
                # surfaces across the nyc_centre pilot).
                if not v or v.lower() == "autocalculate":
                    continue
                try:
                    raw_candidates.append(float(v))
                except ValueError:
                    break
            if len(raw_candidates) >= 9 and len(raw_candidates) % 3 == 0:
                num_v = len(raw_candidates) // 3
                raw = raw_candidates
                return [
                    (raw[i] + dx, raw[i + 1] + dy, raw[i + 2] + dz)
                    for i in range(0, num_v * 3, 3)
                ]
            return []
        raw_floats = [v for v in fields[vs_idx:vs_idx + num_v * 3] if v.strip()]
        raw = [float(v) for v in raw_floats]
        return [
            (raw[i] + dx, raw[i + 1] + dy, raw[i + 2] + dz)
            for i in range(0, num_v * 3, 3)
        ]
    except (ValueError, IndexError):
        return []


def _parse_shading_vertices(
    fields: list[str],
    dx: float = 0.0,
    dy: float = 0.0,
    dz: float = 0.0,
) -> list[tuple[float, float, float]]:
    """Extract world-space vertex list from a Shading:Building:Detailed record."""
    try:
        raw_floats = [v for v in fields[3:] if v.strip()]
        raw = [float(v) for v in raw_floats]
        num_v = len(raw) // 3
        return [
            (raw[i] + dx, raw[i + 1] + dy, raw[i + 2] + dz)
            for i in range(0, num_v * 3, 3)
        ]
    except (ValueError, IndexError):
        return []


def _parse_window_relative(
    fields: list[str],
    parent_verts: list[tuple[float, float, float]],
) -> list[tuple[float, float, float]]:
    """Convert relative Window object geometry to absolute 3D coordinates.

    IDF values for Window, 0-indexed:
      0 Name, 1 Construction Name, 2 Building Surface Name (parent wall),
      3 Frame and divider name, 4 Multiplier,
      5 Starting X (rel. to wall bottom-left), 6 Starting Z, 7 Length, 8 Height
    """
    if len(fields) < 9 or len(parent_verts) < 3 or not _HAS_NUMPY:
        return []

    try:
        start_x = float(fields[5])
        start_z = float(fields[6])
        length = float(fields[7])
        height = float(fields[8])

        # Step 1: find the "Bottom Left" vertex of the parent wall.
        # EnergyPlus surfaces are CCW from outside.
        n = len(parent_verts)
        zs = [v[2] for v in parent_verts]
        min_z = min(zs)

        origin_idx = 0
        for i in range(n):
            if abs(zs[i] - min_z) < 1e-4 and abs(zs[(i - 1) % n] - min_z) > 1e-4:
                origin_idx = i
                break

        v1_p = parent_verts[origin_idx]
        v2_p = parent_verts[(origin_idx + 1) % n]  # Bottom Right
        v0_p = parent_verts[(origin_idx - 1) % n]  # Top Left

        v1 = np.array(v1_p)
        v2 = np.array(v2_p)
        v0 = np.array(v0_p)

        vec_x_full = v2 - v1
        len_x = np.linalg.norm(vec_x_full)
        if len_x == 0:
            return []
        dir_x = vec_x_full / len_x

        vec_z_full = v0 - v1
        len_z = np.linalg.norm(vec_z_full)
        if len_z == 0:
            return []
        dir_z = vec_z_full / len_z

        w_bl = v1 + (dir_x * start_x) + (dir_z * start_z)
        w_br = w_bl + (dir_x * length)
        w_tl = w_bl + (dir_z * height)
        w_tr = w_br + (dir_z * height)

        return [tuple(w_tl), tuple(w_bl), tuple(w_br), tuple(w_tr)]

    except (ValueError, IndexError):
        return []


# ---------------------------------------------------------------------------
# Local helpers (ported from idf_to_sketchup.py)
# ---------------------------------------------------------------------------


def _surface_normal(verts):
    """Unit outward normal of a polygon (Newell's method). Zero vector if degenerate."""
    if not _HAS_NUMPY or len(verts) < 3:
        return (0.0, 0.0, 0.0)
    n = np.zeros(3)
    m = len(verts)
    for i in range(m):
        cur = np.array(verts[i], dtype=float)
        nxt = np.array(verts[(i + 1) % m], dtype=float)
        n[0] += (cur[1] - nxt[1]) * (cur[2] + nxt[2])
        n[1] += (cur[2] - nxt[2]) * (cur[0] + nxt[0])
        n[2] += (cur[0] - nxt[0]) * (cur[1] + nxt[1])
    norm = np.linalg.norm(n)
    if norm < 1e-12:
        return (0.0, 0.0, 0.0)
    n = n / norm
    return (float(n[0]), float(n[1]), float(n[2]))


def _snap_subsurface_to_parent(fv, wall_verts):
    """Repair a sub-surface (window/door) left in zone-local coords by an NU
    merge while its host wall is world-absolute.

    Some merged-neighbourhood IDFs world-place the BuildingSurfaces but leave
    the FenestrationSurface vertices in the zone's local frame (Zone.Origin
    stripped to 0). If `fv` already lies on `wall_verts` it is returned
    unchanged; otherwise it is snapped onto the parent wall plane. Only
    axis-aligned vertical walls are repaired.
    """
    if not _HAS_NUMPY or len(fv) < 3 or len(wall_verts) < 3:
        return fv
    n = _surface_normal(wall_verts)
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if az > 0.5 or max(ax, ay) < 0.9:
        return fv  # not a clean vertical facade; do not touch

    wxs = [v[0] for v in wall_verts]
    wys = [v[1] for v in wall_verts]
    wzs = [v[2] for v in wall_verts]
    wall_cx = sum(wxs) / len(wxs)
    wall_cy = sum(wys) / len(wys)
    wall_min_z, wall_max_z = min(wzs), max(wzs)

    fxs = [v[0] for v in fv]
    fys = [v[1] for v in fv]
    fzs = [v[2] for v in fv]
    win_cx = sum(fxs) / len(fxs)
    win_cy = sum(fys) / len(fys)
    win_min_z = min(fzs)

    perp_x = ax >= ay  # True -> E/W wall (normal along X); False -> N/S wall
    if perp_x:
        on_plane = abs(win_cx - wall_cx) < 0.5
        within = (min(wys) - 0.5 <= win_cy <= max(wys) + 0.5
                  and wall_min_z - 0.5 <= win_min_z <= wall_max_z + 0.5)
    else:
        on_plane = abs(win_cy - wall_cy) < 0.5
        within = (min(wxs) - 0.5 <= win_cx <= max(wxs) + 0.5
                  and wall_min_z - 0.5 <= win_min_z <= wall_max_z + 0.5)
    if on_plane and within:
        return fv  # already correctly placed on its wall

    lat_shift = (wall_cx - win_cx) if not perp_x else (wall_cy - win_cy)
    out = []
    for (x, y, z) in fv:
        if perp_x:
            out.append((wall_cx, y + lat_shift, wall_min_z + z))
        else:
            out.append((x + lat_shift, wall_cy, wall_min_z + z))
    return out


def _door_to_window_fields(door):
    """Map a Door field list onto the Window field layout expected by
    _parse_window_relative.

    Door has no 'Frame and Divider Name' field, so it is one slot shorter than
    Window. We splice a placeholder so StartX..Height land at indices 5..8.
    """
    if len(door) < 8:
        return None
    return [door[0], door[1], door[2], "", door[3],
            door[4], door[5], door[6], door[7]]


def _classify(surf_type, boundary):
    """Return the category key for a BuildingSurface:Detailed."""
    st = surf_type
    bc = boundary
    exterior = "outdoors" in bc
    ground = "ground" in bc
    interior = bc in ("surface", "zone", "adiabatic")
    if st in ("roof", "ceiling") and exterior:
        return "roof"
    if st == "floor" and (ground or exterior):
        return "floor"
    if st == "wall" and exterior:
        return "wall"
    if st in ("floor", "ceiling", "roof") and interior:
        return "slab"
    if interior:
        return "interior"
    if st in ("roof", "ceiling"):
        return "interior"
    if st == "floor":
        return "floor"
    return "wall"


def _building_key(zone_name):
    m = _BUILDING_RE.match(zone_name or "")
    return m.group(1).upper() if m else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def collect_geometry(idf_path, building_name=None, recentre=True):
    """Parse an IDF and return its geometry, grouped and recentred.

    All vertices are in METRES, recentre shift already applied. Every
    `faces`/`subwin` record carries the EnergyPlus object's own `Name` field
    as a 5th tuple element -- the stable per-surface feature ID (T01
    additive change; not present in the ported idf_reader source).

    Args:
        idf_path:      Path to the EnergyPlus .idf file.
        building_name: Override site/group name. Defaults to IDF stem.
        recentre:      Shift geometry toward the origin when far from it.

    Returns a dict with keys:
        site_name, stem, multi_building,
        faces:  list of (building_key, zone_name, category, verts, surf_name)
        subwin: list of (building_key, zone_name, category, verts, surf_name)
        shade_faces: list of verts
        counts: {category: int}
        recentre_offset: (sx, sy, sz) -- the shift SUBTRACTED from every vertex.
            Stored, not applied to anything downstream; kept for future V07
            geo-referencing (add it back to recover true world coordinates).
    """
    idf_data = parse_idf(idf_path)
    stem = os.path.splitext(os.path.basename(idf_path))[0]
    site_name = building_name or stem

    surfaces = idf_data.get("BUILDINGSURFACE:DETAILED", [])
    fenestr = idf_data.get("FENESTRATIONSURFACE:DETAILED", [])
    windows = idf_data.get("WINDOW", [])
    doors = idf_data.get("DOOR", [])
    shading = (idf_data.get("SHADING:BUILDING:DETAILED", [])
               + idf_data.get("SHADING:ZONE:DETAILED", []))

    if not surfaces:
        raise ValueError(f"No BuildingSurface:Detailed objects in {idf_path}")

    is_relative = _is_relative_coords(idf_data)
    zone_origins = _build_zone_origins(idf_data) if is_relative else {}

    # Index sub-surfaces by parent wall name (upper-cased).
    fen_by_parent = {}
    for fen in fenestr:
        if len(fen) >= 4 and fen[3].strip():
            fen_by_parent.setdefault(fen[3].upper(), []).append(fen)
    win_by_parent = {}
    for win in windows:
        if len(win) >= 3 and win[2].strip():
            win_by_parent.setdefault(win[2].upper(), []).append(win)
    door_by_parent = {}
    for door in doors:
        if len(door) >= 3 and door[2].strip():
            door_by_parent.setdefault(door[2].upper(), []).append(door)

    # ---- Pass 1a: build per-building exterior wall plane index --------------
    # Used by the neighbour-aware push clamp (Pass 1b). Stores, for each
    # quantized normal direction, a list of (bkey, plane_d, bbox) where
    # plane_d = normal dot any vertex (the plane intercept), and bbox is the
    # 6-tuple (minx, miny, minz, maxx, maxy, maxz) of the wall polygon.

    def _qnorm(n):
        ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
        if ax >= ay and ax >= az:
            return (1, 0, 0) if n[0] >= 0 else (-1, 0, 0)
        elif ay >= az:
            return (0, 1, 0) if n[1] >= 0 else (0, -1, 0)
        else:
            return (0, 0, 1) if n[2] >= 0 else (0, 0, -1)

    wall_plane_index = {}

    for surf in surfaces:
        if len(surf) < 12:
            continue
        z_idx, bc_idx, nv_idx, vs_idx = _bsd_offsets(surf)
        surf_type_s = (surf[1].strip().lower() if surf[1] else "")
        if surf_type_s != "wall":
            continue
        zone_name_s = surf[z_idx].strip() if len(surf) > z_idx else ""
        bkey_s = _building_key(zone_name_s) or site_name
        dx_s, dy_s, dz_s = zone_origins.get(zone_name_s, (0.0, 0.0, 0.0))
        wv = _parse_bsd_vertices(surf, dx_s, dy_s, dz_s,
                                 vertex_start=vs_idx, num_v_idx=nv_idx)
        if len(wv) < 3:
            continue
        wn = _surface_normal(wv)
        if wn == (0.0, 0.0, 0.0):
            continue
        ax, ay, az = abs(wn[0]), abs(wn[1]), abs(wn[2])
        dom = max(ax, ay, az)
        if dom < 0.99:
            continue
        qk = _qnorm(wn)
        p0 = wv[0]
        plane_d = wn[0] * p0[0] + wn[1] * p0[1] + wn[2] * p0[2]
        xs = [v[0] for v in wv]; ys = [v[1] for v in wv]; zs = [v[2] for v in wv]
        bbox = (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
        wall_plane_index.setdefault(qk, []).append((bkey_s, plane_d, bbox))

    def _clamped_push(win_verts, normal, parent_bkey):
        if not wall_plane_index:
            return _WIN_OFFSET
        qk = _qnorm(normal)
        qk_opp = (-qk[0], -qk[1], -qk[2])
        bucket = wall_plane_index.get(qk, []) + wall_plane_index.get(qk_opp, [])
        if not bucket:
            return _WIN_OFFSET

        cx = sum(v[0] for v in win_verts) / len(win_verts)
        cy = sum(v[1] for v in win_verts) / len(win_verts)
        cz = sum(v[2] for v in win_verts) / len(win_verts)
        wz_min = min(v[2] for v in win_verts)
        wz_max = max(v[2] for v in win_verts)

        pcx = cx + normal[0] * _WIN_OFFSET
        pcy = cy + normal[1] * _WIN_OFFSET

        parent_d = normal[0] * cx + normal[1] * cy + normal[2] * cz

        _INF = 1e9
        closest_gap = _INF

        for (fbkey, fplane_d, fbbox) in bucket:
            if fbkey == parent_bkey:
                continue
            gap_same = (normal[0]*qk[0]+normal[1]*qk[1]+normal[2]*qk[2])*fplane_d - parent_d
            gap_opp  = (normal[0]*qk_opp[0]+normal[1]*qk_opp[1]+normal[2]*qk_opp[2])*fplane_d - parent_d
            gap = None
            for g in (gap_same, gap_opp):
                if 0.0 < g <= _WIN_OFFSET + 0.05:
                    if gap is None or g < gap:
                        gap = g
            if gap is None:
                continue

            minx, miny, minz, maxx, maxy, maxz = fbbox
            if (pcx < minx - 1.0 or pcx > maxx + 1.0
                    or pcy < miny - 1.0 or pcy > maxy + 1.0):
                continue
            if maxz < wz_min - 0.5 or minz > wz_max + 0.5:
                continue

            if gap < closest_gap:
                closest_gap = gap

        if closest_gap >= _INF:
            return _WIN_OFFSET  # no blocking neighbour found
        return min(_WIN_OFFSET, max(0.02, closest_gap - 0.05))

    # ---- Pass 1b: collect every face and emit windows with clamped push -----
    faces = []   # opaque + interior building surfaces
    subwin = []  # windows/doors: (building, zone, category, verts, surf_name)
    counts = {k: 0 for k in _CATEGORY_KEYS}
    all_x, all_y, all_z = [], [], []

    for surf in surfaces:
        if len(surf) < 12:
            continue
        z_idx, bc_idx, nv_idx, vs_idx = _bsd_offsets(surf)
        surf_name = surf[0]
        surf_type = (surf[1].strip().lower() if surf[1] else "")
        zone_name = surf[z_idx].strip() if len(surf) > z_idx else ""
        boundary = (surf[bc_idx].strip().lower()
                    if len(surf) > bc_idx and surf[bc_idx] else "")
        dx, dy, dz = zone_origins.get(zone_name, (0.0, 0.0, 0.0))
        verts = _parse_bsd_vertices(surf, dx, dy, dz,
                                    vertex_start=vs_idx, num_v_idx=nv_idx)
        if len(verts) < 3:
            continue

        category = _classify(surf_type, boundary)
        bkey = _building_key(zone_name) or site_name
        faces.append((bkey, zone_name, category, verts, surf_name))
        counts[category] += 1
        for v in verts:
            all_x.append(v[0]); all_y.append(v[1]); all_z.append(v[2])

        # Sub-surfaces hosted by this wall (windows on exterior walls only).
        is_ext_wall = surf_type == "wall" and "outdoors" in boundary
        if not is_ext_wall:
            continue
        normal = _surface_normal(verts)

        for fen in fen_by_parent.get(surf_name.upper(), []):
            fv = _parse_fen_vertices(fen, dx, dy, dz)
            if len(fv) >= 3:
                fv = _snap_subsurface_to_parent(fv, verts)
                push_d = _clamped_push(fv, normal, bkey)
                push = tuple(c * push_d for c in normal)
                fv = [(x + push[0], y + push[1], z + push[2]) for (x, y, z) in fv]
                subwin.append((bkey, zone_name, "window", fv, fen[0]))
                counts["window"] += 1
        for win in win_by_parent.get(surf_name.upper(), []):
            wv = _parse_window_relative(win, verts)
            if len(wv) >= 3:
                push_d = _clamped_push(wv, normal, bkey)
                push = tuple(c * push_d for c in normal)
                wv = [(x + push[0], y + push[1], z + push[2]) for (x, y, z) in wv]
                subwin.append((bkey, zone_name, "window", wv, win[0]))
                counts["window"] += 1
        for door in door_by_parent.get(surf_name.upper(), []):
            df = _door_to_window_fields(door)
            if not df:
                continue
            dv = _parse_window_relative(df, verts)
            if len(dv) >= 3:
                push_d = _clamped_push(dv, normal, bkey)
                push = tuple(c * push_d for c in normal)
                dv = [(x + push[0], y + push[1], z + push[2]) for (x, y, z) in dv]
                subwin.append((bkey, zone_name, "door", dv, door[0]))
                counts["door"] += 1

    # Shading (absolute world coords; no zone offset).
    shade_faces = []
    for sh in shading:
        if len(sh) < 6:
            continue
        sv = _parse_shading_vertices(sh)
        if len(sv) >= 3:
            shade_faces.append(sv)
            counts["shading"] += 1
            for v in sv:
                all_x.append(v[0]); all_y.append(v[1]); all_z.append(v[2])

    # ---- Re-centre ----
    sx = sy = sz = 0.0
    if recentre and all_x and all_y:
        cx = (max(all_x) + min(all_x)) / 2.0
        cy = (max(all_y) + min(all_y)) / 2.0
        if abs(cx) > _RECENTRE_THRESHOLD or abs(cy) > _RECENTRE_THRESHOLD:
            sx, sy = cx, cy
            sz = min(all_z)  # drop the model onto z=0

    def _shift(vlist):
        return [(x - sx, y - sy, z - sz) for (x, y, z) in vlist]

    faces = [(b, z, c, _shift(v), sn) for (b, z, c, v, sn) in faces]
    subwin = [(b, z, c, _shift(v), sn) for (b, z, c, v, sn) in subwin]
    shade_faces = [_shift(v) for v in shade_faces]

    return {
        "site_name": site_name,
        "stem": stem,
        "multi_building": len({f[0] for f in faces}) > 1,
        "faces": faces,
        "subwin": subwin,
        "shade_faces": shade_faces,
        "counts": counts,
        "recentre_offset": (sx, sy, sz),
    }
