# ToDo — Wider Validation Matrix

**Status:** Backlog (not started) — 🔒 **register item OPEN-20 RETIRED here 2026-08-20 by user
ruling.** This document is now the only place the question is tracked.
**Logged:** 2026-06-17 · **ID retired:** 2026-08-20, following the OPEN-21 precedent
**Priority:** Optional / future — does not block any current work.
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` §2 (row struck) and
§6 (closing note). **`OPEN-20` is retired and must not be reused.**

---

## Why the ID was retired, 2026-08-20

The register holds **defects** — things that are wrong and that someone must fix. This is a **scope
question**: nothing is broken, nothing is blocked, and there is nothing to measure. It sat in the
backlog from 2026-06-17 to 2026-08-20 without ever being actionable, and it was tracked **twice** the
whole time — as a register row and as this document. Retiring the row removes the duplicate, not the
question.

**This is a deferral, not a decision against wider validation.** Like OPEN-21, it is a direction the
project may still take; it is simply not being taken now, and a future arc opens this document
deliberately.

**What the retirement rests on:** the item's substance was already discharged. T20(b) of
`PLAN_twenty-items-2026-08-19.md` wrote the external-validity statement in full —
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-18-20_method-bounds.md` §(b). It states what the
12-cell matrix supports, what it does not, and the one finding that bounds it hardest:

> **OPEN-19 bounds this further** — the simulation model does not yet vary construction or HVAC
> parameters by climate zone, so *even within the three represented cities* the physical basis for
> cross-climate generalisation is weaker than the geographic sampling alone suggests. The matrix
> samples three climates; the model does not yet fully differentiate its response to them.

⚠️ **That caveat is now this document's to carry, and it applies to every published figure** —
including the adopted **153.8231 kWh/m²**, which is a pooled statistic over exactly this population.
Its precision *within* the population is not in question; its reach beyond it is what this document
bounds. **Retiring the ID does not retire the caveat.**

## What

Extend OpenUBEM validation beyond the current 12-cell matrix to broader
geographic and climatic coverage.

Current matrix (R5, closed): **3 cities × 4 urban-form rings = 12 cells**
- Cities: New York (4A), Los Angeles (3B), Austin (2A)
- Rings: centre / urban / suburban / rural
- 8,152 buildings, 100% EnergyPlus success.

## Goal

More cities / climate zones for broader coverage — exercise the pipeline
against ASHRAE zones not yet represented (e.g. cold 5–7, hot-humid 1A,
marine 4C, dry 4B/5B) and additional urban morphologies.

## Why

R5 validated 3 of ~16 ASHRAE climate zones. Wider coverage would:
- stress-test archetype assignment and climate-zone enrichment outside the
  current 2A/3B/4A band;
- confirm the centre→rural fleet-morphology gradient generalises;
- strengthen the aggregate-scale validity claim across more climates.

## Notes / constraints (carry-over from R5/R6 governance)

- Gates remain **report-only** — never tune to pass.
- Manager writes the plan; fresh Sonnet executes.
- New cities require: footprints + climate-zone assignment + EPW weather +
  region-correct CBECS reference selection (West/South/Northeast/Midwest).
- Decide sim host policy per city (local n_jobs≤10 vs cluster) up front.

## Not now

Deferred until current priorities clear. Pick up by writing a PLAN doc that
defines the new cell list, weather/CBECS sources, and per-cell close criteria.
