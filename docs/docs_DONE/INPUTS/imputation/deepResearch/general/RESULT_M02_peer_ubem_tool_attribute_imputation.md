# RESULT_M02 — PEER UBEM TOOL Attribute Imputation

This document inventories and compares how established Urban Building Energy Modeling (UBEM) and GIS-to-BEM tools impute or substitute missing building attributes when the primary spatial data source (e.g., OpenStreetMap) is silent. It benchmarks OpenUBEM's current ad-hoc mechanisms against seven peer tools and workflows: **UMI**, **City Energy Analyst (CEA)**, **CityBES**, **AutoBEM**, **URBANopt**, **TEASER / GEM**, **3DCityDB / CityGML**, and the **İşeri et al. (in-repo)** probabilistic method.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Missing floor-count / height

| Tool | What it substitutes when floor count / height is absent | Default vs. real inference (regression / LiDAR / assessor)? | Provenance recorded? | Source |
|---|---|---|---|---|
| **UMI** | User-supplied height/floors in shapefile or archetype template defaults. GIS importer fails to extrude 2D polygons if height/stories mapping is unconfigured. | **Default** (Requires user definition or pre-assigned template constant; e.g., 3.0 m floor-to-floor height) | No | UMI Docs (2020), Dogan & Reinhart (2013) |
| **CEA** | Assumes a typical floor-to-floor height of `3.0 m` above ground and `3.0 m` below ground if stories are known. If height is completely absent, it can join external LiDAR or assessor data. | **Heuristic Default** (3.0 m per floor) or external GIS join | No | Fonseca et al. (2016), CEA readthedocs ("OSM Importer") |
| **CityBES** | Derives floor count from county assessor records or assumes typical heights (`3.0 m` for residential, `4.0 m` for commercial). If both are absent, it defaults to a flat `1` story. | **Heuristic Default** / Assessor lookup | No | Hong et al. (2016), CityBES Docs (2020) |
| **AutoBEM** | Extracts height from LiDAR (AutoBEM-LiDAR), street-level views using deep learning (AutoBEM-Street), or assessor databases. If all are absent, infers height from 2D footprint area via regression. | **Real Inference** (LiDAR / Computer Vision / Area-Height Regression) | No | New et al. (2018), AutoBEM Docs (2021) |
| **URBANopt/OpenStudio** | Validation schema enforces `number_of_stories` as a required attribute. The workflow fails if stories are missing. Geometry is extruded using default floor heights. | **Schema Requirement** (Tier C fail — no auto-fill without external tool preprocessing) | No | NREL URBANopt Docs, `urbanopt-geojson` schema |
| **TEASER / GEM** | Uses pre-defined archetype class defaults (e.g., a standard residential house has a default number of floors, e.g., 2, and floor height, e.g., 3.0 m). | **Heuristic Default** (archetype class defaults) | No | Remmen et al. (2018), TEASER Docs |
| **3DCityDB / CityGML** | LoD1 creation workflows (e.g., FME, SimStadt) extrude footprint using a flat default (e.g., `9.0 m` or `10.0 m`) or multiply floors by `3.0 m`. | **Heuristic Default** | No | SimStadt Docs (2021) |
| **İşeri et al. (in-repo)** | Not missing in case study (0% missing). Floor counts were obtained directly from the address registry (AIS). | **N/A** (complete local municipality database) | No | İşeri et al. (2026), in-repo paper (Table 2) |
| **OpenUBEM (current)** | `max(1, height_m // 3.5)`; both absent → `1` | Heuristic constant (3.5 m/floor), not inference | Yes — `HEURISTIC_HEIGHT` / `HEURISTIC_DEFAULT` flag | `building_classifier.py:121-127` |

---

### Table 2 — Missing use / function

