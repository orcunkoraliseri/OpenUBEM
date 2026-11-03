# RESULT — V19 National CBECS Re-score Under COP Energy Basis

## Grid specification

- `cooling_cop` ∈ [1.0, 2.5, 3.0, 3.5, 4.0]
- `heating_factor` ∈ [1.0, 1.19]
- `lighting_scale` ∈ [1.0, 0.8, 0.6, 0.5]
- `equipment_scale` ∈ [1.0, 0.7, 0.5]
- Total combos: 120 (5 × 2 × 4 × 3)
- Identity combo (1.0, 1.0, 1.0, 1.0) present: True

**Note (§3 decision):** Service-load reconstruction is intentionally NOT applied here. The national CBECS gate compares to all-fuels site EUI; the published gate path scores the raw `total_eui_kwh_m2` with no reconstruction. This differs from the city sweep (v19_basis_diagnostic), which did apply reconstruction.

## Per-region identity baseline (as-is Phase-C, combo 1.0/1.0/1.0/1.0)

| region | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | 5.041 | True | 54.094 | False | 0.4041 | False | 3267 |
| pacific | 7.917 | True | 67.8 | False | 0.4431 | False | 558 |
| west_south_central | 1.355 | True | 72.593 | False | 0.467 | False | 1481 |

## Top-10 combos by max_abs_nmbe (ascending)

| cooling_cop | heating_factor | lighting_scale | equipment_scale | middle_atlantic_nmbe | middle_atlantic_nmbe_pass | middle_atlantic_cv_rmse_pass | middle_atlantic_ks_d_pass | pacific_nmbe | pacific_nmbe_pass | pacific_cv_rmse_pass | pacific_ks_d_pass | west_south_central_nmbe | west_south_central_nmbe_pass | west_south_central_cv_rmse_pass | west_south_central_ks_d_pass | max_abs_nmbe | n_regions_nmbe_pass | n_regions_cvrmse_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | 1.0 | 0.6 | 1.0 | 0.369 | True | False | False | 1.259 | True | False | False | -4.112 | True | False | False | 4.112 | 3 | 0 |
| 1.0 | 1.0 | 0.8 | 1.0 | 2.705 | True | False | False | 4.588 | True | False | False | -1.379 | True | False | False | 4.588 | 3 | 0 |
| 1.0 | 1.0 | 1.0 | 0.7 | -1.663 | True | False | False | 0.953 | True | False | False | -4.842 | True | False | False | 4.842 | 3 | 0 |
| 1.0 | 1.19 | 0.8 | 0.7 | 3.038 | True | False | False | 0.282 | True | False | False | -4.991 | True | False | False | 4.991 | 3 | 0 |
| 1.0 | 1.19 | 1.0 | 0.7 | 5.373 | True | False | False | 3.611 | True | False | False | -2.258 | True | False | False | 5.373 | 3 | 0 |
| 1.0 | 1.0 | 0.5 | 1.0 | -0.799 | True | False | False | -0.406 | True | False | False | -5.479 | True | False | False | 5.479 | 3 | 0 |
| 1.0 | 1.19 | 0.5 | 1.0 | 6.238 | True | False | False | 2.253 | True | False | False | -2.895 | True | False | False | 6.238 | 3 | 0 |
| 1.0 | 1.19 | 1.0 | 0.5 | 0.904 | True | False | False | -1.032 | True | False | False | -6.389 | True | False | False | 6.389 | 3 | 0 |
| 1.0 | 1.19 | 0.6 | 1.0 | 7.405 | True | False | False | 3.917 | True | False | False | -1.528 | True | False | False | 7.405 | 3 | 0 |
| 1.0 | 1.0 | 0.8 | 0.7 | -3.999 | True | False | False | -2.377 | True | False | False | -7.576 | True | False | False | 7.576 | 3 | 0 |

## Cross-reference: identity vs city-anchor-winning combos (T04)

**Generalization signal** = `nmbe_at_combo − nmbe_at_identity` per region (negative = moved toward 0 = generalizes; positive = moved away = worsen).

### identity: cooling_cop=1.0 heating_factor=1.0 lighting_scale=1.0 equipment_scale=1.0

| region | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | gen_signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | 5.041 | True | 54.094 | False | 0.4041 | False | 0.0 |
| pacific | 7.917 | True | 67.8 | False | 0.4431 | False | 0.0 |
| west_south_central | 1.355 | True | 72.593 | False | 0.467 | False | 0.0 |
n_regions_nmbe_pass=3  n_regions_cvrmse_pass=0

### city_winner: cooling_cop=3.5 heating_factor=1.0 lighting_scale=1.0 equipment_scale=1.0

| region | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | gen_signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | -19.232 | False | 66.085 | False | 0.2259 | False | -24.273 |
| pacific | -30.7 | False | 84.552 | False | 0.2586 | False | -38.617 |
| west_south_central | -36.808 | False | 92.84 | False | 0.3126 | False | -38.163 |
n_regions_nmbe_pass=0  n_regions_cvrmse_pass=0

### grid_min: cooling_cop=2.5 heating_factor=1.19 lighting_scale=0.8 equipment_scale=0.7

| region | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | gen_signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | -17.352 | False | 69.174 | False | 0.2291 | False | -22.393 |
| pacific | -32.157 | False | 86.934 | False | 0.2408 | False | -40.074 |
| west_south_central | -37.048 | False | 96.346 | False | 0.2796 | False | -38.403 |
n_regions_nmbe_pass=0  n_regions_cvrmse_pass=0

## Region-pass count summary (NMBE |·| < 10% and CV(RMSE) < 30%)

| label | cooling_cop | n_regions_nmbe_pass | n_regions_cvrmse_pass |
| --- | --- | --- | --- |
| identity | 1.0 | 3 | 0 |
| city_winner | 3.5 | 0 | 0 |
| grid_min | 2.5 | 0 | 0 |

**F8 cross-reference (factual):** On the OLD Boston-R3 New-England single-cell dataset, a ÷3.5 cooling / ×1.19 heating basis moved NMBE from −16% → −29.5%. That dataset is DIFFERENT from Phase-C; this table is the Phase-C evidence.
