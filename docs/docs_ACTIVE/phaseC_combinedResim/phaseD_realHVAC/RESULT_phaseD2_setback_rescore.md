# RESULT — phaseD2 Setback Rescore Side-by-Side

- **Generated:** 2026-06-26
- **Drivers:** `scripts/validation/phaseD_city_rescore.py`, `scripts/validation/phaseD_national_cbecs_rescore.py`, `scripts/validation/phaseD_reconstruct_rescore.py`
- **Env var gate (S6):** `OPENUBEM_PHASED_SUBDIR` — default `phaseD`; set to `phaseD2` for setback-fix tree
- **Row counts (both trees):** 8,160 loaded / 8,160 success / 12 cells

---

## (a) City-Anchor Table: phaseD vs phaseD2 vs CITY_ANCHORS

Driver: `phaseD_city_rescore.py` run twice with `OPENUBEM_PHASED_SUBDIR=phaseD` and `=phaseD2`.

### Table A — fans EXCLUDED (`total_eui_kwh_m2`)

| city | segment | n | phaseD model median | phaseD2 model median | measured | phaseD Δ% | phaseD2 Δ% |
|---|---|---|---|---|---|---|---|
| nyc | Office | 2570 | 204.62 | 191.45 | 183.9 | +11.3% | +4.1% |
| nyc | Multifamily | 1036 | 169.81 | 169.81 | 226.2 | −24.9% | −24.9% |
| nyc | Overall (excl. Unknown n=558) | 3746 | 189.87 | 182.93 | 219.2 | −13.4% | −16.5% |
| la | Office | 372 | 114.18 | 105.75 | 121.5 | −6.0% | −13.0% |
| la | Multifamily | 1775 | 72.56 | 72.56 | 115.8 | −37.3% | −37.3% |
| la | Warehouse | 38 | 25.31 | 25.31 | 33.9 | −25.3% | −25.3% |
| la | Overall (excl. Unknown n=19) | 2317 | 76.13 | 76.13 | 113.6 | −33.0% | −33.0% |
| austin | Office | 1244 | 126.40 | 119.83 | 162.3 | −22.1% | −26.2% |
| austin | Overall (excl. Unknown n=73) | 1447 | 127.30 | 120.63 | 162.0 | −21.4% | −25.5% |

### Table B — fans INCLUDED (`total_eui_kwh_m2 + fans_eui_kwh_m2`)

| city | segment | n | phaseD model median | phaseD2 model median | measured | phaseD Δ% | phaseD2 Δ% |
|---|---|---|---|---|---|---|---|
| nyc | Office | 2570 | 206.06 | 192.76 | 183.9 | +12.0% | +4.8% |
| nyc | Multifamily | 1036 | 170.34 | 170.34 | 226.2 | −24.7% | −24.7% |
| nyc | Overall (excl. Unknown n=558) | 3746 | 190.74 | 183.93 | 219.2 | −13.0% | −16.1% |
| la | Office | 372 | 115.09 | 106.52 | 121.5 | −5.3% | −12.3% |
| la | Multifamily | 1775 | 72.88 | 72.88 | 115.8 | −37.1% | −37.1% |
| la | Warehouse | 38 | 25.44 | 25.44 | 33.9 | −24.9% | −24.9% |
| la | Overall (excl. Unknown n=19) | 2317 | 76.52 | 76.50 | 113.6 | −32.6% | −32.7% |
| austin | Office | 1244 | 127.54 | 120.84 | 162.3 | −21.4% | −25.5% |
| austin | Overall (excl. Unknown n=73) | 1447 | 128.38 | 121.73 | 162.0 | −20.8% | −24.9% |

---

## (b) National CBECS Gates per Region: phaseD vs phaseD2

Driver: `phaseD_national_cbecs_rescore.py` run twice.

Thresholds: NMBE pass ≤ ±10%, CV(RMSE) pass ≤ 30%, KS_D pass ≤ 0.10, R² pass ≥ 0.60.

### Table C — fans EXCLUDED (`total_eui_kwh_m2`)

