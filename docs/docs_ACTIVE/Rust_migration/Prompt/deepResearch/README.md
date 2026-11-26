# Deep Research Prompts — Selective Python-to-Rust Migration for OpenUBEM

Parent plan: [`../../PLAN_rust_migration.md`](../../PLAN_rust_migration.md)

Each prompt is **self-contained**: paste the whole file (from `## PROMPT` down) into a deep-research tool (Claude Research, ChatGPT Deep Research, Gemini Deep Research, Perplexity, etc.). Save each output as `results/DRxx_result.md` in this folder so it can be reviewed against the plan before starting Phase 1.

**Status 2026-11-26:** prompts written; awaiting research runs and owner decisions (`D-RS-01`..`D-RS-06`).

| ID | File | Question in one line | Priority |
|---|---|---|---|
| DR01 | [DR01_rust_python_scientific_migration_architecture.md](DR01_rust_python_scientific_migration_architecture.md) | How do top teams (Anthropic, Pydantic, Astral, Polars) structure hybrid Python+Rust migrations, shadow-diffing, and cross-platform `maturin`/`uv` builds? | **Run first** |
| DR02 | [DR02_rust_idf_epw_bem_ecosystem.md](DR02_rust_idf_epw_bem_ecosystem.md) | What Rust BEM/IDF/EPW crates exist, and how do we build a fast, deterministic IDF parser/compiler/3D extruder replacing `eppy`/`geomeppy`? | **Run first** |
| DR03 | [DR03_rust_data_control_schemas_provenance.md](DR03_rust_data_control_schemas_provenance.md) | How can Rust ADTs, physical unit newtypes, Arrow/GeoArrow schemas, and `cargo-deny` enforce strict data control across Python pipelines? | **Run first** |
| DR04 | [DR04_rust_bvh_shading_and_microclimate_kernels.md](DR04_rust_bvh_shading_and_microclimate_kernels.md) | CPU BVH + SIMD + `rayon` vs `wgpu` for our 505 s M8 shading bottleneck, plus clean-room Apache/MIT Rust kernels for Step 6 SVF/UTCI? | High |
| DR05 | [DR05_rust_cpu_thermal_solver_and_gpu_interop.md](DR05_rust_cpu_thermal_solver_and_gpu_interop.md) | How should a pure-Rust CPU thermal solver coexist with our existing CUDA/Metal `gpusim` kernels without duplicating physics bugs? | High |
| DR06 | [DR06_rust_results_harvester_and_geospatial_parity.md](DR06_rust_results_harvester_and_geospatial_parity.md) | How fast is parallel Rust SQLite/CSV harvesting into Parquet, and when does Rust `geo`/`geos` beat or diverge from `shapely` 2.0? | Medium |

## Rules every prompt enforces
- Every claim cites a source (URL, DOI, or repo plus commit/release/version). Uncited claims are labelled `UNVERIFIED`.
- For GitHub repos and crates, report stars/downloads, last commit/release date, licence, and whether it is actively maintained (flag 2+ years inactive). Reject GPL/AGPL dependencies (OpenUBEM is `Apache-2.0 OR MIT`).
- Separate **measured benchmarks** (with hardware, dataset size, and baseline stated) from **claimed** or **theoretical** speedups.
- Say plainly when something does not exist. A negative result is a useful result.
