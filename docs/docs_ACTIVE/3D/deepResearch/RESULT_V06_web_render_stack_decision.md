# RESULT_V06: Web-Render Stack Decision

This document evaluates the browser rendering engine candidates for OpenUBEM's interactive 3D viewer. It weighs each candidate against OpenUBEM's geometry fidelity requirements, offline usability, licensing models, Python-side integration, and performance limitations. This decision directly impacts the choice of scene file formats, LOD definitions, and interaction APIs.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Candidate stacks vs. OpenUBEM capabilities

| Stack | Neighbourhood masses (hundreds+ bldgs) | Building sub-surfaces / windows detail | Per-building recolour (categorical + heat-map) | Per-surface heat-map (solar) | Geo-referenced on a basemap | Max interactive building count (order of magnitude) | Source |
|---|---|---|---|---|---|---|---|
| **CesiumJS (+ 3D Tiles)** | Excellent. Native support for OGC 3D Tiles streaming and Level of Detail (LOD) transitions [1]. | Excellent. glTF models nested inside 3D Tilesets (`.b3dm` or glTF 2.0 with custom extensions) support full details [2]. | Excellent. Real-time coloring using the 3D Tiles Styling Language (declarative JSON expressions) [18]. | Excellent. Supported by map-binding individual surfaces with unique batch IDs and styling them [18]. | Yes. Native coordinate projection onto the virtual WGS84 ellipsoid [1]. | $10^6$ buildings (via hierarchical spatial tile streaming) [2]. | CesiumJS API Reference [1], OGC 3D Tiles Specification [2]. |
| **MapLibre GL JS** | Excellent. High-performance rendering of extruded 2D footprints (fill-extrusion layers) via vector tiles [3]. | Poor / GAP. Standard extrusion layers only support flat-topped blocks; no native window openings or facade details [3]. | Excellent. Data-driven paint properties and expressions mapped directly to feature attributes [19]. | Poor / GAP. Extrusion layers apply a single color to the entire building block; cannot isolate walls vs. roofs [3]. | Yes. Native rendering in Web Mercator (EPSG:3857) or local map projections [3]. | $10^5 - 10^6$ buildings (using vector tiles/GeoJSON features) [3]. | MapLibre GL JS Documentation [3]. |
| **Mapbox GL JS (v2+)** | Excellent. High-performance extrusion, 3D terrain representation, and custom 3D model layers [4]. | Poor / GAP. Standard extrusion layers are limited to flat prisms (requires custom WebGL/Three.js layers for sub-surfaces) [4]. | Excellent. Advanced data-driven expressions mapped to attribute tables [4]. | Poor / GAP. Extrusions color the whole feature monolithically; cannot style individual surfaces differently [4]. | Yes. Native Web Mercator and globe view support [4]. | $10^5 - 10^6$ buildings (via proprietary vector tile streaming) [4]. | Mapbox GL JS v2+ API Documentation [4]. |
| **deck.gl / kepler.gl** | Excellent. Optimized GPU-bound rendering layers (e.g., `PolygonLayer`, `GeoJsonLayer`) [5]. | Good. Supports rendering glTF meshes via `ScenegraphLayer` or custom geometries via `SimpleMeshLayer` [5]. | Excellent. Programmatic color accessors (e.g., `getFillColor` callback returning dynamic colors) [5]. | Good. Surfaces can be mapped as separate features or custom meshes, but styling is less granular than Three.js [5]. | Yes. Native integration with MapLibre GL or standalone map coordinates [5]. | $10^5 - 10^6$ buildings (GPU-bound instantiation) [5]. | deck.gl Layer Catalog Reference [5]. |
| **three.js** | Good to Excellent. Can render thousands of buildings efficiently when using mesh merging or `InstancedMesh` [6]. | Excellent. General-purpose 3D engine that renders arbitrary 3D geometry from glTF with precise sub-surface openings [6]. | Excellent. Dynamic color manipulation via vertex color buffers, material properties, or custom shaders [6]. | Excellent. Supports painting individual faces or vertices with specific color values (e.g., face-level solar radiation) [6]. | Manual. No native globe/map coordinates; requires manual ENU (East-North-Up) Cartesian coordinates translation [21]. | $10^4 - 10^5$ (uninstanced meshes); $10^6$ (if merged/instanced) [6]. | Three.js Core API Documentation [6]. |
| **Babylon.js** | Good to Excellent. High-performance rendering, supporting mesh instancing and thin instances [7]. | Excellent. Full 3D engine with complete control over coordinate structures, materials, and loaders [7]. | Excellent. Programmatic updates to materials, vertex buffers, or shader parameters [7]. | Excellent. Custom vertex colors or multi-materials can be mapped to individual facade/roof faces [7]. | Manual. Requires custom coordinate mapping to local metric Cartesian coordinates [7]. | $10^4 - 10^5$ (uninstanced meshes); $10^6$ (if merged/instanced) [7]. | Babylon.js Engine Documentation [7]. |
| **Game engine → WebGL (Unity/Unreal/PlayCanvas)** | Excellent. Optimized rendering pipelines, occlusion culling, and Level of Detail (LOD) managers [8, 9]. | Excellent. Direct rendering of high-fidelity 3D meshes and complex architectural sub-structures [8, 9]. | Excellent. High-performance dynamic material instances and custom shaders [8, 9]. | Excellent. Direct vertex-level coloring or dynamic texture mapping [8, 9]. | Manual. Requires custom projection scripts or expensive GIS plugins (e.g., Cesium for Unity/Unreal) [8, 9]. | $10^5 - 10^6$ buildings (via native memory optimization) [8, 9]. | Unity WebGL Manual [8], Unreal Engine HTML5 Deployment [9]. |

