"""LayoutAssigner: Assigns standardized baseline EnergyPlus reference models and scales floor area.

Instead of generating complex dynamic floor plans from scratch (layoutGenerator), this module
assigns pre-validated baseline IDF reference models from `00.BaselineBuildings_NUs` and scales
their floor area to match target real building dimensions.
"""

import math
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import shapely

from openubem import config

logger = logging.getLogger("openubem.geometry.layout_assigner")

# Mapping from OpenUBEM canonical archetype IDs (openubem/semantic/__init__.py
# _ARCHETYPE_VOCAB) to baseline IDF filenames. Keyed ONLY on canonical vocab
# tokens (plan §3.3) — `Courthouse`/`OpenUBEMUnknown` intentionally absent,
# no baseline exists for them (T03 handles the graceful miss).
ARCHETYPE_IDF_MAP: Dict[str, str] = {
    # Residential
    "MidriseApartment": "ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf",
    "HighriseApartment": "ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf",

    # Commercial / Institutional
    "Hospital": "ASHRAE901_Hospital_STD2022_Buffalo.idf",
    "LargeHotel": "ASHRAE901_HotelLarge_STD2022_Buffalo.idf",
    "SmallHotel": "ASHRAE901_HotelSmall_STD2022_Buffalo.idf",
    "LargeOffice": "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf",
    "LargeOfficeDetailed": "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf",
    "MediumOffice": "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf",
    "MediumOfficeDetailed": "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf",
    "SmallOffice": "ASHRAE901_OfficeSmall_STD2022_Buffalo.idf",
    "SmallOfficeDetailed": "ASHRAE901_OfficeSmall_STD2022_Buffalo.idf",
    "Outpatient": "ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf",

    # Education & Assembly
    "PrimarySchool": "ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf",
    "SecondarySchool": "ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf",
    "College": "College_90.1-2019_6A_Buffalo_v221.idf",
    "Laboratory": "Laboratory_90.1-2019_6A_Buffalo_v221.idf",

    # Retail & Dining & Storage
    "RetailStandalone": "ASHRAE901_RetailStandalone_STD2022_Buffalo.idf",
    "RetailStripmall": "ASHRAE901_RetailStripmall_STD2022_Buffalo.idf",
    "SuperMarket": "Supermarket_V22.1.idf",
    "Warehouse": "ASHRAE901_Warehouse_STD2022_Buffalo.idf",
    "FullServiceRestaurant": "ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf",
    "QuickServiceRestaurant": "ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf",

    # Tall & Specialized
    "TallBuilding": "TallBuilding_90.1-2019_6A_Buffalo_v221.idf",
    "SuperTallBuilding": "SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf",
    "LargeDataCenterHighITE": "ASHRAE901_DataCenterLargeHighITE_STD2019.idf",
    "LargeDataCenterLowITE": "ASHRAE901_DataCenterLargeLowITE_STD2019.idf",
    "SmallDataCenterHighITE": "SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf",
    "SmallDataCenterLowITE": "SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf",
}

# Baseline gross floor area (m2), keyed identically to ARCHETYPE_IDF_MAP.
# *Detailed variants reuse their non-Detailed counterpart's value (same file).
# DataCenter values measured directly from the 4 baseline IDFs (sum of FLOOR-type
# BuildingSurface:Detailed areas, zone Multiplier==1 confirmed) since no prior
# per-variant figure existed (old dict had one generic "DataCenter":5000.0 for
# all 4) — reusing a single placeholder would reproduce the exact wrong-scale
# bug this task fixes (plan §3.3).
DEFAULT_BASELINE_AREAS: Dict[str, float] = {
    "MidriseApartment": 3135.0,
    "HighriseApartment": 7835.0,
    "Hospital": 22422.0,
    "LargeHotel": 11345.0,
    "SmallHotel": 4013.0,
    "LargeOffice": 46320.0,
    "LargeOfficeDetailed": 46320.0,
    "MediumOffice": 4982.0,
    "MediumOfficeDetailed": 4982.0,
    "SmallOffice": 511.0,
    "SmallOfficeDetailed": 511.0,
    "Outpatient": 3804.0,
    "PrimarySchool": 6871.0,
    "SecondarySchool": 19592.0,
    "RetailStandalone": 2294.0,
    "RetailStripmall": 2090.0,
    "SuperMarket": 4181.0,
    "Warehouse": 4835.0,
    "FullServiceRestaurant": 511.0,
    "QuickServiceRestaurant": 232.0,
    "College": 11000.0,
    "Laboratory": 8500.0,
    "TallBuilding": 25000.0,
    "SuperTallBuilding": 60000.0,
    "LargeDataCenterHighITE": 557.4,
    "LargeDataCenterLowITE": 557.4,
    "SmallDataCenterHighITE": 55.7,
    "SmallDataCenterLowITE": 55.7,
}


