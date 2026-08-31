"""EU-04 S2 physics-complete campaign runner over the 31 frozen C1A buildings.

Builds a real IDF from real TABULA constructions, real HVAC controls, and the
pinned Lyon 2023 EPW for each of the 31 rows of the frozen
``s2_c1_high_completeness_sample.csv``, runs EnergyPlus 23.1, and records one
result row per building. This is the first real European energy number in the
arc: S1 (``run_eu_s1_smoke.py``) installed a smoke construction and produced no
energy number.

Schedules are emitted at ``f=0`` only (the uninjected baseline) via
``emit_step8_gain_schedule`` as an external ``Schedule:File`` object. The
per-zone constant gains object that ``add_european_heating_controls`` installs
is removed immediately after being read for its magnitude, per
``emit_step8_gain_schedule``'s own contract that callers must remove a legacy
constant gain object before adding its external-file replacement -- otherwise
the two objects would double-count TABULA's phi_int.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient

from openubem.acquisition.european_weather import sha256_file
from openubem.config import ENERGYPLUS_IDD_PATH, ENERGYPLUS_PATH
from openubem.geometry.context import discover_context, resolve_european_context_height
from openubem.geometry.european_residential import (
    allocate_european_dwellings,
    european_layout_to_zone_specs,
    generate_european_dwelling_layout,
)
from openubem.geometry.zoning import build_zones
from openubem.idf.european_controls import add_european_heating_controls
from openubem.idf.european_physics import add_european_internal_mass, add_nomass_construction
from openubem.idf.builder import write_zone_volumes
from openubem.idf.surfaces import (
    extrude_geometry,
    find_mismatched_interzone_pairs,
    _force_reroute_room_layout_to_one_zone_per_floor,
    _repair_roof_roof_pairs,
    _repair_mismatched_horizontal_pairs,
    _pair_interfloor_surfaces,
)
from openubem.semantic.european_schedules import emit_step8_gain_schedule
from scripts.form_eu_s2_c1_sample import CENSUS_PATH

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_c1_high_completeness_sample.csv"
SUMMARY_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_c1_high_completeness_sample_summary.json"
MANIFEST_GPKG_PATH = ROOT / "openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg"
FR_ARCHETYPES_PATH = ROOT / "openubem/data/construction/tabula_archetypes_fr.json"
WEATHER_PATH = ROOT / "openubem/data/weather/fr_lyon_bron_2023_era5.epw"
REGISTRY_PATH = ROOT / "openubem/data/weather/weather_registry.json"
RUN_ROOT = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_campaign"
CAMPAIGN_MANIFEST_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_campaign_manifest.csv"
ZONE_WINDING_SIGN = 1.0

# FINDING 210 residual (2026-08-31 root-cause pass): geomeppy's intersect_match can
# leave a sub-mm near-duplicate vertex pair on a surface's own ring that EnergyPlus's
# GetVertices/CheckConvexity collapses asymmetrically between a ceiling and its paired
# floor -- observed at 0.0002-0.0006 m separation, well inside a typical OSM-derived
# coordinate's float noise floor. 5 mm is comfortably above that observed range while
# staying well below any real architectural feature.
NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005
# A second, independent instance of the same class of defect: intersect_match can
# also leave an exactly- (or near-) collinear vertex on a ring -- e.g. a point where a
# neighbouring zone's wall meets this surface's shared edge, splitting it at 180.000
# degrees exactly (confirmed on stem `8cdf349a99934f0d`, vertex 7 of a 9-vertex ring,
# interior angle = 180.000 deg, cos(angle) = -1.0000000000000002, i.e. genuinely
# collinear to machine precision, not just "nearly straight"). EnergyPlus's own
# CheckConvexity legitimately treats this as a redundant point and drops it, but not
# symmetrically between a ceiling and its mirrored floor partner, producing the
# identical vertex-size-mismatch FATAL even though no two vertices were close
# together. 0.1 deg is deliberately tight: a real, naturally near-straight OSM
# building corner was measured at 179.348 deg on a known-clean building
# (`BATIMENT0000000240879449_part0`) -- 0.65 deg short of straight -- so 0.1 deg
# catches the machine-precision artifact without flagging real architecture.
COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1


def _has_near_duplicate_vertex_surfaces(idf) -> bool:
    """True if any BUILDINGSURFACE:DETAILED ring carries a near-duplicate or a
    near-/exactly-collinear vertex (FINDING 210 residual, both confirmed independently
    against real EnergyPlus 23.1.0 runs, not just the `find_mismatched_interzone_pairs`
    raw-count heuristic, which catches neither).

    Checked on the ring itself (consecutive triples, including wrap-around), not just
    at interzone boundaries, since either side of a pair can carry the artifact.
    """
    import math

    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        coords = list(surf.coords)
        n = len(coords)
        if n < 3:
            continue
        for i in range(n):
            p0 = coords[(i - 1) % n]
            p1 = coords[i]
            p2 = coords[(i + 1) % n]
            v1 = (p0[0] - p1[0], p0[1] - p1[1], p0[2] - p1[2])
            v2 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
            len1 = math.sqrt(sum(c * c for c in v1))
            len2 = math.sqrt(sum(c * c for c in v2))
            if len1 < NEAR_DUPLICATE_VERTEX_TOLERANCE_M or len2 < NEAR_DUPLICATE_VERTEX_TOLERANCE_M:
                return True
            cos_a = sum(a * b for a, b in zip(v1, v2)) / (len1 * len2)
            cos_a = max(-1.0, min(1.0, cos_a))
            angle_deg = math.degrees(math.acos(cos_a))
            if angle_deg > 180.0 - COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG:
                return True
    return False

PROJECTED_CRS = "EPSG:32631"
FLOOR_TO_FLOOR_M = 3.0
FLOOR_TO_FLOOR_NOTE = "floor_to_floor_m=3.0 pinned geometry-smoke constant, not a physical claim about Lyon"
ENERGYPLUS_J_TO_KWH = 1.0 / 3.6e6
SENSITIVITY_F = 0.0

EUROPEAN_CONTEXT_RADIUS_M = 20.0
EUROPEAN_CONTEXT_RADIUS_NOTE = (
    "D-EU-40 R2: 20.0 m, the published method's own radius -- a separate constant from "
    "config.SHADING_SPHERE_RADIUS=30.0 (the North-American DESIGN value), never edited here."
)
SHADOW_CALCULATION_METHOD = "PolygonClipping"
SHADOW_CALCULATION_UPDATE_FREQUENCY_METHOD = "Periodic"
SHADOW_CALCULATION_UPDATE_FREQUENCY_DAYS = 1
SHADOW_CALCULATION_NOTE = (
    "D-EU-40 R7: EnergyPlus's own 20-day periodic default is documented as unsuitable for "
    "closely-spaced urban buildings; a daily (1-day) periodic update is used instead of "
    "Timestep to keep the four-district fleet's runtime bounded. Chosen once, before any "
    "EnergyPlus run in this task -- reported, not tuned to a result."
)

EUROPEAN_ADIABATIC_TOLERANCE_M = 0.30
EUROPEAN_ADIABATIC_NOTE = (
    "D-EU-40 R6, amended by D-EU-41 (2026-08-30): openubem/idf/surfaces.py's "
    "set_adiabatic_surfaces is a no-op stub with no neighbour-footprint input and is never "
    "called here. The party-wall flip is a European-only pass in this file, reusing the "
    "same neighbour rows and coordinate transform build_european_context (T06) already uses, "
    "so shading and the flip can never disagree about a neighbour's location. Adjacency test: "
    "the wall's XY base segment (its two most distant projected vertices) lies inside the "
    "neighbour footprint (the same minimum-rotated-rectangle emitted for shading), buffered "
    "by EUROPEAN_ADIABATIC_TOLERANCE_M -- state, never tune."
)

MANIFEST_COLUMNS = [
    "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
    "idf_sha256", "weather_sha256", "eplus_return_code", "severe_errors", "fatal_errors",
    "heating_kwh", "floor_area_m2", "eui_kwh_m2", "run_seconds",
]

IDF_HEADER_TEMPLATE = """Version,23.1;
Timestep,12;
Building,EU S2 Campaign,0,City,,,FullExterior,,;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,Yes,Yes,Yes,No,Yes,No,1;
SizingPeriod:WeatherFileDays,AnnualSizingPeriod,1,1,12,31,Monday,No,No;
RunPeriod,RunPeriod1,1,1,,12,31,,Sunday,No,No,No,Yes,Yes;
Site:Location,{city},{latitude},{longitude},{time_zone},{elevation};
ScheduleTypeLimits,Any Number;
ShadowCalculation,
    {shadow_method},
    {shadow_update_method},
    {shadow_update_days};
