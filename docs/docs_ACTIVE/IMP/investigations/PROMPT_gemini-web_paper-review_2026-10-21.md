# PROMPT — Gemini on the web (no repository access) — OpenUBEM paper review — 2026-10-21

**Before pasting:** upload these three files to the Gemini chat:

1. `docs/examples/main.pdf` (CityEL)
2. `docs/examples/1-s2.0-S2210670726005834-main.pdf` (AutoBEM)
3. `docs/docs_ACTIVE/IMP/INVESTIGATION_paper-improvement_2026-10-21.md` (our first-pass review)

🔴 **Do NOT upload** `docs/resources/UK/Energy certificate data APIs – GOV.UK.pdf`: it contains a personal access token. The prompt below describes that page instead.

Use Gemini's Deep Research mode if available. Copy everything below the line.

---

You are a senior reviewer for the journal *Sustainable Cities and Society* and an expert in urban building energy modelling (UBEM). We are preparing a journal paper on **OpenUBEM**, our open-source UBEM platform. I have uploaded two published example papers (CityEL, 2025; AutoBEM, 2026) and our own first-pass review of how to improve our paper. Tell us how to make our paper as strong as, or stronger than, these examples.

## What OpenUBEM is (facts — use only these about our tool; do not invent others)

- Input: a neighbourhood (address, coordinate, bounding box or OpenStreetMap export). Output: annual energy use and carbon for every building.
- Pipeline: data acquisition (OpenStreetMap footprints, heights) → building classification into DOE/ASHRAE-style archetypes → climate zone and weather → physics enrichment (envelope, loads, schedules) → input imputation with recorded provenance → one EnergyPlus model per building, multi-zone, with several resolution modes → parallel simulation on a computer cluster → results, carbon and validation. Optional extra stage: outdoor thermal comfort (UTCI), not validated against measurement.
- **Zero fitted parameters**: nothing is tuned to measured energy.
- **U.S. validation**: 12 density cells (centre, urban, suburban, rural) in New York City, Los Angeles and Austin, 8,160 buildings. Adopted fleet figure: **171.38 kWh/m²** pooled over **8,139 buildings**, carbon **1,146,454 t CO₂e**. City-overall versus measured benchmarks (NYC LL84, LA EBEWE, CBECS proxy): NYC −31.3 %, LA −3.6 %, Austin −30.5 %; archetype-level R² 0.877 / 0.902 / 0.723 (these comparisons were scored on an earlier baseline and still need to be re-scored on the adopted figure). The under-prediction is accepted rather than fitted away.
- **Ten international residential districts**, heating-only results per m², each with its own national construction data (TABULA/EPISCOPE, donor countries where missing), its own weather station (TMYx 2009–2023, Vienna a real year 2008) and its own data licences: Madrid 68.8, Lyon 57.8, London 68.3, Bologna 58.2, Montréal 140.9, Yerevan 48.5, Cape Town 54.2, Helsinki 96.4, Vienna 77.6, Budapest 63.4 kWh/m².
- In these districts **each building is divided into its dwellings** (one thermal zone per flat) by a ruled grid that handles L, U/T and multi-wing shapes. Buildings that cannot be divided by the rules are left out and listed with their reason, never hidden.
- Every published number names its population; superseded numbers are marked and kept with their history.
- Has a 3D web viewer and floor-plan pages per district; three active retrofit measures exist (lighting power, thermostat setback, airtightness; an envelope U-value measure was withdrawn because it equalled the code baseline) but no cost model; hourly outputs are written.
- The UK government offers APIs for energy certificates: domestic EPCs, non-domestic EPCs with recommendation reports, and Display Energy Certificates (DECs, measured energy of public buildings). OpenUBEM already uses EPC construction year as an input for the London district.

## Tasks

1. **Example papers.** For each example: section structure, stated contributions, how it validates, key figures and tables, and the three things reviewers would most likely praise.
2. **Check our review.** For each row of the table in §3 of our uploaded investigation: agree / disagree / change, one sentence why.
3. **What we missed.** Up to 8 further improvements, each with: which example or which other paper it comes from, effort (S = writing only, M = small analysis on existing results, L = new simulations or data).
4. **Literature.** Search the recent UBEM literature (2019–2026) and list 10–15 papers we should cite, especially: UBEM validation against measured data, multi-country or transferable UBEM, dwelling-level or multi-zone UBEM, open-source UBEM platforms (CityBES, UMI, City Energy Analyst, TEASER, SimStock, AutoBEM, CityEL). For each: full reference, DOI, one sentence on why it matters for us. **Only list papers you can verify with a DOI or publisher page; say "unverified" otherwise.**
5. **Related-work table.** Draft a comparison of UBEM platforms. Columns: simulation engine, zoning (single / multi-zone / per dwelling), scale, countries covered, validated against measured energy, fitted or calibrated parameters, open source. Mark unsure cells with "?".
6. **UK certificate data.** What a comparison with EPCs and DECs could and could not prove for the London district, given that EPC construction year is already one of our inputs.
7. **Reviewer attack.** The five hardest questions a reviewer would ask about our paper, and the best honest answer to each from the facts above.
8. **Draft text.** (a) "Research gaps and contributions" section, ≤ 350 words; (b) "Intended users and limits of use" paragraph, ≤ 150 words.

## Output format

Reply in plain English, short sentences, with exactly these headings:

```
# RESULT — Gemini (web) paper review — 2026-10-21
## 1. Example papers
## 2. Check of our review (row by row)
## 3. What we missed
## 4. Literature to cite
## 5. Related-work table (draft)
## 6. UK certificate data — what it can and cannot prove
## 7. Hardest reviewer questions and answers
## 8. Draft text
## 9. Open questions for us (max 5)
```

Do not write the full paper. Do not invent numbers about OpenUBEM beyond the facts given.
