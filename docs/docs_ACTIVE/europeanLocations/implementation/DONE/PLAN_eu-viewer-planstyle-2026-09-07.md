# PLAN — repaint the `outputs_3D` floor-plan modal in the `plans3D` visual style (`eu-viewer-planstyle-2026-09-07`)

**Slug:** `eu-viewer-planstyle-2026-09-07`. **Opened 2026-09-07.** No DESIGN doc governs this arc's viewer
code (a generated-artifact script, not a DESIGN-doc-owned module); the binding sources of truth are the two
scripts themselves, cited below by line. Successor to
`implementation/PLAN_eu-viewer-eui-floorplan-2026-09-07.md` (closed 2026-09-07, `STATE` §8).

**Context.** Owner compared, side by side, 2026-09-07:
- `plans3D/PLANS_ES-MAD-BERRUGUETE_nocore_2026-09-03_r5.html` — dark plan ground, each dwelling filled in a
  distinct saturated colour, thin white zone outlines, short `D1`/`D2` labels, light-on-dark scale bar and
  north arrow, monospace zone table.
- `outputs_3D/eu_ES-MAD-BERRUGUETE_viewer.html` — white plan ground, one heavy near-black footprint stroke,
  blue zone outlines, long `Dwelling 1` labels, dark-on-white scale bar and north arrow, sans-serif zone
  table with a swatch legend row.

**Owner ruling 2026-09-07 (verbatim):** *"floor plan visual style is different, i want to apply same style of
this plan view [`plans3D/PLANS_ES-MAD-BERRUGUETE_nocore_2026-09-03_r5.html`] for the outputs
[`outputs_3D/eu_ES-MAD-BERRUGUETE_viewer.html`]"*. Registered as **`D-EU-106`**.

**This plan is presentational only.** No polygon, no zone payload, no join, no data source changes. The
modal already carries everything it needs (`nm`, `ki`, `di`, `r`, `a` per zone,
`generate_eu_3d_viewers.py:895-916`); this plan changes how those are painted and tabulated, nothing else.

---

## 2. Hard rules for the executor

1. Touch **only** `scripts/generate_eu_3d_viewers.py`, and only inside the CSS block (`:95-118`), the modal
   markup (`:160-166`) and `drawFloorPlan` (`:502-645`). Everything else in the file — scene building,
   joins, `_build_plan_payload`, `openPopup`'s header/badges/storey bar, the 3D canvas painter — stays
   untouched.
2. `scripts/eu21/08_district_viewer.py` and every `plans3D/PLANS_*.html` file are **read-only style
   references**. Never edit them, never re-run `08_district_viewer.py`.
3. **Geometry is not touched.** No change to any ring, any `fx`/`fy` transform, any bounding-box or scale
   computation, any storey selection. If a rendered polygon moves by one pixel for any reason other than the
   canvas being resized to 580×320 (T01), the change is wrong — revert it.
4. **No data is dropped from the modal.** The zone table currently shows the zone area (`zn.a`); the
   `plans3D` table does not have that column. Keep it — the target table is `plans3D`'s columns **plus**
   Area (§6 T03). Same for the `#fp-legend` row: `outputs_3D` has zone kinds `plans3D` has none of
   (circulation/core, undivided massing box), so the legend stays, restyled — never deleted.
5. Regenerate the four viewers with **one** `python -m scripts.generate_eu_3d_viewers` invocation. Never
   hand-edit a generated `.html`.
6. No EnergyPlus run, no Speed submission, no network fetch.
7. No code comments beyond the two that already exist in the touched block (`// North is up`,
   `// Draw Scale Bar …`) — update their wording only if it becomes wrong.

---

## 3. File layout (only these may be touched)

- `scripts/generate_eu_3d_viewers.py` — all code changes (T01–T04)
- `openubem/outputs/3D/eu_{district}_viewer.html` — regenerated, 4 districts (T05)
- `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_{district}_viewer.html` — mirror, written by the same
  run (`generate_eu_3d_viewers.py:1158`+)
- `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-viewer-planstyle-2026-09-07.md` — this file,
  §8 only

Read-only style reference, cited never edited: `scripts/eu21/08_district_viewer.py` (`EXTRA_STYLE` `:82-121`,
modal markup `:440-454`, `ZONE_COLORS` `:489-502`, `drawFloorPlan` `:624-756`).

---

## 4. Dependency decisions (pinned)

- No new dependency. Pure stdlib + the script's existing imports.
- `ZONE_COLORS` is already byte-identical in both scripts (`generate_eu_3d_viewers.py:372-385` vs
  `08_district_viewer.py:489-502`) — do **not** re-order, re-key or extend it.
- Canvas size moves 560×280 → **580×320**, matching `08_district_viewer.py:449`. This is the only geometric
  change permitted, and it is a canvas-size change, not a transform change.

