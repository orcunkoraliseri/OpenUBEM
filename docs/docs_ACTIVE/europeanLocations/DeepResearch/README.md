# Deep Research Dossier II: Weather, Licences, Open Building Data, and TABULA-to-EnergyPlus Translation for the European Locations Arc

This dossier continues the parent Step 8 dossier (`GSSCanada-main/4J_docs_occ/Step8_docs/IMP_step8/DeepResearch/`, reports DR01–DR07) with the research the OpenUBEM European-locations arc still needs before its owed decisions can be closed. The parent dossier covers layout generation, zoning resolution, and the European/national standards framework; **it does not cover the four data-acquisition questions that the 2026-08-23 decision record left open** ([`../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md)).

```
docs/docs_ACTIVE/europeanLocations/DeepResearch/
├── README.md                                                   <- This index
├── DR08_actual_year_weather_sources_and_licences_brief.md      <- Brief (prompt) for the AMY weather question  (D-EU-05)
├── DR09_tabula_licence_and_france_registry_brief.md            <- Brief for the TABULA licence + France subset  (D-EU-08, D-EU-11)
├── DR10_european_open_building_data_and_dense_neighbourhoods_brief.md <- Brief for EPC/cadastre sources + N1 candidates (D-EU-10)
└── DR11_tabula_to_dynamic_simulation_translation_brief.md      <- Brief validating the desk rulings D-EU-01/02/03/07
```

## How this dossier works (two files per topic)

1. **`DRxx_<topic>_brief.md`** — written by the director. A self-contained research brief: context the external model cannot know, the exact questions, the sources it must consult, the output format, and the acceptance test the returned report must pass. It is pasted into a deep-research LLM (the user's choice of tool) as the task.
2. **`DRxx_<topic>.md`** — the report the deep-research run returns, saved next to its brief **unchanged**, then source-verified by the director before any number from it enters the MVP. The report follows the structure of the parent reports (executive summary → numbered sections with tables → synthesis for UBEM → references with URLs and retrieval dates).

A report is **not** an authority by itself. The standing citation rule of this arc applies (director prompt §18.2): a figure becomes usable only when its source file/URL and location are named and the director has opened that source. A report that cannot name a source for a number must say `UNVERIFIED`, and the director rejects any report that invents one.

## Index of Briefs

### 8. [`DR08: Actual-Year Weather Sources and Licences for the Three Fold Windows`](DR08_actual_year_weather_sources_and_licences_brief.md)
* **Closes**: D-EU-05 items 2–3 (source with a publication-compatible licence; station per TABULA region). Windows are already ruled (`es` 2009–2010, `uk` 2014–2015, `it` 2013–2014).
* **Questions**: which AMY sources exist for Madrid/London/Bologna (or better stations) for those years; what each licence permits for *published derived results*; EPW conversion routes and their known defects; how the national time-use surveys' regional distribution should steer the station choice.

### 9. [`DR09: TABULA/EPISCOPE Licence Terms and the France Residential Typology Subset`](DR09_tabula_licence_and_france_registry_brief.md)
* **Closes**: D-EU-08 (licence text verbatim, with URL and date) and D-EU-11 (France physical registry: which TABULA FR rows exist, their construction-period bands, climate tags, and how RE2020 / DPE sources map onto them).

### 10. [`DR10: European Open Building Data and Dense Residential Neighbourhood Candidates`](DR10_european_open_building_data_and_dense_neighbourhoods_brief.md)
* **Closes**: D-EU-10 data half — which open datasets provide construction period, EPC availability, building function and construction material at building level in Madrid, London, Bologna and one French city; which administrative boundaries are open; a first ranked candidate list per city under the ruled density metric.

### 11. [`DR11: Translating TABULA Monthly-Balance Parameters into Dynamic Simulation`](DR11_tabula_to_dynamic_simulation_translation_brief.md)
* **Validates**: the desk rulings D-EU-01 (box from areas + `n_Apartment`), D-EU-02 (mass-less U + explicit `c_m`; ΔU surcharge; `b`-factors as other-side coefficients), D-EU-03 (`n_air_use + n_air_infiltration`), D-EU-07 (`F_red_temp` as transfer-coefficient multiplier; all-convective gain; no cooling). Asks the literature (TEASER, TABULA/EPISCOPE calculation documentation, EN ISO 13790/52016 annexes, published TABULA→EnergyPlus/Modelica studies) whether each realisation is standard, whether a better-founded one exists, and what error each is known to introduce.

## Associated Arc Documents
* **Decision record these briefs serve**: [`../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md)
* **Extracted TABULA columns (evidence)**: [`../debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv`](../debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv)
* **MVP specification**: [`../MVP_european_locations.md`](../MVP_european_locations.md) (§11 source alignment; §11.12 rulings)
* **Walkthrough**: [`../WALKTHROUGH_european_locations.md`](../WALKTHROUGH_european_locations.md) (§12 executor contract)
* **Director prompt**: [`../prompts/DIRECTOR_PROMPT_european_locations.md`](../prompts/DIRECTOR_PROMPT_european_locations.md)
* **Parent dossier (DR01–DR07)**: `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\IMP_step8\DeepResearch\README.md`

## Acceptance Record (2026-08-23, director source-verification pass)

The four reports were returned 2026-08-23 and audited against each brief's acceptance test the same day. Verdicts:

| Report | Acceptance test | Verdict | Caveats recorded |
|---|---|---|---|
| `DR08` | Licence matrix has verbatim clause + URL + date per row; per-fold source tables; conversion defects table; station rule + per-fold recommendation | **ACCEPTED** | The quoted Copernicus licence PDF URL returns 404 (checked live 2026-08-23); the current CDS ERA5 page states plain **CC-BY** — verdict (publication-compatible, redistributable with attribution) unchanged, but the executor must copy the licence text actually served at download time into `weather_registry.json`, not DR08's quotation. Meteonorm/White Box clause wordings not independently re-checked (commercial routes not used). |
| `DR09` | Part A: verbatim licence clause with URL/date + use-by-use verdict; Part B: France rows enumerated from the pinned workbook | **ACCEPTED** | Part A key clause **independently re-verified live** at `episcope.eu/communication/download/` on 2026-08-23 by the director (verbatim match: "intended and desired" + mandatory `IEE Projects TABULA + EPISCOPE (www.episcope.eu)` attribution). Part B counts (40 `FR.N` + 10 `FR.OPHM`) must be re-derived by the executor from the pinned workbook in slice X-08 before `tabula_archetypes_fr.json` is written — the report is the map, the workbook is the authority. |
| `DR10` | Every dataset row carries a licence verdict on derived publication; every candidate count carries a source; crosswalks flag one-to-many cases | **ACCEPTED** | All §5 building counts are published-statistics **estimates** and are candidates only; the final unit is selected by the project's own computed counts under `NS-03`/`NS-05` — no DR10 count may appear as a project number. GB age-band straddle shares (63 %/75 %/88 %/89 %/71 %/71 %) are duration-derived heuristics, usable only as the deterministic tie-break rule they parameterise, never as measured stock shares. |
| `DR11` | Every §1 verdict backed by a §3 citation; clause-level `F_red` answer; concrete fixtures for R3/R5/R7 | **ACCEPTED** | No desk ruling overturned (6 × Standard, 4 × Acceptable-with-caveat). The three §4 fixtures (R3 time constant, R5 flux, R7 scaling) are adopted into slice X-04 with their numeric pass criteria. The quoted bias magnitudes (e.g. +8–18 % peak from mass-less envelope) are literature-order estimates for the dossier's caveat text, not project measurements. |

Closures these acceptances produce are written in `../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md` (closure addendum), MVP §11.13, walkthrough §12.5–12.6, and the director prompt head box. Remaining blocked item: **D-EU-09 (Step 7 chaining rule) only**, and it blocks only `f>0` cells.
