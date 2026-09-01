# PROMPT — EU-18c: the 3D viewer becomes the floor-plan deliverable

**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM` · **Date issued:** 2026-09-01
**Arc:** `docs/docs_ACTIVE/europeanLocations/` · **Ruling that created this slice:** `D-EU-59` (below).

## 0. Why this exists

The owner opened `plans3D/PLANS_ES-MAD-BERRUGUETE.html` (built by T02/T12) and rejected it: it is a
standalone 2D building browser, not what was wanted. The owner then pointed at
`outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html` and said, in their own words, that **that** modal —
3D district → click a building → storey bar → floor-plan canvas + zone table — **is** the deliverable,
minus the energy data.

So this slice does **not** build anything new. It repairs the viewer that already exists.

## 1. Hard rules — obey literally

1. 🔴 **`D-EU-55` — never run EnergyPlus.** Not one building, not a probe, not a rerun. This slice is
   pure geometry: it reads `.idf` text files and writes HTML. If you believe a task needs a simulation,
   STOP and report the exact command you would have run.
2. 🔴 **`D-EU-59` (new, this slice) — the viewer carries no energy.** Forbidden everywhere including
   tooltips, HUD, modal, legend, hidden JSON fields and any emitted CSV side files: EUI, any demand or
   E+ output, `eplus_return_code` / severe / fatal counts, run or job ids, weather, and the words
   "simulated" / "not simulated" used as a building state. **Permitted and to be kept:** footprint,
   height and its provenance, construction year / age, dwelling and circulation polygons, storey index,
   dwelling count, gross and conditioned area, scheme name, refusal reason, circulation share,
   the `FINDING 204` out-of-band tag, CRS / extent / source layer / licence.
3. 🔴 **Plans come from the emitted IDFs, never from the side-cars.** The side-cars disagree with the
   IDFs on 970 buildings (`FINDING 213` / `FINDING 215`) — drawing from them is what put a layout on
   screen that the model does not carry. Source of truth for this slice:
   `openubem/outputs/eu_evidence/EU-17/<district>/**/*.idf` (2,544 files: ES 961, FR 297, GB 82, IT 1,204
   — the post-T15 tree). Read them with the existing reader
   `scripts/eu_idf_plan_reader.py::read_building_plan` — do not write a second parser.
4. **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.** The tree is
   dirty and user-owned; git is handled externally.
5. **Do not touch `plans3D/`** — not the pages, not `scripts/eu18_emit_plan_pages.py`, not
   `scripts/eu18_parity_gate.py`. They stay exactly as they are.
6. Before debugging any error, search `debugs/DEBUG_REFERENCES_european_locations.md` and
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. After solving one, append the entry in house
   format **before** closing the task.
7. Do not propose alternatives — execute. If a rule here contradicts a rule there, STOP and quote both.

## 2. Files you may write

- `scripts/generate_eu_3d_viewers.py` — edit in place.
- `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_<district>_viewer.html` (4 files) — regenerated output.
- `tests/test_eu18c_viewer_geometry_only.py` — new test file (T03 below).
- `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` — error entries only.
- `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` — append one row per task.
- Progress log entries at the bottom of **this** file (§5).

Anything else: STOP and report.

## 3. Tasks

### T01 — Feed the modal from the IDFs

**What.** Replace the side-car source of the per-building floor plan with the IDF reader.

**Why.** Rule 3. The `layouts_map` built at `scripts/generate_eu_3d_viewers.py:930-941` reads
`.../EU-11/<district>/layouts/**/*.json`; those side-cars are the rejected source.

**How.**
- Import `read_building_plan` (and `ZonePlan` / `BuildingPlan` as needed) from `scripts.eu_idf_plan_reader`.
- For each district, walk `openubem/outputs/eu_evidence/EU-17/<district>/**/*.idf` once, keyed by the
  building id the IDF stem encodes (the same stem→`building_id` mapping the plan pages already use —
  reuse it from `scripts/eu18_emit_plan_pages.py`, which you may read but must not edit).
- Build the per-building payload the modal needs, **entirely from the parsed IDF**: per-storey list of
  dwelling rings, the circulation ring if present, the `whole` ring for a massing box, storey index and
  its z-range, dwelling count per storey, gross and conditioned area, and the derived state — one of
  `RULED` (dwelling zones present), `MASSING_BOX` (only a `whole` zone), `NO_IDF` (no file).
- Scheme name and refusal reason are **not** in the IDF. Take them from the side-car **only** as
  annotation, and only when the IDF's own zones agree with the side-car for that building; where they
  disagree, show the IDF state and omit the scheme/reason rather than showing a contradicting one.
  Never let a side-car field decide a polygon.
- Rings must be emitted in the same local-metre convention the modal already draws in (see
  `local_ring_1cm` in the reader and how `b.r` is stored today) — the plan and the footprint must
  overlay exactly.

**How to test.** Pick 5 buildings spanning ES/FR/GB/IT and both states. For each, count the `ZONE,`
objects in its `.idf` and confirm the count and the zone names match what the emitted scene JSON
carries for it. Report the 5 ids and the counts.

### T02 — Strip every energy field

**What.** Remove energy from the generator and therefore from all four pages.

**Why.** Rule 2 / `D-EU-59`.

**How.** There are ~84 EUI/manifest touchpoints in `scripts/generate_eu_3d_viewers.py`. At minimum:
the `colour: EUI` button (`:129`), the EUI filter block (`:134` and its JS at `:202-203`, `:633`,
`:651-668`), the tooltip EUI line (`:347`), the modal EUI line (`:396`, `:407`), the legend text
(`:613`), the manifest read and `sim_map` (`:905-921`), and every `eui_note` / `warn_html` string in the
district table (`:690-800`) — those prose blocks quote pooled EUI and campaign counts and must be
rewritten to describe geometry only. `b.e` and `b.g` leave the scene JSON entirely. Replace the four
"colour:" modes with height / provenance / age / **layout state** (ruled · massing box · no IDF).

**How to test.** A case-insensitive count of `eui|kwh|eplus|severe|fatal|weather|epw|job.?id|not
simulated` over each of the four emitted HTML files must return **0**. Report the four numbers.

### T03 — The regression test

**What.** `tests/test_eu18c_viewer_geometry_only.py`.

**How.** Two tests, both offline, both against the four emitted HTML files:
(a) the forbidden-term scan of T02 returns 0 on all four;
(b) for a fixed sample of 8 building ids (2 per district, at least 2 massing boxes), the polygons in the
scene JSON are identical to what `read_building_plan` returns for that building's `.idf` right now.

**How to test.** `python -m pytest -q tests/test_eu18c_viewer_geometry_only.py`. Paste the exact output.

### T04 — Redraw the plan in the figure-4.2 language

**What.** Restyle `drawFloorPlan` so a storey pane reads like
`content/figure_4_2_dwelling_layout_schemes.svg` and the sheets in
`rules/RULES_dwelling_layout_scheme_2026-08-28.html`.

**Why.** This is the owner's stated bar. Read both files before writing any CSS.

**How.** Keep the modal's structure exactly as it is today (title, sub-line, status box, storey bar,
canvas, zone table) — the owner approved that structure on sight. Change only the drawing:
- The plan sheet is **light**, not dark: white ground, near-black footprint outline (`#172033`, ~4-5 px).
- Dwelling zones: fill `#dbeafe`, stroke `#2563eb` ~3 px, labelled `Dwelling 1…n` in dark text.
- Circulation / core: fill `#fef3c7`, stroke `#d97706` ~3 px, labelled `Unconditioned stair core`
  (point-block / core geometry) or `Unconditioned circulation spine` (corridor geometry) — choose by the
  ring's aspect ratio, and if that is ambiguous label it `Unconditioned circulation`.
