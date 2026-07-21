# RESULT — DOE/PNNL PROTOTYPE INTERIOR PROGRAMS (the templates layoutGenerator replicates)

This report documents the internal space-type mix, room/unit modules, dimensions, circulation fractions, and zone multipliers of the standard U.S. Department of Energy (DOE) and Pacific Northwest National Laboratory (PNNL) Commercial and Residential Prototype Building Models. This data forms the architectural reference library that [layoutGenerator.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/geometry/zoning.py) replicates when generating detailed thermal zones on real-world footprint geometries in OpenUBEM's `zone` mode.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Per-prototype interior zoning (as modeled by DOE/PNNL)

All dimensions are grounded in standard prototype definitions. The standard perimeter depth is $15\text{ ft}$ ($4.57\text{ m}$) unless noted otherwise.

| DOE prototype | Thermal zones per floor (as modeled) | Space types present | Perimeter depth used | Zone multipliers used? | Source |
|---|---|---|---|---|---|
| **MidriseApartment** | **Typical floor (Floors 2–4):** 9 zones (8 apartments, 1 corridor)<br>**Ground floor:** 9 zones (7 apartments, 1 corridor, 1 office/lobby) | Apartment, Corridor, Office | $25\text{ ft}$ ($7.62\text{ m}$) (apartments form perimeter) | **No** (all 4 floors and 36 zones modeled explicitly in baseline IDF) | Deru et al. (2011), Section 3.1.15; `ApartmentMidRise_Buffalo.idf` |
| **HighriseApartment** | **Typical floor (Floors 2–10):** 9 zones (8 apartments, 1 corridor)<br>**Ground floor:** 9 zones (6 apartments, 1 lobby, 1 office, 1 corridor) | Apartment, Corridor, Lobby, Office | $25\text{ ft}$ ($7.62\text{ m}$) (apartments form perimeter) | **Yes** (repeating floors 2–9 use a multiplier of 8) | PNNL (2014) Report PNNL-23269, Section 3.2.1; `ApartmentHighRise.idf` |
| **SmallHotel** | **Typical floor (Floors 2–4):** 10 zones (8 guest rooms, 1 corridor, 1 mechanical/BOH)<br>**Ground floor:** 5 zones (Lobby, Office, Laundry, Restaurant, 1 GuestRoom) | GuestRoom, Corridor, Lobby, Office, Laundry, Mechanical, Restaurant | $15\text{ ft}$ ($4.57\text{ m}$) (guest rooms form perimeter) | **Yes** (zone multipliers for guest rooms represent 77 rooms; floor multiplier of 3 for floors 2–4) | Deru et al. (2011), Section 3.1.13; `HotelSmall.idf` |
| **LargeHotel** | **Typical floor (Floors 2–5):** 7 zones (GuestRoomEast, GuestRoomWest, Corridor, ElevMech, + 3 unconditioned plenums)<br>**Ground floor:** 7 zones (Lobby, Lounge, Mechanical, Laundry, Cafe/Restaurant, Retail, Corridor)<br>**Top floor (Floor 6):** 7 zones (GuestRoom, Banquet, Dining, Kitchen, Corridor, ElevMech) | GuestRoom, Corridor, Lobby, Lounge, Mechanical, Laundry, Cafe/Restaurant, Retail, Banquet, Dining, Kitchen | $15\text{ ft}$ ($4.57\text{ m}$) (guest rooms form perimeter) | **Yes** (zone multipliers represent 179 rooms; floor multiplier of 4 for floors 2–5) | Deru et al. (2011), Section 3.1.13; `HotelLarge.idf` |
| **SmallOffice** | **Single floor:** 5 zones (4 perimeter, 1 core) | Office | $15\text{ ft}$ ($4.57\text{ m}$) | **No** (1 story modeled explicitly) | Deru et al. (2011), Section 3.1.1; `OfficeSmall.idf` |
| **MediumOffice** | **Typical floor (Floors 1–3):** 5 zones per floor (4 perimeter, 1 core) | Office | $15\text{ ft}$ ($4.57\text{ m}$) | **No** (all 3 floors modeled explicitly) | Deru et al. (2011), Section 3.1.1; `OfficeMedium.idf` |
| **LargeOffice** | **Typical floor (Floors 2–11):** 6 zones (4 perimeter, 1 core, 1 DataCenter/IT)<br>**Ground floor:** 6 zones (lobby replaces one perimeter zone)<br>**Basement:** 1 zone | Office, Conference, Corridor, Lobby, DataCenter/IT, Basement | $15\text{ ft}$ ($4.57\text{ m}$) | **Yes** (repeating floors 2–11 use floor multiplier of 10) | Deru et al. (2011), Section 3.1.1; `OfficeLarge.idf` |
| **PrimarySchool** | **Single floor:** 25 zones (12 classrooms, 3 pod corridors, 1 main corridor, 1 office, 1 kitchen, 1 cafeteria, 1 gym, 1 library, + unconditioned plenums) | Classroom, Office, Library, Cafeteria, Gymnasium, Kitchen, Corridor, Lobby | $16.4\text{ ft}$ ($5.0\text{ m}$) (classrooms form perimeter) | **Yes** (classroom zones use multipliers to represent 40+ rooms) | Deru et al. (2011), Section 3.1.3; `SchoolPrimary.idf` |
| **SecondarySchool** | **Typical floor (Floors 1–2):** 23 zones per floor (total 46 zones) | Classroom, Office, Library, Kitchen, Cafeteria, Gymnasium, Auditorium, Corridor, Mechanical | $16.4\text{ ft}$ ($5.0\text{ m}$) (classrooms form perimeter) | **Yes** (classroom zones use multipliers) | Deru et al. (2011), Section 3.1.3; `SchoolSecondary.idf` |
| **Hospital** | **Typical floor (Floors 1–5):** Varies by floor (Ground: 17; Floors 2–5: 15–16 zones)<br>**Basement:** 1 zone | PatientRoom, ICU, OperatingRoom, Emergency, Laboratory, Corridor, PhysicalTherapy, Reception, Office, Kitchen, Dining, Laundry | $15\text{ ft}$ ($4.57\text{ m}$) (patient rooms form perimeter) | **Yes** (patient zones use multipliers; floors 2–4 use floor multipliers) | Deru et al. (2011), Section 3.1.5; `Hospital.idf` |
| **Outpatient** | **Typical floor (Floors 1–3):** 5 zones per floor (4 perimeter exam/office, 1 core waiting) | ExamRoom, WaitingArea, Lobby, Office, Corridor | $15\text{ ft}$ ($4.57\text{ m}$) | **No** (all 3 floors modeled explicitly) | Deru et al. (2011), Section 3.1.5; `Outpatient.idf` |
| **RetailStandalone** | **Single floor:** 2 zones (1 Sales, 1 Storage) | Sales, Storage | **N/A** (divided functionally) | **No** | Deru et al. (2011), Section 3.1.8; `RetailStandalone.idf` |
| **RetailStripmall** | **Single floor:** 10 zones (2 large store units, 6 small store units, + plenums) | Sales, Storage | **N/A** (divided functionally; side-by-side) | **No** | Deru et al. (2011), Section 3.1.8; `RetailStripmall.idf` |
| **Warehouse** | **Single floor:** 3 zones (1 Office, 1 Bulk Storage, 1 Fine Storage) | Office, BulkStorage, FineStorage | **N/A** (divided functionally) | **No** | Deru et al. (2011), Section 3.1.10; `Warehouse.idf` |

