# MEASUREMENT — OPEN-13: what were the 43 tests covering?

**Date:** 2026-08-20. **Task:** T05 of `implemenation/previous/PLAN_five-items-2026-08-20-late.md`.
**Scope:** enumeration and characterisation only. No production code, `tests/`, `scripts/validation/`
or `scripts/cluster/` file was touched; no analysis harness was created (T05 authorises none).

## Pre-registered controls

- **C11** — the enumerated count of tests must be 43, named. If not 43, report the real number and
  where "43" came from; do not adjust evidence to reach 43.
- **C12** — `py -3 -m pytest -q tests/` must report the known baseline (1,875 passed / 55 skipped, or
  1,937 collected under the older count).

## The containing commit

`git log --oneline --since=2026-08-10 --until=2026-08-14 -- tests/` lists three commits; the one that
matches book I's OPEN-13 narrative ("both defects addressed; one fixed, one contained", report
`extra/FIX_open-13_height-cache-and-collection.md`) is:

`a3bf4d956e3ca207d6ecf660ae4ae33c77c3cfc1` — *"docs/code: five-item openings sweep, fusion fix for
open-13, and placeholder trace analysis"* (2026-08-12).

`git show --stat a3bf4d9` shows `tests/test_draw_methods.py | 13 +` (13 insertions, 0 deletions) —
the containment was a **module-level `pytest.skip(allow_module_level=True)` inserted at the top of
the file**, not a deletion. `git diff a3bf4d9^ a3bf4d9 -- tests/test_draw_methods.py` confirms: the
only change is a 13-line `pytest.skip(...)` block added after the imports, citing OPEN-17. No `def
test_` line was removed by this commit or by any other commit in the `--since/--until` window.

## C11 — the number actually named

**43**, matching the register's number, but the count is arrived at independently here, not copied.

`test_draw_methods.py` has **53** collected tests
(`py -3 -m pytest tests/test_draw_methods.py --collect-only -q` → `53 tests collected`). After
`a3bf4d9`, the module-level skip meant **all 53** were skipped at runtime, not deleted. On
2026-08-13 the skip was narrowed to a `_HAS_DRAW_TIER` guard (`_SKIP_NO_DRAW_TIER` on 9 individual
tests plus one class-level `skipif` on `TestNoEUILeakage`), which is still in place at HEAD
(`tests/test_draw_methods.py:50-58`, `:660-667`). Live run today:

```
py -3 -m pytest -q tests/test_draw_methods.py -rs
43 passed, 10 skipped in 0.76s
```

53 − 10 = 43. The **43 named node IDs** are every test in the file except the 10 that carry a
`_HAS_DRAW_TIER`-gated skip; the full list with pass/skip status is in
`openubem/outputs/comparisons/open13_lost_tests.csv`.

Book I's provisional 2026-08-12 note ("only 13 reference the unimplemented draw-tier names") does not
match; book I itself corrects this on 2026-08-18 to **10**, which is what is reproduced live here.
The provisional "13" and "9 failed" figures were measured before the individual `skipif` guards
existed and are superseded — not re-derived here beyond noting the discrepancy.

## C12 — baseline suite

Command run exactly once: `py -3 -m pytest -q tests/`.

**Result, as printed:**

```
1918 passed, 56 skipped, 892 warnings in 1443.51s (0:24:03)
```

exit code 0. This does **not** match either figure the plan pre-registered as "the known baseline"
(1,875 passed / 55 skipped, or 1,937 collected). 1918 + 56 = 1974 collected, which also does not
match 1937. **Not adjusted to fit** — this is the real, single, unrepeated run. The suite has grown
between the plan's baseline and this run (other tasks on this same plan — T01-T04 — and other
concurrent work in this repo add tests over time; the register's own quoted baseline has moved
several times across recent entries: 1822 -> 1857 -> 1875 -> 1918). The extra +1 skip beyond the 55
counted elsewhere was not reconciled here — reconciling the whole suite's skip census file-by-file
is explicitly out of this task's scope (see book I's own note that this reconciliation needs a
dedicated full-suite pass and was deliberately deferred).

