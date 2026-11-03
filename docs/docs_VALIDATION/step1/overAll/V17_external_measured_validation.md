# V17 — External Measured-Data Validation

**Date:** 2026-06-17
**Author:** Manager (Opus session)
**Status:** Report-only synthesis. No EnergyPlus resimulation, no gate tuning, no code change. Per **V-R5-5** gates are diagnostic; this document recommends calibration targets, it does not implement them.

## 0. What this is

The first three validation layers compared OpenUBEM against (a) reference *distributions* (CBECS means), (b) reference *models* (DOE/PNNL round-trip), and (c) literature error bands. None of those is **measured ground truth for the cities we actually modeled.** This document closes that gap: it scores our modeled site-EUI distributions against **real metered building data** from the municipal benchmarking-disclosure programs of the three modeled cities, plus national per-archetype reference values and measured end-use splits.

Inputs (all in `docs/validations/external_literature/`):

| # | Source | Geography | Provenance |
|---|---|---|---|
| RESULT_1 | NYC LL84/133 disclosure, CY2024, N≈30k cleaned | NYC (CZ 4A) | **Measured microdata** (NYC Open Data `5zyy-y8am`) |
| RESULT_2 | LA EBEWE + CA AB 802, CY2024 | LA (CZ 3B) | **Measured microdata** (LADBS `9yda-i4ya`, CEC) |
| RESULT_3 | CBECS-2018 West-South-Central weighted | Austin (CZ 2A) | **ESTIMATED proxy** — Austin ECAD does not disclose building-level EUI |
| RESULT_4 | Published UBEM accuracy (CEA/CityBES/UMI/URBANopt + NYC/TX papers) | — | Mostly verbatim |
| RESULT_5 | ENERGY STAR / CBECS national per-archetype site EUI | National | Direct reads |
| RESULT_6 | CBECS E1 / RECS measured end-use splits | National | Direct reads |

## 1. Comparison basis (read before the tables)

- **Metric:** annual **site** EUI. US disclosure data is site EUI; OpenUBEM simulates site energy. Source EUI is *not* compared.
- **OpenUBEM number used:** the **service-load-reconstructed total** (`total_eui_reconstructed_kwh_m2`), because measured disclosure EUI includes all nine end-uses. The 4-end-use simulated total (`total_eui_kwh_m2`) is a structural lower bound and is shown only where it changes the diagnosis.
- **Unit:** all measured kBtu/ft²·yr converted at **1 kBtu/ft²·yr = 3.15459 kWh/m²·yr**.
- **Statistic:** medians and p25/p75. The measured stock is right-skewed; means are distorted by reporting errors (see RESULT_1 §5).
- **Modeled distribution:** `r7_service_loads.csv`, 8,148 successful buildings across the 12 matrix cells.
- **Caveat on measured provenance:** RESULT_1/2 claim direct microdata processing. The NYC medians line up with the published LL84 values (office ≈58, multifamily ≈72 kBtu/ft²), so they are credible **benchmark bands**, not certified percentiles. RESULT_3 (Austin) is an explicitly-labelled CBECS regional proxy — treat Austin deltas as indicative only.

## 2. Interpretive frame (RESULT_4)

Published archetype UBEMs report **40–100 % per-building error** that cancels on aggregation to **1–10 % at stock scale** (UMI Boston ~5 %; CEA Aarhus NMBE <0.5 %; Dogan NYC cohort CV(RMSE) 5.6 %). This means:

- An **aggregate city median within ~±10–15 %** of measured is a *pass* by field norms.
- Our ~45 % per-building round-trip deviation (V15/R6-4) is **expected and not a defect**, provided aggregates hold.

This is the yardstick used below.

## 3. City-level scorecard

Model = reconstructed-total median; measured = disclosure standard-site-EUI median (CY2024). All kWh/m²·yr.

| City | Segment | Measured median | Model median | Δ | Verdict |
|---|---|---:|---:|---:|---|
| **NYC** (4A) | Office | 183.9 | 183.3 | **−0.3 %** | ✅ excellent |
| | Multifamily | 226.2 | 302.0 | +33.5 % | ⚠ over |
| | **Overall** | 219.2 | 246.9 | **+12.6 %** | ✅ within field band |
| **LA** (3B) | Office | 121.5 | 208.9 | +72.0 % | ❌ runs hot |
| | Multifamily | 115.8 | 153.3 | +32.4 % | ⚠ over |
| | Warehouse | 33.9 | 64.1 | +89 % | ⚠ (abs. small) |
| | **Overall** | 113.6 | 158.6 | **+39.6 %** | ❌ calibrate |
| **Austin\*** (2A) | Office | 162.3 | 187.6 | +15.6 % | ✅ acceptable (proxy) |
| | **Overall\*** | ~162 | 199.8 | +23 % | ⚠ (proxy) |