---

## 5. The style delta, measured (what "same style" means, item by item)

| # | Element | `outputs_3D` now | `plans3D` target | Cite |
|---|---|---|---|---|
| 1 | Plan container | `#fp-container{background:#fbfcfd;…padding:10px}` | `background:#0a0d13;…padding:12px` | gen:109 vs 08:107 |
| 2 | Canvas element | `#fp-canvas{background:#ffffff;border:1px solid #d9dee4}`, 560×280 | `background:#090c10;border:1px solid #1a212d`, 580×320 | gen:110,162 vs 08:108,449 |
| 3 | Canvas ground paint | `fillRect` white over whole canvas (`:505-506`) | no ground fill — the dark canvas shows through | gen:505 vs 08:626 |
| 4 | Footprint | fill `#ffffff`, stroke `#172033` lw 4.5 | fill `rgba(255,255,255,0.04)` (`evenodd`), stroke `#8b95a7` lw 2 | gen:529-533 vs 08:637-642 |
| 5 | Dwelling zone | fill `ZONE_COLORS[di-1]`, stroke `#2563eb` lw 3 | same fill, stroke `rgba(255,255,255,0.85)` lw 1.4 (`#ffffff` lw 2.4 when highlighted) | gen:554-558 vs 08:678-686 |
| 6 | Zone label | `"Dwelling "+di`, `#172033`, bold 12px | `"D"+di`, `#ffffff` bold 11px, `shadowColor rgba(0,0,0,0.85)` `shadowBlur 4` | gen:561-566 vs 08:702-710 |
| 7 | Scale bar | stroke `#334155`, text `#49515b` sans | stroke `#c9d1d9`, text `#8b95a7` `10px monospace`, origin `(24, ch-20)` | gen:617-634 vs 08:728-742 |
| 8 | North arrow | fill/text `#2c5d8a`, `10px sans-serif` | fill/text `#7fb3e0`, `bold 10px sans-serif`, origin `(cw-28, 26)` | gen:637-644 vs 08:745-755 |
| 9 | Zone table | `Zone / Colour / Area / Storey elevation`, sans-serif, swatch border `#172033` | `Zone Name / Colour / Dwelling Index / Storey Elevation`, monospace, `<code>` zone name, swatch border `rgba(255,255,255,0.7)`, row hover highlights the dwelling on the canvas | gen:568-611 vs 08:711-717 |
| 10 | Table CSS | `#m-zones td` inherits sans, padding `3px 6px` | `#m-zones td{font-family:"IBM Plex Mono";font-size:11.5px;color:#c8d1de}`, `td code{color:#8fd0ff}`, padding `5px 8px` | gen:114-117 vs 08:109-114 |
| 11 | Circulation zone | fill `#fef3c7`, stroke `#d97706`, dark label | no `plans3D` equivalent (no-core regime) — map to the dark-amber house palette: fill `#3a2410`, stroke `#7a4b12`, label `#f0c07a` | gen:584-600, palette from 08:99 |
| 12 | Undivided massing box | fill `#e5e7eb`, stroke `#172033` lw 3.5, dark label | no `plans3D` equivalent — map to footprint treatment: fill `rgba(255,255,255,0.07)`, stroke `#8b95a7` lw 2, label `#c8d1de` | gen:545,556-557 |
| 13 | Legend row | dark-on-white swatches, `color:#49515b` | keep the row, restyle: `color:#8b95a7`, swatches updated to items 5/11/12's new colours | gen:111-113,610-615 |

Items 11 and 12 have no `plans3D` counterpart because `plans3D` renders the no-core cutter only. Their
mapping above is the director's ruling, not an invention by the executor: **use the arc's existing dark
palette, do not choose new colours.**

---

## 6. Tasks

### T01 — CSS and modal markup

**What:** items 1, 2, 10, 13 of §5.
**Why:** the container/canvas ground is the single largest visual difference; the table font follows it.
**How:** in `generate_eu_3d_viewers.py`'s CSS block, replace the `#fp-container`, `#fp-canvas`, `#fp-legend`
and `#m-zones*` rules with `08_district_viewer.py:107-114`'s values (keeping `#fp-legend`, restyled to
`color:#8b95a7`). In the modal markup (`:162`) set `width="580" height="320"`. Braces in that block are
doubled (`{{`/`}}`) because it is an f-string — preserve the doubling exactly.
**How to test:** `python -m py_compile scripts/generate_eu_3d_viewers.py`; then regenerate one district only
if the script supports it, otherwise defer rendering to T05.

### T02 — repaint `drawFloorPlan`