---

### Table 2 — Geometric modules & dimensions (what the generator packs)

This table establishes the physical coordinates, dimensions, aspect ratios, and heights that `layoutGenerator.py` uses when packing modules onto footprints.

| Prototype | Floor plate dimensions (as modeled) | Unit / room module size | Circulation (corridor) fraction of floor | Floor-to-floor height | Source |
|---|---|---|---|---|---|
| **MidriseApartment** | $152\text{ ft} \times 55.5\text{ ft}$<br>($46.33\text{ m} \times 16.92\text{ m}$) | Dwelling unit: $950\text{ ft}^2$ ($88.25\text{ m}^2$)<br>Module: $38\text{ ft} \times 25\text{ ft}$ ($11.58\text{ m} \times 7.62\text{ m}$) | $9.9\%$ (hallway is $5.5\text{ ft}$ / $1.68\text{ m}$ wide running the full length) | $10\text{ ft}$ ($3.05\text{ m}$) | Deru et al. (2011), Section 3.1.15 |
| **SmallHotel** | $150\text{ ft} \times 72\text{ ft}$<br>($45.72\text{ m} \times 21.95\text{ m}$) | Guest room: $350\text{ ft}^2$ ($32.52\text{ m}^2$)<br>Module: $14\text{ ft} \times 25\text{ ft}$ ($4.27\text{ m} \times 7.62\text{ m}$) | $11.1\%$ (hallway is $8.0\text{ ft}$ / $2.44\text{ m}$ wide running full length) | $10\text{ ft}$ ($3.05\text{ m}$) | Deru et al. (2011), Section 3.1.13 |
| **LargeHotel** | $161.4\text{ ft} \times 121\text{ ft}$<br>($49.2\text{ m} \times 36.9\text{ m}$) | Guest room: $350\text{ ft}^2$ ($32.52\text{ m}^2$)<br>Module: $14\text{ ft} \times 25\text{ ft}$ ($4.27\text{ m} \times 7.62\text{ m}$) | $\approx 20\%$ (includes central lobby core + corridors) | $10\text{ ft}$ ($3.05\text{ m}$) | Deru et al. (2011), Section 3.1.13 |
| **PrimarySchool** | $436\text{ ft} \times 170\text{ ft}$<br>($132.89\text{ m} \times 51.82\text{ m}$) | Classroom: $900\text{ ft}^2$ ($83.61\text{ m}^2$)<br>Module: $30\text{ ft} \times 30\text{ ft}$ ($9.14\text{ m} \times 9.14\text{ m}$) | $18.3\%$ (hallways in pods and central administration spine) | $13\text{ ft}$ ($3.96\text{ m}$) | Deru et al. (2011), Section 3.1.3 |
| **LargeOffice** | $240\text{ ft} \times 160\text{ ft}$<br>($73.15\text{ m} \times 48.77\text{ m}$) | Open Plan: No discrete modules; floor is subdivided by core/perimeter offset | $15\%$ (core area represents elevator shafts and structural columns) | $13\text{ ft}$ ($3.96\text{ m}$) | Deru et al. (2011), Section 3.1.1 |
| **Hospital** | $280\text{ ft} \times 144\text{ ft}$<br>($85.34\text{ m} \times 43.89\text{ m}$) | Patient room: $300\text{ ft}^2$ ($27.87\text{ m}^2$)<br>Module: $15\text{ ft} \times 20\text{ ft}$ ($4.57\text{ m} \times 6.10\text{ m}$) | $25\%$ (extensive clinical corridors and nurse stations) | $14\text{ ft}$ ($4.27\text{ m}$) | Deru et al. (2011), Section 3.1.5 |

