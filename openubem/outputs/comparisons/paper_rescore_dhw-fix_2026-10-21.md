# Paper re-score on the adopted U.S. fleet

- **Population:** 8,139 buildings in the input, 8,139 with a successful simulation; pooled EUI 154.097 kWh/m2.
- **Source vintage:** adopted fleet of 2026-09-30 (three rulings) with the double-counted district hot water removed (T13, 2026-10-21), per-building table `paper_adopted_fleet_dhw-fix_per_building_2026-10-21.csv`.
- **City Overall** = median total EUI of the city's buildings, OpenUBEMUnknown excluded, against the measured city anchor.
- **Archetype R2** = Pearson R2 of per-archetype mean EUI against CBECS 2018 regional PBA means (apartments, data centres, OpenUBEMUnknown excluded; PBA types with fewer than 10 CBECS records dropped).
- **Density cell** = per-building deviation of simulated EUI from the CBECS 2018 weighted mean of its type in the city's census region (not a measured per-cell anchor: none exists). Outliers are not drawn in the figure.

## City anchor comparison

| city | segment | n | model_median | measured | error_pct |
|---|---|---|---|---|---|
| nyc | Office | 2540 | 141.3 | 183.9 | -23.2 |
| nyc | Multifamily | 1036 | 207.6 | 226.2 | -8.2 |
| nyc | Overall (excl. Unknown n=558) | 3738 | 153.9 | 219.2 | -29.8 |
| la | Office | 362 | 126.9 | 121.5 | 4.4 |
| la | Multifamily | 1775 | 108.7 | 115.8 | -6.1 |
| la | Warehouse | 33 | 23.1 | 33.9 | -31.8 |
| la | Overall (excl. Unknown n=19) | 2309 | 110.0 | 113.6 | -3.2 |
| austin | Office | 1238 | 111.8 | 162.3 | -31.1 |
| austin | Overall (excl. Unknown n=73) | 1442 | 114.3 | 162.0 | -29.4 |

## CBECS archetype gates

| city | CBECS region | n | R2 (archetype) | NMBE % |
|---|---|---|---|---|
| nyc | middle_atlantic | 3260 | 0.8818 | -21.429 |
| la | pacific | 553 | 0.9003 | -25.952 |
| austin | west_south_central | 1476 | 0.715 | -18.687 |

## Deviation by density cell (median, quartiles in the JSON)

| city | density | n | median_err_pct | q1_err_pct | q3_err_pct |
|---|---|---|---|---|---|
| nyc | centre | 691 | -37.3 | -50.4 | -24.0 |
| nyc | urban | 1520 | -45.1 | -48.3 | -41.2 |
| nyc | suburban | 320 | -40.5 | -45.7 | -36.5 |
| nyc | rural | 170 | -45.4 | -50.0 | -37.6 |
| la | centre | 183 | -7.7 | -40.6 | 20.1 |
| la | urban | 158 | -9.1 | -40.4 | 15.3 |
| la | suburban | 58 | -38.9 | -46.8 | -20.5 |
| la | rural | 134 | -17.8 | -31.0 | -3.9 |
| austin | centre | 368 | -18.6 | -40.9 | 5.6 |
| austin | urban | 404 | -37.1 | -41.0 | -24.8 |
| austin | suburban | 411 | -37.5 | -41.4 | -23.7 |
| austin | rural | 220 | -42.6 | -48.2 | -35.7 |

Figure: `openubem/outputs/paper_error_by_density_cell_dhw-fix.png`.
