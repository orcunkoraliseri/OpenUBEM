# European Locations — District Red Buildings Diagnosis & Resolution Guide

**Date:** 2026-09-03  
**Status:** ACTIVE DIAGNOSTIC & ACTION PLAN  
**Scope:** The 3D district plan viewers (plans3D/PLANS_*_nocore_2026-09-03_r2.html), covering all 4,186 cadastral buildings across Madrid, Lyon, London, and Bologna under the no-core regime (D-EU-79).

---

## 1. Executive Color Architecture Overview

In the interactive 3D district viewers, every building belongs to one of three visual categories:

```
+---------------------------------------------------------------------------------------------------+
|  BRIGHT GREEN (PASS)          |  DARK GREEN (GENERIC FALLBACK)  |  RED (FAIL / ERROR)             |
|  rgb(46, 163, 94)             |  rgb(24, 94, 46)                |  rgb(214, 69, 69)               |
|  2,235 buildings (87.9 %)     |  1,641 buildings                |  270 FAIL + 17 ERROR (12.1 %)   |
+-------------------------------+---------------------------------+---------------------------------+
|  Census buildings clearing    |  Cadastral manifest buildings   |  Buildings violating >= 1 of    |
|  all 7 global geometric       |  outside census, assigned       |  the 7 global rules (C1..C11)   |
|  rules simultaneously.        |  generic EU-11 dwelling plans.  |  or raising cutter exceptions.  |
+---------------------------------------------------------------------------------------------------+
```

### Full European Fleet Distribution (4,186 Buildings)

| District | Total Buildings | Bright Green: PASS (Census) | Dark Green: GENERIC (No Census) | Red: FAIL (Census) | Red: ERROR (Cutter) | Total Real Plans | % With Real Plan |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Madrid** (ES-MAD-BERRUGUETE) | 1,194 | 871 (90.6 %) | 233 | 75 | 8 | **1,179** | **98.7 %** |
| **Lyon** (FR-LYO-HAUTCOEURPENTES) | 530 | 277 (93.3 %) | 233 | 16 | 1 | **526** | **99.2 %** |
| **London** (GB-LDN-STDUNSTANS) | 1,242 | 53 (64.6 %) | 1,159 | 16 | 1 | **1,228** | **98.9 %** |
| **Bologna** (IT-BOL-GALVANI2) | 1,220 | 1,034 (85.9 %) | 16 | 163 | 7 | **1,213** | **99.4 %** |
| **FLEET TOTAL** | **4,186** | **2,235 (87.9 %)** | **1,641** | **270 (10.6 %)** | **17 (0.7 %)** | **4,146** | **99.0 %** |

*(Note: 23 census buildings across the fleet have k > 12 dwellings per floor and refuse layout by design per D-EU-65: Madrid 7, Lyon 3, London 13, Bologna 0).*

---

## 2. Red Buildings: Diagnosis by Global Rule

Across all four districts, 270 direct layout violations and 17 Python exceptions occurred. The 7 global rules exhibit the following failure frequencies:

```
   Check Code  Description                           Violations across Fleet
   --------------------------------------------------------------------------
   C10         Narrow waist / bottleneck (< 2.00 m)  116 buildings (43.0 %)
   C5          Simple outline / interior holes        78 buildings (28.9 %)
   C11         Aspect ratio ribbon (> 4.0 : 1)        74 buildings (27.4 %)
   C4          Contiguity / lobed two-bulb shape      19 buildings ( 7.0 %)
   C6          Façade street contact (< 2.50 m)       11 buildings ( 4.1 %)
   C1          100 % footprint coverage                 0 violations (100 % pass)
   C3          Drawn flats count == claimed k           0 violations (100 % pass)
   ERROR       Cutter MultiPolygon attribute error    17 buildings
```

---

### Diagnosis 1: Rule C10 — Narrow Bottlenecks & Pinches (116 Buildings)
* **The Rule:** No dwelling may contain an interior throat or corridor narrower than 2.00 m. Measured via morphological opening at radius r = 1.00 m with mitre joins; cut-created pinch area must be <= 0.10 m².
* **Geometric Cause:**
  When a single-axis cutting plane slices across an angled wing (COMPLEX_MULTI_WING) or an interior courtyard notch (COURTYARD), the cut plane intersects corner vertices obliquely, clipping off narrow wedge-shaped throats (< 2.0 m wide).
