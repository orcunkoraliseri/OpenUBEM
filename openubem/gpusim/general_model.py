"""Unified multi-rung compiler (S1 Solar, S2a Layered/Ground/Wind/Schedules, S3 Shading, S2b Multi-Zone).

Compiles arbitrary single- or multi-zone IdealLoads (+ unconditioned zones) IDFs into a
flat CSR ``GeneralBatch`` with zero padding waste and no hard ceiling on zones or surfaces.
Uses modal diagonal state-space conduction (``MAX_MODES = 12``) for float32 GPU stability
on arbitrarily thick multi-layer constructions.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import numpy as np

from openubem.gpusim.compile import (
    BOUND_DOOR,
    BOUND_INTMASS,
    BOUND_OSC,
    BOUND_OUTDOORS,
    BOUND_WINDOW,
    ROUGHNESS_MAP,
    SURF_DOOR,
    SURF_FLOOR,
    SURF_INTMASS,
    SURF_ROOF,
    SURF_WALL,
    SURF_WINDOW,
    _determine_azimuth_and_tilt,
    _newell_area_and_normal,
    _parse_vertices,
    _polygon_centroid,
)
from openubem.gpusim.ctf import LayerSpec, build_modal_conduction
from openubem.gpusim.physics.convection import ROUGHNESS_MULTIPLIERS
from openubem.gpusim.physics.psychro import STEFAN_BOLTZMANN
from openubem.gpusim.physics.solar import simple_glazing_normal_optics
from openubem.gpusim.physics.window import simple_glazing_layer_conductance
from openubem.gpusim.router import expand_ideal_loads_templates
from openubem.gpusim.schedules import (
    compile_schedule_compact_hourly,
    load_schedule_file_hourly,
    resolve_schedule_path,
)
from openubem.gpusim.shading import compute_exterior_shading
from openubem.gpusim.subset import ParsedIdfObject, SubsetCheckResult, parse_expidf
from openubem.gpusim.viewfactors import (
    calc_approximate_view_factors,
    calc_script_f,
    fix_view_factors,
)
from openubem.gpusim.weather import WeatherSeries

BOUND_GROUND = 5
BOUND_ADIABATIC = 6
BOUND_SURFACE = 7

TERRAIN_MAP: dict[str, int] = {
    "country": 0,
    "suburbs": 1,
    "city": 2,
    "ocean": 3,
    "urban": 1,
}

MAX_MODES: int = 12

GENERAL_ALLOWED_OBJECT_TYPES: frozenset[str] = frozenset(
    {
        "VERSION",
        "SIMULATIONCONTROL",
        "BUILDING",
        "SHADOWCALCULATION",
        "SURFACECONVECTIONALGORITHM:INSIDE",
        "SURFACECONVECTIONALGORITHM:OUTSIDE",
        "HEATBALANCEALGORITHM",
        "TIMESTEP",
        "SITE:LOCATION",
        "SITE:GROUNDTEMPERATURE:BUILDINGSURFACE",
        "SIZINGPERIOD:WEATHERFILEDAYS",
        "SIZINGPERIOD:DESIGNDAY",
        "RUNPERIOD",
        "SIZING:ZONE",
        "GLOBALGEOMETRYRULES",
        "ZONE",
        "BUILDINGSURFACE:DETAILED",
        "FENESTRATIONSURFACE:DETAILED",
        "SHADING:SITE:DETAILED",
        "SHADING:BUILDING:DETAILED",
        "INTERNALMASS",
        "MATERIAL",
        "MATERIAL:NOMASS",
        "MATERIAL:AIRGAP",
        "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM",
        "CONSTRUCTION",
        "SURFACEPROPERTY:OTHERSIDECOEFFICIENTS",
        "SCHEDULETYPELIMITS",
        "SCHEDULE:CONSTANT",
        "SCHEDULE:COMPACT",
        "SCHEDULE:FILE",
        "OTHEREQUIPMENT",
        "ELECTRICEQUIPMENT",
        "LIGHTS",
        "PEOPLE",
        "ZONEVENTILATION:DESIGNFLOWRATE",
        "ZONEINFILTRATION:DESIGNFLOWRATE",
        "THERMOSTATSETPOINT:DUALSETPOINT",
        "ZONECONTROL:THERMOSTAT",
        "ZONEHVAC:EQUIPMENTCONNECTIONS",
        "ZONEHVAC:EQUIPMENTLIST",
        "ZONEHVAC:IDEALLOADSAIRSYSTEM",
        "OUTPUT:VARIABLE",
        "OUTPUT:VARIABLEDICTIONARY",
        "OUTPUT:TABLE:SUMMARYREPORTS",
        "OUTPUTCONTROL:TABLE:STYLE",
        "OUTPUT:SQLITE",
        "OUTPUT:CONSTRUCTIONS",
        "OUTPUT:SURFACES:LIST",
        "OUTPUT:METER",
        "OUTPUT:METER:METERFILEONLY",
    }
)


def _field(obj: ParsedIdfObject, index: int, default: str = "") -> str:
    if index >= len(obj.fields):
        return default
    val = obj.fields[index].strip()
    return val if val else default


def _float_field(obj: ParsedIdfObject, index: int, default: float = 0.0) -> float:
    raw = _field(obj, index, "")
    return float(raw) if raw else default


def check_general_subset(idf_text: str) -> tuple[str | None, SubsetCheckResult]:
    """Fail-closed validation across rungs S0, S1, S2a, S3, S2b.

    Returns ``(rung_name, SubsetCheckResult)`` where ``rung_name`` is the
    highest rung triggered by the IDF, or ``None`` if unsupported.
    """
    expanded = expand_ideal_loads_templates(idf_text)
    objects = parse_expidf(expanded)
    if not objects:
        return None, SubsetCheckResult(False, "Empty IDF")

    for obj in objects:
        if obj.obj_type not in GENERAL_ALLOWED_OBJECT_TYPES:
            return None, SubsetCheckResult(
                False, f"Unsupported object type for gpusim: {obj.raw_type}"
            )

    by_type: dict[str, list[ParsedIdfObject]] = {}
    for obj in objects:
        by_type.setdefault(obj.obj_type, []).append(obj)

    zones = by_type.get("ZONE", [])
    if len(zones) < 1:
        return None, SubsetCheckResult(False, "IDF has 0 Zones")

    for hb in by_type.get("HEATBALANCEALGORITHM", []):
        algo = _field(hb, 0, "ConductionTransferFunction")
        if algo.casefold() != "conductiontransferfunction":
            return None, SubsetCheckResult(False, f"Unsupported HeatBalanceAlgorithm: {algo}")

    # Validate IdealLoadsAirSystem fail-closed limits (no sizing limits, no OA, no economizer/HRV)
    for ideal in by_type.get("ZONEHVAC:IDEALLOADSAIRSYSTEM", []):
        iname = _field(ideal, 0)
        if _field(ideal, 9, "NoLimit").casefold() != "nolimit":
            return None, SubsetCheckResult(
                False, f"IdealLoads '{iname}' Heating Limit='{_field(ideal, 9)}' != NoLimit"
            )
        if _field(ideal, 12, "NoLimit").casefold() != "nolimit":
            return None, SubsetCheckResult(
                False, f"IdealLoads '{iname}' Cooling Limit='{_field(ideal, 12)}' != NoLimit"
            )
        if _field(ideal, 20, "") or _field(ideal, 21, ""):
            return None, SubsetCheckResult(
                False, f"IdealLoads '{iname}' has outdoor air enabled"
            )
        if _field(ideal, 22, "None").casefold() != "none":
            return None, SubsetCheckResult(False, f"IdealLoads '{iname}' has DCV")
        if _field(ideal, 23, "NoEconomizer").casefold() != "noeconomizer":
            return None, SubsetCheckResult(False, f"IdealLoads '{iname}' has Economizer")
        if _field(ideal, 24, "None").casefold() != "none":
            return None, SubsetCheckResult(False, f"IdealLoads '{iname}' has Heat Recovery")

    glass_names = {
        _field(o, 0).casefold()
        for o in by_type.get("WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", [])
    }
    mat_names = {
        _field(o, 0).casefold()
        for o in (
            by_type.get("MATERIAL", [])
            + by_type.get("MATERIAL:NOMASS", [])
            + by_type.get("MATERIAL:AIRGAP", [])
        )
    }
    constructions: dict[str, list[str]] = {}
    for cons in by_type.get("CONSTRUCTION", []):
        constructions[_field(cons, 0).casefold()] = [
            f.strip().casefold() for f in cons.fields[1:] if f.strip()
        ]

    has_sun = False
    has_s2a = False
    has_shading = bool(
        by_type.get("SHADING:SITE:DETAILED") or by_type.get("SHADING:BUILDING:DETAILED")
    )
    has_multizone = len(zones) > 1

    for surf in by_type.get("BUILDINGSURFACE:DETAILED", []):
        sname = _field(surf, 0)
        cons_key = _field(surf, 2).casefold()
        bc = _field(surf, 5).casefold()
        if bc not in ("outdoors", "othersidecoefficients", "ground", "adiabatic", "surface"):
            return None, SubsetCheckResult(
                False, f"Surface '{sname}' unsupported BC='{_field(surf, 5)}'"
            )
        if bc in ("ground", "adiabatic"):
            has_s2a = True
        if bc == "surface":
            has_multizone = True
        if _field(surf, 7, "SunExposed").casefold() == "sunexposed":
            has_sun = True
        if _field(surf, 8, "WindExposed").casefold() == "windexposed":
            has_s2a = True
        layers = constructions.get(cons_key, [])
        if not layers or not all(ly in mat_names for ly in layers):
            return None, SubsetCheckResult(
                False, f"Surface '{sname}' uses unsupported material in '{_field(surf, 2)}'"
            )
        if len(layers) > 1 or any(
            ly in {_field(m, 0).casefold() for m in by_type.get("MATERIAL", [])}
            for ly in layers
        ):
            has_s2a = True

    for fen in by_type.get("FENESTRATIONSURFACE:DETAILED", []):
        fname = _field(fen, 0)
        ftype = _field(fen, 1).casefold()
        cons_key = _field(fen, 2).casefold()
        if _field(fen, 6, ""):
            return None, SubsetCheckResult(
                False, f"Fenestration '{fname}' has Frame and Divider"
            )
        layers = constructions.get(cons_key, [])
        if ftype == "window":
            if len(layers) != 1 or layers[0] not in glass_names:
                return None, SubsetCheckResult(
                    False, f"Window '{fname}' construction is not SimpleGlazingSystem"
                )
        elif ftype == "door":
            if not layers or not all(ly in mat_names for ly in layers):
                return None, SubsetCheckResult(
                    False, f"Door '{fname}' uses unsupported material"
                )
        else:
            return None, SubsetCheckResult(
                False, f"Fenestration '{fname}' unsupported type '{_field(fen, 1)}'"
            )

    if by_type.get("PEOPLE") or by_type.get("LIGHTS") or by_type.get("ELECTRICEQUIPMENT") or by_type.get("ZONEINFILTRATION:DESIGNFLOWRATE"):
        has_s2a = True

    if has_multizone:
        rung = "S2b"
    elif has_shading:
        rung = "S3"
    elif has_s2a:
        rung = "S2a"
    elif has_sun:
        rung = "S1"
    else:
        rung = "S0"
    return rung, SubsetCheckResult(True, None)


@dataclass
class GeneralBatch:
    """Flat-CSR packed multi-zone / multi-rung building batch for CUDA/Metal & CPU."""

    batch_size: int
    n_zones_total: int
    n_surfs_total: int
    steps_per_hour: int
    building_ids: list[str]
    rungs: list[str]
    site_idx: np.ndarray               # [B] int32
    terrain_idx: np.ndarray            # [B] int32
    zone_offset: np.ndarray            # [B+1] int32
    surf_offset: np.ndarray            # [B+1] int32
    site_ground_temp: np.ndarray       # [B, 12] float32
    warmup_min_days: np.ndarray        # [B] int32
    warmup_max_days: np.ndarray        # [B] int32
    loads_conv_tol: np.ndarray         # [B] float32
    temp_conv_tol: np.ndarray          # [B] float32
    h_conv_min: np.ndarray             # [B] float32

    # Per-zone [Z]
    zone_names: list[str]
    zone_surf_offset: np.ndarray       # [Z+1] int32
    zone_sf_offset: np.ndarray         # [Z+1] int32
    zone_bldg_idx: np.ndarray          # [Z] int32
    zone_volume: np.ndarray            # [Z] float32
    zone_floor_area: np.ndarray        # [Z] float32
    zone_centroid_z: np.ndarray        # [Z] float32
    zone_has_hvac: np.ndarray          # [Z] int32
    zone_has_cooling: np.ndarray       # [Z] int32
    zone_max_heat_supply_t: np.ndarray # [Z] float32
    zone_min_cool_supply_t: np.ndarray # [Z] float32
    zone_heat_sp_hr: np.ndarray        # [Z, 8760] float32
    zone_cool_sp_hr: np.ndarray        # [Z, 8760] float32
    zone_gain_conv_hr: np.ndarray      # [Z, 8760] float32
    zone_gain_rad_hr: np.ndarray       # [Z, 8760] float32
    zone_vent_flow_hr: np.ndarray      # [Z, 8760] float32
    zone_total_op_aa: np.ndarray       # [Z] float32
    zone_floor_area_sw: np.ndarray     # [Z] float32
    zone_floor_alpha_eff: np.ndarray   # [Z] float32
    zone_total_eps_area: np.ndarray    # [Z] float32

    # Per-surface [S]
    surf_zone_idx: np.ndarray          # [S] int32
    surf_class: np.ndarray             # [S] int32
    surf_boundary: np.ndarray          # [S] int32
    surf_partner_idx: np.ndarray       # [S] int32 (-1 if none)
    surf_area: np.ndarray              # [S] float32
    surf_tilt_deg: np.ndarray          # [S] float32
    surf_cos_tilt: np.ndarray          # [S] float32
    surf_sin_tilt: np.ndarray          # [S] float32
    surf_azimuth_deg: np.ndarray       # [S] float32
    surf_nx: np.ndarray                # [S] float32
    surf_ny: np.ndarray                # [S] float32
    surf_nz: np.ndarray                # [S] float32
    surf_centroid_z: np.ndarray        # [S] float32
    surf_height: np.ndarray            # [S] float32
    surf_roughness_mult: np.ndarray    # [S] float32
    surf_sun_exposed: np.ndarray       # [S] int32
    surf_wind_exposed: np.ndarray      # [S] int32
    surf_solar_abs_out: np.ndarray     # [S] float32
    surf_solar_abs_in: np.ndarray      # [S] float32
    surf_eps_in: np.ndarray            # [S] float32
    surf_eps_out: np.ndarray           # [S] float32
    surf_vf_ground: np.ndarray         # [S] float32
    surf_vf_sky: np.ndarray            # [S] float32
    surf_vf_sky_ir: np.ndarray         # [S] float32
    surf_vf_ground_ir: np.ndarray      # [S] float32
    surf_air_sky_split: np.ndarray     # [S] float32
    surf_osc_c_const: np.ndarray       # [S] float32
    surf_osc_t_const: np.ndarray       # [S] float32
    surf_osc_c_out: np.ndarray         # [S] float32
    surf_osc_c_zone: np.ndarray        # [S] float32
    surf_scon: np.ndarray              # [S] float32
    surf_t_norm: np.ndarray            # [S] float32
    surf_a_norm: np.ndarray            # [S] float32
    surf_tau_diff: np.ndarray          # [S] float32
    surf_abs_diff: np.ndarray          # [S] float32

    # Modal conduction [S] and [S, MAX_MODES]
    surf_n_modes: np.ndarray           # [S] int32
    surf_ctf_out0: np.ndarray          # [S] float32
    surf_ctf_cross0: np.ndarray        # [S] float32
    surf_ctf_in0: np.ndarray           # [S] float32
    surf_lag_oo: np.ndarray            # [S] float32
    surf_lag_oi: np.ndarray            # [S] float32
    surf_lag_io: np.ndarray            # [S] float32
    surf_lag_ii: np.ndarray            # [S] float32
    surf_m_decay: np.ndarray           # [S, MAX_MODES] float32
    surf_m_gno: np.ndarray             # [S, MAX_MODES] float32
    surf_m_gni: np.ndarray             # [S, MAX_MODES] float32
    surf_m_goo: np.ndarray             # [S, MAX_MODES] float32
    surf_m_goi: np.ndarray             # [S, MAX_MODES] float32
    surf_m_co: np.ndarray              # [S, MAX_MODES] float32
    surf_m_ci: np.ndarray              # [S, MAX_MODES] float32
    surf_m_so: np.ndarray              # [S, MAX_MODES] float32
    surf_m_si: np.ndarray              # [S, MAX_MODES] float32

    # Flat CSR interior LWR ScriptF * sigma
    script_f_sigma: np.ndarray         # [SF_total] float32

    # Exterior shading (S3)
    has_shading: int
    surf_dif_sky_shdg: np.ndarray      # [S] float32
    surf_sunlit_u8: np.ndarray         # [S, 8760] uint8 (or [1, 1] dummy if has_shading==0)


def _resolve_hourly_schedule(
    sched_name: str,
    const_scheds: dict[str, float],
    compact_scheds: dict[str, np.ndarray],
    file_scheds: dict[str, ParsedIdfObject],
    search_dirs: list[Path],
    default_val: float = 1.0,
) -> np.ndarray:
    key = sched_name.strip().casefold()
    if not key:
        return np.full(8760, default_val, dtype=np.float64)
    if key in const_scheds:
        return np.full(8760, const_scheds[key], dtype=np.float64)
    if key in compact_scheds:
        return compact_scheds[key].copy()
    if key in file_scheds:
        fsch = file_scheds[key]
        raw_path = _field(fsch, 2)
        col_num = int(round(_float_field(fsch, 3, 1.0)))
        skip_rows = int(round(_float_field(fsch, 4, 0.0)))
        num_hrs = int(round(_float_field(fsch, 5, 8760.0)))
        csv_path = resolve_schedule_path(raw_path, search_dirs)
        return load_schedule_file_hourly(
            csv_path,
            column_number=col_num,
            rows_to_skip=skip_rows,
            num_hours=num_hrs,
        )
    raise ValueError(f"Unknown schedule '{sched_name}'")


def _compile_one_general_building(
    idf_text: str,
    bldg_id: str,
    search_dirs: list[Path],
    weather: WeatherSeries,
    *,
    compute_shading: bool = True,
    shading_device: str = "auto",
    periodic_shadow_days: int = 20,
) -> dict[str, Any]:
    """Compile a single arbitrary S0/S1/S2a/S3/S2b IDF into intermediate dicts."""
    rung, check = check_general_subset(idf_text)
    if not check.passed or rung is None:
        raise ValueError(f"{bldg_id}: failed general subset check: {check.reason}")

    expanded = expand_ideal_loads_templates(idf_text)
    objects = parse_expidf(expanded)
    by_type: dict[str, list[ParsedIdfObject]] = {}
    for obj in objects:
        by_type.setdefault(obj.obj_type, []).append(obj)

    sph = int(round(_float_field(by_type["TIMESTEP"][0], 0, 12.0)))
    dt_sec = 3600.0 / float(sph)

    bldg = by_type["BUILDING"][0]
    terrain_str = _field(bldg, 2, "Country").casefold()
    terrain_idx = TERRAIN_MAP.get(terrain_str, 0)
    loads_conv_tol = _float_field(bldg, 3, 0.04)
    temp_conv_tol = _float_field(bldg, 4, 0.4)
    sol_dist = _field(bldg, 5, "FullExterior").casefold()
    warmup_max_days = int(round(_float_field(bldg, 6, 25.0)))
    warmup_min_days = int(round(_float_field(bldg, 7, 1.0)))

    hb_algo = by_type.get("HEATBALANCEALGORITHM", [])
    h_conv_min = _float_field(hb_algo[0], 2, 0.1) if hb_algo else 0.1

    # Ground temperatures (12 monthly values, default 18 C per EnergyPlus)
    gnd_objs = by_type.get("SITE:GROUNDTEMPERATURE:BUILDINGSURFACE", [])
    if gnd_objs:
        gnd_temps = np.asarray(
            [_float_field(gnd_objs[0], m, 18.0) for m in range(12)], dtype=np.float64
        )
    else:
        gnd_temps = np.full(12, 18.0, dtype=np.float64)

    # Start day of week from RunPeriod
    rp_objs = by_type.get("RUNPERIOD", [])
    dow_map = {
        "sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3,
        "thursday": 4, "friday": 5, "saturday": 6,
    }
    start_dow = dow_map.get(_field(rp_objs[0], 7, "Sunday").casefold(), 0) if rp_objs else 0

    # Parse schedules
    const_scheds: dict[str, float] = {}
    for sch in by_type.get("SCHEDULE:CONSTANT", []):
        const_scheds[_field(sch, 0).casefold()] = _float_field(sch, 2, 0.0)

    compact_scheds: dict[str, np.ndarray] = {}
    for sch in by_type.get("SCHEDULE:COMPACT", []):
        name = _field(sch, 0).casefold()
        compact_scheds[name] = compile_schedule_compact_hourly(
            sch.fields, start_day_of_week=start_dow
        )

    file_scheds: dict[str, ParsedIdfObject] = {
        _field(sch, 0).casefold(): sch for sch in by_type.get("SCHEDULE:FILE", [])
    }

    # Parse materials & constructions -> ModalConductionModel cache
    mat_specs: dict[str, tuple[LayerSpec, float, float, float, int]] = {}
    for o in by_type.get("MATERIAL:NOMASS", []):
        k = _field(o, 0).casefold()
        r_val = _float_field(o, 2)
        eps = _float_field(o, 3, 0.9)
        sabs = _float_field(o, 4, 0.7)
        rough = ROUGHNESS_MAP.get(_field(o, 1, "MediumRough").casefold(), 2)
        mat_specs[k] = (LayerSpec(k, True, r_val), eps, sabs, sabs, rough)

    for o in by_type.get("MATERIAL:AIRGAP", []):
        k = _field(o, 0).casefold()
        r_val = _float_field(o, 1, 0.15)
        mat_specs[k] = (LayerSpec(k, True, r_val), 0.9, 0.7, 0.7, 3)

    for o in by_type.get("MATERIAL", []):
        k = _field(o, 0).casefold()
        thick = _float_field(o, 2)
        cond = _float_field(o, 3)
        dens = _float_field(o, 4)
        cp = _float_field(o, 5)
        eps = _float_field(o, 6, 0.9)
        sabs = _float_field(o, 7, 0.7)
        rough = ROUGHNESS_MAP.get(_field(o, 1, "MediumRough").casefold(), 2)
        mat_specs[k] = (
            LayerSpec(k, False, thick / max(cond, 1.0e-9), thick, cond, dens, cp),
            eps,
            sabs,
            sabs,
            rough,
        )

    glass_map: dict[str, tuple[float, float]] = {}
    for o in by_type.get("WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", []):
        glass_map[_field(o, 0).casefold()] = (_float_field(o, 1), _float_field(o, 2))

    cons_layers: dict[str, list[str]] = {}
    for o in by_type.get("CONSTRUCTION", []):
        cons_layers[_field(o, 0).casefold()] = [
            f.strip().casefold() for f in o.fields[1:] if f.strip()
        ]

    modal_cache: dict[str, Any] = {}

    def _get_opaque_cons(cons_key: str) -> tuple[Any, float, float, float, float, float]:
        layers_k = cons_layers[cons_key]
        outer_mat = mat_specs[layers_k[0]]
        inner_mat = mat_specs[layers_k[-1]]
        if cons_key not in modal_cache:
            layer_objs = [mat_specs[lk][0] for lk in layers_k]
            modal_cache[cons_key] = build_modal_conduction(
                layer_objs, dt_sec=dt_sec, construction_name=cons_key, max_modes=MAX_MODES
            )
        return (
            modal_cache[cons_key],
            outer_mat[1],  # eps_out
            inner_mat[1],  # eps_in
            outer_mat[2],  # sol_abs_out
            inner_mat[3],  # sol_abs_in
            ROUGHNESS_MULTIPLIERS[outer_mat[4]],
        )

    osc_map: dict[str, ParsedIdfObject] = {
        _field(o, 0).casefold(): o
        for o in by_type.get("SURFACEPROPERTY:OTHERSIDECOEFFICIENTS", [])
    }

    # Index zones
    zone_objs = by_type["ZONE"]
    zone_key_to_local: dict[str, int] = {}
    zones_data: list[dict[str, Any]] = []
    for zi, zobj in enumerate(zone_objs):
        zname = _field(zobj, 0).upper()
        zone_key_to_local[zname.casefold()] = zi
        zvol = _float_field(zobj, 8, 0.0)
        zflr = _float_field(zobj, 9, 0.0)
        zones_data.append(
            {
                "name": zname,
                "volume": zvol,
                "floor_area": zflr,
                "surfaces": [],
                "cen_accum": np.zeros(3, dtype=np.float64),
                "gross_area_sum": 0.0,
                "computed_floor_area": 0.0,
                "z_min": 1.0e9,
                "z_max": -1.0e9,
            }
        )

    # Index fenestrations by host surface
    fens_by_host: dict[str, list[ParsedIdfObject]] = {}
    for fen in by_type.get("FENESTRATIONSURFACE:DETAILED", []):
        fens_by_host.setdefault(_field(fen, 3).casefold(), []).append(fen)

    # Build surfaces grouped per zone
    for surf in by_type.get("BUILDINGSURFACE:DETAILED", []):
        sname = _field(surf, 0).upper()
        stype = _field(surf, 1).casefold()
        if stype == "floor":
            sclass = SURF_FLOOR
        elif stype in ("roof", "ceiling"):
            sclass = SURF_ROOF
        else:
            sclass = SURF_WALL

        zkey = _field(surf, 3).casefold()
        if zkey not in zone_key_to_local:
            continue
        zi = zone_key_to_local[zkey]
        zdata = zones_data[zi]

        cons_key = _field(surf, 2).casefold()
        mc, eps_out, eps_in, sabs_out, sabs_in, rough_mult = _get_opaque_cons(cons_key)

        bc_str = _field(surf, 5).casefold()
        bc_obj = _field(surf, 6).casefold()
        osc_c_const = osc_t_const = osc_c_out = osc_c_zone = 0.0
        partner_name = ""
        if bc_str == "outdoors":
            boundary = BOUND_OUTDOORS
        elif bc_str == "othersidecoefficients":
            boundary = BOUND_OSC
            osc = osc_map[bc_obj]
            osc_t_const = _float_field(osc, 2, 0.0)
            osc_c_const = _float_field(osc, 3, 0.0)
            osc_c_out = _float_field(osc, 4, 0.0)
            osc_c_zone = _float_field(osc, 7, 0.0)
        elif bc_str == "ground":
            boundary = BOUND_GROUND
        elif bc_str == "adiabatic":
            boundary = BOUND_ADIABATIC
        elif bc_str == "surface":
            boundary = BOUND_SURFACE
            partner_name = bc_obj
        else:
            raise ValueError(f"Unsupported BC '{bc_str}'")

        sun_exp = _field(surf, 7, "SunExposed").casefold() == "sunexposed"
        wind_exp = _field(surf, 8, "WindExposed").casefold() == "windexposed"

        verts = _parse_vertices(surf.fields, 11)
        gross_area, normal = _newell_area_and_normal(verts)
        if gross_area < 1.0e-6:
            continue
        az, tilt = _determine_azimuth_and_tilt(verts, normal)
        if sclass == SURF_FLOOR and float(normal[2]) > 1.0e-6:
            verts = verts[::-1].copy()
            gross_area, normal = _newell_area_and_normal(verts)
            az, tilt = _determine_azimuth_and_tilt(verts, normal)
        elif sclass == SURF_ROOF and float(normal[2]) < -1.0e-6:
            verts = verts[::-1].copy()
            gross_area, normal = _newell_area_and_normal(verts)
            az, tilt = _determine_azimuth_and_tilt(verts, normal)

        cos_t = math.cos(math.radians(tilt))
        sin_t = math.sin(math.radians(tilt))
        vf_g_raw = _field(surf, 9, "")
        vf_g = 0.5 * (1.0 - cos_t) if (not vf_g_raw or vf_g_raw.casefold() == "autocalculate") else float(vf_g_raw)
        vf_sky = 0.5 * (1.0 + cos_t)
        air_sky = math.sqrt(max(0.0, vf_sky))
        cen = _polygon_centroid(verts, gross_area)
        height = float(np.linalg.norm(verts[1] - verts[0]))

        zdata["cen_accum"] += np.asarray(cen, dtype=np.float64) * gross_area
        zdata["gross_area_sum"] += gross_area
        zdata["z_min"] = min(zdata["z_min"], float(verts[:, 2].min()))
        zdata["z_max"] = max(zdata["z_max"], float(verts[:, 2].max()))
        if sclass == SURF_FLOOR:
            zdata["computed_floor_area"] += gross_area

        sub_recs: list[dict[str, Any]] = []
        sub_area = 0.0
        for fen in fens_by_host.get(sname.casefold(), []):
            fname = _field(fen, 0).upper()
            ftype = _field(fen, 1).casefold()
            fcons_key = _field(fen, 2).casefold()
            fverts = _parse_vertices(fen.fields, 9)
            farea, fnorm = _newell_area_and_normal(fverts)
            if farea < 1.0e-6:
                continue
            faz, ftilt = _determine_azimuth_and_tilt(fverts, fnorm)
            fcos = math.cos(math.radians(ftilt))
            fsin = math.sin(math.radians(ftilt))
            f_vfg_raw = _field(fen, 5, "")
            f_vfg = 0.5 * (1.0 - fcos) if (not f_vfg_raw or f_vfg_raw.casefold() == "autocalculate") else float(f_vfg_raw)
            f_vfsky = 0.5 * (1.0 + fcos)
            f_airsky = math.sqrt(max(0.0, f_vfsky))
            fcen = _polygon_centroid(fverts, farea)
            fheight = float(np.linalg.norm(fverts[1] - fverts[0]))
            sub_area += farea

            if ftype == "window":
                g_key = cons_layers[fcons_key][0]
                fu, fshgc = glass_map[g_key]
                fscon = float(simple_glazing_layer_conductance(fu, xp=np))
                t_n, _, a_n = simple_glazing_normal_optics(fu, fshgc)
                t_norm = float(t_n)
                a_norm = float(a_n)
                sub_recs.append(
                    {
                        "name": fname,
                        "surf_class": SURF_WINDOW,
                        "boundary": BOUND_WINDOW,
                        "partner_name": "",
                        "area": farea,
                        "tilt_deg": ftilt,
                        "cos_tilt": fcos,
                        "sin_tilt": fsin,
                        "azimuth_deg": faz,
                        "normal": fnorm,
                        "verts": fverts,
                        "centroid_z": fcen[2],
                        "height": max(fheight, 0.1),
                        "roughness_mult": 1.0,
                        "sun_exposed": sun_exp,
                        "wind_exposed": wind_exp,
                        "solar_abs_out": 0.0,
                        "solar_abs_in": 0.0,
                        "eps_in": 0.84,
                        "eps_out": 0.84,
                        "vf_ground": f_vfg,
                        "vf_sky": f_vfsky,
                        "vf_sky_ir": f_vfsky,
                        "vf_ground_ir": 0.5 * (1.0 - fcos),
                        "air_sky_split": f_airsky,
                        "osc": (0.0, 0.0, 0.0, 0.0),
                        "win": (fscon, t_norm, a_norm, 0.887 * t_norm, 0.946 * a_norm),
                        "modal": None,
                    }
                )
            else:
                dmc, d_eo, d_ei, d_so, d_si, d_rm = _get_opaque_cons(fcons_key)
                sub_recs.append(
                    {
                        "name": fname,
                        "surf_class": SURF_DOOR,
                        "boundary": BOUND_DOOR,
                        "partner_name": "",
                        "area": farea,
                        "tilt_deg": ftilt,
                        "cos_tilt": fcos,
                        "sin_tilt": fsin,
                        "azimuth_deg": faz,
                        "normal": fnorm,
                        "verts": fverts,
                        "centroid_z": fcen[2],
                        "height": max(fheight, 0.1),
                        "roughness_mult": d_rm,
                        "sun_exposed": sun_exp,
                        "wind_exposed": wind_exp,
                        "solar_abs_out": d_so,
                        "solar_abs_in": d_si,
                        "eps_in": d_ei,
                        "eps_out": d_eo,
                        "vf_ground": f_vfg,
                        "vf_sky": f_vfsky,
                        "vf_sky_ir": f_vfsky,
                        "vf_ground_ir": 0.5 * (1.0 - fcos),
                        "air_sky_split": f_airsky,
                        "osc": (0.0, 0.0, 0.0, 0.0),
                        "win": (0.0, 0.0, 0.0, 0.0, 0.0),
                        "modal": dmc,
                    }
                )

        net_area = max(gross_area - sub_area, 1.0e-4)
        zdata["surfaces"].append(
            {
                "name": sname,
                "surf_class": sclass,
                "boundary": boundary,
                "partner_name": partner_name,
                "area": net_area,
                "tilt_deg": tilt,
                "cos_tilt": cos_t,
                "sin_tilt": sin_t,
                "azimuth_deg": az,
                "normal": normal,
                "verts": verts,
                "centroid_z": cen[2],
                "height": max(height, 0.1),
                "roughness_mult": rough_mult,
                "sun_exposed": sun_exp,
                "wind_exposed": wind_exp,
                "solar_abs_out": sabs_out,
                "solar_abs_in": sabs_in,
                "eps_in": eps_in,
                "eps_out": eps_out,
                "vf_ground": vf_g,
                "vf_sky": vf_sky,
                "vf_sky_ir": vf_sky,
                "vf_ground_ir": 0.5 * (1.0 - cos_t),
                "air_sky_split": air_sky,
                "osc": (osc_c_const, osc_t_const, osc_c_out, osc_c_zone),
                "win": (0.0, 0.0, 0.0, 0.0, 0.0),
                "modal": mc,
            }
        )
        zdata["surfaces"].extend(sub_recs)

    # InternalMass objects
    for im in by_type.get("INTERNALMASS", []):
        im_name = _field(im, 0).upper()
        cons_key = _field(im, 1).casefold()
        zkey = _field(im, 2).casefold()
        if zkey not in zone_key_to_local:
            continue
        im_area = _float_field(im, 4, 0.0)
        if im_area <= 1.0e-6:
            continue
        mc, eps_out, eps_in, sabs_out, sabs_in, rough_mult = _get_opaque_cons(cons_key)
        zones_data[zone_key_to_local[zkey]]["surfaces"].append(
            {
                "name": im_name,
                "surf_class": SURF_INTMASS,
                "boundary": BOUND_INTMASS,
                "partner_name": "",
                "area": im_area,
                "tilt_deg": 90.0,
                "cos_tilt": 0.0,
                "sin_tilt": 1.0,
                "azimuth_deg": 0.0,
                "normal": np.array([0.0, 1.0, 0.0], dtype=np.float64),
                "verts": np.zeros((0, 3), dtype=np.float64),
                "centroid_z": 0.0,
                "height": 1.0,
                "roughness_mult": rough_mult,
                "sun_exposed": False,
                "wind_exposed": False,
                "solar_abs_out": sabs_out,
                "solar_abs_in": sabs_in,
                "eps_in": eps_in,
                "eps_out": eps_out,
                "vf_ground": 0.0,
                "vf_sky": 0.5,
                "vf_sky_ir": 0.5,
                "vf_ground_ir": 0.0,
                "air_sky_split": math.sqrt(0.5),
                "osc": (0.0, 0.0, 0.0, 0.0),
                "win": (0.0, 0.0, 0.0, 0.0, 0.0),
                "modal": mc,
            }
        )

    # Finalize zone floor areas, volumes, centroids
    for zd in zones_data:
        if zd["floor_area"] <= 1.0e-6:
            zd["floor_area"] = max(zd["computed_floor_area"], 1.0)
        if zd["volume"] <= 1.0e-6:
            h_est = max(zd["z_max"] - zd["z_min"], 2.7) if zd["z_max"] > zd["z_min"] else 2.7
            zd["volume"] = zd["floor_area"] * h_est
        zd["centroid_z"] = (
            float(zd["cen_accum"][2] / zd["gross_area_sum"])
            if zd["gross_area_sum"] > 0.0
            else 1.5
        )
        zd["gain_conv_hr"] = np.zeros(8760, dtype=np.float64)
        zd["gain_rad_hr"] = np.zeros(8760, dtype=np.float64)
        zd["vent_flow_hr"] = np.zeros(8760, dtype=np.float64)
        zd["has_hvac"] = 0
        zd["has_cooling"] = 0
        zd["heat_sp_hr"] = np.full(8760, -100.0, dtype=np.float64)
        zd["cool_sp_hr"] = np.full(8760, 100.0, dtype=np.float64)
        zd["max_heat_supply_t"] = 50.0
        zd["min_cool_supply_t"] = 13.0

    # Internal gains: OtherEquipment, ElectricEquipment, Lights, People
    def _add_equip_gain(obj: ParsedIdfObject, zone_f: int, sch_f: int, meth_f: int, lvl_f: int, wpa_f: int, lat_f: int, rad_f: int, lost_f: int) -> None:
        zkey = _field(obj, zone_f).casefold()
        if zkey not in zone_key_to_local:
            return
        zd = zones_data[zone_key_to_local[zkey]]
        meth = _field(obj, meth_f, "EquipmentLevel").casefold()
        if meth in ("watts/area",):
            design_w = _float_field(obj, wpa_f, 0.0) * zd["floor_area"]
        elif meth in ("equipmentlevel", "lighting level", "lightinglevel"):
            design_w = _float_field(obj, lvl_f, 0.0)
        else:
            design_w = _float_field(obj, lvl_f, 0.0)
        sched = _resolve_hourly_schedule(
            _field(obj, sch_f), const_scheds, compact_scheds, file_scheds, search_dirs, 1.0
        )
        f_lat = _float_field(obj, lat_f, 0.0)
        f_rad = _float_field(obj, rad_f, 0.0)
        f_lost = _float_field(obj, lost_f, 0.0)
        f_conv = max(0.0, 1.0 - f_lat - f_rad - f_lost)
        q_tot = design_w * sched
        zd["gain_conv_hr"] += q_tot * f_conv
        zd["gain_rad_hr"] += q_tot * f_rad

    for eq in by_type.get("OTHEREQUIPMENT", []):
        _add_equip_gain(eq, 2, 3, 4, 5, 6, 8, 9, 10)
    for eq in by_type.get("ELECTRICEQUIPMENT", []):
        _add_equip_gain(eq, 1, 2, 3, 4, 5, 7, 8, 9)
    for lt in by_type.get("LIGHTS", []):
        # Lights: Name(0), Zone(1), Sched(2), Method(3), Level(4), W/area(5), W/pers(6), ReturnAirFrac(7), FracRad(8), FracVis(9)
        zkey = _field(lt, 1).casefold()
        if zkey not in zone_key_to_local:
            continue
        zd = zones_data[zone_key_to_local[zkey]]
        meth = _field(lt, 3, "LightingLevel").casefold()
        design_w = (
            _float_field(lt, 5, 0.0) * zd["floor_area"]
            if meth == "watts/area"
            else _float_field(lt, 4, 0.0)
        )
        sched = _resolve_hourly_schedule(
            _field(lt, 2), const_scheds, compact_scheds, file_scheds, search_dirs, 1.0
        )
        f_ret = _float_field(lt, 7, 0.0)
        f_rad = _float_field(lt, 8, 0.0) + _float_field(lt, 9, 0.0)
        f_conv = max(0.0, 1.0 - f_ret - f_rad)
        q_tot = design_w * sched
        zd["gain_conv_hr"] += q_tot * f_conv
        zd["gain_rad_hr"] += q_tot * f_rad

    for ppl in by_type.get("PEOPLE", []):
        zkey = _field(ppl, 1).casefold()
        if zkey not in zone_key_to_local:
            continue
        zd = zones_data[zone_key_to_local[zkey]]
        meth = _field(ppl, 3, "People").casefold()
        if meth == "people/area":
            n_ppl = _float_field(ppl, 5, 0.0) * zd["floor_area"]
        elif meth == "area/person":
            app = _float_field(ppl, 6, 10.0)
            n_ppl = zd["floor_area"] / max(app, 1.0e-6)
        else:
            n_ppl = _float_field(ppl, 4, 0.0)
        occ_sch = _resolve_hourly_schedule(
            _field(ppl, 2), const_scheds, compact_scheds, file_scheds, search_dirs, 1.0
        )
        act_sch = _resolve_hourly_schedule(
            _field(ppl, 9), const_scheds, compact_scheds, file_scheds, search_dirs, 120.0
        )
        f_rad = _float_field(ppl, 7, 0.3)
        # Approx sensible fraction ~0.6 of total metabolic activity
        q_sens = n_ppl * occ_sch * act_sch * 0.6
        zd["gain_rad_hr"] += q_sens * f_rad
        zd["gain_conv_hr"] += q_sens * (1.0 - f_rad)

    # Ventilation & Infiltration
    for obj in by_type.get("ZONEVENTILATION:DESIGNFLOWRATE", []) + by_type.get(
        "ZONEINFILTRATION:DESIGNFLOWRATE", []
    ):
        zkey = _field(obj, 1).casefold()
        if zkey not in zone_key_to_local:
            continue
        zd = zones_data[zone_key_to_local[zkey]]
        sched = _resolve_hourly_schedule(
            _field(obj, 2), const_scheds, compact_scheds, file_scheds, search_dirs, 1.0
        )
        meth = _field(obj, 3).casefold()
        if meth == "airchanges/hour":
            flow = _float_field(obj, 7, 0.0) * zd["volume"] / 3600.0
        elif meth == "flow/zone":
            flow = _float_field(obj, 4, 0.0)
        elif meth == "flow/area":
            flow = _float_field(obj, 5, 0.0) * zd["floor_area"]
        else:
            flow = 0.0
        zd["vent_flow_hr"] += flow * sched

    # Thermostats & IdealLoads per zone
    dual_sp: dict[str, tuple[str, str]] = {
        _field(o, 0).casefold(): (_field(o, 1), _field(o, 2))
        for o in by_type.get("THERMOSTATSETPOINT:DUALSETPOINT", [])
    }
    zone_tstat: dict[str, tuple[str, str]] = {}
    for zc in by_type.get("ZONECONTROL:THERMOSTAT", []):
        zkey = _field(zc, 1).casefold()
        sp_obj_key = _field(zc, 4).casefold()
        if sp_obj_key in dual_sp:
            zone_tstat[zkey] = dual_sp[sp_obj_key]

    eqlist_to_ideal: dict[str, str] = {}
    for eql in by_type.get("ZONEHVAC:EQUIPMENTLIST", []):
        eql_key = _field(eql, 0).casefold()
        for idx in range(2, len(eql.fields) - 1):
            if eql.fields[idx].strip().casefold() == "zonehvac:idealloadsairsystem":
                eqlist_to_ideal[eql_key] = eql.fields[idx + 1].strip().casefold()
                break

    ideal_by_name: dict[str, ParsedIdfObject] = {
        _field(o, 0).casefold(): o for o in by_type.get("ZONEHVAC:IDEALLOADSAIRSYSTEM", [])
    }
    for conn in by_type.get("ZONEHVAC:EQUIPMENTCONNECTIONS", []):
        zkey = _field(conn, 0).casefold()
        eql_key = _field(conn, 1).casefold()
        if zkey not in zone_key_to_local or eql_key not in eqlist_to_ideal:
            continue
        ideal_obj = ideal_by_name.get(eqlist_to_ideal[eql_key])
        if ideal_obj is None:
            continue
        zd = zones_data[zone_key_to_local[zkey]]
        zd["has_hvac"] = 1
        zd["max_heat_supply_t"] = _float_field(ideal_obj, 5, 50.0)
        zd["min_cool_supply_t"] = _float_field(ideal_obj, 6, 13.0)
        cool_avail_name = _field(ideal_obj, 16, "")
        cool_avail = _resolve_hourly_schedule(
            cool_avail_name, const_scheds, compact_scheds, file_scheds, search_dirs, 1.0
        )
        zd["has_cooling"] = 1 if float(np.max(cool_avail)) > 1.0e-6 else 0
        if zkey in zone_tstat:
            h_name, c_name = zone_tstat[zkey]
            zd["heat_sp_hr"] = _resolve_hourly_schedule(
                h_name, const_scheds, compact_scheds, file_scheds, search_dirs, 20.0
            )
            zd["cool_sp_hr"] = _resolve_hourly_schedule(
                c_name, const_scheds, compact_scheds, file_scheds, search_dirs, 50.0
            )
        else:
            zd["heat_sp_hr"] = np.full(8760, 20.0, dtype=np.float64)
            zd["cool_sp_hr"] = np.full(8760, 50.0, dtype=np.float64)

    # Exterior shading (S3): gather Shading:Site:Detailed + Shading:Building:Detailed
    shdg_objs = by_type.get("SHADING:SITE:DETAILED", []) + by_type.get(
        "SHADING:BUILDING:DETAILED", []
    )
    occluders: list[np.ndarray] = []
    for sh in shdg_objs:
        # Field 0: Name, Field 1: Transmittance Schedule, Field 2: Number of Vertices, Field 3..: x,y,z
        try:
            occluders.append(_parse_vertices(sh.fields, 3))
        except ValueError:
            pass

    # Flatten surfaces for this building & compute shading if occluders exist
    all_surfs: list[dict[str, Any]] = []
    for zd in zones_data:
        all_surfs.extend(zd["surfaces"])

    n_b_surfs = len(all_surfs)
    sunlit_hr: np.ndarray | None = None
    dif_sky = np.ones(n_b_surfs, dtype=np.float64)
    if compute_shading and occluders and weather.solcos_x is not None:
        # Use explicit Shading:Site:Detailed & Shading:Building:Detailed occluders only
        # (never include coplanar host walls which would self-occlude their own windows).
        all_occ = list(occluders)
        # Hourly solar cosines (take midpoint step of each hour)
        mid = sph // 2
        sx_hr = weather.solcos_x[mid::sph]
        sy_hr = weather.solcos_y[mid::sph]
        sz_hr = weather.solcos_z[mid::sph]
        solcos_hr = np.stack([sx_hr, sy_hr, sz_hr], axis=1)
        sunlit_hr, dif_sky = compute_exterior_shading(
            [s["verts"] for s in all_surfs],
            np.stack([s["normal"] for s in all_surfs], axis=0),
            np.asarray([s["sun_exposed"] for s in all_surfs], dtype=bool),
            all_occ,
            solcos_hr,
            periodic_days=periodic_shadow_days,
            n_grid=3,
            n_sky_rays=128,
            device=shading_device,
        )

    return {
        "building_id": bldg_id,
        "rung": rung,
        "steps_per_hour": sph,
        "terrain_idx": terrain_idx,
        "site_ground_temp": gnd_temps,
        "warmup_min_days": warmup_min_days,
        "warmup_max_days": warmup_max_days,
        "loads_conv_tol": loads_conv_tol,
        "temp_conv_tol": temp_conv_tol,
        "h_conv_min": h_conv_min,
        "zones": zones_data,
        "sunlit_hr": sunlit_hr,
        "dif_sky": dif_sky,
    }


def compile_general_batch(
    idf_paths: list[Path],
    weathers: list[WeatherSeries],
    site_indices: np.ndarray,
    building_ids: list[str] | None = None,
    schedule_dirs: list[Path] | None = None,
    *,
    compute_shading: bool = True,
    shading_device: str = "auto",
    periodic_shadow_days: int = 5,
    max_workers: int = 8,
) -> GeneralBatch:
    """Compile a batch of arbitrary S0/S1/S2a/S3/S2b IDFs in parallel into flat CSR."""
    n_bldg = len(idf_paths)
    ids = building_ids if building_ids is not None else [p.stem for p in idf_paths]
    extra_dirs = list(schedule_dirs or [])

    def _work(idx: int) -> dict[str, Any]:
        p = Path(idf_paths[idx])
        txt = p.read_text(encoding="utf-8", errors="replace")
        eff_sh_dev = (
            shading_device
            if (max_workers == 1 or shading_device == "auto")
            else "cpu"
        )
        return _compile_one_general_building(
            txt,
            ids[idx],
            [p.parent, *extra_dirs],
            weathers[idx],
            compute_shading=compute_shading,
            shading_device=eff_sh_dev,
            periodic_shadow_days=periodic_shadow_days,
        )

    if n_bldg > 1 and max_workers > 1:
        with ThreadPoolExecutor(max_workers=min(max_workers, n_bldg)) as pool:
            compiled = list(pool.map(_work, range(n_bldg)))
    else:
        compiled = [_work(i) for i in range(n_bldg)]

    return pack_compiled_general_buildings(compiled, site_indices, building_ids=ids)


def pack_compiled_general_buildings(
    compiled: list[dict[str, Any]],
    site_indices: np.ndarray,
    building_ids: list[str] | None = None,
) -> GeneralBatch:
    """Pack a list of compiled building dicts into a flat-CSR ``GeneralBatch``."""
    n_bldg = len(compiled)
    ids = building_ids if building_ids is not None else [str(c["building_id"]) for c in compiled]
    sph = int(compiled[0]["steps_per_hour"])
    zone_offset = np.zeros(n_bldg + 1, dtype=np.int32)
    surf_offset = np.zeros(n_bldg + 1, dtype=np.int32)
    z_total = 0
    s_total = 0
    for bi, item in enumerate(compiled):
        z_total += len(item["zones"])
        s_total += sum(len(z["surfaces"]) for z in item["zones"])
        zone_offset[bi + 1] = z_total
        surf_offset[bi + 1] = s_total

    # Allocate flat CSR arrays
    terrain_idx = np.zeros(n_bldg, dtype=np.int32)
    site_ground_temp = np.zeros((n_bldg, 12), dtype=np.float32)
    warmup_min_days = np.zeros(n_bldg, dtype=np.int32)
    warmup_max_days = np.zeros(n_bldg, dtype=np.int32)
    loads_conv_tol = np.zeros(n_bldg, dtype=np.float32)
    temp_conv_tol = np.zeros(n_bldg, dtype=np.float32)
    h_conv_min = np.zeros(n_bldg, dtype=np.float32)

    zone_names: list[str] = []
    zone_surf_offset = np.zeros(z_total + 1, dtype=np.int32)
    zone_sf_offset = np.zeros(z_total + 1, dtype=np.int32)
    zone_bldg_idx = np.zeros(z_total, dtype=np.int32)
    zone_volume = np.zeros(z_total, dtype=np.float32)
    zone_floor_area = np.zeros(z_total, dtype=np.float32)
    zone_centroid_z = np.zeros(z_total, dtype=np.float32)
    zone_has_hvac = np.zeros(z_total, dtype=np.int32)
    zone_has_cooling = np.zeros(z_total, dtype=np.int32)
    zone_max_heat_supply_t = np.zeros(z_total, dtype=np.float32)
    zone_min_cool_supply_t = np.zeros(z_total, dtype=np.float32)
    zone_heat_sp_hr = np.zeros((z_total, 8760), dtype=np.float32)
    zone_cool_sp_hr = np.zeros((z_total, 8760), dtype=np.float32)
    zone_gain_conv_hr = np.zeros((z_total, 8760), dtype=np.float32)
    zone_gain_rad_hr = np.zeros((z_total, 8760), dtype=np.float32)
    zone_vent_flow_hr = np.zeros((z_total, 8760), dtype=np.float32)
    zone_total_op_aa = np.zeros(z_total, dtype=np.float32)
    zone_floor_area_sw = np.zeros(z_total, dtype=np.float32)
    zone_floor_alpha_eff = np.zeros(z_total, dtype=np.float32)
    zone_total_eps_area = np.zeros(z_total, dtype=np.float32)

    surf_zone_idx = np.zeros(s_total, dtype=np.int32)
    surf_class = np.zeros(s_total, dtype=np.int32)
    surf_boundary = np.zeros(s_total, dtype=np.int32)
    surf_partner_idx = np.full(s_total, -1, dtype=np.int32)
    surf_area = np.zeros(s_total, dtype=np.float32)
    surf_tilt_deg = np.zeros(s_total, dtype=np.float32)
    surf_cos_tilt = np.zeros(s_total, dtype=np.float32)
    surf_sin_tilt = np.zeros(s_total, dtype=np.float32)
    surf_azimuth_deg = np.zeros(s_total, dtype=np.float32)
    surf_nx = np.zeros(s_total, dtype=np.float32)
    surf_ny = np.zeros(s_total, dtype=np.float32)
    surf_nz = np.zeros(s_total, dtype=np.float32)
    surf_centroid_z = np.zeros(s_total, dtype=np.float32)
    surf_height = np.zeros(s_total, dtype=np.float32)
    surf_roughness_mult = np.zeros(s_total, dtype=np.float32)
    surf_sun_exposed = np.zeros(s_total, dtype=np.int32)
    surf_wind_exposed = np.zeros(s_total, dtype=np.int32)
    surf_solar_abs_out = np.zeros(s_total, dtype=np.float32)
    surf_solar_abs_in = np.zeros(s_total, dtype=np.float32)
    surf_eps_in = np.zeros(s_total, dtype=np.float32)
    surf_eps_out = np.zeros(s_total, dtype=np.float32)
    surf_vf_ground = np.zeros(s_total, dtype=np.float32)
    surf_vf_sky = np.zeros(s_total, dtype=np.float32)
    surf_vf_sky_ir = np.zeros(s_total, dtype=np.float32)
    surf_vf_ground_ir = np.zeros(s_total, dtype=np.float32)
    surf_air_sky_split = np.zeros(s_total, dtype=np.float32)
    surf_osc_c_const = np.zeros(s_total, dtype=np.float32)
    surf_osc_t_const = np.zeros(s_total, dtype=np.float32)
    surf_osc_c_out = np.zeros(s_total, dtype=np.float32)
    surf_osc_c_zone = np.zeros(s_total, dtype=np.float32)
    surf_scon = np.zeros(s_total, dtype=np.float32)
    surf_t_norm = np.zeros(s_total, dtype=np.float32)
    surf_a_norm = np.zeros(s_total, dtype=np.float32)
    surf_tau_diff = np.zeros(s_total, dtype=np.float32)
    surf_abs_diff = np.zeros(s_total, dtype=np.float32)

    surf_n_modes = np.zeros(s_total, dtype=np.int32)
    surf_ctf_out0 = np.zeros(s_total, dtype=np.float32)
    surf_ctf_cross0 = np.zeros(s_total, dtype=np.float32)
    surf_ctf_in0 = np.zeros(s_total, dtype=np.float32)
    surf_lag_oo = np.zeros(s_total, dtype=np.float32)
    surf_lag_oi = np.zeros(s_total, dtype=np.float32)
    surf_lag_io = np.zeros(s_total, dtype=np.float32)
    surf_lag_ii = np.zeros(s_total, dtype=np.float32)
    surf_m_decay = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_gno = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_gni = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_goo = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_goi = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_co = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_ci = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_so = np.zeros((s_total, MAX_MODES), dtype=np.float32)
    surf_m_si = np.zeros((s_total, MAX_MODES), dtype=np.float32)

    any_shading = any(item["sunlit_hr"] is not None for item in compiled)
    surf_dif_sky_shdg = np.ones(s_total, dtype=np.float32)
    surf_sunlit_u8 = (
        np.full((s_total, 8760), 255, dtype=np.uint8)
        if any_shading
        else np.full((1, 1), 255, dtype=np.uint8)
    )

    sf_chunks: list[np.ndarray] = []
    sf_cursor = 0
    z_cursor = 0
    s_cursor = 0

    for bi, item in enumerate(compiled):
        terrain_idx[bi] = int(item["terrain_idx"])
        site_ground_temp[bi] = item["site_ground_temp"].astype(np.float32)
        warmup_min_days[bi] = int(item["warmup_min_days"])
        warmup_max_days[bi] = int(item["warmup_max_days"])
        loads_conv_tol[bi] = float(item["loads_conv_tol"])
        temp_conv_tol[bi] = float(item["temp_conv_tol"])
        h_conv_min[bi] = float(item["h_conv_min"])

        # Track surface name -> global index within this building for interzone pairing
        bldg_name_to_sidx: dict[str, int] = {}
        bldg_partner_requests: list[tuple[int, str]] = []
        bldg_s_local = 0

        for zd in item["zones"]:
            zi = z_cursor
            z_cursor += 1
            zone_names.append(f"{item['building_id']}::{zd['name']}")
            zone_bldg_idx[zi] = bi
            zone_volume[zi] = float(zd["volume"])
            zone_floor_area[zi] = float(zd["floor_area"])
            zone_centroid_z[zi] = float(zd["centroid_z"])
            zone_has_hvac[zi] = int(zd["has_hvac"])
            zone_has_cooling[zi] = int(zd["has_cooling"])
            zone_max_heat_supply_t[zi] = float(zd["max_heat_supply_t"])
            zone_min_cool_supply_t[zi] = float(zd["min_cool_supply_t"])
            zone_heat_sp_hr[zi] = zd["heat_sp_hr"].astype(np.float32)
            zone_cool_sp_hr[zi] = zd["cool_sp_hr"].astype(np.float32)
            zone_gain_conv_hr[zi] = zd["gain_conv_hr"].astype(np.float32)
            zone_gain_rad_hr[zi] = zd["gain_rad_hr"].astype(np.float32)
            zone_vent_flow_hr[zi] = zd["vent_flow_hr"].astype(np.float32)

            surfs = zd["surfaces"]
            n_sz = len(surfs)
            zone_surf_offset[zi] = s_cursor
            zone_surf_offset[zi + 1] = s_cursor + n_sz

            # Per-zone ScriptF
            if n_sz > 0:
                z_areas = np.asarray([s["area"] for s in surfs], dtype=np.float64)
                z_az = np.asarray([s["azimuth_deg"] for s in surfs], dtype=np.float64)
                z_tilt = np.asarray([s["tilt_deg"] for s in surfs], dtype=np.float64)
                z_cls = np.asarray([s["surf_class"] for s in surfs], dtype=np.int32)
                z_eps = np.asarray([s["eps_in"] for s in surfs], dtype=np.float64)
                if n_sz == 1:
                    sf_mat = np.zeros((1, 1), dtype=np.float64)
                else:
                    f_app = calc_approximate_view_factors(z_areas, z_az, z_tilt, z_cls)
                    f_fix = fix_view_factors(z_areas, f_app)
                    sf_mat = calc_script_f(z_areas, f_fix, z_eps)
                sf_flat = (sf_mat * STEFAN_BOLTZMANN).astype(np.float32).reshape(-1)
            else:
                sf_flat = np.zeros(0, dtype=np.float32)
            zone_sf_offset[zi] = sf_cursor
            sf_cursor += len(sf_flat)
            zone_sf_offset[zi + 1] = sf_cursor
            sf_chunks.append(sf_flat)

            # Interior solar & radiant distribution weights
            op_aa = 0.0
            win_loss = 0.0
            flr_a = 0.0
            flr_aa = 0.0
            tot_ea = 0.0
            for s in surfs:
                si = s_cursor
                s_cursor += 1
                bldg_name_to_sidx[s["name"].casefold()] = si
                if s["partner_name"]:
                    bldg_partner_requests.append((si, s["partner_name"]))

                surf_zone_idx[si] = zi
                surf_class[si] = s["surf_class"]
                surf_boundary[si] = s["boundary"]
                surf_area[si] = s["area"]
                surf_tilt_deg[si] = s["tilt_deg"]
                surf_cos_tilt[si] = s["cos_tilt"]
                surf_sin_tilt[si] = s["sin_tilt"]
                surf_azimuth_deg[si] = s["azimuth_deg"]
                nrm = s["normal"]
                surf_nx[si] = float(nrm[0])
                surf_ny[si] = float(nrm[1])
                surf_nz[si] = float(nrm[2])
                surf_centroid_z[si] = s["centroid_z"]
                surf_height[si] = s["height"]
                surf_roughness_mult[si] = s["roughness_mult"]
                surf_sun_exposed[si] = 1 if s["sun_exposed"] else 0
                surf_wind_exposed[si] = 1 if s["wind_exposed"] else 0
                surf_solar_abs_out[si] = s["solar_abs_out"]
                surf_solar_abs_in[si] = s["solar_abs_in"]
                surf_eps_in[si] = s["eps_in"]
                surf_eps_out[si] = s["eps_out"]
                surf_vf_ground[si] = s["vf_ground"]
                surf_vf_sky[si] = s["vf_sky"]
                surf_vf_sky_ir[si] = s["vf_sky_ir"]
                surf_vf_ground_ir[si] = s["vf_ground_ir"]
                surf_air_sky_split[si] = s["air_sky_split"]
                surf_osc_c_const[si], surf_osc_t_const[si], surf_osc_c_out[si], surf_osc_c_zone[si] = s["osc"]
                surf_scon[si], surf_t_norm[si], surf_a_norm[si], surf_tau_diff[si], surf_abs_diff[si] = s["win"]

                mc = s["modal"]
                if mc is not None:
                    k_m = mc.num_modes
                    surf_n_modes[si] = k_m
                    surf_ctf_out0[si] = mc.ctf_out0
                    surf_ctf_cross0[si] = mc.ctf_cross0
                    surf_ctf_in0[si] = mc.ctf_in0
                    surf_lag_oo[si] = mc.lag_oo
                    surf_lag_oi[si] = mc.lag_oi
                    surf_lag_io[si] = mc.lag_io
                    surf_lag_ii[si] = mc.lag_ii
                    if k_m > 0:
                        surf_m_decay[si, :k_m] = mc.decay.astype(np.float32)
                        surf_m_gno[si, :k_m] = mc.g_new_out.astype(np.float32)
                        surf_m_gni[si, :k_m] = mc.g_new_in.astype(np.float32)
                        surf_m_goo[si, :k_m] = mc.g_old_out.astype(np.float32)
                        surf_m_goi[si, :k_m] = mc.g_old_in.astype(np.float32)
                        surf_m_co[si, :k_m] = mc.c_out.astype(np.float32)
                        surf_m_ci[si, :k_m] = mc.c_in.astype(np.float32)
                        surf_m_so[si, :k_m] = mc.steady_out.astype(np.float32)
                        surf_m_si[si, :k_m] = mc.steady_in.astype(np.float32)

                tot_ea += s["area"] * s["eps_in"]
                if s["boundary"] == BOUND_WINDOW:
                    win_loss += s["area"] * (s["win"][3] + s["win"][4])
                else:
                    op_aa += s["area"] * s["solar_abs_in"]
                    if s["surf_class"] == SURF_FLOOR:
                        flr_a += s["area"]
                        flr_aa += s["area"] * s["solar_abs_in"]

                d_sky = float(item["dif_sky"][bldg_s_local])
                surf_dif_sky_shdg[si] = d_sky
                # EnergyPlus shades exterior LWR to sky by DifShdgRatioIsoSky;
                # obstructed sky fraction radiates to surrounding surfaces at T_air.
                if s["sun_exposed"] and d_sky < 0.9999:
                    orig_vf_sky = s["vf_sky_ir"]
                    surf_vf_sky_ir[si] = orig_vf_sky * d_sky
                    surf_vf_ground_ir[si] = s["vf_ground_ir"] + orig_vf_sky * (1.0 - d_sky)
                if any_shading and item["sunlit_hr"] is not None:
                    q = np.clip(np.round(item["sunlit_hr"][:, bldg_s_local] * 255.0), 0, 255).astype(np.uint8)
                    surf_sunlit_u8[si] = q
                bldg_s_local += 1

            zone_total_op_aa[zi] = float(op_aa + win_loss)
            zone_floor_area_sw[zi] = float(flr_a)
            zone_floor_alpha_eff[zi] = float(flr_aa / flr_a) if flr_a > 1.0e-6 else 0.7
            zone_total_eps_area[zi] = float(max(tot_ea, 1.0e-6))

        # Resolve interzone Surface partner indices
        for si, pname in bldg_partner_requests:
            partner_si = bldg_name_to_sidx.get(pname, -1)
            if partner_si >= 0:
                surf_partner_idx[si] = partner_si
            else:
                # Missing partner -> treat as adiabatic safely
                surf_boundary[si] = BOUND_ADIABATIC
                surf_partner_idx[si] = -1

    script_f_sigma = (
        np.concatenate(sf_chunks, axis=0)
        if sf_chunks
        else np.zeros(0, dtype=np.float32)
    )

    return GeneralBatch(
        batch_size=n_bldg,
        n_zones_total=z_total,
        n_surfs_total=s_total,
        steps_per_hour=sph,
        building_ids=list(ids),
        rungs=[str(item["rung"]) for item in compiled],
        site_idx=np.asarray(site_indices, dtype=np.int32),
        terrain_idx=terrain_idx,
        zone_offset=zone_offset,
        surf_offset=surf_offset,
        site_ground_temp=site_ground_temp,
        warmup_min_days=warmup_min_days,
        warmup_max_days=warmup_max_days,
        loads_conv_tol=loads_conv_tol,
        temp_conv_tol=temp_conv_tol,
        h_conv_min=h_conv_min,
        zone_names=zone_names,
        zone_surf_offset=zone_surf_offset,
        zone_sf_offset=zone_sf_offset,
        zone_bldg_idx=zone_bldg_idx,
        zone_volume=zone_volume,
        zone_floor_area=zone_floor_area,
        zone_centroid_z=zone_centroid_z,
        zone_has_hvac=zone_has_hvac,
        zone_has_cooling=zone_has_cooling,
        zone_max_heat_supply_t=zone_max_heat_supply_t,
        zone_min_cool_supply_t=zone_min_cool_supply_t,
        zone_heat_sp_hr=zone_heat_sp_hr,
        zone_cool_sp_hr=zone_cool_sp_hr,
        zone_gain_conv_hr=zone_gain_conv_hr,
        zone_gain_rad_hr=zone_gain_rad_hr,
        zone_vent_flow_hr=zone_vent_flow_hr,
        zone_total_op_aa=zone_total_op_aa,
        zone_floor_area_sw=zone_floor_area_sw,
        zone_floor_alpha_eff=zone_floor_alpha_eff,
        zone_total_eps_area=zone_total_eps_area,
        surf_zone_idx=surf_zone_idx,
        surf_class=surf_class,
        surf_boundary=surf_boundary,
        surf_partner_idx=surf_partner_idx,
        surf_area=surf_area,
        surf_tilt_deg=surf_tilt_deg,
        surf_cos_tilt=surf_cos_tilt,
        surf_sin_tilt=surf_sin_tilt,
        surf_azimuth_deg=surf_azimuth_deg,
        surf_nx=surf_nx,
        surf_ny=surf_ny,
        surf_nz=surf_nz,
        surf_centroid_z=surf_centroid_z,
        surf_height=surf_height,
        surf_roughness_mult=surf_roughness_mult,
        surf_sun_exposed=surf_sun_exposed,
        surf_wind_exposed=surf_wind_exposed,
        surf_solar_abs_out=surf_solar_abs_out,
        surf_solar_abs_in=surf_solar_abs_in,
        surf_eps_in=surf_eps_in,
        surf_eps_out=surf_eps_out,
        surf_vf_ground=surf_vf_ground,
        surf_vf_sky=surf_vf_sky,
        surf_vf_sky_ir=surf_vf_sky_ir,
        surf_vf_ground_ir=surf_vf_ground_ir,
        surf_air_sky_split=surf_air_sky_split,
        surf_osc_c_const=surf_osc_c_const,
        surf_osc_t_const=surf_osc_t_const,
        surf_osc_c_out=surf_osc_c_out,
        surf_osc_c_zone=surf_osc_c_zone,
        surf_scon=surf_scon,
        surf_t_norm=surf_t_norm,
        surf_a_norm=surf_a_norm,
        surf_tau_diff=surf_tau_diff,
        surf_abs_diff=surf_abs_diff,
        surf_n_modes=surf_n_modes,
        surf_ctf_out0=surf_ctf_out0,
        surf_ctf_cross0=surf_ctf_cross0,
        surf_ctf_in0=surf_ctf_in0,
        surf_lag_oo=surf_lag_oo,
        surf_lag_oi=surf_lag_oi,
        surf_lag_io=surf_lag_io,
        surf_lag_ii=surf_lag_ii,
        surf_m_decay=surf_m_decay,
        surf_m_gno=surf_m_gno,
        surf_m_gni=surf_m_gni,
        surf_m_goo=surf_m_goo,
        surf_m_goi=surf_m_goi,
        surf_m_co=surf_m_co,
        surf_m_ci=surf_m_ci,
        surf_m_so=surf_m_so,
        surf_m_si=surf_m_si,
        script_f_sigma=script_f_sigma,
        has_shading=1 if any_shading else 0,
        surf_dif_sky_shdg=surf_dif_sky_shdg,
        surf_sunlit_u8=surf_sunlit_u8,
    )
