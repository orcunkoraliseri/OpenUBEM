# EXEC MASTER — gpusim builder, M2 and M3 (Mac GPU)

**Use:** paste everything under PROMPT into one Gemini session with repo access, at the repo root `/Users/orcunkoraliseri/Desktop/OpenUBEM/`.
**Covers:** M2 (Stage B on MPS + framework spike) and M3 (Stage C fast kernel), approved by the owner on 2026-11-22. M0 and M1 are done (`EXEC_MASTER_gpusim.md`, M1 audited 2026-11-22, commit `8c33f1c7b`).
**Updated:** 2026-11-22 (spec rev. 3; owner rules: Mac only, no Speed cluster, no EnergyPlus runs in M2 or M3; stop after M3, then the Windows CUDA move).

**Kickoff (paste into the Gemini session):**
```
Read /Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_MASTER_gpusim_m2_m3.md and follow its PROMPT section.
Start M2 at T01. Execute the tasks in order. At a checkpoint where every check passes, write its report into the progress log and continue, except M2 CP2: there STOP and wait for the owner's framework choice (D-09).
STOP if a test or gate fails, the spec is ambiguous, or the E+ source disagrees with the spec; quote the problem and wait.
Append one progress-log entry per completed task under §8 of the milestone file and run the tests each task calls for.
Do not propose alternatives — execute the plan. NO sub-agents. Do not commit.
```

---

## PROMPT

You are the **executor** (builder) for gpusim, a GPU re-implementation of a subset of EnergyPlus 23.1 inside the OpenUBEM repo. You build; you do not plan. **NO sub-agents.**

### What to run, in this order

| Order | Milestone | Executor prompt (the plan you follow) | Starts when |
|---|---|---|---|
| 1 | **M2** — Stage B (PyTorch, Mac GPU, float32) + framework spike | `docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M2_stageB_spike_mps.md` | now |
| 2 | **M3** — Stage C fast chunked kernel for S0, fleet check, benchmark | `docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M3_stageC_metal_s0.md` | M2 CP2 audited **and** its §1 shows the owner's D-09 ruling **and** the owner says "start M3" |

**Owner ruling D6 (2026-11-22):** on this Mac the reference is the Mac E+ output and our own Stage A; the published Windows rerun values are reported, never gated. Do not start any milestone that is not in this table. The neighbourhood parity tiers P3 and P4 are not part of this run.

### Read first
1. `CLAUDE.md` at the repo root: the "Hard rules" and "Docs" sections bind you.
2. The executor prompt of the current milestone, in full. Its §2 "Hard rules" bind you.
3. Only the spec sections that prompt names: `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md` (rev. 3).

### How to work
1. Take the current milestone's tasks in order (T01, T02, …). Do each task's **What / How**, then its **How to test**.
2. After each task, append one entry to §8 "Progress log" of **that milestone's file** (format given there). Never edit any other part of those files.
3. At a checkpoint where every line holds, write the checkpoint report into §8 and continue. **Always STOP** at M2 CP2 (owner decision D-09) and at M3 CP2 (end of the Mac milestones).
4. **No EnergyPlus runs** in M2 or M3. The GPU is shared with the owner's work: run one GPU job at a time.
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
The run is done when M3 CP2's checklist all holds. Then report and stop. The manager audits each milestone before the next one is opened.
