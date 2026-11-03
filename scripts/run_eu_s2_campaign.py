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
from itertools import groupby
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
from openubem.idf.european_windows import add_tabula_windows
from openubem.idf.surface_orientation import normalise_surface_orientation
from openubem.idf.builder import write_zone_volumes
import openubem.idf.surfaces as _surfaces
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


def _has_near_duplicate_vertex_surfaces(idf, interzone_only: bool = True) -> bool:
    """True if any BUILDINGSURFACE:DETAILED ring carries a near-duplicate or a
    near-/exactly-collinear vertex (FINDING 210 residual, both confirmed independently
    against real EnergyPlus 23.1.0 runs, not just the `find_mismatched_interzone_pairs`
    raw-count heuristic, which catches neither).

    FINDING 249 restricted remedy (2026-09-04): by default (`interzone_only=True`),
    only surfaces with a valid interzone partner (Outside_Boundary_Condition == "Surface"
    with a resolvable Outside_Boundary_Condition_Object) are checked. Partner-less
    surfaces (Ground, Outdoors, Adiabatic) cannot cause an interzone vertex mismatch
    in EnergyPlus and are excused from setting at_risk. Any interzone-paired defect
    sets at_risk = True unconditionally (no coordinate-symmetry check).
    """
    import math

    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    surf_by_name = {str(s.Name).upper(): s for s in bsds} if interzone_only else {}

    for surf in bsds:
        if interzone_only:
            if str(getattr(surf, "Outside_Boundary_Condition", "")).upper() != "SURFACE":
                continue
            partner_name = str(getattr(surf, "Outside_Boundary_Condition_Object", "") or "").upper()
            if not partner_name or partner_name == str(surf.Name).upper():
                continue
            if partner_name not in surf_by_name:
                continue

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


MIRROR_COVERAGE_AREA_TOLERANCE_M2 = 1e-4
MIRROR_COVERAGE_VERTEX_TOLERANCE_M = 0.005
RING_CLEAN_MIN_EDGE_M = 0.01