"""


def load_frozen_sample() -> pd.DataFrame:
    """Load the frozen 31-row C1A sample; never re-form, reorder, or re-derive it."""
    sample = pd.read_csv(SAMPLE_PATH)
    if len(sample) != 31:
        raise ValueError(f"frozen S2 sample must contain 31 rows, found {len(sample)}")
    counts = sample["building_type"].value_counts().to_dict()
    expected = {"AB": 8, "MFH": 8, "TH": 8, "SFH": 7}
    if counts != expected:
        raise ValueError(f"frozen S2 sample quotas do not match {expected}: found {counts}")
    return sample


def verify_census_sha256(sample_summary_path: Path = SUMMARY_PATH, census_path: Path = CENSUS_PATH) -> str:
    """Return the recorded census SHA-256 after checking it against the file on disk."""
    summary = json.loads(sample_summary_path.read_text(encoding="utf-8"))
    recorded = str(summary["source_census_sha256"])
    recomputed = hashlib.sha256(census_path.read_bytes()).hexdigest()
    if recorded != recomputed:
        raise ValueError(
            f"source census SHA-256 mismatch: recorded={recorded} recomputed={recomputed}"
        )
    return recorded


def validate_mapping_ready(sample: pd.DataFrame) -> None:
    """Fail closed if any frozen row is not MAPPED_LAYOUT_READY."""
    not_ready = sample.loc[sample["mapping_status"] != "MAPPED_LAYOUT_READY", "building_id"].tolist()
    if not_ready:
        raise ValueError(f"S2 campaign requires MAPPED_LAYOUT_READY for every row; not ready: {not_ready}")


def verify_weather_checksum(weather_path: Path = WEATHER_PATH, registry_path: Path = REGISTRY_PATH) -> str:
    """Assert the Lyon EPW SHA-256 equals the registry's recorded value; abort on mismatch."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    fr_target = next(entry for entry in registry["targets"] if entry["fold"] == "fr")
    recorded = str(fr_target["sha256"])
    recomputed = sha256_file(weather_path)
    if recorded != recomputed:
        raise ValueError(
            f"Lyon EPW SHA-256 mismatch: registry={recorded} recomputed={recomputed} file={weather_path}"
        )
    return recomputed


