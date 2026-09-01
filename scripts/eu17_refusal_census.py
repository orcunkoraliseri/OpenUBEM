"""EU-17 T04: the deep refusal census.

`PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` fact 6: the ``fallback_reason``
recorded on a refused building is not always the true cause. ``_secondary``
(``european_residential.py:890-910``) stores ``legacy.fallback_reason if
legacy.fallback_reason else reason_hint`` -- so whenever the legacy
``equal_strip_multi_angle_sweep`` cutter *also* fails on the same footprint,
its own reason (typically ``NARROW_FOOTPRINT_LT_8M`` or
``PARTITION_AUDIT_FAILED``) overwrites the ruled route's real ``reason_hint``
(``L_SHAPE_DECOMPOSITION_FAILED``, ``INTERIOR_RING_COURTYARD_UNFOLD_FAILED``,
``REGULARIZATION_AREA_DELTA_GT_2PCT``, ...) before it is ever returned.

This script replays ``generate_european_building_dwelling_layout`` on every
simulated footprint exactly as ``scripts/emit_eu11_layout_sidecars.py`` does
(same row preparation, same four-tier dwelling-count imputation, same
``allocate_european_dwellings`` call) to reproduce the *recorded* (masked)
refusal totals and reasons -- then, for every refused building only, calls
the module's own routes directly (``classify_building_morphology``,
``regularize_footprint_orthogonal``, ``generate_european_grid_layout``,
``generate_european_linear_gallery_layout``, ``generate_european_courtyard_layout``,
``_split_at_reflex_vertex``, ``_l_shape_wings``, ``_allocate_wing_dwelling_counts``,
``_combine_wing_results``, ``_courtyard_wings_and_nodes``) in the same order
the ruled dispatch (``generate_european_ruled_storey_layout``,
``european_residential.py:855-1003``) uses, stopping *before* the point where
``_secondary`` would run the legacy cutter and mask the reason. That gives
the *true* reason_hint -- route taken, which wing failed, at what depth --
without ever modifying the library (no shipping log lines added to it).

Output: ``openubem/outputs/eu_evidence/EU-17/refusal_census.csv`` (one row
per refused building) and ``refusal_census_summary.csv`` (per-district old
vs. new reason distribution, long format).

Nothing here simulates or writes an IDF (`D-EU-55`): this is a pure-Python
replay of the geometry generator against the Step 2 footprints.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.geometry.european_residential import (
    CIRCULATION_FRACTION_OF_PLATE,
    CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION,
    EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    RULED_GRID_MAX_DWELLINGS_PER_FLOOR,
    EuropeanGridLayout,
    _allocate_wing_dwelling_counts,
    _combine_wing_results,
    _courtyard_wings_and_nodes,
    _facade_contact_lengths,
    _l_shape_wings,
    _minimum_rotated_width_m,
    _reflex_vertex_count,
    _split_at_reflex_vertex,
    allocate_european_dwellings,
    audit_european_floor_partition,
    classify_building_morphology,
    generate_european_building_dwelling_layout,
    generate_european_courtyard_layout,
    generate_european_grid_layout,
    generate_european_linear_gallery_layout,
    generate_european_ruled_storey_layout,
    regularize_footprint_orthogonal,
)
from scripts.run_eu_s2_district_campaign import (
    DISTRICTS, _gb_rows, _it_rows, _mapped_rows, _records, _valid_storeys,
)

REPO_ROOT = Path("C:/Users/o_iseri/Desktop/OpenUBEM")
OUT_DIR = REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-17"

CENSUS_FIELDNAMES = [
    "district", "building_id", "stem", "storeys", "dwellings_total",
    "observed_max_per_floor", "morphology_route", "reflex_count",
    "hull_deficit_fraction", "min_rotated_width_m", "failing_dwelling_count",
    "recorded_fallback_reason", "true_fallback_reason", "masked",
    "gates_evaluated", "wing_failure_detail",
]


def _footprint_metrics(footprint) -> tuple[int, float, float]:
    """Mirror ``classify_building_morphology``'s own denoise/hull/reflex steps
    (``european_residential.py:442-454``) purely for the census's descriptive
    columns -- never used to decide route dispatch (that stays the module's
    own ``classify_building_morphology`` call)."""
    has_courtyard = bool(footprint.interiors)
    denoised = footprint.simplify(0.5, preserve_topology=True)
    if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
        denoised = footprint
    hull_deficit_fraction = (
        (denoised.convex_hull.area - denoised.area) / denoised.area if denoised.area > 0 else 0.0
    )
    reflex_count = _reflex_vertex_count(denoised) if (not has_courtyard and hull_deficit_fraction > 0.03) else 0
    min_width = _minimum_rotated_width_m(footprint)
    return reflex_count, hull_deficit_fraction, min_width


def _trace_storey(
    footprint, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
    regularization_tolerance_m: float = 0.15,
) -> dict:
    """Replay ``generate_european_ruled_storey_layout``'s own dispatch
    (``european_residential.py:855-1003``) one gate at a time, calling the
    module's real routes directly, but returning -- instead of handing a
    refusal to ``_secondary`` -- the untainted ``reason_hint`` that call
    would have carried. Recurses into itself for L-shape/courtyard wings, so
    a wing's own true cause is never masked either."""
    if dwelling_count == 1:
        # Mirrors european_residential.py:873-888 exactly: a single dwelling
        # always takes the whole plate and can never refuse. Built as a real
        # EuropeanGridLayout (not layout=None) because L-shape/courtyard
        # combination needs an actual wing_results entry for every wing,
        # including a 1-dwelling one.
        facade_lengths = _facade_contact_lengths(footprint, (footprint,))
        audit = audit_european_floor_partition(
            footprint, (footprint,), expected_dwelling_count=1,
            topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
        )
        layout = EuropeanGridLayout(
            scheme="ruled_grid_1x1", grid="ruled_grid_1x1", nu=1, nv=1, dwelling_polygons=(footprint,),
            circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
            circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=facade_lengths,
            habitability_rotation_applied=False, habitability_downgrade_applied=False, partition_audit=audit,
            fallback_reason=None, dwelling_layout_emitted=True,
        )
        return {
            "emitted": True, "scheme": "ruled_grid_1x1", "true_reason": None,
            "route": "single_dwelling_whole_plate", "gates": [], "layout": layout, "wing_detail": None,
        }

    if dwelling_count == 2:
        route = "bisection_2x1"
        gates: list = []
        regularization = regularize_footprint_orthogonal(footprint, tolerance_m=regularization_tolerance_m)
        if regularization.exceeds_fallback_band:
            gates.append(("REGULARIZATION_AREA_DELTA", f"FAILED:{regularization.plate_area_delta_fraction:.4f}"))
            return {"emitted": False, "scheme": None, "true_reason": "REGULARIZATION_AREA_DELTA_GT_2PCT",
                    "route": route, "gates": gates, "layout": None, "wing_detail": None}
        gates.append(("REGULARIZATION_AREA_DELTA", "PASSED"))
        try:
            result = generate_european_grid_layout(
                regularization.regularized_polygon, dwelling_count=2,
                minimum_facade_contact_m=minimum_facade_contact_m,
            )
        except (ValueError, IndexError):
            gates.append(("GRID_LAYOUT_2X1", "RAISED"))
            return {"emitted": False, "scheme": None, "true_reason": "PARTITION_AUDIT_FAILED",
                    "route": route, "gates": gates, "layout": None, "wing_detail": None}
        if not result.dwelling_layout_emitted:
            gates.append(("GRID_LAYOUT_2X1", f"FAILED:{result.fallback_reason}"))
            return {"emitted": False, "scheme": None, "true_reason": result.fallback_reason,
                    "route": route, "gates": gates, "layout": None, "wing_detail": None}
        gates.append(("GRID_LAYOUT_2X1", "EMITTED"))
        return {"emitted": True, "scheme": result.scheme, "true_reason": None,
                "route": route, "gates": gates, "layout": result, "wing_detail": None}

    morphology = classify_building_morphology(footprint)
    route = morphology.route
    gates = [("MORPHOLOGY_CLASSIFY", route)]

    if route == "courtyard_secondary":
        wants_circulation = dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION
        target_circulation_area = CIRCULATION_FRACTION_OF_PLATE * footprint.area if wants_circulation else 0.0
        try:
            wings, nodes = _courtyard_wings_and_nodes(footprint, circulation_area_total_m2=target_circulation_area)
        except (ValueError, IndexError):
            gates.append(("COURTYARD_UNFOLD_WINGS", "RAISED"))
            return {"emitted": False, "scheme": None, "true_reason": f"{morphology.reason}_FAILED",
                    "route": route, "gates": gates, "layout": None, "wing_detail": None}
        try:
            counts = _allocate_wing_dwelling_counts([w.area for w in wings], dwelling_count)
        except ValueError:
            gates.append(("COURTYARD_ALLOCATE_WING_COUNTS", "RAISED"))
            return {"emitted": False, "scheme": None, "true_reason": f"{morphology.reason}_FAILED",
                    "route": route, "gates": gates, "layout": None, "wing_detail": None}
        wing_traces = [
            _trace_storey(w, c, minimum_facade_contact_m, regularization_tolerance_m)
            for w, c in zip(wings, counts)
        ]
        failed = [i for i, t in enumerate(wing_traces) if not t["emitted"]]
        if failed:
            gates.append(("COURTYARD_WINGS", f"{len(wings)} wings, {len(failed)} failed"))
            wing_detail = [
                {"wing_index": i, "true_reason": wing_traces[i]["true_reason"], "route": wing_traces[i]["route"]}
                for i in failed
            ]
            return {"emitted": False, "scheme": None, "true_reason": f"{morphology.reason}_FAILED",
                    "route": route, "gates": gates, "layout": None, "wing_detail": wing_detail}
        gates.append(("COURTYARD_WINGS", f"{len(wings)} wings, all emitted"))
        wing_results = [t["layout"] for t in wing_traces]
        combined = _combine_wing_results(
            footprint, wing_results, dwelling_count=dwelling_count,
            minimum_facade_contact_m=minimum_facade_contact_m, scheme="courtyard_wing_unfold",
            extra_circulation=nodes, keep_circulation_polygon=True,
        )
        if combined is None:
            gates.append(("COURTYARD_COMBINE", "FAILED"))
            return {"emitted": False, "scheme": None, "true_reason": f"{morphology.reason}_FAILED",
                    "route": route, "gates": gates, "layout": None, "wing_detail": None}
        gates.append(("COURTYARD_COMBINE", "SUCCESS"))
        return {"emitted": True, "scheme": combined.scheme, "true_reason": None,
                "route": route, "gates": gates, "layout": combined, "wing_detail": None}

    if route == "l_shape_decomposition":
        wing_candidates: list = []
        seen_area_signatures: list = []

        def _add_candidate(wings_to_add) -> None:
            signature = [round(w.area, 6) for w in wings_to_add]
            if len(wings_to_add) >= 2 and signature not in seen_area_signatures:
                wing_candidates.append(wings_to_add)
                seen_area_signatures.append(signature)

        try:
            larger, smaller = _split_at_reflex_vertex(footprint, tolerance_m=0.5)
            _add_candidate([larger, smaller])
        except (ValueError, IndexError):
            pass
        try:
            larger, smaller = _split_at_reflex_vertex(footprint, tolerance_m=regularization_tolerance_m)
            _add_candidate([larger, smaller])
        except (ValueError, IndexError):
            pass
        try:
            _add_candidate(_l_shape_wings(footprint, tolerance_m=regularization_tolerance_m))
        except (ValueError, IndexError):
            pass

        candidate_log: list = []
        success = None
        for cand_idx, wings in enumerate(wing_candidates):
            try:
                counts = _allocate_wing_dwelling_counts([w.area for w in wings], dwelling_count)
            except ValueError:
                candidate_log.append({"candidate": cand_idx, "n_wings": len(wings), "outcome": "ALLOCATE_FAILED"})
                continue
            wing_traces = [
                _trace_storey(w, c, minimum_facade_contact_m, regularization_tolerance_m)
                for w, c in zip(wings, counts)
            ]
            failed = [i for i, t in enumerate(wing_traces) if not t["emitted"]]
            if failed:
                candidate_log.append({
                    "candidate": cand_idx, "n_wings": len(wings), "outcome": "WING_FAILED",
                    "failed_wing_indices": failed,
                    "failed_wing_reasons": [wing_traces[i]["true_reason"] for i in failed],
                    "failed_wing_routes": [wing_traces[i]["route"] for i in failed],
                })
                continue
            wing_results = [t["layout"] for t in wing_traces]
            try:
                combined = _combine_wing_results(
                    footprint, wing_results, dwelling_count=dwelling_count,
                    minimum_facade_contact_m=minimum_facade_contact_m, scheme="l_shape_decomposition",
                    keep_circulation_polygon=False,
                )
            except (ValueError, IndexError):
                combined = None
            if combined is None:
                candidate_log.append({"candidate": cand_idx, "n_wings": len(wings), "outcome": "COMBINE_FAILED"})
                continue
            candidate_log.append({"candidate": cand_idx, "n_wings": len(wings), "outcome": "SUCCESS"})
            success = combined
            break
        gates.append(("L_SHAPE_WING_CANDIDATES", candidate_log))
        if success is not None:
            return {"emitted": True, "scheme": success.scheme, "true_reason": None,
                    "route": route, "gates": gates, "layout": success, "wing_detail": None}
        return {"emitted": False, "scheme": None, "true_reason": "L_SHAPE_DECOMPOSITION_FAILED",
                "route": route, "gates": gates, "layout": None, "wing_detail": candidate_log}

    # i_shape_linear_gallery or point_block_grid
    regularization = regularize_footprint_orthogonal(footprint, tolerance_m=regularization_tolerance_m)
    if regularization.exceeds_fallback_band:
        gates.append(("REGULARIZATION_AREA_DELTA", f"FAILED:{regularization.plate_area_delta_fraction:.4f}"))
        return {"emitted": False, "scheme": None, "true_reason": "REGULARIZATION_AREA_DELTA_GT_2PCT",
                "route": route, "gates": gates, "layout": None, "wing_detail": None}
    gates.append(("REGULARIZATION_AREA_DELTA", "PASSED"))
    plate = regularization.regularized_polygon
    gate_name = "LINEAR_GALLERY_LAYOUT" if route == "i_shape_linear_gallery" else "GRID_LAYOUT"
    try:
        if route == "i_shape_linear_gallery":
            result = generate_european_linear_gallery_layout(
                plate, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
            )
        else:
            result = generate_european_grid_layout(
                plate, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
            )
    except (ValueError, IndexError):
        gates.append((gate_name, "RAISED"))
        return {"emitted": False, "scheme": None, "true_reason": "PARTITION_AUDIT_FAILED",
                "route": route, "gates": gates, "layout": None, "wing_detail": None}
    if not result.dwelling_layout_emitted:
        gates.append((gate_name, f"FAILED:{result.fallback_reason}"))
        return {"emitted": False, "scheme": None, "true_reason": result.fallback_reason,
                "route": route, "gates": gates, "layout": None, "wing_detail": None}
    gates.append((gate_name, "EMITTED"))
    return {"emitted": True, "scheme": result.scheme, "true_reason": None,
            "route": route, "gates": gates, "layout": result, "wing_detail": None}


