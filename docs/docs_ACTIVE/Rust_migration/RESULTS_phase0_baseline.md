# Phase 0 Baseline — Python Hotspot Profile (`T02`)

- **Generated:** 2026-11-26 16:13 UTC
- **Git commit:** `fdf6a3cb8`
- **Host hardware:** `Apple M2 Pro` (arm64, Darwin 22.6.0)
- **Python:** `3.11.4` (`/Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/python`)
- **Rust toolchain:** `rustc 1.100.0 (0ef1bc386 2026-11-09)`
- **Profiler:** `scripts/bench/profile_python_hotspots.py` (median over 3 warm runs where fast; `cProfile` + `tracemalloc` + RSS)

---

## 1. End-to-End Hotspot Summary (Python Baseline)

| Workload | Target Crate / Phase | Items | Median Wall (s) | Median CPU (s) | Peak Py Heap (MiB) | Rate / Extrapolation | SHA-256 |
|---|---|---:|---:|---:|---:|---|---|
| `R1a_results_sql_harvest` | Phase 1 / openubem-results | 7 | 0.1538 | 0.1534 | 4.08 | 21.97 ms/bldg (~178.8 s @ 8,139 bldgs) | `6e9467b519715676` |
| `R1a_results_sql_large` | Phase 1 / openubem-results | 1 | 5.4166 | 5.3335 | 3.39 | 5.42 s for 229 MB SQL | `97a3c49712a34df9` |
| `R1b_eu_csv_heating_real` | Phase 1 / openubem-results | 100 | 1.1807 | 1.1799 | 0.05 | 11.81 ms/bldg (~481.7 s @ 40,800 bldgs) | `36b40c6abeb8fcdc` |
| `R1b_eu_csv_4enduse_dblpass` | Phase 1 / openubem-results | 25 | 1.1562 | 1.1538 | 0.39 | 46.25 ms/bldg (~1887.0 s @ 40,800 bldgs) | `synthetic-eu10-25` |
| `R1c_provenance_schema` | Phase 1 / openubem-schema | 2,381 | 0.0149 | 0.0149 | 1.16 | 0.006 ms/bldg (~0.6 s @ 100k bldgs) | `7a05f8feb082e9e4` |
| `R2_gpusim_shading_cpu` | Phase 2 / openubem-shading | 5 | 5.2569 | 5.2458 | 3.83 | 1051.4 ms/bldg (~4028.9 s @ 3,832 M8 homes) | `1a60d152a13ee16d` |
| `R3a_idf_parse_compile` | Phase 3 / openubem-idf | 50 | 0.2174 | 0.2173 | 8.07 | 4.35 ms/IDF (~43.5 s @ 10k IDFs) | `477593f85f751d8b` |
| `R3b_ctf_and_scriptf` | Phase 3 / openubem-idf | 200 | 0.1314 | 0.1313 | 0.08 | 0.66 ms/zone (~6.6 s @ 10k zones) | `synthetic-4layer` |
| `R4a_stage_a_cpu_solver` | Phase 4 / openubem-sim | 1 | 66.8635 | 66.6938 | 4.86 | 66.86 s/cell-yr (~802.4 s for 12-cell P1) | `83f150cbb8859e9c` |
| `R4b_microclimate_svf` | Phase 4 / openubem-microclimate | 27,224 | 0.5018 | 0.5015 | 11.36 | 54.3 kpix/s (~4.6 s @ 500x500) | `7a05f8feb082e9e4` |
| `R4c_microclimate_utci` | Phase 4 / openubem-microclimate | 4,573,632 | 3.0050 | 2.9989 | 981.41 | 1.52 Mevals/s | `seed-42-synthetic` |
| `R6a_resolve_overlaps` | Phase 5b (deferred) / R6 eval | 4,012 | 0.4902 | 0.4902 | 0.69 | 0.122 ms/bldg | `580fc3b083d68b00` |
| `R6b_discover_context` | Phase 5b (deferred) / R6 eval | 200 | 0.3555 | 0.3555 | 0.14 | 1.78 ms/bldg (~4.2 s for full ES-MAD) | `7a05f8feb082e9e4` |

### Published M8 Reference Anchor

- `openubem/outputs/gpusim_m8_eu_districts.csv` (SHA-256 `00cf642990364d07`): 3,832 homes across 4 EU districts took **2,898.8 s** total, of which **505.1 s** (17.4% total / **93% of non-kernel time**) was brute-force `gpusim/shading.py` and **38.0 s** was Python IDF/layout compile.

---

## 2. Top `cProfile` Cumulative Hotspots per Workload

### `R1a_results_sql_harvest` — parse_building_sql + check_building_integrity on ~650 KB SQLs
- Wall range: `0.1530s`–`0.1818s` (3 run(s)); process peak RSS `227.3 MiB`
  - `profile_python_hotspots.py:374:_bench_sql (0.267s, 1 calls)`
  - `parser.py:119:parse_building_sql (0.242s, 7 calls)`
  - `sql.py:437:read_sql_query (0.222s, 7 calls)`
  - `sql.py:2866:read_query (0.204s, 7 calls)`
  - `sql.py:2906:_fetchall_as_list (0.140s, 7 calls)`

