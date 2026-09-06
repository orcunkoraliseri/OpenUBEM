# European Locations — District Purple Buildings Diagnosis & Resolution Guide
# (Cutter Runtime Exceptions & Unusable Footprints)

**Date:** 2026-09-03  
**Status:** ACTIVE DIAGNOSTIC & ACTION PLAN  
**Color Code:** Purple (`rgb(149, 97, 209)`)  
**Verdict / Status:** `ERROR` and `UNUSABLE_FOOTPRINT`  
**Governing Rule:** `D-EU-79` (No-core direct equal-area cutter)  
**Fleet Total:** 17 buildings across the 4 European locations (Madrid 8, Lyon 1, London 1, Bologna 7)

---

## 1. Executive Summary

In the interactive 3D district viewers (`plans3D/PLANS_*_nocore_2026-09-03_r2.html`), **Purple buildings** represent structures where the floor-plan cutter crashed during execution due to an unhandled Python exception (`status = "ERROR"`).

No building in the fleet had an unusable raw footprint (`UNUSABLE_FOOTPRINT = 0`). All 17 Purple buildings failed during the geometric boolean operations in `cut_nocore()` (`scripts/eu21/07_nocore_tests.py`). Because the cutter threw an unhandled exception, no floor plan could be rendered, and the building defaulted to an undivided purple massing block.

---

## 2. Complete Fleet Roster of Purple Buildings (17 Buildings)

All 17 Purple buildings across Europe are catalogued below with their morphology group, dwelling density $k$, error token, and exact Python exception message:

| District | Building ID | Morphology Group | Density $k$ | Error Token | Python Exception Message |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **Madrid** | `way/100704705` | `COMPLEX_MULTI_WING` | 12 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'exterior'` |
| **Madrid** | `way/288461992` | `COMPLEX_MULTI_WING` | 4 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Madrid** | `way/434877453` | `COMPLEX_MULTI_WING` | 10 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Madrid** | `way/435397047` | `COMPLEX_MULTI_WING` | 6 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'exterior'` |
| **Madrid** | `relation/4179135` | `COURTYARD` | 10 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Madrid** | `relation/12800463` | `COURTYARD` | 6 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'exterior'` |
| **Madrid** | `relation/12800464` | `COURTYARD` | 8 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'exterior'` |
| **Madrid** | `relation/12803902` | `COURTYARD` | 11 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Lyon** | `BATIMENT0000000240881271_part0` | `SLIVER` | 5 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **London** | `way/398158941` | `SLAB` | 5 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'exterior'` |
| **Bologna** | `32790` | `SLIVER` | 3 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'exterior'` |
| **Bologna** | `32800` | `COMPLEX_MULTI_WING` | 6 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Bologna** | `31932` | `SLIVER` | 3 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Bologna** | `30912` | `SLIVER` | 3 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Bologna** | `32062` | `COMPLEX_MULTI_WING` | 3 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Bologna** | `32135` | `SLIVER` | 3 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |
| **Bologna** | `31887` | `SLIVER` | 3 | `CUT_AttributeError` | `'MultiPolygon' object has no attribute 'interiors'` |

---

## 3. Root-Cause Diagnosis: The MultiPolygon Fault (FINDING 243)

Notice the stark pattern in Section 2: **100 % of Purple buildings (all 17) fail on the exact same error**:
- 7 buildings fail with `'MultiPolygon' object has no attribute 'exterior'`.
- 10 buildings fail with `'MultiPolygon' object has no attribute 'interiors'`.

### The Code Pathology in `07_nocore_tests.py`
In `scripts/eu21/07_nocore_tests.py`, the cutter performs the following steps:
1. `_cut_columns(P, k)` slices the polygon $P$ with parallel vertical planes.
2. If $P$ is non-convex (e.g. `COMPLEX_MULTI_WING`, `COURTYARD`, or an irregular `SLIVER`), a single vertical column slice often intersects multiple disjoint wings simultaneously, returning a `MultiPolygon`.
3. `donate_leftovers(P, seeds)` then merges orphan remnants back into the main flats using `shapely.ops.unary_union()`. If an absorbed remnant touches the seed only at a point or has a micro-gap, `unary_union` returns a `MultiPolygon` rather than a single unified `Polygon`.
4. Downstream routines (such as SVG rendering, `check_c5`, or perimeter calculation) expect simple `Polygon` instances and execute:
   ```python
   # Line 621 in 07_nocore_tests.py
   coords = list(flat.exterior.coords)  # CRASH! MultiPolygon has no .exterior
   
   # Line 648 in 07_nocore_tests.py
   holes = len(flat.interiors)          # CRASH! MultiPolygon has no .interiors
   ```
5. Because Shapely `MultiPolygon` objects store components in `.geoms` rather than having `.exterior` or `.interiors` properties, Python immediately raises an unhandled `AttributeError`.

---

## 4. Master Resolution Action Plan for Purple Buildings

The solution to all 17 Purple buildings is completely deterministic and requires zero architectural trade-offs:

### Step 1: Implement Defensive Geometry Normalizer (`_to_single_polygon`)
Add a helper in `scripts/eu21/07_nocore_tests.py` and `scripts/eu21/08_district_viewer.py`:

