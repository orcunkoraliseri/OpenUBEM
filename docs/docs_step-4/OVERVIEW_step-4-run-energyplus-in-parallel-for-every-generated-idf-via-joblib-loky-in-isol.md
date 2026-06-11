# OVERVIEW — Step 4 — Per-Building IDF Fleet → Parallel EnergyPlus Execution in Isolated Work Directories
### OpenUBEM Stage 4 / Module 12 — fan out one EnergyPlus 23.1 subprocess per `<osm_id>.idf` via joblib/loky, each in an isolated work_dir, and emit `04_simulation_manifest.parquet`

> **Slug:** `step-4-run-energyplus-in-parallel-for-every-generated-idf-via-joblib-loky-in-isol` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_step-4-run-energyplus-in-parallel-for-every-generated-idf-via-joblib-loky-in-isol.md` &nbsp;•&nbsp; **Generated:** `2026-06-09`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §11.

---

## AIM

Step 4 executes EnergyPlus 23.1 once per Step 3 IDF, in parallel via joblib/loky, each worker writing to its own isolated `<output_dir>/results/<osm_id>/` directory (invariant I2), and records every outcome — success, fatal, timeout, crash, cached, not-attempted — in `04_simulation_manifest.parquet` for Stage 5. It is deliberately a thin layer: zero building physics (all frozen into the IDF at Step 3); its entire job is correct, isolated, resumable, observable process orchestration. Governing invariants: I1 (one IDF per building → embarrassingly parallel), I2 (isolated work_dir — EnergyPlus's fixed output filenames silently corrupt shared dirs), I3 (binary version handshake against the locked IDD), I6 (persistent manifest; resume-aware idempotent re-runs).

---

## PIPELINE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  3A — Manifest Intake & Task Construction (Module 12b: parallel.py)          ║
║  Inputs:    03_idf_manifest.parquet + enriched GDF (osm_id, epw_path only)   ║
║  Operation: filter generation_status=='success'; join epw_path; build plain- ║
║             primitive SimTask tuples — NO GeoDataFrame crosses process bound ║
║  Output:    list[SimTask(osm_id, idf_path, epw_path, work_dir)] + skipped df ║
║  Validation: fail-fast ValueError on any missing epw_path                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3B — Work-Dir Provisioning & Resume Detection (Module 12b)                  ║
║  Inputs:    task list, force_rerun flag                                      ║
║  Operation: one work_dir per osm_id (I2); resume keyed on eplusout.end       ║
║             "EnergyPlus Completed Successfully" + sql exists → success_cached║
║             stale partial dirs deleted and recreated                         ║
║  Output:    fresh tasks vs cached results split                              ║
║  Validation: cached rows never re-executed; idempotent re-invocation (I6)    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3C — EnergyPlus Subprocess Execution (Module 12a: runner.py)                ║
║  Inputs:    SimTask + SIM_TIMEOUT_S (900 s default, ASSUMPTION_DESIGN_DEFAULT)║
║  Operation: energyplus -w epw -d work_dir -x -r idf; -x MANDATORY (HVAC-     ║
║             Template expansion); one-time binary --version handshake vs 23.1 ║
║             IDD (I3); stdout/stderr → openubem_run.log; timeout kill         ║
║  Output:    raw result dict (returncode, wall_clock_s, timed_out)            ║
║  Validation: handshake aborts whole run on version mismatch                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3D — joblib/loky Parallel Fan-Out (Module 12b)                              ║
║  Inputs:    fresh task list, n_jobs (-1 default; SLURM_CPUS_PER_TASK on HPC) ║
║  Operation: Parallel(n_jobs, backend='loky', verbose=10); worker catch-all   ║
║             converts ANY exception → failed_crash dict — never raises        ║
║  Output:    list of raw result dicts (complete even with failures)           ║
║  Validation: parallel efficiency ≥ 0.7 at n_jobs=8 (Boston fixture)          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3E — Outcome Classification & Error Triage (Module 12a)                     ║
║  Inputs:    raw results + eplusout.end + eplusout.err per work_dir           ║
║  Operation: closed 6-token vocabulary: success / success_cached /            ║
║             failed_fatal / failed_timeout / failed_crash /                   ║
║             not_attempted_invalid_idf; n_warnings + n_severe from .end line  ║
║  Output:    classified row per building (flag-don't-drop, N_input rows)      ║
║  Validation: every failure mode diagnostically distinct                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3F — Retention Purge + Manifest Emission (Module 12b)                       ║
║  Inputs:    classified rows, SIM_RETAIN_FILES                                ║
║  Operation: purge .eso/.audit/.bnd/... keep {sql, csv, mtr, err, end,        ║
║             tbl.htm, run log}; failures never purged; write manifest         ║
║  Output:    04_simulation_manifest.parquet (N_input × 11 cols)               ║
║  Validation: 100% success rows have parseable SQL with ReportData rows > 0   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| Input IDFs                        | one per `generation_status=='success'` row | DESIGN §2 |
| Enriched-GDF columns read         | 2 (`osm_id`, `epw_path`) of 57            | DESIGN §2 |
| Task tuple fields                 | 4 plain strings (no GDF to workers)        | DESIGN §3A |
| EnergyPlus version                | 23.1 (binary handshake vs locked IDD, I3)  | DESIGN §3C |
| Mandatory CLI flags               | `-w`, `-d`, `-x` (ExpandObjects), `-r`     | DESIGN §3C |
| Timeout default                   | 900 s (`ASSUMPTION_DESIGN_DEFAULT`)        | DESIGN §3C |
| Status vocabulary                 | 6 closed tokens                            | DESIGN §3E |
| Manifest columns                  | 11                                         | DESIGN §3F |
| Per-building runtime (unmeasured) | ~5 s–3 min (single-zone → 40-zone)         | DESIGN §6, OQ-1 |
| Wall-clock target (Boston 500 m)  | < 30 min at n_jobs=8                       | DESIGN §6 |
| Peak memory                       | ~0.5 GB/worker → ~4 GB at n_jobs=8         | DESIGN §6 |
| Storage per building (post-purge) | ~10–25 MB                                  | DESIGN §6 |
| Storage (Boston fixture)          | ~4–10 GB                                   | DESIGN §6 |
| GPU hours                         | 0 (pure CPU)                               | DESIGN §6 |
| Open Questions                    | 6                                          | DESIGN §7 |

---

## VALIDATION SUMMARY

- `pct_sim_success`: **≥ 95%** of generation-success IDFs reach `success` (Boston 500 m target)
- Success-row integrity: **100%** — `.end` success marker AND `eplusout.sql` opens with `ReportData` count > 0
- Work-dir isolation: **100%** — exactly one `eplusout.sql` per work_dir; I2 regression test against silent overwriting
- Determinism: same-host re-run of any building reproduces **identical** annual heating/cooling SQL totals
- `pct_failed_timeout`: **≤ 1%** — exceeded ⇒ `SIM_TIMEOUT_S` mis-calibrated (OQ-2)
- Parallel efficiency: **≥ 0.7** at n_jobs=8 vs n_jobs=1 (Boston wall-clock)
- Synthetic 10-building fixture: **100%** complete full annual run; adversarial cases (corrupt IDF → `failed_fatal`, missing EPW → `failed_crash`, pre-completed dir → `success_cached`, 1 s timeout → `failed_timeout`) all classify correctly
- True Future Test: not applicable — deterministic execution wrapper; trains nothing. EUI-vs-CBECS generalization is Stage 5 territory.

---

## KEY DECISIONS

> Mirrors DESIGN §9 — same rows, one line each.

| Decision | Rationale (one line) |
|---|---|
| Plain-primitive task tuples — no GeoDataFrame crosses the process boundary (refines spec signature) | Shading already baked into IDFs at Step 3; shipping the GDF to N workers is O(N²) pickling for unread data. |
| Resume via `eplusout.end` success marker + SQL existence; `success_cached` status; stale dirs recreated | Trusts the engine's own atomic completion record; interrupted city-scale runs never repeat completed work (I6). |
| `-x` ExpandObjects mandatory in the subprocess command | Step 3 IDFs carry `HVACTemplate:*` objects the core engine cannot read — without `-x`, 100% of runs go fatal. |
| One-time `energyplus --version` handshake vs locked 23.1 IDD before dispatch | I3 extended to the binary: IDD/engine mismatch yields silently wrong physics, not clean errors. |
| Per-building 900 s timeout (`ASSUMPTION_DESIGN_DEFAULT`) with kill + `failed_timeout` | One pathological building must not stall a worker slot forever; recalibrated after OQ-1 runtime measurement. |
| joblib + loky; worker catch-all → `failed_crash` result — a worker never raises into the fleet | Confirmed system backend (design_state row 32); overnight runs always land a complete manifest. |
| Closed 6-token status vocabulary; flag-don't-drop N-row manifest | Diagnostically distinct failure modes are the triage signal; mirrors Step 1/2 closed-vocabulary discipline. |
| Retention purge (keep sql/csv/mtr/err/end/htm/log; always purge `.eso`; never purge failures) | Halves retained storage at zero information loss; failure debris keeps its diagnostic evidence. |
| `04_simulation_manifest.parquet` (N_input × 11) with per-building `wall_clock_s` + `ep_version` | The I6 intermediate Stage 5 consumes; runtime column self-collects OQ-1 calibration data on every run. |

---

## OPEN QUESTIONS

- **OQ-1** — Measure per-building runtime distribution (`wall_clock_s` by zoning strategy × `num_zones`) on Boston 500 m. *(blocks §6; feeds OQ-2)*
- **OQ-2** — Calibrate `SIM_TIMEOUT_S` (set ~3× p99.5 runtime; confirm timeout rate ≤ 1%). *(blocks §3C, §5.1)*
- **OQ-3** — Multi-node SLURM-array scale-out (spatial chunking, manifest merge, scratch staging) for >50 k buildings. *(Phase-2 §3D extension)*
- **OQ-4** — Keep or drop the `-r`/`eplusout.csv` fallback at city scale (dropping halves retained storage). *(blocks §3F refinement, §6)*
- **OQ-5** — Module 02 undesigned — `epw_path` provenance chain (same blocker as Step 3 OQ-7 / pending Step 2.5). *(blocks full integration test)*
- **OQ-6** — HPC binary deployment: environment module vs Apptainer container on Calcul Québec / Concordia. *(blocks §6 HPC path)*
