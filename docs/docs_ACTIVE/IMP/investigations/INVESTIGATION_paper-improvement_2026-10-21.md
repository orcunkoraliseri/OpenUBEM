# INVESTIGATION — how to make the OpenUBEM paper stronger, learning from the example papers — 2026-10-21

**Slug:** `paper-improvement` · **Date:** 2026-10-21 · **Author:** manager session · **Status:** first pass, for the owner to read.

**Inputs read:**

| Input | What it is |
|---|---|
| `docs/examples/main.pdf` | Song et al., *CityEL: a web-based platform to support city-scale building energy efficiency based on AutoBPS*, Sustainable Cities and Society 120 (2025) 106147. 21 pages. |
| `docs/examples/1-s2.0-S2210670726005834-main.pdf` | Li et al. (ORNL), *AutoBEM: a scalable framework for nationwide building energy simulation and retrofit evaluation in the United States*, Sustainable Cities and Society 149 (2026) 107700. 23 pages. |
| `docs/examples/alternatives.txt` | Links to tools worth comparing against (Torino 3D heat mapping, Infrared City, ODEN, city2graph, open GIS stack, a personal portfolio page). |
| `docs/resources/UK/Energy certificate data APIs – GOV.UK.pdf` | 2-page GOV.UK page on the new (beta) energy-certificate APIs: domestic EPCs, non-domestic EPCs + recommendations, and Display Energy Certificates (DECs) for public buildings. |
| `README.md` (repo root, updated 2026-10-21) | What OpenUBEM does and the numbers it publishes. |

**Important note on "our paper".** No OpenUBEM manuscript draft exists in the repository (searched `docs/` for manuscript, paper, journal, article; only graphical-abstract prompts were found under `docs/docs_DONE/GENERAL/graphicalAbstract/`). This investigation therefore treats "our paper" as **the OpenUBEM paper still to be written**, and says what it should contain to stand next to CityEL and AutoBEM. If a draft exists outside the repo, the two Gemini prompts in this folder can be pointed at it.

🔴 **Security note.** The UK PDF shows a personal **bearer token** for the GOV.UK energy-certificate API in plain text (page 1, "My Bearer token"). Do not upload this PDF to any web tool, do not commit it to git, and consider regenerating the token on the GOV.UK account page. The web-based Gemini prompt below deliberately leaves this PDF out.

---

## 1. What the two example papers do that reviewers will expect

| What they do | CityEL (2025) | AutoBEM (2026) |
|---|---|---|
| Clear statement of the gaps the paper closes | In the Introduction | Own section "2. Research gaps and innovations": 3 numbered gaps, then contributions (a)–(e) |
| Comparison with other UBEM tools | Short, in the Introduction | Own section "3. Related work" with a table of platforms (Table 2) |
| Validation explained in levels | Light: district EUIs placed inside a range from Shanghai measured reports (Fig. 10) | Strong: Table 1 sorts all validation into three levels — input attributes, single buildings, whole stock |
| Who should use the tool, and for what | Implicit | Explicit paragraph: intended users, core use cases, and what the outputs must NOT be used for |
| Retrofit / energy-saving measures | Yes, with energy savings, NPV and payback per neighbourhood (Figs. 8, 13, 15) | Yes, 151 measures, with sized equipment costs, local utility prices and payback (Tables 7–8, Figs. 13–15) |
| Hourly results and peaks | Yes, district hourly profile on the summer and winter solstice (Fig. 12), neighbourhood hourly (Fig. 14) | Peak and anthropogenic heat as extra outputs |
| Several spatial scales | Building → neighbourhood → district, from one run (aggregation method, Fig. 6) | Building → city → nation |
| Future climate | No | Yes, future typical weather years (fTMY) under several climate scenarios |
| Carbon | Yes | Yes, with grid-region emission factors and stated global warming potentials |
| Platform screenshots | Many (Figs. 2, 16–25) | Web viewer (Fig. 16) |
| Open data release | No | Yes, building-level inputs and outputs released (Model America v1.0) |
| Limitations | Short discussion | Own section "5.6 Limitations and interpretation of results", one paragraph per simplification |

## 2. Where OpenUBEM is already stronger — the paper should say this loudly

1. **Zero fitted parameters, and validated against measured energy in three U.S. cities.** 12 density cells, 8,160 buildings, archetype-level R² of 0.877 / 0.902 / 0.723 (NYC / LA / Austin). CityEL only places its building-type EUIs inside reference ranges from Shanghai reports (its Fig. 10); AutoBEM relies mainly on validation from earlier papers.
2. **Each building is its own multi-zone EnergyPlus model.** AutoBEM's own limitations section admits it uses one thermal zone per building and that multi-zone is "ongoing work". OpenUBEM already has resolution modes and, in Europe, one zone per dwelling.
3. **The same pipeline runs in ten districts in ten countries on four continents** (Spain, France, UK, Italy, Canada, Armenia, South Africa, Finland, Austria, Hungary), each with national construction data, its own weather station and its own licences. Neither example leaves its home country.
4. **Dwelling-level division with stated refusal reasons.** Buildings that cannot be divided by the rules are left out and listed, never hidden. This is a transparency point reviewers rarely see.
5. **Every published number names its population and its history.** The fleet figure's path (153.82 → 153.95 → 172.41 → 171.38 kWh/m²) is fully documented, with the reason for each change. This can become a short "reproducibility and audit trail" subsection.
6. **Outdoor comfort (UTCI) as an optional extra stage**, which neither example has (but it is not validated — say so).

## 3. Gaps, ranked by how much they would strengthen the paper

Effort: **S** = writing only, uses results we already have · **M** = a small new analysis on existing runs · **L** = new simulations or new data.

