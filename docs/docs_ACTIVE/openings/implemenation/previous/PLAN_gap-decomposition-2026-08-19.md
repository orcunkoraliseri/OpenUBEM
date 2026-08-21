# PLAN — where the 25 % cross-mode gap actually comes from, and the OPEN-59 bounds screen

**Slug:** `gap-decomposition` · **Date:** 2026-08-19 (night, later) · **Author:** director (manager session)
**Predecessor:** `PLAN_layout-assign-untrimmed-2026-08-19.md` — T01–T04 executed, CP-1 signed.
**DESIGN pointer:** none new. Nothing is built and nothing is designed. Both tasks read artifacts
that already exist on disk.

**Why this plan exists.** CP-1 established a systematic **≈−25 %** `layout_assign`-vs-`auto` energy
difference on a 48-building sample that **survives** the OPEN-10 floor-area confounder
(`extra/MEASUREMENT_open-03-18_untrimmed-sample.md` §4). Nothing in this arc explains it. OPEN-03
claims *roughly half* of it comes from internal loads modelled at 2022 code regardless of the
building's real vintage — **a claim this arc has never tested**, because until CP-1 no
`layout_assign` build could be parsed at all. It can now, and **the 48 `.sql` files are still on
disk**, each carrying a full end-use breakdown. Splitting that −25 % by end use decides between
"internal loads" and "something else" without rebuilding anything.

Second, the **OPEN-59 local diagnostic has been owed since 2026-08-19 morning and is still not
dispatched.** It is cheap, local, needs no cluster, and touches nothing task A touches.

🔴 **Time-sensitivity, task A only.** `scratchpad/open03-untrimmed-sample/` is ~0.94 GB of
`.sql` files. Nothing protects it. **Do task A first.** If the tree is gone, say so and stop —
do not rebuild it.

---

## 2. Hard rules for the executor

1. **Measurement only.** Do not edit any file under `openubem/`, `tests/`, or `scripts/validation/`.
   New code goes in **two** new scripts under `scripts/analysis/`, one per task. If a task's premise
   is false at HEAD, **STOP and report** — do not adapt the task.
2. **No cluster.** Everything is local. No `ssh`, no `sbatch`, no login node.
3. **No git write command, ever.**
4. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, or the open-items register.
5. **Open, close, strike or retire nothing.** Recommendations only, filed in `extra/`.
6. **Rebuild nothing and re-simulate nothing.** Both tasks are reads of existing artifacts. If you
   find yourself about to call `run_step3` or `run_energyplus`, you have misread the plan.
7. **Sample discipline.** Task A is **n=48** and every sentence carrying one of its numbers must say
   so. The adopted fleet figure — **153.8231 kWh/m² pooled** (total simulated energy ÷ total
   simulated floor area) over **8,153** buildings / **24,320,582 m²** — is untouched by this plan.
8. **Report failures; never substitute a weaker number.** A `.sql` that will not open is a result.
9. **Cap your own output.** `head`, `--stat`, `grep -c`. Report the conclusion and the `file:line`,
   never file contents.
10. **Deviation is a finding.** If a number does not reproduce, say so and explain it.
11. 🔴 **Never end your turn waiting.** Three executors in a row have stalled by making their last
    act "wait for a run to finish", and a waiting agent is never woken. **Every command you run must
    finish inside its own tool call.** Nothing here runs longer than a couple of minutes. Your final
    act is always a **write** — progress log, then report. If you are blocked, **report the blockage
    and stop**; do not wait for it to clear.

## 3. File layout

- Task A script: `scripts/analysis/open03_enduse_decomposition_2026-08-19.py`
- Task B script: `scripts/analysis/open59_pde_bounds_screen_2026-08-19.py`
- Tables: `openubem/outputs/comparisons/open03_enduse_by_building.csv`,
  `openubem/outputs/comparisons/open59_pde_bounds_screen.csv`