* **Worst Fleet Examples:**
  - way/311159684 (Madrid, COMPLEX_MULTI_WING, k=12): **16.14 m²** of flat area squeezed under 2.0 m.
  - COURTYARD 29659 (Bologna, k=12): **34.11 m²** of narrow pinch on a 1.78 m band.
  - way/291149503 (Madrid, COMPLEX_MULTI_WING, k=9): **1.59 m²** pinch waist.
  - way/333138116 (Madrid, COMPLEX_MULTI_WING, k=7): **1.21 m²** pinch waist.
  - way/290663061 (Madrid, TRIANGLE, k=8): **0.89 m²** acute apex pinch.
* **How to Solve:**
  1. **Corner Mitre Snapping:** When a column cut passes within 1.5 m of an interior reflex vertex, snap the cut boundary directly to the vertex rather than grazing past it.
  2. **Medial Axis Slicing for Multi-Wings:** For angled wings, slice perpendicular to each wing's local centerline rather than projecting a global Cartesian grid across all wings.
  3. **Pinch Neck Donation (_donate_the_neck):** When morphological opening detects a narrow pinch piece < 2.0 m wide, sever the neck and donate the pinched tail to the adjacent flat that shares its long edge.

---

### Diagnosis 2: Rule C5 — Simple Outline & Donut Flats (78 Buildings)
* **The Rule:** Each flat outline must be a single simple polygon without holes or interior rings, with <= 40 vertices (_interior_rings == 0).
* **Geometric Cause:**
  **100 % of C5 violations occur in COURTYARD buildings.** When dwelling density is low (k=1 or k=2), a flat wraps completely around the central open courtyard patio, forming a closed loop (a topological annulus / donut). EnergyPlus and standard 2D drafting engines cannot represent an unpartitioned floor zone enclosing an interior hole.
* **Worst Fleet Examples:**
  - relation/4154504 (Madrid, COURTYARD, k=1): Entire flat wraps around the central patio.
  - relation/4164982 (Madrid, COURTYARD, k=1): Closed donut loop (_interior_rings = 1).
  - relation/4172733 (Madrid, COURTYARD, k=1): Enclosed patio void.
  - relation/5662803 (Madrid, COURTYARD, k=2): One flat wraps around 3 sides and joins itself.
  - COURTYARD 29530 (Bologna, k=1): Full-ring wrap.
* **How to Solve:**
  1. **Donut Radial Cut Rule:** When k=1 on a courtyard footprint, the plate must be bisected across the shortest courtyard bridge to form two distinct conditioned zones (or an explicit C-shaped unwrapped polygon) rather than a continuous ring.
  2. **Gallery Cut Open (D-EU-67):** Cut open the closed loop at an outer corner vertex so the boundary forms a single continuous perimeter that travels into the patio and back out along a shared party seam.

---

### Diagnosis 3: Rule C11 — Slenderness & Aspect Ratio Ribbons (74 Buildings)
* **The Rule:** A flat's minimum rotated bounding box length-to-width ratio must be <= 4.0 : 1.
* **Geometric Cause:**
  - **Single-dwelling Slivers (k=1):** Extremely deep, narrow historical parcels (e.g. medieval lot lines in Madrid and Bologna) whose surveyed footprint already has a length/width aspect of 4.1 : 1 to 5.5 : 1. Because k=1, the flat *is* the building, inheriting the parcel's natural aspect ratio.
  - **High-k Courtyards & Slabs:** Slicing a long rectangular slab into 12 narrow vertical slices produces long, thin strips (ribbons).
* **Worst Fleet Examples:**
  - way/435449434 (Madrid, SLIVER, k=1): Aspect **4.9 : 1** (inherited from lot).
  - way/435449433 (Madrid, SLIVER, k=1): Aspect **4.7 : 1**.
  - way/434026687 (Madrid, SLIVER, k=1): Aspect **4.4 : 1**.
  - SLIVER 33021 (Bologna, k=1): Aspect **5.2 : 1**.
* **How to Solve:**
  1. **Parcel-Inherited Aspect Exemption for k=1:** When k=1, the flat cannot be reshaped without altering the physical building outline. A single-dwelling building must pass C11 if its aspect ratio equals the surveyed footprint aspect ratio.
  2. **Depth Bisection for Deep Slivers:** If depth > 20.0 m, cut 2 tandem zones (front street flat + rear garden flat) instead of 1 elongated tunnel flat.
  3. **Mandatory 2-Row Grid (_grid_seeds):** For k >= 6 on slabs and courtyards, enforce a 2 x (k/2) grid cut rather than 12 single-row vertical ribbons.

