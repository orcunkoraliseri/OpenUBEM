# Input Imputation — Deep-Research Prompt Set (INDEX)

> READ FIRST. This set is about the step that decides **what OpenUBEM does when an input it needs is
> absent** — not which archetype a building becomes (that is the sibling `input-framework/` set,
> `I01`–`I03`), but how a *missing* level count, `year_built`, U-value, COP, or footprint gets filled
> so the pipeline can still run. The current behaviour was inventoried by the manager in
> `../REPORT_missing_input_handling.md`: there is **no centralized imputation module** — every stage
> handles missingness ad hoc, in three maturity tiers (A = tracked fallback, B = silent default,
> C = hard fail). The user wants to add a real, data-driven imputation capability with four escalating
> tiers — **basic statistics → OpenUBEM-AI prediction → basic ML → advanced models** — so this set asks
> how the UBEM/BEM literature and peer tools actually impute missing building inputs, with sources, so
> the manager can write a defensible implementation plan. Run each prompt in your deep-research tool;
> save the answer beside it as `RESULT_<id>_<slug>.md`. The manager audits each RESULT and only then
> drafts `PLAN_input_imputation_implementation.md`.

---

## The exact decision this set must inform

OpenUBEM's inputs (`docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md`, 19 categories) split into two
groups for the purpose of imputation:

- **Runtime-fetched, patchy by nature** — OSM `building:levels`, `height`, `start_date` (`year_built`),
  `building`/`amenity`/`shop`/`office` tags. These are volunteer-contributed and *routinely* absent;
  this is where imputation earns its keep.
- **Bundled, gap-free by construction** — the 90.1-2019 construction table, DOE-prototype loads/
  schedules, HVAC/DHW/cooking/refrigeration intensities. These only go "missing" for a *building* when
  its archetype or (archetype, climate-zone) key can't be resolved, or when a user supplies a custom
  table with holes.

The user's four requested feature tiers map onto this set as follows:

| User's requested tier | Primary prompt(s) | What it must decide |
|---|---|---|
| **Basic statistical tools/methods** | `M03` | mean/median/mode, group-wise/stratified defaults, regression, hot-deck, kNN, MICE, KDE-sampling |
| **OpenUBEM AI — prediction of missing parameters** | `M08` (subsystem) + `M10` (foundation/LLM) | how imputation is packaged as a reusable, leakage-safe, provenance-emitting module; the "AI" frontier |
| **Basic ML models** | `M04` | MissForest/random-forest, gradient boosting, kNN-regression, decision trees |
| **Advanced models** | `M05` (generative/deep) + `M06` (spatial/GNN) | GAIN, VAE/DAE, diffusion, tabular transformers; spatial-context & graph methods |

The three cross-cutting prompts (`M01` landscape, `M02` peer-tool practice, `M07` external-data fusion,
`M09` uncertainty/validation) frame and constrain all four tiers.

---

## The prompts

| # | File | What it learns | Priority |
|---|------|----------------|----------|
| M01 | `M01_missing_data_landscape_prompt.md` | The full solution space: what UBEM inputs go missing at scale, the MCAR/MAR/MNAR mechanisms behind each, and the remedy taxonomy (drop / default / impute / fuse). Scopes every downstream prompt. | **core** |
| M02 | `M02_peer_ubem_tool_attribute_imputation_prompt.md` | Tool-by-tool: how UMI, CEA, CityBES, AutoBEM, TEASER/GEM, 3DCityDB, URBANopt fill missing height/levels/use/vintage/area. The "what do others actually do" anchor. | **core** |
| M03 | `M03_basic_statistical_imputation_prompt.md` | Basic-statistics tier: which classical statistical imputers are used for building attributes, their assumptions, and how OpenUBEM's existing KDE/`pd.cut` fills compare. | **core** |
| M04 | `M04_classical_ml_imputation_prompt.md` | Basic-ML tier: MissForest/RF, gradient boosting, kNN-regression for building-attribute imputation — feature sets, reported accuracy, training-data needs. | high |
| M05 | `M05_deep_generative_imputation_prompt.md` | Advanced tier (neural/generative): GAIN, VAE/denoising-autoencoder, diffusion, tabular transformers — when they beat classical ML and their data/repro cost. | medium |
| M06 | `M06_spatial_context_gnn_imputation_prompt.md` | Advanced tier (spatial): kriging, spatial regression, neighbor-voting, and graph neural nets over building-adjacency graphs — exploiting the fact that neighbours correlate. | medium |
| M07 | `M07_external_data_fusion_prompt.md` | Fetch-the-truth alternative to guessing: Google/MS Open Buildings, EUBUCCO, GHSL, Overture, LiDAR/DSM, assessor/registry — coverage, licence, accuracy vs. OSM. | high |
| M08 | `M08_openubem_ai_subsystem_architecture_prompt.md` | "OpenUBEM AI" as a product: how mature open-source tools package imputation as a reusable, fit-on-train/apply-at-inference, leakage-safe, provenance-emitting module. | high |
| M09 | `M09_uncertainty_provenance_validation_prompt.md` | How to *evaluate* imputation (mask-and-recover, downstream-EUI impact) and *carry uncertainty forward* (multiple imputation, confidence flags) — closes the zero-fitted-params + provenance loop. | **core** |
| M10 | `M10_foundation_model_llm_imputation_prompt.md` | The emerging "AI" frontier: TabPFN and other pretrained tabular foundation models, and LLM-prompted / retrieval-augmented attribute prediction — capability, and the hallucination/provenance risk. | low |

