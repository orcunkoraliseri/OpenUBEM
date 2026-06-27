# PLAN — V19 Energy-Basis Diagnostic Sweep (no resim)

- **Slug:** `v19_basis_diagnostic`
- **Date:** 2026-06-20
- **Author:** Manager (Opus session)
- **Binding contracts (read, do not edit):**
  - DESIGN step-3 §3H (Phase-1 HVAC = `IdealLoadsAirSystem`) — `docs/docs_step3/DESIGN_...generate-one-energyplus-idf....md` line 394.
  - V19 verdict — `docs/docs_VALIDATION/overAll/V19_phaseC_rescore.md`.
  - Deep-research inputs — `./deepResearch/RESULT_1_LA_climate_overprediction.md`, `RESULT_2_office_overprediction.md`, `RESULT_3_benchmarking_normalization.md`.
  - Prior basis falsification — `docs/docs_VALIDATION/overAll/results/MEMO_phaseB_cbecs_diagnosis.md`.

## 0. Purpose (why this phase exists)

V19 left two P1 biases: **office over-predicts +30–50 % in every city**, and **LA over-predicts +38.8 % overall**. Investigation (this session) established the real driver: our IDFs use `IdealLoadsAirSystem`, so the EnergyPlus `Zone Ideal Loads Zone Total Cooling/Heating Energy` outputs are **thermal loads**, and the pipeline compares them to **measured metered EUI with no COP / efficiency conversion** (`openubem/results/parser.py:204`). LA is cooling-dominated (LA office cooling = 90.1 of 174.9 kWh/m², `v18_la_enduse_gap.csv`), so its thermal cooling reads ≈ 3.5× the electricity a real DX system would meter. NYC is heating-dominated and matches measured **only by a coincidental offset** (`MEMO_phaseB...` V07).

Before spending a 12-cell cluster resim, this phase answers — **with zero resim and zero `openubem/` change** — one question:

> **Is there a single coherent energy basis (cooling COP + heating efficiency + measured-stock internal-load scaling) that brings NYC, LA, and Austin all within tolerance at once — or are cooling-dominated and heating-dominated cities irreconcilable under any single basis (which would prove a Phase-2 real-HVAC/COP model is required)?**

The sweep is a **reporting-layer post-process over the existing V19 results**. It re-uses the V19 scoring functions verbatim, so the identity parameter set reproduces the V19 numbers exactly.

---

## 1. Hard rules for the executor

1. **Stay in cwd** `C:\Users\o_iseri\Desktop\OpenUBEM`. Windows + PowerShell; the cluster is irrelevant here (no resim).
2. **No `openubem/` modification.** This is report-only (ruling V-R5-5 / M-R2-4 stands). All new code goes under `scripts/validation/`.
3. **No `.py` under `docs/`.** Markdown results only under `docs/`.
4. **No resim, no IDF generation, no EnergyPlus.** You consume existing `05_results.gpkg` outputs only.
5. **Do not re-transcribe measured anchors.** Import them from `scripts/v19_rescore.py` (single source of truth). If an anchor is missing for a segment, skip it exactly as V19 does — do not invent one.
6. **Default to no comments.** One short line max where the WHY is non-obvious.
7. **You execute; you do not re-plan.** If a DESIGN/spec conflict appears, STOP and quote it.
8. **Write data, not verdicts.** The findings file (T06) contains tables and the coherence metrics only. The interpretation/recommendation is the manager's job — do **not** write "we should…" conclusions.

---

## 2. File layout to create

```
scripts/validation/
└── v19_basis_diagnostic.py          ← NEW: the sweep harness (only new code file)

docs/docs_ACTIVE/phaseC_combinedResim/v19_validation/
├── RESULT_basis_diagnostic.md       ← NEW: data tables + coherence metrics (Sonnet, T06)
└── basis_sweep_combos.csv           ← NEW: ranked grid of all combos (Sonnet, T04/T06)

tests/validation/
└── test_v19_basis_diagnostic.py     ← NEW: identity-reproduces-V19 gate + transform tests
```

