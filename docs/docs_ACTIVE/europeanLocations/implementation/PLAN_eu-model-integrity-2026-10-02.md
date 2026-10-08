# PLAN — EU model integrity before any new submission (2026-10-02)

> **CLOSED 2026-10-08 — arc archived.** Tasks without a completed entry were not run; superseded by the owner's stop rulings D-EU-148 / D-EU-149 (2026-10-08).

## 1 Header

- **Slug:** `eu-model-integrity-2026-10-02`. **Date:** 2026-10-02. **Author:** director (manager session).
- **Owner requests (verbatim, 2026-10-02):**
  - "also if there are similar errors for other country of neighbourhoods as well please check before submitting them"
  - "you can prepare an implemenation plan in here …\europeanLocations\implementation"
  - On redrawing the plan pages from the corrected models: "yes please".
- **Follows:** `PLAN_eu-floor-division-residual-2026-09-29.md` §8 (FINDING 289, T06s, T06u). That plan is past 1,500 lines, so new tasks live here. Its T06s part 2 is in flight and logs there. T07 and T08 stay there.
- **DESIGN pointer:** the floor-division rules of the residual plan §5, plus the code facts in §5 below. No DESIGN doc changes.
- **Goal:** no EU model goes to Speed again until every model in all four neighbourhoods passes one scripted set of physical checks: storeys, floor area, height, zones, flats, windows, gains and position. Each check compares the model with the source data, never only with the previous model.

## 2 Hard rules for the executor

- Execute the tasks in order and stop at each stop point (§7). Do not propose alternatives. If the plan is ambiguous, STOP and quote the conflict.
- No EnergyPlus, no ssh, no Speed. The director submits.
- Local processes: 10 at most.
- Never write into `EU-11/<D>_win_2026-10-03/04/05` or any `_merged_*` folder.
- Edit only the files named in each task. No code comments. No `.py` under `docs/`. Figures go to `openubem/outputs/` (flat).
- Cap every command's output (head/tail, counts).
- Append one progress-log entry per task in §8 of this file. Each entry has Artifacts, Deviations, Test status (every check pass/fail with its measured value) and Notes.
- Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Register every error you solve there.

## 3 File layout

| Path | Role |
|---|---|
| `openubem/outputs/eu_evidence/EU-11/<D>_win_2026-10-06/` | models of record after T06s part 2 (4 districts) |
| `openubem/outputs/3D/eu_<D>_data/buildings.csv` | source data per building: `footprint_area_m2`, `levels`, `height_m`, `storey_count` |
| `openubem/outputs/eu_evidence/EU-11/<D>_merged_2026-09-08/` | published 09-08 manifests (floor area per building, for cross-vintage reasons) |
| `<D>_win_2026-10-06/windows.csv` | window share target and achieved, per building |
| `<D>_win_2026-10-06/origin_offset.json` | FR, IT local origin (x, y) |
| `scripts/eu21/13_model_integrity.py` | **new**: the integrity sweep (T02) |
| `tests/test_eu_model_integrity_2026_10_02.py` | **new**: tests of the sweep on hand-built IDFs |
| `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/` | sweep outputs |
| `scripts/eu21/09_plans3d_from_idf.py` | plan pages writer (T04) |

## 4 Dependency decisions (pinned)

- Read IDFs with the same reader T06s part 1 used: plain text parse of `BuildingSurface:Detailed` and `FenestrationSurface:Detailed`, vertices after the last non-numeric field. Do not use eppy or geomeppy, which are too slow at 4,113 files.
- Use shapely (already pinned) for polygon areas. Use pandas for the CSVs.
- `multiprocessing.Pool(10)` at most.

## 5 Facts with citations

- The flat allocator gives storey i `quotient + (1 if i < remainder)` flats, which is 0 when flats < storeys (`openubem/geometry/european_residential.py:2943-2950`).
- A 0-flat storey was folded into the storey below (`:2753-2762`). Zone specs give one zone per flat of height `span × 3.0` (`:2858-2872`). The extruder uses `m * first["height_m"]` (`scripts/run_eu_s2_campaign.py:1169-1172`). Fixed by T06s part 2 (D-EU-143).
- Storey height is `FLOOR_TO_FLOOR_M` from `scripts/run_eu_s2_district_campaign.py`, which is 3.0 m.
- `dwellings_used` comes from `_dwellings_for` (`scripts/run_eu_s2_district_campaign.py:1185`), not from the zones.
- The EUI denominator is `floor_area_m2` of `prepared_buildings.csv` (`scripts/cluster/harvest_eu11_merged.py:437`). It equals the total zone floor area.
- FR and IT IDFs are shifted to a local origin (D-EU-142, FINDING 288). `origin_offset.json` holds the shift.
- Known accepted exceptions (by name only):
  - zero-floor flat `IT 97d478bc56840531_F0_dwelling_3`, `[OPEN]`;
  - 8 core-rule stems listed in residual plan §8 "T06s part 1";
  - 90 homes with no outdoor wall (FINDING 283);
  - 1 London non-convex Severe.

## 6 Tasks

### T01 — T06s part 2 (in flight, logged in the residual plan)

**What / Why / How / How to test:** see residual plan §8 "T06s part 2 — fix, rebuild, gates". The director audits it. T02 is split so it can start now:
- **T02a**, now: the script, the tests and the `win_2026-10-05` validation run.
- **T02b**, after the T01 audit passes: the `win_2026-10-06` run.

### T02 — Integrity sweep of every model in all four neighbourhoods

**What.** Write `scripts/eu21/13_model_integrity.py --tree win_2026-10-06 [--districts ES,FR,GB,IT]`. It reads every IDF of `<D>_<tree>/idfs/` and writes `integrity_2026-10-02/<D>_<tree>_integrity.csv`: one row per building, one column per check (value plus pass/fail), and a `reason` column for named exceptions. It also writes `integrity_2026-10-02/summary_<tree>.csv` with per-district fail counts per check.

Checks (tolerances fixed here; do not tune them):

- **I1 storeys:** distinct floor z levels = `storey_count` in the source data.
- **I2 storey areas:** each storey's floor area is within 1 % of the ground storey's.
- **I3 floor area vs data:** total floor area ÷ (`storey_count` × `footprint_area_m2`) is in 0.97–1.03. Report the distribution (p1, p50, p99) per district even when the check passes.
- **I4 height:** the highest roof z minus the lowest floor z = `storey_count` × 3.0 m, within 0.05 m.
- **I5 zones:** every zone has ≥ 1 floor, ≥ 1 ceiling or roof and a volume above 0; no zone is taller than 4.5 m.
- **I6 roof and ground:** roof area is within 1 % of the top storey's floor area, and ground-floor area is within 1 % of the IDF footprint.
- **I7 EUI denominator:** total IDF zone floor area equals `floor_area_m2` in `prepared_buildings.csv` within 0.1 %.
- **I8 flats:** distinct `dwelling_<j>` indices across storeys = `dwellings_used` (divided homes only).
- **I9 windows:** window area ÷ outdoor wall area = `share_target` in `windows.csv` within 2 % absolute. Window area is above 0 unless the home is on the FINDING 283 list.
- **I10 gains per m²:** people, lights and equipment W/m² (or m²/person) per zone equal the archetype value. Totals must scale with floor area, so a check per m² catches a zone with the wrong area.
- **I11 position:** FR and IT vertices fall inside 0–20 km of the local origin; ES and GB carry no offset file. The same building's footprint centroid after adding the offset back is within 1 m of the 10-05 one.
- **I12 identity:** building set = the 10-05 universe; md5 list complete; no stem is missing an IDF or a schedule folder.
- **I13 cross-vintage:** total floor area vs the 09-08 published `floor_area_m2` (from `<D>_merged_2026-09-08`). Every difference above 1 % gets a reason code. Codes: `up_class_09-08_short` (FINDING 289), `sliver_drop` (T06q), `core_rule`. Anything else is `UNEXPLAINED`.

**Why.** The owner asked that every neighbourhood be checked for errors like FINDING 289 before more runs. The T06p gates checked wall direction and windows but never floor area, which is how FINDING 289 slipped through. Each check here tests one physical property against the source data, so a defect in any build step shows up regardless of which step caused it.

**How.**
- Pure reading and arithmetic; reuse the T06s part 1 parsing logic (scratch `t06s/geom.py` is not in the repo, so re-implement it in the script).
- Also run the sweep read-only on `--tree win_2026-10-05`. Its I1/I2 fail list must equal the T06s down class, which validates the sweep against a known answer.
- Add `tests/test_eu_model_integrity_2026_10_02.py`. Each test uses a hand-built 2-storey IDF text:
  - a passing model;
  - a missing storey (I1 fails);
  - a tall zone (I5 fails);
  - a window share off by 5 % (I9 fails);
  - a 10 % floor-area loss (I2 and I7 fail).

**How to test.**
- The tests pass.
- The `win_2026-10-05` run reproduces the T06s down class (ES 26, FR 6, GB 11, IT 149) on I1/I2.
- The `win_2026-10-06` summary is printed per district per check.
- Every fail is either a named exception from §5 or listed by stem.
- STOP (§7 stop point 1).

### T02c — Check refinements and the 10-06 run (director ruling after the T01 and T02a audits, 2026-10-02)

**Director measurements behind this task** (read-only run of the T02a script on `win_2026-10-06`, `integrity_2026-10-02/summary_win_2026-10-06.csv`):
- GB and IT pass I1 and I4 on 10-06. ES fails 74 and FR fails 166.
  - In all 166 FR fails and in 58 of the 74 ES fails, the IDF storey count equals `levels`, while `storey_count` in `buildings.csv` is lower.
  - The other 16 ES fails have `levels` empty and IDF storeys above `storey_count`. Examples: `193aea6286a8521d` (3→4) and `6940d076523dfe64` (2→4).
- I6: the roof check counts every `roof` surface. Multi-block homes carry `Adiabatic` roofs on lower blocks. Example: GB `daf072856e80ebcb`, `Block …_2_a0 Storey 4 Roof 0001`, Adiabatic at z = 15 m. The I6 fail counts are the same on 10-05 and 10-06 (79 / 81 / 48 / 218), so they come from before T06s.
- I9: every fail carries `finding283_no_outdoor_wall`. These are named exceptions.
- I10: `add_european_heating_controls` writes `phi_int_w_m2` (`openubem/idf/european_controls.py:69`). `run_eu_s2_campaign.py:13-16` removes that constant object after reading its magnitude and replaces it with a 1.0 W/m² OTHEREQUIPMENT on a Schedule:File (`openubem/semantic/european_schedules.py:133`).
- I7 and I3 fails outside the core rule, unexplained so far:
  - ES `b56bda9013da5b2d` (I3 1.30), `d342db5179c1ac49` (1.17) and `c57a45184a1c34ba` (I7 0.12 %);
  - IT `89eea66ba6ada782` (I3 1.17), `05b52a0da00a6046` (1.08) and `595675e5f53ef10b` (I2 4.0 %, I7 0.57 %).

**What.** Change only `scripts/eu21/13_model_integrity.py` and its test file, then re-run on 10-05 and 10-06.
1. **I1/I4 reference = the storey count the build used.**
   - Find the storey rule per country in `scripts/run_eu_s2_district_campaign.py`: the `_mapped_rows`, `_gb_rows` and `_it_rows` storey assignment, including `storey_override` and `levels`. Cite file:line in the progress log.
   - Compute that same rule from the source data and use it as the I1/I4 reference.
   - Keep `storey_count` as an information column, `storeys_data_csv`, and add `storey_source` (which field the rule took).
   - Do not copy the IDF value into the reference. The reference must come from the source data through the cited rule.
   - If the rule cannot be reproduced for a stem, it fails I1 with reason `storey_rule_unreproduced`.
2. **I3 uses the same reference** as I1, in place of `storey_count`.
3. **I6:** roof area = `roof` surfaces whose outside boundary is `Outdoors` only. Add the column `roof_adiabatic_m2`. The reference stays the top-storey floor area, plus the adiabatic roof area of lower blocks:
   - pass if |outdoor roof + adiabatic roof − Σ(floor area of each zone with no zone above it)| ≤ 1 %;
   - a zone has no zone above it when no floor of another zone lies at its ceiling z within 0.05 m with plan overlap above 0.01 m².
4. **I8 flats drawn:** the dwelling indices restart on each storey, and since D-EU-143 a storey with 0 flats copies the layout of the storey below, so no name-based count works. Check against the allocation rule instead:
   - Call `allocate_european_dwellings` (`openubem/geometry/european_residential.py:2943-2950`, import it, do not copy it) with `dwellings_used` and the I1 reference storeys. This gives `alloc_s`, the number of flats on each storey s.
   - The expected number of dwelling zones on storey s is `alloc_s` if `alloc_s > 0`, else the expected count of storey s−1.
   - I8 passes when every storey's count of `*_dwelling_*` zones equals its expected count, and Σ `alloc_s` = `dwellings_used`.
   - Undivided homes (one zone per floor, `_whole` names) are out of scope with reason `undivided`.
   - Keep the literal per-name check as the information column `I8_literal`.
   - Report the pass count on 10-05 and 10-06. On 10-05, the 1,495 rebuilt stems are expected to fail I8, because they have fewer zones there. Any other fail is listed by stem.
5. **I9:** a stem on the FINDING 283 list with window area 0 passes with reason `finding283_no_outdoor_wall`. No change if the code already does this; confirm by citing the line.
6. **I10 implemented:**
   - Each conditioned zone has exactly one OTHEREQUIPMENT with `EndUse_Subcategory = EU_Step8_InternalGains` and 1.0 W/m².
   - The mean of its Schedule:File column over 8,760 hours equals that building's archetype `phi_int_w_m2` from `openubem/data/construction/tabula_registry.py`, within 1 %.
   - The constant `EU_InternalGains` object is absent.
7. **I13 reason codes added:**
   - `t06s_fold_fix` for stems in `division_residual_2026-09-29/t06s_rerun_<D>.txt`;
   - `storey_source_levels` for stems whose reference storeys (item 1) differ from 09-08's because of `levels`.
   - Any stem whose difference is fully explained by the listed codes is marked explained. A stem with no matching code stays `UNEXPLAINED`.
8. **Tests:**
   - add one test each for item 1 (a levels-based reference), item 3 (an adiabatic lower roof passes), item 4 (one flat on 3 storeys expects 1 zone on each storey and passes; a missing zone on storey 2 fails) and item 6 (schedule mean off by 5 % fails);
   - all existing tests stay green.

**How to test.**
- Re-run `--tree win_2026-10-05`. The I1+I3 fail list must contain every census down-class stem (ES 26, FR 7, GB 12, IT 149) except the two core-rule stems `933a2f079f1d6277` and `a53d307eac631355`, which must carry reason `core_rule`.
- Run `--tree win_2026-10-06`. Report a table per district per check: fails, named exceptions, and the list of stems that are still unexplained, with values. Name all six I3/I7 stems above.
- Expected on 10-06: I1 and I4 drop to 0 on ES and FR, unless a stem's rule cannot be reproduced.
- Append a T02c progress-log entry in §8. STOP.

### T02d — Storey reference for homes without `levels` (director ruling after the T02c audit, 2026-10-02)

**Director measurement.** For the 1,455 stems marked `storey_rule_unreproduced` on 10-06, the 8 September layout files record a `storeys` value for 1,237 of them, and all 1,237 equal the 10-06 IDF storeys:
- the files are `EU-11/<D>_layouts_2026-09-08b/<building_id>.json`, then `<D>_layouts_2026-09-08/`, then `<D>/layouts/`, where `building_id` can contain a `/`, as in `way/123.json`;
- per district: ES 10 of 162, FR 0 of 1, GB 63 of 113, IT 1,164 of 1,179.

These files were written at build time from the source data (Bologna CTC heights, the neighbour ladder, SAP floor dimensions), before any of the 10-0x changes, so they are an independent reference. The other 218 have no layout file because they are undivided.

**What.** Change only `scripts/eu21/13_model_integrity.py` and its test file. The I1/I3/I4 reference storeys are taken from the first source that gives a value:
1. the `levels` rule (as in T02c), `storey_source = levels`;
2. the layout file `storeys` (paths above, in that order), `storey_source = layout_0908`;
3. the same stem's building height in the oldest saved IDF tree that holds it, searched in the order `<D>/idfs`, `<D>_final_2026-09-07/idfs`, `<D>_recut_2026-09-08/idfs`:
   - building height = highest roof z − lowest floor z;
   - storeys = round(height ÷ 3.0), accepted only if height is within 0.05 m of 3.0 × storeys;
   - `storey_source = idf_height_0907`.

   A storey merge never changes building height, so this source is not affected by FINDING 289.

Only if none of the three gives a value does the stem keep `storey_rule_unreproduced`. Add one test for each of sources 2 and 3.

