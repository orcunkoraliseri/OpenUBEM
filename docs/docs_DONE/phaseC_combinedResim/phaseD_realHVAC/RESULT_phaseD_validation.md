# RESULT — Phase-D Validation (data only; CP-5 verdict by manager)

Generated: 2026-06-25. Source: `scripts/validation/phaseD_city_rescore.py` (T10) +
`scripts/validation/phaseD_national_cbecs_rescore.py` (T11). No basis transform applied
(D3: HVAC is metered). Phase-C baseline sourced from `RESULT_basis_diagnostic.md` (city)
and `RESULT_national_cbecs_rescore.md` (national, identity combo = best NMBE/NMBE-pass).

---

## T10 — City-anchor re-score (Phase-D vs CITY_ANCHORS)

### Table A — total_eui_kwh_m2 (fans EXCLUDED, as-built)

`delta_vs_measured_pct = (model_median − measured) / measured × 100`

| city | segment | n | phaseD_median (kWh/m²) | measured (kWh/m²) | delta_vs_measured_pct |
| --- | --- | --- | --- | --- | --- |
| nyc | Office | 2570 | 204.62 | 183.9 | +11.3% |
| nyc | Multifamily | 1036 | 169.81 | 226.2 | −24.9% |
| nyc | Overall (excl. OpenUBEMUnknown n=558) | 3746 | 189.87 | 219.2 | −13.4% |
| la | Office | 372 | 114.18 | 121.5 | −6.0% |
| la | Multifamily | 1775 | 72.56 | 115.8 | −37.3% |
| la | Warehouse | 38 | 25.31 | 33.9 | −25.3% |
| la | Overall (excl. OpenUBEMUnknown n=19) | 2317 | 76.13 | 113.6 | −33.0% |
| austin | Office | 1244 | 126.40 | 162.3 | −22.1% |
| austin | Overall (excl. OpenUBEMUnknown n=73) | 1447 | 127.30 | 162.0 | −21.4% |

### Table B — total_eui_kwh_m2 + fans_eui_kwh_m2 (fans INCLUDED)

| city | segment | n | phaseD_median (kWh/m²) | measured (kWh/m²) | delta_vs_measured_pct |
| --- | --- | --- | --- | --- | --- |
| nyc | Office | 2570 | 206.06 | 183.9 | +12.0% |
| nyc | Multifamily | 1036 | 170.34 | 226.2 | −24.7% |
| nyc | Overall (excl. OpenUBEMUnknown n=558) | 3746 | 190.74 | 219.2 | −13.0% |
| la | Office | 372 | 115.09 | 121.5 | −5.3% |
| la | Multifamily | 1775 | 72.88 | 115.8 | −37.1% |
| la | Warehouse | 38 | 25.44 | 33.9 | −24.9% |
| la | Overall (excl. OpenUBEMUnknown n=19) | 2317 | 76.52 | 113.6 | −32.6% |
| austin | Office | 1244 | 127.54 | 162.3 | −21.4% |
| austin | Overall (excl. OpenUBEMUnknown n=73) | 1447 | 128.38 | 162.0 | −20.8% |

### Side-by-side: Phase-D (raw metered) vs Phase-C scalar-basis best

Phase-C best: `cooling_cop=2.5, heating_factor=1.19, lighting_scale=0.8, equipment_scale=0.7`
(best-global from RESULT_basis_diagnostic.md, max_abs_delta 13.0%, all 6 anchors within ±15%).

| city | segment | phaseC_best_delta | phaseD_fans_out_delta | phaseD_fans_in_delta |
| --- | --- | --- | --- | --- |
| nyc | Office | +12.2% | +11.3% | +12.0% |
| nyc | Overall | −7.7% | −13.4% | −13.0% |
| la | Office | +11.3% | −6.0% | −5.3% |
| la | Overall | −13.0% | −33.0% | −32.6% |
| austin | Office | −12.5% | −22.1% | −21.4% |
| austin | Overall | −11.7% | −21.4% | −20.8% |

Note: Phase-C city comparison uses `total_eui_reconstructed_kwh_m2` (after service-load
reconstruction). Phase-D uses `total_eui_kwh_m2` (raw metered; no reconstruction).
The comparison is not identical in basis — logged here for CP-5 manager adjudication.

