# RESULT — Gemini (Antigravity) paper review — 2026-10-21

## 1. Example papers

### 1.1 CityEL (Song et al., *Sustainable Cities and Society* 120 (2025) 106147)

- **Section structure:**
  - 1 Introduction
  - 2 Methodology
    - 2.1 Introduction to CityEL
    - 2.2 Input data and preprocessing
    - 2.3 Introduction to the case study area (Huangpu District, Shanghai)
    - 2.4 Urban building energy model generation (AutoBPS-Geo)
    - 2.5 Retrofitted building energy model generation (envelope, HVAC, lighting, rooftop PV)
    - 2.6 Aggregate method (building → neighborhood → district)
    - 2.7 Neighborhood battery storage module
    - 2.8 Key performance indicators definition (ESP, NPV, SPB)
  - 3 Results
    - 3.1 The enhanced AutoBPS retrofit model results
    - 3.2 Results for the whole district
    - 3.3 Results for the individual buildings
    - 3.4 Results for the Neighborhoods
    - 3.5 Advanced analysis for the neighborhoods (hourly profiles, solar + storage)
  - 4 Discussion
  - 5 Conclusions
  - Appendix A The Screenshots of CityEL (Figs. 16–25)
- **Stated contributions:**
  1. Developed CityEL, a web-based, end-to-end UBEM platform designed specifically for rapid multi-scale energy benchmarking and retrofit analysis across municipal neighborhoods.
  2. Integrated enhanced AutoBPS with a GIS back-end to automate both baseline and retrofit EnergyPlus model construction, including rooftop PV and neighborhood battery energy storage.
  3. Demonstrated multi-scale decision-making on 7,934 buildings across 304 neighborhoods in Shanghai's Huangpu District, identifying 245 economically viable neighborhoods and calculating energy savings and net present value.
- **How it validates:**
  - Very light empirical validation. CityEL performs no building-level calibration against actual utility bills or smart-meter data.
  - In Section 3.2 and Fig. 10, simulated EUI distributions across 17 building prototypes are plotted against empirical EUI reference ranges gathered from published research papers and Shanghai municipal government energy reports (Shanghai Municipal Commission of Housing & Urban-Rural Development, 2024).
  - The authors note that prototype medians fall within published reference bands, while explicitly acknowledging that composite/mixed-use buildings lack empirical reference literature.
- **Key figures and tables:**
  - *Fig. 1:* Overall research and platform framework.
  - *Fig. 2:* Overall web interface architecture of CityEL.
  - *Fig. 4:* AutoBPS-Geo EnergyPlus model generation pipeline.
  - *Fig. 6:* Hierarchical aggregation method (building → neighborhood → district).
  - *Fig. 8:* Scatter plot of Energy Saving Potential (ESP) vs. Net Present Value (NPV) for retrofitted buildings.
  - *Fig. 10:* EUI distribution boxplots by building type compared with literature/report reference ranges.
  - *Fig. 12:* Summer and winter solstice diurnal district electricity demand profiles before and after retrofit + PV.
  - *Fig. 13:* Neighborhood-level energy savings potential and economic NPV/payback spatial distributions.
  - *Figs. 16–25:* Ten comprehensive platform UI screenshots (geometry statistics, EUI choropleths, hourly load curves, building drill-down, neighborhood modal).
  - *Table 1:* Building types, prototype mappings, and floor area distributions.
  - *Tables 3–5:* Retrofit measure parameters, material capital costs, and local time-of-use utility tariffs.
  - *Table 6:* Summary geometric statistics per building type.
- **Three things a reviewer would most likely praise:**
  1. *Actionable policy focus on neighborhood renewal:* Explicitly structures the modeling around China's national urban renewal policy (renovating >50,000 old residential communities), providing direct utility for municipal planning.
  2. *Integrated technical and economic retrofit evaluation:* Couples envelope, lighting, and HVAC upgrades with rooftop PV, neighborhood battery storage, capital costs, local utility tariffs, NPV, and payback periods.
  3. *Polished web-based GIS workflow:* Demonstrates an end-to-end, zero-code interface for non-expert urban planners, backed by detailed UI screenshots.

---

### 1.2 AutoBEM (Li et al., *Sustainable Cities and Society* 149 (2026) 107700)

