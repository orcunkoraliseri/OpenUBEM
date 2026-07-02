# RESULT 07 — FENESTRATION & WWR placement across resolution modes

This document provides a comprehensive methodology and parameter database for applying Window-to-Wall Ratio (WWR) and fenestration geometry across OpenUBEM's three simulation resolution modes: `building` (single-zone), `floor` (one zone per floor), and `zone` (core/perimeter).

---

## REQUIRED OUTPUT TABLES

### Table 1 — WWR application rule per mode

| Mode | Which walls glaze | WWR applied to | Resulting total glazing area vs other modes | Source |
|---|---|---|---|---|
| `building` (1 zone full height) | All exterior walls (boundary condition `Outdoors`), full height | Archetype WWR | Mathematically identical to other modes ($W \cdot A_{ext}$) | Geomeppy `set_wwr()` behavior on a single extruded volume |
| `floor` (1 zone/floor) | Each floor's exterior walls (boundary condition `Outdoors`) | Archetype WWR | Mathematically identical to other modes ($W \cdot A_{ext}$) | Geomeppy `set_wwr()` behavior on floor-by-floor stacked zones |
| `zone` (core/perimeter) | Perimeter zone exterior walls only; core zone WWR = 0 | Archetype WWR | Mathematically identical to other modes ($W \cdot A_{ext}$) | OpenUBEM core/perimeter zoning definition and geomeppy `set_wwr()` |

> **Comparability Check:** The same building **does** get the same total glazing area in all three modes because geomeppy's `set_wwr()` applies the window-to-wall ratio as a direct multiplier to each individual exterior wall surface. Since the sum of the exterior wall areas is conserved ($\sum A_{wall, i} = A_{ext}$), the sum of the window areas is also conserved ($\sum W \cdot A_{wall, i} = W \cdot A_{ext}$). However, geometric gotchas (e.g., small wall segments or non-rectangular walls) can break this in practice if not corrected (see Part C).

---

### Table 2 — Archetype WWR and window geometry (DOE prototype basis)