def _clean_ring_3d(coords):
    import math

    ring = [tuple(float(c) for c in p) for p in coords]
    original = list(ring)

    def _dist(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def _one_pass(ring):
        spiked = True
        while spiked and len(ring) >= 3:
            spiked = False
            n = len(ring)
            for i in range(n):
                if _dist(ring[(i - 1) % n], ring[(i + 1) % n]) < RING_CLEAN_MIN_EDGE_M:
                    j = (i + 1) % n
                    ring = [p for k, p in enumerate(ring) if k not in (i, j)]
                    spiked = True
                    break
        if len(ring) < 3:
            ring = list(original)
        changed = True
        while changed and len(ring) > 3:
            changed = False
            n = len(ring)
            for i in range(n):
                p0, p1, p2 = ring[(i - 1) % n], ring[i], ring[(i + 1) % n]
                v1 = tuple(a - b for a, b in zip(p0, p1))
                v2 = tuple(a - b for a, b in zip(p2, p1))
                len1 = math.sqrt(sum(c * c for c in v1))
                len2 = math.sqrt(sum(c * c for c in v2))
                drop = len1 < RING_CLEAN_MIN_EDGE_M or len2 < RING_CLEAN_MIN_EDGE_M
                if not drop:
                    cos_a = max(-1.0, min(1.0, sum(a * b for a, b in zip(v1, v2)) / (len1 * len2)))
                    drop = math.degrees(math.acos(cos_a)) > 180.0 - COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG
                if drop:
                    del ring[i]
                    changed = True
                    break
        return ring

    while True:
        before = len(ring)
        ring = _one_pass(ring)
        if len(ring) == before:
            break
    return ring


def _plane_basis(ring):
    import math

    nx, ny, nz = _newell_normal(ring)
    norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if norm == 0.0:
        return None
    nx, ny, nz = nx / norm, ny / norm, nz / norm
    ref = (1.0, 0.0, 0.0) if abs(nx) < 0.9 else (0.0, 1.0, 0.0)
    ux = ny * ref[2] - nz * ref[1]
    uy = nz * ref[0] - nx * ref[2]
    uz = nx * ref[1] - ny * ref[0]
    un = math.sqrt(ux * ux + uy * uy + uz * uz)
    u = (ux / un, uy / un, uz / un)
    v = (ny * u[2] - nz * u[1], nz * u[0] - nx * u[2], nx * u[1] - ny * u[0])
    return tuple(ring[0]), u, v, (nx, ny, nz)


def _plane_frame(ring):
    basis = _plane_basis(ring)
    if basis is None:
        return None
    origin, u, v, _n = basis

    def project(p):
        d = tuple(a - b for a, b in zip(p, origin))
        return (sum(a * b for a, b in zip(d, u)), sum(a * b for a, b in zip(d, v)))

    return project


def _pair_covers_same_polygon(clean_ring, partner_ring) -> bool:
    from shapely.geometry import Point

    project = _plane_frame(clean_ring)
    if project is None:
        return False
    a = Polygon([project(p) for p in clean_ring])
    partner_clean = _clean_ring_3d(partner_ring)
    if len(partner_clean) < 3:
        return False
    b = Polygon([project(p) for p in partner_clean])
    if not a.is_valid:
        a = a.buffer(0)
    if not b.is_valid:
        b = b.buffer(0)
    if a.is_empty or b.is_empty or a.geom_type != "Polygon" or b.geom_type != "Polygon" or a.area <= 0.0 or b.area <= 0.0:
        return False
    if a.symmetric_difference(b).area > MIRROR_COVERAGE_AREA_TOLERANCE_M2:
        return False
    boundary = a.exterior
    return all(boundary.distance(Point(project(p))) <= MIRROR_COVERAGE_VERTEX_TOLERANCE_M for p in partner_ring)


def _newell_normal(ring):
    nx = ny = nz = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1, z1 = ring[i]
        x2, y2, z2 = ring[(i + 1) % n]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return nx, ny, nz


def _interzone_groups(bsds):
    by_name = {str(s.Name).upper(): s for s in bsds}
    parent = {name: name for name in by_name}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    linked = set()
    for surf in bsds:
        if str(getattr(surf, "Outside_Boundary_Condition", "")).upper() != "SURFACE":
            continue
        name = str(surf.Name).upper()
        partner = str(getattr(surf, "Outside_Boundary_Condition_Object", "") or "").upper()
        if partner not in by_name or partner == name:
            continue
        linked.update((name, partner))
        parent[find(name)] = find(partner)
    groups = {}
    for name in linked:
        groups.setdefault(find(name), []).append(name)
    return by_name, [sorted(g) for g in groups.values()]


def _same_cyclic_ring(a, b) -> bool:
    if len(a) != len(b):
        return False
    return any(b[i:] + b[:i] == a for i in range(len(b)))


MIRROR_NEAR_SAME_AREA_M2 = 0.01
MAX_ADIABATIC_REMAINDER_M2 = 1.0
REMAINDER_PLANE_TOLERANCE_M = 0.01
PAIR_STAT_KEYS = (
    "pairs_seen", "pairs_rewritten", "pairs_skipped_coverage", "pairs_near_same_mirrored", "pairs_split",
    "remainder_paired", "remainder_dropped", "remainder_adiabatic", "adiabatic_area_m2", "pairs_still_skipped",
    "remainder_outdoors", "outdoors_area_m2",
)


def _fenestration_hosts(idf) -> set:
    try:
        fens = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    except KeyError:
        return set()
    return {str(f.Building_Surface_Name).upper() for f in fens}


def _polygon_in_frame(ring, project):
    poly = Polygon([project(p) for p in ring])
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def _relative_targets(members, rings, ref_index, cleaned):
    ref_normal = _newell_normal(cleaned)
    targets = []
    for i, ring in enumerate(rings):
        if i == ref_index:
            targets.append(list(cleaned))
            continue
        same_side = len(members) > 2 and sum(a * b for a, b in zip(_newell_normal(ring), ref_normal)) > 0.0
        targets.append(list(cleaned) if same_side else list(reversed(cleaned)))
    return targets


def _mirror_near_same_group(members, rings):
    cleaned_all = [_clean_ring_3d(r) for r in rings]
    if any(len(c) < 3 for c in cleaned_all):
        return False
    ref_index = max(range(len(rings)), key=lambda i: _ring_area_m2(cleaned_all[i]))
    ref = cleaned_all[ref_index]
    project = _plane_frame(ref)
    if project is None:
        return False
    ref_poly = _polygon_in_frame(ref, project)
    if ref_poly.is_empty or ref_poly.geom_type != "Polygon" or ref_poly.area <= 0.0:
        return False
    for i, c in enumerate(cleaned_all):
        if i == ref_index:
            continue
        other = _polygon_in_frame(c, project)
        if other.is_empty or other.geom_type != "Polygon" or other.area <= 0.0:
            return False
        if ref_poly.symmetric_difference(other).area > MIRROR_NEAR_SAME_AREA_M2 + 1e-9:
            return False
    for member, target in zip(members, _relative_targets(members, rings, ref_index, ref)):
        member.setcoords(target)
    return True


def _find_remainder_partner(bsds, piece_ring, large, exclude, hosts):
    basis = _plane_basis(piece_ring)
    if basis is None:
        return None
    origin, _u, _v, normal = basis
    project = _plane_frame(piece_ring)
    piece_poly = _polygon_in_frame(piece_ring, project)
    zone = str(getattr(large, "Zone_Name", "")).upper()
    best = None
    for cand in bsds:
        name = str(cand.Name).upper()
        if name in exclude or name in hosts:
            continue
        if str(getattr(cand, "Outside_Boundary_Condition", "")).upper() == "SURFACE":
            continue
        if str(getattr(cand, "Zone_Name", "")).upper() == zone:
            continue
        ring = [tuple(p) for p in cand.coords]
        if len(ring) < 3:
            continue
        if any(abs(sum((a - b) * n for a, b, n in zip(p, origin, normal))) > REMAINDER_PLANE_TOLERANCE_M for p in ring):
            continue
        cn = _newell_normal(ring)
        if sum(a * b for a, b in zip(cn, normal)) >= 0.0:
            continue
        cand_clean = _clean_ring_3d(ring)
        if len(cand_clean) < 3:
            continue
        diff = piece_poly.symmetric_difference(_polygon_in_frame(cand_clean, project)).area
        if diff <= MIRROR_NEAR_SAME_AREA_M2 and (best is None or diff < best[0]):
            best = (diff, cand)
    return None if best is None else best[1]


def _nothing_across(bsds, piece_ring, large, exclude):
    basis = _plane_basis(piece_ring)
    project = _plane_frame(piece_ring)
    if basis is None or project is None:
        return False
    origin, _u, _v, normal = basis
    piece_poly = _polygon_in_frame(piece_ring, project)
    zone = str(getattr(large, "Zone_Name", "")).upper()
    for cand in bsds:
        if str(cand.Name).upper() in exclude or str(getattr(cand, "Zone_Name", "")).upper() == zone:
            continue
        ring = [tuple(p) for p in cand.coords]
        if len(ring) < 3:
            continue
        if any(abs(sum((a - b) * n for a, b, n in zip(p, origin, normal))) > REMAINDER_PLANE_TOLERANCE_M for p in ring):
            continue
        if sum(a * b for a, b in zip(_newell_normal(ring), normal)) >= 0.0:
            continue
        cand_clean = _clean_ring_3d(ring)
        if len(cand_clean) < 3:
            continue
        if piece_poly.intersection(_polygon_in_frame(cand_clean, project)).area > MIRROR_NEAR_SAME_AREA_M2:
            return False
    return True


def _outdoor_construction(bsds, kind):
    for surf in bsds:
        surface_type = str(getattr(surf, "Surface_Type", "")).upper()
        obc = str(getattr(surf, "Outside_Boundary_Condition", "")).upper()
        if kind == "roof" and surface_type == "ROOF" and obc == "OUTDOORS":
            return surf.Construction_Name
        if kind == "floor" and surface_type == "FLOOR" and obc in ("OUTDOORS", "GROUND"):
            return surf.Construction_Name
    return None


def _split_larger_group(idf, bsds, members, rings, adiabatic_used):
    cleaned = [_clean_ring_3d(r) for r in rings]
    if any(len(c) < 3 for c in cleaned):
        return None
    li = max(range(len(members)), key=lambda i: _ring_area_m2(cleaned[i]))
    large, large_clean = members[li], cleaned[li]
    small_index = sorted((i for i in range(len(members)) if i != li), key=lambda i: str(members[i].Name))
    hosts = _fenestration_hosts(idf)
    if str(large.Name).upper() in hosts:
        return None
    basis = _plane_basis(large_clean)
    project = _plane_frame(large_clean)
    if basis is None or project is None:
        return None
    large_poly = _polygon_in_frame(large_clean, project)
    if large_poly.is_empty or large_poly.geom_type != "Polygon":
        return None
    tol = MIRROR_COVERAGE_VERTEX_TOLERANCE_M
    large_normal = basis[3]
    small_polys = []
    for i in small_index:
        poly = _polygon_in_frame(cleaned[i], project)
        if poly.is_empty or poly.geom_type != "Polygon" or not large_poly.buffer(tol).covers(poly):
            return None
        if sum(a * b for a, b in zip(_newell_normal(cleaned[i]), large_normal)) >= 0.0:
            return None
        small_polys.append(poly)
    for a in range(len(small_polys)):
        for b in range(a + 1, len(small_polys)):
            if small_polys[a].intersection(small_polys[b]).area >= MIRROR_NEAR_SAME_AREA_M2:
                return None
    covered = small_polys[0].buffer(tol, join_style=2)
    for poly in small_polys[1:]:
        covered = covered.union(poly.buffer(tol, join_style=2))
    remainder = large_poly.difference(covered)
    parts = [g for g in getattr(remainder, "geoms", [remainder]) if g.geom_type == "Polygon" and not g.is_empty]
    origin, u, v, _n = basis
    plan = []
    adiabatic_area = 0.0
    outdoors_area = 0.0
    dropped = 0
    exclude = {str(m.Name).upper() for m in members}
    for part in parts:
        if part.area < MIRROR_NEAR_SAME_AREA_M2:
            dropped += 1
            continue
        if part.interiors:
            return None
        part = orient(part, 1.0)
        ring3 = [
            tuple(origin[k] + x * u[k] + y * v[k] for k in range(3)) for x, y in list(part.exterior.coords)[:-1]
        ]
        ring3 = _clean_ring_3d(ring3)
        if len(ring3) < 3:
            dropped += 1
            continue
        partner = _find_remainder_partner(bsds, ring3, large, exclude, hosts)
        if partner is not None:
            exclude.add(str(partner.Name).upper())
            plan.append((ring3, partner))
        else:
            kind = None
            large_type = str(getattr(large, "Surface_Type", "")).upper()
            if large_type in ("CEILING", "FLOOR") and _nothing_across(bsds, ring3, large, exclude):
                wanted = "roof" if large_type == "CEILING" else "floor"
                construction = _outdoor_construction(bsds, wanted)
                if construction is not None:
                    kind = (wanted, construction)
            if kind is not None:
                plan.append((ring3, kind))
                outdoors_area += part.area
            else:
                plan.append((ring3, None))
                adiabatic_area += part.area
    if adiabatic_used + adiabatic_area > MAX_ADIABATIC_REMAINDER_M2:
        return None
    existing = {str(s.Name).upper() for s in bsds}

    def fresh_name(base):
        name = base
        while name.upper() in existing:
            name += "x"
        existing.add(name.upper())
        return name

    for order, i in enumerate(small_index):
        small = members[i]
        small.setcoords(list(cleaned[i]))
        if order == 0:
            piece = large
        else:
            piece = idf.copyidfobject(large)
            piece.Name = fresh_name(f"{large.Name}_S{order}")
        piece.setcoords(list(reversed(cleaned[i])))
        piece.Outside_Boundary_Condition = "Surface"
        piece.Outside_Boundary_Condition_Object = small.Name
        small.Outside_Boundary_Condition = "Surface"
        small.Outside_Boundary_Condition_Object = piece.Name
    paired = adiabatic = outdoors = 0
    for index, (ring3, partner) in enumerate(plan, start=1):
        piece = idf.copyidfobject(large)
        piece.Name = fresh_name(f"{large.Name}_R{index}")
        piece.setcoords(ring3)
        piece.Sun_Exposure = "NoSun"
        piece.Wind_Exposure = "NoWind"
        if isinstance(partner, tuple):
            wanted, construction = partner
            piece.Construction_Name = construction
            piece.Outside_Boundary_Condition = "Outdoors"
            piece.Outside_Boundary_Condition_Object = ""
            piece.Wind_Exposure = "WindExposed"
            if wanted == "roof":
                piece.Surface_Type = "Roof"
                piece.Sun_Exposure = "SunExposed"
            outdoors += 1
        elif partner is None:
            piece.Outside_Boundary_Condition = "Adiabatic"
            piece.Outside_Boundary_Condition_Object = ""
            adiabatic += 1
        else:
            piece.Outside_Boundary_Condition = "Surface"
            piece.Outside_Boundary_Condition_Object = partner.Name
            partner.Outside_Boundary_Condition = "Surface"
            partner.Outside_Boundary_Condition_Object = piece.Name
            partner.Sun_Exposure = "NoSun"
            partner.Wind_Exposure = "NoWind"
            partner.setcoords(list(reversed(ring3)))
            paired += 1
    return {
        "paired": paired, "dropped": dropped, "adiabatic": adiabatic, "adiabatic_area_m2": adiabatic_area,
        "outdoors": outdoors, "outdoors_area_m2": outdoors_area,
    }


def _repair_interzone_pairs(idf):
    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    by_name, groups = _interzone_groups(bsds)
    stats = {key: 0 for key in PAIR_STAT_KEYS}
    stats["adiabatic_area_m2"] = 0.0
    stats["outdoors_area_m2"] = 0.0
    unresolved = set()
    for names in sorted(groups):
        stats["pairs_seen"] += 1
        members = [by_name[n] for n in names]
        rings = [[tuple(p) for p in m.coords] for m in members]
        if any(len(r) < 3 for r in rings):
            stats["pairs_skipped_coverage"] += 1
            stats["pairs_still_skipped"] += 1
            unresolved.update(names)
            continue
        cleaned = _clean_ring_3d(rings[0])
        if len(cleaned) < 3:
            stats["pairs_skipped_coverage"] += 1
            stats["pairs_still_skipped"] += 1
            unresolved.update(names)
            continue
        targets = _relative_targets(members, rings, 0, cleaned)
        if all(_same_cyclic_ring(t, r) for t, r in zip(targets, rings)):
            continue
        if all(_pair_covers_same_polygon(cleaned, ring) for ring in rings[1:]):
            for member, target in zip(members, targets):
                member.setcoords(target)
            stats["pairs_rewritten"] += 1
            continue
        stats["pairs_skipped_coverage"] += 1
        if _mirror_near_same_group(members, rings):
            stats["pairs_near_same_mirrored"] += 1
            continue
        split = _split_larger_group(idf, bsds, members, rings, stats["adiabatic_area_m2"])
        if split is not None:
            stats["pairs_split"] += 1
            stats["remainder_paired"] += split["paired"]
            stats["remainder_dropped"] += split["dropped"]
            stats["remainder_adiabatic"] += split["adiabatic"]
            stats["adiabatic_area_m2"] += split["adiabatic_area_m2"]
            stats["remainder_outdoors"] += split["outdoors"]
            stats["outdoors_area_m2"] += split["outdoors_area_m2"]
            continue
        stats["pairs_still_skipped"] += 1
        unresolved.update(names)
    return stats, unresolved


def _mirror_interzone_pairs_stats(idf) -> dict[str, int]:
    return _repair_interzone_pairs(idf)[0]


def _mirror_interzone_pairs(idf) -> int:
    import logging

    stats = _mirror_interzone_pairs_stats(idf)
    logging.getLogger(__name__).info("mirror_interzone_pairs %s", stats)
    return stats["pairs_rewritten"] + stats["pairs_near_same_mirrored"] + stats["pairs_split"]


def _clean_surface_rings(idf, skip=frozenset()) -> int:
    changed = 0
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if str(surf.Name).upper() in skip:
            continue
        ring = [tuple(p) for p in surf.coords]
        cleaned = _clean_ring_3d(ring)
        if len(cleaned) >= 3 and len(cleaned) != len(ring) and _plane_basis(cleaned) is not None:
            surf.setcoords(cleaned)
            changed += 1
    return changed


SLIVER_SURFACE_MAX_AREA_M2 = 0.01
SLIVER_BUILDING_MAX_TOTAL_AREA_M2 = 0.5


def _ring_area_m2(ring) -> float:
    import math

    nx, ny, nz = _newell_normal(ring)
    return 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)


