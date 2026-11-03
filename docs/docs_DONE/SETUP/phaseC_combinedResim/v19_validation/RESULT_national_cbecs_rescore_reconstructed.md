# RESULT — V19 National CBECS Re-score: Reconstruction-ON (Apples-to-Apples with City Sweep)

## Grid specification

- `cooling_cop` ∈ [1.0, 2.5, 3.0, 3.5, 4.0]
- `heating_factor` ∈ [1.0, 1.19]
- `lighting_scale` ∈ [1.0, 0.8, 0.6, 0.5]
- `equipment_scale` ∈ [1.0, 0.7, 0.5]
- Total combos: 120 (5 × 2 × 4 × 3)
- Identity combo (1.0, 1.0, 1.0, 1.0) present: True

**Note:** Service-load reconstruction IS applied here (`reconstruct_frame` via `openubem.results.service_loads`). The gate is scored on `total_eui_reconstructed_kwh_m2` — the identical quantity the city sweep (v19_basis_diagnostic.score_combo) feeds to `build_city_table`. This is the companion to RESULT_national_cbecs_rescore.md (reconstruction OFF).

## Per-region identity baseline — RECONSTRUCTED (combo 1.0/1.0/1.0/1.0)

| region | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | 26.855 | False | 47.432 | False | 0.5066 | False | 3267 |
| pacific | 34.329 | False | 54.887 | False | 0.5466 | False | 558 |
| west_south_central | 34.807 | False | 51.052 | False | 0.5362 | False | 1481 |

## Top-10 combos by max_abs_nmbe — RECONSTRUCTED (ascending)

| cooling_cop | heating_factor | lighting_scale | equipment_scale | middle_atlantic_nmbe | middle_atlantic_nmbe_pass | middle_atlantic_cv_rmse_pass | middle_atlantic_ks_d_pass | pacific_nmbe | pacific_nmbe_pass | pacific_cv_rmse_pass | pacific_ks_d_pass | west_south_central_nmbe | west_south_central_nmbe_pass | west_south_central_cv_rmse_pass | west_south_central_ks_d_pass | max_abs_nmbe | n_regions_nmbe_pass | n_regions_cvrmse_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2.5 | 1.0 | 1.0 | 1.0 | 2.131 | True | False | False | -6.004 | True | False | False | -7.432 | True | False | False | 7.432 | 3 | 0 |
| 2.5 | 1.19 | 0.8 | 1.0 | 7.658 | True | False | False | -7.016 | True | False | False | -8.112 | True | False | False | 8.112 | 3 | 0 |
| 3.0 | 1.19 | 1.0 | 1.0 | 7.766 | True | False | False | -7.29 | True | False | False | -8.976 | True | False | False | 8.976 | 3 | 0 |
| 2.5 | 1.19 | 1.0 | 1.0 | 10.513 | False | False | False | -2.808 | True | False | False | -4.283 | True | False | False | 10.513 | 2 | 0 |
| 1.0 | 1.0 | 0.5 | 0.5 | 6.091 | True | False | False | 9.186 | True | False | False | 10.892 | False | False | False | 10.892 | 2 | 0 |
| 2.5 | 1.0 | 0.8 | 1.0 | -0.725 | True | False | False | -10.211 | False | False | False | -11.261 | False | False | False | 11.261 | 1 | 0 |
| 2.5 | 1.19 | 0.6 | 1.0 | 4.802 | True | False | False | -11.223 | False | False | False | -11.94 | False | False | False | 11.94 | 1 | 0 |
| 3.0 | 1.0 | 1.0 | 1.0 | -0.617 | True | False | False | -10.486 | False | False | False | -12.126 | False | False | False | 12.126 | 1 | 0 |
| 3.5 | 1.19 | 1.0 | 1.0 | 5.804 | True | False | False | -10.491 | False | False | False | -12.329 | False | False | False | 12.329 | 1 | 0 |
| 3.0 | 1.19 | 0.8 | 1.0 | 4.91 | True | False | False | -11.497 | False | False | False | -12.805 | False | False | False | 12.805 | 1 | 0 |

