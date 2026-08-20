# MEASUREMENT — OPEN-46 / T04: divergence inventory (code + prose)

**Executor:** B. **Date:** 2026-08-12. **Scope: EVIDENCE ONLY. No source file edited.**
**Artifacts:** `scripts/analysis/open46_elevator_divergence.py`,
`openubem/outputs/comparisons/open46_elevator_divergence.csv` (12 rows),
`openubem/outputs/comparisons/open46_tenth_enduse_claims.csv` (15 rows).

## Headline, up front

Inventory A confirms everything §4 and the register already state about `parser.py` / `outputs.py` /
`carbon.py` / `aggregator.py` and the five test twins, **and adds one finding those did not check:
`openubem/idf/builder.py` itself never calls `assign_elevators`.** `git log --all -S
"assign_elevators" -- openubem/idf/builder.py` returns nothing — the string was never added or
removed in this file's tracked history. The only commit that ever touched `assign_elevators`
(`ef19141`, 2026-07-21) added it **only** to the archived copy
(`docs/docs_DONE/.../elevators/scripts/openubem/idf/builder.py`), never to the live one. Running the
project's own build-only validation script, `scripts/validation/elevators_live_smoke.py`, against
current code confirms this empirically: **every one of the 10 elevator archetypes builds an IDF with
zero `Elevators` `ElectricEquipment` objects**, and the script itself crashes
(`AttributeError: module 'openubem.idf.builder' has no attribute 'assign_elevators'`) trying to run
its own no-op comparison. `openubem/idf/elevators.py` is present and importable in the live tree, but
it is **orphaned dead code** — nothing in the live package calls it.

This affects how OPEN-46's existing framing should be read. The register (line 2863) and the board
(N10) state: *"`openubem/idf/elevators.py` is live... that energy is simulated and is counted inside
`equipment_eui_kwh_m2`... What is missing is only the separate reporting line."* That statement is
about the **file existing**, not about it being **on the call path**. Per hard rule 12, this
disagreement is reported and not adjudicated here — the director decides. Two things are consistent
with each other and worth separating: (1) the **adopted** `phaseE_elevrb` baseline may well have been
built with elevators active, since the fleet re-baseline predates this drift and its directory name
(`ubem_elev_rebaseline`) and the 12-cell positive deltas recorded in
`project_elevator_loads_arc.md` match that; T03 could not confirm this because the SQL is gone. (2)
**Any build made with today's live `builder.py` — including whatever T05 or future runs would produce
— emits no elevator load at all**, not "elevator load folded into equipment." Whether the elevator
call site needs restoring as part of T05, and whether that changes T05's invariant-gate scope, is a
call for the director, not this task.

## Inventory A — code (12 rows, `openubem/outputs/comparisons/open46_elevator_divergence.csv`)

| # | file | verdict |
|---|---|---|
| 1 | `openubem/data/loads/elevators_by_archetype.json` | IDENTICAL, not a divergence (0 diff lines) |
| 2 | `openubem/idf/elevators.py` | IDENTICAL (0 diff lines), but **orphaned** — not called from anywhere live |
| 3 | `openubem/idf/builder.py` | **FEATURE MISSING** — call site never merged (254 diff lines total; only the `assign_elevators(...)` line is elevator-related, rest is unrelated growth 607→705 lines) |
| 4 | `openubem/idf/outputs.py` | **FEATURE MISSING** — `HVAC_METERS` 13 vs 14 (10 diff lines, all elevator-related) |
| 5 | `openubem/results/parser.py` | **FEATURE MISSING** (elevator lines) + **UNRELATED DRIFT** (`resolution_mode`/`layout_assign` zone-integrity branch, live-only, added after the archive) (117 diff lines total) |
| 6 | `openubem/results/carbon.py` | **FEATURE MISSING** — no `gwp_elevators_kgco2_m2` (48 diff lines) |
| 7 | `openubem/results/aggregator.py` | **FEATURE MISSING** (2 column entries) + **UNRELATED DRIFT** (OPEN-43 fleet-pooling docstring, live-only) (45 diff lines) |
| 8 | `tests/test_elevators.py` | IDENTICAL (0 diff lines); **28 passed** live — tests the emitter directly, bypasses builder |
| 9 | `tests/test_parser_elevators.py` | IDENTICAL (0 diff lines) — expectation **left in place**; **8 failed, 0 passed** live |
| 10 | `tests/test_outputs.py` | **EXPECTATION REMOVED** (25 diff lines, 3 assertions weakened 14→13); **11 passed** live |
| 11 | `tests/test_results_aggregator.py` | **EXPECTATION REMOVED** (34 diff lines, 2 keys dropped from 2 dict templates); **29 passed** live |
| 12 | `tests/test_step3_orchestrator.py` | **WHOLE TEST DELETED**, not edited (30 diff lines); **18 passed** live |

