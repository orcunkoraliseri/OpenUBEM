# EXECUTOR PROMPT — storey matching, **B06** (close E-LA-27 properly)

**For:** a fresh executor session · **Date:** 2026-07-26
**Plan:** `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_implementation.md`

> ## 🚧 GATE — do not paste this while B05 is live
>
> B06 edits capacity handling in `openubem/geometry/layout_assigner.py`. B05/B05e/B05f are editing
> `scale_baseline_idf()` in the same file. Confirm in §0 that **B05, B05e and B05f are all ticked
> `[x]`** before starting. If they are not, STOP and say so.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_implementation.md` in full before doing anything, **including its §0 checklist, §1 hard rules, §7 progress log and §8 error log**. That document is the contract; this message only scopes your run.

You are executing **B06 only.** Stop and report when done. Do not start C01, C02, or any other task.

## What you are fixing

`layout_assign` substitutes a DOE prototype and, when the real building is taller than the prototype, `match_storeys()` sets a **Zone Multiplier** on the middle band. Fixed-capacity equipment does not see that multiplier, so B01b scaled those objects by the geometric `area_scale_ratio`. **That is measured, in a real production run, to be insufficient** — read the "🔴 B01b update" block under **E-LA-27** in §8 before writing any code. The headline numbers:

- `results/b01b_run_matched/eplusout.err` — `134642 Severe Errors`, `** Severe ** Transformer Overloaded`.
- Patching that same model's `Rated Capacity` to 500,000 VA reaches **0 Severe** → the wiring is correct, the magnitude is not.
- A zero-plan-shrink run is **worse** (150,283 occurrences) → not a shrink artefact.
- Against a clean `S=1` control, total electricity grows **2.456×** where the applied geometric factor was **2.0×** — 81% coverage. Cooling electricity goes **0.00 → non-zero** under the multiplier.

That last point is the whole reason a closed form will not work: the amplified middle-band internal gains change the building's heating/cooling balance in a way no linear floor-area ratio predicts.

## The mechanism, already decided — do not re-debate it

Apply the **E-LA-11 pattern**, which this arc already used successfully for the LargeOffice DataCenter coils: for each archetype, take **one real `S=1` EnergyPlus reference run**, read back the autosized / as-designed capacities, record them as measured constants, and have production scale *those* values. Cover at minimum the classes B01b added — `ElectricLoadCenter:Generators`, `Generator:PVWatts`, `Boiler:HotWater`, `Chiller:Electric:EIR`, `Chiller:Electric:ReformulatedEIR`, `Humidifier:Steam:Electric` — plus `ElectricLoadCenter:Transformer`.

**This is a measurement, not a derivation.** If you find yourself deriving a correction coefficient analytically, you have left the task.

## 🔴 Cluster rules — no exceptions, no "just this once"

25 archetypes × 1 reference run is a textbook `sbatch --array` job.

1. **NEVER run compute on the Speed login node.** No blocking `srun`, no `ssh … python …`, no `ssh … srun …`. All compute goes through `sbatch --array`, **fire-and-forget**, and you read the output files afterwards.
2. The login node may only do `mkdir`, `scp`, `tar`, `squeue`, `sacct`. If a remote step needs Python, wrap it in an sbatch script.
3. **Never cancel, requeue or deprioritise a cluster job that is not part of this project.**
4. Poll no more often than every **30 minutes**, and wait on the **artifact**, not on the process. (`pgrep` does not track Windows console processes reliably — that mistake produced a false "did not complete" report in this arc today.)

## Acceptance test — unchanged from B01b, and it is a number, not a judgement

**0 Severe** on A2-bis's scenario (`MediumOffice`, `n_real=6`, `n_proto=3`) through the real `BuildingIDF.build()` path.

- Report the Severe count **verbatim from `eplusout.err`**. Never from the `.end` file — `.end` tells you *that* EnergyPlus died, never *why*.
- **If it is not 0, report the number.** A fix that does not reach 0 is a finding to forward, not a result to reframe. B01b's refusal to close on bad evidence is the most valuable thing that happened in Phase B; hold the same line.
- Also re-measure the `S=1`-control electricity ratio (was 2.456× against 2.0× applied) and state where it lands.

## Hard rules

Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never edit root `main.py`, OVERVIEW or DESIGN docs. No `.py` files under `docs/`. **Never run `git commit`.** `openubem/viz/` is READ-ONLY under this plan. Do not touch `openubem/idf/opaque_assembly.py` or its frozen constants (`T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`). The 25 baseline prototype IDFs are **read-only** — every change happens in memory. Row count must equal artifact count, and both must be stated. Use `.venv/Scripts/python.exe`. Figures go to `openubem/outputs/` flat **and** the arc-local `figures/`.

Default to no comments; one short line only where the WHY is non-obvious. Stop and ask on spec ambiguity — never invent.

## Reporting

Append one progress-log entry under **§7** (Artifacts / Deviations / Test status / Notes) and tick B06's row in **§0**. **Never tick a 🔶 checkpoint row — manager only.**

Report: the measured `S=1` constants per archetype, the row-count = artifact-count statement for the cluster array, the verbatim Severe line and count from the acceptance run, the re-measured electricity ratio, and any archetype you could not produce a reference for and why.

**C02 — the ~15 h, 8,160-building fleet re-run — is gated on this task.** Do not launch it, and do not treat a good result here as permission to.
