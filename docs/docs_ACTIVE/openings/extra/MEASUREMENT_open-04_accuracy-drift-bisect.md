# MEASUREMENT — OPEN-04: bisect the classifier accuracy drift

> Executes M04 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_published-numbers.md` §6.
> Measurement only. No remediation performed. The fixture, the tests, and the classifier were
> not edited by this task — every commit tested was read via a disposable `git worktree` that
> left the main working tree untouched (verified `git status` clean at HEAD before and after,
> see "Working-tree integrity" below).

---

## One-sentence verdict

**The drifted metric is `test_fine_top1`, not `test_coarse_top1`; the drift is fully explained by
two commits that landed the ratified E-R3-3 office/hotel/school tier-boundary change
(2026-07-01 and 2026-07-03), and the Phase-D fusion/crosswalk hypothesis (2026-07-13) is
FALSIFIED — the metric was already stable at 88.0% eighteen days before that work landed.**

---

## Step 1 — Resolving §5.8's discrepancy (gate first, bisect second)

`TestLabelledTop1Accuracy` run at HEAD (`bca92d0`), unmodified:

```
tests/test_building_classifier.py::TestLabelledTop1Accuracy::test_coarse_top1 PASSED
tests/test_building_classifier.py::TestLabelledTop1Accuracy::test_fine_top1 PASSED
tests/test_building_classifier.py::TestLabelledTop1Accuracy::test_archetype_coverage_min10 PASSED
```

Recomputed directly from `_run_labelled_fixture()` (same helper the tests call; no logic
re-implemented) to get exact values rather than pass/fail:

| Metric | HEAD value | Gate |
|---|---|---|
| `test_coarse_top1` | **100.0%** (50/50) | ≥90% |
| `test_fine_top1` | **88.0%** (44/50) | ≥70% |
| `test_archetype_coverage_min10` | **13 distinct** archetypes | ≥10 |

**88.0% matches `test_fine_top1` exactly, and only `test_fine_top1`.** `test_coarse_top1` is and
has always been 100% across every commit tested (see §2 table). This resolves the register's
apparent contradiction cleanly: the 88.0% recorded in the register is the *fine* accuracy compared
against the *fine* gate (70%), which it clears with room to spare — it was never being compared
against the 90% coarse gate, and the register's text never claimed it was; the ambiguity was only
in *which* of the three numbers "88.0%" referred to, and it referred to `test_fine_top1`.

**Primary-source confirmation, with `path:line`, of what "92.0% → 88.0%" means:**

- `docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md:131` — A03 progress log,
  completed 2026-06-11: *"Test status: see A05 (all 3 gate tests pass: coarse=100%, fine=92%, 14
  distinct archetypes)"*.
- `docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md:148` — CP-α ratification, same
  date: *"Fixture accuracy 92% fine / 100% coarse (gate floors 70/90)"*. This is the **R3-era
  reference** the plan's task text names.
- `docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md:84` — T05 task
  text, written before execution: *"current baseline (92.0% fine / 100.0% coarse, per
  `PLAN_step-2-classifier-coverage-R3.md` §8 A02 note)"*.
- `docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md:140` — T05
  progress log, completed 2026-07-21: *"→ 3 passed (coarse 100%, fine 88.0%, coverage ≥10 distinct
  archetypes)"*.

All four citations pair "92.0%"/"88.0%" with the word "fine" explicitly, never "coarse." The
92.0%→88.0% pair is `test_fine_top1`, confirmed independently of the live-run numbers above. The
gate does **not** refer to a third, undocumented metric — bisecting `test_fine_top1` is the
correct target. Proceeding to bisect.

**One footnote, reported per plan rule 8 (never silently drop a discrepancy):** the CP-α doc
(line 131/148) states **14** distinct archetypes; the live re-run at that same commit (§2 below)
measures **13**. This does not affect the fine/coarse numbers (both reproduce exactly) and
`test_archetype_coverage_min10` passes either way (13 ≥ 10 and 14 ≥ 10), so it does not change the
bisect target or its outcome. Left unresolved as an aside, not chased further — out of M04's scope.

---

## Step 2 — Bisect: accuracy at each commit tested

Range: R3-era reference (`7635ce2`, 2026-06-12, CP-α) → HEAD (`bca92d0`, 2026-08-05).

**Only two commits in the entire range touch a file that could plausibly move `test_fine_top1`**
(`tests/test_building_classifier.py`, `tests/fixtures/labelled_archetypes_50.csv`,
`tests/fixtures/boston_downtown_500m.gpkg`, `tests/fixtures/chicago_loop_500m.gpkg`,
`openubem/semantic/building_classifier.py`) — confirmed by:

```
git log --pretty="%h %ad %s" --date=short 7635ce2..bca92d0 -- tests/test_building_classifier.py \
  tests/fixtures/labelled_archetypes_50.csv tests/fixtures/boston_downtown_500m.gpkg \
  tests/fixtures/chicago_loop_500m.gpkg openubem/semantic/building_classifier.py
