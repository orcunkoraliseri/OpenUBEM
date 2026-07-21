# Deep-Research Prompt M02 — PEER UBEM TOOL attribute imputation (how established tools fill missing building inputs)

> SCOPE GUARD — READ FIRST. This is the **"what do peer tools actually do"** anchor for the whole set.
> The deliverable is a sourced, tool-by-tool account of how established UBEM/GIS-to-BEM tools fill the
> specific inputs OpenUBEM struggles with when OSM is silent: **floor count / height, use / function,
> vintage / `year_built`, and floor area / footprint gaps**. It is NOT about generic missing-data
> theory (that's `M01`) and NOT about a single method's accuracy in the abstract (that's `M03`–`M06`);
> it is about *what shipped tools substitute and whether they call it a default or an inference*. See
> `00_README_imputation_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

A fill-in-the-blanks comparison across the peer tools OpenUBEM benchmarks itself against. OpenUBEM's own
handling is known and pre-filled below; the empty cells are what we need. The question the manager must
answer from this table: *is OpenUBEM's per-input handling (heuristic height→levels, oldest-vintage
default, KDE construction fill, size-bucketed office fallback) in line with, more rigorous than, or
cruder than how UMI/CEA/CityBES/AutoBEM/TEASER/3DCityDB fill the same gaps?*

## Role

UBEM / GIS-to-BEM tooling research analyst. Trace every behaviour to the tool's own documentation or a
peer-reviewed description: **UMI** (Dogan & Reinhart), **City Energy Analyst / CEA** (Fonseca et al. —
its data-management / archetype-inference layer), **CityBES** (Hong et al. — county-assessor-driven),
**AutoBEM** (New et al., ORNL — footprint + assessor + inferred height), **URBANopt/OpenStudio** (NREL),
**TEASER / GEM** (RWTH — statistical archetype enrichment), and **3DCityDB / CityGML LoD** workflows
(how they populate missing height/function attributes). Include the İşeri et al. in-repo paper as a
first-class peer method (its KDE-based fill).

## Why this matters (so you scope correctly)

Every input OpenUBEM imputes was imputed by these tools first, and their choices are the closest thing to
an industry convention. If four of six peer tools infer height from a footprint-area regression or a
LiDAR/DSM join rather than OpenUBEM's flat `height // 3.5` heuristic, that is a concrete, citable upgrade.
If they all fall back to a construction-year *default* the same way OpenUBEM does, that ratifies the
current behaviour. This prompt converts "we guessed" into "here is what the field does, and whether we
match it."

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Missing floor-count / height

| Tool | What it substitutes when floor count / height is absent | Default vs. real inference (regression / LiDAR / assessor)? | Provenance recorded? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| CityBES |  |  |  |  |
| AutoBEM |  |  |  |  |
| URBANopt/OpenStudio |  |  |  |  |
| TEASER / GEM |  |  |  |  |
| 3DCityDB / CityGML |  |  |  |  |
| İşeri et al. (in-repo) |  |  |  |  |
| **OpenUBEM (current)** | `max(1, height_m // 3.5)`; both absent → `1` | Heuristic constant (3.5 m/floor), not inference | Yes — `HEURISTIC_HEIGHT` / `HEURISTIC_DEFAULT` flag | `building_classifier.py:121-127` |

### Table 2 — Missing use / function

| Tool | What it substitutes when use/function is absent | Inference method (dominant-use of block, land-use join, ML)? | Provenance recorded? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| CityBES |  |  |  |  |
| AutoBEM |  |  |  |  |
| TEASER / GEM |  |  |  |  |
| İşeri et al. (in-repo) |  |  |  |  |
| **OpenUBEM (current)** | `OpenUBEMUnknown` (LOW) or size-bucketed office if `building=yes` | No inference — sentinel + size heuristic | Yes — `FALLBACK_UNKNOWN` / `FALLBACK_SIZE_DEFAULT`, confidence LOW | `building_classifier.py:316-317`, rule 17a |

### Table 3 — Missing vintage / `year_built`

| Tool | What it substitutes when construction year is absent | Default value / distribution used | Does missing→oldest, →median, →distribution, or →region-typical? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| CityBES |  |  |  |  |
| AutoBEM |  |  |  |  |
| TEASER / GEM |  |  |  |  |
| İşeri et al. (in-repo) |  |  |  |  |
| **OpenUBEM (current)** | `DOERefPre1980` (oldest tier, U-factors ×1.6) | Single deterministic oldest-vintage bin | missing → **oldest** | `construction_sets.py:44,129-139` |

### Table 4 — Missing semantic parameters (U-value, load, COP) & the imputation *style*

| Tool | How it fills a missing envelope/load/system parameter | Deterministic archetype value, distribution sample, or ML? | Is uncertainty propagated (single vs. multiple imputation)? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| CityBES |  |  |  |  |
| TEASER / GEM |  |  |  |  |
| İşeri et al. (in-repo) |  |  |  |  |
| **OpenUBEM (current)** | KDE-fill (envelope) from sibling climate zones; `.get() or default` (HVAC/DHW — silent) | Distribution sample (envelope) / deterministic default (HVAC) | Single imputation — no uncertainty propagated | `construction_sets.py:171-219`; `idf/hvac.py`, `idf/dhw.py` |

---

## Part C — Synthesis (per-input verdict)

For **each of the four inputs** (height/levels, use, vintage, semantic params), give an explicit verdict:
(a) does OpenUBEM's current handling match the majority of peer tools, is it more rigorous, or is it
cruder; (b) the single most-cited upgrade the field would suggest (e.g. "≥3 tools infer height from a
LiDAR/DSM join — see `M07`"); (c) whether any peer tool propagates imputation *uncertainty* into its
results while OpenUBEM's single-imputation approach does not (feeds `M09`). End with the one input where
OpenUBEM is furthest behind peer practice — the highest-value target for the implementation plan.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C per-input verdict.
3. Cite each tool's documentation/paper explicitly; flag where a tool's behaviour is undocumented (GAP).
4. **"Confidence and caveats":** which tool's imputation behaviour is least documented and therefore
   most uncertain in the table.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Cover ≥5 peer tools** plus the İşeri in-repo paper.
- **For every tool, state whether its fill is a default or a real inference** — this distinction is the
  point of the prompt.
- **Note provenance/uncertainty handling per tool** — whether it records that a value was imputed
  (feeds OpenUBEM's non-negotiable provenance requirement and `M09`).
- **No fabricated precision;** flag GAPs. **Stay on topic** — peer-tool *fill behaviour* only, not
  method-accuracy benchmarks or generic mechanism theory.
