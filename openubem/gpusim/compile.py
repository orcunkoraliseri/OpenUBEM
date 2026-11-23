from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np

from openubem.gpusim.schedules import (
    load_schedule_file_hourly,
    resolve_schedule_path,
)
from openubem.gpusim.subset import (
    ParsedIdfObject,
    check_s0_subset,
    check_s1_subset,
    parse_expidf,
)

BOUND_OSC = 0
BOUND_OUTDOORS = 1
BOUND_INTMASS = 2
BOUND_WINDOW = 3
BOUND_DOOR = 4

SURF_WALL = 0
SURF_FLOOR = 1
SURF_ROOF = 2
SURF_WINDOW = 3
SURF_DOOR = 4
SURF_INTMASS = 5

ROUGHNESS_MAP: dict[str, int] = {
    "veryrough": 0,
    "rough": 1,
    "mediumrough": 2,
    "mediumsmooth": 3,
    "smooth": 4,
    "verysmooth": 5,
}


@dataclass(frozen=True)
class SurfaceRecord:
    """Intermediate compiled record for one heat-transfer surface.

    Attributes:
        name: Surface name (uppercase, matching EnergyPlus EIO).
        surf_class: Integer surface class constant (``SURF_*``).
        boundary: Integer boundary condition constant (``BOUND_*``).
        area: Net heat-transfer area in m2.
        gross_area: Gross area before subtracting subsurfaces in m2.
        tilt_deg: Surface tilt in degrees after floor/roof flip.
        cos_tilt: Cosine of tilt.
        sin_tilt: Sine of tilt.
        azimuth_deg: Outward normal azimuth in degrees.
        centroid_xyz: Surface centroid coordinates ``(x, y, z)`` in meters.
        u_value: Opaque conductance (W/m2-K) or simple-glazing U-factor.
        shgc: Window SHGC (0 for opaque surfaces).
        osc_c_const: OSC constant temperature coefficient.
        osc_t_const: OSC constant temperature in C.
        osc_c_out: OSC outdoor dry-bulb coefficient.
        osc_c_zone: OSC zone air temperature coefficient.
        vf_ground: View factor to ground.
        vf_sky: View factor to sky.
        vf_sky_ir: IR view factor to sky.
        vf_ground_ir: IR view factor to ground.
        air_sky_rad_split: ``sqrt(0.5 * (1 + cos_tilt))``.
        eps_in: Inside face thermal absorptance / emissivity.
        eps_out: Outside face thermal absorptance / emissivity.
        roughness: Integer roughness index (``ROUGHNESS_MAP``).
        height: Surface height in meters.
        width: Surface width in meters.
    """

    name: str
    surf_class: int
    boundary: int
    area: float
    gross_area: float
    tilt_deg: float
    cos_tilt: float
    sin_tilt: float
    azimuth_deg: float
    centroid_xyz: tuple[float, float, float]
    u_value: float
    shgc: float
    osc_c_const: float
    osc_t_const: float
    osc_c_out: float
    osc_c_zone: float
    vf_ground: float
    vf_sky: float
    vf_sky_ir: float
    vf_ground_ir: float
    air_sky_rad_split: float
    eps_in: float
    eps_out: float
    roughness: int
    height: float
    width: float
    sun_exposed: bool = False
    wind_exposed: bool = False
    solar_abs_out: float = 0.7
    solar_abs_in: float = 0.7


