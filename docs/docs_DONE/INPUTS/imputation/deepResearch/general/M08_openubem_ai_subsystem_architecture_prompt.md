# Deep-Research Prompt M08 — "OpenUBEM AI" SUBSYSTEM ARCHITECTURE (how to package imputation as a real module)

> SCOPE GUARD — READ FIRST. This is the **engineering/architecture** prompt for the "OpenUBEM AI"
> feature — how imputation is *packaged*, not which algorithm it runs (algorithms are `M03`–`M06`,
> `M10`). Answer: how mature open-source data/ML tools structure a reusable imputation subsystem —
> pipeline placement, fit-on-train/apply-at-inference discipline, leakage prevention, model persistence/
> versioning, the config surface, and (load-bearing for OpenUBEM) **provenance/confidence emission**.
> Do NOT rank imputation algorithms here. See `00_README_imputation_prompt_set.md`.

---

## What this document is

A design-pattern survey. OpenUBEM's report (`../REPORT_missing_input_handling.md`) found that missing-
data handling is scattered across stages with no shared module, and that the newest sites (HVAC/DHW)
regressed to *silent* defaults with no provenance. The user wants a coherent "OpenUBEM AI" subsystem
that centralizes prediction of missing parameters. This prompt asks how the ecosystem's reference
implementations (`scikit-learn` imputers + `Pipeline`, `miceforest`, `autoimpute`, R `mice`/`recipes`,
`feature-engine`, `missingno` for diagnosis) structure this, so the manager can design an
OpenUBEM-native module that fits the existing provenance-flag convention rather than inventing one.

## Role

ML-systems / data-pipeline architecture analyst. Ground every pattern in a real library's documented
API and design (cite the specific class/guide: `sklearn.impute` + `ColumnTransformer`/`Pipeline` +
`set_output`; `miceforest.ImputationKernel`; `autoimpute`; R `recipes::step_impute_*`). Focus on the
*engineering contract*, not the statistics.

## Why this matters (so you scope correctly)

The algorithm choice is reversible; the subsystem's contract is not. If the module bakes in leakage
(fitting imputation statistics on the whole dataset including validation cities), silent substitution
(the HVAC/DHW regression), or unversioned models (irreproducible runs), every downstream result inherits
those flaws no matter how good the algorithm. This prompt defines the interface OpenUBEM must hit:
train/apply separation, deterministic replay, a single queryable provenance surface, and a config that
lets a user pick a tier per input without editing code.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Reference imputation-subsystem designs

| Library / framework | Pipeline-placement model (fit/transform contract) | How it prevents train→test leakage | Model persistence / versioning story | Provenance: does it mark *which* values were imputed? | Source |
|---|---|---|---|---|---|
| `scikit-learn` (`impute` + `Pipeline`) |  |  |  |  |  |
| `miceforest` |  |  |  |  |  |
| `autoimpute` |  |  |  |  |  |
| R `mice` / `recipes` |  |  |  |  |  |
| `feature-engine` / other |  |  |  |  |  |

### Table 2 — The provenance/confidence emission pattern

OpenUBEM's non-negotiable requirement — how do others expose it?

| Approach | How imputed-vs-observed is exposed (mask matrix, indicator column, metadata) | Confidence/uncertainty attached? | Fits OpenUBEM's flag-token convention (`KDE_IMPUTED`, `HEURISTIC_HEIGHT`, confidence HIGH/MED/LOW)? | Source |
|---|---|---|---|---|
| `MissingIndicator` / add-indicator |  |  |  |  |
| Multiple-imputation replicate sets |  |  |  |  |
| Custom provenance column |  |  |  |  |

### Table 3 — Config & tier-selection surface

| Concern | How reference tools let the user choose method-per-column / tier | Recommended OpenUBEM surface (config file, per-input routing) | Source |
|---|---|---|---|
| Per-column method selection |  |  |  |
| Fallback chaining (fuse → stats → ML) |  |  |  |
| Turning imputation off (strict mode) |  |  |  |

### Table 4 — Anti-patterns to design out (OpenUBEM already exhibits some)

| Anti-pattern | Why it's harmful | Does OpenUBEM currently exhibit it? | Design that avoids it | Source |
|---|---|---|---|---|
| Silent substitution (no provenance) | Untraceable results | **Yes** — `idf/hvac.py`, `idf/dhw.py` `.get() or default` |  |  |
| Fit statistics on full dataset (leakage) | Optimistic bias |  |  |  |
| `.get(key) or default` (falsy≠missing) | Overwrites valid `0` | **Yes** — report §3.2 |  |  |
| Unversioned/irreproducible imputer | Non-replayable runs |  |  |  |

---

## Part C — Synthesis (the subsystem contract)

Give: (1) a recommended **module contract** for OpenUBEM AI — the fit/apply separation, where it sits in
the 5-stage pipeline (before archetype assignment? after?), and how it chains fusion (`M07`) → statistical
(`M03`) → ML (`M04+`) fallbacks per input; (2) the **provenance design** that generalizes the existing
flag-token + confidence convention to every imputed field, closing the Tier-B gap the report flagged;
(3) the **leakage-prevention rule** binding for the zero-fitted-parameters posture (never fit on
validation cities; fit-on-complete-case-only); (4) a **config surface** sketch letting a user pick a tier
per input and a strict "impute-nothing, hard-fail" mode for auditing. Keep it a contract, not code.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C subsystem contract.
3. Cite the specific library class/guide for every pattern.
4. **"Confidence and caveats":** which pattern is least standardized across tools.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **The provenance/confidence contract is the centrepiece** — a design that can't say which buildings
  were imputed fails, regardless of algorithm.
- **Explicitly design out the two anti-patterns OpenUBEM already has** (silent HVAC/DHW defaults; `or`
  vs. `get(default)`).
- **State the pipeline-placement decision** relative to archetype assignment.
- **No fabricated precision;** flag GAPs. **Stay on topic** — subsystem engineering only, not algorithm
  ranking (`M03`–`M06`, `M10`).