def load_fr_record(archetype_id: str) -> dict[str, object]:
    payload = json.loads(FR_ARCHETYPES_PATH.read_text(encoding="utf-8"))
    for record in payload["records"]:
        if record["archetype_id"] == archetype_id:
            return record
    raise ValueError(f"archetype_id not found in FR TABULA registry: {archetype_id!r}")


def load_manifest_native(manifest_path: Path = MANIFEST_GPKG_PATH) -> gpd.GeoDataFrame:
    """Load the residential manifest in its own native CRS -- never reproject.

    D-EU-04-H CP-1 measured that reprojecting to EPSG:2154 makes
    generate_european_dwelling_layout's fixed-origin rotation accumulate
    floating-point noise past the partition audit's tolerance
    (OpenUBEM_debug_References.md ch.5); the frozen sample was measured in the
    manifest's native CRS, EPSG:32631.
    """
    if not manifest_path.is_file():
        raise ValueError(f"Manifest does not exist: {manifest_path}")
    gdf = gpd.read_file(manifest_path)
    if gdf.crs is None or gdf.crs.to_string() != PROJECTED_CRS:
        raise ValueError(f"Manifest CRS is {gdf.crs}, expected native {PROJECTED_CRS}")
    return gdf


def _orient_zone_footprints(zones: list[dict[str, object]], *, sign: float = 1.0) -> None:
    """Normalise each zone's floor_polygon winding in place (fixes GetVertices upside-down warning)."""
    for zone in zones:
        oriented = orient(zone["floor_polygon"], sign=sign)
        zone["floor_polygon"] = oriented
        zone["coords_m"] = list(oriented.exterior.coords)[:-1]


def compute_district_median_residential_height_m(
    rows: list[dict[str, object]], *, floor_to_floor_m: float = FLOOR_TO_FLOOR_M,
) -> float:
    """D-EU-40 R4 fallback tier: median height over the district's own simulated
    residential population, each resolved height_m if present else levels *
    floor_to_floor_m. ``rows`` is the district's mapped residential row list
    (the same population that becomes the simulated fleet), never the raw
    01_buildings_clean.gpkg superset -- a non-residential context building must
    never set the "residential" median it may itself fall back to.
    """
    heights: list[float] = []
    for row in rows:
        height_m = row.get("height_m")
        levels = row.get("levels")
        if pd.notna(height_m) and float(height_m) > 0.0:
            heights.append(float(height_m))
        elif pd.notna(levels) and float(levels) > 0.0:
            heights.append(float(levels) * floor_to_floor_m)
    if not heights:
        raise ValueError("district median residential height: no row carries height_m or levels")
    return float(statistics.median(heights))


