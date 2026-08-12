# MEASUREMENT — OPEN-39 orphaned disk / task.rc test, OPEN-40 third-submission trace

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/PLAN_e02-audit-and-closure.md`, T05.
> **Script:** `scripts/analysis/e02_cluster_readonly_audit.py`
> **Date:** 2026-08-11. Read-only throughout: `ls`, `du`, `find`, `sacct` via `_ssh()`
> (`scripts/cluster/t08_harvest_results.py:102-108`). No `sbatch`, `srun`, `ssh ... python`, or
> deletions. Total remote wall-clock used: **13.8 s** (cap was 40 min).

## Connectivity proof (before any batch)

```
_ssh('hostname')                                       -> 'speed-submit1.encs.concordia.ca'
_ssh('du -sh /speed-scratch/o_iseri/fleets/e02_nyc_centre_auto') -> '872M  .../e02_nyc_centre_auto'
```

Both succeeded on the first attempt. No retry/backoff was needed anywhere in this task.

---

## (a) OPEN-39 — orphaned disk from `set -e`, and the `task.rc` completion-test question

### (a)(ii) — does any script use `task.rc` presence as a completion test?

Grepped every `.py` / `.sbatch` / `.sh` under `scripts/` for `task.rc`. **15 references, in 9 files**
(excluding this audit script itself). Every one classified:

| path:line | classification |
|---|---|
| `scripts/cluster/submit_fleet.sbatch:53` | WRITE — `echo $RC > "${OUTDIR}/task.rc"` |
| `scripts/cluster/submit_fleet_t08.sbatch:58` | WRITE — `echo $RC > "${OUTDIR}/task.rc"` |
| `scripts/cluster/submit_fleet_t08.sbatch:81` | comment only (file-retention list) |
| `scripts/cluster/t07b_run_auto_refit_local.py:206` | WRITE — `(outdir / "task.rc").write_text(str(rc))` |
| `scripts/cluster/t07_run_fast_zone_local.py:55` | WRITE — `(outdir / "task.rc").write_text(str(rc))` |
| `scripts/cluster/t08_local_remainder.py:85` | `RETAIN_FILENAMES` tuple — a trim-keep list, not a completion test |
| `scripts/cluster/t08_local_remainder.py:234` | WRITE — `(outdir / "task.rc").write_text(str(rc))` |
| `scripts/validation/v12_*.py` (7 files) | WRITE — `echo $RC > "${{OUTDIR}}/task.rc"` (repair/recovery sbatch templates) |
| `scripts/validation/_repair_281346738.sbatch_template:27` | WRITE — `echo $RC > "${OUTDIR}/task.rc"` |

**Verdict: no script anywhere under `scripts/` reads `task.rc`'s presence or content to decide
whether a task is done.** Every harvest/parse script that determines completion status
(`t07_harvest_results.py`, `t08_harvest_results.py`, `t17`-`t20_harvest_layout_assign.py`,
`elevator_ab_harvest.py`) does it the same way — `status = "success" if eplusout.end exists and
contains "EnergyPlus Completed Successfully"` (e.g. `t08_harvest_results.py:241-243`) — never via
`task.rc`. `task.rc` appears only on the write side (the sbatch template) and in one file-retention
list. OPEN-39's standing rule ("`task.rc`'s presence must never be used as a completion test") has
nothing to correct against in this codebase today — it is confirmed as a **preventive** rule, not one
catching a live bug.

### Existence control (mandatory) — one successful vs. one failed task, same array

`e02_la_centre_auto`, task `way_319507579` (failed, in T02's OPEN-41 census) vs. task
`relation_12292681` (succeeded, picked as the first non-failing, non-fatal directory in the same
array):

| | failed (`way_319507579`) | succeeded (`relation_12292681`) |
|---|---:|---:|
| `du -sh` | **42M** | **340K** |
| `task.rc` present | **No** | **Yes** (`-rw-rw---- 1 ... 2 ... task.rc`, 2 bytes) |
| files present | `Energy+.idd`, `in.idf`, `expanded.idf`, `eplusout.{audit,bnd,dbg,eio,end,err,eso,mdd,mtd,mtr,rdd,shd,sql}`, `eplusssz.csv`, `epluszsz.csv`, `sqlite.err` — **the full untrimmed set, nothing deleted** | `eplusout.{eio,end,err,shd,sql}`, `sqlite.err`, `task.rc` — **trimmed** |

Both the size difference and the `task.rc` presence difference are exactly as OPEN-39 predicts: the
failed task's directory is untrimmed (all of `Energy+.idd`/`in.idf`/`expanded.idf`/the size/schedule
CSVs survive) and carries no `task.rc`, because `set -e` (line 18) killed the script at line 56 before
line 57-58 (`RC=$?` / the `task.rc` write) or the trim block (63-80) ever ran. **OPEN-39's mechanism
fires exactly as described** — this is not the "both have `task.rc`" outcome that the plan flagged as
a would-be finding.

### (a)(i) — total orphaned size, 45 known-failed E02 tasks vs. a same-array successful sample

Batched `du -sh` over all 45 failed task directories (T02's 44-row OPEN-41 census +
`nyc_centre/fast_zone/way_1240348353`, the missing-`.end` 45th failure, reconfirmed locally against
the corpus before use) and over 11 successful directories, one per distinct `(cell, mode)` array that
carries a failure:

| | n | total | mean/dir |
|---|---:|---:|---:|
| **Failed** | 45 (45/45 parsed) | **2,239,488 KB ≈ 2,187.0 MB ≈ 2.14 GB** | 49,766 KB ≈ 48.6 MB |
| **Succeeded (matched sample)** | 11 (11/11 parsed) | 4,944 KB ≈ 4.8 MB | 449 KB |

Ratio ≈ **111×**. The per-directory mean (≈48.6 MB) matches OPEN-39's own write-up almost exactly
("~40 MB combined per the trim-block comment's own budget reasoning"). **Total orphaned disk from
E02's 45 failures alone: ≈2.14 GB.**

### (a)(i) extension — other fleets, by listing + sampling (not a full walk)

`ls -1 /speed-scratch/o_iseri/fleets/` returned **278 entries**. 60 are the E02 arrays (measured
above, in full). The remaining 218 group into 19 non-`e02_` tag families: `austin`, `elev`, `elevab`,
`la`, `nyc`, `phaseC`, `phaseD`, `phaseD2`, `phaseE`, `r05probe`, `t07`, `t08`, `t09cc`, `t14`, `t14h`,
`t17`, `t18`, `t19`, `t20`.

Sampled one fleet per tag (19 fleets), up to 3 task directories each, checked `du -sh` and `task.rc`
presence. 55 of 56 sampled directories had `task.rc` present (trimmed, small). **One did not:**

```
t17_austin_centre_layout_assign/out/relation_13781131   6.5M   TASKRC_ABSENT
  (siblings in the same array: relation_7480583 = 492K/PRESENT, way_1008727466 = 236K/PRESENT)
