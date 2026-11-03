# B05d — `layout_assign` substituted-building overlap diagnosis (E-LA-28)

Date: 2026-07-26. Scope: read-only measurement (plan §B05d). No production code touched.

## Superseded: the "blank scene" report

The session that produced this file's first draft investigated a reported "blank scene" in
`nyc_suburban_layout_assign_viewer.html` / `la_suburban_layout_assign_viewer.html` and found (and
reproduced, headlessly) a real `TypeError` in `openubem/viz/shell/viewer_app.mjs`'s
`_buildLegend()` when a scene has zero CityObjects with a numeric `total_eui_kwh_m2`. **That
investigation is superseded**: on a second look the user confirmed both viewers **do render** —
they were simply slow to load given their size (26.4 MB / ~190k surfaces). The visible defect is
not a blank canvas, it is **substituted buildings overlapping their neighbours** (below). Any code
change made during the blank-scene investigation (`openubem/viz/shell/viewer_app.mjs`,
`openubem/viz/shell/viewer.js`, and the two `*_layout_assign_viewer.html` files) was **reverted**
in this same session — `git status` on `openubem/viz/shell/` is clean and both HTML files are back
to their original byte sizes (26,353,450 / 24,911,108 bytes). Nobody needs to re-run that
investigation.

---

## 1. Where the placement anchor comes from

**Two separate mechanisms compound. Neither re-centres or re-orients the substituted prototype
onto the real footprint.**

### 1a. `builder.py` never repositions the scaled baseline onto the real footprint

`openubem/idf/builder.py`, `build()`:

- Line 419: `poly_local, cx, cy = translate_to_origin(poly)` — computes the **real** building's
  local-frame polygon and its UTM centroid `(cx, cy)`.
- Lines 435–481, the `strategy == "layout_assign"` success branch (baseline available):
  ```
  443:            else:
  444:                # Real baseline available: the baseline IDF already carries its own
  445:                # geometry/zones/loads/schedules/HVAC/service-loads (plan §4 architecture
  446:                # table) — scale it in place and skip the standard per-building pipeline.
  447:                real_area = footprint_area * num_floors
  448:                baseline_area = layout_assigner.get_registry().get_baseline_area(arch)
  449:                scale = layout_assigner.calculate_scaling_factor(real_area, baseline_area)
  450:                layout_assigner.scale_baseline_idf(self.idf, scale)
  451:                layout_assigner.purge_baseline_outputs(self.idf)
  ```
  `poly_local`/`cx`/`cy` (line 419) are **never referenced again** inside this branch — grepped
  the full 435–481 span, neither name appears. Compare to the standard path (line 488,
  `extrude_geometry(self.idf, zones, context)`), which **is** built from `poly_local` via
  `build_zones(osm_id, poly_local, ...)` at line 433 — but the layout_assign success branch
  returns at line 481, before line 483 (`copy_schedule_library`) or line 488 are ever reached.
  **The baseline IDF's own geometry is scaled in place and saved untouched in position** — nothing
  translates or rotates it onto the real footprint.

### 1b. `scale_baseline_idf()` scales surface-local vertices but never the ZONE objects' own Origin

`openubem/geometry/layout_assigner.py`:

- Lines 248–253, `_GEOMETRY_SURFACE_CLASSES`:
  ```
  _GEOMETRY_SURFACE_CLASSES = (
      "BUILDINGSURFACE:DETAILED",
      "FENESTRATIONSURFACE:DETAILED",
      "SHADING:ZONE:DETAILED",
      "SHADING:BUILDING:DETAILED",
  )
  ```
  `"ZONE"` is not in this tuple. The only other place `"ZONE"` appears in the file is line 511,
  inside `parse_baseline_zones()`, which only **reads** zone floor area for the manifest — it does
  not scale anything.
- Lines 440–443, the only geometry-scaling loop in `scale_baseline_idf()`:
  ```
  440:    for cls in _GEOMETRY_SURFACE_CLASSES:
  441:        for surf in idf.idfobjects.get(cls, []):
  442:            scaled_coords = [(x * planar_k, y * planar_k, z) for x, y, z in surf.coords]
  443:            surf.setcoords(scaled_coords)
  ```
  This multiplies each surface's own (`BuildingSurface:Detailed` etc.) vertex list by
  `planar_scale_factor`. Under `GlobalGeometryRules ... Relative` (confirmed below), those
  coordinates are **relative to the surface's own `Zone`'s X/Y/Z Origin** — the `Zone` object's
  Origin fields are a *second*, separate set of numbers that this loop never touches.

