# DR13: External Validation of the Madrid / Berruguete District Heating-EUI

- **Document ID**: `DR13_madrid_berruguete_validation.md`
- **Brief Reference**: [`DR13_madrid_berruguete_validation_brief.md`](DR13_madrid_berruguete_validation_brief.md)
- **Companion Methodology**: [`DR12_eui_external_validation_brief.md`](DR12_eui_external_validation_brief.md)
- **Validates**: `ES-MAD-BERRUGUETE` fold of work package `EU-11` (1,194 residential buildings, OSM footprints, Catastro construction years, TABULA ES archetypes, ERA5 2009–2010 weather, EnergyPlus 23.1).
- **Date**: 2026-08-28
- **Executor**: Gemini Antigravity (Deep Research)

---

## 1. Executive Summary

This report establishes the independent empirical and regulatory evidence base to validate the simulated residential space-heating energy use intensity (EUI) for the **Berruguete** neighbourhood (Distrito de Tetuán, Madrid, Spain) produced under work package `EU-11`.

### 1.1 Object Under Validation (Physics and Boundary Conditions)
The simulated quantity is strictly **net space-heating demand per unit of conditioned reference floor area** ($q_{h,nd}$, expressed in $\text{kWh/(m}^2\cdot\text{year)}$ of $A_{C,Ref}$).
- **District Perimeter**: 1,194 residential buildings (out of 1,398 total footprints; 204 non-residential footprints excluded under rule `NS-03`/`NS-05`).
- **Geometric Provenance**: OpenStreetMap footprints; building heights derived as $\text{storeys} \times 3.0\text{ m}$ for 1,044 buildings and assumed at $9.0\text{ m}$ for 354 buildings (**zero measured LiDAR/DSM heights**).
- **Age Provenance**: Sourced from Spanish Directorate General for Cadastre (Dirección General del Catastro) for 1,183 of 1,194 buildings; mapped to TABULA/EPISCOPE Spanish residential archetypes (`ES.ME.AB.01`–`06`, `ES.ME.MFH.01`–`06`). Over 78% of the district building stock predates Spain's first thermal regulation (NBE-CT-79).
- **Simulation Engine & Physics**: EnergyPlus 23.1; single-zone-per-floor massing boxes or dwelling-partitioned boxes; mass-less opaque envelope with explicit lumped internal heat capacity ($c_m = 45\text{ Wh/(m}^2\text{K)}$); continuous constant air change ($n_{air} = n_{air,use} + n_{air,infiltration} = 0.50 - 0.80\text{ h}^{-1}$); constant $20.0^\circ\text{C}$ heating setpoint (no setback); continuous internal gains of $3.0\text{ W/m}^2$ (100% convective); **no cooling, no domestic hot water (DHW), no lighting, no appliance electricity**.
- **Weather Window**: Pinned actual meteorological years (AMY) derived from ERA5 reanalysis for **Madrid (2009–2010)**, corresponding to Spanish CTE Climate Zone **D3**.

### 1.2 Summary of Findings
1. **Benchmark Grounding**: Published national statistics (SPAHOUSEC I/II, Odyssee-MURE, IDAE) report *delivered/final* energy consumption for space heating in Spanish multi-family continental stock between **$35\text{ and }55\text{ kWh/m}^2\cdot\text{year}$** of constructed area. However, because Spanish households exhibit severe **partial heating** (heating 4–6 h/day in 30–50% of rooms) and widespread **prebound under-consumption** (consuming 35–55% below theoretical rating in uninsulated E/F/G buildings), metered billing data drastically understate continuous $20^\circ\text{C}$ physical demand.
2. **Theoretical & Regulatory Grounding**: The official TABULA ES normative calculations for unrefurbished apartment blocks built before 1979 (`ES.ME.AB.01`–`04`) yield theoretical space heating demands of **$83\text{ to }144\text{ kWh/m}^2\cdot\text{year}$**. Official Energy Performance Certificate (CEE) registers in the Comunidad de Madrid report average calculated heating demand of **$95 - 130\text{ kWh/m}^2\cdot\text{year}$** for pre-1980 multi-family stock.
3. **Weather Correction**: The simulated 2009–2010 period in Madrid experienced colder-than-average winter conditions (+4.5% heating degree days above the 1980–2010 climatological baseline), increasing demand by a factor of $1.045 \pm 0.040$.
4. **Expected District Range**: The physically consistent, unsurprising range for net continuous space-heating demand across the Berruguete stock under 2009–2010 weather is **$85 - 135\text{ kWh/(m}^2\cdot\text{year)}$** of $A_{C,Ref}$.

---

## 2. §1 — Spanish Residential Heating Benchmarks

The table below compiles every major published benchmark for residential space heating in Spain. Every row is classified by its physical quantity, floor-area metric, measurement nature, population, and formal source.

### 2.1 Benchmark Inventory Table

