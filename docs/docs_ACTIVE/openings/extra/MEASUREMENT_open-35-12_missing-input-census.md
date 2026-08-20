# MEASUREMENT — the missing-input census (OPEN-35 · OPEN-12)

> **Slug:** `open-35-12_missing-input-census` · **Date:** 2026-08-06 · **Task:** N06 of
> `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_no-compute-queue-2.md`.
> **MEASUREMENT ONLY. No remediation was performed or proposed.** No EnergyPlus, no IDF generation, no
> fleet pass, no cluster. Every number below is read directly from `01_buildings.gpkg` /
> `05_results.gpkg` already on disk, with `pandas`/`geopandas`, no classifier execution.

---

## 0. Provenance ledger — every file read, and its git state

| File (×12 cells) | Role | Git state |
|---|---|---|
| `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` | Stage-1 raw input — source of the census | `git log -1 --format=%H -- <path>` returns **`e063865c92aa47718ab3b2876a36cd178e3f2803`** for all 12 cells, identically. `git status --porcelain` on each path is empty — working tree = that commit, byte-identical. |
| `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg` | Joined for the "neither" population's persisted `archetype_id`/`levels`/`height_m` | `git log -1 --format=%H -- <path>` returns **`0df422e5c279b840d6dccb066935a0861cc695aa`** for all 12 cells, identically — the same commit N04/N05 already fixed as the current canonical state. |
| `openubem/semantic/building_classifier.py:131-142` (`_impute_levels`) | Defines the archetype-selection-stage missing predicate applied here | Read at HEAD (`bca92d0`). Confirms §5.1 verbatim: `pd.notna(row["levels"])` first; else `pd.notna(h) and h > 0`; else group/global median; else `1` (`LEVELS_DEFAULT_LOW`). |
| `openubem/geometry/footprint.py:58-63` (`derive_num_floors`) | Geometry-stage fallback, for comparison only | Read at HEAD. **Note beyond §5.1's summary:** its height branch tests only `pd.notna(row["height_m"])`, not `> 0` — a narrower null-check than `_impute_levels`'s. Not used in this census's predicate (the plan pins `_impute_levels`'s predicate as the one to apply), but recorded because it is a second, slightly different predicate living one stage downstream. |

Both source commits (`e063865` for inputs, `0df422e` for results) are constant across all twelve cells — no cell was read from a different snapshot than its siblings.

---

## 1. The predicate applied, exactly as pinned

Per `_impute_levels` (`building_classifier.py:131-134`):
- `levels` **usable** iff `pd.notna(levels)`; else **missing (null)**. (Column is present under this exact name in all 12 `01_buildings.gpkg`; no substitution needed.)
- `height_m` **usable** iff `pd.notna(height_m) and height_m > 0`; else split into **missing (null)** and **missing (zero-or-negative, not null)** — these are reported as separate states, not collapsed (plan rule 9).
- **"Neither"** = `levels` missing **and** `height_m` missing-for-purpose (either sub-state) — the population that reaches both the archetype-selection fallback (`GROUPMEDIAN_LEVELS_MED` / `LEVELS_DEFAULT_LOW`) and, downstream, the geometry fallback.

Both columns are present by name in every one of the 12 `01_buildings.gpkg` files — no absent-column case arose.

---

## 2. Per-cell and fleet-wide census

Full table: `openubem/outputs/comparisons/open35_missing_input_census.csv` (13 rows: 12 cells + `FLEET_TOTAL`).

