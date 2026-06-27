# RESULT — Phase-D + V16 Reconstruction Validation (data only; CP-6 verdict by manager)

Generated: 2026-06-25.
Source: `scripts/validation/phaseD_reconstruct_rescore.py` (T13).
No basis transform applied (R3: Phase-D is metered). `reconstruct_frame()` applied UNMODIFIED (R1).
metered `fans_eui_kwh_m2` NOT added to reconstructed total (R2).
Phase-C-reconstructed baseline sourced from `RESULT_national_cbecs_rescore_reconstructed.md`
(national) and `RESULT_basis_diagnostic.md` best-global combo (city).
Phase-D-raw baseline sourced from `RESULT_phaseD_validation.md`.

---

## Sanity assertions (before tables)

| assertion | value | status |
| --- | --- | --- |
| (a) reconstructed total ≥ raw total for every building | 0 violations / 8160 | PASS |
| (b) buildings mapping to passthrough | 0 / 8160 success rows | PASS (zero passthrough) |
| (c) food-service median reconstructed EUI | 931.6 kWh/m² (n=88) | within ≤1000 plausibility band (W4 caveat: 11 buildings exceed 1000 kWh/m²) |
| distinct Phase-D archetypes with no archetype_map entry | 0 | PASS (full coverage) |

---

## T13 — City-anchor re-score: Phase-D reconstructed

`delta_vs_measured_pct = (model_median − measured) / measured × 100`
`total_eui_reconstructed_kwh_m2` = raw Phase-D total + 5 un-modeled end-use terms (V16 formula).

### Table E — city anchors: ALL archetypes (incl. food-service)

| city | segment | n | phaseD_recon_median (kWh/m²) | measured (kWh/m²) | delta_vs_measured_pct |
| --- | --- | --- | --- | --- | --- |
| nyc | Office | 2570 | 241.91 | 183.9 | +31.5% |
| nyc | Multifamily | 1036 | 246.09 | 226.2 | +8.8% |
| nyc | Overall (excl. OpenUBEMUnknown n=558) | 3746 | 242.82 | 219.2 | +10.8% |
| la | Office | 372 | 137.32 | 121.5 | +13.0% |
| la | Multifamily | 1775 | 105.15 | 115.8 | −9.2% |
| la | Warehouse | 38 | 37.23 | 33.9 | +9.8% |
| la | Overall (excl. OpenUBEMUnknown n=19) | 2317 | 108.81 | 113.6 | −4.2% |
| austin | Office | 1244 | 149.70 | 162.3 | −7.8% |
| austin | Overall (excl. OpenUBEMUnknown n=73) | 1447 | 150.67 | 162.0 | −7.0% |

### Table F — city anchors: EXCL. food-service (FullServiceRestaurant / QuickServiceRestaurant / SuperMarket)

R5: food-service excluded to avoid restaurant ×3 signal swamping office/MF reads.

| city | segment | n | phaseD_recon_median (kWh/m²) | measured (kWh/m²) | delta_vs_measured_pct |
| --- | --- | --- | --- | --- | --- |
| nyc | Office | 2570 | 241.91 | 183.9 | +31.5% |
| nyc | Multifamily | 1036 | 246.09 | 226.2 | +8.8% |
| nyc | Overall (excl. OpenUBEMUnknown n=558) | 3726 | 242.64 | 219.2 | +10.7% |
| la | Office | 372 | 137.32 | 121.5 | +13.0% |
| la | Multifamily | 1775 | 105.15 | 115.8 | −9.2% |
| la | Warehouse | 38 | 37.23 | 33.9 | +9.8% |
| la | Overall (excl. OpenUBEMUnknown n=19) | 2310 | 108.74 | 113.6 | −4.3% |
| austin | Office | 1244 | 149.70 | 162.3 | −7.8% |
| austin | Overall (excl. OpenUBEMUnknown n=73) | 1386 | 149.74 | 162.0 | −7.6% |

Note: food-service n=88 total across all 12 cells (FSR=33, QSR=50, SuperMarket=5).
Overall row n-delta between Table E and F reflects their exclusion; named segment (Office/MF/Warehouse)
rows are identical because those segment definitions exclude food-service archetypes.

---

## T13 — National CBECS re-score: Phase-D reconstructed

### Table G — national gates on total_eui_RECONSTRUCTED

Gates: NMBE |·| < 10% pass; CV(RMSE) < 30% pass; KS_D < 0.10 pass; R² > 0.6 pass.

