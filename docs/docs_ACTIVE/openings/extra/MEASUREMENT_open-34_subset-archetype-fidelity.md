# MEASUREMENT — OPEN-34: is a 3-building local re-run archetype-faithful to the fleet?

**Task:** N05, `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_no-compute-queue.md` §6.
**Scope:** Stage 2 only (semantic enrichment + classification). No Step 3, no IDF generation,
no EnergyPlus, no cluster. Measurement only — no remediation attempted, none proposed.
**Repo state:** HEAD `bca92d0a6cdc33923bea8424f1b86ab0f94d82d9`. `git status --short` on every file
read below (`openubem/semantic/building_classifier.py`, `openubem/geometry/footprint.py`,
`openubem/semantic/__init__.py`, `scripts/cluster/t08_full_sweep.py`,
`docs/docs_VALIDATION/.../nyc_centre/05_results.gpkg`, `.../01_buildings.gpkg`) is clean — none
modified by this task.

## 1. The experiment

Ran `t08_full_sweep.run_step2()` — the real function `t08_local_remainder.py` and the E01c harness
both drive, imported from its real file, not reimplemented — twice for `nyc_centre`:

- **RUN A** — the same 3-building subset E01c used (`way/42496314`, `way/42496352`, `way/42500728`),
  filtered from `01_buildings.gpkg`.
- **RUN B** — the **whole cell**, `gdf_raw = gpd.read_file(01_buildings.gpkg)` with **no filter**,
  exactly as `t08_local_remainder.py:635-643` loads it in production (738 raw buildings).

Both runs took under one second combined (script: total wall time 0.6 s — see driver script log,
`n05_work/run.log`, reproduced below); the "STOP if it looks like minutes" clause in §6/N05 never
triggered. No cost estimate needed — it ran.

Script: `C:\Users\o_iseri\AppData\Local\Temp\claude\...\e7c961eb.../scratchpad\n05_stage2_subset_vs_fullcell.py`
(session scratchpad only, not under `docs/` or `openubem/`).

## 2. The 3×3 table (deliverable)

All three columns re-derived from a named file. `levels`/`height_m` in the first two rows are the
**raw upstream OSM columns**, unchanged after `classify()` (see §4 — the classifier's own
byte-equality invariant, `building_classifier.py:636-639`, forbids it from touching them). The third
row's `levels`/`height_m` are **not** the raw OSM columns either (§4 explains what they are).

| `osm_id` | source | `levels` | `height_m` | `archetype_id` |
|---|---|---:|---:|---|
| `way/42496314` | RUN A — 3-building, HEAD | 51 | NaN | **SuperTallBuilding** |
| `way/42496314` | RUN B — full cell (738), HEAD | 51 | NaN | **SuperTallBuilding** |
| `way/42496314` | adopted `05_results.gpkg` (commit `0df422e`) | 51.0 | 178.5 | **SuperTallBuilding** |
| `way/42496352` | RUN A — 3-building, HEAD | NA | NaN | **SuperTallBuilding** |
| `way/42496352` | RUN B — full cell (738), HEAD | NA | NaN | **LargeOffice** |
| `way/42496352` | adopted `05_results.gpkg` (commit `0df422e`) | 1.0 | 3.5 | **LargeOffice** |
| `way/42500728` | RUN A — 3-building, HEAD | NA | NaN | **SuperTallBuilding** |
| `way/42500728` | RUN B — full cell (738), HEAD | NA | NaN | **LargeOffice** |
| `way/42500728` | adopted `05_results.gpkg` (commit `0df422e`) | 1.0 | 3.5 | **LargeOffice** |

CSV: `openubem/outputs/comparisons/open34_subset_vs_fullcell.csv` (9 rows, includes the internal
imputation columns from §4).

**Full-cell run B reproduces the adopted archetype exactly for all three buildings.** Run A (the
3-building subset, same shape as E01c) reproduces E01c's divergence exactly: `SuperTallBuilding` for
both `way/42496352` and `way/42500728`.

## 3. Control: `way/42496314`

Agrees in **both** runs and in the adopted fixture: `SuperTallBuilding`, raw `levels=51` (`OSM_OBSERVED`
provenance token both times), `archetype_source=RULE_HIGHRISE`, `archetype_confidence=HIGH`. Harness
validated — **not a STOP condition.**

## 4. Why: two disjoint imputation pathways, only one of which is subset-dependent

Chasing "what filled `levels`/`height_m`, from what" surfaced that the pipeline runs **two
independent imputations of the same nominal quantity**, and only one of the two ever touches
`archetype_id`:

**(a) The archetype-decision path — subset-dependent.**
`BuildingClassifier._impute_levels()` (`openubem/semantic/building_classifier.py:123-142`), called
inside `classify()` via `self._build_levels_median_lookup(out)`
(`building_classifier.py:609-612, 664-683`). Fallback order: raw `levels` (`OSM_OBSERVED`) → raw
`height_m` (`HEURISTIC_HEIGHT`) → **median of `levels` over rows in the** ***same `classify()` call***
**that have observed (non-null) `levels`, stratified by `use_class`** (`GROUPMEDIAN_LEVELS_MED`) →
flat default 1 (`LEVELS_DEFAULT_LOW`). Called directly (not reimplemented) for provenance:

- RUN A (n=3): `levels_group_median = {'commercial': 51}`, `levels_global_median = 51` — because the
  **only** observed-`levels` row in the 3-building group is `way/42496314` itself (raw `levels=51`).
  Both target buildings get `levels_imputed=51` → `>= super_tall_levels_threshold` (40,
  `building_classifier.py:174,191`) → `RULE_HIGHRISE` → `SuperTallBuilding`.
- RUN B (n=738): `levels_group_median = {'commercial': 19, 'institutional': 4, 'residential': 4,
  'unknown': 5}`, `levels_global_median = 6` — computed over 738 real buildings. Both target
  buildings get `levels_imputed=19` (< 20, `high_rise_levels_threshold`) → falls to the office
  size-tier rule → `RULE_USE_CLASS_SIZE` → `LargeOffice` (footprint 2814/1632 m² × 19 floors clears
  the `LargeOffice` size cut, `building_classifier.py:145-161`).
- **This imputed value (51 or 19) is never persisted.** `classify()`'s own byte-equality invariant
  (`building_classifier.py:636-639`, `pd.testing.assert_frame_equal(input_gdf..., out[input_gdf.columns]...)`)
  guarantees the raw `levels`/`height_m` columns come out of `classify()` exactly as they went in
  (`NA`/`NaN` for both target buildings, in both runs — see §2 table). `archetype_source` records
  which token fired but not the numeric value it used.

**(b) The geometry/IDF-construction path — NOT subset-dependent, and it is what ends up in
`05_results.gpkg`.** `derive_num_floors()` (`openubem/geometry/footprint.py:58-63`) has only **three**
tiers — raw `levels` → raw `height_m`/3.5 → **flat default 1, no group median, no cross-building
term at all**. This is what `openubem/idf/builder.py:420` uses to build each building's IDF zones,
and `scripts/validation/v12_cell_pipeline.py:659-717` (the script that built this adopted
`nyc_centre/05_results.gpkg`) harvests `levels`/`height_m` back **from the built IDF's own SQL zone
geometry** (`Zones` table, `CeilingHeight`) — not from `derive_num_floors()`'s return value directly,
but downstream of it. For both target buildings (raw `levels`/`height_m` both NaN), `derive_num_floors`
returns the flat default `1`, so the IDF is built as a single floor, single 3.5 m zone, and the
harvest reads that back as `levels=1.0, height_m=3.5` — matching §2's adopted-fixture row exactly,
and matching regardless of subset size, because nothing in `derive_num_floors` reads any other row.

**The finding volunteered by this task, not asked for by name:** the pipeline has no persisted record
of the group-median value that actually decided the archetype (51 vs 19 above) — the only trace is the
`archetype_source` token, which names the *mechanism* (`GROUPMEDIAN_LEVELS_MED`) but not the *value*.
This is the same shape as OPEN-30 (a resolved value the pipeline never persists) and is reported here,
not filed as an item.

## 5. Mechanism verdict

**Subset-dependence.** The full-cell HEAD run (RUN B) reproduces the adopted fixture's archetype
exactly for all three buildings, using the same classifier at the same commit as the 3-building run
that disagreed. The only variable between RUN A and RUN B is the row population passed into one
`classify()` call, which changes `BuildingClassifier`'s internal `GROUPMEDIAN_LEVELS_MED` fallback
(§4a) — nothing in the classifier's code differs between the two runs. This is not "both remain
possible": HEAD-divergence is ruled out by RUN B's exact match to the adopted archetype.

**Consequence for the arc's own method (§ per N05's "why"):** a 3-building (or any small-n) local
subset is **not** archetype-faithful for buildings whose `levels`/`height_m` are missing and whose
neighbours-in-scope happen to include a real outlier — because the group-median fallback pools over
whatever is in scope, not over the fleet. E01, E01b, E01c and the timing benchmark all used exactly
this shape of subset. This does not retroactively invalidate what those runs measured (mode
correctness, IDF structure, timing) — only archetype fidelity, which none of them were checking for.

**Relation to OPEN-08/E-LA-22.** Different mechanism, per the register's own caution (§692) not to
merge until measured. OPEN-08 is a **cross-generation** (old harvest vs current HEAD) divergence for
data-poor buildings, driven by a semantic-imputation commit landing after a past fleet run. OPEN-34's
mechanism is **same-commit, same-code**, driven purely by which rows are in scope for one
`classify()` call. They can co-occur on the same building (both are triggered by missing
`levels`/`height_m`) but they are not the same defect.

## 6. Full-cell `SuperTallBuilding` count (fleet-scale check, §6/N05 "how to test" (c))

RUN B (full cell, HEAD): **20 / 738** buildings classified `SuperTallBuilding`
(`openubem/semantic/building_classifier.py` `archetype_id` value_counts on the full-cell output).
Adopted fixture: **20 / 738** (`05_results.gpkg`, re-counted directly:
`(gdf['archetype_id']=='SuperTallBuilding').sum()`). **Exact match — no fleet-scale divergence.**

## 7. Artifacts

- Driver script (scratchpad only): `n05_stage2_subset_vs_fullcell.py`, run log `n05_work/run.log`.
- CSV: `openubem/outputs/comparisons/open34_subset_vs_fullcell.csv` (9 rows).
- This report.
