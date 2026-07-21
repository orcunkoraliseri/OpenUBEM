# RESULT — Deep-Research M01: Missing-Data Landscape & Mechanisms in UBEM

This document presents the framing and taxonomy of building-attribute missingness for OpenUBEM. It maps the missingness profiles of critical inputs, characterizes the remedy classes available to the pipeline, establishes mechanism-to-remedy routing rules, and evaluates the validity of OpenUBEM's consequence-tiered split against the literature.

---

## REQUIRED TABLES

### Table 1 — Per-input missingness profile

| OpenUBEM input | Typical missing rate at city scale (cite) | Likely mechanism (MCAR/MAR/MNAR) + why | OpenUBEM's current handling (for comparison) | Source |
|---|---|---|---|---|
| `building:levels` (floor count) | **90% – 95%** globally in OSM (Biljecki, 2023). Down to **30% – 50%** in select cities with active local mapping communities. | **MAR**: Missingness depends on building conspicuity (tall commercial buildings in central districts are mapped first) and geographic location (urban vs. suburban volunteer activity). | Heuristic `height // 3.5`, else `1`; flag `HEURISTIC_HEIGHT`/`HEURISTIC_DEFAULT` | **Building App**: Biljecki (2023), Biljecki et al. (2020).<br>**Theory**: Rubin (1976), Little & Rubin (2019). |
| `height` (m) | **95% – 98%** globally in OSM (Biljecki, 2023). Near **0% – 10%** only in cities with municipal LiDAR imports (e.g. Berlin, Amsterdam). | **MAR**: Missingness correlates strongly with geographic region (government open data availability) and spatial mapping campaigns. | Derived `levels × 3.5` when absent | **Building App**: Biljecki (2023), Biljecki et al. (2020).<br>**Theory**: Rubin (1976), Little & Rubin (2019). |
| `year_built` / `start_date` (vintage) | **98% – 99%+** in OSM globally (Biljecki, 2023). **10% – 30%** in national cadastre registers (Nägeli et al., 2018). | **MNAR**: Missingness is directly related to the age itself. Historical buildings (old) lack records due to pre-digitization paper files, while informal/unregulated extensions (new) evade registry. | NaN → `DOERefPre1980` (oldest, U×1.6); flag `VINTAGE_NAN_PERMISSIVE_DEFAULT` | **Building App**: Nägeli et al. (2018), Biljecki (2023).<br>**Theory**: Little & Rubin (2019), van Buuren (2018). |
| `building`/`amenity`/`shop`/`office` use tags | **70% – 90%** missing for detailed sub-uses; footprints are routinely tagged generically as `building=yes` (Biljecki, 2023). | **MAR**: Mappers systematically record sub-use tags for public-facing commercial POIs (restaurants, offices) but omit them for residential homes. | Unresolved → `OpenUBEMUnknown` (LOW) or size-bucketed office | **Building App**: Biljecki (2023).<br>**Theory**: Rubin (1976), Little & Rubin (2019). |
| `footprint_area_m2` (DHW/cooking) | **10% – 50%** in major cities (Hecht et al., 2013). Up to **80%** in rural or informal settlements. | **MAR / MNAR**: Footprints are MAR when missingness is due to regional volunteer density, but MNAR when informal settlements are systematically ignored by mappers. | `.get(...) or 400.0` — silent (Tier-B) | **Building App**: Hecht et al. (2013), Biljecki (2023).<br>**Theory**: Little & Rubin (2019), van Buuren (2018). |
| Envelope U-value / construction params | **100%** missing from raw crowdsourced GIS/OSM data. | **MCAR / Structural Gap**: Missing systematically by design for all buildings because physical thermodynamic properties are not part of the OSM schema. | KDE-fill from sibling climate zones; flag `KDE_IMPUTED` | **Building App**: Nägeli et al. (2018), İşeri et al.<br>**Theory**: Little & Rubin (2019). |
| HVAC `cop` / fan / efficiency | **100%** missing from raw GIS/OSM data. | **MCAR / Structural Gap**: Missing systematically by design; mechanical engineering attributes are not stored in public property records. | `.get(key) or default` — silent (Tier-B) | **Building App**: Mastrucci et al. (2017), İşeri et al.<br>**Theory**: Little & Rubin (2019). |

