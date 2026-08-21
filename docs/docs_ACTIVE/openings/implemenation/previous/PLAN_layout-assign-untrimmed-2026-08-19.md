# PLAN — untrimmed `layout_assign` sample: the measurement that three tasks asked for

**Slug:** `layout-assign-untrimmed` · **Date:** 2026-08-19 (late) · **Author:** director (manager session)
**Predecessor:** `PLAN_twenty-items-2026-08-19.md` — all 20 tasks executed, CP-1/CP-2/CP-3 signed.
**DESIGN pointer:** none new. This plan builds nothing and designs nothing; it runs the single
artifact that T15, T18 and T20(a) each independently named as the thing that would settle their
question, and that none of them was authorised to run.

**Why this plan exists.** Every `layout_assign` build in this arc used `trim_outputs=True`, which
skips the per-zone `Output:Variable` block (`openubem/idf/builder.py:516,638` →
`write_outputs(trim_hourly=...)`). The production parser's integrity gate
(`openubem/results/parser.py:203`, `layout_assign` branch at `:221-236`, called at `:772-774`)
requires at least one zone-level key and returns `failed_zone_mismatch` without it. **This is a
measurement-capability defect, not a defect in any published figure** — OPEN-32 already bounds the
effect on adopted results at zero. T18 proved the cure on n=1: the same building parses to
`success`, `total_eui_kwh_m2 = 68.28`, with `trim_outputs=False` as the only variable changed
(`scripts/analysis/open03_t18_trim_hypothesis_check_2026-08-19.py`; recorded in
`extra/MEASUREMENT_open-03_vintage-at-head.md` §3). This plan scales that n=1 to a stratified
sample so OPEN-03 and OPEN-18 can be quantified for the first time at HEAD.

---

## 2. Hard rules for the executor

1. **Measurement only.** Do not edit any file under `openubem/`, `tests/`, or `scripts/validation/`.
   New code goes in **one** new script under `scripts/analysis/`. If a task's premise is false at
   HEAD, **STOP and report** — do not adapt the task.
2. **No cluster.** Everything here is local. No `ssh`, no `sbatch`, no login node.
3. **No git write command, ever.** Git is handled outside this session.
4. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, or the open-items register.
5. **Open, close, strike or retire nothing.** Recommendations only, filed in `extra/`.
6. **One isolated working directory per building.** OPEN-58 records a real defect where a shared
   working directory let EnergyPlus runs overwrite each other's results. Every simulation gets its
   own `run_dir`; never reuse one; never `chdir` into a shared tree.
7. **This is a sample, and must be labelled a sample in every sentence that carries a number.**
   Do **not** compute, restate, or imply a fleet EUI from it. The adopted fleet figure —
   **153.8231 kWh/m² pooled** (total simulated energy ÷ total simulated floor area) over **8,153**
   buildings / **24,320,582 m²** — is untouched by this plan and must not appear as anything other
   than context.
8. **Report failures; never substitute a weaker number.** A building that fails to build, simulate
   or parse is a result: record it with its error text. Do not silently drop it.
9. **Cap your own output.** Use `head`, `--stat`, `grep -c`. Do not paste whole files, whole logs or
   whole diffs into your report. Report the conclusion and the `file:line`, not the contents.
10. **Deviation is a finding.** If a number does not reproduce, say so and explain it with a
    timestamp or an upstream cause. Do not smooth it over.

## 3. File layout

- New script: `scripts/analysis/open03_untrimmed_layout_assign_sample_2026-08-19.py` (**one** file).
- Working tree: `scratchpad/open03-untrimmed-sample/` (gitignored; per-building `sim/<safe_id>/`).
- Tables: `openubem/outputs/comparisons/open03_untrimmed_sample_eui.csv` and
  `openubem/outputs/comparisons/open03_untrimmed_sample_join.csv`.
