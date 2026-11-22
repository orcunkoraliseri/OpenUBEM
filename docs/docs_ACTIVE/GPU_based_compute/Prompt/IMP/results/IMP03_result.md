# IMP03 — Evidence-Based Advice on Owner Decisions D1–D5

**Context checked:** OpenUBEM repository (`eu_cell_runner.py`, `european_box.py`, `european_physics.py`, `european_controls.py`, `european_windows.py`, `hvac.py`, `scripts/run_eu_s2_campaign.py`, `tabula_archetypes_*.json`, `eu_campaign_cell_spec_v1.1.json`, 11 city validation manifests, `BUILD_SPEC` rev. 2, `IMP02_result.md`), local EnergyPlus 23.1.0 (`Energy+.idd`, `InputOutputReference.pdf`), ISO 13786 periodic calculations, and EnergyPlus 23.1.0 sensitivity runs on 5 real EU-08 archetypes (Madrid, Bologna, London).

---

## D1 — F1: Windows receive zero solar gain

### 1. Recommendation
**Recommend Option (c): set `Sun_Exposure=SunExposed` on window host walls, set those host walls' `Solar_Absorptance` to `0`, and reduce window SHGC by TABULA's shading and frame factors (`0.6 × (1 − 0.3) = 0.42 × g_gl_window`, or add explicit frame + shading transmittance `0.6`).**

- **Risk of Option (a) (keep as built):** **Bad option.** It removes a core TABULA heat-balance term, leaves `g_gl_window` as dead code, and inflates heating demand most strongly in sunny climates and well-insulated archetypes, breaking cross-country and vintage comparisons.
- **Risk of Option (b) (`SunExposed` with raw `g_gl_window` and wall absorptance `0.7`):** **Bad option.** It replaces missing solar with severe over-counting: frameless, unshaded glass overstates window gains by roughly 2.4×, and opaque solar absorption (`0.7`) heats only the `Wall_1` host faces while the roof and `b < 1` walls stay `NoSun`.

### 2. Reasons
- TABULA/EPISCOPE explicitly includes window solar gains using glazing `g`-value, frame fraction, and external shading reduction.
- Omitting window solar biases heating demand upward unevenly: sunny Spain and insulated modern dwellings lose far more solar offset than cloudy UK or leaky old dwellings.
- Option (b) is wrong in the opposite direction because it skips TABULA's frame and shading reductions and adds inconsistent opaque-wall solar gain on only part of the envelope.
- TABULA's common method omits opaque solar gains, and EnergyPlus 23.1 allows `Solar_Absorptance = 0` on `Material:NoMass`, so Option (c) cleanly isolates window solar.
- The 3D European district pipeline (`EU-11`) already sets `SunExposed` on exterior walls, so `NoSun` in `european_box.py` is an isolated one-zone campaign bug.

