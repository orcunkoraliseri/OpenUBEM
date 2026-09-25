# PROMPT MANAGER — TechTransfer arc (idf_reader → OpenUBEM)

> **Written:** 2026-09-18, by the manager session that closed block 5 / lane J.
> **Covers:** the whole arc, blocks 1–5, from the report `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`.
> **How to use:** paste everything below the horizontal rule into a **fresh** session that will act
> as manager for this arc. Update this file in place at the close of each block — do not supersede it
> with a new dated copy.
> **Paused 2026-09-25 12:30 (user):** scenario harvest 22 of 84 pieces saved; resume from §7k, last bullet.
> **Measured at the time of writing:** the eight TechTransfer test files pass, `108 passed`
> (`python -m pytest tests/test_scenario_measures.py tests/test_pv_injection.py tests/test_compliance_audit.py tests/test_prep_gate.py tests/test_layout_assigner_fit_check.py tests/test_parser_version_robustness.py tests/test_envelope_patcher_windows.py tests/idf/test_ground_temperature.py -q`).

---

## 0. Ownership — read this before anything else

`C:\Users\o_iseri\Desktop\idf_reader` was written by the user for a postdoc position and **is not the
user's project**. OpenUBEM belongs to the user 100 %.

Consequences, absolute:

- **Nothing is copied.** Not code, not docs, not parameter tables, not IDFs, not naming schemes.
  The report and every plan under it are **re-implementation guidance**: take the method, then source
  every number from a public standard and cite it.
- **No borrowed vocabulary.** The retrofit packages `EEM1`–`EEM4` and their tier structure belong to
  that project; the user ruled them out by name. Measures here are named for what they do
  (`thermostat_setback`, `infiltration_tightening`).
- idf_reader may be **read** and **measured** (its prototype IDFs are the realistic test targets —
  see §6), but no file from it ever enters this repo and no test may point at it.

## 1. Role of the session receiving this

**Manager / director.** Reads docs, writes and audits plan docs, dispatches executors, rules on open
questions. **Never writes feature code.** Feature code is written by fresh Sonnet executor sessions,
one brand-new session per dispatch, `model: "sonnet"` passed explicitly.

All state lives in the plan doc on disk, never in an agent's conversation history.

## 2. Where the arc stands (2026-09-18)

Five plan docs, all in `docs/docs_ACTIVE/TechTransfer/implementation/`. Report item → lane → status:

| Report item | Lane / block | Status |
|---|---|---|
| T1 ground coupling | A, block 1 | **Done.** `Site:GroundTemperature:BuildingSurface` written explicitly at 18 °C; proven byte-neutral (A03). |
| T2 skip-when-better windows | B, block 1 | **Done.** Guard behind `ENVELOPE_PATCH_SKIP_WHEN_BETTER` (default OFF). |
| T3 engine-version traps | C, block 1 | **Partly done.** C01–C03 landed (loud absence, version fence). **C04 (per-archetype per-end-use regression fixture) was never started** — see §4. |
| T4 compliance audit | G, block 3 | **Done.** `openubem/idf/compliance.py`, read-only pre-simulation audit + fleet census. |
| T5 retrofit scenario layer | J, block 5 | **Done, lane closed.** See §3. |
| T6 geometry-aware PV | H, block 4 | **Done.** `openubem/idf/pv.py`, library only, nothing calls it. |
| T7 two-phase prep/sim | F, block 2 | **Done.** Prep gate behind `PREP_ABORT_ON_FAILURE` (default OFF). |
| T8 chosen vs inherited | D02, block 1 | **Done.** `docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md`. |
| T9 prototype-vs-plot fit check | E, block 2 | **Done**, incl. E04/E05 re-measure against the scale factor the builder actually applies. |
| T10 AirflowNetwork landmine | D01, block 1 | **Done.** Registered in the debug reference. |
| T11 benchmark anchors / heat pumps | — | **Parked by design.** Waits for a Canadian district case or a heat-pump scenario. Nothing to do. |

**Block 5 / lane J result, in detail** (`openubem/data/scenarios/measures.json`, applier
`openubem/scenarios/measures.py`, tests `tests/test_scenario_measures.py`, 70 tests):

- `lighting_power_density` — **active**. 6.0 W/m², ASHRAE 90.1-2022 §9.3.2; scoped to six office
  archetypes, any other archetype is gated out rather than approximated.
- `envelope_u_upgrade` — **withdrawn**, on the record with a reason. Its targets were byte-identical
  to the code baseline OpenUBEM already applies, so it was a guaranteed no-op on its own archetype
  and a baseline leak on any other.
- `thermostat_setback` — **active**. 5.5556 / 2.7778 °C deltas, ASHRAE 90.1-2022 §6.4.3.3.2.
- `infiltration_tightening` — **active**. ASHRAE 90.1-2019 Addendum t §11.5.3 formulas, target
  0.0017 m³/s·m² at 75 Pa from §5.4.3.1.1. **Honest coverage limit that must be quoted with any
  saving:** only `Flow/Area` and `Flow/ExteriorWallArea` objects are covered; `Flow/Zone` and
  `Flow/ExteriorArea` have no formula in the cited clause and are declined by design, which is the
  majority of infiltration objects in today's prototype library.

## 3. Everything new is OFF, and nothing is wired into the build path

Four flags, all `False` in `openubem/config.py`: `ENVELOPE_PATCH_SKIP_WHEN_BETTER` (:112),
`PREP_ABORT_ON_FAILURE` (:123), `PV_INJECTION_ENABLED` (:223), `SCENARIO_LAYER_ENABLED` (:224).

