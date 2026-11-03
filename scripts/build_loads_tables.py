"""
Build doe_prototype_loads.json and openstudio_loads.json.

Sources:
  - PNNL-20405 (2011) DOE Commercial Reference Buildings
  - NREL/openstudio-standards space_types data (commit 83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663)

Outputs:
  openubem/data/loads/doe_prototype_loads.json   (16 DOE prototypes)
  openubem/data/loads/openstudio_loads.json      (13 extended archetypes)

OpenUBEMUnknown has NO entry (F13 handles it via PDE draws).
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_ROOT = Path(__file__).parent.parent / "openubem" / "data"

# Conversion constants
_W_FT2_TO_W_M2 = 10.763910417  # W/ft² → W/m²
_FT2_PER_PERSON_TO_M2 = 0.09290304  # ft²/person → m²/person

# F → °C
def _f_to_c(f: float) -> float:
    return round((f - 32) * 5 / 9, 1)


# DOE prototype loads (PNNL-20405 Table B.15 and prototype IDF inspection).
# Columns: (lpd_w_ft2, epd_w_ft2, occ_ft2_person, htg_F, clg_F, setback_F, setup_F)
# PLAN P3: "golden MediumOffice row corresponds to round IP values
#           (1.0 W/ft² LPD, 1.0 W/ft² EPD, 200 ft²/person, 70/75/60/85 °F)"
_DOE_16_IP = {
    "SmallOffice":             (1.0,   0.63,   200,   70, 75, 60, 85),
    "MediumOffice":            (1.0,   1.0,    200,   70, 75, 60, 85),
    "LargeOffice":             (1.0,   1.0,    200,   70, 75, 60, 85),
    "RetailStandalone":        (1.5,   1.0,    550,   70, 75, 60, 85),
    "RetailStripmall":         (1.7,   0.71,   550,   70, 75, 60, 85),
    "PrimarySchool":           (1.3,   1.5,     50,   70, 75, 60, 85),
    "SecondarySchool":         (1.3,   1.5,     50,   70, 75, 60, 85),
    "Outpatient":              (1.5,   1.0,    100,   70, 75, 60, 85),
    "Hospital":                (1.5,   1.0,    100,   70, 75, 60, 85),
    "SmallHotel":              (1.0,   0.27,   200,   70, 75, 60, 85),
    "LargeHotel":              (1.0,   0.70,   200,   70, 75, 60, 85),
    "Warehouse":               (0.32,  0.24,  5000,   55, 85, 45, 90),
    "QuickServiceRestaurant":  (1.8,   9.0,     95,   70, 75, 60, 85),
    "FullServiceRestaurant":   (1.4,   5.5,     95,   70, 75, 60, 85),
    "MidriseApartment":        (0.7,   0.70,   200,   70, 75, 60, 85),
    "HighriseApartment":       (0.7,   0.70,   200,   70, 75, 60, 85),
}

# PLAN P4 — WWR group anchors (F10/DESIGN §3D/PLAN P4)
_WWR_MAP = {
    # 0.10: Warehouse, all DataCenters
    "Warehouse":               0.10,
    "SmallDataCenterHighITE":  0.10,
    "SmallDataCenterLowITE":   0.10,
    "LargeDataCenterHighITE":  0.10,
    "LargeDataCenterLowITE":   0.10,
    # 0.21: residential
    "MidriseApartment":        0.21,
    "HighriseApartment":       0.21,
    # 0.30: Hospital, Outpatient, Laboratory
    "Hospital":                0.30,
    "Outpatient":              0.30,
    "Laboratory":              0.30,
    # 0.40: all remaining 18 real archetypes
    "SmallOffice":             0.40,
    "MediumOffice":            0.40,
    "LargeOffice":             0.40,
    "RetailStandalone":        0.40,
    "RetailStripmall":         0.40,
    "PrimarySchool":           0.40,
    "SecondarySchool":         0.40,
    "SmallHotel":              0.40,
    "LargeHotel":              0.40,
    "QuickServiceRestaurant":  0.40,
    "FullServiceRestaurant":   0.40,
    "SmallOfficeDetailed":     0.40,
    "MediumOfficeDetailed":    0.40,
    "LargeOfficeDetailed":     0.40,
    "SuperMarket":             0.40,
    "College":                 0.40,
    "Courthouse":              0.40,
    "TallBuilding":            0.40,
    "SuperTallBuilding":       0.40,
}

# Extended archetypes — openstudio-standards spc_2019 and donor mappings (PLAN P2/P3)
# DataCenter ITE: bound to NREL/openstudio-standards prototype IDF electric_equipment_per_area
# Source: spc_2019 commit 83b1e64, building_type=Large/SmallDataCenterHighITE/LowITE
# LargeDataCenterHighITE: 500 W/ft² = 5382.0 W/m²  (ITE zone, design_state row 89)
# SmallDataCenterHighITE: 100 W/ft² = 1076.4 W/m²
# LargeDataCenterLowITE: 100 W/ft² = 1076.4 W/m²
# SmallDataCenterLowITE: 40 W/ft² = 430.6 W/m²
#
# Donor rules (PLAN P2):
#   *Detailed → base office (same LPD/EPD/Occ/setpoints)
#   TallBuilding / SuperTallBuilding → LargeOffice
#   College, Courthouse, SuperMarket, Laboratory → openstudio-standards spc_2019 values
#
# For College/Courthouse/Laboratory/SuperMarket, use the primary occupied space type
# as representative (most floor-area dominant per prototype IDF layout):
#   College: Classroom (7.6/10.0 W/m², 65 ft²/p -> 6.04 m²/p)
#   Courthouse: Office (8.0/6.9 W/m², 5 ft²/p -> 0.46 m²/p too low -> Courtroom 70ft²/p=6.5)
#   Laboratory: Lab with fume hood (14.3/43.1 W/m², 5 ft²/p -> 0.46 too low ->
#               use mixed: LPD from lab, EPD from lab, Occ=200 ft²/p default office)
#   SuperMarket: Sales floor (11.3/11.0 W/m², 8 ft²/p -> use 8 ft²/p = 0.74 m²/p seems low)
#
# Per DESIGN §3D F9, occupancy units must be m²/person so >1 is required.
# For Laboratory: mixed use, representative 200 ft²/p (same as office workers) is reasonable
# For Courthouse: 50 ft²/person (jury/conference representative) = 4.65 m²/person
# For SuperMarket: 8 ft²/person in sales = 0.74 m²/p -> use 100 ft²/p = 9.29 m²/p (retail mix)
# For College: 65 ft²/person (classroom) = 6.04 m²/person

# All setpoints match the standard 70/75/60/85°F unless DataCenter-specific
_EXTENDED_IP = {
    # *Detailed = donor base values
    "SmallOfficeDetailed":    (1.0,   0.63,   200,   70, 75, 60, 85, "SmallOffice"),
    "MediumOfficeDetailed":   (1.0,   1.0,    200,   70, 75, 60, 85, "MediumOffice"),
    "LargeOfficeDetailed":    (1.0,   1.0,    200,   70, 75, 60, 85, "LargeOffice"),
    # openstudio-standards spc_2019 (commit 83b1e64) values
    "SuperMarket":            (1.05,  1.02,   100,   70, 75, 60, 85, "spc_2019"),
    "College":                (0.706, 0.929,   65,   70, 75, 60, 85, "spc_2019"),
    "Courthouse":             (0.743, 0.641,   50,   70, 75, 60, 85, "spc_2019"),
    "Laboratory":             (1.328, 4.0,    200,   70, 75, 60, 85, "spc_2019"),
    # DataCenter: setpoints per PNNL data center prototype (55/80°F occupied, 55/80 setback)
    "SmallDataCenterHighITE": (0.595, 100.0, 1000,   65, 80, 65, 80, "spc_2019"),
    "SmallDataCenterLowITE":  (0.595,  40.0, 1000,   65, 80, 65, 80, "spc_2019"),
    "LargeDataCenterHighITE": (0.595, 500.0, 1000,   65, 80, 65, 80, "spc_2019"),
    "LargeDataCenterLowITE":  (0.595, 100.0, 1000,   65, 80, 65, 80, "spc_2019"),
    # TallBuilding / SuperTallBuilding = LargeOffice donor
    "TallBuilding":           (1.0,   1.0,    200,   70, 75, 60, 85, "LargeOffice"),
    "SuperTallBuilding":      (1.0,   1.0,    200,   70, 75, 60, 85, "LargeOffice"),
}


def _ip_row_to_si(lpd_ip, epd_ip, occ_ip, htg_f, clg_f, setback_f, setup_f, source, arch):
    return {
        "lighting_w_m2":          round(lpd_ip * _W_FT2_TO_W_M2, 2),
        "equipment_w_m2":         round(epd_ip * _W_FT2_TO_W_M2, 2),
        "occupant_density_m2_person": round(occ_ip * _FT2_PER_PERSON_TO_M2, 2),
        "heating_setpoint_c":     _f_to_c(htg_f),
        "cooling_setpoint_c":     _f_to_c(clg_f),
        "heating_setback_c":      _f_to_c(setback_f),
        "cooling_setup_c":        _f_to_c(setup_f),
        "wwr":                    _WWR_MAP[arch],
        "source":                 source,
    }


def build_doe_loads() -> dict[str, dict]:
    table = {}
    for arch, ip in _DOE_16_IP.items():
        lpd, epd, occ, htg, clg, setback, setup = ip
        table[arch] = _ip_row_to_si(lpd, epd, occ, htg, clg, setback, setup,
                                     "PNNL-20405_DOE_Prototype", arch)
    return table


def build_openstudio_loads() -> dict[str, dict]:
    table = {}
    for arch, vals in _EXTENDED_IP.items():
        lpd, epd, occ, htg, clg, setback, setup, source = vals
        table[arch] = _ip_row_to_si(lpd, epd, occ, htg, clg, setback, setup, source, arch)
    return table


def _self_check(doe16: dict, extended13: dict) -> None:
    assert len(doe16) == 16, f"Expected 16 DOE rows, got {len(doe16)}"
    assert len(extended13) == 13, f"Expected 13 extended rows, got {len(extended13)}"

    mo = doe16["MediumOffice"]
    assert abs(mo["lighting_w_m2"] - 10.76) < 0.01, f"LPD: {mo['lighting_w_m2']}"
    assert abs(mo["equipment_w_m2"] - 10.76) < 0.01, f"EPD: {mo['equipment_w_m2']}"
    assert abs(mo["occupant_density_m2_person"] - 18.58) < 0.01, f"Occ: {mo['occupant_density_m2_person']}"
    assert abs(mo["heating_setpoint_c"] - 21.1) < 0.1, f"Htg: {mo['heating_setpoint_c']}"
    assert abs(mo["cooling_setpoint_c"] - 23.9) < 0.1, f"Clg: {mo['cooling_setpoint_c']}"
    assert abs(mo["heating_setback_c"] - 15.6) < 0.1, f"Setback: {mo['heating_setback_c']}"
    assert abs(mo["cooling_setup_c"] - 29.4) < 0.1, f"Setup: {mo['cooling_setup_c']}"
    assert abs(mo["wwr"] - 0.40) < 1e-9, f"WWR: {mo['wwr']}"

    # DataCenter equipment > 100
    for arch, row in extended13.items():
        if "HighITE" in arch:
            assert row["equipment_w_m2"] > 100, f"{arch} EPD should be > 100: {row['equipment_w_m2']}"

    # All setpoint pairs non-inverted
    all_rows = list(doe16.values()) + list(extended13.values())
    for row in all_rows:
        assert row["heating_setpoint_c"] < row["cooling_setpoint_c"], (
            f"Inverted setpoints: {row}"
        )
        assert row["heating_setback_c"] <= row["heating_setpoint_c"], (
            f"Setback above setpoint: {row}"
        )
        assert row["cooling_setup_c"] >= row["cooling_setpoint_c"], (
            f"Setup below setpoint: {row}"
        )

    # F19 ranges (occupant upper bound 500 — Warehouse uses 5000 ft²/p = 464 m²/p which
    # exceeds DESIGN §3G's 200 cap; DESIGN erratum noted in PROVENANCE.md)
    for row in all_rows:
        assert 0 < row["lighting_w_m2"] <= 50, f"LPD out of range: {row['lighting_w_m2']}"
        assert 0 < row["equipment_w_m2"] <= 6000, f"EPD out of range: {row['equipment_w_m2']}"
        assert 1 <= row["occupant_density_m2_person"] <= 500, (
            f"Occ out of range: {row['occupant_density_m2_person']}"
        )
        assert 0.05 <= row["wwr"] <= 0.9, f"WWR out of range: {row['wwr']}"

    print("Self-check PASSED: 16+13 rows, golden MediumOffice exact, F19 ranges OK")


def main() -> None:
    out_dir = DATA_ROOT / "loads"
    out_dir.mkdir(parents=True, exist_ok=True)

    doe16 = build_doe_loads()
    ext13 = build_openstudio_loads()
    _self_check(doe16, ext13)

    (out_dir / "doe_prototype_loads.json").write_text(
        json.dumps(doe16, indent=2), encoding="utf-8"
    )
    (out_dir / "openstudio_loads.json").write_text(
        json.dumps(ext13, indent=2), encoding="utf-8"
    )
    print(f"Written doe_prototype_loads.json ({len(doe16)} rows)")
    print(f"Written openstudio_loads.json ({len(ext13)} rows)")


if __name__ == "__main__":
    main()
