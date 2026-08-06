# MEASUREMENT — Which step writes the wrong `archetype_id` into `05_results.gpkg`? (OPEN-06)

> **Slug:** `open-06_archetype-writer-trace` · **Date:** 2026-08-06 · **Task:** N07 of
> `docs/docs_ACTIVE/openings/implemenation/PLAN_no-compute-queue-2.md`.
> **MEASUREMENT ONLY. No remediation performed or proposed.** No EnergyPlus, no IDF generation, no
> cluster, no fleet pass. All code paths were read; the only computation performed was calling the
> already-imported, already-existing `BuildingClassifier().classify()` on data already on disk (the
> same class of operation N04 already performed) — this is code-tracing, not a pipeline run.

---

## 0. Verdict up front

**None of the three named hypotheses (stale join / lossy mapping / overwrite) could be confirmed with
a `path:line` that reproduces the defect.** All three were tested directly against the actual write
path and against 5 of the 41 mislabelled buildings (3 in `nyc_rural`, 1 in `la_urban`, 1 in
`nyc_centre`), and **all three are contradicted by direct evidence**:

- **Lossy mapping — DISPROVED.** `LargeHotel`/`SmallHotel` are real, valid archetypes in the live
  vocabulary (`openubem/data/openstudio_archetypes.json:86,93`) and in the classifier's rule table
  (`openubem/semantic/building_classifier.py:212,216`). No whitelist step removes them.
- **Overwrite (post-hoc patch) — DISPROVED for the buildings checked.** The only known script that
  hand-patches the canonical `05_results.*` files, `scripts/validation/phaseE_recover_10.py`, touches a
  disjoint, hard-coded population of 10 osm_ids (the OPEN-11 inverted-geometry buildings), none of
  which overlap the 41 Hotel mislabels (verified by reading its `GROUP_A`/`GROUP_B` constants,
  `scripts/validation/phaseE_recover_10.py:38-50`).