`openubem/idf/pv.py` and `openubem/scenarios/` are **libraries that nothing calls**. That was a
deliberate ruling (SR-H2, block 4), not an oversight. **Do not wire them up without the user asking.**
No published OpenUBEM number has moved in this whole arc.

## 4. Must not start without the user asking

- **C04**, the per-archetype per-end-use regression fixture (block 1).
- The pre-existing **Warehouse `auto`-mode IDF failure** — known, out of scope.
- **D9**, the prototype IDF library that lives inside idf_reader.
- Rewriting OpenUBEM's existing table-driven **envelope applier**.
- **Racking / `Shading:Building:Detailed`** for PV, and inter-row shading.
- Writing anything into **`05_results`**.
- Wiring `pv.py` or `openubem/scenarios/` into the build path.
- **Any EnergyPlus run** for this arc. Nothing here has been simulated; that is correct and
  intentional. If simulation is ever approved: it is never sequential — `sbatch --array ... %32` on
  Speed, or a local pool of 20.

## 5. Standing rules this arc earned — carry them forward

These are not style preferences. Each one was written after a defect that a fully green test suite
had failed to catch.

1. **Audit by measurement, never by report.** Re-run the executor's own commands yourself, then run
   the artifact against a **real DOE prototype IDF** and read the numbers. Both of the two serious
   defects in this arc (J03-D1, J04-D1) were found this way, and in both cases the executor's suite
   was 100 % green.
2. **A measure that edits a `Schedule:Compact` ships with at least one test whose schedule is copied
   verbatim from a real prototype block, not hand-written. A measure with only synthetic schedule
   tests is not tested.**
3. **Where a cited standard states a quantity directly, no OpenUBEM convention may restate it.** A
   convention is admissible only for a case the standard does not cover at all, and the measure must
   **gate** what it cannot cite rather than reach it through a convention. J04-D1 was exactly this
   failure, and the fix was to delete the invented rule, not to tune it.
4. **Withdraw, don't tune.** A measure that cannot be defended ships `"status": "withdrawn"` with a
   written `withdrawn_reason`, and is restored only by a separate task after re-verification.
   `apply_measure` short-circuits a withdrawn measure, so tests of corrected logic must call the
   applier internals directly.
5. **The manager owns its own spec's defects.** J04-D1 came from the manager's own task spec; the
   audit note says so. Attribute honestly, or the next spec repeats it.
6. **Register every solved error** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before
   closing the task, and **search it before debugging anything**.
7. **Fail closed with a named gate.** Every declined case gets its own gate name in the measure's
   `gates` list; unknown input is never approximated.
8. **Close a plan doc past ~1,100 lines** and carry remaining scope into the next block. Block 5's
   doc reached 1,217 lines and is due for this — see §7.

## 6. Dispatch recipe, and the traps that have actually bitten

**Recipe.** One brand-new Sonnet session per task. Dispatch a verb and exact commands, never a
question. Cap every command's output (`head -30`, `grep -c`, `--stat`). Split long agents at task
boundaries. **Never re-check a finding with a second agent** — re-run the one command yourself.

**Audit target.** The realistic measurement file used throughout lane J:
`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`
— read and measured by the manager only, never copied, never referenced by a test.

**Traps to hand to every executor, verbatim:**

- Windows paths inside `python -c` raise
  `SyntaxError: (unicode error) 'unicodeescape' codec ... truncated \UXXXXXXXX escape`. Use raw
  strings, ASCII only.
- `/tmp/...` gives `FileNotFoundError` — Git Bash `/tmp` is unresolvable by Windows Python. Use the
  session scratchpad with a Windows path.
- `WebFetch` fails with `getaddrinfo ENOTFOUND`: the executor sandbox has **no outbound DNS**. Any
  standard or source must be fetched by the manager and pasted into the task spec.
- Bash heredocs into a file have failed here with
  `unexpected EOF while looking for matching '`. Write the fragment with the Write tool, then
  `cat fragment >> target`.
- PDFs: `WebFetch` cannot parse the standards PDFs, and `Read` on a saved PDF needs poppler
  (`pdftoppm is not installed`). Extract text with `pypdf` into the scratchpad and grep it.

**Semantics an executor gets wrong unless told** (all measured, all cost a re-do):

- A `Schedule:Compact` `Until: HH:MM, value` entry spans from the **previous** until-time to its own.
  Testing the entry's end time to decide occupancy is wrong, and DOE prototype workday until-times
  (05:00/06:00/07:00/22:00/24:00) put nothing inside a 07:00–18:00 window.
- DOE prototypes write `For SummerDesignDay` **without a colon**, so `startswith("for:")` silently
  misses every design-day block.
- A temperature **difference** converts ×5/9 with no 32° offset.
- Clone shared schedules, never mutate them; cap the clone at `len(original.fieldvalues)` because
  eppy's `fieldnames` returns the IDD extensible maximum (10001).

## 7. Decision resolved 2026-09-18

User answered: close block 5, open block 6, **housekeeping only** — no task in block 6 is authorized
yet. `PLAN_techtransfer-block5-2026-09-17.md` carries a 🔒 CLOSED banner naming its successor.
`PLAN_techtransfer-block6-2026-09-18.md` is open, parked, empty progress log — its §2 lists every
remaining item (C04, wiring PV, wiring scenarios, flipping any of the four flags, any EnergyPlus run,
plus the pre-existing out-of-scope items) and the gate on each: a specific user ask, item by item.
Nothing starts in block 6 without that ask.

## 7a. Execution authorized 2026-09-18 — run block 6's list consecutively

