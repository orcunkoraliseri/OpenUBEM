# RESULT_03_zone_level_zoning_schema — Zone-Level Core/Perimeter Zoning Schema on a Real Footprint

This report defines the **core/perimeter zoning schema** to be applied in OpenUBEM's `zone` mode (Resolution Level B1). It establishes how a building's real footprint polygon is procedurally sliced into core and perimeter thermal zones, evaluates the defensibility of generic core/perimeter zoning across all 26 archetypes (including residential and tall building classes), specifies robust fallbacks for degenerate geometries, and synthesizes these findings into a concrete rule set.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Core/perimeter geometry convention

| Parameter | Value (SI / IP) | Source (90.1 App G § / table, or prototype doc) |
|---|---|---|
| **Perimeter depth** (zone thickness from façade inward) | 4.57 m / 15 ft | ASHRAE Standard 90.1-2019, Normative Appendix G, Table G3.1, Row 8 "Thermal Blocks" (a) & (b). |
| **Number of perimeter zones per floor** | 4 zones by default (for rectangular footprints) or $N$ zones (one per exterior edge for irregular polygons). | ASHRAE Standard 90.1-2019, Normative Appendix G, Table G3.1, Row 8 "Thermal Blocks" (b) (separate block for each orientation). |
| **How perimeter is split by orientation on a real polygon** | Inward polygon offset to form the core; annulus divided by drawing lines from core vertices to corresponding outer footprint vertices. | geomeppy geometry engine (`geom/core_perimeter.py`) and CityBES pixel-rasterization method (Hong et al., 2018). |
| **Core-existence test** (min core area before core is dropped) | $A_{\text{core}} \ge 10.0\text{ m}^2$ (107.6 sq ft). If less, core is dropped and floor becomes a single zone. | OpenUBEM geometry module (`openubem/geometry/zoning.py` line 63) and geomeppy polygon-offset safety thresholds. |
| **Does perimeter depth vary by archetype / climate / use?** | No, Appendix G uses a constant 4.57 m (15 ft) depth. However, residential prototypes use 7.62 m (25 ft) unit depths. | ASHRAE 90.1-2019 Table G3.1; PNNL Prototype Model Specifications (PNNL-16770). |

---

### Table 2 — Per-archetype zone-level scheme (does core/perimeter even apply?)

