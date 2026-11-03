# Deep-Research Prompt L07 — DOE/PNNL PROTOTYPE INTERIOR PROGRAMS (the templates layoutGenerator replicates)

> SCOPE GUARD — READ FIRST. This prompt documents **what the DOE/PNNL reference buildings actually
> contain inside** — the space-type mix, room/unit modules and dimensions, circulation fraction, and zone
> multipliers of the prototype models OpenUBEM already draws its loads/schedules from. `layoutGenerator.py`
> re-lays-out *these exact programs* onto real footprints, so we must know them precisely. Deliver a
> per-prototype interior breakdown. Do NOT design the corridor method (that's `L06`) and do NOT judge
> which archetypes get room-level layout (that's `L14`). See `00_README_layoutgenerator_prompt_set.md`
> for shared facts.

---

## What this document is

The template reference. OpenUBEM's Phase-E baseline takes per-space loads/schedules/setpoints verbatim
from the DOE prototypes; `layoutGenerator.py`'s job is to distribute those same per-space intensities onto
the zones it generates. To do that it must know each prototype's *internal* structure: how many thermal
zones the reference model has per floor, what space types they are, the geometric module (unit/room
dimensions), the perimeter depth used, and any zone multipliers. This prompt extracts that from the
prototype documentation so the generated layout matches the *thermal program* the loads assume.

## Role

DOE/PNNL prototype-building documentation analyst. Ground every value in the primary source: the **DOE
Commercial Prototype Building Models** (PNNL, per 90.1 vintage) and their EnergyPlus IDF/documentation,
the **DOE Residential Prototype Buildings**, the **Commercial Reference Buildings** (Deru et al. 2011,
NREL/TP-5500-46861), and the OpenStudio/PNNL space-type libraries. Report the *as-modeled* interior:
zone list per floor, space-type assignment, floor dimensions, perimeter depth, and multipliers. Where the
prototype documentation is silent (e.g. exact unit dimensions in MidriseApartment), say GAP and cite the
closest source.

## Why this matters (so you scope correctly)

`layoutGenerator.py` must produce a layout whose zones can each be assigned a DOE space type so the
building's total loads are conserved. If the DOE MidriseApartment prototype is modeled as
"apartment + corridor" zones per floor with a known unit count and corridor fraction, the generator should
reproduce that structure on the real footprint. If the DOE LargeOffice is core + 4 perimeter + plenum with
specific space types, the generator's core/perimeter output must map to those. This prompt is the bridge
between the geometry (`L05`/`L06`) and the loads (`L11`).

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Per-prototype interior zoning (as modeled by DOE/PNNL)

| DOE prototype | Thermal zones per floor (as modeled) | Space types present | Perimeter depth used | Zone multipliers used? | Source |
|---|---|---|---|---|---|
| MidriseApartment |  |  |  |  |  |
| HighriseApartment (if modeled) |  |  |  |  |  |
| SmallHotel |  |  |  |  |  |
| LargeHotel |  |  |  |  |  |
| SmallOffice |  |  |  |  |  |
| MediumOffice |  |  |  |  |  |
| LargeOffice |  |  |  |  |  |
| PrimarySchool |  |  |  |  |  |
| SecondarySchool |  |  |  |  |  |
| Hospital |  |  |  |  |  |
| Outpatient |  |  |  |  |  |
| RetailStandalone |  |  |  |  |  |
| RetailStripmall |  |  |  |  |  |
| Warehouse |  |  |  |  |  |

### Table 2 — Geometric modules & dimensions (what the generator packs)

| Prototype | Floor plate dimensions (as modeled) | Unit / room module size | Circulation (corridor) fraction of floor | Floor-to-floor height | Source |
|---|---|---|---|---|---|
| MidriseApartment |  | dwelling unit: ? m² |  |  |  |
| SmallHotel |  | guest room: ? m² |  |  |  |
| LargeHotel |  | guest room: ? m² |  |  |  |
| PrimarySchool |  | classroom: ? m² |  |  |  |
| LargeOffice |  | (open plan) |  |  |  |
| Hospital |  | patient room / dept |  |  |  |

### Table 3 — Space-type → load intensity map (for conservation, feeds L11)

| Prototype | Space type | LPD / EPD / occupancy / OA (as-modeled, cite) | Share of floor area | Source |
|---|---|---|---|---|
| MidriseApartment | Apartment |  |  |  |
| MidriseApartment | Corridor |  |  |  |
| SmallHotel | GuestRoom |  |  |  |
| SmallHotel | Corridor / Lobby / BOH |  |  |  |
| LargeOffice | OpenOffice / Conference / Corridor / etc. |  |  |  |

### Table 4 — Mapping DOE zones onto generated geometry

| Prototype | Which generated zone gets which space type | Corridor→? Core→? Perimeter→? | Reconciles with App-G core/perimeter? | Source |
|---|---|---|---|---|
| MidriseApartment | corridor spine → Corridor; packed units → Apartment |  |  |  |
| SmallHotel |  |  |  |  |
| LargeOffice |  |  |  |  |
| PrimarySchool |  |  |  |  |

---

## Part C — Synthesis (the template library)

Give: (1) a **per-prototype "interior template"** the generator can encode — for each archetype, the zone
structure, module dimensions, circulation fraction, and space-type-to-zone map, every value cited or
flagged GAP; (2) an explicit list of **which prototypes are naturally corridor+units** (residential/hotel/
school/dorm — use `L06`) vs. **core+perimeter** (office/retail — use App-G) vs. **department/deep-plan**
(hospital/large hotel — see `L10`); (3) the prototypes whose interior structure is **least documented**
(likely MidriseApartment unit dimensions, Hospital department layout) and the closest defensible source;
(4) confirmation that reproducing these templates lets `L11` conserve the DOE loads exactly.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C template library.
3. Cite the specific prototype IDF / PNNL doc / Deru et al. section for every value.
4. **"Confidence and caveats":** which prototype's interior geometry is least documented.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Report as-modeled DOE values, cited** — no generic space-planning numbers where a prototype value
  exists.
- **Give the space-type-to-generated-zone map** for at least MidriseApartment, SmallHotel, LargeOffice,
  PrimarySchool — these anchor `L08`/`L09`/`L11`.
- **Flag every undocumented dimension as GAP** + closest source (zero-fitted-parameters discipline).
- **No fabricated precision;** flag GAPs. **Stay on topic** — DOE prototype *interior content* only, not
  the packing method (`L06`) or accuracy (`L14`).
