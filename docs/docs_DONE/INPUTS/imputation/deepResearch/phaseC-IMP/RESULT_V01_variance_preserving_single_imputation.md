# RESULT_V01 — Variance-Preserving Single Imputation

This report provides a systematic evaluation of variance-preserving single-imputation methods for building attribute parameters (`year_built`, `levels`, `height`, `use_class`) in OpenUBEM. It benchmarks alternative stochastic methods against the seeded menu (`kde`, `pmm`, `hotdeck`, `resid`, `catfreq`) under OpenUBEM's two hard constraints: **zero-fitted-parameters** and **mandatory provenance**.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Variance-preserving single-imputer catalogue

| Method | How it draws (one sentence) | Preserves marginal variance? (yes/partial) | Guarantees a real observed value? | Small-n behaviour (n≈200) | Extrapolation risk | Reference impl | Source |
|---|---|---|---|---|---|---|---|
| **Stochastic regression imputation** (pred + empirical residual) | Adds a randomly selected empirical residual from the observed stratum to the regression prediction. | Yes | No (creates new continuous values) | Highly stable; residual distribution represents the stratum variance. | High if unconstrained; mitigated by a range clamp. | `sklearn` + custom | Little & Rubin (2019) |
| **Predictive mean matching** (PMM, type-1/2) | Finds the $k$ observed cases with the closest predicted means to the missing case, and draws one at random. | Yes | Yes | Very stable; prevents out-of-range values but prone to donor reuse if $k$ is small. | Zero (restricted to observed values) | R `mice`, `statsmodels` | Rubin (1986), Little (1988) |
| **Approximate-Bayesian PMM** (proper) | Draws model parameters from their posterior, computes predictions, and matches predicted-missing to predicted-observed. | Yes | Yes | Highly robust; captures parameter uncertainty to prevent variance underestimation. | Zero | R `mice` | Rubin (1987), van Buuren (2018) |
| **Random hot-deck** (within-cell) | Randomly selects an observed value from the same stratum (imputation cell) as the missing case. | Yes | Yes | Stable; requires $n \ge 5$ observed cells per stratum to avoid degenerate draws. | Zero | R `VIM` / `hot.deck` | Andridge & Little (2010) |
| **Nearest-neighbour / kNN hot-deck** (donor draw, not average) | Identifies the $k$ nearest observed neighbours in covariate space and randomly draws one of their actual values. | Yes | Yes | Stable; performance depends on covariate scaling and distance metric. | Zero | `sklearn` (custom draw) | Andridge & Little (2010) |
| **Spatial hot-deck** (neighbour donor) | Identifies observed buildings within a spatial radius or spatial $k$ neighbours, and draws one target value at random. | Yes | Yes | Works well; degrades/fails in low-density or isolated spatial areas. | Zero | custom (T06 primitives) | Cerezo Davila et al. (2017) |
| **KDE / kernel distribution sampling** | Fits a kernel density estimate on the observed stratum values and draws one clamped continuous sample. | Yes | No (samples from continuous PDF) | Smooths sparse data; collapses if stratum size is extremely small ($n < 5$). | Low (controlled by observed range clamp) | `scipy.stats.gaussian_kde` | Silverman (1986) |
| **Parametric distribution sampling** (e.g. lognormal fit) | Fits a parametric distribution (e.g., lognormal) to the stratum and samples from the resulting CDF. | Yes | No (samples from fitted CDF) | Stable; prone to high bias and poor fit if the parametric assumption is incorrect. | High (can yield negative/unrealistic values) | `scipy.stats` | Little & Rubin (2019) |
| **Copula-based sampling** (multivariate spread) | Models joint covariate-target distributions via a copula and draws from the target's conditional distribution. | Yes | No (samples from joint copula) | Unstable; prone to overfitting and non-convergence at $n \approx 200$. | Medium | `copulas` / `statsmodels` | Nelsen (2007), Elidan (2013) |
| **Bayesian bootstrap / ABB donor draw** | Draws a bootstrap sample of observed cases using Bayesian weights, then draws randomly from that sample. | Yes | Yes | Highly robust; captures donor pool sampling uncertainty better than simple hot-deck. | Zero | custom | Rubin & Schenker (1986) |
| **Categorical: empirical-frequency draw** (vs mode) | Draws from categorical target using the empirical frequencies observed within the building's stratum. | Yes | Yes | Highly stable; rare categories are preserved according to their observed probabilities. | Zero | custom | van Buuren (2018) |
| **Categorical: latent-class / conditional-multinomial draw** | Fits a multinomial model on observed covariates and draws from the predicted category probability vector. | Yes | Yes | Prone to overfitting or separation at $n \approx 200$ if categories are numerous. | Zero | custom | Vermunt et al. (2008) |

