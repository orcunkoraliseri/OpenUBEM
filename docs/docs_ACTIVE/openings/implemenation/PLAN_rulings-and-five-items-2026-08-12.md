# PLAN — the four rulings, and five more open items

**Slug:** `rulings-and-five-items-2026-08-12`
**Opened:** 2026-08-12 (evening pass, after `PLAN_five-item-sweep-2026-08-12.md` closed)
**Author:** director. **Executors:** fresh Sonnet sessions, one per task group.
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`
**Director prompt:** `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`
**DESIGN pointers:** `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md` (fixture
provenance), `docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md` (rule 17a / E-R3-2),
`openubem/semantic/building_classifier.py` (HEAD).

---

## 0. Why this plan exists

On 2026-08-12 the user ruled on **four** items in one message and then asked for **five more** to be
taken into execution. This document covers both halves. Its two halves are different in kind and the
difference matters:

- **T01–T04 discharge rulings already given.** The decision is made; the work is what remains.
- **T05–T10 are the five newly chosen items.** Each satisfies the arc rule (§6 of the director
  prompt): its first measurement is already made, no user ruling is outstanding, and no cluster CPU
  is required.

🔴 **This plan closes no item on its own authority.** The director decides closure at the checkpoints,
against raw artifacts, never against an executor's report.

---

## 1. Hard rules for the executor

1. 🔴 **No cluster. No `srun`, no `ssh`, no `sbatch`.** Every task here is local. If a task appears to
   need the cluster, **stop and say so** — do not improvise a local substitute and report it as the
   measurement.
2. 🔴 **Never run `git commit`, `git push`, `git checkout <branch>`, `git reset`, or `git stash drop`.**
   Git is handled externally by the user. Read-only git (`log`, `show`, `diff`, `-S`) is fine and is
   required by several tasks.
3. 🔴 **Do NOT edit the register (`INVESTIGATION_open-items-register.md`), the director prompt, or
   §11 of this document.** Several executors run in parallel and concurrent writes lose each other's
   work. You write **your own named report file** and nothing else shared. The director writes all
   register amendments and all progress-log entries.
4. 🔴 **Never edit** root `main.py`, anything under `docs/docs_main/`, or any OVERVIEW / DESIGN doc.
5. 🔴 **No `.py` files under `docs/`, ever.** Analysis scripts go in `scripts/analysis/`. (T05 exists
   partly *because* this rule was broken before.)
6. **A before/after is not reportable until the "before" is shown to differ from the "after."** A
   single "after" number satisfies nothing.
7. **A scan that finds nothing reports emptiness, and proves the scanner works.** Insert a deliberate
   positive into a scratch file, show the scanner catches it, remove it. **Zero without that control
   is not a result.**
8. **A count is not a cause.** "70 tests fail" is a count. "51 of them raise `FileNotFoundError`
   because they assert an output artifact exists" is a cause. Report causes.
9. **`**  Fatal  **` has TWO spaces** on each side in EnergyPlus `.err` files. Never use the
   `has_fatal` column — it is measured wrong (OPEN-29).
10. **Say what you did not do.** An unfinished leg reported as unfinished is a good outcome. An
    unfinished leg reported as finished is the failure mode this arc exists to catch.
11. 🔴 **Do not quote "158.0 kWh/m²" anywhere.** T01 changes it. Until T01 lands, quote no fleet
    headline at all.

---

## 2. File layout

| What | Where |
|---|---|
| This plan | `docs/docs_ACTIVE/openings/implemenation/PLAN_rulings-and-five-items-2026-08-12.md` |
| Executor reports | `docs/docs_ACTIVE/openings/extra/<TYPE>_<slug>.md` |
| CSV / data artifacts | `openubem/outputs/comparisons/` |
| Analysis scripts | `scripts/analysis/` |
| Figures | `openubem/outputs/` (flat) |
| New fixture (T03) | `tests/fixtures/` |

---

## 3. Dependency decisions (pinned — do not renegotiate)

- **Python:** the repo `.venv` as-is (Python 3.14). Do not upgrade, pin, or add packages.
- **pytest:** invoke as `python -m pytest -p no:cacheprovider`. The `no:cacheprovider` flag is
  required — otherwise parallel executors fight over `.pytest_cache`.
- **No new dependencies.** If a task seems to need one, stop and report.
- **Adopted run artifacts** live at
  `docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/05_results.csv`.
  🔴 The register cites this as `results/phaseE_elevrb/...`, which is a **path relative to
  `docs/docs_VALIDATION/validations/overAll/`, not to the repo root.** Two executors have already
  lost time to this. Use the full path.

---

## 4. Facts established by the director, with citations — build on these, do not re-derive

### 4.1 The four fleet aggregations (T01)

Re-derived by the director **twice** on 2026-08-12: once from
`openubem/outputs/comparisons/open42_t02_percell_repro.csv`, and once **independently from the twelve
raw `05_results.csv` files**. Both agree to four decimals. 12 cells, 8 160 rows, **8 154 success**,
total floor area **23 545 868.4 m²**.

| aggregation | value |
|---|---|
| mean of the 12 cell means, weighted by each cell's **total** building count — *the published 158.0* | **158.0298** |
| the same, weighted by each cell's **success** count | 158.0557 |
| **unweighted** mean of the 12 cell means | 160.0993 |
| 🔵 **pooled — `Σ(EUI × area) / Σ(area)` over all 8 154 buildings at once** | **157.0552** |

Because each cell's stored `weighted_total_eui` is itself its area-weighted mean, the pooled figure is
algebraically **total simulated energy ÷ total simulated floor area**.

### 4.2 The classifier fixture pool (T03)

Measured by the director 2026-08-12 from the two source gpkgs.

| | count |
|---|---|
| `tests/fixtures/boston_downtown_500m.gpkg` | 483 |
| `tests/fixtures/chicago_loop_500m.gpkg` | 399 |
| **pool total** | **882** |
| `building_tag` present and **not** the generic `yes` | **558** |
| `function_tag` present | 100 |
| 🔵 **TAG-RICH (either of the two above)** | **592** (boston 233 / chicago 359) |
| generic `yes` with no function tag — the rule-17a population | 290 |
| `levels` present | 647 |
| `height_m` present | 253 |

Top `building_tag` values: office 192, commercial 132, **roof 70**, apartments 39, hotel 26, retail 18,
parking 16, university 11, train_station 11, public 8.
Top `function_tag` values: parking 24, shelter 16, government 9, place_of_worship 8, restaurant 6.

🔴 **The pool is not the constraint.** 592 tag-rich buildings are available; the current exam has
**33** tag-decided rows. A larger, fully tag-decided fixture is possible today with no new data.
⚠️ **`building=roof` (70 rows) is very likely not a building at all** — canopies, carports, shelters.
Whether those belong in an archetype exam is a question T03 must raise, not answer silently.

### 4.3 The current fixture (T03, T10)

- `tests/fixtures/labelled_archetypes_50.csv` — 52 lines = 1 provenance comment + header + **50 rows**.
  Comment line records `labeller=orcunkoral.oseri@concordia.ca, suggested-by=claude-opus-4-7,
  snapshot_date=2026-05-14, ratified=2026-06-11, re-ratified=2026-06-30`.
- Loader and gate: `tests/test_building_classifier.py:1004` (`_run_labelled_fixture`) and `:1035`
  (`test_fine_top1`, gate ≥ 0.70).
- Measured breakdown (2026-08-06, N02, director-audited): 44/50 = **88.0%** overall; excluding the 17
  `FALLBACK_SIZE_DEFAULT` rows, **29/33 = 87.9%**; the excluded 17 alone **15/17 = 88.2%**.
  **The fallback is not inflating the score** — that is measured, not assumed.
- Rule tokens: `FALLBACK_SIZE_DEFAULT` 17, `RULE_USE_CLASS_SIZE` 14, `FALLBACK_UNKNOWN` 5,
  `RULE_HIGHRISE` 5, `RULE_FUNCTION_TAG` 4, `RULE_RESIDENTIAL_TIER` 2, `RULE_LODGING_TIER` 2,
  `RULE_USE_CLASS` 1, `RULE_FUNCTION_TAG_SIZE` **0**, `MIXED_USE_DOMINANT_TAG` **0**.
- Classifier: rule 17a at `openubem/semantic/building_classifier.py:327-329` (E-R3-2) routes
  `use_class == "unknown" and building_tag == "yes"` to `_office_size_tier(...)` at LOW confidence
  (`:356-357`). Size metric is **total floor area** = `footprint_area_m2 × max(levels, 1)`
  (`:186-187`, E-R3-1).

### 4.4 The full test suite (T05, T06)

Run to completion by the director 2026-08-12, `python -m pytest -q -p no:cacheprovider`:
**70 failed · 1 822 passed · 10 skipped · 36 errors · exit 1 · 26m47s.**

| tree | failed + errored |
|---|---|
| `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` | **61** |
| `tests/` | **44** |
| `scripts/analysis/test_viewer_layout_assign.py` | 1 |

| cause | count |
|---|---|
| `FileNotFoundError` — a test asserting an output artifact exists on disk | **51** |
| missing pytest fixture `synthetic_10_gdf` (setup errors) | ~36 |
| `AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DEBIAS…'` | 5 |
| elevator-column `KeyError`s | 8 |

