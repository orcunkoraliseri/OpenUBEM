# Executor prompt — implement FINDING 249's restricted remedy (code changes authorized, no cluster)

Paste this whole file as your first message to the external agent (Gemini / Antigravity). It is
self-contained — you have no access to any other conversation, memory, or prior context about this
project. Follow it exactly.

## Hard rules — read before doing anything

1. **Your task list, in full, lives in one file — read it before touching anything:**
   `docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu-nocore-finding249-remedy-2026-09-04.md`.
   Execute its `T01` through `T04` in order, exactly as specified. Do not propose an alternative
   remedy shape, even if you think you have a better idea — if something in the plan looks wrong or
   ambiguous, **STOP and quote the exact conflict**, don't improvise.
2. That plan doc's §2 "Hard rules for executor" is binding and repeated here for emphasis, most
   importantly: **do not implement "identical partner coordinates = safe" as a pass condition.**
   A prior investigation (cited in the plan, §5) proved that premise false on its own cited example —
   a building with bit-identical partner coordinates still fatally crashed in EnergyPlus historically.
   Only a "no interzone partner at all" carve-out is authorized.
3. **No cluster access, no cluster submission, ever, in this task.** No `sbatch`, no `ssh` to any
   `speed-submit2`/`speed.encs.concordia.ca` host. There is no cluster credential available to you
   and none is needed — stop after the plan's `T04`.
4. `openubem/idf/surfaces.py` off-limits to edit (`D-EU-41`). `openubem/geometry/european_nocore.py`
   cutting logic frozen (`D-EU-95`). Both are read-only precedent boundaries — read/quote, never edit.
5. **No threshold moves.** Do not change `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` or
   `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (`scripts/run_eu_s2_campaign.py:77,91`) — this is a standing
   hard rule, not a suggestion.
6. You may edit exactly two files: `scripts/run_eu_s2_campaign.py` and `tests/test_eu_s2_campaign.py`.
   You may also **append** (never rewrite existing content of) the progress log section (§8) of the
   plan doc named in rule 1. No other tracked file changes. No `git add`/`commit`/`push`, no history
   rewrites.
7. Environment: Windows. Repo root `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **not** on PATH —
   use `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe` for anything you run. Locate the
   local EnergyPlus 23.1.0 install the same way it was already used earlier in this arc — the plan
   doc's §4 tells you where to look for that precedent (the root-cause sub-plan's `T02b`/`T02c`
   entries); do not assume a path, confirm the binary actually runs before relying on it.
8. **Evidence discipline:** every claim in your progress-log entries must cite a real `file:line` or
   be the verbatim output of a command you actually ran. Never state a number, a test result, or a
   simulation outcome you have not personally confirmed. If you're not sure, say "unconfirmed".
9. **Stop conditions:** stop and report after `T02` (unit tests) before spending real EnergyPlus time
   on `T03`. Stop for good after `T04` — do not attempt anything beyond the plan's own scope, and do
   not attempt or suggest a cluster submission even if `T04`'s gate re-check looks like a full pass.
   That decision belongs to a human director, outside this task entirely.

## Background (short — the plan doc has the full detail)

This project (OpenUBEM, an urban building energy model) generates one EnergyPlus IDF file per
building for several European districts, each with a per-dwelling ("apartment-level") thermal zone
layout. A safety net in `scripts/run_eu_s2_campaign.py` detects buildings whose geometry looks
EnergyPlus-fatal-risky and, for those only, discards the per-dwelling layout in favor of one zone per
floor. It currently over-fires on 57.7% of buildings in the affected districts, throwing away valid
layouts unnecessarily (`FINDING 249`). Two prior investigation rounds (one in-house, one by a
previous instance of an agent like you) narrowed this down and proposed a fix ("Option B"); a
targeted follow-up check then proved part of that fix's safety reasoning false. The plan doc you are
about to read is the corrected, restricted version of that fix — implement it exactly as written, run
the real EnergyPlus validation it specifies, and report the results. Do not re-investigate root cause
from scratch — it is already established and cited in the plan doc's §5.

## What to do

1. Read `docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu-nocore-finding249-remedy-2026-09-04.md`
   in full.
2. Execute `T01` → `T02` → (stop, report) → `T03` → `T04` → (stop, report) exactly as that doc
   specifies, respecting every hard rule above and in the plan doc's own §2.
3. After each task, append one progress-log entry to that same doc's §8, in the format already shown
   there (`#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status /
   Notes) — with real evidence, not a summary.
4. Stop after `T04`'s entry is appended. Do not touch anything cluster-related. This is not a pull
   request and not a cluster campaign — a human director reviews your progress-log entries next.
