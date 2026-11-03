# PLAN — draw the ruled circulation polygon in the EU 3D viewers (`FINDING 206`)

- **Arc**: European locations × Step 8, follow-on to `EU-13B`/`EU-14B`.
- **Date**: 2026-08-30.
- **DESIGN pointer**: `docs/docs_ACTIVE/europeanLocations/rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md`
  §3.1/§6 (ruled acceptance sheet — circulation zone must be present per building).
- **Trigger**: `docs/docs_ACTIVE/europeanLocations/debugs/docs/INVESTIGATION_viewer-circulation-not-drawn_2026-08-30.md`
  §1, `FINDING 206`. Owner approved the fix ("recommend yes" accepted 2026-08-30).

## 1. Hard rules for executor

- Do not touch `T06` (`D-EU-36` carve-vs-add) — stays blocked/open, out of scope.
- Do not re-open `FINDING 199`/`DR16` (Lyon/Bologna campaign-wide audit) — out of scope.
- Do not touch `previous/MVP_european_locations.md`, `previous/WALKTHROUGH_european_locations.md`, MVP
  Table 9.7, root `main.py`, or any OVERVIEW/DESIGN doc.
- No live-network integration tests.
- Regenerate sidecars + viewers for all four districts after the code change; verify mirror byte-identical
  (`sha256sum` + `diff -rq`) between `openubem/outputs/3D/` and `docs/docs_ACTIVE/europeanLocations/outputs_3D/`,
  same as prior `EU-13B T09` practice.
- Do not commit — git is handled externally.

## 2. File layout (only these files change)

- `scripts/emit_eu11_layout_sidecars.py` — serialize `circulation_polygon` into each floor dict.
- `scripts/generate_eu_3d_viewers.py` — carry it into the scene JSON and draw it in `drawFloorPlan`.
- New: `tests/geometry/test_eu13b_circulation_sidecar.py` (or similar name) — one small unit test.
- `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` — register `FINDING 206`'s fix per the house rule.
- This plan doc — progress log, §7.

Do not touch `openubem/geometry/european_residential.py` — the geometry is already correct; only the two
downstream files are missing the pass-through.

## 3. Dependency decisions (pinned)

- No new dependency. Reuse `shapely.geometry.polygon.orient` and `ZONE_WINDING_SIGN`, already imported in
  `emit_eu11_layout_sidecars.py`.
- `circulation_polygon` is `BaseGeometry | None` (`openubem/geometry/european_residential.py:261`). Empirically
  it is either `None` or a single `Polygon` (`_centred_circulation_region` returns a `box(...)` rotated —
  `european_residential.py:237-249`), **except** the `l_shape_decomposition` combiner
  (`european_residential.py:707-714`), which deliberately sets the combined `circulation_polygon=None` even
  though both wings had one — leave that as `None` (no combined shape to draw), do not attempt to recover the
  two wing corridors.
