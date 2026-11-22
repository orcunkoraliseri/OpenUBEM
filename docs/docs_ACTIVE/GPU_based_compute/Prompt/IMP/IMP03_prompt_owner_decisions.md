# IMP03 — Owner decisions: evidence-based advice on D1–D5

**Purpose:** the owner must take five decisions. Gemini gives a **recommendation with evidence** on each. The owner decides. Gemini only advises.
**Run with:** Gemini (Pro with search), or an agentic session with repo access. Run after the spec is at rev. 2. Use a new session, separate from IMP01 and IMP02.
**How to run:** paste the PROMPT section as it is. The context is inside. If the session has repo access, it should also read the paths in "Where to look".
**Save output to:** `results/IMP03_result.md`

---

## PROMPT

You are a senior building-energy modeller. You know EnergyPlus 23.1 (source and IDD), the TABULA/EPISCOPE monthly method, and ISO 13790, ISO 52016-1 and ISO 13786.

We are a research team. We run a **European campaign**: about 400 one-zone "cells" in EnergyPlus 23.1, one cell per TABULA archetype and internal-gain level (Spain, Italy and the UK; 395 cells in the latest rerun). The goal is annual **heating demand** for these dwellings, following the TABULA/EPISCOPE method. We also plan "gpusim", a GPU re-implementation of a small part of EnergyPlus.

Our owner must take **five decisions**. Please give a recommendation for each. The owner decides, you advise.

**Scope limits.** Do NOT redesign gpusim. Do NOT review the build spec again. Decisions only.

### How to answer (rules)
- Plain English. Short sentences. The reader is not a native English speaker.
- Separate **checked facts** from **your estimates**. A checked fact needs a source: standard and clause, EnergyPlus source file:line (v23.1.0), IDD or Input Output Reference section, or a paper.
- Mark anything you could not check as `UNVERIFIED`. Do not guess a clause number.
- Do not praise our work. Say what is wrong or risky.
- If an option is bad, say so and say why.

### Context (facts from our repo, checked 2026-11-22)

**The cell.** One `Zone`. Five `BuildingSurface:Detailed` (floor, roof, walls). Window and door host walls use `Outdoors`. Floor, roof, b<1 walls and the thermal-bridge face use `OtherSideCoefficients` (film coefficient 0). All walls are `Sun_Exposure=NoSun`, `Wind_Exposure=NoWind` (`european_box.py:96–125`, line 113). Constructions are `Material:NoMass` with U × `f_red_temp` (the TABULA temperature-reduction factor). Windows are `WindowMaterial:SimpleGlazingSystem` with U × `f_red_temp` and SHGC = `g_gl_window` from TABULA (`european_box.py:290–292`). One `InternalMass`. Ventilation is constant ACH. Ideal loads, heating only, setpoint constant, `NoLimit`. `Timestep,12`. `SimulationControl,Yes,Yes,Yes,No,Yes,No,1` plus a full-year `SizingPeriod:WeatherFileDays` (`eu_cell_runner.py:50–62`, lines 58–59).

**D1 — F1: windows get zero solar gain.**
- The host walls have `Sun_Exposure=NoSun`. A fenestration surface has no sun-exposure field. EnergyPlus copies `ExtSolar` from the host (`SurfaceGeometry.cc:5185`). So window transmitted solar is zero all year. The per-window solar output is registered only for sun-exposed windows (`SolarShading.cc:1253–1312`). Both IMP02 and our own check confirm this.
- `g_gl_window` is written into the IDF but has no effect on the result.
- We have not checked whether the TABULA/EPISCOPE monthly method includes window solar gains. It has the solar term Q_sol = F_sh × (1 − F_F) × g_gl × A_window × I_sol, with shading reduction and frame fraction. **This is your key question.** Our `TABULA_PROVENANCE.md` (first 60 lines) is about data sources and licence only. It does not describe the method.
- Options: **(a)** keep as built. **(b)** set `Sun_Exposure=SunExposed` on window host walls only. This also turns on opaque solar absorption on those walls (absorptance 0.7) unless `Solar_Absorptance` is changed. **(c)** other (for example: sun on, with host wall absorptance set to a TABULA-consistent value, or window-only gains by another route).
- Questions: Does the TABULA method include solar gains through windows (g-value, frame factor, shading)? Which solar-irradiation data does it use, and does it include opaque-wall solar gain? What does omitting window solar do to heating demand, and to comparisons across countries and archetypes? Which option is closest to the method we claim to follow?

