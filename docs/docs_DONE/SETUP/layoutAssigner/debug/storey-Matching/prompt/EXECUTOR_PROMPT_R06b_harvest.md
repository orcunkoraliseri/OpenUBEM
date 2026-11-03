# Executor prompt — R06 part 2 (T20 harvest + the seven reported items)

> Pre-drafted by the director 2026-07-26. Dispatch a **fresh Sonnet** once the T20 arrays are done.
> Part 1 (generation + submission) is already complete — see the "IN-FLIGHT NOTE — R06" at the end of
> §5 of the plan doc. **Do not re-submit the fleet.**

---

Working directory `C:\Users\o_iseri\Desktop\OpenUBEM`. Read, in this order:

1. §1 (hard rules) and §3 task **R06** of
   `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_REMAINder.md`
2. The **AUDIT — CP-D** entry and the **IN-FLIGHT NOTE — R06** at the end of §5 of that same doc.
3. `prompt\EXECUTOR_PROMPT_R06_fleet-rerun.md` — the seven reported items and the evidence rules.

Do **not** read `PLAN_storey-matching_implementation.md` (CLOSED, ~3,500 lines). Grep it by `F-nn` /
`E-LA-nn` ID and read only the surrounding lines.

## 🔴 Absolute rules

- **NEVER run compute on the Speed login node.** `squeue`, `sacct`, `ls`, `mkdir`, `scp`, `tar` only.
  If a remote step needs Python, wrap it in an `sbatch` script. No `srun`, no `ssh … python …`.
- **Never cancel/requeue/deprioritise any cluster job**, least of all another project's.
- **Never `git commit`.**
- **🔒 Frozen:** everything under `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\figures\`,
  and the `t17_*`/`t18_*`/`t19_*` harvests (read-only). R06 produces no figures — R09 does.
- Frozen constants: `T_ENGAGE = 0.868`, `T_MASS_MAX = 0.35`.
- Interpreter: `./.venv/Scripts/python.exe`.
- Progress-log entries are **append-only**; never rewrite a frozen entry.

## What to do

1. Confirm all 12 arrays are complete (`sacct`), then harvest with
   `scripts/cluster/t20_harvest_layout_assign.py`, extending it for the `eio` parsing the items below
   need. Fresh `t20_*` outputs only.
2. Finish `scripts/cluster/t20_r10_reach_change.py` across all 12 cells.
3. Report the **seven items** from the part-1 prompt. All seven; none is optional.

## The three things most likely to go wrong — read these

- **Item 3 (F-08 heating ratio).** The pair you measure on must have **at least one side with status
  `applied` and a residual multiplier ≥ 2**. R05's pair collapsed onto a single code path and gave a
  tautological 1.0000×; that is not a measurement. If the fleet contains no qualifying pair, **say so
  explicitly** rather than substituting a degenerate one.
- **Item 6 (reach change).** `t20_r10_reach_change.py` computes its "before" side by
  **reimplementing** the pre-R10 formula, not by running the old code. Either state that plainly in
  your entry, or take the "before" side from the pre-R10 commit in git history. Do not present a
  reimplementation as measured output of the old pipeline.
- **Evidence provenance.** Ground truth is raw `eplusout.err` (run outcome) and `eplusout.eio`
  (multiplier-aware floor area) — never the `.end` file, never a nominal `footprint × num_floors`
  computed in the harness. Any CSV column with an `eio`-derived name must actually be parsed from
  `eio`. A previous harness in this arc shipped a CSV whose `eio` columns were all `0.0` while its
  report cited them as proof. Hand-check your parser against one raw file before trusting it across
  8,160.

## Framing

- **E-LA-22 still stands**, so a clean T20-vs-T19 comparison is not available. Report deltas, but do
  not present them as attributable to this arc.
- If you cannot distinguish a **real** simulation failure from a **harness** failure, **STOP and
  report.** That ambiguity is a hard stop, not something to resolve by judgement.
- A fleet success rate below T19's **97.92%** for an unmapped reason is a hard stop — report, do not
  patch around it. `T_ENGAGE`/`T_MASS_MAX` stay frozen: a fleet failure reopens the fix plan, never
  the constants.

## Deliverable

Append **one** `R06` progress-log entry to §5 (Artifacts / Deviations / Test status / Notes) carrying
all seven reported quantities, then report back. Do not start R08 or R09.
