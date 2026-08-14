# MEASUREMENT — OPEN-36: proposed correction text for the T07 completion record

**Task:** T04, `PLAN_five-items-2026-08-13.md`
**Date:** 2026-08-13
**Status:** PROPOSAL ONLY. `IMPLEMENTATION_phaseC_ml_imputer.md` is a frozen progress-log record and was
**not edited** by this task. The block under "Proposed correction text" below is written for the
director to place adjacent to the frozen entry, at the director's discretion.

## Re-verification of the five claims, each with command and raw output

1. **`_draw_tier` never committed to `imputation.py`.**
   `grep -n "_draw_tier" openubem/semantic/imputation.py` → **no output** (absent at HEAD/working tree).
   `git log --all -S"_draw_tier" -- openubem/semantic/imputation.py` → **no output** (never introduced
   or removed in any commit reachable from any ref — not merely absent today).

2. **`_draw_stratum_col_for` absent from all of `openubem/`.**
   `grep -rn "_draw_stratum_col_for" openubem/` → the only hits are inside
   `openubem/outputs/comparisons/open36_completion_record_sweep.csv` and
   `open36_governance_resweep.csv` (prior audit CSVs recording the absence, not the symbol itself).
   No `.py` file under `openubem/` contains it.
   `git log --all -S"_draw_stratum_col_for" -- openubem/semantic/imputation.py` → **no output** (never
   committed to that file in any commit reachable from any ref).

3. **`_CANONICAL_TIER_ORDER` has no `"draw"` entry.**
   `grep -n "_CANONICAL_TIER_ORDER" openubem/semantic/imputation.py` →
   `543:_CANONICAL_TIER_ORDER: tuple[str, ...] = ("fusion", "spatial", "ml", "statistical")`. Confirmed:
   four entries, no `"draw"`.

4. **`config.IMPUTE_DRAW_METHOD_BY_TARGET` absent.**
   `grep -n "IMPUTE_DRAW_METHOD_BY_TARGET" openubem/config.py` → **no output.**

5. **Working tree clean on `imputation.py` and `config.py`.**
   `git status --short openubem/semantic/imputation.py openubem/config.py` → **no output** (clean;
   T02's diff, in flight in this same plan, touches only files under `tests/`, confirmed by the same
   command).

All five claims **re-confirmed true**, independently, from git and the working tree, on 2026-08-13.

## The half that DID land

`tests/test_draw_methods.py` is committed (`git ls-files tests/test_draw_methods.py` → present) and
contains **exactly 53 `def test_` functions**, matching the frozen entry's own claimed count
(`53 passed, 0 failed`, line 882):
- Counted in the HEAD-committed blob (`git show HEAD:tests/test_draw_methods.py`, via
  `grep -c "^\s*def test_"`) → **53**.
- Counted in the current working-tree file (which carries T02's in-flight `skipif` guard additions from
  this same plan, decorators only, no new/removed test functions) → **53**.
Both counts match the entry's claim exactly. No finding here.

## Mechanism, restated plainly

The frozen T07 entry (`IMPLEMENTATION_phaseC_ml_imputer.md:849`) describes wiring `_draw_tier` and
`_draw_stratum_col_for` into `openubem/semantic/imputation.py`, and extending `_CANONICAL_TIER_ORDER` to
include `"draw"`. **The test file for that work was committed. The implementation file was not.** This is
not a step nobody did — `tests/test_draw_methods.py`'s `TestDrawTierRouting` (7 tests) and the updated
`TestDefaultByteIdentity` assertions the entry describes are real, committed, and passing under their own
skip guard added by T02 of this plan (`_HAS_DRAW_TIER = hasattr(imp, "_draw_tier") and
hasattr(imp, "_draw_stratum_col_for")`) — it is a step recorded as taken in `imputation.py` that never
happened there.

## Proposed correction text (for the director to place adjacent to the T07 entry)

> **⚠️ CORRECTION — added 2026-08-13, re-verified against HEAD, OPEN-36.**
> This entry's claimed artifacts in `openubem/semantic/imputation.py` — `_draw_tier`,
> `_draw_stratum_col_for`, and the extension of `_CANONICAL_TIER_ORDER` to
> `("fusion","spatial","ml","draw","statistical")` — **were never committed to that file, in any commit,
> on any ref** (`git log --all -S"_draw_tier" -- openubem/semantic/imputation.py` and the same for
> `_draw_stratum_col_for` both return empty). `_CANONICAL_TIER_ORDER` at HEAD reads
> `("fusion", "spatial", "ml", "statistical")` — no `"draw"` entry — and `config.py` has no
> `IMPUTE_DRAW_METHOD_BY_TARGET`.
>
> What **did** land and remains true: `tests/test_draw_methods.py` was committed and holds 53 test
> functions as claimed, including the `TestDrawTierRouting` suite this entry describes. The tests were
> written against code that was designed but not shipped. Until `imputation.py` is actually wired (a
> decision reserved to the user, OPEN-17), those tests either fail or must run under an explicit
> `_HAS_DRAW_TIER` skip guard (added under OPEN-44, 2026-08-13) — they are not evidence the wiring
> exists.
>
> Verified 2026-08-13 via `git log --all -S<symbol> -- openubem/semantic/imputation.py` (empty for both
> symbols), a direct read of `_CANONICAL_TIER_ORDER` and `config.py` at HEAD, and a re-count of
> `tests/test_draw_methods.py`'s test functions (53, HEAD and working tree). See
> `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-36_t07-record-correction.md` for the full command/output
> trail.

## What I could not determine

- Whether the director wants this correction inlined into the frozen `IMPLEMENTATION_phaseC_ml_imputer.md`
  entry, appended as a dated note after it, or kept only in this standalone file and cross-referenced from
  the register — that placement decision is explicitly the director's, not mine, per the plan.
- Whether the same correction should also be applied to the two related governance-gap entries found by
  the prior OPEN-36 resweep (`IMPLEMENTATION_phaseC_ml_imputer.md:946` for T09b, and the T11.8/T11.8b
  entries in `docs_Done/PLAN_phaseC_ml_imputer.md`) — those are out of scope for T04 as written (T04 names
  only the T07 entry at line 849) and I did not re-verify them here.
