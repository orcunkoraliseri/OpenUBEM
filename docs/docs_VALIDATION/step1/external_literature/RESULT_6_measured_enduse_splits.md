# Measured End-Use Energy Splits Validation Reference

This document compiles independent, authoritative measured end-use energy consumption breakdowns for US commercial and multifamily buildings. These statistics serve as an external validation reference to check the building-type end-use fraction splits (service-load reconstruction) used in OpenUBEM.

OpenUBEM simulates four primary end-uses (space heating, space cooling, lighting, and plug/equipment) and reconstructs the remaining five (ventilation fans, pumps, domestic hot water [DHW], refrigeration, and cooking) using per-archetype fraction splits. This ground-truth compilation validates those reconstruction fractions—specifically focusing on the large refrigeration shares in supermarkets and cooking/refrigeration/DHW shares in restaurants and lodging.

---

## Measured End-Use Splits Table

Below is the summary table of measured end-use splits (% of total site energy). 

* **Direct vs. Estimated:** All commercial values are calculated directly from the **EIA CBECS 2018 Table E1** (Major Fuels Consumption by End Use). All residential multifamily values are calculated directly from **EIA RECS 2020 Tables CE5.1a, CE5.1b, and CE5.2**.
* **Sum Check:** Rounded values sum to ~100%. Any values withheld by the EIA due to high relative standard errors (RSE > 50%) or small sample sizes are marked as **Q (Withheld)**.

