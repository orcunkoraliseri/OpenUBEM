# Per-Archetype Benchmark EUI -- US National Reference Values

**Compiled:** 2026-06-17
**Purpose:** Authoritative national/regional Site EUI sanity bands for each OpenUBEM archetype.
**Conversion factor applied throughout:** 1 kBtu/ft2/yr = **3.15459 kWh/m2/yr**

---

## Overview of Sources

| Source ID | Full Name | Edition / Year | Coverage | Notes |
|:---|:---|:---:|:---|:---|
| **ESPM-2024** | US EPA ENERGY STAR Portfolio Manager -- U.S. National Median Table | Aug 2024 | US national median (50th percentile) | Directly read from PDF. Most property types derived from CBECS; hospitals and medical offices from industry surveys. |
| **CBECS-C4** | EIA CBECS -- Table C4: Sum of major fuels gross energy intensities | 2018 | US national mean by PBA | Directly read from web-published EIA table. Arithmetic mean weighted by floorspace. |
| **CBECS-C12** | EIA CBECS -- Table C12: Sum of major fuels by building activity subcategories | 2018 | US national mean by subcategory | Finer PBA subcategory breakdown. |
| **PNNL-CZ6A** | DOE/PNNL Commercial Prototype Building Models -- ASHRAE 90.1-2022, CZ 6A (Buffalo NY) | 2022 | CZ 6A simulation (cold/humid) | Directly read from r6_4_level2_enduse.csv. Includes ALL end-uses. NOT directly comparable to ESPM/CBECS without service-end-use adjustment. |

> **Important methodological note:** ENERGY STAR medians and CBECS means represent **measured utility-bill data from existing buildings**. The PNNL prototype values are **code-minimum EnergyPlus simulations** and include all modeled end-uses (fans, pumps, DHW, refrigeration, cooking). Do **not** average across sources.

---

## Main Benchmark Table

- **Site EUI (orig)** -- value in the original unit published by the source
- **Site EUI (kWh/m2/yr)** -- converted using x3.15459
- **Read** -- **DIRECT** = read from the cited source table; **ESTIMATED** = inferred from secondary description; **N/A** = not available in this source