All diffs computed with line endings normalized (`\r\n`/`\r` stripped to `\n`) — a raw `diff` on these
files reports every line as changed because the two trees mix line-ending conventions; that is a
diff-tool artifact, not evidence of drift, and the script does not treat it as one.

**Confirms the register's count exactly:** of the five test twins, 2 are byte-identical
(`test_elevators.py`, `test_parser_elevators.py`) and 3 have the elevator expectation removed rather
than the feature added (`test_outputs.py`, `test_results_aggregator.py`,
`test_step3_orchestrator.py`). Live pytest run (all five files, one command):

```
FAILED tests/test_parser_elevators.py::TestElevatorMeterParsed::test_elevator_meter_read
FAILED tests/test_parser_elevators.py::TestElevatorMeterParsed::test_missing_elevator_meter_is_zero
FAILED tests/test_parser_elevators.py::TestElevatorsBrokenOut::test_elevators_is_own_column
FAILED tests/test_parser_elevators.py::TestElevatorsBrokenOut::test_elevators_defolded_from_equipment
FAILED tests/test_parser_elevators.py::TestElevatorsBrokenOut::test_total_unchanged_vs_summing_columns
FAILED tests/test_parser_elevators.py::TestElevatorsBrokenOut::test_total_invariant_to_breakout
FAILED tests/test_parser_elevators.py::TestGwpInvariant::test_gwp_total_invariant_to_breakout
FAILED tests/test_parser_elevators.py::TestFailedRowHasElevators::test_failed_row_includes_elevators_column
8 failed, 86 passed in 51.28s
```

Per-file breakdown (run separately): `test_elevators.py` 28 passed; `test_parser_elevators.py` 8
failed/0 passed; `test_outputs.py` 11 passed; `test_results_aggregator.py` 29 passed;
`test_step3_orchestrator.py` 18 passed (includes `<cannot get C stack on this system>` — an
environment warning, not a test failure).

### The builder.py finding, in full

- Live `openubem/idf/builder.py`'s `build()` method (service-load block, live lines ~599-610):
  `assign_hvac(...)` → `assign_dhw(...)` → `assign_cooking(...)` → `assign_refrigeration(...)` →
  `write_outputs(...)`. No `assign_elevators` call anywhere between refrigeration and outputs, or
  anywhere else in the file.
- Archived `docs/docs_DONE/.../elevators/scripts/openubem/idf/builder.py:509`:
  `assign_elevators(self.idf, row, extruded_zones)`, in exactly that slot.
- `python -c "import openubem.idf.builder as b; print(hasattr(b, 'assign_elevators'))"` → `False`.
- `grep -rin "elevat" openubem/` (whole live package tree) matches only
  `openubem/data/loads/elevators_by_archetype.json` and `openubem/idf/elevators.py` itself (plus
  unrelated "elevation" false positives in `layout_assigner.py`, `microclimate/*.py`, and the IDF
  templates — checked individually, all are terrain/site elevation, not elevators).
- Running `scripts/validation/elevators_live_smoke.py` (build-only, no EnergyPlus) against current
  code:
  ```
  archetype            emitted_W  total_m2  kWh/m2/yr    CP-1  status
  College             FAIL: expected 1 Elevators object, got 0
  HighriseApartment   FAIL: expected 1 Elevators object, got 0
  Hospital            FAIL: expected 1 Elevators object, got 0
  LargeHotel          FAIL: expected 1 Elevators object, got 0
  LargeOffice         FAIL: expected 1 Elevators object, got 0
  MediumOffice        FAIL: expected 1 Elevators object, got 0
  MidriseApartment    FAIL: expected 1 Elevators object, got 0
  Outpatient          FAIL: expected 1 Elevators object, got 0
  SecondarySchool     FAIL: expected 1 Elevators object, got 0
  SmallHotel          FAIL: expected 1 Elevators object, got 0
  --------------------------------------------------------------
  Byte-identity check — SmallOffice (no elevator object in table):
  Traceback (most recent call last):
    ...
  AttributeError: module 'openubem.idf.builder' has no attribute 'assign_elevators'
  ```
