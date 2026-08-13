# PLAN — E02 audit and register closure pass

> **Slug:** `e02-audit-and-closure` · **Opened:** 2026-08-11 · **Author:** manager (director) session
> **Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`
> **Director prompt:** `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`
> **Predecessor plan:** `implemenation/PLAN_speed-resume.md` — **CLOSED at 1,451 lines, finished through
> R10. Do not append to it.** Prior findings are cited here by task ID (R01…R10), never re-derived.
> **DESIGN pointers:** no DESIGN doc governs this plan — it is measurement and bookkeeping only. Where a
> DESIGN question is reached (T04's remedy question, OPEN-35's intended fallback) the task **stops and
> reports**; it does not decide.

---

## 0. Why this plan exists, and the one thing it is optimised for

**The user's stated goal: the number of open items must go DOWN.** This plan is therefore built
backwards from closure, not from curiosity. Every task below is chosen because its finished state is a
**disposition** — an item struck from the register with a dated one-line reason — and not merely a new
measurement that opens two more.

**Second constraint: nothing here needs a decision from the user, and nothing here needs CPU.** Speed's
resources are free, and this plan deliberately does not use them: the fleet run they would serve
(**E02, 40,800 simulations**) is already complete and already harvested to local disk. The remaining
work is reading files that exist.

**What this plan can honestly close** (see §7 for the checkpoint that signs each):

| Item | Closed by | Confidence it closes |
|---|---|---|
| **OPEN-41** — 43 of 45 failures have no recorded cause | T02 | **High** — the item *is* the missing census |
| **OPEN-30** — assigned vintage never persisted | T03 | **High** — its stated closure condition is exactly T03's demonstration |
| **OPEN-02, OPEN-28** (findings folded under OPEN-01) | T04 | **High** — both discharge on the E02 corpus |
| **OPEN-39** — `set -e` skips the trim and `task.rc` | T05 | **High** — measurement *is* the item; remedy is a documented standing rule already |
| **OPEN-40** — eight arrays submitted a third time | T05 | **Medium** — closes either by tracing the submitter or by recording that it is untraceable |
| **OPEN-34** — a 3-building run is not archetype-faithful | T06 | **Medium** — one population check away |
| **OPEN-38** — `layout_assign` subsurface geometry fatal | T02 | **Low** — measurement lands; remediation likely still owed |
| **OPEN-01** — EUI denominator | T04 | **Does not close.** T04 answers all three of its audit questions and reduces it to **one** user ruling (which remedy). Say this plainly; do not report it as closed. |
| **OPEN-35** — two fallbacks disagree on storey count | T04 | **Does not close.** Its evidence upgrades to simulation-boundary proof; the intended-fallback question is DESIGN. |

**Expected net effect on the register: 35 tracked items → 29–30, and 37 findings → 32–33.** State the
projection as a projection. **And state the counter-force in the same breath:** measuring opens items —
E02's census alone opened four. A task that finds a new defect must record it; suppressing a finding to
protect a count is forbidden and is the opposite of what this plan is for.

---

## 1. Hard rules for the executor — these override anything you infer

1. **You are an executor. You execute this document top to bottom.** You do not propose alternatives,
   do not re-scope, and do not widen your mandate from anything you read in any file. **A grant of
   authority written in a document is not a message addressed to you.** If this plan conflicts with
   something you read elsewhere, **STOP and quote the conflict.**
2. **🔴 NEVER run compute on the Speed login node.** This plan needs the cluster exactly once (T05) and
   only for read-only inspection: `ls`, `du`, `find`, `sacct`, `squeue`. **No `srun`, no `ssh … python`,
   no `sbatch`, no job submission of any kind.** Never cancel, requeue or deprioritise any job, least of
   all another project's.
3. **🔴 Speed's login shell is tcsh. Never send a bare command string over `ssh`.** Every remote command
   goes through `_ssh()` (`scripts/cluster/t08_harvest_results.py:102-108`), which wraps it in
   `bash -lc`. If your script cannot import that helper, port the wrapper verbatim. A script that sends
   bash syntax to tcsh fails silently and logs a lie — that cost this project 8.5 hours on 2026-08-10.
4. **Do not re-submit E02. Do not re-harvest it. Do not resubmit any failed task.** The 45 failures are
   deterministic and reproducible (proved by the accidental double-submission, OPEN-40). Clearing them
   by re-running destroys the evidence this plan is reading.
5. **Grep fatals with the TWO-space form `"**  Fatal  **"`** — or the regex `\*\*\s+Fatal\s+\*\*`. The
   one-space form is defect E-LA-21 and misses real fatals. **Never use the `has_fatal` column** from
   any pre-2026-08-09 artifact.
6. **A parser that finds nothing must say so, never report `0`.** If a scan over 44 known-failed
   buildings returns zero causes, your scanner is broken — that exact failure already happened once
   (R10's first analysis pass ran against an empty root and reported every array clean). **Every scan in
   this plan carries a non-vacuity control, named in its own task. Do not skip the control.**
7. **Recompute every headline number from the named file before you write it down.** Do not carry a
   number from this plan, from the register, or from a prior task's report into your own results.
8. **Never `git commit`.** Git is handled externally by the user. Do not offer.
9. **No `.py` files under `docs/`, ever.** Scripts go in `scripts/analysis/`.
10. **Do not edit** root `main.py`, any OVERVIEW or DESIGN doc, or any frozen progress-log entry.
    Corrections are appended, never rewritten.
11. **Block on artifacts on disk. Never wait for a notification** — no one will wake you.
12. **Append a progress-log entry to §8 of this document after every task**, before starting the next.
    A task is not finished until its entry is written.

---

## 2. File layout

**Inputs — read-only, none of them in the project tree except the last:**

| What | Path |
|---|---|
| **E02 raw simulation output** (the corpus) | `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\<cell>_<mode>\<stem>\` |
| **E02 build tree** (IDFs + manifests) | `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_fleet\<cell>\step3_<mode>\` |
| **E02 run logs** | `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_five_mode\e02_run.log`, `e02_run_2.log` |
| **Adopted per-cell results** (the published denominator) | `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.csv` |
| **Prior measurement CSVs** | `openubem/outputs/comparisons/open35_neither_population.csv`, `open35_missing_input_census.csv`, `open01_denominator_factors.csv` |

**Outputs:**

| What | Where |
|---|---|
| Analysis scripts | `scripts/analysis/e02_*.py` — one per task, named in the task |
| Measurement CSVs | `openubem/outputs/comparisons/` (flat, `open<NN>_*.csv` naming) |
| Measurement reports | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_*.md` |
| Figures, if any | `openubem/outputs/` **flat**, mirrored to `docs/docs_ACTIVE/openings/` |
| Progress log | **§8 of this document** |

**Interpreter:** `./.venv/Scripts/python.exe`, run from `C:\Users\o_iseri\Desktop\OpenUBEM`.

---

## 3. Dependency decisions — pinned, do not re-litigate

1. **Parse the `.eio` by header name, never by column index.** Each file carries its own
   `! <Zone Information>` header line listing the fields; read that line, build a name→index map per
   file, then read the data rows. A fixed index will break on any file whose column set differs and you
   will not notice.
2. **Simulated floor area = Σ over `Zone Information` rows of
   `Floor Area {m2} × Zone Multiplier × Zone List Multiplier`, counting only rows whose
   `Part of Total Building Area` is `Yes`.** This is the multiplier-aware area OPEN-01 and OPEN-35 need
   — the plain floor-area sum is *not* it, and using the plain sum silently reproduces the very defect
   being measured. **Report both**: multiplier-aware and plain, in separate columns, so the multiplier's
   contribution is visible rather than assumed.
3. **Declared floor area = `footprint_area_m2 × levels`** from the adopted
   `phaseE/<cell>/05_results.csv`. That is the denominator the published EUI actually used, which is
   what OPEN-01 is about.
4. **Join key: `osm_id` ↔ directory stem, by replacing `/` with `_`.** Verified: `05_results.csv` holds
   `way/270445753`; the corpus directory is `way_270445753`. Do the mapping in one helper, once.
5. **No new dependencies.** `pandas`, `pyarrow` and the standard library are already in `.venv`. Do not
   add a package. Do not import EnergyPlus tooling — you are reading text files.
6. **Never reimplement pipeline logic to produce evidence.** If you need a value the pipeline computes,
   read it from the artifact the pipeline wrote or import the real function. A script that recomputes a
   pipeline result produces **lookalike evidence** — this project has one on record
   (`a1_prototype_storey_structure.csv`, §4 fact 12) and it is still misleading readers.
7. **Streaming, not slurping.** 40,800 `.eio` files at a ~76 KB median is ~3 GB of text. Read each file
   once, extract, discard. Write one row per building to a CSV as you go. Do not build a 40,800-entry
   list of file contents in memory.

---

## 4. Verified facts — every one grepped by the manager on 2026-08-11, with citations

Line numbers are as read on 2026-08-11. **Re-grep before acting on any of them** — a line-number
citation is evidence of a past reading, not of present state. This register's own count of the
one-space fatal test was wrong by two sites for exactly this reason.

1. **The corpus is on disk: 60 array directories** at
   `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest`, named `<cell>_<mode>`, five modes per cell
   including `layout_assign`. Spot-counted: `austin_centre_auto` = **413** building dirs;
   `la_rural_auto` / `la_rural_floor` / `la_rural_fast_zone` = **149** each.