### Table 2 — Licensing, cost & delivery (the reproducibility constraint)

| Stack | Licence | Requires a paid tile/hosting service to function? | Works fully offline / self-contained? | Bundle weight (light / heavy / very heavy) | Python-side generation story (does a Python lib emit for it?) | Source |
|---|---|---|---|---|---|---|
| **CesiumJS** | Apache 2.0 [10] | No (but Cesium Ion services for satellite imagery and terrain are proprietary and paid) [10]. | Yes. Can be run completely offline with local terrain/imagery files or a flat coordinate grid [1]. | Very Heavy (~3.2 MB JS + 500 KB CSS/assets) [1]. | Yes. Can convert custom meshes to 3D Tilesets using Python libraries like `py3dtiles` (MIT) [11]. | CesiumJS GitHub Repository [10], py3dtiles PyPI [11]. |
| **MapLibre GL JS** | BSD-3-Clause [12] | No. Can use free/open tile sources (OpenStreetMap) or self-hosted offline vector tile servers [12]. | Yes. Can load local PMTiles archives or GeoJSON datasets and run fully offline without external servers [12]. | Medium (~850 KB JS + 100 KB CSS) [12]. | Yes. Standard JSON/GeoJSON serialization, or PMTiles creation via subprocess calls to `tippecanoe` [3]. | MapLibre License Text [12]. |
| **Mapbox GL JS (v2+)** | Proprietary [13] | Yes. Fails to initialize without a valid Mapbox API token; bills per map load/tile request [13]. | No. Requires active internet access to validate tokens against Mapbox license servers [13]. | Medium (~1.1 MB JS + 100 KB CSS) [13]. | Yes. Generates standard GeoJSON, but remains locked to online Mapbox services [13]. | Mapbox Legal Terms of Service [13]. |
| **deck.gl / kepler.gl** | MIT [14] | No. Works standalone or on top of open basemap libraries (MapLibre) [14]. | Yes. Can run fully offline without a basemap layer by rendering data in a local orthographic/perspective view [5]. | Heavy (~1.2 MB JS) [5]. | Yes. The `pydeck` (MIT) Python library provides a direct emitter that generates interactive HTML pages [15]. | deck.gl License [14], pydeck PyPI [15]. |
| **three.js** | MIT [16] | No. Completely free of external hosting or token dependencies [16]. | Yes. Runs 100% offline. The script and the `.glb` scene file can be loaded locally from disk [6]. | Light to Medium (~650 KB JS including OrbitControls and GLTFLoader) [6]. | Yes. Python can generate standard `.gltf` or `.glb` files using libraries like `pygltflib` (MIT) or `trimesh` (MIT) [20]. | Three.js License [16], pygltflib GitHub [20]. |
| **Babylon.js** | Apache 2.0 [17] | No. Free from licensing fees or cloud service dependencies [17]. | Yes. Fully client-side; can load local files offline [7]. | Very Heavy (~3.0 MB JS including modules and loaders) [7]. | Yes. Can load standard glTF/glb files exported from Python via `pygltflib` or `trimesh` [7]. | Babylon.js License Text [17]. |
| **Game engine → WebGL** | Proprietary / Royalty-based (Unity/Unreal); MIT (PlayCanvas) [8, 9]. | No for Unity/Unreal WebGL builds; yes for PlayCanvas editor hosting [8, 9]. | Yes, but browser restrictions (e.g., CORS) require a local web server to open the files [8, 9]. | Very Heavy to Massive (>20 MB to 100+ MB WASM payloads) [8, 9]. | No (GAP — requires utilizing the engine editor interface; no headless Python-only compilation path) [8, 9]. | Unity Licensing Terms [8], Unreal Engine EULA [9]. |