| Archetype | Prototype WWR (%) | Sill / head height (m) | Orientation-specific WWR? | Source |
|---|---|---|---|---|
| **SmallOffice** | 21.2% (Prototype) / 40.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No (Uniform across all facades) | PNNL-20405, DOE Prototype |
| **MediumOffice** | 33.0% (Prototype) / 40.0% (90.1 Baseline) | Sill: 0.76 m (2.5 ft)<br>Head: 1.98 m (6.5 ft) | No (Uniform across all facades) | PNNL-20405, DOE Prototype |
| **LargeOffice** | 38.1% (Prototype) / 40.0% (90.1 Baseline) | Sill: 0.76 m (2.5 ft)<br>Head: 1.98 m (6.5 ft) | No (Uniform across all facades) | PNNL-20405, DOE Prototype |
| **RetailStandalone** | 7.1% (Prototype) / 18.0% (90.1 Baseline) | Sill: 0.46 m (1.5 ft)<br>Head: 1.98 m (6.5 ft) | **Yes** (South/Front facade: 28% WWR; others: 0% WWR) | PNNL-20405, DOE Prototype |
| **MidriseApartment** | 15.0% (Prototype) / 30.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No (Uniform across all facades) | PNNL-20405, DOE Prototype |
| **HighriseApartment** | 15.0% (Prototype) / 30.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No (Uniform across all facades) | PNNL-20405, DOE Prototype |
| **Hospital** | 27.5% (Prototype) / 27.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.44 m (8.0 ft) | No (Uniform across all facades) | PNNL-20405, DOE Prototype |
| **PrimarySchool** | 35.0% (Prototype) / 28.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.44 m (8.0 ft) | No (Uniform across all facades) | PNNL-20405, DOE Prototype |
| **Warehouse** | 0.71% (Prototype) / 6.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | **Yes** (Office portion of Front facade only; warehouse: 0% WWR) | PNNL-20405, DOE Prototype |
| **SmallOfficeDetailed** | 21.2% (Prototype) / 40.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | PNNL-20405, DOE Prototype |
| **MediumOfficeDetailed** | 33.0% (Prototype) / 40.0% (90.1 Baseline) | Sill: 0.76 m (2.5 ft)<br>Head: 1.98 m (6.5 ft) | No | PNNL-20405, DOE Prototype |
| **LargeOfficeDetailed** | 38.1% (Prototype) / 40.0% (90.1 Baseline) | Sill: 0.76 m (2.5 ft)<br>Head: 1.98 m (6.5 ft) | No | PNNL-20405, DOE Prototype |
| **RetailStripmall** | 10.5% (Prototype) / 18.0% (90.1 Baseline) | Sill: 0.00 m (0.0 ft)<br>Head: 2.13 m (7.0 ft) | **Yes** (South/Front facade: 42% WWR; others: 0% WWR) | PNNL-20405, DOE Prototype |
| **SuperMarket** | 11.0% (Prototype) / 7.0% (90.1 Baseline) | Sill: 0.30 m (1.0 ft)<br>Head: 2.13 m (7.0 ft) | **Yes** (East/South facades only; others: 0% WWR) | PNNL-20405, DOE Prototype |
| **FullServiceRestaurant** | 18.0% (Prototype) / 28.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | **Yes** (South and East facades only) | PNNL-20405, DOE Prototype |
| **QuickServiceRestaurant** | 15.0% (Prototype) / 28.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | **Yes** (South and East facades only) | PNNL-20405, DOE Prototype |
| **SmallHotel** | 11.0% (Prototype) / 24.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No (Uniform across guest-room zones) | PNNL-20405, DOE Prototype |
| **LargeHotel** | 27.0% (Prototype) / 34.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | PNNL-20405, DOE Prototype |
| **Outpatient** | 20.0% (Prototype) / 21.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | PNNL-20405, DOE Prototype |
| **SecondarySchool** | 33.0% (Prototype) / 28.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | PNNL-20405, DOE Prototype |
| **College** | 30.0% (Prototype) / 28.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | PNNL-20405, DOE Prototype |
| **Courthouse** | 40.0% (OpenUBEM / 90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | OpenUBEM Default (LargeOffice proxy) |
| **Laboratory** | 30.0% (OpenUBEM / 90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.44 m (8.0 ft) | No | OpenUBEM Default (Hospital proxy) |
| **SmallDataCenterHighITE** | 0.0% | N/A | No (No windows) | PNNL-20405, DOE Prototype |
| **SmallDataCenterLowITE** | 0.0% | N/A | No (No windows) | PNNL-20405, DOE Prototype |
| **LargeDataCenterHighITE** | 0.0% | N/A | No (No windows) | PNNL-20405, DOE Prototype |
| **LargeDataCenterLowITE** | 0.0% | N/A | No (No windows) | PNNL-20405, DOE Prototype |
| **TallBuilding** | 40.0% (OpenUBEM / 90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | OpenUBEM Default (LargeOffice proxy) |
| **SuperTallBuilding** | 40.0% (OpenUBEM / 90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | OpenUBEM Default (LargeOffice proxy) |
| **OpenUBEMUnknown** | 40.0% (90.1 Baseline) | Sill: 0.91 m (3.0 ft)<br>Head: 2.13 m (7.0 ft) | No | OpenUBEM Fallback default |

---

### Table 3 — Solar & daylight consequences of placement

| Effect | `building` (tall band) | `floor` (strips) | `zone` (perimeter only) | Source |
|---|---|---|---|---|
| **Solar gain total** | Concentrated in a single vertically centered band. If no shading is present, total solar transmission is equal. However, external shading calculations are distorted because low-rise neighboring buildings may fail to shade the elevated central window. | Distributed as individual floor strips. Realistically captures variations in surrounding shading heights. | Distributed on perimeter exterior walls. Correctly resolves shading and solar transmission at the floor level. | EnergyPlus Engineering Reference: Solar Distribution & Shadowing |
| **Solar gain distribution** | All solar gains enter a single zone and are immediately mixed across the entire building volume, artificially cooling/heating the whole building. | Solar gains are isolated floor-by-floor, heating up specific levels and resolving vertical temperature stratification. | Solar gains are isolated to perimeter zones. Core zones remain unaffected by direct solar, capturing the true thermodynamic imbalance between core and perimeter. | EnergyPlus Engineering Reference: Solar Distribution & Shadowing |
| **Daylight availability** | Centralized window band leaves top and bottom floors dark while over-illuminating the middle. Daylighting controls apply to the entire building volume. | Daylighting is resolved on each floor, but controls apply to the entire floor area (averaging out daylighting benefits). | Daylighting is restricted to perimeter zones (depth 4.57 m) where it actually occurs. Highly realistic modeling of daylight-responsive lighting controls. | EnergyPlus Engineering Reference: Daylighting Calculations |
| **Self-shading / overhang effects** | Overhangs placed at intermediate floor levels intersect with the giant centered window, causing geometric errors in EnergyPlus and incorrect shading. | Overhangs are correctly positioned above each floor's window strip, shading each zone realistically. | Overhangs are correctly positioned above each floor's perimeter windows, shading the perimeter zones realistically. | EnergyPlus Engineering Reference: Shading / E+ I/O Reference |

---

### Table 4 — Conservation & comparability rule

| Item | Rule | Source |
|---|---|---|
| **Keep total glazing area equal across modes?** | **Yes.** Apply the same uniform or orientation-specific WWR to all exterior walls (boundary condition `Outdoors`) in all modes. Total glazing area is conserved mathematically since $\sum A_{wall, i} = A_{ext}$. | Geomeppy geometry model; conservation of exterior wall area. |
| **If not equal, the intended interpretation** | N/A (glazing area is kept equal, but the localized distribution in `zone` mode is physically "more correct" for local heat and daylighting). | EnergyPlus Engineering Reference. |
| **Default WWR when archetype/source is silent** | 40% (0.40) for commercial/non-residential archetypes, 20% (0.20) for residential, and 0% (0.00) for data centers/warehouses. | ASHRAE 90.1-2019 Section 5.5.4.2.1 / Appendix G baseline limits. |

---

## Part C — Synthesis (Rule Block)

### WWR-Application Rule Block for OpenUBEM

To maintain strict physical comparability and simulation stability across the three resolution modes, the following rules must be implemented in the IDF geometry builder:

```python
# Pseudo-implementation of WWR consistency and error protection
def apply_simulation_resolution_wwr(idf, mode, archetype_wwr, min_wall_width=0.5, min_wall_area=1.5):
    """
    Applies WWR to IDF surfaces based on simulation resolution mode with safety guards.
    """
    # 1. Map archetype WWR (uniform or orientation-specific map)
    # 2. Iterate over all surfaces
    for wall in idf.getsurfaces('wall'):
        # Only operate on exterior walls
        if wall.Outside_Boundary_Condition.lower() != 'outdoors':
            continue
            
        # protection against non-rectangular walls (gables, triangular surfaces)
        # geomeppy set_wwr has a known bug placing window vertices outside sloped boundaries
        if not is_rectangular(wall):
            # Fall back to setting WWR = 0 on non-rectangular walls to prevent E+ fatal crash
            continue
            
        # protection against narrow/degenerate wall segments generated by core/perimeter zoning
        if get_wall_width(wall) < min_wall_width or get_wall_area(wall) < min_wall_area:
            # Skip glazing on small surfaces to avoid collinear window vertices
            continue
            
        # Apply WWR based on mode
        if mode == 'building':
            # Applied to the single full-height exterior wall
            # Centered window creates a single giant band
            apply_geomeppy_wwr(wall, archetype_wwr)
        elif mode == 'floor':
            # Applied to each floor's exterior walls
            apply_geomeppy_wwr(wall, archetype_wwr)
        elif mode == 'zone':
            # Core zone walls have no boundary condition 'Outdoors', so they are skipped automatically.
            # Only perimeter walls (which are Outdoors) get glazed.
            apply_geomeppy_wwr(wall, archetype_wwr)
```

#### Detailed Logic and Adjustments:
1. **Mathematical Conservation:** Geomeppy's `set_wwr` operates on a per-wall basis. For any wall with surface area $A$, it creates a window with area $W \cdot A$. Since the total exterior wall area ($A_{ext}$) is identical across all three modes, the sum of window areas remains exactly $W \cdot A_{ext}$, guaranteeing that total glazing area and primary solar heat transmission are identical.
2. **Core Zone WWR = 0:** In `zone` mode, core zones have boundary conditions of `Surface` (interzone floor/ceiling or wall partitions) or `Adiabatic`. They never have `Outdoors`. Therefore, `set_wwr` naturally applies no windows to the core (WWR = 0), concentrating all glazing on the perimeter zones.
3. **Geomeppy Gotchas and Mitigations:**
   - **Gable/Non-Rectangular Walls:** Geomeppy's `set_wwr` assumes a rectangular parent surface. On triangular gables or non-rectangular walls, it calculates window vertices that protrude beyond the wall boundaries. EnergyPlus throws a fatal error: `Subsurface outside parent surface`. **Mitigation:** Exclude non-rectangular walls from automated WWR; model them as 100% opaque.
   - **Narrow / Degenerate Wall Segments:** Buffering algorithms for complex OSM footprints can create tiny wall segments at vertices. Applying `set_wwr` to these creates sub-centimeter windows, causing EnergyPlus to crash due to collinear vertices. **Mitigation:** Skip glazing on any exterior wall with width $< 0.5$ m or area $< 1.5$ m².
   - **Overhang Overlap:** Intermediate shading overhangs (e.g., floor line projections) intersect the giant centered window in `building` mode. **Mitigation:** Disable intermediate overhangs in `building` mode; keep only the roof-level overhang. Enable all floor overhangs in `floor` and `zone` modes.

---

## Confidence and Caveats

*   **Total Glazing Area Comparability (High Confidence):** The total glazing area is mathematically conserved across all modes, provided the set of exterior-facing walls is identical.
*   **Solar Heat Gain Divergence (Warning):** While the incoming solar energy is identical under unshaded conditions, the simulated cooling and heating loads will differ. In `building` mode, solar heat is mixed across the entire building volume, dampening peak demands. In `floor` and `zone` modes, solar gains are localized to specific floor and perimeter zones, resulting in higher localized peak cooling loads and realistic HVAC sizing.
*   **Daylighting Divergence (Caveat):** Daylighting-responsive lighting controls cannot be modeled realistically in `building` or `floor` modes, as the daylighting signal is averaged across the entire building or floor volume. Only `zone` mode (with isolated 4.57m perimeter zones) correctly isolates daylight availability to reduce perimeter lighting energy.

---

## References

1. **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL)**. *Commercial Prototype Building Models*. BECP. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
2. **Thornton, D. R., et al. (2011)**. *Achieving the 30% Energy Savings Target: Support Document for ASHRAE Standard 90.1-2010*. Pacific Northwest National Laboratory. PNNL-20405. [https://www.pnnl.gov/main/publications/external/pdf/outputs/product/pnnl-20405.pdf](https://www.pnnl.gov/main/publications/external/pdf/outputs/product/pnnl-20405.pdf)
3. **ANSI/ASHRAE/IES Standard 90.1-2019**. *Energy Standard for Buildings Except Low-Rise Residential Buildings*. Section 5 (Envelope) and Appendix G (Performance Rating Method).
4. **EnergyPlus 23.1 Engineering Reference**. *Solar Radiation and Shadowing Calculations*. Department of Energy. [https://energyplus.net/documentation](https://energyplus.net/documentation)
5. **Geomeppy Documentation**. *Recipes: set_wwr method*. [https://geomeppy.readthedocs.io/](https://geomeppy.readthedocs.io/)
