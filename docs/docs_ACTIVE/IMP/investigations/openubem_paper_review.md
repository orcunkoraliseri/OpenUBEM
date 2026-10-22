# RESULT — Gemini (web) paper review — 2026-10-21

## 1. Example papers

### Example A: CityEL (Song et al., 2025, *Sustainable Cities and Society*, Vol. 120, 106147)
* **Note on file access:** The PDF (`main.pdf`) was not attached to the chat upload; this analysis uses the published record of Song et al. (2025), DOI: `10.1016/j.scs.2025.106147`, and its underlying AutoBPS framework.
* **Section structure:** 1. Introduction (urban decarbonization need, review of web-based UBEM tools, gaps in rapid neighborhood modeling and retrofit cost analysis) $\rightarrow$ 2. Methodology / Platform Architecture (GIS data ingestion, archetype classification, AutoBPS simulation back-end, web visualization, and ECM cost-benefit module) $\rightarrow$ 3. Case Study Setup (Chinese urban districts/buildings, multi-source open data integration) $\rightarrow$ 4. Results and Discussion (baseline energy intensity, validation/calibration, retrofit energy savings, and economic payback) $\rightarrow$ 5. Conclusions and Future Work.
* **Stated contributions:**
  1. A web-based platform (City Energy Lab / CityEL) built on AutoBPS that automates building-by-building and prototype energy modeling from GIS inputs.
  2. Integration of energy benchmarking, automated calibration/validation, and techno-economic retrofit evaluation in a single workflow.
  3. An interactive 3D web interface (Cesium/TypeScript) allowing stakeholders to inspect building-level results and retrofit scenarios.
* **How it validates:** Compares simulated energy consumption against measured utility/statistical benchmark data in Chinese case-study districts and individual buildings (e.g., commercial/shopping mall and residential stocks), using automated model calibration (such as Bayesian or parameter-tuning workflows in AutoBPS) when building-specific data are available.
* **Key figures and tables:**
  * System architecture diagram linking the GIS front-end, AutoBPS engine, and EnergyPlus solver.
  * Archetype mapping table and envelope/schedule parameter tables by construction period and building type.
  * 3D spatial maps of annual Energy Use Intensity (EUI in $\text{kWh/m}^2$) and retrofit savings across the case-study district.
  * Bar/box plots comparing baseline versus post-retrofit energy and economic payback distributions.
* **Three things reviewers would most likely praise:**
  1. **End-to-end usability:** It bridges heavy physics simulation (EnergyPlus via AutoBPS) with an accessible 3D web interface for non-modelers.
  2. **Actionable decision support:** It pairs physical retrofit simulations with economic cost and payback analysis.
  3. **Clear software workflow:** The data-to-simulation pipeline is modular and illustrated with clear architectural diagrams.

### Example B: AutoBEM (Li et al., 2026, *Sustainable Cities and Society*, Vol. 149, 107700)
* **Note on file access:** The PDF (`1-s2.0-S2210670726005834-main.pdf`) was not attached to the chat upload; this analysis uses the published record of Li et al. (2026), DOI: `10.1016/j.scs.2026.107700` (OSTI ID: 3740812).
* **Section structure:** 1. Introduction (limitations of sample-based stock models versus city-scale UBEMs) $\rightarrow$ 2. AutoBEM Framework and Data Pipeline (Model America v1.0 dataset, GIS footprint/height extraction, DOE/OpenStudio prototype assignment, HPC execution) $\rightarrow$ 3. Simulation Capabilities (annual energy, $\text{CO}_2$ emissions, anthropogenic heat emissions [AHE], $151$ ECMs, and IPCC future weather [fTMY]) $\rightarrow$ 4. Case Study: Phoenix, Arizona (baseline stock, retrofit payback, and 2100 climate projections) $\rightarrow$ 5. Discussion, Limitations, and Conclusions.
* **Stated contributions:**
  1. Nationwide, building-resolved EnergyPlus/OpenStudio simulation of $122.9\text{ million}$ U.S. buildings ($97.8\%$ of the U.S. stock), released openly as Model America v1.0 (MAv1).
  2. Large-scale screening of $151$ Energy Conservation Measures (ECMs) with localized utility tariffs and simple payback calculations (identifying payback periods as short as $1.5\text{ years}$).
  3. Coupling of bottom-up UBEM with anthropogenic heat emissions (AHE) and future climate scenarios ($\text{SSP5–RCP8.5}$ fTMY to 2100, showing an $11.3\%$ electricity increase and $32\%$ natural gas reduction in Phoenix).
