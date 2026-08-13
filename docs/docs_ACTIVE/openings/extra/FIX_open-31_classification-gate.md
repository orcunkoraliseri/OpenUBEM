**Task:** T09, `PLAN_rulings-and-five-items-2026-08-12.md`. **Item:** OPEN-31. **Status:** done.

## 1. What changed

The CP-M3 before/after gate — ruled obligatory 2026-08-09 ("yes to all three — make them
obligatory") and never previously written down — is now written in the two places the plan names:
`openubem/semantic/building_classifier.py` (module docstring, the file itself, where someone editing
rules will see it) and the head section of `docs/PROJECT_CHECKLIST.md` (beside the archiving rule
T07/OPEN-33 added, in the same append-to-head-section pattern). Both blocks state the rule, what it
would have caught (E-R3-3's 4-point / 13.4% drift, unmeasured at adoption time), and the two
boundaries the ruling does not cross.

`CLAUDE.md` was **not** touched — that file belongs to the director (T02/OPEN-33 pattern).

## 2. Files changed — exactly two

`git diff --stat` scoped to this task's two files:

```
 docs/PROJECT_CHECKLIST.md                | 15 ++++++++++++++-
 openubem/semantic/building_classifier.py | 14 ++++++++++++++
 2 files changed, 28 insertions(+), 1 deletion(-)
```

Note: `docs/PROJECT_CHECKLIST.md` also carries an unrelated hunk from this session's own T01
(restating the struck fleet figure at the "Adopted simulation baseline" line, also in the head
section, not a journal block) — that hunk is T01's, not T09's, and does not add a third file to this
count. `git diff --stat` for the whole working tree will show more files touched by T01's separate
work in `docs/docs_ACTIVE/openings/extra/` and `implemenation/`; none of those are part of T09.

## 3. `git diff docs/PROJECT_CHECKLIST.md` — head section only, no journal touched

The new block is inserted directly after the existing archiving-rule paragraph and before the `---`
that opens the dated journal (`> **Last updated:** 2026-07-26 …`). No `>`-prefixed journal line was
added, removed, or edited by this task.

```diff
+**🔴 Classification before/after gate — ruled obligatory 2026-08-09 (CP-M3), written here
+2026-08-12 (OPEN-31).** No change to `openubem/semantic/building_classifier.py` that can move
+classification is adopted until the labelled fixture has been run on **both** sides of the change
+and **both** accuracy numbers are recorded. A single "after" number does not satisfy the gate. What
+it would have caught: E-R3-3 cost **4 points** of fine top-1 and reclassified **13.4%** of the shared
+fleet, and **neither number existed at adoption time** — attributing the drift later took a
+five-commit bisection, six weeks late. **What this ruling does not do:** it does not re-open any
+already-adopted change retroactively (re-running M01–M05 is forbidden), and it does not certify the
+fixture itself — OPEN-22 is rebuilding the labelled exam, and if the fixture changes, this gate
+follows it. Also written at the head of `openubem/semantic/building_classifier.py`.
+
 ---
```

## 4. `building_classifier.py` — added docstring block

Inserted into the module docstring at the top of the file, after the existing DESIGN-pointer lines
and before the code:

```python
CP-M3 GATE (obligatory, ruled 2026-08-09, written 2026-08-12, OPEN-31):
No change to this file that can move classification is adopted until the labelled fixture
(tests/fixtures/labelled_archetypes_50.csv, or its successor if OPEN-22 replaces it) has been run
on both sides of the change and both accuracy numbers are recorded. A single "after" number does
not satisfy this gate.

What it would have caught: E-R3-3 cost 4 points of fine top-1 and reclassified 13.4% of the shared
fleet, and neither number existed at the time E-R3-3 was adopted. Attributing that drift after the
fact took a five-commit bisection, six weeks late.

Boundaries this gate does not cross: it does not re-open any already-adopted change retroactively
(re-running M01-M05 is forbidden); and it does not certify the fixture itself — OPEN-22 is rebuilding
the labelled exam, and if the fixture changes, this gate follows it.
```

Verified the file still parses (`ast.parse`) after the edit.

## 5. Notes

- The `tests/fixtures/labelled_archetypes_50.csv` pointer in the classifier docstring is written to
  say "or its successor if OPEN-22 replaces it," so the gate does not need a second edit the day
  OPEN-22's rebuilt fixture is adopted — consistent with boundary 2 (the gate does not certify any
  specific fixture).
- Did not edit `CLAUDE.md`, the register, or the director prompt, per hard rules.