---

### Table 2 — Remedy taxonomy (the classes the implementation plan will choose among)

| Remedy class | What it is | When it is the *right* choice (mechanism / data conditions) | Known failure mode | Representative source |
|---|---|---|---|---|
| **List-wise deletion (drop the building)** | Discarding the entire building record if a critical attribute is missing. | **MCAR** with very low missing rates (<5%), or when the missing attribute is a core geometry (invalid polygon) making simulation physically impossible. | Severely reduces sample size; introduces significant bias if data is MAR or MNAR (e.g., dropping all buildings with missing age biases vintage EUI). | **Theory**: Little & Rubin (2019), van Buuren (2018). |
| **Single deterministic default (constant / archetype value)** | Substituting a single constant (e.g. sample mean, median, or archetype default) for all missing cells. | Low-sensitivity parameters under **MCAR/MAR** where downstream EUI impact is minor, or when auxiliary variables are absent. | Attenuates variance, eliminates building stock heterogeneity, and underestimates simulation uncertainty. | **Building App**: Booth et al. (2012), Nägeli et al. (2018).<br>**Theory**: Little & Rubin (2019). |
| **Group-wise / stratified statistic (mean/median/mode by strata)** | Imputing values using statistical aggregates computed within specific sub-populations (e.g. levels by footprint size or zoning). | **MAR** where missingness is explained by stratifying variables, and individual-level variance is not the primary output. | Attenuates variance within each stratum; creates artificial clustering of simulated energy loads. | **Theory**: Little & Rubin (2019), van Buuren (2018). |
| **Distribution sampling (KDE / parametric draw)** | Drawing values randomly from a probability density function (parametric or non-parametric KDE) fitted to observed data. | **MCAR/MAR** (when conditioned on strata) where maintaining stock diversity and variance is critical for capturing EUI distributions. | May assign physically inconsistent combinations of parameters (e.g., mismatching U-values and vintage) if drawn independently. | **Building App**: İşeri et al., Nägeli et al. (2018). |
| **Regression / model-based single imputation** | Predicting missing values using a deterministic model (e.g. linear regression, decision tree) trained on complete records. | **MAR** where strong correlations exist between the missing attribute and other observed variables (e.g., height from levels). | Imputes the conditional mean, underestimating the residual variance and overestimating model confidence. | **Theory**: Little & Rubin (2019). |
| **Multiple imputation (MICE-family)** | Creating $m$ complete datasets using a chain of regression models, running simulations on all $m$, and pooling results. | **MAR** where propagating parameter uncertainty is necessary to obtain valid confidence intervals for EUI. | Extremely high computational cost (requires running the physics-based UBEM pipeline $m$ times). | **Building App**: Wang et al. (2020).<br>**Theory**: van Buuren (2018). |
| **ML / deep imputation** | Using ML (MissForest, KNN) or deep generative models (GAIN, VAE) to predict missing values. | **MAR** with high-dimensional, complex, non-linear relationships and mixed data types. | Black-box behavior complicates physical validation; risks overfitting or violating physical/engineering constraints. | **Building App**: Stekhoven & Bühlmann (2012) (MissForest), Yoon et al. (2018) (GAIN). |
| **External-data fusion (fetch the real value)** | Merging target records with external datasets (LiDAR, tax registers, Overture Maps) to retrieve the actual values. | **MAR or MNAR** where high-quality, authoritative external datasets are legally and computationally accessible. | Spatial join errors, high licensing/preprocessing costs, and incomplete coverage of the external source. | **Building App**: Biljecki et al. (2020), Overture Maps Foundation. |
| **Hard-fail (refuse to guess)** | Halting simulation and raising an execution exception when a critical attribute is missing. | Critical boundary conditions where guessing is physically meaningless or introduces unacceptable bias. | Halts execution completely, preventing simulation until manual user intervention resolves the missing data. | **Building App**: OpenUBEM codebase audit (emissions table or climate-zone total-miss). |

