"""IDF builder orchestrator and per-building build() entry point (DESIGN §3D, §4)."""
import logging
import traceback
from importlib.resources import files
from pathlib import Path

import geopandas as gpd
import pandas as pd
from geomeppy import IDF as GeomIDF
from eppy.modeleditor import IDDAlreadySetError
from joblib import Parallel, delayed
from shapely.geometry.polygon import orient

from openubem import config
from openubem.config import SHADING_SPHERE_RADIUS
from openubem.geometry.footprint import (
    derive_num_floors,
    simplify_footprint,
    translate_to_origin,
    validate_simplified,
)
from openubem.geometry.zoning import build_zones, decide_zoning_strategy
from openubem.geometry.context import discover_context
from openubem.idf.surfaces import (
    extrude_geometry,
    find_mismatched_interzone_pairs,
    set_adiabatic_surfaces,
    _force_reroute_coreperim_to_one_zone_per_floor,
    _repair_roof_roof_pairs,
    _repair_mismatched_horizontal_pairs,
    _pair_interfloor_surfaces,
)
from openubem.idf.hvac import assign_hvac
from openubem.idf.dhw import assign_dhw
from openubem.idf.cooking import assign_cooking
from openubem.idf.refrigeration import assign_refrigeration
from openubem.idf.outputs import write_outputs
from openubem.semantic.schedules import write_schedules_to_idf
from openubem.semantic.loads import get_space_type_loads

logger = logging.getLogger("openubem.idf")

# Invariant I3: IDD locked once per process (DESIGN §3D line 182).
try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

TEMPLATE_ROUTING: dict[str, str] = {
    "MidriseApartment": "residential_base.idf",
    "HighriseApartment": "residential_base.idf",
    "TallBuilding": "highrise_base.idf",
    "SuperTallBuilding": "highrise_base.idf",
    "Laboratory": "specialized_base.idf",
    "SmallDataCenterHighITE": "specialized_base.idf",
    "LargeDataCenterHighITE": "specialized_base.idf",
    "SmallDataCenterLowITE": "specialized_base.idf",   # Phase-1 unreachable, routed per DESIGN §3D lines 195-196
    "LargeDataCenterLowITE": "specialized_base.idf",   # Phase-1 unreachable, routed per DESIGN §3D lines 195-196
    "Warehouse": "specialized_base.idf",
}


def _parse_epw_location(epw_path: Path) -> tuple[str, float, float, float, float]:
    """Read EPW line 1 and return (city, lat, lon, time_zone, elevation)."""
    with open(epw_path, encoding="utf-8", errors="replace") as f:
        line = f.readline()
    parts = line.strip().split(",")
    city = parts[1].strip()
    lat = float(parts[6])
    lon = float(parts[7])
    tz = float(parts[8])
    elev = float(parts[9])
    return (city, lat, lon, tz, elev)


def _populate_site_location_from_epw(idf: GeomIDF, epw_path: Path) -> None:
    city, lat, lon, tz, elev = _parse_epw_location(epw_path)
    loc = idf.idfobjects["SITE:LOCATION"][0]
    loc.Name = city
    loc.Latitude = lat
    loc.Longitude = lon
    loc.Time_Zone = tz
    loc.Elevation = elev


def _coerce_to_polygon(geom, dq_flag: str) -> tuple:
    """Coerce MultiPolygon to its largest-area part; pass Polygon through.

    Returns (geom_out, dq_flag_out).  Empty/None/other geometry types are
    returned as-is so the existing validate_simplified path handles them.
    """
    if geom is None:
        return geom, dq_flag
    gtype = getattr(geom, "geom_type", None)
    if gtype == "MultiPolygon":
        parts = list(geom.geoms)
        if not parts:
            return geom, dq_flag
        largest = max(parts, key=lambda g: g.area)
        tag = "multipolygon_coerced_to_largest_part"
        dq_flag = (dq_flag + "|" + tag).lstrip("|") if tag not in dq_flag else dq_flag
        logger.warning("MultiPolygon footprint coerced to largest part (area=%.2f m²)", largest.area)
        return largest, dq_flag
    return geom, dq_flag