| Archetype | DOE prototype's ACTUAL per-floor zoning | Is generic core+perimeter a defensible proxy? (Y / N / caveat) | Recommended `zone`-mode scheme | Source |
|---|---|---|---|---|
| `SmallOffice` | 5 zones (4 perimeter, 1 core) | Y | Generic core+perimeter (5 zones per floor, perimeter depth 4.57 m) | PNNL Small Office Prototype |
| `MediumOffice` | 5 zones per floor (4 perimeter, 1 core) | Y | Generic core+perimeter (5 zones per floor, perimeter depth 4.57 m) | PNNL Medium Office Prototype |
| `LargeOffice` | 6 zones per floor (4 perimeter, 1 core, 1 IT closet); basement is 1 zone. | Y | Generic core+perimeter (Lump IT closet into core; basement as 1 zone) | PNNL Large Office Prototype |
| `RetailStandalone` | 2 zones (Sales Area, Storage/Backroom) | Y (with caveat: over-zones sales area but captures solar exposure) | Generic core+perimeter (Sales assigned to both; storage mapped to core) | PNNL Stand-alone Retail Prototype |
| `RetailStripmall` | 10 linear zones (representing 10 separate storefront units side-by-side) | N (Strip malls are thin linear row structures with front/back exposures only) | one_zone_per_floor (narrow slab naturally forces fallback or linear division) | PNNL Strip Mall Prototype |
| `SuperMarket` | 6 zones (Sales, Produce, Bakery, Deli, Office, Storage) | N (zoning is highly functional and load-driven, not core/perimeter) | Generic core+perimeter (envelope proxy; map bakery/deli/storage to core) | PNNL Supermarket Prototype |
| `FullServiceRestaurant` | 2 zones (Dining Area, Kitchen) | N (Dining and Kitchen have radically different load and ventilation profiles) | Dining/Kitchen split (2 zones: Dining = 80% area/perimeter; Kitchen = 20%/core) | PNNL Full-Service Restaurant |
| `QuickServiceRestaurant` | 2 zones (Dining Area, Kitchen) | N (Same as FullServiceRestaurant) | Dining/Kitchen split (2 zones) or one_zone_per_floor if footprint < 200 m² | PNNL Quick-Service Restaurant |
| `SmallHotel` | guest rooms (perimeter by orientation), central corridor (core), lobby/office. | Y (with caveat: perimeter represents guest rooms, core represents corridor) | Generic core+perimeter (Map guest rooms to perimeter, corridor to core) | PNNL Small Hotel Prototype |
| `LargeHotel` | guest rooms (perimeter), corridor (core), retail, laundry, restaurant. | Y (Same as SmallHotel) | Generic core+perimeter (Map guest rooms to perimeter, corridor/service to core) | PNNL Large Hotel Prototype |
| `MidriseApartment` | 8 apartments per floor (perimeter), 1 central corridor (core). | N (creating a windowless residential core zone violates building codes) | Core-as-Corridor (core mapped to corridor template, perimeter to apartments) | PNNL Mid-rise Apartment Prototype |
| `HighriseApartment` | 8 apartments per floor (perimeter), 1 central corridor (core). | N (Same as MidriseApartment) | Core-as-Corridor (core mapped to corridor template, perimeter to apartments) | PNNL High-rise Apartment Prototype |
| `Hospital` | Highly complex (patient rooms perimeter, ORs/ICU/labs in core) | Y (defensible proxy; patient rooms = perimeter, clinical = core) | Generic core+perimeter (patient room templates to perimeter, clinical to core) | PNNL Hospital Prototype |
| `Outpatient` | Multiple zones (exam rooms perimeter, waiting/reception core) | Y | Generic core+perimeter (exam rooms to perimeter, reception to core) | PNNL Outpatient Prototype |
| `PrimarySchool` | classrooms (perimeter), offices/corridors (core), gym/cafeteria (unsplit) | Y (with caveat: assembly spaces should remain unsplit if modeled separately) | Generic core+perimeter (classrooms to perimeter, office/corridors to core) | PNNL Primary School Prototype |
| `SecondarySchool` | classrooms (perimeter), corridors (core), gym/auditorium (unsplit) | Y (Same as PrimarySchool) | Generic core+perimeter (classrooms to perimeter, office/corridors to core) | PNNL Secondary School Prototype |
| `College` | No prototype (varies; classrooms perimeter, lecture halls core) | Y | Generic core+perimeter (classrooms to perimeter, office/corridors to core) | N/A (Proxy-based convention) |
| `Laboratory` | No prototype (fume hoods/equipment core, offices perimeter) | Y (with caveat: high ventilation rates must map to lab core zones) | Generic core+perimeter (lab loads mapped to core, office loads to perimeter) | N/A (Proxy-based convention) |
| `Warehouse` | 2 zones (Bulk Storage, Fine Storage) | N (Warehouses are large single-volume spaces; perimeter zones are a poor proxy) | one_zone_per_floor (No core/perimeter splitting; model as 1 zone per floor) | PNNL Warehouse Prototype |
| `SmallDataCenterHighITE` / `LowITE` | IT Server Room (high load, core), admin/UPS/generator (perimeter) | N (Data centers are dominated by high-intensity IT server loads, not envelope) | Functional split (IT server room mapped to core, admin/support to perimeter) | PNNL Data Center Research |
| `LargeDataCenterHighITE` / `LowITE` | IT Server Rooms (core), admin/UPS (perimeter) | N (Same as SmallDataCenter) | Functional split (IT server room mapped to core, admin/support to perimeter) | PNNL Data Center Research |
| `TallBuilding` | No prototype (custom tall office/residential) | Y | Generic core+perimeter per floor (captures wind and solar gradients) | N/A (Custom archetype) |
| `SuperTallBuilding` | No prototype (custom tall office/residential) | Y | Generic core+perimeter per floor (captures wind and solar gradients) | N/A (Custom archetype) |
| `Courthouse` | No prototype (varies; courtrooms core, offices perimeter) | Y | Generic core+perimeter (courtroom loads to core, offices to perimeter) | N/A (Proxy-based convention) |
| `OpenUBEMUnknown` | N/A (Sentinel fallback) | Y | Generic core+perimeter (if footprint >= 500 m²) | N/A (Sentinel fallback) |

