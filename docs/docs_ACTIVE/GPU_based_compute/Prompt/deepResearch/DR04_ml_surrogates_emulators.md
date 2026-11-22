# DR04 — ML Surrogates, Emulators & Foundation Models for Building Energy Simulation

**Feeds:** Phase 4 (optional ML emulator tier)
**Save output to:** `results/DR04_result.md`

---

## PROMPT

You are a machine-learning researcher focused on scientific surrogate modelling for building energy. Produce a critical, source-cited review.

### Context
OpenUBEM is an open-source Python UBEM platform that simulates every building in a district with **EnergyPlus 23.1** (dwelling-level zones, real geometry, 20 m context shading, 10 HVAC families, US and European archetypes, ERA5/TMYx weather). We already have tens of thousands of EnergyPlus runs with structured inputs (archetype, geometry features, envelope, HVAC, climate) and outputs (annual end-uses by fuel, often hourly meters). The project's public promise is "pure physics, zero fitted multipliers", so any ML tier must be **opt-in, clearly labelled, and evaluated against EnergyPlus**.

I want to know whether a GPU-run ML emulator can give 1,000×+ faster screening (scenarios, retrofits, climate futures, uncertainty quantification) at acceptable accuracy.

### Questions
1. **State of the art.** Building energy surrogates and emulators trained on EnergyPlus/OpenStudio outputs:
   - foundation/pretrained models, e.g. NREL **BuildingsBench** (Buildings-900K, trained on EULP / ResStock / ComStock); verify its details, licence, data and model availability, and accuracy on real buildings
   - ResStock/ComStock-based surrogates, DOE/NREL/LBNL/PNNL efforts
   - architectures: gradient boosting on annual features, MLPs, sequence models (LSTM/TCN/Transformer) for hourly loads, graph neural networks over zones/surfaces, neural operators, physics-informed NNs (e.g. NVIDIA PhysicsNeMo/Modulus), hybrid physics-ML (residual learning on top of an RC model)
2. **Accuracy evidence.** Reported errors (annual EUI MAPE, CV(RMSE) hourly, peak error) and especially **out-of-distribution** results: unseen climates, unseen archetypes, unusual geometry, retrofit scenarios. What breaks?
3. **Data needs.** How many E+ runs per archetype/climate are needed? Sampling strategies: Latin hypercube, Sobol, active learning, multi-fidelity (cheap ROM + few E+ runs). Feature engineering from geometry (surface areas per orientation, shading obstruction metrics, zone counts).
4. **Inference throughput.** Published inference speed on GPU vs E+ runtime; batching; model size.
5. **Uncertainty and trust.** Calibrated uncertainty (ensembles, conformal prediction, MC dropout), out-of-distribution detection to fall back to E+, reporting practices.
6. **Open-source tooling.** Repos ready to adapt (with URL, licence, stars, last commit), and how they would plug into a Python/geopandas pipeline.
7. **Recommendation for OpenUBEM.** Fine-tune a foundation model, train our own, or build a hybrid ROM+ML? Include an E+ fallback policy.

### Required output format
- **Executive summary** (≤10 bullets) with a clear recommendation.
- **Table: models/papers**: citation, DOI/URL, architecture, training data, target (annual/hourly), in-distribution error, OOD error, inference speed + hardware.
- **Table: repos/datasets**: name, URL, licence, stars, last commit, usable for us (Y/N, why).
- **Proposed pipeline** for OpenUBEM: data extraction from our E+ outputs → features → model → uncertainty → E+ fallback.
- **Risks**, including how to keep the "pure physics" claim honest.
- **References**.

### Rules
- Cite everything; mark uncited `UNVERIFIED`. Never invent benchmark numbers.
- Separate in-distribution from out-of-distribution results.
- Note licence restrictions on pretrained weights and datasets.
