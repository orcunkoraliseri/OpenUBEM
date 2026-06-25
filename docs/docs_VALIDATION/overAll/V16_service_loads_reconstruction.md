# V16 — Service-Loads Reconstruction (reporting-layer)

**Date:** 2026-06-17
**Author:** Phase-C manager session (Opus)
**Scope authority:** `REPORT_R5_final.md` §R6-4B (optional reporting-layer service-load
reconstruction). **No resimulation, no IDF/DESIGN change, gates report-only.**
**Plan / coefficients:** `docs/implementation/serviceLoads/PLAN_service-loads-reconstruction_2026-06-17.md`
+ `…/SERVICE_LOADS_coefficients.md` (Table 4, transcribed from the image-only deep-research PDF).
**Deliverables:** `results/r7_service_loads.csv` (8 152 buildings), `results/r7_roundtrip_recon.csv`
(19 archetypes), module `openubem/results/service_loads.py`, CLI `scripts/reconstruct_service_loads.py`.

---

## 1. What this is

The IdealLoads HVAC formulation meters only space heating + cooling; the IDF additionally models
lighting + plug equipment. It **structurally emits zero** energy for fans, pumps, service hot
water (DHW), refrigeration, and cooking/other process loads. ~42% of the Level-2 single-building
gap is exactly this missing energy (V15, R6-4B).

This work adds those five end-uses back **deterministically, as a post-processing layer**, from
the shipped `05_results` end-use EUIs and the CBECS-2018/PNNL **Table-4 archetype fraction
splits**. It produces a new *reported* whole-building EUI alongside the simulated one; it never
overwrites `05_results` and never resimulates.

## 2. Method (fraction-split completion)

For a building of archetype `A` (mapped to one of 11 Table-4 archetypes):

```
modeled_frac = f_space_heat + f_space_cool + f_lighting + f_equip_plug      (the 4 modeled uses)
E_total_est  = (heating + cooling + lighting + equipment) / modeled_frac
recon_j      = f_j × E_total_est     for j ∈ {vent_fans, pumps, swh_dhw, refrig, cooking_other}
total_reconstructed = total_simulated + Σ recon_j   (= E_total_est)
```

Anchored on all four modeled end-uses (robust); `modeled_frac ≥ 0.36` (Supermarket) so the
scale-up is numerically safe. Verified identity in the matrix: `total_eui == heating+cooling+
lighting+equipment` exactly, so the five added uses are precisely the non-modeled Table-4 columns.

## 3. Coverage

- **8 152 buildings**, all 12 cells. **8 148 reconstructed**; 4 `not_simulated` rows pass through.
- **All 18 distinct matrix archetypes map** to a Table-4 archetype → **zero passthrough among
  success rows** (after the CP-2 audit added `SuperMarket`, `Outpatient`, and four DOE-only
  round-trip types). Mapping rationale: `SERVICE_LOADS_coefficients.md`.

## 4. Matrix result — the deliverable

Mean whole-building EUI uplift from service-load completion:

| Cell | n | sim mean | recon mean | uplift | n(recon>1000) |
|---|---|---|---|---|---|
| austin_centre   | 413 | 247.4 | 424.8 | +71.7% | 31 |
| austin_rural    | 245 | 227.7 | 351.6 | +54.4% | 10 |
| austin_suburban | 437 | 197.9 | 285.9 | +44.5% | 14 |
| austin_urban    | 417 | 179.5 | 228.3 | +27.2% | 3 |
| la_centre       | 226 | 190.6 | 250.3 | +31.3% | 3 |
| la_rural        | 149 | 194.1 | 235.0 | +21.1% | 0 |
| la_suburban     | 1343 | 119.5 | 171.4 | +43.4% | 0 |
| la_urban        | 614 | 141.4 | 198.7 | +40.5% | 3 |
| nyc_centre      | 738 | 143.8 | 181.7 | +26.4% | 3 |
| nyc_rural       | 198 | 264.7 | 391.9 | +48.1% | 9 |
| nyc_suburban    | 1589 | 270.0 | 356.9 | +32.2% | 1 |
| nyc_urban       | 1779 | 175.9 | 209.2 | +18.9% | 0 |

- **Non-food-service uplift: +27.1%** (n=8 065) — a plausible, archetype-consistent restoration
  of fans/pumps/DHW/parasitics.
