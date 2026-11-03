# EXECUTOR PROMPT — E-LA-20 Phase A-bis (F02-R, F03-R, stop at CP-A)

**Target executor:** Gemini / Antigravity · **Written by:** manager session · **Date:** 2026-07-25
**Context:** corrective dispatch. The previous Phase-A dispatch had F01 accepted and **F02 and F03 rejected at audit**. Still zero production-code edits.

Copy everything below the line into the executor session.

---

You are the executor for a pre-written implementation plan in the OpenUBEM project. You execute the plan; you do not rewrite it.

This is a **corrective dispatch**. A previous Phase-A run submitted F01, F02 and F03. The manager audited all three:

- **F01 — accepted.** Its measurement stands and has been promoted into the plan as **§4-bis**. It falsified the plan's original Fourier scaling; the rule is now a constant boundary, not a `sqrt(dt)` one. Do not re-run F01.
- **F02 — rejected as circular.** The ground-truth column was defined using the criterion's own threshold, so the clean confusion matrix was guaranteed before any data was read.
- **F03 — rejected.** All 11 runs died in `GetSurfaceData` during input processing and never reached `InitConductionTransferFunctions`. The N = 1 control did not reproduce the defect, which alone voids the task.

The full audit, with verbatim evidence and root cause for each rejection, is the entry `#### AUDIT — CP-A manager audit of F01–F03` in §8 of the plan. **Read it before you write any code.** It is not a reprimand; it is the specification of what the redo must avoid.

## Your assignment

Read this file first, in full:

```
C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\e-la-20\PLAN_e-la-20_multilayer-fix.md
```

Pay particular attention to **§4-bis** (the binding rule — §4-original is superseded and its `L_max` values must not be used), **§6 Phase A-bis** (your two tasks, F02-R and F03-R), and **§8's AUDIT entry**.

Execute **F02-R** and **F03-R** in order, then **stop at CP-A**. Do not start F04 or anything after it.

Background, read-only: `COMPLETION_REPORT_e-la-20-investigation.md` and `PLAN_e-la-20_investigation.md` §7 in the same folder. Those are a completed investigation; their findings are established and are not to be re-derived.

## Hard rules