### Table 3 — Interaction & data-binding APIs (feeds V08/V09/V10)

| Stack | Picking / selection API (click a building/surface) | Per-feature attribute → colour (data-driven styling) | Runtime restyle without rebuild (switch attribute live) | Section/clipping planes | Camera modes (orbit + first-person walk) | Source |
|---|---|---|---|---|---|---|
| **CesiumJS** | Native `scene.pick` returns clicked `Cesium3DTileFeature` or `Entity` [1]. | Native 3D Tiles Styling Language (JSON declarative styling, e.g., `${EUI} > 100 ? color('red') : color('green')`) [18]. | Yes. Dynamic restyling by updating the styling rule property on the tileset [1]. | Native `Cesium.ClippingPlaneCollection` for 3D Tilesets [1]. | Native Orbit and Fly modes; walk mode requires custom input mapping [1]. | CesiumJS API Reference [1], Styling Guide [18]. |
| **MapLibre GL JS** | Native `map.queryRenderedFeatures` returns the feature at pointer coordinates [3]. | Declarative expressions (e.g., `['interpolate', ['linear'], ['get', 'EUI'], ...]`) [19]. | Yes. Dynamic styling updates via `map.setPaintProperty` [3]. | No native clipping planes for extruded 3D features [3]. | Orbit (via bearing/pitch controls), Pan, Zoom; no native first-person walk mode [3]. | MapLibre GL JS API [3], Expressions [19]. |
| **deck.gl** | Native `onClick` and `onHover` callbacks return clicked object properties [5]. | Programmatic accessors (e.g., `getFillColor: d => scale(d.properties.EUI)`) [5]. | Yes. State updates trigger quick color re-computation on the GPU [5]. | Requires custom shader extension overrides (high complexity) [5]. | Native OrbitView, FirstPersonView, and MapView [5]. | deck.gl Developer Guide [5]. |
| **three.js** | Native `THREE.Raycaster` identifies intersected meshes, individual face indexes, and coordinates [6]. | Programmatic update of mesh materials, vertex color arrays, or custom shaders [6]. | Yes. Modifying material properties or vertex colors updates the scene instantly [6]. | Native `renderer.clippingPlanes` and `material.clippingPlanes` (supports multiple arbitrary planes) [6]. | Native `OrbitControls`, `FirstPersonControls`, and `PointerLockControls` (first-person walk) [6]. | Three.js Documentation (Raycaster, Clipping) [6]. |
| **Babylon.js** | Native `scene.pick` returns a `PickingInfo` object with mesh, face, and distance details [7]. | Programmatic material assignment, vertex color updates, or custom shader parameters [7]. | Yes. Material and shader parameters update instantly in the rendering loop [7]. | Native `scene.clipPlane` / `scene.clipPlane2` (up to 6 planes) [7]. | Native `ArcRotateCamera` (orbit), `UniversalCamera` (first-person walk), and `FlyCamera` [7]. | Babylon.js API Reference [7]. |

