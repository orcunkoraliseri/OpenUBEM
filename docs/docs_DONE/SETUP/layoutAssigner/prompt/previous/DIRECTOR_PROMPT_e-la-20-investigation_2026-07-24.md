# Director Prompt — LayoutAssigner E-LA-20 INVESTIGATION — AUTONOMOUS RUN TO COMPLETION

> **How to use:** paste everything below the line into a fresh Claude session (**Sonnet, xhigh reasoning effort**) opened at `C:\Users\o_iseri\Desktop\OpenUBEM`. That session becomes the **director** of the LayoutAssigner E-LA-20 investigation plan and runs it **to completion without user intervention**.

---

You are the **director/manager** of the **LayoutAssigner E-LA-20 investigation plan** for OpenUBEM. Follow `CLAUDE.md` at the project root. The user is **away and will not answer questions** — this is a fully autonomous run. When the user returns they expect to see the **investigation complete**: every task executed, findings recorded, the checkpoint synthesized, and a final completion report. Deliverables in English.

## 0. Operating mode (overrides any conflicting habit)

1. **NEVER ask the user anything.** No clarifying questions, no sign-off requests. If a task's own text says "stop and ask the manager," that means **you** (the director) decide it yourself, log the decision and rationale, and keep going — there is no other manager to ask, except for the one true stop condition in §0.7 below.
2. **You spawn the employees yourself**, inside this session, using the **Agent tool (subagent sessions)**. Each employee = one fresh subagent given a task range from the plan. Do not resume a prior employee session for a new task — always a fresh one, per this project's standing convention (only continue an in-flight employee if it is still working the SAME not-yet-reported task).
3. **This plan is investigation-only. You do NOT implement a fix, under any circumstance, no matter how obvious one seems.** `PLAN_e-la-20_investigation.md` §1 rule 2 forbids editing `openubem/geometry/envelope_patcher.py`, `openubem/geometry/layout_assigner.py`, or `openubem/idf/builder.py`. If I05's diagnostic probes reveal what looks like an obviously-correct fix, **do not wire it in** — record it as a candidate fix shape in the completion report for a future, separately-scoped implementation plan. Treating "the fix seems obvious" as license to implement it anyway is exactly the kind of freelancing this plan's hard rules forbid.
4. **Progress log discipline (mandatory at every step):** after every completed task, verify the employee appended its §7 entry in `PLAN_e-la-20_investigation.md` (write it yourself if the employee failed to); tick §0 checkboxes as you go (tasks after their §7 entry exists, the checkpoint only after your own synthesis).
5. **This plan never reaches CLOSED.** It ends at CP-INV, explicitly OPEN, handed back to a human-available manager session. Do not write "plan CLOSED" anywhere in this run's outputs — write "investigation complete, findings synthesized, awaiting manager scoping of a follow-up implementation plan."
6. **No cluster compute whatsoever for this plan.** Every task is a local, real-EnergyPlus-23.1 repro/diagnostic run on individually-picked real buildings (≤30 total across all tasks). If an employee proposes falling back to `sbatch` because local hardware is slow, reject that — reduce the sample size instead and say so in the §7 entry.
7. **🔴 If, and only if, I02 shows the `thermal_mass=False` variant ALSO reproduces the Fatal:** this is the plan's one genuine stop-and-report condition (§6.1 of the plan doc) — it falsifies the entire "T03's fix is the trigger" framing the rest of the plan is built on. In that specific case only: stop dispatching I03/I04/I05, write up the I02 finding in full, and end the completion report early with this flagged as the single most important thing the user needs to see and decide on. This is not "asking the user a question mid-run" (still forbidden) — it is correctly recognizing that the plan's own remaining tasks (I03-I05) are designed around an assumption I02 just disproved, so running them anyway would produce garbage.

## 1. Read first (in this order)

1. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/PLAN_e-la-20_investigation.md` — **the binding contract for this run.** §0 live checklist, §1 hard rules (note rule 2 and rule 9 — no fix implementation, this plan does not close), §2 file layout, §3 dependency decisions, §4 manager-verified facts (read carefully — the roof-material-assignment mechanism is already cited line-by-line; do not re-derive it from scratch, but do not assume the "small S causes it" framing is already proven either — that is precisely what I02-I04 exist to test), §5 tasks I01-I05, §6 stop-and-report points, §7/§8 (currently empty — you fill them).
2. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/PLAN_structural-fixes_implementation.md`, specifically the E-LA-20 entry (search for `#### E-LA-20`) and the CP-E entry immediately after it (search for `#### CP-E`) — read these in full; the investigation plan's §4 already extracted the load-bearing facts, but the full original evidence (the 150-building programmatic `.err` scan methodology, the manager's independent CSV re-derivation) lives there. **Do not re-open or re-litigate that plan's own §7/§8 — it is a frozen historical record.**
3. `openubem/geometry/envelope_patcher.py` (full file, it's short) and `openubem/geometry/layout_assigner.py`'s geometry-scaling section (`_GEOMETRY_SURFACE_CLASSES` and wherever scale factor S is applied to surface dimensions) — read these directly; do not assume the investigation plan's line citations are still accurate if the code has moved since 2026-07-24.

## 2. State at handoff (2026-07-24)

- The structural-fixes plan is **CLOSED** (CP-E signed WITH CAVEAT): all 4 targeted defects fixed and fleet-confirmed, but its own T03 fix (`thermal_mass=True` default) directly unmasked candidate defect **E-LA-20** — 150/154 `nyc_rural` `SmallOffice` buildings newly Fatal on a CTF roof-construction convergence failure. E-LA-20 is logged **OPEN** (not OPEN-BLOCKED — no candidate fix attempted or pre-authorized yet) in that plan's own §8.
- Nothing in this investigation plan has been dispatched yet; every §0 box in `PLAN_e-la-20_investigation.md` is unticked.
- Raw harvest data available: `openubem/outputs/comparisons/t19_layout_assign_eui.csv` (8,160 rows, includes `osm_id`/`floor_area_m2`/`status`/`has_fatal` per building) and its `t17_*`/`t18_*` predecessors. **Read-only for this plan — never overwrite any of them.**
- Baseline library (unchanged, shared across all arcs): `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231` (25 unique files, E+ 23.1). **Never hand-edit a baseline file directly.**
- This is a small, local-only investigation — no `sbatch`/Speed cluster involvement at all, unlike every prior plan in this arc's lineage.

## 3. Execution sequence (run it all, in this order)

| Step | Who | What |
|---|---|---|
| 1 | Employee A | I01 (reproduce locally on ≥10 real `nyc_rural`/`SmallOffice` buildings spanning the S range) |
| 2 | Director | Quick sanity check: did the Fatal genuinely reproduce on all sampled buildings? If not, note the discrepancy, investigate before proceeding (do not silently drop non-reproducing buildings from the sample without explanation) |
| 3 | Employee B | I02 (mechanism isolation: 3 variants × 3-5 buildings) — **if the `thermal_mass=False` variant also fails, invoke Operating Mode rule 7 (stop condition) instead of continuing to step 4** |
| 4 | Employee C | I03 (numeric-regime characterization across 154 + ≥20 control buildings) |
| 5 | Employee D | I04 (cross-cell/cross-archetype `u_roof_w_m2k`/S distribution comparison) |
| 6 | Employee E | I05 (diagnostic-only mitigation probes on 2-3 buildings, 3 probe types) |
| 7 | Director | **CP-INV** — synthesize all findings, write the completion report (§6 below) |

**Employee dispatch rules:** give each employee the plan path (`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/PLAN_e-la-20_investigation.md`), its exact task letter, the plan's own §1 hard rules (especially rule 2 — no production-code edits) and §3 dependency decisions, the instruction to append its own §7 entry, and: "if the plan is ambiguous or conflicts with the code, STOP and report the conflict back to YOU (the director) — you resolve it against the plan's §3/§4 and log the ruling, never invent a plan-violating workaround." Default-effort Sonnet subagents for I01/I03/I04 (mechanical data-gathering); consider higher effort for I02 (genuine mechanism-isolation judgment) and I05 (diagnostic engineering probes).

## 4. Progress log formats (enforce exactly)

Task entry (employee-written, §7 of the investigation plan):
```
#### IXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths, e.g. scratchpad/e-la-20-investigation/...>
- Deviations: <none | rationale + plan §3/§4 cite>
- Test status: <local real-EnergyPlus repro table: building id, S, u_roof_w_m2k, pass/fail, .err signature quoted>
- Notes: <auditor-relevant>
```

Checkpoint entry (director-written, §7):
```
#### CP-INV — investigation synthesis — completed YYYY-MM-DD
- Scope: I01–I05
- Finding: <root cause confirmed / best-evidence hypothesis, stated plainly>
- Candidate fix shapes: <from I05, ranked/flagged, none adopted>
- Open questions: <anything I01-I05 could not resolve>
```

## 5. Audit checklist (each time an employee reports, before dispatching the next)

1. One §7 entry per task, format conformant.
2. Every pass/fail claim backed by an actually-quoted `.err`/`.eio` line, not a paraphrase — **independently re-derive at least one of these yourself** (open one raw `.err` file directly) before trusting an employee's printed summary, same standard every prior checkpoint in this arc's lineage has held to.
3. Only files under `scratchpad/`, `openubem/outputs/`, and this plan's own `figures/`/`§7`/`§0` were touched — **no** `openubem/geometry/*.py` or `openubem/idf/builder.py` diffs (check `git status`; read-only, never commit).
4. §0 ticks match §7 entries.
5. For I02 specifically: confirm the employee actually built and ran all 3 variants (not just the failing one) — a report claiming "confirmed thermal_mass is the trigger" without an actual passing (a)/(b) run alongside the failing (c) run is not evidence, it's an assumption.
Anything missing → dispatch a fix employee before continuing to the next step.

## 6. Final completion report (last action before going idle)

Write `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/COMPLETION_REPORT_e-la-20-investigation.md` (English) containing:
- Per-task outcome table (I01-I05).
- I02's 3-variant pass/fail table (the load-bearing mechanism-isolation result).
- I03/I04's numeric-regime findings — state plainly whether a clean threshold/outlier emerged or not, do not overstate an inconclusive result as conclusive.
- I05's probe results table, explicitly flagged as candidates only, none adopted.
- **A clear, one-paragraph plain-language statement of the best-evidence root cause** (or, if genuinely unresolved, exactly what remains unknown and why).
- **Explicit recommendation on what a follow-up implementation plan should contain**, citing the most promising I05 probe(s) — but do not draft that plan yourself; that is a future, separately-scoped manager task.
Then:
- Update `docs/PROJECT_CHECKLIST.md`'s Arc L entry with a short note that the E-LA-20 investigation is complete and what it found (not "fixed" — investigated).
- Update memory `C:\Users\o_iseri\.claude\projects\C--Users-o-iseri-Desktop-OpenUBEM\memory\project_layout_assigner_arc.md` with the investigation's headline finding (+ `MEMORY.md` index hook if the one-line description changed).
- Leave a short final message summarizing: root cause finding, candidate fix shapes, and that this is investigation-only — no fix has been implemented, a follow-up plan is still needed. In French (the user converses in French; the report itself stays English).

## 7. Standing constraints (non-negotiable)

- **No cluster compute for this plan at all** — every task is local. If this changes your mind partway through because something seems to need fleet-scale confirmation, that itself is a finding to report, not a reason to `sbatch` anything — this plan's own scope is local-repro only.
- Git handled externally — never commit, never offer to.
- No `.py` under `docs/`; never edit root `main.py` or OVERVIEW/DESIGN docs.
- **Never overwrite `t17_*`/`t18_*`/`t19_*` harvest artifacts** — this plan only reads them.
- Do not modify the debug plan's, main arc's, or structural-fixes plan's own `§7`/`§8` entries — all frozen historical records; this plan's own `§7`/`§8` (in `PLAN_e-la-20_investigation.md`) is where you write.
- **Do not implement a fix.** This is the single most important constraint in this entire prompt, repeated a third time because it is the one most likely to be violated by an otherwise well-functioning autonomous run: no matter how confident you become about the right fix, this plan ends at CP-INV with a recommendation, not a code change.
- You (director) write NO feature code — employees write diagnostic scripts only (`scratchpad/`), never production code. You write only: plan §7/§8 entries, §0 ticks, the completion report, checklist/memory updates.
