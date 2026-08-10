# MEASUREMENT — R05 Speed calibration probe: CP-R2 readout

**Date:** 2026-08-09
**Author:** CP-R2 readout session (measurement/reporting only — no code changes, no new Speed submissions)
**Scope:** Read the ten sbatch arrays submitted 2026-08-09 20:29:21 (`la_rural` 149/mode, `nyc_rural`
198/mode, five modes: `auto`, `building`, `floor`, `layout_assign`, `fast_zone`; 1,735 simulations
total). All ten arrays had drained before this readout began (`squeue -u o_iseri` confirmed empty).

**Remote directories actually read** (via read-only `ssh`/`sacct`/`find`, never `srun`/`python` on the
login node):
- `sacct -j 1174659,1174676,1174704,1174735,1174791,1174813,1174837,1174865,1174924,1174959` (all ten
  job roots, 1,735 array tasks × 3 sacct step-rows each = 5,205 raw lines; full text in
  `r05_sacct_raw.txt` alongside this file).
- `/speed-scratch/o_iseri/fleets/r05probe_la_rural_{auto,building,floor,layout_assign,fast_zone}/out/`
  — 149 subdirectories each, confirmed by remote `ls`/`find` before and independently of harvest.
- `/speed-scratch/o_iseri/fleets/r05probe_nyc_rural_{auto,building,floor,layout_assign,fast_zone}/out/`
  — 198 subdirectories each.
- Fetched (via `tar` over `ssh`, the allowed pattern) into
  `%TEMP%\ubem_r05_harvest\<cell>_<mode>\<stem>\{eplusout.sql,eplusout.err,eplusout.end}` — 149 or 198
  buildings per (cell, mode), matching `fleet.lst` counts exactly in all ten cases.

**How the harvest was done.** `scripts/cluster/t08_harvest_results.py` hard-codes `_FLEET_TAG = "t08"`
(line 42) and builds remote paths from it (line 111) — this probe's remote dirs are tagged `r05probe`,
so a blind harvest would have read nothing. Per the mandate, a driver script in scratchpad
(`r05_harvest.py`, not committed, not under `docs/`) imported `t08_harvest_results.py` as a library and
set `t08_harvest_results._FLEET_TAG = "r05probe"` before calling `fetch_mode_cell` / `parse_cell_mode`.
**The repo file `scripts/cluster/t08_harvest_results.py` was not edited** — `git status` shows it clean.

---

## 1. Timing and memory table

