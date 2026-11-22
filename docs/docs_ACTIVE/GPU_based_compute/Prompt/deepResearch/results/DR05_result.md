# DR05 — Scale-Out (HPC / Cloud) and Tail-Latency Reduction for Large EnergyPlus Fleets

**Target system:** OpenUBEM (EnergyPlus 23.1, Python `subprocess` + `joblib.Parallel(backend="loky")`, SLURM-aware via `SLURM_CPUS_PER_TASK`)  
**Baseline workload (from prompt context, Apple M2 Pro, 12 cores, EnergyPlus 23.1):**
- Per-building runtime distribution: median **3.2 s**, p90 **9.8 s**, p99 **233 s**, max **907 s**.
- Tail-heavy district (`341` buildings): **9,940 CPU-s** total (mean **29.15 CPU-s/building**), top 10 buildings consume **40%** of total CPU time (**3,976 CPU-s**), and the single slowest run (**907 s**) exceeds the ideal 12-core balanced average (`9,940 / 12 = 828.3 s`), bounding minimum 12-core makespan at **907 s**.

---

## Executive Summary

Scaling OpenUBEM from single-district desktop runs to $10^4\text{–}10^6$ building campaigns faces two distinct bottlenecks: (1) **intra-node tail latency** caused by multi-zone high-rise models with dense context shading (where manifest-order dispatch can let the 907 s building start late and stretch a 12-core run from ~907 s toward ~1,735 s), and (2) **per-run process, I/O, and cluster-scheduling overheads** that penalize 3.2 s median runs when scaled naively to SLURM, HTCondor, or NFS.

No peer-reviewed published EnergyPlus runtime predictor with benchmarked regression coefficients ($R^2$/MAE) was found in the literature (`UNVERIFIED`), nor do NREL/vendors publish exact dollar bills per $10^6$ EnergyPlus runs (`UNVERIFIED`). However, combining NREL `buildstockbatch` cloud/HPC patterns, LPT scheduling, local-scratch I/O (`tmpfs`), and targeted tail-building simplification (typical-floor multipliers + context-shading pruning) delivers the bulk of achievable speedups with modest engineering effort.

### Ranked Actions (by Speedup per Engineering Hour)

| Rank | Action | Expected Gain | Effort | Risk |
|---|---|---|---|---|
| **1** | **LPT task ordering in `joblib` (`batch_size=1`, `pre_dispatch="2*n_jobs"`)** driven by a simple geometric cost heuristic / Phase-0 log-runtime fit | Up to **~1.5–1.9×** makespan reduction on tail-heavy districts (approaching the `max(T_sum/P, T_max)` lower bound; e.g., 907 s on 12 cores) | **Low** (hours; ~20 lines Python) | **None** on physics or outputs (exact same EnergyPlus runs) |
| **2** | **Stage working dirs in local scratch / `/dev/shm` (`tmpfs`) and eliminate unnecessary `-x` (`ExpandObjects`) / `-r` (`ReadVarsESO`)** | Eliminates NFS SQLite lock stalls & orders-of-magnitude random-write penalty; saves process-spawn/text-parse overhead on 3 s runs | **Low** (hours–1 day) | **Low** (must copy retained files before `/dev/shm` cleanup and keep Stage-5 CSV/SQL fallback contract) |
| **3** | **Pin concurrency to physical cores (1 E+ process per physical core, no SMT oversubscription)** + memory-aware worker caps | Avoids cache thrashing and floating-point/memory-bandwidth contention across EnergyPlus processes | **Low** (config/SLURM flag) | **None** |
| **4** | **Context-shading simplification on tail buildings** (radius culling $\le 50\text{–}100\text{ m}$, coplanar/convex block merging, `ShadowCalculation` periodic frequency tuning, optional `PixelCounting` where GPU/OpenGL exists) | **2×** (`PixelCounting`, E+ IBPSA 2017) to **3–10×+** (context radius/geometry pruning on shading-heavy models) | **Low–Medium** (1–3 days) | **Low–Medium** (must pass EUI/peak error gate; headless `PixelCounting` requires GPU/EGL or Mesa software fallback) |
| **5** | **SLURM job-array chunking with LPT round-robin bin packing** ($K$ buildings per array task + `--array=...%M` throttle) | Near-linear scaling across cluster nodes while amortizing multi-second SLURM/HTCondor dispatch overhead | **Medium** (2–4 days) | **Low** (requires per-task retry/manifest resume for failed or preempted chunks) |
| **6** | **Typical-floor / zone-multiplier aggregation for tall multi-zone tail buildings** (e.g., $>N$ zones: ground + mid-height typical floor × multiplier + top floor) | **2–3×**+ per tall building (Chen & Hong 2018); higher on 340-zone towers (`UNVERIFIED` exact factor for 340→~15 zones) | **Medium–High** (3–7 days) | **Medium** (up to **2.6%** source-energy error in Chen & Hong 2018; larger errors on peak sizing/stack effect if altitude bands are ignored) |
| **7** | **Cloud Spot scale-out (AWS Batch / GCP Batch)** with small task batches ($\le 100$ sims/task) and `--missingonly` resume | **60–70% cost discount** vs On-Demand (~**\$97–\$146** raw Spot compute per $10^6$ OpenUBEM-median runs, extrapolated) | **Medium–High** (3–7 days) | **Medium** (Spot preemption requires idempotent chunking & retry logic) |

---

## Q1. How Large Campaigns Do It

Large-scale building energy simulation campaigns fall into two architectural families: (a) **batch-containerized physics campaigns** that run full OpenStudio/EnergyPlus per building/sample on HPC or Cloud Batch (`buildstockbatch`, URBANopt, CityBES, SimStock, UBEM.io, Autodesk Insight/Forma), and (b) **reduced-order urban engines** that bypass EnergyPlus entirely in favor of single-zone RC networks (`City Energy Analyst`).

### Architectural Patterns Across Major Platforms

