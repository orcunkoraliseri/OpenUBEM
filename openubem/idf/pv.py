"""Geometry-aware rooftop PV layer (TechTransfer block 4, Lane H, T6 first slices).

Strip-before-replace, classify-by-geometry, inject. Three public functions only:
`strip_existing_pv`, `classify_roof_surfaces`, `inject_pv`. Nothing here nets PV
generation into a demand or EUI figure, and nothing here is called from the build
path -- `inject_pv` is a library function gated by `config.PV_INJECTION_ENABLED`
that this block does not wire up (SR-H2 decision, plan section 7).

Numeric defaults and their public sources (progress log, plan section 8, H02):
MODULE_POWER_DENSITY_W_PER_M2, SYSTEM_LOSSES_FRACTION, GROUND_COVERAGE_RATIO and
INVERTER_EFFICIENCY come from NREL/TP-6A20-62641 (PVWatts Version 5 Manual,
Dobos 2014) via the EnergyPlus IDD's own Generator:PVWatts /
ElectricLoadCenter:Inverter:PVWatts field defaults, which implement that model
verbatim. MIN_QUALIFYING_ROOF_AREA_M2 is an OpenUBEM internal convention, not a
standard-derived default: neither NREL/TP-6A20-62641 nor ASHRAE 90.1 section
10.5.1 states a minimum roof area. Its only job is to drop trivially small
roof slivers that would otherwise each spawn a generator object. California
Title 24's Solar-Ready 80 sq ft (7.43 m2) is named here only as a public
precedent for the order of magnitude -- it is NOT the source of this number,
and any published roof-area or capacity figure must state this threshold
alongside it (H03 ruling, plan section 8).

Tilt is read once per surface via geomeppy's own `.tilt` property (never
re-derived from vertices) and reduced with `pitch = min(tilt, 180 - tilt)`,
because a flat roof whose vertices wind the other way reports `.tilt == 180`
(measured in H01; a raw `tilt > 5` test misclassifies it as pitched).

Groups B and C are classified and reported separately by `classify_roof_surfaces`,
but `inject_pv` treats them identically today (both land in `flat_surfaces`); the
split exists for reporting only, because racking and inter-row shading -- the
only things that would ever make a single-level and a multi-level flat roof
need different treatment -- are out of scope for this block (H03 ruling).
"""
from __future__ import annotations

from eppy.function_helpers import getcoords

MODULE_TYPE = "Premium"
MODULE_POWER_DENSITY_W_PER_M2 = 190.0
SYSTEM_LOSSES_FRACTION = 0.14
GROUND_COVERAGE_RATIO = 0.40
INVERTER_EFFICIENCY = 0.96
DC_TO_AC_SIZE_RATIO = 1.10
MIN_QUALIFYING_ROOF_AREA_M2 = 7.5
PITCH_THRESHOLD_DEG = 5.0
Z_LEVEL_TOLERANCE_M = 0.05

_STRIP_CLASSES = (
    "GENERATOR:PVWATTS",
    "ELECTRICLOADCENTER:GENERATORS",
    "ELECTRICLOADCENTER:INVERTER:PVWATTS",
    "ELECTRICLOADCENTER:DISTRIBUTION",
)

_NAME_PREFIX = "OpenUBEM_PV_"
_GENERATOR_LIST_NAME = f"{_NAME_PREFIX}Generators"
_INVERTER_NAME = f"{_NAME_PREFIX}Inverter"
_DISTRIBUTION_NAME = f"{_NAME_PREFIX}Distribution"
_PV_SCH_NAME = "PV_SCH"


def _pitch_deg(surface) -> float:
    tilt = float(surface.tilt)
    return min(tilt, 180.0 - tilt)


def _mean_z(surface) -> float:
    coords = getcoords(surface)
    return sum(z for _, _, z in coords) / len(coords)


def strip_existing_pv(idf) -> dict:
    counts = {}
    for object_class in _STRIP_CLASSES:
        objects = list(idf.idfobjects[object_class])
        counts[object_class] = len(objects)
        for obj in objects:
            idf.removeidfobject(obj)
    return counts


def classify_roof_surfaces(idf) -> dict:
    group_a = []
    flat = []
    skipped_boundary_condition = 0
    skipped_min_area = 0
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if str(surface.Surface_Type).strip().lower() != "roof":
            continue
        if str(surface.Outside_Boundary_Condition).strip().lower() != "outdoors":
            skipped_boundary_condition += 1
            continue
        if float(surface.area) < MIN_QUALIFYING_ROOF_AREA_M2:
            skipped_min_area += 1
            continue
        if _pitch_deg(surface) > PITCH_THRESHOLD_DEG:
            group_a.append(surface)
        else:
            flat.append(surface)

    z_levels = {
        round(_mean_z(surface) / Z_LEVEL_TOLERANCE_M) * Z_LEVEL_TOLERANCE_M
        for surface in flat
    }
    if len(z_levels) <= 1:
        group_b, group_c = flat, []
    else:
        group_b, group_c = [], flat

    return {
        "group_a": group_a,
        "group_b": group_b,
        "group_c": group_c,
        "skipped_boundary_condition": skipped_boundary_condition,
        "skipped_min_area": skipped_min_area,
    }


def _estimated_capacity_w(surface) -> float:
    return float(surface.area) * GROUND_COVERAGE_RATIO * MODULE_POWER_DENSITY_W_PER_M2