@dataclass(frozen=True)
class BatchSpec:
    """Batched dense float64 specification for a set of S0 buildings.

    Attributes:
        batch_size: Number of buildings ``B``.
        max_surfaces: Maximum surface count ``S`` across the batch.
        steps_per_hour: Number of zone timesteps per hour.
        cell_ids: List of building identifiers of length ``B``.
        site_epw_ids: List of EPW identifiers of length ``B``.
        surf_names: Nested list of uppercase surface names ``[B][S]`` (empty for pad).
        surf_mask: Boolean mask ``[B, S]`` marking active surfaces.
        surf_class: Integer surface class ``[B, S]``.
        surf_boundary: Integer boundary kind ``[B, S]``.
        surf_area: Net surface area in m2 ``[B, S]``.
        surf_gross_area: Gross surface area in m2 ``[B, S]``.
        surf_tilt_deg: Surface tilt in degrees ``[B, S]``.
        surf_cos_tilt: Cosine of surface tilt ``[B, S]``.
        surf_sin_tilt: Sine of surface tilt ``[B, S]``.
        surf_azimuth_deg: Surface azimuth in degrees ``[B, S]``.
        surf_centroid_z: Surface centroid height in meters ``[B, S]``.
        surf_centroid_xyz: Surface centroid coordinates ``[B, S, 3]``.
        surf_u_value: Steady conductance or glazing U-factor ``[B, S]``.
        surf_shgc: Window SHGC ``[B, S]``.
        surf_osc_c_const: OSC constant-temp coefficient ``[B, S]``.
        surf_osc_t_const: OSC constant temperature in C ``[B, S]``.
        surf_osc_c_out: OSC outdoor dry-bulb coefficient ``[B, S]``.
        surf_osc_c_zone: OSC zone air temperature coefficient ``[B, S]``.
        surf_vf_ground: View factor to ground ``[B, S]``.
        surf_vf_sky: View factor to sky ``[B, S]``.
        surf_vf_sky_ir: IR view factor to sky ``[B, S]``.
        surf_vf_ground_ir: IR view factor to ground ``[B, S]``.
        surf_air_sky_rad_split: Sky-air radiation split ``[B, S]``.
        surf_eps_in: Inside thermal emissivity ``[B, S]``.
        surf_eps_out: Outside thermal emissivity ``[B, S]``.
        surf_roughness: Roughness index ``[B, S]``.
        surf_height: Surface height in meters ``[B, S]``.
        surf_width: Surface width in meters ``[B, S]``.
        zone_volume: Zone air volume in m3 ``[B]``.
        zone_floor_area: Zone floor area in m2 ``[B]``.
        zone_centroid_z: Zone centroid height in meters ``[B]``.
        zone_centroid_xyz: Zone centroid coordinates ``[B, 3]``.
        zone_vent_ach: Ventilation air changes per hour ``[B]``.
        zone_vent_flow_m3s: Ventilation design volume flow in m3/s ``[B]``.
        zone_heat_setpoint: Constant heating setpoint in C ``[B]``.
        zone_cool_setpoint: Constant cooling setpoint in C ``[B]``.
        zone_max_heat_supply_temp: Ideal loads max heating supply temp in C ``[B]``.
        zone_max_heat_supply_humrat: Ideal loads max heating supply W ``[B]``.
        zone_gain_hourly_w: Convective internal gains in W per hour ``[B, 8760]``.
        h_conv_min: Minimum surface convection coefficient in W/m2-K ``[B]``.
        h_conv_max: Maximum surface convection coefficient in W/m2-K ``[B]``.
        warmup_min_days: Minimum warm-up days ``[B]``.
        warmup_max_days: Maximum warm-up days ``[B]``.
        loads_conv_tol: Warm-up loads convergence tolerance ``[B]``.
        temp_conv_tol: Warm-up temperature convergence tolerance in K ``[B]``.
        site_elevation: Site elevation in meters ``[B]``.
    """

    batch_size: int
    max_surfaces: int
    steps_per_hour: int
    cell_ids: list[str]
    site_epw_ids: list[str]
    surf_names: list[list[str]]
    surf_mask: np.ndarray
    surf_class: np.ndarray
    surf_boundary: np.ndarray
    surf_area: np.ndarray
    surf_gross_area: np.ndarray
    surf_tilt_deg: np.ndarray
    surf_cos_tilt: np.ndarray
    surf_sin_tilt: np.ndarray
    surf_azimuth_deg: np.ndarray
    surf_centroid_z: np.ndarray
    surf_centroid_xyz: np.ndarray
    surf_u_value: np.ndarray
    surf_shgc: np.ndarray
    surf_osc_c_const: np.ndarray
    surf_osc_t_const: np.ndarray
    surf_osc_c_out: np.ndarray
    surf_osc_c_zone: np.ndarray
    surf_vf_ground: np.ndarray
    surf_vf_sky: np.ndarray
    surf_vf_sky_ir: np.ndarray
    surf_vf_ground_ir: np.ndarray
    surf_air_sky_rad_split: np.ndarray
    surf_eps_in: np.ndarray
    surf_eps_out: np.ndarray
    surf_roughness: np.ndarray
    surf_height: np.ndarray
    surf_width: np.ndarray
    zone_volume: np.ndarray
    zone_floor_area: np.ndarray
    zone_centroid_z: np.ndarray
    zone_centroid_xyz: np.ndarray
    zone_vent_ach: np.ndarray
    zone_vent_flow_m3s: np.ndarray
    zone_heat_setpoint: np.ndarray
    zone_cool_setpoint: np.ndarray
    zone_max_heat_supply_temp: np.ndarray
    zone_max_heat_supply_humrat: np.ndarray
    zone_gain_hourly_w: np.ndarray
    h_conv_min: np.ndarray
    h_conv_max: np.ndarray
    warmup_min_days: np.ndarray
    warmup_max_days: np.ndarray
    loads_conv_tol: np.ndarray
    temp_conv_tol: np.ndarray
    site_elevation: np.ndarray
    surf_sun_exposed: np.ndarray | None = None
    surf_wind_exposed: np.ndarray | None = None
    surf_solar_abs_out: np.ndarray | None = None
    surf_solar_abs_in: np.ndarray | None = None


def _field(obj: ParsedIdfObject, index: int, default: str = "") -> str:
    """Return trimmed field value or default.

    Args:
        obj: Parsed IDF object.
        index: Zero-based field index.
        default: Default string when missing or blank.

    Returns:
        Field string.
    """
    if index >= len(obj.fields):
        return default
    val = obj.fields[index].strip()
    return val if val else default


def _float_field(obj: ParsedIdfObject, index: int, default: float = 0.0) -> float:
    """Return float field value or default.

    Args:
        obj: Parsed IDF object.
        index: Zero-based field index.
        default: Default float when missing or blank.

    Returns:
        Float value.
    """
    raw = _field(obj, index, "")
    return float(raw) if raw else default


def _newell_area_and_normal(
    verts: np.ndarray,
) -> tuple[float, np.ndarray]:
    """Vectors.cc::CreateNewellAreaVector"""
    n_sides = len(verts)
    v1 = verts[1] - verts[0]
    area_vec = np.zeros(3, dtype=np.float64)
    for idx in range(2, n_sides):
        v2 = verts[idx] - verts[0]
        area_vec += np.cross(v1, v2)
        v1 = v2
    area_vec *= 0.5
    gross_area = float(np.linalg.norm(area_vec))

    xval = 0.0
    yval = 0.0
    zval = 0.0
    for idx in range(n_sides):
        cur = verts[idx]
        nxt = verts[(idx + 1) % n_sides]
        xval += (cur[1] - nxt[1]) * (cur[2] + nxt[2])
        yval += (cur[2] - nxt[2]) * (cur[0] + nxt[0])
        zval += (cur[0] - nxt[0]) * (cur[1] + nxt[1])
    norm_vec = np.array([xval, yval, zval], dtype=np.float64)
    norm_len = float(np.linalg.norm(norm_vec))
    if norm_len > 0.0:
        norm_vec = norm_vec / norm_len
    return gross_area, norm_vec


