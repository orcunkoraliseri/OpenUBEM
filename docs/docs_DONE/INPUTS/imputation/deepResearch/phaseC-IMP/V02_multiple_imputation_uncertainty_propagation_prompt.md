# Deep-Research Prompt V02 — MULTIPLE IMPUTATION & UNCERTAINTY PROPAGATION

> SCOPE GUARD — READ FIRST. This prompt covers **multiple imputation (MI)** — drawing M completed
> datasets instead of one — and how the resulting uncertainty is **propagated through** a UBEM pipeline
> into an EUI ensemble (Rubin's rules, congeniality, MI for spatial/clustered data). It asks whether MI
> is worth its M× cost for OpenUBEM, or whether single stochastic imputation (`V01`) + a confidence flag
> is adequate for the aggregate-EUI purpose. **Do NOT re-catalogue single-draw methods** (that's `V01`),
> **evaluation metrics** (`V03`), or **neural/generative samplers** (`V04`). See
> `V00_README_variance_preserving_prompt_set.md` for shared facts.

---

## What this document is

A decision brief on whether OpenUBEM should move from single imputation to **multiple imputation** for
its missing inputs, and if so, how the M draws flow through Stage-3 (IDF) → Stage-5 (EnergyPlus) →
results without violating zero-fitted-parameters or exploding the simulation budget. The output must let
the manager rule: single stochastic draw + confidence flag (cheap, opt-in `draw` tier as planned) vs a
full MI ensemble (M× simulations, a much larger commitment).

## Role

Multiple-imputation methodologist (van Buuren; Little & Rubin; Rubin 1987) with an applied-simulation /
uncertainty-quantification lens. Ground every claim in the canonical MI literature **and**, where it
exists, in a building-stock or spatial-model application that actually ran an MI ensemble downstream.

## Why this matters (so you scope correctly)

Single stochastic imputation restores the *marginal* spread but gives one answer per building; it does
not tell you how much of the final EUI uncertainty is *due to* the imputation. MI does — but at the cost
of M complete datasets and (naively) M× EnergyPlus runs, which collides with OpenUBEM's cluster-budget
discipline. The manager needs to know exactly what MI buys, whether Rubin's rules even apply to a
deterministic physics simulator (congeniality/uncongeniality), and whether a cheaper surrogate (M draws
through a fast EUI emulator, or MI only on the geometry/vintage inputs) captures most of the value.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — MI method families

| MI approach | How the M draws are generated | Assumptions (mechanism, congeniality) | Small-n / low-dim suitability | Reference impl | Source |
|---|---|---|---|---|---|
| Joint modelling (MVN) |  |  |  | R `Amelia`, `norm` |  |
| Fully conditional specification / MICE |  |  |  | R `mice`, `sklearn IterativeImputer` |  |
| PMM within MICE |  |  |  | R `mice` |  |
| Bootstrap-based MI (bootstrap + single impute) |  |  |  | custom |  |
| Approximate Bayesian bootstrap MI |  |  |  | custom |  |
| MI for spatial / clustered data |  |  |  | R `mice` (2l), `jomo` |  |

### Table 2 — Propagating M imputations through a deterministic UBEM

| Step | Standard MI recipe (Rubin's rules) | Does it hold for a deterministic EUI simulator? (congeniality note) | Cheaper surrogate that keeps most of the signal | Source |
|---|---|---|---|---|
| Pool point estimates (mean EUI) |  |  |  |  |
| Pool uncertainty (within + between variance) |  |  |  |  |
| Per-building EUI interval |  |  |  |  |
| Aggregate/fleet EUI interval |  |  |  |  |

### Table 3 — Cost vs value for OpenUBEM

| Option | Sim cost | What uncertainty it recovers | Fit to zero-fitted-params + provenance | Verdict for OpenUBEM | Source |
|---|---|---|---|---|---|
| Single stochastic draw + confidence flag (planned `draw` tier) | 1× | marginal spread only, no EUI CI |  |  |  |
| Full MI ensemble, M× EnergyPlus | M× |  |  |  |  |
| MI on inputs + fast EUI emulator/surrogate | ~1× + emulator |  |  |  |  |
| MI on high-impact inputs only (vintage/geometry) | <M× |  |  |  |  |

### Table 4 — Building-stock / UBEM precedents that used MI downstream

| Study / tool | Inputs imputed by MI | M value | How EUI/demand uncertainty was pooled | Reported finding | Source |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

---

## Part C — Synthesis (the single-vs-multiple ruling)

Give: (1) a crisp verdict — **should OpenUBEM ship single stochastic imputation (the planned opt-in
`draw` tier) or a multiple-imputation ensemble**, for its stated aggregate-EUI purpose plus the future
per-building-distribution use case; (2) if MI is worth it for *any* target, which one(s) and at what M,
and the **cheapest faithful propagation** (Rubin's rules vs a surrogate) given a deterministic simulator
and a constrained cluster budget; (3) the **congeniality caveat** stated plainly — is it even valid to
apply Rubin's rules to EnergyPlus outputs, and what breaks if not; (4) a recommended **provenance/CI
representation** — how M draws become a per-building confidence interval + a queryable flag without a
tuned parameter.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C ruling.
3. Cite MI-methods source and, separately, any downstream-application source.
4. **"Confidence and caveats":** where the MI-through-deterministic-simulator theory is weakest.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **State the congeniality / uncongeniality position explicitly** — do not hand-wave Rubin's rules onto
  a deterministic simulator without addressing it.
- **Quantify cost in simulation multiples** (M×), and always offer the cheapest surrogate.
- **Keep the aggregate-EUI purpose central** — OpenUBEM's headline is already unbiased; MI's value here
  is uncertainty *quantification* and per-building spread, not moving the mean.
- **Respect the two hard constraints;** flag violators. **No fabricated precision;** mark GAPs.
- **Stay on topic** — MI and propagation only; no single-draw catalogue, no metric definitions, no
  neural methods.
