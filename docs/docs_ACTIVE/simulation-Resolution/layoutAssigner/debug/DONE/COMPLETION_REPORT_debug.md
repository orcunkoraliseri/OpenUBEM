# LayoutAssigner Debug-Fixes Plan — Completion Report

**Plan:** `PLAN_debug_implementation.md` · **Closed:** 2026-07-23 · **Director:** autonomous run per `prompt/DIRECTOR_PROMPT_debug.md`

## 1. Outcome in one line

Two of the four residual defects handed off by the closed LayoutAssigner arc are now **fixed and confirmed at full fleet scale** (E-LA-10, E-LA-07-class-1). Fleet-wide success rose from **96.65% (T17) to 98.81% (T18)**, with **zero new failures anywhere in the fleet**. Three defects (two newly surfaced during this plan) are **fully root-caused but remain OPEN-BLOCKED**, each requiring structural engineering work outside this plan's pre-authorized "additive scaling-field tuple" scope. `layout_assign` is recommended for **partial** production use — see §6.

## 2. Per-task outcome table

| Task | What | Outcome |
|---|---|---|
| T01 | Add `WaterHeater:Mixed.Peak_Use_Flow_Rate` to the scaling engine | **Fixed.** Additive tuple, 81 passed (was 79) |
| T02 | Audit all mapped baselines for other unscaled absolute DHW fields | **Fixed.** 4 more literal fields added (`WaterHeater:Mixed` parasitic/loss-coefficient x4); `WaterUse:Equipment`/`WaterUse:Connections` confirmed already-covered/non-applicable. 83 passed |
| T03 | Local retest: E-LA-10 fix validation | **Confirmed.** 5 real buildings, `dhw_eui` distortion (up to 1643 kWh/m²) collapses to the scale-invariant ≈39.4 (MidriseApartment) / 13.6 (SmallOffice) value the undistorted S≈1 fleet population already showed independently |
| T04 | Add `FluidCooler:TwoSpeed` capacity fields to the scaling engine | **Fixed** (its own targeted mechanism). Additive tuple, 85 passed |
| T05 | Local retest: `LargeOffice` Fatal fix validation | **Partial.** Original `SizeFluidCooler` Fatal confirmed gone in all 3 retested buildings; 2/3 still fail on a *new* Fatal (`CheckForRunawayPlantTemps`) → logged as **E-LA-11** |
| T06 | Isolate E-LA-07 class 2/E-LA-08 and E-LA-11 root cause | **Root-caused, both threads.** Class 2/E-LA-08 → `envelope_patcher`'s `MATERIAL:NOMASS` (zero thermal mass) construction swap. E-LA-11 → WSHP coil autosize producing `INF`/`NaN` on shrunk DataCenter zones. New defect **E-LA-12** surfaced (unscaled `Daylighting:ReferencePoint`, latent/masked) |
| T07 | Fix decision for T06's findings | **STOP-AND-REPORT, no code changed** — both roots are structural/pipeline-level, outside this plan's additive-tuple scope. Fix shapes proposed for a future arc |
| T08 | Diff `Outpatient`'s Controller List objects | **Root-caused.** Baseline and `purge_baseline_outputs()` both exonerated; Fatal is a third-party eppy `IDF.save()` serialization bug (`EpBunch.__repr__` zip-truncation on oversized `Controller:MechanicalVentilation` objects) → logged as **E-LA-13**, the true root of the closed arc's E-LA-09 |
| T09 | Fix (or document blocked) `Outpatient`'s Fatal | **STOP-AND-REPORT, no code changed** — 3 candidate fixes evaluated and rejected (eppy-native extension throws `ValueError` on a geomeppy key-casing bug; post-save text patch would silently drop zone-groups; shared-path risk requires regression across all 25 baselines) |
| T10 | Full local regression (all touched archetypes + original 6) | **1 genuine new regression found:** E-LA-14, `SecondarySchool`-family `CheckWarmupConvergence` Severes, isolated via real A/B EnergyPlus reruns to T01/T02's `WaterHeater:Mixed` field additions. Non-Fatal, `status` stays `success`. 211 passed, 3 warnings |
| T11 | Full 12-cell/8,160-building cluster re-sweep + harvest | **Complete.** 8,063/8,160 (98.81%) success. See §5 for the full before/after |

## 3. Checkpoint verdicts