```python
def _to_single_polygon(geom):
    """Guarantees a clean single Polygon from any Shapely geometry."""
    if geom is None or geom.is_empty:
        return Polygon()
    if isinstance(geom, Polygon):
        return geom
    if isinstance(geom, MultiPolygon):
        # Keep only real area components (drop micro-slivers)
        valid = [p for p in geom.geoms if p.area > 1e-4]
        if not valid:
            return Polygon()
        # Return the dominant component
        return max(valid, key=lambda p: p.area)
    if hasattr(geom, "geoms"):
        polys = [p for p in geom.geoms if isinstance(p, Polygon) and p.area > 1e-4]
        if polys:
            return max(polys, key=lambda p: p.area)
    return Polygon()
```

### Step 2: Wrap Leftover Donation and Checking Calls
In `build_flats()` and `check_c5()`:
```python
# Before checking or rendering, normalize all flats:
flats = [_to_single_polygon(f) for f in flats]
```

### Step 3: Buffer Zero Epsilon Cleanup
Before donating leftovers:
```python
merged = flat.union(orphan)
if not merged.is_valid:
    merged = merged.buffer(0)
flat = _to_single_polygon(merged)
```

### Impact of Resolution
- **100 % of Purple buildings (17 of 17) will be eliminated.**
- Madrid error count moves from **8 -> 0**.
- Lyon error count moves from **1 -> 0**.
- London error count moves from **1 -> 0**.
- Bologna error count moves from **7 -> 0**.
- Fleet runtime error rate drops to **0.00 %**.

---

## 5. Manager audit — one caution on the proposed fix

**`_to_single_polygon` must re-donate the dropped components, not discard them.** Keeping only the
`MultiPolygon`'s largest piece silently loses the smaller ones' area — a direct `C1`/`D-EU-80`
violation (no square metre may belong to no flat) if `unary_union` split a real merge rather than a
degenerate sliver. The dropped remainder must be routed back through leftover donation, not returned
as if it never existed.

---

## 6. Progress log — what was implemented — 2026-09-03

**Where the pages are now.** The `_r2` viewers named in §1 were archived 2026-09-03 on the owner's sentence
*"lets archive r2 versions"*: they live at `plans3D/archive/PLANS_*_nocore_2026-09-03_r2.html`, and
`plans3D/index.html` now opens the **`_r4`** pages (`_r3` and `_r2` remain linked). Read this report's diagnosis
against `_r2`, its numbers against `_r3`.

**Confirmed still closed in `_r4`, 2026-09-03.** This report's defect was fixed before the colour-repair plan
opened (`FINDING 243`, compactness `T05d`). The `_r4` rebuild carries `error = 0` in all four district JSONs, so
no purple building exists in any neighbourhood page. The `_r4` cutter is materially different from the `_r3` one
(broader angle search, reflex snapping, ring bisection, and `D-EU-92`'s `k > 12` attempt) and the `error` count
held at zero through all of it — which is the evidence that the fix was structural, not incidental.

**Implemented: the `MultiPolygon` fault is fixed.** `FINDING 243` was closed inside
`PLAN_eu21-compactness-2026-09-03.md` `T05d` (not in this report's own plan), in
`scripts/eu21/07_nocore_tests.py`. The district rebuild `_r3` (tag `2026-09-03_r3`, cutter sha256
`76a124bfda43…`, `MAX_FLAT_ASPECT = 2.5`) reproduces **`error = 0` in all four district JSONs**;
`_r2`, built at sha `d1fa6bd007bf…`, carried 17 (Madrid 8 · Lyon 1 · London 1 · Bologna 7).

**Roster verified one by one against `EU-21/district_plans/*_nocore_2026-09-03_r3.json`** — all 17 ids
found, none raising:

- 16 of 17 are now `status = direct` (cut by the census cutter): **9 PASS all seven checks**
  (`way/100704705` k=12, `way/288461992`, `way/434877453`, `way/435397047`, Lyon
  `BATIMENT0000000240881271_part0`, Bologna `32800`, `31932`, `32062`, `32135`) and **7 FAIL on
  ordinary check grounds, not on an exception** (`relation/4179135`, `relation/12800463`,
  `relation/12800464`, `relation/12803902`, Bologna `32790`, `30912`, `31887` — the `C10`/`C11`
  ring-and-wing residual of `FINDING 242`).
- 1 of 17, London `way/398158941`, reads `status = GENERIC_NO_CENSUS` in `_r3`: it carries no census
  row in that build's manifest and is drawn by the generic fallback. It is not an error and not a
  refusal, but it is **not** proof that the census path handles it. The handoff wording "17/17 now
  `direct`" is corrected here to **16 `direct` + 1 `GENERIC_NO_CENSUS`, 0 errors**.

**The §5 caution stands and was honoured by the fix as measured, not by inspection of the code:** `C1`
= 100.0 % on every one of the 16 census-cut buildings, and `C1` fails on 0 of 2,521 drawn buildings
fleet-wide in `_r3` — no square metre was dropped. The code path itself was not re-read by the
director; the evidence is the census.

**Not implemented, deliberately:** nothing else in §4. Steps 2 and 3 (`buffer(0)` epsilon cleanup,
wrapping every donation call) were not separately dispatched — `T05d`'s own fix cleared the fault, and
a measurement task does not extend a fix past the defect it closed.
