# PLAN — wire real EUI + port the colorful floor-plan modal into the 3D district viewers (`eu-viewer-eui-floorplan-2026-09-07`)

**Slug:** `eu-viewer-eui-floorplan-2026-09-07`. **Opened 2026-09-07.** No DESIGN doc governs this arc's
viewer code (it is a generated-artifact script, `scripts/generate_eu_3d_viewers.py`, not a DESIGN-doc-owned
module); the binding source of truth is the script itself and its sibling `scripts/eu21/08_district_viewer.py`,
cited below by line.

**Context:** owner opened the four `outputs_3D/eu_*_viewer.html` files delivered by the EU-11 ceiling82
harvest (`prompts/DIRECTOR_PROMPT_eu82pct-ceiling-harvest_2026-09-05.md`) and compared them against
`plans3D/PLANS_*_nocore_2026-09-03_r5.html`. Two gaps confirmed by direct inspection 2026-09-07:
1. The viewer's "colour: EUI" button is fully wired in JS (ramp/legend/setMode, `generate_eu_3d_viewers.py:187-209,604-643`)
   but `b.eui` is never populated — the per-building dict never carries an `eui` key
   (`generate_eu_3d_viewers.py:987-999`).
2. The viewer's click-building floor-plan modal (`generate_eu_3d_viewers.py:362-601`) renders flat
   grey/blue/amber shapes with no per-dwelling colour and no QA context, while `08_district_viewer.py`'s
   modal (`:522-757`) renders each dwelling in a distinct colour, a zone table with colour swatches, and a
   check-badge banner (`PASS ALL 7 CHECKS` / per-check chips).

**Owner ruling 2026-09-07 (batched with plan approval, verbatim):** "build and insert EUI data visuals on
top of PLAN 3D visuals so .html files in the outputs3D will be cumulative combination of all steps" — i.e.
port the *full* `08_district_viewer.py` floor-plan style (colours, zone table, check badges, PASS/FAIL
banner) into the `outputs_3D` viewer's modal, **and** add EUI. The two pipelines' geometry disagree on 970
buildings (`FINDING 213`/`FINDING 215`), which is why `generate_eu_3d_viewers.py`'s own docstring
(`:3-13`) restricts it to IDF-only geometry (rule 3) — the owner's ruling accepts the EU-21 census-cutter's
`checks`/`status`/`verdict` fields as **annotation only** (same pattern already used for the EU-17 sidecar's
`scheme`/`reason`/`f204` at `:836-838`), never as a second source of truth for any polygon. Geometry stays
100% IDF-derived; only checks/status/verdict/EUI are merged in by `building_id`.

---

## 2. Hard rules for the executor

1. Touch only `scripts/generate_eu_3d_viewers.py` (edits) and its four generated outputs (regenerate, don't
   hand-edit). Do not touch `scripts/eu21/08_district_viewer.py` or any `plans3D/PLANS_*.html` file — they
   are the read-only style/data reference, never the target.
2. Do not touch `openubem/geometry/european_residential.py`, `main.py`, DESIGN docs, or
   `scripts/eu_idf_plan_reader.py`.
3. Geometry (building rings, zone rings, storey z-ranges) stays exactly as `_build_plan_payload` already
   produces it — sourced only from the EU-17 IDF tree. Never let a `checks`/`status`/`verdict` merge change,
   drop, or gate a polygon; if a building has no EU-21 evidence row (see rule 5), it renders with geometry
   only and no badge, never a fabricated badge.
4. Reuse the exact existing ring-preservation logic (`:930-938`, `existing_rings`) — do not regenerate
   footprint vertex arrays from the GPKGs on this pass.