| Checkpoint | Scope | Verdict |
|---|---|---|
| CP-A | T01–T03 | **PASS** — 83 passed local, 209 passed full regression gate; one raw-`eplusout.sql` EUI figure independently re-derived (39.4088 vs. reported 39.41) |
| CP-B | T04–T07 | **PASS**, one evidentiary caveat recorded (a non-decisive confirmatory TallBuilding run was inconclusive, not decisive — did not change the root-cause conclusion, which rests on the scaled-only-vs-full-pipeline comparison) |
| CP-C | T08–T09 | **PASS** — 211 passed; blast-radius claim (exactly 1/25 baselines corrupts) and the byte-level run-on mechanism both independently reproduced from raw files, not the employee's scripts |
| CP-D | T10 | **PASS** — E-LA-14 accepted as a known, non-blocking cost (Severe-count regression, not failure-rate); decisive A/B isolation (6 vs. 0 `CheckWarmupConvergence` hits) independently reproduced from raw `.err` files |
| CP-E | T11 + final reassessment | **PASS (audit) / PARTIAL (production-readiness)** — see §6 |

Full pytest regression gate held at **211 passed, 3 warnings** from CP-C onward, reproduced independently by the director at every checkpoint.

## 4. Real-EnergyPlus before/after tables (local retests)

**T03 — E-LA-10 (DHW), 5 buildings:**

| osm_id | archetype | S | dhw_eui before | dhw_eui after |
|---|---|---|---|---|
| way/1014146287 | MidriseApartment | 0.00733 | 1643.49 | 39.41 |
| way/429322045 | MidriseApartment | 0.00762 | 1611.35 | 39.35 |
| way/1014146136 | MidriseApartment | 0.00929 | 1465.77 | 39.40 |
| way/382991532 | SmallOffice | 0.03951 | 328.84 | 13.62 |
| way/382991504 | SmallOffice | 0.04007 | 324.87 | 13.62 |

**T05 — E-LA-07 class 1 (`LargeOffice`), 3 buildings:**

| osm_id | S | status before (T17) | status after (T05) |
|---|---|---|---|
| way/42496352 | 0.0608 | failed | failed_fatal (new mechanism, E-LA-11 — original signature confirmed gone) |
| way/42500728 | 0.0353 | failed | failed_fatal (new mechanism, E-LA-11 — original signature confirmed gone) |
| way/86121620 | 0.0999 | failed | **success** |

**T07 — reproduction/isolation of class 2/E-LA-08 and E-LA-11, 9 buildings:** all 9 reproduce their known Fatal at full pipeline; scaled-only (no envelope patch) reruns isolate class 2/E-LA-08 to the envelope patcher (clean at S=0.0085 without it) and confirm E-LA-11 is envelope-patch-independent (still runs away without it) — see §7 T06/T07 entries in the plan doc for the full 9-row table and signatures.

**T09 — `Outpatient`, 6 buildings:** raw baseline `Completed Successfully, 0 Severe`; bare eppy `save()` alone reproduces the Fatal; full pipeline retest of all 6 real T17 `Outpatient` buildings → 6/6 `failed_fatal`, identical signature, scale-independent (S≈0.078–13.70).

## 5. T11 — full-cluster before (T17) vs. after (T18) comparison

Independently re-derived by the director from the raw harvest CSVs, not taken from any employee's report.

| Metric | T17 (before) | T18 (after) |
|---|---|---|
| Fleet success | 7,887/8,160 (96.65%) | **8,063/8,160 (98.81%)** |
| Fleet failures | 273 | **97** |
| New failures (T18 not in T17) | — | **0** |
| Recovered (T17-failed, T18-success) | — | **176** (all `LargeOffice`) |
| `LargeOffice` success rate | 18.15% (49/270) | **83.33% (225/270)** |
| `Outpatient` success rate | 0/6 | 0/6 (unchanged) |
| `MidriseApartment` median `dhw_eui` (n=2,818) | 663.0 | **39.35** |
| `SmallOffice` median `dhw_eui` (n=3,497) | 23.79 | **13.64** |
| `n_warmup_convergence` > 0 (fleet-wide, new metric) | not measured (T17 predates this counter) | **105/8,160 (1.29%)**, all still `status==success` |

**97 T18 failures, by archetype:** `LargeOffice` 45 (E-LA-11), `TallBuilding` 25 + `SuperTallBuilding` 12 + `SmallOffice` 7 + `MediumOffice` 1 + `Hospital` 1 = 46 (E-LA-07 class 2/E-LA-08, unchanged from T17), `Outpatient` 6 (E-LA-09/E-LA-13). Sums exactly to 97 — every failure is accounted for by a known, already-characterized defect; no unexplained residual.