def _determine_azimuth_and_tilt(
    verts: np.ndarray, normal: np.ndarray
) -> tuple[float, float]:
    """Vectors.cc::DetermineAzimuthAndTilt"""
    v0 = verts[2] - verts[1]
    v1 = verts[0] - verts[1]
    v2 = np.cross(v0, v1)
    v2_norm = float(np.linalg.norm(v2))
    cs3_2 = v2 / v2_norm if v2_norm > 0.0 else normal
    v0_norm = float(np.linalg.norm(v0))
    cs3_0 = v0 / v0_norm if v0_norm > 0.0 else np.array([1.0, 0.0, 0.0])

    z_unit = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    costheta = float(np.dot(cs3_2, z_unit))
    if abs(costheta) < 1.0 - 1.12e-16:
        x2 = np.cross(z_unit, cs3_2)
        rotang_0 = math.atan2(float(x2[1]), float(x2[0]))
    else:
        rotang_0 = math.atan2(float(cs3_0[1]), float(cs3_0[0]))

    nz = max(-1.0, min(1.0, float(normal[2])))
    tilt = math.degrees(math.acos(nz))
    az = math.degrees(rotang_0)
    az = (450.0 - az) % 360.0
    az += 90.0
    if az < 0.0:
        az += 360.0
    az = az % 360.0
    if abs(az - 360.0) < 1.0e-3:
        az = 0.0
    elif abs(az - 180.0) < 1.0e-6:
        az = 180.0
    if abs(tilt - 180.0) < 1.0e-6:
        tilt = 180.0
    return az, tilt


def _polygon_centroid(
    verts: np.ndarray, gross_area: float
) -> tuple[float, float, float]:
    """SurfaceGeometry.cc::CalcSurfaceCentroid"""
    n_sides = len(verts)
    if n_sides == 3:
        cen = (verts[0] + verts[1] + verts[2]) / 3.0
        return float(cen[0]), float(cen[1]), float(cen[2])
    if n_sides == 4 and gross_area > 0.0:
        c1 = (verts[0] + verts[1] + verts[2]) / 3.0
        a1 = 0.5 * float(
            np.linalg.norm(np.cross(verts[1] - verts[0], verts[2] - verts[0]))
        )
        c2 = (verts[0] + verts[2] + verts[3]) / 3.0
        a2 = 0.5 * float(
            np.linalg.norm(np.cross(verts[2] - verts[0], verts[3] - verts[0]))
        )
        denom = a1 + a2
        cen = (c1 * a1 + c2 * a2) / denom if denom > 0.0 else verts.mean(axis=0)
        return float(cen[0]), float(cen[1]), float(cen[2])
    cen = verts.mean(axis=0)
    return float(cen[0]), float(cen[1]), float(cen[2])


def _parse_vertices(fields: list[str], start_idx: int) -> np.ndarray:
    """Parse flat x,y,z vertex coordinates from IDF fields.

    Args:
        fields: Full list of IDF object fields.
        start_idx: Zero-based index of Vertex 1 X-coordinate.

    Returns:
        NumPy array of shape ``(N, 3)`` in float64.
    """
    coords = [float(val) for val in fields[start_idx:] if val.strip()]
    if len(coords) < 9 or len(coords) % 3 != 0:
        raise ValueError(f"Invalid vertex coordinate count: {len(coords)}")
    return np.asarray(coords, dtype=np.float64).reshape(-1, 3)


def _extract_const_schedule(obj: ParsedIdfObject) -> float:
    """Extract constant numeric value from Schedule:Constant or Schedule:Compact.

    Args:
        obj: Parsed schedule object.

    Returns:
        Constant schedule value as float.
    """
    if obj.obj_type == "SCHEDULE:CONSTANT":
        return float(_field(obj, 2))
    if obj.obj_type == "SCHEDULE:COMPACT":
        return float(_field(obj, 5))
    raise ValueError(f"Unsupported constant schedule type: {obj.obj_type}")