| Tool | What it substitutes when use/function is absent | Inference method (dominant-use of block, land-use join, ML)? | Provenance recorded? | Source |
|---|---|---|---|---|
| **UMI** | User-assigned mapping. If absent, the GIS importer fails or requires manual template selection in the Rhino UI. | **No inference** (Requires user definition) | No | UMI Docs (2020) |
| **CEA** | Maps to a dominant use class of the district or defaults to a generic default archetype. | **Heuristic Default** / Land-use join | No | Fonseca et al. (2016) |
| **CityBES** | Joins with county assessor classifications or local land-use databases. If absent, requires manual user configuration. | **No inference** (Assessor/land-use join only) | No | Hong et al. (2016) |
| **AutoBEM** | Inferred using satellite image classification (deep learning) or assessor parcel data. | **Real Inference** (ML classifier) | No | New et al. (2018) |
| **URBANopt/OpenStudio** | GeoJSON validation schema enforces `building_type` as a required attribute. Workflow fails if missing. | **Schema Requirement** (Tier C fail) | No | NREL URBANopt Docs |
| **TEASER / GEM** | Fails. The building object must be instantiated with a specific archetype class (e.g., `Office`, `Residential`). | **No inference** (Instantiation constraint) | No | Remmen et al. (2018) |
| **İşeri et al. (in-repo)** | Not missing in case study (0% missing). Obtained from municipality GIS records. | **N/A** (complete data from GIS) | No | İşeri et al. (2026), in-repo paper |
| **OpenUBEM (current)** | `OpenUBEMUnknown` (LOW) or size-bucketed office if `building=yes` | No inference — sentinel + size heuristic | Yes — `FALLBACK_UNKNOWN` / `FALLBACK_SIZE_DEFAULT`, confidence LOW | `building_classifier.py:316-317`, rule 17a |

---

### Table 3 — Missing vintage / `year_built`

| Tool | What it substitutes when construction year is absent | Default value / distribution used | Does missing→oldest, →median, →distribution, or →region-typical? | Source |
|---|---|---|---|---|
| **UMI** | User-assigned template. If absent, must be manually assigned. | N/A (Requires manual assignment) | N/A (manual) | UMI Docs (2020) |
| **CEA** | Maps to a default construction age period based on neighborhood-typical vintages. | Neighborhood construction era (typical period) | missing → **region-typical** | Fonseca et al. (2016) |
| **CityBES** | Assessor construction year or California Title 24 / ASHRAE 90.1 prototype vintage. | Typical vintage of area or code archetype era | missing → **region-typical** | Hong et al. (2016) |
| **AutoBEM** | Assessor vintage or typical construction period of adjacent parcels. | Typical vintage of adjacent parcels / standard default | missing → **region-typical** | New et al. (2018) |
| **URBANopt/OpenStudio** | Schema maps to an optional field, but defaults to the current year if unspecified. | Current year (assumes newest energy code archetype) | missing → **newest** | `building_properties.json` schema |
| **TEASER / GEM** | Defaults to `None` and fails to calculate dependent U-values during statistical enrichment unless provided. | N/A (enrichment fails without construction year) | missing → **fails** | Remmen et al. (2018) |
| **İşeri et al. (in-repo)** | Not missing in case study (0% missing). Obtained from municipality GIS records. | N/A (complete data from GIS) | N/A | İşeri et al. (2026), in-repo paper |
| **OpenUBEM (current)** | `DOERefPre1980` (oldest tier, U-factors ×1.6) | Single deterministic oldest-vintage bin | missing → **oldest** | `construction_sets.py:44,129-139` |

---

### Table 4 — Missing semantic parameters (U-value, load, COP) & the imputation *style*