## Head-to-head: reconstructed vs raw-total (identity / 3.5·1·1·1 / 2.5·1.19·0.8·0.7)

Values from `national_cbecs_sweep_reconstructed.csv` (recon) and `national_cbecs_sweep.csv` (raw). Joined on `(cooling_cop, heating_factor, lighting_scale, equipment_scale)`.

### identity: cooling_cop=1.0 heating_factor=1.0 lighting_scale=1.0 equipment_scale=1.0

| region | recon_nmbe | recon_nmbe_pass | raw_nmbe | raw_nmbe_pass | recon_cv_rmse | recon_cv_rmse_pass | raw_cv_rmse | raw_cv_rmse_pass | recon_ks_d | recon_ks_d_pass | raw_ks_d | raw_ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | 26.855 | False | 5.041 | True | 47.432 | False | 54.094 | False | 0.5066 | False | 0.4041 | False |
| pacific | 34.329 | False | 7.917 | True | 54.887 | False | 67.8 | False | 0.5466 | False | 0.4431 | False |
| west_south_central | 34.807 | False | 1.355 | True | 51.052 | False | 72.593 | False | 0.5362 | False | 0.467 | False |
recon n_regions_nmbe_pass=0  raw n_regions_nmbe_pass=3  recon n_regions_cvrmse_pass=0  raw n_regions_cvrmse_pass=0

### city_winner: cooling_cop=3.5 heating_factor=1.0 lighting_scale=1.0 equipment_scale=1.0

| region | recon_nmbe | recon_nmbe_pass | raw_nmbe | raw_nmbe_pass | recon_cv_rmse | recon_cv_rmse_pass | raw_cv_rmse | raw_cv_rmse_pass | recon_ks_d | recon_ks_d_pass | raw_ks_d | raw_ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | -2.579 | True | -19.232 | False | 52.242 | False | 66.085 | False | 0.335 | False | 0.2259 | False |
| pacific | -13.687 | False | -30.7 | False | 63.133 | False | 84.552 | False | 0.3243 | False | 0.2586 | False |
| west_south_central | -15.478 | False | -36.808 | False | 56.151 | False | 92.84 | False | 0.3809 | False | 0.3126 | False |
recon n_regions_nmbe_pass=1  raw n_regions_nmbe_pass=0  recon n_regions_cvrmse_pass=0  raw n_regions_cvrmse_pass=0

### grid_min: cooling_cop=2.5 heating_factor=1.19 lighting_scale=0.8 equipment_scale=0.7

| region | recon_nmbe | recon_nmbe_pass | raw_nmbe | raw_nmbe_pass | recon_cv_rmse | recon_cv_rmse_pass | raw_cv_rmse | raw_cv_rmse_pass | recon_ks_d | recon_ks_d_pass | raw_ks_d | raw_ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | -0.518 | True | -17.352 | False | 56.598 | False | 69.174 | False | 0.3433 | False | 0.2291 | False |
| pacific | -15.791 | False | -32.157 | False | 66.367 | False | 86.934 | False | 0.3066 | False | 0.2408 | False |
| west_south_central | -16.718 | False | -37.048 | False | 60.645 | False | 96.346 | False | 0.3372 | False | 0.2796 | False |
recon n_regions_nmbe_pass=1  raw n_regions_nmbe_pass=0  recon n_regions_cvrmse_pass=0  raw n_regions_cvrmse_pass=0

## Region-pass count summary — RECONSTRUCTED (NMBE |·| < 10% and CV(RMSE) < 30%)

| label | cooling_cop | recon_n_nmbe_pass | recon_n_cvrmse_pass |
| --- | --- | --- | --- |
| identity | 1.0 | 0 | 0 |
| city_winner | 3.5 | 1 | 0 |
| grid_min | 2.5 | 1 | 0 |
