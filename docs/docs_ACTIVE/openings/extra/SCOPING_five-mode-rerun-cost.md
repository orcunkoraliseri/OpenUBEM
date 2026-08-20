# SCOPING — compute cost of a five-mode fleet re-run with `.eio` retained (cluster PART 1 + local-workstation PART 2)

> **Task type:** scoping/costing only. Nothing was submitted to the cluster, no pipeline/cluster
> script was edited, no job was touched or cancelled. Part 1's cluster commands were all read-only
> (`sacct`, `sacctmgr`, `squeue`, `sinfo`, `scontrol show partition`, `quota -s`, `df -h`, `du -sh`,
> `ls`). Part 2 (appended after the user decided to run locally instead, since the shared cluster
> has other people's work on it — see PART 1 §4.1) performed exactly 3 single-building EnergyPlus
> runs locally, in the session scratchpad, purely for timing/correctness calibration; nothing
> outside the scratchpad was written or modified. Dates: Part 1 2026-08-05, Part 2 2026-08-05
> (same day, later in the session).
> **Scope:** one five-mode pass (`auto`, `building`, `floor`, `fast_zone`, `layout_assign`) across
> the full 12-cell / 8,160-building fleet, with the trim block changed to retain `eplusout.eio`.
> Disk baseline: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-02_eio-disk-budget.md` (M02),
> re-verified live in Part 1 §2, not re-derived.

## Verdict up front

**Part 1 (cluster):** Disk is a non-issue (confirmed again, unchanged from M02). Compute is
**not** a non-issue: the account's cluster-wide concurrency cap is a hard 32 CPUs, that cap is
**currently fully occupied by an unrelated job with 675+ tasks still pending**, and four of the
five modes have no full-fleet timing data and have not been exercised on the cluster in five weeks
of `builder.py` changes. See Part 1 §5 for the cluster recommendation (superseded by the user's
decision to run locally).

**Part 2 (local, this is now the live plan):** Feasible and materially better than the cluster
figure suggested. Empirically (3 single-building timing runs, one cell, three of the four
under-tested modes), this workstation's core is **roughly 3.2×–4.6× faster per zone** than the
cluster core the 540 CPU-hour figure was built from. Net: **≈117–180 single-core-hours** of actual
work, which at a **12-of-20-core** allocation (8 cores/40% left for the user) is **≈10–15 hours of
wall-clock** — an overnight run, not a weekend and nowhere near a month. The `fast_zone` walltime
tail risk that worried Part 1 (2-hour cluster cap) mostly evaporates locally: there's no timeout to
die against, and the extrapolated worst-case single building costs one worker only **≈18–26
minutes**, negligible against the full run. Disk, trimmed-plus-`.eio`, is trivial locally too. The
open item is the reverse of the cluster page: **local disk cannot absorb an untrimmed run at all**
(a documented single-city untrimmed `fast_zone` pass already exceeds this machine's entire free
disk) — trimming must be added to the local runner. See Part 2 §5 for the recommendation and
costed alternatives.

---

# PART 1 — CLUSTER (original scoping, unchanged below)

---

## 1. Wall-clock and CPU cost

### 1.1 What is directly measured, at full 12-cell/8,160-building scale, at current HEAD

`layout_assign` is the only mode with a same-scale, current-code measurement: **T20**
(`scripts/cluster/t20_layout_assign_full_sweep.py`, ran 2026-07-26/27, job names
`t20_<cell>_layout_assign`, read via `sacct -u o_iseri`).

| metric | value |
|---|---|
| tasks | 8,160 (12 cells × 680) |
| completed / failed | 8,153 / 7 (0.09% failure rate) |
| total CPU-time | **240.3 CPU-hours** |
| mean task time | 1.8 min |
| **max task time** | **119.2 min** — 0.8 min under the sbatch `--time=02:00:00` limit |
| wall-clock span (first array start → last array end) | 2026-07-26 17:17:40 → 2026-07-27 01:04:31 = **7h 47min** |

Cross-checked against T17/T18/T19 (same job-name pattern, same 8,160-task scale, older code):
T17 = 214.1 CPU-hr (max 89.9 min), T18 = 178.1 CPU-hr (max 86.7 min), T19 = 134.7 CPU-hr
(max 38.1 min). All four generations: **zero TIMEOUT states** — every task that didn't fail,
completed within the 2-hour limit. T20's 119.2-min max is the closest any generation has come to
that limit.

### 1.2 What is measured, but only at partial scale / older code

`auto`, `building`, `floor`, `fast_zone` last ran on the cluster during **T08**
(2026-06-30 → 2026-07-01, five weeks before this scoping), against 5 of the 12 cells only
(`nyc_centre`, `nyc_urban`, `nyc_suburban`, `nyc_rural`, `la_centre` — the same 5-cell subset M02
used for its `.eio` size estimate). Job names `t08_<cell>_<mode>`, read via the same `sacct` query.

| mode | n (5-cell) | CPU-hours (5-cell) | CPU-hr/building | max task time |
|---|---:|---:|---:|---:|
| `auto` | 4,531 | 48.09 | 0.01061 | 30.5 min |
| `building` | 4,530–5,798* | 21.64 | 0.00373–0.00477 | 6.8 min |
| `floor` | 4,530 | 32.80 | 0.00724 | 14.6 min |
| **`fast_zone`** | 4,530 | 66.40 | 0.01466 | **83.6 min** (nyc_centre) |

\* `building`'s task count (5,798) exceeds the other three modes' (4,530) at the same cell set —
likely retries/resubmits within T08's `sacct` history, not 5,798 distinct buildings. Both bounds
are carried into §1.3.

All T08 states: 19,382 COMPLETED, 5 FAILED, 2 CANCELLED (historical, not this session's doing).
Zero TIMEOUT in T08 either.

**Read-only checks attempted and their result:** searched `sacct` back to 2026-01-01 for any
`fast_zone`/`auto`/`building`/`floor` job outside T07/T08 — none found. `fast_zone` has never run
on the other 7 cells (all 4 LA cells except `la_centre`... actually `la_centre` is the one LA cell
it did run; `la_urban`/`la_suburban`/`la_rural` and all 4 Austin cells have **zero** `fast_zone`
history) or on current-HEAD code. This is a stated gap, not a fabricated number.

### 1.3 Projected cost of one five-mode, 12-cell, 8,160-building pass

Per-building CPU-hour rate from §1.2, scaled to 8,160 buildings (extrapolation for 4 of 5 modes —
flagged where it is):

| mode | basis | projected CPU-hours (8,160 bldg) |
|---|---|---:|
| `layout_assign` | **measured directly**, current HEAD, 12 cells | **240.3** |
| `auto` | extrapolated from 5 cells, 5-week-old code | ~86.6 |
| `building` | extrapolated from 5 cells, 5-week-old code | ~30.5–39.0 |
| `floor` | extrapolated from 5 cells, 5-week-old code | ~59.1 |
| `fast_zone` | extrapolated from 5 cells, 5-week-old code | ~119.6 |
| **Total, 5 modes** | | **≈ 535–545 CPU-hours** (≈ 22.5 CPU-days) |

**Wall-clock projection.** The account's cluster-wide concurrency cap is 32 CPUs (see §4.1) —
confirmed against T20's own numbers: 240.3 CPU-hr ÷ 7.78h wall-clock = 30.9 effective concurrent
CPUs, matching the cap. Applying the same cap to ≈540 CPU-hours: **≈ 540 / 32 ≈ 17 hours of
wall-clock**, if the cluster is uncontended for the account's full 32-CPU allowance the entire time.
**This assumption is currently false — see §4.1.**

**Which numbers are real vs. bounded, explicitly:**
- Real, current-code, full-fleet: `layout_assign` (240.3 CPU-hr).
- Real cluster timing, but 5-cell/5-week-old-code extrapolation: `auto`, `building`, `floor`,
  `fast_zone` CPU-hour totals.
- **Not measured, bounded only:** whether `fast_zone`'s per-task tail scales past the 2-hour
  walltime limit at full 12-cell scale — see §4.2. The 83.6-min max observed in T08 is real, but it
  comes from a 5-cell sample that didn't include the cells/buildings driving `fast_zone`'s
  837-zone maximum (M02 §3's zone-count table is fleet-wide, T08's timing sample is not).

---

## 2. Disk — live re-verification of M02

Re-ran the same three read-only commands M02 used, same day range irrelevant (these are point-in-time):

```
$ ssh o_iseri@speed-submit2.encs.concordia.ca "quota -s"
/speed-scratch   5.8T used / 10.0T limit  (9.8T warn)   →  4.2 TB personal headroom, unchanged

$ ssh o_iseri@speed-submit2.encs.concordia.ca "df -h /speed-scratch/o_iseri"
121T size, 113T used, 8.1T avail (94% used)             →  unchanged

$ ssh o_iseri@speed-submit2.encs.concordia.ca "du -sh /speed-scratch/o_iseri/openubem"
36G                                                       →  unchanged
```

All three numbers are **identical** to M02 (dated the same day, 2026-08-05, so no drift expected,
but confirmed rather than assumed). M02's verdict stands: even the ≈43 GB worst-case five-mode
`.eio` addition is **0.5% of the 8.1 TB shared free space** and **1.1% of the 4.2 TB personal
quota headroom**. Disk is not a constraint on this decision.

---

## 3. The exact change required

`scripts/cluster/submit_fleet_t08.sbatch` — **not applied**, quoted only.

**Header comment (lines 9–12), before:**
```bash
# T08 variant of submit_fleet.sbatch.
# Same simulation logic; after E+ completes, deletes all non-essential output files
# (*.eso, *.eio, *.mtd, *.rdd, *.mdd, *.htm, table files) to keep cluster storage bounded.
# Keeps: eplusout.sql (results), eplusout.end (completion marker), eplusout.err (Fatal check).
```

**Header comment, after:**
```bash
# T08 variant of submit_fleet.sbatch.
# Same simulation logic; after E+ completes, deletes all non-essential output files
# (*.eso, *.mtd, *.rdd, *.mdd, *.htm, table files) to keep cluster storage bounded.
# Keeps: eplusout.sql (results), eplusout.end (completion marker), eplusout.err (Fatal check),
#        eplusout.eio (floor-area proof, OPEN-02).
```

**Trim block (lines 62–81), before:**
```bash
rm -f "$OUTDIR"/*.eso \
      "$OUTDIR"/*.eio \
      "$OUTDIR"/*.mtd \
      "$OUTDIR"/*.rdd \
      "$OUTDIR"/*.mdd \
      "$OUTDIR"/*.htm \
      "$OUTDIR"/*.tab \
      "$OUTDIR"/*.csv \
      "$OUTDIR"/in.idf \
      "$OUTDIR"/expanded.idf \
      "$OUTDIR"/Energy+.idd \
      "$OUTDIR"/eplusout.dxf \
      "$OUTDIR"/eplusout.audit \
      "$OUTDIR"/eplusout.bnd \
      "$OUTDIR"/eplusout.dbg \
      "$OUTDIR"/eplusout.sln \
      "$OUTDIR"/eplusout.rvaudit \
      "$OUTDIR"/eplusmtr.* \
      "$OUTDIR"/eplusout.mtr 2>/dev/null || true
# Kept: eplusout.sql, eplusout.end, eplusout.err, task.rc
```

**Trim block, after (single line removed, comment updated):**
```bash
rm -f "$OUTDIR"/*.eso \
      "$OUTDIR"/*.mtd \
      "$OUTDIR"/*.rdd \
      "$OUTDIR"/*.mdd \
      "$OUTDIR"/*.htm \
      "$OUTDIR"/*.tab \
      "$OUTDIR"/*.csv \
      "$OUTDIR"/in.idf \
      "$OUTDIR"/expanded.idf \
      "$OUTDIR"/Energy+.idd \
      "$OUTDIR"/eplusout.dxf \
      "$OUTDIR"/eplusout.audit \
      "$OUTDIR"/eplusout.bnd \
      "$OUTDIR"/eplusout.dbg \
      "$OUTDIR"/eplusout.sln \
      "$OUTDIR"/eplusout.rvaudit \
      "$OUTDIR"/eplusmtr.* \
      "$OUTDIR"/eplusout.mtr 2>/dev/null || true
# Kept: eplusout.sql, eplusout.end, eplusout.err, eplusout.eio, task.rc
```

That is the entire diff: delete the `"$OUTDIR"/*.eio \` line, adjust two comments. No other line
changes. Confirmed by reading the file directly (`scripts/cluster/submit_fleet_t08.sbatch`,
2,770 bytes, remote copy timestamp 2026-07-26 17:30, matches the local repo copy last touched by
T20's `scp` deployment — the remote and local sbatch are the same file, no drift to reconcile).

---

## 4. Risks and unknowns

### 4.1 Immediate, currently-observed blocker: the account's CPU cap is already full

`sacctmgr show assoc user=o_iseri format=GrpTRES` returns **`cpu=32`** — this is a **cluster-wide,
account-wide** cap (blank `Partition` field in the assoc record), not a per-partition or per-array
limit. It is independent of the `%16` per-array throttle every T08/T17–T20 sweep script sets — that
throttle has never been the binding constraint; the 32-CPU account cap has.

Right now (`squeue -u o_iseri`, checked live): **32 RUNNING, 675 PENDING**, all under job name
`qc1983nu` (job arrays 1172484 / 1172485) — a job that does **not** match any OpenUBEM naming
convention (`t07`–`t20`, `openubem_*`), i.e. this is a different project's job on this account,
currently consuming 100% of the account's concurrency allowance. Its pending-reason is literally
`AssocGrpCpuLimit`. Per the hard rule against touching other-project cluster runs, this job was
**only read**, never queried further, cancelled, or otherwise interacted with.

**Consequence: any five-mode fleet submission today would not start running** — its tasks would
sit `PENDING (AssocGrpCpuLimit)` behind this job's remaining ~675 tasks until they clear the 32-CPU
cap. How long that takes cannot be estimated read-only without speculating about a job this task is
explicitly barred from investigating further. This is a **scheduling dependency**, not a compute
cost, but it directly gates when the 17-hour wall-clock estimate in §1.3 would actually start.

### 4.2 `fast_zone` walltime risk — bounded, not measured, at fleet scale

T20's `layout_assign` max task time (119.2 min) sits within 48 seconds of the sbatch
`--time=02:00:00` limit, and `layout_assign`'s fleet-wide max zone count is 336 (M02 §3). `fast_zone`'s
fleet-wide max zone count is 837 — 2.49× higher. If `fast_zone`'s worst-case task scales with zone
count similarly to how its measured 5-cell sample scales relative to `layout_assign`'s 5-cell
sample, a tail `fast_zone` building could plausibly need on the order of ~5 hours, **well past the
2-hour limit**, and would be killed with a TIMEOUT state (no `.sql`/`.err`/`.end` written, not even
a trimmed result) rather than fail cleanly. **No `fast_zone` task has actually timed out in the
data available** (T08's observed 5-cell max was 83.6 min) — but T08's sample explicitly excluded
the cells outside `{nyc_centre, nyc_urban, nyc_suburban, nyc_rural, la_centre}`, and nothing in the
available evidence confirms whether the 837-zone outlier building lives inside or outside that
5-cell sample. This is the single largest unknown in this report.

### 4.3 Code has moved significantly since the last full run of 4 of 5 modes

`auto`/`building`/`floor`/`fast_zone` last ran on the cluster during T08 (2026-06-30/07-01).
Since the commit `openubem/idf/builder.py` was at during T08 (`e063865`, 2026-06-30), that one
file alone has **223 insertions / 39 deletions** across 9 subsequent commits (through
`69373f9`/`3a925f9`, 2026-07-27) — the storey-matching closure and layoutAssigner work. Those
commits targeted `layout_assign`, but `builder.py` is the shared entry point all five modes route
through; a shared-path regression affecting the other four modes would not have been caught by
T17–T20 (which only ever exercised `layout_assign`). `layout_assign` itself has by far the most
recent and most extensive cluster validation (T17→T20, 4 full-fleet generations, most recent
2026-07-26/27, current HEAD); the other four modes have **zero cluster validation at current HEAD**.

### 4.4 Lower-severity items, checked and cleared

- EnergyPlus install present at the path the sbatch script expects (`ls` confirmed both the
  Ubuntu20.04 and Ubuntu22.04 builds exist under `/speed-scratch/o_iseri/openubem/tools/`).
- Partition `ps` has 7-day max walltime and 2,688 total CPUs cluster-wide (`sinfo`/`scontrol show
  partition ps`) — node/partition capacity is not the constraint; the account's own 32-CPU
  `GrpTRES` is.
- Failure rate at current HEAD (T20) is low (7/8,160 = 0.09%) and no TIMEOUT states across any of
  T17–T20 — the pipeline itself is stable for `layout_assign`; the open question is specifically
  about the four modes without recent full-scale evidence.
- Remote `submit_fleet_t08.sbatch` matches the local repo copy (no undocumented remote drift).

---

## 5. Go/no-go recommendation

**No-go today, conditional go once the queue clears.** The disk cost is negligible (≈1.3 GB
typical, ≈43 GB worst-case, against 4.2 TB of personal and 8.1 TB of shared headroom) and the
`.eio`-retention edit is a one-line, low-risk change to a script already proven at fleet scale.
Compute is the real gate: projected cost is **≈540 CPU-hours (≈17 hours of wall-clock)** *if* the
account's 32-CPU cap is free — but that cap is **100% occupied right now** by an unrelated job with
675+ tasks still pending, so nothing would run today regardless of when it's submitted. Layer onto
that a real, unmeasured risk that `fast_zone`'s longest-tail buildings (up to 837 zones, 2.5× worse
than `layout_assign`'s tail) could exceed the current 2-hour per-task walltime limit and die with no
output at all, plus five weeks of un-cluster-tested `builder.py` changes sitting under the four
modes that aren't `layout_assign`. Recommend: (1) wait for the account's CPU allowance to clear,
(2) apply the one-line `.eio` retention edit from §3, (3) before the full 8,160×5 submission, run a
small `fast_zone`-only smoke array (a handful of the largest-zone-count buildings from the 837-zone
tail, current HEAD) to directly resolve the §4.2 walltime risk rather than submitting the full fleet
against a bounded guess.

---

# PART 2 — LOCAL WORKSTATION (appended after the user chose local over cluster)

> The user has instructed that the re-run happen on this workstation instead of the cluster,
> because the shared cluster has other people's work on it — directly confirmed by Part 1 §4.1's
> live finding (account's 32-CPU cap 100% occupied by an unrelated 707-task job). Standing rules
> for this part: nothing submitted to the cluster, no job touched, no pipeline/cluster script
> edited (diffs quoted as text only), no `git commit`, no `.py` under `docs/`. Exactly 3
> single-building EnergyPlus runs were performed locally for timing calibration — the only compute
> this part performed beyond read-only OS queries and existing-fixture reads.

## 1. Machine capability, measured

Read via `Get-CimInstance` / `Get-PSDrive` (PowerShell, local, read-only):

| resource | value |
|---|---|
| CPU | Intel Core Ultra 7 265 — **20 cores, 20 logical processors** (no SMT reported; physical = logical) |
| RAM | **63.5 GB** total |
| `C:` free space | **659.4 GB** free (1,247.4 GB used) — the only drive; repo and `openubem/outputs/` both live on `C:` |
| local EnergyPlus | confirmed present: `C:\EnergyPlusV23-1-0\energyplus.exe` (same 23.1.0 version the cluster runs) |

**Workers I would use: 12 of 20 (60%), leaving 8 cores / 40% headroom** for the user's own work
during the run, since this is the user's day-to-day machine and the run is projected to take
several hours (§3). `scripts/cluster/t08_local_remainder.py` already exposes this as a plain CLI
flag (`--n-ep-workers 12`) — no script edit needed to change the worker count.

RAM headroom was not independently stress-tested (I did not run 12 EnergyPlus instances
concurrently, only 1 at a time — see §2), but single-building EnergyPlus runs at the zone counts
these buildings use (double digits to low hundreds, not a CFD-scale problem) are typically
low-hundreds-of-MB processes; 63.5 GB ÷ 12 workers ≈ 5.3 GB/worker is generous headroom by
inference, not by direct measurement. **Stated as an inference, not a verified fact.**

## 2. Local-versus-cluster speed factor — established empirically

**3 EnergyPlus runs performed** (the full allowance), all on the **same building**
(`way/265296110`, `nyc_centre`, chosen because it sits at the 75th percentile of that cell's
`fast_zone` zone-count distribution — 80 zones vs. a cell mean of 56.75 — a deliberately
representative pick, not the 837-zone extreme). Ran via a throwaway script in the session
scratchpad (`local_timing_bench.py`) that calls the existing `openubem.idf.builder.run_step3` and
then the same local EnergyPlus invocation pattern `t08_local_remainder.py` already uses — no
pipeline code was modified, only read and called.

| mode | num_zones (this building) | local wall time | status |
|---|---:|---:|---|
| `auto` | 16 | 20.28 s | success, no fatal |
| `floor` | 16 | 20.89 s | success, no fatal |
| `fast_zone` | 80 | 86.47 s | success, no fatal |

`building` mode was **not** run locally (3-run budget spent on the 3 higher-risk/higher-zone-count
modes; `building` is always exactly 1 zone, the least likely of the four to have regressed — see
§6 for why this is an accepted, stated gap rather than an oversight).

**Deriving the factor.** A single building's raw wall time isn't directly comparable to a cluster
*cell mean* (different buildings, different zone counts), so the comparison is normalized
per-zone, using the same cell's T08 cluster data (Part 1 §1.2/§1.3 source):

| mode | cluster mean (nyc_centre, T08) | cluster s/zone | local s/zone (this run) | **speed factor (cluster ÷ local)** |
|---|---:|---:|---:|---:|
| `auto` | 117.6 s @ 23.54 zones (mean) | 4.996 | 1.268 | **3.94×** |
| `floor` | 63.6 s @ 10.68 zones (mean) | 5.955 | 1.306 | **4.56×** |
| `fast_zone` | 195.0 s @ 56.75 zones (mean) | 3.436 | 1.081 | **3.18×** |

**Empirical local-vs-cluster speed factor: 3.2×–4.6×, midpoint ≈3.9×.** This workstation's single
core is meaningfully faster than the cluster's per-task core for this workload — not parity, and
not assumed; measured. Caveats, stated plainly: this is 3 data points, 1 building, 1 cell, compared
against per-zone-normalized cluster *means* rather than the same building's own cluster time (which
isn't recoverable from `sacct` — it aggregates per array, not per building-stem). It is a solid
order-of-magnitude figure, not a precision instrument.

## 3. Wall-clock for the full five-mode, 12-cell, 8,160-building pass

Applying the 3.2×–4.6× factor (plus a deliberately conservative 3.0× floor, below the measured
range, as a safety margin) to Part 1 §1.3's 540 cluster-CPU-hour projection:

| basis | local single-core-hours | wall-clock @ 12 workers |
|---|---:|---:|
| optimistic (4.6×) | 117 | 9.8 h |
| **measured midpoint (3.9×)** | **139** | **11.6 h** |
| measured-range floor (3.2×) | 169 | 14.1 h |
| deliberately conservative (3.0×, below measured range) | 180 | 15.0 h |

**≈10–15 hours of wall-clock at 12 workers — an overnight run.** At 8 workers (more headroom,
50/50 split with the user): ≈15–22.5 h (still under 1 day). At 16 workers (less headroom): ≈7.3–11.3 h.
None of these is "a weekend" or "a month" — the earlier cluster-only framing (800 GB/multi-day
warnings) was about disk and about a contended shared cluster, not about this machine's own
throughput.

**The `fast_zone` tail, folded in.** Locally there is no 2-hour walltime to time out against — a
slow building just occupies one of the 12 workers longer, delaying that worker's next building
rather than dying with no output. Sizing the actual delay: Part 1 §4.2 established the cluster's
own observed `fast_zone` worst case at 83.58 min (nyc_centre, almost certainly the fleet's 837-zone
outlier, the same cell). Applying the empirical 3.18×–3.94× `fast_zone`-relevant speed-factor range
to that single real data point: **≈18–26 minutes locally for the worst single building in the
entire fleet.** That's a rounding error against a 10–15-hour run — one worker blocked for
20-odd minutes while the other 11 keep going. This materially de-risks the item Part 1 flagged as
its single largest unknown.

## 4. Disk, recomputed for local

**Trimmed-plus-`.eio`** (same byte math as Part 1 §2/M02 — file sizes don't change with the
machine running them): fleet-wide, **≈1.3 GB typical, ≈42.9 GB worst-case**. Against this
machine's **659.4 GB free**, worst-case is **6.5%** of free space — still trivial, just a much
smaller headroom ratio than the cluster's 8.1 TB gave (0.53%). Not a constraint either way.

**Fully untrimmed — not computed precisely, and not attempted, because the answer is already known
to be "infeasible."** `submit_fleet_t08.sbatch`'s own header comment (Part 1 §3) documents
**>800 GB untrimmed for a single `fast_zone` city pass** on the cluster. This machine's *entire*
free disk (659.4 GB) is smaller than that one documented single-city, single-mode figure — before
multiplying by the other 4 modes or the other 11 cells. **An untrimmed local run cannot happen on
this machine, full stop.**

**Consequence: trimming is mandatory locally, and it isn't currently there.** Unlike the cluster
path (`submit_fleet_t08.sbatch` already trims; Part 1 §3 is a 1-line edit to what exists),
`scripts/cluster/t08_local_remainder.py`'s `_run_one_ep()` (the function that actually invokes
EnergyPlus locally, lines ~161–192) **performs no trimming at all today** — it runs EnergyPlus and
writes `task.rc`, nothing else. Read, not applied. A local trim step patterned on the cluster's
own block would need to be added there, e.g. (quoted, not applied):

```python
# after the EnergyPlus subprocess.run(...) call in _run_one_ep(), before returning:
for pattern in ("*.eso", "*.mtd", "*.rdd", "*.mdd", "*.htm", "*.tab", "*.csv",
                "in.idf", "expanded.idf", "Energy+.idd", "eplusout.dxf",
                "eplusout.audit", "eplusout.bnd", "eplusout.dbg", "eplusout.sln",
                "eplusout.rvaudit", "eplusmtr.*", "eplusout.mtr"):
    for f in outdir.glob(pattern):
        f.unlink(missing_ok=True)
# Kept: eplusout.sql, eplusout.end, eplusout.err, eplusout.eio, task.rc
```

This mirrors the cluster's `rm -f` list from Part 1 §3 exactly, minus `*.eio` (retained, per the
whole point of this re-run) — same keep-list, same delete-list, just Python instead of bash.
**Not applied — quoted only, per the standing rule.**

## 5. Feasibility verdict and costed alternatives

**Feasible.** ≈10–15 hours of wall-clock, ≈43 GB worst-case disk against 659 GB free, and a
`fast_zone` tail that costs one worker ≈20 minutes rather than dying — all comfortably inside what
one overnight local run can absorb, *provided* the trim step in §4 is added first (otherwise disk,
not compute, is what fails). The user chooses which of the following to run; each line is a
complete, standalone option, not a staged sequence:

| option | scope | projected wall-clock (12 workers) | what it would let us conclude | what it would NOT let us conclude |
|---|---|---:|---|---|
| **Full five-mode fleet** | 5 modes × 12 cells × 8,160 bldgs | **≈10–15 h** | Direct, full replacement of the cluster run — every mode, every cell, `.eio` retained, ready for the floor-area-error analysis the whole arc exists for. | Nothing withheld — this is the complete answer, at the cost of the full wall-clock. |
| **`layout_assign` only** | 1 mode × 12 cells × 8,160 bldgs | **≈4.4–6.7 h** (extrapolated factor, not directly benchmarked for this mode) | Confirms local EnergyPlus reproduces T20's cluster EUI/failure-rate/`.eio` sizes for the one mode already exhaustively cluster-validated (Part 1 §1.1) — a pure local-vs-cluster consistency check. | Nothing about the four modes this whole re-run exists to de-risk (Part 1 §4.3) — `layout_assign` is the one mode NOT in question. |
| **Cell subset** (e.g. 1 NYC + 1 LA + 1 Austin cell, ~2,040 bldgs) | 5 modes × 3 cells | **≈2.5–3.5 h** | Fast per-mode correctness gate across all 3 climate zones/states — catches a `builder.py` regression that's climate- or state-specific. | Cannot rule out a defect specific to a density tier (urban/suburban/rural) not in the chosen 3 cells, and gives no fleet-wide floor-area-error magnitude. |
| **Per-archetype sample** (~1 building/archetype/cell) | 5 modes × ~200–400 bldgs | **< 1 h** | Fastest possible "does it still generate + simulate cleanly at HEAD" gate for all 5 modes — a pure correctness/smoke check, cheaper than even the 3 timing runs already done here. | Sample is far too small/non-representative in building-size distribution to say anything trustworthy about the floor-area error's aggregate size — correctness only, no magnitude. |

## 6. `builder.py` drift — correctness, carried forward and partially resolved

Part 1 §4.3 flagged 223 insertions / 39 deletions in `openubem/idf/builder.py` since the four
non-`layout_assign` modes last ran on the cluster (T08, five weeks prior), meaning those four modes
had **zero** validation at current HEAD. The 3 timing runs in §2 double as a first data point on
that question, by design (3 of the 4 modes were deliberately chosen over re-testing
`layout_assign`, which already has extensive current-HEAD cluster validation via T17–T20):

**`auto`, `floor`, and `fast_zone` all generated a valid IDF and completed EnergyPlus successfully
at current HEAD** (`rc=0`, `eplusout.end` reports "EnergyPlus Completed Successfully", no
`** Fatal **` in `eplusout.err`) for this one building. This is a real, positive, unfabricated data
point — current HEAD has not obviously broken these three modes' basic generate-and-simulate path.

**What this does and doesn't resolve:** it is 1 building out of 8,160, so it cannot rule out an
edge-case regression elsewhere in the fleet (unusual archetype, degenerate footprint, an
`.eio`-adjacent code path this building's geometry never exercises). `building` mode (the 4th)
remains **completely unverified at HEAD**, cluster or local — a stated, accepted gap, not
fabricated as "probably fine" beyond the structural argument that it's the simplest of the five
modes (always exactly 1 zone, least surface area for a geometry bug to hide in). The
per-archetype-sample option in §5's table is the direct, cheap way to close this gap fully before
committing to the full 10–15-hour run, if the user wants that extra confidence first.

---

# PART 3 — CORRECTION, 2026-08-06: Part 2's local wall-clock projection is wrong by ≈10×

> Appended after the E02/C02 local run was actually launched and measured. **Parts 1 and 2 above are
> left unedited** — the prediction must stand as written so the error is visible. This part states
> what the run measured and what must be used instead. Source of record:
> `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_compute-queue.md` §8 **FINDING 3** (and the
> append-only CORRECTION immediately following it).

## 3.1 What Part 2 predicted vs. what the machine actually did

Part 2 §3 projected **≈10–15 h** at 12 workers for the whole five-mode / 12-cell / 8,160-building
pass (≈7.3–11.3 h at 16 workers). The run was launched locally and timed on `nyc_centre`
(738 buildings = **9.04%** of the fleet; the 4th-largest of the twelve cells, so the sample is not
cherry-picked large):

| mode | measured on `nyc_centre` | scaled ×11.06 to the fleet |
|---|---|---:|
| `auto` | ≈85 min (includes a ~90 s restart gap) | ≈**15.7 h** |
| `building` | 12.7 min | ≈**2.3 h** |
| `floor` | 41.7 min | ≈**7.7 h** |
| `fast_zone` | 59 of 738 done in 72 min → ≈15 h extrapolated | ≈**2–7 days** |
| `layout_assign` | not completed in this pass | see PLAN §8 C02-P1 probe |

**Three of the five modes alone extrapolate to ≈26 h** — already more than double Part 2's estimate
for all five — and `fast_zone`, the mode Part 2 §3 explicitly de-risked, is the dominant cost by a
wide margin. Order-of-magnitude verdict: **≈10× low.**

## 3.2 Why Part 2 was wrong — and why the pre-registered explanation was *also* wrong

The overrun cause was recorded in advance (PLAN §8 NOTE) as *unbudgeted Step-3 IDF generation*.
**Measurement disproved that.** From the run's own logs: Step 2 costs **2.5–2.7 s** per cell and
Step 3 costs **7.9 s for 149 buildings** (`la_rural`) — a few minutes at 738. IDF generation is
negligible.

The real cause is the one thing Part 2 §2 built its whole projection on: **the 3.2×–4.6×
"local core is faster than a cluster core" speed factor does not hold at fleet scale.** EnergyPlus
itself is slower per building locally than the cluster-derived scaling assumed. Part 2 §2 stated its
own caveat correctly — *"3 data points, 1 building, 1 cell… a solid order-of-magnitude figure, not a
precision instrument"* — and that caveat is exactly where it failed: one 80-zone building at the 75th
percentile of one cell did not represent the fleet's per-building cost, and the error compounds
multiplicatively across 8,160 buildings × 5 modes.

## 3.3 What to use instead

- **Do not cost E02 (or any five-mode re-run, local or Speed) from Part 1 §1.3 or Part 2 §3.**
  Use FINDING 3's measured per-mode `nyc_centre` figures, scaled by building count, as the
  cost basis. They are real elapsed times from the shipped code path at current HEAD, not a
  per-zone-normalized extrapolation from three calibration runs.
- **Part 1's cluster numbers are not corrected by this** and are not thereby validated either: the
  ≈540 CPU-hour cluster projection rests on the same 5-cell/5-week-old T08 extrapolation for four of
  five modes. Whoever re-scopes E02 for Speed should treat FINDING 3 as evidence that per-building
  cost was systematically underestimated, and re-derive rather than reuse.
- **What did survive.** Disk (Part 1 §2, Part 2 §4) is unaffected — file sizes do not depend on the
  machine, and the ≈1.3 GB typical / ≈42.9 GB worst-case figures stand. So does Part 2 §4's harder
  finding that **an untrimmed local run cannot fit on this machine at all**, and §6's positive data
  point that `auto`/`floor`/`fast_zone` generate and simulate cleanly at current HEAD.
- **Scaling caveat carried forward, not hidden.** FINDING 3's fleet column scales by building count
  only. Manhattan buildings are plausibly above fleet-average complexity, so those figures are
  upper-leaning estimates, not measurements.

## 3.4 Status of the run this correction came from

E02/C02 is **halted, not abandoned** — parked at the user's instruction pending Speed cluster
availability, with the CP-C2 scope ruling deliberately deferred rather than decided under time
pressure. No relaunch is authorised. See PLAN §8 *"DECISION OWED — CP-C2 scope ruling"* for the
state to hand to whoever takes that ruling.