`docs/` holds **30 `.py` files, 5 of them tests**. Two are byte-identical duplicates of files in
`tests/` (`cmp`-verified); **three have drifted from their `tests/` twins**.
⚠️ `tests/fixtures/synthetic_10_buildings.py` **does exist** — so the `synthetic_10_gdf` errors are a
wiring problem, not a missing file. T05 must establish which.
⚠️ `tests/test_sim_integration.py::test_synthetic_fleet_full_annual` emits a Windows access-violation
faulthandler dump from `joblib`/`loky` under Python 3.14. **It does not stop the run.** Known, recorded,
not this plan's business.

### 4.5 The collection abort and its containment (T06)

`tests/test_draw_methods.py` was made collectable on 2026-08-12 by a **module-level skip**. Cost,
measured: the file holds **53 tests**; only **13** depend on the missing feature; **43 pass and 9 fail**
when only the offending class is removed. The abort originates at **class-body evaluation** —
`class TestNoEUILeakage` at `:631`, list literal `imp._draw_tier,` at `:645`. Measured: a
`@pytest.mark.skip` decorator on the class **does not prevent class-body execution**, so the narrow fix
needs conditional collection, not a decorator.

### 4.6 The unwritten completion record (T08)

`IMPLEMENTATION_phaseC_ml_imputer.md:849` — `#### T07 — wire _draw_tier + registry + order … completed
2026-07-16`. Verified from git: `_draw_tier` has **never** been committed to
`openubem/semantic/imputation.py` (`git log --all -S`), `_draw_stratum_col_for` is absent from all of
`openubem/`, `_CANONICAL_TIER_ORDER` is `("fusion","spatial","ml","statistical")` at
`imputation.py:543`, and `config.IMPUTE_DRAW_METHOD_BY_TARGET` has zero `DRAW` matches. **The tests
landed; the feature did not.** The N13 sweep sized this at **596 entries swept, 1 governance gap**.

