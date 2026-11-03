# DEBUG PLAN — clean connected-corridor zoning (kill fake-corridor slivers + connect corridors)

> **Binding contract:** the OpenUBEM zero-fitted-parameters + mandatory-provenance rules, and the
> existing `layoutGenerator.py` behavior (area conservation to machine precision, degrade-to-per-floor
> safety net, 0-Fatal/0-Severe E+ on synthetic + live shapes). Manager (Fable) authored this plan and
> audits; a **Sonnet employee executes ALL code + tests + figures**. Manager does not write feature code.
> Author: manager, 2026-07-03. This activates the long-deferred **T18-DIAG** with a corridor-connectivity
> extension the user flagged this session.

---

## 1. User report (verbatim intent, 2026-07-03)

Looking at `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/outputs/` (both hotel and midrise grids):
> "corridors do not connect to each other, and there are very small spaces looks like corridor but they
> are not, so needs to be updated with clean zoning."

Two defects, one root cause:
- **(D1) fake-corridor slivers** — thin, corridor-width strips tagged as rooms (GuestRoom/Apartment), sitting in the corridor's path. They "look like corridor but are not."
- **(D2) disconnected corridors** — the per-wing corridors read as separate stubs with a gap between them (the gap IS the D1 sliver), instead of one continuous walkable corridor turning at junctions.

---

## 2. Confirmed diagnostic (manager, do NOT re-derive)

`generate_layout(L_shape, "MidriseApartment", 1)` on the synthetic L (`union(box(0,0,40,15), box(0,0,15,40))`) emits **15 floor-0 zones = 6 corridor cells + 9 unit cells**:

| tag | space_type | dims (m) | note |
|---|---|---|---|
| w0c0 | Corridor | 1.68 × 25.0 | vertical corridor run |
| w0c2 | Corridor | 1.68 × 25.0 | second corridor run |
| w0c1,c3,c4 | Corridor | 1.68 × 6.66 | corridor stubs |
| w0c5 | Corridor | 1.68 × 1.68 | junction cell |
| w0u4 | **Apartment** | **1.68 × 6.66** | **← FAKE-CORRIDOR SLIVER (D1)** |
| w0u0,u1,u6,u7 | Apartment | 6.66 × 25.0 | real rooms |
| w0u2,u3,u5,u8 | Apartment | 6.66 × 6.66 | real rooms |

The corridor is fragmented into **6 separate thermal zones**; one room cell (`u4`, exactly corridor-width × room-depth) is a bleed fragment that breaks the visual corridor line.

---

## 3. Root cause (manager, read `layoutGenerator.py`)

`_pack_connected_spine` (`:652`) tiles the **whole** aligned footprint with a **full-span global grid**:
- `_spine_cut_values` (`:554`) emits, for each corridor run, cut coordinates at `centerline ± c/2`, plus every wing bound.
- `_grid_cut` (`:593`) runs those cut lines the **full span** of the footprint (`minx-1 … maxx+1`), then keeps interior polygonized cells.
- Each cell is tagged corridor/unit by a single point-in-`corridor`-buffer test (`:690`).

