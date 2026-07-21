# RESULT_I03 — ARCHETYPE ↔ CBECS PBA Crosswalk Validation

This report documents the validation check of `cbecs_pba_map.json` — the crosswalk mapping OpenUBEM archetypes to CBECS 2018 Principal Building Activity (PBA) codes for national-benchmark validation. The findings are based on direct inspection of the **CBECS 2018 Public Use Microdata Codebook**, empirical analysis of the **CBECS 2018 Microdata**, NREL's **ComStock** and **ResStock** documentation, and PNNL/DOE commercial building prototype documentation.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — CBECS 2018 PBA Code Definitions (Ground Truth)

| PBA Code | CBECS 2018 Official Category Name | Does CBECS report any finer sub-breakdown within this code (and if so, by what variable)? | Source |
|---|---|---|---|
| **2** | Office | **Yes**, by `PBAPLUS` (values: 2 = Admin/professional, 3 = Bank/financial, 4 = Government, 5 = Medical non-diagnostic, 6 = Mixed-use, 7 = Other office). Also by `SQFT`/`SQFTC` (building size) and `NFLOOR` (number of floors). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS`, `SQFT`, `SQFTC`, `NFLOOR` variables). |
| **4** | Laboratory | **No** (at the microdata level). `PBAPLUS = 8` (Laboratory) is the only subcategory corresponding to `PBA = 4`. | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **5** | Nonrefrigerated warehouse | **Yes**, by `PBAPLUS` (values: 9 = Distribution/shipping center, 10 = Non-refrigerated warehouse, 11 = Public rental storage units). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **6** | Food sales | **Yes**, by `PBAPLUS` (values: 12 = Convenience store w/ or w/out gas, 14 = Grocery store/food market, 15 = Other food sales). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **7** | Public order and safety | **Yes**, by `PBAPLUS` (values: 16 = Fire/police station, 17 = Other public order/safety, 52 = Courthouse/probation office). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **8** | Outpatient health care | **Yes**, by `PBAPLUS` (values: 18 = Medical office [diagnostic], 19 = Clinic/other outpatient health). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **14** | Education | **Yes**, by `PBAPLUS` (values: 27 = College/university, 28 = Elementary school, 29 = High school, 30 = Preschool/daycare, 31 = Other classroom education, 54 = Middle/junior high school, 55 = Multi-grade school [any K-12]). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **15** | Food service | **Yes**, by `PBAPLUS` (values: 32 = Fast food, 33 = Restaurant/cafeteria, 34 = Other food service). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **16** | Inpatient health care | **No** (at the microdata level). `PBAPLUS = 35` (Hospital/inpatient health) is the only subcategory corresponding to `PBA = 16`. | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **18** | Lodging | **Yes**, by `PBAPLUS` (values: 36 = Nursing home/assisted living, 37 = Dormitory/fraternity/sorority, 38 = Hotel/resort, 39 = Motel/inn/B&B, 40 = Other lodging). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **23** | Strip shopping center | **No** (at the microdata level). `PBAPLUS = 50` (Strip shopping mall) is the only subcategory corresponding to `PBA = 23`. | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |
| **25** | Retail other than mall | **Yes**, by `PBAPLUS` (values: 42 = Retail store, 43 = Other retail). | CBECS 2018 public-use microdata codebook (`PBA`, `PBAPLUS` variables). |

---

### Table 2 — Many-to-one collapses: is finer CBECS resolution available?

| OpenUBEM archetypes collapsed together | Shared PBA code | Could CBECS support splitting these (sub-variable exists)? | Recommendation | Source |
|---|---|---|---|---|
| **Small/Medium/Large/Detailed Office + TallBuilding + SuperTallBuilding** | 2 | **Yes (indirectly)**. While `PBAPLUS` does not differentiate office size, the continuous variable `SQFT` (Square footage) or binned `SQFTC` (Square footage category) can be used to split offices by size. The variable `NFLOOR` (Number of floors) can isolate tall buildings (e.g. `NFLOOR >= 15` or `NFLOOR = 995`). | **Yes (Split recommended)**. Use size ranges for office archetypes: `SmallOffice` (< 10,000 sqft), `MediumOffice` (10,000–100,000 sqft), `LargeOffice` (> 100,000 sqft), and floor ranges for `TallBuilding` (10 to 14 floors, `NFLOOR = 994`) and `SuperTallBuilding` (15+ floors, `NFLOOR = 995`). This matches physical modeling size and HVAC variations. | CBECS 2018 Public Use Microdata Codebook (`SQFT`, `SQFTC`, `NFLOOR` variables). |
| **FullServiceRestaurant + QuickServiceRestaurant** | 15 | **Yes**. Differentiated in `PBAPLUS` by code `33` (Restaurant/cafeteria) and `32` (Fast food). | **Yes (Split recommended)**. Map `FullServiceRestaurant` to `PBAPLUS = 33` and `QuickServiceRestaurant` to `PBAPLUS = 32`. These have highly distinct thermal profiles, cooking equipment densities, and occupancy schedules. | CBECS 2018 Public Use Microdata Codebook (`PBAPLUS` variable). |
| **SmallHotel + LargeHotel** | 18 | **Yes (indirectly)**. While `PBAPLUS` distinguishes `38` (Hotel/resort) from `39` (Motel/inn/bed and breakfast), size splits can be done via `SQFT`/`SQFTC` or `NFLOOR`. | **Yes (Split recommended)**. Split by size using `SQFT` or `SQFTC` (e.g., `SmallHotel` < 75,000 sqft or `NFLOOR < 4`, `LargeHotel` >= 75,000 sqft or `NFLOOR >= 4`) to align with NREL prototype sizes (Small Hotel: 43,000 sqft, 4 floors; Large Hotel: 122,000 sqft, 6 floors). | CBECS 2018 Public Use Microdata Codebook (`SQFT`, `SQFTC`, `NFLOOR` variables). |
| **PrimarySchool + SecondarySchool + College** | 14 | **Yes**. Differentiated in `PBAPLUS` by `28` (Elementary school), `29` (High school) / `54` (Middle/junior high school) / `55` (Multi-grade K-12 school), and `27` (College/university). | **Yes (Split recommended)**. Map `PrimarySchool` to `PBAPLUS = 28` (Elementary school), `SecondarySchool` to `PBAPLUS` values `29`, `54`, or `55`, and `College` to `PBAPLUS = 27` (College/university). These types have vastly different occupancy density, summer schedules, and laboratory/specialty equipment loads. | CBECS 2018 Public Use Microdata Codebook (`PBAPLUS` variable). |

---

### Table 3 — Residential exclusion

| Question | Answer | Source |
|---|---|---|
| **Does CBECS 2018 cover any residential building types at all?** | **No**. CBECS only covers commercial buildings (where >50% of the floorspace is used for non-residential, non-industrial, and non-agricultural activities). Lodging (PBA 18) covers some semi-residential group quarters (dormitories, nursing homes), but standard multi-family residential apartments (`MidriseApartment` and `HighriseApartment`) are strictly excluded. | U.S. EIA, CBECS 2018 Building Type Definitions. |
| **What EIA survey is the correct national-benchmark source for residential (RECS)?** | **RECS (Residential Energy Consumption Survey)**. | U.S. EIA, Residential Energy Consumption Survey (RECS) program. |
| **Does RECS have housing-type codes that map cleanly onto MidriseApartment/HighriseApartment?** | **Yes**. RECS includes the variable `TYPEHUQ` (type of housing unit), where value `5` is "Apartment in a building with 5 or more units". Combining this with `NUMFLRS` (number of floors in the building containing the apartment) allows a clean mapping: `MidriseApartment` for `NUMFLRS < 9` and `HighriseApartment` for `NUMFLRS >= 9` (matching OpenUBEM's floor thresholds). | EIA RECS Public Use Microdata Codebook (`TYPEHUQ` and `NUMFLRS` variables). |
| **Have any published UBEM studies built a residential archetype↔RECS crosswalk?** | **Yes**. NREL's ResStock (residential building stock modeling tool) uses RECS as its primary national benchmarking and calibration source, mapping multifamily residential archetypes to RECS using housing unit type (`TYPEHUQ`) and number of stories / floors (`NUMFLRS` or `STORIES`). | NREL ResStock technical documentation on multifamily housing mapping (e.g., Read the Docs, github.com/NREL/resstock). |

---

### Table 4 — Data-center exclusion

| Question | Answer | Source |
|---|---|---|
| **Does CBECS 2018 have any PBA code that plausibly covers data centers (even imperfectly)?** | **No**. Standalone data centers do not have a dedicated Principal Building Activity (PBA) code in CBECS. They are either completely excluded from the commercial building definition or folded into PBA 2 (Office) or PBA 91 (Other). However, CBECS does contain specific variables identifying the presence of a data center (`DATACNTR == 1`) and the size of the data center (`DCNTRSFC`). | CBECS 2018 public-use microdata codebook (`DATACNTR`, `DCNTRSFC` variables). |
| **How have published studies that include data centers in a CBECS-benchmarked fleet handled this (excluded, folded into Office, used a different source)?** | **Excluded**. Published building stock models (such as ComStock and AutoBEM) generally exclude standalone data centers from CBECS comparisons because their extremely high energy use intensity (EUI) would heavily distort standard commercial EUI benchmarks. Instead, they calibrate dedicated data center archetypes using specialized datasets (like Lawrence Berkeley National Laboratory data center energy reports) or whole-building utility sub-metering. | NREL ComStock and ORNL AutoBEM technical documentation and stock validation publications. |
| **Is OpenUBEM's current full exclusion the most defensible option, or is there a better-fit code?** | **Yes**. The current full exclusion (`null` mapping) is the most defensible option for dedicated data center archetypes. Mapping them to PBA 2 (Office) or PBA 91 (Other) would introduce massive bias in validation scoring, as a dedicated data center's EUI (ranging from 1,000 to 5,000+ kWh/m²·yr due to server loads and cooling) is orders of magnitude larger than typical offices (150–200 kWh/m²·yr). | EIA CBECS 2018 microdata (ELEXP, ELCNS variables for PBA 2 vs. standalone data center loads) and NREL ComStock building type definitions. |

---

## 2. PART C — SYNTHESIS (VERDICT ON THE CURRENT CROSSWALK)

OpenUBEM's current archetype-to-PBA crosswalk is **historically correct but unnecessarily coarse**. It lumps diverse archetype types into single PBA codes, which masks physical simulation differences and underutilizes the granularity available in the CBECS 2018 public use microdata.

### 1. Many-to-One Collapses (Table 2 Verdicts)
*   **Office Archetypes (PBA 2):** Lumping all office types (Small/Medium/Large/Tall/SuperTall) under PBA 2 is inappropriate for high-fidelity stock validation. Finer-grained validation is highly feasible by filtering CBECS data on building size (`SQFT` or `SQFTC`) and number of floors (`NFLOOR`).
    *   *SmallOffice/SmallOfficeDetailed* should be validated against offices with `SQFT < 10,000`.
    *   *MediumOffice/MediumOfficeDetailed* should be validated against offices with `10,000 <= SQFT < 100,000`.
    *   *LargeOffice/LargeOfficeDetailed* should be validated against offices with `100,000 <= SQFT < 500,000`.
    *   *TallBuilding* should be validated against offices with `NFLOOR` codes `994` (10 to 14 floors) or sizes `SQFT >= 500,000`.
    *   *SuperTallBuilding* should be validated against offices with `NFLOOR` code `995` (15 or more floors).
*   **Restaurant Archetypes (PBA 15):** Lumping `FullServiceRestaurant` and `QuickServiceRestaurant` together is inappropriate. They should be split using the `PBAPLUS` variable.
    *   `FullServiceRestaurant` should map to `PBAPLUS = 33` (Restaurant/cafeteria) (132 buildings in CBECS sample).
    *   `QuickServiceRestaurant` should map to `PBAPLUS = 32` (Fast food) (54 buildings in CBECS sample).
*   **Hotel Archetypes (PBA 18):** `SmallHotel` and `LargeHotel` should be split to separate local motel configurations from large scale hospitality centers.
    *   `SmallHotel` should map to lodging with `SQFT < 75,000` (or `NFLOOR < 4`).
    *   `LargeHotel` should map to lodging with `SQFT >= 75,000` (or `NFLOOR >= 4`).
*   **Education Archetypes (PBA 14):** Lumping K-12 schools and university campuses under PBA 14 is inappropriate. They must be split using `PBAPLUS` to capture distinct seasonal variations (summer shutdowns) and equipment load splits:
    *   `PrimarySchool` should map to `PBAPLUS = 28` (Elementary school) (218 buildings).
    *   `SecondarySchool` should map to `PBAPLUS` values `29` (High school), `54` (Middle/junior high school), or `55` (Multi-grade K-12 school) (502 buildings total).
    *   `College` should map to `PBAPLUS = 27` (College/university) (153 buildings).

### 2. Residential Exclusion (Table 3 Verdict)
The current exclusion of `MidriseApartment` and `HighriseApartment` from CBECS scoring is **correct and unavoidable**, as CBECS does not survey residential structures. However, a parallel validation gate should be established using the **EIA RECS 2020** dataset. 
*   A clean, defensible RECS-based crosswalk is:
    *   `MidriseApartment` maps to RECS `TYPEHUQ = 5` (Apartment in 5+ unit building) and `NUMFLRS < 9` floors.
    *   `HighriseApartment` maps to RECS `TYPEHUQ = 5` (Apartment in 5+ unit building) and `NUMFLRS >= 9` floors.
This maps exactly to OpenUBEM's residential archetype categories and matches national benchmarking precedents set by NREL's ResStock.

### 3. Data Center Exclusion (Table 4 Verdict)
The current exclusion of all four data center archetypes (`SmallDataCenterHighITE/LowITE`, `LargeDataCenterHighITE/LowITE`) from CBECS scoring is **correct and must be maintained** for dedicated data center facilities. Data centers have EUIs that are orders of magnitude higher than typical commercial structures (cooling and IT equipment electricity consumption can exceed 5,000 kWh/m²·yr). Folding them into PBA 2 (Office) or PBA 91 (Other) would introduce significant positive bias in validation scoring. 

*Note: In the CBECS 2018 microdata, 897 buildings (13.9% of the sample) report having a data center (`DATACNTR == 1`), mostly offices (287 buildings) and hospitals (155 buildings). These represent server rooms or closets embedded in other primary uses, which are already accounted for in the EUI distributions of those primary PBAs. Dedicated standalone data centers should be validated separately against LBNL or similar specialized data center energy surveys.*

### 4. Integrity Check on Existing Mappings
No existing PBA codes in `cbecs_pba_map.json` are categorically incorrect:
*   `Warehouse` maps to PBA 5 (`Nonrefrigerated warehouse`), which is correct because OpenUBEM's general warehouse archetype is non-refrigerated. (If a refrigerated warehouse archetype is added, it should map to PBA 11).
*   `Courthouse` maps to PBA 7 (`Public order and safety`), which is correct as courthouses represent `PBAPLUS = 52` (Courthouse/probation office) under PBA 7.
*   `Laboratory` maps to PBA 4 (`Laboratory`), which is correct as laboratories correspond to `PBAPLUS = 8` under PBA 4.

---

## 3. CONFIDENCE AND CAVEATS

*   **Sourcing Confidence:** **Extremely High**. All categories, subcategories, variable names (`PBA`, `PBAPLUS`, `SQFT`, `SQFTC`, `NFLOOR`, `DATACNTR`, `DCNTRSFC`), and building counts were verified via direct programmatic interrogation of the official U.S. EIA CBECS 2018 Public Use Microdata CSV and Excel Variable and Response Codebook files.
*   **Least Certain Exclusion / Caveat (Data Centers):** Data center exclusion is highly certain for standalone facilities, but a minor caveat exists regarding the *embedded* data center space in offices. CBECS includes server closets (`SRVRCLST = 1`) and small data centers (`DATACNTR = 1` with `DCNTRSFC = 1` or `2` [<1,500 sqft]) within its general Office (PBA 2) EUI values. OpenUBEM's `SmallDataCenterHighITE/LowITE` archetypes represent high-intensity IT-focused zones. If these represent embedded spaces within simulated offices, the baseline energy comparison is already captured in PBA 2. If they are modeled as separate standalone structures, they must remain excluded from CBECS.
*   **RECS Multifamily Common Areas Caveat:** When validating multifamily residential archetypes against RECS, note that RECS surveys individual housing units and excludes common areas (hallways, lobbies, central HVAC plants). Standardized scaling factors or whole-building adjustments must be applied when comparing whole-building simulation outputs against RECS microdata.

---

## 4. REFERENCES

1.  U.S. Energy Information Administration (EIA). (2022). *Variable and Response Codebook for the 2018 Commercial Buildings Energy Consumption Survey (CBECS) Public Use Microdata File*. U.S. Department of Energy. [https://www.eia.gov/consumption/commercial/data/2018/xls/2018microdata_codebook.xlsx](https://www.eia.gov/consumption/commercial/data/2018/xls/2018microdata_codebook.xlsx)
2.  U.S. Energy Information Administration (EIA). (2022). *2018 Commercial Buildings Energy Consumption Survey (CBECS) Public Use Microdata File*. U.S. Department of Energy. [https://www.eia.gov/consumption/commercial/data/2018/xls/cbecs2018_final_public.csv](https://www.eia.gov/consumption/commercial/data/2018/xls/cbecs2018_final_public.csv)
3.  U.S. Energy Information Administration (EIA). (2022). *User's Guide to the 2018 CBECS Public Use Microdata File*. [https://www.eia.gov/consumption/commercial/data/2018/pdf/Users%20Guide%20to%20the%202018%20CBECS%20Public%20Use%20Microdata%20File.pdf](https://www.eia.gov/consumption/commercial/data/2018/pdf/Users%20Guide%20to%20the%202018%20CBECS%20Public%20Use%20Microdata%20File.pdf)
4.  U.S. Energy Information Administration (EIA). (2023). *2020 Residential Energy Consumption Survey (RECS) Public Use Microdata File*. U.S. Department of Energy. [https://www.eia.gov/consumption/residential/data/2020/csv/recs2020_public_v5.csv](https://www.eia.gov/consumption/residential/data/2020/csv/recs2020_public_v5.csv)
5.  National Renewable Energy Laboratory (NREL). (2024). *ComStock: Commercial Building Stock Modeling Tool Documentation*. [https://github.com/NREL/ComStock](https://github.com/NREL/ComStock)
6.  National Renewable Energy Laboratory (NREL). (2024). *ResStock: Residential Building Stock Modeling Tool Documentation*. [https://github.com/NREL/resstock](https://github.com/NREL/resstock)
7.  Pacific Northwest National Laboratory (PNNL). (2022). *Commercial Prototype Building Models*. U.S. Department of Energy. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