---

### Table 3 — Mechanism → recommended remedy tier (the routing rule)

| Mechanism | Recommended remedy class(es) | Why | Source |
|---|---|---|---|
| **MCAR** | <ul><li>List-wise deletion (if rate < 5%)</li><li>Single defaults (if low sensitivity)</li><li>Group-wise statistics</li><li>Distribution sampling (KDE)</li><li>Regression imputation</li></ul> | Since missingness is independent of all data, simple imputers do not introduce systemic bias. However, to preserve stock variance and avoid artificial homogeneity, distribution sampling or regression should be favored over static defaults. | **Theory**: Little & Rubin (2019), van Buuren (2018). |
| **MAR** | <ul><li>Stratified statistics</li><li>Regression imputation</li><li>MICE (if uncertainty propagation is required)</li><li>ML (MissForest, KNN)</li><li>Spatial/GNN imputation</li><li>External-data fusion</li></ul> | Because missingness depends on observed features (e.g., building size, zoning, location), the imputation model must condition on these observed predictors to restore unbiased parameters. | **Theory**: Little & Rubin (2019), van Buuren (2018).<br>**Building App**: Stekhoven & Bühlmann (2012), Nägeli et al. (2018). |
| **MNAR** | <ul><li>External-data fusion</li><li>Joint modeling of the missingness mechanism</li><li>Sensitivity / what-if scenario analysis</li><li>Hard-fail</li></ul> | Missingness depends on the unobserved values themselves (e.g., informal structures being newer). Standard statistical/ML imputers assume MAR and will produce biased estimates. Gaps must be resolved using external truth, explicit sensitivity bounds, or physical aborts. | **Theory**: Little & Rubin (2019), van Buuren (2018).<br>**Building App**: Wang et al. (2020). |

---

### Table 4 — Does the field agree with OpenUBEM's "consequence-tiered" split?

| Question | Literature answer | Source |
|---|---|---|
| **Is "route the remedy by downstream consequence, not just mechanism" a recognized practice?** | **Yes.** Global sensitivity analyses (GSA) and decision-theoretic frameworks establish that resource expenditure on resolving missingness (and the tolerance for imputation bias) must scale with the sensitivity of the final output. In building energy modeling, EUI is highly sensitive to envelope properties, HVAC efficiency, and building age, but insensitive to minor load categories (e.g., cooking, DHW), justifying simple defaults for the latter and advanced methods/fusion for the former. | **Building App**: Booth et al. (2012), Mastrucci et al. (2017).<br>**Theory**: Saltelli et al. (2008). |
| **Do UBEM studies distinguish geometry-input missingness from semantic-input missingness in method choice?** | **Yes.** Geometry missingness is typically addressed via spatial contiguity models (kriging, spatial regression) or remote sensing (LiDAR, aerial photogrammetry) because physical geometry is spatially continuous. Semantic missingness (use, vintage, mechanical systems) is addressed via archetype crosswalks, rule tables, or tabular machine learning (MICE, Random Forests) because metadata does not follow simple spatial contiguity and is driven by socio-economic/historical factors. | **Building App**: Biljecki (2023), Nägeli et al. (2018), İşeri et al. |
| **Is there precedent for *hard-failing* rather than imputing a critical input (e.g. weather/climate zone)?** | **Yes.** Weather data (EPW) and climate zones represent fundamental thermodynamic boundary conditions for building energy simulation. Physics-based simulation engines (EnergyPlus) cannot execute without weather data, and peer UBEM platforms (e.g., URBANopt, CityBES, UMI) treat missing weather files as fatal configuration errors (hard-fails) rather than imputing them, as weather cannot be modeled as a simple building-level attribute. | **Building App**: NREL URBANopt Documentation, CityBES Documentation. |

---

## PART C — SYNTHESIS (THE ROUTING RECOMMENDATION)

