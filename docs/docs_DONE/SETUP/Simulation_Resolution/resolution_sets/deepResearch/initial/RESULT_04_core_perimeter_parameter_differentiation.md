# RESULT_04 — CORE vs PERIMETER Parameter Differentiation

This document establishes whether and how core and perimeter zones receive different inputs for zone-level models in OpenUBEM, tracing parameters to the DOE/PNNL Commercial Prototype Building Models (STD2022 release), ASHRAE Standard 90.1-2019, and ASHRAE Standard 62.1-2019.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Core vs perimeter internal-load deltas (representative archetypes)

| Archetype ID | Quantity | Core value | Perimeter value | Differentiated? | Source / Prototype ID |
|---|---|---|---|---|---|
| **SmallOffice** | LPD (W/m²)<br>EPD (W/m²)<br>Occupant density | LPD: 6.18 W/m²<br>EPD: 6.78 W/m²<br>Occupancy: 18.58 m²/person | LPD: 6.18 W/m²<br>EPD: 6.78 W/m²<br>Occupancy: 18.58 m²/person | **No** (Uniform) | `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf`<br>(Conceptually identical office space type loads) |
| **MediumOffice** | LPD (W/m²)<br>EPD (W/m²)<br>Occupant density | LPD: 5.80 W/m²<br>EPD: 10.76 W/m²<br>Occupancy: 18.58 m²/person | LPD: 5.80 W/m²<br>EPD: 10.76 W/m²<br>Occupancy: 18.58 m²/person | **No** (Uniform) | `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`<br>(Uniform office-area loads; core bottom has lifts) |
| **LargeOffice** | LPD (W/m²)<br>EPD (W/m²)<br>Occupant density | LPD: 5.78 W/m²<br>EPD: 10.76 W/m²<br>Occupancy: 18.58 m²/person | LPD: 5.78 W/m²<br>EPD: 10.76 W/m²<br>Occupancy: 18.58 m²/person | **No** (Uniform) | `ASHRAE901_OfficeLarge_STD2022_Buffalo.idf`<br>(Uniform upper office floors; core basement differs) |
| **RetailStandalone** | LPD (W/m²)<br>EPD (W/m²)<br>Occupant density | LPD: 8.69 W/m²<br>EPD: 3.23 W/m²<br>Occupancy: 6.19 m²/person | LPD: 8.69 W/m²<br>EPD: 3.23 W/m²<br>Occupancy: 6.19 m²/person | **No** (Uniform) | `ASHRAE901_RetailStandalone_STD2022_Buffalo.idf`<br>(Retail sales area is uniform; back space differs) |
| **MidriseApartment** | LPD (W/m²)<br>EPD (W/m²)<br>Occupant density | LPD: 5.16 W/m² (Corridor)<br>EPD: 0.0 W/m² (Corridor)<br>Occupancy: Unoccupied | LPD: 0.97 W/m² (Apt)<br>EPD: 6.67 W/m² (Apt)<br>Occupancy: 2-3 people/unit | **Yes** | `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`<br>(Zoned as core corridor vs perimeter dwelling units) |
| **Hospital** | LPD (W/m²)<br>EPD (W/m²)<br>Occupant density | LPD: 6.11–23.62 W/m²<br>EPD: 10.76–30.0 W/m²<br>Occupancy: 9.3–18.6 m²/person | LPD: 7.20–13.60 W/m²<br>EPD: 5.0–10.76 W/m²<br>Occupancy: 18.6 m²/person | **Yes** | `ASHRAE901_Hospital_STD2022_Buffalo.idf`<br>(Core OR/ICU/Labs vs perimeter PatRooms/ER/Offices) |
| **PrimarySchool** | LPD (W/m²)<br>EPD (W/m²)<br>Occupant density | LPD: 4.29 W/m² (Corridor)<br>EPD: 0.0 W/m² (Corridor)<br>Occupancy: Unoccupied | LPD: 7.42 W/m² (Class)<br>EPD: 8.00 W/m² (Class)<br>Occupancy: 3.72 m²/person | **Yes** | `ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf`<br>(Core corridor/mech vs perimeter classroom pods) |

---

### Table 2 — Ventilation (outdoor air) core vs perimeter

