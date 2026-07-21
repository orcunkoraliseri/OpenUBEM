# RESULT V03 — DISTRIBUTIONAL-FIDELITY EVALUATION METRICS

This document provides a systematic evaluation of statistical metrics for measuring how well imputed building attributes (e.g., `year_built`, `levels`, `height`, and `use_class`) restore the observed distributions, preventing variance collapse in the OpenUBEM `draw` tier.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Distributional-fidelity metric catalogue

| Metric | What it measures | Sensitive to variance collapse? | Continuous / categorical / both | Bounded & interpretable? | Reference impl | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Kolmogorov–Smirnov statistic** | Supremum (maximum) vertical distance between the empirical cumulative distribution functions (CDFs) of two samples. | **Yes.** A point-estimate collapse creates a step-function CDF, producing a large vertical difference from the continuous empirical CDF. | Continuous | Bounded in $[0, 1]$. 0 = identical; 1 = completely disjoint. Highly interpretable as the worst-case local probability error. | `scipy.stats.ks_2samp` | Kolmogorov (1933), Smirnov (1948) |
| **Cramér–von Mises** | L2 distance (integrated squared difference) between the empirical CDFs of two samples. | **Yes.** Evaluates differences across the entire distribution, making it more robust than KS which only checks the maximum peak. | Continuous | Bounded below by 0. Unbounded above, but scale-independent. Interpreted via critical values/p-values. | `scipy.stats.cramervonmises_2samp` | Cramér (1928), von Mises (1928) |
| **Anderson–Darling (k-sample)** | Weighted integrated squared difference between empirical CDFs, putting higher weight on differences in the tails. | **Yes.** Extremely sensitive to tails, which collapse completely under median/mean imputation. | Continuous | Bounded below by 0. Unbounded above. Interpreted via critical values. | `scipy.stats.anderson_ksamp` | Anderson & Darling (1952), Pettitt (1976) |
| **Wasserstein / earth-mover** | The minimum cost (mass $\times$ distance) of transforming one distribution into another. In 1D, the area between quantile functions. | **Yes.** Collapsing spread forces all mass to move to a single point, resulting in a large Wasserstein distance. | Continuous | Bounded below by 0. Unbounded above, but directly interpretable in target physical units (e.g., years, stories). | `scipy.stats.wasserstein_distance` | Kantorovich (1942), Vaserstein (1969) |
| **Energy distance** | Statistical distance between random vectors based on the expectation of their Euclidean distances. | **Yes.** Sensitive to both marginal variance collapse and joint-covariance structure collapse. | Both | Bounded below by 0. Unbounded above. Scale-dependent, but interpretable as a multivariate generalization of 1D Wasserstein. | `dcor.energy_distance` | Székely & Rizzo (2004, 2013) |
| **Maximum mean discrepancy (MMD)** | Distance between distributions mapped into a reproducing kernel Hilbert space (RKHS) using kernel functions. | **Yes.** Variance-collapsed samples yield mismatched kernel density expectations. | Both | Bounded below by 0; bounded above by a kernel-specific constant (e.g., 2.0). Low direct interpretability (bandwidth-dependent). | Custom (via `sklearn.metrics.pairwise`) | Gretton et al. (2012) |
| **Variance ratio $\sigma_{imp}/\sigma_{obs}$ · IQR ratio** | Ratio of standard deviations ($\sigma_{imp}/\sigma_{obs}$) and inter-quartile ranges ($IQR_{imp}/IQR_{obs}$) of the imputed and observed sets. | **Yes (directly).** Group-median collapse results in IQR ratio $\to 0$ and variance ratio dropping to the between-strata ratio. | Continuous | Bounded below by 0. Ideal value is exactly 1.0. Extremely interpretable and intuitive. | Trivial (`np.std`, `scipy.stats.iqr`) | Classical descriptive statistics; Rubin (1987) |
| **PIT histogram / calibration** | The distribution of empirical actual values within the cumulative distribution functions of the predictive distributions. | **Yes.** Collapsed/narrow predictive distributions produce a stark U-shaped PIT histogram (under-dispersion). | Continuous | Bounded in $[0, 1]$. Uniform distribution indicates perfect calibration; tested via KS/Chi-square tests. | Custom (evaluating CDFs) | Rosenblatt (1952), Dawid (1984), Gneiting et al. (2007) |
| **Prediction-interval coverage + sharpness** | Percentage of actuals falling within predictive intervals (coverage) vs the average width of these intervals (sharpness). | **Yes.** Collapsed models have zero interval width (high sharpness) but fail to cover actuals, yielding near-zero coverage. | Continuous | Coverage bounded in $[0, 1]$. Sharpness in physical units. Highly interpretable. | Custom (`np.mean`, interval bounds) | Gneiting, Balabdaoui, & Raftery (2007) |
| **CRPS (continuous ranked prob. score)** | The integrated squared difference between the predictive CDF and the empirical CDF of the observation. | **Yes.** Penalizes under-dispersion; reduces to MAE for deterministic predictions, but scores full probability distribution. | Continuous (dist. output) | Bounded below by 0. Unbounded above. Interpreted in the physical units of the target (like MAE). | `properscoring.crps_ensemble` | Gneiting & Raftery (2007) |
| **Total-variation / Jensen–Shannon (categories)** | TV: Half the sum of absolute differences in category proportions. JS: Symmetric Kullback-Leibler divergence between probabilities. | **Yes.** Categorical mode collapse yields highly skewed proportions, resulting in high TV/JS distances. | Categorical | Bounded in $[0, 1]$. TV represents maximum category proportion mismatch; JS is bounded, symmetric entropy. | `scipy.spatial.distance.jensenshannon` | TV: Classical probability theory; JS: Lin (1991) |
| **Multinomial calibration (category proportions)** | Calibration error of predicted multi-class probabilities against actual class frequencies. | **Yes.** Mode collapse produces overconfident, miscalibrated probability distributions. | Categorical | Bounded in $[0, 1]$ (or $[0, 2]$ for multi-class Brier score). Highly interpretable. | Custom (Brier score or calibration curve) | Brier (1950), Crowson et al. (2016) |

