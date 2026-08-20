# MEASUREMENT — OPEN-13: what E-UTCI-12 still costs at HEAD

**Date:** 2026-08-18 · **Task:** T03 of `PLAN_open-48-and-four-items-2026-08-18.md`

Script: `scripts/analysis/open13_eutci12_residual.py`. Output: `openubem/outputs/comparisons/open13_eutci12_residual.csv`.

## 1. Step 1 — the defect is still live

```
grep -c "_draw_tier" openubem/semantic/imputation.py -> 0
```

Confirmed at HEAD, unchanged from the register's citation. `imputation._draw_tier` and `imputation._draw_stratum_col_for` do not exist in the module.

## 2. Step 2 — targeted run of `tests/test_draw_methods.py`

```
.venv\Scripts\python.exe -m pytest -q tests/test_draw_methods.py -rs
```

Result: **43 passed, 10 skipped** in 0.6s. All 10 `SKIPPED` lines carry the same reason family (`OPEN-44 / OPEN-13 / OPEN-17 / OPEN-36: imputation._draw_tier and imputation._draw_stratum_col_for do not exist yet ...`). The register's own T02 note (§ "collection residual DISCHARGED 2026-08-13") says "the **9** tests that *do* need `_draw_tier` ... now skip." That undercounts by one: **9 tests carry an individual `@_SKIP_NO_DRAW_TIER` decorator, and a 10th (`TestNoEUILeakage.test_no_function_code_references_eui_by_name`, line 676) is skipped via a class-level `@pytest.mark.skipif` on the whole `TestNoEUILeakage` class**, which the register's "9" did not count. Total is 10, not 9 — a small stale detail in the register's own T02 note, noted here but not fixed (measurement task).

Skip sites and what each would have verified, if `_draw_tier` existed and were opted in:

| line | test | what it would verify |
|---|---|---|
| 71 | `TestDefaultByteIdentity.test_canonical_tier_order_and_handler_registry_wired_but_opt_in` | `draw` is registered in the canonical tier order / handler registry, reachable only via explicit opt-in |
| 96 | `TestDefaultByteIdentity.test_draw_method_by_target_config_default_empty` | `config.IMPUTE_DRAW_METHOD_BY_TARGET` defaults to `{}` (no target silently routed to `draw`) |
| 581 | `TestDrawTierRouting.test_draw_tier_fills_with_kde_provenance_when_opted_in` | opting a target into `kde` via `IMPUTE_DRAW_METHOD_BY_TARGET` actually fills it and stamps `kde` provenance |
| 591 | `TestDrawTierRouting.test_unconfigured_target_abstains_and_falls_through_to_statistical` | a target left out of the opt-in dict falls through to the existing statistical tier rather than silently doing nothing |
| 601 | `TestDrawTierRouting.test_unknown_method_name_abstains_gracefully_never_raises` | a typo'd/unknown method name in the config abstains instead of raising |
| 611 | `TestDrawTierRouting.test_default_cfg_still_byte_identical_even_with_draw_configured` | with `draw` configured but the tier not in `IMPUTE_ENABLED_TIERS`, output stays byte-identical to the pre-draw baseline |
| 628 | `TestDrawTierRouting.test_catfreq_routes_through_gdf_shaped_path_with_tokens` | `catfreq` routes correctly through the GeoDataFrame-shaped call path and stamps its token |
| 645 | `TestDrawTierRouting.test_hotdeck_routes_through_gdf_shaped_path_with_geometry` | `hotdeck` routes correctly through the geometry-aware GDF call path |
| 676 | `TestNoEUILeakage.test_no_function_code_references_eui_by_name` (class-level skip) | structural zero-fitted-params guard: no draw function's `__code__.co_names` ever references an EUI-like name — this is the leakage pin `_draw_tier` itself needs once it exists |
| 698 | `TestDrawTierDeterminism.test_same_seed_twice_run_byte_identical_across_whole_tier` | same seed run twice through the whole draw tier produces byte-identical output (determinism, end to end) |

## 3. Step 3 — static skip-marker census across `tests/` (documentary, not a full-suite rerun)

Per this task's explicit director instruction, the full 17-minute suite was **not** re-run for this task; targeted `tests/test_draw_methods.py` plus the two collection counts (§4 below) were judged sufficient. The suite-wide **1875 passed / 55 skipped / 1930 collected** figure used below is therefore **quoted**, from `docs/docs_ACTIVE/openings/extra/FIX_open-52_temproot-remedy.md:173` (the OPEN-52 remedy verification run, 2026-08-18) — it was not re-derived by executing the whole suite in this task, per hard rule 7.

