# DR05 — Scale-Out (HPC / Cloud) and Tail-Latency Reduction for Large EnergyPlus Fleets

**Feeds:** Phase 1 (LPT scheduling, zone aggregation, SLURM/cloud recipes)
**Save output to:** `results/DR05_result.md`

---

## PROMPT

You are an HPC/cloud engineer experienced with large building-stock simulation campaigns. Produce a practical, source-cited report.

### Context
OpenUBEM (open-source Python UBEM) runs **EnergyPlus 23.1** once per building via `subprocess`, fanned out with `joblib.Parallel(backend="loky")` in manifest order. It respects `SLURM_CPUS_PER_TASK`. Measured on an Apple M2 Pro (12 cores): median 3.2 s per building, p90 9.8 s, p99 233 s, max 907 s. In one 341-building district, the top 10 buildings take 40% of the 9,940 CPU-seconds, and the single slowest run (907 s) bounds the makespan. Slow buildings are tall, many-zone (up to ~340 dwelling zones) models with dense context shading. Each run writes SQLite plus a few retained files; work dirs are purged after success. Campaigns may grow to many districts (10⁴–10⁶ buildings).

### Questions
1. **How do large campaigns do it?** Architecture of NREL ResStock/ComStock (buildstockbatch on AWS/HPC/Eagle/Kestrel), URBANopt, CityBES, City Energy Analyst, SimStock, UBEM.io, Autodesk/other cloud E+ services: job granularity, containers (EnergyPlus Docker images), storage of outputs, failure handling, cost per 10⁶ simulations. Cite docs and papers.
2. **Scheduling and the tail.**
   - Longest-processing-time-first (LPT) scheduling and runtime prediction for E+ jobs. Any published runtime predictors (features: zones, surfaces, shading surfaces, HVAC type)?
   - joblib/loky specifics: dispatch order, `batch_size`, `pre_dispatch`, and how to guarantee LPT order. Alternatives (Dask, Ray, concurrent.futures, GNU parallel, SLURM job arrays, HTCondor) and their overheads for 3-second tasks vs 15-minute tasks.
3. **Making tail buildings cheaper without losing fidelity.** Evidence on zone multipliers / typical-floor modelling, zone merging, geometry simplification, and context-shading simplification (e.g. merging shading surfaces, limiting shading to surfaces that actually obstruct). Reported accuracy impacts on EUI and peak loads.
4. **Per-run overhead.** Cost of process start, ExpandObjects, IDF parsing, sizing runs, ReadVarsESO, disk I/O (SQLite on network filesystems; local scratch/tmpfs best practice).
5. **Hardware economics.** CPU-hours vs cost on cloud (spot/preemptible), ARM (Graviton/Apple Silicon) vs x86 E+ performance, hyperthreading effect on E+ throughput, and memory per run. Is E+ throughput memory-bandwidth or cache bound?
6. **Recommendation** for OpenUBEM: concrete steps ranked by speedup per engineering hour, and a SLURM job-array template idea.

### Required output format
- **Executive summary** with ranked actions (expected gain, effort, risk).
- **Table: large-campaign systems**: name, URL, infrastructure, scale achieved, cost data, open source (Y/N).
- **Table: tail-reduction techniques**: technique, speedup, accuracy impact, source.
- **Scheduling recipe**: how to implement LPT with joblib (or a recommended alternative) in Python, plus a SLURM job-array pattern.
- **References**.

### Rules
- Cite everything; mark uncited `UNVERIFIED`.
- Give the hardware and E+ version behind every runtime/cost figure.
- Prefer official docs (NREL buildstockbatch docs, EnergyPlus docs) and peer-reviewed sources.
