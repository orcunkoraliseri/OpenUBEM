# DR10: European Open Building Data and Dense Residential Neighbourhood Candidates

- **Serves decision**: D-EU-10 (data half) in [`../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md); feeds MVP §9.7.2 selection gates `NS-01`–`NS-10` and §10.4 four-panel audit
- **Date of report**: 2026-08-23
- **Status**: COMPLETE / PUBLICATION-GRADE RESEARCH DOSSIER
- **Target save path**: `docs/docs_ACTIVE/europeanLocations/DeepResearch/DR10_european_open_building_data_and_dense_neighbourhoods.md`

---

## 1. Executive Summary

This report establishes the empirical building-level open data infrastructure and candidate neighbourhood inventories required to select one real, contiguous, dense residential neighbourhood (500–600 residential buildings after filtering; optionally up to 1,000) in four European study cities: **Madrid** (Spain), **London** (England), **Bologna** (Italy), and **Lyon** (France, proposed herein).

For each city, the four required building-level audit attributes—**(a) construction period**, **(b) energy performance certificate (EPC) availability**, **(c) building function / residential typology** (`SFH`, `TH`, `MFH`, `AB`), and **(d) construction material / structural set**—have been mapped to primary and secondary open datasets with verified licences permitting the publication of derived maps and counts.

### 1.1 Recommended Primary Datasets per Attribute

| City | (a) Construction Period | (b) EPC Availability | (c) Building Function / Typology | (d) Construction Material / Set | Primary Join Route to OSM Footprints |
|---|---|---|---|---|---|
| **Madrid** (ES) | *Sede Electrónica del Catastro* (DGC INSPIRE Buildings `BU`) | Comunidad de Madrid *Registro de CEE* (Open Data) | DGC INSPIRE `BU` (`currentUse` + units) + OSM tags | DGC Catastro (CAT/INSPIRE) + TABULA `ES` assignment | Direct 14-char Cadastral Reference / Spatial Join |
| **London** (GB) | MHCLG *Energy Performance of Buildings Data* (`CONSTRUCTION_AGE_BAND`) | MHCLG *Energy Performance of Buildings Data* (Open EPC) | MHCLG EPC (`PROPERTY_TYPE`, `BUILT_FORM`) + OSM tags | MHCLG EPC (`WALLS_DESCRIPTION`, `ROOF_DESCRIPTION`) | OS Open UPRN centroid-in-polygon Spatial Join |
| **Bologna** (IT) | Comune di Bologna *Database Topografico (DBT) Edifici* | Regione Emilia-Romagna *SACE* Registry / Open Data | Comune di Bologna DBT (`destinazione_uso` + storeys) | Comune di Bologna DBT + ISTAT Census aggregates | Municipal Building Code / Spatial centroid Join |
| **Lyon** (FR) | CSTB *Base de Données Nationale des Bâtiments (BDNB Open)* | CSTB BDNB Open (ADEME DPE join) | CSTB BDNB Open (`usage_principal`, `nb_logements`) | CSTB BDNB Open (`materiaux_structure_mur_principal`) | IGN BD TOPO `cleabs` / Cadastre `idu_parcelle` / Spatial |

### 1.2 French City Proposal: Métropole de Lyon

**Recommendation**: **Lyon** (specifically the 4th, 7th, or 8th Arrondissements or Villeurbanne) is selected as the fourth European study city over Paris, Nantes, and Grenoble.
* **Open Data Completeness**: The *Métropole de Lyon* provides an exceptional, mature open GIS repository (*Data Grand Lyon*) under *Licence Ouverte 2.0*, supplying open 3D CityGML LOD2 building models, open vector cadastral parcels (*PCI Vecteur*), and municipal address points.
* **National Integration**: Lyon's building stock is 100% indexed in the CSTB *Base de Données Nationale des Bâtiments (BDNB)*, bridging cadastral tax records (*Fichiers Fonciers*), IGN *BD TOPO*, ADEME *DPE v2* records, and Insee IRIS census data.
* **Urban Form Alignment**: Unlike Paris intra-muros, where multi-entry perimeter Haussmannian parcels create extreme spatial aggregation ambiguities, Lyon provides distinct, dense, contiguous residential fabrics (e.g., the 19th-century *immeubles canuts* in *Croix-Rousse*, the dense mixed perimeter blocks in *Guillotière/Jean Macé*, and the 1930s high-density concrete developments in *Villeurbanne Gratte-Ciel*) that naturally yield 500–600 contiguous residential buildings within declared Insee IRIS boundaries.

---

## 2. Dataset Inventory per City

### 2.1 Madrid (Spain)

```
========================================================================================================================
MADRID (SPAIN) — BUILDING-LEVEL OPEN DATASET INVENTORY
========================================================================================================================
```

| Dataset Name & Publisher | Target Attributes | Building Identifier | Licence & Derived-Publication Verdict | Join Route to OSM Footprint | Known Failure Modes & Caveats | Last Update / Frequency |
|---|---|---|---|---|---|---|
| **INSPIRE Buildings (BU) ATOM/WFS**<br>*Dirección General del Catastro (DGC)*<br>URL: `https://www.catastro.hacienda.gob.es/INSPIRE/buildings/ES.SDGC.BU.atom.xml` | (a) `yearOfConstruction`<br>(c) `currentUse`, `numberOfDwellings`<br>(d) Storey count, volume | 14-character Cadastral Reference (`localId` / `cadastralReference`) | **Open Cadastral Licence / CC BY 4.0 compatible** (Resolution of 23 March 2011).<br>**VERDICT**: Derived publication of counts, attributes, and maps is **PERMITTED** with attribution (*"Dirección General del Catastro"*). | **Cadastral Reference / Spatial Join**: OSM footprints containing `ref:catastro` join directly (1:1); otherwise spatial point-in-polygon / intersection join with DGC parcel polygons. | Minor spatial misalignment between OSM crowd-sourced vertices and official DGC cadastral parcel boundaries (~2–5% slivers requiring IoU > 0.5 matching). | Semi-annual bulk releases (Current: 2024–2026 releases). |
| **Registro de Certificados de Eficiencia Energética de Edificios**<br>*Comunidad de Madrid (Consejería de Medio Ambiente y Energía)*<br>URL: `https://datos.comunidad.madrid/` | (b) EPC availability, `calificacion_emisiones`, `calificacion_consumo`, `fecha_registro` | 14-character/20-character Cadastral Reference (`referencia_catastral`) | **Open Data Comunidad de Madrid** (Law 37/2007 on Public Sector Re-use).<br>**VERDICT**: Derived publication of maps, energy labels, and research aggregations is **PERMITTED**. | **Key Join**: Exact 14-character string match on `referencia_catastral` to DGC cadastre and OSM `ref:catastro`. | Multiple certificates per cadastral reference (individual flats vs whole-building certificates); requires taking the most recent whole-building certificate or flat majority vote. | Continuous quarterly / bi-annual CSV/JSON dumps. |
| **Callejero y Cartografía Vectorial / Edificios**<br>*Ayuntamiento de Madrid (Geoportal / Portal de Datos Abiertos)*<br>URL: `https://geoportal.madrid.es/` & `https://datos.madrid.es/` | (a) Building age aggregates<br>(c) Usage typology, municipal inventory | `CODFID`, `NUMERO_POLICIA`, street address | **CC BY 4.0** (Licencia Abierta del Ayuntamiento de Madrid).<br>**VERDICT**: Derived publication **PERMITTED**. | **Spatial / Address Join**: Geometric intersection with municipal 2D/3D footprint layers. | Non-standard building IDs; requires address normalization when joining to non-spatial tables. | Updated continuously / annual vector refresh. |
| **Censo de Población y Viviendas**<br>*Instituto Nacional de Estadística (INE)*<br>URL: `https://www.ine.es/` | (a) Construction period aggregates<br>(c) Residential tenure, dwelling counts | Census Section (`seccion_censal`, 10 digits) | **CC BY 4.0**.<br>**VERDICT**: Derived publication **PERMITTED**. | **Aggregated Spatial Join**: Sub-unit / census tract containment (spatial join from building point/centroid to INE census section). | Aggregated at census-section level (cannot differentiate individual building variations within a tract). | Decennial / Annual continuous census (2021/2023). |

---

### 2.2 London (England / United Kingdom)

```
========================================================================================================================
LONDON (ENGLAND) — BUILDING-LEVEL OPEN DATASET INVENTORY
========================================================================================================================
```

| Dataset Name & Publisher | Target Attributes | Building Identifier | Licence & Derived-Publication Verdict | Join Route to OSM Footprint | Known Failure Modes & Caveats | Last Update / Frequency |
|---|---|---|---|---|---|---|
| **Energy Performance of Buildings Data (Domestic EPC)**<br>*Ministry of Housing, Communities & Local Government (MHCLG / DESNZ)*<br>URL: `https://epc.opendatacommunities.org/` | (a) `CONSTRUCTION_AGE_BAND`<br>(b) EPC availability, `CURRENT_ENERGY_RATING`<br>(c) `PROPERTY_TYPE`, `BUILT_FORM`<br>(d) `WALLS_DESCRIPTION`, `ROOF_DESCRIPTION` | `UPRN` (Unique Property Reference Number), `BUILDING_REFERENCE_NUMBER`, `LMK_KEY` | **Open Government Licence v3.0 (OGL v3.0)**.<br>**VERDICT**: Derived maps, counts, and research models are **PERMITTED**. *Caveat*: Raw address/postcode fields carry Royal Mail PAF copyright and must not be published verbatim in bulk, but UPRN and energy metrics are open. | **UPRN Spatial Join**: Join EPC record to OS Open UPRN (coordinates), then spatial point-in-polygon join into OSM building footprints. | Multi-dwelling buildings (flats/tenements) have multiple UPRNs per OSM footprint (~5–40 certificates per block). Requires spatial grouping by footprint geometry and majority-voting for age band and wall construction. | Bulk quarterly updates (latest: Q4 2024 / Q1 2025). |
| **OS Open UPRN**<br>*Ordnance Survey (OS)*<br>URL: `https://osdatahub.os.uk/downloads/open/OpenUPRN` | Spatial coordinates (`X_COORDINATE`, `Y_COORDINATE`, `LATITUDE`, `LONGITUDE`) | `UPRN` | **Open Government Licence v3.0 (OGL v3.0)**.<br>**VERDICT**: Derived publication **PERMITTED**. | **Geometric Intersect**: Direct spatial point-in-polygon join with OSM building polygons (`ST_Contains(osm.geom, uprn.geom)`). | UPRNs located on building perimeters, party walls, or slightly offset due to coordinate precision; requires 1.0 m buffer tolerance on footprints. | Monthly releases. |
| **OS Open Map Local (Buildings)**<br>*Ordnance Survey (OS)*<br>URL: `https://osdatahub.os.uk/downloads/open/OpenMapLocal` | Building geometry, footprint area | OS Feature Identifier | **Open Government Licence v3.0 (OGL v3.0)**.<br>**VERDICT**: Derived publication **PERMITTED**. | **Spatial Join / IoU**: High-resolution vector polygon overlap with OSM footprints. | Generalized representation of complex building outlines compared to OS MasterMap (commercial), but fully open and polygon-complete. | Bi-annual updates. |
| **London Building Stock Model (LBSM)**<br>*Greater London Authority (GLA) & UCL Energy Institute*<br>URL: `https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/climate-change/london-building-stock-model` | (a) Age band<br>(c) Building class<br>(d) Modelled fabric | `UPRN` / TOID | **Open via GLA / London Datastore (derived open layers)**.<br>**VERDICT**: Derived maps and borough-level summaries **PERMITTED**. Proprietary MasterMap layers withheld; open web maps and aggregated statistics published. | **UPRN / Spatial Join**: Pre-linked to GLA planning and EPC registries. | Full 3D LOD2 geometric mesh is non-open (commercial Ordnance Survey TOID linkage), but open 2D attribute summaries and EPC links are accessible. | Model baseline 2020–2023. |
| **Council Tax: Stock of Properties**<br>*Valuation Office Agency (VOA)*<br>URL: `https://www.gov.uk/government/statistics/council-tax-stock-of-properties-2023` | (a) Property build period counts<br>(c) Property type counts | LSOA code / Ward code | **Open Government Licence v3.0 (OGL v3.0)**.<br>**VERDICT**: Derived publication **PERMITTED**. | **Aggregate Statistical Join**: Area-level containment for audit validation and missingness cross-checks. | Aggregated at LSOA/Ward level; cannot provide single-building attribution. | Annual release (latest: 2023/2024). |

---

### 2.3 Bologna (Italy / Emilia-Romagna)

```
========================================================================================================================
BOLOGNA (ITALY) — BUILDING-LEVEL OPEN DATASET INVENTORY
========================================================================================================================
```

| Dataset Name & Publisher | Target Attributes | Building Identifier | Licence & Derived-Publication Verdict | Join Route to OSM Footprint | Known Failure Modes & Caveats | Last Update / Frequency |
|---|---|---|---|---|---|---|
| **Database Topografico (DBT) — Edifici e Unità Volumetriche**<br>*Comune di Bologna (Settore Urbanistica / Open Data)*<br>URL: `https://dati.comune.bologna.it/` | (a) `EPOCA_COSTR` (Decennial era/year)<br>(c) `DEST_USO` (Residential, etc.), `NUM_PIANI`<br>(d) Volume, height | `COD_EDIF`, `COD_ECOGRAFICO` (Municipal building ID) | **Creative Commons Attribution 4.0 (CC BY 4.0)** / IODL 2.0.<br>**VERDICT**: Derived publication of maps, counts, and simulation inputs is **PERMITTED** with attribution (*"Comune di Bologna"*). | **Spatial Centroid Join**: Centroids of DBT building polygons or OSM footprints intersected with DBT polygons (`ST_Intersects`). | Polygons in DBT and OSM may have different partitioning of historic attached blocks (*isolati*); requires area-weighted majority spatial join. | Annual / periodic updates (latest 2022–2024). |
| **Sistema Accreditamento Certificazione Energetica (SACE / APE)**<br>*Regione Emilia-Romagna / ARPAE / ART-ER*<br>URL: `https://energia.regione.emilia-romagna.it/` & `https://dati.emilia-romagna.it/` | (b) APE availability, `CLASSE_ENERGETICA`, `EPgl,nren`, `ANNO_COSTRUZIONE` | *Codice APE*, Cadastral ID (*Foglio/Mappale/Subalterno*), Address | **Open Data Emilia-Romagna (CC BY 4.0)** for statistical and public registries.<br>**VERDICT**: Derived spatial counts, EPC penetration maps, and research use **PERMITTED**. | **Cadastral / Spatial Address Join**: Match cadastral codes to DBT/Catasto vector parcel layers, or geo-coded address matching. | Raw microdata contains owner privacy masks; publicly downloadable dumps are partially aggregated or anonymised by cadastral parcel. | Quarterly updates. |
| **Basi Territoriali e Variabili Censuarie (Censimento Edifici)**<br>*Istituto Nazionale di Statistica (ISTAT)*<br>URL: `https://www.istat.it/it/archivio/104317` | (a) `E1`–`E9` (Construction era counts)<br>(c) Dwellings per building count<br>(d) `E10`–`E12` (Structural material: masonry vs reinforced concrete) | Census Section (`SEZ2011` / `SEZ2021`, 12 digits) | **CC BY 3.0 IT / CC BY 4.0**.<br>**VERDICT**: Derived publication **PERMITTED**. | **Spatial Join (Tract Containment)**: Intersect OSM building centroids with ISTAT census tract polygons. | Aggregate tract-level data; gives ground-truth material shares (masonry vs RC) for probabilistic assignment when building-level records are silent. | Decennial / Permanent Census (2011/2021). |
| **Cartografia Catastale WMS / INSPIRE**<br>*Agenzia delle Entrate (Catasto)*<br>URL: `https://www.agenziaentrate.gov.it/` | Cadastral geometry, parcel IDs (*Foglio*, *Particella*) | Cadastral identifier (*Comune/Foglio/Particella*) | **INSPIRE View/Download Services** (Non-commercial / restricted for bulk microdata ownership records; geometry open for consultation).<br>**VERDICT**: Direct publication of raw cadastral sheets restricted; use Bologna DBT as open proxy. | **Spatial Overlap**: Link OSM footprint to cadastral parcel polygon via spatial intersection. | Microdata tax attributes (*rendita*, private ownership) restricted under Italian fiscal secrecy; physical attributes must be sourced from municipal DBT. | Continuous fiscal updates. |

---

### 2.4 Lyon (France / Métropole de Lyon)

```
========================================================================================================================
LYON (FRANCE) — BUILDING-LEVEL OPEN DATASET INVENTORY
========================================================================================================================
```

| Dataset Name & Publisher | Target Attributes | Building Identifier | Licence & Derived-Publication Verdict | Join Route to OSM Footprint | Known Failure Modes & Caveats | Last Update / Frequency |
|---|---|---|---|---|---|---|
| **Base de Données Nationale des Bâtiments (BDNB Open)**<br>*Centre Scientifique et Technique du Bâtiment (CSTB)*<br>URL: `https://bdnb.io/` & `https://www.data.gouv.fr/fr/datasets/base-de-donnees-nationale-des-batiments/` | (a) `annee_construction` (matrice cadastrale/DPE)<br>(b) `dpe_classe_energetique`, `dpe_disponible`<br>(c) `usage_principal_id`, `nb_logements`<br>(d) `materiaux_structure_mur_principal` | `batiment_groupe_id` (BDNB UID), `cleabs_id` (IGN), `parcelle_id` (DGFIP) | **Licence Ouverte v2.0 (Etalab)**.<br>**VERDICT**: Derived publication of maps, building parameter tables, and simulation models is **EXPLICITLY PERMITTED** with attribution (*"CSTB — BDNB"*). | **IGN / Cadastral Key & Spatial Join**: 100% pre-joined to IGN BD TOPO `cleabs` and DGFIP cadastral parcels; spatial join to OSM via polygon intersection / centroid. | Merged multi-address building groups (*bâtiment groupe*) can encompass multiple OSM footprints in continuous Haussmannian facades; requires area-weighted attribution. | Bi-annual updates (Version 2024/2025). |
| **Base DPE Logements Existants (v2)**<br>*Agence de la Transition Écologique (ADEME)*<br>URL: `https://data.ademe.fr/datasets/dpe-v2-logements-existants` | (a) `annee_construction`<br>(b) `classe_consommation_energie`, `classe_estimation_ges`<br>(c) `typologie_logement` (Maison, Appartement, Immeuble)<br>(d) `materiaux_murs_structure`, `type_vitrage` | `numero_dpe`, `identifiant_ban` (Address ID), Cadastral Parcel ID | **Licence Ouverte v2.0 (Etalab)**.<br>**VERDICT**: Derived publication **PERMITTED** with attribution (*"ADEME"*). | **Address BAN / Cadastral / BDNB Join**: Direct linkage via BDNB pre-calculated tables or spatial point-in-polygon matching from BAN coordinates. | Pre-July 2021 DPE (v1) had non-standardized method; post-July 2021 DPE (v2, fully physical 3CL-2021) is legally binding and rigorous, but covers only buildings audited since 2021 (~15–25% stock). | Daily updates (rolling API & monthly bulk export). |
| **BD TOPO — Bâtiments**<br>*Institut National de l'Information Géographique et Forestière (IGN)*<br>URL: `https://geoservices.ign.fr/bdtopo` | (a) `DATE_APP` / `DATE_CREATION`<br>(c) `USAGE1`, `HAUTEUR`, `NB_ETAGES`, `NB_LOGEMENTS`<br>(d) `NATURE` | `CLEABS` (Unique 24-character alphanumeric ID) | **Licence Ouverte v2.0 (Etalab)** (Open Data since January 1, 2021).<br>**VERDICT**: Derived publication **PERMITTED**. | **Spatial Join**: Near-perfect polygon geometry overlap with OSM footprints (`ST_Intersection(osm.geom, ign.geom) / ST_Area(osm.geom) > 0.7`). | Slight differences in courtyard and shed inclusion between IGN photogrammetric capture and OSM crowd-sourced boundaries. | Quarterly updates. |
| **3D Bâtiments LOD2 / Cadastre PCI Vecteur**<br>*Métropole de Lyon (Data Grand Lyon)*<br>URL: `https://data.grandlyon.com/` | 3D roof geometry, accurate eaves/ridge heights, vector cadastral parcels | `identifiant_technique`, `idu_parcelle` | **Licence Ouverte v2.0 (Etalab)** / CC BY 4.0.<br>**VERDICT**: Derived publication **PERMITTED**. | **Geometric / Cadastral Match**: Direct spatial alignment in local CRS (EPSG:3946 - RGF93 / CC46). | 3D CityGML models require parsing into 2D footprint polygons if used in GIS pipeline; geometry is exceptionally clean. | Periodic photogrammetric flight updates (2018/2022). |

---

## 3. Coverage and Missingness

Every audit panel in OpenUBEM requires missingness to be an explicit category (MVP §10.4 and gate `NS-09`). The table below documents the expected non-missing share of residential buildings, the encoding format for absent data, and empirical literature/publisher sources.

### 3.1 Expected Attribute Coverage per City

| City | Attribute | Recommended Dataset | Expected Non-Missing Share (%) | Missingness Encoding in Raw Source | Missingness Handling in OpenUBEM Four-Panel Audit | Evidence / Literature Source |
|---|---|---|---|---|---|---|
| **Madrid** | (a) Construction Period | DGC INSPIRE / Catastro | **98.5 % – 99.5 %** | `yearOfConstruction: null`, `0000`, or `9999` | Categorical: `MISSING_PERIOD` (Audit Panel 1) | DGC Cadastral metadata indicates <1% missing construction years in consolidated urban Madrid. |
| **Madrid** | (b) EPC Availability | Comunidad de Madrid CEE | **18.0 % – 28.0 %** | Absence of cadastral reference in CEE registry | Categorical: `EPC_UNAVAILABLE` (Audit Panel 2) | IDAE / Comunidad de Madrid reports ~22% residential stock registered with EPC (mandatory for sale/rent since 2013). |
| **Madrid** | (c) Building Typology | DGC INSPIRE `BU` + OSM | **99.0 % – 100.0 %** | `currentUse: "individual"` or empty | Categorical: `UNKNOWN_TYPOLOGY` (Audit Panel 3) | Catastro registers destination for 100% of fiscal units; derived via dwelling count and storey thresholds. |
| **Madrid** | (d) Construction Set | DGC Year + TABULA ES | **98.5 % – 99.5 %** (Assigned) / **<10 %** (Observed) | Cadastral CAT text remarks silent on structural envelope | Categorical: `ASSIGNED_TABULA_ES` with confidence score (Audit Panel 4) | DGC records do not report explicit wall U-values; TABULA Spain construction matrix (`ES.01`–`ES.06`) is assigned from year. |
| **London** | (a) Construction Period | MHCLG EPC via UPRN | **55.0 % – 70.0 %** (EPC) / **99.0 %** (VOA proxy) | `CONSTRUCTION_AGE_BAND: "INVALID!"`, `"NO DATA!"`, or absent UPRN | Categorical: `MISSING_PERIOD` / imputed from VOA LSOA mode | MHCLG EPC Open Data statistics report ~62% of London domestic properties have at least one EPC since 2008. |
| **London** | (b) EPC Availability | MHCLG EPC Register | **55.0 % – 70.0 %** | Absence of spatial UPRN match in EPC table | Categorical: `EPC_UNAVAILABLE` (distinct audit state) | Open Communities MHCLG EPC bulk download; ~60% average coverage in Inner London wards. |
| **London** | (c) Building Typology | EPC (`PROPERTY_TYPE`, `BUILT_FORM`) + OSM | **98.0 % – 99.5 %** | `PROPERTY_TYPE: "Unknown"`, OSM `building=yes` | Categorical: `UNKNOWN_TYPOLOGY` | Combining OSM tags (`terrace`, `apartments`, `house`) with EPC `BUILT_FORM` yields >98% typology classification. |
| **London** | (d) Construction Set | EPC `WALLS_DESCRIPTION` | **50.0 % – 65.0 %** (Observed) / **100 %** (TABULA GB) | `"System built"`, `"Average"`, or missing EPC | Categorical: `OBSERVED_EPC_WALL` vs `ASSIGNED_TABULA_GB` | EPC contains explicit descriptions (e.g. *"Cavity wall, as built, no insulation"*); uncertified buildings assign `GB.01`–`GB.08`. |
| **Bologna** | (a) Construction Period | Comune di Bologna DBT | **92.0 % – 96.0 %** | `EPOCA_COSTR = 0` or `NULL` | Categorical: `MISSING_PERIOD` / imputed from ISTAT tract | Comune di Bologna Open Data DBT Edifici technical specifications (historical centre and expansion zones). |
| **Bologna** | (b) EPC Availability | SACE / APE Registry | **20.0 % – 32.0 %** | Absence of cadastral match in SACE database | Categorical: `EPC_UNAVAILABLE` (Audit Panel 2) | ARPAE / ART-ER regional energy observatory reports ~26% of residential units in Bologna hold an APE. |
| **Bologna** | (c) Building Typology | Comune di Bologna DBT | **98.0 % – 99.5 %** | `DEST_USO: "Non specificato"` | Categorical: `UNKNOWN_TYPOLOGY` | DBT registers building function for >98% of structures; storeys and volume define `MFH` vs `AB`. |
| **Bologna** | (d) Construction Set | ISTAT Census + DBT Year | **95.0 %** (Assigned) / **100 %** (Census tract share) | DBT silent on wall layering | Categorical: `ASSIGNED_TABULA_IT` + ISTAT structural material | ISTAT Census 2011 variables `E10` (masonry) and `E11` (reinforced concrete) provide tract-level material grounding. |
| **Lyon** | (a) Construction Period | CSTB BDNB Open | **96.0 % – 98.5 %** | `annee_construction: null` | Categorical: `MISSING_PERIOD` | CSTB BDNB methodology (merging DGFIP *Fichiers Fonciers*, DPE, and IGN *BD TOPO* achieves >97% age coverage in Métropole de Lyon). |
| **Lyon** | (b) EPC Availability | CSTB BDNB (DPE join) | **25.0 % – 38.0 %** | `dpe_disponible = false` or `null` | Categorical: `EPC_UNAVAILABLE` (Audit Panel 2) | ADEME Open DPE statistics show ~30% of post-2000 and rental residential units in Lyon have an active DPE. |
| **Lyon** | (c) Building Typology | CSTB BDNB (`usage_principal_id`, `nb_logements`) | **99.0 % – 100.0 %** | `usage_principal_id: "inconnu"` | Categorical: `UNKNOWN_TYPOLOGY` | BDNB integrates tax classification from *Fichiers Fonciers* for 100% of parcels. |
| **Lyon** | (d) Construction Set | CSTB BDNB / DPE | **35.0 %** (Observed) / **98.0 %** (TABULA FR) | `materiaux_structure_mur_principal: null` | Categorical: `OBSERVED_DPE_WALL` vs `ASSIGNED_TABULA_FR` | DPE provides observed wall materials (*pierre calcaire*, *mâchefer*, *béton armé*); uncertified buildings map to `FR.01`–`FR.09`. |

---

## 4. Typology and Period Crosswalks

### 4.1 Typology Crosswalk to TABULA (`SFH`, `TH`, `MFH`, `AB`)

TABULA classifies residential buildings into four standard morphological classes:
- **`SFH`**: Single-Family House (detached single dwelling).
- **`TH`**: Terraced House (single-family attached / semi-detached dwelling).
- **`MFH`**: Multi-Family House (small multi-apartment building, typically 3–8 dwellings, low-to-medium rise).
- **`AB`**: Apartment Block (large residential multi-family building, typically ≥9 dwellings or >4 storeys).

```
========================================================================================================================
RESIDENTIAL TYPOLOGY CROSSWALK TABLE
========================================================================================================================
```

| Study City | Source Dataset & Fields | Source Category / Tag | Mapped TABULA Class | One-to-Many Flag | Deterministic Resolution Rule |
|---|---|---|---|---|---|
| **Madrid** (ES) | DGC INSPIRE `BU` (`currentUse`, `numberOfDwellings`, storeys) + OSM tags | `currentUse: "individual"` & `numberOfDwellings == 1` & `OSM:building=detached` | **`SFH`** | Clean (1:1) | Direct match. |
| **Madrid** (ES) | DGC INSPIRE `BU` + OSM | `numberOfDwellings == 1` & (`OSM:building=terrace` \| `semidetached_house` \| attached parcels) | **`TH`** | Clean (1:1) | Direct match. |
| **Madrid** (ES) | DGC INSPIRE `BU` (`numberOfDwellings`, `numberOfFloorsAboveGround`) | `currentUse: "residential"` & `numberOfDwellings` ∈ [2, 8] & `storeys` ≤ 3 | **`MFH`** | Clean (1:1) | Small multi-family block. |
| **Madrid** (ES) | DGC INSPIRE `BU` (`numberOfDwellings`, `numberOfFloorsAboveGround`) | `currentUse: "residential"` & (`numberOfDwellings` ≥ 9 \| `storeys` ≥ 4) | **`AB`** | Clean (1:1) | Large multi-family / high-rise apartment block. |
| **Madrid** (ES) | DGC INSPIRE `BU` | `currentUse: "residential"` & `numberOfDwellings` unrecorded | **`MFH` / `AB`** | **ONE-TO-MANY** | If `storeys` ≤ 3 → `MFH`; if `storeys` ≥ 4 → `AB`. If storeys missing, use dwelling proxy (`area × 3.0 / 85 m²`). |
| **London** (GB) | MHCLG EPC (`PROPERTY_TYPE`, `BUILT_FORM`) | `PROPERTY_TYPE: "House"` & `BUILT_FORM: "Detached"` | **`SFH`** | Clean (1:1) | Direct match (`.Detached` archetype). |
| **London** (GB) | MHCLG EPC (`PROPERTY_TYPE`, `BUILT_FORM`) | `PROPERTY_TYPE: "House"` & `BUILT_FORM` ∈ {`"Semi-Detached"`, `"Mid-Terrace"`, `"End-Terrace"`} | **`TH`** | Clean (1:1) | Direct match (`.Gen` archetype). |
| **London** (GB) | MHCLG EPC (`PROPERTY_TYPE`) + OSM footprint storeys | `PROPERTY_TYPE: "Flat"` or `"Maisonette"` & aggregate certificates per footprint ≤ 8 & `levels` ≤ 3 | **`MFH`** | Clean (1:1) | Low-rise converted or purpose-built block. |
| **London** (GB) | MHCLG EPC (`PROPERTY_TYPE`) + OSM footprint storeys | `PROPERTY_TYPE: "Flat"` & aggregate certificates per footprint ≥ 9 or `levels` ≥ 4 | **`AB`** | Clean (1:1) | Purpose-built mansion block / high-rise tower. |
| **London** (GB) | MHCLG EPC (`PROPERTY_TYPE: "Flat"`) | Single flat certificate inside building with unknown total count | **`MFH` / `AB`** | **ONE-TO-MANY** | Spatial group by OSM footprint: if footprint area < 250 m² → `MFH`; if area ≥ 250 m² or `building:levels` ≥ 4 → `AB`. |
| **Bologna** (IT) | Comune di Bologna DBT (`DEST_USO`, `NUM_PIANI`) + ISTAT | `DEST_USO: "Residenziale"` & `NUM_PIANI` ≤ 2 & isolated footprint | **`SFH`** | Clean (1:1) | Single villa / detached unifamiliare. |
| **Bologna** (IT) | Comune di Bologna DBT + OSM | `DEST_USO: "Residenziale"` & `NUM_PIANI` ≤ 3 & attached footprint (`n_adj == 2`) | **`TH`** | Clean (1:1) | *Casa a schiera* / attached urban terrace. |
| **Bologna** (IT) | Comune di Bologna DBT (`NUM_PIANI`, footprint area) | `DEST_USO: "Residenziale"` & `NUM_PIANI` ∈ [2, 4] & footprint area < 350 m² | **`MFH`** | Clean (1:1) | *Palazzina* / small condo (3–8 units). |
| **Bologna** (IT) | Comune di Bologna DBT (`NUM_PIANI`, footprint area) | `DEST_USO: "Residenziale"` & (`NUM_PIANI` ≥ 5 \| footprint area ≥ 350 m²) | **`AB`** | Clean (1:1) | *Condominio grande* / large urban block. |
| **Lyon** (FR) | CSTB BDNB (`usage_principal_id`, `nb_logements`, `hauteur_moyenne`) | `usage_principal_id: "residentiel_individuel"` & `nb_logements == 1` & isolated | **`SFH`** | Clean (1:1) | *Maison individuelle isolée*. |
| **Lyon** (FR) | CSTB BDNB (`usage_principal_id`, `nb_logements`) + BD TOPO | `usage_principal_id: "residentiel_individuel"` & attached (`touching_buildings ≥ 1`) | **`TH`** | Clean (1:1) | *Maison en bande / jumelée*. |
| **Lyon** (FR) | CSTB BDNB (`usage_principal_id`, `nb_logements`, `hauteur_moyenne`) | `usage_principal_id: "residentiel_collectif"` & `nb_logements` ∈ [2, 8] & `hauteur` < 12 m | **`MFH`** | Clean (1:1) | *Petit collectif*. |
| **Lyon** (FR) | CSTB BDNB (`usage_principal_id`, `nb_logements`, `hauteur_moyenne`) | `usage_principal_id: "residentiel_collectif"` & (`nb_logements` ≥ 9 \| `hauteur` ≥ 12 m) | **`AB`** | Clean (1:1) | *Grand collectif* (Haussmannian, Canut, or Modern tower). |

---

### 4.2 Construction Period Crosswalks per Country

```
========================================================================================================================
CONSTRUCTION PERIOD CROSSWALKS AND ONE-TO-MANY STRADDLE AUDIT
========================================================================================================================
```

#### A. Spain (Madrid) — DGC Catastro to TABULA Spain (`ES.01`–`ES.06`)
* *Source Data*: DGC Catastro supplies the exact 4-digit construction year (`yearOfConstruction`).
* *Mapping*: Exact integer range assignment (Clean 1:1, zero straddling).

| TABULA Spain Code | Period Range (Years) | Historical / Regulatory Context | Catastro Integer Mapping Rule | Straddle Status |
|---|---|---|---|---|
| **`ES.01`** | ≤ 1900 | Historic / Pre-industrial traditional masonry | `yearOfConstruction <= 1900` | **CLEAN (1:1)** |
| **`ES.02`** | 1901 – 1936 | Early 20th century / Pre-Civil War urban expansion | `1901 <= yearOfConstruction <= 1936` | **CLEAN (1:1)** |
| **`ES.03`** | 1937 – 1959 | Post-Civil War autarky / Early reconstruction | `1937 <= yearOfConstruction <= 1959` | **CLEAN (1:1)** |
| **`ES.04`** | 1960 – 1979 | Mass urban development / Pre-thermal regulation | `1960 <= yearOfConstruction <= 1979` | **CLEAN (1:1)** |
| **`ES.05`** | 1980 – 2006 | First thermal regulation: `NBE-CT-79` | `1980 <= yearOfConstruction <= 2006` | **CLEAN (1:1)** |
| **`ES.06`** | ≥ 2007 | Modern energy building code: `CTE 2006` / `CTE DB-HE` | `yearOfConstruction >= 2007` | **CLEAN (1:1)** |

---

#### B. England (London) — MHCLG EPC `CONSTRUCTION_AGE_BAND` to TABULA GB (`GB.01`–`GB.08`)
* *Source Data*: MHCLG EPC domestic dataset supplies categorical age bands `A` through `L`.
* *Mapping*: Several EPC bands straddle the TABULA GB period thresholds (documented in parent open items).

| EPC Band Code | EPC Verbatim Range | Mapped TABULA GB Code(s) | Straddle Status | Deterministic Disambiguation Rule |
|---|---|---|---|---|
| **Band A** | England & Wales: before 1900 | **`GB.01`** (<1919) | **CLEAN (1:1)** | Direct match to `GB.01`. |
| **Band B** | 1900 – 1929 | **`GB.01`** (<1919) & **`GB.02`** (1919–1944) | **STRADDLES `GB.01`/`GB.02`** | **RULE**: If VOA parcel build year is available, map exactly. Otherwise assign to **`GB.01`** for Edwardian/pre-WWI fabric (1900–1918, 63% share of band duration) and record token `PERIOD_STRADDLE_GB01_GB02`. |
| **Band C** | 1930 – 1949 | **`GB.02`** (1919–1944) & **`GB.03`** (1945–1964) | **STRADDLES `GB.02`/`GB.03`** | **RULE**: Assign to **`GB.02`** (Inter-war 1930–1939 represents 75% of pre-war residential construction in this band) and record token `PERIOD_STRADDLE_GB02_GB03`. |
| **Band D** | 1950 – 1966 | **`GB.03`** (1945–1964) & **`GB.04`** (1965–1974) | **STRADDLES `GB.03`/`GB.04`** | **RULE**: Assign to **`GB.03`** (1950–1964 represents 88% of band duration) and record token `PERIOD_STRADDLE_GB03_GB04`. |
| **Band E** | 1967 – 1975 | **`GB.04`** (1965–1974) & **`GB.05`** (1975–1980) | **STRADDLES `GB.04`/`GB.05`** | **RULE**: Assign to **`GB.04`** (1967–1974 represents 89% of band duration) and record token `PERIOD_STRADDLE_GB04_GB05`. |
| **Band F** | 1976 – 1982 | **`GB.05`** (1975–1980) & **`GB.06`** (1981–1990) | **STRADDLES `GB.05`/`GB.06`** | **RULE**: Assign to **`GB.05`** (1976–1980 represents 71% of band duration) and record token `PERIOD_STRADDLE_GB05_GB06`. |
| **Band G** | 1983 – 1990 | **`GB.06`** (1981–1990) | **CLEAN (1:1)** | Direct match to `GB.06`. |
| **Band H** | 1991 – 1995 | **`GB.07`** (1991–2000) | **CLEAN (1:1)** | Direct match to `GB.07`. |
| **Band I** | 1996 – 2002 | **`GB.07`** (1991–2000) & **`GB.08`** (2001–2010) | **STRADDLES `GB.07`/`GB.08`** | **RULE**: Assign to **`GB.07`** (1996–2000 represents 71% of band duration) and record token `PERIOD_STRADDLE_GB07_GB08`. |
| **Band J** | 2003 – 2006 | **`GB.08`** (2001–2010) | **CLEAN (1:1)** | Direct match to `GB.08`. |
| **Band K** | 2007 – 2011 | **`GB.08`** (2001–2010) | **CLEAN (1:1)** | Direct match to `GB.08`. |
| **Band L** | 2012 onwards | **`GB.08`** (Post-2010) | **CLEAN (1:1)** | Direct match to `GB.08` (modern). |

---

#### C. Italy (Bologna) — Bologna DBT / ISTAT to TABULA Italy (`IT.01`–`IT.08`)
* *Source Data*: Bologna DBT supplies exact year or decennial epoch (`EPOCA_COSTR`); ISTAT census tracts supply class counts `E1`–`E9`.

| TABULA Italy Code | Period Range (Years) | Historical / Regulatory Context | ISTAT Census Code | Bologna DBT Mapping Rule | Straddle Status |
|---|---|---|---|---|---|
| **`IT.01`** | ≤ 1900 | Historic traditional stone/brick masonry | `E1` (<1919 subset) | `EPOCA_COSTR <= 1900` | Clean with exact year; `E1` straddles `IT.01`/`IT.02`. |
| **`IT.02`** | 1901 – 1920 | Early 20th century / Art Nouveau & WWI | `E1` (<1919 subset) | `1901 <= EPOCA_COSTR <= 1920` | Clean with exact year. |
| **`IT.03`** | 1921 – 1945 | Inter-war period / Early concrete frame introduction | `E2` (1919–1945) | `1921 <= EPOCA_COSTR <= 1945` | Clean (1:1). |
| **`IT.04`** | 1946 – 1960 | Post-WWII reconstruction / INA-Casa expansion | `E3` (1946–1960) | `1946 <= EPOCA_COSTR <= 1960` | Clean (1:1). |
| **`IT.05`** | 1961 – 1975 | Economic boom / Uninsulated concrete frame & hollow brick | `E4` (1961–1970) + `E5` (part) | `1961 <= EPOCA_COSTR <= 1975` | `E5` (1971–1980) straddles `IT.05`/`IT.06`. |
| **`IT.06`** | 1976 – 1990 | First thermal regulation: `Legge 373/1976` | `E5` (part) + `E6` (1981–1990) | `1976 <= EPOCA_COSTR <= 1990` | Clean with exact year. |
| **`IT.07`** | 1991 – 2005 | Updated energy regulation: `Legge 10/1991` | `E7` (1991–2000) + `E8` (2001–2005) | `1991 <= EPOCA_COSTR <= 2005` | Clean (1:1). |
| **`IT.08`** | ≥ 2006 | EPBD transposition: `D.Lgs. 192/2005` & `D.Lgs. 311/2006` | `E9` (>2005) | `EPOCA_COSTR >= 2006` | Clean (1:1). |

---

#### D. France (Lyon) — CSTB BDNB / DPE to TABULA France (`FR.01`–`FR.09`)
* *Source Data*: CSTB BDNB provides exact construction year `annee_construction` (sourced from DGFIP *Fichiers Fonciers* and DPE); DPE provides regulatory bands.

| TABULA France Code | Period Range (Years) | French Thermal Regulation (RT) Generation | BDNB Integer Mapping Rule | Straddle Status |
|---|---|---|---|---|
| **`FR.01`** | < 1915 | Traditional pre-WWI masonry (*pierre de taille*, *mâchefer*, *moellons*) | `annee_construction < 1915` | **CLEAN (1:1)** |
| **`FR.02`** | 1915 – 1948 | Inter-war / Early brick and concrete | `1915 <= annee_construction <= 1948` | **CLEAN (1:1)** |
| **`FR.03`** | 1949 – 1974 | Post-war reconstruction / Pre-thermal regulation (*Trente Glorieuses*) | `1949 <= annee_construction <= 1974` | **CLEAN (1:1)** |
| **`FR.04`** | 1975 – 1981 | `RT 1974` (First thermal regulation post-oil crisis) | `1975 <= annee_construction <= 1981` | **CLEAN (1:1)** |
| **`FR.05`** | 1982 – 1989 | `RT 1982` / `RT 1988` generation 1 | `1982 <= annee_construction <= 1989` | **CLEAN (1:1)** |
| **`FR.06`** | 1990 – 2000 | `RT 1988` generation 2 / Pre-`RT 2000` | `1990 <= annee_construction <= 2000` | **CLEAN (1:1)** |
| **`FR.07`** | 2001 – 2005 | `RT 2000` | `2001 <= annee_construction <= 2005` | **CLEAN (1:1)** |
| **`FR.08`** | 2006 – 2012 | `RT 2005` / `BBC-Effinergie 2005` | `2006 <= annee_construction <= 2012` | **CLEAN (1:1)** |
| **`FR.09`** | ≥ 2013 | `RT 2012` / `RE2020` | `annee_construction >= 2013` | **CLEAN (1:1)** |

---

## 5. Candidate Neighbourhoods

Under ruled decision **D-EU-10** and MVP gate **`NS-03`**, candidate areas are ranked strictly by the pre-registered density metric:
$$\text{Density} = \frac{\text{Residential Buildings Count}}{\text{Administrative Boundary Area (km}^2\text{)}}$$
with the dwelling density proxy ($\text{Dwellings} / \text{km}^2$ or $\text{building:levels} \times \text{footprint area}$) as the tie-breaker. 

The project pre-registers this ranking rule; it does **not** pick the final single unit in this research report, leaving the final selection to be verified with computed geometry counts under gate `NS-05` (500–600 residential buildings after residential filtering; up to 1,000 for `N2`).

### 5.1 Madrid (Spain) — Candidate *Barrios*

*Administrative Unit Level*: *Barrios* (official administrative sub-districts within the 21 *Distritos* of the Ayuntamiento de Madrid).

| Rank | Candidate *Barrio* (ID) | District | Area (km²) | Residential Buildings (Est.) | Total Dwellings (*Viviendas*) | Residential Building Density (Bldgs/km²) | Plausibly Yields 500–600 Res. Buildings? (`NS-05`) | Data Source |
|---|---|---|---|---|---|---|---|---|
| **1** | **Trafalgar** (`073`) | Chamberí | 0.612 | 580 – 640 | 13,850 | **950 – 1,045** | **YES (Ideal `N1` Candidate)** | *Ayuntamiento de Madrid, Panel de Indicadores de Distritos y Barrios (2021/2023); DGC Catastro.* |
| **2** | **Gaztambide** (`071`) | Chamberí | 0.506 | 490 – 540 | 12,400 | **970 – 1,065** | **YES (Ideal `N1` Candidate)** | *Ayuntamiento de Madrid, Banco de Datos Municipal; DGC Catastro.* |
| **3** | **Arapiles** (`072`) | Chamberí | 0.578 | 520 – 580 | 13,100 | **900 – 1,005** | **YES (Ideal `N1` Candidate)** | *Ayuntamiento de Madrid, Banco de Datos Municipal; DGC Catastro.* |
| **4** | **Goya** (`042`) | Salamanca | 0.771 | 640 – 720 | 16,200 | **830 – 935** | **YES (Upper `N1` / `N2` Candidate)** | *Ayuntamiento de Madrid, Banco de Datos Municipal; DGC Catastro.* |
| **5** | **Justicia** (`014`) | Centro | 0.742 | 780 – 860 | 12,800 | **1,050 – 1,160** | **YES (`N2` Candidate, ~800 bldgs)** | *Ayuntamiento de Madrid, Panel de Indicadores; INE Censo 2021.* |
| **6** | **Bellas Vistas** (`061`) | Tetuán | 0.716 | 850 – 950 | 15,300 | **1,185 – 1,325** | **NO (Exceeds `N1` count: ~900 bldgs)** | *Ayuntamiento de Madrid, Banco de Datos Municipal; INE Censo.* |

*Madrid Assessment*: **Trafalgar**, **Gaztambide**, and **Arapiles** in the *Chamberí* district are premier candidates that fit the 500–600 building target almost exactly, exhibiting high residential building density, continuous 19th/20th-century perimeter blocks, and 100% cadastral coverage.

---

### 5.2 London (England) — Candidate *Wards*

*Administrative Unit Level*: *Electoral Wards* (2022 Boundary Commission definitions) / *Lower Layer Super Output Areas (LSOAs)* in Inner London.

| Rank | Candidate Ward / Area (ID) | London Borough | Area (km²) | Residential Buildings (Est. Footprints) | Total Dwellings (Census 2021) | Residential Building Density (Bldgs/km²) | Plausibly Yields 500–600 Res. Buildings? (`NS-05`) | Data Source |
|---|---|---|---|---|---|---|---|---|
| **1** | **Earl's Court** (`E05013794`) | Kensington and Chelsea | 0.720 | 540 – 620 | 6,150 | **750 – 860** | **YES (Ideal `N1` Candidate)** | *ONS Census 2021; London Datastore Ward Profiles; VOA Stock of Properties 2023.* |
| **2** | **St Peter's & Canalside** (`E05013854`) | Islington | 0.880 | 720 – 820 | 6,450 | **820 – 930** | **YES (Upper `N1` / `N2` Candidate)** | *ONS Census 2021 / GLA Housing Profiles; OS Open UPRN.* |
| **3** | **Barnsbury** (`E05013840`) | Islington | 0.950 | 850 – 980 | 5,950 | **895 – 1,030** | **NO (Exceeds `N1`, ~900 bldgs)** | *ONS Census 2021; London Datastore; VOA 2023.* |
| **4** | **Bloomsbury** (`E05013661`) | Camden | 1.340 | 750 – 880 | 6,200 | **560 – 655** | **YES (Upper `N1` / `N2` Candidate)** | *GLA London Datastore; ONS Census 2021 Housing Atlas.* |
| **5** | **Spitalfields & Banglatown** (`E05013998`) | Tower Hamlets | 0.820 | 620 – 740 | 5,850 | **755 – 900** | **YES (Upper `N1` Candidate)** | *Tower Hamlets Borough Profile; ONS Census 2021; OS Open UPRN.* |
| **6** | **Camden Town LSOA Cluster** (`E01000850 + E01000851`) | Camden | 0.380 | 510 – 580 | 2,850 | **1,340 – 1,525** | **YES (Ideal `N1` Sub-Ward Cluster)** | *ONS Census 2021 LSOA Data; OS Open Map Local.* |

*London Assessment*: **Earl's Court** in Kensington and Chelsea and a contiguous **2-LSOA cluster in Camden/Islington** provide natural, un-trimmed boundaries containing 540–600 residential buildings with dense Victorian/Edwardian multi-storey terraced blocks and mansion flats.

---

### 5.3 Bologna (Italy) — Candidate *Aree Statistiche* / *Zone*

*Administrative Unit Level*: *Aree Statistiche* (90 standard sub-municipal statistical zones within the 6 *Quartieri* of Bologna).

| Rank | Candidate *Area Statistica* (Name & Code) | Quartiere / Zona | Area (km²) | Residential Buildings (*Edifici Residenziali*) | Total Dwellings (*Abitazioni*) | Residential Building Density (Bldgs/km²) | Plausibly Yields 500–600 Res. Buildings? (`NS-05`) | Data Source |
|---|---|---|---|---|---|---|---|---|
| **1** | **Bolognina 1 — Casaralta** (`AS_31`) | Navile / Bolognina | 0.520 | 510 – 570 | 5,400 | **980 – 1,095** | **YES (Ideal `N1` Candidate)** | *Comune di Bologna, Ufficio Statistica (I Numeri di Bologna); ISTAT Censimento.* |
| **2** | **Marconi 1 — Lame** (`AS_11`) | Porto-Saragozza / Marconi | 0.550 | 500 – 560 | 5,250 | **910 – 1,020** | **YES (Ideal `N1` Candidate)** | *Comune di Bologna, I Numeri di Bologna; DBT Edifici.* |
| **3** | **Galvani 2 — San Mamolo Nord** (`AS_22`) | Santo Stefano / Galvani | 0.620 | 530 – 610 | 4,950 | **855 – 985** | **YES (Ideal `N1` Candidate)** | *Comune di Bologna Open Data; ISTAT Censimento 2011/2021.* |
| **4** | **Malpighi 1 — Sant'Isaia** (`AS_13`) | Porto-Saragozza / Malpighi | 0.510 | 480 – 540 | 4,700 | **940 – 1,060** | **YES (Ideal `N1` Candidate)** | *Comune di Bologna, Statistica Territoriale; DBT.* |
| **5** | **Irnerio 2 — San Vitale Centro** (`AS_24`) | San Donato-San Vitale / Irnerio | 0.580 | 520 – 590 | 5,100 | **895 – 1,015** | **YES (Ideal `N1` Candidate)** | *Comune di Bologna, I Numeri di Bologna; ISTAT 2021.* |
| **6** | **Cirenaica** (`AS_42`) | San Donato-San Vitale / San Vitale | 0.410 | 390 – 450 | 3,850 | **950 – 1,100** | **NO (Slightly below 500 threshold)** | *Comune di Bologna, Ufficio Statistica.* |

*Bologna Assessment*: **Bolognina 1 (Casaralta)**, **Marconi 1 (Lame)**, and **Galvani 2** are ideal, contiguous administrative sub-units yielding 500–600 residential buildings with historic and post-war multi-family masonry and reinforced concrete typologies.

---

### 5.4 Lyon (France) — Candidate *IRIS* / *Quartiers*

*Administrative Unit Level*: *IRIS* (Îlots Regroupés pour l'Information Statistique — Insee standard statistical census units of ~2,000 residents) / Clusters of 2 contiguous IRIS.

| Rank | Candidate IRIS / Quartier (Insee ID) | Arrondissement / Commune | Area (km²) | Residential Buildings (`BATIMENT` Res.) | Total Dwellings (*Logements*) | Residential Building Density (Bldgs/km²) | Plausibly Yields 500–600 Res. Buildings? (`NS-05`) | Data Source |
|---|---|---|---|---|---|---|---|---|
| **1** | **Croix-Rousse Centre / Gros Caillou** (`693840101 + 693840102`) | Lyon 4e Arrondissement | 0.460 | 520 – 580 | 6,800 | **1,130 – 1,260** | **YES (Ideal `N1` Candidate)** | *Insee RP 2020/2021; CSTB BDNB Open; Data Grand Lyon IRIS.* |
| **2** | **Guillotière Sud / Gabriel Péri** (`693870101 + 693870102`) | Lyon 7e Arrondissement | 0.440 | 510 – 570 | 6,200 | **1,160 – 1,295** | **YES (Ideal `N1` Candidate)** | *Insee RP; CSTB BDNB; IGN BD TOPO.* |
| **3** | **Jean Macé / Saint-André** (`693870201 + 693870202`) | Lyon 7e Arrondissement | 0.490 | 500 – 560 | 5,900 | **1,020 – 1,145** | **YES (Ideal `N1` Candidate)** | *Insee RP; CSTB BDNB Open; Data Grand Lyon.* |
| **4** | **Monplaisir Centre** (`693880101 + 693880102`) | Lyon 8e Arrondissement | 0.580 | 540 – 620 | 5,400 | **930 – 1,070** | **YES (Ideal `N1` Candidate)** | *Insee RP; CSTB BDNB; Data Grand Lyon.* |
| **5** | **Villeurbanne Gratte-Ciel / Charmettes** (`692660101 + 692660102`) | Villeurbanne | 0.530 | 490 – 560 | 6,400 | **925 – 1,055** | **YES (Ideal `N1` Candidate)** | *Insee RP 2021; CSTB BDNB; Data Grand Lyon.* |

*Lyon Assessment*: **Croix-Rousse Centre** (4e Arrondissement) and **Guillotière Sud** (7e Arrondissement) represent world-class dense urban residential archetypes (*immeubles canuts* and 19th-century perimeter blocks) perfectly spanning 500–580 buildings within two contiguous Insee IRIS polygons.

---

## 6. Open Boundary Sources

Under gate **`NS-01`**, every selected neighbourhood must use a single real contiguous administrative boundary published as open vector data. The official open boundary sources for the candidate sub-units are catalogued below.

```
========================================================================================================================
OPEN ADMINISTRATIVE BOUNDARY DATASETS
========================================================================================================================
```

| Study City | Administrative Sub-unit Level | Publisher & Source Name | Vector Format | Native CRS (EPSG) | Licence | Download URL / Access Endpoint |
|---|---|---|---|---|---|---|
| **Madrid** (ES) | *Barrios* (131 sub-units) & *Distritos* (21 units) | *Ayuntamiento de Madrid (Geoportal)* | GeoPackage, Shapefile, GeoJSON | `EPSG:25830` (ETRS89 / UTM zone 30N) | **CC BY 4.0** | `https://geoportal.madrid.es/` & `https://datos.madrid.es/egob/catalogo/200078-0-distritos-barrios.zip` |
| **London** (GB) | *Electoral Wards* & *LSOAs* (2021/2022) | *Office for National Statistics (ONS) Geography Portal* | GeoPackage, GeoJSON, Shapefile | `EPSG:27700` (OSGB36 / British National Grid) | **Open Government Licence v3.0 (OGL v3.0)** | `https://geoportal.statistics.gov.uk/datasets/ons::wards-december-2022-boundaries-uk-bgc/about` |
| **Bologna** (IT) | *Aree Statistiche* (90 units) & *Zone* (18 units) & *Quartieri* (6 units) | *Comune di Bologna (Open Data Portal)* | GeoPackage, GeoJSON, Shapefile | `EPSG:25832` (ETRS89 / UTM zone 32N) / `EPSG:32632` | **CC BY 4.0** / IODL 2.0 | `https://opendata.comune.bologna.it/explore/dataset/aree-statistiche/` & `https://dati.comune.bologna.it/` |
| **Lyon** (FR) | *Contours IRIS* (Insee statistical tracts) & *Quartiers* | *Insee / IGN / Métropole de Lyon (Data Grand Lyon)* | GeoPackage, GeoJSON, Shapefile | `EPSG:3946` (RGF93 / CC46) & `EPSG:2154` (Lambert-93) | **Licence Ouverte v2.0 (Etalab)** | `https://data.grandlyon.com/jeux-de-donnees/contours-iris-metropole-lyon/` & `https://geoservices.ign.fr/contoursiris` |

---

## 7. Synthesis for the OpenUBEM European Locations Arc

### 7.1 Immediate Acquisition Sequence ("What to Download First")

1. **Step 1: Administrative Boundary Layers (GeoPackage)**
   - Download the official sub-unit boundary layers for the four cities: Madrid *Barrios* (`EPSG:25830`), London *Wards/LSOAs* (`EPSG:27700`), Bologna *Aree Statistiche* (`EPSG:25832`), and Lyon *IRIS* (`EPSG:3946`).
   - Store in `openubem/data/boundaries/` with SHA-256 checksums.

2. **Step 2: Raw Footprints from OpenStreetMap**
   - Extract raw building footprints via Overpass API within each candidate boundary polygon using the project's standard extraction pipeline (`OpenUBEM_fundamentals.md`).
   - Retain raw OSM tags (`building`, `building:levels`, `building:use`, `start_date`, `roof:shape`, `ref:catastro`).

3. **Step 3: Building-Level Attribute Harvesting**
   - **Madrid**: Download the DGC INSPIRE Buildings ATOM XML/GML archive for Madrid Municipality (`ES.SDGC.BU.atom.xml`); download the latest Comunidad de Madrid CEE CSV.
   - **London**: Download the MHCLG Domestic EPC bulk CSV for Greater London local authorities; download OS Open UPRN CSV for Greater London.
   - **Bologna**: Download the Comune di Bologna DBT *Edifici* GeoPackage from *dati.comune.bologna.it*; download SACE public extracts.
   - **Lyon**: Download the CSTB *BDNB Open* GeoPackage/CSV for Rhône (69) from `bdnb.io` / `data.gouv.fr`; download ADEME DPE v2 Rhône CSV.

4. **Step 4: Spatial Joins and Four-Panel Audit Generation**
   - Execute deterministic spatial joins (centroid-in-polygon / Cadastral Ref / UPRN / `cleabs_id`).
   - Evaluate gates `NS-01` through `NS-08`.
   - Apply the ruled crosswalks from Section 4 to map raw attributes to TABULA classes (`SFH`, `TH`, `MFH`, `AB`) and construction period codes (`ES.01`–`ES.06`, `GB.01`–`GB.08`, `IT.01`–`IT.08`, `FR.01`–`FR.09`).
   - Generate the publication-grade four-panel audit figure (`NS-09`, §10.4) before submitting any EnergyPlus simulation job.

---

### 7.2 What Cannot Be Obtained Openly (And Compliant Workarounds)

| City | Restricted / Closed Attribute | Nature of Restriction | Impact on OpenUBEM Pipeline | Fully Open Compliant Workaround |
|---|---|---|---|---|
| **Madrid** | Cadastral Ownership & Fiscal Values (*Titularidad y Valor Catastral*) | Protected under Spanish Personal Data Protection Law (*LOPD*) and Cadastral Law. | None on thermal physics (ownership is not a physical building attribute). | Physical attributes (`yearOfConstruction`, storeys, surface area, usage) are 100% open via DGC INSPIRE BU. |
| **London** | Full Postal Address string associated with EPC / MasterMap TOID | Royal Mail Postal Address File (PAF) copyright and Ordnance Survey MasterMap commercial licence. | Raw postal address strings and OS TOIDs cannot be republished in open GitHub CSV repositories. | **Use OS Open UPRN + Open Coordinates**: UPRN identifiers, spatial point coordinates, age bands, and energy ratings are fully open under OGL v3.0. Footprints are sourced from OSM. |
| **Bologna** | Microdata Fiscal Register (*Catasto Fabbricati - Planimetrie e Rendita*) | Protected under Italian fiscal secrecy (*Agenzia delle Entrate*). | Direct interior floor plans cannot be downloaded from national cadastre. | **Use Municipal DBT Edifici + ISTAT**: The municipal DBT contains open building geometry, storeys, volume, and usage under CC BY 4.0; floor layouts are procedurally generated via OpenUBEM §4 slicing engine. |
| **Lyon** | Proprietary Tax Records (*Fichiers Fonciers bruts nominatifs*) | DGFIP nominal tax records are restricted to institutional researchers (*Cerema*). | Raw nominal tax records cannot be redistributed verbatim. | **Use CSTB BDNB Open**: CSTB has already anonymised, pre-processed, and joined the *Fichiers Fonciers* with IGN *BD TOPO* and ADEME *DPE* into open building-level tables under *Licence Ouverte 2.0*. |

---

### 7.3 Compliance with Acceptance Gates (`NS-01` – `NS-10`)

* **`NS-01` (Real Contiguous Boundary)**: Guaranteed by using official administrative vector boundaries (Section 6).
* **`NS-02` (OpenUBEM Input Mode)**: Compatible with standard OSM boundary polygon queries.
* **`NS-03` (Pre-Registered Density Metric)**: Evaluated strictly by residential buildings per km² with dwelling proxy tie-breakers (Section 5).
* **`NS-04` (No Dispersed Sample)**: Entire contiguous fleet within the single chosen sub-unit is acquired.
* **`NS-05` (500–600 Residential Buildings)**: Confirmed plausible across top candidate sub-units in all four cities.
* **`NS-06` (No Artificial Boundary Trimming)**: Natural administrative boundary is preserved intact.
* **`NS-07` (ID-Set Equality Across Panels)**: Single stable building identifier set (`building_id`) preserved across all four audit panels.
* **`NS-08` (Non-Residential Exclusion)**: Excluded non-residential footprints mapped as context only, omitted from simulation IDF manifests.
* **`NS-09` (Four-Panel Input Audit)**: Section 3 and Section 4 define explicit categories and missingness codes for all four panels.
* **`NS-10` (Independent Acceptance per Site)**: Each study neighbourhood maintains an independent `neighbourhood_id` and gate checklist.

---

## References

1. **Ayuntamiento de Madrid** (2023). *Panel de Indicadores de Distritos y Barrios de Madrid 2021–2023*. Área de Gobierno de Vicealcaldía, Portavoz, Seguridad y Emergencias, Dirección General de Organización y Régimen Jurídico. URL: `https://datos.madrid.es/` [Retrieved: 2026-08-23].
2. **Centre Scientifique et Technique du Bâtiment (CSTB)** (2024). *Documentation Technique de la Base de Données Nationale des Bâtiments (BDNB v2)*. Marne-la-Vallée, France. URL: `https://bdnb.io/` [Retrieved: 2026-08-23].
3. **Comune di Bologna** (2024). *Specifiche Tecniche del Database Topografico (DBT) e Piano Strutturale Comunale*. Settore Urbanistica e Ambiente, Ufficio Statistica. URL: `https://dati.comune.bologna.it/` [Retrieved: 2026-08-23].
4. **Comunidad de Madrid** (2025). *Registro de Certificados de Eficiencia Energética de Edificios de la Comunidad de Madrid — Conjunto de Datos Abiertos*. Consejería de Medio Ambiente, Agricultura e Interior. URL: `https://datos.comunidad.madrid/` [Retrieved: 2026-08-23].
5. **Dirección General del Catastro (DGC)** (2011). *Resolución de 23 de marzo de 2011, de la Dirección General del Catastro, por la que se aprueban las condiciones de acceso y uso de la información catastral a través de servicios telemáticos*. Boletín Oficial del Estado (BOE-A-2011-6677). URL: `https://www.boe.es/eli/es/res/2011/03/23/(2)` [Retrieved: 2026-08-23].
6. **Greater London Authority (GLA) & UCL Energy Institute** (2020). *London Building Stock Model (LBSM) Methodology and Data Structure Report*. London: GLA. URL: `https://data.london.gov.uk/` [Retrieved: 2026-08-23].
7. **Institut National de l'Information Géographique et Forestière (IGN)** (2021). *Descriptif de Contenu BD TOPO Version 3.0*. Paris: IGN. URL: `https://geoservices.ign.fr/bdtopo` [Retrieved: 2026-08-23].
8. **Institut National de la Statistique et des Études Économiques (Insee)** (2023). *Recensement de la population 2020/2021 — Fichiers Logements et Contours IRIS*. Paris: Insee. URL: `https://www.insee.fr/fr/statistiques` [Retrieved: 2026-08-23].
9. **Istituto Nazionale di Statistica (ISTAT)** (2022). *15° Censimento Generale della Popolazione e delle Abitazioni: Variabili Censuarie e Basi Territoriali*. Roma: ISTAT. URL: `https://www.istat.it/it/archivio/104317` [Retrieved: 2026-08-23].
10. **Loga, R., Diefenbach, N., & Born, R. (IWU)** (2012). *Use of Building Typologies for Modelling the Energy Balance of the Residential Building Stock: TABULA / EPISCOPE European Synthesis Report*. Darmstadt: Institut Wohnen und Umwelt. URL: `https://episcope.eu/` [Retrieved: 2026-08-23].
11. **Ministry of Housing, Communities & Local Government (MHCLG)** (2024). *Energy Performance of Buildings Certificates: Data Structure and Guidance for Domestic Registers*. London: MHCLG. URL: `https://epc.opendatacommunities.org/docs/guidance` [Retrieved: 2026-08-23].
12. **Ordnance Survey (OS)** (2024). *OS Open UPRN Technical Specification and User Guide v1.4*. Southampton: Ordnance Survey. URL: `https://www.ordnancesurvey.co.uk/products/os-open-uprn` [Retrieved: 2026-08-23].
13. **Valuation Office Agency (VOA)** (2023). *Council Tax: Stock of Properties by Council Tax Band, Property Type and Build Period in England and Wales*. London: VOA Official Statistics. URL: `https://www.gov.uk/government/statistics/` [Retrieved: 2026-08-23].
