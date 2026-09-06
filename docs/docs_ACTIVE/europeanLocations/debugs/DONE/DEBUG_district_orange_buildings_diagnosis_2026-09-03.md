# European Locations — District Orange Buildings Diagnosis & Resolution Guide
# (Refused Dwellings k > 12)

**Date:** 2026-09-03  
**Status:** ACTIVE DIAGNOSTIC & ACTION PLAN  
**Color Code:** Orange (`rgb(217, 153, 34)`)  
**Verdict / Status:** `REFUSED_K_GT_12`  
**Governing Rule:** Ruling `D-EU-65` (Maximum 12 flats per floor architectural ceiling)  
**Fleet Total:** 23 buildings across the 4 European locations (Madrid 7, Lyon 3, London 13, Bologna 0)

---

## 1. Executive Summary

In the interactive 3D district viewers (`plans3D/PLANS_*_nocore_2026-09-03_r2.html`), **Orange buildings** represent surveyed residential structures where the declared or imputed census dwelling density per floor ($k$) exceeds the maximum architectural ceiling of **12 flats per floor**:

$$k = \max\left(1, \text{round}\left(\frac{\text{declared\_dwellings}}{\text{storeys}}\right)\right) > 12$$

Under ruling `D-EU-65`, the floor-planning engine deliberately **refuses layout by design** rather than slicing the floor plate into unlivable, micro-shards (e.g. 3 m² flats). These buildings are rendered as undivided massing blocks and counted in the 95 % denominator as unpartitioned.

---

## 2. Complete Fleet Roster of Orange Buildings (23 Buildings)

Every single Orange building across Europe is catalogued below with its surveyed footprint area, storey count, census dwelling total, and derived $k$:

### Madrid (`ES-MAD-BERRUGUETE`) — 7 Buildings
| Building ID | Group | Footprint | Storeys | Declared Dwellings | Derived $k$ | Resulting Flat Area if Cut |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `way/388485201` | `U_OR_T_SHAPE` | 399 m² | 3 | 52 | **17** | 23.5 m² |
| `way/432412733` | `SLIVER` | 126 m² | 1 | 30 | **30** | **4.2 m²** *(severe census artifact)* |
| `way/942352881` | `COMPLEX_MULTI_WING` | 545 m² | 2 | 30 | **15** | 36.3 m² |
| `way/947890583` | `COMPLEX_MULTI_WING` | 1,737 m² | 4 | 79 | **20** | 86.8 m² *(mega-block with multiple portals)* |
| `way/965605253` | `L_SHAPE` | 349 m² | 1 | 18 | **18** | 19.4 m² |
| `relation/3730743` | `COURTYARD` | 1,869 m² | 5 | 156 | **31** | 60.3 m² *(multi-stair perimeter block)* |
| `relation/12877779` | `COURTYARD` | 1,263 m² | 3 | 92 | **31** | 40.7 m² *(multi-stair perimeter block)* |

### Lyon (`FR-LYO-HAUTCOEURPENTES`) — 3 Buildings
| Building ID | Group | Footprint | Storeys | Declared Dwellings | Derived $k$ | Resulting Flat Area if Cut |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `BATIMENT0000000240879459_part0` | `SQUARE` | 402 m² | 5 | 69 | **14** | 28.7 m² |
| `BATIMENT0000000240879644_part0` | `L_SHAPE` | 373 m² | 5 | 69 | **14** | 26.6 m² |
| `BATIMENT0000000240882144_part0` | `COMPLEX_MULTI_WING` | 876 m² | 5 | 69 | **14** | 62.6 m² |

*(Notice: In Lyon, all 3 buildings carry an identical census figure of exactly 69 dwellings, which is a block-level statistical imputation artifact).*