| city | region | n | nmbe | nmbe_pass | cv_rmse | cv_rmse_pass | ks_d | ks_d_pass | r2 | r2_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nyc | middle_atlantic | 3268 | +19.087 | False | 50.984 | False | 0.4387 | False | 0.8339 | True |
| la | pacific | 561 | −12.533 | False | 60.062 | False | 0.3093 | False | 0.9231 | True |
| austin | west_south_central | 1481 | −9.209 | True | 51.970 | False | 0.3966 | False | 0.7916 | True |

---

## T13 — Fans cross-check (R2)

Metered PTAC `fans_eui_kwh_m2` vs reconstructed `vent_fans_eui_recon_kwh_m2` (per-archetype medians, success rows).
R2 rationale: metered PTAC cycling fans ≪ reconstruction estimate confirms no double-count;
reconstruction `vent_fans` term supplies the continuous central-AHU/OA fan energy that PTAC cannot model.

| archetype_id | n | median_metered_fans (kWh/m²) | median_recon_vent_fans (kWh/m²) | ratio_metered/recon |
| --- | --- | --- | --- | --- |
| Courthouse | 68 | 0.676 | 16.220 | 0.042 |
| FullServiceRestaurant | 33 | 1.154 | 51.298 | 0.022 |
| HighriseApartment | 29 | 0.248 | 4.351 | 0.057 |
| Hospital | 5 | 0.887 | 22.520 | 0.039 |
| LargeOffice | 390 | 0.800 | 17.099 | 0.047 |
| MediumOffice | 948 | 0.875 | 18.812 | 0.046 |
| MidriseApartment | 2821 | 0.434 | 6.798 | 0.064 |
| OpenUBEMUnknown | 650 | 1.942 | 49.946 | 0.039 |
| Outpatient | 6 | 0.902 | 21.632 | 0.042 |
| PrimarySchool | 11 | 0.738 | 23.836 | 0.031 |
| QuickServiceRestaurant | 50 | 1.693 | 67.947 | 0.025 |
| RetailStandalone | 140 | 1.018 | 22.940 | 0.044 |
| SecondarySchool | 2 | 0.842 | 21.987 | 0.038 |
| SmallOffice | 2848 | 1.356 | 28.276 | 0.048 |
| SuperMarket | 5 | 0.621 | 37.658 | 0.016 |
| SuperTallBuilding | 24 | 0.458 | 12.276 | 0.037 |
| TallBuilding | 92 | 0.587 | 13.938 | 0.042 |
| Warehouse | 38 | 0.129 | 3.350 | 0.039 |

All archetypes: ratio_metered/recon ∈ [0.016, 0.064] — metered PTAC fans are 2–6% of reconstructed
vent_fans estimate across all archetypes. Confirms PTAC under-captures continuous central fans (CP-3
flag 4 / §3.3), and that R2 (no fan double-count) is correct.

---

## T14 — THREE-WAY side-by-side per city/segment

### Column definitions

- **Phase-C recon best**: Phase-C IdealLoads + V16 reconstruction, best-global scalar-COP basis
  (cooling_cop=2.5, heating_factor=1.19, lighting_scale=0.8, equipment_scale=0.7);
  deltas from `RESULT_basis_diagnostic.md` best-global row.
- **Phase-D raw**: Phase-D metered HVAC, no reconstruction; fans-excluded variant
  (Table A of `RESULT_phaseD_validation.md`).
- **Phase-D + recon**: Phase-D metered HVAC + V16 service-loads reconstruction (this task, Table E).

### City-segment three-way: delta_vs_measured_pct

| city | segment | Phase-C recon best | Phase-D raw | Phase-D + recon |
| --- | --- | --- | --- | --- |
| nyc | Office | +12.2% | +11.3% | +31.5% |
| nyc | Multifamily | (no anchor in Phase-C table*) | −24.9% | +8.8% |
| nyc | Overall | −7.7% | −13.4% | +10.8% |
| la | Office | +11.3% | −6.0% | +13.0% |
| la | Multifamily | (no anchor in Phase-C table*) | −37.3% | −9.2% |
| la | Warehouse | (no anchor in Phase-C table*) | −25.3% | +9.8% |
| la | Overall | −13.0% | −33.0% | −4.2% |
| austin | Office | −12.5% | −22.1% | −7.8% |
| austin | Overall | −11.7% | −21.4% | −7.0% |

