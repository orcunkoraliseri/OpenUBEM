# Deep-Research Prompt M05 — DEEP / GENERATIVE IMPUTATION (the advanced-model tier, neural)

> SCOPE GUARD — READ FIRST. This is the **advanced (neural/generative) tier**. Cover deep-learning
> imputers that learn on your own data: GAIN (GAN-based), VAE / denoising autoencoders, diffusion models
> for tabular data, and tabular transformers (TabTransformer, FT-Transformer) used as imputers. Do NOT
> cover classical ML trees/boosting (that's `M04`), spatial/graph methods (`M06`), or *pretrained
> foundation models / LLMs* (that's `M10` — the distinction is training paradigm: this prompt is
> train-on-your-own-table, `M10` is pretrained/zero-shot). See `00_README_imputation_prompt_set.md`.

---

## What this document is

A sober appraisal of whether deep generative imputation is warranted for OpenUBEM's data, and if so
which method. These techniques are the state of the art on large, high-dimensional, richly-correlated
tables — but UBEM building tables are typically small, low-dimensional, and heterogeneous, exactly the
regime where deep methods are hardest to justify. The manager needs the evidence to decide whether this
tier is a real capability worth the reproducibility and data cost, or a research-frontier line to
document but not ship.

## Role

Deep-learning-for-tabular-data research analyst. Ground every method in its primary paper (Yoon,
Jordon & van der Schaar 2018 for GAIN; the VAE/DAE imputation literature; recent tabular-diffusion
imputation papers; Gorishniy et al. / Huang et al. for tabular transformers) and in any *building /
energy* application. Be explicit where a method has **no** documented building-attribute use (most will
not) — that is itself a finding.

## Why this matters (so you scope correctly)

Deep imputers carry three costs OpenUBEM cares about: (1) they need substantial training data, often more
than a single city's complete-case subset provides; (2) they are stochastic and hard to reproduce
bit-for-bit, straining the zero-fitted-parameters/auditability posture; (3) their "confidence" is not
naturally calibrated, complicating the mandatory provenance requirement. This prompt must weigh those
costs against any accuracy gain over `M03`/`M04`, on data of OpenUBEM's actual size — not on the large
benchmarks these methods were designed for.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Deep/generative imputer catalogue

| Method | Mechanism | Min. practical training size | Reproducibility (deterministic given seed?) | Native calibrated uncertainty? | Source |
|---|---|---|---|---|---|
| GAIN (GAN) |  |  |  |  |  |
| VAE imputation |  |  |  |  |  |
| Denoising autoencoder |  |  |  |  |  |
| Tabular diffusion |  |  |  |  |  |
| Tabular transformer (FT/TabTransformer) |  |  |  |  |  |

### Table 2 — Documented building / energy applications (if any)

| Method | Building/energy task it was applied to | Reported result | Dataset size | Source |
|---|---|---|---|---|
|  |  |  |  |  |

### Table 3 — Head-to-head vs. simpler tiers, on small/low-dim tabular data

The decisive comparison: do deep methods actually beat MissForest/MICE when n is small?

| Benchmark study | Deep method(s) tested | Beat MissForest/MICE? | At what dataset size did the advantage appear/vanish? | Source |
|---|---|---|---|---|
|  |  |  |  |  |

### Table 4 — Constraint & operability fit

| Method | Zero-fitted-params posture (reproducible + not target-tuned?) | Provenance/confidence emission story | Data-viability floor for OpenUBEM (single city vs. multi-city corpus) | Verdict (ship / frontier-only / skip) | Source |
|---|---|---|---|---|---|
| GAIN |  |  |  |  |  |
| VAE / DAE |  |  |  |  |  |
| Diffusion |  |  |  |  |  |
| Tabular transformer |  |  |  |  |  |

---

## Part C — Synthesis (frontier verdict)

Give: (1) an evidence-based ruling on whether **any** deep generative imputer is justified for
OpenUBEM's data scale today, or whether this tier should be documented-but-deferred; (2) if one is worth
prototyping, the single most-defensible choice and the data corpus it would require (e.g. pooled
multi-city complete-case set); (3) the reproducibility + provenance design that would make it
admissible, or a clear statement that it cannot meet the constraints; (4) the specific dataset-size
threshold from Table 3 below which OpenUBEM should not attempt this tier and should stay in `M04`/`M03`.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C frontier verdict.
3. Cite the primary method paper for every claim; label any building application vs. generic benchmark.
4. **"Confidence and caveats":** be explicit that most rows may have NO building-specific evidence.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **State the small-n behaviour** of every method — OpenUBEM's data is small; large-benchmark wins do
  not transfer automatically.
- **Address reproducibility and calibrated-uncertainty explicitly** — both are constraint-critical.
- **Do not oversell.** If the honest answer is "not justified at OpenUBEM's scale," say so plainly.
- **No fabricated precision;** flag GAPs. **Stay on topic** — train-on-your-own neural methods only, not
  pretrained foundation models (`M10`) or spatial/graph methods (`M06`).
