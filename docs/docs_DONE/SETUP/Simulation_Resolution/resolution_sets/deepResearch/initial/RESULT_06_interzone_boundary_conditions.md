# RESULT_06 — INTER-ZONE BOUNDARY CONDITIONS & THERMAL COUPLING

This report documents the recommended surface boundary conditions, construction assignments, and thermal coupling strategies for OpenUBEM across all resolution modes (`building`, `floor`, `zone`). The methodology balances physical accuracy against the computational cost and numerical robustness required for urban-scale energy modeling.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Boundary condition per internal surface type

| Internal surface | Appears in mode(s) | Recommended boundary condition | Construction | Source |
|---|---|---|---|---|
| Floor/ceiling between stacked floors | `floor`, `zone` | `Surface` (coupled) with automatic fallback to `Adiabatic` on mismatch | `Floor_Construction` | EnergyPlus Input-Output Reference (v23.1) & OpenUBEM `_pair_interfloor_surfaces` |
| Core ↔ perimeter vertical partition | `zone` | `Surface` (fully coupled interzone wall pairs) | `Wall_Construction` | EnergyPlus Input-Output Reference & PNNL Prototype Models (e.g. `MediumOffice`) |
| Perimeter ↔ perimeter vertical partition | `zone` | `Surface` (fully coupled interzone wall pairs) | `Wall_Construction` | EnergyPlus Input-Output Reference & PNNL Prototype Models (e.g. `Hospital`) |
| Party wall to attached neighbour | All (`building`, `floor`, `zone`) | `Adiabatic` | `Wall_Construction` (with no-heat-flow properties) | ASHRAE 90.1-2019 / DOE Prototype conventions for attached structures |
| Ground floor underside | `building`, `floor`, `zone` | `Ground` / `GroundFCfactorMethod` | `Floor_Construction` (F-factor assembly) | ASHRAE 90.1-2019 Table 6.8.1-11; PNNL Prototype models |
| Top floor roof | `building`, `floor`, `zone` | `Outdoors` | `Roof_Construction` | EnergyPlus Input-Output Reference |
| Single-zone whole-building omitted inter-floors | `building` | `InternalMass` (referenced non-geometric object) | `Floor_Construction` | EnergyPlus Input-Output Reference & Cerezo Davila et al. (2017) |

---

### Table 2 — Adiabatic vs interzone decision (the core trade)

| Surface | If Adiabatic — physical assumption + when valid | If interzone — what it captures | DOE prototype choice | Recommended |
|---|---|---|---|---|
| **Inter-floor slab** | Assumes $\Delta T \approx 0$ between storeys. Valid when stacked zones have identical setpoints, internal loads, and schedules. | Captures vertical conduction from solar gains on top floors downward, and ground cooling upward. | `Surface` (fully coupled interzone ceiling/floor pairs with plenums). | `Surface` for matched footprints; `Adiabatic` for stepped/mismatched footprints. |
| **Core↔perimeter wall** | Assumes $\Delta T \approx 0$ between core and perimeter. Valid if both are conditioned by the same HVAC system and have no solar difference (never strictly true). | Captures lateral conduction driven by exterior solar and air temperature variations in perimeter zones. | `Surface` (fully coupled interzone partition walls). | `Surface` (fully coupled interzone walls matched via `intersect_match`). |
| **Party wall** | Assumes the adjacent building is heated/cooled to the same temperature as the modeled building. | Captures thermal coupling between adjacent buildings (requires modeling neighbor zones in the same IDF). | `Adiabatic` (for all attached boundary conditions). | `Adiabatic` (critical to avoid over-predicting EUI by exposing shared walls to outdoors). |

---

### Table 3 — Inter-zone AIR exchange (not just conduction)

