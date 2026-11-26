# Phase 4 Results — `openubem-sim` + `openubem-microclimate` (`T12`–`T14`, `CP-4`)

- **Generated:** 2026-11-26 17:56 UTC
- **Git commit:** `fdf6a3cb8`
- **Host hardware:** `arm64` (`macOS-13.5.2-arm64-arm-64bit`)
- **Rust toolchain:** `rustc 1.100.0 (0ef1bc386 2026-11-09)`
- **Shadow mismatches:** `0` (`OPENUBEM_RUST_BACKEND="shadow"`)

## 1. Benchmark & Shadow Parity Summary

| Workload | Items | Python Median (s) | Rust Median (s) | Speedup | Shadow Mismatches | Parity Verification |
|---|---:|---:|---:|---:|---:|---|
| `R4a_stage_a_cpu_solver` | 1 | 68.3878 | 0.3089 | **221.39×** | 0 | <=1e-12 annual kWh diff=1.75e-09 across 105,120 steps |
| `R4b_microclimate_svf` | 27224 | 0.5236 | 0.0098 | **53.61×** | 0 | SVF B3 + B1 horizon shadow parity on 166x164 |
| `R4c_microclimate_utci` | 4573632 | 2.6367 | 0.1238 | **21.30×** | 0 | <=1e-12 210-term Brode UTCI & exact stress class parity |

## 2. Gate Verdict (`CP-4`)

- Shadow parity passed with `total_mismatches == 0` across Stage-A solver (`B2`), L1-tiled SVF (`B3`), horizon shadows (`B1`), and 210-term UTCI (`B2`).
- Clean-room microclimate (`openubem-microclimate`) verified free of `GPL-3.0` (`SOLWEIG-GPU`/`UMEP-dev/solweig`) dependencies.
- Speed HPC cluster was **not accessed** per owner directive; Linux `manylinux` wheels tested via CI (`T18`).
- Default runtime flags remain `OPENUBEM_RUST_BACKEND = "off"` per Guardrail 1.
