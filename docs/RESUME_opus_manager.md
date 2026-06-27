# RESUME — Opus Manager Session (Phase-D COMPLETE → consolidation / next-phase intake)

> Hand-off for a fresh Opus **manager** session. Read this top-to-bottom, then read
> the linked specs (CLAUDE.md + the Phase-D REPORT + checklist) before acting.
>
> **Last updated:** 2026-06-26.
> **State in one line:** the Phase-D real-HVAC arc is **COMPLETE and ADOPTED** — nothing
> is running, no resim is indicated, every box in `PROJECT_CHECKLIST.md` is `[x]`. A fresh
> manager session is in **intake mode**: there is no forced next task. Pick up only a
> user-directed new request or one of the explicitly user-gated optional threads in §5.

---

## 0. Who you are

You are the **manager / architect** session. You read specs, write/audit plan docs, make
DESIGN-deviation + validation calls, and keep `PROJECT_CHECKLIST.md` current. **You never
write feature code** — fresh Sonnet sessions ("employees") execute your plans top-to-bottom.
If Sonnet hands back a plan, push it back: manager plans, Sonnet executes. Manager-authored
scratchpad analysis/ops scripts are within role; `openubem/` product code is not.
(Full role table in `CLAUDE.md`.)

Read first, in order:
1. `CLAUDE.md` — governance, model-cost discipline, hard rules.
2. `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/REPORT_phaseD_final.md` — the FINAL adopted-baseline report.
3. `docs/PROJECT_CHECKLIST.md` — the user's single monitoring surface (all boxes `[x]`).
4. This file.

Memory to recall: `project_phaseD_real_hvac` (adopted model), `project_v19_basis_diagnostic`,
`project_v18_diagnosis`, `project_master_checklist`.

---

## 1. The adopted baseline (what "the model" now IS)

**Adopted model = `phaseD2` metered PTAC HVAC + V16 service-loads reconstruction on
REGIONAL CBECS fractions. Zero fitted parameters.**

Three things stacked, each user-ratified:
1. **Phase-D real HVAC** — replaced `IdealLoadsAirSystem` (thermal load + post-hoc COP) with
   `HVACTemplate:Zone:PTAC` + per-archetype prototype COP; parser rewired from thermal →
   **metered** HVAC electricity/gas. Killed the basis error at the source (LA flipped hot→cold).
2. **phaseD2 setback fix (CP-8)** — an OQ-2 schedule-digitization bug held 11 daytime-commercial
   archetypes' weekday heating setpoint flat at 21.1 °C to midnight (no evening setback).
   Fixed to mirror each archetype's own weekend setback → resimmed all 12 cells to `phaseD2`.
   NYC office heating −9.86%; old Limitation #1 (NYC office over-heat) RESOLVED.
3. **Regional CBECS service-load fractions (CP-2, Direction A)** — replaced the climate-blind
   national V16 fraction table with per-census-division fractions via the **DD3b ratio-tilt**
   (`mf_adj = mf_t4 × mf_cb_reg / mf_cb_nat`, anchored on the validated national level, no
   anchor-fitting). Flipped national CBECS NMBE FAIL→PASS in all 3 regions.

**Headline numbers (from `REPORT_phaseD_final.md`):**
- City-Overall within **±9% all 3 cities**: NYC **+2.1%** / LA **−3.7%** / Austin **−8.6%**.
- National CBECS-2018 **NMBE + R² passing all 3 regions** (first time): NYC +7.7 / LA −6.1 / Austin −9.9.
- 8,160/8,160 buildings simulated clean across the 12 cells; 0 exclusions; 0 PTAC fatals.

**Authorized DESIGN deviation:** PTAC activates the `DESIGN_step-3:420` Phase-2 hook
(user-ratified 2026-06-21, PLAN §0.1). DESIGN/OVERVIEW docs were NOT edited. Only the 3
authorized modules changed: `idf/hvac.py`, `idf/outputs.py`, `results/parser.py` (+ the
region-aware `results/service_loads.py` for CP-2).

---

## 2. What is DONE (do not redo)

