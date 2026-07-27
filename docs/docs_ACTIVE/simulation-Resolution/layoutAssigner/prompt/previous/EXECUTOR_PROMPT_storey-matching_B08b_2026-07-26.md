# Executor prompt — B08b, apply D8 (placement re-centring) and rebuild both viewers

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_implementation.md`
and execute **B08b** (§5, Phase B), following **D8** exactly. Do not propose alternatives — the
mechanism is already decided on B08a's evidence. If the plan is ambiguous, STOP and quote the
conflict.

## Gate check, first thing

§0 must show **B06 ticked `[x]`** (or explicitly closed in §7). B06 edits the same file you are about
to edit. If B06 is not closed, STOP and say so.

## What you are implementing (D8 — do not re-debate)

A **pure translation** inside `scale_baseline_idf()` in `openubem/geometry/layout_assigner.py`,
applied *after* scaling, so the prototype lands centred on local `(0, 0)` before the emitter's
existing `+footprint_centroid_utm` placement runs.

- **Anchor** = the XY bounding-box centre of the scaled model's absolute geometry.
- The translation must reach **every** coordinate the module already treats as absolute — the
  `_UNCONDITIONAL_ABSOLUTE_SPECS` classes **and** the `Zone` X/Y Origins. Translating only one of the
  two coordinate systems reintroduces E-LA-28 in mirror image.
- **Z is not touched.**
- Nothing in `openubem/viz/` changes — it is READ-ONLY under this plan and B08a already proved the
  emitter adds no transform of its own.

## Acceptance

- **Binding gate:** median hull-centroid vs `footprint_centroid_utm` offset **≤ 1 m** on both scenes
  (today: nyc 8.49 m, la 11.49 m).
- **Reported, not a gate:** buildings involved in ≥ 1 overlap, against the real-`auto` controls
  (nyc 0.00 %, la 1.79 %). Re-centring cannot reach 0 % — `layout_assign` substitutes a prototype
  whose footprint shape and aspect ratio are not the real building's, so a residual is expected and
  is a design property, not a bug. Report the number that comes out and label the remainder honestly.
- **Per-archetype residual:** if any archetype's residual hull-offset exceeds 1 m because its hull
  centroid and bbox centre genuinely diverge, report it per archetype. Do **not** switch the anchor
  yourself — the manager decides that.
- **Energy null:** re-run B05e's ~10-building before/after and report the deltas. Translating a
  building in XY should change nothing (B08a Q3: the `layout_assign` branch returns before
  `extrude_geometry()`; every row reports `num_context_buildings: 0`). That is a prediction — verify
  it, don't assume it.
- `pytest` on the touched modules.

## The viewer deliverable — this is what the user actually asked for

Rebuild **in place**, at exactly these paths:

- `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\figures\nyc_suburban_layout_assign_viewer.html`
- `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\figures\la_suburban_layout_assign_viewer.html`

- From **real `BuildingIDF.build()` output**. The A4-bis generator is void evidence (§8 E-LA-30) —
  its private `fast_scale_idf_text()` is a content no-op on all 25 prototypes. Do not use it, do not
  copy its approach.
- **Archive the current post-B05 copies** alongside the already-archived pre-B05 ones before
  overwriting. Do not destroy either earlier state.
- Same camera/scene settings as the current files, so the user's re-verification is a like-for-like
  comparison.

## Hard rules

- `./.venv/Scripts/python.exe` — plain `python` is not on PATH.
- Prove any control differs from its treatment **before** measuring with it (§8 E-LA-31, three
  occurrences in this arc). Watch for scripts that `sys.path.insert` at import time and clobber a
  scratch-first ordering, especially before a `loky`/multiprocessing spawn.
- Long runs: detached, and block on **artifacts appearing**, not on process liveness. `pgrep` does
  not track Windows console processes reliably here.
- Never run compute on the Speed login node. `sbatch` fire-and-forget only if you need the cluster.
- Never `git commit`, never offer to.
- Do not touch `openubem/viz/`, `openubem/idf/opaque_assembly.py`, root `main.py`, or any
  OVERVIEW/DESIGN doc.
- Figures to `openubem/outputs/` (flat) **and** a copy under `debug/storey-Matching/figures/`.
- Append progress-log entries under §7 of the plan doc in the arc's format (Artifacts / Deviations /
  Test status / Notes), plus a `git status --short openubem/ tests/ main.py` line.

Report the numbers even if they miss the target. A partial improvement honestly reported is worth
more than a target hit that was reframed.
