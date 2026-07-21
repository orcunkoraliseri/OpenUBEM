# Cooking and Kitchen Loads per Archetype

This document establishes the commercial cooking equipment power densities, fuel splits, heat-gain fractions, schedules, and ventilation (exhaust/makeup air) parameters across all OpenUBEM archetypes. These values are derived from the ASHRAE 90.1-2019 baseline prototype models ("STD2022" release), the ASHRAE Handbook of Fundamentals (Chapter 18), ASHRAE Handbook of HVAC Applications (Chapter 34), and ASHRAE Standard 154.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Cooking equipment power density (per archetype)

Normalizations are provided both per **kitchen floor area** (the native zone-level input) and per **whole-building floor area** (the building-level input for single-zone models).

| Archetype | Total cooking connected power | Gas density (W/m² and Btu/h·ft²) | Electric density (W/m²) | Gas : electric split (%) | Basis (per kitchen ft² / per building ft²) | Source |
|---|---|---|---|---|---|---|
| **FullServiceRestaurant** | 161,735.7 W | **Kitchen:** 614.22 W/m² (194.71 Btu/h·ft²)<br>**Building:** 83.76 W/m² (26.55 Btu/h·ft²) | **Kitchen:** 545.97 W/m² (173.07 Btu/h·ft²)<br>**Building:** 74.45 W/m² (23.60 Btu/h·ft²) | 52.9% Gas / 47.1% Electric | Kitchen: 1,500.5 ft² (139.4 m²)<br>Building: 11,004.0 ft² (1,022.3 m²) | PNNL Prototype (ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf) |
| **QuickServiceRestaurant** | 129,572.3 W | **Kitchen:** 748.62 W/m² (237.31 Btu/h·ft²)<br>**Building:** 187.15 W/m² (59.33 Btu/h·ft²) | **Kitchen:** 366.74 W/m² (116.25 Btu/h·ft²)<br>**Building:** 91.68 W/m² (29.06 Btu/h·ft²) | 67.1% Gas / 32.9% Electric | Kitchen: 1,250.5 ft² (116.2 m²)<br>Building: 5,001.8 ft² (464.7 m²) | PNNL Prototype (ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf) |
| **LargeHotel (kitchen)** | 348,405.2 W | **Kitchen:** 2,419.27 W/m² (766.91 Btu/h·ft²)<br>**Building:** 42.84 W/m² (13.58 Btu/h·ft²) | **Kitchen:** 953.35 W/m² (302.21 Btu/h·ft²)<br>**Building:** 16.88 W/m² (5.35 Btu/h·ft²) | 71.7% Gas / 28.3% Electric | Kitchen: 1,112.0 ft² (103.3 m²)<br>Building: 62,791.3 ft² (5,833.5 m²) | PNNL Prototype (ASHRAE901_HotelLarge_STD2022_Buffalo.idf) |
| **Hospital (kitchen)** | 224,918.3 W | **Kitchen:** 161.40 W/m² (51.16 Btu/h·ft²)<br>**Building:** 7.54 W/m² (2.39 Btu/h·ft²) | **Kitchen:** 80.70 W/m² (25.58 Btu/h·ft²)<br>**Building:** 3.77 W/m² (1.19 Btu/h·ft²) | 66.7% Gas / 33.3% Electric | Kitchen: 10,000.0 ft² (929.0 m²)<br>Building: 214,095.1 ft² (19,890.1 m²) | PNNL Prototype (ASHRAE901_Hospital_STD2022_Buffalo.idf) |
| **SecondarySchool (kitchen)** | 229,288.6 W | **Kitchen:** 1,678.60 W/m² (532.11 Btu/h·ft²)<br>**Building:** 18.51 W/m² (5.87 Btu/h·ft²) | **Kitchen:** 444.44 W/m² (140.89 Btu/h·ft²)<br>**Building:** 4.90 W/m² (1.55 Btu/h·ft²) | 79.1% Gas / 20.9% Electric | Kitchen: 1,162.5 ft² (108.0 m²)<br>Building: 105,443.2 ft² (9,796.0 m²) | PNNL Prototype (ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf) |
| **PrimarySchool (kitchen)** | 140,209.1 W | **Kitchen:** 1,431.10 W/m² (453.66 Btu/h·ft²)<br>**Building:** 34.99 W/m² (11.09 Btu/h·ft²) | **Kitchen:** 238.06 W/m² (75.46 Btu/h·ft²)<br>**Building:** 5.82 W/m² (1.85 Btu/h·ft²) | 85.7% Gas / 14.3% Electric | Kitchen: 904.2 ft² (84.0 m²)<br>Building: 36,979.4 ft² (3,435.5 m²) | PNNL Prototype (ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf) |
| **College (dining)** | 13,835.2 W | **Kitchen:** 0.00 W/m² (0.00 Btu/h·ft²)<br>**Building:** 0.00 W/m² (0.00 Btu/h·ft²) | **Kitchen:** 76.96 W/m² (24.40 Btu/h·ft²)<br>**Building:** 2.16 W/m² (0.68 Btu/h·ft²) | 0.0% Gas / 100.0% Electric | Cafe/Lounge: 1,935.0 ft² (179.8 m²)<br>Building: 69,055.9 ft² (6,415.5 m²) | PNNL Prototype (College_90.1-2019_6A_Buffalo_v221.idf) |
| **SuperMarket (deli/bakery)** | 15,000.0 W | **Kitchen:** 0.00 W/m² (0.00 Btu/h·ft²)<br>**Building:** 0.00 W/m² (0.00 Btu/h·ft²) | **Kitchen:** 71.77 W/m² (22.75 Btu/h·ft²)<br>**Building:** 7.18 W/m² (2.28 Btu/h·ft²) | 0.0% Gas / 100.0% Electric | BackRoom: 2,249.8 ft² (209.0 m²)<br>Building: 22,497.8 ft² (2,090.1 m²) | PNNL Prototype (Supermarket_V22.1.idf) |
| **SmallOffice** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **SmallOfficeDetailed** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **MediumOffice** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **MediumOfficeDetailed** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **LargeOffice** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **LargeOfficeDetailed** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **RetailStandalone** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **RetailStripmall** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **SmallHotel** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **MidriseApartment** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **HighriseApartment** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **Outpatient** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **Warehouse** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **SmallDataCenterHighITE**| no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **SmallDataCenterLowITE** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **LargeDataCenterHighITE**| no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **LargeDataCenterLowITE** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **Laboratory** | no cooking load | no cooking load | no cooking load | N/A | N/A | N/A |
| **Courthouse** | no cooking load | no cooking load | no cooking load | N/A | N/A (Proxy: LargeOffice) | N/A |
| **TallBuilding** | no cooking load | no cooking load | no cooking load | N/A | N/A (Proxy: LargeOffice) | N/A |
| **SuperTallBuilding** | no cooking load | no cooking load | no cooking load | N/A | N/A (Proxy: LargeOffice) | N/A |
| **OpenUBEMUnknown** | no cooking load | no cooking load | no cooking load | N/A | N/A (Proxy sentinel) | N/A |

