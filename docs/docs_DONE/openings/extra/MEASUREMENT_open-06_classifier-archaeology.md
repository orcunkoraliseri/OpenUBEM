# MEASUREMENT — OPEN-06: which code state, if any, emits `Office` for the 41

**Date:** 2026-08-18 · **Task:** T04 of `PLAN_five-items-2026-08-18.md`

## 0. Verdict up front

**Answer is (a): a named commit emits Office for these 41, quoted with its count.** Commit
`67ede73` (2026-07-01 20:14:33 -0400) reproduces the committed `05_results.gpkg` archetype exactly
for all 41 buildings — not just "some Office family value" but the **exact same Office subtype**
(`SmallOffice`/`MediumOffice`/`LargeOffice`) recorded for every one of the 41 osm_ids. This closes
OPEN-06's central question and, as a side effect, resolves the open provenance gap left by N07
(`MEASUREMENT_open-06_archetype-writer-trace.md` §5): the column **did** come from this repository's
classifier — just from an earlier commit than the one N07 checked.

**Mechanism found, git-tracked, not a guess:** the one and only diff to
`openubem/semantic/building_classifier.py` between `67ede73` and `0df422e` is the Hotel rule gaining
a `building_tag` check it did not have before:

```
-    if ft in {"hotel", "motel", "guest_house"} and levels_imputed >= _HOTEL_LARGE_MIN_LEVELS:
+    if (ft in {"hotel", "motel", "guest_house"} or bt in {"hotel", "motel", "guest_house"}) and levels_imputed >= _HOTEL_LARGE_MIN_LEVELS:
```
(and the mirror-image change for the `SmallHotel` branch immediately below it). At `67ede73`, the
Hotel rule read **only** `function_tag`. All 41 of these buildings have `hotel`/`motel` in
`building_tag` with `function_tag` blank (already established by N04's spot-checks and N07 §2.1) —
so at `67ede73` they fell through the Hotel rule entirely and matched a later Office rule instead.
`0df422e` (2026-07-03 10:53:14 -0400) added the `building_tag` check, which is exactly the fix that
makes these 41 buildings classify as Hotel — and has, ever since.

**Why the committed file still holds the old (Office) values despite being "last touched" by
`0df422e`:** the T11 fleet fan-out that generated `05_results.gpkg` ran 2026-07-01 23:14 through
2026-07-02 22:07 (per N07's provenance ledger) — entirely **after** `67ede73` landed
(2026-07-01 20:14) and entirely **before** `0df422e` landed (2026-07-03 10:53, more than 12 hours
after the fan-out finished). The commit that promoted the fleet's output into the repo (`0df422e`)
bundled the classifier's Hotel-rule fix together with results that had already been generated using
the pre-fix classifier. `0df422e`'s "last touch" of `05_results.gpkg` is a promotion of already-computed
output, not a re-run under `0df422e`'s own classifier code.

---

## 1. Population and method

Population: `openubem/outputs/comparisons/open06_mislabel_population.csv`, 41 rows (unchanged,
reused from N04 — not recomputed here), spanning 5 cells: `nyc_centre` (26), `la_urban` (5),
`la_centre` (4), `nyc_rural` (4), `austin_centre` (2).

**Six commits ever touched `openubem/semantic/building_classifier.py`** (`git log`, oldest first):
`42f0c1d` (2026-05-06), `62e5968` (2026-06-09), `7635ce2` (2026-06-12), `67ede73` (2026-07-01),
`0df422e` (2026-07-03), `6aeebb0` (2026-08-13).

**Working tree = `6aeebb0` exactly.** `git diff 6aeebb0 -- openubem/semantic/building_classifier.py`
is empty, so "HEAD" and "`6aeebb0`" are the same object; the control run used the real, already-installed
package (`from openubem.semantic.building_classifier import BuildingClassifier`), not a re-imported
scratchpad copy, matching N04/N07's own method.

**Read-only git only.** Each of the other five commits' `building_classifier.py` was extracted with
`git show <sha>:openubem/semantic/building_classifier.py > scratchpad/classifiers/classifier_<sha>.py`
— never `git checkout`. Each extracted file was then imported as an isolated Python module
(`importlib.util.spec_from_file_location`, a unique module name per commit) and its
`BuildingClassifier` class instantiated and called directly.

**Harness:** `scripts/analysis/open06_classifier_archaeology.py`. For each cell, it loads the frozen
`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`, applies the exact
production subsetting `step2_classify_enrich()` uses (`scripts/validation/v12_cell_pipeline.py:153-166`
— `gdf_raw[_INPUT_SCHEMA_COLUMNS].copy(); gdf_raw2["levels"] = gdf_raw2["levels"].astype("Int64")`),
and classifies the **full cell** (not just the 41-row population subset) before filtering the output
down to the population's osm_ids.

**Methodological note, found and corrected during this task, reported rather than silently fixed:**
classifying only the population subset (instead of the full cell) changed the result for 2 of the 41
buildings (`austin_centre way/231123149` and `way/328723692` flipped `LargeHotel`→`SmallHotel`),
because the levels-imputation fallback (`GROUPMEDIAN_LEVELS_MED`) computes a group-median over
whatever batch it is given — subsetting to 2 rows instead of the full cell changes that median. The
harness was corrected to classify the full cell every time (matching N07's own full-cell method,
`MEASUREMENT_open-06_archetype-writer-trace.md` §2.1 "ruled out a batch-size-dependent bug" by testing
full-198-row batches) before filtering to the population. This is noted as a caveat for anyone reusing
a subset-only harness on this classifier: **group-median imputation is batch-dependent by design; a
population subset is not a safe substitute for the full cell.**

**Second methodological caveat, disclosed rather than hidden:** all six historical module versions
import archetype/tag-mapping data via `importlib.resources.files("openubem.data")`, which resolves to
the **currently-installed** package data files, not that commit's own data files. `git log` shows
`openubem/data/osm_to_use_class.json` and `openubem/data/openstudio_archetypes.json` were touched by
exactly two commits: `42f0c1d` (initial add) and `67ede73` (update). So the archaeology for `42f0c1d`,
`62e5968`, and `7635ce2` — all of which predate `67ede73`'s data update — runs that era's **code**
against **today's** data files, not the data those commits actually shipped with. This does not affect
the decisive finding (which rests on `67ede73` and `0df422e`, both post-dating the last data-file
change), but it means the earlier three commits' exact archetype-subtype counts below should be read
as "this code's logic against current data," not a byte-for-byte historical reproduction. Per the
plan's own rule ("do not stub imports to force a load — a forced load does not emit what that era's
code emitted"), no attempt was made to reconstruct the historical data files; the discrepancy is
reported instead.

---

## 2. Control (step 3, required before any archaeology)

**Control reproduced N04 exactly:** HEAD (`6aeebb0`) classifies the full cells and, filtered to the
41-row population, yields **41/41, 33 `LargeHotel` + 8 `SmallHotel`** — the exact figures N04 recorded.
No archaeology was reported before this control passed.

---

## 3. Per-commit results

All six commits **loaded successfully** — none is `NOT_LOADABLE`. (Each only imports `json`, `logging`,
`re`, `importlib.resources`, `pathlib`, `geopandas`, `pandas`, and the currently-installed
`openubem.acquisition.osm_fetcher._SCHEMA_COLUMNS` — a live, current-package import present at every
commit, so nothing historical had to be resolved.)

| commit | date | loadable | archetype family emitted (all 41) | exact match to committed `05_results.gpkg` (subtype-for-subtype) |
|---|---|---|---|---|
| `42f0c1d` | 2026-05-06 | yes | Office (20 Small / 19 Medium / 2 Large) | 15 / 41 |
| `62e5968` | 2026-06-09 | yes | Office (20 Small / 19 Medium / 2 Large) | 15 / 41 |
| `7635ce2` | 2026-06-12 | yes | Office (6 Small / 18 Medium / 17 Large) | 20 / 41 |
| `67ede73` | 2026-07-01 | yes | Office (7 Small / 21 Medium / 13 Large) | **41 / 41 — exact** |
| `0df422e` | 2026-07-03 | yes | Hotel (8 Small / 33 Large) | 0 / 41 |
| `6aeebb0` (= HEAD) | 2026-08-13 | yes | Hotel (8 Small / 33 Large) — control | 0 / 41 (matches N04, not the mislabel) |

All four pre-`0df422e` commits emit some flavour of Office for all 41 buildings (the Hotel rule's
`function_tag`-only gate is unchanged from `42f0c1d` through `67ede73` — confirmed by reading each
consecutive diff; only the *size-tier* boundaries for Office moved between them, via the E-R3-1/E-R3-2
total-floor-area changes at `62e5968`→`7635ce2` and the E-R3-3 threshold rework at `7635ce2`→`67ede73`,
which is why only `67ede73` lands on the *exact* subtype split the committed file holds). `0df422e` and
`6aeebb0` both emit Hotel for all 41, with `0df422e`'s Hotel-rule fix (§0) as the dividing line.

**Full row-level detail:** `openubem/outputs/comparisons/open06_classifier_archaeology.csv` — 246 rows
(41 buildings × 6 commits), columns `commit, cell, osm_id, emitted_archetype, load_error`.

---

## 4. Relationship to N07's open question

N07 (`MEASUREMENT_open-06_archetype-writer-trace.md` §5) traced the write path end to end and found
that the current code, run against the frozen input, could not reproduce the committed file's Office
values — and explicitly flagged this as an unresolved provenance gap, floating (without confirming) the
possibility of "an analogous transient, unrecorded edit" during the T11 execution window. This task
finds the actual mechanism, and it is **not** an unrecorded edit — it is the tracked, committed
`67ede73`→`0df422e` classifier change, landing in the gap between when the T11 fan-out ran
(2026-07-01 23:14 → 2026-07-02 22:07) and when its results were promoted into the repo (`0df422e`,
2026-07-03 10:53). N07's own write-path trace (`v12_cell_pipeline.py` Step 2 → 3 → 5, §2 of that
report) is unaffected and still correct — it just tested the classifier at the wrong commit for what
the T11 run actually executed.

---

## 5. Answer, per the plan's required form

**(a) A named commit emits Office for these 41, quoted with its count:** `67ede73` (2026-07-01),
41/41 exact subtype match to the committed `05_results.gpkg`.

This is not "the value did not come from this repository" (the register's alternative framing) — the
value came from this repository, from a classifier state (`67ede73`) that was live for roughly 38 hours
between its own commit and the fix that superseded it, and that happened to be the state in effect
during the one fleet run whose output was promoted to the committed baseline.

---

## 6. Artifacts

- `scripts/analysis/open06_classifier_archaeology.py`
- `openubem/outputs/comparisons/open06_classifier_archaeology.csv` (246 rows)
- This report.
- Scratchpad (not committed, not under `docs/`): `scratchpad/classifiers/classifier_<sha>.py` for the
  five non-HEAD commits, extracted via `git show <sha>:path`.

**No files under `openubem/`, `docs_VALIDATION/`, or the register were modified by this task.**