### 3. Evidence (checked)
- **Subsurface `NoSun` inheritance:** `european_box.py:113` sets `Sun_Exposure = "NoSun"` on all walls; EnergyPlus copies `ExtSolar` from the host wall (`SurfaceGeometry.cc:5185`, cited in `BUILD_SPEC` §9), and registers per-window solar output only when `ExtSolar` is true (`SolarShading.cc:1253–1312`, cited in `IMP02_result.md` §3.1).
- **3D EU districts already have sun on:** `scripts/run_eu_s2_campaign.py:1051,1202` set `surf.Sun_Exposure = "SunExposed"`, and `openubem/idf/european_windows.py:60,85` pass `g_gl_window` to `SimpleGlazingSystem`.
- **TABULA includes window solar gains:** Loga, Stein & Diefenbach (2013), *TABULA Calculation Method – Energy Use for Heating and Domestic Hot Water* (IWU, Darmstadt; based on EN ISO 13790), computes heating-season window solar gain as $Q_{\text{sol}} = \sum A_w \cdot g_{\text{gl,n}} \cdot (1 - F_F) \cdot F_{\text{sh}} \cdot F_W \cdot I_{\text{sol}}$, using orientation-specific heating-season global irradiation (N, S, E, W, horizontal) from national climate tables (`Tab.Climate`), with standard defaults $F_{\text{sh}} = 0.6$, $F_F = 0.3$, $F_W = 0.9$. Exact section and table numbers in Loga et al. (2013): `UNVERIFIED`.
- **Opaque solar gain in TABULA vs ISO 13790:** ISO 13790:2008 §11.3.3 defines glazed solar gains and §11.3.4 defines opaque solar gains. TABULA's simplified common method computes $Q_{\text{sol}}$ for transparent elements only and omits explicit opaque solar absorption (exact clause in Loga et al. 2013: `UNVERIFIED`).
- **EnergyPlus handles angular incidence automatically:** `WindowMaterial:SimpleGlazingSystem` computes angle-dependent SHGC internally (`WindowManager.cc:5480–5550`, cited in `IMP02_result.md` §11), so multiplying by TABULA's non-perpendicular factor $F_W = 0.9$ would double-count incidence-angle losses.
- **Zero opaque solar absorptance is valid:** `/Applications/EnergyPlus-23-1-0/Energy+.idd`, `Material:NoMass` field `N3` (`Solar Absorptance`): `\minimum 0`, `\default .7`, `\maximum 1`.
- **Measured EnergyPlus 23.1.0 impact on 5 EU-08 cells (`f = 0`, sizing off, scratch test):**
  - `ES.ME.SFH.01` (Madrid, old): `NoSun` = 147.92 kWh/m²; Option (c) (`alpha=0.0001`, `0.42·g_gl`) = 136.53 (**−7.7%**); window-only raw `g_gl` = 126.91 (**−14.2%**); Option (b) (`alpha=0.7`, raw `g_gl`) = 120.55 (**−18.5%**; opaque share **−4.3%**).
  - `ES.ME.TH.06` (Madrid, new): `NoSun` = 59.46; Option (c) = 35.26 (**−40.7%**); window-only raw `g_gl` = 20.31 (**−65.8%**); Option (b) = 18.31 (**−69.2%**; opaque share **−3.4%**).
  - `IT.MidClim.TH.08` (Bologna, new): `NoSun` = 54.21; Option (c) = 47.45 (**−12.5%**); window-only raw `g_gl` = 41.18 (**−24.0%**); Option (b) = 37.34 (**−31.1%**; opaque share **−7.1%**).
  - `GB.ENG.MFH.01` (London, old): `NoSun` = 156.82; Option (c) = 130.53 (**−16.8%**); window-only raw `g_gl` = 111.53 (**−28.9%**); Option (b) = 98.88 (**−36.9%**; opaque share **−8.1%**).
  - `GB.ENG.MFH.07` (London, new): `NoSun` = 55.97; Option (c) = 39.21 (**−29.9%**); window-only raw `g_gl` = 27.55 (**−50.8%**); Option (b) = 25.59 (**−54.3%**; opaque share **−3.5%**).
- **Dependency with D2 and D3:** Turning solar on creates diurnal indoor heat swings, which increases the sensitivity of heating demand to internal thermal mass (D2). For D3, gpusim S0 still targets the as-built `NoSun` IDF; S1 adds solar after D1 is settled.

### 4. Estimates
- **Fleet heating-demand reduction under Option (c) (estimate, high confidence):** across the 395/510 EU-08 cells, annual heating will drop by roughly **−10% to −20%** on older uninsulated archetypes and **−25% to −45%** on newer insulated or large-glazing archetypes, with Spain shifting more than the UK and Italy on average.
- **Over-reduction under Option (b) (estimate, high confidence):** Option (b) would under-predict heating by roughly **15% to 45%** relative to Option (c), because unshaded frameless glass plus `alpha = 0.7` host walls inject far more solar heat than TABULA assumes.
- **Comparison against TABULA workbook reference (estimate, medium confidence):** Option (c) should align within roughly 5%–15% of TABULA's seasonal solar gain term on matching weather years; Option (a) misses 100% of it.

### 5. Would change my mind
- A written campaign ruling stating that EU-08 was deliberately designed as a *solar-free sensitivity test* (not a TABULA heating-demand model) — if true, keep Option (a) and strip `g_gl_window` from the IDF/claims.
- Checking the pinned `tabula-calculator.xlsx` (`Calc.Set.Building`) and finding that specific countries in our ES/IT/GB subset use non-default `F_sh` or `F_F` values — if so, read those per-archetype factors from the workbook instead of using `0.6 × 0.7 = 0.42`.

### 6. Effect on published results
- **Re-run needed: YES**, for the **one-zone EU-08 campaign cells** (all 395 completed / 510 spec cells built by `eu_cell_runner.py` + `european_box.py`).
- **Not needed** for the 3D multi-zone EU-11 district results (`Madrid`, `Lyon`, `London`, `Bologna`), which already use `SunExposed` walls.
- **Expected shift:** heating demand drops on every EU-08 cell by roughly **−8% to −45%** under Option (c) (largest in Spain and well-insulated modern archetypes). Note that the `f = 0` vs `f > 0` internal-gain sensitivity slopes will also shift slightly because solar gains interact with gain utilization.