def build_european_context(
    building_osm_id: str,
    footprint,
    buildings_clean: gpd.GeoDataFrame,
    district_median_height_m: float,
    height_fallback_counter: Counter,
) -> list[dict[str, object]]:
    """D-EU-40 R2-R5: the target's 20 m context, geometry via ``discover_context``
    unchanged, height re-resolved per the European R4 precedence.

    ``buildings_clean`` must be the district's 01_buildings_clean.gpkg superset
    (R3), never the residential manifest alone, so non-residential/excluded/
    typology-gap neighbours shade too. ``height_fallback_counter`` is mutated
    in place, one increment per context building, keyed by the tier used.
    """
    target_row = pd.Series({"osm_id": str(building_osm_id), "_simplified_geom": footprint})
    raw_context = discover_context(
        target_row, buildings_clean, 0.0, 0.0, sphere_radius_m=EUROPEAN_CONTEXT_RADIUS_M,
    )
    by_osm_id = buildings_clean.set_index(buildings_clean["osm_id"].astype(str), drop=False)
    context: list[dict[str, object]] = []
    for entry in raw_context:
        ctx_osm_id = entry["name"][len("shade_"):]
        ctx_row = by_osm_id.loc[ctx_osm_id]
        height_m, tier = resolve_european_context_height(
            ctx_row.get("height_m"), ctx_row.get("levels"), district_median_height_m,
        )
        height_fallback_counter[tier] += 1
        context.append({**entry, "height": height_m})
    return context


def _wall_xy_segment(coords) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """The wall's two most distant projected (XY) vertices -- its footprint base edge.

    A vertical rectangular wall (as produced by geomeppy's add_block extrusion)
    projects to exactly two distinct XY points; taking the most-distant pair is
    robust to any extra collinear vertices without assuming a fixed count.
    """
    unique: list[tuple[float, float]] = []
    for x, y, _z in coords:
        pt = (round(float(x), 6), round(float(y), 6))
        if pt not in unique:
            unique.append(pt)
    if len(unique) < 2:
        return None
    best_pair = None
    best_dist = -1.0
    for i in range(len(unique)):
        for j in range(i + 1, len(unique)):
            dist = ((unique[i][0] - unique[j][0]) ** 2 + (unique[i][1] - unique[j][1]) ** 2) ** 0.5
            if dist > best_dist:
                best_dist = dist
                best_pair = (unique[i], unique[j])
    return best_pair


def _wall_area_m2(coords) -> float:
    """Planar area of a vertical rectangular wall: base-segment length x height range."""
    segment = _wall_xy_segment(coords)
    if segment is None:
        return 0.0
    (x1, y1), (x2, y2) = segment
    base_length = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    zs = [float(z) for _x, _y, z in coords]
    return base_length * (max(zs) - min(zs))


