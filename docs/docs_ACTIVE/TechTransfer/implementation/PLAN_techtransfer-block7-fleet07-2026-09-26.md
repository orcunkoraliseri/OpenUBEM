# PLAN — TechTransfer block 7: FLEET-07, apply the saving measures and re-run what changes

**Slug:** techtransfer-block7-fleet07 · **Date:** 2026-09-26 · **Manager-authored.** Executors append to §8 only.

**Predecessor:** `PLAN_techtransfer-block6-2026-09-18.md` (past ~1,100 lines; closed to new tasks by its §3
rule). Its last progress-log entry, "FLEET-06c-ALL / FLEET-06c-TABLE — harvest done, table audit FAILED",
is the reason this block exists.

**Authorized by:** user 2026-09-26, "lets go, no need to wait my confirmation, continue to the end", in reply
to "fix the three measures, then re-run the scenarios". No per-task ask is needed. The one exception is
deleting simulation outputs, which stays governed by §2 rule 6.

---

## 1. Why

FLEET-06b simulated 65,112 cases, but no measure was written into any scenario IDF. The fleet EUI is
172.3974 kWh/m² in all 8 cells. Measured on `relation_11171765` (`nyc_centre`):

- **`thermostat_setback` returns `gate_no_thermostat`.** The models carry `HVACTEMPLATE:THERMOSTAT` (fields
  `Heating_Setpoint_Schedule_Name`, `Constant_Heating_Setpoint`, `Cooling_Setpoint_Schedule_Name`,
  `Constant_Cooling_Setpoint`). The measure only reads `THERMOSTATSETPOINT:DUALSETPOINT`
  (`openubem/scenarios/measures.py:147`, `:467`, `:485-486`). The schedules have a real setback block:
  `Heating_Setpoint_OpenUBEMUnknown` weekdays are 15.6 °C until 06:00, 21.1 °C from 06:00 to 19:00, and
  15.6 °C after 19:00.
- **`infiltration_tightening` returns `gate_unsupported_coefficients`.** The model has one
  `ZoneInfiltration:DesignFlowRate` object, `Flow/ExteriorWallArea` 0.000285, with coefficients 1/0/0/0.
  The measure accepts only the DOE-2 set 0/0/0.224/0.
- **`lighting_power_density` returns `gate_archetype_out_of_scope`.** `scripts/analysis/fleet06a_campaign_2026-09-18.py:76`
  calls `apply_cell(idf, cell, enabled=True)` with no `archetype=`. The archetypes in scope (6 office
  types in `measures.json`) cover 4,140 of the 8,139 buildings: SmallOffice 3,495, MediumOffice 390 and
  LargeOffice 255 (`t08_restated_fleet_eui_2026-09-10.csv`, column `archetype_id`).

## 2. Hard rules for the executor

1. Execute only the task you were dispatched for. Stop at its stop point, append §8, and report.
2. Never edit `docs/docs_main/`, OVERVIEW or DESIGN docs, or root `main.py`. No `.py` under `docs/`.
3. Speed: no compute on the login node. Always use the `_ssh()` wrapper (`scripts/cluster/t08_harvest_results.py:104`),
   `sbatch --array=…%32 --time=7-00:00:00`, and at most 10,000 tasks per array job. Submit in waves, and
   keep account-wide submitted jobs under ~20k. Never touch another project's jobs.
4. Never run simulations one after another. The user's 2026-09-23 ruling (block-6 §2f) keeps the local
   machine free, so EnergyPlus runs on Speed only.
