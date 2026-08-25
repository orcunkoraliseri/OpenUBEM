# EU-04 S2 geometry remedy decision note

**Measured:** 2026-08-25T19:55:21Z  
**Status:** diagnostic only; no production geometry, manifest, or EnergyPlus behavior changed.

## Evidence

The companion diagnostic `s2_geometry_limits_diagnostic.csv` measures all 297 Lyon rows with complete mapping inputs. The native generator emits 18 rows. A centroid-translated diagnostic rerun emits 28 rows, with exactly 10 rows changing from `PARTITION_AUDIT_FAILED` to `DWELLING_LAYOUT_EMITTED`:

`BATIMENT0000000240877159_part0`, `BATIMENT0000000240877179_part0`, `BATIMENT0000000240879467_part0`, `BATIMENT0000000240879979_part0`, `BATIMENT0000000240880177_part0`, `BATIMENT0000000240880393_part0`, `BATIMENT0000000240881095_part0`, `BATIMENT0000000240881134_part0`, `BATIMENT0000000240881528_part0`, `BATIMENT0000000240881532_part0`.

This is sensitivity evidence for the current rotation-about-`(0,0)` plus absolute-tolerance contract. It is not evidence that centroid translation is an approved production fix.

One separate row, `BATIMENT0000000240877527_part0` (`AB`, 1860), has 173 exterior vertices against the approximate ~120-vertex EnergyPlus IDD field budget. It remains fail-closed at layout stage and is not an EnergyPlus result.

## Owner decision required before implementation

1. **Coordinate/tolerance remedy:** choose whether to (a) rotate around each footprint centroid, (b) replace the absolute partition tolerance with a declared footprint-area-relative tolerance, or (c) retain the current fail-closed contract. Any selected remedy requires a focused regression corpus including the 10 IDs above, native EPSG:32631 behavior, and a translated-coordinate equivalence assertion.
2. **Vertex-budget remedy:** choose whether to (a) simplify exterior rings under a declared geometric-error bound and record the per-building error, or (b) retain fail-closed refusal for over-budget rings. Any simplification must be validated against reciprocal party-wall and area audits before EnergyPlus rerun.

Until those decisions are ruled, S2 remains **diagnosed but not formable** and no outcome-balanced S2 sample is authorized.
