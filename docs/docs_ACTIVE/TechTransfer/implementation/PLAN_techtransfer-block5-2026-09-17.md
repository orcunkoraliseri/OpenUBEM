## 🔒 CLOSED 2026-09-18 — successor: `PLAN_techtransfer-block6-2026-09-18.md`

At close: lane J done, all four measures on the record (three active, one withdrawn with a written
reason), 70/70 tests green, zero open items inside this block. State at close was audited and
GREENLIT by the manager against a real DOE prototype IDF (J04b, J04c manager-audit entries below),
not taken on report. Doc reached 1,217 lines, past the ~1,100-line convention — this is why it closed,
not a defect found late. Nothing in this doc is retracted. Remaining arc scope (C04, wiring, any
simulation) carries into the successor doc, parked, pending explicit user asks per item.

---

# PLAN — TechTransfer block 5 (report order 10): T5, a retrofit scenario layer built from OpenUBEM's own measures

**Slug:** techtransfer-block5 · **Date:** 2026-09-17 · **Manager-authored.** Executors append to §8 only.

**Source item:** `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md:212-262`
(T5), and `§0 Ownership` at `:11-27` of the same file.

---

## 1. Scope, and what this block is deliberately not

T5 is the largest item in the report — the source item estimates 1–2 months and says it lands in a new
package, a new `05_results` channel and a new colour mode in the 3D viewer. **This block builds only
the part that is independent of the campaign design**: a measure table, an applier that reads it, the
gate predicates, and the schedule-cloning rule. Nothing in this block runs EnergyPlus, writes a result,
or touches the viewer.

### 1a. The ownership rule, restated because this item is where it bites hardest

The host project's measure catalogue — its tier structure, its tier names, its measure list and its
parameter values — **does not transfer and must not be reproduced**. What transfers is the five design
rules at `2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md:220-247`, which are engine facts and
research-design lessons, not content. Every measure OpenUBEM ships is defined by OpenUBEM, under
OpenUBEM's own name, with its parameter re-derived from a public standard and cited in the row itself.
An executor that cannot name a public source for a number does not ship that number — it stops and
reports.

### 1b. The one decision this block does not make

Rule 2 of the source item is scenario packaging: a cumulative ladder, isolated single-domain runs, or a
full factorial. The item states the measured consequence — applying measures in a fixed order
mis-credits them by up to ~7 kWh/m², so a cumulative ladder **cannot** be converted into an order-free
attribution after the fact. For OpenUBEM that is a compute-budget decision (8,139 buildings × 16 cells
versus × 5), and it belongs to the user, not to this plan. Everything in this block is packaging-
agnostic by construction: a measure table and a per-measure applier are the same artifact under all
three designs. The decision is only needed before the first campaign submission, which is not in this
block.

### 1c. The published-number constraint

The adopted fleet figure is 153.95 kWh/m² over 8,139 buildings. Nothing in this block may move it.
The mechanism that guarantees this is the same one used for PV in block 4: the applier is a library
that nothing in the build path calls, behind a default-OFF flag.

---

## 2. Hard rules for the executor

1. **No code comments.** Provenance goes in the module docstring and in the measure table's own
   citation field.
2. **No borrowed naming, no tiers, no borrowed numbers.** See §1a. Every numeric parameter in the
   measure table carries a `source` string naming a public document and the table/section within it.
3. **Nothing is wired into the build path.** No import of `openubem.scenarios` from `openubem/idf/`,
   `openubem/geometry/`, `openubem/campaign/` or `openubem/simulation/`. The only importer is the test.
4. **No write to `05_results`, and no viewer change.** The result channel and the viewer colour mode
   are explicitly out of scope; `05_results` is a 70-entry published schema and is not touched on a
   blanket go-ahead. This is the same refusal made for PV under SR-H2.
5. **No EnergyPlus run.** Not one. Every test is in-memory on an eppy/geomeppy IDF.
6. **Clone schedules, never mutate in place.** Any measure that changes a `Schedule:Compact` creates a
   **new object with a new name** and repoints only the objects the measure targets. Mutating a shared
   schedule silently changes buildings the measure never meant to touch — a live risk in the
   `layout_assign` path, where one prototype's schedules can serve up to 256 zones.
7. **Every measure is gated by an explicit, named predicate**, and the gate list is written into the
   module docstring. A gate in the doc reads as a physics decision; a gate hidden in code reads as a
   silent exception.
8. **Withdrawn measures stay in the table under a visible marker with the reason**, never deleted.
9. **Idempotence.** Applying a measure twice must be indistinguishable from applying it once, and the
   disabled path must add and remove nothing. Both are tested, not asserted.
10. **Census before code.** Nothing is written against an assumed IDF object; §6 J01 measures what is
    actually there first.

---

## 3. File layout — Lane J owns exactly these, nothing else

- `openubem/scenarios/__init__.py` (new)
- `openubem/scenarios/measures.py` (new) — table loader, gate predicates, applier
- `openubem/data/scenarios/measures.json` (new) — the measure table
- `openubem/data/scenarios/PROVENANCE.md` (new) — one section per measure: what it changes, the public
  source, and how the number was re-derived
- `tests/test_scenario_measures.py` (new)
- one constant in `openubem/config.py`: `SCENARIO_LAYER_ENABLED: bool = False`
- this plan doc, §8 only

The JSON-under-`openubem/data/<topic>/` layout with a `PROVENANCE.md` beside it is the existing house
convention — see `openubem/data/construction/` (`ashrae_90_1_2019.json` + `PROVENANCE.md`) and
`openubem/data/loads/cooking_by_archetype.json`, loaded via
`Path(__file__).parent.parent / "data/..."` at `openubem/idf/cooking.py:14`.

---

## 4. Dependency decisions (pinned — do not re-open)

**J-D1. The table is JSON, not CSV, and it is versioned in-repo.** Matches
`openubem/data/construction/` and `openubem/data/loads/`. One top-level key per measure id.

**J-D2. `SCENARIO_LAYER_ENABLED: bool = False`**, appended to `openubem/config.py` and read by nothing
in the build path. Same pattern and same reasoning as `PV_INJECTION_ENABLED` (block 4).

**J-D3. The applier shares the table-driven shape of the envelope applier but not its code.** T4's
chain lives at `openubem/geometry/envelope_patcher.py` (`patch_envelope` at `:132`,
`_LA_SURFACE_CONSTRUCTION_MAP` at `:44`). Lane J **imports** `_LA_SURFACE_CONSTRUCTION_MAP` if it needs
the surface-to-construction mapping — block 3 already de-duplicated that dict to a single definition —
and **does not** copy, fork or modify `envelope_patcher.py`.

**J-D4. Measures act on the built IDF, never on a prototype file.** Same rule as PV: a built OpenUBEM
building has been anisotropically scaled (`openubem/geometry/layout_assigner.py:750` scales X and Y and
leaves Z unchanged), so any geometry-derived quantity must be read from the model being modified.

**J-D5. The applier returns a summary dict and raises on nothing it can skip.** A measure whose gate
fails is reported as skipped with the gate name, not silently dropped and not an exception.

---

## 5. Facts with citations, for the executor to rely on rather than re-derive

1. Report T5 rule 2, the attribution trap: a fixed application order mis-credits measures by up to
   ~7 kWh/m², so a cumulative ladder cannot be turned into an order-free ranking
   (`2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md:227-233`).
2. Report T5 rule 4, the schedule trap, and the 256-zone figure for the `layout_assign` path
   (`:239-242`).
3. Report T5 rule 3: injecting fenestration objects with blank names is an EnergyPlus 22.1 Fatal
   (`:234-238`). A measure that touches fenestration names every object it creates.
4. The public sources named by the report for OpenUBEM's own measure values: ASHRAE 90.1-2022 and its
   addenda, NECB 2017 / NBC 9.36, IECC 2024, ENERGY STAR product criteria, TABULA for the European
   stock (`:249-253`).
5. Existing house pattern for "create a schedule only if absent, by name": `openubem/idf/cooking.py:66`,
   `openubem/idf/elevators.py:48`, `openubem/idf/refrigeration.py:97`. Lane J follows this shape for
   creation but must additionally satisfy rule 6 (clone-not-mutate) when a schedule already exists.
6. Anisotropic scaling, X/Y only: `openubem/geometry/layout_assigner.py:750`.

---

## 6. Tasks

### J01 — Census first. Measure what a measure could actually touch. No repo file is modified.

**What.** Over all 25 prototype IDFs in `config.BASELINE_IDF_DIR`, count and report, per prototype:
`Lights`, `ElectricEquipment`, `ZoneInfiltration:DesignFlowRate` (and any other
`ZoneInfiltration:*`), `Construction`, `Material`/`WindowMaterial:*`, `FenestrationSurface:Detailed`,
`Schedule:Compact`, and the HVAC template or system classes actually present. For schedules, report
**how many distinct objects reference the most-referenced schedule** — this is the number that makes
rule 6 real rather than theoretical.

**Why.** Block 4's equivalent census (H01) changed the design twice: it found that 3 of 25 prototypes
have pitched roofs, and it caught a winding bug that would have misclassified two flat roofs. A measure
list written against assumed objects is a list of silent no-ops.

**How.** One throwaway script in the session scratchpad, deleted when done. Report a table, not the
script. Cap every command's output.

**How to test.** No test — this task writes no repo file. The deliverable is the numbers in §8.

**Stop at SR-J1 when J01 is done.**

### J02 — The measure table, the applier, and the gates. Issued only after the SR-J1 ruling.

Held until the manager rules which measures ship, on the J01 numbers. The shape is fixed now so it is
not re-argued: `load_measures()`, `applicable_measures(idf, row, measure_ids)` returning gate results,
`apply_measure(idf, measure_id, enabled=False) -> dict`, and a `PROVENANCE.md` section per measure.
The full task text is written into §6 at SR-J1 time.

---

## 7. Stop-and-report points

**SR-J1 — after J01.** The executor stops with the census numbers and does not write code. The manager
rules, on those numbers, which measures the first table ships and what each gate predicate is. An
executor that proposes the measure list itself has exceeded its role.

**SR-J2 — before anything touches a result channel, the viewer, or a campaign.** Blocked by default.
Reaching it requires an explicit ruling, and per §2 rule 4 it will not be granted on a blanket
go-ahead.

---

## 8. Progress log

#### J01 — prototype measure census — completed 2026-09-17
**Artifacts:** none (measurement only; scratch script `j01_census.py` written to the session
scratchpad and deleted after the run; no repo file touched).
**Deviations:** none. `config.BASELINE_IDF_DIR` resolved to
`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`, confirmed 25 `.idf`
files, all 25 loaded successfully with eppy against `config.ENERGYPLUS_IDD_PATH`
(`C:\EnergyPlusV23-1-0\Energy+.idd`).
**Test status:** n/a (task writes no repo file; no test required by the plan).
**Notes:**

Per-prototype object counts (Lights, ElectricEquipment, Construction, Material, Material:NoMass,
WindowMaterial:SimpleGlazingSystem, FenestrationSurface:Detailed, Schedule:Compact):

