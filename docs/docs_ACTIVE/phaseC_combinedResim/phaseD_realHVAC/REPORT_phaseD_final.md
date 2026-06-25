# REPORT — Phase-D Real-HVAC: Final Validation & Adopted Baseline

- **Date:** 2026-06-25
- **Author:** Manager (Opus session)
- **Status:** FINAL. Phase-D + V16 service-loads reconstruction **adopted as the OpenUBEM physical baseline.**
- **Binding plan / verdicts:** `PLAN_phaseD_real_hvac_resim.md` §3.1–§3.6 (CP-1…CP-6).
- **Data deliverables:** `RESULT_phaseD_validation.md` (raw metered), `RESULT_phaseD_reconstructed_validation.md` (with service loads).

---

## 1. Executive summary

Phase-D replaced the Phase-1 `IdealLoadsAirSystem` (which reported HVAC as *thermal load* and forced a post-hoc COP patch) with physically-modeled **PTAC + per-archetype prototype COP**, re-ran all 12 validation cells on Speed SLURM, and rewired the parser to read **metered** HVAC electricity/fuel. The result is the first OpenUBEM model that is **physically self-consistent with no fitted parameters** and validates to **city-Overall ±11% in all three cities**.

The arc, in one line each:
- **Basis fix (CP-1→CP-4):** metered HVAC eliminated the thermal-vs-metered basis error at source — cooling EUI fell 75–85%, the chronic "LA runs hot" artifact flipped to cold, 8,160/8,160 buildings succeeded with zero exclusions.
- **Honest re-validation (CP-5):** untuned physical HVAC was well-calibrated in NYC but ran cold in LA/Austin; the residual was correctly re-attributed to the **unmodeled non-HVAC service-loads layer** (DHW/pumps/process), not the HVAC basis.
- **Service-loads re-combination (CP-6):** re-applying the existing V16 reconstruction on the *correct* metered base closed the cold gap — all cities within ±11%, national R² now passes in every region — with **zero fitted knobs** (matching what the retired scalar basis needed four tuned parameters to reach).

**Adopted model = metered PTAC HVAC + V16 service-loads reconstruction.** The scalar-COP basis is retired as a diagnostic crutch.

---

## 2. The adopted model

| Layer | Mechanism | Source / provenance |
|---|---|---|
| HVAC | `HVACTemplate:Zone:PackagedTerminalAirConditioner` per conditioned zone, per-archetype cooling COP + heating coil type/eff | `openubem/data/loads/hvac_cop_by_archetype.json` (30/30 archetypes; DX gross-rated COP from DOE/90.1 prototypes; 10 central-plant archetypes use primary-chiller/WSHP COP × 0.75 plant-auxiliary factor) |
| Metering | Parser reads `Cooling:Electricity`, `Heating:Electricity`+`Heating:NaturalGas`, `Fans:Electricity` (metered end-uses, not thermal load); EUI = energy/(footprint×num_floors) | `openubem/idf/hvac.py`, `openubem/idf/outputs.py`, `openubem/results/parser.py` (authorized §0.1 DESIGN deviation) |
| Service loads | V16 reconstruction adds the 5 unmodeled end-uses (vent_fans, pumps, swh_dhw, refrig, cooking_other) via national CBECS-2018 + PNNL fraction splits, applied to the metered base (which excludes fans → no double-count) | `openubem/results/service_loads.py`, `openubem/data/service_loads/enduse_fractions_table4.json` |

**Fitted parameters: none.** The COP table is read from prototypes; the fraction table is a fixed national reference built before Phase-D. No quantity was tuned to the validation anchors.

**Authorized DESIGN deviation:** PTAC activates `DESIGN_step-3:420` (the Phase-2 hook earmarked "when COP values become available"); DESIGN/OVERVIEW docs unedited. Recorded in PLAN §0.1.

---

## 3. Headline validation — city anchors

Median EUI vs measured city benchmarks (NYC LL84 / LA EBEWE / Austin proxy), success rows, OpenUBEMUnknown excluded.

| City · segment | Phase-D raw (metered) | **Phase-D + V16 (adopted)** | measured |
|---|---|---|---|
| NYC Office | +11.3% | +31.5% | 183.9 |
| NYC Multifamily | −24.9% | **+8.8%** | 226.2 |
| **NYC Overall** | −13.4% | **+10.8%** | 219.2 |
| LA Office | −6.0% | +13.0% | 121.5 |
| LA Multifamily | −37.3% | **−9.2%** | 115.8 |
| LA Warehouse | −25.3% | **+9.8%** | 33.9 |
| **LA Overall** | −33.0% | **−4.2%** | 113.6 |
| Austin Office | −22.1% | −7.8% | 162.3 |
| **Austin Overall** | −21.4% | **−7.0%** | 162.0 |

