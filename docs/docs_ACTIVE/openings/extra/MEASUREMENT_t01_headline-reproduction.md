# MEASUREMENT — T01: the 153.8231 headline that will not reproduce

**Script:** `scripts/analysis/t01_headline-reproduction_2026-08-21b.py`
**CSV:** `openubem/outputs/comparisons/t01_headline-reproduction_percell_2026-08-21b.csv`
**Source table cited by rule 5, §4:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_fleet-restatement-2026-08-19.md:13-14` (headline)
and `:26-38` (per-cell), located via `grep -rn "153.82" docs/`.

## Result

**C1 — reproduced.** Row set (b), the 8,153 successes over `evidence/open48_refleet4`, pools to
**153.8304**, matching F7's two independent recomputations to 4 dp.

**Row sets (a)/(b)/(c)/(d) are identical: 153.8304, n=8,153 (successes), area 24,333,586.4 m².**
The 7 failures carry `floor_area_m2 == 0` (F6), so filtering all-8,160 → successes-only →
area-positive → eui-non-null removes nothing further. There is no subset of this corpus that lands
anywhere near 153.8231.

**Per-cell:** all twelve cells are within 0.02–0.18 kWh/m² of the restatement table's per-cell
figures (`t01_headline-reproduction_percell_2026-08-21b.csv`). `austin_suburban` is the largest
outlier at −0.18. No cell is off by an amount that would explain the pooled 0.0073 gap on its own —
the twelve small per-cell drifts partially cancel.

**Rounding hypothesis — rejected.** 153.8304 rounded to 0–5 decimal places never produces 153.8231
at any precision (153.8, 153.83, 153.8304, 153.83044 — none match).

**Different-source hypothesis — tested two ways, both fail:**
1. **The register's own cited provenance path**, `%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet4\`
   (named at `MEASUREMENT_fleet-restatement-2026-08-19.md:210` as the run-4 source), still exists on
   disk. It reproduces **153.8304 exactly**, byte-for-byte the same pooled figure as
   `evidence/open48_refleet4`, with an identical sorted `osm_id` set across both. The TEMP source and
   the evidence/ copy are not the discrepancy — they agree with each other and disagree with the
   record.
2. **The other five run directories under `evidence/open48_refleet*`:** `open48_refleet` has all 12
   cells but predates the `floor_area_m2`/`floor_area_provenance` columns (F5) — its schema only has
   `footprint_area_m2`, so it cannot be pooled the same way and is not a candidate. `open48_refleet3`,
   `open48_refleet3_t02a3`, `open48_refleet3_t02a4` have 5, 0, and 1 of the 12 cells respectively —
   incomplete populations, not candidates. `open48_repeat` was not checked as a 12-cell candidate
   (single cell only, `nyc_centre`).

## C2 — headline answer

**No.** No row set of `evidence/open48_refleet4`, no alternate run directory on disk, and the
register's own cited TEMP provenance path reproduces **153.8231**. Every path on disk that carries a
complete 12-cell, `floor_area_m2`-bearing 05_results.csv converges on **153.8304**, not 153.8231. The
0.0073 kWh/m² (0.005 %) gap between the adopted record and everything recoverable from disk is
**not explained by rounding, by row-set filtering, or by a different source directory** — including
the exact directory the restatement doc names as its own source, which today returns a different
number than the doc recorded. The record and the recomputation both stand; the 153.8231 origin
itself is not recoverable from what is on disk.

**Per rule 1 of §2: this is a measurement, not a remedy.** No fix is proposed. The adopted
153.8231 figure is not restated or changed by this task.