| Mechanism | Model it? | EnergyPlus object | When it matters | Source |
|---|---|---|---|---|
| **Open-plan air mixing core↔perimeter** | No | `ZoneMixing` / `ZoneCrossMixing` | When high convective coupling exists between core and perimeter zones. | EnergyPlus Input-Output Reference (v23.1) |
| **Stairwell / atrium stack between floors** | No | `AirflowNetwork` (AFN) / `ZoneMixing` | In tall buildings with open shafts or atriums driving stack effect. | EnergyPlus Engineering Reference |
| **Recommendation for UBEM scale** | **Ignore all inter-zone air exchange.** | N/A | AFN adds extreme runtime overhead & convergence failures. Mixing requires unvalidatable schedules. | Cerezo Davila (2017) / Reinhart (2018) |

---

### Table 4 — Robustness to real geometry

| Issue | Note | Mitigation | Source |
|---|---|---|---|
| **Matched vs unmatched interzone surfaces (vertex counts)** | OpenUBEM has hit inter-floor vertex-mismatch fatals. E+ fails if paired surfaces have mismatched coordinate counts. | Apply `_pair_interfloor_surfaces` to match identical horizontal pairs. For mismatched storeys, apply `Adiabatic`. | OpenUBEM surfaces.py; EnergyPlus Input-Output Reference |
| **`intersect_match` behaviour on stacked real footprints** | GIS polygon alignment errors can generate complex sliver surfaces, self-intersections, and winding failures. | complexity gate (`COREPERIM_COMPLEXITY_THRESHOLD = 800`) to bypass `intersect_match` for highly complex shapes. | OpenUBEM surfaces.py / geometry hardening commits (2026-06-19) |
| **When to prefer adiabatic purely for numerical robustness at scale** | Stepped building heights, setbacks, or non-aligned floor plates make 3D geometry matching computationally prohibitive. | Fall back to `Adiabatic` for floor/ceiling surfaces whenever stacked storeys do not share identical exterior boundary shapes. | Cerezo Davila, MIT PhD Thesis (2017) |

---

## 2. PART C — SYNTHESIS (RULE BLOCK)

OpenUBEM should implement the following boundary-condition rule block across its three resolution modes:

### 1. Surface Boundary Condition Rules

*   **Mode 1: `building` (Single Zone)**
    *   **Ground Floor Underside:** `Ground` or `GroundFCfactorMethod` using `Floor_Construction`.
    *   **Top Roof:** `Outdoors` (SunExposed, WindExposed) using `Roof_Construction`.
    *   **Party Walls:** `Adiabatic` using `Wall_Construction`.
    *   **Omitted Inter-floor Slabs:** Modeled via `InternalMass` referencing `Floor_Construction` and a surface area equal to `footprint_area_m2 × (num_floors − 1)`.
    *   **Exterior Walls:** `Outdoors` using `Wall_Construction`.
*   **Mode 2: `floor` (One Zone per Floor)**
    *   **Ground Floor Underside (Storey 0):** `Ground` or `GroundFCfactorMethod`.
    *   **Inter-floor Slabs (Ceiling of Storey $i$ / Floor of Storey $i+1$):**
        *   *If footprints match exactly:* `Surface` pointing to each other (using `_pair_interfloor_surfaces`).
        *   *If footprints mismatch (setbacks/cantilevers) or matching fails:* `Adiabatic` (no heat transfer).
    *   **Top Floor Roof (Storey $N-1$):** `Outdoors`.
    *   **Party Walls:** `Adiabatic` (for any vertical wall sharing a boundary with an adjacent building).
    *   **Exterior Walls:** `Outdoors`.
*   **Mode 3: `zone` (Core + Perimeter per Floor)**
    *   **Ground Floor Underside (Storey 0):** `Ground` or `GroundFCfactorMethod`.
    *   **Inter-floor Slabs:** Matched `Surface` pairs where vertically aligned; `Adiabatic` where mismatches or setbacks occur.
    *   **Core ↔ Perimeter Walls:** Matched `Surface` pairs (conductively coupled) to capture lateral heat transfer.
    *   **Perimeter ↔ Perimeter Walls:** Matched `Surface` pairs where adjacent zones share a partition.
    *   **Party Walls:** `Adiabatic`.
    *   **Exterior Walls:** `Outdoors`.