```
→ `0df422e` (2026-07-03) and `67ede73` (2026-07-01), in that chronological order. Every other
commit in the 22-commit range (including the squashed commit containing the suspected Phase-D
fusion/crosswalk work) is file-path-disjoint from anything the fixture-vs-classifier comparison
can read, so it cannot move the number — confirmed by direct execution at four checkpoints, not
assumed from the file-touch list alone.

Method: read-only `git worktree add --detach <short-path> <commit>` per commit (main tree was
never checked out), `_run_labelled_fixture()` executed with `./.venv/Scripts/python.exe`, worktree
removed immediately after each measurement.

| # | Commit | Date | Subject | coarse | fine | coverage | Δ fine vs. prior |
|---|---|---|---|---|---|---|---|
| 1 | `7635ce2` | 2026-06-12 | cluster offloading, validation pipeline, resume manager, CBECS integration (**R3-era reference / CP-α**) | 100.0% | **92.0%** | 13 | — |
| 2 | `67ede73` | 2026-07-01 | input provenance and spatial imputation semantic steps, reorganize resolution docs | 100.0% | **84.0%** | 13 | **−8.0 pts** |
| 3 | `0df422e` | 2026-07-03 | machine learning imputer, **classification thresholds updates**, 3D viz enhancements | 100.0% | **88.0%** | 13 | **+4.0 pts** |
| 4 | `ef19141` | 2026-07-21 | elevators, debias, **fusion**, layout generator updates (contains Phase-D fusion/crosswalk work dated 2026-07-13 per its own added doc, `docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseD_fusion.md`) | 100.0% | **88.0%** | 13 | 0.0 pts |
| 5 | `bca92d0` | 2026-08-05 | HEAD (docs restructure) | 100.0% | **88.0%** | 13 | 0.0 pts |

Full machine-readable table: `openubem/outputs/comparisons/open04_accuracy_by_commit.csv`.

**First commit at which the value changed: `67ede73a0555f7de977203b8fa673ba15d6a4d45`, dated
2026-07-01, subject "feat: implement input provenance and spatial imputation semantic steps,
reorganize resolution docs."** `fine_top1` moved from 92.0% to 84.0% at this commit — a drop, not
the recorded rise toward 88.0%. A **second** commit, `0df422e5c279b840d6dccb066935a0861cc695aa`
(2026-07-03, "classification thresholds updates"), partially recovered it to 88.0%, where it has
sat unchanged for every commit measured since, including HEAD.

### What actually changed at `67ede73` — this is not an unexplained drift, it is E-R3-3 landing

Two things changed together in this one commit, and both trace to the same ratified decision:

1. **The ground truth moved.** `git diff 7635ce2 67ede73 -- tests/fixtures/labelled_archetypes_50.csv`
   shows 14 rows relabelled. The file's own header changed from
   `ratified=2026-06-11` to `ratified=2026-06-11, re-ratified=2026-06-30 (E-R3-3: 13 office labels
   updated from old 500/4000 to LBNL-CBES 2322/9290 m2 bins; manager-decided claude-opus-4-8)`.
2. **The classifier logic moved to match.** `git diff 7635ce2 67ede73 --
   openubem/semantic/building_classifier.py` (85 insertions / 22 deletions) adds
   `_OFFICE_SMALL_MAX_M2 = 2322.0`, `_OFFICE_MEDIUM_MAX_M2 = 9290.0`, a new `_office_size_tier()`
   helper, and rewrites the hotel-tier (`_HOTEL_LARGE_MIN_LEVELS`) and school-tier
   (`_SECONDARY_SCHOOL_MIN_LEVELS`) rules — every one of them commented `# E-R3-3`.

So the fixture and the classifier were updated **together**, in the same commit, for the same
ratified spec change (E-R3-3, decided 2026-06-30 per the fixture header). The net effect on the
50-row fixture was still a net loss of 4 correct rows (92%→84%), meaning the classifier's E-R3-3
implementation does not perfectly reproduce the hand-computed relabels — some boundary case (e.g.
the school-tier rule switched from an area threshold to a levels threshold, which is not a 1:1
translation of "≥5000 m²") disagrees with 1-2 of the newly re-ratified rows net of whatever it
newly gets right. `0df422e`'s 2-line "classification thresholds updates" three days later closes
part of that gap (84%→88%) but not all of it back to 92%.

