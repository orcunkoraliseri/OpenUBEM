# Step 4 — Per-Building IDF Fleet → Parallel EnergyPlus Execution in Isolated Work Directories
### OpenUBEM Stage 4 / Module 12: `openubem/simulation/{runner,parallel}.py` — fan out one EnergyPlus 23.1 subprocess per `<output_dir>/idfs/<osm_id>.idf` via joblib/loky, each worker in its own isolated `work_dir`, and emit `04_simulation_manifest.parquet` ready for Stage 5 results parsing

> **Slug:** `step-4-run-energyplus-in-parallel-for-every-generated-idf-via-joblib-loky-in-isol` &nbsp;•&nbsp; **First created:** `2026-06-09` &nbsp;•&nbsp; **Latest revision:** `2026-06-09`
>
> Sections 1–9 are **append-once, edit-never** after first APPROVED verdict. Section 10 (Progress Log) is owned by the downstream `/run` reporter. All `/design` re-run changes are recorded under **Section 11 — Revision Log**.
>
> **Scope rule.** This document covers exactly **one** step of the umbrella pipeline — Step 4 (parallel simulation). The step's *internal* sub-stages (3A–3F) live under §3 Pipeline. Stage 3 (IDF generation) and Stage 5 (results aggregation) are covered in their own per-step DESIGN docs.

---

## 1. Aim

Step 4 executes EnergyPlus 23.1 once per generated IDF, in parallel, and records the outcome of every run in a persistent simulation manifest. Upstream it consumes the Step 3 contract: `<output_dir>/idfs/<osm_id>.idf` (one self-contained IDF per simulation building, invariant **I1**) plus `03_idf_manifest.parquet` (which rows generated successfully) and the per-building `epw_path` column committed by Module 02. Downstream it feeds Step 5 — the results parser (Module 13) reads each building's `eplusout.sql` from its isolated `work_dir` and joins on `osm_id` through `04_simulation_manifest.parquet`. Step 4 is deliberately a *thin* layer: it contains no building-physics logic at all — every physical decision was frozen into the IDF at Step 3 — its entire job is correct, isolated, resumable, observable process orchestration. Skipping it (i.e., running EnergyPlus ad hoc) is how UBEM pipelines silently corrupt results: EnergyPlus writes fixed output filenames (`eplusout.sql`, `eplusout.csv`) into its working directory, so two workers sharing a directory overwrite each other without any error (invariant **I2**; `inputs/aim/OpenUBEM_Technical_Pipeline.md` §11.2). The module decomposition, joblib/loky backend choice, and isolated-`work_dir` requirement follow `inputs/aim/OpenUBEM_Technical_Pipeline.md` §7 (Stage 4) and the confirmed decision in `.claude/design_state.md` (joblib + loky; rejects `multiprocessing.Pool` and Dask).

---

## 2. Inputs