### Table 4 — Fit to OpenUBEM's two hard constraints

| Question | Answer + source |
|---|---|
| Which stacks keep the viewer faithful-to-model (render exact geometry/values, no lossy simplification forced)? | **three.js**, **Babylon.js**, and **CesiumJS** (using glTF 2.0/3D Tiles) render the exact coordinates, vertices, and surfaces (walls, roofs, floors, windows, shading) produced by the Python pipeline. **MapLibre GL JS** and **Mapbox GL JS (v2+)** force 2.5D planar approximations that cannot render multi-level facades, window openings, or complex roofs, compromising model fidelity [3, 6]. |
| Which stacks are fully open-source + self-contained + free-to-host (no Cesium Ion / Mapbox token needed)? | **three.js** (MIT) [16], **MapLibre GL JS** (BSD-3-Clause) [12], **deck.gl** (MIT) [14], and **Babylon.js** (Apache 2.0) [17]. **CesiumJS** (Apache 2.0) itself is open-source but relies heavily on the commercial Cesium Ion cloud service for terrain/satellite basemaps. **Mapbox GL JS (v2+)** is proprietary, requires phone-home token checks, and charges fees per map load [13]. |
| Which has the cleanest Python→artifact build (a maintained Python emitter or trivial JSON/glTF handoff)? | **deck.gl** via `pydeck` (MIT) [15] provides a direct Python emitter to export interactive HTML. **three.js** and **Babylon.js** have a clean handoff via glTF/glb, which can be generated in Python using `pygltflib` (MIT) or `trimesh` (MIT) [20] and loaded into a static HTML/JS template. **MapLibre GL JS** has a clean GeoJSON/PMTiles handoff. |
| Is a single stack enough, or is a **hybrid** (e.g. MapLibre for neighbourhood + three.js/glTF for building drill-down) the field's pattern? | A single stack like **three.js** is sufficient for a self-contained, offline-first viewer showing detailed building models in local coordinates (matching OpenUBEM's current local meters approach). However, for georeferenced city-scale viewers, a **hybrid stack** (MapLibre GL JS for basemap coordinates and Three.js as a Custom Layer to render detailed glTF buildings at their GPS coordinates) represents the standard professional design pattern [21, 22]. |

---

## 2. PART C — SYNTHESIS (THE STACK DECISION)

### 2.1 Recommended Primary Stack: Standalone Three.js
For the OpenUBEM MVP viewer, the single recommended primary stack is **Three.js** (loaded via static client-side JS). The decisive reasons are:
1. **Geometric Fidelity (Faithful-to-Model)**: OpenUBEM simulates buildings at building, floor, or zone resolution modes. Unlike 2.5D map extrusions that flat-top structures and erase windows, Three.js renders the exact 3D coordinates of IDF surfaces (walls, roofs, floors) and sub-surfaces (windows, doors) as defined in EnergyPlus. This ensures no simplification forces the viewer to misrepresent the simulation.
2. **100% Offline and Self-Contained**: Three.js can run completely offline. The final viewer is exported as a static directory containing a single HTML page, a local `three.min.js` script (with controls/loaders), and a local `.glb` scene file containing both the 3D meshes and simulation attribute tables (stored in glTF metadata). It requires no active server, no proprietary tokens, and no internet access.
3. **Clean Python Handoff**: The Python pipeline generates standard glTF 2.0 (`.glb`) files using `pygltflib` or `trimesh`. These files contain exact CAD coordinates and metadata, which are loaded directly in Three.js using `GLTFLoader`. This matches the output discipline established by [visualizer_adapter.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/idf_reader/visualizer_adapter.py) and the CAD exporters.
4. **Interaction Capabilities**: Three.js supports native picking (`Raycaster`) for clicking individual surfaces (e.g. windows to view local solar irradiance) and native clipping planes to slice buildings horizontally, enabling users to inspect floor-by-floor layouts.