- **Food-service uplift: +203%** (n=83; sim mean 829 → recon mean 2 513 kWh/m²/yr): Table 4 places
  ~67% of restaurant energy in cooking+refrig+DHW, all non-modeled. **77 buildings reconstruct
  above the R5 plausibility band (>1000 kWh/m²/yr).** These are **reported, never capped** —
  their simulated base inherits the known R5 QSR plausibility-band artifact (OQ-R5-11), which the
  reconstruction amplifies. Aggregate metrics should be read with food-service broken out.

## 5. Round-trip re-evaluation — does NOT close the single-building gap

Applying the same reconstruction to the Level-2 DOE counterparts (building-fixed; `recon_total =
counter_total / modeled_frac`; report-only):

| Subset | median \|dev_sim\| | median \|dev_recon\| |
|---|---|---|
| All 19 archetypes | 43.5% | **62.3%** |
| Excluding food-service (n=17) | 47.3% | **55.3%** |

**Reconstruction widens the median deviation, it does not close it.** Why:

1. The round-trip set is a **mix of over- and under-predictors**. Adding energy helps the
   under-predictors (LargeOffice −63→−55, LargeHotel −58→−34, Warehouse −56→−35, Tall −44→−32,
   HighriseApt −84→−77) but worsens the over-predictors (SmallOffice +309→+381, MediumOffice
   +95→+135, RetailStandalone +47→+82). The over-predictors and the heavy-process archetypes
   dominate the median shift.
2. **Process-heavy archetypes over-correct hardest:** SuperMarket −31→**+90** (50% refrig),
   food-service +30→**+295** (67% cooking/refrig/DHW). A decoupled additive estimate cannot know
   the building was already over-simulated.
3. **Round-trip baseline caveat:** in `roundtrip_report.csv`, `counter_total_eui` is a constant
   **2.0×** the sum of its own four end-use columns (a convention of that Phase-C report, unlike
   the matrix where total==Σ4). The 2× rides through both `dev_sim` and `dev_recon`, so the
   re-evaluation is a **directional** indicator, not a calibration metric.

## 6. Ruling — corroborates R6-4B STOP

This result is the **expected and correct** one, and it **strengthens** the R6-4B close-out
rather than reopening it:

- The Level-2 single-building gap is **not** dominated by the missing service loads in a way that
  a deterministic reporting-layer completion can close. Restoring them and measuring against DOE
  prototypes *increases* median |dev|, because the first-order drivers are **modeled-load
  over/under-prediction** (HVAC configuration, schedules, internal-gain intensities) — exactly
  what R6-4B concluded from the external literature. Service-load completion is **not a route to
  the ±5% gate**, and the ±5% single-building gate remains the wrong acceptance test for an
  archetype UBEM (R6-4B finding 1).
- **The deliverable's value is the matrix completion, not gate closure.** `r7_service_loads.csv`
  gives every one of the 8 152 buildings a complete nine-end-use breakdown and a
  service-load-inclusive whole-building EUI — a more honest *reported* energy total for downstream
  use (carbon, benchmarking, stock rollups), with the food-service caveat flagged.

## 7. Limitations (documented, not closed)

1. **Refrigeration "case-credit" coupling** — supermarket display cases remove sensible/latent heat
   from the zone; a decoupled additive estimate ignores this feedback (PDF notes >25% thermal-
   balance distortion). Phase-1 reports refrig as an additive vector only; no zone feedback.
2. **Static ΔT / no fan-heat pickup** — the fraction-split inherits CBECS-2018 average operating
   conditions; it does not model dynamic SAT/CHW resets or fan-heat gain.
3. **CBECS-2018 vintage** — pre-hybrid-work end-use splits; offices may over-weight occupant-driven
   auxiliary loads for current operation.
4. **2× round-trip baseline** (above) — round-trip numbers are directional only.
5. **Physics-based Tables 1–3 (SFP/SPP, SWH coefficients, refrig EUI) not transcribed** — their
   numeric cells are image-clipped in the source PDF. A future Method-B refinement would need them
   recovered and validated; out of Phase-1 scope.

## 8. Status

Service-loads reconstruction (ToDo item #1) is **COMPLETE** as a reporting-layer deliverable.
Matrix completion shipped (`r7_service_loads.csv`); round-trip re-evaluation shipped and
interpreted (`r7_roundtrip_recon.csv`). No DESIGN deviation, no resimulation. The R6-4B STOP
ruling stands, now additionally corroborated by direct experiment on the OpenUBEM matrix.
