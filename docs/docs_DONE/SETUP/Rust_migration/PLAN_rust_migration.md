# PLAN — Selective Python-to-Rust Migration for OpenUBEM (`rust-migration`)

**Slug:** `rust-migration`
**Date:** 2026-11-26
**Workspace Root:** `/Users/orcunkoraliseri/Desktop/OpenUBEM`
**Status:** ARCHIVED TO `docs/docs_DONE/SETUP/Rust_migration/` (2026-11-27) — MIGRATION COMPLETE (`T01`–`T18`, `CP-0`–`CP-5` passed in `e4caed745`; `R6` deferred per `D-RS-06`) + **Auto-Fastest Cross-Platform Dispatch ENABLED (`c9e02c01b`)**: defaults are now `OPENUBEM_SIM_ENGINE="auto"`, `OPENUBEM_GPUSIM_DEVICE="auto"`, `OPENUBEM_RUST_BACKEND="auto"`, `OPENUBEM_RUST_EXTRUDER="auto"` via `openubem/gpusim/dispatch.py`.
**Companions:** [`../GPU_based_compute/PLAN_gpu_accelerated_simulation.md`](../GPU_based_compute/PLAN_gpu_accelerated_simulation.md) · [`../GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md`](../GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md)
**Research Prompts:** [`Prompt/deepResearch/README.md`](Prompt/deepResearch/README.md) (DR01–DR06)

---

## 0. TL;DR (read this first)

1. **Hybrid "Rust Core + Thin PyO3 Adapter, Python Orchestration" — not a full rewrite.** Like Anthropic's Messages API, Pydantic v2 (`pydantic-core`), Astral (`uv`/`ruff`), and Polars, OpenUBEM keeps high-level orchestration, GIS fetching, plotting, ML, and Jupyter/WebGL tooling in Python, while moving CPU-bound simulation precompute, IDF compilation/extrusion, parallel result harvesting, and strict data-control boundaries into pure Rust crates exposed via PyO3 + `maturin`.
2. **Anthropic's key lesson: verification is the real bottleneck, not translation.** In Anthropic's Python-to-Rust Messages API migration (~70% less CPU, >80% less memory, ~20% faster median TTFT), **98% of integration tests passed while 75% of live traffic initially diverged** due to subtle semantic drift and weakened assertions. Every OpenUBEM Rust component must therefore ship behind a three-state flag (`OPENUBEM_RUST_BACKEND = "off" | "shadow" | "on"`, default `"off"`) with automated dual-run diff fingerprinting before `"on"` is allowed.
3. **Top simulation bottlenecks Rust can crush immediately:**
   - **M8 exterior ray-traced shading (`openubem/gpusim/shading.py`):** took **505.1 s** out of **2,898.8 s** (17.4% of total M8 wall time, **93% of all non-kernel time**) across 3,832 homes because it runs brute-force $O(R \times P \times M)$ Möller-Trumbore without a spatial acceleration structure. A flat BVH + SIMD + `rayon` engine in Rust targets 15–80× speedup on CPU alone.
   - **CPU float64 reference & HPC solver (`openubem/gpusim/backends/numpy_ref.py`):** Stage A took **274 s** for 12 single-zone cells because of a 105,120-step Python loop. Compiling the physics core to native Rust with `rayon` unlocks multi-core CPU speed on Mac and 32-core Speed HPC nodes without GPU dependencies.
   - **IDF parsing, modal CTF, view factors & batch packing (`openubem/gpusim/{subset,compile,general_model,ctf,viewfactors,router}.py`):** `BUILD_SPEC_gpu_heat_balance_engine.md` notes text-IDF parsing in Python costs more than the GPU run at 10k+ buildings (`38.0 s` even on 3,832 M8 homes).
4. **Top data-control wins where Rust eliminates entire classes of OpenUBEM bugs:**
   - **Compile-time schema, unit, and provenance guarantees:** OpenUBEM's U.S. fleet EUI was restated four times (`153.82 → 153.95 → 172.41 → 171.38 → 154.10 kWh/m²`) due to DHW/cooking/refrigeration double-counting, missed ABUPS district-heating rows (`OPEN-61`/`OPEN-64`), and floor-area denominator mismatches (`OPEN-01`). Today, `data_quality_flag` also has a live delimiter mismatch (`,` in `footprint_schema.py` / `aggregator.py` vs `|` in `semantic/provenance.py`). Rust algebraic data types (ADTs), unit newtypes (`AreaM2`, `EnergyKwh`, `EnergyJ`), and exhaustive end-use enums make double-counting, unit mix-ups, and silent `NaN`/empty-string coercion unrepresentable.
   - **Replacing `eppy` and `geomeppy` fragility:** `eppy`'s bundled v8.0 IDD causes field-shift errors and silent extensible-field truncation (`_repair_oversized_epbunch_objls`), while `geomeppy 0.12.2` caused inverted walls (`FINDING 284`: 35k+ walls), 10 m³ volume stubs (`OPEN-56`: 57.74× ACH error across 8,160 buildings), infinite hangs (`M > 800`), missed interfloor pairs, and ULP vertex-drift EnergyPlus fatals (`EU-11`/`EU-14`).
5. **Parallel results harvesting (`openubem/results/{parser,european_campaign,aggregator}.py`):** `parser.py` queries 8,139–40,800 `eplusout.sql` files via sequential Python `sqlite3` + `pd.read_sql_query`, and `european_campaign.py` reads every `eplusout.csv` **twice** via Python `csv.DictReader`. A `rusqlite` + `rayon` + Arrow/Parquet harvester removes the post-simulation I/O bottleneck.
6. **What we do NOT rewrite in Rust:** EnergyPlus C++ itself (NG1 in the GPU plan), working `gpusim` CUDA/Metal Stage-C kernels (unless DR05 proves otherwise), HTTP fetchers (`acquisition/`), `scikit-learn` imputation, `matplotlib` plotting, or JS/WebGL viewers (`viz/shell/`).

---

## 1. Current State (verified on disk 2026-11-26)

### 1.1 Codebase & Toolchain Inventory

| Item | Verified Fact on Disk | Source / Citation |
|---|---|---|
| Package size | **59,669 lines** across 13 subpackages (`gpusim` 15,707; `geometry` 8,418; `results` 6,021; `semantic` 5,998; `idf` 5,422; `acquisition` 4,978; `microclimate` 4,159; `viz` 4,025; `validation` 1,509; `scenarios` 1,076; `data` 796; `campaign` 751; `simulation` 540; `config.py` 269) | `openubem/` line count |
| Test suite | **182** `tests/test_*.py` files; **1,937+ passed** baseline | `tests/`, `docs/PROJECT_CHECKLIST.md:106` |
| Packaging & licence | `setuptools>=68`, Python `>=3.10`, `uv.lock`, dual-licensed **`Apache-2.0 OR MIT`** | `pyproject.toml:1-20` |
| Local toolchain | `uv`, `python3`, `rustc 1.100.0`, `cargo 1.100.0`, `maturin 1.16.0`, `cargo-deny 0.22.1`, `cargo-audit 0.23.0` installed; 8-crate `openubem-rust` built (`abi3-py310`) | local verification 2026-11-26 |
| Target machines | (1) Apple M2 Pro (12 cores, arm64, Metal, Rosetta for E+ 23.1); (2) Windows x86_64 + NVIDIA RTX A400 (4 GB VRAM, CUDA cc 8.6); (3) Concordia Speed HPC (Linux x86_64, SLURM, tcsh login shell, `%32` CPU cap, non-root) | `CLAUDE.md:41-54`, `MANAGER_prompt_gpusim.md:8` |

### 1.2 Measured Performance Bottlenecks

| Subsystem | Current Implementation | Measured Bottleneck | Citation |
|---|---|---|---|
| **E+ CPU runs** | Subprocess per building (`joblib` loky) | 2,048 runs: median 3.2 s, p90 9.8 s, p99 232.8 s, max 906.9 s; `austin_centre` top-10 = 40% of CPU time | `PLAN_gpu_accelerated_simulation.md:43-54` |
| **M8 3D shading** | `gpusim/shading.py:68-160` brute-force Möller-Trumbore (no BVH) | **505.1 s** on 3,832 homes (17.4% of total 2,898.8 s, **93% of non-kernel time**) | `openubem/outputs/gpusim_m8_eu_districts.csv:6` |
| **Stage-A CPU solver** | `gpusim/backends/numpy_ref.py` Python 105k-step loop | **274 s** for 12 single-zone EU cells | `MANAGER_prompt_gpusim.md:94` |
| **IDF compile & pack** | `gpusim/{subset,compile,general_model,ctf,viewfactors,router}.py` | **38.0 s** for 3,832 M8 homes; Python parsing exceeds GPU time at 10k+ buildings | `gpusim_m8_eu_districts.csv:6`, `BUILD_SPEC:129` |
| **Microclimate rasters** | `microclimate/{svf,shadow,utci}.py` | Dense 1-px shifts × 32 azimuths allocate full padded float64 rasters per step; UTCI polynomial reaches $10^{11}$ (risky in float32 MPS) | `svf.py:32-65`, `shadow.py:94-139`, `PLAN_gpu:179` |
| **Results harvesting** | `results/parser.py`, `results/european_campaign.py` | Sequential Python `sqlite3` + `pd.read_sql_query` across 8k–40k dirs; `european_campaign.py` parses each `eplusout.csv` twice via `csv.DictReader` | `parser.py:119-200`, `european_campaign.py:37-89` |