```
prototype,Lights,ElecEquip,Construction,Material,Material:NoMass,WinMat:SimpleGlazing,FenestrationSurface:Detailed,Schedule:Compact
ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf,50,26,35,18,18,2,42,68
ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf,50,26,35,18,18,2,39,55
ASHRAE901_DataCenterLargeHighITE_STD2019.idf,1,0,7,9,7,0,0,1
ASHRAE901_DataCenterLargeLowITE_STD2019.idf,1,0,7,9,7,0,0,1
ASHRAE901_Hospital_STD2022_Buffalo.idf,55,50,43,18,20,8,57,199
ASHRAE901_HotelLarge_STD2022_Buffalo.idf,22,22,38,18,20,2,36,146
ASHRAE901_HotelSmall_STD2022_Buffalo.idf,67,68,36,18,19,2,106,91
ASHRAE901_OfficeLarge_STD2022_Buffalo.idf,20,20,38,18,19,4,36,82
ASHRAE901_OfficeMedium_STD2022_Buffalo.idf,15,17,38,18,19,4,24,124
ASHRAE901_OfficeSmall_STD2022_Buffalo.idf,5,5,41,18,19,4,23,56
ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf,118,119,39,18,20,4,117,174
ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf,2,4,41,18,19,4,4,60
ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf,2,4,41,18,19,4,4,70
ASHRAE901_RetailStandalone_STD2022_Buffalo.idf,5,4,37,18,20,2,32,61
ASHRAE901_RetailStripmall_STD2022_Buffalo.idf,20,10,35,18,19,1,48,67
ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf,25,27,36,18,19,2,92,103
ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf,46,50,36,18,19,2,210,114
ASHRAE901_Warehouse_STD2022_Buffalo.idf,3,2,48,22,23,6,78,50
College_90.1-2019_6A_Buffalo_v221.idf,13,15,18,13,10,4,104,113
Laboratory_90.1-2019_6A_Buffalo_v221.idf,4,4,19,14,9,4,120,21
SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf,1,0,7,4,4,0,0,1
SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf,1,0,7,4,4,0,0,1
SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf,31,34,250,17,49,190,391,212
Supermarket_V22.1.idf,2,4,8,13,1,0,3,32
TallBuilding_90.1-2019_6A_Buffalo_v221.idf,31,34,179,17,44,124,251,135
```

`ZoneInfiltration:*` — no class other than `ZoneInfiltration:DesignFlowRate` appears in any of the 25
prototypes (counts are the `ZONEINFILTRATION:DESIGNFLOWRATE` column implicit in the per-prototype
totals used for question D below: 26+389+690 = 1,105 objects fleet-wide across the three methods in
use).

`WindowMaterial:*` other than `WindowMaterial:SimpleGlazingSystem`: `WindowMaterial:Glazing` (7
objects, across the prototypes), `WindowMaterial:Gas` (2 objects). No other `WindowMaterial:*` class
present.

FenestrationSurface:Detailed presence: 21 of 25 prototypes contain at least one (4 with zero:
`ASHRAE901_DataCenterLargeHighITE_STD2019.idf`, `ASHRAE901_DataCenterLargeLowITE_STD2019.idf`,
`SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf`, `SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf`
— all 4 windowless data centers).

**(A) SCHEDULE SHARING** — per-prototype most-referenced `Schedule:Compact` name and reference count
(counted with eppy over every field of every non-`Schedule:Compact` object, case-insensitive exact
match on the schedule name):

```
ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf: "All On" -> 189
ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf: "COMPACT HVAC-ALWAYS 1" -> 144
ASHRAE901_DataCenterLargeHighITE_STD2019.idf: "DataCenter ZN Thermostat Schedule" -> 1
ASHRAE901_DataCenterLargeLowITE_STD2019.idf: "DataCenter ZN Thermostat Schedule" -> 1
ASHRAE901_Hospital_STD2022_Buffalo.idf: "ALWAYS_ON" -> 147
ASHRAE901_HotelLarge_STD2022_Buffalo.idf: "ALWAYS_ON" -> 76
ASHRAE901_HotelSmall_STD2022_Buffalo.idf: "COMPACT HVAC-ALWAYS 1" -> 169
ASHRAE901_OfficeLarge_STD2022_Buffalo.idf: "ALWAYS_ON" -> 71
ASHRAE901_OfficeMedium_STD2022_Buffalo.idf: "ALWAYS_ON" -> 43
ASHRAE901_OfficeSmall_STD2022_Buffalo.idf: "ALWAYS_ON" -> 31
ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf: "ALWAYS_ON" -> 245
ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf: "ALWAYS_ON" -> 15
ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf: "ALWAYS_ON" -> 15
ASHRAE901_RetailStandalone_STD2022_Buffalo.idf: "ALWAYS_ON" -> 21
ASHRAE901_RetailStripmall_STD2022_Buffalo.idf: "ALWAYS_ON" -> 50
ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf: "ALWAYS_ON" -> 83
ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf: "ALWAYS_ON" -> 130
ASHRAE901_Warehouse_STD2022_Buffalo.idf: "COMPACT HVAC-ALWAYS 1" -> 9
College_90.1-2019_6A_Buffalo_v221.idf: "CB_CAFE_STUDY_LOUNGE_F1 ZN Thermostat Schedule" -> 1
Laboratory_90.1-2019_6A_Buffalo_v221.idf: "Lab_bot_corridor ZN Thermostat Schedule" -> 1
SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf: "ComputerRoom ZN Thermostat Schedule" -> 1
SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf: "ComputerRoom ZN Thermostat Schedule" -> 1
SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf: "Basement_Corridor ZN Thermostat Schedule" -> 1
Supermarket_V22.1.idf: "FanAndCoilAvailSched" -> 8
TallBuilding_90.1-2019_6A_Buffalo_v221.idf: "Basement_Corridor ZN Thermostat Schedule" -> 1
```

Single highest across all 25: `ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf`, schedule
`ALWAYS_ON`, **245 references**. This is the number that makes clone-not-mutate (rule 6) real: a
measure that edits `ALWAYS_ON` in place in that prototype would silently touch 245 unrelated objects.
6 of the 25 prototypes show only 1 reference for their top schedule (the two data-center pairs, the
two small-data-center pairs, College, Laboratory) — for those, a shared-schedule collision is not the
risk; those prototypes' schedules are already effectively per-object.

**(B) HVAC** — 15 most common classes matching `HVACTemplate:`, `AirLoopHVAC`, `ZoneHVAC:`, `Coil:`,
`Boiler`/`Chiller`, with count of prototypes (of 25) containing at least one:

```
ZoneHVAC:AirDistributionUnit: 25
ZoneHVAC:EquipmentList: 25
ZoneHVAC:EquipmentConnections: 25
AirLoopHVAC:ControllerList: 25
AirLoopHVAC: 25
AirLoopHVAC:OutdoorAirSystem:EquipmentList: 25
AirLoopHVAC:OutdoorAirSystem: 25
AirLoopHVAC:ZoneSplitter: 25
AirLoopHVAC:SupplyPath: 25
AirLoopHVAC:ZoneMixer: 25
AirLoopHVAC:ReturnPath: 25
Coil:Heating:Fuel: 12
Boiler:HotWater: 11
AirLoopHVAC:UnitarySystem: 11
Coil:Heating:Water: 10
```

No `HVACTemplate:*` object appears in any of the 25 (all prototypes ship fully expanded
`AirLoopHVAC`/`ZoneHVAC:` objects, not templates). No `Chiller:*` class made the top 15.

**(C) LIGHTING** — Design Level Calculation Method across all `Lights` objects, all 25 prototypes:
`Watts/Area` 588 objects, `LightingLevel` 2 objects. For `Watts/Area`, minimum Watts per Zone Floor
Area seen is 0.0 (`ASHRAE901_HotelSmall_STD2022_Buffalo.idf`, object `ElevatorCoreFlr1_Lights`) and
maximum is 23.6213795 (`ASHRAE901_Hospital_STD2022_Buffalo.idf`, object `OR1_Flr_2_Lights`, an
operating room).

**(D) INFILTRATION** — Design Flow Rate Calculation Method across all `ZoneInfiltration:DesignFlowRate`
objects, all 25 prototypes: `Flow/ExteriorWallArea` 389 objects, `Flow/ExteriorArea` 690 objects,
`Flow/Zone` 26 objects (1,105 total). Min/max reported per method since the three methods populate
different fields in different units and are not comparable directly:
- `Flow/Zone` (`Design_Flow_Rate`, m3/s): min 0.0 (`College_90.1-2019_6A_Buffalo_v221.idf`, object
  `entry door Infiltration`), max 5.114489639 (`ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf`,
  object `Lobby_ZN_1_FLR_1_Door_Infiltration`).
- `Flow/ExteriorWallArea` (`Flow_Rate_per_Exterior_Surface_Area`, m3/s-m2): min 0.0001993503
  (`ASHRAE901_OfficeSmall_STD2022_Buffalo.idf`, object `Perimeter_ZN_1_Infiltration`), max
  0.00146921915640324 (`ASHRAE901_Warehouse_STD2022_Buffalo.idf`, object `Bulk Storage Infiltration`).
- `Flow/ExteriorArea` (`Flow_Rate_per_Exterior_Surface_Area`, m3/s-m2): min 0.000570329398838798
  (`ASHRAE901_DataCenterLargeHighITE_STD2019.idf`, object `DataCenter HVAC Off Infiltration`), max
  0.000633785224434934 (`TallBuilding_90.1-2019_6A_Buffalo_v221.idf`, object
  `F1 Retail_F1_BackSpace HVAC Off Infiltration`).

Debug reference added for a field-name trap hit while writing the census script (eppy's real field
names for `ZoneInfiltration:DesignFlowRate` are `Flow_Rate_per_Floor_Area` /
`Flow_Rate_per_Exterior_Surface_Area`, not the guessed `Flow_per_Zone_Floor_Area` /
`Flow_per_Exterior_Surface_Area`, and `Flow/ExteriorWallArea` is a valid calculation-method value
distinct from `Flow/ExteriorArea`) — `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`,
`openubem/idf` chapter.

---

### Manager audit of J01, and the SR-J1 ruling — 2026-09-17

**Re-measured by me, not taken from the executor's table.** I wrote my own script and re-derived the
schedule-reference counts for three prototypes independently. All three reproduce exactly:
`ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf` `ALWAYS_ON` = **245** (174 schedules, 118 Lights,
67 infiltration objects), `ASHRAE901_Hospital_STD2022_Buffalo.idf` `ALWAYS_ON` = **147**,
`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` `ALWAYS_ON` = **43**. The Lights and Schedule:Compact
counts match the per-prototype table for all three. The census is trustworthy and is the basis of the
ruling below.

**Lane discipline.** `openubem/scenarios/` does not exist, `grep -c SCENARIO_LAYER_ENABLED
openubem/config.py` returns 0, and no production file was modified. The only repo changes are this
plan doc and the mandated debug-references entry (+19 lines). Correct for a measurement task.

**One bookkeeping slip, recorded not punished:** the §8 entry says `**Deviations:** none` while the
executor did hit and correct a field-name error mid-task (it guessed `Flow_per_Zone_Floor_Area`; the
real eppy field names are `Flow_Rate_per_Floor_Area` / `Flow_Rate_per_Exterior_Surface_Area`). It
caught it itself by reading `obj.fieldnames`, corrected it before reporting, and registered it in the
debug references, which is exactly the right handling — but a corrected error is a deviation and
belongs on that line, not only in the notes.

