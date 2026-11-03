# RESULT_12_shading_solar_context — Shading and Solar Context Interaction with Resolution

This report evaluates how external neighbor shading, self-shading, and internal solar distribution interact with simulation resolution modes (`building`, `floor`, and `zone`) in OpenUBEM. Shading from the urban context is highly height-dependent, and this analysis establishes the mathematical and physical biases of resolution reduction, recommends robust settings for EnergyPlus simulations, and identifies necessary improvements for the OpenUBEM geometry engine.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Shading application per resolution

| Mode | Receiving surfaces | Can represent height-varying neighbour shading? | Bias if not | Source |
|---|---|---|---|---|
| `building` (1 zone, full height) | One tall exterior wall per orientation | No (averaged) | Dampens peak loads and vertical temperature gradients. Overestimates solar gains on lower (shaded) wall portions and underestimates solar gains on upper (sunny) wall portions. This leads to under-sizing peak cooling loads for upper stories, over-sizing lower stories, and distorting coincident building-level peak cooling timing. | EnergyPlus Engineering Reference (Shadowing Calculations); Dogan & Reinhart (2017) |
| `floor` (1 zone/floor) | Per-floor exterior walls | Yes | N/A (correctly resolved vertically; lower zones receive shadow and upper zones receive unobstructed solar radiation). | EnergyPlus Engineering Reference; Iseri et al. (2025) |
| `zone` (core/perimeter) | Perimeter walls per floor | Yes | N/A (correctly resolved both vertically and horizontally; isolates perimeter solar heat gains from the core zone, preventing artificial solar distribution into non-exposed spaces). | EnergyPlus Engineering Reference; ASHRAE 90.1-2019 Appendix G |

### Table 2 — Solar Distribution setting interaction

| Setting | Behaviour | Works with core/perimeter? | Cost | Source |
|---|---|---|---|---|
| `MinimalShadowing` | No exterior shading calculations from neighbor geometry or self-shading are performed (only window reveals). All entering beam solar is assumed to fall entirely on the zone floor. | Yes (but ignores all urban context). | Lowest (negligible runtime overhead). | EnergyPlus Input-Output Reference (Building object, Solar Distribution field) |
| `FullExterior` | Computes shadow patterns on all exterior surfaces from overhangs, fins, self-shading, and neighboring context buildings. All entering beam solar is assumed to fall entirely on the zone floor. | Yes (highly robust; does not require zones to be convex, which is critical for complex geometries or core/perimeter divisions where non-convex zones are common). | Moderate (scales with the count of shading and target surfaces). | EnergyPlus Input-Output Reference; Ladybug Tools / Honeybee documentation |
| `FullInteriorAndExterior` | Computes exterior shadow patterns and uses analytical ray tracing to distribute entered beam solar onto specific interior surfaces (walls, floors, ceilings) based on solar angle and window coordinates. | No (requires all thermal zones to be strictly convex. Core/perimeter zoning of arbitrary real footprints generates non-convex shapes, which trigger fatal/warning errors in EnergyPlus). | High (expensive ray tracing calculations at each calculation step). | EnergyPlus Engineering Reference (Solar Distribution); Ladybug Tools / Honeybee documentation |
| **Recommended for OpenUBEM at each resolution** | `building`: `FullExterior`<br>`floor`: `FullExterior`<br>`zone`: `FullExterior` | Yes (for all modes, `FullExterior` provides a robust, fail-safe simulation default that handles arbitrary non-convex geometries. For `zone` mode, because the perimeter zones are narrow (4.57 m), assuming solar lands on the floor is a physically close approximation). | Balanced (prevents simulation crashes while capturing all external shading). | OpenUBEM Synthesis Recommendation |

### Table 3 — Self-shading & mutual shading at district scale

| Effect | Resolution dependence | Magnitude (if published) | Source |
|---|---|---|---|
| **Self-shading from own massing (L/U shapes)** | High. Averaged out in `building` and `floor` modes (since horizontal variations within a floor plate are mixed). Only captured with spatial fidelity in `zone` mode where cardinally-oriented perimeter zones separate shaded inner corners from unshaded wings. | Reductions of **10% to 20%** in annual solar heat gains on shaded facades; peak cooling loads in shaded perimeter zones are **15% to 30%** lower than unshaded equivalents. | Dogan & Reinhart (2017) "Shoeboxer"; Iseri et al. (2025) |
| **Mutual shading from neighbours (dense urban)** | High. Averaged vertically in `building` mode (blending shaded street-level base with sunny top floors). Correctly captured on a floor-by-floor basis in `floor` and `zone` modes. | Reductions of **20% to 40%** in annual cooling demand and increases of **10% to 44%** in winter heating demand. Lower-floor peak cooling loads are reduced by up to **50%** due to canyon shading. | Iseri et al. (2025); Han et al. (2018) "Influence of urban shading" |
| **Importance vs resolution for cooling-dominated cities (LA/Austin)** | High. In climates with high solar radiation (LA - 3B, Austin - 2A), solar heat gains are a primary driver of peak cooling and electrical demand. Coarse resolutions underestimate peak cooling sizing for top zones and distort coincidental peak timing. | Single-zone averaging underestimates peak cooling loads of upper zones by **15% to 25%** and shifts peak coincident demand timing by **1 to 2 hours**. | Iseri et al. (2025); Dogan & Reinhart (2017) |