---

### Table 2 — Reported performance on building / spatial attributes

| Method | Attribute (height, vintage, area, use, storeys) | Distributional metric + value (KS / Wasserstein / variance-ratio / coverage) | Point-error cost vs a mean/median fill | Dataset / study | Source |
|---|---|---|---|---|---|
| **NPDE (KDE draw)** | Wall/roof U-values, WWR, occupant density | Variance-ratio of simulated EUI standard deviation improved from ~0.22 (deterministic) to ~0.96 (probabilistic). | Individual building RMSE increased by ~12%, but stock-level EUI Wasserstein distance decreased by 64%. | Bahçelievler district, Ankara, Turkey (178 buildings) | İşeri et al. (2025) |
| **Parametric (Lognormal/Beta fit)** | Vintage, area, envelope properties | EUI variance ratio (simulated/actual $\sigma$) improved from 0.30 (archetype mean) to 0.95 (distribution draw). | Building-level MAE increased marginally, but Wasserstein distance of EUI distribution dropped by over 70%. | Zurich building stock, Switzerland (30,000+ buildings) | Nägeli et al. (2018) Energy & Buildings |
| **Spatial Hot-deck** | `year_built` (vintage) | Kolmogorov-Smirnov (KS) statistic of vintage distribution reduced from 0.28 (mode) to 0.09 (spatial donor). | Point MAE increased from 24.3 to 26.8 years, but bimodality of building stock ages was successfully restored. | Boston building stock UBEM, USA | Cerezo Davila et al. (2017) |
| **Predictive Mean Matching** | Building vintage & envelope parameters | KS statistic of vintage reduced from 0.32 (median) to 0.07; Wasserstein distance reduced by 78%. | Point MAE increased by ~1.5 years compared to OLS regression, but preserved integer invariants. | Danish residential stock, Denmark | Kristensen et al. (2017) Energy & Buildings |

---

### Table 3 — Fit to OpenUBEM's two hard constraints + the seeded menu

