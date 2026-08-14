# MEASUREMENT — OPEN-44: triage of the real-suite (`tests/`) failing/erroring nodes

**Task:** T02, `PLAN_two-measurements-2026-08-13.md`
**Date:** 2026-08-13
**Supersedes:** the `tests/`-tree portion of the 2026-08-12 T05 report (`PLAN_rulings-and-five-items-2026-08-12.md`).
That report's `tests/`-only run (25 failed / 1788 passed / 10 skipped / 19 errors) is now stale — commit
`6aeebb0` (2026-08-13, same day, ahead of this run) touched 9 files under `tests/` and shipped the elevator
EUI breakout. This report replaces it for the `tests/` tree; it does not touch or re-derive the `docs/` /
`scripts/analysis/` portion of the old report, which T02 is not scoped to.

## Run

```
./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/ --ignore=docs --tb=short \
    --junitxml=<scratchpad>/open44_junit.xml
```

**26 failed, 1857 passed, 10 skipped, 19 errors, exit 1, 1171.43s (19m31s), 1912 collected.**
Numbers recomputed from the run's own JUnit XML (`tests=1912 errors=19 failures=26 skipped=10`) and
stdout, both captured this run — not carried over from memory or the prior report.

**Reconciliation, both directions, stated explicitly per plan rule:**

- **Against plan §4.9's baseline (70 failed / 1822 passed / 10 skipped / 36 errors, 2026-08-12,
  whole-repo):** does **not** reconcile, and is not expected to — §4.9's run collected the whole repo
  (including the 61 `docs/` nodes and 1 `scripts/analysis/` node that are outside the real suite); this
  run is scoped to `tests/` only, exactly as T02 §5 step 1 requires. Both are shown; neither is silently
  adopted as the other.
