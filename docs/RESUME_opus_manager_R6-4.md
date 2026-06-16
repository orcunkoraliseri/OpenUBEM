# Morning Handoff — New Opus Manager Session (R6-4)

**Written:** 2026-06-15 overnight, by the prior Opus manager session, for the user (manager-of-manager) to paste into a fresh Opus session in the morning.
**Working dir:** `C:\Users\o_iseri\Desktop\OpenUBEM` — stay here.

---

## 0. Paste-this-to-start

> You are the Phase-C manager for OpenUBEM (you WRITE plan docs and AUDIT fresh-Sonnet executors; you do NOT write feature code — but analysis/report markdown and glue scripts under `scripts/validation/` are in your scope). Read `CLAUDE.md`, then `docs/RESUME_opus_manager_R6-4.md` (this file), then the §8 progress log of `docs/validations/overAll/PLAN_overall-validation-R6-4.md` and the overnight close-out memory `…/memory/project_r6_4.md`. Resume from "Current state" below. The first thing you owe me is the DESIGN-deviation decision in §3 — do not start any zoning/HVAC pipeline work until I approve it.

---

## 1. Where we are (the big picture)

- **R5 = COMPLETE** (12 cells, 8 152 buildings, 100% E+). **R6 Batch 1 = COMPLETE** (region-correct CBECS, archetype-aware plausibility, eGRID subregion GWP — all reporting-layer, no resim; V14 shipped). See `memory/project_r5_overnight.md`, `memory/project_r6_batch1.md`.
- **R6 is a work ROUND, not a pipeline step.** There is no Step 6.
- Overnight I ran **R6-4A** — the DESIGN-compliant half of the "HVAC/zoning deep calibration" item. Plan: `docs/validations/overAll/PLAN_overall-validation-R6-4.md`.

## 2. The governance finding that reshaped R6-4 (READ THIS)

The user verbally scoped R6-4 as "HVAC/zoning deep calibration." Research against the binding DESIGN proved the **literal** version is a **spec deviation**, so I did NOT let Sonnet touch the pipeline overnight:

- **Detailed HVAC is out of Phase-1 scope** — DESIGN §2.2 line 45: "no chiller plant, district loop, or VAV"; IdealLoads mandated (Step-3 DESIGN §3H).
- **Zoning is already multi-zone** and the table is binding; full 9-zone Appendix-G is **explicitly rejected**, deferred to OQ-1 / Phase-1.5 (Step-3 DESIGN §3B lines 104–111, 138).
- **DQ-1** (the real open question, `OPEN_QUESTIONS_R5.md` lines 72–73) scopes deep calibration as CBECS reference matching + vintage schedules + **a COP/fuel-basis layer at the *reporting* level, "gates code still untouched"** — it does **not** mention zoning.

So overnight = the **decomposition + reporting-level basis overlay** (DQ-1-authorised, throwaway-proof, prerequisite to any structural work). The structural zoning/HVAC rewrite was deliberately deferred to your decision.

## 3. THE DECISION YOU OWE THE USER FIRST

Tonight's decomposition (V15) quantifies *how much* of the Level-2 gap each cause explains, and the answer **strongly conditions the decision**:

> **42.0%** of the median gap is the **"Other" end-use** (fans, pumps, DHW/water systems, HVAC parasitics, refrigeration) — service loads the IdealLoads counterpart simply does not model. Heating+cooling = 36.3%, lighting+equipment = 19.8%. Basis correction (COP/fuel) barely moves the median (45.4%→44.5%) because it can't touch "Other". Richer zoning correlates with only a 4.5pp smaller gap and is confounded by archetype complexity. **Even a full Appendix-G + system-HVAC rewrite would reach only ~19% median deviation — still FAIL at ±5%** — unless brand-new service-end-use modeling (unspecified anywhere in DESIGN) is also added.

So the realistic options, in recommended order:

- **Option STOP (recommended)** — accept the Level-2 single-building gap as a *documented, decomposed* Phase-1 limitation. It is intellectually honest, non-blocking for the neighbourhood-scale use case (fleet composition smooths individual-building error), and R5 + R6-Batch-1 + R6-4A is a complete, publishable validation story. No DESIGN deviation. V15 §6.3 recommends this.
- **Option PHASE-1.5 (low payoff per the decomposition)** — formal DESIGN-deviation work item for richer zoning (toward Appendix-G) and/or PTAC HVAC. Requires the user to authorise editing the binding DESIGN/scope (the drift the role structure vetoes without manager-of-manager sign-off). Per §6.2 this alone cannot reach the ±5% gate — only worth it if paired with service-end-use modeling.
- **Option SERVICE-LOADS** — the only lever that addresses the dominant 42%: add DHW/fan/pump/refrigeration models. This has **no DESIGN basis at all** — it needs a new specification written and approved before any executor touches code. Largest scope.
- **Option REFERENCE-MATCH** — the *other* DQ-1 levers (PBA2/Boston-climate CBECS subsample, vintage-matched deterministic schedules) — addresses at most the 19.8% lighting+equipment share; possibly Phase-1-compliant and cheap, but small payoff.

**Do not start any of PHASE-1.5 / SERVICE-LOADS / REFERENCE-MATCH without the user's explicit pick.** Lead with the V15 numbers, recommend STOP, and let the user decide.

## 4. Current state — R6-4A COMPLETE (all tasks T01–T08, CP-A/B/C closed)

The overnight run finished cleanly. Authoritative record: §8 progress log of `PLAN_overall-validation-R6-4.md` + `memory/project_r6_4.md`.

- **TIER-1, zero resimulation.** `roundtrip_report.csv` already held per-end-use EUI for both reference and counterpart (18 cols), so the entire decomposition was pure analysis — no EnergyPlus ran. No frozen module was touched (verified via `git status`: only `scripts/validation/r6_4_*`, `tests/test_r6_4_*`, `docs/...r6_4_*`, `V15`).
- **Deliverables shipped:** `V15_R6_4_level2_decomposition.md` (synthesis + recommendation memo); `r6_4_level2_enduse.csv`, `r6_4_decomposition.{csv,md}`, `r6_4_basis_corrected.csv`; code `scripts/validation/r6_4_basis_overlay.py` (pure module), `r6_4_level2_decompose.py`, `r6_4_sensitivity.py`, `r6_4_produce_basis_corrected.py`; tests `tests/test_r6_4_basis_overlay.py` (15 tests).
- **Tests:** full suite **594 passed, 1 skipped** (was 579+1; +15 new). Green.
- **Append-only pointers** added to `V13_cross_case_synthesis.md` (near line 169) and `results/REPORT_R5_final.md` §6 — existing text intact (char counts verified in the §8 log).
- **Headline numbers:** raw round-trip 1/20 PASS (median |dev%| 45.4%); basis-corrected 1/20 PASS (44.5%); "Other" service loads = 42.0% of median gap (dominant in 11/20); zoning correlation single_zone 47.3% / one_zone_per_floor 43.5% / perimeter_core 42.8%.
- **Nothing is pending in R6-4A.** The only open item is the §3 decision (which the user must make). The plan is resume-safe if you ever want to re-verify: the Tier-1 path reproduces everything from `roundtrip_report.csv` with no resim.

## 5. Standing constraints (unchanged, must hold)

- All E+ **local, n_jobs=10 hard cap**, never 20 cores; **no cluster/sbatch** while the user's jobs are queued; **never `scancel`** anything.
- **Never git commit/add** (external auto-commit). **Never edit** OVERVIEW/DESIGN, root `main.py`, `tests/fixtures/labelled_archetypes_50.csv`, or `openubem/results/*` core math. **No `.py` under `docs/`.** Gates are **report-only** (V-R5-5) — never tune to pass.
- Manager writes plans + audits; **fresh Sonnet writes `openubem/`/`scripts/` code**. One Sonnet range at a time, audit at each checkpoint.
- R6-4A touched **no** frozen module — verify this still holds (the new code is all under `scripts/validation/` + `tests/`).

## 6. Suggested first moves for the morning session

1. Read V15 + the decomposition md; confirm tests are green (`py -3 -m pytest -q`).
2. Verify no frozen module was touched: `git status` should show only `scripts/validation/r6_4_*`, `tests/test_r6_4_*`, `docs/validations/overAll/results/r6_4_*`, `V15_*`, plan/memory edits.
3. Present the decomposition headline + the §3 decision to the user with a recommendation. Wait for their pick before any structural work.