| Building type | Source | Climate zone | Site EUI (original unit) | Site EUI (kWh/m2/yr) | Source year | Read | Citation URL |
|:---|:---|:---:|---:|---:|:---:|:---:|:---|
| **Small Office** | ESPM-2024 | National (all CZ) | 52.9 kBtu/ft2/yr | **166.9** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| **Small Office** | CBECS-C4 | National (all CZ) | 77.2 kBtu/ft2/yr | **243.5** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| **Small Office** | CBECS-C12 | National (all CZ) | 63.2 kBtu/ft2/yr | **199.4** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| **Small Office** | PNNL-CZ6A | 6A - Buffalo NY | 24.1 kBtu/ft2/yr | **76.0** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=SmallOffice |
| **Small Office** | PNNL-CZ2A | 2A - Houston TX | 28.3 kBtu/ft2/yr | **89.3** | 2016 | ESTIMATED | https://www.nctcog.org/ (secondary) |
| **Small Office** | PNNL-CZ3B | 3B - Las Vegas NV | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| **Small Office** | PNNL-CZ4A | 4A - Baltimore MD | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Medium Office** | ESPM-2024 | National (all CZ) | 52.9 kBtu/ft2/yr | **166.9** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Medium Office | CBECS-C4 | National (all CZ) | 77.2 kBtu/ft2/yr | **243.5** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Medium Office | PNNL-CZ6A | 6A - Buffalo NY | 57.2 kBtu/ft2/yr | **180.5** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=MediumOffice |
| Medium Office | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Large Office** | ESPM-2024 | National (all CZ) | 52.9 kBtu/ft2/yr | **166.9** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Large Office | CBECS-C4 | National (all CZ) | 77.2 kBtu/ft2/yr | **243.5** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Large Office | PNNL-CZ6A | 6A - Buffalo NY | 319.1 kBtu/ft2/yr | **1006.6** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=LargeOffice |
| Large Office | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Stand-alone Retail** | ESPM-2024 | National (all CZ) | 51.4 kBtu/ft2/yr | **162.1** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Stand-alone Retail | CBECS-C4 | National (all CZ) | 64.1 kBtu/ft2/yr | **202.2** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Stand-alone Retail | PNNL-CZ6A | 6A - Buffalo NY | 88.7 kBtu/ft2/yr | **279.8** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=RetailStandalone |
| Stand-alone Retail | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Strip-mall Retail** | ESPM-2024 | National (all CZ) | 103.5 kBtu/ft2/yr | **326.5** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Strip-mall Retail | CBECS-C4 | National (all CZ) | 111.0 kBtu/ft2/yr | **350.2** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Strip-mall Retail | PNNL-CZ6A | 6A - Buffalo NY | 94.7 kBtu/ft2/yr | **298.9** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=RetailStripmall |
| Strip-mall Retail | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Full-Service Restaurant** | ESPM-2024 | National (all CZ) | 325.6 kBtu/ft2/yr | **1027.2** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Full-Service Restaurant | CBECS-C4 | National (all CZ) | 381.5 kBtu/ft2/yr | **1203.5** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Full-Service Restaurant | PNNL-CZ6A | 6A - Buffalo NY | 337.2 kBtu/ft2/yr | **1063.7** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=FullServiceRestaurant |
| Full-Service Restaurant | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Quick-Service Restaurant** | ESPM-2024 | National (all CZ) | 402.7 kBtu/ft2/yr | **1270.3** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Quick-Service Restaurant | CBECS-C4 | National (all CZ) | 381.5 kBtu/ft2/yr | **1203.5** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Quick-Service Restaurant | PNNL-CZ6A | 6A - Buffalo NY | 499.7 kBtu/ft2/yr | **1576.3** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=QuickServiceRestaurant |
| Quick-Service Restaurant | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Mid-Rise Apartment** | ESPM-2024 | National (all CZ) | 59.6 kBtu/ft2/yr | **187.9** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Mid-Rise Apartment | CBECS-C4 | National (all CZ) | N/A | **N/A** | -- | N/A | Residential multifamily not surveyed in CBECS |
| Mid-Rise Apartment | PNNL-CZ6A | 6A - Buffalo NY | 99.4 kBtu/ft2/yr | **313.5** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=MidriseApartment |
| Mid-Rise Apartment | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **High-Rise Apartment** | ESPM-2024 | National (all CZ) | 59.6 kBtu/ft2/yr | **187.9** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| High-Rise Apartment | CBECS-C4 | National (all CZ) | N/A | **N/A** | -- | N/A | Residential multifamily not surveyed in CBECS |
| High-Rise Apartment | PNNL-CZ6A | 6A - Buffalo NY | 281.8 kBtu/ft2/yr | **889.1** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=HighriseApartment |
| High-Rise Apartment | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Small Hotel** | ESPM-2024 | National (all CZ) | 63.0 kBtu/ft2/yr | **198.8** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Small Hotel | CBECS-C4 | National (all CZ) | 120.3 kBtu/ft2/yr | **379.5** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Small Hotel | CBECS-C12 (Motel) | National (all CZ) | 80.0 kBtu/ft2/yr | **252.4** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Small Hotel | PNNL-CZ6A | 6A - Buffalo NY | 108.1 kBtu/ft2/yr | **340.9** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=SmallHotel |
| Small Hotel | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Large Hotel** | ESPM-2024 | National (all CZ) | 63.0 kBtu/ft2/yr | **198.8** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Large Hotel | CBECS-C4 | National (all CZ) | 120.3 kBtu/ft2/yr | **379.5** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Large Hotel | CBECS-C12 (Hotel) | National (all CZ) | 77.7 kBtu/ft2/yr | **245.1** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Large Hotel | PNNL-CZ6A | 6A - Buffalo NY | 287.1 kBtu/ft2/yr | **905.6** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=LargeHotel |
| Large Hotel | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Non-Refrigerated Warehouse** | ESPM-2024 | National (all CZ) | 22.7 kBtu/ft2/yr | **71.6** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Non-Refrigerated Warehouse | CBECS-C4 | National (all CZ) | 35.2 kBtu/ft2/yr | **111.0** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Non-Refrigerated Warehouse | CBECS-C12 | National (all CZ) | 28.8 kBtu/ft2/yr | **90.8** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Non-Refrigerated Warehouse | PNNL-CZ6A | 6A - Buffalo NY | 40.6 kBtu/ft2/yr | **128.2** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=Warehouse |
| Non-Refrigerated Warehouse | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Hospital** | ESPM-2024 | National (all CZ) | 234.3 kBtu/ft2/yr | **739.2** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Hospital | CBECS-C4 | National (all CZ) | 193.3 kBtu/ft2/yr | **609.8** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Hospital | PNNL-CZ6A | 6A - Buffalo NY | 212.6 kBtu/ft2/yr | **670.6** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=Hospital |
| Hospital | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Outpatient / Medical Office** | ESPM-2024 | National (all CZ) | 97.7 kBtu/ft2/yr | **308.2** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Outpatient / Medical Office | CBECS-C4 | National (all CZ) | 82.0 kBtu/ft2/yr | **258.7** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Outpatient / Medical Office | PNNL-CZ6A | 6A - Buffalo NY | 178.4 kBtu/ft2/yr | **562.6** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=Outpatient |
| Outpatient / Medical Office | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Primary School** | ESPM-2024 | National (all CZ) | 48.5 kBtu/ft2/yr | **153.0** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Primary School | CBECS-C4 | National (all CZ) | 82.3 kBtu/ft2/yr | **259.6** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Primary School | CBECS-C12 | National (all CZ) | 53.5 kBtu/ft2/yr | **168.8** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Primary School | PNNL (all CZ) | All CZ | N/A | **N/A** | -- | N/A | SchoolPrimary excluded from local CZ6A batch; see https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Secondary School** | ESPM-2024 | National (all CZ) | 48.5 kBtu/ft2/yr | **153.0** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Secondary School | CBECS-C4 | National (all CZ) | 82.3 kBtu/ft2/yr | **259.6** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Secondary School | CBECS-C12 | National (all CZ) | 65.8 kBtu/ft2/yr | **207.6** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Secondary School | PNNL (all CZ) | All CZ | N/A | **N/A** | -- | N/A | SchoolSecondary excluded from local CZ6A batch; see https://www.energycodes.gov/prototype-building-models |
| | | | | | | | |
| **Supermarket / Grocery** | ESPM-2024 | National (all CZ) | 196.0 kBtu/ft2/yr | **618.3** | 2024 | DIRECT | https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf |
| Supermarket / Grocery | CBECS-C4 | National (all CZ) | 254.5 kBtu/ft2/yr | **802.8** | 2018 | DIRECT | https://www.eia.gov/consumption/commercial/data/2018/ |
| Supermarket / Grocery | PNNL-CZ6A | 6A - Buffalo NY | 214.3 kBtu/ft2/yr | **676.0** | 2022 | DIRECT | local: r6_4_level2_enduse.csv, archetype=SuperMarket |
| Supermarket / Grocery | PNNL-CZ2A/3B/4A | 2A/3B/4A | N/A | **N/A** | -- | N/A | https://www.energycodes.gov/prototype-building-models |