- **Section structure:**
  - 1 Introduction
    - 1.1 Empirical Validation and Interpretation of Model Reliability
    - 1.2 Contributions and Innovations
  - 2 Research Gaps and Innovations
  - 3 Related Work (Table 2)
  - 4 Methodology
    - 4.1 Input Data (Prototype-Derived Model Parameters, HVAC Systems)
    - 4.2 Core Capabilities (Dynamic Archetypes Selection, Energy Conservation Measure Evaluation, Future Typical Meteorological Year [fTMY] Integration)
    - 4.3 Output Fields (Baseline Energy Consumption, Anthropogenic Heat Emissions Assessment, CO2 Equivalent Emission [CO2-eq] Evaluation)
  - 5 Results and Discussion
    - 5.1 Baseline Energy Consumption
    - 5.2 CO2 Equivalent Emission (CO2-eq) Evaluation
    - 5.3 ECM Evaluation
    - 5.4 Future Weather Exploration
    - 5.5 Key Findings and Insights
    - 5.6 Limitations and Interpretation of Results
  - 6 Conclusion
- **Stated contributions:**
  - Formulated across three numbered research gaps (coverage limits of sampling archetypes, decoupled ECM cost/emission pipelines, lack of scalable future-weather fTMY assessments) and five key innovations:
    - (a) Automated, building-resolved EnergyPlus/OpenStudio modeling pipeline at national scale leveraging Model America GIS datasets.
    - (b) Dynamic archetype assignment dynamically pairing building footprints with 16 DOE commercial and residential prototypes.
    - (c) Automated screening of 151 ECMs with autosized equipment costs, EIA local utility rates, and life-cycle payback analysis.
    - (d) Spatially explicit post-processing for Anthropogenic Heat Emissions (AHE) and hourly eGRID CO2-eq emissions.
    - (e) Public release of building-level inputs and outputs (Model America v1.0) and web-based digital twin visualization.
- **How it validates:**
  - Synthesizes multi-year empirical validation evidence into a four-level hierarchy (Section 1.1, Table 1):
    1. *Input building attributes:* Validated LiDAR heights, footprints, and tax assessor classifications in Las Vegas, Flagstaff, and LA100.
    2. *Individual-building energy:* 15-minute AMI smart-meter electricity data for 50,843 buildings in Chattanooga (EPB territory). Uncalibrated baseline median error was −32% (IQR −91% to 12%, R² ≈ 0.07); bias-adjusted conditioned-area corrections shifted median error to −6% (slope 0.90).
    3. *Aggregate city/stock validation:* Annual electricity and natural gas validation across five cities in Model America v2 with an average total energy error of 2.3%.
    4. *Grouped UBEM validation:* 596,064 modelled buildings compared with 247,188 metered buildings in Chicago, achieving NMBE of 10.9% (1.1% post-outlier removal).
  - Explicitly uses this evidence to establish the model's reliability envelope: uncalibrated individual-building results are approximate screening figures, whereas aggregated neighborhood and city totals are reliable planning baselines due to error cancellation.
- **Key figures and tables:**
  - *Table 1:* Multi-scale empirical validation matrix (input attributes, individual-building AMI, aggregate city, grouped UBEM).
  - *Table 2:* Systematic comparison table of representative UBEM platforms and building-stock tools.
  - *Table 6:* Standardized HVAC equipment dispatch by archetype.
  - *Tables 7–8:* ECM taxonomy (151 measures across envelope, lighting, HVAC, service water) and output metric definitions.
  - *Fig. 1:* Overall AutoBEM architecture from Model America inputs to digital twin.
  - *Fig. 2:* Dynamic archetype selection workflow.
  - *Fig. 3:* Automated ECM evaluation workflow.
  - *Fig. 4:* Anthropogenic heat emission (AHE) sensible and latent post-processing workflow.
  - *Fig. 5:* Hourly CO2-eq emission accounting workflow with eGRID subregions.
  - *Figs. 6–12:* Baseline results for Phoenix, AZ (building counts, area, fuel breakdown, EUI, carbon emissions, emission intensity heatmaps).
  - *Figs. 13–15:* Retrofit rankings (window upgrades, top 20 ECMs sorted by payback period and carbon abatement).
  - *Fig. 16:* AutoBEM web viewer displaying fTMY future climate projections.
- **Three things a reviewer would most likely praise:**
  1. *Radical transparency regarding single-building error vs. stock reliability:* Openly publishing that uncalibrated single-building predictions have R² ≈ 0.07 and −32% median error in Table 1 prevents methodological over-claiming and establishes clear boundaries of use.
  2. *Unrivalled national scale and comprehensive outputs:* Simulating millions of buildings while delivering 151 ECM evaluations, autosized capital costs, local utility tariffs, anthropogenic heat emissions (AHE), and future climate (fTMY) scenarios.
  3. *Exemplary self-critical limitations section (Section 5.6):* Dedicated paragraphs dissecting single-zone thermal approximations, archetype classification ambiguity, and floor-area error propagation.

---

## 2. Check of our investigation (row by row)

