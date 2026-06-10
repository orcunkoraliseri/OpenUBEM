# INVESTIGATION — Steps 1–3 Implementation Audit

> **Date:** 2026-06-09 • **Auditor:** Manager session (3 parallel deep-read audits + live test run)
> **Scope:** Step 1 (`acquisition/`), Step 2 (`semantic/`), Step 3 (`geometry/` + `idf/`) vs their DESIGN + PLAN docs.
> **Rule followed:** nothing was changed — warnings only, each with a proposed alternative.

---

## Verdict at a glance

| Step | Plan conformance | Real-world readiness | Biggest risk |
|---|---|---|---|
| **1 — OSM ingest** | ~80–85% | ⚠️ Two live-data crash paths | Dirty real OSM tags kill the run |
| **2 — Classifier** | ~90% (best of the three) | ⚠️ Confidence tiers skewed | HIGH confidence unreachable for the most common OSM pattern |
| **3 — IDF generation** | ~85% structural, **~50% physical** | 🔴 Every IDF would fatal in EnergyPlus | Models pass CI but are un-runnable and physically wrong |
| **Test suite (now)** | — | 🔴 RED: 15 failed, 217 passed, 2 skipped, 1 error | Environment drifted (eppy 0.5.63 → 0.5.69, pytest-mock missing) |

**The recurring disease** (already in project memory as "synthetic-test blind spots"): every step's CI is green-able while the live path is broken. The tests check the *shape* of the output, not whether it *works*. Like a restaurant inspection that checks the menu is printed correctly but never tastes the food.

> **✅ ADDENDUM — 2026-06-09, post-remediation.** Remediation Groups A–E (`REMEDIATION_prompts-audit-fixes.md`, rulings R1–R7 user-approved) were executed by fresh executor sessions the same day. The suite is now **GREEN: 265 passed, 2 skipped, 0 failed, 0 errors** (manager-verified). Every warning below now carries a **✅ FIXED** or **⏳ STILL OPEN** note; the original audit text is preserved unchanged as the snapshot it was.

---

## STEP 1 — OSM ingest (`openubem/acquisition/osm_fetcher.py`)

### 🔴 W1.1 — `building:levels="2.5"` crashes the entire run
**Analogy:** a subway turnstile that jams the whole station when one person inserts a half-fare ticket.
`astype("Int64")` on a float Series containing 2.5 raises `TypeError` (`osm_fetcher.py:210`, same landmine at `:240-243`). Half-storeys are common in real OSM; one such tag kills all N buildings. The DESIGN itself prescribes the crashing form (Step-1 DESIGN line 88), conflicting with its own flag-don't-drop policy (line 14).
**Proposed fix:** `.round().astype("Int64")` (or coerce non-integral to NA + flag). Needs a one-line DESIGN ruling since the spec literally specifies the crashing cast.

> **✅ FIXED — D1 (ruling R4):** the turnstile now rounds a half-fare ticket to the nearest whole fare and waves the passenger through — `"2.5"` becomes 2 floors, the row survives, nothing jams. Applied to both `levels` and `underground`; a regression test feeds `"2.5"` in and asserts the building lives.

### 🔴 W1.2 — `osm_id` loses the `way/` prefix; IDs can collide
**Analogy:** filing patients by first name only — two different "John"s, one record explodes.
The `if "osmid" in gdf.columns` branch always fires for osmnx 1.9 output, so the branch that builds `"way/12345"` (`osm_fetcher.py:176`) is dead code. A way and a node sharing numeric id 12345 both emit `"12345"` → the uniqueness validator hard-fails on real extracts. DESIGN line 95 explicitly requires the `"way/..."` form.
**Proposed fix:** reorder the branches — check `element_type` + `osmid` co-presence first, bare `osmid` last.

> **✅ FIXED — D2:** patients are now filed by full name — every id is `"way/12345"` or `"node/12345"`, so the two Johns can never share a folder. Tests pin the format and the way/node collision case.