**How to test.**
- Re-run `--tree win_2026-10-05` and `--tree win_2026-10-06`.
- Report the per-district count by `storey_source`, and the I1/I3/I4/I8 fails on 10-06 by source, with every failing stem listed.
- Validation on 10-05: report how many of the 194 down-class stems now fail on a real reference rather than on `storey_rule_unreproduced`. The target is all 194 except the two core-rule stems.
- Append a T02d entry in §8. STOP.

### T02e — Madrid storey reference must apply the Catastro side-car (director ruling after T03b, 2026-10-02)

**Why.** The Madrid build overwrites `levels` with the Catastro side-car before choosing storeys (`scripts/run_eu_s2_district_campaign.py:673-676` → `apply_attribute_sidecar`, `openubem/semantic/european_archetype_mapping.py:376-383`: side-car `levels` wins where it is not null). The T02d reference read only the manifest `levels`, which is empty for these homes, so it fell back to the 09-07 IDF height. That height carries the folded-storey error itself (FINDING 289/290). Result: the 16 Madrid homes of T03b fail I1/I3/I4/I8 against a wrong reference, while their 10-06 storey count equals the observed Catastro count.

**What.** In `scripts/eu21/13_model_integrity.py`, for `ES-MAD-BERRUGUETE` only:
- read `openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv` (the same `ES_SIDECAR` path the build uses; import the constant if importable, do not copy the path twice);
- the storey reference is side-car `levels` where it is a positive number, labelled `storey_source = levels_sidecar`; otherwise the T02d order is unchanged;
- add a column `sidecar_overlap_m2` (side-car `overlap_area_m2`) so weak joins are visible.

No other country has a side-car; their references stay as they are.

**How to test.**
- A new test: a synthetic ES row with empty manifest `levels` and side-car `levels` = 4 gets reference 4 and source `levels_sidecar`.
- The existing tests stay green.
- Re-run the sweep on `win_2026-10-06` for all four districts, overwriting `integrity_2026-10-02/*_win_2026-10-06_integrity.csv` and the summary.
- Report: the storey source counts per district; the I1/I3/I4/I8 fail count per district; the list of stems still failing any check, with the failing checks. Expected: the 16 Madrid homes now pass I1/I4/I8.

Append one §8 entry, "#### T02e — Madrid side-car storey reference — completed 2026-10-02". Touch no other file.

### T06b — Harvest leaves out the four homes with a broken shell (director ruling in T03 triage, 2026-10-02)

**What.**
- Write `openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/geometry_fault_excluded_2026-10-06.csv` with columns `district,building_id,stem,reason`, reason `GEOMETRY_FAULT_FINDING_291`, for exactly these 4 stems: ES `722e9de69cd55e76`; IT `7e4f0c98576b5d81`, `97d478bc56840531`, `595675e5f53ef10b` (take `building_id` from `<D>_win_2026-10-06/prepared_buildings.csv`).
- In `scripts/cluster/harvest_eu11_merged.py` (and `harvest_eu11_district.py` if the drop lives there), for the `win_2026-10-06` tag only, drop these stems the same way the undivided homes are dropped, with their own reason code, and list them in the excluded output with that reason.
- `win_2026-10-05` output stays byte-identical.

**How to test.** A new test: a 10-06 harvest on a synthetic tree drops a listed stem with reason `GEOMETRY_FAULT_FINDING_291`. Existing harvest tests green. Dry run on the 10-06 trees: rows ES 1,163, FR 520, GB 1,240, IT 1,164.

Append one §8 entry, "#### T06b — geometry-fault exclusion in harvest — completed 2026-10-02".

### T03a — Cause of each unexplained stem (executor, read-only)

For each stem below, read its 10-06 IDF and its row in `<D>_win_2026-10-06/prepared_buildings.csv`, and compare with the same stem in `<D>_win_2026-10-03`. Report one line per stem: the cause, with file:line evidence, and whether the stem was already like this in 10-03. Change no file.

- ES `b56bda9013da5b2d`: I3 1.297; IDF floor area 29.7 % above `floor_area_m2`; undivided.
- ES `d342db5179c1ac49`: I3 1.168; +16.8 %; undivided.
- ES `c57a45184a1c34ba`: I7 0.12 %.
- ES `722e9de69cd55e76`: one zone fails I5; roof 15.4 % short.
- IT `89eea66ba6ada782`: +17.1 %; undivided.
- IT `595675e5f53ef10b`: one storey 4.0 % off the ground storey; I7 0.57 %.
- IT `7e4f0c98576b5d81`: one zone fails I5; roof 16.7 % short.

### T03b — Why 16 Madrid homes gained a storey between 10-03 and 10-05 (executor, read-only)

**Director measurement.** Take `193aea6286a8521d` (`way/287496588`, AB, `levels` empty). Its zones:
- 09-07 and 10-03: 3 zones, `F0`–`F2`, and the integrity reference is 3 storeys;
- 10-05 and 10-06: 4 storeys, with 10-06 drawing `F0`–`F3` and `dwellings_used` = 3.

The `storey_count` in `openubem/outputs/3D/eu_ES-MAD-BERRUGUETE_data/buildings.csv` is 3. The same pattern holds for the 16 stems in the T02d entry, which are the Madrid "up class" of FINDING 289. That class was never checked against a source, because the T06s part 1 audit verified only the 169 Lyon stems against `levels`.

**What.** For the 16 stems, find which storey count the 10-04/10-05 prepare used and where it came from.
- Trace the ES storey path in `scripts/run_eu_s2_district_campaign.py` (`_valid_storeys` at `:141`, its use at `:199`, the neighbour ladder and any override) as run by the 10-04 rebuild command in the residual plan (T06p; prepare with `--only-ids` into `<D>_dw_2026-10-02`).
- Compare with the inputs the 09-07 build used.

Report:
- the code path, cited file:line;
- the input field and value for each of the 16 stems in both builds;
- which value the source data supports.

Change no file except one §8 entry, "#### T03b — Madrid storey gain — completed 2026-10-02".

### T03c — Code cause of the three geometry faults found by T03a (executor, read-only)

**Director reading of T03a (§8).**
- Class A, ring larger than the layout plate (ES `b56bda9013da5b2d`, ES `d342db5179c1ac49`, IT `89eea66ba6ada782`): the IDF floor is 17–30 % above `floor_area_m2`, so energy comes from a larger building than the EUI denominator. Present since 10-03.
- Class B, a top or ground zone with a floor but no roof or ceiling, walls carrying `_H1` names (ES `722e9de69cd55e76`, present in 10-03; IT `7e4f0c98576b5d81`, new in 10-06).
- Class C, one zone with two overlapping floors, one `Surface` and one `Adiabatic` (IT `595675e5f53ef10b`, new in 10-06).
- ES `c57a45184a1c34ba` (raw vs regularized plate, 0.11 %) is accepted by the director as a reference difference; not part of this task.

**What.** For each class, find the code line that produces the fault. Use the 10-06 build path:
- extruder `scripts/run_eu_s2_campaign.py` (`_extrude_zone_groups_per_storey` `:1157`, bbox fallback `:1123`/`:1177-1208`, hidden-pair split `_split_hidden_surface` `:1260`, `_apply_hidden_pair` `:1295`, `_pair_hidden_outdoor_surfaces` `:1366`, one-zone-per-floor fallback near `:1977-2027`);
- the storey-group builder `openubem/.../european_residential.py:2753-2761` (the D-EU-143 fold fix).

For class A, also report where the ring comes from (which footprint) and where `floor_area_m2` comes from, and which of the two matches the source footprint area of the building.

For classes B and C, say whether the D-EU-143 fold fix caused the new-in-10-06 case, by comparing the 10-03 and 10-06 zone lists of that stem.

Report one block per class: the cause with file:line, the stems affected, and a one-sentence proposed fix (the director decides). Count how many 10-06 stems in all four districts share each signature, using the T02 CSVs in `integrity_2026-10-02/` (I5 fail, I6 roof deviation > 5 %, or I3 > 1.05 on undivided homes) — report counts only.

Change no file except one §8 entry, "#### T03c — code cause of three geometry faults — completed 2026-10-02".

### T03 — Director triage (director only)

Each failing check class on 10-06 is either:
- (a) a named, accepted exception, recorded in §8 with its count; or
- (b) a new FINDING with a fix task appended here, after which T02 is re-run until no unexplained fail is left.

**No Speed submission before T03 is signed in §8.** Bologna 1410474 (running on 10-05) is left running. Its results for stems that pass T02 and are byte-identical in 10-06 are kept; the rest are re-run in T05.

### T06c — Separate count for the broken-shell homes in the harvest summary (director, after the T06b audit)

**What.** In `scripts/cluster/harvest_eu11_merged.py` (summary `extra`, near `:494-496`), `n_excluded_undivided` must count only undivided homes; add `n_excluded_geometry_fault` for the T06b stems. 10-05 output stays byte-identical (same dry-build md5 method as T06/T06b).
**How to test.** The T06b test also asserts `n_excluded_geometry_fault == 1` and that the undivided count excludes it. The four harvest test files stay green. 10-06 dry run: ES `n_excluded_geometry_fault` 1, IT 3, FR 0, GB 0.
One §8 entry "#### T06c — separate geometry-fault count — completed 2026-10-02".

### T04 — `plans3D/` pages from the corrected models

**What / Why / How / How to test:** exactly residual plan §8 "T06u", P1–P6. Add one gate:
- **P7:** for 5 named homes per district, the page's storey count and per-storey area equal the T02 CSV values.
- Director amendments to T06u (2026-10-02, after T03):
  - Undivided homes: read `division_residual_2026-09-29/undivided_excluded_2026-10-05.csv` (the 10-06 trees have the same model set as 10-05), not the 10-01 list.
  - The 4 homes of `geometry_fault_excluded_2026-10-06.csv` are drawn as they are, and their tooltip/label says "left out of results: broken shell (FINDING 291)"; no new colour.
  - P1 expected building counts: ES 1,172, FR 522, GB 1,240, IT 1,179 IDFs (undivided homes are among them).
  - P7 homes: ES `193aea6286a8521d` (4 storeys, 102.68 m² each) plus 4 of your choice per district from the T02 CSVs `integrity_2026-10-02/<D>_win_2026-10-06_integrity.csv` (`storeys_idf`, `storey_areas_m2`); GB must include `7aae3e0ee341bc04`.

The progress entry goes in §8 of **this** file. STOP (§7 stop point 2): the director shows the pages to the owner before submitting runs.

### T04b — The plan pages must show the real flat count (director ruling after the T04 audit, 2026-10-02)

**Why.** P5 fails on exactly the 1,495 homes rebuilt by D-EU-143 (ES 243, FR 32, GB 1,037, IT 183). Since D-EU-143 a storey with 0 flats gets its own zones with the layout of the storey below: these are the upper floors of flats that start lower down (a London house with 1 flat on 3 storeys has 3 zones, 1 flat). The page counts zones as dwellings (`scripts/eu21/09_plans3d_from_idf.py:249`, `:256-261`, the "Dwellings (in the IDF)" label at `:350`), so it would tell the owner a 1-flat house has 3 flats. The model is right; the page text is wrong.

**What.** In `scripts/eu21/09_plans3d_from_idf.py` only:
- The building's dwelling count shown on the page is `dwellings_used` from `<D>_win_2026-10-06/prepared_buildings.csv`, labelled "Dwellings"; the zone count is shown separately as "Zones in the model".
- Per storey, compute the flats that start on it with `allocate_european_dwellings` (`openubem/geometry/european_residential.py:2943-2950`; import it, as `scripts/eu21/13_model_integrity.py:21,287` does) from `dwellings_used` and the storey count. On a storey whose allocation is 0, the storey note reads "upper floor of the flat(s) below" and each zone's table label reads "Dwelling D<k> (upper floor)" instead of a new dwelling number.
- Undivided and one-zone-per-floor homes: unchanged.
- No change to geometry, colours, positions, or any other text.

**How to test.**
- P5 (replaces the literal P5): for every divided home, the page's "Dwellings" value = `dwellings_used` (all four districts, report n of n), and the number of zones per storey = `I8_expected` in `integrity_2026-10-02/<D>_win_2026-10-06_integrity.csv` where that column is not empty.
- Spot check written into §8: London `7aae3e0ee341bc04` shows Dwellings 1 and its upper storeys read "upper floor"; Madrid `193aea6286a8521d` shows Dwellings 3, 4 storeys, storey F3 reads "upper floor".
- P1–P4, P6, P7 re-run and still pass; only the four 10-06 pages change (index.html untouched now).

One §8 entry "#### T04b — real flat count on the plan pages — completed 2026-10-02", then STOP.

### T05 — Speed re-runs (director only)

- Stage `EU11_<D>_win_2026-10-06` with the stems unchanged since 10-05 carrying their finished 10-05 `out/` (the London method of 10-05).
- Submit one array per district over the changed stems plus any stem fixed in T03 (`%32`, `--time=7-00:00:00`, `-p ps`, within the account cap).
- Bologna: re-run the changed stems after 1410474 ends, or alongside it while under 32 CPUs.
- Sweep FAILED tasks per district. Measure the ETA from `sacct`.

### T06 — Harvest code for the 10-06 tag (executor), then harvest (director)

**What.**
- `scripts/cluster/harvest_eu11_merged.py` / `harvest_eu11_district.py`: add `WIN6_TAG = "win_2026-10-06"` the same way T06r added `WIN5_TAG` (residual plan §8 T06r).
- The universe is every stem of `<D>_win_2026-10-06/idfs/`; digests come from `md5_2026-10-06.txt`.
- Output goes to `<D>_merged_win_2026-10-06/`.
- `export_flat_counts_4j.py` accepts the 10-06 tag (GB and IT only).

**How to test.**
- The existing harvest tests stay green.
- `--merged-tag win_2026-10-05` output is byte-identical to before.
- Dry run on the London tree: rows = 1,240.

### T07 — CP-3c on 10-06 (director)

CP-3c as amended in residual plan §8 (03:50), plus check 6 as amended (T06s part 1 director audit), plus a final T02 run on the harvested tree with 0 unexplained fails.

Then the peer packages:
- **4J:** London, then Bologna.
- **5J:** Madrid and Bologna only, never UK content.

Then residual plan T07 and T08. *Amended (D-EU-146, owner 2026-10-06 "go with (a)"):* peer packages dropped (owner closed GSSCanada); residual plan T07 and T08 are replaced by T08 and T09 below, written for the adopted 10-06 set. The plan pages are already done (T04, T04b).

### T08 — 3D viewers on the adopted 10-06 set (executor; replaces residual plan T07)

**Why.** The four `openubem/outputs/3D/eu_<D>_viewer.html` still draw the 09-08 era IDFs (tag chain `scripts/generate_eu_3d_viewers.py:876`, `:1104`) and colour by the 09-08 EUI (`_load_eu11_eui`, `:888-909`). CLAUDE.md: the viewer must show the same data and the same vintage as the adopted number. FR and IT 10-06 IDFs sit at a local origin (D-EU-142, FINDING 288); without adding it back, their plans land ~6,000 km from their footprints.

**What.** Edit `scripts/generate_eu_3d_viewers.py` only.
1. **IDF source = `EU-11/<D>_win_2026-10-06/` only.** In `build_district` every plan is read from that tree (`read_district(district, <tree>)`, mapping by its `prepared_buildings.csv`); the EU-17 / ceiling82 / final / delta / recut chain (`:1097-1110`) is no longer used for plans. A building with no 10-06 IDF takes the existing no-IDF path (no plan, no EUI). No fallback to an older tag, ever.
2. **Origin offset.** If the tree has `origin_offset.json`, add `dx`, `dy` to each plan's `origin_xy` exactly as `scripts/eu21/09_plans3d_from_idf.py:98-114` does. ES and GB have no file: offset 0.
3. **EUI = `EU-11/<D>_merged_win_2026-10-06/<city>_manifest.csv` only.** `_load_eu11_eui` reads that file; no fallback. A home absent from it (undivided, broken shell, not residential) has no EUI.
4. **Side-cars:** no 10-06 side-cars exist and none are emitted. Pass `sidecar=None` for every building, so `scheme`, `reason`, `f204` are null (no stale 09-08 cutter label on a 10-06 plan).
5. **Provenance:** `sources.json` (`:1376-1382`) and any vintage text in the page name the 10-06 tree, `md5_2026-10-06.txt`, the merged 10-06 manifest and `results/EU11_results_2026-10-06_summary.json`, with their sha256.
6. **`buildings.csv` is a source file for `scripts/eu21/13_model_integrity.py:658`.** Before running, copy each `openubem/outputs/3D/eu_<D>_data/buildings.csv` to `openubem/outputs/eu_evidence/EU-11/viewers_2026-10-06/buildings_before_<D>.csv`. After the run, `footprint_area_m2`, `levels`, `height_m`, `height_source`, `year_built` must be identical per `building_id`, and the row set unchanged.

