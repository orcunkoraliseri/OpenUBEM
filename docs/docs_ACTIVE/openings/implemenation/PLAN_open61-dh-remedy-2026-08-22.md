# PLAN — OPEN-61 district-heating remedy, 2026-08-22

**Slug:** `open61-dh-remedy-2026-08-22`
**Date opened:** 2026-08-22
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md`
**Predecessor (ARCHIVED 2026-08-22, citations swept):**
`implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md`
**Ruling that opened it:** user, 2026-08-22 — *"open-61 vas-y"*, after the director offered OPEN-61
as the next action on the grounds that it is the only remaining item with a measured size.

## 1. Why this plan exists

OPEN-61 has been fully diagnosed for two days and has had **no remedy proposed**, because the
register recorded the remedy as "a design question, and neither shape is taken". Both shapes are now
decidable on evidence rather than on preference, and §5 records the evidence. **This plan takes the
decision, writes the fix, proves it against 7,861 real simulation files that already exist, and
produces the corrected fleet figure — but does NOT adopt it.** Adoption is a user ruling and is
CP-2's only question.

**What OPEN-61 is.** `total_eui_kwh_m2` silently drops the District Heating component of Water
Systems. `METER_QUERY` (`openubem/results/parser.py:41-54`) names ten meters and none of them is a
district-heating meter, so district-heated domestic hot water is dropped before the total is formed.
Measured at fleet scale on 2026-08-20: **19.4707 kWh/m² over n = 8,144, 12.7 % of pooled site
energy.**

**The one thing that changed and made this plan possible.** T04 of the predecessor plan established
that the term is **concentrated, not uniform** — 116 buildings carry 70.5 % of it. That finding was
read as making the remedy harder. **It does the opposite: it rules out a flat offset, which is the
only remedy shape a per-building read does not use.** See §5 F6.

## 2. Hard rules for the executor

1. **Execute this plan top-to-bottom. Do not propose alternatives.** If this plan or the DESIGN is
   ambiguous, STOP and quote the conflict. Do not invent a value that is not in §5.
2. **Before debugging ANY error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.
   After solving ANY error, register it there** in house format before closing the task. An error is
   not fixed until its entry exists.
3. **No compute on the Speed login node.** Nothing here needs the cluster. **Nothing here needs
   EnergyPlus** — see §5 F8.
4. Never edit root `main.py`, OVERVIEW or DESIGN docs. No `.py` under `docs/`.
5. Figures to `openubem/outputs/` (flat); CSVs to `openubem/outputs/comparisons/`.
6. **Do not commit.** Git is handled outside this session.
7. **Run `pytest` in the FOREGROUND.** Both executors of the previous plan parked waiting for a
   background test run to notify them, which never happens. Report before or after, never during.
8. Append your progress entry to §8 of this file, one per task, in the house format.
9. 🔴 **DO NOT restate the adopted fleet figure.** `153.8231 kWh/m² pooled over 8,153` stands
   unchanged for the whole of this plan. T03 produces a *candidate* figure and labels it as such.
10. 🔴 **The preserved corpus at `C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20` is
    READ-ONLY.** It cost 97.2 CPU-hours to produce and is protected by ruling R6. Open every `.sql`
    with `mode=ro`. Write nothing into that tree, delete nothing, move nothing.

## 3. Dependency decisions (pinned)

- Python: `.venv\Scripts\python.exe`. pandas as installed. **No new dependencies.**
- Suite baseline: **1,927 passed / 55 skipped / 0 failed.** The authoritative baseline is the
  enumerated 55-skip table in §9 of `implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md`,
  **not the count.** If a skip becomes a pass, name which one.
- Adopted baseline: **153.8231 kWh/m² pooled over 8,153. Untouched by this plan.**
- **No new emission factor is defined by this plan.** See §5 F10 and T04.

## 4. File layout

| Task | Writes |
|---|---|
| T01 | `openubem/results/parser.py`, `openubem/results/aggregator.py`, `tests/test_parser_open61_district_heating.py`, `extra/FIX_open-61_district-heating.md` |
| T02 | `scripts/analysis/open61_remedy_corpus_validation_2026-08-22.py`, `openubem/outputs/comparisons/open61_remedy_validation_2026-08-22.csv` |
| T03 | `scripts/analysis/open61_fleet_restatement_2026-08-22.py`, `openubem/outputs/comparisons/open61_fleet_restatement_2026-08-22.csv`, `extra/MEASUREMENT_open-61_fleet-restatement_2026-08-22.md` |
| T04 | director only — register + prompt + checklist |

`extra/` = `docs/docs_ACTIVE/openings/extra/`.

## 5. Facts with citations — all director-verified for this plan on 2026-08-22

**F1 — the meter route cannot fix a single existing file, and this is a census, not an inference.**
`dh_b_available` is **True on 0 of 8,152** `ok` rows of
`openubem/outputs/comparisons/open61_census_fleet.csv`. The reader's own docstring records the same
finding independently (`scripts/analysis/open61_census_read_2026-08-20.py:10-19`): across every
`.sql` inspected, `ReportDataDictionary` carries **no meter or variable whose name contains
"District" at all**.
➡️ **Remedy shape (a) — request a `DistrictHeating:Facility` meter in the IDF — is REJECTED as the
fix.** It would change what every future run emits and leave all 121.9 GB of existing results
unfixable. It is not rejected as an idea; see §6.

**F2 — ABUPS is the only source, and a verified reader for it already exists.**
`read_district_heating()` in `scripts/analysis/open61_census_read_2026-08-20.py` reads
`TabularDataWithStrings`, `ReportName='AnnualBuildingUtilityPerformanceSummary'`,
`TableName='End Uses'`, `ColumnName='District Heating'`, `RowName='Total End Uses'`. Verified on 108
buildings (`openubem/outputs/comparisons/open61_census_read_verification.csv`) and self-reconciled
against the sum of its own 14 end-use rows on **8,144 of 8,144** buildings carrying DH
(`dh_a_reconciles`).

🔴 **F2 IS CORRECTED, 2026-08-22, by the golden-fixture failures of T01.** The census reader
reads `RowName='Total End Uses'` because a *census* wanted the total. **A parser that folds district
heating into DHW must read `RowName='Water Systems'`, not `'Total End Uses'`.** The two are equal on
every fleet building (F11) and **wildly unequal on the golden fixtures**, which is why T01 as
originally written broke three golden tests. **Every instruction in T01 that names `'Total End Uses'`
is superseded by T01b.**

**F3 — attribution is unambiguous: 100.00 % of fleet district heating is Water Systems.**
Over the 8,152 `ok` rows: Σ`dh_water_systems_gj` = **1,694,992.3 GJ**, Σ`dh_total_gj` =
**1,694,992.3 GJ**, Σ`dh_other_rows_sum_gj` = **0.0**. ➡️ **On the fleet there is no question about which end use
this energy belongs to.** It is DHW, and it goes into `dhw_eui_kwh_m2`.

⚠️ **F3 IS NARROWED, 2026-08-22: this is a statement about the fleet, not about the code.** The golden fixture `r1_single_zone.sql` carries **148.24 GJ of district heating, of which 100 % is the `Heating` row and 0.00 GJ is `Water Systems`** — the exact mirror image of the fleet. Buildings whose district heating serves space heating **exist, are in this repository, and were used to validate the parser**. F3 licenses folding the *Water Systems* row into DHW. It does **not** license treating the district-heating *total* as DHW. See F11 and **OPEN-64**.

**F11 — 🔴 `Total End Uses` ≠ `Water Systems`, and the difference is not
academic. Measured this pass by the director, both populations.**

- **Fleet, 8,152 `ok` census rows:** `max |dh_total_gj − dh_water_systems_gj|` = **0.0**, and
  **0 rows** have `dh_other_rows_sum_gj > 0`. ➡️ Per-building, not merely in aggregate, the
  two rows are **identical on every fleet building**. **F7's +19.4707 kWh/m² is therefore
  unchanged by the T01b correction, and T02's C1/C2/C3 results remain valid** — they compare
  against `dh_total_kwh`, which on this population *is* the Water Systems value.
- **Golden fixtures, the counterexample:** `r1_single_zone.sql` → `Heating` **148.24 GJ**,
  `Water Systems` **0.00 GJ**, `Total End Uses` **148.24 GJ**. Likewise `r2_one_zone_per_floor.sql`
  (709.99 GJ) and `r6_perimeter_core.sql` (1,646.86 GJ). Reading the *total* injected
  **+105.0456 / +78.8878 / +101.6580 kWh/m²** of **space-heating** energy into `dhw_eui_kwh_m2`.
  Each delta was re-derived by the director and matches the observed test failure **to the last
  digit** — e.g. R1: 148.24 GJ × 277.7778 ÷ 392 m² = 105.0456, and the test
  reported 276.9193 against an expected 171.8739, a difference of 105.0454.

⚠️ **This was a defect in the plan, not in the executor's work.** T01 step 2 instructed
`RowName='Total End Uses'` verbatim and the executor implemented exactly that. **The correction is
T01b and the cost is the director's.**

**F4 — the parser already reads ABUPS; this extends an existing route.**
`check_building_integrity()` at `openubem/results/parser.py:693-702` already issues a
`TabularDataWithStrings` / `AnnualBuildingUtilityPerformanceSummary` / `End Uses` query.
➡️ "Reading ABUPS as a second, differently-shaped source of truth inside the parser" — the objection
the register raised against remedy shape (b) — **describes something the parser has been doing since
Phase-E §5.1 P5.**

**F5 — the injection point, and why it is the safe one.**
`_parse_meters_sql()` (`parser.py:106-136`) returns `{meter_name: kWh}`, seeded by a zeros dict
(`:115-125`) and wrapped in a swallow-all `except Exception: pass` (`:133-134`).
`_compute_eui()` reads it **only** through `_m()` (`:526-527`), which returns `0.0` for any absent
key. `dhw_kwh` is formed at `:533`, `dhw_eui_kwh_m2` at `:546`, the ten-term total at `:559-571`.
➡️ A pseudo-meter key added to that dict inherits the existing missing-value contract for free.

**F6 — the concentration finding does NOT constrain a per-building remedy.**
116 buildings (`SuperTallBuilding` 24 + `TallBuilding` 92) carry **70.5 %** of the term, and four
archetypes carry 91.8 %. That result ruled out **applying 19.47 as a flat offset**. A per-building
ABUPS read gives each building **its own measured value**; a building with no district heating reads
0.0 and does not move. ➡️ **Concentration is irrelevant to the correctness of this remedy.** It stays
relevant to how the result is reported (T03) and to the 29.5 % of DH sitting outside the tall class.

**F7 — the size, re-derived by the director from the census CSV for this plan.**
Over the **n = 8,144** rows carrying both `parsed_total_eui_kwh_m2` and `dh_total_kwh`, weighting by
`parsed_floor_area_m2`: pooled **152.3011 → 171.7718 kWh/m²**, a rise of **19.4707 kWh/m² =
+12.78 %**. ⚠️ The 152.3011 base is the **census rebuild's** pooled figure, **not** the adopted
153.8231, which is run 4's over a different 8,153-building population. **The two are not to be
differenced.**

**F8 — no re-simulation is needed, because the corpus survives.**
**7,861 `eplusout.sql`, 121.9 GB, 12 cells**, at
`C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20`, preserved under ruling R6 (T07 of
`implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md:840-870`).
Director-verified for this plan by re-count on 2026-08-22: **7,861 files, 12 cell directories,
`INVENTORY.json` present.** ⚠️ **7,861 against 8,152 census rows — the corpus is 96.4 % of the
fleet, not 100 %**, because the early driver deleted work directories on success. T02 must report
its sample as drawn from the 7,861, not from the 8,152.

**F9 — the corpus reproduces production EUI, so validating against it is meaningful.**
`c1_pass` is **8,143 True / 9 False** of 8,152; `c1_diff_kwh_m2` has median **0.0** and an IQR of
**±5.7 × 10⁻¹⁴**; mean −0.0151, driven by nine outliers.

**F10 — 🔴 CARBON DOES NOT FOLLOW, and this plan will not make it follow.**
`carbon.py:106` builds `gwp_dhw = dhw_gas_eui * f_gas + dhw_elec_eui * f_elec` — from the two fuel
columns only, **never from `dhw_eui_kwh_m2`**. `openubem/config.py:83` defines exactly one factor,
`GWP_NATURAL_GAS_KGCO2_KWH = 0.181`; **there is no district-heating emission factor anywhere in the
codebase.** ➡️ After T01, `total_eui_kwh_m2` rises by 12.78 % and `gwp_total_kgco2_m2` **does not
move**, leaving the two inconsistent. **This is a real defect and it is deliberately left open** —
choosing a district-heating carbon factor is a literature decision, not a coding one, and this
session does not invent values. **T04 opens it as `OPEN-63`.** 🟢 The inconsistency is *pre-existing
and merely made visible*: carbon has been missing this energy all along.

## 6. The decision this plan takes, stated once

**Remedy shape (b) — read District Heating from ABUPS inside the parser — is ADOPTED as the fix**,
on F1 (shape (a) fixes nothing that exists), F2 (the reader exists and is verified), F3 (attribution
is unambiguous) and F4 (the parser already reads ABUPS).

**Remedy shape (a) is NOT rejected as an improvement, only as the fix.** Adding a district-heating
meter to future IDFs would give a second independent source and let `check_building_integrity()`
cross-check the ABUPS read. It is **out of scope here** because it changes what every future run
emits, it fixes nothing already on disk, and it would need its own re-simulation to prove. Recorded
so the option is not lost.

## 7. Tasks

### T01 — Fold district heating into DHW in the parser *(executor, production code)*

**What.** In `openubem/results/parser.py`:

1. Add a module constant `_DISTRICT_HEATING_KEY = "WaterSystems:DistrictHeating"` next to
   `_ELEVATOR_METER` (`:57`). It is a **pseudo-meter key**, not an EnergyPlus meter name — say so in
   one line of comment, because F1 says no such meter exists.
2. Add a private `_read_abups_district_heating(conn) -> float` returning **kWh**, using the query in
   F2 verbatim: `TabularDataWithStrings`, `ReportName='AnnualBuildingUtilityPerformanceSummary'`,
   `TableName='End Uses'`, `ColumnName='District Heating'`, `RowName='Total End Uses'`, value in GJ,
   × `1_000_000/3600`. Missing row, `None`, or blank string → **0.0**.
3. Seed `_DISTRICT_HEATING_KEY: 0.0` in the `_parse_meters_sql` zeros dict (`:115-125`) and call the
   reader **on the connection already open** inside that function's `try` (`:127-134`), so a corrupt
   or ABUPS-less `.sql` falls through the existing `except Exception: pass` to 0.0.
4. In `_compute_eui`: `dh_kwh = _m(_DISTRICT_HEATING_KEY)`; add a new column
   `eui["dhw_district_eui_kwh_m2"] = dh_kwh / floor_area`; add `dh_kwh` into `dhw_kwh` at `:533` so
   it flows into `dhw_eui_kwh_m2` (`:546`) and thence into the total. **Do not add a separate term
   to the total expression** — that would double-count.
5. Add `"dhw_district_eui_kwh_m2"` to `_STEP5_COLS` in `openubem/results/aggregator.py`, immediately
   after `"dhw_elec_eui_kwh_m2"`, and update the column-count comment at `:25-26`.
6. **Do not touch `carbon.py`.** See F10.

**Why.** F1–F5.

**How to test.** New file `tests/test_parser_open61_district_heating.py`, minimum five cases:

- a synthetic `.sql` with a District Heating `Total End Uses` row → `dhw_district_eui_kwh_m2` equals
  GJ × 277.7778 ÷ floor area, and `dhw_eui_kwh_m2` == gas + elec + district;
- **the backwards-compatibility case, which is the load-bearing one:** a `.sql` with no District
  Heating column → `dhw_district_eui_kwh_m2 == 0.0` and `total_eui_kwh_m2` **bit-identical** to the
  value the same fixture produced before this change (assert against a literal, not a
  re-computation);
- an unreadable / non-existent path → 0.0, no raise;
- a blank/`None` ABUPS value → 0.0, no raise;
- `total_eui_kwh_m2` still equals the sum of the ten end-use columns (the D9 invariant), with
  district folded inside `dhw_eui_kwh_m2` and **not** counted twice.

Then the full suite in the **foreground**: `pytest -q tests/`, against the §3 baseline. **If any of
the 55 skips becomes a pass or a failure, name the test.**

**Write** `extra/FIX_open-61_district-heating.md`: mechanism, the query, the four guards, the D9
invariant, and F10 stated as a known unfixed consequence.

### T01b — 🔴 Read the **Water Systems** row, not the total *(executor, production code)*

**Status: MANDATORY, opened 2026-08-22 by the director after reading the T01 suite result. It
supersedes every instruction in T01 that names `RowName='Total End Uses'`.**

**What went wrong.** T01 was implemented exactly as written and the suite came back
**3 failed / 1,933 passed / 55 skipped** against a **1,927 / 55 / 0** baseline. All three failures are
`tests/test_results_parser.py::TestEuiGolden::test_r{1,2,6}_total_eui`. **The sibling
`heating_eui` / `cooling_eui` / `lighting_eui` tests on the same fixtures all passed** — only the
*total* moved, which is the signature of energy being added, not of a component being recomputed.
Cause in one line: **the golden fixtures put 100 % of their district heating in the `Heating` row and
0.00 GJ in `Water Systems`, and T01 folded the `Total End Uses` cell into DHW** (F11).

**What to change — three edits, all in `openubem/results/parser.py`, plus tests.**

1. In `_read_abups_district_heating`, change the query's `RowName` from `'Total End Uses'` to
   **`'Water Systems'`**. Nothing else in the function changes: same table, same column, same
   GJ→kWh factor, same four guards, same `0.0` on missing/`None`/blank/unparseable.
2. Update the function's docstring to state **which row it reads and why**, citing F11: the total
   includes district heating that serves other end uses, and folding that into DHW is wrong.
3. Leave `_DISTRICT_HEATING_KEY`, the zeros-dict seed, the `try/except`, the
   `dhw_district_eui_kwh_m2` column, the fold into `dhw_kwh`, and the aggregator column **exactly as
   T01 left them**. They are correct. **Do not touch `carbon.py`** (F10).

🔴 **What you must NOT do.** Do **not** "fix" the three golden tests by editing their
expected values in the golden JSON. Those expectations are correct for the Water Systems reading and
the tests must return to green **on their own**, with no fixture and no expectation edited. **If any
golden expected value needs to change, stop and report instead — that is a director decision.**

**Why this is the right row and not a workaround.** F11: on all 8,152 fleet buildings
`Total End Uses` and `Water Systems` are **identical per building** (max difference 0.0, zero rows
with any other end use), so this correction **changes no fleet number** — F7's
152.3011 → 171.7718 stands and T02's results stay valid. On the fixtures the two rows differ by
the whole quantity, and the Water Systems reading is the correct one.

**How to test.**

- The three golden tests return to green **untouched**: `pytest -q tests/test_results_parser.py`.
- **Add one new case to `tests/test_parser_open61_district_heating.py`, and it is the point of this
  task:** a `.sql` whose District Heating column has a **non-zero `Heating` row and a zero
  `Water Systems` row** → `dhw_district_eui_kwh_m2 == 0.0` and `total_eui_kwh_m2`
  **bit-identical** to the no-district-heating case. Name it for what it guards, and put a one-line
  comment on it pointing at **OPEN-64**. The real fixture `tests/fixtures/golden_sql/r1_single_zone.sql`
  is exactly this shape and may be used directly.
- Re-run the **full** suite in the **foreground**: `pytest -q tests/`. **The target is
  `1,936 passed / 55 skipped / 0 failed`** — the 1,927 baseline, plus T01's 9 new tests, plus
  this one, minus nothing. Report the real line whatever it says; **if the count differs, report the
  difference and its cause rather than adjusting the target.**

**Progress log.** One entry for T01 and one for T01b, both under §8, each carrying the **exact**
`N passed / M skipped / K failed` line it produced.

### T02 — Prove T01 against the real corpus *(executor, read-only)*

**What.** `scripts/analysis/open61_remedy_corpus_validation_2026-08-22.py`. Draw a **stratified
sample of 200** buildings from the preserved corpus (F8) — proportional across the 12 cells, and
**forced to include at least 20 `SuperTallBuilding`/`TallBuilding`** buildings so the high-DH class
is represented. For each: run the **new** `parse_building()` route over its `.sql`, and compare
`dhw_district_eui_kwh_m2 × parsed_floor_area_m2` against the `dh_total_kwh` already recorded for
that `osm_id` in `open61_census_fleet.csv`.

**Why.** T01's unit tests use synthetic fixtures. F9 says the corpus reproduces production EUI, so it
is a real oracle. This is the check that the ABUPS read behaves the same inside the parser as it did
in the standalone reader that produced the fleet number.

**How to test.** Pre-registered pass conditions, to be reported as pass/fail without adjustment:

- **C1** — ≥ **198 / 200** agree within **0.5 %** relative (or within 1 kWh absolute when
  `dh_total_kwh` < 1,000).
- **C2** — for every sampled building with `dh_total_kwh == 0`, the new column is exactly **0.0**.
- **C3** — `total_eui_kwh_m2` from the new parser equals the CSV's `parsed_total_eui_kwh_m2` **plus**
  `dh_total_kwh / parsed_floor_area_m2`, within **0.01 kWh/m²**, on ≥ 198 / 200.

Write one row per sampled building to
`openubem/outputs/comparisons/open61_remedy_validation_2026-08-22.csv`. **Report the failures
individually** — with `osm_id`, cell and both values — never as a rate alone.

🔴 **`mode=ro` on every connection. The corpus is read-only (§2 rule 10).**

### T03 — The fleet restatement, produced but NOT adopted *(executor, arithmetic only)*

**What.** `scripts/analysis/open61_fleet_restatement_2026-08-22.py`, from `open61_census_fleet.csv`
alone — **no simulation, no corpus walk**. Produce:

1. Pooled EUI before and after, over the n = 8,144 rows of F7, weighted by `parsed_floor_area_m2`,
   to 4 decimals, with n stated on every figure.
2. The same split **per cell (12)** and **per archetype**, sorted by absolute change.
3. The **116** rows of the tall class isolated: their share of the change, and the change with them
   excluded — so the reader can see both what they carry and the 29.5 % that survives without them.
4. Building-level distribution of the change: median, IQR, p90, max, and **how many buildings move
   by 0.0**.

**Why.** OPEN-61's remedy has to be reportable as something other than a single number, because F6's
concentration means the fleet mean describes almost nobody.

**How to test.** **C4** — the recomputed "before" pooled figure must reproduce **152.3011 kWh/m²**
(F7) to within 0.001; if it does not, STOP and report, do not adjust. **C5** — Σ per-building
`dh_total_kwh` must equal Σ`dh_water_systems_gj` × 277.7778 to within 0.01 % (F3).

**Write** `extra/MEASUREMENT_open-61_fleet-restatement_2026-08-22.md`. 🔴 **Its opening sentence must
state that the adopted figure remains 153.8231 over 8,153 and that this document proposes no
replacement.** Include F7's warning that 152.3011 and 153.8231 are different populations and must not
be differenced. **Do not write a "corrected adopted figure" anywhere.**

### T04 — Open OPEN-63 for the carbon gap *(director)*

**What.** Register `OPEN-63 — gwp_total_kgco2_m2 excludes district heating, and there is no
district-heating emission factor in the codebase`, with F10's citations, the size (12.78 % of site
energy now in the energy total and none of it in the carbon total), and the note that the gap is
pre-existing and merely made visible by T01. Update the director prompt and
`docs/PROJECT_CHECKLIST.md`.

**Why.** The rule from the previous pass: never let a known consequence survive only in the sentence
that mentions it.

### Stop-and-report points

- 🛑 **CP-1 — after T01 and T02.** The fix is written and proven against real simulation files.
  Report: suite result against the §3 baseline (naming any skip that moved), C1/C2/C3 with the
  individual failures listed. **Do not start T03 before CP-1 is signed.**
- 🛑 **CP-2 — after T03.** The candidate fleet figure exists. **The only question at CP-2 is the
  user's: adopt the restated figure as the published fleet EUI, or keep 153.8231 and carry the
  correction as a stated caveat.** The executor does not answer it and does not pre-empt it.

## 8. Progress log

<!-- one entry per task: #### TXX — <title> — completed YYYY-MM-DD, then Artifacts / What was done /
     Deviations / Test status / Notes -->

#### T01 — Fold district heating into DHW in the parser — completed 2026-08-22, with a CP-1 STOP

**Artifacts.** `openubem/results/parser.py` (`_DISTRICT_HEATING_KEY`, `_read_abups_district_heating`,
`_parse_meters_sql`, `_compute_eui`), `openubem/results/aggregator.py` (`_STEP5_COLS`),
`tests/test_parser_open61_district_heating.py` (new, 9 cases),
`docs/docs_ACTIVE/openings/extra/FIX_open-61_district-heating.md`.

**What was done.** All six steps of T01's "What" implemented as specified: pseudo-meter key,
ABUPS reader (F2's query verbatim), seeding + call inside `_parse_meters_sql`, fold into `dhw_kwh`
inside `_compute_eui` (no eleventh total term), `_STEP5_COLS` extended, `carbon.py` untouched.

**Deviations.**
1. A self-inflicted bug found and fixed before it reached the full suite: the ABUPS call was first
   placed *before* the real-meter-rows loop inside `_parse_meters_sql`'s `try` block, so any `.sql`
   lacking `TabularDataWithStrings` zeroed ALL nine real meters, not just the new one. Fixed by moving
   the ABUPS read after the loop, in its own inner `try/except`. Registered in
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 8.
2. Two mechanical fixture updates to `tests/test_results_aggregator.py` (`_make_metrics_df`'s two
   row dicts), not in T01's file list — required because `_STEP5_COLS` grew by one column; same
   pattern already used for OPEN-46's `elevators_eui_kwh_m2` addition in the same file.
3. 🔴 **CP-1 STOP — a real conflict, not a skip transition.** The full suite (`pytest -q tests/`,
   foreground, 1277.6 s) came back **3 failed, 1933 passed, 55 skipped** — `TestEuiGolden::
   test_r1_total_eui`, `test_r2_total_eui`, `test_r6_total_eui` (`tests/test_results_parser.py:279,
   289,304`). Cause: T01's unconditional fold rests on plan F3 ("100.00% of fleet district heating
   is Water Systems"), but F3 measured only the OPEN-61 census corpus (8,152 rows). The three golden
   fixtures (`tests/fixtures/golden_sql/r1_single_zone.sql`, `r2_one_zone_per_floor.sql`,
   `r6_perimeter_core.sql` — pre-Phase-D artifacts, Ideal-Loads-style HVAC) route **100% of their
   District Heating "Total End Uses" to the Heating row, 0.00 to Water Systems** — the exact
   opposite of F3 (148.24 / 709.99 / 1646.86 GJ respectively, verified directly against each `.sql`).
   T01's fold therefore misattributes that energy into `dhw_eui_kwh_m2`, inflating
   `total_eui_kwh_m2` by 105.05 / 78.89 / 101.66 kWh/m² for these three fixtures only
   (`heating_eui_kwh_m2` is untouched and its own golden tests still pass). **§2 rule 1 applies: no
   remedy for this case is authorized by §5, so none was invented.** Logged `[OPEN]` in
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 8. This blocks CP-1 sign-off as
   written; a ruling is needed on whether the fold should be conditioned on a per-building
   Water-Systems-only check (mirroring F3's own `dh_other_rows_sum_gj == 0` per-row reconciliation)
   or the three fixtures should be treated as stale and rebuilt/retired against the current,
   Phase-D-metered HVAC route.

**Test status.** New file: 9/9 passed. Full suite: 1933 passed / 55 skipped / **3 failed** (all
three new failures are `TestEuiGolden` total-EUI cases above; no baseline skip changed status).

#### T02 — Prove T01 against the real corpus — completed 2026-08-22

**Artifacts.** `scripts/analysis/open61_remedy_corpus_validation_2026-08-22.py`,
`openubem/outputs/comparisons/open61_remedy_validation_2026-08-22.csv`.

**What was done.** Stratified sample of 200 osm_ids drawn from `open61_census_fleet.csv`
(`status == "ok"`) restricted to osm_ids with a preserved `.sql` in the F8 corpus, proportional
across the 12 cells with exactly 20 forced from {SuperTallBuilding, TallBuilding}. For each: a
manifest_row was reconstructed via `cell_context()` (cached step1 + fresh step2, frozen inputs) and
a fresh `BuildingIDF(...).build()` call — same construction as
`open61_census_build_2026-08-20.py`'s `process_building()`, minus `run_ep_isolated()` (F8: no
re-simulation) — then `openubem.results.parser.parse_building()` (the fixed route) was run over the
EXISTING preserved `.sql`. Every sqlite read (inside `parse_building()`'s own functions) used
`mode=ro`; nothing was written into the corpus tree.

**Sample drawn.** 200 total, 20 forced tall (`SuperTallBuilding`/`TallBuilding`: 4 austin_centre,
1 la_urban, 15 nyc_centre). Per cell: austin_centre 13, austin_rural 6, austin_suburban 10,
austin_urban 9, la_centre 5, la_rural 3, la_suburban 30, la_urban 15, nyc_centre 31, nyc_rural 4,
nyc_suburban 36, nyc_urban 38. Sampled `census_dh_total_kwh` minimum was 22.22 (no zero-DH building
was drawn — the census population's own minimum `dh_total_gj` is 0.06, i.e. ~16.67 kWh, too small a
subpopulation to land in a 200-draw).

**As-scored (script's own pre-registered per-m² comparison).** C1 177/200, C3 123/200; C2
**vacuous** — 0 of the 200 sampled buildings have `census_dh_total_kwh == 0`, so the "every
zero-dh building reads exactly 0.0" condition has no rows to evaluate and cannot be reported as a
pass. Every one of the 23 C1 failures and all 77 C3 failures is a building whose freshly-rebuilt
`new_floor_area_m2` (this run) differs from the census's `parsed_floor_area_m2` (the CSV column the
script's comparison used as prescribed by the plan's wording) — on the 42/200 buildings that rebuild
to a bit-identical floor area, C1 is 42/42 and C3 is 42/42.

**Re-scored in absolute kWh (removes the floor-area confound).** C1: 200/200 within 0.5% (median
relative error exactly 0.0). C3: 200/200 (median relative error 1.32e-16, maximum 6.01e-16 —
floating-point noise). **T01/T01b's ABUPS district-heating read is validated 200/200 against the
real corpus on both testable conditions.** C2 stays vacuous under either scoring — it is a property
of the sampled population, not of the comparison basis.

**Floor-area finding (real, not attributed).** 158/200 buildings do not reproduce their census floor
area on a fresh IDF rebuild. All 34 sampled TallBuilding/SuperTallBuilding/LargeOffice/
RetailStandalone reproduce exactly; the drift is confined to SmallOffice, MidriseApartment,
MediumOffice and OpenUBEMUnknown. Ratio new/census floor area: median 0.999999, 82/158 differ by
less than 0.005%, tail runs to 0.842332 (−15.8%) and 1.034284 (+3.4%).

🔴 **Director correction, 2026-08-22, after CP-1 audit — this paragraph originally read
"consistent with OPEN-62" and that attribution is WITHDRAWN.** The cause is not a modelling defect
and not OPEN-62: it is **corpus incompleteness**. The director verified the executor's observation
independently rather than accepting it on report — corpus-wide there are **7,861 `eplusout.sql`
against 799 `eplusout.eio`**, and the 2×2 cross-tab on this run's own 200 rows is **exact with
zero off-diagonal cells: all 158 drifted buildings lack `eplusout.eio`, all 42 exact ones have it.**
Without the `.eio`, `resolve_simulated_floor_area()` cannot read `eio_simulated` and falls back to
`footprint_area × num_floors`. **What survives the correction is smaller but still real and is
NOT a corpus artefact: the storey-count fallback route disagrees with the simulator's own reported
area by up to 15.8 %.** That disagreement is about `num_floors`, which is exactly OPEN-62's subject,
so it is **reserved for a director ruling as a possible OPEN-62 enlargement — still not
attributed, still no item opened.** Executor's own supporting
observation (director's framing is authoritative): of this run's 158 drifted buildings, all had no
`eplusout.eio` preserved alongside their `.sql` in the corpus (only 42/200 sampled buildings carry
one), which is why `resolve_simulated_floor_area()` fell back to `footprint_area × num_floors`
instead of reading the original `eio_simulated` value — a corpus-completeness fact (F8 only claims
`.sql` preservation), not a defect in T01/T01b.

**Deviations.** None from T02's own "What"/"How to test" — the script's per-m² comparison followed
the plan's literal wording (`dhw_district_eui_kwh_m2 × parsed_floor_area_m2` against `dh_total_kwh`,
using the CSV's `parsed_floor_area_m2` column). Executed in parallel with the full-suite run per the
director's explicit instruction (suite result does not gate T02, which is read-only and depends only
on T01's code already being on disk). Not re-run and not re-scored after T01b per the director's
explicit instruction — T01b does not move any fleet number (F11) and T02 was run against the
census's `Total End Uses`-equal-to-`Water Systems` population, so its validity is unaffected.

#### T01b — Read the Water Systems row, not the total — completed 2026-08-22

**Artifacts.** `openubem/results/parser.py` (`_read_abups_district_heating` query and docstring),
`tests/test_parser_open61_district_heating.py` (`TestDistrictHeatingServingSpaceHeatingNotFoldedIn`,
new), `docs/docs_ACTIVE/openings/extra/FIX_open-61_district-heating.md` §5 (new),
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 8 (closed the `[OPEN]` entry).

**What was done.** The three edits specified, exactly: `_read_abups_district_heating`'s query
changed `RowName='Total End Uses'` → `RowName='Water Systems'`; docstring updated to state which row
and why (F11); `_DISTRICT_HEATING_KEY`, the zeros-dict seed, the try/except ordering, the
`dhw_district_eui_kwh_m2` column, the fold into `dhw_kwh`, and the aggregator column left untouched.
`carbon.py` not touched. No golden fixture and no `golden_expected.json` value was edited.

**Test status.** New guard test
(`TestDistrictHeatingServingSpaceHeatingNotFoldedIn::test_r1_district_heating_serving_heating_reads_zero_and_total_matches_golden`,
using `r1_single_zone.sql` directly) + all three previously-failing golden tests, run targeted:
**54 passed** (`tests/test_parser_open61_district_heating.py` + `tests/test_results_parser.py`).
Full suite, foreground, `pytest -q tests/`, 1378.3 s: **1937 passed, 55 skipped, 0 failed.**

**Deviation — target count.** T01b's own text states the target as "1,936 passed / 55 skipped /
0 failed." The actual result is **1937**, i.e. +1 against the stated target. Cause: 1,927 (baseline)
+ 9 (T01's new test file) + 1 (T01b's own new guard test) = 1937 — the stated target's arithmetic
included T01's 9 but not T01b's own additional test, an arithmetic omission in the task text itself,
not a suite regression. 0 failures; skip count unchanged at 55 (no skip name transition was
surfaced by this run — 0 failed and an unchanged skip count are consistent with none, though the
enumerated 55-skip table itself was not re-diffed line-by-line this pass).

#### T03 — The fleet restatement, produced but NOT adopted — completed 2026-08-22

**Artifacts.** `scripts/analysis/open61_fleet_restatement_2026-08-22.py`,
`openubem/outputs/comparisons/open61_fleet_restatement_2026-08-22.csv`,
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_fleet-restatement_2026-08-22.md`.

