"""M8: Four European 3D Neighbourhoods GPU Simulation & EU-11 Parity Verification.

Compiles the four EU-11 European residential neighbourhoods directly from their
3D multi-dwelling layout JSONs, TABULA archetype registries, district-wide 3D
neighbour context (party walls + 20 m exterior ray-traced shading), and exact
SHA-256-pinned EPW weather files into the unified flat-CSR CUDA engine
(``GeneralBatch`` + ``run_general_cuda``), then compares every building and
district pooled EUI against the published EU-11 EnergyPlus 23.1 results.

Districts:
  1. Madrid Berruguete      (ES-MAD-BERRUGUETE)
  2. Lyon Croix-Rousse      (FR-LYO-HAUTCOEURPENTES)
  3. London St Dunstan's    (GB-LDN-STDUNSTANS)
  4. Bologna Galvani 2      (IT-BOL-GALVANI2)
"""
from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.strtree import STRtree

from openubem.gpusim.backends.general_cuda import run_general_cuda
from openubem.gpusim.ctf import LayerSpec, ModalConductionModel, build_modal_conduction
from openubem.gpusim.general_model import (
    BOUND_ADIABATIC,
    BOUND_GROUND,
    BOUND_INTMASS,
    BOUND_OUTDOORS,
    BOUND_SURFACE,
    BOUND_WINDOW,
    SURF_FLOOR,
    SURF_INTMASS,
    SURF_ROOF,
    SURF_WALL,
    SURF_WINDOW,
    pack_compiled_general_buildings,
)
from openubem.gpusim.physics.solar import simple_glazing_normal_optics
from openubem.gpusim.physics.window import simple_glazing_layer_conductance
from openubem.gpusim.shading import compute_exterior_shading
from openubem.gpusim.weather import WeatherSeries, load_epw_weather
from openubem.idf.european_controls import european_air_change_per_hour
from openubem.idf.european_windows import MIN_WINDOW_AREA_M2, window_record

ROOT = Path(__file__).resolve().parents[2]
EU11_EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
EU11_PER_HOME = (
    ROOT
    / "docs"
    / "docs_ACTIVE"
    / "europeanLocations"
    / "results"
    / "EU11_results_2026-10-08_per_home.csv"
)
EU11_SUMMARY = (
    ROOT
    / "docs"
    / "docs_ACTIVE"
    / "europeanLocations"
    / "results"
    / "EU11_results_2026-10-08_summary.csv"
)
ARCHETYPE_DIR = ROOT / "openubem" / "data" / "construction"
WEATHER_DIR = ROOT / "openubem" / "data" / "weather"
OUT_DIR = ROOT / "openubem" / "outputs"

# Exact EU-11 constants (scripts/run_eu_s2_campaign.py + openubem/idf/european_*.py)
STEPS_PER_HOUR = 12
DT_S = 3600.0 / STEPS_PER_HOUR
TERRAIN_CITY_IDX = 2  # City: alpha=0.33, delta=460
GROUND_TEMP_C = 18.0  # EnergyPlus default when Site:GroundTemperature:BuildingSurface omitted
EUROPEAN_CONTEXT_RADIUS_M = 20.0
EUROPEAN_ADIABATIC_TOLERANCE_M = 0.30
BASE_GAIN_W_M2 = 3.0  # Step-8 f=0 baseline, 100% convective
ROUGHNESS_MEDIUM_ROUGH = 1.52
MASS_THICKNESS_M = 0.10
MASS_CONDUCTIVITY = 1.0
MASS_DENSITY = 1800.0
MASS_CP = 900.0
MASS_CAPACITY_PER_M2 = MASS_THICKNESS_M * MASS_DENSITY * MASS_CP  # 162,000 J/m2K


@dataclass(frozen=True)
class DistrictSpec:
    code: str
    label: str
    country: str
    primary_dir: str
    fallback_dirs: tuple[str, ...]
    epw_name: str
    tabula_file: str


DISTRICTS: dict[str, DistrictSpec] = {
    "ES-MAD-BERRUGUETE": DistrictSpec(
        code="ES-MAD-BERRUGUETE",
        label="Madrid Berruguete",
        country="ES",
        primary_dir="ES-MAD-BERRUGUETE_win_2026-10-06",
        fallback_dirs=("ES-MAD-BERRUGUETE_layouts_2026-09-08",),
        epw_name="es_madrid_2009_2010_y2010.epw",
        tabula_file="tabula_archetypes_es.json",
    ),
    "FR-LYO-HAUTCOEURPENTES": DistrictSpec(
        code="FR-LYO-HAUTCOEURPENTES",
        label="Lyon Hauts de Croix-Rousse",
        country="FR",
        primary_dir="FR-LYO-HAUTCOEURPENTES_recut_2026-09-08",
        fallback_dirs=("FR-LYO-HAUTCOEURPENTES",),
        epw_name="fr_lyon_bron_2023_era5.epw",
        tabula_file="tabula_archetypes_fr.json",
    ),
    "GB-LDN-STDUNSTANS": DistrictSpec(
        code="GB-LDN-STDUNSTANS",
        label="London St Dunstan's",
        country="GB",
        primary_dir="GB-LDN-STDUNSTANS_win_2026-10-06",
        fallback_dirs=(),
        epw_name="uk_london_2014_2015_y2015.epw",
        tabula_file="tabula_archetypes_gb.json",
    ),
    "IT-BOL-GALVANI2": DistrictSpec(
        code="IT-BOL-GALVANI2",
        label="Bologna Galvani 2",
        country="IT",
        primary_dir="IT-BOL-GALVANI2_win_2026-10-06",
        fallback_dirs=("IT-BOL-GALVANI2_layouts_2026-09-08",),
        epw_name="it_bologna_2013_2014_y2014.epw",
        tabula_file="tabula_archetypes_it.json",
    ),
}


def _clean_2d_polygon(coords_raw: list[list[float]]) -> Polygon | None:
    pts = [(float(p[0]), float(p[1])) for p in coords_raw]
    if len(pts) < 3:
        return None
    poly = Polygon(pts)
    if not poly.is_valid:
        poly = poly.buffer(0.0)
    if poly.is_empty:
        return None
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    if poly.geom_type != "Polygon" or poly.area < 0.05:
        return None
    # 5 cm simplification removes OSM digitization micro-jogs while conserving area/perimeter (<0.1%)
    simp = poly.simplify(0.05, preserve_topology=True)
    if simp.is_valid and not simp.is_empty and simp.geom_type == "Polygon" and simp.area >= 0.05:
        poly = simp
    return orient(poly, sign=1.0)


def _ring_edges(poly: Polygon) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    coords = list(poly.exterior.coords)
    edges = []
    for i in range(len(coords) - 1):
        p0, p1 = coords[i], coords[i + 1]
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) >= 0.02:
            edges.append(((float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1]))))
    return edges


def _make_local_wall_quad(
    p0: tuple[float, float],
    p1: tuple[float, float],
    z0: float,
    z1: float,
    ox: float,
    oy: float,
) -> np.ndarray:
    """UpperLeftCorner CCW vertical quad in local coordinates."""
    return np.array(
        [
            [p0[0] - ox, p0[1] - oy, z1],
            [p0[0] - ox, p0[1] - oy, z0],
            [p1[0] - ox, p1[1] - oy, z0],
            [p1[0] - ox, p1[1] - oy, z1],
        ],
        dtype=np.float64,
    )


