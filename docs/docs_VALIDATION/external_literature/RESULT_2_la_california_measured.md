# Los Angeles & California Benchmarking Measured EUI Statistics

This report presents measured Building Energy Use Intensity (EUI) statistics for Los Angeles and California, processed directly from the official Los Angeles Existing Buildings Energy & Water Efficiency (EBEWE) benchmarking database and the California Energy Commission (CEC) statewide AB 802 building benchmarking database. These distributions serve as ground-truth targets for validating urban building energy models (UBEM) like OpenUBEM in ASHRAE Climate Zone 3B (Los Angeles / hot-dry Mediterranean climate).

---

## 1. Dataset Metadata & Information

### A. Los Angeles EBEWE Benchmarking Dataset
* **Official Name:** `Existing Buildings Energy & Water Efficiency (EBEWE) Program`
* **Source Agency:** Los Angeles Department of Building and Safety (LADBS)
* **Most Recent Calendar Year of Substantial Data:** **Calendar Year 2024** (11,245 properties total; 5,678 with valid EUI entries)
* **Dataset Identifier / ID:** `9yda-i4ya`
* **Download URL:** [https://data.lacity.org/City-Infrastructure-Service-Requests/Existing-Buildings-Energy-Water-Efficiency-EBEWE-Pr/9yda-i4ya](https://data.lacity.org/City-Infrastructure-Service-Requests/Existing-Buildings-Energy-Water-Efficiency-EBEWE-Pr/9yda-i4ya)
* **Target Columns for EUI Analysis:**
  * **Standard Site EUI (Unnormalized):** `site_eui` (kBtu/ft²·yr)
  * **Weather-Normalized Site EUI:** `weather_normalized_3` (kBtu/ft²·yr)
  * **Standard Source EUI:** `source_eui` (kBtu/ft²·yr)
  * **Weather-Normalized Source EUI:** `weather_normalized_4` (kBtu/ft²·yr)

### B. California AB 802 Statewide Benchmarking Dataset
* **Official Name:** `CEC Building Energy Benchmarking Program Public Disclosure`
* **Source Agency:** California Energy Commission (CEC)
* **Most Recent Calendar Year of Substantial Data:** **Calendar Year 2024** (25,591 properties total; 19,332 with valid EUI entries)
* **Download URL:** [https://www.energy.ca.gov/media/12019](https://www.energy.ca.gov/media/12019) (Drupal portal endpoint, links to `https://www.energy.ca.gov/sites/default/files/2025-10/2024_Download_ADA.xlsx`)
* **Target Columns for EUI Analysis:**
  * **Weather-Normalized Site EUI:** `Weather Normalized Site EUI (kBtu/ft²)`
  * **Standard Site EUI (Unnormalized):** Calculated by summing the fuel usage columns (`Natural Gas Use (kBtu)`, `Electricity Use - Grid Purchase (kBtu)`, `Fuel Oil #2 Use (kBtu)`, `District Steam Use (kBtu)`, `Diesel Use (kBtu)`, `Propane Use (kBtu)`, `District Hot Water Use (kBtu)`, `District Chilled Water Use (kBtu)`) and dividing by the gross building floor area (`Property GFA - Calculated (Buildings) (ft²)`).

---

## 2. Data Cleaning & Outlier Treatment Methodology

Because the benchmarking databases consist of self-reported entries via ENERGY STAR Portfolio Manager, they contain significant reporting errors (e.g., negative values, units entered in Wh instead of kWh or kBtu instead of MBtu, leading to values in the millions, or GFA division by zero leading to infinite EUIs).
To compute a scientifically valid **Mean** and representative distributions, standard cleaning criteria were applied to filter out extreme outliers:
* **Cleaning Filter:** Only properties with a Site EUI (or Weather Normalized Site EUI) between **0.1 and 1,000 kBtu/ft²·yr** were included in the cleaned analyses.
* **Source Microdata Calculation:** All statistics presented in Section 3 were calculated directly from the raw microdata of both datasets.

---

## 3. Measured EUI Distributions by Primary Property Type (Cleaned)

All EUI values are reported in both the original unit (**kBtu/ft²·yr**) and converted to **kWh/m²·yr** using the exact conversion factor:
$$\text{1 kBtu/ft²·yr} = 3.15459\text{ kWh/m²·yr}$$

### A. Calendar Year 2024 — Standard Site EUI (Cleaned)
This table summarizes the actual, measured site energy consumption from utility bills.

| Property Type | Geography | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| Office | Los Angeles (EBEWE) | 742 | 46.57 | 24.73 | **38.50** | 55.20 | 146.92 | 78.00 | **121.45** | 174.13 | LADBS EBEWE CY2024 |
| Office | CA Statewide | 3674 | 51.57 | 27.24 | **39.27** | 57.74 | 162.69 | 85.92 | **123.87** | 182.14 | CEC AB 802 CY2024 |
| Retail Store | Los Angeles (EBEWE) | 150 | 51.13 | 17.05 | **36.50** | 59.40 | 161.29 | 53.79 | **115.14** | 187.38 | LADBS EBEWE CY2024 |
| Retail Store | CA Statewide | 1132 | 51.91 | 22.57 | **37.89** | 56.90 | 163.74 | 71.21 | **119.51** | 179.49 | CEC AB 802 CY2024 |
| Restaurant | Los Angeles (EBEWE) | 12 | 199.20 | 86.90 | **121.75** | 237.30 | 628.39 | 274.13 | **384.07** | 748.58 | LADBS EBEWE CY2024 |
| Restaurant | CA Statewide | 17 | 132.75 | 37.48 | **64.72** | 106.17 | 418.78 | 118.24 | **204.18** | 334.93 | CEC AB 802 CY2024 |
| Multifamily Housing | Los Angeles (EBEWE) | 3805 | 38.01 | 29.00 | **36.70** | 45.70 | 119.90 | 91.48 | **115.77** | 144.16 | LADBS EBEWE CY2024 |
| Multifamily Housing | CA Statewide | 7129 | 29.50 | 16.52 | **27.35** | 38.99 | 93.05 | 52.10 | **86.28** | 122.99 | CEC AB 802 CY2024 |
| Hotel | Los Angeles (EBEWE) | 89 | 70.92 | 47.70 | **64.40** | 83.60 | 223.71 | 150.47 | **203.16** | 263.72 | LADBS EBEWE CY2024 |
| Hotel | CA Statewide | 967 | 59.95 | 38.19 | **51.79** | 68.96 | 189.13 | 120.46 | **163.36** | 217.53 | CEC AB 802 CY2024 |
| Warehouse | Los Angeles (EBEWE) | 632 | 28.05 | 5.28 | **10.75** | 22.02 | 88.48 | 16.64 | **33.91** | 69.48 | LADBS EBEWE CY2024 |
| Warehouse | CA Statewide | 3935 | 22.37 | 4.24 | **8.13** | 19.90 | 70.57 | 13.36 | **25.64** | 62.78 | CEC AB 802 CY2024 |
| Hospital | Los Angeles (EBEWE) | 12 | 147.51 | 123.38 | **152.60** | 188.15 | 465.33 | 389.20 | **481.39** | 593.54 | LADBS EBEWE CY2024 |
| Hospital | CA Statewide | 172 | 234.26 | 182.69 | **234.27** | 303.86 | 738.98 | 576.32 | **739.03** | 958.54 | CEC AB 802 CY2024 |
| Medical Office | Los Angeles (EBEWE) | 93 | 75.34 | 40.40 | **61.60** | 86.10 | 237.66 | 127.45 | **194.32** | 271.61 | LADBS EBEWE CY2024 |
| Medical Office | CA Statewide | 391 | 84.90 | 49.66 | **72.77** | 101.09 | 267.82 | 156.66 | **229.56** | 318.89 | CEC AB 802 CY2024 |
| K-12 School | Los Angeles (EBEWE) | 58 | 35.33 | 18.52 | **26.95** | 40.75 | 111.45 | 58.44 | **85.02** | 128.55 | LADBS EBEWE CY2024 |
| K-12 School | CA Statewide | 1485 | 29.23 | 17.88 | **25.33** | 36.73 | 92.22 | 56.42 | **79.92** | 115.88 | CEC AB 802 CY2024 |
| Supermarket/Grocery | Los Angeles (EBEWE) | 85 | 195.61 | 135.80 | **172.60** | 222.80 | 617.07 | 428.39 | **544.48** | 702.84 | LADBS EBEWE CY2024 |
| Supermarket/Grocery | CA Statewide | 430 | 140.75 | 114.00 | **138.84** | 166.47 | 444.00 | 359.62 | **437.97** | 525.15 | CEC AB 802 CY2024 |
| **Overall** | Los Angeles (EBEWE) | 5678 | 42.40 | 24.92 | **36.00** | 47.60 | 133.74 | 78.63 | **113.57** | 150.16 | LADBS EBEWE CY2024 |
| **Overall** | CA Statewide | 19332 | 40.57 | 14.74 | **29.28** | 46.61 | 127.97 | 46.50 | **92.36** | 147.04 | CEC AB 802 CY2024 |


*\* Note: Restaurant counts in the CA Statewide dataset are low (N=17) because the statewide AB 802 program generally applies to buildings over 50,000 square feet, which excludes most standalone restaurant properties. Restaurant counts in the LA EBEWE dataset include self-selected "Restaurant", "Other - Restaurant/Bar", "Food Service", and "Bar/Nightclub" properties.*

### B. Calendar Year 2024 — Weather-Normalized Site EUI (Cleaned)
Weather-normalized EUI adjusts the actual energy use to a standardized climate year, useful for eliminating year-to-year temperature fluctuations.

| Property Type | Geography | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| Office | Los Angeles (EBEWE) | 706 | 46.26 | 24.60 | **38.10** | 54.95 | 145.94 | 77.60 | **120.19** | 173.34 | LADBS EBEWE CY2024 |
| Office | CA Statewide | 3610 | 54.72 | 29.30 | **42.40** | 61.58 | 172.61 | 92.43 | **133.75** | 194.24 | CEC AB 802 CY2024 |
| Retail Store | Los Angeles (EBEWE) | 146 | 51.67 | 17.05 | **35.65** | 58.98 | 162.99 | 53.79 | **112.46** | 186.04 | LADBS EBEWE CY2024 |
| Retail Store | CA Statewide | 1130 | 56.42 | 24.90 | **45.80** | 62.58 | 177.99 | 78.55 | **144.48** | 197.40 | CEC AB 802 CY2024 |
| Restaurant | Los Angeles (EBEWE) | 12 | 198.26 | 85.33 | **120.55** | 233.18 | 625.42 | 269.17 | **380.29** | 735.57 | LADBS EBEWE CY2024 |
| Restaurant | CA Statewide | 18 | 167.39 | 47.73 | **112.50** | 174.65 | 528.06 | 150.55 | **354.89** | 550.95 | CEC AB 802 CY2024 |
| Multifamily Housing | Los Angeles (EBEWE) | 3726 | 37.23 | 28.70 | **36.00** | 44.40 | 117.43 | 90.54 | **113.57** | 140.06 | LADBS EBEWE CY2024 |
| Multifamily Housing | CA Statewide | 6986 | 34.05 | 23.12 | **32.80** | 42.00 | 107.42 | 72.95 | **103.47** | 132.49 | CEC AB 802 CY2024 |
| Hotel | Los Angeles (EBEWE) | 89 | 70.25 | 47.90 | **64.40** | 82.50 | 221.61 | 151.10 | **203.16** | 260.25 | LADBS EBEWE CY2024 |
| Hotel | CA Statewide | 962 | 64.76 | 43.42 | **56.20** | 72.78 | 204.30 | 136.99 | **177.29** | 229.58 | CEC AB 802 CY2024 |
| Warehouse | Los Angeles (EBEWE) | 604 | 27.65 | 5.17 | **10.40** | 21.65 | 87.22 | 16.33 | **32.81** | 68.30 | LADBS EBEWE CY2024 |
| Warehouse | CA Statewide | 3822 | 23.41 | 4.20 | **8.20** | 20.50 | 73.84 | 13.25 | **25.87** | 64.67 | CEC AB 802 CY2024 |
| Hospital | Los Angeles (EBEWE) | 11 | 146.17 | 109.45 | **161.00** | 187.00 | 461.12 | 345.27 | **507.89** | 589.91 | LADBS EBEWE CY2024 |
| Hospital | CA Statewide | 169 | 242.90 | 187.60 | **239.70** | 303.30 | 766.24 | 591.80 | **756.16** | 956.79 | CEC AB 802 CY2024 |
| Medical Office | Los Angeles (EBEWE) | 92 | 75.48 | 41.77 | **60.80** | 86.88 | 238.11 | 131.78 | **191.80** | 274.06 | LADBS EBEWE CY2024 |
| Medical Office | CA Statewide | 389 | 93.76 | 57.90 | **82.10** | 113.10 | 295.78 | 182.65 | **258.99** | 356.78 | CEC AB 802 CY2024 |
| K-12 School | Los Angeles (EBEWE) | 58 | 34.59 | 18.52 | **26.50** | 39.08 | 109.12 | 58.44 | **83.60** | 123.27 | LADBS EBEWE CY2024 |
| K-12 School | CA Statewide | 1414 | 34.60 | 21.90 | **29.85** | 40.80 | 109.16 | 69.09 | **94.16** | 128.71 | CEC AB 802 CY2024 |
| Supermarket/Grocery | Los Angeles (EBEWE) | 83 | 195.87 | 136.95 | **171.80** | 218.95 | 617.90 | 432.02 | **541.96** | 690.70 | LADBS EBEWE CY2024 |
| Supermarket/Grocery | CA Statewide | 427 | 147.88 | 125.50 | **142.70** | 167.10 | 466.51 | 395.90 | **450.16** | 527.13 | CEC AB 802 CY2024 |
| **Overall** | Los Angeles (EBEWE) | 5527 | 41.80 | 25.00 | **35.50** | 46.40 | 131.88 | 78.86 | **111.99** | 146.37 | LADBS EBEWE CY2024 |
| **Overall** | CA Statewide | 18927 | 44.57 | 18.60 | **33.40** | 50.20 | 140.60 | 58.68 | **105.36** | 158.36 | CEC AB 802 CY2024 |


---

### C. Calendar Year 2023 — Standard Site EUI (Cleaned)
Provided as a baseline to demonstrate the stability of EUI distributions between adjacent years.

| Property Type | Geography | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| Office | Los Angeles (EBEWE) | 800 | 47.44 | 26.27 | **38.65** | 54.08 | 149.66 | 82.89 | **121.92** | 170.58 | LADBS EBEWE CY2023 |
| Office | CA Statewide | 3548 | 55.41 | 27.76 | **41.47** | 60.92 | 174.81 | 87.58 | **130.82** | 192.19 | CEC AB 802 CY2023 |
| Retail Store | Los Angeles (EBEWE) | 166 | 50.78 | 16.18 | **36.95** | 66.55 | 160.19 | 51.03 | **116.56** | 209.94 | LADBS EBEWE CY2023 |
| Retail Store | CA Statewide | 1100 | 48.71 | 23.12 | **39.14** | 58.15 | 153.66 | 72.94 | **123.48** | 183.45 | CEC AB 802 CY2023 |
| Restaurant | Los Angeles (EBEWE) | 14 | 100.60 | 25.70 | **56.00** | 145.12 | 317.35 | 81.07 | **176.66** | 457.81 | LADBS EBEWE CY2023 |
| Restaurant | CA Statewide | 13 | 74.25 | 23.89 | **62.53** | 102.09 | 234.23 | 75.37 | **197.25** | 322.05 | CEC AB 802 CY2023 |
| Multifamily Housing | Los Angeles (EBEWE) | 3857 | 37.61 | 27.00 | **36.50** | 45.80 | 118.64 | 85.17 | **115.14** | 144.48 | LADBS EBEWE CY2023 |
| Multifamily Housing | CA Statewide | 6886 | 29.52 | 16.53 | **27.72** | 39.52 | 93.14 | 52.16 | **87.43** | 124.67 | CEC AB 802 CY2023 |
| Hotel | Los Angeles (EBEWE) | 103 | 74.67 | 49.85 | **66.90** | 85.25 | 235.56 | 157.26 | **211.04** | 268.93 | LADBS EBEWE CY2023 |
| Hotel | CA Statewide | 870 | 62.03 | 39.91 | **54.22** | 71.36 | 195.66 | 125.90 | **171.05** | 225.11 | CEC AB 802 CY2023 |
| Warehouse | Los Angeles (EBEWE) | 672 | 26.17 | 5.28 | **11.05** | 21.60 | 82.56 | 16.64 | **34.86** | 68.14 | LADBS EBEWE CY2023 |
| Warehouse | CA Statewide | 3681 | 21.59 | 4.43 | **8.51** | 20.11 | 68.11 | 13.97 | **26.85** | 63.43 | CEC AB 802 CY2023 |
| Hospital | Los Angeles (EBEWE) | 15 | 133.59 | 67.30 | **130.80** | 194.30 | 421.41 | 212.30 | **412.62** | 612.94 | LADBS EBEWE CY2023 |
| Hospital | CA Statewide | 141 | 227.89 | 160.32 | **225.29** | 297.23 | 718.91 | 505.74 | **710.69** | 937.63 | CEC AB 802 CY2023 |
| Medical Office | Los Angeles (EBEWE) | 94 | 73.38 | 39.60 | **64.65** | 81.40 | 231.48 | 124.92 | **203.94** | 256.78 | LADBS EBEWE CY2023 |
| Medical Office | CA Statewide | 354 | 89.55 | 49.83 | **75.88** | 107.57 | 282.51 | 157.19 | **239.38** | 339.35 | CEC AB 802 CY2023 |
| K-12 School | Los Angeles (EBEWE) | 57 | 31.38 | 19.70 | **27.00** | 35.10 | 98.98 | 62.15 | **85.17** | 110.73 | LADBS EBEWE CY2023 |
| K-12 School | CA Statewide | 1391 | 30.13 | 18.04 | **25.78** | 37.41 | 95.06 | 56.92 | **81.33** | 118.01 | CEC AB 802 CY2023 |
| Supermarket/Grocery | Los Angeles (EBEWE) | 71 | 188.82 | 132.10 | **178.20** | 256.55 | 595.64 | 416.72 | **562.15** | 809.31 | LADBS EBEWE CY2023 |
| Supermarket/Grocery | CA Statewide | 504 | 147.23 | 113.01 | **137.79** | 169.97 | 464.44 | 356.50 | **434.67** | 536.18 | CEC AB 802 CY2023 |
| **Overall** | Los Angeles (EBEWE) | 5849 | 41.41 | 23.30 | **35.70** | 48.00 | 130.64 | 73.50 | **112.62** | 151.42 | LADBS EBEWE CY2023 |
| **Overall** | CA Statewide | 18488 | 41.53 | 14.96 | **29.89** | 48.14 | 131.02 | 47.19 | **94.29** | 151.87 | CEC AB 802 CY2023 |


### D. Calendar Year 2023 — Weather-Normalized Site EUI (Cleaned)

| Property Type | Geography | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| Office | Los Angeles (EBEWE) | 770 | 47.25 | 26.02 | **38.40** | 53.58 | 149.04 | 82.10 | **121.14** | 169.01 | LADBS EBEWE CY2023 |
| Office | CA Statewide | 3406 | 58.08 | 30.10 | **44.10** | 63.77 | 183.23 | 94.95 | **139.12** | 201.18 | CEC AB 802 CY2023 |
| Retail Store | Los Angeles (EBEWE) | 163 | 51.43 | 16.80 | **37.30** | 66.65 | 162.24 | 53.00 | **117.67** | 210.25 | LADBS EBEWE CY2023 |
| Retail Store | CA Statewide | 1097 | 52.24 | 24.50 | **45.80** | 62.40 | 164.81 | 77.29 | **144.48** | 196.85 | CEC AB 802 CY2023 |
| Restaurant | Los Angeles (EBEWE) | 13 | 104.91 | 25.40 | **64.10** | 143.70 | 330.94 | 80.13 | **202.21** | 453.31 | LADBS EBEWE CY2023 |
| Restaurant | CA Statewide | 13 | 81.50 | 25.40 | **62.20** | 120.30 | 257.10 | 80.13 | **196.22** | 379.50 | CEC AB 802 CY2023 |
| Multifamily Housing | Los Angeles (EBEWE) | 3771 | 37.24 | 27.00 | **36.00** | 45.20 | 117.48 | 85.17 | **113.57** | 142.59 | LADBS EBEWE CY2023 |
| Multifamily Housing | CA Statewide | 6636 | 33.60 | 22.30 | **32.90** | 42.40 | 106.00 | 70.35 | **103.79** | 133.75 | CEC AB 802 CY2023 |
| Hotel | Los Angeles (EBEWE) | 102 | 74.05 | 50.02 | **66.65** | 84.45 | 233.59 | 157.81 | **210.25** | 266.41 | LADBS EBEWE CY2023 |
| Hotel | CA Statewide | 845 | 68.25 | 46.40 | **58.70** | 76.60 | 215.31 | 146.37 | **185.17** | 241.64 | CEC AB 802 CY2023 |
| Warehouse | Los Angeles (EBEWE) | 637 | 25.87 | 5.00 | **10.70** | 21.60 | 81.61 | 15.77 | **33.75** | 68.14 | LADBS EBEWE CY2023 |
| Warehouse | CA Statewide | 3551 | 21.93 | 4.40 | **8.50** | 20.30 | 69.17 | 13.88 | **26.81** | 64.04 | CEC AB 802 CY2023 |
| Hospital | Los Angeles (EBEWE) | 15 | 131.43 | 67.30 | **130.40** | 191.45 | 414.60 | 212.30 | **411.36** | 603.95 | LADBS EBEWE CY2023 |
| Hospital | CA Statewide | 137 | 238.24 | 175.70 | **231.80** | 297.70 | 751.55 | 554.26 | **731.23** | 939.12 | CEC AB 802 CY2023 |
| Medical Office | Los Angeles (EBEWE) | 90 | 74.25 | 40.55 | **65.55** | 81.80 | 234.24 | 127.92 | **206.78** | 258.05 | LADBS EBEWE CY2023 |
| Medical Office | CA Statewide | 348 | 98.98 | 58.52 | **83.75** | 118.33 | 312.23 | 184.62 | **264.20** | 373.27 | CEC AB 802 CY2023 |
| K-12 School | Los Angeles (EBEWE) | 57 | 30.93 | 19.70 | **27.00** | 35.50 | 97.56 | 62.15 | **85.17** | 111.99 | LADBS EBEWE CY2023 |
| K-12 School | CA Statewide | 1348 | 33.70 | 21.80 | **29.70** | 41.10 | 106.30 | 68.77 | **93.69** | 129.65 | CEC AB 802 CY2023 |
| Supermarket/Grocery | Los Angeles (EBEWE) | 70 | 187.77 | 127.60 | **177.65** | 256.00 | 592.34 | 402.53 | **560.41** | 807.58 | LADBS EBEWE CY2023 |
| Supermarket/Grocery | CA Statewide | 495 | 152.32 | 122.95 | **142.80** | 172.90 | 480.50 | 387.86 | **450.48** | 545.43 | CEC AB 802 CY2023 |
| **Overall** | Los Angeles (EBEWE) | 5688 | 41.17 | 23.50 | **35.40** | 47.23 | 129.86 | 74.13 | **111.67** | 148.98 | LADBS EBEWE CY2023 |
| **Overall** | CA Statewide | 17876 | 44.90 | 18.40 | **33.70** | 51.10 | 141.64 | 58.04 | **106.31** | 161.20 | CEC AB 802 CY2023 |


---

## 4. Headline Numbers: Overall Median Site EUI (Cleaned)

The single overall benchmarking population median (calculated across all property types with valid data) represents a key macro-benchmark:

### A. Los Angeles (LADBS EBEWE)
* **Calendar Year 2024:**
  * Standard Site EUI: **36.00 kBtu/ft²·yr** (113.57 kWh/m²·yr)
  * Weather-Normalized Site EUI: **35.50 kBtu/ft²·yr** (111.99 kWh/m²·yr)
* **Calendar Year 2023:**
  * Standard Site EUI: **35.70 kBtu/ft²·yr** (112.62 kWh/m²·yr)
  * Weather-Normalized Site EUI: **35.40 kBtu/ft²·yr** (111.67 kWh/m²·yr)

### B. California Statewide (CEC AB 802)
* **Calendar Year 2024:**
  * Standard Site EUI: **29.28 kBtu/ft²·yr** (92.36 kWh/m²·yr)
  * Weather-Normalized Site EUI: **33.40 kBtu/ft²·yr** (105.36 kWh/m²·yr)
* **Calendar Year 2023:**
  * Standard Site EUI: **29.89 kBtu/ft²·yr** (94.29 kWh/m²·yr)
  * Weather-Normalized Site EUI: **33.70 kBtu/ft²·yr** (106.31 kWh/m²·yr)

---

## 5. Published Analyses, City Reports & Citations

1. **Official Los Angeles EBEWE Policy and Program Portal**
   * **Title:** *Existing Buildings Energy & Water Efficiency Program (EBEWE)*
   * **Author/Agency:** Los Angeles Department of Building and Safety (LADBS)
   * **Year/Version:** 2026 (Live Portal)
   * **URL:** [https://www.ladbs.org/services/green-building-sustainability/existing-buildings-energy-water-efficiency-program](https://www.ladbs.org/services/green-building-sustainability/existing-buildings-energy-water-efficiency-program)
   * **Access Date:** June 17, 2026

2. **Official California Energy Commission Benchmarking Portal**
   * **Title:** *Building Energy Benchmarking Program (AB 802)*
   * **Author/Agency:** California Energy Commission (CEC)
   * **Year/Version:** 2026 (Live Portal)
   * **URL:** [https://www.energy.ca.gov/programs-and-topics/programs/building-energy-benchmarking-program](https://www.energy.ca.gov/programs-and-topics/programs/building-energy-benchmarking-program)
   * **Access Date:** June 17, 2026

3. **Los Angeles EBEWE Microdata Dataset**
   * **Title:** *Existing Buildings Energy & Water Efficiency (EBEWE) Program*
   * **Author/Agency:** LADBS via City of Los Angeles Open Data
   * **Dataset Link:** [https://data.lacity.org/City-Infrastructure-Service-Requests/Existing-Buildings-Energy-Water-Efficiency-EBEWE-Pr/9yda-i4ya](https://data.lacity.org/City-Infrastructure-Service-Requests/Existing-Buildings-Energy-Water-Efficiency-EBEWE-Pr/9yda-i4ya)
   * **Access Date:** June 17, 2026

4. **California Statewide Benchmarking Microdata Datasets**
   * **Title:** *CEC Building Energy Benchmarking Program Public Disclosure (2023 & 2024)*
   * **Author/Agency:** California Energy Commission
   * **2024 Dataset Link:** [https://www.energy.ca.gov/sites/default/files/2025-10/2024_Download_ADA.xlsx](https://www.energy.ca.gov/sites/default/files/2025-10/2024_Download_ADA.xlsx)
   * **2023 Dataset Link:** [https://www.energy.ca.gov/sites/default/files/2025-10/2023_Download_ADA.xlsx](https://www.energy.ca.gov/sites/default/files/2025-10/2023_Download_ADA.xlsx)
   * **Access Date:** June 17, 2026