def _already_injected(idf) -> bool:
    return any(
        obj.Name == _DISTRIBUTION_NAME
        for obj in idf.idfobjects["ELECTRICLOADCENTER:DISTRIBUTION"]
    )


def inject_pv(idf, enabled: bool = False) -> dict:
    groups = classify_roof_surfaces(idf)
    flat_surfaces = groups["group_b"] + groups["group_c"]
    pitched_surfaces = groups["group_a"]
    ordered_surfaces = sorted(
        [(s, "Generator:PVWatts") for s in flat_surfaces]
        + [(s, "Generator:Photovoltaic") for s in pitched_surfaces],
        key=lambda pair: pair[0].Name,
    )

    used = ordered_surfaces

    total_dc_capacity_w = sum(_estimated_capacity_w(s) for s, _ in used)
    n_flat_used = sum(1 for _, kind in used if kind == "Generator:PVWatts")
    n_pitched_used = sum(1 for _, kind in used if kind == "Generator:Photovoltaic")

    summary = {
        "enabled": bool(enabled),
        "surfaces_used": [s.Name for s, _ in used],
        "n_generators": len(used),
        "n_flat_generators": n_flat_used,
        "n_pitched_generators": n_pitched_used,
        "group_a_count": len(pitched_surfaces),
        "group_b_count": len(groups["group_b"]),
        "group_c_count": len(groups["group_c"]),
        "total_dc_capacity_w": total_dc_capacity_w,
        "pv_sch_left_in_place": True,
        "skipped_boundary_condition": groups["skipped_boundary_condition"],
        "skipped_min_area": groups["skipped_min_area"],
        "already_injected": False,
        "defaults_applied": {
            "module_type": MODULE_TYPE,
            "module_power_density_w_per_m2": MODULE_POWER_DENSITY_W_PER_M2,
            "system_losses_fraction": SYSTEM_LOSSES_FRACTION,
            "ground_coverage_ratio": GROUND_COVERAGE_RATIO,
            "inverter_efficiency": INVERTER_EFFICIENCY,
            "dc_to_ac_size_ratio": DC_TO_AC_SIZE_RATIO,
            "min_qualifying_roof_area_m2": MIN_QUALIFYING_ROOF_AREA_M2,
            "pitch_threshold_deg": PITCH_THRESHOLD_DEG,
        },
    }

    if not enabled:
        return summary

    if _already_injected(idf):
        summary["already_injected"] = True
        return summary

    summary["stripped"] = strip_existing_pv(idf)

    if not used:
        return summary

    generator_fields = {}
    for index, (surface, kind) in enumerate(used, start=1):
        capacity_w = _estimated_capacity_w(surface)
        if kind == "Generator:PVWatts":
            generator_name = f"{_NAME_PREFIX}PVWatts_{surface.Name}"
            idf.newidfobject(
                "GENERATOR:PVWATTS",
                Name=generator_name,
                PVWatts_Version="5",
                DC_System_Capacity=capacity_w,
                Module_Type=MODULE_TYPE,
                Array_Type="FixedRoofMounted",
                System_Losses=SYSTEM_LOSSES_FRACTION,
                Array_Geometry_Type="Surface",
                Surface_Name=surface.Name,
                Ground_Coverage_Ratio=GROUND_COVERAGE_RATIO,
            )
        else:
            performance_name = f"{_NAME_PREFIX}Performance_{surface.Name}"
            idf.newidfobject(
                "PHOTOVOLTAICPERFORMANCE:SIMPLE",
                Name=performance_name,
                Fraction_of_Surface_Area_with_Active_Solar_Cells=GROUND_COVERAGE_RATIO,
                Conversion_Efficiency_Input_Mode="Fixed",
                Value_for_Cell_Efficiency_if_Fixed=MODULE_POWER_DENSITY_W_PER_M2 / 1000.0,
            )
            generator_name = f"{_NAME_PREFIX}Photovoltaic_{surface.Name}"
            idf.newidfobject(
                "GENERATOR:PHOTOVOLTAIC",
                Name=generator_name,
                Surface_Name=surface.Name,
                Photovoltaic_Performance_Object_Type="PhotovoltaicPerformance:Simple",
                Module_Performance_Name=performance_name,
                Heat_Transfer_Integration_Mode="Decoupled",
                Number_of_Series_Strings_in_Parallel=1,
                Number_of_Modules_in_Series=1,
            )
        generator_fields[f"Generator_{index}_Name"] = generator_name
        generator_fields[f"Generator_{index}_Object_Type"] = kind
        generator_fields[f"Generator_{index}_Rated_Electric_Power_Output"] = capacity_w

    idf.newidfobject(
        "ELECTRICLOADCENTER:GENERATORS",
        Name=_GENERATOR_LIST_NAME,
        **generator_fields,
    )
    idf.newidfobject(
        "ELECTRICLOADCENTER:INVERTER:PVWATTS",
        Name=_INVERTER_NAME,
        DC_to_AC_Size_Ratio=DC_TO_AC_SIZE_RATIO,
        Inverter_Efficiency=INVERTER_EFFICIENCY,
    )
    idf.newidfobject(
        "ELECTRICLOADCENTER:DISTRIBUTION",
        Name=_DISTRIBUTION_NAME,
        Generator_List_Name=_GENERATOR_LIST_NAME,
        Generator_Operation_Scheme_Type="Baseload",
        Electrical_Buss_Type="DirectCurrentWithInverter",
        Inverter_Name=_INVERTER_NAME,
    )

    return summary
