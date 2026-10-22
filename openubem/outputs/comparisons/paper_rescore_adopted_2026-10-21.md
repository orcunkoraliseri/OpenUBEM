# Paper re-score on the adopted U.S. fleet

- **Population:** 8,139 buildings in the input, 8,139 with a successful simulation; pooled EUI 171.383 kWh/m2.
- **Source vintage:** adopted fleet of 2026-09-30 (three rulings), per-building table `paper_adopted_fleet_per_building_2026-10-21.csv`.
- **City Overall** = median total EUI of the city's buildings, OpenUBEMUnknown excluded, against the measured city anchor.
- **Archetype R2** = Pearson R2 of per-archetype mean EUI against CBECS 2018 regional PBA means (apartments, data centres, OpenUBEMUnknown excluded; PBA types with fewer than 10 CBECS records dropped).
- **Density cell** = per-building deviation of simulated EUI from the CBECS 2018 weighted mean of its type in the city's census region (not a measured per-cell anchor: none exists). Outliers are not drawn in the figure.

## City anchor comparison

| city | segment | n | model_median | measured | error_pct |
|---|---|---|---|---|---|
| nyc | Office | 2540 | 142.7 | 183.9 | -22.4 |
| nyc | Multifamily | 1036 | 244.9 | 226.2 | 8.3 |
| nyc | Overall (excl. Unknown n=558) | 3738 | 156.5 | 219.2 | -28.6 |
| la | Office | 362 | 128.5 | 121.5 | 5.7 |
| la | Multifamily | 1775 | 140.8 | 115.8 | 21.6 |
| la | Warehouse | 33 | 23.6 | 33.9 | -30.4 |
| la | Overall (excl. Unknown n=19) | 2309 | 140.6 | 113.6 | 23.8 |
| austin | Office | 1238 | 113.0 | 162.3 | -30.4 |
| austin | Overall (excl. Unknown n=73) | 1442 | 116.2 | 162.0 | -28.3 |

## CBECS archetype gates

| city | CBECS region | n | R2 (archetype) | NMBE % |
|---|---|---|---|---|
| nyc | middle_atlantic | 3260 | 0.8741 | -19.876 |
| la | pacific | 553 | 0.9016 | -24.101 |
| austin | west_south_central | 1476 | 0.7021 | -16.71 |

## Deviation by density cell (median, quartiles in the JSON)

| city | density | n | median_err_pct | q1_err_pct | q3_err_pct |
|---|---|---|---|---|---|
| nyc | centre | 691 | -35.7 | -49.9 | -17.3 |
| nyc | urban | 1520 | -44.5 | -47.7 | -40.6 |
| nyc | suburban | 320 | -39.9 | -45.1 | -35.9 |
| nyc | rural | 170 | -44.8 | -49.4 | -37.0 |
| la | centre | 183 | -6.4 | -39.6 | 22.3 |
| la | urban | 158 | -7.8 | -38.7 | 21.2 |
| la | suburban | 58 | -38.1 | -46.0 | -19.6 |
| la | rural | 134 | -17.0 | -30.2 | -2.6 |
| austin | centre | 368 | -18.0 | -40.2 | 12.2 |
| austin | urban | 404 | -36.4 | -40.3 | -24.2 |
| austin | suburban | 411 | -36.7 | -40.8 | -23.0 |
| austin | rural | 220 | -41.9 | -47.5 | -35.0 |

Figure: `openubem/outputs/paper_error_by_density_cell.png`.
