# Service-Loads Reconstruction — Coefficient Reference (Table 4)

**Source:** `docs/deepResearch/Simplified UBEM Load Estimation.pdf`, *Table 4 — Consolidated
End-Use Energy Fractions by Archetype (%)* (PDF pages 9–11).
**Transcribed by:** manager session (Opus), 2026-06-17, by rendering the image-only PDF
tables to PNG and reading them visually. The numeric cells are **rasterised images**, not a
text layer (confirmed: `fitz.get_text()` returns empty cells), which is why prior `.txt`/`.md`
extractions showed blanks.
**Verification:** every archetype row below sums to **exactly 100.0%** (sum-check passed).

This file is the **source-of-truth** for the machine-readable
`openubem/data/service_loads/enduse_fractions_table4.json`. If the JSON and this table ever
disagree, this table wins (re-derive the JSON from here).

---

## Table 4 — End-use energy fractions by archetype (% of whole-building site energy)

Column order exactly as printed in the source header:
`Space Heat | Space Cool | Vent. (Fans) | Pumps | SWH (DHW) | Lighting | Equip. (Plug) | Refrig. | Cooking/Other`

| Archetype | SpaceHeat | SpaceCool | Vent_Fans | Pumps | SWH_DHW | Lighting | Equip_Plug | Refrig | Cooking_Other | Σ |
|---|---|---|---|---|---|---|---|---|---|---|
| Large Office          | 30.0 | 14.0 | 11.0 | 3.5 | 1.5 | 12.0 | 27.0 | 0.5 | 0.5  | 100.0 |
| Small Office          | 35.0 | 10.0 | 12.0 | 1.0 | 1.0 | 15.0 | 25.0 | 0.5 | 0.5  | 100.0 |
| Primary School        | 38.0 | 8.0  | 12.0 | 3.0 | 3.0 | 14.0 | 18.0 | 1.0 | 3.0  | 100.0 |
| Secondary School      | 36.0 | 10.0 | 11.0 | 3.0 | 4.0 | 14.0 | 19.0 | 1.0 | 2.0  | 100.0 |
| Stand-alone Retail    | 28.0 | 13.0 | 12.0 | 1.5 | 1.5 | 22.0 | 18.0 | 1.5 | 2.5  | 100.0 |
| Supermarket           | 9.0  | 6.0  | 10.0 | 1.0 | 1.0 | 13.0 | 8.0  | 50.0| 2.0  | 100.0 |
| Full-Service Rest.    | 12.0 | 7.0  | 7.0  | 1.5 | 8.0 | 5.0  | 9.0  | 15.0| 35.5 | 100.0 |
| Large Hotel           | 25.0 | 14.0 | 8.0  | 3.0 | 20.0| 10.0 | 15.0 | 2.0 | 3.0  | 100.0 |
| Hospital              | 40.0 | 14.0 | 10.0 | 3.5 | 3.0 | 11.0 | 16.0 | 1.0 | 1.5  | 100.0 |
| Warehouse             | 51.0 | 3.0  | 9.0  | 1.0 | 1.0 | 10.0 | 4.0  | 5.0 | 16.0 | 100.0 |
| Mid-Rise Apt.         | 28.0 | 11.0 | 5.0  | 1.0 | 23.0| 8.0  | 22.0 | 1.0 | 1.0  | 100.0 |