User instruction: run the block 6 list in order, no per-item pick needed. Recorded at
`PLAN_techtransfer-block6-2026-09-18.md` §2a with the execution order (C04 → PV validation run → PV
build-path wiring → scenario wiring → remaining flag flips → any fleet-scale EnergyPlus run). Two
items in that order still need one specific input, not a style choice, and are not skipped by this
authorization: reversing SR-H2 (PV wiring) needs the one measured EnergyPlus proof it names; wiring
`openubem/scenarios/` needs the user's packaging-design pick (block 5 §1b) before a campaign can be
built at all. Neither blocks the other items.

**Dispatched 2026-09-18:** C04, fresh sonnet executor, task spec in block6 §2a. Awaiting report;
manager audits before item 2 starts.

## 7b. FLEET-06b local run in flight — user is closing this session 2026-09-18

**Read this before touching FLEET-06 anything.** The user is closing this Claude Code session while
FLEET-06b (65,112-case EnergyPlus batch, the third item in the block 6 execution order) is still
running. It is expected to keep running unattended and be found still going (or finished) when a
fresh session next opens this file.

**What changed from §7a/§4's "no EnergyPlus run" default:** the user explicitly authorized and is
running FLEET-06b — this is not a violation of §4's "any EnergyPlus run" gate, it is that gate being
exercised. Full decision trail is in `PLAN_techtransfer-block6-2026-09-18.md` §2a–§2e (packaging,
write-slot, task spec, the original Speed array-split, and **§2e: local-only override**).

**§2e in one line:** the user was running unrelated jobs on the Speed cluster at the same time, ruled
this fleet run not urgent, had the two Speed jobs for it (`1330058`, `1330087`) withdrawn, and directed
the remaining ~65k cases to run locally instead — a deliberate, explicit override of the standing
🔴 "parallel, Speed first" rule in `CLAUDE.md`, not an oversight. Do not resubmit to Speed without a
fresh ask.

**Ground truth lives on disk, not in any agent's memory:**
- `%TEMP%\ubem_validation\fleet06b_local_2026-09-18\progress.json` — `{done, failed, remaining, total,
  timestamp}`, rewritten every ~2 minutes while the run is alive.
- `...\results.csv` — one row per finished case (`building_id,cell_name,...,status,wall_clock_s,...`).
- `...\run_log.txt` — append-only log, including the benchmark summary and every worker-count change.
- `...\benchmark_result.json` — the one genuine local timing measurement (30 real EnergyPlus runs,
  mean 16.68 s, min 5.01 s, max 53.99 s, 14 workers) — the only legitimate basis for any ETA math.
  **Never** extrapolate from the Speed cluster's own timing or vice versa (debug reference line 1595).

**Check these three things first, in order, before doing anything else with FLEET-06b:**
1. Is a run still alive? `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` for
   `fleet06b_local_run_2026-09-18.py full`, or just check whether `progress.json`'s timestamp is
   recent (within a few minutes) versus stale.
