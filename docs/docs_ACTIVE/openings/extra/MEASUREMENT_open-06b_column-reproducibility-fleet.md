# MEASUREMENT — Does the column-reproducibility result hold on the other eight cells? (OPEN-06 / N16)

> **Task:** N16, `docs/docs_ACTIVE/openings/implemenation/PLAN_no-compute-queue-4.md` §6.
> **Scope:** Stage 2 only (semantic enrichment + classification), the plan's single authorised
> compute exception. No Step 3/IDF/EnergyPlus/cluster was run. Measurement only — no remediation.

## 0. The prediction, stated before the results (plan §5.2, verbatim)

> "across the eight cells of §4, `archetype_id` must DIFFER on exactly 2 rows in `austin_centre`,
> 4 in `la_centre`, 5 in `la_urban`, and 0 in each of `nyc_urban`, `la_suburban`, `la_rural`,
> `austin_urban`, `austin_suburban`."

**Outcome, per cell, stated before any other result in this report:**

| cell | predicted `archetype_id` differ-count | measured | verdict |
|---|---|---|---|
| `austin_centre` | 2 | 2 | **HELD** |
| `la_centre` | 4 | 4 | **HELD** |
| `la_urban` | 5 | 5 | **HELD** |
| `nyc_urban` | 0 | 0 | **HELD** |
| `la_suburban` | 0 | 0 | **HELD** |
| `la_rural` | 0 | 0 | **HELD** |
| `austin_urban` | 0 | 0 | **HELD** |
| `austin_suburban` | 0 | 0 | **HELD** |

**Overall verdict: HELD in all eight cells.** Not merely count-for-count: the 11 differing rows'
`osm_id`s and both their values (Stage-2-recomputed and committed) were cross-checked one-for-one
against N04's `open06_mislabel_population.csv` (§3) and match **exactly**, with zero extra rows and
zero missing rows. Combined with N14's four cells, the prediction now holds on **all twelve** fleet
cells and the mislabel population (41 rows) is fully accounted for on the whole fleet by the
reproducibility gap. This attempt at falsification did not succeed — reported as the outcome, not
assumed going in.

A second, unpredicted finding surfaced while executing the required `data_quality_flag` partition
(§4): one building (`la_urban/way/1176846930`) carries a genuine Stage-2 provenance divergence
**despite its `archetype_id` reproducing exactly**, i.e. a row entirely outside the 41-row mislabel
population. This does not contradict the §5.2 prediction (which is scoped to `archetype_id` only) but
it does mean the *set* of `data_quality_flag` provenance-divergent rows is **not** always a subset of
the `archetype_id`-differing rows — see §4.3.

## 1. Method

Drove the real `t08_full_sweep.run_step2(gdf_raw, cell, cfg, work_base)`
(`scripts/cluster/t08_full_sweep.py:106-149`) — the identical function N05/N14 used, imported from
its real file, never reimplemented — over the eight **whole** cells named in the plan's §4 (never a
subset; OPEN-34 established a subset is not archetype-faithful): `nyc_urban`, `la_centre`, `la_urban`,
`la_suburban`, `la_rural`, `austin_centre`, `austin_urban`, `austin_suburban`. All eight cells' input
files (`01_buildings.gpkg`, `05_results.gpkg`) were present and readable — **no cell was missing or
substituted.**

For each cell: loaded frozen `01_buildings.gpkg` (Stage-1 input), ran Stage 2 to get `gdf_57`, loaded
the committed `05_results.gpkg`, merged on `osm_id`, and classified every one of the committed file's
33 columns (32 per `05_results.schema.json` + `geometry`) into exactly one of the four required
buckets: REPRODUCES / DIFFERS / STAGE-3-OR-LATER / ABSENT. Equality predicate identical to N14's:
float columns compared with `1e-9` tolerance (both-NaN counts as match), string/categorical compared
exactly.

**Cell sizes (Stage-1 raw = committed = Stage-2 out = merged, all four counts equal in every cell —
no row was dropped or duplicated by the join):**

| cell | n buildings |
|---|---|
| `nyc_urban` | 1,779 |
| `la_centre` | 226 |
| `la_urban` | 618 |
| `la_suburban` | 1,343 |
| `la_rural` | 149 |
| `austin_centre` | 413 |
| `austin_urban` | 425 |
| `austin_suburban` | 437 |

