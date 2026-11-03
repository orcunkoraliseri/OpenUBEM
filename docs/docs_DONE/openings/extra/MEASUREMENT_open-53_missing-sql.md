# MEASUREMENT — OPEN-53: why 874 harvest directories have no `.sql`, 875 have no `.end`

**Date:** 2026-08-18 · **Task:** T02 of `PLAN_four-items-2026-08-18.md`

Script: `scripts/analysis/open53_missing_sql_census.py`. Output: `openubem/outputs/comparisons/open53_missing_sql_census.csv` (40,800 rows; every short directory and the 200-directory control are fully classified, all other rows carry presence flags only).

## 1. Step 2 — reproduction of the census that opened the item

Walking `HARVEST_ROOT` fresh and counting from scratch:

```
n_dirs=40800  n_eio=40800  n_eio_empty=0  n_err=40800  n_sql=39926  n_end=39925
```

This matches plan §5 fact 1 exactly: 40,800 directories, 40,800 `.eio`/`.err` (both exact, zero empty), `.sql` = 39,926, `.end` = 39,925. Gap: 874 missing `.sql`, 875 missing `.end`. No STOP required.

The union of "missing `.sql` OR missing `.end`" is **875** short directories (874 are missing both; 1 is missing only `.end`), which is the population classified below.

## 2. Step 3 — terminal-class classification of the 875 short directories

Read the tail of each short directory's `eplusout.err` and classified into exactly one of `fatal` / `completed` / `truncated` / `empty`, per the plan's definitions (whitespace-tolerant `FATAL_RE` from `openubem/results/err_parse.py`; `completed` = contains the literal string `EnergyPlus Completed Successfully`; `empty` = 0 bytes; `truncated` = none of the above).

| terminal_class | count | % of 875 |
|---|---|---|
| `completed` | 874 | 99.9% |
| `truncated` | 1 | 0.1% |
| `fatal` | 0 | 0.0% |
| `empty` | 0 | 0.0% |