**What:** items 3–8, 11, 12 of §5.
**Why:** the canvas paint is the style itself.
**How:** delete the white `fillRect` ground (`:505-506`); apply each row of the §5 table literally. Keep the
existing `fx`/`fy`, bounding box, `pad`, `sc`, and `barMeters` ladder untouched — only colours, line widths,
fonts, label strings and the two overlay origins change.
**How to test:** `python -m py_compile`; `node -e "new Function(<emitted script block>)"` on the regenerated
HTML (same check as the previous plan's T-final, `PLAN_eu-viewer-eui-floorplan-2026-09-07.md` §8).

### T03 — zone table

**What:** item 9 of §5.
**Why:** the table is half of what the owner sees under the plan.
**How:** columns become `Zone Name | Colour | Dwelling Index | Area | Storey elevation`. Zone Name is the
**real IDF zone name** already carried in the payload as `zn.nm` (`:896`, `:904`) wrapped in `<code>` — do
not synthesize `08_district_viewer.py`'s `b.id+"_F"+s+"_dwelling_"+z` string, which is a plans-side
invention. Dwelling Index is `"Dwelling "+zn.di` for `ki==="d"`, `—` for `ki==="w"` and the circulation row.
Keep the Area column (rule 4). Swatch border becomes `rgba(255,255,255,0.7)`.
**How to test:** open one regenerated viewer, click a `ruled` building, confirm the table shows the IDF zone
names and that the row count equals `storey.z.length` (+1 when `storey.c` exists).

### T04 — row-hover highlight

**What:** the one behaviour `plans3D` has and `outputs_3D` does not (`08_district_viewer.py:711-717`,
`:596-601`).
**Why:** it is part of the same modal style; without it the ported table is inert.
**How:** add a third argument `hlIdx` to `drawFloorPlan` (default `-1`), stroke the highlighted dwelling
`#ffffff` lw 2.4; add `window.highlightDwelling(zIdx)` / `window.unhighlightDwelling()` mirroring
`08_district_viewer.py:596-601`, and `onmouseenter`/`onmouseleave` + `cursor:pointer` on each dwelling row.
Update the two existing `drawFloorPlan(b, …)` call sites (`:481`, `:492`) to pass `-1`.
**How to test:** hover each zone row of a multi-dwelling building; only the hovered dwelling gains the white
outline, and moving off restores the base render.

### T05 — regenerate and verify

**What:** all four viewers + the `docs_ACTIVE` mirror.
**How:** one `python -m scripts.generate_eu_3d_viewers` from the repo root.
**How to test, all four required:**
1. Exit 0, 4 viewers + 4 `_data/` folders written.
2. Primary (`openubem/outputs/3D/`) and mirror (`docs/docs_ACTIVE/…/outputs_3D/`) byte-identical, per
   district — report the four hash pairs.
3. `node -e "new Function(js)"` on the emitted `<script>` block of each of the four files.
4. **No-regression on content:** for each district, the count of buildings in the scene, the count with
   `pl!==null`, and each district's `nruled`/`nmassing`/`nnoidf` HUD numbers are **identical** to the
   pre-change files. Report the 4×5 table. Any movement means something other than style changed — stop.

---

## 7. Stop-and-report points

- **`CP-1` — after T02.** Report the §5 table with a ✅/❌ per row against the actual code, plus one
  regenerated Madrid viewer for the owner to open. Do not continue to T03 until the director signs.
- **`CP-2` — after T05.** Report the four hash pairs and the 4×5 no-regression table.

---

## 8. Progress log

*(executor appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` +
Artifacts / Deviations / Test status / Notes.)*

#### T01 — CSS and modal markup — completed 2026-09-07

Artifacts: `scripts/generate_eu_3d_viewers.py` — `#fp-container`/`#fp-canvas`/`#fp-legend`/`#m-zones*` CSS
rules (`:109-119`), modal-markup canvas size (`:162`, `560x280`→`580x320`).

Deviations: none.

Test status: `python -m py_compile scripts/generate_eu_3d_viewers.py` — OK.

Notes: `#fp-legend` kept, restyled `color:#8b95a7` per rule 4/item 13; `#m-zones td`/`td code` rules added
verbatim from `08_district_viewer.py:107-114`.

#### T02 — repaint `drawFloorPlan` — completed 2026-09-07

Artifacts: `scripts/generate_eu_3d_viewers.py`, function `drawFloorPlan` (`:504-681`) — removed the white
`fillRect` ground; footprint fill/stroke; dwelling-zone fill/stroke/label (`isWhole` branch → item 12 massing
colours, else → item 5 dwelling colours with item 6 `"D"+di` shadowed label); circulation-zone fill/stroke/
label (item 11); legend swatch colours (item 13's JS half, `ZONE_COLORS[0]`/`rgba(255,255,255,0.85)` for
dwelling, item 11/12 colours for circ/whole); scale-bar and north-arrow colours/fonts/origins (items 7, 8).

Deviations: item 13's legend-swatch update (originally cited at old `:610-615`, inside `drawFloorPlan`) was
implemented in T02, not T01 — T01's "How" only touched the CSS block and modal markup per rule 1, and the
swatch fill/stroke values depend on items 5/11/12's colours, which don't exist until T02. No colour invented:
dwelling swatch fill uses `ZONE_COLORS[0]` (existing array, index 0) with item 5's new stroke; circ/whole
swatches use items 11/12's colours exactly.

Test status: `python -m py_compile scripts/generate_eu_3d_viewers.py` — OK. Full regen run
(`python -m scripts.generate_eu_3d_viewers`) — exit 0, all four viewers + mirrors written. Node syntax check
(`new Function(js)`) on the emitted `<script>` block of the regenerated `eu_ES-MAD-BERRUGUETE_viewer.html` —
`SYNTAX_OK`.

Notes: `fx`/`fy`, bounding box, `pad`, `sc`, `barMeters` ladder untouched, as required. Highlight variant of
item 5 (white `lw 2.4` stroke) is T04's `hlIdx` parameter — not yet added; current base render always uses
the non-highlighted stroke. Item 9 (zone table columns) is T03 — table markup untouched in this task.

#### T03 — zone table — completed 2026-09-07

Artifacts: `scripts/generate_eu_3d_viewers.py:592-596` (dwelling/whole zone row: `<code>zn.nm</code>`, Dwelling
Index column, swatch border `rgba(255,255,255,0.7)`), `:634-636` (circulation row, same swatch border, Dwelling
Index `—`), `:638-640` (`#m-zones` `<thead>`: `Zone Name | Colour | Dwelling Index | Area | Storey elevation`).

Deviations: none. Circulation row's Zone Name cell keeps the existing `clabel` description string (not
`<code>`-wrapped) — the plan's `zn.nm` instruction only covers zones from the `storey.z` loop (`ki==="d"`/`"w"`);
`storey.c` carries no `nm` field in the payload and rule 3/hard-rule-1 forbid adding one (no payload change).
Dwelling Index for the circulation row rendered as `—` per the plan's explicit instruction ("`—` for
`ki==="w"` and the circulation row").

Test status: `python -m py_compile scripts/generate_eu_3d_viewers.py` — OK.

Notes: Area column kept (rule 4). Onmouseenter/onmouseleave row attributes added in the same edit as the table
markup (they reference `highlightDwelling`/`unhighlightDwelling`, defined in T04) since both live in the same
row-building expression; behaviour is inert until T04 defines those two functions and the `hlIdx` parameter.

#### T04 — row-hover highlight — completed 2026-09-07

Artifacts: `scripts/generate_eu_3d_viewers.py` — `drawFloorPlan(b, sIdx, hlIdx)` third parameter with
`hlIdx===undefined` default (`:504-505`); highlighted-stroke branch `hlIdx===z` → `#ffffff` lw 2.4, else
`rgba(255,255,255,0.85)` lw 1.4, `isWhole` unchanged at `#8b95a7` lw 2 (`:561-570`); `window.highlightDwelling`/
`window.unhighlightDwelling` (`:497-502`); two existing call sites updated to pass `-1`
(`drawFloorPlan(b, 0, -1)` at `:483`, `drawFloorPlan(currentModalBuilding, sIdx, -1)` at `:494`).

Deviations: hover (`onmouseenter`/`onmouseleave`/`cursor:pointer`) applied only to dwelling rows (`ki==="d"`),
not to the massing-box or circulation rows — §5 item 5's highlighted-stroke variant is defined for dwelling
zones only, and items 11/12 define no highlighted variant, so there is no highlight state for those rows to
enter. Matches T04's own wording ("each dwelling row").

Test status: `python -m py_compile scripts/generate_eu_3d_viewers.py` — OK.

Notes: zone index `z` (the `storey.z` loop counter, also used for the canvas stroke comparison) is the same
value passed to `highlightDwelling(zIdx)` from each row, so table row and canvas polygon stay in sync.

#### T05 — regenerate and verify — completed 2026-09-07

Artifacts: `openubem/outputs/3D/eu_{district}_viewer.html` + `_data/` (4 districts), mirrored to
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_{district}_viewer.html` (4 districts), via one
`python -m scripts.generate_eu_3d_viewers` run.

Deviations: none.

Test status: exit 0, 4 viewers + 4 `_data/` folders written (console log). Primary/mirror sha256 identical for
all 4 districts (see director report). `node -e "new Function(js)"` on each of the 4 emitted `<script>` blocks
— `SYNTAX_OK` for all 4. No-regression counts (buildings in scene / `pl!==null` count / `nruled`/`nmassing`/
`nnoidf`) identical to the pre-T03/T04 baseline for all 4 districts (see director report's 4×5 table).

Notes: CP-2 reached. Awaiting director sign-off before any further task.
