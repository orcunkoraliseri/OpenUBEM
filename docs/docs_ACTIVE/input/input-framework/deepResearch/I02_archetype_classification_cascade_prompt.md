# Deep-Research Prompt I02 — ARCHETYPE CLASSIFICATION cascade (do OpenUBEM's size/level thresholds match precedent?)

> SCOPE GUARD — READ FIRST. This is the **threshold-validation** task. The deliverable is a sourced
> check of OpenUBEM's specific **size and level-count cutoffs** that decide which of the 30
> archetypes a building gets, once its use-class and tags are already known (tag → use-class is
> `I01`; this prompt starts from use-class). It is NOT about CBECS benchmarking (`I03`) and NOT
> about thermal zoning inside a building once the archetype is picked (that's the `layoutMapping`
> set). If you are writing about anything other than **where the size/level cut-points should sit
> and the source**, stop and return to the tables. See `00_README_input_classification_prompt_set.md`
> for the decision, shared facts, roster, conventions.

---

## What this document is

A fill-in-the-blanks request on cut-point precedent. OpenUBEM's classifier
(`openubem/semantic/building_classifier.py`, function `_apply_rule_table`) picks one archetype per
building using a 17-rule cascade with these **exact current thresholds**:

| Decision | OpenUBEM's current cut-point |
|---|---|
| Super-tall vs. tall building | ≥ 40 levels vs. 20–39 levels |
| Highrise vs. midrise apartment | ≥ 9 levels vs. < 9 levels |
| Large vs. small hotel | ≥ 4 levels vs. < 4 levels |
| Secondary vs. primary school | ≥ 5,000 m² footprint vs. < 5,000 m² footprint |
| Large vs. small data center | ≥ 500 m² footprint vs. < 500 m² footprint |
| Small / medium / large office | < 500 m² / < 4,000 m² / ≥ 4,000 m² **total floor area** (`footprint_area_m2 × levels`) |

None of these six cut-points has a cited source in the codebase — they were authored directly from
DESIGN-doc reasoning. We need to know what DOE/PNNL's own prototype-building selection guidance and
peer UBEM tools actually use, so the manager can confirm or correct each one with a citation.

## Role

UBEM building-classification research analyst. Trace every threshold to: the **DOE/PNNL Commercial
Prototype Building Models** documentation (the technical support documents that define each
prototype's intended size range — Office, School, Hotel, Apartment, Data Center), **ASHRAE 90.1**
Appendix G or the standard's own building-type size guidance if any, and how **URBANopt, CityBES,
AutoBEM, UMI, and CEA** select among size-tiered archetypes (small/medium/large office,
primary/secondary school, low/mid/high-rise residential, small/large hotel) from the GIS attributes
they actually have available (footprint area, floor count, assessor gross floor area, etc.).

## Why this matters (so you scope correctly)

A building near a cut-point (e.g. exactly 9 floors, or 480 m² total office floor area) gets an
entirely different envelope, internal-load density, schedule set, and HVAC system family depending
on which side of the line it falls — this is a step function, not a small error. If OpenUBEM's
cut-points don't match the DOE prototypes' own intended size range, every building assigned the
"wrong-sized" archetype inherits load/HVAC physics calibrated for a different building scale.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — DOE/PNNL prototype's own intended size range, per archetype

| Archetype | DOE/PNNL prototype's documented floor area / size range | Documented floor-count range | Source (TSD name + page/section) |
|---|---|---|---|
| SmallOffice |  |  |  |
| MediumOffice |  |  |  |
| LargeOffice |  |  |  |
| PrimarySchool |  |  |  |
| SecondarySchool |  |  |  |
| MidriseApartment |  |  |  |
| HighriseApartment |  |  |  |
| SmallHotel |  |  |  |
| LargeHotel |  |  |  |
| SmallDataCenterHighITE / LargeDataCenterHighITE |  |  |  |

### Table 2 — How each peer tool selects among size-tiered archetypes

| Tool | Attribute used to pick among small/medium/large variants (footprint area, total floor area, assessor gross area, floor count, other) | Cut-points used (if published) | Source |
|---|---|---|---|
| URBANopt / OpenStudio |  |  |  |
| CityBES |  |  |  |
| AutoBEM |  |  |  |
| UMI |  |  |  |
| CEA |  |  |  |

### Table 3 — OpenUBEM's six cut-points vs. precedent

| Decision | OpenUBEM's current cut-point | Precedent value found (Table 1/2) | Match / looser / stricter / GAP | Source |
|---|---|---|---|---|
| Super-tall vs. tall | ≥ 40 vs. 20–39 levels |  |  |  |
| Highrise vs. midrise apartment | ≥ 9 vs. < 9 levels |  |  |  |
| Large vs. small hotel | ≥ 4 vs. < 4 levels |  |  |  |
| Secondary vs. primary school | ≥ 5,000 m² vs. < 5,000 m² |  |  |  |
| Large vs. small data center | ≥ 500 m² vs. < 500 m² |  |  |  |
| Office small/medium/large | < 500 / < 4,000 / ≥ 4,000 m² total floor area |  |  |  |

### Table 4 — Vintage / `year_built` handling

| Source | Does `year_built`/vintage affect which archetype is picked, or only the envelope-vintage multiplier within a fixed archetype? | Source |
|---|---|---|
| OpenUBEM (current) | Only the envelope-vintage multiplier (`construction/PROVENANCE.md`) — archetype choice itself is vintage-blind | `building_classifier.py` (no `year_built` reference in `_apply_rule_table`) |
| URBANopt / OpenStudio |  |  |
| CityBES |  |  |
| AutoBEM |  |  |
| DOE/PNNL prototypes (do they define a vintage-specific archetype, e.g. "pre-1980 office" as a distinct type rather than a multiplier?) |  |  |

---

## Part C — Synthesis (threshold-by-threshold verdict)

For **each of the six cut-points in Table 3**, give an explicit verdict: keep as-is (cite the
matching precedent), or change to a specific cited value, or **"GAP — no clear precedent, keep
current value as the defensible default"**. Then address vintage: should OpenUBEM ever let
`year_built` influence archetype *selection* (not just the envelope multiplier), and is there
precedent for that, or is the current vintage-blind cascade standard practice?

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C threshold-by-threshold verdict.
3. Cite the DOE/PNNL Technical Support Document by name for every prototype size claim.
4. **"Confidence and caveats":** which cut-point is least defensible either way.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give a verdict for all six cut-points individually** — do not summarize them as a group.
- **Cite the actual DOE/PNNL prototype TSD** (not a secondary description) wherever possible.
- **State units explicitly** (m² vs. ft²) and show the conversion if the source uses IP units.
- **No fabricated precision;** flag GAPs. **Stay on topic** — classification thresholds only, not
  zoning or CBECS mapping.
