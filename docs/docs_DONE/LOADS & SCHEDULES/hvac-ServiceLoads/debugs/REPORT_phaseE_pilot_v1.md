# REPORT — Phase-E Pilot: la_urban 1-cell re-sim (CP-D)

- **Date:** 2026-06-26
- **Cell:** la_urban  (34.0584°N, −118.3040°W) r=500 m
- **Phase-E baseline:** archetype HVAC (central VAV / PSZ / FCU / WLHP) + physical DHW + cooking + refrigeration; reconstruction DISABLED (T15 D8).
- **Plan:** `docs/docs_ACTIVE/hvac-ServiceLoads/PLAN_phaseE_full_realism.md` T16 / CP-D
- **Status:** STOP-AND-REPORT (CP-D hard gate) — awaiting manager Go/No-Go on fan-out.

---

## 1. S0 — Pre-flight wiring proof: PASS


| Archetype | Phase-E object | Present |
|---|---|---|
| LargeOffice | `HVACTemplate:Zone:VAV` | FOUND |
| LargeOffice | `HVACTemplate:System:VAV` | FOUND |
| LargeOffice | `HVACTemplate:Plant:ChilledWaterLoop` | FOUND |
| LargeOffice | `HVACTemplate:Plant:HotWaterLoop` | FOUND |
| LargeOffice | `WaterHeater:Mixed` | FOUND |
| FullServiceRestaurant | `WaterHeater:Mixed` | FOUND |
| FullServiceRestaurant | `GasEquipment` | FOUND |
| FullServiceRestaurant | `ZoneVentilation:DesignFlowRate` | FOUND |
| SuperMarket | `Refrigeration:Case` | FOUND |
| SuperMarket | `Refrigeration:CompressorRack` | FOUND |
| SuperMarket | `WaterHeater:Mixed` | FOUND |


All three fixture archetypes (LargeOffice → central VAV; FullServiceRestaurant → cooking gas + DHW; SuperMarket → Refrigeration:Case + Rack) confirmed before cluster ship.

---

## 2. Archetype composition — la_urban

| Archetype | Count |
|---|---|
| MidriseApartment | 446 |
| MediumOffice | 46 |
| LargeOffice | 37 |
| RetailStandalone | 35 |
| SmallOffice | 29 |
| HighriseApartment | 10 |
| TallBuilding | 4 |
| FullServiceRestaurant | 2 |
| PrimarySchool | 2 |
| SuperMarket | 1 |
| QuickServiceRestaurant | 1 |
| Warehouse | 1 |
| Courthouse | 1 |

Central-plant commercial archetypes confirmed present (LargeOffice, TallBuilding, etc.). FullServiceRestaurant + QuickServiceRestaurant confirmed. SuperMarket present (n≥1).

---

## 3. Simulation success

| Metric | Value | Gate |
|---|---|---|
| Buildings generated | 618 | — |
| E+ simulations succeeded | 617 (99.8%) | ≥Phase-D rate (100%) |
| Phase-D2 la_urban success rate | 618/618 (100.0%) | baseline |

### Failed buildings
| osm_id | Archetype | Error |
|---|---|---|
| `way/402215469` | Warehouse |  |

---

## 4. Per-end-use EUI (Phase-E median, la_urban success rows, OpenUBEMUnknown excluded)

| End-use | Phase-E median kWh/m²/yr |
|---|---|
| Heating (elec + gas) | 10.37 |
| Cooling (elec) | 6.26 |
| Lighting (elec) | 3.97 |
| Equipment (elec) | 43.40 |
| **Fans (elec)** | **7.32** |
| **Pumps (elec)** | **0.00** |
| **DHW (gas)** | **0.00** |
| **DHW (elec)** | **31.57** |
| **DHW (combined)** | **31.59** |
| **Cooking (gas + elec)** | **0.00** |
| **Refrigeration (elec)** | **0.00** |
| **Total (all 9 end-uses, D9)** | **104.68** |

### 4.1 Fans + pumps band check (RESULT_02 Part C: 12–16 kWh/m²)

Fans + pumps median EUI: **7.32 kWh/m²/yr** vs acceptance band 12.0–16.0 kWh/m² → **OUTSIDE BAND — flag for manager**

---

## 5. City-Overall vs EBEWE anchor

| Metric | Value |
|---|---|
| Phase-E la_urban median total_eui | 104.68 kWh/m²/yr |
| LA EBEWE Overall anchor (city-level) | 113.6 kWh/m²/yr |
| **Delta vs EBEWE** | **-7.9%** |
| Phase-D2 la_urban median total_eui (fans excl.) | 72.06 kWh/m²/yr |
| Phase-D2 la_urban median total_eui (fans incl.) | 72.42 kWh/m²/yr |
| Delta Phase-E vs Phase-D2 (fans excl.) | +45.3% |
| Delta Phase-E vs Phase-D2 (fans incl.) | +44.5% |

*Note: Phase-D2 did NOT include pumps/DHW/cooking/refrigeration in the simulated total (those were reporting-layer reconstruction). Phase-E includes all 9 end-uses in total_eui per D9 and DISABLES reconstruction (D8).*

*Phase-D2 adopted baseline (city-level, all 4 LA cells, reconstructed total) was LA Overall −3.7% vs EBEWE.*

---

## 6. Shape gates — CBECS Pacific (report-only per V-R5-5)

| Gate | Phase-E | Phase-D2 (fans excl.) | Delta |
|---|---|---|---|
| NMBE | -3.125%  (True) | -39.280%  (False) | 36.155 pp |
| CV(RMSE) | 58.195%  (False) | 93.071%  (False) | -34.876 pp |
| KS_D | 0.3183  (False) | 0.3162  (False) | 0.0021 |
| R² | 0.4035  (False) | 0.7122  (True) | — |

*CV(RMSE) and KS remain structurally unfixed (archetype-deterministic UBEM vs. per-building CBECS survey; §4 REPORT_phaseD_final). Gate status is report-only.*

---

## 7. SuperMarket refrigeration — R-CP-B-1 watch-item

Expected plausible band: 100.0–350.0 kWh/m²/yr (cp-B post-fix: 100.4 kWh/m² on synthetic Chicago fixture).

| osm_id | Refrig EUI kWh/m²/yr | Total EUI kWh/m²/yr | Assessment |
|---|---|---|---|
| `way/376149058` | 115.9 | 311.4 | PLAUSIBLE |

*LOW = below 100.0 kWh/m²/yr; plausible real climate (LA mild → lower rack COP degradation vs Chicago).*
*Per R-CP-B-1 ruling: if result is LOW vs reconstruction benchmark (~309 kWh/m²), flag for manager calibration decision at CP-D.*

---

## 8. CP-D manager decision items

1. **Go/No-Go on fan-out (T17).** Sim-success rate, fans+pumps band result, and EBEWE delta above.
2. **SuperMarket refrigeration calibration.** If refrigeration EUI is materially below the 100–350 kWh/m² band, per R-CP-B-1 ruling, revisit case parameters before fan-out.
3. **Fans+pumps band.** If outside 12–16 kWh/m², investigate before fan-out.

---

*STOP AT CP-D. No fan-out (T17) without manager greenlight.*