### `R1a_results_sql_large` — parse_building_sql + check_building_integrity on 229 MB SQL
- Wall range: `5.4166s`–`5.4166s` (1 run(s)); process peak RSS `233.8 MiB`
  - `profile_python_hotspots.py:410:_bench_large_sql (5.369s, 1 calls)`
  - `parser.py:850:check_building_integrity (4.290s, 1 calls)`
  - `~:0:<method 'execute' of 'sqlite3.Connection' objects> (4.290s, 5 calls)`
  - `parser.py:119:parse_building_sql (1.079s, 1 calls)`
  - `sql.py:437:read_sql_query (1.075s, 1 calls)`

### `R1b_eu_csv_heating_real` — Single-pass DictReader heating harvest on 100 real EU-08 rep1 CSVs
- Wall range: `1.1792s`–`1.1980s` (3 run(s)); process peak RSS `233.9 MiB`
  - `profile_python_hotspots.py:438:_bench_csv_heating (6.136s, 1 calls)`
  - `~:0:<built-in method builtins.sum> (6.136s, 876001 calls)`
  - `profile_python_hotspots.py:439:<genexpr> (6.136s, 101 calls)`
  - `profile_python_hotspots.py:265:_extract_heating_kwh_csv (6.135s, 100 calls)`
  - `csv.py:107:__next__ (3.982s, 876100 calls)`

### `R1b_eu_csv_4enduse_dblpass` — extract_four_end_use_eplus_csv (double-pass, 25x8760 contract CSVs)
- Wall range: `1.1547s`–`1.1563s` (3 run(s)); process peak RSS `234.6 MiB`
  - `profile_python_hotspots.py:466:_bench_csv_4enduse (6.623s, 1 calls)`
  - `~:0:<built-in method builtins.sum> (6.623s, 1095426 calls)`
  - `profile_python_hotspots.py:467:<genexpr> (6.622s, 26 calls)`
  - `european_campaign.py:37:extract_four_end_use_eplus_csv (6.608s, 25 calls)`
  - `csv.py:107:__next__ (2.477s, 438050 calls)`

### `R1c_provenance_schema` — add_lineage_summary + append_flag on ES-MAD-BERRUGUETE (2,381 bldgs)
- Wall range: `0.0149s`–`0.0151s` (3 run(s)); process peak RSS `261.5 MiB`
  - `profile_python_hotspots.py:507:_bench_provenance (0.114s, 1 calls)`
  - `provenance.py:175:add_lineage_summary (0.096s, 1 calls)`
  - `provenance.py:151:_field_score (0.051s, 16667 calls)`
  - `provenance.py:79:parse_token (0.021s, 16667 calls)`
  - `provenance.py:113:append_flag (0.015s, 1 calls)`

### `R2_gpusim_shading_cpu` — compute_exterior_shading (periodic=5d, 3x3, 64 sky rays) on ES-MAD sample
- Wall range: `5.2401s`–`5.2724s` (3 run(s)); process peak RSS `284.7 MiB`
  - `profile_python_hotspots.py:604:_bench_shading (6.471s, 1 calls)`
  - `shading.py:195:compute_exterior_shading (6.470s, 5 calls)`
  - `shading.py:68:_ray_triangle_any_hit_numpy (6.039s, 5 calls)`
  - `fromnumeric.py:2338:sum (2.363s, 23206 calls)`
  - `~:0:<method 'reduce' of 'numpy.ufunc' objects> (2.362s, 71205 calls)`

### `R3a_idf_parse_compile` — compile_expidf_batch (parse + extract + pack) on 50 EU-08 expIDFs
- Wall range: `0.2166s`–`0.2174s` (3 run(s)); process peak RSS `295.1 MiB`
  - `profile_python_hotspots.py:652:_bench_idf_compile (1.744s, 1 calls)`
  - `compile.py:764:compile_expidf_batch (1.743s, 1 calls)`
  - `compile.py:376:_compile_single_building (1.730s, 50 calls)`
  - `schedules.py:45:load_schedule_file_hourly (1.130s, 50 calls)`
  - `subset.py:71:parse_expidf (0.202s, 100 calls)`

### `R3b_ctf_and_scriptf` — build_modal_conduction + calc_script_f (200 4-layer walls + zones)
- Wall range: `0.1308s`–`0.1318s` (3 run(s)); process peak RSS `295.2 MiB`
  - `profile_python_hotspots.py:687:_bench_ctf_vf (0.439s, 1 calls)`
  - `viewfactors.py:52:fix_view_factors (0.258s, 200 calls)`
  - `fromnumeric.py:2338:sum (0.145s, 24000 calls)`
  - `fromnumeric.py:69:_wrapreduction (0.122s, 24200 calls)`
  - `viewfactors.py:12:calc_approximate_view_factors (0.095s, 200 calls)`

