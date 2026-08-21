# MEASUREMENT — OPEN-60: production's integrity gate run over the whole fleet

**Date:** 2026-08-20 · **Task:** T01 of `PLAN_ten-live-items-2026-08-20-evening.md`
**Population:** every `eplusout.sql` found in the OPEN-61 census corpus
(`<scratchpad>/open61_census_fleet_work/<cell>/<stem>/sim_out/eplusout.sql`) at scan time.
**Denominator: 7,860** throughout (D5).

## 1. What was measured

`openubem.results.parser.check_building_integrity()` (D3, called exactly as
`scripts/run_r3_fleet.py:313` calls it — `check_building_integrity(sql_path)`, no `mtr_path`)
called on every `.sql` found by `CORPUS.glob("*/*/sim_out/eplusout.sql")`. `cell`/`osm_id`/
`archetype_id` joined from `openubem/outputs/comparisons/open61_census_fleet.csv` by stem
(`osm_id` with `/` → `_`). Because the gate does not return the raw ABUPS/hourly diff it computes
internally, the diff is captured for the CSV's `raw_abups_diff` column by monkey-patching
`sqlite3.connect` **inside the analysis script only** (rule 2) — a wrapper that records the four
`fetchone()` values the gate itself already queries, in the order it queries them, then applies
the gate's own formula (`abs(hourly_j - abups_j) / abups_j`) purely for display; the gate's SQL,
its thresholds and its `abups_ok`/`meter_ok`/`gas_zero` booleans are untouched and unre-implemented.

Script: `scripts/analysis/open60_fleet_integrity_gate_2026-08-20.py` (max 4 worker processes, per
instruction — an EnergyPlus job was running on the box). Output:
`openubem/outputs/comparisons/open60_fleet_integrity_gate_2026-08-20.csv` (7,860 rows).

## 2. Population note (not a T01 failure — reported per rule 8)

The census corpus (`open61_census_fleet_work`) holds **7,861 stem directories**, not the 8,151
rows listed in `open61_census_fleet.csv` — **290 buildings short**, spread across all 12 cells
roughly in proportion to cell size (e.g. `nyc_urban` 1,663/1,779, `nyc_suburban` 1,546/1,589,
`austin_centre` 402/413). This is wider than the "one building still simulating" briefing and is
a fact about the local corpus's completeness, not the gate. T01's population is the corpus as it
stands (D2, read-only); the 290-short gap is not fixed or investigated here.

Within the 7,861 stem directories present, exactly **one** building was mid-write during the scan:
`nyc_centre/way_266170763` — its `eplusout.sql` triggered `sqlite3.OperationalError: database is
locked` inside the gate's own `try/except` (`openubem/results/parser.py:686`), which the gate
handles by returning `{abups_ok: None, meter_ok: None, gas_zero: None}` rather than raising. This
is the one still-simulating building; it is counted, not skipped, and is the only row with all
three flags `None` and no census-CSV metadata match (it had not yet reached the census CSV either).
One further stem directory, `la_urban/way_427278443`, has no `sim_out/` at all yet and so was never
in the 7,860-file scan population.

## 3. Results

- **Denominator: 7,860** `.sql` files found and gated; 0 wrapper-level skips (the one mid-write
  file returned an all-`None` row from inside the gate itself, per §2).
- **abups_ok:** True **7,857**, False **2**, None **1** (n=7,860).
- **meter_ok:** True **6**, False **7,853**, None **1** (n=7,860).
- **gas_zero:** True **40**, False **7,819**, None **1** (n=7,860).

### Worst 5 cells by `abups_ok`-false rate

| cell | false | n | rate |
|---|---|---|---|
| la_rural | 1 | 141 | 0.71 % |
| la_centre | 1 | 221 | 0.45 % |
| austin_centre | 0 | 402 | 0.00 % |
| austin_rural | 0 | 235 | 0.00 % |
| austin_suburban | 0 | 420 | 0.00 % |

(Only two cells have any `abups_ok=False` row at all; the remaining three listed are 0.00 % ties.)

### Worst 5 archetypes by `abups_ok`-false rate

| archetype | false | n | rate |
|---|---|---|---|
| SecondarySchool | 1 | 11 | 9.09 % |
| Warehouse | 1 | 32 | 3.13 % |
| LargeOffice | 0 | 256 | 0.00 % |
| HighriseApartment | 0 | 32 | 0.00 % |
| OpenUBEMUnknown | 0 | 619 | 0.00 % |

(Only two archetypes have any `abups_ok=False` row at all; the remaining three listed are 0.00 % ties.)

### C2 — fleet vs. OPEN-60's 48-building sample (pre-registered, allowed to fail)

Fleet `abups_ok` false-rate: **2 / 7,860 = 0.0254 %**. Sample (`layout_assign`, OPEN-60): **42 / 48
= 87.50 %**. The fleet rate is **far below** the sample rate — delta **−87.47 percentage points**.
This is the expected direction stated in the task: the sample was drawn from `layout_assign` and
the fleet corpus is `auto`, and a much lower fleet rate is the anticipated result, not a finding.

### C3 — determinism (5 random buildings, re-run and diffed)

All 5 re-runs reproduced identical `abups_ok`/`meter_ok`/`gas_zero` on the second pass
(`way/280621574`, `way/281345324`, `way/265875622`, `way/1014146196`, `way/813473625`). **PASS.**

### C1 — row count / uniqueness

`gated_rows (7,860) + skipped (0) == sql_found (7,860)` — **PASS.** All 7,860 `osm_id` values in
the output are unique — **PASS** (the one unmatched row has an empty `osm_id`, occurring once).

## 4. C1–C3 verdict

**C1 PASS, C2 PASS (fleet rate far below sample, expected direction), C3 PASS.**

## 5. What this does and does not answer

`meter_ok` fails on nearly the whole fleet (7,853 / 7,860 = 99.9 %) while `abups_ok` passes on
nearly the whole fleet (7,857 / 7,860 = 99.97 %) — two very different pictures from two gates in
the same function. This report states the counts; it does not diagnose why `meter_ok` fails at
that rate or propose a fix (rule 1) — that is a design question for whoever next asks "should the
fleet pipeline call `check_building_integrity()`."