def apply_adiabatic_party_walls(
    idf, context: list[dict[str, object]], *, tolerance_m: float = EUROPEAN_ADIABATIC_TOLERANCE_M,
) -> dict[str, float]:
    """D-EU-40 R6 / D-EU-41: flip walls shared with a neighbour to Adiabatic.

    European-only pass; ``openubem/idf/surfaces.py`` is never edited or called
    here. Reuses the exact neighbour footprints ``context[i]["coords"]`` --
    the same minimum-rotated-rectangle ``build_european_context`` already
    builds for shading -- so shading and the flip can never disagree about a
    neighbour's location. Must be called after ``extrude_geometry`` (so
    ``intersect_match`` and the shading blocks are already in the IDF -- R8).

    Scope: ``BUILDINGSURFACE:DETAILED`` with ``Surface_Type == Wall`` **and**
    ``Outside_Boundary_Condition == outdoors`` only -- never ``ground``, never
    ``surface`` (inter-zone, from ``intersect_match``), never a
    ``Floor``/``Roof``/``Ceiling``. A ground-floor slab at z=0 keeps ``Ground``
    (``surfaces.py:912``) because it is never a ``Wall``.

    Adjacency test: the wall's XY base segment lies inside the neighbour
    footprint buffered by ``tolerance_m`` (shapely ``within``) -- stated here,
    never tuned to move a count.

    Returns the R9 disclosure counts: flipped wall count, exterior wall area
    before the flip, and the flipped subset's area.
    """
    neighbour_polygons = [Polygon(ctx["coords"]).buffer(tolerance_m) for ctx in context]
    flipped_count = 0
    exterior_wall_area_m2 = 0.0
    flipped_wall_area_m2 = 0.0
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if str(surface.Surface_Type).strip().upper() != "WALL":
            continue
        if str(surface.Outside_Boundary_Condition).strip().upper() != "OUTDOORS":
            continue
        coords = list(surface.coords)
        area_m2 = _wall_area_m2(coords)
        exterior_wall_area_m2 += area_m2
        if not neighbour_polygons:
            continue
        segment = _wall_xy_segment(coords)
        if segment is None:
            continue
        line = LineString(segment)
        if any(line.within(poly) for poly in neighbour_polygons):
            surface.Outside_Boundary_Condition = "Adiabatic"
            surface.Outside_Boundary_Condition_Object = ""
            surface.Sun_Exposure = "NoSun"
            surface.Wind_Exposure = "NoWind"
            flipped_count += 1
            flipped_wall_area_m2 += area_m2
    return {
        "adiabatic_wall_count": flipped_count,
        "exterior_wall_area_m2": round(exterior_wall_area_m2, 4),
        "adiabatic_wall_area_m2": round(flipped_wall_area_m2, 4),
    }


def build_geometry_for_row(row: pd.Series, manifest: gpd.GeoDataFrame) -> tuple[list[dict[str, object]], str]:
    """Return (zones, geometry_outcome) re-derived from the real footprint, never from the CSV."""
    building_id = row["building_id"]
    matches = manifest.loc[manifest["osm_id"].astype(str) == building_id, "geometry"]
    if matches.empty:
        raise ValueError(f"building_id missing from manifest: {building_id!r}")
    footprint = matches.iloc[0]
    allocation = allocate_european_dwellings(
        archetype_id=row["archetype_id"],
        building_type=row["building_type"],
        n_apartment=row["observed_dwellings"],
        n_storey=row["observed_storeys"],
        plate_area_m2=float(footprint.area),
    )
    layout = generate_european_dwelling_layout(footprint, requested_dwelling_count=allocation.units_per_floor)
    if layout.dwelling_layout_emitted:
        zones = european_layout_to_zone_specs(layout, building_id=building_id, height_m=FLOOR_TO_FLOOR_M)
    else:
        zones = build_zones(
            building_id, footprint, row["archetype_id"],
            num_floors=int(round(float(row["observed_storeys"]))),
            strategy="one_zone_per_floor", floor_to_floor_m=FLOOR_TO_FLOOR_M,
        )
    _orient_zone_footprints(zones, sign=ZONE_WINDING_SIGN)
    return zones, layout.status


def _envelope_construction(idf, record: dict[str, object], component: str) -> str:
    f_red = float(record["f_red_temp"])
    u_value = float(record[f"u_{component}_w_m2k"]) * f_red
    delta_u = float(record["delta_u_tb_w_m2k"]) * f_red
    return add_nomass_construction(idf, f"EU_{component}", u_value, delta_u)


