# PLAN — Input-Parameter Imputation ("OpenUBEM AI") Implementation

**Slug:** `input-imputation-implementation`
**Date:** 2026-07-01
**Arc type:** ACTIVE feature arc (not a numbered pipeline step) — lives at
`docs/docs_ACTIVE/input/imputation/`.
**Binding contract:** OpenUBEM Stage-2.2 DESIGN §3E (imputation tier) —
`docs/docs_main/docs_step-2-2/DESIGN_step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and.md`
(§3E lines 116-140, §12 provenance vocabulary). Where this plan touches Stage-3 HVAC/DHW/cooking
emitters it is bound by the Stage-3 DESIGN. **This plan may not contradict either DESIGN; on any
conflict the executor STOPS and quotes it.**

**Grounding inputs (all read and audited by the manager session before this plan was written):**
- The nine deep-research RESULT reports `deepResearch/RESULT_M0{1..7,9}.md` + `RESULT_M10.md`
  (M08 was not run — its subsystem-architecture synthesis is folded directly into Phase B here).
- The manager-verified in-repo audit `REPORT_missing_input_handling.md`.
- The in-repo prior-art paper (İşeri et al., *A Method for Zone-level UBEM in Data-scarce Built
  Environments*), `resources/`.
- Live code: `openubem/semantic/{imputation,construction_sets,building_classifier}.py`,
  `openubem/idf/{hvac,dhw,cooking}.py`, `openubem/config.py`.

---

## 0. Status at a glance — monitoring checklist

> Single-glance tracker for this arc. Legend: `[x]` done/greenlit · `[~]` in progress · `[ ]` not started · `[!]` blocked/needs decision. Detail for every line lives in §6 (tasks), §7 (checkpoints), and §8 (progress log).
>
> **Last updated:** 2026-07-01 · **Current position:** **Phase A CLOSED — CP-1 CHECKPOINT MET.** Awaiting explicit user greenlight to open Phase B. Phases B–E dispatch nothing until then.

**Phase A — provenance-complete statistical MVP (user tier 1 + contract foundation) → CP-1**  ✅ **COMPLETE**
- [x] **T01** — canonical imputation provenance schema (`semantic/provenance.py`) — GREENLIT
- [x] **T02** — close HVAC Tier-B provenance gap (`idf/hvac.py`, delicate) — GREENLIT *(incl. wave-2a residual)*
- [x] **T03** — close DHW/cooking Tier-B gap (`idf/dhw.py`, `idf/cooking.py`, delicate) — GREENLIT *(incl. wave-2a residual)*
- [x] **T04** — `year_built` donor/neighbour vintage before oldest-default (`construction_sets.py`, PINNED CONTRACT v2) — GREENLIT
- [x] **T05** — group-wise stratified `levels` vs default-to-1 (`building_classifier.py`) — GREENLIT *(incl. wave-2b test cleanup)*
- [x] **T06** — spatial neighbour-fill utility + MNAR density filter (`semantic/spatial_impute.py`) — GREENLIT
- [x] **CP-1** — five gate suites 75/75 green · MNAR deactivation discharged · Tier-B EUI instrumentation-only CONFIRMED (25/25 IDFs byte-identical, exact local field-diff) — **MET**

**Phase B — "OpenUBEM AI" subsystem + validation harness (user tier 2) → CP-2 (LIVE_SMOKE; gates all data-driven work)**  ⛔ *awaiting user greenlight*
- [ ] **T07** — imputation routing subsystem + strict mode (`imputation.py`, `config.py`)
- [ ] **T08** — mask-and-recover + spatial-block hold-out harness (`validation/mask_recover.py`)
- [ ] **T09** — mandatory downstream-EUI impact check (`validation/eui_impact.py`)
- [ ] **T10** — optional uncertainty mode `--replicates M` (`config.py`, orchestrator)
- [ ] **CP-2** — routing/strict-mode + mask-and-recover green; T09 run once on a real fixture city (LIVE_SMOKE) with MBE/CV(RMSE) reported

**Phase C — classical-ML imputer (user tier 3) → CP-3**  ⛔ *gated on CP-2*
- [ ] **T11** — implement `build_ml_imputer` / §3E ML tier, MissForest (`imputation.py`)
- [ ] **CP-3** — ships only if it beats the Phase-A baseline on T08 mask-and-recover AND does not worsen the T09 EUI check

**Phase D — fusion-first external joins (research-driven) → CP-4**  ⛔ *gated / scoped*
- [ ] **T12** — external-data fusion precedence layer (Overture/LiDAR/assessor, runtime-fetch; expand to full tasks after CP-2)
- [ ] **CP-4** — LIVE_SMOKE join against a real external slice + license/bundle guard before any default run

**Phase E — advanced / data-driven frontier (user tier 4)**  📄 *documented-deferred*
- [ ] **T13** — frontier documentation (deep-generative/GNN/LLM out of scope) + optional isolated experimental TabPFN track (never default)

---

## 1. What this feature is (and what the research changed)

The user requested a four-tier imputation capability for OpenUBEM's **input parameters**:
1. Basic statistical tools/methods
2. "OpenUBEM AI" — a coherent prediction/imputation subsystem
3. Basic ML models
4. Advanced / all-data-driven models

The deep research produced a **clear, evidence-backed ranking** that this plan is built around, and
which overrides any temptation to build the fancy tiers first:

| User tier | Research verdict (internal source) | This plan | External literature cross-reference (independent validation) |
|---|---|---|---|
| 1 — Basic statistics | **Adopt now.** Hot-deck donor + group-wise stratified median + generalized KDE are the safe MVP; they already partly exist (`impute_column`). (M03 Part C) | **Phase A** — build out + close gaps | Andridge & Little 2010, *Int. Stat. Rev.* (hot-deck review); Lin & Tsai 2020 (imputation-method review) `[İşeri 33]`; Silverman 1986 / Sheather & Jones 1991 (KDE bandwidth) `[İşeri 59]` |
| 2 — "OpenUBEM AI" subsystem | **The centrepiece is the *provenance contract*, not the algorithm.** Centralize routing (fusion→stats→ML), fit-on-complete-case-only, strict mode, config surface. (M08 scope / M09 §3) | **Phase B** | van Buuren 2018, *Flexible Imputation of Missing Data* (2nd ed.); Little & Rubin 2019, *Statistical Analysis with Missing Data* (complete-case / no-leakage discipline) |
| 3 — Basic ML | **Adopt, gated.** MissForest/RF for `levels`/`height`/`use_class`/(conditionally)`year_built`, under strict attribute-only-fitting discipline + complete-case floors. Already stubbed as DESIGN F12 / Phase-2. (M04 Part C) | **Phase C** (gated on Phase B harness) | Stekhoven & Bühlmann 2012, *Bioinformatics* (MissForest); van Buuren & Groothuis-Oudshoorn 2011, *J. Stat. Softw.* (MICE); Pedregosa et al. 2011, *JMLR* (scikit-learn) |
| 4 — Advanced / data-driven | **Mostly defer or reject.** Deep-generative = frontier-only (needs n≥30k, multi-city corpus); GNN = reject (violates zero-fitted-params); LLM = **firm disqualification** (hallucination, no provenance); TabPFN = only frontier method that passes constraints but **NOT READY** (zero building-domain validation) → experimental track only. (M05/M06/M10 Part C) | **Phase E** (documented-deferred + optional isolated experimental track) | Grinsztajn et al. 2022, NeurIPS ("trees still beat deep learning on tabular data" — validates the defer); Yoon et al. 2018, ICML (GAIN); Hollmann et al. 2023 ICLR / 2025 *Nature* (TabPFN) |
| — External-data fusion (not a user tier, but the research's highest-value finding) | **Fetch the truth first.** Every gap fillable by a reliable external join (Overture / LiDAR / assessor) is a gap OpenUBEM should *not* be statistically imputing; sidesteps zero-fitted-params entirely. (M07 Part C) | **Phase D** (research-driven; larger runtime-fetch lift) | Milojević-Dupont et al. 2023, *Sci. Data* (EUBUCCO EU building stock); Sirko et al. 2021 (Google Open Buildings); Overture Maps Foundation 2024; Cerezo Davila et al. 2016 (Boston GIS-driven UBEM) `[İşeri 9]` |
| — Spatial neighbour context (not a user tier, but nearly free) | **Make it first-class.** Coordinates are already present; neighbour-fill materially beats aspatial for `year_built`/`use`/`levels`; use neighbour-voting + kNN, **not** GNN. Guard MNAR clusters. (M06 Part C) | folded into **Phase A** (T06) + reused by C/D | Moran 1950, *Biometrika* (spatial autocorrelation); Cressie 1993, *Statistics for Spatial Data* (kriging); Fotheringham et al. 2002 (Geographically Weighted Regression) |

**Prior art this plan already ships — the İşeri et al. foundational paper.** The existing
`impute_column` KDE/PDE tier is a direct implementation of this project's own method paper (İşeri et al.,
*A Method for Zone-level UBEM in Data-scarce Built Environments*, `resources/`). Reading it in full
confirms the "not greenfield" framing and hands us several load-bearing techniques the deep-research
reports independently echoed. The plan inherits them explicitly:

| Paper technique (İşeri et al.) | What it is | Where it lives / maps in this plan | External source (cross-ref) |
|---|---|---|---|
| **NPDE — non-parametric density estimation** (§3.1) | KDE on observed values for inputs with 0%<missing<100% (WWR, U-values, occupant density); Gaussian kernel, **Silverman's-rule bandwidth** (rule-based, *not* EUI-tuned), regenerate-until-within-[min,max] clamp | Already = `impute_column(method="kde")`; the Phase-A statistical tier. Silverman bandwidth is a **zero-fitted-params** choice — keep it, do not sweep it. | Silverman 1986 (*Density Estimation for Statistics & Data Analysis*); Sheather & Jones 1991 `[İşeri 59]`; Grossman & Linskens 1977 `[İşeri 58]` |
| **PDE — parametric density estimation** (§3.2, Tables 3–4) | Uniform/Normal within **literature-cited bounds** for 100%-missing inputs (SHGC 0.30–0.85, COP 0.8–0.95, infiltration ASHRAE 90.1, lighting/equipment/setpoint ranges) | Already = `impute_column(method="pde")` + `PDE_BOUNDS_PATH`. **These are exactly the inputs ML must NEVER touch** (T11 exclusion) — the paper fills them from standards, not from fitting. | ASHRAE 90.1-2013 `[İşeri 27]`; Anderson 2014 `[İşeri 62]`; bounds: Purup & Petersen 2020 `[63]`, Yang et al. 2016 `[64]`, Brohus et al. 2009 `[65]` |
| **Stratified density estimation** (§3.1: separate KDE for masonry n=784 vs concrete n=99) | Fit the donor distribution *within* a physically-meaningful stratum, not pooled | Evidence base for **group-wise stratified fills** — T04 (`year_built` by `use_class`/construction), T05 (`levels` by `use_class`). | Sokol et al. 2017 `[İşeri 36]`; Cerezo et al. 2015 `[47]`; Wang et al. 2020 (distributions by use/year) `[37]` |
| **Adjacent-neighbourhood pooling** (§3.1: borrow from Yukarı Bahçelievler & Emek to enlarge a thin sample) | Grow a thin donor pool with nearby areas of similar typology | Justifies **spatial donor pooling / hot-deck** — T06 neighbour-fill, T04 donor vintage. | Andridge & Little 2010 (hot-deck donor pools, *Int. Stat. Rev.*); İşeri et al. §3.1 |
| **Missingness-mechanism analysis MCAR/MAR/MNAR** (§3.1: NPDE valid for MCAR/MAR, **biased for MNAR**) | Choose the fill by *why* data is missing, not just how much | Rationale for the **MNAR density-guard** (T06, deactivate at R≥0.60) and per-input routing (T07). | Rubin 1976, *Biometrika* (canonical MCAR/MAR/MNAR); Little & Rubin 2019; Lin & Tsai 2020 `[İşeri 33]`; McKnight et al. 2007 `[54]` |
| **Multiple imputation by NPDE** (§3.1: repeated random draws) | Repeated stochastic draws, not a single point estimate | The **`--replicates M`** uncertainty mode — T10. | Rubin 1987 (*Multiple Imputation for Nonresponse in Surveys*); van Buuren 2018 (ch. on MI pooling / Rubin's rules) |
| **Unique-seed independent generation** (§ results: each input seeded separately so no spurious cross-parameter correlation) | Deterministic, reproducible draws | Codifies the **determinism rule** (Rule 8, `RANDOM_SEED`). | Mastrucci et al. 2017 `[İşeri 49]`; Kristensen et al. 2017 (independent parameter distributions) `[46]` |
| **Global sensitivity analysis** (§ results: form factor **70.3%** of QH + envelope U ~11%; SHGC **31.3%** + south-WWR of IOD; form factor **64%** of GWP) | Which inputs actually move the answer | **Prioritization evidence:** geometry/morphology (footprint·height·`levels` → S/V form factor) dominates heating & carbon, so **T04/T05/T06 are the highest-EUI-leverage fills** — this is *why* Phase A is front-loaded. Occupant loads are low-leverage for QH; SHGC/WWR matter mainly for overheating. | Mastrucci et al. 2017 (GSA for stock models) `[İşeri 49]`; Prataviera et al. 2022 `[32]`; Tian et al. 2014 (bootstrap SA) `[29]` |

> **Citation convention for the cross-reference columns.** Entries tagged `[İşeri n]` are the numbered
> references *n* in the foundational paper's own reference list (`resources/…docx.md`, §References) — verified
> against that list, not re-derived. Un-tagged entries are the canonical methodological source for that
> technique (author-year + venue), given so each method can be validated against primary literature
> independently of our internal M0x research reports.

**The single most important framing:** OpenUBEM already has a designed, Phase-1-only imputation
tier (`imputation.py` + §3E). This feature = **execute §3E Phase 2 (the ML imputer, F12), close the
Tier-B silent-default provenance gaps the audit found, add the fusion + spatial tiers the research
endorses, and build the validation harness (M09) that lets us prove any of it is trustworthy** —
all without ever tuning an imputer against validation EUI.

---

## 2. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** No other working directory.
2. **You execute this plan; you do not rewrite it.** If DESIGN §3E or the Stage-3 DESIGN is
   ambiguous or conflicts with a task, **STOP and quote the exact lines** — do not invent a
   resolution.
3. **Never edit `main.py` (root), OVERVIEW, or DESIGN docs. No `.py` under `docs/`.**
4. **Two non-negotiable constraints bind every task** (they are the whole point of the feature):
   - **Zero-fitted-parameters.** No imputer setting, threshold, hyperparameter, or bound may ever be
     calibrated/selected to make simulated EUI match a validation anchor. Imputers are fit **only**
     on independent building-attribute data (observed complete cases, standards tables, registries),
     **never** on the downstream EUI target. The downstream-EUI check (T09) is an *evaluation* metric
     reported to the user; its result is **never** fed back to tune the imputer. (DESIGN §3E "nothing
     is trained"; M04 §2; M09 §4.)
   - **Mandatory provenance.** Every value the pipeline did not observe must leave a **queryable**
     marker: a provenance token **and** a HIGH/MEDIUM/LOW confidence tier. A fill with no trace is a
     defect regardless of how good the value is. (M08/M09; audit §3.)
5. **Extend the existing provenance vocabulary; do not replace it.** The canonical `provenance_*`
   column values are `{ASHRAE_STANDARD, HEURISTIC, KDE_IMPUTED, PDE_GENERATED}` (DESIGN §12 line 35);
   `data_quality_flag` is a `|`-separated multi-token string (`_FLAG_SEP = "|"`,
   `construction_sets.py:45`); `archetype_confidence ∈ {HIGH, MEDIUM, LOW}`. New tokens append to
   these conventions.
6. **Fit-on-complete-case-only / no leakage.** Any statistic, donor pool, or model is computed from
   observed rows only, and (for multi-city work) never from the held-out validation city. (M08
   anti-pattern; M09 Step A.)
7. **Default to no comments.** One short line only where the WHY is non-obvious.
8. **Determinism.** All sampling flows through `np.random.default_rng(config.RANDOM_SEED)` — same
   seed ⇒ byte-identical artifacts (DESIGN §3E line 138). No unseeded `np.random`/`Math.random`.
9. **Delicate code (T02/T03) touches every HVAC/DHW/cooking emitter.** Change the value-substitution
   semantics carefully; a wrong `or`→`get` conversion silently changes behaviour for a valid `0`.
   These tasks stop-and-report before Phase B begins.

---

## 3. File layout

New / modified files (exact tree). **No files outside this list without a plan update.**

```
openubem/
├── semantic/
│   ├── imputation.py          (MODIFY — T07: routing entry `impute_missing()`; T11: real ML tier)
│   ├── spatial_impute.py      (NEW    — T06: neighbour-vote + kNN fill + MNAR density filter)
│   ├── provenance.py          (NEW    — T01: canonical token/confidence schema + lineage summary)
│   ├── construction_sets.py   (MODIFY — T04: `resolve_vintage` donor step + return-contract change (see §6 T04))
│   ├── __init__.py            (MODIFY — T04: enrich_semantics §3B wiring — split env-HEURISTIC mask from tier-3 flag; added at wave-2b pin)
│   └── building_classifier.py (MODIFY — T05: `classify()` builds group-median lookup, threaded → `_impute_levels`)
├── idf/
│   ├── hvac.py                (MODIFY — T02: `.get(k) or d` → tracked default + flag; +_emit_ptac gas-heating residual, wave-1 audit)
│   ├── dhw.py                 (MODIFY — T03: 400 m² / 1-floor tracked default + flag)
│   ├── cooking.py             (MODIFY — T03: same)
│   └── refrigeration.py       (MODIFY — T03 residual: same `_total_floor_area` geometry defaults — added at wave-1 audit)
├── validation/                (NEW dir)
│   ├── __init__.py
│   ├── mask_recover.py        (NEW — T08: mask-and-recover + spatial-block hold-out + per-input metrics)
│   └── eui_impact.py          (NEW — T09: Simulation-A-vs-B downstream-EUI check, MBE/CV(RMSE))
└── config.py                  (MODIFY — T07: per-input imputation routing config + strict mode;
                                          T10: `--replicates` / uncertainty-mode switch)

tests/
├── test_provenance.py         (NEW — T01)
├── test_spatial_impute.py     (NEW — T06, incl. MNAR-block deactivation)
├── test_tierB_provenance.py   (NEW — T02/T03: assert flags emitted, `0`-value not clobbered)
├── test_vintage_donor.py      (NEW — T04)
├── test_levels_groupwise.py   (NEW — T05)
├── test_imputation_routing.py (NEW — T07: fusion→stats→ML fallback order + strict mode)
├── test_mask_recover.py       (NEW — T08)
└── test_ml_imputer.py         (NEW — T11, Phase C)

docs/docs_ACTIVE/input/imputation/
└── PLAN_input_imputation_implementation.md  (this file — §8 progress log appended by executor)
```

---

## 4. Dependency decisions (pre-decided — do not re-debate)

| Concern | Decision | Rationale |
|---|---|---|
| Statistical/spatial tier deps | **Stdlib + existing `numpy`/`pandas`/`scipy`/`geopandas`/`shapely` only.** Neighbour search via `scipy.spatial.cKDTree` or `geopandas.sindex`. | Phase A ships zero new deps; keeps the safe tier trivially auditable (M03 caveat on kNN complexity). |
| ML tier (Phase C) | **`scikit-learn` only** (`IterativeImputer`/`RandomForestRegressor`/`RandomForestClassifier`), persisted with `joblib`. **No `xgboost`/`lightgbm` in core.** | DESIGN F12 already specifies "sklearn Pipeline persisted with joblib" (line 138). GBM needs n≥5,000 (M04 Table 4) — above single-city floors; not worth the dep. |
| MissForest | Implement via `sklearn.impute.IterativeImputer(estimator=RandomForestRegressor/Classifier)` — **do not** add the unmaintained `missingpy`. | M04 recommends MissForest behaviour; sklearn's IterativeImputer is the maintained, pinnable equivalent. |
| Neural / GNN / diffusion / LLM | **Not a dependency. Not implemented.** Phase E documents them as deferred/rejected. | M05/M06/M10 Part C: defer-or-reject for single-city scale + zero-fitted-params. |
| TabPFN (experimental only) | **Optional extra, never a core/default dep**; isolated experimental track only (Phase E). | M10: only frontier method passing constraints, but NOT READY (no building-domain validation). |
| Fusion sources (Phase D) | **Overture Maps via runtime DuckDB spatial query** (like `osm_fetcher`); LiDAR/assessor as **user-config paths**, runtime-fetched. **Nothing bundled in the wheel** (all datasets too large / license-restricted). | M07 §2: Overture ~150GB, LiDAR TB-scale; only city-slice test fixtures bundle. |
| Multiple imputation | **Off by default.** Default = single probabilistic draw + confidence flag; `--replicates M` opt-in. | M03 §2 / M09 §2: m-fold EnergyPlus runs are 5–10× cost; not justified as default. |

---

## 5. Source-of-truth verified facts (manager-grepped — executor does not re-derive)

**A. The imputation tier already exists and is Phase-1-only.**
- `imputation.py::impute_column(series, method="kde"|"pde", bounds, rng, bw_method)` — KDE fit on
  observed + clamp to bounds; PDE = uniform(bounds) when 100% missing (`imputation.py:13-71`).
- `imputation.py::build_ml_imputer(gdf, target_col, feature_cols)` **raises `NotImplementedError`** —
  labelled *"Phase-2 feature (DESIGN §3E / F12)"* (`imputation.py:74-88`). **This is the T11 hook.**
- DESIGN §3E specifies the *full* three-tier `impute_column(method='auto')`: AUTO → KDE
  (0%<missing<100%), PDE (100% missing), **ML (`model_path` provided → joblib sklearn Pipeline) —
  Phase 2** (DESIGN lines 116-138). **Current code drift:** the live signature is `method="kde"`
  default with **no** `auto` routing and **no** `model_path` param. Phase C (T11) reconciles code to
  the §3E AUTO spec.

**B. Provenance mechanism (what "queryable marker" concretely means today).**
- Canonical `provenance_*` column values: `{ASHRAE_STANDARD, HEURISTIC, KDE_IMPUTED, PDE_GENERATED}`
  (DESIGN §12 line 35; `construction_sets.py:235-240`; `_PROV_COLS` line 146-149).
- `data_quality_flag`: `|`-joined multi-token string (`_FLAG_SEP="|"`, `construction_sets.py:45`),
  idempotent-append pattern (`append_vintage_nan_flag`, lines 259-276). Existing tokens include
  `VINTAGE_NAN_PERMISSIVE_DEFAULT`, `HEURISTIC_HEIGHT`, `HEURISTIC_DEFAULT`, `FALLBACK_UNKNOWN`,
  `FALLBACK_SIZE_DEFAULT` (audit §2.1-2.2).
- Confidence tier: `archetype_confidence ∈ {HIGH, MEDIUM, LOW}`, assigned by
  `building_classifier.py::_assign_confidence` (line 322); schema roles emitted by `_write_schema_json`
  with `provenance_role ∈ {provenance, quality}` (lines 63-75, 680-684).

**C. The three fills the research says to fix (all verified against source).**
- **`year_built` NaN → `DOERefPre1980`** (oldest tier, U-factors ×1.6): `resolve_vintage`
  (`construction_sets.py:126-141`), flag `VINTAGE_NAN_PERMISSIVE_DEFAULT`. M02 Part C names this
  **"OpenUBEM is furthest behind peer practice"** and the **highest-value, lowest-cost upgrade** →
  T04. (Tier A — has a flag, but the *value* is biased.)
- **`levels` both-absent → `1`**: `building_classifier.py::_impute_levels` (lines 121-127), flags
  `HEURISTIC_HEIGHT` (from height) / `HEURISTIC_DEFAULT` (both absent) → T05.
- **Tier-B silent defaults (NO flag at all):**
  - HVAC: `.get("cooling_cop") or 3.0`, `heating_efficiency or 0.8`, fan params, etc. — the
    `dict.get(key) or default` pattern (**not** `.get(key, default)`) at
    `idf/hvac.py:125,168-171,206-209,248-252,299-303,351-354,383-389,428-430,462-464,503`. Substitutes
    on **falsy-but-valid** too (a stored `0` becomes `3.0`) (audit §2.6, §3.2) → T02.
  - DHW/cooking: `.get("footprint_area_m2") or 400.0` (`idf/dhw.py:18-20`, `idf/cooking.py:20-21`);
    `num_floors → 1` → T03.

**D. Config + determinism surface.**
- `config.py` exposes `LOAD_MODE` (default `'deterministic'`), `RANDOM_SEED` (default 42 — seeds the
  §3E sampler), `PDE_BOUNDS_PATH` (DESIGN line 29). Probabilistic mode already perturbs
  lighting/equipment/occupant via PDE within ASHRAE bounds (DESIGN lines 136-138) — the T10
  uncertainty-mode hook.

**E. DESIGN explicitly defers holdout/EUI-impact validation to Phase 2.** Stage-2.2 DESIGN validation
note (lines 199-205): *"Not applicable — Step 2.2 trains no model… its EUI-level consequences are
exercised by the Phase-2 probabilistic-mode studies, not by a holdout here."* → the M09 harness
(T08/T09) is the Phase-2 validation this note anticipates. No DESIGN conflict.

**F. Research verdicts that BIND method choice (so the executor cannot substitute a fancier method):**
- Deep-generative (GAIN/VAE/DAE/diffusion/tab-transformer): **skip/frontier-only**; classical
  MissForest/MICE beats them for n<30k (M05 Table 3, Part C §1). → not in scope except as Phase-E docs.
- GNN: **reject** — thousands of fitted weights violate zero-fitted-params; neighbour-vote/kriging
  capture ~80% of the signal with zero trainable weights (M06 Table 4, Part C §2). → T06 uses
  neighbour-vote + kNN, **not** a GNN.
- LLM prompting: **firm disqualification** — hallucination + no provenance + non-determinism (M10
  Part C §1). → never implemented.
- MNAR clustering is spatial fill's signature failure: deactivate spatial fill when local
  missingness ratio ≥ 0.60 (M06 §4). → hard requirement in T06.

---

## 6. Task list

> Each task: **What / Why / How / How to test.** T01–T10 = executable now (Phases A+B).
> T11–T13 = scoped, **gated** (do not start without the gate in §7 being met + manager greenlight).

### Phase A — Provenance-complete statistical MVP (user tier 1 + contract foundation)

#### T01 — Canonical imputation provenance schema (`semantic/provenance.py`)
- **What:** A single module defining the imputation provenance contract every other task emits into:
  (a) a token builder `impute_token(method, source, confidence)` producing the M09 `{METHOD}_{SOURCE}_{TIER}`
  form (e.g. `DEFAULT_ASHRAE901_LOW`, `HOTDECK_NEIGHBOR_MED`), constrained to the existing canonical
  method/confidence vocabulary; (b) helpers to append to `data_quality_flag` (reuse the idempotent
  `|`-join pattern) and set a `provenance_*` column + confidence; (c) a per-building **lineage
  summary** appended once at end of enrichment: `imputed_fields_count` (int) and
  `mean_imputation_confidence` (float; HIGH=1.0/MED=0.5/LOW=0.1, observed=1.0) per M09 §3B.
- **Why:** M08/M09 — the provenance contract is the centrepiece of "OpenUBEM AI"; centralizing it
  stops each site inventing its own token and closes the audit's Tier-B gap uniformly. DESIGN §12.
- **How:** Pure functions over a `gdf`; **extend** `{ASHRAE_STANDARD,HEURISTIC,KDE_IMPUTED,PDE_GENERATED}`
  — do not rename them. Keep `_FLAG_SEP="|"`. No new dependency.
- **How to test:** `test_provenance.py` — token format round-trips; append is idempotent (no dup
  tokens); lineage summary math on a hand-built 5-row frame; observed rows score 1.0.

#### T02 — Close the HVAC Tier-B provenance gap (`idf/hvac.py`) — **delicate**
- **What:** Replace every `cop_entry.get(key) or default` with `.get(key, default)` **and**, when the
  default is used, emit a provenance token via T01 (`DEFAULT_ASHRAE901_<param>` + confidence `LOW`)
  into the building's `data_quality_flag`. Distinguish truly-absent from falsy: a stored `0` must
  **not** be silently replaced (log/flag it instead).
- **Why:** Audit §3.1/§3.2 — HVAC is the only numeric-substitution site leaving no trace; provenance
  rule is non-negotiable. M02 Part C: transition silent HVAC defaults to tracked.
- **How:** Touches ~9 emitters (lines listed in §5C). Keep the default **values** unchanged (this is
  an instrumentation fix, not a physics change). Thread the building id / flag accumulator through
  the emitter or return a per-building flag set the caller merges. **Do not** alter EUI.
- **How to test:** `test_tierB_provenance.py` — a building with no `cooling_cop` gets the flag +
  LOW confidence; a building with `cooling_cop=0` is flagged distinctly and **not** turned into 3.0;
  a building with a real COP gets **no** default flag; EnergyPlus numeric output unchanged vs. baseline.

#### T03 — Close the DHW/cooking Tier-B gap (`idf/dhw.py`, `idf/cooking.py`) — **delicate**
- **What:** Same treatment as T02 for `footprint_area_m2 → 400.0` and `num_floors → 1`: `.get(k,d)`
  + T01 token (`DEFAULT_GEOMETRY_AREA_LOW` / `DEFAULT_GEOMETRY_FLOORS_LOW`). Preserve the deliberate
  table-driven `no_dhw`/`no_cooking` skip (audit §2.7 — that is *not* a guess, leave it).
- **Why:** Audit §3.3 — same instrumentation gap, lower stakes but same rule.
- **How:** Two small sites; keep 400/1 values. Do not touch the `no_dhw`/`no_cooking` branch.
- **How to test:** covered by `test_tierB_provenance.py` — area/floors defaults flagged; `no_dhw`
  archetype emits **no** area-default flag (skip path preserved).

#### T04 — `year_built` donor/neighbour vintage before oldest-default (`construction_sets.py`) — **highest-value**
- **What:** Before `resolve_vintage` falls back to `DOERefPre1980` for NaN `year_built`, attempt, in
  order: (1) **spatial neighbour-median vintage** via T06 (same-use neighbours, MNAR-guarded);
  (2) **group-wise mode** stratified by `use_class` (+ block/postcode if present); (3) last-resort
  oldest-default. Emit `HOTDECK_NEIGHBOR_<tier>` / `GROUPMODE_<tier>` for (1)/(2), keep
  `VINTAGE_NAN_PERMISSIVE_DEFAULT` **only** for (3).
- **Why:** M02 Part C — the flat oldest default (U ×1.6) is "furthest behind peer practice"; peer
  tools (CEA/CityBES/AutoBEM) all use region-typical/neighbour vintage. M03 §4 recommends stratified
  geographic hot-deck. Highest EUI-bias reduction per unit effort.
- **How:** Keep `resolve_vintage`'s bin/label logic; insert the donor step on the `nan_mask` subset
  only. Confidence: neighbour-agreement (T06) → HIGH/MED, group-mode → MED, oldest-default → LOW.
- **How to test:** `test_vintage_donor.py` — a NaN-year building in a block of 1995 buildings imputes
  ~1995 not Pre1980; an isolated NaN building with no donors falls to oldest-default with LOW + the
  legacy flag; determinism under fixed seed.
- **PINNED CONTRACT v2 (manager, re-spec 2026-07-01 — position-stable; supersedes the v1 that STOPPED on arity):**
  - **Why v2:** v1 made position-0 a frame (`gdf_out`-first). Grep proved **8 call sites** all do rigid
    3-value unpacks reading position-0 = vintage `Series`, position-1 = NaN `Index`, position-2 discarded
    (`__init__.py:304`; `test_construction_sets.py` L72/83/122/152/174/188/211). v2 keeps positions 0 and 1
    byte-identical and repurposes only the unused position-2 — no consumer breaks on arity (mirrors how T05
    kept `_impute_levels`'s first two branches byte-stable).
  - **Signature — positions 0 and 1 UNCHANGED.** `resolve_vintage(gdf)` still returns a **3-tuple
    `(vintage_series, nan_rows, vintage_prov)`**. Position-0 `vintage_series` stays a `pd.Series` of vintage
    tokens; position-1 `nan_rows` stays the `pd.Index` of **every** originally-NaN `year_built` row.
    Position-2 (today an unused duplicate of `nan_rows`, discarded as `_` everywhere) becomes a
    **`pd.Series[str]` of the per-row provenance token, indexed over `nan_rows`** (suffix encodes the tier).
  - **Position-0 now carries donor fills.** For formerly-NaN rows, `vintage_series` holds the tier-1/tier-2
    donor vintage (re-binned); tier-3 rows keep `DOERefPre1980`. This is the intended M02 behaviour change and
    flows into the envelope merge unchanged (still just a `Series`).
  - **Three-tier fill on the `nan_mask` subset, in order, leakage-safe:**
    1. **Spatial donor** — stratify the frame by `use_class` if that column is present, else by
       `archetype_id` (guaranteed present — `__init__.py:307` reads it); within each stratum call
       `spatial_impute.knn_fill(stratum, "year_built", ...)` (continuous, MNAR-guarded, donors =
       observed-year rows only → no leakage). Fill the returned year, re-bin via the existing
       `_YEAR_BINS`/`_YEAR_LABELS`. Token `HOTDECK_NEIGHBOR_HIGH` | `HOTDECK_NEIGHBOR_MED` from knn_fill's
       confidence tier. MNAR-blocked / no-donor rows fall through to step 2.
    2. **Group-wise mode** — for rows still NaN, the mode vintage-bin of observed rows in the same
       `use_class`/`archetype_id` stratum. Token `GROUPMODE_MED`.
    3. **Oldest-default** — rows still NaN (empty stratum / no observed donors anywhere) keep
       `DOERefPre1980`. Token `VINTAGE_NAN_PERMISSIVE_DEFAULT` (the legacy LOW token, unchanged).
  - **Caller edit — `__init__.py` enrich_semantics §3B (all position-stable):**
    - L304: `vintage_series, nan_vintage_rows, vintage_prov = resolve_vintage(out)` (add the third name).
    - L318 `apply_nan_vintage_provenance(env_real, nan_vintage_rows.intersection(...))` — **UNCHANGED**
      (env-provenance HEURISTIC for ALL originally-NaN rows is still correct — even a donor vintage selects a
      heuristic envelope).
    - L331: **replace** the blanket `out = append_vintage_nan_flag(out, nan_vintage_rows)` with
      `out = append_vintage_donor_flags(out, vintage_prov)` (NEW helper in `construction_sets.py`) that
      appends each row's position-2 token to `data_quality_flag` via the **same idempotent `_FLAG_SEP`
      logic** as `append_vintage_nan_flag`. For tier-3 rows the token IS `VINTAGE_NAN_PERMISSIVE_DEFAULT`, so
      their `data_quality_flag` stays byte-identical to today; only donor rows now read HOTDECK/GROUPMODE.
    - **Keep `append_vintage_nan_flag` and `apply_nan_vintage_provenance` unchanged** — their direct unit
      tests (`test_construction_sets.py` L90/101/182) must stay green; `append_vintage_donor_flags` is additive.
  - **One authorized test edit in `test_construction_sets.py` — `test_resolve_vintage_nan_year` (L78) ONLY.**
    Its 2-row frame (NaN MediumOffice + observed-2020 MediumOffice) now donor-fills the NaN row to
    `90.1-2019` via tier-2 group-mode, so `assert vintage.iloc[0] == "DOERefPre1980"` legitimately changes.
    Make the NaN row **donorless** so the test keeps asserting the tier-3 fallback it was written for: reduce
    to a **single-row NaN frame**, keep `assert vintage.iloc[0] == "DOERefPre1980"` and `assert 0 in nan_rows`,
    and delete the now-absent `assert 1 not in nan_rows`. Donor behaviour is covered by the new
    `test_vintage_donor.py`, not here. **Touch no other test in that file.**
  - **Zero-fitted-params / determinism:** k/radius stay T06's fixed convention (never swept); all
    tie-breaks via `np.random.default_rng(config.RANDOM_SEED)`; nothing here reads EUI.
  - **STOP-and-report if:** (a) neither `use_class` nor `archetype_id` is present (no stratifier — do not
    vote across all uses); (b) a grep of the test tree shows any assertion of `VINTAGE_NAN_PERMISSIVE_DEFAULT`
    on a NaN row that HAS a same-stratum observed donor (it would flip to HOTDECK/GROUPMODE — quote it, do
    not silently break it); (c) any consumer unpacks position-0 or position-1 with a meaning other than
    (vintage `Series`, all-NaN `Index`).

#### T05 — Group-wise stratified `levels` vs. default-to-1 (`building_classifier.py`)
- **What:** In `_impute_levels`, when `height_m` **and** `levels` are both absent, replace the
  flat `1` with a **group-wise median `levels`** stratified by `use_class` (optionally neighbour
  context via T06), rounded to ≥1. Keep the `height//3.5` path unchanged. Emit `GROUPMEDIAN_LEVELS_MED`
  (replacing `HEURISTIC_DEFAULT` on the imputed rows); keep `HEURISTIC_HEIGHT` for the height path.
- **Why:** M03 Table 4 / Part C — defaulting to 1 storey collapses stock height variance and
  under-counts wall/window area in Stage-3; group-wise median is the strictly-better basic-tier fill.
- **How:** Fit the per-`use_class` median from observed-levels rows only (no leakage). Guard empty
  strata (fall to global observed median, else 1 with LOW).
- **How to test:** `test_levels_groupwise.py` — both-absent office in a stock of 8-storey offices
  imputes ~8 not 1; empty-stratum edge falls back deterministically; height-present rows untouched.
- **PINNED CONTRACT (manager, wave-2b — execute exactly):**
  - **Self-contained in `building_classifier.py`** (does NOT touch `__init__.py`). In `classify()`
    (the method at ~line 568, before the `out.apply(classify_building, …)` at ~585), build a
    `use_class → median(levels)` lookup **from observed-levels rows only** (`out[out["levels"].notna()]`
    grouped by `use_class`, median rounded to `max(1, round(m))`) plus a global observed median. **No
    leakage** — rows with missing levels never enter the lookup.
  - **Thread it down:** pass the lookup (+ global median) as new keyword args through
    `classify_building(...)` (~498) into `_impute_levels(...)` (~121). Keep the two existing branches
    unchanged — `levels` observed → `(int, "OSM_OBSERVED")`; `height_m>0` → `(…, "HEURISTIC_HEIGHT")`.
    **Replace only the third branch** (`return 1, "HEURISTIC_DEFAULT"`):
    1. group median for the row's `use_class` present → `(median, "GROUPMEDIAN_LEVELS_MED")` (MED);
    2. else global observed median present → `(global_median, "GROUPMEDIAN_LEVELS_MED")` (MED);
    3. else (no observed levels anywhere) → `(1, "LEVELS_DEFAULT_LOW")` (LOW) — a new distinct token,
       not the old `HEURISTIC_DEFAULT`, so the tier is queryable.
  - The confidence tier rides in the token suffix (`_MED`/`_LOW`) per M09 §3A — the returned
    `lev_src` string flows to provenance exactly as `HEURISTIC_DEFAULT` did; confirm nothing downstream
    pattern-matches the literal `"HEURISTIC_DEFAULT"` before renaming it (grep first).
  - **STOP-and-report** if any downstream code matches `"HEURISTIC_DEFAULT"` literally (would break on
    the rename) — quote the site instead of guessing.

#### T06 — Spatial neighbour-fill utility + MNAR density filter (`semantic/spatial_impute.py`)
- **What:** New module: (a) `neighbour_vote(gdf, col, k, radius)` for categorical (`use_class`,
  vintage bins) returning value + agreement ratio; (b) `knn_fill(gdf, col, k, radius)` for continuous
  (`levels`, `height`) returning distance-weighted mean + neighbour dispersion; (c) **MNAR missingness
  filter**: compute local missingness ratio R over k/ radius; if R ≥ 0.60, **deactivate** spatial fill
  for that row and emit `SPATIAL_CLUSTER_MNAR_BLOCKED`, routing to the aspatial fallback. Neighbour
  agreement → confidence (e.g. ≥0.8→HIGH, ≥0.5→MED, else LOW / edge-of-bbox → downgrade).
- **Why:** M06 Part C — spatial signal (Moran's I > 0.45) is OpenUBEM's cheapest strong predictor
  (coords already present) and must be first-class; **but** MNAR clustering is its signature failure
  and must be guarded. Neighbour-vote/kNN, **not** GNN (M06 §2, §5-F).
- **How:** `scipy.spatial.cKDTree` / `geopandas.sindex` on centroids; fixed k/radius = **published
  conventions, not EUI-tuned** (e.g. k=10 or 100 m — cite the choice, do not sweep it against EUI).
  Zero trainable weights. Consumed by T04/T05 and later C/D.
- **How to test:** `test_spatial_impute.py` — homogeneous block → high-agreement HIGH-confidence fill;
  a synthetic block with 70% of the attribute missing → `SPATIAL_CLUSTER_MNAR_BLOCKED` + aspatial
  fallback (assert spatial value **not** used); edge building → confidence downgrade.

### Phase B — "OpenUBEM AI" subsystem + validation harness (user tier 2)

#### T07 — Imputation routing subsystem + strict mode (`imputation.py`, `config.py`)
- **What:** A single entry `impute_missing(gdf, config)` that, per input, chains fallbacks in the
  research-mandated precedence **fusion (Phase D, if enabled) → spatial (T06) → statistical (KDE/PDE/
  group/donor) → ML (Phase C, if enabled)**, stopping at the first that succeeds and emitting the
  matching provenance. Add a config surface (`config.py`) for **per-input tier selection** and a
  **strict "impute-nothing, hard-fail" mode** for auditing. Enforce fit-on-complete-case-only.
- **Why:** M08 subsystem contract — the algorithm is reversible, the contract is not; centralize
  routing + leakage rule + config in one place instead of the current scatter (audit §1).
- **How:** Keep `impute_column` as the low-level primitive; `impute_missing` is the orchestrator.
  Reconcile toward the §3E `method='auto'` spec (§5A drift). Strict mode raises with the list of
  still-missing (attribute, building) pairs.
- **How to test:** `test_imputation_routing.py` — fallback order honoured (mock a fusion hit → stats
  not called); strict mode raises on any residual NaN; disabling a tier in config skips it.

#### T08 — Mask-and-recover + spatial-block hold-out harness (`validation/mask_recover.py`)
- **What:** The M09 evaluation protocol: on **complete cases**, spatial-block 80/20 hold-out (group by
  postcode/block, not random rows), mask target attributes on the 20%, run the imputer, score
  per-input-type — continuous: MAE/RMSE + **KS/Wasserstein** (distributional fidelity); categorical:
  PFC + log-loss. Report, do not tune.
- **Why:** M09 Table 1 / Step A-B — random-row splits leak via spatial autocorrelation; distributional
  fidelity catches variance-collapse that RMSE alone rewards. Validate-not-tune keeps
  zero-fitted-params (M09 §4).
- **How:** Pure evaluation; consumes T07. Spatial blocks via existing geometry columns. **No EUI here.**
- **How to test:** `test_mask_recover.py` — on a synthetic frame with known structure, metrics are
  computed correctly; a mean-fill imputer scores worse on KS than a KDE fill (fidelity check bites).

#### T09 — Mandatory downstream-EUI impact check (`validation/eui_impact.py`)
- **What:** The UBEM-specific gate (M09 Step C): for a complete-case validation set, run Stage-3→4
  **twice** — Simulation A (observed inputs) vs Simulation B (imputed inputs) — and report **MBE**
  (target |MBE| < 5% neighbourhood-scale) and **CV(RMSE)** (target < 15% per-building) on annual EUI,
  plus peak-load deviation. Input-reconstruction accuracy alone is **not** sufficient validation.
- **Why:** M09 §1 Step C / hard requirement — an imputer with low input-RMSE that shifts city EUI 15%
  is a failure. This is the gate every fill (A) and the ML tier (C) must pass.
- **How:** Wrap the existing simulation harness; **read-only** on the imputer (its EUI error is
  never fed back — §4/Rule 4). This is a validation utility, not a pipeline stage.
- **How to test:** exercise on the smallest available fixture city; assert the A/B comparator returns
  MBE/CV(RMSE); **flag as LIVE_SMOKE** — synthetic-only green here is a blind spot (memory:
  synthetic ≠ live), so the checkpoint requires one real fixture-city A/B run before greenlight.

#### T10 — Optional uncertainty mode `--replicates M` (`config.py`, orchestrator)
- **What:** Default stays single probabilistic draw + confidence flag. Opt-in `--replicates M` (M≥5)
  draws M independent imputations, runs M simulations, pools via Rubin's rules → EUI mean + 95% CI.
- **Why:** M09 §2 / M03 §2 — multiple imputation is the honesty gold standard but 5–10× cost; make it
  opt-in, not default.
- **How:** Reuse the existing `LOAD_MODE` probabilistic hook + `RANDOM_SEED` (distinct seeds per
  replicate, derived deterministically from the base seed). No default-path cost.
- **How to test:** `--replicates 3` on a tiny fixture yields 3 seed-distinct input sets + a pooled CI;
  default run byte-identical to pre-T10.

### Phase C — Classical-ML imputer (user tier 3) — **GATED (see §7 CP-2)**

#### T11 — Implement `build_ml_imputer` / §3E ML tier (`imputation.py`)
- **What:** Replace the `NotImplementedError` stub with a MissForest-equivalent
  (`sklearn.impute.IterativeImputer` w/ RF estimator) for `levels`/`height`/`use_class` and
  **conditionally** `year_built` (geometry + `centroid_x/y` + spatial-lag neighbour vintage). Enforce
  **attribute-only-fitting discipline** (loss = attribute error only, never EUI), **complete-case
  floors** (RF ≥ 1,000; kNN ≥ 200 — else fall back to Phase-A stats), **frozen weights** persisted via
  joblib, tree-variance/vote-share → confidence (M04 §3). Wire the `method='ml'`/`model_path` path into
  `impute_column` per §3E.
- **Basic-ML method menu (tier 3) — all `scikit-learn`, all attribute-only-fit, all complete-case-floored,
  all deriving confidence from model dispersion.** T11 builds the **primary**; the rest are documented
  alternatives the executor may select per-attribute *only* within these classes (no new deps per §4, no
  EUI in any fit graph). This is the concrete answer to user tier 3 "basic ML models":

  | Method | sklearn class | Best-fit targets | Complete-case floor | Confidence signal | Role | Method origin (external ref) |
  |---|---|---|---|---|---|---|
  | **MissForest** (primary) | `IterativeImputer(RandomForestRegressor/Classifier)` | mixed multivariate morphology + `use_class` | RF ≥ 1,000 | tree/vote dispersion | **T11 default** | Stekhoven & Bühlmann 2012, *Bioinformatics* 28(1) |
  | **MICE / Bayesian Ridge** | `IterativeImputer(BayesianRidge)` | continuous, near-linear | ≥ ~500 | posterior variance | multiple-imputation backbone feeding **T10 replicates** | van Buuren & Groothuis-Oudshoorn 2011, *J. Stat. Softw.* 45(3); van Buuren 2018 |
  | **kNN imputation** | `KNNImputer` | continuous morphology (`levels`, `height`) | ≥ 200 | neighbour dispersion | **below-RF-floor fallback**; feature-space complement to T06's *geographic* kNN | Troyanskaya et al. 2001, *Bioinformatics* 17(6) |
  | **Single-target RF / Extra Trees** | `RandomForestRegressor/Classifier`, `ExtraTrees*` | one field at a time | ≥ 1,000 | OOB / tree variance | simpler than MissForest when only one attribute is missing | Breiman 2001 (Random Forests); Geurts et al. 2006 (Extremely Randomized Trees) |
  | **HistGradientBoosting** | `HistGradientBoostingRegressor/Classifier` | larger multi-city stock | ≥ 5,000 (M04 Table 4) | quantile spread | **optional, gated to multi-city scale** — native NaN handling, **no xgboost/lightgbm dep** | Ke et al. 2017 (LightGBM, NeurIPS — the algorithm sklearn's HistGBM implements); Pedregosa et al. 2011 |
  | **Regularized linear/logistic** | `Ridge` / `LogisticRegression` | continuous / categorical | ≥ ~200 | residual std | interpretable **baseline floor** the trees must beat | Hoerl & Kennard 1970 (ridge regression, *Technometrics*); Pedregosa et al. 2011 |

  **Hard exclusions (unchanged):** none of these ever fit `cooling_cop`/`heating_efficiency`/U-values/`SHGC`
  — they have no attribute-side signal (M04 §1) and stay on the paper's **PDE-from-standards** path (§1
  prior-art table). ML targets are morphology/semantic only: `levels`, `height`, `use_class`, conditionally
  `year_built`.
- **Why:** M04 Part C + DESIGN F12 — classical ML materially beats defaults for morphology/spatial
  targets (height MAE ~1.8 m vs 3.5 m+); already the designed Phase-2 tier. **Never** for HVAC/U-values
  (no feature signal — M04 §1).
- **How:** Train only on complete cases of the training city; never touch the held-out validation
  city (§5F / Rule 6). Below floor → automatic Phase-A fallback (M04 §4).
- **How to test:** `test_ml_imputer.py` — attribute-only loss (no EUI in the fit call graph);
  sub-floor dataset falls back to stats; frozen model reload is deterministic; **must pass T08
  mask-and-recover ≥ Phase-A baseline AND T09 EUI-check** or it does not ship (CP-3).

### Phase D — Fusion-first external joins (research-driven) — **GATED / scoped**

#### T12 — External-data fusion precedence layer (scoped — expand to full tasks after CP-2)
- **What:** Insert authoritative external joins **ahead** of all imputation, per M07 precedence:
  `height/levels` ← LiDAR/3D-model/Overture; `year_built` ← assessor/EUBUCCO/Overture; `use` ←
  assessor/Overture; footprint completeness ← Overture. Emit `FUSED_<SOURCE>_HIGH` provenance; fall
  to imputation only on join miss.
- **Why:** M07 Part C — a real joined value beats any guess and sidesteps zero-fitted-params entirely
  (it's data acquisition). Highest data-quality tier.
- **How (scoped):** Overture via runtime DuckDB spatial query (like `osm_fetcher`); LiDAR/assessor as
  user-config paths; **nothing bundled** (§4). US-first; **ex-US coverage degrades** (M07 §4 — Turkey
  has no 3DEP/open assessor) so imputation must still carry load. **LIVE_SMOKE required** before this
  ships (external-data path — memory blind-spot rule).
- **How to test:** (defined at expansion) join-hit uses fused value + `FUSED_*`; join-miss falls to
  imputation; license/bundle guard asserts no restricted dataset is vendored.

### Phase E — Advanced / data-driven frontier (user tier 4) — **documented-deferred**

#### T13 — Frontier documentation + optional isolated experimental track (scoped)
- **What:** A short in-repo note (under this arc dir) recording, with the M05/M06/M10 evidence, that
  deep-generative/GNN/LLM are **out of scope** for the core pipeline (scale + zero-fitted-params +
  hallucination/provenance), and defining an **optional, isolated, non-default experimental TabPFN
  evaluation track** (pinned weights, complete-case context, entropy→confidence, `TABPFN_IMPUTED`
  provenance, MAR geometric/semantic targets only — never HVAC/U-values).
- **Why:** M05/M06/M10 Part C — ruling options *out* with evidence is a first-class deliverable; keeps
  "all data-driven" represented without letting an unvalidated method into scientific results.
- **How:** Markdown note only (no core-pipeline code); any TabPFN experiment lives behind an optional
  extra and never touches the default run. **NOT READY verdict stands** until building-domain
  validation exists.
- **How to test:** n/a (documentation); if the experimental track is built, it reuses the T08/T09
  harness and must clear the same gates as T11 before any promotion is even discussed.

---

## 7. Stop-and-report checkpoints

Four checkpoints at the integration points where a silent bug would compound. Executor stops, appends
§8 progress-log entries, runs the named tests, and waits for manager audit before proceeding.

- **CP-1 — after T06 (end of Phase A).** The delicate Tier-B closures (T02/T03) and the value
  upgrades (T04/T05) + spatial utility (T06) all land here; a wrong `or`→`get` or a leaky donor
  poisons every downstream EUI. **Gate:** `test_tierB_provenance`, `test_vintage_donor`,
  `test_levels_groupwise`, `test_spatial_impute`, `test_provenance` all green; manager confirms HVAC
  EUI numerically unchanged vs. baseline (instrumentation-only) and MNAR block actually deactivates.
- **CP-2 — after T10 (end of Phase B).** The subsystem contract + validation harness are the gate for
  everything data-driven. **Gate:** routing/strict-mode + mask-and-recover green; **T09 run once on a
  real fixture city (LIVE_SMOKE)** with MBE/CV(RMSE) reported. **No Phase C/D work starts until the
  manager greenlights on these numbers.**
- **CP-3 — after T11 (Phase C).** ML ships **only if** it beats the Phase-A statistical baseline on
  T08 mask-and-recover **and** does not worsen the T09 downstream-EUI check — else it stays stubbed.
- **CP-4 — before T12 ships (Phase D).** External-data path requires a LIVE_SMOKE join against a real
  Overture/assessor slice + the license/bundle guard, before it is allowed into a default run.

---

## 8. Progress log

*(Executor appends one entry per completed task — format per CLAUDE.md. Manager may append audit
notes.)*

#### Manager plan revision — İşeri et al. grounding + expanded basic-ML menu — 2026-07-01
- Artifacts: `PLAN_input_imputation_implementation.md` §1 (new prior-art technique table), §6 T11 (basic-ML method menu).
- Deviations: none — enrichment only; no task added/removed, no scope or dependency change (all methods remain sklearn-only per §4).
- Test status: n/a (plan doc).
- Notes: Manager read the foundational paper (`resources/` İşeri et al.) in full and confirmed the live `impute_column` KDE/PDE tier **is** the paper's NPDE/PDE — hardening the "not greenfield" framing. Folded 8 paper techniques into §1 with task mappings; the paper's sensitivity analysis (form factor 70.3% of QH, 64% of GWP; SHGC 31.3% of IOD) now justifies front-loading the geometry/morphology fills (T04–T06) in Phase A, and marks the PDE-from-standards inputs (SHGC/COP/U/infiltration) as off-limits to ML. Tier 3 (T11) expanded from MissForest-only to a 6-method sklearn menu (primary + documented alternatives) with per-target complete-case floors and the HVAC/U-value/SHGC exclusion restated.

#### Manager plan revision — external-literature cross-reference columns — 2026-07-01
- Artifacts: `PLAN_input_imputation_implementation.md` §1 tier-verdict table (+col "External literature cross-reference"), §1 İşeri-technique table (+col "External source (cross-ref)" + citation-convention note), §6 T11 basic-ML menu (+col "Method origin (external ref)").
- Deviations: none — documentation enrichment only; no task/scope/dependency change. §4 dependency table intentionally left without a cross-ref column (engineering decisions, not literature-validated methods).
- Test status: n/a (plan doc).
- Notes: Each method/verdict row now carries an **independent** literature anchor so the plan is defensible against primary sources, not only our internal M0x reports. Two citation classes, per the §1 note: `[İşeri n]` = verified entries in the foundational paper's own reference list (manager read the full `[1]`–`[82]` list from `resources/`); un-tagged = canonical methodological source (author-year + venue) for that technique (e.g. Stekhoven & Bühlmann 2012 MissForest, van Buuren & Groothuis-Oudshoorn 2011 MICE, Rubin 1976 MCAR/MAR/MNAR, Moran 1950 spatial autocorrelation, Grinsztajn et al. 2022 trees-beat-deep). No citation invented; canonical refs are the standard anchors for each named method.

#### T01 — Canonical imputation provenance schema — completed 2026-07-01
- Artifacts: `openubem/semantic/provenance.py` (NEW); `tests/test_provenance.py` (NEW).
- Deviations: none on contract. Two forced clarifications, both anchored: (a) the token
  tier suffix is the short `{HIGH, MED, LOW}` per M09 §3A example (`cooling_cop_prov =
  'DEFAULT_ASHRAE_90_1_LOW'`, line 118) and the plan T01 example `HOTDECK_NEIGHBOR_MED`;
  `impute_token` accepts canonical `{HIGH, MEDIUM, LOW}` and normalizes. (b) `add_lineage_summary`
  scores a provenance cell as *imputed* only when it parses as a `{METHOD}_{SOURCE}_{TIER}` token
  with METHOD ≠ OBSERVED; empty / legacy canonical values (`ASHRAE_STANDARD` etc., which carry no
  tier) are treated as observed-grade (score 1.0) — documented in the function; it is NOT yet wired
  into `enrich_semantics` (that orchestrator wiring is out of wave-1 scope). Vocabulary EXTENDED,
  not renamed (`CANONICAL_PROVENANCE` kept; `_FLAG_SEP="|"`). No new dependency (numpy/pandas only).
- Test status: `test_provenance.py` 15 passed (part of `33 passed in 1.82s` with T02/T03).
- Notes: API = `impute_token`/`parse_token`/`normalize_confidence`, `append_flag_token`(scalar,
  idempotent)/`append_flag`(vectorized), `set_provenance`(col+`confidence_<field>`),
  `add_lineage_summary` (M09 §3B: `imputed_fields_count` int + `mean_imputation_confidence`
  HIGH=1.0/MED=0.5/LOW=0.1, observed=1.0). Lineage math verified on a hand-built 5-row frame.

#### T02 — Close the HVAC Tier-B provenance gap (`idf/hvac.py`) — completed 2026-07-01
- Artifacts: `openubem/idf/hvac.py` (MODIFY); `tests/test_tierB_provenance.py` (NEW, shared w/ T03).
- Deviations: (1) Sites located by grepping `\.get\(...\)\s*or` (per kickoff), not §5C line numbers.
  Converted all single-key `entry.get(k) or d` sites to a `_resolve()` helper and all multi-source
  `chiller_cop_phaseE or cooling_cop or d` sites to a `_resolve_chain()` helper across the 10 emitters.
  (2) `_emit_ptac` line ~138 `Gas_Heating_Coil_Efficiency = htg_eff if htg_eff is not None else 0.8`
  is NOT the `.get()or` pattern and already preserves a stored 0, so it was left untouched (out of
  the grep-defined scope) — flagged here as a residual silent default the manager may choose to
  instrument later. (3) `_emit_wlhp`'s `heating_efficiency` read is vestigial (result discarded; the
  loop boiler uses the hardcoded 0.80), so its `or` was converted to `.get(k,d)` but emits NO token
  — provenance must reflect values that reach the model. (4) `assign_hvac` return type changed
  `None → list[str]` (backward-compatible; builder.py ignores it). `refrigeration.py` shares the
  same pattern but is NOT in the plan's file list, so it was left untouched (out-of-scope residual).
- Test status: `33 passed in 1.82s` (T01+T02+T03). Regression: `test_hvac.py`+`test_dhw.py`+
  `test_cooking.py`+`test_refrigeration.py`+`test_service_loads.py` = `175 passed, 5 skipped`.
- Notes: **EUI byte-identical confirmed at unit level** — a full sweep of all 30 archetypes (multi-zone)
  emits ZERO default flags (every read key is present & truthy in the bundled tables), and the bundled
  COP table has NO stored 0 in the instrumented keys, so the stored-0 branch never fires in production.
  The default VALUE at every site is unchanged; only a `DEFAULT_ASHRAE901_<PARAM>_LOW` token (confidence
  LOW) is emitted when a default is used, and a distinct `SUSPECT_ZERO_<PARAM>` token when a stored 0 is
  retained. A stored 0 is KEPT (verified: `cooling_cop=0` stays 0, not 3.0). The single-zone downgrade
  path (which deliberately strips VAV fan fields to force PSZ defaults) is the one real path that fires
  flags (fan_static_pa/fan_total_efficiency → 622.5/0.55575, values unchanged) — used as the end-to-end
  row-append test. Tokens are appended in place to `row['data_quality_flag']` (idempotent) AND returned.

#### T03 — Close the DHW/cooking Tier-B gap (`idf/dhw.py`, `idf/cooking.py`) — completed 2026-07-01
- Artifacts: `openubem/idf/dhw.py` (MODIFY), `openubem/idf/cooking.py` (MODIFY); tests in
  `tests/test_tierB_provenance.py`.
- Deviations: (1) `footprint_area_m2 → 400.0` (`DEFAULT_GEOMETRY_AREA_LOW`) and `num_floors → 1`
  (`DEFAULT_GEOMETRY_FLOORS_LOW`, fired only when the floor-count genuinely falls back to 1, i.e.
  no explicit `num_floors` and no parseable `_F` index) instrumented via a `_resolve_area()` helper +
  a floors-fallback flag inside `_total_floor_area`. (2) The per-zone `int(z.get("num_floors",0) or 0)`
  sentinel (line 16) was LEFT as-is: its `or 0` guards `None` before `int()` (converting to `.get(k,0)`
  alone would crash on a stored `None`), and it normalizes to 0 ("count from names"), not to the `→1`
  default the plan names — so it is not a value-substitution site. (3) The table-driven `no_dhw`/
  `no_cooking` skip is UNTOUCHED and runs before any geometry resolution (verified: no_dhw/no_cooking
  archetypes emit no geometry token). `assign_dhw`/`assign_cooking` now return `list[str]` (was None;
  builder.py ignores it). `refrigeration.py` has the same `_total_floor_area` but is out of the plan's
  file list → left untouched.
- Test status: covered by `33 passed`; DHW/cooking regression green (`175 passed, 5 skipped`).
- Notes: Same instrumentation-only guarantee — default area/floors VALUES unchanged. A stored 0
  footprint is preserved (`SUSPECT_ZERO_FOOTPRINT_AREA_M2`, distinct from the absent-default token) and
  correctly yields 0 load rather than a fabricated 400 m². Tokens appended in place to
  `row['data_quality_flag']` immediately after `_total_floor_area`, and returned.

#### Manager audit — Phase A wave 1 (T01–T03) — GREENLIT 2026-07-01
- Reviewed: `semantic/provenance.py` (token build/parse w/ underscore-safe SOURCE, idempotent `|`-append,
  `set_provenance`, `add_lineage_summary`), `tests/test_provenance.py` + `tests/test_tierB_provenance.py`
  (33 passed), and the T01–T03 progress entries. All format-conformant; deviations sound and cited.
- Load-bearing property VERIFIED by reading the tests (not by accepting the report): a stored
  `cooling_cop=0` stays `0.0` (not 3.0) with a distinct `SUSPECT_ZERO_COOLING_COP` token, DEFAULT token
  absent; stored-0 footprint → 0 load, `SUSPECT_ZERO_FOOTPRINT_AREA_M2`, no fabricated 400 m². Clean
  archetype sweep emits zero default flags. **Still owed by the manager at CP-1:** the full-sim
  EUI-byte-identical confirmation via `sbatch` (unit-level evidence only, so far).
- Pre-existing failing test `test_idf_builder.py::test_zoning_follows_column_not_poly_area` CONFIRMED
  unrelated: `builder.py:325` passes 4 args to `decide_zoning_strategy` (`resolution_mode`, added in
  commit e063865); the test's mock takes 3. This arc never touches `builder.py`/`decide_zoning_strategy`,
  so wave 1 did not cause it. Belongs to the resolution-mode arc to fix — out of this arc's scope.
- Follow-ups folded into wave 2a (Sonnet): (a) instrument the `_emit_ptac` gas-heating `else 0.8`
  residual (reuse the T02 `_resolve`/`_default_flag` helpers); (b) instrument
  `refrigeration.py::_total_floor_area` (`footprint_area_m2 or 400`, `num_floors`) — the same gap as T03.
  `refrigeration.py` added to the §3 file tree to authorize the touch.
- Deferred: wiring `add_lineage_summary` into `enrich_semantics` moved from T01 to Phase B / T07 (route all
  provenance through one place first). Open question tracked for T07 — legacy tier-less tokens
  (`ASHRAE_STANDARD`/`PDE_GENERATED`) currently score observed-grade 1.0, which would overstate confidence
  once wired; T07 must decide their lineage weight before the summary is emitted on a real run.
- Model note: wave 1 ran on an Opus employee (delicate `or`→`get` semantics). Per user direction, all
  remaining Phase-A work (residuals + T04/T05/T06 → CP-1) runs on Sonnet employees.

#### T02/T03 residual closure (wave 2a) — completed 2026-07-01
- Artifacts: `openubem/idf/hvac.py` (`_emit_ptac` MODIFY), `openubem/idf/refrigeration.py`
  (`_resolve_area`/`_total_floor_area`/`assign_refrigeration` MODIFY); tests added to
  `tests/test_tierB_provenance.py` (`TestPTACGasHeatingEfficiencyProvenance`,
  `TestRefrigerationGeometryProvenance`).
- Deviations: none from the wave-2a brief. Two implementation notes: (1) In `_emit_ptac`,
  `heating_efficiency` is now resolved via `_resolve()` **only inside the `htg_type == "Gas"`
  branch** (hoisted once, before the zone loop) — Electric-coil PTACs never read this key, so
  resolving it unconditionally would have fired a spurious `DEFAULT_ASHRAE901_HEATING_EFFICIENCY_LOW`
  token on archetypes with no gas heating at all; verified SmallHotel (the only production
  archetype on the PTAC family) has `heating_coil_type="Gas"`, `heating_efficiency=0.8` in
  `hvac_cop_by_archetype.json` — real value, no flag fires in production. (2) In
  `refrigeration.py`, `assign_refrigeration` was reordered so the SuperMarket/lumped-archetype/
  eui<=0 skip guards run **before** `_total_floor_area` — mirroring the dhw/cooking
  no_dhw/no_cooking skip-ordering — so an archetype with zero refrigeration load (e.g.
  SmallOffice) never emits a geometry-default token for geometry that would never be used;
  the original code computed `_total_floor_area` unconditionally for every archetype before
  the guards, which would have been a wrong "guess flag with no consequence" once instrumented.
  `_total_floor_area`/`_resolve_area` are refrigeration's own copy (mirrors dhw.py/cooking.py's
  duplication — no shared helper existed to import). `assign_refrigeration` return type
  changed `None → list[str]` (backward-compatible; `builder.py:417` ignores the return).
- Test status: `tests/test_tierB_provenance.py` = `23 passed`. Emitter regression
  `tests/test_hvac.py`+`test_dhw.py`+`test_cooking.py`+`test_refrigeration.py` = `132 passed`
  (unchanged pass count vs. pre-wave-2a — instrumentation only, EUI-neutral).
  `tests/test_service_loads.py` = `43 passed, 5 skipped` (unchanged).
- Notes: Both residuals follow the exact T02/T03 contract: absent → default VALUE unchanged +
  `DEFAULT_ASHRAE901_HEATING_EFFICIENCY_LOW` / `DEFAULT_GEOMETRY_AREA_LOW` (LOW confidence);
  stored `0` → kept as `0` (not promoted) + a distinct `SUSPECT_ZERO_*` token; real value →
  unchanged, no token. Verified end-to-end: a SuperMarket with `footprint_area_m2=0` emits
  zero `REFRIGERATION:CASE` objects (0 load, not a fabricated 400 m² store).

#### T06 — Spatial neighbour-fill utility + MNAR density filter — completed 2026-07-01
- Artifacts: `openubem/semantic/spatial_impute.py` (NEW), `tests/test_spatial_impute.py` (NEW).
- Deviations: none on the T06 contract (neighbour-vote + kNN + MNAR guard, zero trainable
  weights, fixed k/radius convention). One designed-not-specified interface decision, flagged
  here for manager confirmation before T04/T05 consume it: the plan's kickoff describes the
  return shape as "(value, agreement_ratio, confidence_tier)" / "(distance-weighted mean,
  neighbour dispersion, confidence_tier)"; because the MNAR guard is a **hard requirement**
  that must be both machine-checkable (value never used) and provenance-visible
  (`SPATIAL_CLUSTER_MNAR_BLOCKED` actually emitted via the T01 module, not just returned as a
  label for the caller to apply later), both functions return a **4-tuple**:
  `(value, agreement_ratio_or_dispersion, confidence, gdf_out)`, where `gdf_out` is a copy of
  `gdf` with the MNAR token already appended to `data_quality_flag` for blocked rows (via
  `provenance.append_flag`). The first three elements match the kickoff's literal 3-tuple:
  callers who only need the raw signal can unpack `value, metric, confidence, _`.
- Test status: `tests/test_spatial_impute.py` = `10 passed`. Combined with T02/T03 residual
  gate: `tests/test_spatial_impute.py tests/test_tierB_provenance.py` = `33 passed`.
- Notes: **Public API** —
  `neighbour_vote(gdf, col, k=10, radius=100.0, rng=None, mnar_threshold=0.60)` (categorical:
  `use_class`, vintage bins) and `knn_fill(gdf, col, k=10, radius=100.0, mnar_threshold=0.60)`
  (continuous: `levels`, `height_m`), both in `openubem/semantic/spatial_impute.py`. Neighbour
  search = `scipy.spatial.cKDTree` on `gdf.geometry.centroid`, k=10 nearest capped at 100 m
  radius (`DEFAULT_K`/`DEFAULT_RADIUS_M` — fixed, cited, never swept against EUI per Rule 4);
  tests use a smaller synthetic-grid-scale k/radius (k=8, radius=15 m on a 10 m grid), not the
  production default. Confidence: agreement/dispersion-derived score →
  HIGH>=0.8/MEDIUM>=0.5/LOW, downgraded one tier when the row is within `radius` of the
  dataset's bounding-box edge (`_is_edge_of_bbox`) — verified a corner building drops
  HIGH→MEDIUM vs. an otherwise-identical interior building with full neighbour agreement.
  **MNAR guard verified end-to-end** (hard requirement): a row whose k/radius neighbourhood is
  >=60% missing on the target column gets `value=None`/`NaN` (both `neighbour_vote` and
  `knn_fill` — the spatial value is provably not produced, so it cannot be used) AND
  `SPATIAL_CLUSTER_MNAR_BLOCKED` appended to `gdf_out['data_quality_flag']`; a below-threshold
  (25% missing) neighbourhood is confirmed NOT blocked. Determinism: mode-tie resolution goes
  through `rng` (default `np.random.default_rng(config.RANDOM_SEED)`); a genuine 4/4 tie
  resolves identically across 5 repeated calls with the same explicit seed and across two
  calls using the implicit default-seeded rng. `knn_fill` has no randomness (distance-weighted
  mean/std are deterministic by construction). Zero new dependencies (stdlib + numpy/pandas/
  scipy.spatial.cKDTree/geopandas.centroid only); zero trainable weights (no GNN).
  **Did not start T04/T05** — stopped per the wave-2a instruction for CP-1 manager audit of
  this interface first.

#### Manager audit — Phase A wave 2a (residual closure + T06) — GREENLIT 2026-07-01
- Reviewed by READING source + tests (not the report): `spatial_impute.py`, `test_spatial_impute.py`
  (10 passed), the `_emit_ptac`/`refrigeration.py` diffs, and `test_tierB_provenance.py`'s two new
  classes (`23 passed` total). All format-conformant; deviations sound and cited.
- **Residuals EUI-neutral — VERIFIED at the value level, not just by pass-count.** Both new helpers
  map absent→default / real→real / stored-0→kept-0 — identical to the value the code produced before
  instrumentation, so no number can move. `_emit_ptac` resolves `heating_efficiency` **only** in the
  `htg_type=="Gas"` branch (electric-coil PTACs never read the key → `test_electric_coil_never_reads_
  heating_efficiency` asserts `flags == set()`); `refrigeration.assign_refrigeration` runs the
  not-SuperMarket / not-lumped / eui<=0 skip guards (lines 254–261) BEFORE `_total_floor_area` (269),
  so zero-refrig archetypes emit no geometry token (`test_non_refrig_archetype_emits_no_area_flag`
  asserts `emitted == []` + no `REFRIGERATION:CASE`). Stored-0 area → `SUSPECT_ZERO_FOOTPRINT_AREA_M2`
  + 0 cases (no fabricated 400 m² store). 132 emitter tests unchanged.
- **T06 MNAR hard requirement — VERIFIED end-to-end.** In both `neighbour_vote` and `knn_fill`, a
  neighbourhood with missingness R >= 0.60 sets `blocked_mask[i]=True; continue` **before** any value
  is computed — so the spatial value is structurally never produced (`value` stays `None`/`NaN`,
  `confidence` stays `None`) and `SPATIAL_CLUSTER_MNAR_BLOCKED` is emitted through the T01
  `provenance.append_flag` onto `gdf_out`. Tests: R=0.75 blocks (value `None` + flag present), R=0.25
  fills normally, corner building downgrades HIGH→MEDIUM, 4/4 tie is seed-deterministic. Threshold uses
  `>=` (matches spec "≥ 0.60").
- **INTERFACE DECISION RATIFIED for T04/T05 to consume.** The 4-tuple return
  `(value, agreement_ratio|dispersion, confidence, gdf_out)` — all `pandas.Series` aligned to
  `gdf.index`, populated only on eligible-missing rows, `None`/`NaN` elsewhere — is **accepted** over
  the kickoff's literal 3-tuple: forcing the MNAR token through provenance (rather than returning a
  label for the caller to apply) is the correct design and makes the guard checkable at both value and
  provenance levels. **T04/T05 contract:** unpack `value, metric, confidence, gdf_out = <fn>(...)`;
  use `gdf_out` as the frame carried forward (it already holds the MNAR flags); fill only rows where
  `value` is non-null; for MNAR-blocked / no-donor rows (`value` null) fall through to the aspatial
  tier (T04 group-mode → oldest-default; T05 group-median → global-median → 1).
- **Still owed by the manager at CP-1** (unchanged): full-sim EUI-byte-identical confirmation via
  `sbatch` (unit-level evidence only, so far) once T04/T05 land and all five CP-1 gate suites are green.

#### T04 — donor/neighbour vintage — STOPPED at grep-first tripwire (zero edits) — 2026-07-01
- Artifacts: none. Executor made **zero edits** — correct behaviour, the pinned STOP condition fired.
- What happened: the contract's arity change to `resolve_vintage` requires grepping for other
  consumers first. The executor found a **second consumer outside its touch list** —
  `tests/test_construction_sets.py` (a Step-2 "T08" construction-sets test, 7 call sites) — and halted
  and reported instead of editing an out-of-scope file. Production caller `__init__.py:304` is the only
  other consumer. Tree clean; nothing broken.
- Manager finding (contract needs re-spec before re-kick): the 7 test sites AND `__init__.py:304` all do
  **rigid 3-value unpacks** (`vintage, nan_rows, _ = resolve_vintage(...)`). The pinned "`gdf_out`-first
  3-tuple" both (a) changes position-0 from the vintage `Series` to a frame and (b) cannot also carry
  the new donor-tier provenance without becoming a 4-tuple — either way every 3-value unpack breaks.
  **Deferred to next turn** (budget wrap-up). Leaning, by analogy to how T05 kept `_impute_levels`'s
  first two branches byte-stable: keep `resolve_vintage` position-0 = `vintage_series`, position-1 =
  `remaining_nan_rows` unchanged so existing sites survive, and carry donor-tier provenance either in
  position-2 or via a separate caller-invoked provenance step (mirroring `apply_nan_vintage_provenance`).
  Precise re-spec of §6 T04 PINNED CONTRACT owed before re-dispatch.

#### T05 — group-wise stratified `levels` — completed 2026-07-01
- Artifacts: `openubem/semantic/building_classifier.py` (`_impute_levels` third branch,
  `classify_building`, `BuildingClassifier.classify`/`_build_levels_median_lookup`,
  `_EMIT_TOKENS`/`_READ_SIDE_TOKENS`); `tests/test_levels_groupwise.py` (NEW, 13 tests).
- Deviations: none from the pinned contract (lookup built in `classify()` from observed-levels rows
  only, threaded `classify_building`→`_impute_levels`; first two branches byte-unchanged; third branch
  = group-median → global-median → `(1,"LEVELS_DEFAULT_LOW")`, tokens `GROUPMEDIAN_LEVELS_MED`/
  `LEVELS_DEFAULT_LOW`). One necessary plumbing addition, flagged: `_EMIT_TOKENS`/`_READ_SIDE_TOKENS`
  drop `HEURISTIC_DEFAULT` emit-side and add it read-side-only (mirrors the file's existing
  `FALLBACK_DEFAULT` deprecation) plus add the two new tokens emit-side — else `_validate_output_schema`
  raises `SchemaError` on every third-branch row.
- Test status: `tests/test_levels_groupwise.py` = **13 passed**. `tests/test_building_classifier.py` =
  **125 passed, 3 failed** (baseline before change was 128/128 — all 3 confirmed NEW, not pre-existing).
  The 3 live in `test_building_classifier.py`, which is **outside T05's authorized touch list**, so the
  executor left them per the grep-first STOP rule (see manager audit below for the resolution plan).
- Notes: `OSM_OBSERVED` / `HEURISTIC_HEIGHT` branches byte-unchanged (only the final `return` replaced);
  `_build_levels_median_lookup` fits on `out[out["levels"].notna()]` only (no leakage), keyed by the same
  `_normalise_use_class`, `max(1, round(median))` integer guard. Zero fitted params. Did not start T04.

#### Manager audit — Phase A wave 2b (T05 VERIFIED; T04 re-spec owed) — 2026-07-01
- Reviewed by READING source + the new test (not the report): `building_classifier.py` §§34-46/121-142/
  605-683 and `tests/test_levels_groupwise.py`. Contract-conformant; the one deviation
  (`_EMIT_TOKENS`/`_READ_SIDE_TOKENS`) is necessary and follows the file's own `FALLBACK_DEFAULT`
  precedent. Tests genuinely prove the load-bearing properties: no-leakage (missing rows excluded from
  the lookup), branch-order preservation (height/observed paths re-asserted untouched), and end-to-end
  archetype-tier consequence (both-absent office in an 8-storey stock lands `LargeOffice` not
  `SmallOffice`; residential yields `GROUPMEDIAN_LEVELS_MED` + MEDIUM confidence; no-observed yields
  `LEVELS_DEFAULT_LOW`; the legacy token is asserted to never reappear). **T05 GREENLIT.**
- **Zero-fitted-params + provenance both hold:** the fill is a plain data median (nothing swept against
  EUI), and every imputed row carries a queryable token + non-HIGH confidence.
- **Resolution plan for the 3 `test_building_classifier.py` failures** (executor correctly did NOT touch
  them):
  - #1 `TestImputeLevels::test_nan_nan` and #2 `TestClassifyBuildingRow::test_rule_2b_heuristic_default_
    source` — **pure token-rename staleness**: they hard-code the retired `HEURISTIC_DEFAULT`. Mechanical
    update to `LEVELS_DEFAULT_LOW` (both fixtures have no observed-levels rows → LOW-default branch).
  - #3 `TestArchetypeCoverage30::test_default_mode_coverage` — **cross-arc (E-R3-3) consequence, decide
    deliberately**: the coverage fixture's NaN-levels school used to flat-default to `1`→`PrimarySchool`;
    the group median of its lone observed institutional row (school, levels=2) now yields `2`→
    `SecondarySchool`, so `PrimarySchool` is unreachable in that fixture. Neither value is "true" (levels
    unknown). Correct fix = make `PrimarySchool` reachable via an **observed** levels=1 school row, not an
    imputation default — a fixture edit that touches the E-R3-3 `synthetic_30_archetype_coverage.gpkg`
    coverage guarantee. **Coordinate with the E-R3-3 arc before editing.**
- **Next manager actions (deferred to next turn, budget wrap-up):** (1) re-spec §6 T04 PINNED CONTRACT
  (position-stable `resolve_vintage`) and re-dispatch T04; (2) authorize a Sonnet employee to fix the 3
  `test_building_classifier.py` failures per the plan above (with the E-R3-3 coordination on #3); (3) at
  CP-1, the manager-owed `sbatch` full-sim EUI-byte-identical confirmation once T04 lands and all five
  gate suites (`test_tierB_provenance`, `test_vintage_donor`, `test_levels_groupwise`,
  `test_spatial_impute`, `test_provenance`) are green.

#### Manager — T04 PINNED CONTRACT re-spec to v2 (position-stable) + wave-2b cleanup dispatch — 2026-07-01
- **T04 re-spec DONE (manager reasoning, this session).** Re-grepped ground truth from the repo root
  (earlier "no matches" were an artifact of the `deepResearch` cwd): `resolve_vintage` lives in
  `openubem/semantic/construction_sets.py:117`, returns `(vintage_series, nan_rows, <unused Index>)`; the
  8 consumers (`__init__.py:304` + `test_construction_sets.py` L72/83/122/152/174/188/211) all do rigid
  3-value unpacks reading pos-0 = vintage `Series`, pos-1 = NaN `Index`, pos-2 = discarded. §6 T04 now
  carries **PINNED CONTRACT v2**: keep positions 0/1 byte-identical, repurpose only the unused pos-2 into a
  per-row token `Series` — no arity break, so the v1 STOP is resolved. Verified only **one** test genuinely
  changes behaviour under the donor step (`test_resolve_vintage_nan_year` L78 — its NaN row has an
  observed same-archetype sibling → tier-2 group-mode fills `90.1-2019`); v2 authorizes exactly that one
  surgical test edit (reduce to a donorless single-row frame) and forbids touching any other test there.
- **Dispatched two Sonnet-5 employees in parallel** (independent file sets, no write overlap):
  - **Employee A — T04 execution** against §6 PINNED CONTRACT v2: `construction_sets.py` (donor step +
    `append_vintage_donor_flags`), `__init__.py:304/331` caller, the one authorized `test_construction_sets.py`
    edit, NEW `tests/test_vintage_donor.py`. STOP tripwires (a)/(b)/(c) as pinned.
  - **Employee B — wave-2b test cleanup**: #1/#2 mechanical `HEURISTIC_DEFAULT`→`LEVELS_DEFAULT_LOW` renames
    in `test_building_classifier.py`; #3 diagnose the fixture and make `PrimarySchool` reachable via an
    OBSERVED levels=1 school row, with a hard STOP-and-report before any edit that would change an E-R3-3
    boundary assertion or force a full `synthetic_30_archetype_coverage.gpkg` regeneration.
- **Both audited on return** (next entries). Zero-fitted-params + provenance remain binding on Employee A.

#### Wave-2b test cleanup — completed 2026-07-01
- #1: TestImputeLevels::test_nan_nan — updated assertion HEURISTIC_DEFAULT -> LEVELS_DEFAULT_LOW (pure token-rename staleness).
- #2: TestClassifyBuildingRow — renamed test_rule_2b_heuristic_default_source -> test_rule_2b_levels_default_low_source, updated expected src to RULE_RESIDENTIAL_TIER,LEVELS_DEFAULT_LOW, added docstring note (single-row classify_building has no group-median lookup -> third branch).
- #3: fixed. Diagnosis: the `synthetic_30_gdf` fixture-generation code (embedded in tests/test_building_classifier.py ~793-868; regenerates tests/fixtures/synthetic_30_archetype_coverage.gpkg unconditionally each run) had row 14 (school, levels=pd.NA) relying on pre-T05 flat-default-to-1. Under T05's group-median lookup, row 15 (school, levels=2, OSM_OBSERVED) was the sole observed school row -> levels_group_median["school"]=2 -> row 14's NaN imputed to 2 (GROUPMEDIAN_LEVELS_MED) -> SecondarySchool, making PrimarySchool unreachable. Fix: row 14 -> levels=1, provenance_levels="OSM_OBSERVED" (observed 1-story school), matching the E-R3-3 Primary(1)/Secondary(>=2) rule.
- Test status: test_building_classifier.py = 128 passed/0 failed; test_levels_groupwise.py = 13 passed/0 failed.
- **Manager audit — GREENLIT.** Verified by reading the three edits + two independent cross-checks: (a) global observed-levels median unchanged (5 before/after — [2,5,5,12,2,25,45,2] vs [1,2,2,2,5,5,12,25,45]), so no other NaN row's fallback shifts; (b) only test_building_classifier.py consumes the fixture (no other test loads the .gpkg from disk), so E-R3-3's coverage guarantee is fully re-exercised in-file (TestExactBoundaries + TestArchetypeCoverage30 green). Fix is E-R3-3-aligned (observed level count drives Primary/Secondary), not test-weakening. No .gpkg hand-edit — regenerated deterministically from the corrected Python row on the next run.

#### T04 — donor/neighbour vintage — completed 2026-07-01
- Artifacts: `openubem/semantic/construction_sets.py` (resolve_vintage rewrite + NEW
  append_vintage_donor_flags); `openubem/semantic/__init__.py` (3 pinned touch-points);
  `tests/test_construction_sets.py` (test_resolve_vintage_nan_year reduced to donorless
  single-row, per the one authorized edit); `tests/test_vintage_donor.py` (NEW, 9 tests).
- Deviations: none from PINNED CONTRACT v2. Two implementation notes flagged for the
  auditor: (1) tier-1 spatial donor is guarded by `has_geometry = hasattr(gdf, "geometry")
  and "geometry" in gdf.columns` — plain pd.DataFrame callers (all pre-existing
  test_construction_sets.py fixtures) skip tier 1 entirely and fall straight to tier 2/3;
  required for backward-compat since knn_fill's `_build_tree` calls `.geometry.centroid`
  unconditionally once n>=2, and is a pure no-op on production GeoDataFrame input (real
  callers always have geometry). (2) Per the "How" line ("neighbour-agreement (T06) →
  HIGH/MED"), only knn_fill confidence tiers HIGH/MEDIUM are accepted as tier-1 hits; a
  successful-but-LOW-confidence knn_fill value falls through to tier 2 group-mode — the
  contract only names HOTDECK_NEIGHBOR_HIGH/MED as valid tier-1 tokens, no LOW variant.
- Test status: `pytest tests/test_construction_sets.py tests/test_vintage_donor.py -q` →
  31 passed. `pytest tests/test_step22_orchestrator.py -q` (full file incl. the 3
  `@pytest.mark.slow` 2,400-row sweeps) → 21 passed. Combined: 52 passed, 0 failed.
- Notes: Position-2 is a `pd.Series[str]` indexed over `nan_rows` (position-1), literal
  tokens `HOTDECK_NEIGHBOR_HIGH`/`HOTDECK_NEIGHBOR_MED` (tier 1, from knn_fill's own
  confidence tier), `GROUPMODE_MED` (tier 2, flat MED per spec), `VINTAGE_NAN_PERMISSIVE_DEFAULT`
  (tier 3, unchanged legacy token/value). Tier-2 mode-tie break uses a fresh
  `np.random.default_rng(config.RANDOM_SEED)` per call (determinism verified). Tier 1
  stratifies via `gdf.groupby(strat_col, dropna=False)` and calls `knn_fill(group, "year_built")`
  per stratum (production `DEFAULT_K`/`DEFAULT_RADIUS_M`, never overridden) — donors are
  observed-year rows only (leakage-safe); MNAR-blocked rows fall through, verified in
  `TestMnarBlocksSpatialFill`. STOP-grep (condition b) result: one hit outside the touch
  list — `test_step22_orchestrator.py::test_flag_token_append_only_for_nan_vintage` — but its
  NaN row (`SmallOffice`) and observed row (`MediumOffice`) are different `archetype_id`
  strata (no same-stratum donor), so the legacy token is untouched and no STOP fired;
  reverified green (21 passed). `append_vintage_nan_flag`/`apply_nan_vintage_provenance`
  untouched, both still directly unit-tested and green.

#### Manager audit — T04 GREENLIT — 2026-07-01
- Reviewed by READING source (not the report): `construction_sets.py:126-251` (resolve_vintage
  three-tier fill + 389-418 append_vintage_donor_flags), `__init__.py:304/318/331`,
  `test_construction_sets.py:78-84` (the one authorized edit), and all 9 tests in
  `test_vintage_donor.py`. Contract-conformant on every pinned point.
- **Position-stability holds (the whole point of v2):** signature is `-> tuple[Series, Index,
  Series]`; pos-0 = vintage `Series` (now carrying donor fills), pos-1 = `all_nan_rows` =
  Index of EVERY originally-NaN row (unchanged meaning), pos-2 = new provenance `Series`. All
  8 rigid 3-value unpack sites survive; `__init__.py:318` still feeds pos-1 to
  `apply_nan_vintage_provenance`, so envelope provenance stays HEURISTIC for ALL originally-NaN
  rows regardless of donor tier — exactly as the contract mandated (a donor vintage still
  selects a heuristic envelope). `__init__.py:331` swaps the blanket nan-flag for the per-row
  `append_vintage_donor_flags`; tier-3 rows keep byte-identical `VINTAGE_NAN_PERMISSIVE_DEFAULT`,
  only donor rows read HOTDECK/GROUPMODE (matches contract line 320).
- **Zero-fitted-params holds:** tier-1 calls `knn_fill` with T06's fixed `DEFAULT_K`/
  `DEFAULT_RADIUS_M` (never overridden); the HIGH/MEDIUM gate reuses T06's already-ratified
  thresholds (no new numeric constant); tier-2 tie-break RNG is the fixed `config.RANDOM_SEED`.
  Nothing is swept against validation EUI. `_YEAR_BINS` are the DESIGN-mandated vintage edges,
  not fitted.
- **Provenance holds:** every donor-filled and defaulted row carries a queryable token that
  flows to `data_quality_flag`; confidence rides the token suffix (HOTDECK…_HIGH/_MED,
  GROUPMODE_MED). Leakage-safe by construction (donors = observed-year rows only) and
  MNAR-guarded (T06's >=60% local-missingness block routes to tier 2).
- **Independently checked the STOP-grep call:** `test_flag_token_append_only_for_nan_vintage`
  passes because its lone observed row is a *different* `archetype_id` stratum than the NaN
  row, so no same-stratum donor exists and the row correctly lands on tier-3 legacy token —
  this is genuinely NOT STOP condition (b) (which fires only when a same-stratum observed donor
  exists yet a test still asserts the legacy token). Employee reasoned it through correctly
  rather than blindly editing an out-of-scope test. The two flagged implementation notes are
  both sound: the `has_geometry` guard is a necessary backward-compat measure (production frames
  always carry geometry, so tier 1 is live in the real pipeline), and routing LOW-confidence
  knn_fill to tier 2 is conservative and contract-faithful. **T04 GREENLIT.**

#### CP-1 EUI half — exact IDF field-diff — completed 2026-07-01
- Artifacts:
  - `<scratchpad>\build_step2_shared.py` / `build_step3_after.py` / `build_step3_before.py` / `diff_idfs.py`
  - `scratch\shared\{enriched_gdf.pkl, schedule_lib.pkl}` (25-building, 24-archetype fleet, fixed climate_zone=3A / tests/fixtures/synthetic.epw)
  - `scratch\idfs_after\idfs\*.idf` (25, current Tier-B tree) / `scratch\idfs_before\idfs\*.idf` (25, e063865 4-file swap)
  - `scratch\repo_baseline\openubem\` (full package copy, only idf/{hvac,dhw,cooking,refrigeration}.py replaced with e063865 content; filecmp-verified byte-identical to real repo elsewhere)
- Deviations:
  - Replaced fixture's 1x1 m placeholder geometry with a synthesized square (side=sqrt(footprint_area_m2)) per building, done ONCE upstream of the toggle point in shared Step 2 — required because `openubem/geometry/footprint.py::validate_simplified()` rejects `poly.area<=20 m2` (fixture is classifier-test-only geometry). Held byte-identical across both builds; cannot affect the field-diff.
  - Fixed climate_zone="3A" / epw_path=tests/fixtures/synthetic.epw / provenance_climate_zone="DEFAULT" assigned uniformly (fixture has no real-world coords) — held constant across both builds.
- Test status: not pytest — bespoke field-diff harness per manager spec. 25/25 IDFs generated in BOTH builds; `diff_idfs.py` + independent `diff -rq` (exit 0) + md5sum cross-check all report 0/25 files with ANY difference (byte-identical, not just field-identical).
- Notes: Verdict = instrumentation-only CONFIRMED for this fleet/data. Isolation invariant held: Step 2 enrichment run ONCE and persisted; Step 3 built twice from the SAME gdf toggling ONLY the 4 Tier-B idf modules; baseline swap done in a scratch package copy whose sys.path was verified to resolve inside scratch, filecmp confirming only the 4 intended files differ — so T04/T05 donor fills + classifier + archetype JSON were constant. `data_quality_flag` never leaks into IDF text (only the manifest parquet). Dormant (verified non-firing) risk: `_resolve`/`_resolve_area` correctly preserve a literal `0` and fix a `NaN`-truthiness leak present in the e063865 `x.get(k) or default` idiom — these WOULD change emitted field values IF any ASHRAE default table or `footprint_area_m2` ever carried a literal 0/NaN; verified none currently do (checked hvac_cop_by_archetype.json, hvac_systems_by_archetype.json across EVERY archetype + fixture footprint_area_m2). Main-tree 4 idf files confirmed byte-unchanged (line + provenance-hit counts match pre-run baseline).

#### Manager — CP-1 CHECKPOINT MET — 2026-07-01
- **All three CP-1 conditions satisfied; Phase A (T01–T06) closed.** Audited each against source, not just employee reports.
- **Cond.1 — five gate suites green: MET.** 75/75 (`test_tierB_provenance` 23, `test_vintage_donor` 9, `test_levels_groupwise` 13, `test_spatial_impute` 10, `test_provenance` 20), 0 failed/errored/deselected.
- **Cond.2b — MNAR block deactivates: DISCHARGED at unit level (no cluster needed).** Re-read `test_spatial_impute.py::TestMNARGuard` (R=0.75≥0.60 → spatial value unused, confidence None, `SPATIAL_CLUSTER_MNAR_BLOCKED` stamped; R=0.25 → fills, flag absent) and `test_vintage_donor.py::TestMnarBlocksSpatialFill` (MNAR neighbourhood routes vintage to tier-2 GROUPMODE_MED, not hotdeck). Guard observable only via `data_quality_flag`; `MNAR_THRESHOLD=0.60`. These tests assert exactly that behaviour → the guard demonstrably deactivates spatial fill.
- **Cond.2a — HVAC EUI unchanged (instrumentation-only): CONFIRMED.** Method ratified by the user = exact LOCAL IDF field-diff (supersedes the plan's original `sbatch` full-sim). Recon established no pre-Tier-B baseline EUI CSV exists but `e063865` IS the pre-instrumentation baseline (Tier-B uncommitted). Rationale: identical IDFs ⟹ identical EUI on a deterministic simulator, and a field-level IDF diff has no ≤2 kWh/m² platform-rounding blind spot a cluster EUI-harvest carries → strictly stronger AND zero cluster cost. Result: 25/25 IDFs byte-identical over a 24-archetype coverage fleet with the isolation invariant rigorously verified (see entry above).
- **The caveat does NOT block the gate.** The employee enumerated the ONLY two behavioural divergences between Tier-B and e063865 (literal-0 preservation; NaN-leak fix) — both correctness IMPROVEMENTS — and proved neither fires on any current archetype's data. So Cond.2a is confirmed by empirical byte-identity PLUS exhaustive divergence-enumeration PLUS table-level non-firing proof (this also closes the 24-vs-30 archetype coverage gap). Carry-forward: log both divergences as expected/correct behaviour for the M09 validation harness so a future dataset carrying 0/NaN in a COP/area field is not mistaken for a Tier-B regression.
- **T07–T13 (Phases B–E) remain GATED behind explicit user greenlight.** No Phase-B work dispatched.

<!--
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + DESIGN/research cite>
- Test status: <pytest summary>
- Notes: <auditor-relevant>
-->
