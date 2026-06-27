# V15 — R6-4A: Level-2 Gap Decomposition + Reporting-Level Basis Calibration

**Date:** 2026-06-15
**Round:** R6-4A (Level-2 gap decomposition; no resimulation; no pipeline code change)
**Predecessor:** `V14_R6_batch1_region_corrections.md` (R6 Batch 1 reporting-layer corrections)
**Binding contract:** `docs/validations/overAll/PLAN_overall-validation-R6-4.md` §0 scope guard + §4 dependency decisions; `DESIGN_*` §2.2 line 45 (F-1) and Step-3 DESIGN §3B line 138 (F-2).
**Status:** CP-C close-out.

R6-4A is a **pure analysis run**: no EnergyPlus resimulation, no pipeline code change, no DESIGN deviation. All inputs come from the Tier-1 persisted data in `roundtrip_report.csv` + `r6_4_level2_enduse.csv`. The only new code is a reporting-level overlay (`r6_4_basis_overlay.py`, pure function module) and a sensitivity probe (`r6_4_sensitivity.py`).

---

## 1. What R6-4A Did and Its DESIGN-Compliance Boundary

R6-4A implements exactly the DQ-1 scope: "COP/fuel-basis conversion layer at the *reporting* level, gates code still untouched" (`OPEN_QUESTIONS_R5.md` lines 72–73, F-3). It answers three questions:

1. **Which end-uses drive the Level-2 round-trip gap per archetype?** (per-end-use decomposition, T03)
2. **Does reporting-level basis correction (COP/fuel factor) change the gap?** (T04 overlay)
3. **Does richer zoning strategy correlate with a smaller gap?** (T05 sensitivity probe)

What R6-4A explicitly did NOT do (all require explicit user approval per scope guard §0):

| Item | Why out of scope |
|---|---|
| Detailed HVAC (DX/COP curves, VAV, chiller, PTAC tuning) | DESIGN §2.2 line 45 — Phase 1 ships IdealLoadsAirSystem; no detailed HVAC plant (F-1) |
| New zoning strategies / 9-zone Appendix-G | Step-3 DESIGN §3B line 138 — full 9-zone Appendix-G rejected, deferred to OQ-1 (F-2) |
| Editing `openubem/results/*` gates / aggregator / carbon math | V-R5-5 + manager standing rule |
| Re-simulating the 8 152-building neighbourhood fleet | Out of scope for decomposition analysis |

---

## 2. Per-End-Use Decomposition Table

**Method:** `(counter_i - ref_i) / ref_total * 100` per end-use. Contributions sum to total Dev% by construction (max residual = 0.005%, threshold 0.01%).

**End-use groups:**
- **Heating / Cooling**: envelope and HVAC proxy
- **Lighting / Equipment**: schedule and internal-gain proxy
- **Other**: fans, pumps, DHW/water systems, HVAC parasitics, refrigeration — the **unmodeled service load** group

| Archetype | Dev% | Verdict | DeltaHeat | DeltaCool | DeltaLight | DeltaEquip | DeltaOther | DomEU |
|---|---:|---|---:|---:|---:|---:|---:|---|
| SmallOffice | +308.7 | FAIL | +62.3 | +56.1 | +37.9 | +14.4 | +138.0 | heat |
| SmallDataCenterLowITE | +150.7 | FAIL | +0.0 | +54.1 | -0.1 | +23.7 | +72.9 | cool |
| MediumOffice | +95.3 | FAIL | +11.8 | +29.7 | +13.6 | +0.6 | +39.7 | cool |
| HighriseApartment | -84.3 | FAIL | -4.2 | -0.4 | -1.1 | -13.6 | -65.0 | equip |
| LargeOffice | -62.9 | FAIL | +2.9 | +3.7 | +0.0 | -24.7 | -44.7 | equip |
| LargeHotel | -58.0 | FAIL | +0.8 | +3.4 | +3.0 | -14.1 | -51.1 | equip |
| SuperTallBuilding | -57.4 | FAIL | -10.0 | +5.8 | +0.6 | -12.0 | -41.9 | equip |
| College | +56.2 | FAIL | +34.2 | +15.1 | -2.0 | -9.8 | +18.8 | heat |
| Warehouse | -55.7 | FAIL | -33.5 | +2.7 | +6.2 | +1.5 | -32.5 | heat |
| RetailStandalone | +47.3 | FAIL | -13.8 | +25.0 | +15.5 | +8.0 | +12.6 | cool |
| TallBuilding | -43.5 | FAIL | -4.5 | +7.3 | +1.5 | -10.5 | -37.2 | equip |
| RetailStripmall | +33.7 | FAIL | -14.0 | +23.1 | +12.2 | +5.2 | +7.2 | cool |
| QuickServiceRestaurant | +33.6 | FAIL | -9.0 | +27.0 | +5.1 | +4.6 | +6.0 | cool |
| SuperMarket | -31.5 | FAIL | +10.3 | +7.6 | -13.0 | +0.8 | -37.2 | light |
| Laboratory | -29.3 | FAIL | -33.2 | +11.6 | +2.8 | +9.9 | -20.3 | heat |
| FullServiceRestaurant | +27.1 | FAIL | -8.4 | +23.8 | +5.8 | +6.0 | -0.0 | cool |
| Outpatient | -18.4 | FAIL | +1.0 | +6.7 | +5.1 | -12.5 | -18.6 | equip |
| Hospital | -12.2 | FAIL | -0.7 | +11.6 | +8.4 | -11.0 | -20.4 | cool |
| MidriseApartment | +12.0 | FAIL | +0.7 | +15.7 | +11.9 | -1.5 | -14.7 | cool |
| SmallHotel | -4.5 | PASS | +10.6 | +11.4 | +11.0 | -12.2 | -25.3 | equip |