| Artifact | Source | Dtype | Shape | Notes |
|---|---|---|---|---|
| `03_idf_manifest.parquet` | Step 3 (Module 09 emission) | Parquet | (N_input, ≥9 cols) | Binding Step 3 output contract. Step 4 reads `osm_id`, `idf_path`, `generation_status`, `num_zones`, `data_quality_flag`. Only rows with `generation_status == 'success'` are simulated; all other rows are carried through to the Step 4 manifest with status `not_attempted_invalid_idf` (flag-don't-drop). |
| `<output_dir>/idfs/<osm_id>.idf` | Step 3 (Modules 07–11) | EnergyPlus 23.1 IDF (text) | one file per success row, ~50–500 KB | Self-contained (invariant **I1**): full zones, constructions, loads, schedules, IdealAir HVAC, output requests, shading context. Contains `HVACTemplate:*` objects — therefore ExpandObjects **must** run (see §3C). |
| `02_buildings_classified.gpkg` (post-enrichment) | Step 2 → Modules 02/04/05/06/06b | GeoDataFrame | (N, 57) | Step 4 reads exactly **two** columns: `osm_id`, `epw_path`. Nothing else from the 57-column contract is needed — all physics is already inside the IDF. The `epw_path` column is committed by Module 02 (undesigned at time of writing — see §7 OQ-5; same blocker chain as Step 3 OQ-7 / pending Step 2.5). |
| EPW weather file(s) | Module 02 (`epw_manager.py`) | binary `.epw` | one per unique `epw_path` value | Typically one EPW serves the whole neighbourhood; the contract is nonetheless per-building. Step 4 binds IDF + EPW at subprocess launch (`-w` flag) — the IDF itself never embeds the weather file (Step 3 §2). |
| EnergyPlus 23.1 binary | `config.ENERGYPLUS_PATH` (env-overridable `ENERGYPLUS_PATH`) | native executable | — | Open-source subprocess, not a Python package. Binary version is handshake-checked once at startup against the locked IDD version (invariant **I3** extended to the binary side — see §3C). |
| `config.py` | package config | Python module | — | Exposes `ENERGYPLUS_PATH`, `ENERGYPLUS_VERSION` (`"23.1"`), `SIM_TIMEOUT_S` (default 900), `SIM_RETAIN_FILES` (see §3F), `N_JOBS` (default −1 = all cores; on HPC read from `SLURM_CPUS_PER_TASK`). |

---

## 3. Pipeline

Step 4 is a fan-out / fan-in: build the task list (3A–3B), execute each task in an isolated subprocess (3C) dispatched by joblib/loky (3D), classify each outcome (3E), and persist the fan-in as a manifest (3F). The worker function is a pure function of its task tuple — no shared state, no ordering dependency between buildings — which is what makes the stage embarrassingly parallel and resumable.

### 3A — Manifest Intake & Task-List Construction (Module 12b: `openubem/simulation/parallel.py`)

The task builder joins the Step 3 manifest with the enriched GeoDataFrame's `epw_path` column and produces one plain-primitive task tuple per simulable building:

```python
# Module 12b: openubem/simulation/parallel.py
def build_task_list(
    idf_manifest: pd.DataFrame,          # 03_idf_manifest.parquet
    enriched_gdf: gpd.GeoDataFrame,      # only ['osm_id', 'epw_path'] used
    sim_root: Path,                      # <output_dir>/results/
) -> tuple[list[SimTask], pd.DataFrame]:
    epw_map = enriched_gdf[['osm_id', 'epw_path']].set_index('osm_id')['epw_path']
    simulable = idf_manifest[idf_manifest['generation_status'] == 'success']
    skipped   = idf_manifest[idf_manifest['generation_status'] != 'success']

    tasks = [
        SimTask(
            osm_id   = row.osm_id,
            idf_path = str(row.idf_path),
            epw_path = str(epw_map[row.osm_id]),
            work_dir = str(sim_root / row.osm_id),       # invariant I2
        )
        for row in simulable.itertuples()
    ]
    # skipped rows are returned so 3F can emit them with status 'not_attempted_invalid_idf'
    return tasks, skipped
```

`SimTask` is a frozen dataclass of four strings — `osm_id`, `idf_path`, `epw_path`, `work_dir`. Missing `epw_path` for any simulable `osm_id` is a fail-fast `ValueError` before any subprocess launches (a half-run neighbourhood with mixed weather binding is worse than no run).

> **Why this approach:** The task tuple is deliberately **plain primitives only — no GeoDataFrame crosses the process boundary**. The Technical Pipeline §7 sketch passes `buildings_gdf` into `run_single_building` "for shading context", but in the confirmed OpenUBEM architecture the shading context was already baked into each IDF at Step 3 (§3C/3E of the Step 3 DESIGN); passing the GeoDataFrame would force loky to pickle and ship an N-row spatial frame to every one of N workers — O(N²) serialization traffic for data no worker reads. This is a deliberate, documented refinement of the spec signature. The join against `epw_path` happens once, in the parent process, not per worker. **Rejected:** (a) passing `buildings_gdf` per worker (spec's literal signature) — O(N²) pickling for unused data; (b) re-reading the GeoPackage inside each worker — N redundant file opens and a hidden GDAL thread-safety dependency; (c) embedding `epw_path` into the IDF at Step 3 — EnergyPlus binds weather at the command line, not inside the IDF, and Step 3's contract correctly leaves weather binding to Stage 4.

### 3B — Work-Dir Provisioning & Resume Detection (Module 12b)

Each building simulates inside `<output_dir>/results/<osm_id>/` (invariant **I2**). Before dispatch, the task builder checks for a completed prior run so that re-invoking Step 4 is idempotent (invariant **I6** — persistent intermediates make every stage independently re-runnable):

```python
SUCCESS_MARKER = 'EnergyPlus Completed Successfully'

def is_completed(work_dir: Path) -> bool:
    end_file = work_dir / 'eplusout.end'
    sql_file = work_dir / 'eplusout.sql'
    if not (end_file.exists() and sql_file.exists()):
        return False
    return SUCCESS_MARKER in end_file.read_text(errors='replace')
```

Tasks whose `work_dir` already satisfies `is_completed()` are not re-launched; they enter the manifest with status `success_cached` (distinct from fresh `success` so observability dashboards can see what a given invocation actually executed). A `force_rerun: bool = False` keyword on `run_neighbourhood()` deletes and recreates the `work_dir` for every task when `True`. A `work_dir` that exists but is *not* completed (crash debris from a previous interrupted run) is deleted and recreated — stale partial outputs must never survive into a fresh run.

> **Why this approach:** `eplusout.end` is EnergyPlus's own atomic run-outcome record — a one-line file written at termination containing either `EnergyPlus Completed Successfully-- N Warning; M Severe Errors` or `EnergyPlus Terminated--Fatal Error Detected`. Keying resume detection on it (AND on the SQL file's existence) means Step 4 trusts the engine's own completion semantics rather than inferring success from file timestamps or sizes. Resume-awareness matters at urban scale: a 50,000-building run interrupted at 80% must not repeat 40,000 simulations. **Rejected:** (a) keying resume on `eplusout.sql` existence alone — the SQL file is created at run *start* and exists, truncated, after a crash; (b) a separate JSON state file written by Step 4 — duplicates what `eplusout.end` already records and can drift from it; (c) no resume support (always rerun everything) — unacceptable at city scale and violates the spirit of I6.

### 3C — EnergyPlus Subprocess Execution (Module 12a: `openubem/simulation/runner.py`)

One building, one subprocess, one isolated directory:

```python
# Module 12a: openubem/simulation/runner.py
def run_energyplus(task: SimTask, timeout_s: int = config.SIM_TIMEOUT_S) -> dict:
    cmd = [
        str(config.ENERGYPLUS_PATH / 'energyplus'),
        '-w', task.epw_path,
        '-d', task.work_dir,
        '-x',                      # ExpandObjects — REQUIRED, see below
        '-r',                      # readVarsESO → eplusout.csv (Stage-5 documented fallback)
        task.idf_path,
    ]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=task.work_dir, capture_output=True, text=True, timeout=timeout_s,
        )
        wall = time.monotonic() - t0
        (Path(task.work_dir) / 'openubem_run.log').write_text(
            proc.stdout + '\n--- STDERR ---\n' + proc.stderr
        )
        return {'osm_id': task.osm_id, 'returncode': proc.returncode,
                'wall_clock_s': wall, 'timed_out': False}
    except subprocess.TimeoutExpired:
        return {'osm_id': task.osm_id, 'returncode': None,
                'wall_clock_s': timeout_s, 'timed_out': True}
```

Three hard requirements in the command line:

| Flag | Why it is non-negotiable |
|---|---|
| `-x` (ExpandObjects) | Every Step 3 IDF contains `HVACTemplate:Zone:IdealLoadsAirSystem` and `HVACTemplate:Thermostat` objects (Step 3 §3G/3H). The EnergyPlus core engine **cannot read HVACTemplate objects** — they must be expanded into native objects by the ExpandObjects preprocessor, which the CLI runs only when `-x` is passed. Without it, every single simulation terminates fatal with "HVACTemplate objects found". |
| `-d work_dir` | Invariant **I2** — fixed output filenames demand one directory per worker (`inputs/aim/OpenUBEM_Technical_Pipeline.md` §11.2). |
| `-w epw_path` | Weather binding happens at launch; the IDF never embeds the EPW (Step 3 §2 contract). |

Before any task is dispatched, the parent process performs a **one-time binary version handshake**: it runs `energyplus --version`, parses the version string, and asserts it starts with `config.ENERGYPLUS_VERSION` (`"23.1"`). Mismatch aborts the whole run before a single building simulates. This extends invariant **I3** (IDD locked at import — Step 3 §3D) to the binary side: eppy's IDD and the executing engine must agree, or field-order mismatches produce silently wrong physics rather than clean errors.

On `TimeoutExpired`, `subprocess.run` kills the EnergyPlus process; the building is classified `failed_timeout` (§3E). The default `SIM_TIMEOUT_S = 900` (15 min) is a design default tagged `ASSUMPTION_DESIGN_DEFAULT` — roughly 10× the expected worst-case annual IdealAir runtime for a 40-zone building — to be recalibrated once the Boston runtime distribution is measured (§7 OQ-1/OQ-2).

> **Why this approach:** `subprocess.run` with `capture_output` + `timeout` is the entire process-management story — no pexpect, no shell=True, no PID files. EnergyPlus is a well-behaved batch binary: it reads three paths, writes one directory, and exits. Capturing stdout/stderr into `openubem_run.log` inside the `work_dir` keeps diagnosis local to the building that failed (grep one directory, not one giant interleaved log). The `-r` (readVarsESO) flag is retained because the full-system DESIGN's Stage-4 output contract lists `eplusout.csv` in each work dir and Stage 5's parser documents CSV as its fallback when SQL is absent; the storage cost is bounded by the retention policy in §3F. **Rejected:** (a) the EnergyPlus Python API (`pyenergyplus`) — ties the worker to the binary's bundled Python, complicates HPC module-environment deployment, and offers nothing over the CLI for batch runs; (b) `shell=True` string commands — quoting bugs on Windows paths with spaces; (c) omitting `-x` and pre-expanding templates at Step 3 — would force Step 3 to ship the ExpandObjects output (non-portable, version-coupled) instead of clean declarative templates; (d) no timeout — one pathological building (e.g., a degenerate geometry that sends the solver into convergence thrash) stalls a whole worker slot forever.

### 3D — joblib/loky Parallel Fan-Out (Module 12b)

```python
from joblib import Parallel, delayed

def run_neighbourhood(
    idf_manifest: pd.DataFrame,
    enriched_gdf: gpd.GeoDataFrame,
    sim_root: Path,
    n_jobs: int = -1,
    backend: str = 'loky',
    force_rerun: bool = False,
) -> pd.DataFrame:
    _version_handshake()                                   # §3C — fail fast
    tasks, skipped = build_task_list(idf_manifest, enriched_gdf, sim_root)
    fresh, cached = _split_resume(tasks, force_rerun)      # §3B

    raw = Parallel(n_jobs=n_jobs, backend=backend, verbose=10)(
        delayed(_worker)(t) for t in fresh
    )
    return _emit_manifest(raw, cached, skipped, sim_root)  # §3E + §3F
```

`_worker` wraps §3C's `run_energyplus` plus §3E's classification in a top-level `try/except` that converts **any** unhandled exception into a `failed_crash` result dict carrying the traceback string — a worker never raises into joblib, so one broken building can never abort the fleet. On HPC (Calcul Québec / Concordia), `n_jobs` defaults to `int(os.environ.get('SLURM_CPUS_PER_TASK', 0)) or -1`, so the same code runs unchanged inside a single SLURM allocation; multi-node scale-out via SLURM array jobs chunking N buildings per task is the documented Phase-2 path (§7 OQ-3), matching the spatial-chunking pattern in `inputs/reports/Open Source Urban Building Energy Modeling-Architecture.md`.

> **Why this approach:** joblib + loky is the confirmed architectural decision (`.claude/design_state.md`, full-system DESIGN §9.4): loky is process-based (bypasses the GIL — irrelevant here since the work is in a subprocess anyway, but it also means worker isolation), survives and re-spawns crashed workers, and is the eppy-community standard (eppy's own `runIDFs` uses joblib per `inputs/papers/besos-documentation-besos-documentation.md`). Each joblib worker's payload is trivial — launch a subprocess, wait, classify — so worker count maps 1:1 onto how many EnergyPlus processes run concurrently, and `n_jobs=-1` saturates the machine with EnergyPlus, not with Python. The catch-all-to-result-dict pattern in `_worker` is what makes a 50,000-building overnight run land a complete manifest instead of a stack trace at building 31,407. **Rejected:** (a) `multiprocessing.Pool` — fragile error handling, deadlock-prone on worker death, no progress reporting (rejected at system level, design_state row 32); (b) Dask — heavyweight scheduler for a payload of four strings (full-system DESIGN §9.4); (c) `concurrent.futures.ThreadPoolExecutor` — viable since the GIL releases during `subprocess.run`, but loses loky's crash-resilience and diverges from the confirmed system-level decision for no benefit; (d) MPI — HPC-only, kills the laptop story.

### 3E — Outcome Classification & Error Triage (Module 12a)

Each completed (or killed) subprocess is classified into a **closed status vocabulary** by inspecting, in order: the timeout flag, the process return code, `eplusout.end`, and `eplusout.err`:

| Status token | Condition (first match wins) | Manifest fields populated |
|---|---|---|
| `failed_timeout` | `timed_out == True` | `error_summary = 'killed at {SIM_TIMEOUT_S}s'` |
| `failed_crash` | no `eplusout.end` written (process died before EnergyPlus could terminate cleanly: segfault, OOM-kill, missing EPW, unreadable IDF), or worker exception (§3D catch-all) | `error_summary` = last 500 chars of stderr / traceback |
| `failed_fatal` | `eplusout.end` contains `'EnergyPlus Terminated--Fatal Error Detected'` | `error_summary` = first `**  Fatal  **` line from `eplusout.err`; `n_warnings`, `n_severe` parsed |
| `success` | `eplusout.end` contains `'EnergyPlus Completed Successfully'` AND `eplusout.sql` exists | `n_warnings`, `n_severe` parsed from the `.end` line |
| `success_cached` | resume hit (§3B) — not executed this invocation | counts re-parsed from existing `.end` |
| `not_attempted_invalid_idf` | upstream `generation_status != 'success'` (§3A) | `error_summary` = Step 3's `generation_status` token |

Warning/severe counts are parsed from the `.end` summary line (`...-- 12 Warning; 0 Severe Errors...`) — not by line-counting `eplusout.err` — because the `.end` counts are the engine's own authoritative tally. A run that completes successfully but with `n_severe > 0` remains `success` (EnergyPlus severe-but-recoverable conditions, e.g. minor convergence warnings, still produce valid annual results) but the count is surfaced so Stage 5 / validation dashboards can filter or down-weight.

> **Why this approach:** A closed status vocabulary mirrors the discipline established at Step 1 (`data_quality_flag` closed vocabulary, design_state row 50) and Step 2 (`archetype_confidence` three-tier): downstream code switches on exact tokens, never on substring heuristics. The four failure modes are *diagnostically distinct* — a timeout points at geometry/zone-count pathology, a crash points at environment/deployment problems, a fatal points at IDF content errors (i.e., a Step 3 bug), and that distinction is exactly what a maintainer triaging a 5%-failure overnight run needs first. Flag-don't-drop (every input building appears in the manifest regardless of outcome) preserves the Step 1 policy (design_state row 50) through the simulation stage. **Rejected:** (a) boolean `success`/`failed` (spec sketch) — collapses the triage signal; (b) raising on first failure — one bad building must never kill an urban-scale run; (c) free-text status — defeats exact-token filtering in Stage 5 and CI.

### 3F — Retention Purge & Simulation Manifest Emission (Module 12b)

EnergyPlus writes ~15 files per run; most are redundant once the SQL exists. After classification, each `work_dir` is purged down to the retained set:

```python
SIM_RETAIN_FILES = {
    'eplusout.sql',    # primary Stage-5 input (Output:SQLite SimpleAndTabular)
    'eplusout.csv',    # Stage-5 documented fallback (readVarsESO output)
    'eplusout.mtr',    # RunPeriod facility meters (Output:Meter:MeterFileOnly — Step 3 §3I)
    'eplusout.err',    # diagnosis
    'eplusout.end',    # resume marker (§3B) — never delete
    'eplustbl.htm',    # ABUPS annual summary — Stage-5 unit-conversion cross-check
    'openubem_run.log' # captured stdout/stderr (§3C)
}
# Purged: eplusout.eso (largest file, fully redundant once .csv/.sql exist),
#         .audit, .bnd, .shd, .mtd, .rdd, .mdd, .eio, .dxf, .svg, expanded.idf, ...
```

The purge runs *after* readVarsESO has produced `eplusout.csv` (the `.eso` is its input) and never runs on `failed_*` directories — failure debris is kept intact for diagnosis until the building is rerun. The retained set is configurable via `config.SIM_RETAIN_FILES` for users who want everything kept.

The fan-in then writes **`04_simulation_manifest.parquet`** — one row per Step 3 manifest row (N_input rows, statuses included):

| Column | Dtype | Notes |
|---|---|---|
| `osm_id` | str | join key (Step 1 contract) |
| `idf_path` | str | from 03 manifest |
| `work_dir` | str | `<output_dir>/results/<osm_id>` |
| `sql_path` | str | `<work_dir>/eplusout.sql`; empty string for non-success rows |
| `status` | str | closed 6-token vocabulary (§3E) |
| `n_warnings` | Int64 nullable | from `eplusout.end`; NaN for crash/timeout/not-attempted |
| `n_severe` | Int64 nullable | same |
| `wall_clock_s` | float | per-building runtime; feeds OQ-1 runtime-distribution measurement |
| `ep_version` | str | from the startup handshake (`"23.1.0"`); constant per run, stored per row for provenance |
| `epw_path` | str | weather file actually bound at launch |
| `error_summary` | str | empty for success rows |

> **Why this approach:** The `.eso` file is the single largest output (hourly ESO for 11 variables × many zones easily exceeds the SQL) and is 100% redundant once readVarsESO has converted it — purging it cuts per-building retained storage roughly in half with zero information loss, which is the difference between a city-scale run fitting on scratch storage or not (§6). The manifest is the **I6** persistent intermediate for this stage: Stage 5 never globs directories — it reads the manifest, filters `status.isin({'success', 'success_cached'})`, and follows `sql_path`. Recording `wall_clock_s` per building turns every production run into the runtime-distribution measurement that OQ-1/OQ-2 need — the calibration data collects itself. **Rejected:** (a) keeping all EnergyPlus outputs — ~2× retained storage for files nothing reads; (b) deleting failure debris — destroys exactly the evidence needed to fix the failure; (c) a JSON-lines log instead of Parquet — loses dtype fidelity and cheap columnar filtering at 10⁵–10⁶ rows; (d) one combined manifest that overwrites `03_idf_manifest.parquet` — violates I6 (each stage owns its own intermediate; Step 3's record must survive Step 4 re-runs untouched).

---

## 4. Outputs

| Artifact | Filename | Format | Shape | Consumed by |
|---|---|---|---|---|
| Simulation manifest | `<output_dir>/04_simulation_manifest.parquet` | Parquet | (N_input, 11) | Step 5 / Module 13 (filters `status ∈ {success, success_cached}`, follows `sql_path`); validation dashboards (failure triage, runtime distribution). |
| Per-building work dirs | `<output_dir>/results/<osm_id>/` | directory of retained files (§3F) | one per simulated building | Step 5 / Module 13 (`eplusout.sql` primary, `eplusout.csv` fallback, `eplustbl.htm` for the ABUPS cross-check, `eplusout.mtr` for facility meters); humans (`eplusout.err`, `openubem_run.log` for diagnosis). |
| Run log | `<output_dir>/results/<osm_id>/openubem_run.log` | text | one per executed building | failure diagnosis only — observability artifact, non-binding. |

Step 4 does **not** modify `03_idf_manifest.parquet`, the IDF files, or any upstream GeoPackage (invariant **I6** — each stage's intermediates are immutable to later stages).

---

## 5. Validation

### 5.1 Metrics and acceptance thresholds

| Metric | Threshold | Rationale (cite source) |
|---|---|---|
| `pct_sim_success` | ≥ 95% of `generation_status == 'success'` IDFs reach `success` (Boston 500 m fixture target) | Detects systemic IDF-content or environment failures; mirrors Step 3's ≥95% generation target (`inputs/aim/OpenUBEM_Technical_Pipeline.md` §7) |
| Success-row integrity | 100% of `success` rows: `eplusout.end` contains the success marker AND `eplusout.sql` opens under `sqlite3` with `ReportData` row count > 0 | The manifest's `success` token is a promise to Stage 5; this is the promise check |
| Work-dir isolation | 100%: every `work_dir` contains exactly one `eplusout.sql`; no file in any `work_dir` is newer than the manifest write for a different `osm_id` | Invariant **I2** regression test — the failure mode is silent result overwriting (`inputs/aim/OpenUBEM_Technical_Pipeline.md` §11.2) |
| Determinism | Re-running one building on the same host/binary reproduces identical annual heating/cooling totals from the SQL | EnergyPlus is deterministic given identical IDF + EPW + binary; any drift indicates work-dir contamination or version skew |
| `pct_failed_timeout` | ≤ 1% (Boston fixture) | If exceeded, `SIM_TIMEOUT_S` is mis-calibrated for the zone-count distribution (→ OQ-2) |
| Parallel efficiency | ≥ 0.7 at `n_jobs=8` vs `n_jobs=1` (Boston fixture wall-clock ratio / 8) | Embarrassingly parallel workload; below 0.7 indicates I/O contention or worker-dispatch overhead worth fixing |
| Synthetic-fixture dry run | 100% of the Step 3 synthetic 10-building fixture complete a full annual run | Confirms `-x` expansion, version handshake, timeout path, and classification logic end-to-end without OSM/network |

### 5.2 Test data and holdout strategy

- **Synthetic smoke-test fixture** — the 10 IDFs generated by Step 3's `tests/fixtures/synthetic_10_buildings.py` (all zoning strategies × archetype families × simplification tiers), simulated end-to-end annually with a bundled EPW. Adds Step 4-specific cases: one deliberately corrupted IDF (must classify `failed_fatal`, not crash the fleet), one task pointed at a missing EPW (must classify `failed_crash`), one pre-completed `work_dir` (must classify `success_cached` and not re-execute), and a `SIM_TIMEOUT_S=1` run (must classify `failed_timeout` and kill the process). Requires the EnergyPlus 23.1 binary; marked as an integration-tier test, skipped in binary-less CI.
- **Boston Downtown 500 m integration fixture** — the ~400-building cached GeoPackage from Steps 1–3, run at `n_jobs ∈ {1, 8}` to measure `pct_sim_success`, the runtime distribution (feeds OQ-1), timeout rate, and parallel efficiency.
- Holdout regime: unchanged from Step 3 — Boston is fully held out from any Module 06b training set. Step 4 itself trains nothing.

### 5.3 True Future Test (only if a forecast or generalization claim is made)

Not applicable — Step 4 is a deterministic execution wrapper around a deterministic engine; it trains no model and makes no forecast. The only implicit generalization claim is operational: the orchestration (resume, timeout, classification) behaves identically on unseen neighbourhoods of any size, which is tested by the synthetic fixture's adversarial cases (§5.2) rather than by a holdout. The downstream claim that the simulated EUIs match CBECS distributions on held-out Boston is Stage 5 validation territory and is documented in the Step 5 DESIGN.

---

## 6. Compute

| Resource | Estimate | Source of estimate |
|---|---|---|
| GPU hours (Calcul Québec / Concordia HPC) | 0 | EnergyPlus is pure CPU; HPC GPU time remains reserved for the umbrella project's ML stages |
| CPU | `n_jobs` cores, one EnergyPlus process per core | §3D; `n_jobs=-1` default, `SLURM_CPUS_PER_TASK` on HPC |
| Per-building runtime | ~5–15 s (single-zone IdealAir) to ~1–3 min (20–40-zone high-rise) — **unmeasured, see OQ-1** | annual 8760 h, 6 timesteps/h, IdealAir (no plant iteration); to be measured from `wall_clock_s` on the Boston fixture |
| Wall-clock target (Boston 500 m, ~400 buildings) | < 30 min at `n_jobs=8` | ~400 × ~30 s mean ÷ 8 cores ≈ 25 min; confirms once OQ-1 lands |
| Peak memory | ~0.5 GB per EnergyPlus worker → ~4 GB at `n_jobs=8` | EnergyPlus annual-run RSS for ≤40-zone IdealAir models; parent process holds only the task list |
| Storage per building (retained set, post-purge) | ~10–25 MB (`eplusout.sql` + `.csv` dominate: 11 hourly variables × zones × 8760) | §3F retention policy; pre-purge roughly 2× |
| Storage (Boston fixture) | ~4–10 GB | 400 × 10–25 MB |
| Storage (5 M-building city) | ~50–125 TB retained | linear extrapolation — the reason the §3F purge policy and HPC scratch staging exist |

The dominant cost driver is per-building EnergyPlus runtime, which scales with zone count — this is why Step 3's §3B zoning rule table routes TallBuildings to `one_zone_per_floor` rather than `perimeter_core`. The budget doubles if the timeout distribution forces `SIM_TIMEOUT_S` upward (long-tail buildings holding worker slots), or if the `.csv` fallback retention is kept at city scale (→ OQ-4: dropping `-r`/`.csv` halves retained storage).

---

## 7. Open Questions

- [ ] **OQ-1** — Measure the per-building EnergyPlus runtime distribution (`wall_clock_s` percentiles by zoning strategy and `num_zones`) on the Boston 500 m fixture. Every §6 runtime/wall-clock figure is currently an engineering estimate, not a measurement. *(blocks §6; feeds OQ-2)*
- [ ] **OQ-2** — Calibrate `SIM_TIMEOUT_S`. The 900 s default is tagged `ASSUMPTION_DESIGN_DEFAULT`; once OQ-1 lands, set it to ~3× the p99.5 runtime and confirm `pct_failed_timeout ≤ 1%`. *(blocks §3C, §5.1)*
- [ ] **OQ-3** — Multi-node HPC scale-out design: SLURM array jobs chunking N buildings per task (spatial chunking per `inputs/reports/Open Source Urban Building Energy Modeling-Architecture.md`), shared-filesystem manifest merging, and scratch-storage staging. Phase 1 is single-node joblib; this is the Phase-2 path for >50 k-building cities. *(blocks Phase-2 §3D extension; does not block Phase 1)*
- [ ] **OQ-4** — Decide whether the `-r`/`eplusout.csv` fallback is worth its storage at city scale. Phase 1 keeps it (full-system Stage-4 contract lists `.csv`; Stage 5 documents CSV fallback); if Stage 5's SQL-primary path proves 100% reliable on the Boston fixture, dropping `-r` halves retained storage. *(blocks §3F refinement, §6)*
- [ ] **OQ-5** — Module 02 (`acquisition/climate_zone.py` + `epw_manager.py`) is undesigned; the `epw_path` column Step 4 binds at launch comes from it. Same blocker chain as Step 3 OQ-7 (pending Step 2.5 design session). Synthetic-fixture tests are not blocked (bundled EPW). *(blocks full integration test)*
- [ ] **OQ-6** — EnergyPlus binary deployment on Calcul Québec / Concordia HPC: environment module (`module load energyplus/23.1`) vs Apptainer/Singularity container. Affects the §3C handshake path resolution and reproducibility documentation. *(blocks §6 HPC path; does not block workstation Phase 1)*

---

## 8. References

**`inputs/aim/`** — project charter and pipeline blueprint
- `inputs/aim/OpenUBEM_Technical_Pipeline.md` — §7 (Stage 4 specification: Module 12 decomposition, `run_neighbourhood`/`run_single_building` signatures, joblib/loky, `energyplus -w -d -r` command sketch), §11.2 (parallel output isolation — invariant I2), §11.3 (IDD/binary version matching — invariant I3).
- `inputs/aim/OpenUBEM_Aim_Document.md` — five-stage pipeline framing; open-source subprocess commitment (EnergyPlus is not a Python dependency); Phase-1 US scope.

**`inputs/papers/`** — technical references for libraries and methods
- `inputs/papers/besos-documentation-besos-documentation.md` — eppy/BESOS parallel-execution context; `runIDFs`-style joblib dispatch as the eppy-community standard; anchors §3D backend choice.
- `inputs/papers/welcome-to-eppy-s-documentation-eppy-0-5-69-documentation.md` — eppy runner semantics and IDD-binding behaviour; anchors the §3C version-handshake rationale.
- `inputs/papers/urban-buildings-energy-consumption-estimation-using-hpc-a-case-study-of-bologna.md` — HPC-scale UBEM execution case study; anchors §6 city-scale storage/runtime extrapolation and §7 OQ-3 (chunked scale-out).
- `inputs/papers/python-opens-up-new-applications-for-energyplus-building-energy-simulation-nlr.md` — Python-driven EnergyPlus batch execution context.

**`inputs/reports/`** — UBEM methodology context
- `inputs/reports/Open Source Urban Building Energy Modeling-Architecture.md` — joblib/loky parallelism patterns, SLURM adaptation (`SLURM_CPUS_PER_TASK`), spatial-chunking pattern for multi-node scale-out; anchors §3D HPC path and §7 OQ-3.
- `inputs/reports/Open Source Urban Building Energy Modeling - General.md` — comparative tool analysis; confirms per-building-process isolation as the differentiator vs combined-model tools (UMI, CityBES).

**Prior-step DESIGN docs (binding upstream contracts)**
- `outputs/2026-05-07_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod/DESIGN_step-3-...md` — `03_idf_manifest.parquet` schema (§4), IDF self-containment (§3), HVACTemplate usage (§3G/3H → the §3C `-x` requirement), Output:SQLite + MeterFileOnly requests (§3I → the §3F retained set).

**External anchors (cited via inputs only — no fabricated DOIs)**
- Iseri et al. (2025), *Energy & Buildings* 337, 115620 (`inputs/papers/1-s2-0-s0378778825003500-main-pdf.md`) — per-building parallel simulation methodology that OpenUBEM generalizes.
- EnergyPlus 23.1 command-line interface — `-w`, `-d`, `-x`, `-r` flags; `eplusout.end` termination semantics; fixed output filenames (referenced via Technical Pipeline §7/§11).

---

## 9. Key Decisions Summary

| # | Decision | Sub-stage | Rationale (one line) | Alternatives rejected |
|---|---|---|---|---|
| 1 | Plain-primitive task tuples (`osm_id`, `idf_path`, `epw_path`, `work_dir`) — no GeoDataFrame crosses the process boundary | 3A | Shading context is already baked into each IDF at Step 3; shipping the GDF to N workers is O(N²) pickling for unread data — documented refinement of the spec signature | Spec-literal `buildings_gdf` per worker; per-worker GeoPackage re-read; embedding EPW in the IDF. |
| 2 | Resume-aware idempotency keyed on `eplusout.end` success marker + SQL existence; `success_cached` status; stale partial dirs deleted | 3B | Trusts the engine's own atomic completion record; a city-scale run interrupted at 80% must not repeat the 80% (invariant I6) | SQL-existence-only check (file exists truncated after crash); separate Step 4 state file (drift risk); no resume. |
| 3 | `-x` (ExpandObjects) mandatory in the subprocess command | 3C | Step 3 IDFs contain `HVACTemplate:*` objects which the core engine cannot read — without `-x`, 100% of runs terminate fatal | Pre-expanding templates at Step 3 (non-portable, version-coupled); native-object HVAC authoring (re-litigates Step 3's IdealAir decision). |
| 4 | One-time binary version handshake (`energyplus --version` must match the locked 23.1 IDD) before any dispatch | 3C | Extends invariant I3 to the binary: IDD/engine mismatch produces silently wrong physics, not clean errors — fail the whole run fast instead | Per-building version checks (redundant); trusting the deployment environment (the exact failure I3 exists to prevent). |
| 5 | Per-building `SIM_TIMEOUT_S` (default 900 s, `ASSUMPTION_DESIGN_DEFAULT`) with kill + `failed_timeout` classification | 3C | One pathological building must not stall a worker slot forever; tagged as a design default pending OQ-1/OQ-2 runtime calibration | No timeout (fleet stalls); aggressive low timeout (kills legitimate high-rise runs). |
| 6 | joblib + loky fan-out; worker catch-all converts any exception to a `failed_crash` result — a worker never raises into the fleet | 3D | Confirmed system-level backend (design_state row 32); crash-resilient overnight runs that always land a complete manifest | `multiprocessing.Pool` (deadlock-prone); Dask (scheduler overhead); ThreadPoolExecutor (loses loky crash-resilience); MPI (HPC-only). |
| 7 | Closed 6-token status vocabulary (`success`, `success_cached`, `failed_fatal`, `failed_timeout`, `failed_crash`, `not_attempted_invalid_idf`); flag-don't-drop N-row manifest | 3E | Diagnostically distinct failure modes are the triage signal; mirrors Step 1/2 closed-vocabulary discipline; every building stays visible to Stage 5 | Boolean success/failed (collapses triage); raise-on-first-failure; free-text status. |
| 8 | Retention purge to a fixed retained set (`sql`, `csv`, `mtr`, `err`, `end`, `tbl.htm`, run log); `.eso` always purged; failure debris never purged | 3F | `.eso` is the largest file and fully redundant post-readVars — purge halves retained storage at zero information loss; failures keep their evidence | Keep-everything (~2× storage); purge failures too (destroys diagnosis evidence). |
| 9 | `04_simulation_manifest.parquet` (N_input rows × 11 cols) incl. per-building `wall_clock_s` and `ep_version` | 3F | The I6 persistent intermediate Stage 5 consumes; runtime column makes every production run self-collecting OQ-1 calibration data | JSON-lines log (no dtypes, slow filtering); overwriting the Step 3 manifest (violates I6). |

---

## 10. Progress Log *(populated by downstream `/run` reporter — leave empty here)*

<!-- The downstream execution project's reporter agent appends `### Session: <date> | Loop: <N>` blocks under this header after each /run cycle. NEITHER the architect NOR the documenter writes here. -->

---

## 11. Revision Log *(populated by DOCUMENTER on /design re-runs only — EMPTY on first creation)*

<!-- Append-only. DOCUMENTER inserts a new block on each /design re-run.

On MODE=new this section MUST contain only this comment block — no `### Session:` block. The first revision block is written on the first MODE=update run.

### Session: <YYYY-MM-DD> | Pass: <final-pass>
**Trigger:** <one-line: new evidence, change request, retired decision>
**Inputs added since last session:** <bullets — filenames>
**Changes:**
- §<N>: <delta>
**New Decisions:** <bullets, also propagated to .claude/design_state.md>
**Retired Decisions:** <bullets — moved to design_state.md ## Retired Decisions, with reason>
**OVERVIEW regenerated:** yes
**GRAPHICAL_ABSTRACT regenerated:** yes | no — no material architecture change

-->

### Session: 2026-06-09 | Pass: n/a (direct authoring cross-reference)

**Trigger:** Step 2.1 designed (direct-authoring session, 2026-06-09) — the Module-02 dependency named in this document is now closed on the design side.

**Changes:** none to §1–§9 (frozen). Cross-reference note only:
- **OQ-5 RESOLVED** — Module 02 designed as **Step 2.1** (`outputs/2026-06-09_step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build/`). The `epw_path` column Step 4 joins once in the parent process and binds at launch (`-w`) points at a **validated run-local copy** under `<output_dir>/weather/` — atomic-cached (`.tmp → os.replace`), gated on LOCATION-header parse + 8760|8784 data rows + ≤ 10 km header–index sanity, one EPW per run in Phase 1. Run-dir self-containment means the Step 4 HPC scratch-staging pattern (§6) ships weather with the job by construction. The full-integration-test blocker chain shared with Step 3 OQ-7 is closed on the design side.

**Decisions retired:** none.
**OVERVIEW regenerated:** no — §1–§9 unchanged.
**GRAPHICAL_ABSTRACT regenerated:** no — no material architecture change.
