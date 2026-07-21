# PROVENANCE -- DOE Commercial Prototype Schedules (OQ-2)

**Edition:** ASHRAE 90.1-2013  
**Source:** U.S. DOE Building Energy Codes Program, PNNL.  
**License:** Public Domain (U.S. Federal Government work, 17 U.S.C. SS 105).  
**Energycodes.gov base URL:** https://www.energycodes.gov/prototype-building-models  

## Refresh procedure

1. Visit https://www.energycodes.gov/prototype-building-models and download the
   `ASHRAE901_<Type>_STD2013.zip` for each prototype listed below.
2. Extract any climate-variant IDF (schedules are climate-invariant per PNNL-23269 SS 3).
3. Save to `docs/implementation/scheduleDigitization/sources/<Group>_90.1-2013.idf`.
4. Re-run `python scripts/diagnostics/parse_doe_schedules.py` to regenerate
   `parsed_profiles.json` and verify EFLH cross-check.

## Per-group source map

| Group | Source IDF file | Energycodes ZIP URL | Edition | Occ object | Ltg object | Equip object | Notes |
|---|---|---|---|---|---|---|---|
| Office | `MediumOffice_90.1-2013.idf` | https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_OfficeMedium_STD2013.zip | 90.1-2013 | `BLDG_OCC_SCH` | `ltg_sch_office` | `BLDG_EQUIP_SCH` | MediumOffice dominant-zone whole-building schedules |
| Retail | `RetailStandalone_90.1-2013.idf` | https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RetailStandalone_STD2013.zip | 90.1-2013 | `BLDG_OCC_SCH` | `ltg_sch_sale` | `BLDG_EQUIP_SCH` | RetailStandalone dominant-zone; ltg_sch_sale = main sales floor (dominant area per PLAN §4); also used for SuperMarket |
| School | `SchoolPrimary_90.1-2013.idf` | https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_SchoolPrimary_STD2013.zip | 90.1-2013 | `BLDG_OCC_SCH` | `ltg_sch_classroom` | `BLDG_EQUIP_SCH` | PrimarySchool classroom-dominant; ltg_sch_classroom per PLAN §4; BLDG_OCC_SCH has seasonal structure (Through periods) — parser uses Through:12/31 period |
| Hotel | `SmallHotel_90.1-2013.idf` | energycodes.gov STD2013 (already saved in sources/) | 90.1-2013 | `GuestRoom_Occ_Sch` | `ltg_sch_guestroom` | `Guestroom_Eqp_Sch_Adva` | SmallHotel guest-room dominant zone |
| Apartment | `MidriseApartment_90.1-2013.idf` | energycodes.gov STD2013 (already saved in sources/) | 90.1-2013 | `OCC_APT_SCH_WORKING_FAMILY` | `ltg_sch_apartment_hardwired` | `EQP_APT_SCH` | MidriseApartment dwelling-unit dominant zone; lighting diversity-baked (peak=0.181 verbatim) |
| Warehouse | `Warehouse_90.1-2013.idf` | https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_Warehouse_STD2013.zip | 90.1-2013 | `BLDG_OCC_SCH` | `ltg_sch_bulk_storage` | `Bulk Storage Plug Schedule` | Warehouse bulk-storage dominant zone; ltg_sch_bulk_storage + Bulk Storage Plug Schedule per PLAN §4 / RESULT_1 map |
| Restaurant | `Restaurant_FullServiceRestaurant.idf` | energycodes.gov STD2013 (already saved in sources/) | 90.1-2013 | `BLDG_OCC_SCH` | `ltg_sch_dining` | `BLDG_EQUIP_SCH` | FullServiceRestaurant dining-zone dominant; ltg_sch_dining per PLAN §4; BLDG_EQUIP_SCH = electric plug (kitchen gas out of scope) |
| Hospital | `Hospital_90.1-2013.idf` | https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_Hospital_STD2013.zip | 90.1-2013 | `BLDG_OCC_SCH` | `ltg_sch10_patient_room` | `BLDG_EQUIP_SCH` | Hospital patient-room dominant; ltg_sch10_patient_room per PLAN §4 / RESULT_1 map |
| Outpatient | `OutPatientHealthCare_90.1-2013.idf` | https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_OutPatientHealthCare_STD2013.zip | 90.1-2013 | `BLDG_OCC_SCH` | `ltg_sch_exam` | `BLDG_EQUIP_SCH` | OutPatientHealthCare exam-room dominant; ltg_sch_exam per PLAN §4 / RESULT_1 map |

## DataCenter exception

| Group | Source IDF file | Notes |
|---|---|---|
| DataCenter | N/A | No DOE Commercial Prototype for data centers in STD2013. Kept as 24/7 constant=1.0 for all three families. Documented exception per PLAN SS 4. |

## SuperMarket note

No ASHRAE 90.1-2013 SuperMarket prototype IDF is published on energycodes.gov.
Per PLAN SS 4 and AUDIT ruling 6: SuperMarket uses the Retail group schedules
(`_SCHED_GROUP` maps SuperMarket -> Retail).
Plug EFLH difference vs Retail is only ~2.5% (RESULT_4 finding).
Refrigeration modeled by separate `Refrigeration:*` objects in OpenUBEM reconstruction layer.