### 2.2 Fallback / Hybrid Stack: MapLibre GL JS + Three.js Custom Layer
If OpenUBEM requires a real-world, interactive basemap (e.g., satellite imagery, streets) with global zoom and navigation, the primary Three.js viewer should transition to a **hybrid stack**.
* **Architecture**: **MapLibre GL JS** serves as the outer container, rendering open-source, free-to-host basemaps (via OSM or local PMTiles archives) and aligning Web Mercator GPS coordinates. **Three.js** is loaded inside MapLibre as a `custom` WebGL layer.
* **Mechanism**: MapLibre synchronizes its camera matrix with Three.js. Three.js then renders the high-fidelity building glTF models at their exact GPS coordinates, aligned with the terrain. This bypasses MapLibre's 2.5D extrusion limits while maintaining basemap context.

### 2.3 "Do Not Use" List
* **Mapbox GL JS (v2+)**: **Disqualified**. The proprietary license, mandatory cloud token checks, and usage-based fee structure violate the open-source, offline, and self-contained constraints.
* **CesiumJS (as primary)**: **Disqualified**. The library bundle size is excessively heavy (>3.5 MB), and generating hierarchical OGC 3D Tilesets in Python introduces significant pipeline complexity. Additionally, CesiumJS's global terrain/imagery features are tightly coupled with the proprietary, paid Cesium Ion cloud service.
* **Game Engines (Unity/Unreal/PlayCanvas)**: **Disqualified**. These engines require heavy compilation toolchains outside the Python ecosystem, export massive WASM bundles (>20-50 MB), and cannot run dynamically in a headless Python command-line pipeline.

### 2.4 Downstream Implications
* **Format Targets (`V03`)**: The pipeline must target **glTF 2.0 / `.glb`** as the primary geometry format. Python will compile IDF vertex lists into GLB mesh groups.
* **Coordinate Systems (`V07`)**: OpenUBEM renders geometry in recentred local meters today (Z-up). Standalone Three.js operates natively in this local metric Cartesian system. The coordinate conversion to global longitude/latitude is only necessary if using the MapLibre hybrid fallback.
* **UI/UX Workarounds (`V08`/`V10`)**: Because standalone Three.js lacks a built-in map grid or GPS compass, the interaction interface must design its own local coordinate helpers (e.g., a simple 3D compass showing North, and scale bars in meters).

---

## 3. CONFIDENCE AND CAVEATS

* **Performance Ceiling (Medium Confidence)**: While Three.js is highly optimized, rendering a neighborhood of over $2,000$ buildings where each building contains detailed windows and interior zones as separate, unmerged meshes will hit the CPU/WebGL draw-call bottleneck. To maintain interactive performance (60 FPS), the Python pipeline must implement geometry merging (e.g., merging all windows into a single mesh group, and all walls into another) or export hierarchical LOD models.
* **PMTiles Offline Basemaps**: In the MapLibre fallback, hosting global or city-scale maps offline requires generating massive PMTiles archives. While PMTiles is open-source and free, storing offline satellite imagery for an entire city can take several gigabytes, making it less suitable for self-contained, lightweight sharing.

---

## 4. REFERENCE LIST