| Building Type | Heat % | Cool % | Fans % | Pumps % | DHW % | Lighting % | Equipment % | Refrigeration % | Cooking % | Source | Year |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Large Office** *(Proxy: Office)* | 29.73% | 7.41% | 19.58% | *Not reported* | 1.46% | 11.99% | 26.53% | 2.01% | 1.46% | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |
| **Stand-alone Retail** *(Proxy: Retail)* | 24.32% | 9.31% | 18.02% | *Not reported* | 1.20% | 18.62% | 18.62% | 4.80% | 4.80% | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |
| **Supermarket/Grocery** *(Proxy: Food Sales)* | 14.16% | 3.00% | 5.58% | *Not reported* | **Q** | 5.58% | 0.43% (+ Q) | **37.77%** | 11.16% | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |
| **Full-Service Restaurant** *(Proxy: Food Service)* | 12.05% | 6.85% | 6.30% | *Not reported* | **7.12%** | 4.11% | 8.77% | **15.34%** | **39.45%** | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |
| **Quick-Service Restaurant** *(Proxy: Food Service)* | 12.05% | 6.85% | 6.30% | *Not reported* | **7.12%** | 4.11% | 8.77% | **15.34%** | **39.45%** | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |
| **Mid-Rise Apartment** *(Proxy: MF 5+ units)* | 27.05% | 12.91% | 0.90% | 0.07% | **33.18%** | 5.11% | 9.33% | **6.79%** | **4.66%** | [EIA RECS 2020 Tables CE5.1a/b & CE5.2](https://www.eia.gov/consumption/residential/data/2020/) | 2020 |
| **Hospital** *(Proxy: Inpatient)* | 32.11% | 6.42% | 14.91% | *Not reported* | 7.57% | 6.19% | 22.02% | 2.06% | 8.94% | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |
| **Hotel** *(Proxy: Lodging)* | 18.06% | 6.86% | 14.55% | *Not reported* | **18.56%** | 8.36% | 16.39% | 4.52% | 12.71% | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |
| **Warehouse** *(Proxy: Warehouse & Storage)* | 39.39% | 9.85% | 4.55% | *Not reported* | 1.33% | 15.15% | 22.92% | 6.82% | 0.19% | [EIA CBECS 2018 Table E1](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) | 2018 |

> [!NOTE]
> * **Equipment %** for CBECS commercial buildings is computed as the sum of "Office Equipment", "Computing", and "Other" end uses. 
> * **Fans %** represents "Ventilation" in CBECS and "Ceiling Fans" in RECS. Central ventilation fan energy in residential apartments is typically integrated into HVAC or common area bills (captured in CBECS).
> * **Pumps %** is not separately reported in CBECS (typically folded into HVAC auxiliary/fans or "Other"). In RECS, it represents pool and hot tub pumps (which are negligible at 0.07%).
> * **Q (Withheld)** indicates the data point was suppressed by the EIA due to high Relative Standard Error (RSE > 50%) or small sample sizes. For Supermarkets, DHW, Computing, and Other are suppressed, meaning the reported categories sum to 77.68%, and the remaining 22.32% is distributed among the withheld categories.

---

## Key Synthesis & Verification Insights

### 1. Supermarket Refrigeration Dominance
* **Measured Ground Truth:** The CBECS 2018 data shows that **37.77%** of all site energy in supermarkets (Food Sales) is consumed by refrigeration systems. In terms of absolute energy intensity, refrigeration consumes **88 trillion Btu** out of a total of **233 trillion Btu** nationally.
* **Literature Context:** Peer-reviewed disaggregation and submetering studies (e.g., Brunel University and CIBSE) consistently place supermarket refrigeration at **35% to 50%** of total site energy. PNNL prototype models simulated in EnergyPlus typically model refrigeration as **40% to 50%** of the supermarket energy budget depending on vintage and climate zone.
* **Validation Outcome:** This validates the large refrigeration reconstruction fraction in OpenUBEM, confirming that refrigeration must account for a near-majority share of site EUI in supermarket archetypes.

### 2. Restaurant Cooking, Refrigeration, and DHW
* **Measured Ground Truth:** For food service buildings, CBECS 2018 reports:
  * **Cooking:** 39.45% (144 TBtu)
  * **Refrigeration:** 15.34% (56 TBtu)
  * **Water Heating (DHW):** 7.12% (26 TBtu)
  * **Combined Share:** **61.91%** of total site energy is dedicated to these three process loads.
* **Literature Context:** This aligns perfectly with the expected range of **40% to 67%** in the restaurant industry. Process loads (cooking, cooling/freezing, sanitation) dominate energy intensity. In PNNL Commercial Prototype models (Quick-Service and Full-Service Restaurants), cooking equipment represents **40% to 50%** of site energy, with refrigeration and hot water accounting for another **15% to 25%**.
* **Validation Outcome:** This confirms that OpenUBEM's reconstruction fractions must allocate over **60%** of total site energy to cooking, refrigeration, and DHW for restaurant archetypes. 

### 3. Multifamily Apartment Energy Profile (Mid-Rise Apartment)
* **Measured Ground Truth:** For apartments in buildings with 5 or more units, the RECS 2020 data (summing electricity, natural gas, and propane) shows:
  * **Water Heating (DHW):** **33.18%** (222.3 TBtu out of 669.9 TBtu)
  * **Space Heating:** **27.05%** (181.2 TBtu)
  * **Space Cooling:** **12.91%** (86.5 TBtu)
  * **Refrigeration:** **6.79%** (45.5 TBtu)
  * **Cooking:** **4.66%** (31.2 TBtu)
* **Key Observations:** In multifamily housing, **DHW is the single largest energy load (33.18%)**, surpassing space heating (27.05%). This is due to shared walls and smaller average floor areas reducing thermal transmission loads, while water heating remains high and continuous.
* **Validation Outcome:** OpenUBEM's residential reconstruction fractions must prioritize a very high DHW share (~30–35%) and a lower HVAC share compared to single-family archetypes.

### 4. Lodging (Hotel) DHW and Process Loads
* **Measured Ground Truth:** For lodging buildings, CBECS 2018 reports:
  * **Water Heating (DHW):** **18.56%** (111 TBtu)
  * **Cooking:** **12.71%** (76 TBtu)
  * **Refrigeration:** **4.52%** (27 TBtu)
  * **Combined Share:** **35.79%** of site energy.
* **Validation Outcome:** Reflects the heavy laundry, shower, and food-service demands in hotels, validating the need for a substantial DHW and cooking allocation in the hotel archetype.

---

## Detailed Data Source References

1. **U.S. Energy Information Administration (EIA) Commercial Buildings Energy Consumption Survey (CBECS) 2018**
   * **Table:** Table E1. Major fuels consumption by end use, 2018.
   * **Release Date:** December 2022.
   * **Link:** [EIA 2018 CBECS Consumption and Expenditures Tables](https://www.eia.gov/consumption/commercial/data/2018/ce/xls/e1.xlsx) (Accessed: June 2026).
   * **Methodology:** End-use consumption is estimated using a combination of survey data and engineering models. Estimates represent total consumption in buildings possessing the equipment.

2. **U.S. Energy Information Administration (EIA) Residential Energy Consumption Survey (RECS) 2020**
   * **Tables:** 
     * Table CE5.1a Detailed household site electricity end-use consumption, part 1—totals, 2020.
     * Table CE5.1b Detailed household site electricity end-use consumption, part 2—totals, 2020.
     * Table CE5.2 Detailed household natural gas and propane end-use consumption—totals, 2020.
   * **Release Date:** June 2023.
   * **Link:** [EIA 2020 RECS Consumption and Expenditures Tables](https://www.eia.gov/consumption/residential/data/2020/) (Accessed: June 2026).
   * **Methodology:** End-use disaggregation is modeled statistically using conditional demand analysis (CDA) combined with engineering calibrations.
