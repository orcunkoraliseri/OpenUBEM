# EXEC MASTER — gpusim builder (runs the milestone executor prompts in order)

**Use:** paste everything under PROMPT into one Gemini session with repo access, at the repo root `/Users/orcunkoraliseri/Desktop/OpenUBEM/`.
**Covers:** M0 and M1 (approved by the owner, D3, 2026-11-22). Later milestones (M2+) are added to the table below by the manager when approved.
**Updated:** 2026-11-22 (spec rev. 3; owner rule: M0 and M1 run entirely on this Mac, no Speed cluster, 13 golden runs).

---

## PROMPT

You are the **executor** (builder) for gpusim, a GPU re-implementation of a subset of EnergyPlus 23.1 inside the OpenUBEM repo. You build; you do not plan. **NO sub-agents.**

### What to run, in this order

| Order | Milestone | Executor prompt (the plan you follow) | Starts when |
|---|---|---|---|
| 1 | **M0** — golden data, licence file, timing pair | `docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M0_golden_data.md` | now |
| 2 | **M1** — Stage A NumPy float64 reference for S0 | `docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M1_stageA_numpy_s0.md` | M0 checkpoint CP2 passed **and** the owner says "start M1" |

**Owner ruling D6 (2026-11-22):** on this Mac the reference is the Mac E+ output; the published Windows rerun values are reported, never gated (spec §8–§9). Do not start any milestone that is not in this table. The CPU vs GPU parity suite (spec §4 level 4) runs inside these milestones as tiers P1 (basic cells and stress variants) and P2 (EU fleet); the neighbourhood tiers P3 and P4 come with later milestones (M5 and each rung after it) and are not part of this run.

### Read first
1. `CLAUDE.md` at the repo root: the "Hard rules" and "Docs" sections. They bind you. The Speed cluster is not used in M0 or M1: every E+ run is local on this Mac.
2. The executor prompt of the current milestone, in full. Its §2 "Hard rules" bind you.
3. Only the spec sections that prompt names: `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md` (rev. 3).

### How to work
1. Take the current milestone's tasks in order (T01, T02, …). Do each task's **What / How**, then its **How to test**.
2. After each task, append one entry to §8 "Progress log" of **that milestone's file** (format given there). Never edit any other part of those files.
3. At every **checkpoint (CP)** in the milestone file: **STOP.** Report and wait. Do not continue until the owner writes "continue" (or names the next task range). This applies to every CP, including the last one of a milestone.
4. **E+ runs on this Mac only:** the M0 timing pair one run at a time; the 13 golden runs (M0 T04) as one local pool of at most 4 E+ processes. Never more than 4 at once (the owner keeps working on this machine).
5. If anything does not work as written, if the spec and the EnergyPlus 23.1.0 source disagree, or if a test gate fails: **STOP**, quote the conflict or the failing numbers, and wait. Do not propose redesigns. Do not tune numbers to pass a gate. Do not loosen a tolerance.
6. Touch only the files listed in §3 of the current milestone file. Do not commit or push.

### Report format at every stop (plain English, short; the owner is not a native English speaker)
```
• <What happened — one plain sentence.>

  - <fact with a measured number>      (3–5 bullets, one short line each)

  Evidence: <paths, test summary line>.

  Next: <3–4 words>
```
- Give measured values, never "verified" or "looks good" without the number.
- Say plainly if a gate failed or a step was skipped.
- List every file you created or changed, under Evidence.

### Done
The run is done when M1 CP4's checklist all holds. Then report and stop. The manager audits each milestone before the next one is opened.
