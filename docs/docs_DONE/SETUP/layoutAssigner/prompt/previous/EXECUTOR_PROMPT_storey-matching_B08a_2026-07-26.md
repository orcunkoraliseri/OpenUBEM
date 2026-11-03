# Executor prompt — B08a, placement diagnosis (E-LA-31 item 2)

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_implementation.md`
and execute **B08a only** (§5, Phase B). Do not execute B08b. Do not propose alternatives — execute
the plan. If the plan is ambiguous, STOP and quote the conflict.

## What B08a is

A **measurement-only diagnosis** of the residual cross-building placement defect. After B05,
27.00 % of `nyc_suburban` and 55.40 % of `la_suburban` buildings still overlap, against real-`auto`
controls of 0.00 % and 1.79 %. Median hull-centroid vs `footprint_centroid_utm` offset is 8.49 m
(nyc) against 0.0002 m for `auto`. You are finding out **why**, not fixing it.

**🔴 Remediation is forbidden in this task.** No production file under `openubem/` may be modified.
The manager picks the fix mechanism from your report and dispatches B08b separately.

## The three questions, from the plan

1. **Anchor.** Test the hypothesis that the scaled prototype is anchored at its local `(0, 0)`
   corner instead of centred on the real footprint centroid — i.e. the offset is the prototype's own
   local footprint half-diagonal. Report the fit **per archetype**, not as one aggregate, and report
   the part it fails to explain.
2. **Layer.** Is the offset in the **emitted IDF** or introduced by the **viewer path**?
   🔴 `openubem/viz/` is READ-ONLY under this plan. If the placement convention lives in
   `geometry_extract.py` / the CityJSON emitter, **STOP and report that** — do not edit `viz/`.
3. **Physics.** Does anything downstream consume inter-building placement today? Grep for generated
   shading / neighbour geometry in the `layout_assign` path and state the answer. If nothing does,
   say so — the honest framing is geometry and visual correctness, **not** an energy defect. Do not
   inflate it.

## Hard rules

- Work from **real `BuildingIDF.build()` output**. The A4-bis viewer generator is void evidence
  (§8 E-LA-30) — it reimplements scaling with a helper that is a content no-op on all 25
  prototypes. Do not use it, and do not copy its approach.
- **Prove any control you build differs from its treatment before you measure with it** (§8
  E-LA-31). This arc has produced that failure three times. If you build a comparison tree, byte-
  compare it first and report the proof. Beware `sys.path` clobbering by scripts that do their own
  `sys.path.insert` at import time, especially before a `loky`/multiprocessing spawn.
- Use `./.venv/Scripts/python.exe`. Plain `python` is not on PATH.
- Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never run compute on the Speed login node — `sbatch`
  fire-and-forget only, if you need the cluster at all (you probably do not; this is local geometry).
- Never `git commit` and never offer to. Git is handled externally.
- Figures go to `openubem/outputs/` (flat) **and** a copy under
  `docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/figures/`.
- Do not touch the two viewer HTML files the user named. B08b rebuilds those, not you.

## Deliverables

- `results/b08a_placement_diagnosis.csv` — per building: `osm_id, archetype, planar_k,
  local_centroid_x, local_centroid_y, predicted_offset, measured_offset`.
- A progress-log entry appended under §7 of the plan doc, in the arc's format (Artifacts /
  Deviations / Test status / Notes), plus a `git status --short openubem/ tests/ main.py` line
  proving you changed no production code.
- Your report to the manager: the mechanism, the per-archetype fit, the answers to questions 2 and 3,
  and a recommended fix location — **without implementing it**.

Report and stop.
