"""Emit per-building dwelling layout side-cars and update EU-11 manifests (EU-13).

Fixes:
- FINDING EU-12-01: Extrudes all storeys (n_storey floors).
- Non-convex and courtyard footprint partitioning.
- 4-Tier dwelling count imputation with explicit provenance.
- Tags geometry_outcome as DWELLING_LAYOUT_EMITTED or DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry.polygon import orient

from openubem.geometry.european_residential import (
    DWELLING_DENSITY_REFUSAL_TOKEN,
    allocate_european_dwellings,
    european_building_layout_area_summary,
    european_building_layout_to_zone_specs,
    generate_european_building_dwelling_layout,
    regularize_footprint_orthogonal,
)
from openubem.semantic.european_archetype_mapping import (
    apply_attribute_sidecar,
    compute_footprint_adjacency,
    map_observed_building_to_tabula,
)
from openubem.semantic.construction_sets import tabula_period
from scripts.run_eu_s2_district_campaign import (
    _records, _valid_storeys, DISTRICTS, ES_SIDECAR, GB_EPC, GB_EPC_BANDS,
    _gb_rows, _gb_impute_rows, _it_rows, _mapped_rows, FLOOR_TO_FLOOR_M, ZONE_WINDING_SIGN
)
from scripts.eu_idf_plan_reader import read_district

REPO_ROOT = Path("C:/Users/o_iseri/Desktop/OpenUBEM")


class ManifestSafetyError(RuntimeError):
    """Raised when a manifest column update would blank, drop or widen data
    the caller does not own. See EU-14B T01."""


def _is_blank(value: Any) -> bool:
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def safe_update_manifest_columns(
    manifest_path: Path,
    column_updates: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Read ``manifest_path`` fresh and apply ``column_updates`` (column name ->
    {building_id: value}) to *only* those columns, for *only* the building_ids
    present in the update dict.

    EU-14B T01: the previous implementation wrote
    ``updated_outcomes.get(str(b), "")`` for every manifest row, so any mismatch
    between the rows the emitter recomputed and the rows already on disk (e.g.
    Bologna's ISTAT-imputed rows never matching the generic archetype-mapping
    codepath) silently blanked ``geometry_outcome`` fleet-wide. This function
    can only ever touch the building_ids it was actually given data for, and it
    asserts -- before writing anything -- that row count and the building_id
    set are unchanged and that no previously non-null/non-blank cell in any
    column became null or blank. If any assertion fails, it raises
    ``ManifestSafetyError`` and leaves ``manifest_path`` untouched.
    """
    original_df = pd.read_csv(manifest_path)
    if "building_id" not in original_df.columns:
        raise ManifestSafetyError(f"{manifest_path}: no building_id column, refusing to write")

    bids = original_df["building_id"].astype(str)
    bid_set = set(bids)

    for column, updates in column_updates.items():
        unknown_bids = set(updates) - bid_set
        if unknown_bids:
            sample = sorted(unknown_bids)[:3]
            raise ManifestSafetyError(
                f"{manifest_path.name}: column '{column}' update references "
                f"{len(unknown_bids)} building_id(s) absent from the manifest "
                f"(e.g. {sample}); aborting without writing"
            )

    new_df = original_df.copy()
    any_column_written = False
    for column, updates in column_updates.items():
        if not updates:
            # Nothing computed for this column this run: never widen the
            # manifest with a column that would carry no data.
            continue
        any_column_written = True
        if column not in new_df.columns:
            new_df[column] = pd.NA
        new_values = new_df[column].tolist()
        for i, bid in enumerate(bids):
            if bid in updates:
                new_values[i] = updates[bid]
        new_df[column] = new_values

    if not any_column_written:
        # Nothing to write at all: leave the file untouched rather than
        # round-tripping it through pandas for no data change.
        return original_df

    if len(new_df) != len(original_df):
        raise ManifestSafetyError(
            f"{manifest_path.name}: row count changed {len(original_df)} -> "
            f"{len(new_df)}; aborting without writing"
        )
    if set(new_df["building_id"].astype(str)) != bid_set:
        raise ManifestSafetyError(
            f"{manifest_path.name}: building_id set changed; aborting without writing"
        )
    for col in original_df.columns:
        old_blank = original_df[col].map(_is_blank)
        new_blank = new_df[col].map(_is_blank)
        newly_blank = (~old_blank) & new_blank
        if newly_blank.any():
            raise ManifestSafetyError(
                f"{manifest_path.name}: column '{col}' would lose "
                f"{int(newly_blank.sum())} previously non-blank value(s); "
                f"aborting without writing"
            )

    new_df.to_csv(manifest_path, index=False)
    return new_df


