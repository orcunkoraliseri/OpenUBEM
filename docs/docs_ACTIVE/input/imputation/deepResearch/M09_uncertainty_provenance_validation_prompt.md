# Deep-Research Prompt M09 — UNCERTAINTY, PROVENANCE & VALIDATION of imputed inputs (how to prove the imputer is trustworthy)

> SCOPE GUARD — READ FIRST. This is the **rigor** prompt — it does not choose an imputation algorithm,
> it defines how OpenUBEM *evaluates* whichever it picks and *carries the resulting uncertainty forward*.
> Answer two joined questions: (1) **evaluation** — how to measure imputation quality, including the
> UBEM-specific requirement to measure the *downstream EUI impact*, not just input-reconstruction error;
> (2) **uncertainty propagation & provenance** — multiple imputation → ensemble runs, confidence flags,
> sensitivity analysis. Do NOT rank algorithms (`M03`–`M06`, `M10`) or design the module (`M08`). See
> `00_README_imputation_prompt_set.md`.

---

## What this document is

A methods survey for validating an imputer and propagating its uncertainty in a UBEM context. This is
the prompt that keeps the whole feature honest: an imputer that reconstructs `year_built` with low RMSE
but shifts the city-scale EUI by 15% is a failure, and one whose imputed values carry no uncertainty into
the results misrepresents confidence. OpenUBEM's constraints make this central — the zero-fitted-
parameters rule means the imputer must be *validated*, not *tuned*, against held-out data, and the
provenance rule means every imputed value must be traceable and ideally uncertainty-quantified.

## Role

Uncertainty-quantification / validation-methodology analyst for building-stock modelling. Ground
evaluation methods in the missing-data-validation literature (mask-and-recover / hold-out design; proper
scoring for categorical vs. continuous imputation; Rubin's rules for multiple-imputation variance) and
in UBEM/building-stock studies that report the *downstream* effect of input uncertainty on simulated
energy (the İşeri et al. paper, Kristensen et al., Mastrucci et al., and the UBEM sensitivity-analysis
literature).

## Why this matters (so you scope correctly)

Two failure modes this prompt must prevent. (1) **Validating on the wrong target** — reporting input-
reconstruction accuracy while the thing that matters is EUI robustness; the manager needs the field's
guidance on tying imputation error to energy error. (2) **False confidence** — treating a single imputed
value as if it were observed, so the result's error bars don't reflect that a quarter of the inputs were
guessed. Multiple imputation and provenance flags exist precisely to fix this; this prompt sources how.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Imputation evaluation protocols

| Protocol | What it measures | Suited to categorical (use/vintage) or continuous (height/area)? | Guards against leakage/overfitting how? | Source |
|---|---|---|---|---|
| Mask-and-recover on complete cases |  |  |  |  |
| k-fold / spatial cross-validation |  |  |  |  |
| Proper metric choice (RMSE/MAE vs. PFC/log-loss) |  |  |  |  |
| Distributional fidelity (does it preserve the histogram?) |  |  |  |  |

### Table 2 — Downstream (energy) impact evaluation — the UBEM-specific requirement

| Method | How it links input-imputation error to simulated-EUI error | Reported magnitude in a study (imputed-input → % EUI change) | Source |
|---|---|---|---|
| One-at-a-time input perturbation |  |  |  |
| Multiple-imputation ensemble → EUI distribution |  |  |  |
| Global sensitivity (Sobol/Morris) on imputed inputs |  |  |  |

### Table 3 — Uncertainty propagation & provenance mechanisms

| Mechanism | What it carries forward | How it surfaces to the user (error bars, confidence tier, replicate runs) | Fits OpenUBEM's flag-token + HIGH/MED/LOW convention? | Source |
|---|---|---|---|---|
| Single imputation + confidence flag |  |  | (OpenUBEM's current style) |  |
| Multiple imputation (Rubin's rules) |  |  |  |  |
| Per-value predictive variance (from the imputer) |  |  |  |  |
| Provenance/indicator column |  |  |  |  |

### Table 4 — Distributional-fidelity check (the İşeri paper's core claim)

The in-repo paper argues probabilistic fills preserve building-stock *heterogeneity* where deterministic
defaults collapse it.

| Question | Literature answer | Source |
|---|---|---|
| Do deterministic single-value fills (mean/mode/oldest-vintage) demonstrably collapse stock variance? |  |  |
| Is preserving the input *distribution* (not just the point value) a recognized validation criterion? |  |  |
| Does OpenUBEM's KDE-fill (existing) satisfy this where its `pd.cut → oldest` and `→400 m²` fills do not? |  |  |

---

## Part C — Synthesis (the validation & uncertainty protocol)

Give: (1) a concrete **validation protocol** OpenUBEM should adopt for any imputer — the hold-out design,
the per-input-type metric, and the mandatory downstream-EUI check — expressed so it can go straight into
the implementation plan's test section; (2) a ruling on **single-imputation-with-confidence-flag vs.
multiple-imputation-ensemble** for UBEM: is the added compute of ensemble runs justified by the honesty
gain, or is a well-calibrated confidence flag sufficient (this resolves the question `M03`/`M04` defer
here); (3) the **provenance schema** recommendation — what columns/flags every imputed field must carry
to satisfy the non-negotiable provenance rule, generalizing the existing convention; (4) an explicit
statement of how validating (not tuning) the imputer keeps it inside the zero-fitted-parameters rule.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C protocol.
3. Cite an evaluation-methods source and, separately, any UBEM downstream-impact study.
4. **"Confidence and caveats":** which recommendation rests on the least building-specific evidence.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **The downstream-EUI-impact check is mandatory in the recommended protocol** — input-reconstruction
  accuracy alone is an incomplete validation for UBEM.
- **Resolve single vs. multiple imputation** for OpenUBEM with a clear recommendation.
- **Specify the provenance schema** concretely enough to implement.
- **Tie the whole protocol back to zero-fitted-parameters** (validate, never tune).
- **No fabricated precision;** flag GAPs. **Stay on topic** — evaluation & uncertainty only, not
  algorithm ranking or module engineering.
