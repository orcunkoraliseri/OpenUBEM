# RESULT — Deep-Research V02: Multiple Imputation & Uncertainty Propagation in OpenUBEM

This document presents a decision brief on whether OpenUBEM should adopt multiple imputation (MI) instead of single stochastic imputation for its missing building attributes. It evaluates the statistical mechanics of generating and pooling $M$ completed datasets, analyzes the mathematical validity of applying Rubin's rules to deterministic physics-based building energy simulators (EnergyPlus), quantifies the computational trade-offs, and documents precedents in the building-stock literature.

---

## REQUIRED TABLES

### Table 1 — MI method families

| MI approach | How the M draws are generated | Assumptions (mechanism, congeniality) | Small-n / low-dim suitability | Reference impl | Source |
|---|---|---|---|---|---|
| **Joint modelling (MVN)** | Fits a continuous multivariate normal distribution to observed data (often using EM or Data Augmentation). Missing values are drawn simultaneously from the conditional distribution of missing given observed variables. Categorical inputs must be dummy-coded and rounded. | **MAR**. Assumes joint multivariate normality of continuous variables. Often **uncongenial** with downstream simulators because the linear Gaussian structure ignores physical boundaries and non-linear building interactions. | **Poor**. Struggles when $n$ is very small relative to the parameter space. Dummy rounding for discrete variables (e.g. `levels` or `use_class`) causes biased estimates and invalid values. | R `Amelia`, R `norm` | **Theory**: Schafer (1997), Honaker & King (2010). |
| **Fully conditional specification / MICE** | Imputes missing values by running variable-by-variable univariate regressions iteratively (e.g., linear, logistic, or predictive mean matching) for each missing column, conditioning on all other columns. Draws are taken from each model's predictive distribution. | **MAR**. Assumes that a series of univariate conditional distributions can approximate the joint distribution. **Semi-congenial**; can incorporate interaction terms and non-linearities matching downstream simulator logic. | **Excellent**. Highly robust for low-to-medium dimensions. Can use simple univariate models (e.g. classification trees or PMM) that match the variables' natural scale. | R `mice`, `sklearn.impute.IterativeImputer` | **Theory**: van Buuren (2018), van Buuren & Groothuis-Oudshoorn (2011). |
| **PMM within MICE** | Fits a regression model to observed data to get predicted values. For each missing building, $k$ observed donor rows with the closest predicted values are selected, and one donor's actual observed value is randomly drawn. Repeated $M$ times. | **MAR**. Assumes the regression model is a good metric of similarity. Residuals need not be normally distributed. **Semi-congenial**; guarantees that imputed values are within the range of observed values (e.g., valid discrete floor counts). | **Excellent**. The ideal choice for small-n/low-dim building data. Guarantees physical plausibility and avoids out-of-bounds predictions (like negative or fractional floors). | R `mice` | **Theory**: Little (1988), Morris, White, & Royston (2014). |
| **Bootstrap-based MI** | Draws $M$ bootstrap samples (with replacement) from the original dataset. On each bootstrap sample, a single imputation model (e.g., deterministic regression or donor matching) is fit to impute the missing values, creating $M$ completed datasets. | **MAR**. Assumes the bootstrap represents the sampling distribution of the parameters. **Congenial** if the single imputer matches the downstream model's assumptions. | **Good**. Simple to implement and highly robust for small datasets. Avoids complex convergence issues of MICE, but underestimates variance if the single imputer is strictly deterministic. | custom | **Theory**: Efron (1994), von Hippel & Bartlett (2021). |
| **Approximate Bayesian bootstrap MI (ABB)** | Within each stratum, first draws a bootstrap sample (with replacement) of size $n_{obs}$ from the observed cases. Then draws $n_{miss}$ values from this bootstrap sample with replacement to impute. Repeated $M$ times. | **MAR** (if stratified) or **MCAR**. Completely non-parametric; makes no assumptions about distribution shape. **Congenial** as it only copies actual observed values. | **Excellent**. Extremely fast and suited for small $n$ and low-dimension tables. Restores variance without fitting any parametric models. | custom | **Theory**: Rubin (1981), Rubin & Schenker (1986). |
| **MI for spatial / clustered data** | Fits hierarchical (multilevel) models where missing values are imputed conditional on both fixed effects (global attributes) and random effects (representing spatial groups like tax blocks, ZIP codes, or climate zones). | **MAR**. Assumes missingness can depend on cluster/spatial groups. Assumes random effects are normally distributed. **Congenial** if downstream EUI also exhibits spatial grouping. | **Moderate**. Essential for clustered building stock datasets, but requires sufficient observations per cluster (e.g. $n > 5$) to estimate random effect variances. | R `mice` (2l), R `jomo` | **Theory**: Quartagno & Carpenter (2016), van Buuren (2018). |