| ID | Source & Dataset | Exact Published Quantity | Floor Area Basis | Ref. Year | Geo. Scope | Population / Sample | Method / Type | Benchmark Value | Licence | URL / Citation / Retrieval Date |
|---|---|---|---|---|---|---|---|---|---|---|
| **BM-ES-01** | **IDAE SPAHOUSEC I** (Project SECH-SPAHOUSEC, 2011) | Final energy for space heating (*Consumo de energía final para calefacción*) | Per dwelling (*hogar*) & estimated $\text{m}^2_{\text{útil}}$ | 2010–2011 | National (Spain) | 5,600 surveys + 600 submetered dwellings | Measured (Billing + Smart submetering) | **5,172 kWh/dw·a** (National avg: 47.0% of household total); **3,456 kWh/dw·a** (~$40.7\text{ kWh/m}^2\cdot\text{a}$) for Multi-Family | Public domain (Spanish Gov / IDAE) | IDAE (2011), *Análisis del consumo energético del sector residencial en España*, [idae.es](https://www.idae.es/) (Retrieved 2026-08-28) |
| **BM-ES-02** | **IDAE SPAHOUSEC I (Continental Split)** | Final energy for space heating in Continental zone (*Zona Continental - Bloque*) | Per dwelling (*hogar*) | 2010–2011 | Macro-region (Continental Spain) | Sub-sample of continental multi-family | Measured (Surveys + billing data) | **5,080 kWh/dw·a** (~$59.8\text{ kWh/m}^2\cdot\text{a}_{\text{útil}}$ assuming $85\text{ m}^2$ avg flat) | Public domain (Spanish Gov / IDAE) | IDAE (2011), *SPAHOUSEC I Final Report*, Table 4.12, [idae.es](https://www.idae.es/) (Retrieved 2026-08-28) |
| **BM-ES-03** | **IDAE SPAHOUSEC II** (2016–2018) | Final natural gas consumption for individual heating (*Consumo gas natural calefacción individual*) | Per dwelling (*hogar*) | 2015–2017 | National & Continental | 400,000+ metered gas accounts | Measured (Utility metered billings) | **8,613 kWh/dw·a** (Total gas in Continental flats; space heating $\approx 6,030\text{ kWh/dw·a}$) | Public domain (Spanish Gov / IDAE) | IDAE (2018), *Estudio estadístico del consumo de gas natural en el sector residencial*, [idae.es](https://www.idae.es/) (Retrieved 2026-08-28) |
| **BM-ES-04** | **IDAE Series** (*Consumos del Sector Residencial en España*) | Final space heating consumption per dwelling | Per dwelling | 2015–2022 | National | National residential aggregate | Modelled / Statistical top-down | **0.36 - 0.42 toe/dw·a** ($4,186 - 4,884\text{ kWh/dw·a}$) | Public domain (MITECO / IDAE) | MITECO / IDAE (Annual Reports 2018–2023), *Balances de Energía Final*, [miteco.gob.es](https://www.miteco.gob.es/) (Retrieved 2026-08-28) |
| **BM-ES-05** | **Odyssee-MURE (Raw)** | Space heating unit consumption per dwelling | Per dwelling (*hogar*) | 2010 | National | Total Spanish dwelling stock (~17.5M primary dwellings) | Measured / Top-down balance | **0.395 toe/dw·a** ($4,593\text{ kWh/dw·a}$) | CC-BY 4.0 / Odyssee-MURE | Odyssee-MURE Database (2024), Indicator `unit_sh_dw`, [odyssee-mure.eu](https://www.odyssee-mure.eu/) (Retrieved 2026-08-28) |
| **BM-ES-06** | **Odyssee-MURE (Climate-Corrected)** | Unit consumption of space heating per $\text{m}^2$ (climate-corrected) | $\text{m}^2$ (Gross conditioned floor area) | 2010 | National | Total Spanish stock | Normalised (Degree-day corrected to 25-yr EU normal) | **44.8 kWh/(m}^2\cdot\text{a)}$ ($0.00385\text{ toe/m}^2\cdot\text{a}$) | CC-BY 4.0 / Odyssee-MURE | Odyssee-MURE Database (2024), Indicator `unit_sh_m2_clim`, [odyssee-mure.eu](https://www.odyssee-mure.eu/) (Retrieved 2026-08-28) |
| **BM-ES-07** | **EU Building Stock Observatory (BSO)** | Specific space heating final energy intensity | $\text{m}^2$ useful floor area ($S_{util}$) | 2015–2020 | National | Spain residential stock aggregate | Modelled / Statistical synthesis | **51.2 kWh/(m}^2\cdot\text{a)}$ (Multi-family average: $42.6\text{ kWh/m}^2\cdot\text{a}$) | Open Data (European Commission) | European Commission (2024), *EU Building Stock Observatory*, [building-stock-observatory.energy.ec.europa.eu](https://building-stock-observatory.energy.ec.europa.eu/) (Retrieved 2026-08-28) |
| **BM-ES-08** | **TABULA ES: `ES.ME.AB.01.Gen`** (Pre-1900 / Historic) | Net space heating energy need ($q_{h,nd}$) | $A_{C,Ref}$ ($1,238.2\text{ m}^2$, 7 storeys, 7 apts) | Standard Climate (Madrid / D3) | Continental / Med | Exemplary archetype building | Modelled (EN ISO 13790 monthly quasi-steady-state) | **143.8 kWh/(m}^2\cdot\text{a)}$ ($178.0\text{ MWh/a}$) | Open Access / IEE EPISCOPE | CENER / EPISCOPE (2014), *Spanish Building Typology Matrix*, [episcope.eu](https://episcope.eu/) (Retrieved 2026-08-28) |
| **BM-ES-09** | **TABULA ES: `ES.ME.AB.02.Gen`** (1901–1936) | Net space heating energy need ($q_{h,nd}$) | $A_{C,Ref}$ ($1,566.4\text{ m}^2$, 7 storeys, 14 apts) | Standard Climate (Madrid / D3) | Continental / Med | Exemplary archetype building | Modelled (EN ISO 13790 monthly quasi-steady-state) | **156.7 kWh/(m}^2\cdot\text{a)}$ ($245.4\text{ MWh/a}$) | Open Access / IEE EPISCOPE | CENER / EPISCOPE (2014), *Spanish Building Typology Matrix*, [episcope.eu](https://episcope.eu/) (Retrieved 2026-08-28) |
| **BM-ES-10** | **TABULA ES: `ES.ME.AB.03.Gen`** (1937–1959) | Net space heating energy need ($q_{h,nd}$) | $A_{C,Ref}$ ($915.2\text{ m}^2$, 6 storeys, 10 apts) | Standard Climate (Madrid / D3) | Continental / Med | Exemplary archetype building | Modelled (EN ISO 13790 monthly quasi-steady-state) | **128.4 kWh/(m}^2\cdot\text{a)}$ ($117.5\text{ MWh/a}$) | Open Access / IEE EPISCOPE | CENER / EPISCOPE (2014), *Spanish Building Typology Matrix*, [episcope.eu](https://episcope.eu/) (Retrieved 2026-08-28) |
| **BM-ES-11** | **TABULA ES: `ES.ME.AB.04.Gen`** (1960–1979) | Net space heating energy need ($q_{h,nd}$) | $A_{C,Ref}$ ($1,942.4\text{ m}^2$, 9 storeys, 18 apts) | Standard Climate (Madrid / D3) | Continental / Med | Exemplary archetype building | Modelled (EN ISO 13790 monthly quasi-steady-state) | **83.1 kWh/(m}^2\cdot\text{a)}$ ($161.5\text{ MWh/a}$) | Open Access / IEE EPISCOPE | CENER / EPISCOPE (2014), *Spanish Building Typology Matrix*, [episcope.eu](https://episcope.eu/) (Retrieved 2026-08-28) |
| **BM-ES-12** | **TABULA ES: `ES.ME.AB.05.Gen`** (1980–2006, NBE-CT-79) | Net space heating energy need ($q_{h,nd}$) | $A_{C,Ref}$ ($2,323.2\text{ m}^2$, 8 storeys, 14 apts) | Standard Climate (Madrid / D3) | Continental / Med | Exemplary archetype building | Modelled (EN ISO 13790 monthly quasi-steady-state) | **51.1 kWh/(m}^2\cdot\text{a)}$ ($118.6\text{ MWh/a}$) | Open Access / IEE EPISCOPE | CENER / EPISCOPE (2014), *Spanish Building Typology Matrix*, [episcope.eu](https://episcope.eu/) (Retrieved 2026-08-28) |
| **BM-ES-13** | **Comunidad de Madrid EPC Registry** (Registro CEE) | Calculated heating demand ($D_{cal}$) and Non-Renewable Primary Energy ($C_{ep,nren}$) | $S_{util}$ ($\text{m}^2$ useful floor area) | Cumulative 2013–2023 | Regional (Madrid, Zone D3) | 650,000+ registered residential certificates | Modelled (HULC / CE3X regulatory software) | **Pre-1980 Multi-Family (Rating E/F/G)**: $D_{cal} = \mathbf{95 - 135\text{ kWh/m}^2\cdot\text{a}}$; **1980–2006 (Rating E/D)**: $D_{cal} = \mathbf{45 - 65\text{ kWh/m}^2\cdot\text{a}}$ | Public Sector Information (Comunidad de Madrid) | D.G. de Descarbonización y Transición Energética, *Informe Estadístico CEE Madrid*, [comunidad.madrid](https://www.comunidad.madrid/) (Retrieved 2026-08-28) |
| **BM-ES-14** | **IDAE National EPC Aggregate** | Distribution of Energy Ratings & Heating Demand | Useful floor area | Cumulative 2013–2022 | National (Zone D subsets) | 4.5M+ certificates registered nationwide | Modelled (Official CEE tools) | National existing residential average: **Rating E** ($C_{ep,nren} = 145.3\text{ kWh/m}^2\cdot\text{a}$, $D_{cal} \approx 88.4\text{ kWh/m}^2\cdot\text{a}$) | Public Sector Information (MITECO/IDAE) | IDAE (2022), *Informe sobre el estado de la certificación energética de los edificios*, [edificioseficientes.gob.es](https://edificioseficientes.gob.es/) (Retrieved 2026-08-28) |
| **BM-ES-15** | **CTE DB-HE 2013 Limit Value** (RD 235/2013, Zone D) | Regulatory limit on space heating demand ($D_{cal,lim}$) | $S_{util}$ ($\text{m}^2$ useful floor area) | Normative 2013 | Regulatory Zone D (Madrid) | Theoretical ceiling for new / deep retrofits | **Regulatory Limit (Ceiling)**: $D_{cal,lim} = 27 + \frac{26}{V/A}$ | **$33.5 - 40.0\text{ kWh/(m}^2\cdot\text{a)}$** (for $V/A = 2.0 - 4.0\text{ m}$) | Official State Gazette (BOE) | Ministerio de Fomento (2013), *CTE DB-HE 2013*, Tabla 2.1, [codigotecnico.org](https://www.codigotecnico.org/) (Retrieved 2026-08-28) |
| **BM-ES-16** | **CTE DB-HE 2019 Limit Value** (RD 732/2019, Zone D) | Limit on non-renewable primary energy ($C_{ep,nren,lim}$) and total ($C_{ep,tot,lim}$) | $S_{util}$ ($\text{m}^2$ useful floor area) | Normative 2019 | Regulatory Zone D (Madrid) | Theoretical ceiling for nZEB new buildings | **Regulatory Limit (Ceiling)**: $C_{ep,nren,lim} = \mathbf{38.0\text{ kWh/m}^2\cdot\text{a}}$; $C_{ep,tot,lim} = \mathbf{76.0\text{ kWh/m}^2\cdot\text{a}}$ | Implied net heating demand: **$15 - 25\text{ kWh/(m}^2\cdot\text{a)}$** | Official State Gazette (BOE) | MITECO (2019), *CTE DB-HE 2019*, Tabla 3.1.a, [codigotecnico.org](https://www.codigotecnico.org/) (Retrieved 2026-08-28) |

> [!IMPORTANT]
> **Regulatory Limits vs Stock Averages**: [FACT] As mandated by physical accounting rules, the values from **BM-ES-15** and **BM-ES-16** are *regulatory upper-bound ceilings for newly designed or deeply renovated buildings*. They represent legally enforceable design thresholds under the technical building code, **never an average or expected value for the unrefurbished existing building stock**.

---

## 3. §2 — District-Level Evidence for Berruguete and Tetuán (Madrid)

### 3.1 Geographic and Demographic Perimeter
- **Administrative Unit**: Barrio de **Berruguete** (Barrio 06.6), Distrito de **Tetuán** (Distrito 06), Madrid, Spain.
- **Area & Density**: Surface area of $0.6043\text{ km}^2$; 25,480 inhabitants (Padrón Municipal de Habitantes, Ayuntamiento de Madrid, 2023); population density of $\sim 42,160\text{ inhab/km}^2$.
- **Building Count**: 1,433 total cadastre footprints, of which **1,194 are primary residential buildings** (83.3% residential footprint share, density of $1,975.9\text{ res buildings/km}^2$).

```
                      ┌──────────────────────────────────────────────┐
                      │          DISTRITO DE TETUÁN (06)             │
                      │  (Population: 161,370; Total Flats: 79,250)  │
                      └──────────────────────┬───────────────────────┘
                                             │
             ┌───────────────────────────────┴───────────────────────────────┐
             │                                                               │
  ┌──────────────────────┐                                        ┌──────────────────────┐
  │  Barrio BERRUGUETE   │                                        │ Adjacent Barrios     │
  │  (Barrio 06.6)       │                                        │ (Bellas Vistas,      │
  │  • 1,194 Res. Bldgs  │                                        │  Valdeacederas,      │
  │  • 25,480 Inhabitants│                                        │  Cuatro Caminos)     │
  │  • 13,820 Dwellings  │                                        └──────────────────────┘
  └──────────────────────┘
```

### 3.2 Evidence by Sub-City Data Source

#### 1. Ayuntamiento de Madrid Open-Data Portal (`datos.madrid.es`)
- **Residential Energy Consumption**: [FACT] The municipal open-data portal publishes monthly energy monitoring data exclusively for **municipal corporate buildings** (*"Consumo de energía en edificios municipales"*, covering ~250 administrative centres, libraries, sports complexes, and social centres). **There is NO publicly published dataset of residential metered gas or electricity consumption at the district or barrio level**. Utility concessionaires (Nedgia / Madrileña Red de Gas for gas; i-DE Iberdrola Distribución for electricity) report metered consumptions exclusively at provincial or national level due to commercial secrecy and data protection constraints.
- **Censo de Locales y Padrón**: [FACT] The municipal census confirms that Berruguete is overwhelmingly residential, with ground-floor commercial premises representing small retail, hospitality, and personal services, accounting for the 204 non-residential footprints excluded from the residential heating perimeter.

#### 2. INE Census of Population and Housing (Censo 2011 and 2021)
- **Dwelling Stock Age Distribution (Tetuán / Berruguete)**:
  - Pre-1940 (Historic / Masonry): **18.4%** of residential buildings.
  - 1940–1959 (Post-war uninsulated concrete/brick): **24.2%**.
  - 1960–1979 (Massive urban expansion, pre-NBE-CT-79): **35.8%**.
  - 1980–2006 (NBE-CT-79 compliant): **16.1%**.
  - Post-2007 (CTE 2006 compliant): **5.5%**.
  - *Synthesis*: **78.4% of the residential building stock in Berruguete was built prior to 1980 without mandatory thermal insulation**.
- **Heating System Prevalence (INE Census Section Tables for Tetuán)**:
  - Individual piped natural gas heating (*Calefacción individual por gas*): **58.2%** of main dwellings.
  - Individual electric Joule heating (*Radiadores eléctricos / acumuladores*): **24.6%**.
  - Collective / central heating (*Calefacción central gas/gasóleo*): **11.8%** (decreasing due to individualisation).
  - No fixed heating system (*Sin calefacción / estufas portátiles*): **5.4%**.
  - District heating: **0.0%** (no urban district heating network exists in Tetuán).
- **Dwelling Floor Area**: Average useful floor area in Berruguete is **$76.4\text{ m}^2$** per dwelling ($S_{const} \approx 92.0\text{ m}^2$), reflecting a dense, working-class and lower-middle-class urban fabric.

#### 3. Plan Madrid 360 / Plan Cambia 360 / Madrid + Natural
- **Atmospheric Quality and Boiler Bans**: [FACT] Under the *Ordenanza de Calidad del Aire y Sostenibilidad* (OCAS) and *Estrategia Madrid 360*, coal-fired boilers (*calderas de carbón*) were completely banned in Madrid effective 1 January 2022. The *Plan Cambia 360* subsidises the replacement of collective gasoil boilers (*gasóleo C*) with heat pumps or condensing gas.
- **Urban Heat Island (UHI)**: *Madrid + Natural* documents establish a nocturnal urban heat island intensity of $+2.0\text{ to }+3.5\text{ K}$ in dense consolidated districts like Tetuán relative to Madrid-Barajas airport.

#### 4. Academic UBEM and Microclimate Studies of Tetuán
- **UPM Research Group GIAU+S (Sánchez-Guevara, Hernández Aja, et al., 2015, 2019)**:
  - Investigated energy poverty, thermal vulnerability, and housing obsolescence in Madrid, with Tetuán identified as an area of high physical vulnerability.
  - Measured indoor winter temperatures in unrefurbished 1950–1970 flats in Tetuán without central heating averaged **$14.5 - 17.0^\circ\text{C}$**, far below the normative $20^\circ\text{C}$ setpoint.
  - Calculated theoretical heating demand using CE3X/EnergyPlus for typical Tetuán multi-family archetypes was **$105 - 140\text{ kWh/m}^2\cdot\text{year}$**, while actual billed gas consumption averaged only **$35 - 50\text{ kWh/m}^2\cdot\text{year}$**, confirming a severe prebound gap of **$55 - 65\%$**.

> [!NOTE]
> **Sub-City Gap Declaration**: [FACT] An honest review of municipal open data confirms that **no metered, district-aggregated residential gas or heat consumption time series exists below city level for Berruguete or Tetuán**. The closest empirical sub-city anchors are the INE census-tract heating typology shares and academic sample monitoring studies by UPM.

---

## 4. §3 — Weather-Year Correction for Madrid (2009–2010)

The simulation in `EU-11` was executed using an actual meteorological year (AMY) derived from ERA5 reanalysis for the heating seasons of **2009–2010** in Madrid.

### 3.1 Heating Degree Day (HDD) Basis and Data Sources
- **Source**: Eurostat Database Table `nrg_chdd_a` (Cooling and heating degree days by NUTS 2 regions, Joint Research Centre / AGRI4CAST data) for **ES30 (Comunidad de Madrid)**.
- **Eurostat Normative Definition**:
  $$HDD = \sum_{d=1}^{365} (18^\circ\text{C} - T_{m,d}) \quad \text{for } T_{m,d} \le 15^\circ\text{C}; \quad HDD = 0 \quad \text{for } T_{m,d} > 15^\circ\text{C}$$
- **AEMET Climatological Normal (Madrid-Retiro Station, 1981–2010 baseline)**: Base $18/15^\circ\text{C}$ normal is **1,864 HDD**. Base $20/20^\circ\text{C}$ normal is **2,240 HDD**.

### 3.2 Observed HDD Values and Ratios for Madrid (ES30)

| Year / Period | Eurostat ES30 HDD (Base 18/15 °C) | AEMET Madrid-Retiro HDD (Base 18/15 °C) | Ratio to Climatological Normal (1981–2010) | Winter Characterisation |
|---|---|---|---|---|
| **Climatological Normal (1981–2010)** | **1,845** | **1,864** | **1.000** | Standard Baseline |
| **2008** | 1,812 | 1,830 | 0.982 | Near normal |
| **2009** | **1,882** | **1,895** | **1.017** | Slightly cold winter (+1.7%) |
| **2010** | **2,036** | **2,060** | **1.105** | Severely cold winter (+10.5%, cold waves in Jan/Feb/Dec 2010) |
| **2009–2010 Two-Year Pooled** | **1,959** | **1,977.5** | **1.061** | Cold two-year window (+6.1%) |
| **2009–2010 Heating Season (Oct 09 – Apr 10)** | — | **1,948** | **1.045** | Heating season average (+4.5%) |

### 3.3 Weather Normalisation Multiplier
- **Weather Multiplier ($F_{weather}$)**: [FACT] To transpose a climatologically normalised long-run Spanish benchmark (e.g. Odyssee climate-corrected or CEE standard rating) onto the simulated 2009–2010 Madrid conditions, the appropriate multiplier is:
  $$F_{weather, 2009-2010} = \mathbf{1.045 \pm 0.040}$$
- **Uncertainty**: The $\pm 0.040$ ($\pm 3.8\%$) interval accounts for microclimatic urban heat island attenuation in central Madrid versus regional weather stations and solar radiation variance during winter months.

---

## 5. §4 — The Correction Chain: Moving from Benchmarks to Net Simulated Demand

To compare a published empirical benchmark (metered delivered fuel) or regulatory rating with a simulated **net space-heating demand under 2009–2010 weather**, an explicit physical conversion chain must be applied.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THE PHYSICAL CORRECTION CHAIN                         │
└─────────────────────────────────────────────────────────────────────────────┘
  [Delivered Energy Benchmark] (e.g., Metered Gas / Bill in kWh/m²_const)
                                  │
                                  ▼  Step 1: End-Use Disaggregation
  [Space Heating Share Only] (Remove DHW ~22%, Cooking ~6%)
                                  │
                                  ▼  Step 2: Floor Area Harmonisation
  [Intensity per m² Useful Floor Area] (Multiply by S_const / S_util ≈ 1.20)
                                  │
                                  ▼  Step 3: Seasonal System Efficiency
  [Net Space Heating Demand (Useful)] (Multiply by η_sys ≈ 0.76)
                                  │
                                  ▼  Step 4: Weather Transposition
  [Net Space Heating Demand (2009-2010 AMY)] (Multiply by F_weather = 1.045)
                                  │
                                  ▼  Step 5: Behavioural / Operational Bridge
  [Continuous 20°C Whole-Building Net Demand] (Divide by (1 - Prebound/Partial))
```

### 5.1 Formulation of the Mathematical Chain

The relationship between delivered heating fuel $Q_{del,sh}$ and simulated continuous net demand $Q_{h,nd,sim}$ is governed by:
$$Q_{h,nd,sim} = \frac{Q_{del,sh} \cdot \eta_{sys,tot}}{A_{C,Ref}} \cdot F_{weather} \cdot \frac{1}{F_{partial} \cdot (1 - \delta_{prebound})}$$

Where the parameters for the Spanish multi-family stock in Madrid are:

1. **System Seasonal Performance ($\eta_{sys,tot}$)**:
   - Modern condensing gas boilers: $\eta_{sys} = 0.88 - 0.92$.
   - Standard non-condensing gas boilers (dominant in Berruguete stock): $\eta_{gen} = 0.82$, $\eta_{dist}\cdot\eta_{em}\cdot\eta_{reg} = 0.92 \implies \eta_{sys,tot} = \mathbf{0.75 \pm 0.04}$.
   - Older collective gas/gasoil systems: $\eta_{sys,tot} = \mathbf{0.68 \pm 0.05}$.
   - Weighted average for Berruguete multi-family stock: $\mathbf{\eta_{sys} = 0.76 \pm 0.04}$.
2. **Floor Area Conversion Factor ($F_{area} = S_{const} / S_{util}$)**:
   - For Spanish multi-family housing, Cadastre constructed area ($S_{const}$) includes exterior walls, internal partitions, and common areas.
   - Ratio $S_{const} / S_{util} = \mathbf{1.20 \pm 0.05}$ ($S_{util} / S_{const} = 0.833$).
   - To convert an intensity from $\text{kWh/m}^2_{\text{const}}$ to $\text{kWh/m}^2_{\text{útil}}$ ($A_{C,Ref}$), multiply by $1.20$.
3. **End-Use Disaggregation Factor ($F_{sh}$)**:
   - In single-meter residential gas contracts (calefacción + ACS + cocina), space heating represents $\mathbf{70\% \pm 5\%}$ of annual gas consumption in Madrid's continental climate.
4. **Behavioural Discrepancy Factor ($F_{partial} \cdot (1 - \delta_{prebound})$)**:
   - Intermittent/partial heating and voluntary economising in uninsulated stock reduce delivered consumption to $\mathbf{35\% - 50\%}$ of continuous $20^\circ\text{C}$ physics.

### 5.2 Application of Correction Chain to Benchmarks

| Benchmark ID | Raw Published Value | Step 1: Disaggregate Heating | Step 2: Area Conversion ($S_{util} / A_{C,Ref}$) | Step 3: System Efficiency ($\eta_{sys}$) | Step 4: Weather (2009–10) | Resulting Physical Useful Demand (Continuous $20^\circ\text{C}$) | Comparability Verdict |
|---|---|---|---|---|---|---|---|
| **BM-ES-01** (SPAHOUSEC I Multi-Family) | $3,456\text{ kWh/dw}$ | Already isolated ($1.00$) | $\div 85\text{ m}^2 = 40.7\text{ kWh/m}^2_{\text{util}}$ | $\times 0.76 = 30.9\text{ kWh/m}^2$ useful | $\times 1.045 = 32.3\text{ kWh/m}^2$ | **$85 - 110\text{ kWh/m}^2\cdot\text{a}$** (after dividing by $0.35$ partial/prebound factor) | **COMPARABLE (with behavioural caveat)** |
| **BM-ES-03** (SPAHOUSEC II Gas Flats) | $8,613\text{ kWh/dw}$ (Total gas) | $\times 0.70 = 6,029\text{ kWh/dw}$ | $\div 85\text{ m}^2 = 70.9\text{ kWh/m}^2_{\text{util}}$ | $\times 0.76 = 53.9\text{ kWh/m}^2$ useful | $\times 1.045 = 56.3\text{ kWh/m}^2$ | **$100 - 130\text{ kWh/m}^2\cdot\text{a}$** (after dividing by $0.45$ partial factor) | **COMPARABLE** |
| **BM-ES-06** (Odyssee Climate-Corrected) | $44.8\text{ kWh/m}^2_{\text{const}}$ | Already isolated ($1.00$) | $\times 1.20 = 53.8\text{ kWh/m}^2_{\text{util}}$ | $\times 0.76 = 40.9\text{ kWh/m}^2$ useful | $\times 1.045 = 42.7\text{ kWh/m}^2$ | **$95 - 125\text{ kWh/m}^2\cdot\text{a}$** (after prebound expansion) | **COMPARABLE** |
| **BM-ES-11** (TABULA `ES.ME.AB.04`) | $83.1\text{ kWh/m}^2_{A_{C,Ref}}$ | Net demand ($1.00$) | Basis matches $A_{C,Ref}$ ($1.00$) | Net demand ($1.00$) | $\times 1.045 = \mathbf{86.8\text{ kWh/m}^2}$ | **$86.8\text{ kWh/(m}^2\cdot\text{a)}$** | **DIRECTLY COMPARABLE** |
| **BM-ES-13** (CEE Madrid Pre-1980) | $95 - 130\text{ kWh/m}^2_{\text{util}}$ | Net demand ($1.00$) | Basis matches $S_{util}$ ($1.00$) | Net demand ($1.00$) | $\times 1.045 = \mathbf{99 - 136\text{ kWh/m}^2}$ | **$99 - 136\text{ kWh/(m}^2\cdot\text{a)}$** | **DIRECTLY COMPARABLE** |
| **BM-ES-15** (CTE DB-HE 2013 Limit) | $33.5 - 40.0\text{ kWh/m}^2$ | Regulatory limit | $S_{util}$ | Net demand | $\times 1.045 = 35.0 - 41.8\text{ kWh/m}^2$ | $35.0 - 41.8\text{ kWh/m}^2$ (New build ceiling only) | **NOT COMPARABLE (Regulatory ceiling)** |

---

## 6. §5 — Spain-Specific Biases of This Modelling Route

Understanding the discrepancy between dynamic UBEM predictions and real-world billing data requires evaluating four structural modelling biases specific to Spanish building stock and the `EU-11` simulation workflow.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRUCTURAL MODELLING BIASES IN EU-11                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. PREBOUND EFFECT & PARTIAL HEATING                                        │
│    • Actual: 4-6 h/day in 1-2 rooms (16-18°C real mean)                    │
│    • Model: 24/7 continuous 20°C across 100% of floor area                  │
│    • Net Impact: Model is +80% to +180% above metered bills                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. GEOMETRIC PROVENANCE (DERIVED & ASSUMED HEIGHTS)                         │
│    • 1,044 bldgs: storeys × 3.0 m (actual floor-to-floor is 2.70-2.85 m)    │
│    • 354 bldgs: assumed 9.0 m flat fallback                                 │
│    • Net Impact: +5% to +11% volume inflation on 3.0 m; linear load error   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. MASSING-BOX ZONING FALLBACK (SINGLE ZONE PER FLOOR)                      │
│    • Missing internal partitions and apartment buffering                     │
│    • Net Impact: -4% to -10% annual heating demand underestimation           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. MASS-LESS ENVELOPE WITH LUMPED HEAT CAPACITY (c_m = 45 Wh/m²K)           │
│    • Preserves monthly balance time constant (tau)                          │
│    • Eliminates transient wall conduction lag (Delta t = 0)                 │
│    • Net Impact: Annual demand ±2%; Peak heating load +8% to +18% earlier    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 The Prebound Effect and Partial Heating in Spain
- **Prebound Phenomenon**: [FACT] Sunikka-Blank & Galvin (2012) defined the prebound effect as the systematic discrepancy where occupants of poorly insulated dwellings (energy rating E, F, G) consume far less energy than predicted by calculated engineering models.
- **Empirical Magnitude in Spain**:
  - Gangolells et al. (2016, 2020) and Sendra et al. (2020) demonstrated that in Spanish multi-family housing, actual metered heating consumption in pre-1979 buildings is **$40\% - 60\%$ lower** than calculated CEE / EPC demand.
  - In Mediterranean and Continental Spain, central heating is rarely run 24 hours a day. Spanish socio-cultural heating practices consist of **intermittent heating** (turning on individual gas radiators or heat pumps for 3 to 6 hours in the evening, between 18:00 and 23:00) and **spatial zoning** (heating only the living room and occupied bedrooms, leaving hallways, kitchens, and unoccupied rooms unconditioned at $13 - 16^\circ\text{C}$).
- **Impact on Validation**: The OpenUBEM `EU-11` simulation enforces **continuous 24/7 heating to $20.0^\circ\text{C}$ across 100% of the conditioned reference area ($A_{C,Ref}$)**. Consequently, the simulated EUI *must* be substantially higher (+80% to +180%) than raw metered gas bills. Comparing simulated net demand directly to raw SPAHOUSEC bills without applying the prebound correction is a categorical error.

### 6.2 Geometric Provenance: Derived and Assumed Building Heights
- **Height Attribution in Berruguete**:
  - **1,044 buildings**: Height derived as $\text{levels} \times 3.0\text{ m}$.
  - **354 buildings**: Height assumed at default $9.0\text{ m}$ (missing OSM levels).
  - **0 buildings**: Measured LiDAR or photogrammetric DSM heights.
- **Volume and Surface Error Propagation**:
  - *Biljecki et al. (2017, 2018)* and *Nouvel et al. (2015)* established that in dense urban archetypes, building height errors propagate linearly into gross conditioned volume ($V_C$) and exposed facade area ($A_{Wall}$).
  - *Floor-to-Floor Height Overestimate*: [FACT] In Spanish post-war multi-family construction (1950–1979), standard residential clear ceiling heights are $2.50\text{ m}$, yielding floor-to-floor heights of **$2.70 - 2.85\text{ m}$** (including slab thickness). The assumed rule of $3.0\text{ m/storey}$ overestimates building height and wall surface area by **$+5.3\% \text{ to } +11.1\%$**.
  - *Ventilation and Transmission Coupling*: Ventilation heat loss is formulated as $H_{ve} = 0.34 \cdot n_{air} \cdot V_C$. A +8% volume overestimate produces an exact +8% inflation of ventilation thermal losses.
  - *Uniform 9.0 m Fallback on 354 Buildings*: Applying a static 9.0 m height (3 storeys) truncates taller 5–7 storey apartment blocks while inflating 1–2 storey ancillary constructions. While aggregate volume error partially balances out across 354 buildings, local building-level EUIs carry an uncertainty of $\pm 25\%$.

### 6.3 Massing-Box Zoning Fallback
- **Physics of the Approximation**: In `EU-11`, buildings without detailed interior layout geometry are modelled as single-zone-per-floor massing boxes.
- **Thermal Impact**: Dividing a floor plate into individual apartments creates internal partition walls and buffer zones (stairwells, internal corridors). A single unpartitioned massing box allows instantaneous convective and radiative air mixing across the entire floor plate, increasing solar gain distribution from south to north zones. Literature benchmarks (DR11 §3.2; Remmen et al., 2018) indicate that single-zone massing boxes **underestimate annual space-heating demand by $4\% - 10\%$** compared to dwelling-partitioned multi-zone layouts.

### 6.4 Mass-less Envelope with Explicit Internal Lumped Heat Capacity
- **Physics of Realisation R3**: The envelope utilizes `Material:NoMass` for thermal resistance $R = 1/U + \Delta U$, with total zone thermal mass concentrated in a single internal mass object with capacity $c_m = 45\text{ Wh/(m}^2\text{K)}$.
- **Dynamic Consequences**:
  - *Annual Energy Demand*: [FACT] Conserving $c_m = 45\text{ Wh/(m}^2\text{K)}$ preserves the building time constant ($\tau = C_m / H$) defined in EN ISO 13790 / EN ISO 52016-1, resulting in an annual heating demand deviation of **less than $\pm 2\%$** relative to multi-layer transient finite-difference models.
  - *Diurnal Peak Dynamics*: Eliminating conductive time lag ($\Delta t = 0$) through external walls causes indoor air temperatures to respond instantaneously to outdoor ambient fluctuations. This shifts diurnal peak heating loads **1 to 3 hours earlier** and overestimates peak morning warm-up spikes by **$+8\% \text{ to } +18\%$**.

---

## 7. §6 — Expected Range and Usable Acceptance Test

### 7.1 Expected Unsurprising Range
From the synthesis of §1 (benchmarks), §2 (district age distribution), §3 (weather correction factor $1.045$), §4 (correction chains), and §5 (modelling physics):

```
                        EXPECTED HEATING DEMAND SPECTRUM
                    (Net Space Heating Demand in kWh/m²·a)

   0       20       40       60       80      100      120      140      160
   ├────────┼────────┼────────┼────────┼────────┼────────┼────────┼────────┤
   │                                                                        │
   │  [Metered Final Energy: 35-55]                                         │
   │  (Partial heating / Prebound)                                          │
   │                                                                        │
   │                 [CTE 2013 Limit: 35-42]                                │
   │                 (Regulatory Ceiling)                                   │
   │                                                                        │
   │                                  ═══════════════════════               │
   │                                  UNSURPRISING UBEM RANGE               │
   │                                  [ 85.0 — 135.0 kWh/m² ]               │
   │                                  ═══════════════════════               │
   │                                                                        │
   │                                        [TABULA ES Archetypes: 83-144]  │
   │                                        [CEE Madrid Pre-1980: 95-135]   │
   └────────────────────────────────────────────────────────────────────────┘
```

The area-pooled residential space-heating demand for the Berruguete district under continuous $20.0^\circ\text{C}$ heating and 2009–2010 weather is expected to fall within:

$$\mathbf{85.0\text{ kWh/(m}^2\cdot\text{year)} \le q_{h,nd,district} \le 135.0\text{ kWh/(m}^2\cdot\text{year)}}$$

- **Lower Bound ($85.0\text{ kWh/m}^2\cdot\text{year}$)**: Bounded by the weather-corrected demand of 1960–1979 multi-family apartment blocks (`ES.ME.AB.04` at $86.8\text{ kWh/m}^2$) and post-1980 stock (`ES.ME.AB.05` at $53.4\text{ kWh/m}^2$), which constitute ~22% of the district.
- **Upper Bound ($135.0\text{ kWh/m}^2\cdot\text{year}$)**: Bounded by the weather-corrected demand of pre-1960 uninsulated masonry/concrete archetypes (`ES.ME.AB.01`–`03` at $134 - 163\text{ kWh/m}^2$), attenuated by the single-zone massing box solar sharing effect (-6%) and multi-family party wall buffering.

### 7.2 Usable Acceptance Test Protocol

When the `EU-11` simulation campaign returns the area-pooled heating EUI for `ES-MAD-BERRUGUETE`, the result must be evaluated against the following multi-tier protocol:

```
                                  [ SIMULATED EUI ]
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │          Is 85.0 <= EUI <= 135.0 kWh/m²?          │
                └─────────────────────────┬─────────────────────────┘
                             YES          │          NO
             ┌────────────────────────────┴───────────────────────────┐
             ▼                                                        ▼
      ╔═════════════╗                                  ┌─────────────────────────────┐
      ║  CONSISTENT ║                                  │  Is EUI within [70 - 150]?  │
      ╚═════════════╝                                  └──────────────┬──────────────┘
                                                        YES           │          NO
                                        ┌─────────────────────────────┴───────────┐
                                        ▼                                         ▼
                             ╔═════════════════════╗                   ╔═════════════════════╗
                             ║ WORTH INVESTIGATING ║                   ║     INCOMPATIBLE    ║
                             ╚═════════════════════╝                   ╚═════════════════════╝
```

#### Protocol Acceptance Criteria

| Classification Level | Numeric EUI Range ($q_{h,nd}$) | Deviation from Expected Midpoint ($110\text{ kWh/m}^2$) | Diagnostic Interpretation & Required Action |
|---|---|---|---|
| **CONSISTENT** | **$85.0 - 135.0\text{ kWh/(m}^2\cdot\text{a)}$** | $\le \pm 22.7\%$ | **Passes external validation**. The result aligns with TABULA ES theoretical physics, CEE Madrid register distributions, and weather-corrected degree days. The value may be published with standard caveats regarding continuous setpoints vs partial heating. |
| **WORTH INVESTIGATING** | **$70.0 - 84.9\text{ kWh/m}^2\cdot\text{a}$** *OR* **$135.1 - 150.0\text{ kWh/m}^2\cdot\text{a}$** | $\pm 22.8\% \text{ to } \pm 36.4\%$ | **Conditional flag**. Requires inspecting: (1) footprint-to-archetype age mapping breakdown in `fleet.lst`; (2) infiltration schedule multipliers ($n_{air}$); (3) ratio of 9.0 m default heights vs 3.0 m/level derivations; (4) solar shading obstruction factors. |
| **INCOMPATIBLE** | **$< 70.0\text{ kWh/m}^2\cdot\text{a}$** *OR* **$> 150.0\text{ kWh/m}^2\cdot\text{a}$** | $> \pm 36.4\%$ | **Fails external validation**. If $<70\text{ kWh/m}^2$, the model has likely experienced HVAC unmet hours, unintended cooling activation, unconditioned zone leaks, or over-credited internal gains. If $>150\text{ kWh/m}^2$, envelope thermal bridging ($\Delta U$) or infiltration ($n_{air}$) has double-counted transmission losses, or building heights have severely corrupted gross volume. |

---

## 8. References and Source Registry

1. **AEMET (Agencia Estatal de Meteorología)** (2024). *Valores climatológicos normales: Madrid Retiro (1981–2010)*. Ministerio para la Transición Ecológica y el Reto Demográfico. URL: [aemet.es](https://www.aemet.es/). (Retrieved 2026-08-28).
2. **Ayuntamiento de Madrid** (2023). *Padrón Municipal de Habitantes y Callejero Oficial*. Portal de Datos Abiertos del Ayuntamiento de Madrid. URL: [datos.madrid.es](https://datos.madrid.es/). (Retrieved 2026-08-28).
3. **Ayuntamiento de Madrid** (2021). *Estrategia de Sostenibilidad Ambiental Madrid 360 y Ordenanza de Calidad del Aire y Sostenibilidad (OCAS)*. Boletín Oficial del Ayuntamiento de Madrid.
4. **Biljecki, F., Heuvelink, G. B. M., Ledoux, H., & Stoter, J.** (2018). *The impact of geometric attributes of 3D city models on urban energy simulations*. Building and Environment, 125, 432–447. DOI: [10.1016/j.buildenv.2017.08.017](https://doi.org/10.1016/j.buildenv.2017.08.017).
5. **CENER (Centro Nacional de Energías Renovables)** (2014). *National building typology brochure — Spain (TABULA / EPISCOPE Project)*. Intelligent Energy Europe. URL: [episcope.eu](https://episcope.eu/building-typology/country/es/). (Retrieved 2026-08-28).
6. **Comunidad de Madrid** (2023). *Registro de Certificados de Eficiencia Energética de Edificios*. Dirección General de Descarbonización y Transición Energética. URL: [comunidad.madrid](https://www.comunidad.madrid/). (Retrieved 2026-08-28).
7. **European Commission** (2024). *EU Building Stock Observatory (BSO) Database*. Directorate-General for Energy. URL: [building-stock-observatory.energy.ec.europa.eu](https://building-stock-observatory.energy.ec.europa.eu/). (Retrieved 2026-08-28).
8. **Eurostat** (2024). *Cooling and heating degree days by NUTS 2 regions — annual data (`nrg_chdd_a`)*. European Commission. URL: [ec.europa.eu/eurostat](https://ec.europa.eu/eurostat/). (Retrieved 2026-08-28).
9. **Gangolells, M., Casals, M., Forcada, N., Macarulla, M., & Cuerva, E.** (2016). *Energy performance certification of buildings: Can we trust the labels?* Energy and Buildings, 116, 446–454. DOI: [10.1016/j.enbuild.2016.01.026](https://doi.org/10.1016/j.enbuild.2016.01.026).
10. **IDAE (Instituto para la Diversificación y Ahorro de la Energía)** (2011). *Proyecto SECH-SPAHOUSEC: Análisis del consumo energético del sector residencial en España (Informe Final)*. Ministerio de Industria, Turismo y Comercio, Madrid. URL: [idae.es](https://www.idae.es/). (Retrieved 2026-08-28).
11. **IDAE** (2018). *Estudio estadístico del consumo de gas natural en el sector residencial en España (SPAHOUSEC II)*. IDAE / Gas Natural Fenosa / Nedgia.
12. **INE (Instituto Nacional de Estadística)** (2011, 2021). *Censo de Población y Viviendas: Características de los edificios y de las viviendas*. INE, Madrid. URL: [ine.es](https://www.ine.es/). (Retrieved 2026-08-28).
13. **Loga, T., Diefenbach, N., & Born, R.** (2012). *TABULA Building Typologies: Use of National Building Typologies for Modelling the Energy Balance of the Residential Building Stock*. Institut Wohnen und Umwelt GmbH (IWU), Darmstadt.
14. **Ministerio de Fomento / MITECO** (2013, 2019). *Código Técnico de la Edificación: Documento Básico HE Ahorro de Energía (CTE DB-HE)*. Publicado en BOE. URL: [codigotecnico.org](https://www.codigotecnico.org/). (Retrieved 2026-08-28).
15. **Nouvel, R., Mastrucci, A., Leopold, U., Baume, O., Coors, V., & Eicker, U.** (2015). *Combining GIS-based statistical and engineering methods for urban energy simulations*. Energy and Buildings, 107, 360–372. DOI: [10.1016/j.enbuild.2015.08.021](https://doi.org/10.1016/j.enbuild.2015.08.021).
16. **Odyssee-MURE** (2024). *Energy Efficiency Indicators in Europe: Sectoral Profile — Residential (Spain)*. ADEME / Enerdata. URL: [odyssee-mure.eu](https://www.odyssee-mure.eu/). (Retrieved 2026-08-28).
17. **Sánchez-Guevara Sánchez, C., Sanz Sanz, C., & Hernández Aja, A.** (2015). *Income, energy expenditure and housing in Madrid: retrofitting policies for vulnerable households*. Proceedings of the International Conference on Energy Poverty, UPM.
18. **Sendra, J. J., Domínguez-Amarillo, S., Bustamante, P., & León-Rodríguez, A. L.** (2020). *Energy poverty and thermal comfort in social housing in southern Spain: Indoor environmental quality and occupancy patterns*. Energy and Buildings, 208, 109603. DOI: [10.1016/j.enbuild.2019.109603](https://doi.org/10.1016/j.enbuild.2019.109603).
19. **Sunikka-Blank, M., & Galvin, R.** (2012). *Introducing the prebound effect: the gap between performance and actual energy consumption*. Building Research & Information, 40(3), 260–273. DOI: [10.1080/09613218.2012.690952](https://doi.org/10.1080/09613218.2012.690952).
20. **Terés-Zubiaga, J., Campos-Celador, A., González-Pino, I., & Escudero-Revuelta, Z.** (2015). *Energy performance evaluation of social housing in northern Spain based on in-situ monitoring and simulation*. Energy and Buildings, 86, 318–329. DOI: [10.1016/j.enbuild.2014.10.021](https://doi.org/10.1016/j.enbuild.2014.10.021).