---

## D2 — F2: Internal mass stores about half the intended heat

### 1. Recommendation
**Recommend Option (b): double `InternalMass` `Surface_Area` to `2 × A_floor` (keeping the 0.10 m concrete slab), and fix `internal_mass_capacity_j_k` (`european_physics.py:103`) to account for the half-slab symmetry.**

- **Risk of Option (a) (keep as built):** Realizes only half the declared capacity (22.5 Wh/(m²·K) static; 17.0 Wh/(m²·K) effective 24 h capacity with surface film), under-damping diurnal solar and intermittent gain spikes (`f > 0`).
- **Risk of Option (c) (double thickness to 0.20 m, or one-sided 0.10 m adiabatic slab):** **Bad option.** Although static heat capacity reaches 45 Wh/(m²·K), keeping `1 × A_floor` starves heat transfer through the surface film resistance so the 24 h effective capacity is only **20.6 Wh/(m²·K)** — barely better than as built!
- **Risk of Option (d) (thinner slab at ~3.2–3.5× `A_floor` to hit 45 Wh/(m²·K) *with* $R_{si}$):** Unnecessarily inflates the `InternalMass` surface area inside `ScriptF`, magnifying the interior longwave view-factor shift on the non-enclosed box mesh.

### 2. Reasons
- EnergyPlus 23.1's Input Output Reference explicitly instructs users to enter **twice the surface area** when both sides of an internal slab exchange heat with the zone.
- Under ISO 13786's 24-hour periodic method, Option (b) reaches 44.7 Wh/(m²·K) at the surface (34.0 Wh/(m²·K) including $R_{si} = 0.13$), whereas Option (c) stalls at 20.6 Wh/(m²·K) including $R_{si}$.
- Option (b)'s exposed area (`2.0 × A_floor`) is much closer to ISO 13790 Table 12's effective mass area (`2.5 × A_floor` for medium mass) than Option (c)'s `1.0 × A_floor`.
- Be aware of one real side-effect: doubling `InternalMass` area changes interior longwave view factors (`ScriptF`), which slightly raises steady-state heating (`+0.5%` to `+2.3%` at `f = 0`, `NoSun`) even while improving dynamic heat storage under solar and intermittent gains.
- This decision depends on D1: under `NoSun`, internal mass barely changes annual heating; once D1 turns solar on, thermal mass actually stores daytime solar gains and reduces evening heating.

### 3. Evidence (checked)
- **EnergyPlus I/O Reference rule (direct quote):** `/Applications/EnergyPlus-23-1-0/Documentation/InputOutputReference.pdf`, §1.10.40 `InternalMass` (p. 325): *"Similar to internal surfaces with an adiabatic boundary condition, the zone will only exchange energy with the inside of the Internal Mass construction. If both sides of the surface exchange energy with the zone then the user should input twice the area when defining the Internal Mass object."* Same in §1.10.40.1.5 `Field: Surface Area` (p. 326): *"If both sides of a wall are completely within the same zone, then the area of both sides must be included when describing that internal wall."*
- **EnergyPlus IDD & source:** `Energy+.idd` (`InternalMass` memo) states *"This should be the total surface area exposed to the zone air."* `SurfaceGeometry.cc:7400–7426` and `HeatBalanceSurfaceManager.cc:7463–7466` set `ExtBoundCond = SurfNum` ($T_{\text{out}} \equiv T_{\text{in}}$) with 1× area, placing an adiabatic symmetry plane at mid-thickness (`0.05 m`) (cited in `BUILD_SPEC` §9 and `IMP02_result.md` Table A6).
- **TABULA and ISO 13790 / ISO 52016-1 definitions:** TABULA fixes `c_m = 45 Wh/(m²·K)` (= `162,000 J/(m²·K)`) across archetypes (`tabula_archetypes_*.json`, verified across all 11 country files). ISO 13790:2008 §12.3.1.2 Table 12 defines "Medium" internal effective heat capacity as `C_m = 165,000 J/(m²·K)` ($\approx 45.8\text{ Wh/(m}^2\text{K)}$) with effective mass area `A_m = 2.5 × A_f`, calculated from element areal capacities per ISO 13786 (24 h period). ISO 52016-1:2017 references ISO 13786 and covers internal zone heat capacity in §6.5.11 and Annex A/B (exact ISO 52016-1 table number for `C_m` classes: `UNVERIFIED`).
- **Exact ISO 13786 24-hour periodic math ($T = 86,400\text{ s}$, $k = 1.0$, $\rho = 1800$, $c_p = 900$):**
  - Periodic penetration depth $\delta = \sqrt{T k / (\pi \rho c_p)} = 0.1303\text{ m}$.
  - As built (`1 × A_f`, `d_eff = 0.05 m`, $\xi = 0.384$): static `22.50 Wh/(m²·K)`; periodic surface $|Y|/\omega$ ($R_{si} = 0$) = `22.35 Wh/(m²·K)`; with $R_{si} = 0.13\text{ m}^2\text{K/W}$ = **`17.01 Wh/(m²·K)`**.
  - Option (b) (`2 × A_f`, `d_eff = 0.05 m`, $\xi = 0.384$): static `45.00 Wh/(m²·K)`; periodic ($R_{si} = 0$) = **`44.70 Wh/(m²·K)`**; with $R_{si} = 0.13$ = **`34.02 Wh/(m²·K)`**.
  - Option (c) (`1 × A_f`, `d_eff = 0.10 m`, $\xi = 0.767$): static `45.00 Wh/(m²·K)`; periodic ($R_{si} = 0$) = `40.85 Wh/(m²·K)`; with $R_{si} = 0.13$ = **`20.64 Wh/(m²·K)`** (film-bottlenecked).
