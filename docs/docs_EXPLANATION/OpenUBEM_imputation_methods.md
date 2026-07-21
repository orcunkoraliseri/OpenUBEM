# OpenUBEM — Missing-Input Imputation Methods

**What this document is:** a plain-language reference for the part of OpenUBEM that **fills
the gaps in the input data** — the "OpenUBEM AI" imputation subsystem. It explains why
imputation is needed at all, the four-tier method cascade it uses, how those tiers map to the
imputation arc's phases (A–E), and — the reason this document exists — the **honest limits of
the Phase-B and Phase-C methods** (why the imputed values form a flat band instead of tracking
the real spread), and why those limits are accepted rather than "fixed". For the pipeline
overview see [`OpenUBEM_fundamentals.md`](OpenUBEM_fundamentals.md); for the full catalogue of
inputs and their sources see [`OpenUBEM_inputs_reference.md`](OpenUBEM_inputs_reference.md);
for the binding specs see `docs/docs_main/` (DESIGN §3E) and the arc record under
`docs/docs_ACTIVE/input/imputation/`.

One thing is always true about this subsystem: **it never invents a parameter.** Every fill
is either a real observed value copied from elsewhere, or a draw/estimate from the observed
data's own distribution — never a coefficient tuned to make a result look better. This is the
project's non-negotiable *zero-fitted-parameters* rule (see §2), and it is also the root cause
of the limit described in §6.

---

## 1. Why OpenUBEM needs imputation

OpenUBEM builds a physics model of **every** building from OpenStreetMap footprints. But OSM
is crowd-sourced and **incomplete**: many buildings arrive with a geometry but no
`building:levels`, no `height`, and no `start_date` (year built). The downstream physics
cannot proceed with holes:

| Missing attribute | What breaks downstream if left empty |
|---|---|
| `levels` (floor count) | No floor area (`footprint_area_m2 × levels`) → no EUI denominator, no zoning |
| `year_built` | No vintage → no envelope standard (U-values, infiltration) to assign |
| `height_m` | No massing to extrude → no shading, no volume |

So **Stage 2 (Semantic Enrichment)** runs an imputation step that fills these holes before the
building is turned into an EnergyPlus model. The goal is not archaeological accuracy on any one
building — it is to give every building a **plausible, provenance-tagged** value so the fleet
can be simulated and rolled up to a neighbourhood total.

---

## 2. The one rule that governs everything: zero fitted parameters

Every method below obeys a single hard constraint: **no parameter is ever fitted to make a
result match a target.** Imputation may copy an observed value, take a group median, sample a
fitted-on-observed-data distribution, or average nearby neighbours — but it may never learn a
correction coefficient, and the result of an imputation is **never fed back** to tune a
threshold or bound. This keeps the whole platform reproducible and free of circular
calibration. It is also *why* the imputer behaves the way §6 describes: a method that is
forbidden from fitting will, by construction, fall back on central tendency.

---

## 3. The four-tier cascade — first hit wins

Imputation is a **priority cascade** (`openubem/semantic/imputation.py`,
`impute_missing(...)`). For each missing cell it tries the tiers in order and **stops at the
first tier that yields a value**, emitting a provenance token and a confidence tier alongside
the fill so every value is traceable:

| Order | Tier | What it uses | Enabled by default? | Confidence |
|---|---|---|---|---|
| 1 | **`fusion`** | Real ground-truth values from **external datasets** (Overture Maps height/levels, LiDAR, municipal assessor) joined by location | ✅ yes (no-op when no source is configured) | HIGH / MED (`FUSED_<SOURCE>_*`) |
| 2 | **`spatial`** | A **donor value from nearby observed neighbours** of the same building — distance-weighted | ✅ yes | MED |
| 3 | **`statistical`** | The **observed distribution** of the attribute (KDE / PDE / group-mode) | ✅ yes | LOW–MED |
| — | **`ml`** | Multivariate machine-learning regression/classification (6 methods, §4) | ❌ **opt-in / off by default** | — |

`fusion` is the only tier that can produce a *ground-truth* value; the other three produce
*estimates* from the data OpenUBEM already has. The cascade is intentionally ordered
**best-evidence-first**: a real external measurement beats a neighbour's value, which beats a
distribution statistic.