def census_building(footprint, floor_allocations, minimum_facade_contact_m: float = 2.5) -> dict:
    """Recorded (masked) outcome from the real building-level entry point,
    plus -- only when refused -- the true cause from ``_trace_storey``."""
    observed_max_per_floor = max(fa.dwelling_count for fa in floor_allocations)
    if observed_max_per_floor > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        return {
            "emitted": False, "recorded_reason": "DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8",
            "true_reason": "DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8", "route": None,
            "observed_max_per_floor": observed_max_per_floor,
            "failing_dwelling_count": None, "gates": [("DENSITY_CAP", "FAILED")], "wing_detail": None,
        }

    real_layout = generate_european_building_dwelling_layout(footprint, floor_allocations=floor_allocations)
    if real_layout.dwelling_layout_emitted:
        return {
            "emitted": True, "recorded_reason": None, "true_reason": None, "route": None,
            "observed_max_per_floor": observed_max_per_floor,
            "failing_dwelling_count": None, "gates": [], "wing_detail": None,
        }

    # Refused: find the first failing distinct dwelling count in storey
    # order (mirrors generate_european_building_dwelling_layout's own
    # ``groups``/``reason`` resolution, european_residential.py:1772-1794).
    storey_cache: dict[int, object] = {}
    failing_count = None
    for allocation in floor_allocations:
        count = allocation.dwelling_count
        if count == 0:
            continue
        if count not in storey_cache:
            storey_cache[count] = generate_european_ruled_storey_layout(
                footprint, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
            )
        if failing_count is None and not storey_cache[count].dwelling_layout_emitted:
            failing_count = count
    if failing_count is None:
        failing_count = next(fa.dwelling_count for fa in floor_allocations if fa.dwelling_count > 0)

    try:
        trace = _trace_storey(footprint, failing_count, minimum_facade_contact_m=minimum_facade_contact_m)
    except Exception as exc:  # defensive: never let a census-only re-derivation crash the run
        trace = {
            "true_reason": f"TRACE_ERROR:{exc}", "route": None,
            "gates": [("TRACE_ERROR", str(exc))], "wing_detail": None,
        }

    return {
        "emitted": False,
        "recorded_reason": real_layout.fallback_reason,
        "true_reason": trace["true_reason"],
        "route": trace["route"],
        "observed_max_per_floor": observed_max_per_floor,
        "failing_dwelling_count": failing_count,
        "gates": trace["gates"],
        "wing_detail": trace["wing_detail"],
    }


