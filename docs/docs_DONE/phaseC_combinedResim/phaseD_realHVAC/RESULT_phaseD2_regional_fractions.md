# RESULT — Phase-D2 Regional-Fraction Re-score (CP-2 verdict data, DD3b)

- **Task:** T05 / T06, PLAN_regional_service_load_fractions.md
- **Method:** DD3b ratio-tilt regional fractions (see RESULT_regional_fraction_derivation.md, GUARD PASS).
- **Driver:** `scripts/validation/phaseD_regional_reconstruct_rescore.py`
- **Baseline:** phaseD2 (`OPENUBEM_PHASED_SUBDIR=phaseD2`), 12 cells, 8,160 rows, 8,160 success.
- **Date:** 2026-06-26
- **Scope:** reporting-layer only; reconstructed total is the only quantity that changes between national and regional passes. recon ≥ raw violations = 0 both passes; all reconstructed totals finite; 5,286 rows received the regional basis under the regional pass (national pass: 0).

---

## §A modeled_frac (large_office) national vs regional

| region | modeled_frac | vs national 0.8300 | uplift 1/mf |
|---|---|---|---|
| national (table4) | 0.8300 | — | 1.205 |
| middle_atlantic | 0.8633 | +0.0333 (cold → lower uplift) | 1.158 |
| pacific | 0.7706 | −0.0594 (mild → higher uplift) | 1.298 |
| west_south_central | 0.8093 | −0.0207 (mild → higher uplift) | 1.236 |

(Full per-region×group mf_adj table in RESULT_regional_fraction_derivation.md §3.)

---

## §B City-anchor deltas: national vs regional (ALL archetypes)

delta = (model_recon_median − measured)/measured × 100. Regression flag = a PASSING anchor (|delta|≤ band) that moves OUT of band, or any worsening of an already-passing NYC/LA segment.

| city | segment | n | measured | delta NATIONAL | delta REGIONAL | movement |
|---|---|---|---|---|---|---|
| nyc | Office | 2570 | 183.9 | +23.3% | +18.0% | improved (closer to 0) |
| nyc | Multifamily | 1036 | 226.2 | +8.8% | +8.8% | unchanged (DD5 national fallback) |
| nyc | Overall | 3746 | 219.2 | +5.6% | +2.1% | improved; stays in band |
| la | Office | 372 | 121.5 | +4.5% | +12.3% | moved away from 0 (still single-digit→low-double) |
| la | Multifamily | 1775 | 115.8 | −9.2% | −9.2% | unchanged (DD5 national fallback) |
| la | Warehouse | 38 | 33.9 | +9.8% | +31.2% | WORSENED (see flag below) |
| la | Overall | 2317 | 113.6 | −4.8% | −3.7% | improved; stays in band |
| austin | Office | 1244 | 162.3 | −12.6% | −9.3% | improved (now single-digit) |
| austin | Overall | 1447 | 162.0 | −11.7% | −8.6% | improved (now single-digit) |

### Excl. food-service (R5 variant)

| city | segment | delta NATIONAL | delta REGIONAL |
|---|---|---|---|
| nyc | Overall (excl. food) | +5.6% | +2.0% |
| la | Overall (excl. food) | −4.8% | −3.7% |
| austin | Overall (excl. food) | −12.4% | −9.1% |

### Regression flags (NYC/LA passing anchors must not break)

- **NYC Office** +23.3→+18.0: improved. NYC Office was already over-predicting; regional reduces it. NOT a regression.
- **NYC Overall** +5.6→+2.1: improved, stays in passing band. NOT a regression.
- **LA Overall** −4.8→−3.7: improved, stays in passing band. NOT a regression.
- **LA Office** +4.5→+12.3: moved from low single-digit to low double-digit (regional PAC office uplift 1.298 > national 1.205). This is a directional cost — LA Office over-predicts more under regional. It is the price of pulling the LA *national CBECS NMBE* toward zero (§C). FLAG for CP-2: LA Office city-anchor delta degraded by +7.8 pts.
- **LA Warehouse** +9.8→+31.2: WORSENED materially. Regional PAC warehouse mf_adj 0.5692 (vs national 0.68) → uplift 1.757 vs 1.471. n=38 (small). FLAG for CP-2: LA Warehouse is a city anchor and regional fractions push it well out of band. Driven by CBECS Pacific warehouses allocating far more energy to non-modeled "Other" than national.
- **LA/NYC Multifamily**: unchanged (DD5 keeps national) — correct, MF already passes.

