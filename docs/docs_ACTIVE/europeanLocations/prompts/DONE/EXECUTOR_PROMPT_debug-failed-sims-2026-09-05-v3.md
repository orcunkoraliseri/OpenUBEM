# Executor prompt v3 — third `CalcCoordinateTransformation` instance (addendum, not a replacement)

**For: an external LLM session (Gemini / Antigravity), not a Claude subagent.**
**Repo root (Windows):** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Python:** `python` is **not** on PATH. Always invoke `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`
explicitly, with that repo root as the working directory.
**Cluster access:** `ssh`/`scp` to `o_iseri@speed.encs.concordia.ca`. Login shell is `tcsh` — wrap remote
commands as `ssh o_iseri@speed.encs.concordia.ca "bash -lc '<command>'"`, one physical line, no embedded
literal newlines.
**Local EnergyPlus:** `C:\EnergyPlusV23-1-0\energyplus.exe` if present; otherwise report it missing and stop
before any "run EnergyPlus" step.

## Relationship to prior prompts

This is an **addendum** to `prompts/DONE/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05.md` (v1) and
`prompts/DONE/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05-v2.md` (v2). Both are done — v1's Task A
(`FINDING 253`) is fixed, shipped, and drained on Speed; v1's Task B and v2's Task C (the first two
`CalcCoordinateTransformation` instances) are classified. This prompt adds exactly one new task (Task D) for
a **third instance** of the same signature, found during harvest-monitoring after the fleet finished draining.

**Read `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`'s `FINDING 254` entry first** (search that exact
string) — it already documents the mechanism confirmed on the first two instances (courtyard-hole bypass,
sub-mm `intersect_match` vertex divergence, same family as `FINDING 210`/`D-EU-43`). You do not need to
re-derive the mechanism from scratch; your job is to check whether this third instance fits it or breaks it.

## Full current failure picture (context only, not new work)

Every currently `FAILED` task across the fleet (30 total, all districts, backlog + Step2-delta + remedy jobs)
is already classified into one of 4 signatures: `FINDING 210` (accepted), `D-EU-43` (accepted), `FINDING 253`
(closed — fixed, shipped, drained clean), `FINDING 254` (accepted, courtyard-hole edge case). This third
instance is the **only** currently-failed task that has not yet had an external, vertex-level verification —
everything else is either long-established (`FINDING 210`/`D-EU-43` predate this arc) or already closed
(`FINDING 253`). Do not re-investigate any other failed task; that would be redundant spend.

## What this task is

**Read-only diagnosis only**, same hard rules as v1/v2:

1. Do **not** edit any `.py` file. Do **not** edit any `.idf` file in place (download a copy to inspect only).
2. Do **not** run `sbatch`/`srun`/any compute on the Speed login node. Read-only `ssh`/`scp`/`sacct`/`cat` only.
3. Do **not** edit `main.py`, `docs/docs_main/`, `docs/docs_stepN/`, or any OVERVIEW/DESIGN doc.
4. Do **not** `git commit` anything.
5. The only files you may **write** are:
   - `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/635e498716218cea.idf` (downloaded copy)
   - `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/635e498716218cea_speed.err` (downloaded copy)
   - `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md` (append — add a new `## Task D`
     section, do not overwrite Task A/B/C's content)
6. If you cannot reproduce the symptom against the actual downloaded IDF/err pair, say so plainly and stop.

## Task D — does the 3rd `CalcCoordinateTransformation` instance match Task B/C's classification?

Stem: Bologna (`IT-BOL-GALVANI2`) `635e498716218cea`, task `1305186_524`, folder
`EU11_IT-BOL-GALVANI2_finding249_remedy_2026-09-04` (already resolved — do not re-search):

- IDF: `/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2_finding249_remedy_2026-09-04/idfs/635e498716218cea.idf`
- Err: `/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2_finding249_remedy_2026-09-04/out/635e498716218cea/eplusout.err`

1. `scp` both files down to the two paths listed in rule 5 above.
2. Repeat v1 Task B / v2 Task C's steps: read the `** Severe ** CheckConvexity: ... is non-planar` lines and
   the `Last severe error=` line, find the named surfaces' vertex lists in the downloaded IDF, and check by
   hand whether the same near-duplicate-vertex / near-collinear-point artifact is present (the `FINDING 210`
   family), and whether this building has a genuine courtyard void (`area >= 1.0 m²`) that would explain why
   `_force_reroute_room_layout_to_one_zone_per_floor` declined to reroute it (per the mechanism already
   documented in `FINDING 254`).
3. **State explicitly**: does this third instance share the same mechanism as the first two, or does it look
   different (e.g. no courtyard, a larger sliver, a different boundary condition)? A count of 3 with one
   shared mechanism is a stronger accept-and-move-on case than 3 with any outlier — say which it is.

## Report back

Append to `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md` a `## Task D` section
with: the vertex data quoted, the courtyard-area check, and an explicit same-mechanism-or-not verdict against
Task B/C. Nothing else — no resubmission recommendation, no `git` action, no re-check of any other failed
task. That decision belongs to the project's director, not to you.