Total wall time for all eight Stage-2 runs (incl. EPW station resolution, cached): well under two
minutes.

**Git state of every file read** (`git log -1 --format=%H --date=short`), identical across all eight
cells:
- `01_buildings.gpkg`: `e063865` (2026-06-30), unchanged since.
- `05_results.gpkg`: `0df422e` (2026-07-03), unchanged since.
- `openubem/semantic/building_classifier.py` at HEAD `bca92d0` (2026-08-05): unchanged since
  `0df422e` (re-verified directly this session by `git log -1`, not carried from N04/N07/N14).
- `openubem/geometry/footprint.py` at HEAD: read directly this session (not previously cited in the
  N14 report) — current at `derive_num_floors():58-63` and `simplify_footprint():24-43`.
- `openubem/idf/builder.py` at HEAD: `_coerce_to_polygon():131-149`, the `layout_assign_fallback_auto`
  / `storey_match_fallback_*` branches (:435-474), and the `narrow_perimeter_fallback` branch
  (:605-620) all read directly this session.

## 2. Bucket counts vs. total column count — printed both, per cell (how-to-test (a))

| cell | REPRODUCES | DIFFERS | STAGE-3-OR-LATER | ABSENT | sum | committed columns |
|---|---|---|---|---|---|---|
| `nyc_urban` | 3 | 1 | 29 | 0 | 33 | 33 |
| `la_centre` | 2 | 2 | 29 | 0 | 33 | 33 |
| `la_urban` | 2 | 2 | 29 | 0 | 33 | 33 |
| `la_suburban` | 3 | 1 | 29 | 0 | 33 | 33 |
| `la_rural` | 3 | 1 | 29 | 0 | 33 | 33 |
| `austin_centre` | 2 | 2 | 29 | 0 | 33 | 33 |
| `austin_urban` | 3 | 1 | 29 | 0 | 33 | 33 |
| `austin_suburban` | 3 | 1 | 29 | 0 | 33 | 33 |

Every cell's four bucket counts sum to 33, matching the committed file's own column count in every
case. Aggregated over all 264 (cell × column) checks: **REPRODUCES 21, DIFFERS 11, STAGE-3-OR-LATER
232, ABSENT 0.**

**Bucket assignment (identical mechanism across all eight cells):**
- **REPRODUCES:** `osm_id` (identity passthrough), `geometry` (Stage-1 raw geometry, unchanged
  through `classify()`); `archetype_id` in the five cells where it does not carry a known mislabel
  (`nyc_urban`, `la_suburban`, `la_rural`, `austin_urban`, `austin_suburban`).
- **DIFFERS:** `archetype_id` in `austin_centre`/`la_centre`/`la_urban` only; `data_quality_flag` in
  **all eight** cells (§4 — every cell has at least one Stage-3-appended token, so `data_quality_flag`
  never fully reproduces anywhere in this fleet, independent of the archetype mislabel).
- **STAGE-3-OR-LATER (29 columns, all eight cells):** `zoning_strategy` (Stage 3,
  `openubem/idf/builder.py`); the 10 `*_eui_kwh_m2` + 9 `gwp_*_kgco2_m2` + `iod` +
  `simulation_status` + `error_summary` (24 columns, Stage 4/5, not present in `gdf_57` at all); and,
  per N14's finding, `levels`, `height_m`, `footprint_area_m2` — the geometry-stage-derived values
  established by N14 §5.5, re-confirmed here by the same predicate on all eight cells (spot-checked;
  not the subject of this task's headline claims, carried from N14 per the plan's §5.5 without
  re-deriving numbers since that would require running Stage 3, not authorised).
- **ABSENT:** none, in any of the eight cells.

**No column landed in DIFFERS in these eight cells that did not also land in DIFFERS in N14's four.**
Only `archetype_id` and `data_quality_flag` DIFFER anywhere in this fleet, on both halves of the
twelve-cell fleet, by the identical mechanism. This was checked explicitly by filtering the bucket
CSV for `bucket == DIFFERS AND column NOT IN (archetype_id, data_quality_flag)`: **zero rows.**

