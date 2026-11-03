"""EU-20 M01-M04: the morphology atlas measurement.

Reads the same residential-manifest footprints the EU-11/EU-17 campaign
prepares from, joins them against the building set the campaign actually
simulated (``EU-17/<district>/prepared_buildings.csv``), measures every
footprint, groups them by a fixed, order-applied taxonomy, picks one named
representative per group and draws its bare footprint.

Never runs EnergyPlus. Never edits ``openubem/geometry/european_residential.py``
or anything under ``rules/``/``plans3D/``/``outputs_3D/`` -- the denoise/reflex
helpers are imported from that module, never copied
(PLAN_eu20-morphology-atlas-2026-09-01.md dependency decision 4.3).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openubem.geometry.european_residential import _reflex_vertex_count  # noqa: E402  (dep 4.3: import, never copy)
from scripts.eu_idf_plan_reader import parse_idf_floor_zones, round_ring_1cm  # noqa: E402  (dep: no second parser)

EU02 = ROOT / "openubem" / "outputs" / "eu02"
EU17 = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-17"
EU20 = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-20"
SVG_DIR = EU20 / "svg"

# PLAN §4.2 -- pinned expected residential counts.
EXPECTED_COUNTS = {
    "ES-MAD-BERRUGUETE": 961,
    "FR-LYO-HAUTCOEURPENTES": 297,
    "GB-LDN-STDUNSTANS": 82,
    "IT-BOL-GALVANI2": 1204,
}
DISTRICTS = list(EXPECTED_COUNTS)

CENSUS_COLUMNS = [
    "district", "building_id", "area_m2", "perimeter_m", "n_vertices_raw", "n_vertices_denoised",
    "n_interior_rings", "interior_ring_area_m2", "hull_deficit_fraction", "rectangularity",
    "min_rot_rect_w_m", "min_rot_rect_l_m", "aspect_ratio", "reflex_count", "longest_edge_m",
    "n_edges_ge_15pct_perimeter", "circularity", "storeys", "dwellings_total", "idf_state",
]
NUMERIC_METRICS = [
    c for c in CENSUS_COLUMNS if c not in ("district", "building_id", "idf_state")
]

GROUP_ORDER = [
    "COURTYARD", "SLIVER", "SQUARE", "RECTANGLE", "CORRIDOR_RECTANGLE", "SLAB", "TRIANGLE",
    "TRAPEZOID", "L_SHAPE", "U_OR_T_SHAPE", "COMPLEX_MULTI_WING",
]

EXPECTED_IDF_STATE_TALLY = {"RULED": 541, "MASSING_BOX": 2003, "NO_IDF": 0}


# ---------------------------------------------------------------- M01 -----

def _denoise(footprint):
    """Same denoise the classifier applies -- european_residential.py:447-449."""
    denoised = footprint.simplify(0.5, preserve_topology=True)
    if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
        denoised = footprint
    return denoised


def _edge_lengths(ring_coords_closed):
    return [math.dist(ring_coords_closed[i], ring_coords_closed[i + 1]) for i in range(len(ring_coords_closed) - 1)]


def _measure_footprint(footprint) -> dict:
    ext_raw = list(footprint.exterior.coords)[:-1]
    area_m2 = footprint.area
    perimeter_m = footprint.exterior.length
    n_interior_rings = len(footprint.interiors)
    exterior_only_area = Polygon(footprint.exterior.coords).area
    interior_ring_area_m2 = max(0.0, exterior_only_area - area_m2)

    # dep 4.3: mirror classify_building_morphology's own has_courtyard (raw
    # footprint interiors) / hull_deficit_fraction / reflex_count exactly.
    denoised = _denoise(footprint)
    hull_deficit_fraction = (
        (denoised.convex_hull.area - denoised.area) / denoised.area if denoised.area > 0 else 0.0
    )
    has_courtyard = n_interior_rings >= 1
    reflex_count = 0
    if not has_courtyard and hull_deficit_fraction > 0.03:
        reflex_count = _reflex_vertex_count(denoised)

    denoised_coords = list(denoised.exterior.coords)[:-1]
    n_vertices_denoised = len(denoised_coords)
    denoised_edges = _edge_lengths(denoised_coords + denoised_coords[:1])
    denoised_perimeter = sum(denoised_edges)
    edge_threshold = 0.15 * denoised_perimeter if denoised_perimeter > 0 else 0.0
    n_edges_ge_15pct_perimeter = sum(1 for e in denoised_edges if e >= edge_threshold)

    # M01 "How": rectangularity / aspect_ratio / min-rot-rect on the raw
    # footprint -- matches classify_building_morphology's own lw_ratio,
    # computed on `footprint` before the denoised variable even exists
    # (european_residential.py:433-441).
    rect = footprint.minimum_rotated_rectangle
    rect_coords = list(rect.exterior.coords)
    rect_edges = sorted(math.dist(rect_coords[i], rect_coords[i + 1]) for i in range(len(rect_coords) - 1))
    width, length = rect_edges[0], rect_edges[-1]
    aspect_ratio = length / width if width > 0 else float("inf")
    rectangularity = area_m2 / rect.area if rect.area > 0 else 0.0

    raw_edges = _edge_lengths(ext_raw + ext_raw[:1])
    longest_edge_m = max(raw_edges) if raw_edges else 0.0
    circularity = 4 * math.pi * area_m2 / (perimeter_m ** 2) if perimeter_m > 0 else 0.0

    return {
        "area_m2": area_m2,
        "perimeter_m": perimeter_m,
        "n_vertices_raw": len(ext_raw),
        "n_vertices_denoised": n_vertices_denoised,
        "n_interior_rings": n_interior_rings,
        "interior_ring_area_m2": interior_ring_area_m2,
        "hull_deficit_fraction": hull_deficit_fraction,
        "rectangularity": rectangularity,
        "min_rot_rect_w_m": width,
        "min_rot_rect_l_m": length,
        "aspect_ratio": aspect_ratio,
        "reflex_count": reflex_count,
        "longest_edge_m": longest_edge_m,
        "n_edges_ge_15pct_perimeter": n_edges_ge_15pct_perimeter,
        "circularity": circularity,
    }


def _idf_state(idf_dir: Path, stem: str) -> str:
    idf_path = idf_dir / f"{stem}.idf"
    if not idf_path.exists():
        return "NO_IDF"
    zone_names, _, _ = parse_idf_floor_zones(idf_path)
    if any("_dwelling_" in z for z in zone_names):
        return "RULED"
    return "MASSING_BOX"


def _sidecar_storeys_dwellings(layouts_dir: Path, building_id: str):
    path = layouts_dir / f"{building_id}.json"
    if not path.exists():
        return None, None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("storeys"), data.get("dwellings_total")


def load_census():
    rows = []
    geometries = {}
    mismatches = []
    for district in DISTRICTS:
        prepared = pd.read_csv(EU17 / district / "prepared_buildings.csv", dtype=str)
        stem_by_id = dict(zip(prepared["building_id"], prepared["stem"]))

        gdf = gpd.read_file(EU02 / district / "02_residential_manifest.gpkg")
        gdf = gdf.assign(building_id=gdf["osm_id"].astype(str))
        gdf = gdf[gdf["building_id"].isin(stem_by_id)].copy()

        if len(gdf) != EXPECTED_COUNTS[district]:
            mismatches.append((district, len(gdf), EXPECTED_COUNTS[district]))
            continue

        idf_dir = EU17 / district / "idfs"
        layouts_dir = EU17 / district / "layouts"
        for _, row in gdf.iterrows():
            bid = row["building_id"]
            # FR-LYO-HAUTCOEURPENTES carries Z on its footprint vertices
            # (shapely check: .has_z True there, False elsewhere) -- drop it,
            # every downstream metric here is planar (dep 4.5: metres, no reproject).
            footprint = shapely.force_2d(row.geometry)
            if footprint.geom_type != "Polygon":
                raise ValueError(f"{district}/{bid}: unexpected geometry type {footprint.geom_type!r}")
            metrics = _measure_footprint(footprint)
            storeys, dwellings_total = _sidecar_storeys_dwellings(layouts_dir, bid)
            stem = stem_by_id[bid]
            state = _idf_state(idf_dir, stem)
            record = {
                "district": district, "building_id": bid, **metrics,
                "storeys": storeys, "dwellings_total": dwellings_total, "idf_state": state,
            }
            rows.append(record)
            geometries[(district, bid)] = footprint

    if mismatches:
        for d, got, exp in mismatches:
            print(f"M01 MISMATCH {d}: joined residential count {got} != expected {exp}")
        raise SystemExit("M01 STOP: residential count mismatch against dependency decision 4.2 -- see above")

    return rows, geometries


# ---------------------------------------------------------------- M02 -----

def classify_group(r) -> str:
    if r["n_interior_rings"] >= 1:
        return "COURTYARD"
    if r["min_rot_rect_w_m"] < 8.0:
        return "SLIVER"
    if r["rectangularity"] >= 0.90 and r["aspect_ratio"] < 1.5:
        return "SQUARE"
    if r["rectangularity"] >= 0.90 and 1.5 <= r["aspect_ratio"] < 2.0:
        return "RECTANGLE"
    # 2.0 is not a new invented cut -- it is LINEAR_GALLERY_ASPECT_THRESHOLD,
    # the length/width ratio european_residential.py already uses at generation
    # time to route a plate to the corridor scheme instead of a central core.
    if r["rectangularity"] >= 0.90 and 2.0 <= r["aspect_ratio"] < 3.0:
        return "CORRIDOR_RECTANGLE"
    if r["rectangularity"] >= 0.90 and r["aspect_ratio"] >= 3.0:
        return "SLAB"
    if r["n_edges_ge_15pct_perimeter"] <= 3 and r["reflex_count"] == 0:
        return "TRIANGLE"
    if r["reflex_count"] == 0 and r["rectangularity"] < 0.90:
        return "TRAPEZOID"
    if r["reflex_count"] == 1:
        return "L_SHAPE"
    if r["reflex_count"] == 2:
        return "U_OR_T_SHAPE"
    if r["reflex_count"] >= 3:
        return "COMPLEX_MULTI_WING"
    raise ValueError(f"M02: building matched no group in the taxonomy: {dict(r)}")


def build_groups(rows: list[dict]):
    df = pd.DataFrame(rows)
    df["group"] = df.apply(classify_group, axis=1)

    out_rows = []
    for (district, group), sub in df.groupby(["district", "group"]):
        district_total = int((df["district"] == district).sum())
        out_rows.append(_group_stats_row(district, group, sub, district_total))
    for group, sub in df.groupby("group"):
        out_rows.append(_group_stats_row("FLEET", group, sub, len(df)))

    groups_df = pd.DataFrame(out_rows)
    groups_df["_order"] = groups_df["group"].apply(GROUP_ORDER.index)
    groups_df = groups_df.sort_values(["_order", "district"]).drop(columns="_order").reset_index(drop=True)
    return df, groups_df


def _group_stats_row(district: str, group: str, sub: pd.DataFrame, denom: int) -> dict:
    row = {"district": district, "group": group, "count": len(sub), "share": len(sub) / denom if denom else 0.0}
    for m in NUMERIC_METRICS:
        col = sub[m].dropna()
        row[f"median_{m}"] = float(col.median()) if len(col) else None
    return row


def near_boundary_report(df: pd.DataFrame):
    thresholds = [
        ("min_rot_rect_w_m", 8.0), ("rectangularity", 0.90),
        ("aspect_ratio", 1.5), ("aspect_ratio", 3.0),
    ]
    near_any = set()
    per_threshold = {}
    for col, t in thresholds:
        mask = (df[col] >= 0.9 * t) & (df[col] <= 1.1 * t)
        per_threshold[f"{col}~{t}"] = int(mask.sum())
        near_any.update(df.index[mask].tolist())
    print("M02 near-boundary (within 10%) by threshold:", per_threshold)
    print("M02 near-boundary (within 10%) unique buildings:", len(near_any))


# ---------------------------------------------------------------- M03 -----

def _shoelace(coords_xy) -> float:
    n = len(coords_xy)
    total = 0.0
    for i in range(n):
        x1, y1 = coords_xy[i]
        x2, y2 = coords_xy[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def _rel_dist(value: float, median: float) -> float:
    if median == 0:
        return abs(value - median)
    return abs(value - median) / abs(median)


def choose_representatives(df: pd.DataFrame, geometries: dict):
    fleet_medians = {
        group: {m: float(sub[m].median()) for m in ("area_m2", "aspect_ratio", "rectangularity")}
        for group, sub in df.groupby("group")
    }

    used_districts = set()
    reps = []
    no_unused_district = []

    for group in GROUP_ORDER:
        sub = df[df["group"] == group]
        if sub.empty:
            continue
        med = fleet_medians[group]
        sub = sub.copy()
        sub["_dist"] = sub.apply(
            lambda r: _rel_dist(r["area_m2"], med["area_m2"])
            + _rel_dist(r["aspect_ratio"], med["aspect_ratio"])
            + _rel_dist(r["rectangularity"], med["rectangularity"]),
            axis=1,
        )

        pool = sub
        f1 = pool[pool["storeys"].notna() & (pool["storeys"] >= 3)]
        if not f1.empty:
            pool = f1
        f2 = pool[pool["dwellings_total"].notna()]
        if not f2.empty:
            pool = f2
        f3 = pool[~pool["district"].isin(used_districts)]
        if not f3.empty:
            pool = f3
        else:
            no_unused_district.append(group)

        chosen = pool.loc[pool["_dist"].idxmin()]
        used_districts.add(chosen["district"])

        footprint = geometries[(chosen["district"], chosen["building_id"])]
        ext_coords = list(footprint.exterior.coords)[:-1]
        cx = sum(x for x, _ in ext_coords) / len(ext_coords)
        cy = sum(y for _, y in ext_coords) / len(ext_coords)
        ext_local = tuple((x - cx, y - cy) for x, y in ext_coords)
        ext_ring = round_ring_1cm(ext_local)
        interior_rings = []
        for interior in footprint.interiors:
            icoords = list(interior.coords)[:-1]
            ilocal = tuple((x - cx, y - cy) for x, y in icoords)
            interior_rings.append(round_ring_1cm(ilocal))

        area_from_ring = _shoelace(ext_ring) - sum(_shoelace(r) for r in interior_rings)

        reps.append({
            "group": group,
            "district": chosen["district"],
            "building_id": chosen["building_id"],
            "storeys": int(chosen["storeys"]) if pd.notna(chosen["storeys"]) else None,
            "dwellings_total": int(chosen["dwellings_total"]) if pd.notna(chosen["dwellings_total"]) else None,
            "area_m2": area_from_ring,
            "aspect_ratio": float(chosen["aspect_ratio"]),
            "rectangularity": float(chosen["rectangularity"]),
            "reflex_count": int(chosen["reflex_count"]),
            "n_interior_rings": int(chosen["n_interior_rings"]),
            "idf_state": chosen["idf_state"],
            "exterior_ring": ext_ring,
            "interior_rings": interior_rings,
        })

    return reps, no_unused_district


# ---------------------------------------------------------------- M04 -----

def make_svg(rep: dict) -> str:
    W = H = 900.0
    margin = 0.10

    ext = rep["exterior_ring"]
    ints = rep["interior_rings"]
    xs = [p[0] for p in ext]
    ys = [p[1] for p in ext]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    bbox_w = maxx - minx
    bbox_h = maxy - miny
    draw_w = W * (1 - 2 * margin)
    draw_h = H * (1 - 2 * margin)
    scale = min(draw_w / bbox_w, draw_h / bbox_h) if bbox_w > 0 and bbox_h > 0 else 1.0
    cx_m = (minx + maxx) / 2.0
    cy_m = (miny + maxy) / 2.0

    def to_px(x, y):
        return (W / 2.0 + (x - cx_m) * scale, H / 2.0 - (y - cy_m) * scale)

    def ring_path(ring):
        pts = [to_px(x, y) for x, y in ring]
        body = " ".join(f"L {px:.2f} {py:.2f}" for px, py in pts[1:])
        return f"M {pts[0][0]:.2f} {pts[0][1]:.2f} {body} Z"

    path_d = ring_path(ext) + " " + " ".join(ring_path(r) for r in ints)

    bar_px = 10.0 * scale
    bar_x0 = W * margin * 0.6
    bar_y = H - H * margin * 0.5
    arrow_x = W - W * margin * 0.6
    arrow_y = H - H * margin * 0.5

    caption1 = rep["group"].replace("_", " ").title()
    caption2 = f"{rep['district']} · {rep['building_id']}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-labelledby="title desc">
  <title id="title">{caption1}</title>
  <desc id="desc">{caption2}</desc>
  <style>.t{{font:700 21px Arial;fill:#172033}}.u{{font:18px Arial;fill:#334155}}.out{{fill:none;stroke:#172033;stroke-width:5;fill-rule:evenodd}}.sc{{stroke:#172033;stroke-width:2;fill:none}}.na{{fill:#172033;stroke:none}}</style>
  <rect x="0" y="0" width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>
  <path class="out" d="{path_d}"/>
  <text class="t" x="{W * margin * 0.6:.1f}" y="40">{caption1}</text>
  <text class="u" x="{W * margin * 0.6:.1f}" y="64">{caption2}</text>
  <g>
    <line class="sc" x1="{bar_x0:.1f}" y1="{bar_y:.1f}" x2="{bar_x0 + bar_px:.1f}" y2="{bar_y:.1f}"/>
    <line class="sc" x1="{bar_x0:.1f}" y1="{bar_y - 6:.1f}" x2="{bar_x0:.1f}" y2="{bar_y + 6:.1f}"/>
    <line class="sc" x1="{bar_x0 + bar_px:.1f}" y1="{bar_y - 6:.1f}" x2="{bar_x0 + bar_px:.1f}" y2="{bar_y + 6:.1f}"/>
    <text class="u" x="{bar_x0:.1f}" y="{bar_y + 22:.1f}">10 m</text>
  </g>
  <g>
    <line class="sc" x1="{arrow_x:.1f}" y1="{arrow_y + 14:.1f}" x2="{arrow_x:.1f}" y2="{arrow_y - 14:.1f}"/>
    <path class="na" d="M {arrow_x - 7:.1f} {arrow_y - 6:.1f} L {arrow_x:.1f} {arrow_y - 14:.1f} L {arrow_x + 7:.1f} {arrow_y - 6:.1f} Z"/>
    <text class="u" x="{arrow_x - 5:.1f}" y="{arrow_y + 30:.1f}">N</text>
  </g>
</svg>
'''


# ---------------------------------------------------------------- main ----

def main():
    EU20.mkdir(parents=True, exist_ok=True)
    SVG_DIR.mkdir(parents=True, exist_ok=True)

    rows, geometries = load_census()
    df_census = pd.DataFrame(rows)
    total_expected = sum(EXPECTED_COUNTS.values())
    if len(df_census) != total_expected:
        raise SystemExit(f"M01 STOP: total row count {len(df_census)} != expected {total_expected}")

    census_path = EU20 / "morphology_census.csv"
    df_census.to_csv(census_path, index=False, columns=CENSUS_COLUMNS)

    print("=== M01 ===")
    for d in DISTRICTS:
        print(f"  {d}: {int((df_census['district'] == d).sum())}")
    print(f"  TOTAL: {len(df_census)}")
    tally = df_census["idf_state"].value_counts().to_dict()
    tally_full = {k: int(tally.get(k, 0)) for k in EXPECTED_IDF_STATE_TALLY}
    print("  idf_state tally:", tally_full)
    if tally_full != EXPECTED_IDF_STATE_TALLY:
        print("  MISMATCH: expected", EXPECTED_IDF_STATE_TALLY)
        raise SystemExit("M01 STOP: idf_state tally mismatch -- see above")

    df_grouped, groups_df = build_groups(rows)
    groups_path = EU20 / "morphology_groups.csv"
    groups_df.to_csv(groups_path, index=False)

    print("\n=== M02 ===")
    fleet = groups_df[groups_df["district"] == "FLEET"]
    for _, r in fleet.iterrows():
        print(f"  {r['group']}: {int(r['count'])} ({100 * r['share']:.2f}%)")
    small = fleet[fleet["count"] < 0.01 * len(df_grouped)]
    big = fleet[fleet["count"] > 0.35 * len(df_grouped)]
    if not small.empty:
        print("  groups <1% of fleet:", small["group"].tolist())
    if not big.empty:
        print("  groups >35% of fleet:", big["group"].tolist())
    near_boundary_report(df_grouped)

    reps, no_unused_district = choose_representatives(df_grouped, geometries)
    reps_path = EU20 / "representatives.json"
    reps_path.write_text(json.dumps(reps, indent=2), encoding="utf-8")

    print("\n=== M03 ===")
    for r in reps:
        print(f"  {r['group']}: {r['district']} / {r['building_id']}")
    if no_unused_district:
        print("  groups with no unused-district candidate available:", no_unused_district)

    print("\n=== M04 ===")
    for r in reps:
        svg_text = make_svg(r)
        out_path = SVG_DIR / f"{r['group']}.svg"
        out_path.write_text(svg_text, encoding="utf-8")
        print(f"  {out_path.name}: {out_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
