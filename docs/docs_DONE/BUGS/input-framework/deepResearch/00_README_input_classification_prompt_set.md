# Input Classification — Deep-Research Prompt Set (INDEX)

> READ FIRST. Every other deep-research set in this repo (HVAC/DHW/cooking/refrigeration in
> `docs/docs_DONE/hvac-ServiceLoads/deepResearch/`, geometry in
> `docs/docs_ACTIVE/simulation-Resolution/deepResearch/layoutMapping/`) assumes a building has
> **already** been classified into one of OpenUBEM's 30 archetypes. This set is about the step
> *before* all of that: turning raw OpenStreetMap tags into `archetype_id`. It is currently the
> **only** input category (per `docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md` rows 2, 3, 16)
> with **zero** deep-research backing — every other bundled data file traces to a PROVENANCE.md or
> a RESULT_*.md; the classification cascade traces only to its own DESIGN section and was authored
> without reference to how peer UBEM tools solve the same problem. Run each prompt in your
> deep-research tool; save the answer beside it as `RESULT_<id>_<slug>.md`. The manager audits and
> decides whether to revise `osm_to_use_class.json`, the rule cascade in
> `openubem/semantic/building_classifier.py`, or `cbecs_pba_map.json`.

---

## The exact decision this set must inform

`archetype_id` is the single fan-out point of the entire pipeline: it selects the envelope
(`ashrae_90_1_2019.json`), internal loads (`doe_prototype_loads.json`), schedules
(`doe_schedules.json`), HVAC system family (`hvac_systems_by_archetype.json`), DHW/cooking/
refrigeration intensities, and the CBECS benchmark an archetype is scored against. A classification
error doesn't cause a small numeric error — it swaps in an entirely wrong physics model. The
classifier (`openubem/semantic/building_classifier.py`) is a **17-rule cascade** over
`(use_class, function_tag, building_tag, levels, footprint_area_m2)`, fed by a **manually curated
~60-entry tag map** (`osm_to_use_class.json`). Both were authored directly from the DESIGN doc's own
reasoning — neither was checked against how URBANopt, CityBES, AutoBEM, UMI, or CEA do the
equivalent step. **We are not asking you to redesign the cascade — we are asking how peer UBEM
tools and the literature actually do raw-attribute-to-building-type classification, with sources,
so the manager can judge whether OpenUBEM's specific rules/thresholds are defensible or need a
cited fix.**

---

## The prompts

| # | File | What it learns |
|---|------|----------------|
| I01 | `I01_osm_tag_to_use_class_mapping_prompt.md` | Whether OpenUBEM's 6-class taxonomy and ~60-tag → use-class map (and its function-tag-beats-building-tag precedence rule) matches established OSM/GIS building-classification practice; what tags are conspicuously missing. |
| I02 | `I02_archetype_classification_cascade_prompt.md` | Whether the 17-rule cascade's specific size/level thresholds (office 500/4,000 m², school 5,000 m², apartment 9 levels, hotel 4 levels, data center 500 m², high-rise 20/40 levels) match DOE/PNNL prototype selection guidance or peer-tool practice. |
| I03 | `I03_cbecs_pba_crosswalk_validation_prompt.md` | Whether the archetype → CBECS-2018 Principal Building Activity (PBA) crosswalk used for national benchmarking is consistent with published precedent, including the residential/data-center exclusions. |

> Load-bearing core: **I01 + I02** (the classification cascade itself — everything downstream
> depends on getting these two right). I03 matters specifically for the national-CBECS validation
> gates, not the simulation physics.

---

## Shared facts (all prompts assume these)

- **6 use-classes** (`osm_to_use_class.json`): `residential, commercial, industrial, institutional,
  mixed, unknown`. A row gets a use-class by looking up `function_tag` (from `amenity=`/`shop=`/
  `office=`, first non-null wins) and `building_tag` (from `building=`, excluding the literal value
  `"yes"`) independently in the tag map: if both resolve and **agree** → that class, confidence 1.0;
  if they **disagree** → `"mixed"`, score 0.5; if only one resolves → that one; if neither → `"unknown"`.
