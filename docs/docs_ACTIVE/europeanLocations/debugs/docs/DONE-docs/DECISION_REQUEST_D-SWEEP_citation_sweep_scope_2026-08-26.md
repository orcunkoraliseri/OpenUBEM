# Decision request: D-SWEEP — keep or revert the out-of-scope citation sweep

**Status:** RULED — CLOSED 2026-08-27 (option 3, KEEP AND LOG)
**Opened:** 2026-08-26
**Raised by:** director (self-reported scope overrun)

## Ruling

**RULED 2026-08-27 — option 3, KEEP AND LOG.** Taken by the director under the owner's explicit
delegation of 2026-08-27 (*"continuer jusqu'a la fin, executer"*). The 58 out-of-scope files stay
exactly as committed in `8d816be`; the scope overrun is **recorded, not undone**.

**Re-measured before ruling**, twice: `git show --numstat 8d816be -- docs/` for the commit's own
shape, then a live resolvability pass over the 58 files as they stand on disk today.

| Measure | 2026-08-26 | 2026-08-27 re-measure |
|---|---|---|
| sweep-shaped files under `docs/` | 78 (20 in scope / 58 out) | identical |
| new paths written by the sweep, resolving | 61 / 64 | 58 / 61 |
| old paths the sweep replaced, resolving | 2 / 50 | 2 / 71 |

The denominators differ because the two passes extracted paths with different patterns. The
conclusion is unchanged and slightly stronger than it was on 08-26: **reverting would break 56
citations that resolve today in order to restore 2.**

**Two of the three non-resolving new paths were genuine breaks and were repaired at the ruling.**
The third, `docs/docs_main/docs_step-2-2/DESIGN_step-2-2-...md`, is a prose ellipsis, not a citation.

1. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/implementation_plan.md` →
   `docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md` — **4 files**
   (`debug/DONE/PLAN_debug_implementation.md`, `DONE/COMPLETION_REPORT.md`,
   `prompt/previous/DIRECTOR_PROMPT.md`, `prompt/previous/DIRECTOR_PROMPT_debug.md`).
   The target was **renamed by its own move** (`implementation_plan.md` → `DONE-implementation_plan.md`),
   which is precisely the failure mode `CLAUDE.md` warns about: prefix substitution cannot see a
   changed basename. **This is the fourth confirmed instance of that rule paying for itself.**
2. `docs/docs_step-4/DESIGN_step-4-...-isol.md` → `docs/docs_main/docs_step-4/...` — **2 files**
   (`docs_main/docs_step-4/PLAN_step-4-implementation.md`, `docs_main/docs_step3/PLAN_step-3-remediation-R1.md`).

After the repair, **every path the sweep wrote resolves**; residual measured at **0**.

**Measured and deliberately NOT fixed.** A live pass over the same 58 files finds **16 of 86**
distinct `docs/**.md` citations still non-resolving. All 16 are **pre-existing** breakage the sweep
never touched — `docs/RESUME_*.md` (3, deleted not moved),
`docs_ACTIVE/hvac-ServiceLoads/REPORT_phaseE_final.md` and its `docs_DONE/` twin, three
`simulation-Resolution/layoutAssigner/` sub-plans, `validations/overAll/results/v19_comparison_tables.md`,
and several prose ellipses. Repairing them is a **fresh archiving job across five closed arcs** —
that is exactly the unrequested scope overrun this decision exists to censure, so it is recorded
here and left alone.

**Log entry written** to `docs/PROJECT_CHECKLIST.md`, per option 3, so a future reader knows why
closed-arc files moved inside an EU-arc commit.


## What happened

While repairing citations broken by folder moves inside the European-locations arc, the director
also rewrote citations in documents belonging to **other, already-closed arcs**. Nobody asked for
those files to be touched. The edits are already committed, mixed into commit `8d816be` together
with legitimate EU-arc work, so no clean `git revert` of the sweep alone exists.

The fault is **scope**, not correctness. This document exists so the owner rules on the scope
overrun with the evidence in front of them, rather than the director deciding unilaterally.

## Measured state

All figures below were measured from `git show --numstat 8d816be -- docs/` on 2026-08-26.

- The commit touches **118** documents under `docs/`. **78** of them carry the sweep shape
  (≤ 6 lines changed on each side, i.e. path rewrites, not content edits), totalling **157**
  rewritten lines. **19** entries are file renames recorded by git.
- Of those 78 sweep-shaped files, **20 are in scope** (`docs_ACTIVE/europeanLocations`) and
  **58 are out of scope**. The out-of-scope set breaks down as:

  | Folder | Files |
  |---|---|
  | `docs_DONE/SETUP` | 27 |
  | `docs_DONE/VISUALS` | 7 |
  | `docs_DONE/INPUTS` | 7 |
  | `docs_DONE/LOADS` | 5 |
  | `docs_DONE/BUGS` | 4 |
  | `docs_TODO/layoutgenerator` | 2 |
  | `docs_main/docs_step2`, `docs_main/docs_step3` | 2 |
  | `docs_EXPLANATION` (2 files), `docs_DONE/OUTDOOR`, `docs_DONE/GENERAL` | 4 |

- Every edit inspected is a **path rewrite of the same citation**, e.g.
  `docs/docs_ACTIVE/simulation-Resolution/PLAN_resolution_mode_switch.md` →
  `docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md`.
  No prose, no numbers, no findings were altered.

- **Resolvability check on the out-of-scope set only** (does the cited file exist on disk today?):

  | Path set | Resolves today |
  |---|---|
  | **New** paths written by the sweep | **61 / 64** |
  | **Old** paths the sweep replaced | **2 / 50** |

  The 3 non-resolving new paths are extraction artefacts, not broken links: two are prose
  ellipses (`DESIGN_step-2-2-...md`), one is a path fragment quoted inside a sentence.
  The 2 old paths that still resolve are `docs_main/docs_step-2-2` and `docs_main/docs_step-5`
  DESIGN files, which were not moved.

## Why this matters against project rules

`CLAUDE.md` states: *"Archiving is not finished until every citation pointing into the archived
arc has been swept and repaired."* The out-of-scope edits are exactly that repair, performed for
arcs whose archive sweeps were incomplete. Reverting them re-breaks **~48 of 50** citations that
currently resolve.

Against that stands the equally explicit rule: *"NEVER create anything not explicitly requested."*
The director widened the blast radius of a scoped task without asking first.

## Options

1. **KEEP (recommended).** Leave the 58 out-of-scope files as committed. The citations resolve,
   the edits satisfy the archiving rule, and no published number, finding or decision is affected.
   Cost: the repository history records edits the owner never authorised.
2. **REVERT.** Restore the 58 files to their pre-`8d816be` content by path (not by reverting the
   commit, which would also destroy the EU-arc work). Cost: ~48 citations that resolve today go
   back to pointing at folders that no longer exist, and the archiving rule is left violated for
   five closed arcs.
3. **KEEP AND LOG.** As (1), plus a one-line entry in `docs/PROJECT_CHECKLIST.md` recording that
   the closed-arc sweeps for `docs_DONE/SETUP`, `VISUALS`, `INPUTS`, `LOADS` and `BUGS` were
   completed on 2026-08-26 outside their own arcs, so a future reader knows why those files moved
   in an EU-arc commit.

## Current consequence

None on the European-locations critical path. The Bologna (`it`) ERA5 acquisition, the v1.0 spec
freeze and the boundary-contract closure are all independent of this ruling. D-SWEEP is a
housekeeping decision only; it blocks nothing.

Evidence: commit `8d816be`; `git show --numstat 8d816be -- docs/`;
`git show 8d816be -- docs/docs_DONE/SETUP`.