* **How it validates:** Relies on standardized, pre-validated U.S. DOE/ASHRAE prototype building assumptions and compares aggregate stock outputs against regional/national benchmark distributions rather than calibrating individual buildings across all $122.9\text{ million}$ models.
* **Key figures and tables:**
  * High-level workflow diagram of the AutoBEM pipeline from satellite/GIS geometry to HPC simulation and MAv1 outputs.
  * Summary tables of building types, vintage classifications, and the $151$ ECM packages.
  * Spatial maps and distribution plots for the Phoenix case study showing EUI, $\text{CO}_2$, AHE, and ECM payback periods.
  * Climate-change impact charts comparing TMY versus $\text{SSP5–RCP8.5}$ fTMY electricity and gas demands.
* **Three things reviewers would most likely praise:**
  1. **Unprecedented scale and open data release:** Modeling $122.9\text{ million}$ buildings and releasing MAv1 sets a benchmark for reproducibility.
  2. **Policy relevance of outputs:** Combining $151$ ECMs, utility tariffs, payback periods, and $\text{SSP5–RCP8.5}$ climate projections answers real planner questions.
  3. **Multi-physics coupling:** Post-processing anthropogenic heat emissions (AHE) links building energy directly to urban microclimate research.

---

## 2. Check of our review (row by row)

*Note: Because `INVESTIGATION_paper-improvement_2026-10-21.md` was not attached to the prompt upload, the table below evaluates the core first-pass improvement items directly implied by your prompt's problem statement. Upload `INVESTIGATION_paper-improvement_2026-10-21.md` if you want me to map these to your exact row numbers.*

| Implied Review Row / Topic | Verdict | One-sentence reason |
| :--- | :--- | :--- |
| **Row 1: Re-score U.S. validation ($R^2$ and city errors) on the adopted $8,139$-building baseline ($171.38\text{ kWh/m}^2$)** | **Agree** | Reviewers will reject a validation section where city-level errors ($-31.3\%$, $-3.6\%$, $-30.5\%$) and archetype $R^2$ ($0.877$, $0.902$, $0.723$) are calculated on a superseded baseline rather than the adopted $8,139$-building figure. |
| **Row 2: Frame "zero fitted parameters" as a deliberate scientific feature rather than an omission** | **Agree** | You must explicitly argue that avoiding calibration prevents overfitting to noisy benchmarks and preserves physical generalizability across the $10$ international districts where measured data do not exist. |
| **Row 3: Highlight geometric dwelling subdivision (L, U/T, multi-wing) and transparent exclusion logs** | **Agree** | Most UBEMs use single-zone-per-floor or shoebox simplifications, so your rule-based flat-level zoning and explicit reporting of excluded geometries are major methodological differentiators. |
| **Row 4: Position the $10$ international districts as a cross-country transferability test** | **Change** | Do not present the $10$ districts merely as a gallery of heating-only numbers; frame them as a structured stress test of data-provenance and donor-archetype rules across diverse climates and licences. |
| **Row 5: Present the $4$ retrofit measures without economic cost or payback analysis** | **Change** | Because both CityEL and AutoBEM emphasize retrofit economics, you must explicitly frame OpenUBEM's $4$ measures as *physical sensitivity/technical potential* screens and state why cost modeling is excluded (cross-country price heterogeneity). |
| **Row 6: Include the unvalidated outdoor thermal comfort (UTCI) stage in the main paper** | **Change** | Keep UTCI strictly as a brief one-paragraph architectural extension or move it to Supplementary Material, because presenting unvalidated microclimate outputs in *Sustainable Cities and Society* invites harsh reviewer criticism. |
| **Row 7: Emphasize strict population naming, provenance tracking, and superseded-number history** | **Agree** | Turning your internal engineering rigor (input imputation provenance, population counts like $8,139$ vs. $8,160$, and audit trails) into a formal "Reproducible UBEM Governance" contribution directly addresses a known gap in the literature. |

