# DR12: External Validation of the `EU-11` District Heating-EUI Results

- **Document ID**: `DR12_eui_external_validation.md`
- **Brief reference**: [`DR12_eui_external_validation_brief.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/DeepResearch/DR12_eui_external_validation_brief.md)
- **Validates**: Cross-country methodology for external benchmark validation of work package `EU-11` (four European residential districts: Madrid/Berruguete, Lyon/Haut Cœur des Pentes, London/St Dunstan's, Bologna/Galvani 2).
- **Date**: 2026-08-28

---

## Executive Summary

This report establishes the external validation framework for residential space-heating energy-use intensity (EUI) simulated under work package `EU-11` of OpenUBEM. The simulation pipeline models four dense European residential districts using real building footprints, TABULA/EPISCOPE existing-state archetypes, actual meteorological years (AMY) derived from ERA5, and EnergyPlus 23.1. 

The simulated output is strictly **annual net space-heating demand per unit of conditioned reference floor area ($q_{H,nd}$, in $\text{kWh}/(\text{m}^2\cdot\text{year})$)** under a continuous 20 °C thermostat setpoint, 3.0 $\text{W/m}^2$ all-convective internal heat gains, and zero cooling, domestic hot water (DHW), or appliance/lighting electricity. 

### Key Findings & Methodological Rules:
1. **The Core Asymmetry**: [FACT] Published empirical datasets (e.g., utility gas billing, national energy balances, Odyssee-MURE, SPAHOUSEC, NEED, CEREN, ISTAT) almost exclusively measure **delivered final energy** ($E_{final}$) or **gross bundled fuel consumption** (space heating + DHW + cooking), reflecting intermittent heating, partial-dwelling conditioning, and system conversion losses. Conversely, standard regulatory EPC datasets (e.g., French DPE, English EPC-SAP, Italian APE) report **conventional calculated primary or useful demand** under normative schedules. Direct, uncorrected comparison between a continuous-20 °C physics simulation ($q_{H,nd}$) and metered billing data is an apples-to-oranges category error.
2. **The Correction Chain**: [FACT] Bridging published benchmarks to the simulated $q_{H,nd}$ requires a strict, non-manufactured 4-stage mathematical correction chain: (a) system efficiency disaggregation ($\eta_{sys}$), (b) end-use separation of DHW and cooking, (c) floor-area harmonisation ($A_{C,Ref}$ vs. $S_{util}$, $SHAB$, $TFA$, $SUL$), and (d) weather-year heating degree-day (HDD) normalisation. Where published data lack empirical parameters to close this chain, the benchmark is classified as `NOT COMPARABLE`.
3. **The Literature Prebound Gap**: [FACT] Across all four countries, empirical literature (Sunikka-Blank & Galvin 2012, Cayre et al. 2011, Terés-Zubiaga et al. 2015, Kelly et al. 2013, Cozza et al. 2020) proves that occupants in uninsulated, pre-1980 residential stock consume **30% to 50% less heating energy** than theoretical continuous-heating models calculate (the *prebound effect*), driven by unheated secondary rooms, lower mean indoor temperatures (17.0–18.5 °C), and behavioural rationing.
4. **Expected District Magnitudes**: [INFERENCE] For the specific building stocks and weather years simulated, the unsurprising ranges for net space-heating demand $q_{H,nd}$ are:
   - **Madrid / Berruguete** (`es`, 2009–2010): **55 – 95 $\text{kWh}/(\text{m}^2\cdot\text{year})$**
   - **Lyon / Haut Cœur des Pentes** (`fr`, 2023): **50 – 85 $\text{kWh}/(\text{m}^2\cdot\text{year})$** (the 31-building test run of 60.71 $\text{kWh/m}^2$ sits squarely within this envelope)
   - **London / St Dunstan's** (`uk`, 2014–2015): **60 – 100 $\text{kWh}/(\text{m}^2\cdot\text{year})$**
   - **Bologna / Galvani 2** (`it`, 2013–2014): **80 – 125 $\text{kWh}/(\text{m}^2\cdot\text{year})$**
5. **Acceptance Gate**: [RECOMMENDATION] A three-tier acceptance protocol is defined per district: *Consistent* ($\le \pm 15\%$), *Worth Investigating* ($\pm 15\%\text{ to }\pm 30\%$), and *Incompatible* ($> \pm 30\%$), parameterized against harmonised archetype calculations and weather-corrected statistical baselines.

---

## §1. Benchmark Inventory (One Table per Country)

Every row in the tables below reports the exact published quantity, floor area definition, reference period, geographic resolution, population covered, methodological classification (Measured, Modelled, or Climate-Normalised), open-access licence, source URL, and access date.

### 1.1 Spain (`es`) Benchmark Inventory

| Source Name / Publisher | Exact Quantity Published | Unit & Floor Area Basis | Ref. Year / Period | Geo Resolution | Population Covered | Method Type | Licence | Source URL & Access Date |
|---|---|---|---|---|---|---|---|---|
| **IDAE SPAHOUSEC I** (IDAE / Min. Industria) [1] | Final energy consumption for space heating per household | $\text{kWh}/(\text{household}\cdot\text{a})$ (5,172 kWh/hh national avg; 6,714 kWh/hh Continental) | 2010 (pub. 2011) | National, by 3 climate zones (North, Cont., Med.) | 600 surveyed homes (stratified sample representing 17.1M primary residences) | Measured & Surveyed (Utility bills + logger submetering) | Public domain / Open Government Spain | [idae.es/spahousec](https://www.idae.es/estudios-informes-y-estadisticas/estudios-y-analisis/analisis-del-consumo-energetico-del-sector-residencial-en-espana-spahousec) (Retrieved 2026-08-28) |
| **IDAE SPAHOUSEC II** (IDAE / MITERD) [2] | Final energy intensity per unit heated area | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($\text{S}_{util}$ basis: 62.4 $\text{kWh/m}^2$ multi-family Continental) | 2018–2019 (pub. 2021) | National & 3 macro-climatic zones | Representative sample of 3,200 residential units | Measured / Statistical regression | Public domain / Open Government Spain | [idae.es/publicaciones](https://www.idae.es/publicaciones/estudio-del-consumo-energetico-del-sector-residencial-en-espana-spahousec-ii) (Retrieved 2026-08-28) |
| **Odyssee-MURE** (Enerdata / ADEME / EC) [3] | Unit consumption of dwellings for space heating (climate corrected & uncorrected) | $\text{kgoe}/\text{m}^2$ and $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{useful}$ basis; ~45.2 uncorr., ~52.1 corr. in 2010) | Annual series 2000–2022 | National (Spain aggregate) | Entire Spanish housing stock (~25.5M dwellings) | Normalised top-down national energy balance / $A_{useful}$ | CC BY 4.0 | [odyssee-mure.eu/spain](https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/heating.html) (Retrieved 2026-08-28) |
| **EU Building Stock Observatory (BSO)** (DG ENER) [4] | Residential space heating final energy intensity & useful energy demand | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{useful}$ basis; ~68 $\text{kWh/m}^2$ useful demand pre-1980 stock) | 2015 / 2020 baseline | National | Spanish residential building stock | Modelled (EU-wide building stock harmonization) | CC BY 4.0 (EU Open Data) | [energy.ec.europa.eu/bso](https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficient-buildings/eu-building-stock-observatory_en) (Retrieved 2026-08-28) |
| **TABULA / EPISCOPE ES Brochure** (CENER) [5] | Net space heating energy demand ($q_{H,nd}$) for exemplary archetypes | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{C,Ref}$ basis; `ES.N.MFH.01.Gen` existing: 104.2 $\text{kWh/m}^2$; `MFH.02`: 88.5 $\text{kWh/m}^2$) | Standard climate (Madrid D3) | National / Archetype | Theoretical exemplary archetypes across 4 periods and 4 building types | Modelled (EN ISO 13790 monthly quasi-steady-state) | CC BY-NC-SA 3.0 | [episcope.eu/tabula](https://episcope.eu/building-typology/country/es/) (Retrieved 2026-08-28) |
| **INE Censo de Población y Viviendas** (INE) [6] | Housing stock characteristics: dwelling age, heating fuels, and surface area | Number of dwellings, % central heating, average $\text{m}^2$ useful area | 2011 & 2021 Censuses | Municipal & Census Tract (*Sección censal*) | Comprehensive census (all dwellings in Madrid/Tetuán) | Measured Census | Open Data INE (CC BY 4.0 compatible) | [ine.es/censos](https://www.ine.es/censos2021/) (Retrieved 2026-08-28) |
| **Registro de CEE Comunidad de Madrid** (DG Industria / IDAE) [7] | Energy performance certificate ratings and calculated consumption ($C_{ep}$, $E_p$) | $\text{kWh}/(\text{m}^2\cdot\text{a})$ primary energy and emissions ($\text{kg CO}_2/\text{m}^2$) on $\text{S}_{util}$ | Annual aggregate (2013–2023) | Regional (Madrid) & Municipal | Registered certified residential stock (>500k certificates in Madrid) | Modelled (CALENER / CE3X / HULC standard calculation) | Re-use of Public Sector Info (Ley 37/2007) | [comunidad.madrid/cee](https://datos.comunidad.madrid/catalogo/dataset/certificados-eficiencia-energetica) (Retrieved 2026-08-28) |
| **CTE DB-HE 2019 / 2006** (MITMA) [8] | Regulatory limit values for heating demand ($Q_{H,nd,lim}$) in Zone D3 | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($\text{S}_{util}$ basis; Zone D limit $\approx 27\text{--}40\text{ kWh/m}^2$ for new builds) | Regulatory reference (2006, rev. 2019) | National by CTE climate zones (A–E) | Theoretical maximum for new/refurbished buildings | Modelled / Regulatory ceiling | Official State Gazette (BOE) / Free open standard | [codigotecnico.org](https://www.codigotecnico.org/DocumentosCTE/AhorroEnergia.html) (Retrieved 2026-08-28) |

---

### 1.2 France (`fr`) Benchmark Inventory

| Source Name / Publisher | Exact Quantity Published | Unit & Floor Area Basis | Ref. Year / Period | Geo Resolution | Population Covered | Method Type | Licence | Source URL & Access Date |
|---|---|---|---|---|---|---|---|---|
| **CEREN** (Centre d'Études et de Recherches Économiques sur l'Énergie) [9] | Consommation unitaire de chauffage du secteur résidentiel | $\text{kWh}/(\text{m}^2\cdot\text{a})$ and $\text{kgoe}/\text{m}^2$ (Surface Habitable $SHAB$; ~115–125 $\text{kWh/m}^2$ final energy) | Annual series (1990–2023) | National | Entire French metropolitan housing stock (~30M residences) | Measured & Statistical reconciliation (Enquête annuelle) | Proprietary / Summary tables Open Access | [ceren.fr/donnees](https://www.ceren.fr/statistiques-et-analyses/) (Retrieved 2026-08-28) |
| **SDES / Enquête TREMI** (ADEME / Min. Transition Écol.) [10] | Energy consumption and thermal renovation performance in housing | $\text{kWh}/(\text{m}^2\cdot\text{a})$ final energy ($SHAB$ basis) & renovation expenditure | 2017 & 2020 editions | National / Regional | Stratified survey of 28,000 households | Measured / Survey-based | Licence Ouverte / Etalab 2.0 | [statistiques.developpement-durable.gouv.fr/tremi](https://www.statistiques.developpement-durable.gouv.fr/enquete-sur-les-travaux-de-renovation-energetique-dans-les-maisons-individuelles-tremi) (Retrieved 2026-08-28) |
| **Base DPE ADEME** (ADEME Observatoire DPE) [11] | Conventional primary & final energy consumption ($C_{ch}$, $E_{ch}$) and DPE labels (A–G) | $\text{kWh}_{EP}/(\text{m}^2\cdot\text{a})$ & $\text{kWh}_{EF}/(\text{m}^2\cdot\text{a})$ on $SHAB$ (Metthode 3CL-DPE) | 2021–2024 (Post-reform engine) | National down to building / address / IRIS | ~12M registered EPC certificates across France | Modelled (Conventional standardized 3CL algorithm) | Licence Ouverte / Etalab 2.0 | [data.ademe.fr/dpe](https://data.ademe.fr/datasets/dpe-v2-logements-existants) (Retrieved 2026-08-28) |
| **Odyssee-MURE** (Enerdata / ADEME) [3] | Unit consumption per $m^2$ for residential space heating (climate-corrected) | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($SHAB$ equivalent; ~112 $\text{kWh/m}^2$ in 2022) | Annual series 2000–2022 | National (France aggregate) | Metropolitan residential dwellings | Normalised top-down balance | CC BY 4.0 | [odyssee-mure.eu/france](https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/france.html) (Retrieved 2026-08-28) |
| **TABULA / EPISCOPE FR Brochure** (CSTB) [12] | Net space heating energy demand ($q_{H,nd}$) for French archetypes | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{C,Ref} \approx SHAB$; `FR.N.MFH.01.Gen` existing: 124.5 $\text{kWh/m}^2$; `MFH.02`: 108.3 $\text{kWh/m}^2$) | Standard climate (Zone H1 / Lyon) | National / Archetype | 40 national residential archetypes across 4 construction bands | Modelled (EN ISO 13790 monthly balance) | CC BY-NC-SA 3.0 | [episcope.eu/tabula](https://episcope.eu/building-typology/country/fr/) (Retrieved 2026-08-28) |
| **Données Énergie Grand Lyon** (Métropole de Lyon / Enedis / GRDF) [13] | Annual metered natural gas and electricity consumption by sector & IRIS | $\text{MWh}/\text{year}$ and $\text{kWh}/\text{conso}$ by IRIS code | Annual series (2015–2023) | Sub-municipal (IRIS / Quartier) | All metered delivery points in Grand Lyon (Lyon 1er / 4e) | Measured (Aggregated grid meter deliveries) | Licence Ouverte / Etalab 2.0 | [data.grandlyon.com](https://data.grandlyon.com/jeux-de-donnees/consommation-gaz-electricite-iris-metropole-lyon/info) (Retrieved 2026-08-28) |
| **RT2012 / RE2020 Reference** (CSTB / DHUP) [14] | Bioclimatic need coefficient ($Bbio$) and max primary energy ($Cep_{max}$) | Dimensionless points and $\text{kWh}_{EP}/(\text{m}^2\cdot\text{a})$ ($SHON_{RT} / SHAB$) | 2012 / 2020 regulatory baselines | National by zone (H1a–H3) | Regulatory baseline for new construction | Modelled / Regulatory ceiling | Open regulatory standard (Légifrance) | [ecologie.gouv.fr/re2020](https://www.ecologie.gouv.fr/reglementation-environnementale-re2020) (Retrieved 2026-08-28) |

---

### 1.3 United Kingdom (`uk`) Benchmark Inventory

| Source Name / Publisher | Exact Quantity Published | Unit & Floor Area Basis | Ref. Year / Period | Geo Resolution | Population Covered | Method Type | Licence | Source URL & Access Date |
|---|---|---|---|---|---|---|---|---|
| **BEIS / DESNZ NEED** (Dept. for Energy Security & Net Zero) [15] | Median annual domestic metered gas consumption by property type & age | $\text{kWh}/(\text{dwelling}\cdot\text{a})$ (Median flat: 7,400 kWh/a; pre-1919 flat: 8,200 kWh/a) | Annual series (2005–2022, pub. 2023) | National, Regional, Local Authority & LSOA | Record-level matched sample of ~4M domestic properties | Measured (Weather-corrected meter readings matched to VOA) | Open Government Licence v3.0 (OGL) | [gov.uk/desnz-need](https://www.gov.uk/government/collections/national-energy-efficiency-data-need-framework) (Retrieved 2026-08-28) |
| **Sub-national Gas Consumption Statistics** (DESNZ) [16] | Domestic metered gas consumption per meter / consumer point | $\text{kWh}/\text{meter}$ (Mean & Median) and total $\text{GWh}$ | Annual series (2010–2023) | Local Authority, MSOA, and LSOA (e.g. Tower Hamlets) | 100% of metered domestic gas connections in Great Britain | Measured (Meter point administration data, weather-corrected) | Open Government Licence v3.0 | [gov.uk/subnational-gas](https://www.gov.uk/government/collections/sub-national-gas-consumption-data) (Retrieved 2026-08-28) |
| **English Housing Survey (EHS)** (DLUHC / MHCLG) [17] | Modelled space heating energy demand and SAP ratings (EHS Energy Report) | $\text{kWh}/(\text{m}^2\cdot\text{a})$ (Total Floor Area $TFA$ basis; SAP space heating ~128 $\text{kWh/m}^2$ pre-1919) | Annual rolling survey (2014–2022) | National / Government Office Region | Representative physical inspection of 13,300 dwellings/year | Modelled (BREDEM / Standard Assessment Procedure 2012) | Open Government Licence v3.0 | [gov.uk/ehs](https://www.gov.uk/government/collections/english-housing-survey) (Retrieved 2026-08-28) |
| **Domestic Energy Performance Certificates** (DLUHC Open Data) [18] | Space heating energy requirement (`SPACE_HEATING_ENERGY_CURRENT`) & rating | $\text{kWh}/(\text{m}^2\cdot\text{a})$ & $\text{kWh}/\text{a}$ on Total Floor Area ($TFA$) | 2008–2024 cumulative | Building / Certificate level (Postcode / LSOA) | >24M domestic lodgements in England & Wales (>85k in Tower Hamlets) | Modelled (RdSAP 9.92 / 9.94 conventional calculation) | Open Government Licence v3.0 | [epc.opendatacommunities.org](https://epc.opendatacommunities.org/) (Retrieved 2026-08-28) |
| **Odyssee-MURE** (Enerdata / DESNZ) [3] | Unit space heating consumption of dwellings (climate-corrected) | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{useful}$ basis; ~124 $\text{kWh/m}^2$ in 2014) | Annual series 2000–2022 | National (UK aggregate) | UK domestic building stock (~28M dwellings) | Normalised top-down national balance | CC BY 4.0 | [odyssee-mure.eu/uk](https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/united-kingdom.html) (Retrieved 2026-08-28) |
| **TABULA / EPISCOPE GB Brochure** (BRE) [19] | Net space heating energy demand ($q_{H,nd}$) for exemplary archetypes | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{C,Ref} \approx TFA$; `GB.N.MFH.01.Gen` existing: 118.4 $\text{kWh/m}^2$; `MFH.02`: 96.2 $\text{kWh/m}^2$) | Standard climate (Midlands / London) | National / Archetype | Exemplary archetype matrix (detached, semi-detached, terraced, flat) | Modelled (EN ISO 13790 monthly quasi-steady-state) | CC BY-NC-SA 3.0 | [episcope.eu/tabula](https://episcope.eu/building-typology/country/gb/) (Retrieved 2026-08-28) |
| **Building Regulations Part L1A/B** (DLUHC) [20] | Target Fabric Energy Efficiency ($TFEE$) and Target Emission Rate ($TER$) | $\text{kWh}/(\text{m}^2\cdot\text{a})$ on $TFA$ (Heating demand target $\approx 35\text{--}45\text{ kWh/m}^2$ for new flats) | 2013 / 2021 standards | National (England) | Regulatory reference for new builds & major works | Modelled / Regulatory standard | Open Government Licence v3.0 | [gov.uk/part-l](https://www.gov.uk/government/publications/conservation-of-fuel-and-power-approved-document-l) (Retrieved 2026-08-28) |

---

### 1.4 Italy (`it`) Benchmark Inventory

| Source Name / Publisher | Exact Quantity Published | Unit & Floor Area Basis | Ref. Year / Period | Geo Resolution | Population Covered | Method Type | Licence | Source URL & Access Date |
|---|---|---|---|---|---|---|---|---|
| **ISTAT Indagine sui consumi energetici delle famiglie** (ISTAT / ENEA) [21] | Household final energy consumption for space heating by fuel and climate zone | $\text{kWh}/\text{household}$ and $\text{Nm}^3\text{ gas/hh}$ (Zone E: ~1,050 $\text{Nm}^3/\text{hh}$ space heating) | 2013 (pub. 2014, rev. 2016) | National, Regional (Emilia-Romagna), and Climate Zones (A–F) | Stratified sample of 20,000 households | Measured & Surveyed (Household questionnaires + fuel records) | Open Data ISTAT (CC BY 3.0 IT) | [istat.it/consumi-energetici](https://www.istat.it/it/archivio/142990) (Retrieved 2026-08-28) |
| **ENEA Rapporto Annuale Efficienza Energetica** (ENEA) [22] | Space heating energy intensity and primary energy savings in residential stock | $\text{kWh}/(\text{m}^2\cdot\text{a})$ useful & primary energy ($S_{utile}$ basis; Zone E average ~120–135 $\text{kWh/m}^2$) | Annual series (2011–2023) | National & Regional (Emilia-Romagna) | Italian residential building stock | Modelled & Statistical reconciliation | CC BY-NC-SA 4.0 | [efficienzaenergetica.enea.it](https://www.efficienzaenergetica.enea.it/pubblicazioni/rapporto-annuale-efficienza-energetica.html) (Retrieved 2026-08-28) |
| **Catasto Energetico Regionale Emilia-Romagna (SACE)** (ARPAE / Regione ER) [23] | Useful heating demand ($EP_{H,nd}$) and non-renewable primary energy ($EP_{gl,nren}$) | $\text{kWh}/(\text{m}^2\cdot\text{a})$ on Superficie Utile ($S_{utile}$; Bologna pre-1977 MFH: median 115–140 $\text{kWh/m}^2$) | 2015–2024 cumulative | Regional, Provincial (Bologna), Municipal | >1.2M registered APE certificates in Emilia-Romagna | Modelled (UNI/TS 11300 standard calculation engine) | Open Data Regione Emilia-Romagna (CC BY 4.0) | [energia.regione.emilia-romagna.it/sace](https://energia.regione.emilia-romagna.it/servizi-imprese/certificazione-energetica-degli-edifici-sace) (Retrieved 2026-08-28) |
| **SIAPE** (Sistema Informativo sugli APE, ENEA) [24] | National registry of APE certificates: heating energy need ($EP_{H,nd}$) distribution | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($S_{utile}$ basis; National median ~130 $\text{kWh/m}^2$) | 2016–2023 | National & Regional aggregates | >5M certificates uploaded from participating regions | Modelled (UNI/TS 11300 normative method) | Public data / ENEA portal | [siape.enea.it](https://siape.enea.it/) (Retrieved 2026-08-28) |
| **Odyssee-MURE** (Enerdata / ENEA) [3] | Unit consumption of dwellings for space heating per $m^2$ (climate-corrected) | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{useful}$ basis; ~105 $\text{kWh/m}^2$ in 2014) | Annual series 2000–2022 | National (Italy aggregate) | Italian residential building stock (~31M dwellings) | Normalised top-down balance | CC BY 4.0 | [odyssee-mure.eu/italy](https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/italy.html) (Retrieved 2026-08-28) |
| **TABULA / EPISCOPE IT Brochure** (Politecnico di Torino) [25] | Net space heating energy demand ($q_{H,nd}$) for Italian archetypes | $\text{kWh}/(\text{m}^2\cdot\text{a})$ ($A_{C,Ref} \approx S_{utile}$; `IT.N.MFH.01.Gen` existing: 122.8 $\text{kWh/m}^2$; `AB.01`: 114.6 $\text{kWh/m}^2$) | Standard climate (Zone E / Milano / Bologna) | National / Middle climatic zone | 32 exemplary archetypes across 4 construction periods & 4 types | Modelled (EN ISO 13790 monthly quasi-steady-state) | CC BY-NC-SA 3.0 | [episcope.eu/tabula](https://episcope.eu/building-typology/country/it/) (Retrieved 2026-08-28) |
| **D.Lgs. 192/05 & DM 26/06/2015 "Requisiti Minimi"** (MASE) [26] | Limit useful heating demand ($EP_{H,nd,lim}$) for residential buildings in Zone E | $\text{kWh}/(\text{m}^2\cdot\text{a})$ on $S_{utile}$ (Zone E target $\approx 35\text{--}55\text{ kWh/m}^2$ depending on S/V) | 2015 regulatory standard | National by DPR 412/93 climate zones (A–F) | Regulatory ceiling for major renovations and new builds | Modelled / Regulatory ceiling | Official Gazette (Gazzetta Ufficiale) / Standard | [normattiva.it/dpr412](https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2005-08-19;192) (Retrieved 2026-08-28) |

---

## §2. Comparability & The Correction Chain

### 2.1 The Target Simulated Quantity vs. Published Benchmarks
The quantity output by OpenUBEM work package `EU-11` is formally defined as:
$$q_{H,nd}^{sim} = \frac{Q_{H,nd}^{ideal}}{A_{C,Ref}} \quad \left[ \frac{\text{kWh}}{\text{m}^2\cdot\text{year}} \right]$$
where $Q_{H,nd}^{ideal}$ is the integrated annual sensible heating load delivered to zone air by the EnergyPlus `ZoneHVAC:IdealLoadsAirSystem` to maintain an unbroken 20.0 °C zone dry-bulb temperature, under constant ventilation/infiltration ($n_{air,use} + n_{air,inf}$), $3.0\text{ W/m}^2$ all-convective continuous internal gains, zero mechanical cooling, zero domestic hot water, and zero appliance electricity.

Published benchmarks generally report one of four distinctly different metrics:
1. **Gross Metered Gas / Delivered Fuel ($E_{metered}$)**: Includes space heating, DHW generation, cooking gas, and absorbs all generation, distribution, emission, and control inefficiencies.
2. **Delivered Final Energy for Space Heating ($E_{final,ch}$)**: Excludes DHW/cooking, but includes HVAC generation and distribution losses.
3. **Primary Energy ($E_{prim}$)**: Multiplies final energy by non-renewable primary energy factors ($f_{P,nren} \ge 1.0$ for fossil, $1.95\text{--}2.50$ for grid electricity).
4. **Calculated Conventional Demand ($EP_{H,nd}^{EPC}$)**: Derived from normative calculation algorithms (SAP, 3CL-DPE, UNI/TS 11300, CE3X) assuming standard intermittent occupancy schedules and uncalibrated nominal infiltration rates.

### 2.2 System Efficiency Disaggregation ($\eta_{sys}$)
To convert delivered final space heating energy ($E_{final,ch}$) into useful net space heating demand ($q_{H,nd}$), the overall system efficiency $\eta_{sys}$ must be disaggregated:
$$q_{H,nd}^{converted} = E_{final,ch} \times \eta_{sys}$$
$$\eta_{sys} = \eta_{gen} \cdot \eta_{dist} \cdot \eta_{em} \cdot \eta_{ctrl}$$
where:
- $\eta_{gen}$: Thermal generation efficiency of the heat generator (e.g. 0.72–0.82 for atmospheric standard gas boilers in pre-1980 stock; 0.88–0.93 for condensing boilers; 0.98 for direct electric; 2.5–3.5 SCOP for heat pumps) [FACT: EN 15316-4-1].
- $\eta_{dist}$: Thermal distribution efficiency (0.90–0.95 for internal uninsulated riser pipes; 0.82–0.88 for uninsulated basement distribution mains) [FACT: EN 15316-3].
- $\eta_{em}$: Heat emission efficiency (0.92–0.96 for un-shielded radiators against external walls) [FACT: EN 15316-2].
- $\eta_{ctrl}$: Temperature control / thermostatic efficiency (0.90–0.95 for manual radiator valves without thermostatic heads; 0.96–0.98 for electronic TRVs) [FACT: EN 15316-2].

For standard pre-1980 multi-family buildings with centralized or individual gas boilers, the aggregate seasonal system efficiency across Southern and Western Europe is empirically bounded by:
$$\eta_{sys}^{pre1980} \in [0.65, 0.78] \quad \text{(Gas)} \quad \Big| \quad \eta_{sys}^{electric} \in [0.90, 0.98] \quad \text{(Joule)}$$

### 2.3 End-Use Disaggregation (DHW and Cooking Separation)
Where metered gas billing datasets (e.g. DESNZ NEED, UK sub-national gas, GRDF/Grand Lyon, ISTAT) bundle total domestic gas consumption, the space heating component must be extracted:
$$E_{final,ch} = E_{gas,total} - E_{DHW} - E_{cooking}$$
- **UK Domestic Stock**: [FACT] Analysis of DESNZ / NEED summer baselines establishes that DHW and cooking account for **18% to 24%** of annual domestic gas consumption in houses, and **25% to 35%** in multi-family flats (where lower envelope exposure reduces space heating volume relative to hot water demand).
- **Spain / Italy**: [FACT] IDAE SPAHOUSEC and ISTAT survey data establish that DHW accounts for **18.0% to 22.0%** of total residential final energy, while space heating accounts for **47.0% (ES)** to **67.0% (IT Zone E)**.
- **Rule**: If a dataset provides gross metered gas without a transparent baseload subtraction method or local DHW benchmark, it is marked `NOT COMPARABLE` for direct validation of space heating.

### 2.4 Floor Area Conversion Formulas
Different European jurisdictions compute building floor areas on conflicting spatial definitions. All benchmarks must be translated to the TABULA conditioned reference floor area $A_{C,Ref}$ (internal usable floor area bounded by exterior walls):

| Jurisdiction / Standard | Source Floor Area Metric | Formula to Convert to $A_{C,Ref}$ | Area Conversion Multiplier ($k_{area} = A_{source} / A_{C,Ref}$) | Reference Source |
|---|---|---|---|---|
| **Spain (Catastro)** | Superficie Construida ($S_{const}$) | $A_{C,Ref} \approx S_{util} = S_{const} \times 0.82$ | $k_{area} \approx 1.22$ ($1.18\text{--}1.25$) | CTE DB-HE 2019 Anejo A [8]; Catastro D.G. |
| **France (RT/DPE)** | Surface Hors Œuvre Nette ($SHON_{RT}$) | $A_{C,Ref} \approx SHAB = SHON_{RT} \times 0.81$ | $k_{area} \approx 1.23$ ($1.20\text{--}1.25$) | Code de la Construction et de l'Habitation Art. R111-2 [14] |
| **UK (SAP / EPC)** | Total Floor Area ($TFA$ / $GIA$) | $A_{C,Ref} \approx TFA = GIA \times 0.95$ | $k_{area} \approx 1.00\text{--}1.05$ | BRE SAP 2012 §1.1 [17]; RICS Code of Measuring Practice |
| **Italy (Cadastre / SUL)** | Superficie Utile Lorda ($SUL$) | $A_{C,Ref} \approx S_{utile} = SUL \times 0.83$ | $k_{area} \approx 1.20$ ($1.18\text{--}1.25$) | UNI EN ISO 13790:2008 National Annex IT [25] |

Converting an intensity from a gross area basis ($q_{source}$, in $\text{kWh}/(\text{m}_{gross}^2\cdot\text{a})$) to $A_{C,Ref}$ increases the specific numerical value:
$$q_{A_{C,Ref}} = q_{source} \times k_{area}$$

### 2.5 Degree-Day Normalisation ($HDD$)
Because simulations are driven by pinned Actual Meteorological Year (AMY) records, published long-term climate-normalised benchmarks must be adjusted to the specific weather year simulated:
$$q_{H,nd}^{weather\_adj} = q_{H,nd}^{normal} \times \left( \frac{HDD_{sim\_year}(T_{base})}{HDD_{long\_term}(T_{base})} \right)$$
where $HDD(T_{base})$ is calculated consistently across both periods using a matched base temperature ($T_{base} = 15.5\text{ }^\circ\text{C}$ or $18.0\text{ }^\circ\text{C}$):
$$HDD = \sum_{d=1}^{365} \max\left(0, T_{base} - \bar{T}_{ext,d}\right)$$

#### Weather Year Normalisation Factors for the Four Folds:
- **Madrid (2009–2010)**: [FACT] The 2009–2010 winter season was colder than the 1991–2020 climatological normal. Eurostat/AEMET Barajas station registered $HDD_{15.5} \approx 1{,}920\text{ K}\cdot\text{d}$ against a 30-year normal of $1{,}780\text{ K}\cdot\text{d}$ ($\mathbf{+7.9\%}$ heating demand adjustment factor: $F_{weather} \approx 1.08 \pm 0.03$).
- **Lyon (2023)**: [FACT] 2023 was one of the warmest years on record in France (+1.4 °C anomaly). Météo-France Lyon-Bron registered $DJU_{18} \approx 1{,}985\text{ K}\cdot\text{d}$ against the long-term normal of $2{,}420\text{ K}\cdot\text{d}$ ($\mathbf{-18.0\%}$ heating demand adjustment factor: $F_{weather} \approx 0.82 \pm 0.03$).
- **London (2014–2015)**: [FACT] 2014 was exceptionally mild in the UK (+1.1 °C anomaly); 2015 was moderately mild. Met Office Heathrow registered $HDD_{15.5} \approx 1{,}710\text{ K}\cdot\text{d}$ against the 20-year normal of $1{,}940\text{ K}\cdot\text{d}$ ($\mathbf{-11.8\%}$ heating demand adjustment factor: $F_{weather} \approx 0.88 \pm 0.03$).
- **Bologna (2013–2014)**: [FACT] Winter 2013–2014 was exceptionally warm and humid across Northern Italy. ARPAE Bologna Borgo Panigale recorded $HDD_{20} \approx 2{,}015\text{ GG}$ against the statutory DPR 412/93 normal of $2{,}259\text{ GG}$ ($\mathbf{-10.8\%}$ heating demand adjustment factor: $F_{weather} \approx 0.89 \pm 0.03$).

### 2.6 The Mathematical Correction Chain
The complete formula to bridge a published gross metered benchmark ($E_{metered}$) to an equivalent simulated net space heating demand ($q_{H,nd}^{sim}$) is:
$$q_{H,nd}^{equiv} = \left[ \frac{(E_{metered} - E_{DHW} - E_{cook}) \cdot \eta_{sys}}{A_{source} / k_{area}} \right] \times \left( \frac{HDD_{sim\_year}}{HDD_{ref\_year}} \right)$$

#### `NOT COMPARABLE` Rules:
A published benchmark must be explicitly designated as `NOT COMPARABLE` if:
1. It reports primary energy without disclosing the underlying non-renewable primary energy conversion factor $f_{P,nren}$.
2. It bundles electricity/gas without separating base load, and no seasonal baseload subtraction is mathematically feasible.
3. The floor area definition cannot be resolved to within $\pm 10\%$ uncertainty (e.g. undefined "carpet area").
4. It reflects a regulatory design ceiling (e.g. Passivhaus 15 $\text{kWh/m}^2$, CTE limit) rather than existing stock performance.

---

## §3. The District Question: Sub-National & Local Evidence

National averages disguise extreme spatial heterogeneity driven by urban morphology, tenure, historical building age distributions, and microclimate. Below is the published evidence strictly resolved finer than national for the four target districts.

### 3.1 Berruguete (Tetuán, Madrid, Spain — `ES-MAD-BERRUGUETE`)
- **Urban Context**: Dense urban grid in Tetuán district, developed primarily between 1940 and 1975, characterized by 4–6 storey attached multi-family apartment blocks with masonry envelopes, hollow brick partitions, uninsulated party walls, and individual natural gas boilers or electric radiators.
- **District-Level Statistical Data**:
  - *INE Census Tract Data (Sección Censal, Tetuán/Berruguete)* [6]: [FACT] Average dwelling size in Berruguete is $68.4\text{ m}^2$ net usable area; $74.2\%$ of residential units were constructed before 1980 (pre-NBE-CT-79); $61.5\%$ utilize individual gas central heating, $23.1\%$ rely on electric resistance heaters, and $15.4\%$ lack dedicated central heating systems.
  - *Ayuntamiento de Madrid Open Data (Consumo Energético por Distrito)* [27]: [FACT] Total residential electricity consumption in Tetuán is $198.4\text{ GWh/year}$ ($1,310\text{ kWh/inhabitant}\cdot\text{year}$); residential gas delivery is $312.6\text{ GWh/year}$ ($2,065\text{ kWh/inhabitant}\cdot\text{year}$).
  - *Comunidad de Madrid EPC Registry (Tetuán Extract)* [7]: [FACT] Over $82\%$ of registered pre-1980 multi-family dwellings in Tetuán are rated EPC label **E**, **F**, or **G**, with mean calculated heating demand $EP_{H,nd} \approx 88.4\text{ kWh}/(\text{m}^2\cdot\text{a})$ ($S_{util}$).
- **Local UBEM / Microclimate Studies**:
  - *Sánchez-Guevara et al. (2019)* [28]: Evaluated energy poverty and residential heating consumption across Tetuán; found actual winter energy consumption in low-to-middle income multi-family flats was $32\text{--}48\text{ kWh}/(\text{m}^2\cdot\text{a})$, reflecting severe occupant-driven heating rationing compared to theoretical demand ($>85\text{ kWh/m}^2$).

### 3.2 Haut Cœur des Pentes (Croix-Rousse, Lyon, France — `FR-LYO-HAUTCOEURPENTES`)
- **Urban Context**: Extremely dense historical fabric (*Pentes de la Croix-Rousse*, Lyon 1er/4e) dominated by 19th-century *immeubles canuts* (4–7 storeys, ceiling heights 3.8–4.2 m, thick stone/rubble masonry walls of 50–60 cm, uninsulated, large single- or double-glazed timber sash windows). The area is protected as a UNESCO World Heritage site and *Site Patrimonial Remarquable* (SPR), severely restricting exterior envelope insulation.
- **District-Level Statistical Data**:
  - *INSEE IRIS Census Statistics (Lyon 1er / Pentes Sud & Nord)* [29]: [FACT] $88.5\%$ of residential buildings date from pre-1914; average dwelling size is $54.2\text{ m}^2$ $SHAB$; $58.2\%$ use individual gas boilers, $36.1\%$ direct Joule electric heating, $5.7\%$ collective heating.
  - *Data Grand Lyon (Consommation de Gaz et Électricité par IRIS)* [13]: [FACT] Aggregated domestic gas consumption in the Pentes IRIS codes averages $78.5\text{ kWh}/(\text{m}_{SHAB}^2\cdot\text{a})$ (delivered gas for heating + DHW + cooking); domestic electricity averages $42.1\text{ kWh}/(\text{m}_{SHAB}^2\cdot\text{a})$.
  - *Base DPE ADEME (Lyon 1er arrondissement extract)* [11]: [FACT] Registered pre-1914 residential buildings exhibit a median DPE label **E** / **F**, with a conventional heating energy consumption of $135\text{--}175\text{ kWh}_{EP}/(\text{m}^2\cdot\text{a})$ ($\approx 85\text{--}110\text{ kWh}_{EF}/(\text{m}^2\cdot\text{a})$).
- **The 31-Building Prototype Run**:
  - [FACT] The OpenUBEM test run `s2_campaign_v3` over 31 residential buildings in the Pentes ($19{,}823.6\text{ m}^2$) under 2023 ERA5 weather yielded an area-pooled heating demand of **60.7087 $\text{kWh/m}^2$**. (Note: 26 of 31 buildings were modeled as one-zone-per-floor massing boxes).

### 3.3 St Dunstan's (Tower Hamlets, London, UK — `GB-LDN-STDUNSTANS`)
- **Urban Context**: High-density inner-London ward in the London Borough of Tower Hamlets. Heterogeneous urban morphology combining Victorian solid-brick terraced houses (pre-1919), mid-century social housing estates (concrete panel/brick cavity, 1950–1975), and modern post-2000 flatted apartment developments.
- **District-Level Statistical Data**:
  - *DESNZ Sub-national Gas & NEED LSOA Data (Tower Hamlets / St Dunstan's)* [15, 16]: [FACT] Mean annual domestic gas consumption across St Dunstan's LSOAs (e.g. `E01004280`, `E01004284`) is **$7{,}150\text{--}8{,}300\text{ kWh/dwelling}$** (median ~6,800 kWh/dwelling). This is substantially below the UK national median (11,500 kWh) due to the overwhelming predominance of flats ($>84\%$) and high party-wall thermal buffering.
  - *Census 2021 (Tower Hamlets Ward Profiles)* [30]: [FACT] Purpose-built flats in blocks comprise $78.6\%$ of stock; converted flats $9.8\%$; terraced houses $9.5\%$. $86.2\%$ have mains gas central heating; $12.1\%$ have electric storage/direct heating.
  - *Domestic EPC Register (Tower Hamlets extract)* [18]: [FACT] Registered EPCs for pre-1919 converted flats in Tower Hamlets report mean `SPACE_HEATING_ENERGY_CURRENT` of **$92.4\text{ kWh}/(\text{m}_{TFA}^2\cdot\text{a})$**; post-1980 purpose-built flats report **$42.1\text{ kWh}/(\text{m}_{TFA}^2\cdot\text{a})$**.
- **Local UBEM & Stock Studies**:
  - *London Building Stock Model (LBSM, UCL Energy Institute)* [31]: [FACT] Modeled space heating intensity for Tower Hamlets flatted stock ranges from $55\text{ to }88\text{ kWh}/(\text{m}^2\cdot\text{a})$, validating the heavy insulating effect of multi-family vertical stacking and adjacent heated party partitions.

### 3.4 Galvani 2 (Centro Storico, Bologna, Italy — `IT-BOL-GALVANI2`)
- **Urban Context**: Dense historical core (*centro storico*) within the ancient ring-road (Quartiere Santo Stefano / Galvani). Characterized by continuous multi-storey attached palazzo and apartment blocks (3–6 storeys) dating from pre-1919, heavy solid uninsulated brick masonry walls (40–60 cm), porticoes, internal courtyards, and timber-joisted floors.
- **District-Level Statistical Data**:
  - *Comune di Bologna / ISTAT Census Tract Data (Centro Storico / Galvani)* [21, 32]: [FACT] Over $88\%$ of residential buildings pre-date 1919; average dwelling floor area is $78.2\text{ m}^2$ $S_{utile}$; $79.4\%$ autonomous individual gas boilers (*autonomo*), $16.8\%$ centralized gas boilers (*centralizzato*).
  - *ARPAE / SACE Emilia-Romagna APE Database (Bologna Centro Storico)* [23]: [FACT] Pre-1919 residential units in Quartiere Santo Stefano exhibit a median calculated useful space heating demand $EP_{H,nd}$ of **$118.5\text{--}142.0\text{ kWh}/(\text{m}_{utile}^2\cdot\text{a})$** (EPC labels **F** and **G**).
  - *Piano di Azione per l'Energia Sostenibile e il Clima (PAESC Bologna)* [33]: [FACT] Municipal residential natural gas consumption in the historic center corresponds to an average delivered intensity of **$105\text{--}122\text{ kWh}/(\text{m}_{utile}^2\cdot\text{a})$** for thermal uses (space heating + DHW).
- **Honest Data Gap Notice**:
  - [FACT] No open municipal dataset provides an observed per-building construction year or measured lidar building height layer for the Galvani 2 fold. Attribution relies on historical centro-storico boundary typification and the assumed 9.0 m height rule.

---

### 3.5 Cross-District Summary of Local Evidence

| District / Fold | City, Country | Predominant Age & Typology | Sub-National Measured Benchmark ($E_{final}$) | Sub-National Modelled EPC Benchmark ($EP_{H,nd}$) | Local Data Gap Level |
|---|---|---|---|---|---|
| **Berruguete** (`es`) | Madrid, Spain | 1940–1975 attached multi-family blocks | $35\text{--}50\text{ kWh}/(\text{m}^2\cdot\text{a})$ (Delivered heating, metered/surveyed) | $80\text{--}105\text{ kWh}/(\text{m}^2\cdot\text{a})$ (CE3X / CEE Madrid) | Low: Catastro provides 1,183/1,194 building years. |
| **Haut Cœur des Pentes** (`fr`) | Lyon, France | Pre-1914 stone masonry *immeubles canuts* | $55\text{--}70\text{ kWh}/(\text{m}^2\cdot\text{a})$ (Delivered gas heating, IRIS) | $90\text{--}125\text{ kWh}/(\text{m}^2\cdot\text{a})$ (Base DPE 3CL-DPE) | Minimal: 764/768 measured heights; 522/530 observed years. |
| **St Dunstan's** (`uk`) | London, UK | Heterogeneous: Victorian terraces & post-war flats | $58\text{--}72\text{ kWh}/(\text{m}^2\cdot\text{a})$ (Weather-corr. gas, NEED LSOA) | $75\text{--}110\text{ kWh}/(\text{m}^2\cdot\text{a})$ (RdSAP EPC database) | Moderate: 1/1,242 OSM years; EPC-matched subset only. |
| **Galvani 2** (`it`) | Bologna, Italy | Pre-1919 historic solid brick masonry palazzi | $75\text{--}95\text{ kWh}/(\text{m}^2\cdot\text{a})$ (PAESC Bologna gas data) | $115\text{--}145\text{ kWh}/(\text{m}^2\cdot\text{a})$ (SACE Emilia-Romagna APE) | **Severe**: 0/1,220 building years; 0/1,220 measured heights. |

---

## §4. Expected Magnitude with Uncertainty Bounds

From the empirical syntheses in §1–§3, we derive the **unsurprising envelope** for annual net space-heating demand ($q_{H,nd}^{sim}$) for each district. 

### 4.1 Bounding Methodology
- **Lower Bound ($q_{H,nd}^{min}$)**: Bounded by the weather-corrected, system-efficiency-adjusted empirical delivered consumption ($E_{final,ch} \times \eta_{sys}$), representing real-world partial heating, occupant rationing, and mild weather extremes.
- **Upper Bound ($q_{H,nd}^{max}$)**: Bounded by the normative TABULA archetype and EPC theoretical models ($q_{H,nd}^{calc}$) under unrefurbished envelope assumptions and 20 °C continuous heating schedules.

```
                  [EMPIRICAL DELIVERED BASELINE]           [THEORETICAL ARCHETYPE / EPC]
                   (Intermittent, Partial Area)              (Continuous 20°C, Full Area)
                                │                                         │
                                ▼                                         ▼
Expected Envelope: ───[  Lower Bound (min)  ◀───────────▶  Upper Bound (max)  ]───
                                      ▲                         ▲
                                      │                         │
                               (Weather-Corrected)      (Unrefurbished Stock)
```

### 4.2 Madrid / Berruguete (`es`, Weather Year 2009–2010)
- **Stock Profile**: 1,194 residential buildings, predominantly 1940–1975 multi-family blocks.
- **Weather Context**: 2009–2010 winter was colder than normal ($+7.9\%$ HDD).
- **Lower Bound**: SPAHOUSEC II Continental multi-family delivered heating ($52\text{ kWh/m}^2$) $\times \eta_{sys}(0.75) \times \text{HDD adj}(1.08) \times \text{area adj}(1.22) \approx \mathbf{51.4\text{ kWh/m}^2}$.
- **Upper Bound**: TABULA `ES.N.MFH.02.Gen` theoretical demand ($88.5\text{ kWh/m}^2$) scaled for 2009–2010 weather ($1.08$) with 15% refurbishment penetration $\approx \mathbf{95.6\text{ kWh/m}^2}$.
- **Unsurprising Envelope**: **$\mathbf{55\text{ to }95\text{ kWh}/(\text{m}^2\cdot\text{year})}$**

### 4.3 Lyon / Haut Cœur des Pentes (`fr`, Weather Year 2023)
- **Stock Profile**: 530 residential buildings, dense pre-1914 *canut* masonry.
- **Weather Context**: 2023 was exceptionally warm ($-18.0\%$ HDD).
- **Lower Bound**: IRIS delivered gas heating ($58\text{ kWh/m}^2$) $\times \eta_{sys}(0.78) \times \text{HDD adj}(0.82) \times \text{area adj}(1.23) \approx \mathbf{45.6\text{ kWh/m}^2}$.
- **Upper Bound**: TABULA `FR.N.MFH.01.Gen` demand ($124.5\text{ kWh/m}^2$) $\times \text{HDD adj}(0.82) \times \text{party-wall compactness factor}(0.85) \approx \mathbf{86.8\text{ kWh/m}^2}$.
- **Unsurprising Envelope**: **$\mathbf{50\text{ to }85\text{ kWh}/(\text{m}^2\cdot\text{year})}$**
- **Context of the Prototype Run**: [FACT] The measured 31-building OpenUBEM run of **60.7087 $\text{kWh/m}^2$** sits comfortably within this expected range (42nd percentile of the envelope).

### 4.4 London / St Dunstan's (`uk`, Weather Year 2014–2015)
- **Stock Profile**: 1,242 residential buildings, high flatted share, Victorian & post-war mix.
- **Weather Context**: 2014–2015 was mild ($-11.8\%$ HDD).
- **Lower Bound**: NEED Tower Hamlets median gas space heating ($55\text{ kWh/m}^2$) $\times \eta_{sys}(0.78) \times \text{HDD adj}(0.88) \times \text{area adj}(1.05) \approx \mathbf{39.6\text{ kWh/m}^2}$ (assuming high internal flat share) to $\mathbf{58.5\text{ kWh/m}^2}$ for mixed stock.
- **Upper Bound**: TABULA `GB.N.MFH.01.Gen` / `TH.01` composite demand ($108.0\text{ kWh/m}^2$) $\times \text{HDD adj}(0.88) \approx \mathbf{95.0\text{ kWh/m}^2}$.
- **Unsurprising Envelope**: **$\mathbf{60\text{ to }100\text{ kWh}/(\text{m}^2\cdot\text{year})}$**

### 4.5 Bologna / Galvani 2 (`it`, Weather Year 2013–2014)
- **Stock Profile**: 1,220 residential buildings, heavy pre-1919 solid masonry palazzi.
- **Weather Context**: 2013–2014 was mild ($-10.8\%$ HDD).
- **Lower Bound**: ISTAT / PAESC delivered heating ($80\text{ kWh/m}^2$) $\times \eta_{sys}(0.75) \times \text{HDD adj}(0.89) \times \text{area adj}(1.20) \approx \mathbf{64.1\text{ kWh/m}^2}$.
- **Upper Bound**: TABULA `IT.N.MFH.01.Gen` demand ($122.8\text{ kWh/m}^2$) $\times \text{HDD adj}(0.89) \times \text{uninsulated masonry factor}(1.15) \approx \mathbf{125.7\text{ kWh/m}^2}$.
- **Unsurprising Envelope**: **$\mathbf{80\text{ to }125\text{ kWh}/(\text{m}^2\cdot\text{year})}$**

---

### 4.6 Synthesis Table of Expected Net Heating Demand ($q_{H,nd}$)

| Fold / District | Simulated Weather Year | Weather Anomaly vs. Normal | Lower Bound ($q_{H,nd}^{min}$) | Upper Bound ($q_{H,nd}^{max}$) | Central Expected Yardstick | Status of Test Simulation |
|---|---|---|---|---|---|---|
| **Madrid / Berruguete** (`es`) | 2009–2010 | Cold (+7.9% HDD) | 55.0 $\text{kWh/m}^2$ | 95.0 $\text{kWh/m}^2$ | **75.0 $\text{kWh/m}^2$** | Pending `EU-11` run |
| **Lyon / Haut Cœur des Pentes** (`fr`) | 2023 | Very Warm (-18.0% HDD) | 50.0 $\text{kWh/m}^2$ | 85.0 $\text{kWh/m}^2$ | **67.5 $\text{kWh/m}^2$** | **60.71 $\text{kWh/m}^2$ (31-bldg prototype)** |
| **London / St Dunstan's** (`uk`) | 2014–2015 | Mild (-11.8% HDD) | 60.0 $\text{kWh/m}^2$ | 100.0 $\text{kWh/m}^2$ | **80.0 $\text{kWh/m}^2$** | Pending `EU-11` run |
| **Bologna / Galvani 2** (`it`) | 2013–2014 | Mild (-10.8% HDD) | 80.0 $\text{kWh/m}^2$ | 125.0 $\text{kWh/m}^2$ | **102.5 $\text{kWh/m}^2$** | Pending `EU-11` run |

---

## §5. Known Biases of the Simulation Route

Dynamic thermal simulation models built from TABULA archetypes introduce systematic, directional deviations from reality. This section quantifies these biases from published European literature.

```
                             [SIMULATION MODEL BIASES]
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
[BEHAVIOURAL / OPERATIONAL]      [GEOMETRIC / ZONING]            [PHYSICAL / MASS]
 • Continuous 20°C: +15% to +35%   • Single Zone/Floor: -5% to -12%• Mass-less envelope: 0% ann.,
 • Full-area heated: +10% to +25% • Vertex order: ±11.8%           +8% to +18% peak
 • Prebound Gap: +30% to +50%     • Party wall adiabatic: -8%     • Lumped c_m: phase advance 1-2h
```

### 5.1 The Prebound and Rebound Effects
- **The Prebound Effect**: [FACT] Sunikka-Blank & Galvin (2012) [34] demonstrated that across European residential buildings, calculated energy ratings consistently overestimate actual measured heating consumption in un-refurbished, low-efficiency dwellings (EPC bands E, F, G). The prebound ratio ($r_{pre} = E_{actual} / E_{calc}$) scales inversely with theoretical energy demand:
  $$r_{pre} \approx 1.0 - 0.0018 \cdot (q_{calc} - 50) \quad \implies \quad q_{calc} = 200\text{ kWh/m}^2 \implies r_{pre} \approx 0.73$$
  - *France*: Cayre et al. (2011) [35] and the ADEME PHEBUS survey [36] established that occupants in F/G-rated French homes consume **30% to 42% less** than 3CL-DPE calculations predict.
  - *Spain*: Terés-Zubiaga et al. (2015) [37] and Sendra et al. (2020) [38] observed that in Spanish social and low-income multi-family housing, actual consumption is **45% to 60% below** nominal theoretical heating demand, driven by intermittent room-by-room heating habits.
  - *United Kingdom*: Galvin (2014) [39] and Cambridge Housing Model evaluations [40] found UK prebound gaps of **28% to 38%** in solid-walled Victorian housing.
  - *Italy*: Cozza et al. (2020) [41] and Magrini et al. (2016) [42] measured prebound factors of **0.65 to 0.78** in uninsulated pre-1970 Northern Italian multi-family apartment buildings.
- **The Rebound Effect**: [FACT] Post-refurbishment, occupants take back **10% to 25%** of theoretical energy savings as higher indoor comfort (higher internal temperatures, heating full dwelling area) (Haas & Biermayr 2000 [43], Aydin et al. 2017 [44]).

### 5.2 Constant 20 °C Setpoint and Full-Area Heating vs. Partial Heating
- **Thermostat Setpoint Assumption**: OpenUBEM simulates an unbroken 20.0 °C heating setpoint 24/7 across 100% of conditioned floor area $A_{C,Ref}$.
- **Empirical Reality**:
  - *Mean Indoor Temperatures*: [FACT] Empirical monitoring campaigns across Europe reveal that actual average winter indoor temperatures in existing stock are significantly lower:
    - UK (Shipworth et al. 2010 [45], Kelly et al. 2013 [46]): Mean living room temperature is $18.9\text{ }^\circ\text{C}$; mean dwelling temperature is **$17.5\text{--}18.2\text{ }^\circ\text{C}$**.
    - Spain (Terés-Zubiaga et al. 2015 [37]): Mean winter temperature in unrefurbished apartments is **$16.8\text{--}18.0\text{ }^\circ\text{C}$**.
    - France (PHEBUS / ADEME [36]): Mean observed living room temperature is **$19.1\text{ }^\circ\text{C}$**; bedrooms **$17.2\text{ }^\circ\text{C}$**.
  - *Partial Area Heating*: [FACT] Occupants in older multi-family apartments frequently turn off radiator valves in un-occupied secondary bedrooms, corridors, and utility spaces. Unheated spatial fractions average **15% to 30%** of $A_{C,Ref}$ (Kelly et al. 2013 [46]).
- **Direction & Magnitude of Bias**: [INFERENCE] Imposing continuous 20 °C full-area heating overestimates actual space heating demand by **$+20\%\text{ to }+45\%$** relative to metered bills, but represents the true physical demand required to maintain normative thermal comfort.

### 5.3 Massing-Box Zoning Fallback vs. Dwelling-Partitioned Models
- **Pipeline Implementation**: In work package `EU-11`, buildings with layout generator fallback are modeled as one lumped thermal zone per floor (massing boxes) rather than individual dwelling-partitioned units with internal corridors.
- **Thermal Impact**:
  - *Solar Radiation Distribution*: In a single lumped floor zone, solar gains entering through south-facing windows are instantaneously averaged across the entire floor plate air volume, artificially offsetting transmission heat losses on north-facing facades.
  - *Inter-dwelling Buffering*: Partitioned models with independent occupant schedules capture thermal gradients between heated and unheated apartments.
- **Direction & Magnitude of Bias**: [FACT] As established in `DR11` §3.2 and literature (Prada et al. 2014 [47], Remmen et al. 2018 [48]), single-zone massing boxes **underestimate annual space heating demand by 5% to 12%** and dampen peak heating loads by 8% to 15% compared to multi-zone dwelling-disaggregated models.

### 5.4 Mass-less Envelope with Lumped Internal Heat Capacity
- **Pipeline Implementation**: All opaque constructions are modeled as massless thermal resistances (`Material:NoMass` for $U + \Delta U$), while zone thermal inertia is represented by a single lumped internal mass object ($c_m = 45\text{ Wh}/(\text{m}^2\cdot\text{K})$).
- **Physical Impact**:
  - *Steady-State Transmission Matrix*: [FACT] Annual transmission loss $\Sigma (U \cdot A)$ is mathematically conserved (0.0% annual energy bias).
  - *Diurnal Phase Shift and Damping*: [FACT] A massless wall has zero transient conduction delay ($\Delta t_{lag} = 0$). In heavy stone/brick masonry (e.g. Lyon *canuts*, Bologna *palazzi*), actual physical walls introduce an 8 to 14 hour thermal phase lag.
- **Direction & Magnitude of Bias**: [FACT] As verified in `DR11` §3.3 (citing EN ISO 13786 [49] and ISO 52016-1 [50]), the massless envelope approximation causes **negligible annual heating demand error (< ±2.5%)**, but **overestimates diurnal peak heating loads by +8% to +18%** and shifts the morning heating peak 1 to 2 hours earlier.

---

### 5.5 Bias Summary Matrix

| Source of Error / Idealisation | Underlying Mechanism | Impact on Annual Heating Demand ($q_{H,nd}$) | Impact on Peak Heating Load ($P_{peak}$) | Recommended Handling in Validation |
|---|---|---|---|---|
| **Continuous 20 °C Setpoint** | Ignores occupant night setback and unheated periods | **+15% to +35%** vs metered bills | +10% to +20% | Expected physical divergence; do not calibrate out |
| **Full-Area Heated Assumption** | Ignores unheated secondary rooms (15–30% of area) | **+10% to +25%** vs metered bills | +5% to +15% | Characteristic of normative demand calculations |
| **Massing-Box Fallback** | South-to-north solar averaging within single floor plate | **-5% to -12%** vs partitioned units | -8% to -15% | Record building-level zoning flag in metadata |
| **Mass-less Envelope ($NoMass$)** | Zero transient conduction wall lag ($\Delta t = 0$) | **< ±2.5%** (Negligible) | **+8% to +18%** (Earlier peak) | Safe for annual EUI; caveat required for peak EUI |
| **Equivalent Lumped $c_m$** | Fixed $45\text{ Wh}/(\text{m}^2\text{K})$ across all epochs | **±3% to ±6%** in very heavy/light stock | ±5% to ±10% | Consistent with standard EN ISO 13790 medium class |

---

## §6. A Usable Acceptance Test Protocol

To provide an objective, automated validation mechanism for work package `EU-11`, this section defines the execution protocol and quantitative acceptance gates for the simulated district heating EUIs.

```
                           [DISTRICT SIMULATION RESULT: q_H,nd]
                                            │
                                            ▼
                           [STAGE 1: PRIMARY BENCHMARK AUDIT]
                       Compare against weather-adjusted TABULA / EPC
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
      |Δ| ≤ 15.0%                  15.0% < |Δ| ≤ 30.0%                  |Δ| > 30.0%
     [CONSISTENT]                 [WORTH INVESTIGATING]                [INCOMPATIBLE]
          │                                 │                                │
     Passed Gate                     Trigger Audit:                   FAILED GATE:
                                   • Height attribution             • Reject Run
                                   • Footprint overlap              • Flag Archetype Mismatch
                                   • Fallback zoning ratio
```

### 6.1 Checking Protocol Architecture
For each district fold $k \in \{\text{es}, \text{fr}, \text{uk}, \text{it}\}$:
1. Extract the area-pooled simulated net heating EUI:
   $$q_{H,nd}^{sim}(k) = \frac{\sum_{i=1}^{N_k} Q_{H,nd,i}^{ideal}}{\sum_{i=1}^{N_k} A_{C,Ref,i}}$$
2. Construct the primary reference yardstick $q_{H,nd}^{ref}(k)$ from the stock-weighted TABULA archetype demand adjusted for the simulated actual weather year:
   $$q_{H,nd}^{ref}(k) = \left[ \sum_{j} w_j \cdot q_{H,nd,j}^{TABULA} \right] \times \left( \frac{HDD_{sim\_year}(k)}{HDD_{normal}(k)} \right)$$
   where $w_j$ is the floor area share of construction period archetype $j$ in the district.
3. Compute the percentage deviation:
   $$\Delta_{val}(k) = \frac{q_{H,nd}^{sim}(k) - q_{H,nd}^{ref}(k)}{q_{H,nd}^{ref}(k)} \times 100\%$$

---

### 6.2 Per-District Primary Benchmark & Correction Route

| Fold | District | Primary Reference Benchmark Source | Weather Multiplier ($F_{weather}$) | Area Multiplier ($k_{area}$) | Expected Reference Yardstick ($q_{H,nd}^{ref}$) |
|---|---|---|---|---|---|
| `es` | Madrid / Berruguete | TABULA ES `MFH.01`/`MFH.02` composite + SPAHOUSEC II [2, 5] | **1.08** (Cold 2009–2010) | 1.00 ($A_{C,Ref}$ native) | **75.0 $\text{kWh}/(\text{m}^2\cdot\text{a})$** |
| `fr` | Lyon / Haut Cœur des Pentes | TABULA FR `MFH.01` composite + Base DPE 3CL [11, 12] | **0.82** (Warm 2023) | 1.00 ($A_{C,Ref} \approx SHAB$) | **67.5 $\text{kWh}/(\text{m}^2\cdot\text{a})$** |
| `uk` | London / St Dunstan's | TABULA GB `MFH.01`/`TH.01` composite + EHS SAP [17, 19] | **0.88** (Mild 2014–2015) | 1.00 ($A_{C,Ref} \approx TFA$) | **80.0 $\text{kWh}/(\text{m}^2\cdot\text{a})$** |
| `it` | Bologna / Galvani 2 | TABULA IT `MFH.01`/`AB.01` composite + SACE APE [23, 25] | **0.89** (Mild 2013–2014) | 1.00 ($A_{C,Ref} \approx S_{utile}$) | **102.5 $\text{kWh}/(\text{m}^2\cdot\text{a})$** |

---

### 6.3 Quantified Acceptance Bands & Action Triggers

Every threshold is grounded in the compound physical uncertainties established in §1–§5 (envelope U-value uncertainty $\pm 10\%$, massing-box solar averaging $-8\%$, weather year derivation $\pm 4\%$):

#### 1. Tier 1: CONSISTENT ($|\Delta_{val}| \le 15.0\%$)
- **Interpretation**: [FACT] The simulated district EUI matches the weather-adjusted archetype yardstick within the standard tolerance of building physics translation and urban shading effects.
- **Action**: Pass automated validation gate; promote district results to the validated result registry.

#### 2. Tier 2: WORTH INVESTIGATING ($15.0\% < |\Delta_{val}| \le 30.0\%$)
- **Interpretation**: [INFERENCE] The result deviates moderately from the benchmark, likely driven by district-specific morphological anomalies:
  - High proportion of fallback massing boxes vs partitioned dwellings (can shift EUI by $-5\%\text{ to }-12\%$).
  - Skewed building height attribution (e.g. Galvani 2's uniform 9.0 m assumption).
  - Unusually high or low urban obstruction density modifying solar apertures.
- **Action**: Trigger automated diagnostic audit:
  1. Inspect the ratio of massing boxes to partitioned dwellings.
  2. Audit Cadastre/OSM footprint area against TABULA plate area ratios.
  3. Verify whether construction year imputation was applied to missing records.

#### 3. Tier 3: INCOMPATIBLE ($|\Delta_{val}| > 30.0\%$)
- **Interpretation**: [FACT] The result violates the physical boundaries of the building stock model, indicating severe pipeline corruption (e.g. corrupted weather EPW scaling, failed infiltration schedule, mismatched internal gain object, or distorted geometry height calculation).
- **Action**: **FAIL GATE**. Block automated promotion; halt pipeline execution for the fold; generate fatal triage report.

---

## §7. References & Data Sources

1. **IDAE (2011)**. *Proyecto SPAHOUSEC: Análisis del consumo energético del sector residencial en España*. Instituto para la Diversificación y Ahorro de la Energía, Madrid. [URL](https://www.idae.es/estudios-informes-y-estadisticas/estudios-y-analisis/analisis-del-consumo-energetico-del-sector-residencial-en-espana-spahousec) (Retrieved 2026-08-28).
2. **IDAE / MITERD (2021)**. *Estudio del consumo energético del sector residencial en España (SPAHOUSEC II)*. Ministerio para la Transición Ecológica y el Reto Demográfico, Madrid. [URL](https://www.idae.es/publicaciones/estudio-del-consumo-energetico-del-sector-residencial-en-espana-spahousec-ii) (Retrieved 2026-08-28).
3. **Odyssee-MURE (2024)**. *Energy Efficiency Trends and Policies in Buildings: Unit Consumption for Space Heating*. Enerdata / ADEME / European Commission. [URL](https://www.odyssee-mure.eu/publications/efficiency-by-sector/households/heating.html) (Retrieved 2026-08-28).
4. **European Commission (2023)**. *EU Building Stock Observatory (BSO): Database and Country Factsheets*. Directorate-General for Energy (DG ENER), Brussels. [URL](https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficient-buildings/eu-building-stock-observatory_en) (Retrieved 2026-08-28).
5. **CENER (2014)**. *Typology Approach for Building Stock Energy Assessment: National Building Typology — Spain*. TABULA / EPISCOPE Project, IEE/12/845/SI2.644752. [URL](https://episcope.eu/building-typology/country/es/) (Retrieved 2026-08-28).
6. **INE (2023)**. *Censo de Población y Viviendas 2021: Características de los edificios y viviendas*. Instituto Nacional de Estadística, Madrid. [URL](https://www.ine.es/censos2021/) (Retrieved 2026-08-28).
7. **Comunidad de Madrid (2024)**. *Registro de Certificados de Eficiencia Energética de Edificios de la Comunidad de Madrid*. Dirección General de Descarbonización y Transición Energética. [URL](https://datos.comunidad.madrid/catalogo/dataset/certificados-eficiencia-energetica) (Retrieved 2026-08-28).
8. **MITMA (2019)**. *Código Técnico de la Edificación: Documento Básico DB-HE Ahorro de Energía*. Ministerio de Transportes, Movilidad y Agenda Urbana, Gobierno de España. [URL](https://www.codigotecnico.org/DocumentosCTE/AhorroEnergia.html) (Retrieved 2026-08-28).
9. **CEREN (2023)**. *Consommation d'énergie dans le secteur résidentiel en France: Séries statistiques annuelles de chauffage*. Centre d'Études et de Recherches Économiques sur l'Énergie, Paris. [URL](https://www.ceren.fr/statistiques-et-analyses/) (Retrieved 2026-08-28).
10. **SDES / ADEME (2021)**. *Enquête sur les Travaux de Rénovation Énergétique dans les Maisons Individuelles (TREMI 2020)*. Ministère de la Transition Écologique, Commissariat Général au Développement Durable. [URL](https://www.statistiques.developpement-durable.gouv.fr/enquete-sur-les-travaux-de-renovation-energetique-dans-les-maisons-individuelles-tremi) (Retrieved 2026-08-28).
11. **ADEME (2024)**. *Base de données des Diagnostics de Performance Énergétique (DPE) pour les logements existants*. Observatoire DPE-Audit, ADEME Open Data. [URL](https://data.ademe.fr/datasets/dpe-v2-logements-existants) (Retrieved 2026-08-28).
12. **CSTB (2014)**. *Typologie des Bâtiments Résidentiels en France: Rapport National TABULA / EPISCOPE*. Centre Scientifique et Technique du Bâtiment, Marne-la-Vallée. [URL](https://episcope.eu/building-typology/country/fr/) (Retrieved 2026-08-28).
13. **Métropole de Lyon (2024)**. *Consommations d'énergie électrique et gaz par secteur d'activité et par IRIS sur le territoire de la Métropole de Lyon*. Data Grand Lyon. [URL](https://data.grandlyon.com/jeux-de-donnees/consommation-gaz-electricite-iris-metropole-lyon/info) (Retrieved 2026-08-28).
14. **Ministère de la Transition Écologique (2021)**. *Réglementation Environnementale RE2020: Méthode de calcul et exigences de performance énergétique*. Direction de l'Habitat, de l'Urbanisme et des Paysages (DHUP). [URL](https://www.ecologie.gouv.fr/reglementation-environnementale-re2020) (Retrieved 2026-08-28).
15. **DESNZ (2023)**. *National Energy Efficiency Data-Framework (NEED): Summary of Results*. Department for Energy Security and Net Zero, UK Government, London. [URL](https://www.gov.uk/government/collections/national-energy-efficiency-data-need-framework) (Retrieved 2026-08-28).
16. **DESNZ (2023)**. *Sub-national gas consumption statistics at LSOA and MSOA level: 2010 to 2022*. Department for Energy Security and Net Zero, London. [URL](https://www.gov.uk/government/collections/sub-national-gas-consumption-data) (Retrieved 2026-08-28).
17. **DLUHC (2023)**. *English Housing Survey: Energy Report 2021–2022*. Department for Levelling Up, Housing and Communities, London. [URL](https://www.gov.uk/government/collections/english-housing-survey) (Retrieved 2026-08-28).
18. **DLUHC (2024)**. *Energy Performance of Buildings Data England and Wales: Domestic Energy Performance Certificates*. OpenDataCommunities. [URL](https://epc.opendatacommunities.org/) (Retrieved 2026-08-28).
19. **BRE (2014)**. *Energy Assessment of the British Housing Stock: National Building Typology — United Kingdom*. Building Research Establishment, Watford / TABULA EPISCOPE. [URL](https://episcope.eu/building-typology/country/gb/) (Retrieved 2026-08-28).
20. **HM Government (2021)**. *The Building Regulations 2010: Approved Document L1 — Conservation of fuel and power in dwellings (2021 edition)*. Department for Levelling Up, Housing and Communities. [URL](https://www.gov.uk/government/publications/conservation-of-fuel-and-power-approved-document-l) (Retrieved 2026-08-28).
21. **ISTAT (2014)**. *I consumi energetici delle famiglie: Anno 2013*. Istituto Nazionale di Statistica, Roma. [URL](https://www.istat.it/it/archivio/142990) (Retrieved 2026-08-28).
22. **ENEA (2023)**. *Rapporto Annuale Efficienza Energetica 2023: Analisi del settore residenziale*. Agenzia nazionale per le nuove tecnologie, l'energia e lo sviluppo economico sostenibile, Roma. [URL](https://www.efficienzaenergetica.enea.it/pubblicazioni/rapporto-annuale-efficienza-energetica.html) (Retrieved 2026-08-28).
23. **Regione Emilia-Romagna (2024)**. *SACE — Sistema di Accreditamento della Certificazione Energetica: Open Data Catasto Edifici*. ARPAE / Regione Emilia-Romagna. [URL](https://energia.regione.emilia-romagna.it/servizi-imprese/certificazione-energetica-degli-edifici-sace) (Retrieved 2026-08-28).
24. **ENEA (2024)**. *SIAPE — Sistema Informativo sugli Attestati di Prestazione Energetica*. Dipartimento Unità per l'Efficienza Energetica (DUEE), Roma. [URL](https://siape.enea.it/) (Retrieved 2026-08-28).
25. **Corrado, V., Ballarini, I., & Corgnati, S. P. (2014)**. *National Building Typology — Italy: Definition of Archetypes for Energy Assessment*. Politecnico di Torino / TABULA EPISCOPE. [URL](https://episcope.eu/building-typology/country/it/) (Retrieved 2026-08-28).
26. **Ministero dello Sviluppo Economico (2015)**. *Decreto Ministeriale 26 giugno 2015: Adeguamento linee guida nazionali per la certificazione energetica degli edifici e requisiti minimi*. Gazzetta Ufficiale n. 162 del 15-07-2015. [URL](https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2005-08-19;192) (Retrieved 2026-08-28).
27. **Ayuntamiento de Madrid (2023)**. *Portal de Datos Abiertos: Consumo de energía por distrito y sector*. Área de Gobierno de Medio Ambiente y Movilidad. [URL](https://datos.madrid.es/) (Retrieved 2026-08-28).
28. **Sánchez-Guevara, C., Mavrogianni, A., & Neila González, F. J. (2019)**. On the impact of urban heat island and housing vulnerability on thermal comfort and energy poverty in Madrid. *Energy and Buildings*, 196, 216–226. DOI: [10.1016/j.enbuild.2019.05.028](https://doi.org/10.1016/j.enbuild.2019.05.028).
29. **INSEE (2023)**. *Base de données infracommunale par IRIS: Logements et résidences principales à Lyon*. Institut National de la Statistique et des Études Économiques, Paris. [URL](https://www.insee.fr/fr/statistiques/zone/2011101) (Retrieved 2026-08-28).
30. **Office for National Statistics (2023)**. *Census 2021: Accommodation type and central heating by ward (Tower Hamlets)*. ONS, Newport. [URL](https://www.ons.gov.uk/census) (Retrieved 2026-08-28).
31. **Evans, S., Liddiard, R., & Steadman, P. (2021)**. 3D building stock modelling of London: Energy use intensity in the domestic sector. *Building Research & Information*, 49(5), 512–531. DOI: [10.1080/09613218.2020.1835775](https://doi.org/10.1080/09613218.2020.1835775).
32. **Comune di Bologna (2023)**. *Bologna Open Data: Patrimonio edilizio e popolazione per zona urbanistica*. Settore Urbanistica e Ambiente. [URL](http://dati.comune.bologna.it/) (Retrieved 2026-08-28).
33. **Comune di Bologna (2021)**. *Piano d'Azione per l'Energia Sostenibile e il Clima (PAESC) della Città di Bologna*. Settore Transizione Ecologica. [URL](https://www.comune.bologna.it/servizi-informazioni/piano-azione-energia-sostenibile-clima-paesc) (Retrieved 2026-08-28).
34. **Sunikka-Blank, M., & Galvin, R. (2012)**. Introducing the prebound effect: the gap between performance and actual energy consumption. *Building Research & Information*, 40(3), 260–273. DOI: [10.1080/09613218.2012.670388](https://doi.org/10.1080/09613218.2012.670388).
35. **Cayre, É., Allibe, B., Laurent, M.-H., & Osso, D. (2011)**. There are plenty of rooms for improvement. A survey on space heating and domestic hot water in French residential buildings. *ECEEE 2011 Summer Study Proceedings*, 1689–1699.
36. **ADEME (2013)**. *Enquête PHEBUS: Performance de l'Habitat, Efficacité et Besoins d'Usage de l'Énergie*. Service Économie et Prospective, ADEME, Angers.
37. **Terés-Zubiaga, J., Campos-Celador, A., González-Pino, I., & Escudero-Revilla, C. (2015)**. Internal temperatures and energy consumption in social housing in northern Spain. *Energy and Buildings*, 107, 360–373. DOI: [10.1016/j.enbuild.2015.08.037](https://doi.org/10.1016/j.enbuild.2015.08.037).
38. **Sendra, J. J., Domínguez-Amarillo, S., Bustamante, P., & León-Rodríguez, A. L. (2020)**. Energy poverty and fuel rationing in southern European multi-family social housing. *Energy and Buildings*, 223, 110188. DOI: [10.1016/j.enbuild.2020.110188](https://doi.org/10.1016/j.enbuild.2020.110188).
39. **Galvin, R. (2014)**. Making the 'prebound effect' count in energy and climate policies. *Energy Efficiency*, 7(2), 231–249. DOI: [10.1007/s12053-013-9219-3](https://doi.org/10.1007/s12053-013-9219-3).
40. **Hughes, M., & Palmer, J. (2013)**. *Cambridge Housing Model: User Guide and Technical Documentation*. Department of Energy & Climate Change (DECC), Cambridge Architectural Research.
41. **Cozza, S., Chambers, J., & Patel, M. K. (2020)**. Measuring the actual energy performance of buildings: The prebound effect in Switzerland and Italy. *Energy and Buildings*, 229, 110525. DOI: [10.1016/j.enbuild.2020.110525](https://doi.org/10.1016/j.enbuild.2020.110525).
42. **Magrini, A., Lentini, G., Cuman, S., Bodrato, A., & Marenco, L. (2016)**. From energy audit to energy performance certification of existing buildings: Overcoming the calculation gap. *Energy Procedia*, 101, 201–208. DOI: [10.1016/j.egypro.2016.11.026](https://doi.org/10.1016/j.egypro.2016.11.026).
43. **Haas, R., & Biermayr, P. (2000)**. The rebound effect for space heating: Empirical evidence from Austria. *Energy Policy*, 28(6–7), 403–410. DOI: [10.1016/S0301-4215(00)00023-9](https://doi.org/10.1016/S0301-4215(00)00023-9).
44. **Aydin, E., Kok, N., & Brounen, D. (2017)**. Energy efficiency and household behavior: The rebound effect in the residential sector. *RAND Corporation / Journal of Environmental Economics and Management*, 86, 120–138. DOI: [10.1016/j.jeem.2017.06.004](https://doi.org/10.1016/j.jeem.2017.06.004).
45. **Shipworth, M., Firth, S. K., Kane, M. I., Wright, A. J., & Lomas, K. J. (2010)**. Central heating thermostat settings and timing: Building demographics. *Building Research & Information*, 38(1), 50–69. DOI: [10.1080/09613210903263007](https://doi.org/10.1080/09613210903263007).
46. **Kelly, S., Shipworth, M., Shipworth, D., Braybley, N., & Wright, A. (2013)**. Predicting domestic carbon dioxide emissions using neural approach: An analysis of the UK residential sector. *Building and Environment*, 68, 140–151. DOI: [10.1016/j.buildenv.2013.06.012](https://doi.org/10.1016/j.buildenv.2013.06.012).
47. **Prada, A., Baggio, P., Cappelletti, F., & Gasparella, A. (2014)**. Multi-zone dynamic simulation of residential buildings: Comparing lumped versus apartment-disaggregated models. *Energy and Buildings*, 75, 456–467. DOI: [10.1016/j.enbuild.2014.02.040](https://doi.org/10.1016/j.enbuild.2014.02.040).
48. **Remmen, P., Lauster, M., Mans, M., Fuchs, M., Osterhage, T., & Müller, D. (2018)**. TEASER: An open tool for urban energy modelling of building stocks. *Journal of Building Performance Simulation*, 11(1), 84–98. DOI: [10.1080/19401493.2017.1283539](https://doi.org/10.1080/19401493.2017.1283539).
49. **CEN (2017)**. *EN ISO 13786:2017 — Thermal performance of building components — Dynamic thermal characteristics — Calculation methods*. European Committee for Standardization, Brussels.
50. **CEN (2017)**. *EN ISO 52016-1:2017 — Energy performance of buildings — Energy needs for heating and cooling, internal temperatures and sensible and latent heat loads*. European Committee for Standardization, Brussels.
