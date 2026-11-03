# V19 Phase-C Comparison Tables

## City × Segment (success rows; reconstructed total EUI vs measured and V17 old model)

| city | segment | n | model_recon_median | model_4eu_median | p25_recon | p75_recon | measured | delta_vs_measured_pct | v17_old_model | delta_vs_v17old_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nyc | Office | 2569 | 251.37 | 212.76 | 228.32 | 272.77 | 183.9 | 36.7 | 183.3 | 37.1 |
| nyc | Multifamily | 1036 | 227.74 | 157.14 | 214.14 | 240.24 | 226.2 | 0.7 | 302.0 | -24.6 |
| nyc | Overall (excl. OpenUBEMUnknown n=558) | 3745 | 241.13 | 195.63 | 220.29 | 263.77 | 219.2 | 10.0 | 246.9 | -2.3 |
| la | Office | 369 | 216.73 | 180.67 | 193.22 | 283.21 | 121.5 | 78.4 | 208.9 | 3.7 |
| la | Multifamily | 1775 | 153.91 | 106.2 | 148.9 | 170.32 | 115.8 | 32.9 | 153.3 | 0.4 |
| la | Warehouse | 38 | 56.01 | 38.09 | 45.18 | 69.3 | 33.9 | 65.2 | 64.1 | -12.6 |
| la | Overall (excl. OpenUBEMUnknown n=19) | 2314 | 157.65 | 108.94 | 149.6 | 188.18 | 113.6 | 38.8 | 158.6 | -0.6 |
| austin | Office | 1244 | 229.03 | 193.45 | 208.39 | 253.96 | 162.3 | 41.1 | 187.6 | 22.1 |
| austin | Overall (excl. OpenUBEMUnknown n=73) | 1447 | 230.31 | 194.83 | 206.64 | 267.14 | 162.0 | 42.2 | 199.8 | 15.3 |

## Per-Archetype National (all 12 cells pooled, success rows)

| archetype_id | n | model_recon_median | espm_median | delta_vs_espm_pct | v17_old_model | delta_vs_v17old_pct | low_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MediumOffice | 946 | 220.14 | 166.9 | 31.9 | 160.3 | 37.3 | False |
| SmallOffice | 2848 | 254.26 | 166.9 | 52.3 | 190.3 | 33.6 | False |
| LargeOffice | 388 | 214.59 | 166.9 | 28.6 | 229.8 | -6.6 | False |
| MidriseApartment | 2821 | 173.75 | 187.9 | -7.5 | 228.8 | -24.1 | False |
| RetailStandalone | 140 | 285.36 | 162.1 | 76.0 | 286.7 | -0.5 | False |
| Warehouse | 38 | 56.01 | 71.6 | -21.8 | 64.1 | -12.6 | False |
| SuperMarket | 5 | 597.89 | 618.3 | -3.3 | 631.5 | -5.3 | True |
| FullServiceRestaurant | 33 | 1010.3 | 1027.2 | -1.6 | 2158.5 | -53.2 | False |
| QuickServiceRestaurant | 50 | 1423.63 | 1270.3 | 12.1 | 3307.9 | -57.0 | False |
| PrimarySchool | 11 | 320.67 | 153.0 | 109.6 | 289.4 | 10.8 | True |
