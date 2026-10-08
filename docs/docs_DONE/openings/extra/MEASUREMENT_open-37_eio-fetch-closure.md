# MEASUREMENT — OPEN-37: close the `.eio` fetch gap at the five remaining sites, census the harvest

**Date:** 2026-08-18 · **Task:** T03 of `PLAN_five-items-2026-08-18.md`

## 1. The five edits

All five sites were verified at HEAD before editing, by exact string match on
`{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end`:

| File | Line (pre-edit) | Status |
|---|---|---|
| `scripts/cluster/t07_harvest_results.py` | 102 | matched, edited |
| `scripts/validation/v11_nyc_centre_pipeline.py` | 290 | matched, edited |
| `scripts/validation/v12_cell_pipeline.py` | 354 | matched, edited |
| `scripts/validation/v12_nyc_urban_recovery.py` | 94 | matched, edited |
| `scripts/validation/v12_nyc_urban_recovery.py` | 199 | matched, edited |

Each site's `paths_str` / `fetch_cmd` join now appends ` {oid}/eplusout.eio` in the same f-string
style already used at `t08_harvest_results.py:131` (`*/eplusout.sql */eplusout.err */eplusout.end
*/eplusout.eio`).

`git diff --stat`:

```
 scripts/cluster/t07_harvest_results.py        | 2 +-
 scripts/validation/v11_nyc_centre_pipeline.py | 2 +-
 scripts/validation/v12_cell_pipeline.py       | 2 +-
 scripts/validation/v12_nyc_urban_recovery.py  | 4 ++--
 4 files changed, 5 insertions(+), 5 deletions(-)
```

That is exactly five insertions and five deletions across the four files (two edits land in the same
file, `v12_nyc_urban_recovery.py`, at its two independent fetch sites) — matching "five files, five
insertions, five deletions — nothing else."

`ast.parse` on all four edited files: all four parse cleanly (no syntax check failures). These
scripts were **not executed** — they require a live cluster connection, which this task is forbidden
from opening.

## 2. Confirmation grep

Post-edit, all five sites now name `eplusout.eio`:

```
scripts/cluster/t07_harvest_results.py:102:        f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio"
scripts/validation/v11_nyc_centre_pipeline.py:290:        + " ".join(f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio" for oid in osm_ids)
scripts/validation/v12_cell_pipeline.py:354:            f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio"
scripts/validation/v12_nyc_urban_recovery.py:94:            + " ".join(f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio"
scripts/validation/v12_nyc_urban_recovery.py:199:        + " ".join(f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio" for oid in repaired)
```

The five R09 sites (fixed 2026-08-10) are untouched by this task's edits and still carry `.eio` at
their cited lines, confirmed directly against the plan's citations (the plan's own line numbers for
t18/t19/t20 were re-verified against the actual filenames `t18_harvest_layout_assign.py`,
`t19_harvest_layout_assign.py`, `t20_harvest_layout_assign.py` — no `_r09` files exist under
`scripts/cluster/`):

```
scripts/cluster/t08_harvest_results.py:131:        f"tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end */eplusout.eio"
scripts/cluster/t17_harvest_layout_assign.py:146:        f"tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end */eplusout.eio"
scripts/cluster/t18_harvest_layout_assign.py:142:        f"tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end */eplusout.eio"
scripts/cluster/t19_harvest_layout_assign.py:150:        f"tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end */eplusout.eio"
scripts/cluster/t20_harvest_layout_assign.py:150:        f"tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end */eplusout.eio"
```

All ten fetch sites (the five R09 sites plus the five closed here) now request `eplusout.eio`.
`scripts/cluster/t26_harvest_utci_cluster.py` remains not applicable (fetches UTCI rasters, not
EnergyPlus simulation output).

## 3. The local E02 harvest census

`scripts/analysis/open37_eio_census.py` walked
`C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\<cell>_<mode>\` read-only and wrote
`openubem/outputs/comparisons/open37_eio_census.csv` (61 rows: 60 (cell, mode) directories + 1 TOTAL
row).

**Site-directory count: 60 (cell, mode) directories**, matching the plan's stated expectation exactly
— 3 cities (`austin`, `la`, `nyc`) × 4 sub-cells (`centre`, `rural`, `suburban`, `urban`) × 5 modes
(`auto`, `building`, `fast_zone`, `floor`, `layout_assign`).

**Fleet totals:**

| Metric | Count | Against expected 40,800 |
|---|---|---|
| `n_building_dirs` | **40,800** | exact match, no rounding needed |
| `n_eio` | **40,800** | equal to `n_building_dirs` — every building directory in the local harvest carries an `eplusout.eio` |
| `n_eio_empty` | **0** | none of the 40,800 `.eio` files is zero bytes |
| `n_sql` | 39,926 | 874 short of 40,800 |
| `n_err` | 40,800 | exact match |
| `n_end` | 39,925 | 875 short of 40,800 |

`n_building_dirs` matches the expected 40,800 exactly — reported as-is, no reconciliation needed
because there is no mismatch to reconcile.

**The `n_sql`/`n_end` shortfall is real and is reported, not smoothed over.** Per-(cell, mode)
breakdown shows it is concentrated: `austin_suburban_fast_zone` and `austin_suburban_floor` each show
`n_sql = 0, n_end = 0` against `n_eio = 437` and `n_err = 437` (437 + 437 = 874, exactly the fleet-wide
`n_sql` shortfall), and `nyc_centre_fast_zone` shows `n_end = 737` against `n_eio = 738` (the
remaining 1 of the 875 `n_end` shortfall). Every other (cell, mode) directory has `n_sql = n_end =
n_eio = n_err = n_building_dirs`. This pattern — `.eio` and `.err` present, `.sql` and `.end` absent —
is consistent with runs that reached EnergyPlus's zone/sizing report stage (which writes `.eio`) but
did not reach a normal simulation completion (which writes `.end` and the SQL output database); it is
not an `.eio`-fetch problem, since the `.eio` file is present in every one of these directories.

## 4. Closure recommendation

**OPEN-37 can close.**

- All ten fetch sites in this repository now request `.eio` (five fixed by R09, five fixed by this
  task) — verified by grep against every cited line, exact string match, on both the before and after
  states.
- The census establishes that, for the harvest corpus already on this machine, the `.eio` file did in
  fact come home for every single building directory found (40,800 of 40,800), with zero empty files.
  There is no local evidence of a gap in `.eio` delivery for this corpus.
- The historical caveat — that older harvests predating both R09 and this fix may be missing `.eio`
  — is recorded as a **permanent disposition**: those older harvest runs cannot retroactively gain the
  file, and no fetch-site edit can reach backward in time to fix them. Any future harvest run,
  however, uses code where all ten sites request `.eio`.
- The `.sql`/`.end` shortfall (874–875 directories) found during the census is a **different**
  question — failed/incomplete simulation runs, not a missing-fetch-request defect — and is reported
  here for visibility but is out of this item's scope; it does not block OPEN-37's closure and is not
  itself a fetch-list gap (the `.eio` and `.err` files that share those same directories are present).

**Deliverable CSV:** `openubem/outputs/comparisons/open37_eio_census.csv`.
