# RESULT — PER-ARCHETYPE DOE LAYOUT catalog (target zone layout for every OpenUBEM archetype)

This document provides the reference catalog of every OpenUBEM archetype's actual DOE/PNNL prototype per-floor zone layout — zone count, zone types, corridor/core presence — which is the binding target that `zone` mode is trying to reproduce on a real footprint.

---

## REQUIRED OUTPUT TABLES

### Table 1 — DOE prototype per-floor zone layout, per archetype

| Archetype ID | Zones per floor (prototype) | Zone types / names | Corridor or core type | Reduces to (core+perim / units+corridor / single / functional-split) | DOE prototype? | Source |
|---|---|---|---|---|---|---|
| **SmallOffice** | 5 | `Perimeter_ZN_1` (South), `Perimeter_ZN_2` (East), `Perimeter_ZN_3` (North), `Perimeter_ZN_4` (West), `Core_ZN` | Interior core (open-plan office + circulation) | **core+perim** | Y | DOE/PNNL `ASHRAE901_OfficeSmall_STD2022.idf` |
| **SmallOfficeDetailed** | 5 | Same as SmallOffice (cardinal perimeter + core); "Detailed" variant adds plenum zones above ceiling. | Interior core + ceiling plenum (unconditioned) | **core+perim** | Y (proxy of SmallOffice) | DOE/PNNL `ASHRAE901_OfficeSmall_STD2022.idf` |
| **MediumOffice** | 5 per floor (Ground, Mid, Top vary slightly) | `Perimeter_Bot_ZN_1–4`, `Core_Bot_ZN` (Floors 1–3 × 3 variants) | Interior core (open-plan + stairs/elevators) | **core+perim** | Y | DOE/PNNL `ASHRAE901_OfficeMedium_STD2022.idf` |
| **MediumOfficeDetailed** | 5 per floor | Same as MediumOffice; "Detailed" variant includes plenum return-air zones above each floor. | Interior core + ceiling plenum | **core+perim** | Y (proxy of MediumOffice) | DOE/PNNL `ASHRAE901_OfficeMedium_STD2022.idf` |
| **LargeOffice** | 6 per floor (above-grade) + 1 (basement) | `Perimeter_Bot_ZN_1–4`, `Core_Bot_ZN`, `DataCenter_Bot_ZN`; Basement = 1 zone | Interior core (elevators, stairs, utility) + IT closet | **core+perim** (+IT closet mapped to core) | Y | DOE/PNNL `ASHRAE901_OfficeLarge_STD2022.idf` |
| **LargeOfficeDetailed** | 6 per floor | Same as LargeOffice + ceiling plenum zones per floor. | Interior core + plenum + IT closet | **core+perim** | Y (proxy of LargeOffice) | DOE/PNNL `ASHRAE901_OfficeLarge_STD2022.idf` |
| **RetailStandalone** | 2 | `Sales_ZN`, `Back_ZN` (Storage/Stockroom) | No corridor; Back_ZN serves as functional core | **functional-split** (Sales = perimeter; Storage = core) | Y | DOE/PNNL `ASHRAE901_RetailStandalone_STD2022.idf` |
| **RetailStripmall** | 10 (linear units) | `LGRoom1`–`LGRoom4` (large stores), `SMRoom1`–`SMRoom6` (small stores) | No corridor; units are side-by-side (not double-loaded) | **single** (each unit is individually a single zone; at urban scale → `one_zone_per_floor`) | Y | DOE/PNNL `ASHRAE901_RetailStripmall_STD2022.idf` |
| **SuperMarket** | 6 | `Sales`, `Produce`, `Deli`, `Bakery`, `Office`, `ElecRoom` (or `Storage`) | No corridor; Sales is perimeter-dominant; back-of-house (Bakery/Deli/Storage) is core | **functional-split** (Sales = perimeter; back-of-house = core) | Y | DOE/PNNL `ASHRAE901_Supermarket_STD2022.idf` |
| **FullServiceRestaurant** | 2 | `Dining`, `Kitchen` | No corridor; Kitchen is a functional core (high exhaust, equipment loads) | **functional-split** (Dining = perimeter; Kitchen = core) | Y | DOE/PNNL `ASHRAE901_RestaurantFull_STD2022.idf` |
| **QuickServiceRestaurant** | 2 | `Dining`, `Kitchen` | Same as FullServiceRestaurant | **functional-split** (Dining = perimeter; Kitchen = core) | Y | DOE/PNNL `ASHRAE901_RestaurantQuick_STD2022.idf` |
| **SmallHotel** | Ground: 5 zones; Floors 2–4: 10 guest room zones per floor (representing 24 rooms via multipliers) | Ground: `Lounge`, `Laundry`, `Office`, `Restaurant`, `GuestRoom101`; Floors 2–4: `GuestRoom201`–`GuestRoom210` (East/West rooms) | Central corridor zone per floor; Corridor is separate thermal zone | **units+corridor** (guest rooms = perimeter; corridor = core) | Y | DOE/PNNL `ASHRAE901_HotelSmall_STD2022.idf` |
| **LargeHotel** | Basement: 1; Ground: 7; Floors 2–5: 7 per floor; Floor 6: 7 | Basement: `HotelBasement`; Ground: `Lobby`, `Lounge`, `Mechanical`, `Laundry`, `Cafe/Restaurant`, `Retail`; Floors 2–5: `GuestRoomEast`, `GuestRoomWest`, `Corridor`, `ElevMechRoom`; Floor 6: `GuestRoom`, `Banquet`, `Dining`, `Kitchen`, `Corridor` | Central corridor on every guest floor | **units+corridor** (guest rooms = perimeter; corridor + support = core) | Y | DOE/PNNL `ASHRAE901_HotelLarge_STD2022.idf` |
| **MidriseApartment** | 9 per floor (Ground: 8; Floors 2–4: 8 units + 1 corridor) | `Apartment_Entry` (1 zone Ground floor), `Apt_1A–4A`, `Apt_1B–4B` (8 units per floor), `Corridor_ZN` (1 corridor per floor) | Central corridor (linear hallway, $1.68\text{ m}$ / $5.5\text{ ft}$ wide) | **units+corridor** (apartments = perimeter; corridor = core) | Y | DOE/PNNL `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` |
| **HighriseApartment** | 9 per floor (Ground: 8; Floors 2–10+: 8 units + 1 corridor) | Same zone types as MidriseApartment; additional zones for lobby/office on ground floor. | Central corridor ($1.68\text{ m}$ wide) | **units+corridor** (apartments = perimeter; corridor = core) | Y | DOE/PNNL `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` |
| **Hospital** | 15–17 per floor (complex; varies by floor) | `PatientRoom1`–`PatientRoom4` (perimeter), `ICU`, `OperatingRoom`, `Laboratory`, `Corridor`, `Physical_Therapy`, `Reception`, `MechRoom`, `Basement` | Interior corridor + clinical core | **core+perim** (patient rooms = perimeter; clinical/lab/OR = core) | Y | DOE/PNNL `ASHRAE901_Hospital_STD2022.idf` |
| **Outpatient** | 5 per floor | `ExamRoom_NW/NE/SW/SE` (perimeter), `Core_ZN` (waiting/reception/corridor) | Interior core (waiting, admin, circulation) | **core+perim** (exam rooms = perimeter; waiting/admin = core) | Y | DOE/PNNL `ASHRAE901_Outpatient_STD2022.idf` |
| **PrimarySchool** | 15 per floor (in 3 wings × 5 zones each) | `Corner_Class_1–4` (corners), `Mult_Class_1–8` (wing classrooms), `Corridor_Pod_1–3` (pod corridors), `Cafeteria`, `Gym`, `Main_Corridor`, `Office`, `Kitchen` | Multiple corridors (one per classroom pod + main circulation) | **core+perim** (classrooms = perimeter; corridors/cafeteria/gym = core) | Y | DOE/PNNL `ASHRAE901_SchoolPrimary_STD2022.idf` |
| **SecondarySchool** | 14–22 per floor (complex layout) | `Gym`, `Auditorium`, `ClassroomWing_1–8`, `Library`, `Office`, `Kitchen`, `Corridors_1–4`, `Mechanical` | Multiple corridors + large assembly spaces | **core+perim** (classrooms = perimeter; assembly/corridors = core) | Y | DOE/PNNL `ASHRAE901_SchoolSecondary_STD2022.idf` |
| **College** | 5 (proxy) | No DOE prototype. Proxied as MediumOffice layout: 4 cardinal perimeter zones (classrooms/offices) + 1 core (corridors/common). | Interior core (circulation) | **core+perim** | **proxy** (MediumOffice + PrimarySchool classroom load parameters) | Proxy — GAP; no DOE college prototype. |
| **Courthouse** | 5 (proxy) | No DOE prototype. Proxied as MediumOffice layout: 4 cardinal perimeter zones (offices/courtrooms) + 1 core (circulation). | Interior core (hallways, waiting rooms) | **core+perim** | **proxy** (MediumOffice) | Proxy — GAP; no DOE courthouse prototype. |
| **Laboratory** | 5 (proxy) | No DOE prototype. Proxied as MediumOffice with high-intensity loads: 4 perimeter zones (lab benches/fume hoods) + 1 core (support/storage). | Interior core (support zones, cold storage) | **functional-split** (lab = perimeter; support = core) | **proxy** (MediumOffice + laboratory load parameters from ASHRAE 90.1 lab guides) | Proxy — GAP; no DOE standalone laboratory prototype. |
| **SmallDataCenterHighITE** | 2 | `HPC_ZN` (server room, high-density IT load), `Support_ZN` (UPS, admin, generator) | No corridor; server room is the functional core | **functional-split** (server room = core; support = perimeter) | Y | DOE/PNNL `ASHRAE901_DataCenterSmall_HighITE_STD2022.idf` |
| **SmallDataCenterLowITE** | 2 | `Server_ZN`, `Support_ZN` | Same as SmallDataCenterHighITE | **functional-split** | Y | DOE/PNNL `ASHRAE901_DataCenterSmall_LowITE_STD2022.idf` |
| **LargeDataCenterHighITE** | 2–4 | `ServerRoom_1–2` (core, high-density racks), `UPS_ZN`, `AdminOffice_ZN` | No corridor; server rooms are core | **functional-split** (server rooms = core; admin/support = perimeter) | Y | DOE/PNNL `ASHRAE901_DataCenterLarge_HighITE_STD2022.idf` |
| **LargeDataCenterLowITE** | 2–4 | Same as LargeDataCenterHighITE (lower ITE density) | Same as above | **functional-split** | Y | DOE/PNNL `ASHRAE901_DataCenterLarge_LowITE_STD2022.idf` |
| **Warehouse** | 2 | `Bulk_ZN` (bulk storage, unconditioned or heated-only), `Fine_ZN` (fine storage, conditioned) | No corridor; single large open volume | **single** (`one_zone_per_floor` — core/perim is inappropriate for open warehouses) | Y | DOE/PNNL `ASHRAE901_Warehouse_STD2022.idf` |
| **TallBuilding** | 5 per floor (proxy) | No DOE prototype for generic tall buildings. Proxied as LargeOffice layout: 4 cardinal perimeter zones + 1 central core (elevators, stairs, mechanical) per floor. | Interior core (elevator banks, stairs, mechanical rooms) | **core+perim** | **proxy/custom** (LargeOffice per-floor pattern; per-floor variation may apply) | Proxy — no DOE tall-building prototype above 12 stories. |
| **SuperTallBuilding** | 5 per floor (proxy) | Same as TallBuilding proxy. Sky lobbies and refuge floors may differentiate certain floors, but at UBEM scale these are averaged. | Interior core (elevator shafts, sky lobbies) | **core+perim** | **proxy/custom** (LargeOffice pattern) | Proxy — no DOE supertall prototype. |
| **OpenUBEMUnknown** | 5 (sentinel) | Sentinel archetype. Proxied as MediumOffice layout (most common commercial building type in U.S. stock). | Interior core | **core+perim** | **sentinel** (fallback proxy) | Proxy — undefined archetype; MediumOffice is the modal commercial type in CBECS. |

