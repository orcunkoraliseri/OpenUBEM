# Results — Input-Parameter Imputation ("OpenUBEM AI")

This folder holds the phase-by-phase results of the **input-parameter imputation** arc — the "OpenUBEM
AI" subsystem that fills missing building inputs (vintage, morphology, HVAC/DHW/cooking defaults) with
full provenance, under the arc's non-negotiable **zero-fitted-parameters** rule (no imputer is ever
tuned against an EUI target).

Each phase has its own **self-contained** results document with embedded figures. This README is the
entry point that ties the five together.

> **The arc in one line:** Phase A proved the imputer is **safe**, Phase B proved it is **accurate**,
> Phase C showed classical **ML does not (yet) beat** the validated statistical tier on the EUI-relevant
> target (so ML ships opt-in / off), Phase D **shipped external-data fusion** enabled-by-default
> (byte-identical without a configured source), and Phase E **ruled the advanced frontier out** of the
> default pipeline with evidence. All of it with zero fitted parameters.

> **Quantitative summary:** [`arc_quant_summary.png`](arc_quant_summary.png) storyboards all five
> phases (safe → accurate → tested → shipped → ruled-out) in one figure, built only from the metrics
> already reported in each phase's RESULTS doc.

---

## The five phases at a glance

| Phase | Question it answers | Headline result | Status | Doc |
|---|---|---|---|---|
| **A** (CP-1) | Is the statistical imputer **safe** — does adding provenance change any energy? | 76/76 unit tests · **25/25 IDFs byte-identical** vs baseline `e063865` | ✅ CLOSED (CP-1 MET) | [`phase_A/RESULTS_phaseA.md`](phase_A/RESULTS_phaseA.md) |
| **B** (CP-2) | Is it **accurate** on real cities — does the imputed input reproduce ground-truth EUI? | nyc_centre N=32 **NMBE +0.49% / CV(RMSE) 1.71%** · la_urban N=124 **+0.08% / 0.61%** (both PASS 5%/15%) | ✅ CLOSED (CP-2 FULLY MET) | [`phase_B/RESULTS_phaseB.md`](phase_B/RESULTS_phaseB.md) |
| **C** (CP-3) | Does classical **ML** recover the attribute better **without worsening EUI**? | `knn` wins the attribute leg (marginal) but **EUI do-no-harm FAILS — NMBE −5.51%** (167/167 shift down) | ⏸ built-but-**OFF** (CP-3 not fully met, user-accepted) | [`phase_C/RESULTS_phaseC.md`](phase_C/RESULTS_phaseC.md) |
| **D** (CP-4) | Can **external-data fusion** fill morphology/semantic gaps with authoritative values + provenance? | real Overture LIVE_SMOKE (1,667 bldgs) **`height_m` 87.6% ground-truth fill** · **shipped enabled-by-default**, byte-identical without a source · gate 171/0 | ✅ CLOSED (CP-4 MET + SIGNED) | [`phase_D/RESULTS_phaseD.md`](phase_D/RESULTS_phaseD.md) |
| **E** | Is any **advanced frontier** (deep-generative / GNN / LLM / TabPFN) warranted? | deep-gen/GNN/LLM **ruled out with evidence**; TabPFN **NOT READY** (experimental-only) — **none ship** | 📄 DOCUMENTED-DEFERRED | [`phase_E/RESULTS_phaseE.md`](phase_E/RESULTS_phaseE.md) |

---

## Phase A — the imputer is **safe** (CP-1)

Phase A builds the statistical imputer and closes the provenance gaps. It is **instrumentation-only**:
its result is a proof that adding traceability changes **zero** simulated energy. Converting
`.get(k) or d` → `.get(k, d)` + a tracked flag added provenance to HVAC/DHW/cooking defaults without
touching any physics — proven by an exact local IDF field-diff.

- ✅ **76 / 76** unit tests green (five gate suites)
- ✅ **25 / 25** IDFs byte-identical vs the pre-work baseline (`e063865`)

![Phase A validation gate results](phase_A/phaseA_test_results.png)