def _drop_sliver_surfaces(
    idf,
    max_area_m2: float = SLIVER_SURFACE_MAX_AREA_M2,
    max_total_m2: float = SLIVER_BUILDING_MAX_TOTAL_AREA_M2,
) -> tuple[int, float]:
    import logging

    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    by_name, groups = _interzone_groups(bsds)
    doomed = set()
    for name, surf in by_name.items():
        ring = [tuple(p) for p in surf.coords]
        if len(ring) < 3 or len(_clean_ring_3d(ring)) < 3 or _ring_area_m2(ring) < max_area_m2:
            doomed.add(name)
    if not doomed:
        return 0, 0.0
    for names in groups:
        if any(n in doomed for n in names):
            doomed.update(names)
    area = sum(_ring_area_m2([tuple(p) for p in by_name[n].coords]) for n in doomed)
    if area > max_total_m2:
        return 0, 0.0
    fens = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    for fen in list(fens):
        if str(fen.Building_Surface_Name).upper() in doomed:
            idf.removeidfobject(fen)
    for name in doomed:
        idf.removeidfobject(by_name[name])
    logging.getLogger(__name__).info("drop_sliver_surfaces removed=%d area_m2=%.3e", len(doomed), area)
    return len(doomed), area


DEGENERATE_MIN_EDGE_M = 0.01
DEGENERATE_COLLINEAR_SIN = 1e-4
DEGENERATE_ZERO_AREA_M2 = 1e-4
DEGENERATE_DROP_AREA_M2 = 0.01
PREFLIGHT_FALLBACK_NOTE = "room_layout_preflight_fallback"
LAST_DEGENERATE_STATS: dict = {}