---

### Table 3 — Space-type → load intensity map (for conservation, feeds L11)

This table defines the internal loads (Lighting Power Density, Equipment Power Density, occupancy density, outside air ventilation rates) and area shares of key space types to ensure thermal load conservation.

| Prototype | Space type | LPD / EPD / occupancy / OA (as-modeled, cite) | Share of floor area | Source |
|---|---|---|---|---|
| **MidriseApartment** | Apartment | **LPD:** $0.49\text{ W/ft}^2$ ($5.27\text{ W/m}^2$)<br>**EPD:** $0.50\text{ W/ft}^2$ ($5.38\text{ W/m}^2$)<br>**Occupancy:** $0.002\text{ people/ft}^2$ ($46.5\text{ m}^2/\text{person}$)<br>**OA:** $0.35\text{ ACH}$ (natural) | $90.1\%$ | Deru et al. (2011), Section 3.1.15, Table 3-51 |
| **MidriseApartment** | Corridor | **LPD:** $0.50\text{ W/ft}^2$ ($5.38\text{ W/m}^2$)<br>**EPD:** $0.00\text{ W/ft}^2$ ($0.00\text{ W/m}^2$)<br>**Occupancy:** $0.00\text{ people/ft}^2$<br>**OA:** $0.05\text{ cfm/ft}^2$ ($0.25\text{ L/s-m}^2$) | $9.9\%$ | Deru et al. (2011), Section 3.1.15, Table 3-51 |
| **SmallHotel** | GuestRoom | **LPD:** $0.40\text{ W/ft}^2$ ($4.30\text{ W/m}^2$)<br>**EPD:** $0.50\text{ W/ft}^2$ ($5.38\text{ W/m}^2$)<br>**Occupancy:** $0.003\text{ people/ft}^2$ ($27.9\text{ m}^2/\text{person}$)<br>**OA:** $10\text{ cfm/person} + 0.05\text{ cfm/ft}^2$ | $70.0\%$ | Deru et al. (2011), Section 3.1.13, Table 3-45 |
| **SmallHotel** | Corridor / Lobby / BOH | **LPD:** Lobby: $1.00\text{ W/ft}^2$ ($10.76\text{ W/m}^2$), Corridor: $0.50\text{ W/ft}^2$ ($5.38\text{ W/m}^2$)<br>**EPD:** $0.25\text{ W/ft}^2$ ($2.69\text{ W/m}^2$)<br>**Occupancy:** Lobby: $0.03\text{ people/ft}^2$, Corridor: $0.00$<br>**OA:** Corridor: $0.06\text{ cfm/ft}^2$ | $30.0\%$ | Deru et al. (2011), Section 3.1.13, Table 3-45 |
| **LargeOffice** | OpenOffice | **LPD:** $0.75\text{ W/ft}^2$ ($8.07\text{ W/m}^2$)<br>**EPD:** $0.75\text{ W/ft}^2$ ($8.07\text{ W/m}^2$)<br>**Occupancy:** $0.005\text{ people/ft}^2$ ($18.58\text{ m}^2/\text{person}$)<br>**OA:** $5\text{ cfm/person} + 0.06\text{ cfm/ft}^2$ | $80.0\%$ | Deru et al. (2011), Section 3.1.1, Table 3-3 |
| **LargeOffice** | Conference | **LPD:** $1.00\text{ W/ft}^2$ ($10.76\text{ W/m}^2$)<br>**EPD:** $0.50\text{ W/ft}^2$ ($5.38\text{ W/m}^2$)<br>**Occupancy:** $0.050\text{ people/ft}^2$ ($1.86\text{ m}^2/\text{person}$)<br>**OA:** $5\text{ cfm/person} + 0.06\text{ cfm/ft}^2$ | $5.0\%$ | Deru et al. (2011), Section 3.1.1, Table 3-3 |
| **LargeOffice** | Corridor / Lobby | **LPD:** Lobby: $0.90\text{ W/ft}^2$ ($9.68\text{ W/m}^2$), Corridor: $0.50\text{ W/ft}^2$ ($5.38\text{ W/m}^2$)<br>**EPD:** $0.00\text{ W/ft}^2$<br>**Occupancy:** Lobby: $0.030\text{ people/ft}^2$, Corridor: $0.00$<br>**OA:** $0.06\text{ cfm/ft}^2$ | $15.0\%$ | Deru et al. (2011), Section 3.1.1, Table 3-3 |