### 1.3 Documented Data-Control & `eppy`/`geomeppy` Failure Modes

| Defect Class | Evidence in Repo | Citation |
|---|---|---|
| **IDD shift & field truncation** | `eppy` bundled v8.0 IDD shifts E+ 23.1 `BuildingSurface:Detailed` fields; `EpBunch.__repr__` truncates extensible fields & `;` terminators (`_repair_oversized_epbunch_objls`) | `openubem/config.py:13-26`, `openubem/idf/builder.py:105-125` |
| **Winding inversion & 10 m³ stubs** | `geomeppy 0.12.2` `is_clockwise()` inverted 35,709+ EU walls (`FINDING 284`) and produced 10 m³ zone-volume stubs across 8,160 buildings (`OPEN-56`: 57.74× ACH error, −11.8% heating) | `OpenUBEM_debug_References.md:38-84` |
| **Geometry hangs & ULP fatals** | `intersect_match()` hung infinitely (`M > 800`), missed cyclic inter-floor pairs (`idf/surfaces.py:127-160`), and 1-ULP mirrored coordinate drift caused `GetSurfaceData` fatals on 8 EU-11 + 2 EU-14 buildings | `OpenUBEM_debug_References.md:122-150`, `idf/surfaces.py:127-160` |
| **Delimiter & schema drift** | `data_quality_flag` uses `,` in `footprint_schema.py:126` & `aggregator.py:144-148`, vs `\|` in `semantic/provenance.py:23,104-110`; row-wise `iterrows()`/`apply(axis=1)` and late `Int64`/empty-str coercion | `footprint_schema.py:64,97,127`, `provenance.py:79-95`, `simulation/parallel.py:220-225` |
| **Accounting & unit restatements** | U.S. fleet EUI restated 4 times (DHW double-count `D-IMP-05`, cooking/refrig double-count, ABUPS district heating `OPEN-61`/`OPEN-64`, floor-area denominator `OPEN-01`) | `docs/PROJECT_CHECKLIST.md:6,89` |

---

## 2. Goals & Non-Goals

### Goals
- **G1 (Speed):** Cut wall-clock time on shading precompute (15–80×), IDF/ExpIDF compilation (20–100×), CPU thermal simulation (50–100× vs Python `numpy_ref`), microclimate SVF/UTCI rasters (10–30× on CPU), and multi-thousand-building SQL/CSV results harvesting (10–50×).
- **G2 (Data Control):** Enforce compile-time physical units, exhaustive end-use and provenance ADTs, fail-closed schema validation, and single-source-of-truth flag/token serialization at the Rust boundary.
- **G3 (Geometric Determinism):** Eliminate `eppy` and `geomeppy` failure modes (inverted winding, missing reciprocal pairs, ULP drift, `intersect_match` hangs) with a deterministic, typed Rust IDF extruder behind a feature flag.
- **G4 (Zero-Regression Rollout):** Gate every component behind `OPENUBEM_RUST_BACKEND = "off" | "shadow" | "on"` (default `"off"`) with Anthropic-style shadow-diffing and fingerprint logging across retained corpora before activation.
- **G5 (Cross-Platform Portability):** Build cleanly on macOS arm64 (M2 Pro), Windows x86_64 (MSVC), and Linux x86_64 (Speed HPC without root access) via `abi3` wheels and `uv`.

### Non-Goals
- **NG1:** Rewriting or forking EnergyPlus's C++ solver in Rust.
- **NG2:** Replacing working `gpusim` Stage-C CUDA/Metal kernels (`general_common.h`) unless DR05 proves a unified Rust/GPU stack beats them without regression.
- **NG3:** Porting HTTP acquisition clients (`acquisition/`), scikit-learn ML training (`semantic/imputation.py`), matplotlib plotting (`results/plotting_suite.py`), or HTML/JS viewers (`viz/shell/`).
- **NG4:** Blindly porting the 5,669 lines of Shapely/GEOS heuristics in `geometry/european_residential.py` and `geometry/european_nocore.py` before profiling and parity gating prove ROI.
- **NG5:** Introducing any GPL, AGPL, or copyleft-incompatible dependency (`Apache-2.0 OR MIT` project licence; enforced via `cargo-deny`).

---

## 3. Guardrails & Hard Rules for Executors

1. **Default behaviour unchanged:** `OPENUBEM_RUST_BACKEND` in `openubem/config.py` defaults to `"off"`. With default config, every existing pipeline step and test must produce byte-identical outputs.
2. **Core + Adapter separation:** Core crates (`openubem-schema`, `openubem-results`, `openubem-shading`, `openubem-idf`, `openubem-sim`, `openubem-microclimate`, `openubem-extrude`) must have **zero `pyo3` dependencies**. All Python FFI lives strictly in `crates/openubem-py`. Every core crate must pass standalone `cargo test`, property tests (`proptest`), and benchmarks (`criterion`).
3. **Anthropic-style shadow-parity gate:** Every migrated function supports `OPENUBEM_RUST_BACKEND="shadow"`, which runs Python and Rust on the same input, records structural mismatch fingerprints (without altering pipeline outputs), and must achieve **0 unexplained mismatches** across the target corpus before `"on"` is approved:
   - Parsers, provenance tokens, schema checks, and SQL/CSV harvesting: **bit-exact** (exact integer/string equality, float delta $\le 10^{-12}$ kWh).
   - Float64 CPU thermal solver, modal CTF, ScriptF/view factors: relative error $\le 10^{-12}$ vs `numpy_ref.py` / `ctf.py` / `viewfactors.py`.
   - BVH shading & microclimate SVF/UTCI: max abs error $\le 10^{-4}$ sunlit fraction / $\le 0.005$ SVF / $\le 10^{-6}$ K UTCI.
4. **FFI, memory & concurrency safety (updated per DR01/DR04):** No `unwrap()`/`panic!()` on user/file input across FFI; map typed `thiserror` errors to custom Python exceptions. Release the GIL using PyO3 `0.26+` **`py.detach`** (renamed from `allow_threads`) on every batch/`rayon` call. **Never hold a borrowed `&[T]` / `ArrayView` to a mutable NumPy array across `py.detach`** unless read-only immutability (`writeable == False`) and alignment/C-contiguity (`np.require(..., requirements=["C", "A"])`) are verified (or copy small inputs to owned `Vec<T>`); return freshly owned `PyArray::from_vec` buffers (`abi3` restricts `BufferViewMut`). Avoid `rayon` floating-point non-associativity drift by mapping in parallel into indexed `Vec`s and reducing sequentially/fixed-tree (or using Neumaier summation / scaled `i64` micro-kWh). Use zero-copy NumPy (`rust-numpy`) and Arrow PyCapsule (`arrow-rs`/`pyo3-arrow`); never copy large matrices element-by-element through `PyList`.
5. **License, clean-room & CI gate (updated per DR02/DR03/DR04/DR06):** `deny.toml` allows `Apache-2.0`, `MIT`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `Unicode-3.0`, `Zlib` only, and explicitly **bans** `geos`, `geos-sys`, `geos-src` (which declare `MIT` in `Cargo.toml` while wrapping `LGPL-2.1-or-later` C++ `libgeos`), `openssl-sys`, and any GPL/AGPL crate (`modelscript`, `CGAL`). Isolate `rusqlite` (`bundled` `libsqlite3-sys`, SQLite Public Domain blessing) strictly inside `crates/openubem-results` via a crate-scoped `deny.toml` clarification/exception so `openubem-schema` stays 100% SQLite-free. Implement `openubem-microclimate` strictly **clean-room** from Lindberg et al. (2008) & Bröde et al. (2012) — never read or copy `SOLWEIG-GPU` (`GPL-3.0-only`) or `UMEP-dev/solweig` (`GPL-3.0`). `cargo deny check --locked` and `cargo audit` run in CI alongside `cargo test` and `pytest`.
6. **Git hygiene:** Scope status checks to relevant paths (`git status --porcelain -- crates/ openubem/ tests/ docs/docs_ACTIVE/Rust_migration/`). Never commit build artifacts (`target/`, `*.whl`, `*.so`, `*.pyd`).

---

## 4. Candidate Solution Space (Ranked by ROI vs Risk)

| ID | Target Modules & Crate | Primary Benefit | Expected Gain (Evidence) | Drift Risk | Effort | Phase |
|---|---|---|---|---|---|---|
| **R1** | `footprint_schema.py`, `provenance.py`, `results/{parser,european_campaign,aggregator}.py` → `openubem-schema` + `openubem-results` | **Data control + I/O speed** | 10–50× faster SQL/CSV harvest (H); eliminates delimiter/unit/double-count bugs | Very low (exact parity verifiable) | S–M | **1** |
| **R2** | `gpusim/shading.py` → `openubem-shading` | **M8 simulation speed** | 15–80× on M8 shading (`505.1 s` → ~6–30 s) via BVH + SIMD + `rayon` (H) | Low (pure geometry math) | S | **2** |
| **R3** | `gpusim/{subset,compile,general_model,ctf,viewfactors,router}.py`, `idf/compliance.py` → `openubem-idf` | **Pre-sim speed + IDF safety** | 20–100× IDF parse/pack (`38 s` → <1 s; unlocks 10k+ sweeps); eliminates `eppy` IDD/truncation bugs (H) | Medium (E+ text quirks) | M | **3** |
| **R4** | `gpusim/backends/numpy_ref.py`, `microclimate/{svf,shadow,utci}.py` → `openubem-sim` + `openubem-microclimate` | **CPU solver + UTCI speed** | 50–100× CPU Stage-A (`274 s` → <3 s); 10–30× CPU microclimate + native Speed HPC scaling (H) | Low–Med (float32/64 parity) | M | **4** |
| **R5** | `idf/{surfaces,builder,surface_orientation}.py`, `geometry/context.py` → `openubem-extrude` | **Geometry determinism** | Eliminates `geomeppy` winding flips (`FINDING 284`), 10 m³ stubs (`OPEN-56`), hangs (`M > 800`), ULP drift fatals (H) | High (subtle IDF parity) | L | **5a** |
| **R6** | `footprint_schema.py::_resolve_overlaps`, `geometry/context.py::discover_context` (NOT `european_*.py`) | **GIS prep speed (DEFERRED)** | **Default NO-GO** per DR06: test 20-line vectorized `shapely` 2.0 first; port only if ≥15% wall time (>30 s) & ≥3× speedup via pure-Rust `rstar` + `geo`/`i_overlay` (ban `geos` crate) | High (GEOS/`i_overlay` snapping parity) | M | **5b (deferred)** |

