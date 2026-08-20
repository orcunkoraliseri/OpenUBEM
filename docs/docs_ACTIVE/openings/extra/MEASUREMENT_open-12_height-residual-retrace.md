# MEASUREMENT — OPEN-12: where do 36.4% and 19.2% come from

**Date:** 2026-08-18 · **Task:** T05 of `PLAN_open-48-and-four-items-2026-08-18.md`

Script: `scripts/analysis/open12_height_residual_retrace.py`. Output:
`openubem/outputs/comparisons/open12_height_residual_retrace.csv` (8 rows: 4 cells x 2 datasets).

## Verdict, up front

**Both numbers reproduce exactly, to the fourth decimal, but only in one dataset — and that dataset
is not a repository artifact.** `nyc_rural` 36.3636% and `austin_rural` 19.1837% (both round to
36.4% / 19.2%) are read live off
`scratchpad/e-utci-09-backfill/backfilled/{nyc_rural,austin_rural}_01_buildings_backfilled.gpkg` — the
UTCI arc's own Stage-6 working copy, produced by the E-UTCI-09 partial backfill (CP-C signed
2026-07-25) and never committed. `git ls-files` confirms it is not tracked; `git check-ignore` confirms
`scratchpad/` is gitignored (`.gitignore:41`). This is the same file the arc's own
`PLAN_utci_microclimate_implementation.md:4362-4363` and `UTCI_CHECKLIST.md:128-129` report the
identical figures from — this task independently re-opened the geopackage and recomputed the fraction
rather than trusting those tables.

The fleet's tracked Stage-1 files
(`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`) still read
100.00% / 100.00% for the same two cells, confirming N06/N15's numbers by independent re-derivation.
**The contradiction dissolves into a scope statement, exactly as N15's hypothesis predicted**: the two
number-pairs describe two different, non-overlapping datasets — one a durable, version-controlled
input the fleet actually runs on, the other a disk-resident, gitignored intermediate artifact from a
single investigation session that was never merged back.

## 1. Where the numbers were sought

`docs/docs_DONE/OUTDOOR/UTCI/` was read in full (arc docs only, none edited). The percentages first
appear at `implementation/PLAN_utci_microclimate_implementation.md:1215-1216` (`nyc_rural` 72/198
"still-NaN, 36.4%"; `austin_rural` 47/245 "19.2%"), are restated at `:1353-1367`, `:1418-1419`,
`:1867`, `:1888-1889`, `:1994`, `:2011`, and again in `UTCI_CHECKLIST.md:47,122,128-129`. Every one of
these is a **doc table**, not a dataset. The task's job was to find the file behind the table.

That file is named in the arc's own manifest. Each Stage-6 run directory under
`openubem/outputs/stage6_e_utci_09_backfill/<cell>/06_mc_manifest.parquet` carries a `buildings_path`
field. For `nyc_rural` and `austin_rural` it resolves to:

```
scratchpad/e-utci-09-backfill/backfilled/nyc_rural_01_buildings_backfilled.gpkg
scratchpad/e-utci-09-backfill/backfilled/austin_rural_01_buildings_backfilled.gpkg
```

Both files exist on disk today (`ls` confirms, mtime 2026-07-25 13:02 — same day as the arc's CP-C
sign-off). Per plan §4's standing warning about eroding `%LOCALAPPDATA%`/scratch corpora, presence was
verified before anything was built around them.

## 2. Live re-derivation, not a quoted table

`scripts/analysis/open12_height_residual_retrace.py` opens each geopackage directly with `geopandas`
and counts `height_m.isna()` itself — it does not read the arc's `t11_stage6_backfilled_summary.json`
or `t11_e_utci_09_before_after_comparison.csv`, though both exist and were checked afterward as a
cross-check only (they agree to the same precision).

Command: `.venv\Scripts\python.exe scripts\analysis\open12_height_residual_retrace.py`

| dataset | cell | n | `height_m` NaN | pct NaN | register original | matches |
|---|---|---:|---:|---:|---:|---|
| `fleet_stage1_tracked` | `nyc_rural` | 198 | 198 | **100.0000%** | 36.4% | no |
| `fleet_stage1_tracked` | `austin_rural` | 245 | 245 | **100.0000%** | 19.2% | no |
| `fleet_stage1_tracked` | `nyc_suburban` | 1589 | 1589 | **100.0000%** | — (not named) | — |
| `fleet_stage1_tracked` | `austin_centre` (control) | 413 | 349 | 84.5036% | — (not named) | — |
| `utci_arc_backfilled_scratch` | `nyc_rural` | 198 | 72 | **36.3636%** | 36.4% | **yes** |
| `utci_arc_backfilled_scratch` | `austin_rural` | 245 | 47 | **19.1837%** | 19.2% | **yes** |
| `utci_arc_backfilled_scratch` | `nyc_suburban` | 1589 | 15 | 0.9440% | — (not named) | — |
| `utci_arc_backfilled_scratch` | `austin_centre` (control) | 413 | 11 | 2.6634% | — (not named) | — |

Full CSV: `openubem/outputs/comparisons/open12_height_residual_retrace.csv`.

**Control (plan §2 rule 8).** The same method, same code path, run against two datasets, gave two
different, independently-verifiable answers: 100.0000% on the fleet files (matching N06's
director-verified number exactly) and 36.3636%/19.1837% on the scratch files (matching the arc's own
doc tables exactly). A detector that returns the same number regardless of input would be worthless;
this one discriminates cleanly and both of its answers check out against a source that did not come
from this script. `austin_centre`, added as the fourth-cell control per the task's step 3, was never
claimed to be at 100% by anyone — it reads 84.5% (fleet) / 2.66% (scratch), matching the arc's own
`austin_centre` before/after figures (`t11_e_utci_09_before_after_comparison.csv`:
84.50363196125907% -> 2.6634382566585955%) and confirming the method is not cherry-picking rows.