---

### Table 2 — Cooking heat-gain fractions

The following table documents how much thermal load from cooking equipment enters the space. Fractions represent both the baseline prototype values and values for unhooded vs hooded configurations.

| Parameter | Gas equipment (Hooded) | Electric equipment (Hooded) | Gas / Electric (Unhooded) | Source |
|---|---|---|---|---|
| **Fraction radiant** | 0.20 | 0.30 | 0.30 to 0.40 | PNNL Prototype / ASHRAE Fundamentals Ch. 18 |
| **Fraction latent** | 0.10 | 0.25 | 0.10 to 0.25 | PNNL Prototype / ASHRAE Fundamentals Ch. 18 |
| **Fraction lost** (exhaust) | 0.70 | 0.20 to 0.30 | 0.00 | PNNL Prototype / ASHRAE Fundamentals Ch. 18 |
| **Fraction convective** | 0.00 | 0.15 to 0.25 | 0.35 to 0.60 | Reconstructed remainder |

> [!NOTE]
> * **Hooded Gas Equipment**: The prototype default for gas cooking equipment sets Latent = 0.10, Radiant = 0.20, Lost = 0.70, and Convective = 0.00. This indicates that 70% of the fuel input is direct heat loss captured by the exhaust hood and rejected to the outside.
> * **Hooded Electric Equipment**: The prototype default sets Latent = 0.25, Radiant = 0.30, Lost = 0.20 (FSR) or 0.30 (QSR), leaving 25% (FSR) or 15% (QSR) as convective heat to the zone.
> * **Unhooded Equipment**: Unhooded plug loads (such as warmers or registers in hospitals, supermarkets, and hotels) have a Lost fraction of 0.00, meaning 100% of their heat gain is released into the zone (typically 40%-50% radiant, 50%-60% convective, 0%-10% latent).

---

### Table 3 — Kitchen ventilation (exhaust + makeup air)

