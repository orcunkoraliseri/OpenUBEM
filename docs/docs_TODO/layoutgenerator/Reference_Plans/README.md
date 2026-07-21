# Reference Plans — the 31 DOE baseline buildings, grouped by layout / function

> **What this folder is.** A reference-plan *library* for the LayoutGenerator design phase. It sorts the
> **31 DOE/ASHRAE baseline IDFs** in `C:\Users\o_iseri\Desktop\idf_reader\Content\00.Baseline_NUs_CAN_CLG`
> into **8 layout groups (G1–G8)**, one `.md` per group. Each group file lists its member buildings (exact
> IDF filenames), the zoning family behind it, whether the **corridor/room template applies**, the layout
> recipe + the 2–3 design alternatives to render, and the reference figure (existing or pending).
>
> **This is a VIEW, not a new source of truth.** The authoritative design is `../Design_layoutgenerator.md`
> (groups in §3.1, shape catalogue §4, family recipes §5, alternatives §7, IDF ground-truth §10). These
> files re-index that design against the real filenames so the user can review one group at a time. If a
> group file and the Design doc ever disagree, the Design doc wins. Manager-authored 2026-07-04.

---

## Current decisions (2026-07-04, revisable — we're in progress)

Full ledger in `../Design_layoutgenerator.md` §8. Headlines:
- ✅ SC reference plans **signed off**; figures now save into this `Reference_Plans/` folder.
- ⭐ **Tall towers** → represent with **multiple layouts per function floor** (retail / office / residential /
  hotel) as alternatives (G3) — updates the old "one uniform floor" idea.
- **SmallOffice** → its own core/perim box, not lumped with restaurants (G4).
- **Hospital** → **skipped** in layout generation (keep DOE, rectangular/square only, G6).
- **LargeHotel** → rectangular/square only (too complex, G2); hotel dims = committed values.
- **Houses** → follow DOE exactly = living + attic + basement, no bedroom split (verified, G8).
- **Functional split** (retail / supermarket / restaurant) → **build it**, preserving room function (G4/G5).

## The 8 groups at a glance

| Group | Layout family | Corridor/room template? | Members (n) | Locked step |
|---|---|---|---|---|
| **[G1 — Residential corridor](G1_residential_corridor.md)** | units+corridor | ✅ yes | 4 | **S1** ✅ done |
| **[G2 — Lodging corridor](G2_lodging_corridor.md)** | units+corridor (+podium) | ✅ yes | 2 | **S4** |
| **[G3 — Office & tower core-perimeter](G3_office_tower_core_perimeter.md)** | core+perimeter (+deep-plate) | ✅ yes | 4 | **S2** (towers) + **S3** (offices) |
| **[G4 — Small standalone](G4_small_standalone.md)** | single / functional-split | ❌ no corridor | 5 | S3 (SmallOffice) / S5 |
| **[G5 — Open-volume / big-box](G5_open_volume_bigbox.md)** | single / open-plan | ❌ no corridor | 7 | S5 |
| **[G6 — Institutional cellular](G6_institutional_cellular.md)** | classroom-wing / cellular-departmental | ✅ yes | 6 | S5 |
| **[G7 — Multi-tenant strip](G7_multitenant_strip.md)** | strip / tenant-slice | ❌ no shared corridor | 1 | S5 |
| **[G8 — Single-family](G8_single_family.md)** | single-family | ❌ no corridor | 2 | S5 |
| | | | **31** | |

**Corridor groups (template applies): G1, G2, G3, G6** — residential, lodging, office/tower, institutional.
**Non-corridor groups (opt out — single-zone / functional / tenant split): G4, G5, G7, G8.**
Alternatives are always drawn from the building's **own group**, never one-size-fits-all (Design §3.1).

---

## The two locked constraints (repeated on every group)

1. **Zero fitted parameters.** Every corridor width, room depth, bay pitch, perimeter offset, and area
   fraction traces to a named source (DOE prototype dim / ASHRAE 90.1 App-G 4.57 m / IBC / Neufert).
2. **Provenance mandatory + always degrade, never crash.** Every zone records family + shape path +
   fallback + confidence; any footprint the recipe cannot zone falls back to `one_zone_per_floor`
   (correctness > coverage). Area conservation `Σ zone areas = footprint × floors` holds on every path.

Plus **THE CORRIDOR LAW** for G1/G2/G3/G6 (Design §4): (1) all corridor runs connect into ONE network
(U-base bridged, O-ring closed); (2) every corridor run reaches the exterior facade (egress).

---

## Locked step order → which groups (Design §3, user 2026-07-03)

| Step | Archetype(s) | Group(s) | Status |
|---|---|---|---|
| **S1** | MidriseApartment + HighriseApartment | G1 | ✅ done (highrise = one `MODULE_SPECS` row) |
| **S2** ⭐ | TallBuilding + SuperTallBuilding | G3 (towers) | pending — uniform core+perim proxy |
| **S3** | Offices (Small / Medium / Large) | G3 (Med/Large) + G4 (SmallOffice) | pending — highest ΔEUI value |
| **S4** | Hotels (Small / Large) | G2 | pending — corridor law + podium split |
| **S5** | Hospital / Outpatient / schools / retail / houses | G6, G4, G5, G7, G8 | pending — hardest / lowest priority |

---

## Reference figures currently in this folder (SC-signed)

| Figure | Archetype | Group | Note |
|---|---|---|---|
| `layoutgenerator_doe_vs_generated.png` | MidriseApartment | G1 | THE CORRIDOR LAW reference plan (SC-audited PASS) |
| `layoutgrid_LargeHotel.png` | LargeHotel | G2 | GuestRoom relabel; honest PREVIEW footer |

Regenerated by `scripts/plot_layout_grid.py` into `../outputs/` + `openubem/outputs/LayoutGenerator/` and
mirrored here. Per-group alternative-panel figures (A/B/C) are rendered **one group at a time after each
sign-off**; each group file below names its pending figure.

---

## How to read a group file

Each `G*.md` has: **members** (IDF filename → OpenUBEM archetype → family → DOE zones → status) ·
**template verdict** · **kit-of-parts** (cited dims) · **recipe + shape behaviour** · **alternatives A/B/C
to render** · **reference figure** · **provenance** (Design section cites). Zone counts are the
employee-verified as-modeled values from Design §10 where available, else the zones/floor from Design §3.