def _compile_single_building(
    idf_text: str,
    cell_id: str,
    epw_id: str,
    schedule_search_dirs: list[Path],
    *,
    max_rung: str = "S1",
) -> dict[str, object]:
    """Parse and compile one S0/S1 expanded IDF into geometry and zone fields."""
    check = check_s1_subset(idf_text) if max_rung == "S1" else check_s0_subset(idf_text)
    if not check.passed:
        raise ValueError(f"{cell_id}: failed {max_rung} subset check: {check.reason}")

    objects = parse_expidf(idf_text)
    by_type: dict[str, list[ParsedIdfObject]] = {}
    for obj in objects:
        by_type.setdefault(obj.obj_type, []).append(obj)

    steps_per_hour = int(round(_float_field(by_type["TIMESTEP"][0], 0, 12.0)))

    bldg = by_type["BUILDING"][0]
    loads_conv_tol = _float_field(bldg, 3, 0.04)
    temp_conv_tol = _float_field(bldg, 4, 0.4)
    warmup_max_days = int(round(_float_field(bldg, 6, 25.0)))
    warmup_min_days = int(round(_float_field(bldg, 7, 1.0)))

    hb_algo = by_type["HEATBALANCEALGORITHM"][0]
    h_conv_min = _float_field(hb_algo, 2, 0.1)
    h_conv_max = _float_field(hb_algo, 3, 1.0e7)

    site_loc = by_type["SITE:LOCATION"][0]
    site_elevation = _float_field(site_loc, 4, 0.0)

    zone_obj = by_type["ZONE"][0]
    zone_name = _field(zone_obj, 0).upper()
    zone_volume = _float_field(zone_obj, 8, 0.0)
    zone_floor_area = _float_field(zone_obj, 9, 0.0)

    nomass_map: dict[str, ParsedIdfObject] = {
        _field(o, 0).casefold(): o for o in by_type.get("MATERIAL:NOMASS", [])
    }
    mat_map: dict[str, ParsedIdfObject] = {
        _field(o, 0).casefold(): o for o in by_type.get("MATERIAL", [])
    }
    glass_map: dict[str, ParsedIdfObject] = {
        _field(o, 0).casefold(): o
        for o in by_type.get("WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", [])
    }
    cons_map: dict[str, str] = {
        _field(o, 0).casefold(): _field(o, 1).casefold()
        for o in by_type.get("CONSTRUCTION", [])
    }
    osc_map: dict[str, ParsedIdfObject] = {
        _field(o, 0).casefold(): o
        for o in by_type.get("SURFACEPROPERTY:OTHERSIDECOEFFICIENTS", [])
    }

    const_scheds: dict[str, float] = {}
    for sch in by_type.get("SCHEDULE:CONSTANT", []):
        const_scheds[_field(sch, 0).casefold()] = _extract_const_schedule(sch)
    for sch in by_type.get("SCHEDULE:COMPACT", []):
        const_scheds[_field(sch, 0).casefold()] = _extract_const_schedule(sch)

    file_scheds: dict[str, ParsedIdfObject] = {
        _field(sch, 0).casefold(): sch for sch in by_type.get("SCHEDULE:FILE", [])
    }

    fens_by_host: dict[str, list[ParsedIdfObject]] = {}
    for fen in by_type.get("FENESTRATIONSURFACE:DETAILED", []):
        host_key = _field(fen, 3).casefold()
        fens_by_host.setdefault(host_key, []).append(fen)

    surf_records: list[SurfaceRecord] = []
    zone_cen_accum = np.zeros(3, dtype=np.float64)
    zone_gross_area_sum = 0.0

    for surf in by_type.get("BUILDINGSURFACE:DETAILED", []):
        sname = _field(surf, 0).upper()
        stype_str = _field(surf, 1).casefold()
        if stype_str == "floor":
            sclass = SURF_FLOOR
        elif stype_str in ("roof", "ceiling"):
            sclass = SURF_ROOF
        else:
            sclass = SURF_WALL

        cons_key = _field(surf, 2).casefold()
        mat_obj = nomass_map[cons_map[cons_key]]
        rough_idx = ROUGHNESS_MAP[_field(mat_obj, 1, "MediumRough").casefold()]
        r_val = _float_field(mat_obj, 2)
        u_val = 1.0 / r_val
        eps_val = _float_field(mat_obj, 3, 0.9)
        sol_abs_val = _float_field(mat_obj, 4, 0.7)
        sun_exp = _field(surf, 7, "SunExposed").casefold() == "sunexposed"
        wind_exp = _field(surf, 8, "WindExposed").casefold() == "windexposed"

        bc_str = _field(surf, 5).casefold()
        if bc_str == "outdoors":
            boundary = BOUND_OUTDOORS
            osc_c_const = 0.0
            osc_t_const = 0.0
            osc_c_out = 0.0
            osc_c_zone = 0.0
        else:
            boundary = BOUND_OSC
            osc_obj = osc_map[_field(surf, 6).casefold()]
            osc_t_const = _float_field(osc_obj, 2, 0.0)
            osc_c_const = _float_field(osc_obj, 3, 0.0)
            osc_c_out = _float_field(osc_obj, 4, 0.0)
            osc_c_zone = _float_field(osc_obj, 7, 0.0)

        verts = _parse_vertices(surf.fields, 11)
        gross_area, normal = _newell_area_and_normal(verts)
        az, tilt = _determine_azimuth_and_tilt(verts, normal)

        if sclass == SURF_FLOOR and float(normal[2]) > 1.0e-6:
            verts = verts[::-1].copy()
            gross_area, normal = _newell_area_and_normal(verts)
            az, tilt = _determine_azimuth_and_tilt(verts, normal)
        elif sclass == SURF_ROOF and float(normal[2]) < -1.0e-6:
            verts = verts[::-1].copy()
            gross_area, normal = _newell_area_and_normal(verts)
            az, tilt = _determine_azimuth_and_tilt(verts, normal)

        cos_tilt = math.cos(math.radians(tilt))
        sin_tilt = math.sin(math.radians(tilt))
        vf_ground_raw = _field(surf, 9, "")
        if not vf_ground_raw or vf_ground_raw.casefold() == "autocalculate":
            vf_ground = 0.5 * (1.0 - cos_tilt)
        else:
            vf_ground = float(vf_ground_raw)
        vf_sky = 0.5 * (1.0 + cos_tilt)
        vf_sky_ir = vf_sky
        vf_ground_ir = 0.5 * (1.0 - cos_tilt)
        air_sky_split = math.sqrt(max(0.0, 0.5 * (1.0 + cos_tilt)))

        cen_xyz = _polygon_centroid(verts, gross_area)
        width = float(np.linalg.norm(verts[2] - verts[1]))
        height = float(np.linalg.norm(verts[1] - verts[0]))

        zone_cen_accum += np.asarray(cen_xyz, dtype=np.float64) * gross_area
        zone_gross_area_sum += gross_area

        sub_records: list[SurfaceRecord] = []
        sub_area_sum = 0.0
        for fen in fens_by_host.get(sname.casefold(), []):
            fname = _field(fen, 0).upper()
            ftype_str = _field(fen, 1).casefold()
            fcons_key = _field(fen, 2).casefold()
            fmat_key = cons_map[fcons_key]
            fverts = _parse_vertices(fen.fields, 9)
            f_area, f_normal = _newell_area_and_normal(fverts)
            f_az, f_tilt = _determine_azimuth_and_tilt(fverts, f_normal)
            f_cos = math.cos(math.radians(f_tilt))
            f_sin = math.sin(math.radians(f_tilt))
            f_vf_g_raw = _field(fen, 5, "")
            if not f_vf_g_raw or f_vf_g_raw.casefold() == "autocalculate":
                f_vf_g = 0.5 * (1.0 - f_cos)
            else:
                f_vf_g = float(f_vf_g_raw)
            f_vf_sky = 0.5 * (1.0 + f_cos)
            f_vf_g_ir = 0.5 * (1.0 - f_cos)
            f_split = math.sqrt(max(0.0, 0.5 * (1.0 + f_cos)))
            f_cen = _polygon_centroid(fverts, f_area)
            f_width = float(np.linalg.norm(fverts[2] - fverts[1]))
            f_height = float(np.linalg.norm(fverts[1] - fverts[0]))

            if ftype_str == "window":
                glass_obj = glass_map[fmat_key]
                f_u = _float_field(glass_obj, 1)
                f_shgc = _float_field(glass_obj, 2)
                f_eps = 0.84
                f_sol_abs = 0.0
                f_rough = ROUGHNESS_MAP["verysmooth"]
                f_class = SURF_WINDOW
                f_bound = BOUND_WINDOW
            else:
                dmat_obj = nomass_map[fmat_key]
                f_u = 1.0 / _float_field(dmat_obj, 2)
                f_shgc = 0.0
                f_eps = _float_field(dmat_obj, 3, 0.9)
                f_sol_abs = _float_field(dmat_obj, 4, 0.7)
                f_rough = ROUGHNESS_MAP[_field(dmat_obj, 1, "MediumRough").casefold()]
                f_class = SURF_DOOR
                f_bound = BOUND_DOOR

            sub_area_sum += f_area
            sub_records.append(
                SurfaceRecord(
                    name=fname,
                    surf_class=f_class,
                    boundary=f_bound,
                    area=f_area,
                    gross_area=f_area,
                    tilt_deg=f_tilt,
                    cos_tilt=f_cos,
                    sin_tilt=f_sin,
                    azimuth_deg=f_az,
                    centroid_xyz=f_cen,
                    u_value=f_u,
                    shgc=f_shgc,
                    osc_c_const=0.0,
                    osc_t_const=0.0,
                    osc_c_out=0.0,
                    osc_c_zone=0.0,
                    vf_ground=f_vf_g,
                    vf_sky=f_vf_sky,
                    vf_sky_ir=f_vf_sky,
                    vf_ground_ir=f_vf_g_ir,
                    air_sky_rad_split=f_split,
                    eps_in=f_eps,
                    eps_out=f_eps,
                    roughness=f_rough,
                    height=f_height,
                    width=f_width,
                    sun_exposed=sun_exp,
                    wind_exposed=wind_exp,
                    solar_abs_out=f_sol_abs,
                    solar_abs_in=f_sol_abs,
                )
            )

        net_area = gross_area - sub_area_sum
        surf_records.append(
            SurfaceRecord(
                name=sname,
                surf_class=sclass,
                boundary=boundary,
                area=net_area,
                gross_area=gross_area,
                tilt_deg=tilt,
                cos_tilt=cos_tilt,
                sin_tilt=sin_tilt,
                azimuth_deg=az,
                centroid_xyz=cen_xyz,
                u_value=u_val,
                shgc=0.0,
                osc_c_const=osc_c_const,
                osc_t_const=osc_t_const,
                osc_c_out=osc_c_out,
                osc_c_zone=osc_c_zone,
                vf_ground=vf_ground,
                vf_sky=vf_sky,
                vf_sky_ir=vf_sky_ir,
                vf_ground_ir=vf_ground_ir,
                air_sky_rad_split=air_sky_split,
                eps_in=eps_val,
                eps_out=eps_val,
                roughness=rough_idx,
                height=height,
                width=width,
                sun_exposed=sun_exp,
                wind_exposed=wind_exp,
                solar_abs_out=sol_abs_val,
                solar_abs_in=sol_abs_val,
            )
        )
        surf_records.extend(sub_records)

    zone_cen_xyz = (
        zone_cen_accum / zone_gross_area_sum
        if zone_gross_area_sum > 0.0
        else np.zeros(3, dtype=np.float64)
    )

    for im in by_type.get("INTERNALMASS", []):
        im_name = _field(im, 0).upper()
        cons_key = _field(im, 1).casefold()
        mat_obj = mat_map[cons_map[cons_key]]
        thickness = _float_field(mat_obj, 2)
        cond = _float_field(mat_obj, 3)
        eps_val = _float_field(mat_obj, 6, 0.9)
        im_sol_abs = _float_field(mat_obj, 7, 0.7)
        rough_idx = ROUGHNESS_MAP[_field(mat_obj, 1, "MediumRough").casefold()]
        im_area = _float_field(im, 4)
        surf_records.append(
            SurfaceRecord(
                name=im_name,
                surf_class=SURF_INTMASS,
                boundary=BOUND_INTMASS,
                area=im_area,
                gross_area=im_area,
                tilt_deg=90.0,
                cos_tilt=0.0,
                sin_tilt=1.0,
                azimuth_deg=0.0,
                centroid_xyz=(0.0, 0.0, 0.0),
                u_value=cond / thickness,
                shgc=0.0,
                osc_c_const=0.0,
                osc_t_const=0.0,
                osc_c_out=0.0,
                osc_c_zone=0.0,
                vf_ground=0.0,
                vf_sky=0.5,
                vf_sky_ir=0.5,
                vf_ground_ir=0.0,
                air_sky_rad_split=math.sqrt(0.5),
                eps_in=eps_val,
                eps_out=eps_val,
                roughness=rough_idx,
                height=1.0,
                width=im_area,
                sun_exposed=False,
                wind_exposed=False,
                solar_abs_out=im_sol_abs,
                solar_abs_in=im_sol_abs,
            )
        )

    vent_obj = by_type["ZONEVENTILATION:DESIGNFLOWRATE"][0]
    vent_sched = const_scheds[_field(vent_obj, 2).casefold()]
    vent_method = _field(vent_obj, 3).casefold()
    if vent_method == "airchanges/hour":
        vent_ach = _float_field(vent_obj, 7) * vent_sched
        vent_flow_m3s = vent_ach * zone_volume / 3600.0
    elif vent_method == "flow/zone":
        vent_flow_m3s = _float_field(vent_obj, 4) * vent_sched
        vent_ach = vent_flow_m3s * 3600.0 / zone_volume
    elif vent_method == "flow/area":
        vent_flow_m3s = _float_field(vent_obj, 5) * zone_floor_area * vent_sched
        vent_ach = vent_flow_m3s * 3600.0 / zone_volume
    else:
        raise ValueError(f"{cell_id}: unsupported ventilation method '{vent_method}'")

    tstat = by_type["THERMOSTATSETPOINT:DUALSETPOINT"][0]
    heat_sp = const_scheds[_field(tstat, 1).casefold()]
    cool_sp = const_scheds[_field(tstat, 2).casefold()]

    ideal = by_type["ZONEHVAC:IDEALLOADSAIRSYSTEM"][0]
    max_heat_supply_temp = _float_field(ideal, 5, 50.0)
    max_heat_supply_humrat = _float_field(ideal, 7, 0.0156)

    gain_hourly_w = np.zeros(8760, dtype=np.float64)
    for eq in by_type.get("OTHEREQUIPMENT", []):
        sch_key = _field(eq, 3).casefold()
        method = _field(eq, 4).casefold()
        if method == "watts/area":
            design_w = _float_field(eq, 6) * zone_floor_area
        elif method == "equipmentlevel":
            design_w = _float_field(eq, 5)
        else:
            raise ValueError(f"{cell_id}: unsupported OtherEquipment method '{method}'")

        if sch_key in const_scheds:
            gain_hourly_w += design_w * const_scheds[sch_key]
        elif sch_key in file_scheds:
            fsch = file_scheds[sch_key]
            raw_path = _field(fsch, 2)
            col_num = int(round(_float_field(fsch, 3, 1.0)))
            skip_rows = int(round(_float_field(fsch, 4, 0.0)))
            num_hrs = int(round(_float_field(fsch, 5, 8760.0)))
            csv_path = resolve_schedule_path(raw_path, schedule_search_dirs)
            sched_vals = load_schedule_file_hourly(
                csv_path,
                column_number=col_num,
                rows_to_skip=skip_rows,
                num_hours=num_hrs,
            )
            gain_hourly_w += design_w * sched_vals
        else:
            raise ValueError(f"{cell_id}: unknown schedule '{_field(eq, 3)}'")

    return {
        "cell_id": cell_id,
        "epw_id": epw_id,
        "steps_per_hour": steps_per_hour,
        "surfaces": surf_records,
        "zone_volume": zone_volume,
        "zone_floor_area": zone_floor_area,
        "zone_centroid_xyz": zone_cen_xyz,
        "zone_vent_ach": vent_ach,
        "zone_vent_flow_m3s": vent_flow_m3s,
        "zone_heat_setpoint": heat_sp,
        "zone_cool_setpoint": cool_sp,
        "zone_max_heat_supply_temp": max_heat_supply_temp,
        "zone_max_heat_supply_humrat": max_heat_supply_humrat,
        "zone_gain_hourly_w": gain_hourly_w,
        "h_conv_min": h_conv_min,
        "h_conv_max": h_conv_max,
        "warmup_min_days": warmup_min_days,
        "warmup_max_days": warmup_max_days,
        "loads_conv_tol": loads_conv_tol,
        "temp_conv_tol": temp_conv_tol,
        "site_elevation": site_elevation,
    }


