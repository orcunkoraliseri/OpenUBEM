# PLAN — fix the seven open items (OPEN-67 … OPEN-73) — 2026-09-30

## 1. Header

- **Slug:** `seven-items-2026-09-30`
- **Date:** 2026-09-30. **Author:** director (manager session).
- **Authority:** user, 2026-09-30, verbatim *"yes yes keep going"*, answering: "should I write one plan
  that fixes all seven and turns the switch back off? I recommend yes."
- **Scope:** OPEN-67 laundry (7 runs), OPEN-68 sliver (6), OPEN-69 sizing divergence (13 runs, 7 buildings),
  OPEN-70 non-convex shading (1), OPEN-71 out of memory at 32G (1), OPEN-72 missing prototype folder
  (10 tests), OPEN-73 abort switch (2 tests).
- **Not included:** adopting a new published figure. Buildings that recover are reported as additions;
  folding them into n is CP-C, the user's.
- **Pointers:** register `docs/docs_DONE/openings/INVESTIGATION_open-items-register-II.md` §2, §6
  (lines 1193-1228); predecessor `implemenation/previous/PLAN_three-rulings-2026-09-30.md` (T05 classes, T06 recipe);
  `implemenation/previous/PLAN_tests-and-crashes-2026-09-30.md` (T01 suite, T03 OPEN-72/73).

## 2. Hard rules for the executor

1. Execute your task only. Do not propose alternatives. If this plan or a cited line is wrong, STOP and quote it.
2. **No compute on the Speed login node.** Login node = `mkdir`, `scp`, `tar`, `squeue`, `sacct`, `sinfo`, `ls`.
   Every remote command goes through a `_ssh()` wrapper running `bash -lc` (port it from
   `scripts/cluster/t08_harvest_results.py:104`).
3. **Simulations never run locally and never one by one.** Any EnergyPlus run → one
   `sbatch --array=1-N%32 --time=7-00:00:00` on Speed. State case count and width before submitting.
   Local CPU work ≤ 10 processes. Dead-task check (CLAUDE.md) before cancelling anything. Never touch
   another job of the account.
4. **Never delete by exclusion** in any live folder.
5. No code comments. No `.py` under `docs/`. CSVs/JSON → `openubem/outputs/comparisons/` (flat).
6. Never edit root `main.py`, OVERVIEW or DESIGN docs.
7. One progress-log entry per task under §8, in your task's placeholder only.
8. After fixing any error, update its entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
   (drop `[OPEN]`, add the fix and `file:line`), house format.
9. A harvest counts a run only if `terminal == completed` **and** `parse_status == success`.

## 3. File layout

| Path | Task | Kind |
|---|---|---|
| `openubem/config.py` (lines 49-54, 123) | T01 | edit |
| `scripts/analysis/seven_items_diag_2026-09-30.py` | T02 | new |
| `openubem/outputs/comparisons/seven_items_diag_2026-09-30.csv` | T02 | new |
| `scripts/analysis/seven_items_trial_2026-09-30.py` | T03 | new |
| `openubem/outputs/comparisons/seven_items_trial_2026-09-30.csv` | T03 | new |
| code files named at CP-B | T04 | edit |
| `scripts/analysis/seven_items_rerun_2026-09-30.py` | T05 | new |
| `openubem/outputs/comparisons/seven_items_rerun_2026-09-30.csv`, `seven_items_summary_2026-09-30.json` | T05 | new |

## 4. Dependency decisions (pinned)

- **D1 — OPEN-73.** `PREP_ABORT_ON_FAILURE = False` (`openubem/config.py:123`), as its plan
  (`docs/docs_DONE/TechTransfer/implementation/PLAN_techtransfer-block2-2026-09-17.md:159`) and
  `tests/test_prep_gate.py:47` specify. No script under `scripts/` reads the flag (director grep, 2026-09-30);
  the only reader is `openubem/simulation/parallel.py:270`.
- **D2 — OPEN-72.** The prototype folder moved; it exists at
  `C:\Users\o_iseri\Desktop\NEXA-desktop\Content\00.BaselineBuildings_NUs_v231` (director `ls`, 2026-09-30),
  the folder every adopted-run recipe already sets through `OPENUBEM_BASELINE_IDF_DIR`
  (`scripts/analysis/open38_fix_rerun_2026-09-30.py:119`). Fix = the default at `openubem/config.py:53`
  points there. No published number moves (the adopted runs set the variable to the same folder).
