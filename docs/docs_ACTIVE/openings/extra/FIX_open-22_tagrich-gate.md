# FIX — OPEN-22: wire the tag-rich accuracy gate (ruling 2a)

**Task:** T01–T02, `PLAN_open22-tagrich-gate-2026-08-13.md`
**Date:** 2026-08-13
**File touched:** `tests/test_building_classifier.py` (additive only — `git diff --numstat`: `29 insertions, 2
deletions`, the 2 deletions being the single relocated line of `_run_labelled_fixture()`'s old
hard-coded path).

## 1. New gate — measured accuracy and graded row count

Command: `./.venv/Scripts/python.exe scripts/analysis/open22_grade_tagrich_fixture.py`

```
=== New fixture: labelled_archetypes_tagrich_v2.csv ===
rows total: 100  UNDETERMINED (excluded): 2  graded: 98
accuracy overall (graded rows): 87/98 = 88.8%
FALLBACK_SIZE_DEFAULT rows: 3/98 = 3.1%  (old fixture: 17/50 = 34.0%)
accuracy excluding FALLBACK_SIZE_DEFAULT rows: 87/95 = 91.6%
```

`test_fine_top1_tagrich` (new, `tests/test_building_classifier.py`, `TestTagRichTop1Accuracy`) asserts
this **88.8% (87/98)** against the ruled `>= 0.80` gate on the tag-rich fixture,
`tests/fixtures/labelled_archetypes_tagrich_v2.csv`. It passes, ~9 points above the gate.

`test_tagrich_graded_denominator_98` (new, same class) asserts the graded denominator is exactly **98**.
It passes.

## 2. Coarse accuracy — ungated observation only (no coarse gate added, per plan §5.5)

Computed inline (not a new file — one-off `python -c`, using the test module's own
`_run_labelled_fixture()` driver and `_COARSE_CLASS_MAP`, on the same 98 graded rows):

```
graded rows: 98
coarse top-1: 1.0   (98/98 = 100.0%)
```

**Coarse top-1 on the tag-rich fixture is 100.0% (98/98)**, from `tests/test_building_classifier.py`'s
own `_COARSE_CLASS_MAP`. No gate was added for this number — reported only as the plan requires, for the
director to decide separately whether a coarse gate should ever be ruled.

## 3. Old gate — undisturbed

Command: `./.venv/Scripts/python.exe -m pytest tests/test_building_classifier.py -v` (run twice, before
and after the T01(d) non-vacuity check; both runs: **133 passed**).

`TestLabelledTop1Accuracy`'s three tests, all **PASSED** both times:
- `test_coarse_top1` — `>= 0.90` gate, unchanged.
- `test_fine_top1` — `>= 0.70` gate, unchanged. Quoted from `tests/test_building_classifier.py:1049`:
  `assert acc >= 0.70, f"fine top-1 {acc:.1%} < 70% gate"`
- `test_archetype_coverage_min10` — `>= 10` distinct archetypes, unchanged.

The old fixture's precondition (asserted by the grading script, §1's run) reproduced exactly:
`old fixture: 44/50 = 88.0%`.

`_run_labelled_fixture()` gained a default-valued `csv_path` parameter (default is the original literal,
byte-identical); every existing zero-argument call site is untouched, so the old three tests are
behaviourally identical to before this change.

## 4. Non-vacuity check (T01(d))

In the working copy only, the new gate's threshold was temporarily raised from `0.80` to `0.95` (above
the measured 88.8%). Command: `./.venv/Scripts/python.exe -m pytest
tests/test_building_classifier.py::TestTagRichTop1Accuracy -v`.

Result: `test_fine_top1_tagrich` **FAILED**, `test_tagrich_graded_denominator_98` still passed. Failure
message, verbatim:

```
AssertionError: tag-rich fine top-1 88.8% < 95% gate (n=98 graded rows)
```

The threshold was then restored to `0.80` in the file. The full suite was re-run
(`tests/test_building_classifier.py -v`) and confirmed **133 passed**, including both new tests, at the
restored `0.80`.

## 5. Full suite totals — red-count reconciliation against OPEN-44's 45

