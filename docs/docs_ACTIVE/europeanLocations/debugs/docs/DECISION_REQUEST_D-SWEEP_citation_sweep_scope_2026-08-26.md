# Decision request: D-SWEEP — keep or revert the out-of-scope citation sweep

**Status:** PENDING — awaiting owner ruling
**Opened:** 2026-08-26
**Raised by:** director (self-reported scope overrun)

## Ruling

*(to be filled by the owner)*

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