- **Measured EnergyPlus 23.1.0 impact on 3 insulated EU-08 cells (scratch test):**
  - At `f = 0`, `NoSun` (`ES.ME.TH.06`): `1A, 0.10 m` = 59.46 kWh/m²; Option (b) (`2A, 0.10 m`) = 60.84 (**+2.33%** from `ScriptF` interior view-factor shift); Option (c) (`1A, 0.20 m`) = 59.17 (**−0.47%**).
  - Diurnal intermittent gains (mean 3.0 W/m² conserved, evening peak 3.4×), `NoSun`: Option (b) shifts heating by **+1.80%** (`ES_new`), **+0.50%** (`IT_new`), **+1.05%** (`GB_new`); Option (c) shifts by **−0.58%**, **−0.59%**, **−0.33%**.
  - Same intermittent gains with Option (c) solar ON: Option (b) shifts heating by **−2.55%** (`ES_new`), **+0.02%** (`IT_new`), **−0.84%** (`GB_new`); Option (c) shifts by **−3.01%**, **−0.80%**, **−1.36%**.
- **Scope in repo:** `add_european_internal_mass` is called by **both** `openubem/campaign/eu_cell_runner.py:376` (EU-08 cells) **and** `scripts/run_eu_s2_campaign.py:2055` (the 3D multi-zone EU-11 districts).

### 4. Estimates
- **Annual heating impact across the EU-08 fleet under Option (b) (estimate, medium-high confidence):** if bundled with D1 (solar ON), Option (b) changes annual heating by roughly **−3% to +1.5%** depending on climate and gain intermittency (net of the +0.5% to +2.3% `ScriptF` shift and −1% to −5% added daytime storage). Peak evening heating power drops by roughly **5% to 15%** on high-`f` / high-solar cells (estimate, medium confidence).
- **Impact on EU-11 3D districts (estimate, medium confidence):** roughly **−2% to +1%** on pooled district heating EUI, because those buildings already have sun ON and lower `NoMass` envelope-to-mass distortion than the disconnected one-zone box.

### 5. Would change my mind
- If the owner wants strictly zero `ScriptF` steady-state shift on `NoSun` cells while still avoiding Option (c)'s film bottleneck, that would favour keeping Option (a) only if D1 also stays `NoSun` (since mass barely moves constant-setpoint `NoSun` heating anyway).
- If a test on the 3D EU-11 buildings shows that `2 × A_floor` causes unacceptable `FixViewFactors` distortion in small multi-zone dwellings, then use `2 × A_floor` with `0.08–0.10 m` or switch to a 1-sided adiabatic `BuildingSurface:Detailed` partition.

### 6. Effect on published results
- **Re-run needed: YES for EU-08** (bundle directly with the D1 re-run so the 395/510 cells are only re-run once; net D2 effect is roughly **−3% to +1.5%** on annual heating).
- **EU-11 3D districts (`Madrid`, `Lyon`, `London`, `Bologna`):** `scripts/run_eu_s2_campaign.py:2055` also calls `add_european_internal_mass`. A re-run is **optional** (small shift, roughly **−2% to +1%**); if EU-11 is already frozen/published, documenting the realised `22.5 Wh/(m²·K)` static / `17 Wh/(m²·K)` effective capacity is a reasonable alternative to restating 3,870 buildings.