Artifact: `openubem/outputs/comparisons/open06b_column_reproducibility_fleet.csv` (264 rows, one per
cell × column).

## 3. The `archetype_id` control — two-sided, stated pass/fail (how-to-test (b))

**PASS, in both directions, on all eight cells.**

`archetype_id` DIFFERS in exactly `austin_centre` (2/413), `la_centre` (4/226), `la_urban` (5/618) —
and REPRODUCES (0 differences) in exactly the other five: `nyc_urban` (0/1,779), `la_suburban`
(0/1,343), `la_rural` (0/149), `austin_urban` (0/425), `austin_suburban` (0/437). No cell failed the
control in either direction.

**All 11 differing rows, both values, cross-checked one-for-one against N04's
`open06_mislabel_population.csv` (re-read fresh this session, not carried):**

| cell | osm_id | Stage-2 (HEAD) value | committed `05_results.gpkg` value | matches N04 row? |
|---|---|---|---|---|
| `austin_centre` | `way/231123149` | `LargeHotel` | `LargeOffice` | yes, exact |
| `austin_centre` | `way/328723692` | `LargeHotel` | `LargeOffice` | yes, exact |
| `la_centre` | `relation/6366079` | `LargeHotel` | `MediumOffice` | yes, exact |
| `la_centre` | `way/427817498` | `LargeHotel` | `LargeOffice` | yes, exact |
| `la_centre` | `way/427942886` | `SmallHotel` | `MediumOffice` | yes, exact |
| `la_centre` | `way/428015098` | `LargeHotel` | `MediumOffice` | yes, exact |
| `la_urban` | `relation/6374725` | `SmallHotel` | `SmallOffice` | yes, exact |
| `la_urban` | `way/401904732` | `LargeHotel` | `LargeOffice` | yes, exact |
| `la_urban` | `way/401910463` | `SmallHotel` | `SmallOffice` | yes, exact (OPEN-07 building) |
| `la_urban` | `way/427274663` | `LargeHotel` | `MediumOffice` | yes, exact |
| `la_urban` | `way/428846131` | `SmallHotel` | `SmallOffice` | yes, exact |

All 11 rows match N04's population **exactly** — same `osm_id`, same committed value
(`gpkg_05_results_archetype_id`), same Stage-2-recomputed value (`classifier_archetype_id_HEAD`). Not
one extra row, not one missing row, not one value mismatch. This is a stronger check than a count
match: it is a set-for-set, value-for-value re-derivation. **HELD.**

## 4. `data_quality_flag` — partitioned per §5.3, checked, not asserted

### 4.1 The Stage-3-or-later token vocabulary — extended beyond N14's one known token

N14 named one Stage-3 token, `narrow_perimeter_fallback` (`openubem/idf/builder.py:614-615`,
pipe-appended). Running the sweep on these eight cells surfaced **`data_quality_flag` diffs whose
extra content was not that token** — tracing them found three more Stage-3-or-later appenders, named
here with `path:line` as the plan requires:

| token | appended at | separator | stage |
|---|---|---|---|
| `narrow_perimeter_fallback` | `openubem/idf/builder.py:614-615` | `\|` | 3 (already known, N14) |
| `multipolygon_coerced_to_largest_part` | `openubem/idf/builder.py:145-146` | `\|` | 3 (new, this task) |
| `layout_assign_fallback_auto` | `openubem/idf/builder.py:439-440` | `\|` | 3 (new, this task) |
| `storey_match_fallback_shorter` / `storey_match_fallback_not_expressible` | `openubem/idf/builder.py:472-474` | `\|` | 3 (new, this task) |
| `idf_dp_coarse` | `openubem/geometry/footprint.py:33` (`simplify_footprint()`, called from `builder.py:407`) | `,` | 3 (new, this task) |
| `idf_hull_simplification` | `openubem/geometry/footprint.py:38` | `,` | 3 (new, this task) |
| `idf_bbox_simplification` | `openubem/geometry/footprint.py:42` | `,` | 3 (new, this task, not observed in this fleet's diffs but same mechanism) |
| `RESULTS_CSV_FALLBACK` | `openubem/results/parser.py:548` | `,` | 5 (new, this task) |
| `IOD_NO_OCCUPIED_HOURS` | `openubem/results/parser.py:367,396,410` | `,` | 5 (new, this task, not observed) |

**This matters mechanically, not just for bookkeeping**: the Stage-3 appenders use *two different,
mutually-inconsistent separator conventions* — `builder.py`'s own tags are pipe-appended
(`dq_flag + "|" + tag`), while `footprint.py`'s `_append_flag()` and `parser.py`'s `_append_flag()`
are comma-appended (`dq_flag + "," + token`). A naive suffix-string match on
`"|narrow_perimeter_fallback"` alone (as would be the direct extension of N14's method) **misclassified
two rows** in this run (`la_centre/relation/6410855`, `austin_urban/relation/5682409`) as genuine
provenance divergence when they were in fact only carrying the comma-appended `idf_dp_coarse` /
`idf_hull_simplification` tokens. The partition below uses a tokenizer that splits on both `|` and `,`
and strips the full known-token set above before comparing, which corrects this.

### 4.2 Per-cell (a)/(b) counts

| cell | n differ (dqf) | (a) STAGE-3-TOKEN | (b) PROVENANCE-DIVERGENCE | (a)+(b) check |
|---|---|---|---|---|
| `nyc_urban` | 15 | 15 | 0 | 15 ✓ |
| `la_centre` | 44 | 44 | 0 | 44 ✓ |
| `la_urban` | 36 | 35 | 1 | 36 ✓ |
| `la_suburban` | 10 | 10 | 0 | 10 ✓ |
| `la_rural` | 6 | 6 | 0 | 6 ✓ |
| `austin_centre` | 12 | 10 | 2 | 12 ✓ |
| `austin_urban` | 40 | 40 | 0 | 40 ✓ |
| `austin_suburban` | 8 | 8 | 0 | 8 ✓ |

Every cell's (a)+(b) sums to its own `data_quality_flag` differ-count (171 rows total across the
fleet slice). No row was double-counted or dropped. Every class-(b) row's "extra" content (the tokens
that remain after stripping the known Stage-3/5 vocabulary) was itself checked against the known
Stage-2 provenance vocabulary (`HOTDECK_NEIGHBOR_HIGH`/`_MED`, `GROUPMODE_MED` —
`openubem/semantic/imputation.py:561-563`; `VINTAGE_NAN_PERMISSIVE_DEFAULT` —
`openubem/semantic/construction_sets.py:46`) and in all three class-(b) rows the residual is exactly
one of these tokens on each side — **no unrecognised/unclassifiable token appeared anywhere in this
run.**

**All three class-(b) (PROVENANCE-DIVERGENCE) rows, in full:**

| cell | osm_id | Stage-2 (HEAD) value | committed value |
|---|---|---|---|
| `austin_centre` | `way/231123149` | `no_floors,no_height,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT` | `no_floors,no_height,no_year\|GROUPMODE_MED` |
| `austin_centre` | `way/328723692` | `no_floors,no_height,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT` | `no_floors,no_height,no_year\|GROUPMODE_MED` |
| `la_urban` | `way/1176846930` | `generic_tag,no_floors,no_function,no_height,no_year\|GROUPMODE_MED` | `generic_tag,no_floors,no_function,no_height,no_year\|HOTDECK_NEIGHBOR_HIGH` |

**Representative class-(a) (STAGE-3-TOKEN) rows, ≥3 named** (full 171-row set in the artifact CSV):

| cell | osm_id | Stage-2 (HEAD) value | committed value |
|---|---|---|---|
| `nyc_urban` | `way/241836468` | `generic_tag,no_floors,no_function,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT` | `generic_tag,no_floors,no_function,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT\|narrow_perimeter_fallback` |
| `la_centre` | `relation/6410855` | `no_height,no_year\|GROUPMODE_MED` | `no_height,no_year\|GROUPMODE_MED,idf_dp_coarse` |
| `austin_urban` | `relation/5682409` | `generic_tag,no_floors,no_function,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT` | `generic_tag,no_floors,no_function,no_year\|VINTAGE_NAN_PERMISSIVE_DEFAULT,idf_hull_simplification` |
| `la_urban` | `way/376149058` | `no_floors` | `no_floors\|narrow_perimeter_fallback` |
| `la_urban` | `way/388772955` | `NaN` (no defect tags) | `narrow_perimeter_fallback` |

