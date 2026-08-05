# EXECUTOR PROMPT — E-LA-20 multi-layer fix, Phase A (F01 → F03, stop at CP-A)

**Target executor:** Gemini / Antigravity · **Written by:** manager session · **Date:** 2026-07-25
**Dispatch scope:** Phase A only. This is a first dispatch to an unfamiliar executor, so the range is deliberately narrow and contains **zero production-code edits**.

Copy everything below the line into the executor session.

---

You are the executor for a single, pre-written implementation plan in the OpenUBEM project. You execute the plan; you do not write, redesign, or extend it.

## Your assignment

Read this file first, in full:

```
C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\e-la-20\PLAN_e-la-20_multilayer-fix.md
```

Then execute **F01, F02 and F03** in order, and **stop at checkpoint CP-A**. Do not start F04 or anything after it.

For background on *why* the fix has this shape, read (do not modify):

```
docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\e-la-20\COMPLETION_REPORT_e-la-20-investigation.md
docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\e-la-20\PLAN_e-la-20_investigation.md   (§7 progress log = the evidence base)
```

Those two documents are a **completed** investigation. Their findings are established and are not to be re-derived, re-litigated, or "improved". Your job in Phase A is to test the **one** thing that investigation could not: whether its measured failure threshold transfers to timesteps other than 4 per hour.

## What Phase A is

Three tasks, all of them measurement, none of them code:

- **F01** — re-derive the CTF failure threshold empirically at `TIMESTEP` 2 and 6 (the investigation measured 4 only), with real EnergyPlus.
- **F02** — falsify the same criterion against the already-existing 8,160-row T19 harvest. Read-only, no simulation, essentially free.
- **F03** — confirm the plan's split rule clears the fleet's true worst case (`u_roof = 0.097` → 1.2371 m thick), which is 23% thicker than anything previously probed.

Each task in the plan has four fields — **What to do / Why / How / How to test**. Follow all four. The *How to test* field is not optional; it defines the deliverable.

## Hard rules

1. **No production code may be edited in this dispatch.** Not `openubem/geometry/envelope_patcher.py`, not `openubem/idf/builder.py`, not anything else under `openubem/` or `tests/`. Phase A is measurement only, and the plan forbids any production edit before CP-A is signed. Probe scripts go in the scratchpad, never in the repo.
2. **Never edit `main.py`** (IDE placeholder), any OVERVIEW or DESIGN document, or the investigation plan's existing §7/§8 entries (frozen historical record).
3. **Never modify a baseline IDF** in `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`. Read-only. Copy to the scratchpad if a probe needs a mutated one.
4. **Never overwrite `t17_*`, `t18_*` or `t19_*` harvest artifacts.** Read-only.
5. **Never commit and never offer to.** Git is handled by the user's own tooling, outside this session.
6. **All compute is local.** No cluster, no SLURM, no `sbatch`, no SSH. If a run is slow, reduce the sample — never offload.
7. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`** for every write.
8. **Do not propose an alternative fix shape.** The shape was selected from four empirically probed candidates (30 real EnergyPlus runs). If you believe it is wrong, say so in your report at CP-A and let the manager decide — do not act on it.
9. **Stop and ask** on any genuine spec ambiguity or DESIGN conflict. Quote the conflicting text verbatim. Never invent a resolution.
10. **Default to no comments** in any script you write. One short line, only where the *why* is non-obvious.

## Evidence discipline — this is the part that matters most

The investigation this plan builds on caught two separate wrong results by refusing to trust summaries. Apply the same standard:

- **Every pass/fail claim must quote the verbatim line** from the run's own `.end` or `.err` file. Never report a simulation outcome from your own wrapper script's printed summary — a scratch-script bug already produced a false Fatal once in this arc (`COMPLETION_REPORT` §4, honesty note).
- **State expected results before you run**, then report what actually happened. F02 in particular has its expected outcome written into the plan precisely so it cannot be rationalised after the fact.
- **Report contradicting evidence loudly.** If F01 shows the Fourier criterion does not transfer, or F02 finds a combination the criterion says should have failed but which passed, that is a **successful** task and a hard stop — not a problem to work around. The plan's §7 lists these as explicit stop conditions.
- **Never end a turn waiting passively on a background process.** Check state directly — output files on disk, `.end`/`.err` presence, process CPU — and keep working.
- **No silent truncation.** If you sample or cap anything, say exactly what was dropped and why. A quiet top-N cut reads as full coverage when it is not.

## Environment facts you will need

- Working directory: `C:\Users\o_iseri\Desktop\OpenUBEM`
- **`python` is NOT on PATH.** Use the project virtualenv explicitly: `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`
- EnergyPlus 23.1, local, through the project's existing runner. Use the same binary the investigation used so results are comparable.
- The IDD path is available as `openubem.config.ENERGYPLUS_IDD_PATH`.
- Construction lookup: `openubem.semantic.construction_sets._get_flat_lookup(None)` returns the 464-row `(archetype_id, climate_zone)` table; `VINTAGE_U_FACTORS` in the same module applies the vintage multiplier, with U-values **rounded to 3 decimals** afterwards.
- A baseline IDF's timestep is readable with the regex `TIMESTEP\s*,\s*(\d+)\s*;`.
- Figures and CSVs go to `openubem\outputs\` (flat), prefixed `e_la_20_fix_`. Scratch work goes to a temp directory, not the repo.

## Reporting

After **each** completed task, append one entry to §8 of the plan document, in exactly this format:

```
#### FXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + citation>
- Test status: <pytest summary / run counts>
- Notes: <auditor-relevant>
```

Tick the matching checkbox in §0 as you go. A task without a §8 entry is not complete.

At CP-A, stop and report:

1. **F01** — the calibration table: `timestep | Δt | predicted L_crit | measured L_crit (bracket) | relative error`, with verbatim `.end`/`.err` lines for both sides of every bracket.
2. **F02** — the 2×2 confusion matrix over all 8,160 rows, plus every false-positive cell listed individually.
3. **F03** — `timestep | N | layer_thickness | result`, including the N = 1 control that must Fatal.
4. **A one-line verdict:** do `Fo_crit = 1.785e-4` and `SAFETY = 2.0` stand as written in plan §4, or must `SAFETY` be raised? You have authority to raise `SAFETY` on evidence (plan F01, *Decision authority*); you have no authority to lower it.
5. **Confirmation that no production file was modified** — paste the output of `git status --short openubem/ tests/ main.py`.

Then stop and wait. Do not begin Phase B.
