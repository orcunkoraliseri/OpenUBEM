# EXECUTOR PROMPT — storey matching, **Phase C** (verification)

**For:** an external executor session (Gemini / Antigravity) · **Date:** 2026-07-26
**Plan:** `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_implementation.md`

> ## ✅ GATES CLEARED 2026-07-26 — this prompt is live
>
> **Gate 1 — CP-B signed by the manager 2026-07-26.** See §7. Note the amendment that came with it:
> the identity guarantee is no longer *bit-identity of coordinates*, because B08b made re-centring
> unconditional. It is now *numerically identical scaling factors, geometry identical up to a rigid
> XY translation, energy verified null*. Cite the amendment whenever you cite CP-B.
>
> **Gate 2 — still in force.** C02 is a ~15-hour, 12-cell, 8,160-building cluster re-run and carries
> an explicit **manager go/no-go**. Run C01, then stop and ask. Do not launch C02 on your own
> initiative, no matter how well C01 went.
>
> **Gate 3 — cleared.** B06 closed E-LA-27: **134,642 → 0 Severe** on the A2-bis scenario, verbatim
> from `eplusout.err`. C02 is no longer blocked on it.
>
> **🔴 New reporting requirement, from the B06 audit — applies to C01 *and* C02.** D9's
> `transformer_scale_ratio` is a **conservative upper bound validated at exactly one multiplier (4)**,
> not a derived load ratio. It scales as `planar_area_factor × multiplier`, so a building at
> `n_real=20, n_proto=3` scales transformer nameplate by roughly 6× and **nothing has been measured
> there**. Both tasks must report, across the multiplier range, (i) Severe counts and (ii) the
> transformer's energy effect on the **805 exposed buildings** of F-11. **C01 must include at least
> one high-multiplier case.** Sampling only low multipliers would reproduce exactly the blind spot
> that hid E-LA-20 from every ≤28-building local sample across two plans.
>
> **C04's "before" panel now has two archived states, both real pipeline output — use them, and
> label which is which:** `figures/before_B05/` (pre-Zone-Origin-fix) and `figures/before_B08b/`
> (post-B05, pre-re-centring). The current files at the user's two viewer paths are the "after".
>
> **Also changed at CP-B:** per **E-LA-30**
> the A4-bis viewer artifacts do not depict the pipeline at all — its scaler is a measured no-op on
> 25/25 prototypes. Read E-LA-30 in §8 before assembling any before/after comparison, and do not
> quote the 4,043 / 98.24% or 4,003 / 97.17% overlap figures as a pipeline baseline.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_implementation.md` in full before doing anything, **including its §0 checklist and its §7 progress log**. That document is the contract; this message only scopes your run.

You are executing **Phase C — tasks C01, then C02 (gated), then C04, then C03, in that order.** Note that the plan's task order is C01 → C02 → C04 → C03, not numerical order. Stop at CP-C.

**First, verify your gate.** Confirm in §0 that B01–B04 are ticked `[x]` and CP-B is signed. If not, STOP and say so.

**What Phase C is.** Phase B changed the geometry that every existing `layout_assign` energy result rests on. T17, T18 and T19 are now void — not outdated, *void*. Phase C's job is to produce the first defensible number the mode has had since the fix, and the visual evidence that the geometry is actually right rather than merely differently wrong.

**Hard rules — all of §1 of the plan applies. These are the ones that get broken most often:**

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never `cd` out of it for a write.
2. **🔴 NEVER run compute on the Speed login node.** No blocking `srun`, no `ssh … python …`, no `ssh … srun …`. All cluster compute goes through `sbatch --array`, fire-and-forget, and you read the output files afterwards. The login node may only do `mkdir`, `scp`, `tar`, `squeue`, `sacct`. This rule has no exceptions and no "just this once".
3. **Never cancel, requeue or deprioritise a cluster job that is not part of this project.**
4. **When an EnergyPlus run fails, report the `** Severe **` line verbatim.** Never the `.end` file, never a wrapper's verdict. The `.end` file tells you *that* EnergyPlus died, never *why*.
5. **Row count must equal artifact count, and both must be stated** in every progress entry that reports runs.
6. **Ground truth comes from run artifacts** — never from a restatement of the hypothesis, and never from a prior artifact reused as if it were a matched control.
7. Never edit root `main.py`, never edit OVERVIEW or DESIGN docs, never put a `.py` file under `docs/`. **Never run `git commit`.**
8. **Every artifact of this arc goes under `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/`** — `results/` for harvest CSVs, `figures/` for stills and viewer HTML. Figures additionally keep their canonical flat copy in `openubem/outputs/`.
9. After each completed task: append one progress-log entry under **§7**, then tick that task's row in **§0**. **Never tick a checkpoint row (🔶) — manager only.**

**C01 gates C02; it does not replace it.** Local samples in this arc have repeatedly missed fleet-scale defects — E-LA-20 was invisible to every ≤28-building local sample across two separate plans. A clean C01 is permission to ask for C02, nothing more. Cover all five cases the plan names: shorter than prototype, taller, equal, single-storey, and one excluded-fallback archetype.

**C02 — stop and ask before launching.** New job/harvest generation `t20_*`; leave `t17_`/`t18_`/`t19_` untouched. Report the acceptance criteria the plan states, in particular: fleet success rate against T19's 97.92%, every remaining failure mapped to a known defect ID, and **the heating ratio of F-08 re-measured on the same cell and archetype**. The entire purpose of the fix is that this ratio moves toward 1.0. **Report it whether it does or not.** A fix that does not move it is a finding, not a failure to be reframed. And note in the report that a clean comparison against T19 is not available while E-LA-22 stands — say so plainly rather than presenting deltas as if they were attributable.

**C04 — the one instruction here that is easy to get wrong.** Re-run A4's viewer export on the same two cells from C02's `t20_*` output and assemble a three-way panel: real `auto` massing · `layout_assign` before · `layout_assign` after. **Reuse A4's original artifact for the "before" panel. Do not regenerate it, and do not re-render it from post-fix code.** A before/after where both sides were produced by the new code proves nothing — this is the same class of error as E-LA-24, which is already logged in this arc. Same camera, same colour scale, same buildings across all three scenes.

For at least 5 named buildings spanning shorter/equal/taller than prototype, state the storey count and plate area in all three scenes and confirm the "after" scene matches `num_floors`.

If A4 established that the viewer cannot ingest `layout_assign` IDFs, C04 is **blocked by that finding**, not by this plan. Report it at CP-C rather than working around it, and do not modify geometry to make it render.

**C03 — Q3 is closed by this arc or it is not closed at all.** The documentation closure must include Q3's own entry in `DONE/DONE-implementation_plan.md` §7, plus the results-doc section, this plan's §8/§9, and `PROJECT_CHECKLIST.md` §L.

**When you finish C03, stop and report** for CP-C: the four progress-log entries, the re-measured F-08 heating ratio next to its original value, the fleet success rate against T19's, and the three-way visual panel. Then wait for the manager's signature.