**Zero of the 875 short directories are `fatal`.** 874 of them ran EnergyPlus to completion — the `.err` file itself says `EnergyPlus Completed Successfully-- N Warning; 0 Severe Errors` — despite `.sql` and `.end` both being absent from disk. The one exception (`nyc_centre_fast_zone/way_1240348353`) is `truncated`: its `.err` stops mid-input-processing, inside a run of `GetSimpleAirModelInputs: ZoneInfiltration` warnings for zone `_F88_CORE` (the file's last non-blank line is one of these), well before EnergyPlus even reaches "Beginning Simulation." No Fatal, no Severe, no completion marker. This directory does have `.sql` (208,896 bytes) but no `.end`.

## 3. Step 5 — obligatory control: 200 random directories that DO have `.sql` and `.end`

Random sample, `random.Random(53).sample(...)`, seed fixed to the item number for reproducibility.

| terminal_class | short (n=875) | control (n=200) |
|---|---|---|
| `completed` | 874 (99.9%) | 200 (100.0%) |
| `truncated` | 1 (0.1%) | 0 (0.0%) |
| `fatal` | 0 (0.0%) | 0 (0.0%) |
| `empty` | 0 (0.0%) | 0 (0.0%) |

**The `completed` signature does not separate the populations** — it is at 99.9% in the short population and 100.0% in the control. Per the plan's controls-before-results rule, this is reported as a finding, not a failure of the classifier: it means EnergyPlus's own completion status, as recorded in `.err`, is statistically indistinguishable between directories that got a `.sql`/`.end` and directories that did not. Whatever caused the 874 shortfall, it did not stop EnergyPlus from finishing its run.

`truncated` appears once in 875 short directories and zero times in 200 control directories — too rare in both to call comparable or not from this sample size; it is treated as a single, separately-explained case (§2), not evidence of a broader truncation signature.

## 4. Step 4 — fatal cause classes

`n_fatal = 0` among the 875 short directories. There is no `** Severe **` line to extract and no cause-class table to report — the fatal population from which OPEN-53 was hypothesized to draw is empty.

## 5. Step 6 — concentration by (cell, mode)

| cell_mode | short count | population | fraction short |
|---|---|---|---|
| `austin_suburban_fast_zone` | 437 | 437 | **100.0%** |
| `austin_suburban_floor` | 437 | 437 | **100.0%** |
| `nyc_centre_fast_zone` | 1 | 738 | 0.1% |

874 of 875 sit in exactly two (cell, mode) buckets, and in both buckets **every single directory** is short — not a subset. No other (cell, mode) bucket among the 60 in the harvest has any shortfall (confirmed against `open37_eio_census.csv`: every other row's `n_sql` and `n_end` equal its `n_building_dirs`). The same building (`relation_5698619`) has `.sql`/`.end` present under `austin_suburban_auto`, `austin_suburban_building` and `austin_suburban_layout_assign`, and absent under `austin_suburban_fast_zone` and `austin_suburban_floor` — confirmed by direct listing. This rules out a building-level or archetype-level cause: it is specific to two (cell, mode) cells, not to the buildings inside them, and it is not a `fast_zone`/`floor`-mode-wide defect either — every other cell's `fast_zone` and `floor` directories (e.g. `la_rural_fast_zone`, `austin_centre_floor`) are fully populated per `open37_eio_census.csv`.

Neither `eplusout.eio` nor `eplusout.err` mentions `SQLite` in any of the sampled directories (checked in both a short and a healthy directory for the same building) — EnergyPlus does not log its `Output:SQLite` object status to either artifact under normal operation, so this artifact set cannot say whether the IDFs for these two batches requested `Output:SQLite` in the first place, or whether it was requested and something downstream failed to write/copy the file. Both are consistent with everything observed here.

## 6. Verdict on the three hypotheses

1. **Genuine EnergyPlus failures (the fleet's failure count is wrong).** **Not supported.** Zero of the 875 short directories are `fatal`; 874 completed with 0 Severe Errors, at a rate (99.9%) statistically indistinguishable from the healthy control (100.0%). If these were genuine per-run failures, they should show fatal or severe markers elevated over the control; they do not.

2. **Harvest-timing artifact (the harvest is wrong, the runs are fine).** **Supported for 874 of the 875**, the `austin_suburban_fast_zone` + `austin_suburban_floor` population. EnergyPlus itself reports successful completion for all of them, yet `.sql` and `.end` are both entirely absent — and absent for 100% of exactly two (cell, mode) batches, not scattered across buildings. An all-or-nothing pattern at the batch level, coincident with EnergyPlus-reported success, is the harvest-artifact signature: something about how these two batches were run or harvested differs systematically from the other 58 batches, rather than 874 individual runs each independently failing to produce results in the same way. **This artifact set cannot say which stage** — IDF-level (`Output:SQLite` never requested for these two batches) or harvest/copy-level (requested, produced, but not copied/retained) — because neither `.eio` nor `.err` records `Output:SQLite` request status, and no IDF file is retained in `HARVEST_ROOT` for these runs. Distinguishing the two would require either the IDF text used for these two batches or the harvest/copy script's own logs, neither of which is in this task's file layout.

3. **Something else.** **The single `nyc_centre_fast_zone/way_1240348353` case is not determinable from `eplusout.err`.** It is not fatal, not severe, not completed — the file simply stops mid-warning-block during input processing, before simulation begins. This is consistent with a killed or interrupted process (e.g. a timeout, an out-of-memory kill, a harvest that fetched the file while EnergyPlus was still writing it), but `.err` carries no signal that distinguishes those. Naming the cause would need the process/job log of whatever ran this specific E02 build, which is not an artifact this task has access to.

**What this measurement establishes, plainly:** the 874-directory shortfall is not a simulation-failure population — it is a batch-scoped harvest gap sitting on top of successful EnergyPlus runs, and the register's current text ("did not reach a state that writes `.sql`... or `.end`") should be corrected — these runs did reach EnergyPlus's own completion state; only the output files are missing. The one-directory exception is a genuinely different, unresolved case that this artifact cannot explain further.

## 7. T05, 2026-08-18 — discharging the two custody consequences

**Task:** T05 of `PLAN_open-52-and-four-items-2026-08-18.md`. Cause is answered (§1–6 above,
plus the director's CP-1 ruling); this section discharges the two carried-forward custody
consequences.

### 7.1 Step-1 gate — who reads `e02_corpus_inventory.csv`

```
grep -rn e02_corpus_inventory scripts/ openubem/ tests/ docs/
```

Only one hit outside docs: `scripts/analysis/e02_corpus_inventory.py:15`, and that is the
**writer** (`OUT_CSV = ...`), not a reader. A follow-up `grep -rn "e02_corpus_inventory.csv" scripts/ openubem/ tests/` confirms the same single hit. **No code anywhere in the repository parses this CSV back in as input.** Per the plan's own instruction this makes a sidecar the safe default regardless — used here rather than editing the CSV, so nothing that could ever read it is disturbed.

**Sidecar written:** `openubem/outputs/comparisons/e02_corpus_inventory.SNAPSHOT_NOTICE.md`, next to the CSV itself, so a reader browsing that directory sees it beside the file it annotates. The CSV's own bytes are untouched.

### 7.2 Step-2 — re-verified inventory-vs-disk numbers (not carried from the plan or register)

Inventory rows, read fresh from `openubem/outputs/comparisons/e02_corpus_inventory.csv` today:

```
austin_suburban,fast_zone,437,437,437,437     (n_dirs,n_err,n_eio,n_end)
austin_suburban,floor,437,437,437,437
```

Both record `n_end=437`. Live directory counts taken just now under
`C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\austin_suburban_fast_zone` and
`..._floor` (`find <dir> -maxdepth 1 -type d` for building-dir count,
`find <dir> -maxdepth 2 -iname eplusout.end`/`eplusout.sql` for output counts):

```
austin_suburban,fast_zone : n_dirs=437 n_end=0 n_sql=0
austin_suburban,floor     : n_dirs=437 n_end=0 n_sql=0
```

Building directories are intact (437/437, matching the CSV) but `eplusout.end` and
`eplusout.sql` are **0/437 in both cells today** — confirms the CSV's `n_end=437` for these
two rows is stale, exactly as the register's ruling states.

### 7.3 E02 IDF fleet corpus — checked directly, several cells

`%LOCALAPPDATA%\Temp\ubem_e02_fleet\<cell>\step3_<mode>\idfs\` sampled across 3 cells x 5
modes (`austin_suburban`, `nyc_centre`, `la_urban`; `auto`/`fast_zone`/`floor`/`building`/
`layout_assign`):

```
austin_suburban/step3_auto/idfs           : n_idf=0  dir_mtime=2026-08-17 16:21:16.18
austin_suburban/step3_fast_zone/idfs      : n_idf=0  dir_mtime=2026-08-17 16:21:16.47
austin_suburban/step3_floor/idfs          : n_idf=0  dir_mtime=2026-08-17 16:21:16.63
austin_suburban/step3_building/idfs       : n_idf=0  dir_mtime=2026-08-17 16:21:16.33
austin_suburban/step3_layout_assign/idfs  : n_idf=0  dir_mtime=2026-08-17 16:21:16.78
nyc_centre/step3_auto/idfs                : n_idf=0  dir_mtime=2026-08-17 16:21:22.33
nyc_centre/step3_fast_zone/idfs           : n_idf=0  dir_mtime=2026-08-17 16:21:22.87
nyc_centre/step3_floor/idfs               : n_idf=0  dir_mtime=2026-08-17 16:21:23.14
nyc_centre/step3_building/idfs            : n_idf=0  dir_mtime=2026-08-17 16:21:22.61
nyc_centre/step3_layout_assign/idfs       : n_idf=0  dir_mtime=2026-08-17 16:21:23.37
la_urban/step3_auto/idfs                  : n_idf=0  dir_mtime=2026-08-17 16:21:21.12
la_urban/step3_fast_zone/idfs             : n_idf=0  dir_mtime=2026-08-17 16:21:21.56
la_urban/step3_floor/idfs                 : n_idf=0  dir_mtime=2026-08-17 16:21:21.83
la_urban/step3_building/idfs              : n_idf=0  dir_mtime=2026-08-17 16:21:21.33
la_urban/step3_layout_assign/idfs         : n_idf=0  dir_mtime=2026-08-17 16:21:22.07
```

All 15 sampled `idfs/` directories are **empty**, and every directory mtime clusters within
seconds of 2026-08-17 16:21 across three unrelated cells — the single-sweep signature the
register already asserts, now confirmed directly rather than taken on trust.

### 7.4 `scratchpad/` survival — confirmed, and marked fragile

```
scratchpad/e-la-20-investigation/i03/work_part1/step3_A_as_classified_today/idfs/way_965718402.idf   1,909,240 bytes  2026-07-25 18:58
scratchpad/e-la-20-investigation/i03/work_part1/step3_A_as_classified_today/idfs/way_965718403.idf   1,909,240 bytes  2026-07-25 18:58
scratchpad/e-la-20-investigation/i03/work_part1/step3_B_as_recorded_in_t19_SmallOffice/idfs/way_965718402.idf   358,867 bytes  2026-07-25 19:05
scratchpad/e-la-20-investigation/i03/work_part1/step3_B_as_recorded_in_t19_SmallOffice/idfs/way_965718403.idf   358,867 bytes  2026-07-25 19:05
```

Confirmed present and non-empty, mtimes 2026-07-25 — three weeks before the 2026-08-17 16:21
fleet-wide deletion, and outside the deleted `ubem_e02_fleet` tree entirely (T02 of this same
plan used these same four files as its A/B diff artifact). **This is marked fragile, not
durable**: `scratchpad/` is scratch space by convention, not a protected store, is not part of
any backup or retention policy this project has established, and could be cleared by any
future cleanup pass with no warning. It should not be depended on beyond the investigation
that is currently using it.

### 7.5 Register amendment to apply

> **OPEN-53 §-section, append below the existing 2026-08-18 CP-1 ruling text:**
>
> **T05, 2026-08-18 — custody consequences discharged.** Both carried-forward consequences
> applied: (1) `e02_corpus_inventory.csv` is annotated via a sidecar,
> `openubem/outputs/comparisons/e02_corpus_inventory.SNAPSHOT_NOTICE.md` — no code in the
> repository parses the CSV back in (`grep -rn e02_corpus_inventory scripts/ openubem/ tests/
> docs/` — one hit, the writer script — confirmed 2026-08-18), so the CSV's own bytes were
> left untouched rather than edited. (2) The two falsified rows re-verified live, 2026-08-18:
> `austin_suburban,fast_zone` and `austin_suburban,floor` both record `n_end=437` in the CSV;
> both show `n_end=0, n_sql=0` on disk today (building directories intact at 437/437). The E02
> IDF fleet corpus emptiness was independently re-confirmed across 3 cells x 5 modes, all 15
> sampled `idfs/` directories empty, mtimes clustered at 2026-08-17 16:21 across cells.
>
> **Planning rule (new):** any plan depending on a `%LOCALAPPDATA%` E02 artifact
> (`ubem_e02_harvest` or `ubem_e02_fleet`) must re-verify presence on disk at planning time and
> must not cite `e02_corpus_inventory.csv`, or any other dated census, as current state. The one
> known exception is `scratchpad/e-la-20-investigation/i03/work_part1/` (4 surviving IDFs, 2 of
> the 3 `E-LA-40` buildings, both classifications, mtime 2026-07-25) — **and that exception is
> itself fragile**: `scratchpad/` is not a durable store, carries no retention guarantee, and
> should not be planned around beyond the investigation currently using it.
>
> **Disposition recommended: STAYS OPEN**, narrowed further to a pure custody risk with no
> outstanding measurement question. See §7.6 below for the argument. (Director decides.)

### 7.6 Recommended disposition — argument

**Recommend: keep OPEN-53 open, as a standing custody risk — do not close it as discharged.**

The two consequences named in the CP-1 ruling are now applied (§7.1–7.5), and there is no
remaining *measurement* question — the cause is answered, the falsified rows are documented,
and the corpus emptiness is independently re-confirmed. But "discharged" would mean the risk
itself is retired, and it is not: nothing in this pass changed *why* an external process can
delete `%LOCALAPPDATA%\Temp\ubem_e02_fleet` and `...\ubem_e02_harvest` contents without this
project's knowledge, and nothing prevents it from happening again to the same paths, to
`scratchpad/`, or to any other future artifact stored outside the repository. Closing the item
would remove the one place this recurring hazard is tracked, right after this same pass
demonstrated the hazard is still live (the fleet corpus is still empty, the two Austin cells
still show 0 `.end` on disk, exactly as before). An item whose only remaining content is "this
could happen again, here is the rule to guard against it" belongs open, not closed — closing it
converts a standing risk into a one-time incident, which understates it.

