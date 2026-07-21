# G3 — Office & tower core-perimeter

> **Layout family:** core+perimeter, incl. deep-plate concentric · **Template applies:** ✅ **yes**
> (core+perimeter = the fat-spine cousin of the corridor template) · **Locked steps:** **S2** (towers ⭐) +
> **S3** (Medium/Large offices). Backing design: `../Design_layoutgenerator.md` §5.2 (Family B), §3.1 (G3),
> §10 (tower mixed-use finding). **Highest-value un-built family — offices rank highest ΔEUI (L14).**

## Members (4 IDFs)

| IDF filename | OpenUBEM archetype | Family | DOE zones (as-modeled) | Status |
|---|---|---|---|---|
| `ASHRAE901_OfficeMedium_STD2022_Buffalo_NECB17_Z7A_v221.idf` | MediumOffice | core+perimeter | **18** total · 5/floor × 3 | ⚠️ compact via geomeppy; non-rect degrades |
| `ASHRAE901_OfficeLarge_STD2022_Buffalo_NECB17_Z7A_v221.idf` | LargeOffice | core+perimeter (deep plate) | **23** total · 6/floor (4 perim + core + IT) | ⚠️ compact only; deep-plate not built |
| `TallBuilding_90.1-2019_6A_Buffalo_NECB17_Z7A_v221.idf` | TallBuilding | core+perimeter (uniform proxy) | **164** / ~38 flr | ❌ forced per-floor today |
| `SuperTallBuilding_90.1-2019_6A_Buffalo_NECB17_Z7A_v221.idf` | SuperTallBuilding | core+perimeter (uniform proxy) | **256** / ~72 flr | ❌ forced per-floor today |

**Why grouped together:** all four are **core + 4-perimeter plates**. Towers are just this plate **stacked**
via the representative-floor + Multiplier technique — real towers are prismatic (constant footprint per
floor), so generation needs real geometry for **one typical floor** only. This is why S2 towers are "easy"
and sequenced before S3 offices. **SmallOffice is NOT here** — it lives in G4 per the user's scale hint
("offices together except SmallOffice").

## ⭐ Tall / SuperTall — MULTI-LAYOUT per function floor (user 2026-07-04)

The DOE Tall (164 zones) and SuperTall (256 zones) IDFs are **mixed-use vertical stacks**
(retail podium → office → residential → hotel → mech penthouse), **not** uniform office towers.

**DECISION (user 2026-07-04, revisable):** represent towers with **multiple layouts, one per function
floor** — a retail-podium layout, an office-floor layout, a residential-floor layout, a hotel-floor layout —
rendered as the tower's **alternative panels**. This *updates* the earlier "one uniform floor stacked"
simplification: we now show the different function floors.

⚠️ **Open sub-question for the S2 build:** OSM gives one archetype tag + no per-floor program, so *which
floors get which function* must come from a **documented, zero-fitted assumption** (natural source = the
DOE tower stack proportions). We do **not** silently invent per-floor program — flag + decide this at S2.
`mixed_use_vertical_stack` is the 7th family this opens up.

## Kit-of-parts (zero-fitted)

- **Perimeter depth = 4.57 m** (ASHRAE 90.1-2019 App-G G3.1.1.1) — the *only* dimension the core family
  needs. **Core = the residual** after the perimeter buffer (no fabricated service-core geometry; L09 §3).
- **Deep-plate band rule (L10 §2)** keyed on minor-axis width W:
  - W ≤ 9.14 m → **centerline split**, perimeter-only, no core.
  - 9.14 < W ≤ 18.28 m → **standard core + 4 perimeter**.
  - W > 18.28 m → **concentric multi-band**: outer perimeter ring + intermediate band + deep core.

## Recipe + shape behaviour (a buffer/decompose engine — NOT the corridor packer)

| Shape | behaviour |
|---|---|
| Compact | 5 zones (4 perim + core) — **must equal geomeppy `add_block(zoning="core/perim")` exactly** (no-regression identity, L09 §2) |
| Slab / narrow | centerline split, perimeter-only (core collapsed) |
| L / U / T / cross | decompose into rectangular wings → per-wing core/perim; wing junctions adiabatic |
| O / courtyard | inner + outer 4.57 m perimeter ring, core between (merge if < 2 m); courtyard = Outdoors |
| Very deep plate | concentric multi-band (outer perim / mid / deep core) |
| Ribbon / irregular | single-loaded or degrade |

## Alternatives to render (A = DOE default)

- **A** central core + 4 perimeter — production default.
- **B** side / end core (against one facade).
- **C** concentric multi-band (deep) · centerline-split (narrow).

## Reference figure

Pending (S2 towers first, then S3 offices). No G3 figure signed yet.

## Status caveat

This is the **largest un-built family and the highest-value one**. Today only compact convex offices zone
(via geomeppy `add_block`); non-rect offices, deep plates, tall buildings (forced per-floor), and outpatient
all degrade. Building it = generalizing App-G core/perim to wings + courtyards + deep plates. **No new
packing module needed.**

## Provenance

Design §3.1 (G3), §5.2 (Family B recipe + dims + band rule), §10 (tower mixed-use finding + verified zone
counts), open decision #3 (adopt the deep-plate band rule).