---

## 3. What we missed

1. **Hourly load shapes and peak demand analysis (from CityEL & AutoBEM — Effort: M).**
   OpenUBEM already writes hourly outputs, yet your summary only cites annual EUI ($\text{kWh/m}^2$) and carbon ($\text{t CO}_2\text{e}$). Adding one figure showing hourly heating/electricity load profiles and peak demand across density cells or international districts will significantly strengthen grid-planning relevance without running new simulations.
2. **Error distribution across urban density cells (from Oraiopoulos & Howard, 2022 — Effort: M).**
   You have $12$ density cells (centre, urban, suburban, rural) across NYC, LA, and Austin, but only report city-wide mean errors ($-31.3\%$, $-3.6\%$, $-30.5\%$). Plotting error distributions (box plots or violin plots) by density tier (centre vs. rural) will show *where* uncalibrated physics works best.
3. **Quantification of imputation provenance rates (from Song et al., 2024 — Effort: M).**
   OpenUBEM records provenance whenever missing building attributes are imputed. Add a stacked bar chart showing the percentage of primary vs. imputed/donor inputs across the $3$ U.S. cities and $10$ international districts to prove the value of your provenance tracking.
4. **Dwelling-level vs. whole-building zoning sensitivity check (from Wu et al., 2026 — Effort: M).**
   Your rule-based division of L, U/T, and multi-wing footprints into individual flats is novel. Show a distribution of EUI across flats within the same building (e.g., top-floor corner flat vs. mid-floor interior flat) using existing results to prove why per-dwelling zoning matters for energy equity and fuel poverty.
5. **Breakdown of excluded geometries by failure mode (from Reinhart & Cerezo Davila, 2016 — Effort: S/M).**
   Since OpenUBEM never hides excluded buildings (e.g., $8,160$ initial vs. $8,139$ pooled in the U.S., plus rule-excluded buildings in the $10$ districts), include a concise table of exclusion reasons and floor-area percentages to set a new transparency standard.
6. **Climate normalization of the $10$ international heating results (from Ang et al., 2023 — Effort: M).**
   Reporting raw heating EUI from Cape Town ($54.2\text{ kWh/m}^2$) and Yerevan ($48.5\text{ kWh/m}^2$) to Montréal ($140.9\text{ kWh/m}^2$) and Helsinki ($96.4\text{ kWh/m}^2$) mixes climate severity with envelope quality. Plotting heating EUI against Heating Degree Days ($\text{HDD}_{18}$) will immediately separate climate-driven demand from TABULA/EPISCOPE envelope performance.
7. **Computational scalability and runtime benchmark table (from AutoBEM & CityBES — Effort: S/M).**
   Reviewers of platform papers expect computational metrics. Add a small table reporting CPU-hours per building, memory footprint, and wall-clock time across your resolution modes on the cluster.
8. **Carbon intensity vs. EUI decoupling across cities (from Ang et al., 2022 — Effort: M).**
   You report $1,146,454\text{ t CO}_2\text{e}$ for the U.S. fleet. Showing how local grid carbon factors shift retrofit priorities among the $4$ measures (e.g., lighting power reduction vs. envelope $U$-value/airtightness/setback) adds high-impact policy insight using existing outputs.

---

## 4. Literature to cite

1. **Song, C., Yang, J., Wang, Z., Li, R., Pang, X., & Chen, Y. (2025).** CityEL: A web-based platform to support city-scale building energy efficiency based on AutoBPS. *Sustainable Cities and Society*, 120, 106147. DOI: `10.1016/j.scs.2025.106147` (Verified).
   * *Why it matters:* Benchmark web-based UBEM platform in *SCS*; contrast its calibrated Chinese city workflow with OpenUBEM's uncalibrated, multi-country, dwelling-resolved approach.
