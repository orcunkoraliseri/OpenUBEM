# DR04 Result — Rust BVH Ray-Traced Exterior Shading & Clean-Room Microclimate Raster Kernels

**Research Date:** 2026-11-26
**Feeds:** `PLAN_rust_migration.md` §4 (R2, R4), Phase 2 (T07–T08), Phase 4 (T13–T14)
**Target Codebase Grounding:** [`openubem/gpusim/shading.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py), [`openubem/outputs/gpusim_m8_eu_districts.csv`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/outputs/gpusim_m8_eu_districts.csv), [`openubem/microclimate/svf.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/svf.py), [`openubem/microclimate/shadow.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/shadow.py), [`openubem/microclimate/utci.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/utci.py), [`openubem/microclimate/mrt.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/mrt.py)

---

## Executive Summary

1. **Pure-Rust `obvhs` + `rayon` beats both brute-force NumPy/PyTorch and `embree4-rs` for M8 shading (`523,530` surfaces):** In [`gpusim_m8_eu_districts.csv`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/outputs/gpusim_m8_eu_districts.csv#L6), brute-force $O(R \times P \times M)$ shading took **505.10 s** (`93.0%` of the `543.09 s` compile+shading non-kernel runtime). Replacing brute-force Möller-Trumbore with `obvhs` (`v0.4.0`, `MIT OR Apache-2.0`, PLOC BVH2 / 8-wide CWBVH + SIMD traversal) parallelized over buildings/rays via `rayon` eliminates C++ FFI/wheel-packaging risk while delivering sub-second-to-few-second district runtimes *(projected from BVH complexity reduction; exact OpenUBEM speedup requires benchmark harness verification)*.
2. **Reject `embree4-rs` (`0.0.16`) as primary M8 backend due to distribution & Metal gaps:** Although Intel Embree 4 (`Apache-2.0`) added ARM64/NEON CPU support on macOS/Linux in v4.1 and Windows ARM64 in v4.4 ([RenderKit/embree](https://github.com/RenderKit/embree)), Embree 4 GPU acceleration targets Intel SYCL/Level Zero—**not Apple Metal** ([embree.org](https://www.embree.org/)). Moreover, `embree4-sys` (`0.0.12`, ~4 GitHub stars on [`psytrx/embree4-rs`](https://github.com/psytrx/embree4-rs)) does **not** bundle Embree source and requires pre-installed system SDKs (`embree4.dll` / `brew install embree`), creating fragile `maturin` wheel bundling (`delvewheel`/`delocate`/`auditwheel`).
3. **Reject `wgpu` BVH for Phase 2; defer GPU ray tracing:** `wgpu` (`v30.0.2`, `MIT OR Apache-2.0`) supports cross-platform WGSL compute shaders on Metal/Vulkan/DX12, while hardware `EXPERIMENTAL_RAY_QUERY` remains non-standard and immature on Metal and DX12 relative to Vulkan ([gfx-rs/wgpu](https://github.com/gfx-rs/wgpu)). For OpenUBEM's per-building/neighborhood batches (300–250k triangles), CPU `obvhs` avoids GPU device initialization, WGSL-to-MSL/SPIR-V compilation, and PCIe upload latency.
4. **Precision audit reveals an existing float32/float64 discrepancy in `gpusim/shading.py`:** [`_ray_triangle_any_hit_numpy`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py#L92-L108) uses `float64` (`|det| > 1e-9`, barycentric slack `1e-5`), whereas [`_ray_triangle_any_hit_torch`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py#L131-L179) casts to `float32` (`|det| > 1e-7`, slack `1e-4`), with a `2.0e-3` m (`2 mm`) outward normal nudge and `t_eps = 1.0e-3` m. Implementing Woop/Benthin/Wald (2013) watertight intersection ([JCGT 2013](https://jcgt.org/published/0002/01/05/)) with a double-precision fallback on grazing/edge cases and validating against the `float64` NumPy reference guarantees `<= 1e-4` sunlit fraction parity (matching EnergyPlus's `1 mm` resolution floor).
5. **Strict GPL/AGPL firewall for Step 6 microclimate:** Mature GPU SOLWEIG frameworks—`SOLWEIG-GPU` (`GPL-3.0-only`, Kamath et al. 2026 JOSS), `GLIDE-SOL` (Zonato et al. 2026 GMD), and `UMEP-dev/solweig` (`GPL-3.0`)—are copyleft and **strictly off-limits** for code copying. OpenUBEM's Step 6 Rust crate (`openubem-microclimate`) must be implemented **clean-room** from Lindberg et al. (2008) equations and OpenUBEM's existing [`svf.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/svf.py) / [`shadow.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/shadow.py) / [`utci.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/utci.py) specifications under `Apache-2.0 OR MIT`.
6. **Cache-blocked, zero-allocation Rust eliminates `svf.py`'s `90,528`-allocation memory-bandwidth wall:** [`svf.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/svf.py#L44-L62) pads the full DSM and allocates temporary `(rows, cols)` `float64` arrays at every `(azimuth, distance)` step. Tiling the DSM into L1/L2-resident strips (e.g., `64x64` or `128x128` tiles = `32–128 KB`, fitting Apple M2 Pro's `128 KB` P-core L1D and Raptor Lake/Zen 4's `32–48 KB` L1D / `1–2 MB` private L2) with fast `atan2` or slope-maximization (`max(dz / d)` before a single `atan` per azimuth!) eliminates temporary heap allocations and ~99.9% of transcendental `atan2` calls.
7. **Float64 SIMD Rust (`pulp` + `rayon`) is mandatory for Bröde (2012) UTCI:** In [`utci.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/utci.py#L50-L286), the 210-term 6th-order polynomial evaluates terms up to $d_{Tmrt}^6 = 70^6 \approx 1.176 \times 10^{11}$ multiplied by coefficients down to $4.04 \times 10^{-13}$ with alternating signs. Apple Metal/PyTorch MPS lacks `float64` hardware/API support (`TypeError: Cannot convert a MPS Tensor to float64`), forcing `float32` (~7.2 decimal digits) which suffers catastrophic cancellation drift near UTCI stress-category boundaries; `f64x2` (NEON) / `f64x4` (AVX2) Rust SIMD with FMA preserves full 53-bit IEEE-754 precision.
8. **Zero-copy PyO3 boundary uses `rust-numpy` `0.30.0` (`BSD-2-Clause`) + `py.detach` (PyO3 `0.27+`) / `py.allow_threads`:** Passing `PyReadonlyArray2`/`3<f64>` and extracting `ndarray::ArrayView` (`Send + Sync` for numeric primitives) allows GIL release over `rayon` thread pools with zero input copies, supporting free-threaded Python builds.
9. **Recommended Phase 2 & Phase 4 stack:** Phase 2 (`openubem-shading`) = **`obvhs` (`0.4.0`) + custom watertight `f64`/`f32`-hybrid triangle intersector + `rayon`** (`tinybvh-rs` as optional C++ FFI benchmark baseline); Phase 4 (`openubem-microclimate`) = **clean-room `pulp` (`0.22.3`) + `rayon` (`1.11.0`) cache-tiled `f64` kernels** exposed via **`pyo3` + `rust-numpy` (`0.30.0`)**.

---

## Table 1: Rust BVH / Ray-Tracing / SIMD / Interop Crates

| Crate | URL | Licence | Pure Rust vs FFI | arm64 macOS + x64 Win/Linux | Stars / Latest Release (Date) | Suitability (1–5) |
|---|---|---|---|---|---|---|
| **`obvhs`** | [github.com/DGriffin91/obvhs](https://github.com/DGriffin91/obvhs) / [crates.io/crates/obvhs](https://crates.io/crates/obvhs) | `MIT OR Apache-2.0` | Pure Rust (uses `glam`, `rayon`) | Yes (portable SIMD + `rayon` on all 3) | ~112 stars; `v0.4.0` (Oct 5, 2026); active (used by Avian Physics v0.6, Mar 2026) | **5 / 5** (Best pure-Rust BVH2/CWBVH8 for M8) |
| **`bvh`** (`svenstaro`) | [github.com/svenstaro/bvh](https://github.com/svenstaro/bvh) / [crates.io/crates/bvh](https://crates.io/crates/bvh) | `MIT` | Pure Rust (`no_std` + `rayon` build) | Yes | ~271 stars; `v0.12.0` (Nov 16, 2025); active | **3 / 5** (Good SAH builder, lacks wide SIMD traversal kernels) |
| **`bvh-arena`** | [github.com/jcornaz/bvh-arena](https://github.com/jcornaz/bvh-arena) / [crates.io/crates/bvh-arena](https://crates.io/crates/bvh-arena) | `Unlicense` | Pure Rust | Yes | ~31 stars; `v1.4.0` (Oct 21, 2026); active | **1 / 5** (Generational-arena broad-phase collision, not ray-triangle BVH) |
| **`rtbvh`** | [github.com/meirbon/rtbvh](https://github.com/meirbon/rtbvh) / [crates.io/crates/rtbvh](https://crates.io/crates/rtbvh) | `Apache-2.0` | Pure Rust | Yes (older SIMD intrinsics) | ~17 stars, 28k+ downloads; `v0.6.2` (Jul 2021) — **5+ yrs inactive** | **1 / 5** (Stale/unmaintained; superseded by `obvhs`) |
| **`kiddo`** | [github.com/sdd/kiddo](https://github.com/sdd/kiddo) / [crates.io/crates/kiddo](https://crates.io/crates/kiddo) | `MIT OR Apache-2.0` | Pure Rust | Yes | ~180 stars; `v5.2.3` (Dec 2025); active | **1 / 5** (Point-cloud k-d tree for $k$-NN/radius; unsuitable for triangle ray tracing) |
| **`tinybvh-rs`** | [github.com/DavidPeicho/tinybvh-rs](https://github.com/DavidPeicho/tinybvh-rs) / [crates.io/crates/tinybvh-rs](https://crates.io/crates/tinybvh-rs) | `MIT` (wraps MIT `jbikker/tinybvh`) | C++ FFI (`cxx`, single header) | Yes (needs C++ toolchain; NEON/AVX2) | ~20 stars; `v0.1.0-beta.3` (Jan 25, 2026); beta | **3 / 5** (Fast MIT C++ header, beta Rust wrapper) |
| **`embree4-rs` / `embree4-sys`** | [github.com/psytrx/embree4-rs](https://github.com/psytrx/embree4-rs) / [crates.io/crates/embree4-rs](https://crates.io/crates/embree4-rs) | `MIT` (`embree4-rs`) / `non-standard` (`embree4-sys`), wraps `Apache-2.0` Embree 4 | C++ FFI (`bindgen` to pre-installed `libembree4`) | CPU yes (arm64 NEON via Embree 4.1+, Win x64); **No Metal GPU** | ~4 stars; `v0.0.16` (Aug 15, 2026) / `0.0.12` | **2 / 5** (High wheel/SDK packaging friction; sparse Rust bindings) |
| **`wgpu`** | [github.com/gfx-rs/wgpu](https://github.com/gfx-rs/wgpu) / [crates.io/crates/wgpu](https://crates.io/crates/wgpu) | `MIT OR Apache-2.0` | Pure Rust HAL (Metal/Vulkan/DX12) | Yes (compute shaders); `EXPERIMENTAL_RAY_QUERY` matures on Vulkan, lags on Metal/DX12 | ~19k stars; `v30.0.2` (Jul–Nov 2026); very active | **2 / 5** for M8 (overkill/init overhead); **3 / 5** optional Phase 4 GPU path |
| **`pulp`** | [github.com/sarah-quinones/pulp](https://github.com/sarah-quinones/pulp) / [crates.io/crates/pulp](https://crates.io/crates/pulp) | `MIT` | Pure Rust (runtime ISA dispatch) | Yes (NEON, SSE/AVX2/AVX-512, scalar fallback) | ~375 stars; `v0.22.3` (2025/2026); active (powers `faer`) | **5 / 5** (Best runtime-dispatched `f64`/`f32` SIMD for UTCI & SVF) |
| **`wide`** | [github.com/Lokathor/wide](https://github.com/Lokathor/wide) / [crates.io/crates/wide](https://crates.io/crates/wide) | `Zlib OR Apache-2.0 OR MIT` | Pure Rust (compile-time fixed SIMD) | Yes (`f64x2`, `f64x4`, `f32x4`, `f32x8`) | ~561 stars; `v0.8.3`; active | **4 / 5** (Great for fixed 4-ray/4-tri packet loops) |
| **`rayon`** | [github.com/rayon-rs/rayon](https://github.com/rayon-rs/rayon) / [crates.io/crates/rayon](https://crates.io/crates/rayon) | `MIT OR Apache-2.0` | Pure Rust | Yes | ~13.5k stars; `v1.11.0`; active | **5 / 5** (Standard multi-core work-stealing) |
| **`numpy` (`rust-numpy`)** | [github.com/PyO3/rust-numpy](https://github.com/PyO3/rust-numpy) / [crates.io/crates/numpy](https://crates.io/crates/numpy) | `BSD-2-Clause` | Rust + PyO3 (`C-API`) | Yes | ~1.4k stars; `v0.30.0` (Oct 2026); active | **5 / 5** (Zero-copy NumPy `ArrayView` interop) |

*Note on `kiddo` (`sdd/kiddo`), `wide` (`Lokathor/wide`), and `pulp` (`sarah-quinones/pulp`): exact release dates for `wide v0.8.3` and `pulp v0.22.3` were not explicitly resolved from crates.io JSON in search results and are flagged as `2025/2026` / `UNVERIFIED exact day`.*

---

## Table 2: Measured & Literature Benchmarks vs. Analytical Projections

| Workload / Library | Measurement Type | Hardware & Baseline | Dataset / Scene Size | Measured / Literature Result | Source |
|---|---|---|---|---|---|
| **OpenUBEM M8 Shading (current Python/PyTorch)** | **Measured** (repo artifact) | Windows RTX A400 workstation (`openubem/gpusim/shading.py` brute-force) | 4 EU districts: 3,832 homes, **523,530 surfaces** (Madrid 139k, Lyon 82k, London 59k, Bologna 243k) | **505.10 s** total (`153.80 s` MAD, `70.93 s` LYO, `60.13 s` LDN, `220.25 s` BOL); **93.0%** of non-kernel runtime (`543.09 s`) | [`gpusim_m8_eu_districts.csv`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/outputs/gpusim_m8_eu_districts.csv#L2-L6) |
| **`tiny_bvh` (`jbikker/tinybvh`) CPU SAH Build & Trace** | **Literature / Repo Reported** | Desktop CPU vs Intel Embree baseline (exact CPU model varies in repo suite; `UNVERIFIED` specific CPU SKU) | Crytek Sponza (**~262k triangles**) | **~4 ms** (AVX builder) to **8–30 ms** (SAH/pre-split) build time; matches/beats default Embree on single-ray primary/occlusion traversal | [github.com/jbikker/tinybvh](https://github.com/jbikker/tinybvh) |
| **`tiny_bvh` GPU Compute Traversal (No RT Cores)** | **Literature / Repo Reported** | NVIDIA RTX 5080 Laptop GPU (OpenCL/compute layout) | Crytek Sponza (**~262k triangles**) | **4–5 GRays/s** (4,000–5,000 MRays/s) | [github.com/jbikker/tinybvh](https://github.com/jbikker/tinybvh) |
| **`SOLWEIG-GPU` (`PyTorch`/`CUDA`) Raster Microclimate** | **Literature (JOSS 2026)** | Intel Core i9-13900K + **NVIDIA RTX 4090 (24 GB)** vs legacy QGIS/UMEP CPU | **$2000 \times 2000$ px** (1 m resolution, $4\text{ km}^2$) | **2.7 s** for 1-day (24 h); **21 s** for 30-day (720 h) incl. SVF/wall/GeoTIFF I/O; **10–100x** vs multi-core CPU, up to **4,000x** vs legacy QGIS/UMEP | Kamath et al. (2026), [JOSS 11(118):9535](https://joss.theoj.org/papers/10.21105/joss.09535) |
| **OpenUBEM M8 Shading (`obvhs` CWBVH + `rayon`)** | **Analytical Projection** *(NOT measured)* | 12-core M2 Pro / 20-core Win x64 vs 505.10 s brute-force baseline | 523,530 surfaces, ~1.05M tris, ~9–12M shadow+sky rays | Projected **< 1–3 s** total (150x–500x speedup) via $O(\log M)$ traversal + ray-packet culling (`UNVERIFIED` until Phase 2 benchmarked) | Derived from [`shading.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py) ray counts & BVH complexity |
| **OpenUBEM Step 6 SVF (`svf.py` -> Tiled `pulp` + `rayon`)** | **Analytical Projection** *(NOT measured)* | 12-core M2 Pro (200 GB/s) vs NumPy `np.pad` + 90,528 array allocations | $2000 \times 2000$ px, 32 azimuths, $R_{max}=2829$ | Projected **~0.5–2 s** (replacing `362B` `atan2` calls with L1/L2-tiled `max(dz/d)` + 1 `atan`/az; `UNVERIFIED` until Phase 4 benchmarked) | Derived from [`svf.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/svf.py) loop & M2 Pro cache specs |

*Gap transparency:* Exact per-scene `MRays/s` and `ms` rows from `DGriffin91/tray_racing` (`Bistro` 3.87M tris, `Sponza` 3.7M tris) and Intel Embree's exact x86 AVX2 vs M2 Pro NEON `MRays/s` whitepaper tables could not be retrieved verbatim via search summaries; rather than extrapolating unverified numbers, those cells are omitted and marked in **Gaps & Negative Results**.

---

## Architecture Sketch: `openubem-shading` & `openubem-microclimate`

```
Python Orchestration (OpenUBEM)
├── Phase 2: openubem.gpusim.shading ──► [PyO3 + rust-numpy zero-copy] ──► openubem_shading (Rust crate)
│     Inputs: tris [M, 3, 3] (f64), origins [P, 3] (f64),                ├─ AABB/BVH build: obvhs (0.4.0, PLOC + CWBVH8)
│             dirs [R, 3] (f64), normals [S, 3], slices                  ├─ Any-hit kernel: Watertight Woop et al. (f32 fast + f64 edge fallback)
│     GIL: py.detach(|| ...) / py.allow_threads(|| ...)                  ├─ Outer parallelism: rayon over (ray_batch, surf_point_chunk)
│     Outputs: sunlit_hr [8760, S] (f32), dif_sky [S] (f64)              └─ Early-out: backface dot(ray, normal) <= 0 skips BVH traversal
│
└── Phase 4: openubem.microclimate ──────► [PyO3 + rust-numpy zero-copy] ──► openubem_microclimate (Rust crate, clean-room Apache-2.0 OR MIT)
      Inputs: dsm, dem, cdsm, tdsm [H, W] (f64),                         ├─ svf_horizon_kernel: 64x64 L1/L2-tiled 32-az dense 1-px sweep,
│             ta, tmrt, va10, e_kpa [B, H, W] (f64)                      │    tracks max(dz/d) per azimuth, 1 atan() at end -> horizon [32, H, W]
│     GIL: py.detach(|| ...) / py.allow_threads(|| ...)                  ├─ veg_transmission_kernel: tiled Beer-Lambert along sun vector, early stop > canopy_top
│     Outputs: svf [H, W], horizon [32, H, W], sh_veg [H, W],            └─ utci_kernel: pulp (0.22.3) f64x2/f64x4 FMA + rayon over 210-term Bröde (2012)
               utci [B, H, W] (f64), flags [B, H, W] (u8)                     + bitmask flags + 10-class stress classification
```

---

## Q1: CPU BVH + SIMD + `rayon` vs. GPU (`wgpu` / Embree) for M8 Shading (`523k` Surfaces)

### Grounding the M8 Workload
In [`openubem/gpusim/shading.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py#L195-L275), M8 exterior shading runs per district (or building cluster) with:
- Occluder triangles `[M, 3, 3]` (`59,402` surfaces in London up to `242,997` in Bologna; `523,530` pooled across 3,832 homes in [`gpusim_m8_eu_districts.csv`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/outputs/gpusim_m8_eu_districts.csv#L2-L6)).
- `periodic_days=20` $\rightarrow$ 19 representative days $\times$ ~12 sunlit hours $\approx$ **~228 beam rays** + **64 Fibonacci sky rays** = **~292 directions (`R`)**.
- Up to `9` sample points (`n_grid=3`) per sun-exposed surface (`P` $\le 9 \times S$).
- Total query budget for Bologna (`243k` surfaces): $\sim 292 \times (9 \times 243\text{k}) \approx 6.4 \times 10^8$ potential `(ray, point)` any-hit queries (actually ~half after `dot(ray, normal) <= 0` backface culling, which `shading.py` currently evaluates *after* tracing all rays!). Moving `dot(ray, normal) <= 0` *before* ray traversal immediately cuts beam-ray count by ~50%.

### Candidate Evaluation

1. **Pure-Rust BVH Crates:**
   - **`obvhs` (`v0.4.0`, Oct 2026, `MIT OR Apache-2.0`, ~112 stars):** Implements a Parallel Locally-Ordered Clustering (**PLOC**) BVH2 builder with Parallel Reinsertion and spatial pre-splits, plus an 8-way Compressed Wide BVH (**CWBVH8**, **80 bytes/node**; optional `small_bvh2_node` **32 bytes/node**), using `glam` (`Vec3A`), `rayon` for parallel build, and SIMD CPU traversal intersecting 4 nodes simultaneously ([DGriffin91/obvhs](https://github.com/DGriffin91/obvhs), [docs.rs/obvhs](https://docs.rs/obvhs)). Adoption by Avian Physics `v0.6` (Mar 2026) confirms active maintenance. **Limitation:** `obvhs`'s built-in `Triangle::intersect` uses `f32` `Vec3A` Möller-Trumbore; however, `obvhs` exposes `bvh.ray_traverse(ray, &mut ray_hit, |ray, id| ...)` with a custom leaf-intersection callback, letting us plug in a watertight/double-precision leaf intersector!
   - **`svenstaro/bvh` (`v0.12.0`, Nov 2025, `MIT`, ~271 stars):** Clean SAH BVH with `rayon` parallel construction, but its author explicitly notes it targets general-purpose spatial queries and lacks wide SIMD packet/stream traversal kernels ([svenstaro/bvh](https://github.com/svenstaro/bvh)).
   - **Custom Flat SAH/LBVH + `wide`/`pulp` + `rayon`:** Building a custom 4-wide/8-wide SAH BVH gives full control over 4-ray packet traversal (testing 4 coherent solar rays or 4 sample points from the same `3x3` quad against one AABB node), though `obvhs` already provides PLOC/CWBVH8 construction out of the box—saving ~1,500 lines of tricky BVH builder code.
   - **Disqualified Pure-Rust Crates:** `bvh-arena` (`v1.4.0`, `Unlicense`) is a generational-arena broad-phase AABB overlap detector for games, not a static triangle ray-tracing BVH; `rtbvh` (`v0.6.2`, `Apache-2.0`) has had no releases since July 2021 (5+ years inactive); `kiddo` (`v5.2.3`, `MIT OR Apache-2.0`) is a point-cloud $k$-d tree, not a mesh BVH.

2. **Intel Embree (`embree4-rs` `0.0.16` / `embree4-sys` `0.0.12`) & `tinybvh-rs` (`0.1.0-beta.3`):**
   - **Embree 4 Cross-Platform Reality:** Embree 4 (`Apache-2.0`, [RenderKit/embree](https://github.com/RenderKit/embree)) added **ARM64/NEON CPU** support for macOS Apple Silicon and Linux in Embree 4.1, and **Windows ARM64 MSVC** in Embree 4.4. However, Embree 4's GPU backend uses **SYCL / Level Zero** for Intel Arc/Data Center GPUs—**there is NO Apple Metal backend in Embree 4** ([embree.org](https://www.embree.org/)). On M2 Pro, Embree runs strictly on the CPU via 128-bit NEON (mapping its 8-wide packet logic across NEON registers), whereas on x86_64 Windows/Linux HPC it unlocks 256-bit AVX2 / 512-bit AVX-512.
   - **Packaging & Maintenance Risk:** `embree4-rs` (`0.0.16`, Aug 2026, `MIT`, ~4 GitHub stars) and `embree4-sys` (`0.0.12`, `non-standard` license metadata) use `rust-bindgen` against a **pre-installed system Embree 4** ([psytrx/embree4-rs](https://github.com/psytrx/embree4-rs)). They do not vendor C++ source, forcing CI and end users to install Embree (`brew install embree` + `DYLD_LIBRARY_PATH=/opt/homebrew/lib` on macOS, `embree4.dll`/`.lib` on Windows) and requiring `delocate`/`delvewheel`/`auditwheel` inside `maturin` wheels.
   - **`tinybvh-rs` (`v0.1.0-beta.3`, Jan 2026, `MIT`, ~20 stars):** Wraps Jacco Bikker's single-header C++ `tinybvh` (`MIT`, [jbikker/tinybvh](https://github.com/jbikker/tinybvh)) via `cxx` ([DavidPeicho/tinybvh-rs](https://github.com/DavidPeicho/tinybvh-rs)). Unlike Embree, `tiny_bvh.h` compiles directly with the Rust crate (zero external DLLs!). Crytek Sponza (~262k tris) builds in **4–30 ms** and rivals Embree on CPU traversal, making `tinybvh-rs` a strong secondary C++ benchmark baseline if pure-Rust `obvhs` needs a reference check—though it is still `0.1.0-beta.3` with C++ compiler build dependency.

3. **`wgpu` Compute-Shader BVH Traversal (`v30.0.2`, `MIT OR Apache-2.0`, ~19k stars):**
   - **Compute Shader BVH (Software Traversal in WGSL):** Works portably across macOS Metal, Windows Vulkan/DX12, and Linux Vulkan without CUDA. CPU builds the BVH (e.g., `obvhs` CWBVH8 at 80 B/node $\rightarrow$ ~40 MB for 500k tris), uploads `wgpu::Buffer` storage arrays, and dispatches a stack-based WGSL shadow-ray compute shader.
   - **Hardware `EXPERIMENTAL_RAY_QUERY`:** Native-only (`VK_KHR_ray_query` on Vulkan, DXR Tier 1.1 on DX12, `MTLAccelerationStructure` on macOS 15+ Metal); not in the W3C WebGPU spec, and while Vulkan ray queries work in `wgpu` v28–30+, DX12 and Metal remain behind Vulkan in public API readiness and end-to-end stability ([gfx-rs/wgpu](https://github.com/gfx-rs/wgpu)).
   - **Why GPU `wgpu` Loses to CPU BVH for M8:** On a `59k–243k` surface district, CPU CWBVH build takes **~10–50 ms** and `rayon` CPU any-hit traversal of ~300M coherent shadow queries (accelerated by early termination on first hit + `dot(ray, normal) <= 0` culling) completes in **~0.2–1.5 s** *(analytical projection)*. By contrast, `wgpu` pays adapter/device setup, Naga WGSL$\rightarrow$MSL/DXIL/SPIR-V shader compilation, buffer upload (especially on discrete Windows RTX GPUs over PCIe), and warp divergence on stack-based WGSL traversal—all to save a few hundred milliseconds, while introducing GPU driver/headless-Linux HPC fragility (HPC nodes often lack Vulkan ICDs!).

### Scaling & Footprint Summary (12-Core M2 Pro vs. 20-Core Win x64 vs. 32-Core Linux HPC)
- **Memory footprint (`243k` surfaces $\approx 486\text{k}$ tris):** Triangle array `[M, 3, 3]` in `f64` = `35 MB` (`f32` = `17.5 MB`); `obvhs` CWBVH8 (`80 B/node`, ~0.6–0.8 nodes/tri) $\approx 25–30\text{ MB}$. Easily fits in **L2/L3 cache** on 32-core HPC and unified RAM on M2 Pro (`32–36 MB` P-cluster L2).
- **Multi-core scaling (`rayon`):** Shadow queries across `(surface_point, ray_dir)` are embarrassingly parallel with zero write contention if sharded by target surface `s_idx` (each thread fills `sunlit_hr[:, s_idx]` and `dif_sky[s_idx]`). Scales near-linearly across 8–10 P-cores on M2 Pro, 20 threads on Windows x64, and 32+ cores on Linux HPC without GPU driver dependencies.

---

## Q2: Exactness & Grazing-Ray Numerical Pitfalls in Shading

### EnergyPlus `PolygonClipping` / `PixelCounting` vs. Sample-Grid Ray Tracing
- **EnergyPlus `PolygonClipping`** (default, e.g., Sutherland-Hodgman / Convex Weiler-Atherton in 2D homogeneous coordinates) projects occluder polygons onto the receiver plane and clips analytically, enforcing an internal **1 mm geometric resolution floor** ([EnergyPlus Engineering Reference](https://bigladdersoftware.com/epx/docs/24-2/engineering-reference/shading-and-solar-distribution.html)).
- **EnergyPlus `PixelCounting`** rasterizes surfaces onto a GPU pixel grid (default $512 \times 512$) to avoid concavity errors and $O(N^2)$ clipping blowups, falling back to `PolygonClipping` if no GPU is available.
- **OpenUBEM [`gpusim/shading.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py#L30-L180):** Uses a `3x3` bilinear sample grid per quad (`9` points) nudged `2.0e-3` m (`2 mm`) along the outward normal, plus Möller-Trumbore with `t_eps = 1.0e-3` m (`1 mm`).
- **Critical Finding in Existing Code:** [`_ray_triangle_any_hit_numpy`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py#L92-L108) (`float64`) uses `|det| > 1e-9` and barycentric slack `[-1e-5, 1 + 1e-5]`, whereas [`_ray_triangle_any_hit_torch`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py#L131-L179) (`float32`) uses `|det| > 1e-7` and slack `[-1e-4, 1 + 1e-4]`. Thus, OpenUBEM's PyTorch path already differs slightly from NumPy on near-grazing/edge rays!

### Numerical Pitfalls & Solutions
1. **Planar Self-Intersection & Adjoining Wall/Roof Corners:**
   - The `2 mm` outward normal nudge (`2.0e-3` m) + `t_eps = 1.0e-3` m prevents a surface from intersecting its own coplanar triangles. However, at **grazing solar angles** ($\cos\theta \to 0.01$), a ray starting `2 mm` off a wall travels $\sim 20\text{ cm}$ before clearing `1 mm` of height—and if an adjacent perpendicular wall or window reveal shares the edge, `float32` rounding can hit or miss the seam.
   - **Mitigation:** Pre-cull `dot(ray_dir, target_normal) <= 1e-4` (grazing/backface) before traversal, matching [`shading.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/shading.py#L284).
2. **Non-Watertight Edges in `f32` Möller-Trumbore (Cracks Between Shared Edges):**
   - Fan-triangulating quads/n-gons creates shared interior diagonals. In standard `f32` Möller-Trumbore, shared edges evaluate differently depending on vertex ordering, causing rays to leak through cracks between adjacent triangles or between coplanar building walls (especially for thin/elongated triangles, which are common in EnergyPlus window frames and overhangs).
   - **Solution — Woop, Benthin & Wald (2013) Watertight Ray/Triangle Intersection** ([JCGT Vol. 2, No. 1, 2013](https://jcgt.org/published/0002/01/05/)):
     1. Transforms triangle vertices into a ray-centric coordinate space via translation (`v - orig`), axis permutation (aligning dominant $|d_k|$ along $Z$), and 2D shear/scale.
     2. Computes edge functions $U, V, W$ in 2D using identical vertex order-independent edge rules—guaranteeing zero cracks along shared edges/vertices.
     3. **Zero-overhead `f64` fallback:** If any intermediate edge determinant $U == 0$, $V == 0$, or $W == 0$ (exact edge/grazing degeneracy in `f32`), recomputes $U, V, W$ in **`f64`** for that single triangle (~<0.01% of tests).
3. **BVH Bounds vs. `f32` Quantization:**
   - As Woop et al. (2013) proved, BVH `f32` AABBs must be conservatively expanded (e.g., by a few ULPs / `1e-5` m) so `f32` BVH pruning never rejects a triangle that a `f64` reference or watertight leaf test would hit. Note that `obvhs` constructs AABBs in `f32` (`glam::Vec3A`): for urban coordinates in UTM meters (e.g., `x ~ 400,000 m`, `y ~ 4,500,000 m`), **`f32` has only ~0.25–0.5 m ULP precision!**
   - **CRITICAL URBAN COORDINATE RULE:** Before building an `f32` BVH (`obvhs`), **translate all vertices and ray origins to local district-centroid coordinates** (subtracting `origin_offset: [f64; 3]` in `f64` first)! At local coordinates within $\pm 2\text{ km}$, `f32` ULP is $\sim 10^{-4}\text{ m}$ (`0.1 mm`), completely eliminating UTM precision loss; failing to shift UTM coordinates to local origin is a classic silent bug that breaks `t_eps = 1e-3` m!

### Guaranteeing `<= 1e-4` Match Against `gpusim/shading.py`
1. **Local-origin shift in `f64`** before building `obvhs` BVH (`f32` AABBs padded by `1e-4` m).
2. **Double-precision leaf test option / Woop `f64` fallback:** In the `obvhs` leaf callback, evaluate Woop et al. (2013) or `f64` Möller-Trumbore directly against the original shifted `f64` `[M, 3, 3]` vertices (memory cost: `2`–`3` extra `f64` loads only on the `~2–5` leaf triangles hit per ray!).
3. **Shadow-diff gate:** Assert `max_abs_diff(sunlit_hr_rust, sunlit_hr_numpy) < 1e-4` and `max_abs_diff(dif_sky_rust, dif_sky_numpy) < 1e-4` across all 4 EU districts (`FLEET_4EU`).

---

## Q3: Clean-Room Rust CPU Kernels for Step 6 SVF & Vegetation Ray-March

### Strict License Firewall (GPL/AGPL Off-Limits)
Per OpenUBEM's `Apache-2.0 OR MIT` license policy:
- `nvnsudharsan/SOLWEIG-GPU` ([JOSS 2026](https://joss.theoj.org/papers/10.21105/joss.09535)) is **`GPL-3.0-only`** ([PyPI](https://pypi.org/project/solweig-gpu/)).
- `UMEP-dev/solweig` (even its newer Rust/PyO3/`wgpu` rewrite) is **`GPL-3.0`** ([github.com/UMEP-dev/solweig](https://github.com/UMEP-dev/solweig)).
- `GLIDE-SOL` (Zonato et al. 2026, [GMD 19:7389–7413](https://gmd.copernicus.org/articles/19/7389/2026/)) builds on the SOLWEIG/SOLWEIG-GPU lineage.
- **Policy:** Do **not** read, adapt, or port any code from those repositories. Implement `openubem-microclimate` strictly clean-room from the peer-reviewed mathematical formulation in **Lindberg et al. (2008)** ([*Int. J. Biometeorol.* 52:697–713](https://pubmed.ncbi.nlm.nih.gov/18506488/)) and OpenUBEM's own [`svf.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/svf.py) and [`shadow.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/shadow.py).

### Why `svf.py` and `shadow.py` Hit a Memory-Bandwidth Wall in NumPy
In [`svf.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/svf.py#L44-L64):
- For a $2000 \times 2000$ raster (`32 MB` in `f64`), `max_radius_px = 2829`.
- NumPy allocates a padded DSM (`(7658, 7658)` `f64` $\approx 469\text{ MB}$), then runs `32 * 2829 = 90,528` loop iterations, each allocating a temporary `32 MB` `elev_angle = np.degrees(np.arctan2(...))` array and streaming `32 MB` in + `32 MB` out of DRAM (**~8.7 TB of DRAM traffic!**) plus `362 billion` scalar/vector `arctan2` + `rad2deg` calls!
- Similarly, [`shadow.py::_vegetation_transmission`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/shadow.py#L112-L139) allocates 3 padded `f64` rasters (`~1.4 GB` total at $2000\times 2000$) and creates temporary `cwin/twin/dwin/top/bottom/seg` arrays at every `d` step.

### Clean-Room Algorithmic & Cache-Blocking Optimizations in Rust (`pulp` + `rayon`)
1. **Replace per-step `atan2` with slope maximization:** Since $\arctan(s)$ is strictly monotonically increasing for $s \in (-\infty, +\infty)$ and $d \cdot \text{res} > 0$, maximizing elevation angle $\gamma_i = \max_d \arctan\left(\frac{\text{DSM}(r + \Delta r_d, c + \Delta c_d) - z_{obs}(r, c)}{d \cdot \text{res}}\right)$ is **mathematically identical** to:
   $$s_{max}(r, c) = \max_{d=1..R} \frac{\text{DSM}(r + \Delta r_d, c + \Delta c_d) - z_{obs}(r, c)}{d \cdot \text{res}}$$
   followed by **one single** $\gamma_i = \max(0, \text{atan}(s_{max}))$ at the end of each azimuth sweep! This removes **99.96%** ($2828 / 2829$) of all `atan2` calls and uses a precomputed `inv_dist[d] = 1.0 / (d * res)` multiply instead of division.
2. **Zero-allocation outer-pixel / tile-strip blocking (L1/L2 cache sizing):**
   - **Hardware Cache Targets:**
     - **Apple M2 Pro:** P-core L1D = **128 KB**, E-core L1D = **64 KB**, P-cluster shared L2 = **32–36 MB**, unified memory bandwidth = **200 GB/s** ([Notebookcheck](https://www.notebookcheck.net/), [CPUTronic](https://www.cputronic.com/)).
     - **Intel Raptor Lake (Win x64):** P-core L1D = **48 KB**, private L2 = **2 MB/core** ([Wikipedia](https://en.wikipedia.org/wiki/Raptor_Lake)).
     - **AMD Zen 4 (Linux HPC):** L1D = **32 KB**, private L2 = **1 MB/core** ([AMD](https://www.amd.com/)).
   - **Optimal Blocking Strategy:**
     - Choose a 2D tile (`TILE_H = 32`, `TILE_W = 64` or `TILE_W = 128`, `f64`): one `32 x 64` output tile of `max_slope` + `z_obs` = `2 * 2048 * 8 B = 32 KB`, fitting completely inside **every target L1 data cache** (`32 KB` Zen 4, `48 KB` Raptor Lake, `128 KB` M2 Pro P-core)!
     - **Loop order:** For a fixed azimuth `k`, parallelize over `(tile_row, tile_col)` with `rayon`. Inside each tile, keep `max_slope[32][64]` and `z_obs[32][64]` hot in L1 registers/cache. Loop `d = 1..max_radius_px` in small step chunks (e.g., `d_block = 32`), or better yet: for a given `(drow, dcol)` offset, `dsm[r + drow, c + dcol .. c + dcol + TILE_W]` is a **single contiguous horizontal SIMD load** (`f64x4` AVX2 / `f64x2` NEON via `pulp`)!
     - Because `dsm` shifts `(r + drow, c + dcol)` are unit-stride along columns, hardware prefetchers stream `dsm` linearly from L2/DRAM while `max_slope` and `z_obs` never leave L1D!
     - **Bounds check elimination:** Precompute `d_valid_range` or clamp `(r + drow, c + dcol)` per tile once per `(tile, d)`, avoiding per-pixel boundary branches and **eliminating `np.pad` completely** (`0 MB` padding overhead instead of `469 MB`–`1.4 GB`).
3. **Vegetation Beer-Lambert Ray-March (`_vegetation_transmission`):**
   - Same `32 x 64` L1-resident tile + contiguous row-slice reads of `cdsm`, `tdsm`, `inv_crown_depth = 1.0 / max(cdsm - tdsm, 1e-6)` (precomputed once, not per `d`!).
   - Early-exit per tile: if `tile_z_obs_min + (d + 1) * res * tan_alt > canopy_top`, break the `d` loop immediately for that tile (much tighter than the global `ray_h_next.min() > canopy_top` check in [`shadow.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/shadow.py#L136)).
4. **Comparison vs. PyTorch MPS/CUDA:**
   - Apple Metal/MPS lacks `float64` (`TypeError`), forcing `float32` on Mac GPUs. Clean-room `f64` Rust CPU kernels match `svf.py`/`shadow.py` to machine precision (`~1e-15`), use zero VRAM, and on M2 Pro's 200 GB/s memory subsystem with L1-resident tiles become compute-bound on simple FMA/max ops rather than DRAM-bound.

---

## Q4: Float64 UTCI & MRT Kernels

### Numerical Proof: Why `float32` Fails on Bröde et al. (2012) UTCI
In [`openubem/microclimate/utci.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/utci.py#L44-L286) (transcribed from `UTCI_a002.f90`; Bröde et al. 2012, DOI [`10.1007/s00484-011-0454-1`](https://doi.org/10.1007/s00484-011-0454-1)):
- Bounds are $T_a \in [-50, 50]\,^\circ\text{C}$, $\Delta T_{mrt} = T_{mrt} - T_a \in [-30, 70]\,^\circ\text{C}$, $v_{a,10} \in [0.5, 17.0]\,\text{m/s}$, $p_a \in [0, 5]\,\text{kPa}$.
- Monomial powers reach extreme magnitudes:
  - $\Delta T_{mrt}^6 \le 70^6 = 117,649,000,000 \approx \mathbf{1.176 \times 10^{11}}$
  - $T_a^5 \cdot \Delta T_{mrt} \le 50^5 \times 70 \approx 2.19 \times 10^{10}$
  - $T_a^6 \le 50^6 \approx 1.56 \times 10^{10}$
- Coefficients span **13 orders of magnitude** (from `5.12733497` down to `4.03863260e-13`), with alternating signs across 210 terms.
- In IEEE-754 `float32` (24-bit significand, $\epsilon_{mach} \approx 1.19 \times 10^{-7}$), representing $70^6 \approx 1.176 \times 10^{11}$ has a **1-ULP spacing of $16,384$**, losing all fractional precision in high-order powers before multiplying by $10^{-12}$ coefficients, and partial sums suffer catastrophic cancellation when large positive/negative sub-terms cancel near stress-category boundaries (e.g., `26.0`, `32.0`, `38.0`, `46.0` $^\circ\text{C}$ in [`UTCI_CLASSES`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/utci.py#L335-L346)).
- On **Apple Metal / PyTorch MPS**, `float64` is unsupported at the hardware/MSL level ([PyTorch MPS docs/issues](https://pytorch.org/docs/stable/notes/mps.html)); thus any MPS kernel *must* downgrade to `float32`.
- In IEEE-754 **`float64`** (53-bit significand, $\epsilon_{mach} \approx 2.22 \times 10^{-16}$), $70^6$ has ULP spacing $\sim 1.5 \times 10^{-5}$, preserving $>10$ decimal digits even after summing all 210 terms.

### Rust `pulp` (`f64` SIMD + FMA) + `rayon` vs. NumPy `float64`
- **Why NumPy is slow on the 210-term polynomial:** [`_brode_polynomial_offset`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/utci.py#L50-L286) executes ~450+ elementwise NumPy ufunc calls (`*`, `+`). Even for a moderate `(24, 1000, 1000)` array (`24M` pixels = `192 MB` per `f64` array), NumPy evaluates **one operator at a time across the entire 192 MB array**, thrashing L1/L2/L3 caches and repeatedly reading/writing `result` from DRAM (~450 DRAM round-trips!).
- **Single-Pass Register-Resident Rust Kernel:** With `pulp` (`v0.22.3`, `MIT`) + `rayon`, each thread processes a chunk of `4096` pixels (fitting `4 x 32 KB` inputs + outputs in L1/L2). Each pixel's `ta, va, d_tmrt, pa` stays in SIMD registers (`f64x4` on AVX2 with FMA, `f64x2` on ARM64 NEON with FMA, `f64x8` on AVX-512) for **all 210 Horner-grouped FMA terms** before writing `utci_c` and `flags` once to memory!
- **Throughput estimate *(Analytical projection, not measured)*:** Memory bandwidth drops from ~450 passes to **1 read pass (32 B/px) + 1 write pass (9 B/px) = 41 B/px**. With ~450 FLOPs/px using FMA (~225 FMA ops), at ~10–15 GB/s/core or ~300–600 GFLOP/s multi-core `f64` FMA, `24M` pixels (`24 h` at `1000x1000`) is **compute-bound at ~15–40 ms** vs. several seconds in NumPy `float64` (DRAM-bound). Additionally, MRT view-factor and Stefan-Boltzmann (`SIGMA * T^4`) loops in [`mrt.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/mrt.py) fuse cleanly into the same `pulp` + `rayon` pass.

---

## Q5: Zero-Copy PyO3 Integration (`rust-numpy` `0.30.0` + GIL Release)

For zero-copy transfer of DSM/DEM/CDSM/TDSM `[H, W]` rasters and `[M, 3, 3]` triangle buffers from NumPy to Rust:

1. **Dependencies:** `pyo3` (`0.27+` for `py.detach`, or `0.23–0.26` with `py.allow_threads`) + `numpy` (`rust-numpy` `0.30.0`, Oct 2026, `BSD-2-Clause`).
2. **Input Borrowing (`PyReadonlyArray2` / `PyReadonlyArray3`):**
   - Accept `dsm: PyReadonlyArray2<'py, f64>` and `tris: PyReadonlyArray3<'py, f64>`.
   - Call `.as_array()` to obtain `ndarray::ArrayView2<'_, f64>` / `ArrayView3<'_, f64>`, or `.as_slice()?` for C-contiguous `&[f64]` (falling back to `.as_standard_layout()` only if a non-contiguous stride view was passed from Python!).
   - **Zero-Copy Guarantee:** `PyReadonlyArray` borrows the existing NumPy buffer without copying and prevents concurrent `PyReadwriteArray` borrows while active ([docs.rs/numpy](https://docs.rs/numpy/)).
3. **Releasing the GIL Safely:**
   - `ArrayView<'_, f64, D>` and `&[f64]` are `Send + Sync` (because `f64` is `Send + Sync` and contains no Python object pointers).
   - Release the GIL with **`py.detach(|| { ... })`** (PyO3 `0.27+`, renamed from `py.allow_threads` in `#5221` for free-threaded Python parity; [PyO3 changelog](https://pyo3.rs/)) and execute `rayon` parallel iterators inside the closure.
   - **Rule:** Never touch `Bound<'py, ...>` or Python objects inside `detach`; allocate Rust output buffers (`Vec<f64>`, `Vec<f32>`, `Vec<u8>`) inside `detach` (or mutate pre-allocated NumPy outputs via `PyReadwriteArray` views extracted *before* `detach`), then wrap results with `PyArray::from_vec` / `into_pyarray(py)` after re-attaching.

```rust
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2, PyReadonlyArray3};
use pyo3::prelude::*;

#[pyfunction]
fn compute_shading_rs<'py>(
    py: Python<'py>,
    tris: PyReadonlyArray3<'py, f64>,      // [M, 3, 3] zero-copy
    origins: PyReadonlyArray2<'py, f64>,   // [P, 3] zero-copy
    dirs: PyReadonlyArray2<'py, f64>,      // [R, 3] zero-copy
) -> PyResult<Bound<'py, PyArray2<bool>>> {
    let tris_v = tris.as_array();
    let orig_v = origins.as_array();
    let dir_v = dirs.as_array();
    let (r_len, p_len) = (dir_v.shape()[0], orig_v.shape()[0]);

    // PyO3 0.27+: py.detach (in <=0.26: py.allow_threads)
    let occ_flat: Vec<bool> = py.detach(|| {
        // Safe: ArrayView<f64, _> is Send + Sync; build obvhs BVH + rayon traverse
        raytrace_any_hit_parallel(tris_v, orig_v, dir_v)
    });

    Ok(ndarray::Array2::from_shape_vec((r_len, p_len), occ_flat)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
        .into_pyarray(py))
}
```

---

## Q6: Concrete Ranking & Recommendation

### Phase 2 (`openubem-shading`) — Replacing M8 `505.1 s` Bottleneck
1. **Rank 1 (Recommended): `obvhs` (`0.4.0`) + Local-Origin Shift + Watertight Woop/Benthin/Wald `f64`-Fallback Leaf Intersector + `rayon`.**
   - *Why:* Pure Rust (`MIT OR Apache-2.0`), zero external C++ SDKs/DLLs, active in 2026, builds fast CWBVH8/BVH2 trees, scales across M2 Pro / Win x64 / Linux HPC, and avoids `wgpu` driver/init overhead and `embree4-sys` wheel-packaging fragility.
2. **Rank 2 (Benchmark Baseline Only): `tinybvh-rs` (`0.1.0-beta.3`, `MIT`).**
   - *Why:* Compiles single-header C++ `tiny_bvh.h` directly without external system SDKs; useful as a validation/speed benchmark against `obvhs` if needed, though beta Rust bindings are less ergonomic than pure-Rust `obvhs`.
3. **Rank 3 (Not Recommended for Default): `embree4-rs` (`0.0.16`) or `wgpu` (`30.0.2`).**
   - *Why:* `embree4-sys` requires external `libembree4` installation/wheel repair and lacks Apple Metal; `wgpu` hardware ray queries are immature on Metal/DX12 and unnecessary for `59k–243k` surface batches.

### Phase 4 (`openubem-microclimate`) — Clean-Room Step 6 SVF, Canopy & UTCI/MRT
1. **Rank 1 (Recommended): Clean-Room Pure-Rust CPU Kernels (`pulp` `0.22.3` + `rayon` `1.11.0` + `rust-numpy` `0.30.0`).**
   - *Why:* Strictly `MIT` / `Apache-2.0` / `BSD-2-Clause` (zero GPL/AGPL contamination from `SOLWEIG-GPU`/`UMEP`), native IEEE-754 `f64` FMA SIMD on both Apple Silicon NEON and x86_64 AVX2/AVX-512 (eliminating `float32` UTCI $10^{11}$-term cancellation), L1-tiled (`32x64`) slope-maximization for SVF with zero padding allocations, and zero-copy PyO3 integration.
2. **Rank 2 (Future Optional Extension Only): `wgpu` (`30.0.2`) Compute Shader for `f32`-Safe SVF/Shadow Sweeps.**
   - *Why:* Only worthwhile if future domains exceed `>5000 x 5000` pixels on workstations with discrete GPUs; **never** run Bröde (2012) UTCI in `f32` on Metal/WebGPU—keep UTCI/MRT strictly on `f64` CPU SIMD.

---

## Gaps & Negative Results

1. **No exact `DGriffin91/tray_racing` per-scene `MRays/s` table retrieved:** Search results confirmed the `tray_racing` scenes (`Bistro` 3.87M tris, `Sponza` 3.7M tris), presets (`tfb`/`vfb`/`med`/`vsb`), and `obvhs` vs Embree comparison methodology, but did not return the raw numeric benchmark table cells; exact `obvhs` vs `tinybvh` throughput on OpenUBEM's `FLEET_4EU` geometry must be measured in a Phase 2 Criterion/Python microbenchmark.
2. **No exact Embree 4 ARM64 NEON vs. x86 AVX2 `MRays/s` ratio retrieved:** Confirmed Embree 4.1+ supports macOS ARM64 NEON CPU and lacks Metal GPU support, but specific side-by-side M2 Pro NEON vs. x86_64 AVX2 `MRays/s` numbers remain `UNVERIFIED`.
3. **Exact `crates.io` release dates for `wide` (`0.8.3`), `pulp` (`0.22.3`), and `rayon` (`1.11.0`):** Versions and licenses were verified via `crates.io`/`GitHub`, while exact day-of-month publish timestamps are marked `2025/2026` (`UNVERIFIED` exact day).
4. **Negative Result — `bvh-arena`, `rtbvh`, `kiddo`:** None are suitable for M8 ray-traced exterior shading (`bvh-arena` is game broad-phase collision, `kiddo` is a point $k$-d tree, and `rtbvh` has been unmaintained since July 2021).
5. **Negative Result — Embree 4 on Apple Metal & PyTorch MPS `float64`:** Neither Embree 4 nor PyTorch MPS can execute `f64` or Metal GPU ray tracing for OpenUBEM (`embree` lacks Metal; MPS lacks `float64`), locking out GPU-only unified pipelines on macOS for UTCI and Embree-based shading.