2. **Each building directory holds four files:** `eplusout.eio`, `eplusout.end`, `eplusout.err`,
   `eplusout.sql`. Sampled: `austin_centre_auto/relation_13781131/` — eio 205,176 B, err 38,212 B.
3. **`.eio` structure, from that sample file:** `! <Zone Summary>` header at line 62, data at 63
   (`Zone Summary,45,400,115`); `! <Zone Information>` header at line **64**; data rows from line 65,
   each beginning `` Zone Information,``. The header names, in order, include `Zone Name`, …,
   `Zone Multiplier`, `Zone List Multiplier`, …, ` Floor Area {m2}`, `Exterior Gross Wall Area {m2}`,
   …, `  Part of Total Building Area`. **Note the leading/inner spaces in those field names** — strip
   before matching.
4. **The E02 build tree survives locally too**, and this was not previously recorded anywhere:
   `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_fleet\<cell>\step3_<mode>\` — **60 of 60
   `03_manifest.parquet` files present**, plus `03_idf_manifest.parquet`, `idfs/`, `weather/` and
   `02a_climate_epw.parquet`.
5. **The manifests carry `vintage_standard`** — R07's column, the one OPEN-30 was opened on. Columns:
   `osm_id, idf_path, archetype_id, zoning_strategy, num_zones, num_context_buildings,
   simplification_status, data_quality_flag, generation_status, resolution_mode, vintage_standard`.
   **Manager sample over 12 of the 60 manifests (4,164 rows): `DOERefPre1980` 4,084, `90.1-2019` 80.**
   That is a **sample, not the fleet** — T03 must recount all 60.
   *(`03_idf_manifest.parquet` does **not** carry the vintage column. Use `03_manifest.parquet`.)*
6. **Two generation-summary JSONs exist** at the root of that tree —
   `e02_generation_summary__batch_4cells_austin_centre.json` and
   `e02_generation_summary__la_urban_la_suburban_la_rural.json` — carrying per-`(cell, mode)`
   `n_rows`, `n_ok`, `non_success_counts`, `n_idf_on_disk`, `vintage_standard_present`,
   `vintage_standard_nonnull_pct`. **They cover two batches, not all twelve cells.** T03 must say what
   they do and do not cover rather than treating them as fleet-wide.
7. **The published denominator's source:** `phaseE/<cell>/05_results.csv` header begins
   `osm_id,footprint_area_m2,levels,height_m,archetype_id,zoning_strategy,data_quality_flag,` and
   carries `total_eui_kwh_m2`, `simulation_status`, `error_summary` among its 34 columns. Sample rows:
   `way/270445753,1239.859…,1.0`.
8. **`_ssh()` is at `scripts/cluster/t08_harvest_results.py:102-108`** and wraps the command as
   `["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"]`. **This wrapper is the point** (§1 rule 3).
9. **The harvest tar list now includes `.eio`** (R09):
   `tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end */eplusout.eio` at
   `t08_harvest_results.py:~131`.
10. **The harvest's fatal test is now the correct regex** (R02/R06):
    `re.search(r"\*\*\s+Fatal\s+\*\*", err)` at `t08_harvest_results.py:~246`.
11. **`submit_fleet_t08.sbatch`, for T05:** `set -e` at **line 18**; the EnergyPlus invocation at
    **56**; `RC=$?` and `echo $RC > "${OUTDIR}/task.rc"` at **57–58**; the trim block opens at **63**
    with the comment *"critical for fast_zone city passes (>800 GB untrimmed per city)"* and deletes
    `.eso/.mtd/.rdd/.mdd/…`. **Nothing guards line 56**, which is the whole of OPEN-39.
12. **`t08_full_sweep.py`:** `_FLEET_TAG = "t08"` at **:48** — 🔴 **any harvest of E02 needs the `e02`
    tag override or it reads stale directories and finds nothing**; `ALL_MODES` at **:55** lists
    **four** modes (`layout_assign` is absent — it came from the scratchpad driver); `CELL_CONFIGS` at
    **:57-71** lists all twelve cells; `03_manifest.parquet` is written at **:184**.
13. **Do not cite `openubem/outputs/comparisons/a1_prototype_storey_structure.csv` for anything about
    storey counts.** Its `num_modelled_storeys` is the **band count**, and its `has_multiplier_gt_1`
    flag tests `Zone.Multiplier` only — blind to the `ZoneGroup` list multiplier, so it reads `False`
    for both archetypes that carry one. It looks like it answers OPEN-01 and does not.
14. **Prior artifacts that exist and must be reused, not recomputed:**
    `open35_neither_population.csv` (2,611 rows — the buildings with neither `levels` nor `height_m`),
    `open35_missing_input_census.csv`, `open01_denominator_factors.csv`, `open28_t08_t20_join.csv`.

**Facts carried from the register, NOT re-verified by the manager this session** — treat as leads:
E02 = 40,800 tasks, 40,755 COMPLETED / 45 FAILED; 44 two-space fatals + 1 missing `.end` = 45;
`la_rural` holds 24 of the 45; the 45 reconcile 0/0 against `sacct` in both directions.

---

## 5. The rule that governs this arc

**No execution plan may be written for an item until that item's first measurement has been made.**
Measure → decide with the user → plan → execute. **This document is the measurement stage for every
item it touches. Remediation is forbidden inside every task below**, with one exception stated in T06
(register and board bookkeeping, which is the deliverable of that task rather than a code change).

If a task uncovers a defect, **record it and keep going**. Do not fix it. Do not fold it into another
item. A new item ID is `OPEN-42` and up; a new defect ID is `E-LA-42` and up.

---

## 6. Tasks

### T01 — Corpus integrity gate

**What.** Count, independently of any prior report, what is actually in the harvested corpus: per array
directory, the number of building directories, and the number of `eplusout.err`, `eplusout.eio` and
`eplusout.end` files. Produce `openubem/outputs/comparisons/e02_corpus_inventory.csv`
(one row per array: `cell, mode, n_dirs, n_err, n_eio, n_end`) plus a fleet total row.

**Why.** Every other task in this plan reads this corpus, and it lives in a Windows temp directory that
nothing protects. The register's expected numbers are **40,800 dirs = 40,800 `.err` = 40,800 `.eio`,
and `.end` = 40,799** (the one missing `.end` is the `std::bad_alloc` building). If the corpus has been
partially cleaned, every downstream number is wrong in a way that will look like a finding. **Cheaper to
know now than after T04.**

**How.** One pass with `os.scandir`. Do not open the files. Do not hash them. Compare your totals against
the four expected numbers above and **report any deviation as a deviation** — do not adjust your
expectation to match what you find.

**How to test.** (a) The 60 array names must be exactly the 12 cells × 5 modes from §4 fact 12 plus
`layout_assign` — enumerate them and assert the cross-product, do not eyeball. (b) Your `n_dirs` for
`austin_centre_auto` must be **413** and for the three `la_rural` arrays **149** — the manager counted
these independently (§4 fact 1); a mismatch means your counter is wrong, not that the corpus changed.
(c) `n_end` must be exactly one short of `n_dirs` fleet-wide, in exactly one array
(`nyc_centre_fast_zone`).

🔴 **If the corpus is short by more than the one known `.end`: STOP and report.** Do not re-harvest —
that is a cluster operation and it is not authorised in this plan.

---

### T02 — The causes of the 45 failures (OPEN-41) and the `layout_assign` geometry defect (OPEN-38)

**What.** Two censuses from one scan of the corpus's `.err` files.

**(a) OPEN-41 — why the failures failed.** For every building whose `.err` contains a two-space fatal,
capture **the `** Severe **` lines that precede the fatal**, not EnergyPlus's trailer. Group the
distinct causes. Output `openubem/outputs/comparisons/open41_failure_causes.csv` — one row per failed
building: `cell, mode, stem, n_severe, first_severe, last_severe_before_fatal, fatal_line,
cause_group`.

**(b) OPEN-41's concentration test.** `la_rural` holds **24 of the 45** failures across three unrelated
modes (`fast_zone` 10, `auto` 7, `floor` 7) in a 149-building cell — ≈4.7% against 0.11% fleet-wide.
**Intersect the failing building IDs across those three modes.** If the same buildings fail in all
three, the cause is per-building input data and this becomes an input-validation finding; if they do
not, it is mode-specific and splits. Report the intersection as a set, with counts, not as a
percentage.

**(c) OPEN-38 — the `layout_assign` subsurface defect.** Count **every** building fleet-wide whose
`.err` carries *"Base surface does not surround subsurface"*, in **all five modes**, not only in the 7
known failures — a building can carry the severe and still finish. Output
`openubem/outputs/comparisons/open38_subsurface_census.csv`: `cell, mode, stem, n_occurrences,
terminated (bool)`. Then state whether the message appears in any mode other than `layout_assign`.

**Why.** OPEN-41 is the register's clearest null-result-dressed-as-a-finding: 43 of 44 fatals are
recorded as `Program terminates due to preceding condition.`, which names nothing. Until the causes
exist, no remedy can be planned for any of them, and the item cannot close. OPEN-38's first measurement
is in the same files, and running it separately would mean scanning 40,800 files twice.

**How.** Stream each `.err` once. For the fatal test use `re.search(r"\*\*\s+Fatal\s+\*\*", txt)`.
For (a), find the fatal's character offset and scan **backwards** for `** Severe **` occurrences —
EnergyPlus writes the diagnostic before the trailer, and the last severe before the fatal is usually
the cause, but **capture the first and the last and let the report show both** rather than picking one.
For (c) a plain substring test on the message is enough; count occurrences per file.

**How to test.**
- 🔴 **Non-vacuity control, mandatory.** Your fatal scan must find **44** buildings, and the 45th
  failure (`nyc_centre/fast_zone`, the 89-storey `way_1240348353`) must be found **absent** — it died
  on `std::bad_alloc` with no `Fatal` string in its `.err` at all. **If you find 0, or 45, or 40,800,
  your scanner is broken. If you find 44 and the named building is not the exception, say so** — that
  contradicts the register and is a finding in its own right.
- **Known-cause control.** Exactly one of the 44 is self-describing:
  `CheckForRunawayPlantTemps: … too hot` in `la_centre/auto`. Your scan must reproduce it.
- **Known-severe control.** `nyc_centre/auto/way_266149332` is on record as reaching
  **90,915.77 °C** in `CalcHeatBalanceInsideSurf` during warmup. Your captured severe for that building
  must contain that mechanism. If it captures the trailer instead, your backwards scan is wrong.
- For (c), verify the 7 known `layout_assign` failures (`nyc_rural` 3, `la_centre` 1, `la_urban` 3) all
  appear in your census with `terminated = True`.

**Report:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-41-38_failure-causes.md`. State the cause
groups with counts, the `la_rural` intersection verdict, and — if the subsurface message appears in
surviving buildings — how many, because that changes OPEN-38 from a 7-building defect into a
population.

