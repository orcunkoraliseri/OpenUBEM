# `EU-14` — Executor prompt: reopen Bologna — retry the one open lead, then impute under a tagged, disclosed rule

- **Arc**: European locations × Step 8.
- **Order**: independent of `EU-13`; touches `IT-BOL-GALVANI2` only.
- **Ruling**: `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-34_bologna_construction_year_relax_2026-08-28.md`
  — read it first, it is the spec for this task.
- **Background**: `docs/docs_ACTIVE/europeanLocations/debugs/EU11_Bologna_construction_year_investigation.md`
  — the closed **Fail** investigation this ruling extends. Read it before starting; do not repeat work
  packages A/B/C, they are already measured.
- **Executor**: external. **Paste everything below the rule into the tool.**
- **Date of prompt**: 2026-08-28.

---

## Task (paste from here)

You are reopening `IT-BOL-GALVANI2` (Bologna), currently at **0 of 1,220** residential buildings simulated,
in the OpenUBEM repository `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** —
never bare `python`. Git is handled externally: **never commit and never stage.**

### 1. Step one, mandatory: retry the INSPIRE Buildings WFS lead, live

The investigation's four `GetCapabilities` attempts all failed on **transport** grounds, not a confirmed
absence of the field:

- `servizigeo.regione.emilia-romagna.it` — DNS failure
- `geoportale.regione.emilia-romagna.it` — HTTP 404 (SPA, not a WFS endpoint)
- `wms.cartografia.agenziaentrate.gov.it` — HTTP 500 SOAP fault
- `inspire.agenziaentrate.gov.it` — DNS failure

Retry all four live, plus a general search for a current, working Italian INSPIRE Buildings (or Cadastre)
WFS/download endpoint covering Bologna. If a working endpoint is found:

1. Test it against the investigation's five acceptance criteria (stable building identifier, explicit
   construction year/period, open licence + reproducible access, unambiguous one-to-one join, coverage/
   exclusion counts reported before any IDF). Quote the exact fields you found.
2. **If it passes**, this is a genuine new open source — build the join, report coverage and exclusions, and
   simulate the matched subset with `geometry_outcome`/manifest tag `OBSERVED_YEAR_INSPIRE`, same standing as
   Madrid/Lyon/London's observed-year runs.
3. **If it fails or remains unreachable**, record exactly what you tried (URL, HTTP status or error, retrieval
   timestamp) and proceed to step 2.

### 2. Step two, only if step 1 fails: ISTAT census-section imputation, tagged not observed

Per `D-EU-34` §3.2:

- Join each Bologna residential footprint (`rifter_edif_pl`) to its ISTAT 2011 census section by centroid
  containment — a documented, reproducible spatial join, not a nearest-neighbour guess.
- Take that section's ISTAT construction-period band as the building's TABULA period. If a section's band
  straddles a TABULA period boundary, exclude that building and report it, per the investigation's own rule
  for period-vs-boundary ambiguity.
- Tag every such building's manifest row and side-car `dwelling_count_provenance`-style field
  `construction_period_provenance = "IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD"` —
  **never** `OBSERVED_YEAR`, and this string must appear anywhere the resulting EUI is quoted.
- Report, before any IDF is generated: total residential buildings, buildings with a centroid inside a
  mapped section, buildings excluded (unmapped section, boundary-straddling band, ambiguous join), and the
  final simulated count.
- The height source is unaffected and already solved (`c_a944ctc_edifici_pl.altezza_gr`, CC BY 4.0) — do not
  redo that work, just use it.

### 3. Run the campaign

Once buildings are typed (via step 1 and/or step 2), run them through the same `S2` real-footprint pipeline
already used for Madrid/Lyon/London (`PROMPT_EU-11_full_district_campaign_speed.md`'s machinery), against the
already-pinned `it_bologna_2013_2014_y*` `RULED_PINNED_EXCEPTION` EPW. Follow the same Speed compute rule:
`sbatch --array` fire-and-forget only, never the login node, EnergyPlus 23.1.0 Ubuntu20.

### 4. Bind into the viewer and side-cars

Once results exist, extend `IT-BOL-GALVANI2`'s viewer and layout side-cars exactly as `EU-11B`/`EU-12`
already did for the other three districts — Bologna's `results.csv` and `layouts/` currently do not exist
(correctly, since nothing was simulated); this task is what makes them exist for the first time. Follow the
same data-folder contract in `OpenUBEM_fundamentals.md` §8.5.

### 5. What must never happen

- No per-building year invented from height, storeys, typology, or a neighbouring building.
- No EPC/permit/renovation date reused as a construction year.
- No silent merge of Bologna's figures into the same pooled/compared number as the three observed-year
  districts without the provenance tag stated in the same sentence, in every document that cites it
  (`RESULTS_EU-11.md`, `STATE_european_locations_v2.md`, the viewer itself).

### 6. Deliverable

1. `RESULTS_EU-14.md` in `openubem/outputs/eu_evidence/EU-14/`: what step 1 found (pass/fail, with the exact
   endpoint evidence), and if step 2 ran, the coverage/exclusion census and the final simulated count and
   pooled EUI, explicitly labelled `IMPUTED`.
2. Bologna's `results.csv`, layout side-cars, manifest, and regenerated viewer (`openubem/outputs/3D/` +
   byte-identical mirror in `docs/docs_ACTIVE/europeanLocations/outputs_3D/`), if step 2 or step 1's pass
   branch produced simulations.
3. One appended row in `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`.
4. An update to `OpenUBEM_fundamentals.md` §8.5 if the data-folder contract gained a new provenance field.
5. Any error you hit and solve: one entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, house
   format, before you close the task.
6. If step 1 also fails and step 2's join yields zero usable buildings (e.g. no ISTAT section coverage over
   Galvani), stop and report that measurement — do not invent a fallback beyond what `D-EU-34` authorises.

### 7. Do not

- Do not edit root `main.py`, any OVERVIEW or DESIGN doc, `previous/MVP_european_locations.md`, or
  `previous/WALKTHROUGH_european_locations.md`; do not annotate MVP Table 9.7.
- Do not rewrite or delete the closed investigation doc
  (`debugs/EU11_Bologna_construction_year_investigation.md`) — its Fail disposition stands; this task layers
  a new ruling on top, per `D-EU-34` §3.3.
- Do not put `.py` files under `docs/`. All `.png` and figure outputs go to `openubem/outputs/`, flat.
- Do not use ISTAT bands, height, or any other proxy as a stand-in for an *observed* year — the
  `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` tag must never be dropped once assigned.