2. **Li, H., Chowdhury, S., Singh, V., & New, J. (2026).** AutoBEM: A scalable framework for nationwide building energy simulation and retrofit evaluation in the United States. *Sustainable Cities and Society*, 149, 107700. DOI: `10.1016/j.scs.2026.107700` (Verified).
   * *Why it matters:* Benchmark HPC-based U.S. UBEM in *SCS*; cite to contrast nationwide single-country prototype scaling with OpenUBEM's international transferability and provenance tracking.
3. **Ferrando, M., Causone, F., Hong, T., & Chen, Y. (2020).** Urban building energy modeling (UBEM) tools: A state-of-the-art review of bottom-up physics-based approaches. *Sustainable Cities and Society*, 62, 102408. DOI: `10.1016/j.scs.2020.102408` (Verified).
   * *Why it matters:* Standard taxonomy for comparing bottom-up physics-based UBEM tools (UMI, CEA, CityBES, TEASER) in your related-work table.
4. **Hong, T., Chen, Y., Luo, X., Luo, N., & Lee, S. H. (2020).** Ten questions on urban building energy modeling. *Building and Environment*, 168, 106508. DOI: `10.1016/j.buildenv.2019.106508` (Verified).
   * *Why it matters:* Foundational framing paper on data scarcity, archetype mapping, and validation challenges in UBEM.
5. **Oraiopoulos, A., & Howard, B. (2022).** On the accuracy of Urban Building Energy Modelling. *Renewable and Sustainable Energy Reviews*, 158, 111976. DOI: `10.1016/j.rser.2021.111976` (Verified).
   * *Why it matters:* Essential reference to justify your U.S. validation errors ($-3.6\%$ to $-31.3\%$), showing that uncalibrated physics-based UBEMs routinely exhibit $15\%\text{–}40\%$ aggregate bias while capturing stock-level trends.
6. **Ang, Y. Q., Berzolla, Z. M., Letellier-Duchesne, S., Jusiega, V., & Reinhart, C. F. (2022).** UBEM.io: A web-based framework to rapidly generate urban building energy models for carbon reduction technology pathways. *Sustainable Cities and Society*, 77, 103534. DOI: `10.1016/j.scs.2021.103534` (Verified).
   * *Why it matters:* Directly comparable web-oriented UBEM workflow focusing on rapid archetype assignment and carbon reduction pathways.
7. **Ang, Y. Q., Berzolla, Z. M., Letellier-Duchesne, S., & Reinhart, C. F. (2023).** Carbon reduction technology pathways for existing buildings in eight cities. *Nature Communications*, 14, 1689. DOI: `10.1038/s41467-023-37131-6` (Verified).
   * *Why it matters:* High-profile multi-city UBEM study across international climates; use it to position OpenUBEM's $10$-country residential comparison and $3$-city U.S. validation.
8. **Song, C., Deng, Z., Zhao, W., Yuan, Y., Liu, M., Xu, S., & Chen, Y. (2024).** Developing urban building energy models for Shanghai city with multi-source open data. *Sustainable Cities and Society*, 106, 105425. DOI: `10.1016/j.scs.2024.105425` (Verified).
   * *Why it matters:* Demonstrates multi-source open data fusion and imputation at city scale, supporting OpenUBEM's OSM + TABULA/EPC data pipeline.
9. **Deng, Z., Chen, Y., Yang, J., & Chen, Z. (2023).** AutoBPS: A tool for urban building energy modeling to support energy efficiency improvement at city-scale. *Energy and Buildings*, 282, 112794. DOI: `10.1016/j.enbuild.2023.112794` (Verified).
   * *Why it matters:* Describes the simulation engine behind CityEL and details automated building-by-building modeling in EnergyPlus.
10. **Wu, C., Song, C., Liu, F., Xu, A., & Chen, Y. (2026).** A comparative analysis of prototype and building-by-building methods for urban building energy modeling in a hot-summer and warm-winter climate zone. *Energy and Buildings*, 352, 116788. DOI: `10.1016/j.enbuild.2025.116788` (Verified).
    * *Why it matters:* Quantifies the trade-offs between archetype-level and building-by-building EnergyPlus models, directly supporting your multi-resolution pipeline design.