1. **NREL ResStock / ComStock (`NatLabRockies/buildstockbatch`)**
   - **Infrastructure & Containers:** Orchestrates national-scale ResStock (~350,000–550,000 baseline dwelling models; scaling to >2.2 million runs across upgrade packages) and ComStock (~150,000–350,000 commercial models) using OpenStudio + EnergyPlus inside Docker containers (`nrel/openstudio`, `nrel/energyplus` compressed image ~93–102 MB; legacy 8.9.0 ~74 MB) locally or on AWS/GCP Batch, and Singularity containers / shared environments on NREL HPC systems (legacy **Eagle**: HPE SGI 8600, dual Intel Xeon Gold 6154, 36 physical cores/node; current **Kestrel**: dual Intel Xeon Sapphire Rapids, 104 physical cores/node, 256 GB DDR5/node) [1, 2, 3, 4, 5, 6].
   - **Job Granularity:** Rather than submitting 1 SLURM/Batch job per building, `buildstockbatch` splits the sample into `n_jobs` array jobs on HPC (each job runs a batch of simulations on one node) or `batch_array_size` tasks on cloud Batch (AWS/GCP Batch cap: max **10,000** array elements). For Spot VMs, docs explicitly recommend **<100 simulations per array task** to bound lost work upon preemption [7, 8].
   - **Storage & Post-processing:** Raw simulation outputs are not kept long-term as millions of SQLite/ESO files. `buildstockbatch` uses distributed **Dask** workers (historically multi-node, memory-bounded via `MAX_PARQUET_MEMORY`) and Polars/Pandas to aggregate time-series and annual tables into **Apache Parquet** files stored on Amazon S3 / OEDI and queried via AWS Athena [1, 9, 10].
   - **Failure Handling:** Failed simulations are isolated to individual building directories rather than crashing the batch. Recoveries use `--rerun_failed` (HPC) or `--missingonly` (cloud/Spot) to re-execute only missing/failed simulation batches before re-running `--postprocessonly` [7, 11].

2. **NREL URBANopt (`urbanopt/urbanopt-cli`)**
   - **Architecture:** Modular Ruby/CLI SDK wrapping OpenStudio and EnergyPlus for district energy systems and DERs (with REopt integration). Local/single-VM parallelism uses `num_parallel` in `runner.conf` or `--num-parallel` (1 OpenStudio/E+ process per core) [12, 13]. Multi-node cloud scale-out integrates with **OpenStudio-Server** deployed via Kubernetes Helm charts (`nrel/docker-urbanopt`) [13, 14].

3. **LBNL CityBES (`citybes.lbl.gov`)**
   - **Architecture:** Web platform translating CityGML / municipal GIS datasets into EnergyPlus/OpenStudio IDF models and executing them via an internal parallel simulation manager across multi-core servers/clusters (reported testbeds using 62–72 cores simultaneously) [15, 16]. In the canonical San Francisco case study (Chen, Hong, & Piette, *Applied Energy* 2017), CityBES modeled **940** office/retail buildings across six downtown/northeast districts with 5 ECMs [15].

4. **City Energy Analyst — CEA (`architecture-building-systems/CityEnergyAnalyst`)**
   - **Important distinction:** Unlike CityBES or OpenUBEM, **CEA does NOT run EnergyPlus** for building thermal simulation. Introduced by Fonseca et al. (2016), CEA uses an **hourly single-zone Resistance-Capacitance (RC) network** (adapted from SIA 2044 / ISO standards) coupled to its own radiation/shading engine, enabling rapid neighborhood/district simulation and energy-system optimization [17, 18].

5. **UCL SimStock (`UCL/simstock`)**
   - **Architecture:** Open-source Python package and QGIS plugin (`simstock_qgis`) developed at UCL Energy Institute to translate 3DStock/GIS spatial data into **EnergyPlus 8.9** IDFs (via `eppy`), execute batches in parallel on local multi-core machines or institutional HPC clusters, and post-process outputs in Python for London/UK building stocks [19, 20].

6. **MIT `UBEM.io` (Ang et al., 2022)**
   - **Architecture:** Web-based platform automating GIS-to-UBEM generation and carbon-pathway simulation (EnergyPlus backend for hourly building physics, paired with specialized fast modules like GPU-parallelized **Centroid Neighbor Shading** for solar/PV masks) [21, 22].

7. **Commercial Cloud Services (Autodesk Insight / Forma; Ladybug Tools Pollination)**
   - **Autodesk Insight / Forma:** Proprietary SaaS integrated with Revit/Forma; pushes Energy Analytical Models to Autodesk-managed cloud servers running EnergyPlus and DOE-2.2, billed via **Autodesk Flex tokens** / AEC Collection entitlements (`UNVERIFIED` per-simulation dollar cost) [23, 24].
   - **Pollination (Ladybug Tools):** Commercial Rhino/Revit plugins (starting ~\$125/month concurrent Rhino license) with cloud recipe execution (`UNVERIFIED` per-10⁶-run cloud cost) [25].

### Table: Large-Campaign Systems

*GitHub metadata (stars, license, language, activity) retrieved from indexed repository snapshots during search; exact live star counts fluctuate and commit timestamps not printed in search snippets are marked `UNVERIFIED`.*