The entire arc is closed and consolidated. Concretely:

- **Phase-D resim + scoring** — CP-1…CP-6 all passed; `RESULT_phaseD_validation.md`,
  `RESULT_phaseD_reconstructed_validation.md`.
- **phaseD2 setback fix** — Phase-6 T15–T18, CP-7/CP-8; `RESULT_phaseD2_setback_rescore.md`.
- **Regional fractions** — CP-1/CP-2; `PLAN_regional_service_load_fractions.md`,
  `RESULT_regional_fraction_derivation.md`, `RESULT_phaseD2_regional_fractions.md`,
  `openubem/data/service_loads/enduse_fractions_regional.json`.
- **FINAL report regenerated** — `REPORT_phaseD_final.md` consolidates CP-8 + CP-2.
- **Project-level consolidation** — `REPORT_R5_final.md` + `V13_cross_case_synthesis.md`
  carry supersession banners → point to `REPORT_phaseD_final.md`.
- **Restaurant/MF overshoot** — RESOLVED under adopted model (NYC MF +8.8 / LA MF −9.2;
  FSR/QSR flipped from +110/+160% to −27/−22%). No new fix indicated.
- **Geometry robustness** — MULTI-class hardening verified in code + production
  (8,160/8,160 clean); **generation-time-drop rescue COMPLETE** (HEAD drop count 0;
  complexity gate T=800; `tests/test_generation_drop_rescue.py`, 132 tests green).
- **Figures** — all 65 published PNGs in `openubem/outputs/` refreshed to the adopted
  phaseD2+regional model (plotting suite env-gated, backward-compatible, 20 tests pass);
  only 3 frozen R5/R6 historical diagnostics retain old dates by design.
- **Secondary HVAC levers** (gas-eff 0.945, cooling-COP/0.75-derate) — EVALUATED + CLOSED
  2026-06-26: NOT indicated (gas-eff fix worsens already-slightly-over NYC; cooling-derate is
  resim-gated and unwarranted — model passes all gates within tolerance, zero fitted params).

**Nothing is running on the cluster** for this project. GSSCanada job `987039` and any
user jobs in `squeue` are **not ours — do not touch them.**

---

## 3. Known, accepted limitations (documented — NOT open work)

These are disclosed in `REPORT_phaseD_final.md` §3/§7 and are **closed by decision**, not
pending. Do not "fix" them without an explicit user request:

- **LA Office +12.3% / LA Warehouse +31.2% (n=38)** — the disclosed cost of regional
  fractions; LA-Overall still −3.7%. Accepted (the regional table improved NYC, Austin, and
  LA-Overall; the two sub-segments are the trade).
- **NYC Office +18.0%** — residual from climate-blind national-level fraction anchoring;
  a fraction-table limit, not a COP/gas-eff error. Accepted.
- **CV(RMSE) / KS shape gates fail** for both scalar and physical models → **structural** for
  an archetype-deterministic UBEM (every building of an archetype gets identical loads, so the
  modeled distribution is narrower than metered). Report-only; never tuned to pass.
- **Commercial-only regional fractions** — multifamily & data centers keep national fractions
  (CBECS is commercial-only). Accepted.

---

## 4. First actions for a fresh session

There is **no forced task**. In order:

1. **Confirm steady state** — skim `PROJECT_CHECKLIST.md` (all `[x]`) and the CURRENT BASELINE
   line at its top. Confirm nothing of ours is in `squeue` if a cluster question arises
   (`ssh o_iseri@speed.encs.concordia.ca "squeue -u o_iseri -h"` is a lightweight login-node op).
2. **Take the user's new request** — if the user opens a new thread, that is the work. Scope it,
   write a plan doc under `docs/docs_ACTIVE/...`, hand to Sonnet, audit. Keep the checklist current.
3. **Only if the user re-opens an optional thread** — see §5. None of these auto-run; all are
   user go/no-go (especially anything needing cluster compute).

If a new request would change the model, remember the **process note**: refreshing
`openubem/outputs/` figures is a required step after any model change (env-gate the plotting
suite via `OPENUBEM_PHASED_SUBDIR`).