5. Never write into `fleet06b_local_2026-09-18\out\` or `fleet06a_campaign_2026-09-18\`. All new output goes
   under the roots in §3.
6. **Never delete any simulation output.** The §2h-4 cleanup of block 6 is a separate, manager-run step.
7. Register every solved error in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.
8. If the spec is ambiguous, stop and quote the conflict. Never invent.

## 3. File layout

- `openubem/scenarios/measures.py`, `openubem/data/scenarios/measures.json`: FLEET-07a only.
- `tests/test_scenario_measures.py`: new tests, FLEET-07a.
- `scripts/analysis/fleet07_campaign_2026-09-26.py`: new, FLEET-07b.
- Local roots, all under `%TEMP%\ubem_validation\`:
  - `fleet07_campaign_2026-09-26\<cell>\<stem>.idf`
  - `fleet07_campaign_2026-09-26\measure_status.csv`
  - `fleet07_campaign_2026-09-26\manifest_changed.csv`
  - `fleet07_out_2026-09-26\out\<cell>\<stem>\`, which Speed results are pulled back into.
- Speed: `/speed-scratch/o_iseri/openubem/fleets/fleet07_2026-09-26/`, which holds `idfs/<cell>/`,
  `weather/` (copied from `fleet06b_2026-09-18/weather/` on Speed), `fleet07_wave<k>.lst` and `out/`.
  The sbatch file is `scripts/cluster/submit_fleet06b.sbatch`, used unmodified through `FLEET_DIR` and `FLEET_LST`.

## 4. Dependency decisions (pinned)

- The measure code, gates and parameter digits already shipped stay as they are. FLEET-07a only adds
  support for two object shapes that are already present.
- **Manager ruling R1 (infiltration, 2026-09-26).**
  - A `ZoneInfiltration:DesignFlowRate` with the constant set 1/0/0/0 (within 1e-6) is supported. It is
    compared with the same `IFLR` / `IAGW` target as a DOE-2 object, through the same field, and never raised.
  - Reason: PNNL-18898 (Gowri, Winiarski, Jarnagin 2009) picks the DOE-2 wind coefficient 0.224 s/m so that
    the factor equals 1.0 at its 4.47 m/s reference wind. At that reference, a DOE-2 design value and a
    constant-set design value describe the same flow.
  - This citation is the manager's own and was not re-read from the PDF. Record it as such in
    `measures.json` `description`.
  - Every other coefficient set stays gated.
- **Manager ruling R2 (setback).**
  - `HVACTEMPLATE:THERMOSTAT` is treated exactly like `THERMOSTATSETPOINT:DUALSETPOINT`, with the same
    derivation (`_derive_occupied_and_setback`, `:431`), the same clone (`clone_schedule`, `:362`) and the
    same repoint of only that object.
  - The field map is `Heating_Setpoint_Schedule_Name` / `Cooling_Setpoint_Schedule_Name`.
  - A side whose schedule field is blank and whose `Constant_*_Setpoint` is set has no setback block. It is
    reported `gate_no_setback_block` for that side.
  - `gate_no_thermostat` fires only when both object types are absent.
- **Ruling R3 (lighting).** `archetype` = the building's `archetype_id` from
  `openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv`, passed to every `apply_cell` call.

## 5. Facts with line citations

- `apply_cell` is at `openubem/scenarios/campaign.py:64-69` and passes `archetype` through to `apply_measure`
  (`measures.py:842`).
- The FLEET-06a builder is `scripts/analysis/fleet06a_campaign_2026-09-18.py:66-83`. Fresh IDFs are at
  `REBUILD_BASE/<geo>/step3/idfs/<stem>.idf` (`:38`, `:69`).
- The FLEET-06a scenario IDFs are byte-identical across the 7 cells: 300 of 300 sampled buildings, md5 of
  `relation_11171765` = `983c360a…`.
- The FLEET-06b results per case are at `fleet06b_local_2026-09-18\out\<cell>\<stem>\`. The harvest is
  `scripts/analysis/fleet06c_harvest_2026-09-24.py` (`OUT_ROOT :27`, `HARVEST_ROOT :28`). The table script is
  `scripts/analysis/fleet06c_scenario_table_2026-09-26.py`.

## 6. Tasks

### FLEET-07a — measures accept the fleet's thermostat and infiltration objects

- **What:** implement R1 and R2 in `measures.py`, including `_thermostat_applicability` (`:147`) and the
  infiltration applicability. Update the two `measures.json` `description` strings. Leave the parameters
  and the gate names unchanged.
- **Why:** §1.
- **How:**
  - Extend the existing functions. Add no second code path per measure.
  - The report dict keeps its current keys. Each thermostat object's entry gains `"object_type"`.
- **How to test:**
  - Add tests to `tests/test_scenario_measures.py`, using the `HVACTEMPLATE:THERMOSTAT` and
    `Heating_Setpoint_OpenUBEMUnknown` blocks copied verbatim from
    `%TEMP%\ubem_validation\fleet06a_rebuild_2026-09-18\nyc_centre\step3\idfs\relation_11171765.idf`.
    1. Setback on that block: the heating 15.6 entries become 15.6 − 5.5556, the 21.1 entries are unchanged,
       only that thermostat is repointed, and the original schedule is byte-identical.
    2. A constant-setpoint side gives `gate_no_setback_block`.
    3. Infiltration 1/0/0/0 is compared and lowered when above the target, `already_compliant` when below,
       and 0/0/0.224/0 behaves as before.
    4. A 0.5/0/0.1/0 set is still gated.
  - Then run `pytest tests/test_scenario_measures.py tests/test_scenario_campaign.py tests/test_scenario_campaign_wiring.py -q`:
    all pass, with the pass count stated.
  - On the real `relation_11171765.idf` (a copy in the scratchpad), `apply_measure` for each of the 3
    measures (lighting with `archetype="LargeOffice"` if that is its `archetype_id`) prints status and
    counts. Report those three lines.
- **Stop point:** report after FLEET-07a.

### FLEET-07b — rebuild the 7 scenario cells with archetype, log every measure status

- **What:** `scripts/analysis/fleet07_campaign_2026-09-26.py`, a copy of the FLEET-06a builder logic with
  these changes:
  - `archetype` comes from the T08 csv (R3).
  - It writes to `fleet07_campaign_2026-09-26\<cell>\`.
  - It writes `measure_status.csv` with one row per (stem, cell, measure) and the columns
    `stem, cell, measure_id, status, n_applied`. `n_applied` is `n_lowered`, `n_applied` or `n_tightened`,
    whichever the measure reports.
  - It writes `manifest_changed.csv` (`building_id, cell_name, output_idf_path, geo_cell, epw_name`) with
    only the cases where at least one measure in the cell has `n_applied > 0`.
  - Process pool of 20. Never sequential.
- **How to test:**
  - 56,973 IDFs written (8,139 × 7).
  - For every row not in `manifest_changed.csv`, the new IDF md5 equals the FLEET-06a IDF md5. If any
    differs, stop and report the count and 3 examples.
  - Print the per-cell count of changed cases, and a status × measure count table.
  - The single-measure cells must satisfy changed(lighting) ≤ 4,140.
- **Stop point:** report the counts. The manager audits before FLEET-07c.

### FLEET-07c — simulate the changed cases on Speed

- **What:**
  - Stage the changed IDFs, plus the weather subset they use, to the Speed root in §3.
  - Write `fleet07_wave<k>.lst` slices of at most 10,000 lines, in the same 3-column format as `fleet.lst`
    of `fleet06b_2026-09-18`. Read that file's format on Speed with `head -3` first.
  - Submit one `sbatch --array=1-N%32 --time=7-00:00:00` per wave, only while the account total stays
    under the cap.
  - State the total case count and the width before the first submit.
  - Monitor with `sacct` no more than every 30 min, or by event.
  - Measure the mean task time from finished tasks and state the ETA as remaining × mean ÷ 32.
  - Pull finished case folders back to `fleet07_out_2026-09-26\out\<cell>\<stem>\`.
  - Update the monitor artifact db doc `fleet06b/progress`
    (`https://claude.ai/artifact/6H6xkLiazkjN2akF6wsXKa`): total = changed count, finished, failed,
    status_text, rate.