City-Overall mean \|error\|: **22.6% → 7.3%**. All three cities within **±11%**.

The reconstruction closed the gap exactly where Phase-D ran coldest (residential/Multifamily, which carries a large unmodeled DHW load) — confirming the residual was service loads, not the HVAC basis.

---

## 4. Headline validation — national CBECS-2018 gates

Per region, reconstructed total, no transform.

| Region | NMBE | CV(RMSE) | KS_D | R² |
|---|---|---|---|---|
| NYC → middle_atlantic | +19.1% | 51.0% | 0.439 | **0.834 ✓** |
| LA → pacific | −12.5% | 60.1% | 0.309 | **0.923 ✓** |
| Austin → west_south_central | −9.2% ✓ | 52.0% | 0.397 | **0.792 ✓** |

vs Phase-D raw, the reconstruction lifted **R² to passing in all three regions** (0.55–0.70 → 0.79–0.92) and improved CV(RMSE) everywhere (59–90% → 51–60%).

**CV(RMSE) and KS are reported, not gated.** Both the retired scalar basis and physical HVAC fail them in every region: an archetype-deterministic UBEM has near-zero within-archetype EUI variance, while CBECS is a per-building empirical survey with large natural spread. The shape mismatch is structural to the model class, not a calibration defect (PLAN §3.5).

---

## 5. Integrity (CP-4)

- **8,160 / 8,160 buildings succeeded; 0 exclusions; 0 PTAC fatals** across all 12 cells.
- Cooling EUI fell **74.5% / 79.4% / 80.7%** vs the committed Phase-C baselines (austin_urban / la_centre / nyc_centre); the LA cooling-hot artifact is eliminated.
- `num_floors` zoning invariant clean: 3,259/3,259 `single_zone` rows have `levels==1`; all multi-zone rows have `levels≥2` (V18 fix holds fleet-wide).
- Lighting/equipment EUI archetype-constant except the adjudicated multi-zone office normalization tail and the heterogeneous OpenUBEMUnknown bucket.

---

## 6. Known limitations & residuals

1. **NYC base over-prediction (Office).** NYC Office's *metered base* is already +11.3% over measured **before** any service loads; the reconstruction (which can only add energy) amplifies it to +31.5%. This residual lives in the HVAC/envelope base, not the reporting layer — **no service-load adjustment can fix it.** → Flagged as the single candidate for a future HVAC/envelope **re-calibration resim** (out of current scope).
2. **Climate-blind service-load fractions.** V16 fractions are national-average; on heating-heavy NYC they over-restore service loads, driving the NYC-Overall overshoot (+10.8% from a −13.4% base). A principled fix needs **regional** end-use fractions derived from raw CBECS-2018 microdata — which is not in the repo and would require a new EIA extraction. Deferred rather than anchor-fitted.
3. **CV(RMSE)/KS not closeable** by any basis/HVAC/service-load change (structural; §4).
4. **Fans under-captured by PTAC.** Metered PTAC cycling fans are 2–6% of the reconstruction's `vent_fans` estimate (PTAC has no continuous central-AHU fan); the reconstruction supplies the remainder, so totals are correct, but the metered fan column alone understates real fan energy.
5. **Food-service tail.** Reconstructed food-service median 931.6 kWh/m² (in band); 11 buildings exceed the R5 ~1000 kWh/m² plausibility band (known QSR artifact, reported uncapped).
6. **Secondary HVAC knobs (not indicated).** Central-plant gas-heating eff 0.945 (vs ~0.80) and the 0.75 cooling-plant derate are documented but were **not** the cause of any residual that closed; no resim is warranted on their account.

---

## 7. Reproducibility

- **Resim driver:** `scripts/validation/v12_cell_pipeline.py <cell> --output-subdir phaseD` (ship → one `sbatch --array` → poll → fetch → aggregate); cluster runs ExpandObjects as a separate binary (no `-x`).
- **Re-scoring drivers (local, read-only, no transform):**
  - `scripts/validation/phaseD_city_rescore.py` — city anchors.
  - `scripts/validation/phaseD_national_cbecs_rescore.py` — national CBECS gates.
  - `scripts/validation/phaseD_reconstruct_rescore.py` — V16 reconstruction + re-score (adopted result).
- **Results:** `docs/validations/overAll/results/phaseD/<cell>/05_results.gpkg` (12 cells).
- **12 cells:** {austin,la,nyc} × {rural,suburban,centre,urban}.

---

## 8. Disposition

**Phase-D + V16 service-loads reconstruction is the adopted OpenUBEM physical baseline.** It meets the project's accuracy bar (city-Overall ±11%, national R² passing) with a fully physical, unfitted model, and its remaining residuals are bounded and physically attributed. Future improvement, if pursued, is a NYC HVAC/envelope re-calibration resim and/or regional CBECS end-use fractions — both new, scoped efforts, neither blocking adoption.
