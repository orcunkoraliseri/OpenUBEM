# Phase 1 Results — `openubem-schema` + `openubem-results` (`T04`–`T06`, `CP-1`)

- **Generated:** 2026-11-26 17:20 UTC
- **Git commit:** `fdf6a3cb8`
- **Host hardware:** `arm64` (`macOS-13.5.2-arm64-arm-64bit`)
- **Rust toolchain:** `rustc 1.100.0 (0ef1bc386 2026-11-09)`
- **Shadow mismatches:** `0` (`OPENUBEM_RUST_BACKEND="shadow"`)

## 1. Benchmark & Shadow Parity Summary

| Workload | Items | Python Median (s) | Rust Median (s) | Speedup | Shadow Mismatches | Parity Verification |
|---|---:|---:|---:|---:|---:|---|
| `R1a_results_sql_campaign_small` | 7 | 0.1576 | 0.0145 | **10.88×** | 0 | Bit-exact hourly/integrity/EIO/ERR parity across corpus |
| `R1a_results_sql_golden_large` | 7 | 5.6291 | 1.2456 | **4.52×** | 0 | Bit-exact hourly/integrity/EIO/ERR parity across corpus |
| `R1b_eu_csv_heating_real` | 100 | 1.1901 | 0.0075 | **158.34×** | 0 | Bit-exact heating sums + fail-closed 4-EU guard parity |
| `R1b_eu_csv_4enduse_singlepass` | 25 | 1.1690 | 0.0457 | **25.58×** | 0 | Exact 12-month & 8760-hour closure; single-pass ByteRecord |
| `R1c_provenance_lineage_summary` | 2381 | 0.0327 | 0.0036 | **9.09×** | 0 | Exact int counts + <=1e-12 confidence parity |

## 2. Gate Verdict (`CP-1`)

- Zero shadow mismatches achieved across all retained SQL, CSV, `.eio`, `.err`, and provenance corpora (`total_mismatches == 0`).
- Default runtime flags remain `OPENUBEM_RUST_BACKEND = "off"` per Guardrail 1.