(If `tests/validation/` does not exist, create it. If the repo convention is a flat `tests/`, place the test there and note it in the progress log.)

---

## 3. Dependency decisions (pre-decided — do not re-debate)

- **Reuse, don't reimplement.** Import from `scripts/v19_rescore.py`: `load_all_cells`, `build_city_table`, `CITY_ANCHORS`. Import from `openubem/results/service_loads.py`: `load_coefficients`, `reconstruct_frame`. The diagnostic is a thin wrapper that mutates the four modeled columns, re-runs reconstruction, and re-scores.
- **Basis transform is exact for COP/fuel; a lower bound for loads.** Dividing thermal cooling by a COP and multiplying thermal heating by a fuel factor are exact in post-processing. Scaling `lighting_eui`/`equipment_eui` is *only* a direct scaling of those columns — it **cannot** propagate the reduced internal gain into a lower cooling load (that needs a resim). Therefore load-scaling results are a **lower bound** on the true benefit. This caveat must appear verbatim in the T06 findings.
- **The sweep grid (fixed):**
  - `cooling_cop` ∈ `{1.0, 2.5, 3.0, 3.5, 4.0}`  (1.0 = as-is thermal; 3.5 = `r6_4_basis_overlay.COOLING_COP`)
  - `heating_factor` ∈ `{1.0, 1.19}`  (1.0 = as-is thermal; 1.19 = `r6_4_basis_overlay.HEATING_FUEL_FACTOR`, gas/steam fuel basis)
  - `lighting_scale` ∈ `{1.0, 0.8, 0.6, 0.5}`  (RESULT_2: real LED stock ≈ 0.40 vs prototype 0.82 W/ft²)
  - `equipment_scale` ∈ `{1.0, 0.7, 0.5}`  (RESULT_2: real ≈ 0.35 vs prototype 0.63 W/ft²)
  - Full grid = 5 × 2 × 4 × 3 = **120 combos**. The identity combo `(1.0, 1.0, 1.0, 1.0)` must be present.
- **Tolerance bands:** primary **±15 %** (ASHRAE Guideline-14-style acceptance), secondary **±20 %**. Report counts at both.
- **Objective for "best global" combo:** minimize the **maximum absolute delta** across the six load-bearing city anchors — `{nyc,la,austin} × {Office, Overall}` — i.e. minimax. (Minimax, not mean, because the question is whether *all* cities can be closed simultaneously, not on average.) Report the sum-of-squares ranking as a secondary column.
- **No new measured data.** Use only the anchors already in `CITY_ANCHORS`.

---

## 4. Source-of-truth verified facts (manager-grepped — cite these, don't re-derive)

| # | Fact | Evidence |
|---|---|---|
| F1 | Phase-1 HVAC is `IdealLoadsAirSystem`; detailed/packaged HVAC deferred to Phase-2 "when COP values become available". | DESIGN step-3 line 394 & 420; DESIGN main line 45; `openubem/idf/hvac.py:29` (`Economizer=None`, `Heat Recovery=None`). |
| F2 | EUI parser sums thermal ideal-loads cooling/heating with **no COP/efficiency division**. | `openubem/results/parser.py:48–52, 204`. |
| F3 | Reconstruction reads `total_eui_kwh_m2` as `total_sim` and computes `E_total_est = (heat+cool+light+equip)/modeled_frac`; `total_recon = total_sim + Σ recon`. ⇒ **mutate the four columns AND recompute `total_eui_kwh_m2` before calling `reconstruct_frame`.** | `openubem/results/service_loads.py:83–92`. |
| F4 | Comparison metric: `delta_vs_measured_pct = (recon_median − measured)/measured × 100`, computed per city×segment in `build_city_table`. | `scripts/v19_rescore.py:120,133`. |
| F5 | Binding measured anchors (kWh/m²): NYC Office 183.9 / Overall 219.2; LA Office 121.5 / Overall 113.6 / MF 115.8 / Warehouse 33.9; Austin Office 162.3 / Overall 162.0. | `scripts/v19_rescore.py:48–58` (`CITY_ANCHORS`). |
| F6 | Known V19 deltas the identity sweep must reproduce: LA Overall ≈ **+38.8 %**, LA Office hot (~+72 to +78 %), NYC Office near pass, NYC Overall ~+10 %. | `V19_phaseC_rescore.md`; `MEMO_phaseB...`. |
| F7 | LA gap is cooling-dominated: LA office cooling 90.08 vs heating 21.43 kWh/m². | `results/v18_la_enduse_gap.csv`. |
| F8 | A *global* `÷3.5 cool, ×1.19 heat` basis **worsens** the heating-dominated national fit (NMBE −16 %→−29.5 %); the as-is match is a "coincidental offset". This is why a per-climate answer must be examined, not just a single global one. | `MEMO_phaseB...` V07 (lines 17–25). |
| F9 | Office prototype loads (our values): lighting 10.76 W/m² (~1.0 W/ft²), equipment 6.78 W/m² (~0.63 W/ft²). Measured stock: LPD ~0.40, EPD ~0.35 W/ft². | `openubem/data/loads/doe_prototype_loads.json`; `RESULT_2` table. |

