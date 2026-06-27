# NYC Local Law 84 Benchmarking Measured EUI Statistics

This report presents measured Building Energy Use Intensity (EUI) statistics for New York City, processed directly from the official Local Law 84 (LL84) benchmarking disclosure database. These distributions serve as ground-truth targets for validating urban building energy models (UBEM) like OpenUBEM in ASHRAE Climate Zone 4A (New York City).

---

## 1. Dataset Metadata & Information

* **Dataset Official Name:** `NYC Building Energy and Water Data Disclosure for Local Law 84 (2023-Present)`
* **Source Agency:** NYC Department of Buildings (DOB) & U.S. Environmental Protection Agency (EPA) Portfolio Manager
* **Most Recent Calendar Year of Data:** **Calendar Year 2024** (Reported/Updated in 2024-2025)
* **Dataset Identifier / ID:** `5zyy-y8am`
* **Download URL:** [https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-/5zyy-y8am](https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-/5zyy-y8am)
* **Total Dataset Properties (All Years):** **103,259 properties** (as of June 2026)
  * *Calendar Year 2024:* 39,090 properties
  * *Calendar Year 2023:* 33,684 properties
  * *Calendar Year 2022:* 30,485 properties
* **Target Columns for EUI Analysis:**
  * **Weather-Normalized Site EUI:** `Weather Normalized Site EUI (kBtu/ft²)` (FieldName: `weather_normalized_site_eui`)
  * **Weather-Normalized Source EUI:** `Weather Normalized Source EUI (kBtu/ft²)` (FieldName: `weather_normalized_source`)
  * **Standard Site EUI (Unnormalized):** `Site EUI (kBtu/ft²)` (FieldName: `site_eui_kbtu_ft`)
  * **Standard Source EUI (Unnormalized):** `Source EUI (kBtu/ft²)` (FieldName: `source_eui_kbtu_ft`)

---

## 2. Data Cleaning & Outlier Treatment Methodology

Because the benchmarking database consists of self-reported entries via ENERGY STAR Portfolio Manager, it contains significant reporting errors (e.g., negative values, units entered in Wh instead of kWh or kBtu instead of MBtu, leading to values in the millions). 
To compute a scientifically valid **Mean** and representative distributions, standard cleaning criteria were applied to filter out extreme outliers:
* **Cleaning Filter:** Only properties with a Site EUI between **0.1 and 1,000 kBtu/ft²·yr** were included.
* **Uncleaned / Raw Comparison:** Raw, uncleaned stats are provided in Section 4 to show the impact of outliers on the mean.

---

## 3. Measured EUI Distributions by Primary Property Type (Cleaned)

All EUI values are reported in both the original unit (**kBtu/ft²·yr**) and converted to **kWh/m²·yr** using the exact conversion factor:
$$\text{1 kBtu/ft²·yr} = 3.15459\text{ kWh/m²·yr}$$

### A. Calendar Year 2024 — Standard Site EUI (Cleaned)
This table summarizes the actual, measured site energy consumption from utility bills.

| Property Type | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Office** | 2,343 | 65.79 | 43.00 | **58.30** | 77.10 | 207.53 | 135.65 | **183.91** | 243.22 | NYC LL84 CY2024 Disclosure |
| **Retail Store** | 312 | 76.51 | 41.82 | **61.55** | 86.25 | 241.35 | 131.94 | **194.17** | 272.08 | NYC LL84 CY2024 Disclosure |
| **Restaurant** * | 15 | 207.21 | 79.25 | **119.80** | 335.90 | 653.65 | 250.00 | **377.92** | 1,059.63 | NYC LL84 CY2024 Disclosure |
| **Multifamily Housing** ** | 20,326 | 75.43 | 53.80 | **71.70** | 89.90 | 237.95 | 169.72 | **226.18** | 283.60 | NYC LL84 CY2024 Disclosure |
| **Hotel** | 665 | 93.58 | 67.10 | **86.50** | 111.00 | 295.20 | 211.67 | **272.87** | 350.16 | NYC LL84 CY2024 Disclosure |
| **Non-Refrigerated Warehouse** | 428 | 39.33 | 16.28 | **31.30** | 52.02 | 124.08 | 51.34 | **98.74** | 164.12 | NYC LL84 CY2024 Disclosure |
| **Hospital** | 103 | 239.67 | 107.40 | **230.30** | 295.45 | 756.06 | 338.80 | **726.50** | 932.02 | NYC LL84 CY2024 Disclosure |
| **Medical Office** | 125 | 95.36 | 58.10 | **80.60** | 110.70 | 300.83 | 183.28 | **254.26** | 349.21 | NYC LL84 CY2024 Disclosure |
| **K-12 School** | 1,837 | 61.42 | 48.60 | **59.50** | 72.00 | 193.76 | 153.31 | **187.70** | 227.13 | NYC LL84 CY2024 Disclosure |
| **Supermarket/Grocery** | 108 | 188.52 | 144.50 | **190.50** | 226.13 | 594.70 | 455.84 | **600.95** | 713.33 | NYC LL84 CY2024 Disclosure |
| **Overall (All Property Types)** | 30,325 | 77.35 | 49.50 | **69.50** | 90.70 | 244.01 | 156.15 | **219.24** | 286.12 | NYC LL84 CY2024 Disclosure |