def _scaled_window_quad(quad: np.ndarray, share: float) -> np.ndarray:
    factor = math.sqrt(max(0.0, min(1.0, share)))
    centre = np.mean(quad, axis=0, keepdims=True)
    return centre + factor * (quad - centre)


def _make_horizontal_verts(
    poly: Polygon, z: float, ox: float, oy: float, upward: bool
) -> np.ndarray:
    ring = list(poly.exterior.coords)[:-1]
    if not upward:
        ring = list(reversed(ring))
    return np.array([[p[0] - ox, p[1] - oy, z] for p in ring], dtype=np.float64)


def _build_archetype_cache(
    tabula_path: Path, country: str
) -> dict[str, dict[str, Any]]:
    """Precompute ModalConductionModels, glazing optics, and TABULA controls per archetype."""
    raw = json.loads(tabula_path.read_text(encoding="utf-8"))["records"]
    # Shared EU_InternalMass modal conduction model (0.10 m, k=1.0, rho=1800, c=900)
    im_modal = build_modal_conduction(
        [
            LayerSpec(
                name="EU_InternalMass_Material",
                is_nomass=False,
                r_value=MASS_THICKNESS_M / MASS_CONDUCTIVITY,
                thickness=MASS_THICKNESS_M,
                conductivity=MASS_CONDUCTIVITY,
                density=MASS_DENSITY,
                specific_heat=MASS_CP,
            )
        ],
        dt_sec=DT_S,
        construction_name="EU_InternalMass_Construction",
    )
    cache: dict[str, dict[str, Any]] = {}
    for rec in raw:
        aid = str(rec["archetype_id"])
        f_red = float(rec["f_red_temp"])
        delta_u = float(rec["delta_u_tb_w_m2k"])
        modals: dict[str, ModalConductionModel] = {"intmass": im_modal}
        for comp in ("wall", "roof", "floor"):
            u_eff = max((float(rec[f"u_{comp}_w_m2k"]) + delta_u) * f_red, 1.0e-5)
            modals[comp] = build_modal_conduction(
                [
                    LayerSpec(
                        name=f"EU_{comp}_NoMass",
                        is_nomass=True,
                        r_value=1.0 / u_eff,
                    )
                ],
                dt_sec=DT_S,
                construction_name=f"EU_{comp}_Construction",
            )
        wr = window_record(aid, country=country)
        u_win = float(wr["u"])
        shgc = float(wr["shgc"])
        scon = float(simple_glazing_layer_conductance(u_win, xp=np))
        t_n, _, a_n = simple_glazing_normal_optics(u_win, shgc)
        t_norm = float(t_n)
        a_norm = float(a_n)
        cache[aid] = {
            "record": rec,
            "modals": modals,
            "ach": european_air_change_per_hour(rec),
            "theta_i_c": float(rec["theta_i_c"]),
            "c_m_wh_m2k": float(rec["c_m_wh_m2k"]),
            "win_share": float(wr["share"]),
            "win_tuple": (scon, t_norm, a_norm, 0.887 * t_norm, 0.946 * a_norm),
        }
    return cache


def _load_district_layouts(spec: DistrictSpec) -> dict[str, dict[str, Any]]:
    """Load all non-empty 3D layout JSONs in the district (primary + fallbacks)."""
    dirs = [EU11_EVIDENCE / spec.primary_dir / "layouts"] + [
        EU11_EVIDENCE / d / "layouts" for d in spec.fallback_dirs
    ]
    layouts: dict[str, dict[str, Any]] = {}
    for ld in dirs:
        if not ld.exists():
            continue
        files = list(ld.rglob("*.json"))

        def _read(p: Path) -> tuple[str, dict[str, Any]] | None:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if not obj.get("floors"):
                return None
            return str(obj["building_id"]), obj

        with ThreadPoolExecutor(max_workers=12) as pool:
            for item in pool.map(_read, files):
                if item is not None and item[0] not in layouts:
                    layouts[item[0]] = item[1]
    return layouts


def _build_district_context_index(
    layouts: dict[str, dict[str, Any]]
) -> tuple[list[str], list[Polygon], list[Polygon], list[float], STRtree]:
    """Build 2D footprint polygons, buffered party-wall polygons, heights, and STRtree."""
    bids: list[str] = []
    footprints: list[Polygon] = []
    mrr_bufs: list[Polygon] = []
    heights: list[float] = []

    for bid, obj in layouts.items():
        fls = obj.get("floors", [])
        if not fls:
            continue
        polys = []
        max_z = 0.0
        for fl in fls:
            for z in fl.get("zones", []):
                max_z = max(max_z, float(z.get("z_ceiling", 0.0)))
        for z in fls[0].get("zones", []):
            p = _clean_2d_polygon(z.get("coords_m", []))
            if p is not None:
                polys.append(p)
        if not polys or max_z <= 0.1:
            continue
        fp = unary_union(polys)
        if fp.is_empty:
            continue
        if fp.geom_type == "MultiPolygon":
            fp = max(fp.geoms, key=lambda g: g.area)
        if fp.geom_type != "Polygon":
            continue
        fp_simp = fp.simplify(0.15, preserve_topology=True)
        if fp_simp.is_valid and not fp_simp.is_empty and fp_simp.geom_type == "Polygon":
            fp = orient(fp_simp, sign=1.0)
        else:
            fp = orient(fp, sign=1.0)
        # Match EU-11 apply_adiabatic_party_walls: buffer neighbour minimum_rotated_rectangle
        bids.append(bid)
        footprints.append(fp)
        mrr_bufs.append(fp.minimum_rotated_rectangle.buffer(EUROPEAN_ADIABATIC_TOLERANCE_M))
        heights.append(max_z)

    tree = STRtree(footprints)
    return bids, footprints, mrr_bufs, heights, tree


def _build_occluders_for_building(
    target_bid: str,
    target_fp: Polygon,
    ox: float,
    oy: float,
    ctx_bids: list[str],
    ctx_fps: list[Polygon],
    ctx_heights: list[float],
    tree: STRtree,
) -> list[np.ndarray]:
    """Build 3D neighbour wall quads + roof polygons within 20 m radius in local XY."""
    query_geom = target_fp.buffer(EUROPEAN_CONTEXT_RADIUS_M)
    cand_idxs = tree.query(query_geom)
    occluders: list[np.ndarray] = []
    for ci in cand_idxs:
        idx = int(ci)
        if ctx_bids[idx] == target_bid:
            continue
        nb_fp = ctx_fps[idx]
        if target_fp.distance(nb_fp) > EUROPEAN_CONTEXT_RADIUS_M:
            continue
        h_nb = ctx_heights[idx]
        edges = _ring_edges(nb_fp)
        for p0, p1 in edges:
            occluders.append(_make_local_wall_quad(p0, p1, 0.0, h_nb, ox, oy))
        # Roof cap for completeness (low neighbours shading overhangs/setbacks)
        if len(edges) >= 3:
            occluders.append(_make_horizontal_verts(nb_fp, h_nb, ox, oy, upward=True))
    return occluders