class BaselineIDFRegistry:
    """Registry for discovering and managing baseline IDF models."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or config.BASELINE_IDF_DIR
        self._cache: Dict[str, Path] = {}
        self._scan()

    def _scan(self):
        """Indexes available baseline IDF files in the baseline directory."""
        if not self.base_dir.exists():
            logger.warning(f"Baseline IDF directory does not exist: {self.base_dir}")
            return
        for file in self.base_dir.glob("*.idf"):
            self._cache[file.name] = file
        logger.info(f"Indexed {len(self._cache)} baseline IDF files from {self.base_dir}")

    def get_baseline_idf(self, archetype_id: str) -> Optional[Path]:
        """Finds the baseline IDF file matching an archetype ID, or None if unmapped/missing."""
        filename = ARCHETYPE_IDF_MAP.get(archetype_id)
        if filename and filename in self._cache:
            return self._cache[filename]
        return None

    def get_baseline_area(self, archetype_id: str) -> Optional[float]:
        """Returns baseline gross floor area (m2) for archetype, or None if unmapped."""
        return DEFAULT_BASELINE_AREAS.get(archetype_id)


# Lazy cached registry: no directory scan happens at module import time (plan §3.4/T01).
_registry: Optional[BaselineIDFRegistry] = None


def get_registry() -> BaselineIDFRegistry:
    """Returns the process-wide BaselineIDFRegistry, scanning config.BASELINE_IDF_DIR
    on first call only."""
    global _registry
    if _registry is None:
        _registry = BaselineIDFRegistry()
    return _registry


def calculate_scaling_factor(real_area_m2: float, baseline_area_m2: float) -> Dict[str, float]:
    """Calculates gross floor area scaling ratio and planar coordinate scale factor.
    
    Args:
        real_area_m2: Real building target floor area (footprint_area * num_floors)
        baseline_area_m2: Standardized prototype baseline floor area

    Returns:
        Dict containing area_scale_ratio, planar_scale_factor, target_area_m2, baseline_area_m2.
    """
    if baseline_area_m2 <= 0:
        area_scale_ratio = 1.0
    else:
        area_scale_ratio = real_area_m2 / baseline_area_m2
    
    planar_scale_factor = math.sqrt(area_scale_ratio) if area_scale_ratio > 0 else 1.0

    return {
        "area_scale_ratio": area_scale_ratio,
        "planar_scale_factor": planar_scale_factor,
        "target_area_m2": real_area_m2,
        "baseline_area_m2": baseline_area_m2,
    }


def assign_baseline_layout(
    osm_id: str,
    footprint_poly: shapely.Polygon,
    archetype_id: str,
    num_floors: int,
    floor_to_floor_m: float = 3.5,
) -> Dict[str, Any]:
    """Assigns standardized baseline model layout and calculates floor area scaling metadata.

    Args:
        osm_id: Real building OpenStreetMap identifier.
        footprint_poly: Real building 2D footprint polygon.
        archetype_id: Assigned archetype classification tag.
        num_floors: Number of floors of real building.
        floor_to_floor_m: Floor-to-floor height in meters.

    Returns:
        Dict representing layout assignment, zone metadata, and scaling factors.
    """
    real_area = footprint_poly.area * num_floors
    reg = get_registry()
    baseline_idf_path = reg.get_baseline_idf(archetype_id)
    baseline_area = reg.get_baseline_area(archetype_id)

    if baseline_idf_path is None or baseline_area is None:
        # No baseline exists for this archetype (e.g. Courthouse, OpenUBEMUnknown, or a
        # missing library file) — degrade gracefully, never crash (plan §3.3/T03).
        # `no_baseline=True` / `baseline_idf_filename=None` are the signal T07's builder
        # branch will consume to fall back to the standard template pipeline.
        logger.warning(
            f"No baseline available for archetype_id={archetype_id!r} (osm_id={osm_id}); "
            "returning no_baseline metadata for downstream fallback."
        )
        return {
            "name": f"{osm_id}_assigned_{archetype_id}",
            "mode": "layout_assign",
            "osm_id": osm_id,
            "archetype_id": archetype_id,
            "no_baseline": True,
            "baseline_idf_filename": None,
            "baseline_idf_path": None,
            "real_num_floors": num_floors,
            "target_floor_area_m2": real_area,
            "baseline_floor_area_m2": None,
            "area_scale_ratio": None,
            "planar_scale_factor": None,
            "height_m": num_floors * floor_to_floor_m,
        }

    scaling = calculate_scaling_factor(real_area, baseline_area)

    assigned_metadata = {
        "name": f"{osm_id}_assigned_{archetype_id}",
        "mode": "layout_assign",
        "osm_id": osm_id,
        "archetype_id": archetype_id,
        "no_baseline": False,
        "baseline_idf_filename": baseline_idf_path.name,
        "baseline_idf_path": str(baseline_idf_path),
        "real_num_floors": num_floors,
        "target_floor_area_m2": real_area,
        "baseline_floor_area_m2": baseline_area,
        "area_scale_ratio": scaling["area_scale_ratio"],
        "planar_scale_factor": scaling["planar_scale_factor"],
        "height_m": num_floors * floor_to_floor_m,
    }

    logger.info(
        f"Assigned layout for osm_id={osm_id} ({archetype_id}): "
        f"Target Area={real_area:.1f} m2, Baseline Area={baseline_area:.1f} m2, "
        f"Scale Factor={scaling['area_scale_ratio']:.3f} (Planar={scaling['planar_scale_factor']:.3f})"
    )

    return assigned_metadata


# ── T04 — scale_baseline_idf() ─────────────────────────────────────────────────

# Surface classes whose X/Y vertex coordinates scale by √S; Z is left unchanged.
_GEOMETRY_SURFACE_CLASSES = (
    "BUILDINGSURFACE:DETAILED",
    "FENESTRATIONSURFACE:DETAILED",
    "SHADING:ZONE:DETAILED",
    "SHADING:BUILDING:DETAILED",
)

# E-LA-12: Daylighting:ReferencePoint is a point object (not a surface -- no
# .coords/.setcoords()), so its X/Y fields need direct scaling by the same
# planar_scale_factor; Z is left unchanged, mirroring _GEOMETRY_SURFACE_CLASSES.
# Real IDD field names confirmed via eppy introspection (no leading underscore
# after X/Y, unlike the plan's guessed names): XCoordinate_of_Reference_Point /
# YCoordinate_of_Reference_Point / ZCoordinate_of_Reference_Point.
# Daylighting:Controls audited too -- it only carries Daylighting_Reference_Point_N_Name
# references (strings) and illuminance/fraction settings, no embedded X/Y/Z
# coordinate fields of its own, so no entry is needed for it here.
_GEOMETRY_POINT_SPECS = (
    ("DAYLIGHTING:REFERENCEPOINT", "XCoordinate_of_Reference_Point", "YCoordinate_of_Reference_Point"),
)

# (idf_class, calc_method_field, absolute_value_field, method_value_meaning_absolute).
# Only the branch matching `method_value_meaning_absolute` carries an absolute
# quantity; every other choice (Watts/Area, Flow/Area, People/Area, ...) is a
# density field and must stay byte-identical.
_ABSOLUTE_LOAD_SPECS = (
    ("LIGHTS", "Design_Level_Calculation_Method", "Lighting_Level", "LightingLevel"),
    ("ELECTRICEQUIPMENT", "Design_Level_Calculation_Method", "Design_Level", "EquipmentLevel"),
    ("GASEQUIPMENT", "Design_Level_Calculation_Method", "Design_Level", "EquipmentLevel"),
    ("PEOPLE", "Number_of_People_Calculation_Method", "Number_of_People", "People"),
    ("ZONEINFILTRATION:DESIGNFLOWRATE", "Design_Flow_Rate_Calculation_Method", "Design_Flow_Rate", "Flow/Zone"),
    ("DESIGNSPECIFICATION:OUTDOORAIR", "Outdoor_Air_Method", "Outdoor_Air_Flow_per_Zone", "Flow/Zone"),
)

# (idf_class, absolute_value_field) — no calc-method branch on these classes;
# the field is always an absolute quantity.
_UNCONDITIONAL_ABSOLUTE_SPECS = (
    ("WATERUSE:EQUIPMENT", "Peak_Flow_Rate"),
    ("EXTERIOR:LIGHTS", "Design_Level"),
    # T15/E-LA-06 — fixed-capacity auxiliary equipment, confirmed always-absolute
    # (never a per-area/per-person density field) via eppy inspection of the 6
    # T12 local-leg baselines. WaterHeater:Stratified investigated, absent in
    # all 6 — not added (see plan §9 E-LA-06 update).
    ("ELECTRICLOADCENTER:TRANSFORMER", "Rated_Capacity"),
    ("WATERHEATER:MIXED", "Tank_Volume"),
    ("WATERHEATER:MIXED", "Heater_Maximum_Capacity"),
    # E-LA-10 — Peak_Use_Flow_Rate was never on this list, so it stayed
    # byte-identical between baseline and scaled IDF (confirmed via direct
    # comparison on way_1014146287); fixed-capacity, always-absolute field.
    ("WATERHEATER:MIXED", "Peak_Use_Flow_Rate"),
    # T02 audit (E-LA-10 sibling fields) — literal non-blank in 64/72 and
    # 72/72 WaterHeater:Mixed objects respectively across the 20 mapped
    # baseline files that contain WaterHeater:Mixed objects; never gated on a
    # calc-method choice (unconditionally absolute, same class as
    # Heater_Maximum_Capacity). Heater_Minimum_Capacity
    # and Heater_Ignition_Minimum_Flow_Rate were also investigated: always 0.0
    # or blank, Heater_Control_Type is "Cycle" everywhere (Minimum_Capacity is
    # only used in "Modulate" mode per the E+ 23.1 IDD) -- not added.
    ("WATERHEATER:MIXED", "Off_Cycle_Parasitic_Fuel_Consumption_Rate"),
    ("WATERHEATER:MIXED", "On_Cycle_Parasitic_Fuel_Consumption_Rate"),
    ("WATERHEATER:MIXED", "Off_Cycle_Loss_Coefficient_to_Ambient_Temperature"),
    ("WATERHEATER:MIXED", "On_Cycle_Loss_Coefficient_to_Ambient_Temperature"),
    # Coil:Cooling:DX:MultiSpeed — confirmed literal (non-autosize) rated
    # capacity/flow-rate fields in SmallHotel/SecondarySchool/RetailStandalone/
    # FullServiceRestaurant (unlike the DX:SingleSpeed/DX:TwoSpeed coils used
    # elsewhere, which are autosized); Sensible_Heat_Ratio/COP/effectiveness/
    # waste-heat-fraction fields on the same object are ratios, left untouched.
    ("COIL:COOLING:DX:MULTISPEED", "Speed_1_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_1_Rated_Air_Flow_Rate"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_2_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_2_Rated_Air_Flow_Rate"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_3_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_3_Rated_Air_Flow_Rate"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_4_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_4_Rated_Air_Flow_Rate"),
    # E-LA-07 class 1 — LargeOffice's FluidCooler:TwoSpeed "Central Tower" has
    # Performance_Input_Method=NominalCapacity with literal (never-autosized)
    # High/Low_Speed_Nominal_Capacity, while Design_Water_Flow_Rate and
    # High_Fan_Speed_Air_Flow_Rate on the same object stay autosize (confirmed
    # via eppy on the raw baseline) -- same defect class as E-LA-06/E-LA-10,
    # just never scaled because no T15-tested archetype had this loop.
    ("FLUIDCOOLER:TWOSPEED", "High_Speed_Nominal_Capacity"),
    ("FLUIDCOOLER:TWOSPEED", "Low_Speed_Nominal_Capacity"),
)

# E-LA-11 -- LargeOffice's 4 DataCenter zones' WSHP coils autosize to INF/NaN
# at small S (anisotropic zone-shrink HVAC-autosize degeneracy on the shared
# plant loop -> CheckForRunawayPlantTemps Fatal; confirmed envelope-patch-
# independent, structural-fixes plan §4/debug plan T06-T07 eio evidence).
# Fix: resolve these 8 coils' rated fields to their OWN S=1 raw-baseline
# EnergyPlus-autosized values (real annual EnergyPlus 23.1 run, Buffalo
# TMYx weather -- the baseline's native design climate -- 2026-07-23,
# eplusout.eio component-sizing lines, all 4 zones sane/finite; see
# scratchpad/t19_t06_t07_work/raw_s1_largeoffice/), then scale by
# area_scale_ratio -- same "resolve-the-autosize-once, then S-scale the
# literal" pattern as E-LA-10/E-LA-07-class-1, not a novel mechanism.
#
# (idf_class, exact object Name, field, S=1 literal). Matched by exact
# **Name**, NOT a class-level (idf_class, field) tuple like
# _UNCONDITIONAL_ABSOLUTE_SPECS: a fresh eppy scan of all 25 unique mapped
# baseline files (2026-07-23) confirmed ASHRAE901_ApartmentHighRise also
# carries 24 Coil:Heating:WaterToAirHeatPump:EquationFit +
# 24 Coil:Cooling:WaterToAirHeatPump:EquationFit objects (its per-apartment
# AirLoop G/M/T *_{Heating,Cooling} Coil fleet) -- a class-level match would
# incorrectly overwrite HighriseApartment's own autosize with these
# LargeOffice-specific literals. These 8 Names
# ("AirLoop DataCenter {Basement,bot,mid,top} {Heating,Cooling} Coil") do not
# appear in any other baseline's coil-name set in the same scan, so an
# exact-Name match is sufficient scoping without threading an archetype_id
# parameter through scale_baseline_idf().
_NAMED_ABSOLUTE_SPECS = (
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Heating Coil", "Rated_Air_Flow_Rate", 21.76082),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Heating Coil", "Rated_Water_Flow_Rate", 1.10026e-2),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Heating Coil", "Gross_Rated_Heating_Capacity", 444975.22266),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Heating Coil", "Rated_Air_Flow_Rate", 0.48949),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Heating Coil", "Rated_Water_Flow_Rate", 2.44640e-4),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Heating Coil", "Gross_Rated_Heating_Capacity", 9893.94684),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Heating Coil", "Rated_Air_Flow_Rate", 4.69562),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Heating Coil", "Rated_Water_Flow_Rate", 2.34983e-3),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Heating Coil", "Gross_Rated_Heating_Capacity", 95033.94133),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Heating Coil", "Rated_Air_Flow_Rate", 0.47764),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Heating Coil", "Rated_Water_Flow_Rate", 2.38961e-4),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Heating Coil", "Gross_Rated_Heating_Capacity", 9664.26963),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Rated_Air_Flow_Rate", 21.76082),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Rated_Water_Flow_Rate", 1.10026e-2),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 469899.78316),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 317819.49474),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Rated_Air_Flow_Rate", 0.48949),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Rated_Water_Flow_Rate", 2.44640e-4),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 10448.14012),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 7110.88362),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Rated_Air_Flow_Rate", 4.69562),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Rated_Water_Flow_Rate", 2.34983e-3),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 100357.11237),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 68255.93198),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Rated_Air_Flow_Rate", 0.47764),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Rated_Water_Flow_Rate", 2.38961e-4),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 10205.59792),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 6942.03771),
)


def _is_blank_or_autosize(value: Any) -> bool:
    """True for '' (unset IDF field) or 'autosize'/'autocalculate' (never multiply these)."""
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip().lower()
        return v in ("", "autosize", "autocalculate")
    return False


def scale_baseline_idf(idf: Any, scale_factor_dict: Dict[str, float]) -> Any:
    """Scales a baseline IDF's geometry (√S planar) and absolute loads (S) in place.

    X/Y vertex coordinates on BuildingSurface:Detailed / FenestrationSurface:Detailed /
    Shading:Zone:Detailed / Shading:Building:Detailed scale by `planar_scale_factor`
    (Z unchanged). Daylighting:ReferencePoint X/Y coordinates (E-LA-12) scale by the
    same `planar_scale_factor` (Z unchanged); Daylighting:Controls carries no embedded
    coordinate fields of its own, only reference-point name/fraction/illuminance
    settings, so nothing else needs scaling there. Absolute-quantity fields (Design/Lighting Level, Number of People,
    Design Flow Rate, Outdoor Air Flow per Zone, Peak Flow Rate, Exterior Lights Design
    Level) scale by `area_scale_ratio`, gated on each object's calculation-method field
    so per-area/per-person density fields (Watts/Area, Flow/Area, People/Area, ...) are
    left byte-identical. Blank ('') and autosize/autocalculate fields are never touched.
    Fixed-capacity auxiliary equipment (T15/E-LA-06: ElectricLoadCenter:Transformer
    Rated_Capacity, WaterHeater:Mixed Tank_Volume/Heater_Maximum_Capacity/
    Peak_Use_Flow_Rate (E-LA-10) plus the Off/On-Cycle Parasitic_Fuel_Consumption_Rate
    and Off/On-Cycle Loss_Coefficient_to_Ambient_Temperature fields (T02 audit), the
    literal — never-autosized in this baseline library — Coil:Cooling:DX:MultiSpeed
    per-speed rated capacity/flow-rate fields, and FluidCooler:TwoSpeed
    High/Low_Speed_Nominal_Capacity (E-LA-07 class 1)) also scales by
    `area_scale_ratio`. E-LA-11: LargeOffice's 4 DataCenter zones' 8
    Coil:{Heating,Cooling}:WaterToAirHeatPump:EquationFit coils (matched by
    exact object Name, not class, since ApartmentHighRise's own 48 WSHP coils
    share the same IDF class) have their rated air-flow/water-flow/capacity
    fields resolved from `autosize` to the coils' own S=1 raw-baseline
    EnergyPlus-autosized design values, then scaled by `area_scale_ratio` --
    autosize on these 8 objects degenerates to INF/NaN at small S. Other HVAC
    capacity fields are autosized in every baseline inspected and are never
    touched (not in the class lists above).

    Args:
        idf: A loaded geomeppy/eppy IDF object (mutated in place).
        scale_factor_dict: Output of calculate_scaling_factor() — must contain
            'planar_scale_factor' and 'area_scale_ratio'.

    Returns:
        The same idf object, for chaining.
    """
    planar_k = scale_factor_dict["planar_scale_factor"]
    area_s = scale_factor_dict["area_scale_ratio"]

    for cls in _GEOMETRY_SURFACE_CLASSES:
        for surf in idf.idfobjects.get(cls, []):
            scaled_coords = [(x * planar_k, y * planar_k, z) for x, y, z in surf.coords]
            surf.setcoords(scaled_coords)

    for cls, x_field, y_field in _GEOMETRY_POINT_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            x_val, y_val = getattr(obj, x_field), getattr(obj, y_field)
            if not _is_blank_or_autosize(x_val):
                setattr(obj, x_field, float(x_val) * planar_k)
            if not _is_blank_or_autosize(y_val):
                setattr(obj, y_field, float(y_val) * planar_k)

    for cls, method_field, value_field, absolute_method in _ABSOLUTE_LOAD_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(getattr(obj, method_field, "")).strip() != absolute_method:
                continue
            val = getattr(obj, value_field)
            if _is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)

    for cls, value_field in _UNCONDITIONAL_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            val = getattr(obj, value_field)
            if _is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)

    for cls, obj_name, value_field, s1_value in _NAMED_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(obj.Name).strip() != obj_name:
                continue
            val = getattr(obj, value_field)
            if not _is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, s1_value * area_s)

    return idf


# ── T05 — parse_baseline_zones() ────────────────────────────────────────────────

def _measured_zone_floor_area(idf: Any, zone_name: str) -> float:
    """Sums FLOOR-type BuildingSurface:Detailed areas referencing `zone_name`.

    Fallback for baseline IDFs that leave Zone.Floor_Area blank (common in this
    library — see plan §3.1 progress-log note).
    """
    total = 0.0
    for s in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        if s.Zone_Name == zone_name and str(s.Surface_Type).strip().upper() == "FLOOR":
            total += s.area
    return total


def parse_baseline_zones(idf: Any, archetype_id: str) -> List[Dict[str, Any]]:
    """Builds the extruded_zones-shaped list from a (post-scaling) baseline IDF.

    One dict per raw `Zone` object (plenums/attics/unconditioned included, matching
    plan §3.1's counting convention) — feeds builder.py's `extruded_zones` filter
    (checks `z.get("extruded")`) and the manifest's `num_zones` (T07, not built yet).

    Args:
        idf: A loaded (post scale_baseline_idf) geomeppy/eppy IDF object.
        archetype_id: Canonical archetype ID to stamp on every zone dict.

    Returns:
        [{"name", "archetype_id", "floor_area_m2", "extruded": True}, ...]
    """
    zones = []
    for z in idf.idfobjects.get("ZONE", []):
        floor_area = z.Floor_Area
        if _is_blank_or_autosize(floor_area):
            floor_area = _measured_zone_floor_area(idf, z.Name)
        else:
            floor_area = float(floor_area)
        zones.append({
            "name": z.Name,
            "archetype_id": archetype_id,
            "floor_area_m2": floor_area,
            "extruded": True,
        })
    return zones


# ── T06 — purge_baseline_outputs() / patch_location_and_weather() ─────────────

def purge_baseline_outputs(idf: Any) -> None:
    """Deletes every baseline `Output:*`/`OutputControl:*` object in place.

    Baseline prototype IDFs ship with their own output specification (variables,
    meters, summary/monthly tables, table style). Leaving those in place while also
    calling the project's `write_outputs()` (openubem/idf/outputs.py) would duplicate
    or conflict with the harvest schema the other resolution modes rely on (plan
    §3.4/§4) — so this purges the baseline's entire output spec first, making
    `write_outputs()` the sole source of Output:*/OutputControl:* objects afterwards.

    Args:
        idf: A loaded geomeppy/eppy IDF object (mutated in place).
    """
    output_classes = [cls for cls in idf.idfobjects if cls.startswith("OUTPUT")]
    for cls in output_classes:
        for obj in list(idf.idfobjects[cls]):
            idf.removeidfobject(obj)


def patch_location_and_weather(idf: Any, epw_path: Path) -> None:
    """Overwrites `Site:Location` from the target EPW and normalizes to exactly
    one annual (1 Jan - 31 Dec) `RunPeriod`.

    Reuses builder.py's existing `_populate_site_location_from_epw()`/
    `_parse_epw_location()` — imported lazily inside this function, not at module
    level, because zoning.py imports this module at its own import time and
    builder.py imports zoning.py; a module-level import here would be a
    builder -> zoning -> layout_assigner -> builder circular import.

    `Site:WeatherFile` is not a real EnergyPlus object (plan §3.4) and is not
    created here; `SizingPeriod:DesignDay` objects are left untouched (plan §7 Q2).

    Args:
        idf: A loaded geomeppy/eppy IDF object (mutated in place).
        epw_path: Path to the target building's EPW weather file.
    """
    from openubem.idf.builder import _populate_site_location_from_epw

    _populate_site_location_from_epw(idf, epw_path)

    runperiods = list(idf.idfobjects.get("RUNPERIOD", []))
    for extra in runperiods[1:]:
        idf.removeidfobject(extra)

    rp = runperiods[0] if runperiods else idf.newidfobject("RUNPERIOD", Name="Annual")
    rp.Begin_Month = 1
    rp.Begin_Day_of_Month = 1
    rp.End_Month = 12
    rp.End_Day_of_Month = 31
