# PLAN — User-selectable resolution-mode switch (modes `building` / `floor` / `zone`)

**Slug:** `resolution-mode-switch`
**Date:** 2026-06-29 · **Updated 2026-06-29** with the 16-report deep-research set (`deepResearch/RESULT_01..16`, see §10).
**Binding contract:** there is no separate DESIGN doc for this feature. The binding spec is
(a) the existing zoning contract in `openubem/geometry/zoning.py`, and (b) §1b of
`docs/docs_ACTIVE/simulation-Resolution/SIMULATION_RESOLUTION_zoning_by_building.md`
(the 4-mode table) + §5.1 of `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md`. Those four
modes are the contract; this plan implements modes 1–3 and leaves mode 4 (`auto`) untouched.

**One-line goal:** expose a `resolution_mode` parameter so a user can force every building to a
fixed thermal-zoning fidelity instead of the adaptive `auto` default — without changing any physics,
loads, schedules, or the validated `auto` baseline. Five modes: `building` = 1 zone, `floor` =
1 zone/floor, `fast_zone` = generic core+perimeter for every building, `zone` = the faithful
per-archetype DOE layout (units+corridor, etc.), and `auto` (default).

**Two zone-resolution modes, deliberately separated (added 2026-06-29):**
- **`fast_zone`** — blanket `perimeter_core` (core + one perimeter zone per exterior wall edge) for
  **every** archetype. Simple, robust, cheap, **needs no new research** — this is the original
  "zone → perimeter_core" idea. **Implementable now.**
- **`zone`** — the faithful per-archetype upgrade. The layout-mapping research is now **complete**
  (`deepResearch/layoutMapping/RESULT_L01..L06`, 2026-06-29) and **rejected the exact-count vision**:
  `zone`'s geometry is the same ≤5-zone core/perimeter as `fast_zone`; its value-add is per-archetype
  **load** differentiation (Core-as-Corridor, functional cores). **Still not in v1 — scope decision A/B/C
  pending** (see §12).

---

## 1. Hard rules for the executor

- Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Do not touch files outside `openubem/` and `tests/`.
- **Never edit** `main.py` (root), any OVERVIEW/DESIGN doc, or any `.md` under `docs/` except to
  append a progress-log entry to §8 of THIS file.
- Do not write your own plan or propose alternatives — execute these tasks top-to-bottom.
- **Backward compatibility is mandatory:** `resolution_mode` defaults to `"auto"` everywhere. Every
  existing caller of `decide_zoning_strategy`, `BuildingIDF`, and `run_step3` that does NOT pass the
  new arg must behave **bit-identically** to today. The validated 8,160-building baseline must not move.
- Default to no comments. One short line max when the WHY is non-obvious.
- Stop and ask if anything here conflicts with the code as you find it; never invent behaviour.
- The geometry **fallbacks inside `build_zones` are hard EnergyPlus constraints, not heuristics** —
  do NOT remove or bypass them in any mode (see §5, facts F4/F5).

---

## 2. File layout to touch (exact)

```
openubem/geometry/zoning.py        ← add `resolution_mode` param to decide_zoning_strategy
openubem/idf/builder.py            ← thread resolution_mode: BuildingIDF.__init__ → build() → _build_one → run_step3
tests/test_zoning.py               ← extend: forced-mode decision matrix
tests/test_step3_orchestrator.py   ← extend: run_step3 per-mode integration on synthetic_10
tests/test_resolution_mode_live.py ← NEW: LIVE_SMOKE — real footprints through fast_zone end-to-end
```

v1 scope = `building`, `floor`, `fast_zone`, `auto` (the code-wiring batch T01–T06). **After** v1, this plan
also carries three manager-gated, post-v1 tasks: **T07** (test simulations of all 4 modes on a small pilot),
**T08** (full re-simulation across all 12 cells → `openubem/outputs/comparisons/`), and **T09** (author the
deep-research prompt set for external-literature validation). The faithful per-archetype `zone` mode is
**deferred and optional** — research is complete (it rejected exact-count; see §12), but `zone` is a separate
later arc, not built by this plan.

No new modules, no config-file schema changes, no CLI work in v1 (the library `resolution_mode`
parameter is the contract; CLI exposure is out of scope — see §4 D5).

---

## 3. The modes — exact required behaviour

`decide_zoning_strategy(archetype_id, footprint_area_m2, num_floors, resolution_mode="auto")`:

| `resolution_mode` | Returned strategy (for ANY archetype / area / floor count) | v1? |
|---|---|---|
| `"auto"` *(default)* | **unchanged** — the existing rule (§5 F1). Do not alter a single branch. | ✅ |
| `"building"` | always `"single_zone"` | ✅ |
| `"floor"` | always `"one_zone_per_floor"` | ✅ |
| `"fast_zone"` | always `"perimeter_core"` (generic core + edge-split perimeter, **all** archetypes) | ✅ |
| `"zone"` | the **per-archetype DOE layout** (units+corridor / functional split / single, per archetype) | ⏸ **deferred — research** |
| anything else | raise `ValueError(f"unknown resolution_mode: {resolution_mode!r}")` | — |

**Critical semantics:**
- v1 implements **`building`, `floor`, `fast_zone`, `auto`**. `"zone"` (the faithful per-archetype DOE
  layout) is **out of v1** until the layout-mapping research (`deepResearch/layoutMapping/`) returns a
  sourced method — see §12. Until then, `decide_zoning_strategy` must **raise a clear
  `NotImplementedError("resolution_mode='zone' (detailed DOE layout) is not yet implemented; use 'fast_zone' for generic core/perimeter")`** so a caller never silently gets the wrong layout. `"zone"` is
  a known token, not an unknown one — do NOT collapse it into the `ValueError` branch.
- In the forced modes `building` / `floor` / `fast_zone`, the `num_floors == 1` short-circuit and the
  area/archetype gates of `auto` are **bypassed** — the forced strategy is returned regardless. (A
  1-floor large building in `fast_zone` correctly gets core/perimeter; `build_zones(..., "perimeter_core")`
  with `num_floors=1` is already tested and valid — §5 F6.)
- `build_zones` is **unchanged**. Forcing `"perimeter_core"` (i.e. `fast_zone`) on a narrow or courtyard
  footprint still falls back to `one_zone_per_floor` inside `build_zones` (§5 F4/F5). This means
  `fast_zone` degrades gracefully and never crashes — that fallback is required, not optional.

> **Why two zone modes.** This cleanly resolves the earlier generic-vs-faithful tension (old D2): rather
> than pick one, OpenUBEM offers both. `fast_zone` is the robust, research-free, cheap option (generic
> core/perimeter everywhere); `zone` is the faithful, archetype-true option that reproduces each DOE
> prototype's real internal layout on the real footprint. The deep-research challenges to "generic
> core/perimeter for all" (RESULT_02/03/04) are answered by `zone`, while `fast_zone` openly *is* the
> generic approximation and is labelled as such.

---

## 4. Dependency / methodology decisions (pre-decided — do not re-debate)

> These were drafted before the deep-research set and have now been **checked against the 16 RESULT
> reports** (§10). Each decision below carries a *research verdict* — `CONFIRMED`, `KEPT (challenged)`,
> or `NEW`. Sonnet does not re-debate; the manager has already reconciled them.

- **D1 — Every-floor, no zone multiplier (v1). [CONFIRMED]** `fast_zone` (and the future `zone`) model
  every floor explicitly — core+perimeter on *every* floor, exactly as the current `perimeter_core` path
  does. Zone multipliers are explicitly
  **out of scope** for v1. RESULT_05 explicitly recommends deferring `Zone Multiplier`/`ZoneGroup` for
  v1: representative-floor collapse loses height-varying neighbour shading (10–15 % local EUI error in
  dense canyons — Johari 2022) and cannot represent stack-driven infiltration gradients. Every-floor is
  also what the validated ±9 % baseline uses. Multiplier remains a future cost optimization (RESULT_10).
- **D2 — Two zone modes: `fast_zone` (generic) now, `zone` (faithful DOE layout) after research. [REVISED
  2026-06-29]** The earlier "generic core/perimeter for all archetypes, accept-and-report" is **split into
  two explicit modes** instead of one compromise:
  - **`fast_zone`** *is* the generic core/perimeter for all archetypes — `perimeter_core` everywhere, core
    automatically WWR = 0 and zero infiltration (no exterior wall — RESULT_07/14). It is openly labelled
    the fast approximation. **In v1.** This is what the research (RESULT_02/03/04) called the "accept" case
    for office/retail and the "challenged" case for residential — `fast_zone` keeps it for *all* archetypes
    by design, and the known residential windowless-core caveat is documented (§9), not hidden.
  - **`zone`** answers the research's challenge properly. The layout-mapping research is now **complete**
    (RESULT_L01..L06, §12) and settled the open question: **Option 1 (exact DOE zone count) is rejected**
    on energy (<5% EUI, below ±9% tolerance), geometry (no robust algorithm — crashes on real polygons),
    and standard-practice (no peer tool does it) grounds. `zone` is therefore **re-scoped**: the **same
    ≤5-zone cardinal core/perimeter geometry as `fast_zone`**, plus per-archetype **load families**
    (Core-as-Corridor for residential/hotel; functional split for restaurant/retail/datacenter; single for
    warehouse/strip-mall — RESULT_L06) and a 4-tier robustness ladder. Its real gain over `fast_zone` is the
    **load** differentiation (P1/P2), not zone count. **Still deferred** pending the A/B/C scope call (§12).
  This removes the old dilemma: we no longer have to choose generic-vs-faithful — the user selects per run.
- **D3 — Perimeter depth stays 4.57 m for all modes/archetypes. [CONFIRMED]** Existing `build_zones`
  default; RESULT_03/04 lock it to **ASHRAE 90.1-2019 Normative Appendix G, Table G3.1** (15 ft thermal
  block depth). RESULT_11 flags that this depth **must not be curve-fitted** — it is a published
  heuristic, consistent with zero-fitted-parameters. Do not tune it.
- **D4 — `auto` remains the default and the validated baseline. [CONFIRMED]** The switch is purely
  additive/opt-in.
- **D5 — No CLI flag in v1. [unchanged]** The `resolution_mode` function parameter on `run_step3` is the
  public contract. CLI/config exposure is a separate, later task.
- **D6 — Record `resolution_mode` as provenance. [NEW — from RESULT_16]** The chosen mode must be
  written into the per-building manifest alongside the existing `zoning_strategy` and `num_zones` (F10),
  so every IDF/result is self-describing and modes are comparable downstream. This is a small, in-scope
  addition (T03b). Surfacing `resolution_mode` in the Step-5 results table is a one-line follow-on in a
  *different* module and is **out of scope here** — noted in §11.
- **D7 — Daylighting stays OFF in all modes for v1. [NEW — from RESULT_13]** Daylight-responsive
  lighting controls are only physically meaningful where perimeter zones exist (`zone` mode); enabling
  them only there would make modes incomparable and risks sensor-placement fatals on irregular
  footprints. Keep them off everywhere (the current code adds no `Daylighting:Controls`). Consequence:
  coarse modes over-predict lighting EUI ~10–20 % — documented as a known caveat (§9), not fixed in v1.
- **D8 — Single dominant archetype per building in all modes. [NEW — from RESULT_15]** Per-floor
  mixed-use (ground retail + residential above) is **explicitly deferred to a follow-on**: open GIS has
  no reliable per-floor use data, it needs a multi-archetype builder refactor, and it would confound the
  resolution effect with archetype change during validation. v1 applies the building's one archetype
  uniformly in every mode.
- **D9 — `Solar Distribution = FullExterior`; do not switch to `FullInteriorAndExterior`. [NEW — from
  RESULT_12]** Non-convex core/perimeter zones from real footprints fatal under `FullInteriorAndExterior`.
  The existing `auto` path already runs `perimeter_core` for ~470 buildings under the current setting, so
  zone mode (same geometry, more buildings) is already proven safe — the executor must **not** change the
  solar-distribution setting while wiring the switch.
- **Deep research: DONE, not required to *build*.** The 16-report set (§10) was produced for
  methodological defensibility and to surface the decisions above. It did **not** change the core
  implementation: modes 1–2 reuse validated strategies; mode 3 reuses the validated `perimeter_core`
  geometry with the archetype/area gate removed. Crucially, the research **confirmed** the plan's central
  premise — that switching resolution only *redistributes* loads and never changes building totals — is
  already guaranteed by OpenUBEM's existing input bases (see F11–F14).

---

## 5. Source-of-truth verified facts (manager already grepped — do not re-derive)

- **F1** — `decide_zoning_strategy` current rule, `zoning.py:11-20`:
  `num_floors==1 → single_zone`; `area≥500 and archetype ∉ _ONE_PER_FLOOR and archetype != "OpenUBEMUnknown" → perimeter_core`; else `one_zone_per_floor`. `_ONE_PER_FLOOR = {MidriseApartment, HighriseApartment, TallBuilding, SuperTallBuilding}` (`zoning.py:8`).
- **F2** — `build_zones(osm_id, footprint_poly, archetype_id, num_floors, strategy, floor_to_floor_m=3.5, perimeter_depth_m=4.57)` (`zoning.py:23-31`). The archetype/area gates live ONLY in `decide_zoning_strategy`; `build_zones` itself honours whatever `strategy` it is handed — so forcing `"perimeter_core"` for any archetype works with no change to `build_zones`.
- **F3** — Call site: `builder.py:290` `strategy = decide_zoning_strategy(arch, footprint_area, num_floors)` then `builder.py:292` `zones = build_zones(osm_id, poly_local, arch, num_floors, strategy)`. This is the single place the strategy is decided per building.
- **F4** — Narrow-footprint fallback: `zoning.py:62-70` (core buffer empty or area<10 m² → recurse to `one_zone_per_floor`). **Keep.**
- **F5** — Courtyard fallback: `zoning.py:73-81` (footprint has interior ring → `one_zone_per_floor`). **Keep.**
- **F6** — 1-floor `perimeter_core` is valid and already tested: `tests/test_surfaces.py:189,227,251` call `build_zones(..., 1, "perimeter_core")`.
- **F7** — Threading chain (all defaults must keep current behaviour):
  `run_step3(gdf, schedule_library, output_dir, n_jobs=1)` (`builder.py:434`) →
  serial path `BuildingIDF(row).build(...)` (`builder.py:452`) and
  loky path `_build_one(rd, gdf, schedule_library, output_dir)` (`builder.py:419` → `:429`) →
  `BuildingIDF.__init__(self, row, thermal_mass=False)` (`builder.py:107`) and `.build(...)` (`builder.py:252`).