---

## D3 — Go-ahead for M0 and M1 on the Mac

### 1. Recommendation
**Recommend proceeding with M0 and M1 now on the IDF as built, while adding 2–3 extra "fixed D1/D2" golden cells to M0 right away.**

- **Risk of waiting for D1, D2, or D4 before starting M0/M1:** Wastes schedule time for zero engineering benefit, because S0 (`NoSun`) is the exact non-solar foundation that S1 requires anyway.
- **Risk of recording only "as built" cells in M0:** Low risk — it only costs a few minutes to regenerate extra golden Parquets later, though it misses an early check of whether D2 (`2 × A_floor`) alters `FixViewFactors` or warm-up day counts.

### 2. Reasons
- Every equation in M1 (S0: weather interpolation, height lapse, OSC, TARP/DOE-2/ISO-15099 convection, `ScriptF`, simple glazing, BDF3 air and moisture balance, ideal loads, sub-stepping, warm-up) is 100% reused in S1 even if D1 turns solar on.
- Changing D2 later throws away zero code in M1, because `InternalMass` `Surface_Area` and `Thickness` are pure data inputs to `compile.py` and `ctf.py`.
- D4 (S4 packaged HVAC) is four rungs downstream and does not touch M0, M1, or any S0–S3 data structure.
- Keeping S0 (`NoSun`) as a separate, permanent conformance rung isolates non-solar heat-balance bugs from solar bugs before S1 begins.
- Adding 2–3 D1/D2-fixed golden cells to M0 takes under one minute of E+ runtime and gives immediate test fixtures for S1 and F2.

### 3. Evidence (checked)
- **S0 physics reused by S1:** `BUILD_SPEC_gpu_heat_balance_engine.md` §2 (lines 83–84) and §7 (line 299) confirm S1 adds solar on top of the intact S0 solver, and S0/S1 stay separately testable.
- **D2 is purely parametric:** `openubem/idf/european_physics.py:57–100` changes only `Surface_Area` or `Thickness` on the single `InternalMass` object; no new IDF object type or solver branch is added.
- **M0 runtime cost:** Our scratch EnergyPlus 23.1.0 runs took ~2.5 s per cell (sizing off) and ~4.2 s (sizing on) on this Mac, so recording 5 as-built cells plus 3 fixed-D1/D2 cells takes under 30 seconds total.
- **Existing approval note:** `BUILD_SPEC` §8 line 308 already records owner approval for M0 + M1 on 2026-11-22; this advice confirms that decision is technically sound even while D1/D2 remain open.
- **Dependency with D1 and D2:** If D1 and D2 trigger an EU-08 re-run, M1's P2 fleet parity check (`BUILD_SPEC` §4 line 211) should test S0 against the as-built 346-cell archive first, then test S1 against the re-run fleet once M6 lands.

### 4. Estimates
- **Code throwaway if D1 changes later (estimate, high confidence):** **0%** of S0 physics code; **< 5%** of harness/fixture plumbing (just updating P2 fleet paths for S1).
- **Code throwaway if D2 changes later (estimate, high confidence):** **0%** of code; only a few minutes to regenerate golden Parquets if the golden fixtures are updated.
- **Extra cost to record both as-built and D1/D2-fixed golden cases in M0 now (estimate, high confidence):** **< 1 hour** of scripting and **< 1 minute** of EnergyPlus runtime.

### 5. Would change my mind
- If the owner cancels `gpusim` entirely because the D5 sizing fix already cuts a 400-cell EU rerun to ~90 seconds on 12 cores (`BUILD_SPEC` §5 line 251) and OpenUBEM has no plans for `10⁵+` building-year sweeps.

### 6. Effect on published results
- Not applicable.

---

## D4 — Drop rung S4 from the gpusim ladder

### 1. Recommendation
**Recommend dropping rung S4 (PTAC, PSZ-AC, PSZ-HP) permanently and routing all real-HVAC buildings (S4 and S5) to EnergyPlus on the CPU.**

- **Risk of keeping full S4:** High engineering cost (months of work on autosizing, economizers, DX coil curves, and nested root-finders with heavy GPU warp divergence) that **does not speed up the 900 s city tail**.
- **Risk of a cheaper partial S4 (PTAC only):** **Bad option.** PTAC still needs DX coil curves, outdoor-air mixing, and autosizing, yet covers **0.0%** of our validated city building stock.