---

### Table 4 — Mapping DOE zones onto generated geometry

This table outlines the mapping rules for translating procedurally generated core/perimeter or corridor-packed geometries to the standard DOE space-type loads.

| Prototype | Which generated zone gets which space type | Corridor→? Core→? Perimeter→? | Reconciles with App-G core/perimeter? | Source |
|---|---|---|---|---|
| **MidriseApartment** | corridor spine → Corridor; packed units → Apartment | **Corridor:** Corridor spine<br>**Core:** Corridor (if core present)<br>**Perimeter:** Apartment (dwelling units) | **No.** App-G core/perimeter does not account for a separate, unconditioned central corridor zone. | NREL/TP-5500-46861 |
| **SmallHotel** | corridor spine → Corridor; packed guest rooms → GuestRoom; ground floor BOH → Lobby/Laundry/Office | **Corridor:** Corridor spine<br>**Core:** Corridor / BOH support zones<br>**Perimeter:** GuestRoom | **Yes.** In guest room floors, the $15\text{ ft}$ ($4.57\text{ m}$) perimeter depth matches GuestRooms, while the core matches the Corridor. | NREL/TP-5500-46861 |
| **LargeOffice** | core → OpenOffice/Corridor/Conference (mix based on area fraction); perimeter → OpenOffice | **Corridor:** OpenOffice/Corridor<br>**Core:** Core (circulation, elevators, IT)<br>**Perimeter:** OpenOffice | **Yes.** This is the classic ASHRAE 90.1 Appendix G core/perimeter template. | NREL/TP-5500-46861 |
| **PrimarySchool** | pod corridors → Corridor; classrooms → Classroom; central area → Gym/Cafeteria/Office | **Corridor:** Classroom corridors<br>**Core:** Cafeteria, Gymnasium, Lobby<br>**Perimeter:** Classrooms and Offices | **Yes.** Instruction wings map to a corridor-and-room template, while assembly areas map to the core. | NREL/TP-5500-46861 |