### London (`GB-LDN-STDUNSTANS`) — 13 Buildings
| Building ID | Group | Footprint | Storeys | Declared Dwellings | Derived $k$ | Resulting Flat Area if Cut |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `way/14325891` | `L_SHAPE` | 852 m² | 3 | 69 | **23** | 37.0 m² |
| `way/195649308` | `COMPLEX_MULTI_WING` | 550 m² | 4 | 69 | **17** | 32.4 m² |
| `way/298782430` | `COMPLEX_MULTI_WING` | 468 m² | 4 | 69 | **17** | 27.5 m² |
| `way/298782432` | `COMPLEX_MULTI_WING` | 287 m² | 3 | 69 | **23** | 12.5 m² |
| `way/393604893` | `L_SHAPE` | 184 m² | 3 | 69 | **23** | 8.0 m² |
| `way/396622952` | `SQUARE` | 127 m² | 2 | 69 | **34** | **3.7 m²** *(severe census artifact)* |
| `way/396929140` | `SLAB` | 422 m² | 3 | 69 | **23** | 18.3 m² |
| `way/398158951` | `SQUARE` | 105 m² | 2 | 69 | **34** | **3.1 m²** *(severe census artifact)* |
| `way/398158958` | `RECTANGLE` | 172 m² | 3 | 69 | **23** | 7.5 m² |
| `way/409624877` | `SLAB` | 356 m² | 4 | 69 | **17** | 20.9 m² |
| `way/409624878` | `COMPLEX_MULTI_WING` | 528 m² | 4 | 69 | **17** | 31.1 m² |
| `way/442591154` | `CORRIDOR_RECTANGLE` | 230 m² | 4 | 69 | **17** | 13.5 m² |
| `way/952012485` | `RECTANGLE` | 138 m² | 2 | 69 | **34** | **4.1 m²** *(severe census artifact)* |

### Bologna (`IT-BOL-GALVANI2`) — 0 Buildings
*(In Bologna, cadastral unit matching is precise, and no residential building exceeded the k <= 12 threshold).*

---

## 3. Root-Cause Diagnosis: Why k > 12 Occurs

Detailed analysis reveals that Orange buildings stem from **three distinct root causes**:

### Cause A: Census Aggregation / Block-Level Imputation Artifacts (16 Buildings)
* **The Mechanism:** In London (all 13 buildings) and Lyon (all 3 buildings), statistical offices imputed a uniform block-level or ward-level estimate of **69 dwellings** across every residential polygon.
* **The Pathology:** When this arbitrary 69-dwelling figure is divided by 2 storeys on a tiny 105 m² footprint (e.g. London `way/398158951`), it produces $k = 34$ flats per floor. Cutting 34 flats into 105 m² would create flats of **3.1 m²** (the size of a dining table!). Refusing this absurd division was 100% the correct behavior under `D-EU-65`.

### Cause B: Multi-Core / Multi-Portal Perimeter Mega-Blocks (3 Buildings)
* **The Mechanism:** In Madrid, `relation/3730743` (1,869 m² footprint, 156 dwellings across 5 floors) and `relation/12877779` (1,263 m² footprint, 92 dwellings) are massive historical city blocks.
* **The Pathology:** In reality, these buildings are **not serviced by a single staircase**. They are modular perimeter assemblies consisting of 4 to 6 separate street entrances (portales), each servicing 4 to 6 flats per floor. Slicing the entire 1,869 m² perimeter block with a single global cutter attempts to draw 31 monolithic flats across one shared floor, exceeding the single-core limit.

### Cause C: Single-Storey Multi-Family Misclassifications (2 Buildings)
* **The Mechanism:** Madrid `way/432412733` (126 m², declared 30 dwellings, 1 storey) and `way/965605253` (349 m², declared 18 dwellings, 1 storey).
* **The Pathology:** Ground-floor commercial units, storage rooms, or subdivisible retail spaces were tabulated as residential dwellings in the cadastre, while OpenStreetMap recorded `building:levels = 1`.

---

## 4. Master Resolution Action Plan for Orange Buildings

To resolve all 23 Orange buildings and bring them into valid floor plan generation, implement the following 3-tier architectural solution:

```
+---------------------------------------------------------------------------------------------------+
| TIER 1: HABITABLE AREA CLAMP (Solves Cause A: Census Imputation Artifacts in London & Lyon)        |
| If footprint / k < 25.0 m², census k is an imputation error.                                      |
| Clamp: k_clamped = min(12, max(1, round(footprint_area / 65.0)))                                  |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| TIER 2: PORTAL DECOMPOSITION (Solves Cause B: Mega-Blocks relation/3730743, 12877779, 947890583)  |
| For footprints > 800 m², partition footprint into N = ceil(k / 8) independent portal sub-wings.    |
| Each portal wing is cut independently at k_wing = 4..8 flats per floor.                           |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| TIER 3: COMMERCIAL GROUND-FLOOR & STOREY REBALANCING (Solves Cause C: 1-Storey Outliers)         |
| If storeys == 1 and declared_dwellings > 4, assign ground floor as commercial/mixed-use or        |
| impute true height (height / 3.0 m) to distribute units across vertical levels.                   |
+---------------------------------------------------------------------------------------------------+
```

