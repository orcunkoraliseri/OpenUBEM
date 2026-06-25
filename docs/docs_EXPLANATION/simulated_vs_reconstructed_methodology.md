# Simulated vs Reconstructed EUI — Methodology

**What this document explains:** how OpenUBEM produces two different whole-building
Energy Use Intensity (EUI) numbers for every building — the **simulated** EUI (what
EnergyPlus computes) and the **reconstructed** EUI (simulated + the service loads
EnergyPlus structurally cannot meter) — and exactly how each is calculated.

Written to be read top-to-bottom: the plain-language version first, the technical detail
and equations after.

---

## 1. The one-paragraph version

EnergyPlus, as OpenUBEM configures it, only computes **four** kinds of building energy:
space heating, space cooling, lighting, and plug equipment. It never computes fans,
pumps, hot water, refrigeration, or cooking — those are **structurally zero** in the
output. The **simulated** EUI is the sum of those four. The **reconstructed** EUI takes
that simulated number and adds the five missing end-uses back, estimated from published
per-building-type energy splits (CBECS-2018 / PNNL). Reconstruction is a *reporting-layer*
post-process — it never re-runs the simulation and never changes the physics.

```
Simulated     = heating + cooling + lighting + equipment            (EnergyPlus output)
Reconstructed = Simulated + fans + pumps + DHW + refrigeration + cooking   (added afterward)
```

---

## 2. Simulated EUI — what EnergyPlus actually computes

### 2.1 Why only four end-uses

OpenUBEM conditions every thermal zone with EnergyPlus's
**`ZoneHVAC:IdealLoadsAirSystem`**. This is a deliberate UBEM modeling choice: instead of
modeling a specific chiller, boiler, fan, and duct network for each of thousands of
buildings (which we do not have the data to size), the "ideal loads" object delivers
exactly enough heating or cooling to hold the zone setpoint, at 100% efficiency.

The consequence is that the simulation meters only what the ideal-loads object and the
internal-gain objects represent:

| End-use | Modeled? | Source object |
|---|---|---|
| Space heating | ✅ | IdealLoads (`DistrictHeating` meter) |
| Space cooling | ✅ | IdealLoads (`DistrictCooling` meter) |
| Lighting | ✅ | `Lights` |
| Plug / equipment | ✅ | `ElectricEquipment` |
| Ventilation **fans** | ❌ zero | (no air-loop fan object) |
| **Pumps** | ❌ zero | (no plant loop) |
| Service hot water (**DHW**) | ❌ zero | (no water-heater object) |
| **Refrigeration** | ❌ zero | (no refrigeration object) |
| **Cooking** / process | ❌ zero | (no process-load object) |

The five ❌ rows are not "small" or "rounded to zero" — they are simply **absent** from
the model. There is no object in the IDF that could produce them.

### 2.2 The simulated total

For each building, the pipeline writes four end-use EUIs (in kWh/m²·yr) and their sum:

```
total_eui_kwh_m2 = heating_eui + cooling_eui + lighting_eui + equipment_eui
```

This identity holds **exactly** in the shipped results (`05_results`) — verified during
the service-loads work: the whole-building total equals the sum of precisely those four
columns, confirming the five other end-uses contribute nothing.

This is the **blue bar** in `eui_sim_vs_reconstructed.png` and the value mapped in every
`*__eui_map.png` and the overview grid.

---

## 3. Reconstructed EUI — adding the missing service loads back

### 3.1 The idea (fraction-split completion)

We know, from large measured-building datasets, roughly what fraction of a given building
type's total energy each end-use represents. For example, a Large Office spends about
30% on heating, 14% on cooling, 12% on lighting, 27% on plug loads — and the remaining
~17% on fans/pumps/DHW/refrigeration/cooking.

If the simulation already gives us the four modeled end-uses, and we know those four
*should* be ~83% of the whole for that building type, then we can **scale up** to infer
the missing ~17% — without simulating it.

### 3.2 The reference: Table 4

The fractions come from **Table 4** of the OpenUBEM deep-research source — *Consolidated
End-Use Energy Fractions by Archetype*, derived from **CBECS-2018** (the U.S. Commercial
Buildings Energy Consumption Survey) and the **PNNL Commercial Prototype Building** models.
It gives, for 11 building archetypes, the percentage split across all nine end-uses (every
row sums to 100%). Examples (% of whole-building site energy):

| Archetype | Heat | Cool | Fans | Pumps | DHW | Light | Equip | Refrig | Cook |
|---|---|---|---|---|---|---|---|---|---|
| Large Office | 30 | 14 | 11 | 3.5 | 1.5 | 12 | 27 | 0.5 | 0.5 |
| Stand-alone Retail | 28 | 13 | 12 | 1.5 | 1.5 | 22 | 18 | 1.5 | 2.5 |
| Supermarket | 9 | 6 | 10 | 1 | 1 | 13 | 8 | **50** | 2 |
| Full-Service Rest. | 12 | 7 | 7 | 1.5 | 8 | 5 | 9 | 15 | **35.5** |
| Mid-Rise Apt. | 28 | 11 | 5 | 1 | 23 | 8 | 22 | 1 | 1 |

(Full 11-row table and per-building-type source citations:
`docs/implementation/serviceLoads/SERVICE_LOADS_coefficients.md`. Machine-readable:
`openubem/data/service_loads/enduse_fractions_table4.json`.)

