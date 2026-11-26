# Phase 5 Results — `openubem-extrude` & `R6` Gate (`T15`–`T17`, `CP-5`)

- **Generated:** 2026-11-26 18:10 UTC
- **Git commit:** `fdf6a3cb8`
- **Host hardware:** `arm64` (`macOS-13.5.2-arm64-arm-64bit`)
- **Rust toolchain:** `rustc 1.100.0 (0ef1bc386 2026-11-09)`
- **Audit failures:** `0`

## 1. Benchmark & Gate Summary

| Workload | Items | Baseline Python (s) | Accelerated / Vectorized (s) | Speedup | Failures | Verification |
|---|---:|---:|---:|---:|---:|---|
| `R5_extrude_match_eu_layout` | 10 | 0.7990 | 0.4711 | **1.70×** | 0 | 100% bijective reciprocal party walls + E+ 23.1 GetSurfaceData clean |
| `R6_overlaps_vec_shapely2_gate` | 4012 | 0.5337 | 0.2574 | **2.07×** | 0 | Vectorized shapely 2.0 achieves 0.25s total -> R6 Rust DEFERRED (D-RS-06) |

## 2. Gate Verdict (`T15`–`T17`)

- Pure-Rust `openubem-extrude` (`geo` + `rstar`, zero `geos`/`LGPL`) passes closed-shell divergence checks, courtyard holes, reciprocal interzone audit (`37 passed`), and real EnergyPlus 23.1 execution under `OPENUBEM_RUST_EXTRUDER=1`.
- `T17` confirms `R6` remains **DEFERRED (`NO-GO`)** per `D-RS-06`: vectorized `shapely 2.0` resolves 4,012 real European footprints in `~0.25 s`, well below the >15% threshold.
- Default `OPENUBEM_RUST_EXTRUDER` remains `0` (OFF) per Guardrail 1.