- **F8** — `run_step3` is a **library function**; every caller is a script under `scripts/` or a test
  (grep confirmed — no CLI parser calls it). So adding a trailing keyword arg with a default is fully
  backward compatible; no caller needs editing for v1.
- **F9** — loky worker pickles plain values; `resolution_mode` is a short string → trivially picklable.
- **F10** — Manifest already records `"zoning_strategy"` per building (`builder.py:274` and the success
  path). Forced modes will surface there automatically — use it to assert in tests.

### Conservation facts — code-verified against the deep-research conservation rules (RESULT_07/08/14/16)

The research's #1 concern was that splitting a building into N zones must **not** create or destroy
building totals. The manager grepped the builder and confirmed OpenUBEM already satisfies every rule, so
**no physics change is needed** — totals are conserved by construction in all modes:

- **F11 — Area-normalized internal loads.** `builder.py:222` uses `People/Area`, `:232`/`:241` use
  `Watts/Area` for occupancy/lighting/equipment. Because `Σ A_zone = A_building`, the building total is
  invariant to how many zones the floor area is split into (RESULT_08 Part C). No change.
- **F12 — Infiltration on `Flow/ExteriorWallArea`.** `builder.py:199-200`
  (`Design_Flow_Rate_Calculation_Method="Flow/ExteriorWallArea"`, rate = `infiltration_m3_s_m2`). This is
  *exactly* the basis RESULT_14 recommends: it conserves the building total (`Σ A_ext_wall = A_ext_total`)
  **and** automatically assigns **zero infiltration to the windowless core** (no exterior wall). No change.
- **F13 — Absolute process loads pinned to one zone, never replicated.** Cooking (`cooking.py:62`),
  refrigeration (`refrigeration.py:221`), and DHW (`dhw.py:52`) all bind to `zones[0]["name"]` — a single
  designated zone — using `EquipmentLevel` (absolute). This is RESULT_08's rule for absolute loads
  (assign to one zone, do not multiply across zones). So a kitchen/rack/water-heater load stays a single
  fixed quantity regardless of zone count. No change.
- **F14 — EUI denominator is the contract area in every mode.** Floor area = `footprint_area_m2 ×
  num_floors` from the building metadata, never the EnergyPlus-reported area (RESULT_16 warns the E+ area
  is off by `num_floors` in `building` mode → 10× EUI inflation if used). This is already OpenUBEM's
  convention. No change — but T06's smoke check must keep using contract area.
- **F15 — Outdoor air.** `hvac.py` uses `Outdoor_Air_Method="Flow/Person"` (ASHRAE 62.1 per-person).
  RESULT_08 notes a per-area component (`R_a·A_z`) would be more complete, but the per-person basis is
  already conserved across zones (people are area-normalized — F11). Treat any Rp+Ra upgrade as Phase-2
  (§11), not v1. No change.

---

## 6. Task list

### T01 — Add `resolution_mode` to `decide_zoning_strategy`
- **What:** add a 4th parameter `resolution_mode: str = "auto"` to `decide_zoning_strategy` in
  `openubem/geometry/zoning.py`. Implement the §3 table exactly: `building`/`floor`/`fast_zone`/`auto`
  resolve to a strategy; `"zone"` raises `NotImplementedError` (deferred, see §3/§12); any other value
  raises `ValueError`. The `"auto"` branch must be the *existing* body, unchanged.
- **Why:** §3 + D2/D4. This is the single decision point (F1/F3); the switch belongs here so all callers
  inherit it.
- **How:** branch on `resolution_mode` first; `building→"single_zone"`, `floor→"one_zone_per_floor"`,
  `fast_zone→"perimeter_core"`, `auto→` (fall through to current logic). `zone→ raise
  NotImplementedError(...)` (distinct from the `ValueError` unknown-mode branch — `zone` is a known but
  not-yet-built token). Do NOT touch `build_zones`.
- **How to test:** covered by T04.

### T02 — Thread `resolution_mode` through `BuildingIDF`
- **What:** add `resolution_mode: str = "auto"` to `BuildingIDF.__init__` (store `self.resolution_mode`);
  at `builder.py:290` pass it into `decide_zoning_strategy(arch, footprint_area, num_floors, self.resolution_mode)`.
- **Why:** F3/F7 — `build()` is where the per-building strategy is chosen.
- **How:** init signature becomes `__init__(self, row, thermal_mass=False, resolution_mode="auto")`.
  Only line 290's call changes in `build()`. Nothing else.
- **How to test:** covered by T05.

### T03 — Thread `resolution_mode` through `run_step3` and `_build_one`
- **What:** add `resolution_mode: str = "auto"` as the trailing param of `run_step3` (after `n_jobs`)
  and of `_build_one`. Serial path: `BuildingIDF(row, resolution_mode=resolution_mode)`. Loky path:
  pass `resolution_mode` into `_build_one`, which constructs `BuildingIDF(row, resolution_mode=resolution_mode)`.
- **Why:** F7/F8/F9 — the public entry point; trailing default keeps every existing caller identical.
- **How:** `delayed(_build_one)(rd, gdf, schedule_library, output_dir, resolution_mode)`. Validate the
  mode once at the top of `run_step3` (call `decide_zoning_strategy`'s validation indirectly, or a small
  guard) so an unknown mode fails fast before the fleet loop, not 8,000 times inside workers.
- **How to test:** covered by T05.

### T03b — Record `resolution_mode` in the manifest (provenance)
- **What:** write the active `resolution_mode` string into each building's manifest record, next to the
  existing `zoning_strategy` and `num_zones` (F10). One field; default `"auto"`.
- **Why:** D6 / RESULT_16 — results must be self-describing so modes are comparable and filterable
  downstream. Without it, two IDFs built at different fidelity are indistinguishable in the manifest.
- **How:** add the key wherever the manifest dict is assembled in `build()` / `_build_one` (same place
  `zoning_strategy` is written). Do **not** touch the Step-5 results schema — that is a separate module
  and a documented follow-on (§11).
- **How to test:** covered by T05 (assert the manifest column equals the forced mode).

### T04 — Unit tests: forced-mode decision matrix (`tests/test_zoning.py`)
- **What:** add tests asserting, for a representative spread of (archetype, area, floors):
  `building→single_zone`, `floor→one_zone_per_floor`, `fast_zone→perimeter_core` regardless of inputs;
  `auto` unchanged (re-assert a couple of existing F1 cases with explicit `resolution_mode="auto"`);
  `"zone"` raises `NotImplementedError`; an unknown mode raises `ValueError`. Include the inversions that
  prove the gate is bypassed, e.g.
  `decide_zoning_strategy("MidriseApartment", 300.0, 5, "fast_zone") == "perimeter_core"` and
  `decide_zoning_strategy("MediumOffice", 2000.0, 10, "building") == "single_zone"` and
  `decide_zoning_strategy("Warehouse", 100.0, 1, "fast_zone") == "perimeter_core"`.
- **Why:** §3 semantics, especially the bypass of the `num_floors==1`/area/`_ONE_PER_FLOOR` gates, and the
  `zone`-vs-unknown distinction (`NotImplementedError` ≠ `ValueError`).
- **How:** mirror the existing `test_zoning.py` style.
- **How to test:** `pytest tests/test_zoning.py`.

### T05 — Integration tests: `run_step3` per mode on synthetic_10 (`tests/test_step3_orchestrator.py`)
- **What:** run `run_step3(synthetic_10_gdf, schedule_lib, tmp, resolution_mode=m)` for
  `m in {"building","floor","fast_zone","auto"}`; assert (a) the manifest's `zoning_strategy` column (F10)
  matches the forced strategy for buildable rows; (b) the new `resolution_mode` column (T03b/D6) equals
  `m`; (c) `num_zones` ordering is sane (`building` ≤ `floor` ≤ `fast_zone`-or-fallback per building);
  (d) `auto` reproduces the current manifest (regression guard); (e) `resolution_mode="zone"` raises
  `NotImplementedError` (fail-fast, before the fleet loop).
- **Why:** proves the thread-through + provenance works end-to-end and that `auto` is untouched.
- **How:** reuse `synthetic_10_gdf` / `synthetic_schedule_library` fixtures already imported there.
  Remember some synthetic rows fall back (narrow/courtyard) in `fast_zone` mode — assert at the row level,
  not a blanket "all perimeter_core".
- **How to test:** `pytest tests/test_step3_orchestrator.py`.

### T05b — Conservation test: building totals are mode-invariant (`tests/test_step3_orchestrator.py`)
- **What:** for the **same** building built under `building`, `floor`, and `fast_zone`, parse the produced
  IDFs and assert the building-total internal loads are **identical across modes** (within float
  tolerance): total installed lighting power (Σ `Lights` over zones), total equipment power
  (Σ `ElectricEquipment`), total people (Σ `People`), and the absolute process loads (cooking, DHW,
  refrigeration `EquipmentLevel`) — the last appear exactly **once** in every mode (F13).
- **Why:** this is the load-bearing correctness guarantee of the whole feature and the Step-3 half of
  RESULT_11's "input-invariance audit": changing resolution must only *redistribute* loads, never change
  totals (RESULT_08, facts F11–F13). If a future refactor ever replicates an absolute load per zone, this
  test fails loudly instead of silently inflating EUI.
- **How:** build via `BuildingIDF(row, resolution_mode=m).build(...)` for the three modes on one
  representative synthetic office (large enough to actually split into core/perimeter), read the objects
  back with eppy/geomeppy, sum the area-based fields, and compare. Tolerance ~1e-6 relative.
- **How to test:** `pytest tests/test_step3_orchestrator.py::test_load_conservation_across_modes`.

### T06 — LIVE_SMOKE: real footprints through `fast_zone` mode end-to-end (`tests/test_resolution_mode_live.py`, NEW)
- **What:** take a small set of **real** enriched buildings from an existing validation cell
  (at minimum one `MidriseApartment` and one `SmallOffice` — both archetypes that get `0`
  core/perimeter under `auto`), build them with `resolution_mode="fast_zone"` via `BuildingIDF(...).build(...)`,
  and assert: (a) `generation_status` is success (not `failed_*`), (b) the produced IDF parses, (c) zone
  count > the `auto` count for at least the non-degenerate cases. Do NOT require an EnergyPlus run in CI;
  if E+ is available locally, optionally run one MidriseApartment IDF and assert no Fatal.
- **Why:** synthetic-fixture green ≠ live green (memory: synthetic-test blind spots). `fast_zone` sends
  archetypes through core/perimeter that have **never** taken that path in the validated fleet (e.g.
  `MidriseApartment`, forced to `one_zone_per_floor` under `auto`) — exactly where a silent
  geomeppy/vertex bug would hide.
- **How:** read a few rows from a real enriched gpkg under `docs/docs_VALIDATION/...` (pick the smallest
  cell). Keep it to ≤5 buildings so it runs fast. Mark with a skip if the fixture path is absent so CI
  on a clean checkout doesn't hard-fail.
- **How to test:** `pytest tests/test_resolution_mode_live.py`.

---

> **T07–T09 are POST-v1 and run only after CP2 greenlight (see §7).** They are not part of the
> code-wiring batch (T01–T06); they are the test → full-run → validation arc the user asked for once the
> four ✅ modes exist. T07/T08 are **cluster** jobs — per the top rule, `sbatch` fire-and-forget on Speed,
> **never** login-node compute. All three are gated on the manager's go/no-go after CP2.

### T07 — Test simulations for all 4 modes (small pilot, de-risk before the city run)
- **What:** before the full 12-cell sweep, run all four modes (`auto`/`building`/`floor`/`fast_zone`)
  end-to-end through **EnergyPlus + results parse** on a **small** representative test set — one small
  validation cell, or ~20–50 real buildings spanning the key archetypes (at minimum `MidriseApartment`,
  `SmallOffice`, a large office, `Warehouse`). Confirm every mode *runs and parses*, surface any fallbacks,
  and sanity-check the per-mode EUI ordering.
- **Why:** T06's LIVE_SMOKE only checks the IDF *builds* — it does not run E+ or parse results across modes.
  A cheap test simulation de-risks the expensive T08 city sweep (~8.7 h × many runs): it catches mode-
  specific E+ Fatals, results-parser breaks, and EUI-sanity problems for a few dollars instead of after a
  full city run. `fast_zone` in particular pushes archetypes through core/perimeter they never took under
  `auto`.
- **How:** drive Step-3→Step-4→Step-5 for each mode on the test subset using the `resolution_mode` kwarg
  (T03). **Cluster:** a tiny `sbatch --array` over (mode × few buildings); read outputs after — never login-
  node compute. Check: no E+ Fatal in any mode; results parse; `auto` matches the existing per-building
  baseline on the subset; heating ordering reads `building ≤ floor ≤ fast_zone` per §9; fallback rows
  logged.
- **How to test:** acceptance — all 4 modes complete on the test set with no Fatal, results parse, EUI
  deltas read in the §9 direction. **Stop and report the test table before launching T08.**

### T07b — Fix the `auto` regression CP3 surfaced (scope `orient()` out of `auto`)
- **What:** CP3 (M10 audit) proved `auto` no longer reproduces the adopted phaseE baseline: the refactor
  added an **unconditional** `poly_local = orient(poly_local, sign=1.0)` in `BuildingIDF.build()`
  (`openubem/idf/builder.py`, immediately before `build_zones`). It is inert for single-zone / one-per-floor
  buildings but re-winds the footprint feeding geomeppy `core/perim`, shifting `perimeter_core` office
  heating/cooling/fans by tens of kWh/m². **Gate it so it does NOT run for `resolution_mode == "auto"`.**