### 🔴 W1.3 — The audit log is always an empty file (0 bytes, verified)
**Analogy:** a flight recorder that gets switched on after the plane lands.
The FileHandler is attached inside `_serialize` (`osm_fetcher.py:538-541`) — *after* all cleaner INFO records were already emitted. DESIGN line 216 requires per-step drop counts in this artifact. The PLAN itself specified this broken scoping (a plan bug, not executor drift). Same bug repeats in Step 2's log.
**Proposed fix:** buffer step records (e.g. `logging.handlers.MemoryHandler` or a dict collected during cleaning) and flush them in `_serialize`.

> **✅ FIXED — D4:** the recorder now takes notes *during* the flight and files them after landing — the cleaner collects its per-step counts as it works and `_serialize` writes them straight to the file. The log finally has content, and the test now checks for the content, not just that a (possibly empty) box exists. Same fix applied to Step 2's log.

### 🔴 W1.4 — Dedup misses "contained" duplicates (IoU > 0.95 survives)
**Analogy:** the security guard checks people bumping shoulders, but not someone hiding inside another's coat.
DE-9IM `predicate="overlaps"` (`osm_fetcher.py:307`, per DESIGN line 128) is false when one polygon fully contains the other — the classic re-digitised-smaller-inside-larger duplicate. Verified: a contained pair with IoU = 0.96 survives, violating the §5.1 acceptance metric (DESIGN line 237). Worse, the test fixture was bent to dodge this instead of fixing the predicate.
**Proposed fix:** `predicate="intersects"` for candidate generation (the IoU > 0.95 filter already protects party-wall neighbours). Requires a DESIGN line 128 revision — the spec conflicts with its own acceptance metric.

> **✅ FIXED — D3 (ruling R5):** the guard now stops everyone who *touches*, coats included — fully-contained near-copies get merged, while legitimate wall-sharing neighbours (who only touch at the edge, IoU ≈ 0) still walk through. New tests cover both the contained pair and the party-wall guard.

### 🟡 Medium warnings (terse)
- **W1.5** Warning `bbox` payload emits UTM output bounds `(minx,miny,maxx,maxy)`, not the WGS84 `(n,s,e,w)` the DESIGN specifies (`osm_fetcher.py:69`). → Pass the caller's bbox through.
  > **✅ FIXED — D5:** the warning now reports the real map coordinates of the area you asked for, not metric coordinates of the area it produced.
- **W1.6** `surplus_tags` duplicates all 11 already-mapped source tags into the JSON; `_OSM_RENAME_SOURCES` was built exactly to prevent this and is never referenced (`:162-167`). → Exclude `canonical_out | _OSM_RENAME_SOURCES`.
  > **✅ FIXED — D6:** the suitcase no longer carries copies of clothes already hanging in the wardrobe — mapped tags are skipped, only genuinely surplus tags travel.
- **W1.7** §5.1 vertex-count metric (95th pct ≤ 120) is implemented nowhere — a plan-level omission. → Add a counter + warning, or explicitly defer to Stage 3 with manager sign-off.
  > **✅ FIXED — D8:** a tripwire now counts vertices after cleaning and shouts a warning when the 95th percentile hits 80, so Stage 3's simplifier gets its signal. Nothing is dropped.
- **W1.8** MultiPolygon explode is a per-row `iterrows` copy of a ~150-column frame instead of vectorized `gdf.explode()` (`:352-378`), and the full raw width is dragged through all 7 cleaning steps before trimming to 23 columns at the end. **Analogy:** moving house room-by-room with everything still in the cupboards, then throwing 85% of it away at the new address. → Trim columns right after `_flatten_tags`; use vectorized `explode(index_parts=True)`.
  > **⏳ STILL OPEN (deliberately):** efficiency-only, no wrong answers produced — deferred so the remediation stayed focused on correctness. Worth a small task before city-scale runs.
- **W1.9** No end-to-end `ingest_buildings` test exists — every test calls internal helpers. One mocked-osmnx end-to-end test would have caught W1.2 and W1.3.
  > **✅ FIXED — D7:** one test now drives the whole assembly line on mocked data — raw tags in, 23-column schema out, log non-empty, ids `way/`-prefixed. This single test would have caught W1.2 *and* W1.3.

### ✅ What's solid
Schema, parsers, provenance/flag vocabularies, cleaner ordering, and **all five Gemini-audit remediation items (R1–R3c) verified landed** in the current code.

---

## STEP 2 — Archetype classifier (`openubem/semantic/building_classifier.py`)