| tree | city | region | n | NMBE | NMBE_pass | CV(RMSE) | CV_pass | KS_D | KS_pass | R² | R²_pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phaseD | nyc | middle_atlantic | 3268 | −1.09% | PASS | 59.00% | FAIL | 0.3363 | FAIL | 0.547 | FAIL |
| phaseD2 | nyc | middle_atlantic | 3268 | −6.85% | PASS | 60.40% | FAIL | 0.2938 | FAIL | 0.571 | FAIL |
| phaseD | la | pacific | 561 | −29.64% | FAIL | 81.74% | FAIL | 0.2186 | FAIL | 0.695 | PASS |
| phaseD2 | la | pacific | 561 | −33.23% | FAIL | 83.89% | FAIL | 0.2493 | FAIL | 0.713 | PASS |
| phaseD | austin | west_south_central | 1481 | −31.88% | FAIL | 89.61% | FAIL | 0.3036 | FAIL | 0.567 | FAIL |
| phaseD2 | austin | west_south_central | 1481 | −34.79% | FAIL | 90.62% | FAIL | 0.3029 | FAIL | 0.572 | FAIL |

**Pass counts — fans excluded: phaseD: NMBE 1/3, CV 0/3, KS 0/3, R² 1/3. phaseD2: NMBE 1/3, CV 0/3, KS 0/3, R² 1/3.**

### Table D — fans INCLUDED (`total_eui_kwh_m2 + fans_eui_kwh_m2`)

| tree | city | region | n | NMBE | NMBE_pass | CV(RMSE) | CV_pass | KS_D | KS_pass | R² | R²_pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phaseD | nyc | middle_atlantic | 3268 | −0.51% | PASS | 58.85% | FAIL | 0.3420 | FAIL | 0.546 | FAIL |
| phaseD2 | nyc | middle_atlantic | 3268 | −6.32% | PASS | 60.20% | FAIL | 0.2957 | FAIL | 0.571 | FAIL |
| phaseD | la | pacific | 561 | −29.08% | FAIL | 81.33% | FAIL | 0.2135 | FAIL | 0.693 | PASS |
| phaseD2 | la | pacific | 561 | −32.71% | FAIL | 83.50% | FAIL | 0.2443 | FAIL | 0.712 | PASS |
| phaseD | austin | west_south_central | 1481 | −31.35% | FAIL | 89.28% | FAIL | 0.3075 | FAIL | 0.567 | FAIL |
| phaseD2 | austin | west_south_central | 1481 | −34.28% | FAIL | 90.29% | FAIL | 0.3036 | FAIL | 0.571 | FAIL |

**Pass counts — fans included: phaseD: NMBE 1/3, CV 0/3, KS 0/3, R² 1/3. phaseD2: NMBE 1/3, CV 0/3, KS 0/3, R² 1/3.**

---

## (c) NYC Office Heating Delta (T18-C)

Driver: scratchpad `t18c_nyc_office_heating.py` importing `load_all_cells_phaseD` with env set.
Segment definition: archetype_id ∈ {SmallOffice, MediumOffice, LargeOffice, SmallOfficeDetailed, MediumOfficeDetailed, LargeOfficeDetailed}.

### NYC Office (all 4 cells pooled, n=2570)

| tree | median heating_eui_kwh_m2 | abs Δ (phaseD2 − phaseD) | % Δ |
|---|---|---|---|
| phaseD | 135.37 | — | — |
| phaseD2 | 122.02 | −13.35 | −9.86% |

### nyc_centre per-cell (n=588 office buildings)

| tree | median heating_eui_kwh_m2 | abs Δ | % Δ |
|---|---|---|---|
| phaseD | 92.18 | — | — |
| phaseD2 | 83.05 | −9.13 | −9.91% |

NYC all-archetype median heating: phaseD 129.80 → phaseD2 121.84 kWh/m².

---

## (d) Reconstruct Rescore: phaseD vs phaseD2

Driver: `phaseD_reconstruct_rescore.py` run twice with `OPENUBEM_PHASED_SUBDIR=phaseD` and `=phaseD2`.

### Table E — city-anchor on `total_eui_RECONSTRUCTED` (ALL archetypes)

