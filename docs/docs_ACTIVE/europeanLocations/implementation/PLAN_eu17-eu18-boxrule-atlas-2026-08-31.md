# PLAN — `EU-18a` see the plans · `EU-17` relax the box rule · `EU-18b` prove them

**Slug:** `eu17-eu18-boxrule-atlas` · **Opened:** 2026-08-31 · **Author:** manager session (Opus).
**Executor:** fresh Sonnet sessions, one dispatch per phase, never resumed for new work.

**Read first, in this order:** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v4.md`
(§1 quote bars, §3 findings 211–214, §4 rulings `D-EU-49`…`D-EU-55`, §5 acceptance) and
`BRIEF_european_locations_v4.md`. Method of record: MVP §4.2–§4.4 (`previous/MVP_european_locations.md`),
`rules/RULES_dwelling_layout_scheme_2026-08-28.html`,
`rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §6 (acceptance shape),
`rules/RULES_context_geometry_simulation_2026-08-30.md`.
**Superseded/cancelled, never executed:** everything under `previous/` and the v3 `PROMPT_*` files.

🔴 **The order is fixed by the owner, 2026-08-31:** *"a la fin nous allons voir des .html ici …\plans3D
je vais donner mon confirmation, apres tu vas continuer la simulation. donc la premiere part des .html"*.
The pages come **first**, from the IDFs that exist today. Then the box rule is relaxed. Then the pages are
regenerated and read. Then — and only on the owner's own sentence — anything simulates.

---

## 1. Hard rules for the executor

1. 🔴 **Nothing simulates.** `D-EU-55`: no EnergyPlus run of any kind — Speed, local, one building, a
   "quick check" — without the owner's explicit permission for that specific wave. Building IDFs,
   parsing them, counting, drawing HTML and running pytest are geometry and proceed freely.
   `run_eu_s2_campaign.py` may only ever be invoked with `--dry-run`. If a task looks like it needs a
   simulation to be validated, **stop and report** with the exact command you would run.
2. 🔴 **Never reduce a declared dwelling count.** 28,189 fleet-wide is a floor, not a ceiling
   (`D-EU-36`, `D-EU-39` §2). A storey that cannot host its count is refused, never approximated down.
3. 🔴 **Measure on the emitted IDF, never on the side-car.** `FINDING 213`: 459 buildings advertise a
   layout the IDF does not carry. Every coverage number this plan produces is read out of the `.idf`
   files. A side-car figure may be quoted only as "side-car says X, IDF says Y".
4. **Fail closed, and name the reason.** A building that cannot be expressed is refused with a specific
   `fallback_reason` and lands in the disclosed residual. Never relabel a refusal as a success, never
   widen a tolerance to make a number pass.
5. **Per district, never pooled.** Every count, percentage and test result is reported for each of the
   four districts separately. A fleet figure may accompany them; it may never replace them.
6. **Real footprints stay real.** Regularization is an internal partitioning aid; the geometry written
   into the IDF keeps the building's own outline. No area is invented or discarded.
