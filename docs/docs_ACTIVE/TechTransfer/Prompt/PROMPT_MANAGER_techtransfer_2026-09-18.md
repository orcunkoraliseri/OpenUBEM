# PROMPT MANAGER — TechTransfer arc (idf_reader → OpenUBEM)

> **Written:** 2026-09-18, by the manager session that closed block 5 / lane J.
> **Covers:** the whole arc, blocks 1–5, from the report `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`.
> **How to use:** paste everything below the horizontal rule into a **fresh** session that will act
> as manager for this arc. Update this file in place at the close of each block — do not supersede it
> with a new dated copy.
> **Measured at the time of writing:** the eight TechTransfer test files pass, `108 passed`
> (`python -m pytest tests/test_scenario_measures.py tests/test_pv_injection.py tests/test_compliance_audit.py tests/test_prep_gate.py tests/test_layout_assigner_fit_check.py tests/test_parser_version_robustness.py tests/test_envelope_patcher_windows.py tests/idf/test_ground_temperature.py -q`).

---

## 0. Ownership — read this before anything else

`C:\Users\o_iseri\Desktop\idf_reader` was written by the user for a postdoc position and **is not the
user's project**. OpenUBEM belongs to the user 100 %.

Consequences, absolute:

- **Nothing is copied.** Not code, not docs, not parameter tables, not IDFs, not naming schemes.
  The report and every plan under it are **re-implementation guidance**: take the method, then source
  every number from a public standard and cite it.
- **No borrowed vocabulary.** The retrofit packages `EEM1`–`EEM4` and their tier structure belong to
  that project; the user ruled them out by name. Measures here are named for what they do
  (`thermostat_setback`, `infiltration_tightening`).
- idf_reader may be **read** and **measured** (its prototype IDFs are the realistic test targets —
  see §6), but no file from it ever enters this repo and no test may point at it.

## 1. Role of the session receiving this

**Manager / director.** Reads docs, writes and audits plan docs, dispatches executors, rules on open
questions. **Never writes feature code.** Feature code is written by fresh Sonnet executor sessions,
one brand-new session per dispatch, `model: "sonnet"` passed explicitly.

All state lives in the plan doc on disk, never in an agent's conversation history.

## 2. Where the arc stands (2026-09-18)

Five plan docs, all in `docs/docs_ACTIVE/TechTransfer/implementation/`. Report item → lane → status:

| Report item | Lane / block | Status |
|---|---|---|
| T1 ground coupling | A, block 1 | **Done.** `Site:GroundTemperature:BuildingSurface` written explicitly at 18 °C; proven byte-neutral (A03). |
| T2 skip-when-better windows | B, block 1 | **Done.** Guard behind `ENVELOPE_PATCH_SKIP_WHEN_BETTER` (default OFF). |
| T3 engine-version traps | C, block 1 | **Partly done.** C01–C03 landed (loud absence, version fence). **C04 (per-archetype per-end-use regression fixture) was never started** — see §4. |
| T4 compliance audit | G, block 3 | **Done.** `openubem/idf/compliance.py`, read-only pre-simulation audit + fleet census. |
| T5 retrofit scenario layer | J, block 5 | **Done, lane closed.** See §3. |
| T6 geometry-aware PV | H, block 4 | **Done.** `openubem/idf/pv.py`, library only, nothing calls it. |
| T7 two-phase prep/sim | F, block 2 | **Done.** Prep gate behind `PREP_ABORT_ON_FAILURE` (default OFF). |
| T8 chosen vs inherited | D02, block 1 | **Done.** `docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md`. |
| T9 prototype-vs-plot fit check | E, block 2 | **Done**, incl. E04/E05 re-measure against the scale factor the builder actually applies. |
| T10 AirflowNetwork landmine | D01, block 1 | **Done.** Registered in the debug reference. |
| T11 benchmark anchors / heat pumps | — | **Parked by design.** Waits for a Canadian district case or a heat-pump scenario. Nothing to do. |

**Block 5 / lane J result, in detail** (`openubem/data/scenarios/measures.json`, applier
`openubem/scenarios/measures.py`, tests `tests/test_scenario_measures.py`, 70 tests):

- `lighting_power_density` — **active**. 6.0 W/m², ASHRAE 90.1-2022 §9.3.2; scoped to six office
  archetypes, any other archetype is gated out rather than approximated.
- `envelope_u_upgrade` — **withdrawn**, on the record with a reason. Its targets were byte-identical
  to the code baseline OpenUBEM already applies, so it was a guaranteed no-op on its own archetype
  and a baseline leak on any other.