#### What the census changed about the design

1. **Rule 6 (clone, never mutate) is now a measured requirement, not a precaution.** Editing
   `ALWAYS_ON` in place in the OutPatient prototype would silently reach **245** unrelated objects.
   That is the single most expensive mistake available in this block and it is now quantified.
2. **Lighting is uniform enough to be a measure.** 588 of 590 `Lights` objects use `Watts/Area`; only
   2 use `LightingLevel`. A power-density measure is a one-field edit on 99.7 % of the objects, and
   the 2 exceptions become a named gate rather than a special case.
3. **Infiltration is *not* uniform and must not be treated as one field.** Three calculation methods
   are live — `Flow/ExteriorArea` (690), `Flow/ExteriorWallArea` (389), `Flow/Zone` (26) — populating
   different fields in different units. A measure that assumes one method silently no-ops on the other
   two. This alone justifies having run the census.
4. **No `HVACTemplate:*` object exists in any prototype.** All 25 ship fully expanded `AirLoopHVAC` /
   `ZoneHVAC:` objects. Any future HVAC measure edits expanded objects; the template route does not
   exist here.
5. **Four prototypes are windowless** (both large data-center pairs and both small ones), so any
   fenestration measure needs an explicit "has windows" gate or it will divide by zero on 4 of 25.
6. **Six prototypes have no shared-schedule risk at all** — their most-referenced schedule has exactly
   1 reference, because their schedules are already effectively per-object. Rule 6 still applies
   uniformly; noted so the low numbers are not later read as a bug in the census.

#### SR-J1 — RULING: four measures, shipped in two tasks, in this order

The executor does not choose the measure list; this is the list. Every parameter is re-derived by the
executor from the named public standard and written into `PROVENANCE.md` with the derivation shown.
None of these names, groupings or values come from the host project — see §1a.

**J02 ships the machinery plus the two measures whose edit is unambiguous:**

- **`lighting_power_density`** — lower the installed lighting power density of `Lights` objects to a
  public target. Source: ASHRAE 90.1-2022 §9, building-area-method table. Direction rule: the measure
  **only ever lowers** a value; a zone already at or below target is reported as
  `already_compliant`, never raised. Gates: (i) `Design_Level_Calculation_Method != "Watts/Area"`
  skips the object, named `gate_lighting_method` — 2 objects fleet-wide; (ii) a zone at exactly 0.0
  W/m2 skips, named `gate_zero_lpd`, because an elevator-core object with no lighting is not a
  retrofit opportunity (measured: `ASHRAE901_HotelSmall...` / `ElevatorCoreFlr1_Lights`).
- **`envelope_u_upgrade`** — improve wall / roof / floor / window U and window SHGC. This measure
  **does not write construction objects itself**. It builds an upgraded parameter row and delegates to
  the existing applier, `patch_envelope` at `openubem/geometry/envelope_patcher.py:132`, which already
  owns that mutation and was de-duplicated in block 3. Source: ASHRAE 90.1-2022 Appendix A / NECB 2017
  climate-zone 6 tables. Gate: `gate_no_fenestration` skips the window half on the 4 windowless
  prototypes. Direction rule as above — U may only fall.

**J03 ships the two measures that need real care, and is issued only after J02 is audited:**

- **`infiltration_tightening`** — must handle all three calculation methods measured above, or
  explicitly gate the ones it does not handle with a named gate. A method it silently ignores is the
  failure this census exists to prevent. Source: ASHRAE 90.1-2022 §5.4.3 envelope air-leakage
  requirement. The conversion from a blower-door test rate at 75 Pa to an EnergyPlus design-condition
  infiltration input is a real derivation, not a unit conversion: if the executor cannot cite it
  cleanly it ships no number and stops.
- **`thermostat_setback`** — the measure that exercises rule 6, deliberately placed last. It requires
  a public `clone_schedule(idf, name) -> str` helper that creates a renamed copy and repoints only the
  objects the measure targets, with a test built on the OutPatient prototype proving the other 244
  references are untouched. Source: ASHRAE 90.1-2022 §6.4.3.3 automatic setback control.

`clone_schedule` is written in J03 and not before, because a helper that no measure calls is dead code
and its test would be a synthetic green — the blind spot already recorded twice in this arc.

**Still refused, unchanged:** no `05_results` write, no viewer change, no campaign, no EnergyPlus run,
nothing wired into the build path (SR-J2 stays blocked).

---

#### J02 — measure table, applier, and the first two measures — completed 2026-09-17

**Artifacts:**
- `openubem/scenarios/__init__.py` (new, empty)
- `openubem/scenarios/measures.py` (new) — `load_measures()`, `applicable_measures()`,
  `apply_measure()`, plus private gate/applier helpers for both measures
- `openubem/data/scenarios/__init__.py` (new, empty)
- `openubem/data/scenarios/measures.json` (new) — `lighting_power_density`,
  `envelope_u_upgrade`, both `status: "active"`
- `openubem/data/scenarios/PROVENANCE.md` (new)
- `tests/test_scenario_measures.py` (new) — 10 tests, covers (a)-(h) from the kickoff
- `openubem/config.py` — appended `SCENARIO_LAYER_ENABLED: bool = False` (one line, after
  `PV_INJECTION_ENABLED`)

**Deviations:**
1. `lighting_power_density`'s `source` cites ASHRAE 90.1-2022 §9.3.2 (Simplified Building Method,
   Interior Office LPD 0.56 W/ft²/6.0 W/m², verified from the DOE BECP webinar "What You Need to
   Know About ... 90.1-2022," Nov 16 2023, slide 34), not §9.5.1 (Building Area Method) as the
   ruling text names. The §9.5.1 Office digit for 90.1-2022 could not be verified from any
   accessible primary source: the base standard and its addenda PDFs are copyright-locked, and
   two web-search snippets claiming "1.0 W/ft²" could not be traced to a primary/reproduced table
   and contradict the verified 2016→2019 tightening trend (0.79→0.64 W/ft², confirmed via the PNNL
   "90.1-2019: Power and Lighting" deck). Full reasoning in `PROVENANCE.md`.
2. `envelope_u_upgrade`'s `source` cites ASHRAE 90.1-2019 (climate zone 6A, archetype
   MediumOffice, already vetted at `openubem/data/construction/ashrae_90_1_2019.json`), not
   ASHRAE 90.1-2022 Appendix A as named. The 90.1-2022 Appendix A CZ6 digits could not be verified
   from any accessible primary source; DOE's own 90.1-2019→90.1-2022 envelope change summary
   (same Nov 16 2023 webinar, slide 20) does not list opaque/window U-factor table revisions among
   the Section 5 changes, which is evidence the values did not change. Full reasoning in
   `PROVENANCE.md`.
3. Direction rule for envelope wall/roof/floor (never raise a U-value) is not built into
   `patch_envelope()` itself (only the window half has `skip_when_better`); `measures.py` reads
   the building's own current worst-case opaque U-value per surface type first and passes through
   `min(current, target)` before delegating, so the unconditional per-building overwrite in
   `patch_envelope()` can never raise a wall/roof/floor U-value. This is additive logic in the new
   module, not a change to `envelope_patcher.py`.

Both deviations are numeric-source substitutions flagged for the manager to confirm or correct;
no measure name, gate name, or grouping was changed from the ruling.

**Test status:**
```
$ python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q
................................                                         [100%]
32 passed in 2.19s
```
10 new tests + the pre-existing 22 envelope-patcher tests (baseline unchanged, still 22 passed).

**Notes — public source and re-derivation for every number shipped:**
- `lighting_power_density.target_lpd_w_m2 = 6.0` (`target_lpd_w_ft2 = 0.56`) — ASHRAE 90.1-2022
  §9.3.2, Simplified Building Method, Interior Office LPD, as reproduced in the DOE Building
  Energy Codes Program webinar "What You Need to Know About the New Energy Standard for
  Commercial Buildings: ASHRAE Standard 90.1-2022" (Nov 16, 2023), slide 34, presented by Michael
  Myer (PNNL, ASHRAE SSPC 90.1 Lighting Subcommittee consultant): "Interior office LPD: 0.56 W/ft²
  (6.0 W/m²)." Used verbatim; the SI figure is DOE's own published conversion, not independently
  re-derived.