7. **Search then register errors.** Before debugging, read `debugs/DEBUG_REFERENCES_european_locations.md`
   and then `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. After any fix, append one bullet to the
   arc file in house format: `- **<exact symptom>** — <root cause>. Fix: <what changed, file:line>. *(source)*`.
   A task is not complete until its entry exists.
8. **Append a progress-log entry per task** under §8 of this document — `#### TXX — <title> — completed
   YYYY-MM-DD`, then Artifacts / Deviations / Test status / Notes. Never edit §§1–7.
9. **Only the files in §3.** No new scripts, docs, notebooks or "helpful extras" outside that list. No
   `.py` under `docs/`. No `.png` outside `openubem/outputs/`.
10. **Stop at the checkpoint, do not continue past it.** Three checkpoints, §7. Approval of one phase is
    not approval of the next.
11. **Do not propose alternatives.** Execute the plan. If the rules or the DESIGN are ambiguous, STOP and
    quote the conflict verbatim.
12. 🔴 **"Our rules" means `docs/docs_ACTIVE/europeanLocations/rules/`, and nothing else.** Three files:
    `RULES_dwelling_layout_scheme_2026-08-28.html` (the scheme), `EXAMPLE_dwelling_layout_validation_2026-08-28.md`
    (the worked example **and the acceptance target** — its §6 list of five conditions on eight named
    buildings is a regression test this plan must still pass at the end), and
    `RULES_context_geometry_simulation_2026-08-30.md` (R1–R9, context geometry). A plan drawn in
    `plans3D/` is "according to our rules" only if it satisfies those documents — not merely if the code
    emitted it without raising.

---

## 2. Measured starting state — do not re-derive, verify only if you doubt it

All measured 2026-08-31 on the artefacts on disk (`STATE_european_locations_v4.md` §3).

**Ruled coverage, from the side-cars** — Madrid 616/961 = **64.10 %**, Lyon 198/297 = **66.67 %**,
London 40/82 = **48.78 %**, Bologna 594/1,204 = **49.34 %**, fleet 1,448/2,544 = **56.92 %**. Bar is
**≥ 95 % per district** (`D-EU-39` §1, restated by `D-EU-50`).

**Refusals by recorded reason, fleet** — `L_SHAPE_DECOMPOSITION_FAILED` 629 (24.72 %),
`INTERIOR_RING_COURTYARD_UNFOLD_FAILED` 239 (9.39 %), `NARROW_FOOTPRINT_LT_8M` 144 (5.66 %),
`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` 75 (2.95 %), `PARTITION_AUDIT_FAILED` 9 (0.35 %);
all refusals 1,096 (43.08 %). ⚠ These are *recorded* reasons and are not the whole truth — see §5 fact 6.

**What the IDFs actually contain** — one undivided zone per floor: Madrid 520 (54.11 %), Lyon 151
(50.84 %), London 60 (73.17 %), Bologna 824 (68.44 %), fleet **1,555 (61.13 %)**. Carrying a circulation
zone: 188 / 57 / 13 / 324 = 582 (22.88 %). Side-cars claiming a core: 1,041. **Divergent: 459**
(Madrid 175, Lyon 52, London 18, Bologna 214).

**Other pinned facts** — 46 single-storey buildings (Madrid 19, Lyon 6, London 0, Bologna 21), 3 of them
carrying a core today. Shading geometry on 2,544/2,544. Adiabatic 89.4 / 86.5 / 70.7 / 80.7 %.
conditioned/gross on the 582 cored buildings: 0.9551 / 0.9598 / 0.9083 / 0.9359, minimum 0.5189.
`floor_area_m2 == gross_footprint_area_m2` on 2,544/2,544 rows (`FINDING 214`).

**Suite baseline** — `pytest -q -n 8 tests/` → 2,345 passed / 55 skipped (~7 min). Two known pre-existing
failures in `tests/test_eu_real_footprint_feasibility.py` (`EU-13B` §10) are untouched by this plan.

---

## 3. File layout — the only files this plan may touch

**Edited (existing):**
- `openubem/geometry/european_residential.py` — the layout routes and their gates (T05–T08).
- `scripts/run_eu_s2_district_campaign.py` — `_geometry()`, the manifest columns (T09, T11).
- `scripts/run_eu_s2_campaign.py` — the reroute gate (T09) and its post-extrude at-risk fallback tier,
  `:516-534` (T15, `D-EU-58`). **Never invoked without `--dry-run`.**
- `openubem/idf/surfaces.py` — `_force_reroute_room_layout_to_one_zone_per_floor` (T09).
- `scripts/emit_eu11_layout_sidecars.py` — parity with the IDF path (T09).

**Created (new):**
- `scripts/eu_idf_plan_reader.py` — the IDF → floor-plan reader shared by T02, T03, T12.
- `scripts/eu18_emit_plan_pages.py` — writes the `plans3D/` pages.
- `scripts/eu18_parity_gate.py` — IDF ↔ side-car ↔ manifest gate, exit code 1 on any divergence.
- `scripts/eu17_refusal_census.py` — the deep refusal census.
- `scripts/eu17_reroute_trace.py` — T14's diagnostic trace, side-effect-free (`D-EU-57`).
- `tests/test_eu_idf_plan_reader.py`, `tests/test_eu17_relaxed_layout.py`.

**Written to (outputs):**
- `docs/docs_ACTIVE/europeanLocations/plans3D/` — `index.html`, `PLANS_<district>.html`. Nothing else
  ever writes here (`D-EU-54`).
- `openubem/outputs/eu_evidence/EU-17/` — the census CSVs and the rebuilt district trees.
- `openubem/outputs/eu_evidence/EU-18/` — parity-gate reports.
- `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` — one bullet per fix.
- §8 of this document.

**Forbidden:** `openubem/outputs/eu_evidence/EU-11/**` (today's IDFs — read-only, they are the evidence
the first pages are drawn from), everything under `previous/`, the v3 `PROMPT_*` files, `docs/docs_main/`,
`docs/docs_step*/`, root `main.py`, any OVERVIEW or DESIGN document.

---

## 4. Dependency decisions (pinned — do not revisit)

1. **Interpreter:** `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`, run from the repo root
   as `python -m scripts.<module>`. **No new third-party package** is installed by this plan.
2. **IDF reading is a plain text parse, not eppy.** 2,544 files × an eppy IDD load is hours; the objects
   needed (`ZONE`, and `BUILDINGSURFACE:DETAILED` whose Surface Type is `floor`) are trivially parseable.
   `scripts/eu_idf_plan_reader.py` therefore reads text, and T01 proves it against eppy on 20 buildings.
3. **Zone taxonomy comes from the zone name**, which the emitter guarantees
   (`european_residential.py:1838-1903`): `<stem>_F<i>_dwelling_<k>` = conditioned dwelling,
   `<stem>_F<i>_circulation` = unconditioned core/corridor, `<stem>_F<i>_whole` = massing-box fallback.
   A name matching none of the three is an error, not a default.
4. **Coordinates are absolute projected metres** (UTM, per district CRS). The reader translates each
   building to its own local origin (subtract the storey-0 centroid) and rounds to **1 cm** before
   anything reaches the HTML. Absolute coordinates are never published in the pages.
5. **The pages are self-contained.** One `.html` per district: inline `<style>`, inline vanilla JS,
   inline SVG, one embedded JSON blob. **No CDN, no external script, no network fetch, no image files** —
   the folder must work opened from disk with no internet. Plotly and three.js are not used.
6. **Page size budget: ≤ 25 MB per district file.** Bologna (1,204 buildings) is the binding case. Hit it
   with 1 cm ring precision, storey-0 thumbnails in the list, and the full storey stack rendered only for
   the selected building. If a district still exceeds the budget, split it as
   `PLANS_<district>_part<N>.html` linked from the district page — never by dropping buildings.
7. **Districts and their trees:** `ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`,
   `IT-BOL-GALVANI2`, each at `openubem/outputs/eu_evidence/EU-11/<district>/` with `idfs/`,
   `prepared_buildings.csv` (join key: `building_id` ↔ `stem`) and `layouts/` side-cars.
8. **Rebuilds go to a new tree**, `openubem/outputs/eu_evidence/EU-17/<district>/`, via
   `python -m scripts.run_eu_s2_district_campaign --district <D> --out openubem/outputs/eu_evidence/EU-17/<D>`.
   That script builds IDFs and a manifest and **does not simulate**. EU-11 is never overwritten.
9. **Tolerances are not tuning knobs.** `REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION = 0.02`,
   `CIRCULATION_FRACTION_OF_PLATE = 0.09`, `CORRIDOR_SPINE_WIDTH_M = 1.80`,
   `minimum_facade_contact_m = 2.5` and `RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 8` keep their values.
   Coverage is won by **expressing more shapes**, never by loosening an acceptance threshold. Changing one
   of these numbers is a STOP.

---

## 5. Facts with citations the tasks depend on

1. **The route dispatch.** `classify_building_morphology` (`european_residential.py:426`) works on the raw
   footprint: a courtyard (interior ring) → `courtyard_secondary`; else a 0.5 m-denoised convex-hull
   deficit **> 3 %** (`:453`) with a reflex vertex → `l_shape_decomposition`; else length/width ≥ 2.0
   (`LINEAR_GALLERY_ASPECT_THRESHOLD`, `:45`) → `i_shape_linear_gallery`; else `point_block_grid`.
2. **The refusal funnel.** `generate_european_ruled_storey_layout` (`:855`) short-circuits
   `dwelling_count == 1` (whole plate, `ruled_grid_1x1`, no gate applies) and `== 2` (a bisection, no
   morphology dispatch). Above that: courtyard failure → `_secondary(...)`; the L-shape route tries up to
   three wing candidates and, if all fail, `return _secondary("L_SHAPE_DECOMPOSITION_FAILED")` (`:983`);
   then regularization refuses beyond 2 % (`:986`); then a grid/gallery partition failure →
   `_secondary("PARTITION_AUDIT_FAILED")`.
3. **`_secondary` never succeeds.** It runs the legacy strip cutter for its geometry but always returns
   `dwelling_layout_emitted=False` (`:890-911`, `D-EU-39` §2 / `EU-15` T04), so
   `generate_european_building_dwelling_layout` (`:1738`) fails the **whole building** closed to
   `one_zone_per_floor` (`:1784-1795`). 0 side-cars carry `equal_strip_multi_angle_sweep` — confirmed.
4. **The building-level cap.** `observed_max_per_floor > 8` refuses before any geometry is attempted
   (`:1754-1761`). This is a **table** limit (`FINDING 202`), not a shape limit; `D-EU-50` explicitly does
   **not** relax it — London's 21.95 % sits behind it and needs its own owner decision.
5. **Circulation is carved by every route** — grid (`:309`), courtyard (`:739`), gallery (`:783`), and the
   L-shape per wing then combined (`_combine_wing_results:594`) — whenever a storey has ≥ 2 dwellings
   (`CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION = 2`, `:43`). The L-shape combine is called with
   **`keep_circulation_polygon=False`** (`:977`), which keeps the area and throws away the drawable ring
   (`:634`). Today that costs nothing (0 floors carry area with a null polygon); after T05 it would
   silently un-draw every new L-shape core.
6. ⚠ **The recorded `fallback_reason` is not always the true cause.** `_secondary` stores
   `legacy.fallback_reason if legacy.fallback_reason else reason_hint` (`:908`) — so when the legacy strip
   cutter *also* failed, **its** reason is kept and the ruled route's reason is lost. The legacy reason
   travels from `assess_european_floor_layout_feasibility` (`:1313`, narrow gate `:1345-1350`) through
   `generate_european_dwelling_layout` (`:1469`, `:1492`, `:1647`). Consequence: `NARROW_FOOTPRINT_LT_8M`
   (144) and `PARTITION_AUDIT_FAILED` (9) may be masking an upstream morphology refusal, and the 629
   L-shape count is a **lower bound**. T04 exists to replace that table with the truth.
7. **The 8 m narrow gate is a feasibility-layer gate**, `NARROW_FOOTPRINT_THRESHOLD_M = 8.0` (`:1008`),
   used at `:1210` and `:1345`. It is not applied inside the ruled routes; it reaches the side-cars only
   through fact 6.
8. **Both layers call the same generator.** `scripts/run_eu_s2_district_campaign.py:_geometry` (`:112`)
   and `scripts/emit_eu11_layout_sidecars.py:237` both call
   `generate_european_building_dwelling_layout`. The divergence of `FINDING 213` is therefore **not** in
   the generator: it happens **after**, inside IDF assembly.
9. **Where the divergence happens.** `build_idf_for_building` runs the `FINDING 210` safety net after
   extrusion — `find_mismatched_interzone_pairs` / `_has_near_duplicate_vertex_surfaces`, then
   `_force_reroute_room_layout_to_one_zone_per_floor` (`scripts/run_eu_s2_campaign.py:516-534`,
   implemented at `openubem/idf/surfaces.py:640`), which unions the storey-0 sub-zones into one block per
   floor **and drops the circulation zone with them**. The write-back into `geometry_outcome`
   (`run_eu_s2_district_campaign.py:387-390`) exists but was added 2026-08-31, after these IDFs were
   built: only 2 of the 459 disclose it. The side-car emitter never learns of it at all.
10. **Areas.** `european_building_layout_area_summary` (`:1904`) returns `(gross, conditioned)` already
    summed over storey groups — **not** per storey. The conservation identity is
    `conditioned + circulation = gross` (max relative error measured: 1.2 × 10⁻⁶). Multiplying by the
    storey count is the classic wrong check and produces nonsense.
11. **The denominator.** `run_eu_s2_district_campaign.py:408-418` assigns `floor_area_m2` the **gross**
    sum; both areas are published beside it. `D-EU-39` §3 ruled that the EUI denominator moves to the
    conditioned area (`FINDING 214`).
12. **Circulation is a two-tier rule, and the two tiers conflict.** `rules/EXAMPLE_…md` §2.3, from MVP
    §4.3: **≥ 5 dwellings/storey → a 1.80 m double-loaded corridor spine on the long axis; 2–4
    dwellings/storey → a centroidal stair core**, sized 6–12 % of the plate *and* 12.0–25.0 m². Those two
    sizing conditions can both hold only for plates of **100.0–416.7 m²**; on the 2,544 prepared buildings
    **1,602 (63.0 %)** are inside that window, 542 are too small and 400 too large (`FINDING 204`). The
    code lets the percentage win — `CIRCULATION_FRACTION_OF_PLATE = 0.09` (`:37`) — which is the
    prototype's choice and **is not ruled**. Nothing in this plan resolves it; every building whose core
    leaves the 12.0–25.0 m² band is **tagged**, and the tag is shown on its page so the owner can rule.
13. **The acceptance sheet is a regression test.** `rules/EXAMPLE_…md` §6: eight named buildings —
    `way/51781396` (London), `relation/12704090`, `way/388485191`, `way/420409335`, `relation/3730743`,
    `way/391279229` (Madrid), `BATIMENT0000000240879941_part0`, `BATIMENT0000000240880045_part0` (Lyon) —
    must reproduce the ruled zone count **exactly**, 0.00 % plan-area error, a circulation zone on every
    storey carrying ≥ 2 dwellings, smallest facade contact ≥ 2.50 m within 0.05 m of §3.1, and
    `relation/3730743` still **refused** with `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` and zero zones.
    T05–T08 must not break any of the five; `D-EU-50` does not relax the density cap, so the refusal
    stays a refusal.

---

## 6. Task list

### `EU-18a` — see the plans that exist today (no change to the geometry code)

#### T01 — IDF floor-plan reader
- **What.** `scripts/eu_idf_plan_reader.py`: given a district tree, return per building a record —
  `stem`, `building_id`, a per-storey list of zones `{name, kind ∈ {dwelling, circulation, whole}, ring}`
  in local cm-rounded coordinates, plus storey count, dwelling count, gross and conditioned area computed
  from the rings themselves, and the manifest's `geometry_outcome`.
- **Why.** Every later task — pages, parity gate, coverage census — must read what actually ran (rule 3,
  facts 8 and 9). One reader used by all three, so they cannot disagree with each other.
- **How.** Text parse per §4.2 and §4.3: collect `ZONE` names, then every `BUILDINGSURFACE:DETAILED`
  whose Surface Type is `floor`, keyed by Zone Name; take its vertex ring and drop Z. The storey index is
  the `_F<i>_` fragment of the zone name. Join `prepared_buildings.csv` on `stem`. Never load eppy.
- **How to test.** `tests/test_eu_idf_plan_reader.py`: on 20 buildings spanning all four districts and all
  three zone kinds, the reader's zone-name set and per-zone ring areas equal eppy's to 1 × 10⁻⁶ relative;
  a synthetic IDF with an unknown zone-name pattern raises. Report the 20 stems used.

#### T02 — the `plans3D/` pages, from today's IDFs  🔴 **this is the owner's "premiere part"**
- **What.** `scripts/eu18_emit_plan_pages.py` writes `plans3D/index.html` and
  `plans3D/PLANS_<district>.html` for all four districts, from the **EU-11** IDFs as they stand.
- **Why.** `D-EU-54`: the owner sees the plans before anything simulates, and `EU-17` gets a visual
  instrument instead of a percentage. Drawn from the IDF, so `FINDING 213` is visible rather than hidden.
- **How.** Per district page: a header stating the source tree, its build date and the district totals; a
  searchable, filterable list of every building (filters: ruled / massing box, has core / no core, storey
  count, scheme, refusal reason); a storey-0 SVG thumbnail per building; on selection, the full storey
  stack drawn one plan per storey with dwelling polygons filled, the circulation ring hatched and
  labelled, a north arrow and a metric scale bar. Per building show `building_id`, stem, storeys,
  dwellings, scheme, `geometry_outcome`, gross m², conditioned m², circulation share as a % of the plate
  with the `FINDING 204` out-of-band tag where the core leaves 12.0–25.0 m², the smallest facade contact
  per storey, and — where refused — the reason plus the sentence *"simulated as one undivided zone per
  floor"*. The sheet conventions of `rules/EXAMPLE_…md` §2 are what these drawings follow. `index.html` links the four pages and
  carries the four headline percentages. 🔴 **Content rule (`D-EU-54` §2): no EUI, no demand, no
  EnergyPlus output, no run or job id, no weather — not in the page, not in the JSON blob, not in a
  tooltip.**
- **How to test.** Open each of the four with the network disabled: the list length equals the district's
  IDF count (961 / 297 / 82 / 1,204); a building known to be a massing box renders one polygon per storey;
  a building known to carry a core renders the hatched ring. Run a content grep for the forbidden terms
  (eui, kwh, energyplus, heating, cooling, epw, job) over `plans3D/*.html` and report the exact command
  and its count — it must find nothing but the labels this plan itself names. Report each file's size
  against the 25 MB budget.

#### T03 — parity gate (report-only in this phase)
- **What.** `scripts/eu18_parity_gate.py`: for every building compare the IDF (T01) against the side-car
  and the manifest — zone-name sets equal, circulation presence equal to `has_unconditioned_core`, scheme
  equal, storey count equal, areas equal to 1 × 10⁻⁶. Writes
  `openubem/outputs/eu_evidence/EU-18/parity_<district>.csv` and a summary, and exits 1 on any divergence.
- **Why.** `FINDING 213` is the arc's third occurrence of this defect class (after `FINDING EU-12-01` and
  the `D-EU-35` desync). A gate that compares the two *generators* cannot see it; only one that reads the
  emitted IDF can.
- **How.** Reuse T01. One row per building, one column per check, plus the divergence class.
- **How to test.** Run it now, on EU-11: it must reproduce **459** divergent buildings (175 / 52 / 18 /
  214) and exit 1. If your number differs from 459, **STOP and report** — do not adjust either side to
  make them agree.

### 🔴 Stop-and-report 1 — after T03. The owner reads the pages. Nothing else starts.

### `EU-17` — relax the box rule

#### T04 — the deep refusal census
- **What.** `scripts/eu17_refusal_census.py`: replay `generate_european_building_dwelling_layout` on all
  2,544 footprints and record, for each refused building, the **true** cause — route taken, which wing
  failed, which gate fired, at what depth — not the reason field. Output
  `openubem/outputs/eu_evidence/EU-17/refusal_census.csv` plus a per-district summary.
- **Why.** Fact 6: the published cause table is contaminated by the legacy cutter's own reason. T05–T08
  must be designed against the real distribution, not the recorded one.
- **How.** Call the module's routes directly from the census script; do not add shipping log lines to the
  library. Record `stem`, district, route, reflex count, hull deficit, minimum rotated width,
  dwellings/floor, storeys, and the ordered list of gates evaluated with each outcome.
- **How to test.** Refusal totals reproduce §2 exactly (345 / 99 / 42 / 610). The new cause distribution
  is reported beside the old one, per district, naming how many buildings were reclassified and into what.

### 🔴 Stop-and-report 2 — after T04, before any change to `european_residential.py`.

#### T05 — wing decomposition that cannot refuse the whole building
- **What.** Make `l_shape_decomposition` express L, U, T and cross plates: split at **every** reflex
  corner (not one), recurse per wing, and when a wing cannot host its allocated count **re-allocate**
  across wings or re-split — refusing the building only when every candidate decomposition is exhausted.
  Also set `keep_circulation_polygon=True` on the L-shape combine (`:977`) so wing cores stay drawable.
- **Why.** The single largest cost in the fleet, ≥ 24.7 % of every district (fact 2, `D-EU-50` §1).
- **How.** Extend `_split_at_reflex_vertex` and `_l_shape_wings` (`:477`, `:534`) to produce an ordered
  candidate set of ≥ 2 wings; keep `_allocate_wing_dwelling_counts` (`:566`) area-proportional but allow a
  ±1 rebalance pass; `_combine_wing_results` keeps its audit and its 2.5 m facade gate unchanged.
- **How to test.** New unit tests in `tests/test_eu17_relaxed_layout.py` on synthetic L, U, T, cross and
  double-L plates at 3–8 dwellings/floor: layout emitted, dwelling count exact, partition audit passed,
  circulation polygon **not None**, areas conserved to 1 × 10⁻⁶. Then re-run T04's census and report the
  L-shape refusal count before and after, per district. `pytest -q -n 8 tests/` stays at baseline.

#### T06 — courtyard unfolding hardened
- **What.** Carry `courtyard_secondary` to a layout on the plates it currently refuses (239 fleet-wide,
  13.2 % of Bologna): the perimeter ring is unfolded into wings and partitioned per wing, with the void
  kept as a hole in the plate and never counted as dwelling area.
- **Why.** Bologna's dense perimeter blocks are that district's second-largest refusal class.
- **How.** `generate_european_courtyard_layout` (`:724`) and `_courtyard_wings_and_nodes` (`:665`); reuse
  T05's re-allocation. Corner nodes stay single dwellings.
- **How to test.** Unit tests on a square ring, a rectangular ring, an off-centre void and an open
  U-court; the void area appears in neither dwelling nor circulation area, and gross − void = conditioned
  + circulation to 1 × 10⁻⁶. Census delta reported per district.

#### T07 — narrow plates (< 8 m) get a corridor-free rule
- **What.** A plate whose minimum rotated width is below `NARROW_FOOTPRINT_THRESHOLD_M` is partitioned
  **across its length**, dual-aspect, with **no corridor spine** — access from the stair core only, or
  from the street for a single-dwelling storey. It stops being a refusal.
- **Why.** 11.2 % of Bologna plus Lyon's terraced stock; a 1.80 m spine in a 6 m plate is what makes the
  rule impossible, not the shape itself.
- **How.** Keep the constant at 8.0 (§4.9) and change what it *selects*: a narrow branch inside
  `generate_european_ruled_storey_layout`, reachable also from a wing produced by T05. Core sizing stays
  `CIRCULATION_FRACTION_OF_PLATE`, the corridor is omitted; if the core alone would exceed the plate's
  habitable share, the storey is refused with a new named reason. ⚠ Fact 12: MVP §4.3 asks for a 1.80 m
  spine at ≥ 5 dwellings/storey, which a < 8 m plate cannot host — that is `FINDING 204`'s conflict in its
  sharpest form. Do **not** resolve it by inventing a rule: emit the corridor-free layout, tag the storey
  `CIRCULATION_SPINE_OMITTED_NARROW_PLATE`, show the tag on the page, and report the count per district
  at Stop-and-report 3 for the owner to rule.
- **How to test.** Unit tests at widths 5 / 6 / 7 / 7.9 m × 1–4 dwellings: emitted, no corridor polygon,
  facade contact ≥ 2.5 m each, areas conserved. Census delta per district.

#### T08 — `D-EU-49`: one storey ⇒ no circulation
- **What.** A building whose `floor_allocations` has length 1 carries **no circulation zone**: the whole
  plate is conditioned and its dwellings partition it without a carve.
- **Why.** `D-EU-49`. A stair core exists to connect storeys.
- **How.** Gate at the building level (`generate_european_building_dwelling_layout:1738`) so both the IDF
  path and the side-car emitter inherit it (fact 8) — never inside a single route.
- **How to test.** The 3 named buildings lose their core and keep their dwelling count: `way/340701289`
  (Madrid, `ruled_grid_3x2`), `BATIMENT0000000240881213_part0` and `BATIMENT0000000240881531_part0`
  (Lyon). Fleet: 46 single-storey buildings, **0** with a circulation zone, and every multi-storey
  ≥ 2-dwelling building still carries one. Report both counts.

#### T09 — kill the IDF/side-car divergence at the source (`FINDING 213` → 0)
- **What.** (a) Make the reroute rare by construction: the 1 mm ring snap already exists, so find why the
  interzone pairs still mismatch on these buildings and fix the geometry that feeds them. (b) Make any
  surviving reroute **loud**: it writes `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` into the
  manifest **and** the side-car for that building is regenerated from the IDF, so no layer can advertise a
  layout that did not run.
- **Why.** Third occurrence of this class; the acceptance bar is measured on IDFs precisely because of it.
- **How.** `scripts/run_eu_s2_campaign.py:516-534`, `openubem/idf/surfaces.py:640`,
  `scripts/run_eu_s2_district_campaign.py:387-390`, `scripts/emit_eu11_layout_sidecars.py`. 🔴 A
  Python-only geometric check is **not** proof that a reroute was unnecessary — this arc has already had
  one false-green on exactly that shortcut (`T09-FINDING210-ROOTCAUSE-FIX-V2`). Where proof needs
  EnergyPlus it belongs to T13 and stops here.
- **How to test.** After T10's rebuild, `eu18_parity_gate.py` returns **0** divergent buildings in all
  four districts and every rerouted building is labelled as such in both layers. Report the reroute count
  per district — a low count is the goal, an undisclosed one is a failure.

#### T10 — rebuild all four districts and census the coverage on the IDFs
- **What.** Rebuild into `openubem/outputs/eu_evidence/EU-17/<district>/` (§4.8) and measure ruled
  coverage **from the IDFs** with T01's reader.
- **Why.** `D-EU-50` §2: the ≥ 95 %-per-district bar is proven on the emitted IDFs, not on side-cars.
- **How.** One district at a time; report the exact command and the wall-clock per district. That script
  builds IDFs and never simulates. Then report, per district: ruled %, refused % with the residual listed
  by named reason, buildings carrying a core, dwelling-count conservation against the starting 28,189, and
  area conservation per building.
- **How to test.** Ruled ≥ 95 % in each of the four districts; `FINDING 213` count 0; single-storey cores
  0; no dwelling count reduced anywhere; `conditioned + circulation − gross` ≤ 1 × 10⁻⁶ relative per
  building; full suite at baseline. **Plus the rules regression (fact 13):** all five conditions of
  `rules/EXAMPLE_…md` §6 still hold on the eight named buildings, reported one line each.
  **A district below 95 % is a STOP, not a rounding discussion.**

#### T11 — settle the EUI denominator (`FINDING 214`, `D-EU-39` §3)
- **What.** Add `eui_denominator_m2 = conditioned_floor_area_m2` to the district manifest and record, in
  §8, the per-district ratio distribution it implies. `floor_area_m2` keeps its current meaning so that
  nothing downstream changes silently.
- **Why.** `D-EU-39` §3 ruled the denominator moves; STATE v4 §5 acceptance item 5 requires it settled in
  writing, either way.
- **How.** `scripts/run_eu_s2_district_campaign.py:408-418`, one added column, no recomputation of any
  existing figure. **No EUI is recomputed and nothing is simulated in this task.**
- **How to test.** All rows carry the new column; it equals the conditioned area on 100 % of rows, and the
  gross area only where the two are genuinely equal. Report the four means and the four minima.

### `EU-17a` — root-cause the T10 STOP before anything downstream runs (`D-EU-57`, owner ruling 2026-09-01: option (a))

#### T14 — diagnose the population loss (`FINDING 220`) and the rules-regression collapse (0/8)
- **What.** Diagnosis only, no fix applied yet unless it is a plain code-bug repair fully inside the
  files already editable under §3 — never a tolerance change (§4.9) and never a new fallback tier or
  behaviour change, both of which are design decisions and must be STOPPED and reported, not invented.
  Sample: the 8 named rules-regression buildings from T10's report, plus a stratified sample of 10
  `interzone_vertex_mismatch_unresolved` losses per district (40 total) drawn from the T10
  `openubem/outputs/eu_evidence/EU-17/<district>/` build logs. For each sampled building, trace and
  record: (1) did `find_mismatched_interzone_pairs` or `_has_near_duplicate_vertex_surfaces`
  (`openubem/idf/surfaces.py:547`, `:640` region) fire pre-reroute; (2) did
  `_force_reroute_room_layout_to_one_zone_per_floor` attempt the rebuild, and did the shapely
  `unary_union`/buffer round-trip (`surfaces.py`, same function) produce a valid hole-free `Polygon`,
  return `False` (multipart/degenerate), or return `False` on the courtyard-hole guard; (3) for a
  building where the reroute *did* succeed, did the post-reroute residual check still fire, and on
  which of `mismatched` / `near_duplicate_vertex`; (4) for the 8 rules-regression buildings
  specifically, confirm whether they were rerouted-and-survived (0 dwelling zones, the T10-reported
  symptom) or lost outright, and which of (1)-(3) explains it.
- **Why.** `D-EU-57` (owner, 2026-09-01): continue the arc past the T10 STOP without T12/T13 running on
  a generator that loses 24.9 % of the population and reroutes ruled buildings to massing boxes.
  `T12`/`T13` cannot honestly show the owner plans built from a generator in this state. This task
  answers *why* the reroute safety net's residual rate rose from EU-11's 0 losses to EU-17's 633,
  before any remedy is designed.
- **How.** Instrument the four functions above with one debug entry point (a new, separate script,
  e.g. `scripts/eu17_reroute_trace.py`, reading the same footprints T10 built from) rather than editing
  the campaign path itself for tracing — keep the diagnostic side-effect-free. Compare EU-11 vs EU-17
  zone counts per sampled building (T05/T06 wing search and T09 ruled-grid partitioner both add
  zones — confirm whether the loss rate correlates with zone count, which would point at the shapely
  union/reroute path rather than at geomeppy's `intersect_match` itself). If the trace lands on a
  concrete, narrow bug fully inside `openubem/idf/surfaces.py`'s reroute function (not geomeppy, not a
  tolerance, not a new fallback tier), fix it and re-run `run_eu_s2_district_campaign` (no simulation,
  per dependency decision §4.8) on the same 40 + 8 sample to confirm the loss/regression clears on that
  sample — do **not** re-run all four full districts inside this task. If the trace lands anywhere else
  (geomeppy internals, a tolerance, a needed new fallback tier such as "never lose a building outright,
  degrade to a box instead"), STOP and report the specific decision needed, per rule 11 — do not invent
  or apply it.
- **How to test.** Report the 48-building taxonomy as counts against the four stages above, per
  district; the 8 named buildings each get their individual stage-by-stage trace, named. If a fix was
  applied, report before/after on the 48-building sample only (built/lost/rerouted-to-zero-dwellings
  counts) and the full suite bar (`pytest -q tests/`, serial, `-n 8` known to crash in this environment
  per T10's note).

### 🔴 Stop-and-report 4 — after T14. The director audits; T12/T13 do not start until this STOP is
cleared, either by a landed fix confirmed on the sample or by an owner ruling on the reported decision.
Cleared 2026-09-01: owner ruling `D-EU-58`, option (a) — add the fallback tier, task T15.

### `EU-17b` — apply `D-EU-58` before `EU-18b` runs

#### T15 — the fallback tier: retain a structurally-boxed building instead of losing it
- **What.** In `scripts/run_eu_s2_campaign.py`'s post-extrude at-risk gate (`:516-534`): when
  `_force_reroute_room_layout_to_one_zone_per_floor` returns `False` (`did_reroute is False`) **and**
  the *raw* `find_mismatched_interzone_pairs` check (`mismatched`) never fired — pre- or
  post-reroute-attempt, it is the same variable either way when no reroute ran — do not `raise`. Retain
  the building's already-emitted geometry as-is and record an explicit `fallback_reason` (e.g.
  `near_duplicate_vertex_tolerated_box`) in the manifest, per hard rule 4 (fail closed **and name the
  reason**, never relabel a refusal as a success — this is not a refusal, it is a disclosed tolerance).
  Any building where `mismatched` is truthy at any point still raises exactly as today — that branch is
  untouched. The `did_reroute is True` success branch is untouched.
- **Why.** `D-EU-58` (owner, 2026-09-01, "vas-y", option (a)). T14 found 0/41 sampled losses ever
  trip the raw mismatch check; all 41 trip only the near-duplicate-vertex check, and the reroute net
  then correctly has nothing to do (38/41 no room-layout zone left, 3/41 the courtyard-hole guard).
  Both are already-valid geometry being thrown away, not a defect being masked.
- **How.** Minimal, localized change to the one `if mismatched or residual_near_dup: raise ...` gate.
  Do not touch `_force_reroute_room_layout_to_one_zone_per_floor` or `openubem/idf/surfaces.py` — T14
  confirmed that function is correct per its own docstring. After the change, re-run
  `run_eu_s2_district_campaign.py` (`--dry-run` only, `D-EU-55`) on all four districts to rebuild the
  `openubem/outputs/eu_evidence/EU-17/<district>/` tree — this is the "corrected `EU-17` tree" T12
  regenerates pages from. Do not touch `EU-11` (read-only, §3).
- **How to test.** Per district and fleet: population recovered vs T10's 633 losses (report the
  residual still lost, by reason, if any remain — e.g. genuine `mismatched` hits); the 8 named
  rules-regression buildings re-checked individually; confirm 0 buildings are retained where
  `mismatched` was truthy (this must never happen — spot-check by grepping the rebuilt manifests for
  `fallback_reason == near_duplicate_vertex_tolerated_box` and independently re-running
  `find_mismatched_interzone_pairs` against a sample of them); ruled-layout % per district reported
  alongside (informational only — T15 does not aim at that bar, `EU-17`/T05-T09 already own it);
  `pytest -q tests/` (serial) against the T05/T10/T14 baseline (2,540 passed / 55 skipped / 5 known
  failures, same names) — 0 new failures. Close `FINDING 220` in `DEBUG_REFERENCES` (drop `[OPEN]`)
  once the sample and full rebuild both confirm it.

### 🔴 Stop-and-report 5 — after T15. Director-audited (`D-EU-56` pattern — this is bookkeeping on an
already-ruled decision, not a new owner gate). Dispatch T12 immediately once clean.

### `EU-18b` — prove it, then ask — **blocked until T15 clears (see Stop-and-report 5)**

#### T12 — regenerate the pages and the gate on the new IDFs
- **What.** Re-run T02 and T03 against `EU-17/<district>/`; the `plans3D/` pages are **overwritten in
  place** (same filenames, same folder) and now show the relaxed plans; the parity gate must return 0.
- **Why.** `D-EU-54` §4: these pages plus the ≥ 95 % census are the trigger the owner reads.
- **How.** The same two scripts, pointed at the EU-17 tree. Each page's header states the new source tree
  and its build date.
- **How to test.** Four pages regenerate within the size budget; T02's content grep still finds nothing;
  the gate exits 0; the coverage line on `index.html` equals T10's census exactly.

### 🔴 Stop-and-report 3 — after T12. The owner reads `plans3D/` and gives, or withholds, confirmation.

#### T13 — the non-box sample battery  🔴 **BLOCKED on the owner's explicit permission (`D-EU-55`)**
- **What.** Local EnergyPlus 23.1.0 (`C:\EnergyPlusV23-1-0\energyplus.exe`) on **non-box buildings
  only**: ≥ 6 buildings per refusal class per district where that class exists (L, U/T, courtyard, narrow,
  audit-failed) plus 6 former reroute casualties.
- **Why.** `D-EU-51`(c): a geometric check is not proof that a plan runs.
- **How.** Prepare the sample list, the per-building command and the expected artefacts, write them into
  §8 — **and stop**. Run nothing until the owner has said, in their own words, to run this battery.
- **How to test.** Per building: return code, severe count, fatal count, run time — reported individually,
  never pooled. Zero fatals is the bar.

---

## 7. Stop-and-report points

| # | After | What must be in the report | What may start next |
|---|---|---|---|
🔴 **Amended by `D-EU-56` (owner, 2026-08-31, night): stops 1 and 2 are director-audited checkpoints, not
owner gates.** The director session audits the return, writes the §8 progress-log entry, and dispatches
the next slice immediately. Only stop 3 waits for the owner. T12 moves T02's pages to `plans3D/previous/`
before regenerating — the starting-state atlas is evidence and is never overwritten.

| 1 | **T03** | The four `plans3D/` pages exist and open offline; per-district building counts; the 459 divergences reproduced; the content grep | T04 — audited and dispatched by the director, no owner wait (`D-EU-56`) |
| 2 | **T04** | The true cause distribution beside the recorded one, per district; which classes T05–T08 will actually recover | T05 — audited and dispatched by the director, no owner wait (`D-EU-56`) |
| 3 | **T12** | Ruled % per district (bar ≥ 95 %), residual by named reason, parity 0, single-storey cores 0, dwelling and area conservation, suite result, regenerated pages | **Nothing.** `D-EU-55`: T13 and `EU-19` both wait for the owner's own sentence |
| 4 | **T14** (`D-EU-57`) | The 48-building taxonomy, the 8 named traces, and either a confirmed sample-level fix or the specific decision the director must ask the owner for | T15 — cleared 2026-09-01 by `D-EU-58` |
| 5 | **T15** (`D-EU-58`) | Population recovered per district vs T10's 633 losses, any genuine residual losses by reason, the 8 named buildings re-checked, 0 `mismatched` buildings ever tolerated, suite result | T12 — director-audited, no owner wait (`D-EU-56` pattern) |

---

## 8. Progress log

*One entry per completed task, appended by the executor. Format:*

```
#### TXX — <title> — completed YYYY-MM-DD
Artifacts: <paths>
Deviations: <none, or what and why with the citation>
Test status: <exact command and result>
Notes: <numbers a reader would otherwise have to re-derive>
```

#### T01 — IDF floor-plan reader — completed 2026-08-31
Artifacts: `scripts/eu_idf_plan_reader.py`, `tests/test_eu_idf_plan_reader.py`.
Deviations: (1) `ring` in the spec is a plural `rings: tuple[tuple[...], ...]` on `ZonePlan` —
some zones carry more than one `BUILDINGSURFACE:DETAILED` floor object (observed on courtyard/L-shape
zones, e.g. `IT-BOL-GALVANI2/b49d9a7ec64a2f5b.idf` had one zone with 4 floor surfaces); every sub-ring is
kept, none merged or dropped (rule 6). (2) 1 cm rounding (§4.4) is a function (`round_ring_1cm`) the
reader exposes but does not apply to its own canonical output — applying it before area computation
violates the 1e-6 area-parity test itself (a coordinate-magnitude cancellation argument, see the
DEBUG_REFERENCES entry below); T02 calls it only when building the HTML JSON blob. (3) added
`physical_storey_count` (exposed as `BuildingPlan.storey_count`) alongside `zone_storey_group_count`:
a storey group that absorbed more than one physical storey (`storey_span > 1`) is emitted as a single
zone tagged with only its group's start index, so counting distinct zone-name storey indices
under-counts; physical count is read off the tallest zone's height / `FLOOR_TO_FLOOR_M = 3.0`, confirmed
against `relation/12586384` (side-car `storeys: 7`, 1 zone spanning Z 0-21 m -> 21/3 = 7).
Test status: `pytest -q tests/test_eu_idf_plan_reader.py` -> 23 passed. Reader CLI on all four districts
reproduces §2 exactly: ES 961 (441 ruled / 188 cored), FR 297 (146/57), GB 82 (22/13), IT 1204 (380/324) —
each district's "ruled" count = IDF count − §2's "one undivided zone per floor" count, and "cored" count
matches §2's circulation-zone count exactly.
Notes: 20 sample stems (5/district, 2 box + 3 cored, first-in-CSV-order): ES
`c0469f277749f93e/relation-12582232`, `c6e90803c98dba87/relation-12582233`,
`a3b8acbbaf7cf1cf/relation-12702629`, `8b3598ac47b3f4a0/relation-12771676`,
`e21bec78b937acf5/relation-12877780`; FR `f1b0644cda5b4bf0`, `00625894313050dc`, `489894ba3d990787`,
`7d9a087b87add75b`, `ad5416ce6925106c`; GB `96664f92acdf04e8`, `816e388cc0fdaa78`, `2e6162aa24059905`,
`38af7df582b30cb7`, `6aa541121fa9ffb1`; IT `02dd9c3e4f745e0b`, `cf1704af581bc378`, `0ccdeb0a111369d4`,
`b826981c8c6c380f`, `dd90a841495a9c96`. New debug reference registered: shoelace-on-absolute-UTM-vertices
cancellation (§5 of `debugs/DEBUG_REFERENCES_european_locations.md`).

#### T02 — the `plans3D/` pages, from today's IDFs — completed 2026-08-31
Artifacts: `scripts/eu18_emit_plan_pages.py`, `docs/docs_ACTIVE/europeanLocations/plans3D/index.html`,
`PLANS_ES-MAD-BERRUGUETE.html`, `PLANS_FR-LYO-HAUTCOEURPENTES.html`, `PLANS_GB-LDN-STDUNSTANS.html`,
`PLANS_IT-BOL-GALVANI2.html`.
Deviations: descriptive-only fields the IDF cannot carry (scheme name, recorded `fallback_reason`, the
`FINDING 204` out-of-band tag) are read from the per-building side-car and always kept inside a
`sidecar: {...}` sub-object in the embedded JSON, plus a `divergent` flag and a "side-car says X, IDF
says Y" note in the UI when the side-car's own ruled/box claim disagrees with the IDF (rule 3). Facade
contact per storey is computed directly from the IDF's own zone rings (shapely: a dwelling zone's
boundary intersected with its storey's overall exterior boundary), not read from the side-car's flat
`facade_contact_lengths_m` list, to keep it rule-3 compliant and because that list has no per-storey
index. `index.html`'s header text avoided the word "EnergyPlus" (a forbidden term) even in a negative
sentence ("no EnergyPlus output is shown") — reworded to "no simulated output".
Test status: generated all four pages + index, `python -m scripts.eu18_emit_plan_pages` (15 s total).
List length verified against the embedded JSON equals the IDF count exactly on all four (961/297/82/1204).
`relation/12582232` (box) verified structurally: 4 storeys, each exactly one `whole`-kind zone.
`way/380242662` (cored) verified structurally: every storey carries a `circulation`-kind zone alongside
its dwelling zones (renders with the hatch pattern). Content grep
`grep -icE "eui|kwh|energyplus|heating|cooling|epw|job" docs/docs_ACTIVE/europeanLocations/plans3D/*.html`
-> 0 on all five files. No browser was launched (none available in this environment); "opens offline" was
verified by confirming zero external references (`grep -ioE "https?://|<script src=|<link "` -> no
matches) and that the embedded JSON parses (`json.loads`) on all four pages.
Notes: sizes well inside the 25 MB budget — ES 1.77 MB, FR 0.76 MB, GB 0.18 MB, IT (binding case) 2.95 MB.
Ruled % per district: ES 45.89, FR 49.16, GB 26.83, IT 31.56.

#### T03 — parity gate (report-only in this phase) — reached the STOP condition, 2026-08-31
Artifacts: `scripts/eu18_parity_gate.py`,
`openubem/outputs/eu_evidence/EU-18/parity_{ES-MAD-BERRUGUETE,FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,
IT-BOL-GALVANI2}.csv`, `openubem/outputs/eu_evidence/EU-18/parity_summary.txt`.
Deviations: none in the gate's own five checks (implemented exactly as T03 specifies: zone-name-set
equality, circulation-presence equality, scheme consistency, physical storey-count equality, and area
conservation). "Areas equal to 1e-6" is implemented as the IDF's own conserved identity
`conditioned + circulation == gross` (fact 10), **not** a cross-check of the IDF's gross area against the
side-car's declared `gross_footprint_area_m2` — the latter legitimately differs by up to 2 %
(`REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION`, §4.9, kept in force) and would fail almost the whole
fleet on an intentional tolerance, not a defect.
🔴 **STOP — the gate does not reproduce 459.** Run for real on EU-11 (`python -m scripts.eu18_parity_gate`,
exit code 1): **518** divergent, not 459 — ES-MAD-BERRUGUETE **234** (not 175), FR-LYO-HAUTCOEURPENTES 52,
GB-LDN-STDUNSTANS 18, IT-BOL-GALVANI2 214 (these three match §2 exactly). The extra 59 Madrid buildings
are a fourth, previously undocumented divergence mechanism, disjoint from the 175 known `FINDING 213`
buildings (0 overlap) and isolated to Madrid (0 additional in the other three districts): the side-car
declares an absorbed floor group's `storey_span` (internally consistent — its own `floors[]` entries sum
to its own `storeys` field) but the IDF's actually-emitted zone for that same group is shorter — its
tallest surface reaches fewer physical storeys than the side-car declares (50 of 59 off by exactly one
storey, 5 by two, 2 by three, 2 by four). Example: `way/289979823` (stem `010460eeb4131522`) — side-car
`storeys: 4`, its 3rd group (`storey_index 2-3`, `storey_span: 2`) implies a zone reaching Z = 12.0 m, but
the IDF's `010460eeb4131522_F2_dwelling_0` only reaches Z = 9.0 m (3 `ZONE` objects total, not 4 physical
storeys). `scheme_consistent`, `zone_names_equal` and `circulation_presence_equal` all pass on these 59;
only `storey_count_equal` fails. Per rule 11 / T03's own instruction ("If your number differs from 459,
STOP and report — do not adjust either side to make them agree"), the check was **not** narrowed or
loosened to force agreement. Registered as `[OPEN]` in
`debugs/DEBUG_REFERENCES_european_locations.md` chapter 3.
Test status: `python -m scripts.eu18_parity_gate` — exit code 1 (as expected, divergences exist); the
961/297/82/1204 per-district building counts match; the divergent counts do **not** match §2's 459 for
the reason above.
Notes: this STOP blocks nothing already delivered (T01/T02 stand on their own) but means Stop-and-report 1
cannot be closed as a clean "459 reproduced" until the director/owner rules on the new 59-building finding
(root cause not yet located; candidate: `n_storey` computed differently between
`scripts/run_eu_s2_district_campaign.py:_geometry` and `scripts/emit_eu11_layout_sidecars.py` for these
59 specifically). Per `D-EU-56`, Stop-and-report 1 is director-audited, not owner-gated — but this
executor's mandate was T01-T03 only and stops here per the STOP-and-report-2 rule and rule 11; T04 is not
started.

#### T04 — the deep refusal census — completed 2026-08-31
Artifacts: `scripts/eu17_refusal_census.py`,
`openubem/outputs/eu_evidence/EU-17/refusal_census.csv` (1,096 rows, one per refused building),
`openubem/outputs/eu_evidence/EU-17/refusal_census_summary.csv` (per-district recorded-vs-true reason
counts and reclassified counts, long format).
Deviations: none from the "How" — the census calls the module's real routes directly
(`classify_building_morphology`, `regularize_footprint_orthogonal`, `generate_european_grid_layout`,
`generate_european_linear_gallery_layout`, `generate_european_courtyard_layout`,
`_split_at_reflex_vertex`, `_l_shape_wings`, `_allocate_wing_dwelling_counts`, `_combine_wing_results`,
`_courtyard_wings_and_nodes`) in the same order `generate_european_ruled_storey_layout`
(`european_residential.py:855-1003`) uses, stopping short of the point where `_secondary` would run the
legacy `equal_strip_multi_angle_sweep` cutter and mask the reason (fact 6). No line was added to
`european_residential.py`. One bug was caught and fixed inside the new script before the fleet-wide run
(see debug reference below): the trace's `dwelling_count == 1` branch initially returned no real layout
object for a 1-dwelling wing, which crashed `_combine_wing_results` on any L-shape/courtyard building
whose wing allocation gave a wing exactly one dwelling; fixed by building the same `EuropeanGridLayout`
the real 1-dwelling branch constructs (`european_residential.py:873-888`). 0 `TRACE_ERROR` rows in the
final output.
Test status: `python -m scripts.eu17_refusal_census` (all 4 districts, real-time ~74 s, no EnergyPlus
invoked). Refusal totals reproduce §2 **exactly**: Madrid 345/961, Lyon 99/297, London 42/82, Bologna
610/1204, fleet 1,096/2,544.
Notes — recorded (old, masked) vs true (new, unmasked) reason counts, per district:
ES-MAD-BERRUGUETE (345 refused): `L_SHAPE_DECOMPOSITION_FAILED` 220→226, `INTERIOR_RING_COURTYARD_
UNFOLD_FAILED` 71→71, `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` 44→44, `PARTITION_AUDIT_FAILED` 6→4,
`NARROW_FOOTPRINT_LT_8M` 4→0; 6 reclassified (4 narrow + 2 partition-audit, all into L-shape).
FR-LYO-HAUTCOEURPENTES (99 refused): `L_SHAPE_DECOMPOSITION_FAILED` 75→76, `DWELLING_DENSITY_EXCEEDS_
RULED_GRID_GT_8` 13→13, `INTERIOR_RING_COURTYARD_UNFOLD_FAILED` 9→9, `NARROW_FOOTPRINT_LT_8M` 2→0, new
`INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` 0→1; 2 reclassified (1 narrow into L-shape, 1 narrow into the
new facade reason).
GB-LDN-STDUNSTANS (42 refused): `L_SHAPE_DECOMPOSITION_FAILED` 21→24, `DWELLING_DENSITY_EXCEEDS_RULED_
GRID_GT_8` 18→18, `NARROW_FOOTPRINT_LT_8M` 3→0; 3 reclassified, all narrow into L-shape.
IT-BOL-GALVANI2 (610 refused, the binding case): `L_SHAPE_DECOMPOSITION_FAILED` 313→413, `INTERIOR_RING_
COURTYARD_UNFOLD_FAILED` 159→169, `NARROW_FOOTPRINT_LT_8M` 135→0, `PARTITION_AUDIT_FAILED` 3→21, new
`INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` 0→7; 137 reclassified (135 narrow + 2 partition-audit), landing
mostly in L-shape (+100), courtyard (+10), partition-audit (+18 net, some of it from narrow) and the new
facade reason (+7).
Fleet: 148 of 1,096 refusals (13.5 %) carried a masked recorded reason. Fact 6 confirmed exactly as
written: **every one** of the 144 fleet-wide `NARROW_FOOTPRINT_LT_8M` refusals and 4 of the 9
`PARTITION_AUDIT_FAILED` refusals were masking an upstream ruled-route failure (mostly
`L_SHAPE_DECOMPOSITION_FAILED`, some `INTERIOR_RING_COURTYARD_UNFOLD_FAILED`, `PARTITION_AUDIT_FAILED`
inside the grid/gallery route itself, or `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M`) — `NARROW_FOOTPRINT_
LT_8M` does not exist as a true cause anywhere in the fleet once unmasked. `DWELLING_DENSITY_EXCEEDS_
RULED_GRID_GT_8` (75 fleet-wide) and the courtyard-recorded rows were never masked (`_secondary` is
reached only from the L-shape/gallery/grid/2-way-bisection branches; the density cap short-circuits
before any route runs). **Classes T05–T08 will actually recover** (per true counts, fleet-wide): T05
(L-shape) 739 (was 629 recorded) — the largest and now larger target; T06 (courtyard) 249 (was 239); T07
(narrow, <8 m) recovers **0** directly — narrow-plate geometry turned out to always be a symptom of an
L-shape/courtyard/facade failure on these footprints, never the true cause on its own, so T07's corridor-
free rule must be reachable from within those routes (already true per T05's "reachable also from a wing
produced by T05", §6 T07 How) rather than as its own top-level dispatch branch; T08 (single-storey core
removal) is unaffected by masking (its 46 buildings are not refusals). `PARTITION_AUDIT_FAILED` (25 true
fleet-wide, up from 9 recorded) and the new `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` (8 true, 0 recorded)
are not addressed by any T05–T08 task as scoped and stay open residual after T10.

#### T05 — wing decomposition that cannot refuse the whole building — completed 2026-08-31
Artifacts: `openubem/geometry/european_residential.py` (`_reflex_vertices`, `_split_at_reflex_vertex`
extended with `reflex_vertex_index`, `_split_wing_best_of_all_reflex_vertices`, `_l_shape_wings`
`max_wings` 4→6 and now tries every reflex vertex per step, `_wing_count_candidates`, L-shape branch of
`generate_european_ruled_storey_layout` rewritten to search count-vector candidates and set
`keep_circulation_polygon=True`), `tests/test_eu17_relaxed_layout.py` (T05 section).
Deviations: (1) `keep_circulation_polygon=True` on the L-shape combine directly contradicts an existing,
out-of-scope regression test (`tests/geometry/test_eu13b_circulation_sidecar.py::
test_l_shape_decomposition_building_carries_null_circulation_per_floor`) — that test reads a *static*
side-car JSON file under the read-only `EU-11` tree (rule 3), so it is unaffected at runtime by this
change and still passes; it is stale documentation of the pre-T05 behaviour, not a live check, and is not
edited (outside §3). (2) One existing regression test in the same out-of-scope file,
`tests/geometry/test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_
vertex`, hard-pins that a specific synthetic Z/double-L footprint at `dwelling_count=4` must be *refused*
(`scheme == "equal_strip_multi_angle_sweep"`); it is now correctly recovered (`scheme ==
"l_shape_decomposition"`, `dwelling_layout_emitted=True`) — the direct, intended consequence of T05's own
title ("cannot refuse the whole building"). Confirmed via `git stash` that this is caused by this task's
code change (test passes on unmodified `main`) and is not a pre-existing failure. Not fixed by editing
that test (outside §3); flagged here and in the final report per rule 11 rather than silently accepted or
forced to keep passing by weakening the geometry.
Test status: `pytest -q tests/test_eu17_relaxed_layout.py` → 71 passed (T05+T06+T07+T08 sections
combined, see T06-T08 entries). `pytest -q -n 8 tests/` → 2,540 passed / 55 skipped / **5 failed** (not
the 2,345/55/0 baseline in §2): 4 of the 5 are pre-existing and unrelated (confirmed via `git stash`) — 2
already documented in §2 (`tests/test_eu_real_footprint_feasibility.py`, `EU-13B §10`) and 2 not
previously named here (`tests/geometry/test_eu14b_bologna_layout_binding.py::test_t02_one_sidecar_per_
simulated_building`, `::test_t03_both_provenance_tags_present_on_every_sidecar`, both fail identically on
unmodified `main`); the 5th is the T05 recovery above. Synthetic wing-decomposition tests (L, U, T, cross,
double-L, 3–8 dwellings/floor, 30 cases): all emitted, dwelling count exact, audit passed, area error
< 1e-6, circulation polygon present and > 0 m².
Notes: real-fleet before/after (scratchpad measurement, not a plan-owned script, against T04's
`refusal_census.csv` true-cause population — replays `generate_european_building_dwelling_layout` on the
739 true `L_SHAPE_DECOMPOSITION_FAILED` buildings): Madrid 226→213 (13 recovered), Lyon 76→75 (1),
London 24→24 (0), Bologna 413→398 (15) — **29 of 739 (3.9 %) recovered fleet-wide** on real (GIS-noisy,
non-axis-aligned) footprints, far below the synthetic-fixture success rate; most real L-shape refusals
still fail the combined audit/facade gate even with the wider wing/count search, which is expected —
T05's "How" scopes the mechanism (more candidates, re-allocation), not a guarantee every real footprint
clears it. T10's rebuild will re-measure the final coverage number.

#### T06 — courtyard unfolding hardened — completed 2026-08-31
Artifacts: `openubem/geometry/european_residential.py` (`_courtyard_wings_and_nodes` node-clipping fix,
`generate_european_courtyard_layout` rewritten to search `_wing_count_candidates` instead of one baseline
split), `tests/test_eu17_relaxed_layout.py` (T06 section), `debugs/DEBUG_REFERENCES_european_locations.md`
ch.1 (node-clip fix + new [OPEN] wing-tiling-gap finding).
Deviations: none from the "How" (reuses `generate_european_courtyard_layout`/`_courtyard_wings_and_nodes`,
reuses T05's re-allocation search, corner wings keep their existing >= 1-dwelling floor). One genuine
pre-existing defect was found and fixed while proving this task's own required identity (see Notes) — the
node-clipping fix in `_courtyard_wings_and_nodes` — registered in the debug-references file per rule 7.
Test status: `pytest -q tests/test_eu17_relaxed_layout.py -k t06` → 24 passed (4 fixtures × [4,6 dwellings
unfold test, gross-minus-void identity test], parametrized). Full `pytest -q -n 8 tests/` result reported
under T05 (shared run).
Notes: proving T06's own "gross − void = conditioned + circulation to 1e-6" test on a clean synthetic
square-ring fixture (336 m² footprint, 4 dwellings) initially failed by 7.56 m² (2.3 % relative) — traced
to `_courtyard_wings_and_nodes` centring each corner circulation node **on the void's own inner corner**,
so roughly half of every node box sat inside the void and was still summed into the reported circulation
area. Fixed by clipping each node to the aligned footprint before returning it (changes no wing geometry,
only the reported area); all four synthetic fixtures now hold the identity to < 1e-10 relative. Real-fleet
recovery (same before/after method as T05, against the 249 true `INTERIOR_RING_COURTYARD_UNFOLD_FAILED`
buildings): **0 of 249 recovered** (Madrid 71→71, Lyon 9→9, London 0→0, Bologna 169→169). Investigated one
real failing building (`relation/12582232`): every wing individually emits cleanly and the *only*
mathematically possible count split for its 4 wings / 4 dwellings (1 each) still fails the combined audit
by `AREA_GAP` 0.11 % relative — a wing-boundary tiling gap on the real (rotated, GIS-noisy) footprint that
re-allocation cannot reach, since it is identical across every count candidate. Registered `[OPEN]` per
rule 7 rather than attempted further (outside T06's scoped "How": "reuse T05's re-allocation", not "fix
the wing-tiling geometry").

#### T07 — narrow plates (< 8 m) get a corridor-free rule — completed 2026-08-31
Artifacts: `openubem/geometry/european_residential.py` (`generate_european_narrow_plate_layout`,
`NARROW_PLATE_SCHEME = "narrow_plate_corridor_free"`, dispatched from `generate_european_ruled_storey_
layout`'s `i_shape_linear_gallery` branch when the raw footprint's minimum rotated width is
< `NARROW_FOOTPRINT_THRESHOLD_M`), `tests/test_eu17_relaxed_layout.py` (T07 section).
Deviations: (1) per the dispatcher's own instruction and the plan's T07 "How" ("reachable also from a
wing produced by T05" — not its own top-level dispatch), the narrow check is scoped to the
`i_shape_linear_gallery` route only (the one route carrying `CORRIDOR_SPINE_WIDTH_M`, fact 12's actual
conflict); `point_block_grid` and the `dwelling_count == 2` bisection already use a compact centroidal
core via `_centred_circulation_region`, never the spine, so they were never in fact-12's conflict and are
left untouched. (2) "no corridor polygon" (How-to-test) is implemented as "no `CORRIDOR_SPINE_WIDTH_M`
elongated band" — the scheme still carves a compact `CIRCULATION_FRACTION_OF_PLATE` stair core for >= 2
dwellings/storey (plan text: "Core sizing stays `CIRCULATION_FRACTION_OF_PLATE`, the corridor is
omitted"), checked in the test by the circulation polygon's own aspect ratio staying well under a spine's
(< 10:1 on a 40 m-long test plate); a first implementation attempt (subtract a compact core, then split
the remainder into west/east bands by centroid) was geometrically wrong — a compact core does not span
the plate's full short dimension, so it never disconnects the plate and one band came back empty on every
run — fixed by slicing the whole core-minus-plate remainder in one `_equal_area_axis_cuts` pass instead
(which already conserves area around a hole/notch). (3) If the core alone leaves no usable remainder, the
storey refuses with the new `NARROW_PLATE_CORE_EXCEEDS_HABITABLE_SHARE` reason, per the plan's own "How".
Test status: `pytest -q tests/test_eu17_relaxed_layout.py -k t07` → 21 passed: widths 5/6/7/7.9 m x
1–4 dwellings all emitted via `narrow_plate_corridor_free`, facade contact >= 2.5 m, area error < 1e-6, no
corridor-spine-shaped polygon; the shared entry point (`generate_european_ruled_storey_layout`) reaches
the branch directly on a narrow gallery-shaped plate; exactly 8.0 m does **not** trigger it (still
`i_shape_linear_gallery`, per fact 7's strict `<` gate). Full suite result reported under T05.
Notes: fleet-wide direct top-level recovery is **0**, exactly as predicted in T04's census notes — narrow
width was never the true top-level cause on this fleet on its own; it only matters inside a wing T05/T06
produce (not separately re-measured here; T10's rebuild will show it, since only the district rebuild
actually recurses through wings on real footprints end-to-end).

#### T08 — `D-EU-49`: one storey ⇒ no circulation — completed 2026-08-31
Artifacts: `openubem/geometry/european_residential.py` (`carve_circulation: bool = True` threaded through
`generate_european_ruled_storey_layout`, `generate_european_grid_layout`, `generate_european_linear_
gallery_layout`, `generate_european_narrow_plate_layout`, `generate_european_courtyard_layout`;
`generate_european_building_dwelling_layout` gates it once, `carve_circulation = len(floor_allocations)
!= 1`), `tests/test_eu17_relaxed_layout.py` (T08 section).
Deviations: the courtyard route's void-corner nodes are still geometrically computed and subtracted from
wings when `carve_circulation=False` (needed for valid wing separation — dropping node subtraction risks
overlapping wings at the void's inner corners) but contribute 0 to the reported circulation area
(`target_circulation_area = 0.0` when not wanted, so `node_side = 0`, degenerate no-op boxes); not
merged back into the adjacent dwelling wing's own polygon. Accepted because no single-storey courtyard
building exists in this fleet's pinned 46 (§2) — verified fleet-wide (see Notes) — so this has zero
measured real-world impact; documented rather than silently left implicit.
Test status: `pytest -q tests/test_eu17_relaxed_layout.py -k t08` → 8 passed: single-storey at 2–8
dwellings/floor emits with `circulation_polygon is None` and `circulation_area_m2 == 0.0`, dwelling count
conserved, `gross == conditioned` to 1e-6; a 3-storey control building at 4 dwellings/floor still carries
circulation on every storey; the named Madrid example (way/340701289-like, `ruled_grid_3x2`, 5 dwellings,
161.32 m² gross) loses its core while keeping its scheme and count. Full suite result reported under T05.
Notes: fleet-wide (real footprints, all four districts, replaying the actual `_geometry`-equivalent
pipeline): **exactly 46 single-storey buildings** (Madrid 19, Lyon 6, London 0, Bologna 21 — matches §2
pinned exactly) and **0 of 46 carry a circulation zone** (down from the 3 pinned in §2 — `way/340701289`,
`BATIMENT0000000240881213_part0`, `BATIMENT0000000240881531_part0`, all individually confirmed to lose
their core while keeping their exact dwelling count and scheme).

#### T09 — kill the IDF/side-car divergence at the source (`FINDING 213` → 0) — partially completed
(b), investigated but not fixed (a) — 2026-08-31
Artifacts: `openubem/idf/surfaces.py` (no change — investigated, see Notes), `scripts/emit_eu11_layout_
sidecars.py` (`idf_reroute_divergence` detection via `scripts.eu_idf_plan_reader.read_district`, new
`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` sidecar/manifest branch, IDF-measured areas for
that branch, `idf_reroute_divergence_count` in the returned summary), `debugs/DEBUG_REFERENCES_european_
locations.md` ch.2 (new `[OPEN]` T09(a) finding) and ch.3 (T09(b) fix entry on the existing `FINDING 213`
bullet).
Deviations / STOP-adjacent finding on T09(a): investigated the actual root cause on a real divergent
building (`relation/12582233`) rather than guessing — `idf.intersect_match()` raises `ZeroDivisionError`
outright (not the vertex-count-mismatch-after-a-successful-match `FINDING 210` already describes) on a
genuinely non-degenerate (no near-zero edges) but non-axis-aligned, multi-storey (7 floors) octagonal
dwelling/circulation stack. This is a geomeppy-internal numerical fragility on rotated-polygon interzone
matching, not a ring-construction defect reachable from this task's editable file list (`openubem/idf/
builder.py`, where the block is actually assembled, is not in `EU-17`'s §3) — and per the plan's own
explicit instruction ("A Python-only geometric check is not proof that a reroute was unnecessary...
Where proof needs EnergyPlus it belongs to T13 and stops here"), no geometry change is made without that
proof, which `D-EU-55` forbids this task from obtaining. **T09(a) ("make the reroute rare by
construction") is therefore not implemented** — investigated and disclosed as `[OPEN]`, not guessed at.
T09(b) ("make any surviving reroute loud") **is** implemented: the manifest half
(`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` write-back,
`scripts/run_eu_s2_district_campaign.py:391-392`) already existed from an earlier session (dated
2026-08-31, before this dispatch) — confirmed present, unedited. The side-car half (this task's own work)
reads the actually-built IDF's own zone kinds via T01's `eu_idf_plan_reader.read_district` and overrides
the side-car (and, via the existing `updated_outcomes` mechanism, the manifest) whenever the generator
would emit a ruled layout but the IDF carries only `whole` zones.
Test status: **not run against `EU-11`** — rule 3/§3 forbids writing into `openubem/outputs/eu_evidence/
EU-11/**`, and `emit_layouts_for_district` writes side-car JSON there, so the changed function was never
actually invoked end-to-end this session. Verified the detection logic in isolation instead (scratchpad,
not a plan-owned script): on `relation/12582233` (the known divergent example investigated above),
`idf_reroute_divergence` correctly evaluates `True`; on `relation/12582232` (a genuine
`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` refusal that also happens to be an all-`whole` IDF),
it correctly evaluates `False` (both layers already agree it is a box) — no false positive on the
one case checked where agreement is correct. `pytest -q -n 8 tests/` after this change → same 2,540/55/5
as T05's run (no new failure from this file). Full end-to-end proof (`eu18_parity_gate.py` returning 0)
is explicitly deferred to **after T10's rebuild**, per the plan's own "How to test" for this task — not
claimed here.
Notes: 🔴 the reroute count "before/after" cannot be honestly reported yet — measuring the new detection
logic against **today's EU-11 IDFs** (built by yesterday's generator) mixes two different questions
(genuine `FINDING 213` reroutes vs. buildings T05/T06/T08 now recover that yesterday's generator also
would have, inflating any count taken now); a scratchpad measurement against EU-11 as-is returned 187 /
138 / 31 / 751 per district, which is **not** a T09 number and is not reported as one — it is discarded
here rather than presented as if it were. The real reroute count is a T10 deliverable (rebuild with
today's generator, then measure divergence against IDFs built by that same generator).

#### T10 — rebuild all four districts and census the coverage on the IDFs — reached the STOP condition, 2026-08-31
Artifacts: `openubem/outputs/eu_evidence/EU-17/{ES-MAD-BERRUGUETE,FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,
IT-BOL-GALVANI2}/` (rebuilt IDF trees, `prepared_buildings.csv`, `<slug>_manifest.csv`, `layouts/`),
`openubem/outputs/eu_evidence/EU-18/parity_*.csv` + `parity_summary.txt` (re-run against EU-17),
`scripts/run_eu_s2_district_campaign.py` (writes `<slug>_manifest.csv` alongside `prepared_buildings.csv`
so `eu_idf_plan_reader`/`emit_eu11_layout_sidecars` work unmodified against EU-17, dependency decision
§4.8's own text: "That script builds IDFs **and a manifest**"), `scripts/emit_eu11_layout_sidecars.py`
(`emit_layouts_for_district(district, evidence_root=None)` + `--evidence-root` CLI flag, mirroring
`eu18_parity_gate.py`'s existing pattern, so side-cars can be regenerated against EU-17 instead of only
EU-11), `debugs/DEBUG_REFERENCES_european_locations.md` ch.2 (new `[OPEN]` finding).
Deviations: two infrastructure additions were required and made to already-editable §3 files, both
necessary for T01's reader / T09(b)'s side-car regen / T03's parity gate to run against EU-17 at all
(neither of them wrote a manifest or side-car of their own before this task): (1) `prepare()` did not
write a `<slug>_manifest.csv` (only `prepared_buildings.csv`); `eu_idf_plan_reader.load_manifest` reads
`geometry_outcome` specifically from that file. Added, matching EU-11's exact layout and column set
(`MANIFEST_COLUMNS`), simulation columns (`eplus_return_code`, `heating_kwh`, etc.) left blank since
nothing is simulated (`D-EU-55`). (2) `emit_layouts_for_district` hard-coded the EU-11 path; parameterised
with `evidence_root` (default unchanged, so every EU-11 call site is byte-identical) and a `.resolve()`
fix (a relative `--evidence-root` path broke the new `repo_rel_path` computation on the first attempt --
fixed before any output was trusted).
🔴 **STOP — none of the four districts reach anywhere near the 95 % bar, and the fleet dwelling floor
(rule 2 / `D-EU-36`) is breached.** Measured from the rebuilt IDFs (T01's reader), one district at a time,
via `python -m scripts.run_eu_s2_district_campaign --district <D> --out openubem/outputs/eu_evidence/
EU-17/<D>` (wall-clock: ES ~7min [677/961 built], FR ~3min [269/297], GB ~47s [73/82], IT ~14min
[892/1204]):
ES-MAD-BERRUGUETE: 677/961 IDFs built, 179 ruled (**26.44 %**), 498 refused, 463 `FINDING 213` reroutes
(parity gate), 74 cored, single-storey cores 0/12.
FR-LYO-HAUTCOEURPENTES: 269/297 IDFs built, 104 ruled (**38.66 %**), 165 refused, 91 reroutes, 31 cored,
single-storey cores 0/6.
GB-LDN-STDUNSTANS: 73/82 IDFs built, 17 ruled (**23.29 %**), 56 refused, 21 reroutes, 8 cored,
single-storey cores 0/0.
IT-BOL-GALVANI2: 892/1204 IDFs built, 225 ruled (**25.22 %**), 667 refused, 395 reroutes, 173 cored,
single-storey cores 0/21.
🔴 **New discovery, root cause of the STOP (not yet FINDING-numbered, for the director):** rebuilding with
today's T05-T09 generator, **633 of 2,544 buildings (24.9 %) are entirely lost** -- no IDF at all, not
even a refused/box one -- to `RuntimeError: interzone_vertex_mismatch_unresolved` raised at
`scripts/run_eu_s2_campaign.py:531` (the residual check *after* `_force_reroute_room_layout_to_one_zone_
per_floor` has already run once and been re-verified). Per district: ES 284/961 (29.6 %), FR 28/297
(9.4 %), GB 9/82 (11.0 %), IT 312/1204 (25.9 %). EU-11 (pre-T05 generator, same four districts) had
**zero** such losses (`population_prepared` matched the non-geometric-exclusion count exactly,
`speed_failure_kinds: {}`). Confirmed not confined to newly-recovered ruled layouts: `relation/3730743` --
the `EXAMPLE_...md` §6 acceptance building that is *supposed* to refuse cleanly to a `whole`-zone box at
the density cap, touching no ruled route -- is lost to this exact `RuntimeError` too, so the fragility is
in extrusion/interzone-pairing of the real footprint itself, not specific to the wider wing search T05/T06
added. Registered `[OPEN]` in the debug-references file (extends the `FINDING 219`-class entry); **not
fixed** -- no ring-construction defect reachable from `EU-17`'s editable file list, and `D-EU-55` forbids
the EnergyPlus proof a real fix would need. Routed to `T13` alongside `FINDING 219`.
Consequence for rule 2 (`D-EU-36`, "28,189 fleet-wide is a floor, not a ceiling"): summing the declared
dwelling count (`allocate_european_dwellings(...).dwelling_count`) over every building actually present in
the EU-17 rebuild gives **22,129**, i.e. **6,060 dwellings (21.5 %) below the floor** -- entirely because
633 buildings' declared counts are absent from the population, not because any surviving building's count
was reduced (see below).
Also measured, within bar: `FINDING 213` reroute count is **not** low (970 across the fleet, all correctly
disclosed as `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` in both the manifest and the
regenerated side-car per T09(b) -- T09(b)'s "make it loud" mechanism itself works exactly as designed, the
underlying rate is just far higher post-T05/T06 than anticipated); single-storey cores **0/0/0/0** across
all four districts (test bar holds); `|conditioned + circulation - gross|` relative error **0 violations**
across all 1,911 built IDFs (test bar holds, checked to 1e-6); no dwelling count was reduced *within* any
building that did get an IDF -- the loss is 100 % at the population level, not the partition level.
**Rules regression (fact 13, `EXAMPLE_...md` §6, eight named buildings) -- 0 of 8 pass:**
`way/51781396` (GB) -- present, IDF carries 0 dwelling zones (rerouted to `whole`, expected 69).
`relation/12704090` (ES) -- **not in the EU-17 rebuild** (lost to the same `RuntimeError`).
`way/388485191` (ES) -- present, 0 dwelling zones (rerouted, expected 38).
`way/420409335` (ES) -- present, 0 dwelling zones (`FALLBACK_PENDING_LAYOUT`, expected 20, facade 2.79m).
`relation/3730743` (ES) -- **not in the EU-17 rebuild** (lost to the same `RuntimeError` -- this building
was supposed to stay a clean, unaffected refusal; it did not).
`way/391279229` (ES) -- present, 0 dwelling zones (rerouted, expected 44).
`BATIMENT0000000240879941_part0` (FR) -- **not in the EU-17 rebuild** (not traced to the `RuntimeError`
in the Lyon build log; more likely an unrelated row/typology-mapping exclusion, not investigated further
given the dominant finding above).
`BATIMENT0000000240880045_part0` (FR) -- **not in the EU-17 rebuild** (same as above, not traced to the
`RuntimeError`).
Test status: `pytest -q -n 8 tests/` was attempted twice; both hit repeated `Windows fatal exception:
access violation` crashes inside `joblib`/`execnet` worker-spawn machinery near 85-99 % completion
(environmental, in process-spawn code neither this task nor `EU-17` touches) -- the first run eventually
exited on its own without a parseable pass/fail summary, the second hung indefinitely at 99 % and was
killed. A third, serial `pytest -q tests/` (no `-n 8`) completed cleanly (no crash) in 1017.75s
(0:16:57) -- appeared stalled near the end mid-session (a slow stretch, not a hang) and finished
after this task's own STOP report was already sent: **5 failed, 2540 passed, 55 skipped** -- the
exact T05 baseline, same five named failures (`test_eu14b_bologna_layout_binding.py::test_t02_
one_sidecar_per_simulated_building`, `::test_t03_both_provenance_tags_present_on_every_sidecar`,
`test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`,
`test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_
topology[footprint1-COURTYARD_TOPOLOGY_UNSUPPORTED]` and `[footprint2-NON_CONVEX_TOPOLOGY_
UNSUPPORTED]`), zero new failures from this task's changes. The suite bar holds.
Notes: this is a **STOP, not a rounding discussion**, exactly as the plan's own T10 "How to test" names.
No number here was forced, widened, or relabelled to pass. The four ruled percentages, the population
loss, and the rules-regression failure are reported to the director for a ruling; `T11` (independent of
this regression) proceeds below since its own test bar is unaffected.

#### T11 — settle the EUI denominator (`FINDING 214`, `D-EU-39` §3) — completed 2026-08-31
Artifacts: `scripts/run_eu_s2_district_campaign.py` (`eui_denominator_m2 = conditioned_floor_area_m2`
added to the `prepared.append({...})` dict -- one new column, `floor_area_m2` untouched).
Deviations: none -- exactly the plan's own "How" (one added column, no recomputation, nothing simulated).
Test status: verified against all four EU-17 `prepared_buildings.csv` (677/269/73/892 rows): the column is
present on 100 % of rows in all four; `eui_denominator_m2 == conditioned_floor_area_m2` on 100 % of rows in
all four; `eui_denominator_m2 == gross_footprint_area_m2` **only** where `conditioned_floor_area_m2 ==
gross_footprint_area_m2` genuinely holds, in all four (verified as a row-wise mask equality, not just a
count).
Notes -- per-district mean / minimum of `eui_denominator_m2` (m2): ES-MAD-BERRUGUETE 718.96 / 27.29;
FR-LYO-HAUTCOEURPENTES 1235.71 / 21.45; GB-LDN-STDUNSTANS 1033.43 / 135.26; IT-BOL-GALVANI2 1693.73 / 20.55.
Rows where `eui_denominator_m2 == gross_footprint_area_m2` (i.e. no circulation zone -- box buildings and
`ruled_grid_1x1`/single-storey buildings): ES 603/677, FR 238/269, GB 65/73, IT 719/892. No EUI is
recomputed anywhere by this task, per its own "How".

#### T14 -- diagnose the population loss (FINDING 220) and the rules-regression collapse (0/8) -- reached the STOP condition, 2026-09-01
Artifacts: `scripts/eu17_reroute_trace.py` (side-effect-free instrumentation, no edit to
`openubem/idf/surfaces.py` or `scripts/run_eu_s2_campaign.py` -- every reroute/mismatch/near-duplicate
check is patched from the outside, IDFs written to a system tempdir, never into `EU-11/**` or
`EU-17/<district>/`), `openubem/outputs/eu_evidence/EU-17/reroute_trace_{ES-MAD-BERRUGUETE,
FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}.json` (one per district: the 8 named-building
traces present in that district plus the stratified loss sample, full stage-by-stage event log per
building).
Deviations: (1) a bug caught before trusting any output: the first draft skipped `build_idf_for_building`
entirely for a FALLBACK_PENDING_LAYOUT / _MISSING_DWELLING_COUNT `_geometry()` outcome, on the wrong
assumption that a generator refusal never reaches extrusion -- `prepare()`
(`scripts/run_eu_s2_district_campaign.py:369-424`) never skips it: `_geometry()` always returns some
zones (a plain `one_zone_per_floor` box via `build_zones` when the ruled generator refuses), and
`build_idf_for_building` always runs on them. Caught because GB's first run returned 0 losses against
T10's own recorded 9/82; fixed, re-run, GB then reproduced 9/82 exactly (Test status). (2) sample size:
GB's population carries only 9 `interzone_vertex_mismatch_unresolved` losses in total (confirmed against
`EU-17/GB-LDN-STDUNSTANS/summary.json`'s own `IDF_ASSEMBLY_FAILED_RuntimeError: 9`) -- the 10-per-district
target could not be met there; 9 taken, not padded, per rule 4 (never relabel a refusal as a success).
Fleet-wide sample is 47, not 48, for this reason alone.
STOP -- the root cause is not a bug inside `_force_reroute_room_layout_to_one_zone_per_floor`; it is an
architectural gap outside `EU-17`'s editable file list, and no fix is applied.
Taxonomy over the 8 named buildings + 39 stratified `interzone_vertex_mismatch_unresolved` losses
(10/10/9/10 = ES/FR/GB/IT; GB short by 1, its own total): 41 lost outright, 3 rerouted-and-survived as a
box (0 dwelling zones), 1 box-survived cleanly (never attempted a ruled layout, no interzone issue at
all), 2 excluded upstream of geometry entirely (row-mapping, unrelated to this defect class). Per
district (final status, all 47): ES 15 (12 lost / 2 rerouted-survived / 1 box-survived-clean); FR 12 (10
lost / 2 excluded-upstream); GB 10 (9 lost / 1 rerouted-survived); IT 10 (10 lost).
All 41 losses carry the identical exception text
`interzone_vertex_mismatch_unresolved: mismatched=[] near_duplicate_vertex=True` -- `find_mismatched_
interzone_pairs` (the raw vertex-count check) never fires on any of the 41; every single loss is driven
by `_has_near_duplicate_vertex_surfaces` alone, the near-/collinear-vertex check `scripts/run_eu_s2_
campaign.py` added this same day as `EU-17` T09's own FINDING 210 residual fix (comment dated 2026-08-31
at that file's own lines 71-91) -- EU-11 was built before this check existed, so EU-11's "0 losses" is
not evidence its geometry was cleaner; the check itself is new.
Stage-by-stage, for the 41 losses (`scripts/eu17_reroute_trace.py`'s own read-only replica of the reroute
function's footprint-reconstruction test, verified against the real function's actual return value on
every one of the 44 reroute calls observed in this sample -- 100% agreement, 0 discrepancies): (1)
pre-check: near-duplicate/collinear fires (fired=True), raw mismatch does not (fired=False) -- 41/41.
(2) `_force_reroute_room_layout_to_one_zone_per_floor` is called and correctly, by its own documented
design, returns False -- 38/41 because `zones` carries no room_layout/european_dwelling_layout mode zone
at all (the building was already a plain one_zone_per_floor box before extrusion -- either a clean
generator refusal, or -- for 2 of the 8 named buildings, `relation/12704090` and `relation/3730743` --
the box IS the acceptance-correct outcome), so there is structurally nothing to reroute; 3/41 (all
Madrid, all named as DWELLING_LAYOUT_EMITTED) on the courtyard-hole guard
(`openubem/idf/surfaces.py:693`), correctly refusing to collapse a genuine courtyard void (interior ring
>= 1.0 m2, confirmed by re-deriving the union independently) into an illegal single holed block. Neither
branch is a bug: both are the function behaving exactly as its own docstring says (`:651-653`,
`:692-694`). 0/41 fail the reroute's own geometric reconstruction (multipart/empty after union, or after
the 5 mm/2 cm precision pass) -- that failure mode was never observed. (3) not reached for the 41 (no
successful reroute to residual-check). (4) the 8 named buildings, individually: `way/51781396` (GB) --
rerouted inside `build_idf_for_building`'s own at-risk check (not inside `extrude_geometry`), succeeded,
0 residual -> rerouted-and-survived, EU-17 dwelling_count 0 vs EU-11 69. `way/388485191` (ES) -- rerouted
inside `extrude_geometry` itself (`intersect_match` raised IndexError on the first pass), succeeded, 0
residual on the later at-risk check -> rerouted-and-survived, EU-17 0 vs EU-11 38. `way/391279229` (ES)
-- rerouted at the at-risk check, succeeded, 0 residual -> rerouted-and-survived, EU-17 0 vs EU-11 0 too
(this building was already one of the 175 Madrid FINDING 213 divergent buildings in EU-11 itself,
confirmed by reading `EU-11/.../idfs/f401084e3314e37e.idf` directly -- T10's "expected 44" was the
rules-sheet's acceptance target, not what EU-11 actually built). `way/420409335` (ES) -- plain box from
`_geometry()`, at-risk check never fires at all -> box-survived-clean, no interzone issue whatsoever;
T10's FALLBACK_PENDING_LAYOUT note for this one was already the full story. `relation/12704090` and
`relation/3730743` (ES) -- both plain boxes, no_rl_zones, lost outright (stage 2 above).
`BATIMENT0000000240879941_part0` -- excluded before `_geometry()` even runs, at `_mapped_rows`'s
archetype-mapping gate, reason TYPOLOGY_SIGNALS_DISAGREE (replayed directly against
`02_residential_manifest.gpkg`, not previously known). `BATIMENT0000000240880045_part0` -- same gate,
reason MISSING_OBSERVED_YEAR_BUILT. Neither Lyon building was ever a candidate for this defect class;
T10's "not investigated further" is now closed with a concrete, unrelated cause.
The decision this STOP asks the director/owner to make (per rule 11 -- not invented or applied here):
`build_idf_for_building`'s post-extrude at-risk gate (`scripts/run_eu_s2_campaign.py:516-534`, outside
`EU-17`'s editable file list) has no fallback for the two cases where the one safety net wired to it
correctly declines -- a building with no room-layout zones left to reroute (already the simplest
possible geometry), or a genuine courtyard. Today both cases raise and the whole building is lost. Should
a building that fails only the near-duplicate-vertex check (never the raw mismatch check) and has no
room-layout zones to reroute be tolerated as-is (accept the box/courtyard geometry, disclosed via the
existing loud-reroute manifest tag) rather than raised to a population loss? This is a new fallback tier
/ behaviour change in a file outside this task's scope, and -- per the plan's own T09(a) precedent -- a
Python-only geometric argument is not proof it is safe; proof needs EnergyPlus, which D-EU-55 forbids
here. No code in `openubem/idf/surfaces.py` was changed.
Test status: `pytest -q tests/` (serial, `-n 8` known to crash in this environment per T10's note) --
2540 passed / 55 skipped / 5 failed in 1036.80s (0:17:16), the exact T05/T10 baseline, same 5 named
failures verified identical by name (`test_eu14b_bologna_layout_binding.py::test_t02_one_sidecar_per_
simulated_building`, `::test_t03_both_provenance_tags_present_on_every_sidecar`,
`test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`,
`test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology`
`[footprint1-COURTYARD_TOPOLOGY_UNSUPPORTED]` and `[footprint2-NON_CONVEX_TOPOLOGY_UNSUPPORTED]`) -- 0 new
failures from this task, since no production file was edited. GB reproduced its own recorded total
exactly (9/82) after the Deviation-1 fix; ES/FR/IT loss samples reproduced against their own per-district
`IDF_ASSEMBLY_FAILED_RuntimeError` summary counts by construction (drawn from the same live scan, not a
separate source).
Notes: registered `[OPEN]`, extending the FINDING 220 entry, in
`debugs/DEBUG_REFERENCES_european_locations.md` chapter 2, per CLAUDE.md's register-every-error rule.

#### T15 — the fallback tier: retain a structurally-boxed building instead of losing it — completed 2026-09-01
Artifacts: `scripts/run_eu_s2_campaign.py` (`:530-556`, the `if mismatched or residual_near_dup:` gate),
`scripts/run_eu_s2_district_campaign.py` (new `fallback_reason` column read off `zones` and written into
`prepared_buildings.csv`, `:391-398`, `:430-431`), the rebuilt `openubem/outputs/eu_evidence/EU-17/
{ES-MAD-BERRUGUETE,FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}/` trees (`idfs/`,
`prepared_buildings.csv`, `<slug>_manifest.csv`, `summary.json`), `debugs/DEBUG_REFERENCES_european_
locations.md` chapter 2 (`FINDING 220` closed).
Deviations: the plans own "How" scopes the code change to "the one `if mismatched or residual_near_dup:
raise ...` gate" in `scripts/run_eu_s2_campaign.py` and forbids touching `_force_reroute_room_layout_to_
one_zone_per_floor`/`openubem/idf/surfaces.py` -- both honoured exactly (surfaces.py is byte-identical to
before this task). The "What" text additionally requires the tolerance to "record an explicit
`fallback_reason` ... in the manifest" and the "How to test" explicitly requires "grepping the rebuilt
manifests for `fallback_reason == near_duplicate_vertex_tolerated_box`" -- unreachable without a companion
change, since no `fallback_reason` column existed anywhere in `run_eu_s2_district_campaign.py`'s manifest
plumbing before this task (confirmed: the only existing zones-to-outcome disclosure was the single
`generation_status_note == "room_layout_intersect_fallback"` check at its line 391, added by T09, which
does not read this tasks new marker). Resolved by adding the smallest possible companion change,
mirroring T09s own precedent exactly: the gate tags every zone dict with `fallback_reason =
"near_duplicate_vertex_tolerated_box"` when it tolerates (pure local mutation of the already-in-scope
`zones` list, no import, no new file); `run_eu_s2_district_campaign.py` reads that marker off `zones` the
same way it already reads `generation_status_note`, and writes it as a new, additive column into
`prepared_buildings.csv` only (`pd.DataFrame(prepared)` already includes every dict key with no schema to
edit) -- **not** into `<slug>_manifest.csv`, whose `MANIFEST_COLUMNS` list is deliberately left untouched
to preserve its documented byte-identical-to-EU-11 schema (`scripts/run_eu_s2_district_campaign.py:442-
450`'s own comment: "same manifest layout as EU-11 ... so `eu_idf_plan_reader`/`emit_eu11_layout_sidecars`
work unmodified"). No tolerance, threshold or fallback-tier design was touched or invented beyond the one
authorized by `D-EU-58`; this is disclosure plumbing only, and is reported here rather than silently done.
Test status: `pytest -q tests/` (serial) -> **5 failed, 2540 passed, 55 skipped in 1487.49s (0:24:47)** --
the exact T05/T10/T14 baseline, same five named failures (`test_eu14b_bologna_layout_binding.py::
test_t02_one_sidecar_per_simulated_building`, `::test_t03_both_provenance_tags_present_on_every_sidecar`,
`test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`,
`test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology`
`[footprint1-COURTYARD_TOPOLOGY_UNSUPPORTED]` and `[footprint2-NON_CONVEX_TOPOLOGY_UNSUPPORTED]`) -- 0 new
failures. (Two `Windows fatal exception: access violation` bursts appeared mid-run from `joblib`/`loky`
worker-spawn machinery inside some tests own internal parallelism, not from pytest-xdist -- this run used
no `-n` flag -- and did not abort the run or affect the final tally; same environmental class T10 already
registered, not this tasks code.)
All four districts rebuilt (`python -m scripts.run_eu_s2_district_campaign --district <D> --out
openubem/outputs/eu_evidence/EU-17/<D>`, no `--dry-run` flag exists on this script because it never
simulates by construction, `D-EU-55`; the stale pre-fix EU-17 tree from T10 was deleted first -- its
`schedules/<stem>/` subfolders lack `exist_ok=True` and collided on a same-tree re-run -- `EU-11` was never
touched). **Population recovered per district, exactly matching T10s 633 losses, 0 residual:**
ES-MAD-BERRUGUETE 284/284 (population_prepared 677->**961**/961), FR-LYO-HAUTCOEURPENTES 28/28
(269->**297**/297), GB-LDN-STDUNSTANS 9/9 (73->**82**/82), IT-BOL-GALVANI2 312/312 (892->**1204**/1204);
fleet 633/633, population now **2,544/2,544** -- the full section-2 geometrically-eligible baseline,
exactly. Every `summary.json`s `blocker_exclusions` carries **zero** `IDF_ASSEMBLY_FAILED_RuntimeError`/
`interzone`-class entries in all four districts -- no genuine residual loss remains, so hard rule 4s
"disclosed residual" is empty for this defect class. **0 buildings retained where `mismatched` was ever
truthy**, both structurally (the tolerate branch is gated `if not did_reroute and not mismatched`, so a
truthy `mismatched` cannot reach it -- the pre-existing `raise` branch is unchanged and still fires) and
empirically: independently re-ran `find_mismatched_interzone_pairs` (unedited) against a 39-building
spot-check sample of the tolerated buildings rebuilt IDFs (all 9/9 GB, 10 each ES/FR/IT) -- 0/39
mismatched. **The 8 named rules-regression buildings, individually re-checked:** `relation/3730743` (ES)
-- **recovered**, present, `FALLBACK_PENDING_LAYOUT` + `fallback_reason=near_duplicate_vertex_tolerated_
box`, 5 `_whole` zones (0 dwelling zones) -- its own true refusal reason (`refusal_census.csv`) is
`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`, so this one building now again satisfies its specific
`EXAMPLE_...md` section-6 condition ("refused ... and zero zones"), lost entirely under T10. `relation/
12704090` (ES) -- **recovered**, present, `FALLBACK_PENDING_LAYOUT` + tolerated, true reason `INTERIOR_
RING_COURTYARD_UNFOLD_FAILED`; also lost entirely under T10. `way/51781396` (GB), `way/388485191` (ES),
`way/391279229` (ES) -- unchanged from T10, `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`, not
tolerated (the pre-existing `did_reroute is True` success path, untouched by this task) -- still 0 dwelling
zones, the separate `[OPEN]` T09(a)/geomeppy-rotation-fragility finding, outside T15s scope. `way/
420409335` (ES) -- unchanged, `FALLBACK_PENDING_LAYOUT`, no `fallback_reason` (the at-risk gate never
fired for this one at all, exactly T14s "box-survived-clean" finding). `BATIMENT0000000240879941_part0`,
`BATIMENT0000000240880045_part0` (FR) -- still absent, confirmed unrelated to this defect class (T14:
excluded upstream at the archetype-mapping gate, `TYPOLOGY_SIGNALS_DISAGREE` / `MISSING_OBSERVED_YEAR_
BUILT`), out of T15s scope as before. Net: 2 of 8 recovered by this task (both were "lost entirely" under
T10, now retained); the remaining 6 are unaffected either because they never lost population (3
rerouted-and-survived, 1 box-survived-clean) or are excluded upstream of this defect class entirely (2,
Lyon) -- matches T14s own taxonomy exactly, no surprises.
Notes: ruled % per district (informational only, T15 does not aim at it, `EU-17`/T05-T09 already own the
bar) is unchanged in kind from T10 -- measured off the rebuilt `geometry_outcome` column, `DWELLING_
LAYOUT_EMITTED` (excluding the imputed-count and rerouted variants) is ES 194/961 (20.19%), FR/GB/IT 0 in
this narrow counting (their ruled buildings all carry `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` instead, not
separately re-summed here since this metric is explicitly out of scope for T15s own bar). The fleet
dwelling-count floor (`D-EU-36`, rule 2) was not re-derived in this task -- `prepared_buildings.csv`
carries no per-building dwelling-count column; T10s own 22,129-vs-28,189 shortfall was already attributed
100% to the 633 missing buildings (no surviving buildings own count was ever reduced), so recovering
exactly those 633 buildings is expected to close it, but this was not independently re-measured here and
is flagged for whoever next touches the dwelling-floor bar. `FINDING 220` closed in `debugs/DEBUG_
REFERENCES_european_locations.md` chapter 2 (`[OPEN]` marker dropped, fix appended to the existing entry
per rule 7).