def normalized_space_loads(
    zones: list[dict], lpd_arch: float, epd_arch: float,
    occ_m2_per_person: float, space_table: dict,
) -> dict[str, dict]:
    """Space-Type-Weighted Normalization (RESULT_L11): per-zone absolute loads that
    differentiate by space type (e.g. corridor EPD/occupancy = 0) yet still sum to the
    archetype-average building totals (lpd_arch·A, epd_arch·A, A/occ_m2).

    Returns {zone_name: {"lights", "equip", "people"}} in absolute W / count.
    """
    zs = [z for z in zones if z.get("space_type") and z.get("floor_area_m2")]
    a_tot = sum(z["floor_area_m2"] for z in zs)
    if a_tot <= 0:
        return {}

    def si(z):  # per-space intensities for this zone's space type
        return space_table.get(z["space_type"], {})

    denom_l = sum(z["floor_area_m2"] * si(z).get("lighting_w_m2", 0.0) for z in zs)
    denom_e = sum(z["floor_area_m2"] * si(z).get("equipment_w_m2", 0.0) for z in zs)
    occ_area = sum(z["floor_area_m2"] for z in zs if si(z).get("has_occupancy"))
    alpha_l = (lpd_arch * a_tot / denom_l) if denom_l > 0 else 0.0
    alpha_e = (epd_arch * a_tot / denom_e) if denom_e > 0 else 0.0
    total_people = (a_tot / occ_m2_per_person) if occ_m2_per_person else 0.0

    out: dict[str, dict] = {}
    for z in zs:
        area = z["floor_area_m2"]
        s = si(z)
        out[z["name"]] = {
            "lights": alpha_l * s.get("lighting_w_m2", 0.0) * area,
            "equip": alpha_e * s.get("equipment_w_m2", 0.0) * area,
            "people": (total_people * area / occ_area)
                      if (s.get("has_occupancy") and occ_area > 0) else 0.0,
        }
    return out


