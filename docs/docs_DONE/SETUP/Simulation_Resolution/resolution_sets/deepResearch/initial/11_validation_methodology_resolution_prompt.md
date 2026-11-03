# Deep-Research Prompt 11 — VALIDATION METHODOLOGY for resolution sensitivity (without fitting)

> SCOPE GUARD — READ FIRST. This is a **validation-design** task. The deliverable is the **method** to
> test whether higher resolution improves (or fails to improve) OpenUBEM's agreement with measured
> benchmarks — **without tuning any parameter** — and how to report the resolution effect. It is NOT
> about implementing the modes (Prompts 01–08) or their compute cost (Prompt 10). If you are writing
> about anything other than **how to validate the resolution switch and report it defensibly**, stop
> and return to the tables. See `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request designing the validation of the resolution switch. OpenUBEM already has a
**12-cell / 8,160-building benchmark** (NYC LL84, LA EBEWE, Austin CBECS-proxy) scored under the
`auto` mode with a **zero-fitted-parameters** rule and a headline city-EUI ±9%. The question: how do
we re-run a subset under `building` / `floor` / `zone` and rigorously show what resolution does to
accuracy, without falling into the trap of "resolution as a tuning knob." Treat each cell as a
question; fill with a sourced method or a GAP.

## Role

Building-energy-modelling validation analyst. Trace methods to: **ASHRAE Guideline 14 / IPMVP**
(NMBE, CV(RMSE) acceptance thresholds), **peer-reviewed UBEM validation literature** (how zoning/LOD
sensitivity is reported), and standard statistical practice (paired comparison, stratified sampling,
confidence intervals). Reference OpenUBEM's existing metrics (city-overall EUI %, national CBECS NMBE
+ R²). No fabricated precision.

## Why this matters (so you scope correctly)

A naive "zone mode is more detailed so it must be better" claim is not evidence. We need a design that
(a) holds all non-zoning inputs fixed, (b) compares each mode's error against the **same** measured
benchmark, (c) reports per-stratum (city × density × archetype) so a city-average wash-out doesn't
hide where resolution helps, and (d) preserves the zero-fitted-parameters rule (resolution is a
structural choice, not a calibrated one). We also need to decide what an "improvement" even means
(closer mean? tighter distribution? better peak?).

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Validation metrics per mode (against measured)

| Metric | Definition | Acceptance threshold | Source |
|---|---|---|---|
| City-overall EUI % error | | (OpenUBEM uses ±X%) | |
| NMBE (per region) | | (Guideline 14) | |
| CV(RMSE) (building-level) | | (Guideline 14) | |
| R² (vs measured benchmark) | | | |
| Distribution match (KS / quantiles) | | | |
| Peak-load metric (if measured available) | | | |

### Table 2 — Experimental design

| Element | Recommendation | Rationale | Source |
|---|---|---|---|
| Sample (full 12-cell vs stratified subset) | | | |
| Hold-fixed variables (archetype, weather, envelope, schedules) | | | |
| Paired vs independent comparison across modes | | | |
| Stratification (city × density × archetype) | | | |
| Sample size for a detectable resolution effect | | | |

### Table 3 — What "better" means (avoid false improvement)

| Candidate criterion | Pro | Con / trap | Recommended? |
|---|---|---|---|
| Lower mean city EUI error | | (can wash out per-building) | |
| Lower building-level CV(RMSE) | | | |
| Tighter error distribution | | | |
| Better in resolution-sensitive strata only | | | |

### Table 4 — Guardrails (zero-fitted-parameters discipline)

| Risk | Guardrail | Source |
|---|---|---|
| Treating mode choice as a tuning knob | (pre-register the mode per study; report all modes) | |
| Cherry-picking the mode that fits best | | |
| Confounding resolution with other changes | | |
| Over-claiming from a city-average that hides strata | | |

---

## Part C — Synthesis (validation protocol)

Give a **step-by-step validation protocol** OpenUBEM can run: the sample, the held-fixed inputs, the
metrics, the stratification, the acceptance criteria, and the reporting format (a per-mode × per-cell
table). State explicitly how the protocol preserves zero-fitted-parameters and what result would
**falsify** "higher resolution helps" (e.g. no CV(RMSE) improvement beyond noise).

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C protocol + falsification criterion.
3. Cite Guideline 14 / IPMVP for thresholds and ≥2 UBEM validation papers for LOD-comparison practice.
4. **"Confidence and caveats":** the biggest methodological risk (likely strata wash-out or knob-tuning).
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Define the metrics with thresholds** (Guideline 14 NMBE / CV(RMSE)).
- **Give a concrete experimental design** (sample, held-fixed, stratification).
- **State a falsification criterion** for "resolution helps."
- **Preserve zero-fitted-parameters** — make the guardrails explicit.
- **No fabricated precision;** flag GAPs. **Stay on topic** — validation design only.
