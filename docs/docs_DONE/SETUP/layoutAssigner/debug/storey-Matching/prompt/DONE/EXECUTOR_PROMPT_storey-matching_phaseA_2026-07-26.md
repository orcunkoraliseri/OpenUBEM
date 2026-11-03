# EXECUTOR PROMPT — storey matching, **Phase A** (calibration)

**For:** an external executor session (Gemini / Antigravity) · **Date:** 2026-07-26
**Plan:** `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_implementation.md`
**Gate:** none — Phase A is the entry point of the arc. **Ready to paste now.**

> **Manager note (not part of the prompt).** Phase A writes **no production code**. It runs on
> existing `t19_*` and `phaseE` artifacts plus local EnergyPlus for A2/A3. It ends at CP-A, where two
> pre-registered stop conditions hand the decision back to the manager. Paste everything between the
> rules below, verbatim.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_implementation.md` in full before doing anything. That document is the contract; this message only scopes your run.

You are executing **Phase A only — tasks A1, A1b, A2, A3, A4, in that order.** Stop at CP-A. Do not begin Phase B under any circumstances.

**What Phase A is.** The plan proposes changing how `layout_assign` scales DOE prototypes: today it collapses a real building into one scalar `S = real_area / baseline_area` and applies `√S` to X and Y while leaving Z untouched, so the prototype keeps its own storey count regardless of the real building's. Phase A does not fix that. Phase A measures whether the proposed fix is buildable, and at what cost. Every Phase-A task is measurement.

**Hard rules — all of §1 of the plan applies. These are the ones that get broken most often:**

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never `cd` out of it for a write.
2. **No production code in Phase A.** After each task, run `git status --short openubem/ tests/ main.py` and paste the output into that task's progress entry. It must be clean. Measurement harnesses go in `scripts/analysis/` and are throwaway.
3. **Do not write plans, and do not propose alternatives.** Execute this one. If the plan conflicts with the code or with DESIGN, **STOP and quote the conflict verbatim** — do not choose between them.
4. Never edit root `main.py`, never edit OVERVIEW or DESIGN docs, never put a `.py` file under `docs/`. **Never run `git commit`** — git is handled externally by the user.
5. **Do not touch the E-LA-20 fix.** `openubem/idf/opaque_assembly.py` and its two frozen constants (`T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`) are out of scope. If storey matching appears to require moving them, STOP and report.
6. **When an EnergyPlus run fails, report the `** Severe **` line verbatim.** Never the `.end` file, never a wrapper's verdict. The `.end` file tells you *that* EnergyPlus died, never *why*. A prior task in this arc misreported eleven `GetSurfaceData` input failures as CTF-solver failures because it read the wrong artifact.
7. **Row count must equal artifact count, and both must be stated** in every progress entry that reports runs.
8. **Ground truth comes from run artifacts** — never from a restatement of the hypothesis, and never from a prior artifact reused as if it were a matched control.
9. Default to no comments; one short line only where the WHY is non-obvious.
10. **Every artifact of this arc goes under `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/`** — `results/` for CSVs, `figures/` for figures and viewer HTML. Create them on first use. Figures additionally keep their canonical flat copy in `openubem/outputs/`; that is a copy, not a second home. Nothing lands in the parent `debug/` or at the arc root.
11. After each completed task: append one progress-log entry under **§7** of the plan using the template given there, then tick that task's row in the **§0** checklist. **Never tick a checkpoint row (🔶) — those are the manager's.**

**Task order matters, and A4 is the reason.** A4 captures 3D visual evidence of the *current* distortion. Once Phase B lands there is no way to produce an honest "before" artifact ever again, and task C04 becomes unprovable. A4 must complete while the code is still unchanged. Do not defer it as "the easy visual one".

**Two stop conditions are pre-registered. They are not judgement calls:**

- **A1b:** if **more than 50%** of buildings under 500 m² carry an *imputed* `num_floors`, stop and report before Phase B. The fix may still be right, but it stops being obviously right, and that is the manager's call — not yours.
- **A3:** if deleting a prototype floor band cannot be done without hand-editing HVAC topology for that archetype, stop and report at CP-A. **Do not freelance an HVAC rewrite.** That is a different arc with a different risk profile.

**On A4's known unknown.** The 3D viewer (`openubem/viz/`) was built and validated on `auto`-mode geometry only. Whether it can ingest `layout_assign` IDFs at all is unverified. Check it explicitly and report the answer either way. **If it cannot ingest them, STOP and report that as a finding.** Do not modify geometry to make it render — that breaks the viewer's faithful-to-model constraint and destroys the artifact's entire value. The viewer is read-only in this arc; if it needs changes, that is a finding, not a task.

**A2 and A3 require real EnergyPlus 23.1 runs, locally.** Do not simulate, mock, or reason about what EnergyPlus would probably do. For A2 specifically: confirm from the `.eio`/`.err` that the `Zone Multiplier` actually reached sizing — a multiplier that is silently ignored looks exactly like a clean pass.

**When you finish A4, stop.** Report to the manager: the five progress-log entries, the answers to both stop conditions, what A1 found about whether the G/M/T band convention generalises across all 25 prototypes, and your recommendation on the D3 mechanism per archetype. Then wait. CP-A is a manager signature and the plan explicitly expects Phase A to change Phase B — in the preceding E-LA-20 arc, Phase A destroyed the plan's own adopted fix shape twice, and both stops were correct.