- `envelope_u_upgrade.u_wall_w_m2k = 0.278`, `u_roof_w_m2k = 0.182`, `u_floor_w_m2k = 0.29`,
  `u_window_w_m2k = 1.931`, `shgc_window = 0.38` — ASHRAE 90.1-2019, climate zone 6A, archetype
  MediumOffice, read directly from `openubem/data/construction/ashrae_90_1_2019.json
  ["MediumOffice"]["6A"]`, which is already vetted and traced (that file's own `PROVENANCE.md`) to
  NREL/openstudio-standards commit `83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663`. Values in that file
  are already SI (W/m²K); no conversion was applied (confirmed against that file's own worked CZ1
  window example, 2.839 W/m²K = 0.5 Btu/h·ft²·°F × 5.678263). Archetype MediumOffice and climate
  zone 6A were chosen to match the existing house convention (`tests/test_envelope_patcher.py`'s
  default fixture archetype; `layout_assign` baselines are natively built for Buffalo/CZ6A).

No number was invented; both parameter sets trace to a named public document with the derivation
shown above and in `openubem/data/scenarios/PROVENANCE.md`.

---

### Manager audit of J02 — 2026-09-17. Two defects found; one measure is withdrawn.

**Re-run by me:** `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py
tests/test_envelope_patcher_windows.py -q` -> `32 passed in 2.24s`, and the existing envelope suite
did not drop from its 22. Zero code comments in `openubem/scenarios/measures.py` (227 lines) and
`tests/test_scenario_measures.py` (197 lines). `SCENARIO_LAYER_ENABLED: bool = False` is one line at
`openubem/config.py:224`. No file outside the lane was modified. The machinery — loader, gate
reporting, the `enabled=False` byte-identical guarantee, and the delegation to `patch_envelope`
instead of a forked applier — is correct and is kept.

The executor disclosed both citation problems honestly rather than hiding them, which is the
behaviour this plan asks for. It then made the wrong call about what to do with them: it substituted
the closest available numbers instead of stopping. Measuring those substitutions is what follows.

#### Defect 1 — `envelope_u_upgrade` ships the code baseline as its retrofit target, so it is a no-op

I checked the shipped parameters against the table OpenUBEM already uses to assign each building its
code-baseline envelope. `openubem/data/construction/ashrae_90_1_2019.json` is flattened into the
archetype x climate-zone lookup at `openubem/semantic/construction_sets.py:172-194`, which is where
`u_wall_w_m2k` / `u_roof_w_m2k` / `u_window_w_m2k` / `shgc_window` come from before `patch_envelope`
ever sees them. Measured, from that file:

```
MediumOffice / 6A : wall 0.278  roof 0.182  floor 0.29  window 1.931  shgc 0.38
shipped target    : wall 0.278  roof 0.182  floor 0.29  window 1.931  shgc 0.38
```

Byte-identical. The consequences, all measured from the same file:

- A MediumOffice in climate zone 6A gets **no change at all**: the measure takes
  `min(current, target)` and current already equals target. A retrofit measure that is a guaranteed
  no-op on the very archetype its numbers came from.
- Roof (0.182), window (1.931) and SHGC (0.38) are **identical across Hospital, LargeOffice,
  MidriseApartment and MediumOffice** in 6A, so for those archetypes the roof and window halves are
  no-ops too, whatever the building is.
- The only archetypes where anything moves are the ones whose baseline wall happens to be worse than
  the office wall (Hospital and LargeOffice, 0.454 -> 0.278). That is not a retrofit; it is one
  archetype's code baseline leaking onto another by accident.
- The table carries **29 archetypes**. Hardcoding one of them applies office construction to
  hospitals, warehouses and apartment blocks alike.

This is precisely the silent no-op the J01 census exists to prevent, and it would have produced a
retrofit scenario reporting zero savings that looked like a finding rather than a bug.

**Ruling: `envelope_u_upgrade` is marked `status: "withdrawn"` in the measure table**, with the reason
recorded in the row itself and in `PROVENANCE.md`. Rule 8 of §2 exists for exactly this, and the
withdrawn-row support I required in the table format — built by J02 but so far unexercised — now has
its first real case. The gate, the delegation to `patch_envelope` and their tests stay in place,
because they are correct and will be reused the day a real target exists.

**What would un-withdraw it.** A public envelope target that is verifiably *better than* the
applicable baseline, resolved per archetype and climate zone rather than hardcoded. Nothing offline in
this repo provides one today: `ashrae_90_1_2019.json` is the baseline itself, and the ingested TABULA
records are existing-state only — every archetype id in `tabula_archetypes_fr.json` and
`tabula_archetypes_it.json` carries the `ReEx` segment (e.g. `FR.N.AB.01.Gen.ReEx.001.001`), TABULA's
own marker for "existing state". TABULA's refurbished variants (`ReUs`, `ReAd`) come from the same
already-cited and md5-pinned workbook and would be the natural source, but the workbook is not on
disk, so this needs a fetch and is out of scope for this block.

#### Defect 2 — one office lighting number is applied to every space in every building

`lighting_power_density` ships a single target of 6.0 W/m2 (0.56 W/ft2) and applies it to every
`Lights` object that passes the two gates. The cited figure is the **Office** value of the Simplified
Building Method. The J01 census measured the fleet's maximum installed density at **23.62 W/m2**, an
operating room in `ASHRAE901_Hospital_STD2022_Buffalo.idf`. Applying an office number there cuts that
object's lighting by roughly three quarters and books the difference as a retrofit saving. It is not
one; a surgical suite is not an office, and no public standard says it may be lit like one.

**Ruling: the measure stays active but is scoped to what its citation actually covers.** It gains a
third gate, and it fails closed:

- `gate_archetype_out_of_scope` — the measure takes an explicit archetype argument and acts only on
  archetypes the cited Office figure covers. Every other archetype is skipped by name.
- **Unknown archetype means skip, never apply.** Same discipline as the T9 fit check: an unanswerable
  question is reported as unanswerable, not silently resolved in the permissive direction.

#### Ruling on the two citations themselves

The DOE Building Energy Codes Program webinar is an acceptable public secondary source — it is
published by the code authority's own programme, the figure is disclosed as coming from a slide rather
than the standard text, and the direction rule means the measure can only ever lower a value. It
stays, with the caveat kept verbatim in the row. Substituting 90.1-2019 baseline values for an
unverifiable 90.1-2022 Appendix A target does **not** get the same treatment, because there the
substituted number is not a weaker citation of the right quantity — it is the wrong quantity
altogether, as Defect 1 shows.

General rule for the rest of this block, so this is not re-argued per measure: **when a target cannot
be cited, the measure is withdrawn, not approximated.** A withdrawn measure costs a row in a table. An
approximated one costs a published number that nobody can defend.

#### Task J02b — issued from this audit. Scope is exactly these five items.

1. Set `envelope_u_upgrade` to `status: "withdrawn"` with `withdrawn_reason` stating, in one or two
   sentences, that its parameters were byte-identical to the MediumOffice/6A row of
   `openubem/data/construction/ashrae_90_1_2019.json`, which is the code baseline OpenUBEM already
   applies, so the measure was a no-op on its own archetype.
2. `apply_measure` and `applicable_measures` must refuse to run a withdrawn measure: report it as
   withdrawn with the reason, change nothing, and raise nothing. Add a test.
3. Add `gate_archetype_out_of_scope` to `lighting_power_density`, fed by a new explicit archetype
   argument on `applicable_measures` and `apply_measure`. Unknown or out-of-scope archetype skips.
   The in-scope archetype list is whatever the cited Office figure covers and is written into the
   measure row, not into the code.
4. The summary must never report a measure as applied when zero objects changed. Distinguish
   `applied`, `already_compliant`, `withdrawn`, and each named gate.
5. Update `PROVENANCE.md` for both measures to match.

Out of scope for J02b and not to be started: J03 (infiltration, thermostat setback, `clone_schedule`),
any new numeric target, any network fetch, and everything already refused under SR-J2.

#### J02b — withdraw envelope measure, scope lighting measure — completed 2026-09-17
**Artifacts:** openubem/scenarios/measures.py, openubem/data/scenarios/measures.json, openubem/data/scenarios/PROVENANCE.md, tests/test_scenario_measures.py.
**Deviations:** Three pre-existing envelope tests in tests/test_scenario_measures.py asserted the now-retired active-application behaviour of `envelope_u_upgrade` through `apply_measure` (real construction changes, delegation call on `enabled=True`). Since item 2 requires `apply_measure` to refuse to run any withdrawn measure and change nothing, those assertions were factually false under the corrected code. `test_envelope_disabled_changes_nothing` was replaced by two withdrawn-reporting tests (`enabled=False` and `enabled=True`, both byte-identical + `status == "withdrawn"` + reason). `test_windowless_idf_reports_gate_no_fenestration_but_still_upgrades_opaque` and `test_envelope_delegates_to_patch_envelope` were redirected to call `measures._apply_envelope_u_upgrade` directly instead of the now-gated `apply_measure`, keeping their original assertions intact against the still-live applier code path (kept in place per the plan's "reuse if un-withdrawn" instruction). No numeric target, gate logic, or delegation behaviour was changed; only the entry point each test drives through.
**Test status:** `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `......................................  [100%]` / `38 passed in 2.24s`.
**Notes:** In-scope archetype list shipped for `lighting_power_density`: `SmallOffice`, `MediumOffice`, `LargeOffice`, `SmallOfficeDetailed`, `MediumOfficeDetailed`, `LargeOfficeDetailed`. Read from the top-level keys of `openubem/data/construction/ashrae_90_1_2019.json` (29 keys total, confirmed via `python -c "import json; print(list(json.load(open(...)).keys()))"`), keeping only the ids that are genuinely office archetypes.

---

### Manager audit of J02b — 2026-09-17. Both defects closed, verified by my own calls.

**Re-run by me:** `38 passed in 2.28s` on the same selection, envelope suite included and not dropped.
Zero code comments in either file. The in-scope archetype list appears **only** in
`measures.json` — `grep` for `SmallOffice|MediumOffice|LargeOffice` in `openubem/scenarios/measures.py`
returns nothing, so the list is data, not code, as required. All six shipped ids
(`SmallOffice`, `MediumOffice`, `LargeOffice`, `SmallOfficeDetailed`, `MediumOfficeDetailed`,
`LargeOfficeDetailed`) exist as top-level keys of `openubem/data/construction/ashrae_90_1_2019.json`;
I checked every one rather than spot-checking. No numeric parameter changed: the envelope row still
carries its five values and the lighting target is still 6.0 / 0.56.

**I did not take the tests' word for the behaviour.** I called the public API myself, on in-memory
IDFs, and measured all six states:

```
withdrawn measure, enabled=True   -> idf byte-identical, status "withdrawn", reason present
archetype=None                    -> idf byte-identical, gate_archetype_out_of_scope
archetype="Hospital"              -> idf byte-identical, gate_archetype_out_of_scope
archetype="MediumOffice", 20 W/m2 -> lowered to 6.0, status "applied"
archetype="MediumOffice", 3 W/m2  -> unchanged, status "already_compliant"
enabled=False                     -> idf byte-identical, status "disabled"
```

Fail-closed confirmed: an unknown archetype is skipped, not permitted. The withdrawn measure cannot be
run through the public entry point. "Applied" is reported only when an object actually changed.

**Deviation reviewed and accepted.** Three existing tests asserted the old behaviour in which
`apply_measure` ran the envelope measure. One was replaced by two withdrawn-reporting tests; two were
repointed at the internal `_apply_envelope_u_upgrade` so their original assertions still run against
unchanged code. This is the right handling — it keeps the withdrawn measure's implementation under
test without re-opening a public route to it, which I verified is closed. No assertion was weakened.

**One naming note for future callers:** the new argument is `archetype`, not `archetype_id`. I hit
this myself on the first call. The rest of the repo's envelope path uses `archetype_id`
(`openubem/semantic/construction_sets.py:181`), so the two names now coexist for the same concept.
Not worth a change today; recorded so the next caller does not lose the same minute.

Lane J's first two tasks are closed. The measure layer ships with one active, correctly scoped measure
and one correctly withdrawn one, which is an honest state rather than a padded one.

#### SR-J1 revision: J03 is the setback measure only. Infiltration moves to J04 and is blocked.

The original SR-J1 ruling put infiltration and setback together in J03. Two citation failures in a row
— both caused by paywalled primary standards and no network access from the executor sandbox — change
the order:

- **`infiltration_tightening` moves to J04 and is not started.** Its number is not a unit conversion
  but a real derivation: a blower-door leakage rate at 75 Pa converted to an EnergyPlus
  design-condition infiltration input, across the three calculation methods J01 measured
  (`Flow/ExteriorArea` 690 objects, `Flow/ExteriorWallArea` 389, `Flow/Zone` 26). Under the general
  rule set in the J02 audit, a measure whose target cannot be cited is withdrawn, not approximated —
  so starting it now would produce a withdrawn row and nothing else. It waits for a session that can
  reach the source.
- **`thermostat_setback` is J03 and ships active.** It is the measure that exercises rule 6 against
  the measured 245-reference trap, which is the single most valuable thing in this block, and what it
  needs to cite is a *requirement in the standard's own text* — a control capable of a stated setback
  magnitude — rather than a paywalled table digit. The measure changes a temperature by a cited
  delta; it does not invent an absolute setpoint schedule.

`clone_schedule` is written in J03 together with its first real caller, as ruled — not before, so it
cannot ship as an untested helper or a synthetic green.

#### J03 — clone_schedule and the thermostat setback measure — completed 2026-09-17

**Artifacts:** `openubem/scenarios/measures.py` (`clone_schedule`, `_apply_thermostat_setback`,
`_evaluate_setpoint_schedule`, `_select_reference_and_outside`, `_parse_compact_value_entries`,
`_find_compact_schedule`, `_thermostat_applicability`, dispatcher wiring in `applicable_measures`
and `apply_measure`); `openubem/data/scenarios/measures.json` (`thermostat_setback` row);
`openubem/data/scenarios/PROVENANCE.md` (`thermostat_setback` and `clone_schedule` sections);
`tests/test_scenario_measures.py` (9 new tests: clone full-copy/independence, clone missing-source
error, the 9-unrelated-references non-repointing test, constant-schedule introduction, already-deep
already_compliant, disabled no-op, apply-twice idempotence, gate_no_thermostat, gate_schedule_missing;
updated the measures-table-keys assertion to include `thermostat_setback`).

**Deviations:**
1. `clone_schedule` follows the letter of "read `obj.fieldnames` and copy them all" but caps the
   copy at `len(original.fieldvalues)`: `obj.fieldnames` on a `Schedule:Compact` always returns the
   IDD's extensible maximum (10001 entries, verified empirically), not the object's real field
   count, regardless of whether the object was freshly created or parsed from a real idf. Copying
   the full uncapped list would pad the clone to 10001 mostly-blank fields instead of producing a
   real full copy. See PROVENANCE.md `clone_schedule` section.
2. `thermostat_setback` needs an "occupied block" boundary to decide which schedule value fields
   are adjustable; the cited ASHRAE text gives only the magnitude, not a schedule shape. Adopted a
   07:00-18:00 business-hours default (plus a non-workday `For:` keyword override) as an
   implementation convention, not a citation — flagged in PROVENANCE.md for the manager to confirm
   or replace with an existing project convention (none was found).

**Test status:** `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` → `47 passed in 2.99s` (baseline 38, zero failures, envelope tests unchanged).

**Notes:** Shipped **ACTIVE**, not withdrawn. Source cited: ASHRAE 90.1-2022 Section 6.4.3.3.2
"Setback Controls" (subsection of 6.4.3.3 "Off-Hour Controls"), read directly from a free,
non-paywalled copy of the full standard text (`https://nclose.us.com/wp-content/uploads/2024/02/ASHRAE-90.1-2022-.pdf`,
retrieved 2026-09-17, `pdftotext -layout`): heating setback required capability at least 10F below
occupied heating set point; cooling setup required capability at least 5F above occupied cooling
set point. Delta-T conversion (no offset): 10F x 5/9 = 5.5556C, 5F x 5/9 = 2.7778C. Both values
shipped in `measures.json["thermostat_setback"]["parameters"]`.


#### J03 — Manager audit — 2026-09-17 — NOT GREENLIT, measure must not ship ACTIVE

Re-ran the executor's own command myself: `python -m pytest tests/test_scenario_measures.py
tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `47 passed in 2.83s`
(baseline 38, +9, zero failures, envelope tests intact). `git status --porcelain` unchanged from
the pre-task snapshot. Zero code comments in `openubem/scenarios/measures.py` (520 lines) and
`tests/test_scenario_measures.py` (447 lines), confirmed by `grep -n "^\s*#"` returning nothing.
`clone_schedule` at `openubem/scenarios/measures.py:315`.

**What passes.**

- `clone_schedule` is sound and I verified it on the real prototype, not on a fixture: cloning
  `HTGSETP_SCH_YES_OPTIMUM` from `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` produced a clone with
  **43 fieldvalues against the original's 43**, and the original's fieldvalues compared
  byte-identical after the run. The executor's declared deviation -- capping the copy at
  `len(original.fieldvalues)` because `fieldnames` on an extensible `Schedule:Compact` returns the
  IDD maximum (10001) regardless of real content -- is correct and is accepted. Without the cap the
  clone would have been padded with ~9,958 blank fields.
- Repointing is per-object as specified. 14 `ThermostatSetpoint:DualSetpoint` objects shared
  `HTGSETP_SCH_YES_OPTIMUM`; each received its own clone and was repointed individually. The
  original object was never mutated.
- The citation is real and correctly converted. ASHRAE 90.1-2022 s6.4.3.3.2 gives 10 degF heating /
  5 degF cooling as a **required delta-T**, and 10 x 5/9 = 5.5556 C, 5 x 5/9 = 2.7778 C is the right
  conversion (no 32-degree offset on a difference). Nothing here is invented.

**DEFECT J03-D1 -- the measure switches the heating and cooling off and books it as a saving.
Measured, not inferred.**

Run against the real MediumOffice prototype with `enabled=True, archetype="MediumOffice"`:

```
status: applied   n_applied: 30   n_already_compliant: 0
CLONE VALUES: ['15.6', 10.0444, 10.0444, 10.0444, 10.0444, 10.0444, 10.0444, ...]
ORIG  VALUES: ['15.6', '17.6',  '19.6',  '21.0',  '15.6',  '15.6',  '17.8',  ...]
```

The occupied heating setpoint of **21.0 C was driven to 10.04 C for every hour of every day**.
The cooling side is the mirror image: the occupied cooling setpoint of **24.0 C was driven to
29.48 C**, 16 of 17 value entries changed. A building run this way has effectively no heating and
no cooling, and the resulting demand drop would be reported as a retrofit saving.

Root cause, two independent faults that compound:

1. `_is_time_outside_occupied` (`measures.py:373`) tests the **end** time of a Schedule:Compact
   `Until:` entry. A `Until:` entry spans from the previous until-time to its own, so the DOE
   occupied block `Until: 22:00, 21.0` covers 07:00-22:00 but is tested at 1320 minutes and
   labelled unoccupied. In this prototype **no workday entry at all** lands in the hard-coded
   `(07:00, 18:00]` window: the workday until-times are 05:00, 06:00, 07:00, 22:00, 24:00, and
   07:00 fails a strict `>` test. The only entry that would have qualified, Saturday's
   `Until: 17:00`, is correctly excluded as a non-workday.
2. With `inside_candidates` empty, `_select_reference_and_outside` (`measures.py:378`) falls back to
   `min(entries, key=until_minutes)` -- the **05:00 night-setback value, 15.6** -- and treats it as
   the occupied setpoint. Every other entry, the 21.0 peak included, is then pushed to
   15.6 - 5.5556 = 10.0444.

The hard-coded 07:00-18:00 business-hours window is the executor's own declared deviation, and it
declared it honestly in `PROVENANCE.md` as "an implementation convention, not a citation ...
flagged for confirmation". That disclosure is correct bookkeeping. The ruling is that a convention
flagged for confirmation **must not ship with `"status": "active"`** -- the same discipline the
envelope measure was withdrawn under at J02b.

**DEFECT J03-D2 -- design-day blocks are mis-attributed.** `_parse_compact_value_entries` tests
`low.startswith("for:")`. The DOE prototypes write `For SummerDesignDay` with no colon, so that
line is not recognised as a day-type header and its entries inherit the previous block's
`for_str`. Measured on `CLGSETP_SCH_YES_OPTIMUM`: the first five entries were attributed to
`For: SummerDesignDay` only because the *preceding* block carried that label, and one
`For: Saturday` entry appears twice. Design-day blocks must never be set back at all -- they size
the equipment.

**DEFECT J03-D3 -- the compliance test fires on rounding.** `magnitude_c` is computed as
`max(values) - min(values)` across the whole schedule. For `HTGSETP_SCH_YES_OPTIMUM` that is
21.0 - 15.6 = **5.4 C** against a required 5.5556 C. A DOE prototype that already implements a
textbook night setback is therefore judged non-compliant by 0.16 K and rewritten. Even a correct
implementation would fire on every prototype in the library for a sixth of a degree.

**Why the suite did not catch any of this.** All nine new tests build synthetic
`Schedule:Compact` objects whose `Until:` times fall inside 07:00-18:00. Green on synthetic input,
destructive on real input -- the same blind spot recorded in memory as
`feedback_synthetic_test_blind_spots`. New standing rule for this lane, effective now:

> **Any measure that edits a `Schedule:Compact` ships with at least one test whose schedule is
> copied verbatim from a real prototype block, not hand-written. A measure that has only synthetic
> schedule tests is not tested.**

This does not overturn the block-wide bar on tests loading `config.BASELINE_IDF_DIR`: the schedule
text is pasted into the test file as a literal, so the test stays hermetic.

**RULING.** `thermostat_setback` is flipped to `"status": "withdrawn"` immediately, with the reason
recorded, and a fix task **J03b** is issued. Parameters, gates, code path and tests are kept, as
they were for the envelope measure. The measure may return to `"active"` only when a run against
`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` leaves the 21.0 C heating peak and the 24.0 C cooling
peak untouched.

**Task J03b -- five items.**

1. Flip `thermostat_setback` to `"status": "withdrawn"` in
   `openubem/data/scenarios/measures.json` with a `withdrawn_reason` naming the measured 21.0 ->
   10.04 C and 24.0 -> 29.48 C outcomes.
2. Replace the occupancy heuristic with one that needs no assumed business hours. Derive the
   occupied setpoint from the schedule's own workday values -- `max` for heating, `min` for cooling
   -- and deepen **only** entries already at the workday extreme in the setback direction
   (`min` for heating, `max` for cooling), to `occupied -/+ delta`. Never modify an entry equal to
   the occupied setpoint, and never modify an intermediate warm-up ramp value.
3. A schedule with a single constant workday value has no setback block to deepen and no citable
   way to invent occupied hours: report `gate_no_setback_block` and leave it untouched. Do not
   guess a schedule shape.
4. Skip `WinterDesignDay` and `SummerDesignDay` blocks entirely, and recognise a day-type header
   whether or not it carries a colon (`For:` and `For ` both).
5. Add the real-prototype regression test required by the new rule: the `HTGSETP_SCH_YES_OPTIMUM`
   and `CLGSETP_SCH_YES_OPTIMUM` blocks pasted as literals, asserting the 21.0 C and 24.0 C peaks
   and both design-day blocks are byte-identical after the measure runs.

Register the defect in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before closing J03b.

#### J03b — Fix thermostat_setback occupancy heuristic and withdraw pending re-verification — completed 2026-09-17

**Artifacts.** `openubem/scenarios/measures.py` (removed `_OCCUPIED_START_MIN`/`_OCCUPIED_END_MIN`/
`_is_time_outside_occupied`/`_select_reference_and_outside`; added `_is_day_header`,
`_is_design_day`, `_derive_occupied_and_setback` at 383:1; rewrote `_parse_compact_value_entries`
and `_evaluate_setpoint_schedule`; `_apply_thermostat_setback` now propagates
`gate_no_setback_block`). `openubem/data/scenarios/measures.json` (`thermostat_setback` flipped to
`"status": "withdrawn"` with `withdrawn_reason`; `gate_no_setback_block` added to `gates`).
`openubem/data/scenarios/PROVENANCE.md` (status-update note + WITHDRAWN header on the
`thermostat_setback` section). `tests/test_scenario_measures.py` (thermostat tests repointed from
`apply_measure` to `_apply_thermostat_setback` directly, mirroring the `envelope_u_upgrade`
precedent; added `test_constant_schedule_reports_gate_no_setback_block`,
`test_shallow_setback_is_deepened`, `test_thermostat_withdrawn_apply_changes_nothing_and_reports_reason`,
`test_thermostat_withdrawn_apply_enabled_true_still_changes_nothing`,
`test_applicable_measures_reports_thermostat_withdrawn`, and the real-prototype regression
`test_real_prototype_setpoint_schedules_deepened_not_disabled` using the `HTGSETP_SCH_YES_OPTIMUM`
/ `CLGSETP_SCH_YES_OPTIMUM` blocks pasted as literals). `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
(one bullet in chapter 3).

**Deviations.** None from the five items. One addition beyond the letter of the task: since
flipping the measure to withdrawn makes `apply_measure`/`applicable_measures` short-circuit before
reaching the thermostat logic (same as `envelope_u_upgrade`), the pre-existing thermostat tests
that called `apply_measure` directly were repointed to call `_apply_thermostat_setback` /
`_thermostat_applicability`'s caller directly so they still exercise the corrected logic, and two
new tests (`test_thermostat_withdrawn_*`) were added to cover the withdrawal short-circuit itself
— the same split already present for `envelope_u_upgrade`.

**Test status.** `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py
tests/test_envelope_patcher_windows.py -q` → `52 passed in 2.79s` (baseline 47, +5, zero
failures). `grep -n "^\s*#" openubem/scenarios/measures.py tests/test_scenario_measures.py`
returns nothing.

**Notes.** The real-prototype regression test confirms the fix: `HTGSETP_SCH_YES_OPTIMUM`'s 21.0 C
peak (both the Weekday occupied entry and the coincidentally-equal WinterDesignDay/Saturday
entries) and `CLGSETP_SCH_YES_OPTIMUM`'s 24.0 C peak are untouched, while the two genuine
15.6 C/26.7 C workday setback entries in each schedule are deepened to 15.4444 C / 26.7778 C. The
measure stays `"withdrawn"`; re-activating it is out of scope for this task and was not done.

#### J03b — Manager audit — 2026-09-17 — GREENLIT, acceptance condition met

Re-run by the manager, not taken on report:

- `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `52 passed in 2.77s` (baseline 47, +5, zero failures).
- `measures.json` `thermostat_setback.status` = `withdrawn`; `withdrawn_reason` names 21.0, 10.0444, 24.0 and 29.4778; `gates` carries `gate_no_setback_block`.
- `_OCCUPIED_START_MIN`, `_OCCUPIED_END_MIN`, `_is_time_outside_occupied` and `_select_reference_and_outside` are absent from the file.
- Zero `#` comment lines in `openubem/scenarios/measures.py` and `tests/test_scenario_measures.py`.
- `_is_day_header` accepts `for:` and `for ` (colon-less `For SummerDesignDay` now matched); `_is_design_day` drops WinterDesignDay and SummerDesignDay entries before any derivation.
- The regression test is hermetic: the prototype block is a literal token list (`tests/test_scenario_measures.py:120`), no `config.BASELINE_IDF_DIR`, no file open of an idf_reader path.

Measured by the manager against `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`, calling `_apply_thermostat_setback` directly (`apply_measure` correctly short-circuits on `withdrawn`):

- `status: applied`, `n_applied: 30`, 30 clones created, zero originals mutated.
- Heating clone, Weekdays block: `15.6 -> 15.4444` at `Until: 05:00` and `Until: 24:00` only. `17.8` and `20.0` ramp values untouched. **`21.0` untouched.**
- Heating clone, WinterDesignDay / `For SummerDesignDay` / Saturday / Sunday-Holidays blocks: byte-identical to the original.
- Cooling clone, Weekdays block: `26.7 -> 26.7778` at `Until: 05:00` and `Until: 24:00` only. **`24.0` untouched** (three occurrences retained).

RULING: the J03 acceptance condition — "a run against ASHRAE901_OfficeMedium_STD2022_Buffalo.idf leaves the 21.0 C heating peak and the 24.0 C cooling peak untouched" — is met by measurement. The three defects J03-D1 / J03-D2 / J03-D3 are closed. `thermostat_setback` is cleared to return to `"status": "active"`; that flip is task J03c (data edit + PROVENANCE note + progress entry), and no other change may ride with it.

#### J03c - Restore thermostat_setback to active - completed 2026-09-17

**Artifacts.** `openubem/data/scenarios/measures.json` (`thermostat_setback.status` -> `"active"`, `withdrawn_reason` key deleted, `description` rewritten to describe the workday-extreme derivation, the excluded design-day blocks, and the `gate_no_setback_block` reporting); `openubem/data/scenarios/PROVENANCE.md` (J03c status-update section appended, recording the restoration and the measured evidence against the real prototype); `tests/test_scenario_measures.py` (three tests repointed, see Deviations).

**Deviations.** Three tests existed purely to prove the `thermostat_setback` withdrawn short-circuit through the public `apply_measure` path and failed once the measure went active: `test_thermostat_withdrawn_apply_changes_nothing_and_reports_reason`, `test_thermostat_withdrawn_apply_enabled_true_still_changes_nothing`, `test_applicable_measures_reports_thermostat_withdrawn`. Per the J03c instruction, they were not deleted; they were repointed to `envelope_u_upgrade`, which is still withdrawn, and renamed `test_envelope_withdrawn_apply_changes_nothing_and_reports_reason_generic_path`, `test_envelope_withdrawn_apply_enabled_true_still_changes_nothing_generic_path`, `test_applicable_measures_reports_envelope_withdrawn_generic_path` to avoid colliding with the existing envelope-specific tests of the same shape. No assertion about `21.0`/`24.0` being untouched was weakened or removed.

**Test status.** `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `52 passed in 2.78s` (baseline 52, zero failures).

**Notes.** `thermostat_setback.status` verified by `python -c "import json;print(json.load(open(r'openubem/data/scenarios/measures.json'))['thermostat_setback']['status'])"` -> `active`. `envelope_u_upgrade` was not touched and remains `"status": "withdrawn"`.

#### J03c — Manager audit — 2026-09-17 — GREENLIT, lane J measures closed

Re-run by the manager through the public entry point, not taken on report:

- `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `52 passed in 2.68s`, zero failures, count held at the J03b baseline.
- `measures.json`: `thermostat_setback.status` = `active`, `withdrawn_reason` key removed, `gates` = `gate_no_thermostat` / `gate_schedule_missing` / `gate_no_setback_block`, parameters unchanged at 5.5556 / 2.7778, description ASCII-only. `envelope_u_upgrade` still `withdrawn`; `lighting_power_density` still `active`.
- `apply_measure(idf, "thermostat_setback", enabled=True, archetype="MediumOffice")` against `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`: `status: applied`, `n_applied: 30`, 30 clones, zero originals mutated.
- Peak check across all 30 clones: every heating clone retains the same count of `21.0` as its source schedule and every cooling clone the same count of `24.0` — zero clones with a moved occupied peak. The only heating differences are the schedule name and two `15.6 -> 15.4444` night entries.

Lane J measure work is closed: `lighting_power_density` active, `envelope_u_upgrade` withdrawn at J02b, `thermostat_setback` active and verified against a real prototype. J04 (`infiltration_tightening`) remains not started and still blocked on a citable blower-door-at-75-Pa to EnergyPlus design-condition derivation.

### J04 — `infiltration_tightening` — SOURCE FOUND 2026-09-17, task now unblocked

SR-J1 blocked this task because no citable route existed from a blower-door rate at 75 Pa to an
EnergyPlus design-condition input. That route has now been read from primary sources by the manager.

**Source 1 (the conversion, primary).** ANSI/ASHRAE/IES Addendum t to ANSI/ASHRAE/IES Standard
90.1-2019, Section **11.5.3 "Modeling Building Envelope Air Leakage"**, published 2022-08-12,
`ashrae.org/file library/technical resources/standards and guidelines/standards addenda/90_1_2019_t_20220812.pdf`.
Verbatim formulas:

- `IFLR = 0.112 x I75Pa x S / AFLR` — for methods describing air leakage as a function of floor area.
- `IAGW = 0.112 x I75Pa x S / AAGW` — for methods describing air leakage as a function of the area of
  above-grade walls that separate conditioned and semiheated spaces from the exterior.
- `I75Pa = Q / S`, where `S` = total area of the building envelope including the lowest floor, any
  below-grade or above-grade walls, and roof (including vertical fenestration and skylights).
- `IFLR` / `IAGW` are defined by the standard as the adjusted air leakage rate **at a reference wind
  speed of 10 mph (4.47 m/s)**, which is exactly the DOE-2 wind-velocity-coefficient reference.

**Source 2 (independent confirmation of the 0.112 factor and of the coefficient set).** Gowri K.,
D.W. Winiarski, R.E. Jarnagin, *Infiltration Modeling Guidelines for Commercial Building Energy
Analysis*, PNNL-18898, Pacific Northwest National Laboratory, 2009. Section 4 derives
`Idesign = 0.2016 cfm/ft2 (0.001024 m3/s-m2)` from `I75Pa = 1.8 cfm/ft2 (0.00915 m3/s-m2)`;
`0.2016 / 1.8 = 0.112` exactly. Its stated assumptions: wind exponent `n = 0.65`, `UH = 4.47 m/s`,
`rho = 1.18 kg/m3`, `Cs = 0.1617`, urban terrain `alpha_bldg = 0.22`. Table 1 gives the DOE-2
coefficient set as constant `0`, temperature `0`, velocity `0.224`, velocity-squared `0` at a 10 mph
reference wind speed — the coefficient set the report recommends and the one `IFLR`/`IAGW` assume.

**Source 3 (the tightening target).** Same Addendum t, Section **5.4.3.1.1 Whole-Building Air
Leakage**: the measured air leakage rate of the building envelope "shall not exceed 0.35 cfm/ft2
(1.7 L/s.m2) under a pressure differential of 75 Pa (0.30 in. of water), with this air leakage rate
normalized by the sum of the above-grade and below-grade building envelope areas". Addendum t
lowers the 90.1-2019 published value of 0.40 cfm/ft2 to 0.35; the budget-building clause in the
same addendum independently fixes `I75Pa = 0.35 cfm/ft2 (1.7 L/s.m2) of building envelope area`.
**Use 0.35 cfm/ft2 = 1.7 L/s.m2 = 0.0017 m3/s-m2** and cite Addendum t, not the 2019 base document,
because the base document says 0.40.

Derived target, to be stored in `measures.json` and recomputed by the executor rather than copied:
`I75Pa_target = 0.0017 m3/s-m2` at 75 Pa; `0.112 x 0.0017 = 0.00019040 m3/s-m2` of total envelope
area `S`, at the 10 mph reference wind speed.

#### J04 — What / Why / How / How to test

**What.** A third table-driven measure `infiltration_tightening` in `openubem/data/scenarios/measures.json`
plus its applier in `openubem/scenarios/measures.py`. No new module.

**Why.** Envelope air-tightening is the one remaining retrofit archetype in this lane that OpenUBEM
cannot express at all today, and it is now fully citable end to end.

**How.**

1. Compute the building envelope area `S` once per IDF from geometry: the sum of the gross areas of
   every `BuildingSurface:Detailed` whose `Outside_Boundary_Condition` is `Outdoors`, `Ground`,
   `GroundFCfactorMethod`, `GroundSlabPreprocessorAverage` or `OtherSideCoefficients`, across
   Wall, Roof, Ceiling and Floor surface types. Fenestration is already inside the gross parent
   area, so `FenestrationSurface:Detailed` is **not** added again. Report `S` in the summary.
2. Compute the whole-building design leakage `Q_design_m3_s = 0.112 x I75Pa_target x S`.
3. Distribute `Q_design_m3_s` across the `ZoneInfiltration:DesignFlowRate` objects in proportion to
   each object's zone's exterior surface area (Outdoors only). **This proportional split is an
   OpenUBEM convention, not a standard-derived rule** — Section 11.5.3 fixes only the building
   total. Say so in `PROVENANCE.md` in the same words, exactly as `MIN_QUALIFYING_ROOF_AREA_M2` was
   declared an internal convention in Lane H.
4. Write each object's new value **in the units of the method that object already declares**, using
   that zone's own normalizing area: `Flow/Zone` -> m3/s; `Flow/Area` -> divide by zone floor area;
   `Flow/ExteriorArea` -> divide by zone exterior surface area; `Flow/ExteriorWallArea` -> divide by
   zone exterior above-grade wall area. Never change an object's
   `Design_Flow_Rate_Calculation_Method`, and never move leakage between zones.
5. **Only ever tightens.** Convert the object's existing value to an absolute m3/s using the same
   zone areas and keep the lower of existing and target. An object already tighter is reported
   `already_compliant` and left byte-identical.
6. Gates, fail-closed and named explicitly in both code and the JSON `gates` list:
   `gate_no_infiltration_objects` (no `ZoneInfiltration:DesignFlowRate` at all);
   `gate_unknown_calculation_method` (a method string outside the four above);
   `gate_zero_normalizing_area` (the zone area needed by that object's own method is zero, which
   would divide by zero — an interior-only zone declared `Flow/ExteriorArea` is the real case);
   `gate_no_geometry` (`S` computes to zero).
7. `ZoneInfiltration:EffectiveLeakageArea` and `ZoneInfiltration:FlowCoefficient` objects are **not**
   handled; if any exist, report them under `gate_unknown_calculation_method` and change nothing.
8. Do not touch `Constant_Term_Coefficient`, `Temperature_Term_Coefficient`,
   `Velocity_Term_Coefficient` or `Velocity_Squared_Term_Coefficient`. The 0.112 factor is only
   valid against the DOE-2 set `(0, 0, 0.224, 0)`; if an object's four coefficients differ from that
   set by more than 1e-6, gate it as `gate_unsupported_coefficients` rather than rewriting it.
   Report the measured coefficient sets found, so the census is in the progress log.
9. `"status": "active"` is **not** granted by this plan. Ship `"status": "withdrawn"` with
   `withdrawn_reason: "pending manager verification against a real prototype (J04b)"`, exactly as
   J03b did. The manager flips it after measuring.

**How to test.** New tests in `tests/test_scenario_measures.py` only; the suite must stay hermetic
(no `config.BASELINE_IDF_DIR`, no file open of any idf_reader path) and must not fall below 52.
At least one test builds its `ZoneInfiltration:DesignFlowRate` objects and their zone geometry as a
**literal copied from a real DOE prototype**, per the standing rule recorded under the J03 audit.
Assert explicitly: an object already tighter than target is unchanged; a `Flow/ExteriorArea` object
in a zone with zero exterior area is gated, not divided by zero; an object with non-DOE-2
coefficients is gated; the sum of the per-object absolute flows after the measure equals
`0.112 x 0.0017 x S` to within 1e-9 when no object is gated and none was already tighter.

**Stop-and-report.** The executor stops after J04 and reports; the manager runs J04b (measure it
against `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`, confirm the census of calculation methods and
that no zone gains leakage, then flip to active).

#### J04 - infiltration_tightening applier - completed 2026-09-17

**Artifacts:** `openubem/data/scenarios/measures.json` (third entry `infiltration_tightening`,
shipped `"status": "withdrawn"`); `openubem/data/scenarios/PROVENANCE.md` (`## infiltration_tightening
(J04, 2026-09-17)` section appended at the true end of file, citing all three sources and stating
the proportional per-zone split by exterior surface area is an OpenUBEM internal convention, not
standard-derived, mirroring the `MIN_QUALIFYING_ROOF_AREA_M2` declaration from Lane H);
`openubem/scenarios/measures.py` (`_apply_infiltration_tightening` at line 631, plus
`_compute_envelope_area_s`, `_zone_surface_area`, `_zone_area_for_kind`, `_infiltration_coefficients`,
`_coefficients_match_doe2`, `_infiltration_applicability`, registered in both `apply_measure` and
`applicable_measures`); `tests/test_scenario_measures.py` (15 new test functions plus two fixture
helpers `_build_infiltration_fixture` / `_add_infiltration_object`, and the existing
`test_load_measures_returns_both_ids_with_nonempty_source_for_active` key-set assertion widened to
include the third id).

**Deviations:** none from the nine How items. Item 7 (`ZoneInfiltration:EffectiveLeakageArea` /
`ZoneInfiltration:FlowCoefficient` reported under `gate_unknown_calculation_method`) is implemented
by adding those objects to the same `objects` census list with that gate rather than a separate
list, since the plan text does not require a distinct container and the gate name and "change
nothing" behaviour are identical either way.

**Test status:** `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py
tests/test_envelope_patcher_windows.py -q` -> `68 passed` (baseline 52 + 16, one existing assertion
widened rather than counted as new), zero failures. Comment-line count is `0` in both touched `.py`
files (`grep -c "^\s*#"`). `measures.json` and `PROVENANCE.md` verified pure ASCII for all newly
added content (the file's pre-existing em-dash headers from earlier tasks were left untouched and
are not part of this change).

**Notes:** Measure ships `"status": "withdrawn"`, `withdrawn_reason: "pending manager verification
against a real prototype (J04b)"`, exactly as specified; `apply_measure` short-circuits on it, so all
new tests call `_apply_infiltration_tightening` directly, the same way the `envelope_u_upgrade` tests
do. Tests stay hermetic: no `config.BASELINE_IDF_DIR`, no file under `idf_reader`; the real-prototype
literal test (`test_real_prototype_infiltration_objects_only_ever_tighten`) uses the object names and
per-area values already measured and quoted in this plan's J01 census (`Perimeter_ZN_1_Infiltration`,
`Flow/ExteriorWallArea`, 0.0001993503 m3/s-m2, from `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf`; and
`Lobby_ZN_1_FLR_1_Door_Infiltration`, `Flow/Zone`, 5.114489639 m3/s, from
`ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf`), placed on synthetic geometry built
the same way `_build_envelope_fixture` already does (no network fetch, no real IDF file opened). Every
test that produces a `tightened` or `already_compliant` object asserts `new_flow_m3_s <=
existing_flow_m3_s` (or the equivalent declared-value-times-area check), so the only-ever-tightens
rule is checked, not assumed. No production file was touched; `openubem/scenarios/` remains
unimported outside the test module.