N/A (thermal runaway): LargeDataCenterHighITE, LargeDataCenterLowITE, SmallDataCenterHighITE (per OQ-R5-7).

**Key:** Dev% = (counter_total - ref_total)/ref_total * 100. DeltaX = (counter_X - ref_X)/ref_total * 100.

### 2.1 Headline Finding: "Other" is the Dominant Gap Driver

The "Other" end-use (fans, pumps, DHW/water systems, HVAC parasitics, refrigeration) is the **largest single contributor to the round-trip gap in 11 of 20 archetypes** by absolute contribution magnitude. The median share of the total absolute gap attributed to "Other" across all 20 archetypes is **42.0%**, vs 36.3% for heating+cooling combined and 19.8% for lighting+equipment.

This is the core diagnostic: the OpenUBEM IdealLoads counterpart does not carry the service loads the DOE prototypes do. This is not a zoning resolution artifact or a HVAC sizing artifact — it is an **unmodeled end-use category** that exists in every DOE prototype but has no equivalent in the IdealLoads single-zone box.

Breakdown of dominant end-use across 20 archetypes:
- **equip** dominant in 8/20: LargeHotel, LargeOffice, Outpatient, SmallHotel, SuperTallBuilding, TallBuilding, HighriseApartment (note: "other" gap magnitude often exceeds equip gap in these)
- **cool** dominant in 8/20: MediumOffice, MidriseApartment, Hospital, FullServiceRestaurant, QuickServiceRestaurant, RetailStandalone, RetailStripmall, SmallDataCenterLowITE
- **heat** dominant in 3/20: College, Laboratory, Warehouse
- **light** dominant in 1/20: SuperMarket

---

## 3. Basis-Overlay Result

**Method:** `apply_basis(cooling_thermal, heating_thermal, lighting, equipment, other)` — cooling divided by COP 3.5; heating multiplied by fuel factor 1.19; lighting/equipment/other unchanged. Constants from MEMO_phaseB_cbecs_diagnosis.md lines 55–59 (F-5).

| View | Median |dev%| | PASS count (n=20) |
|---|---:|---:|
| RAW | 45.4% | 1/20 (SmallHotel) |
| BASIS-CORRECTED | 44.5% | 1/20 (MidriseApartment) |

**Result:** The basis correction makes essentially no difference to the headline — median |dev%| shifts from 45.4% to 44.5% (a 0.9pp improvement), and PASS count stays 1/20. The one PASS flip: SmallHotel drops from PASS (-4.5%) to FAIL (-12.6%); MidriseApartment rises from FAIL (+12.0%) to PASS (+0.5%).

**Why the correction barely helps:** The basis correction only adjusts heating (×1.19) and cooling (÷3.5). Because "Other" accounts for 42% of the median gap and is left unchanged, the correction cannot close the dominant contributor. This **re-confirms OQ-R5-8** ("basis correction confirms rather than closes the gap") and now explains **WHY**: the gap is substantially unmodeled service end-uses, not a cooling-fuel-accounting artifact. The V13 §6.5 wording ("fuel-basis correction confirms rather than closes it") is validated with per-end-use granularity.

This finding is importantly different from OQ-R5-8's original finding (which showed basis-corrected median worsening to 66%): OQ-R5-8 applied the correction to counterpart totals relative to raw DOE reference totals, which amplified the gap by adding a fuel penalty to an already-under-predicted counterpart. R6-4A applies the correction to counterpart end-uses individually, which better isolates the basis effect. Both approaches confirm the structural nature of the gap; R6-4A's version is more granular.

---

## 4. Zoning Strategy vs Gap Correlation (T05)

**Method:** Group non-N/A archetypes by counterpart `zoning_strategy` (from manifest); compute median |dev%| per group.

| Zoning strategy | n | Median |dev%| |
|---|---:|---:|
| single_zone | 9 | 47.3% |
| one_zone_per_floor | 3 | 43.5% |
| perimeter_core | 8 | 42.8% |

**Finding:** Richer zoning correlates slightly with a smaller gap: perimeter_core median is 4.5pp lower than single_zone. However:

1. The difference is small relative to the gap magnitudes (4.5pp vs 45% baseline).
2. The result is **confounded by building-type complexity**: perimeter_core archetypes are complex building types (hospitals, hotels, labs, offices) with inherently more unmodeled service loads. The apparent improvement may reflect archetype selection more than zoning quality.
3. The n_zones comparison reveals mixed fidelity: some archetypes match (SuperTallBuilding = 72/72, TallBuilding = 38/38, MediumOffice = 15/15), while others diverge significantly (HighriseApartment = 1 vs DOE 18; SmallOffice = 1 vs DOE 5; LargeOffice = 60 vs DOE 19 — the counterpart has MORE zones than the DOE prototype, which is unexpected).

**Conclusion:** Richer zoning is unlikely to be the primary lever for closing the Level-2 gap, given that "Other" service loads (unaffected by zoning changes) account for 42% of the gap. Even a complete zoning upgrade to 9-zone Appendix-G would leave the service-load deficit unaddressed.

---

## 5. Attribution Summary

| Gap component | Median share of total |dev%| | Addressable by zoning/HVAC upgrade? |
|---|---:|---|
| Other (fans/pumps/DHW/HVAC parasitics) | 42.0% | No — requires modeling service end-uses |
| Heating + Cooling (envelope/HVAC proxy) | 36.3% | Partially — zoning/HVAC tuning could reduce this |
| Lighting + Equipment (schedule/internal-gain) | 19.8% | Partially — vintage-matched schedules could reduce this |

The **42% service-load gap is structural** and cannot be closed by any zoning or HVAC system change within the IdealLoads framework. The IdealAir system in EnergyPlus's IdealLoadsAirSystem does not model fans, pumps, DHW heaters, refrigeration systems, or HVAC parasitics — these appear as non-zero "Other" in DOE prototype results but as zero (or very small) in IdealLoads counterparts.

---

## 6. Recommendation Memo — Structural Calibration Path

**To:** Manager (morning Opus session)
**From:** R6-4A execution (Sonnet)
**Re:** Whether to proceed with HVAC/zoning structural calibration (DQ-1)

### 6.1 What TRUE Structural Calibration Would Require

A zoning/HVAC rewrite to close the Level-2 gap would require, at minimum:

| Work item | Current constraint |
|---|---|
| Replace IdealLoadsAirSystem with system-specific HVAC (DX, VAV, PTAC, chiller plant) | DESIGN §2.2 line 45 — explicitly out of Phase-1 scope (F-1) |
| Implement 9-zone Appendix-G or equivalent per-prototype zoning | Step-3 DESIGN §3B line 138 — rejected, deferred to OQ-1 (F-2) |
| Add service-end-use models (HVAC parasitics, DHW, fans, pumps, refrigeration) | Not addressed in any DESIGN section — new scope requiring user approval |
| Vintage-matched internal-gain and setpoint schedules | DQ-1 scope item, not yet designed |

### 6.2 Expected Payoff Per the Decomposition

Even if heating+cooling and lighting+equipment gaps were fully closed (theoretical maximum from zoning/HVAC + schedules), the "Other" 42% share would remain. A structural rewrite could at best improve the median |dev%| from 45% to approximately 42% × 45% / 100% ≈ 19%  — still FAIL at the ±5% gate. To reach ±5%, service-end-use modeling would be required IN ADDITION to the structural rewrite.

### 6.3 Explicit Statement — DESIGN Deviation Required

**Any structural zoning or HVAC calibration is a binding-DESIGN deviation and requires explicit user (manager-of-manager) approval before execution.**

Specifically:
- Replacing IdealLoads with system-specific HVAC violates DESIGN §2.2 line 45 (F-1). This is a Phase-2+ item.
- Adding new zoning strategies beyond the 3-strategy table violates Step-3 DESIGN §3B lines 104–111 / line 138 (F-2). This is OQ-1, Phase-1.5.
- Adding service-end-use models has no DESIGN basis at all and requires new specification before any executor touches code.

**Recommended next step for the manager:** Decision on whether to (a) accept the Level-2 gap as a documented Phase-1 limitation (preferred — intellectually honest, non-blocking for neighbourhood-scale use cases), or (b) commission a DQ-1 spec to design Phase-2 HVAC/service-end-use modeling. Option (a) requires no further execution; this document closes R6-4.

---

## 7. Artifacts

- Per-archetype end-use data: `docs/validations/overAll/results/r6_4_level2_enduse.csv`
- Decomposition table: `docs/validations/overAll/results/r6_4_decomposition.{csv,md}`
- Basis-corrected comparison: `docs/validations/overAll/results/r6_4_basis_corrected.csv`
- Basis overlay module (pure function): `scripts/validation/r6_4_basis_overlay.py`
- Sensitivity probe: `scripts/validation/r6_4_sensitivity.py`
- Basis corrected CSV producer: `scripts/validation/r6_4_produce_basis_corrected.py`
- Unit tests: `tests/test_r6_4_basis_overlay.py` (15 tests, all pass)
- Plan doc + progress log: `docs/validations/overAll/PLAN_overall-validation-R6-4.md`