| Tool | How it fills a missing envelope/load/system parameter | Deterministic archetype value, distribution sample, or ML? | Is uncertainty propagated (single vs. multiple imputation)? | Source |
|---|---|---|---|---|
| **UMI** | Assigns parameters directly from the XML/JSON template library matching the building's type/vintage. | **Deterministic archetype value** | Single imputation (No uncertainty propagated) | UMI Docs (2020), Dogan & Reinhart (2013) |
| **CEA** | Assigns defaults from region-specific XML databases (`CONSTRUCTION_STANDARDS.xlsx`). | **Deterministic archetype value** | Single imputation (No uncertainty propagated) | Fonseca et al. (2016) |
| **CityBES** | Assigns ASHRAE/Title 24 prototype inputs based on building classification and vintage. | **Deterministic archetype value** | Single imputation (No uncertainty propagated) | Hong et al. (2016) |
| **TEASER / GEM** | Enriches from the German national building database (TABULA/EPISCOPE) or AixLib database. | **Deterministic archetype value** | Single imputation (No uncertainty propagated) | Remmen et al. (2018) |
| **İşeri et al. (in-repo)** | WWR, U-values, and occupant density are sampled from estimated KDE distributions. SHGC, COP, and loads are sampled from parametric Uniform distributions. | **Distribution sample** (KDE-based NPDE and Uniform-based PDE) | Probabilistic sampling (draws a single representative building stock dataset per run; multiple imputation mentioned but EUI uncertainty not propagated to parallel simulations) | İşeri et al. (2026), in-repo paper |
| **OpenUBEM (current)** | KDE-fill (envelope) from sibling climate zones; `.get() or default` (HVAC/DHW — silent) | **Distribution sample** (envelope KDE) / **Deterministic default** (HVAC/DHW) | Single imputation (No uncertainty propagated) | `construction_sets.py:171-219`; `idf/hvac.py`, `idf/dhw.py` |

---

## 2. PART C — SYNTHESIS (PER-INPUT VERDICT)

### Input 1: Floor-count / Height
*   **Comparison**: OpenUBEM's current handling (`max(1, height_m // 3.5)` heuristic or defaulting to `1`) is **looser than or in line with** the majority of peer tools. UMI, CEA, CityBES, TEASER, and SimStadt all rely on similar flat heuristic constants (mostly `3.0 m` or `3.5 m` floor-to-floor heights). However, AutoBEM is significantly more rigorous, utilizing deep learning to extract heights from street-level imagery and LiDAR, or regressing height from footprint area.
*   **Most-Cited Upgrade**: Derive building height or floor count via a **footprint-area-to-height regression model** or **spatial join with external elevation datasets (LiDAR/DSM)**.
*   **Uncertainty Propagation**: No peer tool (except the İşeri in-repo paper, which uses local master plans) propagates height uncertainty. All other tools use deterministic single-imputation defaults.

### Input 2: Building Use / Function
*   **Comparison**: OpenUBEM's current fallback (`OpenUBEMUnknown` or size-bucketed office guess) is **more permissive** than several peer tools (UMI, TEASER, URBANopt), which fail validation or execution (Tier C) if building function is unmapped. It is **cruder** than AutoBEM, which uses automated satellite/aerial image classifiers (deep learning) to predict use.
*   **Most-Cited Upgrade**: Implement a **spatial parcel-land-use database join** (similar to CityBES/CEA) or train a **GNN / spatial-neighbor classification model** (exploiting the fact that adjacent buildings share functions).
*   **Uncertainty Propagation**: No peer tool propagates use uncertainty. They all utilize single-imputation archetype assignment.

### Input 3: Vintage / Year Built
*   **Comparison**: OpenUBEM's default to the oldest vintage tier (`DOERefPre1980` with U-factors scaled ×1.6) is **physically conservative** (representing the worst-case thermal envelope) but **cruder** than peer tools. CEA, CityBES, and AutoBEM map missing vintage to the **region-typical / neighborhood-median construction era**. In contrast, URBANopt defaults to the *current year* (assigning the newest, most efficient code), which risks underestimating energy demand. TEASER fails entirely if the construction year is missing.
*   **Most-Cited Upgrade**: Implement a **spatial neighborhood-majority / median-vintage join** (e.g., using a 500m radius or district-typical age) rather than a flat national pre-1980 default.
*   **Uncertainty Propagation**: All peer tools utilize single imputation for vintage; none carry vintage uncertainty forward to parallel energy simulations.

