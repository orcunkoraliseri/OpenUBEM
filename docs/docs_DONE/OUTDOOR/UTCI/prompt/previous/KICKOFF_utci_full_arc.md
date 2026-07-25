# UTCI arc — executor kickoff prompt

**Purpose.** Hand the **entire** UTCI / Stage-6 arc to a fresh executor session and have it run
**T01 through T26 to completion** — every task in the plan, through all five checkpoints — stopping
only on one of the named hard-stop conditions.

*(Revised 2026-07-23 alongside plan v1.1. The earlier version stopped at T23 and left Phase 5 and
the EnergyPlus wall coupling for a human decision. Re-examination showed those exclusions were
manager conservatism and one false premise, not real constraints — see plan §13. Scope widened;
every hard gate kept exactly as it was.)*

**How to use.** Open a **fresh Sonnet session** in `C:\Users\o_iseri\Desktop\OpenUBEM` and paste the
block in §A verbatim. Nothing else. Do not paste the plan itself — the prompt tells the executor to
read it.

**Model.** Sonnet. This is execution work, not manager reasoning. Do not spend Opus/Fable tokens on
it, and do not keep a manager session spinning to watch it.

**Scope.** All 26 tasks, Phases 0–5, and **no open decisions.** The last product question — whether
UTCI joins EUI and carbon as a headline output — was **decided by the user on 2026-07-23: Option A,
UTCI stays a separate analysis product.** It is binding, and plan §6a turns it into hard constraints
the executor must respect. Nothing is left for arbitration mid-run.

**Realistically this spans two to three sessions.** T26 (the cluster sweep) also spans wall-clock
hours by nature. A resume prompt is in §C.

---

## A. The prompt — paste this verbatim

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\UTCI\implementation\PLAN_utci_microclimate_implementation.md
in full before writing any code. Then read its §4 a second time.

You are the EXECUTOR for the OpenUBEM UTCI / Stage-6 arc. You execute the plan; you do not write or
revise it. If you think the plan is wrong, STOP, quote the conflicting lines, and report — do not
"improve" it and proceed.

YOUR ASSIGNMENT
Execute T01 through T26 in order — the whole plan, all five phases — running to completion through
checkpoints CP-1 to CP-5. You self-sign each checkpoint when its gate passes, log the signature, and
continue. You are expected to finish the arc.

This is a wide scope deliberately paired with strict gates. The gates are what make it safe; do not
trade one for the other. If a gate fails, that is a finding to report, never an obstacle to route
around.

THE PRODUCT DECISION YOU ARE EXECUTING UNDER (plan §6a — read it, it is short and binding)
The user decided on 2026-07-23 that UTCI is a SEPARATE ANALYSIS PRODUCT, not a headline OpenUBEM
output alongside EUI and carbon. Reason: EUI is validated against measured data (LL84, EBEWE,
CBECS); UTCI will not be validated against anything measured in this arc. Putting an unvalidated
number in a validated table lends it authority it has not earned.

That decision forbids five specific things. Do not do any of them, in any task:
1. Do NOT add any UTCI / comfort / Tmrt column to 05_results.gpkg/.csv/.geojson or its schema.
2. Do NOT write outdoor metrics into 05_neighbourhood_summary.json.
3. Do NOT make Stage 6 run as part of a standard pipeline run, and do NOT call run_step6 from any
   Stage 1-5 code path. Stage 6 is invoked explicitly by its own runner; it reads Stage 5 and never
   writes back.
4. Do NOT make the 3D viewer colour buildings by UTCI. T25's ground plane is an optional layer,
   DEFAULT OFF. Energy stays the building colouring.
5. Do NOT describe UTCI as "validated" anywhere, and do NOT place its numbers beside the ±9% /
   LL84 / EBEWE / CBECS claims without an explicit caveat.

Instead: all outdoor results live in the 06_mc_* family; T20 opens 05_results.gpkg READ-ONLY and
writes 06_mc_summary.gpkg; and T23 must state the separation plainly in both documents it touches.

Note this is the same boundary as T13's production-untouched gate (openubem/results/ unmodified).
If you are about to cross one, you are crossing both. Stop.