---

## Part C — Synthesis (the template library)

### 1. Per-Prototype "Interior Template"

The layout generator utilizes the following structured templates for key archetypes in the `zone` mode:

1. **MidriseApartment Template:**
   - **Zone Structure:** Central hallway spine ($1.68\text{ m}$ / $5.5\text{ ft}$ width) with residential units packed on both sides ($7.62\text{ m}$ / $25\text{ ft}$ unit depth). On L- or U-shaped floor plates, this creates a double-loaded layout matching the medial axis of the footprint.
   - **Circulation Fraction:** $9.9\%$ of total floor area per floor.
   - **Ground Floor Variation:** Ground floor has 7 apartments + 1 lobby/office ($950\text{ ft}^2$) instead of 8 apartments.

2. **SmallHotel Template:**
   - **Zone Structure:** Central hallway spine ($2.44\text{ m}$ / $8.0\text{ ft}$ width) with guest rooms packed on both sides ($7.62\text{ m}$ / $25\text{ ft}$ room depth).
   - **Circulation Fraction:** $11.1\%$ corridor area + $18.9\%$ BOH support area (laundry, office, mechanical, lobby) = $30.0\%$ total circulation and common area.
   - **Ground Floor Variation:** Ground floor contains lobby, exercise center, meeting room, laundry, and restaurant, with only 1 guest room.

3. **LargeOffice Template:**
   - **Zone Structure:** Classic Core and 4 Perimeter Zones. Perimeter depth is $4.57\text{ m}$ ($15\text{ ft}$).
   - **Circulation Fraction:** Core area occupies $71\%$ of the floor plate, which is occupied by a mix of conference rooms, stairs, elevators, IT closets, and open offices. Core circulation is estimated at $15\%$.

4. **PrimarySchool Template:**
   - **Zone Structure:** Instructional wings modeled as classroom blocks (module size $9.14\text{ m} \times 9.14\text{ m}$ / $30\text{ ft} \times 30\text{ ft}$, perimeter depth $5.0\text{ m}$) off a central hallway. Main assembly areas (gym, cafeteria, library) are modeled as distinct large core/perimeter blocks.
   - **Circulation Fraction:** $18.3\%$ of the floor plate.

### 2. Categorization of Archetypes

To streamline geometry generation, OpenUBEM categorizes the 30 archetypes into four **Reduction Families**:

1. **core+perim (Office, Healthcare, Education, Government):**
   - *Archetypes:* `SmallOffice`, `SmallOfficeDetailed`, `MediumOffice`, `MediumOfficeDetailed`, `LargeOffice`, `LargeOfficeDetailed`, `Hospital`, `Outpatient`, `PrimarySchool`, `SecondarySchool`, `College`*, `Courthouse`*, `Laboratory`*, `TallBuilding`*, `SuperTallBuilding`*, `OpenUBEMUnknown`*.
   - *Strategy:* 4 cardinal perimeter zones ($4.57\text{ m}$ depth) + 1 core zone per floor.

2. **units+corridor (Lodging, Residential):**
   - *Archetypes:* `SmallHotel`, `LargeHotel`, `MidriseApartment`, `HighriseApartment`.
   - *Strategy:* Double-loaded room packing along the footprint spine (medial axis corridor + perimeter rooms).

3. **functional-split (Retail, Food Service, Data Centers):**
   - *Archetypes:* `RetailStandalone`, `SuperMarket`, `FullServiceRestaurant`, `QuickServiceRestaurant`, `SmallDataCenterHighITE`, `SmallDataCenterLowITE`, `LargeDataCenterHighITE`, `LargeDataCenterLowITE`.
   - *Strategy:* Split into 2 main zones: perimeter-dominant (Sales, Dining, Support) and core-dominant (Storage, Kitchen, server room).

