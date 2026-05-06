# PLAN — Step 1.5 — Remediation (Gemini Audit Follow-up)

> **Slug:** `step-1.5-remediation-gem-audit-report`
> **Date:** 2026-05-06
> **Binding contract:** `docs\docs_step1\DESIGN_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar.md`
> **Source of issues:** `docs\docs_step1\auditing\gemini_auditing_step1.md`
> **Prerequisite:** `docs\docs_step1\PLAN_step-1-implementation.md` — Step 1.0 must be greenlit (it is, after-T12: 35 passed, 1 skipped) before 1.5 starts. Do not reopen the prior plan's progress log.

---

## §1 Summary

Step 1 was greenlit on the strength of 35 passing tests. An independent audit (Gemini) caught two issues the in-house suite missed:

1. A one-line bug at `openubem/acquisition/osm_fetcher.py:196` that **inverts** the load-bearing `function_tag` priority required by DESIGN line 87. Stage 2's `building_classifier.py` consumes this column, so the bug propagates downstream.
2. A test-coverage gap: `_flatten_tags` is imported by the test module (`tests/test_osm_fetcher.py:34`) but never invoked. `_synthetic_gdf` (line 153) builds rows post-flatten, so every cleaner / provenance / serialise test bypasses the flatten module. This is why the priority bug escaped despite a green pytest run.

Three lower-severity items also fall out of the same audit (parser hardening, dead-code collapse, log-key rename) and are bundled into a single task to keep the diff small.

This plan covers exactly three tasks (R1 / R2 / R3). No scope creep.

---

## §2 Hard rules for the executor

- **Stay in the cwd** `C:\Users\o_iseri\Desktop\OpenUBEM`.
- **Manager owns plans.** If you (Sonnet) think the plan is wrong, STOP and quote the conflict — do not author your own plan.
- **No scope creep beyond R1, R2, R3.** Do not refactor unrelated code. Do not rename functions. Do not change the 23-column schema or the 7-token quality vocabulary.
- **Default to no comments.** Add a one-line comment only when the WHY is non-obvious.
- **Stop-and-ask on spec ambiguity.** Never invent. If you find another bug while implementing, STOP and report it; do not silently fix.
- **If the bug fix breaks a prior test, INVESTIGATE — do not silently rewrite the test.** If the prior test was asserting the bugged behaviour, that is itself a defect to flag.
- **Touch only these two files:** `openubem/acquisition/osm_fetcher.py` and `tests/test_osm_fetcher.py`. No new files. No deletions. No edits to `main.py`. No `.py` under `docs/`. No edits to DESIGN / OVERVIEW / prior PLAN / gemini audit report.

---

## §3 File layout to touch

```
openubem/
  acquisition/
    osm_fetcher.py          ← edit (R1, R3a, R3b, R3c)
tests/
  test_osm_fetcher.py       ← edit (R2: new TestFlattenTags class; R3 fixture extension)
```

No other files may be created, moved, deleted, or edited.

---

## §4 Dependency decisions

No changes. Existing pins stand:

- `osmnx >= 1.9, < 2.0`
- `pyogrio` (preferred over fiona)
- `tenacity` remains an optional extra, not a base dependency

Do not add or remove any dependency in `pyproject.toml`.

---

## §5 Source-of-truth verified facts

The manager has independently verified these against the current files. Do not re-derive — trust and cite.

**Fact 5.1 — DESIGN line 87 priority rule (binding):**
> File: `docs\docs_step1\DESIGN_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar.md`, line 87
> Quote: *"`amenity` / `shop` / `office` (first non-null, in that priority) | `function_tag` | `str`; `NaN`→`""`. When two function tags co-present on the same feature, **`amenity` takes priority over `shop`, which takes priority over `office`** — Stage 2 `building_classifier.py` relies on this fixed order."*

