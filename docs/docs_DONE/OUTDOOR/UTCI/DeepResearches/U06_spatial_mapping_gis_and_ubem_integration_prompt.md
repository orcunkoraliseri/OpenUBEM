# Deep-Research Prompt U06 — SPATIAL GIS MAPPING, UBEM INTEGRATION & HEAT MITIGATION

> SCOPE GUARD — READ FIRST. This prompt examines **spatial GIS raster/mesh mapping, integration into OpenUBEM's building-stock pipeline, and urban heat mitigation modeling**. It covers high-resolution thermal comfort mapping (as shown in `1784462193769.jpg`), coupling building envelope surface heat rejection with outdoor microclimates, GIS raster data formats, population heat exposure modeling, and evaluating urban heat mitigation strategies (cool roofs, urban forestry, shade structures). Do NOT cover biometeorological core theory (`U01`), non-radiant scaling (`U02`), or manual polynomial equations (`U05`). See `00_README_utci_prompt_set.md`.

---

## What this document is

A spatial GIS & UBEM subsystem integration specification. As depicted in `docs/examples/UTCI/1784462193769.jpg`, the ultimate value of UTCI analysis lies in generating spatial microclimate field maps overlaid on building footprints, tree canopies, and pedestrian walkways. This prompt details how OpenUBEM can export high-resolution spatial UTCI grids, couple indoor energy performance with outdoor microclimates, and evaluate the effectiveness of municipal heat mitigation strategies.

## Role

GIS spatial analyst & UBEM systems architect. Ground spatial discretization methods, urban heat island (UHI) mitigation physics, and building-microclimate feedback loops in peer-reviewed literature (Santamouris 2014; Akbari et al. 2016; Taleghani 2018; Krayenhoff et al. 2018; Middel et al. 2014, 2019).

## Why this matters (so you scope correctly)

Urban buildings do not exist in isolation: their air conditioning units reject heat into street canyons, and their dark facade materials absorb shortwave radiation, exacerbating outdoor heat stress. Conversely, outdoor microclimates dictate HVAC cooling loads and occupant thermal comfort. By integrating spatial UTCI mapping into OpenUBEM, urban designers can quantify how building massing, retrofits, and urban greening directly alleviate pedestrian heat stress ($26-32^\circ\text{C}$ Moderate vs. $>46^\circ\text{C}$ Extreme).

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — GIS Spatial Data Formats for Microclimate & UTCI Grids

| Data Format | Geometry Type | Spatial Resolution Capabilities | Software Compatibility (QGIS, ArcGIS, OpenUBEM) | File Size / Memory Efficiency | Recommended Use Case | Source |
|---|---|---|---|---|---|---|
| GeoTIFF Raster | Regular 2D Grid ($1 - 5\text{ m}$) | Continuous spatial fields ($T_a, v, MRT, \text{UTCI}$) | Universal (QGIS, GDAL, Rasterio, SOLWEIG) | High (GeoTIFF compression) | Primary spatial output format |  |
| Vector GeoJSON / Geopackage | Polygons / Meshes | Point grids, street segments, building footprints | Universal (PostGIS, GeoPandas) | Moderate | Pedestrian street network comfort |  |
| VTK / NetCDF | 3D Voxel Mesh | Full 3D atmospheric volume ($x, y, z, t$) | ParaView, ENVI-met, PALM-4U | Very Large | Advanced 3D CFD visualization |  |
| COG (Cloud Optimized GeoTIFF) | Web Raster Grid | Multi-resolution pyramid streaming | Web GIS / Mapbox / Leaflet | Optimized for web streaming | Interactive web dashboards |  |

### Table 2 — Building-Stock Feedback & Outdoor Heat Rejection Mechanisms

| Heat Exchange Mechanism | UBEM Source Output | Impact on Street Canyon Microclimate | Impact on Outdoor UTCI | Mitigation Strategy | Source |
|---|---|---|---|---|---|
| HVAC Heat Rejection | Condenser sensible & latent heat release | Increases canyon air temp ($T_a$) by $+1.0\text{ to }+3.0^\circ\text{C}$ at night | Elevates nighttime UTCI | Water-cooled condensers, thermal storage | Santamouris 2014 |
| Wall Surface Heat Release | Envelope surface temp ($T_{wall}$) via EnergyPlus | High longwave emission ($L_{wall}$) during late afternoon | Increases afternoon $T_{mrt}$ by $+5\text{ to }+15^\circ\text{C}$ | Cool wall coatings, green facades |  |
| Pavement Heat Absorption | Ground surface temp ($T_{grd}$) & albedo ($\alpha$) | Massive longwave emission ($L_{grd}$) + sensible heat flux | Dominant driver of $T_{mrt}$ in open plazas | Permeable & cool pavements ($\alpha > 0.40$) | Akbari et al. 2016 |