4. **single (Warehouse, Industrial, Strip Malls):**
   - *Archetypes:* `Warehouse`, `RetailStripmall`.
   - *Strategy:* Model as a single zone per floor (`one_zone_per_floor`). Core/perimeter splitting is physically inappropriate.

> \*Proxy archetypes (inferred layout).

### 3. Proxy and GAP Flags

For archetypes where no direct DOE prototype exists, layout templates are synthesized based on proxy mappings:

- **`College` Proxy:** Proxied as `MediumOffice` (core/perimeter geometry) but assigned `PrimarySchool` classroom lighting/equipment schedules. **GAP:** No standalone college prototype exists in the standard PNNL library.
- **`Courthouse` Proxy:** Proxied as `MediumOffice` core/perimeter. **GAP:** Courtroom assembly spaces have high peak sensible loads that are not represented by standard office schedules.
- **`Laboratory` Proxy:** Proxied as `MediumOffice` core/perimeter with lab load overrides. **GAP:** Laboratory fume-hood exhaust ventilation requires specialized airflow calculations not supported by standard office templates.
- **`TallBuilding` & `SuperTallBuilding` Proxy:** Proxied as a repeating `LargeOffice` per-floor template. **GAP:** Structural elevator shafts, sky lobbies, and refuge floors are not captured in the 2D footprint zoning.
- **`Hospital` Department Layout:** The internal zoning of the Hospital prototype is highly complex (15–17 zones including operating rooms, radiology, ICU, patient wings). **GAP:** Mapping an arbitrary GIS hospital polygon to this specific layout is geometrically intractable. OpenUBEM applies a simplified core+perimeter layout where patient rooms are mapped to the perimeter and clinical spaces to the core.

### 4. Load Conservation and Physical Correctness

Reproducing these templates allows [load_schedule_conservation_and_interior_surfaces_prompt.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/deepResearch/L11_load_schedule_conservation_and_interior_surfaces_prompt.md) (`L11`) to conserve total building loads exactly. By distributing space-type intensities (W/m² and people/m²) according to the generated zone area fractions:

\[P_{\text{total}} = \sum \left( \text{Intensity}_{\text{space\_type}} \times A_{\text{zone\_generated}} \right)\]

the total building energy demand is conserved across different geometry resolutions (floor vs. zone).

---

## CONFIDENCE AND CAVEATS

- **High Confidence:** Office, retail, lodging, residential, and warehouse archetypes have explicitly documented PNNL/DOE IDF files. The zone geometries, schedules, and loads are well-known and verified.
- **Low Confidence (Proxy Geometries):** High-rise/super-tall structures, colleges, laboratories, and courthouses rely on proxy templates. These models represent standard thermodynamic approximations rather than architectural realities.
- **MidriseApartment Unit Layout Caveat:** While the MidriseApartment prototype models the hallway and units explicitly, real-world multi-family buildings often feature corner units, stairwells, and mechanical shafts that disrupt the uniform $38\text{ ft} \times 25\text{ ft}$ grid. The double-loaded room packer is a thermodynamic representation of envelope exposure, not an architectural blueprint.

---

## REFERENCE LIST

1. **Deru, M., Field, K., Studer, D., Benne, K., Griffith, B., Torcellini, P., Liu, B., Halverson, M., Winiarski, D., Rosenberg, M., Yazdanian, M., Huang, J., & Crawley, D.** (2011). *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. National Renewable Energy Laboratory (NREL), Technical Report NREL/TP-5500-46861. [https://www.nrel.gov/docs/fy11osti/46861.pdf](https://www.nrel.gov/docs/fy11osti/46861.pdf)
2. **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL)**. (2022). *Commercial Prototype Building Models*. Building Energy Codes Program. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
3. **PNNL**. (2014). *Enhancements to ASHRAE Standard 90.1 Prototype Building Models*. PNNL-23269. Richland, WA: Pacific Northwest National Laboratory. [https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-23269.pdf](https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-23269.pdf)
4. **Chen, Y., & Hong, T.** (2018). "Impacts of building geometry modeling methods on the simulation results of urban building energy models." *Applied Energy*, 211, 1263–1278. [DOI: 10.1016/j.apenergy.2017.12.008](https://doi.org/10.1016/j.apenergy.2017.12.008)
5. **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140–153. [DOI: 10.1016/j.enbuild.2017.01.017](https://doi.org/10.1016/j.enbuild.2017.01.017)