*\* Restaurant counts include self-selected "Restaurant", "Other - Restaurant/Bar", and "Fast Food Restaurant" properties to maintain a minimally viable sample size. Due to the small sample size (N=15), use caution when interpreting restaurant results.*
*\*\* Multifamily Housing combines all mid-rise and high-rise apartments, as the raw dataset does not break out residential buildings by height or storeys.*

### B. Calendar Year 2024 — Weather-Normalized Site EUI (Cleaned)
Weather-normalized EUI adjusts the actual energy use to a standardized climate year, useful for eliminating year-to-year temperature fluctuations.

| Property Type | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Office** | 2,228 | 67.20 | 43.90 | **59.90** | 79.20 | 211.98 | 138.49 | **188.96** | 249.84 | NYC LL84 CY2024 Disclosure |
| **Retail Store** | 310 | 78.15 | 42.98 | **62.35** | 88.42 | 246.52 | 135.57 | **196.69** | 278.94 | NYC LL84 CY2024 Disclosure |
| **Restaurant** | 14 | 219.91 | 82.45 | **157.65** | 339.00 | 693.72 | 260.10 | **497.32** | 1,069.41 | NYC LL84 CY2024 Disclosure |
| **Multifamily Housing** | 19,571 | 77.61 | 54.90 | **73.90** | 92.60 | 244.83 | 173.19 | **233.12** | 292.12 | NYC LL84 CY2024 Disclosure |
| **Hotel** | 627 | 96.08 | 69.90 | **88.10** | 114.20 | 303.10 | 220.51 | **277.92** | 360.25 | NYC LL84 CY2024 Disclosure |
| **Non-Refrigerated Warehouse** | 416 | 42.00 | 17.48 | **33.80** | 55.92 | 132.49 | 55.13 | **106.63** | 176.42 | NYC LL84 CY2024 Disclosure |
| **Hospital** | 86 | 245.59 | 110.27 | **232.55** | 296.25 | 774.75 | 347.87 | **733.60** | 934.55 | NYC LL84 CY2024 Disclosure |
| **Medical Office** | 119 | 96.31 | 59.65 | **83.10** | 115.35 | 303.82 | 188.17 | **262.15** | 363.88 | NYC LL84 CY2024 Disclosure |
| **K-12 School** | 1,720 | 64.16 | 50.50 | **61.95** | 75.73 | 202.40 | 159.31 | **195.43** | 238.88 | NYC LL84 CY2024 Disclosure |
| **Supermarket/Grocery** | 105 | 192.89 | 148.30 | **194.70** | 229.40 | 608.50 | 467.83 | **614.20** | 723.66 | NYC LL84 CY2024 Disclosure |
| **Overall (All Property Types)** | 29,104 | 79.47 | 50.60 | **71.60** | 93.30 | 250.70 | 159.62 | **225.87** | 294.32 | NYC LL84 CY2024 Disclosure |

---

### C. Calendar Year 2023 — Standard Site EUI (Cleaned)
Provided as a baseline to demonstrate the stability of EUI distributions between adjacent years.

