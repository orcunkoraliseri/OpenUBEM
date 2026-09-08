"""EU-11 T03 (PLAN_eu-recut-95pct-2026-09-08.md): wall-B measurement.

For each of the 184 ``undivided_vertex_bug`` buildings (the near-duplicate-
vertex path that discards an already-cut dwelling layout back to one box per
floor), rebuild the storey layout and the pre-reroute IDF surfaces locally
(no EnergyPlus, no simulation) and record why the at-risk gate in
``scripts/run_eu_s2_campaign.py`` still fires.

This module is a measurement driver, authorised as a new file by the
director note at the end of PLAN_eu-recut-95pct-2026-09-08.md section 8
("T03 runs concurrently with T01-T02"). It imports, but never edits,
``scripts/run_eu_s2_campaign.py``, ``scripts/run_eu_s2_district_campaign.py``
and ``openubem/idf/surfaces.py``.

Method
------
``_geometry`` (imported, unmodified) rebuilds the exact zones the campaign
built. A local wrapper (``_extrude_with_diagnosis``) then replays exactly the
first half of ``build_idf_for_building`` -- IDF header, the real
``_drop_redundant_ring_vertices`` per zone ring, then the real
``extrude_geometry`` (which itself calls ``intersect_match`` once) -- and
stops there, one line before the campaign's at-risk gate
(``run_eu_s2_campaign.py:680-684``). A diagnostic scan
(``_diagnose_surfaces``), reading the same two frozen module constants
(``NEAR_DUPLICATE_VERTEX_TOLERANCE_M``, ``COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG``)
the real ``_has_near_duplicate_vertex_surfaces`` reads, then finds every
flagged interzone-paired surface instead of returning a single bool, which is
the extra information the real function does not expose. ``context`` is
passed empty throughout: ``extrude_geometry`` only consumes it for shading
blocks added after ``intersect_match``, so it cannot affect the interzone
vertex defect being measured (verified by reading
``openubem/idf/surfaces.py:872-984``).

Each flagged vertex is classified ``defect_on`` by matching its (x, y) back
against the zone's own pre-drop ring: not present at all -> the point did not
exist before ``extrude_geometry``'s ``intersect_match``, so the
ring-vertex-removal pass never had a chance at it (``interzone_pair`` /
``not_on_ring``); present and within 0.02 m of the original footprint
boundary -> ``footprint_ring``; present but interior -> ``cut_edge``. For the
two ring-borne cases, ``refused_by`` replays the same three-budget test
``_drop_redundant_ring_vertices`` applies (chord distance, per-removal area,
cumulative area, or the ring-below-3-vertices floor) as a single-shot check
on the vertex's final neighbours -- not a full cumulative replay of the
fixed-point loop, which is a documented approximation, not the real gate.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_eu_s2_campaign as campaign  # noqa: E402
import scripts.run_eu_s2_district_campaign as district_campaign  # noqa: E402
from openubem.config import ENERGYPLUS_IDD_PATH  # noqa: E402
from openubem.idf.surfaces import extrude_geometry, find_mismatched_interzone_pairs  # noqa: E402

DEBUG_CSV = ROOT / "docs/docs_ACTIVE/europeanLocations/debugs/undivided_buildings_all_districts_2026-09-08.csv"
OUT_DIR = ROOT / "openubem/outputs/eu_evidence/EU-11/wallB_second_pass_2026-09-08"

DISTRICT_LABEL_TO_CODE = {
    "Madrid": "ES-MAD-BERRUGUETE",
    "Lyon": "FR-LYO-HAUTCOEURPENTES",
    "London": "GB-LDN-STDUNSTANS",
    "Bologna": "IT-BOL-GALVANI2",
}
FOOTPRINT_SNAP_TOL_M = 0.02
RING_MATCH_TOL_M = 0.02

_IDD_SET = False


def _ensure_idd() -> None:
    global _IDD_SET
    if _IDD_SET:
        return
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    _IDD_SET = True


def _header_kwargs_for(fold: str) -> dict:
    epw_path, _sha = district_campaign._registry_weather(fold, None)
    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        location_fields = stream.readline().strip().split(",")
    city, _state, _country = location_fields[1], location_fields[2], location_fields[3]
    latitude, longitude, time_zone, elevation = (float(v) for v in location_fields[6:10])
    return {
        "city": city, "latitude": latitude, "longitude": longitude,
        "time_zone": time_zone, "elevation": elevation,
        "shadow_method": campaign.SHADOW_CALCULATION_METHOD,
        "shadow_update_method": campaign.SHADOW_CALCULATION_UPDATE_FREQUENCY_METHOD,
        "shadow_update_days": campaign.SHADOW_CALCULATION_UPDATE_FREQUENCY_DAYS,
    }


def _new_scratch_idf(scratch_dir: Path, name: str, header_kwargs: dict):
    from geomeppy import IDF
    _ensure_idd()
    scratch_dir.mkdir(parents=True, exist_ok=True)
    idf_path = scratch_dir / f"{name}.idf"
    idf_path.write_text(campaign.IDF_HEADER_TEMPLATE.format(**header_kwargs), encoding="utf-8")
    return IDF(str(idf_path))


def _extrude_with_diagnosis(zones: list[dict], idf, chord_tol_override: float | None = None):
    original = campaign.RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M
    if chord_tol_override is not None:
        campaign.RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M = chord_tol_override
    try:
        pre_rings: dict[str, list] = {}
        for zone in zones:
            coords = zone.get("coords_m")
            if coords:
                pre_rings[zone["name"]] = list(coords)
                zone["coords_m"] = campaign._drop_redundant_ring_vertices(coords)
        post_rings = {z["name"]: list(z.get("coords_m") or []) for z in zones}
        extrude_geometry(idf, zones, [])
    finally:
        campaign.RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M = original
    return pre_rings, post_rings


def _diagnose_surfaces(idf) -> list[dict]:
    near_dup = campaign.NEAR_DUPLICATE_VERTEX_TOLERANCE_M
    collin = campaign.COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG
    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    surf_by_name = {str(s.Name).upper(): s for s in bsds}
    out: list[dict] = []
    for surf in bsds:
        if str(getattr(surf, "Outside_Boundary_Condition", "")).upper() != "SURFACE":
            continue
        partner = str(getattr(surf, "Outside_Boundary_Condition_Object", "") or "").upper()
        if not partner or partner == str(surf.Name).upper() or partner not in surf_by_name:
            continue
        coords = list(surf.coords)
        n = len(coords)
        if n < 3:
            continue
        for i in range(n):
            p0, p1, p2 = coords[(i - 1) % n], coords[i], coords[(i + 1) % n]
            v1 = tuple(a - b for a, b in zip(p0, p1))
            v2 = tuple(a - b for a, b in zip(p2, p1))
            len1 = math.sqrt(sum(c * c for c in v1))
            len2 = math.sqrt(sum(c * c for c in v2))
            kind = None
            if len1 < near_dup or len2 < near_dup:
                kind = "near_duplicate"
            else:
                cos_a = max(-1.0, min(1.0, sum(a * b for a, b in zip(v1, v2)) / (len1 * len2)))
                angle = math.degrees(math.acos(cos_a))
                if angle > 180.0 - collin:
                    kind = "collinear"
            if kind:
                out.append({
                    "surface": str(surf.Name), "zone": str(surf.Zone_Name),
                    "p1": p1, "defect_kind": kind, "min_edge_len_m": min(len1, len2),
                })
    return out


def _ring_area(points: list) -> float:
    n = len(points)
    if n < 3:
        return 0.0
    nx = ny = nz = 0.0
    for i in range(n):
        x1, y1 = points[i][0], points[i][1]
        z1 = points[i][2] if len(points[i]) > 2 else 0.0
        x2, y2 = points[(i + 1) % n][0], points[(i + 1) % n][1]
        z2 = points[(i + 1) % n][2] if len(points[(i + 1) % n]) > 2 else 0.0
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return math.sqrt(nx * nx + ny * ny + nz * nz) / 2.0


def _is_locally_redundant(p0, p1, p2) -> bool:
    near_dup = campaign.NEAR_DUPLICATE_VERTEX_TOLERANCE_M
    collin = campaign.COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG
    v1 = (p0[0] - p1[0], p0[1] - p1[1])
    v2 = (p2[0] - p1[0], p2[1] - p1[1])
    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if len1 < near_dup or len2 < near_dup:
        return True
    cos_a = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)))
    angle = math.degrees(math.acos(cos_a))
    return angle > 180.0 - collin


def classify_defect(defect: dict, pre_rings: dict, post_rings: dict, footprint_geom) -> tuple[str, str, float | None, float | None]:
    zone_name = defect["zone"]
    x, y = defect["p1"][0], defect["p1"][1]
    post_ring = post_rings.get(zone_name) or []

    def _match(ring, tol=RING_MATCH_TOL_M):
        for idx, c in enumerate(ring):
            if math.hypot(c[0] - x, c[1] - y) <= tol:
                return idx
        return None

    post_idx = _match(post_ring)
    if post_idx is None:
        return "interzone_pair", "not_on_ring", None, None

    on_footprint = footprint_geom.exterior.distance(Point(x, y)) <= FOOTPRINT_SNAP_TOL_M
    defect_on = "footprint_ring" if on_footprint else "cut_edge"

    n = len(post_ring)
    if n <= 3:
        return defect_on, "min_3_vertices", None, None
    p0 = post_ring[(post_idx - 1) % n]
    p2 = post_ring[(post_idx + 1) % n]
    p1 = post_ring[post_idx]
    if not _is_locally_redundant(p0, p1, p2):
        # The point coincides (within RING_MATCH_TOL_M) with a real footprint/
        # cut vertex, but it is not itself near-duplicate or collinear on this
        # zone's own ring -- _drop_redundant_ring_vertices would never have
        # tried to remove it. The defect the surface scan found here comes
        # from cross-surface interzone pairing (FINDING 210: intersect_match
        # clipping this floor's ceiling against a differently-shaped storey
        # above/below), not from a refused local removal.
        return defect_on, "not_on_ring", None, None
    ring_area = _ring_area(post_ring)
    candidate = post_ring[:post_idx] + post_ring[post_idx + 1:]
    cand_area = _ring_area(candidate)
    area_delta = abs(cand_area - ring_area)
    rel_change = (area_delta / ring_area) if ring_area else 0.0
    chord_len = math.hypot(p2[0] - p0[0], p2[1] - p0[1])
    perp = (2.0 * area_delta / chord_len) if chord_len else 0.0
    if perp > campaign.RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M:
        refused = "chord_0.010m"
    elif rel_change > campaign.RING_VERTEX_REMOVAL_PER_REMOVAL_AREA_BUDGET:
        refused = "per_removal_1e-3"
    else:
        refused = "cumulative_2e-3"
    return defect_on, refused, perp, rel_change


def load_debug_rows(district_label: str) -> pd.DataFrame:
    df = pd.read_csv(DEBUG_CSV, dtype=str)
    return df[(df.district == district_label) & (df.defect_class == "undivided_vertex_bug")].copy()


def load_es_fr_gb_rows(district_code: str) -> dict[str, dict]:
    cfg = district_campaign.DISTRICTS[district_code]
    manifest = ROOT / f"openubem/outputs/eu02/{district_code}/02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    records = district_campaign._records(cfg["country"])
    if district_code == "GB-LDN-STDUNSTANS":
        rows, _exclusions = district_campaign._gb_rows(gdf, records)
        # `_final_2026-09-07` was prepared with `--recover-terrace-neighbours`
        # (STATE/BRIEF: 255 London buildings recovered 2026-09-07); the base
        # `_gb_rows` population alone does not cover every vertex-bug id, so
        # the recovery pass (network-free, same as prepare()) is merged in too.
        recovered_rows, _recovery_exclusions = district_campaign._gb_terrace_recovery_rows(gdf, records, rows)
        rows = rows + recovered_rows
    else:
        rows, _exclusions = district_campaign._mapped_rows(district_code, gdf, records)
    return {r["building_id"]: r for r in rows}


def load_it_context():
    gpkg = gpd.read_file(ROOT / "openubem/outputs/eu02/IT-BOL-GALVANI2/02_residential_manifest.gpkg")
    gpkg["osm_id"] = gpkg["osm_id"].astype(str)
    gpkg = gpkg.set_index("osm_id", drop=False)
    fin = pd.read_csv(
        ROOT / "openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_final_2026-09-07/prepared_buildings.csv",
        dtype=str,
    )
    fin = fin.set_index("building_id", drop=False)
    return gpkg, fin


def it_row_for(building_id: str, gpkg: gpd.GeoDataFrame, fin: pd.DataFrame) -> tuple[dict, float]:
    grow = gpkg.loc[building_id]
    frow = fin.loc[building_id]
    footprint_area = float(grow["footprint_area_m2"])
    gross = float(frow["gross_footprint_area_m2"])
    ratio = (gross / footprint_area) if footprint_area else float("nan")
    levels = max(1, round(ratio)) if math.isfinite(ratio) else 1
    deviation = abs(ratio - round(ratio)) if math.isfinite(ratio) else float("inf")
    data = {
        "osm_id": building_id, "building_id": building_id, "geometry": grow.geometry,
        "building_type": frow["building_type"], "archetype_id": frow["archetype_id"],
        "age_band": frow["age_band"], "levels": levels, "observed_dwellings": None,
        "construction_period_provenance": frow.get("construction_period_provenance", ""),
        "storey_provenance": frow.get("storey_provenance", ""),
    }
    return data, deviation


def measure_building(row_data: dict, records: list[dict], scratch_dir: Path, header_kwargs: dict,
                      chord_relaxed: float | None = None) -> dict:
    row = pd.Series(row_data)
    computed_stem = hashlib.sha256(str(row.building_id).encode()).hexdigest()[:16]
    model_row = row.copy()
    model_row["building_id"] = computed_stem
    result = district_campaign._geometry(model_row, records)
    zones, outcome = result[0], result[1]
    idf = _new_scratch_idf(scratch_dir, computed_stem, header_kwargs)
    pre_rings, post_rings = _extrude_with_diagnosis(zones, idf, chord_tol_override=chord_relaxed)
    defects = _diagnose_surfaces(idf)
    mismatched = find_mismatched_interzone_pairs(idf)
    return {
        "stem": computed_stem, "outcome": outcome, "zones": zones,
        "defects": defects, "pre_rings": pre_rings, "post_rings": post_rings,
        "mismatched": mismatched, "footprint": row.geometry,
    }


def run_district(district_label: str, out_dir: Path) -> pd.DataFrame:
    district_code = DISTRICT_LABEL_TO_CODE[district_label]
    cfg = district_campaign.DISTRICTS[district_code]
    debug_rows = load_debug_rows(district_label)
    records = district_campaign._records(cfg["country"])
    header_kwargs = _header_kwargs_for(cfg["fold"])
    scratch_base = out_dir / "scratch" / district_code
    scratch_baseline = scratch_base / "baseline"
    scratch_relaxed = scratch_base / "relaxed"

    if district_code == "IT-BOL-GALVANI2":
        gpkg, fin = load_it_context()
        deviations = []
    else:
        rows_by_id = load_es_fr_gb_rows(district_code)

    out_rows = []
    for _, dbg in debug_rows.iterrows():
        bid = dbg["building_id"]
        stem_expected = dbg["stem"]
        if district_code == "IT-BOL-GALVANI2":
            row_data, deviation = it_row_for(bid, gpkg, fin)
            deviations.append(deviation)
        else:
            row_data = dict(rows_by_id[bid])

        baseline = measure_building(row_data, records, scratch_baseline, header_kwargs, chord_relaxed=None)
        stem = baseline["stem"]
        if stem != stem_expected:
            raise ValueError(f"stem mismatch for {bid}: computed={stem} expected={stem_expected}")

        defects = baseline["defects"]
        n_flagged = len({d["surface"] for d in defects})
        if defects:
            rep = defects[0]
            defect_on, refused_by, perp, rel = classify_defect(
                rep, baseline["pre_rings"], baseline["post_rings"], baseline["footprint"]
            )
            defect_kind = rep["defect_kind"]
            min_edge = rep["min_edge_len_m"]
        else:
            defect_kind = "collinear" if baseline["mismatched"] else "near_duplicate"
            defect_on = "interzone_pair"
            refused_by = "not_on_ring"
            perp = None
            rel = None
            min_edge = None

        relaxed = measure_building(row_data, records, scratch_relaxed, header_kwargs, chord_relaxed=0.020)
        would_clear_at_020 = len(relaxed["defects"]) == 0

        out_rows.append({
            "district": district_label, "building_id": bid, "stem": stem,
            "n_flagged_surfaces": n_flagged, "defect_kind": defect_kind,
            "defect_on": defect_on, "refused_by": refused_by,
            "min_edge_len_m": min_edge, "perp_dist_m": perp, "rel_area_change": rel,
            "would_clear_chord_0.020m": would_clear_at_020,
        })

    df = pd.DataFrame(out_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    district_csv = out_dir / f"wallB_defects_{district_code}.csv"
    df.to_csv(district_csv, index=False)
    print(f"[{district_label}] wrote {len(df)} rows -> {district_csv}", flush=True)
    if district_code == "IT-BOL-GALVANI2" and deviations:
        bad = sum(1 for d in deviations if d > 0.1)
        print(f"[{district_label}] levels-derivation deviation > 0.1 for {bad}/{len(deviations)} buildings", flush=True)
    return df


def merge(out_dir: Path) -> None:
    parts = sorted(out_dir.glob("wallB_defects_*.csv"))
    frames = [pd.read_csv(p) for p in parts]
    merged = pd.concat(frames, ignore_index=True)
    merged.to_csv(out_dir / "wallB_defects.csv", index=False)
    print(f"merged {len(merged)} rows from {len(parts)} district files -> {out_dir / 'wallB_defects.csv'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", choices=sorted(DISTRICT_LABEL_TO_CODE), default=None)
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    if args.merge:
        merge(args.out)
        return
    if args.district is None:
        parser.error("--district is required unless --merge is given")

    t0 = time.time()
    run_district(args.district, args.out)
    print(f"[{args.district}] done in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
