# Analysis request — EU-04 GEO-07 GB synthetic-average storeys

**Date:** 2026-08-24  
**Status:** `RESOLVED` (Option 1 / Option A selected per response template)

## Finding

The frozen TABULA registry has three GB `ApartmentBuildings.SyAv` records with
both a non-integer apartment average and a non-integer `n_Storey` average:

| Archetype | `n_Apartment` | `n_Storey` | `A_C_Ref` m² |
|---|---:|---:|---:|
| `GB.ENG.AB.01.ApartmentBuildings.SyAv.001.001` | 6.5734429892539765 | 2.963203700833504 | 496.2841810399237 |
| `GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001` | 13.640224105603993 | 3.653506549032009 | 886.781009039109 |
| `GB.ENG.AB.04-08.ApartmentBuildings.SyAv.005.001` | 17.212477056753745 | 3.749745575000498 | 1080.1628299053398 |

The accepted D-EU-04 text explicitly authorizes `round()` for the three
non-integer **`n_Apartment`** values (7, 14, 17), but it does not authorize a
rounding, ceiling, floor, or exclusion rule for their non-integer
**`n_Storey`** values. `n_Storey` is required for the D-EU-01 floor plate and
for GEO-07's storey-by-storey remainder allocation.

## Current fail-closed implementation

`openubem.geometry.european_residential.allocate_european_dwellings` accepts
only an integral positive storey count. It implements D-EU-04's explicit
half-up apartment count and first-storey quotient/remainder allocation for
all 139 registry records with integral `n_Storey`; it rejects the three rows
above with `n_storey must be a positive integer` rather than silently creating
fractional floors.

The focused regression includes the three rejected rows as a required
negative case. This is a partial GEO-07 foundation, not completion of EU-04.

## Decision needed

Choose one rule and record it as a D-EU-01/D-EU-04 amendment before these
three archetypes enter S1+ geometry, IDF, or campaign manifests:

1. **Round `n_Storey` half-up** (3, 4, 4), retaining the original value in
   provenance and recalculating the physical plate from `A_C_Ref / n`.
2. **Use ceiling** (3, 4, 4), retaining original average values in provenance.
3. **Exclude `SyAv` rows from observed-building geometry**, with an explicit
   deterministic fallback to a non-synthetic GB row; this conflicts with the
   current D-EU-04 statement that all 102 rows run, so it requires an explicit
   override.
4. **Define a separate synthetic-average geometry convention** that preserves
   a non-integer reference number in an aggregate-only model; it cannot claim
   a literal dwelling-per-storey layout.

## Resolution (2026-08-24)

Option 1 (**Round `n_Storey` half-up**) was formally adopted in `RESPONSE_TEMPLATE_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md`:
- `GB.ENG.AB.01.ApartmentBuildings.SyAv.001.001`: `n_Storey = 2.9632...` rounds to **3** storeys.
- `GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001`: `n_Storey = 3.6535...` rounds to **4** storeys.
- `GB.ENG.AB.04-08.ApartmentBuildings.SyAv.005.001`: `n_Storey = 3.7497...` rounds to **4** storeys.
- The unrounded floating-point values are retained in provenance and geometry records.
- Floor plates are calculated from $A_{\text{plate}} = A_{\text{C,Ref}} / n_{\text{storey,rounded}}$, and dwelling allocations follow the D-EU-04 first-storey remainder distribution across the rounded integer storeys. All 102 campaign archetype rows run.