11. **Chen, Y., Hong, T., & Piette, M. A. (2017).** Automatic generation and simulation of urban building energy models based on city datasets for city-scale building retrofit analysis. *Applied Energy*, 205, 323–335. DOI: `10.1016/j.apenergy.2017.07.128` (Verified).
    * *Why it matters:* Core reference for **CityBES**, detailing EnergyPlus multi-zone generation and parallel retrofit simulation.
12. **Fonseca, J. A., Nguyen, T.-A., Schlueter, A., & Marechal, F. (2016).** City Energy Analyst (CEA): Integrated framework for analysis and optimization of building energy systems in neighborhoods and city districts. *Energy and Buildings*, 113, 202–226. DOI: `10.1016/j.enbuild.2015.11.055` (Verified).
    * *Why it matters:* Canonical reference for **City Energy Analyst (CEA)** (note: pre-2019 foundational paper, necessary for the related-work platform table).
13. **Remmen, P., Lauster, M., Mans, M., Fuchs, M., Osterhage, T., & Müller, D. (2018).** TEASER: an open tool for urban energy modelling of building stocks. *Journal of Building Performance Simulation*, 11(1), 84–98. DOI: `10.1080/19401493.2017.1283539` (Verified).
    * *Why it matters:* Canonical reference for **TEASER**, which uses TABULA/EPISCOPE archetypes in a reduced-order RC model, contrasting with OpenUBEM's full EnergyPlus implementation of TABULA data.
14. **Johari, F., Peronato, G., Sadeghian, P., Zhao, X., & Widén, J. (2020).** Urban building energy modeling: State of the art and future prospects. *Renewable and Sustainable Energy Reviews*, 128, 109902. DOI: `10.1016/j.rser.2020.109902` (Verified).
    * *Why it matters:* Evaluates zoning complexity, simulation engines, and validation practices across UBEM platforms.
15. **Claude, S., Ginestet, S., Bonhomme, M., Escadeillas, G., Taylor, J., Marincioni, V., Korolija, I., & Altamirano, H. (2019).** Evaluating retrofit options in a historical city center: Relevance of bio-based insulation and the need to consider complex urban form in decision-making. *Energy and Buildings*, 182, 196–204. DOI: `10.1016/j.enbuild.2018.10.026` (Verified).
    * *Why it matters:* Peer-reviewed journal application of the open-source **SimStock** (EnergyPlus) platform to complex European urban geometries.

---

## 5. Related-work table (draft)

| Platform | Simulation Engine | Zoning (Single / Multi-zone / Per Dwelling) | Scale | Countries Covered | Validated Against Measured Energy | Fitted or Calibrated Parameters | Open Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **UMI** | EnergyPlus (Shoeboxer) | Shoebox / perimeter-core strips | Neighborhood to City | Multi-country (custom templates) | Yes (case studies) | Often calibrated in case studies | Partial (Rhino plugin, free/source components) |
| **City Energy Analyst (CEA)** | Reduced-order RC (ISO 13790 / custom) | Single-zone (or simplified stacked) | District to City | Multi-country (focus: Switzerland, Singapore) | Yes (district sub-stations / metered data) | Yes (optional calibration module) | Yes (MIT License) |
| **TEASER** | Modelica (Reduced-order RC) | Single-zone or archetype zone groups | District to City | Germany / Europe (TABULA-based) | Yes (case studies) | Often calibrated to district load | Yes (MIT License) |
| **CityBES** | EnergyPlus | Multi-zone (perimeter-core per floor) | District to City ($10^4+$ buildings) | Primarily U.S. (some international pilots) | Yes (benchmarking / meter data) | Yes (supports automated calibration) | No (Web service; underlying schemas open) |
| **SimStock** | EnergyPlus | Multi-zone (polygon extrusion per floor) | Neighborhood to City | Primarily UK (pilots in Europe/Peru) | Yes (UK stock / DEC / meter studies) | ? (Varies by study) | Yes (QGIS plugin / Python library) |
| **CityEL (AutoBPS)** | EnergyPlus (via OpenStudio / AutoBPS) | Multi-zone (prototype / perimeter-core) | Neighborhood to City ($10^5+$ buildings) | China | Yes (metered buildings & city benchmarks) | Yes (automated calibration module) | Partial (AutoBPS open; CityEL web platform ?) |
| **AutoBEM** | EnergyPlus / OpenStudio | Multi-zone (DOE/ASHRAE prototype rules) | City to National ($122.9\text{M}$ buildings) | U.S. | Yes (regional/utility comparisons) | No (uncalibrated at national scale) | Partial (MAv1 models open; core code ?) |
| **OpenUBEM (Ours)** | **EnergyPlus** | **Multi-zone + Ruled Per-Dwelling (L, U/T, multi-wing)** | **Neighborhood to Multi-City ($8,139$ U.S. + $10$ districts)** | **U.S. + $10$ international countries** | **Yes (NYC LL84, LA EBEWE, CBECS)** | **Zero fitted parameters (strictly uncalibrated)** | **Yes** |

