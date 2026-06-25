# ToDo — Wider Validation Matrix

**Status:** Backlog (not started)
**Logged:** 2026-06-17
**Priority:** Optional / future — does not block any current work.

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
