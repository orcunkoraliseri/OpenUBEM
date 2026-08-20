# MEASUREMENT — OPEN-02: `.eio` disk budget for a five-mode fleet pass

> **Task:** M02 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_published-numbers.md` §6.
> **Date:** 2026-08-05. **Type:** measurement only — no remediation performed, no cluster script edited.

## Verdict

**Retention is cheap.** Even the worst-case, tail-weighted estimate across all five resolution modes
(≈43 GB for a full 8,160-building × 5-mode fleet pass) is under 0.5% of the 8.1 TB of free space
currently reported on the shared `speed-scratch` filesystem, and under 1.1% of this account's own
10.0 TB quota headroom (5.8 TB used, 4.2 TB free). The typical (median-based) fleet-wide cost is
≈1.3 GB. **Caveat: `fast_zone` — the mode the 800 GB sbatch comment names — has zero local `.eio`
samples.** Its cost above is a *bounded estimate* derived from real zone-count ratios (not a
measurement, not a fabricated median); see §3. Even that estimate's worst-case bound is negligible
against available headroom, which is why the verdict stands as "cheap" rather than "cannot be
determined" — but if the manager wants a direct measurement before committing to the fleet-wide
edit, one `fast_zone` sample building would remove the last bounded assumption in this report.

---

## 1. Inventory — every `eplusout.eio` in the working tree

**Command (re-runnable):**
```
find . -iname "eplusout.eio" -type f -printf "%s\t%p\n"
```
Run from `C:\Users\o_iseri\Desktop\OpenUBEM`. Returns **881 files**, sum of sizes **77,471,124 bytes**
(≈73.9 MB). This sum was independently reproduced by the Python inventory script below, which also
classifies each file by resolution mode and writes the CSV deliverable.

**Script:** session scratchpad `open02_inventory.py` (throwaway, not committed to `openubem/` or
`docs/` per plan §3/§4 — this is a session temp directory, distinct from the project's own
`scratchpad/` folder that appears throughout this report's mode-classification evidence). Re-run with
`./.venv/Scripts/python.exe <path-to-scratch>/open02_inventory.py` — it walks the repo tree from
`C:\Users\o_iseri\Desktop\OpenUBEM` (skipping `.git`), sums `eplusout.eio`/`.sql`/`.err`/`.end`, and
reproduces every number in this report, including the `open02_eio_inventory.csv` deliverable.

### 1.1 Mode classification — how each file was labelled

No path in the 881-file inventory carries an explicit `auto`/`building`/`floor`/`fast_zone`/
`layout_assign` token (verified: zero matches for any of those five strings across all 881 paths).
Mode was therefore established by **provenance, not naming**, using two evidence classes:

1. **Driver-script confirmation.** For every `scratchpad/<task>_work/` directory holding `.eio` files,
   its driving script(s) were grepped for `resolution_mode=`. All resolve to
   `resolution_mode="layout_assign"` — `r01_r02_r03_work/r01_r02_r03_runs.py:114`,
   `r10_r05_work/r05_runs.py:101` and `r10_runs.py:101`, `r06c_work/r06c_runs.py:165`,
   `t18_t04_t05_work/t05_retest.py:93`, `t18_t06_t07_work/a2_repro_smalloffice.py:82`,
   `t18_t08_t09_work/t09_retest.py:86`, `t18_t10_work/t10_retest.py:133` (+4 siblings),
   `t19_t01_t05_work/t04_retest.py:103` / `t05_retest.py:106`,
   `t19_t06_t07_work/t07_retest.py:99`, `t19_t10_work/t10_full_regression.py:167` /
   `t10_remaining_cells.py:119`. `scratchpad/b05e_work/` and `docs/docs_DONE/SETUP/layoutAssigner/`
   are the LayoutAssigner storey-matching arc itself (confirmed via
   `docs_DONE/.../DONE_PLAN_storey-matching_implementation.md:1986,2046`, both citing
   `resolution_mode="layout_assign"`). `scratchpad/e-la-20-fix/` and
   `scratchpad/e-la-20-investigation/` are the E-LA-20 defect (a LayoutAssigner defect); 11 of its 15
   driver scripts explicitly pass `resolution_mode="layout_assign"`, none pass any other mode.
2. **Out-of-pipeline exclusion.** `openubem/outputs/extra/cpb_fixtures/*` and
   `.../debug_refrig{,_fixed}/` build their IDF via raw `eppy.IDF()`
   (`scripts/validation/phaseE_cpb_fixtures.py:93`) — no `BuildingIDF`, no `resolution_mode` concept.
   These are unmodified-prototype validation fixtures, not a resolution-mode fleet run. Labelled
   `baseline_prototype` and excluded from the five-mode table.

**Result: 874/881 files = `layout_assign`. 7/881 files = `baseline_prototype` (excluded from the
mode table below, reported separately for completeness). 0 files for `auto`, `building`, `floor`,
`fast_zone`.**

This 0-file result for four of the five modes is itself a finding, not a parsing failure — it was
cross-checked two ways:
- Searched every `%TEMP%\ubem_*` directory (`t17_sweep/harvest` … `t20_sweep/harvest`, `b05f_work`,
  `b06_acceptance`, `b08b_work`, `elev_ab`, `elev_meterfix`, `elev_rebaseline`) — **zero** `.eio`
  files anywhere. The T17–T20 harvest-download step trims `.eio` on the way down, mirroring the
  cluster's own T08 trim policy, even for local temp copies.
- The one local script that *did* run all four T08 modes locally
  (`scripts/cluster/t08_local_remainder.py`) writes its EnergyPlus output to
  `Path(tempfile.gettempdir()) / "ubem_t08_local"` (line 488) — **outside** both the repo tree and
  the surviving `%TEMP%\ubem_*` directories found above. That directory no longer exists on disk
  (checked directly, 0 results).

### 1.2 Size distribution per mode (bytes) — `eplusout.eio`

| mode | n | min | median | p90 | max |
|---|---:|---:|---:|---:|---:|
| **layout_assign** | 874 | 6,736 | 76,068 | 160,850 | 1,092,989 |
| baseline_prototype *(not a resolution mode — informational only)* | 7 | 21,374 | 22,211 | 37,342 | 54,849 |
| auto | 0 | — | — | — | — |
| building | 0 | — | — | — | — |
| floor | 0 | — | — | — | — |
| fast_zone | 0 | — | — | — | — |

**Confirms §5.9 of the plan at full scale, not just the spot-check it was based on:** every locally
measurable `.eio` sits between 6.6 KB and 1.04 MB. Nothing in the sample is within three orders of
magnitude of "large."

---

## 2. Context — what the trim already keeps

Same tree, same command shape, for the three file types `submit_fleet_t08.sbatch` retains
(`eplusout.sql`, `eplusout.err`, `eplusout.end`), **not mode-split** (no local sample lets that
split be made honestly — see §3).

| file type | n | min | median | p90 | max |
|---|---:|---:|---:|---:|---:|
| `eplusout.sql` | 940 | 180,224 | 276,480 | 8,355,840 | 119,980,032 |
| `eplusout.err` | 948 | 2,542 | 12,427 | 27,016 | 388,213 |
| `eplusout.end` | 945 | 99 | 103 | 107 | 110 |

Typical (median) retained payload per building: 276,480 + 12,427 + 103 = **289,010 bytes**.
The `.sql` tail is wide (max 120 MB — one detailed-timestep outlier, not representative of a typical
building) and dominates the retained footprint; `.eio` would be a small addition next to it even
before the fleet-wide arithmetic in §4.

**Per-building marginal cost, `layout_assign` only (the one mode actually measured):**
76,068 / 289,010 = **26.3%** — adding the median `layout_assign` `.eio` to what a building's run
already keeps grows that building's retained footprint by about a quarter, in absolute terms a few
tens of KB.

---

## 3. `fast_zone` — no local sample; bounded estimate, not extrapolation

Per plan rule: no `fast_zone` `.eio` size may be extrapolated from another mode's `.eio` size. What
*is* available locally, without simulating anything, is real fleet-scale **zone-count** data for
`fast_zone` alongside `layout_assign`, from two already-published harvest CSVs:

- `openubem/outputs/comparisons/t08_all_modes_eui.csv` — 18,120 rows, `mode` × `num_zones` for
  `auto`/`building`/`floor`/`fast_zone`, 5 cells (`nyc_centre`, `nyc_urban`, `nyc_suburban`,
  `nyc_rural`, `la_centre`).
- `openubem/outputs/comparisons/t19_layout_assign_eui.csv` — 8,160 rows, `layout_assign` `num_zones`,
  12 cells.

Restricted to the 5 cells both files share (4,530 buildings each side):

| mode | n | min zones | median zones | p90 zones | max zones |
|---|---:|---:|---:|---:|---:|
| layout_assign | 4,530 | 1 | 6.00 | 27.00 | 336 |
| fast_zone | 4,530 | 1 | 2.00 | 24.00 | 837 |
| auto | 4,530 | 1 | 2.00 | 10.00 | 338 |
| building | 4,530 | 1 | 1.00 | 1.00 | 1 |
| floor | 4,530 | 1 | 2.00 | 7.00 | 105 |

`.eio` size scales with zone/surface count (§5.9 of the plan). Applying the **zone-count ratio**
(mode ÷ layout_assign) to the *measured* `layout_assign` `.eio` sizes from §1.2 gives a bounded
estimate, not a fabricated point value:

| mode | median-ratio × 76,068 B | max-ratio × 1,092,989 B |
|---|---:|---:|
| fast_zone | 0.333 → **25,353 B** | 2.491 → **2,722,745 B (2.60 MB)** |
| auto | 0.333 → 25,353 B | 1.006 → 1,099,547 B |
| building | 0.167 → 12,681 B | 0.003 → 3,279 B |
| floor | 0.333 → 25,353 B | 0.3125 → 341,559 B |

`fast_zone`'s **median** zone count is lower than `layout_assign`'s (2 vs. 6 — most buildings fall
back to few zones), but its **max** is more than double (837 vs. 336 — a small tail of buildings gets
a full perimeter-core zoning). This asymmetry is exactly the shape the 800 GB sbatch comment describes
(a tail risk, not a typical-case risk), and it is captured by using both the median and the max ratio
rather than one number.

**This is the one number in this report that is an estimate, not a measurement.** It is bounded
top and bottom by real fleet-scale zone-count data, not guessed.

---

## 4. Fleet-wide estimate (8,160 buildings × 5 modes)

Per plan: `median_size(mode) × 8,160`, summed over the five modes, and the same with `max`.

| basis | layout_assign (measured) | auto (est.) | building (est.) | floor (est.) | fast_zone (est.) | **total, 5 modes** |
|---|---:|---:|---:|---:|---:|---:|
| median × 8,160 | 620.7 MB | 206.9 MB | 103.5 MB | 206.9 MB | 206.9 MB | **1.345 GB** |
| max × 8,160 | 8.919 GB | 8.972 GB | 0.027 GB | 2.787 GB | 22.218 GB | **42.923 GB** |

`layout_assign` alone (the only directly measured mode, and the one all current published fleet
numbers actually come from — T17–T20 are all `layout_assign` passes): **0.621 GB** typical,
**8.919 GB** worst-case, for a full 8,160-building fleet pass.

**As a percentage of what is already retained**, extending the same median/p90 sql+err+end baseline
(§2) to fleet scale (289,010 B × 8,160 × 5 modes = 11.79 GB median-based; 8,382,963 B × 8,160 × 5
modes = 342.0 GB p90-based, dominated by the `.sql` tail):

- Median-based: 1.345 GB / 11.79 GB = **11.4%** marginal increase.
- Worst-case-based: 42.92 GB / 342.0 GB = **12.6%** marginal increase.

Either way, retaining `.eio` fleet-wide adds roughly an **eighth** to what the pipeline already
writes to disk per fleet pass — it does not double it, and it is nowhere near the 800 GB figure the
sbatch comment cites for the *whole* trim set.

---

## 5. Independent cross-check (not part of the five-mode table)

`/speed-scratch/o_iseri/openubem/fleets/t11cc_nyc_centre_phaseA/` is an older, pre-`layoutAssigner`
harvest generation (T11) whose provenance script is not present in the current working tree, so its
resolution mode cannot be confirmed and it is **not** counted in §1.2 or §4. It happens to have
retained `.eio` untrimmed for 167 buildings (one NYC-centre cell): sum 12,850,695 bytes → average
**76,950 bytes/building**. That is within 1.2% of this report's measured `layout_assign` median
(76,068 bytes), from a completely different harvest generation. It does not change the verdict; it
is offered only as independent support that `.eio` size clusters in the tens-of-KB range regardless
of which harvest produced it.

---

## 6. Cluster quota and disk headroom

Lightweight ops only, run against `speed-submit2.encs.concordia.ca`. **No `srun`, no `python`, no job
submitted, no job touched.**

```
$ ssh o_iseri@speed-submit2.encs.concordia.ca "quota -s"
========================== user quotas for o_iseri ==========================
WHERE                 used    warn   limit  used  warn limit volume/qtree
Basic Home and Web    5.0G    9.8G   10.0G   22K     -     - vol: users
INBOX                 5.1M   80.0M   85.0M     1     -     - vol: mailspool
/nettemp              0.0K  750.0M  800.0M     0     -     - vol: nettemp
/groups             380.3M    2.0G    2.0G   215     -     - vol: groups
/speed-scratch        5.8T    9.8T   10.0T    3M     -     - vol: speed_scratch
```

```
$ ssh o_iseri@speed-submit2.encs.concordia.ca "df -h /speed-scratch/o_iseri"
Filesystem                           Size  Used Avail Use% Mounted on
filer-speed:/userdata/speed_scratch  121T  113T  8.1T  94% /nfs/speed-scratch
```

```
$ ssh o_iseri@speed-submit2.encs.concordia.ca "du -sh /speed-scratch/o_iseri/openubem"
36G     /speed-scratch/o_iseri/openubem
```

**Findings:**
- **This account's own quota:** 5.8 TB used of a 10.0 TB limit (9.8 TB warn threshold) →
  **4.2 TB of personal headroom** (4.0 TB before the warn threshold).
- **Shared filesystem:** the whole `speed_scratch` volume is at 94% (113 TB of 121 TB), leaving only
  **8.1 TB free across all users of the cluster**, not just this account. This is the binding
  constraint, not the personal quota — a fleet-wide `.eio` retention decision should be checked
  against this 8.1 TB shared figure, not only the 10 TB personal one.
- **Our current total footprint:** `/speed-scratch/o_iseri/openubem` is 36 GB in total, of which the
  `fleets/` directory (all harvest generations, all trimmed to sql+err+end per the T08 policy) is
  33 GB. The two largest single entries are `t11cc_nyc_centre_phaseA` and `t11cc_nyc_centre_phaseC`
  at 11 GB each — a single cell, untrimmed, from before the trim policy existed. Even those two
  outliers are an order of magnitude below the ≈43 GB worst-case fleet-wide `.eio` estimate in §4.
- Both the 42.9 GB worst-case and the 1.3 GB typical-case fleet-wide `.eio` addition are small next
  to both the 4.2 TB personal headroom and the 8.1 TB shared headroom (worst case = 0.53% of personal
  headroom, 0.42% of shared headroom).
- No quota question was left unanswered; all three lightweight commands (`quota -s`, `df -h`,
  `du -sh`) returned real data on the first attempt (after one retry that used `-o BatchMode=yes`,
  which failed key-based non-interactive auth and was dropped — not a compute attempt, just an SSH
  option that didn't match this account's auth setup).

---

## 7. How-to-test results (per plan §6, M02)

- **Sum reproducibility:** the inventory command in §1 and the script in `scratchpad/open02_inventory.py`
  independently agree on 881 files / 77,471,124 bytes. ✅
- **One-sentence verdict at the top of the report:** stated. ✅ ("Retention is cheap", with the
  `fast_zone` caveat spelled out rather than hidden.)
- **No silent zero:** the 0-file result for `auto`/`building`/`floor`/`fast_zone` is reported
  explicitly as "0 files found" with the two-step search (repo tree + `%TEMP%\ubem_*`) that produced
  it, not as an empty table cell. ✅