class BuildingIDF:
    def __init__(self, row: pd.Series, thermal_mass: bool = False, resolution_mode: str = "auto",
                 trim_outputs: bool = False) -> None:
        self.row = row
        self.thermal_mass = thermal_mass
        self.resolution_mode = resolution_mode
        self.trim_outputs = trim_outputs
        template_name = TEMPLATE_ROUTING.get(row["archetype_id"], "commercial_base.idf")
        template_path = str(
            files("openubem.idf").joinpath("templates").joinpath(template_name)
        )
        self.idf = GeomIDF(template_path)
        epw_path = row.get("epw_path")
        if epw_path and Path(str(epw_path)).exists():
            _populate_site_location_from_epw(self.idf, Path(str(epw_path)))

    def assign_constructions(self) -> None:
        """Create opaque assemblies and glazing per DESIGN §3F (fact #20)."""
        row = self.row
        idf = self.idf

        _K = 0.12  # W/m·K light structural — preserves R = Thickness/Conductivity

        for name, u_col in [
            ("Roof_Assembly", "u_roof_w_m2k"),
            ("Wall_Assembly", "u_wall_w_m2k"),
            ("Floor_Assembly", "u_floor_w_m2k"),
        ]:
            r_val = 1.0 / float(row[u_col])
            if self.thermal_mass:
                idf.newidfobject(
                    "MATERIAL",
                    Name=name,
                    Roughness="MediumRough",
                    Thickness=max(0.01, r_val * _K),
                    Conductivity=_K,
                    Density=800.0,
                    Specific_Heat=1000.0,
                    Thermal_Absorptance=0.9,
                    Solar_Absorptance=0.7,
                    Visible_Absorptance=0.7,
                )
            else:
                idf.newidfobject(
                    "MATERIAL:NOMASS",
                    Name=name,
                    Roughness="MediumRough",
                    Thermal_Resistance=r_val,
                    Thermal_Absorptance=0.9,
                    Solar_Absorptance=0.7,
                    Visible_Absorptance=0.7,
                )
            idf.newidfobject(
                "CONSTRUCTION",
                Name=name.replace("_Assembly", "_Construction"),
                Outside_Layer=name,
            )

        idf.newidfobject(
            "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM",
            Name="Window_Material",
            UFactor=float(row["u_window_w_m2k"]),
            Solar_Heat_Gain_Coefficient=float(row["shgc_window"]),
            Visible_Transmittance=0.6,
        )
        idf.newidfobject(
            "CONSTRUCTION",
            Name="Window_Construction",
            Outside_Layer="Window_Material",
        )
        idf.set_default_constructions()
        idf.set_wwr(wwr=float(row["wwr"]), construction="Window_Construction", force=True)

        _SURFACE_CONSTRUCTION_MAP = {
            "wall": "Wall_Construction",
            "roof": "Roof_Construction",
            "floor": "Floor_Construction",
            "ceiling": "Floor_Construction",
        }
        for surf in idf.getsurfaces():
            stype = surf.Surface_Type.lower()
            construction = _SURFACE_CONSTRUCTION_MAP.get(stype)
            if construction:
                surf.Construction_Name = construction

    def assign_infiltration(self, zones: list[dict]) -> None:
        """Per-zone infiltration objects per DESIGN §3F (fact #22)."""
        row = self.row
        idf = self.idf
        arch = row["archetype_id"]
        for z in zones:
            idf.newidfobject(
                "ZONEINFILTRATION:DESIGNFLOWRATE",
                Name=f"Infiltration_{z['name']}",
                Zone_or_ZoneList_or_Space_or_SpaceList_Name=z["name"],
                Schedule_Name=f"Infiltration_Schedule_{arch}",
                Design_Flow_Rate_Calculation_Method="Flow/ExteriorWallArea",
                Flow_Rate_per_Exterior_Surface_Area=float(row["infiltration_m3_s_m2"]),
                Constant_Term_Coefficient=1.0,
            )

    def copy_schedule_library(self, archetype_id: str, schedule_library: dict) -> None:
        """Write Module 07 schedule objects into IDF via write_schedules_to_idf (Step-2.2 §3F)."""
        write_schedules_to_idf(self.idf, archetype_id)

    def assign_loads(self, zones: list[dict]) -> None:
        """Per-zone PEOPLE/LIGHTS/ELECTRICEQUIPMENT/HVACTEMPLATE:THERMOSTAT per DESIGN §3G (fact #23)."""
        row = self.row
        idf = self.idf
        arch = row["archetype_id"]
        people_per_m2 = 1.0 / float(row["occupant_m2_per_person"])

        # Space-type differentiation for room_layout zones (corridor vs unit), alpha-
        # normalized so building totals still equal the archetype-average totals (T08).
        norm = None
        if any(z.get("space_type") for z in zones):
            space_table = get_space_type_loads(arch)
            if space_table:
                norm = normalized_space_loads(
                    zones, float(row["lighting_w_m2"]), float(row["equipment_w_m2"]),
                    float(row["occupant_m2_per_person"]), space_table,
                )

        for z in zones:
            zname = z["name"]
            floor_area_m2 = z.get("floor_area_m2")
            if norm is not None and zname in norm:
                nl = norm[zname]
                if nl["people"] > 0:
                    idf.newidfobject(
                        "PEOPLE",
                        Name=f"People_{zname}",
                        Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                        Number_of_People_Schedule_Name=f"Occupancy_Schedule_{arch}",
                        Number_of_People_Calculation_Method="People",
                        Number_of_People=nl["people"],
                        Activity_Level_Schedule_Name="Activity_Level",
                        Fraction_Radiant=0.3,
                    )
                idf.newidfobject(
                    "LIGHTS",
                    Name=f"Lights_{zname}",
                    Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                    Schedule_Name=f"Lighting_Schedule_{arch}",
                    Design_Level_Calculation_Method="LightingLevel",
                    Lighting_Level=nl["lights"],
                    Fraction_Radiant=0.42,
                )
                if nl["equip"] > 0:
                    idf.newidfobject(
                        "ELECTRICEQUIPMENT",
                        Name=f"Equipment_{zname}",
                        Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                        Schedule_Name=f"Equipment_Schedule_{arch}",
                        Design_Level_Calculation_Method="EquipmentLevel",
                        Design_Level=nl["equip"],
                        Fraction_Radiant=0.5,
                    )
            elif floor_area_m2 is not None:
                idf.newidfobject(
                    "PEOPLE",
                    Name=f"People_{zname}",
                    Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                    Number_of_People_Schedule_Name=f"Occupancy_Schedule_{arch}",
                    Number_of_People_Calculation_Method="People",
                    Number_of_People=people_per_m2 * floor_area_m2,
                    Activity_Level_Schedule_Name="Activity_Level",
                    Fraction_Radiant=0.3,
                )
                idf.newidfobject(
                    "LIGHTS",
                    Name=f"Lights_{zname}",
                    Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                    Schedule_Name=f"Lighting_Schedule_{arch}",
                    Design_Level_Calculation_Method="LightingLevel",
                    Lighting_Level=float(row["lighting_w_m2"]) * floor_area_m2,
                    Fraction_Radiant=0.42,
                )
                idf.newidfobject(
                    "ELECTRICEQUIPMENT",
                    Name=f"Equipment_{zname}",
                    Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                    Schedule_Name=f"Equipment_Schedule_{arch}",
                    Design_Level_Calculation_Method="EquipmentLevel",
                    Design_Level=float(row["equipment_w_m2"]) * floor_area_m2,
                    Fraction_Radiant=0.5,
                )
            else:
                idf.newidfobject(
                    "PEOPLE",
                    Name=f"People_{zname}",
                    Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                    Number_of_People_Schedule_Name=f"Occupancy_Schedule_{arch}",
                    Number_of_People_Calculation_Method="People/Area",
                    People_per_Floor_Area=people_per_m2,
                    Activity_Level_Schedule_Name="Activity_Level",
                    Fraction_Radiant=0.3,
                )
                idf.newidfobject(
                    "LIGHTS",
                    Name=f"Lights_{zname}",
                    Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                    Schedule_Name=f"Lighting_Schedule_{arch}",
                    Design_Level_Calculation_Method="Watts/Area",
                    Watts_per_Zone_Floor_Area=float(row["lighting_w_m2"]),
                    Fraction_Radiant=0.42,
                )
                idf.newidfobject(
                    "ELECTRICEQUIPMENT",
                    Name=f"Equipment_{zname}",
                    Zone_or_ZoneList_or_Space_or_SpaceList_Name=zname,
                    Schedule_Name=f"Equipment_Schedule_{arch}",
                    Design_Level_Calculation_Method="Watts/Area",
                    Watts_per_Zone_Floor_Area=float(row["equipment_w_m2"]),
                    Fraction_Radiant=0.5,
                )
            idf.newidfobject(
                "HVACTEMPLATE:THERMOSTAT",
                Name=f"{zname}_Thermostat",
                Heating_Setpoint_Schedule_Name=f"Heating_Setpoint_{arch}",
                Cooling_Setpoint_Schedule_Name=f"Cooling_Setpoint_{arch}",
            )

    def build(self, gdf: gpd.GeoDataFrame, schedule_library: dict, output_dir: Path) -> dict:
        """Per-building orchestrator (DESIGN §4). Returns one manifest row dict (fact #27)."""
        row = self.row
        osm_id = str(row["osm_id"])
        arch = str(row["archetype_id"])

        # 3A: footprint simplification
        geom = row["geometry"]
        dq_flag = row.get("data_quality_flag", "") or ""
        if pd.isna(dq_flag):
            dq_flag = ""
        dq_flag = str(dq_flag)

        # Coerce MultiPolygon to largest-area part before simplify (no MultiPolygon guard downstream).
        geom, dq_flag = _coerce_to_polygon(geom, dq_flag)

        poly, dq_flag, simp_status = simplify_footprint(geom, dq_flag)

        if validate_simplified(poly):
            logger.info("osm_id=%s generation_status=skipped_invalid_geometry", osm_id)
            return {
                "osm_id": osm_id, "idf_path": "", "archetype_id": arch,
                "zoning_strategy": "", "num_zones": 0, "num_context_buildings": 0,
                "simplification_status": "skip", "data_quality_flag": dq_flag,
                "generation_status": "skipped_invalid_geometry",
                "resolution_mode": self.resolution_mode,
            }

        poly_local, cx, cy = translate_to_origin(poly)
        num_floors = derive_num_floors(row)

        # 3C: context discovery (simplified poly in world CRS for spatial index)
        target_row_ctx = row.copy()
        target_row_ctx["_simplified_geom"] = poly
        context = discover_context(target_row_ctx, gdf, cx, cy, SHADING_SPHERE_RADIUS)

        # 3B: zoning — prefer contract column, fall back to simplified poly area (B5/W3.8)
        _col_area = row.get("footprint_area_m2")
        footprint_area = float(_col_area) if pd.notna(_col_area) else poly_local.area
        strategy = decide_zoning_strategy(arch, footprint_area, num_floors, self.resolution_mode)
        if self.resolution_mode != "auto":
            poly_local = orient(poly_local, sign=1.0)
        zones = build_zones(osm_id, poly_local, arch, num_floors, strategy)

        # 3D: schedule library must be copied before geometry objects reference schedules
        self.copy_schedule_library(arch, schedule_library)

        # 3E: extrude geometry + intersect_match + shading blocks (R2: one add_block per
        # unique footprint with num_stories=N; Z_Origin patch removed — geomeppy stacks at true z)
        extrude_geometry(self.idf, zones, context)

        # Reflect a room_layout→one_zone_per_floor degrade in the manifest, whichever path took
        # it — surfaces.py's intersect_match reroute (generation_status_note) or generate_layout's
        # 1% area-conservation net (room_layout_area_fallback). Otherwise a silently-degraded build
        # still reports zoning_strategy=room_layout, masking that room-level zoning was abandoned.
        if any(z.get("generation_status_note") == "room_layout_intersect_fallback"
               or z.get("room_layout_area_fallback") for z in zones):
            strategy = "one_zone_per_floor"

        # Generation-time gate: any surviving vertex-count mismatch → reroute to
        # one_zone_per_floor (comprehensive: must simulate, not drop).
        mismatched = find_mismatched_interzone_pairs(self.idf)
        if mismatched:
            logger.warning(
                "osm_id=%s interzone mismatch pairs=%s — rerouting to one_zone_per_floor",
                osm_id, mismatched,
            )
            did_reroute = _force_reroute_coreperim_to_one_zone_per_floor(
                self.idf, zones, "interzone_vertex_mismatch"
            )
            if did_reroute:
                self.idf.intersect_match()
                _repair_roof_roof_pairs(self.idf)
                _repair_mismatched_horizontal_pairs(self.idf)
                _pair_interfloor_surfaces(self.idf)
                strategy = "one_zone_per_floor"
                # Re-check: one_zone_per_floor has no interzone perim pairs → should be empty.
                mismatched2 = find_mismatched_interzone_pairs(self.idf)
                if mismatched2:
                    logger.error(
                        "osm_id=%s still mismatched after reroute pairs=%s — dropping",
                        osm_id, mismatched2,
                    )
                    return {
                        "osm_id": osm_id, "idf_path": "", "archetype_id": arch,
                        "zoning_strategy": strategy, "num_zones": 0,
                        "num_context_buildings": len(context),
                        "simplification_status": simp_status, "data_quality_flag": dq_flag,
                        "generation_status": "failed_interzone_vertex_mismatch",
                        "resolution_mode": self.resolution_mode,
                    }
            else:
                logger.error(
                    "osm_id=%s reroute had no coreperim zones to rebuild — dropping",
                    osm_id,
                )
                return {
                    "osm_id": osm_id, "idf_path": "", "archetype_id": arch,
                    "zoning_strategy": strategy, "num_zones": 0,
                    "num_context_buildings": len(context),
                    "simplification_status": simp_status, "data_quality_flag": dq_flag,
                    "generation_status": "failed_interzone_vertex_mismatch",
                    "resolution_mode": self.resolution_mode,
                }

        # 3E-10c: adiabatic party walls and ground-floor slab
        set_adiabatic_surfaces(self.idf, zones, strategy)

        # Only pass zones that were actually extruded into the IDF (B4: use extruded flag)
        extruded_zones = [z for z in zones if z.get("extruded")]

        # D4(a): no extrudable zones → degenerate geometry. Skip loads/HVAC/service emitters
        # (which require zones[0]) and drop the building gracefully rather than crashing.
        if not extruded_zones:
            logger.warning(
                "osm_id=%s no extruded zones — dropping as degenerate geometry", osm_id
            )
            return {
                "osm_id": osm_id, "idf_path": "", "archetype_id": arch,
                "zoning_strategy": strategy, "num_zones": 0,
                "num_context_buildings": len(context),
                "simplification_status": simp_status, "data_quality_flag": dq_flag,
                "generation_status": "failed_no_extruded_zones",
                "resolution_mode": self.resolution_mode,
            }

        # 3F: constructions (needs extruded surfaces for set_wwr)
        self.assign_constructions()
        self.assign_infiltration(extruded_zones)

        # 3G: loads
        self.assign_loads(extruded_zones)

        # 3H: HVAC
        assign_hvac(self.idf, row, extruded_zones)

        # 3H-svc: Phase-E physical service loads
        assign_dhw(self.idf, row, extruded_zones)
        assign_cooking(self.idf, row, extruded_zones)
        assign_refrigeration(self.idf, row, extruded_zones)

        # 3I: outputs
        write_outputs(self.idf, trim_hourly=self.trim_outputs)

        # Save IDF (sanitise osm_id for filesystem)
        safe_id = osm_id.replace("/", "_").replace(":", "_").replace(" ", "_")
        idf_path = output_dir / "idfs" / f"{safe_id}.idf"
        self.idf.save(str(idf_path))

        has_bbox_fallback = any(z.get("fallback_to_bbox") for z in zones)
        has_narrow = any(z.get("narrow_fallback") for z in zones)
        gen_status = "fallback_bbox" if (has_bbox_fallback or simp_status == "bbox") else "success"
        if has_narrow and "narrow_perimeter_fallback" not in dq_flag:
            dq_flag = (dq_flag + "|narrow_perimeter_fallback").lstrip("|")
        logger.info("osm_id=%s generation_status=%s", osm_id, gen_status)

        return {
            "osm_id": osm_id,
            "idf_path": str(idf_path),
            "archetype_id": arch,
            "zoning_strategy": strategy,
            "num_zones": len(extruded_zones),
            "num_context_buildings": len(context),
            "simplification_status": simp_status,
            "data_quality_flag": dq_flag,
            "generation_status": gen_status,
            "resolution_mode": self.resolution_mode,
        }


