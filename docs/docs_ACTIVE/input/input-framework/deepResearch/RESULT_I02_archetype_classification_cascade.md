# RESULT I02 — Archetype Classification Cascade (Size and Level Threshold Validation)

This report validates OpenUBEM's archetype classification thresholds against the intended size ranges of the U.S. Department of Energy (DOE) and Pacific Northwest National Laboratory (PNNL) Commercial Prototype Building Models, ASHRAE 90.1, and peer Urban Building Energy Modeling (UBEM) tools.

---

## REQUIRED OUTPUT TABLES

### Table 1 — DOE/PNNL prototype's own intended size range, per archetype

All unit conversions use the factor $1\text{ ft}^2 \approx 0.092903\text{ m}^2$.

| Archetype | DOE/PNNL prototype's documented floor area / size range | Documented floor-count range | Source (TSD name + page/section) |
|---|---|---|---|
| **SmallOffice** | 5,502 ft² (~511 m²) | 1 story | Deru et al. (2011), Section 3.1.1, Table 3-1, p. 9. |
| **MediumOffice** | 53,628 ft² (~4,982 m²) | 3 stories | Deru et al. (2011), Section 3.1.1, Table 3-1, p. 9. |
| **LargeOffice** | 498,588 ft² (~46,320 m²) [Includes 38,353 ft² basement] | 12 stories above grade + 1 basement (13 stories total) | Deru et al. (2011), Section 3.1.1, Table 3-1, p. 9. |
| **PrimarySchool** | 73,960 ft² (~6,871 m²) | 1 story | Deru et al. (2011), Section 3.1.3, Table 3-1, p. 9. |
| **SecondarySchool** | 210,887 ft² (~19,592 m²) | 2 stories | Deru et al. (2011), Section 3.1.3, Table 3-1, p. 9. |
| **MidriseApartment** | 33,740 ft² (~3,135 m²) | 4 stories | Deru et al. (2011), Section 3.1.15, Table 3-1, p. 9. |
| **HighriseApartment** | 84,360 ft² (~7,837 m²) | 10 stories | PNNL (2014) Report PNNL-23269: "Enhancements to ASHRAE Standard 90.1 Prototype Building Models", Section 3.2.1, Table 3. |
| **SmallHotel** | 43,200 ft² (~4,013 m²) | 4 stories | Deru et al. (2011), Section 3.1.13, Table 3-1, p. 9. |
| **LargeHotel** | 122,120 ft² (~11,345 m²) | 6 stories | Deru et al. (2011), Section 3.1.13, Table 3-1, p. 9. |
| **SmallDataCenterHighITE / LargeDataCenterHighITE** | Small: 600 ft² (~55.7 m²)<br>Large: 6,000 ft² (~557.4 m²) | 1 story (both) | Sun et al. (2021), "Prototype energy models for data centers", Energy and Buildings, Vol. 231, Table 2. (LBNL-2001382). |

---

### Table 2 — How each peer tool selects among size-tiered archetypes

