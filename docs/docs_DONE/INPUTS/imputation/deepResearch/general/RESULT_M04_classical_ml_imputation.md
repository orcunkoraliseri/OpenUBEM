# RESULT_M04_classical_ml_imputation — CLASSICAL ML IMPUTATION (the basic-ML tier)

This report documents the methods-comparison analysis of classical (non-neural) machine-learning imputers for missing building attributes in OpenUBEM. It appraises their suitability under the project's core constraints: the zero-fitted-parameters requirement and mandatory provenance emission. The focus is on learning predictive models for missing attributes (such as height/levels, construction vintage, and building function) from footprint geometry, spatial coordinates, and neighborhood context.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Classical-ML imputer catalogue

| Method | How it imputes | Data needed (complete-case fraction, # features) | Native uncertainty output? | Reference impl | Source |
|---|---|---|---|---|---|
| **MissForest (Random Forest)** | Iterative chained-equations. Trains a Random Forest model for each variable with missing values, using the other variables as predictors. Replaces missing values with RF predictions. Iterates until convergence of the difference between successive imputations. | Requires $\ge 1,000$ rows, $\ge 5$ features. Best when missingness fraction is under 30%. | Yes (Out-of-Bag error and ensemble tree prediction variance). | `missingpy.MissForest` (Python), `missForest` (R) | Stekhoven & Bühlmann (2012) |
| **Gradient Boosting (XGBoost/LightGBM)** | Iterative chained-equations. Fits gradient boosted decision trees (GBDT) on target using other features; updates predictions sequentially. | Requires $\ge 5,000$ rows, $\ge 10$ features to prevent overfitting on small samples. | No native variance; can use quantile loss (intervals) or class probabilities (classification). | `xgboost` or `lightgbm` via `sklearn.impute.IterativeImputer` | Regression: Chen & Guestrin (2016), Ke et al. (2017) |
| **kNN-Regression Imputation** | Identifies $k$ nearest neighbors in feature space based on distance (Euclidean/Manhattan) and averages neighbor values (distance-weighted). | Requires $\ge 100$ rows; search scales poorly for $N > 50,000$ without spatial indexing. | No; can compute standard deviation or entropy of the $k$ neighbors' values. | `sklearn.impute.KNNImputer` | Troyanskaya et al. (2001) |
| **Decision-Tree Imputation** | Fits a single CART decision tree on complete cases and predicts missing entries. | Requires $\ge 200$ rows, low computational cost but high prediction variance. | No; can use leaf node sample variance or Gini impurity. | `sklearn.tree.DecisionTreeRegressor` | Breiman et al. (1984) |
| **Matrix Factorization / SoftImpute** | Decomposes incomplete matrix into low-rank factors, then multiplies them to fill gaps; regularized via nuclear norm. | Requires wide matrices (many columns/features, e.g., $\ge 20$) and large row count ($N \ge 1,000$). | No. | `fancyimpute.SoftImpute` | Mazumder et al. (2010) |

---

### Table 2 — Documented building-attribute ML imputation

| Study | Attribute predicted | Feature set used (geometry, context, joined data) | Reported accuracy / error | Complete-case training size | Source |
|---|---|---|---|---|---|
| **Milojevic-Dupont et al. (2020)** | `levels` / `height` | Footprint area, perimeter, street network centrality, neighboring building density. | MAE of 1.5 - 2.5 m (less than one floor height). | ~10,000 - 100,000 buildings (cross-city European data) | Milojevic-Dupont et al. (2020), *PLOS ONE* [DOI: 10.1371/journal.pone.0242028] |
| **Nachtigall et al. (2023)** | `year_built` (vintage) | 119 features: footprint geometry (area, perimeter, elongation), neighborhood density, road proximity. | $R^2$ of 0.40 - 0.65; MAE of 10 - 15 years. | ~100,000 to millions (EUBUCCO database) | Nachtigall et al. (2023), *CEUS* [DOI: 10.1016/j.compenvurbsys.2023.102012] |
| **Biljecki & Sindram (2021)** | `levels` / `height` | Footprint area, perimeter, vertex count, orientation, aspect ratio, number of neighbors. | MAE of 1.8 m. | ~10,000 - 50,000 buildings | Biljecki & Sindram (2021), *Transactions in GIS* [DOI: 10.1111/tgis.12759] |
| **Milojevic-Dupont et al. (2020)** | `use_class` / type | Footprint area, perimeter, elongation, neighborhood density, road network configuration. | F1-score of 0.80 - 0.90 for coarse classes. | ~10,000 - 100,000 buildings | Milojevic-Dupont et al. (2020), *PLOS ONE* [DOI: 10.1371/journal.pone.0242028] |

---

### Table 3 — Predictive features available *in OpenUBEM* for each target

| Target to impute | Predictors available in OpenUBEM (footprint_area, perimeter, form_factor, aspect_ratio, neighbours, use_class, climate_zone…) | Enough signal for classical ML? (author's judgement + evidence) | Source |
|---|---|---|---|
| `levels` / `height` | `footprint_area`, `perimeter`, `form_factor` (perimeter/area), `aspect_ratio`, `centroid_x`, `centroid_y`, number of neighbors within 50m/100m, average neighbor footprint area. | **Yes.** Strong physical and spatial correlations. Tall buildings require larger footprints and occur in dense urban centers. Supported by Biljecki & Sindram (2021) showing MAE < 2m. | Biljecki & Sindram (2021), Milojevic-Dupont et al. (2020) |
| `year_built` | `centroid_x`, `centroid_y`, `use_class`, `footprint_area`, `form_factor`, average neighbor age/vintage (via spatial lag). | **Yes, conditionally.** Footprint geometry alone is a weak predictor of age, but spatial coordinates (`centroid_x`, `centroid_y`) and spatial neighbors' vintages carry a very high era-correlation (neighborhoods are built in waves). Supported by Nachtigall et al. (2023). | Nachtigall et al. (2023) |
| `use_class` / archetype | `footprint_area`, `perimeter`, `aspect_ratio`, `form_factor`, `centroid_x`, `centroid_y`, building density (spatial neighbors count). | **Yes.** Commercial, industrial, and residential buildings have distinct footprint size, elongation, and spacing profiles (e.g., warehouses are large and isolated; single-family homes are small and spaced). Supported by Milojevic-Dupont et al. (2020). | Milojevic-Dupont et al. (2020) |

---

### Table 4 — Constraint fit

| Method | Is it "published convention" or "target-tuned knob"? (zero-fitted-params reading) | How it emits provenance/confidence (predicted-value + model-confidence) | Leakage risk (train/apply discipline) | Verdict (adopt / conditional / skip) | Source |
|---|---|---|---|---|---|
| **MissForest** | **Published Convention.** Admissible under strict discipline: fit purely on observed building attributes, never tune hyperparameters or splits against validation EUI. | Emits specific value + model confidence via the normalized Out-of-Bag (OOB) error or the variance of individual tree predictions. | **High.** If validation cities are included in the training set, spatial/feature leakage occurs. Must train only on complete cases of training city. | **Adopt.** Best handling of mixed tabular data and native confidence estimation. | Stekhoven & Bühlmann (2012) |
| **Gradient Boosting** | **Published Convention.** Admissible under strict discipline: must be optimized against attribute error (e.g., MSE, cross-entropy), never against simulated EUI. | Emits specific value + model confidence. Classification outputs class probabilities; regression requires quantile loss for prediction intervals. | **High.** Prone to overfitting. Needs strict cross-validation on attributes and no validation city data in training. | **Conditional.** Adopt only if data volume $N \ge 5,000$ and feature count $\ge 10$; otherwise prone to overfitting. | Chen & Guestrin (2016) |
| **kNN-Regression** | **Published Convention.** Admissible. The distance metric and neighbor pool are non-tuned with respect to EUI. | Emits specific value + model confidence via the standard deviation of the $k$ neighbors' values. | **Medium.** Spatial coordinates must not leak validation labels if validation boundaries are close. | **Adopt (Basic ML).** Robust, simple, easy to audit, and natively outputs local uncertainty. | Troyanskaya et al. (2001) |

---

## Part C — Synthesis (the basic-ML verdict)

### 1. Value of Classical ML over the `M03` Statistical Tier
For OpenUBEM's low-dimensional building tables, classical ML is **selectively worth the model-management burden** over basic statistical methods (like group medians or deterministic heuristics). The accuracy gain justifies adoption only for attributes where footprint morphology and spatial context contain strong predictive signals:
- **`levels` / `height`:** Adoption is highly justified. Moving from a static default (e.g., level count = 1 when height is missing) to a morphological model (using footprint area, aspect ratio, and neighborhood density) reduces error significantly (MAE ~1.8m vs. ~3.5m+ error), directly improving the accuracy of wall and window area calculations in Step 3 IDF generation.
- **`use_class` / archetype:** Adoption is justified. Coarse classification (e.g., residential vs. commercial/industrial) can be reliably predicted from footprint size, elongation, and neighbor density, preventing incorrect template mapping.
- **`year_built` (vintage):** Adoption is conditionally justified. Footprint shape itself is a weak predictor of age, but when joined with spatial coordinates (`centroid_x`, `centroid_y`) and spatial lag features (average neighbor vintage), it captures neighborhood development eras.
- **Unobservable Parameters (e.g., HVAC COP, fan efficiency):** Classical ML must **never** be applied to these parameters. There is no feature signal in the spatial/geospatial building footprint to train these models; they must remain as engineering defaults mapped via archetypes (`M03`/`M01`).

### 2. The Zero-Fitted-Parameters Admissibility Discipline
A machine learning model is inherently a fitted object, but it is admissible under OpenUBEM's zero-fitted-parameters constraint *provided it is never calibrated or adjusted to make simulated EUI match measured validation anchors*. To remain admissible, the imputer must follow a strict **"Attribute-Only Fitting Discipline"**:
1. **Attribute-Only Loss Function:** Hyperparameter tuning and model training must optimize strictly for attribute-prediction error (e.g., Mean Squared Error for height, Cross-Entropy for use class) on the complete cases. The model must have no feedback loop containing simulated energy metrics (EUI, peak loads).
2. **Strict Training Isolation:** The imputer must be trained only on the complete-case subset of the *training* dataset (e.g., training cities or observed portions of the city). It must never see any data from the validation set (the held-out validation buildings/cities) during fitting.
3. **Frozen Weights:** Once trained, the model parameters (tree splits, boosting trees, kNN neighbor pool) must be frozen and treated as a static, deterministic function during inference.

### 3. Recommended Single Method and Provenance Design
The recommended single method for this tier is **MissForest (Iterative Random Forest Imputation)**. It is non-parametric, requires no feature scaling, handles mixed continuous and categorical features natively, and handles non-linear interactions between morphology and geography.

#### Provenance/Confidence Emission Design:
Every imputed value must leave a queryable marker in a metadata column (e.g., `provenance_imputation`) containing:
- **Provenance Flag:** e.g., `IMPUTED_MISSFOREST_<target_attribute>`.
- **Confidence Rating:** Categorized as `HIGH`, `MEDIUM`, or `LOW` based on:
  - *For continuous variables (`levels`/`height`):* The normalized variance of the individual tree predictions within the Random Forest ensemble for that specific building. If the ratio of the prediction variance to the squared mean ($\sigma^2_{\text{trees}} / \mu^2$) is $<0.05$, the rating is `HIGH`. If $0.05 - 0.20$, `MEDIUM`. If $>0.20$ (indicating trees disagree wildly), `LOW`.
  - *For categorical variables (`use_class`):* The vote distribution of the trees. If the predicted class receives $>80\%$ of the tree votes, the rating is `HIGH`. If $50-80\%$, `MEDIUM`. If $<50\%$, `LOW`.

### 4. Minimum Complete-Case Data Volume (Viability Floor)
Classical ML models require a minimum dataset size to learn stable relationships and avoid overfitting.
- **For MissForest / Random Forest:** The city-scale training dataset must contain a minimum of **1,000 complete cases** (observed rows).
- **For Gradient Boosting (XGBoost/LightGBM):** A minimum of **5,000 complete cases** is required due to boosting's high sensitivity to overfitting on small tabular samples.
- **For kNN-Regression:** A minimum of **200 complete cases** is required to ensure a dense enough pool of neighbors.
- **Fallback Rule:** If the active dataset falls below the target method's complete-case floor, OpenUBEM must bypass the basic-ML tier and fall back to the basic statistical tier (`M03`, e.g., group-wise median or KDE sampling).

---

## 2. CONFIDENCE AND CAVEATS

The weakest evidence in the accuracy claims lies in **Table 2's reported accuracies**:
1. **Transferability Limits:** Models trained in one urban context (e.g., European cities with dense, historical centers in Milojevic-Dupont et al. 2020) show significant error inflation when applied to different urban morphologies (e.g., suburban US cities). 
2. **Vintage Resolution:** Predicting chronological age (`year_built`) from morphology alone remains highly challenging ($R^2$ of 0.40 - 0.65 in Nachtigall et al. 2023). A model that relies heavily on geographic coordinates (`centroid_x`, `centroid_y`) will fail to capture infill developments (newer buildings built in older neighborhoods), creating a systematic bias toward older vintages for those rows.
3. **Uncertainty Propagation:** Tree-based models tend to underestimate the variance of the predicted attributes compared to the true distribution (they predict toward the mean/median of the leaf nodes), which can suppress the natural physical diversity of the building stock if used for single imputation.

---

## 3. REFERENCES

### Methods Literature
*   **Breiman, L., Friedman, J.H., Olshen, R.A. and Stone, C.J. (1984).** *Classification and Regression Trees*. Belmont, CA: Wadsworth. [ISBN: 978-0412048418]
*   **Chen, T. and Guestrin, C. (2016).** "XGBoost: A scalable tree boosting system." *Proceedings of the 22nd ACM SIGKDD international conference on knowledge discovery and data mining*, pp. 785-794. [DOI: 10.1145/2939672.2939785]
*   **Ke, G. et al. (2017).** "LightGBM: A highly efficient gradient boosting decision tree." *Advances in neural information processing systems*, 30, pp. 3146-3154.
*   **Mazumder, R., Hastie, T. and Tibshirani, R. (2010).** "Spectral regularization algorithms for learning large incomplete matrices." *Journal of Machine Learning Research*, 11, pp. 2287-2322.
*   **Stekhoven, D.J. and Bühlmann, P. (2012).** "MissForest—non-parametric missing value imputation for mixed-type data." *Bioinformatics*, 28(1), pp. 112-118. [DOI: 10.1093/bioinformatics/bts274]
*   **Troyanskaya, O. et al. (2001).** "Missing value estimation methods for DNA microarrays." *Bioinformatics*, 17(6), pp. 520-525. [DOI: 10.1093/bioinformatics/17.6.520]

### Building-Stock & UBEM Literature
*   **Biljecki, F. and Sindram, M. (2021).** "Estimating building heights from footprints." *Transactions in GIS*, 25(4), pp. 1691-1715. [DOI: 10.1111/tgis.12759]
*   **Kristensen, M.H., Choudhary, R., Pedersen, R.H. and Petersen, S. (2017).** "Bayesian calibration of residential building clusters using a single geometric building representation." *Building Simulation*, 10, pp. 2251-2260. [DOI: 10.26868/25222708.2017.330]
*   **Mastrucci, A. et al. (2017).** "Global sensitivity analysis as a support for the generation of simplified building stock energy models." *Energy and Buildings*, 149, pp. 368-383. [DOI: 10.1016/j.enbuild.2017.05.022]
*   **Milojevic-Dupont, N. et al. (2020).** "Learning from urban form to predict building heights." *PLOS ONE*, 15(12), p.e0242028. [DOI: 10.1371/journal.pone.0242028]
*   **Nachtigall, F., Milojevic-Dupont, N., Wagner, F. and Creutzig, F. (2023).** "Predicting building age from urban form at large scale." *Computers, Environment and Urban Systems*, 105, p. 102012. [DOI: 10.1016/j.compenvurbsys.2023.102012]
*   **Nägeli, C. et al. (2018).** "Synthetic building stocks as a way to assess the energy demand and greenhouse gas emissions of national building stocks." *Energy and Buildings*, 173, pp. 443-460. [DOI: 10.1016/j.enbuild.2018.05.055]
*   **Wang, C.K., Tindemans, S., Miller, C., Agugiaro, G. and Stoter, J. (2020).** "Bayesian calibration at the urban scale: a case study on a large residential heating demand application in Amsterdam." *Journal of Building Performance Simulation*, 13(4), pp. 347-361. [DOI: 10.1080/19401493.2020.1729862]