def _split_uncovered_intervals(
    edge_len: float, covered: list[tuple[float, float]], min_len: float = 0.05
) -> list[tuple[float, float]]:
    if not covered:
        return [(0.0, edge_len)] if edge_len >= min_len else []
    merged: list[tuple[float, float]] = []
    for a, b in sorted(covered):
        if not merged or a > merged[-1][1] + 1.0e-4:
            merged.append((a, b))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
    gaps: list[tuple[float, float]] = []
    cur = 0.0
    for a, b in merged:
        if a - cur >= min_len:
            gaps.append((cur, a))
        cur = max(cur, b)
    if edge_len - cur >= min_len:
        gaps.append((cur, edge_len))
    return gaps


def _compile_layout_building(
    bid: str,
    archetype_id: str,
    layout: dict[str, Any],
    arch_info: dict[str, Any],
    ctx_bids: list[str],
    ctx_fps: list[Polygon],
    ctx_bufs: list[Polygon],
    ctx_heights: list[float],
    tree: STRtree,
    bid_to_ctx_idx: dict[str, int],
) -> tuple[dict[str, Any], list[np.ndarray], float, float]:
    """Compile one 3D multi-dwelling layout JSON into a GeneralBatch building dict.

    Returns ``(compiled_dict, occluder_polys_local, outdoor_wall_m2, window_m2)``.
    """
    floors = sorted(layout["floors"], key=lambda fl: float(fl["zones"][0]["z_floor"]))
    modals = arch_info["modals"]
    ach = arch_info["ach"]
    theta_i_c = arch_info["theta_i_c"]
    c_m = arch_info["c_m_wh_m2k"]
    win_share = arch_info["win_share"]
    win_tuple = arch_info["win_tuple"]

    # Local XY origin for float32 ray-tracing precision
    ctx_i = bid_to_ctx_idx.get(bid, -1)
    if ctx_i >= 0:
        target_fp = ctx_fps[ctx_i]
        c_pt = target_fp.centroid
        ox, oy = float(c_pt.x), float(c_pt.y)
    else:
        p0_raw = floors[0]["zones"][0]["coords_m"][0]
        ox, oy = float(p0_raw[0]), float(p0_raw[1])
        target_fp = _clean_2d_polygon(floors[0]["zones"][0]["coords_m"]) or Polygon()

    # Neighbour buffered polygons for party-wall flip (within 2 m)
    nb_bufs: list[Polygon] = []
    if not target_fp.is_empty:
        for ci in tree.query(target_fp.buffer(2.0)):
            idx = int(ci)
            if ctx_bids[idx] != bid:
                nb_bufs.append(ctx_bufs[idx])
    nb_union = unary_union(nb_bufs) if nb_bufs else None

    # Parse polygons per storey; repair stacked/duplicate z_floor ranges (e.g. Lyon recut layouts)
    f2f = float(layout.get("floor_to_floor_m") or 3.0)
    raw_z0s = [float(fl["zones"][0]["z_floor"]) for fl in floors if fl.get("zones")]
    raw_hs = [
        float(fl["zones"][0]["z_ceiling"]) - float(fl["zones"][0]["z_floor"])
        for fl in floors
        if fl.get("zones")
    ]
    needs_z_fix = (len(set(round(z, 2) for z in raw_z0s)) < len(raw_z0s)) or any(
        h > f2f * 1.4 for h in raw_hs
    )

    storey_zones: list[list[dict[str, Any]]] = []
    for f_idx, fl in enumerate(floors):
        zlist = []
        for z_idx, z in enumerate(fl.get("zones", [])):
            poly = _clean_2d_polygon(z.get("coords_m", []))
            if poly is None:
                continue
            if needs_z_fix:
                z0 = f_idx * f2f
                z1 = (f_idx + 1) * f2f
            else:
                z0 = float(z["z_floor"])
                z1 = float(z["z_ceiling"])
            h = max(z1 - z0, 0.5)
            area = float(poly.area)
            zlist.append(
                {
                    "name": str(z.get("name", f"{bid}_F{f_idx}_Z{z_idx}")),
                    "poly": poly,
                    "edges": _ring_edges(poly),
                    "z0": z0,
                    "z1": z1,
                    "h": h,
                    "area": area,
                    "vol": area * h,
                    "conditioned": z.get("conditioned", True) is not False
                    and "circulation" not in str(z.get("name", "")).lower(),
                    "surfaces": [],
                }
            )
        if zlist:
            storey_zones.append(zlist)

    if not storey_zones:
        raise ValueError(f"{bid}: no valid zone polygons")

    outdoor_wall_m2 = 0.0
    window_m2 = 0.0
    pair_counter = 0

    def _make_surf(
        *,
        name: str,
        sclass: int,
        boundary: int,
        partner_name: str,
        area: float,
        tilt: float,
        az: float,
        normal: tuple[float, float, float],
        verts: np.ndarray,
        centroid_z: float,
        height: float,
        sun_exp: bool,
        wind_exp: bool,
        modal: ModalConductionModel | None,
        win: tuple[float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0),
    ) -> dict[str, Any]:
        cos_t = math.cos(math.radians(tilt))
        sin_t = math.sin(math.radians(tilt))
        vf_g = 0.5 * (1.0 - cos_t)
        vf_sky = 0.5 * (1.0 + cos_t)
        is_win = boundary == BOUND_WINDOW
        return {
            "name": name,
            "surf_class": sclass,
            "boundary": boundary,
            "partner_name": partner_name,
            "area": area,
            "tilt_deg": tilt,
            "cos_tilt": cos_t,
            "sin_tilt": sin_t,
            "azimuth_deg": az,
            "normal": np.array(normal, dtype=np.float64),
            "verts": verts,
            "centroid_z": centroid_z,
            "height": max(height, 0.1),
            "roughness_mult": 1.0 if is_win else ROUGHNESS_MEDIUM_ROUGH,
            "sun_exposed": sun_exp,
            "wind_exposed": wind_exp,
            "solar_abs_out": 0.0 if is_win else 0.7,
            "solar_abs_in": 0.0 if is_win else 0.7,
            "eps_in": 0.84 if is_win else 0.9,
            "eps_out": 0.84 if is_win else 0.9,
            "vf_ground": vf_g,
            "vf_sky": vf_sky,
            "vf_sky_ir": vf_sky,
            "vf_ground_ir": vf_g,
            "air_sky_split": math.sqrt(max(0.0, vf_sky)),
            "osc": (0.0, 0.0, 0.0, 0.0),
            "win": win,
            "modal": modal,
        }

    # 1. Vertical walls per storey: interzone pairing + party walls + outdoors + windows
    for f_idx, zlist in enumerate(storey_zones):
        n_zf = len(zlist)
        # Track covered intervals on each (zi, ei)
        covered: dict[tuple[int, int], list[tuple[float, float]]] = {}

        # Pair shared edges between zones on the same storey
        if n_zf > 1:
            bboxes = [z["poly"].bounds for z in zlist]
            for i in range(n_zf):
                bi = bboxes[i]
                edges_i = zlist[i]["edges"]
                for j in range(i + 1, n_zf):
                    bj = bboxes[j]
                    if (
                        bi[2] + 0.1 < bj[0]
                        or bj[2] + 0.1 < bi[0]
                        or bi[3] + 0.1 < bj[1]
                        or bj[3] + 0.1 < bi[1]
                    ):
                        continue
                    edges_j = zlist[j]["edges"]
                    z0 = max(zlist[i]["z0"], zlist[j]["z0"])
                    z1 = min(zlist[i]["z1"], zlist[j]["z1"])
                    h_sh = z1 - z0
                    if h_sh < 0.1:
                        continue
                    for ei, (a0, a1) in enumerate(edges_i):
                        ax, ay = a1[0] - a0[0], a1[1] - a0[1]
                        la = math.hypot(ax, ay)
                        if la < 0.05:
                            continue
                        ux, uy = ax / la, ay / la
                        nix, niy = uy, -ux
                        for ej, (b0, b1) in enumerate(edges_j):
                            bx, by = b1[0] - b0[0], b1[1] - b0[1]
                            lb = math.hypot(bx, by)
                            if lb < 0.05:
                                continue
                            vx, vy = bx / lb, by / lb
                            njx, njy = vy, -vx
                            # Must have opposite outward normals
                            if nix * njx + niy * njy > -0.95:
                                continue
                            # Perpendicular distance between parallel lines
                            d_perp = abs((b0[0] - a0[0]) * nix + (b0[1] - a0[1]) * niy)
                            if d_perp > 0.08:
                                continue
                            # Project b1, b0 onto a0->a1
                            t_lo = (b1[0] - a0[0]) * ux + (b1[1] - a0[1]) * uy
                            t_hi = (b0[0] - a0[0]) * ux + (b0[1] - a0[1]) * uy
                            if t_lo > t_hi:
                                t_lo, t_hi = t_hi, t_lo
                            o0 = max(0.0, t_lo)
                            o1 = min(la, t_hi)
                            olen = o1 - o0
                            if olen < 0.05:
                                continue
                            # Also compute interval on edge j
                            s_lo = (a1[0] - b0[0]) * vx + (a1[1] - b0[1]) * vy
                            s_hi = (a0[0] - b0[0]) * vx + (a0[1] - b0[1]) * vy
                            if s_lo > s_hi:
                                s_lo, s_hi = s_hi, s_lo
                            so0 = max(0.0, s_lo)
                            so1 = min(lb, s_hi)

                            covered.setdefault((i, ei), []).append((o0, o1))
                            covered.setdefault((j, ej), []).append((so0, so1))

                            pair_counter += 1
                            nm_i = f"F{f_idx}_IW_{pair_counter}_A"
                            nm_j = f"F{f_idx}_IW_{pair_counter}_B"
                            area_sh = olen * h_sh
                            az_i = math.degrees(math.atan2(nix, niy)) % 360.0
                            az_j = math.degrees(math.atan2(njx, njy)) % 360.0
                            p_s0 = (a0[0] + ux * o0, a0[1] + uy * o0)
                            p_s1 = (a0[0] + ux * o1, a0[1] + uy * o1)
                            q_i = _make_local_wall_quad(p_s0, p_s1, z0, z1, ox, oy)
                            q_j = _make_local_wall_quad(p_s1, p_s0, z0, z1, ox, oy)
                            zlist[i]["surfaces"].append(
                                _make_surf(
                                    name=nm_i,
                                    sclass=SURF_WALL,
                                    boundary=BOUND_SURFACE,
                                    partner_name=nm_j.casefold(),
                                    area=area_sh,
                                    tilt=90.0,
                                    az=az_i,
                                    normal=(nix, niy, 0.0),
                                    verts=q_i,
                                    centroid_z=0.5 * (z0 + z1),
                                    height=h_sh,
                                    sun_exp=False,
                                    wind_exp=False,
                                    modal=modals["wall"],
                                )
                            )
                            zlist[j]["surfaces"].append(
                                _make_surf(
                                    name=nm_j,
                                    sclass=SURF_WALL,
                                    boundary=BOUND_SURFACE,
                                    partner_name=nm_i.casefold(),
                                    area=area_sh,
                                    tilt=90.0,
                                    az=az_j,
                                    normal=(njx, njy, 0.0),
                                    verts=q_j,
                                    centroid_z=0.5 * (z0 + z1),
                                    height=h_sh,
                                    sun_exp=False,
                                    wind_exp=False,
                                    modal=modals["wall"],
                                )
                            )

        # Uncovered exterior segments -> Adiabatic party wall OR Outdoors + Window
        for i, zd in enumerate(zlist):
            z0, z1, h = zd["z0"], zd["z1"], zd["h"]
            for ei, (a0, a1) in enumerate(zd["edges"]):
                ax, ay = a1[0] - a0[0], a1[1] - a0[1]
                la = math.hypot(ax, ay)
                if la < 0.05:
                    continue
                ux, uy = ax / la, ay / la
                nx, ny = uy, -ux
                az = math.degrees(math.atan2(nx, ny)) % 360.0
                gaps = _split_uncovered_intervals(la, covered.get((i, ei), []))
                for gi, (g0, g1) in enumerate(gaps):
                    glen = g1 - g0
                    gross_area = glen * h
                    if gross_area < 0.05:
                        continue
                    p0 = (a0[0] + ux * g0, a0[1] + uy * g0)
                    p1 = (a0[0] + ux * g1, a0[1] + uy * g1)
                    seg_line = LineString([p0, p1])
                    # Exact EU-11 D-EU-40 R6 / apply_adiabatic_party_walls rule:
                    # wall XY base segment lies within neighbour MRR buffered by 0.30 m
                    is_party = any(seg_line.within(nb) for nb in nb_bufs)
                    quad = _make_local_wall_quad(p0, p1, z0, z1, ox, oy)
                    wname = f"F{f_idx}_Z{i}_W{ei}_{gi}"
                    if is_party:
                        zd["surfaces"].append(
                            _make_surf(
                                name=f"{wname}_PW",
                                sclass=SURF_WALL,
                                boundary=BOUND_ADIABATIC,
                                partner_name="",
                                area=gross_area,
                                tilt=90.0,
                                az=az,
                                normal=(nx, ny, 0.0),
                                verts=quad,
                                centroid_z=0.5 * (z0 + z1),
                                height=h,
                                sun_exp=False,
                                wind_exp=False,
                                modal=modals["wall"],
                            )
                        )
                    else:
                        outdoor_wall_m2 += gross_area
                        w_area = gross_area * win_share
                        if w_area >= MIN_WINDOW_AREA_M2:
                            window_m2 += w_area
                            net_area = max(gross_area - w_area, 1.0e-4)
                            w_quad = _scaled_window_quad(quad, win_share)
                            zd["surfaces"].append(
                                _make_surf(
                                    name=wname,
                                    sclass=SURF_WALL,
                                    boundary=BOUND_OUTDOORS,
                                    partner_name="",
                                    area=net_area,
                                    tilt=90.0,
                                    az=az,
                                    normal=(nx, ny, 0.0),
                                    verts=quad,
                                    centroid_z=0.5 * (z0 + z1),
                                    height=h,
                                    sun_exp=True,
                                    wind_exp=True,
                                    modal=modals["wall"],
                                )
                            )
                            zd["surfaces"].append(
                                _make_surf(
                                    name=f"{wname}_Win",
                                    sclass=SURF_WINDOW,
                                    boundary=BOUND_WINDOW,
                                    partner_name="",
                                    area=w_area,
                                    tilt=90.0,
                                    az=az,
                                    normal=(nx, ny, 0.0),
                                    verts=w_quad,
                                    centroid_z=0.5 * (z0 + z1),
                                    height=h * math.sqrt(win_share),
                                    sun_exp=True,
                                    wind_exp=True,
                                    modal=None,
                                    win=win_tuple,
                                )
                            )
                        else:
                            zd["surfaces"].append(
                                _make_surf(
                                    name=wname,
                                    sclass=SURF_WALL,
                                    boundary=BOUND_OUTDOORS,
                                    partner_name="",
                                    area=gross_area,
                                    tilt=90.0,
                                    az=az,
                                    normal=(nx, ny, 0.0),
                                    verts=quad,
                                    centroid_z=0.5 * (z0 + z1),
                                    height=h,
                                    sun_exp=True,
                                    wind_exp=True,
                                    modal=modals["wall"],
                                )
                            )

    # 2. Horizontal surfaces: ground floor, inter-storey ceiling/floor pairs, top roof
    n_floors = len(storey_zones)
    for i, zd in enumerate(storey_zones[0]):
        zd["surfaces"].append(
            _make_surf(
                name=f"F0_Z{i}_GroundFloor",
                sclass=SURF_FLOOR,
                boundary=BOUND_GROUND,
                partner_name="",
                area=zd["area"],
                tilt=180.0,
                az=0.0,
                normal=(0.0, 0.0, -1.0),
                verts=_make_horizontal_verts(zd["poly"], zd["z0"], ox, oy, upward=False),
                centroid_z=zd["z0"],
                height=1.0,
                sun_exp=False,
                wind_exp=False,
                modal=modals["floor"],
            )
        )

    for f_idx in range(n_floors - 1):
        lo_list = storey_zones[f_idx]
        hi_list = storey_zones[f_idx + 1]
        lo_cov = [0.0] * len(lo_list)
        hi_cov = [0.0] * len(hi_list)
        for i, zlo in enumerate(lo_list):
            b_lo = zlo["poly"].bounds
            for j, zhi in enumerate(hi_list):
                b_hi = zhi["poly"].bounds
                if (
                    b_lo[2] < b_hi[0]
                    or b_hi[2] < b_lo[0]
                    or b_lo[3] < b_hi[1]
                    or b_hi[3] < b_lo[1]
                ):
                    continue
                inter = zlo["poly"].intersection(zhi["poly"])
                ia = float(inter.area)
                if ia < 0.05:
                    continue
                lo_cov[i] += ia
                hi_cov[j] += ia
                pair_counter += 1
                nm_c = f"F{f_idx}_IC_{pair_counter}_C"
                nm_f = f"F{f_idx + 1}_IF_{pair_counter}_F"
                zlo["surfaces"].append(
                    _make_surf(
                        name=nm_c,
                        sclass=SURF_ROOF,
                        boundary=BOUND_SURFACE,
                        partner_name=nm_f.casefold(),
                        area=ia,
                        tilt=0.0,
                        az=0.0,
                        normal=(0.0, 0.0, 1.0),
                        verts=np.zeros((0, 3), dtype=np.float64),
                        centroid_z=zlo["z1"],
                        height=1.0,
                        sun_exp=False,
                        wind_exp=False,
                        modal=modals["floor"],
                    )
                )
                zhi["surfaces"].append(
                    _make_surf(
                        name=nm_f,
                        sclass=SURF_FLOOR,
                        boundary=BOUND_SURFACE,
                        partner_name=nm_c.casefold(),
                        area=ia,
                        tilt=180.0,
                        az=0.0,
                        normal=(0.0, 0.0, -1.0),
                        verts=np.zeros((0, 3), dtype=np.float64),
                        centroid_z=zhi["z0"],
                        height=1.0,
                        sun_exp=False,
                        wind_exp=False,
                        modal=modals["floor"],
                    )
                )
        # Exposed roof setbacks on storey f_idx
        for i, zlo in enumerate(lo_list):
            rem = zlo["area"] - lo_cov[i]
            if rem > 0.05:
                zlo["surfaces"].append(
                    _make_surf(
                        name=f"F{f_idx}_Z{i}_SetbackRoof",
                        sclass=SURF_ROOF,
                        boundary=BOUND_OUTDOORS,
                        partner_name="",
                        area=rem,
                        tilt=0.0,
                        az=0.0,
                        normal=(0.0, 0.0, 1.0),
                        verts=_make_horizontal_verts(zlo["poly"], zlo["z1"], ox, oy, upward=True),
                        centroid_z=zlo["z1"],
                        height=1.0,
                        sun_exp=True,
                        wind_exp=True,
                        modal=modals["roof"],
                    )
                )
        # Exposed floor overhangs on storey f_idx + 1
        for j, zhi in enumerate(hi_list):
            rem = zhi["area"] - hi_cov[j]
            if rem > 0.05:
                zhi["surfaces"].append(
                    _make_surf(
                        name=f"F{f_idx + 1}_Z{j}_OverhangFloor",
                        sclass=SURF_FLOOR,
                        boundary=BOUND_OUTDOORS,
                        partner_name="",
                        area=rem,
                        tilt=180.0,
                        az=0.0,
                        normal=(0.0, 0.0, -1.0),
                        verts=_make_horizontal_verts(zhi["poly"], zhi["z0"], ox, oy, upward=False),
                        centroid_z=zhi["z0"],
                        height=1.0,
                        sun_exp=False,
                        wind_exp=True,
                        modal=modals["floor"],
                    )
                )

    # Top storey roof
    for i, zd in enumerate(storey_zones[-1]):
        zd["surfaces"].append(
            _make_surf(
                name=f"F{n_floors - 1}_Z{i}_Roof",
                sclass=SURF_ROOF,
                boundary=BOUND_OUTDOORS,
                partner_name="",
                area=zd["area"],
                tilt=0.0,
                az=0.0,
                normal=(0.0, 0.0, 1.0),
                verts=_make_horizontal_verts(zd["poly"], zd["z1"], ox, oy, upward=True),
                centroid_z=zd["z1"],
                height=1.0,
                sun_exp=True,
                wind_exp=True,
                modal=modals["roof"],
            )
        )

    # 3. InternalMass & Zone controls (constant 8760 hourly arrays)
    zones_compiled: list[dict[str, Any]] = []
    for zlist in storey_zones:
        for zd in zlist:
            area = zd["area"]
            vol = zd["vol"]
            if zd["conditioned"]:
                im_area = c_m * 3600.0 * area / MASS_CAPACITY_PER_M2
                zd["surfaces"].append(
                    _make_surf(
                        name=f"{zd['name']}_EU_InternalMass",
                        sclass=SURF_INTMASS,
                        boundary=BOUND_INTMASS,
                        partner_name="",
                        area=im_area,
                        tilt=90.0,
                        az=0.0,
                        normal=(0.0, 1.0, 0.0),
                        verts=np.zeros((0, 3), dtype=np.float64),
                        centroid_z=0.5 * (zd["z0"] + zd["z1"]),
                        height=1.0,
                        sun_exp=False,
                        wind_exp=False,
                        modal=modals["intmass"],
                    )
                )
                zones_compiled.append(
                    {
                        "name": zd["name"],
                        "volume": vol,
                        "floor_area": area,
                        "centroid_z": 0.5 * (zd["z0"] + zd["z1"]),
                        "has_hvac": 1,
                        "has_cooling": 0,
                        "max_heat_supply_t": 50.0,
                        "min_cool_supply_t": 13.0,
                        "heat_sp_hr": np.full(8760, theta_i_c, dtype=np.float64),
                        "cool_sp_hr": np.full(8760, 50.0, dtype=np.float64),
                        "gain_conv_hr": np.full(8760, BASE_GAIN_W_M2 * area, dtype=np.float64),
                        "gain_rad_hr": np.zeros(8760, dtype=np.float64),
                        "vent_flow_hr": np.full(8760, ach * vol / 3600.0, dtype=np.float64),
                        "surfaces": zd["surfaces"],
                    }
                )
            else:
                zones_compiled.append(
                    {
                        "name": zd["name"],
                        "volume": vol,
                        "floor_area": area,
                        "centroid_z": 0.5 * (zd["z0"] + zd["z1"]),
                        "has_hvac": 0,
                        "has_cooling": 0,
                        "max_heat_supply_t": 50.0,
                        "min_cool_supply_t": 13.0,
                        "heat_sp_hr": np.full(8760, -100.0, dtype=np.float64),
                        "cool_sp_hr": np.full(8760, 100.0, dtype=np.float64),
                        "gain_conv_hr": np.zeros(8760, dtype=np.float64),
                        "gain_rad_hr": np.zeros(8760, dtype=np.float64),
                        "vent_flow_hr": np.full(8760, 0.0005 * area, dtype=np.float64),
                        "surfaces": zd["surfaces"],
                    }
                )

    occluders = (
        _build_occluders_for_building(
            bid, target_fp, ox, oy, ctx_bids, ctx_fps, ctx_heights, tree
        )
        if not target_fp.is_empty
        else []
    )
    n_tot_surfs = sum(len(z["surfaces"]) for z in zones_compiled)
    rung = "S2b" if len(zones_compiled) > 1 else ("S3" if occluders else "S2a")
    compiled = {
        "building_id": bid,
        "rung": rung,
        "steps_per_hour": STEPS_PER_HOUR,
        "terrain_idx": TERRAIN_CITY_IDX,
        "site_ground_temp": np.full(12, GROUND_TEMP_C, dtype=np.float64),
        "warmup_min_days": 6,
        "warmup_max_days": 25,
        "loads_conv_tol": 0.04,
        "temp_conv_tol": 0.2,
        "h_conv_min": 0.1,
        "zones": zones_compiled,
        "sunlit_hr": None,
        "dif_sky": np.ones(n_tot_surfs, dtype=np.float64),
    }
    return compiled, occluders, outdoor_wall_m2, window_m2


