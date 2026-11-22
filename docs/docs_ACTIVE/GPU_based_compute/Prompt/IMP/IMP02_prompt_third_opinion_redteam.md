# IMP02 — Third opinion (red team): critique our GPU heat-balance build spec

**Purpose:** an adversarial review of our concrete plan. Unlike IMP01, this prompt **includes the spec**. Ask the model to break it, not to agree with it.
**Run with:** Gemini (Deep Research or Pro with search). Run IMP01 first, ideally in a separate session, so the two opinions stay independent.
**How to run:** paste the PROMPT section, then paste the **entire contents** of `../../BUILD_SPEC_gpu_heat_balance_engine.md` where indicated.
**Save output to:** `results/IMP02_result.md`

---

## PROMPT

You are a **hostile but constructive technical reviewer**. You combine two kinds of expertise:
1. **EnergyPlus internals.** You have read `HeatBalanceSurfaceManager.cc`, `ZoneTempPredictorCorrector.cc`, `ConvectionCoefficients.cc`, `HeatBalanceIntRadExchange.cc`, `WindowManager.cc`, `WeatherManager.cc`, `PurchasedAirManager.cc` and `SolarShading.cc` in NREL/EnergyPlus **v23.1.0**.
2. **GPU numerical computing** on Apple Metal/MPS and NVIDIA CUDA.

Below is our build spec for **"gpusim"**: a GPU-native re-implementation of a subset of EnergyPlus 23.1 algorithms, batched across buildings, built on macOS first and Windows/CUDA second. Your job is to **find what is wrong, missing, naive or over-optimistic** before we write code. Assume our team is competent in Python but has not yet read the E+ source.

### Review tasks
1. **Physics completeness for rung S0.** S0 is the one-zone European cell. Go through its object list and tell us every EnergyPlus behaviour we have **not** listed that will move annual heating by more than 0.1%. Consider at least:
   - the order of the inside/outside surface heat balance iteration, its max iterations and convergence criteria;
   - how an OSC with film coefficient 0 is applied: as the outside face temperature directly, and whether it uses the *previous* timestep's zone temperature;
   - the first-timestep and first-day special cases;
   - how warm-up resets or keeps history;
   - convection model limits and floors (minimum h, TARP natural-convection branch by tilt and heat-flow direction);
   - the internal-mass CTF (both faces in the zone?);
   - the window simple glazing model: equivalent layer, inside-film assumption, frame or divider effects;
   - how ventilation air density and cp are evaluated (outdoor or zone conditions? standard density?);
   - humidity effects on cp and ρ even with no latent load;
   - zone air capacitance multiplier;
   - ideal loads' supply-air temperature limits and sizing even with `NoLimit`;
   - what the sizing run changes;
   - how E+ maps hourly EPW to timesteps (interpolation, which hour stamp);
   - the sky temperature formula when horizontal IR is missing;
   - the daylight-saving or holiday flags in our `RunPeriod`.

   Cite the source file and function for each, or mark it `UNVERIFIED`.
2. **Our finding F1** ("windows receive zero solar because the host wall has `Sun_Exposure=NoSun`"). Confirm or refute from the E+ source: do subsurfaces inherit `ExtSolar` from their base surface in v23.1? Is there another explanation for a zero `Zone Windows Total Transmitted Solar Radiation Rate`?
3. **Conformance tolerances (§4).** Are they realistic for an independent re-implementation, or too tight or too loose? What do published re-implementation and validation efforts achieve (ASHRAE 140 inter-program spread, comparative studies)? Suggest revised numbers, with reasons.
4. **Precision (§3.2).** Can float32 on Apple GPUs meet our float32-vs-float64 gate of 0.05% annual and 0.02 K? Identify the most precision-sensitive operations:
   - third-order backward-difference coefficients with a 5-minute step;
   - CTF sums with near-cancelling coefficients;
   - accumulating 105k steps.

   Recommend concrete numerical techniques, or tell us float32 is insufficient and why.
5. **GPU strategy (§3.1).** Critique the three stages: NumPy reference, then PyTorch batched with a Python time loop, then a fused one-thread-per-building kernel. In particular:
   - Will Stage B be hopelessly launch-bound on MPS with about 105k steps per year, making Stage C mandatory?
   - Is `torch.mps.compile_shader` or `mx.fast.metal_kernel` (MLX) usable for a long-running kernel that holds per-thread state? What about GPU watchdog or timeout limits on macOS and Windows (WDDM TDR, about 2 s by default) for a kernel that runs a whole year? How should the year be chunked?
   - Is Taichi a sound single-source choice in late 2026 (maintenance status)?
   - Is PyTorch the right call over JAX/MLX/Warp/WebGPU for "macOS first, then Windows"?
6. **Ladder (§2) and scope.** Is S0→S4 ordered sensibly? Which rung is underestimated? Is "S4 simple DX HVAC without plant loops" realistic, given how E+ unitary systems iterate (`UnitarySystem`, cycling fans, PLR solving with `SolveRoot`)? Where should we stop?
7. **Speed-up hypothesis (§5).** Check our claim that most of E+'s 4 s per one-zone case is overhead (input processing, sizing, warm-up, I/O, start-up), not physics. What fraction is realistic? Remember that E+ 23.1 runs under Rosetta on the Mac. Recompute an expected speed-up range for 10k cases on an M2 Pro GPU and on an RTX-class GPU.
8. **Alternatives we may be dismissing too fast.** Is there a cheaper route to the same outcome? For example:
   - an E+ build stripped of sizing and output;
   - `ExpandObjects` once and reusing the parsed input across thousands of cases, via the EnergyPlus API or `pyenergyplus` state reuse;
   - running E+ natively on Linux many-core;
   - Spawn/Modelica.

   Quantify where possible.
9. **Legal check.** EnergyPlus licence terms for translating its algorithms into a new Apache-2.0/MIT code base: what notice and attribution are required, and are there naming restrictions?

### Required output format
- **Verdict** (≤ 10 lines): proceed / proceed with changes / rethink, and the 3 most important changes.
- **Table A: missing or incorrect physics for S0**: item, E+ source file::function, expected effect on annual heating, fix.
- **F1 ruling** with source evidence.
- **Table B: tolerance recommendations** (ours vs yours, with reasons).
- **Precision analysis**, with a numerical example if possible.
- **GPU strategy critique**, including the watchdog/chunking design.
- **Ladder and scope critique**, **speed-up recomputation**, **alternatives**, **licence notes**.
- **References.**

### Rules
- Be specific and adversarial. Do not praise. Every criticism should come with a fix.
- Cite sources. Mark claims you could not verify in the v23.1.0 source or in documentation as `UNVERIFIED`.
- Separate measured numbers from estimates.

### Our build spec (paste the full file below this line)

<<< PASTE CONTENTS OF BUILD_SPEC_gpu_heat_balance_engine.md HERE >>>