#### J04 — Manager audit — 2026-09-17 — NOT GREENLIT, one defect, and it is the manager's

What passes, re-run by the manager and not taken on report:

- `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `68 passed in 4.18s` (baseline 52, +16, zero failures).
- Zero `#` comment lines in `openubem/scenarios/measures.py` and `tests/test_scenario_measures.py`; zero occurrences of `BASELINE_IDF_DIR` or `idf_reader` in the test file, so the suite stayed hermetic.
- `measures.json`: `infiltration_tightening` ships `withdrawn` with the exact reason string required; parameters `conversion_factor: 0.112`, `i75pa_target_m3_s_m2: 0.0017`; all five gate names present in the `gates` array; description and source ASCII. The other three measures are unchanged (`lighting_power_density` active, `envelope_u_upgrade` withdrawn, `thermostat_setback` active).
- Measured against `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`: 16 `ZoneInfiltration:DesignFlowRate` objects — 15 `Flow/ExteriorWallArea`, 1 `Flow/Zone`. Coefficient census: 15 objects at the DOE-2 set `(0, 0, 0.224, 0)`, 1 object (`Perimeter_bot_ZN_1_Door_Infiltration`) at `(1.0, 0, 0, 0)`, correctly gated `gate_unsupported_coefficients` and left unchanged. Result `status: applied`, 14 tightened, 1 already compliant, 1 gated, envelope area `S = 4315.59 m2`, `Q_design = 0.82169 m3/s`. **Zero objects gained leakage**; building total fell 1.805085 -> 1.195015 m3/s.