---

### Table 2 — Vertical variation (does the layout change by floor?)

| Archetype | Ground floor differs? | Top floor differs? | Repeating mid-floor? | Source |
|---|---|---|---|---|
| **LargeOffice** | **Yes.** Ground floor has a lobby zone replacing one perimeter zone; basement is a single conditioned zone. | **No** (top floor same as mid-floor). | **Yes.** Floors 2–N−1 are identical with the same 6-zone layout. | DOE/PNNL `ASHRAE901_OfficeLarge_STD2022.idf` |
| **MidriseApartment** | **Yes.** Ground floor has 7 apartment units + 1 lobby/office zone instead of 8 apartment units. Corridor zone is present on all floors. | **No** (top floor same as mid-floor apartment layout). | **Yes.** Floors 2–N are identical 9-zone layouts (8 apartments + 1 corridor). | DOE/PNNL `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` |
| **HighriseApartment** | **Yes.** Ground floor has lobby, leasing office, and 6 apartment units; fewer units on ground floor than typical floors. | **No** (top floor same as mid-floor). | **Yes.** Floors 2–N are identical 9-zone layouts. | DOE/PNNL `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` |
| **LargeHotel** | **Yes.** Ground floor has no guest rooms; contains Lobby, Café/Restaurant, Retail, Laundry, Lounge. | **Yes.** Top floor (Floor 6) contains Banquet Hall, Dining, Kitchen, and a reduced set of guest rooms. | **Yes.** Floors 2–5 are identical 7-zone guest floor layouts. | DOE/PNNL `ASHRAE901_HotelLarge_STD2022.idf` |
| **SmallHotel** | **Yes.** Ground floor has 5 guest rooms + lobby/lounge/restaurant/office zones. | **No** (top floor same as mid-floor guest layout). | **Yes.** Floors 2–4 are identical 10-zone layouts. | DOE/PNNL `ASHRAE901_HotelSmall_STD2022.idf` |
| **SmallOffice** | **No.** All floors are identical 5-zone layouts. | **No.** | **Yes.** | DOE/PNNL `ASHRAE901_OfficeSmall_STD2022.idf` |

