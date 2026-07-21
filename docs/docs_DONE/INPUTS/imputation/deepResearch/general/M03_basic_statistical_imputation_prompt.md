# Deep-Research Prompt M03 — BASIC STATISTICAL IMPUTATION (the safe-MVP tier)

> SCOPE GUARD — READ FIRST. This is the **basic-statistics tier** of the imputation feature — the
> first, safest capability OpenUBEM would ship. Cover only *classical statistical* imputers: constant/
> group-wise mean-median-mode, regression imputation, hot-deck/cold-deck, kNN imputation, multiple
> imputation (MICE family), and distribution sampling (KDE / parametric). Do NOT cover tree/forest or
> gradient-boosting ML (that's `M04`), neural/generative methods (`M05`), spatial/graph methods
> (`M06`), or foundation models (`M10`). See `00_README_imputation_prompt_set.md` for shared facts.

---

## What this document is

A method-by-method appraisal of the statistical imputers OpenUBEM could adopt for building attributes,
benchmarked against what it already does. OpenUBEM's existing imputation is *entirely* in this tier —
KDE sampling for construction, deterministic defaults for vintage/height — so this prompt establishes
whether the current choices are the field's basic-tier norm and which additional statistical methods are
worth adding before any ML is considered. The in-repo İşeri et al. paper is itself a basic-to-
intermediate-tier method (density estimation); this prompt situates it among alternatives.

## Role

Statistical missing-data-methods analyst with a building-stock focus. Ground each method in the
canonical source (van Buuren, *Flexible Imputation of Missing Data*, for MICE; Little & Rubin for
theory; Andridge & Little for hot-deck; the `scikit-learn` / R `mice` / `VIM` docs for the reference
implementations) **and** in at least one documented building-attribute application where available.

## Why this matters (so you scope correctly)

Basic statistical imputers are the tier that satisfies the zero-fitted-parameters and provenance
constraints most easily — they are transparent, cheap, and their assumptions are explicit. If the field
shows that a well-chosen group-wise/stratified or MICE approach recovers building attributes about as
well as heavier ML on the modest, low-dimensional tables UBEM works with, OpenUBEM should ship this tier
first and treat ML as an optional upgrade. This prompt must give the manager the evidence to make that
"is basic enough?" call.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Statistical imputer catalogue

| Method | Core assumption (mechanism it's valid under) | Best-suited OpenUBEM input(s) | Handles uncertainty? (single vs. multiple) | Reference impl | Source |
|---|---|---|---|---|---|
| Constant / archetype default |  | vintage, COP |  | — |  |
| Group-wise mean / median / mode (stratified) |  | levels, area |  | `sklearn SimpleImputer` |  |
| Regression imputation |  | height↔area, levels |  | `sklearn` |  |
| Stochastic regression imputation |  |  |  |  |  |
| Hot-deck / cold-deck (donor) |  | use, vintage |  | R `VIM` |  |
| kNN imputation |  | mixed |  | `sklearn KNNImputer` |  |
| MICE / multiple imputation |  | multivariate |  | R `mice`, `sklearn IterativeImputer` |  |
| KDE / distribution sampling |  | U-value, loads |  | (custom) |  |
| EM algorithm |  |  |  |  |  |

### Table 2 — Reported performance on building / stock attributes

Only rows where a study actually measured a statistical imputer on building-attribute data.

| Method | Attribute imputed (height, vintage, area, use, energy) | Reported error metric + value | Dataset / study | Source |
|---|---|---|---|---|
|  |  |  |  |  |

### Table 3 — Fit to OpenUBEM's two hard constraints

| Method | Satisfies zero-fitted-parameters? (transparent, no target-tuned knobs) | Naturally emits provenance/confidence? | Verdict for OpenUBEM basic tier (adopt / skip / conditional) | Source |
|---|---|---|---|---|
| Group-wise statistic |  |  |  |  |
| Regression imputation |  |  |  |  |
| Hot-deck |  |  |  |  |
| kNN |  |  |  |  |
| MICE |  |  |  |  |
| KDE sampling |  |  |  |  |

### Table 4 — OpenUBEM's current statistical fills vs. best-in-tier

| OpenUBEM current fill | Method class | Is there a strictly-better basic-tier method for that input? | Recommended change (or "keep") | Source |
|---|---|---|---|---|
| `year_built` NaN → oldest vintage | Constant default |  |  |  |
| `levels` ← `height // 3.5`, else `1` | Deterministic heuristic |  |  |  |
| Construction gap → KDE from sibling CZ | KDE sampling |  |  |  |
| DHW/cooking `area → 400`, `floors → 1` | Constant default (silent) |  |  |  |

---

## Part C — Synthesis (the MVP recommendation)

Give: (1) a ranked shortlist of **the 2–3 statistical methods OpenUBEM should ship as its basic tier**,
each with the inputs it should handle and its provenance story; (2) an explicit call on **single vs.
multiple imputation** — is MICE-style multiple imputation worth the added complexity for UBEM, or is
single imputation with a confidence flag adequate (this decision feeds `M09`); (3) a verdict on whether
KDE-sampling (OpenUBEM's existing envelope method, and the İşeri paper's core) should be **generalized**
to other inputs or is envelope-specific; (4) which current OpenUBEM fill (Table 4) is the weakest and
what basic-tier method replaces it.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C MVP recommendation.
3. Cite the methods source and, separately, any building-application source.
4. **"Confidence and caveats":** which method's suitability for UBEM data is least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every method must state the missing-data mechanism it is valid under** (cross-refs `M01`).
- **Explicitly judge single vs. multiple imputation** for the UBEM use case.
- **Respect the two hard constraints** — flag any method that needs target-tuned parameters or cannot
  emit provenance.
- **No fabricated precision;** flag GAPs. **Stay on topic** — classical statistics only, no ML/neural.
