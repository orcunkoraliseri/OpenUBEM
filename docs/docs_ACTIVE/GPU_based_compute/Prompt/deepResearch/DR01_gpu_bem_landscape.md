# DR01 — Landscape: GPU Acceleration of EnergyPlus and Building Energy Simulation

**Feeds:** whole plan; decides Non-Goal NG1 (no GPU port of the E+ core)
**Save output to:** `results/DR01_result.md`

---

## PROMPT

You are a research analyst specialising in building performance simulation (BPS), urban building energy modelling (UBEM), and high-performance / GPU computing. Produce a rigorous, source-cited landscape report.

### Context
I maintain **OpenUBEM**, an open-source Python UBEM platform. For each building in a district it generates an EnergyPlus IDF (real footprint geometry, dwelling-level thermal zones (up to ~340 zones per building), 20 m context buildings as shading surfaces, HVACTemplate systems expanded with ExpandObjects, 10-minute timestep, annual run with an EPW weather file). It then runs **EnergyPlus 23.1** as one CPU subprocess per building, in parallel with Python `joblib` (or on HPC via SLURM). Districts have 300–1,200 buildings. Measured runtimes: median 3.2 s per building, p99 233 s, max 907 s (Apple M2 Pro). The slowest 10 buildings in a district can take 40% of all CPU time.

I want to know whether GPUs can **substantially** (10×–1000×) speed up this workflow, and how.

### Questions
1. **GPU EnergyPlus.** Has anyone ported EnergyPlus (whole or in part) to GPU (CUDA, HIP, SYCL, Kokkos, OpenACC, OpenMP offload)? Include NREL/DOE efforts, forks, academic papers, theses, hackathons, and EnergyPlus GitHub issues/discussions. What is the official stance of the EnergyPlus developers on GPU/multithreading? What multithreading exists in E+ today (e.g. the `-j/--jobs` CLI flag, `ProgramControl` "Number of Threads Allowed", any OpenMP history), and what is it actually used for?
2. **Native GPU features in EnergyPlus.** Confirm what `ShadowCalculation` → `PixelCounting` (Penumbra library, OpenGL) does, which version introduced it, its GPU requirements, and published speed/accuracy results. Any other GPU-using component?
3. **Other GPU-native or GPU-accelerated building simulation engines.** For example: GPU heat-transfer/RC solvers, Modelica-on-GPU work, differentiable building simulators (JAX/PyTorch), GPU-accelerated Radiance (e.g. Accelerad), GPU CFD for buildings, GPU-accelerated UBEM platforms. For each: what it simulates, how it compares to EnergyPlus fidelity, measured speedup, maturity.
4. **Why GPU ports of whole-building simulators are hard.** Summarise the technical literature: sequential time-stepping, small per-zone linear systems, branchy HVAC control logic, iterative system/plant solution, memory layout. Is the "batch many buildings across GPU threads" (SIMT over buildings) approach documented anywhere for E+-like physics?
5. **Commercial / cloud offerings** claiming accelerated or GPU building simulation (e.g. cloud E+ services, NVIDIA Omniverse / Modulus-PhysicsNeMo building twins, startups). Separate marketing claims from published benchmarks.
6. **Recommendation.** Given my context, rank realistic paths to a large speedup and say which (if any) need a GPU.

### Required output format
- **Executive summary** (≤10 bullets), including a clear yes/no on "is there a usable GPU EnergyPlus today?"
- **Table: GitHub repositories**: name, URL, what it does, language, licence, stars, last commit date, maintained (Y/N), relevance to OpenUBEM (1–5).
- **Table: papers**: citation, DOI/URL, method, hardware, baseline, measured speedup, fidelity vs E+.
- **Table: products/services**: name, URL, claim, evidence quality.
- Sections answering Q1–Q6.
- **Gaps & negative results**: what you searched for and did not find.

### Rules
- Cite every factual claim (URL / DOI / repo + date). Mark anything uncited `UNVERIFIED`.
- Distinguish *measured* vs *claimed* vs *theoretical* speedups, and always state the baseline (single core? whole node?).
- Prefer primary sources (EnergyPlus GitHub, NREL docs, peer-reviewed papers) over blogs.
- Do not invent repository names or numbers. If uncertain, say so.
- Search terms to include (not exhaustive): "EnergyPlus GPU", "EnergyPlus CUDA", "PixelCounting EnergyPlus", "Penumbra bigladder", "GPU building energy simulation", "massively parallel building simulation", "differentiable building energy model", "JAX building thermal model", "GPU urban building energy modeling", "Accelerad", "EnergyPlus multithreading OpenMP".