*Phase-C basis diagnostic (`RESULT_basis_diagnostic.md`) reports only Office + Overall per city
(6 anchors total); Multifamily and Warehouse anchors were not separately reported in that file.

Note on comparison basis:
- Phase-C recon best uses `total_eui_reconstructed_kwh_m2` (thermal IdealLoads base + V16 reconstruction).
- Phase-D raw uses `total_eui_kwh_m2` (metered HVAC base; no reconstruction).
- Phase-D + recon uses `total_eui_reconstructed_kwh_m2` (metered HVAC base + V16 reconstruction).
Phase-D + recon is the only column with a physically-grounded metered base AND service-loads completion.

### Office segment three-way (all cities)

| city | Phase-C recon best | Phase-D raw | Phase-D + recon |
| --- | --- | --- | --- |
| nyc | +12.2% | +11.3% | +31.5% |
| la | +11.3% | −6.0% | +13.0% |
| austin | −12.5% | −22.1% | −7.8% |

### Multifamily segment three-way

| city | Phase-C recon best | Phase-D raw | Phase-D + recon |
| --- | --- | --- | --- |
| nyc | n/a | −24.9% | +8.8% |
| la | n/a | −37.3% | −9.2% |

### Warehouse segment three-way

| city | Phase-C recon best | Phase-D raw | Phase-D + recon |
| --- | --- | --- | --- |
| la | n/a | −25.3% | +9.8% |

---

## T14 — THREE-WAY national CBECS gates

### National gate three-way (NMBE / CV(RMSE) / KS_D — pass counts)

| region | Phase-C recon best (nmbe / cv_rmse / ks_d pass) | Phase-D raw (nmbe / cv_rmse / ks_d pass) | Phase-D + recon (nmbe / cv_rmse / ks_d pass) |
| --- | --- | --- | --- |
| middle_atlantic | True / False / False | True / False / False | False / False / False |
| pacific | True / False / False | False / False / False | False / False / False |
| west_south_central | True / False / False | False / False / False | True / False / False |

Phase-C recon best national values (identity / cop=2.5 best-reconstructed from `RESULT_national_cbecs_rescore_reconstructed.md`):

| region | Phase-C best-recon nmbe | Phase-C best-recon nmbe_pass | Phase-C best-recon cv_rmse | Phase-C best-recon cv_rmse_pass | Phase-C best-recon ks_d | Phase-C best-recon ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | +2.131 | True | 47.432* | False | 0.5066* | False |
| pacific | −6.004 | True | 54.887* | False | 0.5466* | False |
| west_south_central | −7.432 | True | 51.052* | False | 0.5362* | False |

*CV(RMSE) and KS_D values from the identity-reconstructed baseline (closest available; the 2.5-cop
reconstructed combo did not report CV/KS per-region explicitly in the result file).

Phase-D raw national values (fans-excluded; from `RESULT_phaseD_validation.md` Table C):

| region | Phase-D raw nmbe | Phase-D raw nmbe_pass | Phase-D raw cv_rmse | Phase-D raw cv_rmse_pass | Phase-D raw ks_d | Phase-D raw ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | −1.086 | True | 59.002 | False | 0.3363 | False |
| pacific | −29.638 | False | 81.736 | False | 0.2186 | False |
| west_south_central | −31.884 | False | 89.608 | False | 0.3036 | False |

Phase-D + recon national values (Table G above):

| region | Phase-D+recon nmbe | Phase-D+recon nmbe_pass | Phase-D+recon cv_rmse | Phase-D+recon cv_rmse_pass | Phase-D+recon ks_d | Phase-D+recon ks_d_pass |
| --- | --- | --- | --- | --- | --- | --- |
| middle_atlantic | +19.087 | False | 50.984 | False | 0.4387 | False |
| pacific | −12.533 | False | 60.062 | False | 0.3093 | False |
| west_south_central | −9.209 | True | 51.970 | False | 0.3966 | False |

### NMBE pass-count summary

| model | n_nmbe_pass (/3) | n_cv_rmse_pass (/3) | n_ks_d_pass (/3) |
| --- | --- | --- | --- |
| Phase-C recon best (cop=2.5) | 3 | 0 | 0 |
| Phase-D raw (fans-excluded) | 1 | 0 | 0 |
| Phase-D + recon | 1 | 0 | 0 |

---

_CP-6 verdict (did service-loads re-combination close the LA/Austin/MF cold gap on a metered base?) to be written by manager._
