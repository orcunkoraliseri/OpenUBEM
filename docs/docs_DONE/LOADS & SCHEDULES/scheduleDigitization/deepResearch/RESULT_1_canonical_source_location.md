# Canonical Source Location for U.S. DOE Commercial Prototype Building Schedules

This document presents the research findings and canonical source mappings for the operational schedules (fractional day-profiles) used in the U.S. DOE Commercial Prototype Building Models. It serves as the single reference point for the digitization process described in [PLAN_oq2-schedule-digitization.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/PLAN_oq2-schedule-digitization.md).

---

## 1. Ranked Source Options

The primary source options for per-building-type operating schedules are ranked below by authority and direct reliability for transcription.

### Rank 1: Official U.S. DOE Commercial Prototype EnergyPlus IDF Files (Authoritative & Verified)
*   **Source:** U.S. Department of Energy (DOE) Building Energy Codes Program, developed by Pacific Northwest National Laboratory (PNNL).
*   **URL:** [DOE Commercial Prototype Building Models](https://www.energycodes.gov/prototype-building-models)
*   **Format:** Compressed ZIP archives containing EnergyPlus input files (`.idf`) and HTML reports (`.htm`) covering 16 commercial building types across 19 climate locations and multiple vintage editions (e.g., ASHRAE Standard 90.1-2004 through 2022).
*   **Naming Convention:** File naming follows the pattern `ASHRAE901_<BuildingType>_<StandardVintage>_<RepresentativeCity/ClimateZone>.idf` (e.g., `ASHRAE901_OfficeMedium_STD2013_Buffalo.idf`).
*   **Mapping to Files:** The repository maps directly to local representative files saved under the baseline models path: [00.BaselineBuildings_NUs](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs). For a given prototype, the fractional occupancy, lighting, and equipment schedules are identical across all climate zones (climate-invariant), meaning any climate variant (e.g., Buffalo, CZ 6A) can be used to extract the identical load profiles.

### Rank 2: NREL/openstudio-standards Repository (Programmatic Reference)
*   **Source:** National Renewable Energy Laboratory (NREL).
*   **URL:** [NREL openstudio-standards GitHub Repository](https://github.com/NREL/openstudio-standards)
*   **Data Path:** Schedules and building assumptions are stored as JSON libraries under the standards directories, specifically at:
    `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json` (or similar standard-specific JSON files).
*   **Ruby Code Implementation:** The standards gem parses these JSON files programmatically. Code that creates and applies these schedules is located in modules under `lib/openstudio-standards/` (e.g., `space_type_add_schedules`).
*   **PNNL Database Integration:** Recent versions of the standards database are managed via the [pnnl/building-energy-standards-data](https://github.com/pnnl/building-energy-standards-data) repository, which provides a unified Python API (`pip install building-energy-standards-data`) to compile and export standards data to SQLite, JSON, and CSV.

### Rank 3: PNNL Prototype Technical Reports & Scorecard Spreadsheets (Tabular Reference)
*   **Reports:**
    *   **PNNL-23269:** *Enhancements to ASHRAE Standard 90.1 Prototype Building Models* (September 2014).
        *   URL: [PNNL-23269 PDF Document](https://www.energycodes.gov/sites/default/files/documents/PrototypeModelEnhancements_2014_0.pdf)
    *   **PNNL-20405:** *Achieving the 30% Goal: Energy and Cost Savings Analysis of ASHRAE Standard 90.1-2010* (May 2011).
        *   URL: [PNNL-20405 PDF Document](https://www.energycodes.gov/sites/default/files/documents/BECP_Energy_Cost_Savings_STD2010_May2011_v00.pdf)
*   **Tables:** Hourly schedule profiles are documented in Appendix B of PNNL-20405 (e.g., Table B.5) and updated in PNNL-23269.

---

## 2. Prototype Schedule Object Mapping

The table below maps each target prototype building to its representative source file under [00.BaselineBuildings_NUs](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs) and the exact EnergyPlus schedule object names for occupancy, lighting, and electric/plug equipment.

| Prototype | Source file/URL | Occupancy Object Name(s) | Lighting Object Name(s) | Equipment Object Name(s) |
| :--- | :--- | :--- | :--- | :--- |
| **MediumOffice** | [ASHRAE901_OfficeMedium_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_OfficeMedium_STD2022_Buffalo.idf) | `BLDG_OCC_SCH_wo_SB` (dominant)<br>`BLDG_OCC_SCH_w_SB` (setback) | `ltg_sch_office` | `BLDG_EQUIP_SCH` |
| **RetailStandalone** | [ASHRAE901_RetailStandalone_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_RetailStandalone_STD2022_Buffalo.idf) | `BLDG_OCC_SCH` | `ltg_sch_sale` (main/sale area)<br>`ltg_sch_back`, `ltg_sch_core`, `ltg_sch_entry`, `ltg_sch_front` | `BLDG_EQUIP_SCH` |
| **PrimarySchool** | [ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf) | `BLDG_OCC_SCH` (classroom)<br>`BLDG_OCC_SCH_Extend`, `BLDG_OCC_SCH_Gym`, `BLDG_OCC_SCH_Cafeteria`, `BLDG_OCC_SCH_Offices_w_SB` | `ltg_sch_classroom` (classroom)<br>`ltg_sch_office`, `ltg_sch_gym`, `ltg_sch_cafeteria`, `ltg_sch_lobby`, `ltg_sch_corridor` | `BLDG_EQUIP_SCH`<br>`KITCHEN_ELEC_EQUIP_SCH` |
| **SecondarySchool** | [ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf) | `BLDG_OCC_SCH` (classroom)<br>`BLDG_OCC_SCH_Auditorium`, `BLDG_OCC_SCH_Cafeteria`, `BLDG_OCC_SCH_Gym`, `BLDG_OCC_SCH_Offices_w_SB`, `BLDG_OCC_SCH_Extend` | `ltg_sch_classroom` (classroom)<br>`ltg_sch_auditorium`, `ltg_sch_cafeteria`, `ltg_sch_gym`, `ltg_sch_office`, `ltg_sch_corridor` | `BLDG_EQUIP_SCH`<br>`KITCHEN_ELEC_EQUIP_SCH` |
| **SmallHotel** | [ASHRAE901_HotelSmall_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_HotelSmall_STD2022_Buffalo.idf) | `GuestRoom_Occ_Sch` (guest rooms)<br>`EmployeeLounge_Occ_Sch`, `ExerciseCenter_Occ_Sch`, `Lobby_Occ_Sch`, `Office_Occ_w_SB_Sch`, `LaundryRoom_Occ_Sch`, `MeetingRoom_Occ_w_SB_Sch` | `ltg_sch_guestroom` (guest rooms)<br>`ltg_sch_lobby`, `ltg_sch_office`, `ltg_sch_corridor` | `Guestroom_Eqp_Sch_Adva` (guest rooms)<br>`OFF_EQUIP_SCH`, `Lobby_Eqp_Sch`, `LaundryRoom_Eqp_Elec_Sch` |
| **LargeHotel** | [ASHRAE901_HotelLarge_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_HotelLarge_STD2022_Buffalo.idf) | `GuestRoom_Occ_Sch` (guest rooms)<br>`BLDG_OCC_SCH` (common areas) | `ltg_sch_guestroom` (guest rooms)<br>`ltg_sch_lobby`, `ltg_sch_dining`, `ltg_sch_kitchen`, `ltg_sch_corridor` | `Guestroom_Eqp_Sch_Adva` (guest rooms)<br>`BLDG_EQUIP_SCH`, `Kitchen_Elec_Equip_SCH` |
| **MidriseApartment** | [ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf) | `OCC_APT_SCH_WORKING_FAMILY`<br>`OCC_APT_SCH_STAY_HOME_FAMILY` | `ltg_sch_apartment_hardwired`<br>`ltg_sch_apartment_plugin` | `EQP_APT_SCH` |
| **Warehouse** | [ASHRAE901_Warehouse_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_Warehouse_STD2022_Buffalo.idf) | `BLDG_OCC_SCH` (office area only) | `ltg_sch_bulk_storage` (bulk storage)<br>`ltg_sch_fine_storage` (fine storage)<br>`ltg_sch_office` (office area) | `Bulk Storage Plug Schedule`<br>`Office_Plug_SCH` |
| **FullServiceRestaurant** | [ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf) | `BLDG_OCC_SCH` | `ltg_sch_dining` (dining area)<br>`ltg_sch_kitchen` (kitchen area) | `BLDG_EQUIP_SCH` (dining)<br>`Always_on` (kitchen) |
| **QuickServiceRestaurant** | [ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf) | `BLDG_OCC_SCH` | `ltg_sch_dining` (dining area)<br>`ltg_sch_kitchen` (kitchen area) | `BLDG_EQUIP_SCH` (dining)<br>`Always_on` (kitchen) |
| **Hospital** | [ASHRAE901_Hospital_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_Hospital_STD2022_Buffalo.idf) | `BLDG_OCC_SCH` (standard areas)<br>`BLDG_OCC_EXTD_SCH` (extended) | `ltg_sch10_patient_room` (patient rooms)<br>`ltg_sch1_office`, `ltg_sch12_lab`, `ltg_sch14_dining`, `ltg_sch15_kitchen`, `ltg_sch4_corridor` | `BLDG_EQUIP_SCH`<br>`BLDG_EQUIP_EXTD_SCH` |
| **Outpatient** | [ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf) | `BLDG_OCC_SCH` (outpatient)<br>`OFFICE_OCC_w_SB_SCH`, `MEETINGROOM_OCC_w_SB_SCH` | `ltg_sch_exam` (exam room)<br>`ltg_sch_office`, `ltg_sch_lobby`, `ltg_sch_operation`, `ltg_sch_radiology` | `BLDG_EQUIP_SCH` |
| **SuperMarket** | [Supermarket_V22.1.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/validations/Level%202%20DOE%20round-trip/00.BaselineBuildings_NUs/Supermarket_V22.1.idf) | `People_Shopping_Sch` | `Lighting_Sch` | `Elec_Equip_Sch` (general)<br>`Register_Equip_Sch`, `Bakery_Equip_Sch` |

---

## 3. License and Redistribution Terms

### U.S. DOE Commercial Prototype IDFs (PNNL)
*   **License Status:** Public Domain.
*   **Terms:** These models are developed by Pacific Northwest National Laboratory (PNNL) under contract for the U.S. Department of Energy (a U.S. Federal Government agency). As works of the U.S. Government, they are not subject to copyright protection within the United States.
*   **Redistribution:** Fully permitted. You may extract, digitize, and redistribute the schedule fraction values within any open-source or commercial project without restrictions. Standard academic and professional attribution is requested.

### NREL `openstudio-standards` Data
*   **License Status:** Revised BSD 3-Clause License.
*   **License Link:** [openstudio-standards LICENSE.md](https://github.com/NREL/openstudio-standards/blob/master/LICENSE.md)
*   **Quoted License Terms:**
    > Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
    > 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    > 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    > 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
*   **Redistribution:** Fully permitted. Redistributing the digitized schedule fraction values in an open-source project is permitted under the BSD-3 terms, provided the copyright notice and disclaimers are preserved.

---

## 4. Refresh Procedure

To re-pull and verify these exact source files programmatically in the future, follow this minimal workflow:

1.  **Clone the target OpenStudio Standards repository:**
    ```bash
    git clone https://github.com/NREL/openstudio-standards.git
    cd openstudio-standards
    git checkout <pinned-release-tag-or-commit-hash>
    ```
2.  **Access the data folder:**
    - Navigate to the standard JSON files: `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
3.  **Alternate (PNNL database):**
    - Install the PNNL standards database via python pip:
      ```bash
      pip install building-energy-standards-data
      ```
    - Use the Python API to extract the desired ASHRAE 90.1-2013 space-type operational schedules.

---

## 5. Note on Climate Invariance

*   **Invariance Status:** Verified **identical (climate-invariant)**.
*   **Explanation:** The fractional day-profiles for occupancy, lighting, and electric equipment are constant across all climate zones for a given building prototype and standard vintage. While weather-dependent components (HVAC sizing, thermal coefficients, insulation thickness, and window solar heat gain coefficients) change across the 16+ climate locations to meet zone-specific compliance, the internal load schedules (defining when occupants occupy the space and when equipment/lighting is active) are kept constant.
*   **Justification:** This standardization isolates weather and efficiency-driven energy variations during policy analysis, ensuring that comparison profiles are not skewed by regional behavioral assumptions.
*   **Citation Reference:** Documented in Section 3 of PNNL-23269 (*Enhancements to ASHRAE Standard 90.1 Prototype Building Models*) and on the [DOE Building Energy Codes Program site](https://www.energycodes.gov/prototype-building-models).

---

## Full Citations
1.  *Commercial Prototype Building Models*, U.S. Department of Energy, Building Energy Codes Program, Pacific Northwest National Laboratory, standard version ASHRAE Standard 90.1-2013 / 90.1-2022, [URL](https://www.energycodes.gov/prototype-building-models), Accessed: June 17, 2026.
2.  *openstudio-standards*, NatLabRockies / National Renewable Energy Laboratory (NREL), Version 0.20.0+ / master branch, [GitHub URL](https://github.com/NREL/openstudio-standards), Accessed: June 17, 2026.
3.  *Enhancements to ASHRAE Standard 90.1 Prototype Building Models*, Pacific Northwest National Laboratory, PNNL-23269, September 2014, [PDF URL](https://www.energycodes.gov/sites/default/files/documents/PrototypeModelEnhancements_2014_0.pdf), Accessed: June 17, 2026.
4.  *Achieving the 30% Goal: Energy and Cost Savings Analysis of ASHRAE Standard 90.1-2010*, Pacific Northwest National Laboratory, PNNL-20405, May 2011, [PDF URL](https://www.energycodes.gov/sites/default/files/documents/BECP_Energy_Cost_Savings_STD2010_May2011_v00.pdf), Accessed: June 17, 2026.