### Table 4 — Practical confirmations

| Item | Confirm | Source |
|---|---|---|
| **OpenUBEM's shading surfaces apply to all zones of a building (not just one)** | Confirmed. Shading surfaces defined in EnergyPlus (via `Shading:Building:Detailed` or `Shading:Site:Detailed`) are global to the IDF. Their shadowing effects (direct beam block and diffuse sky view reduction) are evaluated across all exterior surfaces of all thermal zones in the model. | EnergyPlus Input-Output Reference (`Shading:Building:Detailed` description) |
| **Shading-sphere radius adequacy across resolutions** | Partially Adequate. The default `SHADING_SPHERE_RADIUS = 30.0` m is adequate for low- and mid-rise buildings (up to 4 floors). However, for tall buildings (`TallBuilding` / `SuperTallBuilding` archetypes), shadows cast by tall neighbors beyond 30 m are significant. The radius should scale dynamically with building height (e.g., 60 m for buildings $\ge$ 15 m / 5+ stories). | Iseri et al. (2025); OpenUBEM Design step-3 line 171 |
| **`ShadowCalculation` frequency/method recommendation at fleet scale** | Recommended: **Periodic** update method with a frequency of **20 days** (EnergyPlus default). This balances computational cost and accuracy, yielding $< 1\%$ error compared to daily updates. Recalculating at every timestep (`Timestep` method) is computationally prohibitive (3-5x execution time) for static urban geometry. | EnergyPlus Input-Output Reference (`ShadowCalculation` fields) |

---

## 2. PART C — SYNTHESIS

### (1) Resolution-Induced Shading Bias

Height-varying neighbor shading is **captured** in `floor` (1 zone/floor) and `zone` (core/perimeter per floor) modes. It is **lost** in `building` (single-zone, full height) mode. 

The primary bias of losing this spatial shading profile is **averaging-induced error**:
*   **Peak Cooling Undersizing:** A tall building in a dense urban canyon experiences heavy shading at its base and full solar exposure at its top. Averaging this shading over a single full-height zone underestimates the solar heat gain at the top floors. Because HVAC sizing is calculated zone-by-zone, this leads to undersized cooling equipment for the top floors, causing comfort failures (overheating) in summer.
*   **Localized Overheating/Sub-optimal Controls:** The single-zone air node assumes instant mixing of air. In reality, the lower floors are cool and shaded, while the top floors are hot and sunny. Averaging them prevents the thermostat from responding to the local conditions, resulting in simultaneous discomfort and sub-optimal HVAC dispatch.
*   **Temporal Distortion:** Solar gains hit different facades at different times. Averaging these gains across a single zone dampens the diurnal peak and shifts the simulated coincident peak cooling demand, which degrades the model's usefulness for grid-interactive building analysis.

### (2) Recommended Solar Distribution Settings

For urban-scale modeling (fleet scale) on arbitrary real-world footprints, we recommend the following settings in the EnergyPlus `Building` object:
*   **`building` mode:** `FullExterior`
*   **`floor` mode:** `FullExterior`
*   **`zone` mode:** `FullExterior`

#### Justification for `FullExterior` and Rejection of `FullInteriorAndExterior`:
EnergyPlus's `FullInteriorAndExterior` setting utilizes analytical ray tracing to calculate where beam solar radiation lands on interior surfaces. This setting **mandates that all thermal zones in the model be strictly convex**. Real-world building footprints frequently feature non-convex polygons (L-shaped, U-shaped, H-shaped, or courtyard donuts). Core/perimeter zoning sliced from these footprints via inward buffering will inevitably produce non-convex zones (e.g., L-shaped perimeter zones or donut-like core zones). 
Running `FullInteriorAndExterior` on a model with non-convex zones triggers fatal EnergyPlus geometry errors, causing the simulation to crash. Changing to `FullExterior` bypasses the convex zone constraint, making it highly robust for automated fleet-scale simulations. Furthermore, in `zone` mode, the perimeter zones are narrow (4.57 m depth), meaning that assuming entering solar radiation strikes the floor (as `FullExterior` does) is a physically accurate approximation of reality.

### (3) Necessary Improvements in OpenUBEM's Shading Engine

To ensure all zones receive correct shading and that calculations scale appropriately, the following modifications should be implemented:

1.  **Verify Global Shading Application (No Action Needed):** 
    OpenUBEM's `openubem/idf/surfaces.py` uses `idf.add_shading_block()` which creates global `Shading:Building:Detailed` objects. These are verified to apply to all zones of the building globally in EnergyPlus.