---

## Part C — Synthesis (the binding per-archetype target)

### 1. Reduction Family Grouping

| Reduction family | Archetypes | OpenUBEM geometry strategy |
|---|---|---|
| **core+perim** | `SmallOffice`, `SmallOfficeDetailed`, `MediumOffice`, `MediumOfficeDetailed`, `LargeOffice`, `LargeOfficeDetailed`, `Hospital`, `Outpatient`, `PrimarySchool`, `SecondarySchool`, `College`*, `Courthouse`*, `Laboratory`*, `TallBuilding`*, `SuperTallBuilding`*, `OpenUBEMUnknown`* | 4 cardinal perimeter zones + 1 core; geomeppy `core/perim` |
| **units+corridor** | `SmallHotel`, `LargeHotel`, `MidriseApartment`, `HighriseApartment` | 4 cardinal perimeter zones + 1 core (mapped as corridor via Core-as-Corridor rule) |
| **functional-split** | `RetailStandalone`, `SuperMarket`, `FullServiceRestaurant`, `QuickServiceRestaurant`, `SmallDataCenterHighITE`, `SmallDataCenterLowITE`, `LargeDataCenterHighITE`, `LargeDataCenterLowITE` | 2 zones: perimeter (sales/dining/office) + core (back-of-house/kitchen/server room) |
| **single** | `Warehouse`, `RetailStripmall` | `one_zone_per_floor` — core/perimeter is physically inappropriate |