Per-(cell, mode) array, from `sacct -j <jobid> --format=JobID,State,Submit,Start,End,Elapsed,TotalCPU,MaxRSS,ReqMem,ExitCode -P -n`.
`wall` = array wall-clock (last task `End` − first task `Start`, i.e. real elapsed time including the
`--array=...%16` concurrency cap). `cpu` = sum of per-task `TotalCPU` (the `.batch` step, which is where
MaxRSS/TotalCPU actually live in `sacct`'s three-line-per-task output). `mean`/`median` cost are
per-building **core-seconds** (`TotalCPU` divided across the array). `ReqMem` was uniformly `6G` on all
1,735 top-level task rows — verified, no variation.

| cell / mode | n | COMPLETED | FAILED | TIMEOUT | OOM | CANCELLED | wall (min) | total CPU (core-min) | mean core-s/bldg | median core-s/bldg | MaxRSS max (MB) | MaxRSS median (MB)\* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| la_rural / auto | 149 | 142 | 7 | 0 | 0 | 0 | 4.42 | 56.96 | 22.94 | 12.02 | 2812.4 | 0.48 |
| la_rural / building | 149 | 149 | 0 | 0 | 0 | 0 | 1.28 | 16.01 | 6.45 | 5.72 | 46.1 | 0.42 |
| la_rural / floor | 149 | 142 | 7 | 0 | 0 | 0 | 2.15 | 26.50 | 10.67 | 8.43 | 435.9 | 0.46 |
| la_rural / layout_assign | 149 | 149 | 0 | 0 | 0 | 0 | 9.02 | 75.80 | 30.52 | 11.28 | 218.6 | 0.78 |
| la_rural / fast_zone | 149 | 139 | 10 | 0 | 0 | 0 | 4.57 | 51.89 | 20.89 | 10.10 | 2809.7 | 0.50 |
| nyc_rural / auto | 198 | 198 | 0 | 0 | 0 | 0 | 2.03 | 22.85 | 6.92 | 5.68 | 2.0 | 0.43 |
| nyc_rural / building | 198 | 198 | 0 | 0 | 0 | 0 | 2.82 | 26.01 | 7.88 | 5.87 | 2.1 | 0.43 |
| nyc_rural / floor | 198 | 198 | 0 | 0 | 0 | 0 | 1.88 | 20.74 | 6.29 | 5.60 | 2.0 | 0.43 |
| nyc_rural / layout_assign | 198 | 195 | 3 | 0 | 0 | 0 | 10.88 | 120.83 | 36.62 | 10.75 | 375.7 | 0.78 |
| nyc_rural / fast_zone | 198 | 198 | 0 | 0 | 0 | 0 | 3.35 | 35.64 | 10.80 | 6.07 | 1188.9 | 0.43 |

**Task-state census across all 1,735 tasks (all 5,205 sacct rows, grepped directly):** `COMPLETED` and
`FAILED` are the **only** states that occur. Zero `TIMEOUT`, zero `OUT_OF_MEMORY`, zero `CANCELLED`,
anywhere. (`grep -c TIMEOUT/OOM/CANCELLED` on the full raw sacct text all return 0; `awk` over the
`State` column shows exactly two unique values: `COMPLETED`, `FAILED`.)

\* **MaxRSS median caveat — read before using it.** The per-task median MaxRSS is misleadingly low
(sub-1 MB) for every mode. This is **not** a real memory floor; it is a sampling artifact: most tasks
finish in under 30–60 s (see `elapsed`), and `sacct`'s periodic RSS poller frequently misses the peak on
short-lived batch steps, recording only a near-zero snapshot taken before the child process ramped up.
Direct inspection of the raw batch-step rows (`r05_sacct_raw.txt`) confirms real, substantial RSS values
(tens to thousands of MB) on the tasks that ran long enough to be sampled — e.g. `la_rural_auto` task 22
shows `2879916K` (2.75 GB) over a 2 min 27 s run. **Treat `MaxRSS max` as the reliable per-mode ceiling
estimate; do not trust the median as a "typical" figure.**

Total probe cost, all ten arrays combined: **27,194 core-seconds = 453.2 core-minutes = 7.55
core-hours** for 1,735 simulations (mean 15.67 core-s/building-mode across the whole probe).

---

## 2. The two pre-registered risks — resolved

**Risk 1 — the 2-hour wall (`--time=02:00:00`) against `fast_zone`'s worst buildings: CLEAN, zero
TIMEOUT.** No task in any of the ten arrays — including `fast_zone`, the mode expected to be closest to
the wall — ended `TIMEOUT`. The longest single task observed was `la_rural_layout_assign`'s worst
building at ~333 s (5.6 min) elapsed, roughly 4.6% of the 2-hour allowance. The pre-registered concern
(cluster-core-speed-scaled local worst-case landing "on or past the two-hour wall") **did not
materialize on real cluster nodes**; the local extrapolation that raised the concern was itself wrong by
a wide margin, consistent with the ≈10× miss that motivated this whole probe.

**Risk 2 — `--mem=6G` per task, the ceiling whose local analogue killed C02 with a `fast_zone`-specific
MemoryError: CLEAN, zero OOM, and 6G reads as comfortable.** Highest MaxRSS observed anywhere in the
probe: **2,812.4 MB** (`la_rural_auto`, task 22) and **2,809.7 MB** (`la_rural_fast_zone`, same building
by index), both ≈47% of the 6 GB request — never within killing distance of the cap, and `sacct` reports
zero `OUT_OF_MEMORY` states. Both of those high-RSS tasks are `FAILED` for reasons unrelated to memory
(see §3, `has_fatal` cross-check below) — high memory use correlates with model-physics failure, not
cluster-memory failure. C02's local MemoryError was a **different** hazard (16 IDF models held resident
simultaneously by a `N_JOBS`-wide local process pool); one-building-per-task on Speed removes that
failure mode entirely, as expected. Caveat: the median-MaxRSS sampling gap in §1 means genuinely short,
low-memory tasks may be under-measured, but the **maximum** observed value — which is what a memory cap
must be sized against — is trustworthy because it comes from tasks that ran long enough to be sampled.
6G is not tight for `la_rural`/`nyc_rural`; whether it holds for denser, larger-building cells (centre,
urban) is **unmeasured** by this probe (see §4).

---

## 3. Correctness checks