- **D3 — Starting IDFs.** The 28 failing cases were built by T06c of the predecessor plan, current code,
  full outputs: `%TEMP%/ubem_validation/open38_fix_rerun_2026-09-30_full/build_manifest.csv` (`idf_path`)
  with the 28 = rows of `openubem/outputs/comparisons/open38_fix_rerun_2026-09-30.csv` where `group` in
  (`open38`,`oom`) and `terminal != completed`. EPWs: that staging folder's `weather/`. Speed recipe:
  `REMOTE_SBATCH = /speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t07.sbatch`,
  `--export=FLEET_DIR=<remote dir>` (`open38_fix_rerun_2026-09-30.py:34-36`, `:246-249`).
- **D4 — Which fixes may touch the adopted fleet.** A fix that changes no adopted (`auto`) building except
  the 6 missing ones goes in without further question. A fix that would change completing adopted buildings
  must be sized first (T02) and those buildings re-run in T05 with the fix.
- **D5 — Stop line.** Per CLAUDE.md "do not chase the last fraction": each item gets **one** trial round
  (T03). An item no trial variant cures is closed as a *known limitation* with its measured count, not
  chased further.

## 5. Facts with line citations

- F1 — Crash rows (28 runs, 19 buildings) and classes: `open38_fix_rerun_2026-09-30.csv` `cause_class`;
  per-case detail (zone, surface, temperature, gains, HVAC): `open38_diagnosis_2026-09-30.csv`.
- F2 — OPEN-69 pattern (director read of F1): 12 of 13 runs are `la_rural` Warehouses; the failing surface
  is the **storey-2 floor or roof** of the core/whole zone (`BLOCK CORE_ZONE STOREY 2 FLOOR 0001_1`) at
  −104 to −163 °C or +210 °C, zones 784-22,444 m². The 13th is `la_centre` `way/428015178`, floor mode,
  storey-5 roof. 4 of the 7 buildings fail in `auto` and are missing from the 8,139.
- F3 — OPEN-68: all 6 are `la_rural` `fast_zone` perimeter zones of 0.71-1.29 m² floor; the reroute gate
  `_coreperim_has_tiny_zone_area(min_area=_TINY_ZONE_AREA_M2)` (`openubem/idf/surfaces.py:274`, used at
  `:764`) uses 0.5 m², so it does not catch them.
- F4 — OPEN-67: `LAUNDRYROOMFLR1` of the `SmallHotel` prototype, no HVAC by prototype design, gas dryer
  46,287 W + water-heater ambient losses (`extra/MEASUREMENT_open-38_laundryroom-mechanism.md` §3);
  `layout_assign` only. The unmodified DOE prototype runs with the same zone, so something the substitution
  changes (constructions, dryer fractions, or scale) differs.
- F5 — OPEN-70: `la_rural` `way/472961047`, `auto`; `.err` carries `DetermineShadowingCombinations: There
  are 2 ...` (non-convex casting surface); 2 other buildings with the same warning complete.
- F6 — OPEN-71: `la_centre` SecondarySchool `way/319507579`, `auto`; out of memory at 6 GB (job 1401699) and
  `FAILED` at 32 GB (job 1403424).

## 6. Tasks

### T01 — OPEN-72 and OPEN-73: two config lines *(executor, code, CPU only)*

**What.** D1 and D2 in `openubem/config.py` only.
**Why.** User ruling (header); 12 red tests.
**How.** Line 123 → `False`. Line 53 default → `r"C:\Users\o_iseri\Desktop\NEXA-desktop\Content\00.BaselineBuildings_NUs_v231"`.
Update the two `[OPEN]` entries at `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1970` and `:1972`
(drop `[OPEN]`, state the fix and `openubem/config.py:<line>`).
**How to test.** `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_prep_gate.py
tests/test_sim_parallel.py tests/test_pv_injection.py tests/test_scenario_campaign_wiring.py` → 0 failed,
0 errors; `git diff --stat openubem/` shows `config.py` only. STOP and report.

