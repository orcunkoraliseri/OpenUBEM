# Deep Research Prompts — GPU / Accelerated Simulation for OpenUBEM

Parent plan: [`../../PLAN_gpu_accelerated_simulation.md`](../../PLAN_gpu_accelerated_simulation.md)

Each prompt is **self-contained**: paste the whole file (from `## PROMPT` down) into a deep-research tool (Claude Research, ChatGPT Deep Research, Gemini Deep Research, Perplexity, etc.). Save each output as `results/DRxx_result.md` in this folder so it can be reviewed against the plan.

**Status 2026-11-22:** all six results are in `results/` and reviewed in the plan, §11 (spot-checks and corrections).

| ID | File | Question in one line | Priority |
|---|---|---|---|
| DR01 | [DR01_gpu_bem_landscape.md](DR01_gpu_bem_landscape.md) | Does any GPU-accelerated EnergyPlus or BEM engine actually exist, and is any of it usable? | **Run first** |
| DR02 | [DR02_energyplus_runtime_and_pixelcounting.md](DR02_energyplus_runtime_and_pixelcounting.md) | Where does EnergyPlus spend time, and what do PixelCounting (GPU) and other settings buy us? | **Run first** |
| DR03 | [DR03_gpu_batched_reduced_order_physics.md](DR03_gpu_batched_reduced_order_physics.md) | How do we build a GPU-batched RC / ISO 52016 fast tier calibrated to EnergyPlus? | High |
| DR04 | [DR04_ml_surrogates_emulators.md](DR04_ml_surrogates_emulators.md) | Which ML emulators or foundation models can replace E+ for screening, and how accurate are they? | Medium |
| DR05 | [DR05_hpc_cloud_scaleout_and_tail.md](DR05_hpc_cloud_scaleout_and_tail.md) | How do large E+ campaigns (ResStock/ComStock etc.) scale out and handle slow tail buildings? | High |
| DR06 | [DR06_gpu_microclimate_raytracing.md](DR06_gpu_microclimate_raytracing.md) | GPU options for SVF, shadow, MRT and solar ray tracing in urban microclimate. | Medium (side track) |

## Rules every prompt enforces
- Every claim cites a source (URL, DOI, or repo plus commit/release). Uncited claims are labelled `UNVERIFIED`.
- For GitHub repos, report stars, last commit date, licence, language, and whether it is maintained. A repo with no activity for 2+ years is flagged.
- Separate **measured speedups** (with hardware and baseline stated) from **claimed** or **theoretical** ones.
- Say plainly when something does not exist. A negative result is a useful result.
