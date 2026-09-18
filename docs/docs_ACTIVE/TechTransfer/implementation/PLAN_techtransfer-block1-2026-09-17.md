# PLAN — Technology-transfer block 1 (items 1–5)

**Slug:** `techtransfer-block1`
**Date opened:** 2026-09-17
**Manager:** Opus session (this plan is manager-authored; executors append to §8 only)
**Source report:** `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md` §5, items 1–5
**Scope:** T1 (ground coupling), T2 (window traps / skip-when-better), T3 (result-parsing + version
robustness), T8 (chosen-vs-inherited tagging), T10 (AirflowNetwork debug entry).
**Not in scope:** T4, T5, T6, T7, T9, T11. Do not start them.

---

## 2. Hard rules for the executor

1. **Execute this plan. Do not propose alternatives.** If the plan is ambiguous, STOP and quote the
   conflicting lines.
2. **Stay in your lane's file list (§3).** Four lanes run in parallel on disjoint files. Touching a file
   owned by another lane is a merge conflict and a plan violation. If you need a change in another
   lane's file, STOP and report it.
3. **Measure before you change.** Every lane begins with a census task whose only output is numbers.
   No behaviour change may be committed before its census is reported.
4. **No number may change silently.** If any task moves a simulated result, STOP at the nearest
   stop-and-report point (§7) and report the size of the move with the population it was measured on.
   The user decides whether to keep it.
5. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, or `docs/docs_main/`, `docs/docs_stepN/`.
6. **No code comments by default** (project convention). Rationale goes in the progress log, not the source.
7. **No new files beyond those listed in §3.** No helper scripts left in the repo; scratch work goes to
   the session scratchpad.
8. **Multiple EnergyPlus runs are never sequential.** Any task needing more than one simulation uses a
   local process pool (20 concurrent) or a Speed `sbatch --array` at `%32`. A `for idf in …: run()` loop
   is a plan violation.
9. **Append one progress-log entry per task to §8** in the given format, before reporting back.
10. **After solving any error, register it** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
    in the house format. Lane D owns that file — every other lane hands its entry text to the manager
    in its report instead of editing the file.

---

## 3. File layout — lane ownership

