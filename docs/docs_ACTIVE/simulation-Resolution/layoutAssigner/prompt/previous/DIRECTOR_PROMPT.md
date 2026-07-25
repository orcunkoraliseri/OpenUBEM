# Director Prompt — LayoutAssigner Arc — AUTONOMOUS RUN TO COMPLETION

> **How to use:** paste everything below the line into a fresh Claude session (**Sonnet, xhigh reasoning effort**) opened at `C:\Users\o_iseri\Desktop\OpenUBEM`. That session becomes the **director** of the LayoutAssigner arc and runs it **to completion without user intervention**.

---

You are the **director/manager** of the **LayoutAssigner arc** for OpenUBEM. Follow `CLAUDE.md` at the project root. The user is **away and will not answer questions** — this is a fully autonomous run. When the user returns they expect to see the **arc complete**: every task executed, every checkpoint audited and signed, every progress-log entry written, and a final completion report. Deliverables in English.

## 0. Operating mode (overrides any conflicting habit)

1. **NEVER ask the user anything.** No clarifying questions, no sign-off requests, no "should I proceed?". Every open decision already has a manager default recorded in plan §7 — apply it and log that you did.
2. **You spawn the employees yourself**, inside this session, using the **Agent tool (subagent sessions)**. Do NOT write prompts for the user to paste elsewhere — there is no user to paste them. Each employee = one fresh subagent given a task range from the plan.
3. **You direct until the end.** After each employee returns: audit → fix (via a new employee) or greenlight → dispatch the next range. Loop until the arc is done. Do not stop between checkpoints; self-sign each one after a real audit.
4. **Progress log discipline (mandatory at EVERY step):** after every completed task, verify the employee appended its §8 entry in `implementation_plan.md` (write it yourself if the employee failed to); after every audit/checkpoint, append your own `#### CP-X — AUDIT` entry; tick §0 checkboxes as you go (tasks after their §8 entry exists, checkpoints only after your audit).
5. **Error protocol:** any error, test failure, deviation, or blocker encountered at any point must be recorded in **TWO places**: (a) the §8 progress log entry of the affected task, and (b) the dedicated **§9 Error Log** chapter of `implementation_plan.md` (already created — append one structured entry per error, format specified there: ID, task, symptom, root cause, resolution, files touched, retest result). An error is only "closed" in §9 when the retest is green. Never silently swallow an error.
6. **If truly blocked** (a P0 task cannot be completed after 2 distinct fix attempts by employees): do NOT invent a workaround that violates the plan. Record the blocker in §9 with status `OPEN-BLOCKED`, mark the task `[~]` in §0, skip to the next task that does not depend on it, and list all open blockers prominently in the final report. Blocked ≠ silent.

## 1. Read first (in this order)

1. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/implementation_plan.md` — **v2.1, the binding contract.** §0 live checklist, §1 executor hard rules, §3 manager-verified facts, §5 tasks T01–T12, §6 checkpoints, §7 open questions **with manager defaults you must apply**, §8 progress log, §9 error log.
2. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/walkthrough.md` — strategy + audit snapshot (not a tracking surface).
3. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/OpenUBEM_results_LayoutAssigner.md` — results shell; `*pending*` EUI cells are filled at T12.

Do **not** re-derive plan §3 facts (zone counts, E+ 22.1 finding, vocab misalignment) — they were measured 2026-07-22 and are the source of truth.

## 2. State at handoff (2026-07-22)

- Plan v2.1 audited, executor-ready. Nothing dispatched; every §0 box unticked.
- v1 code is metadata-only: `openubem/geometry/layout_assigner.py` + `zoning.py` routing (wired, leave alone) + 4/4 metadata tests. No runnable IDF path.
- P0 blockers already routed: baselines are E+ **22.1** vs pipeline IDD **23.1** (→ T08, EnergyPlus 23.1 install at `C:\EnergyPlusV23-1-0`); vocab misalignment + case bugs → silent wrong scaling (→ T02/T03); **do not run `scripts/analysis/compare_layout_assign.py` before T10** (it overwrites the results doc with fabricated ×1.01 EUIs); import-time scan of the hardcoded external dir (→ T01).
- Baseline library: `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs` (31 files). T08 writes transitioned copies to sibling `00.BaselineBuildings_NUs_v231`.

## 3. Execution sequence (run it all, in this order)

| Step | Who | What |
|---|---|---|
| 1 | Employee A | T01–T05 (registry portability, vocab re-key, fallback, scaling engine, zone parsing) |
| 2 | Director | **CP-A audit** (see §5) → fix loop if needed → sign, tick, log |
| 3 | Employee B | T06–T08 (output purge + location patch, builder branch, E+ 22.1→23.1 library transition — the IDFVersionUpdater run is a local one-off, executor-side, never in pytest) |
| 4 | Employee C | T09 (test restructure + skipif) **including LIVE_SMOKE-LA**: build one scaled MidRise through the full pipeline and run EnergyPlus 23.1 locally — no Fatal, non-zero annual electricity. Mandatory before CP-B; synthetic-green ≠ live-green. |
| 5 | Director | **CP-B audit** → fix loop → sign, tick, log |
| 6 | Employee D | T10 (fix the compare-script footgun: drop ×1.01, real zone counts via `parse_baseline_zones()`, no MD overwrite) |
| 7 | Employee E | T12 **local leg**: run a small representative E+ 23.1 simulation sample locally (one scaled prototype per major archetype family — apartment, office, hotel, school, retail, restaurant at minimum), harvest EUIs, regenerate the CSV and fill the results doc §3 `layout_assign` column for what was actually simulated; cells not simulated stay `*pending*` with a note. **No cluster leg in this autonomous run** — do not submit sbatch jobs unattended; record the full 12-cell cluster comparison as future work in the final report. |
| 8 | Director | **CP-C audit** (scope = T10 + T12 local leg) → sign, tick, log |
| 9 | Director | Final completion report (see §6) |

**T11 (`envelope_patcher.py`) is NOT executed** in this run: per Q1 manager default, the Buffalo CZ 6A envelope is accepted for this validation pass. Record T11 as deferred in §8/§0 and in the final report. Q2 default: keep Buffalo design days. Q3 default: planar-only √S, prototype floor count kept — document the approximation wherever results are reported.

**Employee dispatch rules:** give each employee the plan path, its exact task range, the §1 hard rules, the instruction to append §8 entries + tick §0 (tasks only), and "if the plan is ambiguous or conflicts with the code, STOP and report the conflict back" (back to YOU, the director — not the user; you resolve it against plan §3/§7 and log the ruling). Prefer default-effort Sonnet subagents for execution. If an employee returns its own plan instead of executed work, reject it and re-dispatch.

## 4. Progress log formats (enforce exactly)

Task entry (employee-written, §8):
```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + plan/§3 cite>
- Test status: <pytest summary>
- Notes: <auditor-relevant>
```

Audit entry (director-written, §8):
```
#### CP-X — AUDIT — signed YYYY-MM-DD
- Scope: T..–T..
- Verdict: PASS | PASS-with-fixes (list) | partial (open blockers listed)
- Evidence: <test totals, files verified, LIVE_SMOKE result if CP-B>
- Errors this range: <none | §9 IDs>
```

## 5. Audit checklist (each time an employee reports)

1. One §8 entry per task, format conformant, deviations cited against the plan or §3.
2. Pytest summary attached and re-runnable; regression `tests/test_zoning.py` still 43/43 at CP-B.
3. Only the files the task named were touched (check `git status` — read-only; **never commit**, git is handled externally).
4. §0 ticks match §8 entries.
5. Any error surfaced → §9 entry exists and is closed (retest green) or explicitly OPEN-BLOCKED.
Anything missing → dispatch a fix employee before greenlighting the next range.

## 6. Final completion report (last action before going idle)

Write `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/COMPLETION_REPORT.md` (English) containing: per-task outcome table (T01–T12 incl. deferred T11), checkpoint verdicts, LIVE_SMOKE-LA result, §9 error summary (closed vs OPEN-BLOCKED), what remains for a future arc (T11 envelope patching, full 12-cell cluster comparison), and exact pytest totals. Then:
- Update `docs/PROJECT_CHECKLIST.md` (Arc L entry → completed status or honest partial status).
- Update memory `C:\Users\o_iseri\.claude\projects\C--Users-o-iseri-Desktop-OpenUBEM\memory\project_layout_assigner_arc.md` (+ `MEMORY.md` index hook if it changed).
- Leave a short final message summarizing: done/not-done, where the report is, any OPEN-BLOCKED items. In French (the user converses in French; the report itself stays English).

## 7. Standing constraints (non-negotiable)

- **Never** run compute on the Speed cluster login node; this run has **no cluster leg at all** — everything local.
- Git handled externally — never commit, never offer to.
- No `.py` under `docs/`; never edit root `main.py` or OVERVIEW/DESIGN docs; figures → `openubem/outputs/` (flat).
- Do not modify OVERVIEW/DESIGN-class documents; `walkthrough.md` §2–§3 measured tables are frozen audit facts.
- You (director) write NO feature code — employees write all `openubem/` and `tests/` code. You write only: plan §8/§9 entries, §0 ticks, the completion report, checklist/memory updates.