5. Three joins, all keyed on the viewer's own `bid = str(row["osm_id"])` (`:946`) — verified exact-match
   2026-09-07 (Bologna: 1212/1212 EU-11 manifest ids are a subset of the 1257 `buildings.csv` ids; EU-21
   evidence: 1220/1220 `plates[].building_id` unique, matches the 1220 residential rows 1:1):
   - EUI: `openubem/outputs/eu_evidence/EU-11/<CITY-CODE>_ceiling82_2026-09-05/<city_lower>_manifest.csv`,
     column `eui_kwh_m2`.
   - Checks/status/verdict/scheme: `openubem/outputs/eu_evidence/EU-21/district_plans/<CITY-CODE>_nocore_2026-09-03_r5.json`,
     `plates[]` list, keys `building_id`, `status`, `verdict`, `checks` (dict of `C1/C3/C4/C5/C6/C10/C11` →
     `{"pass": bool, "show": str}`), `scheme`.
   - If either join misses a building (no manifest row / no evidence row), leave that field `null` — the
     existing `b.eui==null` / no-badge handling already degrades gracefully (`:172` grey fallback pattern in
     the rendered JS; port the same null guard for checks).
6. Report the per-district join-miss count (buildings present in the scene but absent from either source)
   at Stop point 1 — do not silently drop or silently invent for misses.
7. No EnergyPlus run, no Speed submission — this plan only reads existing evidence files and regenerates
   static HTML.

---

## 3. File layout (only these may be touched)

- `scripts/generate_eu_3d_viewers.py` — all code changes (T01, T02, T03)
- `openubem/outputs/3D/eu_{district}_viewer.html` — regenerated output, all 4 districts
- `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_{district}_viewer.html` — mirrored output, all 4
  districts (script already mirrors, `generate_eu_3d_viewers.py:1158`+)
- `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-viewer-eui-floorplan-2026-09-07.md` — this
  file, §8 only

Read-only references (cited, never edited): `scripts/eu21/08_district_viewer.py`;
`openubem/outputs/eu_evidence/EU-11/<CITY>_ceiling82_2026-09-05/<city>_manifest.csv` (4 files);
`openubem/outputs/eu_evidence/EU-21/district_plans/<CITY>_nocore_2026-09-03_r5.json` (4 files).

---

## 4. Dependency decisions (pinned)

None — pure Python (`pandas`/`json`, already imported) and vanilla JS in the existing template string. No
new package.

---

## 5. Facts, with line citations

- **EUI plumbing already complete except the data:** `euis`/`euimin`/`euimax` computed from `b.eui`
  (rendered-JS: filters `B` for `eui!=null`); colour ramp branch `if(mode==="u"){{...}}` at
  `generate_eu_3d_viewers.py:209`; legend branch for mode `"u"` at `:609-616`; button wiring
  `document.getElementById("bU").onclick=function(){{setMode("u",this);}};` at `:641`. Only the data source
  is missing: `b_obj` dict literal at `:987-999` has no `"eui"` key.
- **`b_obj` assembly loop:** `generate_eu_3d_viewers.py:945-1000`, `for i, row in combined_gdf.iterrows()`;
  `bid = str(row["osm_id"])` at `:946` is the join key for all three merges (EUI, checks, and the existing
  `pl_obj`/EU-17 sidecar merge at `:970-985`).
- **`buildings.csv` is written, never read, by this script** (`combined_gdf` comes from
  `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg` / `02_excluded_manifest.gpkg`, `:873-878`;
  `buildings.csv` rows are only emitted, around `:1065-1069`) — EUI/checks must be loaded independently, not
  merged via `buildings.csv`.
- **EU-11 manifest** (`<city>_manifest.csv`) columns: `building_id,archetype_id,building_type,age_band,
  geometry_outcome,construction_period_provenance,idf_sha256,weather_sha256,eplus_return_code,
  severe_errors,fatal_errors,heating_kwh,floor_area_m2,eui_kwh_m2,run_seconds,platform,
  energyplus_version`. One row per `building_id`, no duplicates (Bologna: 1212 rows, 1212 unique, verified
  2026-09-07). `building_id` is the same id space as the scene's `osm_id`-derived `id` (Bologna: full
  1212/1212 subset match against the 1257 `buildings.csv` ids — the manifest is a subset because it excludes
  `no_idf`/failed-on-Speed buildings, which is expected and correct: those get `eui=null`).
