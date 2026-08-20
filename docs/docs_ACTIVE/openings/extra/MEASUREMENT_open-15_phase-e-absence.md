# MEASUREMENT — OPEN-15: Phase E has no code path at HEAD

**Task:** T10 of `../implemenation/PLAN_twenty-items-2026-08-19.md`. No script — a search-and-cite
task; every search command is reproduced verbatim below rather than run through a throwaway
script, so it can be re-run directly.

## 1. The DESIGN citation

`docs/docs_DONE/INPUTS/imputation/results/phase_E/RESULTS_phaseE.md` (read-only per §3 rule 4,
cited not edited), header:

> **Status:** DOCUMENTED-DEFERRED (T13 delivered) — deep-generative / GNN / LLM ruled out of core
> scope with evidence; TabPFN ruled NOT READY, permitted only as an optional isolated experimental
> track. **No frontier method enters the default pipeline.**

and further down: *"Phase E is documentation, not execution."* Source of record cited by that
same doc: `../../PLAN_input_imputation_implementation.md` §5 (lines 215–216, 278–283) + §6 T13
(lines 849–863). Four candidate families are named and ruled on: **deep-generative** (GAIN,
VAE/MIWAE, DAE/MIDAS, TabDDPM, tab-transformer) — SKIP; **spatial GNN** (GAT/HGCN/BAPN) — REJECT;
**LLM** (zero/few-shot + retrieval) — FIRM DISQUALIFICATION; **TabPFN / foundation model** — NOT
READY, experimental-only.

## 2. Exhaustive search of `openubem/` — does anything implement it?

Two search passes, not one, per the task's own "how to test" clause — the first on the bare
phrase, the second on the DESIGN's own vocabulary for the four candidate families, so the absence
claim cannot be an artifact of searching only for the label "Phase E":

```
grep -rn "Phase E" openubem/ scripts/            -> 0 hits in openubem/; only this task's own new files in scripts/ (none yet)
grep -rniE "TabPFN|TABPFN_IMPUTED|deep.generative|spatial.gnn|GAIN|MIWAE|TabDDPM|MIDAS|tab-transformer|foundation.model" openubem/ scripts/ --include=*.py
```

The second search returns exactly **one file** with genuine hits:
`openubem/results/impute_figures.py:178-186,676-692` — and every hit there is **plotting
metadata for the figures the RESULTS doc itself embeds** (`"tabddpm_wins_above_n": (10_000,
20_000)`, `"gain_needs_above_n": 30_000`, `"deep-generative": "SKIP"`, `"TabPFN": "NOT READY"`,
matplotlib annotation calls at `:682,688,692` drawing those exact threshold lines onto a chart).
This is **documentation-rendering code that draws the ruling as a figure** — it does not call, fit,
load, or route to any of the four candidate methods. No other file matches either search.

`openubem/semantic/imputation.py` — the module that owns every real tier (`_fusion_tier`,
`_spatial_tier`, `_ml_tier`, `_statistical_tier`, `_CANONICAL_TIER_ORDER` at `:543`) — has **zero**
hits on either search. `_CANONICAL_TIER_ORDER = ("fusion", "spatial", "ml", "statistical")`
(`imputation.py:543`) has no fifth entry for any Phase-E family, and `_TIER_HANDLER_NAMES`
(`imputation.py:882-886`) maps only those same four tier names to their handler functions.

**No provenance token exists for it either**: the project's provenance vocabulary (searched the
same way `_fusion_tier` stamps `FUSED_*`, `_ml_tier` stamps `_ML_TOKEN_HIGH`/`_ML_TOKEN_MED`) has
no `TABPFN_*` or equivalent token defined anywhere — confirming even the experimental-only TabPFN
track RESULTS_phaseE.md describes as "permitted" was never actually built, only permitted in
principle.

**Verdict: no code path exists at all, for any of the four candidate families, anywhere in
`openubem/` or `scripts/`.** The absence claim survives the DESIGN's own vocabulary, not only the
label "Phase E" — satisfying the task's stated test.

## 3. Scoping estimate — what an implementation would have to touch (NOT a plan, NOT code)

Stated as a rough inventory of the surface area, in the same shape the other three tiers already
establish as precedent, not as a design:

- **A new tier module** analogous to `openubem/semantic/draw_methods.py` (the six draw-tier
  imputers) or a new function set inside `imputation.py` alongside `_fusion_tier`/`_ml_tier` — one
  per admitted method (given the ruling, realistically only a TabPFN track, since the other three
  families are disqualified outright).
- **`_CANONICAL_TIER_ORDER`, `_TIER_HANDLER_NAMES`** (`imputation.py:543,882-886`) — a fifth tier
  name and its handler mapping, mirroring how `"ml"` was added without being placed in
  `IMPUTE_ENABLED_TIERS` (`config.py:100,103`, "stays OUT... until CP-3 passes + user" — the same
  opt-in-by-config pattern this tier would need).
- **`openubem/config.py`** — a new config surface (model weights path, per-target enablement dict)
  analogous to `FUSION_SOURCES_BY_TARGET`/`FUSION_OVERTURE_SLICE_PATH` (`config.py:141-150`) or
  `IMPUTE_ML_METHOD_BY_TARGET`.
  - **A pinned model artifact** — TabPFN's own BSD-3 weights (~20 MB per RESULTS_phaseE.md),
    committed or fetched offline, needing the same "never live network in tests" discipline
    `height_cache.py`/`overture_fetcher.py` already enforce for Overture.
- **A provenance token** (e.g. `TABPFN_IMPUTED`) threaded through the same
  `provenance.py` machinery `_fusion_tier` and `_ml_tier` already use (`imputation.py:658-659`
  pattern).
- **Tests**: a new `tests/test_phase_e_tabpfn.py` (or equivalent), on the model of
  `tests/test_height_backfill.py`/`tests/test_draw_methods.py` — registry-scaffold tests, a
  do-no-harm/EUI-neutrality gate (mirroring Phase C's "shifted EUI −5.51%, ships off" precedent
  cited in RESULTS_phaseE.md), and a reproducibility/determinism test (pinned weights, seeded).
- **A validation-domain study**, not code at all: RESULTS_phaseE.md's own blocker is that "no
  peer-reviewed study validates zero-shot foundation-model imputation for building attributes in a
  physics-based UBEM" — this is the actual gate, and it is a research task, not an engineering one.
  No amount of the code scoped above discharges it; RESULTS_phaseE.md is explicit that TabPFN stays
  "NOT READY for production" pending exactly this.

**This is a scoping estimate only** — module names, not a task list; no line of it was written as
code, and no file under `openubem/` was touched by this task.