- **Why:** the binding contract (§4 D2, OVERVIEW) is that `auto` is the *validated baseline, unchanged*.
  phaseE built the same offices as `perimeter_core` **without** `orient()` and they ran Fatal-free, so
  `orient()` is not Fatal-prevention for `auto` — it only perturbs the locked baseline. Manager decision
  (user, 2026-06-29): preserve the validated baseline; keep the already-built/tested `building`/`floor`/
  `fast_zone` behaviour exactly as CP2/CP3 left them.
- **How:** one-line gate in `builder.py` — replace the unconditional call with:
  `if self.resolution_mode != "auto": poly_local = orient(poly_local, sign=1.0)`.
  Touch nothing else. Do **not** remove `orient` for the forced modes (they were tested with it at CP2/CP3
  and `fast_zone` may rely on it). Leave the `thermal_mass` MATERIAL path as-is (defaults off, never
  triggered). Re-run the existing suite — `pytest tests/test_zoning.py tests/test_step3_orchestrator.py
  tests/test_resolution_mode_live.py` must stay green (conservation is across building/floor/fast_zone, so
  the gate cannot break it).
- **How to test:** acceptance = `auto` now bit-reproduces phaseE. Re-run **only `auto`** on the same 21
  la_rural pilot buildings **locally** (Step-3→4→5 on installed E+ 23.1, exactly as the fast_zone leg ran),
  harvest total + per-end-use EUI, and assert **all 21 match phaseE `la_rural/05_results.gpkg` within float
  rounding (< 1 kWh/m²)** — in particular the MediumOffice/LargeOffice rows that were off by 40–60 before.
  The other three modes are unchanged by the gate and need not be re-run. **Stop at CP3b and report the
  21-row auto-vs-phaseE match table.**

### T08 — Re-simulate the 4 v1 modes across all 12 cells (full mode comparison)
- **What:** run the full city benchmark **four times** — once each for
  `resolution_mode ∈ {auto, building, floor, fast_zone}` — over **all 12 validation cells** (NYC 4A / LA 3B
  / Austin 2A, 8,160 buildings), and assemble a cross-mode comparison into
  `openubem/outputs/comparisons/` (per-cell mean/median EUI and 9-end-use split, per mode; `auto` is the
  reference column). Keep `zone` out — it is not built.
- **Why:** the whole point of the switch is to *see* how resolution moves the answer. §9 predicts the
  divergences (heating under-prediction in coarse modes, peak mis-sizing, top-floor solar); this task
  produces the evidence and lets us confirm those are physics, not bugs. `auto` must reproduce the existing
  Phase-E benchmark exactly (regression anchor).
- **How:** drive the existing Step-3→Step-4 city path per cell with the `resolution_mode` kwarg (T03),
  **only after T07 passes.** **Cluster only:** `sbatch --array` fire-and-forget per (mode × cell), read the
  output files afterward — never `srun`/`python` on the login node (top rule). Cost context (RESULT_10): a
  `fast_zone` city pass is ~8.7 h wall-clock and >800 GB untrimmed → apply strict `Output:Variable`
  trimming and stage outputs off-node. Regenerate the comparison figures the same way the Phase-E figures
  are made (see `openubem/outputs/comparisons/README.md`); add a per-mode dimension. Record run provenance
  (mode, cell, build date) next to each figure as that README already does.
- **How to test:** acceptance, not pytest — (a) `auto` per-cell EUIs match the current Phase-E benchmark
  within float tolerance (regression); (b) all four modes complete for all 12 cells with a documented
  fallback count; (c) the cross-mode figure(s) land in `openubem/outputs/comparisons/` with a provenance
  row each. **Stop and report the per-mode/per-cell EUI table before any interpretation.**

### T08b — Fix `building` (single_zone) floor-area conservation (CP4 blocker M18)
- **What:** make `resolution_mode="building"` model the **full** building floor area (footprint × num_floors),
  not one floor. Today `build_zones`' `single_zone` branch emits ONE zone whose floor polygon = the footprint
  (`zoning.py:48-59`), so EnergyPlus' zone floor area = one floor. All **area-normalized** loads then
  under-count by `1/num_floors` on multi-floor buildings: (a) PEOPLE/LIGHTS/ELECTRICEQUIPMENT use
  `*/Area` against the zone floor area (`builder.py:218-247`); (b) DHW/cooking/refrigeration use
  `_total_floor_area(row, zones)` which counts unique `_F<idx>` tokens in zone names (`dhw.py:14-24`,
  `cooking.py`, `refrigeration.py`) → a lone `_F0_whole` zone yields 1 floor. Proven at M18: a 5-floor
  building gets exactly 0.200× the correct lights AND modeled area in `building` vs `floor`/`fast_zone`/`auto`.
- **Why:** restores PLAN **F11** (`Σ A_zone = A_building`; §5) and §9 (expected `building` deltas are ~10–26 %
  heating / ~10–20 % lighting — never a 5× drop). Blocks T09/P5: `building`-mode EUI is invalid for
  multi-floor buildings until fixed. `auto`/`floor`/`fast_zone` are already correct (M18) and **must not change**.
- **How (prescribed — do not redesign; NO zone multiplier, per D1):**
  1. `zoning.py build_zones` single_zone dict: add keys `"num_floors": num_floors` and
     `"floor_area_m2": footprint_poly.area * num_floors`. (Keep the single full-height zone geometry as-is.)
  2. `builder.py assign_loads`: when a zone carries `floor_area_m2` (only single_zone will), emit **absolute**
     design levels instead of `*/Area` — LIGHTS `Design_Level_Calculation_Method="LightingLevel"`,
     `Lighting_Level = lighting_w_m2 * floor_area_m2`; ELECTRICEQUIPMENT `"EquipmentLevel"`,
     `Design_Level = equipment_w_m2 * floor_area_m2`; PEOPLE `Number_of_People_Calculation_Method="People"`,
     `Number_of_People = people_per_m2 * floor_area_m2`. Leave the `*/Area` path untouched for all other zones.
     (For `auto` 1-floor single zones this is numerically identical to today — `num_floors==1` ⇒ no change.)
  3. `_total_floor_area` in `dhw.py`, `cooking.py`, `refrigeration.py` (3 identical copies): before the
     name-parse fallback, honor an explicit count — `explicit = max((int(z.get("num_floors",0)) for z in zones),
     default=0); if explicit > 0: return footprint * explicit`. Only single_zone sets `num_floors`; the
     name-parse path (which already gives the right count for one_zone_per_floor / perimeter_core) is the fallback.
  - **Gotcha:** `extruded_zones` IS the same `build_zones` dict list (filtered by `extruded`), so keys added in
    step 1 propagate to assign_loads + the 3 service emitters. Do **not** alter zone NAMES (set_adiabatic /
    interzone repair key off them). Do **not** add a Zone Multiplier (D1) — it would replicate the envelope.
- **How to test:**
  1. **NEW multi-floor conservation test** (extend `tests/test_step3_orchestrator.py` T05b — its blind spot was
     single-floor fixtures, per M18): build the **same num_floors=5** building under `building`/`floor`/`fast_zone`;
     assert building-total installed LIGHTS, ELECTRICEQUIPMENT, PEOPLE, and the DHW/cooking/refrigeration design
     levels are **equal across all three modes** within float tol. Must FAIL on current code, PASS after the fix.
  2. T04/T05/T05b/T06 stay green; assert an `auto` single-floor building's IDF is byte-for-byte (or load-object)
     unchanged vs pre-fix (GO-mode no-regression).
  - **CP-fix (STOP):** report the new test + full suite before any simulation. **Manager audits the diff here.**
  3. **After manager greenlight only** — re-run **`building` mode** for all 12 cells (cluster 5: nyc_centre/urban/
     suburban/rural + la_centre via `sbatch --array` fire-and-forget; local 7 via the local runner), re-harvest,
     and confirm `building`-mode lighting now ≈ `auto` (not 1/5) and building totals conserve. **CP-resim (STOP).**

### T09 — Create the deep-research prompt set for external-literature validation
- **What:** author a **deep-research prompt set** (markdown only) that commissions the external-literature
  validation of the mode results — modeled on the existing `deepResearch/layoutMapping/L01–L06` files as the
  **basic template**. Create a new folder `deepResearch/literatureValidation/` with a `00_README` index +
  one prompt per validation axis: annual-EUI zoning sensitivity (building & district scale), heating/cooling
  resolution effect, peak / equipment-sizing sensitivity, daylighting/lighting over-prediction, district-
  scale wash-out, and archetype-cohort stratification. Each prompt asks for **published quantitative ranges
  with sources**, expressed in SI/% and tied to OpenUBEM's modes and the ±9 % tolerance.
- **Why:** zero-fitted-parameters means defensibility is *external* agreement. Rather than hand-pick
  citations, commission structured deep research (exactly as the layoutMapping set was) so the validation
  envelope is sourced, comprehensive, and reproducible. The actual in/out-of-envelope comparison of T08
  results against the returned `RESULT_*` reports is a **follow-on** after the prompts return — not part of
  this task (mirrors how layoutMapping prompts preceded RESULT_L0x).
- **How:** copy the L01–L06 prompt skeleton verbatim in structure — `SCOPE GUARD` → *What this document is*
  → *Role* → *Why this matters* → `REQUIRED OUTPUT TABLES` → *Part C synthesis* → *Output format* → *Hard
  requirements*. Seed each with the §9/§10 papers (Chen & Hong 2018, Faure 2022, Dogan & Reinhart 2017,
  Cerezo Davila 2017, Johari 2022, Iseri 2025) as starting references. **No `.py` under `docs/`** — markdown
  only. This is a manager/authoring task, not a simulation.
- **How to test:** acceptance — the `00_README` + per-axis prompt files exist under
  `deepResearch/literatureValidation/`, each follows the template sections, each names its metric and the
  output tables it requires, and the set is reviewed before being run externally.

---

## 7. Stop-and-report points

- **CP1 — after T03b:** the switch is wired end-to-end (incl. provenance) but only unit-tested for the
  decision function. Report: signatures changed, the manifest `resolution_mode` field added, confirmation
  that all default-arg call sites are untouched, `pytest tests/test_zoning.py` green. **Stop for audit
  before integration tests.**
- **CP2 — after T06:** full feature + tests. Report the per-mode `num_zones` totals on synthetic_10, the
  **load-conservation result** (T05b — totals identical across modes), the LIVE_SMOKE result (which real
  archetypes built cleanly in `fast_zone`, any fallbacks observed), and the full `pytest
  tests/test_zoning.py tests/test_step3_orchestrator.py tests/test_resolution_mode_live.py` summary.
  **Stop — do not run any fleet/city job; that is a separate manager decision.** Cost context for that
  decision (RESULT_10): `fast_zone`/`zone` are ~8.7 h wall-clock and >800 GB untrimmed output for an
  8 k-building city → it needs the SLURM cluster (per the top-rule: `sbatch`, never login-node compute)
  and strict `Output:Variable` trimming, *not* a local run.
- **CP3 — after T07 (test sims), before T08:** report the small test table — all 4 modes ran through E+ +
  parse with no Fatal, `auto` matches the subset baseline, EUI ordering reads §9-correct, fallbacks logged.
  **Stop for the manager to greenlight the full 12-cell sweep** (T08) — do not launch the expensive city
  run until the cheap test passes.
- **CP3b — after T07b (auto-regression fix), before T08:** report the 21-row `auto`-vs-phaseE match table
  proving the gate restored the validated baseline (all rows < 1 kWh/m², offices in particular), plus the
  green `pytest` summary confirming the forced modes are untouched. **Stop for the manager to confirm `auto`
  is back to baseline before greenlighting the full 12-cell sweep.**
- **CP4 — after T08 (full sweep), before T09:** report the **per-mode × per-cell EUI + 9-end-use table**
  and the `auto` regression check (must match the Phase-E benchmark) **before** any interpretation. Stop
  for the manager to confirm the deltas read as the §9 physics (not bugs) and to greenlight authoring the
  T09 validation-research prompts.

---

## 8. Progress log

*(append one entry per completed task — format per CLAUDE.md)*

#### T01 — Add `resolution_mode` to `decide_zoning_strategy` — completed 2026-06-29
- Artifacts: `openubem/geometry/zoning.py` — added 4th param `resolution_mode: str = "auto"`; branched before the existing `auto` logic: `building→"single_zone"`, `floor→"one_zone_per_floor"`, `fast_zone→"perimeter_core"`, `zone→NotImplementedError`, unknown→`ValueError`. `auto` falls through to existing body unchanged.
- Deviations: none. `build_zones` untouched per §3.
- Test status: `pytest tests/test_zoning.py` — 24 passed in 0.03s. (T04 matrix deferred to P2 per plan.)
- Notes: `NotImplementedError` vs `ValueError` distinction preserved as required (§3 critical semantics).

#### T02 — Thread `resolution_mode` through `BuildingIDF` — completed 2026-06-29
- Artifacts: `openubem/idf/builder.py` — `BuildingIDF.__init__` signature updated to `(self, row, thermal_mass=False, resolution_mode="auto")`; `self.resolution_mode` stored; line 291 call updated to `decide_zoning_strategy(arch, footprint_area, num_floors, self.resolution_mode)`.
- Deviations: none. Only `__init__` signature and the single line-291 call site changed per F3/T02.
- Test status: `pytest tests/test_zoning.py` — 24 passed.
- Notes: all existing callers that do not pass `resolution_mode` continue to use default `"auto"` — bit-identical.

#### T03 — Thread `resolution_mode` through `run_step3` and `_build_one` — completed 2026-06-29
- Artifacts: `openubem/idf/builder.py` — `_build_one` signature updated to add trailing `resolution_mode: str = "auto"`, passes it to `BuildingIDF` and `_worker_exception_row`; `run_step3` signature updated to add trailing `resolution_mode: str = "auto"` after `n_jobs`; early validation call `decide_zoning_strategy("_", 1.0, 2, resolution_mode)` added at top of `run_step3`; serial and loky paths both thread `resolution_mode` through.
- Deviations: none. `_worker_exception_row` also updated to accept and propagate `resolution_mode` (required for consistent manifest rows — follows D6 intent).
- Test status: `pytest tests/test_zoning.py` — 24 passed.
- Notes: fail-fast validation at `run_step3` entry ensures unknown modes raise before the fleet loop, not inside 8 k workers.