**Consequence, confirmed on real generated output, not just at the call site:**

`scratchpad/t18_t01_t03_work/work/nyc_suburban/step3_layout_assign/idfs/way_1014146136.idf`
(`ApartmentMidRise`, saved by the pipeline after `scale_baseline_idf()` ran on it):

```
GLOBALGEOMETRYRULES,
    LowerLeftCorner,          !- Starting Vertex Position
    Clockwise,                !- Vertex Entry Direction
    Relative;                 !- Coordinate System

ZONE,
    Office,                   !- Name
    0,                        !- Direction of Relative North
    34.7455054899131,         !- X Origin
    0,                        !- Y Origin
    0,                        !- Z Origin
```

The raw, **unscaled** baseline file
(`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`)
has the *same* `Office` zone at `X Origin = 34.7455054899131` — identical to 13 significant
figures. The Zone Origin was not scaled at all.

Meanwhile the **surface**-local coordinates in the same generated file *were* scaled: wall
`g SWall SWA` (zone `G SW Apartment`) reads `Vertex 1 X = 1.1165537935991205` /
`Vertex 3 X = 0` (length 1.1166 m) in the generated file, versus `Vertex 1 = (0,0,0)` /
`Vertex 3 = (11.581835, 0, 3.047851)` (length 11.5818 m) in the raw baseline — a **0.0964×**
linear scale, i.e. this wall genuinely shrank.

So: individual walls shrink correctly inside their own zone, but the zones themselves stay
scattered across the **prototype's own unscaled footprint grid** (Office zone's origin 34.75 m
away from the SW corner, exactly as in the S=1 baseline). For a many-zone, spatially-spread
archetype like `MidriseApartment` (zone origins spanning 0–34.75 m in X, 0–9.30 m in Y per the
`ZONE` block dump above), the building's **overall envelope stays pinned near the unscaled S=1
footprint** no matter how small the target `planar_scale_factor` is — only the *individual rooms*
shrink, the building does not.

### 1c. The viewer places the (already-mis-scaled) IDF geometry exactly where the real building's centroid is, nothing more

`openubem/viz/cityjson_emitter.py`, `build_cityjson()`:
```
137:        def to_surface(verts) -> list[list[int]]:
138:            ring = [add_vertex(x + cx - ox, y + cy - oy, z)
139:                    for (x, y, z) in verts]
```
`cx, cy` (line 133, from `centroids[osm_id]`) is the **real** building's footprint centroid in
UTM, for every resolution mode alike. `x, y, z` come straight from
`collect_geometry(r.idf_path, recentre=False)` (line 134) — i.e. whatever the saved IDF's own
zone-origin + surface-local coordinates say, unmodified. `openubem/viz/geometry_extract.py` lines
516–517 (`_is_relative_coords` / `_build_zone_origins`) and line 643
(`zone_origins.get(zone_name, ...)`) apply the IDF's own `Relative`/Zone-Origin convention exactly
as written — this is a faithful read of whatever the IDF says, not a viewer-introduced bug (see
§4).

