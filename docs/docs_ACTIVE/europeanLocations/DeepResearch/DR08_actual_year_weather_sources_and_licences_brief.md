# DR08 — Brief: Actual-Year Weather Sources and Licences for the Three Fold Windows

- **Serves decision**: D-EU-05 (weather), items 2 and 3, in [`../debugs/docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DECISIONS_parent-open-items-2026-08-23.md)
- **Report to be saved as**: `DR08_actual_year_weather_sources_and_licences.md` (same folder, unchanged on receipt)
- **Date of brief**: 2026-08-23

---

## Task (paste everything below this line into the deep-research tool)

You are producing a publication-grade research report for a building-energy-simulation project that must run EnergyPlus on European residential archetypes using **actual meteorological years (AMY), not typical years**, aligned to the fieldwork windows of three national time-use surveys. The project's own decision has already fixed the windows; your job is the sources, the licences, and the station choice.

### Context you must take as given

- Three populations, each with a fixed weather window ruled on 2026-08-21 by the project author: **Spain `es` 2009–2010**, **England/UK `uk` 2014–2015**, **Italy `it` 2013–2014**. The exact twelve months inside each window will be pinned by the project from its own diary dates; you work with the two calendar years.
- TABULA's climate tags for the building stocks are `ES.ME` (Spain, Mediterranean region tag), `GB.Temperate` with every archetype coded `GB.ENG` (England only), `IT.MidClim` (Italy, mid-climate). They are region tags, not coordinates.
- Working default stations from an earlier, unverified project document: **Madrid, London, Bologna**. Treat them as candidates to confirm or replace, not as facts.
- The simulation engine is EnergyPlus 23.1; the weather file format is EPW; the project must be able to **publish derived results** (annual/monthly/hourly energy figures) in a journal paper. A file that downloads but whose licence forbids publication of derived results is **not acceptable**.
- A typical-year file (TMY, TMYx, IWEC, TRY) is excluded by the project ruling except for engine smoke tests.

### Questions to answer

**A. Sources.** For each of the three cities (and for any better-justified station you propose), list every source that can supply hourly AMY data for the window: ERA5 / ERA5-Land (Copernicus C3S), national meteorological services (AEMET, Met Office MIDAS, Italian regional ARPA networks / ISPRA SCIA), commercial AMY vendors (e.g. Meteonorm, Weather Analytics/White Box, Shiny Weather Data, Climate.OneBuilding AMY where present), and academic reanalysis-to-EPW products. For each: variables available (dry-bulb, dew-point/RH, pressure, wind, global/direct/diffuse radiation, cloud cover), temporal resolution, spatial resolution, and known gaps for those years.

**B. Licences.** For each source, quote the licence **verbatim** (name, URL, retrieval date) and state explicitly whether it permits (i) academic use, (ii) publication of derived results, (iii) redistribution of the converted EPW file. Distinguish clearly between "free to download" and "free to publish derived results". Where the answer is uncertain, say `UNVERIFIED` and name the clause that makes it uncertain.

**C. Conversion to EPW.** Document the established routes from each source to EPW (e.g. ERA5 → EPW converters, `pvlib`/`ladybug` tooling, the ECMWF radiation decomposition problem, time-zone and DST handling, leap-day handling for 2012/2016 if a window touches them — it does not here, but state the rule). List the known defects of each route (solar decomposition bias, precipitation absence, ground temperatures) with references.

**D. Station choice.** Using public information on the regional distribution of each national time-use survey (Spain INE *Encuesta de Empleo del Tiempo 2009–2010*; UK *Time Use Survey 2014–2015* (CTUR/NatCen); Italy ISTAT *Uso del tempo 2013–2014*) and on where the TABULA region tags apply, recommend one station per fold with a stated rule (e.g. most populous city in the TABULA region; or population-weighted centroid). State whether Bologna is a defensible choice for `IT.MidClim` versus Rome or Milan, with reasons, and whether London Heathrow vs another England station matters for the `GB.ENG` stock.

**E. Validation of an AMY file.** Give a checklist to validate a converted EPW before use: header `LOCATION` fields, record count (8,760 / 8,784), missing-value flags, physical range checks, comparison of monthly means against a published climatology for that station and year.

### Sources you must consult (and cite with URL + retrieval date)

Copernicus C3S licence page and ERA5 documentation; EnergyPlus Auxiliary Programs documentation on the EPW format; at least two peer-reviewed papers on reanalysis-to-EPW conversion for building simulation; the official methodology documents of the three time-use surveys; the TABULA/EPISCOPE country pages for ES, GB, IT.

### Hard rules

1. Do not invent a licence term, a data-availability claim, or a station coordinate. Every such statement carries a URL and retrieval date or the tag `UNVERIFIED`.
2. Do not recommend a typical-year file as a substitute.
3. Do not quote energy results from any study as if they applied to this project.
4. Separate facts, inferences and recommendations with explicit labels.

### Output format (mirror the parent dossier's reports)

```
# DR08: Actual-Year Weather Sources and Licences for the Three Fold Windows
## 1. Executive Summary            (≤ 300 words; the one recommended source + station per fold, and the licence verdict)
## 2. Sources per Fold              (one table per fold: source | variables | resolution | years covered | gaps)
## 3. Licence Matrix                (table: source | licence name | verbatim clause on derived results | verdict | URL | date)
## 4. Conversion Routes and Known Defects
## 5. Station Choice per Fold       (rule, candidates, recommendation, what would change it)
## 6. Validation Checklist for a Converted EPW
## 7. Synthesis for the OpenUBEM European Locations Arc   (what the project should do first, second, third)
## References                       (numbered; URL; retrieval date)
```

### Acceptance test the project will apply to your report

The report is accepted only if: every licence verdict quotes a clause; at least one source per fold is marked "publication-compatible" or the report states that none is; the station recommendation names its rule; and no typical-year file is proposed as the campaign file.
