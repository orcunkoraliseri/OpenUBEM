# PROVENANCE — openubem/data/construction/

## ashrae_90_1_2019.json

**Source repository:** NREL/openstudio-standards
**Commit:** `83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663`
**Retrieval date:** 2026-06-10
**License:** Apache 2.0
**URL:** https://github.com/NREL/openstudio-standards

### Files used

| File | Path in repo | Notes |
|---|---|---|
| `ashrae_90_1_2019.construction_properties.json` | `lib/openstudio-standards/standards/ashrae_90_1/ashrae_90_1_2019/data/` | U-values (Btu/h·ft²·°F) and SHGC per climate zone and construction type |
| `ashrae_90_1_2019.construction_sets.json` | same directory | Per-archetype assembly-type assignments (wall/roof/floor type per building_type) |
| `DOE_Ref_Pre-1980.construction_properties.json` | `.../DOE_Ref_Pre-1980/data/` | Used for VINTAGE_U_FACTORS derivation only (not stored in bundled table) |
| `DOE_Ref_1980-2004.construction_properties.json` | `.../DOE_Ref_1980-2004/data/` | Used for VINTAGE_U_FACTORS derivation only |
| `ashrae_90_1_2007.construction_properties.json` | `.../ashrae_90_1_2007/data/` | Used for VINTAGE_U_FACTORS derivation only |
| `ashrae_90_1_2010.construction_properties.json` | `.../ashrae_90_1_2010/data/` | Used for VINTAGE_U_FACTORS derivation only |
| `ashrae_90_1_2013.construction_properties.json` | `.../ashrae_90_1_2013/data/` | Used for VINTAGE_U_FACTORS derivation only |
| `ashrae_90_1_2016.construction_properties.json` | `.../ashrae_90_1_2016/data/` | Used for VINTAGE_U_FACTORS derivation only |

### Construction-type assignment per archetype

Assembly types taken from `ashrae_90_1_2019.construction_sets.json` matching each `building_type`.
Window type: `Fixed` (metal framing) for all archetypes with windows;
DataCenter archetypes (SmallDataCenterHighITE, SmallDataCenterLowITE) have no window row in cp tables — confirmed `None` window in cp data.
For archetypes without explicit cs_2019 entries (TallBuilding, SuperTallBuilding,
SmallDataCenterHighITE, SmallDataCenterLowITE, LargeDataCenterHighITE, LargeDataCenterLowITE),
the assignment follows cs_2019 entries at commit 83b1e64.

**Ruling R-2.2-1:** MediumOffice wall assembly = **SteelFramed** (source-true;
cs_2019.json `exterior_wall_standards_construction_type = SteelFramed`).
DESIGN §3C said "Mass" — recorded as DESIGN erratum.
u_wall (CZ1) = 0.124 Btu/h·ft²·°F × 5.678263 = 0.704 W/m²K.

**Ruling R-2.2-2:** Window values from 90.1-2019 CZ1 Fixed Nonresidential:
u_window = 0.5 Btu/h·ft²·°F × 5.678263 = 2.839 W/m²K, SHGC = 0.23.
DESIGN §3C golden 3.69 W/m²K / SHGC 0.25 traced to 90.1-2007 — recorded as DESIGN erratum.

**Ruling R-2.2-3:** Floor assembly = Mass per cs_2019 for MediumOffice.
u_floor (CZ1) = 0.322 Btu/h·ft²·°F × 5.678263 = 1.828 W/m²K.
DESIGN's 1.89 = erratum (traced to SteelFramed floor CZ1 value).

### Infiltration rates

Uniform prototype value: **0.000285 m³/s·m²** of exterior surface area (= 0.0561 cfm/ft²).
Source: PNNL-20405 (2011) "EnergyPlus New Construction Commercial Reference Buildings",
Table B.19 infiltration design flow rate per exterior wall area.
All 29 real archetypes use 0.000285 except DataCenter archetypes which use 0.000126 m³/s·m²
(PNNL data center prototype IDF at commit 83b1e64, `SpaceInfiltration:DesignFlowRate`
per-exterior-area coefficient, representative PNNL small/large data center prototype values).
Infiltration is **vintage-invariant in Phase 1** (DESIGN §11 OQ-1b confirmed resolution).

---

## VINTAGE_U_FACTORS

Median ratio U_edition / U_2019 across Nonresidential construction-properties entries for:
- ExteriorRoof / IEAD
- ExteriorWall / SteelFramed
- ExteriorWall / Mass
- ExteriorWindow / Fixed (metal framing)

