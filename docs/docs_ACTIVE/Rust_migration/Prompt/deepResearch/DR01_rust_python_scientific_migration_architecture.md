# DR01 — Hybrid Python-to-Rust Migration Architecture, Shadow Verification & Cross-Platform Tooling

**Feeds:** Plan §0, §3, §5, Phase 0 (T01–T03), and Owner Decisions D-RS-01, D-RS-04
**Save output to:** `results/DR01_result.md`

---

## PROMPT

You are a principal systems & scientific-computing architect specialising in incremental Python-to-Rust migrations (`PyO3`, `maturin`, `uv`, `abi3`, Arrow/NumPy FFI) and production verification harnesses. Produce a rigorous, source-cited technical report.

### Context
I maintain **OpenUBEM**, an open-source Urban Building Energy Modeling platform (`Apache-2.0 OR MIT`, Python `>=3.10`, managed with `uv` + `uv.lock` and `pyproject.toml` using `setuptools`). The codebase is **59,669 lines of Python** across 13 subpackages (`gpusim` 15.7k, `geometry` 8.4k, `results` 6.0k, `semantic` 6.0k, `idf` 5.4k, `acquisition` 5.0k, `microclimate` 4.2k, `viz` 4.0k, plus `validation`, `scenarios`, `campaign`, `simulation`), backed by 182 `pytest` files (1,937+ tests).

We do **not** want a big-bang rewrite. We want to selectively migrate simulation precompute, ray-traced shading, IDF parsing/compilation, CPU heat-balance solving, result harvesting, and strict data-control boundaries into Rust while keeping Python orchestration, GIS fetchers, `scikit-learn`, `matplotlib`, and Jupyter/WebGL tooling intact.

Target deployment environments:
1. **macOS arm64** (Apple M2 Pro, 12 cores).
2. **Windows x86_64** (NVIDIA RTX A400 workstation).
3. **Linux x86_64 HPC cluster** (Concordia Speed, SLURM, `tcsh` login shell, **no root access**, restricted login node, 32-CPU compute arrays).

We were also struck by **Anthropic's Messages API Python-to-Rust migration post-mortem**, where 98% of integration tests passed while 75% of live traffic initially diverged until they built a shadow-diffing and mismatch-fingerprinting harness.

### Questions
1. **Industry case studies & architectural patterns.** Detail the concrete architectures, boundary designs, and lessons learned from Anthropic (Messages API Python → Rust), Pydantic v2 (`pydantic-core`), Astral (`uv`, `ruff`), Polars, and at least 2 scientific/geospatial Python+Rust projects (e.g., `tiktoken`, `safetensors`, `orjson`, `deltalake`, `arro3`, `geoarrow-rs`, `obstore`). Specifically: what belongs in Rust vs Python, and where did FFI boundary overhead negate speedups?
2. **Packaging & `uv` workspace strategy (D-RS-01).** Compare:
   - (a) Converting the root `pyproject.toml` to `build-backend = "maturin"` (mixed Python+Rust package), vs
   - (b) Keeping `openubem` as a pure-Python `setuptools` package and adding an internal workspace crate/package `openubem-rust` (exposing `openubem._rust`) as an optional/workspace dependency in `uv` with a clean pure-Python fallback.
   How does `uv` editable development (`uv sync`, `maturin develop`, `uv_build`) handle rebuild ergonomics, CI caching, and contributors who do not have `rustc` installed?
3. **Zero-copy FFI & GIL discipline.** Compare `pyo3` (latest stable 0.23–0.27+), `rust-numpy`, `pyo3-arrow` / `arro3`, and `PyCapsule` Arrow C Data Interface for passing: (i) large contiguous `float64`/`float32` tensors `[B, S]` and `[8760, S]`, (ii) Arrow tables / GeoDataFrames, and (iii) thousands of small per-building IDF structs. What are the real memory-safety and alignment pitfalls with `allow_threads` and borrowed NumPy slices?
4. **Anthropic-style differential shadow testing for scientific pipelines.** How do you design a lightweight, deterministic shadow-parity and diff-fingerprinting harness for batch scientific pipelines (inputs = GeoParquet/IDF/EPW/SQLite; outputs = floating-point arrays, manifests, provenance strings)? Cover tolerance bucketing, hash-canonicalization, floating-point non-associativity (`rayon` reduction order), and automated regression gating in `pytest`.
5. **Cross-platform `abi3` wheels & Linux HPC deployment without root.** Explain the exact `abi3` feature configuration (`abi3-py310` vs newer), Windows MSVC build gotchas, `manylinux_2_28` / glibc compatibility on older SLURM HPC clusters, and `maturin-action` + `sccache` CI patterns.
6. **Recommendation.** Propose a concrete Cargo workspace + `uv` project blueprint and rollout sequence tailored to OpenUBEM's 3-platform reality.

### Required output format
- **Executive summary** (≤10 bullets).
- **Table: Python+Rust projects & crates**: name, URL, PyO3/maturin/ABI setup, FFI mechanism (NumPy/Arrow/custom), licence, stars/activity, key takeaway for OpenUBEM.
- **Table: Packaging options (a) vs (b)** across developer DX, CI, contributor friction (no `rustc`), HPC deployment, and release complexity.
- **Table: Measured FFI overhead & reduction-order pitfalls** (with sources).
- Sections answering Q1–Q6.
- **Gaps & negative results**: what you searched for and did not find.

### Rules
- Cite every factual claim (URL / DOI / crate release + date). Mark anything uncited `UNVERIFIED`.
- Distinguish *measured* vs *claimed* speedups and state baseline + hardware.
- Exclude GPL/AGPL crates/examples (OpenUBEM is `Apache-2.0 OR MIT`).
- Search terms to include: "Anthropic Messages API Python to Rust", "PyO3 maturin uv workspace", "rust-numpy zero copy allow_threads", "pyo3-arrow Arrow C data interface", "abi3-py310 manylinux HPC SLURM", "pydantic-core architecture PyO3".
