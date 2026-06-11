# PROVENANCE — openubem/data/carbon/egrid_2022.json

## Source
- Dataset: EPA eGRID 2022 (Emissions & Generation Resource Integrated Database)
- URL: https://www.epa.gov/system/files/documents/2024-01/egrid2022_data.xlsx
- Retrieval date: 2026-06-10
- SHA-256 of downloaded xlsx: c73fdc561aa402d0f6ed3cc35e5d961bee6af6e003c9c035b40f757f8480b76b
- Excel sheet: ST22 (state-level summary)
- Short-code header row (row 1): PSTATABB = 2-letter USPS abbreviation; STC2ERTA = state annual CO₂e total output emission rate (lb/MWh)
- Territories excluded: ['AS', 'GU', 'MP', 'PR', 'VI'] (outside OpenUBEM continental-US scope)
- Note: subregion not available in ST22 sheet; set to "" in output (informational field only per PLAN P2)

## Conversion
factor_kgco2_kwh = STC2ERTA_lb_mwh × (0.453592 lb/kg) ÷ 1000 (MWh/kWh)

## Simplification (documented per PLAN P2)
The factor used in OpenUBEM is the **state-level** total output CO₂e rate, not the
subregion rate. EPA publishes both; the state-level rate is used here because the `state`
key is the foreign key OpenUBEM has available from Step 2.1 (county→state join). The
`subregion` field is retained as an informational annotation for audit; it is not used
in any computation.

## Coverage
51 entries: 50 US states + DC (PR, VI, etc. excluded — outside OpenUBEM's continental-US
scope, and not present in the ST22 sheet alongside state totals for the 50+DC).

## MA factor
MA: subregion = ,
    factor = 0.389735 kg CO₂e/kWh

## Downstream use (DESIGN §3E, PLAN F7)
- Heating GWP: × 0.181 kg CO₂e/kWh (natural gas, Iseri et al. 2025)
- Cooling / Lighting / Equipment GWP: × egrid_2022[state]['factor_kgco2_kwh']
- Convention: load_referenced_v1 (no η or COP applied — see DESIGN §3E)