---

## 4. What each tier actually does

### 4.1 `fusion` — copy a real value from an external dataset
A source registry (`openubem/semantic/fusion.py`) queries external datasets by location and
copies a genuine measured value when one exists — e.g. Overture Maps building height for a
building OSM left blank. First-hit-wins across sources, always tagged `FUSED_<SOURCE>_HIGH/MED`,
never `LOW`. When no source is configured (the common case), the tier is a structural no-op and
the run is byte-identical to fusion-off. *(Arc Phase D — see §5.)*

### 4.2 `spatial` — borrow from the neighbours
For a building missing an attribute, find its **observed spatial neighbours** and take a
**distance-weighted average of their real values** (`_spatial_tier`). This is a *donor* method:
the fill is anchored in actual nearby buildings, so it respects local context (a block of
pre-war walk-ups imputes to a pre-war vintage). It falls back to a group-mode when no observed
neighbour is in range.

### 4.3 `statistical` — draw from the observed distribution
When there is no neighbour to borrow from, fall back to the attribute's **own observed
distribution** (`impute_column`):

- **KDE** (Kernel Density Estimation) — when the attribute is *partly* observed: fit a density
  on the observed values and sample the missing positions from it.
- **PDE** (Prior-Distribution Estimation) — when the attribute is *entirely* missing in this
  group: fall back to a bounded prior from the standards.
- **group-mode / median** — the categorical/robust fallback: the most common (or median)
  observed value in the stratum.

All draws are clamped to the observed `[min, max]` so no estimate extrapolates past real data.

### 4.4 `ml` — multivariate learning (opt-in, off by default)
A registry of **six** methods behind one interface (`_ml_tier`): `knn`, `missforest`, `rf`,
`histgbm`, `mice`, `linear`. These use *all* available features (geometry, use-class, location)
to predict the missing attribute, rather than one column at a time. This tier is **built but
disabled by default** — see §6–§7 for exactly why. *(Arc Phase C.)*

---

## 5. How the tiers map to the imputation arc's phases (A–E)

The subsystem was built and validated in a five-phase arc. "Phase B" and "Phase C" — the
subject of the user's question — are **arc phases**, not pipeline stages:

| Arc phase | What it delivered | Methods involved | Status |
|---|---|---|---|
| **A** | The base cascade (`spatial` + `statistical`) + the mask-and-recover validation harness | KDE / PDE / group-mode / spatial donor | ✅ shipped (CP-1) |
| **B** | **Downstream-EUI validation** of the base cascade on real cities | same as A (`spatial` + `statistical`) | ✅ shipped (CP-2): NYC NMBE **+0.49%**, LA **+0.08%** |
| **C** | The **`ml` tier** — the 6-method registry, gated on a do-no-harm test | `knn` / `missforest` / `rf` / `histgbm` / `mice` / `linear` | ⏸ **built-but-off / opt-in** (CP-3 not fully met) |
| **D** | The **`fusion` tier** — external-data fusion (Overture/LiDAR/assessor) | source registry | ✅ shipped + enabled by default (CP-4) |
| **E** | Frontier methods (deep-generative, GNN, LLM, TabPFN) | — | ⛔ documented-deferred (none enter the default pipeline) |

So **Phase-B methods = the `spatial` + `statistical` tiers**, and **Phase-C methods = the `ml`
tier**. Both share the limit described next.

---

## 6. The known limit of the Phase-B and Phase-C methods: variance collapse

### 6.1 The symptom
On a predicted-vs-actual scatter of a held-out attribute (`year_built`, `levels`), the imputed
points do **not** follow the 1:1 diagonal — they form a **flat horizontal band**. The real
buildings on the X-axis are widely varied; the imputed values on the Y-axis are nearly
constant. *(Figures: `docs/docs_ACTIVE/input/imputation/results/phase_B/phaseB_scatter_year_built.png`
and `.../phase_C/phaseC_scatter_levels.png`.)*

### 6.2 What is really happening — measured, not eyeballed
The original data is genuinely spread; the imputed data is collapsed toward the middle. Re-run
of the mask-and-recover harness on the committed cells:

| Case | Original data (X, real) | Imputed data (Y) | σ(imputed) / σ(real) |
|---|---|---|---|
| `year_built`, nyc_centre | 1901→2013, σ=33.6 y, IQR=61 y, 29 distinct | σ=14.7 y, **IQR=0.0** | **0.44** |
| `year_built`, la_urban | 1908→2007, σ=22.9 y, IQR=27 y, 49 distinct | σ=9.7 y, IQR=3.3 | 0.42 |
| `levels`, pooled (statistical) | 1→63 floors, σ=13.4, IQR=15, 39 distinct | σ=4.2, **IQR=0.0** | 0.31 |
| `levels`, pooled (`ml`/knn) | same (σ=13.4) | σ=5.1, IQR=5.1 | 0.38 |

The most telling number is **IQR = 0.0**: for `year_built` in nyc_centre and for `levels` under
the statistical tier, the **middle 50% of imputed values are a single constant.** The imputed
distribution carries only **31–44%** of the real variance. That flat middle *is* the horizontal
band.

### 6.3 Why this is inherent, not a bug
Any method restricted to producing **one estimate per building** — a group mode/median
(statistical), a distance-weighted neighbour average (spatial), or a k-nearest-neighbour mean
(`ml`/knn) — mathematically pulls toward central tendency, because the value that minimises
expected error *is* the conditional mean/median. Under the zero-fitted-parameters rule (§2)
there is no mechanism to re-inject spread. So variance collapse is a **property of central-
tendency imputation**, present in both the Phase-B tiers and the Phase-C `ml` methods. It is
not a coding error, and the figures depict it faithfully.

*(The one genuinely broken behaviour that DID exist — `mice`/`linear` extrapolating to
impossible years, MAE ≈ 900–1160 — was a separate footgun, since neutralised by an
observed-range clamp on `MLImputer.predict()`. That is a fix; variance collapse is not
something to "fix".)*

### 6.4 Why the accuracy metrics didn't flag it — and which ones do
Phase B was originally signed off on **NMBE** (normalised mean bias error, +0.49%). But **NMBE
is a mean-bias metric and is structurally blind to variance collapse**: a constant-mean
predictor is unbiased *by construction*, so NMBE ≈ 0 proves the aggregate is unbiased, never
that individual buildings were recovered. The same blindness affects MAE/RMSE, which a flat
central-tendency band can score deceptively low.

The metrics that **do** expose the collapse are distributional — the **Kolmogorov–Smirnov (KS)
statistic** and the **Wasserstein distance** — and they were already computed by the harness
(`mask_recover.py::score_continuous`). They are now surfaced on every scatter legend (e.g.
`year_built` nyc_centre **KS=0.50, W=24 y**; `levels` **KS=0.47**), each with an on-figure note
that a low MAE can still mean a flat band. **Rule going forward: never present NMBE as an
imputation-accuracy metric; for per-building/attribute recovery report MAE/RMSE *and*
KS/Wasserstein.**

### 6.5 The draw tier, illustrated — and why a residual band is still *real data*, not an error

The variance-preserving `draw` tier described forward-looking in §7 is now **built** (opt-in / off
by default) and has been illustrated directly on the same held-out pairs. Two views tell the whole
story, side by side:

- **The scatter view** (`results/phase_C/phaseC_draw_scatter_year_built.png`,
  `phaseC_draw_scatter_levels.png`): the flat Phase-A band (left) becomes a filled cloud under the
  `pmm` draw (right) — variance ratio climbs `0.06 → 0.59` for `year_built` and `0.31 → 0.90` for
  `levels`, KS drops from `0.51 → 0.32` and `0.47 → 0.12`. The point-wise MAE gets *slightly worse*
  (`26.4 → 29.8` y; `9.2 → 12.2` floors) — the **intended** trade: a draw restores spread at the
  cost of point accuracy.

- **The distribution view** (`phaseC_draw_distribution_year_built.png`,
  `phaseC_draw_distribution_levels.png`): histogram + ECDF overlays of *actual* vs *Phase-A imputed*
  vs *pmm imputed*. This is the **correct lens** for a draw method — Phase-A collapses to a single
  spike; `pmm` reproduces the *shape* of the real distribution.

**Two things a first look at the draw scatter gets wrong — both are real data, not bugs:**