To still give an auditable, re-derived (not inherited) accounting of *where* skip logic lives, the script did a static grep-style census of every `pytest.mark.skip(...)` / `pytest.mark.skipif(...)` / `pytest.skip(...)` **site** in `tests/*.py`:

| file | skip-marker sites |
|---|---|
| `test_layout_assigner.py` | 36 |
| `test_plotting_suite.py` | 9 |
| `test_building_classifier.py` | 5 |
| `test_service_loads.py` | 5 |
| `test_sim_integration.py` | 5 |
| `test_v19_national_cbecs_rescore.py` | 4 |
| `test_draw_methods.py` | 2 |
| `test_impute_montage.py` | 2 |
| `test_v19_basis_diagnostic.py` | 2 |
| `test_debias.py` | 1 |
| `test_resolution_mode_live.py` | 1 |
| `test_viz_validation.py` | 1 |
| **total sites** | **73** |

**This does not reconcile to 55 and is not claimed to.** A "site" (a `@pytest.mark.skipif(...)` decorator, or a `pytest.skip(...)` call) is not the same unit as a runtime skip count: a single decorated test method or class produces one skip only if actually collected and its condition is true; a parametrized test can multiply one site into several runtime skips or none; a `skipif` whose condition is false at HEAD contributes zero runtime skips despite being a "site." `test_draw_methods.py` itself is the clean illustration: **2 static sites** (`_SKIP_NO_DRAW_TIER` and the `TestNoEUILeakage` class-level skip) produced **10 runtime skips** in §2, because `_SKIP_NO_DRAW_TIER` decorates 9 separate test methods. The reverse (a site producing 0 runtime skips because its condition is false) is exactly as possible and was not distinguished by this static pass.

**Conclusion on the "how many of the 55 are E-UTCI-12's" question:** this task's own targeted run (§2) proves the number for `test_draw_methods.py` directly and without inheritance: **10 of the (quoted) 55 whole-suite skips belong to E-UTCI-12** — all 10 skips in that file carry an OPEN-13-family reason and none carries any other reason. What this task did **not** do is verify, by execution, that the whole-suite total is still exactly 55 with `test_draw_methods.py` contributing exactly 10 of it (rather than, say, 9 skips elsewhere shifting by one for unrelated reasons since 2026-08-18's FIX doc was written). That full reconciliation requires a full-suite `-rs` run, which was explicitly waived for this task. **Recommendation:** the next full-suite run already planned for T06 of this plan should be run with `-rs` (not bare `-q`) so the 55-skip breakdown is captured by file for good, closing this gap cheaply as a side effect of a run that has to happen anyway.

## 4. Step 4 — collection counts

```
.venv\Scripts\python.exe -m pytest -q --collect-only          -> 1930 tests collected in 1.65s, exit=0
.venv\Scripts\python.exe -m pytest -q tests/ --collect-only    -> 1930 tests collected in 1.60s, exit=0
```

**Bare `pytest -q` (no path) and `pytest -q tests/` now collect identically: 1930 tests, exit 0, no difference.** This is because `pyproject.toml:52` sets `[tool.pytest.ini_options] testpaths = ["tests"]` with no `addopts` — a bare invocation from the repo root already resolves to `tests/` before any test file is even opened. The register's stated consequence ("a bare `pytest -q` aborts at collection... the whole suite has not been runnable as a whole") is **confirmed false today**, independently of the draw-tier defect itself — `testpaths` alone would make bare and scoped invocations identical even if the draw-tier defect still aborted collection outright (it does not; see §5).

## 5. Step 5 — positive control: does the collection-count method actually detect a real error?

An untracked file `tests/test_zzz_open13_control.py` (never tracked by git; matches the `test_*.py` collection glob, unlike a non-matching scratch filename, which was tried first and silently ignored by pytest — noted as a false start) was written with a single deliberately unresolvable import:

```python
import this_module_does_not_exist_anywhere
```

```
.venv\Scripts\python.exe -m pytest -q --collect-only
...
ERROR tests/test_zzz_open13_control.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1930 tests collected, 1 error in 1.98s
exit=2
```

Exit code **2** (vs. **0** clean) and the literal string `Interrupted: 1 error during collection` — this is exactly the failure mode the register describes for the pre-fix state, and the detection method used throughout this task correctly flags it. The control file was then deleted; it was never tracked by git, so nothing needed reverting. Confirmed via `git status` (read-only) both immediately after deletion and again at the end of this task: no trace of the control file, only pre-existing changes from concurrent T01/T02/T04/T05 work.

## 6. Answer