**Source citations** (from the PDF's per-row `[cite: …]` tags): Large Office 35,36; Small Office
35,37; Primary/Secondary School 35,38; Stand-alone Retail 35,37; Supermarket 26; Full-Service
Rest. 6,35; Large Hotel 9,35; Hospital 8,35; Warehouse 30,38; Mid-Rise Apt. 4,35. Underlying
datasets: CBECS 2018 + PNNL Commercial Prototype Building models (PDF works-cited 30,35).

---

## Mapping: OpenUBEM `archetype_id` → Table-4 archetype

OpenUBEM's `archetype_id` vocabulary (from `05_results.gpkg`) is richer than Table 4's 11 rows.
The mapping below is **pre-decided** (manager ruling); the rationale column is the binding
justification. Anything not listed → **passthrough** (no reconstruction, flagged).

| OpenUBEM archetype_id | → Table-4 key | Rationale |
|---|---|---|
| LargeOffice        | large_office          | exact |
| MediumOffice       | large_office          | no "medium" row; office end-use profile, large is closest commercial-office split |
| SmallOffice        | small_office          | exact |
| Courthouse         | large_office          | institutional, office-dominant occupancy |
| TallBuilding       | large_office          | commercial high-rise → office split |
| SuperTallBuilding  | large_office          | commercial high-rise → office split |
| PrimarySchool      | primary_school        | exact |
| SecondarySchool    | secondary_school      | exact (if present) |
| FullServiceRestaurant | full_service_restaurant | exact |
| QuickServiceRestaurant | full_service_restaurant | no QSR row; both are cooking-/refrig-heavy food service |
| RetailStandalone   | standalone_retail     | exact |
| Supermarket        | supermarket           | exact (if present) |
| Warehouse          | warehouse             | exact (if present) |
| Hospital           | hospital              | exact (if present) |
| LargeHotel / Hotel | large_hotel           | exact (if present) |
| MidriseApartment   | mid_rise_apartment    | exact |
| HighriseApartment  | mid_rise_apartment    | no high-rise residential row; mid-rise apt is closest residential profile |
| SuperMarket        | supermarket           | exact (note: matrix uses camel-case `SuperMarket`; both spellings map) |
| Outpatient         | hospital              | no outpatient row; healthcare profile, hospital is closest |
| SmallHotel         | large_hotel           | only hotel row available (round-trip reference only) |
| College            | secondary_school      | closest educational campus profile (round-trip reference only) |
| Laboratory         | hospital              | high-ventilation healthcare-adjacent profile (round-trip reference only) |
| RetailStripmall    | standalone_retail     | retail profile (round-trip reference only) |
| OpenUBEMUnknown    | large_office (DEFAULT)| unknown type; default to most common commercial split; **flag** |
| *DataCenter / ITE* | — PASSTHROUGH —       | ITE load is plug/equipment already modeled; HVAC-aux profile atypical; do NOT reconstruct, flag |

**Coverage note (2026-06-17 CP-2 audit):** the full 12-cell matrix contains 18 distinct
`archetype_id` values; with the two additions above (`SuperMarket`, `Outpatient`) **all 18 map**
(zero passthrough among success rows). `SmallHotel/College/Laboratory/RetailStripmall` appear
only in the DOE round-trip reference set, not the matrix; they are mapped for T09 completeness.

---

## Method (fraction-split completion) — what the reconstruction computes

The IdealLoads engine meters only **heating + cooling**, and the IDF additionally models
**lighting + equipment (plug)**. Confirmed in `05_results`:
`total_eui_kwh_m2 = heating_eui + cooling_eui + lighting_eui + equipment_eui` (exact).

The **missing** end-uses are exactly the 5 remaining Table-4 columns:
`Vent_Fans, Pumps, SWH_DHW, Refrig, Cooking_Other`.

For a building of archetype `A` with Table-4 fractions `f_*` (decimal, Σ=1):

```
modeled_frac = f_SpaceHeat + f_SpaceCool + f_Lighting + f_Equip_Plug
E_total_est  = (heating + cooling + lighting + equipment) / modeled_frac
recon_j      = f_j * E_total_est        for j in {Vent_Fans, Pumps, SWH_DHW, Refrig, Cooking_Other}
total_eui_reconstructed = total_eui + Σ recon_j
```

`E_total_est` anchors on **all four** modeled end-uses (robust — averages over 4 quantities).
`modeled_frac` is never near zero (min = Supermarket 0.36), so the scale-up is numerically safe.

**Provenance columns** the reconstruction must emit per building:
`reconstruction_applied` (bool), `archetype_mapped_to` (Table-4 key or "passthrough"),
`reconstruction_basis` ("table4_fraction_split"), plus the 5 `*_eui_recon_kwh_m2` columns and
`total_eui_reconstructed_kwh_m2`.

---

## What is NOT in this reference (deferred / out of Phase-1 scope)

- **Table 1 (SWH demand coefficients), Table 2 (SFP/SPP fan & pump sizing), Table 3
  (refrigeration EUI intensities):** these are the *physics-based* alternative method. Their
  numeric cells are also image-only; Table 1's metric/imperial coefficient images are **wider
  than their table cells and clipped** (e.g. Large Office reads `57.04 L/(1000 m²·…)` with the
  denominator unit cut off at the cell boundary). They are **not transcribed here** and are not
  needed for the Phase-1 fraction-split method. If a future Method-B refinement is pursued, the
  full unit strings must be recovered from the embedded image objects (xrefs vary per page) and
  validated before use. Do **not** guess these units.
- The "case-credit" refrigeration thermal-coupling correction (supermarkets) — the PDF notes a
  decoupled refrig estimate can distort the thermal balance >25%; Phase-1 reports refrig as an
  additive energy vector only and does **not** feed it back into the zone thermal balance (no
  resimulation). Documented limitation, not closed in Phase-1.
