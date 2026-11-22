# DR02 — EnergyPlus Runtime Anatomy, PixelCounting (GPU Shading) & Speed Settings

**Target platform context:** OpenUBEM running **EnergyPlus 23.1** (`energyplus -w EPW -d DIR -x -r in.idf`), `Timestep, 6;`, annual `RunPeriod`, `Building` Solar Distribution = `FullExterior`, no `ShadowCalculation` object (defaults apply), 20–340 zones per building, neighboring buildings within 20 m modeled as `Shading:Building:Detailed` / `Shading:Site:Detailed`, `HVACTemplate` systems (~10 families), outputs mostly `RunPeriod` meters to SQLite plus optional hourly zone variables. Observed runtime on Apple M2 Pro (1 thread/run): median 3.2 s, p99 233 s, max 907 s. Target GPUs: Apple M2 Pro (macOS) and Windows workstation with NVIDIA CUDA GPU.

---

## 1. Executive Summary & Ranked Speed Levers

OpenUBEM's heavy-tailed runtime distribution (median 3.2 s vs. p99 233 s / max 907 s) is characteristic of two compounding effects in EnergyPlus:
1. **Quadratic exterior polygon-clipping scaling (`PolygonClipping` default)** when neighboring buildings add hundreds of `Shading:Building:Detailed` / `Shading:Site:Detailed` surfaces around multi-zone buildings (20–340 zones). In a controlled ablation conducted on this M2 Pro workstation using `5ZoneAirCooled.idf` + 400 `Shading:Building:Detailed` context surfaces (Denver/Golden TMY3), **exterior shading accounted for 89.5% of total runtime** (60.62 s out of 67.72 s in E+ 23.1).
2. **Non-linear zone/surface and HVAC iteration scaling** in the 20–340 zone tail: `TipsAndTricksUsingEnergyPlus.pdf` (E+ 23.1, §6.10) documents that scaling `MultiStory.idf` from 9 zones to 60 zones (6.67× zones) increases runtime by **11.5–12.5×** (Ideal Loads: 50–51 s → 9m37s–10m31s; Baseboard/WindowAC: 1m04s–1m17s → 13m15s–14m43s).
3. **Platform/post-processing overhead on the fast median buildings (3.2 s):** Local inspection of `/Applications/EnergyPlus-23-1-0/energyplus` confirms E+ 23.1 for macOS is compiled as **`macOS12.1_x86_64`** (running under Rosetta 2 translation on Apple M2 Pro), whereas `/Applications/EnergyPlus-24-2-0/energyplus` is native **`macOS13_arm64`** (~11–23% faster in local benchmarks). Additionally, the `-r` flag invokes `ReadVarsESO`, which alone took **2.43 s** wall-clock in a local test on a 10 MB `eplusout.eso` file—nearly matching OpenUBEM's 3.2 s median when time-series `.eso` output is generated.

### Ranked List of Speed Levers for OpenUBEM