| Name | URL | Infrastructure & Job Granularity | Scale Achieved | Cost Data | Open Source (Y/N) |
|---|---|---|---|---|---|
| **buildstockbatch** (ResStock / ComStock) | [github.com/NatLabRockies/buildstockbatch](https://github.com/NatLabRockies/buildstockbatch) / [docs](https://buildstockbatch.readthedocs.io/) | Python + Docker (`nrel/openstudio`) / Singularity; AWS Batch / GCP Batch (`batch_array_size <= 10,000`, <100 sims/task recommended for Spot) & SLURM on Eagle/Kestrel (`n_jobs` array jobs); Dask → Parquet on S3 | **350k–550k** baseline models; **millions** of sims (e.g., >2.2M ResStock scenarios; 150k–350k ComStock) [1, 2, 3, 7] | Open-source tool (\$0 license); Spot EC2 gives **60–70% savings** over On-Demand [11]. Exact NREL total dollar cost per $10^6$ sims: `UNVERIFIED` | **Y** (BSD-style / BSD-3-Clause; Python ~98.8%; ~26 stars; active 2024–2026) [26, 27] |
| **URBANopt** (`urbanopt-cli`) | [docs.urbanopt.net](https://docs.urbanopt.net/) / [github.com/urbanopt/urbanopt-cli](https://github.com/urbanopt/urbanopt-cli) | Ruby/CLI SDK + OpenStudio/E+; `num_parallel` local multi-core; Docker (`nrel/docker-urbanopt`); Kubernetes via OpenStudio-Server for cloud scale | District / campus / neighborhood scale (tens to thousands of buildings + DER/REopt) [12, 13] | Open-source (\$0 license); cloud cost `UNVERIFIED` | **Y** (BSD-3-Clause; ~12 stars on `urbanopt-cli`; actively maintained) [28, 29] |
| **CityBES** | [citybes.lbl.gov](https://citybes.lbl.gov/) | LBNL web platform; CityGML → OpenStudio/E+; parallel simulation manager across multi-core clusters (62–72 cores reported) [15, 16] | **940** San Francisco commercial buildings (Chen et al. 2017) up to city-scale stocks [15] | Institutional/research web tool; compute cost `UNVERIFIED` | **N** (public web tool, not open-source GitHub repo) [15, 30] |
| **City Energy Analyst (CEA)** | [cityenergyanalyst.com](https://www.cityenergyanalyst.com/) / [github.com/architecture-building-systems/CityEnergyAnalyst](https://github.com/architecture-building-systems/CityEnergyAnalyst) | Python desktop/CLI framework; **single-zone RC model (NOT EnergyPlus)** + built-in radiation engine | Neighborhood & city districts (thousands of buildings rapidly due to RC model) [17, 18] | Open-source (\$0 license) | **Y** (MIT License; Python; ~287 stars, 19,227+ commits; active) [31] |
| **SimStock** | [github.com/UCL/simstock](https://github.com/UCL/simstock) | Python + QGIS plugin (`simstock_qgis`); 3DStock/GIS → **EnergyPlus 8.9** IDFs via `eppy`; local multi-core or HPC batch [19, 20] | London boroughs / urban neighborhoods [19] | Open-source (\$0 license); HPC cost `UNVERIFIED` | **Y** (MIT License; Python 3.11–3.13; ~15 stars; last commit date `UNVERIFIED`) [19, 32] |
| **UBEM.io** | [ubem.io](https://ubem.io/) | Web platform (MIT Sustainable Design Lab); GIS/shapefile → EnergyPlus + fast GPU-parallelized CNS shading module [21, 22] | City-scale municipal pathways (e.g., 20,000 rooftop PV/CNS masks in <5 min) [22] | Web service; per-simulation cloud cost `UNVERIFIED` | **N** (web platform; public source repo `UNVERIFIED`) [21] |
| **Autodesk Insight / Forma** | [autodesk.com](https://www.autodesk.com/) | Proprietary Revit/Forma SaaS pushing EAMs to Autodesk cloud (EnergyPlus + DOE-2.2) [23, 24] | Single building / portfolio design workflows | Commercial subscription + Autodesk Flex tokens (`UNVERIFIED` \$/sim) [24] | **N** (Proprietary) |

**Cost per $10^6$ Simulations (Transparent Estimate for OpenUBEM):**  
Because neither NREL nor commercial cloud BEM platforms publish a verified audited dollar figure per $10^6$ EnergyPlus runs (`UNVERIFIED`), we bound OpenUBEM's raw compute cost directly from AWS EC2 Spot pricing and OpenUBEM's measured CPU time:
- OpenUBEM `austin_centre` average: $9,940\text{ CPU-s} / 341\text{ buildings} = 29.15\text{ CPU-s/building}$ (EnergyPlus 23.1, Apple M2 Pro).
- At $29.15\text{ CPU-s/building}$, $10^6$ simulations require $\approx 2.915 \times 10^7\text{ CPU-s} \approx \mathbf{8,097\text{ CPU-hours}}$ (note: x86/Graviton vCPU speed vs Apple M2 Pro core speed differs; exact cloud CPU-s/building is `UNVERIFIED` without a cloud benchmark).
- Applying observed 2025/2026 AWS EC2 Spot prices of **\$0.012–\$0.019 / vCPU-hr** (`c6i.xlarge`), **\$0.015–\$0.018 / vCPU-hr** (`c7i.xlarge`), and **\$0.010–\$0.020 / vCPU-hr** (`c7g.xlarge` Graviton3) [33, 34, 35, 36]:
  $$\text{Compute cost per } 10^6\text{ runs} \approx 8,097\text{ vCPU-hrs} \times \$0.012\text{–}\$0.018/\text{hr} \approx \mathbf{\$97\text{–}\$146\text{ USD}}$$
  *(Spot raw EC2 compute only; excludes S3/EBS, post-processing, Spot preemption retries, and slower-per-core x86/ARM variance. On-Demand pricing at ~3× Spot would be **\$290–\$440** per $10^6$ runs.)*

---

## Q2. Scheduling and the Tail

### 1. Longest-Processing-Time-First (LPT) Scheduling & Makespan Math
For $m$ identical parallel workers and jobs with durations $t_1 \ge t_2 \ge \dots \ge t_n$, greedy **LPT scheduling** (sorting descending by runtime and assigning each next job to the earliest-free worker) guarantees a worst-case makespan within $\left(\frac{4}{3} - \frac{1}{3m}\right)$ of optimal [37], and in practice hits near-optimal whenever one or a few jobs dominate.

On OpenUBEM's `austin_centre` district ($m=12$ cores, $\sum t_i = 9,940\text{ s}$, $t_{\max} = 907\text{ s}$):
- **Theoretical lower bound:** $\max\left(\frac{9940}{12}, 907\right) = \max(828.3\text{ s}, 907\text{ s}) = \mathbf{907\text{ s}}$.
- **Manifest-order risk:** If the 907 s building (or the top-10 tail totaling 3,976 s) appears late in manifest order, 11 cores finish the small 3.2 s–9.8 s jobs and sit idle while 1 core executes the late 907 s job—pushing makespan toward **~1,735 s** (nearly **1.9×** the 907 s lower bound).
- **LPT outcome:** Dispatching the 907 s job at $t=0$ ensures it overlaps completely with the remaining 9,033 CPU-s distributed across the other 11 cores ($9,033 / 11 = 821.2\text{ s} < 907\text{ s}$), driving makespan down to the **907 s hardware floor**.

### 2. Published EnergyPlus Runtime Predictors
A targeted search of IBPSA, ScienceDirect, and DOE/NREL literature found **no peer-reviewed published regression/ML runtime predictor with validated $R^2$ or MAE coefficients specifically for EnergyPlus execution time** (`UNVERIFIED`). Literature discusses the physical scaling drivers qualitatively—specifically `num_zones`, `num_surfaces`, `num_subsurfaces`, `num_shading_surfaces`, `timestep_per_hour`, `run_period_days`, `hvac_system_type` (IdealLoads vs VAV/plant loops), `solar_distribution`, and `AirflowNetwork` [38, 39]—and notes that right-skewed runtimes (seconds to hours) should be modeled on $\log(\text{runtime})$ using tree ensembles (LightGBM/XGBoost/Random Forest) or regularized linear models [39].

**Practical OpenUBEM proxy before Phase-0 fitting:** Because interior radiant heat exchange scales as $\mathcal{O}(n_{\text{surfaces}}^2)$ per zone [40] and polygon-clipping shading scales super-linearly with exterior + shading surfaces [41], a zero-training heuristic score such as:
$$\text{cost\_proxy} = n_{\text{zones}} \cdot (n_{\text{surfaces}} + n_{\text{shading\_surfaces}})$$
is sufficient to place 340-zone / dense-shading buildings at the front of the queue immediately, then be replaced by a Ridge/LightGBM predictor trained on $\log(\text{wall\_clock\_s})$ from OpenUBEM's 2,048 validation runs.

### 3. `joblib` / `loky` Internals and Task Dispatch Guarantees
How `joblib.Parallel(backend="loky")` behaves on mixed 3 s – 907 s tasks [42, 43]:
- **Submission order:** `joblib` consumes the input generator/list strictly in sequence and preserves submission order in the returned list (`return_as="list"`).
- **`batch_size` trap (`"auto"` vs `1`):** The default `batch_size="auto"` dynamically increases chunk size to target ~0.5 s per batch [42]. While benign for 3 s tasks once warmed up, any auto-batching $>1$ risks bundling multiple tasks onto one worker ahead of idle workers. Explicitly setting **`batch_size=1`** forces 1-building-per-IPC-call, enabling true dynamic work-stealing as workers finish.
- **`pre_dispatch`:** Default is `'2 * n_jobs'`. With an LPT-sorted list and `batch_size=1`, `pre_dispatch='2 * n_jobs'` (or `'n_jobs'`) keeps all workers saturated in descending order without materializing $10^5$ delayed objects in RAM [42, 43].
- **Streaming completion (`return_as="generator_unordered"`):** Available in modern `joblib` (≥1.3), allowing OpenUBEM to log manifest completion and purge/compact outputs as soon as each building finishes rather than blocking behind the 907 s tail in memory [42].

### 4. Orchestrator Overheads: 3-Second vs 15-Minute Tasks

| Framework / Scheduler | Per-Task Dispatch Overhead | Fit for 3.2 s Tasks | Fit for 15 min (900 s) Tasks | Notes & Sources |
|---|---|---|---|---|
| **`concurrent.futures.ProcessPoolExecutor`** | **1–10 ms** (warm pool); **50–200+ ms** (cold spawn) [44] | Excellent (<0.3% overhead) | Excellent (<0.01% overhead) | Standard library; less robust against segfault/broken-worker cleanup than `loky`. |
| **`joblib` (`loky`)** | **10–50+ ms** (warm); **100–500+ ms** (cold) [44] | Excellent (~0.3–1.5% overhead at `batch_size=1`) | Excellent (<0.01% overhead) | Current OpenUBEM choice; handles worker recycling and crashes cleanly. |
| **`Dask` (`dask.distributed`)** | **~1 ms** per Future/task [45] | Good (neg. scaling only <100 ms [45]) | Excellent | Best suited for multi-node post-processing (as in `buildstockbatch`). |
| **`Ray`** | **1–10 ms** per task [46] | Good (overhead felt <10 ms [46]) | Excellent | Strong multi-node dynamic scheduling / custom priority actors. |
| **GNU Parallel** | **2–10 ms** per job [47] | Good (~0.1–0.3% overhead) | Excellent | Shell/CLI native; zero Python serialization overhead. |
| **SLURM Job Arrays** | **Seconds** (`batch_sched_delay` default 3 s; controller/DB thrashing at high rate) [48] | **Poor 1:1** (100%+ overhead; thrashing `slurmctld`) | Marginal–Good | **Must bundle $K$ buildings per array task** (e.g., 5–30 min/task) and run `joblib`/`GNU Parallel` inside each allocation. |
| **HTCondor** | **Seconds–Minutes** (negotiator cycles + sandbox staging) [49] | **Unusable 1:1** | Marginal | Requires bundled tasks running tens of minutes to hours. |

---

## Q3. Tail-Reduction Techniques (Fidelity vs Speedup)

Because OpenUBEM's tail buildings are tall, many-zone (~340 dwelling zones) models with 20 m context shading, four classes of physics-preserving reductions apply.

### Table: Tail-Reduction Techniques

| Technique | Measured / Reported Speedup | Accuracy Impact (EUI & Peak Loads) | Hardware / E+ Version | Source |
|---|---|---|---|---|
| **Typical-floor modelling + Zone/Floor Multipliers** (model ground + mid-height typical floor × $M$ + top floor) | **2–3×** faster than explicit every-floor modeling (Chen & Hong 2018); potentially larger on 340-zone towers (`UNVERIFIED` exact factor for 340→~15 zones) | Source energy / EUI up to **+2.6%** higher than explicit floors (Chen & Hong 2018). **Caveat:** ignores altitude wind/temperature lapse & stack effect; naive ground/top-floor multipliers can skew tall-building end-uses by **10–40%** and mis-size peak loads [50, 51]. | CityBES / EnergyPlus (v8.x era, LBNL) [50] | Chen & Hong (2018), *Applied Energy* 215:717–735 [50]; Tall-building E+ studies [51] |
| **Zone Merging / Thermal Zoning Simplification** (`OneZone` vs `AutoZone` core-perimeter; `Shoeboxer`; RC graph clustering) | Reduces matrix/surface count sharply (`AutoZone` / `OneZone` / `Shoeboxer` cut urban modeling times from hours to minutes [50, 52]) | `OneZone` vs `AutoZone`: **-7.6% to +5.1%** source energy, **-7.5%** cooling load, **-16.9%** heating load (Chen & Hong 2018). DOE `Prototype` vs `AutoZone`: **-12.1% to +19.0%** source energy. `Shoeboxer`: **5–10% RMSE** on annual EUI [52]. Masks intra-building overheating on upper floors [53]. | EnergyPlus (`AutoZone` / `umi` `Shoeboxer`) | Chen & Hong (2018) [50]; Dogan & Reinhart (2017) *Energy & Buildings* [52] |
| **Context-Shading Distance Cutoff & Geometry Merging** (radius $\le 50\text{–}100\text{ m}$, merging coplanar walls into $\le 4$-vertex convex blocks) | **3–10×+** speedup on dense urban blocks (shifts neighbor search from $\mathcal{O}(n^2)$ to $\mathcal{O}(n)$; 100 m is typical sweet spot) [54] | 50 m captures street canyons but can under-shade low floors from tall distant blocks; 100 m preserves annual EUI trends (`UNVERIFIED` exact % error across all climates) [54]. Simplifying non-convex meshes prevents clipping errors [41]. | EnergyPlus UBEM workflows | UBEM shading radius literature [54]; Big Ladder E+ docs [41] |
| **`ShadowCalculation` Periodic Update Frequency** (keep/tune `Periodic`, e.g. 20 days default vs daily) | Significant speedup vs per-timestep/daily shadow updates (`UNVERIFIED` % specifically for 23.1 on `austin_centre`) | Minimal EUI drift for annual runs (20 days is EnergyPlus 23.1 default representing solar declination step) [55] | EnergyPlus 23.1 (`PolygonClipping` / `SutherlandHodgman` default) [55] | Big Ladder Software E+ 23.1 I/O Ref [55] |
| **GPU `PixelCounting` Shading** (`ShadowCalculation = PixelCounting` via OpenGL/Penumbra) | Average **2×** faster than PolygonClipping on complex urban shading (Hoover & Dogan 2017) [56] | **0.01** validated accuracy threshold vs analytical baseline; eliminates non-convex clipping failures [56, 57]. Requires GPU/OpenGL (Apple Metal/OpenGL on M2 Pro, NVIDIA EGL on Linux; Mesa `llvmpipe` CPU fallback gives no speedup) [57]. | EnergyPlus (prototype/v8.x–23.1+, OpenGL) | Hoover & Dogan (2017), *IBPSA*, DOI: `10.26868/25222708.2017.287` [56] |
| **External Shading Masks / Centroid Neighbor Shading (CNS)** | **>1,000–1,350×** for rooftop solar masks (20,000 buildings in <5 min on GPU) [22] | **~9.5% MAPE** on rooftop solar/PV potential; note CNS models a single rooftop centroid mask and **does not replace full multi-zone facade shading inside EnergyPlus** [22]. | Custom GPU pipeline (`UBEM.io`) | IBPSA *Building Simulation* CNS paper [22] |

**Engineering guidance for OpenUBEM's tall buildings:**  
For 340-zone dwelling towers, **banded typical-floor multipliers** (explicit ground floor + 2–3 altitude-banded typical floors with `Zone:Multiplier` + explicit top/roof floor, using mid-height shading/wind proxies) avoid the 10–40% naive single-floor error [51] while collapsing ~340 zones down to ~15–30 zones. Combined with merging OpenUBEM's 20 m context buildings into simple 4-vertex convex `Shading:Site:Detailed` boxes, this targets the dominant $\mathcal{O}(n^2)$ surface radiant and polygon-clipping bottlenecks directly.

---

## Q4. Per-Run Overhead & I/O Bottlenecks

OpenUBEM currently invokes `energyplus -w EPW -d DIR -x -r IDF` via `subprocess` and retains SQLite plus a few output files. Every stage has distinct overhead:

1. **Process Spawn & Python IPC:** `loky` warm dispatch takes ~10–50+ ms [44]; OS `exec` of `energyplus` adds minimal overhead compared to a 3.2 s median run, so **re-architecting around in-process `pyenergyplus` callbacks is low-ROI** (especially since EnergyPlus global C++ state is not thread-safe and process isolation protects against segfaults/memory leaks in $10^4\text{–}10^6$ runs).
2. **`ExpandObjects` (`-x` flag):** Spawns an external preprocessor executable before EnergyPlus, re-parsing the IDF and writing an `.expidf` file if `HVACTemplate:*` or ground-heat-transfer preprocessor objects exist [58]. **If OpenUBEM templates do not emit `HVACTemplate:*` or slab/basement preprocessor objects, dropping `-x` eliminates an entire external process launch and full IDF rewrite per building.**
3. **IDF vs `epJSON` Parsing:** EnergyPlus's native C++ line tokenizer reads **IDF** slightly faster and with smaller file sizes on disk than verbose **`epJSON`** (though `epJSON` is much faster/cleaner for Python-side parsing and schema validation) [59]. Keep `.idf` for engine invocation.
4. **Sizing Runs (`SimulationControl`):** EnergyPlus executes `Sizing:Zone`, `Sizing:System`, and `Sizing:Plant` design-day passes prior to the weather RunPeriod [60]. In complex multi-zone HVAC/plant models, iterative sizing convergence can consume a substantial fraction of total wall time [61]. Ensure IDFs include only necessary `SizingPeriod:DesignDay` objects (and disable `Run Simulation for Sizing Periods` if only annual RunPeriod outputs are needed and systems are pre-sized).
5. **`ReadVarsESO` (`-r` flag) vs Native CSV / SQLite:**
   - Legacy `ReadVarsESO` (`-r`) spawns an external post-processor to scan large text/binary `eplusout.eso` and `eplusout.mtr` files into CSV [62].
   - Since EnergyPlus 9.4.0, `OutputControl:Files` allows native CSV emission (skipping `ReadVarsESO`) [62], or if OpenUBEM's downstream pipeline reads SQLite (`Output:SQLite`) reliably, `-r` should be invoked **only on fallback** when SQLite parsing fails.
   - Note that enabling `Output:SQLite` adds modest in-simulation transaction overhead vs raw `.eso` [63], so **strictly limit requested `Output:Variable` / `Output:Meter` keys** (e.g., hourly/RunPeriod meters via `trim_hourly`) rather than timestep-level zone/surface variables across 340 zones.
6. **Disk I/O — SQLite on NFS vs Local Scratch / `tmpfs` (`/dev/shm`):**
   - **Never write EnergyPlus `eplusout.sql` directly to NFS / Lustre / GPFS.** SQLite performs small random writes with `fsync` and relies on POSIX `fcntl` locking; NFS locking is slow and unreliable over the network, and SQLite WAL mode breaks across hosts—causing orders-of-magnitude slowdowns or `database is locked` failures [64, 65].
   - **HPC Best Practice:** Run each EnergyPlus subprocess in a node-local **`tmpfs` (`/dev/shm/<job>/<bldg_id>`)** or local NVMe **`$SLURM_TMPDIR`**, then copy only the retained SQLite/summary files to shared storage and `rm -rf` the scratch directory immediately after success [65].

---

## Q5. Hardware Economics & Architecture

1. **Cloud Spot Pricing & Cost Sensitivity:**
   - Compute-optimized EC2 Spot instances run **60–70% below On-Demand** [11, 33]: `c7i.xlarge` (Intel Sapphire Rapids) ~**\$0.015–\$0.018/vCPU-hr**, `c6i.xlarge` (Ice Lake) ~**\$0.012–\$0.019/vCPU-hr**, and `c7g.xlarge` (ARM Graviton3) ~**\$0.010–\$0.020/vCPU-hr** [33, 34, 35, 36].
   - At OpenUBEM's ~8,097 CPU-hrs per $10^6$ runs (extrapolated from M2 Pro `austin_centre` mean 29.15 CPU-s), raw Spot compute is **~\$97–\$146 per $10^6$ buildings** (subject to hardware scaling factor between M2 Pro and cloud vCPUs).
2. **ARM (Graviton / Apple Silicon) vs x86:**
   - **Data gap:** No official NREL or peer-reviewed EnergyPlus 23.1 cross-architecture benchmark comparing Graviton3/4, Apple M2 Pro, and Xeon/EPYC was found (`UNVERIFIED` exact speed ratio) [66].
   - **Architectural mechanics:** Native AArch64 compilation is mandatory on ARM (Rosetta 2 x86 emulation on Apple Silicon incurs roughly a **30–50% slowdown**) [67]. AWS Graviton provides **1:1 physical-to-vCPU core mapping** (zero SMT contention) and competitive price-performance (~30–40% better on general AWS workloads), whereas modern x86 Xeon/EPYC processors retain wider **AVX2/AVX-512** SIMD vector units [68, 69].
3. **Hyperthreading (SMT) Effect on EnergyPlus:**
   - Because each EnergyPlus process is a single-threaded floating-point + memory-intensive loop, running $2N$ concurrent EnergyPlus processes on $N$ physical cores with SMT/Hyper-Threading shares ALUs/FPUs and splits per-core **L1/L2 caches**, increasing cache misses and memory-channel contention [70].
   - **Rule:** Always cap concurrent EnergyPlus workers to **physical cores** (`1x` physical core count), never `2x` logical threads. (On SLURM, request `#SBATCH --ntasks-per-node=1 --cpus-per-task=<physical_cores>` or `--hint=nomultithread`).
4. **Memory Footprint per Run:**
   - Small/medium residential or commercial models consume **<1–2 GB RAM** per EnergyPlus process; large multi-zone / sub-hourly models can spike to **4–8+ GB RAM** [71].
   - On high-core-count HPC nodes like NREL **Kestrel** (**104 cores, 256 GB DDR5** → **2.46 GB/core** [4]), running 104 tail models simultaneously would OOM! Memory-aware scheduling (or capping concurrent tail jobs / isolating tail jobs to high-mem nodes) is essential at scale.
5. **Memory-Bandwidth vs Cache-Bound Behaviour:**
   - EnergyPlus is **memory-bandwidth and Last-Level-Cache (LLC) bound** on large multi-zone/multi-surface models. Adams & New (ORNL, SimBuild 2018) profiled EnergyPlus interior radiant heat exchange ($\mathcal{O}(n^2)$ in zone surfaces) with the Empirical Roofline Tool and measured an **arithmetic intensity $\approx 1$**, proving the routine is **memory bound** rather than FLOP bound; switching to cache-aware BLAS/data layouts cut radiant-exchange time by up to **~90%** [40]. Consequently, multi-channel memory bandwidth and large L3 caches matter more than raw clock speed alone when saturating all cores of a node.

---

## Q6. Concrete Recommendations & Scheduling Recipe

### Step-by-Step Implementation Plan for OpenUBEM

1. **Phase 1A — LPT Ordering + `joblib` Tuning (Highest ROI, ~2–4 hours):**
   Sort `fresh` buildings descending by predicted runtime (initially `n_zones * (n_surfaces + n_shading_surfaces)`, later replaced by Phase 0.5 `log(t)` GBM/Ridge predictor). Set `batch_size=1`, `pre_dispatch="2*n_jobs"`, and `return_as="generator_unordered"`.
2. **Phase 1B — `/dev/shm` Staging + Drop Unused `-x` / Conditional `-r` (~0.5–1 day):**
   Verify templates contain no `HVACTemplate:*` objects and remove `-x`; invoke `ReadVarsESO` only if SQLite validation fails; run EnergyPlus inside a per-building directory on `$SLURM_TMPDIR` or `/dev/shm` (falling back to local SSD if RAM < threshold), copying retained outputs atomically to persistent storage.
3. **Phase 1C — Physical-Core Pinning (~1 hour):**
   Ensure `SLURM_CPUS_PER_TASK` / local `N_JOBS` equals physical cores (`os.cpu_count()` on Apple Silicon has no SMT, so 12 = 12 physical cores; on Linux x86 with SMT, divide logical CPUs by threads-per-core or use `--hint=nomultithread`).
4. **Phase 1D — Tail-Building Simplification (~1 week):**
   Add opt-in `TYPICAL_FLOOR_MULTIPLIER` mode for buildings exceeding e.g. 30–50 zones (keeping ground, altitude-banded typical floors, and roof explicit) and merge/simplify 20 m context shading blocks into minimal convex boxes, gated against OpenUBEM's `median |ΔEUI| <= 1%`, `p95 <= 3%` target.
5. **Phase 1E — SLURM Job Array + Cloud Spot Batch (~3–5 days):**
   Pack buildings into array shards using **greedy LPT bin packing** so every array task gets roughly equal CPU-seconds and at least ~10–30 minutes of total work.

---

### Scheduling Recipe

#### 1. Python LPT Recipe with `joblib` (`loky`)

```python
from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from joblib import Parallel, delayed


@dataclass(frozen=True)
class BuildingJob:
    """Metadata required to estimate cost and execute one EnergyPlus run."""

    building_id: str
    idf_path: str
    epw_path: str
    n_zones: int
    n_surfaces: int
    n_shading_surfaces: int
    predicted_s: float | None = None


def estimate_cost(job: BuildingJob) -> float:
    """Return predicted runtime (or monotonic cost proxy) for LPT ordering."""
    if job.predicted_s is not None:
        return job.predicted_s
    # Fallback heuristic reflecting O(surfaces^2) radiant & shading cost
    return float(job.n_zones * max(1, job.n_surfaces + job.n_shading_surfaces))


def run_single_in_scratch(job: BuildingJob, scratch_root: str, out_dir: str) -> str:
    """Execute EnergyPlus in local scratch/tmpfs and copy retained outputs."""
    # Implementation: create scratch_root/job.building_id, run energyplus,
    # copy SQLite + err to out_dir, clean scratch, return status.
    ...
    return job.building_id


def run_lpt_joblib(
    jobs: Iterable[BuildingJob],
    scratch_root: str = "/dev/shm/openubem",
    out_dir: str = "./results",
    n_jobs: int | None = None,
) -> list[str]:
    """Run EnergyPlus jobs in Longest-Processing-Time-first (LPT) order."""
    if n_jobs is None:
        n_jobs = int(os.environ.get("SLURM_CPUS_PER_TASK", -1))

    # 1. Sort strictly descending by estimated runtime BEFORE passing to Parallel
    sorted_jobs = sorted(jobs, key=estimate_cost, reverse=True)

    # 2. batch_size=1 prevents loky from bundling multiple runs into one IPC chunk.
    #    pre_dispatch="2*n_jobs" keeps workers fed strictly from the sorted head.
    #    return_as="generator_unordered" streams completions without tail blocking.
    parallel = Parallel(
        n_jobs=n_jobs,
        backend="loky",
        batch_size=1,
        pre_dispatch="2*n_jobs",
        return_as="generator_unordered",
    )

    completed: list[str] = []
    for bldg_id in parallel(
        delayed(run_single_in_scratch)(job, scratch_root, out_dir)
        for job in sorted_jobs
    ):
        completed.append(bldg_id)
    return completed
```

*Why not Dask/Ray for single-node?* At 3.2 s median runtime, `loky` (`10–50 ms`) adds <1.5% overhead and avoids cluster daemon startup. Switch to SLURM arrays (below) or Ray/AWS Batch only when scaling past one node.

#### 2. SLURM Job-Array Pattern (with LPT Bin Packing & `/dev/shm` Staging)

Never submit 1 SLURM array task per 3 s building (`slurmctld` thrashing). Instead, **pre-shard** a manifest of $N$ buildings into $M$ JSON/Parquet shard files using greedy LPT bin-packing (assign each next-heaviest building to the shard with the smallest cumulative `estimate_cost`, ensuring every shard runs ~10–30 minutes and preventing one shard from getting all tail buildings).

**Step A: LPT Shard Generator (`shard_manifest.py` sketch):**
```python
def lpt_bin_pack(jobs: list[BuildingJob], n_shards: int) -> list[list[BuildingJob]]:
    """Distribute jobs across n_shards via greedy LPT makespan balancing."""
    shards: list[list[BuildingJob]] = [[] for _ in range(n_shards)]
    loads = [0.0] * n_shards
    for job in sorted(jobs, key=estimate_cost, reverse=True):
        # Assign to currently lightest shard (min-heap for large n_shards)
        idx = min(range(n_shards), key=loads.__getitem__)
        shards[idx].append(job)
        loads[idx] += estimate_cost(job)
    return shards
```

**Step B: SLURM Array Script (`submit_openubem.sbatch`):**
```bash
#!/bin/bash
#SBATCH --job-name=openubem_fleet
#SBATCH --output=logs/ubem_%A_%a.out
#SBATCH --error=logs/ubem_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32          # Physical cores only
#SBATCH --hint=nomultithread        # Disable SMT/Hyper-Threading contention
#SBATCH --mem=96G                   # ~3 GB/core headroom for tail buildings
#SBATCH --time=01:00:00
#SBATCH --array=0-99%20             # 100 LPT shards, max 20 nodes concurrently

set -euo pipefail

SHARD_FILE="shards/shard_$(printf '%04d' "${SLURM_ARRAY_TASK_ID}").json"
SCRATCH_DIR="${SLURM_TMPDIR:-/dev/shm}/openubem_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
mkdir -p "${SCRATCH_DIR}"

cleanup() {
    rm -rf "${SCRATCH_DIR}"
}
trap cleanup EXIT

# OpenUBEM reads SLURM_CPUS_PER_TASK (=32) and runs run_lpt_joblib inside this node
python -m openubem.cli run-shard \
    --manifest "${SHARD_FILE}" \
    --scratch-dir "${SCRATCH_DIR}" \
    --output-dir "/shared/nfs/openubem_outputs" \
    --schedule lpt
```

*(Note: If any single tower exceeds node wall-time or per-core RAM, isolate the top-1% extreme tail into a separate SLURM job tier with higher `--mem-per-cpu` and `--time`.)*

---

## References

1. NREL / NatLabRockies, `buildstockbatch` GitHub & Documentation: https://github.com/NatLabRockies/buildstockbatch and https://buildstockbatch.readthedocs.io/
2. Wilson, E. J. H., et al. (2022). *End-Use Load Profiles for the U.S. Building Stock: Methodology and Results of Model Calibration, Validation, and Uncertainty Quantification*. NREL/TP-5500-80889. https://www.nrel.gov/docs/fy22osti/80889.pdf (and OSTI / AWS Open Data Registry).
3. Parker, A., et al. (2023). *ComStock Reference Documentation: Version 1*. NREL/TP-5500-83819.
4. NREL Kestrel HPC System Specifications (104 Sapphire Rapids cores, 256 GB DDR5/node): https://www.nrel.gov/hpc/kestrel-computing-system.html
5. NREL Eagle HPC System Specifications (HPE SGI 8600, dual Intel Xeon Gold 6154, 36 cores/node): TOP500 / Intel Xeon Gold 6154 specs.
6. NREL EnergyPlus Docker Hub (`nrel/energyplus`): https://hub.docker.com/r/nrel/energyplus (and `NREL/EnergyPlus` GitHub: https://github.com/NREL/EnergyPlus).
7. `buildstockbatch` AWS/GCP/HPC Configuration & `batch_array_size` / `n_jobs` Docs: https://buildstockbatch.readthedocs.io/
8. `buildstockbatch` Postprocessing & `--missingonly` / `--rerun_failed` Docs: https://buildstockbatch.readthedocs.io/
9. `buildstockbatch` Parquet / Dask / Athena Output Pipeline: https://github.com/NatLabRockies/buildstockbatch
10. Open Energy Data Initiative (OEDI) End-Use Load Profiles on AWS Open Data: https://registry.opendata.aws/nrel-pds-building-stock/
11. `buildstockbatch` Spot Instance Configuration (`use_spot`, 60–70% savings): https://buildstockbatch.readthedocs.io/
12. NREL URBANopt Documentation (`num_parallel`, `runner.conf`): https://docs.urbanopt.net/
13. URBANopt CLI & Docker (`nrel/docker-urbanopt`, OpenStudio-Server Kubernetes Helm): https://github.com/urbanopt/urbanopt-cli
14. OpenStudio-Server GitHub: https://github.com/NREL/OpenStudio-server
15. Chen, Y., Hong, T., & Piette, M. A. (2017). Automatic generation and simulation of urban building energy models based on city datasets for city-scale building retrofit analysis. *Applied Energy*, 205, 323–335. DOI: `10.1016/j.apenergy.2017.07.128`
16. CityBES (LBNL): https://citybes.lbl.gov/ (and IBPSA / LBNL multi-core parallel manager reports).
17. Fonseca, J. A., Nguyen, T.-A., Schlueter, A., & Marechal, F. (2016). City Energy Analyst (CEA): Integrated framework for analysis and optimization of building energy systems in neighborhoods and city districts. *Energy and Buildings*, 113, 202–226.
18. City Energy Analyst Documentation & Repository: https://www.cityenergyanalyst.com/ and https://github.com/architecture-building-systems/CityEnergyAnalyst
19. UCL SimStock Repository & Docs: https://github.com/UCL/simstock
20. Evans, S., Liddiard, R., Steadman, P., & Symonds, P. — UCL Energy Institute 3DStock / SimStock publications.
21. Ang, Y. Q., Berzolla, Z. M., Letellier-Duchesne, S., Jusiega, V., & Reinhart, C. F. (2022). UBEM.io: A web-based framework to rapidly generate urban building energy models for carbon reduction technology pathways. *Sustainable Cities and Society*, 77, 103534.
22. Centroid Neighbor Shading (CNS) GPU-parallelized shading algorithm in UBEM.io (IBPSA *Building Simulation* proceedings).
23. Autodesk Insight / Forma Carbon Insights: https://www.autodesk.com/
24. Autodesk Flex Token Pricing Overview: https://www.autodesk.com/buying/flex
25. Ladybug Tools Pollination Pricing & Cloud Execution: https://www.pollination.solutions/
26. `NatLabRockies/buildstockbatch` GitHub metadata (Python ~98.8%, ~26 stars, BSD-style license): https://github.com/NatLabRockies/buildstockbatch
27. `NatLabRockies/buildstock-query` (BSD-3-Clause license reference): https://github.com/NatLabRockies/buildstock-query
28. `urbanopt/urbanopt-cli` GitHub metadata (~12 stars, BSD license): https://github.com/urbanopt/urbanopt-cli
29. `urbanopt` BSD-3-Clause licensing: https://github.com/urbanopt
30. LBNL CityBES platform overview (non-open-source web tool).
31. `architecture-building-systems/CityEnergyAnalyst` GitHub metadata (MIT license, ~287 stars, 19,227+ commits): https://github.com/architecture-building-systems/CityEnergyAnalyst
32. `UCL/simstock` GitHub metadata (MIT license, ~15 stars): https://github.com/UCL/simstock
33. AWS EC2 Spot Pricing Overview & Spot Advisor: https://aws.amazon.com/ec2/spot/pricing/
34. Vantage / EC2 Spot tracking for `c7i.xlarge`: https://instances.vantage.sh/aws/ec2/c7i.xlarge
35. Vantage / EC2 Spot tracking for `c6i.xlarge`: https://instances.vantage.sh/aws/ec2/c6i.xlarge
36. Vantage / EC2 Spot tracking for `c7g.xlarge`: https://instances.vantage.sh/aws/ec2/c7g.xlarge
37. Graham, R. L. (1969). Bounds on Multiprocessing Timing Anomalies (LPT 4/3 − 1/(3m) bound). *SIAM Journal on Applied Mathematics*, 17(2), 416–429.
38. EnergyPlus Engineering Reference (Heat Balance & Zone/Surface scaling): https://energyplus.net/documentation
39. EnergyPlus Runtime Regression Feature Considerations (ReadTheDocs / Big Ladder Input-Output Reference).
40. Adams, M. B., & New, J. R. (2018). *EnergyPlus Interior Radiant Heat Exchange Runtime Performance Improvements*. 2018 ASHRAE and IBPSA-USA Building Performance Analysis Conference and SimBuild, Chicago, IL (ORNL / IBPSA).
41. Big Ladder Software EnergyPlus Input-Output Reference — `ShadowCalculation` & Non-convex shading errors: https://bigladdersoftware.com/epx/docs/
42. Joblib Documentation (`Parallel`, `batch_size`, `pre_dispatch`, `return_as`, `loky` backend): https://joblib.readthedocs.io/en/latest/parallel.html
43. Joblib / Loky dispatch internals & worker management: https://loky.readthedocs.io/
44. Python `concurrent.futures.ProcessPoolExecutor` vs `joblib`/`loky` vs `GNU Parallel` dispatch overhead benchmarks.
45. Dask Distributed Performance & Future Overhead (~1 ms/task): https://docs.dask.org/en/stable/
46. Ray Core Performance Tips (1–10 ms task overhead): https://docs.ray.io/en/latest/
47. GNU Parallel Official Documentation & StackExchange overhead benchmarks (~2–10 ms/job): https://www.gnu.org/software/parallel/
48. SchedMD Slurm Configuration (`batch_sched_delay`, `--array` throttling): https://slurm.schedmd.com/slurm.conf.html and https://slurm.schedmd.com/job_array.html
49. HTCondor Manual (High-Throughput Job Scheduling & File Staging): https://htcondor.readthedocs.io/
50. Chen, Y., & Hong, T. (2018). Impacts of building geometry modeling methods on the simulation results of urban building energy models. *Applied Energy*, 215, 717–735. DOI: `10.1016/j.apenergy.2018.02.073`
51. Tall-building EnergyPlus zone multiplier & altitude/stack-effect error studies (LBNL / NREL / *Energy and Buildings*).
52. Dogan, T., & Reinhart, C. (2017). Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation. *Energy and Buildings*, 140, 140–153 (and Dogan, Reinhart, & Michalatos 2016 *Autozoner*, *Journal of Building Performance Simulation*).
53. Thermal zone clustering / aggregation accuracy vs overheating metrics in UBEM (*Energy and Buildings* / IBPSA).
54. Urban context shading distance thresholds (50 m vs 100 m) and complexity reduction in UBEM (MDPI / IBPSA).
55. Big Ladder Software EnergyPlus 23.1 Input-Output Reference — `ShadowCalculation` (`SutherlandHodgman`, `PixelCounting`, 20-day default update frequency).
56. Hoover, J., & Dogan, T. (2017). Fast and Robust External Solar Shading Calculations using the Pixel Counting Algorithm with Transparency. *Proceedings of the 15th International IBPSA Building Simulation Conference*, San Francisco, CA. DOI: `10.26868/25222708.2017.287`
57. Headless EnergyPlus `PixelCounting` via NVIDIA Container Toolkit / EGL vs Mesa `llvmpipe` software fallback.
58. EnergyPlus CLI (`-x` / `ExpandObjects`, `-r` / `ReadVarsESO`) & `SimulationControl`: https://github.com/NREL/EnergyPlus
59. `epJSON` vs `IDF` schema validation and parsing trade-offs (IBPSA / ReadTheDocs).
60. EnergyPlus `SimulationControl` & Sizing Calculations (`Sizing:Zone`, `Sizing:System`, `Sizing:Plant`): Big Ladder Input-Output Reference.
61. DOE / LBNL / ORNL "EnergyPlus 10X" runtime reduction initiative: https://www.energy.gov/
62. `OutputControl:Files` (introduced EnergyPlus 9.4.0) bypassing `ReadVarsESO`: Big Ladder Input-Output Reference.
63. `Output:SQLite` write trade-offs vs `.eso` / `ReadVarsESO`: Big Ladder Input-Output Reference.
64. SQLite Official Documentation ("SQLite Over a Network Filesystem"): https://www.sqlite.org/useovernet.html
65. Linux `tmpfs` (`/dev/shm`) & SLURM local scratch staging patterns for SQLite workloads.
66. NREL EnergyPlus GitHub Repository (no official ARM/Graviton/Apple Silicon cross-arch benchmark published): https://github.com/NREL/EnergyPlus
67. Apple Silicon Rosetta 2 x86 translation overhead for compute-bound C++ workloads vs native ARM64 builds.
68. AWS Graviton Architecture (1:1 physical-to-vCPU core mapping, NEON SIMD) vs x86 AVX2/AVX-512: https://aws.amazon.com/ec2/graviton/
69. AWS Graviton price-performance benchmarks vs x86 EC2 instances: https://aws.amazon.com/ec2/graviton/
70. Simultaneous Multithreading (SMT) / Hyper-Threading cache and floating-point contention in scientific HPC workloads.
71. EnergyPlus RAM consumption per simulation instance (OSTI / DesignBuilder / IBPSA multi-zone guidance).
