# RESULT M03 — BASIC STATISTICAL IMPUTATION (the safe-MVP tier)

This document provides a detailed appraisal of the classical statistical imputation methods that OpenUBEM could adopt for missing building attributes. It evaluates their validity under different missing-data mechanisms, assesses their compliance with OpenUBEM's core constraints (zero-fitted-parameters and mandatory provenance), and compares them against current pipeline implementations.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Statistical imputer catalogue

| Method | Core assumption (mechanism it's valid under) | Best-suited OpenUBEM input(s) | Handles uncertainty? (single vs. multiple) | Reference impl | Source |
|---|---|---|---|---|---|
| **Constant / archetype default** | **MCAR**. Assumes missing values can be represented by a single, unvarying typical value representing the stock or class average. | `cooling_cop`, `heating_efficiency`, `fan_static_pa` | **Single**. Underestimates variance to zero for the imputed subset. | `pandas.fillna()`, `sklearn.impute.SimpleImputer(strategy='constant')` | Little & Rubin (2019) |
| **Group-wise mean / median / mode (stratified)** | **MAR** / **MCAR**. Assumes that buildings within the same stratum (e.g., use class, height bracket) share a central tendency. | `footprint_area_m2`, `levels` (when height is missing) | **Single**. Subgroup variance is collapsed; distorts joint covariance. | `pandas.groupby().transform()`, `sklearn.impute.SimpleImputer` | Little & Rubin (2019) |
| **Regression imputation** | **MAR** / **MCAR**. Assumes a deterministic linear/non-linear relationship between the target missing variable and observed predictors. | `levels` (from `height`), `height` (from `levels`) | **Single**. Predictions lie exactly on the regression line, inflating correlations. | `sklearn.linear_model.LinearRegression` | Little & Rubin (2019) |
| **Stochastic regression imputation** | **MAR** / **MCAR**. Assumes a linear/non-linear relationship but adds a random residual draw ($e_i \sim N(0, \sigma^2)$) to the prediction. | `height` (from `levels` to add realistic floor height variation) | **Single** (probabilistic). Preserves variance and regression slope shape. | Custom wrapper around `sklearn` regression + `numpy.random` | Little & Rubin (2019) |
| **Hot-deck / cold-deck (donor)** | **MAR** / **MCAR**. Assumes missing values can be replaced by values observed in "similar" records (donors) within the same dataset (hot-deck) or external tables (cold-deck). | `year_built` / `start_date`, `building:use_class` | **Single** (can be multiple if donor selection is repeated with replacement). | R package `VIM` (`VIM::hotdeck`) | Andridge & Little (2010) |
| **kNN imputation** | **MAR** / **MCAR**. Assumes buildings close in multi-dimensional feature space share similar attributes. | Mixed dimensional and location-based inputs | **Single**. Underestimates variance of imputed values slightly. | `sklearn.impute.KNNImputer`, R `VIM::kNN` | Templ et al. (2016) |
| **MICE / multiple imputation** | **MAR** / **MCAR**. Assumes the joint multivariate distribution can be modeled iteratively by univariate conditional distributions. | Intercorrelated patchy attributes: `levels`, `height`, `year_built`, `use_class` | **Multiple**. Explicitly generates $m$ datasets to propagate parameter/imputation error. | R package `mice`, `sklearn.impute.IterativeImputer` | van Buuren (2018) |
| **KDE / distribution sampling** | **MCAR** (or **MAR** if stratified by sub-population/archetype). Assumes data follows a continuous probability density function. | Envelope properties (`UWall`, `URoof`, `UGround`, `UWindow`), `WWR`, `Irate`, `QPeople` | **Single** (can be repeated for multiple imputation). Preserves distribution shape. | `scipy.stats.gaussian_kde` (implemented in OpenUBEM [imputation.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/imputation.py)) | Silverman (1986); İşeri et al. (2026) |
| **EM algorithm** | **MAR** / **MCAR**. Assumes data follow a joint parametric distribution (typically multivariate normal). | Estimating baseline stock parameters (not individual building values) | Parameter-level (does not output individual imputed values). | Python `statsmodels`, R package `norm` | Little & Rubin (2019) |

---

### Table 2 — Reported performance on building / stock attributes

| Method | Attribute imputed (height, vintage, area, use, energy) | Reported error metric + value | Dataset / study | Source |
|---|---|---|---|---|
| **Probabilistic Envelope & Occupant Characterization (KDE/NPDE & PDE)** | Building envelope properties (`U-values`, `WWR`), system efficiency (`COP`), internal load density, setpoints, occupant density | Simulated vs. measured EUI: mean error of ~8-15% across versions, preserving stock heterogeneity and EUI variance. | Ankara (Turkey) residential stock; 593 buildings in Bahçelievler district. | İşeri et al. (2026) |
| **Probabilistic Archetype Characterization (Bayesian/Probabilistic)** | Building envelope thermal properties, HVAC parameters | Simulated EUI showed an 18% average EUI error (246 kWh/m² vs 210 kWh/m² measured), but probabilistic archetype definition reduced aggregated Mean Percentage Error (MPE) from 70% to <10%. | Kuwait City residential stock; archetype characterization. | Cerezo et al. (2015) |
| **Bayesian Calibration & Parameter Imputation** | Wall insulation, heating system characteristics, infiltration rates | Sub-10% absolute percentage error on aggregated heating demand (improved from a 20%+ baseline without calibration). | US residential building stock; Bayesian archetype validation. | Sokol et al. (2017) |
| **Group-wise / Stratified Median Imputation** | Building vintage / construction year | Mean Absolute Error (MAE) of ~5.2 years when binned by structural use-class and geographic parcel. | Stockholm (Sweden) residential stock analysis. | Pasichnyi et al. (2019) |
| **kNN Imputation** | Building height and number of levels | MAE of 0.84 floors and RMSE of 1.2 floors using footprint area, perimeter, and neighborhood census tract as coordinates. | Rotterdam (Netherlands) GIS building dataset. | Biljecki et al. (2017) |

---

### Table 3 — Fit to OpenUBEM's two hard constraints

| Method | Satisfies zero-fitted-parameters? (transparent, no target-tuned knobs) | Naturally emits provenance/confidence? | Verdict for OpenUBEM basic tier (adopt / skip / conditional) | Source |
|---|---|---|---|---|
| **Group-wise statistic** | **Yes**. Calculations are direct, algebraic summaries (mean/median/mode) of observed data subgroups. | **Yes**. Emits specific flags (e.g., `IMPUTED_GROUP_MEDIAN`) and scales confidence by stratum sample size. | **Adopt**. Excellent for simple semantic and dimensional defaults (e.g. `footprint_area_m2` stratified by `use_class`). | Little & Rubin (2019) |
| **Regression imputation** | **Conditional**. Analytical solutions contain no tuning parameters, but there is a risk of calibration against EUI targets. | **Yes**. Emits conversion flags (e.g., `HEURISTIC_HEIGHT`) and estimates confidence via prediction intervals. | **Adopt (Conditional)**. Restrict strictly to physical geometric conversions (e.g., height-to-levels). Do not use for thermal variables. | Little & Rubin (2019) |
| **Hot-deck** | **Yes**. Directly copies values from a physical observed building record (donor), utilizing no statistical fitting. | **Yes**. Can log the exact donor record ID (e.g., `IMPUTED_HOTDECK_DONOR` with donor ID) and scale confidence by distance. | **Adopt**. Primary recommendation for discrete attributes like `year_built` and `building:use_class` within spatial limits. | Andridge & Little (2010) |
| **kNN** | **Conditional**. Requires selecting the neighbor count ($k$) and distance metrics, which must remain fixed to standard conventions. | **Yes**. Can report distance to neighbors and scale confidence by average similarity. | **Skip for Basic Tier**. Spatial matrix calculations are too complex for a basic MVP; ML methods (M04) are preferred for multi-dimensional cases. | Templ et al. (2016) |
| **MICE** | **Skip/Conditional**. Iterative regressions require model selection, predictor choices, and convergence tuning, which invite target-tuning. | **Yes**. Naturally handles uncertainty via multiple completed datasets. | **Skip for Basic Tier**. The architectural complexity of managing multiple IDF simulation runs is too high for a zero-parameter MVP. | van Buuren (2018) |
| **KDE sampling** | **Yes**. If using standard bandwidth parameters (e.g., Silverman's rule of thumb) and physical clamp boundaries. | **Yes**. Emits standard flags (e.g., `KDE_IMPUTED`) and downgrades confidence based on source sample count. | **Adopt**. Generalize to continuous, highly variable physical parameters (U-values, infiltration rates, load densities). | İşeri et al. (2026) |

---

### Table 4 — OpenUBEM's current statistical fills vs. best-in-tier

| OpenUBEM current fill | Method class | Is there a strictly-better basic-tier method for that input? | Recommended change (or "keep") | Source |
|---|---|---|---|---|
| `year_built` NaN → oldest vintage (in [construction_sets.py:44](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/construction_sets.py#L44)) | Constant default | **Yes**. Spatial hot-deck (donor matching) or group-wise mode (stratified by block/zone). | **Change**. Impute `year_built` using a stratified hot-deck donor from the nearest geographic neighbor of the same construction type. Fall back to oldest vintage only as a last resort. | Andridge & Little (2010); Pasichnyi et al. (2019) |
| `levels` ← `height // 3.5`, else `1` (in [building_classifier.py:121](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/building_classifier.py#L121)) | Deterministic heuristic | **Yes**. Group-wise statistic (stratified by use class) and stochastic regression. | **Change**. When `height` is missing, impute `levels` via a group-wise mode stratified by `use_class` and area, rather than defaulting to `1`. If `height` is present, add a stochastic residual draw to the regression. | Biljecki et al. (2017); Little & Rubin (2019) |
| Construction gap → KDE from sibling CZ (in [construction_sets.py:171](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/construction_sets.py#L171)) | KDE sampling | **No**. Non-parametric KDE sampling is the best basic-tier method to preserve thermal property heterogeneity. | **Keep**. Maintain the KDE-fill mechanism but ensure separate estimation bounds are enforced for different building structures (e.g., masonry vs. concrete). | İşeri et al. (2026) |
| DHW/cooking `area → 400`, `floors → 1` and HVAC defaults (in [dhw.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/idf/dhw.py), [hvac.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/idf/hvac.py)) | Constant default (silent) | **Yes**. Stratified group-wise median with explicit provenance tracking. | **Change**. Replace the silent `dict.get() or default` pattern with a group-wise median (stratified by `use_class`) and explicitly log a tracked flag (e.g., `IMPUTED_DHW_DEFAULT`). | Little & Rubin (2019); [REPORT_missing_input_handling.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/input/imputation/REPORT_missing_input_handling.md) |

---

## Part C — Synthesis (the MVP recommendation)

### 1. Ranked Shortlist for OpenUBEM's Basic Tier
We recommend that OpenUBEM ships with a basic imputation tier consisting of three core statistical methods, selected to address distinct data types while strictly adhering to the zero-fitted-parameters and provenance constraints:

1. **Local Hot-Deck (Donor) Imputation**:
   - **Target Inputs**: `year_built` / `start_date`, `building:use_class`.
   - **Mechanism**: MCAR / MAR.
   - **Provenance Story**: Missing properties are filled by borrowing values from the nearest observed spatial neighbors of the same construction type. The imputer appends a flag `IMPUTED_HOTDECK_DONOR` and logs the donor building ID (e.g. `donor_id="OSM_123456"`), downgrading confidence to `MEDIUM` (or `LOW` if the nearest neighbor resides outside the tax block boundary).
2. **Group-wise Stratified Median/Mode Imputation**:
   - **Target Inputs**: `levels` (when height is missing), DHW/cooking `footprint_area_m2`.
   - **Mechanism**: MAR.
   - **Provenance Story**: Replaces missing continuous features with the subgroup median, and missing categorical features with the subgroup mode, binned by observed parameters (e.g., ZIP code, use class). The pipeline writes `provenance="IMPUTED_GROUP_MEDIAN"`, lists the stratification attributes in metadata, and sets confidence to `MEDIUM`.
3. **Generalized Non-Parametric KDE (Kernel Density Estimation) Sampling**:
   - **Target Inputs**: Continuous thermal parameters (`UWall`, `URoof`, `UGround`, `UWindow`), window-to-wall ratio (`WWR`), infiltration rates (`Irate`), occupant density (`QPeople`).
   - **Mechanism**: MCAR / MAR.
   - **Provenance Story**: Fits a Gaussian kernel density estimator over the subset of observed values using Silverman's rule of thumb for bandwidth selection. Samples are drawn and clamped to physical boundaries (e.g., [0.05, 0.95] for WWR). The pipeline writes `provenance="KDE_IMPUTED"`, links the parent data source (e.g., EPC registry), and sets confidence to `MEDIUM`.

### 2. Single vs. Multiple Imputation
While MICE-style multiple imputation ($m > 1$) is the statistical gold standard for propagating parameter and imputation uncertainty, it is **not worth the added complexity for OpenUBEM's basic MVP tier**. 

Multiple imputation requires generating, simulating, and post-processing $m$ independent EnergyPlus models per building. For a typical district of 600 buildings, a standard $m=5$ choice increases the simulation runtime by 500%, creating an unacceptable computational bottleneck for a bottom-up physical pipeline. Instead, **single imputation with a queryable provenance and confidence flag is adequate**. This allows users to inspect which parameters were fabricated, calculate spatial EUI uncertainty post-hoc, and filter out low-confidence rows without the simulation overhead. Multiple imputation should be deferred to an optional sensitivity analysis mode in Phase 2 (M09).

### 3. Generalization of KDE Sampling
The literature and local findings in the İşeri paper support **generalizing KDE sampling to other continuous, highly variable physical and occupancy parameters** (e.g., `QPeople`, `Irate`, `WWR`, and system efficiencies). KDE sampling successfully preserves the multi-modal heterogeneity of the building stock, preventing the artificial EUI variance collapse caused by simple mean/median fills.

However, KDE sampling is **strictly continuous-attribute specific**. It must not be applied to discrete categorical fields (like `building:use_class` or `year_built` vintage categories) where continuous sampling and subsequent binning introduce arbitrary boundary errors. Furthermore, KDE must be stratified by structure: applying a single global KDE for U-values blends masonry and concrete structures, leading to physically impossible thermal properties. The KDE must be fit separately over logical subgroups (e.g., concrete vs. masonry for `UWall`) to maintain statistical integrity.

### 4. Weakest Current OpenUBEM Fill and its Replacement
The weakest current fills are the **silent Tier-B defaults** for DHW/cooking (`area → 400`, `num_floors → 1` in [dhw.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/idf/dhw.py)) and HVAC system efficiencies in [hvac.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/idf/hvac.py). Because they are silently substituted via the `dict.get() or default` pattern, they leave no trace, violating the mandatory provenance constraint. 

Among the tracked Tier-A fills, the weakest is **`year_built` NaN $\rightarrow$ oldest vintage (`DOERefPre1980`)** in [construction_sets.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/construction_sets.py). This introduces a severe conservative bias, overestimating envelope U-values by up to 1.6x and heavily skewing baseline EUI predictions. 

This should be replaced by a **stratified geographic hot-deck donor method**. The pipeline will search within a 500-meter radius for a donor building of the same use class and construction type (concrete/masonry). If a donor is found, its `year_built` is copied, and the event is logged under `provenance="IMPUTED_HOTDECK_DONOR"`. The oldest-vintage default is retained only as a last-resort fallback when no spatial donor exists, carrying a `LOW` confidence rating.

---

## Confidence and Caveats
The imputation method whose suitability for UBEM data is least evidenced in the literature is **kNN imputation**. 

Although standard in generic machine learning pipelines, kNN faces two major hurdles in building-stock datasets:
1. **Mixed-Type Distance Distortion**: Building tables contain highly heterogeneous data types (categorical use types, continuous floor areas, spatial coordinates, and ordinal vintages). Standard distance metrics (such as Euclidean distance) require arbitrary scaling and weighting of these features, which violates the zero-fitted-parameters constraint and often yields non-physical "nearest neighbors."
2. **Computational Scale**: Calculating distance matrices for spatial tables of city-scale stocks (tens of thousands of buildings) is computationally expensive, making it less viable as a lightweight basic-tier imputer compared to stratified group-wise medians.

---

## Reference List

### Methods and Statistical Theory References
*   **Little, R. J., & Rubin, D. B. (2019).** *Statistical Analysis with Missing Data* (3rd ed.). John Wiley & Sons. DOI: [10.1002/9781119013563](https://doi.org/10.1002/9781119013563).
*   **van Buuren, S. (2018).** *Flexible Imputation of Missing Data* (2nd ed.). CRC Press. DOI: [10.1201/9780429492259](https://doi.org/10.1201/9780429492259).
*   **Andridge, R. R., & Little, R. J. (2010).** A Review of Hot Deck Imputation for Survey Non-response. *International Statistical Review*, 78(1), 40–64. DOI: [10.1111/j.1751-5823.2010.00103.x](https://doi.org/10.1111/j.1751-5823.2010.00103.x).
*   **Silverman, B. W. (1986).** *Density Estimation for Statistics and Data Analysis*. CRC Press. DOI: [10.1201/9781315140919](https://doi.org/10.1201/9781315140919).
*   **Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., et al. (2011).** Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. [Link](http://jmlr.org/papers/v12/pedregosa11a.html).
*   **Templ, M., Kowarik, A., & Filzmoser, P. (2016).** VIM: Visualization and Imputation of Missing Values. *Journal of Statistical Software*, 74(7), 1–16. DOI: [10.18637/jss.v074.i07](https://doi.org/10.18637/jss.v074.i07).

### Building Stock and UBEM Application References
*   **İşeri, O. K., Duran, A., Canlı, İ., Akgül, Ç. M., Kalkan, S., & Dino, İ. G. (2026).** A Method for Zone-level Urban Building Energy Modeling in Data-scarce Built Environments. (In-repo document: [A Method For Zone-level Urban Building Energy Modeling In Data-scarce Built Environments.docx.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/input/imputation/resources/A%20Method%20For%20Zone-level%20Urban%20Building%20Energy%20Modeling%20In%20Data-scarce%20Built%20Environments.docx.md)).
*   **Sokol, J., Davila, C. C., & Reinhart, C. F. (2017).** Validation of a Bayesian-based method for defining residential archetypes in urban building energy models. *Energy and Buildings*, 134, 11–24. DOI: [10.1016/j.enbuild.2016.10.050](https://doi.org/10.1016/j.enbuild.2016.10.050).
*   **Cerezo, C., Sokol, J., Reinhart, C., & Al-Mumin, A. (2015).** Three methods for characterizing building archetypes in urban energy simulation: A case study in Kuwait City. *Proceedings of BS 2015: 14th Conference of International Building Performance Simulation Association*, 2873–2880. [Link](http://www.ibpsa.org/proceedings/BS2015/p2358.pdf).
*   **Pasichnyi, O., Wallin, J., & Kordas, O. (2019).** Data-driven building archetypes for urban energy modeling. *Energy and Buildings*, 186, 230–243. DOI: [10.1016/j.enbuild.2019.01.034](https://doi.org/10.1016/j.enbuild.2019.01.034).
*   **Biljecki, F., Ledoux, H., & Stoter, J. (2017).** Imputing missing building heights in GIS datasets. *Transactions in GIS*, 21(5), 1014–1035. DOI: [10.1111/tgis.12246](https://doi.org/10.1111/tgis.12246).
*   **openubem Team. (2026).** How OpenUBEM Handles Missing Inputs (Informational Audit). (In-repo document: [REPORT_missing_input_handling.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/input/imputation/REPORT_missing_input_handling.md)).
