# RESULT_V02: Peer-Tool 3D Viewer Teardown (How Shipped UBEM and City Tools Build Interactive 3D)

This document provides a detailed, sourced, tool-by-tool analysis of how established Urban Building Energy Modeling (UBEM), city-energy, and geospatial visualization platforms turn simulated building models and energy results into interactive 3D web experiences. It serves as a benchmark and blueprint for designing OpenUBEM's own interactive 3D viewer MVP, identifying industry-standard patterns and ensuring compatibility with OpenUBEM's Python-based, open-source, and self-contained output constraints.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Stack & Data: WebGL Engines, Geometry Formats, and Georeferencing

| Tool | Interactive 3D web viewer? (or static/2D only) | Rendering stack (Cesium / deck.gl / MapLibre / three.js / engine) | Geometry data it renders (footprint-extrude / CityGML / mesh / IDF) | Geo-referenced on a basemap? | Source |
|---|---|---|---|---|---|
| **ubem.io** | Yes | Mapbox GL JS (with deck.gl layer integrations) | Footprint-extrude (vertical prism extrusion of GeoJSON/vector footprint polygons based on height/storey attributes) | Yes (dynamic Mapbox base map) | Ang et al. (2022) *SCS*; UBEM.io Live Platform |
| **CEA (City Energy Analyst)** | Yes | Plotly.js / Mapbox GL JS (embedded in Python dashboard views) | Footprint-extrude (2D GeoJSON footprints extruded in 3D in Plotly/Mapbox) | Yes (dynamic OpenStreetMap/Mapbox base map) | Fonseca et al. (2016) *RCR*; CEA Documentation |
| **UMI** | No (visualizes in desktop CAD only; web dashboard is 2D charts and maps) | Rhinoceros 3D native OpenGL engine | Rhino BREP meshes (detailed 3D CAD geometries) and SQLite database files | Yes (within Rhino CAD GIS coordinate frame) | Dogan & Reinhart (2013) *BS2013*; UMI project site |
| **Torino-3d-heat-mapping** | Yes | CesiumJS / WebGL | 3D Tiles (binary `.b3dm` mesh packages containing building envelopes) | Yes (WGS84 ellipsoid globe with satellite/OSM basemap) | fereshtehsabeghi/Torino-3d-heat-mapping GitHub; Sabeghi et al. (2021) *JBE* |
| **3DCityDB web-map-client / Cesium** | Yes | CesiumJS / WebGL | OGC 3D Tiles (B3DM/I3DM payloads) and CityGML XML datasets | Yes (WGS84 globe canvas) | Chatziioannou et al. (2018) *ISPRS*; 3DCityDB Developer Docs |
| **kepler.gl / deck.gl** | Yes | deck.gl (luma.gl WebGL engine wrapper) + Mapbox GL | Footprint-extrude (GPU-accelerated vertical extrusion of 2D GeoJSON polygon inputs) | Yes (Web Mercator projection maps) | vis.gl deck.gl & Kepler.gl API Reference Docs |
| **MapLibre / Mapbox GL (energy demos)** | Yes | MapLibre GL JS / Mapbox GL JS | Footprint-extrude (extruded GeoJSON/Vector Tile polygons) | Yes (Web Mercator projection maps) | MapLibre GL JS Documentation |
| **ArcGIS Urban / ArcGIS JS** | Yes | ArcGIS API for JavaScript (WebGL-based) | Esri Scene Layers (I3S format) and Multipatch 3D features | Yes (native Esri global or local scenes) | Esri ArcGIS Urban Documentation |
| **Speckle** | Yes | Custom Speckle Viewer engine built on three.js | Speckle Object Model (serialized JSON meshes, lines, and CAD components) | No (uses local Cartesian metres by default; coordinates can align with GIS) | Speckle Developer Guide & GitHub repositories |
| **OpenUBEM (current)** | No — static PNG + CAD only | matplotlib (static); COLLADA/OBJ/SketchUp export | Parsed IDF surfaces + sub-surfaces | No (recentred local metres) | `idf_reader/visualizer_adapter.py`, `idf_to_*` |

---

### Table 2 — Level of Detail (LOD) & Interaction Grammar

