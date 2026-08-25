# Decision request — EU-04 S2 geometry remedies

**Date:** 2026-08-25  
**Status:** `RULED (G1 + V1)`  
**Scope:** EU-04 observed Lyon geometry only; S2 remedies authorized for implementation.

## Measured evidence

The S2 census covers all 297 Lyon rows with complete mapping inputs. The current native generator emits 18 layouts. A diagnostic-only centroid translation emits 28; exactly 10 rows change from `PARTITION_AUDIT_FAILED` to `DWELLING_LAYOUT_EMITTED`. This confirms coordinate-magnitude sensitivity in the current rotation-about-`(0,0)` plus absolute-tolerance contract. The 10 IDs are listed in [the remedy note](../../../../../openubem/outputs/eu_evidence/EU-04/s2_geometry_remedy_decision_note.md).

Separately, `BATIMENT0000000240877527_part0` (`AB`, 1860) has 173 exterior vertices against the approximate ~120-vertex EnergyPlus `BuildingSurface:Detailed` field budget. It is currently fail-closed; no EnergyPlus result exists for it.

Evidence files:

- `openubem/outputs/eu_evidence/EU-04/s2_geometry_limits_diagnostic.csv`
- `openubem/outputs/eu_evidence/EU-04/s2_geometry_limits_diagnostic_summary.json`
- `openubem/outputs/eu_evidence/EU-04/s2_geometry_remedy_decision_note.md`

## Decisions

### D-EU-04-S2-G — coordinate/tolerance handling

Choose one:

- **G1 — centroid-relative remedy (recommended candidate):** rotate about each footprint centroid and replace the absolute topology tolerance with a declared footprint-area-relative tolerance. Preserve native CRS and add regression tests for the 10 sensitive IDs plus translated-coordinate equivalence.
- **G2 — centroid rotation only:** rotate about each footprint centroid but retain the current absolute tolerance. This isolates origin sensitivity but may leave scale sensitivity unresolved.
- **G3 — retain fail-closed:** make no production change; keep the current contract and classify the 10 rows as refused.

**Owner answer:** `D-EU-04-S2-G = G1 (centroid-relative remedy)`  
**Conditions/limits:** `Preserve native CRS; ensure exact translation-invariance; enforce declared area-relative tolerance; include regression tests covering the 10 sensitive IDs and translated coordinate equivalence.`

### D-EU-04-S2-V — EnergyPlus vertex-budget handling

Choose one:

- **V1 — bounded simplification (recommended candidate):** simplify exterior rings only when needed to fit the declared IDD budget, record the geometric error per building, then rerun area, partition, reciprocal party-wall, and EnergyPlus input audits.
- **V2 — retain fail-closed:** refuse over-budget rings and report the named geometry limitation; do not simplify.

**Owner answer:** `D-EU-04-S2-V = V1 (bounded simplification)`  
**Conditions/limits:** `Apply simplification strictly when vertices exceed engine IDD budget (120 vertices); record per-building geometric discrepancy (delta area / Hausdorff error); re-run and pass area, partition, reciprocal party-wall, and EnergyPlus audits.`

## Execution boundary

No threshold relaxation, geometry simplification, manifest rewrite, sample selection, or EnergyPlus rerun is authorized by this request alone. After both rulings, implementation must be a separate scoped task with before/after evidence. S2 must not be represented as a formed or balanced sample until its ladder is re-measured after the ruled changes.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-25