2. If it died with the session close (i.e. the Task Scheduler detachment below was never confirmed,
   or wasn't reached before close): relaunch it exactly as documented in the block6 plan doc's
   FLEET-06b progress-log entry (once written) — it is resume-safe, skips any `building_id`+
   `cell_name` pair already present in `results.csv`, **never restart from zero**.
3. If it finished (`remaining == 0` in `progress.json`): do not re-run anything. Proceed straight to
   FLEET-06c (harvest into `05_results`) per the unmodified task spec already in the block6 plan doc —
   fresh Sonnet executor, brand-new session, gate = 100 % COMPLETED/FAILED, no schema change, baseline
   cell's fleet EUI sanity-checked against 153.95 with the delta stated plainly.

**Detachment from this session:** the run was originally a direct child of this session's process tree
(confirmed by process inspection — closing the session would very likely have killed it), so it was
being relaunched via `schtasks /create /tn "OpenUBEM_FLEET06b" ...` (Windows Task Scheduler) to survive
independently, with a `CREATE_BREAKAWAY_FROM_JOB` Popen fallback if Task Scheduler was unavailable.
**Whether that relaunch was confirmed before the session closed is not guaranteed** — check step 1
above rather than assuming it worked. `schtasks /query /tn "OpenUBEM_FLEET06b" /v /fo list` shows
whether the scheduled task exists and its last run result.

**Local resource cap:** 5 workers as of 2026-09-21 (halved from 10 — see §7e; the earlier "10, not 20"
reasoning below is superseded). Do not raise or lower it again without a fresh ask.

**Live monitor artifact:** `https://claude.ai/artifact/6H6xkLiazkjN2akF6wsXKa` (a `db`-capability page,
collection `fleet06b`, doc `progress`), pushed to at every 1 % mark by the executor agent that was in
flight when this note was written. **That agent almost certainly does not survive this session
closing** — treat the artifact as possibly stale and re-seed it from `progress.json` (same field shape:
`total, done, failed, remaining, workers, mean_s, min_s, max_s, updated_at`, plus an `events` array) the
next time anyone checks on this, rather than trusting its last-shown numbers.

**Do not double-dispatch.** Before spawning anything new for FLEET-06b/06c, check for a still-running
process (step 1 above) and check `ListAgents` for an agent still actively working this task — only
treat it as dead and start fresh once both come back empty/stale.

**Still unreconciled, low priority:** the block6 plan doc's own FLEET-06b progress-log entry (§4) is
stale — it still reads "STOPPED 2026-09-18 (spec conflict, no job submitted)" from an earlier abandoned
attempt, even though jobs were later actually submitted to Speed, then withdrawn, then this local run
started. Worth a correction pass once FLEET-06b actually completes and gets its real completion entry
written — not urgent, not user-requested yet.

## 7c. FLEET-06b tracker froze 2026-09-19, rebuilt 2026-09-20 — read this before touching FLEET-06b again

**The simulation itself never stopped.** Only the live process's own checkpoint thread inside
`cmd_full()` in `fleet06b_local_run_2026-09-18.py` froze — last `run_log.txt` / `progress.json` write
was 2026-09-19 13:55:47 (done=17,622). The EnergyPlus worker pool (still 10 processes, unchanged) kept
launching and finishing new cases the whole time, just unrecorded. Windows Task Scheduler still showed
the job `OpenUBEM_FLEET06b` as "Running" throughout, never crashed or exited. Likely cause: an unofficial
background cleanup script (`sweep_fleet06b.ps1`, not part of the pipeline, origin unknown — not written
by any documented dispatch) was running concurrently, gzip-compressing finished cases' `eplusout.sql` to
`eplusout.sql.gz` and deleting the original; its own log also stalled mid-pass at 2026-09-19 15:33
("packed=5000") and the process is now dead (confirmed via process list 2026-09-20). Likely disk-I/O
contention between the two caused the run's aggregator thread to hang while workers kept going
independently.

**Correction to an earlier claim in this session's chat:** resume safety does NOT depend on
`results.csv`. `cmd_full()` decides what to (re)run via `openubem.simulation.parallel.is_completed()`,
which checks each `work_dir` on disk directly (`eplusout.end` + `eplusout.sql` present, success marker in
`.end`). So the tracker freeze never put compute at risk of being wasted on restart — `results.csv` only
matters for the eventual FLEET-06c harvest / analysis step, not for resume.

**One real risk from the freeze:** cases whose `eplusout.sql` was swept to `.sql.gz` by the (now-dead)
cleanup script look *incomplete* to `is_completed()` (it only checks for `eplusout.sql`), so they would be
needlessly rerun on any restart, and the FLEET-06c harvest will need to accept `.sql.gz` too or decompress
first. As of the last rebuild (2026-09-20 10:34), 345 finished cases are in this state; the sweep script
is dead so the count will not grow further, but it will not shrink either without either decompressing
those files back or teaching downstream code to read `.sql.gz`.

**Tracker rebuild tool:** `scripts/analysis/fleet06b_tracker_rebuild_2026-09-20.py` — read-only against
the live run, scans `out/<cell>/<building_id>/` for `eplusout.end` not yet in `results.csv`, classifies
each exactly like `openubem.simulation.runner.classify_outcome` would, appends the missing rows, backs up
the old file to `results.csv.bak_rebuild`, and rewrites `progress.json` to match. Run it again any time
`results.csv`'s row count looks stale versus `find <out> -name eplusout.end | wc -l`. It was run three
times on 2026-09-20 (10:08, 10:20, 10:34), recovering 18,954 + 78 + 49 completions respectively.

**Last known snapshot at session close (2026-09-20 10:34:12):** 36,538 success + 22 failed = 36,560 of
65,112 done, 28,552 remaining. At the observed (not benchmark) pace this is roughly 2 more days, not the
original ~22 h benchmark estimate — the benchmark's 16.68 s/case mean does not hold under real load;
measure fresh from `results.csv`/disk deltas rather than trusting `benchmark_result.json` for any ETA.

**Live monitor artifact:** `https://claude.ai/artifact/6H6xkLiazkjN2akF6wsXKa` (db-capability page,
collection `fleet06b`, doc `progress`) was reconnected and pushed with real numbers on 2026-09-20. An
hourly session-only cron job (`076e4f4d`, fires :07 past the hour) was refreshing it plus printing a
`[timestamp] progress: done=X/65112 failed=Y remaining=Z` line in chat — **that job dies when the session
that created it closes** (session-only, per `CronCreate`'s own documented behavior), so it is gone as of
this session ending. The artifact page itself persists and still shows the last pushed snapshot, but it
will go stale exactly like `run_log.txt` did unless a future session either re-runs the rebuild script and
pushes a fresh `ArtifactData` update, or re-arms a cron/loop. Not restarted automatically — needs a fresh
ask.

## 7d. FLEET-06b real halt 2026-09-20→2026-09-21 — no auto-restart, resumed manually

**Confirmed by disk/process audit 2026-09-21 12:33:** the run had actually stopped (zero new
completions for ~26 h, `run_log.txt` last real write at session close, no `python.exe`/`energyplus.exe`
processes alive), not just a tracker freeze like §7c. The scheduled task `OpenUBEM_FLEET06b` is
`Schedule Type: One Time Only` with `Next Run Time: N/A` and `Logon Mode: Interactive only` — it has
no self-restart if the process it launched ever exits, for any reason (crash, or the originating
session closing before independent detachment was confirmed, per the risk flagged in §7b). Windows
kept no Task Scheduler operational log (disabled) and no shutdown/logoff events in that window, so the
exact trigger could not be proven from logs — only that nothing would have restarted it automatically.

**Second risk found and fixed before resuming:** 10,337 completed cases' `eplusout.sql` had been
gzip-compressed to `.sql.gz` (up from the 345 in §7c) by the same dead cleanup script's leftover state;
`is_completed()` only recognizes an uncompressed `.sql`, so these would have been wastefully re-run.
Decompressed all 10,337 files (`gunzip`, reversible, ~2 min) before resuming.

**Resumed 2026-09-21 12:45:59** via `schtasks /run /tn "OpenUBEM_FLEET06b"`: 10 workers active,
36,538 already-done cases correctly recognized, 28,574 picked up as pending. No auto-restart exists —
if this stops again, it needs a person to notice and manually rerun it; not fixed since not asked.

## 7e. Worker count halved 10→5, 2026-09-21 (fresh user ask, CPU load complaint)

User reported the run was pinning local CPU and asked to cut concurrency in half. `MAX_WORKERS` in
`scripts/analysis/fleet06b_local_run_2026-09-18.py:90` changed from `10` to `5` (old value/comment kept
below it, marked superseded, for provenance). Since the constant is only read at process start, the
live run was stopped (killed the dispatcher `python.exe`, its orphaned `multiprocessing-fork` workers,
and all `energyplus.exe` children — safe: `is_completed()` resume logic means nothing already finished
was lost) and relaunched via `schtasks /run /tn "OpenUBEM_FLEET06b"`.

**Confirmed 2026-09-21 13:33:27:** `run_log.txt` shows `already_completed=36766 pending=28346
max_workers=5`; exactly 5 `energyplus.exe` processes running (was 10). Do not raise this back to 10
(or change it at all) without another fresh ask — see updated §7b's "Local resource cap" note.

## 7f. Disk full halt + 2,761 results lost, 2026-09-22 — restarted 20:55

**Halt:** the run stopped 2026-09-22 19:26 (last `run_log.txt` progress: done=56,119) because `C:` was
100 % full (277 MB free). The output tree was ~789 GB, ~14 MB/case (`eplusout.sql` 8.4 MB +
`eplustbl.htm` 5.6 MB; all other retained files are tiny). Input folders `fleet06a_campaign` (65,112
IDFs), `fleet06a_rebuild` (weather) and `fleet06a` (baseline IDFs) are still read by the run — do not delete.

**Loss (manager error):** a cleanup ran an exclusion-based `find -delete` in `out/` while a second
Claude session was concurrently running `xargs -P 12 gzip -f` on `eplusout.sql`. The fresh `.sql.gz`
files were deleted: 2,761 finished cases lost their results (list:
`%TEMP%/ubem_validation/fleet06b_local_2026-09-18/lost_sql_2026-09-22.txt`). They re-simulate
automatically. The HTML reports were all kept (56,124).

**Restart:** pending check in `scripts/analysis/fleet06b_local_run_2026-09-18.py:286` now also counts
`eplusout.sql.gz` + success `.end` as finished (user said "start runs"). Relaunched via `schtasks`
2026-09-22 20:55:33: already_completed=53,396, pending=11,716, 5 workers. Measured pace 648 cases/h
(19,332 in 29.9 h, 5 workers) → ~18 h. Monitor artifact updated (db doc `fleet06b/progress` v9).

**User ruling 2026-09-22:** after the run completes and the FLEET-06c harvest numbers are checked,
delete all `eplusout.sql` / `.sql.gz` (~450 GB). Not before. FLEET-06c must decompress or read
`.sql.gz` before `parse_building`.

## 7g. Local run stopped, remainder moved to Speed — 2026-09-23 (fresh user ask, CPU load complaint)

**§7b/§2e's "local only" is superseded from this point.** User asked 2026-09-23 to move whatever was
left off the local machine onto Speed (CPU load complaint again — this is the "fresh ask" §2e/§7b
required before any resubmission). Full decision + task spec: block6 plan doc §2f. Do not read §7b's
"local resource cap" note as still current — there is no local run anymore.

**State at the switch:** done=61,739, failed=29, remaining=3,373 of 65,112 (94.8%). The local process
tree was force-killed (`schtasks /end` alone left `energyplus.exe` children running — needed
`taskkill /T /F` on the dispatcher PID), the `OpenUBEM_FLEET06b` scheduled task deleted. The finished
61,739 cases were not touched or re-run.

**Speed job `1342940`**, `--array=1-3373%32 --time=7-00:00:00`, submitted ~09:53 2026-09-23, reusing
the already-staged `/speed-scratch/o_iseri/openubem/fleets/fleet06b_2026-09-18/` (idfs/weather from
2026-09-18, still intact — no re-staging needed) plus a new `fleet_remaining.lst` filtered to just the
3,373 still-pending `(cell_name, building_id)` pairs. Confirmed genuinely running (real EnergyPlus
progress in sampled task logs), not a config-error stub.

**Not yet harvested.** FLEET-06c stays gated on 100% COMPLETED/FAILED across the whole 65,112 (local
61,739 + this Speed job), not just this job finishing. No automated monitor set up — check
`sacct -j 1342940` next session; full progress-log entry is in the plan doc §4 (new entry, marked
`IN PROGRESS 2026-09-23`, superseding the stale `STOPPED 2026-09-18` one).

## 7h. Speed job ended, 28 failures fixed and rerunning — 2026-09-23 (user: "let the all process continue")

**Job `1342940` final:** 3,345 COMPLETED, 21 FAILED, 7 OUT_OF_MEMORY. Fleet total 65,084 ok / 28 failed
of 65,112 (the 29 local failures were in the remaining list; 8 of them succeeded on Speed).

- **21 FAILED = PV generator-list overflow** (3 buildings × 7 non-baseline cells: way_381810555,
  way_425993519, way_427278443). Fixed in `openubem/idf/pv.py:47` (`MAX_GENERATORS_PER_LIST = 30`) and
  `:225-262` (chunked Generators/Inverter/Distribution triples); `tests/test_pv_injection.py` +
  `tests/test_pv_validation_run.py` 21 passed (re-run by the manager 2026-09-23). The 21 IDFs were
  regenerated and re-uploaded (md5-checked). Debug entry closed (`OpenUBEM_debug_References.md`, ch. 13).
- **7 OUT_OF_MEMORY = way_281344894** in the non-baseline cells at `--mem=6G`. Rerun at `--mem=32G` on the
  CLI; the shared `submit_fleet06b.sbatch` was not edited.
- **Rerun job `1346459`**, `--array=1-28%32 --mem=32G --time=7-00:00:00`, list `fleet_rerun28.lst`; the
  exact 28 `out/<cell>/<stem>/` dirs were deleted first. At 14:16: 6 COMPLETED (mean ~10 min each),
  1 RUNNING, 21 PENDING with reason `AssocGrpCpuLimit` — the account's 64-CPU cap is full of other
  projects' jobs (histnu 32, wp11_draw_task 6×5, p5_bootstrap 1). **User ruled: leave everything
  running; never touch the other projects' jobs.**
- Monitor artifact `https://claude.ai/artifact/6H6xkLiazkjN2akF6wsXKa` (db `fleet06b/progress`, v11)
  shows the rerun state.

**Next session:** superseded by §7i (the rerun was cancelled with 15 of 28 tasks unfinished).

## 7i. Rerun `1346459` cancelled by the user, 2026-09-23 18:37 — Speed is full, resume later

User asked to cancel everything on Speed and return when resources are free. Only job `1346459`
(`openubem_fleet06b`) was ours; the other queued jobs (`histnu`, `wp11_draw_task`, `wp11_scorer`) belong
to other projects and were not touched.

- **Final state of `1346459`:** tasks 1–13 COMPLETED; tasks 14 and 15 were RUNNING and are CANCELLED; tasks
  16–28 were still PENDING (`AssocGrpCpuLimit`) and are CANCELLED. `squeue` shows zero OpenUBEM jobs
  (re-checked a second time on 2026-09-23 at the user's request). User is closing this session and will
  return later; nothing is running or scheduled.
- **Fleet total is therefore 65,097 ok / 15 not done of 65,112.** FLEET-06c stays gated on all 65,112.
- **Do not trust `out/<cell>/<stem>/` for indices 14–15:** the cancelled tasks may have left partial output.
  Delete those dirs before resubmitting. Indices 16–28 never started, but delete them too (§7h did the same).
- **To resume (needs a fresh user "go", and free CPUs):** build a list of only the 15 unfinished rows from
  `fleet_rerun28.lst` (lines 14–28), then `sbatch --array=1-15%32 --mem=32G --time=7-00:00:00` on the CLI;
  never edit the shared `submit_fleet06b.sbatch`. Before submitting, check `squeue` for the account's
  64-CPU cap: if it is full again the tasks will sit in `AssocGrpCpuLimit` exactly as before.
- **After all 28 have ended:** check each `out/<cell>/<stem>/` has results, then FLEET-06c harvest (plan doc
  task spec; must read `.sql.gz`); after the numbers are checked, delete `eplusout.sql` / `.sql.gz` per §7f.
- Monitor artifact `https://claude.ai/artifact/6H6xkLiazkjN2akF6wsXKa` is now stale (still shows the rerun
  as active).

## 7j. Last 15 cases done on Speed, pull nearly complete, baseline harvest does NOT match yet — 2026-09-25

User: "while waiting for Speed, do all parallel work" → "continue till the end" → 2026-09-25 "update the
manager prompt, I continue in a new session". Nothing is running on Speed for OpenUBEM.

- **Speed job `1348381`** (the 15 unfinished rows of `fleet_rerun28.lst`, list `fleet_rerun15.lst`, remote
  dirs deleted first by `scratchpad/prep15.sh`): **all 15 COMPLETED** (sacct 2026-09-25 08:39, 15–70 min
  each, no OOM). Their folders are still only on Speed:
  `/speed-scratch/o_iseri/openubem/fleets/fleet06b_2026-09-18/out/<cell>/<stem>/`. **Pull them next.**
- **Pull to local `%LOCALAPPDATA%\Temp\ubem_validation\fleet06b_local_2026-09-18\out\`:** 65,105 folders
  on 2026-09-25 (baseline 8,139, every other cell 8,138). The 7 missing are expected to be among the 15
  re-runs — confirm by listing, not by assuming. One `tar`/`ssh` process was still alive; check it has
  ended before starting a new pull. No background watcher is running (two were killed for low memory —
  do not restart them). 30 older local dirs were moved to `out_superseded_local\` (not deleted).
- **5 stale baseline cases fixed:** `way_1008727470`, `relation_13781131`, `way_1008727469`,
  `way_1020754974`, `relation_7480583` had a success `eplusout.end` from 09-18 but a truncated sql from the
  09-22 disk-full event. Old dirs moved aside as `*_stale_2026-09-24`, re-run locally, all 5 now match T08.
  Registered: `OpenUBEM_debug_References.md:1800`. With them, the local runner's own parse gives the fleet
  baseline **153.9501287 over 8,139 = the published 153.95012856722067** (0 buildings off by >0.01).
  `is_completed()` (`openubem/simulation/parallel.py:73`) trusts a stale `.end` — never use it alone.
- **Plan amendments** (block-6 plan, section `## 2g` + "Amendment 2g-1"): harvest is per (scenario cell ×
  geo cell) through `aggregate_results()`; the 57-col Step-2 table is rebuilt per geo cell with
  `step2_classify_enrich()` (seeded, code unchanged since `9d6026af`), guarded on `archetype_id` matching
  `03_idf_manifest.parquet` 100 %, saved once in `_step2\<geo>\02_enriched.gpkg` and reused for all 8 cells.
- **Baseline harvest ran** (`scripts/analysis/fleet06c_harvest_2026-09-24.py`, output
  `%TEMP%\ubem_validation\fleet06c_harvest_2026-09-24\baseline\<geo>\05_results.*`): 12 geo cells, 8,139
  rows (matches T08 per cell), 0 null totals, schema sidecar in each, **86 columns (not the 70 the DESIGN
  expects — code grew; accept after a check)**. Old 38-col diagnostic kept in `_diag_38col_2026-09-24\`.
  The executor's own final report was never received — audit from disk.
- 🔴 **Baseline harvest gives 175.74 kWh/m², not 153.95. Two causes, measured:**
  1. District hot water is now counted: `dhw_district_eui_kwh_m2` adds 20.09 (this is the known
     under-count of the published number, OPEN-65, +19.97 on a subset).
  2. Floor area: 8,134 of 8,139 rows have `floor_area_provenance = footprint_fallback`, because the case
     folders hold no `eplusout.eio` (only csv/end/err/mtr/sql/htm/log); `parser.py:503–525` then falls
     back to footprint area. Harvest area 23.42 M m² vs T08 23.87 M m² (694 buildings off >1 %).
  3. Minor: energy without district is 0.8 % below T08 kWh; 129 buildings off >0.1 %. Not yet explained.
  Without district and on T08 areas the harvest gives 152.70.
- **Decisions owed by the user (asked 2026-09-25, not answered yet):** count district hot water in the
  FLEET-06 tables (recommended yes = OPEN-65 ruling). Manager-side fix, no user decision needed: floor area
  must come from the simulation (sql zone table, as T08 did), not footprint — amend plan §2g, re-run the
  baseline harvest, then re-audit: 8,139 rows, all area provenance from simulation, fleet figure equals
  153.95 excluding district (or state the new figure including district), explain or bound the 129.
- **Then, in order:** pull the 15 re-run folders; verify all 65,112 have a success `.end` + sql/sql.gz;
  fresh Sonnet harvests the other 7 scenario cells reusing `_step2` (tests: rows, columns, sidecar, count
  of buildings with PV > 0); append FLEET-06b COMPLETED and FLEET-06c entries to the plan progress log;
  optionally refresh monitor artifact `6H6xkLiazkjN2akF6wsXKa`. **Never delete the ~450 GB of sql files
  without an explicit user yes.**

## 7k. District hot water counted, all 65,112 cases on disk, baseline re-harvest running — 2026-09-25

User 2026-09-25 (verbatim): "yes of course, count district hot water. secondly, as we close all the
simualations colelct the results update the tables, then delete unnecessary files of the simulations to
prevent low memory warning". This is the explicit yes to delete that §7j asked for, **scoped to after the
tables are written and audited**. Full task list: block-6 plan `## 2h` (FLEET-06c-FIX, -BASE, -ALL, -TABLE,
§2h-4 cleanup).

- **District hot water is counted** in every FLEET-06 table (`dhw_district_eui_kwh_m2` stays inside
  `total_eui_kwh_m2`). The +20.09 in the first harvest is this ruling, not a defect.
- **Floor-area cause found (supersedes §7j cause 2 and 3):** T08 took area from `eplusout.eio`, not the sql.
  Local folders and the gz temp copies have no eio, so area fell back to footprint and the OPEN-60 zone
  multiplier map (`openubem/results/parser.py:984-994`) was empty — that is the 0.8 % / 129-building gap.
  The sql `Zones` table gives the same area (142,456.77 vs eio 142,457.04 m² on one case). §7j cites
  `openubem/simulation/parser.py`; the real file is `openubem/results/parser.py`.
- **Pull done (PULL_OK):** all 8 cells × 8,139 = **65,112 folders, 65,112 with a success `.end` + sql/sql.gz**
  (manager count 2026-09-25). The FLEET-06c-ALL gate is met.
- **FLEET-06c-FIX + BASE dispatched** (Sonnet `a95b7d5bfd6be9c4f`): `parse_sql_zone_area` /
  `parse_sql_zone_multipliers` now in `parser.py:496,520`; the baseline re-harvest was running on
  2026-09-25 (12 geo dirs present). Its report was not yet audited — audit from disk with the §2h
  FLEET-06c-BASE test lines (0 footprint_fallback; area within 0.01 % of 23,871,481.58; EUI without
  district within 0.05 of 153.9501; state EUI with district).
- **Then, in order:** FLEET-06c-ALL (fresh Sonnet, 7 cell processes in parallel) → FLEET-06c-TABLE
  (`openubem/outputs/comparisons/fleet06c_scenario_summary_2026-09-25.csv`) → manager audit → §2h-4 cleanup
  (inclusion list only, free space before/after) → FLEET-06b COMPLETED + FLEET-06c entries in the plan
  progress log.
- Monitor artifact `https://claude.ai/artifact/6H6xkLiazkjN2akF6wsXKa` refreshed 2026-09-25 (db
  `fleet06b/progress`: 65,112 done, 0 failed, 0 remaining).
- **FLEET-06c-BASE audited and ACCEPTED (manager, 2026-09-25):** baseline **172.4076 kWh/m² incl. district**,
  152.6985 excl.; 0 footprint_fallback; area within 0.00001 %. The −1.25 vs 153.95 is a **T08 double count**
  (electric cooking + plug refrigeration sub-meters counted on top of equipment on 129 kitchen buildings),
  proven on the SQL meters of `way/55932517`; full audit in plan §2h, debug reference registered. Tests 32/32.
- **FLEET-06c-ALL + TABLE dispatched** (Sonnet `a95fb18daccfc3498`, 7 cell processes in parallel, stops
  before cleanup). Next: audit its per-cell lines and the 8-row table from disk, then §2h-4 cleanup.
- **FLEET-06c-ALL crashed (manager, 2026-09-25 11:20).** 7 cells × 12-way pools = 84 workers at once: all 84
  geo tasks logged `MemoryError` or `PermissionError(13 … being used by another process)` (the latter raised by
  the temp `.sql` unlink at `fleet06c_harvest_2026-09-24.py:199-203`, which catches only FileNotFoundError);
  executor went idle, no table written. Manager deleted the 7 partial cell dirs + their gz temp (161 GB; free
  disk 353 → 514 GB) and relaunched all 84 tasks in ONE 12-worker pool (scratchpad `rerun_all.py`, log
  `scratchpad/logs/rerun_all.log`). Next: on completion, audit per cell, dispatch TABLE to a new Sonnet, then §2h-4.
- **12-worker rerun killed at 12:27 by Claude Code's low-memory reaper, NOT by the harvest (manager, 2026-09-25).**
  The session was idle; Claude Code stops background shells when system RAM is critically low (12 workers ×
  ~3.7 GB peak on 63.5 GB). 0 MemoryError in the log. No python worker survives. **User ruling 12:30: stop here,
  update this prompt, resume later in this session.** State on disk:
  - **22 of 84 pieces saved** (each has `05_results.csv`): all 7 cells × `nyc_urban`, `nyc_centre`, `austin_centre`,
    plus `lighting/la_centre`. **62 missing**: the other 6 × `la_centre`, and all 7 × `la_urban`, `la_suburban`,
    `austin_urban`, `nyc_suburban`, `austin_suburban`, `la_rural`, `austin_rural`, `nyc_rural`.
  - Measured cost per piece (baseline harvest, 12 geos in parallel, ~×1.15 under 12-way load): nyc_centre 42 min,
    nyc_urban 21, la_urban 15, austin_centre 14, la_centre 14, la_suburban 13, austin_urban 9.5, nyc_suburban 9.5,
    austin_suburban 7, la_rural 4.5, austin_rural 4, nyc_rural 4. Remaining ≈ 590 worker-min → **≈ 85 min at 8
    workers**, ≈ 57 min at 12.
  - Leftover temp: `ab6f94ef-…\scratchpad\gz_tmp\` = 71 GB (decompressed `.sql` left by the unlink
    PermissionError + killed pieces). Free disk 448 GB at 12:27. Free RAM 47.8 GB after the kill.
  - Damaged `.sql.gz` (debug ref `OpenUBEM_debug_References.md:1297`, [OPEN]): nyc_urban 4–8 of 1,779 per
    scenario cell; austin_centre 0. **Manager decision (CLAUDE.md "don't chase the last fraction"):** exclude the
    union of `footprint_fallback`/null-EUI buildings over all 8 cells from every table row, baseline included, and
    state the population; do not re-simulate.
  - **Resume recipe (needs the user's "go"; the reaper note forbids an unasked restart):** (1) delete the
    harvest-root dirs of the 62 missing pieces that exist without `05_results.csv` and their `gz_tmp\<cell>\<geo>`
    dirs (inclusion list only); (2) rerun `rerun_all.py` restricted to tasks whose `05_results.csv` is missing,
    `max_workers=8`, largest first; launch it detached (PowerShell `Start-Process`) or with
    `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` in Claude Code's own environment, so the reaper cannot kill it
    again; (3) then audit all 7 cells per plan §2h, count the damaged union, dispatch FLEET-06c-TABLE to a new
    Sonnet, audit the 8-row table, run §2h-4 cleanup (add the 71 GB `gz_tmp`), progress-log entries, final report.

## 8. Executor kickoff prompt (send verbatim, adjust the range)

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\TechTransfer\implementation\PLAN_techtransfer-blockN-2026-09-17.md.
Execute T<start> through T<end> in order. Stop at the first checkpoint after T<end>,
append progress log entries (one per completed task) under the progress-log section of that doc,
run any standalone tests called for in the plan, and report results before continuing.
Do not propose alternatives — execute the plan. If the DESIGN is ambiguous, STOP and quote the conflict.
```

Start narrow (1–2 tasks) with a new executor; widen once it runs cleanly.

## 9. File map for this arc

- Report: `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`
- Chosen vs inherited: `docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md`
- Plans: `docs/docs_ACTIVE/TechTransfer/implementation/PLAN_techtransfer-block{1..5}-2026-09-17.md`
  (block 5 🔒 CLOSED), `.../PLAN_techtransfer-block6-2026-09-18.md` (open, parked)
- Code added: `openubem/idf/ground.py`, `openubem/idf/compliance.py`, `openubem/idf/pv.py`,
  `openubem/scenarios/measures.py`, `openubem/data/scenarios/measures.json` + `PROVENANCE.md`
- Code touched: `openubem/config.py`, `openubem/geometry/envelope_patcher.py`,
  `openubem/geometry/layout_assigner.py`, `openubem/idf/builder.py`,
  `openubem/simulation/parallel.py`
- Tests added: `tests/test_scenario_measures.py`, `tests/test_pv_injection.py`,
  `tests/test_compliance_audit.py`, `tests/test_prep_gate.py`,
  `tests/test_layout_assigner_fit_check.py`, `tests/test_parser_version_robustness.py`,
  `tests/test_envelope_patcher_windows.py`, `tests/idf/test_ground_temperature.py`
- FLEET-06 scripts: `scripts/analysis/fleet06b_local_run_2026-09-18.py` (local runner),
  `scripts/analysis/fleet06c_harvest_2026-09-24.py` (harvest, `--cells` / `--geo`, untracked in git)
- Error register: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
