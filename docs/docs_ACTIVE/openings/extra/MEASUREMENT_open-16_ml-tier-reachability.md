# MEASUREMENT — OPEN-16: the `ml` tier is reachable only from the validation entry point

**Task:** T11 of `../implemenation/PLAN_twenty-items-2026-08-19.md`. No new script — traces
existing code and re-runs an existing, targeted slice of `tests/test_ml_imputer.py` as the
constructed reachability proof, rather than writing a duplicate throwaway script for a question
the repo's own test suite already answers directly.

## 1. The two entry points

**Production:** `enrich_semantics(gdf, output_dir=None, *, load_mode=None, random_seed=None,
construction_table=None, loads_table=None, schedules_table=None)`
(`openubem/semantic/__init__.py:324-332`) — confirmed by `inspect.signature`, exactly these seven
parameters, none of them a tier config, an `ImputeConfig`, or an `enabled_tiers`/`per_input_tiers`
value. Its own docstring names the pipeline stages: *"gate → vintage → envelope → loads →
Unknown/gap imputation → probabilistic perturbation..."* (`:337-338`).

**Validation:** `impute_missing(gdf, cfg: ImputeConfig | None = None, targets=None, rng=None)`
(`imputation.py:888`) — the only function that dispatches to `_ml_tier` via the tier-name registry
(`_TIER_HANDLER_NAMES["ml"] = "_ml_tier"`, `imputation.py:885`). Its own docstring states it is
*"a new entry point for the T08/T09 validation harness to call directly"* and does *"not reroute
`enrich_semantics`"* (`:889-891`).

## 2. The branch that admits `ml`, and the one that does not

`ImputeConfig.tiers_for(attribute)` (`imputation.py:600-607`) resolves, in order: per-attribute
override → `enabled_tiers` → `config.IMPUTE_ENABLED_TIERS` (`config.py:100`,
`("fusion", "spatial", "statistical")` — **no `"ml"`**). So `impute_missing()` itself only reaches
`_ml_tier` when a caller explicitly constructs `ImputeConfig(enabled_tiers=(...,"ml",...))` or
`ImputeConfig(per_input_tiers={attr: (..., "ml", ...)})` — the admitting branch is that explicit
constructor argument, not any default.

Traced `enrich_semantics`'s own imputation step (*"Unknown/gap imputation"*): it calls
`get_construction_set` (`construction_sets.py`), which in turn calls
`openubem.semantic.imputation.impute_column` (a **different, lower-level** function than
`impute_missing` — series-in/series-out, not tier-routed) at `construction_sets.py:323-330`, with
`method="kde"` **hard-coded as a literal** — never `"ml"`, never a `model_path`. `draw_methods.py:121`
calls the same function, also hard-coded to `method="kde"`. `impute_column` does have an `"ml"`
branch (`imputation.py:16-45`, `method == "ml"` → joblib-loads an `MLImputer`), but **the only
caller anywhere in `openubem/`, `scripts/`, or `tests/` that ever passes `method="ml"` or a
`model_path` is `tests/test_ml_imputer.py`** (grep across all three trees for `impute_column(` —
every non-test call is `method="kde"` literal). So this second, independent code path into "ml"
behaviour is unreachable from production too, by the same kind of check.

**Production never reaches `_ml_tier` by a different route either**: `enrich_semantics` and every
function it transitively calls (`get_construction_set`, `get_loads`, `_build_unknown_envelope`,
`_build_unknown_loads`) were checked for any reference to `impute_missing`/`_ml_tier`/`ImputeConfig`
— none exists (the grep already run for T07's OPEN-14 measurement, `impute_missing(` /
`fusion.fuse(` callers repo-wide, showed the **only** caller of `impute_missing` is
`openubem/validation/mask_recover.py:330,338`).

## 3. What a production caller would have to pass to reach it

**Nothing they can pass through `enrich_semantics`'s own signature reaches it.** Reaching `_ml_tier`
requires calling a different function (`impute_missing`) with an explicit `ImputeConfig` that names
`"ml"` — a caller would have to bypass `enrich_semantics` entirely and call
`openubem.semantic.imputation.impute_missing(gdf, cfg=ImputeConfig(enabled_tiers=("ml",
"statistical")))` (or `per_input_tiers`) directly, which is exactly what the validation harness
(`mask_recover.py`) does and what `enrich_semantics`'s own docstring says it deliberately does not
reroute to.

## 4. Constructed proof, both directions

Re-ran the two existing tests built for exactly this question, fresh, rather than duplicating them
in a throwaway script:

```
.venv/Scripts/python.exe -m pytest -q tests/test_ml_imputer.py -k "TestRouting or TestOptInOnly" -v
```

**6 passed, 0 failed.** The six tests, read directly (not taken on trust):

- `TestRouting` (`test_ml_imputer.py:174-`): constructs
  `impute_missing(gdf, cfg=ImputeConfig(per_input_tiers={"year_built": ("spatial", "ml",
  "statistical")}))` (`:208`) and `per_input_tiers={"year_built": ("ml", "statistical")}` (`:224`)
  — **the tier is reachable and fires** when a caller explicitly asks for it through
  `impute_missing`.
- `TestOptInOnly.test_ml_not_in_default_enabled_tiers` — asserts `"ml" not in
  config.IMPUTE_ENABLED_TIERS` directly against the shipped config.
- `TestOptInOnly.test_default_impute_missing_never_invokes_ml_tier` — monkeypatches `_ml_tier`
  itself to record every call, then calls `impute_missing(gdf, rng=...)` with **no** cfg (the
  default a naive caller would use) and asserts **zero calls** were recorded — i.e., even the
  validation entry point does not reach `ml` unless a caller opts in explicitly.

**Not reachable from the production entry point's argument surface**, per §1's `inspect.signature`
check: `enrich_semantics` has no parameter through which `ImputeConfig`, `enabled_tiers`, or
`per_input_tiers` could be threaded at all — so the question is not "would a production caller
choose to enable ml" but "could one, given the function signature," and the answer is structurally
no without editing `enrich_semantics` itself.

## 5. Verdict

**Confirmed at HEAD, both by trace and by construction**: the `ml` tier is wired
(`imputation.py:543,882-886`), absent from `config.IMPUTE_ENABLED_TIERS` (`config.py:100`), and
reachable only through `impute_missing()`, whose only real caller in the repository is the
validation harness (`openubem/validation/mask_recover.py:330,338`). The production pipeline
(`enrich_semantics`) has no argument surface that could reach it, either through
`impute_missing`/`ImputeConfig` or through the parallel `impute_column(method="ml")` path (which is
called only from tests). This matches N10's original register finding and adds a structural
argument-surface check and a fresh test re-run as independent corroboration, rather than quoting
the finding.