### 2. Reasons
- The 900 s city tail is **not** in S4: 19 of the 20 slowest buildings across all 11 validation cases are S5 (Built-up VAV and Packaged VAV), which is already dropped.
- In `austin_centre`, S5 accounts for **84.8% of total CPU time** and the 907 s single-building wall-clock floor; S4 is only **15.2% of CPU time**, so an infinitely fast S4 cuts 12-core makespan by **0%**.
- PTAC-only is useless on our stock: it covers **0 of 1,024** successful validation buildings (`hvac.py` uses PTAC only for `SmallHotel` and unknown-family fallbacks).
- Real packaged DX systems (`PSZ-AC`, `PSZ-HP`) require autosizing, `DifferentialDryBulb` economizers, and iterative coil root-finding that diverge across GPU threads and break lock-step throughput.
- Cloud many-core CPU EnergyPlus plus Phase 1 CPU wins (LPT ordering, shading cuts, typical-floor multipliers) handle S4 and S5 cheaply with 100% fidelity.

### 3. Evidence (checked)
- **Measured HVAC breakdown in repo validation manifests** (11 cases in `docs/docs_VALIDATION/step1/overAll/results/cases/*/04_simulation_manifest.parquet`, joined with `05_results.csv`, `openubem/data/loads/hvac_systems_by_archetype.json`, and the Option-C 1-zone guard in `openubem/idf/hvac.py:662–680`; 1,024 successful runs, 13,351.9 CPU-s total):
  - **S5 (Built-up VAV + PVAV + WLHP):** 76 of 1,024 buildings (**7.4%**), **9,692.6 s (72.6% of CPU time)**.
  - **S4 (PSZ-HP + PSZ-AC + Option-C 1-zone PSZ-AC):** 948 of 1,024 buildings (**92.6%**), **3,659.4 s (27.4% of CPU time)** — median ~3 s per building. **PTAC = 0 buildings (0.0%).**
- **Measured `austin_centre` breakdown** (341 successful runs, 9,940.3 CPU-s):
  - **S5:** 58 buildings (17.0%), **8,434.4 s (84.8% of CPU time)**. Slowest building: `SuperTallBuilding`, 42 floors, Built-up VAV = **906.9 s**.
  - **S4:** 283 buildings (83.0%), **1,506.0 s (15.2% of CPU time)**.
  - **Top 20 slowest runs across all 11 cases:** ranks #1–#19 (906.9 s down to 178.5 s) are all **S5** (`SuperTallBuilding`, `LargeOffice`, `Courthouse`, `TallBuilding` on Built-up VAV or PVAV w/ HW Reheat). Rank #20 is the first S4 building (`RetailStandalone`, 4 floors, PSZ-AC, 175.0 s).
- **S4 complexity in repo:** `openubem/idf/hvac.py:176–299` emits `HVACTemplate:Zone:PTAC`, `HVACTemplate:System:Unitary` (PSZ-AC), and `HVACTemplate:System:UnitaryHeatPump:AirToAir` (PSZ-HP), all with autosized coils/flows, `Outdoor_Air_Method = Flow/Person`, and `Economizer_Type = DifferentialDryBulb` on PSZ.
- **EnergyPlus `UnitarySystem.cc` size:** IMP02 reports 18,171 LOC and 43 `SolveRoot` loops (`IMP02_result.md` §1); exact counts in `NREL/EnergyPlus` `v23.1.0` source: `UNVERIFIED` directly in this session.
- **Makespan bound:** `PLAN_gpu_accelerated_simulation.md` §1.1 (line 54) confirms the 12-core lower bound for `austin_centre` is $\max(9940/12, 907) = 907\text{ s}$.

### 4. Estimates
- **What we lose by dropping S4 (estimate, high confidence):** we lose GPU-batched sweeps over US/North-American single-zone commercial/residential stock *with* full DX coil part-load curves, latent dehumidification, and economizers. Those sweeps must either run on CPU E+ (many-core/cloud, roughly \$0.15–\$0.30 per 10k 3-second buildings) or run on gpusim `S2a/S2b/S3` ideal loads with post-processed COP/efficiency.
- **Effort saved by dropping S4 (estimate, medium-high confidence):** avoids roughly **3–6 person-months** of implementation and conformance debugging for a **0% reduction** in `austin_centre` 12-core makespan and only a **15%–27% reduction** in total city CPU-seconds.

### 5. Would change my mind
- A firm research requirement to run `10⁵+` North-American scenario sweeps (e.g., nationwide residential/retail heat-pump retrofit or peak-electric-demand uncertainty studies) where ideal loads + post-processed COP fails validation (for example, latent cooling or economizer control errors > 5%) AND cloud CPU EnergyPlus is unaffordable or too slow for interactive use.