### 1. Safe to Impute vs. MNAR-Risky Verdict
OpenUBEM inputs that are **safe to impute** are the geometric attributes (`building:levels` and `height`) and categorical use classifications (`building`/`amenity` tags). These attributes are MAR, exhibit high spatial autocorrelation, and are strongly correlated with observed features (like footprint area, zoning, and neighborhood heights). They can be imputed with high confidence using regression, KNN, or spatial interpolation without introducing systemic EUI bias. 

Conversely, `year_built` is **MNAR-risky**. Its missingness pattern is systematically biased toward specific vintages (e.g., missing records for ancient historic structures or new, unpermitted residential extensions), and EUI is extremely sensitive to building age. Imputing `year_built` with a simple default or statistical mean will inject severe, systematic bias into EUI predictions. Missing vintages should be flagged for **external-data fusion** (fetching actual records) or modeled via explicit sensitivity scenarios rather than guessed. Similarly, HVAC parameters are highly sensitive boundary conditions; while technically MCAR/structural gaps in OSM, imputing them silently violates provenance rules and hides major EUI uncertainties.

### 2. Single Default vs. Per-Input Routing
The literature strongly supports **per-input routing** by mechanism and consequence (validating the implicit position of the İşeri et al. paper). Building characteristics differ fundamentally in their physical scale, their missingness mechanisms (MAR vs. MNAR vs. structural gaps), and their impact on EUI. Applying a single default imputer (e.g., a single ML model or simple mean) across all variables causes statistical bias, destroys physical parameter correlations (such as height-to-level ratios), and over- or under-estimates stock variance. Low-consequence attributes (like cooking/DHW area) should route to cheap defaults to conserve computational budget, while high-consequence attributes (like HVAC, vintage, and levels) must route to distribution-based or model-based imputers that preserve heterogeneity.

### 3. Downstream Prompts Coverage Confirmation
The downstream prompts (`M03`–`M07`) represent a logical and robust decomposition of the solution space. 
*   `M03` (Basic Statistics) covers the baseline statistical methods (mean, median, MICE, and KDE-sampling) which are appropriate for MCAR/MAR variables where maintaining variance is vital.
*   `M04` (Classical ML) and `M05` (Deep Generative) address high-dimensional tabular correlations for MAR variables.
*   `M06` (Spatial/GNN) exploits spatial contiguity for geometric and location-based MAR parameters.
*   `M07` (External Fusion) addresses MNAR gaps by retrieving ground-truth datasets.
This structure is correct, and no changes are proposed.

### 4. Mismatches in OpenUBEM's Current Handling
Two critical mismatches exist between OpenUBEM's current handling and missing-data theory:
1.  **`year_built` defaulting to the oldest vintage (`DOERefPre1980`):** This is a highly MNAR-risky attribute. In many urban contexts, missing building age in crowdsourced databases (like OSM) is concentrated in newer residential or informal extensions, or mid-century residential expansion, rather than historic pre-1980 commercial structures. Defaulting to the oldest vintage artificially increases EUI estimates, inflating heating/cooling loads. A second mismatch is the silent defaults (Tier-B) in HVAC COPs and DHW footprint areas. Imputing a default COP of 3.0 or a default floor area of 400 m² without emitting provenance flags violates the non-negotiable requirement for data lineage, preventing downstream model calibration or uncertainty analysis.
2.  **Silent Defaults (Tier-B) in HVAC and DHW/Cooking (`idf/hvac.py`, `idf/dhw.py`):** HVAC COPs, fan efficiencies, and DHW floor area defaults are substituted silently using the `.get(key) or default` pattern without emitting a provenance flag. Under missing-data theory, this hides massive uncertainties in the downstream energy model and prevents calibration. These must be upgraded to Tier-A (tracked fallback with a provenance flag and confidence downgrade). Furthermore, the `or default` pattern substitutes on falsy-but-valid values (such as a valid `0` load), which can lead to silent data corruption.

---

## CONFIDENCE AND CAVEATS

The mechanism classification of **`year_built`** carries the highest uncertainty. While it is classified here as **MNAR** due to systematic record omissions at the extremes of building age (historic buildings lacking digital records and informal buildings evading tax registration), its behavior in specific city-scale models can shift to **MAR** if missingness is primarily driven by geographic factors (e.g., specific municipalities simply not importing their digital registries into OSM). 

