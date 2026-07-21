# G1 — Residential corridor

> **Layout family:** units+corridor · **Template applies:** ✅ **yes** (double-loaded corridor) ·
> **Locked step:** S1 ✅ **done** (production room-level, DOE-reproduced, live-validated).
> Backing design: `../Design_layoutgenerator.md` §5.1 (Family A), groups §3.1 (G1), corridor law §4.

## Members (4 IDFs)

| IDF filename | OpenUBEM archetype | Family | DOE zones (as-modeled) | Status |
|---|---|---|---|---|
| `ASHRAE901_ApartmentMidRise_STD2022_Buffalo_NECB17_Z7A_v221.idf` | MidriseApartment | units+corridor | **27** total · 9/floor (8 apt + 1 corr) | ✅ production room-level |
| `ASHRAE901_ApartmentHighRise_STD2022_Buffalo_NECB17_Z7A_v221.idf` | HighriseApartment | units+corridor | **27** total · 9/floor | ✅ enabled (identical module) |
| `ASHRAE_HighRise_ST15_Geometric_NECB17_Z7A_v221.idf` | HighriseApartment (15-storey variant) | units+corridor | 27 (rep-floor × mult) | ✅ same module |
| `ASHRAE_HighRise_ST20_Geometric_NECB17_Z7A_v221.idf` | HighriseApartment (20-storey variant) | units+corridor | 27 (rep-floor × mult) | ✅ same module |

**Why grouped together:** all four are the **identical per-floor module** — a central hallway spine with
repeated dwelling-unit modules packed on both sides. Highrise differs from midrise **only in floor count**
(the ST15/ST20 are storey-count variants). One apartment design covers all four; enabling highrise took a
single `MODULE_SPECS` row and zero new geometry — the proof of the one-template thesis.

## Kit-of-parts (zero-fitted)

| corridor width | room depth | bay pitch | room area | circ % | source |
|---|---|---|---|---|---|
| 1.68 m (5.5 ft) | 7.62 m (25 ft) | 11.58 m (38 ft) | 88.25 m² | 9.9% | Deru 2011 §3.1.15 / PNNL-23269 §3.2.1 |

Apartments have **no dimension conflict** — 100% consistent across L06/L07/L08.

## Recipe + shape behaviour (Approach A — corridor-first, per-wing rooms)

Rotate footprint to dominant-edge frame → decompose into wings → build each wing centerline → **connect
into one network** with orthogonal bridges at junctions → `corridor = network.buffer(w/2) ∩ footprint` →
per wing `room = wing − corridor`, subdivide along the wing's long axis into `round(len/bay)` cells.

| Shape | behaviour |
|---|---|
| Compact / slab | single straight double-loaded bar (corridor + N/S rows), short ends open to facade |
| L | corridor bends at the elbow |
| U | two arms + base; corridor **bridged through the base** = 1 connected piece |
| T / cross | stem/arms meet at a corridor junction |
| O / courtyard | corridor ring around void; inner rooms face courtyard (Outdoors); **1 closed ring** |
| Ribbon | too narrow → single-loaded, or single-zone below one room depth |
| Irregular | degrade to per-floor |

## Alternatives to render (A = DOE default)

- **A** double-loaded corridor (rooms both sides) — production default.
- **B** single-loaded / gallery access (rooms one side).
- **C** point-access stair-core cluster (no long corridor).

Production auto-selects by footprint geometry (narrow→single-loaded, wide→double-loaded); the panels are
exploratory only (Design §7).

## Reference figure

`layoutgenerator_doe_vs_generated.png` (MidriseApartment) — **SC-audited PASS**, in this folder + `../outputs/`.
Pending: apartment A/B/C alternative panel (first per-group alternatives figure per the plan).

## Provenance

Design §3.1 (G1), §5.1 (Family A recipe + dims), §4 (corridor law), §10 (verified zone counts, rep-floor+
Multiplier technique). Zero-fitted dims cited to Deru 2011 / PNNL-23269.
