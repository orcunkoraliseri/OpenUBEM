# `EU-15B` — Executor prompt: retire the strip cutter, carve the circulation core (T04–T05)

- **Arc**: European locations × Step 8. **Plan**: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- **Order**: **after `EU-15A` (T01–T03) has been reported and accepted.** Running it first refuses buildings
  that T02/T03 would have recovered.
- **Rulings implemented**: `D-EU-39` §2 (strip cutter retired) and §3 (circulation **CARVED**, not added).
- **Executor**: fresh Sonnet session. **Paste everything below the rule.**
- **Date of prompt**: 2026-08-30. **Authorisation**: local work only — no Speed, no `sbatch`.

---

## Task (paste from here)

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
Execute **T04 then T05**, then **stop at stop-and-report 1**. Do not start T06.

You are working in `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** — never bare
`python`. Git is handled externally: **never commit, never stage**.

### Hard rules

1. **Execute the plan. Do not propose alternatives.** If a rule document is ambiguous, **STOP and quote the
   conflict** — never resolve it yourself.
2. **Never reduce a building's dwelling count** to make it fit a grid, a habitability gate or a coverage bar.
   Refuse it into the disclosed residual instead. This is the one unconditional failure.
3. Touch only the files listed in plan §3. **No new files, reports, boards or helper scripts.**
4. Do not edit root `main.py`, any OVERVIEW/DESIGN doc, `openubem/config.py:34`, the frozen `previous/`
   documents, or anything under `openubem/outputs/eu_certified_rerun_2026-08-28/`.
5. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first**, and
   register any solved error there in the house format before closing the task.
6. Mirror `openubem/outputs/3D/` into `docs/docs_ACTIVE/europeanLocations/outputs_3D/` and verify byte-identical
   (`diff -rq`). Default to no code comments.

### T04 — retire the strip cutter as a success path (`D-EU-39` §2)

*What.* A storey the ruled route cannot express is **refused, not relabelled**: `dwelling_layout_emitted =
False`, `geometry_outcome = FALLBACK_PENDING_LAYOUT*`, `fallback_reason` set, and the building keeps
`one_zone_per_floor`.
*Why.* `DWELLING_LAYOUT_EMITTED` currently counts `equal_strip_multi_angle_sweep` as a success — that is
`FINDING 207`, the 93.6 % / 88.1 % figures that were really 57.81 %.
*How.* `_secondary()` (`openubem/geometry/european_residential.py:641`) stops returning an emitted layout.
*How to test.* **0** side-cars fleet-wide carry `scheme == equal_strip_multi_angle_sweep` together with a
`geometry_outcome` starting `DWELLING_LAYOUT_EMITTED`; per-district ruled coverage is recomputed and reported
against the **≥ 95 % per-district** bar (a fleet average does not satisfy it).

### T05 — carve the unconditioned core and the corridor spine (`D-EU-39` §3)

*What.* Cut circulation **out of the observed plate** and emit it as an unconditioned zone — a centroidal stair
core for **2–4 dwellings/storey** (12.0–25.0 m², 6–12 % of the plate), a **1.80 m double-loaded spine** on the
long axis for **≥ 5** — extruded `z = 0 → roof` so every dwelling shares a party wall with it.
*Why.* `has_unconditioned_core` is true on **0 of 2,541** buildings today; the core is the mechanism behind the
MVP's $b_u$ buffering. This also unblocks `EU-13B` T06.
*How.* `_centred_circulation_region` (`european_residential.py:237`) already computes the polygon — **subtract
it from the plate before partitioning**. Emit the zone with no heating/cooling and infiltration
`0.000500 m³/(s·m²)`. Extend it to the two ruled routes carrying none today: **`ruled_grid_2x1`** (2/storey is
inside the 2–4 stair-core band) and **`l_shape_decomposition`** (one core per wing, at the inner-corner
junction). The percentage rule binds; tag every departure from the absolute band as
`circulation_outside_ruled_absolute_band` (`FINDING 204` — never resolve the two criteria yourself).
**Publish `conditioned_floor_area_m2` beside `gross_footprint_area_m2`** on every side-car, every manifest row
and every viewer pop-up — conditioned area now falls, and both numbers must be visible.
*How to test.* Dwellings + circulation = the observed plate to **0.00 %** on every storey;
`has_unconditioned_core = true` wherever a storey carries ≥ 2 dwellings; the core zone appears in the IDF with
**no** `ZoneHVAC:IdealLoadsAirSystem`; conditioned area < gross area on exactly those buildings.

### Report (🔴 stop-and-report 1 — stop here, before any IDF work)

Append one progress-log entry per completed task to **§8 of the plan** and one row per task to
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`. Then report:

1. Per-district ruled coverage against the **≥ 95 %** bar — Madrid, Lyon, London, Bologna, each named.
2. The residual by `fallback_reason`, and confirmation that no dwelling count anywhere was reduced.
3. The conditioned-vs-gross floor-area table, per district.
4. The eight acceptance buildings of `rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §6, all five
   criteria each, including `relation/3730743` **refused**.
5. Test output — exact commands and pass/fail lines. **Then stop.**
