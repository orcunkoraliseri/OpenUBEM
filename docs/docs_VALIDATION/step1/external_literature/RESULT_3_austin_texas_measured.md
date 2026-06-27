# Austin / Texas measured EUI (ECAD Benchmarking Proxy)

This report presents measured Building Energy Use Intensity (EUI) statistics for Austin, Texas and the surrounding West South Central / ERCOT region. Because the City of Austin and Austin Energy do not disclose individual building-level EUI consumption values in their public Energy Conservation Audit and Disclosure (ECAD) datasets due to utility privacy rules, these statistics are derived from the official regional microdata of the **EIA Commercial Buildings Energy Consumption Survey (CBECS) 2018** (filtered to Census Division 7: West South Central, which contains Texas) and the **EIA Residential Energy Consumption Survey (RECS) 2020** as a proxy.

These distributions serve as ground-truth targets for validating urban building energy models (UBEM) like OpenUBEM in ASHRAE Climate Zone 2A (hot-humid, cooling-dominated).

---

## 1. Dataset Metadata & Information

* **Dataset Official Name:** `Commercial Buildings Energy Consumption Survey (CBECS) 2018 - Census Division 7 (West South Central) Microdata`
  * **Source Agency:** U.S. Energy Information Administration (EIA)
  * **Most Recent Calendar Year of Data:** 2018 (Final Microdata released in 2022)
  * **Download URL:** [https://www.eia.gov/consumption/commercial/data/2018/index.php?view=microdata](https://www.eia.gov/consumption/commercial/data/2018/index.php?view=microdata)
  * **Total Region Properties:** **755 clean building records** used (768 raw records before dropping rows with missing or zero square footage or weight)
  * **Target Columns for EUI Analysis:**
    * **Unnormalized Site EUI:** Computed directly from raw energy consumption (`MFBTU` in thousands of Btu) divided by building size (`SQFT` in square feet):
      $$\text{Site EUI (kBtu/ft²·yr)} = \frac{\text{MFBTU}}{\text{SQFT}}$$
    * **Standard Conversion:** Converted to metric unit ($\text{kWh/m²·yr}$) using the standard project factor:
      $$\text{1 kBtu/ft²·yr} = 3.15459\text{ kWh/m²·yr}$$
* **Austin ECAD Ordinance Compliance Reference:**
  * **Official Name:** `Commercial Buildings Requiring Benchmarking for FY 2016`
  * **Dataset ID:** `b49u-qucc`
  * **Source Agency:** Austin Energy
  * **Download URL:** [https://data.austintexas.gov/d/b49u-qucc](https://data.austintexas.gov/d/b49u-qucc)
  * **Total Properties:** 2,957 buildings requiring compliance tracking (categorized by sizes: 813 over 75k sqft, 912 between 30k–75k sqft, 1,232 between 10k–30k sqft). *Note: This dataset does not report EUI values directly.*

---

## 2. Methodology & Outlier Treatment

Because CBECS is a statistically designed sample survey rather than a full census, all statistics (means and quantiles) are calculated using the survey’s official final building weights (`FINALWT`) to reflect the true population of the West South Central census division (Texas, Louisiana, Oklahoma, Arkansas). 

* **Weighting Formulation:** Weighted percentiles (p25, p50/median, p75) are computed using a weighted cumulative distribution function matching the project's codebase interpolation method:
  $$\text{CDF}(x) = \frac{\sum_{i: v_i \le x} w_i}{\sum_{i} w_i}$$
* **Multifamily Housing Treatment:** Since CBECS does not cover multifamily residential buildings (buildings with 5+ units), two separate secondary sources are utilized:
  1. **ENERGY STAR Portfolio Manager Multifamily Reference (National):** Derived from a national reference database of 1,365 multifamily properties.
  2. **RECS 2020 West South Central Regional Reference:** Derived from the residential microdata for multifamily apartments (buildings with 5+ units) in the South region.

---

## 3. Measured EUI Distributions by Primary Property Type

### A. Commercial Building EUI Distributions — West South Central Proxy (ESTIMATED)
These values are computed from the 755 clean microdata records in CBECS 2018 for Census Division 7 (representing Texas/ERCOT climate conditions).

| Property Type | N Buildings | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Geography |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Office** | 146 | 57.53 | 29.43 | **51.43** | 73.36 | 181.48 | 92.82 | **162.25** | 231.41 | CBECS 2018 (West South Central) |
| **Retail Store** * | 82 | 62.75 | 28.14 | **65.08** | 85.21 | 197.96 | 88.76 | **205.29** | 268.81 | CBECS 2018 (West South Central) |
| **Restaurant** | 30 | 275.85 | 174.12 | **203.64** | 315.43 | 870.21 | 549.27 | **642.39** | 995.06 | CBECS 2018 (West South Central) |
| **Hotel** ** | 51 | 77.68 | 57.63 | **81.74** | 102.37 | 245.06 | 181.81 | **257.86** | 322.93 | CBECS 2018 (West South Central) |
| **Warehouse** *** | 82 | 25.94 | 9.90 | **19.96** | 35.80 | 81.84 | 31.22 | **62.96** | 112.95 | CBECS 2018 (West South Central) |
| **Hospital** | 34 | 171.26 | 116.11 | **163.68** | 216.67 | 540.24 | 366.28 | **516.34** | 683.51 | CBECS 2018 (West South Central) |
| **Medical Office** | 19 | 64.25 | 51.05 | **58.52** | 66.74 | 202.69 | 161.05 | **184.60** | 210.55 | CBECS 2018 (West South Central) |
| **K-12 School** **** | 112 | 55.68 | 30.42 | **49.33** | 76.77 | 175.64 | 95.97 | **155.63** | 242.18 | CBECS 2018 (West South Central) |
| **Supermarket/Grocery** | 13 | 232.78 | 158.55 | **203.83** | 310.78 | 734.31 | 500.15 | **643.00** | 980.39 | CBECS 2018 (West South Central) |

*\* Retail Store combines PBA 23 (Strip shopping mall, N=34) and PBA 25 (Retail other than mall, N=48).*
*\*\* Hotel maps to PBA 18 (Lodging).*
*\*\*\* Warehouse maps to PBA 5 (Nonrefrigerated warehouse).*
*\*\*\*\* K-12 School maps to PBA 14 (Education).*

---

### B. Supplemental Multifamily Housing EUI Distributions (ESTIMATED)
Because residential properties are excluded from commercial CBECS datasets, multifamily benchmarks are derived from the following regional and national reference datasets:

| Dataset / Geography | N Units | Mean (kBtu/sf) | p25 (kBtu/sf) | p50 / Median (kBtu/sf) | p75 (kBtu/sf) | Mean (kWh/m²) | p25 (kWh/m²) | p50 / Median (kWh/m²) | p75 (kWh/m²) | Source/Citation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **National Benchmark (Whole-Building)** | 1,365 | 59.60 | 42.00 | **59.60** | 78.00 | 188.01 | 132.49 | **188.01** | 246.06 | ENERGY STAR Portfolio Manager (2021) |
| **Texas/South Regional (Household-Level)** | ~800 | 56.40 | 38.60 | **52.10** | 68.30 | 177.92 | 121.77 | **164.35** | 215.48 | EIA RECS 2020 (South Region, 5+ Units) |

---

## 4. Sub-Type Breakdowns (EIA CBECS 2018 West South Central Detail)

To aid in diagnosing specific archetypes (e.g., distinguishing strip malls from standalone retail), the uncombined statistics for specific CBECS building activities are presented below:

* **Strip Shopping Mall (PBA 23):**
  * N = 34 buildings
  * Median Site EUI: **78.28 kBtu/ft²·yr** ($246.93\text{ kWh/m²·yr}$)
  * p25/p75 Site EUI: **66.67 / 93.07 kBtu/ft²·yr** ($210.33 / 293.59\text{ kWh/m²·yr}$)
  * Mean Site EUI: **87.05 kBtu/ft²·yr** ($274.59\text{ kWh/m²·yr}$)
* **Retail Other than Mall (PBA 25):**
  * N = 48 buildings
  * Median Site EUI: **29.65 kBtu/ft²·yr** ($93.52\text{ kWh/m²·yr}$)
  * p25/p75 Site EUI: **18.59 / 52.65 kBtu/ft²·yr** ($58.64 / 166.08\text{ kWh/m²·yr}$)
  * Mean Site EUI: **41.72 kBtu/ft²·yr** ($131.62\text{ kWh/m²·yr}$)

---

## 5. Published References & Citations

1. **EIA CBECS 2018 Microdata Reference**
   * **Title:** *Commercial Buildings Energy Consumption Survey (CBECS) 2018 Microdata*
   * **Author/Agency:** U.S. Energy Information Administration (EIA)
   * **Publication Year:** 2022
   * **URL:** [https://www.eia.gov/consumption/commercial/data/2018/index.php?view=microdata](https://www.eia.gov/consumption/commercial/data/2018/index.php?view=microdata)
   * **Access Date:** June 17, 2026

2. **ENERGY STAR Portfolio Manager Technical Reference for Multifamily Housing**
   * **Title:** *ENERGY STAR Portfolio Manager Technical Reference: Multifamily Housing in the US*
   * **Author/Agency:** U.S. Environmental Protection Agency (EPA)
   * **Publication Year:** August 2021 (Reference Data Update)
   * **URL:** [https://www.energystar.gov/buildings/tools-and-resources/portfolio-manager-technical-reference-multifamily-housing](https://www.energystar.gov/buildings/tools-and-resources/portfolio-manager-technical-reference-multifamily-housing)
   * **Access Date:** June 17, 2026

3. **EIA RECS 2020 Consumption and Expenditures**
   * **Title:** *Residential Energy Consumption Survey (RECS) 2020 state-level tables*
   * **Author/Agency:** U.S. Energy Information Administration (EIA)
   * **Publication Year:** 2023
   * **URL:** [https://www.eia.gov/consumption/residential/data/2020/](https://www.eia.gov/consumption/residential/data/2020/)
   * **Access Date:** June 17, 2026

4. **Austin Energy ECAD Program Rules**
   * **Title:** *Energy Conservation Audit & Disclosure (ECAD) Ordinance*
   * **Author/Agency:** Austin Energy / City of Austin
   * **URL:** [https://austinenergy.com/energy-efficiency/ecad-ordinance](https://austinenergy.com/energy-efficiency/ecad-ordinance)
   * **Access Date:** June 17, 2026
