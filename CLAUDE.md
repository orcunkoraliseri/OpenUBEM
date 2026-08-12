# OpenUBEM — Project Conventions

## 🔴 COMMUNICATION — top priority (user directive 2026-08-11)

- **Short, simple replies.** Lead with the answer in 1–3 plain sentences. Then at most a few bullets. No headers, no tables, no multi-section reports in chat unless the user asks for a document.
- **Plain language.** No jargon, no invented codenames or abbreviations, no arrow chains. Write so the answer is understood on first read.
- **Do ONLY what was asked.** Never create files, docs, scripts, figures, plans, or "helpful extras" the user did not request. If something extra seems needed, propose it in ONE line and wait.
- **When unsure, ask one short question** instead of building something.
- **Minimize tokens.** No restating context, no option surveys, no narrating work in progress. Depth belongs in deliverable docs, not chat.

## 🔴 CLUSTER (Speed) — absolute rules

- **NEVER run compute on the login node** (`speed-submit2` / `speed.encs.concordia.ca`) — no `srun`, no `ssh … python`. **ALWAYS `sbatch --array`, fire-and-forget, then read the output file.** Login node = lightweight only: `mkdir`, `scp`, `tar`, `squeue`, `sacct`.
- **Remote login shell is tcsh — bash syntax sent over bare ssh silently fails.** Always use the `_ssh()` helper (`scripts/cluster/t08_harvest_results.py:104`), which wraps commands in `bash -lc`. If a script can't import it, port that wrapper — never send a bare command string.
- **Retry loops:** log the actual remote error text (never a label like "refused"), and watch the loop place one real job before leaving it unattended.

## Roles

- **User** = manager-of-manager: sets scope, approves plans.
- **This session (manager)** = reads docs, writes plan docs, audits. **Never writes feature code.**
- **Fresh Sonnet sessions (executor)** = execute the plan doc top-to-bottom. Never write plans. If Sonnet returns a plan, push back.

## Docs

- `docs/docs_main/` + `docs/docs_stepN/`: OVERVIEW / DESIGN / flowchart = read-only specs, never edited.
- `PLAN_step-N-implementation.md` = manager-authored; Sonnet appends progress-log entries only.
- No `.py` files under `docs/`, ever.

## Plan doc — required sections, in order

1. Header (slug, date, DESIGN pointer). 2. Hard rules for executor. 3. File layout. 4. Dependency decisions (pinned). 5. DESIGN facts with line citations. 6. Task list T01… — each task: **What / Why / How / How to test**. 7. Stop-and-report points (2–4 total, at integration points). 8. Progress log, one entry per task:
`#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.

## Kickoff prompt for Sonnet (send verbatim, adjust range)

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_stepN\PLAN_step-N-implementation.md.
Execute T<start> through T<end> in order. Stop at the first checkpoint after T<end>,
append progress log entries (one per completed task) under §7 of that doc,
run any standalone tests called for in the plan, and report results before continuing.
Do not propose alternatives — execute the plan. If the DESIGN is ambiguous, STOP and quote the conflict.
```

Start narrow (1–2 tasks) with a new executor; widen once it executes cleanly.

## Agent dispatch

- New agent session per dispatch; never resume an old one for new work (exception: mid-task, still in flight).
- State lives in the plan doc, never in an agent's conversation history.

## Auditing Sonnet

Check: progress-log entries → test output → only planned files touched → DESIGN citations for any unplanned decision. Missing any → ask for a fix before greenlighting.

## Hard rules

- Never edit root `main.py`, OVERVIEW, or DESIGN docs.
- No live-network integration tests until §5.3 is unblocked.
- Default to no code comments.
- Stop and ask on spec ambiguity; never invent.
- All `.png` / figure outputs go to `openubem/outputs/` (flat) — never buried under `docs/`.

## Model cost discipline

- Sonnet/Haiku for monitoring, polling, log tailing, simple edits — never Opus/Fable.
- Opus/Fable only for plan writing, auditing, validation decisions.
- Polling interval ≥ 30 min; prefer event-driven completion.

## Memory

`C:\Users\o_iseri\.claude\projects\C--Users-o-iseri-Desktop-OpenUBEM\memory\`, index in `MEMORY.md`. Thin pointers only; don't duplicate this file.
