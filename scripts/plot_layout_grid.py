"""Layout visual grids: DOE reference vs layoutGenerator output, per archetype (T16/T17).

One PNG per supported archetype. MidriseApartment keeps its T16 hand-built DOE reference
panel; other archetypes (no simple hand-drawable DOE reference) use a generated reference
panel on their own DOE-plate compact bar, labeled with corridor/depth/bay dims. Archetypes
without complex_shapes_supported (hotels) degrade L/U/T/O/cross panels to a single per-floor
zone rather than leaving them blank, documenting the T13a correctness>coverage rule.
Output: openubem/outputs/LayoutGenerator/<file>.png
"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from shapely.geometry import box, LineString
from shapely.ops import unary_union
from shapely import affinity

from openubem.geometry.layoutGenerator import generate_layout, MODULE_SPECS, _long_edge_angle

OUT_DIR = Path(__file__).parent.parent / "openubem" / "outputs" / "LayoutGenerator"
_EDGE = "#22333b"
_DEGRADE_COLOR = "#a8998a"
_DEGRADE_LABEL = "per-floor (degraded)"
_DEGRADE_KEY = "__degrade__"

# Per-archetype space_type -> color. Corridor/Apartment are the original T16 pair, unchanged.
_SPACE_TYPE_COLORS = {
    "MidriseApartment": {"Corridor": "#c9c9c9", "Apartment": "#5b8fb0"},
    "SmallHotel": {"Corridor": "#c9c9c9", "GuestRoom": "#c9793f"},
    "LargeHotel": {"Corridor": "#c9c9c9", "GuestRoom": "#c9793f"},
}

ARCHETYPE_FILES = {
    "MidriseApartment": "layoutgenerator_doe_vs_generated.png",
    "SmallHotel": "layoutgrid_SmallHotel.png",
    "LargeHotel": "layoutgrid_LargeHotel.png",
}
# Pending T13b/T13c (no MODULE_SPECS rows yet): LargeOffice, PrimarySchool, SecondarySchool.

# Hotels share a fixed plate LENGTH (viz-only illustration constant, not DOE-cited) so
# SmallHotel vs LargeHotel differ by bay/corridor width alone, not by an incidental rescale.
# Plate WIDTH stays per-archetype real corridor_width_m + 2*unit_depth_m (MODULE_SPECS-traced).
HOTEL_BAR_LENGTH_COMPACT_M = 45.0
HOTEL_BAR_LENGTH_WIDE_M = 60.0


def _bar_plate_dims(archetype):
    """(length, width) of the double-loaded reference/compact-bar plate for an archetype."""
    if archetype == "MidriseApartment":
        return 46.33, 16.92  # DOE MidriseApartment plate (Deru 2011 Table 3.1.15) -- literal, unchanged from T16
    spec = MODULE_SPECS[archetype]
    width = spec["corridor_width_m"] + 2.0 * spec["unit_depth_m"]
    return HOTEL_BAR_LENGTH_COMPACT_M, width


def _wide_bar_dims(archetype):
    """(length, width) of a wider stress-test bar, same shared-plate rule as the compact bar."""
    if archetype == "MidriseApartment":
        return 60.0, 20.0  # literal, unchanged from T16
    spec = MODULE_SPECS[archetype]
    width = spec["corridor_width_m"] + 2.0 * spec["unit_depth_m"]
    return HOTEL_BAR_LENGTH_WIDE_M, width


def _footprint_set(archetype):
    """[(name, polygon), ...]; index 0 is always "Compact bar"."""
    bar_l, bar_w = _bar_plate_dims(archetype)
    wide_l, wide_w = _wide_bar_dims(archetype)
    L = unary_union([box(0, 0, 40, 15), box(0, 0, 15, 40)])
    U = unary_union([box(0, 0, 40, 15), box(0, 0, 12, 40), box(28, 0, 40, 40)])
    T = unary_union([box(0, 30, 40, 45), box(14, 0, 26, 45)])
    O = box(0, 0, 50, 50).difference(box(15, 15, 35, 35))
    return [
        ("Compact bar", box(0, 0, bar_l, bar_w)),
        ("L-shape", L),
        ("U-shape", U),
        ("T-shape", T),
        ("Courtyard (O)", O),
        ("L-shape rotated 30°", affinity.rotate(L, 30, origin=(3, 7))),
        ("Wide bar", box(0, 0, wide_l, wide_w)),
        ("Cross", unary_union([box(15, 0, 27, 45), box(0, 16, 42, 29)])),
    ]


def _doe_reference_zones():
    """DOE MidriseApartment single floor: 8 units (2 rows x 4) + full-length central corridor."""
    spec = MODULE_SPECS["MidriseApartment"]
    plate_w, plate_h = 46.33, 16.92
    c = spec["corridor_width_m"]
    bay = plate_w / 4.0                      # 4 units per row
    cy0, cy1 = (plate_h - c) / 2.0, (plate_h + c) / 2.0
    zones = [{"polygon": box(0, cy0, plate_w, cy1), "space_type": "Corridor"}]
    for i in range(4):
        x0 = i * bay
        zones.append({"polygon": box(x0, 0, x0 + bay, cy0), "space_type": "Apartment"})
        zones.append({"polygon": box(x0, cy1, x0 + bay, plate_h), "space_type": "Apartment"})
    return zones


def _generated_zones(poly, archetype):
    z = generate_layout("viz", poly, archetype, 1)
    return [{"polygon": d["floor_polygon"], "space_type": d.get("space_type", "")}
            for d in z if "_F0_" in d["name"]]


def _zone_room_segments(poly, bay_width_m):
    """Room-division lines (clipped to poly) + room count for one merged room zone.

    Subdivides along the ZONE'S OWN long axis (per-zone OBB via _long_edge_angle), so
    rotated shapes and end-cap bands (whose long axis runs across, not along, the wing)
    are each handled in their own local frame rather than the world/wing frame.
    """
    angle = _long_edge_angle(poly.minimum_rotated_rectangle)
    origin = poly.centroid
    rot = affinity.rotate(poly, -angle, origin=origin)
    minx, miny, maxx, maxy = rot.bounds
    span = maxx - minx  # long axis after alignment (Lx >= Ly by long-edge convention)
    n_rooms = max(1, int(span / bay_width_m + 0.5))
    lines = []
    for i in range(1, n_rooms):
        x = minx + i * (span / n_rooms)
        cut = affinity.rotate(LineString([(x, miny), (x, maxy)]), angle, origin=origin)
        clipped = cut.intersection(poly)
        if not clipped.is_empty:
            lines.append(clipped)
    return lines, n_rooms


def _panel_room_count(zones, bay_width_m, room_space_type):
    total = 0
    for zd in zones:
        if zd["space_type"] == room_space_type:
            _, n_rooms = _zone_room_segments(zd["polygon"], bay_width_m)
            total += n_rooms
    return total


def _reference_panel(archetype, compact_poly):
    spec = MODULE_SPECS[archetype]
    if archetype == "MidriseApartment":
        zones = _doe_reference_zones()
        room_count = _panel_room_count(zones, spec["bay_width_m"], spec["unit_space_type"])
        return f"DOE MidriseApartment\n(reference)\n({room_count} rooms · {len(zones)} zones)", zones
    zones = _generated_zones(compact_poly, archetype)
    room_count = _panel_room_count(zones, spec["bay_width_m"], spec["unit_space_type"])
    title = (f"{archetype} DOE reference\ncorridor {spec['corridor_width_m']:.2f} / "
             f"depth {spec['unit_depth_m']:.2f} / bay {spec['bay_width_m']:.2f} m\n"
             f"({room_count} rooms · {len(zones)} zones)")
    return title, zones


def _draw(ax, zones, title, colors, bay_width_m=None, room_space_type=None):
    for zd in zones:
        p = zd["polygon"]
        xs, ys = p.exterior.xy
        ax.fill(xs, ys, facecolor=colors.get(zd["space_type"], _DEGRADE_COLOR),
                edgecolor=_EDGE, linewidth=1.1)
        if bay_width_m and zd["space_type"] == room_space_type:
            lines, _ = _zone_room_segments(p, bay_width_m)
            for ln in lines:
                segs = ln.geoms if ln.geom_type.startswith("Multi") else [ln]
                for seg in segs:
                    lx, ly = seg.xy
                    ax.plot(lx, ly, color=_EDGE, linewidth=0.6)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def _plot_archetype(archetype, out_path):
    footprints = _footprint_set(archetype)
    colors = dict(_SPACE_TYPE_COLORS[archetype])
    spec = MODULE_SPECS[archetype]
    bay_width_m, room_space_type = spec["bay_width_m"], spec["unit_space_type"]

    if archetype == "MidriseApartment":
        ref_title, ref_zones = _reference_panel(archetype, footprints[0][1])
        loop_shapes = footprints  # apartment's hand-built ref is distinct from the generated compact bar
    else:
        ref_title, ref_zones = _reference_panel(archetype, footprints[0][1])
        loop_shapes = footprints[1:]  # compact bar already shown as the reference panel

    panels = [(ref_title, ref_zones)]
    used_degrade = False
    for name, poly in loop_shapes:
        zones = _generated_zones(poly, archetype)
        if not zones:
            zones = [{"polygon": poly, "space_type": _DEGRADE_KEY}]
            title = f"{name}\n(degrades to per-floor)"
            used_degrade = True
        else:
            room_count = _panel_room_count(zones, bay_width_m, room_space_type)
            title = f"{name}\n({room_count} rooms · {len(zones)} zones)"
        panels.append((title, zones))

    draw_colors = dict(colors)
    draw_colors[_DEGRADE_KEY] = _DEGRADE_COLOR

    n = len(panels)
    ncols = math.ceil(math.sqrt(n))
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 3.2 * nrows))
    axes = axes.ravel()
    for ax, (title, zones) in zip(axes, panels):
        _draw(ax, zones, title, draw_colors, bay_width_m, room_space_type)
    for ax in axes[n:]:
        ax.axis("off")

    if archetype == "MidriseApartment":
        suptitle = ("layoutGenerator: DOE reference vs generated MidriseApartment layouts\n"
                    "corridor (grey) + apartment zones (blue)")
    else:
        suptitle = f"layoutGenerator: DOE reference vs generated {archetype} layouts"
    fig.suptitle(suptitle, fontsize=13, y=0.99)

    legend_handles = [Patch(facecolor=c, edgecolor=_EDGE, label=st) for st, c in colors.items()]
    if used_degrade:
        legend_handles.append(Patch(facecolor=_DEGRADE_COLOR, edgecolor=_EDGE, label=_DEGRADE_LABEL))
    fig.legend(handles=legend_handles, loc="lower center", ncol=len(legend_handles), frameon=False)
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=130)
    print(f"wrote {out_path}")


def main():
    for archetype, filename in ARCHETYPE_FILES.items():
        _plot_archetype(archetype, OUT_DIR / filename)


if __name__ == "__main__":
    main()
