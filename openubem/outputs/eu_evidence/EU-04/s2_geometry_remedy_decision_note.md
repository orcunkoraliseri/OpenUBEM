# EU-04 S2 geometry remedy decision note

**Measured:** 2026-08-25T19:55:21Z  
**Status:** `RULED (G1 + V1)` and implemented; manifest unchanged.

## Evidence

The companion diagnostic `s2_geometry_limits_diagnostic.csv` measures all 297 Lyon rows with complete mapping inputs. After G1, the native generator emits 28 rows and the centroid-translated probe also emits 28, with zero status changes. The former 10 `PARTITION_AUDIT_FAILED` rows are now translation-invariant:

`BATIMENT0000000240877159_part0`, `BATIMENT0000000240877179_part0`, `BATIMENT0000000240879467_part0`, `BATIMENT0000000240879979_part0`, `BATIMENT0000000240880177_part0`, `BATIMENT0000000240880393_part0`, `BATIMENT0000000240881095_part0`, `BATIMENT0000000240881134_part0`, `BATIMENT0000000240881528_part0`, `BATIMENT0000000240881532_part0`.

This was the sensitivity evidence for the former rotation-about-`(0,0)` plus absolute-tolerance contract. G1 now rotates about the footprint centroid and applies the declared relative tolerance.

One separate row, `BATIMENT0000000240877527_part0` (`AB`, 1860), has 173 exterior vertices against the approximate ~120-vertex EnergyPlus IDD field budget. V1 simplifies this ring only for EnergyPlus emission and records Δarea and Hausdorff error; the original manifest geometry is unchanged.

## Ruled implementation

1. **G1:** centroid rotation plus declared area-relative topology tolerance, preserving native CRS and translation invariance.
2. **V1:** simplification only above 120 vertices, with deterministic Δarea/Hausdorff provenance and re-audits before EnergyPlus.

The remedies are implemented and audited. S2 remains **not formable under the original 32-cell completeness ladder**; no outcome-balanced S2 sample was selected.