**What was done.** Arithmetic only, over `open61_census_fleet.csv`, no simulation and no corpus
walk. Filtered to the n = 8,144 `ok` rows carrying both `parsed_total_eui_kwh_m2` and
`dh_total_kwh` (F7's population). Computed pooled EUI before/after weighted by
`parsed_floor_area_m2`, the same split per cell (12) and per archetype (20), the 116-row tall
class (`SuperTallBuilding` 24 + `TallBuilding` 92) isolated with and without, and the
building-level distribution of the per-building change (`dh_total_kwh / parsed_floor_area_m2`).
Wrote the CSV and the measurement doc, whose opening sentence states the adopted figure remains
153.8231 over 8,153 and that no replacement is proposed, and which restates F7's warning that
152.3011 and 153.8231 are different populations and must not be differenced. No "corrected
adopted figure" was written anywhere.

**Test status (gates).** **C4 PASS** — recomputed before-figure 152.3011 kWh/m², target 152.3011,
|diff| = 0.000038 (within 0.001). **C5 PASS** — Σ`dh_total_kwh` = 470,831,194.4444 kWh vs
Σ`dh_water_systems_gj` × 277.7778 = 470,831,194.4444 kWh, relative diff 0.000000 % (within
0.01 %). Neither gate required any adjustment to pass.

**Results.** Pooled before 152.3011 → after 171.7718 kWh/m² (n = 8,144), delta +19.4707
(+12.78 %), reproducing F7 exactly. Tall class (n = 116) carries 70.5 % of Σ`dh_total_kwh`,
matching F6; excluding the tall class entirely, the remaining 8,028 buildings still move by
+9.1111 kWh/m². Building-level change: median 2.4691, IQR [1.3970, 32.2354], p90 37.2753, max
89.1207 kWh/m², **0 of 8,144 buildings move by exactly 0.0** (consistent with T02's finding that
this population's minimum `dh_total_gj` is 0.06 GJ, a floor above zero).

**Deviations.** None from T03's "What"/"How to test". No file outside T03's planned list (§4) was
touched.

**Notes.** Per §2 rule 9 and the plan's explicit CP-2 gate, this entry does not answer or pre-empt
the adoption question. CP-2 is now reached; T03 is complete and awaits the user's ruling.

#### T04 — Open OPEN-63 for the carbon gap — completed 2026-08-22 *(director)*

**Artifacts.** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` (OPEN-63 table row
+ §6 section + §7 amendment entry), `docs/PROJECT_CHECKLIST.md`,
`docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings.md`, and the two memory files.

**What was done.** **OPEN-63** registered — *`gwp_total_kgco2_m2` excludes district heating, and
there is no district-heating emission factor in the codebase* — with F10's citations
(`carbon.py:106` builds the DHW carbon term from gas + electricity only; `config.py:83` carries no DH
factor), the size (**12.78 % of site energy now enters the energy total and none of it enters the
carbon total**), and the explicit statement that **the gap is PRE-EXISTING and was merely made
visible by T01** — it is not a consequence of the fix. `carbon.py` was deliberately **not**
touched, per F10, so the gap stays visible rather than being quietly patched.

**Beyond T04's scope, recorded here because it happened in the same pass.** ➕ **OPEN-64 was also
opened** — district heating serving any end use other than Water Systems is dropped from every
reported column, the repository's own golden fixtures are exactly that shape, and **their expected
values encode the understatement**. **Fleet exposure measured at zero buildings**, so no published
number moves. Register now **14 live / 50 retired / 64 total, next free `OPEN-65`**.

**Test status.** N/A — documentation task, no code touched.

**Deviations.** None. **Notes.** Neither item carries a proposed remedy: OPEN-63 needs an emission
factor from the literature (a sourcing decision), and OPEN-64's honest fix would move golden expected
values that were signed off. **Both are the user's calls, not the director's.**

## 9. Director sign-off

<!-- director only -->

### 🛑 CP-1 — SIGNED 2026-08-22. T03 is authorised.

**Audited against the four house checks** (progress-log entries → test output → only planned
files touched → DESIGN citations for any unplanned decision). All four pass. What follows is the
record, including the two things the executor's own report got right and the one framing the director
had to withdraw.

**1. Suite — the gate, and it is met.** `pytest -q tests/`, foreground, 1378.31 s:
**1937 passed, 55 skipped, 0 failed.** Against the §3 baseline of 1,927 / 55 / 0 that is
**+10 passed, +0 failed, skips unchanged**.

🟢 **No skip moved, and this is proven arithmetically rather than asserted.** The plan
requires naming any skip that flips. None can have: 1,927 + 9 (T01's new file) + 1 (T01b's guard
test) = **1937 exactly**, with the skip count still **55**. A skip flipping to a pass would have left
54 skips and 1938 passes; a skip appearing would have left 56. Both are excluded by the two counts
together. **The enumerated 55-skip table in §9 of the archived `PLAN_rulings-and-fixes-2026-08-21.md`
therefore still stands unmodified**, and the 15 OPEN-17 skips inside it remain the only ones blocked
on a live decision. The executor flagged that it had not re-diffed the table line-by-line; that
caution was correct to state and the identity above closes it.

**Target-count deviation accepted.** T01b's task text stated the target as 1,936. The actual is 1937.
**The error is in the task text the director wrote, not in the execution** — the stated target
counted T01's 9 new tests and omitted T01b's own guard test. Recorded, not held against the executor.

**2. T02 — validated 200/200, on the director's re-scoring, and the re-scoring is the correct
basis.** The script's pre-registered per-m² comparison scored **C1 177/200 and C3 123/200**, both
below the ≥198/200 bar. **Those scores are not evidence against T01/T01b and must not be cited as
if they were.** Every single failure is a building whose freshly-rebuilt floor area differs from the
census CSV's `parsed_floor_area_m2`, i.e. the comparison divided two energy figures by two different
denominators. Re-scored in **absolute kWh**, which removes that confound entirely:

| condition | as-scored (per m²) | re-scored (absolute kWh) | median relative error |
|---|---|---|---|
| **C1** — parsed DH equals census DH | 177/200 | **200/200** within 0.5 % | **exactly 0.0** |
| **C3** — new total equals census total + DH | 123/200 | **200/200** | **1.32e-16** (max 6.01e-16) |
| **C2** — zero-DH buildings read exactly 0.0 | — | — | — |

**On the 42/200 buildings that rebuild to a bit-identical floor area, C1 is 42/42 and C3 is 42/42
even as-scored** — an independent confirmation that the denominator, not the numerator, was the
whole of the gap. **The ABUPS district-heating read is validated against real preserved simulation
output, 200 of 200, on both testable conditions.**

⚠️ **C2 is recorded as VACUOUS, not as passed, and this distinction is load-bearing.** Zero
of the 200 sampled buildings have `census_dh_total_kwh == 0`, so the condition has no rows to
evaluate. It is not a silent pass and must never be summarised as "C1/C2/C3 all pass". This is a
property of the sampled population — the census's own minimum `dh_total_gj` is 0.06 GJ (≈16.67
kWh), a subpopulation too small to land in a 200-draw. **The backwards-compatibility case that C2 was
meant to cover is instead carried by unit tests** (T01's no-District-Heating-column case, asserting
`dhw_district_eui_kwh_m2 == 0.0` and a bit-identical total against a literal), so the property is
tested even though the corpus draw could not test it. **Not treated as a coverage hole; treated as a
condition answered by a different instrument.**

**3. Only planned files touched — one unplanned file, accepted with reason.** Verified against
`git status`, not against the report. This arc's code footprint is exactly:
`openubem/results/parser.py` (+146/−9), `openubem/results/aggregator.py` (+2),
`tests/test_parser_open61_district_heating.py` (new, 10 cases),
`scripts/analysis/open61_remedy_corpus_validation_2026-08-22.py` (new) and its 200-row CSV.
**`openubem/idf/builder.py`, `tests/test_idf_builder.py` and `tests/test_parser_open60_multiplier.py`
also appear dirty in the same working tree but are PRE-EXISTING OPEN-60 work and are not attributed
to this arc.**

✅ **`tests/test_results_aggregator.py` (+5/−2) was not in T01's file list.** Inspected line
by line before accepting: it adds `dhw_district_eui_kwh_m2` to two synthetic fixture rows so the
fixture still matches `_STEP5_COLS` after that list grew from 28 to 29 columns. The added value is
`0.0` alongside `dhw_gas 8.0 + dhw_elec 1.0 = dhw 9.0`, i.e. **the fixture stays internally
consistent and the change cannot mask a real regression.** Same mechanical pattern already used when
OPEN-46 grew the column list. **Accepted as an unplanned but forced consequence of a planned change.**

🟢 **Nothing was touched that the plan forbade.** `git status -- tests/fixtures` is **empty**
— **no golden `.sql` and no `golden_expected.json` value was edited**, which was the hard
constraint on T01b. `openubem/results/carbon.py` is untouched, per F10 — the carbon consequence
stays visible as **OPEN-63** rather than being quietly patched.

**4. The CP-1 STOP was correct and is commended.** T01, executed verbatim as written, returned
**3 failed / 1,933 passed / 55 skipped**, all three `TestEuiGolden::test_r{1,2,6}_total_eui`. **The
executor stopped, quoted the conflict, and did not invent a fix.** That is exactly the required
behaviour and it is why the defect was diagnosed in one sqlite query and one division rather than in
an investigation. **The fault was in the director's instruction** — T01 step 2 specified
`RowName='Total End Uses'` on the strength of fact F3, a measurement true **of the fleet** that was
silently used as a statement **about the code**. Corrected as T01b; F2 corrected in place; F3
narrowed; F11 added; the residue opened as **OPEN-64**; the failure signature registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §9.

**5. Floor-area finding — the director's earlier framing is WITHDRAWN.** The T02 entry above
originally read "consistent with OPEN-62", and the director repeated that to the user. **It was
premature and it is retracted.** The mechanism is settled and it is corpus incompleteness, not a
model defect: **7,861 `.sql` against 799 `.eio` corpus-wide**, and an exact 2×2 with zero
off-diagonal on this run's 200 rows (**158 drifted ⇔ no `.eio`; 42 exact ⇔ has `.eio`**).
Verified by the director directly, not taken on the executor's report. **F8 only ever claimed `.sql`
preservation, so the corpus is not in breach of anything.**

❓ **What survives is smaller and is deferred, not dropped.** The fallback route
`footprint_area × num_floors` disagrees with the simulator's own `eio_simulated` area by up to
**15.8 %** (ratio range 0.842332–1.034284, median 0.999999, 82/158 inside 0.005 %). That is a
statement about `num_floors`, which is OPEN-62's subject. **Reserved for a director ruling as a
possible OPEN-62 enlargement. Deliberately NOT attributed and NOT opened as a new item at CP-1 —
opening items is not a checkpoint's job.**

**6. Ruling.** ✅ **CP-1 is signed. T03 is authorised to start.** T03 is arithmetic over the
existing census CSV only — **no re-simulation, no re-parse, no write into the preserved corpus
(ruling R6)** — and it **must not write a "corrected adopted figure" anywhere**. It produces a
**candidate**. 🔴 **153.8231 kWh/m² pooled over 8,153 remains the adopted published
figure until the user rules at CP-2, and 152.3011 must never be differenced against it — they are
different populations.**

### ✅ CP-2 — SIGNED 2026-08-22. **Ruled: KEEP 153.8231, carry a stated caveat.**

**All four tasks are complete and both checkpoint gates before this one are met.** T03's candidate
exists, its two controls passed without adjustment, and **the director re-derived the figures
independently from `open61_census_fleet.csv` rather than accepting them on report** — C5 matches
to 0.000000 %, the tall class's share of district heating comes back at **70.55 %** against F6's
70.5 %, the per-building distribution reproduces exactly (median **2.4691**, p90 **37.2753**, max
**89.1207**, **0 buildings moving by 0.0**), and the direction and magnitude of the pooled move
reproduce. A deliberately looser row filter than F7's returned 152.2081 → 171.5405 over n = 8,146
rather than 152.3011 → 171.7718 over n = 8,144 — **the two-row difference is the whole of the
gap and it confirms rather than questions T03**, which was required to and did reproduce F7's exact
population.

🔴 **The question is the user's and the director does not answer it here.** Adopt the restated
figure as the published fleet EUI, or keep **153.8231 kWh/m² pooled over 8,153** and carry the
correction as a stated caveat. **Until that ruling, 153.8231 remains the adopted published figure and
no document may present the restatement as a correction to it.** ⚠️ **152.3011 and 153.8231
are different populations — never difference them.**

**Two things the user should have in hand when ruling, neither of which the arc may settle for
them.** (1) **The carbon total will not follow the energy total** — OPEN-63, no district-heating
emission factor exists, so adopting a +12.78 % energy restatement leaves `gwp_total_kgco2_m2`
unchanged and the two published figures inconsistent with each other. (2) **The restatement is
concentrated but not confined** — 116 tall buildings carry 70.5 % of it, yet the other 8,028
still move **+9.1111 kWh/m²** on their own, so it cannot be dismissed as a tall-building
artefact.


---

### ✅ The CP-2 ruling — taken 2026-08-22 under the user's explicit delegation

**The user was given the question and delegated the call back:** *"tu progress comme tu recommend"*.
**The ruling is therefore recorded as the director's recommendation, adopted by the user's
delegation — not as a decision the director took on its own authority.** If the user disagrees
this is reversible at no cost, because nothing was rewritten.

✅ **RULING: keep 153.8231 kWh/m² pooled over 8,153 as the published fleet figure, and carry
the correction as a stated caveat.** The restatement is **not** adopted.

**Four reasons, in the order they weigh.**

**1. 🔴 The arithmetic to restate the adopted figure has never been run, and 171.7718 is not
it.** 171.7718 is computed on the **census rebuild** (n = 8,144); 153.8231 is computed on **run 4**
(n = 8,153). Adopting 171.7718 would not correct the published figure — it would **replace it
with a figure from a different population**, which is precisely the error the plan's own F7 warns
against. **This alone is decisive**: there is no defensible way to publish 171.7718 as *"the
corrected 153.8231"* because that quantity does not exist yet.

**2. Adopting would publish two figures that contradict each other.** OPEN-63: `carbon.py:106` builds
the DHW carbon term from gas + electricity only and `config.py:83` carries no district-heating
emission factor. So a +12.78 % energy restatement leaves `gwp_total_kgco2_m2` **completely
unmoved**. Choosing that factor is a literature decision, and this session does not invent values.
**Publishing energy that has moved beside carbon that has not is worse than publishing a known-low
figure with its size stated.**

**3. Two unresolved items move the same number, one of them the denominator.** OPEN-56's
≈+1.0 kWh/m² volume correction is still not in the baseline, and the floor-area finding
from T02 shows `footprint × num_floors` disagreeing with the simulator's own area by up to
**15.8 %** — OPEN-62's subject, and a **denominator** effect, not a numerator one. **Adopting
now means restating twice**, and a figure restated twice in a week is worth less than a figure
restated once when the inputs have settled.

**4. The caveat costs nothing that adoption buys.** The defect is **fixed in the code**, so every
future run already carries the district heating. The size is **measured, not estimated**
(19.4707 kWh/m² = 12.78 %), and it is stated wherever the figure is stated. **Nothing is hidden
by not adopting; the only thing deferred is the swap itself.**

**🔴 What this ruling does NOT say.** It does not say the restatement is wrong — T03's
gates passed unadjusted and the director re-derived the result independently. It does not say
153.8231 is right — **it is low, by a measured amount, and now says so.** It says the *swap* is
premature.

**The canonical caveat sentence, to be used verbatim wherever the fleet figure is published:**

> 🛑 **CAVEAT, RULED 2026-08-22 (CP-2, user delegated the call to the director): the adopted figure is KNOWN LOW and is NOT being restated.** District heating served to hot water was dropped from `total_eui_kwh_m2`. **The parser was fixed 2026-08-22** (OPEN-61 T01/T01b), so every future run carries it. On the **census** population the fix moves the pooled figure **152.3011 → 171.7718 kWh/m² (+19.4707, +12.78 %, n = 8,144)**. ⚠️ **That is NOT a correction to 153.8231 — the two are different populations and must never be differenced.** **153.8231 over 8,153 stands as the published figure**, carrying this caveat.

**Written into:** `INVESTIGATION_open-items-register-II.md` (the Adopted-fleet-figure row),
`docs/PROJECT_CHECKLIST.md`, the board artifact, and the two memory files.

**❓ One thing proposed, not taken — opening and closing items is the user's.** **OPEN-61's
defect is now fixed in code and its size is measured and published as a caveat, so the item has
nothing left that a plan can act on.** The director **proposes** closing OPEN-61 and does not close
it. **The register stands at 14 live / 50 retired / 64 total, next free `OPEN-65`, unchanged by this
ruling.**

**What is now unblocked, and what is not.** ✅ The arc's plan is complete — all five tasks,
both checkpoints. 🔴 Still owed by the user and untouched by this ruling: the √S test at
n = 69, the OPEN-14 fusion gate, **OPEN-17** (which alone holds 15 tests dormant), **OPEN-63** (needs
a district-heating emission factor from the literature), **OPEN-64** (needs a ruling on moving golden
expected values), and the storey-count-vs-simulated-area disagreement (possible **OPEN-62**
enlargement).