def _ep_effective_ring(ring):
    import math

    pts = [tuple(float(c) for c in p) for p in ring]

    def _d(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    changed = True
    while changed and len(pts) >= 3:
        changed = False
        n = len(pts)
        for i in range(n):
            nxt = pts[(i + 1) % n]
            if _d(pts[i], nxt) < DEGENERATE_MIN_EDGE_M:
                del pts[(i + 1) % n]
                changed = True
                break
        if changed:
            continue
        n = len(pts)
        for i in range(n):
            a, b, c = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
            u = tuple(x - y for x, y in zip(b, a))
            v = tuple(x - y for x, y in zip(c, b))
            lu = math.sqrt(sum(x * x for x in u))
            lv = math.sqrt(sum(x * x for x in v))
            if lu == 0.0 or lv == 0.0:
                del pts[i]
                changed = True
                break
            cx = u[1] * v[2] - u[2] * v[1]
            cy = u[2] * v[0] - u[0] * v[2]
            cz = u[0] * v[1] - u[1] * v[0]
            if math.sqrt(cx * cx + cy * cy + cz * cz) / (lu * lv) < DEGENERATE_COLLINEAR_SIN:
                del pts[i]
                changed = True
                break
    return pts


def _degenerate_ring(ring) -> bool:
    eff = _ep_effective_ring(ring)
    return len(eff) < 3 or _ring_area_m2(eff) < DEGENERATE_ZERO_AREA_M2


EXPOSED_BETWEEN_ZONES_MIN_OVERLAP_M2 = 0.1
HORIZONTAL_LEVEL_TOLERANCE_M = 0.01
FLOOR_NORMAL_Z_SIGN = 1.0
_FLOOR_TYPES = ("FLOOR",)
_CEILING_TYPES = ("ROOF", "CEILING", "ROOFCEILING")
LAST_ORIENTATION_STATS: dict = {}


def _horizontal_level_polygon(surf):
    ring = [tuple(p) for p in surf.coords]
    if len(ring) < 3:
        return None
    zs = [p[2] for p in ring]
    if max(zs) - min(zs) > HORIZONTAL_LEVEL_TOLERANCE_M:
        return None
    poly = Polygon([(p[0], p[1]) for p in ring])
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return None
    return sum(zs) / len(zs), poly


def _exposed_between_zones(bsds) -> list[str]:
    levels = []
    for surf in bsds:
        zone = getattr(surf, "Zone_Name", None)
        if zone is None:
            continue
        level = _horizontal_level_polygon(surf)
        if level is not None:
            levels.append((str(surf.Name), str(zone).upper(), level[0], str(surf.Outside_Boundary_Condition).upper(), level[1]))
    found = []
    for name, zone, z, obc, poly in levels:
        if obc not in _OUTSIDE_CONDITIONS:
            continue
        for other_name, other_zone, other_z, _obc, other_poly in levels:
            if other_zone == zone or abs(other_z - z) > HORIZONTAL_LEVEL_TOLERANCE_M:
                continue
            if poly.intersects(other_poly) and poly.intersection(other_poly).area > EXPOSED_BETWEEN_ZONES_MIN_OVERLAP_M2:
                found.append(name)
                break
    return found


def _fix_horizontal_orientation(idf) -> int:
    fixed = 0
    fens = []
    try:
        fens = list(idf.idfobjects["FENESTRATIONSURFACE:DETAILED"])
    except KeyError:
        pass
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        kind = str(surf.Surface_Type).upper()
        if kind not in _FLOOR_TYPES and kind not in _CEILING_TYPES:
            continue
        ring = [tuple(p) for p in surf.coords]
        if len(ring) < 3 or max(p[2] for p in ring) - min(p[2] for p in ring) > HORIZONTAL_LEVEL_TOLERANCE_M:
            continue
        nz = _newell_normal(ring)[2]
        if abs(nz) < 1e-9:
            continue
        want = FLOOR_NORMAL_Z_SIGN if kind in _FLOOR_TYPES else -FLOOR_NORMAL_Z_SIGN
        if nz * want > 0:
            continue
        surf.setcoords(list(reversed(ring)))
        for fen in fens:
            if str(fen.Building_Surface_Name).upper() == str(surf.Name).upper():
                fen.setcoords(list(reversed([tuple(p) for p in fen.coords])))
        fixed += 1
    LAST_ORIENTATION_STATS["orientation_fixed"] = LAST_ORIENTATION_STATS.get("orientation_fixed", 0) + fixed
    return fixed


def ep_geometry_preflight(idf) -> list[tuple[str, str]]:
    bsds = list(idf.idfobjects["BUILDINGSURFACE:DETAILED"])
    by_name = {str(s.Name).upper(): s for s in bsds}
    eff = {name: _ep_effective_ring([tuple(p) for p in s.coords]) for name, s in by_name.items()}
    found = []
    for name, surf in by_name.items():
        ring = eff[name]
        if len(ring) < 3 or _ring_area_m2(ring) < DEGENERATE_ZERO_AREA_M2:
            found.append((str(surf.Name), "ZERO_AREA"))
        if str(getattr(surf, "Outside_Boundary_Condition", "")).upper() != "SURFACE":
            continue
        partner = str(getattr(surf, "Outside_Boundary_Condition_Object", "") or "").upper()
        if partner not in by_name:
            found.append((str(surf.Name), "NO_PARTNER"))
        elif len(eff[partner]) != len(ring):
            found.append((str(surf.Name), "VERTEX_MISMATCH"))
    found.extend((name, "EXPOSED_BETWEEN_ZONES") for name in _exposed_between_zones(bsds))
    return found


def _remove_degenerate_surfaces(idf) -> tuple[int, float]:
    import logging

    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    by_name, groups = _interzone_groups(bsds)
    doomed = set()
    for name, surf in by_name.items():
        ring = [tuple(p) for p in surf.coords]
        cleaned = _ep_effective_ring(ring)
        if len(cleaned) < 3 or _ring_area_m2(cleaned) < DEGENERATE_DROP_AREA_M2:
            doomed.add(name)
            continue
        if len(cleaned) != len(ring) and _plane_basis(cleaned) is not None:
            surf.setcoords(cleaned)
    for names in groups:
        if any(n in doomed for n in names):
            doomed.update(names)
    for name, surf in by_name.items():
        if name in doomed or str(getattr(surf, "Outside_Boundary_Condition", "")).upper() != "SURFACE":
            continue
        partner = by_name.get(str(getattr(surf, "Outside_Boundary_Condition_Object", "") or "").upper())
        if partner is None or str(partner.Name).upper() in doomed or name > str(partner.Name).upper():
            continue
        ring = [tuple(p) for p in surf.coords]
        other = [tuple(p) for p in partner.coords]
        if len(_ep_effective_ring(ring)) != len(_ep_effective_ring(other)):
            partner.setcoords(list(reversed(ring)))
    area = sum(_ring_area_m2([tuple(p) for p in by_name[n].coords]) for n in doomed)
    fens = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    for fen in list(fens):
        if str(fen.Building_Surface_Name).upper() in doomed:
            idf.removeidfobject(fen)
    for name in doomed:
        idf.removeidfobject(by_name[name])
    if doomed:
        logging.getLogger(__name__).info("remove_degenerate_surfaces removed=%d area_m2=%.3e", len(doomed), area)
    return len(doomed), area


HIDDEN_PLANE_TOLERANCE_M = 0.01
HIDDEN_FACING_DOT = -0.99
HIDDEN_MIN_OVERLAP_M2 = 1e-6
_OUTSIDE_CONDITIONS = ("OUTDOORS", "GROUND")


def _surface_records_from_text(text: str) -> list[dict]:
    records = []
    for block in re.split(r"(?im)^\s*BUILDINGSURFACE:DETAILED\s*,", text)[1:]:
        body = block.split(";", 1)[0]
        fields = [line.split("!", 1)[0].strip().rstrip(",").strip() for line in body.splitlines()[1:]]
        if len(fields) < 11:
            continue
        nums = []
        for f in fields[11:]:
            if f == "":
                continue
            nums.append(float(f))
        ring = [tuple(nums[i:i + 3]) for i in range(0, len(nums) - 2, 3)]
        records.append({
            "name": fields[0], "stype": fields[1].upper(), "zone": fields[3].upper(),
            "obc": fields[5].upper(), "ring": ring,
        })
    return records


def _surface_records_from_idf(idf) -> list[dict]:
    return [
        {
            "name": str(s.Name), "stype": str(s.Surface_Type).upper(), "zone": str(s.Zone_Name).upper(),
            "obc": str(s.Outside_Boundary_Condition).upper(), "ring": [tuple(p) for p in s.coords],
        }
        for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    ]


def _hidden_pairs(records: list[dict]) -> dict[int, list]:
    import numpy as np

    count = len(records)
    normals = np.zeros((count, 3))
    centroids = np.zeros((count, 3))
    areas = np.zeros(count)
    for i, rec in enumerate(records):
        ring = rec["ring"]
        if len(ring) < 3:
            continue
        nx, ny, nz = _newell_normal(ring)
        norm = (nx * nx + ny * ny + nz * nz) ** 0.5
        areas[i] = 0.5 * norm
        if norm > 0.0:
            normals[i] = (nx / norm, ny / norm, nz / norm)
        centroids[i] = np.mean(np.asarray(ring), axis=0)
    pairs: dict[int, list] = {}
    for i, rec in enumerate(records):
        if rec["obc"] not in _OUTSIDE_CONDITIONS or areas[i] <= 0.0:
            continue
        ring = rec["ring"]
        offsets = np.abs((centroids - np.asarray(ring[0])) @ normals[i])
        near = np.nonzero(
            (normals @ normals[i] < HIDDEN_FACING_DOT) & (offsets < 50.0 * HIDDEN_PLANE_TOLERANCE_M) & (areas > 0.0)
        )[0]
        project = _plane_frame(ring)
        if project is None:
            continue
        origin = np.asarray(ring[0])
        mine = _polygon_in_frame(ring, project)
        for j in near:
            other = records[j]
            if other["zone"] == rec["zone"]:
                continue
            verts = np.asarray(other["ring"])
            if np.max(np.abs((verts - origin) @ normals[i])) > HIDDEN_PLANE_TOLERANCE_M:
                continue
            inter = mine.intersection(_polygon_in_frame(other["ring"], project))
            if inter.area > HIDDEN_MIN_OVERLAP_M2:
                pairs.setdefault(i, []).append((int(j), inter))
    return pairs


def _hidden_overlaps(records: list[dict]) -> dict[str, float]:
    from shapely.ops import unary_union

    hidden = {}
    for i, found in _hidden_pairs(records).items():
        hidden[records[i]["name"]] = float(unary_union([inter for _j, inter in found]).area)
    return hidden


def hidden_outdoor_area(idf_path) -> dict:
    records = _surface_records_from_text(Path(idf_path).read_text(encoding="utf-8", errors="replace"))
    hidden = _hidden_overlaps(records)
    by_name = {r["name"]: r for r in records}
    result = {
        "hidden_outdoor_m2": 0.0, "hidden_ground_m2": 0.0, "surface_count": len(records),
        "outdoor_wall_m2": 0.0, "roof_m2": 0.0, "ground_floor_m2": 0.0, "outdoor_floor_m2": 0.0,
        "outdoor_ceiling_m2": 0.0, "hidden_names": sorted(hidden),
    }
    for name, area in hidden.items():
        key = "hidden_ground_m2" if by_name[name]["obc"] == "GROUND" else "hidden_outdoor_m2"
        result[key] += area
    for rec in records:
        if len(rec["ring"]) < 3:
            continue
        area = _ring_area_m2(rec["ring"])
        stype, obc = rec["stype"], rec["obc"]
        if stype == "WALL" and obc == "OUTDOORS":
            result["outdoor_wall_m2"] += area
        elif stype == "ROOF" and obc == "OUTDOORS":
            result["roof_m2"] += area
        elif stype == "FLOOR" and obc == "GROUND":
            result["ground_floor_m2"] += area
        elif stype == "FLOOR" and obc == "OUTDOORS":
            result["outdoor_floor_m2"] += area
        elif stype == "CEILING" and obc == "OUTDOORS":
            result["outdoor_ceiling_m2"] += area
    return result


OVERLAP_TOLERANCE = 1.01
OVERLAP_PAIR_MIN_M2 = 0.1
OVERLAP_FALLBACK_NOTE = "room_layout_overlap_fallback"


def _storey_floor_overlap(records: list[dict]) -> dict:
    from shapely.geometry import Polygon as _Polygon
    from shapely.ops import unary_union

    storeys: dict[float, dict[str, list]] = {}
    for rec in records:
        ring = rec["ring"]
        if rec["stype"] != "FLOOR" or len(ring) < 3:
            continue
        poly = _Polygon([(p[0], p[1]) for p in ring])
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            continue
        z = round(sum(p[2] for p in ring) / len(ring), 1)
        storeys.setdefault(z, {}).setdefault(rec["zone"], []).append(poly)
    out = {"floor_sum_m2": 0.0, "floor_union_m2": 0.0, "overlap_pairs": 0, "worst_ratio": 1.0, "storeys": {}}
    for z, zones in storeys.items():
        merged = {name: unary_union(polys) for name, polys in zones.items()}
        sum_m2 = sum(g.area for g in merged.values())
        union_m2 = unary_union(list(merged.values())).area
        names = list(merged)
        pairs = sum(
            1
            for i in range(len(names))
            for j in range(i + 1, len(names))
            if merged[names[i]].intersection(merged[names[j]]).area > OVERLAP_PAIR_MIN_M2
        )
        out["floor_sum_m2"] += sum_m2
        out["floor_union_m2"] += union_m2
        out["overlap_pairs"] += pairs
        out["storeys"][z] = (sum_m2, union_m2, pairs)
        if union_m2 > 0.0:
            out["worst_ratio"] = max(out["worst_ratio"], sum_m2 / union_m2)
    return out


def zone_floor_overlap(idf_path) -> dict:
    records = _surface_records_from_text(Path(idf_path).read_text(encoding="utf-8", errors="replace"))
    return _storey_floor_overlap(records)


def _storeys_overlap(idf) -> bool:
    return _storey_floor_overlap(_surface_records_from_idf(idf))["worst_ratio"] > OVERLAP_TOLERANCE


HIDDEN_MIN_PIECE_M2 = 0.001
CLIP_MIN_PIECE_M2 = 0.01
CLIP_OUTSIDE_TRIGGER_M2 = 1e-3
CLIP_SURFACE_TYPES = ("FLOOR", "CEILING", "ROOF", "ROOFCEILING")


def _unpair_horizontal(surf) -> None:
    surf.Outside_Boundary_Condition = "Outdoors"
    surf.Outside_Boundary_Condition_Object = ""
    surf.Sun_Exposure = "SunExposed"
    surf.Wind_Exposure = "WindExposed"
    if str(surf.Surface_Type).upper() in ("CEILING", "ROOFCEILING"):
        surf.Surface_Type = "Roof"


def _clip_zone_horizontals_to_own_polygon(idf, dwelling_polygons) -> dict:
    stats = {"surfaces_clipped": 0, "pieces_added": 0, "pieces_dropped": 0, "unpaired": 0}
    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    hosts = _fenestration_hosts(idf)
    names = {str(s.Name).upper() for s in bsds}
    own = {str(k).upper(): v for k, v in dwelling_polygons.items()}
    touched = set()
    for surf in list(bsds):
        if str(surf.Surface_Type).upper() not in CLIP_SURFACE_TYPES:
            continue
        zone_poly = own.get(str(surf.Zone_Name).upper())
        if zone_poly is None or str(surf.Name).upper() in hosts:
            continue
        ring = [tuple(p) for p in surf.coords]
        if len(ring) < 3:
            continue
        poly = Polygon([(p[0], p[1]) for p in ring])
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            continue
        inside = poly.intersection(zone_poly)
        if poly.area - inside.area <= CLIP_OUTSIDE_TRIGGER_M2:
            continue
        z = sum(p[2] for p in ring) / len(ring)
        clockwise = not Polygon([(p[0], p[1]) for p in ring]).exterior.is_ccw
        parts = [g for g in _polygon_parts(inside) if g.area >= CLIP_MIN_PIECE_M2]
        stats["surfaces_clipped"] += 1
        touched.add(str(surf.Name).upper())
        partner = str(surf.Outside_Boundary_Condition_Object).upper()
        if str(surf.Outside_Boundary_Condition).upper() == "SURFACE" and partner:
            touched.add(partner)
        if not parts:
            idf.removeidfobject(surf)
            stats["pieces_dropped"] += 1
            continue
        parts.sort(key=lambda g: -g.area)
        for index, part in enumerate(parts):
            part = orient(Polygon(part.exterior), -1.0 if clockwise else 1.0)
            new_ring = [(x, y, z) for x, y in list(part.exterior.coords)[:-1]]
            if index == 0:
                surf.setcoords(new_ring)
                continue
            piece = idf.copyidfobject(surf)
            name = f"{surf.Name}_C{index}"
            while name.upper() in names:
                name += "x"
            names.add(name.upper())
            piece.Name = name
            piece.setcoords(new_ring)
            touched.add(name.upper())
            stats["pieces_added"] += 1
    for surf in bsds:
        if str(surf.Outside_Boundary_Condition).upper() != "SURFACE":
            continue
        if str(surf.Name).upper() in touched or str(surf.Outside_Boundary_Condition_Object).upper() in touched:
            _unpair_horizontal(surf)
            stats["unpaired"] += 1
    return stats


def _own_polygons_by_zone(zones) -> dict:
    out = {}
    for z in zones:
        coords = z.get("coords_m")
        name = str(z.get("name", ""))
        if not coords or z.get("fallback_to_bbox"):
            continue
        if "_dwelling_" not in name and not name.endswith("_circulation"):
            continue
        poly = Polygon([(c[0], c[1]) for c in coords])
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            out[name] = poly
    return out


RUN_OUTLINE_TOLERANCE_M2 = 0.01


def _zone_outline(zone):
    poly = Polygon([(c[0], c[1]) for c in zone["coords_m"]])
    return poly if poly.is_valid else poly.buffer(0)


def _storey_runs(group) -> list:
    runs = []
    for zone in group:
        index = _surfaces._get_floor_idx(zone["name"]) or 0
        if runs:
            last = runs[-1]
            same = _zone_outline(last[-1][1]).symmetric_difference(_zone_outline(zone)).area <= RUN_OUTLINE_TOLERANCE_M2
            if index == last[-1][0] + 1 and same:
                last.append((index, zone))
                continue
        runs.append([(index, zone)])
    return runs


def _extrude_zone_groups_per_storey(idf, valid_zones, _exc) -> None:
    for key, group_iter in groupby(valid_zones, key=_surfaces._group_key):
        group = list(group_iter)
        group.sort(key=lambda z: (_surfaces._get_floor_idx(z["name"]) or 0))
        base_name = f"{key[0]}_{key[1]}"
        runs = _storey_runs(group)
        whole = len(runs) == 1 and runs[0][0][0] == 0
        for run in runs:
            first_index = run[0][0]
            members = [z for _i, z in run]
            m = len(members)
            first = members[0]
            floor_h = first["height_m"]
            for member in members:
                if int(member.get("storey_span", 1) or 1) != 1:
                    raise AssertionError(f"zone {member['name']} has storey_span {member.get('storey_span')}, expected 1")
            run_height = sum(z["height_m"] for z in members)
            block_name = base_name if whole else f"{base_name}_a{first_index}"
            try:
                idf.add_block(name=block_name, coordinates=first["coords_m"], height=run_height, num_stories=m)
                fallback = False
            except _exc:
                bbox_coords = list(first["floor_polygon"].minimum_rotated_rectangle.exterior.coords)[:-1]
                try:
                    idf.add_block(name=block_name, coordinates=bbox_coords, height=run_height, num_stories=m)
                    fallback = True
                    _surfaces.logger.warning("block %s fell back to bbox extrusion", block_name)
                except Exception:
                    _surfaces.logger.warning(
                        "block %s extrusion failed even with bbox — skipping %d zone(s)", block_name, m
                    )
                    continue
            if first_index:
                shift = first_index * floor_h
                geo_names = {f"Block {block_name} Storey {k}" for k in range(m)}
                for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
                    if surf.Zone_Name not in geo_names:
                        continue
                    surf.setcoords([(p[0], p[1], p[2] + shift) for p in surf.coords])
                    if (
                        surf.Zone_Name == f"Block {block_name} Storey 0"
                        and str(surf.Surface_Type).upper() == "FLOOR"
                    ):
                        surf.Outside_Boundary_Condition = "Outdoors"
                        surf.Outside_Boundary_Condition_Object = ""
                        surf.Sun_Exposure = "SunExposed"
                        surf.Wind_Exposure = "WindExposed"
            for storey_no, z in enumerate(members):
                _surfaces._rename_geomeppy_zone(idf, f"Block {block_name} Storey {storey_no}", z["name"])
                z["extruded"] = True
                if fallback:
                    z["fallback_to_bbox"] = True


HIDDEN_PASS_LIMIT = 60
HIDDEN_PAIRABLE_CONDITIONS = ("OUTDOORS", "GROUND", "ADIABATIC")
HIDDEN_PASS_STAT_KEYS = (
    "pairs_split", "pieces_paired", "pieces_adiabatic", "adiabatic_area_m2", "remainders_dropped",
    "whole_adiabatic", "windows_deleted", "window_area_m2",
)
LAST_HIDDEN_PASS_STATS: dict = {}


def _polygon_parts(geometry) -> list:
    return [g for g in getattr(geometry, "geoms", [geometry]) if g.geom_type == "Polygon" and not g.is_empty]


def _frame_ring_to_3d(part, basis) -> list:
    origin, u, v, _n = basis
    part = orient(part, 1.0)
    return [tuple(origin[k] + x * u[k] + y * v[k] for k in range(3)) for x, y in list(part.exterior.coords)[:-1]]


def _paired_surface_type(surface_type):
    return "Ceiling" if str(surface_type).upper() in ("ROOF", "ROOFCEILING") else surface_type


def _rehost_windows(idf, host, project, overlap_polys, pieces, stats) -> None:
    try:
        fens = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    except KeyError:
        return
    host_name = str(host.Name).upper()
    for fen in list(fens):
        if str(fen.Building_Surface_Name).upper() != host_name:
            continue
        ring = [tuple(p) for p in fen.coords]
        poly = _polygon_in_frame(ring, project) if len(ring) >= 3 else None
        target = None
        if poly is not None and not poly.is_empty:
            if not any(poly.intersection(o).area > HIDDEN_MIN_OVERLAP_M2 for o in overlap_polys):
                for name, piece_poly in pieces:
                    if piece_poly.buffer(MIRROR_COVERAGE_VERTEX_TOLERANCE_M).covers(poly):
                        target = name
                        break
        if target is None:
            stats["windows_deleted"] += 1
            stats["window_area_m2"] += 0.0 if poly is None else float(poly.area)
            idf.removeidfobject(fen)
        else:
            fen.Building_Surface_Name = target


def _split_hidden_surface(idf, surf, basis, overlap_rings, kept_parts, names, overlap_obc):
    def fresh(base):
        name = base
        while name.upper() in names:
            name += "x"
        names.add(name.upper())
        return name

    over = []
    for index, ring in enumerate(overlap_rings):
        if len(ring) < 3 or _plane_basis(ring) is None:
            over.append(None)
            continue
        piece = idf.copyidfobject(surf)
        piece.Name = fresh(f"{surf.Name}_H{index + 1}")
        piece.setcoords(ring)
        piece.Sun_Exposure = "NoSun"
        piece.Wind_Exposure = "NoWind"
        piece.Outside_Boundary_Condition = overlap_obc
        piece.Outside_Boundary_Condition_Object = ""
        if overlap_obc == "Surface":
            piece.Surface_Type = _paired_surface_type(piece.Surface_Type)
        over.append(piece)
    rest = []
    for index, part in enumerate(kept_parts):
        ring = _clean_ring_3d(_frame_ring_to_3d(part, basis))
        if len(ring) < 3 or _plane_basis(ring) is None:
            continue
        piece = idf.copyidfobject(surf)
        piece.Name = fresh(f"{surf.Name}_K{index + 1}")
        piece.setcoords(ring)
        rest.append((str(piece.Name).upper(), part))
    return over, rest


def _apply_hidden_pair(idf, a, b, inter, names, stats) -> bool:
    from shapely.ops import unary_union

    ring_a = [tuple(p) for p in a.coords]
    basis_a = _plane_basis(ring_a)
    project_a = _plane_frame(ring_a)
    if basis_a is None or project_a is None:
        return False
    parts = [g for g in _polygon_parts(inter) if g.area >= HIDDEN_MIN_PIECE_M2]
    if not parts:
        return False
    a_poly = _polygon_in_frame(ring_a, project_a)
    a_rest = _polygon_parts(a_poly.difference(unary_union(parts)))
    a_keep = [g for g in a_rest if g.area >= MIRROR_NEAR_SAME_AREA_M2]
    stats["remainders_dropped"] += len(a_rest) - len(a_keep)
    if any(p.interiors for p in parts) or any(g.interiors for g in a_keep):
        a.Outside_Boundary_Condition = "Adiabatic"
        a.Outside_Boundary_Condition_Object = ""
        a.Sun_Exposure = "NoSun"
        a.Wind_Exposure = "NoWind"
        stats["pairs_split"] += 1
        stats["whole_adiabatic"] += 1
        stats["adiabatic_area_m2"] += _ring_area_m2(ring_a)
        return True
    overlap_rings = [_clean_ring_3d(_frame_ring_to_3d(p, basis_a)) for p in parts]
    b_obc = str(getattr(b, "Outside_Boundary_Condition", "")).upper()
    ring_b = [tuple(p) for p in b.coords]
    basis_b = _plane_basis(ring_b)
    project_b = _plane_frame(ring_b)
    pair_b = b_obc in HIDDEN_PAIRABLE_CONDITIONS and basis_b is not None and project_b is not None
    b_keep = []
    b_overlap_polys = []
    if pair_b:
        b_poly = _polygon_in_frame(ring_b, project_b)
        b_overlap_polys = [_polygon_in_frame(r, project_b) for r in overlap_rings if len(r) >= 3]
        b_rest = _polygon_parts(b_poly.difference(unary_union(b_overlap_polys)))
        b_keep = [g for g in b_rest if g.area >= MIRROR_NEAR_SAME_AREA_M2]
        stats["remainders_dropped"] += len(b_rest) - len(b_keep)
        if any(g.interiors for g in b_keep):
            pair_b = False
    stats["pairs_split"] += 1
    a_over, a_rest_named = _split_hidden_surface(
        idf, a, basis_a, overlap_rings, a_keep, names, "Surface" if pair_b else "Adiabatic",
    )
    _rehost_windows(idf, a, project_a, parts, a_rest_named, stats)
    if pair_b:
        b_over, b_rest_named = _split_hidden_surface(
            idf, b, basis_b, [list(reversed(r)) for r in overlap_rings], b_keep, names, "Surface",
        )
        _rehost_windows(idf, b, project_b, b_overlap_polys, b_rest_named, stats)
        for pa, pb in zip(a_over, b_over):
            if pa is not None and pb is not None:
                pa.Outside_Boundary_Condition_Object = pb.Name
                pb.Outside_Boundary_Condition_Object = pa.Name
                stats["pieces_paired"] += 1
                continue
            for lone in (pa, pb):
                if lone is not None:
                    lone.Outside_Boundary_Condition = "Adiabatic"
                    lone.Outside_Boundary_Condition_Object = ""
                    stats["pieces_adiabatic"] += 1
        idf.removeidfobject(b)
    else:
        for pa in a_over:
            if pa is not None:
                stats["pieces_adiabatic"] += 1
                stats["adiabatic_area_m2"] += _ring_area_m2([tuple(p) for p in pa.coords])
    idf.removeidfobject(a)
    return True


def _pair_hidden_outdoor_surfaces(idf) -> dict:
    stats = {key: 0 for key in HIDDEN_PASS_STAT_KEYS}
    stats["adiabatic_area_m2"] = 0.0
    stats["window_area_m2"] = 0.0
    for _ in range(HIDDEN_PASS_LIMIT):
        objects = list(idf.idfobjects["BUILDINGSURFACE:DETAILED"])
        pairs = _hidden_pairs(_surface_records_from_idf(idf))
        if not pairs:
            break
        used = set()
        names = {str(s.Name).upper() for s in objects}
        for i in sorted(pairs):
            if i in used:
                continue
            across = sorted(
                pairs[i],
                key=lambda item: (str(objects[item[0]].Outside_Boundary_Condition).upper() == "SURFACE", -item[1].area),
            )
            for j, inter in across:
                if j in used:
                    continue
                if _apply_hidden_pair(idf, objects[i], objects[j], inter, names, stats):
                    used.update((i, j))
                    break
        if not used:
            break
    LAST_HIDDEN_PASS_STATS.clear()
    LAST_HIDDEN_PASS_STATS.update(stats)
    return stats


RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M = 0.010
RING_VERTEX_REMOVAL_PER_REMOVAL_AREA_BUDGET = 1e-3
RING_VERTEX_REMOVAL_CUMULATIVE_AREA_BUDGET = 2e-3


def _drop_redundant_ring_vertices(ring):
    """D-EU-109 a/c/f: remove every vertex ``_has_near_duplicate_vertex_surfaces``
    would flag on this ring's own edges (near-duplicate adjacent vertex, or
    near-/exactly-collinear interior angle), reading the same two frozen module
    constants -- never a second, looser copy of them. Iterates to a fixed point
    (removing one vertex can make its neighbour newly collinear), capped at the
    ring's own vertex count. A removal is refused, leaving the vertex in place,
    if its perpendicular distance to the chord joining its two neighbours exceeds
    ``RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M`` (0.010 m), or its own
    relative ring-area change exceeds ``RING_VERTEX_REMOVAL_PER_REMOVAL_AREA_BUDGET``
    (1e-3), or the ring's cumulative relative area change across every removal made
    in this call (measured against the ring's own starting area) would exceed
    ``RING_VERTEX_REMOVAL_CUMULATIVE_AREA_BUDGET`` (2e-3), or the removal would take
    the ring below 3 vertices. Criterion chosen by ``D-EU-109 f`` (``CP-2`` SIGNED,
    PLAN_eu-dwelling-division-recovery-2026-09-07.md), superseding the earlier
    ``1e-6`` relative-area-only budget.
    """
    import math

    points = list(ring)
    closed = len(points) >= 2 and tuple(points[0]) == tuple(points[-1])
    if closed:
        points = points[:-1]
    if len(points) < 3:
        return list(ring)

    def _xyz(p):
        return (p[0], p[1], p[2] if len(p) > 2 else 0.0)

    def _ring_area(pts):
        n = len(pts)
        nx = ny = nz = 0.0
        for i in range(n):
            x1, y1, z1 = _xyz(pts[i])
            x2, y2, z2 = _xyz(pts[(i + 1) % n])
            nx += (y1 - y2) * (z1 + z2)
            ny += (z1 - z2) * (x1 + x2)
            nz += (x1 - x2) * (y1 + y2)
        return math.sqrt(nx * nx + ny * ny + nz * nz) / 2.0

    def _dist3(p0, p2):
        x0, y0, z0 = _xyz(p0)
        x2, y2, z2 = _xyz(p2)
        return math.sqrt((x2 - x0) ** 2 + (y2 - y0) ** 2 + (z2 - z0) ** 2)

    def _is_redundant(p0, p1, p2):
        v1 = tuple(a - b for a, b in zip(p0, p1))
        v2 = tuple(a - b for a, b in zip(p2, p1))
        len1 = math.sqrt(sum(c * c for c in v1))
        len2 = math.sqrt(sum(c * c for c in v2))
        if len1 < NEAR_DUPLICATE_VERTEX_TOLERANCE_M or len2 < NEAR_DUPLICATE_VERTEX_TOLERANCE_M:
            return True
        cos_a = sum(a * b for a, b in zip(v1, v2)) / (len1 * len2)
        cos_a = max(-1.0, min(1.0, cos_a))
        angle_deg = math.degrees(math.acos(cos_a))
        return angle_deg > 180.0 - COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG

    initial_area = _ring_area(points)
    cumulative_delta = 0.0
    cap = len(points)
    for _ in range(cap):
        if len(points) <= 3:
            break
        removed_this_pass = False
        i = 0
        while i < len(points):
            n = len(points)
            if n <= 3:
                break
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[(i + 1) % n]
            if _is_redundant(p0, p1, p2):
                candidate = points[:i] + points[i + 1:]
                original_area = _ring_area(points)
                candidate_area = _ring_area(candidate)
                area_delta = abs(candidate_area - original_area)
                if original_area == 0.0:
                    relative_change = 0.0 if candidate_area == 0.0 else float("inf")
                else:
                    relative_change = area_delta / original_area
                chord_len = _dist3(p0, p2)
                perp_dist = (2.0 * area_delta / chord_len) if chord_len > 0.0 else 0.0
                if initial_area == 0.0:
                    cumulative_relative = 0.0 if (cumulative_delta + area_delta) == 0.0 else float("inf")
                else:
                    cumulative_relative = (cumulative_delta + area_delta) / initial_area
                if (
                    perp_dist <= RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M
                    and relative_change <= RING_VERTEX_REMOVAL_PER_REMOVAL_AREA_BUDGET
                    and cumulative_relative <= RING_VERTEX_REMOVAL_CUMULATIVE_AREA_BUDGET
                ):
                    points = candidate
                    cumulative_delta += area_delta
                    removed_this_pass = True
                    continue
            i += 1
        if not removed_this_pass:
            break

    if closed:
        points = points + [points[0]]
    return points


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


def _assign_envelope_constructions(idf, wall_construction: str, roof_construction: str, floor_construction: str) -> None:
    """FINDING 253 fix (2026-09-05): a nominal ``ROOF``/``ROOFCEILING`` surface whose

    ``Outside_Boundary_Condition == "Surface"`` is an interzone surface paired
    with a shorter neighbour's ``FLOOR`` (e.g. a 1-storey dwelling block sitting
    under a taller one) -- assigning it ``roof_construction`` while its partner
    gets ``floor_construction`` gives EnergyPlus two different-material
    single-layer constructions on the same interzone pair, which can never
    satisfy the reverse-order-materials interzone check and is a guaranteed
    ``GetSurfaceData`` Fatal. Any such surface gets ``floor_construction``
    instead, matching its partner. A true exterior roof (``Outdoors``) is
    unaffected. ``WALL`` and ``FLOOR``/``CEILING`` branches are unchanged.
    """
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        surface_type = str(surface.Surface_Type).upper()
        if surface_type == "WALL":
            surface.Construction_Name = wall_construction
        elif surface_type in ("ROOF", "ROOFCEILING"):
            obc = str(getattr(surface, "Outside_Boundary_Condition", "")).strip().upper()
            if obc == "SURFACE":
                surface.Construction_Name = floor_construction
            else:
                surface.Construction_Name = roof_construction
        elif surface_type in ("FLOOR", "CEILING"):
            surface.Construction_Name = floor_construction


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
    for zone in zones:
        coords = zone.get("coords_m")
        if coords:
            zone["coords_m"] = _drop_redundant_ring_vertices(coords)
    _frozen_extrusion = _surfaces._extrude_zone_groups
    _surfaces._extrude_zone_groups = _extrude_zone_groups_per_storey
    try:
        extrude_geometry(idf, zones, context or [])
    finally:
        _surfaces._extrude_zone_groups = _frozen_extrusion
    _clip_zone_horizontals_to_own_polygon(idf, _own_polygons_by_zone(zones))
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
    _pair_stats, _unresolved_pairs = _repair_interzone_pairs(idf)
    _drop_sliver_surfaces(idf)
    _clean_surface_rings(idf, _unresolved_pairs)
    mismatched = find_mismatched_interzone_pairs(idf)
    # FINDING 249 restricted remedy (2026-09-04): `_has_near_duplicate_vertex_surfaces`
    # only flags surfaces with a valid interzone partner (`Outside_Boundary_Condition ==
    # "Surface"` with resolvable partner). Partner-less surfaces (Ground, Outdoors,
    # Adiabatic) cannot cause an EnergyPlus interzone vertex mismatch fatal and do not
    # set `at_risk`. Any interzone-paired defect sets `at_risk = True` unconditionally.
    near_duplicate = _has_near_duplicate_vertex_surfaces(idf)
    at_risk = mismatched or near_duplicate
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
            # T15 (D-EU-58, owner 2026-09-01): T14 traced every one of the 41 sampled
            # population losses to the identical pattern -- `mismatched` (the raw
            # interzone vertex-count check) never fires, only the near-duplicate-vertex
            # heuristic does, and the one safety net wired to it (`_force_reroute_room_
            # layout_to_one_zone_per_floor`) correctly declines to help for one of two
            # by-design reasons: no room-layout zones left to reroute, or a genuine
            # courtyard hole (surfaces.py:640-696, unedited -- T14 confirmed that
            # function is correct per its own docstring). That is already-valid geometry
            # being discarded, not a defect being masked. When the reroute declined
            # (`did_reroute is False`) and the raw mismatch check never fired at any
            # point (`mismatched` is the same variable pre- and post-reroute-attempt
            # when no reroute ran), retain the building's already-emitted geometry as-is
            # instead of losing it outright, and disclose the tolerance on every zone so
            # the district-campaign manifest can surface it (hard rule 4: fail closed and
            # name the reason -- this is a disclosed tolerance, not a relabelled refusal).
            # Any building where `mismatched` is truthy at any point still raises exactly
            # as before this change; the `did_reroute is True` success branch is
            # untouched.
            if not mismatched:
                for _z in zones:
                    _z["fallback_reason"] = "near_duplicate_vertex_tolerated_box"
            else:
                raise RuntimeError(
                    f"interzone_vertex_mismatch_unresolved: mismatched={mismatched} "
                    f"near_duplicate_vertex={residual_near_dup}"
                )
    apply_adiabatic_party_walls(idf, context or [])
    write_zone_volumes(idf, zones)
    LAST_ORIENTATION_STATS.clear()
    _fix_horizontal_orientation(idf)
    _pair_hidden_outdoor_surfaces(idf)
    _clean_surface_rings(idf, _unresolved_pairs)
    if _storeys_overlap(idf):
        if not _force_reroute_room_layout_to_one_zone_per_floor(idf, zones, "zone_floor_overlap"):
            raise RuntimeError("zone_floor_overlap_unresolved: flats overlap on a storey and no one-zone-per-floor fallback exists")
        idf.intersect_match()
        _repair_roof_roof_pairs(idf)
        _repair_mismatched_horizontal_pairs(idf)
        _pair_interfloor_surfaces(idf)
        _pair_stats, _unresolved_pairs = _repair_interzone_pairs(idf)
        _drop_sliver_surfaces(idf)
        _clean_surface_rings(idf, _unresolved_pairs)
        apply_adiabatic_party_walls(idf, context or [])
        write_zone_volumes(idf, zones)
        _fix_horizontal_orientation(idf)
        _pair_hidden_outdoor_surfaces(idf)
        _clean_surface_rings(idf, _unresolved_pairs)
        for _z in zones:
            _z["generation_status_note"] = OVERLAP_FALLBACK_NOTE

    _removed, _removed_area = _remove_degenerate_surfaces(idf)
    LAST_DEGENERATE_STATS.clear()
    LAST_DEGENERATE_STATS.update(degenerate_removed=_removed, degenerate_area_m2=_removed_area)
    if ep_geometry_preflight(idf):
        if not _force_reroute_room_layout_to_one_zone_per_floor(idf, zones, "ep_geometry_preflight"):
            raise RuntimeError("ep_geometry_preflight_unresolved: degenerate surfaces and no one-zone-per-floor fallback exists")
        idf.intersect_match()
        _repair_roof_roof_pairs(idf)
        _repair_mismatched_horizontal_pairs(idf)
        _pair_interfloor_surfaces(idf)
        _pair_stats, _unresolved_pairs = _repair_interzone_pairs(idf)
        _drop_sliver_surfaces(idf)
        _clean_surface_rings(idf, _unresolved_pairs)
        apply_adiabatic_party_walls(idf, context or [])
        write_zone_volumes(idf, zones)
        _fix_horizontal_orientation(idf)
        _pair_hidden_outdoor_surfaces(idf)
        _clean_surface_rings(idf, _unresolved_pairs)
        _remove_degenerate_surfaces(idf)
        if ep_geometry_preflight(idf):
            raise RuntimeError("ep_geometry_preflight_unresolved: degenerate surfaces remain after one-zone-per-floor fallback")
        for _z in zones:
            _z["generation_status_note"] = PREFLIGHT_FALLBACK_NOTE

    wall_construction = _envelope_construction(idf, record, "wall")
    roof_construction = _envelope_construction(idf, record, "roof")
    floor_construction = _envelope_construction(idf, record, "floor")
    _assign_envelope_constructions(idf, wall_construction, roof_construction, floor_construction)
    normalise_surface_orientation(idf)
    add_tabula_windows(idf, record)

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