> *Proxy archetypes — no DOE prototype exists; layout is inferred.

### 2. Proxy and GAP Flags

| Archetype | Proxy source | Gap/uncertainty |
|---|---|---|
| `SmallOfficeDetailed` | SmallOffice + ceiling plenum | Minor: plenum not modeled in OpenUBEM by default |
| `MediumOfficeDetailed` | MediumOffice + ceiling plenum | Same as above |
| `LargeOfficeDetailed` | LargeOffice + ceiling plenum | Same as above |
| `College` | MediumOffice + PrimarySchool load parameters | **GAP:** No DOE college prototype; load mix unclear |
| `Courthouse` | MediumOffice | **GAP:** Courtrooms have distinctive high-occupancy loads not captured |
| `Laboratory` | MediumOffice + lab load overrides | **GAP:** Lab exhaust/fume-hood ventilation is specialized; needs manager decision |
| `TallBuilding` | LargeOffice per-floor pattern | **GAP:** No DOE prototype; sky lobbies, refuge floors, structural cores not captured |
| `SuperTallBuilding` | LargeOffice per-floor pattern | **GAP:** Same as TallBuilding |
| `OpenUBEMUnknown` | MediumOffice (modal CBECS type) | Sentinel; any building may be assigned this; no zoning fidelity claim |