def build_idf_for_building(
    row: pd.Series,
    record: dict[str, object],
    zones: list[dict[str, object]],
    run_dir: Path,
    *,
    epw_path: Path = WEATHER_PATH,
    context: list[dict[str, object]] | None = None,
) -> Path:
    """Assemble and save one building's IDF; caller runs EnergyPlus separately.

    ``context`` (D-EU-40 / EU-16 T06): shading-only volumes for buildings within
    the European 20 m radius, built by :func:`build_european_context`. Defaults
    to no context (unchanged behaviour) when the caller does not supply one.
    The same ``context`` also drives T07's adiabatic party-wall flip
    (:func:`apply_adiabatic_party_walls`), applied right after
    ``extrude_geometry`` so the ordering invariant (R8) holds.
    """
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        location_fields = stream.readline().strip().split(",")
    city, _state, _country = location_fields[1], location_fields[2], location_fields[3]
    latitude, longitude, time_zone, elevation = (float(value) for value in location_fields[6:10])

    run_dir.mkdir(parents=True, exist_ok=True)
    idf_path = run_dir / f"{row['building_id']}.idf"
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
    extrude_geometry(idf, zones, context or [])
    # FINDING 210 residual (D-EU-42/D-EU-43 [OPEN] correction, 2026-08-31 root-cause
    # pass): geomeppy's own intersect_match (surfaces.py:866, non-editable, D-EU-41)
    # inserts new boundary vertices from live floating-point intersection arithmetic
    # when it cuts a same-zone-label block (e.g. one ``_2`` dwelling-index or
    # ``_circulation`` block spanning every storey that carries that label) against
    # its per-storey neighbours -- independently for the ceiling of storey n and the
    # floor of storey n+1, so the two can end up with different final vertex counts
    # even though the raw ring `_stabilize_ring_coords` emitted was identical and
    # already 1 mm-snapped going in. No further ring construction change can fix a
    # divergence introduced downstream of extrusion, so this reuses the exact
    # gate/reroute safety net `openubem/idf/builder.py` already wires for the same
    # symptom (`find_mismatched_interzone_pairs` +
    # `_force_reroute_room_layout_to_one_zone_per_floor`, which already understands
    # ``mode="european_dwelling_layout"`` zones) -- one_zone_per_floor has no
    # interzone perim pairs, so it structurally cannot reproduce this mismatch.
    #
    # A raw `len(coords)` count match is NOT sufficient on its own -- confirmed by
    # running EnergyPlus 23.1.0 directly (Windows, this session) on stem
    # `e21bec78b937acf5`: `find_mismatched_interzone_pairs` reported 0 mismatches
    # (both paired surfaces carried 7 raw vertices, mirror-ordered), yet EnergyPlus's
    # own GetVertices/CheckConvexity still collapsed them asymmetrically to 4 vs 6 and
    # FATALed identically to Speed. The culprit was a sub-mm near-duplicate vertex
    # pair intersect_match had inserted into BOTH surfaces' own rings (one point
    # grid-clean from the 1 mm snap, the other an unsnapped raw intersection
    # coordinate ~0.0002-0.0006 m away) -- EnergyPlus's own duplicate-vertex removal
    # is winding-direction-dependent, so it does not collapse both sides the same way.
    # `_has_near_duplicate_vertex` below flags exactly this pattern (any two
    # consecutive vertices on one surface's own ring closer than
    # `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`) so the reroute fires proactively instead of
    # relying on a raw count that this class of defect does not always move.
    mismatched = find_mismatched_interzone_pairs(idf)
    at_risk = mismatched or _has_near_duplicate_vertex_surfaces(idf)
    if at_risk:
        reason = "interzone_vertex_mismatch" if mismatched else "near_duplicate_vertex"
        did_reroute = _force_reroute_room_layout_to_one_zone_per_floor(idf, zones, reason)
        if did_reroute:
            idf.intersect_match()
            _repair_roof_roof_pairs(idf)
            _repair_mismatched_horizontal_pairs(idf)
            _pair_interfloor_surfaces(idf)
            mismatched = find_mismatched_interzone_pairs(idf)
            residual_near_dup = _has_near_duplicate_vertex_surfaces(idf)
        else:
            residual_near_dup = _has_near_duplicate_vertex_surfaces(idf)
        if mismatched or residual_near_dup:
            raise RuntimeError(
                f"interzone_vertex_mismatch_unresolved: mismatched={mismatched} "
                f"near_duplicate_vertex={residual_near_dup}"
            )
    apply_adiabatic_party_walls(idf, context or [])
    write_zone_volumes(idf, zones)

    wall_construction = _envelope_construction(idf, record, "wall")
    roof_construction = _envelope_construction(idf, record, "roof")
    floor_construction = _envelope_construction(idf, record, "floor")
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        surface_type = str(surface.Surface_Type).upper()
        if surface_type == "WALL":
            surface.Construction_Name = wall_construction
        elif surface_type in ("ROOF", "ROOFCEILING"):
            surface.Construction_Name = roof_construction
        elif surface_type in ("FLOOR", "CEILING"):
            surface.Construction_Name = floor_construction

    for zone in zones:
        if zone.get("conditioned") is False:
            # D-EU-39 §3 / EU-15 T05: the carved circulation core/corridor is
            # unconditioned -- no SIZING:ZONE, no HVACTemplate:Zone, no
            # internal gains, only the ruled constant infiltration rate.
            if idf.getobject("SCHEDULE:CONSTANT", "EU_AlwaysOn") is None:
                idf.newidfobject("SCHEDULE:CONSTANT", Name="EU_AlwaysOn", Hourly_Value=1.0)
            idf.newidfobject(
                "ZONEINFILTRATION:DESIGNFLOWRATE",
                Name=f"EU_Circulation_Infiltration_{zone['name']}",
                Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone["name"],
                Schedule_Name="EU_AlwaysOn",
                Design_Flow_Rate_Calculation_Method="Flow/Area",
                Flow_Rate_per_Floor_Area=float(zone.get("infiltration_m3_s_m2", 0.000500)),
            )
            continue
        floor_area_m2 = float(zone["floor_polygon"].area)
        add_european_internal_mass(idf, zone["name"], floor_area_m2, c_m_wh_m2k=float(record["c_m_wh_m2k"]))
        idf.newidfobject(
            "SIZING:ZONE",
            Zone_or_ZoneList_Name=zone["name"],
            Zone_Cooling_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
            Zone_Cooling_Design_Supply_Air_Temperature=13.0,
            Zone_Heating_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
            Zone_Heating_Design_Supply_Air_Temperature=50.0,
            Zone_Cooling_Design_Supply_Air_Humidity_Ratio=0.008,
            Zone_Heating_Design_Supply_Air_Humidity_Ratio=0.008,
        )
        names = add_european_heating_controls(idf, record, zone["name"])
        legacy_gain = idf.getobject("OTHEREQUIPMENT", names["gains"])
        if legacy_gain is not None:
            idf.removeidfobject(legacy_gain)
        # emit_step8_gain_schedule always (re-)creates a fixed-name
        # SCHEDULETYPELIMITS object; across multiple dwelling zones in one IDF
        # that duplicates the object and EnergyPlus fails input processing.
        # Drop any prior copy immediately before each call so exactly one survives.
        existing_limits = idf.getobject("SCHEDULETYPELIMITS", "EU_Step8_AnyNumber_Wm2")
        if existing_limits is not None:
            idf.removeidfobject(existing_limits)
        gain_csv_path = run_dir / f"{zone['name']}_f000_gain.csv"
        emit_step8_gain_schedule(
            idf,
            sensitivity_f=SENSITIVITY_F,
            dwelling_zone=zone["name"],
            dwelling_id=zone["name"],
            emitted_csv_path=gain_csv_path,
        )

    idf.newidfobject(
        "OUTPUT:VARIABLE", Key_Value="*",
        Variable_Name="Zone Ideal Loads Zone Total Heating Energy",
        Reporting_Frequency="Hourly",
    )
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
    idf.saveas(str(idf_path))
    return idf_path