**Net anchor rule, confirmed both by code and by measurement (§2):** `substituted_world_position =
real_footprint_centroid_UTM + baseline_prototype's_own_S=1_local_coordinates` (the surface-level
scaling shrinks individual rooms but not the zone-origin grid, so the emitted geometry is anchored
at the real centroid but keeps ~the baseline's full, unscaled spatial footprint).

---

## 2. Overlap, quantified — both scenes, `auto` as control

Method (`scripts/analysis/measure_layout_assign_overlap.py`): parse the embedded CityJSON out of
each viewer HTML's `<script id="scene-data">` block; for every CityObject, take the convex hull of
every XY vertex across its LOD-1 (mass, walls+roof) geometry as an approximate footprint polygon
(shape-agnostic, works identically for a real OSM footprint and a substituted DOE mass — this can
slightly over-count area/overlap for concave buildings, but the same method is applied uniformly
to both the treatment and control scene, so the comparison stays fair); build a `shapely.STRtree`
and count all pairwise intersections with area > 0.5 m² (numerical-noise threshold).

| scene | n buildings | overlapping pairs | buildings in ≥1 overlap | % | overlap area (m²): min / median / p90 / max |
|---|---|---|---|---|---|
| `nyc_suburban_layout_assign_viewer.html` | 1,589 | **4,043** | 1,561 | **98.24%** | 0.51 / 119.47 / 376.49 / 669.67 |
| `nyc_suburban_real_auto_viewer.html` (control) | 1,589 | **0** | 0 | **0.00%** | not found |
| `la_suburban_layout_assign_viewer.html` | 1,343 | **4,003** | 1,305 | **97.17%** | 0.52 / 160.43 / 420.71 / 675.33 |
| `la_suburban_real_auto_viewer.html` (control) | 1,343 | **15** | 24 | **1.79%** | 0.77 / 27.84 / 184.93 / 249.41 |

The `la_suburban` real-`auto` control's 15 pairs / 1.79% is plausibly genuine (attached/row
buildings sharing a wall in OSM); it is two orders of magnitude below the `layout_assign` scenes'
overlap rate either way.

**Placement-anchor mismatch, by archetype** (`scripts/analysis/measure_offset_by_archetype.py`):
distance between each building's *computed* footprint-hull centroid and its own
`footprint_centroid_utm` attribute (the real centroid the emitter was supposed to place it at):

| archetype | nyc n | nyc median offset (m) | nyc min–max | la n | la median offset (m) | la min–max |
|---|---|---|---|---|---|---|
| MidriseApartment | 979 | 24.659 | 24.659–24.660 | 1,283 | 24.659 | 24.659–24.660 |
| SmallOffice | 316 | 16.640 | 16.639–16.640 | 38 | 16.640 | 16.639–16.640 |
| MediumOffice | 1 | 29.993 | — | 4 | 29.993 | 29.993 |
| Warehouse | — | — | — | 3 | 55.241 | 55.241 |
| real_auto control (all archetypes) | 1,589 | 0.0002 | 0.000–3.891 | 1,343 | 0.191 | 0.000–6.433 |

The layout_assign offset is **near-constant within an archetype** (min≈max to 3 decimals) and
**independent of the real building's own location or size** — it is a property of the baseline
prototype file, not of the real neighbourhood. Confirmed directly:
`scripts/analysis/measure_raw_baseline_footprint.py` on the raw, unscaled
`ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` reports its own convex-hull centroid at
`(23.164, 8.458)`, i.e. **24.659 m from its own local origin (0,0)** — the exact figure measured
in both viewer scenes. The control scene's offset is ~0 (real footprint centroid ≈ computed hull
centroid, as expected when geometry is built directly from the real footprint).

---

## 3. Shape/orientation, not just area — named-building comparison

`scripts/analysis/measure_offset_by_archetype.py`, minimum-rotated-rectangle width × depth
(shapely) for the SAME `osm_id`/CityObject key in both scenes:

| building | archetype | real `auto` (w × d, aspect) | `layout_assign` (w × d, aspect) |
|---|---|---|---|
| `relation/6584771` (la) | MidriseApartment | 15.2 × 22.3 m, 1.46 | 16.9 × 46.3 m, **2.74** |
| `relation/6584772` (la) | MidriseApartment | 14.5 × 17.4 m, 1.20 | 16.9 × 46.3 m, 2.74 |
| `relation/6584773` (la) | MidriseApartment | 14.3 × 18.6 m, 1.30 | 16.9 × 46.3 m, 2.74 |
| `relation/6584774` (la) | MidriseApartment | 15.0 × 23.8 m, 1.58 | 16.9 × 46.3 m, 2.74 |
| `way/1010383033` (nyc) | SmallOffice | 9.2 × 14.5 m, 1.58 | 19.7 × 28.9 m, 1.47 |
| `way/1014146117` (nyc) | MidriseApartment | 11.4 × 19.2 m, 1.69 | 16.9 × 46.3 m, 2.74 |