→ Full detail, provenance-token taxonomy, and the three highest-leverage fills: **[`phase_A/RESULTS_phaseA.md`](phase_A/RESULTS_phaseA.md)**

---

## Phase B — the imputer is **accurate** (CP-2)

Phase B builds the **"OpenUBEM AI" routing subsystem** (`impute_missing` — one entry point, tier order,
strict mode) and the **M09 validation harness** (mask-and-recover + downstream-EUI A/B), then *measures*
the Phase-A imputer with them on real OSM cities. The imputed target was `year_built` (EUI-relevant
through the DOE construction sets); metrics are paired ASHRAE-Guideline-14, held-out-only.

| Cell | N | NMBE | CV(RMSE) | Gate (5% / 15%) |
|---|---|---|---|---|
| **nyc_centre** (GATE) | 32 | **+0.49%** | **1.71%** | ✅ PASS |
| **la_urban** (robustness) | 124 | **+0.08%** | **0.61%** | ✅ PASS |

![CP-2 downstream-EUI accuracy](phase_B/phaseB_accuracy_cp2.png)

→ Full detail, the M09 two-leg harness, and the 121/121 deliverable tests: **[`phase_B/RESULTS_phaseB.md`](phase_B/RESULTS_phaseB.md)**

---

## Phase C — classical ML, kept **built-but-off** (CP-3)

CP-2 already exhausted the EUI headroom, so Phase C asks a narrower question: does a 6-method sklearn
imputer recover the vintage/morphology attribute *more accurately at the attribute level* — **without
worsening** the downstream EUI? CP-3 is an **attribute-recovery** gate with an EUI **do-no-harm** guard;
it ships only if **both** legs pass.

- **Leg 1 (attribute):** `knn` beats Phase-A on `year_built` (MAE 26.43 → 25.14) and `levels` (9.18 → 8.39) — **MET, but marginal.**
- **Leg 2 (EUI do-no-harm):** real cluster A/B on 167 nyc_centre buildings → **NMBE −5.51% FAILS** the ±5% gate (CV(RMSE) 7.93% passes). All 167/167 buildings shift **downward** — a systematic bias, not scatter.

![CP-3 verdict — one leg won, one leg lost](phase_C/phaseC_cp3_verdict.png)

**Decision (user, 2026-07-03):** *"one method does not need to cover all input parameters, no worries,
keep it."* → the ML tier is **accepted BUILT-BUT-OFF (opt-in)**; `ml` stays outside the default
`IMPUTE_ENABLED_TIERS`, so the default pipeline and the CP-1 byte-identity are untouched. The registry
is per-target, so a future user can point a per-target imputer where it does clear do-no-harm.

→ Full detail, the 6-method leaderboard, the EUI A/B, and the `mice`/`linear` extrapolation footgun: **[`phase_C/RESULTS_phaseC.md`](phase_C/RESULTS_phaseC.md)**

---

## Phase D — external-data **fusion**, shipped (CP-4)

Phase D adds the **fusion** tier: it fills missing morphology/semantic attributes
(`height`/`levels`/`year_built`/`use_class`) with **authoritative external values** (Overture / LiDAR /
assessor) joined first-hit-wins, each carrying a `FUSED_<SOURCE>_HIGH|MED` provenance token; a join miss
falls through to the validated imputation tiers. A fusion join is a *data-acquisition observation*, so it
respects **zero-fitted-parameters** by construction (a structural no-EUI guard blocks any EUI column).

- **CP-4 gate (real Overture LIVE_SMOKE, release `2026-06-17.0`, 1,667 NYC-centre buildings, anonymous DuckDB/S3):** `height_m` **87.6% ground-truth fill** (all `FUSED_OVERTURE_HIGH`); the live run **caught a real synthetic≠live schema bug** — Overture has **no `year_built` column** at all.
- **Shipped enabled-by-default** (`IMPUTE_ENABLED_TIERS = ("fusion","spatial","statistical")`) — **byte-identical** for any run without a configured source (proven by two byte-identity tests). Gate **171/0**. License guard green (279 KB CDLA-Permissive slice).

![Phase D — CP-4 verdict](phase_D/phaseD_cp4_verdict.png)

