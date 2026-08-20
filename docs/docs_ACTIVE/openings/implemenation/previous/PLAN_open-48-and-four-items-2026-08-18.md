# PLAN — OPEN-48 and four more items — 2026-08-18 (late)

**Slug:** `open-48-and-four-items-2026-08-18`
**Written:** 2026-08-18 (late), by the director, at the user's instruction *"continue jusqu'a la fin pour des taches ouverts vas-y, executer"*.
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`
**Director's log:** `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` §5.21
**Predecessor:** `PLAN_open-52-and-four-items-2026-08-18.md` (CP-3 signed, closed)

---

## 1. Why these five

Same heuristic as the three preceding passes, and it supplied the whole slate again: **hunt for a
stale blocker** — a register sentence saying "cannot be measured because X" or asserting a fact about
the live tree, where X has since become false. All five qualify. **None was picked because it looked
interesting.**

| Task | Item | The stale premise |
|---|---|---|
| T01 | **OPEN-48** | Its entire evidence table describes a live tree in which `assign_elevators` is not called from `builder.py`. Ruling `2d` wired it on 2026-08-13 (commit `6aeebb0`). **Every row of that table is now out of date.** |
| T02 | **OPEN-51** | Not stale but self-specified: the item's own *"What would settle it"* names a cheap, local, documentary check that nobody has run. OPEN-29's T04 (2026-08-18) proved the defect is unpatched, so the ID collision still matters. |
| T03 | **OPEN-13** | Says *"a bare `pytest -q` aborts at collection"* and *"the whole suite has not been runnable as a whole."* Both false at HEAD: the suite collects 1930 and returns 1875 passed / 55 skipped / exit 0. |
| T04 | **OPEN-47** | Its *"Reason 1 it stays open ... Not adjudicated"* is false. `building_classifier.py:170-181` carries a **user ruling of 2026-08-12** on exactly that divergence, with a measured impact and a named flag. The register never absorbed it. |
| T05 | **OPEN-12** | Carries two unreconciled numbers side by side (36.4% / 19.2% vs 100%) under an explicit no-adjudication rule. The UTCI arc's own dataset — the one place the original numbers could come from — has never been checked. |

---

## 2. Hard rules for the executor

1. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, anything under `docs/docs_DONE/`,
   `docs/docs_main/`, or `docs/docs_stepN/`. These are read-only specs.
2. **No `.py` file under `docs/`, ever.** Analysis scripts go in `scripts/analysis/`.
3. **No git write commands.** No `add`, `commit`, `restore`, `checkout`, `stash`, `push`, `clean`.
   Read-only git (`log`, `show`, `diff`, `status`, `grep`, `blame`) is expected and encouraged.
4. **No cluster.** Nothing in this plan touches Speed. No `sbatch`, no `ssh`.
5. **No live-network integration tests** (§5.3 is still blocked).
6. **This is a measurement pass. Do not fix anything.** If a task's finding implies a remedy, write
   the remedy down as a recommendation and stop. Diagnose before remediate.
7. **Re-derive; never inherit a number.** Every figure you report must come from a command you ran in
   this task. If you quote a prior number, label it as quoted and say where it came from.
8. **Run your own control.** A detector that finds nothing must first be shown to find something.
   State what your positive control was; a null with only a negative control is worthless.
9. **Register pen:** only **T01** may edit the register directly. **T02–T05 must NOT touch it.** Each
   writes a `## Register amendment to apply` section at the end of its own measurement doc; the
   director places it. This exists to stop concurrent-write corruption.
10. **Windows paths in edit scripts:** use raw strings (`r'C:\...'`) or forward slashes. A `\t` in a
    non-raw string silently writes a TAB into a doc.
11. **Use `.venv\Scripts\python.exe`**, never bare `python` (it resolves to the Store shim).
12. **Stop and quote the conflict** on any spec ambiguity. Never invent.
13. **Do not propose alternatives to this plan. Execute it.**

---

## 3. File layout

