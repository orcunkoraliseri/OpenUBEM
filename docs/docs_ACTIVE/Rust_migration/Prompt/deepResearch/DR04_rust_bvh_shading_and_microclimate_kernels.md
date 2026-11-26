# DR04 — Rust BVH Ray-Traced Exterior Shading & Clean-Room Microclimate Raster Kernels

**Feeds:** Plan §4 (R2, R4), Phase 2 (T07–T08), and Phase 4 (T13–T14)
**Save output to:** `results/DR04_result.md`

---

## PROMPT

You are a graphics, ray-tracing, and scientific GPU/SIMD engineer specialising in CPU BVH acceleration, portable SIMD in Rust, `wgpu` compute shaders, and urban microclimate radiation modeling. Produce a rigorous, source-cited benchmark and design report.

### Context
OpenUBEM has two ray-marching / ray-intersection bottlenecks currently implemented in pure Python/NumPy/PyTorch:

1. **M8 exterior 3D shading precompute (`openubem/gpusim/shading.py:68-160`):**
   - Computes per-surface hourly beam sunlit fractions `sunlit_frac[H, S]` (`H` sunlit hours, up to 9 sample points per surface) and isotropic sky diffuse shading ratios against surrounding context triangles (`Shading:Site:Detailed`) and self-shading polygons.
   - Currently runs brute-force $O(R \times P \times M)$ Möller-Trumbore with no BVH.
   - **Measured M8 bottleneck (`openubem/outputs/gpusim_m8_eu_districts.csv:6`):** across 4 European districts (3,832 homes, 523,530 3D surfaces) on the Windows RTX A400 workstation, shading precompute took **505.1 s (8.4 min)** out of 2,898.8 s total (**93% of all non-kernel runtime**): Madrid `153.8 s` (139k surfaces), Lyon `70.9 s` (82k surfaces), London `60.1 s` (59k surfaces), Bologna `220.2 s` (243k surfaces).
2. **Step 6 outdoor microclimate (`openubem/microclimate/svf.py`, `shadow.py`, `utci.py`):**
   - `svf.py`: dense 1-pixel stepping along 32 azimuths out to `max_radius_px` (geometric stepping previously failed the analytic canyon gate by 0.33 at $H/W=0.5$), allocating full padded float64 rasters at every step.
   - `shadow.py::_vegetation_transmission`: Beer-Lambert path length through `[TDSM, CDSM]` canopy layers per hour.
   - `utci.py`: 6th-order UTCI polynomial with terms up to $\sim 10^{11}$, where float32 on Apple Metal (MPS lacks float64) risks numerical drift (`PLAN_gpu_accelerated_simulation.md:179`).
   - **Strict licence rule:** Mature GPU SOLWEIG repositories (`SOLWEIG-GPU`, `SOLWEIG-CUDA`, `UMEP-dev/solweig`) are **GPL/AGPL** and strictly off-limits for code copying (`Apache-2.0 OR MIT` only).

### Questions
1. **CPU BVH + SIMD + `rayon` vs GPU (`wgpu`/Embree) for M8 shading (`523k` surfaces).**
   Evaluate the fastest permissively licensed (`Apache-2.0 OR MIT` or `Apache-2.0` Intel Embree C++ FFI) solutions in Rust for shadow-ray any-hit queries (`[R, P]` against `[M]` triangles per building/neighbourhood):
   - Pure-Rust BVH crates (`bvh`, `bvh-arena`, `obvhs`, `kiddo`, or a custom flat SAH/LBVH + `wide` / `pulp` 4-ray or 8-triangle packet SIMD + `rayon`),
   - Intel Embree (`embree4-rs` / `embree-rs`, Apache-2.0 — note: check arm64 macOS support via Embree 4 NEON/Metal vs x86_64!),
   - `wgpu` compute-shader BVH traversal (runs on both Mac Metal and Windows Vulkan/DX12 without CUDA toolkit).
   Compare build/traversal speed, memory footprint, multi-core scaling (12-core M2 Pro, 20-core Windows, 32-core Linux HPC), and maintenance risk.
2. **Exactness & grazing-ray numerical pitfalls in shading.** EnergyPlus `PolygonClipping` / `PixelCounting` vs Möller-Trumbore sample-grid (`t_eps = 1e-3`, planar self-intersection, watertight triangle intersection e.g. Woop/Benthin/Wald). How do we guarantee BVH matches our brute-force reference `gpusim/shading.py` within `1e-4`?
3. **Clean-room Rust CPU kernels for Step 6 SVF & vegetation ray-march.** How fast can a cache-tiled, zero-allocation float64 `rayon` + SIMD Rust kernel execute Lindberg (2008) 32-azimuth dense 1-px SVF horizon sweeps and canopy Beer-Lambert integration compared to NumPy's `np.pad` + shifted-slice loop (`svf.py`) and PyTorch MPS/CUDA? Include cache-blocking strategies (strip/tile sizing to stay in L1/L2 cache on M2 Pro and x86_64).
4. **Float64 UTCI & MRT kernels.** Benchmark or estimate throughput of evaluating the 6th-order Bröde et al. (2012) UTCI polynomial in float64 SIMD Rust (`rayon` over `(B, H, W)` pixels) vs NumPy float64, confirming complete elimination of float32 $10^{11}$-term cancellation error.
5. **Zero-copy PyO3 integration.** Best pattern to pass DSM/DEM/CDSM/TDSM rasters and triangle buffers `[M, 3, 3]` from NumPy to Rust without copies (`rust-numpy` `PyReadonlyArray2`/`3`, releasing the GIL).
6. **Recommendation.** Rank the exact implementation choice for Phase 2 (`openubem-shading`) and Phase 4 (`openubem-microclimate`).

### Required output format
- **Executive summary** (≤10 bullets).
- **Table: Rust BVH / ray-tracing / SIMD crates**: name, URL, licence, pure-Rust vs FFI, arm64 macOS + x64 Windows/Linux support, stars/activity, suitability (1–5).
- **Table: Measured/literature benchmarks** (rays/sec or speedup vs brute-force NumPy/CPU, hardware & baseline cited).
- **Architecture sketch** for `openubem-shading` and `openubem-microclimate`.
- Sections answering Q1–Q6.
- **Gaps & negative results**.

### Rules
- Cite every factual claim (URL / DOI / crate release + date). Mark anything uncited `UNVERIFIED`.
- Verify licences of every crate and underlying C/C++ library (must be `Apache-2.0`, `MIT`, `BSD`, or `Zlib` compatible; reject GPL/AGPL).
- Search terms to include: "rust bvh crate obvhs bvh-arena benchmark", "embree4-rs macos arm64 neon", "rust simd wide pulp ray triangle moller trumbore", "wgpu ray tracing bvh compute shader rust", "SOLWEIG horizon angle tiled cache CPU SIMD", "UTCI polynomial float64 SIMD".
