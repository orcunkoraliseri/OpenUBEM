"""S7 -- real-footprint layout validation (docs_ACTIVE/.../debugs/PLAN_design_buildout_by_
archetype.md S7 / T-S7.1). Runs the SAME auto-assigning layoutGenerator engine on REAL
footprints from the committed 12-cell phaseE validation set, one figure per archetype, so
each building type's engine-assigned form can be checked against real building shapes.
Design/viz only: reads committed phaseE results read-only, calls generate_layout directly
(same viz path as scripts/plot_layout_grid.py), NO EnergyPlus, NO production leakage.
Output: docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/Reference_plans_real/
        (mirrored to) openubem/outputs/LayoutGenerator/Reference_plans_real/
"""
import argparse
import math
import shutil
import sys
import textwrap
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from shapely import affinity
from shapely.ops import unary_union

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from openubem.geometry.layoutGenerator import generate_layout, MODULE_SPECS
from scripts.plot_layout_grid import (
    _draw, _EDGE, _DEGRADE_COLOR, _DEGRADE_KEY, _DEGRADE_LABEL,
    _SPACE_TYPE_COLORS, _OFFICE_SPACE_COLORS, _FUNCTIONAL_SPLIT_COLORS,
    _LEFTOVERS_COLORS, _SCHOOL_COLORS,
)

PHASEE_DIR = REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
DOCS_OUT_DIR = (REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutgenerator"
                / "Reference_plans_real")
OUT_DIR = REPO / "openubem" / "outputs" / "LayoutGenerator" / "Reference_plans_real"

_CELLS = [f"{city}_{zone}" for city in ("nyc", "la", "austin")
          for zone in ("centre", "urban", "suburban", "rural")]

# SuperMarket (classifier label) -> Supermarket (MODULE_SPECS key); all other covered
# labels already match MODULE_SPECS keys exactly.
_ENGINE_KEY_MAP = {"SuperMarket": "Supermarket"}

_COVERAGE_10 = [
    "SmallOffice", "MidriseApartment", "MediumOffice", "LargeOffice", "RetailStandalone",
    "TallBuilding", "QuickServiceRestaurant", "FullServiceRestaurant", "HighriseApartment",
    "SuperTallBuilding", "SecondarySchool",
]
_COVERAGE_ALL = ["Outpatient", "SuperMarket", "PrimarySchool"]
_COVERAGE = _COVERAGE_10 + _COVERAGE_ALL

# Master color map = merge of every per-family dict plot_layout_grid.py already defines.
_MASTER_COLORS = {}
for _d in _SPACE_TYPE_COLORS.values():
    _MASTER_COLORS.update(_d)
_MASTER_COLORS.update(_OFFICE_SPACE_COLORS)
_MASTER_COLORS.update(_FUNCTIONAL_SPLIT_COLORS)
_MASTER_COLORS.update(_LEFTOVERS_COLORS)
_MASTER_COLORS.update(_SCHOOL_COLORS)
_MASTER_COLORS[_DEGRADE_KEY] = _DEGRADE_COLOR

_DEGRADED_FORM = "one_zone_per_floor (degraded)"
_ENGINE_ERROR_FORM = "one_zone_per_floor (engine error)"
_ENGINE_ERROR_LABEL = "per-floor (engine error)"
_RESULTS_COLS = ["osm_id", "archetype_id", "levels", "footprint_area_m2", "total_eui_kwh_m2"]


def load_cell(cell: str) -> pd.DataFrame:
    cell_dir = PHASEE_DIR / cell
    gdf = gpd.read_file(cell_dir / "01_buildings.gpkg")[["osm_id", "geometry"]]
    res = pd.read_csv(cell_dir / "05_results.csv")[_RESULTS_COLS]
    merged = gdf.merge(res, on="osm_id", how="inner")
    merged["cell"] = cell
    # Each cell has its own local UTM zone (per-cell meters, engine-ready) -- drop the
    # GeometryArray/CRS wrapper (plain object dtype instead) so pd.concat across cells
    # doesn't reject mixed CRSes; we never reproject, only translate footprints within
    # their own local frame.
    merged = pd.DataFrame(merged)
    merged["geometry"] = pd.array(merged["geometry"].tolist(), dtype=object)
    return merged


def load_all_cells() -> pd.DataFrame:
    return pd.concat([load_cell(c) for c in _CELLS], ignore_index=True)


def pool(all_df: pd.DataFrame, label: str) -> pd.DataFrame:
    return all_df[all_df["archetype_id"] == label].copy()


def num_floors_for(levels) -> int:
    if pd.isna(levels):
        return 1
    n = int(levels)
    return n if n > 0 else 1


def engine_key_for(label: str) -> str:
    return _ENGINE_KEY_MAP.get(label, label)