### 6. Effect on published results
- Not applicable.

---

## D5 — Turn off the unused sizing pass in the campaign runner

### 1. Recommendation
**Recommend turning off the unused sizing pass in `eu_cell_runner.py` (`SimulationControl,No,No,No,No,Yes,No,1;` and omitting `SizingPeriod:WeatherFileDays` and `Sizing:Zone`), guarded by an explicit fail-closed assertion on `NoLimit` and `Outdoor_Air_Method=None`, after a full-fleet (or 20-cell stratified) parity check.**

- **Risk of keeping sizing ON:** Wastes ~38% of every EU-08 simulation (~1.6 s per cell) computing sizing tables that are never used.
- **Risk of turning sizing OFF without a code guard and parity test:** Silent physics errors if a future template edit adds `LimitCapacity`, `LimitFlowRate`, outdoor air, economizers, heat recovery, or any `autosize` field.

### 2. Reasons
- Under `Heating_Limit = NoLimit`, `Cooling_Limit = NoLimit`, and `Outdoor_Air_Method = None`, EnergyPlus ignores the autosizable heating/cooling flow and capacity fields, so the year-long sizing pass changes nothing.
- Our EnergyPlus 23.1.0 parity check across 5 diverse EU-08 cells (Spain, Italy, UK; old and new; with and without doors and `b < 1` boundaries) showed exact `0.00e+00 kWh` difference on annual total **and** on every single hour of the year.
- Because `SimulationControl` runs each `RunPeriod` as an independent environment with its own `BeginEnvrnFlag` reset and warm-up, removing `SizingPeriod:WeatherFileDays` does not alter warm-up convergence.
- Running a parity test on all 395 cells takes only ~90 seconds on 12 cores (with sizing off), so you do not even need to gamble on a tiny sample — though a 20-cell stratified sample is already sufficient as a fast CI gate.
- A fail-closed assertion in `eu_cell_runner.py` is mandatory so nobody can later turn on capacity limits or outdoor air while sizing stays off.

### 3. Evidence (checked)
- **Current IDF setup:** `openubem/campaign/eu_cell_runner.py:58–59,361–370` emits `SimulationControl,Yes,Yes,Yes,No,Yes,No,1;`, `SizingPeriod:WeatherFileDays,AnnualSizingPeriod,1,1,12,31,,No,No;`, and `Sizing:Zone`. `openubem/idf/european_controls.py:88–92` emits `HVACTemplate:Zone:IdealLoadsAirSystem` with `Heating_Limit="NoLimit"`, `Cooling_Limit="NoLimit"`, `Outdoor_Air_Method="None"`.
- **IDD rules on `NoLimit` and `SimulationControl`:** `/Applications/EnergyPlus-23-1-0/Energy+.idd`:
  - `HVACTemplate:Zone:IdealLoadsAirSystem` and `ZoneHVAC:IdealLoadsAirSystem`: both `Maximum Heating Air Flow Rate` and `Maximum Sensible Heating Capacity` state *"This field is ignored if Heating Limit = NoLimit"*. `Maximum Heating Supply Air Temperature` defaults directly to `50` °C (not autosized).
  - `SimulationControl`: when `Do Zone Sizing Calculation = No`, `Sizing:Zone` objects are ignored.
- **Independent environment warm-up:** `/Applications/EnergyPlus-23-1-0/Documentation/InputOutputReference.pdf`, §1.5.16.1.4–1.5.16.1.5 (p. 69): each `SizingPeriod` and each `RunPeriod` constitutes a separate environment with its own warm-up convergence. `HeatBalanceSurfaceManager.cc:7582–7584` (cited in `BUILD_SPEC` §9) re-initializes surfaces and zone air to 23.0 °C at `BeginEnvrnFlag`.
- **Measured parity on 6 EU-08 cells (zero difference):**
  - IMP02 (`ES.ME.SFH.04`, Bologna): 32,069.768988 kWh vs 32,069.768988 kWh (0.000000 kWh delta, 38.3% faster: 4.23 s → 2.61 s; `IMP02_result.md` §1, §9).
  - Our scratch E+ 23.1.0 tests on 5 cells (`ES.ME.SFH.01` Madrid, `ES.ME.TH.06` Madrid, `IT.MidClim.TH.08` Bologna with door + `b=0.5` floor, `GB.ENG.MFH.01` and `GB.ENG.MFH.07` London with door + `b=0.5` wall): **exact `0.00e+00 kWh` annual difference and `0.00e+00 kWh` max hourly difference across all 8,760 hours on all 5 cells.**