\* Austin = CBECS West-South-Central proxy, ESTIMATED.

**Headline:** NYC is the strongest validation we have — **office is essentially exact (−0.3 %)** and the city aggregate (+12.6 %) sits inside the published field band. Austin office is acceptable. **LA is the clear outlier: the model runs ~40 % hot city-wide and +72 % on office.**

## 4. Per-archetype scorecard (national, RESULT_5)

Model = all-city reconstructed-total median vs ENERGY STAR national median.

| Archetype | ESPM median | Model | Δ | Verdict |
|---|---:|---:|---:|---|
| Medium Office | 166.9 | 160.3 | −4 % | ✅ |
| Small Office | 166.9 | 190.3 | +14 % | ✅ |
| Large Office | 166.9 | 229.8 | +38 % | ⚠ |
| Mid-Rise Apartment | 187.9 | 228.8 | +22 % | ⚠ |
| Stand-alone Retail | 162.1 | 286.7 | +77 % | ❌ |
| Warehouse | 71.6 | 64.1 | −11 % | ✅ |
| **Supermarket** | 618.3 | 631.5 | **+2 %** | ✅✅ |
| Full-Service Restaurant | 1027.2 | 2158.5 | +110 % | ❌❌ |
| Quick-Service Restaurant | 1270.3 | 3307.9 | +160 % | ❌❌ |
| Primary School | 153.0 | 289.4 | +89 % | ❌ (N=11) |

## 5. End-use reconstruction validation (RESULT_6)

Measured CBECS-E1 / RECS splits **confirm the direction** of the service-load reconstruction:

- **Supermarket refrigeration ≈ 38 %** of site energy → and our supermarket reconstructed total lands at +2 % of ESPM. **The refrigeration reconstruction is validated.**
- **Restaurant cooking+refrigeration+DHW ≈ 62 %** (cooking alone 39 %) → direction correct, but our reconstructed restaurant totals overshoot ESPM by 110–160 %. **The fractions are right; the gross-up math is wrong** (a high 4-end-use base is being multiplied as if it were only ~⅓ of total, tripling restaurants).
- **Multifamily DHW ≈ 33 %** (RECS) → consistent with the reconstruction adding load, but NYC multifamily 4-end-use base (208) is already near measured (226, −8 %); reconstruction then overshoots to 302. **The apartment DHW share is being over-allocated.**

## 6. Verdict

### ✅ Validated — leave alone
1. **NYC office** (−0.3 %) and **NYC city aggregate** (+12.6 %) — within field norms; this is the platform's credibility anchor.
2. **Office archetype generally** (Small/Medium −4 to +14 %); LA office is a *climate* problem, not an office problem.
3. **Warehouse** (−11 % vs ESPM).
4. **Supermarket refrigeration reconstruction** (+2 %) — the hardest service load, and it works.
5. **The ~45 % per-building deviation** — confirmed normal by RESULT_4; do not chase it.

### ❌ Calibration targets (priority order)
1. **LA climate response (P1).** +72 % office, +40 % city-wide. LA (3B, mild Mediterranean) should produce the *lowest* EUIs of the three cities (measured overall 114 vs NYC 219); our model has LA only modestly below NYC. Suspect setpoint/HVAC-availability/envelope assumptions not capturing how little heating *and* cooling real LA buildings use. **Highest-value fix.**
2. **Restaurant service-load gross-up (P1).** +110/+160 %. Fractions (RESULT_6) are correct, so the defect is in how `table4_fraction_split` inflates a 4-end-use base for cooking-dominated types. Isolated to ~83 buildings but egregious per-building.
3. **Multifamily reconstruction (P2).** Systematic +32–34 % in NYC/LA. The 4-end-use base is already near measured; the DHW/service uplift over-allocates. Affects ~2,850 buildings — high stock weight.
4. **Stand-alone retail / primary school (P3).** +77 % / +89 % but low N and (school) no measured city anchor — verify classification before treating as a model error.
5. **OpenUBEMUnknown (650 bldgs, recon median 434).** Not a calibration issue — a *classification* gap; these should be re-typed upstream, not tuned.

### Provenance flags
- Austin rests on a CBECS proxy, not real disclosure — do not over-weight Austin deltas.
- Restaurant/supermarket/school verdicts rest on N=5–50 modeled buildings.
- Measured medians are credible bands, not certified percentiles (web-research provenance).

## 7. Recommended next step (not yet executed)

None of the above changes code. If the user greenlights calibration, the natural first cut is a **Sonnet plan doc** scoped to **(1) LA climate/HVAC assumptions** and **(2) the restaurant reconstruction gross-up** — the two P1 items — each validated against the RESULT_1/2/5 bands in this document, gates remaining report-only. The LA fix is the single highest-value change and should run first and alone so its effect is measurable.
