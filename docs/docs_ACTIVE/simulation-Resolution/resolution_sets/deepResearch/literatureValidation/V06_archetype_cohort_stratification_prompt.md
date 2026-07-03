# Deep-Research Prompt V06 — ARCHETYPE-COHORT stratification of resolution sensitivity

> SCOPE GUARD — READ FIRST. This is a **published-range** task. The deliverable is a sourced, quantitative
> account of **which BUILDING-TYPE cohorts are resolution-SENSITIVE** (offices, high-rise / deep-plan
> residential, hospitals / schools with distinct core loads) **versus resolution-INSENSITIVE** (warehouse,
> low-rise, inherently single-zone), and the **geometric / load reason** each cohort behaves that way
> (perimeter-to-core ratio, corridor presence, internal-load intensity). It is NOT the aggregate magnitude
> (V01) or the district wash-out (V05); it is purely the **per-cohort sensitivity, the reason for it, and
> the resulting reporting stratification**, with sources.
> If you are writing about anything other than **a per-cohort resolution-sensitivity finding (magnitude +
> geometric reason) and its source**, stop and return to the tables. Purpose: RESULT_11 requires the
> validation be reported **STRATIFIED by cohort, never city-average** — this prompt supplies the strata.
> See `00_README_literature_validation_prompt_set.md` for the decision, shared facts, mode map, seed
> references, conventions.

---

## What this document is

A fill-in-the-blanks evidence table. The zoning-resolution error is not uniform across building types: it
concentrates in cohorts with a large daylit/thermally-distinct perimeter relative to core and with strong
internal loads (offices, deep-plan / high-rise residential, hospitals, schools), and largely vanishes in
inherently single-zone cohorts (warehouses, low-rise, open big-box). OpenUBEM must report validation
per-cohort so a resolution-sensitive type is not hidden behind a resolution-insensitive one in a
city-average. We need the **published evidence** for which cohorts are sensitive, by how much, and the
geometric reason — then map it onto OpenUBEM's archetype roster. Treat each cell as a question; fill with a
sourced magnitude/finding or a GAP.

## Role

UBEM validation / building-energy-simulation research analyst. Trace every finding to a peer-reviewed study
or tool-accuracy report that **compares zoning resolutions across building types** or otherwise reports
**how zoning-error magnitude varies by archetype / geometry class**, ideally input-invariant (same
loads/schedules/envelope/weather, zoning varied). Prioritise: **Dogan & Reinhart 2017 (Shoeboxer)**,
**Chen & Hong (CityBES)**, **Cerezo Davila 2017 (Boston)** stratified reporting, **Johari 2022 (review)**,
**Faure 2022**, and DOE/PNNL prototype comparisons that span office / residential / warehouse / school /
hospital. SI throughout.

## Why this matters (so you scope correctly)

Zero-fitted-parameters means OpenUBEM cannot calibrate a cohort-specific delta away — each cohort's zoning
sensitivity must *survive* comparison to the literature, and RESULT_11 forbids reporting a single
city-average that would mask a sensitive cohort. The manager needs to know which of OpenUBEM's archetypes
(offices, high-rise residential, warehouse, school, hospital, retail, etc.) carry the real zoning risk, and
the geometric signature (perimeter-to-core ratio, corridor presence, internal-load intensity) that predicts
it, so validation is reported in the right strata and a large delta on a deep-plan office is recognised as
expected while a near-zero delta on a warehouse is confirmed as correct — not a bug in either direction.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Resolution sensitivity by archetype cohort

| Building-type cohort | Zoning-EUI Δ magnitude (signed %, coarse−fine) | Resolution-sensitive? (Y/N) | Study (author, venue, year) | Source detail (page/fig) |
|---|---|---|---|---|
| Office (shallow / deep plan) |  |  |  |  |
| High-rise / deep-plan residential |  |  |  |  |
| Hospital / healthcare |  |  |  |  |
| School / education |  |  |  |  |
| Retail |  |  |  |  |
| Warehouse / big-box / low-rise |  |  |  |  |

*(Add rows per cohort/study; state the sign convention per row.)*

### Table 2 — The geometric / load reason each cohort is (in)sensitive

| Cohort | Perimeter-to-core ratio | Corridor / distinct-core presence | Internal-load intensity | Why this makes it sensitive or insensitive | Source |
|---|---|---|---|---|---|
| Office |  |  |  |  |  |
| High-rise / deep-plan residential |  |  |  |  |  |
| Hospital / healthcare |  |  |  |  |  |
| School / education |  |  |  |  |  |
| Retail |  |  |  |  |  |
| Warehouse / big-box / low-rise |  |  |  |  |  |

### Table 3 — Recommended reporting strata for a UBEM validation

| Reporting stratum | Which cohorts it groups | Why grouped this way (shared sensitivity/geometry) | Source / precedent |
|---|---|---|---|
| High-sensitivity stratum |  |  |  |
| Moderate-sensitivity stratum |  |  |  |
| Low / insensitive stratum |  |  |  |

### Table 4 — OpenUBEM cross-check (map cohorts onto OpenUBEM's archetype roster)

| OpenUBEM archetype (roster) | Published sensitivity class (from Tables 1–3) | In-envelope? (Y/N/partial) | Note |
|---|---|---|---|
| Offices |  |  |  |
| High-rise residential |  |  |  |
| Warehouse / low-rise |  |  |  |
| School / hospital / other core-load cohorts |  |  |  |
| (Overall) effect concentrates in resolution-sensitive cohorts, washes out in insensitive ones |  |  |  |

---

## Part C — Synthesis (the stratification for OpenUBEM)

Give: (1) the **ranked list** of OpenUBEM's archetype cohorts by zoning-resolution sensitivity, each with a
published magnitude range (signed %) and the geometric reason; (2) the **recommended reporting strata** (how
to group OpenUBEM's roster so RESULT_11's stratified reporting is defensible and no sensitive cohort is
masked); (3) the geometric signature (perimeter-to-core ratio, corridor presence, internal-load intensity)
that predicts sensitivity, so a new archetype can be classified; (4) the conditions under which a cohort's
observed delta should be flagged **out-of-envelope / investigate**. Name the published source for each
bound. Flag any cohort with no published range as a GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C stratification + the explicit cohort-by-cohort sensitivity ranking for OpenUBEM's roster.
3. Cite each study explicitly (author, venue, year, and the figure/table the number comes from).
4. **"Confidence and caveats":** where the literature is thin or conflicting, and which cohort is least
   covered.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Report per-cohort, never a single city-average** — a lumped number defeats the purpose of this prompt
  (RESULT_11 requires stratified reporting).
- **Give the geometric / load reason** (perimeter-to-core ratio, corridor, internal-load intensity) for
  each cohort's sensitivity class, with sources — not just the magnitude.
- **Return numeric ranges in signed %** where available, with the sign convention stated per row — flag
  cohorts where only a qualitative Y/N is published as a GAP on magnitude.
- **Map every finding onto OpenUBEM's archetype roster** (offices / high-rise residential / warehouse /
  school / hospital / retail …) in Table 4.
- **No fabricated precision;** flag GAPs. **Stay on topic** — cohort stratification of resolution
  sensitivity only (aggregate magnitude → V01; district wash-out → V05).

---

*OpenUBEM resolution-mode — literature-validation sub-set. Markdown only; binding specs remain
`docs/docs_main/`. 2026-07-01.*