| Archetype | OA basis core (cfm/person + cfm/ft²) | OA basis perimeter | Differentiated? | Source (62.1 space type / Standard 170) |
|---|---|---|---|---|
| **Office (small/med/large)** | 5 cfm/person + 0.06 cfm/ft²<br>(2.5 L/s-person + 0.3 L/s-m²) | 5 cfm/person + 0.06 cfm/ft²<br>(2.5 L/s-person + 0.3 L/s-m²) | **No** (Uniform) | ASHRAE 62.1-2019 Table 6-1 "Office space" |
| **Retail** | 7.5 cfm/person + 0.12 cfm/ft²<br>(3.8 L/s-person + 0.6 L/s-m²) | 7.5 cfm/person + 0.12 cfm/ft²<br>(3.8 L/s-person + 0.6 L/s-m²) | **No** (Uniform) | ASHRAE 62.1-2019 Table 6-1 "Retail sales" |
| **Residential (apt)** | 0 cfm/person + 0.05 cfm/ft²<br>(0 L/s-person + 0.25 L/s-m²) | 5 cfm/person + 0.06 cfm/ft²<br>(2.5 L/s-person + 0.3 L/s-m²) | **Yes** | ASHRAE 62.1-2019 Table 6-1 "Corridor" (Core) vs "Dwelling unit" (Perimeter) |
| **School** | 0 cfm/person + 0.05 cfm/ft²<br>(0 L/s-person + 0.25 L/s-m²) | 10 cfm/person + 0.12 cfm/ft²<br>(5.0 L/s-person + 0.6 L/s-m²) | **Yes** | ASHRAE 62.1-2019 Table 6-1 "Corridor" (Core) vs "Classrooms (ages 5-8)" (Perimeter) |
| **Hospital** | OR: 20 total ACH / 4 outdoor ACH<br>Corridors: 2 total ACH / 0 outdoor ACH | Patient Rooms: 2 total ACH / 2 outdoor ACH<br>ER Exam: 6 total ACH / 2 outdoor ACH | **Yes** | ASHRAE Standard 170-2017 Table 7-1 (Ventilation of Health Care Facilities) |

---

### Table 3 — Thermostat setpoints & schedules core vs perimeter

| Item | Core | Perimeter | Differentiated? | Source |
|---|---|---|---|---|
| **Cooling setpoint (occ / unocc)** | Occupied: 75°F (23.9°C)<br>Unoccupied: 85°F (29.4°C) | Occupied: 75°F (23.9°C)<br>Unoccupied: 85°F (29.4°C) | **No** (Uniform) | ASHRAE 90.1-2019 / PNNL Prototypes |
| **Heating setpoint (occ / unocc)** | Occupied: 70°F (21.1°C)<br>Unoccupied: 60°F (15.6°C) | Occupied: 70°F (21.1°C)<br>Unoccupied: 60°F (15.6°C) | **No** (Uniform) | ASHRAE 90.1-2019 / PNNL Prototypes |
| **Setpoint schedule name (DOE prototype)** | `CLGSETP_SCH_YES_OPTIMUM`<br>`HTGSETP_SCH_YES_OPTIMUM` | `CLGSETP_SCH_YES_OPTIMUM`<br>`HTGSETP_SCH_YES_OPTIMUM` | **No** (Uniform) | PNNL STD2022 Office Prototypes |

---

### Table 4 — Window-to-wall ratio & daylighting

| Item | Core | Perimeter | Source |
|---|---|---|---|
| **WWR** | **0%** (Mathematically no exterior exposure) | Archetype-specific WWR (e.g. SmallOffice = 21.2%, MediumOffice = 33%, LargeOffice = 38%) | ASHRAE 90.1-2019 / PNNL Prototypes |
| **Daylighting controls** | **None** (Zero daylight availability) | Yes, primary daylight zones (4.57 m / 15 ft buffer depth) | ASHRAE 90.1-2019 §9.4.1.1 / PNNL Prototypes |
| **Glazing properties** | **N/A** (No windows) | Climate-zone-specific U-factor and SHGC | ASHRAE 90.1-2019 §5.5 (Envelope requirements) |

---

### Table 5 — HVAC terminal per zone

