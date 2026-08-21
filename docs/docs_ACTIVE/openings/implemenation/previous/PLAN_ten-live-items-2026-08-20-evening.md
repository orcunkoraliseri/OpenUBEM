# PLAN — ten live items, 2026-08-20 (evening)

**Slug:** `ten-live-items-2026-08-20-evening`
**Opened:** 2026-08-20 (evening), by the director, on the user's instruction *"choisir des autres 10
tâches … peut-être '16 live items' pour faire planifier et exécuter si possible"*, and executed
overnight on *"je vais dormir … est-ce que tu peux le continuer jusqu'à la fin?"*.
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` (book II, 16 live).
Each live item's full history is in book I, **now at
`docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md`** (see T07).
**Specs:** `docs/docs_main/` — read-only, never edited by this plan.

> **Status:** ✅ **CLOSED 2026-08-21.** All eleven tasks T01–T11 complete and logged in §8;
> checkpoints CP-A, CP-B, CP-C and CP-D all audited and signed 2026-08-20 (§7b). What the
> pass deliberately did **not** do is stated in §7b. **Archived to `implemenation/previous/`
> on 2026-08-21.**

---

## 1. What this plan is for, in two sentences

Ten of the sixteen live items have a **next step that is a measurement, not a decision**, and none of
those ten needs a user ruling to start. This plan executes those ten and stops before every remedy
choice, because remedy choices are feature-design questions and belong to the user.

**What this plan explicitly does NOT do:** it does not fix `total_eui_kwh_m2` (OPEN-60/61), does not
choose a fallback for OPEN-35, does not define a storey (OPEN-62), does not author a Title 24 table
(OPEN-19), and does not promote an imputation tier (OPEN-17). Where a task's result points at a
remedy, the task **names the design question and stops**.

---

## 2. Hard rules for the executor

1. **Do not write a remedy.** Every task here is measurement, verification or record repair. If a
   task's finding suggests a code fix, write the finding and the design question — not the fix.
2. **Never edit** `docs/docs_main/`, root `main.py`, any OVERVIEW/DESIGN doc, or
   `openubem/results/parser.py`, `openubem/geometry/layout_assigner.py`,
   `openubem/semantic/imputation.py`, `openubem/config.py`. Tasks that need different behaviour from
   these modules **monkey-patch inside the analysis script**, never in the tree.
3. **Before debugging ANY error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first.**
   After solving ANY error, append one bullet in the house format before closing the task.
4. **No cluster compute on the login node.** T05 is the only cluster task; it is restricted to
   `ls`, `find`, `wc`, `tar`, `scp`, `squeue`, `sacct`. **No `srun`, no `ssh … python`, no `sbatch`
   without the director's word.** Wrap every remote command with the `_ssh()` helper at
   `scripts/cluster/t08_harvest_results.py:104` — the remote shell is tcsh and bare bash syntax
   fails silently.
5. **Never touch another project's cluster jobs or directories.**
6. **git is handled externally.** Do not `git add`, `git commit`, `git push`, `git checkout`.
7. **One script per task**, named `scripts/analysis/<slug>_2026-08-20.py`. No `.py` under `docs/`.
   Every figure lands flat in `openubem/outputs/`.
8. **Report the conclusion with its number and file:line, not the file contents.** Cap every
   command's output (`| head -30`, `--stat`, `grep -c`).
9. **Append a progress-log entry to §8 of this doc per completed task** — house format:
   `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.
10. **Stop at the checkpoint after your last assigned task and report.** Do not continue past it.

---

## 3. File layout