- Report: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_gap-decomposition_2026-08-19.md`
- Progress log: §7 of **this** document, one entry per task.

## 4. Dependency decisions (pinned — do not re-decide)

- **Task A inputs, `layout_assign` side:** the 48 `.sql` files at
  `scratchpad/open03-untrimmed-sample/<cell>/sim/<safe_id>/eplusout.sql`. Their `osm_id`, cell and
  per-building totals are already joined in
  `openubem/outputs/comparisons/open03_untrimmed_sample_join.csv` — **use that file as the row list**
  rather than re-walking the tree, so the two tables are guaranteed to describe the same 48.
- **End-use extraction:** EnergyPlus writes the end-use table into the `.sql`
  `TabularDataWithStrings` table. Read it with `sqlite3` directly. Take `ReportName = "AnnualBuildingUtilityPerformanceSummary"`,
  `TableName = "End Uses"`, and keep the rows for **Heating, Cooling, Interior Lighting, Interior
  Equipment, Water Systems, Fans, Pumps**.
  🔴 **The production parser already does exactly this query — reuse it, do not re-implement it.**
  `openubem/results/parser.py:631-633` (`FROM TabularDataWithStrings … TableName = 'End Uses'`),
  inside the ABUPS cross-check documented at `:609` and `:619`. **Verified present at HEAD by the
  director 2026-08-19.** Read that function, call it if it is callable, and if it is private or
  wrongly shaped for this use, copy its SQL verbatim into your script and cite the line. A second,
  hand-written version of this query that disagrees with the production one is exactly the
  "reconstruction, not provenance" failure this project has already recorded once (R07).
  **Verified by the director 2026-08-19: all 48 `eplusout.sql` files are still on disk.**
- **Units.** The end-use table is in **GJ** by default. Convert to kWh with `× 277.7778` and state
  the conversion in the report. Cross-check: the end-use total must reconcile with that building's
  `total_eui_kwh_m2 × floor_area_m2` from the join CSV to within **2 %**. **Report the reconciliation
  before reporting any decomposition** — if it fails, the extraction is wrong and the decomposition
  is meaningless.
- **Task A `auto` side.** ⚠️ **There is no matching end-use breakdown for `auto` on disk** — run 4
  harvested `05_results.csv`, not per-building `.sql`. **Do not invent one and do not rebuild.**
  Task A therefore decomposes the `layout_assign` side only, and answers the question by *shape*:
  which end uses dominate, and whether lighting+equipment are large enough for a vintage effect to
  account for half of a 25 % gap. **Say plainly in the report that this is a one-sided decomposition.**
- **The vintage ratios to test against** are already measured, n=12 archetypes: lighting **1.722**,
  equipment **1.064**, occupancy **1.000** (`extra/MEASUREMENT_open-03_vintage-at-head.md` §5).
- **Task B inputs:** the 290 `OpenUBEMUnknown` buildings and the donor table, exactly as
  OPEN-55 §3 did for equipment alone. Read that section first and **copy its screen structurally**;
  it is proven. Cite the `file:line` you copied from.

## 5. Facts this plan relies on, with citations

- The −25 % that survives the confounder: `extra/MEASUREMENT_open-03-18_untrimmed-sample.md` §4
  (21 area-agreeing buildings, −28.02 % pooled excluding the dominant Courthouse, −26.05 % median).
- 48/48 parsed `success`, so all 48 `.sql` files are well-formed: same report, §2.
- The gap is not uniform by archetype — MidriseApartment −12.6 %, MediumOffice −34.9 %: same
  report, §7. **This is the strongest existing hint about mechanism and Task A should test it.**
- OPEN-03's attribution claim and its ~29 % origin: register, `### OPEN-03` section.
- OPEN-59 was opened 2026-08-19 because unidentified buildings still use **1.7×** the energy of
  identified ones after the equipment fix, with lighting **6.7×** and cooling **5.6×**.

## 6. Task list

### T01 — Decompose the 48 by end use

**What.** For each of the 48, extract the annual end-use breakdown from its `.sql`, write
`openubem/outputs/comparisons/open03_enduse_by_building.csv` (one row per building, one column per
end use in kWh, plus `cell`, `osm_id`, `archetype_id`, `floor_area_m2`, `gap_pct` carried over from
the join CSV).

**Why.** It is the only route to *mechanism* that needs no rebuild, and the artifacts expire.

**How.** §4's pinned extraction. **Reconcile totals first**, then decompose.

**How to test.** Report (i) how many of the 48 reconcile within 2 % and the worst offender's error,
(ii) the sample-wide end-use split as a percentage of total energy, (iii) the same split for the
MidriseApartment rows (n=9, smallest gap) against the office rows (SmallOffice+MediumOffice+LargeOffice,
n=31, largest gap). **State n on every line.** If lighting+equipment together are too small a share to
move a 25 % total by half, **say so — that would contradict OPEN-03's attribution**, and a
contradiction is the most valuable result this task can produce. Do not soften it.

### T02 — The OPEN-59 bounds screen that has been owed all day

**What.** For the 290 `OpenUBEMUnknown` buildings, compare the drawn PDE value in **each** column
against that column's donor-table bounds — not equipment alone. Write
`openubem/outputs/comparisons/open59_pde_bounds_screen.csv` with one row per column: column name,
donor min/max, drawn min/max/median, count out of bounds, worst excursion.

**Why.** It decides between the two live hypotheses — a sibling of the OPEN-55 widened-bounds defect
(in which case the same fix applies and it is quick) versus those buildings genuinely being
higher-intensity (a calibration question, not a bug). **Nothing else can tell them apart, and it is
cheap.**

**How to test.** Report the count of columns with any out-of-bounds draw, and name them. **If every
column is in bounds, that is a clean and decisive answer favouring the calibration hypothesis — report
it as such and do not go looking for a defect anyway.**

## 7. Stop-and-report points

