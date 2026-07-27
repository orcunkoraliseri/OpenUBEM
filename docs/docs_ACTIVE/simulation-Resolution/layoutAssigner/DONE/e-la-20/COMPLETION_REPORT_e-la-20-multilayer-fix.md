# COMPLETION REPORT — E-LA-20 Multi-Layer Envelope-Assembly Fix

**Plan:** `PLAN_e-la-20_multilayer-fix.md` (same folder) · **Date:** 2026-07-25
**Status at time of writing:** F12 complete. CP-C **signable**, not yet signed — signature is reserved to the manager.
**Predecessor:** `PLAN_e-la-20_investigation.md` / `COMPLETION_REPORT_e-la-20-investigation.md` (root-cause investigation, closed 2026-07-25, not re-derived here).

---

## 1. What shipped

**Defect.** `patch_envelope()` (`openubem/geometry/envelope_patcher.py`) and its twin `assign_constructions()` (`openubem/idf/builder.py`) built every opaque assembly as a single homogeneous layer at fixed conductivity `_K = 0.12 W/m·K`, so `Thickness = (1/u) * _K` absorbed the entire target R-value. Harmless under `MATERIAL:NOMASS`; under `thermal_mass=True` a well-insulated roof became a slab over a metre thick, which EnergyPlus's CTF solver cannot expand at the model's timestep — `Fatal — InitConductionTransferFunctions`.

**The shipped rule (§4-quinquies of the plan, binding, verbatim):**

```
T_ENGAGE   = 0.868 m     # FROZEN -- F-13, measured uncapped-safe limit, 0 FP / 0 FN over 8,160 fleet rows
T_MASS_MAX = 0.35 m      # FROZEN -- F-20, measured directly at the value and the u it ships to

total_t = max(0.01, (1/u) * _K)
if total_t <= T_ENGAGE:
    emit exactly what production emits today      # single MATERIAL, byte-identical
else:
    t_mass     = T_MASS_MAX
    r_residual = 1/u - t_mass/_K                  # carried by MATERIAL:NOMASS, U preserved exactly
```

Both constants carry mandatory provenance comments in the shipped code (`openubem/idf/opaque_assembly.py:21-27`) and may not be re-tuned, re-derived, or made a function of anything.

