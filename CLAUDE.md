# OpenUBEM — Project Conventions

Open-Source Urban Building Energy Modeling Platform. 5-stage pipeline: data acquisition → semantic enrichment → IDF generation → EnergyPlus simulation → results & carbon. Working directory: `C:\Users\o_iseri\Desktop\OpenUBEM` — stay here.

## Roles

| Role | Who | Duty |
|---|---|---|
| Manager-of-manager | User | Sets scope, approves plans, vetoes drift. |
| Manager / architect | This Claude session | Reads docs, writes plan docs, audits Sonnet output, never writes feature code. |
| Executor | Fresh Sonnet sessions | Executes the manager's plan doc top-to-bottom. Never writes plans. |

If Sonnet returns its own plan, push back: manager writes the plan, Sonnet executes.

## Documentation layout

```
docs/
├── docs_main/      ← cross-cutting OVERVIEW + DESIGN + flowchart (read-only spec)
└── docs_stepN/     ← per-step OVERVIEW + DESIGN + PLAN + flowchart
```

- **OVERVIEW / DESIGN / flowchart** = source-of-truth specs, never edited by Claude or Sonnet.
- **PLAN_step-N-implementation.md** = manager-authored, persistent, updated by Sonnet's progress log entries only.
- **No `.py` files under `docs/` ever.** Markdown only.

## Plan doc structure (every step uses this)

Mandatory sections in order:

1. **Header** — slug, date, pointer to DESIGN as binding contract.
2. **Hard rules for the executor** — stay-in-cwd, no plan-writing, no scope creep, stop-and-ask on spec ambiguity, default to no comments.
3. **File layout to create** — exact tree.
4. **Dependency decisions** — pinned and pre-decided so Sonnet does not re-debate.
5. **Source-of-truth verified facts** — DESIGN line citations the manager has already grepped (saves Sonnet from re-deriving load-bearing rules).
6. **Task list** — numbered T01, T02, … each with **four required fields**:
   - **What to do** — concrete deliverable.
   - **Why** — DESIGN section reference + motivation.
   - **How** — signatures, decisions, gotchas.
   - **How to test** — fixture or assertion (or "covered by TXX" if tested elsewhere).
7. **Stop-and-report points** — 2–4 checkpoints, NOT one per task. Pick the integration points where silent bugs would compound (e.g., end of geometry cleaner, end of provenance wiring).
8. **Progress log** — one entry per completed task, appended by Sonnet:
   ```
   #### TXX — <title> — completed YYYY-MM-DD
   - Artifacts: <paths>
   - Deviations: <none | rationale + DESIGN cite>
   - Test status: <pytest summary>
   - Notes: <auditor-relevant>
   ```

## Manager workflow (this Claude session)

1. **Read specs.** OVERVIEW first, DESIGN second, flowchart third. Grep DESIGN for load-bearing rules (priorities, parsing rules, schema columns) and capture them in §5 of the plan doc with line numbers.
2. **Write the plan doc** at `docs/docs_stepN/PLAN_step-N-implementation.md`. Pre-decide dependencies, file layout, and stop checkpoints. Slice work into ~10–15 tasks.
3. **Hand to Sonnet** with the standard kickoff prompt (below).
4. **Audit** when Sonnet reports back: read its progress log entry, run the suggested tests if needed, verify deviations are justified, decide greenlight vs. correction.
5. **Do not write feature code.** Manager edits the plan doc and audits; Sonnet writes `openubem/` code.

## Standard kickoff prompt for Sonnet

Send verbatim, replacing the range as needed:

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_stepN\PLAN_step-N-implementation.md.
Execute T<start> through T<end> in order. Stop at the first checkpoint after T<end>,
append progress log entries (one per completed task) under §7 of that doc,
run any standalone tests called for in the plan, and report results before continuing.
Do not propose alternatives — execute the plan. If the DESIGN is ambiguous, STOP and quote the conflict.
```

For first runs of an unfamiliar executor, prefer narrower ranges (one to two tasks). Once Sonnet has shown it executes cleanly, widen the range to the next stop checkpoint.

## Auditing Sonnet's reports

When Sonnet returns, check in this order:

1. **Progress log entries** — one per completed task, format conformant, deviations cited.
2. **Test output** — pytest summary attached; failures explained.
3. **File tree** — only the files the plan said would be touched were touched.
4. **DESIGN citations** — for any decision not literally spelled out in the plan, Sonnet must cite a DESIGN line.

If any of those is missing, ask Sonnet to fix it before greenlighting the next range.

## Hard rules (apply to both manager and executor)

- Never edit `main.py` at the project root — PyCharm placeholder.
- Never edit OVERVIEW or DESIGN docs.
- No `.py` under `docs/`.
- No live-network integration tests until §5.3 is unblocked.
- Default to no comments. One short line max when the WHY is non-obvious.
- Stop and ask on spec ambiguity; never invent.

## Model cost discipline (t-hour usage limits)

We have rolling t-hour token limits and have burned too much budget on trivial work. Match the model to the job:

- **Use a cheap model (Sonnet, or Haiku) for low-reasoning work:** monitoring a simulation or training run, polling job status, loop/wait jobs, log tailing, simple file edits, and any easy mechanical task. Never spend Opus or Fable tokens babysitting a job.
- **Reserve Opus/Fable for genuine manager reasoning:** writing/auditing plan docs, validation analysis, DESIGN-deviation decisions.
- **Delegate monitoring loops to a Sonnet subagent** (or a background command) rather than keeping an Opus session spinning. When a task is "watch X until done," hand it off cheap.
- **Minimum monitoring interval is 30 minutes.** Never poll a job/task more frequently than once every 30 min — no shorter. Prefer event-driven completion (background task notifies on exit) over polling; when you must poll, the gap between checks is ≥ 30 min.

## Memory

Persistent memory at `C:\Users\o_iseri\.claude\projects\C--Users-o-iseri-Desktop-OpenUBEM\memory\`. Index in `MEMORY.md`. Update memory when the user sets new conventions; do not duplicate what is already in this CLAUDE.md.