**Why the sliver (D1):** the wings decompose so that wing A's corridor is vertical (`x=7.5`) and wing B's is horizontal (`y=7.5`, only spanning wing B + a bridge). The **horizontal** corridor's cut lines `y=6.66/8.34` run full-span, so they slice **through wing A's west room band** (`x0–6.66`), carving a `1.68`-tall strip (`u4`). That strip is at corridor height but lies outside the buffered corridor polygon (the horizontal corridor doesn't extend that far west), so the point test tags it a room. It is a cross-wing **bleed fragment**.

**Why disconnected (D2):** the horizontal corridor exists only for `x ≥ 6.66`; west of that, at corridor height, sits the `u4` room sliver — so the corridor visually stops short of the west wall and reads as disconnected from wing A.

## 3a. The hard constraint that makes this delicate (why prior fixes failed)

The full-span grid was **deliberate** (comment `layoutGenerator.py:684`: "conforming by construction"). Because every cell edge lies on a global grid line, adjacent zones share **full** edges, so geomeppy's `intersect_match` never hits its coplanar-containment `IndexError`. The two obvious fixes both regressed before:
- **Wing-local cuts** (only cut each wing by its own corridor) → clean, but creates **T-junctions** at wing boundaries (a room edge meeting the middle of a neighbor's edge) → geomeppy `break_polygons` `IndexError` → E+ Fatal / `failed_worker_exception`.
- **Post-hoc merge of the sliver into its neighbor** → this is exactly what **crashed in T16b** (T-junction reintroduced against the still-subdivided corridor column). `T12-FIX` therefore **drops** degenerate cells, never merges.

So any fix MUST stay extrusion-safe (no new T-junctions) OR rely on the existing degrade net. **This is why the change is Opus-plan / cluster-validated, not a quick redraw.**

---

## 4. Scope + blast radius (READ — this is not viz-only)

- `_pack_connected_spine` is the **shared** engine for **all** `units_corridor` complex-shape packing. Changing it changes:
  - **Hotel preview figures** — preview-only (`force_complex`); production degrades hotels to per-floor, so **zero production-sim risk for hotels**. Figures update immediately.
  - **Production MidriseApartment `room_layout`** — `complex_shapes_supported=True`, so this is the **live production geometry** on L/U/T/O/cross apartments. Changing it is **correctness-affecting** (new zone counts + area split) → **mandatory E+ 0-Fatal/0-Severe re-validation** before it can be trusted; the committed baseline must not regress.
- **Safety net already exists:** `generate_layout`'s 1%-area-conservation check + `_is_degenerate_cell` drop + the `surfaces.py` intersect-fallback reroute all degrade a bad footprint to `one_zone_per_floor` rather than Fatal. The fix must **keep** these nets so worst case is "more degrades," never a Fatal.

---

## 5. Proposed approach (manager-specified; Sonnet prototypes + verifies, does not re-debate the goal)

**Target output per complex footprint:** ONE connected corridor zone (or the minimum number of connected pieces the geometry forces) + clean room cells with **no** corridor-width slivers, area conserved to `<1e-4` relative.

**Primary approach — "corridor-first, per-wing rooms":**
1. Build the connected corridor centerline network exactly as today (`_connect_centerlines([_wing_centerline(w) …])`).
2. `corridor_poly = buffer(net, c/2, cap_style=flat, join_style=mitre) ∩ aligned`, cleaned. Emit the corridor as a **single connected zone** (not per-cell). This alone fixes D2. If `corridor_poly` is a MultiPolygon, emit each connected piece as its own corridor zone (still no interleaved room slivers).
3. Rooms: for **each wing**, `room_region = wing.difference(corridor_poly)`; split into connected parts; subdivide **each part along its own long axis into `round(len/bay)` cells** (reuse the `_long_edge_angle` per-region rotation the plot script's `_zone_room_segments` already uses). Because rooms are cut **locally per region** (never by the perpendicular corridor's global lines), **no bleed sliver forms** → fixes D1.
4. Rotate every sub-polygon back to world frame, `_clean`, drop `_is_degenerate_cell` leftovers, keep the existing 1%-area net → degrade to per-floor if too much is lost.

**The open risk is EXACTLY §3a (extrusion T-junctions).** Sonnet MUST verify via E+, not assume. If the corridor-first output Fatals/Severes on any synthetic shape:
- **Option B (fallback, still clean):** keep the corridor as one zone, but re-derive the **room** cut lines so they are **conforming to the corridor boundary** (extend each room-region cut to the nearest corridor edge, not full-span), and snap emitted world coords to the existing `VERTEX_SNAP_M` grid + drop collinear verts (the `T12-FIX` technique) before extrusion.
- **Option C (last resort, guaranteed safe):** keep today's full-span grid + point-tag, but **re-tag** each corridor-width unit sliver whose full long edge is shared with a corridor cell as **Corridor** (pure tag flip, same conforming cells → zero new T-junctions, area-exact). This kills D1/D2 visually and is provably extrusion-safe, at the cost of a slightly stubby corridor. Use ONLY if A and B both Fatal.

Manager picks among A/B/C **at CP-1** based on Sonnet's local-geometry + E+ evidence — Sonnet reports, does not decide the architecture.

---

## 6. Hard rules for the executor (Sonnet)
1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. No `.py` under `docs/`. Never edit root `main.py`, OVERVIEW, or DESIGN.
2. **Execute this plan; do not re-plan.** If geometry is genuinely ambiguous, STOP and report to the manager with the concrete output — do not invent a fourth approach.
3. **Zero fitted parameters.** corridor width / depth / bay come from `MODULE_SPECS`. No magic numbers beyond the already-cited tolerances (`MIN_ZONE_AREA_M2`, `VERTEX_SNAP_M`, `CLEANUP_SIMPLIFY_TOL_M`).
4. **Keep the degrade net.** Every path must still fall back to `one_zone_per_floor` rather than emit broken geometry or Fatal.
5. **No login-node compute.** Any cluster run = `sbatch` fire-and-forget + read output; monitoring on a cheap model at ≥30-min / event-driven.
6. **`auto` mode unchanged.** Only the `room_layout` complex-shape path changes.
7. Default to no comments; one line max when the WHY is non-obvious.
8. Preserve machine-precision area conservation (the existing strict `1e-5` donut test must stay green).

---

## 7. Task list

- **T1 — Local prototype + cleanliness proof (no E+).** *What:* implement Approach A (§5) as a new internal helper (e.g. `_pack_connected_spine_clean`) OR a rework of `_pack_connected_spine`; run it on synthetic L/U/T/O/cross for MidriseApartment **and** SmallHotel(`force_complex`). *Why:* prove D1/D2 gone before any E+ cost. *How:* reuse `_wings_in_frame`, `_wing_centerline`, `_connect_centerlines`, `_long_edge_angle`, `_clean`, `_is_degenerate_cell`. *How to test:* for every shape print `corridor_zone_count`, `connected_corridor_pieces`, `unit_count`, `sliver_count` (unit whose short side `< c + 0.3`), and area drift. **Acceptance: 0 slivers, corridor in ≤ (number of disjoint wings ÷ 2 + 1) connected pieces, area drift `<1e-4`, no zone `< MIN_ZONE_AREA_M2`.** Report the table to the manager.
- **T2 — Unit-test the geometry.** *What:* extend `tests/test_layout_generator.py` — assert on L/U/T/O/cross that (a) no emitted unit cell has a short side `< corridor_width + 0.3`, (b) corridor cells union to a connected polygon, (c) area conserved `<1e-4`, (d) MidriseApartment still returns non-empty (no accidental degrade on clean synthetics). *How to test:* the suite is the test.
- **T3 — E+ 0-Fatal/0-Severe synthetic smoke (THE GATE).** *What:* build IDFs for L/U/T/O/cross MidriseApartment (production loads path — α-normalized, infiltration, fenestration, HVAC/DHW, per the `T13a` follow-up harness pattern, NOT raw corridor loads) and run E+ 23.1. *Why:* §3a — synthetic-clean ≠ extrusion-safe; this is the make-or-break. *How:* mirror the existing synthetic smoke in `tests/test_layout_generator.py` / the `T13a` prod-loads harness; run **local, single-building, one at a time** (this is small — not a cluster job). *How to test:* **every shape 0 Fatal / 0 Severe.** If ANY Fatals → STOP, report the `.err` signature + which cells; manager rules on Option B/C.
- **T4 — Full regression suite.** *What:* `pytest tests/test_layout_generator.py tests/test_zoning.py tests/test_surfaces.py tests/test_step3_orchestrator.py -q`. *Why:* the room_layout path is shared; nothing else may shift. *How to test:* all green; the strict donut `1e-5` area test still passes.
- **T5 — Regenerate figures.** *What:* re-run `scripts/plot_layout_grid.py`; regenerate all 3 grids into **both** `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/outputs/` and `openubem/outputs/LayoutGenerator/`. *Why:* the deliverable the user sees. *How to test:* manager eyeballs — corridors connected, no fake-corridor slivers, on both hotel grids and the apartment grid.
- **T6 — Cluster LIVE_SMOKE (production-apartment confidence, USER-GATED).** *What:* re-run a `la_suburban`/`la_urban` n≥30 non-rect MidriseApartment subset in `zone` mode (the `T12` pattern) → assert 0 Fatal and report gen-success + how many keep `room_layout` vs degrade. *Why:* synthetic-green ≠ live-green (the standing blind spot); confirms real OSM footprints don't Fatal with the new geometry. *How:* `sbatch` fire-and-forget, cheap-model monitoring ≥30-min. **HELD for explicit user go** (budget-consuming array). *How to test:* the smoke gate.

---

## 8. Stop-and-report checkpoints

> **USER DIRECTIVE 2026-07-03 — DESIGN FIRST, SIMULATE LATER.** User: *"we should focus on the layouts first then focus on the simulations… we did not design but we are simulating it is slowing down the process, please cancel simulations."* So: **layout/geometry iteration proceeds on GEOMETRY evidence alone** (area conservation, sliver-count, corridor connectivity, matplotlib eyeball, pure-python unit tests). **No EnergyPlus gate blocks a geometry change** while the design is still being iterated. The E+ correctness check is not abandoned — it is DEFERRED to a single validation pass once the layout design is settled, and when it runs it must be a **fast geometry-validity check** (IDF build + design-day / input-processing), NOT full annual runs (annual runs were overkill for a crash/extrusion check — manager-acknowledged 2026-07-03). T3's annual smoke already PASSED (kept as evidence); do not re-run per-iteration. **CP-3 cluster LIVE_SMOKE stays user-gated and deferred.**

- **CP-1 (after T1+T2+T3):** geometry clean on synthetics AND E+ 0-Fatal/0-Severe. **Manager decides Approach A vs B vs C here** from the evidence. This is the make-or-break gate — if E+ Fatals and no option clears it, the fix is HELD and the figures stay honest-degrade rather than ship broken geometry.
- **CP-2 (after T4+T5):** regression clean + figures regenerated. Manager eyeballs all 3 grids. Ship the figures.
- **CP-3 (T6, user-gated + DEFERRED per the directive above):** cluster LIVE_SMOKE for production-apartment promotion confidence — held until the layout design is signed off.

---

## 9. Verification (end-to-end)
1. `py -3 -m pytest tests/test_layout_generator.py tests/test_zoning.py tests/test_surfaces.py tests/test_step3_orchestrator.py -q`
2. E+ 23.1 synthetic smoke on L/U/T/O/cross MidriseApartment (prod-loads harness) → 0 Fatal / 0 Severe.
3. `py -3 scripts/plot_layout_grid.py` → 3 grids, manager eyeball.
4. (user-gated) `sbatch` cluster LIVE_SMOKE on real non-rect apartments.

---

## 10. Progress log
*(Append one entry per completed task: `#### TX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes. Sonnet appends; manager audits + records CP decisions.)*

#### T1 — Approach A local prototype + cleanliness proof — completed 2026-07-03
- **Artifacts:** `openubem/geometry/layoutGenerator.py` — `_pack_connected_spine` rewritten corridor-first (§5): corridor = `_connect_centerlines(...).buffer(c/2, cap_style=flat, join_style=mitre) ∩ aligned`, emitted as ONE zone per connected `_polys()` piece (kills D2); rooms = per-wing `wing.difference(corridor)`, each connected part bay-subdivided along its OWN long axis by the new helper `_subdivide_room_region` (kills D1). Removed now-dead `_spine_cut_values` / `_dedupe` / `_grid_cut` (the old full-span-grid + point-tag engine). Diagnostic harness `scratchpad/t1_cleanzoning_prototype.py`.
- **Deviations:** none from §5. Reused the mandated helpers (`_wings_in_frame`, `_wing_centerline`, `_connect_centerlines`, `_long_edge_angle`, `_clean`, `_is_degenerate_cell`); added two small internal helpers (`_polys` MultiPolygon flattener, `_subdivide_room_region` per-region bay cut mirroring `plot_layout_grid.py:_zone_room_segments`). Kept the degrade net intact (per-cell `_is_degenerate_cell` drop + `generate_layout` 1%-area fallback + `force_complex` unchanged).
- **Test status:** T1 cleanliness table (floor-0), `sliver` = unit whose OBB short side `< c+0.3` (c=1.68 → 1.98 m):

  | archetype | shape | corridor_zones | connected_pieces | units | slivers | area_drift% | min_zone_area |
  |---|---|---|---|---|---|---|---|
  | MidriseApartment | L | 1 | 1 | 11 | 0 | +0.000000 | 44.36 |
  | MidriseApartment | U | 2 | 2 | 15 | 0 | +0.000000 | 34.37 |
  | MidriseApartment | T | 1 | 1 | 13 | 0 | +0.000000 | 51.60 |
  | MidriseApartment | O | 3 | 3 | 25 | 0 | +0.000000 | 33.60 |
  | MidriseApartment | cross | 2 | 2 | 12 | 0 | +0.000000 | 26.88 |
  | SmallHotel(force_complex) | L | 1 | 1 | 36 | 0 | -0.000000 | 21.68 |
  | SmallHotel(force_complex) | U | 2 | 2 | 52 | 0 | +0.000000 | 16.74 |
  | SmallHotel(force_complex) | T | 1 | 1 | 37 | 0 | +0.000000 | 19.07 |
  | SmallHotel(force_complex) | O | 3 | 3 | 72 | 0 | +0.000000 | 21.68 |
  | SmallHotel(force_complex) | cross | 2 | 2 | 37 | 0 | +0.000000 | 20.34 |

  Rotated-L(30°) sanity: MidriseApartment 1 corridor / 1 piece / 11 units / 0 slivers / +0.000000% drift.
- **Notes:** Acceptance MET on all counts — 0 slivers everywhere; corridor `connected_pieces == corridor_zone_count` (each emitted corridor zone is already its own connected piece, no stub pair sharing one zone); pieces ≤ (disjoint-wing/2 + 1) bound; area drift machine-precision; every zone ≥ MIN_ZONE_AREA_M2 (2.0). Corridor-piece count per shape reflects true footprint topology: L/T single spine = 1; U = 2 (two parallel arms bridged only through the base, which the flat-buffer intersection separates); O = 3; cross = 2.

#### T2 — Unit-test the geometry — completed 2026-07-03
- **Artifacts:** `tests/test_layout_generator.py` — new `TestConnectedCorridorSpine` (20 parametrized tests over L/U/T/O/cross): (a) `test_no_unit_slivers` no unit short side `< c+0.3`; (b) `test_corridor_cells_union_connected` corridor zones dissolve to exactly `len(corridors)` connected pieces (no accidental merge/split); (c) `test_area_conserved` `<1e-4` rel; (d) `test_no_accidental_degrade` MidriseApartment returns non-empty on clean synthetics. Added `_CROSS()` + `_short_side()` test helpers.
- **Deviations:** one pre-existing test adjusted — `TestWingDecomposition.test_no_degenerate_edges` vertex cap. Old cap was `≤6` verts/zone (tuned for the retired full-span-grid rectangles). Approach A emits the corridor as ONE multi-arm turning polygon (8–11 verts by design on L/T/cross/O), so the cap is now `20` for Corridor zones and `10` for unit cells (a wing-corner unit whose bay slice partially overlaps a corridor notch is a valid 8-vert polygon — manager-verified short side 13.3 m ≫ 1.98 m, area 133 m², not a sliver). The load-bearing anti-sliver assertion `min(edges) > 0.05 m` is UNCHANGED and still green. Manager audited + accepted this widening.
- **Test status:** `pytest tests/test_layout_generator.py -q` → **94 passed**. Adjacent sanity (not the full T4 suite): `pytest tests/test_zoning.py tests/test_surfaces.py tests/test_step3_orchestrator.py -q` → **83 passed**. Strict donut `1e-5` area test (`TestDonutSplitter` / `test_full_layout_hole_free_and_conserved`) still green.
- **Notes:** no `.py` under `docs/`; only `openubem/geometry/layoutGenerator.py` (T1) + `tests/test_layout_generator.py` (T2) touched.

#### T3 — E+ 0-Fatal/0-Severe synthetic smoke (THE GATE) — completed 2026-07-03
- **Artifacts:** harness `scratchpad/t3_cleanzoning_eplus_smoke.py` (production dispatch: `run_step3(resolution_mode="zone")` → room_layout, α-normalized loads + infiltration + WWR 0.30 fenestration + HVAC/DHW/cooking/refrigeration; Chicago TMY3 EPW; `run_neighbourhood(n_jobs=1)` local, one building at a time). Per-shape work dirs + `scratchpad/t3_cleanzoning_work/t3_summary.csv`.
- **Deviations:** none — mirrors the T13a prod-loads harness pattern per the plan.
- **Test status:** **5/5 PASS — 0 Fatal / 0 Severe on every shape.** Ran E+ 23.1 locally, single-building.
- **Notes — per-shape Fatal/Severe counts + `.end` authoritative line:**

  | shape | zoning_strategy | num_zones | status | n_severe | n_fatal | eplusout.end |
  |---|---|---|---|---|---|---|
  | L | room_layout | 36 | success | 0 | 0 | `Completed Successfully-- 2128 Warning; 0 Severe Errors` |
  | U | room_layout | 51 | success | 0 | 0 | `Completed Successfully-- 2363 Warning; 0 Severe Errors` |
  | T | room_layout | 42 | success | 0 | 0 | `Completed Successfully-- 4276 Warning; 0 Severe Errors` |
  | O | room_layout | 84 | success | 0 | 0 | `Completed Successfully-- 10418 Warning; 0 Severe Errors` |
  | cross | room_layout | 42 | success | 0 | 0 | `Completed Successfully-- 5219 Warning; 0 Severe Errors` |

  `grep "**  Fatal  **"` and `grep "**  Severe  **"` on all 5 `eplusout.err` = 0 lines each. No shape rerouted/degraded — all kept `zoning_strategy=room_layout`. §3a extrusion-T-junction risk did NOT materialize: the corridor-first geometry is extrusion-safe. Warnings are benign (interior corridor cells: zero exterior-wall infiltration / zero heating design load), same class as the T13a-accepted apartment path.

> **CP-1 — PASS 2026-07-03 (manager greenlight, Approach A CONFIRMED).** Manager independently verified T1 clean geometry, accepted the T2 vertex-cap widening (min-edge anti-sliver assertion preserved), and verified the T3 summary (all 5 shapes room_layout, 0 Severe / 0 Fatal). Approach A adopted; Options B/C not needed. Proceed to figure regeneration (T5) per user request; full T4 regression + T6 cluster remain gated.