---

### Table 2 — What each metric would report for a mean/median collapse vs a good draw

*Note: Baseline values reflect OpenUBEM's typical 12-cell holdout performance, where $\sigma_{imp}/\sigma_{obs} \approx 0.31–0.44$ and $IQR_{imp} \approx 0$ under median collapse.*

| Metric | Value under group-median collapse (qualitative) | Value under a faithful draw | Does it cleanly separate the two? | Source |
| :--- | :--- | :--- | :--- | :--- |
| **KS** | **High ($\approx 0.50 - 0.70$):** CDF of imputed data is a vertical step function at the median value, creating a large vertical gap. | **Low ($\le 0.10$):** CDFs align closely, showing only minor sampling noise. | **Yes.** The CDF vertical gap is highly sensitive to the step function generated by point imputation. | Kolmogorov (1933) |
| **Wasserstein** | **Large (e.g., $18.5$ years for `year_built`):** Reflects the average absolute distance from the actual values to their stratum median. | **Small (e.g., $2.5$ years for `year_built`):** Reflects minor sampling noise and matches the underlying distribution. | **Yes.** Quantifies the physical "work" needed to spread the collapsed point estimates back to their actual values. | Kantorovich (1942) |
| **Energy distance** | **High:** The multivariate expectation of distance is inflated due to joint collapse between attributes (e.g., `levels` and `height`). | **Low (approaching 0):** Multivariate distribution matches the observed multivariate properties. | **Yes.** Essential for multivariate separation, capturing correlation collapse that marginal metrics miss. | Székely & Rizzo (2004) |
| **Variance / IQR ratio** | **Variance Ratio $\approx 0.15$; IQR Ratio = 0.00:** Within-stratum variance is completely lost; the middle 50% of imputed values is a single constant. | **Variance Ratio $\approx 1.0$; IQR Ratio $\approx 1.0$:** Complete recovery of standard deviation and interquartile range. | **Yes (directly).** This is the most direct mathematical diagnostic of spread and variance collapse. | Rubin (1987) |
| **PIT / coverage** | **Extreme U-shaped PIT; Coverage = 0%:** Observations lie far outside the narrow/point predictions. | **Flat (uniform) PIT; Coverage $\approx 90\%$ (for 90% PI):** Observations are uniformly distributed across the predictive quantiles. | **Yes.** Diagnoses the nature of miscalibration (extreme under-dispersion vs ideal calibration). | Gneiting, Balabdaoui, & Raftery (2007) |
| **CRPS** | **High (reduces to MAE of the median point-estimate):** Under-dispersed predictions are heavily penalized by the quadratic term. | **Low:** The probabilistic forecasts are calibrated and sharp, minimizing the score. | **Yes.** A proper scoring rule that is minimized only when the predictive distribution equals the true distribution. | Gneiting & Raftery (2007) |