- **Tag-map precedence is currently function-tag-and-building-tag-symmetric** (neither overrides the
  other outright — they must agree or the row becomes `"mixed"`). This is itself a design choice
  worth checking against peer practice (rather than e.g. function_tag always winning).
- **`mixed` rows** are re-routed by a **dominant-tag rule**: if the agreement/disagreement score is
  ≥ **0.60**, the row recurses into the rule cascade using whichever of function_tag/building_tag
  resolved a non-null class; below threshold, or if neither resolves, `mixed` rows default to
  `MidriseApartment` (Pass-2 fallback — itself worth scrutiny, see I02).
- **The 17-rule cascade**, in order (current OpenUBEM thresholds, all on `footprint_area_m2` unless
  noted): super-tall ≥ 40 levels / tall 20–39 levels (commercial/institutional/mixed/unknown) →
  highrise apartment ≥ 9 levels / midrise < 9 levels (residential) → large hotel ≥ 4 levels / small
  hotel < 4 levels → restaurant tags (full-service vs. quick-service/cafe/bar/pub) → hospital /
  outpatient (clinic/doctors/dentist) → college/university → secondary school ≥ 5,000 m² / primary
  school < 5,000 m² (area, not total floor area) → courthouse (government/public/civic tags) →
  laboratory → data center ≥ 500 m² (large) / < 500 m² (small) → warehouse/industrial tags →
  supermarket / strip-mall / standalone-retail tags → **office by use_class + total floor area**
  (`footprint_area_m2 × levels`): < 500 m² small, < 4,000 m² medium, ≥ 4,000 m² large → industrial
  use_class (no specific tag) → Warehouse → institutional use_class (no specific tag) → Courthouse →
  mixed-use dominant-tag routing → untagged `building=yes` → size-bucketed office default (LOW
  confidence) → `OpenUBEMUnknown` (LOW confidence, final fallback).
- **30-archetype vocabulary**: `openubem/data/openstudio_archetypes.json` (29 OpenStudio Building
  Types and Templates entries + the `OpenUBEMUnknown` sentinel). Confidence is always one of `HIGH /
  MEDIUM / LOW`, recorded alongside a `archetype_source` provenance token per row — never silent.
- **CBECS PBA crosswalk** (`openubem/data/cbecs_pba_map.json`): 25 of 30 archetypes map to a CBECS
  2018 PBA numeric code (several archetypes collapse onto the same code, e.g. all five office
  archetypes → PBA 2; both restaurant archetypes → PBA 15; both hotel archetypes → PBA 18; all three
  education archetypes → PBA 14). `MidriseApartment`, `HighriseApartment`, and all four data-center
  archetypes are explicitly excluded as "no clean CBECS 2018 PBA"; `OpenUBEMUnknown` is
  `"distribution_only"`.
- **Zero-fitted-parameters constraint applies here too**: any recommended threshold/tag/crosswalk
  change must be a published convention or documented precedent, not a tuned knob chosen to make a
  particular validation number look better.

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; prose after. Empty / "TBD" cells are failures.
2. Every method/value carries a **named, dated source** — a peer-reviewed UBEM paper (author, venue,
   year), tool documentation (URBANopt, CityBES, AutoBEM, UMI, CEA), the DOE/PNNL prototype building
   docs, the CBECS 2018 codebook, or the OpenStreetMap wiki tag taxonomy. Blogs/vendor pages last
   resort, labelled.
3. **Always compare against OpenUBEM's actual current value** (given inline in each prompt's
   tables) — don't just describe peer practice in the abstract, say explicitly whether it matches,
   is stricter, or is looser than what OpenUBEM does today.
4. **No fabricated precision.** If a value is your synthesis, say so. If unpublished, write
   **"GAP — needs manager decision"** + the closest defensible default and its source.
5. **Map onto OpenUBEM's exact archetype IDs and tag vocabulary**, not generic building-type names.
6. **Stay on topic per prompt** — I01 is the tag→use-class step only, I02 is the use-class→archetype
   step only, I03 is the archetype→CBECS step only. Don't re-litigate geometry/zoning (that's the
   `layoutMapping` set) or HVAC/service-load sizing (that's the `hvac-ServiceLoads` set).

---

*OpenUBEM — input classification deep-research set. Markdown only; binding specs remain
`docs/docs_main/`. 2026-06-30.*