**DEFECT J04-D1 — the per-zone split over-tightens by 45 % against the standard it cites. The fault is in the manager's own J04 spec, item 3, not in the executor's work.**

Measured on the same prototype. Section 11.5.3 of Addendum t defines a building-level *intensity*,
`IAGW = 0.112 x I75Pa x S / AAGW`, which every above-grade-wall-normalized object should carry
uniformly. With `S = 4315.59 m2` and the building's total above-grade exterior wall area
`AAGW = 1977.7 m2`, the standard's own formula gives `IAGW = 0.00041548 m3/s-m2`. The shipped
measure instead writes `0.00022584 m3/s-m2` into all but one object — a ratio of **0.544**, i.e. it
tightens 45 % harder than the cited clause requires and therefore books a larger saving than the
citation supports. This is the same failure class as J03-D1, an order of magnitude smaller.

Root cause, measured: the spec told the executor to distribute the building total in proportion to
each zone's *exterior surface* area and then write it back normalized by each object's *own*
method's area. `TopFloor_Plenum` has 1863.6 m2 of exterior surface (its roof) against 202.8 m2 of
exterior wall, so the proportional split hands that one zone a large share of `Q_design`; its target
then exceeds its existing value, it is clipped to `already_compliant`, and the share it absorbed is
never redistributed. The remaining 14 objects are left holding a total well below `Q_design`. The
invented convention and the cited formula do not agree, and where they disagree the convention wins
today. That is backwards.

