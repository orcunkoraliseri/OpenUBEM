# EXECUTOR PROMPT — storey matching, **Phase B** (implementation)

**For:** an external executor session (Gemini / Antigravity) · **Date:** 2026-07-26
**Plan:** `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_implementation.md`

> ## 🚧 DO NOT PASTE THIS YET
>
> **Gate: CP-A must be signed by the manager first.** Phase A may change what Phase B is. The plan
> says so in its own §5 heading: Phase B is *"written against the expected Phase-A outcome; the
> manager rewrites it at CP-A if A2/A3 land differently."*
>
> Before pasting, the manager must have: (a) chosen the D3 mechanism per archetype
> (multiplier / band deletion / hybrid / excluded-with-fallback), (b) ruled on A1b's imputation
> trade, and (c) updated §5 Phase B in the plan if A2/A3 landed differently from expectation.
>
> **If the plan's Phase B was rewritten at CP-A, this prompt still works unchanged** — it delegates
> the task content to the document rather than restating it. That is deliberate: a prompt that
> duplicated the tasks would silently go stale the moment the manager edited the plan.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_implementation.md` in full before doing anything, **including its §0 checklist and its §7 progress log** — the log is where Phase A recorded what was actually found, and it overrides any expectation written elsewhere in the plan. That document is the contract; this message only scopes your run.

You are executing **Phase B only — tasks B01, B02, B03, B04, in that order.** Stop at CP-B.

**First, verify your gate.** Confirm in §0 that A1, A1b, A2, A3 and A4 are all ticked `[x]` and that CP-A shows as signed. **If any Phase-A row is not ticked, or CP-A is unsigned, STOP immediately and say so** — you are not authorised to write production code. This is the plan's rule 1.3 and it is binding.

**What Phase B is.** You are replacing a single-scalar geometric substitution with a two-part one. Today `calculate_scaling_factor()` returns `√(real_area / baseline_area)` and applies it to X and Y with Z untouched, so the prototype keeps its own storey count. After Phase B, the prototype's storey **count** follows the real building's `num_floors` (which is already at the call site and currently discarded), and only the floor **plate** is scaled in plan. Storey **height** stays the prototype's real height — that is by design, not an omission, and you must not change it.

**Hard rules — all of §1 of the plan applies. These are the ones that get broken most often:**

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never `cd` out of it for a write.
2. **Do not write plans, and do not propose alternatives.** Execute this one. If the plan conflicts with the code or with DESIGN, **STOP and quote the conflict verbatim** — do not choose between them.
3. Never edit root `main.py`, never edit OVERVIEW or DESIGN docs, never put a `.py` file under `docs/`. **Never run `git commit`** — git is handled externally by the user.
4. **Do not touch the E-LA-20 fix.** `openubem/idf/opaque_assembly.py` and its two frozen constants (`T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`) must not move. If storey matching appears to require changing them, STOP and report.
5. **The prototype library is read-only.** Never modify the 25 baseline IDFs on disk. Every change is made in memory on the loaded `idf` object, exactly as the current code already does.
6. **Every artifact of this arc goes under `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/`.** Nothing in the parent `debug/` or at the arc root.
7. Default to no comments; one short line only where the WHY is non-obvious.
8. After each completed task: append one progress-log entry under **§7** using the template there, then tick that task's row in **§0**. **Never tick a checkpoint row (🔶) — manager only.**

**The one thing that must not move, and it is easy to break silently.** For a building whose real storey count already equals its prototype's (`n_real == n_proto`), the new planar scaling factor must equal today's **exactly**. That identity case is the regression guard for the whole phase. It is also the trap B02 exists to avoid: if you match storeys *and* keep total-area scaling, you shrink the plate twice. Assert the identity in a test, do not merely reason that it holds.

**Take the band map as input, never assume it.** B01's function receives A1's map of which zones belong to which floor band. Do not re-derive it, do not hardcode a G/M/T assumption — A1 exists precisely because that convention was verified on a sample only and `OfficeSmall` already did not match it.

**On B02's signature.** Either keep the old signature working for non-`layout_assign` callers, or prove by grep that there are none. State which of the two you did.

**On B04.** State the pass count **against the pre-change baseline**, not just "all green". Establish that baseline before you start editing, on the current `HEAD`. Any drop in passing tests is a stop, not something to fix by adjusting the test.

**Do not run any fleet simulation in this phase**, and do not touch the cluster. Phase B is local code plus local tests. The fleet re-run is C02, it costs ~15 hours, and it needs an explicit manager go/no-go.

**When you finish B04, stop.** Report: the four progress-log entries, the test pass count before and after, which mechanism you implemented for which archetypes and where that decision is recorded in the CP-A signature, and the identity-case assertion. Then wait. At CP-B the manager will independently reproduce the identity-case guarantee by reconstructing the old code in a scratchpad — **not** by reading your diff — so make sure your claim is actually true rather than merely plausible.
