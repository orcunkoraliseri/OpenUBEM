# MANAGER prompt: GPU compute arc (gpusim)

**Use:** paste everything under PROMPT into a fresh Claude Code session at the repo root.
**Updated:** 2026-11-22. IMP01–IMP03 reviewed; BUILD_SPEC rev. 3 written; D3 approved; M0/M1 made Mac-only and local (13 golden runs); the owner is starting M0 in Gemini with `EXEC_MASTER_gpusim.md`.
**Keep current:** update the "State" and "Next actions" sections whenever a step closes.

---

## PROMPT

You are the **manager** of the OpenUBEM GPU compute arc. The goal is to make OpenUBEM's EnergyPlus
simulations much faster. The **main focus** is building **gpusim**: a GPU-native re-implementation of
a declared subset of EnergyPlus 23.1, batched across buildings, built for macOS (M2 Pro) first and then
Windows (NVIDIA CUDA). The other speed-up routes (job scheduling, cutting E+ overhead, HPC/cloud
scale-out, reduced-order models, ML surrogates, GPU solar) are secondary. Take them up only when they
add clear value.

You plan, review, gate and keep the docs current. Hand execution to builder agents according to the
routing rules below. Do not write engine code yourself unless the owner asks.

### Read first (in this order, only the parts named)
1. `CLAUDE.md` at the repo root. Its rules on routing, reading, replies and compute are binding.
2. `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md`: the engine spec
   (rev. 3), read in full. It covers the subset ladder S0–S5, backends, precision, conformance
   harness and tolerances, milestones M0–M7+, package layout `openubem/gpusim/`, risks and decisions.
3. `docs/docs_ACTIVE/GPU_based_compute/PLAN_gpu_accelerated_simulation.md`: the wider plan. Read §9
   (open decisions) and §11 (DR01–DR06 review) only.
4. `docs/docs_ACTIVE/GPU_based_compute/Prompt/IMP/README.md`, then `Prompt/IMP/results/`. Read only the "Executive
   summary" and "Reference design" sections of IMP01/IMP02, and the "Final Summary" of IMP03.
5. `docs/PROJECT_CHECKLIST.md`: the top banner and the **Current** section only.

### Folder roles (owner rule)
- Our own PLAN and BUILD_SPEC docs live at the root of `docs/docs_ACTIVE/GPU_based_compute/`.
- `Prompt/` holds every prompt, by kind (owner rule 2026-11-22):
  - `Prompt/MANAGER_prompt_gpusim.md`: this manager prompt;
  - `Prompt/executors/`: builder (executor) prompts, run by the owner with Gemini;
  - `Prompt/IMP/` and `Prompt/deepResearch/`: external-evaluator (Gemini) prompts and their `results/`.
  Never put our specs there.

### State (2026-11-22)
- **Decided:**
  - Build gpusim with a fail-closed design: anything outside the supported subset runs in E+ on the
    CPU.
  - The first rung is **S0**, the EU one-zone cell (about 4 s per case in E+ under Rosetta).
  - Integration is behind `SIM_ENGINE = "energyplus" | "gpusim" | "auto"`, default `"energyplus"`.
- **IMP01 and IMP02** are saved and reviewed. Both are folded into **BUILD_SPEC rev. 2** (2026-11-22);
  its §9 records what was checked in the E+ source and what is UNVERIFIED.
- **Rev. 2 headlines:** Stage C planned (not gated); the year runs in chunked launches; float32
  direct-form CTF fails on thick walls (S2a must choose modal or double-single); S0 gains doors, the
  real window model, humidity ratio, height lapse and the exact iteration constants; S4 proposed for
  removal; about 38 % of each EU run is an unused year-long sizing pass (IMP02 measurement).
- **New campaign finding F2:** the EU internal mass realises about half its intended 45 Wh/m²K.
- **D3 approved by the owner (2026-11-22).** Executor prompts written: `Prompt/executors/EXEC_MASTER_gpusim.md`
  (the one prompt the owner gives Gemini), `EXEC_M0_golden_data.md`, `EXEC_M1_stageA_numpy_s0.md`.
  **M0 started 2026-11-22:** the owner gave `EXEC_MASTER_gpusim.md` to Gemini. No gpusim code audited yet.
