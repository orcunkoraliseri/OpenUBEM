# R6-4 Level-2 Gap Decomposition

Per-end-use contribution to total deviation: `(counter_i - ref_i) / ref_total × 100`.
Contributions sum to total dev% by construction.

| Archetype | Dev% | Verdict | ΔHeat | ΔCool | ΔLight | ΔEquip | ΔOther | DomEU |
|---|---:|---|---:|---:|---:|---:|---:|---|
| SmallOffice | +308.7 | FAIL | +62.3 | +56.1 | +37.9 | +14.4 | +138.0 | heat |
| SmallDataCenterLowITE | +150.7 | FAIL | +0.0 | +54.1 | -0.1 | +23.7 | +72.9 | cool |
| MediumOffice | +95.3 | FAIL | +11.8 | +29.7 | +13.6 | +0.6 | +39.7 | cool |
| HighriseApartment | -84.3 | FAIL | -4.2 | -0.4 | -1.1 | -13.6 | -65.0 | equip |
| LargeOffice | -62.9 | FAIL | +2.9 | +3.7 | +0.0 | -24.7 | -44.7 | equip |
| LargeHotel | -58.0 | FAIL | +0.8 | +3.4 | +3.0 | -14.1 | -51.1 | equip |
| SuperTallBuilding | -57.4 | FAIL | -10.0 | +5.8 | +0.6 | -12.0 | -41.9 | equip |
| College | +56.2 | FAIL | +34.2 | +15.1 | -2.0 | -9.8 | +18.8 | heat |
| Warehouse | -55.7 | FAIL | -33.5 | +2.7 | +6.2 | +1.5 | -32.5 | heat |
| RetailStandalone | +47.3 | FAIL | -13.8 | +25.0 | +15.5 | +8.0 | +12.6 | cool |
| TallBuilding | -43.5 | FAIL | -4.5 | +7.3 | +1.5 | -10.5 | -37.2 | equip |
| RetailStripmall | +33.7 | FAIL | -14.0 | +23.1 | +12.2 | +5.2 | +7.2 | cool |
| QuickServiceRestaurant | +33.6 | FAIL | -9.0 | +27.0 | +5.1 | +4.6 | +6.0 | cool |
| SuperMarket | -31.5 | FAIL | +10.3 | +7.6 | -13.0 | +0.8 | -37.2 | light |
| Laboratory | -29.3 | FAIL | -33.2 | +11.6 | +2.8 | +9.9 | -20.3 | heat |
| FullServiceRestaurant | +27.1 | FAIL | -8.4 | +23.8 | +5.8 | +6.0 | -0.0 | cool |
| Outpatient | -18.4 | FAIL | +1.0 | +6.7 | +5.1 | -12.5 | -18.6 | equip |
| Hospital | -12.2 | FAIL | -0.7 | +11.6 | +8.4 | -11.0 | -20.4 | cool |
| MidriseApartment | +12.0 | FAIL | +0.7 | +15.7 | +11.9 | -1.5 | -14.7 | cool |
| SmallHotel | -4.5 | PASS | +10.6 | +11.4 | +11.0 | -12.2 | -25.3 | equip |

**Key:** Dev% = (counter_total − ref_total)/ref_total × 100.  ΔX = (counter_X − ref_X)/ref_total × 100.  Sum(ΔHeat+ΔCool+ΔLight+ΔEquip+ΔOther) = Dev%.

N non-N/A archetypes: 20  |  N/A (thermal runaway): 3