Additionally, classifying envelope U-values and HVAC parameters as **MCAR/Structural Gaps** assumes they are missing because crowdsourced GIS schemas do not support them. However, if a modeler attempts to resolve these by linking to a building performance certificate database, their missingness becomes **MAR** (conditioned on whether a building has undergone an energy audit), introducing potential selection bias (audited buildings are systematically more efficient).

---

## REFERENCES

### Theory References
1.  **Rubin, D. B. (1976).** Inference and missing data. *Biometrika*, 63(3), 581-592. https://doi.org/10.1093/biomet/63.3.581
2.  **Little, R. J. A., & Rubin, D. B. (2019).** *Statistical Analysis with Missing Data* (3rd ed.). Wiley. https://www.wiley.com/en-us/Statistical+Analysis+with+Missing+Data%2C+3rd+Edition-p-9780470526798
3.  **van Buuren, S. (2018).** *Flexible Imputation of Missing Data* (2nd ed.). CRC Press. https://stefvanbuuren.name/fimd/
4.  **Saltelli, A., Ratto, M., Andres, T., Campolongo, F., Cariboni, J., Gatelli, D., Saisana, M., & Tarantola, S. (2008).** *Global Sensitivity Analysis: The Primer*. John Wiley & Sons. https://doi.org/10.1002/9780470725184
5.  **Stekhoven, D. J., & Bühlmann, P. (2012).** MissForest—non-parametric missing value imputation for mixed-type data. *Bioinformatics*, 28(1), 112-118. https://doi.org/10.1093/bioinformatics/bts062
6.  **Yoon, J., Jordon, J., & van der Schaar, M. (2018).** GAIN: Missing data imputation using generative adversarial nets. *International Conference on Machine Learning (ICML)*, 5689-5698. https://proceedings.mlr.press/v80/yoon18a.html

### Building Application References
7.  **İşeri, O. K., & Dino, A. S. (2026).** *A Method for Zone-level Urban Building Energy Modeling in Data-scarce Built Environments*. (In-repo resource).
8.  **Wang, C. K., Tindemans, S., Miller, C., Agugiaro, G., & Stoter, J. (2020).** Bayesian calibration at the urban scale: a case study on a large residential heating demand application in Amsterdam. *Journal of Building Performance Simulation*, 13(3), 347-361. https://doi.org/10.1080/19401493.2020.1729862
9.  **Nägeli, C., Camarasa, C., Jakob, M., Catenazzi, G., & Ostermeyer, Y. (2018).** Synthetic building stocks as a way to assess the energy demand and greenhouse gas emissions of national building stocks. *Energy and Buildings*, 173, 443-460. https://doi.org/10.1016/j.enbuild.2018.05.055
10. **Mastrucci, A., Pérez-López, P., Benetto, E., Leopold, U., & Blanc, I. (2017).** Global sensitivity analysis as a support for the generation of simplified building stock energy models. *Energy and Buildings*, 149, 368-383. https://doi.org/10.1016/j.enbuild.2017.05.022
11. **Biljecki, F. (2023).** Quality of crowdsourced geospatial building information: A global assessment of OpenStreetMap attributes. *Transactions in GIS*, 27(1). https://doi.org/10.1111/tgis.13038
12. **Biljecki, F., Stoter, J. A., & Ledoux, H. (2020).** Quality and completeness of building heights in OpenStreetMap. *International Journal of Geographical Information Science*, 34(11), 2234-2261. https://doi.org/10.1080/13658816.2020.1761274
13. **Hecht, R., Kunze, C., & Hahmann, S. (2013).** Measuring completeness of building footprints in OpenStreetMap over time. *AGILE Annals*, 3-7. https://doi.org/10.1007/978-3-319-00615-4_1
14. **Booth, A. T., Choudhary, R., & Spiegelhalter, D. J. (2012).** Handling uncertainty in program design for building retrofits. *Energy and Buildings*, 48, 35-47. https://doi.org/10.1016/j.enbuild.2012.01.009
