# Phase 2 Results — `openubem-shading` (`T07`–`T08`, `CP-2`)

- **Generated:** 2026-11-26 17:28 UTC
- **Git commit:** `fdf6a3cb8`
- **Host hardware:** `arm64` (`macOS-13.5.2-arm64-arm-64bit`)
- **Rust toolchain:** `rustc 1.100.0 (0ef1bc386 2026-11-09)`
- **Shadow mismatches:** `0` (`OPENUBEM_RUST_BACKEND="shadow"`, B3 `atol=1e-4`)

## 1. Benchmark & Shadow Parity Summary

| Workload | Items | Python Median (s) | Rust Median (s) | Speedup | Shadow Mismatches | Parity Verification |
|---|---:|---:|---:|---:|---:|---|
| `R2_utm_overhang_analytic` | 1 | 0.0000 | 0.0000 | **1.00×** | 0 | beam_max_diff=0.00e+00, sky_max_diff=8.33e-17 |
| `R2_gpusim_shading_cpu` | 5 | 5.3521 | 0.0116 | **460.51×** | 0 | beam_max_diff=0.00e+00, sky_max_diff=3.33e-16 |

## 2. Gate Verdict (`CP-2`)

- Shadow parity (`atol <= 1e-4` across 8,760 hours and sky diffuse factors) passed with `total_mismatches == 0`.
- UTM centroid origin shifting verified at `(500_000 m, 4_500_000 m)` to preserve sub-mm ray-triangle precision.
- Default runtime flags remain `OPENUBEM_RUST_BACKEND = "off"` per Guardrail 1.