### 4.7 The six failed simulations (T07)

`scripts/validation/v12_cell_pipeline.py:659`, in `_build_enriched_gdf`, initialises
`footprint_area_m2 = 200.0` (with `num_floors = 1.0`, `height_m = 3.5`, centroid `0.0, 0.0`) and
overwrites from the simulation SQL at `:664` **only** when `status == "success"`. **There is no `else`
branch.** All six buildings are `failed`, so the initialiser survives into `05_results.csv`. Stage 1
(`results/phaseE/<cell>/01_buildings.gpkg`, EPSG:32611) carries their **real** footprints —
3 417.0 / 1 398.5 / 1 555.9 / 1 355.2 / 22 443.7 m² (`la_rural`), 1 173.4 m² (`la_urban`).
🔴 **`error_summary` is the empty string for all six manifest rows.** That is the binding obstacle.

### 4.8 The accuracy drift (T10)

OPEN-04's `92.0% → 84.0% → 88.0%` is attributed by bisect to commits `7635ce2` → `67ede73` →
`0df422e`→HEAD. The **unverified lead** recorded in the register: the drift may be a change in *tag
coverage* moving rows across the rule-17a boundary rather than a change in classifier logic. It has
never been tested. ⚠️ The Boston 41.0% / Chicago 65.4% figures predate E-R3-2 and **must not be used**.

---

## 5. Task list

### T01 — OPEN-43: adopt the pooled fleet EUI, and restate every figure that quotes the old one

**Status: the decision is made.** 🔴 **RULED 2026-08-12.** The user's instruction was to proceed on
whichever definition is the most accurate. The director's ruling, on that instruction:

> **The published fleet EUI is `Σ(energy) / Σ(floor area)` pooled over all simulated buildings =
> 157.0552 → published as 157.1 kWh/m².** It is the physical definition of an energy use intensity:
> total energy divided by total area. It is what any reader of "fleet EUI" assumes. It has no
> aggregation artefact — the mean-of-cell-means result changes if the cells are re-cut, and this one
> does not. And it is the only one of the four that answers the question "how much energy does this
> stock use per square metre."

**What.** (a) Replace the fleet headline everywhere it is published. (b) State the definition beside
the number, in every place, so this item cannot recur. (c) Leave a durable record of the old figure.

**Why.** The old headline is a **mean of the 12 cell means**, which lets a 245-building cell weigh as
much as a 900-building one. That was never a stated choice — nothing in
`openubem/results/aggregator.py` decides the fleet roll-up at all (the aggregator is per-cell only), so
the fleet step's author and intent are untraced. A number nobody chose should not be a headline.

**How.**
1. Grep the live tree for `158.0`, `158.03`, `158.0298`, and `fleet EUI`. Cover
   `docs/docs_ACTIVE/`, `docs/docs_REPORTS/`, `docs/docs_EXPLANATION/`, `docs/PROJECT_CHECKLIST.md`,
   `openubem/`, `scripts/`, and every `.html` board under `docs/docs_ACTIVE/openings/`.
   🔴 **Do NOT touch `docs/docs_DONE/`, `docs/docs_main/`, or `docs/docs_VALIDATION/`** — those are
   archived records of what was published at the time, and rewriting them destroys the audit trail.
