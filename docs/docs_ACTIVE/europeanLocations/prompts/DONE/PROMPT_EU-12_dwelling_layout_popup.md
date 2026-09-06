# `EU-12` — Executor prompt: emit the per-building dwelling layouts and show them in a click pop-up

- **Arc**: European locations × Step 8.
- **Order**: runs **after** [`PROMPT_EU-11_full_district_campaign_speed.md`](PROMPT_EU-11_full_district_campaign_speed.md)
  (which produces the zones) and **after / alongside** [`PROMPT_EU-11B_viewer_result_integration.md`](PROMPT_EU-11B_viewer_result_integration.md)
  (which owns the same four viewers). If `EU-11B` has already regenerated the pages, extend those; never
  regenerate from an older copy.
- **Executor**: external. **Paste everything below the rule into the tool.**
- **Date of prompt**: 2026-08-28.

---

## Task (paste from here)

You are adding a **floor-plan pop-up** to the four European district viewers of the OpenUBEM repository
`C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** — never bare `python`.
Git is handled externally: **never commit and never stage.**

### 1. What exists today, measured

The dwelling subdivision of each building **is computed and then thrown away**. Nothing on disk holds it.

- `openubem/geometry/european_residential.py:591` `allocate_european_dwellings` → dwellings per storey,
  `units_per_floor`, and whether an unconditioned core is required.
- `openubem/geometry/european_residential.py:452` `generate_european_dwelling_layout` → an
  `EuropeanGeneratedFloorLayout` carrying `dwelling_polygons`, `partition_audit`,
  `facade_contact_lengths_m`, `fallback_reason`, and `status` ∈
  {`DWELLING_LAYOUT_EMITTED`, `FALLBACK_PENDING_LAYOUT`}.
- `openubem/geometry/european_residential.py:555` `european_layout_to_zone_specs` → one dict per dwelling
  with `name`, `floor_polygon`, **`coords_m`**, `z_floor`, `z_ceiling`, `mode`.
- The campaign scripts call all three and keep only the IDF:
  `scripts/run_eu_s2_campaign.py:162-186` (`build_geometry_for_row`) and
  `scripts/run_eu_s2_district_campaign.py:100-124` (`_geometry`).

Two facts you must carry into the deliverable rather than smooth over:

1. **Most buildings have no dwelling subdivision at all.** When the layout is not emitted the code falls back
   to `build_zones(..., strategy="one_zone_per_floor")` — a massing box. In the Lyon `s2_campaign_v3` run,
   **26 of 31** buildings took that path (`FINDING EU-S2-01`), and the viewer already carries the reason per
   building in the payload field `g` (`geometry_outcome`).
2. **The emitted layout is an equal-strip partition on the long axis** (footprint rotated onto its long axis,
   divided into equal strips, rotated back, then audited for area, topology and ≥2.5 m façade contact). It is
   **not** the point-block scheme and **not** the double-loaded corridor scheme of
   `docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md:276`
   (`content/figure_4_2_dwelling_layout_schemes.svg`) — that figure is the design intent, not what this code
   emits. **Label the pop-up with what was emitted; never draw the MVP figure in its place.**

The viewer payload, per building, in `<script type="application/json" id="scene">`, is
`{r, h, p, c, id, t, a, l, y, e, g}` where `r` is the footprint ring as `[x, y]` pairs **in the viewer's
local metric frame**, `h` height, `id` the `osm_id`, `e` the EUI, `g` the geometry outcome. The data-folder
contract is documented in `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` **§8.5** — read it first.

### 2. Part A — persist the layouts (emit)

Add to the campaign path a **layout side-car** written for every simulated building, in the district's
`EU-11` output directory:

```
openubem/outputs/eu_evidence/EU-11/<DISTRICT>/layouts/<building_id>.json
```

Each file records exactly what was produced, and nothing inferred:

```json
{
  "building_id": "...",
  "archetype_id": "...",
  "building_type": "MFH",
  "geometry_outcome": "DWELLING_LAYOUT_EMITTED",
  "scheme": "equal_strip_long_axis",
  "storeys": 5,
  "dwellings_total": 10,
  "units_per_floor": 2,
  "has_unconditioned_core": true,
  "floor_to_floor_m": 3.0,
  "floors": [
    {"storey_index": 0, "dwelling_count": 2,
     "zones": [{"name": "..._F0_dwelling_0", "coords_m": [[x, y], ...]}]}
  ],
  "facade_contact_lengths_m": [...],
  "partition_audit": {"passed": true, "area_error_fraction": 0.0},
  "fallback_reason": null
}
```

Rules for Part A:

- `coords_m` are written **in the same source CRS metres as the footprint**; record the CRS in the file. The
  viewer does the translation into its local frame, from the footprint it already has.
- **Write a file for a fallback building too**, with `zones: []`, the real `fallback_reason` string, and
  `scheme: null`. An absent subdivision is a result, not a blank.
- 🔴 **Report, do not fix, what the emitted path actually produces.** In the current code the
  dwelling-partitioned branch calls `european_layout_to_zone_specs` once, with the default
  `floor_index=0` / `z_floor_m=0.0`, while the massing-box branch stacks `n_storey` floors. Write the
  side-car to describe exactly the zones that reached the IDF — if only one storey of dwellings was emitted,
  say so in the file (`floors` has one entry) and state it in `RESULTS_EU-12.md` as a finding with the
  file:line evidence. **Do not change the physics to make the picture nicer.**
- The side-car is written from the same objects that built the IDF, in the same run — never re-derived
  afterwards from the CSV.
- Add a `layout_json` column to the `EU-11` manifest holding the side-car's repo-relative path, or an empty
  cell where none exists.

### 3. Part B — the pop-up (draw)

In each of the four viewers, clicking a building opens a **pop-up panel** over the canvas showing that
building's floor plan:

- The footprint outline, plus each dwelling polygon filled and labelled with its zone name, drawn to scale
  with a metre scale bar. Plain 2D canvas or inline SVG.
- A storey selector when the side-car holds more than one floor; otherwise state which storey is shown.
- A header line: `building_id`, archetype, building type, storeys, dwellings, units per floor, whether an
  unconditioned core was allocated, and the height provenance already in the panel.
- The EUI and its status where bound, unchanged from the existing channel.
- **A fallback building opens the same pop-up** and it reads, in full:
  *"No dwelling layout emitted — one zone per floor (massing box). Reason: `<fallback_reason>`. `FINDING EU-S2-01`."*
  It shows the footprint alone. It never shows a drawn subdivision.
- The scheme is named as emitted (`equal-strip partition on the long axis`), with one sentence saying it is
  not the point-block / double-loaded-corridor scheme of the MVP figure.
- `Esc` and a close button dismiss it; keyboard focus returns to the canvas.

### 4. 🔴 Rules the page must keep obeying

- The page stays **self-contained and offline**: no CDN, no external stylesheet, no `fetch`. The layout
  geometry is inlined into the scene JSON (or a second inlined JSON block), not loaded at runtime.
- **Nothing is interpolated, defaulted, borrowed or beautified.** No dwelling polygon is invented for a
  building that has none; no polygon is snapped, simplified or re-wound for looks.
- **Coverage is stated, never implied.** The panel counts how many of the district's residential buildings
  have an emitted layout, how many are massing boxes, and how many are not simulated.
- Keep the existing channels intact: geometry, height provenance (`measured` / `storeys × 3.0 m` /
  `assumed 9.0 m`), EUI colouring, range filter, `Data folder` link.
- This is the **`S2` real-footprint perimeter**, not the S0 archetype campaign — no comparison with
  `it = 108.25 kWh/m² ± 0.16 %` may appear anywhere on the page.
- Every viewer keeps shipping its data folder: add `layouts/` (or `layouts.json`) beside `buildings.csv`, and
  add each side-car's **sha256** and the layout coverage fraction to `sources.json`.

### 5. Deliverable

1. The layout side-cars for all four districts, plus the `layout_json` manifest column.
2. The four regenerated viewers and data folders in `openubem/outputs/3D/` **and** the byte-identical mirror
   in `docs/docs_ACTIVE/europeanLocations/outputs_3D/`.
3. `RESULTS_EU-12.md` in `openubem/outputs/eu_evidence/EU-12/`: per district, the count of
   `DWELLING_LAYOUT_EMITTED` vs `FALLBACK_PENDING_LAYOUT` vs not simulated, the distinct `fallback_reason`
   values with their counts, and the storey-emission finding of §2.
4. One appended row in `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`.
5. An update to `OpenUBEM_fundamentals.md` §8.5 describing the new layout channel, since the document must
   keep describing what the code actually does.
6. Any error you hit and solve: one entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, house
   format, before you close the task.

### 6. Do not

- Do not edit root `main.py`, any OVERVIEW or DESIGN doc, `previous/MVP_european_locations.md`, or
  `previous/WALKTHROUGH_european_locations.md`; do not annotate MVP Table 9.7.
- Do not write into `openubem/outputs/eu_certified_rerun_2026-08-28/` — read-only.
- Do not put `.py` files under `docs/`. All `.png` and figure outputs go to `openubem/outputs/`, flat.
- Do not change any physics, any zone geometry, any archetype assignment, or any IDF. `EU-12` **records and
  draws**; it does not alter what was simulated.
