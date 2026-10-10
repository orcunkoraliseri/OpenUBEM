# Executor prompt — diagnose the backlog wave's non-accepted `FAILED` EnergyPlus tasks

**For: an external LLM session (Gemini / Antigravity), not a Claude subagent.**
**Repo root (Windows):** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Python:** `python` is **not** on PATH. Always invoke `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`
explicitly, with that repo root as the working directory.
**Cluster access:** you DO have `ssh`/`scp` to `o_iseri@speed.encs.concordia.ca` in this environment. Its login
shell is `tcsh`; do not rely on bash-only syntax over a bare `ssh` command — wrap remote commands as
`ssh o_iseri@speed.encs.concordia.ca "bash -lc '<command>'"` and keep each remote command on one physical line
(no embedded literal newlines inside the quoted script — they break tcsh's quote parsing).
**Local EnergyPlus:** if `C:\EnergyPlusV23-1-0\energyplus.exe` exists, use it; otherwise report that it is
missing and stop before any "run EnergyPlus" step — do not install anything.

## What this task is

**Read-only diagnosis only.** You are confirming (or correcting) an already-proposed root cause for one new
bug class, and separately classifying a second, unexplored one. You do **not** apply any fix to production
code. The deliverable is one report file plus, optionally, a *proposed* patch written as text (not applied).

## Hard rules

1. Do **not** edit any `.py` file anywhere in the repo. Do **not** edit any `.idf` file in place — you may
   download a copy of one to inspect or to run a local EnergyPlus test on, but never overwrite the shipped
   original, and never upload/scp anything back to Speed.
2. Do **not** run `sbatch`, `srun`, or any compute on the Speed login node. `scp`/`ssh ... sacct`/`ssh ... cat`
   read-only commands are fine (per this project's cluster rules — login node is for `mkdir`/`scp`/`tar`/
   `squeue`/`sacct` only, never compute).
3. Do **not** edit `main.py`, anything under `docs/docs_main/`, `docs/docs_stepN/`, or any OVERVIEW/DESIGN doc.
4. Do **not** `git commit` anything.
5. The only files you may **write** are:
   - `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/<stem>.idf` (downloaded copies, read-only
     inspection targets — create the parent folder if needed)
   - `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md` (your findings — the deliverable)
6. If you cannot reproduce a symptom described below against the actual downloaded IDF/err pair, say so plainly
   in the report and move on — do not force a match to make the write-up look clean.

## Background — why these four buildings, why now

A ~4,200-building EU-11 residential fleet backlog wave is running on Speed
(`PLAN_eu-82pct-ceiling-2026-09-05.md`, jobs `1306951`/`1306952`/`1306953`/`1305186`). Of the tasks that have
run so far, 24 are `FAILED` with an EnergyPlus `GetSurfaceData` (or related) `Fatal` at sizing, 0.2-1.4 s in,
before warmup. Classifying every failed task's `eplusout.err` (not just `sacct` state) shows **four distinct
signatures**, not one:

1. `RoofCeiling:Detailed` vertex-size mismatch (13/24) — the known `FINDING 210` GEOS-build-fragility class.
   Accepted, no action needed, **not your task**.
2. `GetSurfaceData: Zero or negative surface area[~1E-07 to 1E-09]` sliver (3/24) — the known `D-EU-43` family.
   Accepted, no action needed, **not your task**.
3. **New — your primary task.** `GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface ...
   does not have the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent
   surface ...` (7/24). See `FINDING 253` in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (search that
   exact string to find the entry) for the proposed root cause. **Your job is to verify or correct that root
   cause and write a proposed fix — you do not apply it.**
4. **New — your secondary task.** `CalcCoordinateTransformation: Invalid dot product` fatal, preceded by 13×
   `CheckConvexity: ... is non-planar` and a `114 degenerate surfaces` severe (1/24 so far). Not yet analyzed.
   **Your job is to classify it**: is it the same `intersect_match`-sliver family as `FINDING 210`/`D-EU-43`
   (i.e. would `_stabilize_ring_coords`/`find_mismatched_interzone_pairs` already gate it, or does it slip past
   both), or something genuinely different? A clear classification is a sufficient outcome even without a fix
   proposal, since there is only one instance so far.

## Task A — verify `FINDING 253` (construction reverse-order), primary

Named failing stems (district / stem / Speed task):
- Madrid (`ES-MAD-BERRUGUETE`): `04c3d8bc97b3aa32` (task `1306953_48`), `dc4c8768bb34abb7` (task `1306953_40`)
- Bologna (`IT-BOL-GALVANI2`): `4d40e0364b2f0e16` (task `1305186_133`)

1. Read `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`'s `FINDING 253` entry (ceiling82 chapter, near the
   end of the file) for the full proposed root cause and the exact `file:line` pointers
   (`scripts/run_eu_s2_campaign.py:453-457,587-594`; `openubem/idf/european_physics.py:34-54`). Read those
   actual file sections yourself — do not trust the paraphrase alone.
