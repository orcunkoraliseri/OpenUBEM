# MEASUREMENT — OPEN-30 vintage persistence and OPEN-01(c) one-code-state evidence

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_e02-audit-and-closure.md`, T03.
> **Script:** `scripts/analysis/e02_vintage_and_code_state.py`
> **Outputs:**
> `openubem/outputs/comparisons/open30_vintage_distribution.csv` (192 data rows: 60 `mode_cell` +
> 12 `cell` + 5 `mode` + 5 `fleet` rows — some `(cell, mode)` combinations carry more than one vintage
> value, some only one),
> `openubem/outputs/comparisons/open01c_code_state_evidence.csv` (60 rows, one per `(cell, mode)`),
> `openubem/outputs/comparisons/open30_la_rural_year_built_crosscheck.csv` (independent, not
> plan-required — the detail behind the la_rural verdict below).
> **Date:** 2026-08-11.

## (a) OPEN-30 — vintage distribution, read from the persisted column

Read `vintage_standard` directly out of all 60 `03_manifest.parquet` files
(`C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_fleet\<cell>\step3_<mode>\03_manifest.parquet`). No call
to `resolve_vintage()` anywhere in the script — the column is read, never re-derived (RULING D).

**Coverage.** 60 / 60 manifests read. Fleet row total: **40,800** — matches the expected fleet size
exactly. Non-null `vintage_standard` in every one of the 40,800 rows (0 nulls, 0 empty strings) — every
manifest in this tree postdates R07.

**Fleet-wide distribution:**

| `vintage_standard` | n | % of fleet |
|---|---|---|
| `DOERefPre1980` | 38,125 | **93.44%** |
| `DOERef1980to2004` | 1,065 | 2.61% |
| `90.1-2013` | 890 | 2.18% |
| `90.1-2007` | 610 | 1.50% |
| `90.1-2019` | 110 | 0.27% |

**Non-uniformity control.** 5 distinct values, largest share 93.44% (`DOERefPre1980`) — not constant, not
uniform. This is the register's stated closure test (*"a column that comes out constant or uniform is a
defect, not a pass"*) and it is not tripped.

**Against the register's ≈92.9% `DOERefPre1980` figure:** the fleet-wide measured share is **93.44%**,
0.5 points above the prior proxy figure — same order, same dominant class, consistent with the proxy
being a slight understatement rather than a different population. **This is the demonstration OPEN-30's
closure condition asks for.**

**Per-cell and per-mode breakdowns** are in the CSV in full (`scope` column: `mode_cell`, `cell`, `mode`,
`fleet`). One structural fact worth stating: within every cell, the vintage split is identical across all
five modes (e.g. `austin_centre` is 397 `DOERefPre1980` / 16 `90.1-2019` in `auto`, `building`, `floor`,
`fast_zone` and `layout_assign` alike). Vintage is assigned once per building at classification time and
is mode-independent — this is consistent with that and not itself new evidence of anything.

## (a-2) Independent cross-check: la_rural manifest vintage vs. raw `year_built`

Joined `la_rural`'s manifest `vintage_standard` (all five modes, 149 buildings each) against `year_built`
in that cell's raw `01_buildings.gpkg` — a file the manifest-generation join never touches, so this is an
independent check.

**Result, all five modes identical:**

| Vintage class | n | n with known `year_built` | n missing `year_built` | all known values in expected range? |
|---|---|---|---|---|
| `90.1-2007` | 14 | 12 | 2 | **yes — 2005–2007, all 12** |
| `DOERefPre1980` | 135 | 113 | 22 | **yes — 1920–1979, all 113** |

**Verdict: R07's control reproduces exactly — zero crossover.** The first pass of this check flagged an
apparent discrepancy (12/14 and 113/135, not 14/14 and 135/135); tracing it down showed the shortfall is
entirely buildings with `year_built = NaN` (`provenance_year_built = "OSM_MISSING"` in the raw file, 2 and
22 buildings respectively) — a naive range test scores `NaN >= 2005` as `False` and looks like a
crossover. Once those are separated out as "unknown" rather than "out of range," every building with a
*known* `year_built` falls inside the vintage class's expected window, with no exceptions, in all five
modes. **No discrepancy from R07.**

## (b) OPEN-01(c) — did all five modes come from one code state?

Assembled every piece of local evidence named in the plan. What each piece shows:

**1. Manifest column schema, all 60 files.** Exactly **1 distinct schema** — all 60 manifests carry the
same 11 columns (`osm_id, idf_path, archetype_id, zoning_strategy, num_zones, num_context_buildings,
simplification_status, data_quality_flag, generation_status, resolution_mode, vintage_standard`), in the
same order. A schema difference between modes would mean different code; there is none.

**2. Manifest and IDF-directory mtimes, all 60 `(cell, mode)`.** Full table in
`open01c_code_state_evidence.csv`. Every one of the 60 manifests was written in a single **111-minute
window, 2026-08-09 21:03:01 through 22:54:38**, in a continuous cell-by-cell, mode-by-mode progression
(NYC cells first, then LA, then Austin — no gaps, no jumps backward, no second cluster on a different
day). IDF directory mtimes for each `(cell, mode)` fall inside that same window and precede that pair's
own manifest write, consistent with one continuous generation pass. **This is the strongest piece of
local evidence for one code state**, but it is still indirect: a continuous mtime sequence is consistent
with one code checkout running throughout, and is also consistent with the working tree being edited
mid-run without a new commit — mtimes cannot distinguish those two.

**3. The two `e02_generation_summary__*.json` files.** Cover **35 of 60 `(cell, mode)` pairs (7 of 12
cells)**: `batch_4cells_austin_centre` (austin_centre, austin_urban, austin_suburban, austin_rural × 5
modes = 20) and `la_urban_la_suburban_la_rural` (la_urban, la_suburban, la_rural × 5 modes = 15). **Five
cells have no generation-summary JSON at all: `nyc_centre, nyc_urban, nyc_suburban, nyc_rural,
la_centre`.** Where present, `vintage_standard_present = True` and `vintage_standard_nonnull_pct = 100.0`
for every one of the 35 covered pairs, and `fleet_tag = "e02"` in both files — consistent with one
generation process, but again only for 35 of 60 pairs, and neither file carries a git commit hash, a code
version string, or anything else that pins the code state directly.

**4. The two `e02_run*.log` files — these do NOT document the E02 fleet build.** Both logs
(`C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_five_mode\e02_run.log`, `e02_run_2.log`, dated 2026-08-06,
i.e. **three days before** the manifest mtime window in point 2) are from `t08_local_remainder.py`, a
**local, single-machine "T08 local remainder" run** that intended to cover all 12 cells × 5 modes but,
per the register's own resume-amendment record (line 220, "the newest E02 log write is still 2026-08-06
05:47:01"), got only as far as `nyc_centre` before `e02_run_2.log` ends in an unhandled `MemoryError`
during `t08_local_remainder.py`'s simulation step. Both logs reference **`nyc_centre` only** — no other
cell appears in either file. This attempt was superseded: the register records that the arc was then
paused, and the fleet that actually produced the corpus under audit here (`ubem_e02_fleet` /
`ubem_e02_harvest`) was built later via the Speed cluster path (`PLAN_speed-resume.md`, R01–R08,
2026-08-09 onward) — a different process, on a different machine, writing to a different directory tree.
**These two log files carry no evidential weight for the code state of the corpus this plan audits.**
Citing them as if they did would overstate the evidence.

## What this evidence proves, and what it does not

**Proves:** the 60 manifests share one schema; they were all written inside one continuous ~2-hour local
window with no gaps; where a generation-summary JSON exists (35 of 60 pairs), it confirms 100%
`vintage_standard` coverage and a consistent `fleet_tag`. This is **consistent with** one code state
across all five modes.

**Does not prove:** none of the available local evidence pins a code state directly — no commit hash,
version string, or checksum of `builder.py` / `construction_sets.py` is recorded anywhere in the
manifests, the JSONs, or any log, at generation time. Continuity of mtimes and identical schema are
consistent with one code state but are equally consistent with an uncommitted mid-run edit that changed
nothing about schema or timing (the exact class of risk the resume amendment's item 6 already names for
this same run). Five cells (`nyc_centre, nyc_urban, nyc_suburban, nyc_rural, la_centre` — 25 of 60 pairs)
have **no generation-summary JSON at all**, so even the indirect per-pair confirmation that exists for the
other 35 does not exist for them. **The honest statement is: the local evidence is consistent with one
code state and contains nothing that contradicts it, but it does not constitute proof — a
commit-hash-at-generation-time record does not exist for this run, and the two log files sometimes cited
as fleet evidence in fact cover none of the audited corpus.**

## Test status (plan §6/T03 "How to test")

- **Non-uniformity control:** PASS — 5 distinct values fleet-wide, largest share 93.44%, not 1.
- **Independent la_rural cross-check:** PASS / reproduces R07 — zero crossover among buildings with known
  `year_built`, in all five modes (not only `auto`). The apparent mismatch in the first pass was a script
  defect (NaN treated as out-of-range instead of unknown), corrected before reporting.
- **Coverage:** PASS — 60/60 manifests read, 100% non-null `vintage_standard` per `(cell, mode)`, fleet
  row total 40,800.
- **(b):** the evidence **cannot** demonstrate one code state with certainty; stated above precisely what
  is missing (no code-version stamp at generation time; 25/60 pairs with no JSON corroboration; the two
  named log files do not cover the audited corpus at all).

## Notes

No new register item or defect opened. The apparent la_rural crossover in the first analysis pass was a
script bug (NaN-handling), caught and corrected before being reported — not a finding about the fleet.
