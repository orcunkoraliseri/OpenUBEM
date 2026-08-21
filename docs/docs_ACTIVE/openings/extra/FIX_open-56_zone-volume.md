# FIX — OPEN-56: write `Zone.Volume` explicitly

**Date:** 2026-08-21 (night)
**Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md`, T02
**Ruling spent:** R2 ("Both, plan then execute") — remedy shape (b) only; (a) (extending
`orient()` to `auto` mode) is explicitly not authorised.

## Root cause, confirmed by reading

`openubem/idf/builder.py:464-465`:

```python
if self.resolution_mode != "auto":
    poly_local = orient(poly_local, sign=1.0)
```

`orient` here (imported `openubem/idf/builder.py:13`, `from shapely.geometry.polygon import
orient`) is the real, correctly-functioning shapely winding-normaliser — not the broken
geomeppy corrector described elsewhere for this item. It is simply **gated off for the
adopted `auto` mode**, so `poly_local` keeps whatever winding the OSM footprint arrived
with, and EnergyPlus's own "Indicated Zone Volume" calculation goes negative on it,
substituting the 10 m³ stub (§5 fact 1 of the plan).

**Why CORE zones (0.00% stubbed) differ from WHOLE zones (100.00% stubbed) — the question
T02 required answering before any edit:**

- CORE/PERIM zones are built by geomeppy's `core/perim` zoning
  (`geomeppy/idf.py:268-286`, dispatched from `openubem/idf/surfaces.py`'s
  `_expand_core_perim_placeholder`). The core polygon is derived by
  `core_perim.py:get_core()` → `Polygon2D(footprint).buffer(distance=-perim_depth)`
  (`geomeppy/geom/core_perim.py:7-10`). `Polygon2D.buffer()`
  (`geomeppy/geom/polygons.py:104-113`) internally calls
  `orient(s_poly.buffer(...), sign=1.0)` — **the same real shapely `orient`, but invoked
  unconditionally**, independent of `resolution_mode`. This is "the writer" that §5 fact 2
  says "works whenever it fires" — it fires for CORE regardless of mode, which is why CORE
  is 0.00% stubbed. PERIM zones sit at 95.75% (not 0%, not 100%) because
  `get_perims()` (`core_perim.py:13-26`) builds each perimeter wedge from two points on the
  correctly-oriented core plus two points taken straight from the original, unoriented
  footprint edges — a partial fix.
- WHOLE zones (`one_zone_per_floor`/`single_zone` strategies) are built by geomeppy's
  `by_storey` zoning (`geomeppy/idf.py:263-267`), which extrudes `block.coordinates`
  directly — the raw `poly_local`, with no orientation correction of any kind in `auto`
  mode. Hence 100.00% stubbed.

This matches §5 fact 2's prediction exactly. No STOP condition was triggered.

## Fix applied (remedy shape (b))

Winding is left untouched — no change to `orient()`, no `geomeppy` upgrade. Instead,
`openubem/idf/builder.py` now writes each zone's `Volume` field explicitly, ending
EnergyPlus's need to compute (and mis-compute) it at all.

New helper `_write_zone_volumes(idf, zones)` (`openubem/idf/builder.py`, added before
`class BuildingIDF`):

- Builds a `Zone.Name -> Zone EpBunch` map and a `Zone.Name -> summed FLOOR-surface area`
  map from the **already-extruded, real** IDF geometry (`idf.getsurfaces("floor")`), not
  from the zones-list dict's `floor_polygon` — that field is unreliable for CORE/PERIM
  zones, whose dicts all share the *whole-building* placeholder footprint
  (`openubem/idf/surfaces.py:355,374`), not their own sub-polygon.
- For every zone with `extruded=True`, sets `Volume = floor_area x height_m`, where
  `height_m` is the zone's own floor-to-floor height (already correct for every zone role:
  `openubem/geometry/zoning.py` and the `_expand_core_perim_placeholder` fallbacks all set
  it consistently).
- Skips (leaves untouched) any zone with no floor surface found or non-positive
  area/height — defensive, not expected to trigger on any currently-succeeding build.

Call site: `BuildingIDF.build()`, immediately after the `extruded_zones` guard and before
`self.assign_constructions()` (`openubem/idf/builder.py`), i.e. after all geometry repair
passes (interzone-mismatch reroute, roof/roof repair, adiabatic surfaces) are final.

## Test

`tests/test_idf_builder.py::TestZoneVolumeWritten` (new):

- `test_one_zone_per_floor_whole_zones_get_correct_volume` — 10x10 m, 3-floor
  `MediumOffice` (`footprint_area_m2=100 < 500` -> `one_zone_per_floor`, the
  previously-100%-stubbed WHOLE-zone path). Asserts every `ZONE.Volume` is positive and
  within 1% of `floor_area x FLOOR_TO_FLOOR_M`, floor area independently recomputed from
  `idf.getsurfaces("floor")`.
- `test_core_perim_zones_still_get_correct_volume` — 30x30 m, 3-floor `MediumOffice`
  (`footprint_area_m2=900 >= 500` -> `perimeter_core`, CORE/PERIM zones). Same assertion —
  confirms the fix does not regress the path that already mostly worked.

Both pass. Full suite: `pytest -q tests/` — see plan §8 progress-log entry for the run
result (baseline 1,918 passed / 56 skipped).

## Before / after (one building)

10x10 m footprint, 3 floors, `MediumOffice`, `auto` mode, `osm_id=way/9001`:

| | `way/9001_F0_whole` | `way/9001_F1_whole` | `way/9001_F2_whole` |
|---|---|---|---|
| Before (IDF field, EnergyPlus autocalculates -> negative -> 10 m³ stub at simulation time) | `autocalculate` | `autocalculate` | `autocalculate` |
| After | `350.0` | `350.0` | `350.0` |

`350.0 = 100 m² (floor_area) x 3.5 m (FLOOR_TO_FLOOR_M)` — exact, not just within 1%,
because the synthetic test footprint has no context shading to trim the floor surface.

## Scope / not done

- No fleet re-run. `153.8231` over 8,153 is untouched, per plan §3 and hard rule §2.8.
- `layout_assign` strategy (baseline-IDF path) is untouched — it returns from `build()`
  before `extrude_geometry`/`extruded_zones` exist, uses its own baseline geometry, and is
  OPEN-60's territory, not OPEN-56's.
- Winding (`orient()` gate at `builder.py:464-465`) is unchanged, as authorised.