- `git log --oneline -S "assign_elevators"` (whole repo, no path filter) → exactly one commit,
  `ef19141 feat: add elevators, debias, fusion, and layout generator updates` (2026-07-21). `git show
  --stat ef19141` shows it added the archived `elevators/scripts/openubem/{idf/builder.py,
  idf/elevators.py, idf/outputs.py, results/{carbon,parser}.py}` files **and separately** added the
  live `openubem/idf/elevators.py`, `openubem/data/loads/elevators_by_archetype.json`,
  `tests/test_elevators.py`, `tests/test_parser_elevators.py`, `scripts/cluster/elevator_ab_*.py`, and
  `scripts/validation/elevators_live_smoke.py` — but did **not** touch the live
  `openubem/idf/builder.py`, `openubem/results/parser.py`, `openubem/idf/outputs.py`, or
  `openubem/results/carbon.py`. `git log --all -S "levator" -- <each of those four live files>`
  independently confirms none of them has ever had an elevator-related line added or removed in
  tracked history. **The edits to those four shared files were written only into the archive copy at
  the moment the arc was archived; they were never merged into the live package.** No launcher script
  for the `phaseE_elevrb` rebaseline survives in the repo (`grep -rl "elev_rebaseline"
  --include="*.py" .` finds nothing outside this task's own new files), so exactly which code path
  built the adopted run cannot be re-derived from the repo alone — this is stated as a gap, not
  guessed.

## Inventory B — prose (15 rows, `openubem/outputs/comparisons/open46_tenth_enduse_claims.csv`)

Non-vacuity control (hard rule 7): a scratch file was written containing the string *"the 10th
end-use claim"*, the same regex set used for the real scan was run against it, and it matched (then
the scratch file was deleted). Scan covered `openubem/`, `scripts/`, `tests/`, `docs/docs_ACTIVE/`,
and `docs/PROJECT_CHECKLIST.md`, matching any of: `10th end-use`, `tenth end-use`, `10-way`,
`ten end-uses`, `ten-way` (case-insensitive).

15 hits, all listed in the CSV. By source:

- **`tests/test_parser_elevators.py:5`** (live tree) — docstring: *"...in total. T05 breaks them out
  into a mutually-exclusive 10th end-use while keeping..."* — this is a **currently-live file** making
  the claim, attached to a test that currently fails.
- **`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md:2865`** — already a correction,
  quoting the phrase as false: *"the adopted-baseline phrase 'elevators, the 10th end-use' describes
  the archived arc, not the live code."*
- **`docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html:606-607`** and the identical
  copy at **`docs/docs_ACTIVE/openings/reporting/board_published-numbers.html:606-607`** — item N10,
  already framed as `"open"`: *"Elevators are not the tenth end-use they are described as."*
- **`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_rulings-and-five-items-2026-08-12.md:750`** —
  references the open decision, not an assertion.
- **`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_three-new-items-2026-08-12.md:252,262,292,304,424`**
  — this plan itself (the one this task executes), forward-looking / conditional language about what
  T05 should do, not a standing claim.
- **`docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md:280,1015`** — director
  prompt discussing/quoting the open question.
- **`openubem/outputs/comparisons/open36_completion_record_sweep.csv:110`** — a prior open item's CSV
  artifact, quoting the archived plan's own line ("Elevators as a 10th end-use column").

**`docs/PROJECT_CHECKLIST.md`** — zero hits for the exact "10th end-use" phrase family. A broader,
non-exact search (not part of the regex scan, done separately by eye) found line 151: *"`phaseE` +
E-R3-3 correction + elevators. NYC −31.3% / LA −3.6% / Austin −30.5%, fleet..."* — this names elevators
as part of the adopted baseline's definition but does not use "10th end-use" or claim a separate
reporting line; flagged here for completeness since the task names this file explicitly, but it is not
counted as a "10th end-use" claim.

**Reading:** none of the 15 hits is a live claim asserting, uncorrected, that the separate reporting
line already exists and is trustworthy — the register and board entries are corrections, and the plan
docs are forward-looking. The one item worth the director's attention is
`tests/test_parser_elevators.py:5`: it is a **live, currently-failing test file** whose docstring
still describes the 10-way breakdown as implemented, which is accurate only for the archived code, not
the live code that test file is nominally testing.

## What was NOT done

- No source file was edited (per §1 hard rule 3 / T04's explicit restriction).
- No verdict is offered on whether T05 should also restore the `builder.py` call site — that is a
  scoping decision for the director, flagged here as a fact this inventory surfaced, not resolved by
  this task.
- The question of which code path built the adopted `phaseE_elevrb` run is reported as unresolved
  (no surviving launcher script), not guessed at.