1. **The dense horizontal band that survives at ~1950 is genuine.** In the pooled 12-cell hold-out,
   **794 of 2,247** observed `year_built` values (**35%**) are exactly **1951** — a real mode spike
   in the source data. An honest draw from the observed distribution therefore lands on ~1951 about
   a third of the time, so a dense band at that value is the **faithful reflection of the data**, not
   a leftover of the median fill.

2. **The cloud never hugs the 1:1 diagonal — and no method can make it.** `year_built` (and `levels`)
   are simply **not inferable from a building's footprint shape and location**. The stratifying
   columns that could condition the draw (`use_class`, `archetype_id`) are **absent from the Stage-1
   `01_buildings.gpkg` schema**, so `pmm` degenerates to a *global marginal bootstrap*: it regenerates
   the correct histogram but cannot place each individual building on its true year. A diagonal on
   this scatter would require per-building predictive information the data does not contain.

> **In one sentence:** it is not an error — the band at ~1950 is real (35% of the buildings really
> were built in 1951, so a dense band there is expected), and the cloud does not follow the diagonal
> because `year_built` is not inferable from a building's shape and location (no method can do it).

This is exactly why §7's rule holds: a draw tier is the right upgrade *only* when the per-building
**distribution** is what's needed — it fixes the histogram, never the diagonal.

---

## 7. Why the limit is accepted — and the one condition that would change it

**The variance collapse is a normal, documented limit of the chosen methods, and it is
accepted as-is.** The reasoning:

1. **The purpose is aggregate EUI, not per-building reconstruction.** OpenUBEM's imputation
   exists to let the *fleet* be simulated and rolled up to a neighbourhood total. Variance
   collapse does **not bias that aggregate** — proven directly (Phase B NMBE +0.49% / +0.08%).
   The limit touches a quantity (the per-building distribution) the platform does not depend on.

2. **The "better" method is already built, and it doesn't move the number that matters.** The
   Phase-C `ml` tier (knn) recovers slightly more spread, but a per-cell A/B showed it is
   **EUI-neutral at production granularity** — it changes no aggregate EUI. That is precisely
   why it is kept **opt-in / off**: switching it on would break the byte-identity of every
   validated result and force a re-simulation, for no aggregate benefit.

3. **It is now disclosed honestly.** The scatters carry KS/Wasserstein and a variance-collapse
   annotation; Phase B is described as **"aggregate-EUI unbiased (not per-building accurate)"**
   rather than "accurate". Nothing is hidden.

**The single condition that would change this decision:** if a future application needs the
**per-building distribution** itself (e.g. targeting retrofits, modelling the variety of a
building stock rather than its mean), then the correct upgrade is to move from a *point
estimate* to a **donor draw** — hot-deck / predictive-mean-matching, which copies a real
observed neighbour's value instead of an average, preserving variance **and** staying
zero-fitted-parameters. That is a future arc, triggered by that need — not a parameter to tune
today.

---

## 8. Where to go next

| You want… | Read |
|---|---|
| The plain-language pipeline overview | [`OpenUBEM_fundamentals.md`](OpenUBEM_fundamentals.md) |
| Every input, its real-world source, and consuming module | [`OpenUBEM_inputs_reference.md`](OpenUBEM_inputs_reference.md) |
| The full imputation arc record (Phases A–E, all CPs) | `docs/docs_ACTIVE/input/imputation/` (`results/README.md` is the entry point) |
| The Phase-B honest-precision reframe (KS/Wasserstein) | `docs/docs_ACTIVE/input/imputation/implementation/PLAN_figures_implementation.md` §11 + `results/phase_B/RESULTS_phaseB.md` |
| The binding imputation spec | `docs/docs_main/` DESIGN §3E |
| Current project status | `docs/PROJECT_CHECKLIST.md` |

---

*OpenUBEM — missing-input imputation methods. Plain-language reference; the DESIGN spec (§3E)
and the arc record remain the binding source of truth. Documents the four-tier cascade
(`fusion`/`spatial`/`statistical`/`ml`), the Phase-A–E arc mapping, and the accepted
variance-collapse limit of the Phase-B/Phase-C central-tendency methods. 2026-07-16.*