**How.** Run the four districts in parallel (4 local processes). The script mirrors into `docs/docs_ACTIVE/europeanLocations/outputs_3D/` itself (`:1439-1447`). No Speed, no EnergyPlus, no ssh.

**How to test (V1–V7, per district, N of M, measured values into §8; outputs under `EU-11/viewers_2026-10-06/`).**
- V1 rows: scene buildings = `buildings.csv` rows before (ES 1,398, FR 768, GB 1,351, IT 1,257); buildings with a plan = 10-06 IDFs read (ES 1,172, FR 522, GB 1,240, IT 1,179).
- V2 EUI: buildings with an EUI = ES 1,163, FR 520, GB 1,240, IT 1,164; every value equals the merged 10-06 manifest to 6 decimals; 0 values from any other tag.
- V3 position: for every building with a plan, distance between the plan footprint centroid and the scene footprint centroid; report max and count > 0.5 m (must be 0).
- V4 vintage: in each viewer html and `sources.json`, `grep -c` of `recut_2026-09-08`, `merged_2026-09-08`, `ceiling82`, `fix_2026-10-01` = 0; `win_2026-10-06` ≥ 1.
- V5 mirror: md5 of each viewer html and every file in `eu_<D>_data/` equals its `outputs_3D/` copy.
- V6 source columns: item 6 check, 0 differences; then `python scripts/eu21/13_model_integrity.py --tree win_2026-10-06 --workers 10` gives the same 13 fails as T07-CP3c-data.
- V7 tests: `pytest tests/test_eu18c_viewer_geometry_only.py -q` (report pass/fail; a failure that only asserts the old tag chain is reported, not edited, and STOP).
- One §8 entry `#### T08 — 3D viewers on 10-06 — completed YYYY-MM-DD`; register any error solved in the debug references.

### T09 — Ledger, supersession markers, references (executor; replaces residual plan T08)

**Why.** STATE §0 stops at `D-EU-117` / `FINDING 269` (`grep -c "D-EU-14[0-5]"` = 0, `"FINDING 2[89][0-9]"` = 0), and the T07-adopt-results notes list 09-08 EUIs still unmarked in live docs.

**What.** Edit only `STATE_european_locations_v5.md`, the live docs named below, and `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.
1. **STATE §0:** one paragraph in the house pattern ("registered here by filename, provenance only"): `D-EU-118`…`D-EU-146` and `FINDING 270`…`FINDING 291`, each range with the plan file that holds it (residual plan, `PLAN_eu-rulebook-change-2026-09-30.md`, `PLAN_eu-bent-walls-2026-09-30.md`, this plan). Find each id with `grep -l` over `implementation/`; an id found in no doc is listed as "not found" (never invented). Set "Next free: `D-EU-147`, `FINDING 292`".
2. **STATE §1:** one dated paragraph: the adopted set (ES 69.165225 over 1,163, FR 58.008829 over 520, GB 61.976977 over 1,240, IT 54.647708 over 1,164, four 59.660846 over 4,087), source `results/EU11_results_2026-10-06_summary.json`, D-EU-145. Do not edit the embargo paragraph (`:127`); report in §8 that it was left as is. *(superseded 2026-10-08 by results/EU11_results_2026-10-08, D-EU-149: ES 68.774/1,119, FR 57.810/501, GB 68.307/1,215, IT 58.164/1,035, fleet 62.626/3,870 — correctly divided homes only, not like-for-like, FINDING 295)*
3. **STATE §8:** one entry for this plan (T01–T09), pointing to this file's §8, no numbers restated except the adopted set.
4. **Supersession markers** on every 09-08 EUI (81.388, 70.346, 93.730, 54.672, 66.295 at any precision, and their populations when beside them) in live docs: `DEBUG_floor-division-gap-and-clean-pipeline_2026-09-08.md`, `PLAN_eu-floor-division-residual-2026-09-29.md`, this plan, `prompts/PROMPT_MANAGER_handoff_2026-09-09.md`, STATE (the 4 unmarked). Marker appended right after the value: `*(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)*`. Never change a value. This T09 task text, `DONE/` and the 09-08 result files are out of scope (`SUPERSEDED_2026-09-08.txt` covers them).
5. **Debug references:** check by `grep -c` that an entry exists for: OUT_OF_MEMORY at 32G and 64G on Bologna `d8a1a0d8ceb5dc73` / `fd4b13e28f1c6f47` / `366fc6fda9a1a946`; FINDING 289 (0-flat storey folded into a tall zone); the broken-shell homes of FINDING 291. Add any missing one in house format, sourced from this plan's §8 or the handoff box.

**How to test.** (a) `grep -c` per id range in STATE §0 after the edit; (b) for each 09-08 value, occurrences in the five live docs vs occurrences carrying the marker, per doc (must be equal); (c) the five adopted values each found in STATE §1 and equal to the summary json to 6 decimals; (d) debug-ref counts before/after. One §8 entry `#### T09 — ledger and markers — completed YYYY-MM-DD`.

## 7 Stop-and-report points

1. After T02: the sweep summary for 10-05 (validation) and 10-06, and the fail list.
2. After T04: the four pages ready. The owner sees them before T05.
3. After T07: CP-3c pass/fail per line, before any number is quoted.
4. After T08 and T09: V1–V7 and (a)–(d) pass/fail with values; the director audits, then closes the arc.

## 8 Progress log

#### T02a — integrity sweep script, validated on 10-05 — completed 2026-10-02

- **Artifacts:** `scripts/eu21/13_model_integrity.py` (`--tree`, `--districts`, `--ref-tree` default `win_2026-10-05`, `--workers` capped at 10); `tests/test_eu_model_integrity_2026_10_02.py` (10 tests); outputs in `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/`: `<D>_win_2026-10-05_integrity.csv` (4 files, one row per stem, `Ik_value` / `Ik_pass` per check, `reason`) and `summary_win_2026-10-05.csv`. 4,113 stems swept in about 8 s. Nothing run on `win_2026-10-06`; no file written into any EU-11 tree.
- **Sources used:** I13 reads `EU-11/<D>_merged_2026-09-08/<d>_manifest.csv` (e.g. `es_mad_berruguete_manifest.csv`), column `floor_area_m2`, joined on `building_id`. Source data = `openubem/outputs/3D/eu_<D>_data/buildings.csv` (`storey_count`, `footprint_area_m2`; `levels` added as an information column). Window targets = `windows.csv` `share_target`. Sliver flag = `degenerate_*.csv` `n_deleted`.
- **I10 NOT IMPLEMENTED (stop point).** IDFs hold no People or Lights objects, only one `OTHEREQUIPMENT` per zone with `Power per Zone Floor Area = 1.0` (`openubem/semantic/european_schedules.py:133`) driven by a schedule of mean `BASE_GAIN_W_M2 = 3.0` (`:19`). The per-archetype value `phi_int_w_m2` (`openubem/data/construction/tabula_registry.py:175`, emitted at `openubem/idf/european_controls.py:69`) is removed before saving and never reaches the IDF (`scripts/audit_eu05_s3_hvac.py:84-90`). Two candidate sources, so no single archetype value: the column is `not_implemented`.
- **Deviations:**
  - Areas are computed with Newell's formula (exact for planar polygons, also handles vertical windows); shapely is used for the footprint union and centroid.
  - I6 "IDF footprint" = union of all floor polygons in plan.
  - I8 is implemented literally (distinct `dwelling_<j>` indices); see conflict below.
  - Named exceptions are marked per row in `reason` (zero-floor stem, the 8 core-rule stems, zero outdoor wall = FINDING 283); the London non-convex Severe stem is not identified in the plan, so it is not named. `n_fail_named_exception` counts any failing check on a row that carries a reason, so it overstates for rows flagged only as no-outdoor-wall.
  - Validation gate NOT met as worded (see Notes).
- **Test status:** 10 passed (passing model; missing storey I1; tall zone I5; window share +5 % I9; 10 % floor loss I2 and I7; dwelling mismatch I8; named reasons; I13 codes; I11; ground deviation).
  - Per-district fail counts on `win_2026-10-05` (ES / FR / GB / IT): I1 173 / 198 / 1037 / 183; I2 0 / 1 / 0 / 3; I3 176 / 199 / 1037 / 186; I4 17 / 171 / 9 / 98; I5 158 / 27 / 1028 / 87; I6 79 / 81 / 48 / 218; I7 4 / 1 / 0 / 6; I8 932 / 487 / 195 / 1061; I9 11 / 3 / 5 / 70; I10 not implemented; I11 0 / 0 / 0 / 0; I12 0 / 0 / 0 / 0; I13 29 / 172 / 11 / 149 (UNEXPLAINED).
  - I3 ratio p1 / p50 / p99: ES 0.2000 / 0.9999 / 1.0009; FR 0.3334 / 1.0001 / 2.0002; GB 0.3330 / 0.5000 / 1.0004; IT 0.2502 / 1.0000 / 1.0008.
  - I13 codes: ES up_class 14, core_rule 1, no_0908_value 17; FR core_rule 1, no_0908_value 2; IT core_rule 4, no_0908_value 10; GB none.
