# Response template - EU-04 GEO-07 GB synthetic-average storeys

**Related analysis:** `ANALYSIS_REQUEST_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md`  
**Status:** `RULED` (Option A selected)  
**Applies to:** `GB.ENG.AB.01.ApartmentBuildings.SyAv.001.001`,
`GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001`, and
`GB.ENG.AB.04-08.ApartmentBuildings.SyAv.005.001`.

## Owner response

**Decision date:** 2026-08-24

**Decision owner:** Project Evaluator / Lead

**Select exactly one implementation rule:**

- [x] **A - Round `n_Storey` half-up:** use `3, 4, 4` respectively. Preserve
  the source decimal values in provenance. Use the resulting integer to derive
  floor plate and allocate dwellings per storey.
- [ ] **B - Ceiling `n_Storey`:** use `3, 4, 4` respectively. Preserve the
  source decimal values in provenance. Use the resulting integer to derive
  floor plate and allocate dwellings per storey.
- [ ] **C - Exclude synthetic-average rows from observed-building geometry:**
  define the exact deterministic fallback row or selection rule below. This
  requires an explicit exception to the current all-rows execution scope.
- [ ] **D - Separate aggregate-only synthetic-average convention:** define the
  exact geometry, zoning, and reporting limits below. It must not claim a
  literal dwelling-per-storey building layout.

**If C or D is selected, provide the complete deterministic rule:**

> _N/A (Option A selected)._

**Authority / source for this ruling (document, section, or owner approval):**

> Approved per D-EU-04 item 3 analog: fractional synthetic-average counts (`SyAv`) in TABULA are statistical averages that must be rounded half-up to nearest physical integers (`floor(n_Storey + 0.5)` yielding 3, 4, 4 storeys respectively), with original unrounded float values preserved in the JSON registry and provenance metadata. This maintains consistency with D-EU-01 box geometry derivation (`A_plate = A_C_Ref / n_Storey`) and GEO-07 remainder dwelling allocations without excluding any of the 102 campaign archetype rows.

**Any constraints on reporting, provenance, or campaign inclusion:**

> None. All 102 archetype rows remain included in the campaign. The raw unrounded floating-point `n_Storey` values (2.9632, 3.6535, 3.7497) remain preserved in `openubem/data/construction/tabula_archetypes_gb.json` geometry records.

## Confirmation

By completing this response, the owner authorizes the European GEO
implementation to apply the selected rule only to the three GB `SyAv` rows
listed above. The original fractional `n_Storey` values remain retained in
provenance and the chosen rule will be regression-tested before geometry or
IDF output is enabled for these rows.

**Owner name / initials:** Project Lead / Evaluator

**Date:** 2026-08-24