| Lane | Owns (may edit) | May read | New files allowed |
|---|---|---|---|
| **A — ground** | `openubem/idf/builder.py`, `openubem/idf/ground.py` (new), `tests/idf/test_ground_temperature.py` (new) | all | the two listed |
| **B — windows** | `openubem/geometry/envelope_patcher.py`, `tests/test_envelope_patcher_windows.py` (new) | all | the one listed |
| **C — results** | `openubem/results/parser.py`, `openubem/config.py`, `tests/test_parser_version_robustness.py` (new) | all | the one listed |
| **D — docs** | `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, `docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md` (new) | all | the one listed |

No lane edits `openubem/idf/surfaces.py`, `openubem/geometry/layout_assigner.py`, or any file under
`openubem/validation/`. If a lane concludes one of those must change, STOP and report.

---

## 4. Dependency decisions (pinned — do not revisit)

- **D1. The ground temperature value stays 18 °C.** EnergyPlus already applies 18 °C for every month
  when no `Site:GroundTemperature:BuildingSurface` object exists. The purpose of Lane A is to make that
  value **explicit and cited**, not to change it. An "undisturbed soil temperature" replacement is
  explicitly rejected: under a heated building the slab-adjacent soil sits near indoor temperature, and
  substituting an undisturbed profile makes the model worse, not better.
- **D2. Lane A must not change a single simulated number.** The acceptance test for Lane A is
  *byte-identical end-use results* before and after, on a sample. A non-zero delta is a bug in the
  change, not a finding, unless it comes from the FCfactorMethod object — see D3.
- **D3. `Site:GroundTemperature:FCfactorMethod` is NOT to be added in this block.** Where
  `GroundFCfactorMethod` surfaces exist (they do, in the `layout_assign` prototype library), EnergyPlus
  derives that series from the weather file. Writing it explicitly *would* move results. Lane A
  censuses it and reports; adoption is a separate user decision.
- **D4. Skip-when-better is a config flag, default OFF.** No default behaviour change in this block.
- **D5. EnergyPlus stays pinned at 23.1** (`openubem/config.py:69`). Lane C does not add multi-version
  support; it adds the checks that make a future version change visible instead of silent.
- **D6. Plain `"ground"` boundary condition stays.** The OSM-built path writes layered floors on
  `"ground"`; that is the better model and is not replaced by F-factor floors.

- **D7. SR-C answered 2026-09-17: C02 is WITHDRAWN; C03 proceeds instead.** Lane C's C01 audit found 24
  selectors that yield a silent `0.0` on absence. A zero-check over the delivered fleet
  (`docs/validations/overAll/results/open48_refleet/*/05_results.csv`, 8,160 rows, 12 folds) shows those
  zeros are overwhelmingly *legitimate physical absence*, not lost data: `pumps_eui_kwh_m2` is exactly 0
  for 7,620/8,160 buildings, `cooking_eui_kwh_m2` for 8,020, `refrigeration_eui_kwh_m2` for 8,149,
  `dhw_gas_eui_kwh_m2` for 6,492, `elevators_eui_kwh_m2` for 4,593. Raising on absence would abort the
  large majority of the fleet; a "not present" marker would mark ~94 % of rows and carry no signal.
  The failure mode C02 was meant to catch — a meter name that silently changes between EnergyPlus
  versions — is caught more cheaply and more precisely by C03's version fence, because the vocabulary
  of meter names is fixed by the pinned engine version. C02 is therefore not implemented in this block.
  Not resolved by this ruling and explicitly left open: `heating_eui_kwh_m2` is exactly 0 for 4 buildings
  and `cooling_eui_kwh_m2` for 32 — those are not plausibly legitimate and belong to a separate
  investigation, not to this block.

- **D8. SR-B answered 2026-09-17: B03 proceeds, clamp only, no orphan fix.** Lane B's B01 census over
  the 25-IDF prototype library resolved 23 of 28 archetypes (4 data-centre archetypes carry no windows;
  SuperMarket uses detailed glazing layers, not `WindowMaterial:SimpleGlazingSystem`, so no U/SHGC could
  be extracted). Of N = 496 resolvable archetype/prototype window pairs, **264 (53.2 %) receive a higher
  (worse) installed U-factor**, **222 (44.8 %) a higher (worse) SHGC**, and **112 (22.6 %) are worse on
  both at once**; delta-U spans -2.7827 to +1.4308 W/m2K (median +0.0678), delta-SHGC -0.32 to +0.19
  (median 0.0). The trap is therefore real and common, not an edge case, so the skip-when-better clamp is
  built - but it stays default **OFF** per D4, so this block changes no published number.
  B02 found **zero** `WindowShadingControl` objects across all 25 prototype IDFs; verified independently
  by the manager (a `python` count over `BASELINE_IDF_DIR`: 25 files, total 0). The orphaned-shading trap
  does not exist in this library, so B03 adds the fail-loud check only and **no** orphan fix, exactly as
  the B03 task text allows. A `config.py` entry for the flag is owed to Lane C and is *not* created here.

- **D9. Recorded, not actioned in this block: the prototype IDF library lives outside OpenUBEM.**
  `openubem/config.py:47-53` resolves `BASELINE_IDF_DIR` to
  `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231` - a directory inside the
  other project. OpenUBEM cannot claim to stand alone while its baseline geometry is read from there. This
  is pre-existing, not introduced by this block, and no lane touches it. It needs its own decision
  (vendor the library into OpenUBEM under a clear licence, or rebuild it from the public DOE/NREL
  prototype set) before OpenUBEM is published or handed over.

- **D10. C03 accepted with one deviation; the fence call site is owed a move.** C03's task text asked for
  the check *at the point where prototype IDFs are opened*. That point is `openubem/idf/builder.py:272`,
  which Lane A owns, so Lane C correctly stopped and put the check in `openubem/config.py` instead, where
  `validate_prototype_library_versions()` runs eagerly at import (config.py:111). Measured: whole-library
  validation over the 25-file library costs 0.33 s of total `import openubem.config` time, and the call is
  guarded on `directory.exists()` so it is a no-op wherever the external library is absent. Accepted as-is
  for this block - it passes cleanly on today's library and changes no simulated number. Owed follow-up
  once Lane A releases `builder.py`: call `assert_prototype_idf_version()` on the single file being opened
  at builder.py:272 and drop the eager whole-library sweep, so an off-version IDF fails where it is used
  rather than breaking every import of `openubem.config`.
- **D11. B03 accepted as delivered; no behaviour change is possible today.** `skip_when_better` defaults
  to `False` on `patch_envelope()` (envelope_patcher.py:132) and the sole production call site,
  `openubem/idf/builder.py:557`, does not pass it, so the unconditional-overwrite path is byte-identical to
  before. Re-run by the manager, not taken on trust: 22 passed (9 new + 13 pre-existing). The orphaned
  shading-control guard is fail-loud only, correct per D8, since B02 counted zero `WindowShadingControl`
  objects library-wide. Still owed to Lane C: a `config.py` entry (e.g. `ENVELOPE_PATCH_SKIP_WHEN_BETTER =
  False`) so builder.py:557 can read and pass the flag; until that exists the flag is unreachable from a run.
- **D12. Lane A accepted; A03 measured zero delta, and the census exposes a second ground model.** A02 wires
  `add_ground_temperature(self.idf)` into `BuildingIDF.__init__` (builder.py:288) writing one
  `Site:GroundTemperature:BuildingSurface` at 18.0 degC for all twelve months, idempotent. A03 compared 19
  buildings before/after over 456 building x end-use pairs: max absolute difference 0.0 kWh, max relative
  difference 0.0 - D2 satisfied. Manager re-ran `tests/idf/ tests/test_idf_builder.py`: 55 passed. One
  Warehouse (auto mode) failed identically in both variants with the same pre-existing fatal error, unrelated
  to this change and excluded from the comparison; it is not re-opened here. **Census finding, load-bearing
  for D3:** the `layout_assign` prototype library already ships its own ground model - 75 `GroundFCfactorMethod`
  surfaces, 56 `Construction:FfactorGroundFloor`, and 9 `Site:GroundTemperature:FCfactorMethod` / 3 Shallow /
  3 Deep objects across 10 buildings - which the new BuildingSurface object does not touch and does not
  harmonize. Two ground models now coexist in that path. Reconciling them is D3 and is a user decision, not
  an executor one; nothing in this block may change it.
- **D10 follow-up is now unblocked.** Lane A has released `builder.py`; the per-file
  `assert_prototype_idf_version()` move and the removal of the eager sweep at config.py:111 can be scheduled.

---

## 5. Verified facts with citations (established for this plan — do not re-derive)

1. No `Site:GroundTemperature*` object is emitted anywhere in `openubem/` — `grep -rin
   "GroundTemperature" openubem/ --include=*.py` returns **zero hits**. Every built IDF therefore runs
   on the EnergyPlus default ground temperature by omission.
2. Ground floors in the OSM-built path are written as plain `"ground"` —
   `openubem/idf/surfaces.py:527` (`s.Outside_Boundary_Condition = "ground"`); the comment at
   `openubem/idf/surfaces.py:990` confirms z=0 floors keep geomeppy's `'ground'`.
3. The `layout_assign` path **skips** surfaces whose boundary condition is `GroundFCfactorMethod` and
   leaves them on their native prototype construction — `openubem/geometry/envelope_patcher.py`, the
   `obc == "groundfcfactormethod": continue` branch. Two different ground models therefore coexist
   across resolution modes today.
4. `patch_envelope(idf, row, thermal_mass=...)` is called at `openubem/idf/builder.py:555`.
   (`docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §5.1 still cites `:481` — stale; do not trust it.)
5. `patch_envelope` **unconditionally** overwrites the window with
   `WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM` / `LA_Window_Material` from `row["u_window_w_m2k"]` and
   `row["shgc_window"]`, and repoints every `FENESTRATIONSURFACE:DETAILED` of type Window/GlassDoor to
   `LA_Window_Construction` — `openubem/geometry/envelope_patcher.py` ≈ lines 100–160. There is no
   comparison against the prototype's native window.
6. The SQL result path already selects energy rows by **unit**, not by name —
   `openubem/results/parser.py:123` (`is_energy = df["units"] == "J"`).
7. The ABUPS "District Heating" end-use rows are already mapped explicitly —
   `openubem/results/parser.py:64–80` (OPEN-64 T03).
8. EnergyPlus is pinned and asserted: `openubem/config.py:69` (`ENERGYPLUS_VERSION = "23.1"`),
   checked by `openubem/simulation/runner.py:22`.
9. The `layout_assign` prototype library is repointed to an E+ 23.1-transitioned sibling directory;
   the original library is all `Version,22.1` — `openubem/config.py:47–48`.
10. HVAC families and COPs come from `openubem/data/hvac_cop_by_archetype.json`, applied at
    `openubem/idf/hvac.py:625`.
11. `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 13 is "Pipeline plumbing, Windows &
    parallelism"; chapter 3 is "HVAC sizing, setpoints, exhaust & schedules"; chapter 17 is
    "Not-a-bug: expected behaviour & accepted limitations". The TOC is at line 13.

---

## 6. Tasks

### Lane A — Ground coupling (report item 1 / T1)

#### A01 — Census: what ground model does each building actually get?
**What.** Produce a table of ground-related boundary conditions actually present in built IDFs, split
by resolution mode.
**Why.** The report asserts two ground models coexist. Before writing anything, we need the counts.
**How.**
- Build a small sample with the existing pipeline: at least 10 buildings in a non-`layout_assign` mode
  and at least 10 in `layout_assign`, using whatever the repo's existing smallest build entry point is.
  Build only — no simulation needed for this task.
- For each IDF count, by `Outside_Boundary_Condition`: `ground`, `GroundFCfactorMethod`,
  `GroundSlabPreprocessorAverage`, `OtherSideCoefficients`, anything else ground-like.
- Count objects of class `CONSTRUCTION:FFACTORGROUNDFLOOR`, `CONSTRUCTION:CFACTORUNDERGROUNDWALL`,
  `SITE:GROUNDTEMPERATURE:BUILDINGSURFACE`, `SITE:GROUNDTEMPERATURE:FCFACTORMETHOD`,
  `SITE:GROUNDTEMPERATURE:SHALLOW`, `SITE:GROUNDTEMPERATURE:DEEP`, `FOUNDATION:KIVA`.
**How to test.** The deliverable is the table itself, in the progress log: mode × boundary condition ×
count, plus the per-class object counts. State the sample size. No code is committed in A01.

#### A02 — Emit `Site:GroundTemperature:BuildingSurface` explicitly, at 18 °C
**What.** A new module `openubem/idf/ground.py` with one function that adds a single
`SITE:GROUNDTEMPERATURE:BUILDINGSURFACE` object with all twelve monthly fields set to 18.0, idempotent
(never a second object), called once per IDF from `openubem/idf/builder.py`.
**Why.** Today the value is a default nobody chose. After this task it is a stated, testable choice.
**How.**
- Place the call in `builder.py` next to the other once-per-IDF site objects, after the
  `SITE:LOCATION` handling (`openubem/idf/builder.py:125` is the existing site block).
- The function must be a no-op if such an object already exists.
- Value: 18.0 for every month. Pinned by §4 D1.
**How to test.** New `tests/idf/test_ground_temperature.py`: (a) exactly one object after one call;
(b) exactly one after two calls; (c) all twelve fields equal 18.0; (d) an IDF that already has the
object is left unchanged. Run only this test file plus the existing `tests/idf/` subset.

#### A03 — Prove nothing moved
**What.** Simulate a sample before and after A02 and show the end-use results are unchanged.
**Why.** §4 D2. The whole point is an explicit statement of an existing behaviour.
**How.** Take ≥ 12 buildings spanning ≥ 4 archetypes. Run both variants **in parallel** (local pool at
20 concurrent, or one Speed array at `%32` — never sequentially). Compare per-end-use annual results.
**How to test.** Report max absolute and max relative difference per end use, and the population.
Expectation: zero. Any non-zero difference → STOP (§7 SR-A).

#### A04 — Write the ground decision down
**What.** Four to eight lines added to the Lane D document (see D02) recording: the value, that it is
now written explicitly, the evidence that it is defensible under a heated building, that undisturbed
soil was considered and rejected, and that F-factor floors in `layout_assign` are a known unharmonized
second model.
**Why.** An explicit-but-undocumented constant is only half the fix.
**How.** Lane A writes the text and hands it to the manager **in its report**. Lane A does not edit
Lane D's file.
**How to test.** Text present in the report, with the A01 counts cited.

---

### Lane B — Window traps and skip-when-better (report item 3 / T2)

#### B01 — Census: how often does the patcher install a *worse* window?
**What.** For the `layout_assign` path, compare the prototype's native window against the archetype
window the patcher would install, per building.
**Why.** `patch_envelope` overwrites unconditionally (§5 fact 5). If the archetype window is worse than
the prototype's, the model silently degrades a building that was modelled correctly. In the source
project the equivalent case moved cooling by **+54 %** on one building.
**How.**
- For each prototype in the library, extract the native window's U-factor and SHGC (from
  `WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM`, or from the glazing layers of the referenced construction where
  the prototype uses detailed glazing — if a prototype cannot be resolved, count it as "unresolved",
  do not guess).
- For each of a sample of ≥ 100 buildings, record native vs. archetype U and SHGC.
**How to test.** Report: how many buildings get a *higher* U, how many a *higher* SHGC, the
distribution of both deltas, and the unresolved count. No code change in B01.

#### B02 — Census: orphaned shading controls
**What.** Count `WINDOWSHADINGCONTROL` objects in the prototype library, and check what happens to them
when every window is repointed to `LA_Window_Construction`.
**Why.** In the source project, a `WindowShadingControl` left pointing at a switchable-glazing
construction that no longer matched produced a **30–50 % phantom reduction** in lighting, equipment and
DHW — an implausible result that looked plausible in a summary table.
**How.** Count the objects per prototype; for each, resolve its `Shading_Type`,
`Construction_with_Shading_Name` and its fenestration references; determine whether, after
`patch_envelope`, the referenced construction still exists and still matches the window it controls.
**How to test.** Report the per-prototype count and how many are orphaned or mismatched after patching.
If the count is zero across the whole library, say so plainly — that closes the trap.

#### B03 — Guard, behind a flag
**What.** Add a `skip-when-better` clamp to `patch_envelope`: when enabled, the archetype window is not
installed if the prototype's native window is already better on both U and SHGC. Default **OFF** (§4 D4).
Plus a fail-loud check for the orphan case found in B02 (if B02 found none, add only the check, not a fix).
**Why.** Makes the degradation impossible to reintroduce without someone turning the flag off on purpose.
**How.** Config flag in `openubem/config.py`… **no** — `config.py` belongs to Lane C. Put the flag
argument on `patch_envelope` itself with a default of `False`, and report to the manager that a config
entry is owed. Do not edit `config.py`.
**Gate.** B03 starts only after SR-B is answered (§7).
**How to test.** New `tests/test_envelope_patcher_windows.py`: flag off → current behaviour byte-identical;
flag on + prototype better → native window kept; flag on + prototype worse → archetype window installed;
orphaned shading control → raises or is tagged, never silently passed.

---

### Lane C — Result parsing and version robustness (report item 2 / T3)

#### C01 — Audit: where can a rename or a missing row become a silent zero?
**What.** List every place in `openubem/results/parser.py` where a result is selected by a **name**
string, and state what happens when that name is absent: raise, tag, or silently 0.
**Why.** Between E+ 22.1 and 24.2 the meter family `Electricity` was renamed to `District Heating
Water`. A parser that matches on names and defaults to zero turns a renamed meter into a real-looking
energy saving. The SQL path is already unit-based (§5 fact 6); the tabular path is the exposure.
**How.** Read the module; produce a table: selector → source (SQL/ABUPS) → behaviour when absent.
No code change in C01.
**How to test.** The table, in the progress log, with line citations.

#### C02 — Make absence loud
**What.** For every selector where absence currently yields a silent zero, make it either raise or
carry an explicit "not present" marker into the output row.
**Why.** Project rule: an absent result is shown as absent, never as zero.
**How.** Follow whatever the module's existing provenance/marker convention is; do not invent a second one.
**Gate.** Starts only after SR-C is answered (§7).
**How to test.** New `tests/test_parser_version_robustness.py` with a synthetic result set missing one
expected meter: the parser must not return 0 for it. Existing parser tests must still pass — run the
whole existing parser/results test subset and report pass/fail counts.

#### C03 — Version fence on the prototype library
**What.** An explicit check that no IDF entering the pipeline has a `VERSION` object other than
`config.ENERGYPLUS_VERSION`, with a clear error naming the file and the version found.
**Why.** §5 fact 9 — a 22.1 library and a 23.1 library sit side by side, and one of them is the wrong
one. A field-shifted IDF fails in under a second with an unhelpful message; this makes it say why.
**How.** One check at the point where prototype/baseline IDFs are opened. Keep it to `config.py` +
`parser.py` ownership; if the natural place is another lane's file, STOP and report.
**How to test.** Feed a 22.1 IDF → named error. Feed a 23.1 IDF → passes. Report the count of files in
both library directories and which versions they carry.

#### C04 — Per-archetype, per-end-use regression fixture
**What.** A golden table (archetype × end use) written from a current sample run, plus a test that
compares a fresh run against it and reports **which archetype and which end use moved**, not just a
pass/fail.
**Why.** In the source project an engine upgrade moved one archetype's gas use by **+56.6 %** while the
fleet total looked fine. A fleet-level regression check would have missed it.
**How.** Sample ≥ 12 buildings over ≥ 4 archetypes; run **in parallel** (§2 rule 8). Store the golden
under `tests/reference/` if that is where the repo's existing goldens live — check first; if not, ask.
**How to test.** Test passes against its own golden; deliberately perturb one value and confirm the
failure message names the archetype and the end use.

---

### Lane D — Documentation (report items 4 and 5 / T8, T10)

#### D01 — AirflowNetwork district-scale entry in the debug reference
**What.** One entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, house format:
`- **<exact symptom>** — <root cause>. Fix: <what changed>. *(source doc path)*`
**Content.** AirflowNetwork in `MultizoneWithDistribution` mode does not scale to district-size models:
the pressure-network solver matrix becomes singular / fails to converge once many buildings' zones are
in one network, and the run dies or stalls. `MultizoneWithoutDistribution` is the mode that survives at
that scale. OpenUBEM does not use AirflowNetwork today — this entry exists so the next person who
proposes it finds the answer before spending days on it.
**Why.** CLAUDE.md requires the debug reference to be the first stop before debugging. Recording a trap
we have not yet hit costs minutes now.
**How.** Chapter 17 ("Not-a-bug: expected behaviour & accepted limitations") is the right chapter for a
known limitation; if the executor judges chapter 3 or 13 a better fit, choose one and say why in the
progress log. Update the TOC at line 13 only if a new chapter is created — do not create one.
Mark the entry as forward-looking (the symptom is documented from another project's experience, not
reproduced here) so it is never mistaken for an OpenUBEM run log.
**How to test.** Entry present, format matches the surrounding entries, TOC still correct.

#### D02 — "What we chose vs what we inherited"
**What.** A new document `docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md` listing the
model settings that matter, each tagged one of three ways, in plain words:
- **chosen** — we decided this and can cite why;
- **physics** — it follows from the building physics, no choice to make;
- **inherited** — it is whatever the tool or the source data does by default, and nobody decided it.
**Why.** The cheapest credibility gain available: a reviewer's first question is which numbers were
chosen and which were inherited. Answering it before being asked is worth more than another decimal place.
**Content — at minimum these three inherited rows, which are live today:**
1. **Ground temperature** — 18 °C by omission; Lane A hands you the text and the census counts (A04).
2. **STD2022 internal loads (OPEN-03)** — record it as an open, unresolved inherited value; do not
   attempt to resolve it here. Read the current OPEN-03 wording from
   `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` and cite it rather than
   restating it from memory.
3. **Nominal vs. simulated floor area** — the two areas are not the same quantity and the model uses
   one of them; state which, with a file citation, and tag it.
Add any further rows only where you can cite a file and line. **Do not invent rows to fill the table.**
**How.** Read the register for OPEN-03 before writing. For each row: the setting, the value, chosen /
physics / inherited, the citation, and one plain sentence on what it would take to move it out of
"inherited".
**How to test.** Every row carries a file:line or a doc citation. No row is asserted without one. The
document ends with a short "what is not harmonized" list naming, at minimum, the two coexisting ground
models from A01.

**Lane D ordering:** D01 first (it is independent). D02 needs Lane A's A01 numbers and A04 text — if
they have not arrived, write everything else and leave the ground row as a clearly marked placeholder,
then report. Do not guess the counts.

---

## 7. Stop-and-report points

- **SR-A (Lane A, after A03).** Report the before/after deltas. If any end use moved, stop — a
  non-zero delta contradicts §4 D2 and must be explained before A04. Also report the
  FCfactorMethod census (A01) so the manager can raise D3 with the user.
- **SR-B (Lane B, after B02).** Report both censuses. B03 does not start until the manager answers.
  If B01 shows nobody gets a worse window and B02 finds no orphan, say so — the correct outcome may be
  "no code change needed, one test added to keep it that way".
- **SR-C (Lane C, after C01).** Report the selector table. C02 does not start until the manager answers,
  because "make absence loud" can change published outputs.
- **SR-D (Lane D, after D01).** Report the entry text and the chapter chosen, then continue to D02.

At every stop: append the progress-log entry first, then report. Do not continue past a stop.

---

## 8. Progress log

<!-- One entry per completed task, appended by the executor:
#### TXX — <title> — completed YYYY-MM-DD
**Artifacts:** files touched, tests added
**Deviations:** anything done differently from the plan, and why
**Test status:** command run, pass/fail counts
**Notes:** measurements, counts, anything the manager must decide
-->

#### D01 — AirflowNetwork district-scale entry in the debug reference — completed 2026-09-17
**Artifacts:** `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` — one bullet added to chapter 17
("Not-a-bug: expected behaviour & accepted limitations"), immediately before chapter 18. No TOC change
(chapter 17 already existed).
**Deviations:** None. Chapter 17 chosen as instructed by the plan's default (known limitation, not yet
hit); chapters 3 and 13 were not a better fit since this is neither an HVAC nor a pipeline/parallelism
issue.
**Test status:** Manual check — entry present, house-format bullet with bold lead, root cause, "Fix (if
ever proposed):", and a trailing citation in parentheses, matching the style of surrounding chapter-17
entries. TOC still lists 18 chapters correctly, unchanged.
**Notes:** Entry is explicitly tagged `[FORWARD-LOOKING, not yet hit in OpenUBEM]` per the plan's
instruction, and cites the source report instead of an OpenUBEM run log, since OpenUBEM does not use
AirflowNetwork today.

#### C01 — Audit: where can a rename or a missing row become a silent zero? — completed 2026-09-17
**Artifacts:** None. Read-only audit of `openubem/results/parser.py`; no code touched, per plan ("No
code change in C01").

**Deviations:** None.

**Test status:** N/A — no code change.

**Notes:** Selector table (selector → source → behaviour when the name is absent):

| Selector (name string) | Source | Behaviour when name absent |
|---|---|---|
| 9 HVAC meters in `METER_QUERY` (Cooling:Electricity, Heating:Electricity, Heating:NaturalGas, Fans:Electricity, Pumps:Electricity, WaterSystems:NaturalGas, WaterSystems:Electricity, InteriorEquipment:NaturalGas, Refrigeration:Electricity) | SQL `ReportData`/`ReportDataDictionary`, `Run Period` freq | **Silent 0.0.** `_parse_meters_sql` pre-seeds the dict at 0.0 (parser.py:198-210); a row is only added `if name in meters` (parser.py:215); an absent/renamed name never raises or flags, it just never updates the seed. Feeds `_compute_eui` directly (parser.py:624-631). |
| `Elevators:InteriorEquipment:Electricity` (`_ELEVATOR_METER`) | Same METER_QUERY/`_parse_meters_sql` path | **Silent 0.0**, same mechanism (parser.py:58, 198-216). Guard at parser.py:683 (`if elevators_kwh:`) only skips de-folding when 0 — a renamed meter is indistinguishable from "meter genuinely absent" (OPEN-46's documented pre-existing case), so a real rename would silently misreport 10-way vs 9-way end uses as the latter. |
| 14 ABUPS "District Heating" End-Uses row names (`_DISTRICT_HEATING_ROWS`: Heating, Cooling, Interior Lighting, Exterior Lighting, Interior Equipment, Exterior Equipment, Fans, Pumps, Heat Rejection, Humidification, Heat Recovery, Water Systems, Refrigeration, Generators) | ABUPS `TabularDataWithStrings`, ReportName=AnnualBuildingUtilityPerformanceSummary, TableName=End Uses, ColumnName=District Heating | **Silent 0.0.** `_read_abups_district_heating_rows` pre-seeds all 14 keys at 0.0 (parser.py:164); a missing row, missing table, `None`, or blank value leaves that key at 0.0 with no marker (parser.py:170-177). The call itself is wrapped in a bare `except Exception: pass` (parser.py:217-222) — if the whole ABUPS table is renamed/absent, all 14 keys silently stay 0.0 with zero indication. Feeds `_compute_eui` via `_dh()` (parser.py:621-622) into 9 published EUI columns. |
| `_read_abups_district_heating` (singular, Water-Systems-only reader) | Same ABUPS table/row | Same silent-0.0 contract (parser.py:149,153) but this function is **dead code** — superseded by `_read_abups_district_heating_rows`; no call site found (`grep -n "_read_abups_district_heating("` only matches its own `def`). |
| `NaturalGas:Facility` (`gas_zero` QC flag) | SQL meter, `check_building_integrity` | **Silent 0.0** feeding a QC-only flag, not a published EUI: an absent/renamed name gives `gas_j=0.0` → `gas_zero=True` unconditionally, indistinguishable from a real all-electric building (parser.py:871-879). Informational only, no gate. |
| `Electricity:Facility` (`meter_ok` closure check) | SQL meter, `check_building_integrity` | **Tagged, not silent.** Absent name → `facility_j=0.0`; `meter_ok` is then `zone_elec_j == 0.0` (parser.py:864-868), so any real zone electricity makes the check fail loudly rather than pass falsely. |
| `Zone Lights Electricity Energy`, `Zone Electric Equipment Electricity Energy` (`_EUI_ZONE_VARS`) | Hourly SQL variables | **Tagged, not silent.** Presence checked explicitly; absence returns `(None, dq_flag, var_name)` → caller marks the row `failed_parse` naming the missing variable (parser.py:594-598). |
| `Zone Lights Electricity Energy` / `Zone Ideal Loads*` (zone-key discovery) | Hourly SQL variables | **Tagged, not silent.** Both names absent → zero zone keys → returns `failed_zone_mismatch` (layout_assign: parser.py:322-326; other modes: parser.py:348-349) or raises `RuntimeError` on a foreign-osm_id breach (parser.py:342-346). |
| `Site Outdoor Air Drybulb Temperature`, `Zone Operative Temperature`, `Zone People Occupant Count` (IOD vars) | Hourly SQL variables | **Tagged, not silent.** Any absent → `NaN` + `IOD_NO_OCCUPIED_HOURS` flag (parser.py:744-746), never a bare 0. |
| `Floor Area {m2}`, `Zone Multiplier`, `Zone List Multiplier`, `Part of Total Building Area` (.eio header fields) | `eplusout.eio` header-name-mapped block | **Tagged, not silent.** A missing field name raises `KeyError` per-row, counted in `parse_status` (parser.py:404-409, 434-437); `resolve_simulated_floor_area` only trusts an `"ok"`/`"ok_with_*"` status with a positive area, else falls back to `footprint_fallback` with an explicit provenance string (parser.py:521-525) — never a bare 0 mistaken for a real area. |

**Count: 24 name-based selectors feed published EUI columns and default silently to 0.0 on a name
miss with no marker** (9 real HVAC meters + 1 elevator meter + 14 ABUPS district-heating rows). One
further selector (`NaturalGas:Facility`) has the same defect but only feeds an informational QC flag,
not a published number. The SQL zone-variable and .eio paths are already tagged/raise, matching §5
facts 6-7 — the exposure described in C01's "Why" is entirely in the meter (SQL Run-Period) and ABUPS
tabular paths, not the hourly zone-variable path.

**Manager decision needed (SR-C):** whether C02 should (a) raise when a *named* meter/ABUPS row is
completely absent from the SQL (distinguishing "renamed/version-drifted" from "legitimately zero,
e.g. all-electric building has no Heating:NaturalGas row"), or (b) carry an explicit per-column
"not present" marker instead of 0.0, since D5 keeps EnergyPlus pinned at 23.1 and today every one of
these 24 defaults is indistinguishable between "genuinely zero" and "name not found".

#### C03 — Version fence on the prototype library — completed 2026-09-17
**Artifacts:** `openubem/config.py` — added `PrototypeIDFVersionError`, `read_idf_version()`,
`assert_prototype_idf_version()`, `validate_prototype_library_versions()` (config.py:73-112), and an
eager `validate_prototype_library_versions()` call at config.py:111 immediately after
`ENERGYPLUS_VERSION` is defined, guarded on `directory.exists()` so it is a no-op on any machine
without the external baseline library. `tests/test_parser_version_robustness.py` (new) — 10 tests.
**Deviations:** The plan's "How" says the check belongs "at the point where prototype/baseline IDFs
are opened," which is `openubem/idf/builder.py:272` (`GeomIDF(str(baseline_idf_path))`) — Lane A's
file, not owned by Lane C. Per the plan's own instruction ("if the natural place is another lane's
file, STOP and report"), that call site was not touched. Instead the fence runs eagerly the moment
`openubem.config` is imported (the same pattern `_resolve_idd_path()` already uses in this file),
scanning the whole `config.BASELINE_IDF_DIR` directory once per process. Since `builder.py` already
does `from openubem import config` before ever opening a baseline IDF (builder.py:15), this closes
the same gap without editing Lane A's file. No IDF-opening call site elsewhere in the repo bypasses a
`config` import. Flagging for the manager: if a future baseline IDF is opened through some path that
never imports `openubem.config` first, that path would not be covered — worth a one-line note in
`builder.py`/`layout_assigner.py` next time either file is in scope for another lane.
**Test status:** `pytest tests/test_parser_version_robustness.py -q` — 10 passed. Existing subset
`pytest tests/test_eu_results_accounting.py tests/test_parser_elevators.py
tests/test_parser_hvac_metered.py tests/test_parser_open60_multiplier.py
tests/test_parser_open61_district_heating.py tests/test_parser_version_robustness.py
tests/test_results_aggregator.py tests/test_results_carbon.py tests/test_results_denominator.py
tests/test_results_parser.py -q` — 160 passed, 3 pre-existing `DeprecationWarning`s in
`test_results_parser.py` unrelated to this change. `from openubem.idf import builder` still imports
cleanly after the config.py change.
**Notes:** Census of both library directories (§5 fact 9): the original
`00.BaselineBuildings_NUs` (22.1 library, not referenced by an active `config.py` constant, only by
comment at config.py:47-48) holds 31 `.idf` files, all `Version 22.1` (29 plain `22.1`, 2 `22.1.0`).
The active `00.BaselineBuildings_NUs_v231` (`config.BASELINE_IDF_DIR`) holds 25 `.idf` files, all
`Version 23.1` — including 6 files whose filename still says `v221`/`V22.1` (stale filename from the
transition; their internal `VERSION` object is correctly `23.1`). The real library therefore passes
the fence cleanly today; no simulated or published number is touched by this task.

#### D02 — "What we chose vs what we inherited" — completed 2026-09-17
**Artifacts:** `docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md` (new). Three rows
written: ground temperature (inherited), STD2022 internal loads / OPEN-03 (inherited, open,
unresolved), nominal vs. simulated floor area (chosen). "What is not harmonized" section lists the
two coexisting ground boundary-condition models (A01's territory) and the OPEN-03 inheritance.
**Deviations:** Lane A's A01 census counts and A04 text had not arrived at dispatch time (checked:
`openubem/idf/ground.py` and `tests/idf/test_ground_temperature.py` do not exist yet). Per the plan's
explicit instruction, the ground-temperature row was written with everything citable (value, mechanism,
citation, what it would take to move it) and the census-count line was left as the exact placeholder
`<!-- PENDING Lane A A01/A04: census counts and ground text -->` rather than guessed.
**Test status:** Manual check — every row carries a file:line or a doc citation
(`openubem/idf/surfaces.py:527`, `openubem/geometry/envelope_patcher.py`,
`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md:121`,
`openubem/results/parser.py:496-525`, `openubem/results/parser.py:922`,
`docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md:1080`). No row was invented to
fill the table; only the three minimum rows plus the two "not harmonized" items are present.
**Notes:** OPEN-03's current register wording was read fresh from
`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md:121` and quoted verbatim rather than
restated from memory, per the plan's instruction. The manager owes the ground row a follow-up edit once
Lane A delivers A01/A04.

#### B01 — Census: how often does the patcher install a worse window? — completed 2026-09-17
**Artifacts:** None. No file edited (census only, per plan). Scratch scripts ran from the session
scratchpad, not committed.
**Deviations:** Used an exhaustive population instead of a random ≥100-building sample. Justification:
`envelope_patcher.py`'s own module docstring (lines 6–12) states the installed window U/SHGC is
"identical for every resolution_mode" and keyed only on `(archetype_id, climate_zone)` — so a random
building sample would just resample the same finite grid with repeats. Instead: every archetype in
`ARCHETYPE_IDF_MAP` (`openubem/geometry/layout_assigner.py:23-61`, 28 tokens) was crossed with every
climate zone for that archetype in `openubem/data/construction/ashrae_90_1_2019.json` (16 zones each),
and with every distinct native window (U, SHGC) pair actually present in that archetype's baseline IDF
(`config.BASELINE_IDF_DIR`), resolved via each window/glassdoor `FenestrationSurface:Detailed`'s
`Construction_Name` → `Construction.Outside_Layer` → `WindowMaterial:SimpleGlazingSystem` (UFactor,
Solar_Heat_Gain_Coefficient). Distinct native (U, SHGC) values were deduplicated (many auto-generated
per-surface Construction names, esp. TallBuilding/SuperTallBuilding, point at identical material
values — deduping avoided inflating N with false diversity).
**Test status:** N/A — no code, no tests (per plan, "No code change in B01").
**Notes:** N = 496 (archetype × climate zone × distinct native window triples) across 23 of 28
archetypes with a resolvable native window (23 archetypes × 16 zones, variable number of distinct
native window pairs per archetype). 4 archetypes (`LargeDataCenterHighITE`, `LargeDataCenterLowITE`,
`SmallDataCenterHighITE`, `SmallDataCenterLowITE`) have no windows at all — not a resolution failure,
just structurally inapplicable. 1 archetype (`SuperMarket`, `Supermarket_V22.1.idf`) is unresolved: its
window constructions (`WinLib_1001`, `WinLib_2003`) use detailed glazing layers ("clear 6mm"), not
`WindowMaterial:SimpleGlazingSystem` — no U/SHGC extracted, not guessed, per plan instruction.
Of the 496 resolved triples: 264 (53.2%) get a strictly higher installed U-factor than the native
window (worse insulation); 222 (44.8%) get a strictly higher installed SHGC (more solar gain); 112
(22.6%) get worse on **both** simultaneously — this is the exact population a skip-when-better clamp
(B03) would protect. delta_u (installed − native) ranges from −2.7827 to +1.4308 W/m²K, median +0.0678
(i.e. a small majority of cases get a slightly worse U). delta_shgc ranges from −0.32 to +0.19, median
0.0 (roughly a wash on SHGC in the middle of the distribution, but with a fat higher-SHGC tail). This
confirms the report's concern (fact 5, §5): the unconditional overwrite is not a rare edge case — just
over half of all realizable archetype/zone combinations get a worse U-factor installed than the
building already had.

#### B02 — Census: orphaned shading controls — completed 2026-09-17
**Artifacts:** None. No file edited (census only, per plan).
**Deviations:** None.
**Test status:** N/A — census only.
**Notes:** `WINDOWSHADINGCONTROL` object count across the entire 25-file baseline prototype library
(`config.BASELINE_IDF_DIR`, every file referenced by `ARCHETYPE_IDF_MAP`): **zero**, in every single
prototype. No prototype in the library uses `WindowShadingControl` at all, so there is nothing for
`patch_envelope`'s window repoint to orphan or mismatch. Per the plan's own instruction (§6 B02, "if the
count is zero across the whole library, say so plainly — that closes the trap"): the orphaned-shading
trap described in the source report does not exist in this library today.

#### B03 — Guard, behind a flag — completed 2026-09-17
**Artifacts:** `openubem/geometry/envelope_patcher.py` (added `_native_window_u_shgc()` line 61,
`_check_shading_controls()` line 91, new `skip_when_better: bool = False` keyword arg on
`patch_envelope()` line 132, applied in the fenestration loop lines 237–240, `_check_shading_controls(idf)`
call line 243). `tests/test_envelope_patcher_windows.py` (new, 9 tests).
**Deviations:** None from the B03 task text. Per D8/task instruction, only the fail-loud shading-control
check was built — no repair path, since B02 found zero `WindowShadingControl` objects in the current
prototype library. A `config.py` entry for `skip_when_better` is owed to Lane C and was deliberately not
created here (`config.py` is Lane C's file, per §3).
**Test status:** `pytest tests/test_envelope_patcher_windows.py tests/test_envelope_patcher.py -q` — 22
passed, 0 failed (9 new + 13 pre-existing). New tests cover: flag off leaves today's unconditional
overwrite unchanged; flag on + native window better on both U and SHGC keeps the native window; flag on +
native worse on U only, SHGC only, or both installs the archetype window; an orphaned
`Construction_with_Shading_Name` (references a construction absent from the IDF) raises `ValueError`; a
`WindowShadingControl` whose controlled fenestration surface gets repointed to `LA_Window_Construction`
raises `ValueError` (mismatch after patching); no shading controls present never raises.
**Notes:** `skip_when_better="better"` is defined per the task text as strictly lower on BOTH UFactor and
SHGC than the archetype window (`native_u < new_u and native_shgc < new_shgc`); a native window that
cannot be resolved to a `WindowMaterial:SimpleGlazingSystem` (e.g. detailed glazing layers, the SuperMarket
case from B01) falls back to today's unconditional install, since "better" cannot be established without
its U/SHGC. The shading-control check runs unconditionally (not gated behind `skip_when_better`) and is a
no-op today given B02's zero count, so no published number moves. Owed to Lane C, verbatim for the
manager: a `config.py` entry such as `ENVELOPE_PATCH_SKIP_WHEN_BETTER = False` (or the plan's own naming
convention) that `builder.py:557`'s `envelope_patcher.patch_envelope(...)` call can read and pass through
as `skip_when_better=`.

#### A01 — Census: what ground model does each building actually get? — completed 2026-09-17
**Artifacts:** none (census only, no code committed per plan).
**Deviations:** none. Used the repo's existing `tests/fixtures/synthetic_10_buildings.py` 10-row fixture
(10 distinct archetypes) run through `run_step3` twice — once `resolution_mode="auto"`, once
`resolution_mode="layout_assign"` — giving exactly 10 IDFs per mode, 20 total, satisfying the ≥10/≥10
requirement. One row (`OpenUBEMUnknown`, R10) has no `layout_assign` baseline and fell back to the auto
path inside the `layout_assign` run (tagged `layout_assign_fallback_auto` by existing code), so its
surfaces read like the auto path even inside the `layout_assign` sample — expected, not an error.
**Test status:** N/A (no test file for a census task).
**Notes — census table.**
Mode=auto (10 buildings), `BUILDINGSURFACE:DETAILED` `Outside_Boundary_Condition` counts:
ground=14, outdoors=137, Surface=56, surface=48.
Mode=layout_assign (10 buildings, 9 real baseline + 1 auto-fallback):
Adiabatic=967, Surface=3332, GroundFCfactorMethod=75, Outdoors=622, Zone=137, Ground=15, outdoors=8 (from
the 1 fallback), ground=1 (from the 1 fallback).
Per-class object counts, mode=auto: `CONSTRUCTION:FFACTORGROUNDFLOOR`=0, `CONSTRUCTION:CFACTORUNDERGROUNDWALL`=0,
`SITE:GROUNDTEMPERATURE:BUILDINGSURFACE`=0, `SITE:GROUNDTEMPERATURE:FCFACTORMETHOD`=0,
`SITE:GROUNDTEMPERATURE:SHALLOW`=0, `SITE:GROUNDTEMPERATURE:DEEP`=0, `FOUNDATION:KIVA`=0 (all zero).
Per-class object counts, mode=layout_assign: `CONSTRUCTION:FFACTORGROUNDFLOOR`=56,
`CONSTRUCTION:CFACTORUNDERGROUNDWALL`=0, `SITE:GROUNDTEMPERATURE:BUILDINGSURFACE`=0,
`SITE:GROUNDTEMPERATURE:FCFACTORMETHOD`=9, `SITE:GROUNDTEMPERATURE:SHALLOW`=3,
`SITE:GROUNDTEMPERATURE:DEEP`=3, `FOUNDATION:KIVA`=0.
Sample size: 20 buildings (10 per mode), 10 distinct archetypes. Confirms DESIGN fact #1 (zero
`SITE:GROUNDTEMPERATURE:BUILDINGSURFACE` objects anywhere pre-change) and fact #3 (the `layout_assign`
prototype library already carries its own `GroundFCfactorMethod`/`FCfactorMethod`/`Shallow`/`Deep` ground
objects — a second, pre-existing ground model, untouched by this task per D3).

#### A02 — Emit `Site:GroundTemperature:BuildingSurface` explicitly, at 18 °C — completed 2026-09-17
**Artifacts:** `openubem/idf/ground.py` (new — `add_ground_temperature(idf)`, idempotent, all 12 monthly
fields set to 18.0); `openubem/idf/builder.py` (2 lines: import + one call in `BuildingIDF.__init__`,
right after `_populate_site_location_from_epw`, so it fires once per IDF regardless of resolution mode);
`tests/idf/test_ground_temperature.py` (new, 4 tests).
**Deviations:** none.
**Test status:** `pytest tests/idf/ -q` — 16 passed, 0 failed (4 new + 12 pre-existing). Also ran
`pytest tests/test_idf_builder.py tests/test_step3_orchestrator.py -q` for regression — 57 passed, 0
failed (one benign Windows/loky worker-teardown stack trace printed to stderr, exit code still 0, not a
test failure).
**Notes:** none.

#### A03 — Prove nothing moved — completed 2026-09-17
**Artifacts:** none (measurement only). Scratch build+sim script and outputs kept in the session
scratchpad, not the repo.
**Deviations:** "before" state obtained via `git stash push -- openubem/idf/builder.py` (isolates exactly
the 2-line Lane A diff), build+simulate, `git stash pop` to restore, build+simulate again as "after" —
rather than a second checkout, since only `builder.py` needed to move and no other lane's file was
touched. Verified safe: the build phase used `n_jobs=1` (no subprocess re-import of `builder.py`), and the
simulation phase's `loky` workers only read already-written `.idf`/`.sql` files, never re-import
`builder.py`, so popping the stash mid-run could not contaminate the in-flight "before" simulation.
Ran the same 20-building sample as A01 (10 auto + 10 layout_assign) rather than a fresh ≥12/≥4-archetype
sample, since it already exceeds both minimums (20 buildings, 10 archetypes) and reuses A01's evidence.
**Test status:** N/A (simulation comparison, not a pytest run). Local process pool, `n_jobs=20`
(loky/joblib), both variants — never sequential, per §2 rule 8.
**Notes — before/after comparison.** 19 of 20 buildings produced a result in both variants; 1
(`way/R8`, Warehouse, auto mode) failed identically in both variants (`status=failed_fatal`, same
`error_summary` verbatim in both) — a pre-existing IDF-generation defect unrelated to this task, excluded
from the numeric comparison since it produced no SQL to compare either time. Across the 19 comparable
buildings × up to 24 end-use meter keys each = 456 (building, end-use) pairs: **max absolute difference =
0.0 kWh, max relative difference = 0.0**, on every single pair — byte-identical, as D2 requires. No STOP
triggered.

#### E01 - Version fence moved to the open site; window flag wired to config - completed 2026-09-17

**Artifacts:** openubem/config.py, openubem/idf/builder.py

**Deviations:** Skipped the optional new test asserting `assert_prototype_idf_version` is invoked for a baseline path — building a fixture that reaches the `baseline_idf_path is not None` branch in `BuildingIDF.__init__` needs a real (or heavily mocked) GeomIDF/row/epw chain, not cheap without fixtures, so left `tests/test_parser_version_robustness.py` untouched (existing tests already call `validate_prototype_library_versions()` explicitly, no import-time dependency to rewrite).

**Test status:** tests/test_parser_version_robustness.py 10 passed; tests/idf/ + tests/test_idf_builder.py 55 passed; tests/test_envelope_patcher.py + tests/test_envelope_patcher_windows.py 22 passed. Import time for `openubem.config` measured 0.15s (previously 0.33s import-time IDF sweep).

**Notes:** No errors hit, no debug-references entry needed.

**Manager audit 2026-09-17.** Re-ran independently: module-level `validate_prototype_library_versions()` call is gone from `openubem/config.py`; fence now at `openubem/idf/builder.py:276` on the prototype-open path; `ENVELOPE_PATCH_SKIP_WHEN_BETTER` defined at `openubem/config.py:112` and passed at `openubem/idf/builder.py:564`. `python -m pytest tests/test_parser_version_robustness.py tests/idf/ tests/test_idf_builder.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> 87 passed. `git status --porcelain` unchanged in footprint: no file touched outside the lane.

---

### D3 — RULING: no code change, and the reason is a measured cross-mode inconsistency — 2026-09-17

D3 was left open as "two ground models coexist in the `layout_assign` path; reconciling them is a user
decision". Before ruling I measured what the two models actually are, across all 25 prototypes in
`config.BASELINE_IDF_DIR`, rather than relying on the A01 census summary.

**Correction to the A01 figure.** The census recorded the second ground model on 10 buildings.
Measured directly, **24 of 25 prototypes** carry F-factor ground content — either
`GroundFCfactorMethod` surfaces, a `Site:GroundTemperature:FCfactorMethod` object, or both. The
earlier number understated it.

**What each model says the ground temperature is:**

```
Site:GroundTemperature:FCfactorMethod, 20 ASHRAE901_* prototypes : min -4.20  max 22.00  mean  8.97 degC
Site:GroundTemperature:FCfactorMethod, the 90.1-2019 v221 set    : min -12.60 max 20.90  mean  6.38 degC
Site:GroundTemperature:BuildingSurface, written by add_ground_temperature : 18.0 degC, all twelve months
```

The F-factor values swing with the season, as that method expects, and average roughly 6-9 degC over
the year in Buffalo. The object OpenUBEM now writes is a flat 18 degC.

**Which surfaces each one governs, measured:** in the `layout_assign` prototypes the ground floors are
almost entirely `GroundFCfactorMethod` (e.g. OutPatient 30, College 26, SchoolPrimary 24, and 0 plain
`Ground` surfaces in 20 of the 24). Only `SuperTallBuilding` and `TallBuilding` (7 each) and the two
small data centers (1 each) carry plain `Ground` surfaces. The OSM-built path, by contrast, writes
every ground floor as plain `"ground"` (`openubem/idf/surfaces.py:527`).

**So the two models do not overlap — they split by resolution mode.** That explains A03's measured
zero delta cleanly: the new object is inert in `layout_assign` because almost nothing there reads it,
and where it does apply it writes the same 18 degC that EnergyPlus already defaults to. Nothing moved,
and nothing published moves.

**The finding that matters, and it is not "harmless".** The same building modelled in the two
resolution modes sees ground-floor boundary temperatures roughly **9 K apart** in Buffalo — a flat
18 degC under the OSM path versus a seasonal F-factor profile averaging about 9 degC under
`layout_assign`. In a heating-dominated climate that is a real difference in floor heat loss, not a
rounding artefact. It has always been there; adding the explicit object did not create it, it made it
visible.

**Ruling: no code change in this arc.** Harmonizing means choosing which ground model is canonical for
OpenUBEM, rewriting either the OSM path's boundary conditions or the prototype library's F-factor
constructions, and re-validating against the adopted baseline. That is a modelling decision with a
re-validation cost attached, it is the user's to make, and nothing currently depends on it being made
today. The conservative option forecloses nothing.

**What must be said whenever the two modes are compared.** A heating figure produced in `auto`/OSM mode
and one produced in `layout_assign` mode are not directly comparable on ground heat loss. Any
cross-mode comparison states this, or accounts for it. This is the practical consequence of leaving
D3 open, and it is the reason the ruling is recorded here with the numbers rather than closed silently.

**What would reopen D3:** a study that compares the two resolution modes on heating demand, or a
decision to publish a figure built in OSM mode alongside one built in `layout_assign` mode. Either
makes the 9 K split load-bearing, and at that point it must be harmonized before the number ships.

#### D3 addendum — which mode the adopted figure was built in, and why that closes the question for now

Two facts found after the ruling above was written. Both strengthen it; neither changes it.

**1. The report already says not to adopt this ground model, and gives a defect.** §4 "Do not transfer"
of `2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md` lists `GroundFCfactorMethod` explicitly, with
the reason: adopting it would import a defect in which core-slab loss is modelled as exactly zero,
into a model that currently builds layered floors correctly. So the F-factor model is not merely a
*different* choice from OpenUBEM's — it is the one the report names as the worse of the two. That
makes "harmonize toward F-factor" a non-starter, and narrows any future reconciliation to one
direction: moving the `layout_assign` path onto OpenUBEM's own ground model, never the reverse.

**2. The adopted fleet figure was not built in the affected mode.** The open-items register records,
for OPEN-56, that the single `orient()` call at `openubem/idf/builder.py:464-465` is gated
`if resolution_mode != "auto"` and therefore "never fires for the adopted baseline mode" — i.e. the
adopted baseline is built in **`auto` (OSM) mode**. In that path every ground floor is written as a
plain `"ground"` surface (`openubem/idf/surfaces.py:527`), which is governed by
`Site:GroundTemperature:BuildingSurface`, not by F-factor. The 24-of-25 F-factor prototypes belong to
the `layout_assign` path.

**Consequence, stated plainly: the adopted 153.95 kWh/m2 over 8,139 buildings does not run on the
F-factor ground model at all.** It runs on the 18 degC building-surface model — which is what
EnergyPlus was already defaulting to before `add_ground_temperature` made it explicit, which is why
A03 measured a delta of exactly 0.0 kWh. The published number is untouched by any of this.

So D3 is not urgent, and the ruling stands: no code change. What remains true and must be carried
forward is the cross-mode caveat — a `layout_assign` heating figure and an `auto` heating figure differ
in their ground boundary by roughly 9 K in Buffalo, and additionally the `layout_assign` side carries
the report's defect-2 caveat on core-slab loss. Comparing the two modes on heating demand without
saying so would be wrong in two ways at once, not one.
