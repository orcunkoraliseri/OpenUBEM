# Director Prompt — LayoutAssigner DEBUG FIXES — AUTONOMOUS RUN TO COMPLETION

> **How to use:** paste everything below the line into a fresh Claude session (**Sonnet, xhigh reasoning effort**) opened at `C:\Users\o_iseri\Desktop\OpenUBEM`. That session becomes the **director** of the LayoutAssigner debug-fixes plan and runs it **to completion without user intervention**.

---

You are the **director/manager** of the **LayoutAssigner debug-fixes plan** for OpenUBEM. Follow `CLAUDE.md` at the project root. The user is **away and will not answer questions** — this is a fully autonomous run. When the user returns they expect to see the **plan complete**: every task executed, every checkpoint audited and signed, every progress-log entry written, and a final completion report. Deliverables in English.

## 0. Operating mode (overrides any conflicting habit)

1. **NEVER ask the user anything.** No clarifying questions, no sign-off requests, no "should I proceed?". If a task's own text says "stop and ask the manager" (e.g. T07's geometry-fix branch), that means **you** (the director) decide it yourself, log the decision and rationale, and keep going — there is no other manager to ask.
2. **You spawn the employees yourself**, inside this session, using the **Agent tool (subagent sessions)**. Do NOT write prompts for the user to paste elsewhere. Each employee = one fresh subagent given a task range from the plan.
3. **You direct until the end.** After each employee returns: audit → fix (via a new employee) or greenlight → dispatch the next range. Loop until the plan is done. Do not stop between checkpoints; self-sign each one after a real audit.
4. **Progress log discipline (mandatory at EVERY step):** after every completed task, verify the employee appended its §7 entry in `PLAN_debug_implementation.md` (write it yourself if the employee failed to); after every audit/checkpoint, append your own `#### CP-X — AUDIT` entry there too; tick §0 checkboxes as you go (tasks after their §7 entry exists, checkpoints only after your audit).
5. **Error protocol:** any error, test failure, deviation, or new defect must be recorded in **TWO places**: (a) the §7 progress log entry of the affected task, and (b) the **§8 Error Log** of `PLAN_debug_implementation.md` (continue the numbering from the closed arc — the next new defect is `E-LA-11`, format specified in §8). An error is only "closed" in §8 when the retest is green.
6. **If truly blocked** (a task cannot be completed after 2 distinct fix attempts): do NOT invent a workaround that violates the plan. Record the blocker in §8 with status `OPEN-BLOCKED`, mark the task `[~]` in §0, skip to the next task that does not depend on it, and list all open blockers prominently in the final report.
7. **🔴 THE #1 FAILURE MODE ON THIS ARC — READ THIS TWICE.** Two separate employee sessions on the *previous* phase of this same arc independently made the identical mistake: they submitted or checked on background/cluster work, then **ended their turn believing an external "job finished" notification would arrive on its own** — it never does, for either an employee subagent or for cluster jobs it submitted. Nothing pings a subagent. Nothing pings you either, once you dispatch T11's cluster sweep, except the employee YOU dispatched finishing its own turn. **Rule: whenever you or an employee is waiting on `sacct`/`squeue` state, the ONLY correct pattern is an actual bash sleep-loop that re-checks and only stops once the real state changes — never end a turn on the assumption that something will notify you.** Bake this explicitly into T11's employee dispatch (§3 below already does).

## 1. Read first (in this order)

1. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/PLAN_debug_implementation.md` — **the binding contract for this run.** §0 live checklist, §1 executor hard rules, §2 file layout, §3 dependency decisions, §4 manager-verified facts (line-cited against the current code and the closed arc's error log), §5 tasks T01–T11, §6 stop-and-report points, §7 progress log, §8 error log.
2. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/implementation_plan.md` §9 (Error Log) — read the full `E-LA-06`/`E-LA-07`/`E-LA-08`/`E-LA-09`/`E-LA-10` entries in the CLOSED arc's own words; these are the root-cause investigations this plan's fixes are built on. **Do not re-derive these facts — they are already measured and cited by line number in the debug plan's §4.**
3. `openubem/geometry/layout_assigner.py` lines 260–355 (`_ABSOLUTE_LOAD_SPECS`, `_UNCONDITIONAL_ABSOLUTE_SPECS`, `scale_baseline_idf()`) and `openubem/idf/builder.py` lines ~434–474 (the `layout_assign` branch and its exact function-call order) — read these directly, do not assume the plan's citations are still accurate if the code has moved since 2026-07-23.