- **Against the 2026-08-12 T05 same-scope run (25 failed / 1788 passed / 10 skipped / 19 errors, 44
  nodes, `tests/`-only):** does not reconcile either, and the cause is fully accounted for, not a
  measurement error. `git log -1 -- tests/` shows the most recent commit touching `tests/` is `6aeebb0`,
  timestamped 2026-08-13 15:25 — **after** the T05 baseline was taken. Three effects, confirmed by reading
  the commit diff and the shipped code it touched:
  1. **Elevator EUI breakout shipped.** `openubem/results/parser.py:347` now computes
     `eui["elevators_eui_kwh_m2"]` and `openubem/idf/outputs.py:43` lists the
     `Elevators:InteriorEquipment:Electricity` meter — both were missing at T05 time (T05's report named
     this the cause of 8 failures in `tests/test_parser_elevators.py`). Those 8 tests now pass.
  2. **Two new test files, fully green.** `tests/test_err_parse.py` (OPEN-45, 15 tests) and
     `tests/test_builder_elevators_wired.py` (OPEN-48, 2 tests) were added in the same commit; all 17 pass
     in this run.
  3. **`tests/test_draw_methods.py`'s blanket module-level skip was narrowed.** Before today, the entire
     file carried `pytest.skip(..., allow_module_level=True)` (git `show 6aeebb0 -- tests/test_draw_methods.py`
     confirms the removed lines) — so **none** of its tests were ever counted in any prior tally, including
     T05's 44. Today's commit replaced that blanket skip with a single `@pytest.mark.skipif` on one class
     (`TestNoEUILeakage`, gated on `_HAS_DRAW_TIER = hasattr(imp, "_draw_tier") and hasattr(imp,
     "_draw_stratum_col_for")`), unmasking the other 52 tests in the file for the first time. Of those 52:
     43 pass, 9 fail (see `stale-expectation` below), and the 1 remaining `TestNoEUILeakage` test is now a
     narrow, confirmed `skipped` (it is one of this run's 10 skips — verified directly against the JUnit XML).
  Net effect on the failed count: −8 (elevator fix) + 0 (new files, all green) + 9 (draw-tier unmask) = **+1**,
  matching the observed 25→26. This is a coincidence of magnitude, not a coincidence of cause — three
  independent, fully-explained shifts happen to net to +1.

## Classification

Every failing/erroring node was classified by reading the test and the shipped code it exercises — no
node was classified from the exception text alone.

| category | count |
|---|---|
| `artifact-missing` | 31 |
| `stale-expectation` | 14 |
| `fixture-missing` | 0 |
| `real-defect` | 0 |
| `undetermined` | 0 |
| **total** | **45** |

CSV: `openubem/outputs/comparisons/open44_test_triage.csv` — one row per node, columns `nodeid, outcome,
exception_type, message_first_line, category, evidence, shipped_code_citation`. **45 data rows**, verified
equal to this run's own failed+error count (26+19=45) by the generating script's own assertion (it raises
if any classified nodeid is absent from the run, or if any failing/erroring node lacks a classification).

**Zero `real-defect`.** Checked, not assumed: every failure/error in this run traces to either (a) a disk
artifact absent on this machine (`artifact-missing`, 31: the `docs/docs_DONE/phaseC_combinedResim/
v19_validation/` directory does not exist at all, 26 nodes across `test_v19_basis_diagnostic.py` +
`test_v19_national_cbecs_rescore.py`; and the imputation phase-figure PNGs referenced by
`test_impute_montage.py`, 5 nodes, are not on disk), or (b) a config attribute the test asserts against
that was never shipped (`stale-expectation`, 14: `config.IMPUTE_DEBIAS_NEWERSKEW`, 5 nodes;
`config.IMPUTE_DRAW_METHOD_BY_TARGET` / the "draw" entry in `_CANONICAL_TIER_ORDER`, 9 nodes). No node
exercises shipped code that runs and produces a wrong result.

**Zero `fixture-missing`.** The one pattern this category names (a fixture function that pytest cannot
find, e.g. `synthetic_10_gdf` in the 2026-08-12 sweep) exists only in the archived `docs/` tree, which is
out of T02's scope. Every setup-time `ERROR` this run (19, all in the two `v19_*` files) is a fixture that
pytest **found and ran**, which then raised `FileNotFoundError`/`OSError` while writing into the missing
`v19_validation/` directory — that is `artifact-missing`, not a missing-fixture wiring problem.

**Zero `undetermined`.** All 45 nodes were traced to a named, confirmed cause without changing any code.

## `IMPUTE_DEBIAS_NEWERSKEW` coverage cost (plan §5 step 4, T02 rule 4)

`tests/test_debias.py` has **14 tests total** (`pytest --collect-only`, confirmed). **5 fail**
(`TestMlTierDebiasHook`, all `AttributeError: module 'openubem.config' has no attribute
'IMPUTE_DEBIAS_NEWERSKEW'` — confirmed absent by a full read of `openubem/config.py`, 164 lines, today).
**9 currently pass**: `TestDebiasNewerSkewMarginalAndRank` (2), `TestDebiasPullsNewerSkewTowardDonorMean`
(1), `TestThinStratumSkip` (2), `TestDeterminism` (2), `TestNoEUILeakage` (1),
`TestImputeMissingDefaultOff` (1) — these exercise `openubem/semantic/debias.py`'s actual functions
directly and do not reference the missing config attribute.

- **Minimal fix (skip/delete only the 5 red tests) costs exactly 5 tests of coverage** — all specifically
  of the intended `_ml_tier` hook-wiring behaviour (quantile-map correction of a non-thin stratum,
  thin-stratum skip, the no-stratifier-column global fallback and its own min-donor floor, and the
  `knn`-only method gate). Grepped: no other test file in `tests/` or `docs/` references
  `IMPUTE_DEBIAS_NEWERSKEW` or exercises this specific hook path, so none of that behaviour would be
  covered anywhere else afterward.
- **A blunter suppression — skip or delete at the module/file level — would additionally and silently
  kill the other 9 currently-passing tests**, for a **total cost of 14, the entire file**. This is the
  exact shape named in plan §4.10 (E-UTCI-12: a fix that restored green by removing 43 passing tests).

## A second instance of the same shape, found but not costed (out of this task's named scope)

`tests/test_draw_methods.py`'s 9 failures are the **identical pattern** one file over: a config surface
(`config.IMPUTE_DRAW_METHOD_BY_TARGET`) and a tier-order entry (`"draw"` in `imputation.py`'s
`_CANONICAL_TIER_ORDER`, confirmed absent — `openubem/semantic/imputation.py:543` reads
`("fusion", "spatial", "ml", "statistical")`) that the draw tier's own module explicitly documents as
"opt-in / OFF by construction ... until a future task (T07) wires `_draw_tier` into
`imputation.py`'s `_CANONICAL_TIER_ORDER`" (`openubem/semantic/draw_methods.py:5-9`). Plan §5 step 4 named
`IMPUTE_DEBIAS_NEWERSKEW` specifically, so this group is not costed here — flagged per hard rule 5 ("report
what you did not find") so it is not silently missed a second time.

## What I could not determine

- Whether `tests/test_draw_methods.py`'s draw-tier gap and the "draw tier" arc referenced in project memory
  (`project_variance_preserving_draw_arc.md`, noted there as closed/parked) are the same item under a
  different name, or two separate decisions — I did not open that file; doing so would have widened this
  task past the two config-attribute groups actually asked for.
- Whether any of the 10 currently-`skipped` tests (not in scope — the plan's closed set covers only
  failing/erroring nodes) would themselves fail if unblocked. One in particular,
  `test_draw_methods.py::TestNoEUILeakage::test_no_function_code_references_eui_by_name`, is the one test
  in that file still gated (via `skipif` on `_HAS_DRAW_TIER`) specifically because it would need
  `imp._draw_tier` / `imp._draw_stratum_col_for` to exist — it is the guard that would catch an EUI-leak
  regression if the draw tier is ever wired in, and it is not currently exercising anything.
- Whether this run is free of order-dependent flakiness — it was executed once (~19.5 min); all 45
  failures/errors are deterministic (missing attribute or missing path), not timing-shaped, so this is a
  low-suspicion gap, not a known one.

## Files written

- `scripts/analysis/open44_test_triage.py` — parses the run's JUnit XML, applies a by-hand classification
  keyed by exact node id (raises if any failing/erroring node is unclassified, or if any classified node
  id did not actually fail/error in the run — both-directions reconciliation is enforced in code, not just
  asserted in prose), writes the CSV.
- `openubem/outputs/comparisons/open44_test_triage.csv` — 45 data rows.
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-44_test-triage.md` — this file.

No test was fixed, skipped, deleted, or edited. No file under `docs/` was modified. No `pytest.ini` /
`pyproject.toml` collection setting was changed. Fully local; no cluster.