### 4.3 The set relationship to `archetype_id`'s differing rows — checked, not an impression

Per plan §5.3, the set relationship was checked by `osm_id`, not inferred from counts:

| cell | `archetype_id` differing `osm_id`s | class-(b) `osm_id`s | relationship |
|---|---|---|---|
| `nyc_urban` | {} | {} | EQUAL (both empty) |
| `la_centre` | {`relation/6366079`, `way/427817498`, `way/427942886`, `way/428015098`} | {} | class-(b) is a (trivial, empty) SUBSET |
| `la_urban` | {`relation/6374725`, `way/401904732`, `way/401910463`, `way/427274663`, `way/428846131`} | {`way/1176846930`} | **DISJOINT — not a subset, not a superset, no overlap** |
| `la_suburban` | {} | {} | EQUAL (both empty) |
| `la_rural` | {} | {} | EQUAL (both empty) |
| `austin_centre` | {`way/231123149`, `way/328723692`} | {`way/231123149`, `way/328723692`} | **EQUAL — same two buildings, exactly** |
| `austin_urban` | {} | {} | EQUAL (both empty) |
| `austin_suburban` | {} | {} | EQUAL (both empty) |

**Result: the relationship is not uniform across the fleet.** In `austin_centre` the two error
populations coincide exactly. In five cells both are empty. In `la_urban`, class-(b) is **disjoint**
from the archetype-mislabel population: `way/1176846930` reproduces its `archetype_id` perfectly but
still carries a genuine Stage-2 imputation-provenance divergence (`GROUPMODE_MED` at HEAD vs.
`HOTDECK_NEIGHBOR_HIGH` committed) — a defect entirely independent of, and not explained by, the
Hotel→Office mislabel mechanism. This directly falsifies the (already-struck, per N14's own §5.3
correction) idea that the two columns' error populations are simply "the same rows" — even under the
corrected partition, they are not the same population in every cell.

## 5. What was NOT checked here

- The 24 EUI/GWP/`iod`/`simulation_status`/`error_summary` columns remain Stage 4/5, absent from
  `gdf_57` entirely, and **not checkable without compute**, which this task does not authorise beyond
  Stage 2 — identical to N14's finding, re-confirmed on these eight cells' bucket counts.
- `levels`, `height_m`, `footprint_area_m2`'s STAGE-3-OR-LATER classification is carried from N14's
  established mechanism (§5.5 of the plan; byte-equality invariant at
  `building_classifier.py:636-639`) and re-confirmed by the same bucket mechanism on these eight
  cells; the specific differ-counts for these three columns were not re-tabulated in this report
  since the plan's headline questions concern `archetype_id`/`data_quality_flag` — the raw counts are
  in `open06b_column_reproducibility_fleet.csv` for any reader who wants them.
- `idf_bbox_simplification` and `RESULTS_CSV_FALLBACK`/`IOD_NO_OCCUPIED_HOURS` are named in §4.1's
  vocabulary table by direct code trace but were **not observed** in any of these eight cells' actual
  diffs — named for completeness of the token vocabulary, not because they fired here.
- No cell's input files were missing; there is no "cell skipped" result to report in this run.
- This task does not extend to the remaining register items under OPEN-06 that require compute
  (Stage 3+) — those remain out of scope per the plan's hard rules.

## 6. Artifacts

- `openubem/outputs/comparisons/open06b_column_reproducibility_fleet.csv` — 264 rows (8 cells × 33
  columns), bucket + match/differ counts per (cell, column).
- `openubem/outputs/comparisons/open06b_column_reproducibility_fleet_diff_examples.csv` — 182 rows,
  every DIFFERS row for `archetype_id` (11 rows) and `data_quality_flag` (171 rows) across all eight
  cells, both values shown.
- `openubem/outputs/comparisons/open06b_dqf_partition.csv` — 171 rows, one per `data_quality_flag`
  differing row, with its (a)/(b) classification and the full token-stripped comparison that produced
  it.
