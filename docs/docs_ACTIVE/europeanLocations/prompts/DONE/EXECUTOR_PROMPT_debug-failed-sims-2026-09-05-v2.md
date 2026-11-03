# Executor prompt v2 — second `CalcCoordinateTransformation` instance (addendum, not a replacement)

**For: an external LLM session (Gemini / Antigravity), not a Claude subagent.**
**Repo root (Windows):** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Python:** `python` is **not** on PATH. Always invoke `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`
explicitly, with that repo root as the working directory.
**Cluster access:** `ssh`/`scp` to `o_iseri@speed.encs.concordia.ca`. Login shell is `tcsh` — wrap remote
commands as `ssh o_iseri@speed.encs.concordia.ca "bash -lc '<command>'"`, one physical line, no embedded
literal newlines.
**Local EnergyPlus:** `C:\EnergyPlusV23-1-0\energyplus.exe` if present; otherwise report it missing and stop
before any "run EnergyPlus" step.

## Relationship to the first prompt

This is an **addendum** to `prompts/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05.md` (v1), not a replacement.
If you have already started or finished v1's Task A / Task B, keep going / do not redo them. This prompt adds
exactly one new task (Task C) that v1 could not have scoped, because the 2nd instance below was found by the
project's own harvest-monitoring **after** v1 was handed off.

**Read `docs/docs_ACTIVE/europeanLocations/debugs/docs/INVESTIGATION_failed-sims-classification_2026-09-05.md`
first** — it is a self-contained, current snapshot of all 28 known failed simulations and their classification,
so you do not need to search the ~2,000-line `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` for context.

## What this task is

**Read-only diagnosis only**, same hard rules as v1:

1. Do **not** edit any `.py` file. Do **not** edit any `.idf` file in place (download a copy to inspect only).
2. Do **not** run `sbatch`/`srun`/any compute on the Speed login node. Read-only `ssh`/`scp`/`sacct`/`cat` only.
3. Do **not** edit `main.py`, `docs/docs_main/`, `docs/docs_stepN/`, any OVERVIEW/DESIGN doc, or the
   investigation file you just read.
4. Do **not** `git commit` anything.
5. The only files you may **write** are:
   - `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/<stem>.idf` (downloaded copies)
   - `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md` (append to this file if it
     already exists from your v1 work — add a new `## Task C` section, do not overwrite Task A/B's content)
6. If you cannot reproduce the symptom against the actual downloaded IDF/err pair, say so plainly and move on.

## Task C — does the 2nd `CalcCoordinateTransformation` instance match your v1 Task B classification?

Stem: Bologna (`IT-BOL-GALVANI2`) `fd4b13e28f1c6f47`, task `1308161_12`, folder
`EU11_IT-BOL-GALVANI2_step2delta_2026-09-05` (find its exact path on Speed via
`ssh o_iseri@speed.encs.concordia.ca "bash -lc 'ls /speed-scratch/o_iseri/fleets/ | grep -i bol'"` — do not
assume the exact folder name).

1. Download this stem's IDF and full `eplusout.err` the same way as v1 Task B (Madrid `c71e82e57d99bed1`,
   task `1306953_9`, folder `EU11_ES-MAD-BERRUGUETE_backlog_2026-09-05`).
2. Repeat v1 Task B's steps 2-3 on this second stem: read the `** Severe ** CheckConvexity: ... is non-planar`
   lines, find the named surfaces' vertex lists in the downloaded IDF, and check by hand whether the same kind
   of near-duplicate-vertex or near-collinear-point artifact is present (the `FINDING 210` family,
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, search that exact string), or whether this instance's
   degeneracy has a different shape from the Madrid one.
3. **State explicitly**: do both instances share one classification (same family, or same "slips past the
   existing gate" mechanism), or does the 2nd instance look like a different mechanism from the 1st? A fleet of
   2 with two different mechanisms is a materially different finding from 2 with one mechanism — say which it
   is, do not average them into a vague answer.

## Report back

Append to `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md` (create it if v1 has not
written it yet) a `## Task C` section with: the 2nd stem's vertex data quoted, your classification, and an
explicit same-mechanism-or-not verdict against your own v1 Task B answer. Nothing else — no resubmission
recommendation, no `git` action. That decision belongs to the project's director, not to you.