def census_district(district: str) -> dict:
    cfg = DISTRICTS[district]
    dist_dir = REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / district
    manifest_slug = district.lower().replace("-", "_") + "_manifest.csv"
    manifest_path = dist_dir / manifest_slug
    manifest_df = pd.read_csv(manifest_path)
    simulated_ids = set(manifest_df["building_id"].astype(str))

    step2_manifest = REPO_ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg"
    gdf = gpd.read_file(step2_manifest)
    records = _records(cfg["country"])

    if district == "GB-LDN-STDUNSTANS":
        rows, _ = _gb_rows(gdf, records)
    elif district == "IT-BOL-GALVANI2":
        rows, _ = _it_rows(gdf, records)
    else:
        rows, _ = _mapped_rows(district, gdf, records)

    row_map = {str(r["building_id"]): r for r in rows if str(r["building_id"]) in simulated_ids}

    census_rows: list[dict] = []
    recorded_counter: Counter = Counter()
    true_counter: Counter = Counter()
    refused = 0

    for bid, data in row_map.items():
        row = pd.Series(data)
        footprint = row.geometry
        n_storey = _valid_storeys(row)
        dwellings = row.get("observed_dwellings")

        is_observed = pd.notna(dwellings) and float(dwellings).is_integer() and float(dwellings) > 0
        if is_observed:
            dwellings_val = int(dwellings)
        else:
            btype = row["building_type"]
            rec = next((x for x in records if x["archetype_id"] == row["archetype_id"]), None)
            if btype in ("SFH", "TH"):
                dwellings_val = 1
            else:
                n_apt = rec.get("n_apartment") if rec else 10.0
                dwellings_val = max(1, round(float(n_apt))) if pd.notna(n_apt) else 10

        allocation = allocate_european_dwellings(
            archetype_id=row["archetype_id"], building_type=row["building_type"],
            n_apartment=dwellings_val, n_storey=n_storey, plate_area_m2=float(footprint.area),
        )

        result = census_building(footprint, allocation.floor_allocations)
        if result["emitted"]:
            continue

        refused += 1
        reflex_count, hull_deficit, min_width = _footprint_metrics(footprint)
        recorded = result["recorded_reason"]
        true_r = result["true_reason"]
        recorded_counter[recorded] += 1
        true_counter[true_r] += 1
        stem = hashlib.sha256(str(bid).encode()).hexdigest()[:16]
        census_rows.append({
            "district": district, "building_id": bid, "stem": stem,
            "storeys": allocation.storey_count, "dwellings_total": allocation.dwelling_count,
            "observed_max_per_floor": result["observed_max_per_floor"],
            "morphology_route": result["route"],
            "reflex_count": reflex_count, "hull_deficit_fraction": round(hull_deficit, 6),
            "min_rotated_width_m": round(min_width, 4),
            "failing_dwelling_count": result["failing_dwelling_count"],
            "recorded_fallback_reason": recorded,
            "true_fallback_reason": true_r,
            "masked": recorded != true_r,
            "gates_evaluated": json.dumps(result["gates"]),
            "wing_failure_detail": json.dumps(result["wing_detail"]) if result["wing_detail"] else "",
        })

    return {
        "district": district, "total": len(row_map), "refused": refused,
        "recorded_counter": recorded_counter, "true_counter": true_counter,
        "rows": census_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="EU-17 T04: the deep refusal census.")
    parser.add_argument("--district", action="append", choices=sorted(DISTRICTS), default=None)
    args = parser.parse_args()
    targets = args.district if args.district else sorted(DISTRICTS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    district_results: list[dict] = []
    for district in targets:
        result = census_district(district)
        district_results.append(result)
        all_rows.extend(result["rows"])
        print(f"[{district}] {result['total']} buildings, {result['refused']} refused")
        print(f"  recorded: {dict(result['recorded_counter'])}")
        print(f"  true:     {dict(result['true_counter'])}")

    census_path = OUT_DIR / "refusal_census.csv"
    with census_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CENSUS_FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    summary_rows: list[dict] = []
    for result in district_results:
        for label, counter in (("recorded", result["recorded_counter"]), ("true", result["true_counter"])):
            for reason, count in sorted(counter.items(), key=lambda kv: -kv[1]):
                summary_rows.append({"district": result["district"], "label": label, "reason": reason, "count": count})
        reclassified = sum(1 for r in result["rows"] if r["masked"])
        summary_rows.append({"district": result["district"], "label": "reclassified_count", "reason": "", "count": reclassified})

    summary_path = OUT_DIR / "refusal_census_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["district", "label", "reason", "count"])
        writer.writeheader()
        writer.writerows(summary_rows)

    fleet_total = sum(r["total"] for r in district_results)
    fleet_refused = sum(r["refused"] for r in district_results)
    print(f"\nFleet: {fleet_total} buildings, {fleet_refused} refused")
    for result in district_results:
        print(f"{result['district']}: {result['refused']}/{result['total']} refused")
    print(f"Written {census_path}")
    print(f"Written {summary_path}")


if __name__ == "__main__":
    main()