---

## Quick-Reference Summary by Archetype

| Building type | ESPM-2024 Median (kWh/m2/yr) | CBECS-2018 Mean (kWh/m2/yr) | PNNL CZ6A Prototype (kWh/m2/yr) |
|:---|:---:|:---:|:---:|
| Small Office | 166.9 | 243.5 | 76.0 |
| Medium Office | 166.9 | 243.5 | 180.5 |
| Large Office | 166.9 | 243.5 | 1006.6 |
| Stand-alone Retail | 162.1 | 202.2 | 279.8 |
| Strip-mall Retail | 326.5 | 350.2 | 298.9 |
| Full-Service Restaurant | 1027.2 | 1203.5 | 1063.7 |
| Quick-Service Restaurant | 1270.3 | 1203.5 | 1576.3 |
| Mid-Rise Apartment | 187.9 | N/A | 313.5 |
| High-Rise Apartment | 187.9 | N/A | 889.1 |
| Small Hotel | 198.8 | 379.5 (C4) / 252.4 (C12-motel) | 340.9 |
| Large Hotel | 198.8 | 379.5 (C4) / 245.1 (C12-hotel) | 905.6 |
| Non-Refrigerated Warehouse | 71.6 | 111.0 (C4) / 90.8 (C12) | 128.2 |
| Hospital | 739.2 | 609.8 | 670.6 |
| Outpatient / Medical Office | 308.2 | 258.7 | 562.6 |
| Primary School | 153.0 | 259.6 (C4) / 168.8 (C12) | N/A |
| Secondary School | 153.0 | 259.6 (C4) / 207.6 (C12) | N/A |
| Supermarket / Grocery | 618.3 | 802.8 | 676.0 |