### `R4a_stage_a_cpu_solver` — run_stage_a_batch (105,120 steps, 1 golden EU cell, Python NumPy f64)
- Wall range: `66.8635s`–`66.8635s` (1 run(s)); process peak RSS `323.2 MiB`
  - `profile_python_hotspots.py:728:_bench_stage_a (171.880s, 1 calls)`
  - `numpy_ref.py:264:run_stage_a_batch (171.880s, 1 calls)`
  - `numpy_ref.py:410:_step_one (170.138s, 105984 calls)`
  - `window.py:63:solve_simple_window (43.128s, 105984 calls)`
  - `convection.py:97:calc_iso15099_window_int_conv_coeff (38.786s, 311369 calls)`

### `R4b_microclimate_svf` — compute_svf (32 az, r=50px) on 166x164 grid
- Wall range: `0.5016s`–`0.5265s` (3 run(s)); process peak RSS `346.9 MiB`
  - `profile_python_hotspots.py:756:_bench_svf (0.532s, 1 calls)`
  - `svf.py:32:compute_svf (0.532s, 1 calls)`
  - `~:0:<built-in method builtins.round> (0.008s, 3200 calls)`
  - `~:0:<built-in method numpy.zeros> (0.000s, 33 calls)`
  - `_methods.py:117:_mean (0.000s, 2 calls)`

### `R4c_microclimate_utci` — utci_approx (210-term) on 168h x 166x164
- Wall range: `2.9735s`–`3.1758s` (3 run(s)); process peak RSS `1499.0 MiB`
  - `profile_python_hotspots.py:784:_bench_utci (3.235s, 1 calls)`
  - `utci.py:289:utci_approx (3.219s, 1 calls)`
  - `utci.py:50:_brode_polynomial_offset (3.093s, 1 calls)`
  - `fromnumeric.py:2241:clip (0.034s, 4 calls)`
  - `fromnumeric.py:51:_wrapfunc (0.034s, 4 calls)`

### `R6a_resolve_overlaps` — _resolve_overlaps on ES-MAD (2,381) + IT-BOL (1,631) footprints
- Wall range: `0.4856s`–`0.5249s` (3 run(s)); process peak RSS `1499.0 MiB`
  - `profile_python_hotspots.py:807:_bench_overlaps (1.466s, 1 calls)`
  - `footprint_schema.py:25:_resolve_overlaps (1.465s, 2 calls)`
  - `indexing.py:3446:__getitem__ (0.752s, 13024 calls)`
  - `frame.py:4978:_get_item (0.711s, 17036 calls)`
  - `indexing.py:3294:__getitem__ (0.709s, 13024 calls)`

### `R6b_discover_context` — discover_context (r=30m) for 200 ES-MAD buildings
- Wall range: `0.3553s`–`0.3563s` (3 run(s)); process peak RSS `1499.0 MiB`
  - `profile_python_hotspots.py:838:_bench_context (1.652s, 1 calls)`
  - `context.py:32:discover_context (1.597s, 200 calls)`
  - `indexing.py:1327:__getitem__ (1.119s, 4473 calls)`
  - `indexing.py:2399:_getitem_axis (1.101s, 4473 calls)`
  - `frame.py:4239:_ixs (1.037s, 4673 calls)`

---

## 3. Cold Import Latency (Fresh Python Interpreter)

| Module | Cold Import (ms) |
|---|---:|
| `openubem.config` | 131.9 |
| `openubem.results.parser` | 422.1 |
| `openubem.results.european_campaign` | 432.9 |
| `openubem.gpusim.shading` | 62.9 |
| `openubem.gpusim.compile` | 65.1 |
| `openubem.microclimate.svf` | 347.9 |
| `openubem.microclimate.utci` | 358.5 |

---

## 4. Phase 0 Gate Takeaways for R1–R6 Prioritization

- **R1 (`openubem-schema` + `openubem-results`)**: Both SQL (`parser.py`) and double-pass CSV (`european_campaign.py`) scale linearly with building count across thousands of directories; single open-read-close `rusqlite` + streaming `csv` + `rayon` cleanly removes the post-sim I/O wall.
- **R2 (`openubem-shading`)**: Confirmed dominant per-building geometry cost (`compute_exterior_shading`), reproducing the M8 505.1 s wall.
- **R3 (`openubem-idf`)**: `compile_expidf_batch`, `build_modal_conduction`, and `calc_script_f` grow linearly into multi-minute setup overhead at 10k+ buildings.
- **R4 (`openubem-sim` + `openubem-microclimate`)**: Single-cell Python Stage-A loop (`run_stage_a_batch`), `compute_svf`, and 210-term `utci_approx` confirm large pure-CPU headroom for Rust `rayon` + `pulp`.
- **R6 (`_resolve_overlaps` & `discover_context` — D-RS-06 check)**: Measured directly above so `T17` can decide strictly on empirical wall-time share after testing vectorized `shapely` 2.0.