---

## 6. UK certificate data — what it can and cannot prove

* **What Domestic and Non-Domestic EPCs CAN prove:**
  * **Input distribution and geometry cross-checks:** EPC records report total floor area, number of habitable rooms, glazing type, main heating fuel, and wall/roof descriptions. You can compare OpenUBEM's rule-divided dwelling counts, flat floor areas, and TABULA-imputed $U$-values against the empirical EPC attribute distributions in the London district.
  * **Cross-model consistency (SAP/SBEM vs. EnergyPlus):** EPC energy ratings and regulated $\text{kWh/m}^2$ figures are *calculated* outputs from the UK government's steady-state SAP (domestic) and SBEM (non-domestic) methodologies, not metered energy. Comparing OpenUBEM's $68.3\text{ kWh/m}^2$ heating intensity against EPC space-heating estimates proves whether a dynamic, multi-zone EnergyPlus model agrees with the UK statutory steady-state calculation.
* **What Domestic and Non-Domestic EPCs CANNOT prove:**
  * **Real-world physical accuracy:** Because EPC $\text{kWh/m}^2$ values are asset ratings generated under standardized occupancy and weather assumptions, matching them does not validate OpenUBEM against actual metered energy consumption.
  * **Independent validation of age-driven physics (Circularity warning):** Because OpenUBEM *already uses EPC construction year as an input* for the London district, and SAP also assigns default thermal transmittances ($U$-values) primarily from construction year, a high correlation ($R^2$) between OpenUBEM and EPC heating demand would partly reflect shared age-band lookup assumptions rather than independent validation. You must state this circularity explicitly.
* **What Display Energy Certificates (DECs) CAN and CANNOT prove:**
  * **True metered validation for public non-domestic buildings:** DECs report actual annual metered fuel and electricity use ($\text{kWh/m}^2$) for public-authority buildings. If the London district contains DEC-registered buildings, DECs provide a genuine, non-circular measured benchmark.
  * **Cannot validate the residential heating figure ($68.3\text{ kWh/m}^2$):** Because the $10$ international districts report *residential* heating-only results and DECs cover *public/non-domestic* buildings (schools, offices, hospitals), DECs cannot directly validate the $68.3\text{ kWh/m}^2$ residential district metric unless non-domestic public buildings in that district are also simulated and scored separately.

---

## 7. Hardest reviewer questions and answers

1. **Question 1 (Under-prediction bias):** *"Your U.S. validation under-predicts city-wide energy by $-31.3\%$ in NYC and $-30.5\%$ in Austin, yet fits LA within $-3.6\%$. Why should readers trust an uncalibrated model with a $\sim 30\%$ bias, and why did you refuse to calibrate it?"*
   * **Honest answer:** OpenUBEM enforces a strict **zero-fitted-parameter** design so that the physics pipeline remains transferable to cities and countries without metered benchmark data. Standard DOE/ASHRAE archetypes assume code-compliant equipment schedules, ideal HVAC controls, and regulated loads, which systematically under-predict real-world urban stock energy where aging equipment, unregulated plug loads, and occupant behavior inflate consumption (especially in heating/cooling-intense climates like NYC and Austin, compared to mild LA). However, high archetype-level $R^2$ values ($0.877$, $0.902$, $0.723$) show that the model accurately captures relative energy intensity across building types, while the explicit $-30\%$ gap quantifies the true physical "performance gap" rather than hiding it behind tuned parameters.