def compile_expidf_batch(
    expidf_paths: list[Path],
    cell_ids: list[str] | None = None,
    epw_ids: list[str] | None = None,
    schedule_dirs: list[Path] | None = None,
    *,
    max_rung: str = "S1",
) -> BatchSpec:
    """Compile a batch of expanded S0/S1 IDFs into a padded ``BatchSpec``."""
    if not expidf_paths:
        raise ValueError("expidf_paths must not be empty")

    n_bldg = len(expidf_paths)
    ids = cell_ids if cell_ids is not None else [p.parent.name for p in expidf_paths]
    epws = epw_ids if epw_ids is not None else ["" for _ in expidf_paths]
    extra_dirs = list(schedule_dirs) if schedule_dirs is not None else []

    compiled: list[dict[str, object]] = []
    for path, cid, epw_id in zip(expidf_paths, ids, epws, strict=True):
        search_dirs = [path.parent, *extra_dirs]
        text = path.read_text(encoding="utf-8", errors="replace")
        compiled.append(
            _compile_single_building(text, cid, epw_id, search_dirs, max_rung=max_rung)
        )

    steps_per_hour = int(compiled[0]["steps_per_hour"])
    for item in compiled[1:]:
        if int(item["steps_per_hour"]) != steps_per_hour:
            raise ValueError("All buildings in a batch must share Timestep")

    max_s = max(len(item["surfaces"]) for item in compiled)

    surf_names: list[list[str]] = [[""] * max_s for _ in range(n_bldg)]
    surf_mask = np.zeros((n_bldg, max_s), dtype=bool)
    surf_class = np.zeros((n_bldg, max_s), dtype=np.int32)
    surf_boundary = np.zeros((n_bldg, max_s), dtype=np.int32)
    surf_area = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_gross_area = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_tilt_deg = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_cos_tilt = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_sin_tilt = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_azimuth_deg = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_centroid_z = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_centroid_xyz = np.zeros((n_bldg, max_s, 3), dtype=np.float64)
    surf_u_value = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_shgc = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_osc_c_const = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_osc_t_const = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_osc_c_out = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_osc_c_zone = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_vf_ground = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_vf_sky = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_vf_sky_ir = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_vf_ground_ir = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_air_sky_rad_split = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_eps_in = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_eps_out = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_roughness = np.zeros((n_bldg, max_s), dtype=np.int32)
    surf_height = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_width = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_sun_exposed = np.zeros((n_bldg, max_s), dtype=bool)
    surf_wind_exposed = np.zeros((n_bldg, max_s), dtype=bool)
    surf_solar_abs_out = np.zeros((n_bldg, max_s), dtype=np.float64)
    surf_solar_abs_in = np.zeros((n_bldg, max_s), dtype=np.float64)

    zone_volume = np.zeros(n_bldg, dtype=np.float64)
    zone_floor_area = np.zeros(n_bldg, dtype=np.float64)
    zone_centroid_z = np.zeros(n_bldg, dtype=np.float64)
    zone_centroid_xyz = np.zeros((n_bldg, 3), dtype=np.float64)
    zone_vent_ach = np.zeros(n_bldg, dtype=np.float64)
    zone_vent_flow_m3s = np.zeros(n_bldg, dtype=np.float64)
    zone_heat_setpoint = np.zeros(n_bldg, dtype=np.float64)
    zone_cool_setpoint = np.zeros(n_bldg, dtype=np.float64)
    zone_max_heat_supply_temp = np.zeros(n_bldg, dtype=np.float64)
    zone_max_heat_supply_humrat = np.zeros(n_bldg, dtype=np.float64)
    zone_gain_hourly_w = np.zeros((n_bldg, 8760), dtype=np.float64)
    h_conv_min = np.zeros(n_bldg, dtype=np.float64)
    h_conv_max = np.zeros(n_bldg, dtype=np.float64)
    warmup_min_days = np.zeros(n_bldg, dtype=np.int32)
    warmup_max_days = np.zeros(n_bldg, dtype=np.int32)
    loads_conv_tol = np.zeros(n_bldg, dtype=np.float64)
    temp_conv_tol = np.zeros(n_bldg, dtype=np.float64)
    site_elevation = np.zeros(n_bldg, dtype=np.float64)

    for b_idx, item in enumerate(compiled):
        surfaces = item["surfaces"]
        assert isinstance(surfaces, list)
        for s_idx, rec in enumerate(surfaces):
            assert isinstance(rec, SurfaceRecord)
            surf_names[b_idx][s_idx] = rec.name
            surf_mask[b_idx, s_idx] = True
            surf_class[b_idx, s_idx] = rec.surf_class
            surf_boundary[b_idx, s_idx] = rec.boundary
            surf_area[b_idx, s_idx] = rec.area
            surf_gross_area[b_idx, s_idx] = rec.gross_area
            surf_tilt_deg[b_idx, s_idx] = rec.tilt_deg
            surf_cos_tilt[b_idx, s_idx] = rec.cos_tilt
            surf_sin_tilt[b_idx, s_idx] = rec.sin_tilt
            surf_azimuth_deg[b_idx, s_idx] = rec.azimuth_deg
            surf_centroid_z[b_idx, s_idx] = rec.centroid_xyz[2]
            surf_centroid_xyz[b_idx, s_idx] = rec.centroid_xyz
            surf_u_value[b_idx, s_idx] = rec.u_value
            surf_shgc[b_idx, s_idx] = rec.shgc
            surf_osc_c_const[b_idx, s_idx] = rec.osc_c_const
            surf_osc_t_const[b_idx, s_idx] = rec.osc_t_const
            surf_osc_c_out[b_idx, s_idx] = rec.osc_c_out
            surf_osc_c_zone[b_idx, s_idx] = rec.osc_c_zone
            surf_vf_ground[b_idx, s_idx] = rec.vf_ground
            surf_vf_sky[b_idx, s_idx] = rec.vf_sky
            surf_vf_sky_ir[b_idx, s_idx] = rec.vf_sky_ir
            surf_vf_ground_ir[b_idx, s_idx] = rec.vf_ground_ir
            surf_air_sky_rad_split[b_idx, s_idx] = rec.air_sky_rad_split
            surf_eps_in[b_idx, s_idx] = rec.eps_in
            surf_eps_out[b_idx, s_idx] = rec.eps_out
            surf_roughness[b_idx, s_idx] = rec.roughness
            surf_height[b_idx, s_idx] = rec.height
            surf_width[b_idx, s_idx] = rec.width
            surf_sun_exposed[b_idx, s_idx] = rec.sun_exposed
            surf_wind_exposed[b_idx, s_idx] = rec.wind_exposed
            surf_solar_abs_out[b_idx, s_idx] = rec.solar_abs_out
            surf_solar_abs_in[b_idx, s_idx] = rec.solar_abs_in

        zone_volume[b_idx] = float(item["zone_volume"])
        zone_floor_area[b_idx] = float(item["zone_floor_area"])
        zcen = item["zone_centroid_xyz"]
        assert isinstance(zcen, np.ndarray)
        zone_centroid_xyz[b_idx] = zcen
        zone_centroid_z[b_idx] = float(zcen[2])
        zone_vent_ach[b_idx] = float(item["zone_vent_ach"])
        zone_vent_flow_m3s[b_idx] = float(item["zone_vent_flow_m3s"])
        zone_heat_setpoint[b_idx] = float(item["zone_heat_setpoint"])
        zone_cool_setpoint[b_idx] = float(item["zone_cool_setpoint"])
        zone_max_heat_supply_temp[b_idx] = float(item["zone_max_heat_supply_temp"])
        zone_max_heat_supply_humrat[b_idx] = float(item["zone_max_heat_supply_humrat"])
        gain_arr = item["zone_gain_hourly_w"]
        assert isinstance(gain_arr, np.ndarray)
        zone_gain_hourly_w[b_idx] = gain_arr
        h_conv_min[b_idx] = float(item["h_conv_min"])
        h_conv_max[b_idx] = float(item["h_conv_max"])
        warmup_min_days[b_idx] = int(item["warmup_min_days"])
        warmup_max_days[b_idx] = int(item["warmup_max_days"])
        loads_conv_tol[b_idx] = float(item["loads_conv_tol"])
        temp_conv_tol[b_idx] = float(item["temp_conv_tol"])
        site_elevation[b_idx] = float(item["site_elevation"])

    return BatchSpec(
        batch_size=n_bldg,
        max_surfaces=max_s,
        steps_per_hour=steps_per_hour,
        cell_ids=list(ids),
        site_epw_ids=list(epws),
        surf_names=surf_names,
        surf_mask=surf_mask,
        surf_class=surf_class,
        surf_boundary=surf_boundary,
        surf_area=surf_area,
        surf_gross_area=surf_gross_area,
        surf_tilt_deg=surf_tilt_deg,
        surf_cos_tilt=surf_cos_tilt,
        surf_sin_tilt=surf_sin_tilt,
        surf_azimuth_deg=surf_azimuth_deg,
        surf_centroid_z=surf_centroid_z,
        surf_centroid_xyz=surf_centroid_xyz,
        surf_u_value=surf_u_value,
        surf_shgc=surf_shgc,
        surf_osc_c_const=surf_osc_c_const,
        surf_osc_t_const=surf_osc_t_const,
        surf_osc_c_out=surf_osc_c_out,
        surf_osc_c_zone=surf_osc_c_zone,
        surf_vf_ground=surf_vf_ground,
        surf_vf_sky=surf_vf_sky,
        surf_vf_sky_ir=surf_vf_sky_ir,
        surf_vf_ground_ir=surf_vf_ground_ir,
        surf_air_sky_rad_split=surf_air_sky_rad_split,
        surf_eps_in=surf_eps_in,
        surf_eps_out=surf_eps_out,
        surf_roughness=surf_roughness,
        surf_height=surf_height,
        surf_width=surf_width,
        zone_volume=zone_volume,
        zone_floor_area=zone_floor_area,
        zone_centroid_z=zone_centroid_z,
        zone_centroid_xyz=zone_centroid_xyz,
        zone_vent_ach=zone_vent_ach,
        zone_vent_flow_m3s=zone_vent_flow_m3s,
        zone_heat_setpoint=zone_heat_setpoint,
        zone_cool_setpoint=zone_cool_setpoint,
        zone_max_heat_supply_temp=zone_max_heat_supply_temp,
        zone_max_heat_supply_humrat=zone_max_heat_supply_humrat,
        zone_gain_hourly_w=zone_gain_hourly_w,
        h_conv_min=h_conv_min,
        h_conv_max=h_conv_max,
        warmup_min_days=warmup_min_days,
        warmup_max_days=warmup_max_days,
        loads_conv_tol=loads_conv_tol,
        temp_conv_tol=temp_conv_tol,
        site_elevation=site_elevation,
        surf_sun_exposed=surf_sun_exposed,
        surf_wind_exposed=surf_wind_exposed,
        surf_solar_abs_out=surf_solar_abs_out,
        surf_solar_abs_in=surf_solar_abs_in,
    )