| Task | Measurement doc (new) | Script (new) | Output (new) |
|---|---|---|---|
| T01 | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-48_reproducibility-retest.md` | `scripts/analysis/open48_reproducibility_retest.py` | `openubem/outputs/comparisons/open48_reproducibility_retest.csv` |
| T02 | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-51_ela16-provenance.md` | — (documentary; grep/git only) | — |
| T03 | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_eutci12-residual.md` | `scripts/analysis/open13_eutci12_residual.py` | `openubem/outputs/comparisons/open13_eutci12_residual.csv` |
| T04 | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-47_floorcount-divergence.md` | `scripts/analysis/open47_floorcount_divergence.py` | `openubem/outputs/comparisons/open47_floorcount_divergence.csv` |
| T05 | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_height-residual-retrace.md` | `scripts/analysis/open12_height_residual_retrace.py` | `openubem/outputs/comparisons/open12_height_residual_retrace.csv` |
| T06 | — | `scripts/analysis/open_register_recount_2026-08-18.py` (**exists — reuse, do not rewrite**) | — |

Progress log: **§8 of this file.**

---

## 4. Dependency decisions (pinned)

- Python: `.venv\Scripts\python.exe` (CPython 3.14, uv-managed).
- pytest **9.0.3**. `[tool.pytest.ini_options]` now carries `testpaths = ["tests"]` and **no
  `addopts`**; the repo-root `conftest.py` sets `PYTEST_DEBUG_TEMPROOT` to `<repo>/.pytest_tmp`
  (commit `da6eed7`, OPEN-52).
- 🟢 **Concurrent pytest sessions are now SAFE.** The arc's old "one pytest session at a time,
  repo-wide" rule is **lifted** — OPEN-52's remedy numbers each session (`pytest-0`, `pytest-1`, …).
  You still should not run the full suite twice at once for CPU reasons, but it is no longer unsafe.
- Suite baseline, and the only acceptable command: `.venv\Scripts\python.exe -m pytest -q tests/`
  → **1875 passed, 55 skipped, 11 warnings**, 1930 collected, ~17 min.
  A bare root-level `pytest` is **not** the baseline.
- Pandas / geopandas as already pinned in `pyproject.toml`. Do not add a dependency.
- **The E02 artifact corpus is eroding under a process outside this repository.** An external sweep on
  2026-08-17 16:21 deleted every E02 `.sql`/`.end` in two Austin sub-cells **and emptied the entire
  IDF corpus**. If a task needs a `%LOCALAPPDATA%` artifact, **verify it is on disk before planning
  around it** — never cite `e02_corpus_inventory.csv` as current state.

---

## 5. Facts with citations — read these before starting

Every line below was verified by the director on 2026-08-18. **They are the starting point, not the
answer.** ⚠️ **Two director leads in the last pass were refuted by the tasks built to test them. A
lead written here is a hypothesis. Build the task to disprove it, and say so plainly when it dies.**

**OPEN-48 (register `INVESTIGATION_open-items-register.md:4974`).**
- `openubem/idf/builder.py:40` — `from openubem.idf.elevators import assign_elevators`
- `openubem/idf/builder.py:609` — `assign_elevators(self.idf, row, extruded_zones)`
- `openubem/idf/outputs.py:43` — `"Elevators:InteriorEquipment:Electricity"` meter requested
- `openubem/results/aggregator.py:41` — `"elevators_eui_kwh_m2"`; `:53` — `"gwp_elevators_kgco2_m2"`
- `openubem/results/carbon.py:98` — `elevators_eui = _safe("elevators_eui_kwh_m2", 0.0)`
- The register's table asserts **"no"**, **"absent at HEAD"** and **"zero objects"** for all of these.

**OPEN-51 (register `:5243`).** Four sources, two readings, neither retired:
`docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:279`
(cooling-coil-UA family) vs `implemenation/previous/PLAN_compute-queue.md:343`,
`extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md:116`, and
`openubem/geometry/layout_assigner.py:863-865` (all `CheckWarmupConvergence`).

**OPEN-13 (register `:4033`).**
- `grep -c "_draw_tier" openubem/semantic/imputation.py` → **0**, still true today.
- `tests/test_draw_methods.py:42-43` carries an explicit `# OPEN-13 / OPEN-17 / OPEN-36` comment
  saying the router wiring has never been implemented.
- But the suite runs clean. **So the defect is contained, not fixed** — and the register's stated
  consequence ("the whole suite has not been runnable") is what is stale, not the defect itself.

**OPEN-47 (register `:4730`).**
- `openubem/semantic/building_classifier.py:168-181` — the source's rule is quoted verbatim in a
  comment, then: *"OPEN-47 ruling (user, 2026-08-12, plan §1.2): keep area-only as the default; the
  floor-count half above is deliberately NOT applied by default -- deferred, not rejected."*
- The comment cites **598 buildings** whose archetype changes under the floor-count bound, of which
  only **85 (14.2%)** rest on an OSM-observed floor count; 57.9% `HEURISTIC_HEIGHT`, 27.9%
  `GROUPMEDIAN_LEVELS_MED`. A `use_floor_count` flag exists, default OFF.

**OPEN-12 (register `:3990`).** `nyc_rural` 36.4% vs 100.00% (198/198); `austin_rural` 19.2% vs
100.00% (245/245); `nyc_suburban` 100.00% (1,589/1,589), never named by the item. Fleet-wide
2,806 / 8,160 = 34.39%. Zero present-but-zero heights fleet-wide.

---

## 6. Tasks

### T01 — OPEN-48: re-test reproducibility against the live tree

**What.** Re-derive **every row** of OPEN-48's evidence table against HEAD, and answer the item's own
one-line finding — *"running the pipeline from the current tree would produce different numbers and a
missing column"* — as a yes/no with evidence.

**Why.** The table was assembled on 2026-08-12. Ruling `2d` wired `assign_elevators` into `builder.py`
the next day and it is committed at `6aeebb0`. OPEN-48 is the largest provenance item in the register
and it is being carried on evidence that is a week out of date. **This is the biggest single thing the
register currently gets wrong, if it is wrong.**