### 🟠 W2.1 — HIGH confidence is unreachable for building-tag-only rows
**Analogy:** an exam where the top grade can never be awarded to the most common kind of student, because of the order the rules are read in.
DESIGN §3D rows HIGH(b) and MEDIUM(d) genuinely overlap; the code checks MEDIUM(d) first (`building_classifier.py:343-345`), so `building=apartments` + observed 12 levels returns MEDIUM (runtime-verified). Building-tag-only rows are the single most common OSM pattern → every downstream confidence distribution is skewed low. Per the plan's own hard rules this was a STOP-and-ask case that got silently resolved; a test even pins the disputed behavior with an apologetic comment (`test_building_classifier.py:336-342`).
**Proposed fix:** manager ruling on the §3D conflict; if HIGH(b) wins, add an explicit HIGH branch for rules 1a/1b/2a/2b with observed building_tag + observed levels, checked *before* MEDIUM(d).

> **✅ FIXED — E1 (ruling R6):** the grading order was flipped — the top grade is read first, so the most common student can finally earn it. A clearly-tagged building with an observed floor count now gets HIGH; the same building with a *guessed* floor count still gets MEDIUM (both pinned by tests, apologetic comment deleted).

### 🟠 W2.2 — Rule 15 (dominant-tag mixed routing) is dead code
**Analogy:** a door whose key was designed one millimetre too big for its own lock.
Mixed-use arises only when two tags *disagree*, which always yields dominance score 0.5 — but the threshold is 0.60 (`building_classifier.py:275` vs `:108-111`), so rule 15 never fires end-to-end. Its unit tests inject an unproducible state (mixed + score 1.0), giving false assurance.
**Proposed fix:** lower the default threshold to ≤ 0.5, or weight function-tag dominance above 0.5 in the score formula, or document rule 15 as Phase-2-only. Needs a DESIGN §11/OQ-1 ruling.

> **⏳ STILL OPEN — parked (erratum E4):** re-cutting the key changes how mixed-use buildings get classified, which is a modeling-philosophy decision, not a bug fix. Awaiting the user's ruling; the real-fixture distributions from E5 (below) are the evidence to decide with.

### 🟡 Medium warnings (terse)
- **W2.3** `02_buildings_classified.log` is always 0 bytes — same flight-recorder bug as W1.3 (`:580-597`); `TestSerialize` only asserts the file *exists*. → Emit summary lines (rule fire counts, tier counts, FALLBACK osm_ids) while the handler is attached.
  > **✅ FIXED — D4:** same flight-recorder repair as Step 1 — rule fire counts, tier counts, and FALLBACK osm_ids are now collected during classification and written at serialize time; the test asserts content.
- **W2.4** Zero exact-boundary tests. **Analogy:** testing a speed camera at 80 and 120 km/h but never at the 100 limit. The DESIGN pins inclusive/exclusive edges at 500/4000/5000 m² and 4/9/20/40 levels; tests use 300/600/6000 m² and 2/5/12/25/42 levels. An `>=`→`>` regression would pass green. (Code itself is boundary-correct on inspection.) → One parametrized 7-case boundary test.
  > **✅ FIXED — E2:** the camera is now tested at exactly the speed limit — all 7 boundary values (500/4000/5000 m², 4/9/20/40 levels) pinned by one parametrized test, each expectation cited to its DESIGN line.
- **W2.5** None of the DESIGN §5.1 acceptance gates (HIGH+MEDIUM ≥ 70%, LOW caps, TallBuilding rate, distribution envelope) have a test counterpart. Now partially actionable since `boston_downtown_500m.gpkg` / `chicago_loop_500m.gpkg` exist (untracked). → Commit the fixtures, add threshold tests.
  > **⏳ PARTIALLY DONE — E5 (measurement only):** the food has now been tasted, but the pass mark isn't enforced yet. First real-data run: Boston 483 buildings → HIGH+MEDIUM 41.0%, FALLBACK 57.6%; Chicago 399 → HIGH+MEDIUM 65.4%, FALLBACK 33.8%. Both below the ≥70% gate — driven by generic `building=yes` sparsity, which is exactly the rule-15 / Step-2.5 decision pending above. Gate tests stay parked until that ruling.