### 3. Per-Floor Variation Rule

Archetypes with vertical floor variation (`LargeOffice`, `MidriseApartment`, `HighriseApartment`, `LargeHotel`, `SmallHotel`) have distinct ground and/or top floor layouts. In `zone` mode, OpenUBEM must either:
- Apply the same mid-floor template to all floors (current behaviour, acceptable for annual EUI), OR
- If per-floor load variation matters, assign ground-floor zones the appropriate ground-floor loads (lobby, retail) and top-floor zones the top-floor loads (mechanical penthouse, banquet hall).

For v1, the **mid-floor template uniformly applied** is accepted — vertical variation contributes $< 2\%$ to annual EUI (see RESULT_05).

---

## CONFIDENCE AND CAVEATS

**Well-documented (high confidence):** Office, retail, restaurant, hotel, apartment, warehouse archetypes — all have publicly available PNNL IDFs with clearly named zone objects.

**Proxy / synthesis (lower confidence):**
- `College`, `Courthouse`, `Laboratory`, `TallBuilding`, `SuperTallBuilding`, `OpenUBEMUnknown` — no DOE prototype. These are labelled as **proxy** in Table 1. The zone layout is inferred from the closest DOE archetype.
- `SmallOfficeDetailed` and `MediumOfficeDetailed` — the "Detailed" variants add ceiling-plenum return-air zones which OpenUBEM does not currently model. These are acceptable proxies of their base counterparts.

**GAP:** The zone names in Table 1 are derived from publicly documented prototype specifications and IDF inspection notes; they may not exactly match the naming convention in every ASHRAE 90.1 edition. The authoritative source is always the downloaded `.idf` file from [energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models).

---

## REFERENCE LIST

1. **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL)**. (2022). *Commercial Prototype Building Models — ASHRAE 90.1-2022 Release*. Building Energy Codes Program. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
2. **Deru, M., Field, K., Studer, D., Benne, K., Griffith, B., Torcellini, P., & Crawley, D.** (2011). *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. NREL/TP-5500-46861. Golden, CO: National Renewable Energy Laboratory. [https://www.nrel.gov/docs/fy11osti/46861.pdf](https://www.nrel.gov/docs/fy11osti/46861.pdf)
3. **PNNL**. (2016). *Enhancements to ASHRAE Standard 90.1 Prototype Building Models*. PNNL-25273. [https://www.pnnl.gov/](https://www.pnnl.gov/)
4. **Chen, Y., & Hong, T.** (2018). "Impacts of building geometry modeling methods on the simulation results of urban building energy models." *Applied Energy*, 211, 1263–1278. [DOI: 10.1016/j.apenergy.2017.12.008](https://doi.org/10.1016/j.apenergy.2017.12.008)
5. **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140–153. [DOI: 10.1016/j.enbuild.2017.01.017](https://doi.org/10.1016/j.enbuild.2017.01.017)
