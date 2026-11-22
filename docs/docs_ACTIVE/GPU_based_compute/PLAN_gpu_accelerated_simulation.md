# PLAN — GPU-Accelerated (and Generally Faster) Building Energy Simulation for OpenUBEM

**Date:** 2026-11-22 (rev. 2: DR01–DR06 results reviewed)
**Workspace Root:** `/Users/orcunkoraliseri/Desktop/OpenUBEM`
**Status:** PLANNING. Research done (`Prompt/deepResearch/results/DR01–DR06_result.md`) and reviewed in §11. No code changed yet.
**Research prompts:** [`Prompt/deepResearch/`](Prompt/deepResearch/README.md) (DR01–DR06)
**Owner decision needed before Phase 2+:** see [§9 Open Decisions](#9-open-decisions-owner)

---

## 0. TL;DR (read this first)

1. **EnergyPlus cannot be "run on the GPU". Confirmed by DR01.** There is no CUDA/HIP/SYCL/Kokkos/OpenACC port of the E+ core anywhere. `energyplus -j` only parallelises G-function generation (verified: `energyplus --help` on 23.1). The OpenMP experiment was removed in v8.0. ORNL's CUDA trial on ScriptF (Adams & New 2018) found that kernel-launch overhead cancelled the gains. NG1 stands.
2. **The only native GPU feature is `ShadowCalculation → PixelCounting`** (Penumbra, OpenGL 2.1+). DR02 measured it **on this M2 Pro**: `5ZoneAirCooled` + 400 context shading surfaces went from **67.7 s to 13.9 s (4.86×)** with a site-energy delta of **0.005%**. With 0 context surfaces it is **slower** (0.76×), because the GPU setup overhead outweighs the gain below about 200 shading surfaces. This is a toy model; it still has to be shown on our real tail buildings (Phase 0/2).
3. **Our M2 Pro runs E+ 23.1 under Rosetta 2.** `/Applications/EnergyPlus-23-1-0/energyplus` is an x86_64 binary (verified with `file`). E+ 24.2, also installed, is native arm64. DR02 measured it **11–23% faster** on this machine. Every runtime in §1.1 is therefore a Rosetta number.
4. **The bottleneck is the tail, not the median.** Median 3.2 s, p99 233 s, max 907 s. In `austin_centre` the top 10 buildings use 40% of the CPU time. The cheapest large wins are on the CPU: LPT ordering, cutting the shading cost of tail buildings, and typical-floor multipliers (DR02, DR05).
5. **The "exponential" (10³–10⁴×) speedup only comes from a GPU-batched fast tier.** DR03 recommends a **VDI 6007 7R2C** network per zone: exact ZOH discretisation done in float64, an 8,760-step `lax.scan` rollout in float32, and `vmap` over buildings × scenarios. It is calibrated by autodiff against E+. **No one has published a GPU-batched building-stock RC benchmark** (negative result), so our throughput numbers will be the first. The tier is opt-in, carries its own provenance, and is never presented as EnergyPlus output.
6. **ML emulator (DR04): do not fine-tune BuildingsBench.** It is a short-term load forecaster with no envelope or retrofit inputs, and its zero-shot error on residential buildings is about 79% NRMSE. If we build an emulator, it should be a GBDT or TCN **residual on top of the Phase 3 ROM**, with conformal intervals and a mandatory fallback to E+.
7. **Step 6 microclimate (DR06):** port it with PyTorch (`cuda`/`mps`) plus `array-api-compat` as one code path. The mature GPU SOLWEIG repos are **GPL/AGPL**. OpenUBEM is Apache-2.0 OR MIT, so we can learn from their algorithms but **must not copy their code**.

**Recommended order (unchanged, now evidence-backed):** Phase 0 measure → Phase 1 CPU/scheduling wins → Phase 2 PixelCounting (only if Phase 0 shows a large shading share) → Phase 3 GPU ROM tier → Phase 4 residual emulator (optional) → Phase 5 microclimate GPU (side track).

---

## 1. Current State (verified on disk 2026-11-22)

| Item | Where | Fact |
|---|---|---|
| Runner | `openubem/simulation/runner.py` | `energyplus -w EPW -d DIR -x -r IDF`, one subprocess per building, `SIM_TIMEOUT_S = 3600` |
| Fan-out | `openubem/simulation/parallel.py` | `joblib.Parallel(n_jobs=config.N_JOBS, backend="loky")`. Tasks are dispatched **in manifest order** with the default `batch_size="auto"` (no cost-aware ordering). joblib 1.6.0 is installed. |
| Cores | `openubem/config.py:122` | `N_JOBS = SLURM_CPUS_PER_TASK or -1`, so it is already HPC-aware |
| EnergyPlus | `config.ENERGYPLUS_VERSION = "23.1"` | Pinned, with a fail-fast version handshake. **macOS 23.1 binary = x86_64 (Rosetta 2)**. 24.2 (arm64) and 22.1 are also installed in `/Applications`. |
| Timestep | `openubem/idf/templates/*_base.idf:31` | `Timestep, 6;` (10-min) |
| Solar distribution | templates, `Building` object | `FullExterior` |
| Shading calc | templates | **No `ShadowCalculation` object**, so E+ defaults apply: PolygonClipping, Periodic 20 d, max figures 15000, resolution 512 (IDD-verified) |
| Context shading | Step 3 | 20 m context buildings as opaque shading surfaces. No shading `Transmittance Schedule` is used, so PixelCounting's forced-opaque behaviour is harmless here. |
| Outputs | `openubem/idf/outputs.py` | `trim_hourly` option exists (RunPeriod meters only) |
| Post-run | `-r` flag | readVarsESO writes `eplusout.csv`. This is **a hard dependency** of `openubem/results/european_campaign.py` and `openubem/campaign/eu_cell_runner.py` (they read the CSV directly), plus the Stage-5 fallback in `results/parser.py`. |
| Local hardware | dev machine | Apple **M2 Pro, 12 cores**, Apple GPU (Metal), **no CUDA** |
| GPU hardware | Windows workstation | NVIDIA CUDA GPU (model/VRAM not yet recorded) |
| Microclimate | `openubem/microclimate/{svf,shadow,mrt,solar,utci}.py` | NumPy raster code, CPU |

### 1.1 Runtime distribution (from 8 validation manifests, `status == success`, `wall_clock_s > 0.5`; E+ 23.1 x86_64 under Rosetta on the M2 Pro)

| Stat | Value |
|---|---|
| Runs | 2,048 |
| Median | 3.2 s |
| p90 | 9.8 s |
| p99 | 232.8 s |
| Max | 906.9 s |
| `austin_centre` | 341 bldgs, 9,940 CPU-s total, top-5 = 26%, top-10 = 40%, slowest = 907 / 631 / 418 / 351 / 311 s |

**Implication:** for a typical district, (a) ordering the tail first (LPT scheduling) and (b) making the *largest, many-zone* buildings cheaper will cut wall time more than anything applied uniformly to every building. With LPT, the 12-core lower bound for `austin_centre` is max(9,940/12, 907) = **907 s** (DR05).

---

## 2. Goals & Non-Goals

### Goals
- G1. Cut **wall-clock time per district** (makespan) and **CPU-hours per campaign**, with numbers from a fixed benchmark.
- G2. Use GPUs where they actually help: shading, batched surrogate physics, microclimate rasters.
- G3. Add a **fast screening tier** that can evaluate N buildings × M scenarios orders of magnitude faster than EnergyPlus, with stated error bounds against EnergyPlus.
- G4. Keep every acceleration **opt-in, default-OFF**, reproducible, and recorded in provenance.

### Non-Goals
- NG1. Rewriting or forking EnergyPlus's core heat-balance solver for CUDA. **Confirmed out of scope by DR01** (no credible base exists, plus five structural blockers: causal time-stepping, branch divergence, small sparse matrices, stiff implicit DAEs, and AoS memory layout).
- NG2. Replacing EnergyPlus as the reference engine, or putting surrogate numbers into headline results without labelling them.
- NG3. Changing anything under protected paths (`docs/docs_VALIDATION/`, etc.) or default outputs of existing validated runs.
- NG4. Vendoring or copying GPL/AGPL code (SOLWEIG-GPU, SOLWEIG-CUDA, UMEP-dev/solweig, UrbanSolarCarver) into OpenUBEM (Apache-2.0 OR MIT).

---

## 3. Guardrails (never violate)

1. **Default behaviour unchanged.** Each acceleration is a config flag (`openubem/config.py`), default OFF. A run with no overrides must produce byte-identical IDFs and statistically identical results.
2. **Accuracy gate for every speed change.** Every change that alters physics or numerics (timestep, shading method, zone multipliers, surrogate) must report, against the reference E+ run on the benchmark set: annual EUI error per building (median, p95), heating and cooling end-use error **reported separately** (so opposite biases cannot cancel), and hourly-profile CV(RMSE)/NMBE (ASHRAE Guideline 14 style). Default acceptance targets (owner may revise): **median |ΔEUI| ≤ 1%, p95 ≤ 3%** for "E+-equivalent" changes. Fast/surrogate tiers get the separate budget in §5 Phase 3.
3. **Provenance.** Results from a non-E+ engine are stamped (e.g. `engine = "rom_gpu_v1"` / `"emulator_v1"`) and written to separate columns or files. They are never merged silently into `04_simulation_manifest.parquet` / `05_results.gpkg` as if they were E+ output.
4. **Pinned versions.** Any E+ version change (e.g. 23.1 → 24.2 for native arm64) is a separate, explicitly approved migration.
5. **Silent fallback must be loud.** Any feature that E+ can silently disable (PixelCounting falls back to PolygonClipping when no OpenGL context exists) must be checked after each run (`eplusout.eio` / `.err`) and recorded in the manifest.
6. **Licences.** New dependencies must be compatible with Apache-2.0 OR MIT. GPL/AGPL projects are for reading only.
7. **Git hygiene.** Scope git commands with pathspecs (the repo is huge): `git status --porcelain -- openubem/ scripts/ tests/ docs/docs_ACTIVE/GPU_based_compute/`.

---

## 4. Candidate Solution Space (updated with DR evidence)

"Evidence" says where each number comes from: **M** = measured by DR02 on this M2 Pro (toy model), **L** = literature/docs, **H** = still a hypothesis.

| # | Approach | GPU? | Expected gain (evidence) | Fidelity risk | Effort | Phase |
|---|---|---|---|---|---|---|
| A | LPT (longest-first) ordering, `batch_size=1`, cost proxy → fitted predictor | No | makespan → the `max(ΣT/P, T_max)` floor; up to ~1.9× on tail-heavy districts (L: LPT ≤ 4/3 − 1/3m of optimal; H for our districts) | none | S | 1 |
| B | Pre-expand HVACTemplates once (drop `-x`); keep `-r` but measure it; optional native CSV via `OutputControl:Files` | No | ExpandObjects 0.07 s (M); ReadVarsESO 2.4 s on a 10 MB ESO (M), which is large next to a 3.2 s median | none (CSV contract kept) | S | 1 |
| C | `PerformancePrecisionTradeoffs` (Mode01–04, Representative Surfaces), shading update frequency, `Timestep 6→4`, `Disable Self-Shading` groups | No | Mode04 2.6–2.8× on a 100-zone FCU model, <0.34% elec / ~1% gas (L: E+ I/O Ref §1.5.17); Timestep 6→4 is H | low–med (gated) | S | 1 |
| D | Typical-floor / banded zone multipliers for high-rise tail buildings | No | 2–3× (L: Chen & Hong 2018) up to 11–12× (L: E+ Tips&Tricks, 60→9 zones) | medium: +2.6% source energy (Chen & Hong); up to 76–91% monthly error if height variation is left on | M | 1 |
| E | Context-shading simplification (merge to convex boxes, cull non-obstructing) | No | 3–10× on shading-heavy runs (L/H) | low–med (gated) | M | 1 |
| F | Scale-out: SLURM arrays with LPT bin-packed shards (10–30 min each), local scratch/tmpfs, physical cores only | No | linear in nodes; 1:1 arrays are bad for 3 s tasks (L) | none | M | 1 |
| G | **PixelCounting** exterior shading | **Yes** (OpenGL) | 4.86× on a 400-shade toy model (M); 2× average (L: Hoover & Dogan 2017); **slower below about 200 shading surfaces** | very low for opaque context (0.005%, M) | S | 2 |
| H | E+ 23.1 → 24.2 (native arm64 on Mac) | No | 1.13–1.30× on M2 Pro (M) | 0.04% (M) | M (migration) | decision §9 |
| I | In-process `pyenergyplus` with state reuse | No | ~2.5% (M), **dropped** | — | — | — |
| J | **GPU-batched ROM** (VDI 6007 7R2C, ZOH, JAX/PyTorch), calibrated to E+ | **Yes** | 10³–10⁴× per scenario sweep (H, theoretical; nothing published) | medium–high (own budget) | L | 3 |
| K | **Residual ML emulator** (GBDT annual / TCN hourly on top of J) + conformal + E+ fallback | **Yes** | 10³–10⁵× inference in-distribution (L) | high out of distribution | L | 4 |
| L | **Microclimate on GPU** (PyTorch + array-api-compat; optional CuPy RawKernel for SVF) | **Yes** | 25–41× measured for SOLWEIG-GPU on an RTX A6000 (L) | none if exact | M | 5 |
| M | GPU shading/irradiance precompute fed back to E+ (`Imported` + `Schedule:File:Shading`) | **Yes** | removes the shading share (H) | medium: loses diffuse/longwave from context unless also passed via `SurroundingSurfaces` | L | only if G fails |
| — | GPU port of EnergyPlus core | Yes | 0× (infeasible) | — | XL | **dropped (DR01)** |

---

## 5. Phased Plan

### Phase 0 — Baseline & Profiling (gate for everything else)
**Goal:** know where the time goes before optimizing.

- 0.1 Fix a **benchmark set** (`scripts/bench/gpu_bench_set.json`, new): `austin_centre` (tail-heavy, 341 bldgs), one European district (e.g. `ES-MAD-BERRUGUETE`, 1,119 bldgs), and the **20 slowest buildings** across all validation manifests (the "tail set").
- 0.2 `scripts/bench/profile_energyplus.py` (new). Per building, record: wall time, n_zones, n_surfaces, n_subsurfaces, n_shading_surfaces, HVAC family, warmup days (`eplusout.eio`), E+ `Elapsed Time` from `eplusout.err`, and a `PerformancePrecisionTradeoffs;` perflog row (runtime + oscillating hours) when enabled.
- 0.3 **Differential ablation on the tail set** (DR02 §7, no code changes to E+):
  - B0 = current CLI.
  - B1 = pre-expanded IDF, no `-x`/`-r`, so B0 − B1 = auxiliary overhead.
  - B2 = B1 + `Solar Distribution = MinimalShadowing`, so B1 − B2 = **shading share**. This is the Amdahl ceiling for PixelCounting, context simplification and the Imported route.
  - B3 = B1 + `PixelCounting`, which tests the GPU directly.
  - B4 = B1 + `Timestep, 4`.
  - B5 = B1 + `PerformancePrecisionTradeoffs` Mode04.
- 0.4 Function-level profile of 3 tail buildings. The macOS E+ binaries keep their C++ symbols, so `sample <pid> 30 -mayDie` / Instruments works as shipped. Use `perf record -g` on Linux and VTune on Windows. Group the time by module: SolarShading, HeatBalance/ScriptF, HVAC, Output.
- 0.5 **Rosetta check:** rerun the tail set with E+ 24.2 arm64 (timing only, no results adopted) to size the §9.4 decision.
- 0.6 Fit a **runtime predictor** (Ridge/LightGBM on log-time). Until it exists, use the zero-training proxy `n_zones × (n_surfaces + n_shading_surfaces)` (DR05). It drives LPT (1A) and the timeout policy.
- **Deliverable:** `RESULTS_phase0_baseline.md` (this folder), with the shading share, the zone-count → runtime curve, the Rosetta factor, and the current makespan per district.
- **Exit criterion:** the shading share and HVAC/heat-balance share are known for the tail set.

### Phase 1 — Cheap CPU-side wins (no GPU, highest ROI)
- 1A **LPT scheduling** in `run_neighbourhood`: sort `fresh` by predicted cost, descending; `Parallel(..., batch_size=1, pre_dispatch="2*n_jobs")`; optionally `return_as="generator_unordered"` (joblib ≥1.4) so manifest rows stream out as buildings finish. Flag: `SIM_SCHEDULE = "manifest" | "lpt"` (default `manifest`). Measure makespan against the 907 s floor. No physics change.
- 1B **Aux overhead:** (i) run ExpandObjects once at IDF-build time and drop `-x` (flag); (ii) **keep `-r` by default**, because the EU campaign extractors read `eplusout.csv`. Measure its cost in 0.3. If it matters, evaluate native CSV output (`OutputControl:Files`) as a replacement, keeping the same column headers.
- 1C **Numerics sensitivity on the tail set** (each behind a flag, gated by §3.2): `PerformancePrecisionTradeoffs` Mode01–04 (watch oscillating hours) and `Use Representative Surfaces`; `Timestep 6 vs 4`; shading update frequency 20 → 30 d; `Disable Self-Shading` zone groups. Do not touch warmup limits (DR02: risks convergence failures).
- 1D **Typical-floor / banded multipliers** for buildings above N zones (opt-in): explicit ground floor, 2–3 height-banded typical floors × `Zone Multiplier`, and an explicit top floor. Handle the height-variation effects (`Site:HeightVariation`) explicitly, because DR02 cites up to 76–91% monthly error if they are ignored. Must pass the gate per archetype. This is the largest expected tail win if Phase 0 shows HVAC/heat balance dominating.
- 1E **Context-shading simplification** (opt-in): merge each neighbour into convex boxes and cull surfaces that never obstruct. Gate on EUI and peak load.
- 1F **Scale-out recipe** (DR05 §Q6): SLURM array of LPT bin-packed shards (10–30 min each, `--array=0-N%M`), `--hint=nomultithread` (one E+ per physical core), work dirs on `$SLURM_TMPDIR` or `/dev/shm` with retained files copied out, and resume via the existing `_split_resume`.
- **Exit criterion:** a before/after table of benchmark makespan and CPU-hours, with accuracy-gate results.

### Phase 2 — Native E+ GPU shading (PixelCounting)
DR02 answered the 2.1 questions. Facts to build on:
- E+ 23.1 IDF snippet (field names and defaults verified against the 23.1 IDD; identical in 24.2): `ShadowCalculation, PixelCounting, Periodic, 20, 15000, SutherlandHodgman, 512, SimpleSkyDiffuseModeling, No, No, No;`
- Requires **OpenGL 2.1+** with VAO/FBO, through GLFW. It works on the M2 Pro (both 23.1 Rosetta and 24.2 arm64, with no fallback warning).
- **Fallback is silent apart from a warning:** without a context, `.err` gets "No GPU found (required for PixelCounting)" / "PolygonClipping will be used instead". To verify, check the line `Shadowing/Sun Position Calculations Annual Simulations` in `eplusout.eio`.
- Linux headless needs `xvfb-run` (llvmpipe CPU raster, slow) or an NVIDIA Xorg/VirtualGL. Stock builds have no EGL. **On Windows:** force the NVIDIA dGPU for `energyplus.exe` (Settings → Display → Graphics → High performance), and run in an active console session, since disconnected RDP sessions and services may fall back to the Microsoft Basic renderer.
- Shading surfaces are treated as opaque (issue #9059), which is fine for us (§1).

Steps:
- 2.1 Add opt-in `SIM_SHADING_METHOD = "PolygonClipping" | "PixelCounting" | "auto"`. `auto` uses PixelCounting only when the building's shading-surface count is above a threshold (start at 200 and tune it from 0.3/B3). The default writes nothing, so IDFs stay byte-identical.
- 2.2 Post-run check: parse `eplusout.eio` and record `shading_method_effective` in the manifest (guardrail 3.5).
- 2.3 Benchmark on the M2 Pro and on the Windows NVIDIA workstation. Also measure **concurrent processes sharing one GPU** (4 / 8 / 12 workers), because contention there is untested.
- 2.4 Accuracy gate (§3.2) and a speed table on the tail set and benchmark districts.
- **Exit criterion:** keep it if it gives ≥1.3× on the tail set and passes the gate; otherwise document and drop. Only if the shading share stays above 30–50% after this, consider candidate M (GPU precompute + `Imported`).

### Phase 3 — GPU fast tier: batched reduced-order physics (the "exponential" path)
Design from DR03 (adopted as the starting point; revisit after the 3.1 prototype):
- **Model:** VDI 6007-1 **7R2C** per zone (separate air/fast and structure/slow capacitances). Buildings are bucketed by zone count Z ∈ {1, 2, 4, 8}, with padded states and inter-zone coupling. Many-zone dwellings are aggregated into zone groups.
- **Parameters:** initialised analytically from OpenUBEM's own Step 2/3 data using VDI 6007 / TEASER rules (TEASER and EUReCA serve as reference implementations). They are then fine-tuned by **constrained autodiff calibration** of per-archetype multipliers on physical terms only, never an unconstrained neural correction, to keep retrofit extrapolation sound.
- **Numerics:** exact ZOH (`expm` of the augmented [A B; 0 0]Δt) in **float64 on CPU**, then an hourly **float32** rollout. A branch-free HVAC clamp: free-float step → required power from the deadband → clamp to capacity → linear superposition. Energy conversion uses E+-consistent `CAPFT`/`EIRFT`/`EIRFPLR` curves.
- **Solar/context:** ROMs cannot see 20 m context. Hourly per-facade incident irradiance must be **precomputed** (from E+ shading output via `Output External Shading Calculation Results = Yes`, or from the Phase 5 GPU raster/ray tooling).
- **Framework:** **JAX** (`lax.scan` + `vmap`, best autodiff) on **WSL2 + CUDA** on the Windows workstation, with CPU float64 on the Mac. **PyTorch** (native Windows CUDA + MPS) is the fallback if WSL2 is unacceptable. Decision in §9.6.
- **Acceptance budget (screening tier, DR03 Q7; owner to confirm):** per-archetype annual heating and cooling NMBE ≤ ±5% (district ≤ ±3%), monthly CV(RMSE) ≤ 15%, hourly CV(RMSE) ≤ 30%, annual peak ≤ ±15%, and retrofit-ranking Spearman ρ ≥ 0.90 on **held-out retrofit runs** (not only the baseline).

Steps:
- 3.1 Prototype on CPU (NumPy/JAX float64) for one archetype family against existing E+ runs: parameter extraction + ZOH + HVAC clamp, with no calibration yet. This shows the uncalibrated error.
- 3.2 Add calibration (Optax/Adam with positivity constraints) on a training split. Validate on held-out buildings, climates and retrofits.
- 3.3 Batch on GPU: bucketing, float32 rollout, and a float32-vs-float64 drift check on 50 buildings (< 10⁻³ °C, < 0.01% EUI). Measure **building-years per second** on the Windows GPU, recording precision and hardware. Nobody has published this number.
- 3.4 Integration: new optional `openubem/fast/` emitting `04f_fast_manifest.parquet` with `engine` provenance. It never overwrites Step 4/5 artifacts.
- **Exit criterion:** documented throughput and an error budget that the owner accepts for screening use.

### Phase 4 — Residual ML emulator (optional, after Phase 3)
Revised by DR04: **do not fine-tune BuildingsBench or ResCast** (they are autoregressive load forecasters with no envelope/HVAC/retrofit inputs and poor zero-shot residential accuracy). If we pursue this:
- 4a: an ensemble of 5 LightGBM/XGBoost models predicting **disaggregated** annual/monthly end-uses, as a **residual on the Phase 3 ROM** (y = y_RC + f_ML), wrapped in split conformal intervals (MAPIE).
- 4b (hourly): a residual TCN/TSMixer.
- OOD gates (category/range, Mahalanobis, interval width) route buildings to E+. All shortlisted or Pareto candidates are re-simulated in E+, because DR04 cites a case with <1% annual error where 16.7% of Pareto picks still flipped.
- Training data: our E+ archive. Real volume to be counted; DR04's "tens of thousands" figure is unverified. Use grouped splits (by district, climate year and HVAC family), never random rows.
- Licences: avoid GPL (`besos`, `fastep`) and LGPL (`deepxde`).

### Phase 5 — Microclimate (Step 6) on GPU (side track, independent)
- Backend: **PyTorch** (`mps` on the Mac, `cuda` on Windows) through `array-api-compat` plus a device/dtype helper, so one code path serves both. Add an optional CuPy `RawKernel` only for the fused SVF horizon sweep and the vegetation ray-march on NVIDIA.
- Pre-port gate: run the existing analytic-canyon/UTCI tests in **float32 vs float64** (the UTCI polynomial has terms up to about 10¹¹, and MPS has no float64).
- Keep `svf.py`'s dense 1-px stepping (geometric spacing failed the canyon gate). Bound `max_radius_px` by terrain height, tile large domains, and batch hours as `(B, H, W)`.
- Exactness gate: max abs difference vs the NumPy reference within tolerance.
- SOLWEIG-GPU (GPL-3.0, 25–41× measured on an RTX A6000) is a **benchmark and algorithm reference only** (NG4).

---

## 6. Benchmark & Acceptance Protocol

| Metric | Definition |
|---|---|
| Makespan | wall-clock from first dispatch to last result, per district; compare to the `max(ΣT/P, T_max)` floor |
| CPU/GPU-hours | sum of per-task wall time × devices |
| Throughput | building-years simulated per hour (E+), building-years per second (fast tier; state precision + GPU) |
| EUI error | per building, % vs reference E+ (median, p95, max) |
| End-use error | heating / cooling / fans / DHW separately |
| Hourly | CV(RMSE), NMBE vs reference E+ (ASHRAE G14 thresholds as guidance) |
| Peak | peak heating/cooling load error |
| Effective method | shading method actually used (from `eplusout.eio`), E+ binary architecture (x86_64/arm64) |

All results go into `RESULTS_phaseN_*.md` in this folder, with the exact config flags and git commit used.

---

## 7. Proposed File Layout (new, nothing existing modified until approved)

```
docs/docs_ACTIVE/GPU_based_compute/
  PLAN_gpu_accelerated_simulation.md      ← this file
  Prompt/deepResearch/                     ← DR01–DR06 prompts + README
  Prompt/deepResearch/results/             ← DR01–DR06 results (done)
  RESULTS_phase0_baseline.md               ← Phase 0 output
scripts/bench/
  gpu_bench_set.json
  profile_energyplus.py                    ← features + ablation variants B0–B5
  bench_makespan.py
openubem/simulation/parallel.py           ← Phase 1A (flag-gated LPT)
openubem/simulation/cost_model.py         ← Phase 0.6 runtime predictor (new)
openubem/idf/…                            ← Phase 1C/2 ShadowCalculation / PerformancePrecisionTradeoffs writer (flag-gated)
openubem/fast/                             ← Phase 3 GPU ROM tier (new, optional)
tests/test_sim_schedule.py, tests/test_shadowcalc_flag.py, tests/test_fast_rom_*.py
```

---

## 8. Research Workstreams (deep-research prompts)

| ID | Prompt | Result | Feeds |
|---|---|---|---|
| DR01 | [GPU + EnergyPlus / BEM landscape](Prompt/deepResearch/DR01_gpu_bem_landscape.md) | [result](Prompt/deepResearch/results/DR01_result.md) | whole plan, NG1 |
| DR02 | [E+ runtime anatomy, PixelCounting, speed settings](Prompt/deepResearch/DR02_energyplus_runtime_and_pixelcounting.md) | [result](Prompt/deepResearch/results/DR02_result.md) | Phases 0, 1C, 2 |
| DR03 | [GPU-batched reduced-order physics](Prompt/deepResearch/DR03_gpu_batched_reduced_order_physics.md) | [result](Prompt/deepResearch/results/DR03_result.md) | Phase 3 |
| DR04 | [ML surrogates / emulators](Prompt/deepResearch/DR04_ml_surrogates_emulators.md) | [result](Prompt/deepResearch/results/DR04_result.md) | Phase 4 |
| DR05 | [Scale-out & tail-latency reduction](Prompt/deepResearch/DR05_hpc_cloud_scaleout_and_tail.md) | [result](Prompt/deepResearch/results/DR05_result.md) | Phase 1 |
| DR06 | [GPU microclimate & solar geometry](Prompt/deepResearch/DR06_gpu_microclimate_raytracing.md) | [result](Prompt/deepResearch/results/DR06_result.md) | Phase 5, candidate M |

---

## 9. Open Decisions (owner)

1. ~~**Target GPU hardware.**~~ **Decided 2026-11-22:** develop on the M2 Pro; GPU work on the **Windows NVIDIA CUDA workstation**. Still open: **GPU model and VRAM** (sets the Phase 3 batch size; consumer RTX cards run FP64 at 1/64 speed, which is why the rollout is float32).
2. **Acceptance thresholds** for "E+-equivalent" changes (§3.2) and for the fast tier (Phase 3 budget proposed above).
3. **Scope of the fast tier.** Screening and scenarios only, or also allowed in published district totals (with labels)? This interacts with the README's "Pure Physics, Zero Fitted Multipliers" claim. DR04 recommends screening only, with E+ verification of final picks.
4. **EnergyPlus version.** Evidence now exists: 24.2 arm64 is 11–23% faster on the M2 Pro, and the ShadowCalculation fields are unchanged. One breaking IDD rename matters only for the `Scheduled` route (`SurfaceProperty:LocalEnvironment` A3). This is only a Mac-side gain; Windows x86 builds are native either way. Options: stay on 23.1, or run a migration study.
5. **Zone aggregation (1D).** Acceptable as an opt-in mode for high-rise tail buildings?
6. **Phase 3 framework:** JAX on WSL2 (best fit per DR03) or PyTorch native on Windows (no WSL2, but a weaker 8,760-step loop story)?

---

## 10. Next Actions

1. ~~Owner runs DR01–DR06.~~ Done; reviewed in §11.
2. Implement **Phase 0** (benchmark set, profiler, ablation B0–B5, Rosetta check) and **Phase 1A** (LPT, flag-gated). Neither depends on any §9 decision.
3. Owner records the Windows GPU model/VRAM and answers §9.4 and §9.6.
4. **Implementation track (2026-11-22):** the owner chose to *build* GPU-based E+-equivalent computation. See `BUILD_SPEC_gpu_heat_balance_engine.md`: a GPU-native re-implementation of a subset of E+ 23.1, batched across buildings, macOS first, then Windows. It recommends PyTorch for §9.6 and records findings F1 (European campaign windows get zero solar) and F2 (internal mass at half capacity). Outside reviews IMP01–IMP03 are in `Prompt/IMP/`; IMP03's advice on D1–D5 is in BUILD_SPEC rev. 3 §8.
4. After Phase 0: decide 1C/1D/1E/Phase 2 from the measured shading and HVAC shares. Start the Phase 3.1 CPU prototype in parallel.

---

## 11. Deep-Research Review (2026-11-22)

### 11.1 What changed in the plan
- NG1 confirmed. Candidates I (`pyenergyplus`, ~2.5%) and the E+ GPU port were dropped.
- New levers: `PerformancePrecisionTradeoffs` (1C), context-shading simplification (1E), the Rosetta/version question (§9.4), and the `eio`-based fallback check (2.2).
- `-r` cannot simply be dropped, because the EU campaign code reads `eplusout.csv` (found during review, not in the DRs).
- Phase 3 now has a concrete design (7R2C + ZOH + float32 scan). Phase 4 was re-scoped from "foundation model" to a residual emulator. Phase 5 framework chosen (PyTorch + array-api-compat).

### 11.2 Spot-checks done during review
| Claim | Check | Result |
|---|---|---|
| E+ 23.1 macOS is x86_64; 24.2 is arm64 | `file /Applications/EnergyPlus-*/energyplus` | ✅ confirmed (22.1 is also arm64) |
| `-j` is G-function only | `energyplus --help` (23.1) | ✅ "Currently only for G-Function generation" |
| ShadowCalculation fields/defaults; fallback note | `Energy+.idd` l.575+ (23.1) | ✅ PolygonClipping / Periodic / 20 / 15000 / SutherlandHodgman / 512; IDD states the warning + revert |
| Cited repos exist | GitHub API | ✅ all checked exist. Corrections: `bigladder/penumbra` last push **2026-04-02** (not 2025-11-07); `pyBuildingEnergy` licence **BSD-3-Clause** (not MIT); `jax_ec_ai_lab` **1 star** (not 12); `NREL/*` repos now redirect to **`NatLabRockies/*`**; SOLWEIG-GPU/SOLWEIG-CUDA/UMEP solweig **GPL-3.0**, UrbanSolarCarver **AGPL-3.0** |
| DR02 local timings (4.86×, Rosetta factor, ReadVarsESO 2.43 s) | test artifacts not found on disk | ⚠️ not reproduced; Phase 0.3/0.5 re-measures them on real tail buildings |
| DR04 "tens of thousands of historical E+ runs" | — | ⚠️ unverified; count before Phase 4 |
| DR03 10³–10⁴× ROM speedup | — | ⚠️ theoretical; DR03 itself flags it `UNVERIFIED` |