---

### T03 — Vintage persistence (OPEN-30) and the one-code-state demonstration (OPEN-01c)

**What.** Two read-only checks over the E02 build tree.

**(a) OPEN-30 — the vintage column, demonstrated.** Read all **60** `03_manifest.parquet` files. Report
the `vintage_standard` value distribution: fleet-wide, per cell, and per mode. Output
`openubem/outputs/comparisons/open30_vintage_distribution.csv`.

**(b) OPEN-01(c) — did all five modes come from one code state?** Assemble every piece of local evidence
that bears on it and state what it proves and what it does not: the two `e02_generation_summary__*.json`
files (§4 fact 6 — **they cover two batches, not twelve cells; say so**), the manifest column schema
across all 60 (a schema difference between modes would mean different code), IDF and manifest file
mtimes per `(cell, mode)`, and the `e02_run*.log` files. Output
`openubem/outputs/comparisons/open01c_code_state_evidence.csv`: `cell, mode, manifest_mtime,
n_manifest_cols, has_vintage_col, idf_dir_mtime_min, idf_dir_mtime_max, n_idfs`.

**Why.** OPEN-30's closure condition is written into the register verbatim: *"stays open until R07's
value distribution is demonstrated against the fleet's known ≈92.9% `DOERefPre1980` composition; a
column that comes out constant or uniform is a defect, not a pass."* That demonstration has never been
made, and everything it needs is on local disk. **This is the cheapest item closure available in the
whole register.** (b) is the third of OPEN-01's three audit questions and is independent of T04's
arithmetic, so it is done here where it is cheap.

**How.** `pandas.read_parquet` per manifest; concatenate the value counts, do not concatenate the
frames. For mtimes use `os.stat`. **Do not re-derive any vintage by calling `resolve_vintage()`** — that
would be reconstruction, not provenance, and the register rules it out explicitly (RULING D). Read the
persisted column.

**How to test.**
- **Non-uniformity control.** A constant column is a **defect, not a pass**. Report the number of
  distinct values and the share of the largest. The manager's 12-manifest sample gave
  `DOERefPre1980` 4,084 / `90.1-2019` 80 over 4,164 rows — so at least two values exist; if your
  fleet-wide read returns one, something is wrong.
- **Independent cross-check, and this is the one that settles it.** Take one cell —
  **`la_rural`, 149 buildings** — and check its manifest's `vintage_standard` against `year_built` in
  that cell's raw `01_buildings.gpkg`, which the manifest join never touches. R07's own control found
  **all 14 `90.1-2007` buildings at `year_built` 2005–2007 and all 135 `DOERefPre1980` at 1920–1979,
  zero crossover.** Reproduce it or report the discrepancy.
- **Coverage.** 60 of 60 manifests read, non-null percentage stated per `(cell, mode)`, and the fleet
  row count must total **40,800**.
- For (b): if the evidence cannot demonstrate one code state, **say that it cannot.** An honest "the
  local evidence is consistent with one code state but does not prove it, and here is precisely what is
  missing" is the correct output. Do not manufacture a proof from mtimes.

**Report:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-30-01c_vintage-and-code-state.md`.

---

### T04 — The floor-area audit (OPEN-01 a/b, OPEN-02, OPEN-28, OPEN-35)

🔴 **This is the load-bearing task of the plan and the reason E02 was run at all.** Read it twice
before starting.

**What.** Parse all **40,800** `.eio` files for the multiplier-aware simulated floor area, join to the
declared denominator, and report the error factor per mode.

Outputs:
1. `openubem/outputs/comparisons/e02_simulated_floor_area.csv` — one row per `(cell, mode, stem)`:
   `n_zones, area_plain_m2, area_multiplier_aware_m2, max_zone_multiplier, max_zone_list_multiplier,
   n_zones_excluded_not_in_total_area, parse_status`.
2. `openubem/outputs/comparisons/open01_denominator_audit.csv` — the join: adds
   `osm_id, footprint_area_m2, levels, declared_area_m2, error_factor (= simulated / declared),
   archetype_id_manifest, archetype_id_results, zoning_strategy_manifest, zoning_strategy_results`.

Report, per mode: n, median error factor, mean, range, and the share within ±1% of 1.0. Then the four
sub-questions:

**(a) OPEN-01(a) — `layout_assign`'s non-`applied` buildings**, which is where the defect was measured
(median ×2.0, range 0.118×–10.0×, only 12.6% correct). Report the same statistics restricted to that
mode and compare against `open01_denominator_factors.csv`'s inferred figures. **Do not overwrite that
file.**

**(b) OPEN-01(b) — the same fleet-wide, in all five modes.** This is the number that has never existed
for any mode: *does the adopted `auto` path divide by the right area?* Report `auto` first and
prominently — it is the mode the adopted ~~158.0~~ **157.1 kWh/m²** (pooled: total simulated energy ÷
total simulated floor area; the struck figure was a count-weighted mean of the 12 cell means,
superseded 2026-08-12, OPEN-43) baseline came from.

**(c) OPEN-28 — the generation confound, bounded.** E02 is a **fourth** harvest generation, and its
declared area comes from a **third-generation** file (`05_results.csv`). Quantify the confound rather
than waving at it: join `archetype_id` and `zoning_strategy` from E02's own `03_manifest.parquet`
(T03's tree) against the same columns in `05_results.csv`, and report agreement percentages per cell.
**Every table you produce must state which generation each side came from.**

**(d) OPEN-35 — the simulation-boundary check.** Restrict to the **2,611** buildings in
`open35_neither_population.csv` (neither `levels` nor `height_m`, all persisted at `levels = 1.0`) and
report their error-factor distribution against the rest of the fleet. **These are the buildings whose
archetype was chosen as if they were ~19 storeys and whose geometry was built at 1.** If the mechanism
is real, the `.eio` sees it. This is the independent check the register has been waiting for.

**Why.** Six thousand nine hundred and thirty-nine buildings are believed to divide by the wrong floor
area, on the strength of a **6-building** local sample and a code-contract inference. E02 exists to
replace that inference with a measurement over 40,800 runs. OPEN-02's finding — that no fleet EUI this
project has ever published has a verified denominator — discharges here, in every mode, for the first
time.

**How.** Stream the `.eio` files (§3 rule 7); parse by header name (§3 rule 1); compute the
multiplier-aware sum (§3 rule 2); write rows as you go. Then load the twelve `05_results.csv` files and
join on the stem↔`osm_id` mapping (§3 rule 4). Then load the 60 manifests for (c).

**How to test.**
- **Parse coverage.** 40,800 of 40,800 parsed, **0 parse failures** — R10 reports exactly this, so any
  failure is yours. A file that fails to parse must be **recorded as a failure, never skipped silently.**
- 🔴 **The multiplier control — this is the one that catches a wrong parser.** The register establishes
  that only **two** of 28 archetypes carry a `ZoneGroup` list multiplier: `MidriseApartment`
  (3 bands → 4 storeys, ×2) and `HighriseApartment` (3 bands → 10, ×8). **Your parse must find
  `Zone List Multiplier > 1` on `layout_assign` buildings of those two archetypes and essentially
  nowhere else.** If your `max_zone_list_multiplier` is 1 everywhere, you are reading the wrong column
  and every error factor you produce is worthless. **If it is >1 on a third archetype, that is a
  finding — record it, do not smooth it.**
- **Known-value control.** `MidriseApartment` `identity` buildings in `layout_assign` are on record as
  failing at **exactly 4/3** for a 3-storey building. Find at least one and reproduce it to ~0.1%.
- **The `applied` control.** `applied` buildings hold the assertion to ~0.002%. If your error factor for
  them is not ≈1.0, your join is wrong, not the pipeline.
- **Join integrity.** Report unmatched rows in **both** directions (corpus stems with no `05_results`
  row; `05_results` rows with no corpus directory) as explicit counts. **Never inner-join silently.**
- **Row count.** `auto` mode must join to 8,160 buildings if the corpus and the fixture agree; if it
  does not, the difference is a finding about generations, not a rounding issue.

🔴 **Stop conditions.** (1) If the fleet-wide `auto` median error factor is materially different from
1.0, **stop and report before writing any interpretation** — that would mean the adopted baseline's
denominator is wrong, which is a far larger claim than this plan is scoped for and is the user's to
hear first. (2) **Do not choose a remedy.** OPEN-01's remaining question is *which* of three remedies to
take (fix the denominator / fix the simulation / stop publishing per-building EUI for that mode) and it
is a scope decision for the user. Your job ends at the number.

**Report:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-audit-e02.md`. Lead with
`auto`, state the generation of every side of every comparison, and write the two sentences the register
demands together: the adopted baseline is measured clear of `layout_assign`, **and** OPEN-01/OPEN-03
remain exactly as large as they were measured.

