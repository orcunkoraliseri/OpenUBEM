# PLAN — the three items the audit opened

**Slug:** `three-new-items-2026-08-12`
**Opened:** 2026-08-12 (night pass, after `PLAN_rulings-and-five-items-2026-08-12.md` closed)
**Author:** director. **Executors:** fresh Sonnet sessions, one per task group.
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — §2 (OPEN-45),
§4 (OPEN-46), §6 (OPEN-47).
**Director prompt:** `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`
**Predecessor plan:** `implemenation/previous/PLAN_rulings-and-five-items-2026-08-12.md` §10, entries T04, T05, T07.

---

## 0. Why this plan exists

The user asked, 2026-08-12: *"pour des nouveaux trois, creer une autre d'un plan d'implementation, et
executer jusqu'a la fin."* The three are **OPEN-45, OPEN-46 and OPEN-47** — the items the previous
pass opened. All three share one property that is worth stating before any task text:

🔴 **None of them was found by doing a task. All three were found by checking a result.** OPEN-45 and
OPEN-46 were incidental findings inside tasks about something else; OPEN-47 exists because the
director downloaded a paper an executor claimed to have read. **That is the reason this plan keeps
the same audit discipline and does not relax it for being a "cleanup" pass.**

✅ **Read this before touching anything in OPEN-46's scope.** The adopted fleet figure —
**157.1 kWh/m², pooled** — **is not in question in this plan and no task here may change it.**
Elevator energy is already simulated and already inside `equipment_eui_kwh_m2` and inside the total.
What is missing is a **reporting breakout**, not a load. T05 carries a hard numerical invariant to
guarantee that stays true.

🔴 **This plan closes no item on its own authority.** The director decides closure at the
checkpoints, against raw artifacts, never against an executor's report.

---

## 1. Hard rules for the executor

1. 🔴 **No cluster. No `srun`, no `ssh`, no `sbatch`.** Every task here is local. If a task appears to
   need the cluster, **stop and say so** — do not improvise a local substitute and report it as the
   measurement.
2. 🔴 **Never run `git commit`, `git push`, `git checkout <branch>`, `git reset`, or `git stash drop`.**
   Git is handled externally by the user. Read-only git (`log`, `show`, `diff`, `-S`) is fine.
3. 🔴 **Do NOT edit the register, the director prompt, the published-numbers board, or §10 of this
   document.** Executors run in parallel and concurrent writes lose each other's work. You write
   **your own named report file** and the source files your task names, and nothing else shared.
4. 🔴 **Never edit** root `main.py`, anything under `docs/docs_main/`, or any OVERVIEW / DESIGN doc.
5. 🔴 **No `.py` files under `docs/`, ever.** Analysis scripts go in `scripts/analysis/`.
6. 🔴 **Do not quote a fleet EUI other than `157.1 kWh/m²` (pooled).** `158.0` is superseded.
7. **A scan that finds nothing reports emptiness, and proves the scanner works.** Insert a deliberate
   positive into a scratch file, show the scanner catches it, remove it. **Zero without that control
   is not a result.**
8. **A count is not a cause.** Report causes.
9. **`**  Fatal  **` and `**  Severe  **` have TWO spaces.** This plan exists partly because of that.
   Never use the `has_fatal` column — it is measured wrong (OPEN-29).
10. 🔴 **No claim about an external document without the document.** If a task cites a paper, the PDF
    or HTML must be **downloaded to the scratchpad**, the matching string **quoted verbatim**, and the
    page number given. Every DOI must be **Crossref-verified** (`https://api.crossref.org/works/<doi>`).
    **"I could not retrieve it" and "the string is not in the document" are both good answers.
    A reconstructed-from-memory citation is a fabrication and will be caught** — that is precisely
    how OPEN-47 was opened.
11. **Say what you did not do.** An unfinished leg reported as unfinished is a good outcome. An
    unfinished leg reported as finished is the failure mode this arc exists to catch.
12. **Report your own numbers, not the register's.** Where this plan states a figure, treat it as a
    **precondition to reproduce**, not as an answer to restate. If your re-derivation disagrees with
    this document, **that disagreement is the finding** — report both, adjudicate neither.

---

## 2. File layout

| Purpose | Path |
|---|---|
| Executor reports | `docs/docs_ACTIVE/openings/extra/<TYPE>_open-NN_<slug>.md` |
| Analysis scripts | `scripts/analysis/openNN_<slug>.py` |
| Tabular evidence | `openubem/outputs/comparisons/openNN_<slug>.csv` |
| New library helper (T01) | `openubem/results/err_parse.py` |
| New unit tests (T01) | `tests/test_err_parse.py` |
| Scratch downloads (T07) | scratchpad only — **never** committed under `docs/` |

`<TYPE>` is `FIX_` when the task changes behaviour, `MEASUREMENT_` when it only measures,
`RESEARCH_` for the literature task.

---

## 3. Dependency decisions (pinned by the director — do not re-decide)

1. **The Severe/Fatal matcher becomes one shared helper, not N patched literals.** New module
   `openubem/results/err_parse.py`. Rationale: this is the **third** instance of the same bug; a
   third point-patch guarantees a fourth instance. The helper is regex-based and
   **whitespace-tolerant on both sides**, so it matches one-space and two-space forms alike.
2. **The helper lives under `openubem/`, not under `scripts/`.** `scripts/validation/` is not a
   package and its modules cannot be imported reliably; `v12_cell_pipeline.py` already imports
   `openubem.*` from inside its functions (`:125`, `:155`, `:204`), so the import path is proven.
3. 🔴 **The elevator breakout is implemented as an ADDITIVE, GUARDED change — never an unguarded
   one.** If the `Elevators:InteriorEquipment:Electricity` meter is absent from a SQL file (which is
   the case for every file the adopted run produced, unless T03 proves otherwise), the parser must
   emit `elevators_eui_kwh_m2 = 0.0` and **must not de-fold anything from equipment**. Rationale: the
   de-folding line in the archived copy is only correct when the meter exists. Applied blindly to old
   SQL it would subtract zero — harmless — but the guard must be **explicit and tested**, not
   accidental, because the failure mode if it is ever wrong is a silently changed published number.