- **Stale join (cached/reused artifact from an earlier run) — DISPROVED for every cache point found.**
  `step1_fetch`'s geometry cache holds the frozen, git-unchanged raw data (confirmed — see §3). Step 2
  has no cache. Step 3's own manifest cache is unconditionally pre-empted:
  `scripts/validation/v12_cell_pipeline.py:986-990` deletes any existing
  `03_idf_manifest.parquet` immediately before every `step3_generate()` call ("Mandatory fresh IDF
  regen: clear any stale manifest so IDFs rebuild from current code+data") — this guard has existed
  since **2026-06-25** (`git blame`, commit `075934c2`), i.e. it already existed when the Phase-E
  fleet that produced the committed baseline ran (2026-07-01 to 07-03). So the classic "leftover
  parquet from an earlier attempt" mechanism cannot have fired for the standard `run_cell()` entry
  point that both the original baseline and its `E-R3-3` promotion used.

**What is true instead, and is itself the finding:** every stage of the write path, traced end to end
at `path:line` and **re-executed** (not just read) against the exact frozen inputs the committed file
was built from, reproduces `LargeHotel`/`SmallHotel` — never Office. The committed
`05_results.gpkg`/`05_results.csv` nonetheless carry Office archetypes for these buildings, with real,
successfully-simulated EUI values (not NaN, not a dropped/failed row). **The current code, run against
the current frozen inputs, cannot reproduce the value the committed file holds.** Per this plan's own
stop condition (§6 N07 "how to test" (b): *"if your trace predicts a different value than the file
holds, your trace is wrong: STOP and report"*) — that is exactly the state reached here, and it is
reported rather than resolved.

**One writer, not several.** Only one code path writes `archetype_id` into the committed
`docs_VALIDATION/.../phaseE/<cell>/05_results.*` files: `scripts/validation/v12_cell_pipeline.py`
(Step 2 → Step 3 → Step 5, detailed below). No second writer of this column was found for this file.

---

## 1. Provenance ledger

| File | Role | Git state |
|---|---|---|
| `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg`/`.csv` (12 cells) | The file under investigation | Last touch **`0df422e`** (2026-07-03, E-R3-3 promotion, T11.7). Working tree = HEAD, no uncommitted changes. |
| `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` | Raw Stage-1 input actually classified | Last touch **`e063865`** (2026-06-30) — **one commit before** `0df422e`. `0df422e` did **not** touch this file (confirmed by `git log --follow`). This is exactly the file the T11 rerun's own plan (`docs_DONE/BUGS/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md` fact M4/T11.1) says it pre-seeded from, to freeze geometry. |
| `openubem/semantic/building_classifier.py` | Classifier | Last touch `0df422e` (2026-07-03), unchanged since, confirmed by N04 and re-confirmed here. |
| `scripts/validation/v12_cell_pipeline.py` | The fleet-generation script that produced the committed baseline (per `PLAN_archetype_threshold_fix_E-R3-3.md` M1/T11.2: `python scripts/validation/v12_cell_pipeline.py <cell> --output-subdir phaseE_er33`) | Last touch `03e2121` (2026-07-02) — the version current for essentially the whole T11 run window; unchanged since. |
| `openubem/idf/builder.py` | Step 3 IDF/manifest writer (`BuildingIDF.build()`, `run_step3()`) | Last touch `69373f9` (2026-07-27) — **after** T11. Checked separately: the archetype-pass-through property verified at HEAD was **also** true in the exact commit current during T11 (`03e2121`, `git show 03e2121:openubem/idf/builder.py`) — see §2.2. |
| `openubem/results/__init__.py` (`aggregate_results`) | Step 5 orchestrator | Last touch `6bebc03` (2026-07-02, 21:37 local) — landed **during** the 11-cell fan-out window (fan-out ran 07-01 23:14 → 07-02 22:07); the join logic was verified identical at that commit too (§2.3). |
| `openubem/results/aggregator.py` (`join_results`) | Step 5 key-based merge | Last touch `b2ca38f` (2026-06-26) — unchanged since before T11. |
| `scripts/validation/phaseE_recover_10.py` | Candidate second writer (hand-patch script) | Read at HEAD; targets a disjoint, hard-coded 10-building population (§0). |
| `scripts/cluster/t20_harvest_layout_assign.py` | Independent corroborating source (R06, 2026-08-04) | `PHASED_RESULTS` constant (`:84-85`) resolves to the **same** `docs_VALIDATION/.../phaseE` path — confirms R06's finding is about this exact file, not a different one. |

---

## 2. The write path, traced `path:line` with the call chain

**Entry point → write site**, one hop per line (fleet pipeline reachability, how-to-test (a)):

1. `scripts/validation/v12_cell_pipeline.py:946 run_cell(cell_name, output_subdir)` — the one function
   that runs a cell end to end (called from `__main__`, `:1083` `ap.add_argument("cell_name", ...)`).
2. `:973 gdf_raw = step1_fetch(...)` → `:137-150` — caches/loads `01_buildings.gpkg` verbatim (no
   transform of tags).
3. `:977 gdf_57, schedule_library = step2_classify_enrich(...)` → `:153-199` — line **166**:
   `gdf_26 = bc.classify(gdf_raw2)` is the **only** place `archetype_id` is *computed* anywhere in this
   chain. Everything downstream **reads** this value; nothing downstream **recomputes** it.
4. `:986-990` — stale-manifest guard fires (unconditionally deletes any existing
   `03_idf_manifest.parquet`) immediately before generation.
5. `:993 idf_manifest = step3_generate(gdf_57, schedule_library, step3_dir)` → `:202-219`, which calls
   `:212 run_step3(gdf_57, schedule_library, step3_dir, n_jobs=1)`.
6. `openubem/idf/builder.py:683 for _, row in gdf.iterrows(): BuildingIDF(row, ...).build(...)` —
   direct, key-free, order-preserving row iteration (`n_jobs=1`, so no `loky` parallel path, no
   `row.to_dict()` reconstruction). `build()` at `:395 arch = str(row["archetype_id"])`, then **every**
   return branch (`:412, 496, 546, 559, 580, 621` at HEAD; `:389, 452, 465, 486, 527` at the
   T11-current commit `03e2121`) emits `"archetype_id": arch` **unchanged**. No branch in `build()`
   ever reassigns `arch` to a different value.
7. `scripts/validation/v12_cell_pipeline.py:713 "archetype_id": idf_row["archetype_id"]` inside
   `_build_enriched_gdf()` (`:651-718`) — copies `idf_manifest`'s per-row `archetype_id` 1:1, iterating
   `idf_mf.iterrows()` directly (no merge, no join key, so no join-alignment risk here).
8. `:742 aggregate_results(sim_mf, idf_manifest, enriched_gdf, ...)` (`enriched_gdf` here **is** the
   `_build_enriched_gdf()` object from step 7) → `openubem/results/__init__.py:179
   results_gdf = join_results(enriched_gdf, metrics_df)`.
9. `openubem/results/aggregator.py:74 result = enriched.merge(metrics_sub, on="_osm_id_key", how="left", ...)`
   — a **key-based** merge (`osm_id` string equality both sides), not positional. `archetype_id` is
   **not** in `_STEP5_COLS`/`metric_cols` (`aggregator.py:18-48,71`), so it is never touched by this
   merge — it survives from the `enriched` (left) side untouched, for both success **and**
   non-success rows (`__init__.py:163-174` builds NaN metric rows but never sets `archetype_id`).
10. `export_results(results_gdf, output_dir, summary)` writes `05_results.gpkg`/`.csv`/`.geojson`
    (`v12_cell_pipeline.py` step 5 call chain terminates here).

**Conclusion of the trace:** `archetype_id` in the committed file is, by construction of every hop
above, byte-identical to whatever `BuildingClassifier().classify()` returned at step 3 for that osm_id.
There is no second computation, no lookup table, no whitelist substitution, and no positional
join anywhere between steps 3 and 10.

### 2.1 Re-executing the trace against the real 41-row population (3 buildings, plus 2 more for
robustness)

Ran the **exact** production subsetting from `step2_classify_enrich` (`_INPUT_SCHEMA_COLUMNS` subset +
`levels` cast to `Int64`) against the **frozen, git-unchanged** `01_buildings.gpkg`, then
`BuildingClassifier().classify()` — first on a 3-row subset, then on the **full 198-row `nyc_rural`
cell** (to rule out a batch-size-dependent bug), then on two more cells' full data:

| cell | osm_id | committed `05_results.gpkg` `archetype_id` | re-derived `classify()` output (this task) | `archetype_source` | committed `simulation_status` |
|---|---|---|---|---|---|
| `nyc_rural` | `way/965718400` | SmallOffice | **SmallHotel** | `RULE_LODGING_TIER,LEVELS_DEFAULT_LOW` | success |
| `nyc_rural` | `way/965718402` | SmallOffice | **SmallHotel** | `RULE_LODGING_TIER,LEVELS_DEFAULT_LOW` | success |
| `nyc_rural` | `way/965718403` | SmallOffice | **SmallHotel** | `RULE_LODGING_TIER,LEVELS_DEFAULT_LOW` | success |
| `la_urban` | `way/401910463` | SmallOffice | **SmallHotel** | `RULE_LODGING_TIER,HEURISTIC_HEIGHT` | success (89.28 kWh/m²) |
| `nyc_centre` | `way/260180778` | LargeOffice | **LargeHotel** | `RULE_LODGING_TIER,GROUPMEDIAN_LEVELS_MED` | success (112.10 kWh/m²) |

Raw tag confirmed for all 5: `building_tag == "hotel"` (nyc_rural, la_urban¹) or the row's raw tag
matches "hotel" per N04's spot-check (nyc_centre). `function_tag` is blank for the nyc_rural rows —
the rule fires on `building_tag` alone, exactly as coded
(`building_classifier.py:212,216: (ft in {...} or bt in {...})`).

¹ `la_urban way/401910463` is the "Wilshire Serrano Motel" building N04 spot-checked directly.

**Full-batch check (rules out an index/order bug specific to small subsets):** classifying all 198
`nyc_rural` rows in one call still returns `SmallHotel` for the 3 targets (archetype distribution:
150 SmallOffice, 22 MidriseApartment, 6 FullServiceRestaurant, 5 OpenUBEMUnknown, 4 Courthouse,
**4 SmallHotel**, ...). Same result as the row/subset-level call. **How-to-test (b) result: FAIL** —
the trace predicts SmallHotel/LargeHotel; the committed file holds SmallOffice/LargeOffice for all 5
buildings checked. Per the plan's own rule, this is reported, not silently resolved.

### 2.2 Version-drift check on `builder.py` (it was touched after T11)

`openubem/idf/builder.py` was modified twice after T11 (`3a925f9` 2026-07-25, `69373f9` 2026-07-27,
both layoutAssigner-arc work). Read `git show 03e2121:openubem/idf/builder.py` — the version current
for essentially the whole T11 execution window — directly: `build()` at that commit (`:368-538`) does
`arch = str(row["archetype_id"])` (`:372`) and re-emits it unchanged in every return branch
(`:389,452,465,486,527`), identically to HEAD. **No drift affects this conclusion.**

### 2.3 Version-drift check on `results/__init__.py` (commit landed mid-fan-out)

`6bebc03` (2026-07-02 21:37 local) landed while the 11-cell fan-out (`bcjz97x9w`, launched 07-01 23:14,
completed 07-02 22:07) was already running as a live Python process — but a running process does not
hot-reload modules from disk, so it used whichever version was on disk at its own launch time
regardless. Read `git show 6bebc03:openubem/results/__init__.py` directly: `join_results(enriched_gdf,
metrics_df)` call and the archetype-column handling are identical to HEAD (`:179`, `:262-303`
unchanged). **No drift affects this conclusion either — both the pre- and post-commit code give the
same trace result.**

---

## 3. Independent corroboration (R06, 2026-08-04) — same file, different method, same verdict

`docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_REMAINder.md:1174-1194`
(R06, item 2) independently found, by reading a **raw retained cluster `in.idf`** (not a re-derivation —
the actual file EnergyPlus was handed, for `way/965718400`, retrieved because the sbatch template's
`set -e` skips cleanup only on a Fatal-terminated task): the file reads **`Building, HotelSmall`
verbatim**. That run is from the **T20 `layout_assign`** harvest generation (a different generation
from Phase-E's own `auto`-mode run — register OPEN-28's generation-mismatch warning applies; this is
noted as an observation, not merged into the Phase-E-specific finding above). R06 also confirms
`PHASED_RESULTS` in `scripts/cluster/t20_harvest_layout_assign.py:84-85` resolves to the exact same
`docs_VALIDATION/.../phaseE` path investigated here, and independently states the column is "STALE"
without identifying which step made it so — the same open question this task was asked to close.
R06's finding and this task's finding **agree** (both find Hotel is the correct label and Office is
what the file holds) and **neither** locates the writer.

---

## 4. What was ruled out, explicitly

- **Hotel templates absent from the archetype vocabulary** — false;
  `openubem/data/openstudio_archetypes.json:86,93` define `SmallHotel`/`LargeHotel`.
- **`TEMPLATE_ROUTING` silently reassigning the archetype** — false; `TEMPLATE_ROUTING`
  (`openubem/idf/builder.py:53-64`) has no Hotel entry (falls back to `commercial_base.idf` as the IDF
  *template file*, a physical-model choice) but is never used to overwrite the `archetype_id` *string*
  that flows into the manifest/results — confirmed by reading every line that sets or reads `arch` in
  `build()`.
- **Step 3 manifest cache reusing a stale, earlier-code-era file** — false; the guard at
  `v12_cell_pipeline.py:986-990` (present since 2026-06-25, before T11 ran) unconditionally deletes any
  pre-existing manifest before every generation call.
- **A batch-size-dependent classifier bug (row-order/index misalignment on the full fleet)** — false;
  reproduced on 1-row, 3-row, and full-198-row batches with identical (correct) output.
- **A second script patching `archetype_id` post-hoc** — no second writer of this column was found;
  the one known hand-patch script (`phaseE_recover_10.py`) targets a disjoint, unrelated 10-building
  population.
- **Code drift between the T11 run window and HEAD masking the mechanism** — checked explicitly for
  the two files touched after T11 (`builder.py`, `results/__init__.py`); both give identical trace
  results at the T11-era commit and at HEAD.

## 5. What remains genuinely unresolved (reported as an unknown, not guessed at)

The committed `05_results.gpkg`/`.csv` for these 5 (and by extension, presumably all 41) buildings
carry a `simulation_status == "success"` row with a real, plausible total EUI — i.e. Phase-E's own run
actually built and simulated *something* under the Office label; this was not a dropped/failed row
patched with a placeholder. Given `build()`'s unconditional pass-through of `row["archetype_id"]`
(confirmed at both the T11-era and current commit), the only way this is consistent with the trace is
if `gdf_57["archetype_id"]` — i.e., the **live output of `step2_classify_enrich`'s own `classify()`
call, at the moment it actually ran during the 2026-07-01–03 T11 execution** — held "SmallOffice" /
"LargeOffice" for these rows, even though the identical code, called today against the identical frozen
input, holds "SmallHotel"/"LargeHotel". `classify()` is a pure function of its input row and of module
constants that are unchanged in git since 2026-05-06 (`RULE_LODGING_TIER`, confirmed by `git log -S`)
for the hotel rule specifically. **No mechanism found by static reading of the current or T11-era
repository explains how the same deterministic function, on the same committed input, could have
returned a different value at write time than it returns now.** The T11 execution window is
independently documented (`PLAN_archetype_threshold_fix_E-R3-3.md` §8, T11 entries dated 2026-07-01)
as having involved at least one live, uncommitted, mid-run hotfix to this same pipeline script
(the `v12_cell_pipeline.py:520` reroute-lambda signature fix, applied to the working tree during the
run and only described in the progress log, not isolated as its own commit until folded into
`03e2121`) — establishing that the code actually executing during the T11 window is not guaranteed to
be fully captured by any single git commit. Whether an analogous transient, unrecorded edit touched
classification behaviour during that same window **cannot be determined from files on disk** — this is
reported as an open, unresolved provenance gap, not asserted as the cause.

---

## 6. How-to-test results (plan §6 N07)

- **(a) PASS.** The named write site (`v12_cell_pipeline.py:713` inside `_build_enriched_gdf()`,
  ultimately sourced from `step2_classify_enrich:166`) is reachable from the fleet entry point
  `run_cell()` by the ten-hop chain in §2, each hop cited by `path:line`.
- **(b) FAIL, reported per the plan's own instruction.** All 5 traced buildings predict
  SmallHotel/LargeHotel; the committed file holds SmallOffice/LargeOffice for all 5. The trace does
  **not** arrive at the value the file holds — stated explicitly rather than papered over.
- **(c) One writer.** Only `v12_cell_pipeline.py`'s Step 2→3→5 chain writes `archetype_id` into the
  committed `docs_VALIDATION/.../phaseE/<cell>/05_results.*` files. `phaseE_recover_10.py` is a second
  script capable of writing into these files, but its scope is a disjoint 10-building population that
  does not include any of the 41 Hotel mislabels.

---

## 7. Artifacts

- This report.
- No new CSV artifact was produced — every number here is either quoted from `open06_mislabel_population.csv`
  (N04's artifact, unchanged) or re-derived inline via the `classify()` calls documented in §2.1 and
  reproducible from the commands described there (no throwaway script was persisted; the exact
  subsetting/casting steps are quoted verbatim in §2.1 so this is reproducible from `path:line` alone).
- **No files under `openubem/`, `docs_VALIDATION/`, or the register were modified by this task.**
