# EXECUTOR PROMPT — storey matching, **Phase A-bis** (corrective round)

**For:** an external executor session (Gemini / Antigravity) · **Date:** 2026-07-26
**Plan:** `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_implementation.md`
**Gate:** none — **ready to paste now.** This replaces the Phase-A prompt, which has been executed.

> **Manager note (not part of the prompt).** CP-A was reviewed on 2026-07-26 and **not signed**.
> A1, A1b and A3 were accepted; A2 came back void and A4 came back half-built. The audit is in §7 of
> the plan under *"🔶 CP-A — manager audit"*, with the evidence quoted from the run artifacts. This
> prompt covers only the three corrective tasks. Paste everything below the rule, verbatim.
>
> Use a **fresh session**. Do not continue the session that ran Phase A — it reported two claims its
> own artifacts contradict, and re-waking it re-imports that context.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_implementation.md` in full before doing anything, **including its §0 checklist, its §7 progress log, and its §8 error log**. Start with the §7 entry titled **"🔶 CP-A — manager audit — NOT SIGNED 2026-07-26"** — it states exactly why the previous round did not pass, and what you are correcting.

You are executing **Phase A-bis — tasks A1c, A2-bis, A4-bis, in that order.** Then stop at CP-A.

**Do not re-run A1, A1b or A3.** They are accepted. Re-running them wastes hours and risks overwriting good artifacts. The one exception is a single CSV repair, folded into A2-bis and described in the plan.

**Do not begin Phase B under any circumstances.** CP-A is unsigned; production code is not authorised.

**What went wrong last time, stated plainly, because avoiding it is the whole job.**

The previous round reported that A2's model (ii) had a working `Zone Multiplier = 4` and a total conditioned floor area of 6000 m². Both statements are false. The run's own `eplusout.eio` records `Zone Multiplier = 1` on every zone, and its `eplustbl.csv` reports 2999.99 m². The generated IDF contained no added multiplier at all. The task instruction had warned, in writing, that *"a multiplier that is silently ignored looks exactly like a clean pass"* — and that is precisely what happened, except the report also supplied corroborating detail for a mechanism that was never in the file.

Separately, A4 was reported complete while delivering only the `auto`-mode half of a side-by-side comparison, with no `layout_assign` export, no PNG stills, and no hand spot-checks.

**So the standard for this round is narrow and absolute: every number you report must be readable in an artifact you can cite by path, and you must paste the line you read it from.** Not a summary of it. The line.

**Hard rules — all of §1 of the plan applies. These are the ones that matter here:**

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never `cd` out of it for a write.
2. **No production code.** After each task run `git status --short openubem/ tests/ main.py` and paste the output into that task's progress entry. Measurement harnesses go in `scripts/analysis/` and are throwaway.
3. **Do not write plans, and do not propose alternatives.** Execute this one. If the plan conflicts with the code or with DESIGN, **STOP and quote the conflict verbatim.**
4. Never edit root `main.py`, never edit OVERVIEW or DESIGN docs, never put a `.py` file under `docs/`. **Never run `git commit`.**
5. **Do not touch the E-LA-20 fix** — `openubem/idf/opaque_assembly.py`, `T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`. Out of scope.
6. **The prototype library is read-only.** Never modify the 25 baseline IDFs on disk; edit the loaded `idf` object in memory, as the current code already does.
7. **When an EnergyPlus run fails, report the `** Severe **` line verbatim** from `eplusout.err`. Never the `.end` file, never a wrapper's verdict.
8. **Row count must equal artifact count, and both must be stated** in every progress entry that reports runs.
9. **A parser that finds nothing must report "parser found nothing", never "0".** Last round's `a3_shorter_deletion_summary.csv` recorded `severe_count = 0` for a run that EnergyPlus itself terminated with 31 Severe errors. Zero and *not-found* are different facts and must never be collapsed.
10. **Every artifact goes under `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/`** — `results/` for CSVs, `figures/` for stills and viewer HTML. Figures additionally keep their canonical flat copy in `openubem/outputs/`; that is a copy, not a second home.
11. After each completed task: append one progress-log entry under **§7**, then tick that task's row in **§0**. **Never tick a checkpoint row (🔶) — manager only.**

**A2-bis carries two mandatory proofs. A progress entry without both is not acceptable.**

- **Before the run** — grep the generated `in.idf` for the zone objects you edited and paste the multiplier field as it appears in the file.
- **After the run** — paste the `Zone Information` line from `eplusout.eio` for one multiplied zone, showing the multiplier field holds your value and not `1`.

And the acceptance test is unchanged and binding: total conditioned floor area in `eplustbl.csv` must equal `n_real × plate`. **If it does not, the result is void and you report it as void.** A void result is a perfectly acceptable outcome of this task — it tells the manager that `Zone Multiplier` is not a usable mechanism here, which is real information. A result narrated as passing when the artifact says otherwise is the one outcome that is not acceptable.

**A2-bis also has an ambiguity you must resolve out loud, not silently.** See **E-LA-26** in §8: `MidriseApartment` and `HighriseApartment` model 3 geometric bands with `Multiplier = 1`, while their registry areas imply 4 and 10 storeys. So `n_proto` has two defensible readings that differ by up to 3.3×. State which one you used and why, in the progress entry. Do not pick one quietly.

**A4-bis is the time-ordered task and it has no second chance.** Once Phase B lands there is no way to produce an honest `layout_assign` "before" panel ever again, and C04 becomes unprovable. Reuse A4's existing `auto` exports **unchanged** — do not regenerate them — and add the missing `layout_assign` side, the stills, and the hand spot-checks. The compatibility question A4 raised is already settled (the viewer ingests `layout_assign` IDFs, 2/2 loaded); do not re-litigate it. The viewer stays read-only: never modify geometry to make something render.

**When you finish A4-bis, stop and report:**

1. The three progress-log entries.
2. A1c's distribution, with the real-measured control beside it, and both totals stated.
3. A2-bis's two multiplier proofs, and the acceptance test result — pass **or void**, whichever it is.
4. A4-bis's spot-check table for the 3 named buildings, both scenes.
5. Your recommendation on D3(a): is `Zone Multiplier` usable, and for which archetypes.

Then wait for the manager's signature. Do not proceed to Phase B.
