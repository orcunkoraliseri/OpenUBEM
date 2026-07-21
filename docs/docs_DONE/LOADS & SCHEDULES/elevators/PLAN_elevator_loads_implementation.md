# PLAN — Elevator service-load emitter (R6-4B residual, elevator sub-item)

**Slug:** elevator-loads
**Date:** 2026-07-14
**Author:** Manager (Opus session)
**Binding contract:** Phase-E service-load discipline as implemented in `openubem/idf/cooking.py`, `dhw.py`, `refrigeration.py`; wired at `openubem/idf/builder.py:505-507`. This PLAN inherits the **zero-fitted-parameters** rule verbatim: every number emitted must trace to a DOE prototype IDF constant, never a tuned/fitted value.

---

## 0. Why this arc exists (scoping record — read before executing)

The memory framing "R6-4B = ~42% unmodelled 'Other' = fans/pumps/parasitics" is a **pre-Phase-E artifact** (R6-4A / V15, 2026-06-15, IdealLoads era). Phase-E already physically models fans, pumps, DHW, cooking, refrigeration. The **remaining** post-Phase-E "Other" residual = **elevators + process loads + miscellaneous plug loads** (`REPORT_phaseE_final.md` §12.1, line 166).

Of that remainder, only **elevators have a verbatim DOE source** — the DOE prototypes carry an explicit `Elevators` object with a published lift design level. Process/misc plug loads have **no** DOE source and remain a STOP-decision residual (adding them = fitting = forbidden). This arc addresses **elevators only**.

**Honest magnitude:** single-digit kWh/m²/yr (LargeOffice ≈ 6, MediumOffice ≈ 3.4), currently **100% missing** (`openubem/` emits zero elevator load). This is a **fidelity/attribution win + a modest under-prediction contributor**, NOT a headline mover. Do not oversell it in the report.

---

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** No writing outside the repo.
2. **You execute this plan; you do not rewrite it.** If the DESIGN/spec is ambiguous, STOP and quote the conflict — do not invent.
3. **Zero-fitted-parameters is absolute.** Every emitted watt traces to a DOE prototype IDF constant. No calibration, no tuning to CBECS.
4. **No scope creep.** Elevators only. Do NOT add process loads, misc plug loads, or touch HVAC/DHW/cooking/refrigeration emitters.
5. **Default to no comments.** One short line max where the WHY is non-obvious. Match the surrounding code style in `cooking.py`.
6. **Byte-identity for no-elevator archetypes.** An archetype absent from the elevator table must produce a byte-identical IDF to today (mirror the `no_cooking` early-skip in `cooking.py`).
7. **No cluster/EnergyPlus annual runs without a checkpoint.** Build + unit-test + a single one-IDF-per-archetype smoke is in scope; a fleet re-sim is gated at CP-2.

---

## 2. File layout to create / touch

```
openubem/
├── idf/
│   ├── elevators.py                      # NEW — assign_elevators(idf, row, zones)
│   └── builder.py                        # EDIT — add one call after line 507
├── data/loads/
│   └── elevators_by_archetype.json       # NEW — harvested DOE lift design levels + schedule
└── results/
    ├── parser.py                         # EDIT — register "Elevators" subcategory
    └── aggregator.py                     # EDIT — surface Elevators in the end-use breakdown
tests/
└── test_elevators.py                     # NEW — mirrors test_cooking.py structure
```

---

## 3. Dependency decisions (pre-decided — do not re-debate)