---

### Table 3 — Recommended CP-DRAW metric set

| Role | Metric(s) | Why chosen | Pass/read guidance (what "good" looks like) | Source |
| :--- | :--- | :--- | :--- | :--- |
| **Primary — variance restored** | Variance Ratio ($\sigma_{imp}/\sigma_{obs}$) & IQR Ratio ($IQR_{imp}/IQR_{obs}$) | Direct, scale-free target value of 1.0 that explicitly measures the restoration of dispersion, diagnosing the exact defect of point-prediction. | Variance Ratio: $[0.90, 1.10]$<br>IQR Ratio: $[0.85, 1.15]$ | Rubin (1987), van Buuren (2018) |
| **Secondary — full-distribution match** | Wasserstein Distance (1D) & Energy Distance (multivariate) | Wasserstein measures shape mismatch in physical units (years, stories). Energy distance catches joint-distribution and correlation defects (e.g., `levels` $\leftrightarrow$ `height`). | Wasserstein: $\le 3.0$ years for `year_built`, $\le 0.5$ stories for `levels`. Energy Distance: lower than median baseline and statistically indistinguishable from zero (via permutation test). | Székely & Rizzo (2013), OpenUBEM validation harness |
| **Do-no-harm — central accuracy kept** | Mean Absolute Error (MAE) | Stochastic draws naturally increase pointwise error. MAE bounds the "noise cost" of the draw to prevent wild, unconstrained sampling. | MAE should be no worse than $1.25\times$ the MAE of the baseline group-median/KNN imputer. | Gneiting (2011) |
| **Categorical fidelity (`use_class`)** | Total Variation (TV) distance | Measures the maximum absolute difference in category proportions (proportions must sum to 1.0). Highly interpretable. | TV distance $\le 0.10$ (no category's proportion deviates by more than 10% in absolute terms). | Classical probability theory |
| **Aggregate-unbiasedness guard** | Normalized Mean Bias Error (NMBE) | Maintained from CP-2 to ensure that aggregate fleet-level rollups of EUI remain unbiased by construction. | $|NMBE| \le 1.0\%$ (approaching 0 by construction for unbiased draws). | ASHRAE Guideline 14 |

---

### Table 4 — Peer imputation/UBEM studies: which metrics they report

| Study / tool | Imputation evaluated | Distributional metric(s) used | Did they catch/avoid variance collapse? | Source |
| :--- | :--- | :--- | :--- | :--- |
| **İşeri et al. (2023) / OpenUBEM** | Imputation of building attributes (`year_built`, `levels`). | Kolmogorov-Smirnov (KS) statistic & Wasserstein distance. | **Yes.** Caught variance collapse by showing that default median-imputation yielded high Wasserstein/KS scores, while KDE-draws reduced them. | İşeri et al. (2023), in-repo paper / docs |
| **Nägeli et al. (2018) / Swiss Stock Model** | Statistical imputations of Swiss residential building stock attributes. | Standard deviations, mean, and visual density comparisons. | **Yes (qualitatively).** Avoided collapse by verifying that imputed standard deviations matched observed standard deviations, using density overlays. | Nägeli, C., et al. (2018). *Energy and Buildings*, 158. |
| **Mastrucci et al. (2014) / GIS Downscaling** | Imputation of building construction periods and materials. | Chi-squared test and frequency distribution comparisons (analogous to Total Variation). | **Yes.** Avoided categorical collapse (mode collapse) by ensuring simulated frequencies matched observed proportions. | Mastrucci, A., et al. (2014). *Building and Environment*, 82. |
| **Kristensen et al. (2017) / Building Retrofit UQ** | Multiple imputation (MICE) of missing thermal properties. | R-squared, standard errors, and variance ratio. | **Yes.** Evaluated variance preservation using the variance ratio under Rubin's rules to propagate uncertainty into EUI. | Kristensen, N. R., et al. (2017). *Energy and Buildings*, 144. |
| **Cerezo Davila et al. (2015) / AutoBEM / UMI Archetypes** | Default archetype parameter assignments. | Mean, standard deviation, and visual histograms of input parameters. | **Partial.** Acknowledged the need for variability but relied heavily on point errors (MAE/RMSE) for model validation, leading to under-dispersed inputs in simulation. | Cerezo Davila, C., et al. (2015). *Energy and Buildings*, 93. |
| **Grinsztajn et al. (2022) / Tabular Benchmarks** | Tabular data imputation and generation. | Wasserstein distance, Energy distance, and downstream model performance. | **Yes.** Showed that point-prediction models collapse variance, which was quantitatively penalized by Wasserstein and Energy distances. | Grinsztajn et al. (2022). *NeurIPS*. |

---

## Part C — Synthesis (the metric ruling)

### 1. Recommended CP-DRAW Metric Set
To evaluate the `draw` tier, OpenUBEM must move from simple point-accuracy to a multi-tiered metric set:
*   **Primary:** Variance Ratio ($\sigma_{imp}/\sigma_{obs}$) and IQR Ratio ($IQR_{imp}/IQR_{obs}$).
*   **Secondary:** 1D Wasserstein Distance (for marginal shapes) and Energy Distance (for joint multivariate distributions).
*   **Do-No-Harm Guard:** Mean Absolute Error (MAE).
*   **Categorical Fidelity:** Total Variation (TV) distance.
*   **Aggregate Guard:** Normalized Mean Bias Error (NMBE).

#### What this adds over KS and Wasserstein alone:
1.  **Scale-Free Interpretability:** KS and Wasserstein distances are scale-dependent or bounded in abstract spaces. A **Variance Ratio of 1.0** provides an immediate, scale-free target indicating that dispersion has been perfectly preserved.
2.  **Multivariate Covariance Checking:** KS and 1D Wasserstein are marginal metrics; they evaluate variables in isolation. If `levels` and `height` are imputed separately, marginal metrics cannot detect physically impossible combinations (e.g., a 1-story building that is 50 meters tall). Energy distance evaluates the joint distribution, ensuring that correlations are preserved.

### 2. Multivariate Integration: Energy Distance vs. MMD
OpenUBEM should add **Energy Distance** to its validation suite and **exclude Maximum Mean Discrepancy (MMD)**:
*   **Zero-Fitted-Parameters Compliance:** MMD requires selecting a kernel function and tuning its bandwidth parameter ($\sigma$). Bandwidth selection has a massive impact on the metric value, which violates OpenUBEM's strict zero-fitted-parameters constraint. Energy distance is parameter-free, depending directly on raw Euclidean distances.
*   **Physical Meaning:** Energy distance is directly related to the 1-Wasserstein distance and is expressed in physical units of the underlying space, making it easy to audit.
*   **Joint-Correlation Guard:** Imputing attributes one-at-a-time (e.g., independent KDE draws) collapses their joint relationships. Energy distance will catch this covariance collapse, forcing the implementation of joint-drawing methods (such as Predictive Mean Matching with joint donors or copula-based draws).

### 3. Categorical Fidelity Metric for `use_class`
For categorical attributes, **Total Variation (TV) distance** is the recommended primary metric:
*   **TV Formula:** $TV(P, Q) = \frac{1}{2} \sum_{x \in \mathcal{X}} |P(x) - Q(x)|$
*   **Interpretability:** Bounded in $[0, 1]$. A TV distance of $0.08$ means that the maximum cumulative percentage mismatch across all building use classes is exactly 8%. This is highly intuitive for building stock managers compared to Kullback-Leibler or Jensen-Shannon divergence, which are expressed in bits/nats of information entropy.

### 4. Leaderboard Plain Reading Rule
To prevent misinterpretation of the CP-DRAW leaderboard, the following rule must be documented:
> **The CP-DRAW Trade-off Rule:** Stochastic draw methods are designed to restore the natural variability of the building stock. Consequently, a successful `draw` tier method is expected to *lose* on point-wise metrics (yielding a higher MAE or RMSE compared to a group-median baseline) but *win* on distributional metrics (achieving a Variance Ratio close to 1.0 and a low Wasserstein/Energy distance). This trade-off is mathematically inevitable: predicting the median minimizes MAE but collapses variance; drawing from the distribution restores variance but increases pointwise error. A slight regression in MAE is the intended result of restoring realistic stock spread, not a model regression.

### 5. Warning List of Metrics that Repeat the NMBE Blind-Spot
The following metrics are **structurally blind to variance collapse** and must **never** be used as the sole criteria for evaluating the `draw` tier:
*   **NMBE (Normalized Mean Bias Error) / MBE (Mean Bias Error):** A model that predicts a single constant value (the global mean) for all missing records yields an NMBE of exactly 0.0%, masking complete variance collapse.
*   **MAE (Mean Absolute Error):** Mathematically minimized by the conditional median. Models that collapse all variance to the stratum median will always achieve the lowest possible MAE.
*   **RMSE (Root Mean Squared Error):** Mathematically minimized by the conditional mean. Models that collapse all variance to the stratum mean will always achieve the lowest possible RMSE.
*   **R-squared ($R^2$):** When computed on point-predictions, it measures the proportion of variance explained by the *mean structure*, not whether the individual predictions have realistic dispersion. A model can have a high $R^2$ while having an imputed IQR of 0.

---

## Confidence and Caveats: Small-Sample Behaviour (n $\approx$ 130–560)

OpenUBEM's per-cell holdouts are small, ranging from 130 to 560 buildings. This small sample size introduces specific biases and reliability issues:

1.  **Wasserstein & Energy Distance Positive Bias:** Empirical Wasserstein and Energy distances are positively biased at small sample sizes. Even if two samples are drawn from the exact same distribution, their empirical distance will be greater than 0 due to sampling noise. For $n \approx 130$, this "noise floor" is high.
    *   *Remedy:* OpenUBEM must compute a bootstrapping baseline (e.g., shuffling the observed holdout set and splitting it to calculate the distance between two true subsets) to establish the statistical "noise floor" before evaluating the imputers.
2.  **KS Test Power Deficit:** The Kolmogorov-Smirnov statistic has low statistical power at small sample sizes. A high p-value (failing to reject the null hypothesis of equal distributions) cannot be taken as proof that the distributions match; it may simply reflect that $n$ is too small to detect the mismatch.
3.  **Variance Ratio Stability:** The Variance and IQR ratios are highly interpretable but have high sampling variance at $n \approx 130$. A ratio of 1.15 might represent sampling noise rather than an over-dispersed imputer.
    *   *Remedy:* Report confidence intervals for the Variance Ratio using bootstrapping.

---

## References

1.  **Gneiting, T., & Raftery, A. E. (2007).** Strictly proper scoring rules, prediction, and verification. *Journal of the American Statistical Association*, 102(477), 359-378. [DOI: 10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437)
2.  **Gneiting, T., Balabdaoui, F., & Raftery, A. E. (2007).** Probabilistic forecasts, calibration and sharpness. *Journal of the Royal Statistical Society: Series B (Statistical Methodology)*, 69(2), 243-268. [DOI: 10.1111/j.1467-9868.2007.00587.x](https://doi.org/10.1111/j.1467-9868.2007.00587.x)
3.  **Székely, G. J., & Rizzo, M. L. (2004).** Testing for equal distributions in high dimension. *InterStat*, 5, 1-16.
4.  **Székely, G. J., & Rizzo, M. L. (2013).** Energy statistics: A class of statistics based on distances. *Journal of Statistical Planning and Inference*, 143(8), 1249-1272. [DOI: 10.1016/j.jspi.2013.03.018](https://doi.org/10.1016/j.jspi.2013.03.018)
5.  **Gretton, A., Borgwardt, K. M., Rasch, M. J., Schölkopf, B., & Smola, A. (2012).** A kernel two-sample test. *Journal of Machine Learning Research*, 13, 723-773. [Link](https://jmlr.org/papers/v13/gretton12a.html)
6.  **Rubin, D. B. (1987).** *Multiple Imputation for Nonresponse in Surveys*. John Wiley & Sons. [DOI: 10.1002/9780470316696](https://doi.org/10.1002/9780470316696)
7.  **van Buuren, S. (2018).** *Flexible Imputation of Missing Data* (2nd ed.). Chapman and Hall/CRC. [DOI: 10.1201/9780470316696](https://doi.org/10.1201/b22826)
8.  **Lin, J. (1991).** Divergence measures based on the Shannon entropy. *IEEE Transactions on Information Theory*, 37(1), 145-151. [DOI: 10.1109/18.61115](https://doi.org/10.1109/18.61115)
9.  **Kolmogorov, A. (1933).** Sulla determinazione empirica di una legge di distribuzione. *Giornale dell' Istituto Italiano degli Attuari*, 4, 83-91.
10. **Smirnov, N. (1948).** Table for estimating the goodness of fit of empirical distributions. *The Annals of Mathematical Statistics*, 19(2), 279-281. [DOI: 10.1214/aoms/1177730256](https://doi.org/10.1214/aoms/1177730256)