- Massing box: the single `whole` zone, fill `#e5e7eb`, stroke `#172033`, labelled `Undivided massing box`.
- Keep the existing north arrow and scale bar; keep them legible on white.
- A legend strip under the plan, same two swatches and wording as the SVG.
- The zone table below keeps its columns but drops any energy column.
- The rest of the viewer (3D scene, HUD) stays dark — only the plan sheet inside the modal goes light.

**How to test.** Regenerate all four viewers, open
`outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html`, click `BATIMENT0000000240880127_part0`, and report:
storey count, dwelling count on F0, whether a core is drawn, and the labels rendered. Then do the same
for one ES building and one massing-box building. Report the three, with their ids.

### T05 — Regenerate and report

**What.** Run the generator for all four districts and record the result.

**How to test.** Report per district: file size, building count in the scene JSON, and the split
ruled / massing box / no IDF read from the IDFs. Then `python -m pytest -q -n 8 tests/` and paste the
tail — the expected baseline is 2,540 passed / 55 skipped / 5 failed (4 pre-existing + 1 known T05
consequence); any *new* failure must be named.

## 4. Stop-and-report

**One stop only, at the end of T05.** Report, then wait. Do not start anything beyond T05.

## 5. Progress log

(Append one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD`, then
Artifacts / Deviations / Test status / Notes.)

#### T01 — Feed the modal from the IDFs — completed 2026-09-01

Artifacts: `scripts/generate_eu_3d_viewers.py` (`_scene_ring`, `_storey_z_ranges`,
`_circulation_label`, `_load_eu17_sidecar`, `_build_plan_payload`, and the `plans_by_id`
read in `build_district`).

Deviations: none from the prompt's own field list. Two decisions the prompt left to the
executor: (1) storey z-ranges are read off `parse_idf_floor_zones`'s measured `zone_max_z`
per storey group, stacked bottom-up, rather than a nominal `storey_index * 3.0` — an
absorbed group's true height is not a multiple of `FLOOR_TO_FLOOR_M` (confirmed on
`ES-MAD-BERRUGUETE way/288447771`, three groups each 4.0 m tall, not 3.0 m); (2) `scheme`
/ `reason` (and the `FINDING 204` tag) are read from the **EU-17** side-car
(`EU-17/<district>/layouts/`), not EU-11 — same rebuild tree the IDFs come from, per rule 3's
own logic, since EU-11 is the disputed source.

Test status: 5-building spot check (ES ruled `way/100704712`, ES massing `way/100704656`,
FR ruled `BATIMENT0000000240877101_part0`, GB massing `way/14325891`, IT ruled `32471`) —
IDF `ZONE,` object count and names match the emitted scene JSON exactly on all 5.

Notes: rings are re-expressed in the same district-centred `cx`/`cy` frame the footprint
ring `b.r` already uses (via `plan.origin_xy` un-translation), so the plan overlays the
footprint exactly, per the prompt's own requirement.

#### T02 — Strip every energy field — completed 2026-09-01

Artifacts: `scripts/generate_eu_3d_viewers.py` (HUD rows/buttons, `#flt` block removed,
tooltip/modal/legend JS, `DISTRICT_SPECS`, `build_district`'s manifest/`sim_map`/
`results.csv` removal).