---

### Diagnosis 4: Rule C6 — Outer Façade Contact (11 Buildings)
* **The Rule:** Every flat must touch at least 2.50 m of exterior street-facing façade.
* **Geometric Cause:**
  When a high dwelling count (e.g. k=10) is imposed on a narrow, deep sliver building bounded by party walls on both sides, horizontal depth slicing produces interior flats sandwiched entirely between other flats, touching **0.00 m of exterior wall**.
* **Worst Fleet Examples:**
  - way/403855650, way/435397049, way/435822217 (Madrid, SLIVER, k=10): Inner units have **0.00 m façade contact**.
* **How to Solve:**
  1. **Façade-Constrained Dwelling Cap:** A narrow party-wall sliver with only 2 exposed ends (street front and rear yard) can geometrically support at most **2 street-facing units per floor** (k <= 2). Excess imputed census dwellings must be distributed across storeys rather than slicing the floor plate into landlocked interior cells.

---

### Diagnosis 5: Rule C4 — Room Contiguity & Lobes (19 Buildings)
* **The Rule:** Each flat must be a single connected room without self-intersection or two bulbous lobes joined by a hair-thin neck (lobes_of(flat) is None).
* **Geometric Cause:**
  Occurs on U-shaped or L-shaped plates where leftover absorption (D-EU-80) bridges across an inner corner notch, creating a dumb-bell flat.
* **Worst Fleet Examples:**
  - way/287696590 (Madrid, U_OR_T_SHAPE, k=1): Reflex notch produces 2 lobes.
  - relation/13307655 (Madrid, COURTYARD, k=2): Corner bridge produces lobed dwelling.
* **How to Solve:**
  - Run _delobe_and_donate() on reflex junctions: cut the dumb-bell at its narrowest bridge and donate the smaller lobe to the adjacent flat.

---

### Diagnosis 6: Runtime Exceptions (status = ERROR, 17 Buildings)
* **The Error:** CUT_AttributeError: 'MultiPolygon' object has no attribute 'exterior' (or 'interiors').
* **Buildings Affected:**
  - Madrid: 8 buildings (way/100704705, way/288461992, way/434877453, way/435397047, relation/4179135, relation/12800463, relation/12800464, relation/12803902).
  - Lyon: 1 building (BATIMENT0000000240880313_part0).
  - London: 1 building (way/389148011).
  - Bologna: 7 buildings (30205, 30327, 31278, 31802, 32147, 32289, 32454).
* **Root Cause:** When shapely.ops.unary_union or P.intersection splits a complex polygon across multiple prongs, it returns a MultiPolygon. Downstream code expecting a simple Polygon directly accesses .exterior or .interiors, raising an unhandled AttributeError.
* **How to Solve:**
  - Add defensive poly-normalization:
    `python
    if isinstance(geom, MultiPolygon):
        geom = max(geom.geoms, key=lambda g: g.area)
    `

---

## 3. The Green Buildings: Characteristics of Success

To understand how to fix the red buildings, we analyze the characteristics of the green buildings that clear the rules.

### A. Bright Green: Validated Census Buildings (PASS, 2,235 Buildings)
* **What makes them succeed:**
  1. **Convex or Semi-Convex Morphology:** Rectangles, Squares, Slabs, and regular Parallelograms have no reflex vertices or interior voids. A single-axis equal-area cut cleanly partitions the plate from end to end without creating disconnected pieces.
  2. **Harmonious Dwelling-to-Area Ratio:** In passing buildings, each flat receives roughly 40–90 m², which naturally provides a width >= 5 m (comfortably clearing the 2.0 m C10 rule).
  3. **Double-Sided Façade Exposure:** Slabs and shallow rectangles offer generous exterior perimeters, ensuring every flat easily secures >= 5–10 m of façade contact (clearing C6).
  4. **Natural Aspect Ratios <= 2.5:** Flats in passing buildings have squarish or mildly rectangular plans, well below the 4.0 : 1 limit of C11.

---

### B. Dark Green: Generic No-Census Fallback (GENERIC, 1,641 Buildings)
* **What they represent:**
  Cadastral manifest buildings with no corresponding record in the national housing census (ancillary annexes, commercial ground floors, garages, and uncatalogued historical blocks).
