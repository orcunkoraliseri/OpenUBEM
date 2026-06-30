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
| Comparison figure | `openubem/outputs/comparisons/eui_sim_vs_reconstructed.png` ⚠️ historical — illustrates the §§1–6 reconstruction method (Phase-D2 data, 2026-06-26); **retired in Phase-E** — see §7 and [`outputs/comparisons/README.md`](../../openubem/outputs/comparisons/README.md). Phase-E successor: `phaseE_enduse_breakdown.png`. |

---

## 7. Phase-E — replacing reconstruction with physical simulation

> **Status of this chapter.** §§1–6 above describe the model as it stood in mid-2026:
> `IdealLoadsAirSystem` for HVAC plus a reporting-layer *reconstruction* overlay for the
> five missing end-uses. **Phase-E (2026-06-27) retired both halves of that approach.** This
> chapter explains what replaced them, presents the results, and — importantly — explains a
> counter-intuitive finding: the physically-complete model scores *further* from measured
> benchmarks than the reconstructed one did, and *why that is the correct outcome*.
> Full record: `docs/docs_ACTIVE/hvac-ServiceLoads/REPORT_phaseE_final.md` and the
> decomposition in `docs/docs_ACTIVE/hvac-ServiceLoads/validation-investigate/INVESTIGATION_phaseD2_vs_phaseE_why_D2_closer.md`.

### 7.1 The one-paragraph version

Reconstruction (§3) was always a stopgap: it *estimated* the five missing end-uses from
average fraction tables because EnergyPlus, as configured, could not produce them. Phase-E
removes the need to estimate. It gives every building its **real HVAC system** (central VAV
with chiller + boiler for large offices, packaged rooftop units for small/medium
nonresidential, fan-coil and water-loop heat pumps for large hotels and high-rise
apartments, PTAC kept only for mid-rise residential) and adds **real EnergyPlus objects**
for hot water, cooking, and refrigeration. Now all nine end-uses — including fans and pumps
— are computed by the physics engine. The reconstruction overlay is switched off entirely
(`OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0`). There is no longer a "simulated vs reconstructed"
split: there is one **physically simulated** EUI.

```
Phase-E total = heating + cooling + lighting + equipment
              + fans + pumps + DHW + cooking + refrigeration      (ALL from EnergyPlus)
```

### 7.2 What Phase-E models — compare to the §2.1 table

Every ❌ row from §2.1 is now a ✅, produced by a real object in the IDF rather than added
afterward:

| End-use | §2.1 (IdealLoads) | Phase-E | Phase-E source object |
|---|---|---|---|
| Space heating | ✅ ideal | ✅ physical | archetype HVAC heating coil / hot-water boiler |
| Space cooling | ✅ ideal | ✅ physical | archetype HVAC DX coil / chilled-water chiller |
| Lighting | ✅ | ✅ | `Lights` |
| Plug / equipment | ✅ | ✅ | `ElectricEquipment` |
| Ventilation **fans** | ❌ zero | ✅ | `HVACTemplate` supply/exhaust fans → `Fans:Electricity` |
| **Pumps** | ❌ zero | ✅ | hot-water + chilled-water plant pumps (central-plant archetypes) |
| Service hot water (**DHW**) | ❌ zero | ✅ | `WaterHeater:Mixed` + `WaterUse:Equipment` |
| **Refrigeration** | ❌ zero | ✅ | `Refrigeration:Case` + `Refrigeration:CompressorRack` (SuperMarket) |
| **Cooking** / process | ❌ zero | ✅ | `ZoneVentilation` kitchen exhaust + `OtherEquipment` process load |

This required a re-simulation of all 8,160 buildings and an authorized deviation from the
Phase-1 IdealLoads mandate (recorded in the Phase-E plan). It is **not** a reporting-layer
change — it is a different simulation.

### 7.3 Performance — Phase-E vs the reconstructed baseline