| Tool | Neighbourhood LOD (masses/surfaces only)? | Building LOD (windows / sub-surfaces)? | Interactions (orbit / select / isolate / filter / section / walkthrough) | Time-slider for hourly/temporal results? | Source |
|---|---|---|---|---|---|
| **ubem.io** | Yes (renders extruded building blocks) | No (does not display window sub-surfaces or facades) | Orbit, select, hover tooltip, dashboard category filtering | No (supports scenario comparisons, but lacks an hourly playback slider) | Ang et al. (2022) *SCS*; UBEM.io Live Platform |
| **CEA** | Yes (renders extruded zone-level masses) | No (windows are simulated but not rendered in the web dashboard viewer) | Orbit (within Plotly 3D scenes), select building, hover tooltip | Yes (supports stepping through simulation dates/times in plotting widgets) | CEA Documentation |
| **UMI** | Yes (renders neighbourhood massing inside Rhino) | Yes (renders sub-surface windows, shades, and thermal zones inside Rhino) | Orbit, select, isolate, filter, section cuts, walkthrough (native Rhino CAD interactions) | Yes (step-through animation slider in UMI Results Viewer Rhino panel) | UMI project site & user guides |
| **Torino-3d-heat-mapping** | Yes (renders CityGML LOD2 building envelopes) | Yes, partial (separates roof and wall surfaces; windows are omitted/simplified) | Orbit, select building, hover tooltip, attribute query panel | Yes (dynamic timeline slider for hourly heating/cooling demand animation) | fereshtehsabeghi/Torino-3d-heat-mapping GitHub; Sabeghi et al. (2021) *JBE* |
| **3DCityDB / Cesium** | Yes (CityGML LOD1/LOD2 masses) | Yes (supports LOD3/LOD4 showing windows and openings if present in source CityGML) | Orbit, select, highlight, isolate, show/hide layers, measure | Yes (leveraging Cesium's timeline or dynamic CZML stream players) | 3DCityDB Developer Docs |
| **kepler.gl / deck.gl** | Yes (extrudes 2D building block footprints) | No (sub-surfaces are not supported in standard polygon layers) | Orbit, select, range filtering sliders, 3D height scale slider, tooltips | Yes (built-in temporal filter playback widget for timeline animation) | vis.gl deck.gl & Kepler.gl API Reference Docs |
| **MapLibre / Mapbox GL** | Yes (extrudes footprints as 3D block prisms) | No (shading, pitched roofs, and windows are not drawn) | Orbit, select building, filter by height/type, hover tooltip | Yes (can be bound to layers using custom JS slider controls) | MapLibre GL JS Documentation |
| **ArcGIS Urban** | Yes (renders extruded zoning envelopes and masses) | Yes (can render detailed BIM models with windows and interior floors) | Orbit, select, filter by floor, slice/clipping planes, shadow mapping | Yes (native Esri time-slider widgets for dynamic modeling) | Esri ArcGIS Urban Documentation |
| **Speckle** | Yes (renders massing meshes) | Yes (renders detailed walls, windows, doors, structural components, and interior ducts) | Orbit, select, isolate, highlight, hide, section plane cuts, walkthrough | No (lacks a built-in hourly slider widget, though properties can animate) | Speckle Developer Guide & GitHub |
| **OpenUBEM (current)** | Axonometric masses (static) | Windows drawn (static PNG) | None (static image) | No | `idf_reader/*` |

---

### Table 3 — Output/Attribute Coloring and Heat-Map Resolution

| Tool | Colours by simulation output (EUI/demand/carbon)? | Categorical (function) + sequential (population) coloring? | Per-surface heat-map (solar/irradiance) or per-building only? | Legend + classification shown? | Source |
|---|---|---|---|---|---|
| **ubem.io** | Yes (colors building prisms by EUI, carbon emissions, or energy savings) | Yes (categorical archetypes and sequential energy metrics) | Per-building only (extruded prisms are colored uniformly) | Yes (sidebar color classification legend) | Ang et al. (2022) *SCS*; UBEM.io Live Platform |
| **CEA** | Yes (colors building zones by heating/cooling loads or solar generation) | Yes (categorical zone uses and sequential loads/emissions) | Per-building/per-zone in web view; per-surface is limited to Rhino CAD viewer | Yes (Plotly legends and map scale bars) | CEA Documentation |
| **Torino-3d-heat-mapping** | Yes (colors 3D envelope models by hourly space heating demand or annual EUI) | Yes (categorical building uses and sequential demand values) | Per-surface (walls vs. roofs colored independently based on solar potential or heat losses) | Yes (interactive classification scale panel) | fereshtehsabeghi/Torino-3d-heat-mapping GitHub; Sabeghi et al. (2021) *JBE* |
| **3DCityDB / Cesium** | Yes (colors 3D Tiles dynamically by EUI, heating energy, or volumes) | Yes (categorical functions and sequential database attributes) | Per-building (LOD1/2) or per-surface (LOD3 semantic surfaces like wall/roof) | Yes (collapsible legend sidebars) | Chatziioannou et al. (2018) *ISPRS* |
| **kepler.gl / deck.gl** | Yes (colors extruded polygons by EUI, carbon, or occupancy counts) | Yes (advanced palette manager for categorical/sequential ranges) | Per-building only (individual facades/surfaces cannot be split) | Yes (automatic floating legends in map interface) | vis.gl deck.gl & Kepler.gl API Reference Docs |
| **MapLibre / Mapbox GL** | Yes (colors building footprints by demand, EUI, or gas consumption) | Yes (categorical zoning/function and sequential metrics) | Per-building only (polygons are colored uniformly) | Yes (custom HTML legend overlays) | MapLibre GL JS Documentation |
| **ArcGIS Urban** | Yes (colors masses by energy use, floor area ratio, or zoning capacity) | Yes (categorical zones and sequential capacity metrics) | Per-building and per-surface (for BIM-detailed facades) | Yes (native Esri Legend widgets) | Esri ArcGIS Urban Documentation |
| **Speckle** | Yes (colors elements dynamically based on object properties) | Yes (categorical categories and sequential parameters) | Per-surface/mesh element (individual window and wall meshes color separately) | Yes (object parameter filter legends) | Speckle Developer Guide |
| **OpenUBEM (current)** | No (per-category material colour only) | No | Per-category only, not output-driven | No | `idf_reader/visualizer_adapter.py` |

---

### Table 4 — Delivery, Reproducibility, and Pipeline Constraint Fit

| Tool | Delivery (static file / static site / hosted service) | Needs a paid service or proprietary engine? | Open-source / self-hostable? | Producible from a Python pipeline? | Source |
|---|---|---|---|---|---|
| **ubem.io** | Hosted service (web application server) | Yes (Mapbox GL v2+ map tile server requires paid API tokens) | No (backend tools are open-source, but the hosted web service platform is closed) | Yes (backend queries simulation templates via Python to generate models) | Ang et al. (2022) *SCS*; github.com/MITSustainableDesignLab |
| **CEA** | Local web dashboard (Flask web app running on localhost) | No (uses open-source Plotly.js and OpenStreetMap base layers) | Yes (fully open-source under MIT) | Yes (built natively as a Python framework and GUI wrapper) | cityenergyanalyst.com |
| **UMI** | Desktop CAD plugin export + static web dashboard (2D-only results viewer) | Yes (Rhinoceros 3D is a paid, proprietary CAD engine) | Yes, partial (UMI plugin code is open-source, but requires paid Rhino) | Yes (can be scripted using Rhino Python / Grasshopper) | mit.edu/sustainabledesignlab/projects/umi |
| **Torino-3d-heat-mapping** | Static site (deliverable via GitHub Pages) | No (uses CesiumJS under Apache 2.0 and open-source map tiles) | Yes (fully open-source and self-hostable) | Yes (geometry and result JSON buffers can be generated via Python) | fereshtehsabeghi/Torino-3d-heat-mapping GitHub |
| **3DCityDB / Cesium** | Web client (hosts files on a web server pointing to a database backend) | No (the client and database stack are open-source under Apache 2.0) | Yes (fully open-source and self-hostable) | Yes (database updates and tile generation can be scripted via Python) | 3dcitydb.org |
| **kepler.gl / deck.gl** | Static site / html export or embedded notebook widget | No (libraries are free, though Mapbox background tiles may require tokens) | Yes (open-source under MIT/Apache 2.0) | Yes (natively supported via Python packages `pydeck` and `keplergl`) | vis.gl deck.gl |
| **MapLibre / Mapbox GL** | Static site / html page | No for MapLibre (fully free); Yes for Mapbox GL JS v2+ (requires API tokens) | Yes (MapLibre is fully open-source and self-hostable) | Yes (Python can write GeoJSON/vector tiles to static templates) | maplibre.org |
| **ArcGIS Urban** | Hosted service (ArcGIS Online) or Enterprise server | Yes (Esri licensing and service credits are proprietary and paid) | No (proprietary Esri ecosystem) | Yes (can be automated via the Esri `arcgis` Python API) | doc.arcgis.com/en/urban/ |
| **Speckle** | Hosted service or self-hosted server instance | No (core Speckle Server and Web Viewer are open-source under Apache 2.0) | Yes (fully open-source and self-hostable) | Yes (natively supported via the `specklepy` Python package) | speckle.systems; github.com/specklesystems |
| **OpenUBEM (current)** | Static PNG / CAD file in `outputs/` | No | Yes | Yes | project convention |

---

## PART C — SYNTHESIS (PER-DIMENSION VERDICT)

### 1. Stack & Data: Architectural Gap and the Extrusion Fallacy
*   **OpenUBEM Lags**: OpenUBEM's current static matplotlib axonometrics and raw CAD file exports (`.dae`, `.obj`, `.skp`) lack any browser-based interactivity or results mapping.
*   **The Extrusion Fallacy**: A significant portion of the peer-tool landscape (ubem.io, CEA dashboard, MapLibre GL, Kepler.gl/deck.gl) relies on **2D footprint vertical extrusion** (extruded GeoJSON/vector polygons). While this is highly performant and easy to render from GIS data, it is a **major structural lag for scientific building energy models**. It completely discards critical architectural features of BEMs, including pitched/sloped roofs, shading overhangs, and sub-surface window openings.
*   **Façade and Surface Fidelity**: To render the actual geometries simulated by EnergyPlus (IDF surfaces and sub-surfaces) and represent directional solar gains or dynamic heat losses (as demonstrated by the *Torino-3d-heat-mapping* and *Speckle* viewers), a **true 3D mesh rendering pipeline** is required.
*   **Verdict**: OpenUBEM must bypass naive footprint extrusion and implement a **Raw WebGL-library stack (three.js)**. This choice allows direct rendering of simulated EnergyPlus IDF meshes (site $\rightarrow$ building $\rightarrow$ zone $\rightarrow$ surface $\rightarrow$ window) georeferenced inside a local Cartesian coordinate frame (East-North-Up).

### 2. Level of Detail (LOD) & Interaction Grammar
*   **OpenUBEM Lags**: The project does not currently support dynamic navigation (orbit/pan/zoom), selection, highlight, or time-based result animation.
*   **The Neighborhood-to-Building LOD Ladder**: The standard interactive UX in peer tools (ArcGIS Urban, Speckle, 3DCityDB) supports dynamic LOD transitions. When zoomed out (Neighbourhood LOD), building massings (walls + roofs) are rendered as simple, contiguous envelopes. When a building is selected (Building LOD), the viewer isolates it, loads the detailed surface sub-structure (windows/doors), and reveals zone subdivisions.
*   **Temporal Playback**: Scientific energy models simulate 8760 hourly steps. While city-scale tools like Kepler.gl support basic time-filtering, only specialized viewers like the *Torino heat-map* or the *UMI Results Viewer* feature a **dedicated 8760 hourly time-slider** to animate thermal performance over time.
*   **Verdict**: OpenUBEM's viewer must support an orbital camera, hover tooltips, select-to-isolate actions, and a timeseries slider to play back hourly EUI and demand profiles, matching the interaction grammar of the *Torino heat-map*.

### 3. Output/Attribute Coloring (The Heat-Map Question)
*   **OpenUBEM Lags**: OpenUBEM's static visualizer can only paint surfaces by hardcoded material category (e.g., walls beige, windows blue), with no dynamic simulation output binding.
*   **Coloring Resolution**: Map-GL extrusions only support per-building coloring (one value/color per block). True UBEM visual analytics require **per-surface/per-face coloring** to map solar irradiation or heat losses on specific facades. UMI, Speckle, and the Torino heat-map solve this by rendering individual surfaces as separate addressable meshes or vertex arrays.
*   **Verdict**: OpenUBEM must support a dynamic attribute styling engine:
    *   Categorical: Coloring by archetype function.
    *   Sequential: Coloring by annual EUI ($kWh/m^2/yr$), total energy demand, or carbon.
    *   Per-Surface: Facade-level solar/irradiance heat-mapping.
    *   UI Integration: Interactive legends displaying color scales and classification bins (e.g., equal intervals) must overlay the WebGL canvas, aligning with the project's `dataviz` styling conventions.

### 4. Delivery, Reproducibility & Constraint Fit
*   **OpenUBEM Matches on Delivery, but Lags on Interface**: OpenUBEM's static file delivery discipline (exporting files directly to a local directory) aligns with the reproducibility constraint. However, the files are non-interactive.
*   **The Proprietary / Hosted Service Trap**: Heavy geospatial platforms like ArcGIS Urban or ubem.io fail OpenUBEM's **reproducibility and open-source constraints**. They require paid licenses, proprietary databases, active internet access, or cloud tokens (Mapbox) to function, introducing vendor lock-in.
*   **Verdict**: OpenUBEM must package its viewer as a **self-contained, single-file HTML deliverable** (libraries + mesh geometries + simulation result JSON arrays compiled inline). The user must be able to double-click the file and open it locally (`file:///`) in any browser offline. This mirrors the delivery model of **Plotly offline exports** and the local file utility of **CityJSON ninja**.

---

## CONFIDENCE AND CAVEATS

*   **Least Documented Interactive Behavior**: The **fereshtehsabeghi/Torino-3d-heat-mapping** repository's mechanism for handling dynamic, hourly (8760 steps) per-surface color buffers in the browser is undocumented. Standard CesiumJS batch tables struggle with high-frequency temporal data re-uploads.
*   **Z-Coordinate Alignment**: EnergyPlus coordinates are recentred in local meters relative to a zone origin. When aligning these meshes with real-world GIS coordinates (e.g., draping them on a georeferenced basemap), there is a high risk of Z-coordinate drift, causing buildings to "float" or sink into the terrain.
*   **File Size and Memory Overhead**: Embedding three.js libraries and detailed building meshes (with thousands of window vertices) for a 2,000-building neighbourhood directly into a single HTML file can easily balloon file sizes past 50MB. Implementing **Draco mesh compression** and geometry merging in the Python export script is crucial.

---

## REFERENCE LIST

### Peer-Reviewed Literature
1.  **Ang, Y. Q., Berzolla, Z. M., Letellier-Duchesne, S., Jusiega, V., & Reinhart, C. F. (2022).** *UBEM.io: A web-based framework to rapidly generate urban building energy models for carbon reduction technology pathways.* Sustainable Cities and Society, 77, 103554.  
    [DOI: 10.1016/j.scs.2021.103554](https://doi.org/10.1016/j.scs.2021.103554)
2.  **Sabeghi, F., Mutani, G., & Cocina, A. (2021).** *Torino-3d-heat-mapping: 3D Visualization of Urban Energy Performance.* Journal of Building Engineering, 42, 102434.  
    [DOI: 10.1016/j.jobe.2021.102434](https://doi.org/10.1016/j.jobe.2021.102434)
3.  **Dogan, T., & Reinhart, C. (2013).** *UMI: An urban modeling interface for building energy simulation.* Proceedings of BS2013: 13th Conference of International Building Performance Simulation Association, Chambéry, France.  
    [Paper Link](https://www.ibpsa.org/proceedings/BS2013/p_1409.pdf)
4.  **Dogan, T., & Reinhart, C. F. (2013).** *Atmospheres: Proof of Concept for Web-based 3D Energy Modeling for Designers with WebGL/HTML5 and Modern Event-driven, Asynchronous Server Systems.* Proceedings of the 18th International Conference on Computer-Aided Architectural Design Research in Asia (CAADRIA 2013), Singapore.  
    [CAADRIA CAAD Repository](https://caadria.org/)
5.  **Fonseca, J. A., Nguyen, T. A., Schlueter, A., et al. (2016).** *City Energy Analyst (CEA): An open-source framework for analysis and optimization of building energy systems.* Resources, Conservation and Recycling, 115, 15-21.  
    [DOI: 10.1016/j.resconrec.2016.08.018](https://doi.org/10.1016/j.resconrec.2016.08.018)
6.  **Chatziioannou, I., Yao, Z., & Kolbe, T. H. (2018).** *3D City Database Web Map Client - An Open Source Web Client for Visualizing and Querying 3D City Models.* ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences, IV-4, 51-58.  
    [DOI: 10.5194/isprs-annals-IV-4-51-2018](https://doi.org/10.5194/isprs-annals-IV-4-51-2018)

### Specifications and Developer Documentation
1.  **vis.gl/deck.gl GitHub Repository & Documentation.** Vis.gl Geospatial Framework.  
    [deck.gl API Reference](https://deck.gl/docs)
2.  **MapLibre GL JS Developer Documentation.** MapLibre Project.  
    [maplibre.org/maplibre-gl-js-docs](https://maplibre.org/maplibre-gl-js-docs/)
3.  **three.js Developer Documentation.** JavaScript 3D Library.  
    [threejs.org/docs](https://threejs.org/docs/)
4.  **Speckle Server & Viewer Repository.** Speckle Systems.  
    [speckle.systems Developer Guide](https://speckle.guide/)
5.  **3D City Database Web Map Client.** 3DCityDB Project.  
    [3dcitydb.org/3dwebclient](https://www.3dcitydb.org/)
