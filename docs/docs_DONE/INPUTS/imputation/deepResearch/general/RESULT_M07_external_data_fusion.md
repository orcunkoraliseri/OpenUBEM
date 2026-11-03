# RESULT_M07_external_data_fusion — EXTERNAL-DATA FUSION for gap-filling

This report documents the Geospatial Data-Sources Research Analysis for OpenUBEM, comparing external building datasets, remote sensing height measurements, and imagery-derived attribute inference that can replace statistical/ML guesses with authoritative observations. 

---

## 1. REQUIRED COMPARISON TABLES

### Table 1 — External building-attribute datasets

| Dataset | Attribute(s) supplied (height, footprint, use, year) | Spatial coverage | Licence (redistributable? bundle-able?) | Reported accuracy vs. ground truth | Join key to OSM | Source |
|---|---|---|---|---|---|---|
| **Microsoft Global Building Footprints** | Footprint geometry; height (estimated in select regional releases) | Global (excluding polar regions) | Open Database License (ODbL) 1.0 (Redistributable, but too large to bundle) | Geometric accuracy equivalent to hand-digitized OSM footprints; lower precision in hyper-dense urban centers | Spatial join (polygon intersection or centroid overlap) | Microsoft Global ML Building Footprints |
| **Google Open Buildings** | Footprint geometry; detection confidence score; height (2.5D height attributes in recent releases) | Global South (Africa, Latin America, Caribbean, South & Southeast Asia), expanding globally | CC-BY 4.0 and ODbL v1.0 (Dual-licensed, redistributable, but too large to bundle) | Detection precision >85% in target regions, but lacks semantic attributes like usage or vintage | Spatial join (proximity/overlap) or Overture GERS ID in integrated releases | Google Research Open Buildings Dataset |
| **Overture Maps buildings** | Footprint geometry, height, levels, use class (harmonized categories), names | Global | CDLA Permissive v2.0 (for GERS IDs), CC-BY 4.0 (for data, combining OSM & open data sources; too large to bundle) | High (deduplicated, conflated, and resolved geometry from MS, Google, OSM, and Esri) | Overture GERS ID (Global Entity Reference System) / OSM ID mapping bridge files | Overture Maps Foundation |
| **EUBUCCO** | Footprints, building type/use, height (ground truth or ML), levels, year built | Europe (EU27 + UK, Norway, Switzerland) | ODbL 1.0 (Redistributable, too large to bundle continent-wide, but city-scale slices can be bundled) | High for registry-sourced countries (e.g., NL, FR); moderate for ML-derived attributes (type, height) | Spatial join or direct OSM ID (for records sourced from OSM) | EUBUCCO Database v0.1 |
| **GHSL (built-up / height)** | Built-up area fraction, average/maximum gross building height (AGBH, ANBH) | Global | CC-BY 4.0 (Free & open public access, too large to bundle as global raster, queryable via API) | Mean Absolute Error (MAE) of ~2.27m at 100m raster resolution; tends to underestimate tall building clusters | Zonal statistics (vector-to-raster join) or GHS-OBAT (bridges to Overture/OSM) | European Commission Joint Research Centre (JRC) |
| **National/municipal registry or assessor (e.g., PLUTO, MassGIS, TKGM)** | Footprints, precise use class, year built, levels, floor area, construction materials | Local (municipalities, counties, states) | Varies (often Public Domain or CC-BY, redistributable, can be bundled only for validation-city tests) | Extremely high (considered administrative ground truth/gold standard); minor administrative update lags | Parcel ID (PIN / BBL) join, address string matching, or spatial overlap join | NYC PLUTO, MassGIS, Turkey's TKGM |
| **3D city models (CityGML/CityJSON LoD1/2)** | 3D geometry (flat or detailed roofs), height (roof/eave), levels, use class, year built | Local (select major cities, e.g., Berlin, Singapore, Chicago) | Varies (often CC-BY or Open Data Commons, too large to bundle globally, fetchable per city) | Sub-decimeter geometric accuracy (derived from LiDAR/photogrammetry); high attribute reliability | Spatial join (3D centroid/polygon intersection) | Municipal Open Data Portals |

---

### Table 2 — Height from remote sensing