City-Overall median total EUI (kWh/m²·yr) against measured benchmarks (NYC LL84 / LA EBEWE /
Austin CBECS-WSC proxy). "Phase-D2 reconstructed" = the §3 overlay method (the previous
production model):

| City | Measured | Phase-D2 reconstructed | Phase-E physical |
|---|---|---|---|
| NYC | 219.2 | 223.8 (**+2.1 %**) | 165.7 (**−24.4 %**) |
| LA | 113.6 | 109.4 (−3.7 %) | 107.2 (−5.6 %) |
| Austin | 162.0 | 148.1 (−8.6 %) | 120.4 (−25.7 %) |

At face value Phase-E looks **worse**: NYC and Austin move from near-perfect to ~−25 %. But
two other metrics move the opposite way:

| Metric | Phase-D2 reconstructed | Phase-E physical |
|---|---|---|
| Distribution shape, R² (NYC / LA / Austin) | ~0.71 / ~0.71 / ~0.71 | **0.895 / 0.924 / 0.718** |
| End-use attribution | fans/pumps inferred from a national table | **physically computed per building** |
| Fitted parameters | none (but a strong CBECS prior) | none |

R² (how well the model ranks high- vs low-energy buildings) jumps sharply: the
archetype-appropriate HVAC and real service loads inject genuine per-building variation that
a smooth multiplier could not. The model now puts the right buildings in the right order —
it just sits low on the absolute level. Phase-E per-end-use medians (success rows, excl.
`OpenUBEMUnknown`):

| City | Heat | Cool | Light | Equip | Fans | Pumps | DHW | Cook | Refrig | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| NYC | 60.7 | 12.2 | 26.5 | 43.4 | 15.0 | 0.0 | 6.3 | 0.0 | 0.0 | 165.7 |
| LA | 13.9 | 4.8 | 4.0 | 43.4 | 6.8 | 0.0 | 33.3 | 0.0 | 0.0 | 107.2 |
| Austin | 15.3 | 28.2 | 26.5 | 27.8 | 11.7 | 0.0 | 4.4 | 0.0 | 0.0 | 120.4 |

(Pumps/cooking/refrigeration read 0.0 at the city median because they apply only to
central-plant / food-service / supermarket archetypes — a minority of buildings. They are
non-zero at the archetype level: e.g. LargeOffice pumps ≈ 9, SuperMarket refrigeration is
substantial.)

### 7.4 The key methodological point — why the *more complete* model scores *worse*

This is the part worth understanding, because it is easy to misread the table in §7.3 as
"reconstruction was better." It was not. Here is the decomposition, on the **same 8,160
buildings matched one-to-one**, for a NYC office (measured 184):

| Energy piece | Phase-D2 reconstructed | Phase-E physical |
|---|---|---|
| Heating | **122** ← far too high | **55** ← realistic |
| Cooling + Lighting + Equipment | 68 | 68 (identical) |
| Service loads | 26 (estimated overlay) | 22 (physically simulated) |
| **TOTAL** | **217 (+18 %)** | **147 (−20 %)** |

Two facts fall out of this table:

1. **The service-load layers are nearly equal (26 vs 22).** Removing the reconstruction
   overlay did *not* drop the total — it was replaced by physically-simulated service loads
   of almost the same size. (City-wide: NYC overlay +41 vs physical +37; LA +33 vs +39;
   Austin +27.5 vs +16.3.) So the regression is **not** "we stopped adding the missing
   loads."
2. **The entire drop is heating** (122 → 55, a 67-point fall that accounts for ~all of the
   70-point total drop). It appeared the moment each archetype switched off the simplified
   blanket-PTAC system onto its real HVAC. Cooling/lighting/equipment did not move at all.

**So why was the reconstructed model closer to measured?** Because it contained a large
*compensating error*. Think of adding up a grocery bill whose true total is \$184: if you
over-count one item by \$70 and forget a \$70 item, you still land on \$184 — right answer,
wrong twice. Phase-D2's simplified PTAC heating was the \$70 over-count; the unmodeled
"Other" loads (elevators, IT/process, miscellaneous plug loads — see §4 and the R6-4B
close-out) were the \$70 it forgot. The two cancelled, and the total *looked* accurate.
Phase-E fixed the heating, so the forgotten "Other" loads are no longer hidden — and the
total honestly sits below measured.

