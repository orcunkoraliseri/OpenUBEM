"""EU-17a T14: diagnose the T10 STOP (`FINDING 220`) without editing the campaign path.

Side-effect-free instrumentation, per `D-EU-57` / T14's own "How"
(`docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md`
§6 T14): this script monkeypatches the already-imported function *references* in
`openubem.idf.surfaces` and `scripts.run_eu_s2_campaign` from the outside, calls
the exact same functions `prepare()` (`scripts/run_eu_s2_district_campaign.py`)
already calls per building, and records what fired at each of T14's four stages.
Nothing in `openubem/idf/surfaces.py` or `scripts/run_eu_s2_campaign.py` is
edited. IDFs are written to a system tempdir, never into `EU-11/` or `EU-17/`
(rule 3 / §3 forbids writing into `EU-11/**`; `EU-17/<district>/` is T10's own
rebuilt tree and is not touched here either). Nothing is simulated (`D-EU-55`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

import openubem.idf.surfaces as surfmod
import scripts.run_eu_s2_campaign as camp
import scripts.run_eu_s2_district_campaign as dcamp
from openubem.idf.surfaces import _get_floor_idx
from openubem.semantic.european_archetype_mapping import (
    compute_footprint_adjacency,
    map_observed_building_to_tabula,
)
from scripts.eu_idf_plan_reader import read_building_plan

ROOT = Path(__file__).resolve().parents[1]
EU11_ROOT = ROOT / "openubem/outputs/eu_evidence/EU-11"
OUT_ROOT = ROOT / "openubem/outputs/eu_evidence/EU-17"

NAMED_BUILDINGS: dict[str, list[str]] = {
    "GB-LDN-STDUNSTANS": ["way/51781396"],
    "ES-MAD-BERRUGUETE": [
        "relation/12704090", "way/388485191", "way/420409335",
        "relation/3730743", "way/391279229",
    ],
    "FR-LYO-HAUTCOEURPENTES": [
        "BATIMENT0000000240879941_part0", "BATIMENT0000000240880045_part0",
    ],
    "IT-BOL-GALVANI2": [],
}

LOSS_SAMPLE_TARGET_PER_DISTRICT = 10
SCAN_CAP_PER_DISTRICT = 1500  # safety bound; smaller districts exhaust before this


# ---------------------------------------------------------------------------
# Instrumentation: wrap already-bound references, never edit source files.
# ---------------------------------------------------------------------------

_EVENTS: list[dict] = []


def _record(**kw) -> None:
    _EVENTS.append(kw)


def _diagnose_reroute_feasibility(zones: list[dict]) -> str:
    """Read-only replica of `_force_reroute_room_layout_to_one_zone_per_floor`'s
    own footprint-reconstruction test (`openubem/idf/surfaces.py:664-709`), used
    only to classify *why* a reroute would fail before calling the real
    function. Mutates nothing; the real function is still the one that decides.
    """
    rl_zones = [z for z in zones if z.get("mode") in ("room_layout", "european_dwelling_layout")]
    if not rl_zones:
        return "no_rl_zones"
    floor0 = [z["floor_polygon"] for z in rl_zones if (_get_floor_idx(z["name"]) or 0) == 0]
    if not floor0:
        return "no_floor0_zones"
    merged = unary_union([p.buffer(0.01, join_style=2) for p in floor0]).buffer(-0.01, join_style=2)
    footprint = shapely.make_valid(merged).buffer(0)
    if footprint.geom_type == "MultiPolygon":
        footprint = max(footprint.geoms, key=lambda g: g.area)
    if footprint.is_empty or footprint.geom_type != "Polygon":
        return "multipart_or_empty_after_union"
    if any(Polygon(r).area >= 1.0 for r in footprint.interiors):
        return "courtyard_hole_guard"
    if list(footprint.interiors):
        footprint = Polygon(footprint.exterior)
    footprint = shapely.set_precision(footprint, 0.005)
    if footprint.geom_type == "MultiPolygon":
        footprint = max(footprint.geoms, key=lambda g: g.area)
    if footprint.is_empty or footprint.geom_type != "Polygon":
        return "multipart_or_empty_after_set_precision"
    footprint = footprint.simplify(0.02, preserve_topology=True)
    if footprint.geom_type != "Polygon" or footprint.is_empty:
        return "multipart_or_empty_after_simplify"
    return "predicted_reconstructable"


def _wrap_reroute(original, site: str):
    def wrapper(idf, zones, reason):
        pre_diag = _diagnose_reroute_feasibility(zones)
        result = original(idf, zones, reason)
        _record(fn="force_reroute", site=site, reason=reason, pre_diagnosis=pre_diag, succeeded=bool(result))
        return result
    return wrapper


def _wrap_check(original, name: str):
    state = {"n": 0}

    def wrapper(idf):
        state["n"] += 1
        stage = "pre" if state["n"] == 1 else "post"
        result = original(idf)
        _record(fn=name, stage=stage, call_idx=state["n"], fired=bool(result))
        return result

    wrapper._state = state
    return wrapper


def _reset_per_building_state(wrapped_checks: list) -> None:
    _EVENTS.clear()
    for w in wrapped_checks:
        w._state["n"] = 0


def install_instrumentation():
    original_reroute = surfmod._force_reroute_room_layout_to_one_zone_per_floor
    surfmod._force_reroute_room_layout_to_one_zone_per_floor = _wrap_reroute(
        original_reroute, "extrude_geometry_intersect_exception"
    )
    camp._force_reroute_room_layout_to_one_zone_per_floor = _wrap_reroute(
        original_reroute, "post_extrude_atrisk_check"
    )
    wrapped_mismatch = _wrap_check(camp.find_mismatched_interzone_pairs, "find_mismatched_interzone_pairs")
    camp.find_mismatched_interzone_pairs = wrapped_mismatch
    wrapped_near_dup = _wrap_check(camp._has_near_duplicate_vertex_surfaces, "has_near_duplicate_vertex_surfaces")
    camp._has_near_duplicate_vertex_surfaces = wrapped_near_dup
    return [wrapped_mismatch, wrapped_near_dup]


# ---------------------------------------------------------------------------
# District row loading -- reuses prepare()'s own loaders unmodified.
# ---------------------------------------------------------------------------

def _load_district_rows(district: str):
    import geopandas as gpd

    cfg = dcamp.DISTRICTS[district]
    manifest = ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    weather, _weather_sha = dcamp._registry_weather(cfg["fold"], None)
    records = json.loads(
        (ROOT / f"openubem/data/construction/tabula_archetypes_{cfg['country'].lower()}.json")
        .read_text(encoding="utf-8")
    )["records"]
    if district == "GB-LDN-STDUNSTANS":
        rows, exclusions = dcamp._gb_rows(gdf, records)
    elif district == "IT-BOL-GALVANI2":
        rows, exclusions = dcamp._it_rows(gdf, records)
    else:
        rows, exclusions = dcamp._mapped_rows(district, gdf, records)
    buildings_clean = gpd.read_file(ROOT / f"openubem/outputs/eu02/{district}/01_buildings_clean.gpkg")
    district_median_height_m = camp.compute_district_median_residential_height_m(rows)
    return gdf, rows, exclusions, records, weather, buildings_clean, district_median_height_m


def _upstream_exclusion_reason(district: str, gdf, osm_id: str, records: list[dict]) -> str:
    """Only called for a named building absent from `rows`: replicate the
    per-item checks `_mapped_rows` runs (`scripts/run_eu_s2_district_campaign.py`
    :326-343) for this one row, read-only, to name which check excluded it --
    `_mapped_rows` itself only returns an aggregate `Counter`, not a per-building
    reason, so this is not otherwise recoverable from disk.
    """
    cfg = dcamp.DISTRICTS[district]
    if district == "FR-LYO-HAUTCOEURPENTES":
        gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))
    matches = gdf[gdf["osm_id"].astype(str) == osm_id]
    if len(matches) == 0:
        return "NOT_IN_02_RESIDENTIAL_MANIFEST_GPKG"
    item = matches.iloc[0]
    decision = map_observed_building_to_tabula(
        item, neighbourhood_id=district, country_stock_code=cfg["country"], records=records
    )
    if not decision.archetype_id:
        return f"archetype_mapping: {decision.reason or decision.mapping_status}"
    if dcamp._valid_storeys(item) is None:
        return "MISSING_OBSERVED_STOREY_COUNT"
    return "UNEXPLAINED (passed both _mapped_rows gates on replay -- report as-is)"


# ---------------------------------------------------------------------------
# Per-building instrumented trace.
# ---------------------------------------------------------------------------

def trace_one_building(
    data: dict, district: str, records, weather, buildings_clean,
    district_median_height_m, context_height_fallback_census, scratch_root: Path,
    wrapped_checks: list,
) -> dict:
    _reset_per_building_state(wrapped_checks)
    row = pd.Series(data)
    stem = hashlib.sha256(str(row.building_id).encode()).hexdigest()[:16]
    result = {
        "district": district, "building_id": row.building_id, "stem": stem,
        "geometry_outcome": None, "final_status": None, "exception": None,
        "eu17_dwelling_count": None, "eu17_zone_names": None,
        "eu11_dwelling_count": None, "eu11_zone_names": None,
        "events": None,
    }
    model_row = row.copy()
    model_row["building_id"] = stem
    try:
        zones, outcome = dcamp._geometry(model_row, records)
        result["geometry_outcome"] = outcome
        # prepare() (scripts/run_eu_s2_district_campaign.py:369-424) never skips
        # build_idf_for_building for a FALLBACK_PENDING_LAYOUT outcome -- _geometry
        # itself never refuses; it returns plain one_zone_per_floor box zones
        # (via build_zones, mode="one_zone_per_floor") and prepare() still extrudes
        # them. A box-only building carries no room_layout/european_dwelling_layout
        # zones, so it cannot be *rerouted*, but it still runs the same
        # find_mismatched_interzone_pairs / _has_near_duplicate_vertex_surfaces
        # gate and can still be lost outright to the same RuntimeError.
        context = camp.build_european_context(
            row.osm_id, row.geometry, buildings_clean, district_median_height_m,
            context_height_fallback_census,
        )
        record = next(x for x in records if x["archetype_id"] == row.archetype_id)
        run_dir = scratch_root / stem
        path = camp.build_idf_for_building(
            model_row, record, zones, run_dir, epw_path=weather, context=context,
        )
        rerouted = any(z.get("generation_status_note") == "room_layout_intersect_fallback" for z in zones)
        was_ruled_attempt = outcome not in ("FALLBACK_PENDING_LAYOUT", "FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT")
        if not was_ruled_attempt:
            result["final_status"] = "box_survived_generator_refused_no_ruled_attempt"
        elif rerouted:
            result["final_status"] = "rerouted_survived_box"
        else:
            result["final_status"] = "ruled_survived"
        plan = read_building_plan(path, stem=stem, building_id=row.building_id, district=district, geometry_outcome=outcome)
        result["eu17_dwelling_count"] = plan.dwelling_count
        result["eu17_zone_names"] = len(plan.zone_names)
        shutil.rmtree(run_dir, ignore_errors=True)
    except ValueError as exc:
        result["final_status"] = "value_error_excluded_pre_extrusion"
        result["exception"] = str(exc)
    except (RuntimeError, ZeroDivisionError, IndexError) as exc:
        kind = type(exc).__name__
        msg = str(exc)
        if kind == "RuntimeError" and msg.startswith("interzone_vertex_mismatch_unresolved"):
            result["final_status"] = "lost_interzone_vertex_mismatch_unresolved"
        else:
            result["final_status"] = f"lost_other_{kind}"
        result["exception"] = msg
    result["events"] = list(_EVENTS)
    _attach_eu11(result, district, stem)
    return result


def _attach_eu11(result: dict, district: str, stem: str) -> None:
    eu11_idf = EU11_ROOT / district / "idfs" / f"{stem}.idf"
    if not eu11_idf.exists():
        return
    plan = read_building_plan(eu11_idf, stem=stem, building_id=result["building_id"], district=district, geometry_outcome="EU11")
    result["eu11_dwelling_count"] = plan.dwelling_count
    result["eu11_zone_names"] = len(plan.zone_names)


# ---------------------------------------------------------------------------
# Driver: named buildings + stratified loss sample, per district.
# ---------------------------------------------------------------------------

def run_district(district: str, scratch_root: Path, wrapped_checks: list) -> dict:
    gdf, rows, _exclusions, records, weather, buildings_clean, district_median_height_m = _load_district_rows(district)
    context_height_fallback_census: Counter = Counter()

    named_targets = list(NAMED_BUILDINGS.get(district, []))
    named_traces: dict[str, dict] = {}
    loss_traces: list[dict] = []
    taxonomy: Counter = Counter()

    row_by_id = {str(d["building_id"]): d for d in rows}
    for osm_id in named_targets:
        if osm_id not in row_by_id:
            named_traces[osm_id] = {
                "district": district, "building_id": osm_id, "final_status": "excluded_upstream_of_geometry",
                "upstream_reason": _upstream_exclusion_reason(district, gdf, osm_id, records),
            }

    scanned = 0
    for data in rows:
        if scanned >= SCAN_CAP_PER_DISTRICT:
            break
        bid = str(data["building_id"])
        need_named = bid in named_targets and bid not in named_traces
        need_loss_sample = len(loss_traces) < LOSS_SAMPLE_TARGET_PER_DISTRICT
        if not need_named and not need_loss_sample:
            remaining_named = [t for t in named_targets if t not in named_traces]
            if not remaining_named:
                break
        scanned += 1
        trace = trace_one_building(
            data, district, records, weather, buildings_clean, district_median_height_m,
            context_height_fallback_census, scratch_root, wrapped_checks,
        )
        taxonomy[trace["final_status"]] += 1
        if need_named:
            named_traces[bid] = trace
        elif trace["final_status"] == "lost_interzone_vertex_mismatch_unresolved" and need_loss_sample:
            loss_traces.append(trace)

    for osm_id in named_targets:
        if osm_id not in named_traces:
            named_traces[osm_id] = {
                "district": district, "building_id": osm_id, "final_status": "NOT_ENCOUNTERED_within_scan_cap",
            }

    return {
        "district": district,
        "scanned": scanned,
        "population_total": len(rows),
        "taxonomy_over_scanned": dict(sorted(taxonomy.items())),
        "named_traces": named_traces,
        "loss_sample": loss_traces,
        "loss_sample_shortfall": max(0, LOSS_SAMPLE_TARGET_PER_DISTRICT - len(loss_traces)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", choices=list(dcamp.DISTRICTS), default=None)
    args = parser.parse_args()
    districts = [args.district] if args.district else list(dcamp.DISTRICTS)

    wrapped_checks = install_instrumentation()
    scratch_root = Path(tempfile.mkdtemp(prefix="eu17_reroute_trace_"))
    all_results = {}
    try:
        for district in districts:
            all_results[district] = run_district(district, scratch_root, wrapped_checks)
    finally:
        shutil.rmtree(scratch_root, ignore_errors=True)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = OUT_ROOT / (
        f"reroute_trace_{args.district}.json" if args.district else "reroute_trace.json"
    )
    out_path.write_text(json.dumps(all_results, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({d: r["taxonomy_over_scanned"] for d, r in all_results.items()}, indent=2))
    print(f"written: {out_path}")


if __name__ == "__main__":
    main()