2. In each live location: **strike the old number, do not delete it**, and write the new one beside
   it — `~~158.0~~ **157.1 kWh/m²** (pooled: total simulated energy ÷ total simulated floor area;
   the struck figure was a count-weighted mean of the 12 cell means, superseded 2026-08-12, OPEN-43)`.
   Adapt the markup to the file type; the three elements — struck old, new, definition — are required
   in all of them.
3. Add the definition to `openubem/results/aggregator.py` as a short docstring note stating that the
   aggregator is **per-cell only** and that the fleet roll-up is pooled and lives outside it.
   **Do not implement a fleet roll-up function** — that is not this task.
4. Write `scripts/analysis/open43_fleet_aggregations.py`: reads the twelve `05_results.csv`, emits all
   four aggregations, and asserts the pooled figure reproduces to 4 dp. This makes the number
   re-derivable by anyone, forever. Emit
   `openubem/outputs/comparisons/open43_fleet_aggregations.csv`.

**How to test.** The script reproduces **157.0552 / 158.0298 / 158.0557 / 160.0993** and exits 0. A
final grep shows **no live file quotes a bare `158.0` as the fleet headline**. Report the exact count
of files changed and list every one. 🔴 **If the grep finds a location you decided not to change, name
it and say why** — a silent omission here is the whole defect repeating.

**Report:** `extra/FIX_open-43_fleet-aggregation.md`.

---

### T02 — OPEN-33: put the archiving rule where every session will meet it — **DONE BY DIRECTOR**

Not for an executor. Recorded here so the plan is complete. See §11.

---

### T03 — OPEN-22: build the new labelled fixture

**Status: the decision is made.** 🔴 **RULED 2026-08-12** — rebuild the fixture. The follow-on question
(*who authors the labels*) was put to the user on 2026-08-12 and answered: **the labels are authored
here, from source evidence, and audited by the director.** The user additionally asked for external
validation against the literature — that is **T04**, a separate task, deliberately kept separate so
that a weak literature result cannot quietly contaminate the label set.

**What.** Build `tests/fixtures/labelled_archetypes_tagrich_v2.csv` — a new exam whose rows are decided
by **tag logic**, not by the size-bucket fallback.

**Why.** 17 of the current 50 rows (34%) are decided by `FALLBACK_SIZE_DEFAULT`, all at LOW confidence,
and 16 of those 17 carry an office label in the answer key. The score is not inflated by this
(measured, §4.3) — but a third of the exam is grading the size-bucketing rule rather than the tag
logic, and the user ruled that is the wrong exam.

**How.**
1. 🔴 **Do not modify, move, or delete `labelled_archetypes_50.csv` or its `.template.csv`.** They are
   the only artifacts against which the existing published accuracy numbers and the OPEN-04 bisect can
   be re-derived. The new fixture is an **addition**.
2. **Sample 100 rows from the 592 tag-rich pool** (§4.2), stratified by `building_tag` so the
   distribution is not all office. Draw with a **fixed seed, recorded in the file's provenance
   comment**, so the sample is reproducible. If a stratum has fewer rows than its share, take all of
   it and say so.
3. ⚠️ **Decide `building=roof` explicitly (70 rows).** These are very likely canopies and shelters, not
   buildings. State your decision and its reason in the report. **Do not include them silently.**
4. **Label each row from source evidence**, not from what the classifier emits. 🔴 **Never run the
   classifier first and label from its output** — that is grading an exam against its own answers, and
   it is the exact failure this rebuild exists to avoid. For each row record: the tags used, the
   inferred use, the chosen archetype, the chosen coarse class, and a one-line reason. Where the
   evidence genuinely does not determine an archetype, **mark the row `UNDETERMINED` and exclude it**
   rather than guessing — and report how many.
5. Reproduce the current fixture's header shape and write a provenance comment naming the labeller
   (`claude-opus-5, director-audited`), the seed, the pool size, the date, and the source gpkgs.
6. **Do not repoint `test_fine_top1` at the new fixture.** The gate's 0.70 threshold is defined against
   the old exam and is not transferable — that is a separate decision the user has not been asked.
   Add a **new, separate, non-gating** test that reports the new fixture's accuracy without asserting
   a threshold.

**How to test.** Run the classifier over the new fixture and emit
`openubem/outputs/comparisons/open22_v2_fixture_breakdown.csv` with one row per fixture row:
`osm_id, source, label, emitted, rule_token, confidence, match`. Report: rows total, rows decided by
`FALLBACK_SIZE_DEFAULT` (🔴 **this is the number the rebuild exists to reduce — state it against the
old 17/50 = 34%**), accuracy overall, and accuracy excluding fallback rows. Also confirm the **old**
fixture still scores **44/50 = 88.0%** — if it does not, stop, because something else has changed.

