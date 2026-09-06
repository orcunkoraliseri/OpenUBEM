"""EU-21 T01/T02 (`eu-nocore-interzone-rootcause`, 2026-09-04): storey-group
transition census and raw `find_mismatched_interzone_pairs` characterization.

CP-1 gated (plan `PLAN_eu-nocore-interzone-rootcause-2026-09-04.md`). This
script only characterizes -- it never edits `openubem/idf/surfaces.py`,
`openubem/geometry/european_nocore.py` or `scripts/eu21/01`-`08` (all
read-only, only their exported functions/data are called), and T02 never
acts on a reroute -- it captures `find_mismatched_interzone_pairs`'s raw
pre-gate output only and stops.

PLAN/CODE CONFLICT, reported at CP-1, not resolved here (hard rule 10):
Plan section 6 T01 "What" defines the diagnostic quantity in English as "the
number of times the per-floor dwelling count changes between consecutive
floors." Plan section 6 T01 "How" instead says to read it as
`len(storey_groups) - 1`. These are NOT the same quantity.
`generate_european_building_dwelling_layout`
(`european_residential.py:2686-2698`) appends one `EuropeanStoreyGroup` per
non-absorbed floor UNCONDITIONALLY -- it never merges two consecutive floors
into one group just because they share the same dwelling count; only the
`_layout_for` cache (line 2673-2684) reuses the same layout OBJECT across
equal-count floors, the `storey_groups` list itself still carries one entry
per floor. Verified empirically on a synthetic 4-storey building with
per-floor counts [3, 3, 2, 2]: 4 `storey_groups` are returned (span 1 each),
so `len(storey_groups) - 1 == 3`, while the number of times
`count[i] != count[i-1]` is 1. `len(storey_groups) - 1` is therefore
`n_floors - 1` for essentially every AB building regardless of whether any
dwelling count ever actually changes -- it does not test the mechanism plan
section 1 describes ("two floors with the SAME count reuse the identical
cached cut and stay perfectly aligned ... two floors with DIFFERENT counts
... get two independently computed calls to `cut_storey_nocore`").
Both quantities are computed and reported below as separate columns
(`n_transitions` = the literal `len(storey_groups)-1` "How" formula,
`n_dwelling_count_changes` = the "What"/section-1 semantic quantity).
Neither is treated as authoritative here; CP-1 decides. T02's sampling and
classification uses `n_dwelling_count_changes`, because `n_transitions`
(literal) is ~constant per floor-count and cannot usefully stratify a
sample or classify a mismatched pair as "crossing a transition" (almost
every inter-floor pair "crosses" a `len(storey_groups)-1`-style boundary by
construction).

Dependency decision 3 (plan section 4): floor_allocations are re-derived
from the same census inputs `scripts/eu21/10_engine_census.py` (T05a) used
-- EU-20's `morphology_census.csv` `storeys`/`dwellings_total` via
`load_universe()`, archetype_id="engine_census_T05a", building_type="AB" --
never from the IDF, and never from the district campaign's own
network-dependent TABULA mapping (`_it_rows` for Bologna makes live HTTP
calls to opendata.comune.bologna.it, forbidden by CLAUDE.md "No live-network
integration tests until section 5.3 is unblocked"). T02's zones are built
the same census-derived way for all four districts (never through
`run_eu_s2_district_campaign.py::_geometry`, which would trigger that
network call for Bologna) -- justified because `context` (the only thing
`_geometry`'s production pipeline adds that this script's zones do not) is
applied in `build_idf_for_building` at line 557, strictly AFTER the
`find_mismatched_interzone_pairs` call at line 516 this task observes, so it
cannot affect the result being captured.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util as ilu
import json
import pathlib
import random
import time

import pandas as pd
from shapely.geometry.polygon import orient

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.geometry.european_residential import (
    DWELLING_DENSITY_REFUSAL_TOKEN,
    RULED_GRID_MAX_DWELLINGS_PER_FLOOR,
    _stabilize_ring_coords,
    allocate_european_dwellings,
    european_building_layout_to_zone_specs,
    generate_european_building_dwelling_layout,
)
from openubem.idf.surfaces import (
    _get_floor_idx,
    extrude_geometry,
    find_mismatched_interzone_pairs,
)
from scripts.run_eu_s2_campaign import (
    FLOOR_TO_FLOOR_M,
    IDF_HEADER_TEMPLATE,
    SHADOW_CALCULATION_METHOD,
    SHADOW_CALCULATION_UPDATE_FREQUENCY_DAYS,
    SHADOW_CALCULATION_UPDATE_FREQUENCY_METHOD,
    WEATHER_PATH,
    ZONE_WINDING_SIGN,
    _has_near_duplicate_vertex_surfaces,
)
# T02c note: the coordinator's message and the plan doc's T02c "How" both say
# `_has_near_duplicate_vertex_surfaces` lives in `openubem/idf/surfaces.py` --
# it does not. `grep -rn "def _has_near_duplicate_vertex_surfaces"` finds it
# only at `scripts/run_eu_s2_campaign.py:94`. Imported from its actual
# location above; still a read-only import, not edited, so the substantive
# constraint holds regardless of the file named.

ROOT = pathlib.Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
CUTTER_PATH = ROOT / "scripts" / "eu21" / "07_nocore_tests.py"
EU11 = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
OUT_DIR = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "interzone_rootcause"
T01_CSV = OUT_DIR / "T01_transition_census_2026-09-04.csv"
T02_JSON = OUT_DIR / "T02_mismatch_detail_2026-09-04.json"
REFERENCE_ENGINE_CENSUS = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "engine_parity" / "engine_census_2026-09-03.json"

DISTRICTS = [
    "ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2",
]


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_census_universe():
    """Same loader T05a's own `_engine_status` used (`10_engine_census.py:36,58-62,115`):
    `07_nocore_tests.py`'s own re-export of `01_cut_group_plans.py::load_universe`.
    Read-only -- only the loader function is called, no cutting test harness runs."""
    m07 = _load_module("eu21_m11_m07_nocore_tests", str(CUTTER_PATH))
    geoms, rows, *_ = m07.load_universe()
    census_lookup = {}
    for r in rows:
        district = r["district"]
        bid = r["building_id"]
        storeys = max(1, int(float(r["storeys"])))
        dwellings_total = max(1, int(float(r["dwellings_total"])))
        census_lookup[(district, bid)] = (storeys, dwellings_total)
    return geoms, rows, census_lookup


def _floor_allocations_for(g, storeys, dwellings_total):
    return allocate_european_dwellings(
        archetype_id="engine_census_T05a", building_type="AB",
        n_apartment=dwellings_total, n_storey=storeys, plate_area_m2=float(g.area),
    )


def _classify(g, storeys, dwellings_total):
    allocation = _floor_allocations_for(g, storeys, dwellings_total)
    counts = [fa.dwelling_count for fa in allocation.floor_allocations]
    building_layout = generate_european_building_dwelling_layout(g, floor_allocations=allocation.floor_allocations)
    n_count_changes = sum(1 for i in range(1, len(counts)) if counts[i] != counts[i - 1])
    if not building_layout.dwelling_layout_emitted:
        engine_status = (
            "REFUSED_K_GT_12" if building_layout.fallback_reason == DWELLING_DENSITY_REFUSAL_TOKEN else "FALLBACK"
        )
        return {
            "engine_status": engine_status, "n_groups": None, "n_transitions": None,
            "n_dwelling_count_changes": n_count_changes, "counts": counts,
            "building_layout": None, "allocation": allocation,
        }
    n_groups = len(building_layout.storey_groups)
    return {
        "engine_status": "EMITTED", "n_groups": n_groups, "n_transitions": n_groups - 1,
        "n_dwelling_count_changes": n_count_changes, "counts": counts,
        "building_layout": building_layout, "allocation": allocation,
    }


def census_transitions():
    """T01: one row per census building, every one of the 2,544 EU-20
    `morphology_census.csv` rows (matches T05a's own universe, `FINDING 246`),
    joined against each district's `prepared_buildings.csv` `geometry_outcome`.
    """
    t0 = time.time()
    geoms, rows, census_lookup = _load_census_universe()

    outcome_by_key: dict[tuple[str, str], str] = {}
    for district in DISTRICTS:
        csv_path = EU11 / f"{district}_nocore_2026-09-03" / "prepared_buildings.csv"
        df = pd.read_csv(csv_path, dtype=str)
        for _, r in df.iterrows():
            outcome_by_key[(district, r["building_id"])] = r["geometry_outcome"]

    records = []
    engine_counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    n_floor_mismatches = 0
    n_missing_geom = 0
    for r in rows:
        district = r["district"]
        bid = r["building_id"]
        key = (district, bid)
        g = geoms.get(key)
        if g is None:
            n_missing_geom += 1
            continue
        storeys, dwellings_total = census_lookup[key]
        result = _classify(g, storeys, dwellings_total)
        if len(result["counts"]) != storeys:
            n_floor_mismatches += 1
        engine_counts[district][result["engine_status"]] += 1
        records.append({
            "building_id": bid, "district": district, "n_floors": storeys,
            "dwellings_total": dwellings_total,
            "n_groups": result["n_groups"], "n_transitions": result["n_transitions"],
            "n_dwelling_count_changes": result["n_dwelling_count_changes"],
            "engine_status": result["engine_status"],
            "geometry_outcome": outcome_by_key.get(key, ""),
        })

    df_out = pd.DataFrame.from_records(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(T01_CSV, index=False)

    ref = json.loads(REFERENCE_ENGINE_CENSUS.read_text(encoding="utf-8"))
    sanity_engine_status = {}
    all_match = True
    for district in DISTRICTS:
        mine = engine_counts[district]
        theirs = ref["districts"][district]
        row_match = (
            mine.get("EMITTED", 0) == theirs["EMITTED"]
            and mine.get("REFUSED_K_GT_12", 0) == theirs["REFUSED_K_GT_12"]
            and mine.get("FALLBACK", 0) == theirs["FALLBACK"]
        )
        all_match = all_match and row_match
        sanity_engine_status[district] = {
            "mine": {"EMITTED": mine.get("EMITTED", 0), "REFUSED_K_GT_12": mine.get("REFUSED_K_GT_12", 0), "FALLBACK": mine.get("FALLBACK", 0)},
            "t05a_engine_census_2026-09-03": {"EMITTED": theirs["EMITTED"], "REFUSED_K_GT_12": theirs["REFUSED_K_GT_12"], "FALLBACK": theirs["FALLBACK"]},
            "match": row_match,
        }
    sanity_engine_status["fleet_match"] = all_match
    sanity_floor_count = {"n_floor_mismatches": n_floor_mismatches, "n_missing_geometry": n_missing_geom, "total_rows": len(records)}

    wall_time_s = round(time.time() - t0, 1)
    return df_out, sanity_engine_status, sanity_floor_count, wall_time_s


def _reroute_table(df_out: pd.DataFrame, column: str):
    fam = df_out[df_out["geometry_outcome"].astype(str).str.startswith("DWELLING_LAYOUT_EMITTED", na=False)].copy()
    fam["rerouted"] = fam["geometry_outcome"] == "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"
    pooled = fam.groupby(column)["rerouted"].agg(["sum", "count"])
    pooled["rate"] = pooled["sum"] / pooled["count"]
    per_district = fam.groupby(["district", column])["rerouted"].agg(["sum", "count"])
    per_district["rate"] = per_district["sum"] / per_district["count"]
    zero_vs_nonzero = fam.assign(bucket=(fam[column] > 0)).groupby("bucket")["rerouted"].agg(["sum", "count"])
    zero_vs_nonzero["rate"] = zero_vs_nonzero["sum"] / zero_vs_nonzero["count"]
    return pooled, per_district, zero_vs_nonzero, len(fam), int(fam["rerouted"].sum())


def _stem(building_id: str) -> str:
    return hashlib.sha256(str(building_id).encode()).hexdigest()[:16]


def _build_zones(g, storeys, dwellings_total, stem):
    allocation = _floor_allocations_for(g, storeys, dwellings_total)
    building_layout = generate_european_building_dwelling_layout(g, floor_allocations=allocation.floor_allocations)
    if not building_layout.dwelling_layout_emitted:
        return None, None, None
    zones = european_building_layout_to_zone_specs(building_layout, building_id=stem, height_m=FLOOR_TO_FLOOR_M)
    for zone in zones:
        poly = orient(zone["floor_polygon"], sign=ZONE_WINDING_SIGN)
        zone["floor_polygon"] = poly
        zone["coords_m"] = _stabilize_ring_coords(poly)
    counts = [fa.dwelling_count for fa in allocation.floor_allocations]
    return zones, building_layout, counts


_IDD_SET = False


def _ensure_idd():
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


def _extrude_and_find_mismatches(zones, stem, run_dir):
    """Mirrors `build_idf_for_building` (`scripts/run_eu_s2_campaign.py:442-485,516`)
    up to and including the raw `find_mismatched_interzone_pairs` call -- never
    executes the reroute branch (lines 517-556), observe-only per T02's `How`.
    `context` is intentionally passed as `[]`: `apply_adiabatic_party_walls` (the
    only consumer of `context` inside `build_idf_for_building`) runs at line 557,
    strictly after the line-516 call this task captures, so it cannot change the
    result. Shared by T02 (`_probe_building`, census-derived zones) and T02b
    (`t02b_real_geometry_diff`, real production zones) -- identical IDF assembly,
    different zone source.
    """
    from geomeppy import IDF
    _ensure_idd()

    with WEATHER_PATH.open(encoding="utf-8", errors="replace") as stream:
        location_fields = stream.readline().strip().split(",")
    city, _state, _country = location_fields[1], location_fields[2], location_fields[3]
    latitude, longitude, time_zone, elevation = (float(v) for v in location_fields[6:10])

    run_dir.mkdir(parents=True, exist_ok=True)
    idf_path = run_dir / f"{stem}.idf"
    idf_path.write_text(
        IDF_HEADER_TEMPLATE.format(
            city=city, latitude=latitude, longitude=longitude, time_zone=time_zone, elevation=elevation,
            shadow_method=SHADOW_CALCULATION_METHOD,
            shadow_update_method=SHADOW_CALCULATION_UPDATE_FREQUENCY_METHOD,
            shadow_update_days=SHADOW_CALCULATION_UPDATE_FREQUENCY_DAYS,
        ),
        encoding="utf-8",
    )
    idf = IDF(str(idf_path))
    extrude_geometry(idf, zones, [])
    mismatched = find_mismatched_interzone_pairs(idf)
    return idf, mismatched


def _probe_building(g, storeys, dwellings_total, stem, run_dir):
    zones, building_layout, counts = _build_zones(g, storeys, dwellings_total, stem)
    if zones is None:
        return None

    idf, mismatched = _extrude_and_find_mismatches(zones, stem, run_dir)

    pairs_detail = []
    transition_floor_indices = {i for i in range(1, len(counts)) if counts[i] != counts[i - 1]}
    for surf_name, partner_name in mismatched:
        s1 = idf.getobject("BUILDINGSURFACE:DETAILED", surf_name)
        s2 = idf.getobject("BUILDINGSURFACE:DETAILED", partner_name)
        f1 = _get_floor_idx(s1.Zone_Name) if s1 is not None else None
        f2 = _get_floor_idx(s2.Zone_Name) if s2 is not None else None
        same_floor = f1 is not None and f2 is not None and f1 == f2
        crosses_transition = False
        if f1 is not None and f2 is not None and f1 != f2:
            lo, hi = sorted((f1, f2))
            crosses_transition = any(lo < t <= hi for t in transition_floor_indices)
        pairs_detail.append({
            "surf": surf_name, "partner": partner_name, "floor_a": f1, "floor_b": f2,
            "same_floor": same_floor, "crosses_dwelling_count_change_transition": crosses_transition,
        })

    return {
        "counts": counts, "n_dwelling_count_changes": len(transition_floor_indices),
        "transition_floor_indices": sorted(transition_floor_indices),
        "n_mismatched_pairs": len(mismatched), "pairs": pairs_detail,
    }


def sample_and_probe(df_out: pd.DataFrame, per_cell: int = 10, seed: int = 20260904):
    """T02: stratified sample, rebuilt locally, `find_mismatched_interzone_pairs`
    captured pre-gate for every sampled building (including clean ones)."""
    geoms, _rows, census_lookup = _load_census_universe()

    fam = df_out[df_out["geometry_outcome"].astype(str).str.startswith("DWELLING_LAYOUT_EMITTED", na=False)].copy()
    fam["rerouted"] = fam["geometry_outcome"] == "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"
    fam["has_transition"] = fam["n_dwelling_count_changes"] > 0

    cells = {
        "reroute_transitions": fam[fam.rerouted & fam.has_transition],
        "reroute_no_transitions": fam[fam.rerouted & ~fam.has_transition],
        "real_transitions": fam[~fam.rerouted & fam.has_transition],
        "real_no_transitions": fam[~fam.rerouted & ~fam.has_transition],
    }
    cell_sizes = {name: len(c) for name, c in cells.items()}

    sample_rows = []
    for name, cell_df in cells.items():
        n = min(per_cell, len(cell_df))
        if n == 0:
            continue
        picked = cell_df.sample(n=n, random_state=seed)
        for _, r in picked.iterrows():
            sample_rows.append({**r.to_dict(), "stratum": name})

    idf_root = OUT_DIR / "t02_idfs"
    sample_detail = []
    label_agreement = {"agree": 0, "disagree": 0}
    for srow in sample_rows:
        district = srow["district"]
        bid = srow["building_id"]
        storeys, dwellings_total = census_lookup[(district, bid)]
        g = geoms[(district, bid)]
        stem = _stem(bid)
        run_dir = idf_root / district / stem
        probe = _probe_building(g, storeys, dwellings_total, stem, run_dir)
        if probe is None:
            sample_detail.append({
                "district": district, "building_id": bid, "stratum": srow["stratum"],
                "geometry_outcome": srow["geometry_outcome"], "engine_status": srow["engine_status"],
                "note": "dwelling_layout_emitted False on rebuild -- census/T01 said EMITTED, conflict",
            })
            continue
        rerouted_label = bool(srow["rerouted"])
        locally_mismatched = probe["n_mismatched_pairs"] > 0
        if rerouted_label == locally_mismatched:
            label_agreement["agree"] += 1
        else:
            label_agreement["disagree"] += 1
        sample_detail.append({
            "district": district, "building_id": bid, "stratum": srow["stratum"],
            "geometry_outcome": srow["geometry_outcome"], "rerouted_label": rerouted_label,
            "n_floors": int(srow["n_floors"]), "n_transitions_literal": (None if pd.isna(srow["n_transitions"]) else int(srow["n_transitions"])),
            **probe,
            "locally_mismatched": locally_mismatched,
            "label_agrees_with_local_rebuild": rerouted_label == locally_mismatched,
        })

    total_pairs = sum(d.get("n_mismatched_pairs", 0) for d in sample_detail)
    crossing_pairs = sum(
        sum(1 for p in d.get("pairs", []) if p["crosses_dwelling_count_change_transition"])
        for d in sample_detail
    )
    within_group_pairs = total_pairs - crossing_pairs
    zero_transition_with_mismatch = [
        d["building_id"] for d in sample_detail
        if d.get("n_dwelling_count_changes") == 0 and d.get("n_mismatched_pairs", 0) > 0
    ]

    report = {
        "cell_sizes_available": cell_sizes,
        "cell_sizes_sampled": {name: sum(1 for r in sample_rows if r["stratum"] == name) for name in cells},
        "label_agreement_local_rebuild_vs_prepared_csv": label_agreement,
        "aggregate": {
            "total_mismatched_pairs_in_sample": total_pairs,
            "crossing_dwelling_count_change_transition": crossing_pairs,
            "within_one_group": within_group_pairs,
            "crossing_fraction": (crossing_pairs / total_pairs) if total_pairs else None,
            "zero_transition_buildings_still_mismatched": zero_transition_with_mismatch,
            "zero_transition_buildings_still_mismatched_count": len(zero_transition_with_mismatch),
        },
        "sample": sample_detail,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    T02_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


T02B_JSON = OUT_DIR / "T02b_real_geometry_diff_2026-09-04.json"
DISTRICTS_T02B = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS"]


def _district_rows_for_mapping(district: str):
    """Real production mapping rows for one network-safe district -- the exact
    functions `run_eu_s2_district_campaign.py::prepare` (lines 346-357, 369-377)
    calls before `_geometry`, called directly for just the buildings T02b needs
    rather than running the whole district's `prepare()`. Bologna's `_it_rows`
    is never imported (live HTTP to opendata.comune.bologna.it, forbidden)."""
    import geopandas as gpd
    from scripts.run_eu_s2_district_campaign import DISTRICTS as DC, _gb_rows, _mapped_rows

    cfg = DC[district]
    manifest = ROOT / "openubem" / "outputs" / "eu02" / district / "02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    if str(gdf.crs) != cfg["crs"]:
        raise ValueError(f"Manifest CRS is {gdf.crs}, expected {cfg['crs']}")
    records = json.loads(
        (ROOT / "openubem" / "data" / "construction" / f"tabula_archetypes_{cfg['country'].lower()}.json").read_text(encoding="utf-8")
    )["records"]
    if district == "GB-LDN-STDUNSTANS":
        rows, _exclusions = _gb_rows(gdf, records)
    else:
        rows, _exclusions = _mapped_rows(district, gdf, records)
    return rows, records


def _pick_t02b_sample(n_per_bucket: int = 8, seed: int = 20260904) -> pd.DataFrame:
    """The exact 16-building selection T02b used -- factored out so T02c can
    reuse the identical (deterministic, same seed) sample rather than risk a
    second, differently-selected sample."""
    df_t01 = pd.read_csv(T01_CSV)
    fam = df_t01[
        df_t01["district"].isin(DISTRICTS_T02B)
        & df_t01["geometry_outcome"].astype(str).str.startswith("DWELLING_LAYOUT_EMITTED", na=False)
    ].copy()
    fam["rerouted"] = fam["geometry_outcome"] == "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"
    reroute_pool = fam[fam.rerouted]
    clean_pool = fam[~fam.rerouted]
    n = min(n_per_bucket, len(reroute_pool), len(clean_pool))
    return pd.concat([
        reroute_pool.sample(n=n, random_state=seed),
        clean_pool.sample(n=n, random_state=seed),
    ])


def t02b_real_geometry_diff(n_per_bucket: int = 8, seed: int = 20260904):
    """T02b: pick real-labelled buildings (reroute + clean) from the three
    network-safe districts, run the REAL `_geometry()` production path (not the
    census reconstruction), diff its `floor_allocations` (read back from the
    real per-floor `_dwelling_` zone counts, since `_geometry` does not return
    `floor_allocations` directly) against T01/T02's census-derived
    reconstruction for the same `building_id`, and report the corrected
    `find_mismatched_interzone_pairs` label agreement.
    """
    from scripts.run_eu_s2_district_campaign import _geometry

    picked = _pick_t02b_sample(n_per_bucket, seed)

    geoms, _rows, census_lookup = _load_census_universe()
    mapping_cache = {d: _district_rows_for_mapping(d) for d in DISTRICTS_T02B}

    results = []
    for _, prow in picked.iterrows():
        district = prow["district"]
        bid = prow["building_id"]
        rows_by_id = {r["building_id"]: r for r in mapping_cache[district][0]}
        records = mapping_cache[district][1]
        raw = rows_by_id.get(bid)
        rerouted_label = bool(prow["rerouted"])
        if raw is None:
            results.append({
                "district": district, "building_id": bid, "rerouted_label": rerouted_label,
                "note": "NOT_FOUND_IN_REAL_MAPPING_ROWS",
            })
            continue

        row = pd.Series(raw)
        stem = _stem(bid)
        model_row = row.copy()
        model_row["building_id"] = stem
        try:
            zones, outcome = _geometry(model_row, records)
        except Exception as exc:
            results.append({
                "district": district, "building_id": bid, "rerouted_label": rerouted_label,
                "note": f"_geometry raised {type(exc).__name__}: {exc}",
            })
            continue

        real_counts_by_floor: dict[int, int] = {}
        for z in zones:
            if z.get("mode") != "european_dwelling_layout" or "_dwelling_" not in z["name"]:
                continue
            fidx = _get_floor_idx(z["name"])
            real_counts_by_floor[fidx] = real_counts_by_floor.get(fidx, 0) + 1
        real_counts = [real_counts_by_floor[i] for i in sorted(real_counts_by_floor)]

        storeys, dwellings_total = census_lookup.get((district, bid), (None, None))
        recon_counts = None
        if storeys is not None:
            g = geoms.get((district, bid))
            if g is not None:
                recon_allocation = _floor_allocations_for(g, storeys, dwellings_total)
                recon_counts = [fa.dwelling_count for fa in recon_allocation.floor_allocations]

        run_dir = OUT_DIR / "t02b_idfs" / district / stem
        try:
            idf, mismatched = _extrude_and_find_mismatches(zones, stem, run_dir)
        except Exception as exc:
            results.append({
                "district": district, "building_id": bid, "rerouted_label": rerouted_label,
                "real_floor_dwelling_counts": real_counts, "reconstructed_floor_dwelling_counts": recon_counts,
                "note": f"extrude/find_mismatched raised {type(exc).__name__}: {exc}",
            })
            continue
        locally_mismatched = len(mismatched) > 0

        results.append({
            "district": district, "building_id": bid, "stem": stem,
            "geometry_outcome_real": prow["geometry_outcome"], "rerouted_label": rerouted_label,
            "geometry_outcome_freshly_computed_pre_reroute": outcome,
            "storeys_census": storeys, "dwellings_total_census": dwellings_total,
            "real_floor_dwelling_counts": real_counts,
            "reconstructed_floor_dwelling_counts": recon_counts,
            "counts_identical": (real_counts == recon_counts),
            "n_mismatched_pairs": len(mismatched), "locally_mismatched": locally_mismatched,
            "label_agrees": locally_mismatched == rerouted_label,
        })

    n_agree = sum(1 for r in results if r.get("label_agrees") is True)
    n_disagree = sum(1 for r in results if r.get("label_agrees") is False)
    n_errors = sum(1 for r in results if "note" in r)
    n_counts_identical = sum(1 for r in results if r.get("counts_identical") is True)
    n_counts_diff = sum(1 for r in results if r.get("counts_identical") is False)

    report = {
        "n_sampled": len(results), "n_errors": n_errors,
        "label_agreement": {"agree": n_agree, "disagree": n_disagree},
        "floor_allocations_diff": {"identical": n_counts_identical, "different": n_counts_diff},
        "detail": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    T02B_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


T02C_JSON = OUT_DIR / "T02c_at_risk_probe_2026-09-04.json"


def t02c_at_risk_probe(n_per_bucket: int = 8, seed: int = 20260904):
    """T02c: re-probe the SAME T02b 16-building real-geometry sample
    (`_pick_t02b_sample`, identical seed/bucket size) and this time also
    capture `_has_near_duplicate_vertex_surfaces(idf)` -- the second half of
    the real `at_risk = mismatched or _has_near_duplicate_vertex_surfaces(idf)`
    gate (`scripts/run_eu_s2_campaign.py:517`), which T02/T02b never checked.
    T02b did not persist the extruded `idf` objects (only the header text was
    written to `t02b_idfs/`, `extrude_geometry` was never followed by
    `idf.saveas`), so this rebuilds the same 16 in-process -- the plan's own
    accepted fallback ("if reusing the in-memory objects is impractical,
    rebuild only these 16").
    """
    from scripts.run_eu_s2_district_campaign import _geometry

    picked = _pick_t02b_sample(n_per_bucket, seed)
    mapping_cache = {d: _district_rows_for_mapping(d) for d in DISTRICTS_T02B}

    results = []
    for _, prow in picked.iterrows():
        district = prow["district"]
        bid = prow["building_id"]
        rows_by_id = {r["building_id"]: r for r in mapping_cache[district][0]}
        records = mapping_cache[district][1]
        raw = rows_by_id.get(bid)
        rerouted_label = bool(prow["rerouted"])
        real_geometry_outcome = prow["geometry_outcome"]
        if raw is None:
            results.append({
                "district": district, "building_id": bid, "rerouted_label": rerouted_label,
                "note": "NOT_FOUND_IN_REAL_MAPPING_ROWS",
            })
            continue

        row = pd.Series(raw)
        stem = _stem(bid)
        model_row = row.copy()
        model_row["building_id"] = stem
        try:
            zones, _outcome = _geometry(model_row, records)
        except Exception as exc:
            results.append({
                "district": district, "building_id": bid, "rerouted_label": rerouted_label,
                "note": f"_geometry raised {type(exc).__name__}: {exc}",
            })
            continue

        run_dir = OUT_DIR / "t02c_idfs" / district / stem
        try:
            idf, mismatched = _extrude_and_find_mismatches(zones, stem, run_dir)
            near_duplicate = _has_near_duplicate_vertex_surfaces(idf)
        except Exception as exc:
            results.append({
                "district": district, "building_id": bid, "rerouted_label": rerouted_label,
                "note": f"extrude/probe raised {type(exc).__name__}: {exc}",
            })
            continue

        at_risk = bool(mismatched) or bool(near_duplicate)
        results.append({
            "district": district, "building_id": bid, "stem": stem,
            "geometry_outcome_real": real_geometry_outcome, "rerouted_label": rerouted_label,
            "mismatched": bool(mismatched), "near_duplicate_vertex": bool(near_duplicate),
            "at_risk": at_risk, "at_risk_agrees_with_real_label": at_risk == rerouted_label,
        })

    reroute_rows = [r for r in results if r.get("rerouted_label") is True and "note" not in r]
    clean_rows = [r for r in results if r.get("rerouted_label") is False and "note" not in r]
    n_reroute_now_at_risk = sum(1 for r in reroute_rows if r["at_risk"])
    n_clean_stays_not_at_risk = sum(1 for r in clean_rows if not r["at_risk"])
    n_errors = sum(1 for r in results if "note" in r)

    report = {
        "n_sampled": len(results), "n_errors": n_errors,
        "n_reroute_labelled": len(reroute_rows), "n_clean_labelled": len(clean_rows),
        "reroute_now_at_risk": f"{n_reroute_now_at_risk}/{len(reroute_rows)}",
        "clean_stays_not_at_risk": f"{n_clean_stays_not_at_risk}/{len(clean_rows)}",
        "detail": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    T02C_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--t01-only", action="store_true")
    parser.add_argument("--t02-only", action="store_true")
    parser.add_argument("--t02b-only", action="store_true")
    parser.add_argument("--t02c-only", action="store_true")
    args = parser.parse_args()

    if args.t02c_only:
        report = t02c_at_risk_probe()
        print("T02c n_sampled/n_errors:", report["n_sampled"], report["n_errors"])
        print("T02c reroute_now_at_risk:", report["reroute_now_at_risk"])
        print("T02c clean_stays_not_at_risk:", report["clean_stays_not_at_risk"])
        for r in report["detail"]:
            print(" ", r.get("district"), r.get("building_id"), "rerouted_label=", r.get("rerouted_label"),
                  "mismatched=", r.get("mismatched"), "near_dup=", r.get("near_duplicate_vertex"),
                  "at_risk=", r.get("at_risk"), "agrees=", r.get("at_risk_agrees_with_real_label"),
                  "note=", r.get("note"))
        return

    if args.t02b_only:
        report = t02b_real_geometry_diff()
        print("T02b n_sampled/n_errors:", report["n_sampled"], report["n_errors"])
        print("T02b label_agreement:", report["label_agreement"])
        print("T02b floor_allocations_diff:", report["floor_allocations_diff"])
        for r in report["detail"]:
            print(" ", r.get("district"), r.get("building_id"), "rerouted_label=", r.get("rerouted_label"),
                  "real=", r.get("real_floor_dwelling_counts"), "recon=", r.get("reconstructed_floor_dwelling_counts"),
                  "n_mismatched=", r.get("n_mismatched_pairs"), "note=", r.get("note"))
        return

    df_out = None
    if not args.t02_only:
        df_out, sanity_engine, sanity_floor, wall_time_s = census_transitions()
        print(f"T01 wall_time_s={wall_time_s} rows={len(df_out)}")
        print("sanity engine_status vs t05a engine_census_2026-09-03.json:")
        for district in DISTRICTS:
            print(f"  {district}: {sanity_engine[district]}")
        print(f"  fleet_match={sanity_engine['fleet_match']}")
        print(f"sanity n_floor_mismatches={sanity_floor}")

        for column in ("n_transitions", "n_dwelling_count_changes"):
            pooled, per_district, zero_vs_nonzero, n_fam, n_rerouted = _reroute_table(df_out, column)
            print(f"\n=== reroute-rate-by-{column} (emitted-family n={n_fam}, rerouted={n_rerouted}) ===")
            print(pooled.to_string())
            print(f"--- zero vs nonzero {column} ---")
            print(zero_vs_nonzero.to_string())
            print(f"--- per-district ({column}) ---")
            print(per_district.to_string())
    else:
        df_out = pd.read_csv(T01_CSV)

    if not args.t01_only:
        report = sample_and_probe(df_out)
        print("\nT02 aggregate:", json.dumps(report["aggregate"], indent=2))
        print("T02 cell sizes available:", report["cell_sizes_available"])
        print("T02 cell sizes sampled:", report["cell_sizes_sampled"])
        print("T02 label agreement (local rebuild vs prepared_buildings.csv):", report["label_agreement_local_rebuild_vs_prepared_csv"])


if __name__ == "__main__":
    main()