| Parameter | FullServiceRestaurant | QuickServiceRestaurant | Notes | Source |
|---|---|---|---|---|
| **Kitchen exhaust airflow** | 5,400 cfm (2.549 m³/s)<br>3.60 cfm/ft² (18.28 L/s·m²) | 3,300 cfm (1.557 m³/s)<br>2.64 cfm/ft² (13.41 L/s·m²) | Includes primary kitchen exhaust fan; excludes dining-specific exhaust. | PNNL Prototype / ASHRAE Standard 154 |
| **Hood type / duty** | Heavy Duty | Heavy Duty | Heavy Duty applies to under-hood appliances like griddles, fryers, and charbroilers. | ASHRAE Standard 154 |
| **Makeup-air fraction** | 100% of exhaust | 100% of exhaust | Sourced via outdoor air systems: 52.2% (2,821 cfm) balanced HVAC air, 47.8% (2,579 cfm) zone outdoor air. | PNNL Prototype |
| **Makeup-air conditioning** | Fully Conditioned | Fully Conditioned | Delivered by the kitchen Dedicated Outdoor Air or primary zone AirLoop (heating and cooling active). | PNNL Prototype |
| **Exhaust operating schedule** | 5:00 AM – 1:00 AM (the next day) | 5:00 AM – 1:00 AM (the next day) | Active during cooking and prep hours (20 hours daily). | PNNL Prototype (`Hours_of_operation` schedule) |

---

### Table 4 — Cooking schedule

| Archetype group | Peak fraction + meal-time profile | Reference schedule name | Source |
|---|---|---|---|
| **Restaurants (FSR/QSR)** | **Peak fraction:** 0.29<br>**Lunch peak:** 11:00 AM – 12:00 PM (Hour 11: 0.29)<br>**Dinner peak:** 4:00 PM – 6:00 PM (Hour 16-17: 0.26) | `Rest_GAS_EQUIP_SCH`<br>`FF_GAS_EQUIP_SCH`<br>`BLDG_EQUIP_SCH` | DOE/PNNL Restaurant prototypes |
| **LargeHotel (kitchen)** | **Peak fraction:** 0.30<br>**Gas profile:** peaks at breakfast (8 AM: 0.20), lunch (10 AM: 0.25), and dinner (4-6 PM: 0.30).<br>**Electric profile:** flat at 0.30 from 7:00 AM to midnight. | `Kitchen_Gas_Equip_SCH`<br>`Kitchen_Elec_Equip_SCH` | DOE/PNNL LargeHotel prototype |
| **Hospital (kitchen)** | **Peak fraction:** 0.90<br>**Meal profile:** 0.90 active from 8:00 AM to 3:00 PM; 0.60 active from 4:00 PM to 10:00 PM. | `BLDG_EQUIP_EXTD_SCH` | DOE/PNNL Hospital prototype |
| **Primary/Secondary Schools** | **Peak fraction:** 0.10 (electric), 0.02 (gas)<br>**Meal profile:** Flat occupancy profile (24 hours constant). | `KITCHEN_ELEC_EQUIP_SCH`<br>`KITCHEN_GAS_EQUIP_SCH` | DOE/PNNL School prototypes |
| **College (dining)** | **Peak fraction:** 1.00<br>**Profile:** 1.00 active from 8:00 AM to 5:00 PM; 0.40 off-peak at night. | `College BLDG_EQUIP_SCH_Base` | PNNL College prototype |
| **Supermarket (deli/bakery)** | **Peak fraction:** 1.00<br>**Profile:** 1.00 active from midnight to 6:00 PM; 0.00 from 6:00 PM to midnight. | `Bakery_Equip_Sch` | DOE/PNNL Supermarket prototype |

---

## SUPPORTING PROSE BY ARCHETYPE GROUP

### Food Service (FSR / QSR)
In restaurants, commercial cooking represents one of the largest gas and electric process loads. The prototypes are modeled with substantial kitchen equipment. In FSR (FullServiceRestaurant), cooking connected load totals **161.7 kW**, split **52.9% gas** (85.6 kW griddles, broilers, ovens) and **47.1% electric** (76.1 kW fryers, steamers, holding cabinets, and dining-area cooking/warming). In QSR (QuickServiceRestaurant), the cooking load totals **129.6 kW**, split **67.1% gas** (87.0 kW) and **32.9% electric** (42.6 kW). 

Because restaurant kitchens run heavy-duty appliances (charbroilers, fryers), they drive massive exhaust flows. Under ASHRAE Standard 154, these hoods are classified as **Heavy Duty**. The FSR kitchen exhaust fan exhausts **5,400 cfm** (\(3.60\text{ cfm/ft}^2\) of kitchen floor area), and the QSR kitchen exhaust fan exhausts **3,300 cfm** (\(2.64\text{ cfm/ft}^2\)). In both prototypes, the makeup air is balanced 100%: part is introduced as direct outdoor air sized to the kitchen zone (\(2,579\text{ cfm}\) in FSR; \(2,418\text{ cfm}\) in QSR), and the remaining part is balanced through air loop supply, tempered/conditioned by the main HVAC system to prevent large temperature swings.