2. Download each stem's shipped IDF and its `eplusout.err` from Speed, e.g. for Madrid:
   `ssh o_iseri@speed.encs.concordia.ca "bash -lc 'cat /speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_backlog_2026-09-05/idfs/04c3d8bc97b3aa32.idf'" > openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/04c3d8bc97b3aa32.idf`
   and the matching `.../out/04c3d8bc97b3aa32/eplusout.err` the same way (adjust the district folder name —
   `EU11_ES-MAD-BERRUGUETE_backlog_2026-09-05` for Madrid, find Bologna's equivalent folder yourself via
   `ssh ... "bash -lc 'ls /speed-scratch/o_iseri/fleets/'"` — do not assume its exact name).
3. In each downloaded IDF, find the two named `BUILDINGSURFACE:DETAILED` objects from the `.err`'s
   `Last severe error=` line and their `Construction_Name`. Find the matching `CONSTRUCTION` and
   `MATERIAL:NOMASS` objects and compare: do `EU_roof_Construction` and `EU_floor_Construction` reference
   different materials (different `Thermal_Resistance`)? Confirm this directly from the IDF text, quote the
   actual object blocks in your report, do not infer from the code alone.
4. Confirm reproduction: run local EnergyPlus directly on the downloaded IDF (`ExpandObjects` then
   `energyplus.exe`, matching how `submit_fleet_t08.sbatch` invokes it — read that script if you need the
   exact invocation) and confirm you get the same `Fatal` locally, not only on Speed.
5. Write a **proposed fix** as text in your report (a unified diff or a precise before/after code block against
   `scripts/run_eu_s2_campaign.py`'s construction-assignment loop) that would make every interzone
   `ROOF`↔`FLOOR`/`CEILING` pair use matching materials, without changing the construction assigned to true
   exterior/ground surfaces. Do not write this fix into the actual `.py` file.
6. If your own diagnosis disagrees with `FINDING 253`'s proposed root cause, say exactly where and why —
   do not silently adjust your findings to match it.

## Task B — classify the `CalcCoordinateTransformation` fatal, secondary

Stem: Madrid `c71e82e57d99bed1` (task `1306953_9`), folder `EU11_ES-MAD-BERRUGUETE_backlog_2026-09-05` (same
as Task A).

1. Download this stem's IDF and full `eplusout.err` the same way as Task A.
2. Read `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`'s `FINDING 210` entry in full — it already
   documents `intersect_match`-introduced vertex divergence, near-duplicate-vertex slivers, and collinear-point
   convexity failures as one family, with the exact gate functions
   (`find_mismatched_interzone_pairs`, `_has_near_duplicate_vertex_surfaces`) that already exist in
   `openubem/idf/surfaces.py` (non-editable, `D-EU-41` — read it, do not edit it).
3. For 2-3 of the surfaces named in this stem's `** Severe ** CheckConvexity: ... is non-planar` lines, find
   their `BUILDINGSURFACE:DETAILED` vertex lists in the downloaded IDF and check by hand (or with a short
   throwaway script that writes only into the debug folder above) whether the listed vertices contain a
   near-duplicate pair or a near-collinear point — the same kind of artifact `FINDING 210` describes — or
   whether the degeneracy is of a different shape (e.g. a genuinely self-intersecting or zero-area ring from
   the start, not an EnergyPlus-side convexity collapse).
4. Report your classification plainly: same family as `FINDING 210`/already gated, same family but slipping
   past the existing gate (say which check misses it and why), or a new mechanism. A fix proposal is optional
   here — a clear classification is a sufficient outcome for this task.

## Report back (do not paraphrase into a summary — quote the real numbers/text)

Write `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md` containing, in order:

1. Task A: the two constructions' actual `MATERIAL:NOMASS`/`CONSTRUCTION` object text for all 3 named stems,
   confirmation (or refutation) of the root cause, the local-EnergyPlus reproduction result (RC, severe/fatal
   count), and your proposed fix as a diff/code block.
2. Task B: the vertex data you inspected, quoted, and your classification with reasoning.
3. Nothing else — no recommendation on when/whether to resubmit anything to Speed, no `git` action, no
   editing of the live `.py` files. That decision belongs to the project's director (a separate Claude Code
   session), not to you.