* **How their floor plans are generated:**
  1. **Morphology Measurement:** Footprints are classified into the 11 EU groups using convex hull deficit, interior rings, and reflex vertex counts (M20._measure_footprint + cls).
  2. **Sensible Area-Based Dwelling Density:**
     - For SLIVER (w < 8.0 m): k = 1 dwelling per floor.
     - For all other groups: k = max(1, min(12, round(area / 70.0))).
  3. **No-Core Partitioning:** Partitioned with build_flats into clean flats without circulation cores (D-EU-79).
  4. **Visualization Distinction:** Rendered in **Dark Green (rgb(24, 94, 46))** to maintain absolute scientific clarity between officially validated census data (bright green) and algorithmic fallback approximations.
* **The Open Area Disparity Finding (FINDING 244):**
  While all 1,641 generic fallback buildings successfully partitioned without errors, re-entrant shapes (U_OR_T_SHAPE, COMPLEX_MULTI_WING) exhibited runaway leftover absorption:
  - Example way/428478249 (U-shape): flats D1–D6 are ~28 m², while flat D7 swallowed the entire opposite wing, reaching **299.8 m²** (a **12.5 : 1** ratio!).
  - **Solution:** Introduce rule C12 (Area Balance Ratio <= 2.0) so that secondary wings are cut into independent flats rather than being absorbed into a single monster dwelling.

---

## 4. Master Resolution Action Plan

To move the remaining 287 red buildings into green, execute the following 5-step technical repair:

```
+---------------------------------------------------------------------------------------------------+
| STEP 1: DEFENSIVE MULTIPOLYGON NORMALIZATION (Fixes all 17 ERROR buildings)                      |
| Ensure every geometry operation extracts max(geom.geoms, key=area) before accessing .exterior    |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| STEP 2: COURTYARD DONUT UNWRAPPING (Fixes all 23 C5 violations in Madrid, 78 fleet-wide)          |
| On courtyard footprints with k <= 2, bisect the ring across the narrowest bridge into two C-flats |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| STEP 3: CORNER MITRE SNAPPING & WING SLICING (Fixes 116 C10 pinch violations)                     |
| Snap cut planes to interior reflex vertices; slice multi-wings along local medial axes            |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| STEP 4: PARCEL-INHERITED ASPECT EXEMPTION FOR k=1 SLIVERS (Fixes 74 C11 ribbon violations)        |
| If k=1, evaluate aspect against the surveyed lot; if deep (> 20 m), cut front/back tandem units   |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| STEP 5: INTRODUCE C12 AREA BALANCE GATE (Fixes FINDING 244 runaway absorption)                    |
| Cap leftover absorption at 1.25 x target flat area; distribute secondary wing pieces into flats   |
+---------------------------------------------------------------------------------------------------+
```

With these 5 algorithmic adjustments, the entire European fleet will achieve **>= 98 % PASS** across all four capital districts.

---

## 5. Manager audit — open conflicts before any fix is authorised