| cell | n | levels usable | levels missing(null) | height usable | height missing(null) | height missing(zero) | height missing(total) | % no height_m | n "neither" | % "neither" |
|---|---|---|---|---|---|---|---|---|---|---|
| austin_centre | 413 | 118 | 295 | 64 | 349 | 0 | 349 | 84.50 | 247 | 59.81 |
| austin_rural | 245 | 1 | 244 | 0 | 245 | 0 | 245 | 100.00 | 244 | 99.59 |
| austin_suburban | 437 | 46 | 391 | 323 | 114 | 0 | 114 | 26.09 | 74 | 16.93 |
| austin_urban | 425 | 4 | 421 | 378 | 47 | 0 | 47 | 11.06 | 43 | 10.12 |
| la_centre | 226 | 79 | 147 | 181 | 45 | 0 | 45 | 19.91 | 31 | 13.72 |
| la_rural | 149 | 3 | 146 | 148 | 1 | 0 | 1 | 0.67 | 0 | 0.00 |
| la_suburban | 1343 | 6 | 1337 | 1328 | 15 | 0 | 15 | 1.12 | 15 | 1.12 |
| la_urban | 618 | 31 | 587 | 576 | 42 | 0 | 42 | 6.80 | 29 | 4.69 |
| nyc_centre | 738 | 136 | 602 | 617 | 121 | 0 | 121 | 16.40 | 107 | 14.50 |
| nyc_rural | 198 | 0 | 198 | 0 | 198 | 0 | 198 | 100.00 | 198 | 100.00 |
| nyc_suburban | 1589 | 0 | 1589 | 0 | 1589 | 0 | 1589 | 100.00 | 1589 | 100.00 |
| nyc_urban | 1779 | 17 | 1762 | 1739 | 40 | 0 | 40 | 2.25 | 34 | 1.91 |
| **FLEET_TOTAL** | **8160** | **441** | **7719** | **5354** | **2806** | **0** | **2806** | **34.39** | **2611** | **32.00** |

**Notable third state:** `height_missing_zero` (present-but-`0`-or-negative, distinct from null) is **0 across all 12 cells** — every missing `height_m` in this fleet is a genuine null, never a `0`. The three-state distinction (usable / null / zero) was applied as required (plan rule 9) and the zero-state came back empty; that is itself a small, clean finding, not an omission.

**Fleet total row (8,160) matches the pinned fleet building count exactly** — no per-cell/fleet reconciliation gap.

**Denominators, stated explicitly (plan §4):** all percentages above use **8,160** (the Stage-1 input population), because this census is a Stage-1/Stage-2 question about inputs reaching the fallback, not a simulation-outcome question. The fleet's *simulated* count (8,154, six inverted-geometry drops, N04-confirmed) is **not** the right denominator here and was not used.

---

## 3. The "neither" population: archetype and persisted-storey outcome

`n = 2,611` buildings fleet-wide (32.00% of 8,160) have **neither** a usable `levels` nor a usable
`height_m` in the Stage-1 input. Full row set: `openubem/outputs/comparisons/open35_neither_population.csv`
(2,611 rows: `cell`, `osm_id`, raw `building_tag`/`function_tag`, persisted `levels`, persisted
`height_m`, `archetype_id`, `simulation_status`).

**Archetype distribution over the 2,611 (`05_results.gpkg`, `0df422e`):**

| archetype_id | count |
|---|---|
| MidriseApartment | 1,028 |
| SmallOffice | 898 |
| OpenUBEMUnknown | 364 |
| MediumOffice | 119 |
| LargeOffice | 85 |
| RetailStandalone | 33 |
| QuickServiceRestaurant | 28 |
| Courthouse | 23 |
| FullServiceRestaurant | 18 |
| SecondarySchool | 4 |
| HighriseApartment | 3 |
| SuperMarket | 3 |
| Outpatient | 3 |
| Hospital | 1 |
| PrimarySchool | 1 |

**Persisted `levels`/`height_m` in `05_results.gpkg` for all 2,611: uniformly `1.0` / `3.5`.** §5.1
predicted the persisted value is `1` — **checked, not assumed: confirmed for all 2,611 rows, no
exceptions.** `3.5` is exactly `floor_to_floor_m`, i.e. `1 level × 3.5 m/level`.

