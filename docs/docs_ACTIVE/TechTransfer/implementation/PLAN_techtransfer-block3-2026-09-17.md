# PLAN — TechTransfer block 3 (T4, pre-simulation compliance audit)

- **Slug:** `techtransfer-block3`
- **Date opened:** 2026-09-17
- **Source:** `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`,
  section 5 "Recommended sequence", order 8 (**T4**, report lines 164-210).
- **Predecessors:** `PLAN_techtransfer-block1-2026-09-17.md` (orders 1-5, delivered) and
  `PLAN_techtransfer-block2-2026-09-17.md` (orders 6-7; Lane F delivered, Lane E in flight).
  Decisions D1-D12 and E1-E5 / F1-F5 remain binding and are not re-opened here.
- **Out of scope, do not start:** report items T5, T6, T11.

---

## 1a. Scope note — why this block is smaller than the report's estimate

The report sizes T4 at 1-2 weeks because it assumes OpenUBEM still hardcodes its code-baseline
constants. **It does not.** Measured 2026-09-17: the envelope values already arrive as data
(`openubem/data/construction/tabula_archetypes_{es,fr,gb,it}.json`,
`ashrae_90_1_2019.json`, `doe_prototype_loads.json`) and are applied by
`patch_envelope()` (`openubem/geometry/envelope_patcher.py:132`). The applier-chain half of T4 is
therefore **already present** and must not be rewritten — a refactor would risk moving the adopted
European numbers for no gain.

What is genuinely missing is the report's second bullet: **"compliance gates that need no EnergyPlus
run"**. OpenUBEM's gates today are post-simulation (`openubem/validation/` = `eui_impact.py`,
`european_campaign.py`, `step8_gates.py`, `step8_bands.py`, `mask_recover.py`); nothing checks that
the envelope transform actually landed on the IDF before a fleet run is dispatched. That, and only
that, is this block.

The third T4 bullet (the internal-loads gap, OPEN-03) is an **investigation**, not an
implementation, and is not started here.

---

## 2. Hard rules for the executor

1. Execute the tasks in order. Do not propose alternatives. If the code contradicts this plan,
   **STOP and quote the conflict** rather than improvising.
2. Edit only the files your lane owns (section 3).
3. **No published number may move in this block.** The audit reads an IDF and reports; it mutates
   nothing. If a change of yours alters a simulated result, you have exceeded the task — revert and
   report.
4. **Zero EnergyPlus simulations.** IDF *generation* (Step 3) is allowed for the census and must run
   in parallel, never in a `for` loop. EnergyPlus *runs* are forbidden in this block entirely.
5. No code comments. No new files beyond those named in section 3.
6. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. After
   solving one, register it there in the house format before you close the task.
7. Append one progress-log entry per completed task under section 8.

---

## 3. File layout and lane ownership

**Lane G — the audit**

- `openubem/idf/compliance.py` (new)
- `tests/test_compliance_audit.py` (new)

**Nobody edits in this block:** `openubem/geometry/envelope_patcher.py`,
`openubem/geometry/layout_assigner.py` (owned by block 2 Lane E), `openubem/idf/builder.py`,
`openubem/simulation/parallel.py`, `openubem/config.py`, `openubem/validation/`, any OVERVIEW or
DESIGN doc, root `main.py`.

---

## 4. Dependency decisions (pinned — do not re-litigate)

- **G1. The audit reads; it never writes to the IDF.** Signature
  `audit_envelope_compliance(idf, row) -> dict`. It takes an already-patched in-memory IDF and the
  same Step-2 row `patch_envelope()` was given, and returns findings. No object is added, removed or
  edited. No file is written.