BEFORE ANYTHING ELSE — the four corrections that will silently ruin this work
The deep-research corpus at docs/docs_DONE/OUTDOOR/UTCI/DeepResearches/ (U01-U06) is a research INPUT,
NOT a specification. A manager audit found seven load-bearing defects in it. Every one fails
silently: wrong numbers, no crash, a map that still looks plausible. §4 of the plan overrides the
research on every point. The four you are most likely to trip over:

1. The UTCI polynomial code printed in U05 §3 and U06 §3 is FABRICATED — seven hand-written terms
   standing in for the real 210-coefficient Bröde polynomial. Do not copy it, do not adapt it, do
   not use it as a starting point. Transcribe the official COST-730 source (see T05).
2. The polynomial's wind argument is at 10 m, NOT 1.1 m. Follow the conversion convention in §4.2
   exactly.
3. The 6-directional radiative weights are 0.22 (x4 vertical) and 0.06 (x2 horizontal) — they must
   sum to exactly 1.00. U03 prints 0.08, which sums to 1.04. Use 0.06.
4. Vapour pressure: your API works in kPa, the official polynomial takes hPa. Convert in exactly one
   place, and pin it with a test.

If you find yourself transcribing ANY formula, coefficient, unit, or constant out of U01-U06,
stop and verify it at its primary source first. That is the lesson this arc was built around.

ENVIRONMENT — already measured for you, do not re-derive (plan §3.1, facts F-15 to F-19)
- Python 3.14.3. rasterio, geopandas, shapely, scipy, pyproj, matplotlib, numpy, pandas, contextily
  all import cleanly. EnergyPlus 23.1 is at C:\EnergyPlusV23-1-0. numba has no 3.14 wheel — which is
  why the plan rejects it; do not try to add it.
- The 12 validated cells are local, at docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/.
- Three traps in those run-dirs that will bite you if you assume the documented layout:
  * the buildings file is 01_buildings.gpkg, NOT 01_buildings_clean.gpkg — accept both;
  * there is NO weather/ subdirectory — resolve the EPW from the global cache ~/.openubem/epw/
    via the 3-step ladder in T18;
  * the bare 06_ prefix is already taken by the viz basemap — every Stage-6 artifact is 06_mc_*.
- nyc_centre (the T22 target): 738 buildings, EPSG:32618, height_m present on only 617/738 = 83.6%.
  Expect ~121 buildings excluded from the DSM for missing height. That is the honest gap. Report the
  count; never invent a height to close it.

THE ONE THING MOST LIKELY TO STOP YOU: getting the 210 polynomial coefficients (T05)
The plan's §11 has a three-rung escalation ladder. Read it before you start T05. Short version:
try the official COST-730 UTCI_a002.f90 first; if unreachable, lifting the coefficients out of an
established open-source port (ladybug-comfort, pythermalcomfort) is explicitly ACCEPTABLE — copy the
numbers, not the dependency, and record the provenance and licence. Only if both fail do you stop.
Whichever rung you use, T06's reference-table gate at atol=1e-6 is what proves it correct.

