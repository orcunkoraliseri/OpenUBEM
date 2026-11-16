# Image Generation Prompts — OpenUBEM Pipeline Graphical Abstract

This reference contains ready-to-paste prompts designed for modern generative image models (Gemini Web, Midjourney v6, DALL-E 3, Stable Diffusion XL) to generate the **OpenUBEM Graphical Abstract** that visually replaces the technical ASCII pipeline box diagram.

Follows the design principles and visual hierarchy established in `docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md`.

---

## Prompt 1: 3D Axonometric Realistic (Hero Abstract / Storytelling)
*Style: §2.2 Realistic 3D Axonometric. Best for: GitHub README Hero, presentation cover slides, executive summaries.*

```text
Create a wide, publication-grade realistic 3D axonometric (isometric) architectural illustration, in the style of an elite architectural technology monograph or high-end engineering journal cover. Clean daylight studio lighting, soft ambient occlusion shadows, photorealistic materials (structural glass curtain walls, warm timber accents, architectural fair-faced concrete, brushed aluminum, and subtle double glazing), all set against an ultra-clean, minimalist, light-neutral pale gray background (no competing sky, no horizon line).

The composition is one continuous horizontal sequence of five interconnected floating isometric stages reading strictly left-to-right, each resting on its own floating geometric ground plane, connected by a luminous cyan/teal data ribbon and subtle dimension leader-lines.

Stage 1 — Data Acquisition (Leftmost):
An isometric city fragment showing raw real-world GIS parcels with irregular footprint polygons (L-shapes, U-shapes, perimeter blocks), overlaid with subtle laser-scanned grid lines and vector parcel boundaries. Small floating matte white technical card: "01 DATA ACQUISITION · GIS & LiDAR".

Stage 2 — Semantic Enrichment:
The building footprints extrude into simplified 3D building massings, color-coded by standard building archetypes (terracotta residential apartments, cool-slate commercial office, warm-timber civic). A faint translucent hemispherical weather dome hovers above them with tiny sun vector arrows and a mini meteorological coordinate grid. Small floating matte white technical card: "02 SEMANTIC ENRICHMENT · TABULA & ERA5".

Stage 3 — Dwelling Layout & IDF Generation (Centerpiece):
A large, intricate architectural cutaway / exploded axonometric of a multi-storey residential building. The facade is partially peeled open to reveal internal floor plates sliced into distinct individual dwelling thermal zones (soft cyan / light blue conditioned apartments) wrapping around a central warm amber stair/circulation core that pierces from ground to roof. Translucent contextual shading volumes stand around it at 20 m radius. Small floating matte white technical card: "03 DWELLING ZONING · IDF GENERATION".

Stage 4 — Physics & EnergyPlus Simulation:
The building model actively interacting with physical simulation forces: low-angle golden solar rays casting precise shadows onto adjacent facades, dynamic thermal heat flux vectors entering glazing, airflow streamlines, and a glowing circular computational accelerator base plate underneath. Small floating matte white technical card: "04 PHYSICS ENGINE · ENERGYPLUS 23+".

Stage 5 — Urban Results & Microclimate (Rightmost):
A dense urban district where every building is rendered in a vibrant heatmap gradient (deep purple to viridis green and warm gold) representing simulated heating and cooling EUI (kWh/m²). Above the district floats a minimalist holographic glass dashboard with tiny sparklines, annual load curves, and carbon emission metrics (kg CO₂e/m²). On the street level between buildings, a subtle thermal comfort mesh shows outdoor microclimate pedestrian comfort. Small floating matte white technical card: "05 URBAN SCALE RESULTS · ENERGY & CO₂".

Visual Discipline:
All five stages share the exact same isometric 30-degree camera angle, consistent scale, and daylight direction. The palette is strictly controlled: natural architectural neutrals (concrete gray, white, timber) tied together by the glowing cyan/teal data ribbon and viridis thermal accents. Clean, sharp lines, zero watermarks, zero random stock figures, zero invented text beyond the five specified cards.
```

---

## Prompt 2: Hybrid Annotated Axonometric (Technical Hero Figure)
*Style: §2.3 Hybrid Annotated Axonometric. Best for: Peer-reviewed journal submission (e.g. Energy & Buildings), GitHub Technical Architecture section.*

