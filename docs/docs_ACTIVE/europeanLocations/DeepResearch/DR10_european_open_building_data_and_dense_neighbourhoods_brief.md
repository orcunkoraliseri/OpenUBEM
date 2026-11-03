# DR10 — Brief: European Open Building Data and Dense Residential Neighbourhood Candidates

- **Serves decision**: D-EU-10 (data half) in [`../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md); feeds MVP §9.7.2 gates `NS-01`–`NS-10` and §10.4 four-panel audit
- **Report to be saved as**: `DR10_european_open_building_data_and_dense_neighbourhoods.md`
- **Date of brief**: 2026-08-23

---

## Task (paste everything below this line into the deep-research tool)

You are producing a publication-grade research report for an urban building energy modelling project that must select **one real, contiguous, dense residential neighbourhood** (500–600 residential buildings after filtering; optionally up to 1,000) in each of four European study cities, and must audit that neighbourhood on four building-level attributes **before** any simulation: (a) construction period, (b) availability of an energy performance certificate (EPC) or national equivalent, (c) building function / residential typology (single-family, terraced, multi-family, apartment block), (d) construction material or construction set.

### Context you must take as given

- Footprint geometry comes from OpenStreetMap (the project's existing acquisition path) and may be enriched by other open sources; the audit attributes must be **joinable to a building footprint** (by geometry, by cadastral reference, or by address).
- Study cities, working defaults: **Madrid** (Spain), **London** (England), **Bologna** (Italy) — these may be replaced by the weather report DR08 — and **one French city** to be proposed by you with reasons (candidates: Lyon, Grenoble, Nantes, Paris intra-muros *arrondissement*), chosen for open-data completeness rather than size.
- The density metric is ruled: **residential buildings per km² of the candidate boundary after a residential filter**, with a dwelling proxy (`building:levels × footprint area`) as tie-breaker. Candidate boundaries must be **open administrative sub-units** (Madrid *barrios*; London *wards* or LSOAs; Bologna *quartieri* / *zone* / *aree statistiche*; France *IRIS*).
- The project will not accept a "dispersed citywide sample"; the selected unit is one natural boundary, not trimmed to hit a count.

### Questions to answer

**A. Building-level open datasets per city.** For each city, list every open dataset that supplies at least one of attributes (a)–(d) at building level, with: publisher, URL, licence (name + whether it permits publication of derived maps and counts), building identifier (cadastral reference, UPRN, *codice ecografico*, *identifiant BDNB*, address), fields for each attribute, last update, and the **join route to an OSM footprint** (spatial join, reference key, address matching) with its known failure modes. Expected candidates to check (not exhaustive): Spain — *Sede Electrónica del Catastro* INSPIRE buildings (construction year, use, units), Madrid *Open Data* EPC/CEE registry (Comunidad de Madrid *Registro de certificados de eficiencia energética*); England — *Energy Performance of Buildings Register* open data (EPC by UPRN; `CONSTRUCTION_AGE_BAND`, `PROPERTY_TYPE`, `BUILT_FORM`, `WALLS_DESCRIPTION`), Ordnance Survey Open UPRN / Open Map Local, VOA data; Italy — *Agenzia delle Entrate* cadastre (limited openness), Emilia-Romagna regional APE register (*SACE*), Bologna *Open Data* (edifici, *epoca di costruzione*), ISTAT census sections (*sezioni di censimento* with *epoca di costruzione* aggregates); France — ADEME DPE open database, BDNB (CSTB), *Fichiers fonciers*, BD TOPO, IGN *Bâtiments* with `DATE_APP`.

**B. Attribute coverage and missingness.** For each dataset and attribute, what fraction of residential buildings is expected to carry a non-missing value (cite the publisher's documentation or a published study using the dataset), and how missingness is encoded. The project requires missingness to be an explicit category in every audit panel.

**C. Typology crosswalk.** How each dataset's categories map onto the TABULA classes `SFH` / `TH` / `MFH` / `AB` and onto the TABULA construction-year classes (Spain `ES.01`–`ES.06`, GB `GB.01`–`GB.08`, Italy `IT.01`–`IT.08`; France from DR09). Flag every one-to-many mapping (e.g. EPC `CONSTRUCTION_AGE_BAND` "1930–1949" straddles `GB.02`/`GB.03`).

**D. Candidate neighbourhoods.** For each city, produce a first ranked list of at least five candidate administrative sub-units under the ruled density metric, using **published** residential building counts or dwelling counts per unit and unit areas (census or municipal statistics), with the source for every number. State which candidates plausibly contain 500–600 residential buildings. Do not pick the final unit; the project pre-registers the rule and makes the selection with its own computed counts.

**E. Boundaries.** Where the open boundary polygons for those sub-units are published (format, CRS, licence, URL).

### Hard rules

1. No invented counts, fractions, field names or URLs. Every figure carries its source and retrieval date or `UNVERIFIED`.
2. Distinguish "dataset exists" from "dataset is open under a licence that permits publishing derived counts and maps".
3. Do not recommend scraping a service whose terms forbid it; say so instead.
4. Separate facts, inferences and recommendations with explicit labels.

### Output format

```
# DR10: European Open Building Data and Dense Residential Neighbourhood Candidates
## 1. Executive Summary                 (one recommended primary dataset per attribute per city; the French city proposal)
## 2. Dataset Inventory per City        (table per city: dataset | attributes | identifier | licence | join route | update)
## 3. Coverage and Missingness          (table: city | attribute | expected non-missing share | encoding | source)
## 4. Typology and Period Crosswalks    (tables; one-to-many cases flagged)
## 5. Candidate Neighbourhoods          (table per city: unit | area km² | residential buildings or dwellings | density | source)
## 6. Open Boundary Sources
## 7. Synthesis for the OpenUBEM European Locations Arc   (what to download first; what cannot be obtained openly)
## References
```

### Acceptance test the project will apply

Accepted only if every dataset row carries a licence verdict on derived-publication, every candidate-neighbourhood count carries a source, and every crosswalk flags its one-to-many cases.
