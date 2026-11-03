# Simulation Resolution — Thermal Zoning by Building

**What this answers:** for every building type, *is it simulated floor-by-floor, as a single
zone, or core+perimeter per floor?* One EnergyPlus model is built per building in all cases —
this doc is only about how many **thermal zones** go inside that one model.

Source of truth: `openubem/geometry/zoning.py` (`decide_zoning_strategy`, `build_zones`).
Verified against code 2026-06-29.

---

## 1. One rule, three inputs

Zoning is **not** fixed per building type. It is decided per building from three inputs —
`archetype_id`, `footprint_area_m2`, and `num_floors`:

```
if num_floors == 1:                                    → single_zone
elif footprint_area_m2 >= 500 and archetype is commercial:  → perimeter_core
else:                                                  → one_zone_per_floor
```

"Commercial" above means *not* in the forced-per-floor set and *not* unknown (see §3).

| Strategy | Zones built | Geometry |
|---|---|---|
| **`single_zone`** | 1 zone for the whole building | footprint extruded to full height (`num_floors × 3.5 m`) |
| **`one_zone_per_floor`** | **1 zone per floor** | footprint stacked N times (3.5 m each) |
| **`perimeter_core`** | **core + 4 perimeter zones, per floor** | geomeppy native core/perim, 4.57 m perimeter depth |

---

## 1b. The four resolution modes (proposed user switch)

Today the mode is fixed to **AUTO** (the adaptive rule above). The proposal is to expose a
user-selectable `resolution_mode` so the same building can be simulated at different fidelity
depending on the study. AUTO becomes the validated default; the other three force one strategy
on **every** building.

| Mode | Zoning applied to every building | Zones/building | Fidelity | Use case |
|---|---|---|---|---|
| **`building`** | 1 zone for the whole building (full height) | 1 | lowest | early-design screening |
| **`floor`** | 1 zone per floor, all archetypes | `num_floors` | medium | mid-fidelity studies |
| **`zone` (B1)** | core + perimeter per floor, **all** archetypes regardless of area | ~5 × `num_floors` | highest | detailed studies |
| **`auto`** *(current default)* | adaptive — picks per building (see §1 rule) | mixed | validated baseline | the 8,160-building benchmark |

**B1 = "real footprint, DOE-style slicing":** core/perimeter zones are cut from the building's
*actual* OSM polygon by an inward buffer (~4.57 m), preserving true shape + neighbour shading —
not a resized DOE rectangle. The `zone` mode just extends the core/perimeter logic that AUTO
already applies to large commercial (§1) to **all** archetypes, including MidriseApartment and
SmallOffice, at any footprint area.

> Tiers `building` and `floor` reuse strategies the code already has (`single_zone`,
> `one_zone_per_floor`). Only `zone` requires extending B1 beyond large commercial.

### Current finished fleet (8,152 buildings, 12-cell validation matrix) under AUTO

| Strategy chosen by AUTO | Buildings | Share |
|---|---|---|
| `one_zone_per_floor` (floor-level) | 3,919 | 48.1% |
| `single_zone` (building-level) | 3,763 | 46.2% |
| `perimeter_core` (zone-level B1) | 470 | 5.8% |

So today **~94% of the fleet is at building- or floor-level**, and only ~6% (large multi-floor
commercial) is already at zone-level B1.

**Approximate total zone count across the whole fleet if you force one mode** (drives EnergyPlus
runtime/cost):

| Forced mode | ~Total zones in fleet | Relative cost |
|---|---|---|
| `building` | ~8,200 | 1× (cheapest) |
| `floor` | ~19,700 | ~2.4× |
| `zone` (B1) | ~98,000* | ~12× (most expensive) |

\* Upper-bound estimate (assumes ~5 zones/floor everywhere). Real `zone` totals are lower —
narrow and courtyard footprints fall back to one-zone-per-floor (§4), and very small footprints
can't form a valid core.

---

## 2. Quick answer by floor count

| Building | num_floors | Result |
|---|---|---|
| Any 1-floor building (house, standalone retail, warehouse, big-box) | 1 | **single_zone** (1 zone) |
| 10-floor apartment | 10 | **one_zone_per_floor** → 10 zones |
| 10-floor large office (≥500 m² footprint) | 10 | **perimeter_core** → ~50 zones (5 × 10) |
| 3-floor small shop (<500 m² footprint) | 3 | **one_zone_per_floor** → 3 zones |

**Floor area (EUI denominator) is always `footprint_area_m2 × num_floors`**, regardless of
zoning strategy.

---

## 3. Per-archetype behaviour (when the building is multi-floor)

For 1-floor buildings every archetype is `single_zone`. The table below shows what happens
when the same archetype has **2+ floors**.

| Archetype | Multi-floor zoning | Why |
|---|---|---|
| **MidriseApartment** | **one_zone_per_floor** (always) | forced per-floor set |
| **HighriseApartment** | **one_zone_per_floor** (always) | forced per-floor set |
| **TallBuilding** | **one_zone_per_floor** (always) | forced per-floor set |
| **SuperTallBuilding** | **one_zone_per_floor** (always) | forced per-floor set |
| **OpenUBEMUnknown** | **one_zone_per_floor** (always) | unclassified — never core/perim |
| SmallOffice / SmallOfficeDetailed | perimeter_core if footprint ≥500 m², else one_zone_per_floor | area-gated commercial |
| MediumOffice / MediumOfficeDetailed | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| LargeOffice / LargeOfficeDetailed | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| RetailStandalone | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| RetailStripmall | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| SuperMarket | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| FullServiceRestaurant | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| QuickServiceRestaurant | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| SmallHotel | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| LargeHotel | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| Hospital | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| Outpatient | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| PrimarySchool | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| SecondarySchool | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| College | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| Courthouse | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| Laboratory | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| Warehouse | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| SmallDataCenterHighITE / LowITE | perimeter_core if ≥500 m², else per-floor | area-gated commercial |
| LargeDataCenterHighITE / LowITE | perimeter_core if ≥500 m², else per-floor | area-gated commercial |

> Note: residential archetypes (`MidriseApartment`, `HighriseApartment`) and the tall-building
> archetypes are **never** core/perimeter even when large — apartments are modelled per floor by
> design. Only multi-floor commercial ≥500 m² gets core+perimeter.

---

## 4. Two graceful fallbacks (perimeter_core → one_zone_per_floor)

A building that *qualifies* for `perimeter_core` still drops back to `one_zone_per_floor` when
the core can't be formed cleanly (`zoning.py:63`, `zoning.py:73`):

| Trigger | Reason |
|---|---|
| **Narrow footprint** — core buffer empties or core area < 10 m² | a 4.57 m inward buffer collapses → no valid core |
| **Courtyard footprint** — footprint has an interior ring (hole) | donut core produces mismatched inter-floor vertices → EnergyPlus fatal |

So a thin or O-shaped large office is simulated per floor, not core/perim.

---

## 5. Summary

- **Always one IDF / one EnergyPlus run per building.** Floors are never separate models.
- **Single-zone** ⇔ genuinely 1-floor buildings only.
- **One zone per floor** ⇔ all multi-floor residential/tall, all unclassified, all small (<500 m²)
  commercial, plus any large commercial that fails the core test.
- **Core + perimeter per floor** ⇔ multi-floor commercial with footprint ≥ 500 m².
- **Temporal resolution is identical for every building:** annual, 8760 hourly timesteps.

---

*Derived from `openubem/geometry/zoning.py`. Matches `OpenUBEM_fundamentals.md` §5.1. 2026-06-29.*
