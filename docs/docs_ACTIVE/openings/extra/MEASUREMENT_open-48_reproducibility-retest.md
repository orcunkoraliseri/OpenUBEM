# MEASUREMENT — OPEN-48: re-test reproducibility against the live tree

**Task:** T01 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`.
**Date:** 2026-08-18.
**Script:** `scripts/analysis/open48_reproducibility_retest.py`.
**Output:** `openubem/outputs/comparisons/open48_reproducibility_retest.csv`.

## 1. What this re-tests

OPEN-48's register evidence table (register `:4985-4991`) was assembled 2026-08-12, before ruling
`2d` restored `assign_elevators` wiring into `builder.py` (commit `6aeebb0`, 2026-08-13). Every claim
in that table is a "live tree today" claim, so every row is a candidate to be stale. This document
re-derives all five rows plus a live-build count, against HEAD as of 2026-08-18, with a positive
control on the detection method.

## 2. Control

Before trusting any "absent at HEAD" result, the detection method must be shown to find a symbol known
to be present.

```
git log --all -S "def assign_elevators" -- openubem/idf/elevators.py
```
→ `commit ef19141f93439d8a598b8ef615c139671b36e13e` (the commit that added `elevators.py` itself).
The `-S` search finds a known-present definition. **Control passes.**

## 3. The five rows, re-derived

| # | Register's original claim (2026-08-12) | Command | Raw result at HEAD (2026-08-18) | Still true? |
|---|---|---|---|---|
| 1 | `assign_elevators` called from `builder.py`: **no** — `git log --all -S ...` empty; `hasattr` `False`; zero "elevator" occurrences | `git log --all -S assign_elevators -- openubem/idf/builder.py` | `commit 6aeebb0db742cc797b70ab19087cc8056a64d63a` (non-empty) | **NO — now false** |
| 1b | (same row) `hasattr(builder, 'assign_elevators')` | `hasattr(openubem.idf.builder, 'assign_elevators')` | `True` | **NO — now false** |
| 1c | (same row) "elevator" occurrence count in `builder.py` | `inspect.getsource(builder).lower().count('elevator')` | `3` (import at line 40, call at line 609, plus one more reference) | **NO — now false** |
| 2 | `elevators_eui_kwh_m2` in results: **absent** at HEAD | `'elevators_eui_kwh_m2' in inspect.getsource(openubem.results.aggregator)` | `True` (also present in `openubem/results/parser.py` and `openubem/results/carbon.py`) | **NO — now false** |
| 3 | `gwp_elevators_kgco2_m2`: **absent** at HEAD | `'gwp_elevators_kgco2_m2' in inspect.getsource(openubem.results.carbon)` | `True` | **NO — now false** |
| 4 | elevator meter in `outputs.py`: **absent** at HEAD (13 meters) | `'Elevators:InteriorEquipment:Electricity' in openubem.idf.outputs.HVAC_METERS` | `True` (`len(HVAC_METERS) == 14`) | **NO — now false** |
| 5 | elevator equipment emitted by a live build: **zero objects**, all 10 elevator archetypes | live build, LargeOffice/12 levels, count `ELECTRICEQUIPMENT` with `EndUse_Subcategory == "Elevators"` | `generation_status=success; count=1; names=['Elevators_LargeOffice']` | **NO — now false** |

Negative control on row 5 (added by this measurement, not in the original table): the same live-build
method applied to a **non-eligible** archetype (SmallOffice, 1 level) emits **0** elevator objects
(`generation_status=success; count=0`) — confirming the detector is not simply always returning a
non-zero count.

**Every row of the table is now the opposite of what it said in 2026-08-12.** All five rows are
individually reproduced as false-today, using the item's own stated commands plus one live build. Full
CSV: `openubem/outputs/comparisons/open48_reproducibility_retest.csv`.

## 4. Which build method was used

**A real, direct build was run — not the pytest fixture.** `BuildingIDF(row).build(gdf, {}, out_path)`
was called directly from the analysis script (`scripts/analysis/open48_reproducibility_retest.py`),
using the same synthetic fixtures (`tests/fixtures/synthetic.epw`) and the same construction pattern as
`tests/test_builder_elevators_wired.py`, but as a standalone script run, not a test assertion.
`BuildingIDF.build()` performs no network access and does not invoke the EnergyPlus binary — it only
constructs an in-memory `IDF` object and writes it to a temp directory, so this satisfies the plan's "no
live-network integration tests" rule while still being a live, real build.

`tests/test_builder_elevators_wired.py` was also read (not re-run standalone here) and asserts the same
two cases (elevator-eligible emits one object named `Elevators_<archetype>`; non-eligible emits none)
via pytest — it is part of the full-suite baseline reported elsewhere in the register (already-quoted:
`1875 passed, 55 skipped, 11 warnings`, per the register's OPEN-46 closure note at `:681`, itself dated
2026-08-18 T01 of a different plan, `PLAN_four-items-2026-08-18.md`). That number is quoted, not
re-derived by this task — this task's own re-derivation is the direct-script build above.

## 5. Reporting half vs. load-wiring half

The item itself separates these two halves. Both are now live and committed:

- **Reporting half** (parser → outputs meter → carbon → aggregator): `elevators_eui_kwh_m2` present in
  `openubem/results/parser.py`, `openubem/results/aggregator.py`; `gwp_elevators_kgco2_m2` present in
  `openubem/results/carbon.py`; `Elevators:InteriorEquipment:Electricity` present in
  `openubem/idf/outputs.py`'s `HVAC_METERS` (14 meters total). **Live and committed.**
- **Load-wiring half** (`builder.py` emitting the equipment object): `assign_elevators` imported at
  `openubem/idf/builder.py:40` and called at `:609`; live build confirmed above emits exactly one
  `ElectricEquipment` object named `Elevators_LargeOffice` for an eligible archetype and zero for a
  non-eligible one. **Live and committed.**

`git status --porcelain openubem/idf/builder.py openubem/idf/elevators.py openubem/idf/outputs.py openubem/results/parser.py openubem/results/aggregator.py openubem/results/carbon.py`
→ **empty output** (checked as part of the broader `git status --porcelain` in §6). Nothing in either
half is uncommitted.

## 6. Can the adopted `phaseE_elevrb` run be regenerated from version control now?

**Short answer: still no — but not for the reason the original table gave, and not for a code-provenance
reason at all.** The code (both halves, §5) is fully committed. The remaining gap is documented
elsewhere in the register itself and is re-confirmed here rather than assumed:

1. **`git status --porcelain`** at repo root, run fresh for this task, shows only four untracked
   files, all belonging to this pass: this plan doc, this measurement's own script/CSV, and
   `tests/test_zzz_open13_control.py` (T03's territory, not touched by T01). **Nothing tracked is
   modified; nothing elevator- or semantic-related is uncommitted.**
2. A second, independent code path affects whole-run reproducibility and was checked because the
   register's own OPEN-49 section names it as the actual blocker: the `wwr`/PDE-column
   re-randomisation mechanism. `openubem/semantic/__init__.py` now contains `_per_building_rng`
   (line 212) and an unconditional `_get_cross_archetype_loads()` call at the `enrich_semantics` site
   (line 366) — the per-building-seed fix the register records as landed 2026-08-17. `git log --oneline
   --all -- openubem/semantic/__init__.py` shows this file's most recent commit is `82bbd25`
   ("docs/tests: complete test suite triage, tagrich gate fixes, and openings measurement updates"),
   and `git status --porcelain openubem/semantic/` is empty. **This fix is also fully committed.**
3. **No third fleet run exists on disk.** `docs/docs_VALIDATION/validations/overAll/results/` contains
   exactly two adopted-baseline directories, `phaseE` and `phaseE_elevrb` — no post-fix re-run. This
   matches the register's own account: ruling 4 of `PLAN_open-49-and-open-01-2026-08-13.md` explicitly
   declined a third fleet run in favour of a twelve-cell before/after at fixed classification.
4. **What is still missing, precisely:** not code — a *confirmed end-to-end number*. The
   2026-08-13 twelve-cell re-run (`open48_refleet`) that reproduced the elevator column exactly was run
   under the **pre-fix** `wwr` mechanism and diverged from the adopted run by +2.16 kWh/m² pooled, for a
   reason the register traces to input drift (OSM re-fetch classification change), not to missing code.
   That divergence's *mechanism* is now fixed and committed (point 2), but **nobody has re-run the fleet
   through the current, fixed HEAD to confirm it reproduces `157.1` (or lands somewhere else) end to
   end.** Additionally, the register records that the adopted run's own original `01_buildings.gpkg`
   snapshot no longer exists, so even a fresh OSM fetch today cannot be diffed against the exact
   population the adopted run used — an external-data provenance gap, not a version-control one.

**So: the load and reporting code that produced `phaseE_elevrb`'s elevator columns is now 100%
reconstructable from HEAD — confirmed, not assumed, by the checks above. The provenance gap that
remains is (a) no post-fix fleet re-run has been executed, and (b) the original input snapshot for the
adopted run is gone. Neither is a "missing commit" problem any longer.**

## 7. Answer to the item's own one-line finding

*"Running the pipeline from the current tree would produce different numbers and a missing column."*

**The "missing column" half is now false** — confirmed in §3, row 2–4: both elevator columns and the
meter are present at HEAD. **The "different numbers" half is not resolved by this task** — it was
already measured by the 2026-08-13 twelve-cell re-run (quoted, not re-derived here: pooled EUI
159.2157 vs adopted 157.0552, attributed to OPEN-49's pre-fix mechanism) and no fresh re-run exists
under the now-fixed code to update that number. This task's contribution is: the code-provenance
question is fully answered (yes, reconstructable), and what remains is an execution gap (no re-run) and
a data-provenance gap (original snapshot gone), both already on the record under OPEN-48's own
Amendment 2026-08-13 and under OPEN-49.

## 8. Does this change OPEN-48's status?

**No — it stays OPEN, and the reason for that has partially shifted; this is stated explicitly rather
than left implicit.** OPEN-48's own Amendment 2026-08-13 said it stays open "until OPEN-49 is fixed and
the fleet is re-run a third time." As of this measurement:

- OPEN-49's mechanism **is** fixed and committed (§6.2) — this half of the stated condition is now
  satisfied, which was not yet true on 2026-08-13.
- The fleet has **not** been re-run a third time (§6.3) — this half is not satisfied, and per the
  register's OPEN-49 section, ruling 4 explicitly declined that re-run in favour of a different check.

The conjunction in OPEN-48's own stated closing condition is therefore still not met, so the item
correctly stays open — but the register should reflect that the reason has narrowed: it is no longer
"code is missing," it is now solely "no post-fix fleet re-run has been authorised or executed."
Whether to authorise one is a ruling for the user, not a measurement conclusion — this task does not
recommend one way or the other, per the plan's "do not fix, recommend and stop" rule; it only reports
that the remaining blocker is now narrower and named.

## Register amendment applied

T01 holds the pen for OPEN-48 (plan §2 rule 9). The register's evidence table and status line were
struck in place (not deleted) and a new dated block was appended directly in
`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`, citing this document and its CSV.
See the register itself for the applied text; it is not duplicated here.