### Table 3 — Urban Heat Mitigation Strategies & Simulated UTCI Efficacy

| Mitigation Strategy | Physical Parameter Shift | Impact on $T_a$ ($^\circ\text{C}$) | Impact on $T_{mrt}$ ($^\circ\text{C}$) | Impact on Outdoor UTCI ($^\circ\text{C}$) | Primary Stress Category Shift | Source |
|---|---|---|---|---|---|---|
| Urban Tree Canopy Expansion | Increases Shade ($\tau = 0.15$), LAI $\uparrow$ | $-0.5\text{ to }-1.5^\circ\text{C}$ | $-15.0\text{ to }-25.0^\circ\text{C}$ | $-4.0\text{ to }-10.0^\circ\text{C}$ | Extreme ($>46^\circ\text{C}$) $\to$ Strong ($32-38^\circ\text{C}$) | Taleghani 2018 |
| Cool Roofs & Cool Pavements | Increases Albedo ($\alpha: 0.15 \to 0.60$) | $-0.5\text{ to }-2.0^\circ\text{C}$ | $+2.0\text{ to }+8.0^\circ\text{C}$ (Ground reflection) | $-0.5\text{ to }+2.0^\circ\text{C}$ (Net radiation tradeoff) | Moderate shift | Akbari et al. 2016 |
| PV Canopy / Shade Sails | Solar obstruction over plazas | $-0.2\text{ to }-0.8^\circ\text{C}$ | $-20.0\text{ to }-30.0^\circ\text{C}$ | $-6.0\text{ to }-12.0^\circ\text{C}$ | Very Strong $\to$ Moderate | Middel et al. 2014 |
| High-Albedo Building Facades | Wall Albedo ($\alpha_{wall}: 0.2 \to 0.7$) | $-0.2\text{ to }-0.5^\circ\text{C}$ | $+5.0\text{ to }+12.0^\circ\text{C}$ (Reflected radiation to street) | $+1.0\text{ to }+4.0^\circ\text{C}$ (Can worsen pedestrian stress!) | Shifts toward higher heat stress | Chatzidimitriou & Yannas |

### Table 4 — Population Heat Exposure & Spatial Vulnerability Metrics

| Exposure Metric | Mathematical Formulation | Input Data Required | Application in Municipal Planning | Source |
|---|---|---|---|---|
| Person-Hours of Extreme Heat | $\sum \text{People}_i \times \text{Hours}(\text{UTCI}_i > 46^\circ\text{C})$ | Spatial UTCI raster + Pedestrian movement / Census | Quantifying heat mortality risk |  |
| Cumulative Thermal Stress | $\int (\text{UTCI}(t) - 26^\circ\text{C}) dt \text{ for } \text{UTCI} > 26^\circ\text{C}$ | Hourly UTCI spatial series | Heat wave severity index |  |
| Vulnerable Subgroup Exposure | Overlay of UTCI map with Elderly / Low-Income GIS layers | Socio-demographic GIS rasters + UTCI map | Climate equity & intervention targeting |  |

---

## Part C — Synthesis (Spatial Pipeline & Mitigation Architecture for OpenUBEM)

Give:
1. A complete architectural specification for OpenUBEM's spatial export module (GeoTIFF generation, color maps matching `1784462193769.jpg`, vector overlays).
2. A critical evaluation of the "Cool Pavement Tradeoff" (where high albedo lowers air temperature but increases reflected shortwave radiation onto pedestrians, potentially increasing daytime UTCI).
3. A step-by-step workflow for integrating spatial UTCI heat exposure reporting into OpenUBEM's municipal urban design suite.

## Output Format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Include GIS processing code patterns using GeoPandas, Rasterio, or QGIS python scripts (`pyqgis`).
4. **"Confidence and caveats":** address spatial resolution tradeoffs (e.g., $1\text{ m}$ vs. $10\text{ m}$ grids) and dynamic pedestrian movement assumptions.
5. **Reference list** — complete citations with DOIs.

## Hard Requirements

- **Populate every cell in Tables 1–4.**
- **Analyze the high-albedo radiation tradeoff explicitly in Table 3 and Part C.**
- **Provide clear GIS raster export standards matching `1784462193769.jpg`.**