**How.**
1. Re-run each of the five table rows as a live check and record the command and its raw output:
   `git log --all -S assign_elevators -- openubem/idf/builder.py`; `hasattr(builder, 'assign_elevators')`;
   the count of `"elevator"` in `builder.py`; the presence of both columns in the aggregator's schema;
   the meter in `outputs.py`.
2. **Build one building live and count the emitted elevator objects.** This is the row that matters —
   the others are static. Pick an elevator-eligible archetype, build through the live `builder.py`, and
   count `ElectricEquipment` objects whose `EndUse_Subcategory` is `Elevators`. Report the count and
   the archetype. If you cannot build without network or cluster, say so and fall back to
   `tests/test_builder_elevators_wired.py` — but **say which you did.**
3. Separate the two halves the item itself separates: the **reporting** half (parser / outputs /
   carbon / aggregator) and the **load-wiring** half (`builder.py` emitting objects). State the status
   of each independently.
4. Then answer the provenance question directly: **can the adopted `phaseE_elevrb` run now be
   regenerated from version control?** If not, name precisely what is still missing. Do not assume the
   answer is yes just because the wiring is back — check whether anything else in that run's
   configuration is uncommitted.
5. **Control:** before believing any "absent at HEAD" result, verify your detection method finds a
   symbol you know IS present. State it.

**How to test.** Every claim carries the command that produced it and its verbatim output. The
live-build count is a real number from a real build, not a test's assertion.

**Register:** T01 holds the pen. Amend OPEN-48 in place — **strike, never delete** — and if the
finding changes OPEN-48's status, say so explicitly rather than implying it.

---

### T02 — OPEN-51: settle which defect `E-LA-16` names

**What.** Execute the item's own *"What would settle it"*: read the structural-fixes arc's original
`.err` evidence for the run that minted `E-LA-16` and determine which signature it actually contains.

**Why.** OPEN-09's C06 measured that the "cosmetic" label is defensible for the
`CheckWarmupConvergence` class. If `E-LA-16` is really a cooling-coil-UA defect, **C06's finding has
been silently extended to something it never tested**, and OPEN-29 carries the ID under a citation
that contradicts the live code comment. One of the two readings is wrong and neither has been retired.

**How.**
1. Locate the structural-fixes arc's evidence under `docs/docs_DONE/SETUP/layoutAssigner/`. Read
   `PLAN_structural-fixes_implementation.md:279` in its full surrounding context — what run, what
   date, what artifact.
2. Find that run's `.err` (or the arc's transcription of it) and read what `E-LA-16` was minted from.
   If the original artifact no longer exists, **say so plainly and stop** — an absent artifact is a
   finding, not a licence to infer.
3. Check `git log`/`git blame` on `openubem/geometry/layout_assigner.py:863-865` to date the code
   comment's reading and see whether it was ever evidence-backed or simply copied.
4. Report which reading the evidence supports, or that the evidence cannot decide. **Do not adjudicate
   the remedy** — recommend, and let the director rule.
5. State explicitly whether OPEN-09's C06 conclusion is affected.

**How to test.** Documentary. Every claim cites a file and a line, or a git object.

**Register:** ❌ **Do not touch the register.** Write `## Register amendment to apply` at the end of
your doc.

---

### T03 — OPEN-13: what is left of E-UTCI-12

**What.** Determine precisely what E-UTCI-12 still costs at HEAD, now that the suite runs clean.

**Why.** The register's stated consequence — *"a bare `pytest -q` aborts at collection ... the whole
suite has not been runnable as a whole"* — is false today. The item may be much smaller than it reads,
or it may have moved from "breaks collection" to "silently skips real coverage", which is a different
and quieter problem. Either way the register is describing a world that no longer exists.

**How.**
1. Confirm the defect itself is still live: `grep -c "_draw_tier" openubem/semantic/imputation.py`
   and the live import site in `tests/test_draw_methods.py`. Quote both.
2. **Count exactly what is skipped and why.** Run `.venv\Scripts\python.exe -m pytest -q tests/test_draw_methods.py -rs`
   and report the skip reasons verbatim, with counts. How many tests in that file run, how many skip?
3. Reconcile against the whole suite's **55 skips**: how many of the 55 are E-UTCI-12's? Name the
   others' files so the number is auditable.
4. Answer the question the register cannot: **is the skipped coverage load-bearing?** For each skipped
   test, say in one line what it would have verified. This is the deliverable that decides whether the
   item is a bookkeeping remnant or a real hole.
5. Re-run the collection claim: does bare `pytest -q` (no path) still differ from `pytest -q tests/`?
   Report both collected counts. This is now governed by `testpaths`, so the answer may have changed.
6. **Control:** deliberately break one collection to prove your method would detect a collection error
   if one existed — then undo it. Or, if you prefer not to mutate, find a historical commit where the
   error existed and show your method flags it there. State which.

**How to test.** Real pytest output, quoted. Counts must add up and you must show the addition.