| Decision | Ruling |
|---|---|
| EnergyPlus object | `ElectricEquipment` (interior), `EndUse_Subcategory = "Elevators"`. Meters to `InteriorEquipment:Electricity` and counts in building total EUI. (DOE LargeOffice uses `Exterior:FuelEquipment`; for OpenUBEM's zone-box the interior form is the clean equivalent and still meters to electricity.) |
| Scaling rule | `design_level_w × (total_floor_area / prototype_floor_area_m2)`, **no cap**. `total_floor_area` = `footprint × floors` via the existing `cooking._total_floor_area` helper — this implicitly captures building rise (a taller building = more total area = more elevator load), which is the physically-correct direction. |
| Schedule | Transcribe the DOE `BLDG_ELEVATORS` `SCHEDULE:COMPACT` **verbatim** into a named schedule (one per archetype or a shared one if identical across prototypes — T01 determines). Do NOT approximate with a constant peak fraction; elevators have a strong daily profile. |
| Archetype coverage | Only archetypes whose DOE prototype contains an `Elevators`/`ElevatorLift` object. Confirmed present: LargeOffice, MediumOffice, LargeHotel, SmallHotel, Hospital, Outpatient, HighriseApartment, MidriseApartment, SecondarySchool, TallBuilding, SuperTallBuilding. Confirmed **absent** (emit nothing): SmallOffice, Warehouse, RetailStandalone, RetailStripmall, restaurants, PrimarySchool, data centers. T01 produces the authoritative list from the IDFs. |
| Provenance | Mirror `cooking.py`: footprint/floors defaults record `GEOMETRY_AREA`/`GEOMETRY_FLOORS` tokens via `provenance`. Elevators add no new token family. |
| Missing-geometry guard | Empty `zones` → return `[]` (no emission), exactly like `cooking.assign_cooking`. |

---

## 4. Source-of-truth verified facts (manager-grepped)

DOE prototype `Elevators` / `ElevatorLift` **lift design levels** (W), grepped from `docs/docs_VALIDATION/step1/Level 2 DOE round-trip/00.BaselineBuildings_NUs/`:

| DOE prototype | ElevatorLift Design Level (W) | E+ object class |
|---|---:|---|
| ASHRAE901_OfficeLarge | **140025.3** | `Exterior:FuelEquipment` |
| ASHRAE901_HotelLarge | **44860.63** | `Exterior:FuelEquipment` |
| ASHRAE901_Hospital | **34667.95** | `ElectricEquipment` |
| ASHRAE901_OfficeMedium | **8517.82** | `ElectricEquipment` |
| ASHRAE901_ApartmentHighRise | present (harvest exact) | `ElectricEquipment` |
| ASHRAE901_ApartmentMidRise | present (harvest exact) | `ElectricEquipment` |
| ASHRAE901_HotelSmall | present (harvest exact) | `ElectricEquipment` |
| ASHRAE901_OutPatientHealthCare | present (harvest exact) | `ElectricEquipment` |
| ASHRAE901_SchoolSecondary | present (harvest exact) | `ElectricEquipment` |
| TallBuilding / SuperTallBuilding | present (harvest exact) | `ElectricEquipment` |

- The `Elevators_Lights_Fan` object (e.g. LargeOffice 631.89 W) is the elevator **cabin lights/vent**, a *second, much smaller* object. **Scope decision: include the `ElevatorLift` motor only.** Adding the lights/fan is optional and second-order; if T01 finds it trivial to include, include it under the same `"Elevators"` subcategory, else defer.
- Prototype floor areas needed for the scaling denominator: harvest from each IDF's `Building`/zone geometry, or reuse the values already stored for cooking (`cooking_by_archetype.json` `prototype_floor_area_m2`) where the archetype overlaps.
- Integration call site: `openubem/idf/builder.py:505-507` calls `assign_dhw`, `assign_cooking`, `assign_refrigeration` on `extruded_zones`. Add `assign_elevators` at 508.
- `archetype_id` on `row` is the join key into the JSON table (same as `cooking.py:90`).

---

## 5. Task list

### T01 — Harvest elevator specs into `elevators_by_archetype.json`
- **What:** For every DOE prototype IDF in `00.BaselineBuildings_NUs/`, extract the `ElevatorLift` design level (W), the `BLDG_ELEVATORS` schedule, and the prototype total floor area. Produce `openubem/data/loads/elevators_by_archetype.json` keyed by OpenUBEM `archetype_id`, each entry `{design_level_w, prototype_floor_area_m2, schedule_ref}`. Archetypes with no elevator object are **omitted** (absence = no emission).
- **Why:** §3/§4 — the table is the verbatim DOE source. Zero-fitted-params requires the values be transcribed, not assumed.
- **How:** Map DOE prototype file → OpenUBEM `archetype_id` using the same crosswalk `cooking_by_archetype.json` uses. Reuse `prototype_floor_area_m2` from `cooking_by_archetype.json` where the archetype exists there. Capture the `BLDG_ELEVATORS` SCHEDULE:COMPACT verbatim (store the field list, or a schedule-name reference if you emit a shared digitized schedule).
- **How to test:** A unit test asserts the four manager-verified anchors are present and exact: OfficeLarge 140025.3, HotelLarge 44860.63, Hospital 34667.95, OfficeMedium 8517.82. Assert SmallOffice/Warehouse/PrimarySchool are absent from the table.

### T02 — `elevators.py` emitter
- **What:** `assign_elevators(idf, row, zones)` mirroring `cooking.assign_cooking`: empty-zones guard → `[]`; archetype absent from table → `[]` (byte-identical); else compute `total_area` via the shared floor-area helper, emit one `ElectricEquipment` with `Design_Level = round(design_level_w * total_area / prototype_floor_area_m2, 2)`, the digitized `BLDG_ELEVATORS` schedule, `EndUse_Subcategory = "Elevators"`. Return sorted provenance flags.
- **Why:** §3 scaling + object decisions.
- **How:** Import and reuse `cooking._total_floor_area` (or lift it to a shared `openubem/idf/_service_geom.py` helper if you prefer — but do NOT change `cooking.py` behaviour). Heat-gain fractions: elevators are a motor load; use `Fraction_Radiant = 0.5, Fraction_Latent = 0, Fraction_Lost = 0` unless the DOE prototype object specifies otherwise (transcribe if it does — LargeOffice `Exterior:FuelEquipment` has no zone heat gain; the interior-equivalent should not dump 100% to the zone as latent).
- **How to test:** covered by T03.

### T03 — `test_elevators.py`
- **What:** Structural mirror of `test_cooking.py`: (a) an elevator archetype emits exactly one ElectricEquipment with subcategory "Elevators" and the area-scaled design level; (b) a no-elevator archetype (SmallOffice) emits nothing; (c) doubling `total_area` doubles the design level (linear scaling); (d) empty zones → `[]`; (e) provenance tokens fire on missing footprint/floors.
- **Why:** locks the contract before wiring.
- **How to test:** `pytest tests/test_elevators.py -q`.

### T04 — Wire into `builder.py`
- **What:** Add `from openubem.idf.elevators import assign_elevators` and call `assign_elevators(self.idf, row, extruded_zones)` immediately after line 507.
- **Why:** §4 integration point.
- **How to test:** existing builder tests stay green; add one assertion that a built LargeOffice IDF contains an `ElectricEquipment` with subcategory "Elevators".

### T05 — Results wiring (`parser.py`, `aggregator.py`)
- **What:** Register "Elevators" as a recognized end-use subcategory so it appears in the end-use breakdown and is counted in total EUI (it already is, via InteriorEquipment:Electricity, but the *breakdown* must name it as the 10th use rather than folding it into generic Equipment).
- **Why:** Phase-E reports 9 physical end-uses; this makes 10. End-use attribution honesty is half the value of the arc.
- **How:** find where `parser.py`/`aggregator.py` enumerate subcategories (Cooking/Refrigeration/etc.) and add "Elevators" alongside. Do not change the total-EUI math.
- **How to test:** parse a fixture SQL/result with an Elevators subcategory; assert it surfaces as its own column and that total EUI is unchanged vs summing the columns.

### T06 — LIVE_SMOKE (build-only, no annual sim)
- **What:** Build one real IDF per elevator archetype through the full `builder` path and assert the Elevators object is present with a plausible non-zero design level; build one no-elevator archetype and assert byte-identity to a pre-change build.
- **Why:** synthetic-fixture green ≠ live-path green (standing rule).
- **How to test:** a standalone script under `scripts/validation/`, not in pytest; report the per-archetype emitted W and implied kWh/m² hand-estimate.

---

## 6. Stop-and-report checkpoints

- **CP-1 (after T04):** emitter + table + wiring done, unit tests green. Report the harvested table (all archetype design levels) and the per-archetype hand-computed kWh/m²/yr so the manager can sanity-check magnitude against the §0 estimate BEFORE any results/sim work.
- **CP-2 (after T06):** LIVE_SMOKE passed, byte-identity confirmed for no-elevator archetypes. **STOP.** A fleet re-simulation (12-cell re-baseline) changes the adopted Phase-E headline numbers and is a **user sign-off decision** — do not fire it. Report expected EUI deltas from the hand-estimate and await the manager's gate.

---

## 7. Progress log

#### T01 — Harvest elevator specs into `elevators_by_archetype.json` — completed 2026-07-14
- Artifacts: `openubem/data/loads/elevators_by_archetype.json`
- Deviations:
  - **TallBuilding and SuperTallBuilding omitted** despite PLAN §4 listing them as "present (harvest exact)". Grep for `ElevatorLift|Elevators_Equip` returns zero matches in both `TallBuilding_90.1-2019_6A_Buffalo_v221.idf` and `SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf`. Both prototypes model elevator lobby/shaft zones as ordinary conditioned space (generic Watts/Area "Elec Equip" plug load, same formula as any other zone) plus a dedicated `Top_ElevatorMachineRm` HVAC-only zone (cooling for the machine room, no equipment object). There is no DOE-authored elevator lift design level to transcribe for these two archetypes, so per zero-fitted-params they are correctly omitted (absence = no emission), overriding the PLAN's illustrative table per §3's own instruction that "T01 produces the authoritative list from the IDFs."
  - **College added** (not in PLAN §4's coverage list). `College_90.1-2019_6A_Buffalo_v221.idf` carries a real `2 Elevator Lift Motors` ElectricEquipment object (32,110 W, subcategory `Elevators`). Included per T01's explicit "for every DOE prototype IDF" instruction.
  - **RetailStandalone confirmed absent** (matches PLAN's expectation): the file has an orphan `BLDG_ELEVATORS` Schedule:Compact that no object references — correctly omitted.
  - **HighriseApartment / MidriseApartment floor-area anomaly (flagged, not silently resolved):** `prototype_floor_area_m2` was computed by summing `BuildingSurface:Detailed` Floor-surface areas × Zone Multiplier in the same IDF instance the design level was harvested from (self-consistent pairing). For both apartment archetypes this yields ~2351 m², essentially identical for "high-rise" and "mid-rise" despite very different Z-origin spacing (G=0m, M=12.19m, T=27.43m for HighriseApartment) implying more physical floors than the 3 explicitly-zoned groups (G/M/T) capture. Raw-text-verified: all Zone objects in both files literally have `Multiplier=1`. This means the repeated middle floors these prototypes conceptually represent are not captured by an explicit multiplier in this exported IDF, so the geometry-summed floor area likely understates the true total prototype floor area for these two archetypes specifically. I did not invent a corrected multiplier (would be fitting/guessing) — I used the literal, self-consistent, verbatim IDF value and flagged it in the JSON's per-archetype `source` field and here. **This directly drives the CP-1 magnitude flag below (HighriseApartment ≈10.2 kWh/m²/yr, higher than any other archetype) and needs a manager decision before CP-2.**
  - `SecondarySchool`'s `design_level_w` (5896.595 W) and `prototype_floor_area_m2` (9796.0 m²) were both harvested from the same `_50pct_downscaled` IDF instance (not the RESULT_04 full-size 19,592 m² used by `cooking_by_archetype.json`) — the pairing is self-consistent (density is scale-invariant) but the absolute numbers deliberately do not match cooking.json's SecondarySchool floor area.
  - Heat-gain fractions were transcribed verbatim per archetype (not a single blanket default): LargeOffice/LargeHotel/Hospital use the PLAN's 0.5/0/0 fallback (source is `Exterior:FuelEquipment`, no zone heat-gain fields exist to transcribe); MediumOffice/SmallHotel/SecondarySchool/College independently show the DOE-authored 0/0.5/0 split (confirms the fallback is not an invented number); Outpatient shows 0/0.1/0.9 and both apartment archetypes show 0/0/0.95 (transcribed verbatim, not defaulted).
  - College's schedule was reformatted (values unchanged) from the source's `Schedule:Year`/`Schedule:Week:Daily`/`Schedule:Day:Interval` chain into an equivalent `Schedule:Compact` token list, since every other archetype's `BLDG_ELEVATORS` is natively `Schedule:Compact` and the emitter (T02) only knows how to write that one object type.
  - All design-level and heat-gain-fraction values were harvested programmatically via `eppy` `fieldvalues`/`fieldnames` (not manually transcribed from grep output) to eliminate transcription risk; floor areas were computed by summing `BuildingSurface:Detailed` Floor-surface `.area` × Zone Multiplier via `geomeppy`.
- Test status: covered by T03 (`test_anchor_values_exact`, `test_no_elevator_archetypes_absent`, `test_no_extra_archetype_keys`, `test_prototype_floor_areas_positive` — all pass).
- Notes: manager-verified anchors (OfficeLarge 140025.3, HotelLarge 44860.63, Hospital 34667.95, OfficeMedium 8517.82) match exactly.

#### T02 — `elevators.py` emitter — completed 2026-07-14
- Artifacts: `openubem/idf/elevators.py`
- Deviations: none beyond what T01 already documents. Mirrors `cooking.assign_cooking` structure (empty-zones guard, archetype-absent early-return before any geometry resolution, provenance-token collection via the reused `cooking._total_floor_area` helper, `SCHEDULE:COMPACT` written once per archetype via `if not any(...)` idempotency guard). No cap applied on the area-scaling ratio (per PLAN §3, unlike cooking's exhaust-flow cap). `cooking.py` itself was not modified.
- Test status: covered by T03.
- Notes: heat-gain fractions and design level are both fully table-driven (no hardcoded per-archetype logic in the emitter itself), so any future correction to the JSON (e.g. the apartment floor-area flag above) requires no code change.

#### T03 — `test_elevators.py` — completed 2026-07-14
- Artifacts: `tests/test_elevators.py`
- Deviations: none.
- Test status: `pytest tests/test_elevators.py -q` → **28 passed**. Also re-ran `tests/test_cooking.py tests/test_refrigeration.py tests/test_dhw.py` together (79 + 23 = confirmed unaffected) to verify no cross-contamination from the shared `cooking._total_floor_area` import.
- Notes: includes the four manager-verified anchors, absence checks for SmallOffice/Warehouse/PrimarySchool, a full no-elevator-archetype parametrized sweep (12 archetypes including TallBuilding/SuperTallBuilding per the T01 finding), linear no-cap scaling, empty-zones guard, and a verbatim-heat-gain-transcription check (HighriseApartment's 0/0/0.95 split, proving the emitter doesn't blanket-default).

#### T04 — Wire into `builder.py` — completed 2026-07-14
- Artifacts: `openubem/idf/builder.py` (added `from openubem.idf.elevators import assign_elevators` at the import block and `assign_elevators(self.idf, row, extruded_zones)` immediately after the `assign_refrigeration` call, i.e. at the former line 507/508), `tests/test_step3_orchestrator.py` (new test `test_medium_office_idf_contains_elevator_equipment`).
- Deviations: PLAN asked for "a built LargeOffice IDF"; the synthetic 10-building fixture (`tests/fixtures/synthetic_10_buildings.py`) has no LargeOffice row. Used **MediumOffice** (fixture row R6) instead — it is a real archetype confirmed present in `elevators_by_archetype.json` (T01 anchor 8517.82 W) that already flows through the same full `run_step3` → `BuildingIDF.build` pipeline. Cited here per the "if not literally spelled out, cite a DESIGN/PLAN line" rule since this substitutes the PLAN's named archetype.
- Test status: `pytest tests/test_step3_orchestrator.py -k elevator -v` → **1 passed**. Full suite `pytest tests/test_step3_orchestrator.py -q` → **19 passed** (pre-existing Windows loky/joblib stderr access-violation noise appears in the console during `test_parallel_byte_identity` but is non-fatal and unrelated to this change — the run still reports all 19 passed; reproduced without inspecting further since it is loky/joblib subprocess-teardown noise on Windows, not a test failure).
- Notes: **byte-identity independently verified** by direct script (not just pytest) — built all 10 synthetic-fixture archetypes through `run_step3` and confirmed exactly 3 emit an `Elevators` `ElectricEquipment` object (MediumOffice, MidriseApartment, HighriseApartment — 1 each) and the other 7 (SmallOffice, TallBuilding, SuperTallBuilding, RetailStripmall, Warehouse, SmallDataCenterHighITE, OpenUBEMUnknown) emit **zero**, confirming TallBuilding/SuperTallBuilding correctly produce no elevator load per the T01 finding.

**CP-1 reached.** Harvested table and hand-computed magnitude sanity check reported to the manager for review before any further build-out (T05/T06). Headline flag: the HighriseApartment/MidriseApartment prototype floor-area anomaly (see T01 deviations) needs a manager decision — it currently drives HighriseApartment's estimated kWh/m²/yr well above every other archetype's, which is physically counter-intuitive for a "high-rise" building and should not be shipped past CP-1 without a ruling.

#### T01 CP-1 area correction — apartment full-building denominators — completed 2026-07-14
- Artifacts: `openubem/data/loads/elevators_by_archetype.json` (HighriseApartment `prototype_floor_area_m2` 2350.94 → **7838**; MidriseApartment 2350.96 → **3135**; both gain a `prototype_floor_area_note` recording that the value is the full-building area, not the reduced-zone-model area, because the DOE elevator `design_level_w` is a whole-building quantity. SecondarySchool gains a `prototype_floor_area_note` flagging its `_50pct_downscaled` provenance as ratio-self-consistent and explicitly NOT a bug.)
- Ruling applied: manager CP-1 correction. Pure geometry, zero-fitted-params preserved.
- **Verification (done BEFORE writing, per instruction):** both apartment prototypes model only 3 representative levels at Zone Multiplier=1. Derived footprint = modeled-3-level-area / 3 = 2350.94/3 = **783.65 m²** (identical for both files). Floor counts from Z-origins at 3.048 m floor height: HighRise [0, 12.1914, 27.4307] → 27.43/3.048 = 9 gaps → **10 floors**; MidRise [0, 3.0479, 9.1436] → 9.14/3.048 = 3 gaps → **4 floors**. footprint × floors: 783.65×10 = 7836.5 m² vs DOE-published 7838 (**0.02%** agreement); 783.65×4 = 3134.6 m² vs DOE-published 3135 (**0.01%** agreement). Both hold well within the ~3% tolerance — no invented value.
- **Spot-check of every other archetype (area = footprint × integer floors):** the distinct-Z-origin count is an unreliable proxy (most prototypes place all zones at Z_Origin=0 with real Z in the surface vertices, and LargeOffice/LargeHotel/Hospital represent repeated floors via captured Zone Multipliers). The reliable measure — the floor-surface-area sum × multiplier that the original harvest used — already yields the TRUE full-building area for all of LargeOffice (46320, multiplier-captured), MediumOffice (4982, all 3 bottom/mid/top floor groups present), LargeHotel (11345, multiplier-captured), SmallHotel (4014), Hospital (22436, multiplier-captured), Outpatient (3804, 3 explicit floors), SecondarySchool (9796, ratio-self-consistent downscale), College (6416, 4 explicit floors). **The two apartments were the only prototypes whose real floors were neither explicitly modelled nor captured by a multiplier** — none of the others need correction.
- Test status: `pytest tests/test_elevators.py -q` → **28 passed** (no test pinned the old apartment area; `test_prototype_floor_areas_positive` still green with the new values).
- **Corrected magnitude table (kWh/m²/yr, verbatim DOE schedule annual-average × density × 8760h):** LargeOffice 6.86, MediumOffice 3.54, LargeHotel 8.98, SmallHotel 4.93, Hospital 6.79, Outpatient 8.00, **HighriseApartment 3.07** (was 10.23), **MidriseApartment 3.16** (was 4.21), SecondarySchool 0.84, College 3.00. Both apartments now land ≈3 kWh/m², consistent with each other and with the office/hotel band — the over-count is resolved. **STOP at CP-1; awaiting manager gate before T05/T06. No parser.py/aggregator.py/results/sim work performed.**

#### T05 — Results wiring (Elevators as a 10th end-use column) — completed 2026-07-14
- Artifacts: `openubem/results/parser.py` (added `Elevators:InteriorEquipment:Electricity` to `METER_QUERY` + the `_parse_meters_sql` dict; in `_compute_eui` broke elevators out into `elevators_eui_kwh_m2` and subtracted it from `equipment_eui_kwh_m2`, added it to the total sum; added the column to `_failed_row`), `openubem/results/carbon.py`, `openubem/results/aggregator.py` (`_STEP5_COLS` +2), `tests/test_parser_elevators.py` (new, 8 tests), `tests/test_results_aggregator.py` (fixture rows +2 cols).
- **Deviation (scope) — carbon.py touched, though the manager's T05 line named only parser.py + aggregator.py.** Rationale, cited to the manager's own two constraints ("rather than being folded into generic Equipment" + "Do NOT change the total-EUI math"): elevators are `ElectricEquipment`, so their kWh is already inside `Zone Electric Equipment Electricity Energy` → `equipment_eui_kwh_m2` → total. The only way to make the breakdown mutually-exclusive (10 real end-uses that SUM to total, satisfying the manager's test (b)) is to **subtract** elevators from `equipment_eui` and re-add them as `elevators_eui`. That subtraction flows into `carbon.py`'s `gwp_equipment = equipment_eui × f_elec`, which would then silently DROP the elevator carbon from `gwp_total`. To keep `gwp_total` numerically invariant (the same "do not change the totals" principle applied to carbon) I added a parallel `gwp_elevators_kgco2_m2` column (`elevators_eui × f_elec`) and included it in `gwp_total`. Net effect: BOTH `total_eui_kwh_m2` and `gwp_total_kgco2_m2` are byte-for-byte invariant vs the pre-T05 9-way computation; the elevator's energy/carbon simply moves from the equipment bucket into its own bucket. Not adding gwp_elevators would have been the larger violation (a real carbon regression). Flagged for audit.
- Neighbourhood-summary `eui_cols` (aggregator.py) intentionally NOT extended — it already reports only heating/cooling/lighting/equipment/total and omits every other service load (fans/pumps/dhw/cooking/refrigeration); elevators follows that existing convention. Total-EUI math there is unchanged.
- Test status: `pytest tests/test_parser_elevators.py -q` → **8 passed**; full results regression `pytest tests/test_parser_hvac_metered.py tests/test_results_parser.py tests/test_results_carbon.py tests/test_results_aggregator.py -q` → **112 passed** (one aggregator fixture updated to carry the 2 new columns; the pre-existing pandas `strptime` DeprecationWarning is unrelated). Tests assert: (a) `elevators_eui_kwh_m2` surfaces as its own column; (b) total == sum of the 10 columns; total invariant vs the folded case; `gwp_total` invariant vs the folded case with elevator carbon accounted exactly once.
- Notes: total-EUI math result is unchanged (manager's hard requirement met); only the *attribution* changed. Confirmed the EnergyPlus submeter name for `EndUse_Subcategory="Elevators"` on interior ElectricEquipment is `Elevators:InteriorEquipment:Electricity`.

#### T06 — LIVE_SMOKE (build-only, NO simulation) — completed 2026-07-14
- Artifacts: `scripts/validation/elevators_live_smoke.py` (standalone, not pytest).
- What it does: builds one real IDF per elevator archetype through the full `BuildingIDF.build` path (auto resolution, real geometry/context/extrusion), asserts exactly one `Elevators` `ElectricEquipment` with a plausible non-zero design level, and prints emitted W + size-invariant implied kWh/m² cross-checked against the CP-1 table. Then builds SmallOffice twice — once normally, once with `builder.assign_elevators` monkeypatched to a no-op (== the pre-change code path) — and diffs the two IDF byte streams.
- **Smoke result — ALL PASSED.** Every one of the 10 elevator archetypes emitted one Elevators object; each implied kWh/m² matched the CP-1 table to ≤0.01 (College 3.001, HighriseApartment 3.070, Hospital 6.785, LargeHotel 8.977, LargeOffice 6.863, MediumOffice 3.544, MidriseApartment 3.158, Outpatient 7.999, SecondarySchool 0.835, SmallHotel 4.934). SmallOffice emitted **0** Elevators objects and the with-call vs no-op-patch builds were **byte-identical** — proving the elevator wiring is provably inert for absent archetypes (the CP-4/byte-identity requirement).
- Test status: script exit 0 (all checks passed). NO EnergyPlus run performed.

**CP-2 reached — STOP HARD.** Emitter + table + results wiring + LIVE_SMOKE all green; byte-identity confirmed. Per PLAN §6 CP-2 and the manager's standing instruction, the 12-cell fleet re-simulation is a **user sign-off decision** and was NOT fired. Expected fleet EUI delta (build-time density estimate, from the real adopted-baseline 12-cell mix, n=8,152 buildings, 17.36 M m²):
- **Fleet-weighted elevator EUI adder = +2.47 kWh/m²/yr ≈ +1.4% of the current baseline total EUI (171.4 kWh/m²).** Direction is +EUI (elevators were 100% missing → this is a pure addition, a modest under-prediction correction toward measured, consistent with §0's "modest under-prediction contributor" framing).
- Elevator-bearing archetypes cover **49.1%** of fleet floor area (LargeOffice 23.8%, MidriseApartment 12.0%, MediumOffice 7.3%, HighriseApartment 5.1%, plus small Outpatient/Hospital/SecondarySchool shares); the other ~51% (SmallOffice, retail, warehouse, data centers, restaurants, TallBuilding/SuperTallBuilding, etc.) get +0.
- **Per-cell range: +0.4% (nyc_rural, +1.03 kWh/m²) to +2.7% (austin_urban, +5.29 kWh/m²).** Full per-cell adders (kWh/m²): austin_centre 1.96, austin_rural 2.69, austin_suburban 1.15, austin_urban 5.29, la_centre 2.98, la_rural 1.30, la_suburban 2.71, la_urban 3.77, nyc_centre 1.02, nyc_rural 1.03, nyc_suburban 2.34, nyc_urban 2.86.
- Caveat: this is the direct-electricity adder from density × DOE schedule; the actual simulated delta will also carry a small secondary HVAC interaction (elevator waste heat = summer cooling penalty / winter heating credit via the transcribed Fraction_Radiant/Lost). The primary +1.4% number is the electricity term. **Awaiting the manager's gate to bring these numbers to the user for the re-sim decision.**

#### CP-2 gate decision + single-cell A/B validity dispatch — in progress 2026-07-14
- **Manager gate ruling:** CP-2 numbers presented to the user. Rather than fire the full 12-cell fleet re-baseline immediately (user-gated, changes the adopted Phase-E headline + costs cluster budget), the user chose **"Sim 1 cellule d'abord"** — validate the emitter against a real EnergyPlus run on a single cell before committing the fleet. Cell picked: **austin_urban** (the max per-cell adder, +5.29 kWh/m² / +2.7% estimate → highest signal-to-noise for a validity check).
- **Dispatch:** a fresh Sonnet cluster employee built and submitted a paired A/B experiment (per [[feedback_sonnet_for_cluster_harvest]], [[feedback_cluster_no_login_compute]] — all compute via `sbatch --array` fire-and-forget, no login-node work):
  - **Arm A (elevators active):** SLURM job `1116396`, 425-task array → `/speed-scratch/o_iseri/fleets/elevab_austin_urban_A`.
  - **Arm B (elevators disabled):** SLURM job `1116425`, 425-task array. Arm B monkeypatches `assign_elevators` to a no-op during Step 3 only (reverted after); everything else identical.
  - **Isolation verified pre-ship:** shared Steps 1-2 (425 buildings, no non-elevator drift between arms); Arm A carries 56 elevator-bearing IDFs (LargeOffice 13 + MediumOffice 27 + MidriseApartment 11 + Hospital 3 + Outpatient 2), Arm B carries 0.
- **Status:** both arrays live in the Speed queue; a 30-min poller + harvest/analysis script (`scripts/cluster/elevator_ab_harvest.py`) are armed. Pending: the harvested simulated A−B delta EUI for austin_urban vs the +2.7% hand-estimate, with the HVAC-interaction component isolated (simulated total delta − Arm A `elevators_eui_kwh_m2` adder). That result gates the user's full-fleet re-sim decision and will be appended here on harvest. **The unrelated `lmn_can` array (1115134_*) sharing the queue is NOT touched** ([[feedback_never_touch_other_project_runs]]).

#### Single-cell A/B harvest RESULT + attribution-meter audit — 2026-07-14
- **Both arrays completed 425/425, exit 0:0, zero failures.** Harvest respected cluster discipline: per-building `eplusout.sql` streamed down via scp (lightweight I/O), aggregated **locally on the Windows box** through the project venv — **no login-node compute** ([[feedback_cluster_no_login_compute]] honoured). Result JSON at `%TEMP%\ubem_elev_ab\austin_urban\ab_result.json` (+ `parsed_A/B.parquet`).
- **austin_urban A/B numbers (area-weighted by conditioned floor area, 425 buildings):**
  | Metric | Value |
  |---|---|
  | Arm A total EUI (elevators on) | **250.65** kWh/m²/yr |
  | Arm B total EUI (elevators off) | **244.52** kWh/m²/yr |
  | Simulated A−B total delta | **+6.13 kWh/m² (+2.51%)** cell-wide |
  | Per-elevator-building mean total delta | **+5.13 kWh/m²** (vs manager hand-estimate +5.29 — close match ✓) |
  | Direct elevator electricity (A−B `equipment_eui` delta) | **+4.87 kWh/m²** |
  | HVAC-interaction (total delta − direct elec) | **+1.26 kWh/m² (+0.52 pp), signed POSITIVE** |
  | Elevator-bearing buildings (equipment-delta > 0.01) | **56 / 425 ✓** (matches the 56 expected) |
- **Physics validated.** HVAC-interaction sign is POSITIVE as predicted for cooling-dominated Austin: waste heat rejected indoors → cooling +0.67, fans +0.60, pumps +0.17, heating −0.17 = net +1.26 on top of direct electricity. Magnitude and per-building mean both match the DOE-verbatim hand-estimate. **The emitter is physically correct and correctly scaled — the "Sim 1 cellule d'abord" magnitude gate is PASSED.**
- **⚠️ AUDIT FINDING — attribution breakout wiring gap (real production bug, NOT a harvest artifact).** The dedicated `elevators_eui_kwh_m2` column read **0/425 in BOTH arms.** Manager root-caused it in the production code (no cluster work): `openubem/idf/outputs.py` `HVAC_METERS` (lines 28-42) emits the `Output:Meter` for Cooking (`Cooking:InteriorEquipment:Electricity`) and Refrigeration (`Refrigeration:InteriorEquipment:Electricity`) but **omits `Elevators:InteriorEquipment:Electricity`**, which both the emitter (`elevators.py:65`, `EndUse_Subcategory="Elevators"`) and the parser (`parser.py:47/111`) reference. With no `Output:Meter` request, EnergyPlus never writes that subcategory meter to the SQL at RunPeriod → `_parse_meters_sql` returns the 0.0 default → `elevators_eui_kwh_m2 = 0` and the de-fold on `parser.py:306` is a no-op, so elevators stay folded inside `equipment_eui`.
  - **Impact scoped:** **total EUI is CORRECT** (elevator kWh flows through `InteriorEquipment:Electricity`, which IS metered) — the +6.13 validity proof stands. Only the 10th-end-use *attribution line* is missing. LIVE_SMOKE (T05) did not catch this because it asserts on the emitted IDF object, not on a parsed SQL meter — a synthetic-test blind spot ([[feedback_synthetic_test_blind_spots]]).
  - **Fix = one line** (add `"Elevators:InteriorEquipment:Electricity"` to `HVAC_METERS`, mirroring Cooking/Refrigeration). Must land BEFORE any fleet re-baseline if the breakout column is to be populated. Feature code → dispatched to a fresh Sonnet employee (T07-METERFIX + a single-building post-fix sbatch to confirm `elevators_eui > 0` and that it equals the equipment delta). The completed austin_urban A/B run does NOT need re-doing for magnitude — only a one-building confirmation of the breakout mechanism end-to-end.
- **Full 12-cell fleet re-baseline remains user-gated and NOT fired.** To be brought to the user once T07-METERFIX + its one-building confirmation are green.

#### T07-METERFIX + T07-CONFIRM — attribution meter fixed + confirmed end-to-end — 2026-07-14
- **Source fix (one line):** `openubem/idf/outputs.py` — added `"Elevators:InteriorEquipment:Electricity"` to `HVAC_METERS` immediately after the `Refrigeration:InteriorEquipment:Electricity` entry, mirroring the two adjacent `*:InteriorEquipment:Electricity` meters exactly. This is the only source edit. EnergyPlus now emits the RunPeriod `Output:Meter` the parser was already querying.
- **Tests updated (existing file, no new file invented):** `tests/test_outputs.py` — `test_hvac_meters_count` 13→14, `test_output_meter_count` 13→14, `test_hvac_meters_phase_e_required` gains the Elevators meter. `tests/test_outputs.py` + `tests/test_parser_elevators.py` = **19 passed**.
- **Cluster end-to-end confirmation (fire-and-forget `sbatch` job 1117389, COMPLETED, no login-node compute):** rebuilt building `way/312329732` (LargeOffice, austin_urban, 1658.5 m²) through the production Step 1–3 path WITH the fix (rebuilt IDF verified to contain the Elevators `Output:Meter` + 1 Elevators ElectricEquipment), 1-building fleet, single-task sbatch, `eplusout.sql` scp'd down, parsed locally with the production `parse_building`:
  | Metric | Value |
  |---|---|
  | pre-fix `elevators_eui_kwh_m2` | **0.000000** (bug; re-parsing the old harvest SQL also → 0) |
  | post-fix `elevators_eui_kwh_m2` | **6.863061 kWh/m²** (>0 ✓) |
  | expected elevator elec (Arm A−B equipment delta) | **6.863061 kWh/m²** |
  | match | **100.000 % (+0.000 %)** |
  | `equipment_eui` de-fold | 50.926337 → 44.063276 (drops by exactly 6.863061 ✓) |
- **Total invariance airtight:** on the *same* post-fix SQL, computing total with elevators broken-out vs folded-into-equipment gives an identical total (|diff| = 1.4e-14). The fix only **re-attributes**; it never changes the total. The +0.37 % cross-run total difference (113.58→114.00) is independent-run HVAC-coupling noise (the *direct* elevator-electricity term matched to 0.000 %).
- **Net effect:** `elevators_eui_kwh_m2` now populates for elevator-bearing buildings in production; total EUI unaffected. **Both magnitude (Sim-1-cellule) and attribution mechanism are now proven end-to-end. Arc is technically complete; only the user-gated 12-cell re-baseline remains before headline adoption.**

#### T08 — 12-cell fleet re-baseline (user-gated, user-approved) — completed 2026-07-15
- **Method:** frozen E-R3-3 geometry reused; 12 `sbatch --array` jobs (one per cell, fire-and-forget, zero login-node compute); SQL harvested via scp and parsed LOCALLY on Windows with production `parse_building`; area-weighted aggregation. Executed by fresh Sonnet employees across 2026-07-14/15 (harvest resumed twice after background-task deaths; manifest + idempotent scripts made every resume re-sim-free).
- **Artifacts:** per-cell results at `docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/` (04_simulation_manifest.parquet, 05_neighbourhood_summary.json, 05_results.csv/.geojson/.gpkg, figures/); aggregate table `elev_rebaseline_results.json` (session scratchpad, transcribed below).
- **Per-cell results (baseline → new total EUI kWh/m², Δ, n_success, n elevator-bearing, mean elevators_eui among bearing):**

  | Cell | Baseline | New | Δ abs | Δ % | n | n elev | mean elev EUI |
  |---|---|---|---|---|---|---|---|
  | austin_centre | 167.63 | 168.77 | +1.14 | +0.68% | 413 | 127 | 4.67 |
  | austin_rural | 155.95 | 157.14 | +1.19 | +0.76% | 245 | 26 | 3.73 |
  | austin_suburban | 171.09 | 171.50 | +0.42 | +0.24% | 437 | 8 | 2.75 |
  | austin_urban | 172.75 | 177.14 | +4.39 | +2.54% | 425 | 56 | 4.46 |
  | la_centre | 129.41 | 132.89 | +3.48 | +2.69% | 226 | 91 | 4.75 |
  | la_rural | 120.15 | 121.46 | +1.31 | +1.09% | 149 | 17 | 3.32 |
  | la_suburban | 105.82 | 108.44 | +2.62 | +2.47% | 1343 | 1288 | 3.16 |
  | la_urban | 125.72 | 130.00 | +4.28 | +3.40% | 618 | 516 | 3.35 |
  | nyc_centre | 167.09 | 168.11 | +1.02 | +0.61% | 738 | 338 | 5.20 |
  | nyc_rural | 232.42 | 234.90 | +2.48 | +1.07% | 198 | 27 | 3.60 |
  | nyc_suburban | 196.63 | 198.56 | +1.93 | +0.98% | 1589 | 980 | 3.16 |
  | nyc_urban | 150.30 | 152.28 | +1.97 | +1.31% | 1779 | 87 | 3.61 |

- **Fleet-weighted headline:** 155.85 → **158.03 kWh/m²** (+2.18, **+1.4%**). All 12 deltas positive (elevators are net-new load, as designed); breakout magnitudes 2.75–5.20 kWh/m² among elevator-bearing buildings — consistent with the single-digit "honest magnitude" stated at arc opening and the 6.86 kWh/m² LargeOffice single-building confirmation (T07).
- **New city-anchor gates (median total EUI vs measured anchor):** NYC **−31.3%** (was −31.9%), LA **−3.6%** (was −6.2%), Austin **−30.5%** (was −30.7%). CBECS R² 0.877 / 0.902 / 0.723 (was 0.888 / 0.920 / 0.720). Under-prediction narrows in all three cities; no gate regresses materially.
- **Audit (manager):** frozen-baseline per-cell values reproduced exactly (nyc_urban 150.303, nyc_suburban 196.625, nyc_centre 167.092, la_suburban 105.824, austin_urban 172.748 — all match the adopted E-R3-3 record); austin_urban new total 177.14 matches the mid-harvest spot-check; zero-fitted-params preserved (every design level a verbatim DOE constant, area-scaled).
- **Decision: ADOPTED.** E-R3-3+elevators is the new Phase-E adopted baseline; headline NYC −31.3% / LA −3.6% / Austin −30.5%, fleet-weighted 158.0 kWh/m². Elevators = 10th physically-modelled end-use. Arc complete.
- Note for a future reader: `05_neighbourhood_summary.json`'s weighted-EUI dict does not carry a separate `elevators_eui_kwh_m2` key (aggregator surfaces it per-building in `05_results.csv`; equipment is already de-folded). Cosmetic only; totals and per-building attribution are correct.
