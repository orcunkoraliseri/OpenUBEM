# Deep-Research Prompt M04 — CLASSICAL ML IMPUTATION (the basic-ML tier)

> SCOPE GUARD — READ FIRST. This is the **basic-ML tier** of the imputation feature. Cover only
> *classical (non-neural) machine-learning* imputers: MissForest / random-forest imputation, gradient
> boosting (XGBoost/LightGBM/CatBoost) as an imputer, kNN-regression, decision-tree and matrix-
> factorization imputation. Do NOT cover simple statistics (that's `M03`), neural/generative methods
> (`M05`), spatial/graph methods (`M06`), or foundation models (`M10`). See
> `00_README_imputation_prompt_set.md` for shared facts.

---

## What this document is

An appraisal of classical-ML imputers for OpenUBEM building attributes. These methods learn a predictor
for each incomplete field from the *complete-case* subset of the same building table (plus any joined
features), then predict the gaps. The manager needs to know: which of them are documented to work on
building-stock attributes, what feature sets they use, how much complete-case training data they need,
and — critically — whether they can be operated inside the zero-fitted-parameters + provenance
constraints (an ML model *is* a fitted object; the constraint is about not tuning it against validation
EUI, not about avoiding fitting per se — clarify this boundary).

## Role

Applied-ML analyst for tabular / geospatial building data. Ground each method in its methods source
(Stekhoven & Bühlmann 2012 for MissForest; the XGBoost/LightGBM papers; `sklearn` `IterativeImputer`
with tree estimators) **and** any documented building-attribute imputation study (height, vintage,
floor area, use-type prediction from footprint morphology + context).

## Why this matters (so you scope correctly)

Classical ML is the tier most likely to beat basic statistics *when there is a usable complete-case
subset and informative predictors* (footprint geometry, neighbours, morphology). But it introduces
model-management burden (training, versioning, leakage control) and a subtler zero-fitted-parameters
question: is a random forest trained on the city's own complete buildings a "published convention" or a
"tuned knob"? This prompt must give the manager both the accuracy evidence and a clear read on whether
this tier is admissible under OpenUBEM's constraints.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Classical-ML imputer catalogue

| Method | How it imputes | Data needed (complete-case fraction, # features) | Native uncertainty output? | Reference impl | Source |
|---|---|---|---|---|---|
| MissForest (RF) |  |  |  | `missingpy`, R `missForest` |  |
| Gradient boosting (XGBoost/LightGBM) |  |  |  | `xgboost`, `IterativeImputer` |  |
| kNN-regression imputation |  |  |  | `sklearn` |  |
| Decision-tree imputation |  |  |  |  |  |
| Matrix factorization / SoftImpute |  |  |  | `fancyimpute` |  |

### Table 2 — Documented building-attribute ML imputation

| Study | Attribute predicted | Feature set used (geometry, context, joined data) | Reported accuracy / error | Complete-case training size | Source |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Table 3 — Predictive features available *in OpenUBEM* for each target

What OpenUBEM actually has to predict each gap — the feasibility check.

| Target to impute | Predictors available in OpenUBEM (footprint_area, perimeter, form_factor, aspect_ratio, neighbours, use_class, climate_zone…) | Enough signal for classical ML? (author's judgement + evidence) | Source |
|---|---|---|---|
| `levels` / `height` |  |  |  |
| `year_built` |  |  |  |
| `use_class` / archetype |  |  |  |

### Table 4 — Constraint fit

| Method | Is it "published convention" or "target-tuned knob"? (zero-fitted-params reading) | How it emits provenance/confidence (predicted-value + model-confidence) | Leakage risk (train/apply discipline) | Verdict (adopt / conditional / skip) | Source |
|---|---|---|---|---|---|
| MissForest |  |  |  |  |  |
| Gradient boosting |  |  |  |  |  |
| kNN-regression |  |  |  |  |  |

---

## Part C — Synthesis (the basic-ML verdict)

Give: (1) whether classical ML is **worth the model-management burden over the `M03` statistical tier**
for OpenUBEM's low-dimensional building tables — and for *which* specific inputs the accuracy gain
justifies it; (2) a clear ruling on the **zero-fitted-parameters question** — under what discipline
(fit on complete-case only, never touch validation cities, freeze the model) a trained imputer stays
admissible, or a statement that it cannot; (3) the recommended single method if this tier is adopted,
with its provenance/confidence emission design; (4) the minimum complete-case data volume below which
this tier is not viable and OpenUBEM should stay in `M03`.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C basic-ML verdict.
3. Cite methods source and building-application source separately.
4. **"Confidence and caveats":** the weakest evidence in the accuracy claims (Table 2).
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Answer the zero-fitted-parameters admissibility question explicitly** — this is the load-bearing
  decision for whether OpenUBEM can use any trained model at all.
- **State training-data requirements** for every method — the manager needs the viability floor.
- **Describe the provenance/confidence output** each method can emit — no method that fails this passes.
- **No fabricated precision;** flag GAPs. **Stay on topic** — classical ML only, no neural/deep methods.