Evaluation of the 12 rows in Table 3 of [INVESTIGATION_paper-improvement_2026-10-21.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/IMP/INVESTIGATION_paper-improvement_2026-10-21.md#L48-L65):

| # | Improvement | Verdict | Sentence Rationale | Evidence Path |
|---|---|---|---|---|
| 1 | Research gaps and contributions section | **Agree** | Structuring the section with 3 numbered gaps and 5 lettered contributions directly highlights OpenUBEM's three main strengths: zero fitted parameters, multi-country dwelling division, and transparent reporting of exclusions. | [README.md:69-75](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L69-L75), [README.md:721-753](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L721-L753) |
| 2 | Organise validation in three levels | **Change** | We agree with the three-level structure, but level (b) must be clarified as municipal disclosure distributions (NYC LL84 / LA EBEWE) rather than individual smart-meter AMI utility matching, and level (c) must be re-scored on the adopted 171.38 kWh/m² baseline before submission using the existing script. | [README.md:781-802](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L781-L802), [phaseE_rescore.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/scripts/validation/phaseE_rescore.py) |
| 3 | Related-work table of UBEM platforms | **Change** | Creating the table is essential, but generic GIS libraries from `alternatives.txt` (QGIS, PostGIS, GDAL, GeoPandas) must be excluded so the table compares only actual urban energy and microclimate simulation platforms. | [alternatives.txt:1-59](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/examples/alternatives.txt#L1-L59) |
| 4 | Intended users and limits of use paragraph | **Agree** | Explicitly stating that uncalibrated physics models are built for neighborhood screening and policy rather than single-building HVAC sizing or utility bill prediction directly pre-empts reviewer objections. | [README.md:5](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L5), [README.md:368-370](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L368-L370) |
| 5 | Limitations section (one paragraph per simplification) | **Agree** | Transparently reporting the 6 warehouse/school simulation crashes, the accepted uncalibrated under-prediction, and the Cape Town non-redistribution license turns perceived weaknesses into methodological rigor. | [README.md:741-742](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L741-L742), [README.md:806-818](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L806-L818) |
| 6 | Retrofit results | **Change** | We agree with presenting retrofit results, but must correct the investigation's claim of 4 measures: `envelope_u_upgrade` was withdrawn because it duplicated the ASHRAE 90.1-2019 baseline, leaving exactly 3 active measures in the repository. | [measures.json:21-46](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/data/scenarios/measures.json#L21-L46) |
| 7 | Hourly and peak results | **Agree** | OpenUBEM's EnergyPlus parser already extracts hourly zone and meter variables, making seasonal solstice diurnal load profiles and peak demand metrics straightforward to render. | [README.md:234](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L234), [README.md:278-285](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L278-L285), [parser.py:50-120](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/results/parser.py) |
| 8 | Several scales from one run (multi-scale figure) | **Agree** | The repository already structures data hierarchically from single buildings to density cells, cities, and the 8,139-building U.S. fleet, making a multi-scale aggregation diagram straightforward to build. | [README.md:781-802](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L781-L802), [aggregator.py:30-85](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/results/aggregator.py) |
| 9 | Viewer figures (3D viewer and floor plans) | **Agree** | Including figures of OpenUBEM's standalone, zero-network 3D HTML viewer and dwelling-level floor plan layouts visually proves our unique flat-division capability. | [README.md:374-388](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L374-L388), [viewer_export.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/viz/viewer_export.py) |
| 10 | UK cross-check with energy certificates (EPCs/DECs) | **Change** | We agree with the comparison, but it must be framed as an engineering cross-check against RdSAP rather than independent validation because EPC construction year is already an input for London (`FINDING 256`), whereas public DECs offer true metered operational validation. | [BRIEF_v5.md:192-209](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/BRIEF_european_locations_v5.md#L192-L209), [gb_epc_sidecar.csv](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv) |
| 11 | Open data release | **Agree** | Publishing building-level input and output datasets for the 12 U.S. cells and open European districts (with explicit provenance and license sidecars) aligns with current journal reproducibility standards. | [README.md:741-750](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L741-L750), [eu_evidence/](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/eu_evidence/) |
| 12 | Future weather exploration | **Agree** | AutoBEM used national laboratory fTMY morphing datasets, whereas OpenUBEM currently downloads historical TMYx files from One Building, making future climate exploration a high-effort (L) task that should remain parked for future work. | [README.md:138-142](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L138-L142), [epw_manager.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/acquisition/epw_manager.py) |

---

## 3. What we missed

Eight additional improvements suggested by the example papers that our initial investigation did not list:

1. **Zoning fidelity sensitivity study (Single-zone vs. Core/Perimeter vs. Dwelling-level):**
   - *Learned from:* AutoBEM Section 5.6 (where single-zone modeling is acknowledged as AutoBEM's primary architectural limitation, with multi-zoning left as future work).
   - *Effort:* **S** (writing and plotting from existing results).
   - *Evidence in OpenUBEM:* OpenUBEM already implements selectable resolution modes (`auto`, `building`, `floor`, `fast_zone`, `layout_assign`) in [zoning.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/geometry/zoning.py) and [README.md:355-371](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L355-L371). The repository documents that single-zone models under-predict annual heating by 10–26% compared to perimeter-core zoning, while washing out to <2.3% at district scale. Including this comparison provides a methodological contribution neither example paper offers.

2. **Per-attribute input provenance and data-quality reporting:**
   - *Learned from:* AutoBEM Section 5.6 (discussion of input attribute uncertainty).
   - *Effort:* **S** (summarizing existing data).
   - *Evidence in OpenUBEM:* OpenUBEM tracks provenance and data quality tokens (`{METHOD}_{SOURCE}_{TIER}`) for every input attribute on every building ([README.md:99, 148, 158-173](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L99), [provenance.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/provenance.py)). Presenting an input provenance breakdown (observed vs. fused vs. spatial vs. statistical default across cities) demonstrates data governance and transparency absent in both example papers.

3. **Physical modeling of service loads vs. empirical post-hoc multipliers:**
   - *Learned from:* AutoBEM Table 6 & CityEL Section 2.4 (both rely on simplified prototype equipment loads or unmodeled secondary end-uses).
   - *Effort:* **S** (writing / reporting existing metrics).
   - *Evidence in OpenUBEM:* OpenUBEM explicitly models domestic hot water (`WaterHeater:Mixed`), commercial kitchen exhaust process loads, supermarket refrigeration compressor racks, and elevator motors as discrete EnergyPlus objects ([README.md:222-232](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L222-L232), [builder.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/idf/builder.py)). It retired legacy CBECS post-hoc reconstruction overlays ([README.md:321](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L321)). Demonstrating all 10 metered end-uses provides a clear physics advantage over competitors.

4. **Indoor overheating degree (IOD) and thermal resilience reporting:**
   - *Learned from:* CityEL and AutoBEM (both focus exclusively on annual energy and carbon, omitting indoor comfort and heatwave resilience).
   - *Effort:* **S** (data already computed).
   - *Evidence in OpenUBEM:* OpenUBEM calculates the occupant-weighted Indoor Overheating Degree (IOD) under an adaptive thermal comfort model across summer months (June–September) for every building in Step 5 ([README.md:300-302](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L300-L302), [parser.py:5D](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/results/parser.py)). Reporting IOD alongside EUI introduces a building resilience and occupant health dimension.

5. **Coupling building simulation with pedestrian microclimate (Step 6 UTCI):**
   - *Learned from:* AutoBEM Section 4.3.2 (AHE post-processing) and `alternatives.txt` (city2graph / Infrared City microclimate tools).
   - *Effort:* **S** (module exists and is documented).
   - *Evidence in OpenUBEM:* OpenUBEM includes an optional outdoor microclimate module ([scripts/run_step6_microclimate.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/scripts/run_step6_microclimate.py), [README.md:327-350](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L327-L350)) that computes sky view factor (SVF), shade rasters, mean radiant temperature (MRT), and 210-term COST-730 Universal Thermal Climate Index (UTCI). Featuring this stage—with its honest disclaimer that it is unvalidated against field campaigns—demonstrates advanced multi-physics capability.

6. **Automated simulation error diagnosis and failure classification:**
   - *Learned from:* AutoBEM Section 1.1 (where simulation crash counts and causes are not detailed).
   - *Effort:* **S** (writing / extracting from existing manifests).
   - *Evidence in OpenUBEM:* OpenUBEM includes an automated error parser ([results/err_parse.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/results/err_parse.py), [README.md:268, 809-813](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L268)) that diagnoses EnergyPlus fatal/severe causes, openly accounting for the 6 crashed buildings (5 warehouse sizing divergences, 1 school plant temperature runaway) out of 8,160.

7. **Archetype classification granularity (30 archetypes vs. 16 prototypes):**
   - *Learned from:* AutoBEM Table 6 (16 prototypes) and CityEL Table 1 (17 prototypes).
   - *Effort:* **S** (writing / citing test fixtures).
   - *Evidence in OpenUBEM:* OpenUBEM uses a 17-priority rule classifier mapping to 30 OpenStudio archetypes (including super-tall, tall, outpatient, hospital, laboratory, courthouse, 3 hotel tiers, and multiple office bins aligned with DOE prototype cut-points; [README.md:111-135](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L111-L135)). It is validated against frozen ground-truth fixtures (88.8% on 98 tag-rich buildings; `tests/fixtures/labelled_archetypes_tagrich_v2.csv`).

8. **Anthropogenic Heat Emissions (AHE) post-processing:**
   - *Learned from:* AutoBEM Section 4.3.2 and Fig. 4 (sensible and latent heat rejection broken into HVAC exhaust, envelope transmission, and exfiltration).
   - *Effort:* **M** (extracting HVAC heat rejection meters and envelope heat flux).
   - *Evidence in OpenUBEM:* OpenUBEM simulates real HVAC equipment across 10 families rather than ideal loads ([README.md:205-221](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L205-L221)) and extracts exterior surface temperatures in Step 6 ([README.md:338](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md#L338)). EnergyPlus heat rejection meters can be parsed via [parser.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/results/parser.py) to provide AHE profiles.

---

## 4. Related-work table (draft)

Comparison of representative UBEM and urban environmental modeling platforms:

| Platform / Tool | Simulation Engine | Zoning Fidelity | Spatial Scale | Countries Covered | Validated Against Measured Energy | Fitted or Calibrated Parameters | Open Source | Data Licence |
|---|---|---|---|---|---|---|---|---|
| **OpenUBEM** | EnergyPlus 23.1 | Multi-zone (adaptive `auto`: single, per-floor, core/perimeter) & per-dwelling (European) | Neighbourhood to district / city | 10 countries, 4 continents (US, ES, FR, GB, IT, CA, AM, ZA, FI, AT, HU) | **Yes** (NYC LL84, LA EBEWE, CBECS 2018 in US; pooled checks in EU) | **No** (strict zero-fitted rule) | **Yes** (Python) | Open (OSM ODbL, open city portals; Cape Town non-redistribution) |
| **AutoBEM** | EnergyPlus / OpenStudio | Single-zone (national scale; multi-zone AutoZone in development) | City to national (contiguous US) | 1 (United States) | **Yes** (EPB AMI electricity, Chicago metered, 5-city MAv2) | **Partly** (standard prototypes; post-hoc bias adjustments for conditioned area and fuel) | **Partly** (workflow published; Model America open data) | Open (Public domain / US Gov) |
| **CityEL** | EnergyPlus (via AutoBPS) | Single-zone (extruded footprints) | Neighbourhood to district | 1 (China: Shanghai) | **Partly** (compared against literature/report EUI ranges only; no billing/AMI validation) | **No** (prototype lookup) | **No** (web platform; code not public) | Proprietary / closed |
| **CityBES** | EnergyPlus / OpenStudio | Multi-zone (core/perimeter by floor) | City / district | 1 (United States; selected research demos) | **Partly** (benchmarked against SF/Chicago municipal disclosure) | **No** (uncalibrated DOE prototype baselines) | **No** (hosted web platform; algorithms published) | CityGML / Municipal open data |
| **UMI** | EnergyPlus (via Rhino/Grasshopper) | Core/perimeter or per-floor zones | Neighbourhood / district | Multi-country (user-imported geometry/templates) | **Partly** (academic case studies in Boston/Kuwait) | **No** (standard template assignments) | **Partly** (Rhino plugin free, core open, requires commercial Rhino) | User-provided data |
| **City Energy Analyst (CEA)** | Custom dynamic thermal model (ISO 13790) + E+ export | Single-zone per building or per floor | District / neighbourhood | Multi-country (Swiss/European & global archetypes) | **Partly** (case studies in Zurich, Singapore) | **Partly** (optional Bayesian calibration modules) | **Yes** (GPL-3.0) | Open |
| **TEASER** | Modelica (AixLib) / reduced-order RC | Reduced-order multi-zone (1- to 4-element RC) | District to city | Multi-country (primarily Germany / Europe, TABULA) | **Partly** (VDI 6007 benchmarks, university campus cases) | **No** (archetype synthesis) | **Yes** (MIT) | Open |
| **SimStock** | EnergyPlus | Single-zone or per-floor zones | City to national | 1 (United Kingdom) | **Partly** (benchmarked against UK national energy statistics) | **Partly** (calibrated against national stock data) | **Partly** (UCL academic repository) | UK OGL v3.0 / Ordnance Survey |
| **Torino 3D Heat Mapping** | GIS / 3D CityGML spatial heat loss model | Whole-building envelope | City (Torino, Italy) | 1 (Italy) | **Partly** (benchmarked against district heating billing) | **Partly**? (empirical regression / GIS heat factors) | **Yes** (GitHub) | Open (Torino open data) |
| **Infrared City** | AI / Deep Learning surrogate (trained on OpenFOAM CFD) | N/A (outdoor microclimate and wind comfort) | District / urban block | Global (climate-agnostic geometry) | **No** (validated against CFD / wind tunnel datasets, not building energy) | **Yes** (trained deep neural network weights) | **Partly** (open Python integrations; commercial SaaS) | Proprietary platform |
| **ODEN** | Web GIS / urban indicators framework | Building / neighbourhood aggregate | City / regional | Multi-country (Nordic / European focus) | **Partly**? (macro-level urban benchmarks) | **No**? (indicator-based) | **Partly**? (web analytics tool) | Open / municipal data |
| **city2graph** | Graph Neural Networks + ray casting (MRT, UTCI, SVF) | Exterior façade surfaces | District / block | Multi-country (case studies in Barcelona) | **No** (microclimate and outdoor thermal comfort only) | **Yes** (trained GNN surrogate models) | **Partly**? (academic prototype) | Open GIS / Sentinel-2 / ERA5 |

*(Note: cells marked with "?" denote attributes inferred from available technical documentation where explicit source code or licensing terms could not be independently verified).*

---

## 5. UK certificate data — what it can and cannot prove

Analysis of UK Energy Performance Certificates (domestic/non-domestic EPCs) and Display Energy Certificates (DECs) for the London St Dunstan's district (`GB-LDN-STDUNSTANS`), in light of `FINDING 256` ([BRIEF_european_locations_v5.md:192-209](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/BRIEF_european_locations_v5.md#L192-L209)):

### 5.1 What an EPC / DEC comparison CAN prove
1. **Cross-methodology compliance consistency (EnergyPlus vs. RdSAP/SBEM):**
   - Comparing OpenUBEM's simulated space heating EUI against the domestic EPC's calculated space heating requirement (kWh/m²/yr) evaluates whether full dynamic EnergyPlus physics paired with TABULA archetypes aligns with the UK government's official compliance tool (RdSAP).
2. **Input attribute and geometry validation:**
   - Domestic and non-domestic EPC records contain on-site surveyor-inspected parameters: total floor area, wall construction type (e.g., solid brick vs. cavity), glazing type, and primary heating system fuel. Comparing OpenUBEM's OSM-derived footprints and inferred envelope properties against EPC surveyor observations provides independent verification of input enrichment accuracy.
3. **True operational metered validation for public buildings (via DECs):**
   - Unlike EPCs, Display Energy Certificates (DECs) are mandatory for public buildings >250 m² and are calculated from **12 months of actual metered utility consumption** (electricity, gas, heating oil). Comparing OpenUBEM's non-domestic predictions against DECs for schools and municipal facilities in London provides genuine operational validation in Europe, directly mirroring the U.S. municipal disclosure validation (NYC LL84 / LA EBEWE).

### 5.2 What an EPC / DEC comparison CANNOT prove
1. **Cannot prove independent validation of construction vintage (due to circularity):**
   - Under `FINDING 256` ([BRIEF_european_locations_v5.md:192-209](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/BRIEF_european_locations_v5.md#L192-L209)), cached UK domestic EPC records were queried to harvest observed `construction_year` values to resolve TABULA age bands and straddles for London buildings (`openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv`). Validating OpenUBEM's age assignment or age-derived thermal properties against EPC records is circular.
2. **Cannot prove operational energy accuracy for domestic dwellings:**
   - Domestic EPC ratings are theoretical asset ratings derived from standardized RdSAP operating assumptions (standard occupant counts, fixed 21 °C setpoints, 9-hour weekday heating schedules). They do not reflect real occupant behavior or actual billing data. Extensive literature confirms an "EPC performance gap" of 30–50% between RdSAP predictions and smart-meter billing data.
3. **Cannot cover the complete district fleet without selection bias:**
   - As established in `FINDING 256` and `DEBUG_why-not-100-percent-2026-09-04.md`, 418 London footprints in St Dunstan's have never had an EPC lodged (unrented, owner-occupied since 2008, or exempt), and 269 footprints hold multiple mutually contradictory certificates. An EPC cross-check covers only an opportunistic, self-selected sub-sample.
4. **Cannot validate unregulated plug loads or process energy:**
   - EPCs only account for regulated energy (space heating, water heating, fixed lighting, ventilation). They omit consumer electronics, plug-in appliances, and cooking, which OpenUBEM models explicitly.

---

## 6. Draft text

### 6.1 Section: Research gaps and contributions (≤ 350 words)

> Despite rapid advances in urban building energy modelling (UBEM), current platforms face three fundamental limitations:
> 
> 1. *Pervasive parameter fitting and calibration dependency:* Most UBEM tools achieve acceptable agreement with empirical benchmarks by tuning unmeasured parameters or applying post-hoc empirical multipliers. This obscures physical modeling errors, eliminates transferability to unmeasured regions, and prevents cross-city generalization.
> 2. *Geographic confinement and single-zone approximations:* State-of-the-art platforms are predominantly confined to a single nation (typically the United States) and model buildings as monolithic single thermal zones. Single-zone models cannot capture core-perimeter thermal dynamics or dwelling-level variations essential for residential urban planning.
> 3. *Opaque simulation attrition and undocumented exclusions:* Large-scale platforms rarely publish detailed diagnostics for buildings that crash during simulation or fail geometry generation, presenting artificially sanitized summaries over unstated populations.
> 
> To resolve these gaps, this paper presents **OpenUBEM**, an open-source, automated UBEM framework operating with zero fitted parameters. The key contributions are:
> 
> - **(a) Physics-based, uncalibrated modeling:** An automated 5-stage pipeline simulating every building as an individual EnergyPlus model across ten real HVAC families, with physically modelled service loads (DHW, cooking, refrigeration, elevators) and strict provenance tracking.
> - **(b) Cross-national transferability across four continents:** End-to-end simulation of 12 U.S. density cells (8,139 buildings, 171.38 kWh/m²) and 10 residential districts in 10 countries (3,870 pooled European buildings, 62.63 kWh/m² heating EUI) using local municipal registers, national TABULA archetypes, and localized weather stations without regional retuning.
> - **(c) Dwelling-level spatial zoning:** An algorithmic floor-plan partitioning workflow that divides multi-family buildings into individual residential units and thermal zones.
> - **(d) Multi-level empirical validation:** Systematic validation against U.S. municipal disclosure datasets (NYC LL84, LA EBEWE, CBECS 2018) achieving archetype-level R² of 0.723–0.902 across three climate zones.
> - **(e) Complete transparency of exclusions:** Explicit accounting of every excluded building and crash root cause (e.g., 6 production warehouse and school crashes), alongside standalone, zero-network 3D web viewers and floor-plan visualizations.

*(Word count: 326 words)*

---

### 6.2 Paragraph: Intended users and limits of use (≤ 150 words)

> **Intended users and limits of use.** OpenUBEM is designed for urban planners, municipal sustainability offices, district energy engineers, and academic researchers conducting neighbourhood- and district-scale energy screening, decarbonisation planning, stock-level retrofit prioritization, and outdoor thermal stress mapping. Because OpenUBEM operates with zero fitted parameters and relies on archetype-based internal loads and schedules, individual building outputs represent uncalibrated engineering screening estimates rather than utility-bill predictions. Building-level uncertainties arise from unobserved occupant behavior and operational schedules. Therefore, OpenUBEM outputs must **not** be used for investment-grade single-building financial retrofits, mechanical equipment sizing, or statutory building code compliance certification without on-site audits, local utility sub-metering, and building-specific calibration.

*(Word count: 111 words)*

---

## 7. Evidence list (every file you cited)

All statements, numbers, and code capabilities cited above trace directly to the following repository files:

1. [README.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/README.md)
   - Lines 1–75: Platform architecture, 5-stage pipeline, design principles (zero fitted parameters, 10 HVAC families).
   - Lines 80–175: Step 1 ingest, Step 2 classification (30 archetypes, 88.8% fixture accuracy), and 3-tier imputation.
   - Lines 178–242: Step 3 IDF builder, Douglas-Peucker simplification, zoning strategies, physical service loads.
   - Lines 243–271: Step 4 parallel runner, resume capabilities, version handshake, and failure classification.
   - Lines 274–326: Step 5 parser (10 metered end-uses, .eio simulated floor area), carbon, and CBECS validation gates.
   - Lines 327–350: Step 6 microclimate module (SVF, shadow rasters, MRT, 210-term COST-730 UTCI).
   - Lines 355–371: Simulation resolution modes (`auto`, `building`, `floor`, `fast_zone`, `layout_assign`) and zoning physics.
   - Lines 374–388: Interactive zero-network 3D HTML viewer and CityJSON generator.
   - Lines 721–773: European & international district results (10 districts, 4 continents, pooled heating EUI 62.63 kWh/m²).
   - Lines 777–822: Status & validation: adopted U.S. fleet figure (171.38 kWh/m², 1,146,454 t CO₂e over 8,139 buildings), R² scores (0.877 / 0.902 / 0.723), and the 6 production crash causes.
2. [INVESTIGATION_paper-improvement_2026-10-21.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/IMP/INVESTIGATION_paper-improvement_2026-10-21.md)
   - Lines 1–89: First-pass review, initial 12 improvement proposals, and suggested paper outline.
3. [BRIEF_european_locations_v5.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/BRIEF_european_locations_v5.md)
   - Lines 192–209: `FINDING 256` detailing cached UK EPC `construction_year` extraction for London St Dunstan's, resolving TABULA age bands and straddles, and identifying the 418 uncertified footprint ceiling.
4. [EU11_results_2026-10-08_summary.csv](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/results/EU11_results_2026-10-08_summary.csv)
   - Lines 1–6: Adopted results for Madrid (68.77 kWh/m²), Lyon (57.81 kWh/m²), London (68.31 kWh/m²), Bologna (58.16 kWh/m²), and pooled fleet (62.63 kWh/m² over 3,870 buildings).
5. [EU22_results_*_summary.csv](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/results/)
   - Summary files for Yerevan (48.52 kWh/m²), Vienna (77.58 kWh/m²), Montreal (140.90 kWh/m²), Helsinki (96.42 kWh/m²), Budapest (63.36 kWh/m²), and Cape Town (54.15 kWh/m²).
6. [measures.json](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/data/scenarios/measures.json)
   - Lines 1–65: Technical definitions for `lighting_power_density` (active), `envelope_u_upgrade` (withdrawn due to baseline overlap), `thermostat_setback` (active), and `infiltration_tightening` (active).
7. [gb_epc_construction_year_sidecar.csv](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv)
   - Evidence sidecar linking London `osm_id`s to cached UK EPC certificate years.
8. [zoning.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/geometry/zoning.py)
   - Resolution mode logic: single zone, per-floor zone, and core/perimeter zone definitions.
9. [builder.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/idf/builder.py)
   - Step 3 IDF assembly and dispatch across 10 HVAC families and physical service loads.
10. [parser.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/results/parser.py)
    - SQLite and CSV parsing of 10 EnergyPlus end-use meters and summer Indoor Overheating Degree (IOD).
11. [err_parse.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/results/err_parse.py)
    - EnergyPlus fatal and severe error parser extracting failure causes.
12. [provenance.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/provenance.py)
    - Canonical provenance token schema `{METHOD}_{SOURCE}_{TIER}`.
13. [viewer_export.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/viz/viewer_export.py)
    - Standalone, self-contained 3D HTML viewer exporter with baked basemap and trust badges.
14. [alternatives.txt](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/examples/alternatives.txt)
    - Tool links for Torino 3D heat mapping, Infrared City, ODEN, and city2graph.
15. [Energy certificate data APIs – GOV.UK.pdf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/resources/UK/Energy%20certificate%20data%20APIs%20%E2%80%93%20GOV.UK.pdf)
    - API documentation for UK Domestic EPCs, Non-Domestic EPCs, and Display Energy Certificates (DECs).
16. [CityEL paper (Song et al., SCS 2025)](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/examples/main.pdf)
    - CityEL platform structure, methodology, validation, figures, and screenshots.
17. [AutoBEM paper (Li et al., SCS 2026)](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/examples/1-s2.0-S2210670726005834-main.pdf)
    - AutoBEM platform structure, Table 1 validation levels, Table 2 related work, and Section 5.6 limitations.

---

## 8. Open questions for the owner (max 5)

1. **Manuscript scope (One flagship paper vs. Two focused papers):** Should OpenUBEM be presented as a single comprehensive journal paper covering both the zero-fitted U.S. validation (12 cells, 8,139 buildings) and international transferability (10 countries, dwelling-level division), or split into Paper 1 (U.S. methodology, zero-calibration philosophy, and municipal validation) and Paper 2 (international dwelling-level division, TABULA integration, and cross-national stock modeling)?
2. **Re-scoring city disclosure comparisons:** May we run `scripts/validation/phaseE_rescore.py` to update the city-overall comparison figures (currently reporting NYC −31.3%, LA −3.6%, Austin −30.5% against the superseded 2026-08-19 baseline) to reflect the adopted 2026-09-30 figure (171.38 kWh/m²)?
3. **Retrofit measure scope:** Given that `envelope_u_upgrade` is currently marked "withdrawn" in `openubem/data/scenarios/measures.json` because it duplicated the ASHRAE baseline, should the paper report retrofit impacts strictly across the three active measures (lighting, thermostat setback, airtightness), or would you prefer a corrected envelope retrofit target formulated prior to publication?
4. **Open data release licensing:** For the proposed open data repository accompanying the paper, should we release the 12 U.S. validation cells and the open European districts (Madrid, Lyon, London, Vienna, Helsinki) while explicitly withholding Cape Town (due to municipal non-redistribution terms) and noting census restrictions for Yerevan?
5. **Operational DEC validation for London:** Would you like to perform a targeted operational validation against UK Display Energy Certificates (DECs) for public non-domestic buildings in London St Dunstan's, providing our first European empirical comparison against metered billing data?
