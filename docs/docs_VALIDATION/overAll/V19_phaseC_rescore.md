# V19 — Phase-C Re-score vs Measured Anchors

**Date:** 2026-06-20
**Author:** Manager (Opus session)
**Status:** Report-only synthesis. No EnergyPlus resimulation in this document; it re-scores the **fresh
Phase-C results** (all 12 cells re-simulated 2026-06-19 with multi-floor zoning + DOE prototype schedules +
core/perimeter geometry repair, 12/12 clean, zero exclusions) against the same measured anchors used in
[V17](V17_external_measured_validation.md). Gates remain diagnostic; this recommends calibration targets,
it does not implement them.

## 0. What this is

V17 scored the **old** model (the one carrying the 1-floor-internal-loads ÷ n_floors zoning defect that
[V18](V18_calibration_diagnosis.md) diagnosed) against real metered city data. It found LA running ~+40 % hot and flagged NYC
office (−0.3 %) as the credibility anchor — but V18 warned that the NYC match was *partly an artifact of the
defect*. Phase C fixed the defect (proper multi-floor zoning), digitized real DOE schedules (OQ-2), and
repaired degenerate core/perimeter geometry, then re-simulated all 12 cells. **V19 re-runs the V17
comparison on those fresh results** to answer two questions:

1. **Did the fixes move the numbers in the right direction?**
2. **Is LA still hot once the zoning defect is removed — i.e., was V17's LA outlier real or an artifact?**

## 1. Comparison basis (unchanged from V17)

- Metric = annual **site** EUI, kWh/m²·yr. Statistic = **median** (+ p25/p75).
- Model number = `total_eui_reconstructed_kwh_m2` median (all 9 end-uses; service loads reconstructed by the
  same tested `reconstruct_frame` Table-4 layer V17 used). 4-end-use median shown alongside as the
  structural lower bound.
- Population: **8,156** successful buildings across the 12 cells (V17 had 8,148; the +8 are previously-failed
  buildings the geometry fix-batch recovered via the one-zone-per-floor fallback — none dropped).
- Field-norm yardstick (V17 §2): aggregate city median within **±10–15 %** of measured = a *pass*.
- "Δ vs V17-old" columns isolate the **effect of the Phase-C fixes** (V19 model − V17 model).

## 2. Headline

**The fixes worked where V17 said the model was over-predicting, and they sharpened — not closed — the LA
problem.**

- **NYC city aggregate is now +10.0 %** (was +12.6 %) — solidly inside the field band. **NYC is still a
  pass.**
- **NYC multifamily went +33.5 % → +0.7 %** and **food-service went +110/+160 % → −1.6/+12 %.** These were
  V17's worst over-predictions; the DOE-schedule fix essentially resolved them.
- **The NYC office "anchor" was partly a V17 artifact, as V18 predicted.** With the ÷n_floors defect
  removed, NYC office rose −0.3 % → **+36.7 %**. The old near-perfect match was the defect under-counting
  office internal loads, coincidentally landing on the measured median.
- **LA is still hot: Overall +38.8 % (was +39.6 %), essentially unmoved by the fix (−0.6 %).** This is the
  important result — **LA's hotness was never the zoning defect.** It is a genuine climate/HVAC-response
  problem, now confirmed rather than confounded.

## 3. City-level scorecard (V19)

Model = reconstructed-total median; measured = disclosure median (CY2024). All kWh/m²·yr.

| City | Segment | n | Measured | V19 model | Δ vs measured | V17 model | Δ vs V17 (fix effect) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **NYC** | Office | 2569 | 183.9 | 251.4 | **+36.7 %** | 183.3 | +37.1 % | ❌ now over |
| | Multifamily | 1036 | 226.2 | 227.7 | **+0.7 %** | 302.0 | −24.6 % | ✅ resolved |
| | **Overall** | 3745 | 219.2 | 241.1 | **+10.0 %** | 246.9 | −2.3 % | ✅ within band |
| **LA** | Office | 369 | 121.5 | 216.7 | **+78.4 %** | 208.9 | +3.7 % | ❌ runs hot |
| | Multifamily | 1775 | 115.8 | 153.9 | +32.9 % | 153.3 | +0.4 % | ⚠ over (unmoved) |
| | Warehouse | 38 | 33.9 | 56.0 | +65.2 % | 64.1 | −12.6 % | ⚠ (abs. small) |
| | **Overall** | 2314 | 113.6 | 157.7 | **+38.8 %** | 158.6 | −0.6 % | ❌ calibrate |
| **Austin\*** | Office | 1244 | 162.3 | 229.0 | +41.1 % | 187.6 | +22.1 % | ⚠ over (proxy) |
| | **Overall\*** | 1447 | ~162 | 230.3 | +42.2 % | 199.8 | +15.3 % | ⚠ (proxy) |

\* Austin = CBECS West-South-Central proxy, ESTIMATED — indicative only.
Overall excludes `OpenUBEMUnknown` (NYC 558, LA 19, Austin 73) — a classification gap, not a building type.

## 4. Per-archetype national scorecard (all 12 cells pooled)

