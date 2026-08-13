# FIX — OPEN-13: narrow the `tests/test_draw_methods.py` skip

**Task:** T06, `PLAN_rulings-and-five-items-2026-08-12.md`
**Date:** 2026-08-12
**File touched:** `tests/test_draw_methods.py` (only file changed, per T06's scope)

## Root cause, confirmed

Grepped every occurrence of `_draw_tier` and `_draw_stratum_col_for` in the file. There is exactly **one**
class-body-level (collection-time) reference: `TestNoEUILeakage`'s `_FUNCS` tuple (previously at module
lines 650-660), which included `imp._draw_tier` and `imp._draw_stratum_col_for` as tuple elements —
evaluated the instant the `class TestNoEUILeakage:` statement executes, i.e. during collection, before any
test runs. Since neither symbol exists in `openubem/semantic/imputation.py` (confirmed, §4.6), this raised
`AttributeError` at import time and aborted collection of the whole module. Every other reference to the
missing symbols in the file (`imp._CANONICAL_TIER_ORDER`, `imp._TIER_HANDLER_NAMES`, `config.
IMPUTE_DRAW_METHOD_BY_TARGET`, `imp.ImputeConfig(per_input_tiers=...)`) sits inside a test **method** body
and is only evaluated when that individual test runs — those do not block collection, they just fail (or
would fail) at test-execution time, one test at a time.

## Approach chosen, and the trade-off

Chose the **in-file guard**, not a separate file: added a module-level
`_HAS_DRAW_TIER = hasattr(imp, "_draw_tier") and hasattr(imp, "_draw_stratum_col_for")` right after the
imports, removed the module-level `pytest.skip(..., allow_module_level=True)` call, and moved the `_FUNCS`
tuple construction from `TestNoEUILeakage`'s class body into its one test method
(`test_no_function_code_references_eui_by_name`), so the class body itself no longer touches the missing
symbols at definition time. The class is now decorated with
`@pytest.mark.skipif(not _HAS_DRAW_TIER, reason=...)`.

**Why this over moving the tests to a new file:** `TestNoEUILeakage` is one class with one test method; a
whole new file for a single skipped test would add a file this arc's `docs/`-vs-`tests/` drift problem
(§4.4/T05) has just shown is a maintenance liability, for no benefit — the guard achieves the same
collection-time safety without adding a second place for this feature's test coverage to live and drift out
of sync. The trade-off is that the guard variable and the skip reason must be kept consistent by hand if a
future symbol gets added to the structural pin; a separate file would isolate that risk slightly further,
but at the cost of a second file to keep wired into the suite (the exact kind of wiring this whole plan is
finding broken elsewhere — e.g. T05's `synthetic_10_gdf` conftest gap).

The skip reason names **OPEN-13** (the collection abort this fix resolves), **OPEN-17** (the DESIGN
decision on whether to promote the draw tier, which this fix explicitly does not take), and **OPEN-36**
(the governance-gap item this pattern feeds), and lists both missing symbols
(`imputation._draw_tier`, `imputation._draw_stratum_col_for`).

Per hard rule 3 of T06: **`_draw_tier` was not implemented.** No code was added to
`openubem/semantic/imputation.py` or anywhere under `openubem/`.

## Before / after, both measured

**Before** (module-level skip, confirmed by re-reading the file prior to editing):
`python -m pytest -q -p no:cacheprovider tests/test_draw_methods.py` → **1 skipped** (the whole module
skipped as a single collection-time skip).

**After** (this fix): `python -m pytest -q -p no:cacheprovider tests/test_draw_methods.py --tb=short` →

```
9 failed, 43 passed, 1 skipped in 0.83s
```

This is **better than the plan's estimate** of "~40 passed, ~9 failed, ~13 skipped" — only one test
(`TestNoEUILeakage::test_no_function_code_references_eui_by_name`) actually needed to be skipped, because
only that one test's class body touched the missing symbols at collection time. The other 12 tests the plan
guessed might need skipping (`TestDefaultByteIdentity::test_canonical_tier_order_and_handler_registry_
wired_but_opt_in`, `TestDefaultByteIdentity::test_draw_method_by_target_config_default_empty`, all 7 of
`TestDrawTierRouting`, and `TestDrawTierDeterminism`'s one test) reference the missing feature only inside
their own method bodies, so they collect fine and simply **fail at runtime** with `AttributeError:
module 'openubem.config' has no attribute 'IMPUTE_DRAW_METHOD_BY_TARGET'` — which is exactly what they
should do, since the feature genuinely does not exist. 43+9+1 = 53, matching the file's full test count.

**The 9 failures, not fixed, left failing as instructed:**

| test | failure |
|---|---|
| `TestDefaultByteIdentity::test_canonical_tier_order_and_handler_registry_wired_but_opt_in` | `AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DRAW_METHOD_BY_TARGET'. Did you mean: 'IMPUTE_ML_METHOD_BY_TARGET'?` |
| `TestDefaultByteIdentity::test_draw_method_by_target_config_default_empty` | same `AttributeError` |
| `TestDrawTierRouting::test_draw_tier_fills_with_kde_provenance_when_opted_in` | same `AttributeError` |
| `TestDrawTierRouting::test_unconfigured_target_abstains_and_falls_through_to_statistical` | same `AttributeError` |
| `TestDrawTierRouting::test_unknown_method_name_abstains_gracefully_never_raises` | same `AttributeError` |
| `TestDrawTierRouting::test_default_cfg_still_byte_identical_even_with_draw_configured` | same `AttributeError` |
| `TestDrawTierRouting::test_catfreq_routes_through_gdf_shaped_path_with_tokens` | same `AttributeError` |
| `TestDrawTierRouting::test_hotdeck_routes_through_gdf_shaped_path_with_geometry` | same `AttributeError` |
| `TestDrawTierDeterminism::test_same_seed_twice_run_byte_identical_across_whole_tier` | same `AttributeError` |

All 9 raise the identical `AttributeError` for `config.IMPUTE_DRAW_METHOD_BY_TARGET` — one root cause
(the config surface for the draw tier was never added), not nine distinct defects.

## Collection-wide check

`python -m pytest --collect-only -q` → **1990 tests collected in 44.19s, exit code 0.** No collection
errors anywhere in the output (checked). 1990 ≥ 1937, the plan's floor.

## What T06 did not do

Did not implement `_draw_tier`, `_draw_stratum_col_for`, `_CANONICAL_TIER_ORDER`'s `"draw"` entry, or
`config.IMPUTE_DRAW_METHOD_BY_TARGET`. Did not fix or skip the 9 failing tests — left them failing,
visibly, with the shared root cause stated above. Did not touch any file other than
`tests/test_draw_methods.py`.