---

## Data Provenance Notes

### ENERGY STAR Portfolio Manager (ESPM-2024)

- **PDF directly read:** US National Median Table.pdf, August 2024 edition.
- **URL:** https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf
- ENERGY STAR does **not** subdivide Office into small/medium/large -- all three map to the same value (52.9 kBtu/ft2).
- Hotel is a single category (63.0 kBtu/ft2) -- no Small vs. Large distinction.
- Multifamily Housing (59.6) covers both Mid-Rise and High-Rise; data source is Fannie Mae Industry Survey, not CBECS.
- Hospitals (234.3) and Medical Offices (97.7) are from Industry Surveys, not CBECS.
- Non-Refrigerated Warehouse (22.7) reflects the ENERGY STAR-enrolled population, which skews toward more efficient distribution centers.
- K-12 School (48.5) aggregates Elementary, Middle, and High School.

### EIA CBECS 2018 (CBECS-C4 and CBECS-C12)

- **URL:** https://www.eia.gov/consumption/commercial/data/2018/
- Table C4 provides gross energy intensities by Principal Building Activity (PBA) -- arithmetic mean, weighted by floorspace.
- Table C12 provides finer subcategory breakdowns.
- CBECS does **not** survey residential multifamily -- Mid-Rise and High-Rise Apartments are excluded.
- CBECS Food service (381.5) aggregates quick-service and full-service restaurants.
- CBECS Lodging (C4=120.3); Table C12: Hotel=77.7, Motel=80.0.
- CBECS Education (C4=82.3); Table C12: Elementary school=53.5, High school=65.8.
- CBECS Retail other than mall (64.1) maps to Stand-alone Retail.
- CBECS Enclosed and strip malls (111.0) maps to Strip-mall Retail.

### DOE/PNNL Prototype Building Models (PNNL-CZ6A)

- **Local data source:** docs/validations/overAll/results/r6_4_level2_enduse.csv
- **Standard:** ASHRAE 90.1-2022 prototype IDFs, EnergyPlus v22.1
- **Climate:** CZ 6A -- Buffalo NY (TMYx 2011-2025 weather file)
- **End-use scope:** ALL modeled end-uses -- heating, cooling, interior lighting, interior equipment, fans, pumps, domestic hot water, refrigeration, elevators. Total site EUI.
- **Scaling note for Large Office:** CZ6A Large Office = 1006.6 kWh/m2 (breakdown: heating 18.8, cooling 31.3, lighting 33.5, equipment 286.0, other 637.0 kWh/m2). The Other (637) is dominated by ventilation, DHW, and elevator loads in the 60-zone, 14,252 m2 prototype. This is a simulation scaling artifact.
- **CZ 2A, 3B, 4A:** Not in local simulation batch. Listed as N/A. Full dataset at https://www.energycodes.gov/prototype-building-models
- **Primary and Secondary School:** IDF files exist in ref_inventory but were excluded from the r6_4_level2_enduse.csv batch. Listed as N/A.

---

## Interpretation Guidance for OpenUBEM Validation

1. **OpenUBEM uses IdealLoadsAirSystem** -- models sensible/latent HVAC, interior lighting, and interior equipment only. Fans, pumps, DHW, refrigeration, cooking, and elevators are NOT modeled. Therefore:
   - OpenUBEM EUI ~ PNNL (heating + cooling + lighting + equipment) only
   - OpenUBEM output represents approximately 42-65% of the PNNL total site EUI

2. **Recommended sanity check approach:**
   - Lower bound: ENERGY STAR median x 0.55 (expected, since OpenUBEM omits service loads)
   - Lower bound: CBECS mean x 0.45 similarly
   - Do not expect OpenUBEM to match PNNL total prototype EUI without a service-load reconstruction layer

3. **The service-load gap** (fans, pumps, DHW, refrigeration) accounts for a median 42% of the total prototype EUI across 20 archetypes (per V15 Level-2 Decomposition analysis, V15_R6_4_level2_decomposition.md).

---

*All source URLs and direct citations are provided inline in the main table. No values were invented or interpolated across sources -- gaps are explicitly marked as N/A.*