| Archetype | n | ESPM | V19 model | Δ vs ESPM | V17 model | Δ vs V17 (fix effect) |
|---|---:|---:|---:|---:|---:|---:|
| MediumOffice | 946 | 166.9 | 220.1 | +31.9 % | 160.3 | +37.3 % |
| SmallOffice | 2848 | 166.9 | 254.3 | +52.3 % | 190.3 | +33.6 % |
| LargeOffice | 388 | 166.9 | 214.6 | +28.6 % | 229.8 | −6.6 % |
| MidriseApartment | 2821 | 187.9 | 173.8 | **−7.5 %** | 228.8 | −24.1 % |
| RetailStandalone | 140 | 162.1 | 285.4 | +76.0 % | 286.7 | −0.5 % |
| Warehouse | 38 | 71.6 | 56.0 | −21.8 % | 64.1 | −12.6 % |
| SuperMarket† | 5 | 618.3 | 597.9 | −3.3 % | 631.5 | −5.3 % |
| FullServiceRestaurant | 33 | 1027.2 | 1010.3 | **−1.6 %** | 2158.5 | −53.2 % |
| QuickServiceRestaurant | 50 | 1270.3 | 1423.6 | **+12.1 %** | 3307.9 | −57.0 % |
| PrimarySchool† | 11 | 153.0 | 320.7 | +109.6 % | 289.4 | +10.8 % |

† n < 12 — low-confidence.

## 5. Why the numbers moved the way they did

The two fixes pull in **opposite directions by archetype**, which is exactly what produces the headline
pattern (offices up, dwellings/restaurants down):

1. **Multi-floor zoning (pushes loads UP):** the old defect applied one floor's internal loads divided by
   `n_floors`, drastically under-counting tall buildings. Correcting it raises internal loads most for
   floor-heavy, equipment-driven types → **offices rose +33–37 %** (Small/Medium). *LargeOffice fell −6.6 %*:
   for the tallest offices the schedule change offset the zoning increase — a heterogeneity worth a closer
   look but not material to the "office over-predicts" headline (Small+Medium dominate, n=3,794 vs 388).

2. **DOE prototype schedules / OQ-2 (pushes loads DOWN for dwellings & kitchens):** the synthetic
   occupancy-derived schedules over-counted residential lighting ~10× and kitchen-equipment runtime.
   Real DOE schedules cut both → **MidriseApartment −24 %** (to −7.5 % vs ESPM) and **food-service −53/−57 %**
   (FSR to −1.6 %, QSR to +12 % vs ESPM). This independently **validates V17 §5/§6**: the restaurant
   overshoot was a runtime/gross-up artifact, and it is now gone.

3. **Net per-city:** NYC (office + dwelling mix) nets to a small −2.3 % move and stays a pass. LA is
   dwelling-heavy (MF n=1,775 vs office n=369) and its MF barely moved (+0.4 %), so the city total is
   essentially unchanged — **the fixes simply don't touch LA's problem.**

**The LA signal, sharpened.** Measured LA overall (113.6) is **52 % of** measured NYC (219.2) — LA's mild
3B climate should make it the lowest-EUI city by far. The model puts LA at **65 % of** NYC (157.7 / 241.1):
it does place LA lower, but nowhere near low enough. LA office at +78.4 % vs measured (vs NYC office +36.7 %)
carries ~40 pts *beyond* the now-global office bias. That residual is the genuine **LA climate/HVAC-response
gap** — not zoning, not schedules.

## 6. Verdict

### ✅ Validated / resolved by Phase C
1. **NYC city aggregate (+10.0 %)** — still inside field norms; remains the platform's credibility anchor at
   the *city* level.
2. **NYC multifamily (+0.7 %)** and **MidriseApartment nationally (−7.5 % vs ESPM)** — V17's +33 % MF
   over-prediction is resolved by the DOE-schedule fix.
3. **Food-service (FSR −1.6 %, QSR +12.1 % vs ESPM)** — V17's +110/+160 % overshoot is resolved; confirms
   the V17 §6 diagnosis that the fractions were right and the runtime/gross-up was wrong.
4. **Supermarket (−3.3 %)** and **Warehouse (−21.8 %)** — stable, still reasonable.

### ❌ Calibration targets (revised priority order — supersedes V17 §6)
1. **Office over-prediction, all cities (NEW P1).** +30–52 % vs ESPM; +37/78/41 % vs measured in
   NYC/LA/Austin. The old NYC-office anchor masked this; with zoning corrected, office is now the model's
   largest *systematic* bias. Target office internal-load intensity / HVAC sizing / setpoint assumptions.
   Investigate the SmallOffice (+52 %) vs LargeOffice (+29 %) split.
2. **LA climate response (still P1).** Overall +38.8 %, unmoved by the fix → confirmed as a real
   climate/HVAC problem, not a zoning artifact. LA should be the lowest-EUI city; the model doesn't make it
   low enough. Highest-value *city-specific* fix; should run alone so its effect is measurable.
3. **Stand-alone retail (+76 %) / primary school (+110 %, n=11).** Unchanged by Phase C; verify
   classification before treating as a model error (school N is tiny, no measured city anchor).
4. **`OpenUBEMUnknown` (650 bldgs).** Still a *classification* gap, not a calibration issue — re-type
   upstream.

### Provenance flags
- Austin rests on a CBECS proxy, not real disclosure — do not over-weight Austin deltas.
- Restaurant / supermarket / school verdicts rest on n = 5–50 modeled buildings.
- Measured medians are credible bands, not certified percentiles.
- Geometry-fallback cells: the few buildings rerouted to one-zone-per-floor are industry-standard and shift
  aggregate city EUI **< 0.1 %** (deep-research RESULT_3 Defensibility Verdict) — they do not affect any
  verdict above.

## 7. Recommended next step (not yet executed)

The picture has flipped from V17: **office over-prediction is now the dominant systematic bias, and LA is a
confirmed climate problem.** If the user greenlights calibration, the natural first cut is a **Sonnet plan
doc** scoped to the two P1 items — **(1) office internal-load/HVAC assumptions** and **(2) LA
climate/HVAC response** — each validated against the measured bands here, gates remaining report-only. Per
project norms (V17 §7), the LA fix should run first and alone so its effect is isolable. This document
changes no code.
