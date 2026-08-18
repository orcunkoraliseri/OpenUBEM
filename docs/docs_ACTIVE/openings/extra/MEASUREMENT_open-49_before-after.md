# MEASUREMENT — OPEN-49 T04: before/after on the twelve cells

> Executes T04 of `docs/docs_ACTIVE/openings/implemenation/PLAN_open-49-and-open-01-2026-08-13.md` §6.
> Measures the change in Step-2.2 semantic-enrichment **inputs** only. **No EnergyPlus was run, no
> cluster was touched.** No EUI claim is made anywhere in this document — floor area and energy are
> not computed here. The ±300 kWh/m² figure belongs to OPEN-49's original measurement and is not
> re-derived by this task.

---

## One-sentence verdict

**The eight-field fix is confirmed at the input level on all twelve real cells** (8,160 buildings,
every cell present, none skipped) — but **the moving/reproducing cell split from OPEN-49's original
EUI measurement does not reappear here**, and that is expected once the two experiments are told
apart: this task swaps the semantic-stage *code* at fixed classification, while OPEN-49's original
split compared two different classification *snapshots* at fixed (buggy) code. They are different
axes, and only one of them is what T04 was asked to run.

---

## Method

For each of the twelve adopted cells' cached `01_buildings.gpkg` (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`,
all twelve present — none skipped), re-ran `BuildingClassifier.classify()` → `assign_climate_zones()`
→ `enrich_semantics(random_seed=42)` twice: once with the pre-T02 source of
`openubem/semantic/__init__.py` (read via `git show 82bbd25^:openubem/semantic/__init__.py`, written
over the tree file with a plain copy, **never** `git restore`) and once with the current (post-T02,
committed) source. Classification and climate-zone assignment are identical in both passes — only
the semantic-enrichment code differs. `01_buildings.gpkg` is the raw OSM fetch (pre-classification),
matching what `scripts/validation/v12_cell_pipeline.py:step2_classify_enrich` consumes; `epw_path` was
set to a constant placeholder string since `enrich_semantics` only requires it non-null, never reads
its content.

Script: `scripts/analysis/open49_before_after_cells.py`.
Output: `openubem/outputs/comparisons/open49_before_after_cells.csv` (12 rows, one per cell).

```
.venv/Scripts/python.exe scripts/analysis/open49_before_after_cells.py --mode raw --label before --out <scratch>/open49_raw_before.parquet   # pre-T02 source on disk
.venv/Scripts/python.exe scripts/analysis/open49_before_after_cells.py --mode raw --label after  --out <scratch>/open49_raw_after.parquet    # post-T02 source on disk
.venv/Scripts/python.exe scripts/analysis/open49_before_after_cells.py --mode finalize --before <scratch>/open49_raw_before.parquet --after <scratch>/open49_raw_after.parquet --out openubem/outputs/comparisons/open49_before_after_cells.csv
```

Both raw passes wrote **8,160 rows** — the full fleet, all twelve cells present, zero skipped.

---

## Results — count of Unknown buildings whose `wwr` moved by more than 0.01

| cell | OPEN-49 "moving" cell? | n Unknown | n `wwr` changed >0.01 |
|---|---|---:|---:|
| austin_centre | yes | 37 | 34 |
| austin_rural | no | 7 | 7 |
| austin_suburban | no | 24 | 23 |
| austin_urban | no | 5 | 4 |
| la_centre | yes | 15 | 14 |
| la_rural | no | 0 | 0 |
| la_suburban | no | 2 | 2 |
| la_urban | yes | 2 | 2 |
| nyc_centre | yes | 35 | 29 |
| nyc_rural | no | 5 | 5 |
| nyc_suburban | no | 290 | 272 |
| nyc_urban | no | 228 | 218 |

Full eight-column min/mean/max before and after, per cell, are in
`openubem/outputs/comparisons/open49_before_after_cells.csv`.

---

## Does the moving/reproducing pattern reproduce? No — and here is why

OPEN-49's original register entry measured **4 of 12 cells whose `archetype_id` **set** changed
between the adopted run and the elevator-restoration re-run** also moved in EUI, while the other 8
(same archetype set in both runs) reproduced to ±0.07. That comparison held the **code** fixed (both
runs used the pre-OPEN-49-fix code) and varied the **classification** between two different runs.

T04, as specified, holds the **classification** fixed (one `classify()` call per cell, one result,
reused for both passes) and varies the **code** (pre-T02 vs post-T02). These are orthogonal axes.
Swapping from the old draw mechanism (one shared vectorised block, bounds from present archetypes) to
the new one (per-building `blake2b(osm_id)` key, bounds from the fixed cross-archetype table) changes
**almost every** Unknown building's `wwr` in **almost every** cell, moving or not — because the two
RNG algorithms simply do not produce the same stream for the same row, regardless of whether that
cell happens to be one where classification drifted between two OSM fetches. The near-100% "changed"
fraction in `nyc_suburban` (272/290) and `nyc_urban` (218/228) — both **not** OPEN-49-moving cells —
makes this plain: the count of buildings whose `wwr` moved tracks **how many Unknown buildings the
cell has**, not whether it was on the moving or reproducing side of the original split.

**This is the result, reported as the plan instructs when the pattern does not hold**: OPEN-49's
mechanism story (moving vs. reproducing cells) is a statement about classification-driven coupling
under the *old* code, and it is not restated or re-tested by an old-code-vs-new-code comparison at
fixed classification. What T04 *does* confirm is the eight-field fix's effect size on real cell data:
the fix changes nearly every Unknown building's PDE/scalar draw, cell by cell, which is the expected
footprint of a change to the RNG mechanism itself — not evidence against the fix, and not a claim
about EUI.
