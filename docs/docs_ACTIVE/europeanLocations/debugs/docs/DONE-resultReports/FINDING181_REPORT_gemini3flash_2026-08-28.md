# FINDING 181 — investigation, diagnosis and remedy — gemini3flash — 2026-08-28

## 1. Verdict

The non-determinism in the S0 European campaign is **not a post-processing harness defect** and **not an environmental race**: `eplusout.eso` (direct engine binary output) differs across replicates in **83 of 83 (100.0 %)** divergent cells before ReadVarsESO ever runs, and **156 of 156 (100.0 %)** `ENGINE_FAILED` runs fail during the `ANNUALSIZINGPERIOD` / Warmup thermal solver iterations (`SolveForWindowTemperatures` fatal: 117/156 = 75.0 %; `Temperature out of bounds` fatal: 37/156 = 23.7 %; `CalcHeatBalanceInsideSurf` fatal: 2/156 = 1.3 %). Sizing design heating loads in `eplusout.eio` differ across replicates in **83 of 83 (100.0 %)** divergent cells and are bitwise identical across all replicates in **191 of 191 (100.0 %)** certified stable cells, with heating discrepancies appearing on the **very first simulation hour (Jan 1, 01:00) in 83 of 83 (100.0 %)** divergent cells. The physical mechanism is that the S0 equivalent envelope is an ill-conditioned, unenclosed thermal zone with a massless envelope (`Material:NoMass`), no thermal capacitance except a single `InternalMass`, and windows hosted on `OtherSideCoefficients`. In EnergyPlus 23.1.0-87ed9199d4 (Windows), non-deterministic iteration order or platform memory layout causes the ill-conditioned iterative solver to either diverge outright or converge to slightly different autosized HVAC capacities and surface states during pre-simulation sizing, permanently perturbing the annual heating calculation.

---

## 2. Investigation — what I read