### T02 — Diagnose OPEN-67 … OPEN-71 before any trial *(executor, CPU only, no simulation)*

**What.** One CSV row per measured item below; no code change.
- (a) OPEN-69: for the 7 buildings (F2) and for **every `la_rural` Warehouse in the adopted 8,139 that
  completes** (controls): the failing surface (or, for controls, the same storey-2 floor/roof surface): its
  construction and every layer (name, thickness, conductivity, density, specific heat, or NoMass R), outside
  boundary condition and partner surface, area, vertex count, tilt; the zone's floor area, volume, ceiling
  height, `Zone Multiplier`; the building's `num_floors`, `height_m`, storey height. Then the column(s) whose
  values do not overlap between failing and completing. From the IDFs (D3; controls from the adopted run's
  IDFs or rebuilt locally, D5 recipe of the predecessor plan) and the `.eio`.
- (b) OPEN-67: for the 7 cases, the laundry zone's `GasEquipment` "Dryer" fields (design level, Fraction
  Latent, Radiant, Lost) and its surface constructions, **side by side with the unmodified DOE prototype**
  `ASHRAE901_HotelSmall_STD2022_Buffalo.idf` in D2's folder. Name every field that differs.
- (c) OPEN-68: over the adopted 8,139 (`auto`), count the buildings whose smallest zone floor area is in
  [0.5, 2.0) m² — the ones a 2.0 m² threshold would newly reroute. Zone floor areas from the adopted run's
  SQL `Zones` table as read by `scripts/analysis/open65_reparse_2026-09-29.py` (reuse its source paths).
  Report the count and their osm_ids.
- (d) OPEN-70: the full first Severe/Fatal block of the `.err`, the casting surface named, its vertex count
  and whether it is a wall, roof or neighbour shading surface; the IDF's `ShadowCalculation` object as written.
- (e) OPEN-71: `sinfo -o "%P %m %c"` (login node, query only) for partition `ps`; the IDF's zone count,
  surface count, and `Output:Variable` count.
**How to test.** Every item (a)-(e) has a value; (a) names the separating column or states "none separates"
with the table; counts measured, not estimated. STOP and report (CP-A).

### CP-A (director) — choose the trial variants from T02, then write T03 here.

**CP-A findings (director, 2026-09-30, read of the fetched `.err` under
`%TEMP%/ubem_validation/open38_fix_rerun_2026-09-30_full/fetched/out/<mode>__<cell>__<stem>/eplusout.err`):**
- A1 — 27 of the 28 runs die the same way: an inside-surface heat balance diverging in one zone
  (`Temperature (high) out of bounds (213.50]` / `(low) … [-236.01]` in run period, or
  `CalcHeatBalanceInsideSurf: The temperature of -13938.37 C … during warmup` for the laundry). That covers
  OPEN-67, OPEN-68, OPEN-69 and **OPEN-70**. For OPEN-70 the non-convex line is a non-fatal Severe; the kill is
  `out of bounds` in `WAY/472961047_F1_PERIM2` at 08/04 16:20. Every IDF has `Timestep, 6`, and none sets
  `ZoneAirHeatBalanceAlgorithm` (so the default applies).
- A2 — **OPEN-71 is not out of memory at 32 GB.** Its fatal is
  `CheckForRunawayPlantTemps: Simulation terminated because of run away plant temperatures, too hot`
  (`OPENUBEM_HW_LOOP HOT WATER LOOP`, 09/28 17:40). The `.err` has 257 kB, 21 non-convex casting surfaces and
  `Too many figures [>15000]`. Memory stays at 32G for this case only because it is known to fit.
- A3 — OPEN-68: a 2.0 m² threshold would newly reroute 41 adopted buildings, none below 0.5 (T02 c). Because
  of D4, the 2.0 m² reroute is trialled only on the 6 failing runs. Adoption waits for CP-B.