---

## §C National CBECS gates: national vs regional (THE HEADLINE TEST)

| city | region | n | NMBE NAT | NMBE REG | NMBE pass NAT→REG | CV_RMSE NAT→REG | KS_d NAT→REG | R² NAT→REG |
|---|---|---|---|---|---|---|---|---|
| nyc | middle_atlantic | 3268 | +12.240 | +7.698 | False → **True** | 49.544 → 49.523 | 0.4038 → 0.3829 | 0.8359 → 0.8474 |
| la | pacific | 561 | −16.791 | −6.101 | False → **True** | 61.975 → 53.964 | 0.2954 → 0.3279 | 0.9240 → 0.9090 |
| austin | west_south_central | 1481 | −12.644 | −9.914 | False → **True** | 52.806 → 51.201 | 0.3756 → 0.3957 | 0.7924 → 0.7840 |

All three regions: NMBE gate FLIPS from FAIL to **PASS** (|NMBE| < 10). CV_RMSE/KS/R² remain structurally similar (CV/KS still fail their thresholds in all three under both passes — unchanged story, structural per §0 thesis). LA CV_RMSE improved notably (61.975→53.964).

---

## §D Predicted vs actual NMBE movement (D2 prize-sizing)

| region | predicted (D2) | actual NATIONAL | actual REGIONAL | actual movement | matches prediction? |
|---|---|---|---|---|---|
| NYC (middle_atlantic) | +12 → single digits (~0) | +12.24 | +7.70 | −4.54 toward 0 | YES (single-digit, passes) |
| LA (pacific) | −17 → single digits (~0) | −16.79 | −6.10 | +10.69 toward 0 | YES (single-digit, passes) |
| Austin (west_south_central) | −13 → single digits (~0) | −12.64 | −9.91 | +2.73 toward 0 | YES (single-digit, passes; proxy-confounded) |

All three regions move toward zero into the passing band, in the predicted direction, with no anchor-fitting (fractions are pure CBECS climate ratio × validated table4 level). LA shows the largest correction (mild-climate uplift increase), NYC second, Austin smallest.

---

## §E Sanity / integrity

- 8,160 success rows both passes; recon ≥ raw violations = 0 both; all reconstructed totals finite.
- Regional pass applied regional basis to 5,286 rows; national pass to 0 (national path byte-identical).
- large_office modeled_frac verified distinct: national 0.8300, MA 0.8633, PAC 0.7706, WSC 0.8093.
- No resim, no IDF/DESIGN edit. The 05_results gpkgs were not modified.
- No anchor-fitting: r_factor is FINALWT-weighted CBECS only; level is pre-validated table4.

---

## §F Open items for CP-2 (manager verdict — NOT decided here)

1. National NMBE gate passes all three regions under regional fractions (the §0 goal achieved).
2. LA Office city-anchor delta degraded +4.5→+12.3 and LA Warehouse +9.8→+31.2 (n=38). NYC/LA *Overall* and NYC Office did NOT regress (all improved or held). Whether the LA Office/Warehouse city-anchor cost is acceptable against the national-NMBE win is the CP-2 trade-off.
3. CV_RMSE/KS still fail in all regions both passes (structural, unchanged) — regional fractions are a mean (NMBE) lever only, as predicted.

---

_Auto-generated from phaseD_regional_reconstruct_rescore.py, 2026-06-26 (DD3b). Data only — manager writes the CP-2 verdict; user ratifies any baseline change._
