# Deep-Research Prompt I01 — OSM TAG → USE-CLASS mapping (how peer tools turn raw attribute tags into a building-type taxonomy)

> SCOPE GUARD — READ FIRST. This is a **methods-comparison** task about exactly one step: turning a
> raw building/amenity/shop/office tag (OpenStreetMap, or the closest equivalent attribute in a
> peer tool's data source) into a small, coarse **use-class** bucket. It is NOT about which of the
> 30 final archetypes a building gets (that's `I02`), and NOT about CBECS benchmarking (`I03`). If
> you are writing about anything other than **how raw tags are bucketed into use-classes and the
> source**, stop and return to the tables. See `00_README_input_classification_prompt_set.md` for
> the decision, shared facts, roster, conventions.

---

## What this document is

A fill-in-the-blanks comparison. OpenUBEM has no per-building survey of what each building
actually is — it has only OpenStreetMap tags (`building=*`, `amenity=*`, `shop=*`, `office=*`,
contributed by volunteers, inconsistently populated). Its current solution is a manually curated
**~60-entry lookup table** (`osm_to_use_class.json`) mapping specific tag values to one of **6
use-classes**: `residential, commercial, industrial, institutional, mixed, unknown`. We need to know
how established UBEM tools and OSM-classification literature solve the same raw-attribute-to-class
problem, so the manager can judge whether OpenUBEM's specific taxonomy, tag list, and
conflict-resolution rule are defensible.

## Role

UBEM/GIS building-classification research analyst. Trace every method to the tool's own
documentation or a peer-reviewed description: **URBANopt/OpenStudio** (`Building Type` input field
and its mapping guidance), **CityBES** (Hong et al. — uses county assessor Land Use Codes),
**AutoBEM** (New et al., ORNL — uses footprint + county assessor records + NAICS codes), **UMI**
(Dogan & Reinhart — manual/GIS-attribute building-type assignment), **City Energy Analyst (CEA)**
(Fonseca et al. — zone `STANDARD`/use-type code), plus any peer-reviewed studies specifically on
**automated OpenStreetMap building-function/use classification** (e.g. work using `osmnx`,
machine-learning OSM-tag classifiers, or building-function inference from volunteered geographic
information), and the **OpenStreetMap wiki**'s own `building=*`/`amenity=*` tagging guidance.

## Why this matters (so you scope correctly)

OpenUBEM's tag map was authored once, by hand, from the DESIGN doc's own reasoning — never checked
against precedent. Two concrete risks: (1) **taxonomy granularity** — is 6 classes
(residential/commercial/industrial/institutional/mixed/unknown) the right cut, or do peer tools use
more/fewer/different buckets that better separate buildings that get materially different physics
downstream (e.g. splitting "institutional" into education vs. healthcare vs. government, which
OpenUBEM currently lumps together at the use-class level and only re-separates later via
`function_tag`/`building_tag` in the archetype rule cascade)? (2) **tag coverage** — OSM has dozens
of building/amenity/shop tags OpenUBEM's ~60-entry map may not cover (e.g. less common
`building=`/`amenity=` values), silently routing real buildings to `unknown` → `OpenUBEMUnknown`.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Use-class taxonomy per tool/source

| Tool / source | # of use-classes / building-type buckets at the coarse level | Bucket names | Real footprint-tag-driven or attribute-table-driven? | Source |
|---|---|---|---|---|
| OpenUBEM (current) | 6 | residential, commercial, industrial, institutional, mixed, unknown | Tag-driven (OSM `building=`/`amenity=`/`shop=`/`office=`) | `osm_to_use_class.json` |
| URBANopt / OpenStudio |  |  |  |  |
| CityBES |  |  |  |  |
| AutoBEM |  |  |  |  |
| UMI |  |  |  |  |
| City Energy Analyst (CEA) |  |  |  |  |
| OSM-classification literature (name the paper) |  |  |  |  |

### Table 2 — Tag priority / conflict-resolution rule per source

| Source | Does a function/use tag (amenity, shop, office) outrank a generic structural tag (building=*)? | What happens when two tags disagree | OpenUBEM's current rule (for comparison) | Source |
|---|---|---|---|---|
| URBANopt / OpenStudio |  |  | — | |
| CityBES |  |  | — | |
| AutoBEM |  |  | — | |
| UMI |  |  | — | |
| CEA |  |  | — | |
| OpenUBEM (current) | Symmetric — both must agree or row becomes `mixed` (score 0.5) | `mixed`; re-routed via dominant-tag rule at ≥0.60 score, else default | — | `building_classifier.py` `_normalise_use_class` |

### Table 3 — Missing / ambiguous tag handling

| Source | Fallback class when no usable tag exists | Reported "unclassified"/"unknown" rate (if published) | Source |
|---|---|---|---|
| URBANopt / OpenStudio |  |  |  |
| CityBES |  |  |  |
| AutoBEM |  |  |  |
| UMI |  |  |  |
| CEA |  |  |  |
| OpenUBEM (current) | `unknown` → cascades to `OpenUBEMUnknown` (LOW confidence) or size-bucketed office default if `building=yes` | not yet measured at city scale — note as GAP if no published OpenUBEM number exists |  |

### Table 4 — Reported classification accuracy (if any literature reports it)

| Source | Ground-truth comparison performed? | Reported accuracy / error rate | Confounders noted by the authors | Source |
|---|---|---|---|---|
| (OSM-classification literature) |  |  |  |  |
| (any of the 5 tools above, if they report validation) |  |  |  |  |

---

## Part C — Synthesis (assessment of OpenUBEM's current tag map)

Give: (1) whether OpenUBEM's **6-class taxonomy** is finer, coarser, or differently cut than
established practice, with a recommendation only if the evidence is clear; (2) whether the
**symmetric agree/disagree conflict rule** (vs. a strict priority order like "amenity always beats
building") matches how peer tools resolve multi-tag buildings; (3) a list of **specific OSM tag
values** that peer literature/tools commonly classify but that do **not** appear in OpenUBEM's
current ~60-entry `tag_to_use_class` map (name the exact tag string, e.g. `amenity=community_centre`,
and the use-class it should plausibly map to, with justification) — this is the most actionable
output of this prompt; (4) whether OpenUBEM's `unknown`/fallback handling is more or less aggressive
than peer tools' approach to unclassifiable buildings.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Cite each tool's documentation/paper explicitly.
4. **"Confidence and caveats":** which comparison is weakest (e.g. if a tool doesn't use OSM at all
   and the comparison is necessarily approximate).
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Compare ≥5 tools/sources** (URBANopt, CityBES, AutoBEM, UMI, CEA) plus ≥1 OSM-specific
  classification study or the OSM wiki taxonomy.
- **Name specific missing OSM tags** OpenUBEM should add to `osm_to_use_class.json`, each with a
  proposed use-class and source — this is the deliverable the manager acts on directly.
- **No fabricated precision;** flag GAPs. **Stay on topic** — tag → use-class only, not the
  downstream archetype assignment.