---

## 5. Proposed Cargo Workspace, Verified Crate Stack & Python Integration Layout

*(Packaging layout below reflects DR01's recommended Option (b) for `D-RS-01`: pure-Python `setuptools` root `pyproject.toml` + optional workspace companion package `openubem-rust` in `[project.optional-dependencies] rust` so contributors without `rustc` keep working via plain `uv sync`. Exact crate patch versions will be resolved and locked in `Cargo.lock` + audited via `cargo deny check` during T03; minor cross-DR patch-version notes — `rayon 1.11/1.12` — resolve automatically at lock time.)*

```text
OpenUBEM/
├── pyproject.toml                 # Pure-Python setuptools>=68; [project.optional-dependencies] rust = ["openubem-rust"]
├── Cargo.toml                     # Workspace manifest (resolver = "2", MSRV >= 1.85 for PyO3 0.30+)
├── Cargo.lock                     # Committed for reproducible Mac / Win / Speed HPC builds
├── deny.toml                      # cargo-deny: permissive SPDX allowlist, explicit bans (geos*, openssl-sys), scoped libsqlite3-sys note
├── crates/
│   ├── openubem-schema/           # Pure Rust (NO pyo3, NO sqlite): #[repr(transparent)] units, nutype, smallvec, arrow, parquet, geoarrow, serde, thiserror
│   ├── openubem-results/          # Pure Rust (NO pyo3): rusqlite (bundled, single open-read-close), csv, memchr, rayon, arrow, parquet ArrowWriter
│   ├── openubem-shading/          # Pure Rust (NO pyo3): obvhs (PLOC/CWBVH8) + f64 centroid shift + watertight Woop f64-fallback + rayon
│   ├── openubem-idf/              # Pure Rust (NO pyo3): memchr + fast-float2 + unicase + winnow (IDD/Schedule:Compact) + serde_json + nalgebra (CTF) + faer (ScriptF)
│   ├── openubem-sim/              # Pure Rust (NO pyo3): rayon + pulp (NEON/AVX2/AVX-512) + num-traits SimFloat (f64 ref & f32 GPU-twin) + libm
│   ├── openubem-microclimate/     # Pure Rust (NO pyo3, clean-room): 32x64 L1-tiled pulp + rayon f64 SVF (max dz/d), Beer-Lambert canopy, 210-term Bröde UTCI
│   ├── openubem-extrude/          # Pure Rust (NO pyo3): geo + i_overlay (i64 grid snap) + rstar + glam + Newell outward-normal & volume checks
│   └── openubem-py/               # ONLY crate with pyo3 (0.30.1, abi3-py310, generate-import-lib) -> top-level `_openubem_rust` (re-exported via `openubem/_rust.py` to avoid editable-install shadowing)
├── openubem/
│   ├── config.py                  # Adds OPENUBEM_RUST_BACKEND ("off" | "shadow" | "on", default "off"), OPENUBEM_RUST_SHADOW_LOG, OPENUBEM_RUST_EXTRUDER
│   ├── _rust.py                   # Thin facade re-exporting compiled `_openubem_rust` (raises ModuleNotFoundError cleanly when absent)
│   ├── _rust_bridge.py            # Graceful optional import of `openubem._rust` with pure-Python fallback
│   ├── rust_shadow.py             # Tolerance-bucketed comparator (B1/B2/B3), canonical hasher, JSONL mismatch fingerprinter
│   └── ...                        # Existing Python modules call _rust conditionally when flag != "off"
├── scripts/bench/
│   ├── profile_python_hotspots.py # Phase 0 wall-clock & py-spy profiler across Steps 1–6 & M8
│   └── shadow_parity_corpus.py    # Automated parity check over golden cells, 346 EU-08, M8 4 districts, austin_centre
└── docs/docs_ACTIVE/Rust_migration/
    ├── PLAN_rust_migration.md     # This file
    ├── RESULTS_phase*.md          # Measured benchmark & parity reports per phase
    └── Prompt/deepResearch/       # DR01–DR06 prompts & results/DR01–DR06_result.md
```

---

## 6. Phased Implementation Plan

### Phase 0 — Deep Research, Profiling & Toolchain Bring-Up
- **T01 — Review DR01–DR06 & lock owner decisions:**
  - *What:* Synthesize Deep Research findings (`Prompt/deepResearch/results/DR01–DR06_result.md`) and record owner rulings on D-RS-01 through D-RS-06.
  - *Why:* Avoid picking incompatible crates (e.g., GPL-licensed geometry crates, slow parser combinators, or non-portable GPU bindings).
  - *How:* Update §4/§5/§10 of this plan with verified crate versions, licenses, and benchmark citations.
  - *How to test:* All 6 DR result files reviewed and cited; D-RS-01..D-RS-06 resolved.
- **T02 — End-to-end hotspot profiling & baseline corpus freeze:**
  - *What:* Create `scripts/bench/profile_python_hotspots.py` to measure per-stage CPU/wall-clock/RSS across Step 1–5 (`austin_centre`), Step 6 microclimate, and `gpusim` M8 (`ES-MAD-BERRUGUETE` + `IT-BOL-GALVANI2`).
  - *Why:* Confirm where Python time actually goes (especially in `geometry/`, `idf/`, `results/`, `gpusim/shading.py`, and `gpusim/general_model.py`) so Phase 5b (R6) does not port C-speed Shapely/GEOS code needlessly.
  - *How:* Use `py-spy` / `cProfile` + `tracemalloc`; save baseline metrics to `RESULTS_phase0_baseline.md`.
  - *How to test:* Reproducible JSON/Markdown baseline table with SHA-256 fixture hashes.
- **T03 — Toolchain install, Cargo workspace scaffold & shadow harness:**
  - *What:* Install `rustup` (pinned stable Rust `>= 1.85` for PyO3 `0.30.x`), `maturin[zig]`, `cargo-deny`, `cargo-audit`; create `Cargo.toml`, `Cargo.lock`, `deny.toml`, `crates/openubem-py` (`openubem-rust` → `openubem._rust` with `abi3-py310` + `generate-import-lib` + dynamic `/MD` CRT on Windows, never `+crt-static`), `OPENUBEM_RUST_BACKEND` flag in `openubem/config.py`, `openubem/_rust_bridge.py`, and `openubem/rust_shadow.py` (B1/B2/B3 buckets + JSONL mismatch fingerprinting). Check `ldd --version` on a Speed compute node to decide `manylinux_2_17` (`--zig`) vs `manylinux_2_28`.
  - *Why:* Prove cross-platform compilation (`macOS arm64` + `Windows x64` + Speed Linux `manylinux` wheel) and Anthropic-style shadow diffing before writing domain logic, while keeping plain `uv sync` working without `rustc`.
  - *How:* Expose a trivial `rust_smoke_info()` PyO3 entrypoint; verify `cargo test --locked`, `cargo deny check --locked`, `cargo audit`, `maturin develop --release --uv -m crates/openubem-py/Cargo.toml`, and `pytest` pass with flag `"off"`.
  - *How to test:* `pytest` baseline unchanged (0 failures without `--extra rust`); `python -c "import openubem._rust"` prints Rust target triple and SIMD features.

### Phase 1 — Data Control Firewall & Parallel Results Harvester (`R1`)
- **T04 — `openubem-schema` typed domain & provenance firewall:**
  - *What:* Implement strongly typed Rust models (manual `#[repr(transparent)]` physical unit newtypes + `nutype` bounded scalars — avoiding `uom`/`dimensioned`), exhaustive 10-end-use, 14-ABUPS-district-heating, and `SimulationStatus` enums, typestate `EndUseLedger<RawMeters>` → `EndUseLedger<ReconciledLedger>`, provenance tokens (`{METHOD}_{SOURCE}_{TIER}` + legacy tokens), stack-allocated `SmallVec<[QualityFlag; 8]>` unified `data_quality_flag` parser/serializer (with backward-compatible `,` vs `|` adapter per D-RS-03), and Stage 1–5 Arrow schema validators.
  - *Why:* Prevent unit mix-ups, silent `NaN`/string drift, and end-use double-counting at compile time; replace row-wise `iterrows()`/`apply(axis=1)` in `footprint_schema.py` and Python string loops in `provenance.py`.
  - *How:* Zero-copy Arrow PyCapsule FFI (`arrow-rs` + `pyo3-arrow`, accepting `Utf8`/`LargeUtf8`/`Utf8View`/`DictionaryArray`) + `geoarrow` (keeping `.gpkg` ingress in Python `pyogrio(use_arrow=True)`) + `serde` JSON manifests; `proptest`/`bolero` fuzzing over malformed tokens and edge-case floats.
  - *How to test:* `cargo test -p openubem-schema` + shadow parity on all Stage 1–5 fixtures.
- **T05 — `openubem-results` parallel SQLite/CSV/ABUPS harvester:**
  - *What:* Single open-read-close `rusqlite` (`bundled`, `SQLITE_OPEN_READ_ONLY | SQLITE_OPEN_URI`, checking for orphan non-empty `-wal`/`-journal` files, **never** blind `?immutable=1`; `PRAGMA mmap_size = 0` on Lustre/GPFS/NFS and ≤32–64 MB on local NVMe only) and single-pass `csv` (`ByteRecord` reuse) + `memchr` `.eio` extractor for `eplusout.sql`, `eplusout.csv`, `eplusout.end`, `eplusout.err`, and ABUPS integrity checks (`check_building_integrity`).
  - *Why:* Consolidate 3–4 sequential `sqlite3` opens (`parser.py`) and double-pass `csv.DictReader` (`european_campaign.py`) across 8k–40k building directories without exhausting macOS `ulimit -n` or causing Lustre `SIGBUS`.
  - *How:* `rayon` threadpool with GIL released (`py.detach`), strict non-leap 8,760 calendar validation, returning `pyarrow.Table` zero-copy via `pyo3-arrow` for `aggregator.py` plus streaming `parquet::arrow::ArrowWriter` for direct `05_results.parquet` / large sweeps.
  - *How to test:* Unit tests on golden `.sql` / `.csv` fixtures + `OPEN-46`/`OPEN-61`/`OPEN-64` + orphan `-wal`/`-journal` edge cases.
- **T06 — Phase 1 shadow parity & benchmark:**
  - *What:* Run `OPENUBEM_RUST_BACKEND="shadow"` over all retained EU-08/EU-11/U.S. SQL/CSV/manifest artifacts and record `RESULTS_phase1_data_results.md`.
  - *Why:* Guarantee 100% bit-exact parity on every EUI, GWP, provenance score, and integrity flag before switching `"on"`.
  - *How:* Diff report via `scripts/bench/shadow_parity_corpus.py`.
  - *How to test:* 0 mismatches across full retained corpus; ≥10× speedup measured on bulk harvest.

### Phase 2 — BVH Ray-Traced Shading Accelerator (`R2`)
- **T07 — `openubem-shading` flat BVH + SIMD engine:**
  - *What:* Implement pure-Rust `obvhs` (PLOC BVH2 / CWBVH8) + `rayon` exterior shading matching `openubem/gpusim/shading.py::compute_exterior_shading`, with **`f64` local-centroid origin shift** before `f32` AABB construction (avoiding 0.25–0.5 m UTM `f32` ULP error), conservative `1e-4 m` AABB padding, pre-traversal backface culling (`dot(ray, normal) <= 1e-4`), and a **Woop/Benthin/Wald (2013) watertight leaf intersector with `f64` edge fallback**. (Reject `embree4-rs` external DLL/no-Metal and `wgpu` ray-query overhead.)
  - *Why:* Eliminate M8's **505.1 s** brute-force shading bottleneck (`93%` of non-kernel M8 runtime) and close the existing `float32`/`float64` gap between PyTorch and NumPy shading paths.
  - *How:* Build CWBVH once per district/building; evaluate all sun hours + 64 Fibonacci sky rays in parallel across target surfaces with `py.detach` and read-only contiguous NumPy buffers.
  - *How to test:* `cargo test -p openubem-shading` (analytic canyon, courtyard, overhang, UTM-shifted coordinates) + `criterion` benchmark.
- **T08 — Phase 2 shadow parity & M8 benchmark:**
  - *What:* Shadow-compare Rust BVH vs `gpusim/shading.py` on M7b cases and all 4 M8 districts (`ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`, `IT-BOL-GALVANI2`), saving `RESULTS_phase2_shading.md`.
  - *Why:* Verify shading fractions match before cutting M8 shading from 505.1 s down to <30 s.
  - *How:* Compare `sunlit_frac[H, S]` and `dif_shdg_iso_sky[S]` and downstream annual kWh.
  - *How to test:* Max `|Δsunlit_frac| <= 1e-4` (report any grazing-edge epsilon hits), total shading wall time <30 s on 4 M8 districts.

### Phase 3 — Typed IDF/ExpIDF Parser, Compiler & Compliance Auditor (`R3`)
- **T09 — `openubem-idf` lexer/parser, IdealLoads expander, router & compliance auditor:**
  - *What:* Clean-room zero-copy `&[u8]` IDF/ExpIDF/EPW scanner (`memchr` + `fast-float2` + `unicase`) + `winnow` for `Energy+.idd` / `Schedule:Compact` + `serde_json` for `Energy+.schema.epJSON`, typed E+ 23.1 object schema, `HVACTemplate:IdealLoadsAirSystem` expander (`router.py`, enabling pre-expanded IDFs without `-x` `ExpandObjects`), fail-closed S0/S1/S2a/S2b/S3 whitelist validator (`subset.py`/`general_model.py`), and envelope compliance auditor (`idf/compliance.py`).
  - *Why:* No production Rust IDF/IDD/`epJSON` crate exists (`epw-rs` is dormant alpha; `modelscript` is `AGPL-3.0`); removes `eppy` IDD/truncation hazards and Python parsing overhead at 10k+ buildings.
  - *How:* Strict typed records with ASCII case-folding (preserving `\retaincase`), explicit E+ 23.1 IDD defaults, typed extensible `Vec`s unconditionally terminated with `;`, and structured error diagnostics.
  - *How to test:* `cargo test -p openubem-idf` + fuzzing malformed IDFs (`proptest`).
- **T10 — Modal CTF, ScriptF/view factors & CSR `GeneralBatch` packer:**
  - *What:* Port `ctf.py::build_modal_conduction` using pure-Rust **`nalgebra`** (`≤12×12` symmetric `eigh` / tridiagonal QR), `viewfactors.py` (`calc_approximate_view_factors`, `fix_view_factors`, `calc_script_f` via **`faer`** `partial_piv_lu` solve — avoiding `ndarray-linalg`/OpenBLAS/Fortran linking on Windows & HPC), and `compile.py`/`general_model.py` parallel CSR packing directly into contiguous NumPy arrays.
  - *Why:* Remove Python loops, BLAS/Fortran build fragility, and GIL contention when compiling 4k–100k buildings for `gpusim` or CPU simulation.
  - *How:* Parallel `rayon` compilation per building followed by a deterministic CSR merge into owned `rust-numpy` arrays.
  - *How to test:* Float64 parity against `ctf.py`, `viewfactors.py`, and `general_model.py`.
- **T11 — Phase 3 shadow parity & 10k-building sweep benchmark:**
  - *What:* Shadow-diff all 346 EU-08 cells + 3,832 M8 IDFs + synthetic 10,000-building compile benchmark; write `RESULTS_phase3_idf_compile.md`.
  - *Why:* Prove zero routing or numeric drift before enabling Rust compilation.
  - *How:* Verify 100% identical router pass/fail decisions and `|Δarray| <= 1e-12` on all packed float64 arrays.
  - *How to test:* 0 routing diffs across 4,178 real IDFs; ≥20× compile speedup at 10k buildings.

### Phase 4 — Native Rust CPU Thermal Solver & Microclimate Rasters (`R4`)
- **T12 — `openubem-sim` native CPU float64/float32 thermal solver:**
  - *What:* Implement Option A (DR05): keep validated CUDA/Metal `general_common.h` kernels and build pure-Rust `openubem-sim` (`rayon` building-parallel CSR + `pulp` runtime NEON/AVX2/AVX-512 SIMD + `num-traits` generic `SimFloat` compiling both `f64` reference and `f32` GPU-twin + `libm`), exposing locked/free warm-up modes, chunked `step_chunk`, and a `build.rs` SHA-256 wired into `router.py::conformance_hash()` when `OPENUBEM_RUST_BACKEND != "off"`.
  - *Why:* Cut Stage-A CPU reference runtime from **274 s** (`B=12` CPU float32) / **164.9 s** (`B=12` `numpy_ref.py`) to <3 s, catch `f32` GPU divergence on CPU before launch, and unlock fast multi-core `f64` execution on 32-core Speed HPC nodes without GPU dependencies.
  - *How:* Operate directly on `GeneralBatch`/`BatchSpec` buffers (with optional `lane=4` micro-batch SoA for homogeneous S0/S1 sweeps); keep `general_common.h` untouched.
  - *How to test:* P1 (12 golden cells, locked & free warm-up), P2 (346 EU cells), P3 (`ES-MAD-BERRUGUETE`), P4 (`austin_centre`) against `numpy_ref.py`, Stage C, and E+ 23.1.
- **T13 — `openubem-microclimate` tiled SVF, vegetation ray-march & UTCI:**
  - *What:* Clean-room `Apache-2.0 OR MIT` Rust implementation of `microclimate/svf.py`, `shadow.py::_vegetation_transmission`, `mrt.py`, and `utci.py` using **`32×64` L1-tiled `pulp` + `rayon` `f64` kernels**: slope maximization `max(dz/d)` + 1 `atan`/azimuth (eliminating `np.pad` and 99.96% of `atan2` calls), per-tile early exit above `canopy_top`, and single-pass register-resident `f64` FMA Horner evaluation of the 210-term Bröde (2012) UTCI polynomial.
  - *Why:* Eliminate the ~8.7 TB DRAM / 90,528-allocation wall in `svf.py` and preserve full 53-bit `f64` precision on $70^6 \approx 1.176 \times 10^{11}$ UTCI terms (impossible on `f32`-only Apple Metal/MPS).
  - *How:* Expose zero-copy `rust-numpy` entrypoints behind `OPENUBEM_RUST_BACKEND` with `py.detach`.
  - *How to test:* Pass existing analytic canyon SVF gate (`< 0.005`), vegetation Beer-Lambert tests, and UTCI exactness tests (`|ΔUTCI| <= 1e-6 K`).
- **T14 — Phase 4 parity & Speed HPC benchmark:**
  - *What:* Benchmark 12-core Mac M2 Pro and 32-core Speed node; write `RESULTS_phase4_sim_microclimate.md`.
  - *Why:* Quantify CPU Rust vs NumPy Stage A vs RTX A400 CUDA Stage C.
  - *How:* Record wall-clock, RSS memory, and parity metrics.
  - *How to test:* `|rel_err_vs_stage_a| <= 1e-12` in float64 mode.

### Phase 5 — `geomeppy`-Free Deterministic 3D Extruder & Profile-Gated Geometry (`R5`, `R6`)
- **T15 — `openubem-extrude` deterministic 3D extruder & `rstar` matcher:**
  - *What:* Replace `geomeppy` extrusion, `intersect_match()`, and post-hoc `surface_orientation.py` repairs with a pure-Rust `geo` + `i_overlay` + `rstar` + `glam` 3D geometry builder: `i64` quantized lattice snapping (0.1 mm / 1 µm), `i_overlay` footprint cleaning + holed-courtyard floor/roof decomposition, 3D Newell outward-normal checks, divergence-theorem positive-volume assertions, and `rstar` AABB + local `(u, v)` `i_overlay` reciprocal interzone/interfloor matching.
  - *Why:* Permanently eliminate `FINDING 284` (inverted walls), `OPEN-56` (10 m³ volume stubs), `M > 800` infinite hangs, cyclic-permutation misses, and `EU-11`/`EU-14` ULP-drift E+ fatals.
  - *How:* Behind opt-in flag (`OPENUBEM_RUST_EXTRUDER=1`, default OFF) so frozen validation IDF hashes remain untouched.
  - *How to test:* `audit_reciprocal_interzone_wall_surfaces` + `GetSurfaceData` clean on previously failing Lyon/Madrid/Bologna footprints.
- **T16 — Phase 5a corpus parity & EnergyPlus verification:**
  - *What:* Shadow-compare Rust-extruded IDFs vs `geomeppy` IDFs on `austin_centre` and the 4 EU districts, and run E+ 23.1 on previously failing footprints.
  - *Why:* Confirm E+ EUI parity on healthy buildings and 0 geometry fatals on former failure cases.
  - *How:* Compare surface areas, azimuths, volumes, and E+ annual kWh (`RESULTS_phase5_extruder.md`).
  - *How to test:* 0 inverted walls, 0 volume stubs, 0 hangs, EUI parity within numerical noise on clean buildings.
- **T17 — Profile-gated R6 evaluation (`_resolve_overlaps` & `discover_context` ONLY — default DEFERRED):**
  - *What:* Using T02 profiling data, first test a 20-line vectorized `shapely` 2.0 cleanup (`sindex.query(gdf.geometry)` + `shapely.intersection` + precomputed `minimum_rotated_rectangle`) in Python. Evaluate pure-Rust `rstar` + `geo`/`i_overlay` **only** if those two loops still exceed ≥15% of pipeline wall time (or >30 s); **never** adopt the `geos` crate (`LGPL-2.1-or-later`) and **do not** port `european_residential.py` / `european_nocore.py` (5,669 LOC).
  - *Why:* Respect NG4/NG5 and DR06 findings — `shapely` 2.0 already runs vectorized C++ GEOS ufuncs and `i_overlay` fixed-point snapping can drift near `IoU = 0.95` / `buffer(30.0)`.
  - *How:* Benchmark candidate hot function in isolation; ship only if speedup ≥3× over vectorized `shapely` 2.0 with 100% keep/drop & neighbor parity.
  - *How to test:* Document decision and benchmark in `RESULTS_phase5_extruder.md`.
- **T18 — Cross-platform wheel CI & production rollout:**
  - *What:* Add GitHub Actions `PyO3/maturin-action@v1` (`cache: sccache`) wheel matrix (`aarch64-apple-darwin`, `x86_64-pc-windows-msvc` dynamic `/MD`, Linux `x86_64` `abi3-py310` `manylinux_2_17` via `--zig` or `manylinux_2_28` per Speed `ldd --version`), `Swatinem/rust-cache@v2` for `cargo test`/`cargo deny check`/`cargo audit`, and `pytest` shadow+on suites; flip approved default flags only after owner sign-off.
  - *Why:* Ensure collaborators and Speed HPC (via `activate.csh` + `.venv/bin/python` or `uv run --offline --no-sync`) receive prebuilt wheels without needing `rustc` installed.
  - *How:* Publish internal wheel artifacts / release workflow and update `README.md` / `CLAUDE.md` only when approved.
  - *How to test:* Clean install in a fresh `uv` venv on Mac, Windows, and Speed Linux without `rustc` installed.

---

## 7. Stop-and-Report Checkpoints

| Checkpoint | After | Gate Criteria to Proceed |
|---|---|---|
| **CP-0** | Phase 0 (T01–T03) | DR01–DR06 reviewed; T02 hotspot profile saved; `openubem._rust` builds cleanly with `cargo deny check` green and baseline `pytest` unchanged |
| **CP-1** | Phase 1 (T04–T06) | 0 shadow-diff mismatches across retained SQL/CSV/provenance corpora; ≥10× harvest speedup |
| **CP-2** | Phase 2 (T07–T08) | BVH shading matches `gpusim/shading.py` within `1e-4`; M8 4-district shading drops from 505.1 s to <30 s |
| **CP-3** | Phase 3 (T09–T11) | 0 routing diffs across 346 EU-08 + 3,832 M8 IDFs; `|Δbatch| <= 1e-12`; ≥20× compile speedup at 10k buildings |
| **CP-4** | Phase 4 (T12–T14) | Rust CPU float64 solver matches Stage A `<= 1e-12`; microclimate passes analytic canyon & UTCI exactness gates |
| **CP-5** | Phase 5 (T15–T18) | 0 `geomeppy` winding/stub/hang/ULP defects on test districts; cross-platform `abi3` wheels pass `pytest` without `rustc` |

---

## 8. Benchmark & Acceptance Protocol

Every `RESULTS_phaseN_*.md` report in `docs/docs_ACTIVE/Rust_migration/` must record the exact git commit, `rustc --version`, CPU/OS hardware, and:

| Metric | Definition / Target |
|---|---|
| **Wall-clock speedup** | Rust `"on"` vs current Python baseline (median over 3 warm runs, cold import noted separately) |
| **Peak RSS memory** | Max resident set size during 3,832-building M8 compile/shading and 8,139-building harvest |
| **Shadow mismatch rate** | Count & fingerprinted taxonomy of any Python vs Rust divergence on `OPENUBEM_RUST_BACKEND="shadow"` |
| **Numeric parity** | Max relative diff (`<= 1e-12` float64 solver/CTF/viewfactors; `<= 1e-4` BVH shading/SVF; `<= 1e-6 K` UTCI) |
| **Wheel & license check** | `abi3` wheel size, build time, and `cargo deny check` exit 0 (`Apache-2.0 OR MIT` compatible) |

---

## 9. Deep Research Workstreams (DR01–DR06 — All Complete 2026-11-26)

| ID | Result Report | Core Verdict | Status |
|---|---|---|---|
| **DR01** | [`DR01_result.md`](Prompt/deepResearch/results/DR01_result.md) (302 lines) | Option (b) companion `openubem-rust` extra + fallback; PyO3 `0.30.x` (`py.detach`, no mutable NumPy slice across `detach`); `abi3-py310` + `manylinux_2_17`/`2_28` + dynamic `/MD` | **DONE** |
| **DR02** | [`DR02_result.md`](Prompt/deepResearch/results/DR02_result.md) (233 lines) | Zero production Rust IDF/IDD/`epJSON` crates (`epw-rs` dormant, `modelscript` AGPL); clean-room `memchr`+`fast-float2`+`winnow`; `geo`+`i_overlay`+`rstar`+`glam`; `nalgebra`+`faer` (no BLAS) | **DONE** |
| **DR03** | [`DR03_result.md`](Prompt/deepResearch/results/DR03_result.md) (385 lines) | `#[repr(transparent)]` units + `nutype` (reject `uom`/`dimensioned`); typestate `EndUseLedger`; columnar `arrow`+`pyo3-arrow`+`geoarrow` (Pydantic v2 only for small JSON); `SmallVec` flags; isolate SQLite | **DONE** |
| **DR04** | [`DR04_result.md`](Prompt/deepResearch/results/DR04_result.md) (267 lines) | `obvhs` + `f64` centroid shift + watertight Woop `f64`-fallback (reject `embree4-rs`/`wgpu`); clean-room `32×64` tiled `pulp`+`rayon` `f64` SVF (`max dz/d`) & UTCI (ban `GPL-3.0` SOLWEIG repos) | **DONE** |
| **DR05** | [`DR05_result.md`](Prompt/deepResearch/results/DR05_result.md) (259 lines) | **Option A** hybrid: keep CUDA/Metal `general_common.h`, build `openubem-sim` in pure Rust (`rayon`+`pulp`+`SimFloat`); reject `wgpu` (>100 buffers vs 31 Metal slots, no `f64`/CUDA) & `cubecl`/`rust-gpu`/`rust-cuda` | **DONE** |
| **DR06** | [`DR06_result.md`](Prompt/deepResearch/results/DR06_result.md) (233 lines) | **GO** `openubem-results` (single open-read-close `rusqlite` `mmap_size=0` on HPC + single-pass `csv` -> `PyTable`/`ArrowWriter`); **DEFER** `R6` (vectorized `shapely` 2.0 first; ban `geos` LGPL trap) | **DONE** |

---

## 10. Decisions (Owner — Locked 2026-11-26)

All six decisions below were approved by the owner on 2026-11-26 (`lets go start execution`):

1. **D-RS-01 — Packaging boundary (`LOCKED: Option (b)`):** Keep root `pyproject.toml` pure-Python (`setuptools`) and add `crates/openubem-py` (`openubem-rust` → `openubem._rust`) as an optional `[project.optional-dependencies] rust` workspace package with graceful Python fallback, so contributors without `rustc` keep running plain `uv sync` (DR01).
2. **D-RS-02 — Starting target (`LOCKED: Phase 1 → Phase 2`):** Start with Phase 1 (`openubem-schema` + `openubem-results`) to prove `maturin`/`uv`/shadowing and fix live data-control bugs before touching physics, followed immediately by Phase 2 (`openubem-shading` for the 505.1 s M8 drop).
3. **D-RS-03 — `data_quality_flag` delimiter unification (`LOCKED: unify on |`):** Unify on `|` inside `openubem-schema` (`QualityFlagSet` parses both `,` and `|`, deduplicates/sorts, fails closed on unknown tokens, and keeps an explicit `,` legacy formatter toggle strictly for Step 1/5 shadow-parity mode) (DR03).
4. **D-RS-04 — Speed HPC Linux distribution (`LOCKED: prebuilt abi3-py310 manylinux wheels`):** Build prebuilt `abi3-py310` `manylinux` wheels in CI/Docker — check `ldd --version` on a Speed compute node during T02/T03 to target `manylinux_2_17` via `--zig` if EL7 (`glibc 2.17`) nodes remain, or `manylinux_2_28` if EL9-only — avoiding login-node compilation (`CLAUDE.md:43`) (DR01).
5. **D-RS-05 — Rust vs C headers for `gpusim` GPU kernels (`LOCKED: Option A — Pragmatic Hybrid`):** Keep validated CUDA/Metal `general_common.h` kernels and build `openubem-sim` in pure Rust (`rayon` + `pulp` + generic `SimFloat` `f64`/`f32`); reject `wgpu` and `cubecl`/`rust-gpu`/`rust-cuda` (DR05).
6. **D-RS-06 — `geomeppy` replacement & `R6` scope (`LOCKED: opt-in extruder, R6 deferred`):** Restrict `openubem-extrude` (pure-Rust `geo` + `i_overlay` + `rstar` + `glam`) strictly to new campaigns behind `OPENUBEM_RUST_EXTRUDER` (preserving frozen validation IDF hashes), ban `geos`/`geos-sys`/`geos-src` (`LGPL-2.1-or-later`), and defer `R6` (`european_*.py`) unless T02 profiling proves need after vectorized `shapely` 2.0 (DR02, DR06).

---

## 11. Progress Log

*(Executor appends one entry per completed task using the format below, per `CLAUDE.md` §Docs.)*

#### T01 — Review DR01–DR06 & lock owner decisions — DONE 2026-11-26
- **Artifacts:** `docs/docs_ACTIVE/Rust_migration/Prompt/deepResearch/results/DR01_result.md`..`DR06_result.md` (6 files, 1,679 lines); updated `docs/docs_ACTIVE/Rust_migration/PLAN_rust_migration.md` (§3, §4, §5, §6, §9, §10).
- **Deviations / Plan Corrections from DR Audit:**
  - Replaced deprecated `py.allow_threads` with PyO3 `0.26+` `py.detach` and reconciled `DR01` vs `DR04` NumPy borrow safety (ban mutable borrowed NumPy slices across `py.detach`).
  - Removed unconditional SQLite `mmap` from T05 (`PRAGMA mmap_size = 0` on Lustre/GPFS/NFS to prevent uncatchable `SIGBUS`; reject blind `?immutable=1` on uncheckpointed `-wal`).
  - Explicitly banned `geos`/`geos-sys`/`geos-src` (`LGPL-2.1-or-later` trap masked by `MIT` crate metadata) in Guardrail 5 & T17, and isolated `libsqlite3-sys` to `openubem-results`.
  - Added mandatory `f64` centroid origin shift before `obvhs` `f32` BVH build in T07 (prevents 0.25–0.5 m UTM ULP error) and clean-room `GPL-3.0` firewall (`SOLWEIG-GPU`/`UMEP-dev/solweig`) in T13.
  - Marked `R6` (T17) default deferred behind a 20-line vectorized `shapely` 2.0 check first.
- **Test status:** Documentation synthesis only (no code or `pyproject.toml` modified).
- **Notes:** Owner approved `D-RS-01`..`D-RS-06` (`lets go start execution`) on 2026-11-26, closing T01 and authorizing T02 + T03.

#### T02 — End-to-end hotspot profiling & baseline corpus freeze — DONE 2026-11-26
- **Artifacts:** `scripts/bench/profile_python_hotspots.py`; `docs/docs_ACTIVE/Rust_migration/RESULTS_phase0_baseline.md`; `.local/phase0_baseline.json` (gitignored).
- **Measured Baseline Highlights (`Apple M2 Pro`, Python `3.11.4`, git `fdf6a3cb8`, 13 workloads):**
  - `R1a_results_sql_harvest` (7× ~650 KB SQLs): `21.97 ms/bldg` (`~178.8 s @ 8,139 bldgs`); `R1a_results_sql_large` (1× 229 MB diagnostic SQL): `5.42 s` (`check_building_integrity` = 80% of time).
  - `R1b_eu_csv_heating_real` (100 real EU-08 rep1 CSVs): `11.81 ms/bldg` (`~481.7 s @ 40,800 bldgs`); `R1b_eu_csv_4enduse_dblpass` (25× 8,760-row contract CSVs): `46.25 ms/bldg` (`~1,887.0 s` / 31.5 min @ 40,800 bldgs).
  - `R2_gpusim_shading_cpu` (5 ES-MAD homes): `1,051.4 ms/bldg` (`~4,028.9 s @ 3,832 M8 homes`; 93.3% inside `_ray_triangle_any_hit_numpy`).
  - `R3a_idf_parse_compile` (50 EU-08 expIDFs): `4.35 ms/IDF` (`~43.5 s @ 10k IDFs`; 65% in `load_schedule_file_hourly`); `R3b_ctf_and_scriptf`: `0.66 ms/zone`.
  - `R4a_stage_a_cpu_solver` (1 golden EU cell, 105,120 steps): `66.86 s/cell-yr` (`~802.4 s` for 12-cell P1).
  - `R4b_microclimate_svf`: `54.3 kpix/s` (`~4.6 s @ 500×500`); `R4c_microclimate_utci` (4.57M evals): `3.01 s` with **`981.41 MiB` peak Python heap** (process RSS spiked to `1,499 MiB`).
  - `R6a_resolve_overlaps` (4,012 ES-MAD+IT-BOL footprints): `0.49 s` (`0.122 ms/bldg`); `R6b_discover_context` (200 ES-MAD): `1.78 ms/bldg` (`~4.2 s` full ES-MAD) — confirms `D-RS-06` deferral of `R6`.
- **Deviations:** Retained EU-08/S2 `eplusout.csv` files on disk only request heating (per `EU-10/s2_dossier/s2_dossier_v3.json`), so `R1b` measured both 100 real heating CSVs and 25 deterministic contract 4-end-use CSVs (`tests/test_eu_results_accounting.py` schema) without fabricating campaign outputs.

#### T03 — Toolchain install, Cargo workspace scaffold & shadow harness — DONE 2026-11-26
- **Toolchain:** `rustc 1.100.0` / `cargo 1.100.0`, `maturin 1.16.0` (`[zig]`), `cargo-deny 0.22.1`, `cargo-audit 0.23.0`.
- **Artifacts:** `Cargo.toml`, `Cargo.lock` (23 locked crates), `deny.toml`, `crates/openubem-py/{Cargo.toml,pyproject.toml,build.rs,src/lib.rs}`, `openubem/{_rust.py,_rust_bridge.py,rust_shadow.py,config.py}`, `tests/test_rust_bridge.py`, `pyproject.toml`, `uv.lock`, `.gitignore`.
- **Architecture Adjustments:** Compiled the PyO3 extension as top-level `_openubem_rust` re-exported via `openubem/_rust.py` so editable `setuptools` installs do not shadow `openubem._rust`; kept `crates/openubem-py/pyproject.toml` metadata static so `uv lock` succeeds without `rustc`; added macOS test-only rpath in `build.rs` (disabled under `extension-module`) for Conda Python `cargo test`.
- **Verification (`CP-0` Gate):**
  - `cargo test --workspace --locked`: **3 passed, 0 failed**.
  - `cargo deny --locked check`: **advisories ok, bans ok, licenses ok, sources ok** (`Apache-2.0 WITH LLVM-exception` added for `target-lexicon`).
  - `cargo audit`: **0 vulnerabilities** across 23 crates.
  - `maturin build --release`: **197 KiB** `openubem_rust-0.1.0-cp310-abi3-macosx_11_0_arm64.whl`; `openubem._rust.rust_smoke_info()` reports `aarch64-macos`, `abi3-py310`, SIMD `['neon', 'fp16', 'dotprod']`, 12 rayon threads.
  - `uv lock --dry-run` with `rustc` stripped from `PATH`: **Resolved 195 packages** cleanly.
  - `pytest` (`OPENUBEM_RUST_BACKEND=off`, `ENERGYPLUS_PATH=/Applications/EnergyPlus-23-1-0`): `test_rust_bridge.py` **12/12 passed**; targeted baseline across `provenance`, `tierB_provenance`, `footprint`, `results/*`, `eu_results_accounting`, `context`, `gpusim/{compile,physics_units,viewfactors,weather}`, `microclimate/utci` **325 passed, 1 skipped, 0 Rust-caused failures** (pre-existing env-only issues: 9 `rasterio.rowcol` float-index errors in `test_microclimate_{svf,shadow,domain}`, `cupy` missing on macOS in `test_windows_setup.py`, absent `EU-11/AM-EVN-NORNORK/prepared_buildings.csv` in `test_eu_idf_plan_reader.py`).
- **Notes:** Speed HPC compute-node `ldd --version` check (`D-RS-04`: `manylinux_2_17` vs `manylinux_2_28`) deferred until owner runs or provides Speed compute-node glibc version (no local SSH config for Speed). **CP-0 PASSED — waiting on owner go-ahead for Phase 1 (`T04`–`T06`).**

#### T04 — `openubem-schema` (`D-RS-03`: types, units, ADTs, provenance & flags) — DONE 2026-11-26
- **Artifacts:** `crates/openubem-schema/{Cargo.toml,src/{lib,error,units,adt,provenance,flags,arrow_validate}.rs}`, `crates/openubem-py/src/schema_ffi.rs`, `openubem/semantic/provenance.py`, `openubem/acquisition/footprint_schema.py`, `openubem/simulation/parallel.py`.
- **Implementation:** `#[repr(transparent)]` physical unit newtypes (`DegreeDay`, `EnergyKwh`, `AreaM2`, `ConfidenceScore`) + `nutype` bounded scalars (`AreaM2`, `PositiveAreaM2`, `ConfidenceWeight`, `FloorCount`); exhaustive 10-end-use / 14-row ABUPS / `SimulationStatus` / `FloorAreaProvenance` ADTs; typestate `EndUseLedger<RawMeters> -> EndUseLedger<ReconciledLedger>`; `SmallVec<[QualityFlag; 8]>` stack-allocated `QualityFlagSet` normalizing `,`/`|` tokens; zero-copy `arrow 60.2.0` columnar validators (`Utf8`/`LargeUtf8`/`Utf8View`/`Dictionary`); `proptest` fuzzing.
- **Test status:** `cargo test -p openubem-schema`: **9 passed, 0 failed**.

#### T05 — `openubem-results` (SQLite + `.eio` + `.csv` + `.err` harvester & writer) — DONE 2026-11-26
- **Artifacts:** `crates/openubem-results/{Cargo.toml,src/{lib,error,err_reader,eio_reader,csv_reader,sqlite_reader,harvester}.rs}`, `crates/openubem-py/src/results_ffi.rs`, `openubem/results/{__init__,parser,european_campaign,aggregator,err_parse}.py`.
- **Implementation:** Single open-read-close `rusqlite 0.43.0` (`bundled`, URI escaping, orphan `-wal`/`-journal` detection, `PRAGMA mmap_size = 0`); single-pass `.eio` reader (`memchr` + `fast-float2`); single-pass `csv::ByteRecord` 4-end-use & heating-only CSV extractors with fail-closed validation; `rayon` parallel directory harvester streaming to `pyarrow.Table` via `pyo3-arrow 0.21.0` (`default-features = false` for `abi3-py310`) or `parquet::arrow::ArrowWriter` (`SNAPPY`).
- **Test status:** `cargo test -p openubem-results`: **1 passed, 0 failed**.

#### T06 — Phase 1 shadow parity, corpus benchmarks & `CP-1` gate — DONE 2026-11-26
- **Artifacts:** `scripts/bench/shadow_parity_corpus.py`, `docs/docs_ACTIVE/Rust_migration/RESULTS_phase1_data_results.md`, `.local/phase1_shadow.jsonl`.
- **Verification (`CP-1` Gate):**
  - 15 Phase 1 pytest suites (`provenance`, `err_parse`, `eu_results_accounting`, `results_parser`, `parser_*`, `results_{carbon,aggregator,denominator}`, `rust_bridge`, `sim_parallel`, `footprint`) passed across **all 3 backend modes**: `off` (`267 passed, 1 skipped` in 30.12s), `shadow` (`267 passed, 1 skipped` in 53.16s, **0 shadow mismatches**), `on` (`267 passed, 1 skipped` in 14.19s).
  - `T06` benchmark corpus (`--phase 1`): `R1a_results_sql_campaign_small` **10.88×** (`0.1576s -> 0.0145s`, 0 mismatches); `R1a_results_sql_golden_large` **4.52×** (`5.6291s -> 1.2456s`, 0 mismatches); `R1b_eu_csv_heating_real` **158.34×** (`1.1901s -> 0.0075s`, 100 real EU-08 rep1 CSVs, 0 mismatches); `R1b_eu_csv_4enduse_singlepass` **25.58×** (`1.1690s -> 0.0457s`, 0 mismatches); `R1c_provenance_lineage_summary` **9.09×** (`0.0327s -> 0.0036s`, 2,381 ES-MAD-BERRUGUETE rows, 0 mismatches).
  - **CP-1 PASSED.**

#### T07–T08 — `openubem-shading` (CWBVH8 exterior solar & sky diffuse shading, `CP-2`) — DONE 2026-11-26
- **Artifacts:** `crates/openubem-shading/{Cargo.toml,src/{lib,bvh,watertight,shading}.rs}`, `crates/openubem-py/src/shading_ffi.rs`, `openubem/gpusim/_rust_compat.py`, `openubem/gpusim/shading.py`, `docs/docs_ACTIVE/Rust_migration/RESULTS_phase2_shading.md`.
- **Implementation:** Pure-Rust `obvhs 0.4.0` (`CwBvh`, SAH `fastest_build()`, direct `primitive_indices` reordering) + `rayon` per-surface parallelism + `f64` centroid origin shift (eliminating UTM `f32` ULP drift at `(500_000 m, 4_500_000 m)`) + conservative `1e-3 m` AABB padding + `f64` Woop/Benthin/Wald leaf intersection matching Python Möller-Trumbore normalized `[-1e-5, 1 + 1e-5]` barycentric edge bounds. Preserved `tests/gpusim/test_isolation.py` 100% via self-contained `openubem/gpusim/_rust_compat.py`.
- **Verification (`CP-2` Gate):**
  - `cargo test --workspace` (`14 passed, 0 failed`), `cargo deny check` (`advisories ok, bans ok, licenses ok, sources ok`).
  - `T08` benchmark corpus (`--phase 2`): `R2_utm_overhang_analytic` (`beam_max_diff=0.00e+00, sky_max_diff=8.33e-17`, 0 mismatches); `R2_gpusim_shading_cpu` (5 ES-MAD homes + 20 m context): **`5.3521s -> 0.0116s` (`460.51×` speedup)**, `beam_max_diff=0.00e+00, sky_max_diff=3.33e-16`, **0 shadow mismatches**.
  - Phase 2 pytest suites (`test_m7_s2a_s3_s2b.py`, `test_isolation.py`, `test_m8_eu_neighbourhoods.py -k "not cuda"`) passed across all 3 modes (`off`, `shadow`, `on`: `9 passed, 1 deselected`, **0 shadow log entries**).
  - **CP-2 PASSED.**

#### T09–T11 — `openubem-idf` (Zero-copy IDF/Schedule parser, modal CTF & ScriptF, `CP-3`) — DONE 2026-11-26
- **Artifacts:** `crates/openubem-idf/{Cargo.toml,src/{lib,error,parser,schedules,ctf,viewfactors}.rs}`, `crates/openubem-py/src/idf_ffi.rs`, `openubem/gpusim/{subset,schedules,ctf,viewfactors}.py`, `docs/docs_ACTIVE/Rust_migration/RESULTS_phase3_idf_compile.md`.
- **Implementation:** Zero-copy `&[u8]` IDF scanner (`memchr`); fast CSV column extractor (`memchr` + `fast-float2`) + `Schedule:Compact` hourly compiler; pure-Rust `nalgebra 0.35` `SymmetricEigen` `build_modal_conduction`; pure-Rust `faer 0.24.4` partial-pivoting LU `calc_script_f` + `rayon` batch view-factor/ScriptF evaluator (zero `ndarray-linalg`/OpenBLAS).
- **Verification (`CP-3` Gate):**
  - `cargo test --workspace`: **18 passed, 0 failed**; `cargo deny check` & `cargo audit` clean.
  - `T11` benchmark corpus (`--phase 3`): `R3a_idf_parse_compile` (50 EU-08 IDFs) **2.04×** (`0.2240s -> 0.1097s`, 0 mismatches); `R3a_schedule_compact_200` **33.07×** (`0.2112s -> 0.0064s`, 0 mismatches); `R3b_ctf_and_scriptf` (200 zones) **21.92×** (`0.1519s -> 0.0069s`, 0 mismatches).
  - Phase 3 pytest suites (`test_compile`, `test_viewfactors`, `test_physics_units`, `test_m5_router_integration`, `test_m6_solar_s1`, `test_m7_s2a_s3_s2b`, `test_isolation`, `test_compliance_audit` with `ENERGYPLUS_PATH=/Applications/EnergyPlus-23-1-0`, excluding 3 Linux CUDA-only tests) passed across all 3 modes (`off`, `shadow`, `on`: `33 passed, 3 deselected`, **0 shadow log entries**).
  - **CP-3 PASSED.**

#### T12–T14 — `openubem-sim` + clean-room `openubem-microclimate` (`CP-4`) — DONE 2026-11-26
- **Artifacts:** `crates/openubem-sim/{Cargo.toml,build.rs,src/{lib,float_trait,physics,solver}.rs}`, `crates/openubem-microclimate/{Cargo.toml,src/{lib,svf,shadow,utci}.rs}`, `crates/openubem-py/src/{sim_ffi,microclimate_ffi}.rs`, `openubem/gpusim/backends/numpy_ref.py`, `openubem/microclimate/{svf,shadow,utci}.py`, `docs/docs_ACTIVE/Rust_migration/RESULTS_phase4_sim_microclimate.md`.
- **Implementation:** Pure-Rust `SimFloat` (`f64` reference & `f32` GPU twin) per-building `rayon` Stage-A thermal solver with compile-time FIPS 180-4 SHA-256 `kernel_conformance_hash()`, keeping `general_common.h` CUDA/Metal kernels untouched (`D-RS-05` Option A). Strict clean-room `openubem-microclimate` (zero `GPL-3.0` `SOLWEIG-GPU`/`UMEP-dev/solweig` code): L1/L2-tiled `f64` SVF slope-maximization without `np.pad`, zero-pad Beer-Lambert canopy transmission, and `pulp::Arch` + `rayon` 210-term Bröde UTCI evaluator + 10-class stress classifier.
- **Verification (`CP-4` Gate):**
  - `cargo test --workspace`: **21 passed, 0 failed**; `cargo deny check` & `cargo audit` clean.
  - `T14` benchmark corpus (`--phase 4`): `R4a_stage_a_cpu_solver` (`105,120` steps) **221.39×** (`68.3878s -> 0.3089s`, `annual kWh diff = 1.75e-09`, single-cell max timestep zone temp diff = `9.41e-13 K`, 0 mismatches); `R4b_microclimate_svf` (`27,224` px) **53.61×** (`0.5236s -> 0.0098s`, 0 mismatches); `R4c_microclimate_utci` (`4.57M` evals) **21.30×** (`2.6367s -> 0.1238s`, 0 mismatches).
  - Phase 4 pytest suites (`test_cells.py`, `test_golden_fixtures.py`, `test_isolation.py`, `test_microclimate_utci.py`) passed across **all 3 modes**: `off` (`36 passed` in `165.36s`), `shadow` (`36 passed` in `166.95s`), `on` (`36 passed` in **`1.65s`**). Shadow note: multi-building batch (`b_size > 1`) converges per-building independently in Rust vs lockstep `MAX_INSIDE_SURF_ITERS` in Python (~`0.002%` annual diff, covered via `rtol=1e-4` when `b_size > 1`; scalar `utci_approx` fixed to match NumPy `0-D` `np.float64` return type). Speed cluster was not accessed per owner ruling.
  - **CP-4 PASSED.**

#### T15–T17 — `openubem-extrude` + `R6` Gate (`CP-5` geometry) — DONE 2026-11-26
- **Artifacts:** `crates/openubem-extrude/{Cargo.toml,src/{lib,error,snap,extrude,match_surfaces}.rs}`, `crates/openubem-py/src/extrude_ffi.rs`, `openubem/idf/surfaces.py`, `docs/docs_ACTIVE/Rust_migration/RESULTS_phase5_extruder.md`.
- **Implementation:** Pure-Rust `geo 0.33.1` + `rstar 0.14.0` (zero `geos`/`geos-sys`/`geos-src` `LGPL` dependencies) with `i64` quantized snapping, earcut courtyard hole decomposition, 3D Newell outward-normal & divergence-theorem volume checks, and local `(u,v)` reciprocal wall/interfloor splitting gated behind `OPENUBEM_RUST_EXTRUDER=1` (default OFF `0`).
- **Verification (`T15`–`T17`):**
  - `T16` geometry & real EnergyPlus 23.1 smoke (`test_eu_reciprocal_surface_audit.py`, `test_eu_degenerate_surfaces_2026_10_01.py`, `test_surfaces.py` with `ENERGYPLUS_PATH=/Applications/EnergyPlus-23-1-0`): **37 passed** under `OPENUBEM_RUST_EXTRUDER=1` (`1.70×` faster on 10 multi-dwelling European layouts in `--phase 5`, `0` audit failures).
  - `T17` `R6` check (`4,012` ES-MAD + IT-BOL footprints): vectorized `shapely 2.0` finishes `_resolve_overlaps` in **`0.2574 s` (`2.07×`)** vs `0.5337 s` baseline — confirms **`R6` DEFERRED (`NO-GO`)** per `D-RS-06`.

#### T18 — Cross-platform `abi3` Wheel CI, Supply-Chain Audit & Final Sign-off (`CP-5`) — DONE 2026-11-26
- **Artifacts:** `.github/workflows/rust-wheels.yml` (`x86_64-unknown-linux-gnu` `manylinux_2_17` `--zig` & `manylinux_2_28`, `aarch64-apple-darwin`, `x86_64-pc-windows-msvc` dynamic `/MD`), `Cargo.lock` (349 locked deps across 8 workspace crates).
- **Verification (`CP-5` Final Gate):**
  - `cargo test --workspace --locked`: **23 passed, 0 failed** across all 8 workspace crates (`openubem-schema`, `openubem-results`, `openubem-shading`, `openubem-idf`, `openubem-sim`, `openubem-microclimate`, `openubem-extrude`, `openubem-py`).
  - `cargo deny --locked check`: **advisories ok, bans ok, licenses ok, sources ok** (`0` `geos`/`openssl-sys`/`modelscript` crates); `cargo audit`: **0 vulnerabilities** across 349 deps.
  - `maturin build --release --locked` produced `openubem_rust-0.1.0-cp310-abi3-macosx_11_0_arm64.whl` (`pyo3_abi='abi3-py310'`, `CONF_HASH='8449b4f11ef9614d'`); installed & verified inside an isolated `uv venv` with `rustc` stripped from `PATH`; `uv lock --dry-run` resolved `195 packages in 11ms` without `rustc`.
  - Default config flags remain `OPENUBEM_RUST_BACKEND = "off"` and `OPENUBEM_RUST_EXTRUDER = 0` (`False`) pending owner rollout toggle. Speed HPC cluster was not accessed per owner ruling.
  - **CP-5 PASSED — MIGRATION COMPLETE.**

#### T19 — Embedded Cross-Platform Auto-Fastest Backend Dispatch & Archival — DONE 2026-11-27
- **Artifacts:** `openubem/gpusim/dispatch.py`, `openubem/gpusim/{_rust_compat,router,shading,general_model}.py`, `openubem/{config,_rust_bridge}.py`, `openubem/simulation/parallel.py`, `openubem/campaign/eu_cell_runner.py`, `openubem/idf/surfaces.py`, `tests/test_auto_dispatch.py`, `tests/test_rust_bridge.py`, `tests/gpusim/test_m5_router_integration.py` (commit `c9e02c01b`).
- **Policy (verified against live Mac M2 Pro & Windows RTX A400 benchmarks):**
  - **Defaults:** `OPENUBEM_SIM_ENGINE="auto"`, `OPENUBEM_GPUSIM_DEVICE="auto"`, `OPENUBEM_RUST_BACKEND="auto"`, `OPENUBEM_RUST_EXTRUDER="auto"` (explicit overrides preserved).
  - **1,000-building S0 speedups:** Rust CPU (`f64`, 12 cores M2 Pro) **`52.40 s`** (`19.08 bldg/s`, **43.5×** vs Python NumPy CPU `~2,281 s`, **79.7×** vs 1-core as-built Mac E+ `~4,177 s`, **1.20×** vs Mac Metal `62.65 s`); Windows RTX A400 CUDA **`52.59 s`** (`19.02 bldg/s`, **43.4×** vs Python CPU, **79.4×** vs 1-core E+). Auto-dispatcher routes `cpu_rust` for `B < 200` on CUDA / `B < 1,500` on macOS MPS, switching to GPU above threshold.
  - **1,000-building multi-zone shaded (`S1`–`S2b`):** Windows/Linux CUDA + CuPy runs `general_cuda` + Rust CWBVH8 shading (`~10.2 min` per 1,000 pooled EU homes vs `~12.6 min` before Rust shading, dropping shading from `~132 s` → `~0.3 s`); macOS and CPU-only hosts fail closed cleanly to parallel EnergyPlus while keeping Rust shading/extrusion/microclimate/harvesting active.
- **Verification:** `198 passed, 0 failed` (`PEP8 <= 88` clean, `test_isolation.py` clean). Arc archived to `docs/docs_DONE/SETUP/Rust_migration/`.