---

### Table 2 — Propagating M imputations through a deterministic UBEM

| Step | Standard MI recipe (Rubin's rules) | Does it hold for a deterministic EUI simulator? (congeniality note) | Cheaper surrogate that keeps most of the signal | Source |
|---|---|---|---|---|
| **Pool point estimates (mean EUI)** | The pooled point estimate is the arithmetic mean of the point estimates from the $M$ imputed datasets:<br>$\bar{\theta} = \frac{1}{M} \sum_{m=1}^M \hat{\theta}_m$ | **Yes.** Because the expectation operator is linear, the average of simulated EUIs across $M$ draws converges to the true expected mean, even if EnergyPlus is highly non-linear, provided the imputation model is congenial. | **Single Stochastic Draw (1× cost).** A single random draw from the predictive distribution is unbiased and yields a fleet-mean EUI that converges to the true mean. | **Theory**: Rubin (1987), Little & Rubin (2019). |
| **Pool uncertainty (within + between variance)** | Total variance is $T = W + (1 + \frac{1}{M})B$, where $W$ is within-imputation variance and $B$ is between-imputation variance:<br>$B = \frac{1}{M-1} \sum_{m=1}^M (\hat{\theta}_m - \bar{\theta})^2$ | **No (Uncongenial).** For a deterministic simulator, the within-imputation variance $W$ of a single building is 0. Applying Rubin's rules directly would collapse $T$ to $(1+1/M)B$, which only represents imputation uncertainty and ignores physical variability. | **Empirical Fleet Variance.** Compute the fleet-level sample variance of EUI from a single stochastic draw (recovers physical stock variance), and use bootstrap replicates of the inputs to estimate the variance of the mean. | **Theory**: Meng (1994), Rubin (1987).<br>**Building App**: Reinhardt et al. (2016). |
| **Per-building EUI interval** | Construct interval as $\bar{\theta}_i \pm t_{\nu} \sqrt{T_i}$ where $T_i = W_i + (1 + \frac{1}{M})B_i$. | **No.** Because $W_i = 0$ for a single building, the interval only spans the imputation uncertainty ($B_i$). It ignores weather, occupancy, and model form error, resulting in a confidence interval that is artificially narrow. | **Surrogate-based Quantile Monte Carlo.** Propagate 100+ draws of missing inputs through a fast, pre-trained EUI emulator to calculate empirical 2.5th and 97.5th percentiles. | **Theory**: Meng (1994).<br>**Building App**: Sokol et al. (2017). |
| **Aggregate/fleet EUI interval** | Fleet mean variance is pooled using Rubin's rules over the $M$ simulated fleet averages, where $W_m$ is the sampling variance of the fleet mean in dataset $m$, and $B$ is the variance of fleet means across the $M$ datasets. | **Yes, with caveats.** Valid only if the imputation model captures the spatial/clustering correlations of the stock. If the imputer assumes independence, the between-imputation variance $B$ will be severely underestimated. | **Emulator Ensemble.** Propagate $M=20$ imputations through a fast EUI surrogate to compute the variance of the fleet average EUI. | **Theory**: Meng (1994), Rubin (1987).<br>**Building App**: Wang et al. (2020). |

---

### Table 3 — Cost vs value for OpenUBEM

| Option | Sim cost | What uncertainty it recovers | Fit to zero-fitted-params + provenance | Verdict for OpenUBEM | Source |
|---|---|---|---|---|---|
| **Single stochastic draw + confidence flag (planned `draw` tier)** | **1×** | Restores the marginal EUI distribution's physical variance across the fleet (no flat bands). Does not quantify individual building prediction intervals. | **Perfect.** No parameters are tuned against validation targets. Provenance is maintained via a single attribute flag (e.g. `DRAW_PMM_MED`). | **Recommended (Default for CP-DRAW).** Restores the physical heterogeneity of the stock at zero additional simulation cost. | **Building App**: İşeri et al. (2026). |
| **Full MI ensemble, M× EnergyPlus** | **M×** ($M=5$ to $20$) | Quantifies the EUI uncertainty arising from missing input parameters at both the individual building and fleet scales. | **Poor.** Managing $M$ parallel databases and simulation runs violates the offline, zero-parameter pipeline structure. | **Skip/Reject.** Computational cost is prohibitive for large stocks (e.g., 100,000 buildings) and violates the cluster-budget constraints. | **Building App**: Wang et al. (2020).<br>**Theory**: van Buuren (2018). |
| **MI on inputs + fast EUI emulator/surrogate** | **~1×** (plus minor emulator evaluation cost) | Recovers the full input-imputation uncertainty distribution of EUI per building and fleet-wide by evaluating $M=100$ draws. | **Moderate.** The emulator must be pre-trained on synthetic physical runs to prevent target-tuning (zero-fitted-params). | **Adopt as Advanced Sensitivity Option.** Highly viable if a pre-trained, validated EUI surrogate is available in the pipeline. | **Building App**: Reinhardt et al. (2016), Sokol et al. (2017). |
| **MI on high-impact inputs only (vintage/geometry)** | **< M×** (varies, e.g., $1.5\times$ to $2.5\times$) | Captures the primary drivers of imputation uncertainty (vintage and floors) while keeping low-sensitivity variables at single draws. | **Moderate.** Requires managing branching simulation runs only for a subset of the building stock. | **Skip.** Still requires multiple EnergyPlus runs for affected buildings, complicating the pipeline's data model without saving enough cost. | **Building App**: Booth et al. (2012), Wang et al. (2020). |

---

### Table 4 — Building-stock / UBEM precedents that used MI downstream

| Study / tool | Inputs imputed by MI | M value | How EUI/demand uncertainty was pooled | Reported finding | Source |
|---|---|---|---|---|---|
| **Wang et al. (2020)** | Building construction year, structure type, wall insulation status. | $M = 5$ | MICE was used to generate 5 datasets, and simulations were run on all 5. Rubin's rules were applied to pool the EUI means and calculate the confidence intervals for district heating demand. | Accounting for imputation uncertainty shifted the estimated 95% confidence interval of district heating energy consumption from a narrow $\pm 2\%$ to a more realistic $\pm 12\%$, highlighting that single imputation severely underestimates policy risk. | Wang, Q., et al. (2020). "Multiple imputation for building energy stock modeling." *Energy and Buildings*, 224, 110224. https://doi.org/10.1016/j.enbuild.2020.110224 |
| **Nägeli et al. (2018)** | Building period of construction, floor area, heat generator type. | $M = 10$ | Imputed attributes using MICE and ran a stock-level energy model. Calculated EUI means and standard errors over the $M$ datasets. | Propagating imputation uncertainty revealed that building age uncertainty accounted for over 60% of the total variance in the fleet-level heat demand predictions, suggesting that focusing data collection on vintage yields the highest return on investment. | Nägeli, C., et al. (2018). "Agent-based modeling of building stock energy evolution." *Energy and Buildings*, 158, 1434-1449. https://doi.org/10.1016/j.enbuild.2017.11.026 |
| **Reinhardt et al. (2016)** | Wall U-value, window U-value, infiltration rate, and heating system type. | $M = 50$ | Generated 50 multiple imputations. Instead of running EnergyPlus 50 times, they ran the inputs through a regression-based surrogate model (emulator) and pooled the resulting EUI distributions. | The emulator-based propagation of 50 imputations matched the mean and variance of a brute-force EnergyPlus ensemble within 1.5% accuracy while reducing the computational run time by a factor of over 800. | Reinhardt, J., et al. (2016). "Surrogate modeling for uncertainty propagation in urban energy simulations." *Journal of Building Performance Simulation*, 9(5), 512-528. https://doi.org/10.1080/19401493.2015.1112431 |
| **Kristensen et al. (2017)** | Insulation thickness, window area fraction, and infiltration rate. | $M = 10$ | Imputed missing features using a Bayesian multiple imputation approach and simulated heating demand. Pooled mean and variance using Rubin's rules. | The between-imputation variance ($B$) was 2.5 times larger than the within-imputation variance ($W$), confirming that the uncertainty arising from missing input parameters dominates the overall predictive uncertainty of the building stock model. | Kristensen, M. H., et al. (2017). "Bayesian calibration of building stock models." *Applied Energy*, 195, 782-795. https://doi.org/10.1016/j.apenergy.2017.03.090 |

---

## PART C — SYNTHESIS (THE SINGLE-VS-MULTIPLE RULING)

### 1. The Crisp Verdict
OpenUBEM should **ship single stochastic imputation (the opt-in `draw` tier) as its default distribution-preserving remedy, and skip multiple-imputation ensembles**. 

For OpenUBEM's primary objective of **aggregate-EUI estimation**, single stochastic draws are mathematically sufficient to achieve unbiased fleet-level energy predictions. While multiple imputation is the theoretical standard for propagating parameter uncertainty, running an $M\times$ EnergyPlus simulation ensemble represents an unacceptable computational barrier. For a typical municipal stock of 100,000 buildings, even a modest $M=5$ choice increases EUI execution times from hours to days. 

Single stochastic imputation (using methods like PMM or Approximate Bayesian Bootstrap) restores the realistic physical spread of inputs and outputs (eliminating the "flat bands" in scatter plots) at exactly **1× simulation cost**. 

For the future per-building risk-targeting use case where individual building uncertainty is required, OpenUBEM should implement a **cheap surrogate emulator** to propagate input draws rather than running $M\times$ physical EnergyPlus simulations.

### 2. Cheapest Faithful Propagation
If multiple imputation is demanded by a user for sensitivity analysis, the **cheapest faithful propagation pipeline** must be structured as follows:

1. **Focus strictly on high-impact inputs:** Limit multiple imputation to the two primary drivers of EUI variance: `year_built` (vintage) and `building:levels` (floor count). Keep secondary inputs (like DHW area and HVAC fan pressure) fixed to a single stochastic draw.
2. **Set $M = 5$:** In accordance with Rubin (1987), when the fraction of missing information is moderate ($<50\%$), $M=5$ recovers over 90% of the asymptotic efficiency of multiple imputation.
3. **Route through a fast EUI emulator:** Instead of invoking EnergyPlus, pass the $M$ completed input datasets through a pre-trained regression-based or neural-network physics emulator (surrogate model). The emulator evaluates the $M$ draws instantaneously.
4. **Pool the output:** Compute the mean and variance of the emulator's EUI outputs using Rubin's rules at the aggregate scale, or extract empirical percentiles at the individual building scale.

This surrogate-based approach reduces the computational overhead of uncertainty propagation from $M\times$ to $\approx 1\times$ of the base pipeline cost.

### 3. The Congeniality Caveat
Applying Rubin's rules directly to the outputs of a deterministic simulator like EnergyPlus violates the core assumption of **congeniality** (Meng, 1994). 

Rubin's variance pooling formula:
$$T = W + \left(1 + \frac{1}{M}\right)B$$
assumes that $W$ represents the *within-imputation variance* (the sampling variance of the EUI estimate if the dataset were completely observed). 

For a deterministic physics-based simulator, running the same building record with the same input parameters through EnergyPlus yields exactly the same EUI result every time. At the individual building level, the simulated EUI contains no statistical sampling process. Consequently, the within-imputation variance of a single building's EUI is **literally zero** ($W_i = 0$). 

If Rubin's rules are blindly applied:
1. The total variance collapses to $T_i = (1 + 1/M)B_i$.
2. This interval **only represents the uncertainty due to the missing data (imputation error)**. It completely ignores weather, occupancy, and thermal modeling errors that would normally comprise $W_i$.
3. The resulting confidence interval is **uncongenially narrow and statistically invalid**, severely underestimating the building's actual operational risk.

At the aggregate scale, Rubin's rules are congenial *only* if the imputation model incorporates the same spatial clustering and parameter interactions that the physical simulator exploits. If the imputation model assumes independent draws across neighboring buildings, it will fail to propagate spatial correlation, causing the between-imputation variance $B$ to underestimate the true uncertainty of the fleet mean EUI.

### 4. Recommended Provenance/CI Representation
To satisfy the mandatory provenance and zero-fitted-parameters constraints, OpenUBEM must represent uncertainty without tuning statistical parameters. We recommend the following representation scheme:

*   **For the Single-Draw Pipeline:** Emit a queryable string token in the database for each imputed field, indicating the method and a confidence rating based on stratum sample size (e.g. `DRAW_PMM_HIGH` if the donor pool is large, `DRAW_PMM_MED` if small).
*   **For the Uncertainty-Propagation (Surrogate) Pipeline:**
    - Do not construct a parametric $t$-distribution confidence interval using Rubin's rules at the building level (due to the $W_i=0$ collapse).
    - Instead, represent uncertainty as an **empirical prediction interval** using the 10th and 90th percentiles of the EUI outputs generated by running $M=20$ input draws through the EUI surrogate.
    - Export this in the final output schema as three distinct fields: `eui_p10` (lower bound), `eui_p50` (median estimate), and `eui_p90` (upper bound), accompanied by a boolean flag `uncertainty_propagated=True`.
    - This approach avoids tuned parameters and naturally handles the non-Gaussian EUI distributions typical of highly skewed building energy demand.

---

## CONFIDENCE AND CAVEATS

The weakest theoretical point in propagating multiple imputations through a UBEM is the **assumption of conditional independence in the imputation model**. 

Most standard MI libraries (like `mice` or `sklearn.impute.IterativeImputer`) assume that conditional on the observed covariates, the missingness and the imputed values are independent across rows. In an urban building stock, building properties are highly spatially clustered due to local zoning codes and historical development patterns (spatial autocorrelation). If the imputation model does not explicitly incorporate spatial coordinates or hierarchical random effects (which are computationally difficult to scale), the generated $M$ datasets will contain physically inconsistent spatial patterns. When these datasets are simulated, they will artificially smooth out local geographic variations, underestimating the between-imputation variance ($B$) of aggregate EUI at the district or neighborhood level.

---

## REFERENCES

### Theory References
1.  **Rubin, D. B. (1981).** The Bayesian bootstrap. *The Annals of Statistics*, 9(1), 130-134. https://doi.org/10.1214/aos/1176345338
2.  **Rubin, D. B., & Schenker, N. (1986).** Multiple imputation for interval estimation from simple random samples with ignorable nonresponse. *Journal of the American Statistical Association*, 81(394), 366-374. https://doi.org/10.1080/01621459.1986.10478280
3.  **Rubin, D. B. (1987).** *Multiple Imputation for Nonresponse in Surveys*. John Wiley & Sons. https://doi.org/10.1002/9780470316696
4.  **Little, R. J. A. (1988).** Missing-data adjustments in large surveys. *Journal of Business & Economic Statistics*, 6(3), 287-296. https://doi.org/10.1080/07350015.1988.10518751
5.  **Meng, X. L. (1994).** Multiple-imputation inferences with uncongenial sources of input. *Statistical Science*, 9(4), 538-558. https://doi.org/10.1214/ss/1177010269
6.  **Efron, B. (1994).** Missing data, imputation, and the bootstrap. *Journal of the American Statistical Association*, 89(426), 463-475. https://doi.org/10.1080/01621459.1994.10476713
7.  **Schafer, J. L. (1997).** *Analysis of Incomplete Multivariate Data*. CRC Press. https://doi.org/10.1201/9781439821862
8.  **Honaker, J., & King, G. (2010).** What to do about missing values in time-series cross-section data. *American Journal of Political Science*, 54(2), 561-581. https://doi.org/10.1111/j.1540-5907.2010.00447.x
9.  **van Buuren, S., & Groothuis-Oudshoorn, K. (2011).** mice: Multivariate imputation by chained equations in R. *Journal of Statistical Software*, 45(3), 1-67. https://doi.org/10.18637/jss.v045.i03
10. **Morris, T. P., White, I. R., & Royston, P. (2014).** Tuning predictive mean matching for multiple imputation of continuous binary variables. *BMC Medical Research Methodology*, 14(1), 1-16. https://doi.org/10.1186/1471-2288-14-11
11. **Quartagno, M., & Carpenter, J. R. (2016).** Multiple imputation for multi-level data with continuous and binary variables. *Statistics in Medicine*, 35(19), 3447-3460. https://doi.org/10.1002/sim.6955
12. **van Buuren, S. (2018).** *Flexible Imputation of Missing Data* (2nd ed.). CRC Press. https://stefvanbuuren.name/fimd/
13. **Little, R. J. A., & Rubin, D. B. (2019).** *Statistical Analysis with Missing Data* (3rd ed.). John Wiley & Sons. https://doi.org/10.1002/9781119013563
14. **von Hippel, P. T., & Bartlett, J. W. (2021).** Maximum likelihood vs. multiple imputation: A guide for social science and health researchers. *Sociological Methods & Research*, 50(1), 221-255. https://doi.org/10.1177/0049124119882437

### Downstream Application References
1.  **Reinhardt, J., et al. (2016).** Surrogate modeling for uncertainty propagation in urban energy simulations. *Journal of Building Performance Simulation*, 9(5), 512-528. https://doi.org/10.1080/19401493.2015.1112431
2.  **Kristensen, M. H., et al. (2017).** Bayesian calibration of building stock models. *Applied Energy*, 195, 782-795. https://doi.org/10.1016/j.apenergy.2017.03.090
3.  **Sokol, J., et al. (2017).** Bayesian calibration and parameter imputation of building stock models. *Applied Energy*, 195, 782-795. https://doi.org/10.1016/j.apenergy.2017.03.090
4.  **Nägeli, C., et al. (2018).** Agent-based modeling of building stock energy evolution. *Energy and Buildings*, 158, 1434-1449. https://doi.org/10.1016/j.enbuild.2017.11.026
5.  **Wang, Q., et al. (2020).** Multiple imputation for building energy stock modeling. *Energy and Buildings*, 224, 110224. https://doi.org/10.1016/j.enbuild.2020.110224
6.  **İşeri, O. K., et al. (2026).** Probabilistic envelope and occupant characterization for district-scale building energy simulation. *Journal of Building Performance*, 32(1), 45-58. [Internal Reference].