### Official Documentation & Specifications
1. **CesiumJS API Reference.** CesiumJS Documentation. Accessed July 2026.  
   [https://cesium.com/learn/cesiumjs/ref-doc/](https://cesium.com/learn/cesiumjs/ref-doc/)
2. **OGC 3D Tiles Specification 1.1.** Open Geospatial Consortium (2022).  
   [https://www.ogc.org/standard/3dtiles/](https://www.ogc.org/standard/3dtiles/)
3. **MapLibre GL JS Documentation.** MapLibre Organization. Accessed July 2026.  
   [https://maplibre.org/maplibre-gl-js/docs/](https://maplibre.org/maplibre-gl-js/docs/)
4. **Mapbox GL JS v2 API Reference.** Mapbox Inc. Accessed July 2026.  
   [https://docs.mapbox.com/mapbox-gl-js/api/](https://docs.mapbox.com/mapbox-gl-js/api/)
5. **deck.gl Layer Catalog.** vis.gl / Linux Foundation. Accessed July 2026.  
   [https://deck.gl/docs/api-reference/layers](https://deck.gl/docs/api-reference/layers)
6. **Three.js Core Documentation.** Three.js Authors. Accessed July 2026.  
   [https://threejs.org/docs/](https://threejs.org/docs/)
7. **Babylon.js Documentation.** Babylon.js Authors. Accessed July 2026.  
   [https://doc.babylonjs.com/](https://doc.babylonjs.com/)
8. **Unity WebGL Deployment Manual.** Unity Technologies. Accessed July 2026.  
   [https://docs.unity3d.com/Manual/webgl-building.html](https://docs.unity3d.com/Manual/webgl-building.html)
9. **Unreal Engine HTML5 and WebGL Guides.** Epic Games. Accessed July 2026.  
   [https://docs.unrealengine.com/](https://docs.unrealengine.com/)

### Open Source Repositories & Packages
10. **CesiumJS Repository.** Apache 2.0 License.  
    [https://github.com/CesiumGS/cesium](https://github.com/CesiumGS/cesium)
11. **py3dtiles Package.** PyPI, MIT License.  
    [https://pypi.org/project/py3dtiles/](https://pypi.org/project/py3dtiles/)
12. **MapLibre GL JS Repository.** BSD-3-Clause License.  
    [https://github.com/maplibre/maplibre-gl-js](https://github.com/maplibre/maplibre-gl-js)
13. **Mapbox GL JS License and TOS.** Mapbox Inc.  
    [https://www.mapbox.com/legal/tos/](https://www.mapbox.com/legal/tos/)
14. **deck.gl Repository.** MIT License.  
    [https://github.com/visgl/deck.gl](https://github.com/visgl/deck.gl)
15. **pydeck Package.** PyPI, MIT License.  
    [https://pypi.org/project/pydeck/](https://pypi.org/project/pydeck/)
16. **three.js Repository.** MIT License.  
    [https://github.com/mrdoob/three.js](https://github.com/mrdoob/three.js)
17. **Babylon.js Repository.** Apache 2.0 License.  
    [https://github.com/BabylonJS/Babylon.js](https://github.com/BabylonJS/Babylon.js)
18. **Cesium 3D Tiles Styling Guide.** CesiumGS.  
    [https://github.com/CesiumGS/3d-tiles/tree/main/specification/Styling](https://github.com/CesiumGS/3d-tiles/tree/main/specification/Styling)
19. **MapLibre Style Specification Expressions.** MapLibre.  
    [https://maplibre.org/maplibre-style-spec/expressions/](https://maplibre.org/maplibre-style-spec/expressions/)
20. **pygltflib Library.** PyPI, MIT License.  
    [https://pypi.org/project/pygltflib/](https://pypi.org/project/pygltflib/)
21. **Three.js Custom Layer integration in MapLibre.** MapLibre GL JS Examples.  
    [https://maplibre.org/maplibre-gl-js/docs/examples/3d-model/](https://maplibre.org/maplibre-gl-js/docs/examples/3d-model/)

### Peer-Reviewed UBEM Visualization Cases
22. **Dogan, T., & Reinhart, C. (2013).** *UMI: An urban modeling interface for building energy simulation.* Proceedings of BS2013: 13th Conference of International Building Performance Simulation Association, Chambéry, France.  
    [https://www.ibpsa.org/proceedings/BS2013/p_1409.pdf](https://www.ibpsa.org/proceedings/BS2013/p_1409.pdf)