- **G2. It checks what OpenUBEM itself claims to have written — nothing borrowed.** Five checks,
  each derived from `patch_envelope()` (`envelope_patcher.py:132-245`), not from any external code
  baseline:
  1. `ENVELOPE_PATCH_INCOMPLETE` — an opaque surface whose `Surface_Type` is in the patcher's
     construction map, whose `Outside_Boundary_Condition` is **not** `groundfcfactormethod`, still
     references a construction other than `LA_Wall_Assembly` / `LA_Roof_Assembly` /
     `LA_Floor_Assembly`. Report the count and the first five surface names.
  2. `ENVELOPE_U_MISMATCH` — the effective U of each `LA_*_Assembly` construction, recomputed from
     its own materials, differs from `row["u_wall_w_m2k"]` / `u_roof_w_m2k` / `u_floor_w_m2k` by
     more than **0.01 W/m2K**. Report the assembly, the wanted and the found value.
  3. `WINDOW_PROPERTY_MISMATCH` — `LA_Window_Material`'s `UFactor` or
     `Solar_Heat_Gain_Coefficient` differs from `row["u_window_w_m2k"]` / `row["shgc_window"]` by
     more than **0.01**.
  4. `GLAZING_UNPATCHED` — a `FenestrationSurface:Detailed` of type `Window` or `GlassDoor` that is
     not on `LA_Window_Construction`. **Informational when `skip_when_better` was on** (that flag
     leaves better native windows in place deliberately, block 1 D8) — so the audit records the
     count and the flag state, and only marks it a failure when the flag was off.
  5. `GROUND_SURFACE_UNPATCHED` — the count of surfaces the patcher deliberately skipped because
     their boundary condition is `GroundFCfactorMethod`. **This is informational, never a failure.**
     It is the known two-ground-model situation (block 1 D3, still the user's open decision); the
     audit's job is to make its size visible, not to judge it.
- **G3. Return shape.** `{"status": "pass" | "fail", "failures": [ ... ], "info": { ... }}`, where
  each failure is a dict with `reason` (one of the names above), `count`, and `examples` (at most
  five strings). `status` is `"fail"` if and only if `failures` is non-empty. Informational checks
  never enter `failures`.
- **G4. Nothing is wired in this block.** The audit is not called from `builder.py`, not written to
  a manifest column, not surfaced in the viewer, and does not abort anything. Wiring is a separate
  decision at SR-G, for the same reason block 2's prep gate shipped OFF: a new gate that fires on
  day one stops the fleet before anyone has seen its numbers.
- **G5. Tolerances are pinned for this block** (0.01 W/m2K, 0.01) and are not physical constants.
  They absorb float round-trip noise through the IDF text, nothing more.

---

## 5. Verified facts, with line citations (measured 2026-09-17, do not re-derive)

1. `patch_envelope(idf, row, thermal_mass=False, skip_when_better=False)` —
   `openubem/geometry/envelope_patcher.py:132`. It builds `LA_Roof_Assembly`, `LA_Wall_Assembly`,
   `LA_Floor_Assembly` via `build_opaque_assembly()`, then `LA_Window_Material` +
   `LA_Window_Construction`, then repoints surfaces.
2. Opaque loop: `for surf in idf.getsurfaces()`, mapped through `_LA_SURFACE_CONSTRUCTION_MAP`,
   **skipping** `obc == "groundfcfactormethod"` (`envelope_patcher.py:211-220`). Those skipped
   surfaces are check 5, not a defect.
3. Fenestration loop repoints only `Surface_Type` in `{"Window", "GlassDoor"}`; `Door` is left
   untouched deliberately (an opaque door on a glazing construction is an EnergyPlus fatal). The
   audit must apply the same two-type filter or it will report false failures on doors.
4. `skip_when_better` is now wired from config: `ENVELOPE_PATCH_SKIP_WHEN_BETTER: bool = False`
   (`openubem/config.py:112`), passed at `openubem/idf/builder.py:564`. Default False, so check 4 is
   a real failure today and becomes informational only if the flag is turned on.
5. The five envelope columns the patcher requires on `row` are
   `u_wall_w_m2k`, `u_roof_w_m2k`, `u_floor_w_m2k`, `u_window_w_m2k`, `shgc_window`; the patcher
   raises `ValueError` rather than defaulting any of them (`envelope_patcher.py:161-171`).
6. `openubem/idf/european_physics.py` is 165 lines and already exposes
   `effective_u(u_value_w_m2k, delta_u_w_m2k)` (`:21`) — use it for check 2 rather than writing a
   second U-value routine.
7. There is no `03_idf_manifest.parquet` on disk in this working tree, so the census (G02) must
   generate its own IDFs, exactly as block 1's A01 census did (20 buildings, 10 archetypes,
   `layout_assign` mode) — in parallel, never sequentially.

---

## 6. Tasks