---

### Table 3 — Degenerate-footprint handling (the fallbacks)

| Case | OpenUBEM current behaviour | Recommended behaviour + rule | Source |
|---|---|---|---|
| **Footprint too narrow to buffer** (core empties / core < 10 m²) | Revert to `one_zone_per_floor`. | **Accept.** Revert to `one_zone_per_floor`. If the footprint width is less than $2 \times \text{perimeter\_depth}$, the space is entirely perimeter-dominated. | OpenUBEM geometry module (`zoning.py` line 63). |
| **Footprint with interior courtyard** (ring/hole) | Revert to `one_zone_per_floor`. | **Accept.** Revert to `one_zone_per_floor`. geomeppy's core/perimeter algorithm fails on donut geometries, producing vertex mismatches and E+ Fatal errors. | OpenUBEM geometry module (`zoning.py` line 73). |
| **Very small total footprint** (e.g. < 100 m²) | Core/perimeter attempted (may empty and revert). | **Revise.** Revert to `one_zone_per_floor` immediately if footprint area is $< 100\text{ m}^2$ (or $< 500\text{ m}^2$ per `decide_zoning_strategy`). Prevents tiny, unstable perimeter zones. | OpenUBEM zoning strategy (`zoning.py` line 18) & standard UBEM practice. |
| **Single-floor building** in `zone` mode | Core/perimeter with `num_floors=1`. | **Accept.** Core/perimeter with `num_floors=1` is defensible to capture orientation-dependent solar gains on the single floor. | OpenUBEM design doc & `PLAN_resolution_mode_switch.md` line 64. |
| **L-/U-/T-shaped real footprint** | Inward buffer (shape preserved). | **Accept.** shapely inward buffer. If non-convexity causes geomeppy extrusion to fail, execute the robust 4-tier fallback (DP 1.5 → convex hull → bbox). | OpenUBEM geometry module (`surfaces.py` line 281). |

---

### Table 4 — Precedent: how peer UBEM tools auto-zone real footprints

| Tool / paper | Auto-zoning method (core/perim? perimeter depth? real footprint or bbox?) | Applies to residential? | Source |
|---|---|---|---|
| **CityBES** | Pixel-based auto-zoning. Rasterizes arbitrary GIS footprints, buffers boundary inward by 4.57 m (15 ft) for core, and segments perimeter into 4 orientation zones. | Yes, applies identical core/perimeter zoning to residential at city scale. | Hong et al. (2018), *CityBES: A Web-based Platform for City-scale Building Energy Efficiency*. |
| **AutoBEM / AutoBEM-Energy** | Straight-skeleton polygon offset or 1-zone-per-floor. Supports core/perimeter zoning with a standard 15 ft (4.57 m) perimeter depth and 4 orientation zones. | Yes, when multi-zone modeling is selected for massive stocks. | New et al. (2021), *Autotuning and Scale of AutoBEM*. |
| **URBANopt / OpenStudio** | OpenStudio `urban-geometry-creation-zoning` measure. Straight-skeleton core/perimeter zoning (default 15 ft / 4.57 m). Also supports double-loaded corridor templates. | Yes, with core/perimeter and custom double-loaded corridor layouts. | NREL URBANopt Geometry and Zoning documentation (2022). |
| **UMI / shoeboxer** | Auto-generates multi-zone models by dividing building volumes into storeys and then auto-generating core and perimeter zones (default depth is 2x floor-to-floor height $\approx$ 6-7 m). | Yes, UMI applies core/perimeter zoning to residential templates. | sustainabledesignlab/umi; Reinhart et al. (2013). |
| **City Energy Analyst (CEA)** | GIS footprint polygons. Core/perimeter zoning template. The perimeter depth is configurable (default is 4 m or 15 ft). | Yes, CEA applies the same zoning structure to residential buildings. | ETH Zurich, CEA documentation (2018), Schlueter et al. |
| **geomeppy** | Native core/perimeter zoning. Inward offset of the footprint; perimeter is split into $N$ segments (one per exterior wall edge). Default perimeter depth is 3.0 m. | Yes, applies this to any building block passed to it. | geomeppy source code on GitHub (`geom/core_perimeter.py`). |