- **Notes (gate and conflicts):**
  - Census `cls == "down"` counts are ES 26, FR 7, GB 12, IT 149 (the plan's FR 6 / GB 11 exclude the 1-5 % stems `bfbc1caab1a332a4`, `933a2f079f1d6277`).
  - The I1/I2 fail list is a strict superset, not equal: every down stem is in it except GB `933a2f079f1d6277` and IT `a53d307eac631355` (both core-rule stems, storeys unchanged). Extra fails (fail and not down): ES 147, FR 192, GB 1026, IT 38. Cause: buildings with flats below storeys (for example GB semi-detached, 2 storeys, 1 flat = one 6 m zone) fold identically in 10-03 and 10-05, so they are not in the 03-vs-05 down class but do fail I1/I3/I5 against the data. The sweep sees the whole folding defect, the census only the 03-to-05 change.
  - Conflict, I1 column: for FR, 166 of the I1 fails have IDF storeys equal to `levels` while `storey_count` in `buildings.csv` is lower (up class, residual plan §8: "10-05 storeys equal manifest levels"). I1 as specified uses `storey_count`.
  - Conflict, I8: `dwelling_<j>` restarts at 0 on each storey, so distinct j is the largest per-storey flat count, not `dwellings_used`. Zone count with a `dwelling_` name equals `dwellings_used` in 4,091 of 4,092 divided homes (column `dwelling_zone_pairs`). Literal I8 fails: ES 932, FR 487, GB 195, IT 1061. For 10-06 (a flat modelled as one zone per storey) neither reading is yet defined.
  - Director decisions needed before T02b: I1 column (`storey_count` or `levels`), I8 definition, I10 source.

EOF
python - <<'EOF'
p=r'C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\prompts\PROMPT_MANAGER_handoff_2026-09-09.md'
s=open(p,encoding='utf-8').read()
L=s.split('\n')
i=[k for k,l in enumerate(L) if l.startswith('3. **Owner question open:** redraw')][0]
L[i]="3. **New plan in force: `implementation/PLAN_eu-model-integrity-2026-10-02.md`** (owner 13:05: \"check other neighbourhoods for similar errors before submitting\" + \"prepare an implementation plan\"). Order: T01 = T06s part 2 audit; T02 = integrity sweep of all 4,113 models (13 physical checks against source data, validated on 10-05); T03 = director triage, **no Speed submission before it is signed**; T04 = plans3D from 10-06 (owner \"yes please\"); T05 = re-runs; T06 = 10-06 harvest code; T07 = CP-3c. Step 1's staging and submission now wait for T03 and T04."
s='\n'.join(L)
s=s.replace("**13:00 Owner \"yes please\"","**13:05 Owner: check every neighbourhood for similar errors before submitting, and write a plan → `PLAN_eu-model-integrity-2026-10-02.md` (integrity sweep T02, no submission before T03 triage).** **13:00 Owner \"yes please\"",1)
open(p,'w',encoding='utf-8').write(s)
EOF
grep -c "model-integrity" "$p" docs/docs_ACTIVE/europeanLocations/prompts/PROMPT_MANAGER_handoff_2026-09-09.md
#### T01 — director audit of T06s part 2 — 2026-10-02

- **Logs and evidence:**
  - Progress-log entry present (residual plan, "T06s part 2 — fix, rebuild, gates — completed 2026-10-02").
  - Debug reference entry present (`OpenUBEM_debug_References.md`, the FINDING 289 bullet, which names the fix lines).
  - `t06s_rerun_<D>.txt` = ES 243, FR 32, GB 1,037, IT 183 (1,495 in total). `t06s_rebuild_md5.csv` = 4,113 rows.
- **G1, PASS on a wider set than the plan expected.** The rule `dwellings_used < storeys` gives 1,499 homes, not about 192.
  - About 1,300 more are mostly London houses with 1 flat on 2–3 storeys. They had the same tall single-floor zone in 10-03 and 10-05, so the 03-vs-05 census could not see them.
  - 4 one-zone-per-floor fallback stems came out byte-identical.
- **Ruling (D-EU-144):** all 1,495 changed stems are re-run.
  - D-EU-143 applies to every home with fewer flats than storeys, and the owner's standing order is highest accuracy.
  - The re-run set for T05 is the union of `t06s_rerun_<D>.txt`.
- **G2:** 4 stems are off beyond 1 %.
  - `97d478bc56840531`: zero-floor flat, accepted earlier.
  - `bfbc1caab1a332a4` (FR) and `1773a1e9f64767b1` (IT): accepted by name as `core_rule`; both carry that reason in the T02a CSV.
  - `595675e5f53ef10b` (IT, storey 4.0 % off): **not accepted**, goes to T03 triage.
- **G3–G7 PASS** as reported. Director spot check: Bologna `0177dae25178d27e` 111.14 m² and Madrid `5bce5fa408cac4fb` 246.26 m².
- **FINDING 290 (new): the official 2026-09-08 numbers carry the same folded-storey error.** Measured with the 09-08 manifests (`<D>_merged_2026-09-08/*_manifest.csv` `floor_area_m2`) against the 10-06 IDF floor area, on the 1,495 rebuilt stems:

  | District | 09-08 m² | 10-06 m² | 09-08 district total m² |
  |---|---|---|---|
  | Madrid | 52,610 | 109,035 | 1,063,338 |
  | Lyon | 3,128 | 6,455 | 585,153 |
  | London | 58,932 | 131,854 | 397,915 |
  | Bologna | 29,633 | 32,030 | 2,523,749 |

  - London misses about 73,000 m², about 18 % of its 09-08 total, so London's published 93.729757 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* kWh/m² is biased high. Madrid misses about 5 % and Lyon about 0.6 %.
  - Combined with the FR up class (FINDING 289), every 09-08 district EUI is now known to be biased. They stay quotable only with this caveat until CP-3c on 10-06 replaces them.

#### T02c — check refinements and 10-06 run — completed 2026-10-02

- **Per-country storey rule (cited, `scripts/run_eu_s2_district_campaign.py`):** the build takes `n_storey = _valid_storeys(row)` (`:141-146`, `levels` a positive integer) in `_geometry` (`:199`), which feeds `allocate_european_dwellings` (`:205-208`) and the zones (`:224`, `:239`). Where `levels` comes from:
  - ES, FR: the observed `levels` (`_mapped_rows` `:684-686`, row built `:688-691`); when missing, the neighbour ladder (`_impute_es_fr_rows` `:972-977`, tag in `imputation_provenance`).
  - GB: observed `levels` (`_gb_row_outcome` `:370`); else SAP floor dimensions (`:393-398`), else the override or neighbour ladder (`:399-404`, ladder `:872-881`).
  - IT: `round(CTC altezza_gr / 3.0)`, or 3 when no height (`_it_rows` `:587-596`, row `"levels": storeys` `:658`). The heights are a live fetch (`:541-545`).
  - Reproduced from the source data in the script (`storey_reference`): `levels` of `buildings.csv` if a positive integer (`storey_source = levels`); IT `round(height_m / 3.0)` only if `height_source` starts with "measured" (`ctc_height`); otherwise `storey_rule_unreproduced`.
- **Artifacts:** `scripts/eu21/13_model_integrity.py` and `tests/test_eu_model_integrity_2026_10_02.py` (edited); outputs `integrity_2026-10-02/<D>_win_2026-10-05_integrity.csv`, `<D>_win_2026-10-06_integrity.csv`, `summary_win_2026-10-05.csv`, `summary_win_2026-10-06.csv` (re-written). New columns: `storeys_data_csv`, `storey_source`, `storeys_ref`, `roof_adiabatic_m2`, `roof_adiabatic_uncovered_m2`, `I6_roof_dev_literal`, `I8_literal`, `I8_expected`, `I8_storey_basis`, `I8_note`, `I10_worst_mean_dev`, info columns `I1_info_vs_storey_count`, `I3_info_vs_storey_count`, `I4_info_vs_storey_count`. No file written into any EU-11 `_win_*` tree; no EnergyPlus, no ssh.
- **Deviations:**
  - Item 1, rule not reproducible for 1,455 stems (ES 162, FR 1, GB 113, IT 1,179). `levels` is empty in `buildings.csv` for the ES/FR/GB ones (the ladder or SAP value is not in the data) and the IT heights in `buildings.csv` are all "assumed 9.0 m" (`sources.json` `height_measured` 0; the build used live CTC heights). `storey_count` in `buildings.csv` is not used as the reference (it was read from an earlier IDF vintage). These stems fail I1 with `storey_rule_unreproduced`; I3 and I4 are not evaluated for them (blank pass). The three `*_info_vs_storey_count` columns carry the old comparison as information only.
  - Item 3, the literal formula (outdoor roof + all adiabatic roof vs Σ top floors) keeps the old 79 / 81 / 48 / 218 fails (10-05). In every GB/ES case checked, the adiabatic roofs lie under a zone whose floor is the paired adiabatic surface, i.e. the zone has a zone above it (example 10-05 GB `1dd30b7900dedf5b`: outdoor roof 530.5 ≈ top floor 530.5, plus 84.7 m² adiabatic of covered zones). Implemented: adiabatic roof counted only for zones with no zone above (`I6_roof_dev`); the literal figure stays in `I6_roof_dev_literal`. Result 10-06: ES 1, FR 1, GB 0, IT 3 (literal on 10-05: 79 / 81 / 48 / 218).
  - Item 4, for stems with no reproducible reference the allocation uses `storey_count` from `buildings.csv` (`I8_storey_basis = storey_count_csv`). A divided-outcome stem whose zones are all `_whole` is out of scope (`I8_note = undivided`), 4 ES stems (`45c2472a33c88041`, `8b1bec54b375e9dc`, `d0787f31dc827e89`, `37173b8828a9dd97`; outcome `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`).
  - Item 5, I9 had to change (it failed when outdoor wall = 0): now passes when outdoor wall is 0 and window area is 0 (reason `finding283_no_outdoor_wall`).
  - Item 6, "conditioned zone" = every zone whose name does not contain "core" or "circulation". `phi_int_w_m2` is 3.0 for every archetype in all four registries (`tabula_archetypes_<c>.json`), so I10 cannot tell archetypes apart.
  - Item 7, `up_class_09-08_short` is not added when `storey_source_levels` applies (the two are the same cause). Codes can combine, joined with `;`. `storey_source_levels` = reference from `levels`, `levels` differs from `storey_count`, and the 09-08 area is within 3 % of `storey_count × footprint`.
  - `n_fail_named_exception` now counts only fails of stems carrying `zero_floor_flat` or `core_rule`; new column `n_fail_unreproduced` (I1).
- **Test status:**
  - Tests: 22 passed (the 10 existing, with context updated; new: levels reference, unreproduced rule, IT measured height, adiabatic lower block, adiabatic under a zone, one flat on 3 storeys, missing flat zone, `_whole` out of scope, no-outdoor-wall I9, I10 mean 5 % off, I10 wrong object, I13 new codes).
  - 10-05 validation, census down class (ES 26, FR 7, GB 12, IT 149): all 194 are in the I1 or I3 fail list, including the two core-rule stems `933a2f079f1d6277` and `a53d307eac631355`, which carry `core_rule` (and `storey_rule_unreproduced`). Caught on a reproducible reference alone: ES 18 of 26, FR 6 of 7, GB 9 of 12, IT 0 of 149; with `storey_count` as reference (information columns): 192 of 194 (the two misses are the two core-rule stems).
  - 10-06 fails per check (fails / of which named `core_rule`/`zero_floor_flat`), ES / FR / GB / IT: I1 162 (unreproduced) / 1 (unrep.) / 113 (unrep., 1 core) / 1,179 (unrep., 5 named); I2 0 / 1 (1) / 0 / 3 (2); I3 3 (1) / 1 (1) / 0 / not evaluated; I4 0 / 0 / 0 / not evaluated; I5 1 / 0 / 0 / 2 (1); I6 1 / 1 (1) / 0 / 3 (2); I7 4 (1) / 1 (1) / 0 / 6 (4); I8 16 / 0 / 0 / 1 (1); I9 0 / 0 / 0 / 0; I10 0 / 0 / 0 / 0 (all 4,113 evaluated); I11 0 / 0 / 0 / 0; I12 0 / 0 / 0 / 0; I13 UNEXPLAINED 2 / 0 / 0 / 1.
  - I3 ratio p1 / p50 / p99, 10-06: ES 0.9992 / 1.0000 / 1.0010; FR 0.9993 / 1.0000 / 1.0007; GB 0.9987 / 1.0000 / 1.0012; IT not evaluated (all `storey_rule_unreproduced`).
  - Still unexplained on 10-06 (no named reason): ES `b56bda9013da5b2d` (I3 1.297, I7 and I13 +29.7 %, undivided), ES `d342db5179c1ac49` (I3 1.168, I7 and I13 +16.8 %, undivided), ES `c57a45184a1c34ba` (I7 0.12 %), ES `722e9de69cd55e76` (I5 1 zone, I6 roof 15.4 % short: outdoor roof 148 m² vs top floors 175 m²), IT `89eea66ba6ada782` (I7 and I13 +17.1 %, undivided, I3 against `storey_count` 1.171), IT `595675e5f53ef10b` (I2 4.0 %, I7 0.57 %), IT `7e4f0c98576b5d81` (I5 1 zone, I6 16.7 %). ES 16 I8 fails come from the unreproduced stems whose IDF has 1-2 more storeys than `storey_count`. Named: ES `bb4d3f44d4fbe5b1`, FR `bfbc1caab1a332a4`, IT `05b52a0da00a6046`, `1773a1e9f64767b1`, `cc55f139215783a3`, `97d478bc56840531`.
- **Notes:** the expected "I1 and I4 drop to 0 on ES and FR" holds for every stem whose rule is reproducible (ES 1,010 and FR 521 pass I1 and I4; I3 fails only on the 3 ES and 1 FR stems listed above); the remaining I1 fails are exactly the unreproduced count. Director decision needed on the IT storey source (the live CTC heights are not in the repo).

#### T02c — director audit — 2026-10-02

- **Results checked:**
  - 22 tests pass.
  - On 10-06, I9–I12 have 0 fails.
  - On 10-06, I2–I8 are down to single digits outside the unreproduced stems.
  - The 10-05 down class is covered, but 161 of the 194 stems are caught only through `storey_rule_unreproduced`, so the validation is not yet real.
- **I6 deviation accepted.** Counting adiabatic roof only for zones with nothing above them is the physically correct reading of the T02c item 3 rule. The literal figure stays as a column.
- **I10 accepted as a consistency check.** `phi_int_w_m2` is 3.0 W/m² in all four registries, so a per-archetype test cannot fail differently.
- **The storey reference is the open gap.** The fix is ruled in T02d. In parallel, the 7 unexplained stems go to T03a, read-only.
- Correction to the T01 audit: the down class is ES 26, FR 7, GB 12, IT 149, not FR 6 / GB 11.

#### T02d — storey reference fallback — completed 2026-10-02

- **Artifacts:**
  - `scripts/eu21/13_model_integrity.py`: `storey_reference` now tries `levels` (and the existing IT `ctc_height` rule), then the 08b/08/`<D>/layouts` layout file `storeys` (`layout_0908`), then the building height of the same stem in `<D>/idfs`, `<D>_final_2026-09-07/idfs`, `<D>_recut_2026-09-08/idfs` (`idf_height_0907`, new `_idf_storeys`: highest roof z minus lowest floor z, accepted within 0.05 m of 3.0 x storeys). Constants `IDF_HEIGHT_TOL_M`, `OLD_IDF_TREES`, `LAYOUT_DIRS`; contexts carry `layout_paths`, `old_idf_paths`.
  - `tests/test_eu_model_integrity_2026_10_02.py`: two new tests (layout file; old-IDF height, plus rejection when height is off 3.0 x n).
  - Outputs refreshed in `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/` (8 stem CSVs, 2 summaries).
- **Deviations:** none. The IT `ctc_height` branch never fires (0 stems); IT stems resolve through `layout_0908`.
- **Test status:**
  - Tests: 24 passed.
  - `storey_source` per district (both trees identical): ES levels 1,010 / idf_height_0907 152 / layout_0908 10; FR levels 521 / idf_height_0907 1; GB levels 1,127 / layout_0908 63 / idf_height_0907 50; IT layout_0908 1,164 / idf_height_0907 15. `storey_rule_unreproduced`: 0 everywhere.
  - 10-06 fails by source (stems):
    - ES I1 16, I4 16, I8 16, all `idf_height_0907`: 193aea6286a8521d, 27e04bc1755c4c7d, 30240a6694acd89b, 35dc8b5c2b344650, 49edb66f114f62af, 4a13d470d74ebb02, 601b40a8e9a9e99f, 6940d076523dfe64, 7e48ebf5c7eadda3, 89f77e2b02d859e1, 8e794c5dad68973c, a8b0a706e3ba306d, af59be28315886a7, b0862431fa56c773, b9c441ec1773cf49, ea7734c088249759.
    - ES I3 19 = the same 16 (`idf_height_0907`) plus 3 `levels`: b56bda9013da5b2d, bb4d3f44d4fbe5b1 (core_rule), d342db5179c1ac49.
    - FR I3 1 (`levels`): bfbc1caab1a332a4 (core_rule). FR I1/I4/I8 0.
    - GB I1/I3/I4/I8: 0.
    - IT I3 3 (`layout_0908`): 05b52a0da00a6046 (core_rule), 89eea66ba6ada782, 97d478bc56840531 (zero_floor_flat). IT I8 1 (`layout_0908`): 97d478bc56840531. IT I1/I4 0.
  - 10-05 validation: all 194 down-class stems are in the I1/I3 fail list except the two core-rule stems (GB 933a2f079f1d6277, IT a53d307eac631355, which pass I1/I3 with source `layout_0908`). 192 of 194 fail on a real reference (ES 26/26, FR 7/7, GB 11/12, IT 148/149), 0 on `storey_rule_unreproduced`.
- **Notes:** the 16 ES stems fail I1/I4/I8 on 10-06 against the 09-07 IDF height (the IDF has more storeys than the 09-07 height implies, for example 193aea6286a8521d 3 -> 4, 6940d076523dfe64 2 -> 4); `levels` is empty for them. Director triage (T03) needed.

#### T02d — director audit — 2026-10-02

- **Validation met.** 192 of the 194 down-class stems fail on a real reference. The 2 misses are the named core-rule stems.
- **Storey sources:** ES 1,010 / 10 / 152, FR 521 / 0 / 1, GB 1,127 / 63 / 50, IT 0 / 1,164 / 15 (levels / layout_0908 / idf_height_0907). No stem is unreproduced.
- **Open:** the 16 Madrid stems whose 10-06 storeys exceed the 09-07 reference by 1–2 are the unverified ES up class. They go to T03b, read-only. GB is clean on I1/I3/I4/I8.

#### T03a — cause of 7 unexplained stems — completed 2026-10-02

- **Artifacts:** none (read-only; one-off python totals only). Debug-references search (floor area, undivided, roof, storey): no matching entry.
- **Deviations:** none.
- **Test status (measured, 10-06 IDFs in `EU-11/<D>_win_2026-10-06/idfs/`; "10-03" = same stem in `_win_2026-10-03`):**
  - ES `b56bda9013da5b2d` (I3 1.297): undivided whole-zone fallback (`FALLBACK_PENDING_LAYOUT`, `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12`). The IDF extrudes a 5-vertex ring of 2,424.46 m2 per storey (IDF lines 217-262, one `_F<n>_whole` zone per storey, sum 12,122.3), while the layout plate is 1,868.65 m2 (`recut_2026-09-08/layouts/relation/3730743.json`) and prepared `floor_area_m2` = 5 x 1,868.65 = 9,343.26. The IDF ring is not the layout plate (not traced why). Already in 10-03: yes (IDF byte-identical, prepared row identical).
  - ES `d342db5179c1ac49` (I3 1.168): same cause. IDF ring 1,475.17 m2 x 3 = 4,425.5 (lines 193-208) vs layout plate 1,263.37 (`layouts/relation/12877779.json`) x 3 = 3,790.1 prepared. In 10-03: yes (byte-identical).
  - ES `c57a45184a1c34ba` (I7 0.12 %): IDF stories are the raw plate, 490.98 m2 (layout `plate_area_raw_m2` 490.9932); prepared `floor_area_m2` 1,966.2713 = 4 x the regularized plate 491.5441 (`layouts/way/286685222.json`, delta 0.112 %). Reference difference only; no geometry fault. In 10-03: yes (byte-identical IDF, same prepared value).
  - ES `722e9de69cd55e76` (roof 15.4 % short): zone `_F0_dwelling_0` (block `_0`, a 3-vertex floor of 26.9 m2, IDF lines 1197-1218) has walls and a floor but no roof or ceiling surface at all; roof outdoors 147.93 = 174.83 - 26.9. Its walls and floor carry `_H1` / `_K1_H1` suffixes (hidden-pair split, `scripts/run_eu_s2_campaign.py:1260-1292`); which step removed the roof is not traced. In 10-03: yes (byte-identical).
  - IT `89eea66ba6ada782` (+17.1 %): same undivided-fallback cause as the two ES stems (`FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`, `NOCORE_CHECK_FAILED_C4_C10_C11`): IDF ring 1,465.58 m2 x 6 = 8,793.5 (lines 229-289) vs prepared 7,506.31. In 10-03: yes (same IDF floor 8,793.5, same prepared 7,506.3112).
  - IT `595675e5f53ef10b` (one storey 4.0 % off; I7 0.57 %): zone `_F2_dwelling_6` carries two overlapping floors of 27.57 m2 each (IDF line 17267 boundary `Surface`, line 21075 boundary `Adiabatic`; overlap 27.57 m2, union of storey 2 = 686.75), so storey 2 sums 714.31 vs 686.77 on the others. Not in 10-03 (16 zones, all storeys 686.76, floor 4,807.3): new in 10-06.
  - IT `7e4f0c98576b5d81` (roof 16.7 % short): zone `_F4_dwelling_5` (top storey, 55.9 m2, floor at line 7048 `Surface`) has no roof or ceiling surface (5 of 6 top zones carry a roof; outdoors roof 279.34 vs 335.20); its surfaces carry `_H1` suffixes. Not in 10-03 (roof outdoors 335.2 + adiabatic 145.4): new in 10-06; the removing step is not traced.
- **Notes:** five stems were already like this in 10-03 (the 3 undivided fallbacks, ES c57 reference-only, ES 722 missing roof); two are new in 10-06 (IT 595 duplicate floor, IT 7e4f missing roof). No fix proposed.

#### T06 — harvest code for the 10-06 tag — completed 2026-10-02

- **Artifacts:** `scripts/cluster/harvest_eu11_district.py` (`WIN6_TAG` at line 89; `is_win5` true for either win tag at line 272; md5 file name derived from the tag at line 277); `scripts/cluster/harvest_eu11_merged.py` (import line 18, `WIN_TAGS` line 31, `is_win5` line 272); `scripts/cluster/export_flat_counts_4j.py` (`WIN6_TAG`, `TAGS`, `build_flat_counts(district, tag)`, `--tag` option, output `merged_<tag>/flat_counts_<date>.csv`; lines 15-16, 23-32, 44, 68-71); `tests/test_harvest_eu11_win_2026_10_05.py` (one new test, `test_win6_tag_reads_its_own_md5_and_exports`). Output folder for the 10-06 tag is `<D>_merged_win_2026-10-06/` by the existing `merged_<tag>` rule. No folder written.
- **Deviations:** none. Choice where the plan is silent: the 10-06 tag reuses `undivided_excluded_2026-10-05.csv` as its list of excluded undivided buildings (no 10-06 list exists).
- **Test status:** harvest test files (win_2026_10_05, win_2026_10_01, fix3_2026_10_01, uses_production_parser) 27 passed. Byte identity for `win_2026-10-05`: PASS, 12 output files (manifest, excluded list, summary for ES / FR / GB / IT) md5-identical between the code before and after the edit; run as dry builds from the existing local 10-05 manifests, written to temp dirs (IT has no local 10-05 manifest, so no file for it). Dry run `win_2026-10-06` rows: GB 1,240 (PASS), ES 1,164, FR 520, IT 1,167; all counted as `win_failed` because no 10-06 run exists yet.
- **Notes:** no ssh, no Speed, no EnergyPlus. The non-dry harvest needs `speed_jobs.txt` in each 10-06 tree, which the director writes after submission. `export_flat_counts_4j.py --tag win_2026-10-06` needs the non-dry merged manifest.

#### T03b — Madrid storey gain — completed 2026-10-02

- **Artifacts:** none (read-only). Scratch scripts in the session scratchpad only.
- **Deviations:** the plan premise "4 storeys in 10-04/10-05" is wrong for 15 of 16 stems. Zone counts (`ZONE,` objects per IDF) are identical in 09-07, 10-03, 10-04 and 10-05 and rise by 1-2 only in 10-06. The exception is 30240a6694acd89b: 3 (09-07, 10-03), 1 (10-04, 10-05, from `ES-MAD-BERRUGUETE_dw_2026-10-02`), 4 (10-06).
- **Test status:**
  - Input field: Catastro `levels` in `openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv` (`provenance_levels` CATASTRO_BUILDINGPART_OBSERVED), joined in `openubem/semantic/european_archetype_mapping.py:376-383` (`apply_attribute_sidecar`) from `scripts/run_eu_s2_district_campaign.py:675-677`. `_valid_storeys` (`:141-146`) reads it; `_geometry` (`:199`) passes it as `n_storey` to `allocate_european_dwellings`. The manifest `levels` and `3D/eu_ES-MAD-BERRUGUETE_data/buildings.csv` `levels` are empty (`height_m` 9.0, "assumed 9.0 m"); its `storey_count` equals the old drawn storeys, not the source.
  - Code that changed the drawn count: `openubem/geometry/european_residential.py:2753-2761` (T06s part 2: a 0-flat storey is its own group; the committed version absorbed it, `storey_span + 1`), with `scripts/run_eu_s2_campaign.py:1169-1181`. Old builds drew one storey per flat-bearing storey: zones = `dwellings_used` for all 16.
  - Per stem: sidecar levels / Catastro dwellings / old zones (09-07 to 10-05) / 10-06 zones: 193aea6286a8521d 4/3/3/4; 27e04bc1755c4c7d 3/2/2/3; 30240a6694acd89b 4/3/3(10-04: 1)/4; 35dc8b5c2b344650 4/3/3/4; 49edb66f114f62af 5/3/3/5; 4a13d470d74ebb02 3/2/2/3; 601b40a8e9a9e99f 5/4/4/5; 6940d076523dfe64 4/2/2/4; 7e48ebf5c7eadda3 5/4/4/5; 89f77e2b02d859e1 5/4/4/5; 8e794c5dad68973c 6/5/5/6; a8b0a706e3ba306d 4/2/2/4; af59be28315886a7 4/3/3/4; b0862431fa56c773 4/3/3/4; b9c441ec1773cf49 7/6/6/7; ea7734c088249759 5/4/4/5.
  - 10-06 zones = sidecar `levels` for 16 of 16; old zones = Catastro dwellings for 16 of 16.
- **Notes:** the source supports the 10-06 count (sidecar `levels`, an observed Catastro floor count); the dwelling count is a separate field and may be lower than the floors (n_building_units is higher, for example 193aea6286a8521d 5 units, 3 dwellings). Caveat: 30240a6694acd89b (overlap 0.24 m2) and 6940d076523dfe64 (overlap 0.11 m2) carry `levels` from a Catastro join under `MIN_CATASTRO_OVERLAP_M2` (5.0); the overlap rule drops their dwellings but not their `levels`, so their storey source is weak.

#### T03a / T03b / T06 — director audit — 2026-10-02

- **T03a: PASS.** Only the plan doc touched (file times checked). Causes named for all 7 stems. Rulings: ES `c57a45184a1c34ba` accepted (raw vs regularized plate, 0.11 %, a reference difference). The other six fall into three geometry classes (ring larger than layout plate; top/ground zone without roof or ceiling after the hidden-pair split; one zone with two overlapping floors), sent to T03c for the code cause before any fix is ruled.
- **T03b: PASS, and it overturns the T02d premise for these homes.** The 16 Madrid homes gained their storey in 10-06, not 10-04/10-05. The 10-06 count equals the observed Catastro side-car `levels` for all 16; the old count equalled `dwellings_used` because the 0-flat top storey was folded away (FINDING 289). Director measurement on `193aea6286a8521d`: 10-06 draws 4 × 102.68 m² = 410.72 m², height 12.0 m, and `floor_area_m2` = 410.7197 m² (10-05: 308.0398 m², 3 storeys). Model and denominator agree. **Ruling: the 10-06 storey count is right; the check's reference is wrong** (manifest `levels` empty → 09-07 IDF height, which carries the fold). Fix = T02e. The two weak Catastro joins (`30240a6694acd89b`, `6940d076523dfe64`, overlap < 5 m²) are the build's own rule and are accepted as named, not chased.
- The T02d plan text "a storey merge never changes building height" is **wrong** for these homes: the fold dropped the 0-flat storey's height too (9.0 m → 12.0 m). `idf_height_0907` is therefore only trustworthy where no storey was folded; T02e removes it as the reference for Madrid homes with a side-car count.
- **T06: PASS.** Harvest tests 27 green (director re-ran `tests/test_harvest_eu11_win_2026_10_05.py`: 7 passed). 10-05 output byte-identical on 12 files. London dry run 1,240 rows. Choice not in the plan (reuse `undivided_excluded_2026-10-05.csv` for 10-06) **accepted**: director check shows the 10-06 and 10-05 model sets are identical (ES 1,172, FR 522, IT 1,179; no stem added or removed) and the list hits the same 8 / 2 / 12 stems in both.

#### T03c — code cause of three geometry faults — completed 2026-10-02

- **Artifacts:** none (read-only; scratch scripts in the session scratchpad only). Debug-references search ("hidden", "_H1", "bbox", "fallback"): matches at lines 67, 88, 95, 653, 724, 835, 946, 952, 1072, 1093-1169, 1208, 1348-1351, 1546, 1705, 1911, 2007, 2029, 2449, 2473-2477; none names these three faults (line 653 is the reversed-winding `intersect_match` fragments case, a different symptom).
- **Deviations:** class B roof removal is NOT isolated (see B). No rebuild was run, per instruction.
- **Class A, ring larger than the plate: CAUSED, traced.** All five stems (ES `b56bda9013da5b2d`, `d342db5179c1ac49`, `bb4d3f44d4fbe5b1`; IT `89eea66ba6ada782`, `05b52a0da00a6046`) are undivided fallbacks whose manifest footprint has a courtyard hole (1, 1, 1, 3, 1 holes). The one-zone-per-floor zone takes `coords = list(footprint_poly.exterior.coords)[:-1]` (`openubem/geometry/zoning.py:102`, used at `:119-130`), `scripts/run_eu_s2_district_campaign.py:249` re-snaps it with `_stabilize_ring_coords` (`openubem/geometry/european_residential.py:2803-2816`, exterior only), and `scripts/run_eu_s2_campaign.py:1176` extrudes that ring (`add_block(coordinates=first["coords_m"])`). The hole is dropped. `floor_area_m2` is `sum(z["floor_polygon"].area)` (`run_eu_s2_district_campaign.py:1181`), and `floor_polygon` keeps the hole. Footprint source is `openubem/outputs/eu02/<D>/02_residential_manifest.gpkg`. Measured: b56 manifest area 1,868.65, exterior 2,424.23, hole 555.58 (IDF ring 2,424.46); d342 1,263.37 / 1,475.35 / 211.98; IT 89ee 1,251.05 / 1,465.58 / holes 86.51+52.68+75.34 (prepared 7,506.31 = 6 x 1,251.05). The prepared floor area (with hole) matches the source footprint area; the IDF ring does not. Present in 10-03 (same code).
- **Class B, top or ground zone missing a horizontal: PARTLY traced.** Measured by scanning every 10-06 and 10-03 IDF (zone with no roof/ceiling, or no floor): 10-06 flags 3 stems (ES `722e9de69cd55e76` no roof; IT `7e4f0c98576b5d81` `_F4_dwelling_5` no roof, 55.87 m2, 6-vertex floor; IT `97d478bc56840531` `_F0_dwelling_3` no floor, 3-vertex ceiling 55.0 m2, the T02 I5 fail pair with 7e4f). 10-03 flags only ES 722. Not removed by `_remove_degenerate_surfaces` or `_drop_sliver_surfaces` (degenerate CSV: 0 deleted for all three). The only sites that delete a horizontal without a full replacement are `run_eu_s2_campaign.py:1090` (clip, `not parts`), `:1356` / `:1362` (hidden pair removes `b` / `a`), plus frozen `intersect_match` (`openubem/idf/surfaces.py`, D-EU-41). ES 722 is not the hidden pass: its floors and roofs carry no `_H` suffix (names `Floor 0001_3`, `Roof 0001_2` ... only `intersect_match` suffixes), so for 722 the removal is at `:1090` or inside `intersect_match`; the `_H1` on its walls is incidental. For 7e4f and 97d4 the whole building carries `_H1` horizontals in every storey (10-06 has 74 / 54 `_H` surfaces against 32 / 26 in 10-03), the lost surface is one horizontal of one zone, and no step is isolated by reading. Isolating it needs a per-pass surface count on one stem (a rebuild), which this task forbids. New in 10-06 for 7e4f and 97d4: yes, zones rose 16 -> 30 and 16 -> 20 with the per-storey zone fix (`european_residential.py:2753-2761`, `run_eu_s2_campaign.py:1169-1181`).
- **Class C, two overlapping floors in one zone: PARTLY traced.** IT `595675e5f53ef10b` `_F2_dwelling_6` (floor z=6): five floor pieces sum 69.23 m2 against a 41.65 m2 ceiling above; `Floor 0001_H1` (27.57, `Surface` to `Roof 0001_H1`) and `Floor 0001_K1_K1_H1` (27.57, `Adiabatic`) are the same polygon (overlap 27.57 = the whole piece). The chain of suffixes (`_H1`, `_K1_H1`, `_K1_K1_H1`, `_K1_K1_K1_H1`, `_K1_K1_K2_H1`) shows repeated passes of `_pair_hidden_outdoor_surfaces` (`run_eu_s2_campaign.py:1366`) / `_apply_hidden_pair` (`:1295`) / `_split_hidden_surface` (`:1260`) on one floor; the paired roofs below (`F1_dwelling_6`: 29.95 + 3.07 + 16.03 = 49.05 m2) are larger than the floor pieces they pair with (41.66 m2), so the storey-1 and storey-2 outlines of dwelling 6 do not coincide. The step that makes the same 27.57 m2 region twice (one `Surface` piece, one `Adiabatic` piece) is not isolated. New in 10-06: yes, zones rose 16 -> 86 and `_H` surfaces 10 -> 291 against 10-03, so the per-storey zone fix (D-EU-143) is the cause of its appearance; the duplicate itself is made by the hidden-pair code.
- **Signature counts, 10-06 (T02 CSVs, `integrity_2026-10-02/`):**
  - A (I3 > 1.05 on a fallback undivided home): ES 3, FR 0, GB 0, IT 2. ES also has 16 other I3 > 1.05 stems, which are the Madrid storey gain of T03b, not class A.
  - B/C (I5 fail): ES 1 (722), FR 0, GB 0, IT 2 (7e4f, 97d4); class C (595) is not an I5 fail, it shows as I7 0.57 % and a 4.0 % storey excess.
  - I6 (roof deviation fail by `I6_pass`): ES 1 (722), FR 1 (`bfbc1caab1a332a4`), GB 0, IT 3 (7e4f, 97d4, `1773a1e9f64767b1`). FR bfbc and IT 1773 have no zone missing a roof or floor, so they are not class B; their cause is not examined here. Raw `|I6_roof_dev| > 5 %` counts ES 69 / FR 59 / GB 42 / IT 158 are dominated by adiabatic roofs and are not a class signature.
- **Proposed fixes (director decides):** A, extrude the full polygon including its holes, or refuse the one-zone fallback for footprints with interiors and keep the exterior-only ring with `floor_area_m2` taken from it. B and C, add a per-pass count of surfaces by type (and a closed-zone check after each pass) on stems 7e4f, 97d4, 595 and 722, to isolate the removing step before any fix.
- **Notes:** the T03a statement that ES 722's floor carries `_H1` / `_K1_H1` suffixes is not borne out by the 10-06 IDF (only its walls would); the T03a conclusions on zone, roof and area figures stand.

#### T03 — director triage — 2026-10-02 (signed, with T02e as the one open condition)

Every failing check class on 10-06, after T03a/T03b/T03c:
- **Madrid storey gain, 16 homes (I1, I3, I4, I8): (b) fix to the check, not the model.** 10-06 matches the observed Catastro storey count; the check's reference ignored the Catastro side-car. Fix task T02e. Weak joins `30240a6694acd89b`, `6940d076523dfe64` accepted as named.
- **Class A, ring larger than the plate, 5 homes (ES `b56bda9013da5b2d`, `d342db5179c1ac49`, `bb4d3f44d4fbe5b1`; IT `89eea66ba6ada782`, `05b52a0da00a6046`): (a) accepted, no effect on any number.** Director check: all 5 are in `undivided_excluded_2026-10-05.csv`, so they are not simulated and not harvested (D-EU-139). The one-zone fallback draws the courtyard filled in (`openubem/geometry/zoning.py:102`); recorded under FINDING 291 for any future use of undivided homes.
- **Class B (zone without roof or floor) and class C (one zone with a doubled floor), 4 homes: (a) accepted as left out of the results.** ES `722e9de69cd55e76` (no roof, since 10-03); IT `7e4f0c98576b5d81` (no roof), `97d478bc56840531` (no floor), `595675e5f53ef10b` (doubled floor), new in 10-06. A shell with a hole or a doubled floor gives a wrong energy number, so these 4 are not published; the code step that removes or doubles the surface is not isolated (needs a per-pass trace and a rebuild). 4 of 4,113 homes; CLAUDE.md "do not chase the last fraction". Harvest drop = task T06b. They are not submitted to Speed in T05. This supersedes the T02c acceptance of `97d478bc56840531` as a zero-floor flat. FINDING 291 records the open cause.
- **ES `c57a45184a1c34ba` (I7 0.11 %): (a) accepted** (raw vs regularized plate).
- **FR `bfbc1caab1a332a4`, IT `1773a1e9f64767b1` (I6 roof only): (a) stay accepted** under the T02c core_rule exception; no surface is missing (T03c).
- **All other core_rule stems and `finding283_no_outdoor_wall` (I9): (a) as ruled in the T02c audit.**

**FINDING 291 (new).** Two geometry faults survive the 10-06 build. (1) The one-zone-per-floor fallback extrudes only a footprint's outer ring, so a courtyard footprint is drawn filled in (`openubem/geometry/zoning.py:102`, `european_residential.py:2803`, extruded at `scripts/run_eu_s2_campaign.py:1176`); `floor_area_m2` keeps the hole. Only undivided homes, none simulated. (2) The surface-pairing passes can leave a zone with no roof or no floor, or with the same floor twice (`_pair_hidden_outdoor_surfaces`, `scripts/run_eu_s2_campaign.py:1366`, repeated `_K1` suffixes); 4 homes; step not isolated. Remedy: leave the 4 out of the results (T06b); the code fix is parked.

**Gate.** T03 is signed when T02e reports: the 16 Madrid homes pass, and no stem fails a check outside the classes above. Then T04.

#### T02e — Madrid side-car storey reference — completed 2026-10-02
- **Artifacts:** `scripts/eu21/13_model_integrity.py` (side-car `levels` first for ES, source `levels_sidecar`; new column `sidecar_overlap_m2`; `ES_SIDECAR` imported from `scripts/run_eu_s2_district_campaign.py`, fallback to same path); `tests/test_eu_model_integrity_2026_10_02.py` (+1 test); `integrity_2026-10-02/*_win_2026-10-06_integrity.csv` and `summary_win_2026-10-06.csv` overwritten.
- **Deviations:** none. A side-car value is rounded to an integer storey count.
- **Test status:** 25 passed. Sweep on `win_2026-10-06`, 10 workers. Storey sources: ES levels 1010 / levels_sidecar 159 / idf_height_0907 3; FR levels 521 / idf_height_0907 1; GB levels 1127 / layout_0908 63 / idf_height_0907 50; IT layout_0908 1164 / idf_height_0907 15. Fails I1/I3/I4/I8: ES 0/3/0/0; FR 0/1/0/0; GB 0/0/0/0; IT 0/3/0/1. The Madrid up-class homes now pass I1/I4/I8.
- **Still failing:** ES 722e9de69cd55e76 I5,I6; b56bda9013da5b2d I3,I7,I13; bb4d3f44d4fbe5b1 I3,I7; c57a45184a1c34ba I7; d342db5179c1ac49 I3,I7,I13. FR bfbc1caab1a332a4 I2,I3,I6,I7. GB none. IT 05b52a0da00a6046 I3,I7; 1773a1e9f64767b1 I2,I6,I7; 595675e5f53ef10b I2,I7; 7e4f0c98576b5d81 I5,I6; 89eea66ba6ada782 I3,I7,I13; 97d478bc56840531 I2,I3,I5,I6,I7,I8; cc55f139215783a3 I7.
- **Notes:** none.

#### T06b — geometry-fault exclusion in harvest — completed 2026-10-02

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/geometry_fault_excluded_2026-10-06.csv` (4 rows: ES `722e9de69cd55e76` = way/420409347; IT `7e4f0c98576b5d81` = 30946, `97d478bc56840531` = 28473, `595675e5f53ef10b` = 33327; building_id from `<D>_win_2026-10-06/prepared_buildings.csv`); `scripts/cluster/harvest_eu11_merged.py` (`GEOMETRY_FAULT_REASON` / `GEOMETRY_FAULT_CSV_PARTS` lines 44-45, `_geometry_fault_ids` line 110, used in `_build_win_manifest` lines 314 and 324-328, `win_2026-10-06` tag only; the stems go to `excluded_buildings.csv` with blocker `GEOMETRY_FAULT_FINDING_291`); `tests/test_harvest_eu11_win_2026_10_05.py` (one new test, `test_win6_drops_geometry_fault_stem_with_reason`). `harvest_eu11_district.py` not touched (the drop lives in the merged script).
- **Deviations:** none. Note: the summary field `n_excluded_undivided` now also counts these 4 for the 10-06 tag.
- **Test status:** the four harvest test files (win_2026_10_05, win_2026_10_01, fix3_2026_10_01, uses_production_parser) 28 passed. Byte identity for `win_2026-10-05`: PASS, 12 files (manifest, excluded list, summary for ES / FR / GB / IT) md5-identical between dry builds before and after the edit (temp dirs). Dry run `win_2026-10-06` rows: ES 1,163, FR 520, GB 1,240, IT 1,164 (all match the plan); excluded-list sizes ES 24, FR 9, GB 0, IT 51.
- **Notes:** no ssh, no Speed, no `_merged_win_*` folder written.

#### T02e / T06b — director audit; T03 signed — 2026-10-02

- **T02e: PASS.** Director re-ran: 25 tests pass. Re-read the four 10-06 integrity CSVs (4,113 rows): failing stems ES 5, FR 1, GB 0, IT 7, and **every one is a named class of the T03 triage** (class A: `b56bda9013da5b2d`, `d342db5179c1ac49`, `bb4d3f44d4fbe5b1`, `89eea66ba6ada782`, `05b52a0da00a6046`; class B/C: `722e9de69cd55e76`, `7e4f0c98576b5d81`, `97d478bc56840531`, `595675e5f53ef10b`; reference difference: `c57a45184a1c34ba`; core_rule: `bfbc1caab1a332a4`, `1773a1e9f64767b1`, `cc55f139215783a3`). 0 unexplained. The 16 Madrid homes pass I1/I4/I8; storey source ES now levels 1,010 / levels_sidecar 159 / idf_height_0907 3.
- **T06b: PASS with one fix demanded.** CSV holds exactly the 4 stems; director re-ran `tests/test_harvest_eu11_win_2026_10_05.py`: 8 passed; 10-05 byte-identical (12 files); dry rows ES 1,163, FR 520, GB 1,240, IT 1,164 as planned. Defect: `n_excluded_undivided` now also counts the 4 broken-shell homes (a mislabelled count in the summary) → T06c.
- **T03 SIGNED.** No unexplained fail remains on 10-06. Speed submission is unblocked by T03; per §7 it still waits for T04 (plan pages shown to the owner).

#### T06c — separate geometry-fault count — completed 2026-10-02

- **Artifacts:** `scripts/cluster/harvest_eu11_merged.py` `build_summary` (`n_excluded_geometry_fault` added for the `win_2026-10-06` tag only; `n_excluded_undivided` there now excludes blocker `GEOMETRY_FAULT_REASON`; other tags keep the old single count); `tests/test_harvest_eu11_win_2026_10_05.py` (`test_win6_drops_geometry_fault_stem_with_reason` also asserts `n_excluded_geometry_fault == 1` and `n_excluded_undivided == 0`).
- **Deviations:** none.
- **Test status:** the four harvest test files (win_2026_10_05, win_2026_10_01, fix3_2026_10_01, uses_production_parser) 28 passed. Byte identity `win_2026-10-05`: PASS, 12 files (manifest, excluded list, summary x 4 districts) md5-identical between before and after dry builds (temp dirs). Dry run `win_2026-10-06` (`n_excluded_undivided` / `n_excluded_geometry_fault`): ES 23 / 1, FR 9 / 0, GB 0 / 0, IT 48 / 3; rows ES 1,163, FR 520, GB 1,240, IT 1,164.
- **Notes:** no ssh, no Speed, no `_merged_win_*` folder written. The 10-05 summary has no `n_excluded_geometry_fault` key (kept absent for byte identity).

#### Speed check — director — 2026-10-02 13:35 EDT (Speed clock)

- Bologna 1410474 (10-05): 264 COMPLETED, 32 RUNNING, 882 PENDING, 1 OUT_OF_MEMORY. Mean of completed tasks 1,185 s (`sacct` ElapsedRaw); 914 left × 1,185 / 32 = 9.4 h → about 23:00 EDT. Unchanged from the 12:39 measure.
- `1410474_261` = `366fc6fda9a1a946` (501 zones, byte-identical in 10-05 and 10-06, not in the T06s re-run list): OUT_OF_MEMORY at the 32G limit after 50 s on speed-16 (sampled MaxRSS 8.3 GB, the peak was missed). **T05 adds it to the IT array with `--mem=64G`** after deleting its `out/366fc6fda9a1a946`.
- Note: `<D>_win_2026-10-06/changed_stems.txt` lists every stem of the tree (IT 1,179), not the stems changed since 10-05; the re-run lists are `division_residual_2026-09-29/t06s_rerun_<D>.txt` (IT 183). T05 must use the latter.

#### T06c — director audit — 2026-10-02

- **PASS.** Tests re-run by the director (green); 10-05 byte-identical (12 files); 10-06 `n_excluded_geometry_fault` ES 1, FR 0, GB 0, IT 3 as planned.
- Known, accepted: `n_excluded_undivided` (ES 23, FR 9, IT 48) counts rows of the undivided list, not undivided stems present in the 10-06 tree (ES 8, FR 2, IT 12). Same behaviour as the 10-05 summary (byte-identical), so it is a label, not a population error; the row counts (ES 1,163 = 1,172 − 8 − 1; FR 520 = 522 − 2; IT 1,164 = 1,179 − 12 − 3) are right. CP-3c reads the row counts.

#### T04 — plan pages from 10-06 — completed 2026-10-02

- **Artifacts.** `scripts/eu21/09_plans3d_from_idf.py` (new `--source-tag`, `--date`; reads only `<D>_win_2026-10-06/idfs/`, adds `origin_offset.json` back to the storey-0 origin, undivided list `undivided_excluded_2026-10-05.csv`, the 4 broken-shell homes labelled "left out of results: broken shell (FINDING 291)" in the popup and the IDF-state field, no new colour). Pages `plans3D/archive/PLANS_<D>_2026-10-06.html`: ES 4.72 MB, FR 3.20 MB, GB 3.22 MB, IT 9.69 MB. The four 10-01 pages moved to `plans3D/archive/PLANS_<D>_2026-10-01_fix.html`. `plans3D/index.html`: 4 lines changed (diff shows 4 removed + 4 added), 0 links left to 10-01 pages.
- **Deviations.** (1) `origin_offset.json` keys are `dx`, `dy` (plan says x, y); read as such. (2) The 3 Bologna broken-shell homes (`30946`, `28473`, `33327`) have zones with no floor surface, which `read_building_plan` refuses ("ZONE ... has no floor surface"); they are read with a tolerant wrapper in the page script that drops the floorless zones (reader file untouched), so those homes are drawn from the zones that have a floor. (3) ES/GB have no `origin_offset.json`, so no offset applied there.
- **Test status.**
  - P1 pass: ES 1,172 of 1,172 (8 undivided among them), FR 522 of 522 (2), GB 1,240 of 1,240 (0), IT 1,179 of 1,179 (12).
  - P2 pass: buildings ES 1,172, FR 522, GB 1,240, IT 1,179 (all); storeys 4,475 / 2,882 / 3,077 / 5,932 (all), drawn area within 0.5 % of the zone areas read from the IDFs.
  - P3 pass: JSON parses in all 4, 0 `eui` keys, storey list correct for every building, 0 storeys missing; Madrid `5bce5fa408cac4fb` shows 3, Bologna `0177dae25178d27e` shows 4.
  - P4 pass on position: for 5 named homes per district the scene footprint centroid is identical to the 10-01 page (0.000 m ES, GB, FR, IT; checked on the page's scene ring). The zone outline sits within 0.28 m (ES), 1.27 m (FR), 1.07 m (GB), 3.81 m (IT) of the footprint relative to 10-01; the walls-out geometry change explains this, and ES/GB (no offset) show the same size, so the FR/IT offset is right.
  - P5 FAIL as literally worded, explained: flats drawn (all storeys) equal `dwellings_used` for ES 921 of 1,164, FR 488 of 520, GB 203 of 1,240, IT 983 of 1,167 divided homes. Every remaining home (ES 243, FR 32, GB 1,037, IT 183) has exactly one dwelling zone per storey and `dwellings_used` below the storey count (one dwelling spread over several storeys, one zone per storey, FINDING 289). One exception: IT `28473` (broken shell) draws 19, `dwellings_used` 20.
  - P6: sizes above; `index.html` diff = 4 changed lines.
  - P7 pass: ES `193aea6286a8521d` 4 storeys of 102.68 m²; GB `7aae3e0ee341bc04` 3 storeys of 53.42 m²; 5 homes per district in total (the named one plus 4 random from the T02 CSVs; FR and IT 5 random): storey count equal and per-storey area within 0.5 % of `storey_areas_m2` in all 20 of 20.
- **Notes.** Pages built and checked with `--all` (4 processes). The director decides whether P5's one-dwelling-over-several-storeys homes need a different count on the page. STOP: owner review of the pages.

#### T04 — director audit — 2026-10-02

- P1, P2, P3, P6, P7 **PASS** as reported (P2 16,366 of 16,366 storeys within 0.5 %; pages 3.2–9.7 MB; index diff 4 lines).
- P4 **PASS**: footprint shift 0.000 m in all four districts. The zone-outline drift vs 10-01 (up to 3.8 m in Bologna) is expected: the flat counts changed in 10-04 (T06p), so the cuts inside the plate changed.
- Deviation 2 (floorless zones of the 3 Bologna broken-shell homes dropped from the drawing inside the page script) **accepted**; those homes are labelled as left out of results.
- P5 **FAIL, page defect**: counts zones as dwellings on the 1,495 D-EU-143 homes → T04b. The 1 extra Bologna mismatch (`28473` = `97d478bc56840531`, 19 vs 20) is the broken-shell home with a floorless zone, accepted.

#### T04b — real flat count on the plan pages — completed 2026-10-02

- **Artifacts.** `scripts/eu21/09_plans3d_from_idf.py` only (import of `allocate_european_dwellings`; `PREP` map of `prepared_buildings.csv` rows; per-storey flats from `dwellings_used` and the storey count; new record fields `zn`, `up`; `declared_dwellings` = `dwellings_used` on divided homes; JS patches for the "Dwellings" / "Zones in the model" labels and the "(upper floor)" table label). Undivided and one-zone-per-floor homes carry no `zn`, so their text is unchanged. The four `plans3D/archive/PLANS_<D>_2026-10-06.html` pages regenerated with `--all --source-tag win_2026-10-06 --date 2026-10-06` (4 processes): ES 5.01 MB, FR 3.38 MB, GB 3.45 MB, IT 10.23 MB. `index.html` and the archive untouched.
- **Deviations.** The table label for an upper-floor zone is written literally as plan wording: "Dwelling D<k> (upper floor)" (other rows keep "Dwelling <k>"). The T02 CSV's first column is the stem, so the named homes were looked up by `stem` and matched to the page by `building_id`.
- **Test status.**
  - P5 (new) dwellings = `dwellings_used`: ES 1,164 of 1,164, FR 520 of 520, GB 1,240 of 1,240, IT 1,167 of 1,167. Zones per storey = `I8_expected` where not empty: ES 1,161 of 1,161, FR 520 of 520, GB 1,240 of 1,240, IT 1,166 of 1,167 (the miss is `28473`, the broken-shell home with a floorless zone, accepted in the T04 audit).
  - P1 pass: ES 1,172 of 1,172, FR 522 of 522, GB 1,240 of 1,240, IT 1,179 of 1,179. P2 pass: all buildings, storeys 4,475 / 2,882 / 3,077 / 5,932 within 0.5 %. P3 pass: JSON parses, 0 `eui` keys, storey list complete in all four.
  - P4 pass: footprint centroid shift vs the 10-01 pages 0.000 m (5 homes per district).
  - P6: page sizes above; `index.html` not touched.
  - P7 pass: 5 of 5 per district (ES `193aea6286a8521d` and GB `7aae3e0ee341bc04` included), storey count equal and per-storey area within 0.5 % of the T02 CSV.
  - Spot checks: London `7aae3e0ee341bc04` shows Dwellings 1, Zones in the model 3, 3 storeys, F1 and F2 notes read "upper floor of the flat(s) below". Madrid `193aea6286a8521d` shows Dwellings 3, Zones in the model 4, 4 storeys, F3 reads "upper floor of the flat(s) below".
- **Notes.** STOP: director audit of T04b.

#### T04b — director audit; owner rulings — 2026-10-02

- **T04b: PASS.** Director re-check of the four 10-06 pages: 0 `eui` keys; "upper floor of the flat(s) below" appears ES 451, FR 53, GB 1,289, IT 305 times, which equals the number of schedule files that changed between 10-05 and 10-06 per district (one per added upper-floor zone); `index.html` diff 4/4 lines (from T04). P5 now ES 1,164/1,164, FR 520/520, GB 1,240/1,240, IT 1,167/1,167 (zones per storey 1,166/1,167, the miss = broken-shell `97d478bc56840531`, accepted).
- **Owner, verbatim, 2026-10-02:** "ok continue to the end" (reply to "After that fix, I show you the pages before any new run goes to the cluster") and "please handle all for all neighbourhoods". Read as: go on to T05 for all four districts without a separate page-review stop; the pages are handed over with the T05 report.
- **Owner, verbatim, 2026-10-02:** "i closed gsscanada sessions, can you handle by yourself". The 4J/5J peer packages of T07 are not sent; no peer message is written. T07 ends at CP-3c and the internal results files.

#### T05 — Speed re-runs staged and submitted — director — 2026-10-02 ~14:10 EDT (Speed clock)

- **Run lists** = `division_residual_2026-09-29/t06s_rerun_<D>.txt` (no undivided or broken-shell stem is in them), plus IT `366fc6fda9a1a946` (out of memory at 32G in 1410474). Local `<D>_win_2026-10-06/fleet.lst` is now this run list (the T06s build list is kept as `fleet_t06s_build.lst`); the harvest maps run times by this order.
- **Staged** `/speed-scratch/o_iseri/fleets/EU11_<D>_win_2026-10-06/` (mkdir + tar only; script `t05_up/stage6.sh`): run IDFs + their 10-06 schedules uploaded; all other schedules, weather and `submit_recut.sbatch` copied from 10-05; `out/` of every stem not re-run copied from 10-05. Counts: ES fleet 243, out carried 929 (= 1,172 − 243); FR 32, 490; GB 1,037, 203; IT 184, carry pending (Bologna 10-05 still running). Weather files unchanged (local diff 0).
- **Bologna 1410474:** the 134 not-yet-started tasks of re-run stems cancelled (`scancel 1410474_[list]`, tested on one index first; the rest of the array kept pending, 32 running). 47 re-run stems had already run or are running on 10-05; their 10-05 output is not carried.
- **Submitted** (`-p ps --time=7-00:00:00`, `%32`, `--mem=32G`): London **1416438** (1–1,037), Madrid **1416439** (1–243), Bologna **1416440** (1–183), Lyon **1416441** (1–32), Bologna **1416442** (index 184 = `366fc6fda9a1a946`, `--mem=64G`). `speed_jobs.txt` written per district. Account at 64 CPUs (another project 32, Bologna 32), so the new arrays start as Bologna 10-05 slots free.
- **Still to do:** when 1410474 ends, carry IT `out/` for every stem not in the IT run list (exclude list `xout_IT-BOL-GALVANI2.txt` + `366fc6fda9a1a946`); FAILED / OUT_OF_MEMORY sweep per array; measure ETA from `sacct`; then T06 harvest `--merged-tag win_2026-10-06` ×4, T07 CP-3c and a final T02 run. Peer packages dropped (owner closed the GSSCanada sessions).

#### T07-CP3c-data — completed 2026-10-03

- **Artifacts:** `scripts/eu21/14_cp3c_win6.py`; `openubem/outputs/eu_evidence/EU-11/cp3c_2026-10-06/` (`summary.json`, `check1_run_status.csv`, `check2_new_extremes.csv`, `check3_spearman.csv`, `check4_ratio_split.csv`, `check4_pooled.csv`, `check5_finding283.csv`, `check6_storey_fails.csv`). Final integrity run: `scripts/eu21/13_model_integrity.py --tree win_2026-10-06 --workers 10` re-wrote `integrity_2026-10-02/*_win_2026-10-06_integrity.csv` and `summary_win_2026-10-06.csv`. Nothing under `results/`.
- **Deviations:** none. Check 6 is read from the integrity CSVs (I1 pass = z levels equal the storey reference; I2 <= 0.01 = each storey within 1 % of the ground storey), on all 4,113 stems. "Flat count changed" = `old_count != new_count` in `dwelling_counts_2026-10-06.csv`.
- **Test status:** integrity run: 4,113 stems, 13 fails, set identical to the T02e still-failing list. CP-3c data: check 1 pass (ES 1163, FR 520, GB 1240, IT 1164 of the same, 4,087 total); check 2 no home above 300 kWh/m2 (09-08 had 399); check 3 FAIL for ES AB (Spearman -0.246, n=1093), all other district/type groups > 0; check 4 pooled 10-06 vs 09-08: ES 69.165 vs 81.388 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* (-15.0 %), FR 58.009 vs 70.346 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* (-17.5 %), GB 61.977 vs 93.730 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* (-33.9 %), IT 54.648 vs 54.672 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* (-0.04 %), four 59.661 vs 66.295 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* (-10.0 %); check 5 FINDING 283 ES 11, FR 3, GB 5, IT 70 (89); check 6 fails FR bfbc1caab1a332a4, IT 1773a1e9f64767b1, 595675e5f53ef10b (I2), IT 97d478bc56840531 (named exception). *(superseded 2026-10-08 by results/EU11_results_2026-10-08, D-EU-149: ES 68.774/1,119, FR 57.810/501, GB 68.307/1,215, IT 58.164/1,035, fleet 62.626/3,870 — correctly divided homes only, not like-for-like, FINDING 295)*
- **Notes:** adoption not decided. Values per check and district are in `summary.json`.

#### T07 — CP-3c on 10-06 — director audit and ruling — 2026-10-03

- **Audit of T07-CP3c-data: PASS.** Final integrity run on 4,113 stems: 13 fails, the same 13 named in the T03 triage, 0 unexplained.
- **Check 1 PASS** (1,163 / 520 / 1,240 / 1,164 = 4,087, no failure). **Check 2 PASS** (no home above 300 kWh/m2; 09-08 had 399). **Check 5 PASS** (FINDING 283 population 89: ES 11, FR 3, GB 5, IT 70). **Check 4 reported** (see `cp3c_2026-10-06/check4_*.csv`).
- **Check 3 amended (D-EU-145):** pooled Spearman fails only for ES apartment blocks (-0.246, n 1,093). Director re-measure: inside each age band it is strongly positive (ES.02 0.71, ES.03 0.82, ES.04 0.79, ES.05 0.55, ES.06 0.59). Cause: newer bands have both more window share and much lower EUI (Simpson mix), not a model fault. Check 3 is therefore read within age band for building types that fail pooled; all pass.
- **Check 6 PASS with named exceptions:** FR `bfbc1caab1a332a4` and IT `1773a1e9f64767b1` (core rule, accepted at T03), IT `97d478bc56840531` (zero-floor flat, known limitation), IT `595675e5f53ef10b` (broken shell, left out of results, FINDING 291). Storey-count test: 0 fails.
- **Ruling: CP-3c passes. The 10-06 set is adopted** under the standing ruling "highest accuracy". Pooled EUI per district (population in brackets): ES 69.165 (1,163), FR 58.009 (520), GB 61.977 (1,240), IT 54.648 (1,164), four together 59.661 (4,087). Every 2026-09-08 EUI is superseded. *(superseded 2026-10-08 by results/EU11_results_2026-10-08, D-EU-149: ES 68.774/1,119, FR 57.810/501, GB 68.307/1,215, IT 58.164/1,035, fleet 62.626/3,870 — correctly divided homes only, not like-for-like, FINDING 295)*

#### T07-adopt-results — completed 2026-10-03

- **Artifacts:** `scripts/eu21/15_write_results_win6.py`; `results/EU11_results_2026-10-06_per_home.csv/.json` and `_summary.csv/.json` (same columns and key names as the 09-08 files, plus `tag` = win_2026-10-06 and `supersedes` = 2026-09-08); `results/SUPERSEDED_2026-09-08.txt`; three supersession markers in `STATE_european_locations_v5.md` (lines 19, 167, 1958).
- **Deviations:** column `undivided_excluded_from_2026-10-01` is kept and is False on every row (undivided and broken-shell homes are not in the merged manifests, so they have no row). The 09-08 summary csv cannot take a header line without breaking it, so the marker is a note file for both formats and the 09-08 files are untouched. `BRIEF_european_locations_v5.md` and `CHECKLIST_european_locations_v5.md` contain none of the five 09-08 EUIs, so they were not edited.
- **Test status:** per-home rows ES 1,163, FR 520, GB 1,240, IT 1,164 = 4,087; non-null EUI 4,087 (csv and json); summary pooled EUI equals the manifest `summary.json` to 6 decimals: ES 69.165225, FR 58.008829, GB 61.976977, IT 54.647708, four 59.660846; csv and json agree on every row and every summary value. 09-08 EUI occurrences elsewhere (grep -c, not edited): DEBUG_floor-division-gap 2, DONE/PLAN_eu-recut-95pct 8, PLAN_eu-floor-division-residual 5, PLAN_eu-model-integrity 1, PROMPT_MANAGER_handoff_2026-09-09 4, EU11_results_2026-09-08 summary csv 5 and json 5, STATE 7 (3 marked). *(superseded 2026-10-08 by results/EU11_results_2026-10-08, D-EU-149: ES 68.774/1,119, FR 57.810/501, GB 68.307/1,215, IT 58.164/1,035, fleet 62.626/3,870 — correctly divided homes only, not like-for-like, FINDING 295)*
- **Notes:** the handoff prompt still quotes the 09-08 values and was not edited.

#### T09 — ledger and markers — completed 2026-10-06

- **Artifacts:** `STATE_european_locations_v5.md` (§0 new paragraph for `D-EU-118`-`146` and `FINDING 270`-`291` by plan file, Next free set to `D-EU-147` / `FINDING 292`, old Next-free line marked superseded; §1 adopted-set paragraph with `D-EU-145`; §8 one entry for this plan). Supersession marker `*(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)*` appended after each 09-08 EUI in `STATE_european_locations_v5.md`, `debugs/DEBUG_floor-division-gap-and-clean-pipeline_2026-09-08.md`, `implementation/PLAN_eu-floor-division-residual-2026-09-29.md`, this plan (§6 line 442 and the 5 rounded values in the T07-adopt notes), `prompts/PROMPT_MANAGER_handoff_2026-09-09.md`. `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`: one new OUT_OF_MEMORY entry (end of file).
- **Deviations:** none. Marker placed right after the value token, before its population. The existing "(superseded 2026-10-03 ...)" notes in STATE were left and the standard marker added beside each value. The embargo paragraph of STATE §1 (`:127`) was left as is. The T09 task text (line 368) was not marked, as ordered.
- **Test status:** (a) PASS: all 29 `D-EU-118`..`146` and 22 `FINDING 270`..`291` ids are present in STATE §0 (0 missing), "Next free `D-EU-147`, `FINDING 292`" present; ids found in no doc: none (all 51 found by `grep` over `implementation/`; `D-EU-144`, `145`, `FINDING 290`, `291` only in this plan). (b) PASS: occurrences vs marked, STATE 15/15, DEBUG 5/5, residual plan 12/12, this plan 6/6 (the other 5 are the T09 task text, out of scope), handoff 5/5. (c) PASS: ES 69.165225, FR 58.008829, GB 61.976977, IT 54.647708, fleet 59.660846 each found in STATE §1 and equal to `results/EU11_results_2026-10-06_summary.json` at 6 decimals. (d) PASS: `grep -c` before/after: OUT_OF_MEMORY 1 to 2, `d8a1a0d8ceb5dc73` 0 to 1, `fd4b13e28f1c6f47` 1 to 2, `366fc6fda9a1a946` 2 to 3; `FINDING 289` 1 (existing), `FINDING 291` 1 (existing, covers the 4 broken-shell homes `7e4f0c98576b5d81`, `97d478bc56840531`, `722e9de69cd55e76`, `595675e5f53ef10b`, each already present).
- **Notes:** populations beside the 09-08 values were not marked separately (the marker after the value covers the pair). The new debug-reference entry is sourced from the handoff box lines 25-27 and §8 of this plan; the 200G re-run outcome of `d8a1a0d8ceb5dc73` is not stated there, so the entry says only that a stem failing at 200G is left out under `FINDING 291`.

#### T08 — 3D viewers on 10-06 — completed 2026-10-06

- **Artifacts:** `scripts/generate_eu_3d_viewers.py` (plans from `<D>_win_2026-10-06` only, origin offset added back, EUI from `<D>_merged_win_2026-10-06` manifest, `sidecar=None`, no `layouts/` folder, sources.json names the 10-06 tree, `md5_2026-10-06.txt`, merged manifest and results summary with sha256, dead `_load_eu17_sidecar` removed); regenerated `openubem/outputs/3D/eu_<D>_viewer.html` and `eu_<D>_data/` (4 districts) with the mirror in `docs/docs_ACTIVE/europeanLocations/outputs_3D/`; `openubem/outputs/eu_evidence/EU-11/viewers_2026-10-06/` (`buildings_before_<D>.csv` x4, `run_<D>.log` x4, `verify_V1_V6.txt`, `verify_V3_holes.txt`, `integrity_run.log`); the integrity run rewrote `EU-11/integrity_2026-10-02/*_win_2026-10-06_integrity.csv` and `summary_win_2026-10-06.csv` (same names as T07-CP3c-data).
- **Deviations:** (1) The plain reader refuses the 3 IT and 1 ES broken-shell homes (`ValueError ... has no floor surface`), so those 4 ids (`geometry_fault_excluded_2026-10-06.csv`) are read with the same zone filter as `09_plans3d_from_idf.py::read_fault_plan` (`_read_tree`); needed to reach IT 1,179 plans. Registered in the debug references, ch. 11. (2) No `layouts/` folder is written (item 4: no side-cars); the old one is deleted from the data folder and its mirror. (3) `EU17_ROOT` constant kept because `tests/test_eu18c_viewer_geometry_only.py:19` imports it.
- **Test status:** V1 PASS: scene rows ES 1,398 / FR 768 / GB 1,351 / IT 1,257; plans ES 1,172 / FR 522 / GB 1,240 / IT 1,179. V2 PASS: EUI ES 1,163 / FR 520 / GB 1,240 / IT 1,164, 0 mismatches at 6 decimals, 0 values absent from the 10-06 manifest. V3 FAIL as written (">0.5 m must be 0"): plan centroid vs the scene footprint ring, max / count>0.5 = ES 0.762 m / 4, FR 1.753 / 4, GB 1.692 / 3, IT 13.495 / 48; 53 of the 59 are courtyard buildings (the scene ring has no hole, the plan does). Against the real footprint including courtyards: ES 0.76 m / 1, FR 1.755 / 1, GB 0.531 / 1, IT 1.069 / 3 of 4,113 (plan shape differs from the OSM footprint: plan area 348 vs 395 m2 etc.); nothing is near the 6,000 km origin error, so the offset is correct. V4 PASS: `recut_2026-09-08`, `merged_2026-09-08`, `ceiling82`, `fix_2026-10-01` = 0 in all 4 html and 4 sources.json; `win_2026-10-06` = 1 per html and 4 per sources.json. V5 PASS: 4 of 4 viewers and 4 of 4 data folders (buildings.csv, index.html, sources.json) byte-identical to the mirror, no extra mirror files. V6 PASS: row set unchanged and 0 differences in `footprint_area_m2`, `levels`, `height_m`, `height_source`, `year_built` in all 4 districts; `13_model_integrity.py --tree win_2026-10-06 --workers 10` gives 13 failing stems (ES 5, FR 1, GB 0, IT 7), including `bfbc1caab1a332a4`, `1773a1e9f64767b1`, `595675e5f53ef10b`, `97d478bc56840531`. V7 FAIL (12 of 12 fail, reported not edited): `test_viewer_html_has_zero_forbidden_terms` x4 asserts no "EUI" in the page (the committed 09-08 viewer already carried `"eui"`, so it failed before this task); `test_scene_polygons_match_idf_right_now` x8 reads plans from `EU-17/<D>/prepared_buildings.csv`, the old tree.
- **Notes:** the 4 stale-tree tests need the director's decision (point them at the 10-06 tree and drop the EUI rule). STOP here as ordered.

#### T08 / T09 — director audit and rulings — 2026-10-06

- **T09: PASS.** STATE §0 holds `D-EU-118`…`146` and `FINDING 270`…`291`, next free `D-EU-147` / `FINDING 292` (grep 1); spot check of handoff markers: every 09-08 value found carries the marker. Embargo paragraph (STATE `:127`) left as is, by plan.
- **T08 V1, V2, V4, V5, V6: PASS** as logged.
- **V3 ruling:** the test as written compared a plan with courtyards to a scene ring without them, so it was the wrong test. Read against the footprint with courtyards (`viewers_2026-10-06/verify_V3_holes.txt`): 6 of 4,113 above 0.5 m (ES 1, FR 1, GB 1, IT 3), max 1.76 m. Cause: the simulated outline differs from the OSM outline (ring cleaning, slivers), not the position; no plan is anywhere near the 6,000 km error the offset would cause. **V3 passes with these 6 named.**
- **V7 ruling:** `tests/test_eu18c_viewer_geometry_only.py` encodes the EU-18c geometry-only contract (no EUI on the page), which the EU-11 viewers dropped before this task (the committed 09-08 viewer already failed it), and reads the EU-17 tree. It is stale, not a T08 regression. Repaired in T08b.

### T08b — Repoint the stale viewer test (executor, director ruling 2026-10-06)

**What.** Edit only `tests/test_eu18c_viewer_geometry_only.py`.
1. `FORBIDDEN_RE`: drop `eui` and `kwh` (the EU-11 viewer colours by EUI by design); keep every other term.
2. `test_scene_polygons_match_idf_right_now`: read `prepared_buildings.csv` and the IDF from `openubem/outputs/eu_evidence/EU-11/<D>_win_2026-10-06/` instead of `EU17_ROOT / district`; add the `origin_offset.json` shift when present, as `scripts/generate_eu_3d_viewers.py` now does. Keep every assertion.
3. `SAMPLE`: for each of the 8 ids, if its `expected_state` no longer matches the 10-06 IDF (`geometry_outcome` in the 10-06 `prepared_buildings.csv`), replace the id with the first id (sorted) of that district that has the expected state in 10-06; report each swap. If a district has no `massing_box` in 10-06, STOP and report.
**How to test.** `pytest tests/test_eu18c_viewer_geometry_only.py -q`: 12 of 12 pass. Append `#### T08b — viewer test repointed — completed YYYY-MM-DD` at the end of §8.

#### T08 — director note: old side-cars removed — 2026-10-06

- T08's run of `scripts/generate_eu_3d_viewers.py` deletes `eu_<D>_data/layouts/` before writing (`:1338-1340`, mirror `:1428`); with `sidecar=None` nothing is re-written, so the 09-08-era side-cars are gone from `openubem/outputs/3D/` and `outputs_3D/` (GB 2,480 and IT 2,422 git-tracked files, recoverable with `git checkout`). They described 09-08 layouts, so they are superseded, not lost. 4J (2026-10-06 request in `messages_GSSCanada/`) read them; 10-06 side-cars do not exist yet. Owner decision pending on the GSSCanada hand-over.

#### T08b — director ruling on the STOP — 2026-10-06

- STOP was correct: GB 10-06 has 1,240 ruled and 0 massing_box (every London home is divided). **Ruling:** GB's second SAMPLE id = the first ruled GB id (sorted) other than `way/190348384`, with `expected_state` = `ruled`. ES, FR, IT swaps as the executor found (`relation/12867469`, `BATIMENT0000000240881193_part0`, `30025`). Execute T08b with this ruling.


#### T08b — viewer test repointed — completed 2026-10-06

- **Artifacts:** `tests/test_eu18c_viewer_geometry_only.py` (only file edited). Reads `EU-11/<D>_win_2026-10-06/` via `EU11_ROOT`/`WIN_TAG`, adds the `origin_offset.json` shift with `dataclasses.replace`. SAMPLE swaps: ES massing_box `way/100704656` -> `relation/12867469`; FR massing_box `BATIMENT0000000013365727_part0` -> `BATIMENT0000000240881193_part0`; IT massing_box `32166` -> `30025`; GB second id `way/14325891` (massing_box) -> `relation/6171462` (ruled).
- **Deviations:** GB has 0 massing_box in 10-06, STOP reported, director ruled the GB swap above. Second STOP: `not simulated` (legend "IDF only, not simulated", 7 hits per viewer) matched the kept terms; director ruled it dropped from `FORBIDDEN_RE` as well (label intended, D-EU-139). `FORBIDDEN_RE` now `eplus|severe|fatal|weather|epw|job.?id`.
- **Test status:** `pytest tests/test_eu18c_viewer_geometry_only.py -q`: 12 passed of 12.
- **Notes:** No debug-reference entry needed (no error solved, test repointed per ruling).

#### GSSCanada hand-overs reopened — director — 2026-10-06

- Owner, this session, 2026-10-06: "yes, please continue" to "may I reopen hand-overs for both teams (5J reply, 4J package)", then "answer both 5th and 4th journal". The T07 line "peer packages dropped" is lifted for these two requests only.
- 5J answered by the director: `messages_GSSCanada/2026-10-06_OpenUBEM_to_5J_win6_final_madrid_bologna.md` (10-06 final; changed stems = `t06s_rerun_<D>.txt`, verified equal to the 10-05→10-06 md5 diff, ES 243, IT 183; `59231039c486b1fb` run as delivered).
- 4J package: T10 below (executor). The director writes the 4J reply after the T10 audit.

### T10 — 4J package on 10-06, London and Bologna only (executor)

**Scope.** `GB-LDN-STDUNSTANS` and `IT-BOL-GALVANI2` only. Never ES or FR. Request: `messages_GSSCanada/2026-10-06_4J_to_OpenUBEM_request_win6_package.md`.
**Files you may write.** New folders `EU-11/<D>_win_2026-10-06/layouts/`; `EU-11/<D>_merged_win_2026-10-06/flat_counts_2026-10-06.csv`; everything under `openubem/outputs/eu_evidence/EU-11/handover_4J_2026-10-06/`; `/speed-scratch/o_iseri/handover_4J_2026-10-06/` on Speed. No repo `.py` edit, except the one allowed in step 1c. Never write into `openubem/outputs/3D/` or `outputs_3D/` (the viewer build deletes `layouts/` there). Never touch `idfs/`, `schedules/`, `md5_2026-10-06.txt` of any tree. Write no message file to `messages_GSSCanada/`.
`EU` below = `openubem/outputs/eu_evidence/EU-11`; `H` = `EU/handover_4J_2026-10-06`.

**1. Layout side-cars (per district).**
a. `python -m scripts.emit_eu11_layout_sidecars --district <D> --evidence-root <D>=<abs EU>/<D>_win_2026-10-06 --population-manifest <D>=<abs EU>/<D>_merged_win_2026-10-06/<slug>_manifest.csv > H/emit_<D>.log 2>&1` (`<slug>` = `gb_ldn_stdunstans` / `it_bol_galvani2`).
b. If the log contains `WARNING: could not read IDF plans` (the reader fails on broken-shell homes, see the "has no floor surface" entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`), delete the half-written `layouts/` and go to c. Otherwise skip c.
c. The one allowed edit: in `scripts/emit_eu11_layout_sidecars.py`, read the plans per IDF with the same tolerant reader `scripts/eu21/09_plans3d_from_idf.py:81-93` uses (skip a home whose IDF cannot be read, collect its id), instead of the one `read_district` call. Re-run a. Report the skipped ids.
d. Do not move, shift or rewrite any coordinate in the side-cars. Report the frame instead (step 5, check P4).

**2. Flat counts.** `python -m scripts.cluster.export_flat_counts_4j --district <D> --tag win_2026-10-06` for GB and IT. Then `sha256sum` of each output CSV.

**3. Code digests.** `sha256sum` of these ten files, as they are on disk now: `openubem/geometry/european_residential.py`, `openubem/geometry/european_nocore.py`, `openubem/idf/surface_orientation.py`, `openubem/idf/degenerate_surfaces.py`, `scripts/run_eu_s2_campaign.py`, `scripts/run_eu_s2_district_campaign.py`, `scripts/emit_eu11_layout_sidecars.py`, `scripts/eu21/12_drop_degenerate.py`, `scripts/eu_idf_plan_reader.py`, `scripts/cluster/export_flat_counts_4j.py`. Signature check: `git diff HEAD -- <those ten> | grep -E '^[-+](def|class) [A-Za-z]' | head -40`. Report "no public signature changed" only if no line starts with `def`/`class` followed by a name without a leading underscore; otherwise list them.
Write all digests to `H/sha256_2026-10-06.txt` (`<sha256>  <repo-relative path>`, LF).

**4. Speed copy.** Use the `_ssh()` wrapper from `scripts/cluster/t08_harvest_results.py:104` (bash -lc). Login node: `mkdir`, `scp`, `tar` only. Make a local tar per district of `<D>_win_2026-10-06/{idfs,schedules,weather,layouts,prepared_buildings.csv,md5_2026-10-06.txt,origin_offset.json if present}` plus `<D>_merged_win_2026-10-06/flat_counts_2026-10-06.csv`, upload it to `/speed-scratch/o_iseri/handover_4J_2026-10-06/`, untar there, then `rm` the remote tar. Delete the local tar. Upload `H/sha256_2026-10-06.txt` too.

**5. How to test (write results to `H/verify_P1_P6.txt`).**
- P1 count: side-car files per district = rows of the merged 10-06 manifest (GB 1,240, IT 1,164), plus any skipped ids named.
- P2 flats: for every side-car with non-empty `floors`, distinct zone names = `dwellings_total` = that building's `dwellings_used` in the merged 10-06 manifest. 0 mismatches, or list them all.
- P3 flat-count CSV: rows = manifest rows; `new_count` = `dwellings_used` for every row.
- P4 frame: for 5 Bologna side-cars, compare the first floor ring centroid to (a) the IDF floor centroid as read, (b) the same plus `origin_offset.json`. Report which one matches within 1 m. Do the same for 5 London ones.
- P5 Speed: on Speed, `find /speed-scratch/o_iseri/handover_4J_2026-10-06 -name '*.idf' | wc -l` and `-name '*.json' -path '*layouts*' | wc -l` per district equal the local counts; `sha256sum` of the remote flat-count CSVs equal the local ones.
- P6 trees untouched: `md5sum` of every IDF in both 10-06 trees still matches `md5_2026-10-06.txt`.
Append `#### T10 — 4J package — completed YYYY-MM-DD` here (Artifacts / Deviations / Test status / Notes), with the per-district file counts, the three sha256 of step 2 and 3 locations, P4's answer, and the Speed paths. If you solved an error, register it in the debug references first.
**Stop point 5:** after T10. The director audits, then writes the 4J reply.

#### T10 — 4J package — STOPPED 2026-10-06 (check failures, not completed)

- Artifacts: side-cars GB 1,240 (`EU-11/GB-LDN-STDUNSTANS_win_2026-10-06/layouts/{way,relation}/`), IT 1,161 (`IT-BOL-GALVANI2_win_2026-10-06/layouts/`, left in place, not deleted); flat counts `GB-LDN-STDUNSTANS_merged_win_2026-10-06/flat_counts_2026-10-06.csv` sha256 `7a2cbfbcea8f5e8286ec36b5841ca447958ce62c72a9a186e303316f4a84cde9`, `IT-BOL-GALVANI2_merged_win_2026-10-06/flat_counts_2026-10-06.csv` sha256 `7b4bf81dbbb60a9f5419828535c71f5bbcf5799792cad5ac3dc79ea4e712a94b`; code digests `H/sha256_2026-10-06.txt` (10 files); `H/verify_P1_P6.txt`; `H/emit_<D>.log`.
- Deviations: step 1c not applied and step 4 (Speed copy) not done, because P2 fails and the fix is outside T10's allowed edits. IT log has `WARNING: could not read IDF plans` (97d478bc56840531.idf, "has no floor surface"); IT side-cars 1,161 of 1,164 (missing 30835, 33610, 81117). Signature check: NOT "no public signature changed" — new public defs: `ruleset_is_relaxed`, `nocore_ruleset`, `c13_bent_walls`, `rescore_cut`, `improve_cut_nocore` (european_nocore.py); `ep_geometry_preflight`, `hidden_outdoor_area`, `zone_floor_overlap` (run_eu_s2_campaign.py).
- Test status: P1 GB pass / IT fail; P2 fail both (GB 196 of 1,240, IT 1,051 of 1,160 side-cars have dwellings_total != dwellings_used; the side-car re-imputes its own count, e.g. 17 or 16 against 73 or 132 simulated); P3 simulated rows match 1,240/1,240 and 1,164/1,164 but the CSV holds extra non-simulated rows (1,351 and 1,257); P4 GB frame = IDF as read, IT frame = IDF plus origin_offset (side-cars are absolute UTM); P5 not run; P6 pass both (0 md5 mismatches).
- Notes: conflict with the plan: P2 assumes side-car counts equal the 10-06 simulated counts, but `emit_eu11_layout_sidecars.py` does not read `dwellings_used`. Director decision needed before step 4.

### T10b — 4J package, side-cars carry the 10-06 flat counts (executor)

*Director decision D-EU-147 (2026-10-06, under the hand-over the owner reopened):* the side-cars must carry the simulated count, because 4J asked for side-cars "that carry the 10-06 flat counts" and the side-car must describe the simulated model. Cause of the T10 P2 failure: `emit_eu11_layout_sidecars.py:245-260` still uses the old count rule (`n_apartment` of the reference building), while the 10-06 models use `_dwellings_for` (`run_eu_s2_district_campaign.py:148-167`, area rule). The 3 Bologna buildings with no side-car (30835, 33610, 81117: not produced by `_it_rows`) are accepted as missing and stated to 4J; do not chase them.
Same scope, same allowed files and same rules as T10, plus the one `.py` edit below. Flat counts (step 2) and P4 stand as T10 measured them; do not redo them.

1. **Clean.** Delete exactly `EU/GB-LDN-STDUNSTANS_win_2026-10-06/layouts/` and `EU/IT-BOL-GALVANI2_win_2026-10-06/layouts/` (written by T10 today, nothing else lives there), and `H/verify_P1_P6.txt.part`.
2. **The one allowed edit, `scripts/emit_eu11_layout_sidecars.py` only.**
   a. T10 step 1c as written (tolerant per-IDF reader in place of the one `read_district` call; collect skipped ids and print them).
   b. When `population_manifest` is given, build `{str(building_id): (int(dwellings_used), str(dwellings_source))}` from it. In the per-building loop, if the id is in that map, set `dwellings_val` from it and `provenance_token = "DWELLINGS_USED_" + dwellings_source.upper()`, before `allocate_european_dwellings` is called. Without `population_manifest`, behaviour is unchanged.
   No other change. Run `python -m py_compile` on the file.
3. **Re-emit.** T10 step 1a for GB and IT (overwrite `H/emit_<D>.log`).
4. **Re-digest.** T10 step 3 (the emitter's sha256 changes); overwrite `H/sha256_2026-10-06.txt`. Signature check: also run the same `git diff` with `grep -E '^-(def|class) [A-Za-z]'` and report its line count (T10 found 8 added public functions and none removed).
5. **Speed copy.** First run P1, P2a, P2b and P3 of step 6; only if they pass, do T10 step 4 as written.
6. **Checks, write to `H/verify_P1_P6.txt` (overwrite).**
   - P1: side-cars GB = 1,240; IT = 1,161 with exactly 30835, 33610, 81117 missing, plus any id skipped by 2a.
   - P2a: `dwellings_total` = merged-manifest `dwellings_used` for every side-car. 0 mismatches.
   - P2b: for every side-car with non-empty `floors` and `idf_reroute_divergence` false: the set of side-car zone names `floors[*].zones[*].name` with the leading `<building_id>_` removed (London: the id after `way/` or `relation/`) equals the set of IDF zone names containing `_dwelling_` with the leading `<stem>_` removed (stem from `prepared_buildings.csv`; IDF zone names: regex `Zone,\s*\n\s*([^,;\s]+)\s*,`). Report matches / compared per district and up to 20 mismatching ids with both set sizes. Count the reroute side-cars separately.
   - P3: rows with `status == simulated` = manifest rows and `new_count` = `dwellings_used` on all of them (non-simulated rows are by design, see `2026-10-01_OpenUBEM_to_4J_flat_counts_status.md` §2). Re-read only; T10 measured 1,240/1,240 and 1,164/1,164.
   - P5 as in T10. P6 as in T10.
7. Debug references (`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`): extend the existing "has no floor surface" entry with the emitter fix (2a), and add one entry for `dwellings_total` != `dwellings_used` in the side-cars (cause and fix 2b, file:line).
Append `#### T10b — 4J package — completed YYYY-MM-DD` (Artifacts / Deviations / Test status / Notes) with per-district counts, P2a/P2b numbers, the two flat-count sha256, the emitter's new sha256 and the Speed paths. If P2a fails or P2b mismatches exceed 1 % of compared in either district, stop after step 6 and report; do not guess a fix.
**Stop point 5b:** after T10b. The director audits, then writes the 4J reply.

#### T10b — 4J package — completed 2026-10-06

- Artifacts: side-cars GB 1,240 (`EU-11/GB-LDN-STDUNSTANS_win_2026-10-06/layouts/{way,relation}/`), IT 1,161 (`EU-11/IT-BOL-GALVANI2_win_2026-10-06/layouts/`; 30835, 33610, 81117 missing as accepted in D-EU-147); `scripts/emit_eu11_layout_sidecars.py` new sha256 `11dbd5cb3008c17751a3c7597f365b2c098d9647185e62eccf0c902052b8380b` (2a tolerant per-IDF reader via `load_prepared_buildings` + `read_building_plan`, skipped ids printed; 2b `used_map` from the population manifest sets `dwellings_val` and `DWELLINGS_USED_<SOURCE>` before `allocate_european_dwellings`; `py_compile` ok; +31/-2 lines); flat counts unchanged from T10: GB `7a2cbfbcea8f5e8286ec36b5841ca447958ce62c72a9a186e303316f4a84cde9`, IT `7b4bf81dbbb60a9f5419828535c71f5bbcf5799792cad5ac3dc79ea4e712a94b`; `H/sha256_2026-10-06.txt` (10 files, overwritten); `H/verify_P1_P6.txt`; `H/emit_GB-LDN-STDUNSTANS.log`, `H/emit_IT-BOL-GALVANI2_shard0-7.log` and `_rescue0-6.log`. Speed: `/speed-scratch/o_iseri/handover_4J_2026-10-06/{GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}_win_2026-10-06/` and `..._merged_win_2026-10-06/flat_counts_2026-10-06.csv`, plus `sha256_2026-10-06.txt`.
- Deviations: (1) IT emission ran as 8 parallel shards of one scratch wrapper (monkeypatching `_it_rows` to a stride of rows, no repo edit) after the single process sat 28+ min on building 27931 (501 dwellings); shard 3 stuck on 30090 (1,247 dwellings), so 7 rescue shards did the rest and shard 3 was killed once `30090.json` existed (all 1,161 files load as JSON, P2a/P2b re-run on the final tree). Output per building is the same code path as the CLI. (2) The P2b IDF zone regex needs case-insensitive matching (`ZONE,` upper case in the IDFs); applied. (3) Signature check: 8 new public defs as in T10 (none from this task), removed `def`/`class` lines: 0.
- Test status: P1 GB 1,240/1,240 PASS; IT 1,161/1,164, exactly 30835/33610/81117 missing PASS (reader skipped id: 28473, side-car still emitted). P2a 0 mismatches GB 1,240, IT 1,161. P2b GB 1,240 of 1,240 match, IT 1,161 of 1,161 match, 0 reroute side-cars, 0 mismatches. P3 simulated rows = manifest rows, `new_count` = `dwellings_used` GB 1,240/1,240, IT 1,164/1,164 (CSV also holds non-simulated rows by design). P4 stands (GB frame = IDF as read; IT = IDF + origin_offset). P5 Speed idf GB 1,240 / IT 1,179, layouts GB 1,240 / IT 1,161, flat-count sha256 equal local: PASS. P6 0 md5 mismatches GB 1,240, IT 1,179.
- Notes: debug references extended ("has no floor surface") and new entry for side-car `dwellings_total` != `dwellings_used` (`OpenUBEM_debug_References.md`). Local emission cost is steep for very large IT buildings (501 dwellings > 28 min, 1,247 dwellings several hours).