def _apply_building_shading(
    compiled: dict[str, Any],
    occluders: list[np.ndarray],
    solcos_hr: np.ndarray,
    *,
    periodic_days: int = 10,
    n_grid: int = 2,
    n_sky_rays: int = 64,
    device: str = "cuda",
) -> None:
    if not occluders:
        return
    all_surfs = [s for zd in compiled["zones"] for s in zd["surfaces"]]
    n_s = len(all_surfs)
    sun_mask = np.asarray(
        [bool(s["sun_exposed"]) and len(s["verts"]) >= 3 for s in all_surfs],
        dtype=bool,
    )
    if not np.any(sun_mask):
        return
    verts_list = [s["verts"] for s in all_surfs]
    normals = np.stack([s["normal"] for s in all_surfs], axis=0)
    sunlit_hr, dif_sky = compute_exterior_shading(
        verts_list,
        normals,
        sun_mask,
        occluders,
        solcos_hr,
        periodic_days=periodic_days,
        n_grid=n_grid,
        n_sky_rays=n_sky_rays,
        device=device,
    )
    compiled["sunlit_hr"] = sunlit_hr
    compiled["dif_sky"] = dif_sky


def _make_subbatches(
    compiled_list: list[dict[str, Any]],
    *,
    max_bldgs: int = 128,
    max_zones: int = 1000,
) -> list[list[int]]:
    """Sort by n_zones ascending to eliminate CUDA warp divergence and cap VRAM/TDR."""
    order = sorted(range(len(compiled_list)), key=lambda i: len(compiled_list[i]["zones"]))
    groups: list[list[int]] = []
    cur: list[int] = []
    cur_z = 0
    for idx in order:
        nz = len(compiled_list[idx]["zones"])
        if cur and (len(cur) >= max_bldgs or cur_z + nz > max_zones):
            groups.append(cur)
            cur = []
            cur_z = 0
        cur.append(idx)
        cur_z += nz
    if cur:
        groups.append(cur)
    return groups