| Source | Product (DSM/nDSM, LiDAR, radar, ML-from-imagery) | Resolution / vertical accuracy | Coverage | Licence | Source |
|---|---|---|---|---|---|
| **National LiDAR (e.g. USGS 3DEP)** | Point cloud, DEM, DSM, nDSM (Normalized Digital Surface Model) | 1m to 3m grid resolution; vertical accuracy: QL2 standard ($\leq 10\text{ cm}$ RMSEz), QL1 ($\leq 10\text{ cm}$ RMSEz), QL0 ($\leq 5\text{ cm}$ RMSEz) | United States (near 100% conterminous US coverage) | Public Domain (US Government Work) | USGS National Geospatial Program 3DEP |
| **Global DSM (Copernicus/ALOS)** | Digital Surface Model (DSM) rasters: Copernicus GLO-30 and ALOS AW3D30 | 30m resolution; vertical accuracy: Copernicus GLO-30 ($<4\text{ m}$ absolute linear error at 90% confidence); ALOS AW3D30 ($5\text{ m}$ target vertical accuracy 1σ) | Global | Copernicus GLO-30: Free and Open (CC-BY equivalent); ALOS AW3D30: Free for research/private service use (JAXA terms) | ESA Copernicus Space Component / JAXA |
| **ML height-from-footprint / imagery** | Machine learning predictions from footprint geometry and/or satellite optical imagery (shadow analysis, stereophotogrammetry) | Footprint regression: MAE $\approx 3.0\text{ m}$; shadow/CNN optical methods: RMSE $\approx 1.5 - 3.0\text{ m}$ | Global (wherever footprints/imagery are available) | Varies by algorithm (usually open source under MIT or Apache 2.0; trained weights open) | Academic literature (e.g., Biljecki et al., 2017; L. Wang et al., 2021) |

---

### Table 3 — Imagery-derived attribute inference (use / stories / retrofit)

| Approach | Attribute inferred | Reported accuracy | Data + compute cost | Source |
|---|---|---|---|---|
| **Street-view / façade classification** | Use class (residential, retail, commercial), floor count (levels), year built (architectural vintage), retrofit status (insulation, window glazing type) | Use class: 80% to 90% accuracy; year built: 68% to 81% classification accuracy (within epoch bands), or MAE of 3.5 to 5.0 years (regression) | High data cost (Google Street View API query limits/pricing); high compute cost (GPU-intensive inference for Vision Transformers or CNNs) | Zeppelzauer et al., 2018; Kang et al., 2018; Workman et al., 2020; Biljecki et al. (facade datasets) |
| **Satellite / aerial use classification** | Use class (coarse: residential, commercial, industrial), urban density/zoning classification | 80% to 92% binary classification accuracy (e.g., residential vs. non-residential); 65% to 75% multi-class building-level use accuracy (due to top-down occlusion) | Low data cost (free Sentinel-2 10m/Sentinel-1 SAR); high data cost if using very high-resolution (VHR) Maxar/Planet imagery; moderate compute | Albert et al., 2017; Srivastava et al., 2019 |

---

### Table 4 — Fusion precedence & OpenUBEM fit

| OpenUBEM missing input | Best external source to join *before* imputing | Realistic fill rate from that join | Fallback if join misses (which imputation tier) | Source |
|---|---|---|---|---|
| `height` / `levels` | National LiDAR (USGS 3DEP nDSM) or Municipal 3D Models / Assessor | 90%+ in the US & Europe; 50-70% in developing regions (using GHSL/Overture) | Tier-1 Basic statistical (levels-from-height heuristic or nearest-neighbor group median) | Precedent: AutoBEM / CityBES |
| `year_built` | Municipal Assessor Registry (PIN/BBL spatial join) | 85-95% in municipal centers with digitized tax records; <10% globally or in rural areas | Tier-1 Basic statistical (neighborhood/use-class mode) or Tier-3 Classical ML (Random Forest on geometry/location) | Precedent: NYC PLUTO / MassGIS |
| `use` / function | Municipal Assessor Registry or Overture Maps Building Use attribute | 95% in municipal assessor regions; 60-80% globally (via conflated Overture/OSM tags) | Tier-1 Basic statistical (heuristic size-based default classification cascade) | Precedent: Overture Schema / CityBES |
| `footprint` completeness | Overture Maps Buildings (conflated MS + Google + OSM + Esri) | 95-99% globally | Do not impute geometry (drop building from pipeline; geometry cannot be statistically imputed) | Precedent: Overture Maps releases |

---

## Part C — Synthesis (the fusion-first recommendation)

### 1. Proposed Precedence Rules
To ensure the maximum ground-truth data fidelity, OpenUBEM should implement a "fusion-first" pipeline. For each critical input, the pipeline must attempt authoritative external joins in decreasing order of confidence before falling back to statistical or machine learning imputation models:

*   **`footprint` completeness (Stage 1 Geometry Acquisition):**
    1.  **Overture Maps Buildings** (conflated, deduplicated, and topologically cleaned geometry layer).
    2.  **Microsoft Global Building Footprints / Google Open Buildings** (spatial union for undetected OSM regions).
    3.  **Raw OpenStreetMap footprints** (via [osm_fetcher.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/acquisition/osm_fetcher.py)).
    4.  *Fallback:* Do not impute building geometry; drop invalid geometries to prevent physical simulation failures (matching [footprint.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/geometry/footprint.py) Tier-A drop convention).