**This is not the kind of drift the register's language ("drifts without anyone noticing") frames
it as.** It is a deliberate, ratified, and documented spec amendment (E-R3-3) whose net effect on
the labelled-fixture score was negative and was never re-measured against the fixture's *previous*
92% baseline at the time — the T05 re-measurement in
`PLAN_input-framework-classification-fixes.md` (2026-07-21) treated 92.0%/100.0% as "the current
baseline" (line 84) without noting that E-R3-3 had already moved it three weeks earlier, and simply
reported the (by-then-already-88.0%) live number without flagging the change. The "unnoticed" part
of the drift is real — nobody flagged the 92%→84%→88% move at the time it happened — but its
*cause* is a known, ratified, on-the-record decision, not a mystery regression.

---

## Step 3 — Phase-D fusion/crosswalk hypothesis: FALSIFIED

The register's suspected cause is *"the already-in-tree Phase-D fusion/crosswalk work of
2026-07-13."* That work is contained in commit `ef19141` (2026-07-21), which is the commit that
adds `openubem/semantic/fusion.py`, `tests/test_fusion.py`, and
`docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseD_fusion.md` (dated 2026-07-13 internally).

Measured directly (row 4 of the table above): `fine_top1` at `ef19141` is **88.0%**, identical to
the commit immediately before it (`0df422e`, 2026-07-03) and identical to HEAD (2026-08-05).
**Zero movement.** `git diff 0df422e ef19141 -- tests/test_building_classifier.py
tests/fixtures/labelled_archetypes_50.csv tests/fixtures/boston_downtown_500m.gpkg
tests/fixtures/chicago_loop_500m.gpkg openubem/semantic/building_classifier.py` is empty — none of
the five files the metric can possibly depend on were touched by the fusion/crosswalk commit at
all.

**The drift was complete 18 days before the Phase-D fusion/crosswalk work landed.** The hypothesis
is falsified. The register's own text ("Proven unrelated to that arc's own changes by a live
before/after reproduction" — `INVESTIGATION_open-items-register.md:188`) was already correct about
the *input-framework-classification-fixes* arc being uninvolved; this measurement extends that same
conclusion to the Phase-D fusion/crosswalk work specifically, which the register had left open.

---

## Step 4 — Validation: does the reproduction match the recorded drift?

| | coarse | fine |
|---|---|---|
| R3-era reference (`7635ce2`) | 100.0% | 92.0% |
| HEAD (`bca92d0`) | 100.0% | 88.0% |
| Difference | 0.0 pts | **−4.0 pts** |

This exactly reproduces the register's recorded "92.0% → 88.0%" drift, on the `fine` metric only,
with `coarse` unchanged at 100% throughout — consistent with Step 1's identification. **The
reproduction succeeds.**

---

## Working-tree integrity

All five measurements above were taken from disposable `git worktree add --detach` checkouts at
short paths (`/c/wt04`, `/c/wt04b`, `/c/wt04c`, `/c/wt04d`), each removed with
`git worktree remove --force` immediately after its measurement. **The main working tree
(`C:\Users\o_iseri\Desktop\OpenUBEM`) was never checked out to any commit other than HEAD at any
point in this task.**

`git status --short` on the main tree, before and after this task, both show the same 11 pre-existing
entries (one deletion, ten untracked paths from the other in-flight M01/M02/M03/M05 tasks) — none
added, none removed, none modified by this task. `git rev-parse HEAD` on the main tree is
`bca92d0a6cdc33923bea8424f1b86ab0f94d82d9` before and after. No file under `tests/`, no fixture, and
no classifier source was edited by this task.

---

## Files this measurement is derived from

- `tests/test_building_classifier.py:1034-1057` (`TestLabelledTop1Accuracy`, `_run_labelled_fixture`)
  — run unmodified at HEAD and at each bisected commit.
- `docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md:131,148` — R3-era reference
  numbers (92% fine / 100% coarse), independently reproduced by live run at `7635ce2`.
- `docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md:84,140` —
  confirms the 92.0%/88.0% pair is the fine metric.
- `openubem/semantic/building_classifier.py`, `tests/fixtures/labelled_archetypes_50.csv` (read-only,
  historical `git show`/`git diff` only — never edited on the main tree) — source of the E-R3-3
  causal trace.
- `docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseD_fusion.md` (read via `git show ef19141:...`)
  — confirms the Phase-D fusion/crosswalk work's own internal date (2026-07-13) and its landing
  commit (`ef19141`).
- `openubem/outputs/comparisons/open04_accuracy_by_commit.csv` — the full per-commit table.
