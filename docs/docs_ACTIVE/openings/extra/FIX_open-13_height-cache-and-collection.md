# FIX — OPEN-13 (E-UTCI-13 and E-UTCI-12)

**Date:** 2026-08-12
**Plan:** `implemenation/previous/PLAN_five-item-sweep-2026-08-12.md`, tasks T03–T04
**Status:** E-UTCI-13 **fixed**. E-UTCI-12 **contained, not fixed**. **OPEN-13 stays open.**

> 🔴 **Authorship note, recorded rather than smoothed over.** This report is **written by the
> director, not by the executor that did the work.** The T03–T04 executor completed both code changes
> correctly but then stalled twice waiting on a background full-suite run it had lost track of,
> notified completion twice with nothing written, and never produced its report. It was stopped. Every
> number below was measured by the director from raw output; none is carried over from the executor.
> **The code changes were audited on their own merits and are sound** — the failure was in reporting,
> not in the work. *(This is the third time in this arc that an executor's "completed" has not meant
> completed. See the director prompt §8.)*

---

## 1. E-UTCI-13 — the height cache nulls two columns on every re-read. **FIXED.**

### 1.1 The mechanism, read at source rather than inferred

`overture_fetcher._normalize()` (`openubem/acquisition/overture_fetcher.py:111-127`) reads the
**raw** Overture schema and renames as it goes:

| raw column read | normalized column written |
|---|---|
| `num_floors` | `levels` |
| `class` (falling back to `subtype`) | `use_class` |
| `height` | `height` |
| `year_built` | `year_built` |
| `id` | `id` |

**The rename is not idempotent.** After pass 1 there is no `num_floors` and no `class`, so a second
pass takes the `else` branches at `:116` and `:118-120` and writes `np.nan` and `None`. `height`,
`year_built` and `id` survive **only because their names happen to be stable across both passes** —
that asymmetry is the fingerprint of this defect, not a coincidence.

`height_cache.pull_overture` stores `fetch_overture()`'s already-normalized output, and
`fusion.OvertureSource.join` then re-read that cache **through `fetch_overture()` again**.

### 1.2 The fix

`openubem/semantic/fusion.py` (+34 lines): a module constant `_NORMALIZED_OVERTURE_COLUMNS` and a
`_load_overture_layer(cfg)` helper, called from `OvertureSource.join` in place of the direct
`fetch_overture(...)` call. If the configured slice on disk already carries the normalized schema it
is read straight through; a raw-schema slice or a live `endpoint` pull goes through `fetch_overture()`
exactly as before.

### 1.3 🔴 Measurement — all three legs in one process, on one fixture

A two-row raw-schema slice was built, written, normalized, re-written as a cache, and re-read:

| state | `levels` non-null | `use_class` non-null |
|---|---|---|
| pass 1 — raw slice through `fetch_overture` | **2 / 2** | **2 / 2** |
| pass 2 — normalized cache through `fetch_overture` (**before**) | **0 / 2** | **0 / 2** |
| pass 2 — normalized cache through `_load_overture_layer` (**after**) | **2 / 2** | **2 / 2** |

**Values, not only counts:**

- before → `levels = [nan, nan]`, `use_class = [None, None]`, while `height = [10.0, 20.0]` and
  `year_built = [1990, 2001]` pass through untouched — exactly the two-column asymmetry predicted.
- after → `levels = [3, 6]`, `use_class = ['residential', 'commercial']`.

**Pass 1 differs from "before", so the before/after is non-vacuous** and reportable under the
project's evidence rules.

### 1.4 Regression leg

A **raw**-schema slice still routes through `fetch_overture` and still comes back normalized
(`levels` non-null 2/2, all six normalized columns present). The guard changes the cached path only.

### 1.5 Guard correctness — and its weakness

`_NORMALIZED_OVERTURE_COLUMNS` was checked **at runtime** to be set-equal to the fetcher's own
`_NORMALIZED_COLUMNS` (`overture_fetcher.py:29`). It is.

⚠️ **Weakness recorded, not smoothed.** It is a **duplicated literal, not an import**. If the
fetcher's normalized schema ever gains or loses a column, the exact set-equality stops matching and
every read **silently** falls back to the double-normalizing path — this defect returns with no error
and no warning. The failure direction is safe (old behaviour, never wrong data from a wrong branch)
but it is **silent**, which is the property that let E-UTCI-13 live this long.

**No unit test covers the cached-read path.** The guard is currently protected by this measurement
alone.

---

## 2. E-UTCI-12 — the suite could not be collected. **CONTAINED, NOT FIXED.**

### 2.1 The fix

`tests/test_draw_methods.py` (+13 lines): a module-level
`pytest.skip(..., allow_module_level=True)` naming OPEN-17 and stating exactly which symbols are
missing.

### 2.2 🔴 The user's OPEN-17 decision was NOT taken — checked, not assumed

| symbol | present at HEAD? |
|---|---|
| `imputation._draw_tier` | **absent** |
| `imputation._CANONICAL_TIER_ORDER` | present — `('fusion','spatial','ml','statistical')`, **no `"draw"`** |
| `imputation._TIER_HANDLER_NAMES` | present — four entries, **no `"draw"`** |
| `config.IMPUTE_DRAW_METHOD_BY_TARGET` | **absent** |

Nothing was implemented. **OPEN-17 remains wholly the user's call**, and the register's standing rule
— *do not close E-UTCI-12 and OPEN-17 with each other* — is intact.

### 2.3 🔴 Measurement — both legs, on the real tree