- A4 — Choice of variants: A1 says the cure is numerical and zone-local, so one uniform set is applied to all 28. Each
  variant is a text edit of the existing T06c IDF (no rebuild), except S1:
  - **V1** `Timestep` 6 → 20.
  - **V2** add `ZoneAirHeatBalanceAlgorithm, AnalyticalSolution;` (replace the object if present).
  - **V3** V1 + V2.
  - **S1** (the 6 OPEN-68 runs only): rebuild in `fast_zone` with `openubem.idf.surfaces._TINY_ZONE_AREA_M2 = 2.0`
    set in the trial script (monkeypatch, no code edit), the T06c recipe otherwise unchanged.
  - **Controls:** 8 cases that complete in `open38_fix_rerun_2026-09-30.csv` (`terminal == completed`,
    `parse_status == success`, `mode == auto`). Take both storey-2 Warehouses `way/472961091` and `way/472961164`
    if present in `build_manifest.csv`. Fill the rest with the first rows (sorted by `stem`) of 6 distinct
    `archetype_id`s. Each control runs as V0 (unchanged), V1, V2 and V3, which sizes the shift a variant would cause on
    completing buildings (D4).

### T03 — One trial round on Speed *(executor; the director submits)*

**What.** Build and stage 28×3 (V1-V3) + 6 (S1) + 8×4 (controls) = **122 cases**, upload them, and STOP before
`sbatch`. After the director submits and the array finishes, harvest them (T03b).
**Why.** CP-A A4; D5 (one round).
**How (T03a — stage).** New `scripts/analysis/seven_items_trial_2026-09-30.py`, copying
`scripts/analysis/open38_fix_rerun_2026-09-30.py` for paths, `_ssh()`, tar, scp and `_fetch`:
- `WORK = %TEMP%/ubem_validation/seven_items_trial_2026-09-30` and
  `REMOTE_DIR = /speed-scratch/o_iseri/openubem/fleets/seven_items_trial_2026-09-30`.
- Case name `<variant>__<mode>__<cell>__<stem>`.
- The 28 = D3 rows. Source IDFs = D3 `idf_path`.
- Text edits apply only to the named objects. Assert that each edit changed exactly one object (or added one).
- EPW selection as in the source script.
- `stage` subcommand: writes `cases.csv` (name, variant, mode, cell, stem, osm_id, archetype_id, group
  ∈ {failing, sliver_s1, control}) and `fleet.lst`, uploads, then prints the exact command
  `sbatch --array=1-122%32 --mem=32G --time=7-00:00:00 --export=FLEET_DIR=<REMOTE_DIR> <REMOTE_SBATCH>`
  without running it.
- STOP and report the case count by group.
**How (T03b — harvest, after director notice).**
- `harvest` subcommand: fetch as in the source script and parse with the same parser.
- Write `openubem/outputs/comparisons/seven_items_trial_2026-09-30.csv` with one row per case: name, variant,
  group, osm_id, mode, `terminal`, `parse_status`, `total_eui_kwh_m2`, the first Severe line (≤200 chars) and the
  Fatal line.
- Add a pivot per item (OPEN-67…71) × variant: runs completed over runs tried.
- For controls, add `total_eui` per variant and its % change against V0.
**How to test.**
- The staged count is 122, and `fleet.lst` has 122 lines on Speed (`wc -l` via `_ssh`).
- The harvest has 122 rows.
- Every completed-count follows rule 9.
- The pivot and the control % changes are printed in the progress log.

### T03 progress split: T03a entry on staging, T03b entry on harvest.

### CP-B (director) — choose the fix per item from T03, then write T04 and T05 here.