Do **not** re-open or re-litigate the CLOSED arc's own §8/§9 — it is a frozen historical record; if you need to reference something from it, cite it, do not edit it.

## 2. State at handoff (2026-07-23)

- The main LayoutAssigner arc is **CLOSED** (CP-E signed): full 12-cell/8,160-building cluster sweep done, 7,887/8,160 (96.65%) succeeded. `layout_assign` is adopted for high-fidelity zone/HVAC-topology studies but **not yet production-grade for fleet-level EUI reporting**, pending exactly the 4 defects this plan fixes.
- Raw harvest data from that closed run is at `openubem/outputs/comparisons/t17_layout_assign_eui.csv` (8,160 rows, building-level) and `t17_layout_assign_cell_summary.csv`. **Use these directly** to pick real failed/anomalous buildings for T03/T05/T06/T07/T09's retests — do not invent synthetic scale factors when a real one is sitting in this file.
- Nothing in this debug plan has been dispatched yet; every §0 box in `PLAN_debug_implementation.md` is unticked.
- Baseline library (unchanged from the closed arc): `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231` (25 unique files, E+ 23.1). **Never hand-edit a baseline file directly** without treating it as a major, separately-flagged decision (see plan T09's own caution about this) — it's shared infrastructure.
- `envelope_patcher.py` (T16 of the closed arc) already runs in the pipeline between `patch_location_and_weather()` and `parse_baseline_zones()`/`write_outputs()` — leave its architecture alone, this plan's fixes are all inside `scale_baseline_idf()`'s field-spec tuples (T01/T04) or new investigation (T06/T08).

## 3. Execution sequence (run it all, in this order)

| Step | Who | What |
|---|---|---|
| 1 | Employee A | T01–T03 (E-LA-10 fix: add `WaterHeater:Mixed.Peak_Use_Flow_Rate` to the scaling spec, audit for siblings, local retest on real cluster-observed buildings) |
| 2 | Director | **CP-A audit** (see §5) → fix loop if needed → sign, tick, log |
| 3 | Employee B | T04–T05 (E-LA-07 class 1 fix: add `FluidCooler:TwoSpeed` capacity fields, local retest on real failed `LargeOffice` buildings) |
| 4 | Employee C | T06–T07 (E-LA-07 class 2 / E-LA-08 investigation + fix-or-confirm-blocked) — **genuine open-ended investigation, no prescribed answer; if the finding points to anything beyond a simple missed scaling field (e.g. a geometry-level fix), the employee must stop and report back to YOU rather than freelance a fix shape this plan didn't pre-authorize** |
| 5 | Director | **CP-B audit** → fix loop → sign, tick, log |
| 6 | Employee D | T08–T09 (E-LA-09 investigation + fix-or-confirm-blocked on `Outpatient`'s Controller List Fatal) — same caution: if the root cause turns out to require editing the shared baseline library file itself, the employee stops and reports to YOU before touching it |
| 7 | Director | **CP-C audit** → sign, tick, log |
| 8 | Employee E | T10 (full local regression: every archetype touched by this plan + the original 6 T12 archetypes, zero new regressions) |
| 9 | Director | **CP-D audit** (local regression gate) → sign, tick, log — **do not let T11 (real cluster compute) start until this is genuinely green** |
| 10 | Employee F | T11 (full 12-cell/8,160-building cluster re-sweep + harvest, new filenames `t18_*`, before/after comparison vs. `t17_*`, results-doc update) — **dispatch this employee with the explicit instruction from Operating Mode rule 7: it must self-poll `sacct` in a real sleep-loop (≥30 min between checks per CLAUDE.md's cluster monitoring rule) and must NOT end its turn assuming a notification will arrive. If it stalls anyway, resume it with a correction exactly as needed — do not just wait indefinitely yourself either; you are also subject to rule 7.** |
| 11 | Director | **CP-E audit** (final production-readiness reassessment) → sign, tick, log |
| 12 | Director | Final completion report (see §6) |

**Employee dispatch rules:** give each employee the plan path (`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/PLAN_debug_implementation.md`), its exact task range, the plan's own §1 hard rules, the instruction to append §7 entries + tick §0 (tasks only), and "if the plan is ambiguous or conflicts with the code, STOP and report the conflict back to YOU (the director) — you resolve it against plan §4 and log the ruling, never invent a plan-violating workaround." Default-effort Sonnet subagents for execution; the T06/T08 investigation employees may warrant higher effort given they're genuinely open-ended. If an employee returns its own plan instead of executed work, reject it and re-dispatch.

## 4. Progress log formats (enforce exactly)

Task entry (employee-written, §7 of the debug plan):
```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + plan/§4 cite>
- Test status: <pytest summary / real-EnergyPlus retest table>
- Notes: <auditor-relevant>
```

Audit entry (director-written, §7):
```
#### CP-X — AUDIT — signed YYYY-MM-DD
- Scope: T..–T..
- Verdict: PASS | PASS-with-fixes (list) | partial (open blockers listed)
- Evidence: <test totals, files verified, real-EnergyPlus before/after numbers if applicable>
- Errors this range: <none | §8 IDs>
```

New defect entry (whoever finds it, §8 — continue numbering from E-LA-10):
```
#### E-LA-<nn> — <short title> — <CLOSED | OPEN-BLOCKED> — YYYY-MM-DD
- Task: T<XX>
- Symptom: <exact error / failing assertion / wrong output>
- Root cause: <what was actually wrong>
- Resolution: <fix applied, or why blocked>
- Files touched: <paths>
- Retest: <result, or "n/a (blocked)">
```

## 5. Audit checklist (each time an employee reports)

1. One §7 entry per task, format conformant, deviations cited against the plan or §4.
2. Pytest summary attached and re-runnable; full regression suite (`pytest tests/test_layout_assigner.py tests/test_zoning.py tests/test_idf_builder.py tests/test_envelope_patcher.py tests/test_results_parser.py -q`) still green at every checkpoint from CP-A onward.
3. Only the files the task named were touched (check `git status` — read-only; **never commit**, git is handled externally).
4. §0 ticks match §7 entries.
5. Any error surfaced → §8 entry exists and is closed (retest green) or explicitly `OPEN-BLOCKED`.
6. **For any real-EnergyPlus retest claim (T03/T05/T07/T09/T10/T11): independently re-derive at least one number yourself** (a fresh `sqlite3` query against a raw `eplusout.sql`, or a fresh `sacct`/CSV row count) rather than trusting the employee's printed summary — this is exactly the standard the closed arc's own CP-E audit held itself to, and it caught real precision errors even in an otherwise-solid report.
Anything missing → dispatch a fix employee before greenlighting the next range.

## 6. Final completion report (last action before going idle)

Write `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/COMPLETION_REPORT_debug.md` (English) containing: per-task outcome table (T01–T11), checkpoint verdicts, the T03/T05/T07/T09 real-EnergyPlus before/after tables, T11's full-cluster before (T17) vs. after (T18) success-rate and EUI-median comparison, §8 error summary (closed vs. any new `OPEN-BLOCKED`), and exact pytest totals. Then:
- Update `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md` with the new post-fix numbers (append a new section — do not rewrite §3's original T17 table, which stays as the historical record).
- Update `docs/PROJECT_CHECKLIST.md`'s Arc L entry with the debug plan's outcome (does `layout_assign` now qualify as production-grade for fleet EUI? Say so plainly, either way, with the numbers).
- Update memory `C:\Users\o_iseri\.claude\projects\C--Users-o-iseri-Desktop-OpenUBEM\memory\project_layout_assigner_arc.md` (+ `MEMORY.md` index hook if the one-line description changed).
- Leave a short final message summarizing: done/not-done, where the report is, any `OPEN-BLOCKED` items remaining. In French (the user converses in French; the report itself stays English).

## 7. Standing constraints (non-negotiable)

- **Absolute cluster rule:** never a blocking/interactive `srun`/compute on the Speed login node for T11 — `sbatch --array` fire-and-forget always, read the output file after. See Operating Mode rule 7 for the notification-waiting failure mode specifically.
- Minimum cluster-monitoring interval is 30 minutes — never poll `sacct`/`squeue` more often than that.
- Git handled externally — never commit, never offer to.
- No `.py` under `docs/`; never edit root `main.py` or OVERVIEW/DESIGN docs; figures → `openubem/outputs/` (flat) **and** duplicated into `docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/figures/`.
- **Never overwrite T17's original harvest artifacts** (`t17_layout_assign_eui.csv`/`t17_layout_assign_cell_summary.csv`) — T11 writes to new `t18_*` filenames so a real before/after comparison survives.
- Do not modify the CLOSED arc's `implementation_plan.md` §7/§8/§9 entries — it is a frozen historical record; this plan's own §7/§8 (in `PLAN_debug_implementation.md`) is where you write.
- You (director) write NO feature code — employees write all `openubem/` and `tests/` code. You write only: plan §7/§8 entries, §0 ticks, the completion report, checklist/memory updates.