→ Full detail, the per-attribute fill rates, and the source-registry architecture: **[`phase_D/RESULTS_phaseD.md`](phase_D/RESULTS_phaseD.md)**

---

## Phase E — the advanced frontier, **ruled out with evidence** (documented-deferred)

Phase E is the arc's closing question: is any *data-driven frontier* method warranted? Judged against the
arc's four filters (zero-fitted-params · reproducible/offline · provenance-emitting · viable at our
hundreds-to-low-thousands cell scale), **none ship**:

- **Deep-generative** (GAIN/VAE/DAE/TabDDPM/tab-transformer) → **SKIP** — classical MissForest/MICE dominate below n≈30 k; the one UBEM precedent used ~2.2 M buildings.
- **Spatial GNN** → **REJECT** — the real spatial signal is already captured by the Phase-A neighbour-vote/kNN tier; a GNN adds thousands of fitted weights (violates zero-fitted-params) for a marginal gain.
- **LLM** → **FIRM DISQUALIFICATION** — hallucination + no provenance + non-determinism/API drift.
- **TabPFN** → **NOT READY** — the only architecturally-compatible method, but no building-domain validation exists; quarantined to an **opt-in isolated experimental track** (MAR geometry/semantics only, same CP-3-style gate before any promotion).

→ Full rulings, the four-filter table, and the TabPFN experimental-track contract: **[`phase_E/RESULTS_phaseE.md`](phase_E/RESULTS_phaseE.md)**

---

## Folder map

```
results/
├── README.md                          ← this file (arc entry point)
├── arc_quant_summary.png              ← 5-column quantitative storyboard, all phases
├── phase_A/   safe · CP-1 MET
│   ├── RESULTS_phaseA.md               + 4 figures + phaseA_gate_tests_output.txt
│   └── phaseA_{test_results,provenance_taxonomy,routing_cascade,three_fixes}.png
│       + phaseA_quant_provenance.png   ← quantitative before/after (traceability at 0 kWh/m²)
├── phase_B/   accurate · CP-2 FULLY MET
│   ├── RESULTS_phaseB.md               + 4 figures
│   └── phaseB_{accuracy_cp2,validation_harness,test_results,routing_subsystem}.png
│       + phaseB_quant_accuracy.png     ← quantitative before/after (NMBE/CV(RMSE) vs gates)
│       + phaseB_scatter_year_built.png ← predicted-vs-actual year_built, real recovered pairs
├── phase_C/   ML built-but-off · CP-3 NOT fully met
│   ├── RESULTS_phaseC.md               + 4 figures
│   └── phaseC_{cp3_verdict,leaderboard,eui_donoharm,footgun}.png
│       + phaseC_quant_{leaderboard,eui_beforeafter}.png  ← quantitative leaderboard + EUI dumbbell
│       + phaseC_scatter_{year_built,levels}.png          ← predicted-vs-actual, Phase-A vs knn
├── phase_D/   fusion shipped · CP-4 MET
│   ├── RESULTS_phaseD.md               + 4 figures
│   └── phaseD_{cp4_verdict,fillrate,architecture,byte_identity}.png
│       + phaseD_quant_fillrate.png     ← quantitative fill-rate per attribute
└── phase_E/   frontier ruled out · documented-deferred
    ├── RESULTS_phaseE.md               + 4 figures (documentation only — no run)
    └── phaseE_{four_filters,scale_gap,frontier_verdict,tabpfn_contract}.png
        + phaseE_quant_scalegap.png     ← quantitative data-scale number line
```

**Source of record:** the parent plan `../PLAN_input_imputation_implementation.md` §8 progress log
(Phase A/B), `../docs_Done/PLAN_phaseC_ml_imputer.md` §8 (Phase C), `../docs_Done/PLAN_phaseD_fusion.md` §8 (Phase D), and
the deep-research `RESULT_M05/M06/M10` Part-C rulings (Phase E). The `docs/PROJECT_CHECKLIST.md` §G is the
single-surface arc tracker. All numbers in these result docs are verbatim from those logs — nothing is
re-derived or invented here.