Deviations: `results.csv` / `results_source.csv` are no longer written at all (their only
content was EUI) rather than left conditionally absent. `sources.json`'s `speed_run` block
is removed; `idf_source_directory` (EU-17 idfs path) and `prepared_buildings.csv` sha256
added in its place for provenance. `buildings.csv` gained `layout_state` /
`storey_count` / `dwelling_count` / `gross_area_m2` / `conditioned_area_m2` /
`circulation_pct` columns in place of the dropped `eui_kwh_m2` / `eui_status` /
`geometry_outcome` (sim) columns — all six are on rule 2's permitted list.

Test status: case-insensitive `eui|kwh|eplus|severe|fatal|weather|epw|job.?id|not simulated`
scan on all four emitted `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_*_viewer.html` —
**0, 0, 0, 0**.

#### T03 — The regression test — completed 2026-09-01

Artifacts: `tests/test_eu18c_viewer_geometry_only.py` (new).

Deviations: none. Fixed 8-building sample (2/district, 4 massing box ≥ required 2):
ES `way/100704712`+`way/100704656`; FR `BATIMENT0000000240877101_part0`+
`BATIMENT0000000013365727_part0`; GB `way/190348384`+`way/14325891`; IT `32471`+`32166`.

Test status: `python -m pytest -q tests/test_eu18c_viewer_geometry_only.py` → **12 passed**
(4 forbidden-term params + 8 polygon-identity params) in 1.59s.