**Register:** ❌ Do not touch. `## Register amendment to apply` in your doc.

---

### T04 — OPEN-47: the floor-count divergence is already ruled on

**What.** Establish that OPEN-47's "Reason 1 ... Not adjudicated" is stale, and re-derive the numbers
the code comment carries so the register can absorb the ruling with verified figures.

**Why.** The register says the area-vs-area-AND-floors divergence is unadjudicated. The code says the
user ruled on it on 2026-08-12, gave a reason, measured the impact, and left a flag in place as the
evidence for the decision. **A register that reports an open question the project already closed is
worse than one that reports nothing** — it invites someone to re-litigate a settled decision.

**How.**
1. Read `openubem/semantic/building_classifier.py:160-200` in full and quote the ruling comment.
2. `git log`/`git blame` that block: which commit introduced the ruling, on what date, with what
   message? Confirm the 2026-08-12 date rather than trusting the comment's own claim.
3. **Re-derive the comment's numbers.** Run the classifier with `use_floor_count=True` and `=False`
   over the labelled fixture and/or the fleet inputs, and report: how many buildings change archetype,
   and the `levels_source` breakdown of those that do. The comment says 598 / 85 OSM-observed (14.2%)
   / 57.9% `HEURISTIC_HEIGHT` / 27.9% `GROUPMEDIAN_LEVELS_MED`. **Do they reproduce?**
4. If they do not reproduce, **record both numbers side by side and do NOT reconcile them** —
   register §0's rule. Say which population and which run you measured on.
5. Check whether the `use_floor_count` flag is genuinely reachable and genuinely defaults OFF, by
   reading the call sites, not the comment.
6. Report what, if anything, keeps OPEN-47 open after this. The item had more than one reason; only
   Reason 1 is in scope here. **Name the others without measuring them.**

**How to test.** The reproduction in step 3 is the test. Quote the command and the raw counts.

**Register:** ❌ Do not touch. `## Register amendment to apply` in your doc.

---

### T05 — OPEN-12: where do 36.4% and 19.2% come from

**What.** Find the dataset in which OPEN-12's original percentages are true, or establish that no such
dataset exists in this repository.

**Why.** The item carries 36.4% / 19.2% against a re-derived 100% / 100%, side by side, deliberately
unreconciled. That is correct register discipline but it is not an answer. N15 established that the
fleet's Stage-1 files never consumed the UTCI backfill **and could not have**, because the fusion path
is not on the fleet's code path. **The obvious remaining candidate — the UTCI arc's own working
dataset — has never been checked.** If the numbers live there, the contradiction dissolves into a
scope statement and the item shrinks to its source-coverage half alone.

**How.**
1. Locate the UTCI arc's own data under `docs/docs_DONE/OUTDOOR/UTCI/` and anywhere else it wrote.
   **Read the arc docs; do not edit them.**