**Report:** `extra/FIX_open-22_tagrich-fixture.md`.

---

### T04 — OPEN-22: external validation of the archetype mapping against the literature

**What.** A literature review establishing whether this project's OSM-tag → archetype mapping agrees
with how the published UBEM literature does the same mapping — and, where it disagrees, whether the
disagreement is a defect or a defensible choice.

**Why.** Every accuracy number this project has ever published is scored against **its own answer
key**, authored inside the project. T03 improves the exam but does not escape that circularity: the
labels are still ours. An external reference is the only thing that can. The user asked for this
explicitly.

**How.**
1. **Search the literature** for how UBEM tools map OSM/cadastral tags to building archetypes. Cover at
   minimum: the **US DOE / PNNL commercial prototype and reference building** set (this project's
   archetypes are OpenStudio/DOE prototypes, so their own definitions are the primary source), **CBECS**
   and **RECS** building-type definitions, **LBNL-CBES** (already cited in the fixture's own provenance
   comment for the 2 322 / 9 290 m² office bins — **find and cite the actual source of those two
   thresholds**), **UMI**, **CityBES**, **TEASER**, **CityLearn**, and the **OSM wiki's own `building=*`
   semantics**.
2. **Produce a comparison table**: for each of this project's archetypes, what tag evidence *we* use,
   what the literature uses, and whether they agree. Include the size thresholds — **the office
   size-tier boundaries are the single most load-bearing unvalidated numbers in the classifier**, since
   they decide a third of the current exam.
3. 🔴 **Cite everything with a resolvable reference.** A claim about the literature with no citation is
   worth less than no claim. If a threshold's origin **cannot** be traced, say so plainly — "the
   2 322 m² boundary is cited to LBNL-CBES in our own fixture comment and I could not find it in the
   source" is a **valuable** finding, not a failure.
4. **Do not change any code, any threshold, or any label.** This task produces a document and nothing
   else. Recommendations are listed for the director; they are not applied.

**How to test.** Not a code task; the deliverable is the document. It must contain the comparison
table, a resolvable citation for every external claim, and an explicit **"what I could not find"**
section. 🔴 **An empty "could not find" section will be treated as a sign the task was not done
honestly** — nobody traces every threshold.

**Report:** `extra/RESEARCH_open-22_archetype-mapping-literature.md`.

---

### T05 — OPEN-44: triage the 44 failing tests in `tests/`

**What.** Sort the 44 failures/errors in `tests/` into categories, and state for each whether it
indicates a **defect in shipped code**.

**Why.** The suite ran end to end for the first time in months (§4.4). 106 tests fail or error. Nobody
knows how many mean the code is broken. Until that is known, the suite's verdict cannot be used for
anything, and **every past claim that "the tests pass" remains uninterpretable**.

**How.**
1. Run `python -m pytest -q -p no:cacheprovider tests/ --tb=short` and capture the full output to
   `openubem/outputs/comparisons/open44_tests_run.txt`. ⚠️ **This takes ~25 minutes. Run it in the
   foreground and wait.** Do not background it and then report before it finishes — two executors have
   already done exactly that in this arc.
2. Classify **every** failing/erroring node into exactly one of:
   `artifact-missing` (asserts a file exists that was never regenerated) · `fixture-wiring` (setup
   error, e.g. `synthetic_10_gdf`) · `tests-for-code-that-never-existed` (the T07 pattern —
   `IMPUTE_DEBIAS`, `_draw_tier`) · `stale-expectation` (code changed deliberately, test not updated) ·
   🔴 `REAL-DEFECT` (shipped code is wrong).
3. 🔴 **`REAL-DEFECT` requires evidence, not a guess.** For each one: the assertion, the actual vs
   expected value, and the source line you believe is wrong. **If you cannot produce that, the category
   is `UNTRIAGED`, and `UNTRIAGED` is an honest answer.** Do not inflate or deflate this category —
   it is the number the whole item turns on.
4. **Resolve the `synthetic_10_gdf` question specifically.** `tests/fixtures/synthetic_10_buildings.py`
   exists, so this is a wiring problem — a missing `conftest.py` registration, a renamed fixture, or an
   import that fails silently. **Find which.** ~36 of the errors are this one cause and it may be a
   single-line fix; **do not fix it**, just identify it precisely.
5. **Report on the 61 `docs/` failures separately and do not touch those files.** State: which are
   byte-identical duplicates of `tests/` files, which have drifted, and **what the drift is** in each
   drifted pair. 🔴 Deleting or moving them is a separate decision for the user — this task only
   produces the evidence for it.

**How to test.** `openubem/outputs/comparisons/open44_test_triage.csv` — one row per failing/erroring
node: `nodeid, tree, category, evidence, likely_source_line`. Row count **must equal 106**; state it
and prove it. The report gives the count in each category, and 🔴 **names every `REAL-DEFECT`
individually.**