| Item | Recommendation | Source |
|---|---|---|
| **Does each core/perimeter zone get its own terminal unit (PTAC / VAV box)?** | **Yes.** Each thermal zone must have its own dedicated terminal unit (VAV box with reheat coil, or zonal PTAC/HP unit) to handle independent load dynamics. | ASHRAE 90.1-2019 Appendix G (G3.1.1) and PNNL commercial prototypes. |
| **Core vs perimeter reheat / economizer differences** | Core zone VAV reheat coils remain inactive during normal operation due to year-round cooling demand, but VAV boxes must maintain a minimum air flow setpoint (20-30%) for ventilation. Economizers are central (AHU-level). | ASHRAE 90.1-2019 §6.5.2 (reheat limits) / EnergyPlus Engineering Reference. |
| **How this maps onto OpenUBEM's per-zone HVAC assignment** | OpenUBEM iterates over all zones and writes a zone-level connection (`HVACTemplate:Zone:VAV:Reheat` or zonal terminal equipment). This already supports core/perimeter equipment separation. | `openubem/idf/builder.py:assign_hvac()` structure. |

---

## Part C — Synthesis (verdict)

We recommend a **hybrid accept-and-differentiate verdict** for OpenUBEM's `zone` mode:

1. **Accept Uniform Internal Loads and Setpoints (Default)**: For offices, retail sales areas, and generic nonresidential spaces, keep applying uniform archetype densities and setpoints to both core and perimeter zones. The PNNL prototypes themselves do not differentiate loads between office/retail core and perimeter zones of the same floor. This aligns with the **zero-fitted-parameters** rule and avoids adding arbitrary parameter knobs.
2. **Differentiate Geometry and Envelope (Glazing/WWR/Daylighting)**:
   - **WWR = 0 in Core**: You **MUST** force WWR to 0% in all core zones since they lack exterior surfaces. Placing windows in core zones is a physical impossibility.
   - **Daylighting Controls in Perimeter Only**: Enable daylighting sensors/controls exclusively in perimeter zones. Applying daylighting controls to core zones is physically incorrect and causes EnergyPlus errors or zero-saving loops.
3. **Differentiate Functional Zones by Space Type (Advanced)**: For residential, school, and hospital archetypes, core and perimeter zones map to different physical functions (e.g. core = corridor, perimeter = apartments or classrooms). For these, apply differentiated properties (e.g. corridor loads/OA to core, apartment/classroom loads/OA to perimeter) as defined in Table 1 and Table 2.

---

## Confidence and Caveats

> [!IMPORTANT]
> The single most critical parameter differentiation is **WWR = 0 in Core and Daylighting controls in Perimeter only**. Failing to set WWR = 0 in core zones will cause EnergyPlus to crash or place windows on interior walls, which violates the engine's boundary conditions.
>
> **Caveat**: PNNL prototypes specify equipment loads in total Watts (`EquipmentLevel`) rather than densities (`Watts/Area`) for offices and retail to control absolute totals. In OpenUBEM, dividing these levels by zone area yields uniform densities (e.g., 10.76 W/m² or 1.0 W/ft² for office equipment), which confirms that uniform density is the correct conceptual model for UBEM.

---

## Reference List

1. **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL)**: *Commercial Prototype Building Models (STD2022 release)*. [PNNL Prototype Models](https://www.energycodes.gov/commercial-prototype-building-models).
2. **ANSI/ASHRAE Standard 90.1-2019**: *Energy Standard for Buildings Except Low-Rise Residential Buildings*. Section 5 (Envelope), Section 6 (HVAC), Section 9 (Lighting), and Appendix G (Performance Rating Method).
3. **ANSI/ASHRAE Standard 62.1-2019**: *Ventilation for Acceptable Indoor Air Quality*. Table 6-1 (Minimum Ventilation Rates in Breathing Zone).
4. **ANSI/ASHRAE/ASHE Standard 170-2017**: *Ventilation of Health Care Facilities*. Table 7-1 (Design Parameters).
5. **EnergyPlus 23.1.0 IO Reference**: *Input Output Reference for EnergyPlus*. Section on `Lights`, `ElectricEquipment`, `People`, `ZoneControl:Thermostat`, and `HVACTemplate:Zone`.