- **The defect (E-UTCI-12) is unchanged and still open**: `_draw_tier` / `_draw_stratum_col_for` do not exist; 10 tests in `test_draw_methods.py` skip because of it (not 9, per §2's correction to the register's own T02 note).
- **The register's stated consequence is stale, confirmed by two independent mechanisms**: (a) `testpaths = ["tests"]` (present since the OPEN-52 remedy, `pyproject.toml:52`) makes bare `pytest -q` and `pytest -q tests/` collect identically regardless of the draw-tier defect; (b) even without that, the draw-tier defect itself no longer aborts collection — it degrades to a scoped skip via `_HAS_DRAW_TIER` / `_SKIP_NO_DRAW_TIER`, discharged 2026-08-13 per the register's own T02 note, and reconfirmed live here.
- **Is the skipped coverage load-bearing?** Yes, in the ordinary sense that any router-wiring feature carries untested code paths while unimplemented — the 10 skipped tests in §2 each pin a specific behavior of the not-yet-existing `_draw_tier` (opt-in isolation, per-target routing, graceful abstention, determinism, EUI-leakage guard). But none of them is *currently* silently-not-covering live production code: `_draw_tier` is not called from anywhere reachable by default (`IMPUTE_DRAW_METHOD_BY_TARGET` defaults to `{}`, `draw` stays out of `IMPUTE_ENABLED_TIERS`), so the skip is honest — it is future-feature test coverage waiting on OPEN-17's promotion decision, not a hole in tested production behavior. The item is therefore, at HEAD, a **contained, correctly-labelled remnant of a decision (OPEN-17) still pending**, not a "silently skips real coverage" problem.
- **What is left of E-UTCI-12 specifically**: nothing beyond "the draw tier's router wiring has never been implemented," which is squarely OPEN-17's scope, not OPEN-13's. OPEN-13 itself has no remaining open technical content beyond that forward pointer.

## 7. Recommendation (not enacted — measurement task)

Run T06's already-planned full-suite pass with `pytest -q tests/ -rs` instead of bare `-q`, and capture the per-file skip breakdown into the recount artifact. That closes the "which 55" gap this task could not close without violating the no-full-suite-rerun instruction, at zero extra cost since the run has to happen anyway.

## Register amendment to apply

Apply to OPEN-13 (register `:4033`), appended after the existing 🟢 discharge note (do not touch the note above it — strike nothing, this is additive):

> 🟢 **T03 of `PLAN_open-48-and-four-items-2026-08-18.md` (2026-08-18) re-confirmed the discharge and closed the two remaining stale claims:**
> - The item's stated consequence — *"a bare `pytest -q` aborts at collection... the whole suite has not been runnable as a whole"* — is **false today**, by two independent mechanisms: `pyproject.toml:52`'s `testpaths = ["tests"]` (landed with the OPEN-52 remedy) makes bare `pytest -q` and `pytest -q tests/` collect identically (1930/1930, exit 0/0), and separately the draw-tier defect itself no longer aborts collection at all — it degrades to a scoped skip (discharged 2026-08-13, reconfirmed live: `tests/test_draw_methods.py -rs` → 43 passed, 10 skipped).
> - **Correction to this doc's own T02 note above:** it says "the **9** tests that do need `_draw_tier`... now skip." The true count is **10** — 9 carry an individual `@_SKIP_NO_DRAW_TIER` decorator and a 10th (`TestNoEUILeakage.test_no_function_code_references_eui_by_name`) is skipped via a class-level `skipif` that the "9" did not count.
> - All 10 skips are E-UTCI-12/OPEN-17-family and none is a hole in tested *production* behavior: `_draw_tier` is unreachable by default (`IMPUTE_DRAW_METHOD_BY_TARGET` defaults to `{}`; `draw` stays out of `IMPUTE_ENABLED_TIERS`), so the skipped coverage is future-feature pinning for OPEN-17's promotion decision, not live coverage loss.
> - Whole-suite skip reconciliation (how many of the quoted 55 are E-UTCI-12's, file by file) was **not** performed by full-suite execution in this task per explicit director instruction to save the ~17-minute run; a static skip-marker census (73 sites across 12 files, `test_draw_methods.py` contributing 2 sites / 10 runtime skips) is documentary only and does not reconcile to a runtime count. Recommend T06's already-planned full-suite pass use `-rs` to capture this for good.
> - See `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_eutci12-residual.md` for full evidence, the per-test load-bearing table, and the collection-detection positive control (exit 2 / `Interrupted: 1 error during collection` on a deliberately broken untracked file, confirming the method would catch a real regression).