### Institutional Kitchens (Hotel, Hospital, School, College)
* **LargeHotel**: The kitchen (located on Floor 6) features **348.4 kW** of connected power, with a **71.7% gas** split. The large banquet and dining zones feature electric holding and warming plug loads (22.5 kW each) controlled by the kitchen schedule. Exhaust ventilation is **4,000 cfm** (\(3.60\text{ cfm/ft}^2\)), operating on a specific hotel kitchen schedule.
* **Hospital**: The kitchen zone has **224.9 kW** of connected cooking power, split **66.7% gas** (150 kW) and **33.3% electric** (75 kW). These are modeled as unhooded process loads with a 0% lost fraction (released to the zone) and default plug load characteristics. Hospital kitchen exhaust is **7,200 cfm** (\(0.72\text{ cfm/ft}^2\)).
* **Schools**: Primary and secondary schools feature moderate kitchen connected power (**140.2 kW** and **229.3 kW** respectively) with high gas splits (**85.7%** and **79.1%**). These kitchens exhaust **4,500 cfm** and **5,400 cfm** respectively. The schedules are modeled flat (constant at 10% electric and 2% gas) to represent continuous baseline kitchen readiness.
* **College**: The dining area is modeled as a Cafe/Study Lounge with **13.8 kW** of connected electric-only equipment (76.96 W/m² over 179.8 m²) serving as the local cooking/warming load.

### Retail (Supermarket Deli / Bakery)
In supermarkets, the bakery/deli department is modeled as a **15 kW** electric process load (`SalesFloor ElecEq 2`) inside the sales floor zone. This equipment runs on the `Bakery_Equip_Sch` (1.00 multiplier from midnight to 6:00 PM and 0.00 at night) to simulate baking prep cycles. No gas equipment or exhaust fans are explicitly mapped for cooking in this prototype.

---

## CONFIDENCE AND CAVEATS

1. **Modeling Approach (Sub-zone vs Building-level)**:
   * **Recommendation**: For full physical realism, cooking loads and exhaust fans should be assigned to a separate **Kitchen sub-zone** where possible, using the **Kitchen Area** densities and exhaust flow rates. 
   * **Fallback**: If OpenUBEM models a single-zone building, the cooking loads must be scaled using the **Building Area** densities, and the kitchen exhaust airflow must be added to the zone's outdoor air/exhaust definitions.

2. **Exhaust and Makeup Air Sizing**:
   * Sizing the exhaust airflows correctly is critical for sizing the building cooling and heating plant. Because kitchen exhaust fans remove conditioned air from the zone, they must be balanced by an equivalent volume of makeup air. If makeup air is not conditioned, it will drive high infiltration loads in the kitchen. In the prototype models, makeup air is fully conditioned by the zone AirLoop.

3. **Fuel Splits and Vintage Dependence**:
   * The gas-to-electric split represents the standard ASHRAE 90.1-2019 baseline. In historical stocks (Pre-1980), gas was more dominant. In future all-electric scenarios, these gas loads will be replaced by equivalent electric load densities (primarily induction cooking, which has higher thermal efficiency, allowing a ~15%-20% reduction in connected electric power density and lower heat-gain fractions).

---

## REFERENCE LIST

1. **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL)**:
   * *Commercial Prototype Building Models (STD2022 release)*. PNNL EnergyPlus prototype IDFs for RestaurantSitDown, RestaurantFastFood, HotelLarge, Hospital, SchoolPrimary, SchoolSecondary, College, and Supermarket.
   * [PNNL Commercial Prototype Building Models Portal](https://www.energycodes.gov/prototype-building-models)

2. **ASHRAE Standard 154-2016**:
   * *Ventilation for Commercial Cooking Operations*. Atlanta, GA. Section 4: Appliance Duty Classifications (Light, Medium, Heavy, Extra-Heavy), Section 5: Exhaust Hoods, and Section 6: Exhaust Airflow Rates.

3. **ASHRAE Handbook — Fundamentals (2021)**:
   * *Chapter 18: Nonresidential Cooling and Heating Load Calculations*. Tables 5A and 5B (Heat Gain from Commercial Cooking Appliances in W and Btu/h, hooded vs unhooded).

4. **ASHRAE Handbook — HVAC Applications (2019)**:
   * *Chapter 34: Kitchen Ventilation*. Principles of capture and containment, hood design, and makeup air systems.

5. **EnergyPlus Input-Output Reference (v23.1)**:
   * *Object: ElectricEquipment, GasEquipment, OtherEquipment, Fan:ZoneExhaust, DesignSpecification:OutdoorAir*.