| Property Type | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Office** | 2,363 | 64.94 | 41.45 | **56.60** | 76.35 | 204.86 | 130.76 | **178.55** | 240.85 | NYC LL84 CY2023 Disclosure |
| **Retail Store** | 285 | 74.81 | 41.60 | **60.60** | 86.90 | 235.99 | 131.23 | **191.17** | 274.13 | NYC LL84 CY2023 Disclosure |
| **Restaurant** | 10 | 189.58 | 48.50 | **104.80** | 285.20 | 598.05 | 153.00 | **330.60** | 899.69 | NYC LL84 CY2023 Disclosure |
| **Multifamily Housing** | 20,614 | 74.60 | 54.10 | **71.50** | 88.80 | 235.34 | 170.66 | **225.55** | 280.13 | NYC LL84 CY2023 Disclosure |
| **Hotel** | 649 | 94.82 | 65.00 | **84.50** | 111.50 | 299.12 | 205.05 | **266.56** | 351.74 | NYC LL84 CY2023 Disclosure |
| **Non-Refrigerated Warehouse** | 437 | 42.33 | 17.20 | **33.50** | 54.60 | 133.53 | 54.26 | **105.68** | 172.24 | NYC LL84 CY2023 Disclosure |
| **Hospital** | 108 | 252.73 | 136.67 | **224.05** | 323.95 | 797.25 | 431.15 | **706.79** | 1,021.93 | NYC LL84 CY2023 Disclosure |
| **Medical Office** | 122 | 100.94 | 63.52 | **85.10** | 106.92 | 318.43 | 200.40 | **268.46** | 337.30 | NYC LL84 CY2023 Disclosure |
| **K-12 School** | 1,853 | 61.89 | 47.80 | **59.60** | 73.00 | 195.25 | 150.79 | **188.01** | 230.29 | NYC LL84 CY2023 Disclosure |
| **Supermarket/Grocery** | 93 | 192.04 | 143.10 | **191.40** | 242.80 | 605.81 | 451.42 | **603.79** | 765.93 | NYC LL84 CY2023 Disclosure |
| **Overall (All Property Types)** | 30,560 | 76.47 | 49.40 | **69.20** | 89.40 | 241.23 | 155.84 | **218.30** | 282.02 | NYC LL84 CY2023 Disclosure |

### D. Calendar Year 2023 — Weather-Normalized Site EUI (Cleaned)

| Property Type | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Office** | 2,245 | 68.81 | 44.30 | **60.60** | 80.40 | 217.08 | 139.75 | **191.17** | 253.63 | NYC LL84 CY2023 Disclosure |
| **Retail Store** | 283 | 78.05 | 44.40 | **65.30** | 91.00 | 246.21 | 140.06 | **205.99** | 287.07 | NYC LL84 CY2023 Disclosure |
| **Restaurant** | 10 | 198.18 | 48.50 | **106.05** | 285.20 | 625.18 | 153.00 | **334.54** | 899.69 | NYC LL84 CY2023 Disclosure |
| **Multifamily Housing** | 19,630 | 80.64 | 57.70 | **77.90** | 96.90 | 254.40 | 182.02 | **245.74** | 305.68 | NYC LL84 CY2023 Disclosure |
| **Hotel** | 642 | 97.98 | 66.90 | **86.95** | 114.72 | 309.08 | 211.04 | **274.29** | 361.91 | NYC LL84 CY2023 Disclosure |
| **Non-Refrigerated Warehouse** | 425 | 47.32 | 20.00 | **37.10** | 62.00 | 149.27 | 63.09 | **117.04** | 195.58 | NYC LL84 CY2023 Disclosure |
| **Hospital** | 84 | 265.11 | 129.22 | **231.30** | 350.70 | 836.30 | 407.65 | **729.66** | 1,106.31 | NYC LL84 CY2023 Disclosure |
| **Medical Office** | 118 | 105.89 | 65.67 | **89.40** | 115.97 | 334.04 | 207.18 | **282.02** | 365.85 | NYC LL84 CY2023 Disclosure |
| **K-12 School** | 1,667 | 69.07 | 53.25 | **67.50** | 81.70 | 217.89 | 167.98 | **212.93** | 257.73 | NYC LL84 CY2023 Disclosure |
| **Supermarket/Grocery** | 93 | 198.76 | 147.20 | **194.30** | 251.80 | 627.01 | 464.36 | **612.94** | 794.33 | NYC LL84 CY2023 Disclosure |
| **Overall (All Property Types)** | 28,947 | 82.00 | 52.50 | **75.10** | 97.20 | 258.69 | 165.62 | **236.91** | 306.63 | NYC LL84 CY2023 Disclosure |

---

## 4. Headline Numbers: Overall NYC Median Site EUI

The single overall benchmarking population median (calculated across all property types with valid data) represents a key macro-benchmark:

### A. Calendar Year 2024
* **Standard Site EUI (Cleaned):**
  * Original: **69.50 kBtu/ft²·yr**
  * Converted: **219.24 kWh/m²·yr**
* **Weather-Normalized Site EUI (Cleaned):**
  * Original: **71.60 kBtu/ft²·yr**
  * Converted: **225.87 kWh/m²·yr**

