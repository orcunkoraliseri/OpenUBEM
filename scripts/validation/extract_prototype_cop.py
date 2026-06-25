"""
T02 / T02b — Extract dominant DX coil COP + heating coil type/efficiency from prototype IDFs.
Central-plant archetypes use chiller/WSHP COP × 0.75 plant-auxiliary factor (§3.1 ruling).
Emits openubem/data/loads/hvac_cop_by_archetype.json.

Run from project root:
    python scripts/validation/extract_prototype_cop.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from openubem import config

PROTO_DIR = ROOT / "docs/validations/Level 2 DOE round-trip/00.BaselineBuildings_NUs"
OUT_PATH = ROOT / "openubem/data/loads/hvac_cop_by_archetype.json"
ARCHETYPES_PATH = ROOT / "openubem/data/openstudio_archetypes.json"

PLANT_FACTOR = 0.75  # §3.1: converts chiller/WSHP COP to effective plant COP

DX_COOLING_TYPES = {
    "COIL:COOLING:DX:SINGLESPEED": lambda c: (
        _safe_float(c, "Gross_Rated_Total_Cooling_Capacity"),
        _safe_float(c, "Gross_Rated_Cooling_COP"),
    ),
    "COIL:COOLING:DX:TWOSPEED": lambda c: (
        _safe_float(c, "High_Speed_Gross_Rated_Total_Cooling_Capacity"),
        _safe_float(c, "High_Speed_Gross_Rated_Cooling_COP"),
    ),
    "COIL:COOLING:DX:MULTISPEED": lambda c: (
        _safe_float(c, "Speed_1_Gross_Rated_Total_Cooling_Capacity"),
        _safe_float(c, "Speed_1_Gross_Rated_Cooling_COP"),
    ),
    "COIL:COOLING:DX:VARIABLESPEED": lambda c: (
        _safe_float(c, "Rated_Total_Cooling_Capacity_At_Selected_Nominal_Speed_Level"),
        _safe_float(c, "Rated_Cooling_COP_At_Selected_Nominal_Speed_Level"),
    ),
}
DX_TYPE_ALIASES = {
    "Coil:Cooling:DX:SingleSpeed": "COIL:COOLING:DX:SINGLESPEED",
    "Coil:Cooling:DX:TwoSpeed": "COIL:COOLING:DX:TWOSPEED",
    "Coil:Cooling:DX:MultiSpeed": "COIL:COOLING:DX:MULTISPEED",
    "COIL:COOLING:DX:TWOSPEED": "COIL:COOLING:DX:TWOSPEED",
}

# §3.1: archetypes that use central chiller → COP × PLANT_FACTOR
# TallBuilding/SuperTallBuilding map to LargeOffice IDF → same chiller logic
CENTRAL_PLANT_ARCHETYPES = {
    "LargeOffice", "LargeHotel", "Hospital", "College",
    "LargeDataCenterHighITE", "LargeDataCenterLowITE", "HighriseApartment",
    "TallBuilding", "SuperTallBuilding",
}

# §3.1: DataCenters have no heating
DATA_CENTER_ARCHETYPES = {"LargeDataCenterHighITE", "LargeDataCenterLowITE",
                          "SmallDataCenterHighITE", "SmallDataCenterLowITE"}


def _safe_float(obj, field):
    try:
        v = getattr(obj, field)
        if isinstance(v, str) and v.lower() in ("autosize", ""):
            return None
        return float(v)
    except Exception:
        return None


def _parse_idf(idf_path):
    from eppy.modeleditor import IDF
    IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    return IDF(str(idf_path))


def _dominant_dx_coil(idf):
    """Return (coil_type_str, cop, capacity, coil_name) for the dominant DX coil."""
    candidates = []
    for type_key, extractor in DX_COOLING_TYPES.items():
        coils = list(idf.idfobjects.get(type_key, []))
        for coil in coils:
            cap, cop = extractor(coil)
            name = getattr(coil, "Name", "")
            candidates.append((type_key, cop, cap, name))
        for alias, canonical in DX_TYPE_ALIASES.items():
            if canonical == type_key:
                alias_coils = list(idf.idfobjects.get(alias, []))
                for coil in alias_coils:
                    cap, cop = extractor(coil)
                    name = getattr(coil, "Name", "")
                    if not any(c[3] == name and c[0] == type_key for c in candidates):
                        candidates.append((type_key, cop, cap, name))

    if not candidates:
        return None

    with_cap = [(t, cop, cap, n) for t, cop, cap, n in candidates if cap is not None]
    if with_cap:
        best = max(with_cap, key=lambda x: x[2])
    else:
        best = candidates[0]

    return best


def _dominant_chiller(idf):
    """Return (cop, capacity, chiller_name, chiller_type) for the primary chiller.
    Primary = largest-capacity; if all autosized, take first by reference COP.
    §3.1: covers CHILLER:ELECTRIC:EIR and :REFORMULATEDEIR."""
    candidates = []
    for ctype in ("CHILLER:ELECTRIC:EIR", "CHILLER:ELECTRIC:REFORMULATEDEIR"):
        for c in idf.idfobjects.get(ctype, []):
            name = getattr(c, "Name", "")
            cop = _safe_float(c, "Reference_COP")
            cap = _safe_float(c, "Reference_Capacity")
            candidates.append((cop, cap, name, ctype))
    if not candidates:
        return None
    with_cap = [(cop, cap, n, t) for cop, cap, n, t in candidates if cap is not None]
    if with_cap:
        return max(with_cap, key=lambda x: x[1])
    # all autosized — take highest COP
    return max(candidates, key=lambda x: (x[0] or 0))


def _wshp_cooling_cop(idf):
    """Return (cop, coil_name) for the dominant WSHP cooling coil (HighriseApartment)."""
    coils = list(idf.idfobjects.get("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", []))
    if not coils:
        return None, None
    # Take first (all are autosized; use Gross_Rated_Cooling_COP)
    c = coils[0]
    cop = _safe_float(c, "Gross_Rated_Cooling_COP")
    name = getattr(c, "Name", "")
    return cop, name


def _wshp_heating_cop(idf):
    """Return (cop, coil_name) for the dominant WSHP heating coil (HighriseApartment)."""
    coils = list(idf.idfobjects.get("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", []))
    if not coils:
        return None, None
    c = coils[0]
    cop = _safe_float(c, "Gross_Rated_Heating_COP")
    name = getattr(c, "Name", "")
    return cop, name


def _fuel_heating(idf, prefer_boiler=False):
    """Return (heating_coil_type, heating_efficiency, coil_object_name).
    Default priority: Coil:Heating:Fuel > Coil:Heating:Electric > Boiler:HotWater.
    prefer_boiler=True (central-plant): Boiler:HotWater > Coil:Heating:Fuel > Electric.
    §3.1: central-plant archetypes use boiler fuel+efficiency as representative heating."""
    boilers = list(idf.idfobjects.get("BOILER:HOTWATER", []))
    if prefer_boiler and boilers:
        b = boilers[0]
        eff = _safe_float(b, "Nominal_Thermal_Efficiency")
        return "Gas", eff, getattr(b, "Name", "")

    fuel_coils = list(idf.idfobjects.get("COIL:HEATING:FUEL", []))
    if fuel_coils:
        c = fuel_coils[0]
        eff = _safe_float(c, "Burner_Efficiency")
        return "Gas", eff, getattr(c, "Name", "")

    elec_coils = list(idf.idfobjects.get("COIL:HEATING:ELECTRIC", []))
    if elec_coils:
        c = elec_coils[0]
        eff = _safe_float(c, "Efficiency")
        return "Electric", eff if eff is not None else 1.0, getattr(c, "Name", "")

    if boilers:
        b = boilers[0]
        eff = _safe_float(b, "Nominal_Thermal_Efficiency")
        return "Gas", eff, getattr(b, "Name", "")

    return None, None, None


PROTO_FILE = {
    "SmallOffice":              "ASHRAE901_OfficeSmall_STD2022_Buffalo.idf",
    "MediumOffice":             "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf",
    "LargeOffice":              "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf",
    "RetailStandalone":         "ASHRAE901_RetailStandalone_STD2022_Buffalo.idf",
    "RetailStripmall":          "ASHRAE901_RetailStripmall_STD2022_Buffalo.idf",
    "SuperMarket":              "Supermarket_V22.1.idf",
    "FullServiceRestaurant":    "ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf",
    "QuickServiceRestaurant":   "ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf",
    "SmallHotel":               "ASHRAE901_HotelSmall_STD2022_Buffalo.idf",
    "LargeHotel":               "ASHRAE901_HotelLarge_STD2022_Buffalo.idf",
    "MidriseApartment":         "ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf",
    "HighriseApartment":        "ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf",
    "Hospital":                 "ASHRAE901_Hospital_STD2022_Buffalo.idf",
    "Outpatient":               "ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf",
    "PrimarySchool":            "ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf",
    "SecondarySchool":          "ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf",
    "College":                  "College_90.1-2019_6A_Buffalo_v221.idf",
    "SmallDataCenterHighITE":   "SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf",
    "SmallDataCenterLowITE":    "SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf",
    "LargeDataCenterHighITE":   "ASHRAE901_DataCenterLargeHighITE_STD2019.idf",
    "LargeDataCenterLowITE":    "ASHRAE901_DataCenterLargeLowITE_STD2019.idf",
    "Laboratory":               "Laboratory_90.1-2019_6A_Buffalo_v221.idf",
    "Warehouse":                "ASHRAE901_Warehouse_STD2022_Buffalo.idf",
    "TallBuilding":             "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf",
    "SuperTallBuilding":        "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf",
}

INHERITS_FROM = {
    "SmallOfficeDetailed":  "SmallOffice",
    "MediumOfficeDetailed": "MediumOffice",
    "LargeOfficeDetailed":  "LargeOffice",
}

GENERIC_FALLBACK = {
    "cooling_cop": 3.0,
    "heating_coil_type": "Gas",
    "heating_efficiency": 0.80,
    "fallback": True,
}

GENERIC_FALLBACK_ARCHETYPES = {
    "Courthouse":      "No DOE prototype available; no matching IDF in repo",
    "OpenUBEMUnknown": "Synthetic sentinel; no archetype-specific prototype",
}


def extract_entry(arch_id, idf_path, source_prototype, inherit_note=None):
    """Parse idf_path and return the JSON dict for arch_id.
    Central-plant archetypes: chiller/WSHP COP × PLANT_FACTOR (§3.1).
    SmallHotel: uses PTAC SingleSpeed COP (§3.1 point 4).
    """
    idf = _parse_idf(idf_path)

    # §3.1 point 4: SmallHotel — use SingleSpeed PTAC unit COP
    if arch_id == "SmallHotel":
        coils = list(idf.idfobjects.get("COIL:COOLING:DX:SINGLESPEED", []))
        if coils:
            ptac_coil = coils[0]
            cop = _safe_float(ptac_coil, "Gross_Rated_Cooling_COP")
            coil_name = getattr(ptac_coil, "Name", "")
        else:
            cop = None
            coil_name = ""
        htg_type, htg_eff, htg_name = _fuel_heating(idf)
        return {
            "cooling_cop": cop,
            "heating_coil_type": htg_type,
            "heating_efficiency": htg_eff,
            "source_prototype": source_prototype,
            "source_coil_object": coil_name,
            "source_dx_type": "COIL:COOLING:DX:SINGLESPEED",
            "source_capacity_w": None,
            "ptac_unit_cop": True,
        }

    # §3.1 points 1-3: central-plant archetypes
    if arch_id in CENTRAL_PLANT_ARCHETYPES:
        # HighriseApartment uses WSHP loop
        if arch_id == "HighriseApartment":
            wshp_cop, wshp_name = _wshp_cooling_cop(idf)
            wshp_htg_cop, _ = _wshp_heating_cop(idf)
            raw_cop = wshp_cop
            if raw_cop is None:
                raw_cop = 4.69  # §3.1 fallback
            derated_cop = round(raw_cop * PLANT_FACTOR, 6)
            htg_eff = wshp_htg_cop if wshp_htg_cop is not None else 3.5  # §3.1 fallback
            return {
                "cooling_cop": derated_cop,
                "raw_chiller_cop": raw_cop,
                "plant_factor": PLANT_FACTOR,
                "source_chiller_object": wshp_name,
                "heating_coil_type": "Electric",
                "heating_efficiency": htg_eff,
                "source_prototype": source_prototype,
                "source_coil_object": wshp_name,
                "central_plant": True,
                "chiller_type": "COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT",
            }

        # DataCenters: no heating (§3.1 point 3)
        if arch_id in DATA_CENTER_ARCHETYPES:
            chiller = _dominant_chiller(idf)
            if chiller:
                raw_cop, cap, chiller_name, chiller_type = chiller
            else:
                raw_cop, cap, chiller_name, chiller_type = None, None, "", ""
            if raw_cop is None:
                raw_cop = 5.0
            derated_cop = round(raw_cop * PLANT_FACTOR, 6)
            return {
                "cooling_cop": derated_cop,
                "raw_chiller_cop": raw_cop,
                "plant_factor": PLANT_FACTOR,
                "source_chiller_object": chiller_name,
                "heating_coil_type": None,
                "heating_efficiency": None,
                "source_prototype": source_prototype,
                "source_coil_object": chiller_name,
                "central_plant": True,
                "chiller_type": chiller_type,
            }

        # All other central-plant: chiller + gas boiler
        chiller = _dominant_chiller(idf)
        if chiller:
            raw_cop, cap, chiller_name, chiller_type = chiller
        else:
            raw_cop, cap, chiller_name, chiller_type = None, None, "", ""
        if raw_cop is None:
            raw_cop = 4.0
        derated_cop = round(raw_cop * PLANT_FACTOR, 6)
        htg_type, htg_eff, htg_name = _fuel_heating(idf, prefer_boiler=True)
        return {
            "cooling_cop": derated_cop,
            "raw_chiller_cop": raw_cop,
            "plant_factor": PLANT_FACTOR,
            "source_chiller_object": chiller_name,
            "heating_coil_type": htg_type,
            "heating_efficiency": htg_eff,
            "source_prototype": source_prototype,
            "source_coil_object": chiller_name,
            "central_plant": True,
            "chiller_type": chiller_type,
        }

    # DX archetypes
    dominant = _dominant_dx_coil(idf)
    if dominant is None:
        cool_types = [k for k in idf.idfobjects.keys()
                      if "COOL" in k.upper() and list(idf.idfobjects.get(k, []))]
        return {
            "archetype_id": arch_id,
            "source_prototype": source_prototype,
            "non_dx": True,
            "cooling_object_types_found": cool_types,
            "note": inherit_note,
        }

    dx_type, cop, cap, coil_name = dominant
    htg_type, htg_eff, htg_name = _fuel_heating(idf)
    entry = {
        "cooling_cop": cop,
        "heating_coil_type": htg_type,
        "heating_efficiency": htg_eff,
        "source_prototype": source_prototype,
        "source_coil_object": coil_name,
        "source_dx_type": dx_type,
        "source_capacity_w": cap,
    }
    if inherit_note:
        entry["inherit_note"] = inherit_note
    return entry


def main():
    archetypes = json.loads(ARCHETYPES_PATH.read_text())["archetypes"]
    archetype_ids = [a["archetype_id"] for a in archetypes]

    result = {}

    # 1. Direct prototype extractions
    for arch_id, proto_fname in PROTO_FILE.items():
        idf_path = PROTO_DIR / proto_fname
        entry = extract_entry(arch_id, idf_path, proto_fname)
        result[arch_id] = entry

    # 2. Detailed variant inheritance
    for arch_id, base_id in INHERITS_FROM.items():
        base_entry = result[base_id]
        entry = dict(base_entry)
        entry["inherit_note"] = f"Inherits from {base_id} (Detailed variant, §3)"
        result[arch_id] = entry

    # 3. Generic fallbacks
    for arch_id, rationale in GENERIC_FALLBACK_ARCHETYPES.items():
        entry = dict(GENERIC_FALLBACK)
        entry["source_prototype"] = None
        entry["source_coil_object"] = None
        entry["fallback_rationale"] = rationale
        result[arch_id] = entry

    # 4. Validate coverage
    missing = [a for a in archetype_ids if a not in result]
    assert not missing, f"Missing archetype coverage: {missing}"

    # 5. Validation asserts (widened to [2.0, 5.5] per §3.1 — derated plant COPs like LargeOffice 5.18)
    errors = []
    for arch_id, entry in result.items():
        if entry.get("fallback") or entry.get("non_dx"):
            continue
        cop = entry.get("cooling_cop")
        if cop is None:
            errors.append(f"{arch_id}: cooling_cop is None")
        elif not (2.0 <= cop <= 5.5):
            errors.append(f"{arch_id}: cooling_cop {cop:.4f} outside [2.0, 5.5]")
        htg_type = entry.get("heating_coil_type")
        eff = entry.get("heating_efficiency")
        if htg_type is None and arch_id not in DATA_CENTER_ARCHETYPES:
            print(f"  INFO: {arch_id}: no heating coil (expected for data centers)")
        elif htg_type is not None and eff is None:
            errors.append(f"{arch_id}: heating_efficiency is None")
        elif htg_type is not None and eff is not None:
            if htg_type == "Electric" and eff > 1.0:
                # WSHP heating COP can be > 1 (it's COP, not thermal efficiency)
                pass
            elif htg_type == "Gas" and not (0.5 < eff <= 1.0):
                errors.append(f"{arch_id}: gas heating_efficiency {eff:.4f} outside (0.5, 1.0]")

    # 6. Write output
    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Written: {OUT_PATH}")

    # 7. Print coverage table
    print("\n=== ARCHETYPE -> PROTOTYPE COVERAGE TABLE ===")
    print(f"{'Archetype':<28} {'Type':<12} {'raw_COP':>8} {'plant_f':>7} {'cooling_cop':>11} {'HtgType':<10} {'HtgEff':>8} {'Flags'}")
    print("-" * 110)
    for arch_id in archetype_ids:
        entry = result[arch_id]
        if entry.get("fallback"):
            typ = "FALLBACK"
            raw = "-"
            pf = "-"
            cop_s = f"{entry['cooling_cop']:.2f}"
            htg = entry["heating_coil_type"]
            eff_s = f"{entry['heating_efficiency']:.3f}"
            flags = "fallback"
        elif entry.get("non_dx"):
            typ = "NON-DX"
            raw = "-"
            pf = "-"
            cop_s = "NONE"
            htg = "N/A"
            eff_s = "N/A"
            flags = "non_dx"
        elif entry.get("central_plant"):
            typ = "CENTRAL"
            raw_c = entry.get("raw_chiller_cop")
            raw = f"{raw_c:.4f}" if raw_c else "-"
            pf = f"{entry.get('plant_factor', PLANT_FACTOR):.2f}"
            cop_s = f"{entry['cooling_cop']:.4f}"
            htg = entry.get("heating_coil_type") or "null"
            eff_v = entry.get("heating_efficiency")
            eff_s = f"{eff_v:.3f}" if eff_v else "null"
            flags = "derated"
            if entry.get("inherit_note"):
                flags += ",inherit"
        else:
            typ = "DIRECT" if "inherit_note" not in entry else "INHERIT"
            raw = "-"
            pf = "-"
            cop_s = f"{entry['cooling_cop']:.4f}" if entry.get("cooling_cop") else "None"
            htg = entry.get("heating_coil_type") or "N/A"
            eff_v = entry.get("heating_efficiency")
            eff_s = f"{eff_v:.3f}" if eff_v else "None"
            flags = ""
            if entry.get("ptac_unit_cop"):
                flags = "ptac_unit"
        print(f"{arch_id:<28} {typ:<12} {raw:>8} {pf:>7} {cop_s:>11} {htg:<10} {eff_s:>8} {flags}")

    total = len(archetype_ids)
    covered = sum(1 for a in archetype_ids if a in result and not result[a].get("non_dx"))
    print(f"\nTotal archetypes: {total}, With valid COP: {covered}/{total}")

    if errors:
        print("\n=== VALIDATION ERRORS ===")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    else:
        print("\nAll validation asserts PASSED.")


if __name__ == "__main__":
    main()