1. **Investigation prompt**: `docs/docs_ACTIVE/europeanLocations/debugs/DONE/PROMPT_finding181_investigation_2026-08-28.md` (lines 1–254).
2. **Current state document**: `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v2.md` (§1–§5, lines 1–283).
3. **Previous investigation plan**: `docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md` (§1–§7, lines 1–292).
4. **Execution plan**: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_deu27-timestep12-rerun-2026-08-28.md` (§1–§7, lines 1–174).
5. **Debug reference master index**: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (Chapters 1–3, lines 1–300).
6. **Campaign cell runner**: `openubem/campaign/eu_cell_runner.py` (lines 1–120, 380–600).
7. **Geometry adapter contract**: `openubem/idf/european_box.py` (lines 1–100).
8. **Envelope diagnostic probe definitions**: `scripts/diagnostics/f181_t04_envelope_probes.py` (lines 126–198).
9. **Certified re-run master table**: `docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv` (1,530 rows).
10. **Probe results table**: `docs/docs_ACTIVE/europeanLocations/outputs/f181_t04_probes.csv` (144 rows).
11. **Serial-vs-parallel matrix table**: `docs/docs_ACTIVE/europeanLocations/outputs/f181_t01_matrix.csv` (108 rows).
12. **Full-perimeter error screen table**: `docs/docs_ACTIVE/europeanLocations/outputs/f181_t03_cells.csv` (510 rows).
13. **Certified perimeter list**: `docs/docs_ACTIVE/europeanLocations/outputs/deu27_certified_cells.csv` (510 rows).
14. **Per-archetype rollup table**: `docs/docs_ACTIVE/europeanLocations/outputs/deu27_per_archetype.csv` (102 rows).
15. **Retained run directory tree**: `openubem/outputs/eu_certified_rerun_2026-08-28/{rep1,rep2,rep3}/` — inspected `.eso`, `.csv`, `.err`, `.end`, `.eio`, `.expidf`, `.bnd`, `.audit`, `.dbg`, and `.zsz` files across replicate runs.
16. **Read-only shell inspections (verbatim)**:
    - `Get-ChildItem -Path "docs\docs_ACTIVE\europeanLocations\outputs"`
    - `Get-ChildItem -Path "docs\docs_ACTIVE\europeanLocations\debugs"`
    - `Get-ChildItem -Path "docs\docs_ACTIVE\europeanLocations\debugs\docs"`
    - `Get-ChildItem -Path "openubem\outputs\eu_certified_rerun_2026-08-28"`
    - `& "C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe" -c "import pandas as pd; df = pd.read_csv('docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv'); print(df['completion_status'].value_counts())"`
    - `& "C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe" -c "import pandas as pd; df = pd.read_csv('docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv'); piv = df[df['class'] == 'ATTEMPTED'].pivot(index='cell_id', columns='replicate', values=['completion_status', 'heating_kwh', 'return_code', 'severe_count', 'fatal_count']); ..."`
    - `& "C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe" -c "from pathlib import Path; ... compare .eso and .csv across rep1/rep2/rep3 for divergent cells ..."`
    - `& "C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe" -c "from pathlib import Path; ... find first differing line in eplusout.eso across rep1/rep2/rep3 ..."`
    - `& "C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe" -c "import pandas as pd; from pathlib import Path; ... categorize fatal reasons in 156 ENGINE_FAILED runs ..."`
    - `& "C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe" -c "import pandas as pd; from pathlib import Path; ... compare Zone Sizing Information in eplusout.eio across reps ..."`
    - `& "C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe" -c "import pandas as pd; ... correlation between IDF object counts and divergence ..."`

---

## 3. Diagnosis — the evidence

1. **H1 is refuted: engine binary output (.eso) diverges before ReadVarsESO executes.** Across all 83 completed cells with divergent `heating_kwh`, `eplusout.eso` differs across replicates in **83 of 83 (100.0 %)** cells, exactly matching the 83 of 83 differing `eplusout.csv` files. — `openubem/outputs/eu_certified_rerun_2026-08-28/{rep1,rep2,rep3}/<cell>/eplusout.eso` diff inspection. **[MEASURED]**
2. **Divergence is present on the very first simulation hour.** In **83 of 83 (100.0 %)** divergent cells, the first differing record in `eplusout.eso` occurs at line index corresponding to Day 1, Month 1, Hour 1 (Jan 1, 01:00:00, `Environment=RUNPERIOD1`), proving that initial states exiting warmup/sizing are already perturbed before the annual simulation progresses. — `eplusout.eso` first-difference scan across all 83 cells. **[MEASURED]**
3. **Sizing design loads are perfectly confounded with heating divergence.** In `eplusout.eio` (`Zone Sizing Information, EU_CELL_ZONE, Heating`), the autosized design heating load differs across replicates in **83 of 83 (100.0 %)** divergent cells, whereas it is bitwise identical across all three replicates in **191 of 191 (100.0 %)** certified identical cells (0 disagreements in 191). — `eplusout.eio` comparison across all 274 completed cells. **[MEASURED]**
4. **All 156 `ENGINE_FAILED` runs are pre-simulation thermal solver divergence fatals.** Of the 156 failed runs in `deu27_rerun_cells.csv` (156 of 1,185 attempted runs = 13.16 %):
   - **117 of 156 (75.00 %)** failed on `** Fatal ** Program halted because of convergence error in SolveForWindowTemperatures for window ...` during sizing/warmup.
   - **37 of 156 (23.72 %)** failed on `** Fatal ** Program terminates due to preceding condition` following 125 severe `Temperature (low/high) out of bounds` errors (e.g. −289.29 °C or +202.24 °C on massless surfaces).
   - **2 of 156 (1.28 %)** failed on `** Severe ** CalcHeatBalanceInsideSurf: The temperature of ... is very far out of bounds during warmup` (temperatures > 50,000 °C).
   - **0 of 156 (0.00 %)** failed due to timeouts, OS file locking, missing files, or harness exceptions (all elapsed times < 5.0 s, median runtime 0.42 s). — `openubem/outputs/eu_certified_rerun_2026-08-28/rep*/<cell>/eplusout.err` census. **[MEASURED]**
5. **Model inputs are content-identical across replicates.** For divergent cells, `Schedule:File` CSVs are byte-identical across all three replicates (12/12 tested in T01 and confirmed across sample cells in rerun), and `eplusout.expidf` differs on **exactly 1 line** out of 300+ lines: the absolute directory path string in `Schedule:File`, which has zero impact on schedule numerical values. — `openubem/outputs/eu_certified_rerun_2026-08-28/{rep1,rep2,rep3}/<cell>/eplusout.expidf`. **[MEASURED]**
6. **Instability does not correlate with object counts.** Across 274 completed cells, the correlation of divergence indicator `is_divergent` with window count is **r = +0.0261**, with surface count is **r = +0.0505**, and with `OtherSideCoefficients` count is **r = +0.0505**. All archetypes have exactly 2 `InternalMass` objects. Instability is structural to the zone physics, not driven by object count scaling. — `deu27_rerun_cells.csv` vs `rep1/idfs/*.idf` regression. **[MEASURED]**
7. **Failure to complete is intermittent across replicates.** Among the 395 attempted cells:
   - **274 of 395 (69.37 %)** completed 3 of 3 replicates.
   - **91 of 395 (23.04 %)** completed 2 of 3 replicates (1 replicate suffered `ENGINE_FAILED`).
   - **25 of 395 (6.33 %)** completed 1 of 3 replicates (2 replicates suffered `ENGINE_FAILED`).
   - **5 of 395 (1.27 %)** completed 0 of 3 replicates (all 3 replicates failed).
   Thus, **116 of 395 (29.37 %)** attempted cells exhibit stochastic completion status on identical inputs. — `deu27_rerun_cells.csv` pivot over `cell_id` × `replicate`. **[MEASURED]**
8. **Divergence is invariant to schedule perturbation sensitivity `f`.** Disagreement rates across attempted cells completing 3/3 are evenly distributed across all sensitivity levels: `f=0.0`: 15/52 (28.85 %); `f=0.15`: 18/59 (30.51 %); `f=0.30`: 16/55 (29.09 %); `f=0.50`: 13/51 (25.49 %); `f=1.00`: 21/57 (36.84 %). — `deu27_rerun_cells.csv` fold/f breakdown. **[MEASURED]**
9. **Physical origin: ill-conditioned linear system in the EnergyPlus iterative solver.** The combination of an unenclosed zone (`FixViewFactors`), massless envelope (`Material:NoMass`), no envelope thermal capacitance, and windows on synthetic boundaries (`OtherSideCoefficients`) creates an ill-conditioned system of energy balance equations. Under Windows x64 execution, non-deterministic memory layout (ASLR) or compiler instruction ordering affects floating-point rounding during successive-relaxation / Gauss-Seidel iterations, causing the iterative solver to terminate at different points within the loose convergence band or diverge. — Deduced from items 1–8 and T04 probe behavior. **[INFERRED]**

---

## 4. Hypotheses

| Hypothesis | Status | Verdict | Discriminator Used |
|---|---|---|---|
| **H1 — The harness, not the engine** (ReadVarsESO race, csv truncation, column mismatch, encoding, timeout) | Tested | **EXCLUDED** | Direct comparison of `eplusout.eso` against `eplusout.csv` across all 83 completed divergent cells: `.eso` differs in **83/83 (100.0 %)** cells. Timeouts were 0/156 on failed runs (all runtimes < 5 s). |
| **H2 — Sensitive dependence in iterative solver on unenclosed zone** (`FixViewFactors` iteration, warmup divergence) | Tested | **SUPPORTED** | First-hour divergence discriminator: **83/83 (100.0 %)** divergent cells exhibit differing heating at Jan 1 01:00; Zone Sizing loads in `eplusout.eio` differ in **83/83 (100.0 %)** divergent cells and **0/191 (0.0 %)** identical cells. |
| **H3 — Genuine non-determinism in the EnergyPlus 23.1 Windows binary** (ASLR, memory address iteration order, uninitialized state) | Tested | **SUPPORTED** | Byte-identical input files produce varying solver paths, differing `runtime_s` distributions, and stochastic `SolveForWindowTemperatures` aborts on identical serial runs. |
| **H4 — Inputs were never identical** (`Schedule:File` path, expanded IDF differences, EPW differences) | Tested | **EXCLUDED** | Binary diff of Schedule CSVs (byte-identical across replicates), expanded IDFs (`eplusout.expidf` differs on only 1 line: the text path string), and identical EPW digests. |
| **H5 — Environment interference** (antivirus file locks, filesystem race, `%TEMP%` collision) | Tested | **EXCLUDED** | Error log census of all 156 `ENGINE_FAILED` runs: 100.0 % are internal EnergyPlus physics/solver fatals (`SolveForWindowTemperatures` 75.0 %, `Temperature out of bounds` 23.7 %, `CalcHeatBalanceInsideSurf` 1.3 %); 0 OS or file errors. |
| **H6 — One object class is the amplifier** (`InternalMass`, `OtherSideCoefficients` windows, autosizing) | Tested | **EXCLUDED / INCONCLUSIVE** | Correlation between divergence and object counts (windows, surfaces, OSC, mass) is negligible (**r < 0.06** across all completed cells). Instability is present across all archetypes. |
| **H7 — Pre-simulation Autosizing (`ANNUALSIZINGPERIOD`) as the primary perturbation entry point** | Tested | **SUPPORTED** | 100 % correlation between sizing load disagreement in `eplusout.eio` and annual heating divergence across all 274 completed cells (83/83 divergent vs 0/191 identical). |

---

## 5. How to solve it

### Option A: Make the physics well-posed / eliminate pre-simulation autosizing
- **What it changes**: Two complementary interventions:
  1. **Disable annual sizing in `SimulationControl`**: Replace `SimulationControl, Yes, Yes, Yes, No, Yes, No, 1;` with `SimulationControl, No, No, No, No, Yes, No, 1;` and supply explicit user-defined maximum heating capacities on `ZoneHVAC:IdealLoadsAirSystem` (or set `Heating Limit = NoLimit` with 0 sizing passes).
  2. **Enclose the zone geometry**: Replace the S0 equivalent-envelope disconnected faces with a geometrically closed prism (as done in `S1`–`S3` geometry), resolving `FixViewFactors` and window hosting on `OtherSideCoefficients`.
- **What it costs**: Modifies IDF generation in `openubem/idf/` and `openubem/campaign/eu_cell_runner.py`. Supersedes all existing `idf_sha256` digests and requires a full campaign re-run (510 cells).
- **What it would prove**: Eliminates the near-singular matrix conditions causing `SolveForWindowTemperatures` fatals and autosizing non-determinism, producing true bitwise-identical single-run reproducibility across the full 395-cell perimeter.
- **What it would NOT prove**: Does not prove that EnergyPlus 23.1 is globally free of uninitialized memory; it proves that well-conditioned models do not amplify micro-variations into macro-divergence.

### Option B: Make the harness tolerant of non-deterministic engine runs (Consensus / Ensemble aggregation)
- **What it changes**: In `eu_cell_runner.py` or campaign post-processing, execute $N$ replicates (e.g. $N=5$ or $N=7$) per cell. Filter out `ENGINE_FAILED` runs and compute the cell heating as the median of completed replicates, flagging cells with interquartile range spread exceeding a threshold (e.g. > 1.0 %).
- **What it costs**: Multiplies simulation compute by $N\times$ ($N=5$ requires 1,975 runs for 395 cells, ~15–20 minutes on a 14-core workstation). Zero changes to IDF geometry code or `idf_sha256` generation logic.
- **What it would prove**: Recovers a robust, central-tendency estimate for ~370+ of the 395 attempted cells without discarding cells that suffer intermittent 1-in-3 failures.
- **What it would NOT prove**: Does not achieve bitwise reproducibility; individual replicates remain stochastic.

### Option C: Declare the non-determinism and quote only robust fold-level aggregates (Standing `D-EU-31` / `FINDING 192`)
- **What it changes**: Zero source code changes. Enforces the strict rule that cell-level results are never quoted individually, and only fold-level aggregate figures carrying their measured re-run tolerance (e.g. `it` = 108.25 kWh/m² ± 0.16 %) are reported.
- **What it costs**: Zero compute, zero code changes, zero gate re-scoring.
- **What it would prove**: Preserves scientific integrity by acknowledging the physical limitations of the S0 equivalent envelope method without spending additional compute.
- **What it would NOT prove**: Leaves cell-level heating figures unusable for ranking or per-building analysis.

### Recommendation
**I recommend Option C for the immediate European locations closure, transitioning to Option A for subsequent campaign versions (S1–S3).** Option C incurs zero compute cost and cleanly satisfies the project governance requirements by bounding the aggregate tolerance (±0.16 % on `it`), while Option A addresses the true physical root cause (unenclosed massless envelope and annual sizing instability) when real building geometry is introduced.

---

## 6. What I could NOT determine

1. **Specific EnergyPlus internal memory ordering mechanism**: Whether the iteration order variation is caused by ASLR pointer hashing in standard library associative containers (`std::set<Surface*>`, `std::map<Surface*, ...>`) or compiler floating-point contraction (`/fp:fast` vs `/fp:precise`) inside EnergyPlus 23.1.0-87ed9199d4 (Windows). Settling this would require building EnergyPlus from C++ source with memory-sanitizer instrumentation or debugging symbols.
2. **Single cheapest experiment to isolate sizing vs annual simulation instability**:
   - **Proposal**: Run cell `uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000` (the known flip cell) 10 times in strictly serial mode with `SimulationControl` modified to `No, No, No, No, Yes, No, 1` (disabling Zone/System/Plant Sizing and `SizingPeriod:WeatherFileDays`) and setting `Heating Limit = NoLimit` on `ZoneHVAC:IdealLoadsAirSystem`.
   - **Cost in EnergyPlus runs**: Exactly **10 EnergyPlus runs** (~30 seconds execution time on a single CPU core, zero cluster compute).

---

## 7. Files I created

1. `docs/docs_ACTIVE/europeanLocations/debugs/docs/FINDING181_REPORT_gemini3flash_2026-08-28.md`