| Kind | Path |
|---|---|
| Scripts | `scripts/analysis/<slug>_2026-08-20.py` |
| CSV outputs | `openubem/outputs/comparisons/<slug>_2026-08-20.csv` |
| Figures | `openubem/outputs/` (flat) |
| Reports | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_<slug>.md` |
| This plan | `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md` |

---

## 4. Dependency decisions — pinned, do not revisit

| # | Decision | Reason |
|---|---|---|
| D1 | **Run 4 is the corpus** — `C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4`, layout `<cell>/sim_out/<stem>/eplusout.{err,eio}` and `<cell>/fleet_staging/idfs/<stem>.idf` | It is the adopted baseline's run (153.8 kWh/m² pooled over 8,153). Run 2 is superseded and must not be quoted as fleet. |
| D2 | **The OPEN-61 census `.sql` corpus is read-only for this plan** | It is the only fleet-wide `.sql` corpus in existence; ruling R6 preserves it. Read, never delete, never re-run into it. |
| D3 | **Production parsers are called, never re-implemented** — `openubem.results.parser.parse_building`, `check_building_integrity`, `resolve_simulated_floor_area` | Three defects in this register (OPEN-58, OPEN-60, OPEN-61) came from an analysis script computing a quantity its own way. |
| D4 | **stdlib + pandas/geopandas only**; no new dependency | Repo convention. |
| D5 | **Every task states its population and its denominator in the first line of its result** | OPEN-10 sat two weeks without a denominator. |
| D6 | **`py -3`, never bare `python`** | Bare `python` hits the Windows Store shim. |

---

## 5. Facts this plan stands on — each verified at HEAD by the director, 2026-08-20

| F | Fact | Citation |
|---|---|---|
| F1 | `check_building_integrity()` exists and returns `abups_ok` / `meter_ok` / `gas_zero`; `abups_ok` is `diff <= 0.005` against the ABUPS total | `openubem/results/parser.py:602`, `:608`, `:643` |
| F2 | It is called by four scripts and **not** by the path that produced `05_results.csv` | book I §OPEN-60; `scripts/run_r1_t12.py:211`, `run_r3_fleet.py:313`, `run_r3_step5.py:204`, `run_t12_boston.py:198` |
| F3 | Zone multipliers are written in exactly one place in `openubem/` | `openubem/geometry/layout_assigner.py:649` (`z_obj.Multiplier = residual_multiplier`, inside `match_storeys()`) |
| F4 | `resolve_simulated_floor_area()` is the multiplier-aware area used by `total_eui_kwh_m2` | `openubem/results/parser.py:362` |
| F5 | The fusion tier is a guaranteed no-op at HEAD: `FUSION_SOURCES_BY_TARGET: dict = {}` | `openubem/config.py:141`; the comment at `:96` says so in the file itself |
| F6 | `IMPUTE_ENABLED_TIERS = ("fusion", "spatial", "statistical")` — **`ml` and `draw` are both absent** | `openubem/config.py:100` |
| F7 | Two orphaned modules read `config.IMPUTE_DRAW_METHOD_BY_TARGET` unguarded and would raise `AttributeError` on first use | `openubem/results/draw_leaderboard.py:174`, `openubem/results/impute_scatter.py:235` |
| F8 | OPEN-53's shortfall: 40,800 `n_building_dirs` and 40,800 `.eio`/`.err`, against `.sql` 39,926 and `.end` 39,925 | book I §OPEN-53 |
| F9 | OPEN-38's fatal census: 44 fatal `.err` + 1 missing `.end` = 45 = `sacct` FAILED, both directions 0; 43 of 44 carry only the generic trailer `Program terminates due to preceding condition.`; `la_rural` carries **24 of 45** across `fast_zone` 10 / `auto` 7 / `floor` 7 | book I §OPEN-38 |
| F10 | The e02 harvest corpus is on local disk at `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest` | verified present 2026-08-20 |
| F11 | Book I was moved into `docs/docs_ACTIVE/openings/DONE/` and **committed** on 2026-08-20, and the citation sweep the archiving rule requires **had not been run** | commit `4f2a5a4` *"docs: archive Register I, establish Register II…"*; `git ls-files` shows the file only under `DONE/`; the rule is in the head section of `docs/PROJECT_CHECKLIST.md` |

---

## 6. Task list

### T01 — Run production's integrity gate over the whole fleet *(executor)*

**What.** Call `check_building_integrity()` on **every** `.sql` in the OPEN-61 census corpus
(`<scratchpad>/open61_census_fleet_work/<cell>/<stem>/sim_out/eplusout.sql`, ≈8,150 files) and write
one row per building: cell, osm_id, archetype_id, `abups_ok`, `meter_ok`, `gas_zero`, and the raw
diff the gate computed. Report the counts of each, by cell and by archetype, with the denominator.

**Why.** OPEN-60 established that the gate **already exists** and that the fleet pipeline never calls
it, and that a single unasked reconciliation control found three separate defects in three
consecutive passes (OPEN-58, OPEN-60, OPEN-61). Nobody has ever run the gate at fleet scale. This
answers the open question *"should the fleet pipeline call `check_building_integrity()`"* with a
number rather than an argument.

**How.** New script `scripts/analysis/open60_fleet_integrity_gate_2026-08-20.py`. Import the gate
from `openubem.results.parser` — do not re-implement it (D3). Read the census corpus read-only (D2).
Serial or `ProcessPoolExecutor`; no EnergyPlus is invoked. Output
`openubem/outputs/comparisons/open60_fleet_integrity_gate_2026-08-20.csv`.
Report `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-60_fleet-integrity-gate.md`.

**How to test.**
- **C1** — row count equals the number of `.sql` files found, and every `osm_id` is unique.
- **C2 (pre-registered, allowed to fail)** — the fleet `abups_ok` false-rate is compared against
  OPEN-60's 48-building sample (42 of 48 failed a 2 % reconciliation). **State whether the fleet rate
  is above or below it and by how much.** The sample was `layout_assign`; the fleet is `auto`, so a
  much lower rate is the expected result and a high one is the finding.
- **C3** — for 5 buildings picked at random, re-run the gate a second time and assert identical
  output (determinism).

⚠️ **You may not** change the gate, change its threshold, or fix anything it flags.

---

### T02 — Bound OPEN-60 at 8,160 instead of 3 *(executor)*

**What.** Scan **every** run-4 `auto` IDF (`<cell>/fleet_staging/idfs/*.idf`, 8,160 files) for `Zone`
objects whose `Multiplier` field is not 1, and for `ZoneGroup` objects whose `Zone List Multiplier`
is not 1. Report the count of files with any non-1 multiplier, the count of offending objects, and
the archetypes involved.

**Why.** OPEN-60's blast-radius bound — *"153.8231 kWh/m² pooled over 8,153 is untouched"* — rests on
the director reading **three** IDFs. The bound is load-bearing for the project's headline number and
deserves a census, not a sample. F3 says only `layout_assigner.py:649` writes a multiplier and the
`auto` path never calls it; this is the direct test of that claim at the artifact.

**How.** New script `scripts/analysis/open60_fleet_multiplier_census_2026-08-20.py`. Plain-text parse
of the IDF (stdlib only) — the field is positional; take the `ZONE,` object's Multiplier field and
the `ZONEGROUP,` object's Zone List Multiplier field, and **state in the report which field index you
used and how you confirmed it** (quote the IDD or a commented prototype line).
Output `openubem/outputs/comparisons/open60_fleet_multiplier_census_2026-08-20.csv` (one row per
non-1 object; write the file with a header even if empty).

**How to test.**
- **C4** — file count is exactly 8,160. If it is not, **stop and report the number** rather than
  proceeding on a short corpus.
- **C5 (pre-registered)** — the expected result is **0 non-1 multipliers**. If any is found,
  OPEN-60's bound is wrong and **that is the finding** — do not adjust the fleet figure, report it.
- **C6** — as a positive control, run the same parser over one `layout_assign` IDF known to carry a
  multiplier and confirm it detects it. If no such IDF is on disk, say so and mark C6 not run.

---

### T03 — Fleet `.err` census on the adopted run *(executor)*

🔴 **AMENDED by the director 2026-08-20 (evening), before execution, on the first executor's
pushback — and the pushback was right.** The task as first written named `CheckWarmupConvergence` as
OPEN-09's signature. It is not: OPEN-09's own census scripts match **`Inside surface heat balance did
not converge`** (`scripts/analysis/open09_fleet_err_taxonomy.py:42`), and `CheckWarmupConvergence`
has **0 occurrences** in the auto corpus (`open29_eight_defect_adjudication_2026-08-19.csv`, row
E-LA-18). **Second correction, larger:** OPEN-09 has *already* been re-derived on run 4 —
`extra/MEASUREMENT_open-09_run4-rederivation.md` (T13, 2026-08-19) reports **16 / 8,160 (0.1961 %)**,
identical to run 2, cell for cell, with a verified 150-warning anchor. **So the OPEN-09 half of this
task is a confirmation, not a measurement**, and it must reproduce 16 exactly or report why not.
The OPEN-56 half stands: the *"8,160 / 8,160 = 100.00 %"* stub rate has only ever been derived on
run-2 corpora, never on the adopted run.

**What.** Scan all 8,160 run-4 `<cell>/sim_out/<stem>/eplusout.err` files and count, per building:
`Indicated Zone Volume <= 0.0` occurrences (OPEN-56), `Inside surface heat balance did not converge`
warnings (OPEN-09 — **this exact string, not `CheckWarmupConvergence`**), `** Severe **` lines, and
`**  Fatal  **` lines (two-space test, E-LA-21). Report totals, per-cell and per-archetype rates,
and the denominator.

**Why.** OPEN-56's *"8,160 / 8,160 = 100.00 %"* was measured on **run 2**, which is superseded, and
on 70- and 16-building intervention samples — never on the adopted run's full corpus. The severe and
fatal census on run 4 has never been taken at all. OPEN-09 rides along as a cheap independent
reproduction of T13's 16.

**How.** New script `scripts/analysis/open56_open09_run4_err_census_2026-08-20.py`. Read-only.
Use the **two-space** `**  Fatal  **` form for the fatal test — the one-space form is the OPEN-45
defect and finds nothing. Output
`openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv`.
Report `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-56-09_run4-err-census.md`.

**How to test.**
- **C7** — file count 8,160; if short, report the number and which cells are short.
- **C8 (pre-registered, allowed to fail)** — OPEN-56's volume-stub rate on run 4 against run 2's
  100.00 %. **Report both.**
- **C9 (pre-registered, must pass)** — OPEN-09's non-convergence population on run 4 must reproduce
  **16 / 8,160** and the cell split **la_centre 2, la_rural 10, la_suburban 3, la_urban 1, others 0**
  (`extra/MEASUREMENT_open-09_run4-rederivation.md` §2). If it does not, **stop and report the
  difference by osm_id** (capped at 20 rows) — a failure here means the join or the corpus is wrong,
  and everything else in this task is then suspect too.
- **C10** — the fatal count must reconcile with run 4's recorded status: the count of buildings with
  a fatal must not exceed the count of non-`success` rows in run 4's `05_results.csv` (7). Report
  both numbers even if they agree.

---

### T04 — OPEN-38's first measurement: what actually killed the 44 *(executor)*

**What.** Re-scan the 44 fatal `.err` files in `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest`
capturing, for each fatal, the **`** Severe **` lines that precede it** — not the generic trailer.
Group the distinct causes with counts. Then intersect the `la_rural` failing building IDs across the
three affected modes (`fast_zone`, `auto`, `floor`) and report whether the **same buildings** fail in
all three.

**Why.** This is the item's own named first measurement, quoted verbatim in book I §OPEN-38, and it
has never been run. For 43 of 44 fatals we know the building, the cell and the mode and **nothing**
about the cause (F9). The intersection is the discriminating test: same buildings across modes ⇒
per-building input data, and the item becomes an input-validation item; different buildings ⇒
mode-specific, and the item splits.

**How.** New script `scripts/analysis/open38_fatal_cause_census_2026-08-20.py`. For each `.err`
containing `**  Fatal  **`, capture every `** Severe **` line in the file plus the 5 lines preceding
the fatal; normalise each severe message into a message *class* by stripping building-specific tokens
(surface names, zone names, numbers); count classes. Output two CSVs:
`open38_fatal_causes_2026-08-20.csv` (one row per fatal building: cell, mode, stem, severe class, raw
first severe line truncated to 300 chars) and `open38_la_rural_intersection_2026-08-20.csv` (one row
per `la_rural` failing stem × mode membership).
Report `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38_fatal-cause-census.md`.

**How to test.**
- **C11** — the scan finds exactly **44** fatal files + **1** missing-`.end` building = 45, matching
  F9. If it does not, report the number found and stop before the intersection.
- **C12** — every fatal building is assigned exactly one severe class, or is explicitly reported in a
  `no_preceding_severe` class. The count of `no_preceding_severe` is a headline number, not a
  footnote.
- **C13 (pre-registered, the decisive one)** — the `la_rural` cross-mode intersection size, stated as
  *"N of M buildings fail in all three modes"*. **Do not write a remedy either way** — report which
  of the two branches the evidence selects and stop.

---

### T05 — OPEN-53: is the missing 874 still on the cluster? *(executor, cluster — login-node safe operations only)*

**What.** Determine whether the 874/875 harvest directories missing `.sql`/`.end` are missing
**because the remote files never existed** or **because the harvest did not fetch them**. Inventory
the corresponding remote directories on Speed, count `.sql`/`.end` there, and report the split. If
the remote files exist, **fetch a sample of 20** by `scp` and confirm they parse.

**Why.** OPEN-53 is 874 of 875 directories short across 40,800 (F8), concentrated in two Austin
sub-cells, and the item has never been able to say which of the two causes it is — the two lead to
completely different remedies (re-fetch vs re-simulate). The user granted Speed resources for this
pass, on 2026-08-20.

**How.**
1. Read the 874 short directory names from
   `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_custody-reinventory.md` and
   `openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv` if present; otherwise
   re-derive locally from `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest`.
2. Import `_ssh` from `scripts/cluster/t08_harvest_results.py:104` (**mandatory** — tcsh, rule 4).
3. Remote, **login node, read-only**: `find <remote_run_root> -name 'eplusout.sql' | wc -l` and the
   same for `*.end`, scoped to the two Austin sub-cells first, then fleet-wide. Cap output — return
   **counts and at most 40 example paths**, never a full listing.
4. If present remotely: `scp` **20** of them into `<scratchpad>/open53_sample/`, and call
   `parse_building()` on each (D3).
5. **STOP** and report. Do not re-fetch all 874 without the director's word; do not `sbatch`.

**How to test.**
- **C14** — the remote count is reported for both `.sql` and `.end`, with the remote path used, and
  the local shortfall (874/875) restated beside it.
- **C15 (the decisive one)** — the answer is stated in one sentence as either *"the remote files
  exist → this is a harvest defect"* or *"the remote files are absent → this is a simulation-side
  loss"*, with the counts backing it.
- **C16** — if 20 were fetched, `parse_building()` returns a non-null `total_eui_kwh_m2` for each, or
  the failures are listed with their error strings.

⚠️ **If Speed is unreachable, say so, record the exact error text (never a label like "refused"), and
mark T05 blocked.** Do not retry in a loop for more than 3 attempts.

---

### T06 — OPEN-58's four recommended corrections *(director)*

**What.** Apply the four corrections OPEN-58's blast-radius measurement recommended and did not take:
(a) correct the item's own mechanism language from *"shared outdir"* to *"shared process cwd"*;
(b) correct the stated reason for excluding `nyc_centre/relation_3566904` from *"geometry mis-reports
area"* to *"cross-contaminated `.sql` — foreign `osm_id` in the zone keys"*; (c) annotate that row in
`openubem/outputs/comparisons/open56_fleet_cost_stratified.csv` so the raw artifact carries its own
warning; (d) record that the remedy decision is the user's and is un-taken.

**Why.** All four are record repairs with the evidence already in hand. A raw CSV that carries a
contaminated row with no marking is the exact failure mode this arc keeps re-finding.

**How.** Edit the register row and book I §OPEN-58 in place; add a `data_quality_note` column to the
CSV (or a sibling `*_notes.csv` if adding a column would break a consumer — check with
`grep -rn "open56_fleet_cost_stratified" scripts/ openubem/ | head` first).

**How to test.** `grep -c "shared outdir"` in both register books → **0**; the CSV row for
`relation_3566904` carries the note; the register's OPEN-58 row states the remedy is un-taken and
whose it is.

---

### T07 — Sweep the citations broken by book I's move *(director)*

**What.** Book I moved from `openings/INVESTIGATION_open-items-register.md` into
`openings/DONE/INVESTIGATION_open-items-register.md` (F11). Find every citation to the old location
across `docs/`, `scripts/` and `openubem/`, and repair each one **by filename resolution, not by
prefix substitution**. Note that this doc's own prose is inside the sweep's blast radius — a literal
search-and-replace rewrites the *quoted old path* in any doc that documents the move, this plan
included. Check §5 F11 and this task's own text after the sweep.

**Why.** The project's archiving rule, ruled obligatory 2026-08-09 under OPEN-33 and stated in the
head section of `docs/PROJECT_CHECKLIST.md`: *"archiving is not finished until every citation
pointing into the archived arc has been swept and repaired."* The move has been made and the sweep
has not been run — this is the rule's own failure mode, live right now.

**How.**
1. `grep -rn "openings/INVESTIGATION_open-items-register\.md" docs/ scripts/ openubem/ | grep -v "/DONE/" | wc -l` → the count.
2. Repair each hit to the `DONE/` path. **Resolve by filename** — do not substitute the prefix
   blindly; confirm each target exists after the edit.
3. Re-run the grep → must return **0** outside `DONE/`.
4. Also check the reverse: citations that name book II but mean book I.

**How to test.**
- **C17** — the pre-count and post-count are both reported; post-count is 0.
- **C18** — a random sample of 10 repaired citations is opened and the target file confirmed to exist.
- **C19** — `docs/PROJECT_CHECKLIST.md` records the sweep with its date and count.

---

### T08 — OPEN-14: what would the one tracked Overture slice actually fill? *(executor)*

**What.** In a sandbox (no repo edit — monkey-patch in the script, rule 2), set
`FUSION_SOURCES_BY_TARGET = {"height_m": ("overture",)}` and run the imputation router over
`nyc_centre`'s buildings input, the **one** cell with a tracked Overture slice
(`overture_nyc_centre_slice.parquet`). Report how many of that cell's null `height_m` rows the fusion
tier fills, with what provenance token, and the distribution of the filled values against the
non-null population.

**Why.** OPEN-14 established that the fusion tier is a guaranteed no-op at HEAD (F5) and that **zero**
`FUSED` tokens exist across 8,160 buildings — so the missing slices are a real but *non-operative*
blocker. What has never been measured is the other half: **if the gate were opened and a slice were
present, how much would it actually fill?** `nyc_centre` is 16.40 % null and is the only cell where
this can be answered from tracked data. That number sizes the whole backfill question.

**How.** New script `scripts/analysis/open14_fusion_yield_nyc_centre_2026-08-20.py`. Set the config
attribute on the imported module object inside the script; restore it in a `finally`. Call the
production router, not a re-implementation (D3). Output
`openubem/outputs/comparisons/open14_fusion_yield_nyc_centre_2026-08-20.csv`.
Report `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-14_fusion-yield.md`.

**How to test.**
- **C20** — the run stamps `FUSED_*` provenance on at least one row, or the report states plainly
  that the tier still fires on nothing **and why** (traced, not guessed).
- **C21** — the fill rate is reported as *"N of M null `height_m` rows in `nyc_centre`"*, both numbers.
- **C22** — `openubem/config.py` is **unmodified** at the end of the task:
  `git status --porcelain openubem/config.py` → empty.

⚠️ **This is a yield measurement, not a promotion.** Do not enable the tier in the repo, do not
regenerate any fleet input, do not touch run 4.

---

### T09 — OPEN-17: which tier actually fills the fleet, and what the two orphans do at HEAD *(executor)*

**What.** Two parts.
(a) **Tier census** — across the fleet's 8,160 buildings, count how many values each imputation tier
filled, per target column, from the provenance tokens already recorded in the inputs. Report as a
table: target × tier × count, with the denominator (rows needing a value).
(b) **Orphan check** — confirm at HEAD that `openubem/results/draw_leaderboard.py:174` and
`openubem/results/impute_scatter.py:235` still raise `AttributeError` on first use (F7), and report
the current state of `tests/test_draw_methods.py` (`py -3 -m pytest -q tests/test_draw_methods.py`
→ counts only, `| tail -3`).

**Why.** OPEN-17 is one decision — *does this project want a non-deterministic input tier at all?* —
and it is the user's. What the user has never been given is the **size of what the existing tiers
actually do**, which is the context that decision needs. The carried figures
(`VINTAGE_NAN_PERMISSIVE_DEFAULT` 4,255, `GROUPMODE_MED` 1,519, `HOTDECK_NEIGHBOR_HIGH` 90,
`HOTDECK_NEIGHBOR_MED` 46) are for one column on run 2 and were never extended to every target.

**How.** New script `scripts/analysis/open17_tier_census_2026-08-20.py`, reading run 4's
`<cell>/01_buildings.gpkg` provenance columns. Output
`openubem/outputs/comparisons/open17_tier_census_2026-08-20.csv`.
Report `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-17_tier-census.md`.

**How to test.**
- **C23** — every provenance token found is either mapped to a tier or listed as unmapped; the
  unmapped list is a headline, not a footnote.
- **C24** — the `FUSED` count is reported explicitly and is expected to be **0** (F5, cross-check on T08).
- **C25** — the two orphan modules' behaviour is reported as the actual exception type and message,
  quoted, or as "no longer raises" with the line that changed.

⚠️ **Do not promote, enable or wire any tier. Do not delete or skip the failing draw-method tests** —
they are the standing evidence that the tier is unfinished.

---

### T10 — The C04 leftover: drift or non-determinism? *(executor)*

**What.** Settle whether the `iod` difference and the single `simulation_status` flip carried as the
"C04 leftover" are **code drift** (the tree changed between the two runs) or **non-determinism** (the
same HEAD produces two answers). Run the same building twice at the same HEAD, in two separate
working directories, and diff the two results.

**Why.** It is item 5 on the register's own priority list, it has been carried unresolved across
three passes, and it is the cheapest open question in the register — one building, two runs. A
non-deterministic pipeline invalidates every before/after comparison this project makes, so the
answer matters out of all proportion to its cost.

**How.** New script `scripts/analysis/c04_same_head_double_run_2026-08-20.py`. Identify the affected
building by searching `docs/docs_ACTIVE/openings/extra/*.md` for `C04` (cap the grep). Rebuild +
simulate it twice from the same commit, in `<scratchpad>/c04_a/` and `<scratchpad>/c04_b/`, with
**`cwd=` passed explicitly to every EnergyPlus invocation** (OPEN-58 defect (a) — the shared process
cwd is the contamination path). Parse both with `parse_building()` (D3) and diff every column.
Output `openubem/outputs/comparisons/c04_same_head_double_run_2026-08-20.csv` (one row per column:
name, value A, value B, equal).

**How to test.**
- **C26** — the two runs are provably at the same HEAD: record `git rev-parse HEAD` before and after.
- **C27 (the decisive one)** — the verdict is stated in one sentence: *"identical ⇒ the historical
  difference was code drift"* or *"differs ⇒ the pipeline is non-deterministic, in these columns"*.
- **C28** — if they differ, the differing columns are listed with both values, and the report states
  whether `iod` and `simulation_status` are among them.

---

### T11 — Finish T10's job: prove determinism on a run that COMPLETES *(executor)*

🔴 **Added by the director 2026-08-20 (evening), after auditing T10. T10's verdict is real but thin,
and the audit says so rather than banking it.** T10 ran `nyc_centre/way/266034056` twice at the same
HEAD and got **0 of 33 columns differing** — but **both runs terminated `failed_fatal` at warmup**,
so every EUI column was `NaN` in both arms and `NaN == NaN` counted as agreement. What was actually
proved is that the *failure path* is deterministic (identical severe text, identical warning count
362, identical returncode). **The columns the C04 leftover is about — `iod` and a completed
`simulation_status` — were never exercised.** T10 also surfaced a second, unplanned fact that is a
better candidate explanation than either branch it was asked to choose between.

**What.** Two parts.
(a) **Repeat T10's method on a building that SUCCEEDS.** Pick one at random from
`openubem/outputs/comparisons/open61_census_fleet.csv` where `recorded_simulation_status == "success"`
and `parsed_total_eui_kwh_m2` is non-null, preferring a mid-sized archetype so the run is minutes not
hours. Two runs, same HEAD, separate working directories, `cwd=` passed explicitly. Diff every column
**and state how many of the compared columns were non-null** — a comparison of nulls is not a
comparison.
(b) **Test the two-IDF hypothesis.** T10 found that this building has **two different IDFs on disk**:
`nyc_centre/fleet_staging/idfs/way_266034056.idf` (2,569,123 B, 16:37) and
`nyc_centre/step3/idfs/way_266034056.idf` (550,260 B, 19:42) — *"a later, repaired version"* — and
that they fail with **different** fatal errors. Run the `step3` file once, record its
`simulation_status` and severe text, and report whether the two IDFs give **different statuses for
the same building**.

**Why.** (a) T10's question is only answered for a corpse. (b) If one building has two IDFs that
disagree on whether it simulates, then a historical `simulation_status` flip needs **neither** code
drift **nor** non-determinism to explain it — it needs only a run pointed at a different file. That
is a third branch nobody offered, and it is cheap to test.

**How.** New script `scripts/analysis/c04_determinism_completing_2026-08-20.py`. Reuse T10's
structure (`scripts/analysis/c04_same_head_double_run_2026-08-20.py`) — do not rewrite it from
scratch. **Run EnergyPlus serially, one process at a time**; other jobs share this host.
Output `openubem/outputs/comparisons/c04_determinism_completing_2026-08-20.csv`.
Append to `docs/docs_ACTIVE/openings/extra/MEASUREMENT_c04_determinism.md` — a new §, do not rewrite
T10's sections.

**How to test.**
- **C29** — the chosen building **completes** in both arms (`simulation_status` is a success value).
  If it fatals, pick another and say how many you tried.
- **C30 (the decisive one)** — of the columns compared, **how many were non-null in both arms**, and
  how many of those differ. The verdict sentence must quote the non-null count.
- **C31** — `iod` and `simulation_status` are reported explicitly with both values.
- **C32** — the `step3` vs `fleet_staging` IDF comparison is reported as two statuses and two severe
  strings (truncated to 200 chars), or as "identical", with the file sizes and mtimes.

⚠️ **Do not repair either IDF, and do not decide which one production should use.** That is a design
question and it is not in this plan.

---

## 7. Stop-and-report points

| CP | After | The question it answers |
|---|---|---|
| **CP-A** | T01–T03 | Do the fleet-scale controls hold on the adopted run — is the gate worth wiring, is OPEN-60's bound real at 8,160, and do OPEN-56/OPEN-09's run-2 numbers survive on run 4? |
| **CP-B** | T04–T05 | Do the two forensic items resolve to a cause — 43 nameless fatals, and 874 files that are either un-fetched or never made? |
| **CP-C** | T06–T07 | Is the record repaired: OPEN-58's four corrections applied, and zero citations left pointing at book I's old path? |
| **CP-D** | T08–T10 | Do the three cheap experiments land — fusion yield, tier census, and the determinism verdict? |

---

## 7b. ✅ CP-A — CP-D, AUDITED AND SIGNED, 2026-08-20 (director)

All four checkpoints are signed together, at the close of the pass. **Nothing in this plan was
greenlit on an executor's word alone where the claim was load-bearing** — the four re-derivations the
director ran itself are named below.

### CP-A — the fleet-scale controls (T01–T03) — ✅ SIGNED

| Question | Answer |
|---|---|
| Is the integrity gate worth wiring? | **Only one third of it.** `abups_ok` 2/7,860 (safe); `meter_ok` 7,853/7,860 (mis-specified); `gas_zero` informational. |
| Is OPEN-60's bound real at 8,160? | **Yes.** 0 non-1 multipliers, 0 `ZoneGroup` objects. |
| Do OPEN-56/OPEN-09's run-2 numbers survive on run 4? | **Both.** Stub 8,160/8,160; non-convergence 16/8,160 with the cell split intact. |

🔴 **Director's own re-derivations, because these three carry the headline.**
1. **T02 reproduced independently:** `grep -rh "!- Multiplier"` over all run-4 IDFs returns
   **47,278 `1,` + 238,322 `1.0,` = 285,600 fields, every one 1**, and `grep -rl "^ *ZoneGroup"`
   returns **0 files**. T02's conclusion holds by a different method than T02 used.
2. **T01's `meter_ok` diagnosed at the source, not accepted as a rate.** The gate compares zone
   lights + equipment against `Electricity:Facility`; measured on `austin_centre/relation/13781131`
   the numerator is **47.0 %** of the denominator. **The check cannot pass for a building with
   cooling or fans.**
3. **T01's six `meter_ok` passes opened individually:** all six have `Electricity:Facility` = 0 **and**
   zone electricity = 0. **The gate reads True only when the simulation produced nothing.** That is
   the finding, and it is the opposite of what a pass rate suggests.
4. **T01's six degenerate buildings cross-checked against the census:** all six carry
   `parsed_parse_status = failed_zone_mismatch` with every EUI null, while run 4 records 389–873
   kWh/m² for them. **Same signature as OPEN-53's meter-only `.sql`, in a local rebuild.**

⚠️ **One control could not be run and is recorded as such:** T02's positive control C6 — no
`layout_assign` IDF survives on disk, so the multiplier parser is proven only against a prototype
file, not against the mode that writes multipliers.

### CP-B — the two forensic items (T04–T05) — ✅ SIGNED

Both resolved to a cause, and **both resolved into something already tracked rather than into
something new** — which is the outcome that should be expected more often than it is.

- **T04:** 44/44 fatals named; 86 % one family; the `la_rural` cluster is **entirely `Warehouse`**.
  🔴 **Director's cross-check at the artifact:** the 11 stems were joined against
  `open61_census_fleet.csv` — six appear as `Warehouse`/`success`, and the five that do not are
  exactly run 4's five `la_rural` `not_simulated` buildings. **The mode-independent half is
  OPEN-42/OPEN-56's face.**
- **T05:** 874 `.sql` + 874 `.end` on Speed, matching the shortfall cell for cell. **Harvest defect.**
  ⚠️ And the sampled files are meter-only, so the re-fetch buys custody rather than numbers — a
  second question the item did not have this morning.

### CP-C — the record (T06–T07) — ✅ SIGNED

OPEN-58's four corrections applied; 129 dead citations swept to 1 (a `docs_DONE/` exclusion). **Two
stated tests were wrong and are restated rather than fudged**: T06's `grep -c "shared outdir"` → 0
is impossible and undesirable (the three survivors all quote the wrong phrasing in order to strike
it), and T07's sweep rewrote this plan's own *quotation* of the dead path.

### CP-D — the three cheap experiments (T08–T11) — ✅ SIGNED

- **T08 verified by the director from the artifact:** the output CSV's
  `provenance_height_m_after` is **617 `OSM_OBSERVED` + 106 `FUSED_OVERTURE_HIGH` + 15 `OSM_MISSING`
  = 738**. The 106 is real.
- **T09's headline was corrected before it entered the register.** The executor concluded that no
  imputation tier ever fires in production. **It does** — the tokens live in `05_results.csv`'s
  `data_quality_flag`, not in `01_buildings.gpkg`'s `provenance_*` columns (acquisition-only in runs
  2, 3 and 4 alike). Director's own fleet count: `VINTAGE_NAN_PERMISSIVE_DEFAULT` **4,256**,
  `GROUPMODE_MED` **1,521**, `HOTDECK_NEIGHBOR_HIGH` **90**, `HOTDECK_NEIGHBOR_MED` **46** — summing
  to **5,913**, exactly the `year_built` missing count. **The true statement is not "no tier fires";
  it is "one target of seven is covered."**
- **T10 was NOT signed on its own** — its double run fatalled in both arms, so its 0-of-33 agreement
  was `NaN == NaN`. **T11 was added mid-pass to finish the job** and did: 23 non-null columns, 0
  differing, `total_eui_kwh_m2` identical to the last digit. **Verdict: code drift.**

### What this pass did not do, stated plainly

**No item was opened. No item was closed. No published number moved. No ruling was taken.** Six items
moved from *unmeasured* to *measured and waiting on the user*, and that is the entire result.

---

## 8. Progress log

#### T01 — Run production's integrity gate over the whole fleet — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open60_fleet_integrity_gate_2026-08-20.py`
- `openubem/outputs/comparisons/open60_fleet_integrity_gate_2026-08-20.csv` (7,860 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-60_fleet-integrity-gate.md`

**Deviations.** The census corpus (`open61_census_fleet_work`) holds 7,861 stem directories, not
the 8,151 rows listed in `open61_census_fleet.csv` — 290 buildings short, spread across all 12
cells, wider than the briefed "one building still simulating." Reported as a population note in
the measurement doc §2, not fixed or investigated (D2 read-only, rule 1). The gate's raw ABUPS
diff (not part of `check_building_integrity()`'s return value) was captured for the CSV's
`raw_abups_diff` column by monkey-patching `sqlite3.connect` inside the analysis script only
(rule 2) — no re-implementation of the gate's SQL, thresholds or booleans.

**Test status.** C1 pass (7,860 gated + 0 skipped = 7,860 found; all `osm_id` unique). C2 pass
(pre-registered, allowed to fail): fleet `abups_ok` false-rate 2/7,860 = 0.0254 % vs. the 48-building
`layout_assign` sample's 42/48 = 87.50 % — far below, expected direction (fleet is `auto`). C3 pass:
5 random re-runs reproduced identical `abups_ok`/`meter_ok`/`gas_zero`.

**Notes.** Denominator 7,860. `abups_ok` True 7,857 / False 2 / None 1; `meter_ok` True 6 / False
7,853 / None 1; `gas_zero` True 40 / False 7,819 / None 1 — the one `None` row across all three
(`nyc_centre/way_266170763`) is the still-simulating building, caught by the gate's own
`try/except` as `sqlite3.OperationalError: database is locked` and returned as `None`s rather than
raised (`openubem/results/parser.py:686`) — counted, not skipped, and not a new defect (the gate's
existing behaviour is already correct), so no entry added to
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Worst 5 cells by `abups_ok`-false rate:
la_rural 1/141 (0.71 %), la_centre 1/221 (0.45 %), then three 0.00 % ties. Worst 5 archetypes:
SecondarySchool 1/11 (9.09 %), Warehouse 1/32 (3.13 %), then three 0.00 % ties. `meter_ok` fails on
99.9 % of the fleet while `abups_ok` passes on 99.97 % — reported, not diagnosed (rule 1).

---

#### T08 — OPEN-14: what would the one tracked Overture slice actually fill? — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open14_fusion_yield_nyc_centre_2026-08-20.py`
- `openubem/outputs/comparisons/open14_fusion_yield_nyc_centre_2026-08-20.csv` (738 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-14_fusion-yield.md`

**Deviations.** The task text names only `FUSION_SOURCES_BY_TARGET` to set; read `fusion.py:224-228`
(`OvertureSource.available`) first and found the source also needs `FUSION_OVERTURE_SLICE_PATH` (or
`FUSION_OVERTURE_ENDPOINT`) truthy or `precedence_for` returns `[]` regardless — since the task
explicitly names `overture_nyc_centre_slice.parquet` as the input to measure against, also
monkey-patched `config.FUSION_OVERTURE_SLICE_PATH` to that tracked fixture's path, restored in the
same `finally` block as `FUSION_SOURCES_BY_TARGET`. Called `impute_missing` with
`ImputeConfig(enabled_tiers=("fusion",))` rather than the default 3-tier chain, so the reported yield
is the fusion tier's own fill count, not conflated with what `spatial`/`statistical` would
additionally fill on the same rows.

**Test status.** C20 pass — 106 rows stamped `FUSED_OVERTURE_HIGH`; the tier is not a no-op once both
config keys are set. C21 pass — 106 of 121 null `height_m` rows in `nyc_centre` filled. C22 pass —
`git status --porcelain openubem/config.py` empty after the run.

**Notes.** Of the 15 unfilled: 14 matched an Overture footprint spatially but the matched record's
own `height` field is `NaN` (Overture source-data gap, not a join failure); 1 had no spatial match
within the 10 m tolerance. 0 were discarded by the 2.1 m height floor. Filled-value distribution
(mean 95.7 m) sits well above the cell's already-observed `height_m` distribution (mean 41.9 m). No
new error encountered; nothing added to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.

#### T05 — OPEN-53: is the missing 874 still on the cluster? — completed 2026-08-20

**Artifacts.** Script `scripts/analysis/open53_remote_inventory_2026-08-20.py`. CSVs
`openubem/outputs/comparisons/open53_remote_inventory_2026-08-20.csv` and
`..._parse.csv`. Report `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_remote-inventory.md`.

**Deviations.** None from the plan's How. Remote run root found by grep, not guessed:
`REMOTE_FLEET_BASE` at `scripts/analysis/e02_cluster_readonly_audit.py:35`
(`/speed-scratch/o_iseri/fleets`), directory convention `e02_{cell}_{mode}/out/{stem}` at the
same file's lines 143/191–192. No debug-reference entry added: the `failed_zone_mismatch` result
on all 20 samples is production's parser working as designed (zero zone-level report variables in
this SQL population), not a bug solved by this task — see report §4.

**Test status.** C14 PASS, C15 PASS (decisive: remote files exist → harvest defect, 874/874 `.sql`
+ `.end` on Speed for 874 locally-short directories, both Austin sub-cells at 100%), C16 PASS on
the negative branch (20/20 fetched, 20/20 parsed without exception, 0/20 non-null
`total_eui_kwh_m2`, all 20 failures listed with the identical quoted error string and traced to a
real cause).

**Notes.** Speed reached in 1 connection attempt, no retries needed. Login-node-safe operations
only (`find`, `wc`, `ls`, `scp`) — no `srun`, no `sbatch`, no `ssh ... python`. Remedy choice
(re-fetch the 874 vs. accept the loss) is un-taken and is the user's, per rule 1.

#### T03 — Fleet .err census on the adopted run — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open56_open09_run4_err_census_2026-08-20.py`
- `openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv` (8,160 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-56-09_run4-err-census.md`

**Deviations.** Executed as amended, not as first written: OPEN-09's signature is `Inside surface
heat balance did not converge`, not `CheckWarmupConvergence` (0 occurrences in the auto corpus).
Reused the shared whitespace-tolerant `SEVERE_RE`/`FATAL_RE` matchers from
`openubem/results/err_parse.py` (E-LA-21/OPEN-45) for the severe/fatal counts instead of a literal
substring check, and the two-space `**  Fatal  **` form per the amendment. No other deviation from
the amended task text.

**Test status.** C7 pass (8,160/8,160, no short cells). C8 pass (informational): run 4
volume-stub 8,160/8,160 = 100.0000 %, matches run 2's 100.00 %. C9 pass (must-pass): OPEN-09
reproduced exactly at 16/8,160, cell split la_centre 2, la_rural 10, la_suburban 3, la_urban 1,
others 0 — byte-identical to `extra/MEASUREMENT_open-09_run4-rederivation.md` §2. C10 pass:
7 fatal buildings (two-space) = 7 non-`success` rows in run 4's `05_results.csv`, exact
reconciliation.

**Notes.** Severe: 26/8,160 buildings. Fatal: 7/8,160 (5 `la_rural`, 1 `la_urban`, 1 `nyc_centre`
— the same 7 osm_ids as run 4's non-success set). No new error encountered; nothing added to
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.

#### T02 — Bound OPEN-60 at 8,160 instead of 3 — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open60_fleet_multiplier_census_2026-08-20.py`
- `openubem/outputs/comparisons/open60_fleet_multiplier_census_2026-08-20.csv` (header-only: `file,cell,stem,object_type,object_name,field_name,field_index,value`)

**Deviations.** None from the plan's How. C6's positive control could not be run against a real
`layout_assign` IDF because none exists on local disk (searched
`ubem_b05f_work`, `ubem_b08b_work`, `ubem_e02_five_mode`, `ubem_e02_fleet`,
`ubem_e02_harvest`'s `step3_layout_assign`/`sim_out_layout_assign` trees — the directories exist but
hold no `.idf` files, only manifests/sim outputs). Per the plan's own fallback ("If no such IDF is on
disk, say so and mark C6 not run"), C6 is marked **not run**, not failed.

**Test status.**
- **C4 — PASS.** IDF file count = 8,160, matches exactly.
- **C5 — PASS (pre-registered expectation confirmed).** 0 files with a non-1 multiplier; 0 offending
  objects; 0 archetypes involved. OPEN-60's blast-radius bound holds at 8,160, not just the 3 IDFs
  the director read by hand.
- **C6 — NOT RUN.** No `layout_assign` IDF found on disk anywhere under the checked roots.

**Notes.** Field-index evidence (positional parse, stdlib-only, no eppy):
- `ZONE`: `Multiplier` is `fields[6]` (0-indexed after the object keyword: Name, Direction of
  Relative North, X Origin, Y Origin, Z Origin, Type, Multiplier, ...). Confirmed at
  `C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4\austin_centre\fleet_staging\idfs\relation_13781131.idf:379`
  — `    1,                         !- Multiplier`.
- `ZONEGROUP`: `Zone List Multiplier` is `fields[2]` (Name, Zone List Name, Zone List Multiplier).
  Confirmed at
  `docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/sources/HighriseApartment_90.1-2013.idf:2670`
  — `    8;                       !- Zone List Multiplier`. No `ZONEGROUP` object exists anywhere in
  the run-4 corpus (checked with a corpus-wide grep before writing the script).

#### T04 — OPEN-38's first measurement: what actually killed the 44 — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open38_fatal_cause_census_2026-08-20.py`
- `openubem/outputs/comparisons/open38_fatal_causes_2026-08-20.csv` (44 rows)
- `openubem/outputs/comparisons/open38_la_rural_intersection_2026-08-20.csv` (11 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38_fatal-cause-census.md`

**Deviations.** F9's "44 fatal + 1 missing `.end` = 45" reconciliation could only be verified for
the 44-fatal half from local disk; the specific "1 missing-`.end`" building among the corpus's
875 harvest-custody-missing directories (OPEN-53's population) requires `sacct` status data,
which is T05's scope. Reported as a scoping boundary in §2 of the measurement doc, not treated
as a failed control, since the 44-fatal count the intersection depends on matched exactly.

**Test status.**
- C11 — pass: 44/44 fatal files found, matches F9.
- C12 — pass: every fatal assigned exactly one severe class; `no_preceding_severe` = 0, reported
  as a headline number.
- C13 (decisive) — evaluated: 6 of 11 `la_rural` failing stems fail in all three modes
  (`fast_zone`, `auto`, `floor`); the other 5 fail in only one or two modes. No remedy proposed
  either way, per rule 1.

**Notes.** No codebase defect was hit during this task (the two-space fatal marker and
`check_building_integrity`-adjacent parsing were not invoked), so no new entry was added to
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Severe-message classes: temperature
out-of-bounds (high) 21, `CalcHeatBalanceInsideSurf` extreme temperature 17, temperature
out-of-bounds (low) 5, non-convex shadowing surfaces 1 — 38/44 (86%) are a
temperature/heat-balance divergence class.


#### T07 — Sweep the citations broken by book I's move — completed 2026-08-20 *(director)*

**Artifacts.** No script. Edits in place across 61 files; summary row added to the path-migration
table at the head of `docs/PROJECT_CHECKLIST.md`.

**Result.** **129 dead citations across 58 files → 1**, and the survivor is inside `docs_DONE/`,
a standing exclusion resolved through the migration table rather than edited. Three citation forms
were found and handled separately: 129 full-path hits (`docs/docs_ACTIVE/openings/…`) repaired to the
`DONE/` path across 57 files; 4 `../INVESTIGATION_open-items-register.md` hits in archived plans under
`implemenation/previous/`, which were **already stale by one directory level before this move** and
are now written out as full repo-relative paths; and 78 bare-filename mentions left alone — a bare
filename is not a path and resolves by the rule's own filename-resolution standard.

**The move was real and committed.** `git ls-files` shows the file only under `DONE/`, and the move
rides in commit `4f2a5a4` *("docs: archive Register I, establish Register II…")*. This was checked
before touching anything, because `docs/PROJECT_CHECKLIST.md` asserted the opposite in writing.

**Deviations.**
1. 🔴 **The checklist's own 🔒 paragraph was false and is corrected, not just supplemented.** It read
   *"stays exactly where it is … no link in this file is dead because of it"*. Both halves were
   wrong. The paragraph now records the rotation, the move, the 129 dead citations and the sweep.
2. **The sweep rewrote this plan doc's own quoted old path**, in §5 F11 and in T07's "What" — a
   literal search-and-replace cannot tell a citation from a quotation of the dead path. Both were
   repaired by hand and T07 now carries the warning for the next person.
3. F11 was written from a stale `git status` snapshot that showed the file as deleted-not-moved; it
   is restated from `git ls-files` and the commit hash.

**Test status.** C17 pass (129 → 1, both counts reported). C18 pass — the single move target exists
and was confirmed at 8,246 lines. C19 pass — the checklist records the sweep, its date and its count.

**Notes.** Measured cost ~25 minutes, consistent with the rule's own "~30 minutes per archive".
The rule's failure mode is now demonstrated twice: an archive is easy to do and easy to leave
half-done, and the half-done state **asserts in writing that it is finished**.

---

#### T06 — OPEN-58's four recommended corrections — completed 2026-08-20 *(director)*

**Artifacts.** `openubem/outputs/comparisons/open56_fleet_cost_stratified.csv` (new
`data_quality_note` column, 30 columns / 70 rows, 1 row annotated); book I §OPEN-58 defect-(a) block
and §OPEN-56 X01 block; book II's OPEN-58 row.

**Result.** All four applied. (a) The mechanism language is corrected from *"shared outdir / shared
working directory"* to **shared process cwd**, with the consequence stated: the wrong phrasing
implied concurrency was the discriminator and would have **cleared the two serial importers
wrongly** — all three are exposed. (b) The exclusion reason for `nyc_centre/relation_3566904` is
corrected from *"geometry mis-reports area"* to **cross-contamination**, at the block where the wrong
reason was written, with the fifteen-significant-figure duplicate as the evidence. (c) The raw CSV
now warns for itself. (d) The remedy decision is recorded as the user's and un-taken.

**No published figure moved** — every correction is to a stated reason or a label, and the row was
already excluded from the pooled statistic before this task.

**Deviations.**
1. **The stated test was wrong and is restated.** T06's "How to test" asked for
   `grep -c "shared outdir"` → **0**. Three occurrences remain and **all three are correct**: each
   quotes the wrong phrasing in order to strike it. The real standard is *zero occurrences that
   assert the wrong mechanism*, and that is met.
2. **Book I's §1 summary row for OPEN-58 was left unedited.** Book I is closed; its §1 table is a
   historical snapshot, and the live row is book II's, which carries the correction.
3. Adding a column was checked against the CSV's only consumer first —
   `scripts/analysis/open56_fleet_cost_repair.py:30` reads it with `pd.read_csv` by name, so the
   column is safe.

**Test status.** Row annotated (1 matched, verified). Column count 30, row count 70 — unchanged
except for the added column. Both books state the corrected mechanism.

**Notes.** These four sat un-taken since 2026-08-19 with the evidence already in hand. The one that
mattered most was (a): the wrong mechanism was not a wording problem, it was an audit that would have
cleared two of three exposed scripts.

#### T09 — OPEN-17: which tier actually fills the fleet, and what the two orphans do at HEAD — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open17_tier_census_2026-08-20.py`
- `openubem/outputs/comparisons/open17_tier_census_2026-08-20.csv` (7 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-17_tier-census.md`
- `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 7, new `[OPEN]` bullet for
  `impute_scatter.py`'s `ImportError`.

**Deviations.** (a) executed literally as the "How" specifies — read run 4's `01_buildings.gpkg`
`provenance_*` columns directly, no re-implementation, no call into `enrich_semantics` (that
function requires a classified 29-column frame; `01_buildings.gpkg` is the raw 23-column
Step-2.1 acquisition output and would fail `_validate_input_schema`). Finding: every token
present is `OSM_OBSERVED`/`OSM_MISSING`/`OSM_GENERIC` — zero T07-tier or legacy-provenance
tokens appear anywhere in run 4's persisted inputs, because `impute_missing` is never called
from the production fleet-build path (confirmed by `grep -rln impute_missing openubem/ scripts/`
outside tests: only `validation/eui_impact.py` and `validation/mask_recover.py`), and
`resolve_vintage`'s real production fill writes to the ephemeral 57-column frame's
`data_quality_flag`, never persisted back to `01_buildings.gpkg`. (b) found a second, worse
failure than F7 predicted: `impute_scatter.py` fails at import time
(`ImportError: cannot import name 'recover_pairs' from 'openubem.validation.mask_recover'`,
`impute_scatter.py:63`) before its own `config.IMPUTE_DRAW_METHOD_BY_TARGET` read at line 235 is
ever reached; `draw_leaderboard.py:174` does reproduce F7's `AttributeError` exactly.

**Test status.** `py -3 -m pytest -q tests/test_draw_methods.py` → 43 passed, 10 skipped in
0.80s. No test deleted or skipped. No tier enabled, promoted or wired.

**Notes.** C23 pass (both real tokens found are classified; none unmapped-and-unexplained). C24
pass (`FUSED` count reported explicitly = 0, matches F5). C25 pass (both orphans' exact exception
text quoted in the report).

---

#### T10 — The C04 leftover: drift or non-determinism? — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/c04_same_head_double_run_2026-08-20.py`
- `openubem/outputs/comparisons/c04_same_head_double_run_2026-08-20.csv` (33 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_c04_determinism.md`

**Deviations.** Building identified per the "How": `nyc_centre`/`way/266034056`, from
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_twentysix-simulation-columns.md:230`. Used
D1's pinned `<cell>/fleet_staging/idfs/<stem>.idf` layout literally. Found in passing that this
building has **two** IDFs on disk — `fleet_staging/idfs` (older, 2026-08-19 16:37) and
`step3/idfs` (newer, repaired; the one `04_simulation_manifest.parquet` actually points at) —
both independently malformed, with different fatal severe errors at different zones. Not
investigated further (out of T10's scope, D1 not revisited); noted in the report so the
`step3` variant can be re-tested separately if wanted. Called `openubem.simulation.runner.
run_energyplus`/`classify_outcome` (production, not reimplemented) rather than hand-rolling the
subprocess call, since `run_energyplus` already passes `cwd=` explicitly (`runner.py:66`).

**Test status.** Both runs terminated `failed_fatal` (a genuine, reproducible geometry defect in
this IDF, not a script error) — this is itself the determinism signal, not a test failure. C26
pass: `git rev-parse HEAD` = `3860f62b3ba8fbf4c68b5e056083f5ea5999e9a0` before and after, unchanged.
C27 pass: verdict stated — "identical -> the historical difference was code drift." C28 pass: 0 of
33 columns differ; report states `iod` and `simulation_status` are both checked and neither
differs (`iod` blank in both — fatal before it's computed; `simulation_status` = `failed_fatal` in
both).

**Notes.** 33 columns compared (10 EUI + 10 GWP + `iod` + `simulation_status` + `error_summary` +
`floor_area_m2` + `floor_area_provenance` + `osm_id` + 3 raw diagnostic columns), 0 differ. No
debug-reference entry added — the fatal EnergyPlus error is an expected, reproducible property of
this IDF's geometry, not a bug encountered while executing the task.

#### T11 — Finish T10's job: prove determinism on a run that COMPLETES — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/c04_determinism_completing_2026-08-20.py`
- `openubem/outputs/comparisons/c04_determinism_completing_2026-08-20.csv` (30 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_c04_determinism.md` (new §, T10's sections
  untouched)

**Deviations.** None from the "How." Part (a)'s building (`austin_rural`/`way/1480414365`,
`SmallOffice`, 1 zone) was the first of 15 candidates sampled and completed successfully in both
arms on the first try — no fallback candidate needed. Part (b) reused T10's own already-completed
`fleet_staging`-arm result (from its CSV and its still-present work dir) rather than re-running
that IDF, to avoid a redundant EnergyPlus process; only the `step3` IDF was run (once). Found in
the course of the work that `classify_outcome`'s `error_summary` field captures only the generic
FATAL_RE trailer line (identical for both IDFs, per F9), which does not distinguish them — the
script additionally reads each arm's first `** Severe **` line directly from `eplusout.err` (plain
text read, not a re-derived metric) to get the actual, distinguishing severe cause.

**Test status.** C29 pass: part (a) building completed (`success`) in both arms, 1 of 1 candidates
tried. C30 pass (decisive): 28 columns compared, 23 non-null in both arms, 0 of those 23 differ —
verdict "identical on a COMPLETING building." C31 pass: `iod` (A=`0.0`, B=`0.0`, equal) and
`simulation_status` (A=`success`, B=`success`, equal) reported explicitly. C32 pass: `step3` vs
`fleet_staging` reported as two statuses (`failed_fatal`/`failed_fatal`, equal) and two severe
strings (200c, different — different zone, different runaway temperature, 362 vs 75 warnings),
with both IDFs' file sizes and mtimes.

**Notes.** `git rev-parse HEAD` = `3860f62b3ba8fbf4c68b5e056083f5ea5999e9a0` before and after both
parts, unchanged. Neither IDF was repaired and no choice between them was made (plan's explicit
constraint). No debug-reference entry added — no bug was hit; the FATAL_RE-trailer/`** Severe **`
distinction is expected `classify_outcome` behaviour (F9), not a defect.