- **Behaviours sizing CAN change even when `Heating_Limit = NoLimit`:**
  1. *Outdoor air economizer or heat recovery on IdealLoads:* `ZoneHVAC:IdealLoadsAirSystem` IDD notes that `Maximum Cooling Air Flow Rate` (autosizable) is required when outdoor air economizer / heat recovery is active (exact `PurchasedAirManager.cc` lines: `UNVERIFIED`).
  2. *Demand-controlled ventilation or `DesignSpecification:OutdoorAir` sizing:* if `Outdoor_Air_Method != None`, zone sizing populates design outdoor airflow.
  3. *`Sizing:Zone` design supply temperature:* does **not** alter `HVACTemplate:Zone:IdealLoadsAirSystem`'s `50 °C` cap (which is a direct field, not read from `Sizing:Zone`), and under `NoLimit` the `50 °C` temperature simply increases mass flow $\dot{m} = Q / (c_p(50 - T_z))$ without capping sensible heating capacity (exact `PurchasedAirManager.cc:2569–2842` formula cited in `IMP02_result.md` Table A17).
  4. *Hidden global state leak across environments:* not observed on 6 cells, and `BeginEnvrnFlag` resets thermal state, though an exhaustive audit of every EnergyPlus 23.1 module for leaked static variables across environments is `UNVERIFIED` — this is why a fleet parity gate is required.
  5. *CSV/SQL schema:* `eplusout.sql` sizing tables (`ZoneSizes`) will be empty when sizing is off; verify no downstream extractor reads them (`eu_cell_runner.py:406–420` reads only `eplusout.csv` hourly heating).

### 4. Estimates
- **Sufficient parity check before adoption (recommendation/estimate, high confidence):**
  - **Sample size:** **20 stratified cells** as the fast minimum gate — OR **all 395 cells** once (takes only ~90 s on 12 cores, completely eliminating sampling risk).
  - **Mandatory strata in the 20-cell set:** all 3 countries (ES, IT, GB); oldest uninsulated and newest insulated periods; all dwelling types (SFH, TH, MFH, AB); with door and without door; with `b < 1` walls/floors and thermal-bridge faces; `f = 0` and `f = 1.0` intermittent gains; plus 2 extreme climates (e.g., Helsinki, Montreal) if future sweeps use them.
  - **Metrics and tolerances:** annual heating `|Δ| ≤ 1e-6 kWh` (expect exact `0.0`); all 12 monthly totals `|Δ| ≤ 1e-6 kWh`; peak hourly heating `|Δ| ≤ 1e-6 kW`; all 8,760 hourly values `max |Δ| ≤ 1e-6 kWh`; zero new severe errors in `eplusout.err`; and confirm downstream extractors do not read SQL sizing tables.
- **Runtime saving (estimate, high confidence):** ~**35%–40% faster** per EU-08 cell (~4.2 s → ~2.6 s on M2 Pro E+ 23.1 Rosetta; ~90 s for 400 cells on 12 cores).

### 5. Would change my mind
- Any single cell in the 20-cell or 395-cell parity check showing `max |ΔQ_hour| > 1e-6 kWh`, a warm-up day-count shift, or a downstream script failing because `eplusout.sql` lacks `ZoneSizes` tables.
- Any plan to introduce `LimitCapacity`, `LimitFlowRate`, or `Outdoor_Air_Method != None` into `eu_cell_runner.py` (in which case sizing must stay ON for those cells).

### 6. Effect on published results
- **Re-run needed: NO.** Turning off the unused sizing pass changes heating results by `0.000000 kWh` (exact bit-for-bit parity on 6 tested cells). Keep published EU-08 manifests as they are and apply the sizing-off change (with provenance flag) to all future runs and to any D1/D2 re-run.

---

## Final Summary

D1: option (c) (SunExposed host walls, wall Solar_Absorptance=0, TABULA F_sh×(1−F_F) window scaling), high, yes
D2: option (b) (double InternalMass Surface_Area to 2×A_floor), medium, yes
D3: proceed with M0 and M1 now on IDF as built (plus 2–3 fixed-D1/D2 golden cells in M0), high, no
D4: drop S4 permanently (route all real HVAC to CPU EnergyPlus), high, no
D5: turn off unused sizing pass with NoLimit/NoOA guard after 20-cell or full 395-cell exact-parity check, high, no