```

This is independent confirmation, in a fleet run through the same "T08 variant" sbatch template
(`t17_*` — one of the `layout_assign` harvest generations, per OPEN-39's own claim that the defect
"replicates across every fleet this template has run, T08 through T20"), of the identical
size-inflation + missing-`task.rc` signature seen in E02. **OPEN-39 is not E02-specific; this sample
reproduces it in a different fleet generation.** No attempt was made to size all 218 non-E02
directories (out of scope: "by sampling, not by walking every fleet").

`austin_centre` and `la_centre` (bare cell names, no tag prefix, oldest-generation directories) had
empty `out/` listings under this test — they predate the `out/<stem>` layout and are out of scope for
this defect, which is specific to the T08-derived sbatch template.

### Methodological finding (not part of OPEN-39/40, logged for the record)

While building the multi-target batch commands for this task, a **remote command length limit was
found empirically**: a single `_ssh()` command string of **8,192 characters or more** returns
`Unmatched '.` (a `tcsh` quote-parse error) and produces **no useful output**, even when the payload
itself contains zero quote characters (reproduced with a quote-free `echo x; echo x; ...` payload:
7,808/7,904/8,008/8,104 chars all succeed; 8,192/8,200/8,208 all fail identically). This is not a
Python-side quoting bug — it reproduces with balanced quotes and short ones alike — and is not
previously documented anywhere in this project. It silently produced a 13-character error output in
this task's first draft (caught by inspecting the raw output rather than trusting a nonzero-length
return). **Recommendation for the register: any future script building a multi-target `_ssh()` command
should chunk below ~7,500 chars.** This audit's own script now does so
(`REMOTE_CMD_SAFE_LEN = 7500` in `e02_cluster_readonly_audit.py`). Left for the director to decide
whether this becomes its own item (candidate: OPEN-42) or a note appended to `_ssh()`'s docstring.