> **Load-bearing core: `M01 + M02 + M03 + M09`.** These four decide whether OpenUBEM ships a modest,
> defensible statistical imputer first (the safe MVP) before investing in the ML/advanced tiers. Run
> them first; run `M04`/`M07`/`M08` next if the MVP proves worth extending; treat `M05`/`M06`/`M10` as
> the research-frontier tier, run only if the advanced-model track is greenlit.

---

## Shared facts (all prompts assume these)

Pulled from `../REPORT_missing_input_handling.md` and `docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md`.
Every prompt pre-fills its own OpenUBEM-current row from this list — do not re-derive it.

- **No centralized imputation today.** Missing-data handling is per-stage and ad hoc, in three tiers:
  **A — tracked** (fallback value + a provenance/confidence marker records it happened),
  **B — silent default** (value substituted, nothing recorded),
  **C — hard fail** (missing input raises rather than guessing). The split roughly tracks how
  consequential a wrong guess would be.
- **OpenUBEM already imputes in four places (all Tier-A, all statistical/heuristic):**
  1. **Levels from height** — `max(1, int(height_m // 3.5))`, flag `HEURISTIC_HEIGHT`; both absent → `1`,
     flag `HEURISTIC_DEFAULT` (`semantic/building_classifier.py:121-127`).
  2. **`year_built` NaN → oldest vintage** — `pd.cut(..., right=False)` bins NaN → `DOERefPre1980`
     (U-factors ×1.6), flag `VINTAGE_NAN_PERMISSIVE_DEFAULT` (`semantic/construction_sets.py:44,129-139`).
  3. **Construction (archetype, climate-zone) gap → KDE-fill** from sibling climate zones, same
     archetype, flag `KDE_IMPUTED` (`semantic/construction_sets.py:171-219`) — the one existing
     *distribution-based* imputer, and the closest precedent for the new feature.
  4. **Unresolved use-class → `OpenUBEMUnknown`** (LOW confidence) or size-bucketed office default
     (`FALLBACK_SIZE_DEFAULT`); climate-zone point-miss → nearest-county join ≤ 5 km
     (`nearest_fallback`, HEURISTIC).
- **The silent-default (Tier-B) weak spot** the feature should also address: HVAC `cop`/fan/efficiency
  defaults and DHW/cooking `footprint_area_m2 → 400 m²` / `num_floors → 1` are substituted with **no
  provenance marker** via the `dict.get(key) or default` pattern (`idf/hvac.py`, `idf/dhw.py`,
  `idf/cooking.py`). Any new imputer must emit provenance to avoid widening this gap.
- **OpenUBEM's own prior art** is in-repo: İşeri et al., *A Method for Zone-level UBEM in Data-scarce
  Built Environments* (`../resources/…docx.md`) — a probabilistic, **density-estimation (KDE)**-based
  imputation/generation method with explicit missing-data-mechanism analysis, four UBEM granularity
  tiers, and a Bahçelievler/Ankara case study. The new feature is the productionization of that method;
  every prompt should check whether peer practice supports or contradicts the paper's KDE-first stance.
- **Zero-fitted-parameters constraint applies here too.** Any recommended imputation method, default, or
  hyperparameter must be a published convention or documented precedent, not a knob tuned to make a
  particular validation EUI look better. An imputer that is itself calibrated against the validation
  targets would violate this — flag any method that requires it.
- **Provenance is non-negotiable.** Every imputed value must leave a queryable marker (a flag token +
  confidence downgrade), matching the Tier-A convention already used for the four imputers above. A
  method that cannot report *which* buildings it touched is unacceptable regardless of accuracy.

## Peer-tool / source roster (use across prompts where relevant)

UMI (Dogan & Reinhart) · City Energy Analyst / CEA (Fonseca et al.) · CityBES (Hong et al.) ·
AutoBEM (New et al., ORNL) · URBANopt/OpenStudio (NREL) · TEASER / GEM (RWTH) · 3DCityDB / CityGML ·
plus the missing-data-methods literature (van Buuren *Flexible Imputation of Missing Data*; MICE;
MissForest — Stekhoven & Bühlmann; GAIN — Yoon et al.; TabPFN — Hollmann et al.) and the building-stock
imputation literature (the İşeri, Wang, Nägeli, Mastrucci, Kristensen, Cerezo/Sokol references catalogued
in the in-repo paper's bibliography).

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; prose after. Empty / "TBD" cells are failures.
2. Every method/value carries a **named, dated source** — a peer-reviewed UBEM or missing-data-methods
   paper (author, venue, year), tool documentation, or a library's official docs. Blogs/vendor pages
   last resort, labelled.
3. **Always compare against OpenUBEM's actual current behaviour** (given inline in each prompt from the
   Shared facts above) — say explicitly whether peer practice matches, is more rigorous, or is looser.
4. **No fabricated precision.** If a value is your synthesis, say so. If unpublished, write **"GAP —
   needs manager decision"** + the closest defensible default and its source.
5. **Map onto OpenUBEM's exact inputs and vocabulary** (the 19 input categories; `levels`, `year_built`,
   `use_class`, `cooling_cop`, `footprint_area_m2`, the A/B/C tiers, the provenance-flag convention),
   not generic "missing data" in the abstract.
6. **Respect the two hard constraints** in every recommendation: zero-fitted-parameters, and
   mandatory provenance emission. A method that violates either is a non-starter — say so.
7. **Stay on topic per prompt** — do not re-litigate archetype classification (that's the
   `input-framework/` `I0x` set) or geometry/zoning resolution (that's the `layoutMapping` set).

---

*OpenUBEM — input imputation deep-research set. Markdown only; binding specs remain `docs/docs_main/`.
Grounded in `../REPORT_missing_input_handling.md`, the 19-category inputs reference, and the in-repo
İşeri et al. data-scarce-UBEM paper. 2026-07-01.*