| Tool | Attribute used to pick among variants | Cut-points used (if published) | Source |
|---|---|---|---|
| **URBANopt / OpenStudio** | User-specified `building_type` property in the GeoJSON FeatureFile. No automated classification is performed by default. | *No automated thresholds.* Relies on explicit user inputs or mappers mapping to specific types. | NREL (2020) "URBANopt Schema Documentation: Feature Properties" (https://docs.urbanopt.net/geojson-gem/building_properties.json). |
| **CityBES** | Gross Floor Area (GFA) and stories from GIS shapefiles, CityGML, or Tax Assessor databases. | **Offices:**<br>- Small Office: GFA < 25,000 ft² (~2,322 m²) AND Stories ≤ 3<br>- Medium Office: GFA 25,000–100,000 ft² (2,322–9,290 m²) AND Stories ≤ 5 (or GFA < 2,322 m² with Stories ∈ {4, 5})<br>- Large Office: GFA > 100,000 ft² (~9,290 m²) OR Stories ≥ 6<br>**Residential/Lodging:** Mapped directly via assessor land-use classification codes. | Hong et al. (2015). "Commercial Building Energy Saver: An energy retrofit analysis toolkit." Energy and Buildings, 100, 290-302. |
| **AutoBEM** | Inferred from building footprint area, LiDAR height (stories), and tax assessor land use codes. | Assigns buildings to the nearest matching DOE commercial reference building archetype (e.g., matching 12 stories to Large Office, 3 stories to Medium Office, 1 story to Small Office). No intermediate floor area bins are used by default; relies on geometric closeness to the prototype profiles. | New et al. (2021). "Automatic Building Energy Modeling (AutoBEM) software suite." Oak Ridge National Laboratory (ORNL). |
| **UMI** | User-assigned template from a template library (e.g., Boston Template Library) within the Rhino CAD environment. | *No automated thresholds.* Relies entirely on manual selection by the modeler. | MIT Sustainable Design Lab (2019). "UMI: Urban Modeling Interface documentation." |
| **CEA** | Multi-use occupancy percentage vectors (e.g. `building_use` contains `%` of office, residential, retail). | *No discrete thresholds.* Internal loads and thermal properties are continuously scaled based on the mix of uses rather than selecting a single discrete size-tiered archetype. | Fonseca et al. (2016). "City Energy Analyst (CEA): Integrated framework for analysis of energy systems." readthedocs.io. |

---

### Table 3 — OpenUBEM's six cut-points vs. precedent

| Decision | OpenUBEM's current cut-point | Precedent value found (Table 1/2) | Match / looser / stricter / GAP | Source |
|---|---|---|---|---|
| **Super-tall vs. tall** | ≥ 40 vs. 20–39 levels | *No direct precedent.* Large Office tops out at 12 stories. CTBUH defines tall as ≥ 50m (~15 levels), supertall as ≥ 300m (~90 levels). | **GAP** | Council on Tall Buildings and Urban Habitat (CTBUH) Heights Database / DOE Prototypes. |
| **Highrise vs. midrise apartment** | ≥ 9 vs. < 9 levels | Aligns with the 10-story Highrise Apartment prototype and 4-story Midrise Apartment prototype. Multifamily industry defines mid-rise as 4-8 levels and high-rise as ≥9 levels. | **Match** | PNNL (2014) Report PNNL-23269 (Highrise is 10 stories; Midrise is 4 stories). |
| **Large vs. small hotel** | ≥ 4 vs. < 4 levels | Small Hotel is 4 stories, Large Hotel is 6 stories. | **Mismatch / Stricter** (Under current rules, a 4-story Small Hotel is misclassified as a Large Hotel). | Deru et al. (2011), Section 3.1.13, Table 3-1. |
| **Secondary vs. primary school** | ≥ 5,000 m² vs. < 5,000 m² | Primary School footprint is ~6,871 m² (73,960 ft²), Secondary School footprint is ~9,796 m² (105,444 ft²). | **Mismatch / Stricter** (Under current rules, the Primary School prototype itself is misclassified as Secondary). | Deru et al. (2011), Section 3.1.3, Table 3-1. |
| **Large vs. small data center** | ≥ 500 m² vs. < 500 m² | Small Data Center is ~55.7 m² (600 ft²), Large Data Center is ~557.4 m² (6,000 ft²). | **Match** (500 m² footprint/floor area cleanly bisects the small and large templates). | Sun et al. (2021). "Prototype energy models for data centers." Energy and Buildings, 231. |
| **Office small/medium/large** | < 500 / < 4,000 / ≥ 4,000 m² total floor area | CBES thresholds: < 2,322 m² (Small) / 2,322–9,290 m² (Medium) / ≥ 9,290 m² (Large). | **Mismatch / Stricter** (Under current rules, the 511 m² Small Office prototype is misclassified as Medium, and the 4,982 m² Medium Office prototype is misclassified as Large). | Deru et al. (2011) and LBNL CBES (Hong et al., 2015). |

---

### Table 4 — Vintage / `year_built` handling

| Source | Does `year_built`/vintage affect which archetype is picked, or only the envelope-vintage multiplier within a fixed archetype? | Source |
|---|---|---|
| **OpenUBEM (current)** | Only the envelope-vintage multiplier (`construction/PROVENANCE.md`) — archetype choice itself is vintage-blind. | `building_classifier.py` (no `year_built` reference in `_apply_rule_table`). |
| **URBANopt / OpenStudio** | Only the characteristics of the model (envelope, HVAC efficiency, schedules) change with vintage; the physical shape and archetype template (e.g. MediumOffice) are selected first by the modeler/input file. | NREL `openstudio-standards` documentation. |
| **CityBES** | Vintage determines the building code envelope requirements (U-values, SHGC), lighting density, and HVAC system type (e.g., constant volume vs. VAV) according to historic California Title 24 or ASHRAE 90.1 baselines, but the archetype choice (Small vs. Medium vs. Large Office) remains vintage-blind. | LBNL CBES (Hong et al., 2015). |
| **AutoBEM** | Vintage selects the specific age-based configuration of the prototype model, but does not influence the geometric archetype selection (e.g. Medium Office vs. Small Office). | ORNL AutoBEM (New et al., 2021). |
| **DOE/PNNL prototypes** | The physical geometry (stories, footprint, shape) of the prototypes remains identical across all vintages, but thermal properties, internal loads, and systems are defined vintage-specifically. | Deru et al. (2011). |

---

## Part C — Synthesis (threshold-by-threshold verdict)

### 1. Super-Tall vs. Tall Building Threshold
*   **Current OpenUBEM Rule:** $\ge 40$ levels (Super-Tall), $20\text{--}39$ levels (Tall).
*   **Verdict:** **GAP — no clear precedent, keep current value as the defensible default.**
*   **Rationale:** The standard 16 DOE/PNNL commercial prototypes top out at 12 stories (Large Office) or 10 stories (Highrise Apartment). While CTBUH defines tall as $\ge 15$ levels (50m) and supertall as $\ge 90$ levels (300m), these do not map onto OpenUBEM's 30-archetype vocabulary. The current thresholds are reasonable boundaries to isolate exceptionally tall high-rises that do not conform to standard prototypical office or residential physics.

### 2. High-Rise vs. Mid-Rise Apartment Threshold
*   **Current OpenUBEM Rule:** $\ge 9$ levels (Highrise), $< 9$ levels (Midrise).
*   **Verdict:** **Keep as-is.**
*   **Rationale:** Standard multifamily residential building classifications separate mid-rise structures (typically 4 to 8 levels, matching traditional wood-frame limits) from high-rise structures (9+ levels, concrete/steel frame). This maps well onto the 4-story Midrise Apartment and 10-story Highrise Apartment prototypes.

### 3. Large vs. Small Hotel Threshold
*   **Current OpenUBEM Rule:** $\ge 4$ levels (Large), $< 4$ levels (Small).
*   **Verdict:** **Change threshold to $\ge 5$ levels (or change from $\ge 4$ to $\ge 5$ levels).**
*   **Rationale:** The standard DOE Small Hotel prototype has 4 stories. Under the current rule ($\ge 4$ levels = Large), the Small Hotel prototype itself would be incorrectly classified as a Large Hotel. Changing the cut-point to $\ge 5$ levels correctly places 4-story hotels in the `SmallHotel` category and 6-story hotels in the `LargeHotel` category.

### 4. Secondary vs. Primary School Threshold
*   **Current OpenUBEM Rule:** $\ge 5,000\text{ m}^2$ footprint (Secondary), $< 5,000\text{ m}^2$ footprint (Primary).
*   **Verdict:** **Change threshold to $\ge 8,000\text{ m}^2$ footprint (or use story count: 1 story for Primary, 2+ stories for Secondary).**
*   **Rationale:** The standard DOE Primary School prototype has a footprint of 73,960 ft² (~6,871 m²), and the Secondary School prototype has a footprint of 105,444 ft² (~9,796 m²). The current threshold of 5,000 m² misclassifies the Primary School prototype as a Secondary School. A threshold of 8,000 m² cleanly separates the two prototypes. Alternatively, since Primary School is 1 story and Secondary School is 2 stories, level-count is a highly robust discriminator.

### 5. Large vs. Small Data Center Threshold
*   **Current OpenUBEM Rule:** $\ge 500\text{ m}^2$ footprint (Large), $< 500\text{ m}^2$ footprint (Small).
*   **Verdict:** **Keep as-is.**
*   **Rationale:** In Sun et al. (2021), the small computer room prototype is 600 ft² (~55.7 m²), and the standalone data center prototype is 6,000 ft² (~557.4 m²). The current threshold of 500 m² (equivalent to 5,382 ft²) cleanly separates these two scales.

### 6. Office Small/Medium/Large Thresholds
*   **Current OpenUBEM Rule:** $< 500\text{ m}^2$ (Small), $< 4,000\text{ m}^2$ (Medium), $\ge 4,000\text{ m}^2$ (Large) total floor area.
*   **Verdict:** **Change thresholds to: $< 2,322\text{ m}^2$ (Small), $2,322\text{ to } 9,290\text{ m}^2$ (Medium), and $\ge 9,290\text{ m}^2$ (Large) total floor area.**
*   **Rationale:** Under the current rules, the standard Small Office prototype (5,502 ft² / 511 m²) is classified as Medium, and the Medium Office prototype (53,628 ft² / 4,982 m²) is classified as Large. The current thresholds are too strict and misclassify standard prototypical geometries. Adopting the LBNL CBES thresholds (equivalent to 25,000 ft² and 100,000 ft²) aligns the binning with standard energy policy and correctly maps the DOE Small (511 m²), Medium (4,982 m²), and Large (46,320 m²) prototypes.

### Vintage Influence on Archetype Selection
OpenUBEM should **remain vintage-blind** for the core archetype selection. Precedent from URBANopt, CityBES, AutoBEM, and the DOE/PNNL prototype framework shows that building geometry (the size/stories archetype classification) is independent of the year built. The construction year (vintage) is used downstream to assign envelope U-values, HVAC efficiency, and internal load schedules, but the geometric template itself remains constant. The current vintage-blind cascade is the correct industry-standard practice.

---

## Confidence and Caveats

*   **Least Defensible Cut-point:** The **Super-tall vs. Tall** threshold has the least direct empirical grounding in UBEM literature because standard prototype datasets do not include models for buildings above 12 stories. 
*   **Office & School Thresholds:** The current office and school thresholds are highly indefensible as they misclassify the standard DOE prototype geometries themselves. Correcting them to the LBNL CBES and PNNL-derived values is strongly recommended.

---

## Reference List

1. **Deru, M., et al.** (2011). *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. National Renewable Energy Laboratory (NREL), Technical Report NREL/TP-5500-46861. Available at: [NREL/TP-5500-46861](https://www.nrel.gov/docs/fy11osti/46861.pdf).
2. **PNNL** (2014). *Enhancements to ASHRAE Standard 90.1 Prototype Building Models*. Pacific Northwest National Laboratory, Report PNNL-23269. Available at: [PNNL-23269](https://www.energycodes.gov/sites/default/files/2021-07/901_PrototypeBuildingModelEnhancements.pdf).
3. **Hong, T., et al.** (2015). *Commercial Building Energy Saver: An energy retrofit analysis toolkit*. Energy and Buildings, 100, 290-302. DOI: [10.1016/j.enbuild.2015.04.035](https://doi.org/10.1016/j.enbuild.2015.04.035).
4. **Sun, K., Luo, N., Luo, X., & Hong, T.** (2021). *Prototype energy models for data centers*. Energy and Buildings, Volume 231, 110586. DOI: [10.1016/j.enbuild.2020.110586](https://doi.org/10.1016/j.enbuild.2020.110586).
5. **New, J., et al.** (2021). *Automatic Building Energy Modeling (AutoBEM) software suite*. Oak Ridge National Laboratory (ORNL). Project details at: [AutoBEM](https://www.ornl.gov/project/autobem).
6. **NREL** (2020). *URBANopt Schema Documentation*. National Renewable Energy Laboratory. Available at: [URBANopt Schema](https://docs.urbanopt.net/geojson-gem/building_properties.json).