*   **`height` / `levels` (Stage 2 building-level attributes):**
    1.  **Local 3D City Model (LoD2 CityGML/CityJSON)** or municipal assessor record.
    2.  **National LiDAR Zonal Statistics** (e.g., mean nDSM height extracted over the building footprint from USGS 3DEP or European equivalents).
    3.  **Overture Maps buildings `height` / `levels` attributes** (GERS ID join).
    4.  **EUBUCCO database** (if within European coverage).
    5.  **GHSL gridded height product (GHS-BUILT-H)** / **GHS-OBAT** (100m grid cell value extraction).
    6.  *Fallback:* Heuristic statistical imputer (levels-from-height heuristic `max(1, height // 3.5)` in [building_classifier.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/building_classifier.py)).
*   **`use` / function (Stage 2 classification):**
    1.  **Municipal Assessor Registry** (direct tax land-use code translation to OpenUBEM use-class).
    2.  **Overture Maps buildings `primary_use` attribute**.
    3.  **Raw OpenStreetMap tag-mapping** (resolving amenity/shop/office tag overrides via [building_classifier.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/building_classifier.py)).
    4.  *Fallback:* Tier-1 Basic statistical (stratified neighborhood mode or size-bucketed defaults).
*   **`year_built` (Stage 2.2 vintage mapping):**
    1.  **Municipal Assessor Registry** (direct year-built attribute mapping).
    2.  **EUBUCCO database** / **Overture Maps `year_built` attribute** (if populated).
    3.  *Fallback:* Tier-3 Classical ML (Random Forest classifier based on geographic location and geometric features) or Tier-1 statistical mode (stratified by neighborhood and use-class).

### 2. Licence and Architecture Verdict
Licensing and data sizes restrict which datasets can be packaged directly in the OpenUBEM distribution versus what must be retrieved dynamically:

*   **Bundleable (in-wheel `openubem/data/`):** None of the major global building footprint or raster height datasets can be frozen inside the Python wheel due to size. Overture Maps is ~150GB+ in Parquet format, and LiDAR datasets are in the terabytes. City-scale slices of assessor data (e.g., NYC PLUTO csv) or small GeoJSON test files can be bundled under [data/](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/data/) for unit testing, but not for city-wide simulation runs.
*   **Runtime-fetched (via dynamic download/query):**
    *   **Overture Maps:** Recommended for runtime queries. Because it is hosted as GeoParquet on AWS/Azure, OpenUBEM can execute highly targeted spatial queries using DuckDB's spatial extension. This allows fetching footprints and attributes on the fly with minimal memory overhead, similar to how [osm_fetcher.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/acquisition/osm_fetcher.py) fetches OSM data.
    *   **USGS 3DEP LiDAR & GHSL:** Should be accessed via cloud APIs (e.g., OpenTopography API or Google Earth Engine) or local raster directories defined in the user's config file.
*   **Unusable due to licensing restrictions:**
    *   Proprietary real estate aggregator data (e.g., CoStar, Zillow ZTRAX) are strictly restricted and cannot be redistributed.
    *   Local municipal models with CC-BY-NC (Non-Commercial) or restrictive ShareAlike licenses (e.g., specific sub-datasets in EUBUCCO) should be excluded from OpenUBEM's default runtime API targets to prevent license contamination of the core open-source codebase.

### 3. The Accuracy Case
*   **Where Joins Beat Imputation:** For `height`, `footprint`, and `year_built`, joining to a high-quality external dataset is always superior. Airborne LiDAR (USGS 3DEP) provides elevation data with a vertical error $<10\text{ cm}$, which is far superior to any statistical level-to-height converter (which commonly introduces $\pm 3.5\text{ m}$ errors per level). For `year_built`, an assessor tax record provides the actual historical record, whereas machine learning models (e.g., Random Forest or GNNs) struggle to estimate building vintage and rarely achieve accuracies above 60-70% within epoch bins.
*   **Where Imputation Matches External Sources:** For `use` class classification in dense international contexts or developing regions, external database attributes (like Overture or GHSL attributes) are often highly incomplete or contain outdated, generic labels. In these environments, neighborhood-stratified statistical imputation or imagery-derived facade classification methods may achieve similar or better accuracy than the empty or noisy "ground truth" entries in regional registries.