- Report: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03-18_untrimmed-sample.md`.
- Progress log: §8 of **this** document, one entry per task.

## 4. Dependency decisions (pinned — do not re-decide)

- **Fixtures:** `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4/<cell>/01_buildings.gpkg`.
  Run 4 and nothing else — it is the generation the adopted figure comes from, so the join is
  generation-clean. Verified present for all 12 cells at plan time.
- **`auto`-mode comparison side:** `.../open48_refleet4/<cell>/results/05_results.csv`, joined on
  `osm_id`. Do not use the `t17`–`t20_layout_assign_eui.csv` harvests: OPEN-28/OPEN-08 and this
  arc's own T15 all establish archetype-label drift across generations in them.
- **Cell coordinates:** `CELL_CONFIGS` at `scripts/validation/v12_cell_pipeline.py:45` (`lat`/`lon`
  per cell). Read them; do not hard-code your own.
- **Build/simulate/parse recipe:** copy the working sequence in
  `scripts/analysis/open03_t18_trim_hypothesis_check_2026-08-19.py:36-88` verbatim in structure
  (`classify` → `assign_climate_zones` → `enrich_semantics` → `run_step3(..., trim_outputs=False)`
  → `SimTask`/`run_energyplus`/`classify_outcome` → `parse_building`). It is proven to work; changing
  it re-opens a question already answered.
- **Sample:** **4 buildings per cell × 12 cells = 48.** Per cell, sort the run-4 successful
  buildings by `footprint_area_m2` and take the rows at the **10th, 35th, 65th and 90th percentile
  positions** (integer index, deterministic, no RNG). This spans the size range in every cell and
  guarantees small buildings in the cold cells that OPEN-18 needs.
- **Parallelism:** `n_jobs=4` for the build step; simulations may run up to 4 concurrent **only**
  because each has its own `run_dir` (rule 6). If that isolation cannot be guaranteed, run
  sequentially — correctness beats wall-clock here.

## 5. Facts this plan relies on, with citations

- `trim_outputs` default is `False` and threads to `write_outputs(trim_hourly=...)`:
  `openubem/idf/builder.py:219,227,516,638,701,706,720`.
- The gate that fails without zone variables: `openubem/results/parser.py:203`, `layout_assign`
  branch `:221-236`, called `:772-774`; the comment at `:85` states it "still looks for Ideal Loads
  variables to parse zones".
- The cure, proven at n=1: `extra/MEASUREMENT_open-03_vintage-at-head.md` §3–§4 — same building,
  `layout_assign` **68.28** vs `auto` **81.87** kWh/m², **−16.6 %**, with a 326 vs 1,055 m²
  denominator mismatch flagged as a confounder (`match_storeys()` = `fallback_not_expressible`).
- The static vintage ratios the gap is being tested against: lighting **1.722**, equipment **1.064**,
  occupancy **1.000**, n=12 archetypes (`extra/MEASUREMENT_open-03_vintage-at-head.md` §5).
- Disk-cost context: the register records untrimmed `fast_zone` city passes exceeding **800 GB** —
  which is why `trim_hourly` exists and why a full-fleet untrimmed run is **not** proposed here.

## 6. Task list

### T01 — Select the sample, deterministically

**What.** Build the 48-building sample list (4 per cell × 12) per §4 and write it to
`openubem/outputs/comparisons/open03_untrimmed_sample_eui.csv` with columns `cell`, `osm_id`,
`footprint_area_m2`, `levels`, `archetype_id`, `auto_total_eui_kwh_m2`, `percentile_slot`.

**Why.** A sample chosen after seeing the answers is not a sample. Fix it first, in one pass, and
never revise it later — if a building fails downstream it stays in the table as a failure row.

**How.** Read each cell's `05_results.csv`, keep `simulation_status == success`, sort by
`footprint_area_m2`, take integer index positions at 10/35/65/90 %.

**How to test.** The file has exactly 48 rows, 12 distinct cells, 4 rows per cell, and every
`osm_id` is present in that cell's `01_buildings.gpkg`. Report those four counts.

### T02 — Rebuild and simulate the sample untrimmed

**What.** For each of the 48, rebuild in `layout_assign` with **`trim_outputs=False`**, simulate
locally, and parse with the production `parse_building()`.

**Why.** This is the artifact T15, T18 and T20(a) each named and none could run.

**How.** §4's pinned recipe. One `run_dir` per building (rule 6). Record for every building:
`parse_status`, `total_eui_kwh_m2`, `floor_area_m2`, `num_zones`, the EnergyPlus outcome from
`classify_outcome`, the `.sql` size in bytes, and — for failures — the first line of the error.

**How to test.** Row count still 48. Report how many parsed `success` and how many did not, **with
the reason for each failure**. A failure rate is a finding, not something to hide.

### T03 — Join to `auto`, and size the disk cost

**What.** Join the 48 untrimmed `layout_assign` results to run 4's `auto` results on `osm_id`.
Report, **for the sample only and labelled as such**: (a) the pooled cross-mode gap (Σ energy ÷ Σ
floor area, both sides, same buildings), (b) the median per-building gap, (c) how much of the gap
survives when the floor-area denominator disagrees by more than 10 % (the OPEN-10 confounder T18
flagged), and (d) the mean and max untrimmed `.sql` size, with the implied full-fleet disk cost at
8,160 buildings.

**Why.** (a)–(c) are the first HEAD-consistent, generation-clean cross-mode numbers this arc has
ever had for OPEN-03. (d) is what a decision about a full-fleet untrimmed run would need, and
nobody has ever measured it.

**How to test.** State both weightings side by side, each labelled. If pooled and median disagree in
sign or size, **say so** — that disagreement is itself the finding (OPEN-59 taught this lesson).

### T04 — OPEN-18's slice: small buildings, cold cells

**What.** Using only the sample rows that are small buildings in cold cells (the 10th/35th
percentile slots of the four NYC cells), report the `layout_assign`-vs-`auto` gap for that slice and
compare it to the rest of the sample.

**Why.** OPEN-18's √S vertical-form distortion is recorded as biting hardest on small buildings in
cold cells, and T20(a) could not size the residual because no parseable number existed.

**How to test.** n is small — **state n explicitly in every sentence carrying a number**, and do not
generalise beyond the slice. If n < 5, say the slice is too small to support a conclusion and stop
there. That is an acceptable answer.

## 7. Stop-and-report points

- **CP-1 — after T04.** One checkpoint only; the whole plan is a single block of work. Stop, append
  four progress-log entries under §8, write the report, and report back. Do not continue past it.

## 8. Progress log

*(executor appends one entry per completed task here:*
`#### TXX — <title> — completed YYYY-MM-DD` *+ Artifacts / Deviations / Test status / Notes)*