Full harvest CSVs: `openubem/outputs/comparisons/t18_layout_assign_eui.csv` / `t18_layout_assign_cell_summary.csv` (also copied to `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/results/`). Comparison plots: `openubem/outputs/comparisons/t18_vs_t17_*.png` (also in `docs_ACTIVE/.../debug/figures/`). Full write-up: results doc `## 5. Post-debug-fix full-cluster result`.

## 6. §8 Error Log summary — final disposition

| ID | Title | Disposition |
|---|---|---|
| E-LA-10 | DHW fixed-capacity fields never scaled | **FIXED**, confirmed at fleet scale (T01–T03, T11) |
| E-LA-07 class 1 / E-LA-08 (`LargeOffice` share) | `FluidCooler:TwoSpeed` capacity fields never scaled | **FIXED**, confirmed at fleet scale (T04–T05, T11) |
| E-LA-11 | `LargeOffice` WSHP coil autosize → `INF`/`NaN` → plant-loop runaway, exposed once E-LA-07-class-1 was fixed | **OPEN-BLOCKED** — root-caused (T06), fix is structural (small-zone/HVAC-autosize handling), not implemented |
| E-LA-07 class 2 / E-LA-08 | `envelope_patcher`'s `MATERIAL:NOMASS` construction swap → `CalcHeatBalanceInsideSurf` divergence in small/marginal zones | **OPEN-BLOCKED**, unchanged — root-caused (T06), fix touches shared `envelope_patcher` infrastructure, not implemented |
| E-LA-09 / E-LA-13 | `Outpatient` 100% Fatal, root cause is a third-party eppy `IDF.save()` serialization bug on oversized `Controller:MechanicalVentilation` objects | **OPEN-BLOCKED**, fully root-caused (T08), fix touches the shared `idf.save()` path, needs regression across all 25 baselines, not implemented |
| E-LA-12 | `Daylighting:ReferencePoint` coordinates not scaled by `scale_baseline_idf` | **OPEN, latent/masked** — currently has zero production impact (masked by E-LA-07 class 2 firing first in the same archetypes); would need attention if class 2 is ever fixed |
| E-LA-14 | `SecondarySchool`-family `CheckWarmupConvergence` Severes, side effect of T01/T02's DHW fix | **OPEN, accepted as non-blocking** — Severe-count only, `status` stays `success`, confirmed 1.29% fleet-wide prevalence at cluster scale (T11) |
| E-LA-06 | Pre-existing Severe-count cosmetic issue (2 archetypes) | **Out of this plan's scope from the start** (Executive Summary), unchanged |

Final pytest state: **211 passed, 3 warnings** — no code changes since CP-C, no regressions introduced by this plan's actual fixes (T01/T02/T04).

## 7. Production-readiness recommendation

**PARTIAL.** `layout_assign` is materially improved (96.65% → 98.81% fleet success, zero new failures, one major EUI-distortion defect genuinely closed) and is recommended for production fleet-EUI aggregation **with two explicit caveats**:

1. **`Outpatient` is 100% non-functional** — any fleet total including this archetype silently omits it entirely (data absence, not a small error).
2. **`LargeOffice` is at 83% success**, not 100% — 45/270 (16.7%) of this archetype is unrepresented, concentrated at small building-to-baseline scale ratios. `TallBuilding`/`SuperTallBuilding`/`SmallOffice`/`MediumOffice`/`Hospital` retain their pre-existing, unimproved failure rates from E-LA-07 class 2/E-LA-08.

All three remaining OPEN-BLOCKED defects (E-LA-11, E-LA-07-class-2/E-LA-08, E-LA-09/E-LA-13) are now fully root-caused with documented candidate fix shapes — a future arc could reasonably scope "implement the three blocked structural fixes" as a single well-defined unit of work.

## 8. This plan's own process note

T11's cluster-completion wait surfaced a recurring failure mode (documented in the plan doc's §7 T11 entries): a subagent ending its turn while believing a background/cluster process it started would "wake it up" later gets marked complete by the harness regardless, even mid-work. This happened twice with the sweep-submission employee. The director's own first attempt at a top-level background wait had a second, distinct bug (a `grep -c` exit-code/`||`-fallback interaction that corrupted the loop's exit condition, causing it to poll forever without ever detecting the cluster had finished) — caught only because the user asked for a live status check, not by the watcher itself. Both are noted here for awareness in any future arc that needs to wait on `sacct`/`squeue` state.