---

## T11 — National CBECS re-score (Phase-D vs per-region CBECS 2018)

Gates: NMBE |·| < 10% pass; CV(RMSE) < 30% pass; KS_D < 0.10 pass; R² > 0.6 pass.
All three cities scored against their correct regional reference (D5 confirmed — see below).

### D5 — Region-label confirmation

| city | scored_against_region | expected_region | ref_file_exists | status |
| --- | --- | --- | --- | --- |
| nyc | middle_atlantic | middle_atlantic | True | OK |
| la | pacific | pacific | True | OK |
| austin | west_south_central | west_south_central | True | OK |

D5 PASS: all three cities score against their correct CBECS region file.
No "CBECS NE label for an LA cell" mismatch found — the CP-3/CP-4 flag is cleared.

### Table C — national gates on total_eui_kwh_m2 (fans EXCLUDED)

| city | region | n | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | r2 | r2_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nyc | middle_atlantic | 3268 | −1.086 | True | 59.002 | False | 0.3363 | False | 0.5466 | False |
| la | pacific | 561 | −29.638 | False | 81.736 | False | 0.2186 | False | 0.6946 | True |
| austin | west_south_central | 1481 | −31.884 | False | 89.608 | False | 0.3036 | False | 0.5673 | False |

### Table D — national gates on total_eui + fans_eui (fans INCLUDED)

| city | region | n | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | r2 | r2_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nyc | middle_atlantic | 3268 | −0.514 | True | 58.849 | False | 0.3420 | False | 0.5456 | False |
| la | pacific | 561 | −29.079 | False | 81.330 | False | 0.2135 | False | 0.6931 | True |
| austin | west_south_central | 1481 | −31.352 | False | 89.283 | False | 0.3075 | False | 0.5665 | False |

### Side-by-side: Phase-D (raw metered) vs Phase-C scalar-basis best

Phase-C national baseline: identity combo (cooling_cop=1.0/1.0/1.0/1.0), which achieved the
best NMBE pass count (3/3 NMBE pass, 0/3 CV(RMSE) pass) in RESULT_national_cbecs_rescore.md.
The city-winner combo (cop=3.5) achieved 0/3 NMBE pass and 0/3 CV(RMSE) pass.

| region | phaseC_identity_nmbe | phaseC_identity_nmbe_pass | phaseC_identity_cv_rmse | phaseC_identity_cv_rmse_pass | phaseC_identity_ks_d | phaseC_identity_ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | +5.041 | True | 54.094 | False | 0.4041 | False |
| pacific | +7.917 | True | 67.800 | False | 0.4431 | False |
| west_south_central | +1.355 | True | 72.593 | False | 0.4670 | False |

| region | phaseD_fans_out_nmbe | phaseD_fans_out_nmbe_pass | phaseD_fans_out_cv_rmse | phaseD_fans_out_cv_rmse_pass | phaseD_fans_out_ks_d | phaseD_fans_out_ks_d_pass | phaseD_fans_in_nmbe | phaseD_fans_in_nmbe_pass | phaseD_fans_in_cv_rmse | phaseD_fans_in_cv_rmse_pass | phaseD_fans_in_ks_d | phaseD_fans_in_ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | −1.086 | True | 59.002 | False | 0.3363 | False | −0.514 | True | 58.849 | False | 0.3420 | False |
| pacific | −29.638 | False | 81.736 | False | 0.2186 | False | −29.079 | False | 81.330 | False | 0.2135 | False |
| west_south_central | −31.884 | False | 89.608 | False | 0.3036 | False | −31.352 | False | 89.283 | False | 0.3075 | False |

Summary pass counts (Phase-C identity vs Phase-D):

| model | fans_variant | n_nmbe_pass (/3) | n_cv_rmse_pass (/3) | n_ks_d_pass (/3) |
| --- | --- | --- | --- | --- |
| Phase-C identity (cop=1.0) | N/A | 3 | 0 | 0 |
| Phase-D metered | fans-excluded | 1 | 0 | 0 |
| Phase-D metered | fans-included | 1 | 0 | 0 |

---

_CP-5 verdict (go/no-go on Phase-D as new baseline) to be written by manager._