def emit_layouts_for_district(
    district: str,
    evidence_root: Path | None = None,
    population_manifest: Path | None = None,
) -> dict[str, Any]:
    """``evidence_root`` overrides the EU-11 default (T10/T12: point at the
    EU-17 rebuild tree, same layout as EU-11 per dependency decision §4.8).
    Default unchanged so every existing EU-11 call site behaves identically.

    ``population_manifest`` (T07c/D-EU-114) overrides only the source of
    ``simulated_ids`` -- IDFs still come from ``evidence_root``'s ``dist_dir``
    and output still goes to ``dist_dir/layouts``. When given, the manifest
    write-back (``safe_update_manifest_columns``) is skipped entirely."""
    cfg = DISTRICTS[district]
    dist_dir = (evidence_root if evidence_root is not None else (
        REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / district
    )).resolve()
    layouts_dir = dist_dir / "layouts"
    layouts_dir.mkdir(parents=True, exist_ok=True)

    manifest_slug = district.lower().replace("-", "_") + "_manifest.csv"
    manifest_path = dist_dir / manifest_slug
    has_manifest = manifest_path.exists()

    if not has_manifest:
        print(f"[{district}] No EU-11 manifest (unsimulated). 0 layout side-cars emitted.")
        return {
            "district": district,
            "population_total": 1220 if district == "IT-BOL-GALVANI2" else 0,
            "population_simulated": 0,
            "observed_emitted": 0,
            "imputed_emitted": 0,
            "narrow_fallback": 0,
            "other_fallback": 0,
            "not_simulated": 1220 if district == "IT-BOL-GALVANI2" else 0,
            "outcomes": {},
            "fallback_reasons": {"NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE": 1220} if district == "IT-BOL-GALVANI2" else {},
        }

    manifest_df = pd.read_csv(manifest_path)
    if population_manifest is not None:
        population_df = pd.read_csv(population_manifest)
        simulated_ids = set(population_df["building_id"].astype(str))
    else:
        simulated_ids = set(manifest_df["building_id"].astype(str))

    # T09(b) / FINDING 213: this emitter recomputes a layout from the raw
    # footprint (below) and has no way to know `build_idf_for_building`
    # rerouted that same building to one_zone_per_floor inside geomeppy --
    # the ``DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`` outcome
    # write-back (`run_eu_s2_district_campaign.py:391-392`) only exists on
    # `prepared_buildings.csv` rows built after 2026-08-31 and is therefore
    # stale on most of the fleet's already-built IDFs. Read the actual IDF
    # zone kinds instead of trusting that column -- ground truth, not a
    # second independent recomputation of what the layout *should* be.
    try:
        idf_plans_by_id = {plan.building_id: plan for plan in read_district(district, dist_dir)}
    except (FileNotFoundError, ValueError) as exc:
        print(f"[{district}] WARNING: could not read IDF plans for parity check ({exc}); "
              f"proceeding without reroute disclosure for this run.")
        idf_plans_by_id = {}

    # Read Step 2 manifest
    step2_manifest = REPO_ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg"
    gdf = gpd.read_file(step2_manifest)
    records = _records(cfg["country"])

    # EU-14B T01: mirrors scripts/run_eu_s2_district_campaign.py::prepare
    # (line ~345). Bologna's rows come from the ISTAT census-section cascade
    # (_it_rows), not the generic observed-attribute mapper (_mapped_rows) --
    # the latter requires an observed year_built/building_tag Bologna's OSM
    # extract never carries, so it always returned zero mapped rows for
    # IT-BOL-GALVANI2 (root cause of the manifest-corruption bug, see T01).
    if district == "GB-LDN-STDUNSTANS":
        rows, _ = _gb_rows(gdf, records)
        recovered_rows, _ = _gb_impute_rows(gdf, records, rows)
        rows = rows + recovered_rows
    elif district == "IT-BOL-GALVANI2":
        rows, _ = _it_rows(gdf, records)
    else:
        rows, _ = _mapped_rows(district, gdf, records)

    # Filter rows to only those that were simulated in EU-11
    row_map = {str(r["building_id"]): r for r in rows if str(r["building_id"]) in simulated_ids}

    layout_paths: dict[str, str] = {}
    updated_outcomes: dict[str, str] = {}
    outcome_counter = Counter()
    fallback_counter = Counter()
    observed_emitted_count = 0
    imputed_emitted_count = 0
    narrow_fallback_count = 0
    density_exceeded_count = 0
    regularization_fallback_count = 0
    other_fallback_count = 0
    idf_reroute_divergence_count = 0
    scheme_histogram: Counter = Counter()
    strip_cutter_reason_counter: Counter = Counter()
    regularization_deltas: list[float] = []
    circulation_outside_band_count = 0
    habitability_rotation_total = 0
    habitability_downgrade_total = 0

    for bid, data in row_map.items():
        row = pd.Series(data)
        footprint = row.geometry
        n_storey = _valid_storeys(row)
        dwellings = row.get("observed_dwellings")

        # Determine dwelling count and provenance (Observed vs Imputed Cascade)
        is_observed = pd.notna(dwellings) and float(dwellings).is_integer() and float(dwellings) > 0
        if is_observed:
            dwellings_val = int(dwellings)
            provenance_token = "OBSERVED_CATASTRO"
        else:
            btype = row["building_type"]
            rec = next((x for x in records if x["archetype_id"] == row["archetype_id"]), None)
            if btype in ("SFH", "TH"):
                dwellings_val = 1
                provenance_token = "IMPUTED_TIER4_TYPOLOGY_SFH_TH"
            else:
                n_apt = rec.get("n_apartment") if rec else 10.0
                dwellings_val = max(1, round(float(n_apt))) if pd.notna(n_apt) else 10
                provenance_token = "IMPUTED_TIER4_STATISTICAL_TABULA"

        allocation = allocate_european_dwellings(
            archetype_id=row["archetype_id"],
            building_type=row["building_type"],
            n_apartment=dwellings_val,
            n_storey=n_storey,
            plate_area_m2=float(footprint.area),
        )

        # EU-13B T01/T02/T04/T05/T07: conserve the declared dwelling total
        # storey-by-storey, cap density at the ruled grid's 8/floor ceiling,
        # and use the ruled n_u x n_v grid / morphological routes as the
        # primary scheme (equal_strip_multi_angle_sweep stays the secondary
        # route for storeys the ruled grid cannot serve).
        building_layout = generate_european_building_dwelling_layout(
            footprint,
            floor_allocations=allocation.floor_allocations,
        )

        # T09(b): the IDF actually built for this building is the ground
        # truth (rule 3). If every zone the IDF carries is a `whole` (massing
        # box) zone while this independent recompute would have emitted a
        # ruled layout, the IDF was rerouted inside geomeppy after this
        # generator ran (FINDING 210/213) -- the side-car must describe what
        # was simulated, not what the generator alone would have produced.
        idf_plan = idf_plans_by_id.get(bid)
        idf_reroute_divergence = (
            building_layout.dwelling_layout_emitted
            and idf_plan is not None
            and bool(idf_plan.zones)
            and all(z.kind == "whole" for z in idf_plan.zones)
        )

        if building_layout.dwelling_layout_emitted and not idf_reroute_divergence:
            scheme_by_storey = list(building_layout.scheme_by_storey)
            fallback_reason_by_storey = list(building_layout.fallback_reason_by_storey)
            # D-EU-111 (T02): a best-effort storey rides `fallback_reason_by_storey`
            # unchanged (fact 3) -- its own outcome token, never folded into the
            # plain `DWELLING_LAYOUT_EMITTED*` tokens, same as the campaign.
            best_effort_reasons = [
                reason for reason in fallback_reason_by_storey if reason and reason.startswith("NOCORE_BEST_EFFORT_")
            ]
            if best_effort_reasons:
                outcome = "DWELLING_LAYOUT_EMITTED_BEST_EFFORT" if is_observed else "DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT"
                best_effort_failed_checks = sorted({
                    check_id
                    for reason in best_effort_reasons
                    for check_id in reason[len("NOCORE_BEST_EFFORT_"):].split("_")
                })
            else:
                outcome = "DWELLING_LAYOUT_EMITTED" if is_observed else "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT"
                best_effort_failed_checks = []
            if is_observed:
                observed_emitted_count += 1
            else:
                imputed_emitted_count += 1
            scheme_str = scheme_by_storey[0] if scheme_by_storey else None
            if best_effort_reasons:
                fb_reason = best_effort_reasons[0]
            elif scheme_str == "equal_strip_multi_angle_sweep" and fallback_reason_by_storey:
                fb_reason = fallback_reason_by_storey[0]
            else:
                fb_reason = None
            if scheme_str == "equal_strip_multi_angle_sweep":
                strip_cutter_reason_counter[fb_reason or "UNKNOWN"] += 1
            zones = european_building_layout_to_zone_specs(
                building_layout,
                building_id=row["building_id"],
                height_m=FLOOR_TO_FLOOR_M,
            )
        elif idf_reroute_divergence:
            # T09(b) / FINDING 213 -> 0: the ruled layout generated cleanly
            # but the IDF that actually simulates this building was rerouted
            # to one_zone_per_floor after that (FINDING 210's safety net).
            # This is not a refusal (fallback_reason counters below do not
            # apply -- the layout was never rejected) and it is not a ruled
            # emission either: name it as its own, loud outcome so no layer
            # can advertise a layout that did not run.
            #
            # D-EU-62 (2026-09-01): P00 proved these layouts are
            # geometrically sound on their own (max interzone overlap
            # 5.0e-10 m2, area conserved to <=0.01 %) -- only the IDF that
            # would simulate them was demoted. The deliverable of this arc is
            # a drawn floor plan, not a simulation result, so the ruled
            # geometry is carried through exactly as the
            # DWELLING_LAYOUT_EMITTED branch above computes it; the loud
            # ..._REROUTED outcome plus idf_reroute_divergence=True on the
            # payload keep this from ever being read as simulated/certified.
            outcome = "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"
            fb_reason = None
            best_effort_failed_checks = []
            scheme_by_storey = list(building_layout.scheme_by_storey)
            scheme_str = scheme_by_storey[0] if scheme_by_storey else None
            zones = european_building_layout_to_zone_specs(
                building_layout,
                building_id=row["building_id"],
                height_m=FLOOR_TO_FLOOR_M,
            )
            idf_reroute_divergence_count += 1
        else:
            outcome = "FALLBACK_PENDING_LAYOUT"
            fb_reason = building_layout.fallback_reason
            best_effort_failed_checks = []
            if fb_reason == "NARROW_FOOTPRINT_LT_8M":
                narrow_fallback_count += 1
            elif fb_reason == DWELLING_DENSITY_REFUSAL_TOKEN:
                density_exceeded_count += 1
            elif fb_reason == "REGULARIZATION_AREA_DELTA_GT_2PCT":
                regularization_fallback_count += 1
            else:
                other_fallback_count += 1
            scheme_by_storey = []
            scheme_str = None
            zones = []

        # Group zones by floor index. A group's storey_span > 1 means trailing
        # storeys were absorbed (a single dwelling spanning multiple floors,
        # e.g. a multi-storey SFH/TH) -- the group's zones extrude across the
        # whole span as one tall zone, so every physical storey in the span
        # gets its own "floors" entry (for the viewer's per-floor slicing)
        # pointing at the SAME zone geometry/name.
        floors_list: list[dict[str, Any]] = []
        circulation_area_total_m2 = 0.0
        habitability_rotation_count = 0
        habitability_downgrade_count = 0
        circulation_outside_band = False
        has_unconditioned_core = False
        gross_footprint_area_m2 = round(float(footprint.area), 4)
        conditioned_floor_area_m2 = gross_footprint_area_m2
        if idf_reroute_divergence:
            # Ground truth per rule 3: the IDF's own extruded (whole) zone
            # areas, never the ruled-route sums this building never actually
            # simulated.
            gross_footprint_area_m2 = round(idf_plan.gross_area_m2, 4)
            conditioned_floor_area_m2 = round(idf_plan.conditioned_area_m2, 4)
        elif building_layout.dwelling_layout_emitted:
            gross_sum, conditioned_sum = european_building_layout_area_summary(building_layout)
            gross_footprint_area_m2 = round(gross_sum, 4)
            conditioned_floor_area_m2 = round(conditioned_sum, 4)

        if building_layout.dwelling_layout_emitted:
            # D-EU-62: also runs when idf_reroute_divergence is True (the
            # ruled layout's own geometry populates floors[] for the viewer
            # even though this building's IDF was rerouted); the area totals
            # above stay the IDF's ground truth in that case regardless.
            for group in building_layout.storey_groups:
                storey_layout = group.layout
                g_zones = []
                for z in zones:
                    if z["name"].startswith(f"{row['building_id']}_F{group.start_storey_index}_dwelling_"):
                        poly = orient(z["floor_polygon"], sign=ZONE_WINDING_SIGN)
                        g_zones.append({
                            "name": z["name"],
                            "coords_m": list(poly.exterior.coords)[:-1],
                            "z_floor": z["z_floor"],
                            "z_ceiling": z["z_ceiling"],
                        })
                circulation_area_total_m2 += storey_layout.circulation_area_m2
                circulation_outside_band = circulation_outside_band or storey_layout.circulation_outside_ruled_absolute_band
                habitability_rotation_count += int(storey_layout.habitability_rotation_applied)
                habitability_downgrade_count += int(storey_layout.habitability_downgrade_applied)
                circ_ring = None
                storey_has_core = storey_layout.circulation_polygon is not None
                has_unconditioned_core = has_unconditioned_core or storey_has_core
                if storey_layout.circulation_polygon is not None:
                    circ_source = storey_layout.circulation_polygon
                    if circ_source.geom_type == "MultiPolygon":
                        # P01c 2026-09-01: a scheme's circulation remainder can
                        # come back split into disjoint pieces (e.g. a
                        # courtyard perimeter band's two corridor segments) --
                        # take the largest by area for display, same choice
                        # made in _stabilize_ring_coords for this class of
                        # non-simple circulation ring.
                        circ_source = max(circ_source.geoms, key=lambda g: g.area)
                    circ_poly = orient(circ_source, sign=ZONE_WINDING_SIGN)
                    circ_ring = list(circ_poly.exterior.coords)[:-1]
                for s_idx in range(group.start_storey_index, group.start_storey_index + group.storey_span):
                    floors_list.append({
                        "storey_index": s_idx,
                        "z_floor_m": s_idx * FLOOR_TO_FLOOR_M,
                        "dwelling_count": len(g_zones),
                        "zones": g_zones,
                        "circulation": circ_ring,
                        "scheme": storey_layout.scheme,
                        "grid": storey_layout.grid,
                        "storey_span": group.storey_span,
                        "circulation_area_m2": round(storey_layout.circulation_area_m2, 4),
                        "circulation_pct_of_plate": round(storey_layout.circulation_pct_of_plate, 4),
                        "circulation_outside_ruled_absolute_band": storey_layout.circulation_outside_ruled_absolute_band,
                        "habitability_rotation_applied": storey_layout.habitability_rotation_applied,
                        "habitability_downgrade_applied": storey_layout.habitability_downgrade_applied,
                        "has_unconditioned_core": storey_has_core,
                    })

        outcome_counter[outcome] += 1
        fallback_counter[fb_reason or "EMITTED"] += 1
        updated_outcomes[bid] = outcome
        for scheme_name in scheme_by_storey:
            scheme_histogram[scheme_name] += 1
        habitability_rotation_total += habitability_rotation_count
        habitability_downgrade_total += habitability_downgrade_count
        if circulation_outside_band:
            circulation_outside_band_count += 1

        # T03 disclosure: measured independently of which internal route the
        # building actually took (ruled grid, gallery, L-shape wing, or
        # secondary fallback), on the raw observed footprint.
        try:
            regularization = regularize_footprint_orthogonal(footprint)
            regularization_deltas.append(float(regularization.plate_area_delta_fraction))
            regularization_record = {
                "plate_area_raw_m2": round(regularization.plate_area_raw_m2, 4),
                "plate_area_regularized_m2": round(regularization.plate_area_regularized_m2, 4),
                "plate_area_delta_fraction": round(regularization.plate_area_delta_fraction, 6),
                "vertices_raw": regularization.vertices_raw,
                "vertices_regularized": regularization.vertices_regularized,
            }
        except ValueError:
            regularization_record = None

        # T09(b): facade/audit stats describe the ruled route this building
        # never actually simulated once rerouted -- never publish them
        # alongside the IDF's own (whole-zone) truth.
        combined_facade = tuple(
            length for group in building_layout.storey_groups for length in group.layout.facade_contact_lengths_m
        ) if not idf_reroute_divergence else ()
        combined_audit_passed = (
            all(
                group.layout.partition_audit is not None and group.layout.partition_audit.passed
                for group in building_layout.storey_groups
            ) if building_layout.dwelling_layout_emitted else None
        ) if not idf_reroute_divergence else None
        combined_area_error = (
            (
                max((g.layout.partition_audit.area_error_fraction for g in building_layout.storey_groups if g.layout.partition_audit), default=0.0)
                if building_layout.dwelling_layout_emitted else None
            ) if not idf_reroute_divergence else None
        )
        # 4J ask 1 of 2026-09-08 (director amendment 13:05): report-only
        # fields beside `passed`/`area_error_fraction` -- never a gate.
        _storey_audits = [
            g.layout.partition_audit for g in building_layout.storey_groups if g.layout.partition_audit
        ]
        combined_failures = (
            (sorted({failure for a in _storey_audits for failure in a.failures}) if building_layout.dwelling_layout_emitted else None)
            if not idf_reroute_divergence else None
        )
        combined_gap_area = (
            (round(max((a.gap_area_m2 for a in _storey_audits), default=0.0), 6) if building_layout.dwelling_layout_emitted else None)
            if not idf_reroute_divergence else None
        )
        combined_overlap_area = (
            (round(max((a.overlap_area_m2 for a in _storey_audits), default=0.0), 6) if building_layout.dwelling_layout_emitted else None)
            if not idf_reroute_divergence else None
        )
        combined_outside_area = (
            (round(max((a.outside_area_m2 for a in _storey_audits), default=0.0), 6) if building_layout.dwelling_layout_emitted else None)
            if not idf_reroute_divergence else None
        )

        sidecar = {
            "building_id": str(row["building_id"]),
            "archetype_id": str(row["archetype_id"]),
            "building_type": str(row["building_type"]),
            "geometry_outcome": outcome,
            # D-EU-62: loud per-building flag so no downstream layer can
            # read a rerouted building's floors[] as a simulated/certified
            # plan -- always present, true only for the reroute outcome.
            "idf_reroute_divergence": idf_reroute_divergence,
            "scheme": scheme_str,
            "scheme_by_storey": scheme_by_storey,
            "storeys": n_storey,
            "dwellings_total": dwellings_val,
            "units_per_floor": allocation.units_per_floor,
            "observed_max_per_floor": building_layout.observed_max_per_floor,
            # D-EU-39 §3 / EU-15 T05: true wherever at least one storey
            # carved and emitted the unconditioned stair core / corridor
            # spine (see floors[].has_unconditioned_core for the per-storey
            # detail); this always reflects the emitted geometry, never the
            # allocate_european_dwellings density heuristic.
            "has_unconditioned_core": has_unconditioned_core,
            "gross_footprint_area_m2": gross_footprint_area_m2,
            "conditioned_floor_area_m2": conditioned_floor_area_m2,
            "circulation_area_m2_total": round(circulation_area_total_m2, 4),
            "circulation_outside_ruled_absolute_band": circulation_outside_band,
            "habitability_rotation_applied_count": habitability_rotation_count,
            "habitability_downgrade_applied_count": habitability_downgrade_count,
            "floor_to_floor_m": FLOOR_TO_FLOOR_M,
            "dwelling_count_provenance": provenance_token,
            # EU-14B T03: only IT-BOL-GALVANI2 rows carry this (set by
            # scripts/run_eu_s2_district_campaign.py::_it_rows) -- Bologna is
            # the only district where both the construction period and the
            # dwelling count are imputed, and a reader of its pop-up must see
            # both tags without opening a document.
            "construction_period_provenance": row.get("construction_period_provenance") or None,
            "floors": floors_list,
            "facade_contact_lengths_m": [round(x, 4) for x in combined_facade],
            "partition_audit": {
                "passed": combined_audit_passed,
                "area_error_fraction": combined_area_error,
                "failures": combined_failures,
                "gap_area_m2": combined_gap_area,
                "overlap_area_m2": combined_overlap_area,
                "outside_area_m2": combined_outside_area,
            } if building_layout.dwelling_layout_emitted else None,
            "fallback_reason": fb_reason,
            # D-EU-111 (T02): non-empty only for a best-effort emission -- the
            # shape checks (C6/C10/C11) it failed, parsed from `fb_reason`, so
            # the FAIL verdict stays visible even though the building drew.
            "best_effort_failed_checks": best_effort_failed_checks,
            "crs": cfg["crs"],
            "regularization": regularization_record,
        }

        # Write sidecar JSON safely
        rel_sidecar_file = f"{bid}.json"
        sidecar_out_path = layouts_dir / rel_sidecar_file
        sidecar_out_path.parent.mkdir(parents=True, exist_ok=True)
        sidecar_out_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")

        repo_rel_path = str((dist_dir / "layouts" / rel_sidecar_file).relative_to(REPO_ROOT)).replace("\\", "/")
        layout_paths[bid] = repo_rel_path

    # EU-14B T01: only the columns this emitter owns (geometry_outcome,
    # layout_json) are ever written, only for the building_ids it actually
    # recomputed this run; row count, building_id set and every previously
    # non-blank cell elsewhere are asserted unchanged before anything is
    # written to disk. See safe_update_manifest_columns above.
    if population_manifest is not None:
        print(f"[{district}] --population-manifest given: skipping manifest write-back to {manifest_path}")
    else:
        manifest_df = safe_update_manifest_columns(
            manifest_path,
            column_updates={
                "geometry_outcome": dict(updated_outcomes),
                "layout_json": dict(layout_paths),
            },
        )
        print(f"[{district}] Updated manifest {manifest_path} ({len(manifest_df)} rows)")
    print(f"[{district}] Written {len(layout_paths)} layout side-cars to {layouts_dir}")
    print(f"[{district}] Outcomes: {dict(outcome_counter)}")
    print(f"[{district}] Fallback reasons: {dict(fallback_counter)}")
    print(f"[{district}] Strip-cutter fallback_reason census: {dict(strip_cutter_reason_counter)}")

    n_res_total = len(gdf)
    not_simulated_count = n_res_total - len(manifest_df)

    return {
        "district": district,
        "population_total": n_res_total,
        "population_simulated": len(manifest_df),
        "observed_emitted": observed_emitted_count,
        "imputed_emitted": imputed_emitted_count,
        "narrow_fallback": narrow_fallback_count,
        "density_exceeded_gt_8": density_exceeded_count,
        "regularization_fallback": regularization_fallback_count,
        "other_fallback": other_fallback_count,
        "idf_reroute_divergence": idf_reroute_divergence_count,
        "not_simulated": not_simulated_count,
        "outcomes": dict(outcome_counter),
        "fallback_reasons": dict(fallback_counter),
        "scheme_histogram": dict(scheme_histogram),
        "strip_cutter_fallback_reason_census": dict(strip_cutter_reason_counter),
        "strip_cutter_building_count": sum(strip_cutter_reason_counter.values()),
        "regularization_area_delta_fraction": regularization_deltas,
        "circulation_outside_ruled_absolute_band_count": circulation_outside_band_count,
        "habitability_rotation_applied_total": habitability_rotation_total,
        "habitability_downgrade_applied_total": habitability_downgrade_total,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="EU-13/T09(b)/T10: emit dwelling-layout side-cars.")
    parser.add_argument("--district", action="append", choices=sorted(DISTRICTS), default=None)
    parser.add_argument(
        "--evidence-root",
        action="append",
        default=None,
        help="DISTRICT=path override (T10/T12: point at the EU-17 rebuild tree).",
    )
    parser.add_argument(
        "--population-manifest",
        action="append",
        default=None,
        help="DISTRICT=path override for the source of simulated_ids only "
             "(T07c/D-EU-114: re-emit against the full recut population "
             "instead of dist_dir's own manifest). Skips manifest write-back.",
    )
    args = parser.parse_args()

    roots: dict[str, Path] = {}
    for entry in args.evidence_root or []:
        district, _, path = entry.partition("=")
        roots[district] = Path(path)

    pop_manifests: dict[str, Path] = {}
    for entry in args.population_manifest or []:
        district, _, path = entry.partition("=")
        pop_manifests[district] = Path(path)

    targets = args.district if args.district else list(DISTRICTS)
    results = {}
    for district in targets:
        print(f"\n=== Emitting layout side-cars for {district} ===")
        results[district] = emit_layouts_for_district(
            district, roots.get(district), pop_manifests.get(district)
        )

    print("\n=== Summary of Layout Emission across all 4 districts ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