**(a) `.eio` present and non-empty for every successful building — R01's proof on real hardware: PASS,
but not via the CSV harvest.** `t08_harvest_results.py`'s `fetch_mode_cell()` (line ~131) builds its tar
command as `tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end` — it **does not
fetch `.eio` at all**. This is a pre-existing gap in the harvest script (not something this session
introduced or is authorized to fix), and it means the harvest CSV's local-file check for `.eio` reads
`0` for every mode — that `0` is "read the wrong path", not "0 retained on Speed." Verified instead by
direct remote `find` against the actual output directories:

```
find /speed-scratch/o_iseri/fleets/r05probe_<cell>_<mode>/out -maxdepth 2 -name eplusout.eio -size +0c | wc -l
```

| mode | la_rural (of 149) | nyc_rural (of 198) |
|---|---:|---:|
| auto | 149 | 198 |
| building | 149 | 198 |
| floor | 149 | 198 |
| layout_assign | 149 | 198 |
| fast_zone | 149 | 198 |

**100% of all 1,735 tasks retained a non-empty `.eio`** — including the 27 `FAILED` tasks, because
`.eio` is written during EnergyPlus's input-processing phase, before the point where these particular
buildings' solves diverge. Sampled directly with `ls -la` on one building
(`r05probe_la_rural_auto/out/way_222366800/`): `eplusout.eio` present at 21,190 bytes alongside
`eplusout.sql`, `.end`, `.err`, `.shd`, `sqlite.err`, `task.rc`. R01's template fix holds on real cluster
hardware.

**(b) `vintage_standard` populated with a plausible distribution — R03/R07 on real hardware: PASS.**
Sourced from the probe's local `03_manifest.parquet` files (which do carry the `vintage_standard`
column per R07 — confirmed present in all ten manifests, 149 or 198 rows each) and joined through
`t08_harvest_results.parse_cell_mode`'s existing manifest-read path (unmodified). Distribution over all
1,735 rows:

| vintage_standard | count |
|---|---:|
| `DOERefPre1980` | 915 |
| `90.1-2013` | 750 |
| `90.1-2007` | 70 |

Three distinct, plausible vintage tokens, no blanks, no fabricated defaults — matches R07's intended
behavior end-to-end on a real cluster run, not just its unit test.

**(c) `has_fatal` via the new regex `re.search(r"\*\*\s+Fatal\s+\*\*", err)` — R02 on real hardware:
PASS, and it cross-validates against `sacct`.** Count of buildings with a real Fatal, per (cell, mode):

| cell | mode | has_fatal count |
|---|---|---:|
| la_rural | auto | 7 |
| la_rural | building | 0 |
| la_rural | floor | 7 |
| la_rural | layout_assign | 0 |
| la_rural | fast_zone | 10 |
| nyc_rural | auto | 0 |
| nyc_rural | building | 0 |
| nyc_rural | floor | 0 |
| nyc_rural | layout_assign | 3 |
| nyc_rural | fast_zone | 0 |

**Total: 27 buildings with a genuine Fatal**, and this figure matches the `sacct` `FAILED` task census
in §1 **exactly**, per array (7/0/7/0/10 for `la_rural`, 0/0/0/3/0 for `nyc_rural`) — every `FAILED`
sacct task corresponds to a real EnergyPlus Fatal, and every `COMPLETED` task has zero. Spot-checked one:
`la_rural/auto` task 22 (`way_472960972`) — its `eplusout.err` ends with `EnergyPlus
Terminated--Fatal Error Detected. 745 Warning; 24 Severe Errors`, triggered by `Temperature (high) out
of bounds` (a divergent zone-solve, i.e. a model-physics fatal — not an infrastructure failure, not
memory-related, not a timeout). The 7 `la_rural` failures recur across `auto`/`floor`/`fast_zone`
(overlapping building set, `fast_zone` adds 3 more), and `nyc_rural/layout_assign`'s 3 failures are a
disjoint set of buildings. **Report empty as empty: this is 27 real failures, not 0.**

**(d) `city` resolving correctly, not silently falling back to the cell name: PASS.**
`results.groupby("cell")["city"].unique()` → `la_rural → ['LA']`, `nyc_rural → ['NYC']`. Neither column
shows the cell string itself (`la_rural`, `nyc_rural`) as the city value, which is the failure mode
`t08_local_remainder.py:423` has. `CITY_OF` resolved correctly for both cells in this probe.

---

## 4. Fleet-cost RANGE — not a single number