HARD RULES (the plan's §1 is the full list; these are the ones that end the session if broken)
- Stay in C:\Users\o_iseri\Desktop\OpenUBEM. Never edit main.py at the repo root.
- Never edit the OVERVIEW/DESIGN docs under docs/docs_main/, and never edit U01-U06.
- No .py files under docs/. Scratch work goes in scratchpad/.
- Zero fitted parameters. Every numeric constant carries a citation or it does not enter the code.
  If you cannot cite it, STOP and ask — do not pick a plausible number.
- Never tune anything to make a gate pass. A failing gate is a finding to report, not a target.
- All .png / figure outputs go to openubem/outputs/ (flat), and are also copied into
  docs/docs_DONE/OUTDOOR/UTCI/implementation/.
- Default to no comments. One short line maximum, only where the WHY is non-obvious.
- Determinism: seeded RNG, byte-identical rasters on re-run.
- Honest gaps: where a fact is absent in the source data (no OSM height, no tree canopy), emit an
  explicit marker and a provenance flag. Never invent a default to fill a hole.
- CLUSTER RULE, ABSOLUTE: never run a blocking srun, python, or any computation on the Speed login
  node. Always sbatch fire-and-forget, then read the output file. (Not relevant until Phase 5, but
  it applies the moment you touch the cluster.)

PROGRESS LOG — MANDATORY
Append one entry to §9 of the plan doc for EVERY completed task, in exactly this format:

  #### TXX — <title> — completed YYYY-MM-DD
  - Artifacts: <paths>
  - Deviations: <none | rationale + PLAN cite>
  - Test status: <pytest summary>
  - Notes: <auditor-relevant>

An undocumented task is an incomplete task. Do not batch these up at the end — append as you go.
Use §10 (Error Log) for anything that broke and how you fixed it.

CHECKPOINT PROTOCOL
At CP-1 (after T07), CP-2 (after T11), CP-3 (after T16) and CP-4 (after T23): append a checkpoint
entry to §9, report the exact evidence bundle listed in the plan's checkpoint box, then CONTINUE on
your own authority. The manager pre-signs all four, each conditional on its gate passing.
CP-5 (after the T26 harvest) closes the arc — report and stop there.

But each checkpoint has ONE hard gate. If it fails, STOP and report — do not continue, do not
work around it:
  - CP-1: the official UTCI reference table must match at atol = 1e-6. If it does not, or if you
    could not obtain the official COST-730 polynomial source at all, STOP.
  - CP-2: mid-canyon sky view factor at pedestrian height (z=1.1m) must match
    1 / sqrt(1 + (2*(H-1.1)/W)^2) within +/-0.03 for H/W = 0.5, 1.0 and 2.0
    (targets 0.7268 / 0.4677 / 0.2558). CORRECTED TWICE 2026-07-23 by manager adjudication (plan
    doc E-UTCI-01, then E-UTCI-02) — the original sqrt(1+(2H/W)^2)-2H/W was the wrong formula
    entirely (mis-cited from the research corpus), and the first fix (1/sqrt(1+(2H/W)^2)) was a
    floor-level formula that still didn't match the code's pedestrian-height default. If it does
    not match the current target above, STOP.
  - CP-3: raising ground albedo from 0.15 to 0.45 in an UNSHADED cell must RAISE Tmrt by +2.5 to
    +8 °C (the cool-pavement paradox). If your model says cool pavement straightforwardly helps
    pedestrians in open sun, your reflected-shortwave term is wrong. STOP.
  - CP-4: `git status --porcelain` must show NO modification under openubem/idf/,
    openubem/simulation/, openubem/results/, openubem/semantic/, openubem/geometry/, or
    docs/docs_VALIDATION/. This is THE condition that lets you sign CP-4 yourself instead of waiting
    for a human: Stage 6 is additive and must stay that way. If any of those paths changed, STOP —
    the design has drifted. (openubem/viz/ is the single authorised exception, at T25, and only
    behind its byte-identical guard.)
  - CP-5: after the T26 harvest. Report and stop — the arc is complete.

THE TWO THINGS THAT ARE NOT AS HARD AS THEY SOUND
- T13 Tier-2 (the EnergyPlus facade-temperature coupling, this arc's scientific contribution) does
  NOT require re-running any validated cell or editing any production module. You extract COPIES of
  the archived IDFs (every phaseE cell ships <cell>_step3_idfs_archive.zip; nyc_centre has 738),
  patch two things into each copy — one Output:Variable and a narrowed RunPeriod — run them locally
  through the existing openubem/simulation/runner.py::run_energyplus, and harvest. A 7-day window is
  about 1/52 of the annual work these IDFs were already validated with. Build it; do not skip it.
- T26 spans wall-clock hours because sbatch arrays do. That is a scheduling fact, not a gate. Fire
  the arrays, log the job IDs in §9 immediately, end the session cleanly, harvest later.

ALSO STOP IMMEDIATELY, AT ANY POINT, IF:
- The plan is ambiguous or contradicts the DESIGN docs. Quote the conflict; never invent.
- A task turns out to need something the plan does not describe.
- You would have to add a dependency the plan's §6 does not authorise.
- You would have to modify a file outside the list in the plan's §5.
- Backward compatibility breaks: the existing 12-cell validated baseline must stay bit-identical
  with the new flags off. Verify this at T13, do not assume it.

TESTING
Follow the repo's conventions: flat tests/test_<module>.py, pytest, markers `slow` and `energyplus`.
Run the full suite before each checkpoint report, and quote the summary line. New fixtures go under
tests/fixtures/ with a README recording where the reference data came from and when you retrieved it.

REMEMBER WHY T22 EXISTS
Everything before T22 runs on synthetic canyons. 100% synthetic-fixture green is NOT live-path
green — that has bitten this project before. T22 is the live smoke test on real nyc_centre geometry
and real weather, and it is expected to find things the synthetic gates missed. Report what it finds
plainly, including the ugly parts.

REMEMBER WHY T23 EXISTS
T23 is not paperwork. It is what makes the outdoor measurements findable by someone who has never
read this plan — updating docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md from
"planned" to what actually got built, with real measured ranges, and adding §11 to
OpenUBEM_fundamentals.md. Only mark something as implemented if T22 actually ran it. A registry
that is not updated when reality changes is worse than no registry.

IF YOU RUN LOW ON CONTEXT BEFORE T26
T01-T26 is a lot of work for one session. Do not rush or skip tests to fit it. Instead, stop at a
clean task boundary, make sure §9's progress log is fully up to date through the last COMPLETED
task, and report exactly which task number to resume from. The progress log is what makes this arc
resumable — a session that ends with an accurate log has lost nothing.

Do not propose alternatives. Execute the plan.
```

## C. Resume prompt (for the next session — expect to need this)

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\UTCI\implementation\PLAN_utci_microclimate_implementation.md
in full, including §4 and its §9 progress log. The log tells you what is already done.

You are the EXECUTOR continuing the OpenUBEM UTCI / Stage-6 arc. Resume at the first task with no
progress-log entry and continue under the same rules as the original kickoff
(docs/docs_DONE/OUTDOOR/UTCI/prompt/KICKOFF_utci_full_arc.md §A — read it, it still applies in full).

Before writing any new code: run the full pytest suite and confirm the previous session left the
repo green. If it did not, fix that first and log it in §10 (Error Log).
```

---

## B. Narrower first run (use this if the executor is unproven)

`CLAUDE.md` recommends a narrow range for the first run of an unfamiliar executor. If you would
rather see one clean cycle before handing over the whole arc, send the §A prompt with the
**ASSIGNMENT** paragraph replaced by:

```
YOUR ASSIGNMENT
Execute T01 through T07 in order. Stop at CP-1 and report — do not continue past it under any
circumstances, even if the gate passes. Append a progress-log entry per completed task to §9 of the
plan doc, plus a CP-1 checkpoint entry, and run the full pytest suite before reporting.
```

Once CP-1 comes back clean, re-send the full §A prompt (it will resume from T08 via the progress log).

**Why T01–T07 is the right narrow slice:** it is exactly the UTCI kernel. It ends on the arc's one
truly binary gate — the polynomial either reproduces the official reference table to 1e-6 or it does
not — so it tells you whether the executor can follow a precision-critical instruction before you
trust it with the spatial engine, where errors are subtler and much harder to see.

---

## C. What the manager checks when the executor reports back

In this order (from `CLAUDE.md`):

1. **Progress-log entries** — one per completed task, format-conformant, deviations cited.
2. **Test output** — pytest summary attached; every failure explained.
3. **File tree** — only files the plan authorised (§5) were touched. Pay attention to
   `openubem/idf/outputs.py` and `pyproject.toml` in particular.
4. **Citations** — for any decision not literally spelled out in the plan, a DESIGN or literature
   line is cited.
5. **The §4 corrections** — verify each one was actually applied, not just acknowledged. The
   cheapest checks: does the weights-sum-to-1.0 test exist? Does the polynomial have 210
   coefficients? Is there exactly one kPa→hPa conversion?

If any of these is missing, ask for it before greenlighting the next range.
