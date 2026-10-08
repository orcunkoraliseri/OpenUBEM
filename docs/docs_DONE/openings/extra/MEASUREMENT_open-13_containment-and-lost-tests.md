# MEASUREMENT — OPEN-13: E-UTCI-12 containment at HEAD, and independent verification of the 43 traded-away tests

**Task:** T09 of `../implemenation/previous/PLAN_twenty-items-2026-08-19.md`. Script:
`scripts/analysis/open13_t09_containment_and_lost_tests_2026-08-19.py`. Output:
`openubem/outputs/comparisons/open13_t09_containment_and_lost_tests.csv`.

## 1. Part (a) — does the containment still hold at HEAD, and what does "contained" mean operationally

**The defect is still live, unfixed, only contained.** `grep -c "_draw_tier" openubem/semantic/imputation.py` → **0**, re-confirmed fresh today. The router hook the draw tier would need has never been added (independently re-verified again in this pass's T12, `extra/MEASUREMENT_open-17_router-hook-archaeology.md`).

**The containment mechanism**, read directly at `tests/test_draw_methods.py:50`:

```python
_HAS_DRAW_TIER = hasattr(imp, "_draw_tier") and hasattr(imp, "_draw_stratum_col_for")
```

`hasattr()` never raises even when the attribute is absent — it returns `False`. This is what changed operationally: before the 2026-08-12 fix, the module *imported* `imp._draw_tier` directly (a name that does not exist), which raised `AttributeError` at **collection time**, aborting collection for the whole file (and, before `pyproject.toml:52`'s `testpaths` fix, for a bare `pytest -q` repo-wide). `hasattr` converts that same absence into a boolean the module can safely branch on. Individual tests that need the two missing symbols carry `@_SKIP_NO_DRAW_TIER` (a `pytest.mark.skipif(not _HAS_DRAW_TIER, ...)` built from that boolean) or, for one test, an equivalent class-level `skipif`; every other test in the file has no dependency on those two symbols and is never gated by the guard at all.

**"Contained" means, precisely**: the defect (an unimplemented router hook) is downgraded from a collection-time abort (blocking the entire suite) to a scoped, per-test `skipif` (blocking exactly the tests that need the missing symbols, and nothing else). It does not implement the hook; it does not remove the defect; OPEN-17 still owns "should the hook be built."

**Constructed case that the containment "contains"**: any test decorated with `_SKIP_NO_DRAW_TIER` demonstrates it directly — e.g. `tests/test_draw_methods.py:676`, `TestDrawTierRouting::test_draw_tier_fills_with_kde_provenance_when_opted_in`. Running it today:

```
.venv/Scripts/python.exe -m pytest -q tests/test_draw_methods.py -rs
```
reproduces **43 passed, 10 skipped** — the 10 being exactly the tests needing `_draw_tier`/`_draw_stratum_col_for`, with the skip reason printed for each (all ten reasons read, not just counted — every one names `OPEN-44 / OPEN-13 / OPEN-17 / OPEN-36` or `OPEN-13 / OPEN-17 / OPEN-36` and the same underlying cause).

## 2. Part (b) — independent verification of the 43 traded-away tests

**What was traded, and when, read from git history rather than the register's own account:**

- `a3bf4d9` (2026-08-12, the containment commit) added a **module-level** `pytest.skip(..., allow_module_level=True)` (`tests/test_draw_methods.py`, +13 lines) — this skipped **all 53** tests in the file, not just the 10 that need the missing symbols, because a module-level skip has no way to discriminate between tests. This is the trade: the file went from "aborts collection for the whole repo" to "collects, but 0 of its 53 tests run" — 43 tests that had no dependency on the draw tier stopped running as a side effect.
- `6aeebb0` (2026-08-13) narrowed this to individual `@_SKIP_NO_DRAW_TIER` decorators (+31/-25 lines) — restoring the 43 to running state, leaving only the 10 genuinely dependent tests skipped.

**Independent re-derivation, not a repeat of the register's own account:**

1. **Function-set diff, pre-containment (`25924dd`, the parent of `a3bf4d9`) vs HEAD**: `grep -oP "def \K test_\w+"` extracted from `git show 25924dd:tests/test_draw_methods.py` and from the HEAD file. **53 `def test_` occurrences on both sides**; deduplicated-by-name sets (44 unique names each, since several names repeat across sibling test classes such as `TestKDE`/`TestPMM`/`TestHotdeck`) are **set-identical — zero present-before/absent-now, zero present-now/absent-before**. No test was deleted or renamed anywhere in this file between the pre-containment commit and HEAD.
2. **Fresh run, per-node-ID classification**: `pytest tests/test_draw_methods.py -v --no-header`, all 53 node IDs captured, each classified as `still_present_and_passing` (43) or `skipped_future_feature_pin` (10). **Zero** fell into a `deleted_or_renamed_MISMATCH` bucket. Full per-test table: `openubem/outputs/comparisons/open13_t09_containment_and_lost_tests.csv`.

**Verdict for (b): the 43 are NOT still absent at HEAD.** They were traded away by the 2026-08-12 containment commit and restored by the 2026-08-13 narrowing commit — independently confirmed here by diffing the actual function set (not trusting the register's prose) and by a fresh, today's-date test run (43 passed / 10 skipped, matching `6aeebb0`'s stated outcome exactly).

## 3. F9 baseline — full suite, run fresh

```
.venv/Scripts/python.exe -m pytest -q tests/
```

**1919 passed, 55 skipped, 11 warnings in 1240.80s (0:20:40).**

**Reproduces F9 exactly** — 1,919 passed / 55 skipped, no deviation. Per rule 11 and the task's own "how to test" clause ("any deviation is itself a finding — report it, do not chase it"): there is no deviation to report. This also answers why F9 is safe to interpret alongside part (b): the 43 tests this task confirmed are running today are already counted inside that 1,919 — they are not a separate population sitting outside the baseline.

## 4. What this changes for OPEN-13

Nothing about the item's open/closed status — this task recommends nothing beyond what is already on record. It **independently corroborates**, rather than merely restates, two things the register's prose already claimed: that the 43 tests are back (traced through git history and a fresh per-test classification, not taken on trust) and that F9 is unaffected (re-run fresh, exact match). E-UTCI-12 remains open, contained not fixed, and its only remaining technical content is OPEN-17's router-wiring decision, exactly as the register already states.