- **EU-21 evidence JSON** (`<district>_nocore_2026-09-03_r5.json`, `openubem/outputs/eu_evidence/EU-21/
  district_plans/`) — written by `08_district_viewer.py:879-887` (`evidence["plates"]`), one dict per
  building at `plates[]`. Sampled Bologna 2026-09-07: 1220 plates, 1220 unique `building_id`, matching the
  1220 residential rows in the scene 1:1 (no misses expected there; verify the other 3 districts as part of
  T03). Per-plate keys of interest: `building_id`, `status` (`"direct"` or `"GENERIC_NO_CENSUS"`; Bologna:
  1204/16), `verdict` (`"PASS"`/`"FAIL"`/`"GENERIC"`; Bologna: 1085/119/16), `checks` (dict, e.g.
  `{{"C1":{{"pass":true,"show":"100.0 %"}}, "C3":{{"pass":true,"show":"1/1"}}, ...}}` for all of
  `CHECK_IDS = ("C1","C3","C4","C5","C6","C10","C11")`, `08_district_viewer.py:46`), `scheme`.
- **Dwelling colour palette to port:** `ZONE_COLORS` array, `08_district_viewer.py:489-501` (verify exact
  line span on read; 12 hex entries, indexed `ZONE_COLORS[z % ZONE_COLORS.length]` at `:662`).
- **Badge/banner rendering to port:** `08_district_viewer.py` `openPopup` (`:522-616`) builds `chipsHtml`
  from `b.ch` (array of `[cid, show, pass]` triples, loop `:542-549`, chip HTML
  `<span class="chk ok/bad">CID show</span>`) and the `PASS ALL 7 CHECKS` / scheme banner gated on
  `b.v==="PASS"` (`:553-` ff.). `drawFloorPlan` (`:617-757`) colours each dwelling zone via
  `ZONE_COLORS[z % ZONE_COLORS.length]` and builds the zone table with a colour-swatch column.
- **Target-side equivalents already present, ready to extend (not replace from scratch):**
  `generate_eu_3d_viewers.py`'s own `_build_plan_payload` (`:774-847`) already tags every zone with
  `"ki":"d"/"w"/"c"` and, for dwellings, a 1-based `"di"` dwelling index (`:797-804`) — this is exactly the
  index `ZONE_COLORS[(di-1) % N]` needs; no new geometry field is required, only the colour lookup and the
  zone-table swatch column in `drawFloorPlan` (`:456-601`) and the badge block in `openPopup` (`:382-450`).
  `_load_eu17_sidecar` (`:767-771`) is the existing pattern for a by-`building_id` JSON sidecar load — the
  EU-21 evidence load (T03) should follow the same shape (read once per district into a `dict[str, ...]`
  keyed by `building_id`, looked up per building in the `:945` loop), not be re-derived per building.

---

## 6. Tasks