- **How to test:** every manifest row has a local folder with `eplusout.end` reading
  `EnergyPlus Completed Successfully`. List the failures by id.

### FLEET-07d — harvest and the scenario table

- **What:**
  - Harvest as in block-6 FLEET-06c, into `%TEMP%\ubem_validation\fleet07_harvest_2026-09-26\`.
  - A case's sim folder is `fleet07_out_2026-09-26\out\<cell>\<stem>\` if it is in `manifest_changed.csv`,
    otherwise `fleet06b_local_2026-09-18\out\<cell>\<stem>\`. Unchanged IDFs give unchanged results.
  - Baseline is not re-harvested: reuse `fleet06c_harvest_2026-09-24\baseline\`.
  - Then run the table (`fleet06c_scenario_table_2026-09-26.py` logic, pointed at the new root) and write
    `openubem/outputs/comparisons/fleet07_scenario_summary_2026-09-26.csv` with the columns of block-6
    FLEET-06c-TABLE.
- **How to test:**
  - 8 rows with the same `n_buildings`, and baseline delta 0.
  - Every scenario containing lighting or setback has delta < 0.
  - Print the table.

## 7. Stop-and-report points

1. After FLEET-07a (code and tests).
2. After FLEET-07b (changed counts, before any Speed submit).
3. After FLEET-07c's first wave has 32 tasks running and one finished (measured task time).
4. After FLEET-07d (the table).

## 8. Progress log

#### FLEET-07a — measures accept the fleet's thermostat and infiltration objects — completed 2026-09-26

- **Artifacts:** `openubem/scenarios/measures.py` (`_thermostat_applicability`, `_apply_thermostat_setback`
  extended to `HVACTEMPLATE:THERMOSTAT` via `_THERMOSTAT_OBJECT_FIELD_MAPS`, every object entry now carries
  `object_type`; `_coefficients_match_doe2` renamed `_coefficients_match_supported` and extended to accept
  the constant set `(1,0,0,0)` via `_ACCEPTED_INFILTRATION_COEFFICIENTS`; module docstring updated for both
  measures); `openubem/data/scenarios/measures.json` (`thermostat_setback` and `infiltration_tightening`
  `description` strings updated per R1/R2, parameters and gate lists unchanged); `tests/test_scenario_measures.py`
  (6 new tests: HVACTEMPLATE:THERMOSTAT real-prototype deepening + original-schedule-untouched,
  constant-setpoint-side `gate_no_setback_block`, `_thermostat_applicability` recognizing
  HVACTEMPLATE:THERMOSTAT, infiltration constant-coefficients tightened-above-target and
  already-compliant-below-target; 1 existing test's coefficients changed from `(1,0,0,0)` (now accepted) to
  `(0.5,0,0.1,0)` to keep testing a still-gated set).
- **Deviations:** none from R1/R2/R3 as pinned in §4. One correction to the plan's own illustrative test
  text: §6 FLEET-07a "How to test" item 1 states the heating 15.6 entries "become 15.6 − 5.5556"; the
  existing (unmodified) derivation `_derive_occupied_and_setback`/`_evaluate_setpoint_schedule` computes the
  new setback as `occupied − delta_c`, i.e. `21.1 − 5.5556 = 15.5444`, not `15.6 − 5.5556`, and this matches
  both the pre-existing DUALSETPOINT test (`test_shallow_setback_is_deepened`, asserts `21.0 − 5.5556`) and
  the ASHRAE 90.1-2022 6.4.3.3.2 text quoted in `measures.json` ("...at least 10F below the occupied heating
  set point"). R2 requires reusing "the same derivation" as DUALSETPOINT, so the test was written to the
  actual, unmodified derivation (`21.1 − 5.5556`) rather than the plan's illustrative arithmetic. No code
  changed for this; treated as a slip in the plan's example, not a spec conflict, since R2 itself pins the
  behavior unambiguously.
- **Test status:** `pytest tests/test_scenario_measures.py tests/test_scenario_campaign.py tests/test_scenario_campaign_wiring.py -q`
  → 65 passed. Real-IDF check on a scratch copy of
  `%TEMP%\ubem_validation\fleet06a_rebuild_2026-09-18\nyc_centre\step3\idfs\relation_11171765.idf`, `apply_measure`
  for all 3 measures: `thermostat_setback: status=applied gate=None n_applied=1, n_already_compliant=1,
  n_gate_schedule_missing=0, n_gate_no_setback_block=0`; `infiltration_tightening: status=already_compliant
  gate=None n_tightened=0, n_already_compliant=1, n_gate_unsupported_coefficients=0` (previously
  `gate_unsupported_coefficients`, now accepted and evaluated); `lighting_power_density:
  status=gate_archetype_out_of_scope gate=gate_archetype_out_of_scope` (its `archetype_id` in
  `t08_restated_fleet_eui_2026-09-10.csv` is `OpenUBEMUnknown`, not in `in_scope_archetypes`; unchanged by
  this task, in scope for FLEET-07b/R3).
- **Notes:** none.

#### FLEET-07b — rebuild the 7 scenario cells with archetype, log every measure status — completed 2026-09-26

- **Artifacts:** `scripts/analysis/fleet07_campaign_2026-09-26.py` (new, copy of the FLEET-06a builder logic
  per §6; `fleet06a_campaign_2026-09-18.py` untouched); outputs under
  `%TEMP%\ubem_validation\fleet07_campaign_2026-09-26\`: `<cell>\<stem>.idf` for the 7 non-baseline cells,
  `measure_status.csv` (97,668 rows), `manifest_changed.csv` (40,746 rows).
- **Deviations:** none from §6 FLEET-07b as pinned. Process note only: the first launch attempt (backgrounded
  with a shell `&` + `nohup` redirect) detached from the tool's own process tracking and reported a false
  "exited" status while the python process kept running; a second launch was started before this was caught,
  producing two concurrent full-population builds against the same output root for a few minutes. Caught via
  `Get-CimInstance Win32_Process`, the second (duplicate) run and its 20 workers were killed
  (`Stop-Process -Force` on PID 53876 and its children) before any output CSV was written by either run, only
  the surviving first run (PID 41868) completed and wrote `measure_status.csv` / `manifest_changed.csv`. No
  script or plan file was affected; recorded for provenance only, not a deviation from the plan's method.
- **Test status:**
  - IDF count: 56,973 written (8,139 x 7), 0 `MISSING_FRESH` reported. Matches §6's required count.
  - Per-cell changed counts (n_applied > 0 for the cell, from `manifest_changed.csv`): infiltration 2,247;
    lighting 2,798; setback 8,071; lighting+infiltration 3,359; lighting+setback 8,071;
    setback+infiltration 8,100; lighting+setback+infiltration 8,100. Sum 40,746, matches
    `manifest_changed.csv` row count.
  - Single-measure-cell check: changed(lighting) = 2,798 <= 4,140 required by §6. Pass.
  - Status x measure count table (from `measure_status.csv`, 97,668 rows total = 12 measure-applications x
    8,139 buildings): `lighting_power_density` applied 11,192 / gate_archetype_out_of_scope 15,996 /
    no_applicable_objects 5,368 (sum 32,556 = 4 lighting-bearing cells x 8,139); `thermostat_setback` applied
    32,284 / already_compliant 132 / gate_no_setback_block 140 (sum 32,556 = 4 setback-bearing cells x
    8,139); `infiltration_tightening` applied 8,988 / already_compliant 23,568 (sum 32,556 = 4
    infiltration-bearing cells x 8,139).
  - md5 check (every (stem, cell) pair not in `manifest_changed.csv` vs. the matching FLEET-06a IDF): 16,227
    pairs checked, 0 missing on either side, **2 mismatches**: `way_381810555`/infiltration and
    `way_425993519`/lighting. Root-caused (both are `Generator:PVWatts` "DC System Capacity" fields the
    measures never touch; the two source files under
    `fleet06a_rebuild_2026-09-18\<geo>\step3\idfs\<stem>.idf` were overwritten in place on 2026-09-23,
    5 days after FLEET-06a's campaign build read them on 2026-09-18 — FLEET-07b (built 2026-09-26)
    reproduces the current source exactly; FLEET-06a's output reflects the pre-2026-09-23 value). Registered
    in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §17. Not a defect in this task's code or in R1/R2/R3.
  - Wall time: generation done in 897 s (~15 min), pool of 20, `.venv\Scripts\python.exe`.
  - 3-building smoke test (before the full run, `lighting+setback+infiltration` cell,
    SmallOffice/MidriseApartment/OpenUBEMUnknown archetypes): status rows correct per archetype scope
    (lighting gated `gate_archetype_out_of_scope` for the two non-office archetypes,
    `no_applicable_objects` for SmallOffice; setback `applied` for all 3; infiltration `already_compliant`
    for all 3).
- **Notes:** the 2 md5 mismatches mean FLEET-07b's "unchanged" IDFs are not, for those 2 buildings alone,
  byte-identical to FLEET-06a's own (now slightly stale) build — but they are correct against the current
  shared source tree. No action taken beyond registering the finding; left for the manager's audit.

#### FLEET-07c (part 1) — staged and wave 1 submitted — 2026-09-26

- **Artifacts:** Speed root `/speed-scratch/o_iseri/openubem/fleets/fleet07_2026-09-26/` with `idfs/<cell>/`
  (7 non-baseline cells, 40,746 IDFs total — exactly the `manifest_changed.csv` set, not the full 56,973;
  counts per cell match the manifest: infiltration 2,247, lighting 2,798, lighting+infiltration 3,359,
  lighting+setback 8,071, lighting+setback+infiltration 8,100, setback 8,071, setback+infiltration 8,100),
  `weather/` (the same 9 `.epw` files copied server-side from `fleet06b_2026-09-18/weather/`, matching the
  9 distinct `epw_name` values in the manifest), `out/`; `fleet07_wave1.lst` … `fleet07_wave5.lst`
  (10,000/10,000/10,000/10,000/746 lines, tab-separated `cell_name<TAB>building_id<TAB>epw_name`, same
  format as `fleet06b_2026-09-18/fleet.lst`) at both the local campaign root and the Speed root. Job
  1349546 = wave1 (`--array=1-10000%32 --time=7-00:00:00`, `FLEET_LST=fleet07_wave1.lst`), submitted via
  the unmodified `submit_fleet06b.sbatch` found at `/speed-scratch/o_iseri/openubem/scripts/cluster/`.
- **Deviations:** "large buildings evenly spread" was implemented as: join `manifest_changed.csv` to
  `t08_restated_fleet_eui_2026-09-10.csv` on `building_id`/`stem`, flag `archetype_id` in
  {MediumOffice, LargeOffice} as large (3,801 of 40,746), then assign large rows to the 5 waves in
  proportion to each wave's capacity (933/933/933/933/70, rounding remainder to wave1) before filling the
  rest of each wave with the remaining rows in original order; each wave's assigned rows are then sorted
  back to original manifest order. Before this, the plain contiguous slice put 1,253/1,053/1,205/160/130
  large buildings in waves 1–5 respectively (wave4 at 13% of the average of waves 1–3); after, it is
  932/933/933/933/70 (proportional to each wave's share of the 40,746 total). This distribution choice was
  not itself specified in the plan or facts beyond "put the large buildings evenly spread, do not reorder
  otherwise"; treated as the plain-language meaning of that sentence, not an invention of new scope.
  IDFs were staged as the changed-only subset (7 per-cell tar.gz built from filelists, 586 MB total) rather
  than tarring the full local `fleet07_campaign_2026-09-26\` tree (12 GB, 56,973 IDFs) — the extra 16,227
  unchanged-per-cell IDFs give identical results to the already-simulated FLEET-06b baseline (§6 FLEET-07d)
  and were not needed on Speed. Per the coordinator's mid-task correction: `squeue -u o_iseri -h -r | wc -l`
  read 5 (another project's jobs, untouched) both before and after staging, so only wave1 was submitted;
  wave2 (or wave1+wave5 had the count been 0) is left for a later dispatch.
- **Test status:** account-wide user tasks after submit: 10,005 (5 pre-existing + 10,000 wave1), under the
  ~20,000 cap. `squeue -j 1349546` showed 32 RUNNING / 9,968 PENDING immediately after submit (default
  array throttle already at 32; no `scontrol update` needed). A `sacct` check ~5 min later found 198
  COMPLETED, 27 RUNNING, 1 PENDING (task count fluctuates near 32 because each task is short). Task 1
  (`setback/way_1008727470`) checked directly: `eplusout.end` reads "EnergyPlus Completed Successfully--
  24 Warning; 0 Severe Errors; Elapsed Time=00hr 00min 16.40sec". Mean Elapsed over the first 154 COMPLETED
  tasks = 17.87 s. ETA for the remaining 40,548 cases (40,746 total − 198 finished) at width 32:
  40,548 × 17.87 s ÷ 32 ≈ 22,660 s ≈ 6.3 hours. Stop point 3 condition (32 running, ≥5 finished) was met
  well within the first 10-minute check; no further polling was needed.
- **Notes:** monitor artifact db `fleet06b/progress` updated (version 13 → 14): `total` 40,746, `finished`
  198, `failed` 0, `status_text` "RUNNING — FLEET-07c wave 1 of 5 (job 1349546, 10,000 tasks) submitted; 32
  running, 198 finished, mean 17.9s/task", `rate_per_h` 6,449 (= 32 × 3600 ÷ 17.87). Waves 2–5 (30,746
  remaining cases) are staged and ready (`.lst` files exist on both sides) but not submitted; a later
  dispatch submits wave2 next per the coordinator's correction, re-checking `squeue -u o_iseri -h -r | wc -l`
  first.

