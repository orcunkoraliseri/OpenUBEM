# DR11 — Brief: Translating TABULA Monthly-Balance Parameters into Dynamic Simulation

- **Validates decisions**: D-EU-01, D-EU-02, D-EU-03, D-EU-07 in [`../debugs/docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DECISIONS_parent-open-items-2026-08-23.md). These were ruled from the TABULA workbook on 2026-08-23 under the principle "reproduce TABULA's own balance literally, declare the rest"; this brief asks the literature whether each realisation is standard practice, whether a better-founded one exists, and what error it is known to carry.
- **Report to be saved as**: `DR11_tabula_to_dynamic_simulation_translation.md`
- **Date of brief**: 2026-08-23

---

## Task (paste everything below this line into the deep-research tool)

You are producing a publication-grade research report on how TABULA/EPISCOPE archetype parameters — which are defined for a **monthly quasi-steady-state energy balance (EN ISO 13790 seasonal/monthly method)** — are translated into **hourly dynamic simulation models (EnergyPlus; also Modelica/TEASER, IDA-ICE, TRNSYS where the literature uses them)**, and on the consequences of each translation choice.

### Context you must take as given

The project holds, for 102 existing-state archetypes (Spain 24, England 36, Italy 42), the following TABULA `Calc.Set.Building` quantities per archetype: conditioned reference area `A_C_Ref`, conditioned volume `V_C`, storeys `n_Storey` (and `n_Storey_effective_envelope`), room height `h_room`, envelope areas `A_Roof_1..2`, `A_Wall_1..3`, `A_Floor_1..2`, `A_Door_1`, window areas by orientation `A_Window_{Horizontal,East,South,West,North}`, U-values per element, `delta_U_ThermalBridging` (defined by TABULA as "supplement to all U-values"; values 0–0.15 W/(m²K)), `b_Transmission_*` adjustment factors per element (1 or 0.5), `g_gl_n_Window_1` (0.67–0.85), `n_Apartment` (1 for SFH/TH; 5–78 for MFH/AB; three non-integer synthetic-average rows), `n_air_use = 0.4 h⁻¹` and `n_air_infiltration ∈ {0.05, 0.1, 0.2, 0.4}`, internal heat capacity `c_m = 45 Wh/(m²K)` of reference area, internal gains `phi_int = 3 W/m²` constant, heating set-point `theta_i = 20 °C`, intermittency factors `F_red_htr1 = 0.90/0.95`, `F_red_htr4 = 0.80/0.85` and the per-archetype interpolated `F_red_temp` (0.80–0.99), DHW need `q_w_nd`, and the resulting `h_Transmission` and `h_Ventilation` (W/(m²K) of reference area).

The project has provisionally ruled the following realisations in EnergyPlus and wants each one checked against the literature:

| ID | Provisional realisation |
|---|---|
| R1 | **Box from areas**: floor plate `A_C_Ref/n_Storey`, storey height `V_C/A_C_Ref`, exposed perimeter from Σ`A_Wall`/(storeys × height); rectangle solved from area + perimeter; if the perimeter is too short for the area (attached rows), a square plate with adiabatic party walls for the missing perimeter. Faces are literally N/E/S/W and `A_Window_<dir>` sits on its own face; roof gets `A_Window_Horizontal`. One centred window per face per storey. |
| R2 | **Dwellings per archetype = `n_Apartment`**, sliced into one thermal zone per dwelling; an unconditioned circulation core added **outside** `A_C_Ref` for MFH/AB. |
| R3 | **Mass-less envelope + explicit internal mass**: every opaque construction is a single `Material:NoMass` layer sized to `U + delta_U`; all thermal mass is one `InternalMass` per zone with `ρ·c_p·d·A = c_m·A_zone`. |
| R4 | **Thermal bridging** as a uniform surcharge `delta_U` on every element including windows. |
| R5 | **`b`-factors** as `SurfaceProperty:OtherSideCoefficients` (b = 0.5 → 0.5·T_zone + 0.5·T_ext), no ground-domain model. |
| R6 | **Air change** = `n_air_use + n_air_infiltration`, constant, no wind/temperature dependence, no window opening. |
| R7 | **`F_red_temp`** realised as a multiplier on every envelope U-value and on the air-change rate (no set-back schedule). |
| R8 | **Internal gain** as one `OtherEquipment` per zone, 3 W/m², all-convective (radiant 0, latent 0). |
| R9 | **No cooling**; heating-only ideal loads at 20 °C constant; summer free-floating with overheating reported as an indicator only. |
| R10 | **Windows** as `SimpleGlazingSystem` with `SHGC = g_gl_n`, `U = U_Window + delta_U`. |

### Questions to answer, per realisation R1–R10

1. Is this how published TABULA-to-dynamic translations do it? Name the studies and tools (TEASER's TABULA import and its geometry/mass assumptions; EPISCOPE/TABULA "calculation method" documentation; the IWU "TABULA Calculation Method" report; EN ISO 13790 Annexes on `b` factors, `c_m` classes and `F_red`; EN ISO 52016-1 and 52017-1 on mass and gain splits; published EnergyPlus or Modelica archetype studies for Spain, the UK, Italy built from TABULA). Quote the relevant passage or table.
2. If a better-founded alternative exists, state it with its source and with the **reason** the literature prefers it.
3. What error or bias is each realisation known to introduce in annual heating demand, peak load, and overheating indicators? Cite measured comparisons where they exist (e.g. monthly-method vs dynamic results for the same TABULA archetype; mass-less vs layered envelope; constant vs wind-driven infiltration; all-convective vs split gains).
4. For R7 specifically: how do EN ISO 13790 §13.2 and the TABULA method define `F_red` (temperature-reduction factor for intermittent heating and unheated spaces), and which dynamic-model realisation preserves its meaning — U-multiplier, set-point reduction, or a reduced operating-hours schedule? The project must not add a schedule that would confound an occupancy signal; say whether the U-multiplier is defensible under that constraint.
5. For R3 specifically: how does EN ISO 52016-1 (Table B.14 classes; the "areal heat capacity" definition) relate `c_m` to a dynamic model's mass surfaces, and what is the accepted way to verify that a model's effective capacity equals the target (e.g. EN ISO 13786 periodic method; a decrement-factor test)?
6. For R1/R2: what do TABULA's own documentation and the national brochures say about the reference geometry (is `A_C_Ref` net or gross; what the wall areas include; whether party walls are counted), and how do the Spanish, English and Italian brochures define the example buildings' shapes?

### Hard rules

1. No invented numbers, tables, or standard clauses. Every figure or quotation carries its source (standard number and clause; DOI or URL; retrieval date) or `UNVERIFIED`.
2. Do not present a tool's default as a standard; say which is which.
3. Separate facts, inferences and recommendations with explicit labels.
4. Do not propose calibration to measured data; the project has none and says so.

### Output format

```
# DR11: Translating TABULA Monthly-Balance Parameters into Dynamic Simulation
## 1. Executive Summary                 (for each R1–R10: "standard / acceptable-with-caveat / not recommended" and one sentence why)
## 2. What TABULA's Method Defines      (A_C_Ref, areas, b, c_m, F_red, n_air, phi_int — with clause citations)
## 3. Realisation-by-Realisation Review (one subsection per R; literature practice, alternative, known error)
## 4. Verification Tests the Project Should Add   (read-back and single-surface fixtures that prove each realisation)
## 5. Comparative Table                 (R | project rule | literature practice | expected bias | verdict)
## 6. Synthesis for the OpenUBEM European Locations Arc
## References
```

### Acceptance test the project will apply

Accepted only if every verdict in §1 is backed by at least one cited source in §3, the `F_red` question (item 4) receives a clause-level answer, and §4 proposes a concrete fixture test for R3, R5 and R7.
