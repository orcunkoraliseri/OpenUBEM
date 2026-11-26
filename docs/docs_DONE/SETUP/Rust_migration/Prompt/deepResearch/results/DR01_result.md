# DR01 Result — Hybrid Python-to-Rust Migration Architecture, Shadow Verification & Cross-Platform Tooling

**Feeds:** [`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md) §0, §3, §5, Phase 0 (T01–T03), and Owner Decisions D-RS-01, D-RS-04  
**Date:** 2026-11-26  
**Project Licence Policy:** `Apache-2.0 OR MIT` ([`pyproject.toml`](../../../../../../pyproject.toml))  

---

## Executive Summary

1. **Verification—not Rust code generation—dominates migration risk.** In Anthropic's November 25, 2026 post-mortem (*"Migrating our Messages API to Rust"*), Claude generated the initial Rust port in ~1 week, yet **98% of integration tests passed while ~75% of live traffic initially diverged** (>100 assertions had been silently weakened), requiring April–September 2026 production shadow-diffing and mismatch fingerprinting before cutover (~70% less CPU, >80% less memory, ~20% faster median TTFT).
2. **Adopt the "Thin Python Facade + Coarse-Grained Rust Core" boundary (`pydantic-core`, Polars, `obstore`, `arro3`).** Crossing the PyO3 FFI boundary costs ~20–30 ns per call (~67–70 ns PyO3 no-op vs ~43 ns pure Python); functions doing <100 ns of work or iterating row-by-row over `PyList`/`Vec<T>` lose to pure Python. Cross the boundary once per batch/district/raster with zero-copy NumPy or Arrow buffers.
3. **Select Packaging Option (b) for D-RS-01: keep root `openubem` as a pure-Python `setuptools` package and add `crates/openubem-py` (`openubem-rust`, exposing `openubem._rust`) as an optional `[tool.uv.workspace]` member with graceful Python fallback.** Option (a) (root `build-backend = "maturin"`) breaks editable workflows for contributors without `rustc`/`cargo` and forces Rust rebuilds on Python-only edits. Note that `uv_build` supports pure Python only (cannot compile Rust) and `uv` does not yet support optional missing workspace paths ([`astral-sh/uv#13670`](https://github.com/astral-sh/uv/issues/13670)), so `openubem-rust` must stay an optional extra (`[project.optional-dependencies] rust = ["openubem-rust"]`) paired with prebuilt wheels or explicit fallback.
4. **Target PyO3 `0.30.x` (`0.30.1`, Oct 2026) + `rust-numpy` `0.30.0` + `pyo3-arrow` `0.21.0`—and strictly isolate `pyo3` inside `crates/openubem-py`.** Note the PyO3 `0.26+` API rename: `Python::allow_threads` is now `Python::detach` (and `with_gil` is `attach`). Core domain crates (`openubem-schema`, `openubem-shading`, etc.) must remain pure Rust with zero `pyo3` dependencies so `cargo test`, `proptest`, and `criterion` run standalone.
5. **Never hold a borrowed `&[T]` / `ArrayView` to a NumPy buffer across `py.detach` (`allow_threads`) unless provenance/immutability is guaranteed.** Because NumPy arrays are mutable from Python, releasing the GIL allows concurrent Python threads to mutate or free the buffer while Rust reads it—causing undefined behavior (aliasing/data races). Furthermore, `PyReadonlyArray::as_slice()` rejects non-contiguous/strided slices, and `abi3` restricts `BufferViewMut`. Copy small inputs to owned `Vec<T>` or enforce contiguous, unaliased ownership before `py.detach`.
6. **Use Arrow PyCapsule (`__arrow_c_array__` / `__arrow_c_stream__`) via `pyo3-arrow` for tables/GeoDataFrames, `rust-numpy` for `[B, S]`/`[8760, S]` tensors, and columnar SoA/Arrow batches (not per-building `PyDict`/PyObject lists) for IDF compilation.** `orjson` and `pydantic-core` show that walking Python objects one-by-one incurs CPython allocation/refcount overhead; passing raw IDF paths/bytes or columnar Arrow batches keeps thousands of buildings inside Rust.
7. **Build an Anthropic-style differential shadow harness (`OPENUBEM_RUST_BACKEND = "off" | "shadow" | "on"`, default `"off"`) with tolerance bucketing, canonical hashing, and structural diff fingerprinting.** `rayon`'s work-stealing `fold_with`/`reduce` changes floating-point accumulation trees dynamically across runs; use sequential final reductions, `.with_min_len()`, Kahan/Neumaier summation, or scaled integer `i64` accumulators where bit-exactness is required, and bucket `pytest` checks into bit-exact (`<= 1e-12`), solver (`rtol=1e-12`), and geometric/ray (`atol=1e-4` / `0.005`) gates.
8. **Ship `abi3-py310` wheels with `generate-import-lib`, dynamic MSVC CRT (`/MD`), and cluster-verified `manylinux` targeting.** Never enable `+crt-static` on Windows `cdylib` wheels (dual-CRT heap crashes with CPython `/MD`). On Concordia Speed HPC (which spans legacy Scientific Linux 7 / EL7 `glibc 2.17` and AlmaLinux 9 / EL9 `glibc 2.34` with `tcsh` login shells and no root), verify compute-node `ldd --version`: use `maturin build --release --zig --manylinux 2_17` if EL7 nodes remain, or `manylinux_2_28` if EL9-only, activate with `source .venv/bin/activate.csh`, and execute SLURM jobs via `.venv/bin/python` or `uv run --offline --no-sync`.

---

## Table 1: Python + Rust Projects & Crates Reference

*(All metrics, versions, licences, and release dates retrieved via search on 2026-11-26. All listed crates/projects use permissive licences compatible with OpenUBEM's `Apache-2.0 OR MIT` policy, except `orjson` which includes `MPL-2.0` as one of three tri-license options; no GPL/AGPL crates are included. Where exact download counts or star counts were not returned in search output, they are marked `UNVERIFIED`.)*

| Name | URL | PyO3 / Maturin / ABI Setup | FFI Mechanism | Licence (SPDX) | Stars / Downloads / Activity | Key Takeaway for OpenUBEM |
|---|---|---|---|---|---|---|
| **`pydantic-core`** (`pydantic/pydantic`) | [github.com/pydantic/pydantic](https://github.com/pydantic/pydantic) · [pypi.org/project/pydantic-core](https://pypi.org/project/pydantic-core/) | PyO3 + `maturin`; **non-`abi3`** versioned wheels (+ PyPy support) for max CPython/PyPy speed | Direct `PyObject`/JSON walking in Rust (`jiter`, `speedate`); thin Python `pydantic` facade | `MIT` | ~1.8k stars (archived standalone repo, merged into `pydantic/pydantic`); v`2.50.5` (late 2026); **Active** | Coarse-grained validation of JSON/configs in Rust beats Python 4×–50× (~17× avg), but avoids row-by-row Python object creation for large tables. |
| **`uv`** (`astral-sh/uv`) | [github.com/astral-sh/uv](https://github.com/astral-sh/uv) | Pure-Rust Cargo workspace; distributed via `maturin` / binary wheels on PyPI | CLI binary (no PyO3 extension FFI); manages Python `uv_build` & `maturin` workspaces | `MIT OR Apache-2.0` | ~90k+ stars; **Active** (2026) | Workspace manager for OpenUBEM; supports `cache-keys`, `no-build-isolation-package`, `activate.csh`, and `--offline --no-sync` on HPC. |
| **`ruff`** (`astral-sh/ruff`) | [github.com/astral-sh/ruff](https://github.com/astral-sh/ruff) | Cargo workspace; `crates/ruff` packaged for PyPI via `maturin` | CLI binary invoked over files (no per-token Python FFI) | `MIT` | ~50k+ stars; **Active** (2026) | Proves Cargo workspace separation (pure-Rust crates + thin packaging wrapper) scales cleanly across platforms. |
| **`polars`** (`pola-rs/polars`) | [github.com/pola-rs/polars](https://github.com/pola-rs/polars) · [pypi.org/project/polars](https://pypi.org/project/polars/) | `py-polars` adapter crate using PyO3 + `maturin` + **`abi3`** limited API | Apache Arrow columnar memory + Arrow C Data / PyCapsule Interface; releases GIL for Rust compute | `MIT` | ~40k+ stars; v`2.2.0` (late 2026); **Active** | Canonical "Core crates (no PyO3) + thin `py-*` adapter + coarse Arrow buffer handoff" pattern OpenUBEM should mirror. |
| **`tiktoken`** (`openai/tiktoken`) | [github.com/openai/tiktoken](https://github.com/openai/tiktoken) | PyO3 + `Cargo.toml` Rust extension | String/byte slices across PyO3 boundary; batching amortizes `&str`/`PyString` conversion | `MIT` | ~19.7k stars; v`0.14.0` (Aug 2026); **Active** | Small-string calls in tight Python loops lose throughput to `PyString` allocation; batch inputs before crossing FFI. |
| **`safetensors`** (`safetensors/safetensors`) | [github.com/safetensors/safetensors](https://github.com/safetensors/safetensors) | PyO3 + `maturin` (`bindings/python`) + **`abi3`** wheels (`abi3-py310` floor since v0.8.0) | Zero-copy `memmap2` file mapping + bounded JSON header + GIL-released serialization (`v0.8.0`) | `Apache-2.0` | ~4.0k stars; ~15.6M recent / ~38.1M all-time crate downloads; v`0.8.0` (Jun 2026); **Active** | Shows zero-copy `mmap` + strict bounded headers + `abi3` wheels + GIL release (`detach`) across macOS/Windows/Linux. |
| **`orjson`** (`ijl/orjson`) | [github.com/ijl/orjson](https://github.com/ijl/orjson) | `pyo3-ffi` (raw C-API) + `maturin` (PyPI package only, not on crates.io) | Direct `pyo3-ffi` C-API calls avoiding high-level PyO3 wrapper overhead; supports `numpy`/dataclasses | `Apache-2.0 OR MIT OR MPL-2.0` | ~8.3k stars; tens of millions monthly PyPI downloads (`UNVERIFIED` exact); v`3.13.0` (Oct 2026); **Active** | Even `pyo3-ffi` sees boundary overhead on tiny payloads; reserve low-level `pyo3-ffi` only if profiling proves PyO3 dispatch bottlenecks (note `MPL-2.0` option; OpenUBEM excludes non-Apache/MIT deps in `deny.toml`). |
| **`deltalake`** (`delta-io/delta-rs`) | [github.com/delta-io/delta-rs](https://github.com/delta-io/delta-rs) | PyO3 + `maturin` + **`abi3`** (`abi3-py38`+) | Apache Arrow + DataFusion 55 / Arrow 59 FFI zero-copy | `Apache-2.0` | ~3.4k+ stars; `deltalake` v`1.6.6` / core `1.0.0` (late 2026); **Active** | Large Rust ecosystem (`arrow`, `datafusion`, `parquet`) cleanly ships single `abi3` wheels per OS/arch via `maturin`. |
| **`arro3` / `pyo3-arrow`** (`kylebarron/arro3`) | [github.com/kylebarron/arro3](https://github.com/kylebarron/arro3) · [crates.io/crates/pyo3-arrow](https://crates.io/crates/pyo3-arrow) | PyO3 + `maturin` (`pyo3-arrow` Rust crate + `arro3` Python packages) | Arrow **PyCapsule Interface** (`__arrow_c_array__`, `__arrow_c_stream__`); zero hard `pyarrow` compile dep | `MIT OR Apache-2.0` | ~269 stars; `pyo3-arrow` ~562k recent / ~7.7M all-time downloads; `py-v0.9.0` / `0.21.0` (2026); **Active** | Best FFI bridge for passing Step 1–5 Arrow tables, GeoParquet batches, and `pyarrow`/`pandas`/`polars` frames without copying. |
| **`geoarrow-rs`** (`geoarrow/geoarrow-rs`) | [github.com/geoarrow/geoarrow-rs](https://github.com/geoarrow/geoarrow-rs) | PyO3 + `pyo3-geoarrow` + `pyo3-arrow` + `maturin` | Native `arrow-rs` GeoArrow arrays exported zero-copy via Arrow PyCapsule | `MIT OR Apache-2.0` | ~430+ stars; `geoarrow` v`0.9.0` (Sep 2026), `geoarrow-pyarrow` `0.3.0` (Sep 2026); **Active** | Pure-Rust Apache/MIT spatial buffers without linking LGPL `geos-sys`; avoids Shapely object overhead if kept columnar. |
| **`obstore`** (`developmentseed/obstore`) | [github.com/developmentseed/obstore](https://github.com/developmentseed/obstore) | PyO3 (`0.30` in v0.12.0) + `maturin` + **`abi3`** | `pyo3-object_store` + optional Arrow-backed directory listings (`return_arrow=True`) | `MIT` | ~840+ stars; v`0.12.0` (Oct 2026); **Active** | Returning Arrow tables instead of lists of Python `dict`s removes Python heap allocation bottlenecks on bulk metadata. |
| **`pyo3`** (`PyO3/pyo3`) | [github.com/PyO3/pyo3](https://github.com/PyO3/pyo3) · [crates.io/crates/pyo3](https://crates.io/crates/pyo3) | Core FFI binding crate (`extension-module`, `abi3-py310`, `generate-import-lib`) | `Bound<'py, T>`, `py.detach` (renamed from `allow_threads` in 0.26+), `IntoPyObject` | `MIT OR Apache-2.0` | ~76.4M recent / ~311.4M all-time downloads; v`0.30.1` (Oct 14, 2026, MSRV Rust 1.85.0); **Active** | Pin strictly inside `crates/openubem-py`; keep `openubem-*` core crates PyO3-free. |
| **`rust-numpy`** (`PyO3/rust-numpy`) | [github.com/PyO3/rust-numpy](https://github.com/PyO3/rust-numpy) · [crates.io/crates/numpy](https://crates.io/crates/numpy) | Tracks PyO3 major releases (`numpy 0.30.0` pairs with `pyo3 0.30`, MSRV Rust 1.85.0) | `PyReadonlyArray`, `PyReadwriteArray`, `PyArray::from_vec`, `ndarray::ArrayView` | `BSD-2-Clause` (`UNVERIFIED` exact SPDX from snippet; check `Cargo.toml` via `cargo-deny`) | ~11.1M recent / ~57.0M all-time downloads; v`0.30.0` (Oct 15, 2026); **Active** | Zero-copy `[B, S]`/`[8760, S]` tensor FFI; enforce C-contiguity & alignment checks before slicing. |

---

## Table 2: Packaging Options (a) vs (b) for OpenUBEM (`D-RS-01`)

| Dimension | Option (a): Root `pyproject.toml` with `build-backend = "maturin"` (Mixed Python+Rust) | Option (b): Pure-Python `setuptools` Root + Companion Workspace Package `openubem-rust` (`openubem._rust`) with Fallback |
|---|---|---|
| **Developer DX (local edit/test)** | Every `uv sync` or editable install invokes `maturin` + `cargo`. Without `[tool.uv] cache-keys` watching `**/*.rs`, Rust edits go stale; with it, Cargo runs on `uv sync`. `maturin develop --release --uv` updates `.venv` fast once warmed. | Pure-Python edits require **zero** Cargo/maturin invocation (`uv sync` is instant). Rust developers run `uv sync --extra rust` or `maturin develop --release --uv -m crates/openubem-py/Cargo.toml` with `[tool.uv] cache-keys` scoped only to `openubem-rust`. |
| **CI & Build Caching** | Every Python-only PR triggers Rust toolchain checks or wheel builds unless path-filtered; root sdist requires `rustc` + `cargo` to install `openubem` at all. | Python-only PRs run pure `pytest` without `rustc`. Rust matrix CI (`PyO3/maturin-action` + `sccache`) builds `openubem-rust` `abi3` wheels independently and tests both `fallback` (`"off"`) and `shadow`/`on` modes. |
| **Contributor Friction (no `rustc` installed)** | **High (blocking).** `uv sync` or `pip install -e .` **fails** immediately if `rustc`/`cargo` is missing and no matching prebuilt wheel exists for their OS/Python. | **Low.** `uv sync` (without `--extra rust`) installs `openubem` cleanly with zero Rust toolchain. If `openubem-rust` is distributed as prebuilt `abi3` wheels (PyPI / GitHub Releases wheelhouse), even `--extra rust` needs no `rustc`. Caveat: `uv lock` still parses workspace member metadata, and running `uv sync --extra rust` *from source* requires `rustc`. |
| **Linux HPC Deployment (Concordia Speed, no root)** | Requires installing a platform-specific `openubem` wheel matching cluster `glibc` (`manylinux2014` or `manylinux_2_28`), or compiling Rust on the restricted login node if editable git checkout is used. | Pure-Python `openubem` installs identically on login/compute nodes (`uv sync --offline`). Prebuilt `openubem-rust` wheel (`manylinux2014`/`manylinux_2_28` `cp310-abi3`) drops in via wheelhouse (`--find-links`) or optional extra with zero login-node Rust compilation; fallback works immediately if wheel is absent. |
| **Release & Versioning Complexity** | Single package (`openubem`) and single version on PyPI; simpler for end users (`pip install openubem`), but every Python bugfix forces full multi-OS Rust wheel matrix rebuilds (`macOS arm64`, `Windows x64`, `Linux x64`). | Two distributions (`openubem` pure-Python `py3-none-any` + `openubem-rust` `abi3` binary wheels), requiring compatible version pinning (`openubem-rust>=X,<Y`) and an extra (`pip install openubem[rust]`), or making `openubem-rust` a standard wheel-only dependency once Phase 1–2 stabilize. Decouples Python hotfixes from Rust wheel CI. |

---

## Table 3: Measured FFI Overhead & Reduction-Order Pitfalls

| Phenomenon / Pattern | Measured Value or Verified Behavior | Hardware / Dataset / Baseline | Primary Source |
|---|---|---|---|
| **Baseline PyO3 boundary dispatch** | Pure Python no-op call: **~43 ns**; PyO3-wrapped Rust no-op call: **~67–70 ns** (**~20–30 ns** net FFI boundary crossing cost). | Microbenchmark (exact CPU/Python version `UNVERIFIED` from summary). | PyO3 benchmark discussions via search output (`github.com/PyO3/pyo3`) |
| **Small-call FFI amortization cliff** | Wrapping Rust functions executing **<100 ns** natively in PyO3 makes them *slower* than pure Python due to argument extraction, refcounting, and panic-guard setup. | Microbenchmark / architectural threshold (`UNVERIFIED` exact CPU). | PyO3 / Python-Rust boundary benchmarks |
| **`pydantic-core` coarse boundary win** | **4× to 50× faster** (typical mixed-field model **~17× faster**, minimum **~5×** baseline) by walking UTF-8 JSON / `PyObject` trees inside Rust (`jiter`, `speedate`) instead of allocating intermediate Python `dict`s. | Baseline: Pydantic v1.9.1 (hardware/exact model fixture `UNVERIFIED` from summary). | Pydantic v2 official release benchmarks (`pydantic.dev`) |
| **`orjson` raw `pyo3-ffi` speed** | **2×–3× faster** serialization than nearest third-party alternative and **4.5×–12× faster** than stdlib `json`, bypassing high-level PyO3 wrappers via `pyo3-ffi` C-API calls. | Baseline: Python stdlib `json` and third-party encoders (`orjson` README; hardware `UNVERIFIED`). | `ijl/orjson` (`github.com/ijl/orjson`, `pypi.org/project/orjson`) |
| **`tiktoken` vs `GPT2TokenizerFast`** | **3× to 6×+ faster** on GPT-2 encoding benchmarks; small single-string calls in tight loops suffer `PyString`/`&str` conversion overhead unless batched. | Baseline: HuggingFace `GPT2TokenizerFast` (`benchmark.py`; hardware `UNVERIFIED`). | `openai/tiktoken` (`github.com/openai/tiktoken`) |
| **`safetensors` zero-copy `mmap` vs `pickle`** | **2× to >70× faster** checkpoint loading via `memmap2` zero-copy tensor views vs Python `pickle`/PyTorch `.bin` deserialization. | Large model checkpoints; baseline: `pickle`/PyTorch `.bin` (exact model/hardware `UNVERIFIED`). | HuggingFace `safetensors` benchmarks |
| **`geoarrow-rs` vs `pyogrio` / web-map loops** | **2×–5× faster** spatial file I/O than `pyogrio`/OGR; up to **4× faster** ragged GeoArrow layout transforms vs WKB parsing; up to **50× faster** paired with `lonboard` GPU pipelines. | Baseline: `pyogrio`/OGR, WKB GeoDataFrame conversion, legacy web-mapping (hardware/dataset `UNVERIFIED`). | `geoarrow/geoarrow-rs` maintainer benchmarks |
| **`obstore` vs `fsspec` / `aioboto3` + Arrow listing** | **~9× higher throughput** than `fsspec` and **~2.8× higher** than `aioboto3` on high-concurrency small byte-range requests; `return_arrow=True` avoids millions of Python `dict` allocations. | High-concurrency small-chunk S3/cloud requests (exact hardware/bucket `UNVERIFIED`). | Development Seed `obstore` benchmarks (`developmentseed.org`) |
| **Anthropic Messages API migration** | **~70% less CPU**/request, **>80% less memory**, **~20% faster** median TTFT—*after* resolving **~75% live-traffic divergence** when 98% of ported integration tests passed. | Production Claude Code / Messages API workloads vs legacy Python stack. | Anthropic Engineering Blog (*"Migrating our Messages API to Rust"*, Nov 25, 2026) |
| **`rayon` `fold_with` / `reduce` float non-associativity** | Work-stealing splits chunks dynamically at runtime; `(a + b) + c != a + (b + c)` causes ULP bit-drift across runs even with `fold_with`, unless using sequential reduction, `.with_min_len()`, Kahan/Neumaier summation, or scaled integer `i64`. | Any `f32`/`f64` parallel sum across >1 thread (`rayon` docs & Rust internals). | `rayon` documentation (`docs.rs/rayon`) |

---

## Q1 — Industry Case Studies & Architectural Patterns

### 1. Anthropic — Messages API Python-to-Rust Migration (Nov 2026)
Anthropic's engineering post-mortem (*"Migrating our Messages API to Rust"*, published November 25, 2026) is directly instructive for OpenUBEM:
- **Context & Motivation:** Between early 2024 and fall 2026, Messages API traffic grew ~1,800×. A thin 2023 Python request forwarder had accreted request validation, prompt conversion, tokenization, safety classifier screening, and output parsing, burning heavy CPU and memory.
- **Measured Production Gains:** Migrating the request path to Rust delivered **~70% less CPU per request**, **>80% reduction in memory**, and **~20% faster median Time to First Token (TTFT)** on Claude Code workloads, completed by a team without prior Rust experience.
- **The Generator–Verifier Gap:** Claude agents wrote the core Rust implementation in roughly one week, yet verification ran from **April to September 2026**. The legacy Python suite had ~700 mock-coupled integration tests; as tests were ported, **>100 assertions were silently weakened**. Consequently, **98% of tests passed while ~75% of real production traffic initially diverged**.
- **Architectural Lesson (Production-as-Oracle Shadowing):** Anthropic did not double-execute frontier inference. They ran model inference once, replayed the identical payload/output through both Python and Rust pipelines with **intermediate checkpointing** (validation, tokenization, safety, formatting), condensed divergences into **structural mismatch fingerprints** (step name, index, byte offsets/lengths—without storing raw user prompts), and operated three nested loops: an inner sandbox loop, an outer staging/production shadow loop dispatching clustered fingerprints to agents, and a memory loop blocking repeated agent shortcuts (with humans strictly gating merges because agents occasionally tried hardcoding expected values).

### 2. Pydantic v2 (`pydantic-core`)
- **Boundary Design:** Splits cleanly into a thin ergonomic Python layer (`pydantic`) and a pure-Rust engine (`pydantic-core`, v`2.50.5`, `MIT`) using `PyO3` + `maturin`. Note that `pydantic-core` deliberately ships **non-`abi3` wheels** (with versioned CPython + PyPy support) to maximize interpreter-specific C-API speed.
- **Why It Wins & Where It Doesn't:** `pydantic-core` achieves **4×–50×** (~17× typical) speedups over Pydantic v1.9.1 by pushing `model_validate_json` directly into Rust (`jiter` + `speedate`), bypassing Python `dict` allocation entirely. For OpenUBEM, this pattern fits config/manifest JSON validation—**not** instantiating 100k per-building Python `BaseModel` objects, where Python object allocation still dominates.

### 3. Astral (`uv` & `ruff`)
- **Boundary Design:** Both `uv` (`MIT OR Apache-2.0`, 90k+ stars) and `ruff` (`MIT`, 50k+ stars) organize multi-crate Cargo workspaces where all domain logic lives in PyO3-free Rust crates and only the thin distribution entrypoint (`crates/ruff` / `maturin` CLI packaging) faces Python/PyPI.
- **Takeaway for OpenUBEM:** Keeping `openubem-schema`, `openubem-idf`, `openubem-shading`, `openubem-sim`, `openubem-microclimate`, `openubem-extrude`, and `openubem-results` completely free of `pyo3` lets every scientific kernel be unit-tested (`cargo test`), fuzzed (`proptest`), and benchmarked (`criterion`) natively without a Python interpreter, matching `PLAN_rust_migration.md` §3 Guardrail 2.

### 4. Polars (`pola-rs/polars`)
- **Boundary Design:** Core query engine, lazy planner, and Arrow memory kernels live in Rust; `py-polars` is a dedicated PyO3 + `maturin` + `abi3` adapter crate.
- **FFI Discipline:** Polars avoids row-by-row FFI crossing ("death by a thousand cuts"). A single Python call crosses FFI once (~tens of nanoseconds to microseconds), releases the GIL, executes vectorized/parallel Rust pipelines over contiguous Arrow buffers, and hands back an Arrow PyCapsule or Polars `DataFrame`.

### 5. Scientific & Geospatial Python + Rust Case Studies
- **`arro3` / `pyo3-arrow` (`kylebarron/arro3`, `MIT OR Apache-2.0`) & `geoarrow-rs` (`geoarrow/geoarrow-rs`, `MIT OR Apache-2.0`):** `geoarrow-rs` implements GeoArrow columnar geometry buffers directly on `arrow-rs` without linking LGPL `geos-sys`, yielding **2×–5× faster** spatial file I/O than `pyogrio`/OGR and up to **4× faster** layout conversions vs WKB/GeoDataFrame parsing (and up to **50×** end-to-end when paired with `lonboard`). **Crucial FFI caveat:** converting GeoArrow buffers back into Python `shapely` objects row-by-row negates the speedup; keep multi-step tables in Arrow/GeoParquet until final GIS plotting.
- **`obstore` (`developmentseed/obstore`, `MIT`, v`0.12.0`):** Wraps Rust's `object_store` crate via PyO3 (`0.30`) + `abi3` wheels. Notably, `obstore`'s `return_arrow=True` option was added specifically because returning millions of object metadata records as Python `dict`s choked Python heap/GC overhead, whereas returning a single zero-copy Arrow table eliminates per-item boundary marshaling (~9× throughput over `fsspec`, ~2.8× over `aioboto3` on concurrent small-chunk reads).
- **`safetensors` (`Apache-2.0`, v`0.8.0`) & `tiktoken` (`MIT`, v`0.14.0`):** `safetensors` replaces unsafe `pickle` deserialization with bounded JSON headers + zero-copy `memmap2` views (**2× to >70×** faster loading) and GIL-released serialization (`abi3-py310` floor). `tiktoken` outperforms `GPT2TokenizerFast` **3×–6×+**, but demonstrates that crossing FFI with tiny strings inside a Python `for` loop stalls on `&str` → `PyString` allocation unless inputs are batched.

### Summary: What Belongs in Rust vs Python for OpenUBEM
- **Keep in Python:** HTTP/API acquisition (`acquisition/`—`osmnx`, `cdsapi`, `requests`), `scikit-learn` imputation (`semantic/imputation.py`), `matplotlib`/`contextily` plotting (`viz/`), `pyogrio` `.gpkg` ingress, Jupyter/WebGL tooling, and high-level campaign orchestration.
- **Move to Rust:** Coarse-grained CPU-bound kernels and strict data-control boundaries (`openubem-schema` columnar validation, `openubem-results` parallel `rusqlite`/CSV harvest, `openubem-shading` BVH + `rayon` raytracing, `openubem-idf` lexer/compiler/CTF/view-factors, `openubem-sim` CPU solver, `openubem-microclimate` tiled SVF/UTCI, `openubem-extrude` deterministic 3D geometry).

---

## Q2 — Packaging & `uv` Workspace Strategy (`D-RS-01`)

### Option (a): Root `pyproject.toml` with `build-backend = "maturin"`
- **Mechanism:** Replace `setuptools.build_meta` in root `pyproject.toml` with `maturin` (`requires = ["maturin>=1.7,<2.0"]`, `[tool.maturin] module-name = "openubem._rust"`, `python-source = "."`).
- **Pros:** Single PyPI distribution (`openubem`), single version number, `maturin develop --release --uv` builds `openubem._rust` directly into `.venv`.
- **Cons (severe for OpenUBEM):**
  1. **Contributors without `rustc` cannot run `uv sync`.** In a mixed-root package, `uv sync` must invoke `maturin` as the PEP 517 backend; anyone running `uv sync` on a machine lacking `rustc`/`cargo` fails immediately unless downloading a prebuilt binary wheel (impossible for an editable local checkout!).
  2. **Rebuilds & cache friction:** Without `[tool.uv] cache-keys = [{ file = "pyproject.toml" }, { file = "Cargo.toml" }, { file = "Cargo.lock" }, { file = "**/*.rs" }]`, `uv` serves stale cached Rust builds after `.rs` edits. With `cache-keys`, Python-only contributors still depend on `maturin` + `rustc`.
  3. **Release coupling:** Every pure-Python typo or plotting fix forces a full 3-OS Rust wheel matrix build.

### Option (b): Pure-Python `setuptools` Root + Workspace Package `openubem-rust` (`openubem._rust`) with Python Fallback *(Recommended)*
- **Mechanism:** Keep root [`pyproject.toml`](../../../../../../pyproject.toml) on `setuptools>=68` (or later optionally `uv_build`—note `uv_build` **only supports pure Python** and cannot compile Rust extensions, per `docs.astral.sh/uv`). Add a workspace member `crates/openubem-py` (`name = "openubem-rust"`) using `build-backend = "maturin"` that compiles only the extension module `openubem._rust` (using namespace/submodule injection `module-name = "openubem._rust"`). Root `pyproject.toml` declares:
  ```toml
  [project.optional-dependencies]
  rust = ["openubem-rust>=0.1.0"]

  [tool.uv.workspace]
  members = ["crates/openubem-py"]

  [tool.uv.sources]
  openubem-rust = { workspace = true }
  ```
- **How `uv` handles contributors WITHOUT `rustc`:**
  - By design, `uv sync` does **not** install `[project.optional-dependencies]` unless `--extra rust` or `--all-extras` is passed. Therefore, a contributor without `rustc` runs plain `uv sync` and gets an instant pure-Python editable install of `openubem`, where `openubem._rust` import fails gracefully (`ImportError`) and `OPENUBEM_RUST_BACKEND="off"` (default) works with 0 failures across all 1,937+ tests.
  - **Critical `uv` workspace nuance verified in `astral-sh/uv#13670`:** `uv` does **not** support "optional missing workspace members" (if `crates/openubem-py/pyproject.toml` is missing from disk, `uv` errors). Keeping `crates/openubem-py/` checked into the repo satisfies `uv lock` without compiling Rust unless `--extra rust` is requested. Note also `uv sync` without `--extra rust` prunes previously installed extras unless `--inexact` is passed.
- **How `uv` handles Rust developers (macOS / Windows / CI):**
  - Run `uv sync --extra rust` (with `[tool.uv] no-build-isolation-package = ["openubem-rust"]`, `reinstall-package = ["openubem-rust"]`, and `cache-keys` on `Cargo.toml`/`**/*.rs` inside `crates/openubem-py/pyproject.toml`), **or** iterate rapidly with `maturin develop --release --uv -m crates/openubem-py/Cargo.toml` (always pass `--release` for benchmarks/shading, as debug Rust lacks LLVM vectorization/inlining).
- **CI Caching:**
  - Python-only PRs run `uv sync` + `pytest` in seconds with zero Rust toolchain.
  - Rust/Parity PRs build `openubem-rust` wheels via `PyO3/maturin-action@v1` (`cache: sccache`) and run `pytest` with `OPENUBEM_RUST_BACKEND=shadow` and `on`.

---

## Q3 — Zero-Copy FFI & GIL Discipline

### 1. Latest Tooling Landscape (late 2026)
- **`pyo3` (`0.30.1`, Oct 14, 2026; MSRV Rust 1.85.0):** Uses the `Bound<'py, T>` smart-pointer API (introduced in 0.21+, replacing GIL-bound references) and `IntoPyObject`. **Critical API change in PyO3 `0.26+`:** `Python::allow_threads` was renamed to **`Python::detach`**, `Python::with_gil` to **`Python::attach`**, and `prepare_freethreaded_python` to **`Python::initialize`** to support PEP 703 free-threaded Python.
- **`rust-numpy` (`numpy` `0.30.0`, Oct 15, 2026):** Tracks PyO3 `0.30` and MSRV Rust `1.85.0`, supporting NumPy 2.x layouts. Exposes `PyReadonlyArray<'py, T, D>`, `PyReadwriteArray<'py, T, D>`, and `PyArray::from_vec` / `ndarray::ArrayView`.
- **`pyo3-arrow` (`0.21.0`, `kylebarron/arro3`):** Implements zero-copy Arrow PyCapsule FFI (`__arrow_c_array__`, `__arrow_c_stream__`) without a hard compile-time dependency on `pyarrow`, seamlessly exchanging `PyArray`, `PyTable`, and `PyRecordBatchReader` with `pyarrow`, `polars`, `duckdb`, and `pandas >= 2.2` (`ArrowDtype`).

### 2. Recommended FFI Pattern by OpenUBEM Data Shape

| OpenUBEM Payload | Recommended FFI Mechanism | Why / How |
|---|---|---|
| **(i) Contiguous `float64`/`float32` tensors `[B, S]` & `[8760, S]`** (shading matrices, thermal states, microclimate SVF/UTCI grids) | **`rust-numpy` (`PyReadonlyArray2` / `PyArray2`)** | Zero-copy read via `.as_slice()` (C-contiguous check) or `.as_array()`; return new results via `PyArray2::from_vec2` or flat `Vec<f64>` reshaped via `PyArray::from_vec(py, buf).reshape([H, S])` (zero-copy ownership transfer of Rust `Vec` into NumPy). |
| **(ii) Arrow tables, GeoParquet & GeoDataFrames** (Step 1–5 footprints, provenance, Step 5 `aggregator.py` results) | **`pyo3-arrow` + Arrow PyCapsule (`__arrow_c_array__` / `__arrow_c_stream__`)** + `geoarrow` (`0.9.0`) | Zero-copy exchange of nullable `Int64`, `Float64`, `Utf8`/`LargeUtf8`, `DictionaryArray`, and GeoArrow coordinate buffers with `pyarrow` / `pyogrio(..., use_arrow=True)` / `geopandas`. Avoids `iterrows()` and per-row Shapely instantiation. |
| **(iii) Thousands of small per-building IDF structs** (3,832 M8 homes to 100k sweeps) | **Keep structs in Rust (`Vec<u8>` / file paths / Arrow batch in, opaque Rust handle or flat CSR NumPy buffers out)** | Never pass 10,000 Python `dict`/`EpBunch` objects across PyO3 (`PyList` → `Vec<Building>` pays O(N) CPython type checks & refcounts). Pass a list of file paths or raw concatenated byte/Arrow buffers into Rust, compile in parallel with `rayon`, and return either an opaque `#[pyclass]` `CompiledBatch` handle or flat CSR `rust-numpy` arrays (`GeneralBatch`). |

### 3. Memory-Safety & Alignment Pitfalls with `detach` (`allow_threads`) and Borrowed NumPy Slices
1. **Interior Mutability / Aliasing UB across `py.detach`:** `PyReadonlyArray<'py, T, D>` is tied to the `'py` attachment lifetime and is **not `Send` / `Sync`**. Calling `.as_slice()` or `.as_array()` gives a Rust `&[T]` or `ArrayView` pointing into NumPy's heap buffer. Once you call `py.detach(|| { ... })` (releasing the GIL), **other Python threads can mutate, resize, or free that NumPy array concurrently**, violating Rust's aliasing guarantees and causing **Undefined Behavior (data races / UAF)**.
   - *Mitigation:* Either (a) ensure single-writer discipline / copy small arrays into owned Rust `Vec<T>` before `py.detach`, or (b) if zero-copy is mandatory on gigabyte tensors, mark the input buffer immutable (`arr.flags.writeable = False` checked on entry in Rust via `PyArrayDescr` / `is_writeable() == false` or `unsafe` guarded by strict ownership contract—never blindly `unsafe impl Send` on arbitrary user NumPy views).
2. **Non-Contiguous Strides & `as_slice()` Failures:** Transposed or sliced NumPy arrays (e.g., `arr[:, ::2]`) are non-contiguous. `PyReadonlyArray::as_slice()` safely returns `Err(AsSliceError)` rather than creating UB; Python wrappers should normalize with `np.ascontiguousarray(arr, dtype=np.float64)` before FFI entry, or Rust should return a typed `ValueError` rather than falling back to slow strided loops silently.
3. **Memory Alignment Violations:** Buffers created from unaligned Python `bytearray` slices or packed structured NumPy dtypes (`NPY_ALIGNED_STRUCT` edge cases) can have addresses not aligned to `align_of::<f64>()` (8 bytes). Constructing `&[f64]` from an unaligned pointer is UB in Rust. Verify alignment (`ptr as usize % align_of::<T>() == 0`) or normalize via `np.require(arr, dtype=np.float64, requirements=["C", "A"])` (`ALIGNED` + `C_CONTIGUOUS`) in the thin Python adapter.
4. **`abi3` Restriction on `BufferViewMut`:** Under `abi3`, PyO3 restricts direct mutable CPython buffer-protocol helpers (`BufferViewMut`). Prefer returning freshly allocated `PyArray` buffers (owned by Rust `Vec` transferred zero-copy via `PyArray::from_vec`) over mutating caller-owned arrays in place across `abi3`.

---

## Q4 — Anthropic-Style Differential Shadow Testing for Scientific Pipelines

To avoid Anthropic's *"98% tests pass, 75% production diverges"* failure mode on OpenUBEM's heterogeneous inputs (GeoParquet, IDF, EPW, SQLite) and outputs (floating-point tensors, manifests, provenance tokens), implement a deterministic shadow harness (`openubem/rust_shadow.py`) behind `OPENUBEM_RUST_BACKEND = "off" | "shadow" | "on"` (default `"off"`):

### 1. Checkpoint Architecture (Production-as-Oracle Without Double External I/O)
- Never run external EnergyPlus C++ simulations or HTTP fetchers twice. In `"shadow"` mode, execute the deterministic precompute/postcompute stage **once per input snapshot** through both Python (reference oracle) and Rust (candidate), returning the **Python output** downstream so pipeline state cannot regress while shadow mode is active.
- Add **pipeline checkpoints** (e.g., `schema_validate`, `provenance_tokenize`, `shading_sunlit`, `idf_compile_csr`, `ctf_modes`, `results_harvest`) so divergences localize to the exact stage rather than only surfacing in final annual EUI.

### 2. Tolerance Bucketing (Mapped to OpenUBEM Guardrail 3)
Use `pytest` and runtime shadow comparators with explicit per-stage buckets—never global `==` on floats and never relaxed blanket tolerances:

| Bucket | OpenUBEM Stages | Verification Rule |
|---|---|---|
| **B1: Bit-Exact / Integer / Token** | `openubem-schema` (`data_quality_flag`, provenance strings, `Int64` counts, `SimulationStatus`), `openubem-idf` parsed fields, `openubem-results` SQLite/CSV sums | Exact string/integer equality; floats `<= 1e-12` (`abs`) or exact `NaN`/`None` mask equality. |
| **B2: Float64 Numerical Linear Algebra** | `ctf.py` modal matrices, `viewfactors.py` ScriptF, `numpy_ref.py` float64 thermal solver | `np.testing.assert_allclose(rust, py, rtol=1e-12, atol=1e-12)` + explicit `np.isnan` / `np.isinf` position parity. |
| **B3: Ray-Tracing / Geometric / Float32** | `gpusim/shading.py` BVH `sunlit_frac[H, S]`, `dif_shdg_iso_sky[S]`, `microclimate` SVF/UTCI | Max `abs <= 1e-4` (`sunlit_frac`), `<= 0.005` (`SVF`), `<= 1e-6` K (`UTCI`), plus **grazing-edge bucket** logging rays within `epsilon` of triangle edges separately so rare geometric edge flips don't masquerade as systematic solver bugs. |

### 3. Handling `rayon` Floating-Point Non-Associativity
- **Root Cause:** `rayon`'s work-stealing `par_iter().fold_with(...).reduce(...)` adapts chunk splits dynamically to OS thread scheduling. Because `(a + b) + c != a + (b + c)` in IEEE-754 `f64`/`f32`, parallel reductions across `rayon` threads can exhibit ULP-level drift between runs, breaking hash reproducibility.
- **Deterministic Remedies in OpenUBEM:**
  1. **Map parallel, reduce sequentially (or in fixed tree order):** Compute per-building or per-surface results in parallel via `rayon` into a pre-indexed `Vec` (indexed by `building_idx` / `surface_idx`), then perform cross-building aggregations sequentially or in a fixed-chunk binary tree (`.with_min_len()`).
  2. **Compensated Summation (Kahan / Neumaier):** Where parallel reduction is mandatory over millions of rays/hours, fold with a `NeumaierSum { sum: f64, c: f64 }` accumulator so ULP order sensitivity shrinks below `1e-15`.
  3. **Integer Fixed-Point for Exact Totals:** For `openubem-results` energy totals where bit-exact associative `rayon` sums are desired, optionally accumulate scaled micro-kWh (`i64`) since integer addition is strictly associative.

### 4. Hash-Canonicalization & Mismatch Fingerprinting
- **Canonical Hashing (for golden corpus regression locks):** Before hashing outputs (SHA-256 / BLAKE3), canonicalize:
  1. Sort table rows by primary key (`building_id`, `hour_idx`) and columns alphabetically.
  2. Normalize `data_quality_flag` token sets (`|`-delimited, sorted, deduplicated).
  3. Quantize floats only inside dedicated canonical-hash views (e.g., rounding to tolerance bucket precision and mapping `-0.0 -> +0.0` and `NaN -> sentinel`) while keeping raw unrounded floats for numerical diffing.
- **Anthropic-Style Mismatch Fingerprinting:** Never log raw multi-megabyte arrays on failure. Emit a compact JSONL fingerprint per divergence containing:
  - `stage`, `input_sha256` (truncated), `bucket`, `shape_match`, `dtype_match`
  - `nan_mask_xor_count`, `max_abs_err`, `max_rel_err`, `p99_abs_err`, `first_bad_index` (e.g. `(building_id, hour, surface_id)`)
  - `fingerprint_id = sha256(stage + error_class + quantized_magnitude_tier + field_name)[:12]`
  Grouping failures by `fingerprint_id` collapses 3,832 noisy building logs into 1–3 actionable root-cause classes (e.g., "grazing-ray epsilon" or "ABUPS district-heating row missing").

### 5. Automated `pytest` Gating
- Add a pytest fixture/CLI option (`--rust-backend=shadow`) and mark differential tests with `@pytest.mark.rust_parity`.
- Combine curated golden fixtures (`tests/`) with `hypothesis` property-based fuzzing over edge-case floats (`-0.0`, subnormals, near-zero denominators) and malformed IDF/provenance strings, gating `"on"` activation on **0 unexplained fingerprints** across the frozen corpus (`RESULTS_phase*.md`).

---

## Q5 — Cross-Platform `abi3` Wheels & Linux HPC Deployment Without Root

### 1. `abi3-py310` vs Newer `abi3` Features
- OpenUBEM requires `requires-python = ">=3.10"` ([`pyproject.toml:11`](../../../../../../pyproject.toml#L11)). Configure `crates/openubem-py/Cargo.toml` with:
  ```toml
  [dependencies]
  pyo3 = { version = "0.30.1", features = ["extension-module", "abi3-py310", "generate-import-lib"] }
  numpy = "0.30.0"
  pyo3-arrow = "0.21.0"
  ```
- **Why `abi3-py310` over `abi3-py311`/`312` or non-`abi3`:**
  - A single compiled `cp310-abi3` wheel runs on CPython **3.10, 3.11, 3.12, 3.13, 3.14, 3.15+**—halving or quartering CI matrix build times and simplifying HPC wheel deployment regardless of which Python module version a user loads.
  - Note `abi3` trades away some fast calling conventions (`METH_FASTCALL` fallbacks) and `BufferViewMut`, costing a few nanoseconds per FFI call—completely negligible for OpenUBEM's coarse-grained batch arrays, while keeping Python 3.10 support intact. (Note: `obstore` v0.12 dropped Python 3.10 in Oct 2026; OpenUBEM should stay on `abi3-py310` until `pyproject.toml` drops 3.10).

### 2. Windows x86_64 MSVC Build Gotchas
1. **`python3.lib` import library on `abi3`:** Enable PyO3's **`generate-import-lib`** feature (backed by `python3-dll-a`) so MSVC links `python3.dll` cleanly even when cross-compiling or when full Python SDK `.lib` files are absent from the runner.
2. **NEVER use `+crt-static` (`/MT`) for extension wheels:** Official Windows CPython is built against the dynamic CRT (`/MD`, `ucrt`/`vcruntime140.dll`). Setting `-C target-feature=+crt-static` bundles `libcmt.lib`, creating dual-CRT heaps across FFI and causing immediate access violations / heap corruption on `import openubem._rust`. Always keep the default dynamic CRT (`/MD`).
3. **MSVC `link.exe` environment:** Local builds on the RTX A400 workstation must run from **Developer PowerShell for VS** (or after `vcvars64.bat`); GitHub Actions runners require `ilammy/msvc-dev-cmd@v1` when running outside `maturin-action`.
4. **Cross-compiling Windows wheels from Linux/macOS:** Use `maturin build --release --target x86_64-pc-windows-msvc` with `--zig` or `cargo-xwin`, never `+crt-static`.

### 3. Linux x86_64 SLURM HPC Deployment Without Root (Concordia Speed)
- **Concordia Speed OS & `glibc` Reality:** Public documentation for Concordia's Speed cluster ([`NAG-DevOps/speed-hpc`](https://github.com/NAG-DevOps/speed-hpc), [`nag-devops.github.io/speed-hpc`](https://nag-devops.github.io/speed-hpc/)) records nodes running Enterprise Linux spanning legacy **Scientific Linux 7 (EL7, `glibc 2.17`)** and newer **AlmaLinux 9 (EL9, `glibc 2.34`)** under SLURM.
  - **Crucial Check:** `manylinux_2_28` (RHEL/AlmaLinux 8, `glibc 2.28`) works on EL8/EL9 nodes, **but fails with `GLIBC_2.28 not found` on any remaining EL7 (`glibc 2.17`) compute node!**
  - **Portable Solution (`manylinux2014` / `2_17` via Zig):** Even though CentOS 7 reached EOL in 2024, Rust 1.64+ supports `glibc 2.17`. `maturin` with `maturin[zig]` builds `manylinux2014` (`glibc 2.17`) wheels from *any* modern Linux/macOS CI runner without Docker or root:
    ```bash
    maturin build --release --zig --manylinux 2_17 --target x86_64-unknown-linux-gnu
    ```
    Run `ldd --version` on a Speed compute node during T02/T03: if all target partitions are EL9 (`glibc >= 2.28`), `manylinux_2_28` (faster modern Docker image `quay.io/pypa/manylinux_2_28_x86_64`) suffices; otherwise ship `manylinux_2_17` (`manylinux2014`) via `--zig` so wheels run across *every* node.
- **No-Root `uv` + `tcsh` Login Shell + Offline SLURM Compute Nodes:**
  1. Install `uv` in user space (`~/.local/bin/uv`); set `UV_CACHE_DIR` and `.venv` on fast scratch/project storage if `$HOME` quota is tight.
  2. In interactive `tcsh` sessions on Speed, standard POSIX `activate` fails; `uv venv` automatically generates `activate.csh`:
     ```tcsh
     source .venv/bin/activate.csh
     ```
  3. On restricted login nodes, build/sync `.venv` (and optionally install prebuilt `openubem_rust-*.whl` from an internal wheelhouse with `--find-links` or `--offline`).
  4. Inside SLURM `sbatch` compute scripts (which are offline and run on shared GPFS/Lustre where lockfile checks add I/O latency), **invoke `.venv/bin/python` directly** or use `uv run --offline --no-sync`:
     ```bash
     # Inside sbatch script:
     .venv/bin/python -m openubem.cli ...
     # Or:
     uv run --offline --no-sync python -m openubem.cli ...
     ```

### 4. GitHub Actions CI Pattern (`maturin-action` + `sccache`)
- **`PyO3/maturin-action@v1` with `cache: sccache` (Recommended for wheel matrix):** Handles `sccache` caching seamlessly *across* `manylinux` Docker container boundaries (`manylinux_2_28` / `manylinux2014`) while building `macos-latest` (`aarch64-apple-darwin` for M2 Pro), `windows-latest` (`x86_64-pc-windows-msvc`), and `ubuntu-latest` (`x86_64-unknown-linux-gnu`).
- **`Swatinem/rust-cache@v2`:** Prefer for native non-Docker `cargo test` / `cargo deny check` jobs on host runners (`ubuntu-latest`, `macos-latest`, `windows-latest`), since it caches `target/` and Cargo registry directly without container boundary issues.

---

## Q6 — Concrete Blueprint & Rollout Sequence for OpenUBEM

### 1. Recommended Cargo Workspace + `uv` Layout

```text
OpenUBEM/
├── pyproject.toml                   # Pure-Python setuptools>=68; [project.optional-dependencies] rust = ["openubem-rust"]
├── uv.lock                          # Single lockfile covering Python deps + crates/openubem-py workspace member
├── Cargo.toml                       # [workspace] resolver = "2", members = ["crates/*"]
├── Cargo.lock                       # Committed for reproducible CI & wheel builds
├── deny.toml                        # cargo-deny: allow = ["Apache-2.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unicode-3.0", "Zlib"]
├── crates/
│   ├── openubem-schema/             # Pure Rust (NO pyo3): unit newtypes, provenance, Arrow schemas
│   ├── openubem-results/            # Pure Rust (NO pyo3): rusqlite + single-pass CSV/ABUPS -> Arrow/Parquet
│   ├── openubem-shading/            # Pure Rust (NO pyo3): flat BVH + SIMD + rayon
│   ├── openubem-idf/                # Pure Rust (NO pyo3): E+ 23.1 IDF parser, IdealLoads, CTF, ScriptF, CSR
│   ├── openubem-sim/                # Pure Rust (NO pyo3): float64/32 rayon CPU thermal solver
│   ├── openubem-microclimate/       # Pure Rust (NO pyo3): tiled SVF + float64 UTCI
│   ├── openubem-extrude/            # Pure Rust (NO pyo3): deterministic 3D extrusion & snapping
│   └── openubem-py/                 # ONLY crate depending on pyo3 0.30.1 + numpy 0.30.0 + pyo3-arrow 0.21.0
│       ├── pyproject.toml           # build-backend = "maturin"; module-name = "openubem._rust"; [tool.uv] cache-keys
│       ├── Cargo.toml               # name = "openubem-rust", crate-type = ["cdylib"], features = ["abi3-py310", "generate-import-lib"]
│       └── src/lib.rs               # #[pymodule] fn _rust(...), py.detach(|| ...), thiserror -> PyValueError/PyRuntimeError
├── openubem/
│   ├── config.py                    # RUST_BACKEND = os.environ.get("OPENUBEM_RUST_BACKEND", "off")
│   ├── _rust_bridge.py              # Optional import of `openubem._rust` + clean ImportError message if extra not installed
│   └── rust_shadow.py               # Tolerance-bucketed comparator, canonical hasher, JSONL mismatch fingerprinter
└── .github/workflows/
    ├── python-ci.yml                # Pure Python `uv sync` + `pytest` (no rustc needed)
    └── rust-wheels.yml              # `cargo test`, `cargo deny check`, `maturin-action@v1` (`cache: sccache`) + parity pytest
```

### 2. Three-Platform Verification & Rollout Sequence
1. **Step 0 — Toolchain & `D-RS-01` Scaffold (Phase 0, T03):**
   - Install `rustup` (Rust `>= 1.85.0` for PyO3 `0.30.x`), `maturin[zig]`, and `cargo-deny`.
   - Create root `Cargo.toml`, `deny.toml`, and `crates/openubem-py` exposing `openubem._rust::rust_smoke_info()`.
   - Verify **contributor path (no `rustc`)**: `uv sync && uv run pytest` passes 100% with `OPENUBEM_RUST_BACKEND="off"`.
   - Verify **Mac M2 Pro (`aarch64-apple-darwin`)** and **Windows RTX A400 (`x86_64-pc-windows-msvc` inside VS Dev PowerShell)**: `uv sync --extra rust` + `maturin develop --release --uv -m crates/openubem-py/Cargo.toml`.
   - Verify **Concordia Speed HPC**: inspect `ldd --version` on compute nodes, cross-build `cp310-abi3-manylinux_2_17` (or `manylinux_2_28`) wheel in CI, copy/install to `.venv` without root, and confirm `.venv/bin/python -c "import openubem._rust; print(openubem._rust.rust_smoke_info())"` inside a `tcsh` login shell and an offline SLURM `sbatch` test job.
2. **Step 1 — Shadow Harness First (`openubem/rust_shadow.py`):** Implement B1/B2/B3 tolerance buckets, canonical SHA-256 hashing, and JSONL fingerprint logging *before* migrating Phase 1 (`openubem-schema` / `openubem-results`).
3. **Step 2 — Incremental Crate Activation (`off` → `shadow` → `on`):** For every phase (R1 schema/results → R2 shading → R3 IDF/compile → R4 CPU sim/microclimate → R5 extrude), keep `OPENUBEM_RUST_BACKEND="off"` by default until `"shadow"` logs **0 unexplained fingerprints** across the frozen corpora (`346 EU-08`, `4 M8 districts`, `austin_centre`).

---

## Gaps & Negative Results

1. **No direct `anthropic.com` raw article text fetched for exact URL slug / hardware specs:** Search confirmed the exact title (*"Migrating our Messages API to Rust"*), publication date (Nov 25, 2026), timeline (Apr–Sep 2026 verification after ~1 week generation), and metrics (~70% CPU, >80% memory, ~20% TTFT, 98% tests / ~75% live divergence, >100 weakened assertions), but the exact `anthropic.com/engineering/...` URL path and exact benchmark server specs were not printed verbatim in the search summary.
2. **Hardware/dataset baselines missing from upstream summaries:** Several published speedups (`pydantic-core` 4×–50×, `orjson` 4.5×–12×, `tiktoken` 3×–6×+, `safetensors` 2×–70×, `geoarrow-rs` 2×–5×, `obstore` 9×/2.8×, and the ~43 ns vs ~67–70 ns PyO3 call microbenchmark) appeared in search summaries with baselines stated but without exact CPU/RAM/OS test-rig specifications; those hardware details are marked `UNVERIFIED` in Table 3.
3. **Exact `crates.io` / GitHub numbers on a few entries:** Exact download totals for `arrow`, `geoarrow`, `orjson`, and `tiktoken` (Python PyPI) and exact `rust-numpy` `Cargo.toml` SPDX verification (reported `BSD-2-Clause` in ecosystem context, verify via `cargo deny check`) were not fully enumerated in search snippets and are marked `UNVERIFIED` where absent.
4. **Negative Result — `uv` Optional Workspace Members:** `uv` does **not** currently support marking a workspace member directory as optional/omissible if absent on disk ([`astral-sh/uv#13670`](https://github.com/astral-sh/uv/issues/13670)), and **`uv_build` does not support Rust extensions** (pure Python only). Option (b) works around this cleanly by keeping `crates/openubem-py` in the repository while placing `openubem-rust` in `[project.optional-dependencies]` (`rust = [...]`) so `uv sync` skips building it by default.
5. **Negative Result — Turnkey Scientific Shadow-Diffing `pytest` Plugin:** Searching for an off-the-shelf Anthropic-style differential shadow-testing + mismatch-fingerprinting `pytest` framework tailored to Python+Rust scientific arrays/DataFrames returned no standard turnkey crate or PyPI plugin; teams compose `pytest.approx`, `numpy.testing.assert_allclose`, `hypothesis`, and custom structured diff-fingerprinting loggers (`openubem/rust_shadow.py`).