| city | segment | n | phaseD recon median | phaseD2 recon median | measured | phaseD Δ% | phaseD2 Δ% |
|---|---|---|---|---|---|---|---|
| nyc | Office | 2570 | 241.91 | 226.72 | 183.9 | +31.5% | +23.3% |
| nyc | Multifamily | 1036 | 246.09 | 246.09 | 226.2 | +8.8% | +8.8% |
| nyc | Overall (excl. Unknown n=558) | 3746 | 242.82 | 231.48 | 219.2 | +10.8% | +5.6% |
| la | Office | 372 | 137.32 | 126.99 | 121.5 | +13.0% | +4.5% |
| la | Multifamily | 1775 | 105.15 | 105.15 | 115.8 | −9.2% | −9.2% |
| la | Warehouse | 38 | 37.23 | 37.23 | 33.9 | +9.8% | +9.8% |
| la | Overall (excl. Unknown n=19) | 2317 | 108.81 | 108.18 | 113.6 | −4.2% | −4.8% |
| austin | Office | 1244 | 149.70 | 141.86 | 162.3 | −7.8% | −12.6% |
| austin | Overall (excl. Unknown n=73) | 1447 | 150.67 | 143.09 | 162.0 | −7.0% | −11.7% |

### Table F — city-anchor on `total_eui_RECONSTRUCTED` (EXCL. food-service)

| city | segment | n | phaseD recon median | phaseD2 recon median | measured | phaseD Δ% | phaseD2 Δ% |
|---|---|---|---|---|---|---|---|
| nyc | Office | 2570 | 241.91 | 226.72 | 183.9 | +31.5% | +23.3% |
| nyc | Multifamily | 1036 | 246.09 | 246.09 | 226.2 | +8.8% | +8.8% |
| nyc | Overall (excl. Unknown n=558, excl. food) | 3726 | 242.64 | 231.39 | 219.2 | +10.7% | +5.6% |
| la | Office | 372 | 137.32 | 126.99 | 121.5 | +13.0% | +4.5% |
| la | Multifamily | 1775 | 105.15 | 105.15 | 115.8 | −9.2% | −9.2% |
| la | Warehouse | 38 | 37.23 | 37.23 | 33.9 | +9.8% | +9.8% |
| la | Overall (excl. Unknown n=19, excl. food) | 2310 | 108.74 | 108.15 | 113.6 | −4.3% | −4.8% |
| austin | Office | 1244 | 149.70 | 141.86 | 162.3 | −7.8% | −12.6% |
| austin | Overall (excl. Unknown n=73, excl. food) | 1386 | 149.74 | 141.98 | 162.0 | −7.6% | −12.4% |

### Table G — national gates on `total_eui_RECONSTRUCTED`

| tree | city | region | n | NMBE | NMBE_pass | CV(RMSE) | CV_pass | KS_D | KS_pass | R² | R²_pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phaseD | nyc | middle_atlantic | 3268 | +19.09% | FAIL | 50.98% | FAIL | 0.4387 | FAIL | 0.834 | PASS |
| phaseD2 | nyc | middle_atlantic | 3268 | +12.24% | FAIL | 49.54% | FAIL | 0.4038 | FAIL | 0.836 | PASS |
| phaseD | la | pacific | 561 | −12.53% | FAIL | 60.06% | FAIL | 0.3093 | FAIL | 0.923 | PASS |
| phaseD2 | la | pacific | 561 | −16.79% | FAIL | 61.98% | FAIL | 0.2954 | FAIL | 0.924 | PASS |
| phaseD | austin | west_south_central | 1481 | −9.21% | PASS | 51.97% | FAIL | 0.3966 | FAIL | 0.792 | PASS |
| phaseD2 | austin | west_south_central | 1481 | −12.64% | FAIL | 52.81% | FAIL | 0.3756 | FAIL | 0.792 | PASS |

**Pass counts — reconstructed: phaseD: NMBE 1/3, CV 0/3, KS 0/3, R² 3/3. phaseD2: NMBE 0/3, CV 0/3, KS 0/3, R² 3/3.**