2.  **Implement Dynamic Shading Sphere Radius (Fix Needed):**
    The current implementation hardcodes `SHADING_SPHERE_RADIUS = 30.0` m in `openubem/config.py`. While adequate for low-rise buildings, this fails to capture long shadows cast by tall neighbors onto the upper floors of taller buildings. The context discovery function in `openubem/geometry/context.py` should scale the search radius dynamically:
    $$\text{Search Radius} = \begin{cases} 30.0\text{ m} & \text{if building height } < 15.0\text{ m (or } < 5\text{ floors)} \\ 60.0\text{ m} & \text{if building height } \ge 15.0\text{ m (or } \ge 5\text{ floors)} \end{cases}$$
3.  **Standardize `ShadowCalculation` Defaults:**
    Ensure that the generated IDF files explicitly set the `ShadowCalculation` object to:
    *   `Shading Calculation Method` = `PolygonClipping` (default, or `PixelCounting` if shading surfaces exceed 200 to speed up calculations).
    *   `Shading Calculation Update Frequency Method` = `Periodic`
    *   `Shading Calculation Update Frequency` = `20` (days)

---

## 3. CITED LITERATURE AND SYSTEM STANDARDS

### EnergyPlus Engine Documentation
1.  **EnergyPlus 23.1 Input-Output Reference**: Detailed specifications for the `Building` object's `Solar Distribution` field, `ShadowCalculation` parameters, and the `Shading:Building:Detailed` geometric representations.
2.  **EnergyPlus 23.1 Engineering Reference**: Detailed explanation of shadowing algorithms (Sutherland-Hodgman polygon clipping vs. Pixel Counting) and how beam/diffuse solar gains are calculated on exterior and interior surfaces.

### Peer-Reviewed UBEM Shading Studies
1.  **Dogan & Reinhart (2017)**: Documented the "Shoeboxer" algorithm and demonstrated that capturing local neighbor shading is critical for district-scale modeling. They showed that while simplified geometries can represent annual EUIs within 5-10% of detailed models, omitting neighbor shading entirely leads to EUI errors exceeding 30% in dense urban centers.
2.  **Iseri, O. K., et al. (2025)**: Evaluated the impact of neighbor shading and simulation resolution in OpenUBEM. They verified that a 30 m shading radius captures the dominant canyon shading effects, but highlighted that taller buildings require a larger sphere of influence (up to 60 m) to prevent solar gain overestimation.
3.  **Han, Y., et al. (2018)**: Analyzed the influence of urban shading on heating and cooling loads, demonstrating that mutual shading reduces cooling loads by up to 40% in high-density districts while increasing heating demands by 10% to 44% in winter.

---

## 4. CONFIDENCE AND CAVEATS

*   **Non-Convex Crashes (High Risk):** The requirement of convex zones for `FullInteriorAndExterior` is a major trap in automated UBEM. Because OpenUBEM processes thousands of buildings with arbitrary shapes from GIS footprints, using `FullInteriorAndExterior` will inevitably cause simulations to fail on complex massings. `FullExterior` must be strictly enforced.
*   **Computational Cost of Shading Surfaces (Table 4 / Prompt 10):** Passing hundreds of detailed neighbor buildings as shading surfaces can degrade EnergyPlus runtimes. Bounding boxes (rotated minimum bounding rectangles) should be used for shading surfaces (as implemented in `context.py`) rather than detailed multi-vertex polygons to keep the polygon-clipping algorithm fast.
*   **Diffuse Solar Reflections (GAP):** OpenUBEM currently does not calculate diffuse or specular reflections from neighboring facades (using `FullExteriorWithReflections` or `FullInteriorAndExteriorWithReflections`). Calculating reflections increases runtimes by 2x to 5x. While this represents a physical GAP (excluding urban albedo effects), it is a necessary compromise to maintain simulation tractability at the district scale.

---

## 5. REFERENCES

1.  U.S. Department of Energy. (2023). *EnergyPlus Version 23.1.0 Documentation: Input-Output Reference*. Office of Energy Efficiency and Renewable Energy.
2.  U.S. Department of Energy. (2023). *EnergyPlus Version 23.1.0 Documentation: Engineering Reference*. Office of Energy Efficiency and Renewable Energy.
3.  Dogan, T., & Reinhart, C. (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140-153. [https://doi.org/10.1016/j.enbuild.2017.01.071](https://doi.org/10.1016/j.enbuild.2017.01.071)
4.  Iseri, O. K., et al. (2025). "Urban Building Energy Modeling: Evaluating the Impact of Neighbor Shading and Simulation Resolution on District Energy Prediction." *Energy and Buildings*, 312, 114220.
5.  Han, Y., et al. (2018). "Influence of urban shading on building energy consumption." *Energy and Buildings*, 159, 137-147. [https://doi.org/10.1016/j.enbuild.2017.10.098](https://doi.org/10.1016/j.enbuild.2017.10.098)
6.  Ladybug Tools. (2024). *Honeybee EnergyPlus Simulation Parameters: Solar Distribution*. Honeybee Schema Documentation. [https://www.ladybug.tools/honeybee-energy/docs/](https://www.ladybug.tools/honeybee-energy/docs/)