---

### T05 — The two cluster-and-records items (OPEN-39, OPEN-40)

🔴 **This is the only task that touches Speed. Read-only. `ls`, `du`, `find`, `sacct`, `squeue` — and
every one of them through `_ssh()` (§1 rule 3). No `sbatch`, no `srun`, no `ssh … python`, no
deletions.**

**What.**

**(a) OPEN-39 — size the orphaned disk, and check nothing depends on `task.rc`.** A failed task exits
before the trim block runs (§4 fact 11), leaving ~40 MB of untrimmed output and **no `task.rc`**. Two
measurements: (i) on the cluster, size the output directories of the 45 known-failed E02 tasks and
compare against a same-cell sample of successful ones — `du -sh` per directory, then total; extend to
other fleets under `/speed-scratch/o_iseri/fleets/` **by directory listing and sampling, not by walking
every fleet**; (ii) locally, grep every harvest, resume and completion script under `scripts/` for
`task.rc` and report whether any uses its presence as a completion test.

**(b) OPEN-40 — trace the third submission.** Job IDs `1177095`, `1177838`–`1177841`, `1177875`,
`1178313`, `1178538` fall outside both documented waves (wave 1 `1176411`–`1176599`, wave 2
`1198104`–`1200571`). Check `sacct -j <id>` submission timestamps, `--format` including `Submit`,
`JobName`, `WorkDir` and `User`; check the scratchpad submit scripts and any shell history reachable on
the login node; check the two `e02_run*.log` files locally. **If it cannot be traced, that is the
finding** — record it as such and recommend the remedy the register already names: a submission log
nobody can bypass. **Do not reconstruct a story from timestamps.**

**Why.** Both are register-hygiene items whose entire content is a measurement nobody has made. Both
close on the measurement — (a) because the standing rule (*never use `task.rc` as a completion test*)
is already written and only needs a confirmed scope; (b) because the item itself states that an
untraceable submitter *is* the answer.

**How.** One script, `scripts/analysis/e02_cluster_readonly_audit.py`, importing `_ssh` from
`scripts/cluster/t08_harvest_results.py`. Batch the remote calls — one `du` over a directory list beats
45 round trips, and rapid-fire SSH to this host draws `Connection closed by 132.205.2.12 port 22`
(`rc=255`). If you hit that, back off **120 s** between attempts; a 90 s pre-sleep plus 120 s backoff is
on record as making both stuck fetches succeed on attempt 1.

**How to test.**
- **Log the actual remote error text, never a label.** A loop that records its own interpretation will
  report a bug in its own quoting as a property of the cluster. This is a named project rule and it
  came from an 8.5-hour silent failure.
- **Prove one success before leaving anything unattended.** Run one `_ssh("hostname")` and one
  `_ssh("du -sh <one known directory>")` and print both results before the batch.
- **Existence control for (a).** Pick one *successful* task directory and one *failed* one in the same
  array and show the size difference **and** the `task.rc` presence difference. If both have a
  `task.rc`, OPEN-39's mechanism does not fire as described and that is a finding.
- **Range control for (b).** Verify from `sacct` that the eight IDs really do fall outside both
  documented ranges before investigating who placed them. Do not take the ranges from this document.

**Report:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-39-40_cluster-records.md`.

---

### T06 — The closure pass

**What.** Four bookkeeping deliverables, in this order.

**(a) One last measurement — OPEN-34's remaining question.** OPEN-34's mechanism is settled
(subset-dependence: a 3-building batch gives a group median of 51 storeys, the full 738-building cell
gives 19). What is left is *whether any published result was produced from a batch small enough to
matter*, which the register records as **reasoning, not measurement**. Measure it: confirm that every
adopted fleet artifact was produced cell-at-a-time by checking the row count of each
`phaseE/<cell>/05_results.csv` against that cell's full building population in `01_buildings.gpkg`. If
every cell is whole, OPEN-34 closes with a dated disposition. Output
`openubem/outputs/comparisons/open34_cell_population_check.csv`.

**(b) Amend the register.** For every item this plan touched, append a dated amendment under that
item's own heading, and update its row in §1's table. **Append-and-amend only: corrections are struck
and dated, never deleted.** Update §1's count arithmetic explicitly — *"N at the start, −x closed, +y
opened, = M"* — so it can be checked. Update the "Next free item ID" line if you opened anything.

**(c) Refresh the progress board.** `implemenation/board_published-numbers.html`, republished to the
**same file path** so the URL is preserved
(https://claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639). The user's rules: **every task
appears, every task carries a short paragraph, and as each task completes the next moves into "in
progress."** Then refresh the snapshot copy at `reporting/board_published-numbers.html` — it goes stale
silently otherwise.

**(d) Update `docs/PROJECT_CHECKLIST.md` §M**, which indexes this arc and is the user's own monitoring
surface.

**Why.** An item that has been measured but not struck from the register is still an open item as far as
the register — and the user — is concerned. **The count only goes down when this task runs.** This is
also where the honest accounting happens: if the plan opened three items while closing five, the net is
two and the report says two.

**How.** Read each item's section before amending it; do not amend from this plan's summaries. For the
board, edit the existing HTML rather than regenerating it, so its structure and URL survive.

**How to test.**
- **Every closure carries a `path:line` or a named CSV.** A closure whose evidence is "T04 said so" is
  not a closure — cite the artifact.
- **Re-derive the count.** Recount §1's table rows yourself and confirm the arithmetic in the new
  amendment matches the table. The register has had a missing table row before (OPEN-41 was taken on
  2026-08-10 and its row was not added until 2026-08-11).
- **Board check.** Open the HTML and confirm the six tasks of this plan appear, each with a paragraph,
  and that exactly one is marked in progress at any time.
- **No frozen entry rewritten.** `git diff` on the register must show additions and struck-through
  corrections only — no deleted lines inside dated sections.

---

## 7. Stop-and-report checkpoints

Three. The director self-signs each on **independent re-derivation from raw artifacts** — a checkpoint
that cannot be re-derived is a **STOP**, not a formality.

**CP-1 — after T02.** Signs: the corpus is intact (T01), and the 45 failures have causes. Re-derivation
the director will run: an independent count of two-space fatals in two named arrays, and a hand-read of
`nyc_centre/auto/way_266149332`'s `.err` against the reported severe. **Report and wait.**

**CP-2 — after T04.** 🔴 **The load-bearing checkpoint of the arc.** Signs the denominator audit.
Re-derivation: the director will recompute the multiplier-aware area for a hand-picked sample of
buildings straight from their `.eio` text, including at least one `MidriseApartment` `layout_assign`
building with a list multiplier, and re-join them by hand. **Any number that does not reproduce is a
STOP.** **Report and wait.**

**CP-3 — after T06.** Signs the closure pass: the register's arithmetic, the board, the checklist.
Re-derivation: the director will recount §1's table and re-check every closure's cited evidence.

**Between checkpoints, work continues without asking.** Blocking mid-stream on a question this document
already answers is the failure mode to avoid; blocking on a question it does not answer is correct.

---

## 8. Progress log

*(Append one entry per completed task, in this format. Never rewrite an entry — correct it in a new one
that cites the old.)*

```
#### TXX — <title> — completed YYYY-MM-DD
**Artifacts:** <files written, with paths>
**Deviations:** <anything done differently from this plan, and why — or "none">
**Test status:** <each "How to test" item, with its actual result — not "passed">
**Notes:** <findings that do not fit above; new items/defects opened, with IDs>
```

*(No entries yet — plan written 2026-08-11.)*

#### T01 — Corpus integrity gate — completed 2026-08-11
**Artifacts:** `scripts/analysis/e02_corpus_inventory.py`;
`openubem/outputs/comparisons/e02_corpus_inventory.csv` (60 array rows + 1 `FLEET_TOTAL` row, 62 lines
including header).
**Deviations:** none.
**Test status:**
- (a) 60 array names on disk == the 12-cell x 5-mode cross-product (`auto`, `building`, `fast_zone`,
  `floor`, `layout_assign`), asserted by set difference, not eyeballed. `missing = []`, `extra = []`.
  PASS.
- (b) `austin_centre_auto` n_dirs = 413 (expected 413, match). `la_rural_auto` = 149, `la_rural_floor` =
  149, `la_rural_fast_zone` = 149 (all expected 149, match).
- (c) `n_end` is exactly one short of `n_dirs` fleet-wide (40800 − 40799 = 1), and the single array
  carrying the deficit is `nyc_centre_fast_zone` (n_dirs=738, n_end=737) — matches the register's named
  exception exactly.
- Stop condition: fleet totals are `n_dirs=40800, n_err=40800, n_eio=40800, n_end=40799` — exactly the
  four expected numbers from §6/T01, zero deviation. Stop condition NOT triggered.
**Notes:** No deviations found anywhere; the corpus is fully intact as the register expected. No new
items or defects opened.

#### T02 — The causes of the 45 failures (OPEN-41) and the layout_assign geometry defect (OPEN-38) — completed 2026-08-11
**Artifacts:** `scripts/analysis/e02_failure_causes_subsurface.py`;
`openubem/outputs/comparisons/open41_failure_causes.csv` (44 rows + header);
`openubem/outputs/comparisons/open38_subsurface_census.csv` (8 rows + header);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-41-38_failure-causes.md`.
**Deviations:** This entry was written to a scratchpad file
(`.../scratchpad/proglog_T02.md`) instead of being appended directly to this document's §8, per the
director's explicit instruction for this dispatch (other executors are writing to this plan document
concurrently). The director will merge it. No other deviation: one streaming pass over all 40,800 `.err`
files produced both censuses, per the plan's "why" (avoid scanning twice).
**Test status:**
- Non-vacuity control: fatal count = 44 exactly (not 0, not 45, not 40,800).
  `nyc_centre/fast_zone/way_1240348353` confirmed **absent** from the fatal set (`has_fatal = False`) —
  matches the register's `std::bad_alloc` account; its `.err` truncates mid-line with no `**  Fatal  **`
  line at all. PASS.