🔴 **This section is a weak extrapolation and is labeled as such.** The probe measured **2 of 12 cells**,
both `rural` — the least dense, smallest-building tier. Per-building-mode cost varies by **5.8× within
this probe alone**: `nyc_rural/floor` mean 6.29 core-s/building vs. `nyc_rural/layout_assign` mean 36.62
core-s/building. That spread is *before* accounting for cell density at all (both are the same `rural`
tier); the manager's pre-registered concern — `nyc_centre/auto` ≈110 core-s/building against
`la_rural`'s ≈25.7 (this probe's own measured `la_rural/auto` mean lands at 22.94, closely consistent
with that prior estimate) — is about a **different, unmeasured axis**: cell density. `nyc_centre`,
`la_centre`, `austin_centre` and the `urban`/`suburban` tiers of all three cities are **not in this
probe** and their cost is **undetermined**.

Combining both spreads (this probe's mode spread × the cited density spread) gives a defensible range,
not a point estimate:

- **Measured floor** (this probe's cheapest mode-cell, `nyc_rural/floor`): **6.3 core-s/building-mode**.
- **Measured ceiling** (this probe's most expensive mode-cell, `nyc_rural/layout_assign`): **36.6
  core-s/building-mode**.
- **External reference point, not re-verified here**: `nyc_centre/auto` ≈110 core-s/building (cited in
  the plan doc from an earlier scoping run) — **≈3–17× above this probe's measured range**, depending on
  which mode-cell it is compared against.

Applying the probe's own measured range (6.3–36.6 core-s) to the full fleet pass (8,160 buildings × 5
modes = 40,800 simulations) gives **71 to 415 core-hours** — but this is very likely a **lower bound**,
since it excludes every centre/urban/suburban cell where per-building cost is known (from the external
reference) to run several times higher. **Do not read 71–415 core-hours as the fleet estimate; read it
as the floor of the true range, with the true ceiling undetermined by this probe.** The only way to
narrow this range is to measure at least one non-rural cell directly — this probe deliberately did not,
per its whole-cells-only, two-cheap-cells design (OPEN-34).

---

## 5. Undetermined / evidence-is-silent

- **Cost for centre/urban/suburban density tiers** — genuinely undetermined by this probe; the cited
  110 core-s/building figure for `nyc_centre/auto` is an external, unverified-in-this-session number.
- **Whether `--time=02:00:00` holds for a `fast_zone` task on a centre-density cell** — this probe's
  `la_rural/fast_zone` array (its worst-case mode) took only 4.57 min wall-clock end-to-end (274 s) with
  no single task above ~134 s, but centre-cell buildings (more zones, denser context) were not tested.
- **Whether `--mem=6G` holds for centre-density cells** — same caveat; 2.8 GB peak here says nothing
  about a building with, e.g., 5–10× the zone count.
- **Root cause of the 27 Fatal failures** — confirmed to be model-physics divergence (temperature
  out-of-bounds) on the one building sampled, not infrastructure. Whether all 27 share that root cause,
  or whether some are a distinct defect, was **not** exhaustively checked (out of this mandate's scope —
  measurement of runtime/memory/correctness plumbing, not model debugging).

---

## Appendix — raw artifacts

- `r05_sacct_raw.txt` (this folder) — full `sacct -j <10 job IDs> --format=JobID,JobName,State,Submit,Start,End,Elapsed,TotalCPU,MaxRSS,ReqMem,ExitCode -P -n` output, 5,205 lines, the entire basis for §1–§2.
- `r05_probe_all_buildings.csv` (this folder) — per-building harvest output (1,735 rows: cell, mode, osm_id, archetype_id, status, has_fatal, vintage_standard, zoning_strategy, num_zones), the basis for §3.
- `r05_fetch_report.csv` (this folder) — per-(cell,mode) fetch counts (fleet.lst size vs. files actually extracted), confirming 149/149 and 198/198 for all ten arrays.
- Remote paths read (read-only `ssh`/`find`, no compute): `/speed-scratch/o_iseri/fleets/r05probe_{la_rural,nyc_rural}_{auto,building,floor,layout_assign,fast_zone}/out/`.
- Local fetch destination: `%TEMP%\ubem_r05_harvest\<cell>_<mode>\<stem>\{eplusout.sql,eplusout.err,eplusout.end}`.
- Job IDs / submission record: `%TEMP%\ubem_r05_probe\r05_job_ids.json`.
- `scripts/cluster/t08_harvest_results.py` — read for the harvest logic, **not edited** (`_FLEET_TAG`
  override applied only in a scratchpad driver script, per the mandate).
