# PROMPT MANAGER — TechTransfer arc (idf_reader → OpenUBEM)

> **Written:** 2026-09-18, by the manager session that closed block 5 / lane J.
> **Covers:** the whole arc, blocks 1–5, from the report `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`.
> **How to use:** paste everything below the horizontal rule into a **fresh** session that will act
> as manager for this arc. Update this file in place at the close of each block — do not supersede it
> with a new dated copy.
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

**Local resource cap:** 10 workers, not 20 and not the 14 used for the benchmark — the user explicitly
asked to leave half this 20-core machine free for other work. Do not raise it without a fresh ask.

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
- Error register: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