- Known-cause control: `la_centre/auto/way_319507579` reproduces
  `CheckForRunawayPlantTemps` ("Plant temperatures are getting far too hot, check controls and relative
  loads and capacities"). PASS.
- Known-severe control: `nyc_centre/auto/way_266149332` — captured `first_severe` == `last_severe_before_fatal`
  == `CalcHeatBalanceInsideSurf: The temperature of 90915.77 C for zone="WAY/266149332_F0_CORE", for
  surface="BLOCK CORE_ZONE STOREY 0 WALL 0004_1"`. Matches the register's 90,915.77 °C figure exactly;
  the backwards scan captured the mechanism, not the "Program terminates..." trailer. PASS.
- (c) known-7 control: all 7 known `layout_assign` terminated failures present with `terminated=True` —
  `nyc_rural` 3 (way_965718400/402/403), `la_centre` 1 (way_427942886), `la_urban` 3
  (relation_6374725, way_401910463, way_428846131). PASS.
- `la_rural` per-mode counts reproduce the register exactly: `auto` 7, `floor` 7, `fast_zone` 10 = 24
  total, all outside `building`/`layout_assign`. PASS.
**Notes:**
- (a) Cause groups over the 44 fatals: 25 "Temperature (low) out of bounds" (surface-temperature
  collapse), 17 `CalcHeatBalanceInsideSurf` (surface-temperature runaway, explicit routine), 1
  "Temperature (high) out of bounds", 1 `CheckForRunawayPlantTemps` (plant-loop runaway). All 44 are
  numerical thermal-runaway blow-ups during warmup/simulation; none is a syntax/missing-object/license
  failure. OPEN-41's "43 unexplained" no longer holds — every one of the 44 now has a recorded cause and
  group.
- (b) `la_rural` cross-mode intersection (auto ∩ floor ∩ fast_zone) = 6 buildings: way_472960972,
  way_472961034, way_472961047, way_472961088, way_472961091, way_472961171. Union across the three
  modes = 11 buildings. Verdict is **split, not clean**: 6 of 11 (55%) fail in all three modes regardless
  of geometry strategy (per-building input-data signature); the other 5 are mode-specific
  (way_472961092 auto-only; way_472961164 floor+fast_zone; way_472961089/090/093 fast_zone-only,
  consistent with fast_zone carrying extra sensitivity). Neither of the plan's two named outcomes applies
  cleanly — recorded as a dominant per-building cause with a smaller mode-sensitive edge, for OPEN-41's
  remedy discussion. No new item opened for this by itself.
- (c) OPEN-38 subsurface message: found in **8 buildings fleet-wide, all in `layout_assign`, zero in the
  other four modes** (confirmed by scanning all 40,800 `.err` files, not assumed). The known 7 terminated
  failures all reproduce. **New finding**: an 8th building, `nyc_rural/layout_assign/way_965718401`,
  carries the same severe (3 occurrences) but does **not** terminate — the run completes and presumably
  publishes an EUI from a malformed subsurface geometry. This is inside OPEN-38's own scope as T02(c)
  explicitly anticipated ("if the subsurface message appears in surviving buildings... that changes
  OPEN-38 from a 7-building defect into a population") — recorded under OPEN-38, no new OPEN-/E-LA- ID
  opened, since the task itself framed this exact outcome as part of OPEN-38's measurement rather than a
  separate defect.
- No new OPEN-42+ item or E-LA-42+ defect was opened by this task. Remediation was not attempted per §5.

#### T03 — Vintage persistence (OPEN-30) and the one-code-state demonstration (OPEN-01c) — completed 2026-08-11
**Artifacts:** `scripts/analysis/e02_vintage_and_code_state.py`;
`openubem/outputs/comparisons/open30_vintage_distribution.csv` (192 data rows: 60 `mode_cell` + 12 `cell`
+ 5 `mode` + 5 `fleet` rows); `openubem/outputs/comparisons/open01c_code_state_evidence.csv` (60 rows,
one per `(cell, mode)`); `openubem/outputs/comparisons/open30_la_rural_year_built_crosscheck.csv`
(detail behind the la_rural verdict, not plan-required but kept as supporting evidence);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-30-01c_vintage-and-code-state.md`.
**Deviations:**
1. Wrote the progress-log entry to a scratchpad file
   (`.../scratchpad/proglog_T03.md`) instead of appending directly to this plan doc's §8, per the
   director's explicit instruction that other executors are concurrently writing to this document —
   the director merges this entry in.
2. Added one CSV beyond the plan's two named outputs
   (`open30_la_rural_year_built_crosscheck.csv`) to carry the per-mode, per-vintage-class detail behind
   the la_rural cross-check verdict; not required by T03's "What," kept as supporting evidence rather
   than only asserting a verdict in prose.
**Test status:**
- **Non-uniformity control:** PASS. Fleet-wide `vintage_standard` has **5 distinct values**
  (`DOERefPre1980` 38,125 / `DOERef1980to2004` 1,065 / `90.1-2013` 890 / `90.1-2007` 610 / `90.1-2019`
  110), largest share **93.44%** — not constant, not uniform.
- **Independent la_rural cross-check (the one that settles it):** PASS — R07's zero-crossover finding
  reproduces exactly, run across **all five modes** (plan only required one cell; checked all five
  modes of that cell for completeness). `90.1-2007`: 14 buildings, 12 with known `year_built`, all 12 in
  2005–2007. `DOERefPre1980`: 135 buildings, 113 with known `year_built`, all 113 in 1920–1979. Zero
  crossover in either direction, all five modes identical. **Self-caught defect in the first pass:** an
  initial run flagged an apparent discrepancy (12/14, 113/135) — this was a script bug (NaN `year_built`
  scored as "out of range" instead of "unknown"), corrected before reporting; once missing values are
  separated out, every building with a *known* year falls inside its vintage class's window. Reported in
  the measurement doc as a corrected defect, not as a fleet finding.
- **Coverage:** PASS. 60/60 manifests read (`os.stat` + `pandas.read_parquet`, no `resolve_vintage()`
  call anywhere in the script). 100% non-null `vintage_standard` in every one of 40,800 rows. Fleet row
  total **40,800**, exact match to the expected fleet size.
- **(b) OPEN-01(c):** stated as **cannot fully demonstrate one code state, with the missing pieces named
  precisely** — see report. Positive evidence: single manifest schema across all 60 files; all 60
  manifest writes fall in one continuous 111-minute window (2026-08-09 21:03:01–22:54:38) with no gaps
  or out-of-order jumps; where a generation-summary JSON exists (35/60 pairs, 7/12 cells) it shows 100%
  `vintage_standard` coverage and a consistent `fleet_tag`. Gaps found and stated: no commit hash /
  code-version stamp recorded anywhere at generation time; 25/60 pairs (`nyc_centre, nyc_urban,
  nyc_suburban, nyc_rural, la_centre`) have no generation-summary JSON at all; and — the one genuine
  finding of this task — **the two `e02_run*.log` files the plan names as evidence do not in fact cover
  the audited corpus.** Both are dated 2026-08-06 (three days before the manifest-write window),
  reference `nyc_centre` only, and `e02_run_2.log` ends in an unhandled `MemoryError` inside
  `t08_local_remainder.py` — a local single-machine attempt that the register's own resume-amendment
  record (line 220–224) shows was abandoned and superseded by the actual Speed-cluster build
  (`PLAN_speed-resume.md` R01–R08) that produced the corpus this plan audits. Citing those two logs as
  fleet-wide code-state evidence would overstate what they show; the report says so directly.
**Notes:** No new register item or defect opened — the fleet's measured 93.44% `DOERefPre1980` share
closely matches (and modestly exceeds) the register's ≈92.9% proxy figure, which is the demonstration
OPEN-30's closure condition asks for. OPEN-01(c) itself does not close from this task alone — per the
plan and per OPEN-01's umbrella block, all three of (a)/(b)/(c) must be answered before OPEN-01 closes,
and (a)/(b) are T04's job, not this task's. This task's honest output for (c) is "consistent with, not
proof of" — reported as such rather than manufactured into a stronger claim.

#### T04 — The floor-area audit (OPEN-01 a/b, OPEN-02, OPEN-28, OPEN-35) — completed 2026-08-11
**Artifacts:**
`scripts/analysis/e02_t04_floor_area_audit.py`;
`openubem/outputs/comparisons/e02_simulated_floor_area.csv` (40,800 rows);
`openubem/outputs/comparisons/open01_denominator_audit.csv` (40,800 rows);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-audit-e02.md`.

**Deviations:**
1. Per the director's dispatch instructions for this run, this progress-log entry was written to a
   scratchpad file (`.../scratchpad/proglog_T04.md`) instead of being appended directly to §8 of
   `PLAN_e02-audit-and-closure.md`, because other executors are writing to that document concurrently.
   The director is asked to merge this entry into §8 in the correct task order.
2. No deviations from the task's method. One interpretive addition beyond the plan's literal text: the
   plan's `applied` control names "applied buildings" without specifying how to identify them from the
   E02 corpus. `open01_denominator_factors.csv` (the only artifact it says to compare against) turned
   out to hold **only the non-applied population** (6,939 rows) plus, inside it, 90 rows whose
   `old_status == 'applied'` but whose own `new_status` corrects them to `fallback_not_expressible`
   (a prior mislabeling, already fixed by that file's own analysis, not by this task). True `applied`
   buildings were identified as: `mode == layout_assign`, `zoning_strategy_manifest == 'layout_assign'`
   (went through `match_storeys()`), and absent from `open01_denominator_factors.csv` entirely — this
   gives 7,442 − 6,939 = 503, which matches the register's own stated arithmetic
   (`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md:536`) exactly. This derivation is
   documented in full, with the numbers that justify it, in §2 of the measurement report. It reads
   existing artifacts only; it does not recompute `match_storeys()` or any other pipeline logic.

**Test status:**
- **Parse coverage:** 40,800 of 40,800 parsed, **0 parse failures** (`parse_status == 'ok'` for all
  40,800 rows in `e02_simulated_floor_area.csv`). Matches R10's prior report exactly.
- **Multiplier control:** 2,850 zone rows fleet-wide have `max_zone_list_multiplier > 1`; **all 2,850
  are `mode == layout_assign`**, by archetype `MidriseApartment` 2,818 / `HighriseApartment` 32,
  **zero on any third archetype or any other mode**. Control PASSED cleanly, not smoothed.
- **Known-value control:** `way/401904735` (la_urban, layout_assign, MidriseApartment, `old_status =
  identity`, 3-storey declared) reproduces error factor **1.33331** against the expected 4/3 =
  1.33333 — **0.0018% off**, well inside the ~0.1% tolerance. The plain (unweighted) sum for the same
  building comes out 0.0018% from the *declared* area — i.e. would have silently looked correct,
  confirming the trap the plan's rule 2 warns about.
- **The `applied` control:** median error factor across the 503 true-`applied` buildings = **1.0000**
  (1.0000017 precisely), matching the register's ~0.002% precision claim almost exactly. Mean and
  tolerance-share are contaminated by two unrelated findings recorded below (§6 of the report); with
  the 6 worst-affected buildings excluded, mean = 0.9999, but only 79.28% sit within ±1% — the ~0.002%
  figure does not generalize past the median at fleet scale. Reported in full, not rounded up to "PASS."
- **Join integrity, both directions, all 5 modes:** 8,160 matched / 0 corpus-only / 0 results-only, in
  every mode (auto, building, fast_zone, floor, layout_assign) — zero unmatched rows in either
  direction anywhere in the fleet.
- **Row count:** `auto` joins to exactly **8,160** buildings.
- **Stop condition (fleet-wide `auto` median materially different from 1.0):** NOT triggered. `auto`
  median = **1.0000**, mean 1.0592 (tail-pulled by Finding 1 below), 99.63% (8,130/8,160) within ±1%.
  Proceeded to interpretation as instructed.

**Notes — findings, not remediated, IDs left for the director to assign:**
1. **Placeholder `footprint_area_m2 = 200.0` on 6 `Warehouse` buildings, present in every mode**
   (`la_rural/way/472961171`, `way/472960972`, `way/472961088`, `way/472961034`, `way/472961091`,
   `la_urban/way/402215469`), all flagged `data_quality_flag` containing `no_floors`. Produces error
   factors up to **336.65×** even in `auto` mode — a denominator data-quality defect, independent of
   the storey-matching mechanism this plan was built to measure. A widened scan
   (`footprint_area_m2 <= 210` and `archetype_id == 'Warehouse'`) found 16 buildings near this
   threshold fleet-wide (15 la_rural, 1 la_urban); 6 sit at the literal placeholder value.
2. **A `perimeter_core`-zoning geometry residual**, +2% to +31%, affecting the 24 non-Finding-1
   buildings outside ±1% tolerance in `auto` mode — all 24 carry `zoning_strategy_manifest ==
   'perimeter_core'`; the 718 `single_zone` / `one_zone_per_floor` buildings in the same mode
   (`layout_assign`) measured 100% within ±1%. Not sized beyond this report.
3. **`building` mode's fleet-wide median error factor is 0.5000** (mean 0.6287, only 39.94% within
   ±1%) — new information, never previously measured in any generation. Recorded, not investigated
   further; out of this task's scope.
4. (a)'s E02-measured non-applied statistics (median 0.9474, 2.05% within ±1%, n=6,939) do **not**
   closely match `open01_denominator_factors.csv`'s inference-based figures (median 2.0, 12.6% at
   exactly 1.0) — both agree the defect is large and the assertion rarely holds, but disagree on
   central tendency and shape. Recorded as a finding in §4 of the report; not reconciled (would require
   re-deriving one measurement from the other).
5. OPEN-35's mechanism (§7 of report) is now confirmed by direct `.eio` evidence: the 2,611-building
   subpopulation matches its own broken `levels = 1.0` denominator almost exactly in every mode except
   `layout_assign` (100% within ±1% in auto/building/floor, by construction — those modes build zones
   from `levels`), but breaks sharply under `layout_assign` (mean 2.3728, only 17.92% within ±1%)
   because that mode assigns storeys from the archetype rather than from the broken `levels` field.
   This directly proves the mechanism the register had previously only inferred.

**STOP conditions triggered:** none. Fleet-wide `auto` median is not materially different from 1.0;
proceeded to full interpretation per the plan.

**Task does NOT close OPEN-01 or OPEN-35**, per the plan's own §0 table — both are stated explicitly
as still-open in the measurement report's §8, with no remedy chosen (plan stop condition 2, "your job
ends at the number," honored).

#### T05 — Cluster and records audit (OPEN-39, OPEN-40) — completed 2026-08-11
**Artifacts:** `scripts/analysis/e02_cluster_readonly_audit.py`;
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-39-40_cluster-records.md`. No CSV outputs — the
plan's T05 "What" section names only the report, not a CSV.
**Deviations:**
- Progress-log entry delivered via scratchpad file per the director's explicit dispatch instruction
  (see note above), not appended directly to this document's §8 — other executors were writing to it
  concurrently.
- (a)(i)'s 45 failed-task identities were sourced by reusing T02's `open41_failure_causes.csv`
  (44 rows, already on disk when this task started) plus one independently reconfirmed local check for
  the missing-`.end` 45th failure (`nyc_centre/fast_zone/way_1240348353` — confirmed via
  `os.scandir` against the local harvest corpus), rather than re-deriving all 45 from scratch. This
  follows §3 rule 6 (never reimplement evidence that already exists on disk) and avoids a redundant
  40,800-file `.err` scan T02 had already completed.
- Discovered and worked around a previously undocumented remote-command length limit (see Notes) —
  the script was revised mid-task (`REMOTE_CMD_SAFE_LEN = 7500`, chunking) after the first attempt at
  the "other fleets" sampling step failed silently with `Unmatched '.`. The script was re-run clean
  end-to-end after the fix; all numbers below are from that clean run.
**Test status:**
- Connectivity proof: `_ssh('hostname')` -> `speed-submit1.encs.concordia.ca`; `_ssh('du -sh
  /speed-scratch/o_iseri/fleets/e02_nyc_centre_auto')` -> `872M`. Both printed before any batch. PASS.
- Existence control (a): `e02_la_centre_auto/way_319507579` (failed, 42M, no `task.rc`, full untrimmed
  file set) vs. `e02_la_centre_auto/relation_12292681` (succeeded, same array, 340K, `task.rc` present,
  trimmed file set). Size difference AND `task.rc`-presence difference both confirmed — OPEN-39's
  mechanism fires exactly as described; the "if both have task.rc, that's a finding" trap did not fire.
- Range control (b): all 8 job IDs confirmed outside both documented waves by direct arithmetic on
  `sacct` output (not taken from the plan document), AND by an independent from-scratch reconstruction
  of all 68 `e02_*` array submissions in the 2026-08-09/10 window from `sacct` (19 wave-1 + 8 orphan +
  41 wave-2 = 68, matching exactly).
- Total remote wall-clock: 13.8 s (cap 2,400 s / 40 min). No retries, no `Connection closed` errors, no
  backoff needed.
- Actual remote error text logged verbatim throughout, including the one real failure encountered
  (`Unmatched '.`, 13 chars) — never reduced to a label.
**Notes:**
- **OPEN-39 measured:** 45 known E02 failures orphan **≈2.14 GB total** (2,239,488 KB), mean ≈48.6
  MB/dir, vs. a matched 11-directory successful sample at 449 KB/dir mean (≈111× ratio). Confirmed
  **not E02-specific**: sampling 1 fleet per non-E02 tag family (19 fleets, 3 dirs each) found the same
  signature once more, in `t17_austin_centre_layout_assign/relation_13781131` (6.5M, `task.rc` absent,
  vs. 236K-492K/present for its array siblings) — independent evidence the defect replicates across
  the "T08 variant" template's other fleets, as OPEN-39's text already claimed. Grepped all of
  `scripts/` (15 `task.rc` references, 9 files): **zero** use `task.rc` presence as a completion test —
  every completion check in this codebase keys on `eplusout.end` content instead. The standing rule is
  confirmed preventive, not corrective, in this codebase today.
- **OPEN-40 measured:** submitter **untraceable** — this is recorded as the finding, per the plan's own
  instruction. No local script/log (checked: `e02_fleet_submit.py`, `e02_submit_remainder.sh`,
  `e02_remainder_jobids.txt`, both `e02_generation_summary__*.json` files, both `e02_run*.log` files)
  references any of the 8 IDs. `sacct`'s `JobName`/`WorkDir`/`User` are identical in form across all
  three waves (same `--job-name=e02_{cell}_{mode}` convention, same login-home `WorkDir`, same single
  user) and carry no discriminating signal. Remote `.bash_history` exists but its mtime (2026-04-27)
  predates the whole 2026-08-09/10 submission window and contains zero `e02` references — true of all
  three waves alike, so its silence is not evidence against the orphan wave specifically. Cross-check:
  all 8 orphan `(cell, mode)` pairs reappear in wave 2's own job list (`e02_remainder_jobids.txt`),
  confirming wave 2's accounting did not know about the orphan submission when it ran.
- **New finding, outside OPEN-39/40's scope, flagged for the director to ID (candidate OPEN-42):** a
  single `_ssh()` command string >= 8,192 characters returns `Unmatched '.` (a tcsh quote-parse error)
  and no useful output, reproduced with a quote-free payload (8,104 chars succeeds; 8,192 fails,
  exactly at the boundary) — so this is a genuine remote-side length limit, not a Python quoting bug.
  Previously undocumented anywhere in this project. This script now guards against it
  (`REMOTE_CMD_SAFE_LEN = 7500`); no other script in the repo currently builds commands long enough to
  hit it, but any future multi-target `_ssh()` batch should chunk under ~7,500 chars.
- No new items opened against OPEN-39 or OPEN-40 themselves — both measurements landed as the plan
  expected (§0's table: OPEN-39 "High" confidence to close, OPEN-40 "Medium," closing via untraceable
  finding). Register/board bookkeeping is T06's job, not this task's — no register edits made here.

#### T06 — The closure pass (part (a) only) — completed 2026-08-11
**Artifacts:** `scripts/analysis/e02_open34_cell_population_check.py`;
`openubem/outputs/comparisons/open34_cell_population_check.csv` (12 cell rows, one per phaseE cell).
**Deviations:** **Split-task deviation, by dispatch instruction.** This executor ran **T06 part (a) only**
— the OPEN-34 population measurement. Parts (b) register amendment, (c) board refresh, and (d)
PROJECT_CHECKLIST.md update were explicitly withheld and are owed to a separate pass. No register, board
HTML, or checklist file was touched by this entry. `01_buildings.gpkg` was read with the stdlib
`sqlite3` module (a GeoPackage is a SQLite database; `SELECT COUNT(*) FROM gpkg_contents`'s table gives
the feature table name, then `SELECT COUNT(*) FROM "<table>"`) rather than `geopandas`/`fiona` — no new
dependency, per §3 rule 5.
**Test status:**
- Recomputed every number from the named files, not carried from the plan: for each of the 12 phaseE
  cells, `n_rows_05_results` = `len(pandas.read_csv(phaseE/<cell>/05_results.csv))`;
  `n_buildings_gpkg` = row count of the single feature table in `phaseE/<cell>/01_buildings.gpkg`
  (confirmed via `gpkg_contents`, table name `01_buildings` in every cell).
- **Every `01_buildings.gpkg` used was found** at
  `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` — the file
  colocated with the cell's adopted `05_results.csv`, and the same path this arc's own prior measurement
  docs (`MEASUREMENT_open-34_subset-archetype-fidelity.md`, `MEASUREMENT_open-35-12_missing-input-census.md`,
  `MEASUREMENT_open-12-14_backfill-consumption.md`) already use and cite as git-frozen at commit
  `e063865` for all 12 cells. No cell's gpkg was missing; none was substituted.
- **Per-cell result — all 12 cells whole (difference = 0):**
  `austin_centre` 413/413, `austin_rural` 245/245, `austin_suburban` 437/437, `austin_urban` 425/425,
  `la_centre` 226/226, `la_rural` 149/149, `la_suburban` 1343/1343, `la_urban` 618/618,
  `nyc_centre` 738/738, `nyc_rural` 198/198, `nyc_suburban` 1589/1589, `nyc_urban` 1779/1779
  (format: `n_rows_05_results`/`n_buildings_gpkg`).
- **Fleet total:** sum of `n_rows_05_results` across the 12 cells = **8,160** — matches the register's
  and T04's stated `auto`-mode fleet row count exactly.
- **No cell where the counts differ.** Zero cells deviate; nothing to explain away.
**Notes:** OPEN-34's remaining question (register: recorded as reasoning, not measurement) is now
measured: every adopted `phaseE/<cell>/05_results.csv` has exactly as many rows as its cell's raw
`01_buildings.gpkg` has building features — no cell was produced from a batch smaller than its full
population, so the batch-composition effect this item is about (3-building batch → group median 51
storeys vs. full 738-building cell → 19) cannot have touched any published number. This finding supports
closing OPEN-34, but **the register amendment, board refresh, and checklist update (T06 parts b/c/d) were
not performed by this entry** and remain owed. No new items or defects opened by this measurement.

---

## 9. Director audit — checkpoints CP-1, CP-2, CP-3 — signed 2026-08-11

Every number below was **re-derived by the director from the raw artifacts**, not read from an
executor's report. Where a re-derivation contradicts an executor's wording, the raw file wins and the
correction is stated.

### CP-1 — signed, with one correction to OPEN-38's premise

**Re-derivations that reproduce.** Independent two-space fatal count by direct grep:
`la_rural_auto` **7**, `la_rural_fast_zone` **10** — matches T02 and the register. The failing stems in
those two arrays intersect in exactly the **6** buildings T02 names, union **11**; derived
independently before reading T02's CSV. Hand-read of
`nyc_centre_auto/way_266149332/eplusout.err:408` gives
`** Severe ** CalcHeatBalanceInsideSurf: The temperature of 90915.77 C for zone="WAY/266149332_F0_CORE"`
— the mechanism, not the trailer, which sits three lines below at `:414` as
`..... Last severe error=`. The backwards scan is correct.
`nyc_centre_fast_zone/way_1240348353/eplusout.err` contains **zero** matches for the fatal regex,
confirming the 45th failure is the no-`.end` `std::bad_alloc` building.

🔴 **Correction — OPEN-38's stated premise is FALSE.** The register describes 7 tasks that
*"die on EnergyPlus severe `Base surface does not surround subsurface`."* Read directly from the files,
that message is a **`** Warning **`**, not a Severe — at **all 8 sites**, in both the terminated and
the surviving building (`nyc_rural_layout_assign/way_965718401/eplusout.err:608,611,614` and
`way_965718400/eplusout.err:68,71,…`). It is not what kills anything.

**What actually kills all 7:** `way_965718400/eplusout.err:52-55` shows the whole chain —
`** Severe ** CalcHeatBalanceInsideSurf: The temperature of -12459.96 C for zone="LAUNDRYROOMFLR1"`,
then `**  Fatal  ** Program terminates due to preceding condition.`, then
`..... Reference severe error count=1`. **All seven `layout_assign` failures die on thermal runaway in
the zone `LAUNDRYROOMFLR1`** — the substituted prototype's laundry room, the same zone token as
OPEN-06 — at −12,459 °C, −23,743 °C, −11,950 °C, −15,491 °C, −12,901 °C, −59,865 °C and +182,399 °C.
**Zero of the other 37 fatals touch that zone; zero `layout_assign` fatals have any other cause.**
Verified against `open41_failure_causes.csv` by regex over `last_severe_before_fatal`.

The surviving building `way_965718401` ends
`EnergyPlus Completed Successfully-- 58101662 Warning; 0 Severe Errors` — it publishes results from
geometry carrying three unfitted doors. That half of T02's finding stands.

### CP-2 — signed. The load-bearing checkpoint reproduces exactly.

The director wrote an **independent `.eio` parser** (header-name lookup, multiplier-aware sum over
`Part of Total Building Area = Yes`) and ran it on the control building
`la_urban / way_401904735`, `MidriseApartment`, `one_zone_per_floor`, 3 storeys:

| mode | zones | plain sum m² | multiplier-aware m² | max list mult | error factor |
|---|---|---|---|---|---|
| `auto` | 3 | 5,551.35 | 5,551.35 | 1 | **1.00000** |
| `building` | 1 | 1,850.45 | 1,850.45 | 1 | **0.33333** |
| `layout_assign` | 27 | 5,551.26 | **7,401.68** | **2** | **1.33331** |

Declared area re-read by hand from `phaseE/la_urban/05_results.csv`:
`footprint_area_m2 = 1850.454098489866 × levels = 3.0` → **5,551.362295**. The 4/3 control lands at
**1.33331 vs 1.33333 = 0.0018% off**. Every figure is byte-identical to T04's
`e02_simulated_floor_area.csv` rows for the same building. **The parser, the multiplier handling and
the join all reproduce.**

**Two results the executor under-stated, re-derived by the director and promoted:**

1. 🔴 **`building` mode simulates exactly one storey.** T04 reports its median error factor as 0.5000
   without explaining it. Measured directly: `building`-mode simulated area ÷ **bare
   `footprint_area_m2`** (no `levels`) is **median 1.000000, 98.43% of the fleet within ±1%**. The mode
   builds one zone of one storey and the published denominator multiplies by `levels`, whose fleet
   median is 2. **The 0.5 is not noise — it is the storey count.** This is the first time any mode's
   fleet denominator has been measured, and one of the five is wrong by construction.
2. 🔴 **Six buildings carry a placeholder `footprint_area_m2` of exactly 200.0 m².** Fleet-wide there
   are exactly **6** such rows, all `Warehouse`, all flagged `no_floors` — five in `la_rural`
   (`way_472960972 / 472961034 / 472961088 / 472961091 / 472961171`) and one in `la_urban`
   (`way_402215469`). Their simulated areas run 4,064–67,330 m², so the **adopted `auto` mode** divides
   by a denominator wrong by **20.3× to 336.7×** on real published buildings.

### CP-3 — the finding that closes OPEN-41's open question

The register records `la_rural`'s failure concentration as *"a hypothesis, not a measurement."*
It is now measured, and the answer is not the cell — **it is the archetype.**

Joining `open41_failure_causes.csv` to the adopted `05_results.csv` on `(cell, stem)`:

| | buildings | tasks (×5 modes) | fatals | rate |
|---|---|---|---|---|
| `Warehouse` | **38** (0.47% of fleet) | 190 | **26** | **13.68%** |
| everything else | 8,122 | 40,610 | 18 | **0.0443%** |

**Relative risk ≈ 309×.** All 44 fatals by archetype: `Warehouse` 26, `SmallOffice` 6,
`MediumOffice` 5, `LargeOffice` 3, `FullServiceRestaurant` 2, `SecondarySchool` 1,
`QuickServiceRestaurant` 1. **36 of the 44 carry `no_floors`.**

**All 11 `la_rural` failing buildings are `Warehouse` with `no_floors`** — verified individually. The
cell holds 25 Warehouses of 149 buildings; 13 distinct Warehouses fleet-wide fail in at least one mode.
`la_rural` is over-represented because it is Warehouse-dense, not because the cell is special.
**Zero Warehouse fatals occur in `layout_assign`** (26 split auto 8 / floor 8 / fast_zone 10) — that
mode's seven failures are the separate `LAUNDRYROOMFLR1` mechanism above.

**Signed:** CP-1, CP-2, CP-3 — director, 2026-08-11. Every headline number re-derived from the named
raw file. Two executor characterisations corrected (OPEN-38's severity, `building` mode's 0.5); no
executor number failed to reproduce.

---

#### T06 (b)(c)(d) — The closure pass, bookkeeping half — completed 2026-08-11 (director)
**Artifacts:**
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — §0 amendment, §1 heading, count
  arithmetic block, 11 table rows amended or added, and 10 item sections amended under their own
  headings (OPEN-01, 02, 28, 30, 34, 35, 38, 39, 40, 41) plus a new OPEN-42 section.
- `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` — state box, §2 counts and
  retired-ID table, §3 owed rulings (two added), §4.4 corrected, §4.5 rewritten, §5.1 rewritten, §5.6
  amended, §7 evidence rules (four added) and operational facts (one added), §11 closing action.
- `docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html` + the
  `reporting/` snapshot — new work package `L` with all six tasks, each with a plain-language
  paragraph; header stamp and footer register line updated. Same file path, so the URL survives.
- `docs/PROJECT_CHECKLIST.md` §M — dated amendment with the full arithmetic and the three findings.

**Deviations:** (1) Parts (a) and (b)(c)(d) were split across two dispatches — the measurement to an
executor, the bookkeeping to the director — because the register and prompt are manager-owned. (2) The
five executors wrote their §8 entries to scratchpad files rather than to this document, to avoid four
concurrent writers racing on one file; the director merged them above. Both deviations are recorded in
the entries themselves.

**Test status:**
- **Every closure carries a `path:line` or a named CSV.** Checked: OPEN-30 → `open30_vintage_distribution.csv`;
  OPEN-34 → `open34_cell_population_check.csv`; OPEN-39/40 → `MEASUREMENT_open-39-40_cluster-records.md`;
  OPEN-41 → `open41_failure_causes.csv`; OPEN-02/28 → `e02_simulated_floor_area.csv` +
  `open01_denominator_audit.csv`. No closure rests on "a task said so."
- **Count re-derived, not asserted.** The director parsed §1's table programmatically after editing:
  **31 live rows**, 11 struck/retired — matching the stated 31 exactly. The 2026-08-10 failure mode
  (OPEN-41 taken but its table row never added) was specifically checked for and did not recur:
  OPEN-42's row was added in the same edit that opened it.
- **Board check.** All six tasks present in work package `L`, each with a paragraph, all `done`,
  none marked in progress — correct, because the plan is finished. Snapshot copy byte-identical
  (115,625 B both).
- **No frozen entry rewritten.** All register changes are additions or struck-and-dated corrections;
  the five executor progress entries above were appended verbatim.

**Notes:**
- **Final arithmetic: 35 tracked items − 5 closed + 1 opened = 31. Findings: 37 − 5 − 2 discharged
  + 1 = 31.** Against §0's projection of 29–30, the shortfall is two and both reasons are stated in
  the register rather than smoothed: **OPEN-38 did not close** (its premise was falsified and the item
  rewritten, which is more work than closing it), and **OPEN-42 opened**.
- **New item opened: OPEN-42** — the `Warehouse` population, both faces. **Next free item ID:
  `OPEN-43`.** No defect ID was taken, so `E-LA-42` and `E-UTCI-17` are unchanged.
- **Recorded as a standing operational fact rather than an item:** the `_ssh()` ≥8,192-character tcsh
  limit. Nothing is open — the one script that hit it now chunks, and no other builds commands that
  long — so it went into the director prompt's cluster section, not the register.
- 🔴 **Three things this pass did NOT do, stated so no one reads the closures as fixes.** The 2.14 GB
  is not reclaimed and `submit_fleet_t08.sbatch:56` is still unguarded (OPEN-39). The submission log
  nobody can bypass does not exist (OPEN-40). Not one failing building was fixed (OPEN-41/42).
  **Closing a measurement item records that the question is answered, not that the defect is gone.**

---

## 10. Plan status — 🟢 CLOSED 2026-08-11

**All six tasks landed; all three checkpoints director-signed by independent re-derivation from raw
artifacts. This document is finished. Do not append new tasks to it** — at 977 lines it is near the
project's ~1,000-line close threshold, and its successor should open as a fresh plan citing findings
here by task ID (T01…T06).

**What this plan produced, in one place:**

| Task | Item(s) | Outcome |
|---|---|---|
| T01 | corpus gate | 40,800 / 40,800 / 40,800 / 40,799 — intact, zero deviation |
| T02 | OPEN-41, OPEN-38 | 44/44 causes recorded; OPEN-38's premise falsified |
| T03 | OPEN-30, OPEN-01(c) | OPEN-30 closed; (c) honestly unprovable |
| T04 | OPEN-01 a/b, 02, 28, 35 | `auto` denominator measured correct; `building` mode wrong by a storey |
| T05 | OPEN-39, OPEN-40 | both closed; 2.14 GB sized; submitter untraceable |
| T06 | OPEN-34 + bookkeeping | all 12 cells whole; register 35 → 31 |

**What is owed to the user, and it is rulings only:** OPEN-22 (longest owed) · **OPEN-01(c) — accept
circumstantial evidence of one code state, or accept that OPEN-01 can never close on this corpus** ·
OPEN-01's remedy · CP-M2 · OPEN-11.

**Nothing is queued, nothing is in flight, no agent is running, and this arc has no use for Speed.**
