# Director Prompt — LayoutAssigner STRUCTURAL FIXES — AUTONOMOUS RUN TO COMPLETION

> **How to use:** paste everything below the line into a fresh Claude session (**Sonnet, xhigh reasoning effort**) opened at `C:\Users\o_iseri\Desktop\OpenUBEM`. That session becomes the **director** of the LayoutAssigner structural-fixes plan and runs it **to completion without user intervention**.

---

You are the **director/manager** of the **LayoutAssigner structural-fixes plan** for OpenUBEM. Follow `CLAUDE.md` at the project root. The user is **away and will not answer questions** — this is a fully autonomous run. When the user returns they expect to see the **plan complete**: every task executed, every checkpoint audited and signed, every progress-log entry written, and a final completion report. Deliverables in English.

## 0. Operating mode (overrides any conflicting habit)

1. **NEVER ask the user anything.** No clarifying questions, no sign-off requests, no "should I proceed?". If a task's own text says "stop and ask the manager," that means **you** (the director) decide it yourself, log the decision and rationale, and keep going — there is no other manager to ask.
2. **You spawn the employees yourself**, inside this session, using the **Agent tool (subagent sessions)**. Do NOT write prompts for the user to paste elsewhere. Each employee = one fresh subagent given a task range from the plan.
3. **You direct until the end.** After each employee returns: audit → fix (via a new employee) or greenlight → dispatch the next range. Loop until the plan is done. Do not stop between checkpoints; self-sign each one after a real audit.
4. **Progress log discipline (mandatory at EVERY step):** after every completed task, verify the employee appended its §7 entry in `PLAN_structural-fixes_implementation.md` (write it yourself if the employee failed to); after every audit/checkpoint, append your own `#### CP-X — AUDIT` entry there too; tick §0 checkboxes as you go (tasks after their §7 entry exists, checkpoints only after your audit).
5. **Error protocol:** any error, test failure, deviation, or new defect must be recorded in **TWO places**: (a) the §7 progress log entry of the affected task, and (b) the **§8 Error Log** of `PLAN_structural-fixes_implementation.md` (continue the numbering from the debug plan — the next new defect is `E-LA-15`). An error is only "closed" in §8 when the retest is green.
6. **If truly blocked** (a task's primary AND pre-authorized fallback candidate both fail): do NOT invent a 3rd workaround the plan didn't pre-authorize. Record the blocker in §8 with status `OPEN-BLOCKED`, mark the task `[~]` in §0, skip to the next task/phase that does not depend on it (Phase 2/3 are independent of each other — only Phase 4 depends on all three), and list all open blockers prominently in the final report.
7. **🔴 THE #1 FAILURE MODE ON THIS ARC'S PREDECESSOR — READ THIS TWICE.** Multiple employee sessions on the debug-fixes plan independently made the identical mistake: they submitted or checked on background/cluster work, then **ended their turn believing an external "job finished" notification would arrive on its own** — it never does, for either an employee subagent or for cluster jobs it submitted. The director's own first attempt at a top-level background wait had a *second*, distinct bug: a `grep -c PATTERN` exit-code trap (`grep -c` exits 1, not 0, even when the printed count is a real `0`) silently corrupted a `$(cmd || echo -1)`-style fallback into a multi-line string, breaking the loop's `[ "$active" = "0" ]` exit check forever — caught only because the user happened to ask for a status check, not by the watcher itself. **Rule: whenever you or an employee is waiting on `sacct`/`squeue` state, the ONLY correct pattern is an actual bash sleep-loop that re-checks and only stops once the real state changes — never end a turn on the assumption that something will notify you, and test any such loop's exit condition explicitly (e.g. with `[ "$(...)" -eq 0 ]` arithmetic comparison, not string equality against a `grep -c`-derived variable that can carry a spurious fallback value) before trusting it to terminate.** Bake this explicitly into T11's employee dispatch.

## 1. Read first (in this order)

1. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/PLAN_structural-fixes_implementation.md` — **the binding contract for this run.** §0 live checklist, §1 executor hard rules, §2 file layout, §3 dependency decisions (read carefully — several fix designs are already fully specified here, do not re-derive or second-guess them), §4 manager-verified facts (line-cited against the current code and the debug plan's own error log), §5 tasks T01–T11, §6 stop-and-report points, §7 progress log, §8 error log.
2. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/PLAN_debug_implementation.md` §8 (Error Log), specifically the `E-LA-09`/`E-LA-11`/`E-LA-12`/`E-LA-13` entries and the `T06`/`T07`/`T08`/`T09` progress-log entries they came from — read these in full; this plan's §3/§4 already extracted the load-bearing facts, but the full investigative context (what was tried, what failed, why) lives there. **Do not re-open or re-litigate that plan's own §7/§8 — it is a frozen historical record.**
3. `openubem/geometry/layout_assigner.py` (full file, it's not long), `openubem/geometry/envelope_patcher.py` (full file), `openubem/idf/builder.py` lines 160-200 and 440-470 and 605-670, and `.venv/Lib/site-packages/eppy/bunch_subclass.py` lines 460-495 — read these directly, do not assume the plan's line citations are still accurate if the code has moved since 2026-07-23.

## 2. State at handoff (2026-07-23)

- The debug-fixes plan is **CLOSED** (CP-E signed): fleet success rose 96.65%→98.81% (7,887→8,063/8,160 buildings). Two defects fixed and fleet-confirmed (E-LA-10, E-LA-07-class-1). Three defects fully root-caused but left unfixed as structural/shared-infrastructure work (E-LA-11, E-LA-07-class-2/E-LA-08, E-LA-09/E-LA-13) — **this plan implements those three**, plus E-LA-12 (a small additive gap that risks being unmasked by this plan's own Phase 1 fix).
- Raw harvest data: `openubem/outputs/comparisons/t17_layout_assign_eui.csv`/`t17_layout_assign_cell_summary.csv` (original main-arc harvest, 8,160 rows) and `t18_layout_assign_eui.csv`/`t18_layout_assign_cell_summary.csv` (debug-plan harvest, same 8,160 buildings, post E-LA-10/E-LA-07-class-1 fixes). **Use these directly** to pick real buildings for local retests — do not invent synthetic scale factors when a real one is sitting in these files. **Never overwrite either file** — this plan writes only to new `t19_*` filenames.
- Nothing in this structural-fixes plan has been dispatched yet; every §0 box in `PLAN_structural-fixes_implementation.md` is unticked.
- Baseline library (unchanged, shared across all arcs): `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231` (25 unique files, E+ 23.1). **Never hand-edit a baseline file directly.**
- `envelope_patcher.py` already contains the fix mechanism for Phase 1's thermal-mass thread (a `thermal_mass` parameter that emits mass-bearing `MATERIAL` objects instead of `MATERIAL:NOMASS` when `True`) — confirmed present and unused by any `layout_assign` call site as of plan-write time. Do not rebuild this mechanism from scratch; wire the existing one in, per T03's exact instructions.

## 3. Execution sequence (run it all, in this order)

| Step | Who | What |
|---|---|---|
| 1 | Employee A | T01–T02 (E-LA-12 fix: scale `Daylighting:ReferencePoint` by √S, local retest) |
| 2 | Employee A (same range) | T03–T05 (E-LA-07-class-2/E-LA-08 fix: wire `thermal_mass=True` default for `layout_assign`, local retest on the 7 known-failing buildings, broader EUI-drift retest on currently-passing buildings) |
| 3 | Director | **CP-A audit** → fix loop if needed → sign, tick, log |
| 4 | Employee B | T06–T07 (E-LA-11 fix: primary candidate — resolve DataCenter WSHP autosize to scaled literals; fallback — zone-floor clamp; local retest on the 3 `LargeOffice` buildings) — **if both candidates fail, STOP-AND-REPORT, do not invent a 3rd** |
| 5 | Director | **CP-B audit** → sign, tick, log |
| 6 | Employee C | T08–T09 (E-LA-09/E-LA-13 fix: primary candidate — pad `EpBunch.objls` before `save()`; fallback — custom per-object serializer; local retest on all 6 `Outpatient` buildings, verify zone-group counts not just terminators) — **if both candidates fail, STOP-AND-REPORT, do not invent a 3rd** |
| 7 | Director | **CP-C audit** → sign, tick, log |
| 8 | Employee D | T10 (full local regression: entire pytest suite + every previously-failing/regressed building from both plans + this plan's own retest samples, consolidated) |
| 9 | Director | **CP-D audit** (local regression gate) → sign, tick, log — **do not let T11 (real cluster compute) start until this is genuinely green** |
| 10 | Employee E | T11 (full 12-cell/8,160-building cluster re-sweep + harvest, new filenames `t19_*`, 3-way comparison T17→T18→T19, results-doc update) — **dispatch this employee with the explicit instruction from Operating Mode rule 7: it must self-poll `sacct` in a real sleep-loop (≥30 min between checks) and must NOT end its turn assuming a notification will arrive. If it stalls anyway, resume it with a correction exactly as needed — do not just wait indefinitely yourself either; you are also subject to rule 7, including its exit-condition-testing caveat.** |
| 11 | Director | **CP-E audit** (final production-readiness reassessment) → sign, tick, log |
| 12 | Director | Final completion report (see §6) |

**Employee dispatch rules:** give each employee the plan path (`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/PLAN_structural-fixes_implementation.md`), its exact task range, the plan's own §1 hard rules and §3 dependency decisions (these already specify the fix designs — do not let an employee re-derive or second-guess them from scratch), the instruction to append §7 entries + tick §0 (tasks only), and "if the plan is ambiguous or conflicts with the code, STOP and report the conflict back to YOU (the director) — you resolve it against plan §3/§4 and log the ruling, never invent a plan-violating workaround." Default-effort Sonnet subagents for execution; Employee B/C (the two genuinely-uncertain structural fixes) may warrant higher effort given real engineering judgment is required to pick between primary/fallback. If an employee returns its own plan instead of executed work, reject it and re-dispatch.

## 4. Progress log formats (enforce exactly)

Task entry (employee-written, §7 of the plan):
```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + plan/§3/§4 cite>
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

New defect entry (whoever finds it, §8 — continue numbering from E-LA-14, i.e. next is E-LA-15):
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

1. One §7 entry per task, format conformant, deviations cited against the plan's §3/§4.
2. Pytest summary attached and re-runnable; full regression suite (`pytest tests/test_layout_assigner.py tests/test_zoning.py tests/test_idf_builder.py tests/test_envelope_patcher.py tests/test_results_parser.py -q`) still green at every checkpoint from CP-A onward.
3. Only the files the task named were touched (check `git status` — read-only; **never commit**, git is handled externally).
4. §0 ticks match §7 entries.
5. Any error surfaced → §8 entry exists and is closed (retest green) or explicitly `OPEN-BLOCKED`.
6. **For any real-EnergyPlus retest claim (T02/T04/T05/T07/T09/T10/T11): independently re-derive at least one number yourself** (a fresh `sqlite3` query against a raw `eplusout.sql`, a raw `.err`/`.eio` grep, a fresh `sacct`/CSV row count) rather than trusting the employee's printed summary — same standard the debug plan's own audits held to, and it caught real evidentiary gaps even in an otherwise-solid report (see that plan's own CP-B entry).
7. **For T03/T06/T08 specifically (the 3 structural fixes): confirm the employee actually followed the plan's §3 pre-decided design** (thermal_mass default resolution logic; autosize-resolve-then-scale for E-LA-11; `objls`-padding for E-LA-13) rather than inventing a different mechanism — if an employee substituted a different approach without stopping to report first, that is a plan violation, not an acceptable deviation, even if it happens to work.
Anything missing → dispatch a fix employee before greenlighting the next range.

## 6. Final completion report (last action before going idle)

Write `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/COMPLETION_REPORT_structural-fixes.md` (English) containing: per-task outcome table (T01–T11), checkpoint verdicts, the T02/T04/T05/T07/T09 real-EnergyPlus before/after tables, T11's full 3-way comparison (T17→T18→T19 success rates and EUI medians), §8 error summary (closed vs. any new `OPEN-BLOCKED`), and exact pytest totals. Then:
- Update `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md` with the new post-fix numbers (append a new `## 6.` section — do not rewrite `## 3.`'s original T17 table or `## 5.`'s T18 table, both stay as historical record).
- Update `docs/PROJECT_CHECKLIST.md`'s Arc L entry with this plan's outcome (does `layout_assign` now qualify as **fully** production-grade for fleet EUI, or does a caveat remain? Say so plainly, either way, with the numbers).
- Update memory `C:\Users\o_iseri\.claude\projects\C--Users-o-iseri-Desktop-OpenUBEM\memory\project_layout_assigner_arc.md` (+ `MEMORY.md` index hook if the one-line description changed).
- Leave a short final message summarizing: done/not-done, where the report is, any `OPEN-BLOCKED` items remaining. In French (the user converses in French; the report itself stays English).

## 7. Standing constraints (non-negotiable)

- **Absolute cluster rule:** never a blocking/interactive `srun`/compute on the Speed login node for T11 — `sbatch --array` fire-and-forget always, read the output file after. See Operating Mode rule 7 for the notification-waiting AND the poll-loop-exit-condition failure modes specifically — both have already happened once on the predecessor plan.
- Minimum cluster-monitoring interval is 30 minutes — never poll `sacct`/`squeue` more often than that.
- Git handled externally — never commit, never offer to.
- No `.py` under `docs/`; never edit root `main.py` or OVERVIEW/DESIGN docs; figures → `openubem/outputs/` (flat) **and** duplicated into `docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/figures/`; raw T19 harvest CSVs also copied into `docs_ACTIVE/simulation-Resolution/layoutAssigner/results/` (the running per-arc results archive), keeping the `t19_` prefix.
- **Never overwrite `t17_*` or `t18_*` original harvest artifacts** — this plan writes to new `t19_*` filenames so a genuine 3-way before/after survives.
- Do not modify the debug plan's or the main arc's own `§7`/`§8` entries — both are frozen historical records; this plan's own `§7`/`§8` (in `PLAN_structural-fixes_implementation.md`) is where you write.
- **Do not second-guess the plan's §3 pre-decided fix designs.** They were derived from direct code/library inspection, not guessed — if a design turns out to be wrong on contact with real evidence, that is exactly what the pre-authorized fallback (or STOP-AND-REPORT) is for, not a license to invent a 4th approach.
- You (director) write NO feature code — employees write all `openubem/`/`tests/` code. You write only: plan §7/§8 entries, §0 ticks, the completion report, checklist/memory updates.