## 3. Git-tracking status of the reproducing dataset

```
git ls-files --error-unmatch scratchpad/e-utci-09-backfill/backfilled/nyc_rural_01_buildings_backfilled.gpkg
  -> exit 1 (not tracked)
git check-ignore -v scratchpad/e-utci-09-backfill/backfilled/nyc_rural_01_buildings_backfilled.gpkg
  -> .gitignore:41:scratchpad/    scratchpad/e-utci-09-backfill/backfilled/nyc_rural_01_buildings_backfilled.gpkg
git log --oneline -1 -- scratchpad/e-utci-09-backfill/
  -> (empty — no history, directory has never been committed)
find . -iname "*backfilled*.gpkg" (whole repo, excluding .git)
  -> only the 4 files under scratchpad/e-utci-09-backfill/backfilled/; no committed copy anywhere
```

The dataset that reproduces OPEN-12's original percentages is **not, and has never been, a repository
artifact.** It is a local, gitignored, single-machine byproduct of one Stage-6 run from the E-UTCI-09
investigation (CP-C, 2026-07-25), sitting in `scratchpad/`. Nobody else who clones this repository has
it, and nothing in the tracked pipeline reads it — `06_mc_manifest.parquet`'s `buildings_path` is an
absolute path baked in at run time, not a relative reference the fleet pipeline resolves.

## 4. Answer to the binding question

**Do 36.4% and 19.2% reproduce, on any dataset, to within rounding? Yes — on the UTCI arc's own
gitignored Stage-6 scratch dataset, exactly (36.3636% / 19.1837%).** This satisfies plan §4's binding
condition: a dataset was found, so this is not a "construct one" situation and the task does not stop
at a null. The reproduction is real, live, and independently re-derived (not inherited from the arc's
own summary files, though those agree).

## 5. Does this change OPEN-12's blast radius or the arc's closing constraint

**No, on both counts, and re-derivation confirms rather than revises either.**

- **Blast radius unchanged.** The register's "3 cells, 2,032 buildings; 2,806 / 8,160 fleet-wide" is
  measured against the fleet's tracked Stage-1 files — the only files any adopted run actually reads.
  Those files still show 100.00% / 100.00% / 100.00% for `nyc_rural` / `austin_rural` / `nyc_suburban`,
  confirmed again in §2 above by direct re-read. The scratch dataset that reproduces the original
  percentages is not on that path and never was; it cannot change a blast radius computed over files it
  is not part of.
- **The arc's closing constraint holds, and this finding reinforces it rather than just leaving it
  alone.** *"Closing this needs better source coverage, not another imputation pass"* is now supported
  by two independent facts instead of one: (a) N15 already showed the fusion/backfill mechanism cannot
  reach the fleet's Stage-1 files at all (architectural, not configuration), and (b) this task shows
  that even where the backfill *was* run, by the people who built it, on the two hardest cells, it
  still left 36.4% and 19.2% of buildings with no height — the best-case, most-favourable application
  of the existing imputation mechanism does not close the gap. A better mechanism applied to the same
  OSM source data would not do better than the mechanism already tried and measured.

**What this changes in the register's framing.** The item's original percentages are not an error, a
stale artifact, or evidence of a bug — they are a real, reproducible measurement of a different,
narrower population (the arc's own partially-backfilled working set) than the population the register's
100%/100% describes (the fleet's actual tracked inputs). Both number-pairs are correct for what they
each measure; neither should be "corrected" toward the other.

## Register amendment to apply

In `INVESTIGATION_open-items-register.md`, under **OPEN-12 — The rural building-height residual**,
after the existing "Both numbers are recorded side by side and NOT adjudicated" paragraph and its
fleet-wide/zero-present-but-zero sentences, append (do not delete or restrike anything already there):

> **T05 (2026-08-18, `extra/MEASUREMENT_open-12_height-residual-retrace.md`) — source of the original
> 36.4% / 19.2% found; the contradiction is a scope statement, not an error.** Both figures reproduce
> exactly (`nyc_rural` 72/198 = 36.3636%, `austin_rural` 47/245 = 19.1837%) on a live re-read of
> `scratchpad/e-utci-09-backfill/backfilled/{nyc_rural,austin_rural}_01_buildings_backfilled.gpkg` — the
> UTCI arc's own Stage-6 working copy from the E-UTCI-09 partial backfill (CP-C, 2026-07-25). That file
> is confirmed **not tracked by git** (`scratchpad/` is gitignored, `.gitignore:41`; no commit history
> for the directory) and is not read by any part of the adopted pipeline. The fleet's tracked Stage-1
> files (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`) were
> re-confirmed at 100.00% / 100.00% / 100.00% for the three cells, independently of N06/N15, plus a
> fourth cell (`austin_centre`) as a control, matching the arc's own before/after figures for that cell
> too (84.50% -> 2.66%). **Blast radius unchanged** — it is computed over the tracked files, which the
> scratch dataset is not part of and never was. **The arc's closing constraint is reinforced, not
> weakened:** even the UTCI team's own best-effort backfill, run by hand on exactly these two cells,
> left 36.4%/19.2% unfilled — source coverage, not imputation method, is the binding constraint. Both
> number-pairs are correct for the (different) populations they each describe; the item does not need,
> and should not receive, a reconciliation toward one value.