#### T12 — regenerate the pages and the gate on the new IDFs — completed 2026-09-01
Artifacts: `docs/docs_ACTIVE/europeanLocations/plans3D/{index.html,PLANS_ES-MAD-BERRUGUETE.html,
PLANS_FR-LYO-HAUTCOEURPENTES.html,PLANS_GB-LDN-STDUNSTANS.html,PLANS_IT-BOL-GALVANI2.html}` (regenerated,
overwritten in place), `docs/docs_ACTIVE/europeanLocations/plans3D/previous/` (the five pre-T12 pages
moved there first, unmodified, per the `D-EU-56` amendment to §7), `openubem/outputs/eu_evidence/EU-17/
{ES-MAD-BERRUGUETE,FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}/layouts/` (regenerated --
absent on the tree T15 left behind, see below), `openubem/outputs/eu_evidence/EU-18/parity_{ES-MAD-
BERRUGUETE,FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}.csv` + `parity_summary.txt`
(re-run against EU-17), `debugs/DEBUG_REFERENCES_european_locations.md` chapter 3 (new bullet).
Deviations: no code changed in `scripts/eu18_emit_plan_pages.py` or `scripts/eu18_parity_gate.py` --
both already carry the `--evidence-root` override T10 added. One companion step was required and run,
not planned in T12's own "How" text: `scripts/emit_eu11_layout_sidecars.py --evidence-root <D>=<path>`
per district, before T02/T03. T15's rebuild (`run_eu_s2_district_campaign.py` only) left `layouts/`
absent from all four EU-17 trees; without it every building reads `sidecar_present=False` and the parity
gate reports 100% `NO_SIDECAR` divergence on all four districts (961/297/82/1204), which is tooling
noise, not a measurement. Ran the emitter (mirrors T10's own precedent, same script, same flag) --
`layouts/` now holds 961/297/82/1204 files, exactly the census, and the gate measures the real defect
classes instead. Registered in `debugs/DEBUG_REFERENCES_european_locations.md` chapter 3 per rule 7 (no
code was changed, so "Fix" is the re-run procedure, not a diff).
Test status: not re-run -- no script was modified, so per this task's own instruction the last known
baseline applies (`pytest -q tests/` -> 5 failed, 2540 passed, 55 skipped, T15's own run, unchanged).
`python -m scripts.eu18_emit_plan_pages --evidence-root ...` x4 -> four pages + `index.html` regenerated,
961/297/82/1204 buildings listed (exactly T15's/T10's census, 2544/2544). Content grep
`grep -icE "eui|kwh|energyplus|heating|cooling|epw|job" docs/docs_ACTIVE/europeanLocations/plans3D/*.html`
-> 0 on all five files. All four pages inside the 25 MB budget: ES 1.35 MB, FR 0.60 MB, GB 0.14 MB, IT
2.36 MB. Each page's header states the new source tree (`openubem\outputs\eu_evidence\EU-17\<district>`)
and build date `2026-09-01` (the EU-17 IDFs' own mtime). `python -m scripts.eu18_parity_gate
--evidence-root ...` x4 -> **exit 1, not 0** -- 970 divergent fleet-wide (ES 463, FR 91, GB 21, IT 395).
Notes: the gate's non-zero exit is not a new defect -- it reproduces, building-for-building, the fleet
divergence T10 already measured and disclosed on its own (pre-fallback-tier) rebuild ("`FINDING 213`
reroute count is not low (970 across the fleet ...) -- T09(b)'s 'make it loud' mechanism itself works
exactly as designed, the underlying rate is just far higher post-T05/T06 than anticipated"), now
reproduced identically on the fully-recovered 2,544/2,544 population: ES 463 = 434
`SCHEME_DIVERGENT_FINDING_213;ZONE_NAME_SET_MISMATCH` (all `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_
REROUTED`) + 29 `STOREY_COUNT_MISMATCH`-only (all plain `DWELLING_LAYOUT_EMITTED`, the Madrid-only
`FINDING 215` mechanism); FR 91, GB 21, IT 395, all `SCHEME_DIVERGENT_FINDING_213;ZONE_NAME_SET_MISMATCH`
on `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` buildings, no other divergence class present in
those three districts. Both mechanisms are pre-existing `[OPEN]` entries (`FINDING 213`, `FINDING 215`,
chapter 3) that no T05-T15 task targeted; T12's own "How to test" ("the gate exits 0") was written before
either was disclosed and does not hold -- not narrowed or adjusted to force agreement, per rule 4/rule 11.
Ruled % per district (bar >= 95%, read off `is_ruled()`, T02's broader definition -- includes
`DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`, not only the narrow `DWELLING_LAYOUT_EMITTED` T15 quoted): ES
20.19% (194/961), FR 35.35% (105/297), GB 20.73% (17/82), IT 18.69% (225/1204) -- all far below the bar;
`EU-17`/T05-T09 own that bar per T15's own note ("informational only, T15 does not aim at it") and it was
not re-targeted by this task. Residual by named reason: 0 -- every `summary.json` carries zero
`IDF_ASSEMBLY_FAILED_RuntimeError`/interzone-class blocker exclusions in all four districts (T15's own
figure, unchanged, not re-measured here). Single-storey cores: 0/74 (ES), 0/31 (FR), 0/8 (GB), 0/173
(IT) -- bar holds, measured directly off T01's reader (`storey_count == 1 and has_unconditioned_core()`)
against the regenerated `layouts/`. Dwelling and area conservation: `|conditioned + circulation - gross|`
relative error -- 0 violations across all 2,544 buildings, checked to 1e-6 (T01's reader, matches T10's
own bar); the fleet dwelling-count floor (`D-EU-36`, 28,189) was not independently re-derived in T12
either, same caveat T15 already flagged -- T15's own conclusion (no surviving building's declared count
was ever reduced, population now 2,544/2,544 complete) stands, unchanged by this task. Coverage line on
`index.html`: 961/297/82/1204 = 2,544/2,544, exactly T10's/T15's census. Suite result: unchanged baseline
(above), no code touched. Per this task's rule 10, T13 and `EU-19` do not start; only T12's own dispatch
happened.
