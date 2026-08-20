# PLAN — five open items, 2026-08-18

> **Slug:** `five-items-2026-08-18` · **Written:** 2026-08-18 by the manager session ·
> **Arc:** `openings` · **Register:** `../INVESTIGATION_open-items-register.md`
> **Director prompt:** `../prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` (§5.18 is this plan's log)
> **Predecessor:** `PLAN_open-49-and-open-01-2026-08-13.md` — fully executed, CP-1 and CP-2 signed
> 2026-08-17. Nothing was in flight when this plan was written.
>
> **The five items, and why these five.** All five are **local, read-only-or-small-edit, and blocked
> on nothing** — no cluster time, no user ruling, no simulation. Every other live register item is
> either waiting on a user decision (OPEN-17, OPEN-27, OPEN-35, OPEN-46, OPEN-48/49) or needs a fleet
> pass. Three of the five can close on this plan's evidence; two are decisive measurements that end a
> question each item has carried for weeks.
>
> | Task | Item | Shape | Can it close? |
> |---|---|---|---|
> | T01 | **OPEN-52** — fixed `--basetemp` makes concurrent pytest sessions delete each other's temp dirs | config fix + concurrency proof | **yes** |
> | T02 | **OPEN-51** — one defect ID `E-LA-16` used for two failure signatures | documentary adjudication | **yes** |
> | T03 | **OPEN-37** — five harvest sites still never fetch `.eio` | 5 one-line edits + local census | **yes** |
> | T04 | **OPEN-06** — no code state in this repo accounts for the archetype column | git archaeology, read-only | sharpens, may close |
> | T05 | **OPEN-42** — why the *zoning mode* decides whether a Warehouse blows up | `.eio` geometry diagnosis | sharpens, may close |
> | T06 | all five | register / checklist / director prompt + full suite | — |

---

## 2. Hard rules for the executor

1. **🔴 NO git write commands, ever.** `add`, `commit`, `restore`, `checkout --`, `stash`, `reset`,
   `clean` are all forbidden. Git is handled externally by the user. **Read-only git is required and
   expected**: `git log`, `git show <sha>:<path>`, `git diff`, `git status`. To see historical code,
   `git show <sha>:<path> > <scratchpad>/<name>.py` — never check anything out.
2. **🔴 NO cluster, no SLURM, no `ssh`, no `srun`, no `sbatch`.** Nothing in this plan needs Speed.
   Every artifact this plan reads already exists on this machine.
3. **🔴 ONE pytest session at a time, repo-wide.** This is the very defect T01 fixes. Do not start a
   pytest run while any other run is alive, including your own background ones. T01's deliberate
   concurrency experiment is the single exception and it runs against a scratchpad test file.
4. **No simulation.** No EnergyPlus invocation, no IDF regeneration, no re-run of any pipeline stage.
5. **Never edit anything under `docs/docs_DONE/`, `docs/docs_main/`, `docs/docs_stepN/`, root
   `main.py`, or any OVERVIEW/DESIGN document.** Archived arcs are the record; corrections are
   recorded in the live tree, not applied to the archive.
6. **Do not decide a DESIGN question.** If a task's answer requires choosing what the specification
   *should* say, STOP and report, quoting the conflict.
7. **Before/after evidence rule.** Any claim that a fix changed behaviour must demonstrate the OLD
   behaviour first, on the same harness. A test that passes both before and after proves nothing and
   must be reported as non-probative rather than counted.
8. **Never restate the fleet headline.** It is `157.1 kWh/m²`, **pooled**. `159.2157` is not a fleet
   figure and must not appear as one. No task here touches any published number.
9. **`.venv/Scripts/python.exe`** for every python invocation. No new dependencies.
10. **No `.py` files under `docs/`.** Scripts go to `scripts/analysis/`, CSVs to
    `openubem/outputs/comparisons/`, reports to `docs/docs_ACTIVE/openings/extra/`.
11. **Append one progress-log entry per task under §8** of this file, in the required shape, as each
    task lands — not in a batch at the end.
12. **Report what you saw, not what was expected.** A task that fails to reproduce its own premise is
    a result, not a failure, and must be reported as such.

---

## 3. File layout — nothing outside this list may be created or edited

**Edited (existing):**
- `pyproject.toml` — T01, the `[tool.pytest.ini_options]` block only
- `scripts/cluster/t07_harvest_results.py` — T03, line 102 only
- `scripts/validation/v11_nyc_centre_pipeline.py` — T03, line 290 only
- `scripts/validation/v12_cell_pipeline.py` — T03, line 354 only
- `scripts/validation/v12_nyc_urban_recovery.py` — T03, lines 94 and 199 only
- `openubem/geometry/layout_assigner.py` — T02, the comment at `:863-865` only, **and only if T02's
  adjudication proves it wrong**
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — **T06 only**
- `docs/PROJECT_CHECKLIST.md` — **T06 only**
- `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` — **T06 only**
- this plan's §8 — every task

**Created:**
- `scripts/analysis/open37_eio_census.py` · `scripts/analysis/open06_classifier_archaeology.py` ·
  `scripts/analysis/open42_zone_geometry.py`
- `openubem/outputs/comparisons/open37_eio_census.csv` ·
  `openubem/outputs/comparisons/open06_classifier_archaeology.csv` ·
  `openubem/outputs/comparisons/open42_zone_geometry.csv`
- `docs/docs_ACTIVE/openings/extra/FIX_open-52_pytest-basetemp.md`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-51_e-la-16-identity.md`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-37_eio-fetch-closure.md`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_classifier-archaeology.md`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_zoning-mechanism.md`

**Scratchpad** (anything temporary, never committed, never under `docs/`): the session scratchpad
directory given in your dispatch prompt.

---

## 4. Dependency decisions — pinned, do not revisit

- Python: `.venv/Scripts/python.exe`. Nothing is installed, upgraded, or pinned by this plan.
- `pandas` / `geopandas` / `pyarrow` are already in the venv and are the only libraries needed.
- EnergyPlus is **not** required by any task here.
- The E02 harvest corpus is at `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\<cell>_<mode>\<stem>\`
  and carries `eplusout.eio`, `.end`, `.err`, `.sql` per building — **verified present 2026-08-18** for
  `la_rural_auto/way_472960972`. It is a temp directory: **read it, never write into it.**
- The adopted-run frozen inputs are at
  `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` and
  `.../phaseE_elevrb/<cell>/05_results.csv`.

---

## 5. Facts this plan is built on, with citations — verified by the manager 2026-08-18

**OPEN-52**
- `pyproject.toml:51-54` — `[tool.pytest.ini_options]`, `tmp_path_retention_policy = "failed"`,
  `tmp_path_retention_count = 3`, `addopts = "--basetemp=.pytest_tmp"`.
- The pin's only author: `git log -S"basetemp" -- pyproject.toml` returns exactly one commit,
  **`fe05509`** — *"feat: implement climate zone assignment, building attribute enrichment, parallel
  EnergyPlus runner, and results parsing/carbon components"*. **Why it was pinned was never
  established**, and the register forbids removing the line until it is.
- Observed harm, register §OPEN-52: an executor's `1 failed, 6 passed in 12.67s` on
  `tests/test_sim_integration.py` against four sequential director runs of `7 passed` at ~66s.

**OPEN-51**
- Defining text: `docs/docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:279`
  — *"E-LA-16 — Cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family … OPEN — 2026-07-23 (T04/T05)"*,
  naming buildings `way/402036176`, `way/402036789`, `way/1395739331`.
- Competing reading: `implemenation/previous/PLAN_compute-queue.md:343`,
  `extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md:116`, and the live code comment at
  `openubem/geometry/layout_assigner.py:863-865`, which groups `CheckWarmupConvergence` with
  *"E-LA-14/16/18/19/E-LA-06"*.
- Files that mention the ID at all (15, from `grep -rl`): the four above plus
  `extra/MEASUREMENT_open-05_defect-id-sweep.md`, `extra/MEASUREMENT_open-29_defect-status-trace.md`,
  `extra/MEASUREMENT_open-29_eight-defect-recheck.md`, `implemenation/previous/PLAN_no-compute-queue.md`,
  `implemenation/previous/PLAN_five-more-items-2026-08-13.md`, the register, `docs/PROJECT_CHECKLIST.md`, and
  four archived `layoutAssigner` documents.

**OPEN-37**
- Fixed already (R09, 2026-08-10), five files: `t08_harvest_results.py:131`,
  `t17_harvest_layout_assign.py:146`, `t18:142`, `t19:150`, `t20:150`.
- **Still carrying the gap, verified at HEAD 2026-08-18 by exact string match on
  `{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end`:**
  `scripts/cluster/t07_harvest_results.py:102`, `scripts/validation/v11_nyc_centre_pipeline.py:290`,
  `scripts/validation/v12_cell_pipeline.py:354`, `scripts/validation/v12_nyc_urban_recovery.py:94`
  **and `:199`.** (The register's line numbers — 105/289/357/93/198 — are stale by 1–3 lines; the
  **string** is the anchor, not the number.)
- `scripts/cluster/t26_harvest_utci_cluster.py` is **not applicable** — it fetches UTCI rasters.

**OPEN-06**
- Population: `openubem/outputs/comparisons/open06_mislabel_population.csv` — **41 rows** + header,
  columns `cell,osm_id,gpkg_05_results_archetype_id,classifier_archetype_id_HEAD,in_open07_three,t20_status,t20_n_severe`.
- Every commit that ever touched the classifier — `git log -- openubem/semantic/building_classifier.py`
  returns exactly **six**: `6aeebb0` (2026-08-13), `0df422e` (2026-07-03), `67ede73` (2026-07-01),
  `7635ce2` (2026-06-12), `62e5968` (2026-06-09), `42f0c1d` (2026-05-06).
- The register's own framing: *"check out the classifier at successive commits … and find one that
  emits Office for these 41. If none does, the value did not come from this repository at all — and
  that is the more important answer."*

**OPEN-42**
- The six buildings and their per-mode outcome: `openubem/outputs/comparisons/open42_six_failure_causes.csv`
  (30 rows = 6 × 5 modes). All 16 failing runs die on `Temperature (low|high) out of bounds` on a
  **zone**; all six succeed under `building` mode; the five `la_rural` stems also succeed under
  `layout_assign`; `la_urban/way_402215469` fails **only** in `auto`.
- The remaining question, and the only thing standing between this item and closure: *why one zoning
  mode survives where another blows up.*
- **The artifact that can answer it exists locally and nobody has read it:** the harvested
  `eplusout.eio` carries a `Zone Information` record per zone. Manager-checked 2026-08-18 on
  `way_472960972`: **57 zones under `auto`** (e.g. `WAY/472960972_F0_PERIM1`, floor area 54.47 m²,
  volume 190.65 m³, height 3.50 m) against **1 zone under `building`** (`_F0_WHOLE`, floor area
  3 417.58 m², volume 35 884.54 m³). The failing and succeeding geometries are both on disk.

---

## 6. Tasks

### T01 — OPEN-52: establish why `--basetemp` was pinned, then remove the collision

**What.** Answer the register's blocking question — *what was the pinned path for?* — and, only if the
answer permits, remove the fixed `--basetemp` so two pytest sessions can no longer delete each other's
temporary directories.

**Why.** This defect has already corrupted one executor's report and cost the director a false
diagnosis (register §OPEN-52 and §OPEN-24's amendment). It is the one item on this plan that makes
every *other* item's test evidence trustworthy.

**How.**
1. **Establish the reason, do not assume there isn't one.** Read `git show fe05509 -- pyproject.toml`
   and that commit's message. Then search the whole repo — code, scripts, `.gitignore`, CI config,
   docs, `docs_DONE` included (reading archives is allowed; editing them is not) — for `.pytest_tmp`
   and for `basetemp`. **If any consumer depends on that literal path, STOP and report** with the
   citation; do not remove the line.
2. **Reproduce the collision first (the before leg).** In the scratchpad, write a throw-away test file
   with two tests: one that writes a file into `tmp_path`, waits ~15 s, then asserts the file still
   exists; and one trivially fast test. Run **two** pytest sessions against it concurrently, both with
   `--basetemp=.pytest_tmp` given explicitly, the second started a few seconds after the first. Record
   the exact failure. **If the collision does not reproduce, say so plainly and STOP** — the remedy is
   not justified by a mechanism that will not show itself.
3. **Apply the remedy.** Remove the `addopts` line entirely (pytest's default per-session
   `pytest-of-<user>/pytest-<n>` root is already collision-free) and keep both `tmp_path_retention_*`
   keys. If — and only if — step 1 found a real consumer of the path, STOP instead.
4. **Prove it (the after leg).** Re-run the identical two concurrent sessions, this time letting the
   repo config apply, and show both pass.

**How to test.**
- The before/after pair above, with the raw session output quoted in the FIX doc.
- `.venv/Scripts/python.exe -m pytest tests/test_sim_integration.py` **alone** → expect `7 passed`
  (~60–70 s). This is the file whose flake started the item; it must still be green, and its runtime
  must be in the 60 s range, not 12 s.
- Confirm no stray `.pytest_tmp` directory is created by the post-fix run.
- **Deliverable:** `docs/docs_ACTIVE/openings/extra/FIX_open-52_pytest-basetemp.md` — the reason the
  pin existed (or the evidence that no reason survives in the repo), the before/after transcripts, and
  an explicit statement of whether OPEN-52 can close.

### T02 — OPEN-51: adjudicate `E-LA-16`

**What.** Decide which failure signature `E-LA-16` actually names, on evidence, and correct the wrong
reading in the **live** tree only.

**Why.** OPEN-09's C06 measured that the *"cosmetic"* label is defensible for the
`CheckWarmupConvergence` class. If `E-LA-16` is not that class, C06's conclusion has been silently
extended to a cooling-coil-UA defect it never tested. One of the two readings is wrong and neither has
been retired.

**How.**
1. Read the defining entry in full — `PLAN_structural-fixes_implementation.md` around `:279` — and
   record the exact signature text, the task that minted it (T04/T05), and the three named buildings.
2. Try to reach that arc's raw `.err` evidence. Search for the run directories it cites (the arc's own
   `debug/` and `results/` trees, and any surviving temp harvest). **If the raw `.err` files are gone,
   say so** — the defining document's own quoted `** Severe **` / `** Fatal **` lines are then the
   best available evidence, and they are documentary rather than re-derived. Grade the verdict
   accordingly and do not overstate it.
3. Trace the competing reading to its origin: which document first put `E-LA-16` into the
   `CheckWarmupConvergence` list, and does it cite anything, or does it inherit the grouping from the
   code comment at `openubem/geometry/layout_assigner.py:863-865`?
4. **Decide**, and state the decision as a single sentence with its citation. Then, in the live tree
   only: correct the code comment if it is the wrong reading (comment text only — **no code change**),
   and record the adjudication in the measurement doc. **Do not renumber or split the ID.** Do not
   edit the archived documents, and do not rewrite earlier measurement docs — the register's
   append-only convention means the correction is *added*, not applied backwards.
5. State explicitly what the verdict does to **OPEN-09's C06 finding** and to **OPEN-29's** citation
   of `E-LA-16` — whether either must be narrowed, and by how much.

**How to test.** The adjudication must carry `path:line` for both readings and a verbatim quote of the
deciding text. A verdict with no quoted evidence is not acceptable. If the evidence is genuinely
ambiguous, report ambiguity — **inventing a third reading is the one forbidden outcome.**
**Deliverable:** `extra/MEASUREMENT_open-51_e-la-16-identity.md`.

### T03 — OPEN-37: close the `.eio` fetch gap at the five remaining sites, and census what is on disk

**What.** (a) Add `*/eplusout.eio` to the five tar lists that still omit it. (b) Census the local E02
harvest to establish whether the file this item is about actually came home for the corpus every
current claim rests on.

**Why.** R09 fixed five sites and deliberately left five, out of scope. The item stays open on those
five plus the historical caveat. Both halves are answerable today, locally, with no cluster.

**How.**
1. At each of the five sites (anchor on the **string**, not the line number):
   `{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end` → append ` {oid}/eplusout.eio`, matching
   the exact style already used in `t08_harvest_results.py:131`. **Five files, five insertions, five
   deletions — nothing else.** `git diff --stat` must say exactly that.
2. Syntax-check each edited file with `ast.parse`. These scripts cannot be executed without a cluster
   and **must not be** — the check is static.
3. Write `scripts/analysis/open37_eio_census.py`: walk
   `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\<cell>_<mode>\`, and per (cell, mode) emit
   `n_building_dirs, n_eio, n_eio_empty, n_sql, n_err, n_end` plus a fleet total row →
   `openubem/outputs/comparisons/open37_eio_census.csv`. Read-only: never write into the harvest tree.

**How to test.**
- The `git diff --stat` shape above, plus a `grep` proving all five sites now name `eplusout.eio` and
  that the five R09 sites are untouched.
- The census must report **60 (cell, mode) directories**; state the true `n_building_dirs` total
  against the expected 40,800 and **do not round or reconcile a mismatch away** — report it.
- A non-empty-file check: `n_eio_empty` must be reported, not assumed zero.
- **Closure recommendation, stated explicitly in the deliverable:** if all ten fetch sites now request
  `.eio` and the census is complete, say OPEN-37 can close with the historical caveat recorded as a
  permanent disposition. If the census finds gaps, say it cannot, and why.
- **Deliverable:** `extra/MEASUREMENT_open-37_eio-fetch-closure.md`.

### T04 — OPEN-06: which code state, if any, emits `Office` for the 41

**What.** Run every historical state of `building_classifier.py` over the 41 mislabelled buildings and
record what each one emits.

**Why.** Four independent sources say these buildings are hotels; only the committed `05_results.gpkg`
says office. If no version of this classifier ever emitted `Office` for them, then the column did not
come from this repository — which is a bigger finding than the mislabel itself, and it is the
measurement the register has named as the next step for months.

**How.**
1. **Read-only git only.** For each of the six commits (§5), `git show <sha>:openubem/semantic/building_classifier.py`
   into the scratchpad as `classifier_<sha>.py`. **Never `git checkout`.**
2. Build one harness that, for a given classifier module, classifies the 41 buildings from their raw
   inputs in `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`
   (the same inputs and predicate the N04 measurement used — read
   `extra/MEASUREMENT_open-06-07-11_failure-population.md` first and reuse its method rather than
   inventing a second one).
3. **Control first, results second.** Run HEAD's classifier through the harness and confirm it
   reproduces N04 exactly: 41/41, 33 `LargeHotel` + 8 `SmallHotel`. **If the control does not
   reproduce, STOP** — the archaeology is worthless without it, and reporting archaeology on a broken
   harness is the failure mode to avoid.
4. Then run each historical version. A version that cannot be imported (its era's helper modules are
   gone, its imports moved) is recorded as `NOT_LOADABLE` **with the verbatim exception text** and the
   run continues. Do not reconstruct a historical tree; do not stub imports to force a load — a forced
   load does not emit what that era's code emitted.
5. Emit `openubem/outputs/comparisons/open06_classifier_archaeology.csv`: one row per
   (commit, cell, osm_id) with `emitted_archetype`, plus a per-commit summary of how many of the 41
   came out `*Office*`.

**How to test.** The control in step 3 is the test. Beyond it: the answer must be one of exactly three
statements, chosen by the data — *(a)* a named commit emits Office for these 41, quoted with its count;
*(b)* no loadable commit does, and the loadable set covers N of 6; *(c)* too few versions load for the
question to be answered, with the exception text for each. **Do not assert (b) while several versions
sit at `NOT_LOADABLE`** — that is (c) wearing (b)'s clothes.
**Deliverable:** `extra/MEASUREMENT_open-06_classifier-archaeology.md`.

### T05 — OPEN-42: what the zoning step does to these six buildings

**What.** Extract the zone geometry EnergyPlus actually built, for the six buildings × five modes, from
the harvested `.eio`, and identify what distinguishes the runs that blew up from the runs that did not.

**Why.** This is the single question OPEN-42 still stands on. It was previously unanswerable because
it *"needs the geometry/zoning code, which a measurement task was correctly forbidden to touch"* — but
it does not: EnergyPlus reports the geometry it received, and that file came home with the harvest.

**How.**
1. Write `scripts/analysis/open42_zone_geometry.py`, read-only over the harvest. For each of the 30
   (building, mode) runs, parse the `Zone Information` records from `eplusout.eio` and emit one row per
   zone: zone name, floor area, volume, ceiling height, min/max X/Y/Z, and the derived
   `volume / floor_area` and an aspect/extent measure. Add the run's outcome by joining
   `open42_six_failure_causes.csv` on (cell, stem, mode).
2. For each failing run, pull the **zone named in its own `Temperature (low|high) out of bounds`
   Severe** out of `eplusout.err`, and compare that zone's geometry against the other zones of the same
   run. Is the blow-up zone the degenerate one, or an ordinary one?
3. **Background control — required.** Compute the same per-zone statistics for a sample of at least 20
   **successful** buildings in the same two cells and the same modes. Without it, "these zones are
   unusual" cannot be said. State how the sample was chosen.
4. Report a mechanism **only if the data carries it**: name the statistic, the threshold, and how many
   of the 16 failing runs it separates from how many of the 14 succeeding ones. If the `.eio` does not
   separate them, say so — *"not determinable from `eplusout.eio`"* is an acceptable and useful result,
   and is far better than a plausible story.

**How to test.** The control in step 3 is the test: any claimed distinguishing feature must be shown to
be **absent** (or much rarer) in the successful background sample, with counts. Row-count check: 30
runs, every one present or explicitly accounted for. **No fix, no code change, no simulation** — this
is diagnosis only, per the diagnose-before-remediate rule.
**Deliverable:** `extra/MEASUREMENT_open-42_zoning-mechanism.md` +
`openubem/outputs/comparisons/open42_zone_geometry.csv`.

### T06 — bookkeeping: register, checklist, director prompt, full suite

**What.** Write all five outcomes into the register, update the two tracking surfaces, and run the full
test suite alone.

**How.**
1. **Register** (`INVESTIGATION_open-items-register.md`): per item, amend its own §-section with a
   dated block (never delete superseded text — strike it), update its §1 table row, and for anything
   that closes, strike the row and retire the ID.
2. **🔴 The count rule, which this arc has got wrong three passes running.** Recount the table
   **programmatically** (`grep -c` over the table's rows, struck vs live) **and** re-derive the
   retired-ID total from the struck-header lineage — **never from the trailing parenthetical, which
   has been stale since 2026-08-13.** Baseline going in: **28 live / 24 struck / 52 total, 22 IDs
   retired**, and the reconciliation sentence *"24 struck rows but 22 retired IDs; the difference of
   exactly 2 is OPEN-02 and OPEN-28, folded under OPEN-01's umbrella and never independently
   tracked"* must survive in the header.
3. **`docs/PROJECT_CHECKLIST.md`** — the user's monitoring surface; reflect the new state.
4. **Director prompt** — append this plan's outcome to **§5.18** and refresh the RESUME box at the head
   so the next session reads the true state. **Re-read the file immediately before writing**: the
   director may have edited §5.18 while you worked. One surgical insertion, never a rewrite.
5. **Full suite, alone, nothing else running:** `.venv/Scripts/python.exe -m pytest -q`. Baseline to
   measure against is **1875 passed / 55 skipped / 0 failed** (2026-08-17). Report the raw counts and
   account for every difference by name. `Windows fatal exception: access violation` lines are known
   pre-existing joblib/loky noise from `test_sim_integration.py::test_synthetic_fleet_full_annual` —
   **exactly 7 of them** in each of the last three full-suite logs. A different count is a finding.

**How to test.** The programmatic recount is the test for §1; the suite counts are the test for the
code. Both raw numbers go in the progress log, not a summary of them.

---

## 7. Stop-and-report points

- **CP-1 — after T02.** Report: OPEN-52's reason-for-the-pin finding and the before/after concurrency
  transcripts; OPEN-51's verdict with its quoted evidence; `tests/test_sim_integration.py` alone.
  **Do not start T03–T05 before the director signs CP-1** — every later task's test evidence depends
  on T01 being right.
- **CP-2 — after T05.** Report: the five-site diff and the `.eio` census totals; the archaeology
  control plus the per-commit table; the zoning statistic with its background control. Three closure
  recommendations, each a yes or a no with a reason.
- **CP-3 — after T06, final.** Report: the programmatic register recount, the retired-ID lineage
  arithmetic, and the full-suite counts against the 1875/55/0 baseline.

---

## 8. Progress log

*One entry per completed task, appended by the executor as each lands. Required shape:*
`#### TXX — <title> — completed YYYY-MM-DD` *then* **Artifacts** / **Deviations** / **Test status** /
**Notes**.

#### T01 — OPEN-52: establish why `--basetemp` was pinned, then remove the collision — completed 2026-08-18

- **Artifacts:** `docs/docs_ACTIVE/openings/extra/FIX_open-52_pytest-basetemp.md`. `pyproject.toml` is
  **byte-identical to its pre-task state** (edited, tested, reverted — see Deviations).
- **Deviations:** (1) Step 1 (search for a documented reason) found none — the commit that added the
  pin (`fe05509`) and the same-day plan progress-log entry (`docs/docs_main/docs_step-2-1/PLAN_step-2-1-implementation.md:263`)
  both list the addopts line as an artifact with no stated rationale, and no code/CI/fixture reads the
  literal `.pytest_tmp` path. (2) Step 2's literal reproduction recipe (write a file, sleep 15s, assert
  it exists) did **not** surface a failure in two attempts, despite directory census proving the wipe
  fired both times (a single `test_slow_writer0` directory instead of two). A third, busy-loop design
  (continuous writes, no sleep) **did** catch a hard failure: session B got
  `FileExistsError: [WinError 183]` cascading from an `OSError [WinError 145] directory not empty`
  inside pytest's own `rm_rf`. Collision reproduced, different failure signature than the register's
  original incident, same root cause. (3) Step 3's remedy (delete `addopts`) was applied, but the
  after-leg concurrency proof required a `TEMP`-redirect workaround, because this machine's default
  pytest temp root (`C:\Users\o_iseri\AppData\Local\Temp\pytest-of-o_iseri`, dated Apr 1, predating
  this session) is **currently access-denied** — `PermissionError [WinError 5]`, confirmed even to
  `icacls` run directly against it. With `TEMP` redirected, two concurrent sessions passed cleanly
  into separate `pytest-0`/`pytest-1` directories, proving the remedy is mechanically correct. But
  **without** the redirect (i.e. a normal invocation on this machine), `tests/test_sim_integration.py`
  alone gave `1 passed, 6 errors` (all `PermissionError` on `pytest-of-o_iseri`), not the required
  `7 passed`. This is a real, currently-active reason a fixed repo-relative basetemp is useful on this
  box (it was incidentally shielding every `tmp_path` test from this unrelated OS lockout), even though
  no one wrote that reason down in 2026-06-10. `pyproject.toml` was therefore **reverted** to its
  original content — the remedy cannot be safely applied as a bare line deletion on this machine.
- **Test status:** `tests/test_sim_integration.py` alone, with the repo restored to its original state:
  **7 passed in 67.14s**, re-run once more for a second data point: **7 passed in 68.08s** — matching
  the register's four prior sequential 60-70s runs, not the 12.67s flake shape. No stray `.pytest_tmp`
  left behind.
- **Notes:** OPEN-52 does not close. See FIX doc §6 for the full disposition: two sub-questions now
  open, (a) the original collision (real, reproduced) and (b) the newly-found `pytest-of-o_iseri`
  lockout, which blocks (a)'s specified remedy and needs either ACL repair or a different remedy shape
  — a design choice outside this task's authority. Only one pytest session ran at a time except the
  deliberate, torn-down-after-use concurrency experiments in this task (hard rule 3).

#### T02 — OPEN-51: adjudicate `E-LA-16` — completed 2026-08-18

- **Artifacts:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-51_e-la-16-identity.md`;
  `openubem/geometry/layout_assigner.py:865` (comment text only — `E-LA-16` removed from the ID list,
  a 4-line pointer to the measurement doc added; `git diff --stat` shows only comment lines touched;
  `ast.parse` confirms the file still parses).
- **Deviations:** none from the plan's method. The arc's own raw `.err` evidence for the three named
  buildings (`way/402036176`, `way/402036789`, `way/1395739331`) is gone from this machine (searched
  exhaustively under `docs/docs_DONE/SETUP/layoutAssigner/` — none of the 57+ local `eplusout.err`
  files belong to these buildings) — per the plan's contingency, the defining document's quoted text
  was the fallback. Independent corroborating evidence was then found and used: the same three building
  IDs exist in the current local E02 harvest (`la_urban_layout_assign` mode), and their raw
  `eplusout.err` files show 0 `CheckWarmupConvergence` hits, 0 `CheckAirLoopFlowBalance` hits, and
  23/21/16 Severes respectively (corrected 2026-08-18/T06 — the original 26/24/19 count wrongly
  included each file's 3 trailing `Error Summary` lines, which contain the word "Severe" but are not
  `** Severe **` fault lines; corrected counts match each file's own final summary line exactly and do
  not change the verdict), all `Calculation of cooling coil design UA failed` — matching the
  defining text exactly and directly contradicting the code comment's grouping. Graded as
  documentary-plus-corroborating, not a byte-identical re-derivation of the original run (one
  discrepancy noted and reported, not smoothed over: this harvest shows 0 Fatal where the original text
  reported a cooling-tower-UA-autosize Fatal for two of the three buildings, most likely a run-config
  difference, not a mechanism difference).
- **Test status:** n/a (measurement/documentary task). The decisive check was the `.err` grep in §3 of
  the measurement doc; the syntax check on `layout_assigner.py` (`ast.parse`) passed.
- **Notes:** Decision — E-LA-16 is the cooling-coil-design-UA-failed/cooling-tower-UA-autosize-failed
  family (`PLAN_structural-fixes_implementation.md:279`); the code comment's grouping with
  `CheckWarmupConvergence`/`CheckAirLoopFlowBalance` was a documentation error (an imprecisely recalled
  ID list in an unrelated comment, added 4 days later by a different commit documenting a different
  6-run experiment that never touched E-LA-16's own buildings), now corrected. **Effect on OPEN-09's
  C06:** its "five inherited log entries" list narrows to four (E-LA-14, E-LA-18, E-LA-19, E-LA-23) —
  E-LA-16 does not belong and its own accuracy impact remains untested. **Effect on OPEN-29:** none —
  both OPEN-29 measurement docs already used the defining-text reading for their own verdicts and had
  already flagged this exact contradiction as unresolved (`extra/MEASUREMENT_open-29_eight-defect-recheck.md:71-82`);
  this task resolves the question they deliberately left open. `docs_DONE/` was not touched.

#### T03 — OPEN-37: close the `.eio` fetch gap at the five remaining sites, and census what is on disk — completed 2026-08-18

- **Artifacts:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-37_eio-fetch-closure.md`;
  `scripts/analysis/open37_eio_census.py`; `openubem/outputs/comparisons/open37_eio_census.csv`; the
  five edits in `scripts/cluster/t07_harvest_results.py:102`,
  `scripts/validation/v11_nyc_centre_pipeline.py:290`, `scripts/validation/v12_cell_pipeline.py:354`,
  `scripts/validation/v12_nyc_urban_recovery.py:94` and `:199`.
- **Deviations:** none. All five pre-edit sites matched the plan's cited string exactly at the cited
  lines; `git diff --stat` came back exactly 5 insertions / 5 deletions across the 4 files (two edit
  sites live in the same file); `ast.parse` passed on all four edited files (not executed — no
  cluster). The five R09 sites were re-verified as already carrying `.eio` and untouched (the plan's
  `t18/t19/t20` citations were matched to the actual filenames `t18_harvest_layout_assign.py` etc.,
  since no `_r09`-suffixed files exist).
- **Test status:** `git diff --stat` shape confirmed as required; grep confirmed all five edited sites
  plus all five R09 sites name `eplusout.eio`; census script run once, read-only, against the local
  harvest.
- **Notes:** Census found **60 (cell, mode) directories** as expected (3 cities × 4 sub-cells × 5
  modes), **40,800 `n_building_dirs`** matching the expected total exactly, **40,800 `.eio` files with
  0 empty**, and **`.err` also at 40,800**. `.sql` and `.end` are short (39,926 and 39,925
  respectively) — reported, not reconciled away — concentrated almost entirely in
  `austin_suburban_fast_zone`/`austin_suburban_floor` (874 of the 875-count gap) plus one
  `nyc_centre_fast_zone` directory; these directories still have `.eio` and `.err` present, so this is
  an incomplete-simulation signature, not an `.eio`-fetch gap, and is out of OPEN-37's scope.
  **Closure recommendation: OPEN-37 can close** — all ten fetch sites now request `.eio`, and the local
  corpus census finds zero `.eio` gaps and zero empty `.eio` files; the historical caveat for
  pre-fix harvests is recorded as a permanent disposition.

#### T04 — OPEN-06: which code state, if any, emits `Office` for the 41 — completed 2026-08-18

- **Artifacts:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_classifier-archaeology.md`;
  `scripts/analysis/open06_classifier_archaeology.py`;
  `openubem/outputs/comparisons/open06_classifier_archaeology.csv` (246 rows: 41 buildings × 6
  commits); scratchpad `classifiers/classifier_<sha>.py` for the five non-HEAD commits (read-only
  `git show`, never checked out).
- **Deviations:** (1) First harness draft classified only the 41-row population subset per cell, not
  the full cell; this changed 2/41 results (`austin_centre way/231123149`, `way/328723692`) because
  `GROUPMEDIAN_LEVELS_MED` levels-imputation is batch-dependent, and the control (step 3) failed as a
  result (31 LargeHotel/10 SmallHotel instead of N04's 33/8). Corrected to classify the full cell
  (matching N07's own full-198-row method) before filtering to the population; control then reproduced
  N04 exactly. Reported as a finding per hard rule 12, not silently fixed. (2) All six historical
  module versions resolve their data-file imports (`osm_to_use_class.json`,
  `openstudio_archetypes.json`) via `importlib.resources` against the **currently-installed** package
  data, not each commit's own data files — `git log` shows those two data files were touched only at
  `42f0c1d` and `67ede73`, so the three commits between them (`62e5968`, `7635ce2`, and `42f0c1d`
  itself) ran their era's code against today's (post-`67ede73`) data. Disclosed in the deliverable as a
  caveat on those three commits' exact-count columns; does not affect the decisive finding, which rests
  on `67ede73` and `0df422e` (both post-dating the last data-file change).
- **Test status:** Control (step 3) reproduced N04 exactly after the fix in (1): 41/41, 33
  `LargeHotel` + 8 `SmallHotel`. All six commits loaded successfully — zero `NOT_LOADABLE`, zero
  `CLASSIFY_ERROR` — so the answer is category (a), not (b) or (c).
- **Notes:** **Decisive finding: commit `67ede73` (2026-07-01) reproduces the committed
  `05_results.gpkg` archetype exactly for all 41 buildings** — not merely "Office family" but the
  exact `SmallOffice`/`MediumOffice`/`LargeOffice` subtype recorded per building (41/41 exact match).
  The sole diff between `67ede73` and `0df422e` (2026-07-03) on `building_classifier.py` is the Hotel
  rule (`RULE_LODGING_TIER`) gaining a `building_tag` check it previously lacked — at `67ede73` it read
  `function_tag` only, and all 41 buildings have `hotel`/`motel` in `building_tag` with `function_tag`
  blank, so they fell through to an Office rule. The T11 fleet fan-out that produced the committed file
  ran 2026-07-01 23:14 → 2026-07-02 22:07 — after `67ede73` landed (07-01 20:14) and entirely before
  `0df422e` landed (07-03 10:53, >12h after the fan-out finished) — so the fan-out necessarily ran
  under the pre-fix classifier; `0df422e`'s commit bundled the fix together with promoting the
  already-generated (pre-fix) results. This resolves N07's open provenance gap
  (`MEASUREMENT_open-06_archetype-writer-trace.md` §5): the value did come from this repository's
  classifier, just from `67ede73`, not the commit N07 checked. `docs_DONE/` was not touched; only
  read-only git commands were used to view historical states.

#### T05 — OPEN-42: what the zoning step does to these six buildings — completed 2026-08-18

- **Artifacts:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_zoning-mechanism.md`;
  `scripts/analysis/open42_zone_geometry.py`;
  `openubem/outputs/comparisons/open42_zone_geometry.csv` (1,011 rows: 411 target zone rows across the
  30 runs + 600 background zone rows across 100 runs, 20 background buildings).
- **Deviations:** none from the plan's method; the finding is weaker than the plan's framing hoped for
  (see Notes) and is reported as such rather than oversold. Two candidate statistics were tried and
  both were disproved by the required background control before being reported as ruled out, not
  reported as findings.
- **Test status:** Row-count check passed (30/30 target runs had zones parsed, no missing runs).
  Background control required by plan step 3: 20 buildings (10 `la_rural` + 10 `la_urban`, succeeding
  in all 5 modes) — met, and it did its job: it disproved both candidate statistics before they could
  be reported as a mechanism.
- **Notes:** **Is the blow-up zone degenerate or ordinary? Ordinary, 15/16.** All 5 `la_rural`
  buildings fail on the topmost floor's zone in each of the 3 per-floor-zoned modes (`auto`,
  `fast_zone`, `floor`); that zone's floor area/volume/ceiling-height/extents are byte-identical to
  its own non-fatal sibling zones one and two floors below in the same run (e.g. `way_472960972`'s
  `_F0_CORE`/`_F1_CORE`/`_F2_CORE` all report floor area 2,221.44 m², volume 7,775.03 m³ — only `_F2`
  fails). Only its position (topmost floor, roof-adjacent, no zone above) differs. The 1 exception
  (`la_urban/way_402215469/auto`, fails on `_F3_WHOLE` of 6 floors, not the top `_F5`) has instead a
  **uniform, whole-run Volume anomaly** (every zone reports `Volume=10.00 m³` regardless of floor
  area, vs. ~4,128.73 m³ that Floor Area × Ceiling Height implies, and vs. what the same building's
  own succeeding `fast_zone`/`floor` modes correctly report). **This looked like a mechanism and was
  disproved by the background control:** 12 of the 20 background buildings (60%) show the exact same
  uniform-Volume=10.00-in-auto-mode signature and all 12 succeed — ruled out, reported as ruled out.
  A looser per-zone volume-consistency threshold and raw zone size/aspect-ratio statistics were also
  tested and also failed to separate the 16 failing from the 14 succeeding runs (background rates
  nearly identical to target rates: 34% vs 40% for the volume-consistency check; most fatal zones sit
  inside the background's own size/aspect-ratio range). **Verdict, stated in the plan's own permitted
  terms: the positional pattern (topmost floor, 15/16) is real and evidenced, but `eplusout.eio` does
  not carry a field that explains why THESE six buildings' topmost zones are unstable while 20
  background buildings' topmost zones are not — "not determinable from eplusout.eio" for that deeper
  question.** Connected (not re-derived) to OPEN-11: all six are the same six inverted-geometry
  buildings N04 already identified; a per-surface winding/orientation defect (not visible in `Zone
  Information`, which only ever reports zone-level aggregates) is named as the most likely next
  artifact to check, out of this task's `.eio`-only scope. **Closure recommendation: OPEN-42 sharpens,
  does not close.** No fix, no code change, no simulation — diagnosis only.

#### T06 — bookkeeping: register, checklist, director prompt, full suite — completed 2026-08-18

- **Artifacts:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` (amended: OPEN-06,
  OPEN-37, OPEN-51 closed + retired with dated blocks in their own §-sections and struck §1 rows;
  OPEN-52 and OPEN-42 sharpened with dated blocks, §1 rows updated in place; OPEN-09's C06 narrowed to
  four inherited entries; new item **OPEN-53** opened with its own §10 section and §1 row; §1 header
  recounted and extended; "Next free item ID" advanced to `OPEN-54`); `docs/PROJECT_CHECKLIST.md`
  (dated summary entry appended at the end of the file); `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`
  (one entry appended to the end of §5.18; no other edit to that file by this task); this plan's own
  §8, T02's entry corrected in place, this T06 entry added.
- **Deviations:** none from the plan's method. Two corrections applied exactly as specified: (1) the
  OPEN-51 measurement doc's Severe counts (26/24/19 → **23/21/16**, with a one-line note that the
  original `grep -ic "Severe"` also matched each `.err` file's 3 trailing `Error Summary` lines) —
  fixed in both `extra/MEASUREMENT_open-51_e-la-16-identity.md` and this plan's own T02 progress-log
  entry; (2) the `.sql`/`.end` shortfall (874/875, `austin_suburban_fast_zone`/`austin_suburban_floor`
  plus one `nyc_centre_fast_zone`) given its own new register item, **OPEN-53**, rather than folded
  into OPEN-37. Mid-task, the coordinator flagged one wording slip in the register header's new
  2026-08-18 clause ("both closures" where three items closed) — corrected to "all three closures" in
  place, verified as the only occurrence via a whole-string count before replacing.
- **Test status — the count rule (recount script, run twice: once before the wording fix, once after,
  identical both times):**

  ```
  Total data rows found: 53
  Live rows: 26
  Struck rows: 27
  Total: 53
  Missing IDs (expected but not in table): []
  Extra/unexpected IDs: []
  Duplicated IDs: []

  Struck IDs: OPEN-01, OPEN-02, OPEN-04, OPEN-05, OPEN-06, OPEN-21, OPEN-22, OPEN-23, OPEN-24,
  OPEN-25, OPEN-26, OPEN-28, OPEN-30, OPEN-31, OPEN-32, OPEN-33, OPEN-34, OPEN-36, OPEN-37, OPEN-39,
  OPEN-40, OPEN-41, OPEN-43, OPEN-44, OPEN-45, OPEN-50, OPEN-51 (27)

  Live IDs: OPEN-03, OPEN-07, OPEN-08, OPEN-09, OPEN-10, OPEN-11, OPEN-12, OPEN-13, OPEN-14, OPEN-15,
  OPEN-16, OPEN-17, OPEN-18, OPEN-19, OPEN-20, OPEN-27, OPEN-29, OPEN-35, OPEN-38, OPEN-42, OPEN-46,
  OPEN-47, OPEN-48, OPEN-49, OPEN-52, OPEN-53 (26)
  ```

  Table body = lines 635-688 of the register (header at 633, separator at 634), extracted and
  classified by whether the ID cell begins with `~~`. **26 live / 27 struck / 53 total, exactly
  OPEN-01…OPEN-53, no row missing, none duplicated** — matches the plan's stated arithmetic
  (28 live minus 3 closed plus 1 opened = 26; 24 struck plus 3 newly struck = 27; 52 total plus 1 new
  ID = 53) exactly. **Retired-ID lineage:** baseline 22 retired IDs going in; this pass retires three
  more (OPEN-06, OPEN-37, OPEN-51) giving **25 retired IDs**. Reconciliation: 27 struck minus 25
  retired = **2**, unchanged from baseline — still exactly OPEN-02 and OPEN-28, folded under OPEN-01's
  umbrella and never independently tracked (all three of this pass's closures retired an ID that was
  also a struck row already, one-for-one, so the gap neither widened nor narrowed). Script:
  scratchpad `open53_recount.py` (session scratchpad, not committed to the repo per hard rule).

  **Full suite, alone, nothing else running:** `.venv/Scripts/python.exe -m pytest -q` (no path
  argument, run once, not repeated) gives
  **`36 failed, 1918 passed, 55 skipped, 11 warnings, 17 errors in 1544.83s (0:25:44)`**.
  No `xfailed`/`xpassed` present. `skipped` matches the 1875/55/0 baseline exactly (55 = 55).
  `Windows fatal exception: access violation` counted **exactly 7**, matching the expected joblib/loky
  noise from `test_sim_integration.py::test_synthetic_fleet_full_annual`, not a different count.

  **Accounting for every non-passing result by name:** all 36 failed plus 17 errors are pre-existing,
  long-committed test files, none touched or created by this plan's T01–T06. **35 failed plus 17
  errors** are under `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` (`test_elevators.py`,
  `test_outputs.py`, `test_results_aggregator.py`, `test_step3_orchestrator.py`), tracked since commit
  `ef19141`, an old commit well predating this plan, and off-limits to edit under this plan's hard
  rules. **1 failed** is `scripts/analysis/test_viewer_layout_assign.py::test_layout_assign_idf_ingestion`,
  tracked since commit `69373f9`, also outside this plan's file layout. This exact failure population
  matches a whole-tree run already on record in `docs/PROJECT_CHECKLIST.md` (`1910 passed, 35 failed,
  55 skipped, 17 errors`, "51 missing IDF template plus 1 `zones_found` NameError", filed under
  OPEN-44's rider that only `tests/`-scoped runs are guaranteed green, not the bare repo-root
  `pytest -q`) — a standing, previously-documented condition, not something this pass introduced.
  🔴 **This directly contradicts the CP-2 sign-off recorded 2026-08-17** in the director prompt
  (§5.16, quoting `1875 passed, 55 skipped, 0 failed, 11 warnings, 1650.61s` from the same bare
  command on a tree where `ef19141` and `69373f9` were already old, committed history, so those files
  should have been collected and failing then too, on the evidence available). `pyproject.toml` is
  unmodified (`git diff` empty, absent from `git status`), so no collection-scope change in that file
  explains the gap. **Not reconciled here** — the suite was not re-run a second time (explicit
  instruction not to), so whether the 2026-08-17 report was scoped differently than its own text
  states, read from a different or truncated log, or something else, cannot be determined from a
  single log file. Reported as an open contradiction, not smoothed over.
  **`passed`: 1918 vs. the 1875 baseline is +43.** No `tests/` file was created or edited by T01–T06 of
  this plan (T01–T05's own edits were `pyproject.toml`, reverted; `openubem/geometry/layout_assigner.py`
  comment-only; and four cluster/validation scripts' tar-list strings — zero test files). The
  pre-existing dirty tree at the start of this whole session already carried uncommitted changes to
  `openubem/results/aggregator.py`, `openubem/results/parser.py`, `tests/test_results_aggregator.py`,
  `tests/test_semantic_unknown_draw.py`, plus a new untracked `tests/test_results_denominator.py` —
  all present before this plan's T01 ever ran and outside this plan's authorised file set (§3). These
  are the only candidate source of the +43, but the exact figure is not fully attributable from a `-q`
  log alone (no per-test pass list at this verbosity) without a further pytest invocation, which was
  not run. **Stated plainly per hard rule 12: the passed-count delta is not fully accounted for by
  name; it is bounded to files outside this plan's own edits, but the precise reconciliation is not
  established.**
- **Notes:** `pyproject.toml` confirmed byte-identical to HEAD throughout this task (`git diff` empty,
  absent from `git status`) — the `--basetemp=.pytest_tmp` line was never touched by T06. No git write
  command (`add`/`commit`/`restore`/`checkout --`/`stash`/`reset`/`clean`) was run at any point in this
  task; only `git log`, `git show`, `git diff`, `git status` were used. `docs/docs_DONE/`, `docs_main/`,
  `docs_stepN/`, root `main.py`, and all OVERVIEW/DESIGN docs were not touched. Only one pytest session
  ran, alone, for the full-suite invocation above; no other pytest process was started concurrently.