#### T01 — Wire real per-building EUI from the EU-11 ceiling82 manifest
**What:** load `<city>_manifest.csv`, build a `{{building_id: eui_kwh_m2}}` dict once per district, and set
`"eui": eui_by_id.get(bid)` in the `b_obj` dict literal (`:987-999`) — `None` when the building has no
manifest row (no_idf / excluded / failed-on-Speed).
**Why:** the colour-mode JS (ramp/legend/button) already exists and is fully wired (§5) — this is purely a
missing data feed, not new UI.
**How:** add a small loader function (mirror `_load_eu17_sidecar`'s shape, but CSV not JSON) near
`_load_eu17_sidecar` (`:767`); call it once in `build_district` before the `:945` loop; extend `b_obj`.
**How to test:** for each of the 4 districts, assert `eui_by_id` has exactly as many entries as the
manifest's unique `building_id` count (no silent drops on parse); regenerate one viewer (Bologna) and grep
the emitted `<script id="scene">` JSON for `"eui"` occurring on ~1200 of the 1220 residential buildings;
open in a browser, click "colour: EUI", confirm the legend shows a non-degenerate min/max (not 0/200
fallback) and buildings render on a colour ramp instead of flat grey.

#### T02 — Port per-dwelling colour + zone-table swatches into the floor-plan modal
**What:** replace the flat `"#dbeafe"` dwelling fill in `drawFloorPlan` (`:456-601`, dwelling-zone branch)
with `ZONE_COLORS[(zn.di - 1) % ZONE_COLORS.length]`; add a matching colour-swatch cell to each dwelling row
in the zone table (mirrors `08_district_viewer.py`'s zone table column, §5).
**Why:** owner ruling — port the "detailed and colorful" style, this is its core visual element.
**How:** copy the `ZONE_COLORS` array verbatim from `08_district_viewer.py:489-501` into
`generate_eu_3d_viewers.py`'s JS template (near the modal block, `:362`); change the dwelling-zone
`fpCtx.fillStyle` assignment and the `zonesTable` row-building string to include the swatch.
**How to test:** regenerate all 4 viewers; open each, click 3 buildings with `layout_state:"ruled"` (has
real multi-dwelling zones, not massing_box), confirm each dwelling renders a distinct colour matching its
zone-table swatch row, and confirm massing-box buildings (single "whole" zone) are unaffected (still grey,
no colour-cycling on a single non-dwelling zone).

#### T03 — Merge EU-21 checks/status/verdict as annotation and port the badge banner
**What:** load each district's `<district>_nocore_2026-09-03_r5.json`, index `plates[]` by `building_id`
into `{{building_id: {{"status":..., "verdict":..., "checks":..., "scheme":...}}}}`; attach to `pl_obj` (or a
sibling key on `b_obj`, executor's call — keep it inside `pl_obj` if it's not `None`, else skip, per hard
rule 3) only when the building already has an IDF-derived `pl_obj` from `_build_plan_payload` (never attach
checks to a `no_idf` building that has no geometry to check). Port `openPopup`'s badge-chip rendering
(`08_district_viewer.py:542-553`) into `generate_eu_3d_viewers.py`'s `openPopup` (`:382-450`), gated on the
merged `verdict`/`checks` being present; when absent (join miss), render the modal exactly as it does today
(no badge row), never a placeholder or fabricated "unknown" badge.
**Why:** owner ruling — full cumulative combination, badges included, checks/status treated as annotation
only per rule 3 (never overrides IDF geometry).
**How:** mirror `_load_eu17_sidecar`'s per-district single JSON load, called once in `build_district`
alongside T01's manifest load; join on the same `bid` used everywhere else in the `:945` loop.
**How to test:** for all 4 districts, report join-hit/miss counts (hit = building has both a `pl_obj` and an
EU-21 evidence row); regenerate and open each viewer, click a `verdict:"PASS"` building (expect the green
`PASS ALL 7 CHECKS` banner + 7 chips) and a `verdict:"FAIL"` building (expect red/failing chips on the
specific failed check ids, matching what `PLANS_<district>_..._r5.html` shows for the same `building_id`);
spot-check 2 buildings per district against the PLANS_*_r5.html rendering of the same building for
check-value/badge parity (`show` text and pass/fail colour must match exactly, since it's the same source
JSON).

---

## 7. Stop-and-report points

1. **After T01:** report per-district EUI join-hit/miss counts and confirm the 4 legend min/max values look
   plausible against the pooled EUI figures already reported (London 97.08, Lyon 65.94, Madrid 77.15,
   Bologna 54.94 kWh/m² — per-building spread should bracket these pooled means, not be wildly outside).
2. **After T02:** screenshot or describe 2 `ruled` buildings per district (colour-cycling working, matches
   zone table) before proceeding to T03.
3. **After T03 (final):** report per-district checks join-hit/miss counts and the FAIL-badge spot-check
   parity result against `PLANS_*_r5.html`; STOP if any spot-checked value disagrees (would mean the join
   key or evidence file version drifted, not a badge-styling bug).

---

## 8. Progress log

#### T01 — Wire real per-building EUI from the EU-11 ceiling82 manifest — completed 2026-09-07

**Artifacts:** `scripts/generate_eu_3d_viewers.py` — added `EU11_ROOT` constant (:34), added
`_load_eu11_eui(district)` loader next to `_load_eu17_sidecar` (:793-808), called once per district in
`build_district` (:951, before the `:1007` `b_obj` loop), added `"eui": eui_by_id.get(bid)` to the `b_obj`
dict literal. Regenerated and mirrored all 4 viewers + their `_data/` folders (`buildings.csv`,
`sources.json`, `index.html`, `layouts/`) via `python -m scripts.generate_eu_3d_viewers`.

**Deviations:** none from the plan's approach. One implementation bug found and fixed during T01, before
regenerating: the first `_load_eu11_eui` draft used `df.iterrows()`, which silently upcasts a row's `int64`
`building_id` + `float64 eui_kwh_m2` to a common float dtype — for Bologna, whose manifest `building_id` is
plain numeric (`27410`, no `way/`/`relation/` OSM prefix, unlike the other 3 districts), this turned every id
into `"27410.0"`, matching nothing and silently producing 0/1220 EUI hits. Fixed by reading with
`dtype={"building_id": str}` and iterating via `zip(df["building_id"], df["eui_kwh_m2"])` instead of
`iterrows()` — verified `eui_by_id` length now equals the manifest's unique `building_id` count for all 4
districts (no silent drops).

**Test status:** `eui_by_id` entry count == manifest unique `building_id` count for all 4 districts (Madrid
1174/1174, Lyon 507/507, London 451/451, Bologna 1212/1212 — no parse drops). No browser is available in this
environment (headless Chromium/Playwright not installed) — legend min/max was verified by replicating the
emitted JS's own `B.filter(b=>b.eui!=null)` / `Math.min`/`Math.max` logic directly against the regenerated
scene JSON in Python, which is exact, not a proxy.

**Notes — Stop point 1 report:**
| District | n_res (scene) | EUI join-hit | EUI join-miss (no manifest row) | manifest row, null eui | EUI range | pooled mean (reference) |
|---|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE | 1194 | 1164 | 20 | 10 | 24.7–861.3 | 77.15 |
| FR-LYO-HAUTCOEURPENTES | 530 | 506 | 23 | 1 | 22.2–398.6 | 65.94 |
| GB-LDN-STDUNSTANS | 1242 | 451 | 791 | 0 | 23.3–479.5 | 97.08 |
| IT-BOL-GALVANI2 | 1220 | 1200 | 8 | 12 | 29.5–301.9 | 54.94 |

All 4 legend ranges are non-degenerate (not the 0/200 fallback) and bracket their district's pooled mean.
London's 791 join-miss is large relative to n_res (64%) — expected per §5's own framing (manifest excludes
`no_idf`/failed-on-Speed buildings) and consistent with London's already-small `ruled_count` (17) /
`massing_count` (65) vs `n_res` 1242 seen elsewhere in this arc; not investigated further here, out of T01's
scope. No excluded/non-residential building received a leaked `eui` value (checked all 4 districts: 0/109
Bologna-scale excluded counts carry `eui`).

---

#### T02 — Port per-dwelling colour + zone-table swatches into the floor-plan modal — completed 2026-09-07

**Artifacts:** `scripts/generate_eu_3d_viewers.py` — added the 12-entry `ZONE_COLORS` array verbatim from
`08_district_viewer.py:489-501`, placed immediately before the `/* Floor Plan Modal Logic */` block (:363+).
In `drawFloorPlan`'s dwelling-zone branch: replaced the flat `isWhole ? "#e5e7eb" : "#dbeafe"` fill with
`var zoneColor = isWhole ? "#e5e7eb" : ZONE_COLORS[(zn.di - 1) % ZONE_COLORS.length];` and
`fpCtx.fillStyle = zoneColor;`; stroke colour/width left unchanged (plan scoped the edit to the fill
assignment and the zone-table row only). Added a `Colour` column to the zone table (header + per-row swatch
`<span>` using the same `zoneColor` variable for dwelling rows, `#e5e7eb` for whole/massing-box rows,
`#fef3c7` for the circulation row) so every row stays structurally consistent and every swatch matches
exactly what the canvas already drew, by construction (same variable, same code block). Regenerated in the
same run as T01 (one `python -m scripts.generate_eu_3d_viewers` invocation covers both tasks).

**Deviations:** the plan's own wording says "add a matching colour-swatch cell to each dwelling row" — the
executor's call (per rule 5/hard-rule-3 spirit: no fabricated data, and the plan flags "executor's call" for
adjacent ambiguities in T03) was to add the `Colour` header/cell to every row, not only dwelling rows, so the
table stays well-formed HTML; whole/circulation rows show their own pre-existing hardcoded fill colour as a
swatch (no new colour invented, purely labels what the canvas already renders).

**Test status:** no browser available in this environment (see T01), so per the plan's own "screenshot or
describe" alternative, verified at the data level instead: for each district, found `ls:"ruled"` buildings
with multi-dwelling storeys and confirmed `ZONE_COLORS[(di-1)%12]` cycling for each `di`:
- Madrid `way/432411464` F0: 6 dwellings, `di` 1-6 -> `#287294,#328452,#937320,#9e4438,#7b5294,#b35c34` (6
  distinct colours).
- Lyon `BATIMENT0000000240881213_part0` F0: 8 dwellings, `di` 1-8 -> 8 distinct colours through
  `#8a4f7d`.
- London `way/388460386` F0: 6 dwellings, `di` 1-6 -> same 6-colour sequence as Madrid.
- Bologna `32471` F0: 2 dwellings, `di` 1-2 -> `#287294,#328452`.
Massing-box check: one sampled `ls:"massing_box"` building per district (Madrid `way/100704656`, Lyon
`BATIMENT0000000013365727_part0`, London `way/14325891`, Bologna `32166`) has storey-0 zone kinds `{"w"}`
only — no `"d"` zone present, so the `isWhole` branch (`"#e5e7eb"`, no cycling) is the only branch that can
fire; confirmed unaffected by construction, not just by sampling. Since `zoneColor` is the single source for
both the canvas `fpCtx.fillStyle` and the table swatch `<span>` in the same loop iteration, table/canvas
match is guaranteed by the code structure, not merely observed.

**Notes — Stop point 2:** colour-cycling and swatch-table parity confirmed at the data/code level for 2
`ruled` buildings per district (examples above); massing-box buildings confirmed unaffected (still grey, no
`"d"`-kind zones present). Halting here per the plan's stop-and-report point 2 before starting T03.

---

#### T03 — Merge EU-21 checks/status/verdict as annotation and port the badge banner — completed 2026-09-07

**Artifacts:** `scripts/generate_eu_3d_viewers.py` — added `EU21_ROOT` constant and `CHECK_IDS =
("C1","C3","C4","C5","C6","C10","C11")` (:35-39, same order as `08_district_viewer.py:46`); added
`_load_eu21_evidence(district)` next to `_load_eu11_eui`, per-district single-JSON load into
`{building_id: {"status","verdict","checks","scheme"}}` from `<district>_nocore_2026-09-03_r5.json`'s
`plates[]`; called once per district in `build_district` alongside the T01 EUI load. In the `:1007` per-building
loop, after `pl_obj` is built (ruled/massing_box branches only — never for `no_idf`, rule 3), look up
`evidence_by_id.get(bid)`: if absent, count a miss; if present, count a hit and, only when
`status=="direct"` (the only status carrying real `checks`), build `ch=[[cid, show, pass 0/1], ...]` for each
`CHECK_IDS` and set `pl_obj["chk"]={"v": verdict, "ch": ch}`; otherwise `pl_obj["chk"]=None`. Added
`.checks`/`.chk`/`.chk.ok`/`.chk.bad` CSS verbatim from `08_district_viewer.py:115-118`. In `openPopup`,
after the existing FINDING-204 block, added a new block gated on `pl && pl.chk`: builds the chip row from
`pl.chk.ch` (ported from `08_district_viewer.py:542-550`) and appends either the green
`m-badge emitted` "PASS ALL 7 CHECKS" banner (`v==="PASS"`) or the amber `m-badge fallback` "FAIL" banner
with a "Failing checks: …" line (ported from `:552-561`) — appended to, never replacing, the existing
IDF-derived `ls`-based status box. Also added a one-line `[district] EU-21 checks join: N hit, M miss`
print in `build_district` (next to the existing "Written viewer" print). Regenerated and mirrored all 4
viewers + `_data/` folders via one `python -m scripts.generate_eu_3d_viewers` invocation (covers T01+T02+T03
in the same run, per the director prompt).

**Deviations:** none from the plan's approach. Two executor calls, both within the plan's own "executor's
call" allowance: (1) the checks payload is nested as `pl_obj["chk"]={"v":...,"ch":...}` rather than a flat
sibling key on `b_obj`, since the plan named `pl_obj` as the preferred location "if it's not `None`"; (2) the
ported badge block also carries the reference's "Failing checks: …" line (`08_district_viewer.py:558-561`,
just past the plan's cited `:542-553` range) because the plan's own T03 test explicitly expects "red/failing
chips on the specific failed check ids" and the FAIL branch is not meaningfully portable without it — the
cited line range reads as illustrative, not a hard cutoff (confirmed by the render-logic check below).

**Test status:** no browser available in this environment (as in T01/T02), so verified at the data level:
`python -m py_compile` clean; `node -e "new Function(js)"` syntax-checked the emitted `<script>` block on all
4 regenerated viewers (all OK); replicated the ported JS chip/badge logic in Python against the regenerated
scene JSON for one PASS building and one FAIL building (Bologna `31323`/`28237`) and confirmed the exact
expected shape — green `PASS ALL 7 CHECKS` + 7 `chk ok` chips for the PASS building, amber `FAIL` + "Failing
checks: C5" + 6 `chk ok`/1 `chk bad` (on C5) for the FAIL building; confirmed T01 (EUI non-null count,
Bologna 1200) and T02 (`ZONE_COLORS[` present) outputs are unchanged by the T03 regeneration; confirmed all
4 primary (`openubem/outputs/3D/`) vs mirror (`docs/docs_ACTIVE/europeanLocations/outputs_3D/`) viewer HTML
files are byte-identical after regeneration.