**Report:** `extra/MEASUREMENT_open-44_test-triage.md`.

---

### T06 — OPEN-13: narrow the skip, and get the 43 innocent tests back

**What.** Replace the module-level skip on `tests/test_draw_methods.py` with conditional collection, so
that the 40 tests which do **not** depend on the missing `_draw_tier` feature run again.

**Why.** The 2026-08-12 containment made the suite collectable by skipping the **whole file** — 53
tests. Only 13 depend on the missing feature. Measured: removing only the offending class yields
**43 passed, 9 failed** (§4.5). The containment is paying 40 working tests to suppress 13 broken ones.

**How.**
1. The abort happens at **class-body evaluation** (`:631`, `:645`), and a `@pytest.mark.skip` decorator
   **does not prevent that** — measured. So the fix must stop the class body from evaluating.
2. **Choose one approach and justify it in the report.** Either guard the class body behind a
   module-level `_HAS_DRAW_TIER = hasattr(imputation, "_draw_tier")` and a
   `@pytest.mark.skipif(not _HAS_DRAW_TIER, ...)` on a class whose body no longer touches the symbol at
   definition time (move the symbol reference inside the test methods) — or move the dependent tests
   into their own file and skip that file. **State the trade-off you chose and why.**
3. 🔴 **Do not implement `_draw_tier`.** Promoting the draw tier is OPEN-17 and is a DESIGN decision
   nobody has made. Implementing it here would be inventing a feature to make a test pass.
4. The skip must still **name OPEN-17 and OPEN-36** and list the missing symbols, as the current one
   does.
5. **The 9 failures are not yours to fix.** Report what they are and leave them failing.

**How to test.** Before/after, both shown: `python -m pytest -q -p no:cacheprovider
tests/test_draw_methods.py` currently reports `1 skipped`; after, it must report **~40 passed, ~9
failed, ~13 skipped** (state the exact numbers you get). Then `python -m pytest --collect-only -q`
must still exit 0 with ≥1937 collected. 🔴 **If collection breaks, revert your change and report
that** — a collectable suite is worth more than 40 tests.

**Report:** `extra/FIX_open-13_narrow-skip.md`.

---

### T07 — OPEN-42: why did the six simulations fail?

**What.** Establish a recorded cause for each of the six `not_simulated` buildings in the adopted run.

**Why.** This is **the binding obstacle to closing OPEN-42**. The 200.0 placeholder is fully explained
(§4.7) and its fleet impact is measured at exactly zero. What remains is that six buildings failed and
`error_summary` is the **empty string** for all six.

**How.**
1. Identify the six from
   `docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/04_simulation_manifest.parquet`
   — five in `la_rural`, one in `la_urban`. Confirm the count is six and no more.
2. **Find their EnergyPlus output locally.** Look for `eplusout.err`, `.end`, `.audit` under the
   `phaseE_elevrb` tree, the T20/T19 harvest caches, and `cache/`. 🔴 **If no `.err` survives locally,
   that is the answer and you stop** — fetching from the cluster is forbidden. **"The cause is not
   locally recoverable" is a correct, complete, reportable result.** Do not substitute a hypothesis.
3. If `.err` files do survive: extract Severe and Fatal counts (🔴 **two-space `**  Fatal  **`**), the
   named zone and surface, and the phase (Warmup vs **Sizing** — OPEN-07 found the register names the
   wrong phase for a similar failure, so read it, do not assume it).
4. **Trace why `error_summary` is empty.** Find the writer that populates that column and the branch
   that leaves it blank. That is a defect in its own right regardless of what the six failures were,
   and it is cheap to find. Cite the file and line.
5. ⚠️ **Do not pair these with the E02 40 800-run harvest.** That is a different campaign; the register
   already made that mistake once and corrected it.

**How to test.** `openubem/outputs/comparisons/open42_six_failures.csv` — `stem, cell,
simulation_status, error_summary, err_file_found, severe_count, fatal_count, phase, zone, surface,
cause`. Six rows, no more, no fewer. The report states plainly which of the six have a recovered cause
and which do not.

**Report:** `extra/MEASUREMENT_open-42_six-failures.md`.

---

### T08 — OPEN-36: re-check the "one governance gap" bound

**What.** Re-run the completion-record sweep, and decide whether N13's finding of **1 governance gap in
596 entries** still holds.

**Why.** 🔴 **There is direct evidence it does not.** The full-suite run found **5 tests failing on
`config.IMPUTE_DEBIAS…`, an attribute that has never existed** (§4.4). That is *exactly* the T07
pattern — tests committed for an implementation that was not — and it is **not** T07. If it is a second
instance, N13's bound is wrong and **OPEN-36 must not be closed on it.**

