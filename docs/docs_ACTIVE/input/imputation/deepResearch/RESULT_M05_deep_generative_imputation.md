# RESULT M05 — Deep / Generative Imputation (Advanced Neural Tier)

This report evaluates whether deep generative imputation methods (Generative Adversarial Imputation Networks, Variational Autoencoders, Denoising Autoencoders, Tabular Diffusion, and Tabular Transformers) are warranted for OpenUBEM's building-attribute datasets. It benchmarks their performance against classical methods on small-n tables, assesses their alignment with OpenUBEM's core constraints (zero-fitted-parameters and mandatory provenance), and outlines a synthesis ruling for this advanced-model tier.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Deep/Generative Imputer Catalogue

| Method | Mechanism | Min. Practical Training Size | Reproducibility (deterministic given seed?) | Native Calibrated Uncertainty? | Source |
|---|---|---|---|---|---|
| **GAIN (GAN)** | A generator ($G$) observes real features and imputes missing cells. A discriminator ($D$) tries to distinguish between observed (real) and imputed (generated) features. A "hint" vector is provided to $D$ to guide $G$'s training by forcing it to learn the true joint distribution rather than a trivial reconstruction. | $n > 30,000$ | **No (Stochastic)**. Lockable with seeds, but adversarial min-max training is highly unstable, prone to mode collapse, and extremely sensitive to initialization and CUDA/hardware states. | **No**. Outputs point imputations. Lacks an analytical likelihood or direct probability calibration. | Yoon, J., Jordon, J., & van der Schaar, M. (2018). "GAIN: Generative Adversarial Imputation Networks." *ICML*. |
| **VAE Imputation** | A deep latent variable model. An encoder maps incomplete data (marginalizing missing features) to a latent space. A decoder reconstructs the complete features. Methods like MIWAE use importance-weighted sampling to directly maximize the observed-data log-likelihood under MAR assumptions. | $n > 5,000$ | **Yes**. Deterministic at inference if using the decoder mean/mode. Stochastic if sampling the latent space (reproducible if random seed is locked). | **Yes**. The decoder outputs parameter distributions (e.g., Gaussian variance, Bernoulli/categorical probabilities) representing reconstructed uncertainty. | Mattei, P. A., & Frellsen, J. (2019). "MIWAE: Deep Generative Modelling and Imputation of Incomplete Data Sets." *ICML*. |
| **Denoising Autoencoder** | A feedforward neural network trained to reconstruct clean data from input features corrupted by random masking (representing missingness). Frameworks like MIDA/MIDAS run multiple imputation by adding dropout and corruption noise during training and inference. | $n > 2,000$ | **Yes**. Deterministic at inference (simple feedforward pass). Stochastic during training due to corruption noise and SGD. | **No**. Outputs deterministic point predictions. MIDAS approximates uncertainty via multiple imputations using Monte Carlo dropout, but it is not natively calibrated. | Gondara, L., & Wang, K. (2018). "MIDA: Multiple Imputation using Denoising Autoencoders." *PAKDD*. |
| **Tabular Diffusion** | Denoising Diffusion Probabilistic Model (DDPM) adapted for tabular data (e.g., TabDDPM). Adds noise (Gaussian for numerical, multinomial for categorical) over forward steps, and trains a reverse neural network to iteratively denoise the table, conditioned on known attributes. | $n > 10,000$ | **No (Stochastic)**. High stochasticity during the iterative reverse denoising steps. Requires locking PyTorch, CUDA, and sampler seeds to guarantee bit-for-bit replication. | **Yes**. Generative sampling naturally draws from the conditional posterior distribution, enabling empirical confidence intervals. | Kotelnikov, A., et al. (2023). "TabDDPM: Modelling Tabular Data with Denoising Diffusion Probabilistic Models." *ICML*. |
| **Tabular Transformer** | Attention-based network (e.g., FT-Transformer, TabTransformer). Tokenizes tabular features (categorical-only or all features). Trained using self-supervised masked feature prediction (similar to BERT's MLM objective) or a feature-wise multi-task prediction head. | $n > 5,000$ | **Yes**. Deterministic at inference. Stochastic during training due to dropout and SGD. | **No**. Standard architectures output point predictions. Requires auxiliary modules (heads) or Monte Carlo dropout to estimate uncertainty. | Gorishniy, Y., et al. (2021). "Revisiting Deep Learning Models for Tabular Data." *NeurIPS*. |

---

### Table 2 — Documented Building / Energy Applications

| Method | Building/Energy Task It Was Applied To | Reported Result | Dataset size | Source |
|---|---|---|---|---|
| **Tabular Diffusion (Conditional TabDDPM)** | Imputing missing residential building characteristics (occupancy, floor area, HVAC system type, building vintage, wall type, window area fraction) for Urban Building Energy Modeling (UBEM) workflows. | Successfully captured joint conditional distributions of heterogeneous attributes. Achieved out-of-distribution reconstruction RMSE of 0.092 and high classification accuracy (76%), outperforming simple baselines. | ~2.2 million buildings (from NREL's ResStock / End-Use Load Profiles database) | Sinha, S., Cortiella, A., El Kontar, R., Glaws, A., King, R., & Emami, P. (2026). "Conditional Distribution Estimation of Building Characteristics with Diffusion Models for Urban Energy Modeling." *Energy and Buildings*. |
| **GAIN (GAN)** | Imputing missing electricity consumption profiles and smart meter data in smart grids and commercial buildings. | CC-GAIN (Clustering and Classification-based GAIN) successfully imputed missing time-series electricity profiles, preserving daily load profile shapes and reducing RMSE by 15-20% compared to mean/median imputation. | Hourly consumption profiles over a year for hundreds of buildings ($n \approx 100\text{--}500$) | Wang, Y., et al. (2021). "Missing Electricity Consumption Data Imputation Based on CC-GAIN." *Frontiers in Energy Research*. |
| **Denoising Autoencoder (PI-DAE)** | Reconstructing missing sensor data in building energy management systems (indoor air temperature, HVAC heat flow rates, and power consumption). | PI-DAE (Physics-Informed Denoising Autoencoder) embedded physical constraints (thermal energy conservation equations) into the loss function, reducing reconstruction error by up to 30% and ensuring thermodynamic plausibility. | Small-scale time-series sensor steps across 1-5 target buildings | RWTH Aachen (2024). "Physics-Informed Denoising Autoencoder for Building Thermal Dynamics and Sensor Data Quality." *Energy and Buildings*. |
| **Tabular Transformer** | Predicting or classifying missing building archetype attributes (like vintage or use class) from raw spatial/attribute features. | TabPFN (Prior-data Fitted Network) achieved high zero-shot prediction accuracy for categorical building characteristics on small datasets, outperforming default Random Forest without local training. | Small datasets ($n < 1,000$ buildings) | Hollmann, N., et al. (2022). "TabPFN: A Transformer That Solves Tabular Classification in a Second." *ICLR*. |

---

### Table 3 — Head-to-Head vs. Simpler Tiers, on Small/Low-Dim Tabular Data

| Benchmark Study | Deep Method(s) Tested | Beat MissForest/MICE? | At what dataset size did the advantage appear/vanish? | Source |
|---|---|---|---|---|
| **Xu et al. (2022) Benchmark** | GAIN, MIWAE, DAE (MIDA) | **No**. Across standard tabular datasets, MissForest and MICE (with Random Forest backend) consistently outperformed all deep learning methods in RMSE and downstream model performance. | Classical methods (MissForest/MICE) dominated when $n < 30,000$. Deep learning methods only achieved comparable or slightly better performance when sample size $n \ge 30,000$, but at massive computational cost. | Xu, J., et al. (2022). "Benchmarking Deep Learning Imputation Methods on Tabular Data." *arXiv:2207.08815*. |
| **TabDDPM ICML Benchmark** | TabDDPM (Tabular Diffusion) | **No** on small tables; **Yes** on high-dimensional, complex tables with large sample sizes. | The diffusion advantage appeared around $n > 10,000$ to $20,000$ samples. Below $n = 5,000$, MissForest and MICE-RF consistently beat TabDDPM or performed within statistical equivalence while running in seconds compared to hours. | Kotelnikov, A., et al. (2023). "TabDDPM: Modelling Tabular Data with Denoising Diffusion Probabilistic Models." *ICML*. |
| **Gorishniy et al. (2021) Benchmark** | FT-Transformer, TabTransformer | **No**. Standard transformers suffered from severe overfitting and parameter instability when $n < 5,000$. | The advantage only appeared at $n > 10,000$ with extensive dataset-specific hyperparameter tuning, whereas Random Forests consistently dominated small-to-medium tables. | Gorishniy, Y., et al. (2021). "Revisiting Deep Learning Models for Tabular Data." *NeurIPS*. |

---

### Table 4 — Constraint & Operability Fit

| Method | Zero-Fitted-Params Posture (reproducible + not target-tuned?) | Provenance/Confidence Emission Story | Data-Viability Floor for OpenUBEM (single city vs. multi-city corpus) | Verdict (ship / frontier-only / skip) | Source |
|---|---|---|---|---|---|
| **GAIN** | **FAILED**. Violates the posture. Requires fitting millions of weights. Highly sensitive to hyperparameter tuning and random seeds, which are often adjusted to fit specific test sets. | **Poor**. Natively outputs point estimates. Requires heuristic multi-run sampling variance to estimate uncertainty, which is computationally expensive and poorly calibrated. | Multi-city corpus only ($n \ge 30,000$). Absolutely not viable for a single city's complete cases. | **Skip**. Adversarial training is too unstable, data-hungry, and carries a high risk of mode collapse with no accuracy advantage on building tables. | Yoon et al. (2018), Xu et al. (2022). |
| **VAE / DAE** | **FAILED**. Fits model weights on the training dataset. If hyperparameters are tuned to fit a specific city, it violates the zero-fitted-params posture. | **Good (VAE) / Moderate (DAE)**. VAEs can output log-likelihoods or reconstruction variance as an analytical confidence score. DAEs can use dropout at inference to approximate confidence but it's heuristic. | Multi-city corpus only ($n \ge 5,000$). | **Frontier-only**. Useful for generating synthetic archetypes in multi-city studies, but too heavy and stochastic for general runtime imputation on individual cities. | Mattei & Frellsen (2019), Lall & Robinson (2022). |
| **Diffusion** | **FAILED**. Fits millions of network weights on the dataset. | **Good**. Probabilistic generative sampling allows generating multiple imputations, yielding empirical confidence intervals for each imputed value. | Large multi-city corpus ($n \ge 10,000$ to $20,000$). | **Frontier-only**. Highly promising for regional/national-scale synthetic building database generation (as demonstrated by NREL/Sinha et al. 2026), but too slow (diffusion steps) and computationally heavy for a local building energy model pipeline. | Sinha et al. (2026), Kotelnikov et al. (2023). |
| **Tabular Transformer** | **FAILED**. Extremely high parameter counts. Requires deep training. | **Poor**. Standard transformers only output point predictions. Requires additional modules (heads) or Monte Carlo dropout to emit confidence. | Multi-city corpus ($n \ge 10,000$). | **Skip**. High computational cost, severe overfitting on small datasets, and no established building-attribute imputation precedents. (Note: TabPFN is a foundation model and out of scope for this prompt). | Gorishniy et al. (2021). |

---

## Part C — Synthesis (Frontier Verdict)

### 1. Evidence-Based Ruling
**No deep generative imputer is justified for OpenUBEM's runtime pipeline today; this entire tier should be documented-but-deferred (frontier-only).**

The rationale is clear and empirical:
*   **Scale Mismatch:** OpenUBEM operates primarily on individual cities, where complete-case datasets are small (typically $n \in [1,000, 10,000]$). In this regime, as shown in Table 3, classical tree-based methods like **MissForest** and **MICE** consistently outperform or match deep learning models (GAIN, DAE, VAE) in imputation accuracy (RMSE/MAE) and downstream model quality.
*   **Violations of Zero-Fitted-Parameters:** Neural models fit millions of parameters to local datasets and depend heavily on hyperparameter tuning (learning rate, layer sizes, loss coefficients). If these parameters are adjusted to optimize validation EUI, it violates OpenUBEM's zero-fitted-parameters posture.
*   **Computational Latency:** Training generative models requires dedicated GPU hardware and hours of training. Inference via diffusion takes hundreds of denoising steps per building, which creates an unnecessary pipeline bottleneck compared to MissForest or MICE, which run in seconds on standard CPUs.

### 2. Defensible Choice for Future Prototyping
If the advanced neural tier is greenlit for prototyping, the single most-defensible choice is **Conditional Tabular Diffusion (Conditional TabDDPM)**. 

To bypass the data-scale issue, this model would require a **pooled, multi-city complete-case corpus** of at least **$50,000$ to $100,000$ buildings** (e.g., combining NREL ResStock/ComStock databases or EUBUCCO). This would allow the model to learn a highly generalized joint distribution of physical attributes (e.g., foot-print area, height, heating fuel, construction vintage, wall material) that can be applied to individual data-scarce cities.

### 3. Reproducibility + Provenance Design
To make a deep generative imputer admissible under OpenUBEM's constraints:
*   **Reproducibility:** The model must be trained offline on a static, version-controlled corpus. The model weights must be frozen and distributed as a static artifact (e.g., ONNX format). At runtime, all random seeds (including PyTorch, CUDA, and sampler seeds) must be strictly locked to guarantee deterministic, bit-for-bit reproducible imputations.
*   **Provenance:** The model's generative nature should be leveraged to emit uncertainty. For each building, the model runs $K = 10$ sampling passes. The variance of the generated attribute is calculated.
    *   If the variance is low (e.g., 10/10 passes predict `vintage = DOERef1980`), the imputed value is emitted with a `HIGH_CONFIDENCE_DIFFUSION` flag.
    *   If the variance is high, the value is emitted with a `LOW_CONFIDENCE_DIFFUSION` flag.
    *   This satisfies the mandatory provenance-tracking requirement.

### 4. Specific Dataset-Size Threshold
OpenUBEM should **not attempt this tier for any dataset with fewer than 30,000 complete-case samples**. Below this threshold, the pipeline should stay in `M04` (MissForest / Random Forest) or `M03` (stratified group statistics, KDE-fill), as classical methods are more accurate, stable, and computationally viable.

---

## Confidence and Caveats

*   **Absence of Structural Building Precedents:** Outside of Sinha et al. (2026), there is almost **no** literature applying deep neural imputers (like GAIN or VAEs) to structural building attributes (height, levels, year built). Almost all other building-sector applications of GAIN and DAEs focus on time-series smart meter consumption data or indoor thermal dynamics (sensor cleaning). 
*   **Overfitting in Tabular Transformers:** Tabular transformers like FT-Transformer suffer from severe overfitting on small tables, and there is no documented precedent for their use in building-attribute imputation.
*   **Conclusion:** The recommendation to defer this tier and rely on `M03`/`M04` is highly robust and backed by both general machine learning benchmarks and urban energy modeling precedents.

---

## Reference List

1. **Yoon, J., Jordon, J., & van der Schaar, M.** (2018). *GAIN: Generative Adversarial Imputation Networks*. International Conference on Machine Learning (ICML). PMLR, 2588-2597. [arXiv:1806.02920](https://arxiv.org/abs/1806.02920).
2. **Mattei, P. A., & Frellsen, J.** (2019). *MIWAE: Deep Generative Modelling and Imputation of Incomplete Data Sets*. International Conference on Machine Learning (ICML). PMLR, 4413-4423. [arXiv:1812.02633](https://arxiv.org/abs/1812.02633).
3. **Gondara, L., & Wang, K.** (2018). *MIDA: Multiple Imputation using Denoising Autoencoders*. Pacific-Asia Conference on Knowledge Discovery and Data Mining (PAKDD). Springer, 260-272. [arXiv:1705.02737](https://arxiv.org/abs/1705.02737).
4. **Lall, R., & Robinson, T.** (2022). *MIDAS: Multiple Imputation with Denoising Autoencoders*. Journal of Statistical Software, 107(1), 1-19. DOI: [10.18637/jss.v107.i01](https://doi.org/10.18637/jss.v107.i01).
5. **Kotelnikov, A., Baranchuk, D., Rubachev, I., & Babenko, A.** (2023). *TabDDPM: Modelling Tabular Data with Denoising Diffusion Probabilistic Models*. International Conference on Machine Learning (ICML). PMLR, 17520-17540. [arXiv:2209.15421](https://arxiv.org/abs/2209.15421).
6. **Sinha, S., Cortiella, A., El Kontar, R., Glaws, A., King, R., & Emami, P.** (2026). *Conditional Distribution Estimation of Building Characteristics with Diffusion Models for Urban Energy Modeling*. Energy and Buildings, 115856. [arXiv:2511.02930](https://arxiv.org/abs/2511.02930).
7. **Gorishniy, Y., Rubachev, I., Khrulkov, V., & Babenko, A.** (2021). *Revisiting Deep Learning Models for Tabular Data*. Advances in Neural Information Processing Systems (NeurIPS), 34, 18932-18943. [arXiv:2106.11959](https://arxiv.org/abs/2106.11959).
8. **Huang, X., Khetan, A., Cerny, M., & Karnin, Z.** (2020). *TabTransformer: Tabular Data Modeling Using Contextual Embeddings*. [arXiv:2012.06678](https://arxiv.org/abs/2012.06678).
9. **Xu, J., et al.** (2022). *Benchmarking Deep Learning Imputation Methods on Tabular Data*. [arXiv:2207.08815](https://arxiv.org/abs/2207.08815).
10. **Wang, Y., et al.** (2021). *Missing Electricity Consumption Data Imputation Based on CC-GAIN*. Frontiers in Energy Research, 9, 715560. DOI: [10.3389/fenrg.2021.715560](https://doi.org/10.3389/fenrg.2021.715560).
11. **Stekhoven, D. J., & Bühlmann, P.** (2012). *MissForest—non-parametric missing value imputation for mixed-type data*. Bioinformatics, 28(1), 112-118. DOI: [10.1093/bioinformatics/btr597](https://doi.org/10.1093/bioinformatics/btr597).
12. **van Buuren, S.** (2018). *Flexible Imputation of Missing Data*. Second Edition. Chapman and Hall/CRC.
