# Deep-Research Prompt L15 — VALIDATION METHODOLOGY & COMPUTATIONAL COST (how to trust a generated layout, and what it costs)

> SCOPE GUARD — READ FIRST. This prompt answers two operational questions: (1) **how do you validate a
> *generated* interior layout** when there is no ground-truth floor plan for a city's buildings, and
> (2) **how do zone count, IDF size, and EnergyPlus runtime scale** with layout resolution across the
> fleet. It is NOT the accuracy-benefit question (that's `L14`, which asks *whether* room-level changes
> EUI); this asks *how to verify the generator is correct* and *what it costs to run*. See
> `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The verification-and-budget reference. `layoutGenerator.py` produces layouts for buildings whose real
interiors OpenUBEM will never see, so classical "compare to truth" validation is impossible. The manager
needs the field's methods for validating synthetic layouts (geometric plausibility checks, mask-and-
recover on the few buildings with known plans, downstream-EUI stability, expert review) and a realistic
cost model, since forcing `zone` mode fleet-wide was estimated at ~12× the building-level zone count.

## Role

UBEM validation / HPC-cost research analyst. Ground the validation methods in the UBEM validation
literature (calibration/validation frameworks — ASHRAE Guideline 14 concepts adapted to stock,
cross-validation on buildings with known plans, the İşeri et al. validation approach) and the
layout-plausibility literature (net-to-gross ratios, circulation-fraction sanity, geometric-validity
checks). Ground the cost scaling in EnergyPlus performance data (runtime vs. zone count / surface count)
and the project's own fleet numbers (8,152 buildings; ~8,200 / ~19,700 / ~98,000 zones for
building/floor/zone modes).

## Why this matters (so you scope correctly)

Without a validation story, a "more realistic" layout is unfalsifiable and could quietly bias the fleet.
And without a cost model, room-level might be infeasible at city scale on the cluster. The manager needs
both: a concrete acceptance test for the generator (geometric + energetic), and the runtime/zone budget so
the plan can decide whether room-level is fleet-wide or targeted (`L14`'s decision table) — and how it
fits the sbatch-array cluster workflow.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Validation methods for a synthetic layout

| Method | What it checks | Needs ground-truth plans? | Applicable at city scale? | Source |
|---|---|---|---|---|
| Geometric-validity check (no slivers, closed zones, valid E+ geometry) |  | No |  |  |
| Net-to-gross / circulation-fraction sanity vs. DOE prototype |  | No |  |  |
| Mask-and-recover on buildings with known plans |  | Yes (few) |  |  |
| Downstream-EUI stability (generated vs. floor-level totals conserved) |  | No |  |  |
| Expert plausibility review (sample) |  | No |  |  |
| Cross-check vs. DOE prototype EUI for that archetype |  | No |  |  |

### Table 2 — Acceptance criteria (what "the generator is correct" means)

| Criterion | Threshold (cite or GAP) | How measured | Source |
|---|---|---|---|
| Conserved conditioned floor area | exact (`footprint×floors`) |  | (see L11) |
| Conserved total loads | within ε of floor-level model |  |  |
| Circulation fraction within DOE-prototype range |  |  |  |
| No E+ geometry fatals across fleet | 0 |  |  |
| EUI vs. floor-level within expected sensitivity band | (from L14) |  |  |

### Table 3 — Computational cost scaling

| Resolution mode | ~Zones (8,152-bldg fleet) | Relative E+ runtime | IDF size / surface-count driver | Feasible fleet-wide on cluster? | Source |
|---|---|---|---|---|---|
| building (single-zone) | ~8,200 | 1× |  |  | project fleet numbers |
| floor (per-floor) | ~19,700 | ~2.4× |  |  | project fleet numbers |
| zone / room-level (B1 + layoutGenerator) | ~98,000 (upper bound) | ~12× |  |  | project fleet numbers |

### Table 4 — Cost-control levers

| Lever | Effect on cost | Effect on accuracy | Source |
|---|---|---|---|
| Zone-multiplier for identical units (E+ `Zone Multiplier`) |  |  |  |
| Merge same-orientation perimeter units |  |  |  |
| Target room-level only where `L14` says it matters |  |  |  |
| Representative-floor modeling (multiplier on mid-floors) |  |  |  |

---

## Part C — Synthesis (the V&V + budget plan)

Give: (1) a concrete **acceptance-test suite** for `layoutGenerator.py` — the geometric + energetic checks
that must pass, with thresholds cited or flagged GAP; (2) a **validation strategy** given no ground-truth
interiors (which of Table 1's methods to use, and how to get a few known-plan buildings for mask-and-
recover); (3) a **cost verdict** — is room-level feasible fleet-wide, or must it be targeted per `L14`,
and how it maps to the sbatch-array workflow; (4) the cost-control levers to adopt. This section feeds
directly into the plan's stop-and-report checkpoints and test tasks.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C V&V + budget plan.
3. Cite validation-methodology and E+ performance sources.
4. **"Confidence and caveats":** which cost estimate or threshold is least certain.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Deliver a concrete acceptance-test suite** with thresholds (the plan will encode these as tests).
- **Give a realistic fleet cost verdict** tied to the project's actual zone-count numbers and the
  cluster/sbatch workflow.
- **Address the no-ground-truth problem head-on** — mask-and-recover source + plausibility checks.
- **No fabricated precision;** flag GAPs. **Stay on topic** — validation & cost only, not the
  accuracy-benefit case (`L14`).