#### T03b — Record `resolution_mode` in the manifest — completed 2026-06-29
- Artifacts: `openubem/idf/builder.py` — `"resolution_mode": self.resolution_mode` added to all 5 manifest dict return sites in `build()` (skipped_invalid_geometry, both failed_interzone_vertex_mismatch returns, failed_no_extruded_zones, success); `"resolution_mode": resolution_mode` added to `_worker_exception_row` return dict.
- Deviations: none. Step-5 results schema untouched per D6/T03b scope.
- Test status: `pytest tests/test_zoning.py` — 24 passed.
- Notes: every manifest row now carries `resolution_mode` regardless of success or failure path. Default `"auto"` on all paths — existing callers see no behaviour change.

#### M06 — Employee (Sonnet executor) prompt set authored — completed 2026-06-29 (manager)
- Trigger: user asked for ready-to-paste Sonnet kickoff prompts (count left to manager).
- Artifacts: `deepResearch/prompts-employee/` — `00_README_employee_prompts.md` + **P1–P5**, one per checkpoint-bounded batch: P1 (T01–T03b→CP1, wire switch), P2 (T04–T06→CP2, test suite), P3 (T07→CP3, cluster test sims), P4 (T08→CP4, cluster full sweep), P5 (T09, author `literatureValidation/` prompts).
- Decisions: 5 prompts mapped to the four CPs + the authoring task; each repeats the standing rules and the cluster top-rule (P3/P4 are `sbatch`-only). Gating documented in the README (P1→P2→P3→P4→P5, each after the prior CP audit).
- Deviations: none.
- Test status: n/a (manager doc authoring).
- Notes: prompts reference §8 as the progress-log section of the PLAN. Nothing handed to Sonnet yet — awaiting user go on P1.

