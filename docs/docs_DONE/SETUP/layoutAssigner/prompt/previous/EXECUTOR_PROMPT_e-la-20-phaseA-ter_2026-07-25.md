# EXECUTOR PROMPT — E-LA-20 Phase A-ter (F03-T, stop at CP-A-bis)

**Target executor:** Gemini / Antigravity · **Written by:** manager session · **Date:** 2026-07-25
**Context:** CP-A is signed. Both Phase-A-bis tasks were accepted — and F03-R's result **retired the plan's own fix shape**. This dispatch calibrates the replacement. Still zero production-code edits.

Copy everything below the line into a **fresh** executor session.

---

You are the executor for a pre-written implementation plan in the OpenUBEM project. You execute the plan; you do not rewrite it.

**Your previous dispatch went well.** F02-R and F03-R were both accepted at audit, and the manager reproduced both against the raw artifacts independently of your scripts. The evidence discipline held: severe lines quoted, ground truth read from artifacts, row counts matched directory counts, controls checked first. Keep doing exactly that.

**F03-R did something better than confirm the plan — it falsified it.** Splitting into N layers cannot fix the worst case at any N ≤ 10, because splitting preserves the assembly's total `R·C` exactly and `R·C` is the quantity the CTF series responds to. The adaptive-N shape is retired. Reporting that clearly was the right outcome, not a failure.

The replacement shape — pre-registered in the plan as reserve candidate (c2) — is now adopted: **a capped mass layer plus a `MATERIAL:NOMASS` layer carrying the residual R.** It has one free constant, `T_MASS_MAX`, and that constant is unmeasured. Measuring it is your entire assignment.

## Your assignment

Read this file first, in full:

```
C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\e-la-20\PLAN_e-la-20_multilayer-fix.md
```

Pay particular attention to:

- **§4-ter** — the adopted shape, the rules (T-a) vs (T-b), and the reasoning. This is binding.
- **§6 Phase A-ter → F03-T** — your single task, with its five series, controls and decision authority.
- **§8 AUDIT — CP-A-bis** — what was accepted and why, including the one place the manager parted company with your write-up.

**§4 and §4-bis are superseded.** Do not use `L_CRIT_MEASURED`, `SAFETY_L`, `Fo_crit`, `SAFETY`, or any N-splitting logic. The single-layer boundary measurement inside §4-bis still stands and is reused by §4-ter; nothing else in those sections does.

Execute **F03-T**, then **stop at CP-A-bis**. Do not start F04 or anything after it — F04–F07 are written against the retired shape and are stale; the manager will rewrite them once your constants land.

## Hard rules