def run_district(
    spec: DistrictSpec,
    per_home_df: pd.DataFrame,
    *,
    limit: int | None = None,
    use_shading: bool = True,
    shading_periodic_days: int = 10,
    shading_device: str = "cuda",
    max_zones_per_batch: int = 2500,
    max_bldgs_per_batch: int = 512,
) -> tuple[dict[str, Any], pd.DataFrame]:
    t0 = time.perf_counter()
    weather = load_epw_weather(WEATHER_DIR / spec.epw_name, steps_per_hour=STEPS_PER_HOUR)
    arch_cache = _build_archetype_cache(ARCHETYPE_DIR / spec.tabula_file, spec.country)
    layouts = _load_district_layouts(spec)
    ctx_bids, ctx_fps, ctx_bufs, ctx_heights, tree = _build_district_context_index(layouts)
    bid_to_ctx_idx = {b: i for i, b in enumerate(ctx_bids)}

    sub_ph = per_home_df[per_home_df["district"] == spec.code].copy()
    sub_ph["building_id"] = sub_ph["building_id"].astype(str)
    matched_rows = [
        row for _, row in sub_ph.iterrows() if row["building_id"] in layouts
    ]
    if limit is not None and limit > 0:
        matched_rows = matched_rows[:limit]

    # 1. Parallel CPU geometry + physics compilation
    t_comp0 = time.perf_counter()

    def _compile_one(row: pd.Series):
        bid = str(row["building_id"])
        aid = str(row["archetype_id"])
        return _compile_layout_building(
            bid,
            aid,
            layouts[bid],
            arch_cache[aid],
            ctx_bids,
            ctx_fps,
            ctx_bufs,
            ctx_heights,
            tree,
            bid_to_ctx_idx,
        )

    with ThreadPoolExecutor(max_workers=12) as pool:
        results_comp = list(pool.map(_compile_one, matched_rows))

    compiled_list = [r[0] for r in results_comp]
    occluders_list = [r[1] for r in results_comp]
    out_wall_m2_list = [r[2] for r in results_comp]
    win_m2_list = [r[3] for r in results_comp]
    compile_s = time.perf_counter() - t_comp0

    # 2. Group into zone-balanced sub-batches; run 3D ray-traced shading + CUDA heat balance per sub-batch
    #    (keeps peak host RAM < 1.5 GB even for Bologna's 35,941 zones / ~400k surfaces!)
    groups = _make_subbatches(
        compiled_list,
        max_bldgs=max_bldgs_per_batch,
        max_zones=max_zones_per_batch,
    )
    solcos_hr = None
    if use_shading and weather.solcos_x is not None:
        mid = STEPS_PER_HOUR // 2
        solcos_hr = np.stack(
            [
                weather.solcos_x[mid::STEPS_PER_HOUR],
                weather.solcos_y[mid::STEPS_PER_HOUR],
                weather.solcos_z[mid::STEPS_PER_HOUR],
            ],
            axis=1,
        )

    gpu_kwh = np.zeros(len(compiled_list), dtype=np.float64)
    shading_s = 0.0
    gpu_kernel_s = 0.0
    max_launch_s = 0.0
    t_gpu_all0 = time.perf_counter()

    for gi, idxs in enumerate(groups):
        sub_comp = [compiled_list[i] for i in idxs]
        # 2a. 3D ray-traced neighbour shading for this sub-batch
        t_shd0 = time.perf_counter()
        if solcos_hr is not None:
            if shading_device == "cuda":
                for i in idxs:
                    _apply_building_shading(
                        compiled_list[i],
                        occluders_list[i],
                        solcos_hr,
                        periodic_days=shading_periodic_days,
                        n_grid=2,
                        n_sky_rays=64,
                        device="cuda",
                    )
            else:
                def _shd_work(i: int):
                    _apply_building_shading(
                        compiled_list[i],
                        occluders_list[i],
                        solcos_hr,
                        periodic_days=shading_periodic_days,
                        n_grid=2,
                        n_sky_rays=64,
                        device="cpu",
                    )
                with ThreadPoolExecutor(max_workers=12) as pool:
                    list(pool.map(_shd_work, idxs))
        b_shd_s = time.perf_counter() - t_shd0
        shading_s += b_shd_s

        # 2b. Pack CSR & run zone-parallel CUDA heat balance
        batch = pack_compiled_general_buildings(
            sub_comp,
            np.zeros(len(sub_comp), dtype=np.int32),
        )
        # Release float32 sunlit_hr before GPU launch to minimize RAM
        for i in idxs:
            compiled_list[i]["sunlit_hr"] = None

        res = run_general_cuda(
            batch,
            [weather],
            record_zone_temp=False,
            run_chunk_days=1,
            run_chunk_steps=144,  # 12-hour partner sync, TDR-safe (< 0.5 s/launch)
            block_size=64,
            zone_parallel=True,
        )
        gpu_kernel_s += res.gpu_s
        max_launch_s = max(max_launch_s, res.max_launch_s)
        for local_i, orig_i in enumerate(idxs):
            gpu_kwh[orig_i] = float(res.annual_heating_kwh[local_i])
        if len(groups) > 1:
            print(
                f"  [{spec.code}] batch {gi + 1}/{len(groups)}: "
                f"bldgs={len(idxs)} zones={batch.n_zones_total} surfs={batch.n_surfs_total} "
                f"shd={b_shd_s:.1f}s gpu={res.gpu_s:.1f}s max_launch={res.max_launch_s:.3f}s",
                flush=True,
            )

    gpu_wall_s = time.perf_counter() - t_gpu_all0 - shading_s
    total_s = time.perf_counter() - t0

    # 4. Assemble per-building comparison DataFrame
    per_rows = []
    tot_zones = 0
    tot_surfs = 0
    for i, row in enumerate(matched_rows):
        c = compiled_list[i]
        nz = len(c["zones"])
        ns = sum(len(z["surfaces"]) for z in c["zones"])
        tot_zones += nz
        tot_surfs += ns
        gpu_floor_m2 = sum(float(z["floor_area"]) for z in c["zones"])
        pub_floor_m2 = float(row["floor_area_m2"])
        pub_kwh = float(row["heating_kwh"])
        g_kwh = float(gpu_kwh[i])
        pub_eui = pub_kwh / pub_floor_m2 if pub_floor_m2 > 0 else 0.0
        g_eui = g_kwh / pub_floor_m2 if pub_floor_m2 > 0 else 0.0
        rel_diff = (g_kwh - pub_kwh) / pub_kwh if pub_kwh > 1.0 else 0.0
        per_rows.append(
            {
                "district": spec.code,
                "building_id": str(row["building_id"]),
                "archetype_id": str(row["archetype_id"]),
                "building_type": str(row["building_type"]),
                "n_zones": nz,
                "n_surfaces": ns,
                "pub_floor_area_m2": pub_floor_m2,
                "gpu_floor_area_m2": gpu_floor_m2,
                "outdoor_wall_m2": out_wall_m2_list[i],
                "window_m2": win_m2_list[i],
                "pub_heating_kwh": pub_kwh,
                "gpu_heating_kwh": g_kwh,
                "pub_eui_kwh_m2": pub_eui,
                "gpu_eui_kwh_m2": g_eui,
                "rel_diff": rel_diff,
            }
        )
    per_df = pd.DataFrame(per_rows)

    pub_tot_kwh = float(per_df["pub_heating_kwh"].sum())
    gpu_tot_kwh = float(per_df["gpu_heating_kwh"].sum())
    tot_area = float(per_df["pub_floor_area_m2"].sum())
    pub_eui_pool = pub_tot_kwh / tot_area
    gpu_eui_pool = gpu_tot_kwh / tot_area
    rel_eui_diff = (gpu_eui_pool - pub_eui_pool) / pub_eui_pool

    # Per-building R^2 on kWh and EUI
    if len(per_df) >= 2:
        r_kwh = float(np.corrcoef(per_df["pub_heating_kwh"], per_df["gpu_heating_kwh"])[0, 1])
        r2_kwh = r_kwh * r_kwh
        r_eui = float(np.corrcoef(per_df["pub_eui_kwh_m2"], per_df["gpu_eui_kwh_m2"])[0, 1])
        r2_eui = r_eui * r_eui
    else:
        r2_kwh = float("nan")
        r2_eui = float("nan")

    med_rel = float(per_df["rel_diff"].median())
    med_abs_rel = float(per_df["rel_diff"].abs().median())

    summary = {
        "district": spec.code,
        "label": spec.label,
        "n_published_homes": int(len(sub_ph)),
        "n_simulated_homes": int(len(per_df)),
        "coverage_pct": 100.0 * len(per_df) / max(1, len(sub_ph)),
        "n_zones": tot_zones,
        "n_surfaces": tot_surfs,
        "floor_area_m2": tot_area,
        "pub_heating_kwh": pub_tot_kwh,
        "gpu_heating_kwh": gpu_tot_kwh,
        "pub_eui_kwh_m2": pub_eui_pool,
        "gpu_eui_kwh_m2": gpu_eui_pool,
        "rel_eui_diff_pct": 100.0 * rel_eui_diff,
        "r2_kwh": r2_kwh,
        "r2_eui": r2_eui,
        "median_rel_diff_pct": 100.0 * med_rel,
        "median_abs_rel_err_pct": 100.0 * med_abs_rel,
        "compile_s": compile_s,
        "shading_s": shading_s,
        "gpu_kernel_s": gpu_kernel_s,
        "gpu_wall_s": gpu_wall_s,
        "max_launch_s": max_launch_s,
        "total_s": total_s,
        "bldg_yr_per_s": len(per_df) / max(total_s, 1.0e-6),
        "gpu_bldg_yr_per_s": len(per_df) / max(gpu_kernel_s, 1.0e-6),
    }
    print(
        f"[{spec.code}] n={len(per_df)}/{len(sub_ph)} ({summary['coverage_pct']:.1f}%) "
        f"zones={tot_zones} surfs={tot_surfs} | "
        f"EUI pub={pub_eui_pool:.2f} gpu={gpu_eui_pool:.2f} ({summary['rel_eui_diff_pct']:+.2f}%) | "
        f"R2_kwh={r2_kwh:.4f} R2_eui={r2_eui:.4f} med_err={summary['median_rel_diff_pct']:+.2f}% | "
        f"comp={compile_s:.1f}s shd={shading_s:.1f}s gpu={gpu_kernel_s:.1f}s "
        f"max_launch={max_launch_s:.3f}s tot={total_s:.1f}s",
        flush=True,
    )
    return summary, per_df


