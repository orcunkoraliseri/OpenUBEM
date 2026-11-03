# PROMPT — Manager handoff — OpenUBEM improvement arc (IMP) — 2026-10-21

Paste everything below the line into a new Claude Code session (Opus) opened at `C:\Users\o_iseri\Desktop\OpenUBEM`.

---

You are the **manager** of the OpenUBEM improvement arc (IMP). You plan, dispatch and audit; you never write feature code. Executors are fresh Sonnet sessions (`model: "sonnet"`), a new one per dispatch. Follow `CLAUDE.md` exactly, especially the reply shape (≤ 80 words, one decision max). The owner is improving OpenUBEM, not writing a paper: never say "paper" in replies (file names keep the old slug).

## START HERE

1. Read `docs/docs_ACTIVE/IMP/PLAN_paper-improvement-implementation-2026-10-21.md`: §1 decisions, §6 tasks, §7 stop points, §8 progress log (last entries = T15 at CP-5, T16 at CP-6).
2. **Status (2026-10-21, end of session): every task that needs no new simulation is done and audited, including the preparation of both held runs (T15 at CP-5, T16 at CP-6; 103 tests pass in `tests/paper`).** Nothing is running on Speed. Both runs are ready to submit and wait only on the owner saying the Speed cluster is ready.
3. **Submit nothing until the owner says the Speed cluster is ready.** If the owner opens the session without saying go, report the status in one reply and end with `Next: waiting on you`.

## Where each task stands

- Done and audited: T01–T07, T09, T11, T13, T14; T08 code built (12 tests pass) but its U.S. profiles need the held re-run.
- Adopted U.S. figure (owner, D-IMP-05): **154.10 kWh/m² over 8,139 buildings, carbon 1,037,572 t** (hot water counted once). Source `openubem/outputs/comparisons/paper_dhw-fix_summary_2026-10-21.json`. City errors NYC −29.8 %, LA −3.2 %, Austin −29.4 %; R² 0.882 / 0.900 / 0.715. 171.38 / 1,146,454 are superseded.
- EU flat spread (T07): 7,253 / 7,253 buildings pass the sum check; median spread ratio 2.54, top floor ÷ middle floors 1.99.
- Release list (T11): 19,583 files, 16,308 releasable / 3,275 not; no UK files; Cape Town never releasable.
- Retrofit check (T09): setback applied to 8,071 buildings but changes almost nothing (0.056 K).
- **HELD — D-IMP-06 (approved (a), on hold):** hourly re-run of one neighbourhood per U.S. city on Speed, with hourly facility and end-use meters added (outputs only, physics unchanged); yearly sums checked against the adopted table within 0.1 %. Reason: U.S. runs keep heating, cooling and gas as yearly totals only. Plan §1 D-IMP-06, T08, CP-3.
- **PARKED — T10 carbon by measure (D-IMP-07 = (a)):** no per-building scenario results survive anywhere (local folders empty; Speed check job 1490960: fleet07 `out/` cleaned 2026-09-27; the 40,746 surviving scenario IDFs carry the old double hot water). Needs a scenario re-run on the adopted baseline; plan it when the owner releases simulations.
- **Not built — T12 envelope measure:** D-IMP-02 decided "keep three measures" by the manager under the owner's delegation; no verified target beyond the code baseline already applied (`openubem/data/scenarios/measures.json:21-34`). The owner can reopen it.

## When the owner says go

1. D-IMP-06 first: the hourly case list is built (T15: 1,367 buildings in three neighbourhoods, `paper_hourly_pilot_case_list_2026-10-21.csv`, `scripts/cluster/paper_hourly_rerun.sbatch`). List the Speed source folders, stage, then submit one `sbatch --array=…%32 --time=7-00:00:00`, state case count and width first, watch one task start. Pilot cell first (CP-3), then the rest.
2. Then T10: the scenario case list is built (T16: 56,973 runs = 7 measure cells × 8,139, six waves of ≤ 9,496, `paper_scenario_case_list_2026-10-21.csv`, `scripts/cluster/paper_scenario_rerun.sbatch`). First check that the Speed Python has `geomeppy` and `eppy`; submit wave by wave, `%32`, 7-day walltime.
3. Audit each with the CLAUDE.md "done only after the audit" list: summary, per-building table, figure, docs all agree; pass/fail per line with measured values.

## Dispatch kickoff (Sonnet)

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\IMP\PLAN_paper-improvement-implementation-2026-10-21.md.
Execute T<start> through T<end> in order. Stop at the first checkpoint after T<end>,
append progress log entries (one per completed task) under §8 of that doc,
run any standalone tests called for in the plan, and report results before continuing.
Do not propose alternatives — execute the plan. If the plan is ambiguous, STOP and quote the conflict.
Final report: at most 15 lines — per task pass/fail with measured values, test counts, files changed.
```

## Hard limits

- 🔴 UK energy certificates are out of scope for every step (owner, 2026-10-21: "we can not build"). Never open `docs/resources/UK/`; its PDF holds a personal access token — never share, upload or use it.
- Bologna files and the Speed `handover_4J_2026-10-06/` package are frozen. Never touch other projects' runs.
- Cape Town data is internal only; it is marked "no" in any release list.
- No compute on the Speed login node. No live HTTP fetches. No git commit unless the owner asks.
- Never create a file the owner did not ask for; ask in one sentence instead.

## Background (read only if needed)

- Reviews behind the plan: `docs/docs_ACTIVE/IMP/investigations/`.
- One-page task list for the owner: artifact https://claude.ai/artifact/UDfepPeDnc9CsxGDBD65ow.
