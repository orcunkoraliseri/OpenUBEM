# RESULT_I01_osm_tag_to_use_class_mapping — OSM TAG → USE-CLASS mapping

This report documents the methods-comparison analysis between OpenUBEM and established urban building energy modeling (UBEM) tools, GIS building-classification methodologies, and crowdsourced geospatial literature. The focus is specifically on the first stage of classification: how raw attribute tags (primarily OpenStreetMap attributes or equivalent land-use codes) are grouped into coarse use-classes.

---

## 1. REQUIRED COMPARISON TABLES

### Table 1 — Use-class taxonomy per tool/source

| Tool / source | # of use-classes / building-type buckets at the coarse level | Bucket names | Real footprint-tag-driven or attribute-table-driven? | Source |
|---|---|---|---|---|
| **OpenUBEM (current)** | 6 | residential, commercial, industrial, institutional, mixed, unknown | Tag-driven (OSM `building=`, `amenity=`, `shop=`, `office=`) | `osm_to_use_class.json` |
| **URBANopt / OpenStudio** | 28 | Single-Family Detached, Single-Family Attached, Multifamily, Single-Family, Multifamily (2 to 4 units), Multifamily (5 or more units), Vacant, Office, Laboratory, Nonrefrigerated warehouse, Food sales, Public order and safety, Outpatient health care, Refrigerated warehouse, Religious worship, Public assembly, Education, Food service, Inpatient health care, Nursing, Lodging, Strip shopping mall, Enclosed mall, Retail other than mall, Service, Mixed use, Uncovered Parking, Covered Parking | Attribute-table-driven (via GeoJSON `building_type` attribute) | URBANopt Schema `building_properties.json` in `urbanopt-geojson-gem` |
| **CityBES** | ~15 | SmallOffice, MediumOffice, LargeOffice, StandaloneRetail, StripMall, PrimarySchool, SecondarySchool, Outpatient, Hospital, SmallHotel, LargeHotel, Warehouse, Supermarket, FullServiceRestaurant, QuickServiceRestaurant | Attribute-table-driven (California county assessor Land Use Codes mapped to CBECS types) | LBNL CityBES Technical Documentation (Hong et al., 2016) |
| **AutoBEM** | ~16 | LargeOffice, MediumOffice, SmallOffice, Warehouse, StandaloneRetail, StripMall, PrimarySchool, SecondarySchool, Outpatient, Hospital, SmallHotel, LargeHotel, QuickServiceRestaurant, FullServiceRestaurant, Supermarket, MidriseApartment, HighriseApartment, Single-Family (detached/attached) | Hybrid (combines footprint geometry + county tax assessor records + NAICS codes) | ORNL AutoBEM Methodology (New et al., 2018) |
| **UMI** | 9 | Residential Single Family, Residential Multi Family, Office, Retail, Food, School, Hotel, Hospital, Warehouse | Attribute-table-driven (user-assigned Rhino attributes mapped to standard template libraries) | MIT Sustainable Design Lab (Cerezo, Dogan & Reinhart, 2014) |
| **City Energy Analyst (CEA)** | 14 | MULTI_RES, SINGLE_RES, OFFICE, RETAIL, FOODSTORE, RESTAURANT, HOTEL, SCHOOL, INDUSTRIAL, GYM, HOSPITAL, PARKING, SERVERROOM, LABORATORY | Attribute-table-driven (occupancy shares defined per building in `typology.dbf`) | ETH Zurich Architecture & Building Systems (Fonseca et al., 2016) |
| **OSM-classification literature** (Fill et al. GNN Model) | 9 | Residential, Retail, Office, Public (Institutional/Civic/Worship/Health), Industrial, Agricultural, Unclassified/Other (further sub-divided into apartments, detached, semi-detached, terraced) | Tag-driven (OSM `building`, `amenity`, `shop`, `office` tags) + spatial context features | Fill, Eichelbeck & Ebner (2024) "Predicting building types and functions at transnational scale" |

---

### Table 2 — Tag priority / conflict-resolution rule per source