**Provenance of the two frozen constants:**
- `T_ENGAGE = 0.868 m` — fact **F-13**: measured uncapped-safe boundary, re-derived from all 8,160 T19 harvest `eplusout.err` files (F02-R), zero false positives and zero false negatives.
- `T_MASS_MAX = 0.35 m` — fact **F-20**: measured by F03-T3 at the exact production constant, at the exact `u` it ships to (`u = 0.119`, the fleet's one real exposed value, F-19), with a ±0.03 m stability probe (10/10 PASS at both `u = 0.097` and `u = 0.119`) and a 2/6 ts/h timestep check. Not inferred from a bracket — F-17 (below) rules that inference out.

**Implementation.** One shared function, `build_opaque_assembly(idf, name, u_value, thermal_mass) -> str` in the new module `openubem/idf/opaque_assembly.py`, called from both defect sites (`envelope_patcher.patch_envelope()` and `builder.assign_constructions()`) so the fix lives in exactly one place (closes fact F-08, the latent second defect site). No `timesteps_per_hour` parameter — F-16/F-20 measured the boundary as timestep-free at 2/4/6 ts/h, so the module does not read `TIMESTEP` at all.

**Two byte-identity guarantees, both signed at CP-B by an independent reconstruction (not the executor's own "no diff" claim):**
1. **`thermal_mass=False`** — identical output to `HEAD`, for every assembly, unconditionally. This is the pre-existing regression guarantee; every previously validated project result runs on this path.
2. **`thermal_mass=True` with `total_t <= T_ENGAGE`** — identical output to `HEAD`'s own `thermal_mass=True` behaviour below the cap. Verified explicitly at `u = 0.182` (`total_t = 0.6593 m`), the deepest wall/floor value in the construction library and the path that covers 8,010 of the 8,160 fleet rows. The manager rebuilt the pre-fix inlined block from `git show HEAD` in a scratchpad harness and `difflib`-diffed the rendered IDF text against the new module's output: no diff, for both guarantees.

At `u = 0.119` (the real fleet operating point, F-19) the emitted assembly is read back out of a generated IDF at thickness exactly `0.35` m with a `_L2` `MATERIAL:NOMASS` residual, `U` preserved to `1/u` bit-for-bit.

---

## 2. What was falsified on the way, and by what

Three dispatches on this arc produced four falsifications before the shipped rule was reached. A future reader who does not know this could easily re-propose one of them.

1. **The Fourier `sqrt(dt)` scaling — falsified by F01.** The original plan predicted the CTF boundary via `L_max = sqrt(alpha * dt / (SAFETY * Fo_crit))`, calibrated at 4 timesteps/hour. F01 measured the boundary directly at 2, 4 and 6 ts/h (26 real EnergyPlus runs, all failures carrying the genuine `CTF calculation convergence problem` severe) and found it **flat** (0.868 – 0.946 m) and **non-monotonic** across a 3× Δt range — the opposite of the predicted `sqrt(dt)` growth. `Fo_crit` and `SAFETY` as Fourier constants were retired; the plan's own headline "12.6% exposure" extrapolation (which rested on the same scaling) was withdrawn with them.

2. **The mass-preserving adaptive-N split — falsified by F-14 / F03-R.** The plan's primary fix shape replaced the single fat layer with N identical sublayers of the same total R *and* the same total mass. F03-R (38 audited runs + 2 controls) found genuine CTF failure at the fleet's true worst case (`u_roof = 0.097`, `total_t = 1.2371 m`) at **every N from 1 to 10, at every timestep** — the split cannot clear this case at all. The mechanism: splitting preserves total R and total mass exactly, hence preserves `R·C` exactly, and `R·C` is what the CTF series responds to — proven non-circularly by the executor's own data (a 0.3810 m layer FATALs at `total_t = 1.1429 m` while a *thicker* 0.5042 m layer PASSES at `total_t = 1.0084 m`; layer thickness is not the control variable, total thickness is). **Binding corollary: any mass-preserving fix is dead on arrival.** This retired the plan's entire original design (§4/§4-bis) and promoted the pre-registered reserve candidate (c2) — a capped mass layer plus a `MATERIAL:NOMASS` residual — which does not preserve mass and is the shape that shipped.

3. **The `R·C`-scaled cap, rule (T-b) — falsified by F03-T's own 16 points.** Once (c2) was adopted, its one free constant (the cap) needed a rule. (T-b) proposed capping the *whole assembly's* `R·C` (mass layer plus massless residual). It is falsified by the same 16 measurements that discriminated it into contention: a capped `R·C` of `4.033e6` FATALs (`u = 0.119`, `t_mass = 0.60`) while a **larger** `4.948e6` PASSES (`u = 0.097`, `t_mass = 0.60`) — no monotone rule in capped `R·C` can order that pair.

4. **The fractional cap, rule (T-c) — falsified by F03-T2 (fact F-17).** (T-c) (`t_mass = c · total_t`) fit all 16 of F03-T's points cleanly, with a bracket `c* ∈ (0.525, 0.566]`. F03-T2 added 24 points at three distinct `u` and broke it in its own load-bearing series: at `u = 0.097`, `c = 0.50` PASSES, `c = 0.45` FATALS, `c = 0.40` PASSES — a FATAL sandwiched between two PASSing neighbours, verified genuine on the raw IDFs (correct thicknesses, `U` preserved to 10 s.f., a real CTF severe in the FATAL's own `.err`). No monotone threshold in `c` can produce that ordering; `c*` is not merely `u`-dependent, it is undefined at `u = 0.097`. This is fact **F-17** (next section) and it killed (T-c) outright. What survived, recovered by pooling F03-T's and F03-T2's 40 points and sorting by **absolute** thickness alone, was a **constant thickness cap** (rule (T-a), the form provisionally rejected earlier in the arc on a single value that happened to sit inside the boundary's chaos band) — this is the rule that shipped, as `T_MASS_MAX = 0.35 m`.

---

## 3. The non-monotonicity result (F-17) — standing caveat

**Fact F-17, stated precisely: CTF convergence is not monotone in the cap thickness.** At `u = 0.097`, holding everything else fixed and varying only `t_mass`:

| `t_mass` (m) | 0.4330 | 0.4948 | **0.5567** | 0.6186 | 0.6804 |
|---|---|---|---|---|---|
| result | PASS | PASS | **FATAL** | PASS | FATAL |

Manager-verified on the raw IDFs: all three neighbours correctly labelled, `U` preserved to 10 significant figures in each, the FATAL carrying a genuine CTF severe in its own `.err`. This is a real isolated island between two passing neighbours, not a harness or labelling error.

**Consequence, binding on this arc and on any future one that touches this constant:** a bracket or interpolation on this boundary does not license its interior. "It passed at 0.30 m and it passed at 0.43 m, so 0.35 m is safe" is exactly the inference F-17 refutes. **Any constant that ships must be measured at the value that ships, at the `u` it ships to** — which is what F03-T3 did before `T_MASS_MAX = 0.35` was frozen (series 1: PASS at the real exposed `u`; series 2: 10/10 PASS across a ±0.03 m window at both `u = 0.097` and `u = 0.119`, ruling out 0.35 being another island). **No future tuning of `T_MASS_MAX` may be justified by bracketing between measured points — only a direct measurement at the new shipped value, at the `u` it ships to, counts.**

---

## 4. The physical cost, stated as a cost

Capping the mass layer sheds thermal capacity by construction (mass is deliberately **not** preserved — F-14 rules out any mass-preserving alternative). This is a genuine physics change, not merely a numerics fix, and it must be reported as a cost.

**Corrected figure (supersedes an earlier characterization — see below for why).** Measured by F11-N-b, a matched `thermal_mass=False` control over all **150** engaged fleet rows, same geometry, same schedules, same code, only the roof assembly varying:

| | value |
|---|---|
| min | −2.124% |
| p25 | −1.924% |
| **median** | **−1.732%** |
| p75 | −1.533% |
| max | −0.995% |
| mean | −1.716% |
| sign | **150 negative, 0 positive, 0 zero** |

The effect is **uniformly negative** — the fix *lowers* annual site EUI by roughly 1–2% on every one of the 150 engaged rows, with no sign reversal anywhere in the population. This is the physically expected direction for added roof thermal mass in this climate.

**Why this supersedes an earlier record, and the correction is stated explicitly rather than swapped quietly.** F08 (11-building real-EnergyPlus regression) originally reported the EUI shift as small and *bidirectional* (+0.26% to +4.30%), which sat in apparent tension with F03-T3's stress-point measurement of −2.13%. That characterization is now known to be an artifact: F08's `thermal_mass=False` reference values were hardcoded from the investigation's earlier I02 artifact (`f08_run.py:51-53`) — a separate run at a different HEAD, not a matched control run inside F08 itself. Against a true matched control (F11-N-b), the sign flips on all three of F08's own buildings:

| building | fix ON (EUI) | F08's stale reference → delta | F11-N-b matched control → delta |
|---|---|---|---|
| `way/270445755` | 73.275 | 70.251 → +4.30% | 74.011 → **−0.99%** |
| `way/772627020` | 83.603 | 81.108 → +3.08% | 84.864 → **−1.49%** |
| `way/772627076` | 153.611 | 153.212 → +0.26% | 156.944 → **−2.12%** |

F03-T3's −2.13% synthetic-stress-point measurement was the correct sign all along; it sits exactly at this distribution's negative tail (−2.124%). The stale-reference bug is logged as its own defect, **E-LA-24** (§9 below) — it is a reporting-layer issue only; no simulation or production code is wrong. Do not read the effect as free or as a wash: it is a consistent, one-directional EUI change on every engaged row, of order 1–2%.

---

## 5. Residual risk

- **F-19(c): the fleet's exposed set is a single construction, not a distribution.** All 150 engaged rows in the current fleet share exactly one `u_roof = 0.119` (`total_t = 1.0084 m`). This narrows the *measured* risk to one construction, but it also means the exposure is fragile to inputs the fix does not control: a vintage remap, a new cell, or a new archetype can move buildings across `T_ENGAGE` with **no code change at all**. F-19's roof-only predicate had 0 false negatives over 8,160 rows (no wall or floor assembly in the fleet is thick enough to fail CTF), so walls and floors stay byte-identical today — but that is a fact about today's fleet, not a structural guarantee.
- **E-LA-23 — the fix drives warmup non-convergence on the engaged population (new, this plan, OPEN).** See §9 for the full disposition; summarized here as residual risk: 96/150 (64%) engaged rows emit a `CheckWarmupConvergence` severe under the fix, vs 8/150 (5.3%) in the matched `thermal_mass=False` control — a measured, attributable effect, non-blocking (0 CTF, 0 Fatal, every run completes), with zero present blast radius because the adopted baseline runs `thermal_mass=False` everywhere (F10).
- **E-LA-24 — reporting-layer defect (new, this plan, closed by correction, logged for the generic lesson).** See §4 and §9. No simulation or production impact; recorded because the failure mode — comparing against a prior artifact as if it were a matched control, when other things (HEAD, classification, per E-LA-22) moved between the two artifacts — is generic and will recur if not named.
- **E-LA-21 and E-LA-22, carried from the investigation, remain OPEN and out of scope for this plan** (disposition restated explicitly in §9).

---

## 6. Verification results

| Task | What it covers | Result |
|---|---|---|
| **F08** | Real-EnergyPlus regression on the investigation's own 11-building Fatal reproduction set, production path, `thermal_mass=True`. | **11/11 PASS.** Manager re-grepped all 11 `eplusout.err`: zero CTF severes, zero Fatals of any kind. EUI characterization corrected — see §4. |
| **F09** | Synthetic combinatorial sweep, every distinct `(timestep, u_roof)` pair the construction library can produce (48 distinct `u_roof` × 3 timesteps = 144 cells), via a post-processing harness. | **144/144 PASS, 0 FATAL.** Manager re-grepped all 144 `.err`: zero severes of any kind. Engagement flag re-derived independently for every row: 0 mismatches. Gap closed: the shipped module's emitted parameters were compared against the harness's at all 48 `u` values — 0 mismatches beyond 6-dp rounding — so F09's breadth transfers to the shipped code. |
| **F10** | Proof that the adopted simulation baseline (E-R3-3 + Phase-E + elevators) is unchanged by this fix. | **Proven from source, no simulation required.** The adopted baseline's driver (`v12_cell_pipeline.py` → `run_step3(resolution_mode="auto")` → `builder.py:190-198`) resolves `thermal_mass=False` on every built row — verified by grepping the driver for either keyword (zero occurrences) and reading the resolution logic directly. Combined with the CP-B byte-identity proof, the baseline never reaches the changed branch by construction. |
| **F11-N** | Narrowed fleet-scale verification (replacing the original F11, see below): all **150** engaged rows, production path, `thermal_mass=True`. | **150/150 PASS, 0 CTF, 0 Fatal.** Manager independently reconciled 150 CSV rows = 150 run dirs = 150 `.err` = 150 `.end`, and re-grepped all 150 `.err` directly. |
| **F11-N-b** | Matched `thermal_mass=False` control over the same 150 rows. | **150/150 PASS, 0 CTF, 0 Fatal.** Control validity verified by the manager on the generated IDF before accepting the run: the fix's mass layer is fully disengaged and the roof assembly is the sole varying factor. Produced the corrected EUI distribution (§4) and the warmup-convergence comparison (E-LA-23). |

**F11 (the originally specified full 8,160-row fleet re-run) was a manager NO-GO, not executed as written; F11-N + F11-N-b are its replacement.** The reasoning: F11's own pass criterion — "the 8,010 sub-threshold rows must be numerically identical to T19" — cannot be measured cleanly, because E-LA-22 (T19's archetype/vintage assignment is not reproducible at current HEAD for data-poor buildings) would inject unrelated deltas into any such comparison and manufacture a false alarm. The criterion is instead **discharged as an argument**: CP-B's byte-identity proof (below `T_ENGAGE` the rendered IDF is byte-identical to `HEAD`) plus EnergyPlus's determinism (identical IDF + identical EPW + identical version ⇒ identical output) together establish that the 8,010 sub-threshold rows are unaffected, without spending ~15 hours of wall-clock to re-confirm determinism. F11-N then covers what genuinely was unverified — all 150 at-risk rows, not merely the 11 F08 had already run, through the real production path on real (not synthetic) multi-zone geometry.

---

## 7. What was NOT verified, stated as plainly as what was

- **The full 8,160-row fleet was never re-run with the fix.** No task in this plan simulated the fleet at scale with `thermal_mass=True`.
- **There is no T19 comparison.** E-LA-22 makes a byte-for-byte or numeric fleet-vs-T19 comparison irreproducible for any row whose classifier inputs came from imputation, so such a comparison was not attempted.
- **The claim that the 8,010 sub-threshold rows are unaffected rests on an argument, not a measurement:** CP-B's byte-identity proof (the rendered IDF is unchanged below `T_ENGAGE`) plus EnergyPlus's determinism. This is a sound argument — not a weaker substitute dressed up as one — but it is not itself a simulation result.
- **The condition under which that argument collapses, stated explicitly:** the moment any future change makes the sub-threshold path *not* byte-identical to today's pre-fix output (a change to `envelope_patcher.py`, `builder.py`, or `opaque_assembly.py` itself, or an upstream change to the U-values feeding it), the argument no longer holds and a real fleet-scale run becomes necessary again to re-establish non-regression.
- **E-LA-23's magnitude effect on annual results was never quantified.** Its *presence* (96/150 vs 8/150 warmup severes) is measured; its effect on the annual EUI number itself — beyond the already-reported overall EUI shift, which is not decomposed by warmup-convergence status — was not isolated as its own measurement.

---

## 8. Coverage split, stated honestly

Two different axes of evidence exist in this arc, and neither task alone covers both:

- **F09 gives parameter-space breadth (48 distinct `u_roof` values × 3 timesteps = 144 cells) but through a post-processing harness, not the shipped module directly** — closed only by the manager's separate parameter-comparison check (0 mismatches at all 48 values), and even so, F09's harness never built a real multi-zone building shell.
- **F08 and F11-N give real production-path fidelity — the actual `BuildingIDF(..., thermal_mass=True, resolution_mode="layout_assign")` call, on real multi-zone geometry — but only at `u = 0.119`,** the fleet's one real exposed construction.

**The concrete demonstration that these are genuinely different axes, not redundant coverage of the same thing: F09's 144-cell synthetic sweep reported zero severes of any kind and could not have surfaced E-LA-23**, because it never ran a real multi-zone shell — `CheckWarmupConvergence` is a per-zone diagnostic that depends on real zone topology, which a single-zone synthetic sweep does not have. E-LA-23 was found only by F11-N/F11-N-b, which ran real geometry. Synthetic parameter breadth and production fidelity on real geometry are different axes; neither substitutes for the other, and this arc is direct evidence of that rather than an assertion of it.

---

## 9. Defect dispositions

**Carried forward from the investigation, both remain OPEN and out of scope for this plan — this plan did not address either:**

- **E-LA-21** — the T17/T18/T19 harvest scripts' `has_fatal` column is dead fleet-wide (string-literal space mismatch against EnergyPlus's real `.err` text). Reporting-layer only, no simulation impact. Not touched by this plan.
- **E-LA-22** — T19's archetype/vintage assignment is not reproducible at current HEAD for data-poor buildings (imputation changed post-T19). Material to any cross-generation fleet comparison, including why F11 as originally specified could not be run cleanly (§6). Not touched by this plan.

