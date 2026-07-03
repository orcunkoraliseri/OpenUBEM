"""Layout visual grid: DOE MidriseApartment reference vs layoutGenerator output (T16).

Renders a single figure — panel 1 is the DOE MidriseApartment single-floor reference
(8 dwelling units + central corridor, from the pinned prototype dims); the rest are
generated room_layout floor plans for MidriseApartment across representative footprints,
zones colored by space type. Output: openubem/outputs/LayoutGenerator/layoutgenerator_doe_vs_generated.png
"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from shapely.geometry import box
from shapely.ops import unary_union
from shapely import affinity

from openubem.geometry.layoutGenerator import generate_layout, MODULE_SPECS

OUT = (Path(__file__).parent.parent / "openubem" / "outputs" / "LayoutGenerator"
       / "layoutgenerator_doe_vs_generated.png")
_COLOR = {"Corridor": "#c9c9c9", "Apartment": "#5b8fb0"}
_EDGE = "#22333b"


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


def _generated_zones(poly):
    z = generate_layout("viz", poly, "MidriseApartment", 1)
    return [{"polygon": d["floor_polygon"], "space_type": d.get("space_type", "Apartment")}
            for d in z if "_F0_" in d["name"]]


def _draw(ax, zones, title):
    for zd in zones:
        p = zd["polygon"]
        xs, ys = p.exterior.xy
        ax.fill(xs, ys, facecolor=_COLOR.get(zd["space_type"], "#5b8fb0"),
                edgecolor=_EDGE, linewidth=1.1)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def main():
    L = unary_union([box(0, 0, 40, 15), box(0, 0, 15, 40)])
    U = unary_union([box(0, 0, 40, 15), box(0, 0, 12, 40), box(28, 0, 40, 40)])
    T = unary_union([box(0, 30, 40, 45), box(14, 0, 26, 45)])
    O = box(0, 0, 50, 50).difference(box(15, 15, 35, 35))
    generated = [
        ("Compact bar", box(0, 0, 46.33, 16.92)),
        ("L-shape", L),
        ("U-shape", U),
        ("T-shape", T),
        ("Courtyard (O)", O),
        ("L-shape rotated 30°", affinity.rotate(L, 30, origin=(3, 7))),
        ("Wide bar", box(0, 0, 60, 20)),
        ("Cross", unary_union([box(15, 0, 27, 45), box(0, 16, 42, 29)])),
    ]

    panels = [("DOE MidriseApartment\n(reference)", _doe_reference_zones())]
    for name, poly in generated:
        zones = _generated_zones(poly)
        panels.append((f"{name}\n({len(zones)} zones)", zones))

    n = len(panels)
    ncols = math.ceil(math.sqrt(n))
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 3.2 * nrows))
    axes = axes.ravel()
    for ax, (title, zones) in zip(axes, panels):
        _draw(ax, zones, title)
    for ax in axes[n:]:
        ax.axis("off")

    fig.suptitle("layoutGenerator: DOE reference vs generated MidriseApartment layouts\n"
                 "corridor (grey) + apartment zones (blue)", fontsize=13, y=0.99)
    fig.legend(handles=[Patch(facecolor=_COLOR["Corridor"], edgecolor=_EDGE, label="Corridor"),
                        Patch(facecolor=_COLOR["Apartment"], edgecolor=_EDGE, label="Apartment")],
               loc="lower center", ncol=2, frameon=False)
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