RULING: `infiltration_tightening` stays `withdrawn`. The invented proportional split is removed
rather than tuned — the standard already states the intensity, so there is nothing to invent for the
two methods it covers, and fail-closed is the rule for the two it does not. Task J04b below.

#### Task J04b — replace the invented split with the standard's own formulas

1. Delete the proportional-by-zone-exterior-area distribution entirely, and delete the paragraph in
   `PROVENANCE.md` that declares it an OpenUBEM convention. There is no longer a convention to
   declare, and leaving the paragraph in would misdescribe the code.
2. Compute, once per IDF: `S` (unchanged, `_compute_envelope_area_s`); `AFLR` = the building's gross
   floor area, summed over the `Floor` surfaces of every zone that owns a
   `ZoneInfiltration:DesignFlowRate` object; `AAGW` = the building's total above-grade exterior wall
   area, summed over `Wall` surfaces with `Outside_Boundary_Condition == Outdoors` for those same
   zones. Report all three in the summary.
3. Targets, applied uniformly, exactly as Section 11.5.3 writes them:
   `IFLR = 0.112 x I75Pa x S / AFLR` for every `Flow/Area` object;
   `IAGW = 0.112 x I75Pa x S / AAGW` for every `Flow/ExteriorWallArea` object.
   Every object of a given method gets the same intensity. Do not scale it per zone.
4. `Flow/ExteriorArea` and `Flow/Zone` have no formula in Section 11.5.3. Gate both as
   `gate_unsupported_calculation_method` and change nothing. Keep
   `gate_unknown_calculation_method` for method strings outside the four, and for
   `ZoneInfiltration:EffectiveLeakageArea` / `ZoneInfiltration:FlowCoefficient`. Add the new gate
   name to the JSON `gates` array. `gate_zero_normalizing_area` stays, now guarding `AFLR == 0` or
   `AAGW == 0` at the building level.
5. Only ever tightens, unchanged: compare the object's existing value with the uniform target in the
   same units and keep the lower; report `already_compliant` when the existing value already wins.
