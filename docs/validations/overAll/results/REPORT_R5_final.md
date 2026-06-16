# REPORT_R5_final — OpenUBEM R5 Validation Close-Out (CP-V3)

**Date:** 2026-06-15
**Checkpoint:** CP-V3 (final R5 close-out)
**Author:** Phase-C manager session
**Verdict:** **R5 COMPLETE.** All 12 matrix cells closed at zero-fail / zero-skip; cross-case synthesis (V13) and Level-2 round-trip delivered; all open questions resolved or routed to R6.

Supersedes nothing; consolidates CP-V1 (Level-2 round-trip), CP-V1b (storeys-corrected re-run), Phase-B CBECS diagnosis, and the V11/V12 per-cell closes into one R5 conclusion.

---

## 1. What R5 set out to do

Validate the OpenUBEM 5-stage pipeline at neighbourhood scale across a 12-cell matrix — {city-centre, urban, suburban, rural} × {New York City, Los Angeles, Austin} — to a true *n/n* zero-fail, zero-skip close per cell, plus a single-building Level-2 round-trip against DOE prototypes, with all validation gates **report-only** (V-R5-5: never tune to pass).

## 2. Headline result

| Metric | Result |
|---|---|
| Cells closed | **12 / 12** |
| Buildings simulated | **8 152** |
| EnergyPlus success | **100% (zero-fail, zero-skip)** |
| F12 parse_success | 100.00% in all 12 cells |
| F12 zone_count_integrity | 0 mismatches in all 12 cells |
| F12 EUI plausibility | PASS in 8; FAIL in 4 (all QSR-band artifact, band held) |
| EnergyPlus version | 23.1.0 across all cells |
| Level-2 round-trip | 1/20 PASS raw, 0/20 basis-corrected (structural gap) |

Full per-cell tables: **`../V13_cross_case_synthesis.md`** (EUI L1/L2, GWP, gates, fleet, climate). Per-cell deliverables: `results/cases/<cell>/`.

## 3. Cell-by-cell close status

| City | centre | urban | suburban | rural | Sim host |
|---|---|---|---|---|---|
| New York (4A) | ✅ 738 | ✅ 1779 | ✅ 1589 | ✅ 198 | Speed cluster |
| Los Angeles (3B) | ✅ 226 | ✅ 618 | ✅ 1343 | ✅ 149 | Speed cluster |
| Austin (2A) | ✅ 413 | ✅ 417 | ✅ 437 | ✅ 245 | **LOCAL** (approved V-R5-6 deviation) |

Every ✅ = full pipeline run, 100% EnergyPlus success, F12 evaluated, CBECS report-only computed, 10 deliverables shipped, §8 progress-log entry appended, raw intermediates archived to `runtime/`.

## 4. Climate validation signal

The matrix reproduces the expected physics:
- **Heating EUI:** NYC (4A) 25.6–64.9 ≫ Austin (2A) 8.1–23.9 ≈ LA (3B) 7.4–20.4 kWh/m²/yr.
- **Cooling EUI:** Austin (2A) 93.7–106.1 ≥ LA (3B) 55.2–99.4 ≥ NYC (4A) 55.3–99.1 kWh/m²/yr.
- Fleet morphology follows the centre→rural urban-form gradient in all three cities (office/tall downtown → small-office/midrise outward).

## 5. Open questions — final disposition

| OQ / DQ | Topic | Disposition |
|---|---|---|
| V-R5-5 | Gates report-only | Honoured throughout; no threshold tuned. |
| OQ-R5-6/7 | Storeys fix; data-centre N/A | CP-V1b accepted; 3 ITE counterparts permanently N/A. |
| OQ-R5-8 | Level-2 basis correction | Applied as supplementary column (V13 §2, §6.5); confirms structural gap. |
| OQ-R5-9/10 | V11 deviations; V12 mechanics | Recorded; non-blocking. |
| OQ-R5-11 | QSR plausibility-band FAIL | **Band held** (V-R5-8); 4 cells FAIL honestly; archetype-aware band → R6. |
| V-R5-6 | All E+ on cluster | **Approved deviation** for Austin (local); documented (V13 §6.3). |

## 6. Known gaps carried to R6 (none block R5)

1. **Archetype-aware plausibility band** for food-service types (current generic [25,1000] is correct policy for R5 but flags real QSR EUIs).
2. **Region-correct CBECS references** — LA vs CBECS *West*, Austin vs CBECS *South* (all cells were scored vs *Northeast*); a reporting-layer re-run from shipped `05_results.csv`, no resimulation.
3. **`egrid_subregion` metadata** is empty in all 12 summaries (GWP math is valid; only the provenance label is unpersisted).
4. **Level-2 HVAC/zoning fidelity** — single-zone IdealAir vs multi-floor DOE prototype is the dominant round-trip error; basis correction does not close it (DQ-1 calibration scope).

**R6 Batch 1 update (2026-06-15):** items 1–3 above are closed at the reporting layer; region-correct CBECS gates, archetype-aware plausibility, and eGRID subregion GWP corrections are documented in `docs/validations/overAll/V14_R6_batch1_region_corrections.md`.

## 7. Caveats on the headline

- **Local-vs-cluster (Austin):** identical EnergyPlus 23.1.0 engine; only OS build and scheduler differ; Austin IODs are the tightest in the matrix. Treated as cluster-equivalent.
- **CBECS report-only:** the regional + compositional mismatch (V13 §6.2) means CBECS CV(RMSE)/KS_D FAILs are reference-construction artifacts, not model defects; R² (0.69–0.996) shows OpenUBEM tracks the EUI distribution shape.
- **Level-2 basis column** is a presentational delivered-energy view, not a calibration.

## 8. Artifacts

- Cross-case synthesis: `docs/validations/overAll/V13_cross_case_synthesis.md`
- Per-cell deliverables (×12): `docs/validations/overAll/results/cases/<cell>/`
- Level-2 round-trip: `docs/validations/overAll/results/roundtrip_report.{md,csv}`
- Phase-B CBECS diagnosis: `docs/validations/overAll/results/MEMO_phaseB_cbecs_diagnosis.md`
- Progress log (binding §8): `docs/validations/overAll/PLAN_overall-validation-R5.md`
- Open-question rulings: `docs/validations/overAll/OPEN_QUESTIONS_R5.md`
- Raw simulation intermediates: `runtime/ubem_validation/cases/<cell>/`

---

**CP-V3 ruling:** R5 is complete and closed. The OpenUBEM pipeline is validated as operational across 3 climate zones × 4 urban-form rings at neighbourhood scale (8 152 buildings, 100% EnergyPlus success). Binding F12 gates pass except for the documented QSR plausibility-band artifact. All report-only gate shortfalls are explained and non-blocking. The next body of work is R6 (deep calibration + reporting-layer corrections), scoped in §6.

**R6-4A update (2026-06-15):** §6 item 4 (Level-2 HVAC/zoning fidelity) decomposed per end-use — see `docs/validations/overAll/V15_R6_4_level2_decomposition.md`. "Other" service loads account for 42% of the median gap; basis correction does not close it (1/20 PASS raw and basis-corrected); structural calibration is a DESIGN deviation requiring user approval.