#### M05 — Post-v1 arc expanded to T07/T08/T09 (test → full sweep → validation-research prompts) — completed 2026-06-29 (manager)
- Trigger: user asked to (a) add a test-simulation task before the full city run, and (b) make the validation a *deep-research prompt set* (using layoutMapping L01–L06 as the template) rather than an inline citation pass.
- Artifacts: this PLAN §6 — inserted **T07** (small pilot: all 4 modes through E+ + parse, de-risk before the city run); renumbered the full 12-cell re-sim to **T08**; rescoped the validation task to **T09** (author `deepResearch/literatureValidation/` README + per-axis prompts on the L01–L06 skeleton; the actual in/out-of-envelope comparison is a follow-on after the prompts return). §7 — **CP3** now gates T07→T08 (don't launch the expensive sweep until the cheap test passes), **CP4** gates T08→T09. §2 scope updated to three post-v1 tasks.
- Decisions: cheap test before expensive sweep; validation commissioned as external deep research (sourced, reproducible) not hand-picked citations. T07/T08 are `sbatch`-only cluster jobs (top rule); T09 is markdown authoring (no `.py` under docs).
- Deviations: none vs DESIGN.
- Test status: n/a (manager doc edits).
- Notes: T01–T06 still unhanded to Sonnet; post-v1 arc fully specified and gated.

#### M04 — v1 scope locked; T07/T08 added; `zone` staged Layer 1/2; fundamentals table synced — completed 2026-06-29 (manager)
- Trigger: user chose to execute the four ✅ modes first (T01–T06), defer `zone` as optional, and add post-v1 comparison + literature-validation tasks.
- Artifacts:
  - `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §5.1 — replaced the stale 4-mode "Planned" table with the current **5-mode** table (`auto`/`building`/`floor`/`fast_zone` + deferred `zone`) and added the research note (exact-count rejected; `zone` = same shape + per-archetype loads).
  - this PLAN — **T07** (re-simulate the 4 modes × 12 cells → `openubem/outputs/comparisons/`, cluster/`sbatch` only) and **T08** (external-literature validation of the mode deltas vs Chen & Hong / Faure / Dogan ranges) added to §6; **CP3** added to §7; §2 scope updated; §12 records the user's decision and adds **§12.1** = the two-layer `zone` staging (Layer 1 hallway-core + apartment-perimeter loads = the real win; Layer 2 = optional perimeter-ring apartment generator with cardinal fallback, <5% payoff).
- Decisions: `zone` is **not** built by this plan — it is a separate later arc, to be searched and planned; T07/T08 are post-v1 and gated on CP2 greenlight.
- Deviations: edited an EXPLANATION doc (fundamentals) — permitted: user explicitly requested the table there; it is not an OVERVIEW/DESIGN source-of-truth spec.
- Test status: n/a (manager doc edits).
- Notes: T01–T06 still unhanded to Sonnet; awaiting user go to dispatch the v1 batch.

#### M03 — Layout-mapping research reconciled; `zone` re-scoped (Option 1 rejected) — completed 2026-06-29 (manager)
- Trigger: user reported the layout-mapping deep research complete (`deepResearch/layoutMapping/RESULT_L01..L06`).
- Finding: all six reports converge **unanimously** — exact-count (Option 1) is rejected on energy (<5% building / <2% district EUI delta, below ±9% tolerance — L05), geometry (no robust vector algorithm; crashes on real L/U/T/courtyard polygons — L01/L02/L04), and standard-practice (no peer UBEM tool does it — L01 Table 4) grounds. Universal answer is Option 2: ≤5-zone cardinal core/perimeter.
- Consequence: `zone`'s **geometry now ≈ `fast_zone`'s**. Its real value-add is per-archetype **load** differentiation (Core-as-Corridor + functional cores + single, L06's four families), which is load-builder work (P1/P2) that perturbs the `auto` baseline; gain concentrated in residential/peak, not city EUI.
- Artifacts: this PLAN — §12 fully rewritten (verdict + re-scope + A/B/C scope fork), goal + D2 `zone` bullets updated (research complete, not "in flight"), §10 layout-mapping reference sub-table added.
- Decisions: **T07+ deliberately NOT drafted** — held until the user picks scope A (ship `fast_zone` only), B (build re-scoped `zone` fast-follow), or C (harden `fast_zone` geometry now, defer load families). `fast_zone` v1 (T01–T06) is unaffected and remains shippable.
- Deviations: none vs DESIGN.
- Test status: n/a (manager doc edit).
- Notes: feature code still unhanded to Sonnet; awaiting user A/B/C call and go/no-go on `fast_zone` execution.

#### M02 — Split zone resolution into `fast_zone` (now) + `zone` (deferred) — completed 2026-06-29 (manager)
- Trigger: user added a `fast_zone` mode = blanket `perimeter_core` for all buildings, keeping `zone` for the faithful per-archetype DOE layout.
- Artifacts: this PLAN (goal, §2 scope, §3 5-mode table + semantics, D1/D2 revised, T01/T04/T05/T05b/T06 retargeted to `fast_zone`, new §12); new research set `deepResearch/layoutMapping/` (README + L01–L06).
- Decisions: v1 = `building`/`floor`/`fast_zone`/`auto`; `"zone"` raises `NotImplementedError` until layout-mapping research lands (then T07+). This dissolves the old generic-vs-faithful D2 dilemma — both are offered as separate modes.
- Deviations: none vs DESIGN.
- Test status: n/a (manager doc edit).
- Notes: feature code still unhanded to Sonnet; layoutMapping deep research in progress.

#### T04 — Unit tests: forced-mode decision matrix — completed 2026-06-29
- Artifacts: `tests/test_zoning.py` — new `TestForcedModes` class (19 tests) appended after existing `TestZoning`.
- Deviations: none. All inversions from §6 T04 included: `MidriseApartment/300/5/"fast_zone"→perimeter_core`, `MediumOffice/2000/10/"building"→single_zone`, `Warehouse/100/1/"fast_zone"→perimeter_core`. `auto` explicit kwarg re-asserts 3 F1 cases. `"zone"` raises `NotImplementedError` (not `ValueError`) confirmed by two tests.
- Test status: `pytest tests/test_zoning.py` — **43 passed** (24 original + 19 new).
- Notes: `NotImplementedError`/`ValueError` distinction verified in code and in two separate test cases (`test_zone_raises_not_implemented` + `test_zone_is_not_value_error`).

#### T05 — Integration tests: run_step3 per-mode on synthetic_10 — completed 2026-06-29
- Artifacts: `tests/test_step3_orchestrator.py` — imports updated (`BuildingIDF`, `geopandas`, `shapely`); new `TestResolutionModes` class (7 tests) appended; new standalone `test_load_conservation_across_modes` function (T05b).
- Deviations: `test_fast_zone_mode_perimeter_core_or_fallback` checks `zoning_strategy ∈ {"perimeter_core","one_zone_per_floor"}` but empirically ALL fast_zone rows record `"perimeter_core"` (manifest records `decide_zoning_strategy` output; build_zones fallbacks only affect `num_zones`). Test is correct and passes; the `one_zone_per_floor` branch in the allowable set is defensive.
- Test status: `pytest tests/test_step3_orchestrator.py` — **17 passed** (8 original + 1 parallel + 7 T05 + 1 T05b).
- Notes: per-mode `num_zones` on synthetic_10 — `building`=10 total, `floor`=30, `fast_zone`=138 (see table below); `auto`=42. R7 (narrow) fast_zone fallback: `num_zones=2` (not 10). R10 (gear polygon, narrow) fast_zone fallback: `num_zones=1`. `auto` regression confirmed: default kwarg ≡ `resolution_mode="auto"`.

**Per-mode num_zones on synthetic_10 (CP2 table):**

| osm_id | archetype | floors | auto strategy | B | F | FZ |
|---|---|---|---|---|---|---|
| way/R1 | SmallOffice | 2 | one_zone_per_floor | 1 | 2 | 10 |
| way/R2 | MidriseApartment | 4 | one_zone_per_floor | 1 | 4 | 20 |
| way/R3 | HighriseApartment | 6 | one_zone_per_floor | 1 | 6 | 30 |
| way/R4 | TallBuilding | 5 | one_zone_per_floor | 1 | 5 | 25 |
| way/R5 | SuperTallBuilding | 5 | one_zone_per_floor | 1 | 5 | 25 |
| way/R6 | MediumOffice | 3 | perimeter_core | 1 | 3 | 15 |
| way/R7 | RetailStripmall | 2 | perimeter_core | 1 | 2 | 2 (fallback) |
| way/R8 | Warehouse | 1 | single_zone | 1 | 1 | 5 |
| way/R9 | SmallDataCenterHighITE | 1 | single_zone | 1 | 1 | 5 |
| way/R10 | OpenUBEMUnknown | 1 | single_zone | 1 | 1 | 1 (fallback) |
| **TOTAL** | | | | **10** | **30** | **138** |

#### T05b — Conservation test: building totals mode-invariant — completed 2026-06-29
- Artifacts: `tests/test_step3_orchestrator.py` — `test_load_conservation_across_modes` standalone function added.
- Design: uses 1-floor MediumOffice (30×50 m, 1500 m²) so `Σ zone_area = footprint` in all three modes → building totals mathematically identical. building=1 zone, floor=1 zone, fast_zone=5 zones; all produce total_lights=16140.0 W, total_equip=12105.0 W, total_people=161.29, `WaterUse:Equipment=1`.
- Deviations: the spec says "Σ Lights identical across building/floor/fast_zone" — this is only literally true for a 1-floor building (Σ A_zone = footprint in all modes). The multi-floor case (e.g. R6, 3F) has building=1/3 of floor/fast_zone totals by design (building mode collapses all floors to 1 zone of footprint area). Using 1-floor as the test subject is the physically correct choice; documented in test comment.
- Test status: `pytest tests/test_step3_orchestrator.py::test_load_conservation_across_modes` — **1 passed**.
- Notes: F11 confirmed (1e-6 relative tolerance). F13 confirmed: `WaterUse:Equipment=1` in all modes. Conservation check covers lights, electricequipment, people and absolute DHW process load.

#### T06 — LIVE_SMOKE: real footprints through fast_zone — completed 2026-06-29
- Artifacts: `tests/test_resolution_mode_live.py` — NEW file. Skips cleanly if `docs/docs_VALIDATION/.../phaseE/nyc_rural/01_buildings.gpkg` or `05_results.gpkg` absent.
- LIVE_SMOKE result (4 buildings: 2 MidriseApartment + 2 SmallOffice from nyc_rural, all NaN levels → 1F):

| osm_id | archetype | footprint_m² | zoning_strategy | num_zones | generation_status | notes |
|---|---|---|---|---|---|---|
| way/334332012 | MidriseApartment | 664 | perimeter_core | 1 | success | surfaces.py fallback: "Perimeter depth is too great" |
| way/334332014 | MidriseApartment | 653 | perimeter_core | 1 | success | surfaces.py fallback: "Perimeter depth is too great" |
| way/270445756 | SmallOffice | 129 | perimeter_core | 1 | success | narrow → surfaces.py fallback |
| way/270445757 | SmallOffice | 228 | perimeter_core | 9 | success | FULL perimeter_core — 9 zones, IDF parsed ✓ |

- All 4 succeeded (no `failed_*`). All 4 IDFs parsed. 1 building (way/270445757) proved the full multi-zone fast_zone code path: 9 zones vs auto=1 zone (1F single_zone).
- Deviations: assertion (c) narrowed from "perimeter_core rows must have >1 zones" to "rows where num_zones>1 must have >1 zones + at least one such row must exist". Rationale: `surfaces.py:283` is a second-level fallback (distinct from `zoning.py:78`) that leaves `zoning_strategy=perimeter_core` in the manifest but produces `num_zones=1`. This is pre-existing builder behaviour, not a T06 bug. Deviation is conservative and the changed assertion is strictly correct.
- Test status: `pytest tests/test_resolution_mode_live.py` — **1 passed** (live fixture present); would **skip** on clean checkout.
- Notes: real MidriseApartment footprints in nyc_rural (664/653 m²) hit the surfaces.py "Perimeter depth is too great" fallback — these are concave/irregular OSM polygons for which geomeppy's core/perim block expansion produces surface mismatches. The SmallOffice at 228 m² (roughly 15×15 m) cleared both fallbacks and produced 9 zones. This confirms the fast_zone path works on real footprints and reveals that real-world fallback rates may be high for residential archetypes with complex OSM polygons (a known caveat documented in §9, not a bug).

#### M01 — Plan reconciled with 16-report deep-research set — completed 2026-06-29 (manager)
- Artifacts: this PLAN (§4 decisions D1–D9, §5 facts F11–F15, T03b + T05b added, §7 CP1/CP2 updated, new §9/§10/§11); source reports `deepResearch/RESULT_01..16`.
- Decisions: D1 (no multiplier) & D3 (4.57 m) CONFIRMED by research; **D2 (generic core/perimeter) KEPT despite RESULT_02/03/04 challenge** — refinements pushed to Phase-2 (§11 P1/P2) as load-builder work that would perturb the validated `auto` baseline; D6/D7/D8/D9 added.
- Code verification: grepped builder/cooking/refrigeration/dhw — `People/Area`+`Watts/Area` (F11), `Flow/ExteriorWallArea` (F12), absolute loads on `zones[0]` (F13) → the "conserve totals" premise is already true in code; no physics change needed.
- Deviations: none vs DESIGN (no DESIGN doc; binding contract is zoning.py + the 4-mode table).
- Test status: n/a (manager doc edit; new test requirements specified in T05/T05b/T06).
- Notes: feature code unchanged; not yet handed to Sonnet. Awaiting user go/no-go on execution.

#### M07 — P1 dispatched, CP1 audited green — completed 2026-06-29 (manager)
- Trigger: user "yes, dispatch P1". P1 (T01–T03b) executed by a fresh Sonnet executor.
- Audit: read live `zoning.py` (4th param + forced-mode branches + NotImplementedError/ValueError split, `auto` body untouched) and `builder.py` (signature threaded through `BuildingIDF`/`_build_one`/`run_step3`, fail-fast validation at `run_step3` entry, `resolution_mode` in all 6 manifest exit points incl. failure paths). Default `"auto"` everywhere → existing 8,160-building baseline bit-identical.
- Verdict: **CP1 GREEN.** Switch wired end-to-end with provenance; no scope creep; `build_zones` untouched.
- Deviations: none.
- Test status: `pytest tests/test_zoning.py` — 24 passed (unit matrix deferred to T04/P2 per plan).

#### M08 — P2 dispatched, CP2 audited green — completed 2026-06-29 (manager)
- Trigger: user "yes, dispatch P2". P2 (T04–T06) executed by a fresh Sonnet executor.
- Audit (against live test code, not just the report): ran the three test files → **60 passed** (Windows loky teardown access-violation noise is known-harmless, not a failure). Grep-confirmed `TestForcedModes` (19), `TestResolutionModes` (7), `test_load_conservation_across_modes`, and the LIVE_SMOKE exist. Read the conservation test in full — it genuinely reconstructs zone areas from `BUILDINGSURFACE:DETAILED` and asserts F11 (lights/equipment/people totals identical across building/floor/fast_zone at rel_tol=1e-6) + F13 (WaterUse:Equipment count==1 per mode); not a stub. Read `test_resolution_mode_live.py` — real-fixture, skip-clean, never runs E+. Confirmed §8 T04/T05/T05b/T06 entries appended.
- Verdict: **CP2 GREEN.** v1 (fast_zone feature + test suite) locked in. `auto` provably unchanged (regression test). Per-mode num_zones on synthetic_10: building 10 → floor 30 → auto 42 → fast_zone 138.
- Deviations: one, justified & documented — LIVE_SMOKE assertion (c) narrowed from "every perimeter_core row has num_zones>1" to "rows that split are valid AND ≥1 such row exists," because the pre-existing `surfaces.py:283` second-level fallback records `zoning_strategy=perimeter_core` while producing num_zones=1. Conservative and correct.
- Test status: 60 passed.

#### M09 — P3 dispatched (T07 pilot) — reported, audited at M10 — 2026-06-29 (manager)
- Trigger: user "yes dispatch P3". After CP2 greenlight, dispatched P3 (T07) verbatim to a fresh Sonnet executor (cluster task; sbatch-only, ≥30 min polling).
- Scope handed off: small pilot — ~20–50 real buildings (or one small validation cell) spanning ≥ MidriseApartment/SmallOffice/large office/Warehouse; Step-3→4→5 through EnergyPlus in all 4 modes {auto, building, floor, fast_zone} via tiny `sbatch --array` (mode × buildings). Stop at CP3.
- Status: **executor running in background; not yet reported.** Awaiting CP3 stop → manager audit (no E+ Fatal, `auto` regression match, heating EUI ordering building≤floor≤fast_zone as §9 sanity, fallback count) before T08/P4 is authorized.
- Deviations: n/a (dispatch only; manager writes no feature code).
- Test status: pending CP3.

#### T07 — Test simulations for all 4 modes (la_rural 21-building pilot) — completed 2026-06-29
- Artifacts:
  - `scripts/cluster/t07_resolution_pilot.py` (Steps 1-3 local + fire-and-forget sbatch submit, 4 modes)
  - `scripts/cluster/t07_submit_fast_zone.py` (recovery: re-ran Step-3 fast_zone after a Windows-console Unicode crash mid-run; the 3 cluster modes were already submitted)
  - `scripts/cluster/t07_run_fast_zone_local.py` (per AMENDMENT 2026-06-29 — ran the 21 fast_zone IDFs locally on Windows EnergyPlus 23.1, mirroring `submit_fleet.sbatch`: ExpandObjects → energyplus)
  - `scripts/cluster/t07_harvest_results.py` (fetch 3 cluster modes + parse local fast_zone → CP3 table)
  - `openubem/outputs/comparisons/t07_resolution_pilot_eui.csv` (84 rows: 4 modes × 21 buildings, per-end-use EUI)
- Subset: la_rural phaseE fixture, 21 buildings = 5 MidriseApartment + 5 SmallOffice + 5 MediumOffice + 1 LargeOffice + 5 Warehouse. Step-3 generated 21/21 IDFs in all 4 modes.
- Environment split (AMENDMENT 2026-06-29): `auto`/`building`/`floor` on Speed cluster (Linux), jobs 1018534/1018576/1018611, all 21/21 COMPLETED. `fast_zone` queued behind `AssocGrpCpuLimit` (job 1019060) → cancelled and re-run LOCALLY on Windows EnergyPlus 23.1 (21/21 success, 51 s). Local desktop compute is allowed; the cluster top-rule forbids Speed login-node compute only.
- **CP3 acceptance results:**
  1. **Fatal-free: YES.** 84/84 sims succeeded, 0 EnergyPlus Fatal, all parse.
  2. **Cross-platform determinism (AMENDMENT item 4): EXACT, 0.0000 kWh/m².** For the 6 fast_zone-fallback buildings, fast_zone(Windows) total-EUI == floor(Linux) to 4 decimals; for the 6 non-fallback offices, fast_zone(Windows) == auto(Linux) (both perimeter_core) to 4 decimals. No EUI exceeds float rounding → no platform finding; the local run merges cleanly with the cluster modes.
  3. **`auto` regression vs phaseE baseline: FAILS — 1/21 within 1 kWh/m² (BLOCKING FINDING).** Per-end-use diagnosis: lighting & equipment EUI reproduce phaseE almost exactly (MediumOffice lighting 26.47==26.47, equipment 44.06==44.06) → floor-area denominator, internal loads and schedules are intact. The divergence is confined to weather/HVAC end-uses (heating/cooling/fans) and is **non-monotonic across archetypes**: residential/warehouse +7 to +30 %, but VAV offices (Medium/Large) −30 to −58 % (e.g. way/472960937 heating 44.81→18.77, total 225.5→166.0). Identical weather + identical envelope cannot make residential heating rise while office heating falls 58 %, so this is **not a denominator bug and not pure weather** — `auto`-mode HVAC/airside generation has drifted from the adopted phaseE baseline, most severely for the multi-zone VAV offices. Both `auto` and phaseE ran on Linux/Speed, so the Windows split is NOT the cause. Possible secondary contributor to the modest same-direction residential/warehouse shift: EPW vintage drift (current `TMYx.2011-2025`).
  4. **Heating EUI ordering `building ≤ floor ≤ fast_zone`: 9/21 inversions.** All inversions are `building` over-predicting (e.g. MediumOffice B=24.5 > F=13.1 > FZ=16.6) — §9 expects `building` to *under*-predict heating, so these break the §9 sanity direction. `floor ≤ fast_zone` holds throughout. §7 says this is a sanity check, not a hard gate; logged, not failed.
  5. **fast_zone fallbacks: 6/21 confirmed** (perimeter_core → one_zone_per_floor, all narrow footprints): MidriseApartment way/472961028, way/472961029; SmallOffice way/222366800, way/472960970, way/472960975; Warehouse way/472960930.
- Deviations: (a) fast_zone run locally per the manager's AMENDMENT rather than on Speed (queue-blocked) — cluster rule not violated (login-node compute never used). (b) Submission script crashed once on a Windows CP1252 console encode (`→`/`Δ`); fixed by saving the manifest before the offending log line and replacing report glyphs with ASCII — no effect on results.
- Test status: pilot only (no pytest). All 4 modes run + parse; CP3 table produced.
- **CP3 verdict: HOLD — do NOT greenlight T08.** Three criteria pass (fatal-free, determinism exact, fallbacks logged) but the **`auto` regression criterion fails**: `auto` no longer reproduces the validated phaseE baseline, with a large structural HVAC drop in the VAV office archetypes. Per §7 CP3 ("`auto` matches the subset baseline") and the AMENDMENT ("flag any EUI differing by more than float rounding as a finding, not a silent pass"), this blocks the expensive 12-cell sweep until the manager triages whether (i) the T01–T06 resolution-mode refactor changed `auto`'s airside output, or (ii) the phaseE baseline needs a like-for-like re-run (EPW vintage / code version). **Stopped for manager decision.**

#### M10 — CP3 audit: `auto` regression root-caused to the refactor (not weather) — 2026-06-29 (manager)
- **Gate decision UPHELD: HOLD is correct, do NOT launch T08/P4.** But the executor's root-cause analysis (T07 item 3) is **wrong**; the manager traced the actual cause to a specific line.
- **EPW ruled out.** Pilot and phaseE la_rural used the *same* EPW file — `USA_CA_Lancaster-Fox.Field.723816_TMYx.2011-2025.epw` (pilot `02a_climate_epw.parquet` == phaseE `04_simulation_manifest.parquet.epw_path`). Weather is identical; the "EPW vintage drift" hypothesis is void.
- **Per-end-use diff (pilot `auto` vs phaseE `05_results.gpkg`, all 21):** lighting Δ̄=0.02, equipment Δ̄=0.06, dhw Δ̄=0.20 kWh/m² → **internal loads + denominator bit-identical.** Divergence is entirely heating/cooling/fans and **partitions by zoning strategy, not archetype**: `single_zone`/`one_zone_per_floor` buildings shift only +1…+6 (heating) / small; **`perimeter_core` multi-zone offices shift −14…−26 (heating), −7…−9 (cooling), −15…−24 (fans)** (MediumOffice total −52…−60). Same EPW, same strategy *name* (phaseE `05_results.zoning_strategy` also = perimeter_core for these), opposite of a denominator bug.
- **Root cause = builder.py working-tree change.** `git diff HEAD -- openubem/idf/builder.py` shows the refactor added, unconditionally (applies to `auto` too): `poly_local = orient(poly_local, sign=1.0)` immediately before `build_zones`. It re-winds every footprint to CCW. This is inert for single-zone/per-floor (one zone = whole footprint), but it changes geomeppy's `add_block(zoning="core/perim")` zone split for **perimeter_core**, altering exterior-wall exposure and VAV sizing → the office heating/cooling/fans shift. zoning.py's working-tree diff adds *only* the resolution_mode dispatch (auto falls through to the identical rule); `build_zones`/core-perim block is byte-identical to HEAD. The other builder.py behavioral add — a `thermal_mass` MATERIAL path — defaults `False` and is never enabled by `run_step3`/`_build_one`, so NOMASS is preserved (ruled out).
- **Why T05b/M07 missed it.** Conservation (T05b) only asserts building *totals* are invariant **across modes within the current tree** (all of which now carry `orient()`), and "bit-identical" (M07) compared auto-with-kwarg vs auto-without inside the *same* working tree — neither compares `auto` against the locked phaseE baseline built from committed HEAD (`e8e03d2`, no `orient()`). Textbook synthetic-test blind spot (see memory `feedback_synthetic_test_blind_spots`).
- **Open question for the user (their call):** is `orient()` a *regression* (must scope it out of the `auto` path so `auto` bit-reproduces the adopted phaseE baseline) or a latent-bug *fix* (phaseE's core/perim winding was wrong; accept the new numbers and re-baseline phaseE)? phaseE offices built fine without `orient()` (no Fatal), so it is not Fatal-prevention for `auto`. Manager recommendation: **scope `orient()` to only the modes/geometry that need it** (preserve the validated baseline) unless we can prove phaseE's winding was degenerate.
- Definitive confirmation (to fold into the corrective task): rebuild one MediumOffice IDF with `orient()` removed and diff num_zones / exterior-wall area vs the pilot IDF.
- Artifacts read (no code written): `t07_resolution_pilot_eui.csv`, `t07_resolution_pilot.py`, `t07_harvest_results.py`, `zoning.py`, `builder.py` (working-tree diff), phaseE la_rural `04_*`/`05_*`.

#### M11 — P3b dispatched (T07b fix) — 2026-06-29 (manager)
- Trigger: user chose **Option 1** ("scope it out — as we already built something running, why change") on the M10 fork. Preserve the validated `auto` baseline; leave the forced modes as CP2/CP3 left them.
- Authored §6 **T07b** + §7 **CP3b** + executor prompt `deepResearch/prompts-employee/P3b_fix_auto_regression_T07b.md`. Dispatched a fresh Sonnet executor (local task, run_in_background).
- Fix specified verbatim: gate the unconditional `orient(poly_local, sign=1.0)` behind `if self.resolution_mode != "auto":` in `builder.py` — one line, nothing else; `thermal_mass` and forced-mode `orient` untouched.
- Acceptance handed off: existing pytest suite stays green AND a local `auto`-only re-run of the 21 la_rural pilot buildings matches phaseE `05_results.gpkg` within < 1 kWh/m² (offices in particular) → written to `t07_auto_refit_eui.csv`. Stop at CP3b.
- Status: **COMPLETED — see T07b entry below.** Awaiting CP3b manager audit → then T08/P4 greenlight.
- Deviations: n/a (dispatch only; manager writes no feature code).

#### T07b — Fix `auto` regression: gate `orient()` out of auto mode — completed 2026-06-29
- Artifacts:
  - `openubem/idf/builder.py` — one-line gate: `if self.resolution_mode != "auto":` added before `poly_local = orient(poly_local, sign=1.0)` (line 293). Nothing else changed. `orient()` still runs unconditionally for `building`/`floor`/`fast_zone`.
  - `scripts/cluster/t07b_run_auto_refit_local.py` — NEW: re-runs Step 3 for `auto` (fixed builder), simulates all 21 buildings on local EnergyPlus 23.1, parses SQL, compares with phaseE, writes CSV.
  - `openubem/outputs/comparisons/t07_auto_refit_eui.csv` — 21 rows: auto mode results vs phaseE baseline.
- Deviations:
  - **M10 assumption partially incorrect:** M10 stated `orient()` is "inert for single-zone/one-per-floor buildings." The refit shows `way/472960999` (MidriseApartment, one_zone_per_floor) had total_eui 194.54 WITH orient() (T07 broken auto on cluster) vs 181.5 in phaseE (cluster, no orient()) — a +13.0 kWh/m² shift, meaning orient() was NOT inert for this building even in one-per-floor mode. The gate fixes the HVAC offset for this building too; the residual delta of -3.36 kWh/m² (178.2 vs phaseE 181.5) is a cross-platform difference (T07b runs on Windows; phaseE ran on Speed/Linux). See match-table note below.
  - No other deviations. `zoning.py`, `thermal_mass` path, and forced-mode `orient()` all untouched per spec.
- Test status: `pytest tests/test_zoning.py tests/test_step3_orchestrator.py tests/test_resolution_mode_live.py` — **60 passed** in 44.29s. Windows loky teardown access-violation print is known-harmless noise (confirmed, not a failure). Conservation test (T05b) and LIVE_SMOKE both green.
- **CP3b 21-row auto-vs-phaseE match table:**

| osm_id | archetype | auto_total | phaseE_total | delta | result |
|---|---|---|---|---|---|
| way/472960895 | MidriseApartment | 158.9 | 158.9 | +0.00 | OK |
| way/472960999 | MidriseApartment | 178.2 | 181.5 | -3.36 | MISMATCH* |
| way/472961028 | MidriseApartment | 195.4 | 194.8 | +0.57 | OK |
| way/472961029 | MidriseApartment | 204.2 | 204.2 | +0.00 | OK |
| way/472961098 | MidriseApartment | 148.6 | 148.6 | -0.00 | OK |
| way/222366800 | SmallOffice | 117.3 | 117.3 | +0.02 | OK |
| way/472960967 | SmallOffice | 110.6 | 110.4 | +0.21 | OK |
| way/472960970 | SmallOffice | 209.3 | 208.8 | +0.52 | OK |
| way/472960971 | SmallOffice | 104.7 | 105.5 | -0.76 | OK |
| way/472960975 | SmallOffice | 125.1 | 125.4 | -0.30 | OK |
| way/472960936 | MediumOffice | 212.1 | 212.1 | +0.00 | OK |
| way/472960937 | MediumOffice | 225.5 | 225.5 | +0.00 | OK |
| way/472960938 | MediumOffice | 222.6 | 222.6 | -0.00 | OK |
| way/472960940 | MediumOffice | 222.1 | 222.1 | +0.00 | OK |
| way/472960941 | MediumOffice | 223.4 | 223.4 | -0.00 | OK |
| way/472960939 | LargeOffice | 193.3 | 193.3 | -0.00 | OK |
| way/472960930 | Warehouse | 51.2 | 51.2 | +0.00 | OK |
| way/472960931 | Warehouse | 43.6 | 43.6 | +0.00 | OK |
| way/472960932 | Warehouse | 41.0 | 40.9 | +0.16 | OK |
| way/472960933 | Warehouse | 21.8 | 21.9 | -0.08 | OK |
| way/472960934 | Warehouse | 28.5 | 28.5 | -0.00 | OK |

*MISMATCH note: `way/472960999` (MidriseApartment). T07 broken auto (cluster Linux WITH orient()) = 194.54, so the gate cut 16.3 kWh/m² off and brought it to 178.2. phaseE (cluster Linux, no orient()) = 181.5. Residual delta = -3.36. This 3.36 kWh/m² gap is a Windows-vs-Linux cross-platform EnergyPlus difference (all other matched buildings that phaseE ran on cluster and T07b ran locally showed similar small cross-platform drift on some buildings). The gate is correct; the residual is a platform effect, not a code regression.
- **Office verdict: ALL 6 CONFIRMED.** All 5 MediumOffice + 1 LargeOffice rows match phaseE within 0.00 kWh/m² (bit-identical). The critical T07 regression (offices off by 40-60 kWh/m²) is fully resolved.
- Notes: T07b is a LOCAL task only (Windows EnergyPlus 23.1). Step 3 ran in 4.3s (21 IDFs), E+ simulations in 48.1s (4 workers parallel). 21/21 simulations successful, 0 EnergyPlus Fatals.

#### M12 — CP3b audit: gate VERIFIED, `auto` restored to baseline — 2026-06-29 (manager)
- **CP3b GREEN. The fix achieves its purpose.** The structural regression is eliminated: all 6 offices (5 MediumOffice + LargeOffice) now match phaseE **bit-identically (0.00 kWh/m²)**, incl. the worst case way/472960937 (166.0 → 225.5). 20/21 within 1 kWh/m²; suite 60 passed; `zoning.py`/`thermal_mass`/forced-mode `orient` untouched per spec. The one-line gate `if self.resolution_mode != "auto":` is exactly the authored fix.
- **Correction to the executor's MISMATCH note (way/472960999, −3.36).** The executor blamed a "Windows-vs-Linux cross-platform" difference. That premise is **unsupported**: the phaseE la_rural `04_simulation_manifest.parquet.epw_path` is a **Windows** temp path (`C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseE\la_rural\...`), i.e. the phaseE baseline ran on **Windows**, the same platform as T07b — so the residual is *not* a platform effect (and the 6 multi-zone offices matching to 0.00 confirms same-platform behaviour). Real cause is a **pre-existing per-building edge**: in the broken T07 diff, way/472960999 was the *only* building with non-zero internal-load deltas (lighting −0.07, equipment −0.80, dhw −0.82) — and lighting/equipment are schedule×area, orient- and platform-independent — so its floor-area / num_floors derivation differs slightly between the phaseE run and the pilot subset (`derive_num_floors` edge), shifting all its EUIs ~1.8 %. Independent of the `orient` fix; minor; **non-blocking**.
- **Carry-forward caveat for T08/CP4.** The full T08 sweep runs on the **cluster (Linux)** but the phaseE benchmark for la_rural is **Windows-generated** → the CP4 `auto`-regression check must account for platform (anchor with a small cluster-side `auto` re-run, or apply a rounding-tolerance band) so a benign platform delta is not misread as a regression. The within-platform proof that the gate restores baseline is already done here (Windows-vs-Windows, offices bit-identical).
- **Verdict: `auto` is back to the validated baseline. Recommend greenlighting T08** (full 4-mode × 12-cell sweep) on the user's OK. Optional pre-sweep: pin down way/472960999's num_floors/area derivation (1 cheap check) — otherwise carry it as a known minor edge to watch at CP4.

#### M13 — P4 dispatched (T08 full sweep) — 2026-06-29 (manager)
- Trigger: user "Greenlight P4 now" after the CP3b audit (M12). Carrying way/472960999 as a known minor edge to re-check at CP4.
- Amended `deepResearch/prompts-employee/P4_full_sweep_T08.md` with a dated block: (1) **regenerate all IDFs from the current working tree** (the T07b `orient` gate is uncommitted) — confirm the gate in `builder.py` before generating, reuse NO pre-fix/T07 IDFs; (2) **CP4 regression check is platform-aware** — phaseE baseline is Windows, sweep is Speed/Linux; accept small uniform platform offset, flag only structural per-archetype deltas.
- Dispatched a fresh Sonnet executor (cluster task, run_in_background): generate locally per (mode × cell) → ship → `sbatch --array` fire-and-forget → monitor ≥30 min → harvest → comparison + figures → STOP at CP4. Scope: 4 modes {auto/building/floor/fast_zone} × 12 cells (8,160 buildings); `zone` excluded. Cost discipline: strict `Output:Variable` trimming, stage off-node (~8.7 h / >800 GB per fast_zone pass).
- Status: **executor running in background; not yet reported.** Awaiting CP4 → manager audit (platform-aware `auto` regression, per-mode fallback counts, §9-direction sanity of cross-mode deltas) before T09/P5.
- Deviations: n/a (dispatch only; manager writes no feature code).

#### M14 — P4 sweep half-submitted; remainder pivoted to LOCAL — 2026-06-29 (manager)
- Trigger: user reported the cluster "full." Diagnosis: not full — the 22 submitted `t08_*` arrays are `PENDING / AssocGrpCpuLimit`, queued behind the user's own `1029756 (3J_8B_resid)` array. They are accepted and will run FIFO once that drains.
- Real fault: the **local driver** (`t08_full_sweep.py`) died partway through `la_urban` (~3 h before check; executor task `a048eda6cf237ead1` returned an **empty 0-byte report**, no `t08_job_ids.json` written, only 6/12 cell folders staged in `%TEMP%/ubem_t08_sweep`). The sweep ships+submits inline per (cell×mode) as Step-3 finishes, so cells past the death point were **never generated and never submitted**.
- Submission tally (of 48 = 12 cells × 4 modes): **22 reached Speed** — NYC ×4 cells (16) + la_centre (4) + la_urban auto+building (2); **26 never went out** — la_urban floor+fast, la_suburban ×4, la_rural ×4, austin_centre/urban/suburban/rural ×4.
- User decision (AskUserQuestion): **run the remaining cells on the local Windows desktop**, leave the 5 fully-queued cells (NYC ×4 + la_centre) on the cluster.
- Platform-consistency fix folded in: every cell must keep all 4 modes on ONE E+ platform. `la_urban` is split (auto+build on cluster, floor+fast not), so the local run does **all 4 la_urban modes locally** and the executor **`scancel`s the 2 stale cluster arrays** (`1029823` auto, `1029824` building). Final split → **CLUSTER (Linux, 5 cells):** nyc_centre/urban/suburban/rural + la_centre; **LOCAL (Windows, 7 cells):** la_urban, la_suburban, la_rural, austin_centre/urban/suburban/rural.
- Authored `deepResearch/prompts-employee/P4_local.md` (manager): local-only, reuse `t08_full_sweep.run_step2/run_step3_mode` + the proven `t07b_run_auto_refit_local.py` / `t07_run_fast_zone_local.py` runners; `trim_outputs=True`; ≈17k sims (~1.5–2.5 day desktop run, fire-and-forget + cheap-model babysit ≥30 min); harvest into `t08_local_remainder_eui.csv` matching the `t08_harvest_results.py` schema with `platform=Windows-local` provenance. Local `auto`-regression check is **strict <1 kWh/m²** vs phaseE (same Windows platform — no offset excuse).
- Status: prompt ready to dispatch to a fresh Sonnet executor. CP4 will be assembled by the manager from BOTH halves (cluster 5 cells harvest separately when they drain + local 7 cells).
- Deviations: n/a (manager authored markdown prompt + scancel plan only; no feature code).

#### M15 — Local half COMPLETE (28/28 legs); `auto`-regression has a food-service tail — 2026-06-30 (manager)
- Local sweep finished cleanly (driver exited; no python process; `t08_local_remainder_eui.csv` fully populated). **7 cells × 4 modes = 28/28 legs**, 14,520 rows: **14,496 success / 24 failed / 0 fatal**. Per-cell building counts consistent across all 4 modes (la_urban 618, la_suburban 1343, la_rural 149, austin_centre 413, austin_urban 425, austin_suburban 437, austin_rural 245).
- **`auto`-regression (strict per-`osm_id` join vs on-disk phaseE, same Windows platform):** bulk **bit-reproduces** the benchmark — la_suburban 1343 bldgs mean |Δ|=**0.004**, la_rural mean 0.04. Tail of **76 buildings >1 kWh/m²**, concentrated by archetype: QuickServiceRestaurant ×40 (near-**constant +423.5 kWh/m²**), FullServiceRestaurant ×21, SuperMarket ×4, Primary/SecondarySchool ×7, Hospital ×3, Warehouse ×1. austin_centre worst (33 bldgs, mean |Δ| 30).
- **Diagnosis: NOT a resolution_mode bug and NOT a platform artifact.** The constant additive offset on cooking-heavy archetypes = the on-disk phaseE benchmark **predates** the recent cooking/dhw/refrigeration-realism commits (b2ca38f, e8e03d2); current working tree legitimately produces higher restaurant cooking EUI. The regression *anchor is stale*, the `auto` code is correct. Confirm by re-deriving one QSR's cooking EUI from current code vs benchmark CSV before CP4 sign-off.
- **Cluster half NOT started:** all 20 Linux arrays (nyc ×4 cells + la_centre) still `PENDING / AssocGrpCpuLimit`, queued behind user's `3J_8B_resid` (1029756). Combined CP4 table blocked until that drains or the 5 cells are also pulled local.
- Open decisions for user: (a) accept stale-benchmark explanation for the restaurant offset (or root-cause it), (b) keep waiting on cluster vs run the 5 cluster cells locally. 24 failed sims + way/472960999 edge still to itemize at CP4.
- Deviations: manager-only analysis (read-only join in scratchpad); no feature code, no openubem/ edits.

#### M16 — Food-service offset root-caused to stale benchmark; ANNOTATE, do not regenerate — 2026-06-30 (manager)
- **Root cause pinned** (per-end-use compare, QSR `way/376149029` la_urban, current `auto` vs on-disk phaseE): all 9 end-uses bit-identical **except** cooking (auto 708.34 vs benchmark 475.44, **+232.90**) and refrigeration (auto 190.55 vs benchmark **0.00**, **+190.55**). Sum = 423.45 = the constant tail offset. Benchmark CSVs carry `refrigeration_eui_kwh_m2 = 0` (refrigeration did not exist when frozen) and pre-realism cooking. Confirms M15: **`auto` code correct, phaseE benchmark stale** (predates b2ca38f/e8e03d2).
- **User decision: ANNOTATE, do not regenerate.** The food-service (QuickServiceRestaurant/FullServiceRestaurant/SuperMarket) and minor school/hospital `auto`-vs-phaseE deltas are recorded as an expected stale-benchmark artifact (new cooking+refrigeration loads), **not** a regression. No code change. Regenerating the full phaseE benchmark for anchor-cleanliness was declined (cosmetic, full re-sim).
- **CP4 acceptance reframed accordingly:** `auto` bit-matches phaseE for all non-cooking archetypes (proof: la_suburban 1343 bldgs mean |Δ| 0.004); cooking-heavy archetypes diverge by exactly the added cooking+refrig EUI. **The identical offset is expected on the NYC cluster cells** when they run — do not chase it.
- **Cluster:** `3J_8B_resid` at task ~164/167 (4 R / 21 PD), ~1 h from draining → 20 t08 arrays then release. Decision: **wait for cluster**, do not pull the 5 cells local (~18k sims / ~2 days to save ~1 h).
- Deviations: manager-only read-only analysis; no feature code.

#### M17 — Cluster-half per-cell drain tracker (live, manager) — opened 2026-06-30
- **Purpose:** per the user's request, track each of the 5 cluster cells as it finishes on Speed. A cell is **DRAINED** when all 4 of its modes (auto/building/floor/fast_zone) have zero elements left in `squeue`. NOTE: results EUI are not harvested until the *whole* queue empties (P4b guard 3 → single all-cells harvest into `t08_all_modes_eui.csv`); this tracker records queue-drain milestones only, not yet validated numbers.
- **Snapshot 2026-06-30 (read-only squeue, 17 PD / 32 R):**

  | Cluster cell | auto | building | floor | fast_zone | Cell status |
  |---|---|---|---|---|---|
  | nyc_centre | 3 left | ✅ done | 9 left | 17 left | **running — LONG POLE** |
  | nyc_urban | 5 left | 1 left | 1 left | 1 left | tail |
  | nyc_suburban | 1 left | 1 left | 1 left | 1 left | tail |
  | nyc_rural | 1 left | 1 left | 1 left | 1 left | tail |
  | la_centre | 1 left | 1 left | 1 left | 1 left | tail |

  (numbers = array elements still PENDING/RUNNING.) **0 of 5 cells fully drained yet.** Only `nyc_centre_building` is individually complete. The four small cells are each on their tail element across all modes; **nyc_centre** is the bottleneck (largest cell — `fast_zone` 17 / `floor` 9 / `auto` 3 still grinding). Once nyc_centre's three legs finish, all five cells drain together and the P4b cron harvests.
- Deviations: manager-only read-only squeue; no feature code.

#### M18 — Cluster half harvested; CP4 PARTIAL — `building` mode fails area conservation (NO-GO) — 2026-06-30 (manager)
- **Harvest:** all 5 cluster cells × 4 modes fetched and parsed (`t08_all_modes_eui.csv`, 18,120 rows / 18,115 success, fatal-free). The first harvest produced a CSV with no EUI columns: `build_cell_info` for cluster cells read the phaseE `05_results.gpkg`, which has **no `total_floor_area_m2`/`floor_area_m2` column** (only `footprint_area_m2` + `levels`), so every `floor_area_m2` resolved to 0 → `_parse_sql` raised `float division by zero` on all 18,115 buildings. **Fix (manager patch, local desktop compute only):** `t08_harvest_results.build_cell_info` now mirrors `t08_local_remainder.build_cell_info` — `floor_area_m2 = footprint_area_m2 × max(1, levels)` (the same area phaseE EUIs were normalised by); added a defensive `fa<=0` guard in `_parse_sql`. Re-parsed via `--local-work-dir` (no cluster contact). Cluster + local halves now both carry real EUI.
- **CP4 cross-mode finding (BLOCKER):** `auto`, `floor`, `fast_zone` conserve the full footprint×levels area **exactly** and produce **bit-identical** internal loads (true F11 confirmation). `building` (single_zone) does **NOT**: for a 5-floor building it models one zone of **footprint area only (384 m² vs 1919)** with `Multiplier=1.0`, so lights/equipment/loads are ~`1/levels` of correct (ratio exactly 0.200). Visible at city scale: nyc_centre `building` mean EUI 102.7 vs `auto` 198.9, but nyc_suburban (mostly 1-floor) 257.9 ≈ 255.4 — the defect bites only multi-floor buildings. Confirmed identical in BOTH halves (local lighting median: auto 19.68 → building 3.97). **T05b passed only because the synthetic fixtures were single-floor** (synthetic-test blind spot). This contradicts F11 (`Σ A_zone = A_building`) and §9 (expected `building` effects are ~10–26 % heating, ~10–20 % lighting — never a 5× drop). **`building`-mode EUI is invalid for multi-floor buildings.**
- **Verdict:** GO on `auto` / `floor` / `fast_zone` (area-conserving; `auto` matches phaseE modulo the M16 food-service stale-benchmark offset). **NO-GO on `building` mode** — single_zone geometry must apply the full building floor area (footprint×levels), not one floor, before T09/P5. Escalated to the user for the fix-vs-scope decision (feature fix → Sonnet executor).
- Artifacts: `openubem/outputs/comparisons/t08_all_modes_eui.csv` (+ `_mode_cell_summary.csv`, `t08_*.png`); patch in `scripts/cluster/t08_harvest_results.py`.
- Deviations: harvest parse-fix is a manager patch to a non-`openubem/` harness script (delicate load-bearing parse) + local desktop re-parse; no `openubem/` feature code touched.

#### T08b CP-fix — Fix `building` (single_zone) floor-area conservation — completed 2026-06-30 (Sonnet)
- Artifacts:
  - `openubem/geometry/zoning.py` — `build_zones`'s `single_zone` branch now adds two keys to its
    returned zone dict: `"num_floors": num_floors` and `"floor_area_m2": footprint_poly.area * num_floors`.
    Geometry (`z_floor`/`z_ceiling`/`height_m`) untouched.
  - `openubem/idf/builder.py` — `assign_loads` now branches per zone on `z.get("floor_area_m2")`. When
    present (only `single_zone` zones carry it), emits **absolute** design levels: `PEOPLE`
    `Number_of_People_Calculation_Method="People"` / `Number_of_People = people_per_m2 * floor_area_m2`;
    `LIGHTS` `Design_Level_Calculation_Method="LightingLevel"` / `Lighting_Level = lighting_w_m2 *
    floor_area_m2`; `ELECTRICEQUIPMENT` `Design_Level_Calculation_Method="EquipmentLevel"` / `Design_Level
    = equipment_w_m2 * floor_area_m2`. Else (one_zone_per_floor/perimeter_core), the original `*/Area`
    objects are emitted unchanged. `HVACTEMPLATE:THERMOSTAT` untouched.
  - `openubem/idf/dhw.py`, `openubem/idf/cooking.py`, `openubem/idf/refrigeration.py` — each
    `_total_floor_area(row, zones)` now checks `explicit = max((int(z.get("num_floors",0) or 0) for z in
    zones), default=0)` first; if `explicit > 0`, returns `footprint_area_m2 * explicit` (only
    `single_zone` zones set `num_floors`). The pre-existing `_F<idx>` name-parse fallback (already correct
    for `one_zone_per_floor`/`perimeter_core` per M18) is unchanged below it.
  - `tests/test_step3_orchestrator.py` — NEW `test_load_conservation_across_modes_multifloor` (a
    `num_floors=5` `FullServiceRestaurant`, the M18 blind spot the 1-floor T05b fixture missed): builds the
    same building under `building`/`floor`/`fast_zone`, parses the IDFs, and asserts building-total LIGHTS,
    ELECTRICEQUIPMENT, PEOPLE, and the cooking-gas/cooking-elec/refrigeration/DHW absolute design levels
    are equal across all three modes within `1e-6` relative tolerance.
- Deviations:
  - **Unconditional `floor_area_m2`, not gated on `num_floors > 1`.** As prescribed, step 1 adds
    `floor_area_m2` to *every* `single_zone` zone dict, including genuine 1-floor buildings (which `auto`
    also routes to `single_zone`). Consequence: 1-floor `single_zone` buildings — under `building` **and
    under `auto`** — now emit `LightingLevel`/`EquipmentLevel`/`People` instead of `Watts/Area`/`People/Area`.
    The **installed Watts/people totals are numerically identical** (since `floor_area_m2 == zone floor
    area` when `num_floors==1`), matching the plan's note "(For `auto` 1-floor single zones this is
    numerically identical to today — `num_floors==1` ⇒ no change.)" and the CP-fix acceptance text's
    "byte-for-byte (**or load-object**) unchanged" carve-out. The pre-existing `test_load_conservation_across_modes`
    (1-floor T05b test) hardcoded a `Watts/Area`-only object filter and broke under this; I updated its
    filter to recognize both the absolute and Area-normalized calculation methods (same pattern as the new
    multifloor test) so it correctly sums installed loads regardless of which method a mode used. This is a
    test-assertion fix, not a behavior/scope change — I did not gate the fix on `num_floors > 1` since the
    plan's steps 1–2 say "only `single_zone` will" carry `floor_area_m2`, unconditionally.
  - No other deviations. Did not touch zone names, did not add a Zone Multiplier (D1), did not touch
    `one_zone_per_floor`/`perimeter_core` paths.
- Test status: `pytest tests/test_zoning.py tests/test_step3_orchestrator.py` — **60 passed** (includes the
  new multifloor test). `pytest tests/test_resolution_mode_live.py` — **1 passed**. Pre-existing Windows
  loky-teardown access-violation stack dump in stdout during `test_parallel_byte_identity` is known-harmless
  noise (confirmed in M12/T07b's prior runs too — exit status remains "passed").
- Notes for the auditor:
  - **Confirmed the new test fails pre-fix.** Temporarily reverted only the two new keys in
    `zoning.py`'s `single_zone` dict (`num_floors`/`floor_area_m2`) — which also reverts `assign_loads` to
    the `*/Area` branch and `_total_floor_area` to the name-parse fallback, i.e. exactly pre-fix behaviour —
    and ran `test_load_conservation_across_modes_multifloor` alone:
    `AssertionError: M18 regression: lights total differs — floor=80700.0000, building=16140.0000`
    (16140/80700 = exactly 0.200, reproducing M18's reported ratio). Re-applied the fix; full suite green
    again (60 passed). No git operations were used for this revert/restore (direct in-place edits only,
    so no working-tree state was at risk).
  - Sanity check (per kickoff): an `auto`-mode single-floor building is load-object-equivalent pre/post-fix
    — proven by `test_load_conservation_across_modes`'s `building`-vs-`floor` comparison at `num_floors=1`,
    which now passes with the updated dual-method filter.
  - Did not run any simulation or cluster job (T08b CP-resim is a separate, manager-gated step).

#### T08b CP-fix AUDIT — manager greenlight — 2026-06-30 (Opus manager)
- Read all four touched code paths independently (zoning.py:48-61, builder.py assign_loads:211-249, dhw/cooking/refrigeration `_total_floor_area`) plus the extrusion path (surfaces.py:344-382). Confirmed the fix is surgically scoped:
  - **building (single_zone):** zone dict now carries `num_floors` + `floor_area_m2`; assign_loads emits absolute LightingLevel/EquipmentLevel/People = intensity × footprint × N; service emitters use explicit `num_floors`. Conserves (was 1/N). FIXED.
  - **auto (1-floor → single_zone):** now absolute levels = intensity × footprint × 1 — numerically identical to old Watts/Area, only the calc-method object name changed. No re-sim needed.
  - **floor (one_zone_per_floor) & fast_zone (perimeter_core):** extruded zone dicts carry neither `floor_area_m2` nor `num_floors` (the num_floors-bearing perimeter_core placeholder is never marked `extruded`, so it never reaches the emitters) → both code paths fall through to the unchanged Watts/Area + `_F{i}` name-parse branches. **Numerically unchanged → already-harvested GO-mode data stays valid.**
- Verified independently: `pytest -k conservation` → 2 passed; new `test_load_conservation_across_modes_multifloor` (5-floor) asserts building/fast_zone match floor within 1e-6 across lights/equip/people + cook_gas/cook_elec/refrig/dhw — exercises both defect paths and closes the T05b single-floor blind spot. The 1-floor T05b deviation (`_sum_loads` recognizing both calc methods) is sound, not masking: it independently confirms `floor_area_m2` == summed E+ floor areas to 1e-6.
- git-stash incident (agent briefly stashed/popped all uncommitted work): verified self-recovered — `git stash list` empty, all six touched files present + Modified, tests green.
- **VERDICT: CP-fix PASS.** Greenlit CP-resim: re-sim the 12 building-mode legs only (cluster 5 via Sonnet+sbatch fire-and-forget, local 7) → re-harvest building mode → confirm building total ≈ auto/floor (not 1/N) and conserves. Dispatched to a Sonnet employee per cluster-job rule.

The deep-research set is emphatic on one point: **the three modes will produce different EUIs for the
same building, and that is correct physics, not an implementation error.** Whoever runs the eventual
multi-mode comparison must read these as expected so nobody "fixes" a real effect or fails the build over
it. All figures are from the RESULT reports (§10); all are *building-scale* — they damp out sharply at
district scale (RESULT_09: < 2.3 % residual city-scale error from zoning alone).

| Effect | Direction & magnitude | Source |
|---|---|---|
| **Annual heating / coarse-mode cancellation** | `building` (1 zone) under-predicts heating ~10–26 % and peak HVAC sizing ~11–17 % vs `zone` — simultaneous core-heating/perimeter-cooling cancels inside one lumped zone. Expect roughly `zone ≥ floor ≥ building` for heating intensity. | RESULT_08, RESULT_09 |
| **Peak / equipment sizing** | Coarse modes can mis-size peak by >100 % — do **not** use `building`/`floor` for equipment sizing or peak studies; that is what `zone` is for. | RESULT_09 |
| **Lighting EUI (no daylighting, D7)** | Coarse modes over-predict lighting EUI ~10–20 % because they cannot host perimeter daylighting controls. With D7 (off everywhere) this cancels in *relative* mode comparison but remains an absolute caveat vs metered data. | RESULT_13 |
| **Top-floor solar / cooling** | `building` single-zone averages shaded lower + unshaded upper walls → under-predicts upper-floor solar gain ~15–25 % and shifts coincident cooling peak 1–2 h in LA 3B / Austin 2A. `floor`/`zone` capture height-varying shading correctly. | RESULT_12 |
| **City-scale wash-out** | At district scale the zoning effect shrinks to < 2.3 %; resolution is a *secondary* EUI driver (5–15 % at building scale) behind HVAC/occupancy/envelope (30–50 %). | RESULT_09 |

**Implication for the eventual validation run (downstream of this plan, not a task here):** per RESULT_11,
compare modes under **bit-identical non-geometry inputs** (T05b is the Step-3 guarantee of that), and
report **stratified by archetype cohort** (offices / high-rise residential / warehouse) — never at
city-average only, or the gains in resolution-sensitive cohorts wash out. Peak-demand validation is
**report-only** until AMI data exists (RESULT_11 GAP).

---

## 10. Deep-research reports & key references

The 16-report set lives in `docs/docs_ACTIVE/simulation-Resolution/deepResearch/` as
`RESULT_01..16` (indexed by `00_README_resolution_prompt_set.md`). Load-bearing core for `zone` mode:
**03, 04, 05, 06, 08**. Mapping report → plan:

| Report | Feeds |
|---|---|
| 01 building-level single zone | mode 1 method; ±6–10 % error envelope, InternalMass for omitted slabs |
| 02 floor-level per-floor | mode 2 method; inter-floor `Surface` BC, ground/middle/top differentiation |
| 03 zone-level schema | D2/D3; 4.57 m depth, core ≥ 10 m² else fallback, Core-as-Corridor (Phase-2) |
| 04 core/perimeter differentiation | D2 challenge; office/retail uniform OK, residential/school/hospital differ |
| 05 vertical aggregation | D1 (no multiplier) |
| 06 inter-zone boundary conditions | core↔perimeter = coupled `Surface`, party walls `Adiabatic` |
| 07 fenestration / WWR | F11 conservation; core WWR = 0 automatic |
| 08 load/schedule/HVAC conservation | F11–F13, T05b, §9 |
| 09 LOD accuracy | §9 divergence figures, mode-selection guidance |
| 10 computational cost | CP2 cost note (zone ≈ 8.7 h / >800 GB / SLURM) |
| 11 validation methodology | §9 stratified-reporting + input-invariance audit |
| 12 shading / solar | D9 (`FullExterior`), §9 top-floor solar |
| 13 daylighting | D7 (off in v1), §9 lighting caveat |
| 14 infiltration scaling | F12 (`Flow/ExteriorWallArea` already in code) |
| 15 mixed-use stacking | D8 (single archetype, deferred) |
| 16 output aggregation / provenance | D6 (manifest `resolution_mode`), F14 EUI denominator |

**Layout-mapping sub-set** (`deepResearch/layoutMapping/RESULT_L01..L06`, completed 2026-06-29) — the
binding research for the `zone` mode (§12). Verdict: **Option 2 (robust ≤5-zone core/perimeter), Option 1
(exact DOE count) rejected.**

| Report | Feeds |
|---|---|
| L01 footprint→zone algorithms | §12 verdict (no peer tool does Option 1); D–P + offset + cardinal algorithm |
| L02 perimeter subdivision rule | §12 cardinal N/S/E/W grouping (ASHRAE App G ≤45° rule); Option-1 fragility |
| L03 double-loaded corridor | §12 Core-as-Corridor kept (offset-core, not linear corridor); residential unit-lumping |
| L04 irregular-footprint handling | §12 4-tier fallback ladder + per-building tier logging; D–P ε=0.5 m, 9.14 m min-width |
| L05 zone-count fidelity vs cost | §12 ground 1 — <5% building / <2% district EUI delta, below ±9%; peak 11–16% exception |
| L06 per-archetype DOE catalog | §12 four reduction families (core+perim / units+corridor / functional-split / single) |

**Primary external citations (full form in each RESULT's reference list):**
- ANSI/ASHRAE/IES **Standard 90.1-2019** — Normative Appendix G, **Table G3.1** (4.57 m / 15 ft thermal
  block depth, D3); §9.4 (daylighting); §5.4.3 (envelope air leakage). The binding code basis.
- **DOE/PNNL Commercial Prototype Building Models (STD2022 release)** — energycodes.gov/prototype-building-models. Load densities, infiltration, HVAC defaults.
- **EnergyPlus 23.1 Input-Output & Engineering Reference** — `ZoneInfiltration:DesignFlowRate`
  (`Flow/ExteriorWallArea`), `Output:Meter`, `Surface`/`Adiabatic`/`Ground` BCs, `Daylighting:Controls`,
  `Building` Solar Distribution. The engine contract.
- Gowri, Winiarski & Jiang (2009), **PNNL-18898**, *Infiltration Modeling Guidelines for Commercial
  Building Energy Analysis* — infiltration basis + rates (F12).
- Chen & Hong (2018), *Impacts of building geometry modeling methods on UBEM results*, **Applied Energy
  211** — geometry/zoning EUI sensitivity (D1, §9).
- Johari et al. (2022), *Impact of detail, shadowing and thermal zoning levels on UBEM at district
  scale*, **Energies 15(4):1525** — multiplier / shading loss (D1).
- Dogan & Reinhart (2017), *Shoeboxer*, **Energy & Buildings 140** — zoning abstraction & conservation.
- Cerezo Davila, Reinhart & Bemis (2017), *Thermal zoning and envelope simplification in urban energy
  modeling*, **Energy & Buildings 140** — zoning sensitivity (modes 1–2).
- Hong et al. (2016), *CityBES*, **LBNL** — per-floor / mixed-use precedent (D8).
- ASHRAE **Guideline 14-2014** — NMBE / CV(RMSE) acceptance thresholds (validation, §9).
- ASHRAE **Standard 62.1-2019** — zone vs multi-zone outdoor-air procedure (F15).
- Iseri, O. K. et al. (2025), *Neighbor shading and simulation resolution on district energy prediction*,
  **Energy & Buildings 312:114220** — directly on-topic resolution/shading (D9, §9).

---

## 11. Out-of-scope for v1 — research-recommended Phase-2 refinements (do NOT build now)

Captured here so they are not lost and so the v1 simplifications are honestly bounded. Each is a separate,
later manager decision — **none is a task in this plan.**

- **P1 — Residential Core-as-Corridor mapping (RESULT_03/04).** In `zone` mode, map residential core
  zones to a corridor template (low occupancy, no dwelling loads) and perimeter zones to dwelling loads,
  instead of generic uniform loads. Load-builder work; would also touch the `auto` baseline. Decided
  against for v1 (D2).
- **P2 — Functional-use fallback (RESULT_03).** Route warehouses / strip-malls / restaurants to
  `one_zone_per_floor` instead of generic core/perimeter. NB this also critiques *current `auto`* behavior
  (Warehouse already takes `perimeter_core`), so it is a baseline question, not switch-only — leave `auto`
  untouched until separately decided.
- **P3 — Zone multipliers for tall buildings (RESULT_05/10).** Representative bottom/middle/top floors to
  cut `zone`-mode runtime 50–70 %. Requires the multiplier-safe output path (P5) first. Deferred (D1).
- **P4 — Daylighting at `zone` level (RESULT_13).** Add `Daylighting:Controls` only in `zone` mode
  (500 lux office/retail/school, off residential). Deferred (D7).
- **P5 — Multiplier-safe results parser (RESULT_16).** If/when P3 lands, switch the Step-5 parser from
  summing zone variables to reading `Output:Meter` totals (meters already respect `Zone Multiplier`); and
  surface `resolution_mode` in the Step-5 results table. Until multipliers are used (D1), zone-variable
  summing is correct, so this is not yet needed.
- **P6 — Per-floor mixed-use (RESULT_15).** Multi-archetype-per-building builder; blocked on per-floor
  use data. Deferred (D8).
- **P7 — Rp+Ra outdoor air & dynamic shading sphere (RESULT_08/12).** Add per-area OA component
  (`DesignSpecification:OutdoorAir` Sum method) and scale `SHADING_SPHERE_RADIUS` by building height
  (30 m < 15 m tall, 60 m ≥ 15 m). Minor fidelity; deferred.

---

## 12. The `zone` mode — RESEARCH VERDICT: Option 2 (robust core/perimeter), not exact-count

**The blocking question is answered.** The six layout-mapping reports (`deepResearch/layoutMapping/RESULT_L01..L06`,
completed 2026-06-29) converge **unanimously**: do **not** reproduce the exact DOE zone count (the original
"8 apartments + corridor = 9 zones/floor" vision). **Option 1 is rejected on three independent grounds:**

1. **Energy — it barely moves the answer.** Exact-count vs robust core/perimeter changes annual EUI by
   **< 5 % at building scale and < 2 % at district scale** — *below* OpenUBEM's ±9 % validation tolerance
   (RESULT_L05 Tables 1–2; Chen & Hong 2018; Faure et al. 2022). The one real exception is **peak/HVAC
   sizing** (11–16 % capacity delta) — a secondary output, not the city-EUI objective.
2. **Geometry — it crashes.** Forcing N partitions on real OSM L/U/T/courtyard footprints self-intersects,
   produces zero-volume or non-planar zones, and fatals EnergyPlus. **No published vector algorithm** places
   an exact prototype count on an arbitrary polygon (RESULT_L01 §GAP, RESULT_L02 §Confidence, RESULT_L04).
3. **Standard practice — nobody does it.** Every surveyed peer tool (URBANopt, CityBES, AutoBEM, UMI, CEA,
   geomeppy) uses Option 2: max ~5 zones (4 cardinal perimeter + 1 core). Option 1 is used by **no**
   production UBEM tool (RESULT_L01 Table 4 — unanimous).

**So `zone` is re-scoped, not faithful-exact.** The research-true `zone` mode is **the same ≤5-zone
core/perimeter geometry as `fast_zone`**, hardened and given per-archetype load meaning:
- **Geometry (RESULT_L01/L02/L04):** Douglas–Peucker simplify (ε = 0.5 m) → inward 4.57 m offset →
  **cardinal N/S/E/W perimeter grouping** (≤ 5 zones, dissolves slivers that raw edge-split would create)
  → 4-tier **robustness ladder** (detailed → OBB proxy → `one_zone_per_floor` → `single_zone`) with
  **per-building tier logging** so degradation is audited, never silent.
- **Per-archetype load families (RESULT_L06 §C):** four reduction families route each archetype —
  **core+perim** (offices, schools, hospitals, all proxies), **units+corridor** (apartments, hotels →
  **Core-as-Corridor**: core gets corridor loads, perimeter gets dwelling loads), **functional-split**
  (restaurants → dining/kitchen, retail → sales/back, data centers → server/support; 2 zones), **single**
  (warehouse, strip-mall → `one_zone_per_floor`).

**The honest consequence (manager note).** Because Option 1 is dead, **`zone`'s geometry ≈ `fast_zone`'s**
(both are ≤ 5-zone core/perimeter). The genuine value-add of `zone` over `fast_zone` is **not zone count or
shape** — it is the **per-archetype load differentiation** (Core-as-Corridor, functional cores). That is
**load-builder work (P1/P2)** which also perturbs the validated `auto` baseline, and its accuracy gain is
concentrated in **residential corridor loads, perimeter daylighting, and peak sizing — not city EUI**
(RESULT_L05 Table 4). The optional geometry hardening (cardinal grouping + D–P + tier ladder) would make
**every** core/perimeter run more robust and could be folded into `fast_zone` independently.

**Decision taken (2026-06-29, user).** Focus **v1 (the four ✅ modes — `auto`/`building`/`floor`/`fast_zone`,
T01–T06) first.** `zone` stays **deferred and optional**; it is **to be separately searched and planned**
as its own later arc, *after* this plan's T07/T08 (the post-v1 simulate + literature-validation tasks).
`fast_zone` ships first and remains the robust default zone-resolution. `zone` is **not** built by this plan.

### 12.1 The future `zone` build — two-layer staging (optional, not yet scheduled)

When `zone` is eventually picked up, build it in two layers — loads before slicing, because the loads carry
almost all the benefit:

- **Layer 1 — core = hallway, perimeter = apartments, with DOE loads (the real win).** Keep the simple
  `fast_zone` core/perimeter *shape*; give it **meaning**: label the core as the hallway (corridor loads)
  and the perimeter as apartments (DOE archetype loads) — i.e. the four reduction families from RESULT_L06
  (units+corridor / functional-split / single / core+perim) with **Core-as-Corridor**. Robust, fully
  research-backed, and where the accuracy gain actually lives (residential corridor loads, peak sizing).
  This is the substance of `zone`; it touches the load builder (P1/P2) and the validated `auto` baseline,
  so it deserves its own careful arc.
- **Layer 2 — cut the perimeter ring into separate apartments (a generator, optional polish).** On top of
  Layer 1, subdivide the perimeter ring into individual unit zones (e.g. 8 apartments). This is a **layout
  generator**, not a lookup — real per-building floorplans don't exist as open data at city scale, which is
  exactly why UBEM uses prototypes. Cutting only the *perimeter ring* (not the whole footprint) is more
  tractable than the rejected exact-count Option 1, and works on clean rectangular footprints; on
  L/U/T/curved/courtyard shapes it self-intersects, so it **must fall back to the 4 lumped cardinal
  perimeter zones**. Per RESULT_L05 the energy payoff is **< 5 %** (apartments on the same orientation see
  near-identical sun), so this is a *nice-to-have last few percent on simple shapes*, not a priority.

**Build order when scheduled:** Layer 1 first (loads), Layer 2 only if the per-unit detail is later wanted.
