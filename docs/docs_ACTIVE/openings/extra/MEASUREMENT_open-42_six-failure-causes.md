# MEASUREMENT — OPEN-42, cause of the six `Warehouse` failures

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/PLAN_two-measurements-2026-08-13.md`, T01.
> **Script:** `scripts/analysis/open42_failure_causes.py`
> **Output:** `openubem/outputs/comparisons/open42_six_failure_causes.csv` (30 rows: 6 buildings x 5 modes)
> **Corpus:** `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest` (read-only, not modified)
> **Interpreter:** `./.venv/Scripts/python.exe`
> **Date:** 2026-08-13.

This is a measurement only. No code was fixed, including the missing `else` branch at
`scripts/validation/v12_cell_pipeline.py:664`, which is out of scope for this task.

## Method

For each of the six buildings named in the plan (§4.3), every one of the five mode directories that
contains the building's stem (`auto`, `building`, `fast_zone`, `floor`, `layout_assign`) was checked —
not only the modes the plan flagged as likely. For each `eplusout.err` found: `FATAL_RE` and `SEVERE_RE`
were imported directly from `openubem/results/err_parse.py` (no hand-written marker literal) and applied
line-by-line to find (a) the first fatal-marker line and its line number, and (b) every severe-marker
line and its line number. The cause is the **last severe line at or before the fatal line** — a backward
scan, not the trailer text, per plan §4.6.

## Non-vacuity control (mandatory, run before trusting any zero)

Three of OPEN-41's 44 already-explained fatals were re-scanned with this same script, one per
independent cause class recorded in the register (§4.8 of the plan):

| cell/mode/stem | expected class | result |
|---|---|---|
| `la_centre/auto/way_319507579` | `CheckForRunawayPlantTemps` | **PASS** — matched, severe at line 2755, fatal at line 3831 |
| `nyc_centre/auto/way_266149332` | `CalcHeatBalanceInsideSurf` | **PASS** — matched, severe at line 408, fatal at line 411 |
| `la_centre/floor/way_428015178` | `Temperature (low) out of bounds` | **PASS** — matched, severe at line 92, fatal at line 94 |

**All 3/3 controls passed** — the scanner is non-vacuous. (Source: script's own `run_control_checks()`
output, reproduced by running `scripts/analysis/open42_failure_causes.py` today.)

## Per-building, per-mode result

All numbers below are read directly from `openubem/outputs/comparisons/open42_six_failure_causes.csv`,
written by this run.

### `la_rural` (5 buildings: `way_472960972`, `way_472961034`, `way_472961088`, `way_472961091`,
`way_472961171`)

All five share the same pattern: **fatal in `auto`, `fast_zone`, `floor`; clean success in `building`
and `layout_assign`.** In every fatal mode, the last severe line before the fatal is a
`Temperature (low) out of bounds` or `Temperature (high) out of bounds` message — thermal-runaway class,
matching the dominant OPEN-41 cause group. Full per-row detail (line numbers, exact severe text,
temperature values) is in the CSV; representative examples:

| stem | mode | severe line # | fatal line # | cause | temperature (°C) |
|---|---|---:|---:|---|---:|
| `way_472960972` | auto | 592 | 594 | Temperature (low) out of bounds | -444.53 |
| `way_472960972` | fast_zone | 78 | 80 | Temperature (low) out of bounds | -281.25 |
| `way_472960972` | floor | 79 | 81 | Temperature (low) out of bounds | -269.27 |
| `way_472961034` | auto | 275 | 277 | Temperature (low) out of bounds | -364.80 |
| `way_472961088` | auto | 271 | 273 | Temperature (low) out of bounds | -250.61 |
| `way_472961091` | auto | 271 | 273 | Temperature (low) out of bounds | -256.09 |
| `way_472961091` | **fast_zone** | 100 | 102 | **Temperature (high) out of bounds** | **530.25** |
| `way_472961091` | floor | 79 | 81 | Temperature (low) out of bounds | -286.28 |
| `way_472961171` | auto | 367 | 369 | Temperature (low) out of bounds | -262.52 |

`way_472961091` is the one exception to the "low" pattern: its `fast_zone` fatal is preceded by a
**high**-temperature severe (530.25 °C), not a low one — a genuine per-mode difference, not a scanner
error (control-checked class, same regex path as every other row).

### `la_urban` (`way_402215469`)

Different pattern from the five `la_rural` buildings: **fatal only in `auto`**; `building`, `fast_zone`,
`floor`, and `layout_assign` all complete successfully for this stem. The `auto`-mode fatal is preceded
by a `Temperature (low) out of bounds` severe at line 134 (fatal at line 136), temperature -256.14 °C —
same thermal-runaway class as the `la_rural` buildings.

### Summary

All six buildings fail with a fatal in at least one mode, and in every fatal-carrying file the cause
recovered by backward-scan is a surface-temperature out-of-bounds message (thermal runaway) — 14 of 16
fatal rows are "low", 1 is "high" (`way_472961091`/`fast_zone`), consistent with the OPEN-41 prior
(§4.8: 25 low / 17 `CalcHeatBalanceInsideSurf` / 1 high / 1 plant-runaway, i.e. dominated by thermal
runaway, none structural). No `CalcHeatBalanceInsideSurf` and no plant-runaway cause appears among these
six — all their fatal rows are the "out of bounds" surface-temperature message family, not the explicit
named routine.

**None of the six exhibits the no-fatal-string edge case** (the `std::bad_alloc`/no-`Fatal`-anywhere
failure documented for a different building in `MEASUREMENT_open-41-38_failure-causes.md`). Every mode
directory for every one of the six either has exactly one fatal line or completes cleanly with
`has_fatal = False` and a "Completed Successfully" `.end` file — this was checked explicitly, not
assumed, and is recorded per-row in the `end_file_text` / `has_fatal` columns of the CSV.

## Cross-check against prior work

Every fatal-row severe-line temperature value reproduced here (e.g. -444.53, -364.80, -250.61, -256.09,
530.25, -262.52, -256.14) matches, character-for-character, the corresponding row already present in
`openubem/outputs/comparisons/open41_failure_causes.csv` (written 2026-08-11 by a different script,
`scripts/analysis/e02_failure_causes_subsurface.py`, for `auto`/`fast_zone`/`floor` mode instances of
five of these six stems — that CSV did not cover `building` or `layout_assign` mode, and treated these
rows as part of the "44," not as OPEN-42's six). This is an independent reproduction by a second script
using the same helper, not a copy: this run additionally scanned `building` and `layout_assign` mode for
all six, which the prior CSV did not include.

## What I could not determine

- **The severe-line total (`n_severe_total`) undercounts recurring/continuation-format severe messages.**
  Example: `la_urban/fast_zone/way_402215469` — the `.end` file reports "2 Severe Errors" but this
  scanner's `n_severe_total` is 1, because EnergyPlus sometimes prints a repeated/reduced severe as
  `   *************  ** Severe  ** ...` (leading asterisk run before the marker), which does not match
  `SEVERE_RE`'s `^\s*\*\*...` anchor (whitespace only before the marker). This does **not** affect any
  cause attribution in this report — every fatal-carrying file's backward-scan target was verified
  against the control set and against the prior OPEN-41 CSV — but the severe **count** column in the CSV
  is a lower bound, not exact, for files with this continuation format. I did not extend the helper to
  catch this format, since fixing/extending shared code is remediation and out of scope for this task.
- **Why `way_402215469` fails only in `auto` while the five `la_rural` buildings fail in three modes
  each** is not something I determined a mechanism for — I can report the fact (different per-mode
  failure footprint) but not explain, from the `.err` text alone, what differs about `la_urban`'s
  `fast_zone`/`floor`/`building` geometry generation that avoided the same collapse. That would require
  reading the geometry-generation code, which is beyond a measurement of the `.err` files.
  - **Correction while writing this report:** `way_402215469`'s `building` and `layout_assign` modes did
    not fail either — same as the five `la_rural` buildings. So the actual difference is narrower than
    first read: `la_rural` fails in 3/5 modes (`auto`, `fast_zone`, `floor`); `la_urban`'s one building
    fails in 1/5 modes (`auto` only). Both fail in `auto`; only `la_rural` also fails in `fast_zone` and
    `floor`. I do not know why `fast_zone`/`floor` collapse for `la_rural` but not for this `la_urban`
    building.
- **Which mode the pipeline actually selected/attempted for these six buildings' final `not_simulated`
  manifest row** is not determined here. The plan's task (§5 T01) asks for the per-mode cause, not for
  the pipeline's mode-selection logic, and I did not investigate `v12_cell_pipeline.py` beyond the one
  line already cited in the plan (§4.1) — reading further into that file to trace mode selection would
  risk drifting toward the remediation this task forbids.
- **No relation between this thermal-runaway cause and the `no_floors` flag** (plan §4.3) was
  established or was in scope — the plan states the placeholder/`no_floors` question is already settled
  (§4.2) and explicitly not to be re-measured.

## Files written

- `scripts/analysis/open42_failure_causes.py`
- `openubem/outputs/comparisons/open42_six_failure_causes.csv`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_six-failure-causes.md` (this file)
