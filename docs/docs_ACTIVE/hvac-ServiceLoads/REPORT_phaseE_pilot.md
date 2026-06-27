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
| Heating (elec + gas) | 9.29 |
| Cooling (elec) | 6.26 |
| Lighting (elec) | 3.97 |
| Equipment (elec) | 43.40 |
| **Fans (elec)** | **7.26** |
| **Pumps (elec)** | **0.00** |
| **DHW (gas)** | **0.00** |
| **DHW (elec)** | **31.57** |
| **DHW (combined)** | **31.59** |
| **Cooking (gas + elec)** | **0.00** |
| **Refrigeration (elec)** | **0.00** |
| **Total (all 9 end-uses, D9)** | **103.81** |

### 4.1 Fans + pumps gate (RD6 per-archetype physics check)

| Archetype | Plant type | fans kWh/m² | pumps kWh/m² | f+p kWh/m² | n |
|---|---|---|---|---|---|
| Courthouse | packaged | 34.8 | 0.3 | 35.1 | 1 |
| FullServiceRestaurant | packaged | 29.7 | 0.0 | 29.7 | 2 |
| HighriseApartment | CENTRAL | 2.9 | 3.9 | 6.7 | 10 |
| LargeOffice | CENTRAL | 32.2 | 7.8 | 40.1 | 37 |
| MediumOffice | packaged | 40.7 | 0.0 | 40.7 | 46 |
| MidriseApartment | packaged | 7.1 | 0.0 | 7.1 | 446 |
| PrimarySchool | packaged | 12.9 | 0.0 | 12.9 | 2 |
| QuickServiceRestaurant | packaged | 43.6 | 0.0 | 43.6 | 1 |
| RetailStandalone | packaged | 14.4 | 0.0 | 14.4 | 35 |
| SmallOffice | packaged | 10.2 | 0.0 | 10.2 | 29 |
| SuperMarket | packaged | 7.6 | 0.0 | 7.6 | 1 |
| TallBuilding | CENTRAL | 25.5 | 6.7 | 32.1 | 4 |
| Warehouse | packaged | 0.1 | 0.0 | 0.1 | 1 |

**G2 composite = gates (a) AND (b)** → **PASS**
- Gate (a) central-plant archetypes pumps > 0
- Gate (b) packaged archetypes (PVAV+HW exempt) pumps < 1
- Gate (c) LargeOffice f+p ∈ 12.0–16.0 kWh/m² — REPORT-ONLY (D3: no longer gates; re-anchor band from this distribution)

---

## 5. City-Overall vs EBEWE anchor

| Metric | Value |
|---|---|
| Phase-E la_urban median total_eui | 103.81 kWh/m²/yr |
| LA EBEWE Overall anchor (city-level) | 113.6 kWh/m²/yr |
| **Delta vs EBEWE** | **-8.6%** |
| Phase-D2 la_urban median total_eui (fans excl.) | 72.06 kWh/m²/yr |
| Phase-D2 la_urban median total_eui (fans incl.) | 72.42 kWh/m²/yr |
| Delta Phase-E vs Phase-D2 (fans excl.) | +44.1% |
| Delta Phase-E vs Phase-D2 (fans incl.) | +43.3% |

*Note: Phase-D2 did NOT include pumps/DHW/cooking/refrigeration in the simulated total (those were reporting-layer reconstruction). Phase-E includes all 9 end-uses in total_eui per D9 and DISABLES reconstruction (D8).*

*Phase-D2 adopted baseline (city-level, all 4 LA cells, reconstructed total) was LA Overall −3.7% vs EBEWE.*

---

## 6. Shape gates — CBECS Pacific (report-only per V-R5-5)

| Gate | Phase-E | Phase-D2 (fans excl.) | Delta |
|---|---|---|---|
| NMBE | -17.614%  (False) | -39.280%  (False) | 21.666 pp |
| CV(RMSE) | 58.460%  (False) | 93.071%  (False) | -34.611 pp |
| KS_D | 0.2751  (False) | 0.3162  (False) | -0.0411 |
| R² | 0.9164  (True) | 0.7122  (True) | — |

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