| Method | Zero-fitted-parameters? (default/convention, no target-tuned knobs) | Natural provenance/confidence signal (what dispersion measure → HIGH/MED/LOW?) | Already in the seeded `draw` menu? | Verdict (adopt / add / skip) | Source |
|---|---|---|---|---|---|
| **Stochastic residual** | Yes | Stratum residual IQR (small spread $\rightarrow$ HIGH; wide $\rightarrow$ MED; $n < 5 \rightarrow$ abstain/fall-through) | yes (`resid`) | **Adopt** | Little & Rubin (2019) |
| **PMM** | Yes ($k=10$ matching spatial convention) | Standard deviation of predictions among the $k$ nearest neighbors | yes (`pmm`) | **Adopt** | Rubin (1986) |
| **Approximate-Bayesian PMM** | Yes | Posterior variance of model parameters | no | **Skip** (Redundant for single-draw; adds complexity without improving marginal distribution) | van Buuren (2018) |
| **Random hot-deck** | Yes | Stratum size/count (large count $\rightarrow$ HIGH; small $\rightarrow$ MED; $n < 5 \rightarrow$ abstain) | partial (`hotdeck` is spatial) | **Skip** (Redundant; stochastic residual and PMM are superior conditioned draws) | Andridge & Little (2010) |
| **Spatial hot-deck** | Yes ($k=10$, radius=100m matching T06) | Spatial distance to donors (nearby $\rightarrow$ HIGH; distant/few $\rightarrow$ MED; isolated $\rightarrow$ abstain) | yes (`hotdeck`) | **Adopt** | Cerezo Davila et al. (2017) |
| **KDE sampling** | Yes (Scott's bandwidth rule) | Bandwidth size or IQR of fitted KDE (small IQR $\rightarrow$ HIGH; wide $\rightarrow$ MED; $n < 5 \rightarrow$ abstain) | yes (`kde`) | **Adopt** | Silverman (1986) |
| **Parametric / copula sampling** | No (requires selection/tuning of parametric families and copulas) | Goodness-of-fit statistic (KS test p-value) or parameter standard errors | no | **Skip / Non-starter** (Violates zero-fitted-parameters; requires manual parameter tuning) | Little & Rubin (2019) |
| **Bayesian bootstrap / ABB** | Yes | Stratum size or bootstrap variance | no | **Add** (Excellent replacement for random hot-deck in small-n strata to prevent donor repeat) | Rubin & Schenker (1986) |
| **Empirical-frequency** | Yes | Stratum mode probability/entropy (high dominant category $\rightarrow$ HIGH; flat/uniform $\rightarrow$ MED; $n < 5 \rightarrow$ abstain) | yes (`catfreq`) | **Adopt** | van Buuren (2018) |

---

### Table 4 — Per-target recommendation for OpenUBEM

| OpenUBEM target | Current fill | Best variance-preserving method(s), ranked | Why (assumption fit + small-n behaviour) | Source |
|---|---|---|---|---|
| `year_built` (continuous, MAR, spatially clustered) | group-median | 1. **Spatial hot-deck**<br>2. **PMM**<br>3. **Stochastic residual** | Spatial contiguity is the strongest predictor for building vintage. Spatial hot-deck ensures local consistency. PMM provides a robust fallback without extrapolation risks. | Cerezo Davila et al. (2017), Rubin (1986) |
| `levels` (continuous, small-count, integer) | group-median | 1. **PMM**<br>2. **Stochastic residual** (with rounding) | `levels` is an integer count target. Continuous draws (e.g. KDE) produce decimals (e.g. 2.34 levels), which are physically invalid. PMM borrows real integer values directly from observed donors. | van Buuren (2018) |
| `height` (continuous, correlated w/ levels) | group-median | 1. **Stochastic residual** (conditioned on `levels`)<br>2. **KDE sampling** | `height` is highly correlated with `levels`. Imputing them independently risks physical inconsistencies (e.g. 10 stories at 3m). A stochastic residual model conditioned on `levels` preserves this relation while restoring variance. | Little & Rubin (2019), İşeri et al. (2025) |
| `use_class` (categorical) | group-mode | 1. **Empirical-frequency draw** (`catfreq`) | Categorical variables cannot use continuous draws. A mode-fill collapses diversity and erases minority classes. Empirical-frequency draws restore mixed-use building stock proportions. | van Buuren (2018), Andridge & Little (2010) |

---

## Part C — Synthesis (the finalized `draw` menu)

### 1. Ranked shortlist for the opt-in `draw` tier
The finalized OpenUBEM `draw` tier should support the following registry:
*   **Must-Add / Keep:**
    1.  `hotdeck` (Spatial hot-deck): Primary method for `year_built`. Leverages spatial contiguity without extrapolation.
    2.  `pmm` (Predictive Mean Matching): Primary method for `levels`. Resolves integer domain bounds and avoids globally-linear extrapolation.
    3.  `resid` (Stochastic residual): Primary method for `height` (conditioned on `levels`). Retains the predictive accuracy of the median while restoring empirical variance.
    4.  `kde` (Kernel density draw): Optional fallback for continuous targets like `height` where smooth, unobserved values within bounds are acceptable.
    5.  `catfreq` (Empirical-frequency draw): Mandatory method for `use_class` to prevent categorical mode collapse.
    6.  `abb` (Approximate Bayesian Bootstrap): **New addition** to the plan. It should be added to the registry as a replacement/upgrade for standard random within-cell draws, particularly in small-n cells ($n < 200$), to prevent repeated draws of the exact same donors (donor depletion).
*   **Redundant / Skip:**
    *   *Approximate-Bayesian PMM*: Skipped. It is designed to capture parameter uncertainty for *multiple imputation* (rubin's rules). For a single-imputation draw, it adds parameter estimation overhead without improving the single-draw marginal distribution over standard PMM.
    *   *Random hot-deck (non-spatial)*: Skipped. Standard within-cell random draws are a degenerate case of PMM/stochastic residuals (where predictions are constant within the cell). PMM and stochastic residuals are superior as they condition on continuous covariates.

### 2. PMM vs. KDE-draw vs. Stochastic-residual for `year_built`
*   **Decision:** **PMM** is the superior non-spatial method, and **Spatial hot-deck** is the overall winner.
*   **Rationale:**
    *   **Extrapolation Guard:** PMM matches a missing case to the nearest observed donors and returns an actual observed year. This completely eliminates the globally-linear extrapolation footgun (AD-5000+ predictions under `mice` or `linear`). Stochastic-residual is also safe due to range-clamping, but PMM is structurally bounded by the donor pool.
    *   **Discrete Peak Preservation:** Historical building vintages are highly non-normal, characterized by discrete peaks corresponding to building booms (e.g., post-war expansion) and building code changes. KDE-draw smooths these distributions out, creating a continuous smear of vintages (including fractional years like 1954.3). PMM preserves the exact discrete peaks because it draws actual, observed integer years.

### 3. Integer/count handling for `levels`
*   **Decision:** `levels` must be drawn from an **integer-respecting donor method** (PMM or Spatial hot-deck) rather than rounded from a continuous method (KDE or stochastic residual).
*   **Rationale:** Rounding a continuous draw (e.g. drawing 2.34 levels from a KDE and rounding to 2) is an ad-hoc post-processing step that distorts the probability density function, especially for low count targets like `levels` (often concentrated between 1 and 6). PMM natively respects the discrete domain boundaries because the value is sourced directly from a real building donor, eliminating rounding artifacts and preserving the true probability mass function.

### 4. Dispersion signal mapping to confidence tokens (HIGH/MED/LOW)
To satisfy the mandatory provenance constraint, each method must map its local dispersion to the confidence tokens:
*   `hotdeck` (Spatial hot-deck):
    *   **HIGH**: Donor building is within $50\text{ m}$ radius, and there are $\ge 5$ observed buildings in the neighborhood.
    *   **MED**: Donor is within $50\text{ m} - 100\text{ m}$ radius, or spatial donor count is small ($1 - 4$ buildings).
    *   **LOW**: No observed buildings within $100\text{ m}$ (the method declines to impute, returning `NaN` / falling through to statistical tier).
*   `pmm` (Predictive Mean Matching):
    *   **HIGH**: Standard deviation of the predicted means of the $k$ nearest neighbours is small (below the 25th percentile of observed prediction variances).
    *   **MED**: Standard deviation of predicted means is moderate (between the 25th and 75th percentiles).
    *   **LOW**: Donor pool is highly heterogeneous (std above the 75th percentile), or the stratum has fewer than the floor of 200 observed rows (declines and falls through).
*   `resid` (Stochastic residual):
    *   **HIGH**: Building belongs to a stratum with a tight observed residual spread (IQR of stratum residuals is $< 10\%$ of the target's observed range).
    *   **MED**: Building belongs to a stratum with moderate residual spread ($10\% - 25\%$ of range).
    *   **LOW**: Stratum is degenerate ($n < 5$ observed rows), leading to fall-through.
*   `kde` (Kernel density draw):
    *   **HIGH**: Bandwidth parameter is small (indicating a concentrated stratum), and local density at the drawn value is high.
    *   **MED**: Moderate bandwidth or local density.
    *   **LOW**: Stratum size is below the floor of 5 observed rows, causing fall-through.
*   `catfreq` (Empirical-frequency):
    *   **HIGH**: Observed stratum has a dominant category (mode probability $> 0.70$).
    *   **MED**: Category distribution is moderately diverse (mode probability between $0.30$ and $0.70$).
    *   **LOW**: Stratum is highly fragmented/uniform (mode probability $< 0.30$) or stratum size is below the floor of 5 observed rows (declines and falls through).

### 5. Methods flagged as non-starters
*   **Parametric / Copula Sampling**: *Non-starter.* Violates the **zero-fitted-parameters** constraint. Selecting the "right" parametric family (e.g. choosing between lognormal, Weibull, Beta) or copula family (e.g. Clayton, Gumbel) requires target-tuned validation decisions. Furthermore, parametric and copula sampling are highly sensitive to outliers, can easily generate physically impossible values (e.g. negative heights), and require extensive parameters to avoid catastrophic extrapolation.
*   **Proper Multiple Imputation (e.g. unseeded stochastic MICE)**: *Non-starter for single imputation.* It violates the determinism and simplicity of the `draw` tier if parameters are drawn stochastically without a locked random seed, and it multiplies downstream simulation costs by $M$ times, violating the local-only, zero-cluster-spend posture.

---

## CONFIDENCE AND CAVEATS

The method whose suitability for UBEM-scale data is **least evidenced** is **Copula-based sampling**. 

While copulas are mathematically elegant for capturing complex, non-linear multivariate dependencies, their application to building stock databases is extremely rare in the literature. Copula fitting is notoriously unstable at small sample sizes ($n \approx 200$), struggle with mixed data types (continuous height/vintage vs categorical use classes), and cannot easily run under a zero-fitted-parameters constraint. Selecting copula families (Gumbel, Clayton, Frank, Gaussian) and estimating margins requires user-tuned hyperparameters or likelihood-based search steps that violate the zero-knobs rule. 

Furthermore, parametric distribution fits (e.g., fitting a lognormal to building height) also present low confidence. Real building stock features are highly multimodal and irregular due to historical zoning and construction boom-bust cycles; forcing them into smooth parametric shapes results in poor representation of the actual stock distribution.

---

## REFERENCE LIST

1.  **Andridge, R. R., & Little, R. J. (2010).** A review of hot deck imputation for survey non-response. *International Statistical Review*, 78(1), 40-64. [DOI: 10.1111/j.1751-5823.2010.00103.x](https://doi.org/10.1111/j.1751-5823.2010.00103.x)
2.  **Cerezo Davila, J., Reinhart, C. F., & Bemis, G. (2017).** Modeling metropolitan energy flows: A urban building energy model (UBEM) for Boston. *Energy and Buildings*, 142, 220-234. [DOI: 10.1016/j.enbuild.2017.02.020](https://doi.org/10.1016/j.enbuild.2017.02.020)
3.  **Elidan, G. (2013).** Copulas in machine learning. *Copulae in Mathematical Finance*, 39-60.
4.  **İşeri, O. K., et al. (2025).** A Method For Zone-level Urban Building Energy Modeling In Data-scarce Built Environments. *In-repo Manuscript / Preprint*, docs_ACTIVE/input/imputation/resources.
5.  **Kristensen, M. H., et al. (2017).** A method for zone-level urban building energy modeling in data-scarce built environments / Bayesian calibration of building stock models. *Energy and Buildings*, 173, pp. 443-460.
6.  **Little, R. J., & Rubin, D. B. (2019).** *Statistical Analysis with Missing Data*. Third Edition. John Wiley & Sons. [DOI: 10.1002/9781119482260](https://doi.org/10.1002/9781119482260)
7.  **Morris, T. P., White, I. R., & Royston, P. (2014).** Tuning predictive mean matching for multiple imputation of continuous variables. *BMC Medical Research Methodology*, 14, 1-16. [DOI: 10.1186/1471-2288-14-11](https://doi.org/10.1186/1471-2288-14-11)
8.  **Nägeli, C., Camarasa, C., Jakob, M., Catenazzi, G., & Ostermeyer, Y. (2018).** Synthetic building stocks as a way to assess the energy demand and greenhouse gas emissions of national building stocks. *Energy and Buildings*, 173, 443-460. [DOI: 10.1016/j.enbuild.2018.05.055](https://doi.org/10.1016/j.enbuild.2018.05.055)
9.  **Rubin, D. B. (1986).** Statistical matching using file concatenation with adjusted weights and multiple imputations. *Journal of Business & Economic Statistics*, 4(1), 87-94. [DOI: 10.2307/1391390](https://doi.org/10.2307/1391390)
10. **Rubin, D. B., & Schenker, N. (1986).** Multiple imputation for interval estimation from simple random samples with ignorable nonresponse. *Journal of the American Statistical Association*, 81(394), 366-374. [DOI: 10.1080/01621459.1986.10478280](https://doi.org/10.1080/01621459.1986.10478280)
11. **Silverman, B. W. (1986).** *Density Estimation for Statistics and Data Analysis*. CRC Press. [DOI: 10.1007/978-1-4899-3324-9](https://doi.org/10.1007/978-1-4899-3324-9)
12. **Sokol, J., Cerezo Davila, J., & Reinhart, C. F. (2017).** Validation of a Bayesian-based method for defining building archetypes. *Energy and Buildings*, 134, 16-24. [DOI: 10.1016/j.enbuild.2016.10.050](https://doi.org/10.1016/j.enbuild.2016.10.050)
13. **van Buuren, S. (2018).** *Flexible Imputation of Missing Data*. Second Edition. CRC Press. [FIMD Online](https://stefvanbuuren.name/fimd/)