**Notes — Stop point 3 report:**
Checks join-hit/miss (hit = building has both a `pl_obj` and an EU-21 evidence row, any status):
ES-MAD-BERRUGUETE 961 hit / 0 miss, FR-LYO-HAUTCOEURPENTES 297 hit / 0 miss, GB-LDN-STDUNSTANS 82 hit / 0
miss, IT-BOL-GALVANI2 1204 hit / 0 miss — every `ruled`/`massing_box` building in all 4 districts has an
EU-21 evidence row (no true join misses). Of those hits, the ones actually carrying a rendered badge
(`status=="direct"`, i.e. `chk` non-null) are fewer: ES-MAD 955/961, FR-LYO 295/297, GB-LDN 75/82, IT-BOL
1204/1204 — the gap is evidence rows present but with `status` `GENERIC_NO_CENSUS`/`REFUSED_K_GT_12` (no
`checks` in the source JSON, per rule 3 no fabricated badge is shown for those, exactly as `08_district_viewer.py`
itself only builds `ch` for `status=="direct"`).

FAIL-badge spot-check parity: 2 buildings per district (1 `verdict:"PASS"`, 1 `verdict:"FAIL"`), compared
`b.pl.chk.v` and `b.pl.chk.ch` (our viewer) against `b.v`/`b.ch` for the same `building_id` in the
corresponding `PLANS_<district>_nocore_2026-09-03_r5.html`'s own embedded scene JSON (same source EU-21
evidence file): ES-MAD `way/435822228` (PASS) / `way/400445221` (FAIL), FR-LYO
`BATIMENT0000000240877523_part0` (PASS) / `BATIMENT0000000240881166_part0` (FAIL), GB-LDN `way/396619819`
(PASS) / `way/381466697` (FAIL), IT-BOL `31323` (PASS) / `28237` (FAIL) — all 8 buildings: verdict match and
full `ch` array match (every check id's `show` text and `pass` bit) exact, byte-for-byte, no disagreement.
No STOP condition triggered. This is the plan's final stop-and-report point (§7.3); the arc is complete.