- **W2.6** Uncommitted DESIGN edit contains a factual error in "sealed" OQ-7 text: Residential sector listed as "MidriseApartment, **MultifamilyHome**" — but MultifamilyHome is not in the 30-archetype vocabulary (the JSON says HighriseApartment). Same error in `PLAN_step-2.5...md:78`. → Fix both names **before committing** the DESIGN modification.
  > **⏳ STILL OPEN — yours:** DESIGN docs are generated in your external LLM and are read-only here; correct the name at the source before committing the modified DESIGN file.
- **W2.7** Input validator checks column names/order but not dtypes, despite DESIGN §3F line 278 requiring both (`:401-407`).
  > **✅ FIXED — E3:** the doorman now checks the ID *type*, not just the name on the list — load-bearing columns (`levels`, `footprint_area_m2`, `height_m`) are dtype-validated with a clear error naming the offender.

### ⚠️ W2.8 — Step 2.5 labelled-fixture: the answer key was written for a different exam
The 50 pre-filled labels (paused at your review step) conflict with the classifier's contract two ways: (1) 19/50 rows are generic `building=yes` but labelled SmallOffice/MediumOffice etc. — the classifier will correctly emit OpenUBEMUnknown for these; (2) office tiers were suggested using *total floor area* (footprint × levels) while DESIGN §3C uses *footprint only*. If the labels stand as-is, the accuracy gate will CI-fail in a way that looks like a classifier bug but is actually a labelling-protocol mismatch.
**Proposed fix:** before reviewing labels row-by-row, decide the labelling protocol (footprint-proxy semantics, matching the classifier's contract) and re-derive the suggested labels under it.

> **⏳ STILL OPEN — yours:** decide which exam the answer key grades (what-the-tags-say vs what-the-building-really-is) before resuming the label review. The E5 distributions above are the supporting evidence.

### ✅ What's solid
17-rule order, all 55 use-class tokens, the 30-archetype JSON, TallBuilding exemptions, `_impute_levels`, override merge, no-input-mutation guarantee — all verified verbatim against the DESIGN. Executor deviations were honestly logged. Best-executed step of the three.

---

## STEP 3 — IDF generation (`openubem/geometry/`, `openubem/idf/`)

The structure matches the plan almost verbatim (all 16 tasks executed and logged), but the **physics is disconnected from the geometry**. Four HIGH findings mean today's IDFs would fatal in EnergyPlus 23.1, and after the one-line fatal fixes they would still simulate the wrong building.

### 🔴 W3.1 — No `Building` object anywhere → every IDF is EnergyPlus-fatal
**Analogy:** a fully assembled car with no chassis number — it cannot even enter the inspection line.
`Building` is a required EnergyPlus object (it also carries North Axis). It is absent from all four templates and never emitted by code (grep-verified). The DESIGN's own template table (Step-3 DESIGN lines 204–214) omits it too — a spec gap the §5.1 dry-run gate would have caught, but that gate has never run.
**Proposed fix:** add `Building` (North Axis 0, FullExterior solar distribution) to the four templates; record as a DESIGN erratum.

> **✅ FIXED — B1 (ruling R1):** the chassis number is stamped on — all four templates now carry a `Building` object (North Axis 0, Terrain City, FullExterior), and a test asserts exactly one exists per built IDF. The car can enter inspection.

### 🔴 W3.2 — Archetype U-values/SHGC never reach any surface
**Analogy:** you paid for custom triple-glazing and premium insulation; the builder installed the showroom defaults and left your order in the garage.
`assign_constructions` creates `Roof/Wall/Floor/Window_Construction` objects, then `idf.set_default_constructions()` (`builder.py:119-120`) assigns every surface geomeppy's generic `Project Wall`/`DefaultMaterial` constructions. The archetype's `u_roof/u_wall/u_floor/u_window/shgc` columns have **zero simulation effect** (W3.2). No test checks surface→construction wiring.
**Proposed fix:** after (or instead of) `set_default_constructions()`, rewrite each surface's `Construction_Name` by `Surface_Type`; add a test asserting a wall references `Wall_Construction`.

> **✅ FIXED — B3:** the custom insulation is out of the garage and in the walls — after the builder lays the showroom defaults, every surface is re-pointed to the archetype constructions (wall→Wall, roof→Roof, floor/ceiling→Floor). A test asserts no surface still references `Project Wall`, so the U-values you paid for finally heat and cool the model.

### 🔴 W3.3 — Every window has a blank construction → EnergyPlus fatal
`set_wwr` is called without `construction=` (`builder.py:120`), so every `FenestrationSurface:Detailed` gets `Construction_Name=""`.
**Proposed fix:** `idf.set_wwr(wwr=..., construction="Window_Construction", force=True)`. One line.

> **✅ FIXED — B2:** every window now has its glazing spec on the order form — the one-line fix landed, and a test asserts every window references `Window_Construction`.

### 🔴 W3.4 — Multi-floor buildings simulate as N detached bungalows
**Analogy:** a 6-storey tower modeled as six bungalows filed in a drawer — each one believing it sits on soil and has its roof open to the sky.
Every storey block is extruded at z=0 (`surfaces.py:60-83`); geomeppy's `intersect_match` finds no coincident surfaces between identical stacked blocks, so every storey gets a `ground`-BC floor and a SunExposed roof. Setting `Z_Origin` afterwards (`builder.py:232-237`) moves the geometry but the wrong boundary conditions persist. Heating/cooling loads for anything > 1 storey will be badly wrong.
**Proposed fix:** build per-floor blocks at true z-coordinates so `intersect_match` sees real floor/ceiling adjacency (the CP2 deviation note acknowledged the issue; the Z_Origin patch does not repair BCs).

> **✅ FIXED — C1 (ruling R2):** the six bungalows became one tower — each building is now a single extrusion with `num_stories=N`, storeys stacked at true heights. Only the bottom floor touches soil, only the top sees sky, and storeys exchange heat through real shared floor/ceiling pairs (a vertex-matching helper was added because geomeppy's own matcher misses rotated-but-identical surfaces). A 3-storey test pins all three facts.

### 🔴 W3.5 — Perimeter+core zoning double-counts floor area; the core is open to the sky
**Analogy:** counting the donut *and* the hole both as donut — then putting windows on the hole.
The perimeter zone polygon drops its interior hole (`zoning.py:92` takes only `exterior.coords`), so the perimeter block overlaps the full core volume: floor areas double-count (~1.3–1.6× inflated W/m² loads), no perim↔core party wall ever exists (the adiabatic flip is dead code), and core walls are `outdoors` + windowed. The DESIGN §3B "exterior-ring zone" schema is itself physically unsound — this is a spec defect, not just a code bug.
**Proposed fix:** split the perimeter ring into 4 quadrant polygons (ASHRAE Appendix-G style) or use geomeppy's `zoning="core/perim"`; revise DESIGN §3B accordingly.

> **✅ FIXED — C2 (ruling R7, issued at the checkpoint):** the donut and the hole are now counted separately — geomeppy's native core/perimeter split carves the footprint into perimeter wedges plus a core that sum to the footprint within 0.002%, with real interior walls between them that exchange heat (Surface-matched, which is physically *better* than the adiabatic wall the old DESIGN asked for). Zones renamed to the `{osm_id}_F{i}_…` convention; degenerate-core buildings fall back to per-floor zoning with a manifest note.

### 🔴 W3.6 — Suite is red: eppy 0.5.69 renamed a field
`OUTPUT:METER:METERFILEONLY` is set via `Name=` but the installed eppy 0.5.69 IDD calls it `Key_Name` (`outputs.py:31-35`) → 15 test failures (all of `test_outputs.py` + all of `test_step3_orchestrator.py`). The environment drifted since CP3 (eppy 0.5.63 → 0.5.69, Python 3.14.3); the T13 deviation note is now inverted.
**Proposed fix:** set the field defensively (try `Key_Name`, fall back to `Name`) **and** pin eppy exactly in `pyproject.toml`.

> **✅ FIXED — A2:** the field is now asked for by both names — try the new one, fall back to the old — so the code works under both eppy versions. All 15 failures cleared; environment baseline recorded (Python 3.14.3, eppy 0.5.69, geomeppy 0.12.2).

### 🟡 Medium warnings (terse)
- **W3.7** All EnergyPlus-23.1-specific content is validated against eppy's bundled **v8.0.0** IDD; 11 of 13 IdealLoads fields are silently dropped by a `try/except pass` (`hvac.py:39-43`). **Analogy:** mailing a modern letter through a 1920s censor who silently deletes every word he doesn't recognise. Also no `SizingPeriod:DesignDay` despite autosize → severe at runtime. → Add a LIVE_SMOKE task with a real 23.1 IDD + EnergyPlus design-day dry-run before declaring Step 3 closed.
  > **⏳ STILL OPEN — parked:** the censor is still on duty. This is the LIVE_SMOKE gate (real 23.1 IDD + an actual EnergyPlus design-day run) — the recommended next remediation block before Stage 4 planning.
- **W3.8** Zoning rule keyed on post-simplification `poly_local.area` instead of the contract column `footprint_area_m2` (`builder.py:222-223`) — hull/bbox tiers can flip the zoning rule. → Read the column, fall back to geometry area.
  > **✅ FIXED — B5:** zoning now reads the official measurement from the paperwork, not the re-traced sketch — `footprint_area_m2` first, geometry area only when the column is missing.
- **W3.9** Zones whose extrusion failed twice still receive People/Lights/HVAC objects referencing a nonexistent Zone (`surfaces.py:77-79` + `builder.py:243`) → E+ severe. → Mark `z["extruded"]=True` on success and filter on that.
  > **✅ FIXED — B4:** lights and thermostats are only installed in rooms that were actually built — zones carry an `extruded` flag, and loads/HVAC/`num_zones` filter on it.
- **W3.10** Ground-floor adiabatic rule is dead code: geomeppy assigns z=0 floors `ground`, the flip matches `outdoors` (`surfaces.py:110`); its test passes only by manually forcing floors to Outdoors first. → Decide ground vs adiabatic, then de-rig the test.
  > **✅ FIXED — C3 (ruling R3):** the rule now matches reality — ground floors touch soil (`ground` BC), the dead flip is deleted, and the rigged test was un-rigged to assert real pipeline output.
- **W3.11** Synthetic fixture has 36 of the 57 contract columns; works only because code never reads the missing ones. → Complete the fixture so contract regressions surface.
  > **⏳ STILL OPEN:** small task; best bundled with the Module 04/05 bridge work (see X1), when the missing columns gain real producers.
- **W3.12** bbox-fallback never lands in manifest `data_quality_flag` (`builder.py:263-275`); missing-EPW silently leaves Site:Location at (0,0); `compute_form_factor` implemented but never called; neighbour bounding boxes recomputed per target in context shading.
  > **⏳ STILL OPEN:** four small polish items, none load-bearing; candidates for a future cleanup task. (Note: the core/perim fallback from C2 *does* record itself in the manifest now.)

### ✅ What's solid
Module layout, 4-tier simplification, zoning rule table, geomeppy call ordering, output-variable set, manifest schema — all near-verbatim to the DESIGN. The executor logged its deviations honestly, including the stacking problem (CP2 deviation #3).

---

## CROSS-STEP SEAMS

### 🟠 X1 — The Step 2 → Step 3 bridge does not exist yet
Step 2 emits 26 columns (23 in + `archetype_id`, `archetype_confidence`, `archetype_source`). Step 3 hard-requires 15 columns Step 2 never produces (`u_roof_w_m2k`, `wwr`, `infiltration_m3_s_m2`, `lighting_w_m2`, …) — those come from Modules 04/05/06 (envelope/loads/schedules lookup), which are designed but not built.
**Analogy:** track has been laid on both banks of the river; the bridge is on the blueprint but not in the water. Nothing connects today except the synthetic fixture.
**Not an error** — but Step 3 was built and "tested" entirely against a hand-made fixture of its own input. When Module 04/05 land, run an integration test that pipes real Step-2 output through them into Step 3 before trusting any of the green checkmarks.

> **⏳ STILL OPEN — by design:** the bridge (Modules 04/05/06) is the next construction project, not a defect in what exists. Keep the integration-test requirement when it lands.

### 🟠 X2 — `osm_id` format drift will poison every downstream join
Stages 4–5 join everything on `osm_id`. DESIGN says `"way/12345"`; Step 1 actually emits `"12345"` (W1.2). Step 3 names IDFs `<osm_id>.idf`. Fix W1.2 *before* Stage 4 exists, or the format will fossilize.

> **✅ FIXED — via D2:** resolved before it could fossilize — all ids now carry the `way/`/`node/` prefix end to end, matching the DESIGN, with the end-to-end test (D7) pinning the format.

### 🟠 X3 — Both serialization log artifacts are empty; nothing would notice
Steps 1 and 2 share the identical flight-recorder bug (W1.3/W2.3) and the identical vacuous test (`assert path.exists()`). When fixing, fix both and assert on *content*.

> **✅ FIXED — via D4:** both recorders repaired in the same change, both tests upgraded from "the box exists" to "the box contains the flight notes".

---

## DESIGN ERRATA — for regeneration in your other LLM

Since the DESIGN/OVERVIEW docs are generated externally and are read-only here, these spec defects need fixing **at the source**:

| # | Doc | Defect |
|---|---|---|
| E1 | Step-1 DESIGN line 88 | `astype("Int64")` cast crashes on fractional `building:levels`; contradicts flag-don't-drop (line 14) |
| E2 | Step-1 DESIGN line 128 vs line 237 | `predicate='overlaps'` cannot satisfy the IoU > 0.95 acceptance metric (misses contained duplicates) |
| E3 | Step-2 DESIGN §3D (line ~230) | Confidence rows HIGH(b) and MEDIUM(d) overlap; precedence undefined |
| E4 | Step-2 DESIGN §11 (line ~480) | Rule-15 dominance threshold 0.60 unreachable (max producible score is 0.5) |
| E5 | Step-2 DESIGN line 529 (uncommitted edit) | "MultifamilyHome" is not in the 30-archetype vocabulary (should be HighriseApartment); also in PLAN_step-2.5 line 78 |
| E6 | Step-3 DESIGN §3D template table (lines 204–214) | Required `Building` object missing from the IDF object set |
| E7 | Step-3 DESIGN §3B (lines 113–121) | Single perimeter ring-with-hole zone is physically unsound (double-counted volume, no party wall surface possible) |
| E8 | Step-3 DESIGN §3F pseudocode (lines ~271–311) | `set_default_constructions()` overwrites the archetype constructions the same section creates |

> **Status 2026-06-09:** the *code* no longer follows the defective spec text for E1, E2, E3, E6, E7, E8 — bridged by approved rulings R4, R5, R6, R1, R7, and fix B3 respectively (recorded in `REMEDIATION_prompts-audit-fixes.md` §4). The DESIGN texts themselves still need correcting at the source so spec and code agree again. **E4 and E5 remain unaddressed in both code and doc** — they are the two parked decisions.

---

## RECOMMENDED REMEDIATION ORDER

1. **Environment + red suite** (hours): install dev extras (`pytest-mock`, `tenacity`), pin eppy, fix the `Key_Name` field → suite green again. Nothing else is auditable until this. *(✅ done — Group A)*
2. **Step 3 fatal fixes** (small): Building object (W3.1), window construction arg (W3.3), construction wiring (W3.2). Three near-one-liners that take IDFs from "won't parse" to "runs". *(✅ done — Group B)*
3. **Step 3 geometry corrections** (needs DESIGN errata E6–E8 first): stacking (W3.4), perim-core (W3.5). *(✅ done — Group C, rulings R2/R3/R7)*
4. **Step 1 live-data crashers** (small): levels cast (W1.1, needs E1 ruling), osm_id branches (W1.2). *(✅ done — Group D)*
5. **Shared logging fix + test hardening**: W1.3/W2.3, end-to-end ingest test, boundary tests, de-rigged adiabatic test. *(✅ done — Groups C/D/E)*
6. **Step 2 confidence ruling** (needs E3/E4): then re-run the distribution. *(✅ E3/R6 done — Group E; E4/rule-15 still parked)*
7. **LIVE_SMOKE gates before closing anything**: real-OSM extract through Steps 1–2; real 23.1 IDD + EnergyPlus design-day dry-run for Step 3. This is the structural cure for the recurring synthetic-blind-spot disease. *(⏳ next up — the only remaining block, together with the parked rule-15 / MultifamilyHome / Step-2.5 decisions)*

Each numbered block above is sized to become one short remediation PLAN doc (Step-1.6, Step-3.5, …) for a fresh executor session.