**How.**
1. Find the `IMPUTE_DEBIAS` tests. Establish from git whether the implementation **ever** existed:
   `git log --all -S"IMPUTE_DEBIAS" -- openubem/` and the same for any function name they import.
   **A `-S` search over all branches is the standard of proof here** — anything less cannot
   distinguish "never written" from "written and reverted."
2. Find the completion record that claims this work. Search progress logs across
   `docs/docs_DONE/`, `docs/docs_ACTIVE/`, `docs/docs_main/` for the task that claims to have
   implemented it. Quote the entry and its file:line.
3. **Re-run N13's sweep** if its script survives (search `scripts/`); if it does not, say so and write
   a fresh one under `scripts/analysis/`. For every completed-task progress-log entry naming a code
   artifact, check that artifact exists at HEAD.
4. **Report the new count against N13's `596 entries / 1 gap`.** 🔴 **If the number of gaps is now more
   than 1, that is the headline of your report** and it changes what OPEN-36 means — from "one bad
   record" to "completion records are not reliable as a class."
5. Distinguish **gap** (a named artifact that does not exist) from **rename** (it exists under another
   name). Renames are not governance gaps. Check before you count.

**How to test.** `openubem/outputs/comparisons/open36_governance_resweep.csv` —
`record_file, line, task, claimed_artifact, exists_at_head, ever_in_git, verdict`. State the total
entries swept and the gap count, both against N13's numbers. 🔴 **Non-vacuity: the sweep must find
T07's known gap.** If it does not find the gap we already know about, the sweep is broken — fix it
before reporting anything else.

**Report:** `extra/MEASUREMENT_open-36_governance-resweep.md`.

---

### T09 — OPEN-31: write the before/after gate where an executor will meet it

**What.** Write the ruled-obligatory classification before/after rule into the place the next person
changing the classifier will actually encounter it.

**Why.** CP-M3 was ruled **obligatory** on 2026-08-09 — *"yes to all three — make them obligatory"* —
and the rule has **never been written down**. The item's own closure condition is that the gate is
written where an executor will meet it. **An unwritten obligatory rule is not a rule.** This is the
same shape as OPEN-33's T07, which closed cleanly on 2026-08-12; follow that pattern.

**How.**
1. The rule, in the form it must be written: **no change that can move classification is adopted until
   the labelled fixture has been run on both sides of it and both numbers are recorded.** A single
   "after" number does not satisfy it.
2. Include **what it would have caught**, because a rule without a reason gets skipped: E-R3-3 cost
   **4 points** of fine top-1 and reclassified **13.4%** of the shared fleet, and **neither number
   existed at adoption time**; attributing the drift later took a five-commit bisection, six weeks late.
3. **Write it in two places, deliberately.** (a) A docstring block at the head of
   `openubem/semantic/building_classifier.py` — the file itself, where someone editing rules will see
   it. (b) The head section of `docs/PROJECT_CHECKLIST.md`, beside the archiving rule T07 added.
   🔴 **Append to that head section; do not rewrite it, and do not touch any journal block below it** —
   they are append-only.
4. **State the two boundaries the ruling does not cross:** it does **not** re-open any adopted change
   retroactively (re-running M01–M05 is forbidden), and it does **not** certify the fixture — OPEN-22
   is rebuilding the exam, and **if the fixture changes, the gate follows it.**
5. 🔴 **Do not edit `CLAUDE.md`** — the director handles that file (see T02).

**How to test.** `git diff --stat` shows exactly two files changed. `git diff docs/PROJECT_CHECKLIST.md`
shows an addition to the head section **only** — no journal block touched. Quote both added blocks in
the report.

**Report:** `extra/FIX_open-31_classification-gate.md`.

---

### T10 — OPEN-04: test the tag-coverage hypothesis for the accuracy drift

**What.** Compute the rule-token breakdown of the 50-row fixture **at the bisect commits**, and
determine whether the `92.0 → 84.0 → 88.0` drift is rows moving across the rule-17a boundary rather
than classifier logic changing.

**Why.** This is recorded in the register as an **unverified lead**, explicitly not a finding. It is the
last unexplained part of OPEN-04, and it is testable today with no new data. It also feeds T03: if the
drift is tag coverage, then the rebuilt fixture must be built to be **insensitive** to coverage
changes, which is a design requirement nobody has stated.

**How.**
1. Commits: `7635ce2` (92.0%), `67ede73` (84.0%), `0df422e` (88.0%), and HEAD.
2. 🔴 **Do NOT `git checkout` any commit** — the working tree is the user's and other executors are
   using it. Use `git show <commit>:<path>` to read historical file contents, or
   `git worktree add` into the **scratchpad directory** and remove it when done. If you use a worktree,
   say so and confirm you removed it.
3. For each commit, run that commit's classifier over the **current** 50-row fixture and emit the
   per-row rule token. **The fixture is held constant on purpose** — that is what isolates classifier
   change from label change. State explicitly that you did this and why.
