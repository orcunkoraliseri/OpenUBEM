# MEASUREMENT — Did the fleet's Stage-1 files ever consume the height backfill? (OPEN-12 / OPEN-14)

> **Task:** N15, `PLAN_no-compute-queue-3.md` §6. **Measurement only — no remediation, no CPU, no
> network.** HEAD read at `bca92d0` throughout.

## Verdict (one sentence)

**No** — the fleet's Stage-1→Stage-2 path never calls `fusion.fuse()` at all for `height_m`/`levels`
(the classification fallback is a self-contained function that does not route through fusion), **and**
independently, every `01_buildings.gpkg` in the fleet — including `nyc_centre`'s — was committed
(`e063865`, 2026-06-30) three weeks before any Overture slice existed in the tree (`ef19141`,
2026-07-21), so no `01_buildings.gpkg` could physically have consumed a slice regardless of code path.
**§5.4's convergence (four no-slice cells = four worst-height cells) is a coincidence, not a causal
mechanism, and must be reported as one.**

---

## 1. The acquisition/classification path traced

`scripts/validation/v12_cell_pipeline.py` (last touched `03e2121`, 2026-07-02) is the fleet pipeline
(the only script that writes `01_buildings.gpkg` for the twelve phaseE cells; confirmed sole writer by
N07, round 2):

- **`step1_fetch()` (`v12_cell_pipeline.py:137-148`)** — if `01_buildings.gpkg` already exists it is
  loaded from cache and returned unchanged (`:139-141`); otherwise it calls
  `openubem.acquisition.osm_fetcher.ingest_buildings()` (`:144-145`) and writes the result straight to
  `01_buildings.gpkg` (`:148`). **`grep -in "fus(e|ion)|overture" openubem/acquisition/osm_fetcher.py`
  → no matches.** Step 1 has no fusion call of any kind.
- **`step2_classify_enrich()` (`v12_cell_pipeline.py:153-199`)** calls `BuildingClassifier().classify()`
  (`:165-166`), then `assign_climate_zones()`, then `enrich_semantics()` (`:197`, from
  `openubem/semantic/__init__.py`). **`grep -in "fus(e|ion)|overture" scripts/validation/
  v12_cell_pipeline.py` and `.../t08_full_sweep.py` → no matches in either file.**
- **`BuildingClassifier.classify()`**'s height/levels fallback is `_impute_levels()`
  (`openubem/semantic/building_classifier.py:123-142`, last touched `0df422e`, 2026-07-03) — a
  self-contained four-step ladder (`OSM_OBSERVED` → `HEURISTIC_HEIGHT` → `GROUPMEDIAN_LEVELS_MED` →
  `LEVELS_DEFAULT_LOW`). **It never imports or calls `openubem.semantic.fusion` or
  `openubem.semantic.imputation.impute_column`.** It is a different function from the tiered
  `impute_column`/`_fusion_tier` system entirely.
- **`enrich_semantics()`** (`openubem/semantic/__init__.py:273-433`) imports `impute_column`
  (`:20`) but the read of the full function body shows **zero call sites** for it inside
  `enrich_semantics` — the function's only imputation-shaped work is vintage resolution, envelope
  merge (`get_construction_set`), and loads merge (`get_loads`), none of which touch `height_m` or
  `levels`.
- Repo-wide, `impute_column(` (the entry point that would reach `_fusion_tier` →
  `fusion.fuse()`) has exactly two call sites: `openubem/semantic/draw_methods.py:121` (the opt-in KDE
  draw tier, not reached unless a caller explicitly requests it — E-UTCI-12/N09) and
  `openubem/semantic/construction_sets.py:323` (envelope properties, not height/levels).
  **`height_m`/`levels` are never passed to `impute_column` anywhere in the repository.**

**Conclusion of the code trace: the production fleet path that writes `01_buildings.gpkg` and then
classifies it has no route to `fusion.fuse()` for height or levels, independent of
`FUSION_SOURCES_BY_TARGET`'s value.** The empty default (`config.py:141`) is a second, independently
sufficient reason `fuse()` never fires, but it is not the only one — even a populated
`FUSION_SOURCES_BY_TARGET` would not reach this code path, because nothing in the classification chain
calls `fuse()` or `impute_column` for these two attributes. **No script under `scripts/` overrides
`FUSION_SOURCES_BY_TARGET`** — `grep -rn "FUSION_SOURCES_BY_TARGET\s*=" scripts/` → no matches; the
only overrides anywhere are in `tests/test_fusion.py`, `tests/test_height_backfill.py`, and
`tests/test_imputation_routing.py` (test-only, `monkeypatch`/local `cfg` objects, verified by N09).

---

## 2. The artifact's own history (ordering test)

`git log --follow` on `01_buildings.gpkg` for every affected cell and `nyc_centre`, plus the two
committed Overture slices:

| File | Commit | Date |
|---|---|---|
| `docs/docs_VALIDATION/.../phaseE/nyc_rural/01_buildings.gpkg` | `e063865` | 2026-06-30 |
| `docs/docs_VALIDATION/.../phaseE/nyc_suburban/01_buildings.gpkg` | `e063865` | 2026-06-30 |
| `docs/docs_VALIDATION/.../phaseE/austin_rural/01_buildings.gpkg` | `e063865` | 2026-06-30 |
| `docs/docs_VALIDATION/.../phaseE/austin_centre/01_buildings.gpkg` | `e063865` | 2026-06-30 |
| `docs/docs_VALIDATION/.../phaseE/nyc_centre/01_buildings.gpkg` | `e063865` | 2026-06-30 |
| `openubem/data/fixtures/fusion/overture_nyc_centre_slice.parquet` | `ef19141` | 2026-07-21 |
| `openubem/data/fixtures/fusion/overture_testcell_slice.parquet` | `ef19141` | 2026-07-21 |

Each `01_buildings.gpkg` shows exactly **one** commit in its `--follow` history (single origin, never
touched again at that path). **All twelve fleet `01_buildings.gpkg` files were written on 2026-06-30 —
three weeks before any Overture slice was committed on 2026-07-21.** A slice that does not exist in the
tree cannot have been read by a file written three weeks earlier. **This alone settles the question for
every cell, healthy or sick, independent of the code trace in §1.**

`git ls-files -- "openubem/data/fixtures/fusion/*"` → 6 files (`LICENSES.md`, `__init__.py`,
`assessor_testcell.gpkg`, `lidar_testcell_ndsm.tif`, `overture_nyc_centre_slice.parquet`,
`overture_testcell_slice.parquet`) — confirmed independently of N09, same result. No slice is tracked
for `nyc_suburban`, `nyc_rural`, `austin_rural`, or `austin_centre` at any commit.

---

## 3. The `nyc_centre` discriminating check

**§5.4 asked directly: does `nyc_centre`'s good height coverage come from its tracked slice, or from raw
OSM tags?** The check falls decisively on the **raw-OSM-tags** side, for two independent reasons:

1. **Code path (§1):** `nyc_centre`'s `01_buildings.gpkg` goes through the identical
   `step1_fetch → BuildingClassifier.classify → _impute_levels` chain as every other cell, which never
   calls `fusion.fuse()`. There is no cell-specific branch anywhere in `v12_cell_pipeline.py` that
   treats `nyc_centre` differently or reads the Overture slice.
2. **Ordering (§2):** `nyc_centre`'s `01_buildings.gpkg` was committed 2026-06-30 (`e063865`); its
   Overture slice did not exist until 2026-07-21 (`ef19141`) — three weeks later. The slice cannot have
   contributed to a file it postdates.

**Therefore `nyc_centre`'s heights came from raw OSM tags, exactly like every other cell's, and the
tracked slice played no role in it.** The convergence recorded in §5.4 — the four no-slice cells being
exactly the four worst on missing height — **is a coincidence** (most plausibly: the same
geography/mapping-density factors that leave a cell under-tagged in raw OSM also happen to be the cells
nobody bothered fetching an Overture slice for), **not a causal fusion mechanism, and this measurement
reports it as a coincidence.**

---

## 4. What this means for OPEN-12 vs OPEN-14

- **OPEN-12 (missing `height_m`, a data-coverage question) and OPEN-14 (backfill reproducibility) are
  NOT the same item wearing different names.** They are not even on the same code path: OPEN-12's
  numbers (§5.3, N06) describe the classifier's raw-OSM-tag coverage, entirely unrelated to fusion.
  OPEN-14 describes the separate, disconnected UTCI-arc backfill mechanism (E-UTCI-09,
  `docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md`), which
  itself was never reachable from a clean checkout (N09, round 2: `FUSION_SOURCES_BY_TARGET` still
  `{}`, no committed slice for the affected cells).
- **OPEN-12 remains a pure data-coverage problem** for the fleet-classification path: raw OSM tagging
  density is the only mechanism operating on `01_buildings.gpkg`, and it is what N06 already measured
  (34.39% fleet-wide no-`height_m`, 100%/100%/100%/84.50% at the four worst cells).
- **OPEN-14 remains its own, separate reproducibility defect** in the UTCI microclimate arc's own
  backfill script — unaffected by this finding one way or the other, since that backfill never touches
  `01_buildings.gpkg` or the fleet classification path measured here.

---

## 5. How-to-test results

- **(a) Verdict in one sentence at top:** stated above — **No**.
- **(b) `nyc_centre` discriminating check, reported explicitly:** §3 — falls on the **raw-OSM-tags**
  side; the tracked slice is not the explanation.
- **(c) Every claim about what a file consumed carries a commit hash and date:** §2 table (all six
  files, hash + date) and §1 (`v12_cell_pipeline.py` at `03e2121`/2026-07-02,
  `building_classifier.py` at `0df422e`/2026-07-03, `osm_fetcher.py` at `62e5968`/2026-06-09, all
  re-checked live at HEAD `bca92d0`).

**No item is undetermined.** Both the code trace (§1) and the artifact-ordering check (§2) converge on
the same "No" independently — either alone would have been sufficient, and their agreement is itself
worth recording.
