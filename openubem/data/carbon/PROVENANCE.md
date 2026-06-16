# PROVENANCE — openubem/data/carbon/egrid_2022.json + egrid_2022_subregions.json

## Source
- Dataset: EPA eGRID 2022 (Emissions & Generation Resource Integrated Database)
- URL: https://www.epa.gov/system/files/documents/2024-01/egrid2022_data.xlsx
- Retrieval date: 2026-06-10
- SHA-256 of downloaded xlsx: c73fdc561aa402d0f6ed3cc35e5d961bee6af6e003c9c035b40f757f8480b76b

## State-level factors (egrid_2022.json)
- Excel sheet: ST22 (state-level summary)
- Short-code header row (row 1): PSTATABB = 2-letter USPS abbreviation; STC2ERTA = state annual CO₂e total output emission rate (lb/MWh)
- Territories excluded: ['AS', 'GU', 'MP', 'PR', 'VI'] (outside OpenUBEM continental-US scope)
- factor_kgco2_kwh = STC2ERTA_lb_mwh × (0.453592 lb/kg) ÷ 1000 (MWh/kWh)
- 51 entries: 50 US states + DC
- MA factor: 0.389735 kg CO₂e/kWh
- NY subregion tag: NYCW (informational, B2 decision 2026-06-15)
- CA subregion tag: CAMX (informational, B2 decision 2026-06-15)
- TX subregion tag: ERCT (informational, B2 decision 2026-06-15)

## Subregion factors (egrid_2022_subregions.json) — R6-2 / B2 decision 2026-06-15
- Excel sheet: SRL22 (subregion summary)
- Short-code header row (row 1): SUBRGN = eGRID subregion acronym; SRC2ERTA = subregion annual CO₂e total output emission rate (lb/MWh)
- factor_kgco2_kwh = SRC2ERTA_lb_mwh × (0.453592 lb/kg) ÷ 1000 (MWh/kWh)
- 27 subregions extracted
- City→subregion mapping for R6-2: NYC→NYCW (0.402146 kg CO₂e/kWh), LA→CAMX (0.226469 kg CO₂e/kWh), Austin→ERCT (0.351215 kg CO₂e/kWh)

## B2 decision (PLAN R6 §4.3, manager ruling 2026-06-15)
GWP recompute uses grid-subregion factors (from egrid_2022_subregions.json) instead of
state-level factors for the 3 R6 cities. Heating GWP (natural gas) is unchanged. Only
cooling + lighting + equipment electricity GWP is rescaled by ratio = f_subregion / f_state.
This is post-processing of energy already in 05_results.csv — no resimulation.
R5 shipped state-level GWP remains the immutable baseline; subregion GWP presented as R6 refinement.

## Downstream use (DESIGN §3E, PLAN F7)
- Heating GWP: × 0.181 kg CO₂e/kWh (natural gas, Iseri et al. 2025)
- Cooling / Lighting / Equipment GWP: × egrid_2022[state]['factor_kgco2_kwh'] (runtime core)
- R6-2 post-processing only: × egrid_2022_subregions[acronym]['factor_kgco2_kwh'] applied in r6_rescore_cells.py
- Convention: load_referenced_v1 (no η or COP applied — see DESIGN §3E)