#### G01 — Implement the audit
**What.** `openubem/idf/compliance.py` with `audit_envelope_compliance(idf, row, skip_when_better=False)`
implementing the five checks of G2 and the return shape of G3.
**Why.** Today a bad envelope table is only discovered after a fleet of EnergyPlus runs has finished,
or never. This turns it into a check that costs milliseconds.
**How.** Pure reading. Reuse `effective_u()` from `european_physics.py`. Re-use the patcher's own
surface-type map and boundary-condition rule rather than re-deriving them, so the audit cannot drift
from the code it audits.
**How to test.** `tests/test_compliance_audit.py` (new): (a) an IDF freshly patched by
`patch_envelope()` with a valid row audits `pass` with an empty `failures` list; (b) manually
repointing one wall surface back to a prototype construction yields exactly one
`ENVELOPE_PATCH_INCOMPLETE` failure with `count == 1`; (c) perturbing `LA_Window_Material.UFactor`
by 0.5 yields `WINDOW_PROPERTY_MISMATCH`; (d) perturbing it by 0.001 does **not**; (e) a baseline
carrying `GroundFCfactorMethod` surfaces reports them under `info`, and `status` stays `"pass"`;
(f) an opaque `Door` fenestration never appears as a failure. Then run
`python -m pytest tests/test_compliance_audit.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q`
— all three must be green.

#### G02 — Fleet census: what does the audit say about the buildings we actually build?
**What.** Run the audit over at least 20 `layout_assign` buildings spanning all 10 archetypes and
report the distribution.
**Why.** A gate nobody has measured cannot be turned on. This number is what the user decides on at
SR-G.
**How.** A throwaway script in the scratchpad directory (NOT under `docs/`, NOT committed). Generate
the IDFs in parallel (process pool of 20), audit each in memory, discard. **No EnergyPlus runs.**
**How to test.** Report: sample size, how many audit `pass`, and for each failure reason the number
of buildings and the worst example. Report the `GROUND_SURFACE_UNPATCHED` count separately as
information, not as a failure. **STOP at SR-G.**

---

## 7. Stop-and-report points

- **SR-G (after G02).** Report the census. **User decision owed:** whether to (a) leave the audit as
  a library function anyone can call, (b) call it from `run_step3()` and record the result as a
  manifest column, or (c) let it block a fleet run the way block 2's prep gate can. Do not start
  (b) or (c) without it.

---

## 8. Progress log

<!-- One entry per completed task:
#### TXX - <title> - completed YYYY-MM-DD
**Artifacts:** / **Deviations:** / **Test status:** / **Notes:**
-->

#### G01 — Implement the audit — completed 2026-09-17
**Artifacts:** `openubem/idf/compliance.py` (new, `audit_envelope_compliance` at line 73),
`tests/test_compliance_audit.py` (new, 8 tests).
**Deviations:** none from G2/G3. Check 1 and check 5 compare each opaque surface's
`Construction_Name` against the exact per-type expected LA construction
(`_LA_SURFACE_CONSTRUCTION_MAP`, reused verbatim from `envelope_patcher.py`) rather than membership
in the 3-name set the plan prose uses as shorthand — same code-derived source, stricter, no
behavioural ambiguity; not treated as a plan conflict. Check 2 uses `effective_u()` only as the
positivity-validating wrapper around a U recomputed by summing each construction layer's own
resistance (`MATERIAL:NOMASS.Thermal_Resistance` or `MATERIAL.Thickness/Conductivity`), since
`effective_u()` itself only adds a delta and does not read materials.
**Test status:** `python -m pytest tests/test_compliance_audit.py tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` — `29 passed in 2.01s`.
**Notes:** No new debug-reference entry — no error was hit or fixed.

