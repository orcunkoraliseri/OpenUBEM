# MEASUREMENT — OPEN-12: re-deriving the height_m residual on run-4 tracked Stage-1 files

**Task:** T08 of `../implemenation/previous/PLAN_twenty-items-2026-08-19.md`. Script:
`scripts/analysis/open12_t08_residual_rederivation_2026-08-19.py`. Output:
`openubem/outputs/comparisons/open12_t08_residual_rederivation_2026-08-19.csv`.

## 1. Method and which artifact this uses

OPEN-12's fleet-tracked figures (34.39%, 2,806, and the three 100%-cells) were originally derived
from the fleet's own Stage-1 `01_buildings.gpkg` files, **not** the UTCI arc's gitignored
scratchpad backfill copies (those reproduce the separate 36.4%/19.2% pair, per the register's own
scope split — not re-touched here). This re-derivation uses **`open48_refleet4`'s**
`01_buildings.gpkg` per cell — run 4, the fleet's current run, rather than run 2 (which the prior
2026-08-19 subset-check task used) — since run 4 is the most current tracked-artifact-equivalent
input this pass has, and rule 11 asks for re-derivation, not a repeat of the same run.

Per cell: `n` buildings, `height_m` absent (`isna()`) vs present; present split into **observed**
(raw source — `provenance_height_m` is `OSM_OBSERVED`, `None`/empty) vs **backfilled** (any other
provenance token, i.e. an imputation/fusion tier stamped it); cross-checked against
`data_quality_flag`'s `no_height` token.

## 2. Fleet-wide table

| cell | n | absent | % absent | observed | backfilled | flag `no_height` | disagreements |
|---|---:|---:|---:|---:|---:|---:|---:|
| austin_centre | 413 | 349 | 84.5036% | 64 | 0 | 349 | 0 |
| austin_rural | 245 | 245 | **100.0000%** | 0 | 0 | 245 | 0 |
| austin_suburban | 437 | 114 | 26.0870% | 323 | 0 | 114 | 0 |
| austin_urban | 425 | 47 | 11.0588% | 378 | 0 | 47 | 0 |
| la_centre | 226 | 45 | 19.9115% | 181 | 0 | 45 | 0 |
| la_rural | 149 | 1 | 0.6711% | 148 | 0 | 1 | 0 |
| la_suburban | 1,343 | 15 | 1.1169% | 1,328 | 0 | 15 | 0 |
| la_urban | 618 | 42 | 6.7961% | 576 | 0 | 42 | 0 |
| nyc_centre | 738 | 121 | 16.3957% | 617 | 0 | 121 | 0 |
| nyc_rural | 198 | 198 | **100.0000%** | 0 | 0 | 198 | 0 |
| nyc_suburban | 1,589 | 1,589 | **100.0000%** | 0 | 0 | 1,589 | 0 |
| nyc_urban | 1,779 | 40 | 2.2485% | 1,739 | 0 | 40 | 0 |
| **FLEET_TOTAL** | **8,160** | **2,806** | **34.3873%** | 5,354 | 0 | 2,806 | **0** |

## 3. Whether the register's carried numbers reproduce

- **Fleet-wide 2,806 / 8,160 = 34.39% reproduces exactly** (34.3873%, same to the reported
  precision) on run 4, independent of the run-2 figure the register carried before.
- **The three-cell, 100%-absent population totals exactly 2,032** (245 + 198 + 1,589) —
  reproduces T08's own stated "3 cells / 2,032 buildings" figure exactly.
- **The third cell — never named by the item's original two-cell framing — is `nyc_suburban`**
  (1,589 / 1,589, 100.00%), matching N06's 2026-08-06 finding, reproduced fresh here.
- **`data_quality_flag`'s `no_height` token agrees with `height_m.isna()` for every one of 8,160
  buildings — zero disagreements fleet-wide**, reproducing the register's "zero disagreements"
  cross-check on run 4.
- **`n_backfilled` is zero in every cell, fleet-wide.** `provenance_height_m` takes exactly two
  distinct values across the whole fleet — `OSM_OBSERVED` and `OSM_MISSING` — no fusion, spatial,
  ml or statistical token appears anywhere. This corroborates OPEN-14's independent finding (T07,
  this pass) that no code path ever backfills `height_m` on the fleet's own tracked files: the
  absence here is not a sampling artifact of this method, it is the whole population.
- **The 36.4% (`nyc_rural`) / 19.2% (`austin_rural`) pair is not re-derived here** — those numbers
  describe the UTCI arc's own gitignored scratchpad backfill copies
  (`scratchpad/e-utci-09-backfill/backfilled/*.gpkg`), a different artifact than the fleet's
  tracked Stage-1 files this task measures, per the register's own explicit scope split
  (2026-08-18 T05 finding, quoted in the register: "both number-pairs stand"). Re-deriving that
  pair was not this task's target — T08's `data_quality_flag` cross-check and 2,032/2,806
  reproduction targets the tracked-fleet numbers specifically, and both of those numbers
  reproduce.

## 4. Verdict

**Every number T08 was asked to re-derive reproduces on run 4**, using a different run than the
figure was last checked against (run 2 → run 4), with the same zero-disagreement cross-check
holding. No STOP condition triggered — nothing here contradicts the register.