---

## 5. Optional / user-gated future threads (none started)

These are real candidates but **deliberately not in flight** — each needs a user go decision:

- **LA cooling-dominated deep-research (C3).** V19 confirmed LA's residual is a real
  climate/HVAC-response question (Title 24 vs our ASHRAE 90.1 archetypes: envelope U-values,
  infiltration, economizers for CZ 3B), NOT zoning. Under the adopted model LA-Overall is only
  −3.7%, so this is a refinement, not a defect. Gated on user go for a calibration phase.
- **Secondary HVAC levers** — already evaluated + closed as not-indicated (§2). Re-open only if
  a future anchor demands it (would be resim-gated).
- **Multi-city / distribution expansion** — the long-standing OVERVIEW gap list (L2/L3/L4,
  more cities, distribution mode). Net-new scope; needs a fresh DESIGN-aligned plan + user go.

---

## 6. Standing governance constraints (do not violate)

- **Manager writes/audits plans + makes DESIGN calls; NEVER writes feature code.** Sonnet executes.
- **Never edit:** OVERVIEW/DESIGN docs · root `main.py` · gate/core-math modules · committed
  `05_results.*` of validation cells · adopted `phaseD2/` + `phaseD/` + `phaseC/` outputs.
- **Authorized Phase-D edits were ONLY** `idf/hvac.py`, `idf/outputs.py`, `results/parser.py`,
  region-aware `results/service_loads.py` — all landed. No further core edits without a ruling.
- **Gates are report-only — never tune to pass.**
- No `.py` under `docs/`. All figures → `openubem/outputs/` flat (never under `docs/.../figures/`).
- **Never git commit/add** — the user's external tool auto-commits.
- **Cluster:** ABSOLUTE rule — never run blocking `srun`/python/compute on the Speed login node;
  `sbatch` fire-and-forget, then read the output file. Login node only: mkdir/scp/tar/squeue/sacct.
  ONE sbatch array in queue at a time; verify `squeue -u o_iseri` empty before submitting.
  **Do NOT touch GSSCanada job `987039` or any non-OpenUBEM user job.**
- **Model-cost discipline:** Sonnet/Haiku for execution + monitoring; reserve Opus for manager
  reasoning. Min 30-min monitoring interval; prefer event-driven completion. Never babysit a job on Opus.
- EUI normalization stays `energy ÷ (footprint × num_floors)`; `single_zone` survives only for
  `num_floors == 1`.
- Stop-and-ask on spec ambiguity; never invent.

---

## 7. Pointers

- **FINAL report (read this):** `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/REPORT_phaseD_final.md`
- Phase-D plan + progress log: `…/phaseD_realHVAC/PLAN_phaseD_real_hvac_resim.md`
- Regional-fractions plan: `…/phaseD_realHVAC/PLAN_regional_service_load_fractions.md`
- Adopted data: `openubem/data/loads/hvac_cop_by_archetype.json`,
  `openubem/data/service_loads/enduse_fractions_regional.json`,
  `openubem/data/schedules/doe_schedules.json` (phaseD2 setback)
- Region-aware reconstruction: `openubem/results/service_loads.py`
- Cluster harness: `scripts/validation/v12_cell_pipeline.py` (env-gate `OPENUBEM_PHASED_SUBDIR`,
  default `phaseD`); rescore drivers `scripts/validation/phaseD_*_rescore.py`
- Figures + env-gated plotting: `openubem/outputs/`, `openubem/results/plotting_suite.py`,
  `openubem/results/visualization.py`
- Checklist (user's monitoring surface): `docs/PROJECT_CHECKLIST.md`
- Memory index: `…/memory/MEMORY.md` (`project_phaseD_real_hvac`, `project_v19_basis_diagnostic`,
  `project_v18_diagnosis`, `project_master_checklist`)
- Superseded-but-banner'd history: `docs/docs_VALIDATION/overAll/REPORT_R5_final.md`,
  `V13_cross_case_synthesis.md`, V14–V19 docs