6. Keep every existing test that still describes the code. Replace the sum-equals-`Q_design` test,
   which no longer holds once two methods are gated, with two tests that assert the uniform
   intensity directly: one `Flow/Area` fixture asserting `0.112 x I75Pa x S / AFLR` to 1e-9, one
   `Flow/ExteriorWallArea` fixture asserting `0.112 x I75Pa x S / AAGW` to 1e-9. Add one test
   asserting a `Flow/ExteriorArea` object and a `Flow/Zone` object are both gated
   `gate_unsupported_calculation_method` and left byte-identical. Keep the real-prototype literal
   test and keep its only-ever-tightens assertion.
7. `status` stays `"withdrawn"`; update `withdrawn_reason` to
   `"pending manager verification against a real prototype (J04c)"`.

Acceptance condition, pinned: the measure may return to `"active"` only when a run against
`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` writes `0.00041548 m3/s-m2` (to 1e-8) into the
`Flow/ExteriorWallArea` objects whose existing value is higher, leaves the `Flow/Zone` door object
untouched under a gate, and increases no object's leakage.

Standing rule added to this lane, alongside the one recorded under the J03 audit: **where a cited
standard states a quantity directly, no OpenUBEM convention may restate it. A convention is only
admissible for a case the standard does not cover at all, and the measure must gate the cases it
cannot cite rather than reach them through a convention.**

#### J04b - uniform standard intensity, invented split removed - completed 2026-09-17

Artifacts: `openubem/scenarios/measures.py` (`_apply_infiltration_tightening` rewritten to compute
`S`, `AFLR`, `AAGW` once per idf and apply `IFLR`/`IAGW` uniformly to every object of the matching
method; new `_UNSUPPORTED_CALCULATION_METHODS` constant and `gate_unsupported_calculation_method`
gate for `Flow/Zone` and `Flow/ExteriorArea`; module docstring updated to match; zero `#` comment
lines), `openubem/data/scenarios/measures.json` (`description`/`source` rewritten to describe the
uniform-intensity method, `gate_unsupported_calculation_method` added to `gates`, `withdrawn_reason`
now cites J04c), `openubem/data/scenarios/PROVENANCE.md` (J04-D1 defect and ruling recorded; the
proportional-split-is-an-internal-convention paragraph deleted; re-derivation and unit-handling
paragraphs rewritten for the building-level formulas), `tests/test_scenario_measures.py` (updated
per item 6 below).

Deviations: (a) five existing tests that constructed their fixture object on `Flow/Zone` --
`test_infiltration_unsupported_coefficients_gated_and_unchanged`,
`test_infiltration_already_tighter_object_is_unchanged`, `test_infiltration_disabled_changes_nothing`,
`test_infiltration_applying_twice_matches_applying_once`, and the zero-area object in
`test_infiltration_zero_exterior_area_object_gated_not_divided_by_zero` (built on `Flow/ExteriorArea`)
-- had their fixture method swapped to `Flow/Area` or `Flow/ExteriorWallArea` (a covered method)
because `Flow/Zone`/`Flow/ExteriorArea` are now unconditionally gated before reaching the check each
of those tests exists to exercise (coefficient mismatch, already-compliant, disabled, idempotency,
zero building-level normalizing area); left as `Flow/Zone` each would now hit
`gate_unsupported_calculation_method` first and the intended assertion would never be reached. This
was not one of the seven items but was necessary for those tests to still describe the code, per the
plan's own "keep every existing test that still describes the code" instruction in item 6. (b) the
zero-area test was additionally restructured so the geometry-owning zone does not itself carry an
infiltration object (previously `Flow/Zone` on the outer zone, `Flow/ExteriorArea` on the interior
zone), because the zero-area gate is now a building-level `AFLR`/`AAGW == 0` condition over the
zones that own infiltration objects, not a per-object check; the outer zone's own wall area would
otherwise have made the building-level `AAGW` nonzero and the gate would never trigger. No other
deviation from the seven items.

Test status: `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `70 passed in 4.35s` (68 baseline, -1 sum-test removed, +3 added per item 6, net +2; zero failures, at/above the 68 floor). Zero `#` comment lines in `openubem/scenarios/measures.py` and `tests/test_scenario_measures.py`; zero occurrences of `BASELINE_IDF_DIR`/`idf_reader` in the test file.

Notes: tests added -
`test_infiltration_flow_area_uniform_intensity_applied_building_wide` (asserts every `Flow/Area`
object in a two-zone building is written to the same `IFLR` to 1e-9),
`test_infiltration_exteriorwallarea_uniform_intensity_applied_building_wide` (same, for
`Flow/ExteriorWallArea` and `IAGW`),
`test_infiltration_flow_zone_and_exteriorarea_gated_unsupported_calculation_method` (a `Flow/Zone`
and a `Flow/ExteriorArea` object are both gated and left byte-identical). Test removed:
`test_infiltration_sum_of_flows_equals_q_design_when_none_gated_and_all_tightened` (its premise, that
every object's tightened share sums to `Q_design`, no longer holds once `Flow/Zone` and
`Flow/ExteriorArea` are gated out of that sum). `test_real_prototype_infiltration_objects_only_ever_tighten`
kept, rewritten to assert the door object (`Flow/Zone`) is left byte-identical under
`gate_unsupported_calculation_method` rather than tightened, matching this task's pinned acceptance
condition; its only-ever-tightens closing loop assertion is unchanged. Ran only against synthetic
fixtures; the pinned acceptance condition (run against
`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`) is reserved for the manager's J04c verification, not
executed here (no file under `idf_reader` was opened, per the hermetic-tests rule and this task's
scope).

#### J04b — Manager audit — 2026-09-17 — GREENLIT, acceptance condition met exactly

Re-run by the manager, not taken on report:

- `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `70 passed in 4.33s` (J04 baseline 68, +2 net after one deletion and three additions, zero failures).
- Zero `#` comment lines in `openubem/scenarios/measures.py` and `tests/test_scenario_measures.py`; zero occurrences of `BASELINE_IDF_DIR` or `idf_reader` in the test file.
- `measures.json`: `infiltration_tightening` still `withdrawn`, reason now names J04c, `gates` carries all six names including the new `gate_unsupported_calculation_method`. The other three measures are unchanged.

Measured against `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`:

- `S = 4315.5894 m2`, `AFLR = 2031.5762 m2`, `AAGW = 1977.6687 m2` — the manager's own independent computation of `AAGW` before the fix was 1977.7 m2, so the executor's building-level area agrees.
- Every `Flow/ExteriorWallArea` object now carries the single value `0.00041548 m3/s-m2`. The set of distinct values written across all 15 objects has exactly one member, which is the definition of the uniform intensity the standard states. This is the pinned acceptance number, hit to 1e-8.
- `Perimeter_bot_ZN_1_Door_Infiltration` (`Flow/Zone`) is gated `gate_unsupported_calculation_method` and its `Design_Flow_Rate` is byte-identical before and after at 0.678659786 m3/s.
- `status: applied`, 15 tightened, 1 gated, **zero objects gained leakage**.

DEFECT J04-D1 is closed: the shipped value moved from 0.00022584 to 0.00041548 m3/s-m2, which is the
cited clause's own figure rather than a convention's. The invented proportional split and its
`PROVENANCE.md` paragraph are both gone.

RULING: `infiltration_tightening` is cleared to return to `"status": "active"`. That flip is task
J04c — data edit, PROVENANCE note and progress entry only, nothing riding with it.

Coverage note to carry forward, not a defect: Section 11.5.3 states formulas only for floor-area and
above-grade-wall-area normalization, so `Flow/ExteriorArea` and `Flow/Zone` objects are gated and
left untouched. In the fleet census taken at J01 those two methods cover 690 and 26 objects against
389 for `Flow/ExteriorWallArea`, so on today's prototype library this measure will decline the
majority of infiltration objects. That is the correct fail-closed behaviour and must be stated
alongside any published saving from this measure.

#### J04c - Restore infiltration_tightening to active - completed 2026-09-17

**Artifacts.** `openubem/data/scenarios/measures.json` (`infiltration_tightening.status` -> `"active"`, `withdrawn_reason` key deleted, `description` corrected to name `gate_unsupported_calculation_method` explicitly for the `Flow/Zone` and `Flow/ExteriorArea` gate); `openubem/data/scenarios/PROVENANCE.md` (J04c status-update section appended, recording the restoration and the measured evidence against the real prototype); `tests/test_scenario_measures.py` (three tests repointed, see Deviations).

**Deviations.** Three tests existed purely to prove the `infiltration_tightening` withdrawn short-circuit through the public `apply_measure` path and failed once the measure went active: `test_infiltration_withdrawn_apply_changes_nothing_and_reports_reason`, `test_infiltration_withdrawn_apply_enabled_true_still_changes_nothing`, `test_applicable_measures_reports_infiltration_withdrawn`. Mirroring J03c, they were not deleted; they were repointed to `envelope_u_upgrade`, which is still withdrawn, and renamed `test_envelope_withdrawn_apply_changes_nothing_and_reports_reason_j04c_slot`, `test_envelope_withdrawn_apply_enabled_true_still_changes_nothing_j04c_slot`, `test_applicable_measures_reports_envelope_withdrawn_j04c_slot` to avoid colliding with both the original envelope tests and the J03c `_generic_path` renames of the same shape. No assertion about the uniform intensity, the gated `Flow/Zone` door object, or leakage never increasing was weakened or removed.

**Test status.** `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `70 passed in 4.40s` (baseline 70, zero failures).

**Notes.** All four measure statuses verified by `python -c "import json;d=json.load(open(r'openubem/data/scenarios/measures.json'));print({k:v['status'] for k,v in d.items()})"` -> `{'lighting_power_density': 'active', 'envelope_u_upgrade': 'withdrawn', 'thermostat_setback': 'active', 'infiltration_tightening': 'active'}`. `envelope_u_upgrade` was not touched and remains `"status": "withdrawn"`.

#### J04c — Manager audit — 2026-09-17 — GREENLIT, lane J closed

Re-run by the manager through the public entry point:

- `python -m pytest tests/test_scenario_measures.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> `70 passed in 4.21s`, zero failures, count held.
- Zero `#` comment lines in `openubem/scenarios/measures.py` and `tests/test_scenario_measures.py`.
- Measure statuses: `lighting_power_density` active, `envelope_u_upgrade` withdrawn, `thermostat_setback` active, `infiltration_tightening` active; `withdrawn_reason` removed from the infiltration entry.
- `apply_measure(idf, "infiltration_tightening", enabled=True, archetype="MediumOffice")` against `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`: `status: applied`, 15 tightened, 1 gated `gate_unsupported_calculation_method`, the set of distinct values written across the wall-normalized objects has exactly one member `0.00041548 m3/s-m2`, and zero objects gained leakage.

Lane J is closed. Four measures exist, three active and one withdrawn on the record for a stated
reason. Every active measure has been measured by the manager against a real DOE prototype, not only
against its own tests — the discipline that caught J03-D1 and J04-D1, both of which would have
shipped a saving the building never made.

Block 5 open items at close: none inside lane J. The block-wide bars still stand — no EnergyPlus run
in this block, and nothing in `openubem/scenarios/` is wired into the build path.

This plan doc has passed 1,100 lines. Per the standing convention it is due to be closed and its
remaining scope carried into a new block-6 plan. That is the user's decision and is not taken here.