---

## 5. Task list

### T01 — Harness scaffold + identity-reproduces-V19 gate
- **What:** Create `scripts/validation/v19_basis_diagnostic.py`. Import `load_all_cells`, `build_city_table`, `CITY_ANCHORS` from `v19_rescore`, and `load_coefficients`, `reconstruct_frame` from `service_loads`. Load the 12 cells once into a base DataFrame; load coefficients once.
- **Why:** Reusing V19's own loader + scorer guarantees the diagnostic is measured on the identical basis as the published V19 numbers (F4, F6).
- **How:** `sys.path` insert the repo root (mirror `v19_rescore.py:14–17`). Keep the base df immutable; every combo works on a `.copy()`.
- **How to test (in `test_v19_basis_diagnostic.py`):** run the identity combo (next task's transform with `cop=1, heat=1, light=1, equip=1`) through `reconstruct_frame` → `build_city_table` and assert: LA Overall delta within **±0.5 pp** of +38.8 %; NYC Office present; row count of success buildings ≈ 8,150 (±50). **If this fails, the harness is wrong — STOP.**

### T02 — Basis transform function
- **What:** `apply_basis_to_frame(df, cooling_cop, heating_factor, lighting_scale, equipment_scale) -> pd.DataFrame` returning a copy with: `cooling_eui_kwh_m2 /= cooling_cop`; `heating_eui_kwh_m2 *= heating_factor`; `lighting_eui_kwh_m2 *= lighting_scale`; `equipment_eui_kwh_m2 *= equipment_scale`; and **`total_eui_kwh_m2` recomputed as the sum of the four mutated columns** (F3).
- **Why:** Reconstruction depends on `total_eui_kwh_m2` and on the four columns (F3); all must be consistent before re-scoring.
- **How:** Pure column arithmetic; do not touch any other column. Reuse the constant names from `scripts/validation/r6_4_basis_overlay.py` where natural.
- **How to test:** identity `(1,1,1,1)` returns a frame whose four columns + `total_eui_kwh_m2` equal the input within 1e-9; a `(3.5,1,1,1)` frame has cooling exactly input/3.5.

### T03 — Single-combo scorer
- **What:** `score_combo(base_df, coeffs, params) -> dict` that: transforms (T02) → `reconstruct_frame` → `build_city_table`, then extracts the six city anchors `{nyc,la,austin}×{Office,Overall}` deltas plus summary metrics: `max_abs_delta`, `sumsq_delta`, `n_within_15`, `n_within_20` (counted over the six). Return a flat dict including the four params and every per-segment delta.
- **Why:** This is the per-point objective of the sweep; minimax over the six (F4, §3).
- **How:** Pull deltas from the `build_city_table` output by `(city, segment)`. "Overall" segment label is prefixed (`"Overall (excl...)"`) — match by `startswith("Overall")` as V19's self-check does (`v19_rescore.py:255`).
- **How to test:** `score_combo` on identity reproduces the V19 city table deltas (same assertion as T01, plus NYC Overall ≈ +10 % ±1 pp).

### T04 — Run the full grid
- **What:** Iterate the 120-combo grid (§3), call `score_combo` for each, assemble a DataFrame, sort by `max_abs_delta` ascending, write `basis_sweep_combos.csv` to the `v19_validation/` folder.
- **Why:** The ranked grid is the raw evidence for the coherence verdict.
- **How:** `itertools.product`. Vectorized column math makes 120×~8k rows trivial; if `reconstruct_frame`'s row-wise `apply` is slow, it is still acceptable for a one-off (note runtime in the log). Assert grid length == 120 and the identity row is present.
- **How to test:** covered by T05/T06 assertions; spot-assert the CSV has 120 rows and columns for all four params + six deltas + summary metrics.

### T05 — Coherence analysis
- **What:** Compute and capture three things:
  1. **Best global combo** = the grid row with the lowest `max_abs_delta`. Capture its params and its full six-segment delta table.
  2. **Climate-aware ceiling** = for each city independently, the best achievable `max_abs_delta` over that city's two anchors (allowing a *different* `cooling_cop` per city). This quantifies how much a per-climate basis (≈ what a real Phase-2 COP model would give) could achieve vs a single global basis.
  3. **Coherence verdict metric** (data only): does *any* single global combo put all six anchors within ±15 %? within ±20 %? Report the best global combo's `n_within_15` / `n_within_20` and the signed deltas, so the manager can see whether NYC and LA end up on **opposite sides** (the irreconcilability signature).
- **Why:** Directly answers the §0 question and feeds the Phase-2 go/no-go (F8).
- **How:** All derivable from the T04 grid DataFrame; no new scoring. For the per-city ceiling, group the grid by city-relevant deltas.
- **How to test:** assert best-global `max_abs_delta` ≤ identity `max_abs_delta`; assert the three per-city ceilings are each ≤ the global `max_abs_delta` (a per-city basis can never be worse than the global one).

### T06 — Findings memo (data only) + self-check
- **What:** Write `RESULT_basis_diagnostic.md` to `v19_validation/` containing, in order: (a) the grid spec; (b) **the verbatim load-scaling caveat from §3** (load scaling is a lower bound; cooling secondary effect needs resim); (c) top-10 combos by `max_abs_delta`; (d) the best-global combo's six-segment signed-delta table; (e) the per-city climate-aware ceiling table; (f) the coherence verdict metrics (n_within_15 / n_within_20, and whether NYC/LA land on opposite signs). Also print a stdout self-check echoing the identity reproduction and the best-global row.
- **Why:** Hands the manager a decision-ready evidence pack with **no interpretation** (rule 8).
- **How:** Reuse `v19_rescore._df_to_md_table`. No "recommendation" / "conclusion" prose.
- **How to test:** file exists, all tables non-empty, identity reproduction line present in stdout.

---

## 6. Stop-and-report points

- **CP-1 — after T03.** This is the critical correctness gate. Report the identity reproduction: LA Overall, LA Office, NYC Office, NYC Overall deltas vs the V19 published numbers, and the success-row count. **If identity does not reproduce V19 within tolerance, STOP and report — do not run the grid.**
- **CP-2 — after T06.** Report the best-global combo, its six-segment deltas, the per-city ceilings, and the coherence verdict metrics. Stop for manager verdict (the manager writes the interpretation + the Phase-2 go/no-go).

### CP-2 manager verdict — written 2026-06-21 (Opus session)

**Question (§0) answer: a single coherent basis CLOSES all three cities at ±15%. The cities are NOT irreconcilable. The going-in irreconcilability hypothesis is falsified for the six load-bearing anchors.**

1. **The conclusion does not depend on the load-scaling caveat.** The combo `cooling_cop=3.5, heating_factor=1.0, lighting=1.0, equipment=1.0` (row 6 of the top-10) lands all six anchors within ±15% (max 14.6%) using **only the exact COP transform** — no lighting/equipment scaling, so the "load-scaling is a lower bound" caveat does not apply to it. This is the robust anchor, and `3.5` is exactly `r6_4_basis_overlay.COOLING_COP`. The grid-minimum combo (`2.5, 1.19, 0.8, 0.7`, max 13.0%) is slightly tighter but leans on load scaling and so carries the lower-bound caveat; the manager weights the caveat-free row as the primary evidence.

2. **Root cause confirmed = unit/basis error, not geometry/zoning/climate.** Dividing IdealLoads thermal cooling by a realistic DX COP collapses LA Office from **+78.4% → within band** and resolves the +30–50% office bias across all cities simultaneously. The V19 P1 biases were predominantly the no-COP comparison of thermal cooling energy to metered electricity (F2), not a physical modeling defect.

3. **NYC and LA land on the SAME (negative) sign** under every passing global combo (NYC Overall −7.7% to −12.1%, LA Overall −5.5% to −13.0%). The opposite-sides irreconcilability signature is **absent**. A per-climate COP (per-city ceilings nyc 8.2% / la 6.0% / austin 1.8%) is marginally better but **not required** to pass.

4. **Phase-2 real-HVAC/COP RESIM is NOT a prerequisite to pass validation. Recommend DEFER (no resim now).** A reporting-layer COP basis in the ~3.0–3.5 band brings the anchors inside ASHRAE G14 ±15% with zero resim. Real-HVAC remains a future *credibility/accuracy* upgrade (part-load COP, climate-dependent SEER, fan/pump energy, internal-gain→cooling feedback) — not a gate. **User decision required** on whether to (a) adopt the reporting COP basis now, or (b) still schedule the 12-cell resim for physical self-consistency.

5. **Open caution — do not over-claim globally.** This sweep scored only the six city anchors. F8 established that a global `÷3.5 ×1.19` basis *worsens* the national heating-dominated CBECS NMBE. "COP basis fixes the city anchors" ≠ "COP basis is correct for every national CBECS segment"; the heating/fuel-factor side is where national-scale divergence could still appear. A national re-score under the chosen COP basis is the natural next diagnostic before treating the basis as universal.

**Deviation accepted (T05):** per-city ceiling computed over all 4 free params rather than cooling_cop-only; yields a stricter (lower) ceiling, conservative w.r.t. the verdict, no DESIGN contradiction.

---

## 7. Progress log

_(Sonnet appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` with Artifacts / Deviations / Test status / Notes.)_

#### T01 — Harness scaffold + identity-reproduces-V19 gate — completed 2026-06-21
- Artifacts: `scripts/validation/v19_basis_diagnostic.py` (scaffold with `_load_base`, `__main__` identity check); `tests/test_v19_basis_diagnostic.py` (class `TestIdentityReproducesV19`)
- Deviations: Plan specified `tests/validation/` subdirectory; repo convention is flat `tests/` (all prior tests live there, no `tests/validation/` existed). Test placed at `tests/test_v19_basis_diagnostic.py` per repo convention.
- Test status: 4/4 identity-gate tests passed (20/20 total for T01+T02+T03 together). LA Overall +38.8% ✓, NYC Overall +10.0% ✓, success count 8156 (within ±50 of 8150) ✓, NYC Office present ✓.
- Notes: Unmapped archetype warning (`LargeOffice`, `MediumOffice`) is a known passthrough logged by `reconstruct_frame`; unchanged from V19 baseline.

#### T02 — Basis transform function — completed 2026-06-21
- Artifacts: `apply_basis_to_frame` in `scripts/validation/v19_basis_diagnostic.py`; `tests/test_v19_basis_diagnostic.py` class `TestApplyBasisToFrame` (9 tests)
- Deviations: None. `total_eui_kwh_m2` recomputed as sum of four mutated columns per F3.
- Test status: 9/9 transform unit tests passed. Identity returns identical values within 1e-9; `÷3.5` cooling verified exactly; total = sum of four verified per row.
- Notes: Pure column arithmetic on a `.copy()`; input df not mutated (verified by test).

#### T03 — Single-combo scorer — completed 2026-06-21
- Artifacts: `score_combo` in `scripts/validation/v19_basis_diagnostic.py`; `tests/test_v19_basis_diagnostic.py` class `TestScoreCombo` (7 tests)
- Deviations: None. "Overall" matched via `str.startswith("Overall")` per plan; dict keys: `{city}_{seg.lower()}_delta`.
- Test status: 7/7 scorer tests passed. Identity combo via `score_combo` reproduces LA Overall +38.8% ±0.5 pp ✓, NYC Overall +10.0% ±1 pp ✓, max_abs_delta consistency ✓.
- Notes: **CP-1 identity reproduction numbers** (actual): NYC Office +36.7%, NYC Overall +10.0%, LA Office +78.4%, LA Overall +38.8%, Austin Office +41.1%, Austin Overall +42.2%. Success-row count: 8156.

#### T04 — Run the full grid — completed 2026-06-21
- Artifacts: `run_grid` + `_identity_present` in `scripts/validation/v19_basis_diagnostic.py`; `docs/docs_ACTIVE/phaseC_combinedResim/v19_validation/basis_sweep_combos.csv` (120 rows); `tests/test_v19_basis_diagnostic.py` class `TestRunGrid` (7 tests)
- Deviations: None. Grid asserted 120 rows exactly; identity combo verified present. CSV written sorted by max_abs_delta ascending.
- Test status: 7/7 grid tests passed (including CSV on-disk check). Runtime: ~488 s total for full test session (120 combos × ~8k rows, serial; acceptable for a one-off per plan note).
- Notes: `itertools.product` over 5×2×4×3 = 120. `reconstruct_frame` call per combo is the bottleneck; no parallelism needed per plan.

#### T05 — Coherence analysis — completed 2026-06-21
- Artifacts: `compute_coherence` in `scripts/validation/v19_basis_diagnostic.py`; `tests/test_v19_basis_diagnostic.py` class `TestCoherence` (5 tests)
- Deviations: Per-city ceiling computed as min over ALL grid rows (vary all params, not just cooling_cop) to give the most conservative (lowest) achievable max_abs_delta per city. This is strictly tighter than "allow different cooling_cop only" as stated in the plan — it is a broader optimum and makes the ceiling claim stronger. Per §3 "no new measured data / no scope creep" this is conservative data; the interpretation remains the manager's.
- Test status: 5/5 coherence tests passed. Assertions: best-global (13.00%) ≤ identity (78.40%) ✓; per-city ceilings (NYC 8.2%, LA 6.0%, Austin 1.8%) ≤ global best ✓.
- Notes: **CP-2 coherence results**: best-global combo = (cop=2.5, hf=1.19, ls=0.8, es=0.7), max_abs_delta=13.00%, n_within_15=6/6, n_within_20=6/6. NYC Overall −7.7%, LA Overall −13.0% — SAME sign (both negative). Per-city ceilings all well below global best.

#### T06 — Findings memo — completed 2026-06-21
- Artifacts: `write_findings` + `_LOAD_SCALING_CAVEAT` in `scripts/validation/v19_basis_diagnostic.py`; `docs/docs_ACTIVE/phaseC_combinedResim/v19_validation/RESULT_basis_diagnostic.md`; `tests/test_v19_basis_diagnostic.py` class `TestFindingsFile` (7 tests)
- Deviations: None. All six sections present in order per plan. Verbatim caveat from §3 included. `_df_to_md_table` imported from `scripts.v19_rescore` (single source of truth). No interpretation prose written (rule 8 complied with).
- Test status: 7/7 findings file tests passed. File exists, all sections non-empty, coherence metrics section contains n_within_15/n_within_20/opposite-sign fields.
- Notes: stdout self-check echoes identity reproduction and best-global row on every `__main__` run. `n_within_15` and `n_within_20` appear as floats in the MD header line (from pandas Series `.iloc[0]`); the integer values are correct (6/6). **Full test suite: 39/39 passed.**