- `thermostat_setback` — **active**. 5.5556 / 2.7778 °C deltas, ASHRAE 90.1-2022 §6.4.3.3.2.
- `infiltration_tightening` — **active**. ASHRAE 90.1-2019 Addendum t §11.5.3 formulas, target
  0.0017 m³/s·m² at 75 Pa from §5.4.3.1.1. **Honest coverage limit that must be quoted with any
  saving:** only `Flow/Area` and `Flow/ExteriorWallArea` objects are covered; `Flow/Zone` and
  `Flow/ExteriorArea` have no formula in the cited clause and are declined by design, which is the
  majority of infiltration objects in today's prototype library.

## 3. Everything new is OFF, and nothing is wired into the build path

Four flags, all `False` in `openubem/config.py`: `ENVELOPE_PATCH_SKIP_WHEN_BETTER` (:112),
`PREP_ABORT_ON_FAILURE` (:123), `PV_INJECTION_ENABLED` (:223), `SCENARIO_LAYER_ENABLED` (:224).

`openubem/idf/pv.py` and `openubem/scenarios/` are **libraries that nothing calls**. That was a
deliberate ruling (SR-H2, block 4), not an oversight. **Do not wire them up without the user asking.**
No published OpenUBEM number has moved in this whole arc.

## 4. Must not start without the user asking

- **C04**, the per-archetype per-end-use regression fixture (block 1).
- The pre-existing **Warehouse `auto`-mode IDF failure** — known, out of scope.
- **D9**, the prototype IDF library that lives inside idf_reader.
- Rewriting OpenUBEM's existing table-driven **envelope applier**.
- **Racking / `Shading:Building:Detailed`** for PV, and inter-row shading.
- Writing anything into **`05_results`**.
- Wiring `pv.py` or `openubem/scenarios/` into the build path.
- **Any EnergyPlus run** for this arc. Nothing here has been simulated; that is correct and
  intentional. If simulation is ever approved: it is never sequential — `sbatch --array ... %32` on
  Speed, or a local pool of 20.

## 5. Standing rules this arc earned — carry them forward

These are not style preferences. Each one was written after a defect that a fully green test suite
had failed to catch.

1. **Audit by measurement, never by report.** Re-run the executor's own commands yourself, then run
   the artifact against a **real DOE prototype IDF** and read the numbers. Both of the two serious
   defects in this arc (J03-D1, J04-D1) were found this way, and in both cases the executor's suite
   was 100 % green.
2. **A measure that edits a `Schedule:Compact` ships with at least one test whose schedule is copied
   verbatim from a real prototype block, not hand-written. A measure with only synthetic schedule
   tests is not tested.**
3. **Where a cited standard states a quantity directly, no OpenUBEM convention may restate it.** A
   convention is admissible only for a case the standard does not cover at all, and the measure must
   **gate** what it cannot cite rather than reach it through a convention. J04-D1 was exactly this
   failure, and the fix was to delete the invented rule, not to tune it.
4. **Withdraw, don't tune.** A measure that cannot be defended ships `"status": "withdrawn"` with a
   written `withdrawn_reason`, and is restored only by a separate task after re-verification.
   `apply_measure` short-circuits a withdrawn measure, so tests of corrected logic must call the
   applier internals directly.
5. **The manager owns its own spec's defects.** J04-D1 came from the manager's own task spec; the
   audit note says so. Attribute honestly, or the next spec repeats it.
6. **Register every solved error** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before
   closing the task, and **search it before debugging anything**.
7. **Fail closed with a named gate.** Every declined case gets its own gate name in the measure's
   `gates` list; unknown input is never approximated.
8. **Close a plan doc past ~1,100 lines** and carry remaining scope into the next block. Block 5's
   doc reached 1,217 lines and is due for this — see §7.

## 6. Dispatch recipe, and the traps that have actually bitten

**Recipe.** One brand-new Sonnet session per task. Dispatch a verb and exact commands, never a
question. Cap every command's output (`head -30`, `grep -c`, `--stat`). Split long agents at task
boundaries. **Never re-check a finding with a second agent** — re-run the one command yourself.

**Audit target.** The realistic measurement file used throughout lane J:
`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`
— read and measured by the manager only, never copied, never referenced by a test.

**Traps to hand to every executor, verbatim:**

- Windows paths inside `python -c` raise
  `SyntaxError: (unicode error) 'unicodeescape' codec ... truncated \UXXXXXXXX escape`. Use raw
  strings, ASCII only.
- `/tmp/...` gives `FileNotFoundError` — Git Bash `/tmp` is unresolvable by Windows Python. Use the
  session scratchpad with a Windows path.