| Source | Does a function/use tag (amenity, shop, office) outrank a generic structural tag (building=*)? | What happens when two tags disagree | OpenUBEM's current rule (for comparison) | Source |
|---|---|---|---|---|
| **URBANopt / OpenStudio** | N/A (GeoJSON has a single unified `building_type` attribute) | N/A (Disagreements must be resolved before model export. Supports `Mixed use` category by defining area percentage splits). | — | URBANopt Schema docs |
| **CityBES** | Yes (assessor land-use and occupancy data outrank basic physical structural labels) | Priority is given to the primary property assessor code; multi-occupant parcels are resolved using area-weighted primary activities. | — | Hong et al. (2016) |
| **AutoBEM** | Yes (NAICS business classification codes or tax assessor property classifications strictly outrank footprint-derived shapes) | NAICS codes are treated as highest priority, followed by tax assessor property codes. Footprint shapes are used only for geometric mapping or if database records are empty. | — | New et al. (2018) |
| **UMI** | Yes (template library categories represent active thermal/operational occupancy, not structural style) | No automated resolution; modelers must manually map geometry layers or pre-resolve attributes in GIS. | — | Cerezo et al. (2014) |
| **CEA** | Yes (occupancy shares in `typology.dbf` dictate simulation; physical construction code is a separate parameter) | Mixed use is handled natively by simulating proportional energy loads across up to three distinct occupancy fractions (e.g., `use_type1r`, `use_type2r`). | — | Fonseca et al. (2016) |
| **OpenUBEM (current)** | Symmetric — both must agree or row becomes `mixed` (score 0.5) | `mixed`; re-routed via dominant-tag rule at ≥0.60 score, else defaults to `MidriseApartment`. | — | `building_classifier.py` `_normalise_use_class` |

---

### Table 3 — Missing / ambiguous tag handling

| Source | Fallback class when no usable tag exists | Reported "unclassified"/"unknown" rate (if published) | Source |
|---|---|---|---|
| **URBANopt / OpenStudio** | Validation fails (building_type is required). Simulation mappers typically apply a user-configured default. | N/A (unclassifiable buildings cannot be exported) | URBANopt Schema validation docs |
| **CityBES** | Defaults to `MediumOffice` (or `SmallOffice` if area < 500 m²) in commercial zones; defaults to residential typologies in residential zones. | Low (<5%) because municipal parcel-level assessor records are legally required to carry a property tax code. | Hong et al. (2016) |
| **AutoBEM** | Infers building type using a Random Forest classifier trained on building height, footprint area, perimeter, and spatial density. | ~10-15% of records initially had missing/unclassifiable assessor tags; all were imputed using GIs/ML context. | New et al. (2018) |
| **UMI** | Buildings without an assigned template are excluded from simulation. | 0% in simulated models (simulation fails or skips buildings without valid templates). | Cerezo et al. (2014) |
| **CEA** | Defaults to `MULTI_RES` (residential) or `OFFICE` based on the dominant zone typology. | Not reported (defaults are silently applied during geometry mapping). | CEA `data-helper` ReadTheDocs |
| **OpenUBEM (current)** | `unknown` → cascades to `OpenUBEMUnknown` (LOW confidence) or size-bucketed office default if `building=yes` | GAP — not yet measured at city scale. | `building_classifier.py` |

---

### Table 4 — Reported classification accuracy (if any literature reports it)

| Source | Ground-truth comparison performed? | Reported accuracy / error rate | Confounders noted by the authors | Source |
|---|---|---|---|---|
| **OSM-classification literature** | Yes (GNN model predictions compared against OSM tags and municipal building databases across the EU/UK). | Cohen's Kappa of **0.845** for binary (res/non-res) and **0.755** for 9 classes. | Inconsistencies and regional differences in OSM tagging conventions, class imbalance (residential dominates), and low completeness of height attributes. | Fill, Eichelbeck & Ebner (2024) |
| **AutoBEM (ORNL)** | Yes (compared predicted prototypes against tax assessor records and utility data). | Classification accuracy of **75% to 92%** depending on region and assessor data quality. | Out-of-date tax records, multi-use buildings (e.g. retail on ground floor, office above), and inconsistent county tax schemas. | New et al. (2018) |
| **OSM-classification literature** | Yes (quality assessment comparing global OSM datasets against government cadastres). | Attribute accuracy is **>90%** when tags are populated; however, semantic completeness is low (only 10-20% of buildings have specific usage tags). | Crowdsourced nature of OSM (variable contributor skill), urban-centric contribution bias, and lack of standardized naming validation. | Biljecki, Chow & Lee (2023) |

---

## Part C — Synthesis (assessment of OpenUBEM's current tag map)

Based on the comparison against established UBEM tools and crowdsourced geospatial literature, we evaluate OpenUBEM's current tag-mapping approach across four key areas:

### 1. Use-Class Taxonomy Granularity
OpenUBEM’s **6-class taxonomy** (`residential, commercial, industrial, institutional, mixed, unknown`) is highly consistent with standard GIS classification papers (which typically use 5 to 9 classes) and maps cleanly to downstream physical archetypes. 
*   **Taxonomy Gap:** The primary weakness is lumping all **institutional** buildings (education, health, civic) into a single coarse class. If a building is tagged with a generic institutional label (e.g. `building=institutional`) but lacks specific functional tags (e.g. `amenity=school`), it defaults to the `Courthouse` archetype (Rule 14 in `building_classifier.py`). In contrast, peer tools like UMI and CityBES split education ("School") from healthcare ("Hospital") early in the mapping process to prevent routing generic institutional buildings to a civic/office-like default, as their thermal schedules and ventilation loads differ dramatically.

### 2. Symmetric Conflict Resolution Rule
OpenUBEM's symmetric conflict rule (requiring both `function_tag` and `building_tag` to agree, or else assigning `mixed`) is a **significant deviation** from peer tools and literature:
*   **Precedent:** In both machine learning studies (e.g., Fill et al., 2024) and UBEM frameworks (e.g., CEA, AutoBEM), **specific function tags (`amenity`, `shop`, `office`) strictly override generic structural tags (`building=house` or `building=commercial`)**. 
*   **Rationale:** The active socioeconomic use of a building dictates its internal loads and operating schedules, regardless of its structural design. For example, a doctor's clinic operating inside a converted detached house (`building=house` + `amenity=clinic`) should be simulated as an `Outpatient` facility, not as a `mixed` or `residential` building. 
*   **Risk:** OpenUBEM's symmetric rule forces these cases into the `mixed` category (score 0.5). If they fall below the dominant-tag threshold, they default to `MidriseApartment` (Rule 16). This causes systematic misclassification of commercial and institutional facilities operating in residential-style structures.

### 3. Specific Missing OSM Tags (Actionable Changes)
The current ~60-entry `tag_to_use_class` map in `osm_to_use_class.json` misses several highly common OSM building and amenity tags. We recommend adding the following tags to improve coverage and prevent buildings from being incorrectly routed to `unknown` → `OpenUBEMUnknown` (LOW confidence):

| Missing OSM Tag | Proposed Use-Class | Justification | Source |
|---|---|---|---|
| `building=duplex` | **residential** | Standard two-family residential housing. | OSM Wiki / standard practice |
| `building=semidetached` | **residential** | Extremely common abbreviation for `semidetached_house` used by contributors. | OSM Wiki / Biljecki et al. (2023) |
| `building=terraced_house` | **residential** | Alternate tag for `terrace` frequently used in European datasets. | OSM Wiki |
| `building=cabin` | **residential** | Small residential structures (cabins, cottages). | OSM Wiki / Fill et al. (2024) |
| `building=static_caravan` | **residential** | Residential manufactured housing. | OSM Wiki |
| `building=houseboat` | **residential** | Floating residential units. | OSM Wiki |
| `building=service` | **commercial** | Service buildings (e.g., administrative outbuildings, workshops). | OSM Wiki / Biljecki et al. (2023) |
| `building=depot` | **industrial** | Storage, transport depots, or light industrial usage. | OSM Wiki / Fill et al. (2024) |
| `building=barn` | **industrial** | Agricultural storage (closely matches industrial/warehouse loads). | OSM Wiki / Fill et al. (2024) |
| `building=stable` | **industrial** | Agricultural animal housing (similar to industrial/barn thermal profiles). | OSM Wiki |
| `building=cowshed` | **industrial** | Agricultural facility. | OSM Wiki |
| `building=greenhouse` | **industrial** | Commercial/agricultural greenhouse structures. | OSM Wiki |
| `building=silo` | **industrial** | Storage tower structure. | OSM Wiki |
| `building=storage_tank` | **industrial** | Industrial fuel/water storage structures. | OSM Wiki |
| `building=substation` | **industrial** | Electrical utility substation buildings. | OSM Wiki |
| `amenity=place_of_worship` | **institutional** | Standard parent tag for religious structures (churches, temples, mosques). | OSM Wiki / Fill et al. (2024) |
| `amenity=townhall` | **institutional** | Civic government administrative headquarters. | OSM Wiki / Fill et al. (2024) |
| `amenity=community_centre` | **institutional** | Public assembly and civic center. | OSM Wiki / Fill et al. (2024) |
| `amenity=post_office` | **commercial** | Retail postal and commercial service facility. | OSM Wiki |
| `amenity=theatre` | **commercial** | Public assembly / commercial entertainment venue. | OSM Wiki |
| `shop=department_store` | **commercial** | Large retail department store. | OSM Wiki |
| `shop=mall` | **commercial** | Large enclosed retail shopping mall. | OSM Wiki |
| `office=company` | **commercial** | Private corporate office space. | OSM Wiki |
| `office=government` | **institutional** | Government administrative office space. | OSM Wiki / Fill et al. (2024) |
| `office=educational` | **institutional** | Administrative offices of schools or universities. | OSM Wiki |