Every `MidriseApartment` substitution in both scenes shows the **identical** 16.9 × 46.3 m, 783.6
m² footprint (confirmed to 6 decimal places — `scripts/analysis/check_identical_shapes.py`: nyc's
979 MidriseApartment CityObjects collapse to only 6 distinct area values, all within 783.62–783.68
m²; la's 1,283 collapse to 5), regardless of the real building's own footprint being anywhere from
133.6 to 321.6 m² across the sampled set. This is the raw, **unscaled** baseline plate
(783.654 m², measured directly off the S=1 IDF, §1b) to within floating-point rounding — i.e. in
these two scenes the emitted geometry is, for `MidriseApartment`, indistinguishable from *no
scaling having reached the overall envelope at all* — consistent with §1b's zone-origin mechanism,
which leaves the outer envelope pinned to the unscaled zone-origin grid regardless of how much the
individual rooms inside it shrink.

**`SmallOffice`'s case is not explained by the zone-origin mechanism** — its raw baseline
(`ASHRAE901_OfficeSmall_STD2022_Buffalo.idf`) uses the DOE "Core+Perimeter" convention where every
`Zone`'s own Origin is `(0,0,0)` (all positional information lives in the surface-local vertices,
which §1b showed thefine-grained loop *does* scale correctly — verified independently on
`scratchpad/e-la-20-fix/f01_work/idfs/f01_ts2_init_fat/idfs/way_772627076.idf`, a different
SmallOffice-template output, where `Core_ZN_floor`'s vertices are consistently scaled ~0.207× on
both X and Y relative to the raw baseline). Yet all 316 (nyc) / 38 (la) `SmallOffice` CityObjects
in these two specific viewer scenes show the exact same 567.9774 m² footprint — the raw, unscaled
baseline plate again. **This is flagged as an open, unresolved observation, not asserted as a
mechanism**: whatever produced these two specific "A4-bis" viewer artifacts may not be exercising
per-building `planar_scale_factor` at all for `SmallOffice`, for a reason this diagnosis did not
track down (the plan doc's own audit already struck A4-bis's hand-built spot-check table as
"arithmetic, not measurement," and noted none of its 6 named buildings has an IDF on disk — see
`PLAN_storey-matching_implementation.md` lines 946–953). Whoever owns B05 should treat the
`MidriseApartment` §1b mechanism as confirmed-on-real-output, and re-derive `SmallOffice`'s number
from a real per-building IDF before relying on it.

The coordinator's hypothesis is confirmed for the dominant case: `MidriseApartment`'s plan is a
long bar (aspect ratio 2.74, 16.9 × 46.3 m) that, even area-for-area, would not fit most compact
suburban parcels (real comparison buildings above run 14–15 m wide, 17–24 m deep) — and because
§1b/§1c show the substitution isn't even area-shrunk in these two scenes, the bar is dropped at
essentially full DOE-prototype size onto a parcel built for a building 2.5–6× smaller in area.

---

## 4. In the IDF geometry, or only in the viewer's placement?

**In the IDF geometry itself.** Both mechanisms in §1 operate on the `eppy`/`geomeppy` IDF object
before it is saved:

- `layout_assigner.scale_baseline_idf(self.idf, scale)` (`builder.py:450`) mutates
  `self.idf` in place, scaling `BuildingSurface:Detailed` vertices but not `Zone` Origins
  (§1b) — this is the actual EnergyPlus input model.
- `self.idf.save(str(idf_path))` (`builder.py:467`) writes that same, already-mis-scaled geometry
  to disk as the per-building `.idf` file EnergyPlus would simulate.
- Confirmed directly on a real saved file
  (`scratchpad/t18_t01_t03_work/work/nyc_suburban/step3_layout_assign/idfs/way_1014146136.idf`,
  §1b): its `Zone` Origins match the raw baseline's S=1 values exactly, and this is the file the
  pipeline actually wrote to disk, not something the viewer synthesized.
- `openubem/viz/geometry_extract.py` reads this file with the standard IDF `Relative`/Zone-Origin
  resolution (lines 516–517, 643) — the same code path used for every other resolution mode — and
  applies no `layout_assign`-specific transform of its own (grepped: no `layout_assign` or
  `resolution_mode` branch anywhere in `geometry_extract.py` or `cityjson_emitter.py`). The viewer
  is rendering the IDF's own geometry faithfully; it is not introducing the overlap.