#### G02 — Fleet census — completed 2026-09-17
**Artifacts:** none committed (throwaway script ran from the scratchpad directory, per plan).
**Deviations:** none. Built 20 `layout_assign` IDFs (the existing 10-archetype
`tests/fixtures/synthetic_10_buildings.py` rows, 2 variants each) via `run_step3(..., n_jobs=20,
resolution_mode="layout_assign")` (loky process pool of 20, zero EnergyPlus runs), then ran
`audit_envelope_compliance` on each saved-and-reloaded IDF, `skip_when_better=False` (today's
`config.ENVELOPE_PATCH_SKIP_WHEN_BETTER` default).
**Test status:** N/A (census, no test file).
**Notes — census.** Sample size 20 (10 archetypes x 2 variants). Pass: 18/20. Fail: 2/20 — both are
the 2 `OpenUBEMUnknown` variants, the one archetype with no `layout_assign` baseline; those rows fall
back to the `auto` path internally (`layout_assign_fallback_auto`, existing behaviour) so
`patch_envelope()` never runs on them at all — a structural non-applicability, not an audit defect.
Failure-reason totals (both failing buildings only): `ENVELOPE_PATCH_INCOMPLETE` 18 surfaces (9+9),
`ENVELOPE_U_MISMATCH` 6 (3 unresolved LA assemblies x 2 buildings), `GLAZING_UNPATCHED` 14 (7+7).
The 18 genuine `layout_assign` buildings (9 archetypes x 2) are 100% clean: 0 failures of any reason.
`GROUND_SURFACE_UNPATCHED` (informational, never a failure): 150 surfaces total across the 20
buildings, per-building range 0-18, identical between each archetype's 2 variants, 0 for the 2
`OpenUBEMUnknown` fallback rows.

**Manager audit 2026-09-17 (Lane G).** Re-ran independently: `openubem/idf/compliance.py` is 166
lines with `audit_envelope_compliance(idf, row, skip_when_better=False)` at `:73`;
`tests/test_compliance_audit.py` is 182 lines. `python -m pytest tests/test_compliance_audit.py
tests/test_envelope_patcher.py tests/test_envelope_patcher_windows.py -q` -> **29 passed in 1.97s**.
The three rules that make the audit agree with the patcher rather than drift from it are present and
were checked by grep: the `groundfcfactormethod` skip (`compliance.py:85`, `:159`), the
`("window", "glassdoor")` two-type fenestration filter that keeps opaque `Door` out of the failures
(`:134`), and reuse of `effective_u()` from `european_physics` (`:14`, `:70`). Tolerances are the
pinned 0.01 (`:29-30`). G4 holds: nothing is wired — the module is imported by nothing but its test.

**Deviation, to be closed (task G03).** G01's *How* required re-using the patcher's own surface-type
map; the executor instead re-declared a private copy, `_LA_SURFACE_CONSTRUCTION_MAP` at
`compliance.py:16`, duplicating `envelope_patcher.py`'s. That is precisely the drift the plan
forbade: a future surface type added to the patcher would silently stop being audited.

#### G03 — Remove the duplicated surface map
**What.** Delete `_LA_SURFACE_CONSTRUCTION_MAP` from `openubem/idf/compliance.py` and import the
patcher's own module-level map instead.
**Why.** One definition, so the audit cannot drift from the code it audits (G1/G2).
**How.** Import only; no behaviour change, no other edit to either file. If the patcher's map is not
importable as a module-level name, STOP and report rather than working around it.
**How to test.** `python -m pytest tests/test_compliance_audit.py tests/test_envelope_patcher.py
tests/test_envelope_patcher_windows.py -q` — all 29 still green.

**Manager ruling at SR-G (2026-09-17): option (a).** The audit stays a library function that nothing
calls. The census measured 18 of 18 genuine `layout_assign` buildings clean, and the only 2 failures
are `OpenUBEMUnknown`, which has no `layout_assign` baseline and structurally falls back to the
`auto` path where `patch_envelope()` never runs — so a gate turned on today would fail buildings for
a reason that is not an envelope defect. Same reasoning as block 2's prep gate shipping OFF. (b) and
(c) are not started. The 150 `GROUND_SURFACE_UNPATCHED` surfaces are recorded as information and
remain the open D3 two-ground-model question, unchanged.

#### G03 — Remove the duplicated surface map — completed 2026-09-17
**Artifacts:** `openubem/idf/compliance.py` (removed the locally re-declared
`_LA_SURFACE_CONSTRUCTION_MAP`, added `from openubem.geometry.envelope_patcher import
_LA_SURFACE_CONSTRUCTION_MAP`).
**Deviations:** none. Verified by grep that both dicts were module-level names (column 0 in each
file) and byte-identical in content (4 keys: wall/roof/floor/ceiling to LA_Wall_Construction/
LA_Roof_Construction/LA_Floor_Construction/LA_Floor_Construction) before editing.
**Test status:** `python -m pytest tests/test_compliance_audit.py tests/test_envelope_patcher.py
tests/test_envelope_patcher_windows.py -q` — 29 passed.
**Notes:** No behaviour change; import only, per plan.
