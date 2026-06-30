# RESULT — HVAC System-Type Assignment per Archetype

This document establishes the per-archetype assignment of HVAC system types for OpenUBEM Phase-E, tracing assignments to ASHRAE Standard 90.1-2019 Appendix G and the DOE/PNNL Commercial Prototype Building Models.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Per-archetype HVAC system assignment

| Archetype ID | DOE/PNNL prototype | App G baseline system (# + name, cite G3.1.1-3/-4) | System the prototype actually uses | Cooling source | Heating source + fuel | Air distribution (CV / VAV; zonal / central) | Source |
|---|---|---|---|---|---|---|---|
| **SmallOffice** | `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf` | System 3 (PSZ-AC, Table G3.1.1-3 Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Packaged Single-Zone Heat Pump (PSZ-HP) w/ supplemental gas heating | DX (Direct Expansion) | Heat Pump (Electric) + Supplemental Gas Furnace | CV (Constant Volume); Zonal | PNNL OfficeSmall Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **SmallOfficeDetailed** | Inherits from `SmallOffice` | System 3 (PSZ-AC, Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Packaged Single-Zone Heat Pump (PSZ-HP) w/ supplemental gas heating | DX (Direct Expansion) | Heat Pump (Electric) + Supplemental Gas Furnace | CV (Constant Volume); Zonal | Inherits from `SmallOffice` |
| **MediumOffice** | `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Packaged VAV with zonal electric reheat and central gas furnace | DX (Direct Expansion) | Electric Resistance (zonal reheat) + Gas Furnace (central morning warm-up) | VAV; Central (floor-by-floor) | PNNL OfficeMedium Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **MediumOfficeDetailed** | Inherits from `MediumOffice` | System 5 (Packaged VAV w/ reheat, Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Packaged VAV with zonal electric reheat and central gas furnace | DX (Direct Expansion) | Electric Resistance (zonal reheat) + Gas Furnace (central morning warm-up) | VAV; Central (floor-by-floor) | Inherits from `MediumOffice` |
| **LargeOffice** | `ASHRAE901_OfficeLarge_STD2022_Buffalo.idf` | System 7 (VAV w/ reheat, Table G3.1.1-3 Row 5) [NYC/LA] / System 8 (VAV w/ PFP, Row 5) [Austin] | Built-up VAV w/ chilled-water cooling and hot-water reheat | Chilled Water (central water-cooled chiller) | Hot Water (central gas boiler) | VAV; Central | PNNL OfficeLarge Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **LargeOfficeDetailed** | Inherits from `LargeOffice` | System 7 (VAV w/ reheat, Row 5) [NYC/LA] / System 8 (VAV w/ PFP, Row 5) [Austin] | Built-up VAV w/ chilled-water cooling and hot-water reheat | Chilled Water (central water-cooled chiller) | Hot Water (central gas boiler) | VAV; Central | Inherits from `LargeOffice` |
| **RetailStandalone** | `ASHRAE901_RetailStandalone_STD2022_Buffalo.idf` | System 3 (PSZ-AC, Table G3.1.1-3 Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Packaged Single-Zone Air Conditioner (PSZ-AC) w/ gas furnace | DX (Direct Expansion) | Gas Furnace (Natural Gas) | CV (Constant Volume); Zonal | PNNL RetailStandalone Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **RetailStripmall** | `ASHRAE901_RetailStripmall_STD2022_Buffalo.idf` | System 3 (PSZ-AC, Table G3.1.1-3 Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Packaged Single-Zone Air Conditioner (PSZ-AC) w/ gas furnace | DX (Direct Expansion) | Gas Furnace (Natural Gas) | CV (Constant Volume); Zonal | PNNL RetailStripmall Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **SuperMarket** | `Supermarket_V22.1.idf` | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Packaged Single-Zone Air Conditioner (PSZ-AC) w/ gas furnace | DX (Direct Expansion) | Gas Furnace (Natural Gas) | CV (Constant Volume); Central | PNNL Supermarket Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **FullServiceRestaurant** | `ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf` | System 3 (PSZ-AC, Table G3.1.1-3 Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Packaged Single-Zone Air Conditioner (PSZ-AC) w/ gas furnace | DX (Direct Expansion) | Gas Furnace (Natural Gas) | CV (Constant Volume); Zonal | PNNL RestaurantSitDown Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **QuickServiceRestaurant** | `ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf` | System 3 (PSZ-AC, Table G3.1.1-3 Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Packaged Single-Zone Air Conditioner (PSZ-AC) w/ gas furnace | DX (Direct Expansion) | Gas Furnace (Natural Gas) | CV (Constant Volume); Zonal | PNNL RestaurantFastFood Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **SmallHotel** | `ASHRAE901_HotelSmall_STD2022_Buffalo.idf` | System 1 (PTAC, Table G3.1.1-3 Row 1) [NYC/LA] / System 2 (PTHP, Row 1) [Austin] | PTAC (zonal guest rooms) + PSZ-AC (gas furnace, common areas) | DX (Direct Expansion) | Electric Resistance (guest rooms) + Gas Furnace (common areas) | CV (Constant Volume); Zonal | PNNL HotelSmall Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **LargeHotel** | `ASHRAE901_HotelLarge_STD2022_Buffalo.idf` | System 1 (PTAC, Table G3.1.1-3 Row 1) [NYC/LA] / System 2 (PTHP, Row 1) [Austin] | Four-Pipe Fan Coil Units (guest rooms) + Central VAV w/ hot-water reheat (common areas) | Chilled Water (central water-cooled chiller) | Hot Water (central gas boiler) | CV Zonal (guest rooms) / VAV Central (common areas) | PNNL HotelLarge Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **MidriseApartment** | `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` | System 1 (PTAC, Table G3.1.1-3 Row 1) [NYC/LA] / System 2 (PTHP, Row 1) [Austin] | Zonal residential split DX air conditioner w/ gas furnace | DX (Direct Expansion) | Gas Furnace (Natural Gas) | CV (Constant Volume); Zonal | PNNL ApartmentMidRise Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **HighriseApartment** | `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` | System 1 (PTAC, Table G3.1.1-3 Row 1) [NYC/LA] / System 2 (PTHP, Row 1) [Austin] | Water-Loop Heat Pump (WLHP) system w/ individual water-to-air heat pumps | DX (Water-to-Air heat pump) | DX Heat Pump (Electric) + central loop Gas Boiler heat | CV (Constant Volume); Zonal | PNNL ApartmentHighRise Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **Hospital** | `ASHRAE901_Hospital_STD2022_Buffalo.idf` | System 7 (VAV w/ reheat, Table G3.1.1-3 Row 7) [NYC/LA] / System 8 (VAV w/ PFP, Row 7) [Austin] | Built-up VAV w/ chilled-water cooling and hot-water reheat | Chilled Water (central water-cooled chillers) | Hot Water (central gas boiler) | VAV Central (CV Zonal for kitchen CAV) | PNNL Hospital Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **Outpatient** | `ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf` | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Packaged VAV w/ hot-water reheat (DX central cooling, central gas boiler) | DX (Direct Expansion) | Hot Water (central gas boiler) | VAV; Central | PNNL OutpatientHealthCare Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **PrimarySchool** | `ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf` | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Hybrid (Packaged VAV w/ hot-water reheat for classrooms; PSZ-AC for admin/gym) | DX (Direct Expansion) | Hot Water (central gas boiler) + Gas Furnace (PSZ units) | VAV Central (classrooms) / CV Zonal (admin/gym) | PNNL SchoolPrimary Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **SecondarySchool** | `ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf` | System 7 (VAV w/ reheat, Table G3.1.1-3 Row 5) [NYC/LA] / System 8 (VAV w/ PFP, Row 5) [Austin] | Hybrid (VAV w/ chilled-water cooling & hot-water reheat for classrooms; PSZ-AC for gym) | Chilled Water (central water-cooled chiller) + DX (PSZ units) | Hot Water (central gas boiler) + Gas Furnace (PSZ units) | VAV Central (classrooms) / CV Zonal (gym) | PNNL SchoolSecondary Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **College** | `College_90.1-2019_6A_Buffalo_v221.idf` | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Central plant VAV with hot water reheat | Chilled Water (central water-cooled chiller) | Hot Water (central gas boiler) | VAV; Central | PNNL College Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **Laboratory** | `Laboratory_90.1-2019_6A_Buffalo_v221.idf` | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Packaged VAV w/ hot-water reheat (including 100% Outdoor Air loop w/ exhaust) | DX (Direct Expansion) | Hot Water (central gas boiler) | VAV; Central | PNNL Laboratory Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **Warehouse** | `ASHRAE901_Warehouse_STD2022_Buffalo.idf` | System 9 (Gas furnace CV, Table G3.1.1-3 Row 6) [NYC/LA] / System 10 (Electric furnace CV, Row 6) [Austin] | Hybrid (PSZ-AC for office/fine storage; Gas radiant & unit heaters for bulk storage) | DX (Direct Expansion, offices only) / None (bulk storage) | Gas Furnace (offices) + Gas Radiant/Unit Heaters (bulk storage) | CV (Constant Volume); Zonal | PNNL Warehouse Prototype Model, ASHRAE 90.1-2019 Appendix G |
| **SmallDataCenterHighITE** | `SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf` | System 3 (PSZ-AC, Table G3.1.1-3 Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Computer Room Air Conditioner (CRAC) | DX (Direct Expansion) | None | VAV (Variable Volume); Zonal | PNNL DataCenter Small Prototype, ASHRAE 90.1-2019 Appendix G |
| **SmallDataCenterLowITE** | `SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf` | System 3 (PSZ-AC, Row 3) [NYC/LA] / System 4 (PSZ-HP, Row 3) [Austin] | Computer Room Air Conditioner (CRAC) | DX (Direct Expansion) | None | VAV (Variable Volume); Zonal | Inherits from `SmallDataCenterHighITE` |
| **LargeDataCenterHighITE** | `ASHRAE901_DataCenterLargeHighITE_STD2019.idf` | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Computer Room Air Handler (CRAH) | Chilled Water (central water-cooled chiller) | None | VAV (Variable Volume); Zonal | PNNL DataCenter Large Prototype, ASHRAE 90.1-2019 Appendix G |
| **LargeDataCenterLowITE** | `ASHRAE901_DataCenterLargeLowITE_STD2019.idf` | System 5 (Packaged VAV w/ reheat, Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Computer Room Air Handler (CRAH) | Chilled Water (central water-cooled chiller) | None | VAV (Variable Volume); Zonal | Inherits from `LargeDataCenterHighITE` |
| **Courthouse** | None (No PNNL prototype) | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Proxy recommendation: `MediumOffice` Packaged VAV w/ hot-water reheat | DX (Direct Expansion) | Hot Water (central gas boiler) | VAV; Central | **PROXY DECISION** (Courthouse has no native PNNL prototype) |
| **TallBuilding** | None (custom) | System 7 (VAV w/ reheat, Table G3.1.1-3 Row 5) [NYC/LA] / System 8 (VAV w/ PFP, Row 5) [Austin] | Proxy recommendation: `LargeOffice` VAV w/ chilled-water cooling & hot-water reheat | Chilled Water (central water-cooled chiller) | Hot Water (central gas boiler) | VAV; Central | Proxy recommendation mapped to LargeOffice |
| **SuperTallBuilding** | None (custom) | System 7 (VAV w/ reheat, Table G3.1.1-3 Row 5) [NYC/LA] / System 8 (VAV w/ PFP, Row 5) [Austin] | Proxy recommendation: `LargeOffice` VAV w/ chilled-water cooling & hot-water reheat | Chilled Water (central water-cooled chiller) | Hot Water (central gas boiler) | VAV; Central | Proxy recommendation mapped to LargeOffice |
| **OpenUBEMUnknown** | None (sentinel) | System 5 (Packaged VAV w/ reheat, Table G3.1.1-3 Row 4) [NYC/LA] / System 6 (Packaged VAV w/ PFP, Row 4) [Austin] | Proxy recommendation: `MediumOffice` Packaged VAV w/ hot-water reheat | DX (Direct Expansion) | Hot Water (central gas boiler) | VAV; Central | **PROXY DECISION** (Conservative general nonresidential proxy) |

---

## Table 2 — The ASHRAE 90.1-2019 Appendix G selection logic (the rule behind Table 1)

| Building-type category | #Floors / area breakpoint | Baseline system # | System name | Fan | Heating type | Cite (G3.1.1-3 / -4 row) |
|---|---|---|---|---|---|---|
| **Residential** | Any size / any floors | System 1 [NYC/LA] <br> System 2 [Austin] | PTAC (System 1) <br> PTHP (System 2) | CV | Hot-Water Fossil Fuel Boiler <br> Electric Heat Pump | Table G3.1.1-3 Row 1; Table G3.1.1-4 |
| **Public assembly** | < 120,000 ft² (11,000 m²) | System 3 [NYC/LA] <br> System 4 [Austin] | PSZ-AC (System 3) <br> PSZ-HP (System 4) | CV | Fossil Fuel Furnace <br> Electric Heat Pump | Table G3.1.1-3 Row 2; Table G3.1.1-4 |
| **Public assembly** | ≥ 120,000 ft² (11,000 m²) | System 12 [NYC/LA] <br> System 13 [Austin] | SZ-CV-HW (System 12) <br> SZ-CV-ER (System 13) | CV | Hot-Water Fossil Fuel Boiler <br> Electric Resistance | Table G3.1.1-3 Row 2; Table G3.1.1-4 |
| **Nonresidential** | ≤ 3 floors AND < 25,000 ft² (2,300 m²) | System 3 [NYC/LA] <br> System 4 [Austin] | PSZ-AC (System 3) <br> PSZ-HP (System 4) | CV | Fossil Fuel Furnace <br> Electric Heat Pump | Table G3.1.1-3 Row 3; Table G3.1.1-4 |
| **Nonresidential** | 4–5 floors OR 25,000–150,000 ft² (2,300–14,000 m²) | System 5 [NYC/LA] <br> System 6 [Austin] | Packaged VAV w/ reheat (System 5) <br> Packaged VAV w/ PFP (System 6) | VAV | Hot-Water Fossil Fuel Boiler <br> Electric Resistance (reheat) | Table G3.1.1-3 Row 4; Table G3.1.1-4 |
| **Nonresidential** | > 5 floors OR > 150,000 ft² (14,000 m²) | System 7 [NYC/LA] <br> System 8 [Austin] | VAV w/ reheat (System 7) <br> VAV w/ PFP (System 8) | VAV | Hot-Water Fossil Fuel Boiler <br> Electric Resistance (reheat) | Table G3.1.1-3 Row 5; Table G3.1.1-4 |
| **Heated-only storage** | Any size / any floors | System 9 [NYC/LA] <br> System 10 [Austin] | Gas Furnace (System 9) <br> Electric Furnace (System 10) | CV | Fossil Fuel Furnace <br> Electric Resistance | Table G3.1.1-3 Row 6; Table G3.1.1-4 |

---

### Table 3 — Special-system archetypes (where App G's generic rule is overridden by use)

| Archetype | System the prototype uses | Why it differs from the generic rule | Key feature for modelling | Source |
|---|---|---|---|---|
| **Hospital** | Central VAV with chilled-water cooling and hot-water reheat (System 7/8) | Strict zoning, infection control, and high outdoor air ventilation requirements override low-rise VAV rules. | Central hydronic water-cooled chillers, multi-boiler hot water loop, CAV loop for kitchens. | PNNL Hospital Prototype TSD |
| **Laboratory** | Packaged VAV with hot-water reheat + 100% Outdoor Air loop | Laboratory chemical fumes require 100% outdoor air intake and exhaust with zero return-air recirculation in lab spaces. | Dedicated 100% Outdoor Air VAV system, exhaust fan flow tracking. | PNNL Laboratory Prototype TSD |
| **SuperMarket** | Packaged Single-Zone Air Conditioner (PSZ-AC) w/ gas furnace | Supermarkets require constant-volume single-zone systems to control humidity and avoid interfering with refrigerated display cases. | Constant volume single-zone air distribution, integrated refrigeration heat rejection. | PNNL Supermarket Prototype TSD |
| **Warehouse** | Zonal PSZ-AC (offices) + Gas radiant & unit heaters (bulk storage) | Bulk storage zones are heated-only, uncooled large volumes that rely on high-capacity radiant and unit heaters. | Heated-only bulk zone, unit heaters, zonal split layout. | PNNL Warehouse Prototype TSD |
| **Data center (High/Low ITE)** | Computer Room Air Conditioner (CRAC - small) or Computer Room Air Handler (CRAH - large) | Data centers have very high sensible ITE cooling loads, zero heating load, and require high airflow circulation. | High sensible heat ratio, air/water-side economizers, no heating coils. | PNNL DataCenter Prototypes TSD |
| **Large/Highrise residential** | Four-Pipe Fan Coil Units (LargeHotel guest rooms) or Water-Loop Heat Pump (HighriseApartment) | High-density multi-zone residential units require flexible local control and hydronic loop distribution for energy efficiency. | Central fluid cooler & gas boiler loop (WLHP) or central chilled/hot water serving local fan coils. | PNNL HotelLarge / ApartmentHighRise TSDs |

---

### Table 4 — Custom / no-prototype archetypes — proxy recommendation

| Archetype | Recommended system proxy | Rationale | Source |
|---|---|---|---|
| **TallBuilding** | `LargeOffice` VAV w/ chilled-water cooling & hot-water reheat (System 7/8) | Multi-story high-rise structures require central hydronic plants (chillers/boilers) and VAV reheat. | Matches large office central plant proxy. |
| **SuperTallBuilding** | `LargeOffice` VAV w/ chilled-water cooling & hot-water reheat (System 7/8) | Supertall structures utilize centralized hydronic VAV reheat networks for floor-by-floor distribution. | Matches large office central plant proxy. |
| **Courthouse** | `MediumOffice` Packaged VAV w/ hot-water reheat (System 5/6) | Courthouses are multi-zone, public nonresidential spaces best represented by Packaged VAV with hot-water reheat. | Multi-zone nonresidential public VAV proxy. |
| **OpenUBEMUnknown** | `MediumOffice` Packaged VAV w/ hot-water reheat (System 5/6) | Provides a conservative, representative multi-zone VAV baseline for unknown nonresidential spaces. | General conservative VAV proxy. |

---

## Part C — Decision summary

Based on the actual system configurations in the 30 building archetypes, we collapse the roster into **10 distinct HVAC system families** for OpenUBEM to implement via EnergyPlus `HVACTemplate` structures:

1. **PSZ-AC w/ Gas Furnace (System 3)**: Constant-volume single-zone packaged units w/ DX cooling and gas heating. (Used by: `RetailStandalone`, `RetailStripmall`, `SuperMarket`, `FullServiceRestaurant`, `QuickServiceRestaurant`, `MidriseApartment` splits, and common areas in `SmallHotel`, `PrimarySchool`, `SecondarySchool`, `Warehouse` offices).
2. **PSZ-HP w/ Gas Backup (System 4)**: Constant-volume single-zone packaged units w/ DX heat pump heating/cooling and backup gas furnace. (Used by: `SmallOffice`, `SmallOfficeDetailed`).
3. **Packaged VAV w/ Electric Reheat (System 6)**: Variable air volume w/ packaged central DX cooling, central gas furnace (morning warm-up), and zonal electric resistance reheat coils. (Used by: `MediumOffice`, `MediumOfficeDetailed`).
4. **Built-up VAV w/ Chilled Water & Hot Water Reheat (System 7)**: Variable air volume w/ water-cooled chiller loop, hot water boiler loop, and zonal hot water reheat coils. (Used by: `LargeOffice`, `LargeOfficeDetailed`, `Hospital`, `College`, `SecondarySchool` main pods, `TallBuilding`, `SuperTallBuilding`).
5. **Packaged VAV w/ Hot Water Reheat (System 5)**: Variable air volume w/ central DX cooling, hot water boiler loop, and zonal hot water reheat coils. (Used by: `Outpatient`, `PrimarySchool` main pods, `Laboratory` (standard & DOAS loops), and proxies `Courthouse`, `OpenUBEMUnknown`).
6. **Water-Loop Heat Pump (WLHP)**: Constant-volume zonal water-to-air heat pump units in each zone, served by a central loop gas boiler and loop fluid cooler. (Used by: `HighriseApartment`).
7. **Four-Pipe Fan Coil Units (FPFC)**: Constant-volume zonal fan coil units served by central chilled water (chiller) and hot water (boiler) loops, plus a DOAS ventilation loop. (Used by: `LargeHotel` guest rooms).
8. **PTAC w/ Electric Reheat (System 1)**: Constant-volume zonal PTAC units in each zone w/ DX cooling and electric resistance heating. (Used by: `SmallHotel` guest rooms).
9. **Heated-only Radiant / Unit Heaters (System 9)**: Constant-volume zonal gas radiant heaters and gas unit heaters. (Used by: `Warehouse` bulk storage).
10. **Data Center CRAC / CRAH**: Computer Room Air Conditioner (CRAC - DX) or Computer Room Air Handler (CRAH - Chilled Water) with variable volume fans and no heating. (Used by: `SmallDataCenterHighITE`, `SmallDataCenterLowITE`, `LargeDataCenterHighITE`, `LargeDataCenterLowITE`).

---

## Part D — Confidence and Caveats

### 1. Divergence between App G Baseline and Prototype Actuals
For several key archetypes, the PNNL prototype building model deviates from the generic selection logic in ASHRAE 90.1 Appendix G Table G3.1.1-3:
* **Supermarket:** App G assigns VAV (System 5/6), but the prototype uses a constant-volume PSZ-AC system. This is because VAV systems are highly problematic in supermarkets due to massive sensible/latent loads from open refrigerated displays.
* **LargeHotel & HighriseApartment:** App G assigns PTAC/PTHP (System 1/2), but the prototypes use central Four-Pipe Fan Coils (LargeHotel) and Water-Loop Heat Pumps (HighriseApartment). These central plant designs represent standard large-scale engineering practice for taller high-rise residential projects.
* **SmallOffice:** App G assigns PSZ-AC (System 3) for Zones 3-8, but the prototype actually implements a PSZ-HP (Heat Pump) with gas burner backup.

### 2. Modeling Recommendation
For OpenUBEM Phase-E, **we recommend adopting the prototype-actual systems** rather than strictly enforcing the generic App G baseline. The reasons are two-fold:
1. **Efficiency and Sizing Alignment:** Prompt 02 collects actual plant, pump, and airside parameters (such as fan power and chiller/boiler efficiencies) straight from these PNNL prototype IDFs. Choosing the actual system type ensures these physical parameters map correctly.
2. **Physical Realism:** The prototype systems represent what is physically engineered (e.g. WLHP in high-rise apartments to manage heating loop addition), which leads to far more accurate load profile simulations.

---

## Part E — References

1. **ASHRAE Standard 90.1-2019**, Normative Appendix G: Performance Rating Method. Table G3.1.1-3 "Baseline HVAC System Types" and Table G3.1.1-4 "Baseline System Descriptions."
2. **U.S. Department of Energy (DOE) & Pacific Northwest National Laboratory (PNNL)**. *Commercial Prototype Building Models (STD2022 release)*. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
3. **PNNL Technical Support Documents (TSDs)**:
   * *Commercial Prototype Building Models: Office, Retail, Lodging, Apartment, Healthcare, Education, Warehouse, and Data Center.* Pacific Northwest National Laboratory, Richland, WA.
4. **EnergyPlus Input-Output Reference & Engineering Reference (v22.1)**. *HVACTemplate objects documentation*.
