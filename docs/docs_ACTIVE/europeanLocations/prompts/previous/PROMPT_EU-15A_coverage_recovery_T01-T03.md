# `EU-15A` — Executor prompt: attribute the 33.2 % gap and recover it (T01–T03)

- **Arc**: European locations × Step 8. **Plan**: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- **Order**: first dispatch of the plan. Nothing depends on it upstream; `EU-15B` depends on it.
- **Executor**: fresh Sonnet session. **Paste everything below the rule.**
- **Date of prompt**: 2026-08-30. **Authorisation**: local work only — no Speed, no `sbatch`.

---

## Task (paste from here)

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
Execute **T01, T02, T03** in order, then stop and report. Do not start T04.

You are working in `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** — never bare
`python`. Git is handled externally: **never commit, never stage**.

### Hard rules

1. **Execute the plan. Do not propose alternatives.** If a rule document is ambiguous, **STOP and quote the
   conflict** — never resolve it yourself.
2. **Never reduce a building's dwelling count** to make it fit a grid, a habitability gate or a coverage bar.
   Refuse it into the disclosed residual instead. This is the one unconditional failure.
3. **Do not loosen `audit_european_floor_partition`, the 0.15 m regularization tolerance, or the 2 % area gate.**
4. Touch only the files listed in plan §3. **No new files, reports, boards or helper scripts.**
5. Do not edit root `main.py`, any OVERVIEW/DESIGN doc, `openubem/config.py:34`, the frozen `previous/`
   documents, or anything under `openubem/outputs/eu_certified_rerun_2026-08-28/`.
6. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first.** After
   solving any error, register it there in the house format before closing the task. Not optional.
7. Default to no code comments. No `.py` files under `docs/`.

### T01 — record why the secondary route was taken

*What.* Set `fallback_reason` on every building that leaves the ruled route, and publish the per-cause census
per district.
*Why.* It is `None` on all 843 strip-cutter buildings today, so the 33.2 % gap cannot be attributed to a cause.
*How.* `_secondary()` (`openubem/geometry/european_residential.py:641`) already receives a `reason_hint` and
discards it when the legacy layout succeeds — keep the hint and propagate it into the side-car
(`scripts/emit_eu11_layout_sidecars.py`). **Measurement and plumbing only — no partitioner behaviour change.**
*How to test.* Re-emit one district; `fallback_reason` is non-null on 100 % of `equal_strip_multi_angle_sweep`
side-cars, and the per-cause census sums to that district's strip count exactly.

### T02 — implement courtyard unfolding (report §6.4)

*What.* Detect the interior-ring / U-shape footprint, subtract the courtyard void, unfold the remaining C-band
into three orthogonal wings served by circulation nodes at the two inner corners, partition each wing by area
fraction.
*Why.* `classify_building_morphology` returns `courtyard_secondary` and
`generate_european_ruled_storey_layout:676` sends it straight to the strip cutter — a named, un-implemented
route and the single largest identified cause of the 33.2 %.
*How.* New route alongside `l_shape_decomposition`, reusing `_split_at_reflex_vertex` and the wing-proportional
recursion already at `european_residential.py:676`–`:700`.
*How to test.* Golden fixtures (square courtyard, rectangular courtyard, U-shape, C-shape) in
`tests/geometry/test_eu15_ruled_coverage.py`: every wing partition passes `audit_european_floor_partition`,
area error **0.00 %**, every dwelling keeps **≥ 2.50 m** facade contact.

### T03 — harden the L-shape and gallery routes on noisy GIS footprints

*What.* Make `_split_at_reflex_vertex` and the gallery route survive real footprints with near-collinear
vertices, slivers and multiple reflex vertices.
*Why.* They currently fall back rather than mislabel — correct behaviour, but it is the second cause of the gap.
*How.* Pre-simplify at the existing `regularization_tolerance_m = 0.15`; handle more than one reflex vertex by
recursing on the larger lobe; leave the 2 % regularization area gate unchanged.
*How to test.* Replay the 843 strip-cutter buildings. Report how many T02 and T03 each recover, **separately**,
and that **0 buildings changed their declared dwelling count**.

### Report (stop here)

Append one progress-log entry per completed task to **§8 of the plan** (`#### TXX — <title> — completed
YYYY-MM-DD`, then Artifacts / Deviations / Test status / Notes) and one row per task to
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`. Then report to the director:

1. The per-district `fallback_reason` census (Madrid / Lyon / London / Bologna, each named), summing to 843.
2. Recovery from T02 and from T03, separately, as counts and as new per-district ruled coverage %.
3. The residual still on the strip cutter, by cause.
4. Test output — the exact `pytest` command and its pass/fail line.
5. Any conflict you stopped on, quoted verbatim.
