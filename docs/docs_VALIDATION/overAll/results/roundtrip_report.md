# Level-2 DOE Round-Trip Report (V05b — corrected storeys)

n_pass / n_mapped = **1 / 23**  (+-5% gate, report-only per V-R5-5)

Storeys_heuristic = original `_floor_count_from_zones` value (buggy for DOE prototypes).
Storeys_corrected = geometry-derived from IDF zone names / documented DOE prototype counts.

| Archetype | Stry_h | Stry_c | Ref EUI | OUB EUI | Dev% | Verdict | Ref-H | Ctr-H | Ref-C | Ctr-C | Ref-L | Ctr-L | Ref-E | Ctr-E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| College | 117 | 4 | 317.4 | 495.7 | 56.2 | FAIL | 23.9 | 132.4 | 9.2 | 57.1 | 30.4 | 23.9 | 65.8 | 34.5 |
| FullServiceRestaurant | 3 | 1 | 1063.7 | 1351.7 | 27.1 | FAIL | 121.9 | 32.4 | 22.0 | 274.8 | 10.4 | 72.2 | 233.0 | 296.5 |
| HighriseApartment | 27 | 10 | 889.1 | 139.8 | -84.3 | FAIL | 78.8 | 41.2 | 23.6 | 19.8 | 13.8 | 4.4 | 125.2 | 4.5 |
| Hospital | 55 | 5 | 670.6 | 588.8 | -12.2 | FAIL | 44.6 | 39.8 | 26.6 | 104.1 | 32.7 | 89.2 | 135.3 | 61.4 |
| Laboratory | 3 | 5 | 1015.3 | 717.8 | -29.3 | FAIL | 354.2 | 17.0 | 31.0 | 148.3 | 16.6 | 44.9 | 48.5 | 148.7 |
| LargeDataCenterHighITE | 1 | 1 | 79594.5 | -- | -- | N/A | 0.0 | -- | 4701.6 | -- | 60.3 | -- | 30164.9 | -- |
| LargeDataCenterLowITE | 1 | 1 | 16228.1 | -- | -- | N/A | 0.0 | -- | 1026.0 | -- | 60.3 | -- | 6056.5 | -- |
| LargeHotel | 22 | 6 | 905.6 | 380.7 | -58.0 | FAIL | 34.0 | 41.4 | 34.0 | 64.7 | 20.9 | 48.5 | 163.7 | 35.7 |
| LargeOffice | 3 | 12 | 1006.6 | 373.7 | -62.9 | FAIL | 18.8 | 47.6 | 31.3 | 68.4 | 33.5 | 33.8 | 286.0 | 37.2 |
| MediumOffice | 3 | 3 | 180.5 | 352.6 | 95.3 | FAIL | 23.1 | 44.5 | 7.3 | 60.9 | 9.3 | 33.8 | 36.1 | 37.2 |
| MidriseApartment | 27 | 4 | 313.5 | 351.0 | 12.0 | FAIL | 26.2 | 28.4 | 8.8 | 58.1 | 6.8 | 43.9 | 49.9 | 45.2 |
| Outpatient | 3 | 3 | 562.6 | 459.3 | -18.4 | FAIL | 64.7 | 70.2 | 31.4 | 69.0 | 23.5 | 52.3 | 108.6 | 38.2 |
| QuickServiceRestaurant | 3 | 1 | 1576.3 | 2106.7 | 33.6 | FAIL | 168.8 | 26.3 | 23.2 | 449.1 | 12.7 | 92.8 | 413.0 | 485.3 |
| RetailStandalone | 5 | 1 | 279.8 | 412.1 | 47.3 | FAIL | 55.5 | 16.8 | 8.5 | 78.5 | 21.6 | 64.8 | 23.5 | 46.0 |
| RetailStripmall | 10 | 1 | 298.9 | 399.7 | 33.7 | FAIL | 59.0 | 17.1 | 7.6 | 76.7 | 36.9 | 73.4 | 17.0 | 32.7 |
| SmallDataCenterHighITE | 1 | 1 | 14376.8 | -- | -- | N/A | 0.0 | -- | 777.5 | -- | 60.4 | -- | 5962.0 | -- |
| SmallDataCenterLowITE | 1 | 1 | 5817.8 | 14584.0 | 150.7 | FAIL | 0.0 | 0.0 | 315.1 | 3464.2 | 60.4 | 56.1 | 2393.7 | 3771.7 |
| SmallHotel | 67 | 4 | 340.9 | 325.8 | -4.5 | PASS | 12.5 | 48.7 | 12.9 | 51.9 | 11.0 | 48.5 | 55.5 | 13.8 |
| SmallOffice | 6 | 1 | 76.0 | 310.6 | 308.7 | FAIL | 6.0 | 53.3 | 2.2 | 44.8 | 5.0 | 33.8 | 12.4 | 23.4 |
| SuperMarket | 2 | 1 | 676.0 | 463.3 | -31.5 | FAIL | 2.3 | 72.1 | 15.7 | 67.2 | 133.2 | 45.3 | 41.8 | 46.9 |
| SuperTallBuilding | 72 | 72 | 896.2 | 381.6 | -57.4 | FAIL | 140.7 | 51.4 | 16.5 | 68.4 | 28.1 | 33.8 | 144.7 | 37.2 |
| TallBuilding | 38 | 38 | 664.0 | 375.2 | -43.5 | FAIL | 77.4 | 47.4 | 20.8 | 69.3 | 24.2 | 33.8 | 107.1 | 37.2 |
| Warehouse | 3 | 1 | 128.2 | 56.8 | -55.7 | FAIL | 44.8 | 1.8 | 0.3 | 3.8 | 4.7 | 12.6 | 8.2 | 10.2 |

**Summary:** 1/23 PASS, 19 FAIL, 3 N/A

N/A rows = simulation failed; see failure_diag column in CSV.