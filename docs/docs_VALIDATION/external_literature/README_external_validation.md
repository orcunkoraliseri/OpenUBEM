# External Validation — Deep Research Prompts & Results

**Goal.** Compare OpenUBEM's modeled EUI against **real measured building energy data** for the three
modeled cities (NYC / LA / Austin) plus published UBEM accuracy norms. So far the model has only been
compared against reference *distributions* (CBECS-2018 means), reference *models* (DOE/PNNL prototype
round-trip), and literature *error bands*. These prompts close that gap with measured ground truth.

**Tool.** Prompts are written to be run in **Google Antigravity** (deep web research). Run one prompt
file at a time; each ends with an instruction to save its answer as a `RESULT_*.md` back into this
same folder.

## Prompts (run these)

| File | Fetches | Priority |
|---|---|---|
| `PROMPT_1_nyc_ll84_measured.md` | NYC LL84/133 measured site EUI by property type (CZ 4A) | **High** — best ground truth |
| `PROMPT_2_la_california_measured.md` | LA EBEWE / CA AB 802 measured site EUI by type (CZ 3B) | High |
| `PROMPT_3_austin_texas_measured.md` | Austin ECAD / Texas measured site EUI by type (CZ 2A) | High |
| `PROMPT_4_published_ubem_studies.md` | What comparable UBEMs reported & validated against | Medium — interpretive frame |
| `PROMPT_5_per_archetype_benchmarks.md` | National per-archetype reference site EUI (ENERGY STAR / CBECS / PNNL) | Medium |
| `PROMPT_6_measured_enduse_splits.md` | Measured end-use splits to check the service-load reconstruction | Medium |

**Suggested order:** run Prompt 1 first as a pilot — if the NYC matching works, the LA/Austin
prompts will too. Prompts 4–6 are lower-risk literature pulls; run anytime.

## Results (Antigravity writes these back here)

`RESULT_1_nyc_ll84_measured.md` · `RESULT_2_la_california_measured.md` ·
`RESULT_3_austin_texas_measured.md` · `RESULT_4_published_ubem_studies.md` ·
`RESULT_5_per_archetype_benchmarks.md` · `RESULT_6_measured_enduse_splits.md`

## Comparability conventions baked into every prompt

- **Site** EUI (not source), reported in **both** kBtu/ft²·yr and kWh/m²·yr (1 kBtu/ft²·yr = 3.15459 kWh/m²·yr).
- **Medians + p25/p75 quartiles**, not just means — distributions are the unit of comparison.
- Broken out by OpenUBEM's **archetype vocabulary** and the three cities' **climate zones** (4A/3B/2A).
- **Citations + URLs/DOIs + access dates** required; gaps flagged, never invented.

## Next step (this Claude session, once RESULTs are back)

Write `docs/validations/overAll/V17_external_measured_validation.md`: harmonize the measured
benchmarks to kWh/m²·yr and OpenUBEM archetypes, score the modeled per-archetype/per-city
distributions (from `r7_service_loads.csv` and the 12-cell `05_results`) against the measured
medians/quartiles — distribution overlap, **report-only** (per V-R5-5), no resim — framed by the
published-UBEM accuracy context from Prompt 4.

*Manager-authored. No resimulation, no DESIGN change, report-only validation. 2026-06-17.*