- **CP-1 — after T02.** One checkpoint. Append two progress-log entries under §8, write the report,
  report back. **Do not open, close or strike anything; recommendations only.**

## 8. Progress log

*(executor appends one entry per completed task here:*
`#### TXX — <title> — completed YYYY-MM-DD` *+ Artifacts / Deviations / Test status / Notes)*

#### T01 — Decompose the 48 by end use — completed 2026-08-19

**Artifacts.** `scripts/analysis/open03_enduse_decomposition_2026-08-19.py`;
`openubem/outputs/comparisons/open03_enduse_by_building.csv` (48 rows, `extract_status=ok` for all
48); write-up in `extra/MEASUREMENT_gap-decomposition_2026-08-19.md` SS1.

**Deviations.** The plan's 2 % reconciliation gate **fails**: only 6/48 (12.5 %) reconcile within
2 % (median error 4.71 %, worst 192.28 % at `la_centre/way/427817563`). Diagnosed, not an extraction
bug: `total_eui_kwh_m2` sources lighting/equipment from hourly zone variables that are **not**
zone-multiplier-scaled, while its own `floor_area_m2` and the ABUPS `Total End Uses` table (used
here) **are** multiplier-scaled — so `total_eui_kwh_m2` undercounts lighting+equipment by exactly the
zone multiplier for the 42/48 buildings that use one (`num_zones < levels`). Confirmed
component-by-component (cooling/heating/fans/pumps/DHW match ABUPS to <0.01 %, only lighting and
equipment diverge, by exactly the Zone Multiplier, 4.00x on the worst case). Confirmed the existing
`check_building_integrity()` gate (`openubem/results/parser.py:602-646`) already flags this file
`abups_ok=False`; the T01 sampling pipeline that built the join CSV never calls it. **Per plan rule
1/§4, the decomposition was therefore not compared against `total_eui_kwh_m2`/`gap_pct` — that
comparison is reported as failed, not used.** The ABUPS end-use split itself is self-consistent
(reads one table directly) and is reported descriptively in SS1.2 of the write-up, independent of
the failed cross-check.

**Test status.** Extraction: 48/48 (0 failures, 0 sql errors). Reconciliation: 6/48 pass at the
plan's 2 % threshold (fails the plan's premise check; documented, not silently substituted).

**Notes.** Sample-wide end-use split (n=48, ABUPS-derived): Interior Equipment 32.45 %, Fans
21.17 %, Cooling 15.63 %, Interior Lighting 13.86 %, Heating 9.09 %, Water Systems 7.08 %, Pumps
0.73 %; Lighting+Equipment = 46.31 %. MidriseApartment (n=9) vs Office (n=31): Lighting+Equipment
41.21 % vs 57.30 %. Using the n=12 vintage ratios (lighting 1.722x, equipment 1.064x), the maximum
possible total-energy reduction from full vintage-correction of lighting+equipment is 7.76 % (all
48), 6.13 % (Office, the highest-gap group) — well short of "half" a 25-35 % gap (12.5-17.5 points
needed). **This contradicts OPEN-03's "roughly half" attribution as stated**, on this sample's own
end-use mix, independent of the reconciliation failure (the bound uses only the internally-valid
ABUPS shares).

#### T02 — The OPEN-59 bounds screen that has been owed all day — completed 2026-08-19

**Artifacts.** `scripts/analysis/open59_pde_bounds_screen_2026-08-19.py`;
`openubem/outputs/comparisons/open59_pde_bounds_screen.csv` (4 rows, one per PDE column); write-up
in `extra/MEASUREMENT_gap-decomposition_2026-08-19.md` SS2.

**Deviations.** None. Regenerated draws for the 290 `OpenUBEMUnknown` buildings in `nyc_suburban`
(osm_ids from the OPEN-55 acceptance-test run's `03_idf_manifest.parquet`, `open48_refleet3_t02a4`)
using the production functions directly (`_build_unknown_loads`, `_per_building_rng`,
`_get_cross_archetype_loads`); cross-checked bit-identical against
`extra/MEASUREMENT_open-55_acceptance-test-attempt4.md` SS3 for the three columns it already
reported (equipment, occupancy, lighting), confirming correctness before adding `wwr`.

**Test status.** All 4 PDE columns (`lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person`,
`wwr`): **0/290 out of bounds**, in every column. The donor screen (`_UNKNOWN_DONOR_EXCLUDE` +
`Warehouse` for occupancy) already applies uniformly to all four columns at HEAD, not equipment
alone.

**Notes.** This refutes OPEN-59's hypothesis 1 (a per-column sibling of the OPEN-55 widened-bounds
defect) at HEAD — no column draws from an unscreened pool. Per plan instruction, reported as a clean,
decisive result favouring hypothesis 2 (the post-screen donor pool is genuinely higher-intensity than
the buildings it stands in for — a calibration question). No further defect hunt performed.