1. **No production code may be edited in this dispatch.** Not `openubem/geometry/envelope_patcher.py`, not `openubem/idf/builder.py`, not anything else under `openubem/` or `tests/`. Probe scripts go in the scratchpad, never in the repo.
2. **Never edit** `main.py`, any OVERVIEW or DESIGN document, or the investigation plan's existing §7/§8 entries. In the multi-layer-fix plan, **never edit the AUDIT entry or the existing F01/F02/F03 log entries** — append new ones below them.
3. **Never modify a baseline IDF** in `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`. Read-only; copy to the scratchpad if a probe needs a mutated one.
4. **Never overwrite `t17_*`, `t18_*` or `t19_*` harvest artifacts**, and do not overwrite the previous run's `e_la_20_fix_f02_*` / `f03_*` CSVs — the redo writes to `f02r_` / `f03r_` names. The rejected artifacts stay on disk as part of the record.
5. **Never commit and never offer to.** Git is handled by the user's own tooling.
6. **All compute is local.** No cluster, no SLURM, no `sbatch`, no SSH. If a run is slow, reduce the sample — never offload.
7. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`** for every write.
8. **Do not propose an alternative fix shape.** If you believe the shape is wrong, say so at CP-A and let the manager decide.
9. **Stop and ask** on any genuine spec ambiguity. Quote the conflicting text verbatim; never invent a resolution.
10. **Default to no comments** in scripts. One short line, only where the *why* is non-obvious.

## Evidence discipline — the two rejections both came from here

Both rejected tasks satisfied the letter of the previous dispatch and still produced wrong conclusions. The specific mechanisms, and the rules that follow from them:

- **`.end` is not sufficient.** `EnergyPlus Terminated--Fatal Error Detected` says *that* E+ died, never *why*. F03 quoted it faithfully and still misattributed eleven input-parsing aborts to the CTF solver. **Every failure claim must quote the `** Severe **` line from `eplusout.err`.** For this arc, a CTF failure means the string `CTF calculation convergence problem` is present. Any other Fatal is a harness bug: stop the task, fix the harness, do not score it.
- **Never let your own script decide what a run means without checking the raw text.** The previous classifier was `"LA_ROOF_CONSTRUCTION" in err_text and "Fatal" in err_text` — true for a duplicate-name error as readily as for a CTF failure. Match on the specific severe string.
- **Never define the ground truth using the hypothesis.** F02 wrote `actual_fatal = (... and u_roof <= 0.138 and status == "failed")`, embedding the criterion's own threshold in the outcome it was testing. Ground truth comes from artifacts, or the question is reported as unanswerable — never from a re-statement of the prediction.
- **Controls are load-bearing.** If a negative control does not reproduce the defect (F03's N = 1 did not), the run is void regardless of what the other rows show. Check controls first and abort on failure.
- **Row count must equal artifact count.** Report both numbers explicitly in every deliverable. The rejected F03 claimed 38 runs with 11 directories on disk and a 12-row CSV; the missing series were the ones its conclusion rested on. If you cannot produce an artifact for a row, the row does not exist.
- **A silently-empty lookup is a bug, not a no-op.** F03's construction filter matched zero objects and continued. Assert non-empty after every IDF object query.
- **Report contradicting evidence loudly.** If F03-R shows genuine CTF failures at every N ≤ 10, that is a successful task and a hard stop — not a problem to engineer around.
- **Never end a turn waiting passively on a background process.** Check output files, `.end`/`.err` presence and process CPU directly, and keep working.

## Environment facts you will need

- Working directory: `C:\Users\o_iseri\Desktop\OpenUBEM`
- **`python` is NOT on PATH.** Use `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`
- EnergyPlus 23.1, local, through the project's existing runner — the same binary the investigation and F01 used.
- IDD path: `openubem.config.ENERGYPLUS_IDD_PATH`.
- Construction lookup: `openubem.semantic.construction_sets._get_flat_lookup(None)`; `VINTAGE_U_FACTORS` in the same module, U-values **rounded to 3 decimals** after the multiplier.
- **Object names in generated IDFs are mixed case** — `LA_Roof_Assembly`, `LA_Roof_Construction`. EnergyPlus reports them upper-cased in `.err`. Never compare the two forms directly; normalise case on both sides.
- A working F01 harness already exists at `scratchpad/e-la-20-fix/f01_run.py` and produced valid runs. Prefer adapting it over rebuilding — its IDF handling reached the CTF solver, which `f03_run.py`'s never did.
- Outputs go to `openubem\outputs\` (flat), prefixed `e_la_20_fix_`. Scratch work stays in the scratchpad.

## Reporting

After **each** completed task, append one entry to §8 of the plan document — below the AUDIT entry, not inside it — in exactly this format:

```
#### FXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + citation>
- Test status: <pytest summary / run counts>
- Notes: <auditor-relevant>
```

Tick the matching checkbox in §0 as you go. A task without a §8 entry is not complete.

At CP-A, stop and report:

1. **F02-R** — the 2×2 confusion matrix over all 8,160 rows, the name of the artifact you read `actual_fatal` from, one verbatim example line from it, and the count of rows with versus without usable evidence. Every false positive and false negative listed individually.
2. **F03-R** — the full results table, including the N = 1 control (must Fatal with a genuine `CTF calculation convergence problem` severe) and the N = 2 @ 1.0084 m control (must pass). Row count and on-disk directory count, stated side by side.
3. **A one-line verdict:** do §4-bis's `L_CRIT_MEASURED = 0.868` and `SAFETY_L = 1.45` stand? You have authority to raise `SAFETY_L` on evidence; you have no authority to lower it.
4. **Confirmation that no production file was modified** — paste the output of `git status --short openubem/ tests/ main.py`.

Then stop and wait. Do not begin Phase B.