def main() -> None:
    ap = argparse.ArgumentParser(description="M8 European 3D Neighbourhood GPU Runner")
    ap.add_argument(
        "--districts",
        nargs="+",
        default=list(DISTRICTS.keys()),
        choices=list(DISTRICTS.keys()),
    )
    ap.add_argument("--limit", type=int, default=None, help="Optional max buildings per district")
    ap.add_argument("--no-shading", action="store_true")
    ap.add_argument("--shading-periodic-days", type=int, default=10)
    ap.add_argument("--shading-device", choices=("cuda", "cpu"), default="cuda")
    ap.add_argument("--max-zones-per-batch", type=int, default=2500)
    ap.add_argument("--max-bldgs-per-batch", type=int, default=512)
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    per_home_df = pd.read_csv(EU11_PER_HOME)
    summaries: list[dict[str, Any]] = []
    per_dfs: list[pd.DataFrame] = []

    t_all0 = time.perf_counter()
    for code in args.districts:
        s, pdf = run_district(
            DISTRICTS[code],
            per_home_df,
            limit=args.limit,
            use_shading=not args.no_shading,
            shading_periodic_days=args.shading_periodic_days,
            shading_device=args.shading_device,
            max_zones_per_batch=args.max_zones_per_batch,
            max_bldgs_per_batch=args.max_bldgs_per_batch,
        )
        summaries.append(s)
        per_dfs.append(pdf)

    all_per = pd.concat(per_dfs, ignore_index=True)
    tot_all_s = time.perf_counter() - t_all0

    # Pooled FLEET row
    pub_tot_kwh = float(all_per["pub_heating_kwh"].sum())
    gpu_tot_kwh = float(all_per["gpu_heating_kwh"].sum())
    tot_area = float(all_per["pub_floor_area_m2"].sum())
    pub_eui = pub_tot_kwh / tot_area
    gpu_eui = gpu_tot_kwh / tot_area
    r_kwh = float(np.corrcoef(all_per["pub_heating_kwh"], all_per["gpu_heating_kwh"])[0, 1]) if len(all_per) >= 2 else float("nan")
    r_eui = float(np.corrcoef(all_per["pub_eui_kwh_m2"], all_per["gpu_eui_kwh_m2"])[0, 1]) if len(all_per) >= 2 else float("nan")
    tot_pub_n = sum(s["n_published_homes"] for s in summaries)
    fleet_row = {
        "district": "FLEET_4EU",
        "label": "Four European Neighbourhoods (Pooled)",
        "n_published_homes": tot_pub_n,
        "n_simulated_homes": int(len(all_per)),
        "coverage_pct": 100.0 * len(all_per) / max(1, tot_pub_n),
        "n_zones": int(sum(s["n_zones"] for s in summaries)),
        "n_surfaces": int(sum(s["n_surfaces"] for s in summaries)),
        "floor_area_m2": tot_area,
        "pub_heating_kwh": pub_tot_kwh,
        "gpu_heating_kwh": gpu_tot_kwh,
        "pub_eui_kwh_m2": pub_eui,
        "gpu_eui_kwh_m2": gpu_eui,
        "rel_eui_diff_pct": 100.0 * (gpu_eui - pub_eui) / pub_eui,
        "r2_kwh": r_kwh * r_kwh,
        "r2_eui": r_eui * r_eui,
        "median_rel_diff_pct": 100.0 * float(all_per["rel_diff"].median()),
        "median_abs_rel_err_pct": 100.0 * float(all_per["rel_diff"].abs().median()),
        "compile_s": float(sum(s["compile_s"] for s in summaries)),
        "shading_s": float(sum(s["shading_s"] for s in summaries)),
        "gpu_kernel_s": float(sum(s["gpu_kernel_s"] for s in summaries)),
        "gpu_wall_s": float(sum(s["gpu_wall_s"] for s in summaries)),
        "max_launch_s": float(max(s["max_launch_s"] for s in summaries)),
        "total_s": tot_all_s,
        "bldg_yr_per_s": len(all_per) / max(tot_all_s, 1.0e-6),
        "gpu_bldg_yr_per_s": len(all_per) / max(sum(s["gpu_kernel_s"] for s in summaries), 1.0e-6),
    }
    summaries.append(fleet_row)
    sum_df = pd.DataFrame(summaries)
    print(
        f"\n[FLEET_4EU] n={fleet_row['n_simulated_homes']}/{tot_pub_n} "
        f"({fleet_row['coverage_pct']:.1f}%) zones={fleet_row['n_zones']} "
        f"surfs={fleet_row['n_surfaces']} | "
        f"EUI pub={pub_eui:.2f} gpu={gpu_eui:.2f} ({fleet_row['rel_eui_diff_pct']:+.2f}%) | "
        f"R2_kwh={fleet_row['r2_kwh']:.4f} R2_eui={fleet_row['r2_eui']:.4f} | "
        f"gpu_kernel={fleet_row['gpu_kernel_s']:.1f}s total={tot_all_s:.1f}s "
        f"({fleet_row['bldg_yr_per_s']:.1f} bldg-yr/s end-to-end)",
        flush=True,
    )

    if not args.no_save and args.limit is None:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        sum_df.to_csv(OUT_DIR / "gpusim_m8_eu_districts.csv", index=False)
        all_per.to_csv(OUT_DIR / "gpusim_m8_eu_per_building.csv", index=False)
        print(f"Saved {OUT_DIR / 'gpusim_m8_eu_districts.csv'} and gpusim_m8_eu_per_building.csv")


if __name__ == "__main__":
    main()
