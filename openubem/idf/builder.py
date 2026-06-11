"""IDF builder orchestrator and per-building build() entry point (DESIGN §3D, §4)."""
import logging
from importlib.resources import files
from pathlib import Path

import geopandas as gpd
import pandas as pd
from geomeppy import IDF as GeomIDF
from eppy.modeleditor import IDDAlreadySetError

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
from openubem.idf.surfaces import extrude_geometry, set_adiabatic_surfaces
from openubem.idf.hvac import assign_hvac
from openubem.idf.outputs import write_outputs
from openubem.semantic.schedules import write_schedules_to_idf

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


class BuildingIDF:
    def __init__(self, row: pd.Series) -> None:
        self.row = row
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

        for name, u_col in [
            ("Roof_Assembly", "u_roof_w_m2k"),
            ("Wall_Assembly", "u_wall_w_m2k"),
            ("Floor_Assembly", "u_floor_w_m2k"),
        ]:
            idf.newidfobject(
                "MATERIAL:NOMASS",
                Name=name,
                Roughness="MediumRough",
                Thermal_Resistance=1.0 / float(row[u_col]),
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

        for z in zones:
            zname = z["name"]
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

        poly, dq_flag, simp_status = simplify_footprint(geom, dq_flag)

        if validate_simplified(poly):
            logger.info("osm_id=%s generation_status=skipped_invalid_geometry", osm_id)
            return {
                "osm_id": osm_id, "idf_path": "", "archetype_id": arch,
                "zoning_strategy": "", "num_zones": 0, "num_context_buildings": 0,
                "simplification_status": "skip", "data_quality_flag": dq_flag,
                "generation_status": "skipped_invalid_geometry",
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
        strategy = decide_zoning_strategy(arch, footprint_area, num_floors)
        zones = build_zones(osm_id, poly_local, arch, num_floors, strategy)

        # 3D: schedule library must be copied before geometry objects reference schedules
        self.copy_schedule_library(arch, schedule_library)

        # 3E: extrude geometry + intersect_match + shading blocks (R2: one add_block per
        # unique footprint with num_stories=N; Z_Origin patch removed — geomeppy stacks at true z)
        extrude_geometry(self.idf, zones, context)

        # 3E-10c: adiabatic party walls and ground-floor slab
        set_adiabatic_surfaces(self.idf, zones, strategy)

        # Only pass zones that were actually extruded into the IDF (B4: use extruded flag)
        extruded_zones = [z for z in zones if z.get("extruded")]

        # 3F: constructions (needs extruded surfaces for set_wwr)
        self.assign_constructions()
        self.assign_infiltration(extruded_zones)

        # 3G: loads
        self.assign_loads(extruded_zones)

        # 3H: HVAC
        assign_hvac(self.idf, row, extruded_zones)

        # 3I: outputs
        write_outputs(self.idf)

        # Save IDF (sanitise osm_id for filesystem)
        safe_id = osm_id.replace("/", "_").replace(":", "_").replace(" ", "_")
        idf_path = output_dir / "idfs" / f"{safe_id}.idf"
        self.idf.save(str(idf_path))

        has_bbox_fallback = any(z.get("fallback_to_bbox") for z in zones)
        gen_status = "fallback_bbox" if (has_bbox_fallback or simp_status == "bbox") else "success"
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
        }


def run_step3(
    gdf: gpd.GeoDataFrame,
    schedule_library: dict,
    output_dir: Path,
) -> pd.DataFrame:
    """Iterate all buildings, call BuildingIDF.build(), write 03_idf_manifest.parquet (DESIGN §4)."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "idfs").mkdir(exist_ok=True)

    manifest_rows = []
    for _, row in gdf.iterrows():
        manifest_row = BuildingIDF(row).build(gdf, schedule_library, output_dir)
        manifest_rows.append(manifest_row)

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_parquet(output_dir / "03_idf_manifest.parquet", engine="pyarrow", index=False)
    return manifest_df