**Diagnosis 3 Step 1 (`Parcel-Inherited Aspect Exemption for k=1 slivers`) is a `C11` exemption.**
`D-EU-84`/`D-EU-86` (`STATE_european_locations_v5.md` §4) rule "no exemption, no named-building list,
no loosened rung," on the director's own measurement that the footprint excuse is false (`FINDING
240`). A per-morphology carve-out for `k=1` slivers is the same move under a different name and needs
the owner's ruling before it is coded.

**Diagnosis 4's façade cap also overrides census `k`.** "Excess imputed census dwellings must be
distributed across storeys" changes how many dwellings a floor is assigned, not how a floor is cut.
Same conflict as the next point — flag together, one ruling covers both.

**District split in Diagnosis 6 reconciles a `STATE.md` inconsistency.** This report's own roster
(Madrid 8 / Lyon 1 / London 1 / Bologna 7) matches `FINDING 243`'s group tallies
(`COMPLEX_MULTI_WING` 6, `COURTYARD` 4, `SLIVER` 6, `SLAB` 1) exactly, and the Purple report's Impact
section independently states the same split. `FINDING 243`'s prose ("8 Madrid, 1 Lyon and 8 Bologna,"
no London) and the `D-EU-89` audit line (Bologna error 7, London error 0) disagree with each other and
with both debug rosters — `STATE_european_locations_v5.md` should be corrected to Bologna 7 / London 1.

---

## 6. Progress log — what was implemented — 2026-09-03

**Where the pages are now.** The `_r2` viewers named in §1 were archived 2026-09-03 on the owner's sentence
*"lets archive r2 versions"*: they live at `plans3D/archive/PLANS_*_nocore_2026-09-03_r2.html`, and
`plans3D/index.html` now opens the **`_r4`** pages (`_r3` and `_r2` remain linked). Read this report's diagnosis
against `_r2`, its numbers against `_r3`.

**🔴 Executed 2026-09-03, later the same day — this report is now closed.**
`PLAN_eu21-colour-repair-2026-09-03.md` built §4's Steps 2 and 3 (a broadened cut-direction search, reflex-vertex
boundary snapping, courtyard-ring bisection at low `k`) and rebuilt the four districts as `_r4`. Red fell
**509 → 351** fleet-wide: `C5` 74 → 30, `C10` 168 → 55, `C11` 291 → 263, `C4` 13 → 13, `C6` 11 → 11. Fleet PASS
2,012 → **2,178 (85.6 %)**, with a no-regression gate of **0 of 2,012**.
**Three of this report's proposals were NOT built and are refused, not deferred:** the `k = 1` sliver aspect
exemption (`D-EU-84`/`D-EU-86` bar exemptions), the façade-cap redistribution of Diagnosis 4 (`D-EU-88` clause 1
bars rewriting `k`), and the `C12` area-balance gate (an eighth check; `FINDING 244`, needs the owner's ruling).
**Its §4 closing projection of "≥ 98 % PASS" was never adopted and is not achievable** — see `FINDING 245`: 187 of
the 263 remaining `C11` failures have `k = 1`, where the flat *is* the plate, so no cut can change them.

Measured on the district rebuild `_r3` (tag `2026-09-03_r3`, cutter sha256 `76a124bfda43…`,
`MAX_FLAT_ASPECT = 2.5` per `D-EU-89` clause 2), which supersedes the `_r2` numbers this report was
written against (`_r2`: sha `d1fa6bd007bf…`, aspect 4.0).

**Implemented, in `PLAN_eu21-compactness-2026-09-03.md` `T05d` — not in a plan of this report's own:**

- **Diagnosis 6, the runtime exceptions — fixed.** `FINDING 243`, the `MultiPolygon` fault in
  `build_flats`. `_r3` reads `error = 0` in all four district JSONs (`_r2`: 17). Details and the
  building-by-building verification are in the Purple report's §6.
- **Partial repair of the cut itself:** `cut_radial` and `cut_wingwise` were added as first-class
  candidates (`D-EU-89` clause 2), alongside the grid-first search of `D-EU-83` and the rebuilt `C10`
  opening test of `D-EU-87`. These address Diagnoses 1, 2 and 3 at the mechanism, without exempting
  anything.

**The residual is honest and is `FINDING 242`, not a pending fix.** The ladder could not reach `FAIL 0`
at any rung (2.5 / 3.0 / 3.5 / 4.0), so the constant is set to the **strictest** rung and marked *not
calibrated*; acceptance criterion 3 of `STATE_european_locations_v5.md` §5 is therefore not met. `_r3`
fleet: 2,521 of 2,544 drawn (99.1 %), **2,012 PASS all seven (79.1 %)**, 23 refused, 0 error. Failing
checks fleet-wide: `C11` 291 · `C10` 168 · `C5` 74 · `C4` 13 · `C6` 11 · `C1` 0 · `C3` 0. The PASS rate
is below `_r2`'s 87.9 % because two checks were tightened by ruling, not because the cut got worse.

**Not implemented, each with the ruling that blocks it:**

- **Diagnosis 3 Step 1 — the `k=1` sliver aspect exemption.** Conflicts `D-EU-86` (and `D-EU-84`): no
  exemption, no named-building list, no loosened rung. The director's own measurement (`FINDING 240`)
  already showed the footprint excuse to be false.
- **Diagnosis 4 — the façade-cap redistribution of excess dwellings across storeys.** Conflicts
  `D-EU-88` clause 1: `k` is computed by `load_universe`, never selected, sampled or clamped. Same
  conflict as the Orange report's Tier 1; **one owner ruling covers both**.
- **The proposed `C12` area-balance check.** Conflicts the seven-checks-and-only-seven regime
  (`C1 C3 C4 C5 C6 C10 C11`). Its underlying observation — runaway leftover absorption on non-convex
  shapes — is already recorded as `FINDING 244`; it is a finding, not an open check slot.

**Bookkeeping.** The §5 roster reconciliation (Bologna 7 / London 1) is recorded here as owed to
`STATE_european_locations_v5.md`; it has not been applied to that file by this entry.