| Rank | Lever | Expected Speedup Range | Accuracy Risk | Evidence Quality |
|---:|---|---|---|---|
| **1** | **Switch `ShadowCalculation` Method to `PixelCounting`** (on buildings with >~200 shading/exterior surfaces; keep `PolygonClipping` below ~200) | **2× average** (Hoover & Dogan 2017); **4.86× overall / ~7.8× shading** measured on M2 Pro (`5ZoneAirCooled` + 400 shading surfaces: 67.72 s → 13.94 s) | **Very low** for opaque context (`0.01` sunlit fraction threshold per Hoover & Dogan 2017; **0.005%** site energy delta measured locally: 205.82 → 205.81 GJ). **High if translucent shading is used** (E+ 23.1 forces transmittance = 0). | **High** (peer-reviewed IBPSA 2017 + E+ I/O Ref + local M2 Pro measurement) |
| **2** | **Zone / Floor Multipliers (`Zone` `Multiplier` + `ZoneGroup`)** for identical repeated apartment/office stories | **5–12×** on tall repetitive buildings (11.3–12.5× measured in E+ `TipsAndTricks` §6.10 for 60→9 zones) | **Low if height variation is neutralized and floors are unshaded/identically shaded** (<0.5% when `Site:WeatherStation`/`Site:HeightVariation` height effects disabled); **High (up to 76–91% monthly error)** if height variation is left active or urban shading varies sharply by floor. | **High** (E+ 23.1 `TipsAndTricksUsingEnergyPlus.pdf` §6.10 benchmark) |
| **3** | **`PerformancePrecisionTradeoffs` `Use Representative Surfaces for Calculations = Yes`** | **Moderate–High** (unquantified general speedup; targets surface heat balance & `ScriptF` longwave exchange, which is $O(N_{\text{surf}}^2)$ per zone) | **Very low** (keeps individual solar shading & interior solar per surface; area-averages absorbed solar across identical surfaces in a zone/enclosure). | **Moderate** (E+ 23.1 I/O Ref p. 77–78; exact speedup % not published in I/O Ref) |
| **4** | **Context & Geometry Simplification + `Disable Self-Shading` Zone Groups** (merge coplanar walls, replace multi-face neighbor buildings with simple bounding boxes, cull context >20 m or negligible view factor, group unshaded interior/courtyard zones) | **1.5–10×** on urban-dense tail buildings (depends on surface reduction squared: $O(N_{\text{cast}} \times N_{\text{recv}})$) | **Low–Moderate** (depends on geometric fidelity of bounding boxes and self-shading occlusion). | **Moderate** (algorithmic $O(N^2)$ scaling + E+ I/O Ref §1.5.11.1.9–10 + local 0-vs-400 shading ablation) |
| **5** | **Drop `-r` (`ReadVarsESO`) when only SQLite is needed** (or use `OutputControl:Files, Yes` native CSV) | **Saves ~0.5–5+ s fixed post-processing** (measured **2.43 s** on 10 MB `.eso`; eliminates a major share of OpenUBEM's 3.2 s median if `.eso` is non-empty) | **Zero** (output format only; SQLite retains identical numerical results). | **High** (E+ 23.1 I/O Ref p. 2803 + local M2 Pro measurement) |
| **6** | **Pre-expand `HVACTemplate:*` once (drop `-x`) & turn off unused outputs (`OutputControl:Files`)** | **Saves ~0.07–2 s/run** (0.067 s measured for `ExpandObjects` with no templates; up to 1–2 s with heavy templates/ground preprocessors; disabling ESO/MTR/DXF/EIO/Tabular cuts disk I/O) | **Zero** (identical expanded IDF and physics). | **Moderate–High** (E+ 23.1 I/O Ref p. 2803 + local M2 Pro timing; template-heavy timing claimed) |
| **7** | **Upgrade E+ 23.1 → E+ 24.2+ (native `arm64` on Apple M2 Pro)** | **1.13–1.30× on Apple Silicon** (measured on M2 Pro: 11.4% faster baseline `5Zone`, 22.9% faster on 400-shading `PolygonClipping`: 67.72 s → 52.20 s) | **Negligible** (version-to-version model updates: 205.52 → 205.44 GJ = 0.04% on `5ZoneAirCooled`). | **High** (local M2 Pro measurement + verified Mach-O architectures) |
| **8** | **Relax `Timestep` (`6` → `4` or `2`)** | **~1.4–2.5×** (sublinear with timestep reduction; Hong et al. 2008 & `PerformancePrecisionTradeoffs` Mode01 `6→1` gave **2.64×** on 100-zone FCU model) | **Low–Moderate** at `4` (15 min); **Moderate–High** at `2` or `1` (IOR `Timestep` IDD warns `< 6` may cause inaccuracies; increases deadband oscillation hours). | **High** (E+ 23.1 IDD l.923 + I/O Ref Table 1.3–1.5 + Hong et al. 2008) |
| **9** | **`ShadowCalculation` Update Frequency (`20` → `30` days)** vs **`1` or `Timestep`** | **Marginal** (`20→30` saves ~33% of shading work, ~5–15% total only on shading-dominated runs; conversely avoiding `1`/`Timestep` prevents **5–20×** slowdown) | **Low** (`20→30` days averages solar angles over 30 days; IDD warns if `> 31` days). | **Moderate** (E+ 23.1 IDD l.601–606 + I/O Ref p. 62) |
| **10** | **`PerformancePrecisionTradeoffs` `Override Mode` (`Mode02`–`Mode04`)** | **2.64–2.82×** measured on 100-zone FCU + chiller/boiler model (`275.56 s → 97.87 s`, Mode04; Mode05–08 reach **5.8–6.2×** at `44–47 s`) | **Low** for Mode01–04 (<0.34% elec, 0.5–1.1% gas, 2.6→8.7 hr oscillation); **High** for Mode05–08 (oscillating hours jump **65×**, 2.6→169 hr). | **High** (E+ 23.1 I/O Ref §1.5.17 Tables 1.3–1.5) |
| **11** | **`SimulationControl` Sizing Control** (pre-size once, or set `Do Zone/System/Plant Sizing Calculation = No` and `Run Simulation for Sizing Periods = No` for parametric sweeps) | **Small–Moderate** (IOR p. 68 states standard sizing runs *"do not add much to the overall simulation time"*; disabling `Do HVAC Sizing Simulation for Sizing Periods` avoids multi-pass overhead) | **Zero** if equipment is already hard-sized from a baseline run; **Severe** if autosized fields become un-sized. | **Moderate** (E+ 23.1 I/O Ref p. 68–69) |
| **12** | **In-process `pyenergyplus` (`run_energyplus` + `reset_state`)** vs CLI subprocess | **Negligible (~1.02× / ~0.13 s/run)** (measured on M2 Pro E+ 24.2: 5.35 s vs 5.49 s mean over 3 runs) | **Low** if `reset_state` succeeds, **Risk of heap bloat / leak** over 100s of diverse IDFs. | **High** (local M2 Pro benchmark + E+ `pyenergyplus/state.py` inspection) |

---

## 2. Q1: EnergyPlus Runtime Anatomy & Scaling

### 2.1 Subsystem Breakdown

EnergyPlus executes a tightly coupled, sequential-per-timestep heat balance + HVAC/plant loop inside `ManageSimulation()` (`RunEnergyPlus`):
1. **Input Parsing & Preprocessing (`GetInput`, `ExpandObjects`, CTF initialization):** Reads IDF/epJSON, expands `HVACTemplate:*` / `GroundHeatTransfer:*` if `-x` is passed, and computes Conduction Transfer Function (CTF) coefficients once at startup (`AuxiliaryPrograms.pdf` p. 171; Hong et al. 2008).
2. **Sizing & Warm-up Periods:** Runs `SizingPeriod:DesignDay` (if enabled) and iterates warmup days (min 1, max 25 by default) until zone mean air temperature and cooling/heating load changes between consecutive warmup days fall below `Temperature Convergence Tolerance Value` (`0.4 °C`) and `Loads Convergence Tolerance Value` (`0.04 W`) (`Building` object, E+ 23.1 IDD lines 535–573; I/O Ref p. 53–54).
3. **Solar & Shadowing (`SolarShading::PerformSolarCalculations`):** By default (`Periodic, 20`), computes sun positions and shadow overlaps once every 20 days for all hourly/sub-hourly sunlit timesteps, storing sunlit fractions for reuse across the 20-day block (E+ 23.1 I/O Ref p. 61). Under `PolygonClipping`, `SHADOW` → `SHDGSS` → `DeterminePolygonOverlap` → `CLIPPOLY` projects every candidate casting surface onto every receiving surface.
4. **Surface Heat Balance & Interior Longwave Radiation (`ManageHeatBalance`):** Evaluates inside/outside convection, CTF conduction history, and interior longwave radiant exchange (`ScriptF` matrix or `CarrollMRT`). In LBNL's profiling study (*EnergyPlus Run Time Analysis*, Hong, Buhl, & Haves 2008, LBNL-1311E), `CALCINTERIORRADEXCHANGE` and `UPDATEDATAANDREPORT` consistently appeared at the top of CPU self-time routines. Switching `HeatBalanceAlgorithm` from default `ConductionTransferFunction` to `ConductionFiniteDifference` increased runtimes by **1.8× to 3.9×** (Hong et al. 2008). Changing interior/exterior convection algorithms altered runtime by **< 3.6%** on school models (Hong et al. 2008).
5. **Zone Air Heat Balance & Predictor-Corrector (`ManageHVAC`):** Solves the zone air thermal capacitance ODE (`ThirdOrderBackwardDifference`, `AnalyticalSolution`, or `EulerMethod`) and iterates air-loop and plant-loop solvers (`RegulaFalsi` / `Bisection`) up to `Maximum HVAC Iterations` (default 20) and `Maximum Plant Iterations` (default 8), ratcheting the system timestep down toward `Minimum System Timestep` (default 1 min if `ConvergenceLimits` is omitted; `MaxZoneTempDiff` = 0.3 °C, `MaxAllowedDelTemp` = 0.002 °C) whenever loads/temperatures swing rapidly (E+ 23.1 IDD lines 932–960; I/O Ref p. 76–77).
6. **Output Writing & Post-Processing (`UPDATEDATAANDREPORT`, `Output:SQLite`, `ReadVarsESO`):** Hong et al. (2008) identified `UPDATEDATAANDREPORT`, `SETREPORTNOW`, and `SETMINMAX` as major CPU consumers when sub-hourly/hourly variables are reported. `Output:SQLite` adds concurrent/end-of-run DB write overhead (claimed **+5–20%** depending on `Simple` vs. `SimpleAndTabular` and reporting frequency; exact percentage across OpenUBEM models should be measured locally as literature varies). `ReadVarsESO` (`-r`) runs as a separate post-processing pass on `eplusout.eso` and `eplusout.mtr`.

### 2.2 Scaling Behavior (Zones, Surfaces, Shading Surfaces)

* **Shading surfaces — Quadratic $O(N_{\text{cast}} \times N_{\text{recv}})$ under `PolygonClipping`:** Traditional polygon-clipping shading tests candidate casting surfaces against receiving building surfaces (UBEM literature, e.g., Hoover & Dogan 2017; CityBES/UBEM reviews). Adding neighboring buildings within 20 m as `Shading:Building:Detailed` creates an $O(N_{\text{shad}} \cdot N_{\text{ext}})$ explosion—and because `DoNotMirrorDetachedShading` is off by default, EnergyPlus mirrors detached shading surfaces to catch back-facing orientation errors (E+ 23.1 I/O Ref p. 65), effectively doubling the casting polygons tested.
  * **Local M2 Pro measurement (`5ZoneAirCooled.idf`, Denver/Golden TMY3, E+ 23.1):**
    * 0 context shading surfaces (`PolygonClipping`): **6.04 s**
    * +400 `Shading:Building:Detailed` surfaces (`MinimalShadowing`): **7.10 s**
    * +400 `Shading:Building:Detailed` surfaces (`PolygonClipping`, `FullExterior`): **67.72 s** (**11.2× total slowdown**; **60.62 s = 89.5%** spent purely in exterior shading!)
* **Zone & Surface count — Super-linear scaling:** Interior view-factor and `ScriptF` longwave exchange scale as $O(N_{\text{surf,zone}}^2)$ within each zone (E+ I/O Ref §1.5.17; Hong et al. 2008), while whole-building HVAC/plant loops and surface lists introduce cache/memory pressure and solver coupling.
  * **E+ `TipsAndTricks` Benchmark (`MultiStory.idf`, 5 US cities, 10-story building):**
    * 9 zones (multipliers active): **0:50–0:51** (Ideal Loads) / **1:04–1:17** (Baseboard + WindowAC)
    * 18 zones (partially un-multiplied): **1:34–1:40** (~1.9×) / **2:05–2:28** (~1.95×)
    * 60 zones (fully explicit, 6.67× zones vs. 9-zone model): **9:37–10:31** (**11.3–12.4×**) / **13:15–14:43** (**11.5–12.5×**).
  * This super-linear scaling (6.67× zones → ~12× runtime) directly explains why OpenUBEM's 20–340 zone buildings with 20 m urban context stretch to 233–907 s.

---

## 3. Q2: Profiling EnergyPlus

### 3.1 Built-in Timing, Logs & Diagnostics

1. **`eplusout.err` & `eplusout.end` (Built-in Elapsed Time):**
   Every run prints total wall-clock elapsed time at the bottom of `eplusout.err`:
   `************* EnergyPlus Completed Successfully-- 5 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  6.04sec`
   It also separates `Warmup Error Summary` and `Sizing Error Summary`. Warmup iteration count per environment is recorded in `eplusout.eio` under `Environment:WarmupDays` (`OutputDetailsAndExamples.pdf` p. 124).
2. **`Output:Diagnostics` (E+ 23.1 IDD lines 105906–105980):**
   * `DisplayExtraWarnings`: surfaces geometry/volume/non-convexity warnings that cause solver slowdowns.
   * `ReportDetailedWarmupConvergence`: writes per-day, per-zone temperature/load deltas to `eplusout.eio` so you can spot zones stalling warmup at 25 days.
   * `DisplayZoneAirHeatBalanceOffBalance`: developer diagnostic flagging zone heat balance residuals.
   * Note: `Output:Diagnostics` does **not** print per-module CPU timers.
3. **`PerformancePrecisionTradeoffs` → `<prefix>_perflog.csv` (I/O Ref p. 69–70):**
   Adding even a default `PerformancePrecisionTradeoffs;` object causes EnergyPlus to append a row to `eplusout_perflog.csv` containing `Runtime [second]`, `Warnings`, `Oscillating [hour]` (total/occupancy/deadband), and ABUPS energy totals (`OutputDetailsAndExamples.pdf` p. 134). High oscillating hours directly signal HVAC timestep ratcheting (`min system timestep` shrinking to 1 min).
4. **CLI `--debug` / Compile-time Timers:**
   * **Verified via `/Applications/EnergyPlus-23-1-0/energyplus --help` and `/Applications/EnergyPlus-24-2-0/energyplus --help`:** There is **no `--debug` CLI flag** and no user-facing `--timer` CLI flag in shipped EnergyPlus binaries. (There is `Output:DebuggingData`, IDD l.105982, which dumps node state every timestep to `eplusout.dbg` and slows runs down—not a profiler.)
   * Compile-time developer performance tests (`BUILD_PERFORMANCE_TESTS`) exist in the source repo, not in release binaries.

### 3.2 External Native Profilers (Unstripped Symbols Confirmed!)

By inspecting `/Applications/EnergyPlus-23-1-0/libenergyplusapi.23.1.0.dylib` and `/Applications/EnergyPlus-24-2-0/libenergyplusapi.24.2.0.dylib` with `nm` and `sample`, **official macOS EnergyPlus release binaries retain full C++ symbol names** (not stripped). That means OS sampling profilers work out-of-the-box without recompiling from source:
* **macOS (Apple M2 Pro):** Built-in `sample` CLI or Xcode **Instruments (Time Profiler)**. Verified live on `energyplus-24.2.0` (`shade400_poly.idf`): `sample` resolved exact C++ call stacks (`SolarShading::PerformSolarCalculations` → `SHADOW` → `SHDGSS` → `DeterminePolygonOverlap` → `CLIPPOLY` + `CTRANS` + `HTRANS1`).
* **Linux:** `perf record -F 999 -g -- energyplus ...` + `perf report` (or `FlameGraph`).
* **Windows / Linux (x86_64):** Intel VTune (`vtune -collect hotspots -- energyplus.exe ...`).

*(Concrete step-by-step commands and shading-share ablation instructions are in **Section 7: Profiling Recipe**.)*

---

## 4. Q3: PixelCounting / Penumbra Dossier

### 4.1 History, Library (`bigladder/penumbra`), and E+ Configuration

* **EnergyPlus version introduced:** `PixelCounting` was introduced in **EnergyPlus v9.3.0** (April 2020), building on the algorithm of Jones et al. (2011) and Hoover & Dogan (2017, *Building Simulation 2017*, "Fast and Robust External Solar Shading Calculations using the Pixel Counting Algorithm with Transparency").
* **Underlying library — `bigladder/penumbra`:**
  * **URL:** `https://github.com/bigladder/penumbra`
  * **Author / Maintainer:** Big Ladder Software (primary developer: Neal Kruis `@nealkruis`).
  * **Language / Build:** C++ with cross-platform CMake (`third_party/penumbra` inside EnergyPlus), using **GLFW** for OpenGL context creation and `tess2` for polygon tessellation.
  * **Licence:** **BSD-3-Clause**.
  * **Popularity & Maintenance:** Niche engineering library (~8–9 GitHub stars, 312+ commits noted in repository index). Receives periodic CI/compiler/submodule maintenance commits (e.g., GLFW header fixes, `clang-cl` / Ubuntu Wayland CI updates; exact latest commit timestamp not retrievable via `search_web` summary — check repo directly before pinning a fork, flag exact date as `UNVERIFIED` here). Inside EnergyPlus (`NatLabRockies/EnergyPlus`, formerly `NREL/EnergyPlus`), Penumbra integration also receives occasional maintenance PRs (e.g., PR #11258 masking host floating-point traps around GLFW).

#### Exact E+ 23.1 `ShadowCalculation` IDD Fields & Defaults (`/Applications/EnergyPlus-23-1-0/Energy+.idd`, lines 575–680)
All `ShadowCalculation` field names and defaults are **identical in E+ 23.1 and E+ 24.2** (verified line-by-line against `/Applications/EnergyPlus-24-2-0/Energy+.idd` lines 576–680):

| Field ID | Exact IDD Field Name | Choices / Type | Default | Role with `PixelCounting` |
|---|---|---|---|---|
| `A1` | `Shading Calculation Method` | `PolygonClipping`, `PixelCounting`, `Scheduled`, `Imported` | `PolygonClipping` | Selects GPU Penumbra engine. |
| `A2` | `Shading Calculation Update Frequency Method` | `Periodic`, `Timestep` | `Periodic` | `Timestep` required only for dynamic shades/blinds; drastically slower. |
| `N1` | `Shading Calculation Update Frequency` | integer ($\ge 1$, warn $> 31$) | `20` | Days between shading recalculations (`Periodic` mode). |
| `N2` | `Maximum Figures in Shadow Overlap Calculations` | integer ($\ge 200$) | `15000` | Applies to `PolygonClipping` only (ignored by `PixelCounting`). |
| `A3` | `Polygon Clipping Algorithm` | `ConvexWeilerAtherton`, `SutherlandHodgman`, `SlaterBarskyandSutherlandHodgman` | `SutherlandHodgman` | Applies to `PolygonClipping` (and fallback). |
| `N3` | `Pixel Counting Resolution` | integer | `512` | Width & height ($512 \times 512$) of offscreen orthographic render target per sun/sky pass. |
| `A4` | `Sky Diffuse Modeling Algorithm` | `SimpleSkyDiffuseModeling`, `DetailedSkyDiffuseModeling` | `SimpleSkyDiffuseModeling` | One-time vs. periodic/timestep sky diffuse shading. |
| `A5` | `Output External Shading Calculation Results` | `Yes`, `No` | `No` | Writes `<prefix>shading.csv` for reuse via `Imported`. |
| `A6–A13` | `Disable Self-Shading Within Shading Zone Groups` / `From Shading Zone Groups to Other Zones` / `Shading Zone Group 1..6 ZoneList Name` | `Yes`/`No` + `ZoneListNames` | `No` | Skips exterior self-shading between heat-transfer surfaces (never disables `Shading:*` surfaces). |

#### Copy-Paste IDF Config Snippet (EnergyPlus 23.1)
```idf
ShadowCalculation,
  PixelCounting,             !- Shading Calculation Method
  Periodic,                  !- Shading Calculation Update Frequency Method
  20,                        !- Shading Calculation Update Frequency {days}
  15000,                     !- Maximum Figures in Shadow Overlap Calculations (used only on fallback)
  SutherlandHodgman,         !- Polygon Clipping Algorithm (used only on fallback)
  512,                       !- Pixel Counting Resolution
  SimpleSkyDiffuseModeling,  !- Sky Diffuse Modeling Algorithm
  No,                        !- Output External Shading Calculation Results
  No,                        !- Disable Self-Shading Within Shading Zone Groups
  No;                        !- Disable Self-Shading From Shading Zone Groups to Other Zones
```

### 4.2 Hardware, OS, and Headless Requirements

Binary string inspection of `/Applications/EnergyPlus-23-1-0/libenergyplusapi.23.1.0.dylib` confirms the exact graphics requirements inside EnergyPlus/Penumbra:
* **OpenGL 2.1+**, **Vertex Array Objects (VAOs)**, and **Framebuffer Objects (FBOs)** via **GLFW** (exact binary error strings: `"Unable to initialize GLFW."`, `"Unable to create OpenGL context. OpenGL 2.1+ is required to perform GPU accelerated shading calculations."`, `"The current version of OpenGL does not support vertex array objects."`, `"The current version of OpenGL does not support framebuffer objects."`).

**Platform-by-platform behavior:**
1. **macOS (Apple M2 Pro) — DIRECTLY VERIFIED:**
   * Even though Apple deprecated OpenGL (capping legacy compatibility at OpenGL 2.1 and Core Profile at 4.1 since macOS 10.14), Penumbra requests an **OpenGL 2.1+** compatibility context via Cocoa/GLFW, which **still executes natively on macOS**.
   * **Verified locally on M2 Pro:** Both E+ 23.1 (`x86_64` Rosetta 2) and E+ 24.2 (`arm64` native) ran `ShadowCalculation, PixelCounting` cleanly with **0 fallback warnings**, confirmed in `eplusout.eio` (`Shadowing/Sun Position Calculations Annual Simulations,PixelCounting,...`).
2. **Linux Headless / HPC:**
   * Standard upstream EnergyPlus Linux binaries link GLFW against **X11/GLX**, **not** native headless EGL (`UNVERIFIED` for a given distro build without `ldd` inspection, though `third_party/penumbra` uses standard desktop GLFW/X11 unless compiled with `-DGLFW_USE_OSMESA=1`).
   * **Without an X server (`$DISPLAY` unset):** `glfwInit()` fails (`"Unable to initialize GLFW."`) and E+ silently falls back to `PolygonClipping`.
   * **Headless Recipe Option A (`Xvfb` — CPU Mesa `llvmpipe` or virtual display):**
     ```bash
     # Works on GPU-less Linux HPC/Docker nodes (uses CPU software rasterizer Mesa llvmpipe; slower than hardware GPU)
     xvfb-run -a -s "-screen 0 1024x768x24" energyplus -w weather.epw -d out in.idf
     ```
   * **Headless Recipe Option B (NVIDIA GPU on headless Linux via VirtualGL or headless Xorg):**
     Running an NVIDIA-backed Xorg or VirtualGL (`vglrun`) allows GLFW/GLX to bind the physical NVIDIA GPU without a monitor. Native **EGL** without X11 requires recompiling GLFW/Penumbra with an EGL backend (not stock in E+ 23.1). **OSMesa** (CPU offscreen rendering) requires building EnergyPlus/GLFW with `-DGLFW_USE_OSMESA=1`.
3. **Windows Workstation with NVIDIA CUDA GPU (OpenUBEM target):**
   * **Multi-GPU / Optimus hazard:** EnergyPlus 23.1 I/O Reference (p. 62) explicitly warns: *"Some computers have multiple GPUs. In this case, the highest performance GPU is not always used by default. You may want to select which GPU is used when running EnergyPlus by setting the graphics performance preferences on your computer."*
   * **Does official `energyplus.exe` export `NvOptimusEnablement = 1`?** `UNVERIFIED` (not observed directly on a Windows binary in this macOS session; absent from macOS `dylib` as expected). Do not assume automatic dGPU selection on hybrid Intel/AMD + NVIDIA systems.
   * **How to force the NVIDIA dGPU on Windows 10/11:**
     1. *Windows OS Graphics Settings (takes precedence over NVIDIA Control Panel on Win 10/11):* **Settings → System → Display → Graphics** → Browse to `C:\EnergyPlusV23-1-0\energyplus.exe` → **Options → High performance** (select NVIDIA GPU).
     2. *NVIDIA Control Panel:* **Manage 3D settings → Program Settings** → Add `energyplus.exe` → **Preferred graphics processor: High-performance NVIDIA processor**.
   * **Headless / Remote Desktop (RDP) / Windows Service Warning:** Disconnected RDP sessions or non-interactive Windows Services (Session 0) can drop or virtualize the OpenGL WGL context onto Microsoft Basic Render Driver (CPU/OpenGL 1.1), causing `PixelCounting` to fail OpenGL 2.1+ checks and revert to `PolygonClipping`. Run inside an active console/VNC session or persistent GPU-enabled user session.
   * **How to confirm Windows E+ actually used the NVIDIA GPU (and didn't fall back):**
     1. Check `eplusout.err` for `"No GPU found"` or `"PolygonClipping will be used instead"`, AND check `eplusout.eio` line `Shadowing/Sun Position Calculations Annual Simulations,PixelCounting,...` (if it says `PolygonClipping`, it fell back!).
     2. Observe GPU utilization during the initialization/shading phase via **Task Manager → Performance → GPU (3D / Copy engine)** or `nvidia-smi dmon -s pu` (note: OpenGL processes show under `nvidia-smi` when using NVIDIA ICD, though compute/graphics visibility depends on WDDM vs TCC mode; **RenderDoc** or **Process Explorer** GPU Engine column reliably confirms `energyplus.exe` is bound to the NVIDIA adapter vs. Intel iGPU).
     3. Sanity-time a 400-shading-surface test (`5ZoneAirCooled` + 400 `Shading:Building:Detailed`) — NVIDIA dGPU should match or beat M2 Pro's 4.86× speedup over `PolygonClipping`, whereas software rasterization (`llvmpipe` / Microsoft Basic) will be much slower.

### 4.3 Fallback Behavior

Verified directly from `strings /Applications/EnergyPlus-23-1-0/libenergyplusapi.23.1.0.dylib`:
* If GLFW/OpenGL 2.1+ initialization fails (no display, no GPU, missing FBO/VAO), EnergyPlus **does not crash**; it logs a warning in `eplusout.err`:
  * `"No GPU found (required for PixelCounting)"`
  * `"PolygonClipping will be used instead"`
* And reverts `Shading Calculation Method` to **`PolygonClipping`** (confirmed in E+ 23.1 IDD lines 582–583 and `eplusout.eio`).
* **Dangerous side effect if using `FullInteriorAndExterior` on non-convex zones:** If you rely on `PixelCounting` to avoid non-convex zone errors under `FullInteriorAndExterior`, a silent/warning-only fallback to `PolygonClipping` in headless CI/HPC will trigger `PolygonClipping` concavity severe errors!

### 4.4 Speed & Accuracy Benchmarks + Known Bugs/Limitations

* **Crossover & Literature Benchmarks:**
  * **E+ 23.1 I/O Reference (p. 61):** `PixelCounting` incurs CPU↔GPU transfer overhead, so for **fewer than ~200 shading surfaces**, `PolygonClipping` is faster; above ~200 shading surfaces, `PixelCounting` scales dramatically better.
  * **Hoover & Dogan (2017, BS2017):** Reported **2× average speedup** over `PolygonClipping` on complex models, within a **0.01** sunlit-fraction validation threshold.
* **Direct Local M2 Pro Measurements (E+ 23.1 & 24.2, `5ZoneAirCooled.idf`, Golden TMY3):**

| Model Variant | E+ 23.1 `PolygonClipping` | E+ 23.1 `PixelCounting` | Speedup (23.1) | E+ 24.2 `PolygonClipping` | E+ 24.2 `PixelCounting` | Total Site Energy Delta (`Pix` vs `Poly`) |
|---|---:|---:|---:|---:|---:|---|
| `5ZoneAirCooled` (0 context shades) | 6.04 s | 7.95 s | **0.76×** (1.91 s slower) | 5.35 s | 6.36 s | 205.51 vs 205.52 GJ (**-0.005%**) |
| `5ZoneAirCooled` + 400 `Shading:Building:Detailed` | 67.72 s | **13.94 s** | **4.86× faster** | 52.20 s | **11.29 s** | 205.81 vs 205.82 GJ (**-0.005%**) |

* **Known Bugs & Limitations (critical for OpenUBEM):**
  1. **Shading transmittance ignored (forces opaque, transmittance = 0):** Verified directly in E+ 23.1 binary strings:
     `The Shading Calculation Method of choice is "PixelCounting"; ... With "PixelCounting" Shading Calculation Method, the shading surfaces will be treated as completely opaque (transmittance = 0) during the shading calculation, It is suggested switching to another Shading Calculation Method, such as "PolygonClipping".`
     Also tracked in `NREL/EnergyPlus` Issue **#9059** (*"Unexpected behavior when using shading surfaces with transmittance schedule and PixelCounting"*). If OpenUBEM models deciduous trees or louvered overhangs with `Transmittance Schedule Name`, `PixelCounting` ignores the transmittance! (For solid neighboring buildings, transmittance = 0 is exact.)
  2. **Non-convex zones & `FullInteriorAndExterior`:** E+ I/O Ref (p. 61) explicitly states `PixelCounting` *"has no limitations related to zone concavity when used with any 'FullInterior' solar distribution options"*. However, **GitHub Issue #10299** documented that `CheckConvexity` still emits `"Surface is Non-Convex"` warnings regardless of `ShadowCalculation` settings. (Not an issue for OpenUBEM's `FullExterior`, though helpful if switching to `FullInteriorAndExterior`.)
  3. **`Pixel Counting Resolution` trade-off:** Default `512` (512×512). Increasing resolution (e.g., 1024 or 2048) raises pixel rasterization/readback time significantly (`I/O Ref` p. 63); reducing below 512 risks aliasing errors on thin fins/small windows.
  4. **Parallelism contention:** Running 8–16 E+ processes simultaneously on 1 GPU (`-j` / multiprocessing pool) causes GPU context-switching/VRAM contention across processes (`UNVERIFIED` exact contention factor on NVIDIA CUDA GPUs—benchmark 4 vs 8 vs 12 concurrent workers on the Windows GPU workstation!).
  5. **GLFW Floating-Point Traps:** Resolved in newer releases (e.g., PR #11258 masking host FP traps around GLFW).

---

## 5. Q4: E+ Settings & Speed Levers Reference Table

All object names, field names, and defaults verified directly against `/Applications/EnergyPlus-23-1-0/Energy+.idd` (and checked against `24-2-0/Energy+.idd`).

| Object / Field (E+ 23.1 IDD) | Value Options (Default) | Speed Effect | Accuracy Effect | Source & Evidence |
|---|---|---|---|---|
| `Timestep` → `Number of Timesteps per Hour` | `1,2,3,4,5,6,10,12,15,20,30,60` (default **`6`**) | **~1.4–2.6×** when reduced (`6→1` gave **2.64×** in IOR Mode01 on 100-zone FCU; `6→4` ~1.3–1.5× `UNVERIFIED` exact ratio for OpenUBEM) | IDD l.923 warns `< 6` may cause inaccuracies; `6→1` changed 100-zone elec by 0.34%, gas by 1.06%, deadband oscillations 0.18→6.87 hr | E+ 23.1 IDD l.912–931; IOR Table 1.3–1.5; Hong et al. 2008 |
| `ShadowCalculation` → `Shading Calculation Method` | `PolygonClipping` (default), `PixelCounting`, `Scheduled`, `Imported` | `PixelCounting`: **0.76×** (<200 shades) to **4.86×** (400 shades). `Imported`/`Scheduled`: eliminates shading geometry runtime (**~89.5%** on 400-shade model) | `PixelCounting`: **0.005%** site energy delta on opaque context; forces transmittance=0. `Imported`: exact if precomputed for same geometry (`Schedule:File:Shading` + `Output External Shading Calculation Results`) | E+ 23.1 IDD l.575–592; IOR p. 61–63; local M2 Pro runs |
| `ShadowCalculation` → `Shading Calculation Update Frequency Method` & `Frequency` | `Periodic` (default), `Timestep`; integer $\ge 1$ (default **`20`** days) | Keeping `Periodic, 20` avoids **~5–20×** slowdown of `Timestep`/`1` day. Increasing `20→30` saves ~33% of shading work | Averages sun position over $N$ days; `>31` triggers warning; `Timestep` required only for movable/dynamic shading | E+ 23.1 IDD l.593–606; IOR p. 62; EngRef p. 214 |
| `ShadowCalculation` → `Maximum Figures in Shadow Overlap Calculations` | integer $\ge 200$ (default **`15000`**) | Lowering to `200` speeds diagnostic runs (Tips&Tricks Table 16.1); raising `>15000` slows complex scenes | Truncating overlap figures loses shadow accuracy or throws `Too many figures in shadow overlap` error | E+ 23.1 IDD l.607–611; Tips&Tricks Table 16.1; binary strings |
| `ShadowCalculation` → `Polygon Clipping Algorithm` | `SutherlandHodgman` (default), `ConvexWeilerAtherton`, `SlaterBarskyandSutherlandHodgman` | `SlaterBarskyandSutherlandHodgman` reduces clipping work on rectangular surfaces | Same geometric result for convex polygons; `ConvexWeilerAtherton` fails on concave receiving walls | E+ 23.1 IDD l.612–619; IOR p. 62–63; EngRef p. 218–224 |
| `ShadowCalculation` → `Disable Self-Shading Within Shading Zone Groups` / `From ... to Other Zones` | `Yes`, `No` (default **`No`**) | Skips exterior-to-exterior self-shading between building zones (does **not** skip `Shading:*` context) | Safe when buildings are convex/box footprints without L-wings self-shading; inaccurate for courtyards/wings | E+ 23.1 IDD l.639–679; IOR p. 64 |
| `Building` → `Solar Distribution` | `MinimalShadowing`, `FullExterior` (default), `FullInteriorAndExterior`, `*WithReflections` | `MinimalShadowing` cuts **89.5%** runtime on 400-shade test (`67.72→7.10 s`); `*WithReflections` is *"very time-consuming"* | `MinimalShadowing` removes all neighbor & self-shading (unacceptable in UBEM unless unshaded); `FullInteriorAndExterior` slower & requires convex zones under `PolygonClipping` | E+ 23.1 IDD l.548–556; IOR p. 49–51; local M2 Pro run |
| `Building` → `Loads Convergence Tolerance Value` & `Temperature Convergence Tolerance Value` | Loads: `>0..0.5` W (default **`0.04`**); Temp: `>0..0.5` °C (default **`0.4`**) | Loosening reduces warmup days (each saved warmup day saves ~1/365th of annual sim per environment) | Too loose prevents thermal mass stabilization before Jan 1 / design days | E+ 23.1 IDD l.535–547; IOR p. 53 |
| `Building` → `Maximum Number of Warmup Days` & `Minimum Number of Warmup Days` | Max: default **`25`** (IDD warns not `<25`); Min: default **`1`** (legacy was `6`) | Default Min=`1` already avoids 5 needless days vs legacy `6`. Capping Max (`<25`) saves time only on non-converging models | Capping Max below 25 risks `CheckWarmupConvergence` failure and thermal drift | E+ 23.1 IDD l.557–573; IOR p. 53–54 |
| `SimulationControl` → `Do Zone/System/Plant Sizing Calculation`, `Run Simulation for Sizing Periods`, `Do HVAC Sizing Simulation for Sizing Periods` | `Yes`/`No`; Sizing Periods default `Yes`; HVAC Sizing Sim default **`No`** (passes default `1`) | IOR p. 68: standard sizing runs *"do not add much to the overall simulation time"*; setting `Do HVAC Sizing Simulation = No` avoids multi-pass sizing loops; skipping sizing (`No`) saves design-day pass if pre-sized | `No` on sizing fields requires all equipment capacities/flows to be hard-sized | E+ 23.1 IDD l.400–456; IOR p. 68–69 |
| `ZoneAirHeatBalanceAlgorithm` → `Algorithm` | `ThirdOrderBackwardDifference` (default), `AnalyticalSolution`, `EulerMethod` | `EulerMethod` slightly faster per step (contributes ~5% of Mode02's gain over Mode01: `104.37→98.81 s` in IOR Table 1.3); `AnalyticalSolution` negligible per-step overhead | `AnalyticalSolution` has **zero time-step truncation error** and supports coarse timesteps cleanly; `EulerMethod` is 1st-order accurate | E+ 23.1 IDD l.773–797; IOR p. 58–59, 70 |
| `HeatBalanceAlgorithm` → `Algorithm` | `ConductionTransferFunction` (default), `MoisturePenetrationDepth...`, `ConductionFiniteDifference`, `CombinedHeatAndMoisture...` | Keep **`ConductionTransferFunction`** (default); `ConductionFiniteDifference` is **1.8–3.9× slower** (Hong et al. 2008) and requires `Timestep >= 20` | CTF is exact for linear constant-property walls without PCM/hygrothermal storage | E+ 23.1 IDD l.719–734; Hong et al. 2008 |
| `PerformancePrecisionTradeoffs` → `Override Mode` / `Use Representative Surfaces` / `Use Coil Direct Solutions` / `Zone Radiant Exchange Algorithm` | `Normal`..`Mode08`, `Advanced`; `Yes`/`No` (default `No`); `ScriptF` (default) / `CarrollMRT` | `Mode01–04`: **2.6–2.8×** (`275.6→97.9 s`); `Mode05–08`: **5.8–6.2×** (`44–47 s`); `Use Coil Direct Solutions`: **0.8%** (`275.6→273.4 s`); `CarrollMRT`: **no speedup** on 1-window/zone box (`276.7 s`) | `Mode04`: <0.34% elec, 0.84% gas, 2.6→8.7 hr osc. `Mode05–08`: **161–169 hr osc.** `CarrollMRT`: **16.6% gas shift** (`1.52M→1.27M MJ`) on 100-zone FCU model! | E+ 23.1 IDD l.457–508; IOR §1.5.17 Tables 1.3–1.5 |
| `Zone` (`Multiplier`, `N6`) & `ZoneGroup` (`Zone List Multiplier`, `N1`) | integer $\ge 1$ (default `1`) | **11.3–12.5×** (`MultiStory.idf`: 60 explicit zones `9m37s–14m43s` → 9 zones w/ multipliers `50s–1m17s`) | `<0.5%` diff **only** if height variation (`Site:WeatherStation`/`Site:HeightVariation`) is negated & interzone/shading match; **up to 76–91% monthly diff** otherwise | E+ 23.1 IDD l.9576, 10002; Tips&Tricks §6.10 Tables 6.1–6.4 |
| Geometry / Shading Simplification | Coplanar merge, bounding-box neighbor buildings, distance culling | Cuts both shading $O(N_{\text{cast}} \cdot N_{\text{recv}})$ and zone radiant exchange $O(N_{\text{surf}}^2)$ | Low if bounding-box envelope preserves solar obstruction profile; verify no missing close-in facade shading | E+ EngRef §5.4; local 400-shade ablation |
| `Output:SQLite` + `OutputControl:Files` | `Simple`, `SimpleAndTabular`; `OutputControl:Files` toggles CSV/ESO/MTR/EIO/Tabular/SQLite/DXF/etc. | `Output:SQLite` adds **~5–20%** (`UNVERIFIED` exact OpenUBEM %); `Simple` faster than `SimpleAndTabular`. Disabling unused `ESO`/`MTR`/`DXF`/`JSON`/`Tabular` saves I/O. Native CSV replaces `ReadVarsESO` | **Zero** physics impact (`Simple` omits `TabularData` HTML/SQL tables if you only query `ReportData` time-series/meters) | E+ 23.1 IDD l.105543, 105744; IOR p. 2801–2803 |
| Skipping `-r` (`ReadVarsESO`) & `-x` (`ExpandObjects`) | CLI flags `-r`, `-x` | `ReadVarsESO` measured **2.43 s** on 10 MB `.eso`; `ExpandObjects` measured **0.067 s** (no templates) up to ~1–2 s with heavy templates | **Zero** if SQLite is used directly (`-r` unneeded) and `HVACTemplate:*` is expanded once offline (`-x` unneeded) | Local M2 Pro measurement; AuxiliaryPrograms.pdf p. 171, 232 |

---

## 6. Q5 & Q6: Version Performance (23.1 → 25.x) & `pyenergyplus` API

### 6.1 EnergyPlus 23.1 → 24.x → 25.x Performance & IDD Deltas

* **Apple Silicon Native `arm64` (Huge for OpenUBEM's M2 Pro):**
  * `/Applications/EnergyPlus-23-1-0/energyplus` is compiled as **`Mach-O 64-bit executable x86_64`** (`Built on Platform: macOS12.1_x86_64`), running under Rosetta 2 emulation on Apple M2 Pro.
  * Starting in **v24.1.0**, EnergyPlus ships native **`macOS13_arm64`** builds (`/Applications/EnergyPlus-24-2-0/energyplus` verified `Mach-O 64-bit executable arm64`).
  * **Directly measured on M2 Pro (`5ZoneAirCooled.idf`):** Upgrading E+ 23.1 (`x86_64`) → E+ 24.2 (`arm64`) yielded **11.4% speedup** on baseline `PolygonClipping` (`6.04 s → 5.35 s`), **20.0% speedup** on `PixelCounting` (`7.95 s → 6.36 s`), and **22.9% speedup** on the 400-shading-surface `PolygonClipping` test (`67.72 s → 52.20 s`).
* **Engine & Reporting Optimizations (24.1 → 25.2):**
  * Release changelogs (`NREL/EnergyPlus` / `NatLabRockies/EnergyPlus` v24.1–v25.2) focus primarily on HVAC/plant feature additions, state/API refactoring for co-simulation (Spawn/Modelica), memory-leak fixes in `clear_state`, solver robustness (zero/low-flow stability, BSDF matrix transpositions), and targeted performance PRs (e.g., PR #11774 optimizing recurring error summarization; PR #11258 fixing Penumbra/GLFW FP traps). No single blanket engine-wide speedup percentage is claimed across v24.x–v25.x release notes for standard CTF/VAV models beyond native `arm64` compilation.
* **Verified IDD Changes (23.1 → 24.2 relevant to OpenUBEM):**
  * `ShadowCalculation` (A1–A13, N1–N3): **Unchanged** (no transition breakage for `PixelCounting`).
  * `SurfaceProperty:LocalEnvironment` A3: renamed from `External Shading Fraction Schedule Name` (23.1, IDD l.18724) to `Sunlit Fraction Schedule Name` (24.2, IDD l.18861) — matters only if using `Shading Calculation Method = Scheduled`.
  * `Output:SQLite` A2: added `InchPoundExceptElectricity` key in 24.2 (IDD l.107581).

### 6.2 `pyenergyplus` Python API (`run_energyplus`, State Reuse)

Inspected `/Applications/EnergyPlus-23-1-0/pyenergyplus/{api.py,runtime.py,state.py}` and benchmarked `/Applications/EnergyPlus-24-2-0/pyenergyplus` directly on M2 Pro (`5ZoneAirCooled.idf`, 3 consecutive runs):
* **Measured timing on M2 Pro:**
  * `EnergyPlusAPI()` load time: **0.011 s**
  * In-process `run_energyplus(state, ...)` + `reset_state(state)` (3 runs): `5.236 s`, `5.312 s`, `5.504 s` → **5.351 s/run** mean (16.140 s total)
  * Fresh `subprocess.run(['energyplus', ...])` (3 runs): `5.493 s`, `5.506 s`, `5.460 s` → **5.486 s/run** mean (16.459 s total)
  * **Net saving from eliminating process spawn:** **~0.135 s/run (~2.5%)** — practically negligible relative to OpenUBEM's 3.2 s median and 233 s p99.
* **Is reusing `state` across different buildings safe?**
  * `StateManager.reset_state(state)` (`state.py` l.90–98) invokes `api.stateReset(state)`, which resets simulation state and clears registered callbacks so a single state pointer *can* run different IDFs sequentially.
  * **Caveats:** (1) EnergyPlus allocates extensive heap structures during simulation, and upstream issues document occasional incomplete `clear_state` reclamation / RSS memory creep across many resets; (2) if a building hits a fatal error or segfault, the state/process is tainted; (3) passing `-x` or `-r` in `run_energyplus` args still spawns external `ExpandObjects` / `ReadVarsESO` subprocesses (`runtime.py` l.154–197).
  * **Recommendation for OpenUBEM:** Stick to `multiprocessing` / worker-pool CLI processes (or recycle `pyenergyplus` workers every 50–100 buildings via `delete_state` + worker restart) rather than an unbounded single-process `reset_state` loop.

---

## 7. Profiling Recipe (macOS & Linux)

### Step 1: Quantify Coarse Phase Costs via Differential Ablation (Zero Code Changes)
Pick 3–5 representative tail buildings (e.g., 100–340 zones, p95–max runtime) and run 5 controlled variants using `eplusout.err` (`Elapsed Time=...`) and `PerformancePrecisionTradeoffs;` (`eplusout_perflog.csv`):

1. **Baseline (`B0`):** Exact OpenUBEM CLI (`energyplus -w EPW -d out_B0 -x -r in.idf`). Measure total wall time $T_{\text{total}}$.
2. **Strip `-x` and `-r` (`B1`):** Pre-run `ExpandObjects` once to produce `expanded.idf`, then run `energyplus -w EPW -d out_B1 expanded.idf` (no `-x`, no `-r`).
   * $\Delta_{\text{aux}} = T_{\text{B0}} - T_{\text{B1}}$ gives exact `ExpandObjects` + `ReadVarsESO` overhead.
3. **Shading Ablation (`B2`):** Copy `expanded.idf` and set `Building` → `Solar Distribution = MinimalShadowing` (removes all exterior polygon clipping/shading).
   * **Shading share** $\approx (T_{\text{B1}} - T_{\text{B2}}) / T_{\text{B1}}$. *(Validated locally on `shade400`: $(67.72 - 7.10)/67.72 = 89.5\%$.)*
4. **PixelCounting Test (`B3`):** Keep `FullExterior`, add `ShadowCalculation, PixelCounting, Periodic, 20;`. Verify `eplusout.eio` contains `PixelCounting` (not `PolygonClipping` fallback).
   * Shading speedup $= (T_{\text{B1}} - T_{\text{B2}}) / (T_{\text{B3}} - T_{\text{B2}})$.
5. **HVAC / Output Check (`B4`):** Check `eplusout_perflog.csv` `Oscillating [hour]` and test `OutputControl:Files, No, No, No, No, No, Yes;` (SQLite only) to isolate I/O share.

### Step 2: Function-Level CPU Profiling (Per-Module Time)

#### On macOS (Apple M2 Pro — confirmed unstripped symbols in `libenergyplusapi.*.dylib`)
```bash
# 1. Start EnergyPlus in background and attach macOS 'sample' for 30s (1ms interval)
/Applications/EnergyPlus-24-2-0/energyplus -w weather.epw -d out_prof expanded.idf &
EP_PID=$!
sample $EP_PID 30 1 -mayDie -file eplus_sample.txt
wait $EP_PID

# 2. Aggregate samples by top-level EnergyPlus module (SolarShading, HeatBalance, HVAC, Output)
grep -E "EnergyPlus::[A-Za-z0-9_]+::" eplus_sample.txt | head -n 60
```
*(Or open **Xcode Instruments → Time Profiler**, target `/Applications/EnergyPlus-24-2-0/energyplus`, pass `-w ... -d ... expanded.idf`, and inspect the Call Tree grouped by `SolarShading`, `HeatBalanceSurfaceManager`, `ZoneTempPredictorCorrector`, `HVACManager`, `SQLite`.)*

#### On Linux (x86_64 / arm64)
```bash
# Record call-graph CPU samples at 999 Hz
perf record -F 999 -g --call-graph dwarf -- energyplus -w weather.epw -d out_prof expanded.idf

# Terminal top-down/bottom-up breakdown
perf report --stdio -n --sort=dso,symbol | head -n 60

# Optional: generate FlameGraph SVG
perf script | stackcollapse-perf.pl | flamegraph.pl > eplus_flamegraph.svg
```
Look for the dominant namespaces in the profile:
* `EnergyPlus::SolarShading::` (`SHADOW`, `SHDGSS`, `CLIPPOLY`, `DeterminePolygonOverlap`) → exterior shading bottleneck (`PixelCounting` / context simplification target).
* `EnergyPlus::HeatBalanceSurfaceManager::` / `CalcInteriorRadExchange` → interior radiant exchange / surface CTF (`Use Representative Surfaces for Calculations = Yes` / `ZoneGroup` multiplier target).
* `EnergyPlus::HVACManager::` / `SimAirServingZones` / `PlantManager` / `SystemReports` → HVAC timestep ratcheting or plant loop iteration (`ConvergenceLimits`, `PerformancePrecisionTradeoffs`, `HVACTemplate` tuning target).
* `EnergyPlus::SQLite::` / `UpdateDataAndReport` → output I/O bottleneck (`OutputControl:Files`, `Simple` vs `SimpleAndTabular`, fewer hourly variables).

---

## 8. References

1. **Local EnergyPlus 23.1 & 24.2 Installations (directly verified):**
   * `/Applications/EnergyPlus-23-1-0/Energy+.idd` (lines 400–979, 4826, 9536–9670, 10002–10019, 13312–13360, 14425–14470, 18712–18740, 105543–105995)
   * `/Applications/EnergyPlus-24-2-0/Energy+.idd` (lines 401–979, 4832, 9673–9780, 10139, 18849–18877, 107564–107816)
   * `/Applications/EnergyPlus-23-1-0/Documentation/InputOutputReference.pdf` (v23.1: `Building` p. 49–54, `ZoneAirHeatBalanceAlgorithm` p. 58–59, `ShadowCalculation` p. 61–64, `Output:Diagnostics` p. 64–65, `SimulationControl` p. 68–69, `PerformancePrecisionTradeoffs` p. 69–78, `Output:SQLite` p. 2801–2803, `OutputControl:Files` p. 2803, `ReadVarsESO` p. 2809–2811)
   * `/Applications/EnergyPlus-23-1-0/Documentation/EngineeringReference.pdf` (v23.1: `Shading Module` / Polygon Clipping / Pixel Counting / Solar Distribution p. 214–235)
   * `/Applications/EnergyPlus-23-1-0/Documentation/TipsAndTricksUsingEnergyPlus.pdf` (v23.1: `Using Multipliers` §6.10 p. 27–34, `Platforms and Run-Time` §16.1–16.2 p. 73–74)
   * `/Applications/EnergyPlus-23-1-0/Documentation/AuxiliaryPrograms.pdf` (v23.1: `ExpandObjects` p. 171–172, `convertESOMTR` / `ReadVarsESO` p. 176, 232)
   * `/Applications/EnergyPlus-23-1-0/Documentation/OutputDetailsAndExamples.pdf` (v23.1: `Warmup` p. 124–127, `eplusout.end` p. 127, `eplusout.err` p. 128, `_perflog.csv` p. 134, `eplusout.sql` p. 159–160)
   * `/Applications/EnergyPlus-23-1-0/pyenergyplus/{api.py,runtime.py,state.py}` and binary inspection (`strings`/`nm`/`file`/`sample`) of `energyplus-23.1.0`, `energyplus-24.2.0`, `libenergyplusapi.23.1.0.dylib`, and `libenergyplusapi.24.2.0.dylib`.
2. **Hong, T., Buhl, W. F., & Haves, P. (2008).** *EnergyPlus Run Time Analysis*. Lawrence Berkeley National Laboratory, Report LBNL-1311E / CEC-500-2008-094. [https://escholarship.org/uc/item/36h4m5z0](https://escholarship.org/uc/item/36h4m5z0)
3. **Hoover, J., & Dogan, T. (2017).** *Fast and Robust External Solar Shading Calculations using the Pixel Counting Algorithm with Transparency*. Proceedings of Building Simulation 2017 (15th IBPSA Conference). (And foundational method: Jones, N., Greenberg, D., & Pratt, K. 2011, *Journal of Building Performance Simulation*, 5(5), 300–312, cited in EnergyPlus Engineering Reference p. 233).
4. **Big Ladder Software — Penumbra repository:** [https://github.com/bigladder/penumbra](https://github.com/bigladder/penumbra) (BSD-3-Clause C++ / CMake / GLFW GPU pixel-counting library).
5. **EnergyPlus GitHub Repository & Issues/PRs:** [https://github.com/NatLabRockies/EnergyPlus](https://github.com/NatLabRockies/EnergyPlus) (formerly `NREL/EnergyPlus`):
   * Releases v24.1.0, v24.2.0, v25.1.0, v25.2.0 (`github.com/NREL/EnergyPlus/releases`)
   * Issue #9059 (PixelCounting shading surface transmittance schedule behavior)
   * Issue #10299 (`CheckConvexity` non-convex warnings regardless of `ShadowCalculation`)
   * Issue #9997 (Emscripten / OSMesa headless compilation constraints)
   * PR #11258 (Penumbra: mask host floating point traps around GLFW)
   * PR #11774 (Performance: recurring error reporting/summarization)
6. **Windows Dual-GPU / OpenGL Selection Guidance:** NVIDIA Optimus / AMD PowerXpress driver export documentation & Windows Graphics Settings (`Settings > System > Display > Graphics`), referenced alongside EnergyPlus I/O Reference p. 62 multi-GPU note.