- If a future scheme ever returns a `MultiPolygon`, fail closed (log and skip drawing that floor's circulation,
  do not crash the emitter) — do not add silent unary-union merging speculatively; there is no such case in the
  current 2026-08-30 fleet (confirmed in the investigation doc's 5-building cross-check, all single `Polygon`).

## 4. DESIGN facts with line citations

- `european_residential.py:261` — `circulation_polygon: BaseGeometry | None` field on the storey-layout result.
- `european_residential.py:304-306` — computed as `_centred_circulation_region(...)`, non-null for every
  non-refused, non-`l_shape_decomposition`-combined building.
- `emit_eu11_layout_sidecars.py:281-311` — the `for group in building_layout.storey_groups:` loop already binds
  `storey_layout = group.layout` (line 282), which is where `storey_layout.circulation_polygon` is directly
  available — no new lookup needed, just read the field already in scope.
- `emit_eu11_layout_sidecars.py:284-292` — existing per-zone serialization pattern to mirror:
  `orient(poly, sign=ZONE_WINDING_SIGN)` then `list(poly.exterior.coords)[:-1]`.
- `generate_eu_3d_viewers.py:953-967` — where the sidecar's `floors[i].zones` is remapped into the scene's
  `floors_data[i].zones` (offsetting by `cx, cy` and renaming `coords_m` → `r`). The same remap must be applied
  to a new `circulation` key.
- `generate_eu_3d_viewers.py:466-534` (`drawFloorPlan`) — draws `floorData.zones` only; the dwelling index
  label `"D" + (z+1)` and the zones-table rows are built from the same loop. A new `floorData.circulation` draw
  call must not perturb this indexing (draw it as a separate step, not inserted into the `for(var z=...)` loop).

## 5. Task list

### T01 — Serialize `circulation_polygon` in the sidecar

**What.** In `emit_eu11_layout_sidecars.py`, inside the `for group in building_layout.storey_groups:` loop
(around line 281-311), when `storey_layout.circulation_polygon is not None`, orient it and extract its exterior
ring the same way zones are extracted, and store it as a new `"circulation"` key on each floor dict (parallel
to the existing `"zones"` key), `None` when there is no circulation polygon for that storey.

**Why.** This is the actual root cause of `FINDING 206` — the geometry is computed but discarded before this
point.

**How.**
```python
circ_ring = None
if storey_layout.circulation_polygon is not None:
    circ_poly = orient(storey_layout.circulation_polygon, sign=ZONE_WINDING_SIGN)
    circ_ring = list(circ_poly.exterior.coords)[:-1]
```
computed once per `group` (outside the `for s_idx in range(...)` sub-loop, same as `g_zones`), then add
`"circulation": circ_ring` to the dict appended in `floors_list.append({...})` (line 298-311).

**How to test.** Re-run the emitter for Madrid only first (`district="ES-MAD-BERRUGUETE"` scoped run, or full
run if the script has no per-district flag — check `emit_eu11_layout_sidecars.py`'s `argparse`/dispatch before
assuming), then `python -c` load `way/388485191`'s sidecar JSON and confirm `floors[0]["circulation"]` is a
non-empty coordinate list (this building has scheme `ruled_grid_2x2` or similar per the investigation doc's
table, not `l_shape_decomposition`, so it must be non-null).

### T02 — Carry `circulation` into the viewer scene JSON

**What.** In `generate_eu_3d_viewers.py`'s floor-remap loop (lines 953-967), add a parallel remap of
`fl.get("circulation")`: if present, offset each point by `(-cx, -cy)` and round to 2 decimals exactly like the
zone ring (line 957), producing `"circulation": {"r": circ_r}` or `"circulation": None` on each `floors_data[i]`
dict.

**Why.** Without this the sidecar's new field never reaches the HTML.

**How.** Mirror the existing `zr = [[round(pt[0]-cx,2), round(pt[1]-cy,2)] for pt in z["coords_m"]]` pattern
(line 957) for `fl.get("circulation")`.

**How to test.** Regenerate Madrid's viewer only if the script supports a single-district build
(`build_district("ES-MAD-BERRUGUETE")` or similar — check the script's `if __name__` dispatch), grep the
embedded scene JSON for `"circulation"` and confirm at least one non-null entry exists for `way/388485191`.

### T03 — Draw the circulation polygon in `drawFloorPlan`

**What.** In `drawFloorPlan` (`generate_eu_3d_viewers.py:466-534`), after the footprint outline is drawn
(line 495) and before the dwelling-zone loop (line 502), add: if `floorData && floorData.circulation && floorData.circulation.r`,
draw that ring filled with a distinct, clearly-non-dwelling style (e.g. `rgba(140,140,140,0.55)` fill, dashed
`#ffffff` stroke) and a small centred label (`"C"` or `"Circulation"`, matching the `"D"+(z+1)` label style at
line 525). Add one row to `zonesTable` for it (e.g. `<tr><td>Circulation</td>...</tr>`), separate from the
dwelling rows so `z+1` numbering in the existing loop is untouched.

**Why.** This is the second half of `FINDING 206` — the emitter fix alone does not change what the owner sees
until the canvas draws it.

**How.** Reuse the same `fx()/fy()` projection functions already defined at lines 481-482 (they close over
`minx/maxx/etc.` computed from the building footprint, valid for any ring in the same coordinate frame).

**How to test.** Open the regenerated Madrid viewer in a browser (or headless-render check via a JS scene-JSON
parse, same technique used in the investigation doc), click `way/388485191`, confirm a distinct grey/hatched
shape is visible inside the dwelling zones, not overlapping any dwelling colour, and that the zones table still
lists exactly 6 dwellings (unchanged from the investigation doc's cross-check) plus one new circulation row.

### T04 — Regenerate sidecars + viewers for all four districts, verify mirror

**What.** Run, in order: `.venv/Scripts/python.exe scripts/emit_eu11_layout_sidecars.py` then
`.venv/Scripts/python.exe scripts/generate_eu_3d_viewers.py` (full run, all four districts — same two-command
sequence as `EU-13B T09`/`EU-14B T03`).

**Why.** Only Madrid was spot-checked in T01-T03; all four districts' sidecars and viewers must carry the fix.

**How to test.**
- Re-run the investigation doc's §1 zone-count cross-check on the same 5 buildings — must still match exactly
  (this fix must not change any dwelling zone, count, or area — only add the circulation ring).
- `sha256sum` the four `openubem/outputs/3D/eu_*_viewer.html` files against their
  `docs/docs_ACTIVE/europeanLocations/outputs_3D/` mirrors — must be identical (same practice as `EU-13B T09`).
- Confirm `has_unconditioned_core`/other unrelated badges are unchanged (regression guard, same style as the
  `EU-13B T07` check).

### T05 — Unit test + debug-reference registration

**What.** Add one small unit test asserting a known ruled-grid building's sidecar carries a non-empty
`circulation` ring and an `l_shape_decomposition`-scheme building carries `circulation: None` (both cases
matter — the negative case documents the pinned decision in §3). Then append one bullet to
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`'s matching European-locations chapter registering
`FINDING 206`'s fix, per the house format.

**Why.** House rule: an error is not closed until it is registered; this fix should not regress silently.

**How to test.** `pytest -q <new test file>` — must pass.

## 6. Stop-and-report points

1. After T03 (Madrid-only spot check) — report the before/after popup screenshot-equivalent (zone-count table
   + confirmation the circulation ring rendered) before touching the other three districts.
2. After T04 (all-district regeneration + mirror verification) — report pooled-EUI-unchanged confirmation (this
   fix touches geometry serialization only, not the IDF/Speed path, so all four districts' pooled EUI figures
   in `RESULTS_EU-11.md` must be untouched) and the sha256/diff -rq mirror result.

## 7. Progress log

(append one entry per completed task, house format, below this line)

#### T01 — Serialize `circulation_polygon` in the sidecar — completed 2026-08-30

Artifacts: `scripts/emit_eu11_layout_sidecars.py` (lines 293-308) — computed `circ_ring` once per `group`
(mirroring the existing `orient(...)`/`list(poly.exterior.coords)[:-1]` zone pattern) and added a
`"circulation": circ_ring` key to each floor dict. Ran `emit_layouts_for_district("ES-MAD-BERRUGUETE")`
directly (script has no per-district CLI flag; used the existing callable) — 952 sidecars written, outcome
counts unchanged from the pre-existing manifest (`DWELLING_LAYOUT_EMITTED`: 900,
`DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`: 2, `FALLBACK_PENDING_LAYOUT`: 50).

Deviations: none.

Test status: loaded `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/layouts/way/388485191.json` —
all 7 floors carry a non-empty `circulation` ring (4 points each, `ruled_grid_3x2` scheme), dwelling zone
counts per floor `[6,6,6,5,5,5,5]` unchanged from the investigation doc's ruled table.

Notes: none.

#### T02 — Carry `circulation` into the viewer scene JSON — completed 2026-08-30

Artifacts: `scripts/generate_eu_3d_viewers.py` (floor-remap loop, after the `floors_data.append(...)` zones
block) — added `circ = fl.get("circulation")`, offset/rounded into `circ_r` mirroring the existing `zr`
pattern (line 957), and set `"circulation": {"r": circ_r} if circ_r else None` on each `floors_data[i]` dict.

Deviations: none.

Test status: ran `build_district("ES-MAD-BERRUGUETE")` (script's existing per-district function, no separate
CLI flag needed) — parsed the regenerated viewer's embedded `<script type="application/json" id="scene">`
JSON and confirmed `way/388485191`'s `k.floors[i].circulation.r` is a non-null 4-point ring on all 7 floors,
alongside unchanged `zones` counts `[6,6,6,5,5,5,5]` (38 dwelling-zone total, matching the sidecar).

Notes: none.

#### T03 — Draw the circulation polygon in `drawFloorPlan` — completed 2026-08-30

Artifacts: `scripts/generate_eu_3d_viewers.py`, `drawFloorPlan` — inserted a circulation-drawing block after
`floorData` is resolved and before the dwelling `for(var z=...)` loop: draws `floorData.circulation.r` filled
`rgba(140,140,140,0.55)` with a dashed white stroke and a centred `"C"` label, and builds a separate `circHtml`
row (`<tr><td>Circulation</td>...`) appended to `zonesTable` after the dwelling rows (or used alone via a new
`else if(circHtml)` branch when no dwelling zones exist). The dwelling loop's `z+1` indexing is untouched.

Deviations: none.

Test status: `node --check` on the extracted JS logic block of the regenerated viewer passed (syntax ok).
Data-level "headless-render check via a JS scene-JSON parse" (per the plan's stated alternative to opening a
browser): confirmed `way/388485191`'s scene-JSON `circulation.r` is present and non-empty on every floor,
matching T02. Mirror check: `sha256sum` of `openubem/outputs/3D/eu_ES-MAD-BERRUGUETE_viewer.html` and its
`docs/docs_ACTIVE/europeanLocations/outputs_3D/` copy are byte-identical
(`9b42ce03f90530a9288e8b810141d68b8307dd39c1870a33906a2be78113b1d8`).

Notes: did not open the HTML in an actual browser (no browser automation tool available in this run) — relied
on the JS syntax check + scene-JSON data verification instead, per the plan's own stated alternative. Full
visual/on-screen confirmation still pending user or a browser-capable check if required.

#### T04 — Regenerate sidecars + viewers for all four districts, verify mirror — completed 2026-08-30

Artifacts: ran `.venv/Scripts/python.exe scripts/emit_eu11_layout_sidecars.py` then
`.venv/Scripts/python.exe scripts/generate_eu_3d_viewers.py`, full runs, no per-district flags — both scripts'
own `main()` iterate `DISTRICTS`/`DISTRICT_SPECS` over all four districts and mirror automatically. Sidecar
outcome counts: `ES-MAD-BERRUGUETE` `{DWELLING_LAYOUT_EMITTED: 900, DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT: 2,
FALLBACK_PENDING_LAYOUT: 50}` (unchanged from T01's Madrid-only run), `FR-LYO-HAUTCOEURPENTES`
`{DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT: 268, FALLBACK_PENDING_LAYOUT: 15}`, `GB-LDN-STDUNSTANS`
`{DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT: 59, FALLBACK_PENDING_LAYOUT: 21}`, `IT-BOL-GALVANI2`
`{DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT: 1058, FALLBACK_PENDING_LAYOUT: 143}`. All four viewers regenerated and
mirrored ("All four European district 3D viewers regenerated and mirrored successfully").

Deviations: none.

Test status:
- Zone-count cross-check (investigation doc §1, same 5 buildings), parsed from each regenerated viewer's
  embedded scene JSON (`k.floors[i].zones`): `way/388485191` `[6,6,6,5,5,5,5]`=38, `way/391279229`
  `[6,6,6,6,5,5,5,5]`=44, `relation/3730743` refused/0 zones, `relation/12704090` `[6,6,6,6,6]`=30,
  `way/420409335` `[7,7,6]`=20 — all five exactly match the investigation doc's table, unchanged.
  `circulation` is now present (non-null `r` ring) on every floor of `way/388485191` and `way/391279229`
  (`ruled_grid_3x2`); `None` on every floor of `way/420409335` (`l_shape_decomposition`, per the pinned §3
  decision) and, newly observed, also `None` on every floor of `relation/12704090`
  (`equal_strip_multi_angle_sweep`) — confirmed at the sidecar level
  (`circulation_polygon` is already `None` there upstream of this fix, not introduced by it; out of scope to
  investigate further per the plan's hard rules).
- `sha256sum` of all four `openubem/outputs/3D/eu_*_viewer.html` against their
  `docs/docs_ACTIVE/europeanLocations/outputs_3D/` mirrors: all four identical
  (`ES-MAD-BERRUGUETE 9b42ce03…8113b1d8`, `FR-LYO-HAUTCOEURPENTES 30d96744…27889f96`,
  `GB-LDN-STDUNSTANS 4aca3f93…96254b9ea`, `IT-BOL-GALVANI2 5bfa497a…8de11682`). `diff -rq` on all four
  `eu_*_data` mirror folders: no differences.
- `has_unconditioned_core`/`core` badge spot-checked on all 5 cross-check buildings: `False` throughout,
  unchanged (regression guard only, not re-investigated further).

Notes: `RESULTS_EU-11.md` pooled-EUI figures not touched by this task (geometry-serialization-only change, no
IDF/Speed path involved) — not re-verified here beyond that structural argument, per the plan's own framing of
stop-and-report point 2.

#### T05 — Unit test + debug-reference registration — completed 2026-08-30

Artifacts: `tests/geometry/test_eu13b_circulation_sidecar.py` (new) — two tests:
`test_ruled_grid_building_carries_non_empty_circulation_ring_per_floor` (asserts `way/388485191`'s sidecar,
scheme `ruled_grid_3x2`, carries a `>=3`-point `circulation` ring on every floor) and
`test_l_shape_decomposition_building_carries_null_circulation_per_floor` (asserts `way/420409335`'s sidecar,
scheme `l_shape_decomposition`, carries `circulation: None` on every floor). Registered `FINDING 206`'s fix in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` under the `## European locations EU-14B` chapter (most
recent/specific EU chapter; TOC unchanged, matching the existing untitled-in-TOC precedent for EU-13B/EU-14B).

Deviations: none.

Test status: `.venv/Scripts/python.exe -m pytest -q tests/geometry/test_eu13b_circulation_sidecar.py` → `2
passed`.

Notes: none.