1. **No production code may be edited in this dispatch.** Not `openubem/geometry/envelope_patcher.py`, not `openubem/idf/builder.py`, not anything under `openubem/` or `tests/`. Probe scripts go in the scratchpad.
2. **Never edit** `main.py`, any OVERVIEW or DESIGN document, the investigation plan's §7/§8 entries, or — in the multi-layer-fix plan — **any existing §8 entry, including the two AUDIT entries**. Append below them.
3. **Never modify a baseline IDF** in `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`. Read-only; copy to the scratchpad if a probe needs a mutated one.
4. **Never overwrite `t17_*`, `t18_*`, `t19_*` harvest artifacts, or any existing `e_la_20_fix_f0*` CSV.** This task writes `f03t_` names only. Every prior artifact stays on disk as part of the record.
5. **Never commit and never offer to.** Git is handled by the user's own tooling.
6. **All compute is local.** No cluster, no SLURM, no `sbatch`, no SSH. If a run is slow, reduce the sample — never offload.
7. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`** for every write.
8. **Do not pick `T_MASS_MAX`.** Report the measured bracket; the manager picks the margin inside it. This is the one decision explicitly reserved.
9. **Stop and ask** on any genuine spec ambiguity. Quote the conflicting text verbatim; never invent a resolution.
10. **Default to no comments** in scripts. One short line, only where the *why* is non-obvious.

## Evidence discipline — unchanged, and it is why the last dispatch was accepted

- **Quote the `** Severe **` line, never `.end` alone.** `.end` says *that* E+ died, never *why*. A CTF failure means the literal string `CTF calculation convergence problem` is present in `eplusout.err`. Any other Fatal is a harness bug: stop, fix the harness, do not score the run.
- **Keep the four guarantees your F03-R harness already has** — case-insensitive object matching, the pre-flight assertion that exactly one roof `CONSTRUCTION` exists and every referenced layer resolves to a real `MATERIAL`, the literal-string classifier, and the hard abort on any non-CTF Fatal. Reuse `scratchpad/e-la-20-fix/f03r_run.py`; it is audited and correct. Change only the assembly-construction step.
- **Controls first, abort on failure.** `u = 0.097` with `t_mass = total_t` and no NOMASS layer must FATAL with a genuine CTF severe. `u = 0.5` with `t_mass = total_t` must PASS. A harness that cannot reproduce today's defect proves nothing about the fix.
- **Row count must equal on-disk directory count.** State both numbers explicitly for each CSV.
- **Read every EUI figure from the run's own output file**, never from a wrapper script's printed summary.
- **A silently-empty lookup is a bug, not a no-op.** Assert non-empty after every IDF object query.
- **Report contradicting evidence loudly and stop.** If no `t_mass ≥ 0.10 m` clears `u = 0.097`, that retires (c2) as well — say so plainly; it is a successful task, not a problem to engineer around. Same if the discriminator and the sweep disagree.
- **Do not interpolate in your conclusions.** State what you measured and where the untested gaps are. The one correction at the last audit was a boundary asserted between two tested points.
- **Never end a turn waiting passively on a background process.** Check output files, `.end`/`.err` presence and process CPU directly, and keep working.

## Environment facts you will need

- Working directory: `C:\Users\o_iseri\Desktop\OpenUBEM`
- **`python` is NOT on PATH.** Use `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`
- EnergyPlus 23.1 at `C:\EnergyPlusV23-1-0\energyplus.exe`, local — the same binary F01, F02-R and F03-R used.
- IDD path: `openubem.config.ENERGYPLUS_IDD_PATH`. Construction lookup: `openubem.semantic.construction_sets._get_flat_lookup(None)`.
- **Object names in generated IDFs are mixed case** — `LA_Roof_Assembly`, `LA_Roof_Construction`. EnergyPlus reports them upper-cased in `.err`. Normalise case on both sides; never compare the two forms directly.
- `MATERIAL:NOMASS` takes `Name`, `Roughness`, `Thermal_Resistance` (m²K/W), and the three absorptances. It contributes R and **no** capacitance — that is the whole point of the shape.
- Material properties for the mass layer are **unchanged**: `_K = 0.12`, ρ = 800, cp = 1000. Changing them is out of scope (§3).
- Outputs go to `openubem\outputs\` (flat), prefixed `e_la_20_fix_f03t_`. Scratch work stays in `scratchpad/e-la-20-fix/`.

## Reporting

Append one entry to §8 of the plan document — below the CP-A-bis AUDIT entry, not inside it — in exactly this format:

```
#### F03-T — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + citation>
- Test status: <run counts, controls, row-count vs directory-count>
- Notes: <auditor-relevant>
```

Tick the matching checkbox in §0. A task without a §8 entry is not complete.

At CP-A-bis, stop and report:

1. **The discriminator** — `u = 0.097`, `t_mass = 0.85 m` + NOMASS, 4 ts/h: PASS or FATAL, with its verbatim severe line if it failed, and which rule it selects — **(T-a)** the massless R is inert and the cap is a plain constant, or **(T-b)** whole-assembly `R·C` governs and the cap must scale with R.
2. **The boundary bracket** — largest `t_mass` that passes and smallest that fails at `u = 0.097`. Do not pick a value inside it.
3. **Timestep confirmation** (2 and 6 ts/h) and **coverage** (`u ∈ {0.105, 0.119, 0.138, 0.182}`), as tables.
4. **Both EUI deltas** — the `u = 0.182` figure (today vs (c2)) and the `u = 0.5` figure (must be exactly 0.0), plus the `u = 0.097` (c2) vs `thermal_mass=False` bracket.
5. **Row count vs on-disk directory count**, stated side by side, for each of the two CSVs.
6. **Confirmation that no production file was modified** — paste the output of `git status --short openubem/ tests/ main.py`.

Then stop and wait. Do not begin Phase B.