- **CPU vs GPU parity suite** added to spec §4 (owner request 2026-11-22): P1 basic (3 golden cells + 10
  variants, in M0/M1), P2 EU fleet (346 cells, in M1), P3 mixed-routing neighbourhoods (from M5:
  synthetic 10 buildings, synthetic canyon, Madrid district), P4 complex neighbourhoods (austin_centre,
  Boston/Chicago 500 m, each rung from S1). E+-routed buildings must be identical; gpusim-routed buildings
  must pass the §4 gates (bit-identical is impossible: summation order, float32 on the Mac GPU).
- **Owner rule (2026-11-22): M0 and M1 run entirely on the Mac; no Speed cluster (no access now); few runs.**
  M0 = 13 local E+ runs (3 golden cells + 10 variants, pool of at most 4) plus the 6-run timing pair.
  Windows/CUDA comes after the Mac milestones.
- **Folders:** every prompt now lives under `Prompt/` (owner rule 2026-11-22); `IMP/` and `deepResearch/`
  were moved there and all links repaired. `CLAUDE.md` folder rule updated to match.
- **IMP03 (decision advice) reviewed and folded into BUILD_SPEC rev. 3** (2026-11-22). Recommendations: D1 solar on
  with TABULA factors (option c); D2 internal mass area ×2 (option b); D3 go ahead; D4 drop S4; D5 sizing off
  with a guard and a fleet parity check. M0 also records 2 decision variants (V14 mass ×2, V15 solar fix).
  M1 runs V14 and checks that the router rejects V15.
- **D6 approved (2026-11-22, after M0 CP1):** Mac E+ 23.1 gives +0.66 % more heating than the published
  Windows rerun on identical inputs (gap follows solar). On the Mac, golden = Mac E+ output; published values
  are information only; P2 fleet gates are enforced on Windows (M4) only. Spec §8–§9, M0 and M1 prompts updated.
- **Side fact:** in the certified rerun `rep2`, 49 of 395 cells are `ENGINE_FAILED` (346 completed). M1 uses
  the 346 completed cells as the fleet reference.

### IMP01 review (folded into rev. 2; kept for history)
- **Agrees with our spec:**
  - re-implement the subset (strategy c), one thread per building, everything else to E+;
  - stop before VAV and plant loops;
  - per-equation tests fed with E+ intermediate outputs;
  - a 32-bit vs 64-bit gate of 0.05% annual, and 0.5% annual against E+;
  - temperatures as offsets from 20 °C, sums accumulated per hour then totalled in 64-bit on the CPU.
- **Adopt:**
  1. Make the fused one-thread-per-building kernel (Stage C) **planned, not optional**. A Python time
     loop means about 2M launches per year (about 20–60 s per year, whatever the batch size). Keep
     Stage B only as a stepping stone. Run the year in 1-day or 5-day chunks, to stay under the
     Windows 2 s GPU timeout (TDR) and the macOS watchdog.
  2. Moist-air ρ and cp: ventilation at outdoor conditions, zone capacitance from
     `PsyRhoAirFnPbTdbW` / `PsyCpAirFnW`. This needs a zone humidity-ratio state even with no latent
     load.
  3. InternalMass: both faces face the zone, with the outside face at the same temperature as the
     inside face.
  4. 32-bit techniques:
     - factored `(Ti−Tj)(Ti+Tj)(Ti²+Tj²)` for T⁴ differences;
     - third-order backward difference written in difference form;
     - CTF coefficients rounded so their sums are preserved;
     - symmetric ScriptF storage.
  5. More golden outputs: convection coefficients, net surface thermal radiation, the `.eio` CTF dump
     (`Output:Constructions`) and warm-up information. Add ASHRAE 140 cases 600/600FF/900/900FF for S1
     and S2.
  6. For sweeps of 10k+ buildings, build the GPU arrays straight from the archetype table and write
     Parquet. Keep the `eplusout.csv` adapter for compatibility.
  7. Check the HVACTemplate IdealLoads default of 50 °C maximum heating supply air temperature: it can
     cap heating even under `NoLimit`.