### B. Calendar Year 2023
* **Standard Site EUI (Cleaned):**
  * Original: **69.20 kBtu/ft²·yr**
  * Converted: **218.30 kWh/m²·yr**
* **Weather-Normalized Site EUI (Cleaned):**
  * Original: **75.10 kBtu/ft²·yr**
  * Converted: **236.91 kWh/m²·yr**

---

## 5. Raw / Uncleaned Statistics Comparison (Calendar Year 2024)

This table shows the raw metrics without any outlier filtering. Note how extreme reporting errors distort the arithmetic mean, while the median and quartiles remain relatively robust.

| Property Type | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Office** | 2,355 | 95.50 | 42.85 | **58.30** | 77.20 | 301.25 | 135.17 | **183.91** | 243.53 |
| **Retail Store** | 332 | 3,038.35 | 43.38 | **63.45** | 92.22 | 9,584.76 | 136.83 | **200.16** | 290.93 |
| **Restaurant** | 15 | 207.21 | 79.25 | **119.80** | 335.90 | 653.65 | 250.00 | **377.92** | 1,059.63 |
| **Multifamily Housing** | 20,438 | 7,482.20 | 53.80 | **71.80** | 90.10 | 23,603.26 | 169.72 | **226.50** | 284.23 |
| **Hotel** | 666 | 93.44 | 67.03 | **86.45** | 110.97 | 294.75 | 211.44 | **272.71** | 350.08 |
| **Non-Refrigerated Warehouse** | 431 | 44.12 | 15.90 | **31.30** | 52.05 | 139.19 | 50.16 | **98.74** | 164.20 |
| **Hospital** | 111 | 648.62 | 107.40 | **236.20** | 329.00 | 2,046.12 | 338.80 | **745.11** | 1,037.86 |
| **Medical Office** | 126 | 94.60 | 58.02 | **80.55** | 110.33 | 298.44 | 183.05 | **254.10** | 348.03 |
| **K-12 School** | 1,839 | 75.45 | 48.60 | **59.50** | 72.00 | 238.02 | 153.31 | **187.70** | 227.13 |
| **Supermarket/Grocery** | 109 | 186.79 | 144.20 | **187.90** | 225.60 | 589.24 | 454.89 | **592.75** | 711.68 |
| **Overall (All Property Types)** | 30,577 | 5,137.18 | 49.40 | **69.50** | 91.00 | 16,205.68 | 155.84 | **219.24** | 287.07 |

---

## 6. Published Analyses, City Reports & Citations

1. **Official City Policy and Benchmarking Overview Portal**
   * **Title:** *Local Law 84 Benchmarking & Disclosure*
   * **Author/Agency:** NYC Mayor's Office of Climate & Environmental Justice (MOCEJ) & NYC Department of Buildings (DOB)
   * **Year/Version:** 2026 (Live Portal)
   * **URL:** [https://www.nyc.gov/site/buildings/codes/benchmarking.page](https://www.nyc.gov/site/buildings/codes/benchmarking.page)
   * **Access Date:** June 17, 2026

2. **Official Annual Performance and Trend Report**
   * **Title:** *New York City Energy and Water Use Report*
   * **Author/Agency:** NYC Mayor's Office of Climate & Environmental Justice (MOCEJ)
   * **Publication Year:** 2022 (covers historical benchmarking trends and policy evaluations)
   * **URL:** [https://www.nyc.gov/site/climate/codes-and-policies/energy-and-water-use-reports.page](https://www.nyc.gov/site/climate/codes-and-policies/energy-and-water-use-reports.page)
   * **Access Date:** June 17, 2026

3. **External NGO / Professional Association Summary Report**
   * **Title:** *NYC Building Energy Use Trends*
   * **Author/Agency:** Urban Green Council
   * **Publication Year:** 2023 / 2024 (Ongoing Data Briefs)
   * **URL:** [https://www.urbangreencouncil.org/resources/nyc-building-energy-use-trends/](https://www.urbangreencouncil.org/resources/nyc-building-energy-use-trends/)
   * **Access Date:** June 17, 2026

4. **Source Data Citation**
   * **Title:** *NYC Building Energy and Water Data Disclosure for Local Law 84 (2023-Present)*
   * **Author/Agency:** NYC Department of Buildings (DOB) via NYC Open Data
   * **Dataset Link:** [https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-/5zyy-y8am](https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-/5zyy-y8am)
   * **Access Date:** June 17, 2026
