# Prompt 3 — Energy-accuracy impact of zoning simplification (one-zone-per-floor vs core+perimeter)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** Our fix falls back from core+perimeter zoning to **one thermal zone per floor** on degenerate footprints. That is coarser: it loses the thermal distinction between sun-exposed perimeter and shielded core. We need to know, from the literature, **how much energy error that simplification introduces** — so we can state (and defend) the accuracy cost in the report, and decide whether the handful of affected buildings matter at the city-aggregate scale. This is the "quantify the cost of graceful degradation" question.

---

```
You are a building-energy-simulation methodologist. I need a rigorous, citeable review of how
THERMAL-ZONING RESOLUTION affects EnergyPlus / building energy simulation results — specifically the
error introduced by simplifying from an ASHRAE-style CORE + PERIMETER multi-zone model to a single
zone per floor (or a single zone for the whole building).

Do deep web research across peer-reviewed papers, ASHRAE / IEA EBC reports, and BEM tool
documentation. Address:

1. THE CORE/PERIMETER RATIONALE: why standards and tools split floors into a core plus 4+ perimeter
   zones (perimeter depth ~4.57 m / 15 ft) — what physical effect (solar gains, envelope-driven
   loads, differing setpoints/HVAC) this captures that a single zone cannot. Cite the standard
   (e.g. ASHRAE 90.1 Appendix G / PRM) and key references.

2. QUANTIFIED ERROR from zoning simplification: gather published comparisons of single-zone vs
   multi-zone (core/perimeter) models for the SAME building — report the magnitude and direction of
   error in annual heating, cooling, and total energy (EUI). Give specific percentages and the study
   conditions (building type, climate). Note especially any results for the regimes OpenUBEM covers
   (offices, mid-rise apartments; climate zones 2A Austin, 3B/4B Los Angeles, 4A New York).

3. DEPENDENCE ON BUILDING DEPTH/COMPACTNESS: evidence on when single-zone simplification is
   ACCEPTABLE — e.g. small-footprint or deep-plan buildings where perimeter area is a small fraction
   of floor area, so core/perimeter and single-zone converge. Is there a footprint-size or
   surface-to-volume threshold below which the simplification is considered negligible? Cite it.

4. UBEM-SCALE PERSPECTIVE: at the URBAN aggregate scale (thousands of buildings), how much does
   simplifying a SMALL FRACTION of pathological buildings to single-zone affect the city/portfolio
   total EUI? Cite any UBEM validation work discussing per-building zoning error vs aggregate error
   cancellation, and the accepted accuracy bands for UBEM (e.g. CV(RMSE), NMBE targets, ASHRAE 14
   calibration thresholds).

5. BEST-PRACTICE STATEMENT: is "fall back to a simplified single/one-per-floor zoning for buildings
   whose automatic core/perimeter decomposition fails" a documented, defensible practice in UBEM
   workflows? Quote any tool docs or papers that explicitly adopt it.

Output as clean markdown: a numbered section per topic, a summary table
[Study | Building type | Climate | Single-zone vs core/perim error % | Notes], and a one-paragraph
DEFENSIBILITY VERDICT I can cite in a validation report on whether falling back to one-zone-per-floor
for a small minority of degenerate footprints is acceptable, with the strongest supporting citation.
Give a full citation (title, author/org, year, URL, access date) for every claim. If the literature is
thin or mixed on any point, SAY SO EXPLICITLY rather than overstating. Flag anything you are not fully
confident about.

WHEN FINISHED: save your full response as a markdown file named
`RESULT_3_zoning_simplification_energy_impact.md` in the SAME FOLDER as this prompt document
(`docs/implementation/phaseC_combinedResim/deepResearch`).
```

---

**After researching, save your full response as a markdown file named**
`RESULT_3_zoning_simplification_energy_impact.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\phaseC_combinedResim\deepResearch`