---

## (b) OPEN-40 — tracing the eight-array third submission

### Range control (mandatory) — verified from `sacct`, not from the plan document

`sacct -j 1177095,1177838,1177839,1177840,1177841,1177875,1178313,1178538 -X -P
--format=JobID,JobName,Submit,State,WorkDir,User` returned one row per array **task** (job arrays do
not collapse under `-X`), 1,644 rows total. Arithmetic per array ID against the two documented wave
ranges (wave 1 `1176411`-`1176599`, wave 2 `1198104`-`1200571`):

| Job ID | in wave 1? | in wave 2? | outside both? |
|---:|:---:|:---:|:---:|
| 1177095 | No | No | **Yes** |
| 1177838 | No | No | **Yes** |
| 1177839 | No | No | **Yes** |
| 1177840 | No | No | **Yes** |
| 1177841 | No | No | **Yes** |
| 1177875 | No | No | **Yes** |
| 1178313 | No | No | **Yes** |
| 1178538 | No | No | **Yes** |

All eight confirmed outside both documented ranges by direct arithmetic on the fetched IDs.

**Independent reconstruction of the wave boundaries themselves**, rather than trusting the plan's
stated numbers: `sacct -u o_iseri -X -P --starttime=2026-08-09T00:00:00 --endtime=2026-08-11T00:00:00
--format=JobID,JobName,Submit,State`, filtered to `JobName` containing `e02_`, deduplicated to one row
per array ID. **68 distinct `e02_*` array job IDs found in the window — exactly 19 (wave 1) + 8
(orphan) + 41 (wave 2) = 68.** The 8 orphan IDs sit in a genuine numeric and temporal gap: wave 1's
last submission is `1176599` at `2026-08-09T23:01:12`; the 8 orphans run `1177095`-`1178538`,
submitted `2026-08-09T23:08:58` through `2026-08-10T00:04:49`; wave 2's first submission is `1198104`
at `2026-08-10T07:48:57`. (Stated as raw fact from `sacct`, not as a reconstructed narrative of intent
— per the plan's instruction.)

### The 8 job IDs, as facts from `sacct`

| Job ID | JobName | Submit | State (all tasks) | WorkDir | User |
|---:|---|---|---|---|---|
| 1177095 | `e02_la_centre_layout_assign` | 2026-08-09T23:08:58 | 225 COMPLETED, 1 FAILED (226 tasks) | `/nfs/home/o/o_iseri` | o_iseri |
| 1177838 | `e02_la_rural_auto` | 2026-08-09T23:31:00 | 142 COMPLETED, 7 FAILED (149 tasks) | `/nfs/home/o/o_iseri` | o_iseri |
| 1177839 | `e02_la_rural_building` | 2026-08-09T23:31:00 | 149 COMPLETED (149 tasks) | `/nfs/home/o/o_iseri` | o_iseri |
| 1177840 | `e02_la_rural_floor` | 2026-08-09T23:31:00 | 142 COMPLETED, 7 FAILED (149 tasks) | `/nfs/home/o/o_iseri` | o_iseri |
| 1177841 | `e02_la_rural_layout_assign` | 2026-08-09T23:31:00 | 149 COMPLETED (149 tasks) | `/nfs/home/o/o_iseri` | o_iseri |
| 1177875 | `e02_la_rural_fast_zone` | 2026-08-09T23:33:01 | 139 COMPLETED, 10 FAILED (149 tasks) | `/nfs/home/o/o_iseri` | o_iseri |
| 1178313 | `e02_austin_urban_fast_zone` | 2026-08-09T23:53:03 | 425 COMPLETED (425 tasks) | `/nfs/home/o/o_iseri` | o_iseri |
| 1178538 | `e02_austin_rural_auto` | 2026-08-10T00:04:49 | 245 COMPLETED (245 tasks) | `/nfs/home/o/o_iseri` | o_iseri |

`WorkDir` is the same (`/nfs/home/o/o_iseri`, the login home) for every job in this project's `sacct`
history — `sbatch` records the directory it was invoked *from*, not the `FLEET_DIR` it operates on, so
this field carries no discriminating information between the two known drivers or a third one.

**Cross-check against wave 2's own log:** every one of these 8 `(cell, mode)` pairs — `la_centre
layout_assign`; `la_rural` all five modes (`auto`, `building`, `floor`, `layout_assign`,
`fast_zone`); `austin_urban fast_zone`; `austin_rural auto` — **reappears in wave 2**
(`e02_remainder_jobids.txt`: `1198125`, `1198155`/`57`/`58`/`59`/`60`, `1198185`, `1200564`
respectively). This is the fact underlying the register's own statement that the duplication "proves
the pipeline deterministic" — the same buildings failed both times these arrays ran.

### Local-side trace

Searched every locally-reachable artifact that could document a submission event:

- `e02_fleet_submit.py`, `e02_submit_remainder.sh`, `e02_remainder_jobids.txt` (a prior session's
  scratchpad) — **`e02_remainder_jobids.txt` fully accounts for wave 2's 41 IDs** with per-array
  timestamps; it contains **zero references** to any of the 8 orphan IDs.
- `%TEMP%\ubem_e02_five_mode\e02_run.log`, `e02_run_2.log` — **zero references** to any of the 8 IDs.
- The two `e02_generation_summary__*.json` files under `%TEMP%\ubem_e02_fleet\` (T03's tree) —
  both have `"submitted_flag": false` and `"job_ids": {}`, confirming **neither locally-recorded
  generate+ship invocation submitted anything** — wave 1's actual submission event has no local
  artifact at all (only its ID range, which is register-carried, not re-derived here from a file).

### Remote shell history

`ls -la ~/.bash_history ~/.history` on the login node: `.bash_history` exists (38,270 bytes) but its
**mtime is 2026-04-27**, months before the 2026-08-09/10 submission window; `.history` is 16 bytes,
mtime 2026-07-29, and its content is unrelated (`ls`). Grepped `.bash_history` for `e02` directly:
**0 matches.** This is not selective evidence against the orphan wave specifically — **none** of the
three waves (wave 1, wave 2, or the 8 orphans) appear in `.bash_history` at all, consistent with every
submission in this project going through non-interactive `ssh host "command"` execution (the same
`_ssh()`-style single-shot mechanism used throughout this codebase), which does not write to an
interactive login shell's history. Shell history is therefore **not a discriminating source** here —
its silence proves nothing about which of the three waves is which.

### OPEN-40 verdict

**The submitter cannot be traced.** No local script or log claims these 8 array submissions (wave 2's
own accounting log shows it treated these 8 `(cell, mode)` pairs as still-outstanding and resubmitted
them, meaning whatever submitted the orphan wave was not the process that produced
`e02_remainder_jobids.txt`). `sacct`'s `JobName`, `WorkDir`, and `User` fields are identical in form
across all three waves and carry no distinguishing signal — `JobName` is generated by the same
`--job-name=e02_{cell}_{mode}` convention embedded in `e02_fleet_submit.py`'s ready-command output
(§ `t08.submit_array`), which any invocation of that convention — including a manually copy-pasted
`sbatch` command from that ready-command text — would reproduce identically. Remote shell history
cannot help because it captures none of the three waves. **This is the finding, per the plan's own
instruction ("if it cannot be traced, that is the finding").** The remedy the register already names —
a submission log nobody can bypass — is the correct one; this measurement adds no new remedy option
and proposes none (out of scope for this task).

---

## Summary for the director

- **OPEN-39**: mechanism confirmed exactly as described (existence control: 42M/no-`task.rc` vs.
  340K/`task.rc`-present, same array). 45 known E02 failures orphan **≈2.14 GB** total (≈48.6 MB mean,
  ≈111× the successful-sample mean). Confirmed **not E02-specific** — reproduced once in `t17_*`
  (a different fleet generation through the same sbatch template). Zero of 15 `task.rc` references
  anywhere in `scripts/` use it as a completion test — the standing rule is preventive, not corrective,
  in this codebase today.
- **OPEN-40**: all 8 job IDs independently confirmed outside both waves, both from direct arithmetic
  and from a from-scratch `sacct` reconstruction of all 68 `e02_*` array submissions in the window.
  Submitter **untraceable** — no local artifact, no `sacct` field, and no shell history (which is
  silent for all three waves alike, not selectively for this one) identifies who or what submitted it.
- **One methodological finding logged, not part of OPEN-39/40**: `_ssh()` commands ≥ 8,192 chars fail
  silently with a misleading `Unmatched '.` error on this remote path; this audit's script now chunks
  under 7,500 chars. Left to the director to assign an item ID if warranted.