def build_records(pooled_df: pd.DataFrame, engine_key: str) -> list[dict]:
    records = []
    for _, row in pooled_df.iterrows():
        num_floors = num_floors_for(row["levels"])
        try:
            zones_raw = generate_layout(row["osm_id"], row.geometry, engine_key, num_floors)
        except Exception as exc:
            # Viz-side robustness ONLY (engine untouched): a few real footprints make the
            # engine raise a GEOS TopologyException rather than return []; treat as a degrade
            # but tag distinctly so the manifest stays honest (production zoning.py does not
            # catch this -- surfaced as a finding, not silently absorbed).
            print(f"ENGINE_ERROR osm_id={row['osm_id']} cell={row['cell']} "
                  f"archetype={engine_key}: {type(exc).__name__}: {exc}")
            records.append({
                "cell": row["cell"], "osm_id": row["osm_id"], "form": _ENGINE_ERROR_FORM,
                "zones": [{"polygon": row.geometry, "space_type": _DEGRADE_KEY}],
                "levels": num_floors, "footprint_area_m2": row["footprint_area_m2"],
                "total_eui_kwh_m2": row["total_eui_kwh_m2"],
            })
            continue
        f0 = [z for z in zones_raw if "_F0_" in z["name"]]
        if not f0:
            form = _DEGRADED_FORM
            zones = [{"polygon": row.geometry, "space_type": _DEGRADE_KEY}]
        else:
            form = f0[0]["generation_status_note"]
            zones = [{"polygon": z["floor_polygon"], "space_type": z["space_type"]} for z in f0]
        records.append({
            "cell": row["cell"], "osm_id": row["osm_id"], "form": form, "zones": zones,
            "levels": num_floors, "footprint_area_m2": row["footprint_area_m2"],
            "total_eui_kwh_m2": row["total_eui_kwh_m2"],
        })
    return records


def select_ten(records: list[dict], limit: int = 10) -> list[dict]:
    """Bucket by assigned form, round-robin across buckets (sorted by osm_id), deterministic."""
    buckets: dict[str, list[dict]] = {}
    for r in records:
        buckets.setdefault(r["form"], []).append(r)
    for form in buckets:
        buckets[form].sort(key=lambda r: r["osm_id"])
    forms = sorted(buckets)
    chosen = []
    i = 0
    while len(chosen) < limit and any(buckets[f] for f in forms):
        form = forms[i % len(forms)]
        if buckets[form]:
            chosen.append(buckets[form].pop(0))
        i += 1
    return chosen


def _recentered_zones(zones: list[dict]) -> list[dict]:
    cx, cy = unary_union([z["polygon"] for z in zones]).centroid.coords[0]
    return [{"polygon": affinity.translate(z["polygon"], -cx, -cy), "space_type": z["space_type"]}
            for z in zones]


def render_archetype(name: str, chosen: list[dict]) -> Path:
    n = len(chosen)
    ncols = 5
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.4 * ncols, 3.8 * nrows), squeeze=False)
    axes = axes.ravel()
    used_types = set()
    for ax, rec in zip(axes, chosen):
        zones = _recentered_zones(rec["zones"])
        used_types.update(z["space_type"] for z in zones)
        title = f"{rec['cell']} · {rec['osm_id']}"
        # Caption uses the SHORT degrade label (matches the legend); manifest keeps the
        # full form string. Wrap + smaller font so no long form label bleeds into an
        # adjacent panel's title.
        form_label = {_DEGRADED_FORM: _DEGRADE_LABEL,
                      _ENGINE_ERROR_FORM: _ENGINE_ERROR_LABEL}.get(rec["form"], rec["form"])
        sub = textwrap.fill(
            f"{form_label} · {rec['levels']}fl · "
            f"{rec['footprint_area_m2']:.0f} m² · EUI {rec['total_eui_kwh_m2']:.0f}",
            width=30,
        )
        _draw(ax, zones, f"{title}\n{sub}", _MASTER_COLORS)
        ax.set_title(f"{title}\n{sub}", fontsize=8)
    for ax in axes[n:]:
        ax.axis("off")

    legend_handles = [Patch(facecolor=_MASTER_COLORS[st], edgecolor=_EDGE, label=st)
                      for st in _MASTER_COLORS if st in used_types and st != _DEGRADE_KEY]
    if _DEGRADE_KEY in used_types:
        legend_handles.append(Patch(facecolor=_DEGRADE_COLOR, edgecolor=_EDGE, label=_DEGRADE_LABEL))
    fig.legend(handles=legend_handles, loc="lower center", ncol=max(1, len(legend_handles)),
               frameon=False)
    fig.suptitle(
        f"{name} — {n} real footprints from the 12-cell set (engine auto-assigned form)",
        fontsize=13, y=0.99,
    )
    fig.tight_layout(rect=[0, 0.07, 1, 0.94])

    DOCS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    docs_path = DOCS_OUT_DIR / f"layoutreal_{name}.png"
    out_path = OUT_DIR / f"layoutreal_{name}.png"
    fig.savefig(docs_path, dpi=130)
    plt.close(fig)
    shutil.copyfile(docs_path, out_path)
    print(f"wrote {docs_path}")
    print(f"wrote {out_path}")
    return docs_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None, help="restrict to one archetype (checkpoint use)")
    args = parser.parse_args()

    coverage = [args.only] if args.only else _COVERAGE
    all_df = load_all_cells()

    manifest_rows = []
    for name in coverage:
        engine_key = engine_key_for(name)
        assert engine_key in MODULE_SPECS, (
            f"FATAL: engine_key {engine_key!r} (from archetype {name!r}) not in MODULE_SPECS"
        )
        pooled = pool(all_df, name)
        records = build_records(pooled, engine_key)
        chosen = select_ten(records, limit=10)
        render_archetype(name, chosen)
        for r in chosen:
            manifest_rows.append({
                "archetype": name, "cell": r["cell"], "osm_id": r["osm_id"],
                "assigned_form": r["form"], "levels": r["levels"],
                "footprint_area_m2": r["footprint_area_m2"],
                "total_eui_kwh_m2": r["total_eui_kwh_m2"],
            })

    manifest_path = DOCS_OUT_DIR / "_manifest.csv"
    pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False)
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