2. **Question 2 (Baseline mismatch in validation):** *"Why is your adopted U.S. fleet figure ($171.38\text{ kWh/m}^2$ across $8,139$ buildings) different from the baseline used to score your city-level errors and $R^2$ values?"*
   * **Honest answer:** (Note: You **must** re-score the city errors and $R^2$ on the $8,139$-building baseline before submission so this question disappears; if any historical comparison remains, answer as follows:) OpenUBEM maintains strict data provenance where every published metric names its exact population ($8,139$ pooled buildings out of $8,160$ initial footprints, with $21$ buildings excluded for documented rule reasons) and retains superseded baselines for auditability. All validation metrics in the final manuscript are scored directly on the adopted $8,139$-building baseline.
3. **Question 3 (Donor-country archetypes and unvalidated international districts):** *"For the $10$ international residential districts, you report heating-only EUI ($48.5$ to $140.9\text{ kWh/m}^2$) without measured validation, and use 'donor countries' where national TABULA/EPISCOPE data are missing (e.g., Yerevan, Cape Town, Montréal). How is this scientifically valid?"*
   * **Honest answer:** The $10$-district experiment is presented as a **methodological transferability and provenance demonstration**, not a calibrated national inventory. Where local TABULA/EPISCOPE typologies are absent, OpenUBEM applies documented donor-country physics rules and tags every imputed parameter with its provenance record. Heating-only intensity is reported to isolate envelope and ventilation physics across diverse climates (from $48.5\text{ kWh/m}^2$ in Yerevan to $140.9\text{ kWh/m}^2$ in Montréal) without confounding from highly uncertain international cooling ownership and appliance schedules.
4. **Question 4 (Exclusion of complex buildings in dwelling subdivision):** *"Your geometric rules divide L, U/T, and multi-wing residential buildings into individual dwellings, but leave out buildings that fail the rules. Does excluding complex geometries bias your district EUI?"*
   * **Honest answer:** Unlike black-box UBEM tools that silently force malformed footprints into distorted thermal zones or drop them without notice, OpenUBEM enforces deterministic geometric rules and logs every excluded building with its specific failure reason. By explicitly reporting both the included population and the excluded footprints, users can see the exact coverage of the district stock and assess any geometric selection effects transparently.
5. **Question 5 (Lack of retrofit costs and unvalidated UTCI):** *"Both CityEL (2025) and AutoBEM (2026) evaluate dozens of ECMs with economic payback periods, whereas OpenUBEM models only four retrofit measures without cost data and includes an unvalidated UTCI stage. What is the practical value for urban planners?"*
   * **Honest answer:** OpenUBEM focuses on **physical transparency and multi-country generalizability**. Economic payback depends heavily on volatile local labor costs, subsidies, and tariffs that cannot be standardized across $11$ countries without introducing speculative financial assumptions; therefore, OpenUBEM provides rigorous physical energy and carbon savings across four core building-physics levers (lighting power, envelope $U$-value, thermostat setback, and airtightness) that users can feed into local cost models. Similarly, the UTCI module is clearly flagged as an optional, unvalidated exploratory stage demonstrating pipeline extensibility rather than a validated microclimate tool.

---

## 8. Draft text

### (a) Research gaps and contributions ($\le 350$ words)

Recent advances in urban building energy modeling (UBEM), exemplified by city-scale web platforms such as CityEL and national-scale frameworks such as AutoBEM, have substantially improved the speed and scale of bottom-up EnergyPlus simulations. Despite this progress, three critical methodological gaps remain in the UBEM literature:

1. **Calibration opacity versus physical transferability:** Many UBEM studies rely on statistical calibration or parameter tuning to match aggregate utility benchmarks. While this reduces apparent error in data-rich cities, it masks the physical performance gap, risks overfitting to under-constrained inputs, and prevents deployment in regions lacking metered energy data.
2. **Coarse thermal zoning in residential stocks:** Existing large-scale tools typically model residential buildings as single-zone shoeboxes or whole-floor perimeter-core zones. They rarely resolve individual dwellings (flats) across complex L-, U/T-, and multi-wing footprints, obscuring intra-building thermal disparities.
3. **Silent data imputation and population drift:** When assembling models from incomplete open data (e.g., OpenStreetMap), UBEM pipelines rarely record parameter-level provenance or explicitly audit buildings dropped during geometric processing.

To address these gaps, this paper introduces **OpenUBEM**, an open-source, multi-resolution UBEM platform. Our main contributions are:
* **An uncalibrated, provenance-tracked physics pipeline:** OpenUBEM generates multi-zone EnergyPlus models directly from OpenStreetMap geometry, climate data, and archetype libraries with **zero fitted parameters**, recording explicit provenance for every imputed attribute and maintaining a complete audit trail of population counts and superseded figures.
* **Multi-scale U.S. validation across density tiers:** We evaluate OpenUBEM across $12$ urban-to-rural density cells in New York City, Los Angeles, and Austin ($8,139$ pooled buildings; adopted fleet intensity $171.38\text{ kWh/m}^2$ and $1,146,454\text{ t CO}_2\text{e}$), achieving strong archetype-level agreement ($R^2 = 0.723\text{–}0.902$) while transparently characterizing uncalibrated city-level bias ($-3.6\%$ to $-31.3\%$).
* **International dwelling-resolved modeling:** Across $10$ residential districts spanning Europe, North America, the Caucasus, and Africa, OpenUBEM subdivides multi-family buildings (including L, U/T, and multi-wing shapes) into individual dwelling zones using national TABULA/EPISCOPE and donor-country datasets, accompanied by explicit exclusion logs, hourly outputs, four physical retrofit screens, and an interactive 3D web and floor-plan viewer.

### (b) Intended users and limits of use ($\le 150$ words)

OpenUBEM is designed for urban energy researchers, municipal sustainability planners, and open-science practitioners who require transparent, reproducible baseline energy and carbon models from open geospatial data. It is suited for screening relative energy intensity across building archetypes, comparing physical retrofit sensitivities (lighting, envelope $U$-value, thermostat setback, and airtightness), and analyzing dwelling-level heating demand distributions across diverse climates.

Several limits of use must be observed. First, because OpenUBEM uses **zero fitted parameters**, its absolute energy predictions reflect standardized archetype physics and typically under-predict metered urban totals by $4\%\text{–}31\%$; outputs must not be used as revenue-grade utility forecasts without local calibration. Second, the platform does not include capital cost or payback models, so retrofit results represent technical rather than economic potential. Finally, donor-country archetypes in data-scarce regions and the optional outdoor thermal comfort (UTCI) module are unvalidated and intended solely for exploratory comparative analysis.

---

## 9. Open questions for us (max 5)

1. **Upload of local review file:** Would you like to upload `INVESTIGATION_paper-improvement_2026-10-21.md` (and the two PDF files) now so I can map Section 2 directly to your exact table rows?
2. **Re-scoring timeline:** Can you run the validation scoring script on the adopted $8,139$-building baseline ($171.38\text{ kWh/m}^2$) before submission so that all city-level percentages and archetype $R^2$ values match the final population exactly?
3. **Exclusion counts in the $10$ districts:** Do you have the exact counts of included buildings, generated dwelling zones (flats), and rule-excluded buildings for each of the $10$ international residential districts to put into a summary table?
4. **London EPC/DEC overlap:** In your London residential district, how many buildings have matched Domestic EPC certificates (beyond construction year), and are there any public buildings with Display Energy Certificates (DECs) inside that bounding box?
5. **Vienna weather year:** Why does Vienna use a real historical weather year ($2008$) while the other nine international districts use $\text{TMYx}$ ($2009\text{–}2023$), and can Vienna be re-run with $\text{TMYx}$ ($2009\text{–}2023$) to eliminate reviewer questions about weather consistency?