def _worker_exception_row(row_like: dict, osm_id: str, resolution_mode: str = "auto") -> dict:
    """Manifest row recorded when a build raises (shared by serial + loky paths)."""
    logger.error("osm_id=%s worker exception: %s", osm_id, traceback.format_exc()[-300:])
    return {
        "osm_id": osm_id, "idf_path": "", "archetype_id": str(row_like.get("archetype_id", "")),
        "zoning_strategy": "", "num_zones": 0, "num_context_buildings": 0,
        "simplification_status": "skip", "data_quality_flag": "",
        "generation_status": "failed_worker_exception",
        "resolution_mode": resolution_mode,
    }


def _build_one(row_dict: dict, gdf: gpd.GeoDataFrame, schedule_library: dict,
               output_dir: Path, resolution_mode: str = "auto",
               trim_outputs: bool = False) -> dict:
    """Module-level worker: build one IDF in a loky subprocess (C10 — picklable, never raises)."""
    try:
        # Each loky worker process needs its own IDD lock (process-local state).
        try:
            GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
        except IDDAlreadySetError:
            pass
        row = pd.Series(row_dict)
        return BuildingIDF(row, resolution_mode=resolution_mode,
                           trim_outputs=trim_outputs).build(gdf, schedule_library, output_dir)
    except Exception:
        return _worker_exception_row(row_dict, str(row_dict.get("osm_id", "unknown")), resolution_mode)