```text
Create a wide, highly detailed technical hybrid 3D isometric cutaway diagram for an urban energy engineering paper, combining photorealistic architectural rendering with crisp CAD engineering annotations. Clean white background, high contrast, studio ambient lighting with sharp directional shadows.

Organized into four progressive isometric panels (a), (b), (c), (d) arranged horizontally from left to right on floating ground slabs:

Panel (a) — Footprint Regularization & Morphology:
A real European cadastral block. The orange noisy GIS footprints are snapped to cleaned blue vector outlines with dashed tolerance markers. Three small callout cards with thin leader-lines: "GIS Cadastre → 0.15 m Snap", "Morphology: Point Block / Slab / Perimeter Block", "Area Conservation Error < 0.00%".

Panel (b) — Ruled Dwelling Stratification:
An exploded multi-storey building volume showing the interior zoning scheme: each floor plate is divided into equal-area dwelling units tinted pale translucent cyan (labeled "Conditioned Living Zones") arranged along an unconditioned central corridor and stair core tinted warm amber (labeled "Unconditioned Circulation Core, 1.80 m"). Thin CAD dimension lines call out facade frontage and floor-to-ceiling heights.

Panel (c) — 20 m Context Shading Envelope:
One target building highlighted in crisp solid green, surrounded by neighboring context buildings rendered as semi-transparent frosted acrylic massing blocks. A translucent circular boundary ring on the ground labeled "20.0 m Solar Shading Radius". Touching party walls are highlighted with an adiabatic hatch pattern labeled "Shared Party Wall → Adiabatic Boundary". Golden solar rays demonstrate FullExterior solar tracking.

Panel (d) — EnergyPlus Metered Results:
The completed district rendered with building surfaces colored continuously by annual heating Energy Use Intensity (kWh/m²·a) using a standard Viridis colormap (30 to 140 kWh/m²). Thin leader-lines connect to a small floating stats card: "Validated against NYC LL84 / CBECS", "Per-Building Metered End Uses", "0.00% Tuning / Unfitted Physics".

Engineering Hygiene:
Crisp sans-serif typography, ultra-thin leader-lines with dot anchors, consistent isometric perspective across all panels, publication-ready vector clarity, no clutter.
```

---

## Prompt 3: Clean Modern Vector Technical Flowchart
*Style: §2.1 Modern Vector Architecture Flowchart. Best for: High-res SVG/Vector documentation, GitHub dark/light mode diagram.*

```text
Create a clean, modern, horizontal engineering flowchart diagram on a pristine white background. Technical vector style, flat shapes with subtle edge radiuses, elegant sans-serif monospace typography, and generous whitespace. Navy/slate and neutral gray primary palette with an electric cyan accent for data flows and an amber accent for validation checkpoints.

A single main horizontal pipeline reading left to right across 5 primary process blocks:

1. [01 DATA ACQUISITION]
   Sub-label: "Overpass API / Cadastre / LiDAR / 3D Bags"
   Artifact tag: "01_buildings_clean.gpkg"

2. [02 SEMANTIC ENRICHMENT]
   Sub-label: "Archetype Mapping (TABULA/DOE) + Climate (ERA5/TMYx)"
   Artifact tags: "02_classified.gpkg · 02a_climate.gpkg · 02b_enriched.gpkg"

3. [03 IDF GENERATION]
   Sub-label: "Ruled Dwelling Zoning · 20 m Context Shading Envelope"
   Artifact tag: "03_idf_manifest + idfs/*.idf"

4. [04 ENERGYPLUS SIMULATION]
   Sub-label: "EnergyPlus 23+ Multi-process · 10 HVAC Families · Native Meters"
   Artifact tag: "04_simulation_manifest.parquet"

5. [05 RESULTS & CARBON]
   Sub-label: "Annual End-Use EUI · Hourly Loads · Operational Carbon (eGRID/EU)"
   Artifact tags: "05_results.gpkg · 05_summary.json · 3D Viewer"

Branching downwards from Step 5 via an opt-in dashed connector line:
└─► [06 OUTDOOR MICROCLIMATE & COMFORT (Opt-in)]
    Sub-label: "ENVI-met / UTCI / PET pedestrian thermal comfort"
    Artifact tag: "06_mc_*.tif / .gpkg"

Footer note strip:
"Design Principles: 100% physically modelled meters (no statistical regression) · Zero fitted parameters · Explicit input provenance · 10 European & International testbeds."
```