Command, scoped exactly as OPEN-44's own measurement (`docs/docs_ACTIVE/openings/extra/
MEASUREMENT_open-44_test-triage.md`):
`./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/ --ignore=docs --tb=short`

Result: **26 failed, 1859 passed, 10 skipped, 19 errors, 11 warnings, 1102.87s (18m22s).**

**26 + 19 = 45**, matching OPEN-44's count exactly. Passed count is **1859 vs OPEN-44's 1857 (+2)** —
exactly the two new tests added in this task; skipped is 10, unchanged.

Went one step further than the plan asked and diffed the actual failing/erroring **nodeids** (not just
the count) against `openubem/outputs/comparisons/open44_test_triage.csv`'s 45 rows: **the two sets are
identical, node-for-node** (0 nodes in one set and not the other). This is the same 45 red tests OPEN-44
classified as 31 `artifact-missing` + 14 `stale-expectation`, 0 real defects — none of them touch
`test_building_classifier.py`.

Aside, not requested by the plan but run before the scope was pinned down, so reported per the
report-every-number rule: an earlier, **unscoped whole-repo run** (`./.venv/Scripts/python.exe -m
pytest`) gave **61 failed, 1903 passed, 10 skipped, 36 errors, 1174.49s**. This does not reconcile against
45 and is not expected to — it includes the `docs/` tree nodes that OPEN-44's own baseline explicitly
scoped out. Not used for reconciliation; §5's `tests/`-only run is the one that matches.

## 6. OPEN-50 fixture dirt

Running the suite rewrote `tests/fixtures/synthetic_30_archetype_coverage.gpkg` (binary, `106496 ->
106496` bytes per `git diff --stat`) — this is the known OPEN-50 timestamp-only churn, left untouched and
uncommitted, exactly as the plan anticipates.

`git diff --stat -- tests/` shows exactly two touched paths: `tests/test_building_classifier.py` (the
planned edit) and that OPEN-50 `.gpkg` (expected collateral, not written to by this task's edits).

## 7. What I could not determine

- I did not re-verify each of the 45 red nodes' individual `artifact-missing` / `stale-expectation`
  classification from scratch — I confirmed the **set of failing/erroring nodeids is identical** to
  OPEN-44's triage CSV, which is sufficient to reconcile the count and composition, but I did not re-read
  each test/shipped-code pair myself.
- I did not determine why the unscoped whole-repo run's failed count (61) differs from the
  `docs/`-portion implied by OPEN-44's own whole-repo baseline note (which cited 70 failed at 2026-08-12,
  whole-repo, now stale) — out of scope for this task per plan §1.1, and not needed since §5's reconciled
  run uses the correct, matching scope.
- I did not investigate whether the 100.0% coarse accuracy on the tag-rich fixture is a stable property of
  the fixture's tag distribution or a small-sample artifact of 98 rows — it is reported only as the raw
  ungated number the plan asked for.

---

## 8. Director's independent audit — added 2026-08-13, after §1–§7

**§6 of the plan required the checkpoint to be audited by independent re-derivation, not by reading this
report. That was done, and — for a reason worth recording — it was done *without* the report in hand.**

While the executor's scoped full-suite run was in flight (it takes **18m22s**, and produced no output for
that whole period), the director independently re-ran the gate and re-ran
`scripts/analysis/open22_grade_tagrich_fixture.py` from scratch, computed the ungated coarse figure, and
performed the non-vacuity check by hand. **Every figure below was derived before §1–§7 existed, and they
agree.**

| Quantity | Director's re-derivation | Executor's §1–§5 | Agree |
|---|---|---|---|
| Tag-rich fine top-1 | **0.8878 → 88.8%** | 87/98 = 88.8% | ✅ to four decimals |
| Graded denominator | **98** (100 − 2 `UNDETERMINED`) | 98 | ✅ |
| Old-fixture precondition | **44/50 = 88.0%** | 44/50 = 88.0% | ✅ |
| Fallback-size share | **3/98 = 3.1%** (old: 17/50 = 34.0%) | same | ✅ |
| Coarse, ungated | **98/98 = 100.0%**, 0 unmapped | 98/98 = 100.0% | ✅ |
| `test_building_classifier.py` | **133 passed, no skips** | 133 passed | ✅ |
| Old gate line 1049 | quoted, `>= 0.70`, unchanged | same | ✅ |
| Diff scope | **+29 / −2, one source file** | same | ✅ |

**Non-vacuity was checked twice, independently, by both parties** — the director raised the threshold to
`0.95`, observed `AssertionError: tag-rich fine top-1 88.8% < 80% gate (n=98 graded rows)`, and restored
`0.80`. The executor did the same and reports the message as `< 95% gate`, because it also edited the
message string during its check. **Both restored correctly**; the on-disk file was re-verified afterwards
at `assert acc >= 0.80` (line 1071) with `133 passed`, so **the two concurrent working-copy edits did not
collide.**

⚠️ **One cosmetic defect, reported not fixed:** the failure message at line 1072 hard-codes the string
`"< 80% gate"` rather than interpolating the threshold. It is correct at today's value. **If anyone ever
changes the number, the message will lie.** Fixing it was outside ruling `2a` and this task did not widen
its own scope.

🔴 **A process correction belongs here, because the director got it wrong first.** An empty output file
and a long silence were read as an executor stall, and that reading was written into the plan log, the
director prompt and the checklist before the executor's report arrived. **It had not stalled — it was
inside the 18-minute suite run.** The claim has been retracted everywhere it was written. The lesson is
narrow and worth keeping: **on this repo a full scoped suite run is ~18 minutes of total silence, and
silence is not evidence of a stall.** What the mistake did *not* cost anything is the audit itself —
because the director re-derived rather than waited, the checkpoint was already provable on its own
evidence before the report existed. **That is the property to keep.**

**The executor's run went further than the director's on one axis, and it is the more valuable half.**
The scoped full-suite run (`pytest tests/ --ignore=docs`) gave **26 failed, 1859 passed, 10 skipped,
19 errors** → **26 + 19 = 45, reconciling exactly against OPEN-44**, and it diffed the actual failing
**nodeids** against `open44_test_triage.csv`: **the two 45-node sets are identical node-for-node.**
Passed went 1857 → **1859, exactly the two new tests.** The director's own audit was scoped to
`test_building_classifier.py` and could not have established that. **Both halves were needed.**