**Decided 2026-09-30 by the director** (user, verbatim: *"i will sleep so what i want from you to continue
to the end based on your recommendations"*, *"no need my confirmation"*). Source: T03b entry and
`openubem/outputs/comparisons/seven_items_trial_2026-09-30.csv`.

- **OPEN-67, OPEN-69, OPEN-70 — closed, known limitation (D5).** No variant cures a single run: 0/7, 0/13,
  0/1 under V1, V2 and V3.
- **OPEN-68 — closed, known limitation (D4, D5).** V1-V3 cure 0/6; S1 (2.0 m² sliver threshold) cures 3/6,
  all `fast_zone` runs outside the published figure. Not adopted: a global 2.0 m² threshold reroutes 41
  adopted buildings (T02 (c)), which would mean re-running them to recover 3 runs that never enter the figure.
- **OPEN-71 — closed, known limitation, reclassified.** The 32 GB failure is a runaway plant temperature,
  not memory. V2 (`ZoneAirHeatBalanceAlgorithm, AnalyticalSolution`) completes it: 231.80 kWh/m², 12.5 GB,
  26 min. Not adopted: one building of 8,140 (do not chase the last fraction), and V2 is a whole-model
  switch with no per-building setting in production code; V1-V3 also make the completing control
  `way/472961091` fatal. Recipe recorded in the debug reference for anyone who needs this school.
- **OPEN-72, OPEN-73 — closed, fixed by T01** (58 passed).
- **T04, T05 — not needed:** no code change chosen, so nothing to re-run. **CP-C — moot:** no building
  enters the figure. **Adopted figure unchanged: 171.38 kWh/m² / 1,146,454 t CO₂e over 8,139.**

### T04 — Apply the chosen fixes in code *(executor; written at CP-B)* — not needed (CP-B: no fix adopted)

### T05 — Re-run the 28, the touched adopted buildings, and controls; candidate figure *(executor; written at CP-B)* — not needed (CP-B: nothing to re-run)

### T06 — Sweep, register, boards *(director)*

**What.** Register (§1 state row, §2 rows closed or kept with measured counts, §4 head, §6 closing notes,
§7 entry), director prompt START HERE box, debug reference (§18 table and each entry), both boards
republished in place (counter tiles included), memory. If CP-C adopts a figure: supersession markers beside
every quote of 171.38 / 1,146,454.
**How to test.** Register counts add up in every place that states them; both boards agree with the register.

## 7. Stop-and-report points

- **CP-0 (director)** after T01: audit diff and test output.
- **CP-A (director)** after T02: pick trial variants, write T03.
- **CP-B (director)** after T03: pick fixes (D4, D5), write T04/T05.
- **CP-C (user)** after T05: add the recovered buildings to the published figure or not. Everything else
  closes without the user.

## 8. Progress log

#### T01 — OPEN-72 and OPEN-73: two config lines — completed 2026-09-30

- **Artifacts:** `openubem/config.py:53` default of `BASELINE_IDF_DIR` now `...\Desktop\NEXA-desktop\Content\00.BaselineBuildings_NUs_v231`; `openubem/config.py:123` `PREP_ABORT_ON_FAILURE = False`; `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1970` and `:1972` `[OPEN]` dropped, fix and `file:line` stated.
- **Deviations:** none.
- **Test status:** the four test files → `58 passed in 131.74s`, 0 failed, 0 errors. `git diff --stat -- openubem/config.py` → `config.py | 4 ++--` (2 insertions, 2 deletions). `git diff --stat openubem/` as a whole lists 10 files because other files in `openubem/` were already modified before T01; `config.py` is the only one T01 touched.
- **Notes:** none.

#### T02 — Diagnose OPEN-67 … OPEN-71 before any trial — completed 2026-09-30

- **Artifacts:** `scripts/analysis/seven_items_diag_2026-09-30.py` (new); `openubem/outputs/comparisons/seven_items_diag_2026-09-30.csv` (new, long format `item,case,field,value`, 913 rows; items `a_row`, `a_separation`, `a_population`, `b_proto`, `b_case`, `b_diff`, `b_diff_summary`, `c_*`, `d_*`, `e_*`). No file under `openubem/` touched; no simulation run; no local rebuild.
- **Deviations:** (1) Controls for (a) read from `evidence/open48_refleet4/la_rural/fleet_staging/idfs/` (IDFs) with the zone table from `%TEMP%/ubem_validation/open65_reparse_2026-09-29/la_rural/<stem>/eplusout.eio`; the `.eio` in `evidence/open48_refleet4/.../sim_out/` is from an older 3-zone layout and was not used (IDF zone names equal the open65 `.eio` zone names for both storey-2 controls). (2) Only 2 of the 20 completing adopted `la_rural` Warehouses (`way/472961091`, `way/472961164`) have a storey-2 core/whole zone (modelled storeys of the 20: 1 storey x4, 2 x14, 3 x2), so the completing side of (a) is 2 buildings / 4 surfaces (floor + roof each). (3) (d): the `.err` names no surface (DisplayExtraWarnings is off), so the casting surfaces were identified by a convexity test on the 57 sun-exposed building surfaces + shading surfaces of the IDF; result is exactly 2, matching the `.err` count. (4) (b) `Zone.field[2]`/`[3]` differences are zone X/Y origin placement only. (5) (c) zone floor areas from SQL `Zones.FloorArea` (all zones, none zero) of the open65 fetch for all 8,139.
- **Test status:** every item (a)-(e) has a value. (a) separating columns, all 13 failing runs (7 buildings) vs 4 completing rows: zone floor area (fail 783.79..22,443.7 m2, completing 541.88..750.28), zone volume (fail 2,743..78,553 m3, completing 1,896.58..2,625.98) and the surface area of the failing surface (fail 783.79..22,443.7, completing 541.88..750.28) separate with no overlap; auto-only (4 failing vs 2 completing buildings) gives the same three plus footprint area (fail 1,398.5..22,443.7, completing 1,219.68..1,355.23). No overlap-free separation in construction, layers (NoMass R), outside boundary, tilt, vertex count, ceiling height (3.5 all), multiplier (1 all), storeys (all 3-storey in auto), `height_m`. (b) only differences from the DOE prototype in all 7 cases: Dryer `Design Level` (W; W/m2 is 409.867 in case and prototype), all surface constructions (single-layer `LA_*` k=0.12 rho=800 vs multilayer prototype with concrete floor and gypsum/stucco/insulation), zone origin. Fraction Latent 0, Radiant 0.2, Lost 0 identical. (c) 41 buildings with smallest zone floor in [0.5, 2.0) (0 below 0.5); osm_ids in `c_building` rows. (d) first Severe: `DetermineShadowingCombinations: There are 2 surfaces which are casting surfaces and are non-convex`; casting surfaces = `Block Core_Zone Storey 1 Roof 0001` (roof, 6 vertices) and `Block Perimeter_Zone_3 Storey 1 Floor 0001_1` (floor with Outdoors/SunExposed, 5 vertices); no wall or neighbour shading surface is non-convex (12 shading objects, all convex); IDF has no `ShadowCalculation` object (E+ defaults apply). (e) `sinfo` partition `ps` 31338+ MB, 4+ CPUs; per node max 1,030,600 MB (antenna3), min 31,338 MB, 39 of 50 nodes >= 64 GB; `way/319507579` IDF: 338 zones, 2,308 BuildingSurface:Detailed + 754 FenestrationSurface:Detailed, 0 shading, 11 Output:Variable, 6.49 MB.
- **Notes:** `gpkg_levels` is missing for all 20+7 buildings (provenance OSM_MISSING), so that column is n/a. The separating size threshold lies between 750.28 and 783.79 m2 but rests on 2 completing buildings.

#### T03a — stage trial cases — completed 2026-09-30

- **Artifacts:** `scripts/analysis/seven_items_trial_2026-09-30.py` (new, `stage` subcommand only); staging `%TEMP%/ubem_validation/seven_items_trial_2026-09-30/` (`cases.csv`, `cases_full.csv`, `fleet.lst`, `fleet.tar.gz`, `s1_build/`); Speed `/speed-scratch/o_iseri/openubem/fleets/seven_items_trial_2026-09-30` (122 IDFs, 8 EPWs, `fleet.lst`). No sbatch run, no EnergyPlus run.
- **Deviations:** (1) Only 1 of the 2 named storey-2 Warehouses is a control: `way/472961164` has no `auto` row in `build_manifest.csv` (its rows are `fast_zone`/`floor`, both failing), so the fill is 7 distinct archetypes, not 6, to reach 8 controls (122 cases). (2) `_TINY_ZONE_AREA_M2` is bound as a default argument of `_coreperim_has_tiny_zone_area` (`openubem/idf/surfaces.py:274`), so patching the module constant alone has no effect; the script also sets `_coreperim_has_tiny_zone_area.__defaults__ = (2.0,)`. No code edit. The 6 S1 builds log `rerouting to one_zone_per_floor` and have 2-3 zones each.
- **Test status:** 122 staged: failing 84 (28 x V1/V2/V3), sliver_s1 6, control 32 (8 x V0-V3). On Speed via `_ssh` bash -lc: `IDF=122 LST=122 EPW=8`. Every text edit asserted one object (Timestep changed once; `ZoneAirHeatBalanceAlgorithm` absent or replaced once, then added).
- **Notes:** Controls (osm_id, archetype_id): way/472961091 Warehouse; relation/3576201 LargeHotel; relation/5698619 SecondarySchool; way/1014146286 MidriseApartment; way/1020753276 FullServiceRestaurant; way/1020979630 QuickServiceRestaurant; way/1165379861 SmallOffice; way/1313606713 OpenUBEMUnknown. Submit command (director): `sbatch --array=1-122%32 --mem=32G --time=7-00:00:00 --export=FLEET_DIR=/speed-scratch/o_iseri/openubem/fleets/seven_items_trial_2026-09-30 /speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t07.sbatch`

#### T03b — harvest trial cases — completed 2026-09-30

- **Artifacts:** `scripts/analysis/seven_items_trial_2026-09-30.py` (`harvest` subcommand added); `openubem/outputs/comparisons/seven_items_trial_2026-09-30.csv` (122 rows, plus `item`, `slurm_state`, `max_rss`, `cause_class`). No file under `openubem/` touched except that CSV; no simulation run.
- **Deviations:** (1) `parse_building` is fed `data_quality_flag=""` and `num_zones` counted from the staged IDF `Zone,` objects (no manifest holds them for S1/controls). (2) cause_class values in the source CSV: A_laundry_gas_dryer_unconditioned, B_conditioned_core_zone_with_huge_gas_load, C1_sliver_perimeter_zone_under_2m2, C2_ordinary_gains_diverges_in_sizing_no_column_explains, D_nonconvex_shading, D_nonconvex_shading_survived, E_out_of_memory, Z_completed; the 84 failing cases carry only A, C1, C2, D_nonconvex_shading, E, mapped to OPEN-67, 68, 69, 70, 71; B, D_survived and Z do not occur among them.
- **Test status:** 122 rows. Terminal: fatal 87, completed 33, sql_no_end 2 (the two out-of-memory tasks). Rule 9 applied (3 S1 rows are fatal but parse "success"; not counted). Pivot completed/tried: OPEN-67 V1 0/7, V2 0/7, V3 0/7; OPEN-68 S1 3/6, V1 0/6, V2 0/6, V3 0/6; OPEN-69 0/13 in each of V1-V3; OPEN-70 0/1 in each; OPEN-71 V1 0/1, V2 1/1, V3 0/1. Controls, total_eui % change vs V0 (7 comparable): V1 -0.26..+0.39, V2 -0.20..+0.20, V3 -0.32..+0.45. The 8th control, way/472961091 (storey-2 Warehouse), completes in V0 (22.363) but is fatal in V1, V2 and V3, so 7 of 8 controls compare.
- **Notes:** way/319507579 (tasks 82-84): V1 OUT_OF_MEMORY at 32G after 26 s (sacct MaxRSS 132K, not meaningful); V2 COMPLETED, MaxRSS 13,157,836K (12.5 GB), 26 min 10 s, parse success; V3 OUT_OF_MEMORY at 32G after 41 s (MaxRSS 19,652,784K = 18.7 GB).

#### T06 — Sweep, register, boards — completed 2026-09-30

- **Artifacts:** register `INVESTIGATION_open-items-register-II.md` (§1 new state row, §2 header and rows OPEN-67 … OPEN-73 closed, §4 head, §6 closing note, §7 entry); `prompts/DIRECTOR_PROMPT_openings.md` START HERE box; `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (laundry, sliver, non-convex, sizing-divergence and out-of-memory entries closed, OPEN-71 corrected to runaway plant temperature, §18 table and TOC); `reporting/board_open-items.html` and `reporting/board_published-numbers.html` republished in place (artifacts `7960a833-…`, `0615b50a-…`); memory index pointer.
- **Deviations:** T04, T05 and CP-C not run (CP-B: no fix adopted). No supersession markers needed (figure unchanged).
- **Test status:** register counts 0 live / 73 retired / 73 total, next free OPEN-74, in §1, §2 header, §4 head, §7 entry, director prompt and open-items board tiles; numbers board stamp states 171.38 / 1,146,454 over 8,139 unchanged.
- **Notes:** plan complete.