**Consequence:** this is a defect in the actual EnergyPlus input model, not a rendering artifact.
Any downstream consumer of these IDFs' geometry (not just the viewer) — surface-to-surface view
factors, self-shading within the building, a future site-massing export — inherits the same
overlap/mis-scale.

---

## 5. Does `layout_assign` generate inter-building context shading?

**No.** `openubem/idf/builder.py`, `build()`:

- Line 425: `context = discover_context(target_row_ctx, gdf, cx, cy, SHADING_SPHERE_RADIUS)` is
  computed unconditionally, **before** the strategy branch.
- The **only** place `context` is consumed is line 488, `extrude_geometry(self.idf, zones,
  context)` — part of the standard per-building geometry pipeline (§3D/§3E, comment at line
  483–488), reached only when execution falls through past the `strategy == "layout_assign"`
  block.
- The `layout_assign` success branch (lines 443–481) returns at line 481 — **before** line 483 —
  so `context` is computed and then discarded, unused, for every successful `layout_assign`
  building. The branch's own returned manifest row states this explicitly at line 476:
  `"num_context_buildings": 0`.
- `scale_baseline_idf()` does scale `SHADING:ZONE:DETAILED`/`SHADING:BUILDING:DETAILED` objects
  (`_GEOMETRY_SURFACE_CLASSES`, `layout_assigner.py:248-253`) — but those are whatever shading
  surfaces the **baseline prototype file itself** already carries (e.g. any self-shading
  overhangs baked into the DOE template), not surfaces derived from the real neighbourhood's
  actual neighbouring buildings.

**Reading against the plan's own D7 candidates (§B05, `PLAN_storey-matching_implementation.md`
lines 529–531):** `layout_assign` buildings are already simulated in complete isolation from their
real neighbours — there is no inter-building shading calculation for the overlap to corrupt. This
means option (c) — "documentation-only, declare `layout_assign` unusable for any inter-building
study (solar, shading, UTCI)" — already describes the mode's *current* EnergyPlus-simulation
behaviour regardless of whether B05 fixes the overlap: `layout_assign` never modelled neighbour
shading in the first place, overlap or not. What the overlap **does** break is anything reading
these IDFs'/the viewer's geometry as an urban-form/massing model in its own right (the viewer
itself, any future solar/view-factor/UTCI massing export) — those consumers see interpenetrating
buildings that do not correspond to any real site condition.

---

## Artifacts

- Overlap/anchor measurement scripts (throwaway, read-only):
  `scripts/analysis/measure_layout_assign_overlap.py`,
  `scripts/analysis/measure_offset_by_archetype.py`,
  `scripts/analysis/check_identical_shapes.py`,
  `scripts/analysis/measure_raw_baseline_footprint.py`.
- Superseded blank-viewer scripts (kept for the record, not part of this finding):
  `scripts/analysis/diagnose_blank_viewer.py`, `scripts/analysis/repro_legend_crash.mjs`,
  `scripts/analysis/headless_check_viewer.py`.
- Screenshot from the superseded investigation (kept only as a record that a real, separate JS
  crash bug exists and was reverted, not evidence for the overlap finding):
  `results/viewer_blank_diagnosis_nyc_BEFORE_FIX.png`.
- Real generated IDFs read directly (not modified):
  `scratchpad/t18_t01_t03_work/work/nyc_suburban/step3_layout_assign/idfs/way_1014146136.idf`,
  `scratchpad/e-la-20-fix/f01_work/idfs/f01_ts2_init_fat/idfs/way_772627076.idf`.
- Raw baseline IDFs read directly (not modified):
  `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`,
  `...\ASHRAE901_OfficeSmall_STD2022_Buffalo.idf`.
- No files under `openubem/viz/`, `openubem/geometry/layout_assigner.py`, `openubem/idf/builder.py`,
  or `tests/` were modified in the course of this diagnosis (the two viewer-JS files touched during
  the superseded blank-scene investigation were reverted — see top section).