### 2. Adiabatic vs. Inter-zone Decision Logic
*   **Core ↔ Perimeter partitions must remain `Surface` (coupled).** Fully coupling core and perimeter zones is critical to capture the physical reality of building load patterns. Perimeter zones experience high solar gains and exterior conduction, while core zones are dominated by internal loads (lighting, equipment). Modeling this wall as adiabatic prevents temperature equalization, causing artificial heating in the core and cooling in the perimeter, which distorts HVAC system sizing and energy calculations.
*   **Inter-floor slabs can fall back to `Adiabatic` for robustness.** While vertical heat transfer occurs, it is secondary to horizontal conduction (since stacked zones typically run on similar HVAC setpoints). For non-convex, non-aligned, or stepped footprints, the computational overhead and fatal error risk of 3D intersection matching far outweigh the accuracy gains. OpenUBEM should attempt `Surface` matching for identical footprints but silently apply `Adiabatic` for mismatched levels or when intersection exceptions are caught.

### 3. Inter-zone Air Exchange Recommendation
*   **Do not model inter-zone air exchange.** At the UBEM scale, ignoring air mixing (via `ZoneMixing` or `ZoneCrossMixing`) is the only defensible option. The `AirflowNetwork` is numerically unstable and increases simulation time by orders of magnitude. `ZoneMixing` introduces unvalidatable parameters (such as scheduled air exchange rates) that would violate the **zero-fitted-parameters** philosophy.

---

## 3. REFERENCES AND SOURCE CITATIONS

1. **EnergyPlus™ Version 23.1.0.** *Input Output Reference* and *Engineering Reference*. U.S. Department of Energy. [https://energyplus.net/documentation](https://energyplus.net/documentation).
   *   *Outside Boundary Condition* options (`Surface`, `Adiabatic`, `Ground`, `Outdoors`).
   *   *InternalMass* object specifications for single-zone modeling.
2. **Pacific Northwest National Laboratory (PNNL) & U.S. Department of Energy.** *Commercial Prototype Building Models*. Standard 90.1-2019 / STD2022 release. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models).
   *   Conventions for setting inter-zone walls as matched `Zone`/`Surface` boundaries and ground coupling via `GroundFCfactorMethod`.
3. **Cerezo Davila, C.** (2017). *Urban Building Energy Modeling: Workflows and Algorithms for Energy Efficient Cities*. PhD Thesis, Massachusetts Institute of Technology. [https://dspace.mit.edu/handle/1721.1/111956](https://dspace.mit.edu/handle/1721.1/111956).
   *   AutoZone algorithm development and validation of simplified zoning and boundary conditions (adiabatic slab approximations for vertical stacks) at urban scale.
4. **ASHRAE.** (2019). *ANSI/ASHRAE/IES Standard 90.1-2019: Energy Standard for Buildings Except Low-Rise Residential Buildings*. Atlanta, GA: ASHRAE.
   *   Standard envelope assemblies, F-factors for slab-on-grade floors, and default interior partition thermal parameters.

---

## 4. CONFIDENCE AND CAVEATS

### The Surface Treatment That Matters Most: The Party Wall
The single most critical boundary condition in urban building energy modeling is the **party wall** separating attached structures. 
*   **The Physics:** Attached buildings share a physical wall. Since neighboring buildings are typically conditioned to similar indoor temperatures, the net heat transfer across this boundary is near zero.
*   **The Impact:** If a party wall is incorrectly modeled as `Outdoors` instead of `Adiabatic`, EnergyPlus exposes it to wind, solar radiation, and the full outdoor air temperature gradient. In row houses, brownstones, and dense urban blocks, shared walls can represent up to **50% of the building's total vertical envelope**. Modeling these shared walls as exterior surfaces causes massive over-prediction of space heating and cooling loads (often between **30% and 60%**).
*   **UBEM Implementation:** In OpenUBEM, party wall detection must be robust. Any surface that is coplanar with a neighboring building footprint must have its boundary condition flipped to `Adiabatic`. Ground floors (Z=0) must be exempt from this flip to retain their correct ground-coupled boundary conditions.