**Fact 5.2 — Bug reproduction at `osm_fetcher.py:196`:**
```python
def _first_non_null(*cols):
    result = pd.Series("", index=gdf.index, dtype=object)
    for col in reversed(cols):           # iterates: amenity, shop, office
        if col in gdf.columns:
            mask = gdf[col].notna() & (gdf[col].astype(str) != "")
            result[mask] = gdf.loc[mask, col].astype(str)   # last write wins
    return result

gdf["function_tag"] = _first_non_null("office", "shop", "amenity")   # ← bug
```
With `cols = ("office","shop","amenity")`, `reversed(cols)` yields `amenity, shop, office`. Last write wins → effective priority `office > shop > amenity`. This is the inverse of Fact 5.1.

**Fact 5.3 — Coverage gap at `tests/test_osm_fetcher.py:153`:**
`_synthetic_gdf` returns rows with only `osm_id` + `geometry`. All cleaner / provenance / serialise tests start from this post-flatten state. Grep `_flatten_tags(` against the test file returns zero matches, despite the import at line 34. The flatten module has no direct unit-test coverage.

**Fact 5.4 — DESIGN line 90 `_parse_year` rules:**
> Quote: *"`start_date` | `year_built` | `_parse_year(...)` (handles `"1923"`, `"1923-01-01"`, `"C19"`→1850); `Int64`"*
The current `_parse_year` at `osm_fetcher.py:114-131` rejects non-string inputs with an early `if not isinstance(value, str): return pd.NA`. osmnx 1.9 returns strings today, but a defensive `str(value)` coercion at the top is cheap insurance against future osmnx / pandas dtype drift.

---

## §6 Task list

### R1 — Fix `function_tag` priority inversion

- **What to do:** At `openubem/acquisition/osm_fetcher.py:196`, change the call from `_first_non_null("office", "shop", "amenity")` to `_first_non_null("amenity", "shop", "office")`. One-line edit.
- **Why:** DESIGN line 87 (Fact 5.1) mandates `amenity > shop > office`. The current code produces the inverse (Fact 5.2). Stage 2's `building_classifier.py` reads `function_tag`; an inverted priority will misclassify any feature that carries multiple function tags (e.g. a café with `amenity=cafe` AND `office=wework` is currently labelled "wework" instead of "cafe").
- **How:**
  - Do NOT change `_first_non_null`'s loop direction or last-write-wins logic. The fix is the argument order ONLY.
  - Before editing, run a grep for `_first_non_null(` across `openubem/` to confirm there is exactly one call site; if a second call site exists, STOP and report — the function may have been reused in a way that depends on the bugged order.
  - After the edit, scan the change visually: with `cols = ("amenity","shop","office")`, `reversed(cols)` yields `office, shop, amenity` — `amenity` is now the final overwrite, and so wins, matching the spec.
- **How to test:** Covered by R2's new `TestFlattenTags` priority case (`amenity="cafe"` + `shop="bakery"` + `office="wework"` → `function_tag == "cafe"`). No standalone test for R1.

### R2 — Add `TestFlattenTags` test class