at the 16 US climate sub-zones (using sub-zone expansion for edition files that have full
sub-zone notation mapped to parent zones from cp_2019).

| Token | Committed factor | Derivation method | n matched pairs | Notes |
|---|---|---|---|---|
| DOERefPre1980 | **1.6** | Spec-mandated (DESIGN §3C line 63, Technical Pipeline §5) | — | Measured ratio 2.143 (n=64) recorded below as Phase-1.5 calibration evidence per R-2.2-5 |
| DOERef1980to2004 | **1.583** | Median ratio cp_ref_1980_2004 vs cp_2019 | 64 | 16 sub-zones × 4 assembly types |
| 90.1-2007 | **1.309** | Median ratio cp_2007 vs cp_2019 | 32 | 9 parent zones (0-8) × 4 types (some zones share parent) |
| 90.1-2010 | **1.309** | Median ratio cp_2010 vs cp_2019 | 32 | Tie with 90.1-2007 accepted (R-2.2-6, DESIGN line 189 requires non-strict monotonicity) |
| 90.1-2013 | **1.0** | Median ratio cp_2013 vs cp_2019 | 32 | Tie with 90.1-2019 accepted (R-2.2-6) |
| 90.1-2016 | **1.0** | Median ratio cp_2016 vs cp_2019 | 32 | Tie with 90.1-2013 accepted (R-2.2-6) |
| 90.1-2019 | **1.0** | Baseline | — | |

**Monotonicity:** 1.6 ≥ 1.583 ≥ 1.309 ≥ 1.309 ≥ 1.0 ≥ 1.0 ≥ 1.0 — non-increasing per
DESIGN line 189.

**Phase-1.5 calibration evidence (R-2.2-5):**
Measured median ratio DOE-Ref-Pre-1980 / 90.1-2019 = **2.143** (n=64, same assembly types).
DESIGN §3C and ruling R-2.2-5 pin DOERefPre1980 to the spec-sourced value **1.6**.
The 2.143 figure is recorded here for future calibration study (backlog: Step 3 OQ-3 infiltration
bias study companion for U-value bias). Do NOT use 2.143 in any computation.

---

## doe_prototype_loads.json and openstudio_loads.json

**Primary source:** PNNL-20405 (2011), "EnergyPlus New Construction Commercial Reference
Buildings Energy Use Characteristics", Tables B.14–B.16, PNNL-20405, U.S. DOE.
URL: https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-20405.pdf

**Secondary source for extended archetypes:**
NREL/openstudio-standards commit `83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663`,
file `lib/openstudio-standards/standards/ashrae_90_1/ashrae_90_1_2019/data/ashrae_90_1_2019.space_types.json`

Donor mappings:
- `*Detailed` → base office (SmallOffice/MediumOffice/LargeOffice loads)
- `TallBuilding`, `SuperTallBuilding` → LargeOffice loads
- `College`, `Courthouse`, `Laboratory`, `SuperMarket` → spc_2019 primary occupied space type
- DataCenter ITE `equipment_w_m2` → spc_2019 `electric_equipment_per_area` (design_state row 89)

**DataCenter ITE values (bound to NREL prototype, design_state row 89):**
- LargeDataCenterHighITE: 500 W/ft² = 5382 W/m²
- SmallDataCenterHighITE: 100 W/ft² = 1076 W/m²
- LargeDataCenterLowITE: 100 W/ft² = 1076 W/m²
- SmallDataCenterLowITE: 40 W/ft² = 431 W/m²

**Deviation from DESIGN F19 occupant plausibility range:**
DESIGN §3G states `occupant_m2_per_person ∈ [1, 200]` as a plausibility gate.
Warehouse uses 5000 ft²/person = 464 m²/person from PNNL-20405 (very low occupant density
for a storage building). The validate_schema gate uses [1, 500] to accommodate Warehouse.
DESIGN's [1, 200] upper bound is a DESIGN erratum for warehouse-type archetypes; recorded here.

---

## doe_schedules.json

**Source:** PNNL-20405 Table B.5 DOE Commercial Prototype Building schedule sets, digitized.
OpenUBEMUnknown: clone of MediumOffice schedule set under its own key (DESIGN §3F).
Setpoint plateau values bound to T03 scalar columns (DESIGN F16, P6).
Infiltration schedule: inverse-occupancy convention (1.0 = full leakage when unoccupied,
0.25 = reduced during occupied hours when HVAC system pressurizes the building).