**Is the new, lower heating itself a mistake?** No — and this is the check that settles the
interpretation. Compared against the DOE reference prototypes the archetypes are built from
(ASHRAE 90.1-2022, in Buffalo — a climate *colder* than NYC, so heating there should be
*higher* if anything):

| Office archetype | DOE prototype heating (Buffalo) | Phase-D2 (NYC) | Phase-E (NYC) |
|---|---|---|---|
| SmallOffice | 6.0 | 132 (~22×) | 55 (~9×) |
| MediumOffice | 23.1 | 81 (~3.5×) | 56 (~2.4×) |
| LargeOffice | 18.8 | 69 (~3.7×) | 51 (~2.7×) |

Phase-E heating is **above** the reference prototype, never below. A model that, if anything,
still over-heats cannot be under-predicting the total *because of heating*. Therefore the
remaining gap is genuinely the unmodeled "Other" category — exactly the residual the R6-4B
work identified and that no Phase-1 object can produce.

### 7.5 Three ways to report a whole-building EUI — updating §4

The §4 "simulated vs reconstructed" table now has a third, preferred column:

| | Simulated (§2) | Reconstructed (§3) | **Physical (Phase-E)** |
|---|---|---|---|
| HVAC | IdealLoads, 100 % efficient | IdealLoads | **real archetype system** |
| End-uses | 4 | 9 (4 simulated + 5 estimated) | **9, all simulated** |
| Service loads | absent | average-ratio estimate | **physically computed** |
| Re-runs simulation? | — | No | **Yes (full re-sim)** |
| Distribution shape (R²) | n/a | low | **high (0.72–0.92)** |
| Closeness to measured *level* | low | high (by compensation) | lower, but honest |
| Best use | what we modeled | a quick completed total | **the production baseline** |

The headline lesson for anyone reading the figures: **closer to measured ≠ more correct.**
The reconstructed bar matched the anchor by stacking a heating over-prediction on top of an
estimated overlay; the physical bar is built from defensible per-end-use physics and reveals,
rather than hides, the one category the model legitimately cannot produce.

### 7.6 What this means going forward

- **Phase-E is the adopted physical baseline.** Its end-use structure is faithful; its only
  weakness is an absolute-level under-prediction driven by the unmodeled "Other" loads.
- **The remaining gap is not closable without fitting.** Adding "Other" means tuning plug
  loads until the total matches CBECS — curve-fitting to the answer, which violates the
  zero-fitted-parameters rule. Per R6-4B (user-ratified, externally corroborated) this is
  **accepted and documented, not calibrated away.**
- **There is no honest lever that improves the *level*.** The only physically-correct
  adjustment still available — bringing heating fully down to prototype levels — would push
  the total *further* below measured, because the still-elevated heating is partly what holds
  the total up. The −24 % city gap should therefore be read as a *lower bound* on the true
  structural "Other" deficit, not its full size.
- **One open, non-fitting question remains** (diagnostic, not blocking): why Phase-E heating
  sits ~3–9× the DOE prototype. This is an envelope/infiltration question (OSM-derived
  geometry on a leakier-than-new-code envelope), is the same upward direction across all
  phases, and is entangled with the long-standing LA hot-bias. Resolving it would make the
  model *more* faithful while making the scorecard *look* worse — an "understand the physics"
  task, not a "match the benchmark" one.

---

*OpenUBEM — methodology note in two parts. §§1–6: reporting-layer reconstruction (no
resimulation, no DESIGN change; 2026-06-17). §7: Phase-E physical simulation — full re-sim
with an authorized DESIGN deviation from the Phase-1 IdealLoads mandate (2026-06-28).*