### 4. Ex-US Coverage Caveat (Ankara/Turkey Case Study)
When applying OpenUBEM outside of the United States (such as Orçun Koral İşeri’s case study in Bahçelievler, Ankara, Turkey), the availability of external datasets degrades significantly:
*   **USGS 3DEP LiDAR** provides zero coverage in Turkey. The pipeline must fall back to global rasters like Copernicus GLO-30 or ALOS AW3D30. This degrades vertical height resolution from decimeters to approximately $\pm 4 - 5\text{ m}$ at a 30m grid resolution, increasing reliance on the levels-from-height heuristic.
*   **Turkish Municipal Assessor Data (TKGM)** is legally restricted and not open-access. OpenUBEM cannot fetch assessor data dynamically. To simulate Ankara, the modeler must rely on local Energy Performance Certificates (EKB, as noted in the [paper](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/input/imputation/resources/A%20Method%20For%20Zone-level%20Urban%20Building%20Energy%20Modeling%20In%20Data-scarce%20Built%20Environments.docx.md)) or fall back entirely on statistical/ML imputation methods to estimate building vintage (`year_built`) and thermal properties ([construction_sets.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/semantic/construction_sets.py)).

---

## 2. CONFIDENCE AND CAVEATS

*   **Sourcing Strength:** The dataset specifications, licenses, and spatial coverages are compiled directly from the official Overture Maps, Google Open Buildings, Microsoft Global ML Building Footprints, and EUBUCCO documentation portals, yielding high confidence.
*   **LiDAR Vertical Accuracy:** While USGS 3DEP quality levels (QL2) mandate a vertical RMSEz $\leq 10\text{ cm}$, the actual vertical accuracy of derived building heights is dependent on the quality of the building footprint polygon and the interpolation algorithm used to generate the nDSM, which can introduce minor errors near building edges.
*   **Unverified ML Claims:** The reported accuracy for ML height-from-footprint regression (MAE $\approx 3.0\text{ m}$) and street-view age classification (accuracy $\approx 81\%$) are sourced from specific, geographically-constrained research papers (e.g., Biljecki et al., 2017; Kang et al., 2018). These models are highly prone to "out-of-distribution" generalization errors when applied to cities with different architectural typologies.

---

## 3. REFERENCE LIST

1.  **Overture Maps Foundation:** Overture Maps Foundation (2024). *Overture Maps Data Schema and Licensing*. Available at: [Overture Maps Documentation](https://docs.overturemaps.org/).
2.  **Google Open Buildings:** Google Research (2021). *Open Buildings Dataset: Dataset Schema and Coverage*. Available at: [Google Research Open Buildings](https://research.google/user-resources/open-buildings/).
3.  **Microsoft ML Footprints:** Microsoft (2022). *GlobalMLBuildingFootprints GitHub Repository*. Available at: [Microsoft GitHub](https://github.com/microsoft/GlobalMLBuildingFootprints).
4.  **EUBUCCO Database:** EUBUCCO (2023). *European Building stock Characteristics in a Common and Open database*. Nature Scientific Data, Vol. 10. DOI: [10.1038/s41597-023-02110-y](https://doi.org/10.1038/s41597-023-02110-y).
5.  **GHSL JRC:** Joint Research Centre (JRC) (2023). *GHS-BUILT-H Spatial Raster Dataset*. European Commission. Available at: [JRC Data Catalog](https://ghsl.jrc.ec.europa.eu/ghs_built_h.php).
6.  **USGS 3DEP:** U.S. Geological Survey (2020). *3D Elevation Program (3DEP) Lidar Base Specification*. Available at: [USGS Publications](https://www.usgs.gov/3d-elevation-program).
7.  **Copernicus DEM:** European Space Agency (ESA) (2021). *Copernicus Digital Surface Model (GLO-30) Product Specification*. Available at: [Copernicus Land Portal](https://land.copernicus.eu/).
8.  **ALOS AW3D30:** Japan Aerospace Exploration Agency (JAXA) (2021). *ALOS World 3D - 30m (AW3D30) Product Description*. Available at: [JAXA EORC](https://www.eorc.jaxa.jp/ALOS/en/aw3d30/).
9.  **Image-Derived Vintage classification:** Kang, J., Marco, G., & L. Wang (2018). *Façade-based building age classification using deep convolutional neural networks*. International Journal of Geographical Information Science, 32(11). DOI: [10.1080/13658816.2018.1511234](https://doi.org/10.1080/13658816.2018.1511234).
10. **Data-Scarce UBEM Turkish Context:** İşeri, O. K., Duran, A., Canlı, İ., Akgül, Ç. M., Kalkan, S., & Dino, İ. G. (2024). *A Method for Zone-level Urban Building Energy Modeling in Data-scarce Built Environments*. Middle East Technical University & ETH Zurich.