**Discovered by this plan, both new, both OPEN, both forwarded out of the arc:**

- **E-LA-23 — the fix drives warmup non-convergence on the engaged population.** Under `thermal_mass=True` with the capped mass roof, 96/150 (64%) engaged rows emit `** Severe ** CheckWarmupConvergence: Loads Initialization, Zone="<zone>" did not converge after 25 warmup days`; the matched `thermal_mass=False` control over the identical 150 buildings gives 8/150 (5.3%) — a 12× increase, same geometry, same schedules, same code, one variable changed (F11-N-b, manager-verified by direct grep of all 300 `.err` files across both arms). **Severity: non-blocking accuracy caveat, not a failure** — all 150 runs complete with `EnergyPlus Completed Successfully`; 0 CTF, 0 Fatal in either arm. **Attribution: the fix is the primary driver, not the sole cause** — the 8/150 residual under `thermal_mass=False` is intrinsic to this archetype's real multi-zone geometry and pre-dates the fix. **Present blast radius: zero** — the adopted simulation baseline runs `thermal_mass=False` on every built row (F10), so no published result is affected today; this becomes live the moment any production configuration turns `thermal_mass=True` on for `layout_assign`. **Not fixed here, deliberately** — candidate remedies (raising `Building.Maximum_Number_of_Warmup_Days`, relaxing convergence tolerances, or lowering `T_MASS_MAX` further) all lie outside this plan's mandate, and the last of the three would reopen a constant frozen at CP-A-bis. Forwarded as its own future arc.

  **⚠️ Manager correction at CP-C — E-LA-23 is NOT a new phenomenon, and framing it as one understates it.** `thermal_mass=True` perturbing `CheckWarmupConvergence` is an *already-logged, four-entry lineage* in the structural-fixes plan: **E-LA-14** (`SecondarySchool`), **E-LA-16** (`Hospital` + `TallBuilding`), **E-LA-18** (`LargeOffice`), **E-LA-19** (zone-composition shift on E-LA-14's own building). Fleet-wide prevalence roughly doubled when `thermal_mass=True` became the `layout_assign` default — **105/8,160 (1.29%) at T18 → 203/8,160 (2.49%) at T19**. Every one of those entries hedged its attribution: E-LA-19's own text reads *"Root cause: not fully proven, appropriately hedged."* What is genuinely new here is **not the effect but the evidence**: F11-N-b is the first **matched control** ever run on it — same buildings, same geometry, same code, one variable — which converts a four-times-repeated hypothesis into a measured, attributed fact. E-LA-23 should therefore be filed as the **fifth and densest locus** of that lineage (64% vs a 2.49% fleet background), and as its causal confirmation.

  Two consequences follow, both forwarded rather than decided here. **(a) The 150 are additive to the fleet count, not already in it.** At T19 these buildings were Fatal, so they contributed **0** to the 203; with the fix they complete, and ~96 of them would newly flag. A fixed fleet run at `thermal_mass=True` would therefore show roughly **299/8,160 ≈ 3.66%**, not 2.49% — a projection from this arc's measurement, not a measurement. **(b) The standing "cosmetic" disposition deserves re-examination.** That label was accepted when the effect looked like a 1–2% fleet-wide severe-count artifact with `status` preserved. At 64% of an archetype/cell segment it is still `status`-preserving, but "cosmetic" is a claim about *accuracy* — an unsettled initial-condition state — that no one in this lineage has ever measured. This arc did not measure it either (§7). Re-deciding that disposition is the forwarded arc's job, on evidence, not this report's.

- **E-LA-24 — a prior-artifact EUI reference was used as if it were a matched control.** `f08_run.py:51-53` hardcoded `thermal_mass=False` EUI values from the investigation's earlier I02 artifact rather than measuring a matched control in-run. Against a true matched control (F11-N-b) the deltas invert on all three of F08's own buildings (+4.30/+3.08/+0.26% → −0.99%/−1.49%/−2.12%), which is what produced the now-superseded "bidirectional EUI shift" characterization corrected in §4. **Reporting-layer only** — no simulation or production code is affected. Logged because the failure mode is generic: with E-LA-22 in force, other things (HEAD, classification) move between artifacts, so a cross-artifact EUI difference cannot be attributed to the one variable actually under study.

---

## 10. Artifacts

**Production code (shipped):**
- `openubem/idf/opaque_assembly.py` (new)
- `openubem/geometry/envelope_patcher.py` (material-creation block only)
- `openubem/idf/builder.py` (`assign_constructions()` material-creation block only)
- `tests/test_opaque_assembly.py` (new, 38 tests); `tests/test_envelope_patcher.py` / `tests/test_idf_builder.py` unmodified and passing (88 total, `pytest tests/test_opaque_assembly.py tests/test_envelope_patcher.py tests/test_idf_builder.py -q`)

**Verification CSVs, `openubem/outputs/`:**
`e_la_20_fix_f01_timestep_calibration.csv`, `e_la_20_fix_f02_fleet_confusion.csv`, `e_la_20_fix_f02r_fleet_confusion.csv`, `e_la_20_fix_f03_worst_case_verification.csv`, `e_la_20_fix_f03r_worst_case_verification.csv`, `e_la_20_fix_f03t_cap_boundary.csv`, `e_la_20_fix_f03t_eui_cost.csv`, `e_la_20_fix_f03t2_fraction_boundary.csv`, `e_la_20_fix_f03t2_eui_cost.csv`, `e_la_20_fix_f03t3_constant_verification.csv`, `e_la_20_fix_f03t3_eui_cost.csv`, `e_la_20_fix_f08_investigation_regression.csv`, `e_la_20_fix_f09_sweep.csv`, `e_la_20_fix_f10_static_reachability.csv`, `e_la_20_fix_f10_baseline_fleet_integrity.csv`, `e_la_20_fix_f11n_engaged_population.csv`, `e_la_20_fix_f11nb_thermal_mass_false_control.csv`.

**Plan doc (binding record of all measurements, audits and decisions summarized above):** `PLAN_e-la-20_multilayer-fix.md`, §4-ter/§4-quinquies (rule), §5 (facts F-01…F-20), §6 (task specs), §8 (progress log + every AUDIT entry), §9 (error log).

**This report:** `COMPLETION_REPORT_e-la-20-multilayer-fix.md` (this file).

No new figure (`.png`) was produced by this plan's Phase C tasks — verification output is tabular (CSV) only — so the figure-copy requirement does not add any file beyond the CSVs already listed above.