---

## 2. PART C — SYNTHESIS (RULE BLOCK + VERDICT)

### 1. Minimum Sourced Rule Set for `zone`-mode Zoning
* **Perimeter Depth:** Locked to **4.57 m (15 ft)** based on ASHRAE Standard 90.1-2019 Normative Appendix G Table G3.1 (Item 8a).
* **Perimeter Zone Segmentation:** The perimeter annulus is split by facade segment (native geomeppy behavior), resulting in $N$ perimeter zones for a footprint with $N$ vertices. This preserves the exact orientation of each facade wall, which is critical for solar distribution.
* **Core-Existence Test:** A core zone is created only if the inward-buffered polygon is non-empty and has an area $A_{\text{core}} \ge 10.0\text{ m}^2$. If it fails this test, the zoning strategy for that floor falls back to `one_zone_per_floor`.
* **The Residential/Apartment Rule:** Residential archetypes (`MidriseApartment` and `HighriseApartment`) must **not** be modeled with residential occupant loads in the core. Slicing a residential footprint into core/perimeter creates a large windowless core zone that is physically unrealistic (violating municipal codes requiring natural light/ventilation in habitable rooms). 
  * **Remedy:** We establish the **Core-as-Corridor** rule. The geometry generator still uses geomeppy's core/perimeter split (to avoid donut geometry generation issues), but the results parser and load builder map the core zone to a **Corridor** template (with low internal loads, zero design occupancy, and different ventilation rates) while mapping the perimeter zones to the **Apartment** template.

### 2. Accept-or-Revise Verdict on OpenUBEM's Current Implementation
* **Verdict: REVISE (Minor).**
* **Rationale:** The current implementation (`openubem/geometry/zoning.py`) successfully handles degenerate footprints (narrow slices, courtyards) and matches standard UBEM precedent (CityBES, URBANopt). However, forcing all residential classes (`MidriseApartment`, `HighriseApartment`) to `one_zone_per_floor` misses orientation-dependent solar gains and envelope conduction along the facade. 
* **Smallest Change Required:**
  1. Remove `MidriseApartment` and `HighriseApartment` from the `_ONE_PER_FLOOR` exclusion list in `openubem/geometry/zoning.py` so they undergo `perimeter_core` zoning.
  2. Implement the **Core-as-Corridor** load mapping in `openubem/idf/builder.py` (or load scheduler): if the archetype is residential and the zone is a core zone (`_core` suffix), assign it the archetype's Corridor/Common loads and schedules, rather than the Apartment dwelling unit loads.

---

## 3. THE RESIDENTIAL AND TALL BUILDING ZONING CHALLENGE

In building energy modeling, multifamily residential and office zones have fundamentally different spatial requirements:

### The Residential Egress & Lighting Constraint
Under building codes (such as the International Building Code §1205), all habitable residential spaces (living rooms, bedrooms) must have direct access to natural light and ventilation (exterior windows). Consequently, multifamily apartments are arranged as single- or double-loaded corridors where every apartment unit is situated along the perimeter. 
* **The Core in Residential:** The only interior (core) spaces in a typical apartment building are corridors, stairwells, elevators, and utility shafts.
* **The E+ Core Zone Issue:** If a generic core/perimeter algorithm is applied to a residential building, and the core zone is assigned the same loads (people, lighting, appliances) as the perimeter units, the model will simulate high internal gains in a windowless space. This leads to artificial cooling loads and incorrect HVAC sizing.

### The Tall and SuperTall Stacking Effect
Tall buildings (`TallBuilding`, `SuperTallBuilding`) require core/perimeter zoning to capture:
1. **Solar Gradients:** Solar radiation varies significantly with height due to surrounding urban shading.
2. **Wind and Infiltration:** Wind pressure increases exponentially with height (wind speed profile), causing higher infiltration rates at upper floors.
3. **Core vs. Perimeter Loading:** In tall commercial towers, core zones house elevator shafts, mechanical ducts, and restrooms, which have distinct load profiles from the glass-facade offices.
* **UBEM Precedent:** Tools like UMI and CityBES model tall buildings by stacking core/perimeter slices and applying floor multipliers (e.g. simulating bottom, middle, and top floors, then multiplying middle floors).

---

## 4. CONFIDENCE AND CAVEATS

> [!WARNING]
> **The Courtyard Footprint Donut Geometry Pitfall**
> When a building footprint contains an interior courtyard (donut shape), geomeppy's `add_block(zoning="core/perim")` creates a donut-shaped core zone. When stacking multiple floors, EnergyPlus's `intersect_match` struggles to pair the ceiling of one donut core with the floor of the storey above due to vertex-ordering and vertex-count mismatches, resulting in a fatal simulation crash. Reverting to `one_zone_per_floor` for footprints with interior holes is a mandatory stability guard that must be preserved.

> [!IMPORTANT]
> **Warehouse and Large Single-Volume Spaces**
> Warehouses (`Warehouse`) and strip malls (`RetailStripmall`) should never undergo core/perimeter zoning. Doing so creates artificial internal walls and partition boundaries inside what is physically a single, open thermal volume (or a heated-only bulk storage space). This introduces unnecessary inter-zone conduction calculations and can cause HVAC control loop instability in the simulation engine.

---

## 5. REFERENCES

1. ASHRAE. (2019). *ANSI/ASHRAE/IES Standard 90.1-2019 — Energy Standard for Buildings Except Low-Rise Residential Buildings*. American Society of Heating, Refrigerating and Air-Conditioning Engineers. Atlanta, GA. Normative Appendix G, Table G3.1.
2. Hong, T., Chen, Y., Lee, S. H., & Ye, K. (2018). *CityBES: A Web-based Platform for City-scale Building Energy Efficiency*. Energy and Buildings, 158, 979-995. [https://doi.org/10.1016/j.enbuild.2017.10.021](https://doi.org/10.1016/j.enbuild.2017.10.021)
3. PNNL. (2022). *Commercial Prototype Building Models*. Pacific Northwest National Laboratory & U.S. Department of Energy. Building Energy Codes Program. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
4. Reinhart, C. F., Dogan, T., Ibarra, D., & Samuelson, H. W. (2013). *Umi — An Urban Modeling Interface for Rhinoceros*. Proceedings of BS2013: 13th Conference of International Building Performance Simulation Association, Chambéry, France.
5. geomeppy on GitHub. *Core/Perimeter Zoning Engine*. [https://github.com/jamiebull1/geomeppy/blob/master/geomeppy/geom/core_perimeter.py](https://github.com/jamiebull1/geomeppy/blob/master/geomeppy/geom/core_perimeter.py)
6. NREL. (2022). *URBANopt Software Development Kit (SDK) documentation*. National Renewable Energy Laboratory. [https://docs.urbanopt.net/](https://docs.urbanopt.net/)
