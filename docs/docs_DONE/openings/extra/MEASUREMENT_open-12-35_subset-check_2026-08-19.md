# MEASUREMENT — OPEN-12 / OPEN-35: is the height-residual population a subset of the storey-count population?

> T07 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`. Read-only measurement — no production
> code touched. Script: `scripts/analysis/open12_open35_subset_check_2026-08-19.py`. Outputs:
> `openubem/outputs/comparisons/open12_open35_subset_check.csv` (per-cell contingency) and
> `openubem/outputs/comparisons/open12_open35_subset_check_buildings.csv` (8,160 per-building rows).

## The question

The register asserts, never computed: *"1,589 of `nyc_suburban`'s buildings have neither
input, so they are 61% of OPEN-35's 2,611"* and calls the two items *"the same population seen
from two sides"* (`INVESTIGATION_open-items-register.md:4495-4498`). This task computes the
exact overlap, building by building, on a fleet corpus that still exists (run 2,
`open48_refleet`), re-deriving both populations fresh rather than reusing the carried figures.

## Pre-registered prediction (written before running)

By the two items' own stated definitions — OPEN-12 = "no `height_m`" (regardless of `levels`);
OPEN-35 = "neither `levels` nor `height_m`" — OPEN-35's predicate is logically nested inside
OPEN-12's. So the prediction was: **OPEN-35 is a strict subset of OPEN-12, never the reverse**;
the fleet-wide residual (height missing, levels present — in OPEN-12 but not OPEN-35) should be
2,806 − 2,611 = 195; nyc_suburban's 1,589 should reproduce exactly and equal 60.86 % (≈ 61 %) of
OPEN-35's 2,611; and within `nyc_suburban` the two populations should coincide exactly, since the
cell is on record at 100 % missing `height_m`.

**Every part of the prediction held.**

## Method

1. Re-verified all twelve `01_buildings.gpkg` present on disk under
   `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/<cell>/` before reading anything (hard
   rule 11). This is run 2's frozen Stage-1 corpus, the same one X04 (2026-08-18 overnight) used
   when it reproduced OPEN-35's 2,611 to the unit.
2. Per cell: `height_null = height_m.isna()`, `levels_null = levels.isna()`, and the four-way
   partition `neither` / `height_only` / `levels_only` / `both_present`.
3. **Hard rule 10 cross-check.** Stage-1's `data_quality_flag` column is stamped independently,
   at acquisition (`openubem/acquisition/osm_fetcher.py:510`), with `no_height` / `no_floors`
   tokens whenever the raw OSM tag is absent — a mechanism that shares no code path with the
   `.isna()` predicates above. Every cell's token-based count was compared against the
   notna()-based count before any population figure was quoted.
4. Joined the `neither` population to each cell's `05_results.csv` to check the persisted
   `levels` value (the geometry-stage output, `derive_num_floors`).
5. Checked the `nyc_suburban` claim directly: re-derived count, and its share of OPEN-35's fleet
   total.

## Results

**Fleet-wide 2×2 contingency** (8,160 buildings, sums exactly):

| | levels present | levels missing |
|---|---|---|
| **height present** | 246 (both present) | 5,108 (levels-only) |
| **height missing** | 195 (height-only) | **2,611 (neither — OPEN-35)** |

Row total, height missing = 195 + 2,611 = **2,806 — OPEN-12, reproduces exactly.**

**Hard rule 10 cross-check: zero disagreements, fleet-wide, on both tokens, in every cell.**
The `data_quality_flag` `no_height`/`no_floors` tokens (acquisition-time) and the `.isna()`
predicates (Stage-1 read) agree on all 8,160 rows. Present-but-zero `height_m`: 0 fleet-wide,
confirming the register's note that no "0 means missing" ambiguity is in play.

**Both carried figures reproduce exactly** on run 2:
- OPEN-12: register 2,806 / 8,160 = 34.39 % → re-derived **2,806 / 8,160 = 34.39 %**.
- OPEN-35: register 2,611 / 8,160 = 32.00 % → re-derived **2,611 / 8,160 = 32.00 %**.

**Verdict: OPEN-35 is a strict (proper) subset of OPEN-12, fleet-wide.** Every one of the 2,611
"neither" buildings is also a "height missing" building by construction, so OPEN-35 ⊆ OPEN-12.
The residual, OPEN-12 \ OPEN-35 — height missing but levels present — is **195 buildings
fleet-wide (6.95 % of OPEN-12's population)**: `austin_centre` (102), `austin_suburban` (40),
`nyc_centre` (14), `la_centre` (14), `la_urban` (13), `nyc_urban` (6), `austin_urban` (4),
`la_rural` (1), `austin_rural` (1); zero in `nyc_suburban`/`nyc_rural`/`la_suburban`
(102+40+14+14+13+6+4+1+1 = 195; see the CSV for the full per-cell breakdown). OPEN-35 \ OPEN-12
is 0 by construction — not computed as a coincidence, but impossible under the predicates.

Note on the task's own title phrasing (*"is the height-residual population [OPEN-12] a strict
subset of the storey-count population [OPEN-35]?"*): read literally, the answer is **no** — a
larger population (2,806) cannot be a subset of a smaller one (2,611). The subset relationship
runs the other way: OPEN-35 ⊆ OPEN-12.

**`nyc_suburban` claim, checked to the building:**
- height_null = **1,589 / 1,589** (100 %); neither = **1,589 / 1,589** (100 %) — the two counts
  coincide exactly inside this cell, because every one of its buildings lacks both inputs.
- 1,589 matches the claim's numerator exactly.
- 1,589 / 2,611 = **60.86 %**, which matches the claim's stated **61 %** to the rounding used.

**Control: persisted geometry.** All 2,611 "neither" buildings persist at `levels = 1.0` in
`05_results.csv` — **2,611 / 2,611 = 100.0000 %, no exceptions** — reconfirming the register's
already-established mechanism finding on this corpus.

## What this settles, and what it does not

- The register's framing — "the same population seen from two sides" — is **imprecise but not
  wrong in spirit**: OPEN-35 is not equal to OPEN-12, it is a proper subset covering 93.05 % of
  it (2,611 of 2,806). The two items diverge on exactly 195 buildings fleet-wide (6.95 %) that
  are missing `height_m` but do have an observed `levels` value — these are OPEN-12's population
  but never reach OPEN-35's two-fallback mechanism, because `_impute_levels` and
  `derive_num_floors` both take the observed `levels` value first and never touch the height
  fallback for these rows.
- Within `nyc_suburban` specifically, the two populations are **identical** (both 1,589) — this
  is the cell driving the "same population" impression, and it is a correct impression for that
  one cell, not fleet-wide.
- **Recommendation, not taken:** a merge of OPEN-12 into OPEN-35 (or vice versa) would need to
  explicitly carry forward the 195-building residual that only OPEN-12 covers, or the merge would
  silently drop a real (if small) population from tracking. Whether to merge is the user's call
  per ruling discipline; this measurement only supplies the numbers.

## Reproducibility

Corpus: `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/<cell>/01_buildings.gpkg`, all
twelve cells, re-verified present at run time. Results join:
`docs/validations/overAll/results/open48_refleet/<cell>/05_results.csv`. Script and both CSV
outputs are committed alongside this write-up.