4. **`total_eui_kwh_m2` is invariant. This is a hard gate, not an aspiration.** T05 must parse a real
   adopted-run SQL before and after its change and show **every EUI column identical**. If any column
   moves, T05 stops and reports rather than adjusting the expectation.
5. **`RESULT_I02` is archived paper trail and is amended by APPENDING a dated erratum at the end of
   the file.** Its original lines — including the fabricated citation at `:113` — are **not
   rewritten and not deleted.** Rationale: the register's own rule (strike and date, never erase) and
   the fact that the fabricated line is now evidence about how that document was produced.
6. **The code comment at `building_classifier.py:143` is corrected to say only what is established.**
   It may not name a source that T07 has not verified. If T07 finds nothing, the comment says the
   provenance is untraced. **Comment-only diff — no executable line may change.**

---

## 4. Facts with citations (verified by the director, 2026-08-12 — reproduce, do not trust)

**OPEN-45**
- `scripts/validation/v12_cell_pipeline.py:625` — `severes = [l.strip() for l in etxt.splitlines() if "** Severe **" in l]`, **one space**.
- `:622` — `_re.findall(r"(\d+)\s+Warning;\s*(\d+)\s+Severe", etxt)`. **This one works**, which is why the failure *counts* are sound and only the cause text is lost.
- Non-empty `error_summary` across all twelve adopted `04_simulation_manifest.parquet` (8,160 rows) = **0**.
- Live one-space sites already enumerated by the director (excluding `scratchpad/` and `docs_DONE/`):
  `scripts/validation/v12_cell_pipeline.py:625`, `run_v11_step5.py:79`,
  `v12_la_centre_fetch_step5.py:125`, `v12_la_centre_step5_fix.py:101`,
  `v12_la_rural_repair_472961100.py:335`, `v12_la_suburban_recover.py:396`,
  `v12_la_suburban_sql_repair_step5.py:73`, `v12_la_urban_repair_step5.py:355`,
  `v12_nyc_urban_recovery.py:258`, `scripts/cluster/make_manifest_from_cluster.py:47`,
  `scripts/diagnostics/t01_reproduce_degenerate.py:109`.
  **Two sites already handle both forms** and are the pattern to copy, not to change:
  `scripts/validation/phaseE_cpb_fixtures.py:177`, `scripts/diagnostics/t04_validate_way428643335.py:134`.
  ⚠️ **This list is the director's and is a starting point, not a closed set.** T02 re-derives it.

**OPEN-46**
- Live `openubem/idf/outputs.py:28-42` — `HVAC_METERS`, **13 entries, no elevator meter**.
- Archived `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/openubem/idf/outputs.py:40` — has the
  14th, `"Elevators:InteriorEquipment:Electricity"`.
- Live `openubem/results/parser.py:269` — docstring says *"sum of all 9 end-use EUIs"*; `:318-327`
  sums nine terms; **zero occurrences of `elevators_eui_kwh_m2`** in the live tree.
- Archived parser `:291-322` — reads the elevator meter, adds `elevators_eui_kwh_m2`, de-folds it out
  of equipment, sums **ten** terms, and states the total is invariant against the 9-way total.
- Live `openubem/results/carbon.py:68-77, 91-99` — nine `gwp_*` terms, **no `gwp_elevators_kgco2_m2`**.
- Live `openubem/idf/elevators.py` **is on the live path** and emits the lift motor as
  `ElectricEquipment` with `EndUse_Subcategory = "Elevators"`. ✅ **This is why no energy is missing.**
- `openubem/idf/outputs.py:78-83` — `Output:Table:SummaryReports / AllSummary` is written **only when
  `trim_hourly=False`**; `Output:SQLite / SimpleAndTabular` is written unconditionally (`:84`).
  **T03 exists because of this line: whether the adopted run's SQL carries the tabular
  End-Uses-By-Subcategory table is an empirical question, not a deducible one.**