def _extract_heating_kwh(csv_path: Path) -> float:
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"eplusout.csv has no header: {csv_path}")
        columns = [
            field for field in reader.fieldnames
            if "zone ideal loads zone total heating energy" in field.casefold()
            and "[j]" in field.casefold() and "(hourly)" in field.casefold()
        ]
        if not columns:
            raise ValueError(f"eplusout.csv lacks hourly heating energy output: {csv_path}")
        total_j = 0.0
        for row in reader:
            total_j += sum(float(row[column]) for column in columns)
    return total_j * ENERGYPLUS_J_TO_KWH


def run_energyplus_for_building(idf_path: Path, run_dir: Path, *, epw_path: Path = WEATHER_PATH, timeout: int = 600) -> dict[str, object]:
    energyplus_exe = ENERGYPLUS_PATH / ("energyplus.exe" if sys.platform == "win32" else "energyplus")
    start = time.perf_counter()
    eplus_return_code: int | None = None
    err_text = ""
    try:
        result = subprocess.run(
            [str(energyplus_exe), "-w", str(epw_path), "-x", "-r", "-d", ".", str(idf_path)],
            cwd=run_dir, capture_output=True, text=True, timeout=timeout,
        )
        eplus_return_code = result.returncode
        err_path = run_dir / "eplusout.err"
        err_text = err_path.read_text(encoding="utf-8", errors="replace") if err_path.is_file() else ""
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
    run_seconds = time.perf_counter() - start

    severe_errors = len(re.findall(r"\*\*\s*Severe\s*\*\*", err_text, re.IGNORECASE))
    fatal_errors = len(re.findall(r"\*\*\s*Fatal\s*\*\*", err_text, re.IGNORECASE))
    completed = (
        not timed_out and eplus_return_code == 0 and "Completed Successfully" in err_text
    )

    heating_kwh = None
    floor_area_m2 = None
    if completed:
        csv_path = run_dir / "eplusout.csv"
        heating_kwh = _extract_heating_kwh(csv_path)

    return {
        "eplus_return_code": eplus_return_code if eplus_return_code is not None else -1,
        "severe_errors": severe_errors,
        "fatal_errors": fatal_errors,
        "completed": completed,
        "heating_kwh": heating_kwh,
        "floor_area_m2": floor_area_m2,
        "run_seconds": round(run_seconds, 3),
        "err_text": err_text,
    }