| state | result |
|---|---|
| **before** — `git stash` of that one file, HEAD content restored in place | `AttributeError: module 'openubem.semantic.imputation' has no attribute '_draw_tier'` at `tests/test_draw_methods.py:645`; `Interrupted: 1 error during collection`; **no tests collected**; exit **2** |
| **after** — working tree | **1937 tests collected in 55.26s**; exit **0** |

The abort is at **class-body evaluation** (`class TestNoEUILeakage`, line 631, list literal at 645),
i.e. at import — which is why one broken file aborted the entire repository's collection.

### 2.4 🔴 The containment is broader than the fault — a cost the executor did not report

The module skip removes **53 tests** from collection. Only **13** of them reference the unimplemented
draw-tier names.

Measured directly, in a scratchpad copy of the HEAD file with **only the single offending class
removed** (no repo edit): the file collects and runs **43 passed, 9 failed** — the 9 being genuine
not-yet-implemented failures, correctly red.

**So the fix silently costs 43 currently-passing tests** of the `draw_methods` registry scaffold,
which *is* implemented. Nothing now reports them as missing.

**Also measured, so the next session does not waste time on it:** `@pytest.mark.skip` on the class
does **not** prevent the class body from executing, so decorating it still aborts collection with the
same `AttributeError`. A genuine narrow fix needs **conditional collection** (e.g. guarding the class
on `hasattr(imp, "_draw_tier")`) — a design choice, not a mechanical one.

**Verdict: contained, not fixed.** The stated goal is met and proven both ways; the cost is 43 tests
that no longer run.

---

## 3. 🔴 What the restored collection immediately exposed — the suite's real state, for the first time

**Because the suite can be collected again, it could be run to completion.** The director ran it:

```
python -m pytest -q -p no:cacheprovider
70 failed, 1822 passed, 10 skipped, 11 warnings, 36 errors in 1606.88s (0:26:46)
exit 1
```

**This is the first complete pass/fail count this project has had in months, and it is the real
payoff of T04 — not the 1937 collection number.** It is also the first evidence for how much the
collection failure was hiding: **106 failing or erroring tests**.

### 3.1 Where they are — and 61 of 106 are in files that violate a project hard rule

| tree | failed + errored |
|---|---|
| 🔴 `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` | **61** |
| `tests/` | **44** |
| `scripts/analysis/test_viewer_layout_assign.py` | 1 |

**`docs/` contains 30 `.py` files, 5 of them test files**, against the project's own hard rule —
*"No `.py` files under `docs/`, ever."* pytest collects them, and they produce **58% of the whole
failure count**.

**Two of the five are byte-identical duplicates of files in `tests/`** (`test_elevators.py`,
`test_parser_elevators.py`, verified with `cmp`); the other three differ from their `tests/` twins.
**A stale duplicate that differs from the live file is worse than one that does not** — it can pass
or fail for reasons that have nothing to do with the shipped code.

### 3.2 What the 106 actually are

| cause | count |
|---|---|
| `FileNotFoundError` — a test asserting an **output artifact exists on disk** | **51** |
| missing pytest fixture `synthetic_10_gdf` (setup errors) | ~36 |
| `AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DEBIAS…'` | 5 |
| `KeyError: 'elevators_eui_kwh_m2'` / `'Elevators:InteriorEquipment:Electricity'` | 8 |
| other assertions | remainder |

🔴 **Roughly half are artifact-existence tests, not logic tests.** They assert that a CSV or a
findings document is present on disk, so they fail on any checkout where that artifact was never
regenerated. **That is a different kind of red from a broken calculation and must not be reported as
"70 broken tests."**

⚠️ **The `IMPUTE_DEBIAS…` group is the same shape as E-UTCI-12 all over again** — tests committed
against a config attribute that does not exist. **This project has at least two independent instances
of tests-without-implementation**, which is OPEN-36's territory (*a signed completion record
describing code that has never existed*).

### 3.3 Incidental, recorded so it is not rediscovered as a mystery

`tests/test_sim_integration.py::test_synthetic_fleet_full_annual` emits a **Windows fatal exception:
access violation** faulthandler dump from `joblib`'s `loky` backend spawning subprocesses under
Python 3.14. **It does not stop the run** — the suite continued past it and finished. Noise, but
undocumented noise.

`tests/fixtures/synthetic_30_archetype_coverage.gpkg` shows as modified in git. Compared table by
table against HEAD: every table identical except `gpkg_contents`, whose only differing field is
`last_change` (`2026-07-26T16:23:33.730Z` → `2026-08-12T17:35:11.287Z`). The `synthetic` data table
is hash-identical at 25 rows. **A test opens the checked-in fixture for write; no data changed.**

---

## 4. Disposition

- **E-UTCI-13 — closes.** Fixed, measured three ways, regression leg checked, weakness recorded.
- **E-UTCI-12 — does not close.** The suite is collectable, which was the stated goal, but **43
  passing tests were traded for it** and narrowing the skip is a design decision nobody has made.
- **OPEN-13 stays open** on that residual.
- **OPEN-17 is untouched** and still the user's decision.
- 🔴 **A new item is opened — OPEN-44** — for the 70 failures / 36 errors the restored collection
  exposed, and for the 30 `.py` files under `docs/`. **This was found by auditing the fix's own side
  effects, not by running a task, which is now the fifth time in this arc.**

**Nothing published changes as a result of any of this.** No fleet number, no accuracy figure and no
E02 conclusion depends on the height cache's `levels`/`use_class` columns or on the draw-tier tests.