OpenUBEM's richer archetype vocabulary (e.g. `MediumOffice`, `QuickServiceRestaurant`,
`HighriseApartment`) is mapped onto these 11 rows by a pre-decided mapping table; all 18
archetypes present in the validation matrix map to a Table-4 archetype.

### 3.3 The math

For a building of archetype `A`, with Table-4 fractions `f_*` (as decimals, summing to 1):

```
# 1. What fraction of this archetype's energy is the part we DID simulate?
modeled_frac = f_heat + f_cool + f_lighting + f_equip

# 2. Back out the implied whole-building total from the simulated four end-uses.
E_total_est  = (heating + cooling + lighting + equipment) / modeled_frac

# 3. Each missing end-use is its Table-4 fraction of that estimated whole.
recon_j      = f_j × E_total_est       for j ∈ {fans, pumps, DHW, refrig, cooking}

# 4. The reconstructed whole-building EUI.
total_eui_reconstructed = total_eui_simulated + Σ recon_j      (= E_total_est)
```

**Why anchor on all four modeled end-uses** (step 1–2) rather than just one? Robustness.
Dividing by a single end-use's fraction would amplify any single-end-use error; averaging
over four quantities is far more stable. And `modeled_frac` is never near zero — its
smallest value is the Supermarket at 0.36 (36%) — so the scale-up in step 2 is
numerically safe.

This is the **orange bar** in `eui_sim_vs_reconstructed.png`. The **uplift %** annotation is:

```
uplift% = (reconstructed − simulated) / simulated × 100
```

Because reconstruction only *adds* energy, the orange bar is always ≥ the blue bar, and
the uplift is always positive.

### 3.4 Why the uplift varies so much between cells

The uplift is driven entirely by **how much of each archetype's energy lives in the five
missing end-uses**:

- **Modest uplift (+19 % to +30 %)** — office- and apartment-dominated cells, where
  fans/pumps/DHW are a small-to-moderate slice.
- **Large uplift (up to +72 %)** — cells containing **restaurants (QuickServiceRestaurant)
  or supermarkets**, where cooking + refrigeration + DHW can be ~50–67 % of total energy —
  all of it unsimulated. A handful of such buildings pulls an entire cell's mean up.

This is the meaning of the figure caption *"Food-service uplift ~+203 % inflates cells
with QSR/restaurants."* Aggregate numbers should be read with food-service broken out.

---

## 4. What reconstruction is — and is NOT

| | Simulated | Reconstructed |
|---|---|---|
| Produced by | EnergyPlus physics engine | Deterministic post-processing |
| End-uses | 4 (heat, cool, light, equip) | 9 (the 4 + fans, pumps, DHW, refrig, cook) |
| Re-runs simulation? | — | **No** |
| Changes the IDF / DESIGN? | — | **No** |
| Per-building accuracy | physics-based | average-ratio estimate |
| Best use | what we modeled | a more complete *reported* whole-building total |

**Reconstruction is a reporting enhancement, not a calibration.** It restores energy that
is genuinely missing from the model, giving a more honest whole-building EUI for downstream
use (carbon, benchmarking, stock rollups). But it does **not** make individual buildings
match a reference more closely — because the gap between a modeled building and its
real-world counterpart is dominated by over/under-prediction *inside the four simulated
end-uses* (HVAC configuration, schedules, internal-gain intensities), not by the missing
service loads. (Established in the R6-4B close-out and confirmed by the round-trip
re-evaluation in V16.)

---

## 5. Known limitations of the reconstruction

1. **Refrigeration "case-credit" coupling** — supermarket display cases remove heat from
   the zone, which would feed back into the thermal balance. The additive estimate ignores
   this coupling (reports refrigeration as an energy vector only; no zone feedback).
2. **Static operating conditions** — the fraction split inherits CBECS-2018 average
   operating conditions; it does not model dynamic supply-air/chilled-water resets or
   fan-heat pickup.
3. **CBECS-2018 vintage** — pre-hybrid-work end-use splits; offices may over-weight
   occupant-driven auxiliary loads relative to current operation.
4. **Plausibility band** — a small number of food-service buildings reconstruct above the
   R5 plausibility band (>1000 kWh/m²·yr). These are **reported, never capped**.
5. **Physics-based tables not used** — the alternative method (Tables 1–3: fan/pump sizing,
   DHW coefficients, refrigeration intensities) is out of Phase-1 scope; their numeric cells
   are image-clipped in the source PDF and were not transcribed.

---

## 6. Where this lives in the code & data

| Artifact | Path |
|---|---|
| Coefficient reference (Table 4 + mapping) | `docs/implementation/serviceLoads/SERVICE_LOADS_coefficients.md` |
| Machine-readable fractions | `openubem/data/service_loads/enduse_fractions_table4.json` |
| Reconstruction module | `openubem/results/service_loads.py` |
| Reconstruction CLI | `scripts/reconstruct_service_loads.py` |
| Per-building output (8 152 rows, 9 end-uses) | `docs/validations/overAll/results/r7_service_loads.csv` |
| Full analysis & findings | `docs/validations/overAll/V16_service_loads_reconstruction.md` |
| Comparison figure | `openubem/outputs/comparisons/eui_sim_vs_reconstructed.png` |

---

*OpenUBEM — reporting-layer methodology note. No resimulation, no DESIGN change. 2026-06-17.*