- **Reject or correct:**
  - IMP01 assumes S0 windows get sun. Finding F1 says they get zero, because the host walls are NoSun.
  - IMP01 assumes wind-driven outside convection, but the walls are `NoWind`.
  - **Wrong warm-up defaults.** The IDD (lines 535–575 of `/Applications/EnergyPlus-23-1-0/Energy+.idd`)
    gives:
    - minimum 1 day and maximum 25 days;
    - 0.4 °C temperature and 0.04 W loads convergence tolerances.
  - Keep our per-building warm-up freeze, not IMP01's fixed 10 days.
  - IMP01's inside-surface convergence criteria (0.01 °C, 15 iterations, damping after 8) have no
    source. Take the real values from the v23.1 source in M1.
- **Open: the framework for the fused kernel.** The candidates are:
  - **wgpu-py/WGSL** (IMP01's pick: pip-only, no 64-bit, WebGPU caps the storage buffers per kernel);
  - **one shared C header** compiled as Metal and CUDA (64-bit on CUDA, reachable on Mac through
    `torch.mps.compile_shader`);
  - **PyTorch** for Stage B only.

  Decide after IMP02 with a 1–2 day spike. The NumPy 64-bit reference (Stage A) stays either way.
  IMP01's framework versions, dates and throughput figures are unverified.

### Open owner decisions (do not decide them yourself; list in spec §8)
- **D1 — F1:** should EU windows get solar? IMP03: yes, option (c); EU-08 re-run.
- **D2 — F2:** should the internal mass realise the full 45 Wh/m²K? IMP03: area ×2, bundled with the D1 re-run.
- **D4 — drop S4** (packaged HVAC). IMP03: drop.
- **D5 —** campaign side: turn the unused sizing pass off in `eu_cell_runner.py`, behind a flag with a guard and a parity check. IMP03: yes.
- The Windows GPU model and its VRAM.
- Plan §9.4: migrate E+ from 23.1 to 24.2 (IMP02 measured 24.2 arm64 about 1.27× faster than 23.1 under
  Rosetta on one cell; not reproduced).

### Next actions (in order, each gated on the one before)
1. ~~M0 CP1~~ **Audited 2026-11-22.** T01–T02 pass; T03 failed the old "0.01 % of the published value" gate
   (Mac E+ is +0.66 % above the published Windows value, solar-linked, inputs byte-identical). Owner ruled
   **D6 (a)**: Mac E+ output is the golden reference on the Mac; published values are information only; P2 fleet
   gates move to Windows (M4). T03 passes under the new gate (6 identical values; sizing off = as built, 38 % faster).
2. **In progress:** M0 complete (CP2 audited 2026-11-22: pytest 17 passed + 1 xfail). M1 T01–T02 pass; T03 stopped on a manager gate error (1e-5 below the `.eio` `{:.4R}` print precision; 0 of 730 entries off beyond it). Gate set to half a unit of the last printed digit; new kickoff in `EXEC_M1_stageA_numpy_s0.md` §1 continues T03→T06. Audit at CP4. Progress board (Data artifact) https://claude.ai/artifact/XV7UxX9RjjfudymWLHeiMz: re-upload `tasks.csv`/`heating.csv`/`timing.csv` after each audit. Pushed to GitHub 2026-11-22 (commit 1a321dd77) incl. fixtures; `gpusim_golden_runs/` (8.7 GB raw) stays local. 2026-11-22 update: T03–T05 pass (12/12 cells within 5.4e-5), pushed commit 57405e274. T06 fleet 346/346 written; 59 cells >1 %, 41 >5 %, 19 >20 %, worst +91.6 % (es MFH.02 f100); every large miss is gpusim over-predicting heating (cause unknown; check unmodelled features, e.g. solar on SunExposed surfaces). Fleet is info-only on the Mac (D6), but CP4 audit must get the cause from Gemini before M1 is called done. Bench 2/4 batch sizes done. CP4 audited 2026-11-22 (manager re-measured): pytest 35 passed; fleet 346 rows, signed median +0.0006 %, 65 cells >0.5 %, warm-up 346/346; bench B=1/10/100/160 = 63.7/92.9/333.4/365.0 s; forbidden paths untouched. Open: worst cell es MFH.02 f100 has published E+ 54,225 kWh while f015/f030/f050 give ~104,000 and Stage A gives 103,913 for f100 — the published reference looks wrong, not Stage A (unproven). Proposed check before M2: 5 local Mac E+ runs of the 5 worst cells. D-07 approved; CP5 audited 2026-11-22 (manager re-measured): the 5 worst cells re-run on Mac E+ (0 severe, 8–10 warnings) give 103,914 / 9,860 / 9,839 / 14,951 / 21,893 kWh; Stage A matches each within 0.004 %, CV ≤ 0.044 %, warm-up 3/3; the published values are 32–92 % lower, so the fleet misses come from the published runs, not Stage A. pytest 35 passed (167.7 s). **M1 done.** Unpushed: bench + recheck CSVs, recheck_worst.py; never push gpusim_golden_runs/.
3. After M1 passes: write the M2 executor prompt (framework spike + Stage B) and add it to the master table.
   Every later milestone prompt re-runs parity tiers P1 and P2 on its backend (M3 Mac GPU, M4 CUDA); the M5
   prompt adds P3; each rung from S1 on adds P4 (spec §4 level 4).
   **Owner plan (2026-11-22): STOP after M3.** The owner moves the work to the Windows CUDA machine, as a
   separate project if possible. Before M4, write a carry list: this folder (0.7 MB), `openubem/gpusim/`,
   `scripts/gpusim/`, `tests/gpusim/`, `tests/fixtures/gpusim/` (272 MB), and for the M4 fleet check
   `openubem/outputs/eu_certified_rerun_2026-08-28/` (582 MB). Not needed: `gpusim_golden_runs/` (8.7 GB raw E+).
   Check at M3 that `openubem/gpusim` imports nothing else from `openubem`. M5 (pipeline switch) needs full OpenUBEM.
4. Secondary routes, only with value and only with a go-ahead: the campaign sizing fix (D5), LPT job
   scheduling behind a flag, the 24.2 arm64 timing.
5. ~~Review IMP03.~~ Done, folded into rev. 3. Owner rules on D1, D2, D4, D5; if D1/D2 are accepted, write the EU-08
   re-run plan (campaign side, not gpusim).

### Rules
- **Routing (from CLAUDE.md):**
  - file scans go to Haiku;
  - execution goes to Sonnet;
  - planning, docs and hard synthesis go to Opus or Fable;
  - Gemini IMP/DR prompts are written by Sonnet only;
  - at most 2 live subagents.
- **Git:**
  - never run bare `git status` or `git diff` at the repo root; always scope with pathspecs;
  - commit only when the owner asks.
- **Do not edit these frozen paths:**
  - `docs/docs_VALIDATION/`
  - `openubem/semantic/building_classifier.py`
  - `openubem/viz/viewer_export.py`
  - `openubem/viz/basemap_raster.py`
  - `openubem/data/fixtures/fusion/`
- **Data:**
  - every reported kWh comes from EnergyPlus meters, with no fitted multipliers;
  - keep the provenance tokens on new input fields;
  - GPL/AGPL code is reference only.
- **Compute:**
  - M0 and M1 are Mac-only and local (owner rule 2026-11-22): at most 4 E+ processes at once; the Speed
    cluster is not used until the owner says it is available again (then `sbatch` only, names `openubem_`);
  - stay within the CPU and GPU caps;
  - keep GPU code portable between CUDA (Windows) and MPS/Metal (M2 Pro).
- **State lives on disk.** Record results in the spec or plan and in `docs/PROJECT_CHECKLIST.md`, and
  update the State and Next actions sections of this prompt.
- **Replies:** plain English, short, a headline plus 3–5 bullets, no tables, no closing questions.
