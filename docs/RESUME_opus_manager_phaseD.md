# RESUME — Opus Manager Session (Phase D: real-HVAC resim)

> Hand-off for a fresh Opus **manager** session. Read this top-to-bottom, then read
> the linked specs (CLAUDE.md + the Phase-D PLAN) before acting.
> **Last updated:** 2026-06-24 (fresh session resumed; la_urban pilot STILL waiting — the user's queue
> now holds a *new* job `987039 step6_2split` (partition `pg`), so the empty-queue gate still blocks us.
> User re-chose "cheap watcher, auto-run"; a background Sonnet watcher (`a863907128f14a5ee`) is re-armed:
> polls `squeue` ≥30 min, auto-runs the pilot when the queue clears, stops at CP-3. **The watcher dies if
> this session closes** — re-establish it on next resume (re-check `squeue`, re-launch the watcher).

---

## 0. Who you are

You are the **manager / architect** session. You read specs, write/audit plan docs,
and make DESIGN-deviation calls. **You never write feature code** — fresh Sonnet
sessions ("employees") execute your plans top-to-bottom. If Sonnet hands back a plan,
push it back: manager plans, Sonnet executes. (Full role table in `CLAUDE.md`.)

Read first, in order:
1. `CLAUDE.md` — governance, model-cost discipline, hard rules.
2. `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/PLAN_phaseD_real_hvac_resim.md` — the active plan (12 tasks, 5 checkpoints).
3. `docs/PROJECT_CHECKLIST.md` — the user's single monitoring surface. Keep it ticked + current.
4. This file.

Memory to recall: `project_phaseD_real_hvac`, `project_v19_basis_diagnostic`, `project_v18_diagnosis`.

---

## 1. What "Phase D" is and WHY

Phase D = a **physical-HVAC re-simulation** of all 12 validation cells. It replaces the
Phase-1 `IdealLoadsAirSystem` with `HVACTemplate:Zone:PTAC` parameterized by a
per-archetype prototype **COP**, and rewires the parser from **thermal** loads to
**metered** HVAC electricity/gas.

**Why (the root cause it kills):** IdealLoads reports *thermal* cooling/heating loads, but
we compare against *measured metered* EUI with no COP conversion. LA (cooling-dominated)
therefore reads ~3.5× too hot. The V19 basis diagnostic ([[project_v19_basis_diagnostic]])
proved a scalar post-hoc COP can pass mean-level NMBE but **never** clears the
distribution-shape gates (CV(RMSE)/KS) and **can't** reconcile city-optimal COP (~3.5)
with national-optimal COP (~2.5). So we fix it at the source with real HVAC. **Resim GO is
evidence-backed, not a preference.**

**This is an AUTHORIZED DESIGN deviation** (PLAN §0.1): deviates from DESIGN_step-3 §3H
(IdealLoads mandate, lines 392–394), activates the line-420 PTAC Phase-2 hook, and
DESIGN_main line 45. User-ratified 2026-06-21. **DESIGN docs are NOT edited.**

Scope note: the V18 re-zoning fix is **already baked into the Phase-C baseline** (IDFs
regenerated 2026-06-19), so Phase D is **HVAC-only** — no re-zoning task.
Output isolation: Phase D → `--output-subdir phaseD` (Phase-C `phaseC/` stays untouched).

---

## 2. Where we are RIGHT NOW (state at hand-off)

**All code work is DONE and audited. Only the cluster runs remain.**

- **CP-1 PASSED** — COP extraction. `openubem/data/loads/hvac_cop_by_archetype.json`,
  30/30 archetypes, manager-verified by reading the file directly. 16 DX archetypes use
  gross-rated DX COP; 10 central-plant archetypes (LargeOffice/Hospital/LargeHotel/College/
  HighriseApartment/LargeDataCenter/Tall/SuperTall + others) have no DX coil → ruling:
  cooling_cop = primary chiller/WSHP COP × **0.75** plant-auxiliary factor (PLAN §3.1).
- **CP-2 PASSED + audited** — core code changed (the 3 authorized modules):
  - `openubem/idf/hvac.py` → emits `HVACTEMPLATE:ZONE:PTAC` per zone (field
    `Cooling_Coil_Gross_Rated_Cooling_COP`), reads COP from the JSON.
  - `openubem/idf/outputs.py` → adds meters Cooling:Electricity, Heating:Electricity,
    Heating:NaturalGas, Fans:Electricity.
  - `openubem/results/parser.py` → `_EUI_VARS` now metered (cooling←Cooling:Electricity,
    heating←Heating:Electricity+NaturalGas) + new separate `fans_eui_kwh_m2`.
  - Local smoke (SmallOffice NYC) sane; 785 tests pass (4 pre-existing unrelated fails).
- **T07a local taste-test PASSED** — standalone `ExpandObjects` (cluster path, no `-x`)
  expands PTAC → real DX coils + curves, no IdealLoads. 5 la_urban buildings, 0-fatal,
  metered EUI sane. **LA MediumOffice cooling 20.7 metered vs old thermal ~90 → basis fix
  visibly working.** Cluster-expansion risk CLEARED.

### THE OPEN THREAD (start here) — T07 la_urban pilot is WAITING, not done

The pilot was **never submitted** because the **user's own unrelated cluster job**
(`blockB_v23`, job 981716) occupied the queue, and our rule is **one sbatch array at a
time**. As of pause (2026-06-22) that job was draining (~40 → ~14 tasks). Per the user
"wait for my queue to clear, then auto-run," a cheap **Sonnet employee** owned a poll loop.

**On resume the background watcher is GONE** (it died when the prior session closed). So:
**do not assume the pilot ran.** First thing: check the cluster state yourself
(`ssh o_iseri@speed.encs.concordia.ca "squeue -u o_iseri -h"` — this is a lightweight
login-node op, allowed) and check whether `phaseD/la_urban/` deliverables exist. Then
re-dispatch the pilot (below). Nothing is lost if it didn't run.

---

## 3. First actions for the fresh session

**A. Re-establish cluster state.** Confirm `squeue -u o_iseri` is empty (the user's
`blockB_v23` should be long finished by the next day). Confirm no stray `phaseD/la_urban/`
partial outputs.

**B. Run the T07 la_urban pilot.** Delegate the run + monitoring to a **cheap (Sonnet/Haiku)
employee** per model-cost discipline:
```
py -3 scripts/validation/v12_cell_pipeline.py la_urban --output-subdir phaseD
```
This regenerates PTAC IDFs → ships → ONE sbatch array → polls → aggregates to
`phaseD/la_urban/05_results.gpkg`. The employee stops at **CP-3** and reports.

**C. Audit CP-3 (you, Opus).** Greenlight T08 only if:
1. la_urban success count is healthy (compare to Phase-C's 616/616) with **zero new PTAC
   EnergyPlus fatals** and **zero buildings excluded** (user's binding "fix don't skip").
2. Metered cooling EUI **dropped vs Phase-C thermal** (the whole point — esp. LA offices).
3. Zoning unchanged from Phase-C (§0.2 — Phase D is HVAC-only; lighting/equipment EUI must
   match Phase-C, only HVAC end-uses move).
4. fans_eui_kwh_m2 is populated and plausible.

**D. After CP-3 clean → T08 fan out the remaining 11 cells** (austin/la/nyc ×
centre/rural/suburban/urban, minus la_urban), **one sbatch array at a time**, same harness,
`--output-subdir phaseD`. Then **T09** aggregate → **CP-4**.

**E. T10–T12 re-validate** Phase-D results vs BOTH city anchors (NYC/LA/Austin LL84/EBEWE)
AND national CBECS regional gates, **with NO post-hoc transform** (the model is now
self-consistent). **CP-5 = manager verdict:** did real HVAC clear city + national + shape
gates with one consistent physical model? This is the question the whole phase exists to answer.

---

## 4. CP-4 carry-forward flags (decide from the resim data, not now)

- **(a) fans in/out of total_eui:** currently `fans_eui_kwh_m2` is OUT of
  `total_eui_kwh_m2`, but CBECS includes fan electricity → likely fold INTO total for the
  national comparison. Decide from data.
- **(b) central-plant gas heating efficiency 0.945** reads high vs typical ~0.80 —
  sanity-check against measured heating before trusting central-plant heating EUI.
- **(c) smoke fan EUI 1.15 kWh/m²** looked low — verify at scale.

---

## 5. How to run a cell (the harness)

```
py -3 scripts/validation/v12_cell_pipeline.py <cell_name> --output-subdir phaseD
```
- `run_cell` clears the stale manifest first → forces fresh PTAC IDF regen.
- Cluster: `o_iseri@speed.encs.concordia.ca`, partition `ps`, E+ 23.1.0, BatchMode SSH.
  **ExpandObjects runs SEPARATELY on the cluster (no `-x`, symlink crash)** — this is why
  PTAC expands fine; do not "fix" it back to `-x`.
- All compute via `sbatch --array`; login node only does mkdir/scp/tar/squeue/sacct.
- **ABSOLUTE rule:** never run blocking `srun`/python/compute on the Speed login node.
  `sbatch` fire-and-forget, then read the output file. ONE array in queue at a time —
  verify `squeue -u o_iseri` is empty before submitting.
- Delegate the run + wait to a **cheap employee**; do NOT keep Opus spinning. Event-driven
  completion preferred; if polling, **≥30-min** interval.

---

## 6. Standing governance constraints (do not violate)

- **Manager writes/audits plans + makes DESIGN calls; NEVER writes feature code.** Sonnet executes.
- **Authorized edits for Phase D are ONLY** `idf/hvac.py`, `idf/outputs.py`,
  `results/parser.py` (PLAN §0.1) — all already landed. No further core edits without a ruling.
- **Never edit:** OVERVIEW/DESIGN docs · root `main.py` · gate/core-math modules ·
  schedule JSON/builders · `visualization.py` · `enduse_fractions_table4.json` ·
  LPD/EPD scalars · committed `05_results.*` of validation cells · Phase-C `phaseC/` outputs.
- **Gates are report-only — never tune to pass.**
- No `.py` under `docs/`. Figures → `openubem/outputs/` flat.
- **Never git commit/add** — user's external tool auto-commits.
- **Model cost discipline:** Sonnet/Haiku for execution + monitoring; reserve Opus for
  manager reasoning. Min 30-min monitoring interval; prefer event-driven completion.
- EUI normalization stays `energy ÷ (footprint × num_floors)` (DESIGN §300).
- `single_zone` strategy survives only for `num_floors == 1`.
- Stop-and-ask on spec ambiguity; never invent.

---

## 7. Pointers
- Active plan + progress log: `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/PLAN_phaseD_real_hvac_resim.md`
- COP table: `openubem/data/loads/hvac_cop_by_archetype.json`
- Cluster harness: `scripts/validation/v12_cell_pipeline.py`, `scripts/cluster/submit_fleet.sbatch`
- Checklist (user's monitoring surface): `docs/PROJECT_CHECKLIST.md`
- Memory index: `…/memory/MEMORY.md` (see `project_phaseD_real_hvac`,
  `project_v19_basis_diagnostic`, `project_v18_diagnosis`).
- Validation history: `docs/validations/overAll/REPORT_R5_final.md`, V13–V19 docs.