def run_step3(
    gdf: gpd.GeoDataFrame,
    schedule_library: dict,
    output_dir: Path,
    n_jobs: int = 1,
    resolution_mode: str = "auto",
    trim_outputs: bool = False,
) -> pd.DataFrame:
    """Iterate all buildings, call BuildingIDF.build(), write 03_idf_manifest.parquet (DESIGN §4).

    n_jobs=1 (default): unchanged serial path. n_jobs>1: loky process pool (C10).
    trim_outputs=True: skip hourly per-zone Output:Variable objects (T08 large-fleet use).
    """
    # Validate mode once before the fleet loop (raises ValueError or NotImplementedError fast).
    decide_zoning_strategy("_", 1.0, 2, resolution_mode)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "idfs").mkdir(exist_ok=True)

    if n_jobs == 1:
        manifest_rows = []
        for _, row in gdf.iterrows():
            try:
                manifest_row = BuildingIDF(row, resolution_mode=resolution_mode,
                                           trim_outputs=trim_outputs).build(gdf, schedule_library, output_dir)
            except Exception:
                manifest_row = _worker_exception_row(row.to_dict(), str(row.get("osm_id", "unknown")), resolution_mode)
            manifest_rows.append(manifest_row)
    else:
        row_dicts = [row.to_dict() for _, row in gdf.iterrows()]
        manifest_rows = Parallel(n_jobs=n_jobs, backend="loky")(
            delayed(_build_one)(rd, gdf, schedule_library, output_dir, resolution_mode, trim_outputs)
            for rd in row_dicts
        )

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_parquet(output_dir / "03_idf_manifest.parquet", engine="pyarrow", index=False)
    return manifest_df