**D2 — F2: internal mass stores about half the intended heat.**
- `add_european_internal_mass` (`european_physics.py:57–100`) makes one 0.10 m slab, k = 1, ρ = 1800, cp = 900. That is 162,000 J/(m²·K). `Surface_Area = c_m × 3600 × A_floor / 162000`, with c_m = 45 Wh/(m²·K) (`EU_INTERNAL_MASS_WH_M2K`). So Surface_Area = A_floor, and area × capacity = 45 Wh/(m²·K) × A_floor.
- In EnergyPlus the `InternalMass` outside boundary is the surface itself. Both faces sit at the inside-face temperature. Heat is exchanged with the zone through **one** face area (`SurfaceGeometry.cc:7400–7426`, `:2173/2191`). By symmetry the mid-plane is adiabatic, so only half the slab (0.05 m) charges. Realised: about 22.5 Wh/(m²·K) instead of 45. This is our reading, plus IMP02's. The IDD memo says the area is "the total surface area exposed to the zone air". We have **not** checked what the Input Output Reference says about one-sided or two-sided mass.
- Options: **(a)** keep as built. **(b)** double the area. **(c)** double the thickness, or use a one-sided slab with an adiabatic back. **(d)** other.
- Questions: How is c_m defined in TABULA and in ISO 13790 and ISO 52016-1 (effective internal heat capacity per floor area, by the ISO 13786 periodic method with a 24 h period)? In that method, only a penetration depth of the layer takes part. So which option reproduces "45 Wh/(m²·K) effective"? Is the real answer different, because a 0.10 m concrete slab in a daily cycle may not be fully used even when both sides are exposed? What does the Input Output Reference say about `InternalMass` area?

**D3 — Go-ahead for M0 and M1 on the Mac.**
- M0 = golden reference data from EnergyPlus (annual and hourly outputs for a set of cells). M1 = a 64-bit NumPy reference engine for rung S0. S0 reproduces the IDF **as built** (no sun, current mass). S1 adds sun. Rung S2a adds general layered mass.
- Question: should anything in D1, D2 or D4 be settled **first**? Or can S0 safely start by reproducing the IDF as built? What is the cost if D1 or D2 changes later (what is thrown away, what is reused)? Should M0 record both the "as built" and the "fixed" variants now?

**D4 — Drop rung S4 from the gpusim ladder.**
- S4 = packaged DX HVAC (PTAC, PSZ-AC, PSZ-HP). It needs autosizing, economizers and nested DX-coil root-finding (`UnitarySystem.cc`). The proposal: route all of it to EnergyPlus on the CPU. S5 (VAV, plant) is already "not planned".
- The city path (multi-zone, North-American HVAC) is where the 900 s tail runs are. S4 would cover part of it.
- Question: is dropping S4 sound? What do we lose? Is there a cheaper partial form (for example, PTAC only)? What would make you keep it?

**D5 — Turn off the unused sizing pass in the campaign runner.**
- About 1.6 s of 4.2 s (38 %) per cell is a full-year zone sizing pass (`SizingPeriod:WeatherFileDays`, 1 Jan to 31 Dec). Its result is not used. Turning the sizing flags off gave identical annual heating to 8 decimals on one cell (`ES.ME.SFH.04`, Bologna): 32,069.768988 kWh. This is one cell only (IMP02 measurement, not yet reproduced by us). It is safe only because heating is `NoLimit` and there is no outdoor air.
- The campaign reruns about 400 cells per repetition.
- Question: what parity check is **enough** before we adopt it? Say how many cells, which metrics (annual heating, monthly, peak, hourly), which tolerance, and which cells must be in the sample (different countries, archetypes, with and without door, b<1 walls, extreme climates). Name any EnergyPlus behaviour that sizing can change even with `NoLimit` (for example the ideal-loads maximum supply temperature, autosized flow, or warm-up).

### Where to look (only if you have repo access)
- `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md`: §1 (F1, F2, runtime), §2 (rows S4, S5), §8 (decisions).
- `openubem/campaign/eu_cell_runner.py` lines 50–62.
- `openubem/idf/european_physics.py` lines 57–100.
- `openubem/idf/european_box.py` lines 96–125 and 249–325.
- `openubem/data/construction/TABULA_PROVENANCE.md` first 60 lines.
- `docs/docs_ACTIVE/GPU_based_compute/Prompt/IMP/results/IMP02_result.md` §3 (lines 43–70).

If you have no repo access, use only the context above and public sources. Say which sources you used.

### Required output format
Write **one section per decision**, in this order: D1, D2, D3, D4, D5. Each section has exactly these headings:

1. **Recommendation:** the one option you recommend, in one sentence. Then one line each on the risk of every other option.
2. **Reasons:** the 3 to 5 strongest reasons, strongest first. One short sentence each.
3. **Evidence (checked):** each fact with its source (standard and clause, E+ file:line, IDD or I/O Reference section, paper). Mark `UNVERIFIED` if not checked.
4. **Estimates:** your own numbers or judgements. Give the size (for example "heating demand changes by about X %") and your confidence. Mark every estimate as an estimate.
5. **Would change my mind:** the specific evidence or test that would change your answer.
6. **Effect on published results:** for the EU campaign results already published: re-run needed or not? If yes, which cells, and what changes in the numbers (direction and rough size). For D3 and D4, write "not applicable" if there is no effect.

Then end with a **final summary of exactly 5 lines**: one line per decision, in the form `Dn: option, confidence (high/medium/low), re-run needed (yes/no)`.

### Final rules
- Do not make the decision for us. Recommend, and show how sure you are.
- If two decisions depend on each other (for example D1 and D3), say so inside the sections.
- No tables unless a table is much shorter than the text.