**Important clarification beyond §5.1's framing:** `05_results.gpkg`'s `levels`/`height_m` columns are
**not** the untouched raw Stage-1 columns (those stay byte-identical through `classify()`, per the
`building_classifier.py:636-639` invariant N05 established) — they are the **geometry-stage
(`derive_num_floors`) derived values**, written later in the pipeline. For this "neither" population
both stages agree (`_impute_levels`'s `LEVELS_DEFAULT_LOW` = 1 and `derive_num_floors`'s flat `1`
fallback coincide), so the two-fallback disagreement described in §5.1 **leaves no visible trace for
this specific population** — consistent with §5.1's own statement that the disagreement "leaves no
trace in any output." This measurement cannot distinguish, from `05_results.gpkg` alone, whether a
given row's persisted `1` came from `_impute_levels`'s `LEVELS_DEFAULT_LOW` token or from
`derive_num_floors`'s independent flat fallback — both stages are read from the same input row, and only
the input, not the imputation token, survives to this file.

---

## 4. OPEN-12 re-derived, all twelve cells

Register (§0's own rule: never carry a 📄 number into a plan without re-deriving it): `nyc_rural`
**36.4%**, `austin_rural` **19.2%**, both marked 📄, dated to the UTCI arc's close.

**Re-derived from `01_buildings.gpkg` (commit `e063865`) using the identical predicate (`height_m`
missing = not(`notna` and `>0`)):**

| cell | register (📄) | re-derived (this task) | n | agree? |
|---|---|---|---|---|
| nyc_rural | 36.4% | **100.00%** (198/198) | 198 | **No — large disagreement** |
| austin_rural | 19.2% | **100.00%** (245/245) | 245 | **No — large disagreement** |

**Both numbers reported, not adjudicated (plan rule 13).** Every one of the 198 `nyc_rural` rows and
all 245 `austin_rural` rows has a null `height_m` in the `01_buildings.gpkg` read today — there is no
partial-coverage subset in the file that would produce 36.4%/19.2%. Two candidate explanations exist,
**neither confirmed here** because settling between them was out of this task's scope (it belongs to
N09, whose subject is exactly the UTCI backfill's reproducibility — OPEN-14):
1. The register's percentages describe a **post-UTCI-backfill** state, and that backfill's output was
   never merged back into the `01_buildings.gpkg` these two cells ship today — i.e. the backfilled
   heights exist (existed) somewhere else, or no longer exist on this checkout.
2. The register's percentages are stale relative to a **different snapshot** of `01_buildings.gpkg`
   than commit `e063865`.
**This task does not choose between them.** It is flagged here because it is directly relevant to N09
(OPEN-13/OPEN-14) and to CP-N4, and because the plan requires reporting disagreement rather than
silently reconciling it.

**All twelve cells' no-`height_m` percentage** (same query, "while you are there"):

| cell | % no height_m |
|---|---|
| austin_centre | 84.50 |
| austin_rural | 100.00 |
| austin_suburban | 26.09 |
| austin_urban | 11.06 |
| la_centre | 19.91 |
| la_rural | 0.67 |
| la_suburban | 1.12 |
| la_urban | 6.80 |
| nyc_centre | 16.40 |
| nyc_rural | 100.00 |
| nyc_suburban | 100.00 |
| nyc_urban | 2.25 |
| **FLEET** | **34.39** |

**Notable, not asked for but visible in the same table:** `nyc_suburban` is also at 100% no-`height_m`
(and 100% "neither") — a third cell at the ceiling, not previously named in OPEN-12's two-cell framing.
Reported as an observation; not adjudicated as to whether OPEN-12's scope should widen.

---

## 5. OPEN-18 overlap — observation only, not merged (plan rule §5.8)

OPEN-18 (the √S vertical-form-distortion problem) concerns the same general class of mismatch — an
archetype's expected height/storey count versus the geometry actually built. The "neither" population
found here (2,611 buildings, all forced to a flat 1-storey / 3.5 m geometry regardless of their true
archetype, including `MidriseApartment` and `LargeOffice` rows) is a population where that mismatch is
structurally guaranteed for every affected row. **This is recorded as an overlap for the manager's
attention only. This task does not claim OPEN-35 causes OPEN-18, and does not merge the two items.**

---

## 6. How-to-test results

**(a) Three per-column states sum to the cell's row count, printed per cell.**
Verified programmatically for all 12 cells: `levels_usable + levels_missing_null == n` and
`height_usable + height_missing_null + height_missing_zero == n` (asserted in the census script; no
assertion failure raised for any cell). **PASS.**

**(b) Twelve per-cell "neither" counts sum to the reported fleet figure.**
`247+244+74+43+31+0+15+29+107+198+1589+34 = 2,611`, matching the reported `FLEET_TOTAL` row exactly.
**PASS.**

**(c) Spot-check 3 buildings by hand from the "neither" population — audit trail:**

| cell | osm_id | raw `levels` | raw `height_m` | raw `building_tag`/`function_tag` | persisted `archetype_id` | persisted `levels` (05_results) |
|---|---|---|---|---|---|---|
| nyc_centre | `way/42496352` | NaN | NaN | `office` / (blank) | `LargeOffice` | 1.0 |
| la_suburban | `way/285843826` | NaN | NaN | `yes` / `library` | `Courthouse` | 1.0 |
| nyc_urban | `way/220649876` | NaN | NaN | `yes` / `toilets` | `SmallOffice` | 1.0 |

All three: both raw columns null, both confirmed in the population, both persisted at `1`/`3.5` in
`05_results.gpkg`. **PASS.**

**(d) `way/42496352` and `way/42500728` (OPEN-35's worked examples, `nyc_centre`) in the "neither"
population?**
Checked directly: `way/42496352` → **True**. `way/42500728` → **True**. Both raw rows are
`levels=NaN, height_m=NaN`; both are labelled `LargeOffice`, persisted `levels=1.0, height_m=3.5` in
`05_results.gpkg`. **Both appear, as required. Predicate confirmed correct — no STOP triggered.**

---

## 7. Summary table

| Question | Answer | Evidence |
|---|---|---|
| Fleet buildings reaching **both** fallbacks ("neither") | **2,611 / 8,160 = 32.00%** | `open35_missing_input_census.csv` |
| Persisted storey count for that population | **Uniformly `1.0` levels / `3.5` m** (§5.1's prediction, confirmed not assumed) | `open35_neither_population.csv` |
| Archetype diversity within "neither" | **15 distinct archetypes**, dominated by `MidriseApartment` (1,028) and `SmallOffice` (898) | `open35_neither_population.csv` |
| Fleet-wide no-`height_m` | **2,806 / 8,160 = 34.39%** | `open35_missing_input_census.csv` |
| OPEN-12 `nyc_rural` (register 36.4%) | **100.00%** re-derived — large disagreement, not adjudicated | §4 |
| OPEN-12 `austin_rural` (register 19.2%) | **100.00%** re-derived — large disagreement, not adjudicated | §4 |
| Third cell at the ceiling | `nyc_suburban`, also 100% | §4 |
| Spot-check / worked-example checks | **All pass** (§6 a–d) | §6 |

---

## 8. Artifacts

- `openubem/outputs/comparisons/open35_missing_input_census.csv` — 13 rows (12 cells + `FLEET_TOTAL`):
  `cell, n_buildings, levels_usable, levels_missing_null, height_usable, height_missing_null,
  height_missing_zero, height_missing_total, pct_no_height_m, n_neither_levels_nor_height, pct_neither`.
- `openubem/outputs/comparisons/open35_neither_population.csv` — 2,611 rows: `cell, osm_id,
  raw_building_tag, raw_function_tag, persisted_levels, persisted_height_m, archetype_id,
  simulation_status`.
- This report.

**No files under `openubem/` (other than the two named comparison CSVs), `docs/docs_VALIDATION/`, or
the register were modified by this task.**
