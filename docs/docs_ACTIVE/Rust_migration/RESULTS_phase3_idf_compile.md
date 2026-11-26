# Phase 3 Results — `openubem-idf` (`T09`–`T11`, `CP-3`)

- **Generated:** 2026-11-26 17:41 UTC
- **Git commit:** `fdf6a3cb8`
- **Host hardware:** `arm64` (`macOS-13.5.2-arm64-arm-64bit`)
- **Rust toolchain:** `rustc 1.100.0 (0ef1bc386 2026-11-09)`
- **Shadow mismatches:** `0` (`OPENUBEM_RUST_BACKEND="shadow"`, B1/B2)

## 1. Benchmark & Shadow Parity Summary

| Workload | Items | Python Median (s) | Rust Median (s) | Speedup | Shadow Mismatches | Parity Verification |
|---|---:|---:|---:|---:|---:|---|
| `R3a_idf_parse_compile` | 50 | 0.2240 | 0.1097 | **2.04×** | 0 | Exact parse_expidf + <=1e-12 Schedule/ScriptF parity on 50 EU-08 IDFs |
| `R3a_schedule_compact_200` | 200 | 0.2112 | 0.0064 | **33.07×** | 0 | Exact 8760-hour Schedule:Compact parity across all 7 weekdays |
| `R3b_ctf_and_scriptf` | 200 | 0.1519 | 0.0069 | **21.92×** | 0 | <=1e-12 modal CTF invariants & ScriptF LU solve parity |

## 2. Gate Verdict (`CP-3`)

- Shadow parity passed with `total_mismatches == 0` across IDF parse (`B1`), Schedule CSV/Compact (`B2`), modal CTF (`B2`), and ScriptF (`B2`).
- Zero `ndarray-linalg`/OpenBLAS dependencies: pure-Rust `nalgebra` + `faer` verified.
- Default runtime flags remain `OPENUBEM_RUST_BACKEND = "off"` per Guardrail 1.