def run_campaign(dry_run: bool = False) -> pd.DataFrame:
    verify_census_sha256()
    sample = load_frozen_sample()
    validate_mapping_ready(sample)
    if not dry_run:
        verify_weather_checksum()
    manifest = load_manifest_native()

    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for _, row in sample.sort_values("building_id").iterrows():
        building_id = row["building_id"]
        record = load_fr_record(row["archetype_id"])
        zones, geometry_outcome = build_geometry_for_row(row, manifest)
        run_dir = RUN_ROOT / building_id
        idf_path = build_idf_for_building(row, record, zones, run_dir)
        idf_sha256 = sha256_file(idf_path)
        floor_area_m2 = sum(float(zone["floor_polygon"].area) for zone in zones)

        result_row = {
            "building_id": building_id,
            "archetype_id": row["archetype_id"],
            "building_type": row["building_type"],
            "age_band": row["age_band"],
            "geometry_outcome": geometry_outcome,
            "idf_sha256": idf_sha256,
            "weather_sha256": "",
            "eplus_return_code": "",
            "severe_errors": "",
            "fatal_errors": "",
            "heating_kwh": "",
            "floor_area_m2": round(floor_area_m2, 4),
            "eui_kwh_m2": "",
            "run_seconds": "",
        }

        if not dry_run:
            weather_sha256 = verify_weather_checksum()
            outcome = run_energyplus_for_building(idf_path, run_dir)
            result_row["weather_sha256"] = weather_sha256
            result_row["eplus_return_code"] = outcome["eplus_return_code"]
            result_row["severe_errors"] = outcome["severe_errors"]
            result_row["fatal_errors"] = outcome["fatal_errors"]
            result_row["run_seconds"] = outcome["run_seconds"]
            if outcome["completed"]:
                heating_kwh = outcome["heating_kwh"]
                result_row["heating_kwh"] = round(heating_kwh, 6)
                result_row["eui_kwh_m2"] = round(heating_kwh / floor_area_m2, 6) if floor_area_m2 > 0 else ""
                status = "EPLUS_COMPLETED"
            else:
                fatal_match = re.search(r"^.*\*\*\s*Fatal\s*\*\*.*$", outcome["err_text"], re.MULTILINE)
                severe_match = re.search(r"^.*\*\*\s*Severe\s*\*\*.*$", outcome["err_text"], re.MULTILINE)
                first_error = (fatal_match or severe_match).group(0).strip()[:300] if (fatal_match or severe_match) else "no Severe/Fatal line in eplusout.err"
                status = "EPLUS_FATAL"
                print(f"    first_error: {first_error}")
            print(
                f"  {building_id}: geometry_outcome={geometry_outcome} zones={len(zones)} "
                f"status={status} run_seconds={outcome['run_seconds']}"
            )

        rows.append(result_row)

    frame = pd.DataFrame.from_records(rows, columns=MANIFEST_COLUMNS)
    if not dry_run:
        frame.to_csv(CAMPAIGN_MANIFEST_PATH, index=False)
    return frame


def main() -> None:
    global RUN_ROOT, CAMPAIGN_MANIFEST_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="build IDFs only; do not run EnergyPlus")
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="override RUN_ROOT; manifest is written alongside it as <name>_manifest.csv "
             "(default preserves openubem/outputs/eu_evidence/EU-04/s2_campaign/)",
    )
    args = parser.parse_args()
    if args.output_dir is not None:
        RUN_ROOT = args.output_dir.resolve()
        CAMPAIGN_MANIFEST_PATH = RUN_ROOT.parent / f"{RUN_ROOT.name}_manifest.csv"
    frame = run_campaign(dry_run=args.dry_run)
    if not args.dry_run:
        print(f"Wrote {CAMPAIGN_MANIFEST_PATH} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