### 4. Fallback / Unknown Handling
OpenUBEM's fallback strategy (defaulting generic `building=yes` to size-bucketed offices, and completely untagged buildings to `OpenUBEMUnknown`) is much more conservative than the "silent defaults" applied by CityBES (defaulting to dominant regional types) or CEA (defaulting to MULTI_RES/OFFICE).
*   **Assessment:** OpenUBEM's approach is structurally superior for energy audit traceability because it explicitly marks these buildings as `LOW` confidence and records the `OpenUBEMUnknown` sentinel. However, to minimize the rate of untagged structures dropping into `OpenUBEMUnknown` at scale, the pipeline should incorporate a spatial default (e.g. referencing local zoning layers, similar to CityBES) rather than relying solely on OSM tags.

---

## 2. CONFIDENCE AND CAVEATS

*   **Sourcing Strength:** The taxonomic lists and schema enums for URBANopt, CityBES, and CEA are extracted directly from their respective source repositories, documentation manuals, or peer-reviewed primary publications, representing high sourcing confidence.
*   **Comparison Weakness:** The comparison with UMI and URBANopt is necessarily approximate. Both tools do not natively classify raw OSM tags; they are downstream engines that expect pre-classified attributes (GeoJSON or Rhino layer attributes). The translation comparison represents how their standard template sets categorize the same physical building stock.
*   **OSM Literature Generalizability:** While the studies by Fill et al. (2024) and Biljecki et al. (2023) represent state-of-the-art global and European classification standards, local tagging completeness and contributor patterns in the US (where OpenUBEM is primarily applied) can differ, which may introduce minor regional bias.

---

## 3. REFERENCE LIST

1.  **URBANopt / OpenStudio:** NREL (2023). *URBANopt GeoJSON Gem Schema Specifications*. Available at: [urbanopt-geojson-gem GitHub](https://github.com/urbanopt/urbanopt-geojson-gem).
2.  **CityBES:** Hong, T., Chen, Y., Lee, S. H. & Piette, M. A. (2016). *CityBES: A Web-based Platform for City-Scale Building Energy Simulation*. Lawrence Berkeley National Laboratory (LBNL), Energy Technologies Area. Available at: [LBNL Publications](https://simulationresearch.lbl.gov/publications/files/lbl-1005743.pdf).
3.  **AutoBEM:** New, J. R., Adams, E. E., Garrison, A. L., et al. (2018). *AutoBEM: Automatic Building Energy Modeling at National Scale*. Oak Ridge National Laboratory (ORNL). Available at: [ORNL Research Repository](https://www.ornl.gov/publication/autobem-automatic-building-energy-modeling).
4.  **UMI:** Cerezo, C., Dogan, T. & Reinhart, C. F. (2014). *Towards standardized building properties template files for early design energy model generation*. MIT Sustainable Design Lab. Available at: [MIT SDL Publications](https://sustainabledesignlab.mit.edu/publications/Cerezo_TowardsStandardizedBuildingProperties.pdf).
5.  **City Energy Analyst (CEA):** Fonseca, J. A., Nguyen, T. A., Schlueter, A., et al. (2016). *City Energy Analyst (CEA): An open-source framework for building energy simulation in districts*. ETH Zurich. Available at: [CEA ReadTheDocs](https://city-energy-analyst.readthedocs.io/).
6.  **Transnational OSM GNN Study:** Fill, J., Eichelbeck, M. & Ebner, M. (2024). *Predicting building types and functions at transnational scale*. IEEE Access (Preprint available on arXiv: [arXiv:2309.07160](https://arxiv.org/abs/2309.07160)).
7.  **OSM Global Assessment:** Biljecki, F., Chow, Y. S. & Lee, K. (2023). *Quality of crowdsourced geospatial building information: A global assessment of OpenStreetMap attributes*. Building and Environment, Vol 243. DOI: [10.1016/j.buildenv.2023.110685](https://doi.org/10.1016/j.buildenv.2023.110685).
8.  **OpenStreetMap Wiki:** *Key:building* and *Key:amenity* tagging guides. Available at: [OSM Wiki Key:building](https://wiki.openstreetmap.org/wiki/Key:building).