## Groups and survival of coverage

All 53 tests live in one file, `tests/test_draw_methods.py`, grouped by class:

| group (class) | exercises | passed / total | skipped, reason |
|---|---|---|---|
| `TestDefaultByteIdentity` | default-config byte-identity floor (enabled tiers, router output, registry shape, token constants unchanged when the draw tier is not configured) | 4/6 | 2 skipped — need `IMPUTE_DRAW_METHOD_BY_TARGET` / handler-registry entry that don't exist |
| `TestKDE` | KDE draw method (registration, variance/KS bounds, small/unknown-stratum abstain, explicit bounds, determinism, multi-stratum, mixed abstain/fill) | 9/9 | 0 |
| `TestPMM` | Predictive mean matching draw method (registration, donor invariants, thin-stratum borrowing, unknown-stratum fallback, abstain, determinism) | 6/6 | 0 |
| `TestHotdeck` | Hot-deck draw method (registration, donor invariants, isolated/no-neighbour abstain, determinism) | 5/5 | 0 |
| `TestResid` | Residual draw method (registration, central accuracy/KS, small-stratum abstain, explicit/default clamp, determinism) | 6/6 | 0 |
| `TestCatFreq` | Categorical-frequency draw method (registration, stratum proportions, minority recovery vs mode-fill, self-stratification guard, small-stratum fallback, abstain floor, determinism) | 7/7 | 0 |
| `TestABB` | Approximate Bayesian bootstrap draw method (registration, donor invariants under depletion, small/unknown-stratum abstain, determinism) | 5/5 | 0 |
| `TestDrawTierRouting` | router-level integration (does enabling `IMPUTE_DRAW_METHOD_BY_TARGET` actually route work, byte-identity when configured-but-unused, gdf-shaped paths) | 1/7 | 6 skipped — need `imputation._draw_tier` / `_draw_stratum_col_for`, which do not exist (router wiring is OPEN-17) |
| `TestNoEUILeakage` | static check that no draw-method function references EUI by name | 0/1 | 1 skipped (class-level `skipif`) — same missing-symbol reason |
| `TestDrawTierDeterminism` | whole-tier byte-identical reproducibility across two configured targets | 0/1 | 1 skipped — same missing-symbol reason |

**Per group, does equivalent coverage survive today?** For every one of the 43: **yes, identically —
the same node ID, in the same file, running and passing today**, confirmed by the live
`-rs` run above. Nothing was ever deleted from git history; the "trade" on 2026-08-12 was a blanket
runtime skip of the whole file, and the 2026-08-13 narrowing (already recorded in book I) restored
exactly these 43 to collecting and passing, leaving only the 10 tests that genuinely need the
unimplemented `_draw_tier` / `_draw_stratum_col_for` symbols skipped, each with a reason string
naming OPEN-13/OPEN-17/OPEN-36 (and OPEN-44 for 9 of the 10). No search for coverage "elsewhere in
the suite" was needed because the originals are still in place; a name-search
(`grep -rn "def test_registered_under_kde\|def test_registered_under_pmm" tests/`) would only
re-confirm they are defined once, in this file — not run, since the live pytest execution already
proves survival more directly.

## CANDIDATE DEFECT

None found. This task changed no production code, restored no test, and built no harness — it
enumerated and cross-checked a historical trade against the tree as it stands today. What was
**not** done: no attempt to reconcile the file's 10 current skips against the whole-suite 55-skip
figure (book I already flags this as a separate, undone reconciliation, and T05's scope is this one
file, not the whole suite's skip census); no judgement on whether OPEN-17 should be promoted (reserved
to the user).

## Artifacts

- `openubem/outputs/comparisons/open13_lost_tests.csv` — 53 rows, all node IDs, per-row pass/skip
  status at HEAD, verbatim skip reason where applicable.
- This file.