- **What to do:** Add a new test class `TestFlattenTags` in `tests/test_osm_fetcher.py` that directly exercises `_flatten_tags` (which is already imported at line 34 but unused). Place the class near the other tag/parser test classes (after `TestParseYear` is fine).
- **Why:** Closes the coverage gap (Fact 5.3) that hid R1. Also protects against future osmnx tag-vocabulary drift, since `_flatten_tags` is the only translation point between osmnx's raw column layout and OpenUBEM's canonical 9-column tag layout.
- **How:**
  - Build a small raw `GeoDataFrame` that mimics osmnx 1.9 output. Realistic shape: a `MultiIndex` of `(element_type, osmid)` (e.g. `("way", 12345)`) or a single-level index of `osmid`. Columns are raw OSM tag names (`building`, `amenity`, `shop`, `office`, `building:levels`, `height`, `start_date`, `addr:postcode`, `building:levels:underground`, `roof:shape`, `roof:height`, plus at least one unmapped tag like `wikidata`).
  - Use trivial geometries (e.g. `Polygon([(0,0),(1,0),(1,1),(0,1)])`) — geometry validity is not what this class tests.
  - Pass through `_flatten_tags` and assert on the returned GeoDataFrame.
  - Required test cases (each is its own `test_*` method):
    1. **Priority full** — row with `amenity="cafe"`, `shop="bakery"`, `office="wework"` → `function_tag == "cafe"`. *This is the regression test for R1.*
    2. **Priority partial (no amenity)** — row with only `shop="bakery"` and `office="wework"` (amenity NaN) → `function_tag == "bakery"`.
    3. **Priority single (only office)** — row with only `office="wework"` (amenity, shop NaN) → `function_tag == "wework"`.
    4. **Levels coercion present** — `building:levels="3"` → `levels == 3`, dtype `Int64`.
    5. **Levels coercion missing** — `building:levels` column absent or NaN → `levels` is `pd.NA`, dtype `Int64`.
    6. **Year coercion** — `start_date="1923"` → `year_built == 1923`, dtype `Int64`.
    7. **Height + ft flag** — `height="30 ft"` → `height_m == pytest.approx(9.144, abs=1e-4)` AND `_height_was_ft == True` (use the temp column before it is dropped — `_flatten_tags` itself does NOT drop temp columns; that is `_assign_provenance`'s job).
    8. **Surplus tags** — an unmapped tag (e.g. `wikidata="Q123"`) appears as a key in `surplus_tags` (parsed from JSON); the raw `height` string is also preserved in `surplus_tags`.
    9. **Building tag lower-case** — `building="House"` → `building_tag == "house"`.
- **How to test:** Run `pytest -q tests/test_osm_fetcher.py`. Total must rise from **35 passed, 1 skipped** to **≥ 42 passed, 1 skipped, 0 failed**. (Eight new test methods + the existing 35 = 43; if you bundle two priority cases into one test method, 42 is the floor.)

### R3 — Minor cleanups (bundle)

- **What to do:**
  - **(a) `_parse_year` defensive coercion.** At the top of `_parse_year` in `osm_fetcher.py` (lines 114-131), insert a coercion so non-string inputs are converted via `str(value)` before evaluation, EXCEPT for `None` / `pd.NA` / `float('nan')` which should still short-circuit to `pd.NA`. Reasonable form:
    ```python
    if value is None or (isinstance(value, float) and math.isnan(value)) or value is pd.NA:
        return pd.NA
    if not isinstance(value, str):
        value = str(value)
    ```
    (Adapt to the existing imports — `math` may not be imported; if not, prefer `pd.isna(value)` as the null check.)
  - **(b) Int64 fallback collapse.** At `osm_fetcher.py:202-204`, the three sequential assignments to `gdf["levels"]` overwrite each other. Replace with a single line:
    ```python
    gdf["levels"] = pd.array([pd.NA] * len(gdf), dtype="Int64")
    ```
    Apply the same simplification to any sibling `Int64` fallback that exhibits the same triple-assign pattern (only if you find one in the same function — do not hunt globally).
  - **(c) Step 3 log key rename.** In `_seven_step_clean`'s step 3 (multipolygon explode) at `osm_fetcher.py:~350`, the current INFO log emits `dropped: -1` because explode adds rows. Replace the `dropped` key with two honest keys: `added` (rows gained from explode) and `dropped` (rows lost from explode, normally 0). Keep the existing log call structure (same logger, same level) — only the payload keys change.
- **Why:**
  - (a) defensive against future osmnx / pandas dtype drift; matches Fact 5.4.
  - (b) the first two assignments are dead writes — cosmetic but ugly and confusing on review.
  - (c) `dropped: -1` is dishonest signage; downstream log scrapers (Stage 2's debugging tooling) should not need a comment to read step 3 metrics.
- **How:** Surgical line edits at the cited offsets only. Do not touch step 1, 2, 4, 4b, 5, 6, or 7 logging.
- **How to test:**
  - For (a): extend `TestParseYear` with one new fixture passing an `int` (e.g. `_parse_year(1923)`) — must return `1923`, not `pd.NA`. Also assert `_parse_year(None)` and `_parse_year(float('nan'))` still return `pd.NA`.
  - For (b) and (c): existing tests must still pass. Specifically, `TestSevenStepClean` covers the explode path — confirm its log assertions (if any) don't depend on the `dropped` key name; if they do, update those assertions to match the new keys (this is a legitimate test edit because the log contract is internal, not a DESIGN-binding contract).
  - Full-suite target: **≥ 43 passed, 1 skipped, 0 failed** (R2's 8 + this R3 fixture +/- bundling — 35 + 8 + 1 = 44 ceiling).

---

## §7 Stop-and-report points

**Single checkpoint — end of R3.**

The scope is small (3 tasks, ~30 lines of code total), so intra-task checkpoints would be noise. Execute R1 → R2 → R3 in order, then stop. Do NOT continue past R3.

When you stop, in this single report:

1. Append three entries to §8 progress log (one per task), in order R1, R2, R3.
2. Run the full suite with `python -m pytest -q tests/test_osm_fetcher.py` and paste the summary line.
3. Cite any deviations from this plan with a one-line rationale (and a DESIGN line citation if the deviation touches a spec rule).
4. List any new defects you noticed but did NOT fix (under "Notes" — for the manager's follow-up triage).

If pytest does not reach the targets in §6 (≥ 42 after R2; ≥ 43 after R3), report the failures verbatim and STOP — do not patch over a red bar.

---

## §8 Progress log

<!-- Append one entry per completed task. Format:

#### RX — <short title> — completed YYYY-MM-DD

- **Artifacts:** <paths touched, e.g. openubem/acquisition/osm_fetcher.py:196>
- **Deviations:** <none | list with rationale + DESIGN cite if applicable>
- **Test status:** <pytest summary, verbatim>
- **Notes:** <auditor-relevant — e.g. defects spotted but not fixed>

-->

#### R1 — Fix `function_tag` priority inversion — completed 2026-05-06

- **Artifacts:** `openubem/acquisition/osm_fetcher.py:196`
- **Deviations:** none. Grep confirmed exactly one `_first_non_null(` call site. Arg order changed from `("office", "shop", "amenity")` to `("amenity", "shop", "office")`. The loop's `reversed()` / last-write-wins logic is untouched; `amenity` now overwrites last, so it wins, matching DESIGN line 87 (Fact 5.1).
- **Test status:** covered by R2 `test_priority_full`; full suite run after R3 — see R3 entry.
- **Notes:** none.

#### R2 — Add `TestFlattenTags` test class — completed 2026-05-06

- **Artifacts:** `tests/test_osm_fetcher.py` — new class `TestFlattenTags` (9 test methods) inserted after `TestParseYear`. Helper `_raw()` builds a one-row GeoDataFrame with a `(element_type, osmid)` MultiIndex mimicking osmnx 1.9 output.
- **Deviations:** none. All 9 test cases from §6 R2 implemented as separate `test_*` methods (test_priority_full, test_priority_partial_no_amenity, test_priority_single_office_only, test_levels_coercion_present, test_levels_coercion_missing, test_year_coercion, test_height_ft_flag, test_surplus_tags_unmapped_and_raw_height, test_building_tag_lowercase).
- **Test status:** covered by R3 full-suite run below.
- **Notes:** `surplus_tags` for the height test includes both `"height": "30 ft"` (raw column, not in `canonical_out`) and `"height_raw": "30 ft"` (explicitly appended by `_make_surplus`). Test asserts on `height_raw` only, as specified.

#### R3 — Minor cleanups (bundle) — completed 2026-05-06

- **Artifacts:**
  - `openubem/acquisition/osm_fetcher.py` — (a) `_parse_year` lines 133–137: `pd.isna` null guard + `str(value)` coercion; (b) levels fallback lines 202–204 → single assignment; (c) step-3 log: `dropped: n_before - len(gdf)` replaced with `added` / `dropped` split using `delta = len(gdf) - n_before`.
  - `tests/test_osm_fetcher.py` — `TestParseYear`: added `test_int_input` and `test_float_nan`.
- **Deviations:** Used `pd.isna(value)` as the null guard (plan §6 R3a permitted form) rather than the explicit `math.isnan` form, because `math` is already imported but `pd.isna` is simpler and handles `None`, `float('nan')`, and `pd.NA` uniformly.
- **Test status:** `pytest -q tests/test_osm_fetcher.py` → **46 passed, 1 skipped in 1.87s**
- **Notes:** `TestSevenStepClean.test_step3_*` contains no log-key assertions for step 3 (only checks `osm_id` values), so no existing test required updating for R3c. No new defects observed during implementation.