### Input 4: Envelope and Operational Semantic Parameters (U-values, HVAC COPs, Internal Loads)
*   **Comparison**: OpenUBEM is **more rigorous** than almost all peer tools for envelope properties because it implements a distribution-based **KDE-fill** (sampling U-values from sibling climate zones). Peer tools (UMI, CEA, CityBES, TEASER) map these parameters to deterministic, static archetype database lookups. However, OpenUBEM's HVAC parameter defaults (`cooling_cop = 3.0`, `heating_efficiency = 0.8`) are **cruder and silent** (Tier B defaults with no provenance).
*   **Most-Cited Upgrade**: Transition the silent Tier-B HVAC defaults to **probabilistic parametric distributions (PDE)** (such as Uniform distributions for COP and loads, as documented in the in-repo paper) or map them to ASHRAE prototype standards while **enforcing mandatory provenance flags**.
*   **Uncertainty Propagation**: Only the **İşeri et al. (in-repo)** paper implements probabilistic sampling from estimated KDE and Uniform PDFs to maintain building stock heterogeneity, representing a major conceptual precedent for OpenUBEM. However, it does not propagate this uncertainty into multiple parallel EUI simulations (true multiple imputation).

### Highest-Value Imputation Target for OpenUBEM
**OpenUBEM is furthest behind peer practice in its handling of vintage (`year_built`).**
While peer tools infer region-typical vintages from local assessor data or adjacent building age distributions, OpenUBEM assigns the oldest tier (`DOERefPre1980`), which heavily biases EUI predictions upwards (U-factors scaled ×1.6). Transitioning from a flat oldest-vintage default to a **spatial neighborhood-typical / district-median vintage join** is the highest-value, lowest-cost upgrade for the upcoming implementation plan.

---

## 3. CONFIDENCE AND CAVEATS

The imputation behavior of **3DCityDB / CityGML workflows** is the least documented and most uncertain. Because 3DCityDB is a storage schema rather than an execution pipeline, actual imputation behavior is entirely dependent on the specific user-developed converter (e.g., SimStadt, FME scripts, or custom converters). These workflows frequently utilize ad-hoc, undocumented Python/SQL scripts to hardcode elevation offsets or default values, leaving a significant documentation gap in peer literature.

---

## 4. REFERENCE LIST

1. **UMI**: Dogan, T. & Reinhart, C. F. (2013). *umi - An urban modeling interface for single building energy, neighborhood daylighting and district-scale walkability evaluations*. 13th International Conference of IBPSA - Building Simulation 2013, BS 2013. [Link](http://www.ibpsa.org/proceedings/BS2013/p_1400.pdf)
2. **City Energy Analyst (CEA)**: Fonseca, J. A., Nguyen, T.-A., Schlueter, A., & Pinheiro, F. (2016). *City Energy Analyst (CEA): An open-source computational framework for the optimization of smart energy systems in districts*. Resources, Conservation and Recycling, 115, 15-32. [DOI: 10.1016/j.resconrec.2016.08.018](https://doi.org/10.1016/j.resconrec.2016.08.018)
3. **CityBES**: Hong, T., Chen, Y., Lee, S. H., & Piette, M. A. (2016). *CityBES: A Web-based Platform for City-Scale Building Energy Modeling*. Lawrence Berkeley National Laboratory. LBNL-1005475. [Link](https://citybes.lbl.gov/)
4. **AutoBEM**: New, J. R., Adams, M., Im, P., & Garrison, E. (2018). *Automatic Building Energy Modeling (AutoBEM) from satellite imagery, LiDAR, and assessor data*. Oak Ridge National Laboratory. [Link](https://www.ornl.gov/)
5. **URBANopt**: NREL. (2021). *URBANopt Schema and GeoJSON Gem Documentation*. National Renewable Energy Laboratory. [Link](https://github.com/urbanopt/urbanopt-geojson)
6. **TEASER**: Remmen, P., Lauster, M., Spitthof, J., Fuchs, M., & Müller, D. (2018). *TEASER: an open-source Python package for statistical enrichment of building data sets*. Journal of Building Performance Simulation, 11(2), 198-217. [DOI: 10.1080/19401493.2017.1328960](https://doi.org/10.1080/19401493.2017.1328960)
7. **İşeri et al. (in-repo)**: İşeri, O. K., et al. (2026). *A Method for Zone-level Urban Building Energy Modeling in Data-scarce Built Environments*. (In-repo manuscript, `docs/docs_ACTIVE/input/imputation/resources/`).