#### T01 — Select the sample, deterministically — completed 2026-08-19
**Artifacts:** `openubem/outputs/comparisons/open03_untrimmed_sample_eui.csv` (48 rows).
**Test status:** 48 rows, 12 distinct cells, 4 rows per cell, slots 10/35/65/90 in every cell — all four counts pass.
**Deviations:** none. Selection verified deterministic in the script: stable `mergesort` on `footprint_area_m2`, integer index `int(n*p/100)`, no RNG.
**Notes:** run-4 (`open48_refleet4`) fixtures, `simulation_status == success` only, exactly as §4 pinned.

#### T02 — Rebuild and simulate the sample untrimmed — completed 2026-08-19
**Artifacts:** `scratchpad/open03-untrimmed-sample/<cell>/sim/<safe_id>/` (12 cells × 4 = 48 isolated run dirs); `..._sample_eui.csv` filled.
**Test status:** row count 48. **48/48 parsed `success`; 0 build failures, 0 simulation failures, 0 parse failures.**
**Deviations:** (1) executor stalled after launch without reporting — the run completed on its own and the director recovered state from disk; (2) undocumented `OPEN03_SMOKE_SLOTS` env gate at script lines 89–92, used for a 1-building smoke, not set for the full run; (3) no run log redirected to disk, so T02 wall-clock is unrecoverable.
**Notes:** `trim_outputs=False` and `resolution_mode="layout_assign"` confirmed at script line 139; one `run_dir` per building confirmed at lines 197–204 (OPEN-58 guard holds).

#### T03 — Join to `auto`, and size the disk cost — completed 2026-08-19 (by director)
**Artifacts:** `openubem/outputs/comparisons/open03_untrimmed_sample_join.csv`; report §3–§5 of `extra/MEASUREMENT_open-03-18_untrimmed-sample.md`.
**Test status:** both weightings stated and labelled. (a) pooled sample gap **−26.25 %** (108.64 vs 147.30). (b) median per-building **−24.40 %**. Pooled and median agree in sign and within 2 points — no OPEN-59-style disagreement. (c) area-agreeing subset n=21 pools to −19.73 % / median −25.87 %; that pooled figure is 75 % carried by one 88,309 m² Courthouse, and excluding it the other 20 pool to **−28.02 %** / median −26.05 %. **The gap survives the confounder.** (d) `.sql` mean **20.0 MB**, median 8.1, max 124.9, ≈1.40 MB/zone → full fleet 8,160 ≈ **159 GB** mean-based.
**Deviations:** executed by the director, not the executor (see T02).
**Notes:** 47 of 48 buildings sit below `auto`; the one exception is `austin_rural way/1165379866` at +2.67 %.

#### T04 — OPEN-18's slice: small buildings, cold cells — completed 2026-08-19 (by director)
**Artifacts:** report §6 of `extra/MEASUREMENT_open-03-18_untrimmed-sample.md`.
**Test status:** **n = 8**, stated in every sentence carrying a number. Slice pooled −27.98 % / median −26.36 % vs rest-of-sample (n=40) −25.00 % / −24.31 %.
**Deviations:** executed by the director, not the executor.
**Notes:** the ≈3-point separation is far inside the slice's own −12 % to −37 % spread. **OPEN-18 is not sized by this measurement** and the report says so; a purpose-built small-cold-cell sample would be needed. Reported as inconclusive rather than stretched into a conclusion.

---

**CP-1 signed by the director 2026-08-19.** Plan complete: T01–T04 done, all artifacts present.
Audit: only planned files touched (one new script under `scripts/analysis/`, two CSVs under
`openubem/outputs/comparisons/`, one report under `extra/`, this progress log); no file under
`openubem/`, `tests/` or `scripts/validation/` modified; no git write; no register edit; nothing
opened, closed, struck or retired. Three deviations recorded above and in §8 of the report.
**No adopted number changed — 153.8231 kWh/m² pooled over 8,153 buildings stands untouched.**