- `WebFetch` fails with `getaddrinfo ENOTFOUND`: the executor sandbox has **no outbound DNS**. Any
  standard or source must be fetched by the manager and pasted into the task spec.
- Bash heredocs into a file have failed here with
  `unexpected EOF while looking for matching '`. Write the fragment with the Write tool, then
  `cat fragment >> target`.
- PDFs: `WebFetch` cannot parse the standards PDFs, and `Read` on a saved PDF needs poppler
  (`pdftoppm is not installed`). Extract text with `pypdf` into the scratchpad and grep it.

**Semantics an executor gets wrong unless told** (all measured, all cost a re-do):

- A `Schedule:Compact` `Until: HH:MM, value` entry spans from the **previous** until-time to its own.
  Testing the entry's end time to decide occupancy is wrong, and DOE prototype workday until-times
  (05:00/06:00/07:00/22:00/24:00) put nothing inside a 07:00–18:00 window.
- DOE prototypes write `For SummerDesignDay` **without a colon**, so `startswith("for:")` silently
  misses every design-day block.
- A temperature **difference** converts ×5/9 with no 32° offset.
- Clone shared schedules, never mutate them; cap the clone at `len(original.fieldvalues)` because
  eppy's `fieldnames` returns the IDD extensible maximum (10001).

## 7. Decision resolved 2026-09-18

User answered: close block 5, open block 6, **housekeeping only** — no task in block 6 is authorized
yet. `PLAN_techtransfer-block5-2026-09-17.md` carries a 🔒 CLOSED banner naming its successor.
`PLAN_techtransfer-block6-2026-09-18.md` is open, parked, empty progress log — its §2 lists every
remaining item (C04, wiring PV, wiring scenarios, flipping any of the four flags, any EnergyPlus run,
plus the pre-existing out-of-scope items) and the gate on each: a specific user ask, item by item.
Nothing starts in block 6 without that ask.

## 7a. Execution authorized 2026-09-18 — run block 6's list consecutively

User instruction: run the block 6 list in order, no per-item pick needed. Recorded at
`PLAN_techtransfer-block6-2026-09-18.md` §2a with the execution order (C04 → PV validation run → PV
build-path wiring → scenario wiring → remaining flag flips → any fleet-scale EnergyPlus run). Two
items in that order still need one specific input, not a style choice, and are not skipped by this
authorization: reversing SR-H2 (PV wiring) needs the one measured EnergyPlus proof it names; wiring
`openubem/scenarios/` needs the user's packaging-design pick (block 5 §1b) before a campaign can be
built at all. Neither blocks the other items.

**Dispatched 2026-09-18:** C04, fresh sonnet executor, task spec in block6 §2a. Awaiting report;
manager audits before item 2 starts.

## 8. Executor kickoff prompt (send verbatim, adjust the range)

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\TechTransfer\implementation\PLAN_techtransfer-blockN-2026-09-17.md.
Execute T<start> through T<end> in order. Stop at the first checkpoint after T<end>,
append progress log entries (one per completed task) under the progress-log section of that doc,
run any standalone tests called for in the plan, and report results before continuing.
Do not propose alternatives — execute the plan. If the DESIGN is ambiguous, STOP and quote the conflict.
```

Start narrow (1–2 tasks) with a new executor; widen once it runs cleanly.

## 9. File map for this arc

- Report: `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`
- Chosen vs inherited: `docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md`
- Plans: `docs/docs_ACTIVE/TechTransfer/implementation/PLAN_techtransfer-block{1..5}-2026-09-17.md`
  (block 5 🔒 CLOSED), `.../PLAN_techtransfer-block6-2026-09-18.md` (open, parked)
- Code added: `openubem/idf/ground.py`, `openubem/idf/compliance.py`, `openubem/idf/pv.py`,
  `openubem/scenarios/measures.py`, `openubem/data/scenarios/measures.json` + `PROVENANCE.md`
- Code touched: `openubem/config.py`, `openubem/geometry/envelope_patcher.py`,
  `openubem/geometry/layout_assigner.py`, `openubem/idf/builder.py`,
  `openubem/simulation/parallel.py`
- Tests added: `tests/test_scenario_measures.py`, `tests/test_pv_injection.py`,
  `tests/test_compliance_audit.py`, `tests/test_prep_gate.py`,
  `tests/test_layout_assigner_fit_check.py`, `tests/test_parser_version_robustness.py`,
  `tests/test_envelope_patcher_windows.py`, `tests/idf/test_ground_temperature.py`
- Error register: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