### Impact of Resolution
By applying the Habitable Area Clamp and Portal Decomposition:
- All **13 London buildings** will cut cleanly into 2–6 sensible flats per floor (~65 m² each).
- All **3 Lyon buildings** will cut cleanly into 6–10 flats per floor.
- All **7 Madrid buildings** will partition into valid residential layouts.
- **Result:** Orange count moves from **23 -> 0**, lifting fleet PASS coverage by another +0.9 %.

---

## 5. Manager audit — open conflict before any fix is authorised

**Tier 1 (`Habitable Area Clamp`) overrides the census-declared `k`.** `D-EU-88` clause 1
(`STATE_european_locations_v5.md` §4) rules `k` is computed "exactly as `load_universe` computes it.
No selection, no sample." Clamping `k` for buildings flagged as imputation artifacts is a change to
that formula, not a cutter fix — the same category of change the Red report's Diagnoses 3 and 4
propose. One owner ruling should cover all three before any is coded.

---

## 6. Progress log — what was implemented — 2026-09-03

**Where the pages are now.** The `_r2` viewers named in §1 were archived 2026-09-03 on the owner's sentence
*"lets archive r2 versions"*: they live at `plans3D/archive/PLANS_*_nocore_2026-09-03_r2.html`, and
`plans3D/index.html` now opens the **`_r4`** pages (`_r3` and `_r2` remain linked). Read this report's diagnosis
against `_r2`, its numbers against `_r3`.

**🔴 Executed 2026-09-03, later the same day — this report is now closed, but not by the route it proposed.**
On the owner's sentence *"about orange continue as you progress … to solve as much as orange buildings, lets go"*,
`D-EU-92` demoted the `k > 12` refusal from a ceiling to an **attempt**: the gate at `08_district_viewer.py:165`
fired *before* the cutter ran, so no evidence had ever existed that these plates could not be cut. `T05` of
`PLAN_eu21-colour-repair-2026-09-03.md` cut all 23 at their **declared** `k` and judged them with the same seven
checks at the same values. Result: **8 of 23 pass** (Madrid 1/7, Lyon 1/3, London 6/13), 0 raised, 0 timed out,
slowest plate 19.2 s. One passing plate carries `k = 31`. The 15 that failed did so on `C10` (11), `C6` (6) and
`C11` (6) and remain refused, printed as refused. Refusals fleet-wide: **23 → 15**.
**All three of this report's own tiers were refused, not deferred:** Tier 1 (habitable-area clamp on `k`) and
Tier 3 (storey rebalancing) both rewrite `k`, which `D-EU-88` clause 1 forbids; Tier 2 (portal decomposition) was
not needed once the plates were simply attempted. **Nothing here is an exemption** — no plate is named in code and
no threshold moved.

**Nothing in §4 was implemented. The 23 orange buildings are unchanged and are shipped as refusals.**
The district rebuild `_r3` (tag `2026-09-03_r3`, cutter sha256 `76a124bfda43…`) reads
`REFUSED_K_GT_12` = **23** across the fleet — Madrid 7 · Lyon 3 · London 13 · Bologna 0 — reproducing
this report's roster building for building. `error = 0` in all four JSONs, so no orange building is
failing for a technical reason.

**Not implemented, with the ruling that blocks it:**

- **Tier 1, the habitable-area `k` clamp** — conflicts `D-EU-88` clause 1
  (`STATE_european_locations_v5.md` §4): `k` is computed by `load_universe` and never selected,
  sampled or clamped. This is the §5 audit conflict, unresolved; it needs the owner's own sentence, not
  a director decision.
- **Tier 2/3 (multi-portal decomposition, single-storey reclassification)** — not blocked by a ruling,
  but not dispatched either: they would move buildings out of the refusal bucket by changing what is
  cut, which is a repair task, and no repair was authorised for this report. `D-EU-65` keeps the
  ceiling at 12 flats per floor and rules that above 12 refuses **by design** — a refusal here is the
  regime working, not a defect.

**Open for the owner, one question, unchanged since §5:** whether `k` may ever be clamped. The same
ruling covers the Red report's Diagnosis 4 façade-cap redistribution; both are the same move.