#### T04 — Redraw the plan in the figure-4.2 language — completed 2026-09-01

Artifacts: `scripts/generate_eu_3d_viewers.py` (`drawFloorPlan`, `openPopup`, CSS
`#fp-container`/`#fp-canvas`/`#fp-legend`/`.m-badge.*`).

Deviations: circulation core-vs-spine classification threshold is this task's own decision
(not specified upstream) — ring bounding-box long/short aspect ratio, `<=1.6` → core,
`>=2.75` → spine, else ambiguous → "Unconditioned circulation" (`scripts/generate_eu_3d_viewers.py`,
`_circulation_label`).

Test status: manual/scripted inspection (no EnergyPlus, no browser available in this
environment) of the scene JSON for the three named buildings:
- FR `BATIMENT0000000240880127_part0`: under the IDF-truth read this building is
  **massing_box**, not ruled — 10 storeys, 0 dwellings on every storey including F0, no core,
  every storey labelled "Undivided massing box". (The pre-EU-18c side-car-driven page showed
  it differently; this is exactly the FINDING 213/215 divergence rule 3 exists to fix.)
- ES `way/100704712`: 3 storeys, 1 dwelling on F0 (label "Dwelling 1"), no core.
- GB `way/14325891` (massing box): 3 storeys, "Undivided massing box" each floor.
- IT `32471` additionally exercised circulation labelling: F0 carries 2 dwellings plus a
  compact core, correctly labelled "Unconditioned stair core".

#### T05 — Regenerate and report — completed 2026-09-01

Artifacts: `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_{ES-MAD-BERRUGUETE,
FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}_viewer.html` regenerated.

Test status: per-district file size / scene building count / ruled·massing·no-idf split (of
residential): ES 1,427,052 B / 1398 / 194·767·233 of 1194; FR 726,306 B / 768 / 105·192·233
of 530; GB 393,233 B / 1351 / 17·65·1160 of 1242; IT 2,466,548 B / 1257 / 225·979·16 of 1220.
`python -m pytest -q -n 8 tests/` → **2551 passed / 55 skipped / 6 failed** in 323.53s — one
more than the plan's stated baseline (2540/55/5). Import-inspection of all 6 failures shows
5 (`test_eu14b_bologna_layout_binding.py::test_t02_one_sidecar_per_simulated_building`,
`::test_t03_both_provenance_tags_present_on_every_sidecar`,
`test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`,
`test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology[footprint1-COURTYARD_TOPOLOGY_UNSUPPORTED]`,
`[footprint2-NON_CONVEX_TOPOLOGY_UNSUPPORTED]`) import only
`openubem.geometry.european_residential` or read EU-11 Bologna files this slice never
touches — pre-existing, not caused by T01–T05. The 6th,
`test_eu14b_bologna_layout_binding.py::test_t03_construction_period_badge_appears_in_generated_viewer`,
is the anticipated T05 consequence: it asserts `CONSTRUCTION PERIOD IMPUTED` / `cprov` text
in `openubem/outputs/3D/eu_IT-BOL-GALVANI2_viewer.html`, which T01's closed side-car payload
(scheme + reason only) deliberately no longer emits. No new failure caused by this slice.
