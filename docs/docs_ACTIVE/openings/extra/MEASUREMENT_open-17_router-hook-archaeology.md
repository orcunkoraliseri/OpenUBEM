# MEASUREMENT — OPEN-17: the router hook's "never existed in any commit" claim, verified with a positive control

**Task:** T12 of `../implemenation/PLAN_twenty-items-2026-08-19.md`. Read-only git archaeology only
— `log`/`grep`/`show`/`rev-list`, no write commands. No new script; every command reproduced
verbatim.

## 1. The claim

Register OPEN-17: the six variance-preserving draw-tier imputers are not "off" — the tier is
unreachable and **"its router hook has never existed in any commit."** N10 supported this with one
command (`git log --all -S"_draw_tier" -- openubem/semantic/imputation.py` → empty). This task
independently re-runs and widens that search, and — per the task's own "how to test" clause —
proves the method itself would have found the hook had it existed, using a symbol known to exist.

## 2. Independent re-run, widened

```
git log --all -S"_draw_tier" --oneline -- openubem/semantic/imputation.py    -> (empty, exit 0)
git log --all -S"IMPUTE_DRAW_METHOD_BY_TARGET" --oneline -- openubem/config.py -> (empty, exit 0)
```

Both reproduce N10's finding exactly: **neither the hook name nor its config surface has ever been
added to, or removed from, the file that would have to define them, in any commit reachable from
any ref.**

**Widened to the whole repository** (not just `imputation.py`), since a hook could in principle
live somewhere else:

```
git log --all -S"_draw_tier" --oneline
```

returns **8 commits** — but every one of them, checked individually (`git show --stat <hash>`),
touches only `tests/test_draw_methods.py` / `tests/test_semantic_unknown_draw.py` (tests that
*reference* the hoped-for hook, e.g. `imp._draw_tier` in an `hasattr` guard), documentation/register
commits (`9270ac7`, `bca92d0`), or `ef19141` — the commit that added the six imputers themselves
(`openubem/semantic/draw_methods.py`, `openubem/results/draw_leaderboard.py`) but **not**
`imputation.py`. A fresh `git grep -n "_draw_tier" -- '*.py' | grep -v '^tests/'` at HEAD confirms
the same: the only non-test hits are two `scripts/analysis/*.py` files (`open36_governance_resweep.py:68`,
`open44_test_triage.py:62,72`) — this pass's and prior passes' own investigation scripts describing
the absence, and `draw_methods.py:6`'s own docstring saying a *future* task "wires `_draw_tier` into
`openubem/semantic/imputation.py`." **The string exists in the repository's history and at HEAD; the
router hook itself, as code inside `imputation.py`, does not, anywhere.**

## 3. Positive control (the task's own required test)

To prove the search method would have caught the hook had it existed, the identical command was
run for `_ml_tier` — a symbol independently confirmed to exist at HEAD (`imputation.py:685`, T11
this pass) and known to have been added at some point in history, not always present:

```
git log --all -S"_ml_tier" --oneline -- openubem/semantic/imputation.py
```

returns **2 commits**: `0df422e` (2026-07-03, *"feat: implement machine learning imputer..."*) and
`03e2121` (2026-07-02). **The method finds a real symbol's introduction when one exists.** The
empty result for `_draw_tier` on the identical command, against the identical file, is therefore
evidence of absence, not a blind spot in the search — satisfying the task's stated test.

## 4. Earliest/latest commits touching the imputers themselves

```
git log --follow --format="%h %ad %s" --date=short --reverse -- openubem/semantic/imputation.py
```
`fe05509` (2026-06-10) → `03e2121` (2026-07-02) → `0df422e` (2026-07-03) → `3a925f9` (2026-07-25,
latest).

```
git log --follow --oneline -- openubem/semantic/draw_methods.py
```
**One commit only**: `ef19141` (2026-07-21) — the six draw imputers were added complete in a
single commit and have not been touched since (earliest = latest = the same commit).

**The opportunity existed and was not taken.** `imputation.py` was modified again at `3a925f9`
(2026-07-25) — four days *after* the six imputers landed (`ef19141`, 2026-07-21) — and even that
later touch to the file that would host the hook did not add one. This rules out "the imputers
just haven't been touched by a wiring commit yet, chronologically" as an innocent explanation for
recency; there was a commit to the right file after the imputers existed, and it still did not
wire them in.

## 5. Verdict

**The claim reproduces exactly, and the method is now proven non-blind by a positive control**: the
router hook (`_draw_tier` inside `openubem/semantic/imputation.py`) and its config surface
(`IMPUTE_DRAW_METHOD_BY_TARGET` inside `openubem/config.py`) have never existed in any commit on any
branch, while the same search technique correctly locates `_ml_tier`'s real introduction two commits
before it first appears. **OPEN-17's framing does not need reframing** — if anything this
strengthens it: the absence is not a stale artifact of one early search, it holds across the widened
repository-wide search, across all refs, and survives a chronological window where the hook could
easily have been added and was not.