**OPEN-47**
- `openubem/semantic/building_classifier.py:143` — `# E-R3-3: office size-tier bins (LBNL CBES 25,000 / 100,000 ft²; Hong et al. 2015)`; `_OFFICE_SMALL_MAX_M2 = 2322.0`, `_OFFICE_MEDIUM_MAX_M2 = 9290.0`.
- `docs/docs_DONE/BUGS/input-framework/deepResearch/RESULT_I02_archetype_classification_cascade.md:33` — Table 2, attributes the bins to **CityBES** (so the code's "CBES" is a name-swap).
- Same file `:113` — DOI `10.1016/j.enbuild.2015.04.035`. **Crossref-verified by the director: it
  resolves to Padilla et al., "A combined passive-active sensor fault detection and isolation
  approach for air handling units", Energy and Buildings 99, 214–219 — an unrelated paper.** The real
  Hong et al. CBES paper is **Applied Energy 159, 298–309**.
- Chen, Hong & Piette (2017), IBPSA BS2017: 8 pages, 21,520 characters of extractable text. The
  strings `2322`, `2,322`, `9290`, `9,290`, `25,000`, `100,000`, `Large Office` appear **zero times**.
- Arithmetic that does hold: 25,000 × 0.09290304 = 2,322.576; 100,000 × 0.09290304 = 9,290.304.

---

## 5. Task list

### T01 — OPEN-45: one whitespace-tolerant matcher, with a test that fails without it

**What.** Create `openubem/results/err_parse.py` exposing, at minimum:
`SEVERE_RE`, `FATAL_RE`, `WARNING_RE` (compiled, tolerant of any run of whitespace inside the
`** … **` delimiters and of leading indentation), `iter_severe(text) -> list[str]`,
`first_severe(text) -> str`, `count_severe(text) -> int`, `has_fatal(text) -> bool`. Then repoint
`scripts/validation/v12_cell_pipeline.py:625` at it.

**Why.** The substring `"** Severe **"` never occurs in a real EnergyPlus `.err` file, so
`error_summary` is `""` on every row of every manifest this pipeline has ever written — 8,160 rows in
the adopted run alone. The counts survive because a different regex parses them; the **cause text
does not**, which is exactly what the previous pass went looking for and could not find.

**How.**
1. Write the module. Docstring must state the two-space fact and cite this plan.
2. Write `tests/test_err_parse.py` with fixtures containing **the real two-space forms**
   (`**  Severe  **`, `**  Fatal  **`) and the one-space forms, and assert both match.
3. 🔴 **Non-vacuity control, and report it explicitly:** show that a test asserting on the real
   two-space fixture **fails** against the old one-space substring check, and passes against the new
   matcher. A green test that would also have been green before the fix proves nothing.
4. Repoint `v12_cell_pipeline.py:625` (import inside the function, matching that file's existing
   convention at `:125`/`:155`/`:204`). **Leave `:622`'s working count regex alone.**
5. Run `pytest tests/test_err_parse.py -q` and paste the full output.

**How to test.** The pytest output above, plus a demonstration on a **real** `.err` file found
anywhere on this machine: show `first_severe()` returning a non-empty string where the old check
returned `""`. If no real `.err` file with a Severe line exists locally, **say so** and use a byte
fixture instead — do not claim a live demonstration you did not run.

---

### T02 — OPEN-45: sweep the whole family, and answer whether the adopted run is recoverable

**What.** Two legs.
- **Leg A — the sweep.** Re-derive, independently of §4's list, every site in the **live** tree
  (`openubem/`, `scripts/`, `tests/` — **excluding** `scratchpad/` and `docs_DONE/`) that matches a
  hard-coded `** Severe **` / `** Fatal **` / `** Warning **` literal. Classify each row as
  **`load-bearing`** (on a path that produced or could produce an adopted artifact),
  **`one-off`** (a repair or diagnostic script for a specific building, already spent), or
  **`already-correct`** (handles both spacings). Repoint the **load-bearing** ones at T01's helper.
  **Leave the one-offs alone and list them** — rewriting spent scripts changes history for no gain.
- **Leg B — recoverability.** Answer, with evidence: **can `error_summary` be backfilled for the
  adopted run?** Search this machine for any surviving `eplusout.err` belonging to `phaseE_elevrb`.
  The previous pass established all six failed buildings' `work_dir`s exist and contain **0 files**;
  Leg B asks the same question for the other 8,154. **"No, the evidence is gone" is a complete and
  expected answer.**

**Why.** This is the third instance of the same bug. Patching one line and declaring it fixed is what
produced instances two and three.

**How.** One script, `scripts/analysis/open45_severe_literal_sweep.py`, writing
`openubem/outputs/comparisons/open45_severe_literal_sweep.csv` with columns
`path, line, literal, classification, action_taken, reason`. Non-vacuity per hard rule 7. Report in
`extra/FIX_open-45_severe-matcher.md`, covering **both T01 and T02**.

**How to test.** Every file you repointed must still import cleanly (`python -c "import ast,sys;
ast.parse(open(p).read())"` at minimum, and a real import where the module allows it). State the
before/after count of load-bearing one-space sites. **A single "after" number satisfies nothing.**

---

### T03 — OPEN-46: is the elevator breakout derivable from the adopted run's existing SQL? **EVIDENCE ONLY**

**What.** Determine, empirically, whether the adopted `phaseE_elevrb` SQL files contain enough
information to report elevator energy separately **without re-simulating anything**. Three
sub-questions, each answered from a real file:
1. Was the adopted run built with `trim_hourly=True` or `False`? Determine it **from the artifacts**
   (presence/absence of the `AllSummary` tabular tables and of hourly zone variables in the SQL), not
   from reading configuration.
2. Does the SQL's `TabularDataWithStrings` contain an **"End Uses By Subcategory"** table, and does
   that table carry an **`Elevators`** row under Interior Equipment?
3. Does the SQL's meter/`ReportDataDictionary` carry anything named for elevators?

**Why.** Decision 3 in §3 is written on the assumption that the meter is absent from old SQL. **That
assumption is the kind of thing this arc keeps catching people out on.** If the subcategory table is
present, the breakout is backfillable for the whole adopted fleet and OPEN-46 becomes much cheaper.
If it is absent, T05's guard is load-bearing and the adopted run keeps nine reported end-uses forever.

**How.** Sample **at least five SQL files from at least three different cells** under
`docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/` — locate them via the `sql_path`
column of `04_simulation_manifest.parquet`. Query with `sqlite3` directly. **Paste the actual table
names found and the actual rows**, not a summary of them. 🔴 **Make no fix and change no source file.**
If the SQL files are not on this machine, **say that plainly and stop the task** — do not substitute a
freshly generated SQL and report it as the adopted run's.

**How to test.** The pasted rows are the test. Report
`extra/MEASUREMENT_open-46_sql-subcategory-probe.md` + a CSV of every file probed and what it
contained.

---

### T04 — OPEN-46: the complete live-vs-archived divergence inventory, and every "10th end-use" claim **EVIDENCE ONLY**

**What.** Two inventories.
- **Inventory A — code.** Every divergence between the live tree and
  `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/openubem/` that relates to the elevator
  feature: `results/parser.py`, `idf/outputs.py`, `results/carbon.py`, `results/aggregator.py`,
  anything else that differs. For each: file, live state, archived state, and whether the divergence
  is **the feature missing** or **an unrelated drift** (the live tree has moved on since the archive
  in ways that have nothing to do with elevators — **do not report those as missing features**).
- **Inventory B — prose.** Every place in the live tree, `docs/docs_ACTIVE/`, and
  `docs/PROJECT_CHECKLIST.md` that describes elevators as an end-use, a "10th end-use", or otherwise
  implies a separate elevator reporting line exists. File, line, exact quote.
  **Do not edit any of them** — T05 or the director decides the wording.

**Why.** T05 cannot be scoped safely without A, and the director cannot decide what to correct
without B. Also: the previous pass established that three of five archived test twins had the
elevator **expectation removed rather than the feature added**. **Inventory A must state, for each of
those five test files, exactly which assertions differ** — that list becomes T05's restoration list.

**How.** `scripts/analysis/open46_elevator_divergence.py` →
`openubem/outputs/comparisons/open46_elevator_divergence.csv`
(`kind, file, live_state, archived_state, verdict`) and
`openubem/outputs/comparisons/open46_tenth_enduse_claims.csv` (`file, line, quote`).
Report `extra/MEASUREMENT_open-46_divergence-inventory.md`. 🔴 **No source file may be edited.**

**How to test.** Inventory A must be complete enough that a reader can predict T05's diff from it.
Non-vacuity for Inventory B per hard rule 7.

---

### T05 — OPEN-46: implement the breakout, guarded, with the total proven invariant

**Dispatched only after the director accepts T03 and T04.** Its exact shape depends on T03's answer.

**What.**
1. `openubem/idf/outputs.py` — add `"Elevators:InteriorEquipment:Electricity"` to `HVAC_METERS`
   (13 → 14), matching the archived copy.
2. `openubem/results/parser.py` — read that meter; emit `elevators_eui_kwh_m2`; de-fold it out of
   `equipment_eui_kwh_m2`; include it in `total_eui_kwh_m2`. 🔴 **Guarded per §3 decision 3: when the
   meter is absent, `elevators_eui_kwh_m2 = 0.0` and no de-folding occurs.** Update the docstring
   from "9 end-uses" to state both the 10-way breakdown and the guard.
3. `openubem/results/carbon.py` — add `gwp_elevators_kgco2_m2 = elevators_eui × f_elec`, with the
   same guard, and add it to the `nan` block at `:68-77`. **Check whether `gwp_total_kgco2_m2` needs
   the same de-folding treatment and say what you found before changing it.**
4. Restore the test expectations T04 lists: `tests/test_outputs.py` (13 → 14 meters),
   `tests/test_results_aggregator.py` (the two removed keys), `tests/test_step3_orchestrator.py`
   (the deleted `test_medium_office_idf_contains_elevator_equipment`), and make
   `tests/test_parser_elevators.py` pass.

**Why.** Because the project's own documents describe a reporting line that does not exist. The two
honest resolutions were *implement* or *retract*; the user asked for an implementation plan.
**Retraction of the prose is still needed for the adopted run** if T03 says the meter is absent from
its SQL — in that case the correct sentence is *"ten end-uses are reported for runs built after this
change; the adopted `phaseE_elevrb` baseline reports nine"*, and T05 writes exactly that into the
parser docstring. **It does not edit the checklist, the register or the board — the director does.**

**How.** 🔴 **The invariant gate, run before you report anything:** take a real adopted-run SQL, parse
it with the pre-change parser and with the post-change parser, and **diff every EUI column.**
`total_eui_kwh_m2` must be **bit-identical**, and with the meter absent so must every other column.
Paste both column dictionaries. **If any value moves, stop and report — do not adjust the
expectation.** Then run `pytest tests/test_parser_elevators.py tests/test_outputs.py
tests/test_results_aggregator.py tests/test_step3_orchestrator.py tests/test_elevators.py -q` and
paste the output. Then `pytest --collect-only -q` on the whole repo and report the collected count
(**1,990 before this task** — a drop is a regression you caused).

**How to test.** As above. Report `extra/FIX_open-46_elevator-breakout.md`.

---

### T06 — OPEN-47: the erratum, the citation audit, and the corrected code comment

**What.** Three legs.
- **Leg A — erratum.** Append a dated erratum block at the **end** of
  `docs/docs_DONE/BUGS/input-framework/deepResearch/RESULT_I02_archetype_classification_cascade.md`.
  🔴 **Append only. Do not rewrite, strike, or delete `:33`, `:113`, or any other original line.** The
  erratum records: the DOI at `:113` resolves to an unrelated paper (name it, with the Crossref JSON
  quoted); the real Hong et al. CBES citation is Applied Energy 159, 298–309; and the Table 2
  thresholds at `:33` are the origin of the code's values and are **not** externally corroborated.
- **Leg B — audit every other citation in that document.** For each reference it carries (Deru et al.
  2011, PNNL-23269, Sun et al. 2021, CTBUH, and any others), record **verified / unverified /
  fabricated** with the evidence. 🔴 **Hard rule 10 applies with full force: no verdict without a
  retrieval.** "Unverified — could not retrieve" is the correct verdict when retrieval fails, and it
  is **not** the same verdict as "fabricated". Put the tally in the erratum and in the report.
- **Leg C — the code comment.** Correct `openubem/semantic/building_classifier.py:143`. It currently
  names **CBES**; the document it derives from says **CityBES**; and per §3 decision 6 it may not
  claim a provenance nobody has verified. 🔴 **Comment-only diff.** Wait for T07's result before
  writing the final wording; if T07 finds nothing, the comment must say the external provenance is
  untraced and point at OPEN-47.

**Why.** A fabricated DOI in a paper-trail document is a finding about that document, not about one
line of it. Leg B is what turns a single catch into a bounded statement about the whole file — the
same move that turned "one governance gap" into six.

**How to test.** Leg B's table is the test; each row must carry a retrieval artifact or an explicit
retrieval failure. Leg C: `git diff` must show comment lines only. Report
`extra/FIX_open-47_citation-erratum.md`.

---

### T07 — OPEN-47: trace the thresholds to a primary source, or establish that none exists

**What.** Try to find a **primary, retrievable** source that defines an office size tiering at
**25,000 ft² / 100,000 ft²** (= 2,322.576 / 9,290.304 m²). Candidates, in the order the director
considers them most likely — **this list is a starting point, not a permission to stop at it**:
1. **CBECS** published size-category bin edges (EIA). Note the known limitation: CBECS bins **all**
   building types by floor area for sampling; it does **not** define office archetypes. A hit here
   establishes a **numeric** donor, not a **definitional** one, and must be reported as such.
2. **CityBES / CBES** papers by Hong, Chen, Piette et al. — including the real Applied Energy 159,
   298–309 that `RESULT_I02` mis-cited, and any CityBES documentation. ⚠️ **The 2017 BS2017 paper has
   already been searched and does not contain the numbers — do not re-report it as a hit.**
3. **DOE Commercial Prototype / Reference Building** documentation (Deru et al. 2011,
   NREL/TP-5500-46861; PNNL prototype documentation) — the small/medium/large office prototypes have
   published floor areas; establish whether any DOE document draws the *boundaries* at these values.
4. **ASHRAE 90.1** and any other standard that tiers offices by area.

**Why.** Two of this project's thresholds decide roughly a third of the labelled classification exam,
and their stated provenance has just been shown to be circular. Either there is a real source or
there is not, and **both answers are useful.**

**How.**
- Every document consulted is **downloaded to the scratchpad** and searched with a script, not by eye.
- For every candidate: report **found / not found**, the exact search strings used, and — when found
  — the verbatim sentence and page.
- 🔴 **Non-vacuity control, mandatory:** for each document you search and find nothing in, show your
  search finds a string you *know* is in it (a phrase from its own title or abstract). **A "not
  found" from an unproven searcher is worth nothing** — this is exactly how the fabricated claim in
  OPEN-47 got as far as it did.
- Every DOI Crossref-verified.
- 🔴 **You may not cite `RESULT_I02`, this plan, the register, or any OpenUBEM document as evidence.**
  They are the thing being checked. Citing them is the circularity that opened this item.

**How to test.** The non-vacuity controls are the test. Report
`extra/RESEARCH_open-47_threshold-provenance.md` with a candidate-by-candidate table and a single
plain-language verdict sentence at the top. ✅ **"No primary source found; the thresholds remain
untraced" is a complete, acceptable, and fully expected result. Do not manufacture a hit.**

---

## 6. Execution order and parallelism

| Executor | Tasks | Files it may write |
|---|---|---|
| **A** | T01 → T02 | `openubem/results/err_parse.py` (new), `tests/test_err_parse.py` (new), the load-bearing `scripts/**` sites, `scripts/analysis/open45_*.py`, its own report + CSV |
| **B** | T03 → T04 | **evidence only** — `scripts/analysis/open46_*.py`, its own reports + CSVs |
| **C** | T06 (Legs A, B) → T07 | `RESULT_I02…md` (**append only**), `scripts/analysis/open47_*.py`, its own reports. **Leg C waits for T07.** |
| **D** | T05 | `openubem/idf/outputs.py`, `openubem/results/parser.py`, `openubem/results/carbon.py`, the four named test files, its own report |

**A, B and C run in parallel — their write sets are disjoint. D runs only after the director accepts
T03 and T04.**

---

## 7. Stop-and-report points

- 🔴 **CP-1 — after T01–T04, T06 and T07.** Director re-derives: the non-vacuity control for T01;
  the sweep's before/after counts; **T03's pasted SQL rows, personally re-queried**; T04's inventory
  against the two trees; T07's "not found" verdicts against at least one document he downloads
  himself. **T05 is not dispatched until T03 is verified by the director, because T05's entire shape
  depends on it.**
- 🔴 **CP-2 — after T05.** Director re-runs the invariant gate personally on a different SQL file
  than the executor used, re-runs the four test files, and re-runs `--collect-only`. **A changed
  `total_eui_kwh_m2` at this gate means the change is reverted, not explained.**
- **CP-3 — close-out.** Director writes §10, the register amendment, the director prompt and both
  board copies. **No executor writes any of these.**

---

## 8. What closure requires for each item

| Item | Closes when | Does **not** close on |
|---|---|---|
| **OPEN-45** | The matcher is fixed, every load-bearing site is repointed, a test that would have failed before now passes, and Leg B has answered the backfill question either way. | "line 625 is fixed." |
| **OPEN-46** | The breakout exists and is guarded, the invariant gate is green, the restored tests pass, **and** every "10th end-use" claim is either true or corrected. | The code landing while the prose still overstates it. |
| **OPEN-47** | The erratum is written, every citation in `RESULT_I02` has a verdict, the code comment says only what is established, and the provenance question has a definite answer — **including "none found."** | Finding a source that "looks right" without a retrieval. **OPEN-47 stays open if T07's controls are not run.** |

---

## 9. Known risks

1. **T05 is the only task in this plan that can change a published number.** Every guard in §3 and §7
   exists for it. If the invariant gate is ambiguous, the correct action is to stop.
2. **T07 is under pressure to find something.** The task that preceded it fabricated a result under
   exactly that pressure. ✅ **The plan states in three places that "not found" is a success. Read
   hard rule 10 again before starting.**
3. **T02 could over-reach** by rewriting spent one-off repair scripts. The classification step exists
   to prevent that; one-offs are listed, not edited.
4. **T04's Inventory A can mistake unrelated drift for a missing feature.** The live tree has moved on
   since the archive for reasons that have nothing to do with elevators. Each row carries a verdict
   for that reason.

---

## 10. Progress log

*(Director-written. One entry per task: Artifacts / Deviations / Test status / Notes.)*

#### T01 — OPEN-45: one whitespace-tolerant matcher, with a test that fails without it — completed 2026-08-12

**Artifacts.** `openubem/results/err_parse.py` (new: `SEVERE_RE`/`FATAL_RE`/`WARNING_RE`, `iter_severe`,
`first_severe`, `count_severe`, `has_fatal`); `tests/test_err_parse.py` (new, 16 tests including
`TestNonVacuityControl`).

**Deviations.** None.

**Test status.** Director re-ran `pytest tests/test_err_parse.py -q` → **16 passed in 0.05s**.

**Notes — the non-vacuity control, re-derived by the director on the real file, not read from the
report.** On `docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/a2_run_multiplier/eplusout.err`,
whose real line is `'   ** Severe  ** Transformer Overloaded'`:

```
OLD one-space check : []
NEW first_severe()  : '** Severe  ** Transformer Overloaded'
```

🔴 **A correction to this project's own stated fact, established by the director censusing every
marker in all 64 real `.err` files on this machine.** The two-space rule we have been repeating is
only half right. The real spellings are:

| marker | real form | occurrences |
|---|---|---|
| Warning | `** Warning **` — **one** space both sides | 4,881 |
| Severe | `** Severe  **` — **one** space before, **two** after | 37 |
| Fatal | `**  Fatal  **` — two both sides | 1 |

**Consequence: a literal written for two-spaces-both-sides misses `Severe` exactly as badly as the
one-space literal did.** This is why the shared helper tolerates *any* run of whitespace rather than
enumerating spellings, and it is the reason to route future code through it instead of writing a
third literal.

---

#### T02 — OPEN-45: sweep the whole family, and answer whether the adopted run is recoverable — completed 2026-08-12

**Artifacts.** `scripts/analysis/open45_severe_literal_sweep.py` (carries its own non-vacuity control);
`openubem/outputs/comparisons/open45_severe_literal_sweep.csv` (25 classified rows); repointed
`scripts/validation/v12_cell_pipeline.py:625` and `scripts/cluster/make_manifest_from_cluster.py:47`
at `first_severe`; report `extra/FIX_open-45_severe-matcher.md`.

**Deviations.** Two further load-bearing sites were found **outside** Executor A's authorised
write-set and were correctly left untouched and flagged rather than edited silently:
`openubem/simulation/runner.py:140` and `tests/test_sim_integration.py:171`. See Notes.

**Test status.** Load-bearing one-space sites **2 → 0**, director-verified by reading both diffs.
Remaining 23 rows: 15 spent one-off repair/diagnostic scripts (listed, not edited), 8 already correct.

**Notes.** 🔴 **`tests/test_sim_integration.py:171` is a live, latent instance of the same bug in its
worse form.** It matches `"**  Severe  **"` (two spaces both sides) — which matches **0 of the 37 real
Severe lines on this machine**, director-verified. `openubem/simulation/runner.py:140` matches
`"**  Fatal  **"`, which does match the single real Fatal instance found, but is a bare literal rather
than the tolerant helper. **Both remain open and are carried into the register.**

**Leg B — is the cause backfillable? No, and the scope is wider than the six.** Director re-derived
independently, all rows not a sample: **12 adopted manifests, 8,160 rows; every `work_dir` exists and
every one is empty — 8,160 empty, 0 with any file.** Reported as a complete result, not backfilled
with a hypothesis.

---

#### T03 — OPEN-46: is the breakout derivable from the adopted run's SQL? — completed (STOPPED, correctly) 2026-08-12

**Artifacts.** `scripts/analysis/open46_*`; report `extra/MEASUREMENT_open-46_sql-subcategory-probe.md`.

**Deviations.** None. The executor was told to stop rather than substitute a freshly generated SQL for
the adopted run's, and it did exactly that.

**Test status.** All three sub-questions (`trim_hourly`, `End Uses By Subcategory`, elevator-named
meter) are **undetermined** — the adopted `.sql` files do not exist on this machine. Every `sql_path`
in the 12 manifests points under `%TEMP%\ubem_elev_rebaseline\`, and all twelve cell roots contain
**0 files**. A synthetic-SQL non-vacuity control confirms the probe query itself works, so the
"not found" is a real absence, not a broken scanner.

**Notes.** ✅ **The right outcome.** The one failure mode that would have made this task worthless —
generating a fresh SQL and reporting it as the adopted run's — did not happen.

---

#### T04 — OPEN-46: live-vs-archived divergence inventory — completed 2026-08-12, **and its headline was WRONG**

**Artifacts.** `openubem/outputs/comparisons/open46_elevator_divergence.csv` (12 rows);
`open46_tenth_enduse_claims.csv` (15 rows); report `extra/MEASUREMENT_open-46_divergence-inventory.md`.

**Deviations.** 🔴 **See Notes — the executor's central conclusion did not survive re-derivation, and
neither did the director's first attempt to check it.**

**Test status.** The mechanical half is correct and director-verified: live `parser.py` has no
`elevators_eui_kwh_m2`, live `outputs.py` has no elevator meter, live `carbon.py` has no
`gwp_elevators_kgco2_m2`, live `builder.py` **never calls `assign_elevators`**
(`git log --all -S assign_elevators -- openubem/idf/builder.py` is empty; the only commit ever to
touch the string is `ef19141`, which added the **archived** copies plus three orphan live files).
Of five archived test twins, three had the elevator expectation removed rather than the feature added.

**Notes — the correction, and it reverses the item.** T04 concluded, and the director initially
confirmed, that "the adopted run therefore contains no elevator load." **That is false.** The check
used was change in `equipment_eui_kwh_m2` between `phaseE` and `phaseE_elevrb` — flat for the 87
eligible nyc_urban buildings. **Flat is exactly what de-folding produces**: the load is added, then
subtracted back out of equipment into its own column, netting to zero.

**What the adopted run's own outputs actually contain, director-derived:**

- All 12 `phaseE_elevrb/*/05_results.csv` carry **`elevators_eui_kwh_m2` and
  `gwp_elevators_kgco2_m2`** columns.
- **3,561 of 8,160 rows are non-zero**, summing to 12,508.8 kWh/m². In nyc_urban exactly **87** rows
  are non-zero — precisely the 87 elevator-eligible buildings.
- Against `phaseE`, the **median** of `|Δtotal_eui − elevators_eui|` is **exactly 0** in nyc_urban and
  austin_centre. The whole total-column change *is* the elevator column.

✅ **So elevator energy IS in the adopted run and IS inside the published 157.1 kWh/m². No energy is
missing from the published number.**

🔴 **But the real defect is worse than the one the item was opened for: the adopted run cannot be
reproduced from this repository.** The code that produced it had elevators wired end-to-end; the code
in the repo today does not. The wiring existed in the working tree at run time and was never
committed — only the archived copies under `docs/docs_DONE/` were. **Registered as OPEN-48.**

**Method note worth keeping.** The wrong test was not a careless one; it was the natural one. It
failed because a de-folding transform is invisible in the column it de-folds *out of*. **Check the
invariant that the transform preserves (the total), not the column it moves energy between.**

---

#### T05 — OPEN-46: implement the breakout, guarded, with the total proven invariant — completed 2026-08-12

**Artifacts.** `openubem/results/parser.py` (`_ELEVATOR_METER`, guarded de-fold at `:346-349`, total
at `:364`); `openubem/idf/outputs.py:43` (14th meter); `openubem/results/carbon.py`
(`gwp_elevators_kgco2_m2`, guarded); `openubem/results/aggregator.py` (`_STEP5_COLS`, two column names
at the adopted-CSV positions); `tests/test_parser_elevators.py`, `tests/test_outputs.py`,
`tests/test_results_aggregator.py`; report `extra/FIX_open-46_elevator-breakout.md`.

**Deviations.** Three, all disclosed by the executor rather than found by audit:

1. **`aggregator.py` was touched** — flagged in advance in §6 as conditional, and genuinely required:
   without it the new columns never reach `05_results.csv`.
2. **`tests/test_step3_orchestrator.py` was left untouched.** Its
   `test_medium_office_idf_contains_elevator_equipment` asserts a *built IDF* contains the Elevators
   object — that is the load wiring, which is out of scope and would fail. Its deliberate absence is
   recorded in the test docstring. ✅ **Correct call.**
3. The task was re-scoped mid-flight by the director after T04's headline was overturned (see above).
   The executor **independently re-verified the correction before acting on it**, and found a
   confirmation the director had not: the adopted CSV header order matches the archived `_STEP5_COLS`
   position-for-position, `elevators` between `refrigeration` and `total`. So the restored shape is
   the one that actually produced the adopted files, not an invented one.

**Test status.** Director re-ran everything personally.

- Six-file run (`test_parser_elevators`, `test_outputs`, `test_results_aggregator`, `test_elevators`,
  `test_results_parser`, `test_results_carbon`): **147 passed**.
- `pytest --collect-only -q`: **2006 collected**. The plan's 1,990 figure was stale — A and C landed
  new tests in parallel. **No drop.**
- 🔴 **`tests/test_parser_elevators.py` passes 8/8 with every original assertion intact.** Nothing was
  weakened; only the docstring changed, to state that the file covers the reporting path only and
  that `builder.py` still never calls `assign_elevators`.

**Gate 1 — meter-absent invariance.** Executor: 7 real surviving `eplusout.sql`, every EUI and GWP
value compared as `float.hex()`, **all bit-identical**, the only dict difference being the two new
keys, both `0.0`. Director re-ran the same comparison independently, against `HEAD`'s parser loaded
side-by-side with the working-tree parser, **on a different SQL file than the executor used**:
```
GATE on: scratchpad\t3_cleanzoning_work\cross\sim\way\cc_cross\eplusout.sql
elevator meter present in this file: False
keys added by the change: ['elevators_eui_kwh_m2']  ->  {'elevators_eui_kwh_m2': 0.0}
shared keys compared: 12   BIT-IDENTICAL: True
total_eui_kwh_m2 hex: 0x1.d492d97e88c30p+7 | 0x1.d492d97e88c30p+7
```

✅ **Independently reproduced. Every pre-existing key bit-identical; the only change is the new key,
reading `0.0`.** One correction to the executor's framing: it reported 7 usable SQL files; the
director's sweep found **348 of the 940 repo-wide `eplusout.sql` parse with data**. The executor's
criterion was stricter than it needed to be. The gate result is unaffected.

**Gate 2 — non-vacuity, meter present.** A 12,000 kWh `Elevators:InteriorEquipment:Electricity` Run
Period row injected into a copy of a real SQL: elevators → 3.5294117647058822; equipment
63.73196294400685 → 60.20255117930097 (Δ exactly the elevator EUI); `|total − Σ(10 end-uses)|` =
**0.0**; `gwp_total` Δ = **0.0**. Total moves **2.84e-14 (1 ULP)** between the absent and present
paths — pure float re-association, **reported by the executor rather than hidden**. The absent path,
which is the one every existing artifact travels, is bit-exact.

**Notes.** The guard is the whole point and it is implemented as specified: the column is *always*
set, and `if elevators_kwh:` gates the de-fold. The archived parser subtracts unconditionally at
`:306`; this one does not. **The physical load was NOT re-wired: `openubem/idf/builder.py` was never
opened and no `assign_elevators` call was added anywhere.** Anything simulated from the live tree
today still emits no elevator equipment and reports `0.0`. **That restoration is a user ruling, not an
executor's call — see OPEN-48.**

---

#### T06 — OPEN-47: the erratum, the citation audit, and the corrected code comment — completed 2026-08-12

**Artifacts.** Append-only erratum at the end of
`docs/docs_DONE/BUGS/input-framework/deepResearch/RESULT_I02_archetype_classification_cascade.md`
(director-verified **64 insertions, 0 deletions** — nothing rewritten); comment-only correction at
`openubem/semantic/building_classifier.py` (now `:159`; the plan's cited `:143` had drifted, and the
executor anchored on the constant names instead of the line number and said so); report
`extra/FIX_open-47_citation-erratum.md`.

**Deviations.** One, disclosed rather than silently applied: §3 anticipated the erratum would record
that the thresholds are "not externally corroborated." T07 ran first and **found corroboration**, so
the executor wrote what was true and flagged the disagreement with the plan's anticipatory text.
✅ **Correct — a permanent document must not carry a stale claim because a plan predicted it.**

**Test status.** Director-verified the classifier diff is docstring-and-comment only:
`_OFFICE_SMALL_MAX_M2 = 2322.0` and `_OFFICE_MEDIUM_MAX_M2 = 9290.0` are unchanged and no executable
line moved.

**Notes — the audit found more than the one known fabrication.**

- **A second fabricated DOI**, previously unflagged: Sun et al. 2021 cited as
  `10.1016/j.enbuild.2020.110586`. **Director Crossref-checked it personally: HTTP 404, it does not
  resolve at all.** The real DOI is `10.1016/j.enbuild.2020.110603` (*Prototype energy models for data
  centers*, Energy and Buildings 231) — director-verified. The content was otherwise transcribed
  correctly, so this is a locator failure, not an invented finding.
- **A systemic wrong-locator pattern**: every Table-1 row sourced to Deru et al. (2011) cites
  "Section 3.x.x, Table 3-1, p.9" — **a table that does not exist in that report**, whose real
  structure is flat sections 1.0–8.0 with Tables 1–42. The actual data is Table 13, p.19, and **the
  numbers themselves are correct.**
- PNNL-23269's HighriseApartment content (84,360 ft², Section 3.2.1) is **not in that document at
  all**. Two further references have dead links to otherwise-real resources.

---

#### T07 — OPEN-47: trace the thresholds to a primary source — completed 2026-08-12, **source FOUND**

**Artifacts.** `scripts/analysis/open47_threshold_search.py` (mandatory non-vacuity control per
candidate); six downloaded documents + Crossref JSON in the session scratchpad; report
`extra/RESEARCH_open-47_threshold-provenance.md`.

**Deviations.** The plan was written expecting "no source exists." It does. The executor reported the
finding rather than the expectation.

**Test status — director re-derived the headline personally, by opening the PDF himself.** This task's
predecessor fabricated exactly this kind of claim, so the verification was done from scratch, not read:

```
chen2017_apenergy205_citybes_retrofit.pdf — 36 pages
  p19 [2322] ... Small office (<2322 m2 and <= 3 floors) 173 148 95 ...
  p20 [2322] ... Medium office* (2322 to 9290 m2, <= 5 floors) 149 478 290
               Large office (>9290 m2 or >=6 Floors) 279 6,153 4125 ...
hong2015_apenergy159_cbes.pdf — 13 pages — total hits: 0
```

DOI `10.1016/j.apenergy.2017.07.128` Crossref-verified by the director → *Automatic generation and
simulation of urban building energy models based on city datasets*, **Applied Energy 205, 323–335**.
Exactly the paper claimed.

**Notes.**

- ✅ **The source is real: Chen, Hong & Piette (2017), Applied Energy 205, Table 1.** The 2,322 /
  9,290 m² bins appear verbatim. The code's credit to "LBNL CBES … Hong et al. 2015" was wrong on both
  counts — director-verified that Hong 2015 contains **zero** occurrences of either number.
- ⚠️ **Caveat the executor stated and which must travel with the finding:** the Chen 2017 table is
  CityBES's own case-study classification, **not a citation to an external standard.** It is a real,
  verified, definitional source for CityBES — not proof of a DOE/PNNL/ASHRAE/CBECS lineage.
- 🔴 **A divergence the executor understated and the director confirmed from the quoted text: the
  source's rule is area AND floor count** — `<2322 m² and ≤3 floors`, `2322–9290 m² and ≤5 floors`,
  `>9290 m² or ≥6 floors`. **Our classifier at `building_classifier.py:175-177` tests area only; the
  floor-count condition was dropped.** Not adjudicated here. **Registered as part of OPEN-47, which
  stays open.**
- CBECS 2018 does contain 25,000/100,000 ft² bin edges, but as general all-building bins — a numeric
  coincidence, not an office-specific source. ASHRAE 90.1 **could not be retrieved** (paywalled) and
  is reported as a retrieval failure, **not** as "not found." ✅ The distinction was the point of
  hard rule 10.

---

#### Close-out — completed 2026-08-12

**What the three items did.** None closed. All three are better understood, one is materially
reversed, and **one new item (OPEN-48) is opened by the audit — again, by checking a result rather
than by running a task, for the sixth consecutive pass.**

| Item | State | Why it does not close |
|---|---|---|
| OPEN-45 | advanced | The matcher is fixed and shared, but two live sites remain outside the executor's write-set, one of them (`tests/test_sim_integration.py:171`) a latent instance of the same bug. |
| OPEN-46 | **reversed, then advanced** | The reporting path is restored and gated. The premise was wrong: nothing was missing from the published number. What is missing is reproducibility → OPEN-48. |
| OPEN-47 | advanced | The source is found and the comment corrected, but the area-only vs area-and-floors divergence is unadjudicated, and two fabricated DOIs plus a systemic wrong-locator pattern remain in the source document. |

**Four executor headlines went out; three survived re-derivation and one did not.** T04's did not, and
**the director's own first check of it was wrong in the same direction** — recorded here rather than
quietly corrected, because the failure mode (checking the column a transform moves energy *out of*)
is the transferable lesson.

**Behaviour worth restating in the next plan's hard rules, because all of it was specified and all of
it happened:** T03 stopped rather than substitute a fresh SQL for the adopted run's; C reported a
found source against a plan that predicted none, and separately reported a retrieval failure as a
retrieval failure rather than a null result; D refused a test restoration that was out of scope,
reported a 1-ULP movement it could have hidden, and independently re-verified a director correction
before acting on it; A flagged two out-of-scope sites instead of editing them.