4. Produce, per commit: overall fine top-1, the rule-token distribution, and — the key number — **how
   many rows are decided by `FALLBACK_SIZE_DEFAULT`**. If that count swings across the commits and the
   accuracy tracks it, the hypothesis is supported. **If it does not swing, the hypothesis is refuted,
   and refuting it is just as good a result** — say so in those words.
5. ⚠️ **Reproduce the three known accuracy numbers first.** If your run of `7635ce2` does not give
   **92.0%**, stop — your harness is wrong, and nothing downstream of it is trustworthy.
6. ⚠️ **Do not use** the Boston 41.0% / Chicago 65.4% figures. They predate E-R3-2 and are stale.

**How to test.** `openubem/outputs/comparisons/open04_ruletoken_by_commit.csv` —
`commit, fine_top1, n_fallback_size_default, n_rule_use_class_size, n_fallback_unknown, …`, four rows.
The report states, in one sentence, whether the hypothesis is **supported or refuted**, and 🔴 if the
harness could not be made to reproduce the known numbers, it says that instead and claims nothing.

**Report:** `extra/MEASUREMENT_open-04_tag-coverage-hypothesis.md`.

---

## 6. Stop-and-report points

| CP | After | The director checks |
|---|---|---|
| **CP-1** | T01, T09 | The two documentation/adoption tasks. Every changed file listed; no archived tree touched; the aggregation script reproduces all four numbers. |
| **CP-2** | T05, T06, T08 | The test-integrity group. Row counts match the stated totals; `REAL-DEFECT` claims carry evidence; T08's non-vacuity control found T07's known gap. |
| **CP-3** | T03, T04, T07, T10 | The measurement group. The old fixture still scores 88.0%; the new fixture's fallback share is stated against 34%; T10 reproduced the three historical accuracy numbers before claiming anything. |

🔴 **At every checkpoint the director re-derives the headline number from the raw artifact, never from
the executor's report.** Three times in this arc an executor's "completed" has not meant completed.

---

## 7. What closing looks like — decided by the director, not by an executor

| Item | Closes if | Stays open if |
|---|---|---|
| **OPEN-43** | every live figure restated, definition written beside it, script reproduces all four | any live location still quotes a bare 158.0 |
| **OPEN-33** | rule in `CLAUDE.md` (T02) — **the last leg; the rest closed 2026-08-12** | — |
| **OPEN-31** | the gate is written in both places with its reason | written in only one, or without the E-R3-3 justification |
| **OPEN-22** | the new fixture exists, is labelled from source, and its fallback share is materially below 34% | fallback share not materially reduced, or labels traced to classifier output |
| **OPEN-13** | the 40 innocent tests run again **and** collection still exits 0 | either half fails |
| **OPEN-44** | **will not close** — triage is step one of several | always, this pass |
| **OPEN-36** | **only if** the re-sweep confirms exactly one gap **and** `IMPUTE_DEBIAS` is shown not to be a second | more than one gap — and then the item grows |
| **OPEN-42** | a cause is recorded for all six, or all six are shown not locally recoverable **and** the empty-`error_summary` writer is cited | neither |
| **OPEN-04** | the hypothesis is supported or refuted on reproduced numbers | the harness could not reproduce 92.0/84.0/88.0 |

---

## 8. Explicitly not chosen, and why

So this is a choice rather than an omission. **OPEN-01** (rulings 2 and 3 still owed by the user),
**OPEN-11** (the six inverted-geometry buildings need the user's remediation call), **OPEN-35** (the
intended fallback is a DESIGN decision, not a measurement), **OPEN-38** (the remedy needs a design call
on the substituted prototype), **OPEN-27** (fixable only by the user at the external source),
**OPEN-07** (needs T20 IDFs that do not survive locally — cluster-blocked),
**OPEN-12 / OPEN-14 / OPEN-19** (need data acquisition or code that does not exist),
**OPEN-17** (promoting the draw tier is a DESIGN decision — T06 is explicitly forbidden from touching it).

---

## 9. Kickoff prompts

Send verbatim, one fresh session per group, no resumption of an old session.

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\openings\implemenation\PLAN_rulings-and-five-items-2026-08-12.md.
Execute T<start> through T<end> in order. Read §1 (hard rules) and §4 (established facts) first and
build on §4 rather than re-deriving it. Write ONLY your own report file under
docs/docs_ACTIVE/openings/extra/ — do NOT edit the register, the director prompt, or §11 of the plan.
Run every measurement in the FOREGROUND and wait for it to finish; do not report before it completes.
Report results and stop. Do not propose alternatives — execute the plan. If the plan is ambiguous,
STOP and quote the conflict.
```

---

## 10. Progress log

*One entry per completed task, director-written. Executors do not write here (hard rule 3).*

---