| # | Improvement | Learned from | Effort | Why it matters |
|---|---|---|---|---|
| 1 | **Write a "Research gaps and contributions" section** with 3 numbered gaps and a lettered contribution list, as AutoBEM does. Candidate gaps: (i) UBEM tools tune to measured data, so their accuracy is not transferable; (ii) most are single-country and single-zone; (iii) few report what they could not model. | AutoBEM §2 | S | Reviewers look for this first. |
| 2 | **Organise validation in three levels**, as AutoBEM Table 1: (a) inputs — classification exam, storey match on 99.91 % of buildings, input imputation checks; (b) single buildings — per-building comparison with NYC LL84 / LA EBEWE where available; (c) stock — city-overall and archetype R². Re-score level (c) on the adopted 171.38 figure first: the README says the city comparisons are still on the 2026-08-19 baseline. | AutoBEM §1.1, Table 1 | M | Turns our biggest strength into a clean, reviewable table. The re-score is a must before submission. |
| 3 | **Related-work table** of UBEM platforms: CityEL, AutoBEM, CityBES, UMI, CEA (City Energy Analyst), TEASER, SimStock, plus the tools in `alternatives.txt` (Infrared City, Torino 3D heat mapping, ODEN, city2graph). Columns: engine, zoning, scale, countries, validation against measured data, fitted parameters, open source, licence. | AutoBEM Table 2 | S | Places OpenUBEM; most columns favour us (zones, countries, no fitting). |
| 4 | **"Intended users and limits of use" paragraph.** Planners and researchers, neighbourhood screening; not for sizing equipment or single-building audits. | AutoBEM §1.2 | S | Pre-empts the "how accurate is one building?" objection. |
| 5 | **Limitations section, one paragraph per simplification:** archetype-based loads, the accepted under-prediction in NYC and Austin (no fitting by design), the 6 buildings that crash, EU results are heating only, Cape Town data licence. | AutoBEM §5.6 | S | We already have every fact; it is only writing. |
| 6 | **Retrofit results.** OpenUBEM has three active measures (lighting power, thermostat setback, airtightness); the envelope U-value measure is withdrawn because it equals the code baseline (`openubem/data/scenarios/measures.json:21-34`; correction from the Antigravity review, 2026-10-21). Show savings per archetype and per neighbourhood. Costs and payback need a cost source; keep them out if no open source exists, to stay within the no-fitting rule. | CityEL Figs. 8, 13, 15; AutoBEM §4.2.2 | M | Both examples centre on retrofits; a paper without them looks incomplete for this journal. |
| 7 | **Hourly and peak results.** We already write hourly outputs (README Step 3J / 5A). Add a district hourly profile for a winter and a summer day, and peak demand per district. | CityEL Figs. 12, 14 | M | Cheap to make, very visual, answers grid-planning readers. |
| 8 | **Several scales from one run**: building → neighbourhood (density cell) → city → fleet, as one figure. | CityEL §2.6, Fig. 6 | S | We have the data; it shows the tool is multi-scale. |
| 9 | **Viewer figures**: the 3D viewer and the floor-plan pages (`docs/docs_ACTIVE/europeanLocations/plans3D/`, `outputs_3D/`). One figure per district type is enough. | CityEL Figs. 16–25 | S | Shows the dwelling division visually — our most original method. |
| 10 | **[Out of scope, owner 2026-10-21: we cannot build it.]** ~~**UK cross-check with energy certificates (EPCs).**~~ For London St Dunstan's, compare our per-building heating demand with the EPC's modelled heating demand, and our inputs (floor area, wall type, heating system) with the certificate's. EPCs are already used as an input for London construction year (FINDING 256), so this is a **partial** check, not independent validation — say so. DECs give **measured** energy for public buildings and could support a non-domestic check. | `docs/resources/UK/` | M | A second-country check against a national register; strong for a European reader. |
| 11 | **Open data release** of per-building results and IDFs, where licences allow (not Cape Town; Armenia census data is "all rights reserved"). | AutoBEM contribution (e), MAv1 | M | Reproducibility; journals increasingly ask for it. Needs a licence review per site. |
| 12 | **Future weather** (fTMY or morphed EPWs) for one city as a demonstration. | AutoBEM §5.4 | L | Nice to have; only if time allows. |

## 4. Suggested paper outline

1. Introduction (problem, why tuning hides error, one-paragraph contributions)
2. Research gaps and contributions (item 1)
3. Related work, with the platform table (item 3)
4. Method: data acquisition → classification → enrichment and imputation → IDF generation and resolution modes → simulation → results and carbon; European dwelling-division path as its own subsection
5. Validation in three levels (item 2)
6. Results: U.S. fleet; ten international districts; retrofit scenarios (item 6); hourly and peak (item 7); multi-scale figure (item 8); viewer figures (item 9); UK certificate cross-check (item 10)
7. Discussion: intended users and limits (item 4); the accepted under-prediction; transparency of refusals
8. Limitations (item 5)
9. Conclusion and data availability (item 11)

## 5. What to decide before writing

- Which journal (both examples are in *Sustainable Cities and Society*; that fits).
- Whether the paper covers the U.S. validation and the ten international districts together, or as two papers. One paper is stronger on "transferability"; two papers are easier to review.
- Whether retrofit costs are in scope (needs an open cost source).

## 6. Prompts for a deeper review by Gemini

- Local (Gemini in Antigravity, reads the repository): `PROMPT_gemini-antigravity_paper-review_2026-10-21.md` in this folder.
- Web (Gemini in the browser, files uploaded by hand): `PROMPT_gemini-web_paper-review_2026-10-21.md` in this folder.

Both ask Gemini to write its answer as a new file / reply in a fixed format, so the result can be compared with this investigation.