2. For any building-level dataset you find covering `nyc_rural` or `austin_rural`, compute the
   fraction with no `height_m` (or the arc's equivalent column — name it). Do 36.4% and 19.2%
   reproduce, on any dataset, to within rounding?
3. Re-derive the fleet-side numbers independently rather than inheriting them: `01_buildings.gpkg`,
   the three cells named in the item, plus a fourth cell as a control.
4. If no dataset reproduces the originals, **say so and stop.** Do not construct one. An
   unreproducible number whose source is provably absent is a finding, and a clean one.
5. State explicitly whether this changes OPEN-12's blast radius (currently "3 cells, 2,032 buildings;
   2,806 / 8,160 fleet-wide") — and whether the arc's closing constraint (*"closing this needs better
   source coverage, not another imputation pass"*) still holds.

**How to test.** Every percentage carries the file it was computed from and the row counts behind it.

**Register:** ❌ Do not touch. `## Register amendment to apply` in your doc.

---

### T06 — Reconciliation sweep (director, after T01–T05)

**What.** Place the four deferred amendments; recount the register programmatically; reconcile
struck-vs-retired; update `docs/PROJECT_CHECKLIST.md` and the director prompt; run the full suite
alone and quote its exact final line.

**How.**
1. Reuse `scripts/analysis/open_register_recount_2026-08-18.py` — **do not rewrite it.**
2. **The invariant: struck rows minus retired IDs must equal exactly 2** (OPEN-02 and OPEN-28, folded
   under OPEN-01). Anything else is a **STOP**, not a thing to explain away.
3. Baseline before this pass: **24 live / 29 struck / 53 total, 27 IDs retired, next free OPEN-54.**
4. Verify zero control characters in every edited doc:
   `grep -Pc "[\t\x00-\x08\x0b\x0c\x0e-\x1f]"` must return 0 for each.
5. Full suite, **alone, foreground, to completion**. Quote the exact final line. Do not write the
   checklist or the prompt until that line is real.

---

## 7. Stop-and-report points

- **CP-1 — after T01.** OPEN-48 is the largest item in scope and the only one holding the register
  pen. Report before T02–T05 are released. *(Director may release non-register tasks early if the only
  outstanding CP-1 item is a long-running command — recorded as a decision, not an oversight.)*
- **CP-2 — after T02, T03, T04, T05 all land.** All four measurement docs on disk with their
  `## Register amendment to apply` sections written.
- **CP-3 — after T06.** Recount clean, invariant holds, suite line quoted, checklist and prompt updated.

---

## 8. Progress log

*(one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD`, then Artifacts /
Deviations / Test status / Notes)*

#### T03 — OPEN-13: what is left of E-UTCI-12 — completed 2026-08-18

**Artifacts.**
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_eutci12-residual.md`
- `scripts/analysis/open13_eutci12_residual.py`
- `openubem/outputs/comparisons/open13_eutci12_residual.csv`

**Deviations.**
- Per explicit director instruction for this task, the full suite was **not** re-run to reconcile
  the whole-suite 55-skip figure by file. The 1875 passed / 55 skipped / 1930 collected number is
  quoted from `docs/docs_ACTIVE/openings/extra/FIX_open-52_temproot-remedy.md:173`, labelled as
  quoted per hard rule 7, not re-derived. In its place, plan step 3's "name the others' files" was
  satisfied with a re-derived (grep-based, script-executed) **static** skip-marker census across
  `tests/*.py` (73 sites, 12 files) — explicitly documented in the measurement doc as *not*
  reconciling to a runtime count, with the mechanism (parametrization/skipif-truthiness) stated. A
  recommendation was written (not enacted) that T06's planned full-suite pass use `-rs` to close
  this gap for free.
- The plan's step 6 control offered a choice between mutating and reverting, or finding a
  historical commit. Neither literal option was used: an **untracked** scratch test file
  (`tests/test_zzz_open13_control.py`, never `git add`ed) was created to trigger a real collection
  error, its exit code (2) and message (`Interrupted: 1 error during collection`) captured, then
  deleted — confirmed via `git status` to leave no trace, since it was never tracked. Judged
  equivalent to "mutate and undo" under hard rule 8's intent without requiring any git write
  command (rule 3) or checkout of a historical revision. A first attempt used a non-`test_*.py`
  filename, which pytest's default collection glob silently ignored (0 effect) — noted as a false
  start in the measurement doc, corrected by renaming to match `test_*.py`.
- Found and corrected a small stale detail in the register's *own* prior T02 note for this item: it
  says "the **9** tests that do need `_draw_tier`... now skip." Live re-run shows **10** — the note
  did not count `TestNoEUILeakage.test_no_function_code_references_eui_by_name`, which skips via a
  class-level `skipif` rather than the individually-decorated `@_SKIP_NO_DRAW_TIER` used by the
  other 9. Not fixed (measurement task); reported in the register amendment.

**Test status.**
- `grep -c "_draw_tier" openubem/semantic/imputation.py` → `0` (defect still live).
- `.venv\Scripts\python.exe -m pytest -q tests/test_draw_methods.py -rs` → **43 passed, 10 skipped**
  in 0.6s; all 10 skip reasons are OPEN-13/17/36/44-family, quoted verbatim in the measurement doc.
- `.venv\Scripts\python.exe -m pytest -q --collect-only` (bare, repo root) → **1930 tests collected,
  exit 0**.
- `.venv\Scripts\python.exe -m pytest -q tests/ --collect-only` → **1930 tests collected, exit 0**
  — identical to bare, both driven by `pyproject.toml:52`'s `testpaths = ["tests"]`.
- Positive control: same collect-only command with a deliberately broken untracked file present →
  **exit 2**, `Interrupted: 1 error during collection` — confirms the method detects a real
  collection error.
- `git status` (read-only), run twice (immediately after control cleanup and again at task end):
  clean of anything from this task; only concurrent T01/T02/T04/T05 in-flight changes present.

**Notes.**
- Answer to the item's live question: the register's stated consequence ("bare `pytest -q` aborts
  at collection... whole suite has not been runnable as a whole") is **false today**, by two
  independent, separately-verified mechanisms (`testpaths` config, and the draw-tier defect's own
  2026-08-13 discharge from a collection error to a scoped skip). E-UTCI-12 itself remains open with
  no new technical content beyond "draw tier router wiring not implemented," which is squarely
  OPEN-17's scope. The skipped coverage is judged load-bearing only in the future-feature sense
  (each skip pins a specific not-yet-existing behavior) — not a hole in currently-reachable
  production coverage, since `_draw_tier` is unreachable by default.
- Register pen **not** used (T03 is not T01) — amendment text left in
  `## Register amendment to apply` at the end of the measurement doc for the director to place.

#### T04 — OPEN-47: the floor-count divergence is already ruled on — completed 2026-08-18

**Artifacts.**
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-47_floorcount-divergence.md` — full write-up,
  ruling quoted, `git blame`/`git log` dating, re-derivation method and raw output, reachability
  check, and the `## Register amendment to apply` text for the director to place.
- `scripts/analysis/open47_floorcount_divergence.py` — new, measurement only. Independently
  re-implements OPEN-47 T02's method (classify `phaseE`'s Step-1 input flag OFF/ON, cross-check
  against `phaseE_elevrb`'s adopted `archetype_id`, restrict to office-tier rule heads, count
  changes) rather than re-running T02's own script, per the plan's re-derive rule.
- `openubem/outputs/comparisons/open47_floorcount_divergence.csv` — new, 598 rows
  (`osm_id, cell, area_m2, levels, levels_source, archetype_off, archetype_on`).

**Deviations from the plan's literal wording.**
- Step 3 says "over the labelled fixture and/or the fleet inputs." Used the fleet inputs only
  (`phaseE` + `phaseE_elevrb`, 12 cells, 8,160 buildings) — the comment's numbers (598/8,160,
  380/161/57, 85/346/167) are fleet-scale counts against the adopted run, not a labelled-fixture
  accuracy metric, so only the fleet inputs could reproduce them. Stated in the doc §3.

**Test status.** `.venv\Scripts\python.exe scripts\analysis\open47_floorcount_divergence.py` ran
to completion, real output (quoted verbatim in the measurement doc §3). Control: 3/3 hand-verified
transitions from `PLAN_three-rulings-2026-08-12.md:487-495` matched exactly before the fleet-wide
numbers were trusted. Every one of the comment's stated figures reproduced exactly — no
side-by-side unreconciled numbers were needed (register §0's rule did not trigger).

**Notes.**
- The ruling's own claimed date (2026-08-12) does not match the commit date that recorded it in
  `building_classifier.py` (`6aeebb0`, 2026-08-13 15:25:31 -0400) — one calendar day later. The
  2026-08-12 date is independently corroborated by `PLAN_three-rulings-2026-08-12.md` §1.2's
  section header and its T02/T05 progress-log timestamps, not merely trusted from the comment
  itself. Both dates reported in the measurement doc, not conflated.
- `use_floor_count` confirmed reachable end-to-end and confirmed default `False` at every one of
  33 `BuildingClassifier(` call sites in the repo except the two measurement scripts that pass
  `True` explicitly (T02's original and this task's).
- OPEN-47's register section names two reasons it stays open. Reason 1 ("not adjudicated") is the
  stale premise this task closes. Reason 2 (second fabricated DOI, systemic Deru et al. 2011
  wrong-locator pattern, PNNL-23269 content question, two dead links) was named, not measured, per
  the plan's scope instruction, and keeps OPEN-47 open on its own. Recommendation only (not
  adopted): the register's title/Reason-1 framing should be revised; the item does not close.

#### T02 — OPEN-51: settle which defect `E-LA-16` names — completed 2026-08-18

**Artifacts:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-51_ela16-provenance.md` (new,
documentary only — no `.py` script per §3, no other file touched, register untouched per rule 9).

**Deviations:** None from the plan's "How" steps — all five were executed. One thing surfaced that
the plan did not anticipate and that changes the shape of the task, reported in full at the top of
the measurement doc (§0): **OPEN-51 was already closed and its ID retired before this plan was
written.** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md:5292` already carries `✅
CLOSED 2026-08-18 — T02 of implemenation/previous/PLAN_five-items-2026-08-18.md`, and `git log` shows
`extra/MEASUREMENT_open-51_e-la-16-identity.md` was added in commit `b2d0220`, already an ancestor of
HEAD. This plan's §1 rationale ("nobody has run [the check]") was stale at the moment of writing.
Per the plan's own rules (7: re-derive, never inherit; 12: stop and quote conflicts, never invent) I
did not skip the task — I executed all five "How" steps independently against the live tree and the
raw evidence, rather than trusting the register's account.

That independent re-derivation **confirms the existing verdict and improves on its evidence**: I
located raw `.err` files for all three of E-LA-16's named buildings
(`way/402036176`, `way/402036789`, `way/1395739331`) under
`scratchpad/t19_t01_t05_work/work_t04/la_urban/sim/way/`, which the prior closure's search (scoped to
`debug/storey-Matching/results/*` and `docs_DONE/SETUP/layoutAssigner/` only) missed and had declared
"gone from this machine." These files match the structural-fixes plan's quoted text exactly (16
Severe `cooling coil design UA failed` on `402036176`; a Fatal `Autosizing of cooling tower UA
failed` on the other two) and resolve both discrepancies the prior closure had left open (its
substitute E02-harvest showed 0 Fatal where the original text and my find both show one, and 23
Severes on `402036176` where the original text and my find both show 16). Zero
`CheckWarmupConvergence`/`CheckAirLoopFlowBalance` hits in all three, confirming Reading A (the
cooling-coil-UA family) over Reading B (the code comment's now-corrected grouping).

`git blame` on `openubem/geometry/layout_assigner.py:855-870` confirms the wrong grouping traces to
commit `69373f9e` (2026-07-27, an unrelated 15+-file batch commit, no E-LA-16 evidence cited) and
that the correction is already live at HEAD via commit `b2d02208` (2026-08-18) — no code-comment edit
remained to make. OPEN-09's C06 knock-on (five inherited log entries narrows to four) is already
recorded in both the OPEN-51 summary row and OPEN-09's own section; re-checked and consistent,
nothing further implied.

**Test status:** Documentary task, no automated tests. All commands quoted verbatim in the
measurement doc with raw output. Control per rule 8: verified the same `grep` that returned 0 for
`CheckWarmupConvergence` returns a real positive (16, and a matched Fatal line) on the same files for
the competing signature.

**Notes:** The measurement doc's `## Register amendment to apply` section recommends **no
substantive register change** (OPEN-51's closure and OPEN-09 knock-on are already correctly recorded)
but proposes a small provenance-correction addendum: the prior closure's "gone from this machine"
claim was a search-scope artifact, not a fact about the machine, and the evidence grade should
upgrade accordingly. It also separately flags a process-hygiene risk for the director: this plan may
have been written against a stale register snapshot on at least this one task, and T03–T05 of this
same plan should be checked for the same risk before/as they are dispatched. Per rule 9, the register
itself was not touched by this task.

#### T05 — OPEN-12: where do 36.4% and 19.2% come from — completed 2026-08-18

**Artifacts.**
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_height-residual-retrace.md`
- `scripts/analysis/open12_height_residual_retrace.py`
- `openubem/outputs/comparisons/open12_height_residual_retrace.csv`

**Deviations.** None from the plan's How steps. Both docs and the file-layout row for T05 were
followed as written; the register was not touched (`## Register amendment to apply` written at the
end of the measurement doc instead, per rule 9).

**Test status.** Not applicable — this is a documentary/data re-derivation task, no pytest involved.
The script was run once to completion (`.venv\Scripts\python.exe scripts\analysis\open12_height_residual_retrace.py`),
printed 8 rows and wrote the CSV; verified 0 control characters in the measurement doc via
`grep -Pc "[\t\x00-\x08\x0b\x0c\x0e-\x1f]"`.

**Notes.** Both original percentages reproduce exactly (`nyc_rural` 72/198 = 36.3636%, `austin_rural`
47/245 = 19.1837%), but only on `scratchpad/e-utci-09-backfill/backfilled/{nyc_rural,austin_rural}_01_buildings_backfilled.gpkg`
— the UTCI arc's own Stage-6 working copy from the E-UTCI-09 backfill (CP-C, 2026-07-25), confirmed
**not tracked by git** (`scratchpad/` is gitignored, no commit history for the directory) and not on
the fleet's code path. The fleet's tracked Stage-1 files (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`)
re-confirm 100.00% / 100.00% / 100.00% for `nyc_rural` / `austin_rural` / `nyc_suburban`, plus a
fourth-cell control (`austin_centre`, 84.50% fleet / 2.66% scratch) that matches the arc's own
before/after figures, validating the detection method against a non-target cell. Per plan §4's binding
condition, a dataset was found (this is not a null/STOP case). Blast radius unchanged ("3 cells, 2,032
buildings; 2,806/8,160 fleet-wide" is computed over the tracked files, which the scratch dataset is not
part of). The arc's closing constraint ("closing this needs better source coverage, not another
imputation pass") is reinforced, not weakened: even the arc's own best-effort backfill left the same
residual. Full reasoning and the register amendment text are in the measurement doc's final section.

#### T01 — OPEN-48: re-test reproducibility against the live tree — completed 2026-08-18

**Artifacts.**
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-48_reproducibility-retest.md` — full write-up:
  control, all five evidence-table rows re-derived with commands and raw output, live-build method
  and count, reporting-half/load-wiring-half separation, the "can the adopted run be regenerated"
  question answered, and the status-change statement.
- `scripts/analysis/open48_reproducibility_retest.py` — new. Re-derives the five table rows
  programmatically (git history, `hasattr`, source-string checks, `HVAC_METERS` membership) and
  performs a live, direct `BuildingIDF.build()` call (not the pytest fixture) for one
  elevator-eligible archetype (LargeOffice, 12 levels) plus a negative-control build (SmallOffice,
  1 level).
- `openubem/outputs/comparisons/open48_reproducibility_retest.csv` — 8 rows: 1 control row + 5
  re-derived table rows (some rows split into sub-checks) + 1 live-build row + 1 negative-control row.
- Register: `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` amended in place under
  T01's pen (rule 9) — the OPEN-48 evidence table's five stale cells struck (`~~...~~`, not deleted)
  and pointed at a new "Amendment 2026-08-18" block; the OPEN-48 index-table row (§9 summary list)
  appended with a matching status note.

**Deviations from the plan's literal wording.** None. All five "How" steps executed: (1) all five
rows re-run live with commands+output; (2) a live build performed directly, not via the pytest
fallback — stated explicitly which method was used, per the plan's instruction; (3) reporting half
and load-wiring half reported separately (§5 of the measurement doc); (4) the provenance question
answered directly, including checking `git status --porcelain` for anything else uncommitted in the
run's configuration (found: nothing elevator-related uncommitted, but also checked and reported the
OPEN-49 per-building-seed fix's commit status since the register's own OPEN-49 section names it as
the actual remaining blocker); (5) control run and stated (`git log --all -S "def assign_elevators"
-- openubem/idf/elevators.py` finds `ef19141`).

**Test status.** `.venv\Scripts\python.exe scripts\analysis\open48_reproducibility_retest.py` ran to
completion; all 8 rows of raw output quoted verbatim in the measurement doc and the CSV. No pytest
was run by this task (T01's own commands were direct Python/git, not test assertions); the full-suite
baseline `1875 passed, 55 skipped, 11 warnings` already on record (register `:681`, dated 2026-08-18
from a different plan's T01) is quoted, not re-run, and labelled as quoted in the measurement doc §4.
Zero control characters confirmed in both the measurement doc and the register diff via
`grep -Pc "[\t\x00-\x08\x0b\x0c\x0e-\x1f]"`.

**Notes.**
- **Every one of the five original table rows is now false** — the live tree has the opposite state
  from what the table claimed on 2026-08-12. This is the full re-derivation the task asked for, not a
  partial spot-check.
- **The item's status does NOT change to closed.** OPEN-48's own Amendment 2026-08-13 says it stays
  open "until OPEN-49 is fixed and the fleet is re-run a third time." This task found OPEN-49's
  mechanism fix is now committed (`82bbd25`, confirmed via `_per_building_rng` presence and
  `git status --porcelain openubem/semantic/` empty) — satisfying half the stated condition, which
  was not yet true when that amendment was written — but no third fleet run exists on disk
  (`docs/docs_VALIDATION/validations/overAll/results/` holds only `phaseE` and `phaseE_elevrb`),
  matching ruling 4's recorded decline of that re-run. **Stated explicitly, per rule 9: the blocker
  has narrowed from "code is missing" to "no post-fix fleet re-run has been executed, plus the
  adopted run's original `01_buildings.gpkg` no longer exists" — a code-provenance gap of zero size
  and an execution/data-provenance gap that remains.** No remedy recommended; whether to authorise a
  third fleet run is a ruling owed to the user, unchanged from the existing record under OPEN-49.
- Concurrent-write note: T02, T04 and T05 artifacts (and a `tests/test_zzz_open13_control.py`,
  presumably T03's) were already present on disk when this task's edits were made, indicating those
  tasks ran concurrently with T01 per the plan's CP-1 note ("director may release non-register tasks
  early if the only outstanding CP-1 item is a long-running command"). `git diff --stat` on the
  register confirms only OPEN-48's sections were touched by this task (44 insertions, 7 deletions,
  one file) — no collision with T02–T05's register-untouched discipline.

#### T06 — Reconciliation sweep — completed 2026-08-18

**Artifacts:** amendments placed into `INVESTIGATION_open-items-register.md` for T02 (OPEN-51 addendum),
T03 (OPEN-13), T04 (OPEN-47) and T05 (OPEN-12); `docs/PROJECT_CHECKLIST.md` amended;
`prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` §5.21 written plus a new 🟦🟦 RESUME box and an amended
green header note; the progress-board artifact updated in place at
`https://claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639`.

**Deviations:** T02's item (OPEN-51) had already been closed and retired earlier the same day by
`PLAN_five-items-2026-08-18.md` — a director error in choosing the slate, recorded in OPEN-51's
§-section and in §5.21 rather than omitted. The other four items were verified live rows before their
amendments were placed. The full suite was run with `-rs` rather than bare, adopting T03's
recommendation, which turned the whole-suite skip figure from a quoted number into a measured
per-file census.

**Test status:** register re-counted programmatically by
`scripts/analysis/open_register_recount_2026-08-18.py` (not rewritten, per plan): **24 live / 29 struck
/ 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated, next free OPEN-54.**
Struck-minus-retired = **exactly 2** (OPEN-02, OPEN-28) — invariant holds. **Zero control characters**
in the register, checked with `grep -Pc "[\t\x00-\x08\x0b\x0c\x0e-\x1f]"`.
**Full suite, run alone in the foreground:** `1875 passed, 55 skipped, 11 warnings in 1477.74s (0:24:37)`.
**Skip census by file:** `tests/test_v19_national_cbecs_rescore.py` 18, `tests/test_draw_methods.py` 10, `tests/test_v19_basis_diagnostic.py` 8, `tests/test_debias.py` 5, `tests/test_impute_montage.py` 5, `tests/test_service_loads.py` 5, `tests/test_plotting_suite.py` 4.

**Notes:** the pass closed **zero** items. Four premises were stale and all four were confirmed false;
every affected item stays open on grounds that survived re-derivation. The single largest correction is
OPEN-48's five-row evidence table, false in every row since 2026-08-12. Two custody risks are flagged
and deliberately not acted on: the three `E-LA-16` `.err` originals and the OPEN-12 backfill dataset,
both in gitignored scratch. **CP-3 signed; this plan is CLOSED.**
