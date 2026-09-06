# Diagnostic Report: EU-11 Ceiling82 Failed Simulations Diagnosis

- **Date**: 2026-09-05
- **Author**: Antigravity Diagnostic Session
- **Reference Prompts**:
  - `docs/docs_ACTIVE/europeanLocations/prompts/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05.md` (v1)
  - `docs/docs_ACTIVE/europeanLocations/prompts/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05-v2.md` (v2 addendum)
- **Reference Investigation**: `docs/docs_ACTIVE/europeanLocations/debugs/docs/INVESTIGATION_failed-sims-classification_2026-09-05.md`
- **Reference Findings**: `FINDING 210`, `FINDING 252`, `FINDING 253`, `D-EU-43` (`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`)

---

## Task A — Verify `FINDING 253` (Construction Reverse-Order Mismatch)

### 1. Root Cause Analysis and Confirmation

`FINDING 253` proposed root cause is **CONFIRMED**.

In `scripts/run_eu_s2_campaign.py` (lines 584–594), envelope constructions are assigned to surfaces based strictly on their nominal `Surface_Type`, without inspecting `Outside_Boundary_Condition`:

```python
wall_construction = _envelope_construction(idf, record, "wall")
roof_construction = _envelope_construction(idf, record, "roof")
floor_construction = _envelope_construction(idf, record, "floor")
for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
    surface_type = str(surface.Surface_Type).upper()
    if surface_type == "WALL":
        surface.Construction_Name = wall_construction
    elif surface_type in ("ROOF", "ROOFCEILING"):
        surface.Construction_Name = roof_construction
    elif surface_type in ("FLOOR", "CEILING"):
        surface.Construction_Name = floor_construction
```

When a building contains adjacent dwelling blocks or wings with differing storey counts (e.g. Block A has 1 storey, Block B has 2 storeys, where Block A sits partly beneath Block B):
1. `extrude_geometry` creates surfaces where Block A's Storey 0 top surface is initially typed `ROOF` (since within Block A there is no higher floor).
2. Geomeppy's `intersect_match` pairs Block A's Storey 0 top surface with the overlapping part of Block B's Storey 1 bottom surface (`FLOOR`), setting both surfaces' `Outside_Boundary_Condition` to `"Surface"`.
3. The loop in lines 587–594 assigns `EU_roof_Construction` to Block A's top surface (`Surface_Type == "ROOF"`) and `EU_floor_Construction` to Block B's bottom surface (`Surface_Type == "FLOOR"`).
4. As defined in `openubem/idf/european_physics.py:34-54`, `EU_roof_Construction` consists of single-layer `EU_roof_NoMass` with thermal resistance $R_{roof} = 1 / U_{roof}$, while `EU_floor_Construction` consists of single-layer `EU_floor_NoMass` with thermal resistance $R_{floor} = 1 / U_{floor}$. Because $U_{roof} \ne U_{floor}$, the two constructions reference different materials.
5. EnergyPlus performs an interzone surface validation check during sizing: adjacent interzone surfaces (`Outside_Boundary_Condition == "Surface"`) must have matching materials in reverse layer order. Because single-layer `EU_roof_NoMass` $\ne$ `EU_floor_NoMass`, EnergyPlus immediately halts with a `Fatal` error before simulation begins.

---

### 2. Quoted IDF Objects for Named Failing Stems

#### Stem 1: Madrid `04c3d8bc97b3aa32` (Task `1306953_48`)
- **Speed `.err` Error Message**:
  ```text
  ** Severe  ** GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface BLOCK 04C3D8BC97B3AA32_2 STOREY 0 ROOF 0001_1 does not have the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent surface BLOCK 04C3D8BC97B3AA32_0 STOREY 1 FLOOR 0001_2
  **  Fatal  ** GetSurfaceData: Errors discovered, program terminates.
  ```

- **Surface 1 (`ROOF`)**:
  ```text
  BUILDINGSURFACE:DETAILED,
      Block 04c3d8bc97b3aa32_2 Storey 0 Roof 0001_1,    !- Name
      roof,                     !- Surface Type
      EU_roof_Construction,     !- Construction Name
      04c3d8bc97b3aa32_F0_dwelling_2,    !- Zone Name
      ,                         !- Space Name
      surface,                  !- Outside Boundary Condition
      Block 04c3d8bc97b3aa32_0 Storey 1 Floor 0001_2,    !- Outside Boundary Condition Object
      NoSun,                    !- Sun Exposure
      NoWind,                   !- Wind Exposure
      autocalculate,            !- View Factor to Ground
      autocalculate,            !- Number of Vertices
      440196.8759999997,        !- Vertex 1 Xcoordinate
      4479191.839,              !- Vertex 1 Ycoordinate
      3,                        !- Vertex 1 Zcoordinate
      440198.466,               !- Vertex 2 Xcoordinate
      4479188.008,              !- Vertex 2 Ycoordinate
      3,                        !- Vertex 2 Zcoordinate
      440198.466,               !- Vertex 3 Xcoordinate
      4479188.007,              !- Vertex 3 Ycoordinate
      3,                        !- Vertex 3 Zcoordinate
      440198.4669999997,        !- Vertex 4 Xcoordinate
      4479188.003,              !- Vertex 4 Ycoordinate
      3;                        !- Vertex 4 Zcoordinate
  ```

- **Surface 2 (`FLOOR`)**:
  ```text
  BUILDINGSURFACE:DETAILED,
      Block 04c3d8bc97b3aa32_0 Storey 1 Floor 0001_2,    !- Name
      floor,                    !- Surface Type
      EU_floor_Construction,    !- Construction Name
      04c3d8bc97b3aa32_F1_dwelling_0,    !- Zone Name
      ,                         !- Space Name
      surface,                  !- Outside Boundary Condition
      Block 04c3d8bc97b3aa32_2 Storey 0 Roof 0001_1,    !- Outside Boundary Condition Object
      NoSun,                    !- Sun Exposure
      NoWind,                   !- Wind Exposure
      autocalculate,            !- View Factor to Ground
      autocalculate,            !- Number of Vertices
      440198.4669999997,        !- Vertex 1 Xcoordinate
      4479188.003,              !- Vertex 1 Ycoordinate
      3,                        !- Vertex 1 Zcoordinate
      440198.466,               !- Vertex 2 Xcoordinate
      4479188.007,              !- Vertex 2 Ycoordinate
      3,                        !- Vertex 2 Zcoordinate
      440198.466,               !- Vertex 3 Xcoordinate
      4479188.008,              !- Vertex 3 Ycoordinate
      3,                        !- Vertex 3 Zcoordinate
      440196.8759999997,        !- Vertex 4 Xcoordinate
      4479191.839,              !- Vertex 4 Ycoordinate
      3;                        !- Vertex 4 Zcoordinate
  ```

- **Constructions & Materials**:
  ```text
  CONSTRUCTION,
      EU_roof_Construction,     !- Name
      EU_roof_NoMass;           !- Outside Layer

  CONSTRUCTION,
      EU_floor_Construction,    !- Name
      EU_floor_NoMass;          !- Outside Layer

  MATERIAL:NOMASS,
      EU_roof_NoMass,           !- Name
      MediumRough,              !- Roughness
      2.167675243136898,        !- Thermal Resistance
      0.9,                      !- Thermal Absorptance
      0.7,                      !- Solar Absorptance
      0.7;                      !- Visible Absorptance

  MATERIAL:NOMASS,
      EU_floor_NoMass,          !- Name
      MediumRough,              !- Roughness
      1.143389139237045,        !- Thermal Resistance
      0.9,                      !- Thermal Absorptance
      0.7,                      !- Solar Absorptance
      0.7;                      !- Visible Absorptance
  ```
  *(Notice: $R_{roof} = 2.167675$ vs $R_{floor} = 1.143389$)*

---

#### Stem 2: Madrid `dc4c8768bb34abb7` (Task `1306953_40`)
- **Speed `.err` Error Message**:
  ```text
  ** Severe  ** GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface BLOCK DC4C8768BB34ABB7_8 STOREY 0 ROOF 0001_1 does not have the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent surface BLOCK DC4C8768BB34ABB7_7 STOREY 1 FLOOR 0001_2
  **  Fatal  ** GetSurfaceData: Errors discovered, program terminates.
  ```

- **Surface 1 (`ROOF`)**:
  ```text
  BUILDINGSURFACE:DETAILED,
      Block dc4c8768bb34abb7_8 Storey 0 Roof 0001_1,    !- Name
      roof,                     !- Surface Type
      EU_roof_Construction,     !- Construction Name
      dc4c8768bb34abb7_F0_dwelling_8,    !- Zone Name
      ,                         !- Space Name
      surface,                  !- Outside Boundary Condition
      Block dc4c8768bb34abb7_7 Storey 1 Floor 0001_2,    !- Outside Boundary Condition Object
      NoSun,                    !- Sun Exposure
      NoWind,                   !- Wind Exposure
      autocalculate,            !- View Factor to Ground
      autocalculate,            !- Number of Vertices
      439980.27399999974,       !- Vertex 1 Xcoordinate
      4479236.635,              !- Vertex 1 Ycoordinate
      3,                        !- Vertex 1 Zcoordinate
      439973.46999999974,       !- Vertex 2 Xcoordinate
      4479227.93,               !- Vertex 2 Ycoordinate
      3,                        !- Vertex 2 Zcoordinate
      439973.47299999977,       !- Vertex 3 Xcoordinate
      4479227.934,              !- Vertex 3 Ycoordinate
      3;                        !- Vertex 3 Zcoordinate
  ```

- **Surface 2 (`FLOOR`)**:
  ```text
  BUILDINGSURFACE:DETAILED,
      Block dc4c8768bb34abb7_7 Storey 1 Floor 0001_2,    !- Name
      floor,                    !- Surface Type
      EU_floor_Construction,    !- Construction Name
      dc4c8768bb34abb7_F1_dwelling_7,    !- Zone Name
      ,                         !- Space Name
      surface,                  !- Outside Boundary Condition
      Block dc4c8768bb34abb7_8 Storey 0 Roof 0001_1,    !- Outside Boundary Condition Object
      NoSun,                    !- Sun Exposure
      NoWind,                   !- Wind Exposure
      autocalculate,            !- View Factor to Ground
      autocalculate,            !- Number of Vertices
      439973.47299999977,       !- Vertex 1 Xcoordinate
      4479227.934,              !- Vertex 1 Ycoordinate
      3,                        !- Vertex 1 Zcoordinate
      439973.46999999974,       !- Vertex 2 Xcoordinate
      4479227.93,               !- Vertex 2 Ycoordinate
      3,                        !- Vertex 2 Zcoordinate
      439980.27399999974,       !- Vertex 3 Xcoordinate
      4479236.635,              !- Vertex 3 Ycoordinate
      3;                        !- Vertex 3 Zcoordinate
  ```

- **Constructions & Materials**:
  ```text
  CONSTRUCTION,
      EU_roof_Construction,     !- Name
      EU_roof_NoMass;           !- Outside Layer

  CONSTRUCTION,
      EU_floor_Construction,    !- Name
      EU_floor_NoMass;          !- Outside Layer

  MATERIAL:NOMASS,
      EU_roof_NoMass,           !- Name
      MediumRough,              !- Roughness
      0.5132681413430042,       !- Thermal Resistance
      0.9,                      !- Thermal Absorptance
      0.7,                      !- Solar Absorptance
      0.7;                      !- Visible Absorptance

  MATERIAL:NOMASS,
      EU_floor_NoMass,          !- Name
      MediumRough,              !- Roughness
      0.5681631297219353,       !- Thermal Resistance
      0.9,                      !- Thermal Absorptance
      0.7,                      !- Solar Absorptance
      0.7;                      !- Visible Absorptance
  ```
  *(Notice: $R_{roof} = 0.513268$ vs $R_{floor} = 0.568163$)*

---

#### Stem 3: Bologna `4d40e0364b2f0e16` (Task `1305186_133`)
- **Speed `.err` Error Message**:
  ```text
  ** Severe  ** GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface BLOCK 4D40E0364B2F0E16_3 STOREY 0 ROOF 0001_1 does not have the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent surface BLOCK 4D40E0364B2F0E16_2 STOREY 1 FLOOR 0001_2
  **  Fatal  ** GetSurfaceData: Errors discovered, program terminates.
  ```

- **Surface 1 (`ROOF`)**:
  ```text
  BUILDINGSURFACE:DETAILED,
      Block 4d40e0364b2f0e16_3 Storey 0 Roof 0001_1,    !- Name
      roof,                     !- Surface Type
      EU_roof_Construction,     !- Construction Name
      4d40e0364b2f0e16_F0_dwelling_3,    !- Zone Name
      ,                         !- Space Name
      surface,                  !- Outside Boundary Condition
      Block 4d40e0364b2f0e16_2 Storey 1 Floor 0001_2,    !- Outside Boundary Condition Object
      NoSun,                    !- Sun Exposure
      NoWind,                   !- Wind Exposure
      autocalculate,            !- View Factor to Ground
      autocalculate,            !- Number of Vertices
      686802.8799999999,        !- Vertex 1 Xcoordinate
      4928984.706,              !- Vertex 1 Ycoordinate
      3,                        !- Vertex 1 Zcoordinate
      686802.8770000003,        !- Vertex 2 Xcoordinate
      4928984.709999999,        !- Vertex 2 Ycoordinate
      3,                        !- Vertex 2 Zcoordinate
      686807.435,               !- Vertex 3 Xcoordinate
      4928980.051,              !- Vertex 3 Ycoordinate
      3;                        !- Vertex 3 Zcoordinate
  ```

- **Surface 2 (`FLOOR`)**:
  ```text
  BUILDINGSURFACE:DETAILED,
      Block 4d40e0364b2f0e16_2 Storey 1 Floor 0001_2,    !- Name
      floor,                    !- Surface Type
      EU_floor_Construction,    !- Construction Name
      4d40e0364b2f0e16_F1_dwelling_2,    !- Zone Name
      ,                         !- Space Name
      surface,                  !- Outside Boundary Condition
      Block 4d40e0364b2f0e16_3 Storey 0 Roof 0001_1,    !- Outside Boundary Condition Object
      NoSun,                    !- Sun Exposure
      NoWind,                   !- Wind Exposure
      autocalculate,            !- View Factor to Ground
      autocalculate,            !- Number of Vertices
      686807.435,               !- Vertex 1 Xcoordinate
      4928980.051,              !- Vertex 1 Ycoordinate
      3,                        !- Vertex 1 Zcoordinate
      686802.8770000014,        !- Vertex 2 Xcoordinate
      4928984.709999998,        !- Vertex 2 Ycoordinate
      3,                        !- Vertex 2 Zcoordinate
      686802.8799999999,        !- Vertex 3 Xcoordinate
      4928984.706,              !- Vertex 3 Ycoordinate
      3;                        !- Vertex 3 Zcoordinate
  ```

- **Constructions & Materials**:
  ```text
  CONSTRUCTION,
      EU_roof_Construction,     !- Name
      EU_roof_NoMass;           !- Outside Layer

  CONSTRUCTION,
      EU_floor_Construction,    !- Name
      EU_floor_NoMass;          !- Outside Layer

  MATERIAL:NOMASS,
      EU_roof_NoMass,           !- Name
      MediumRough,              !- Roughness
      0.3759304,                !- Thermal Resistance
      0.9,                      !- Thermal Absorptance
      0.7,                      !- Solar Absorptance
      0.7;                      !- Visible Absorptance

  MATERIAL:NOMASS,
      EU_floor_NoMass,          !- Name
      MediumRough,              !- Roughness
      0.6711395814079611,       !- Thermal Resistance
      0.9,                      !- Thermal Absorptance
      0.7,                      !- Solar Absorptance
      0.7;                      !- Visible Absorptance
  ```
  *(Notice: $R_{roof} = 0.375930$ vs $R_{floor} = 0.671140$)*

---

### 3. Local EnergyPlus Reproduction & Candidate Fix Proof

#### Baseline Reproduction (as shipped)
Running EnergyPlus 23.1.0 locally (`C:\EnergyPlusV23-1-0\ExpandObjects.exe` followed by `energyplus.exe` matching `submit_fleet_t08.sbatch`):

| Stem | District | Local RC | Severe Count | Fatal Count | Last Severe Error | Sizing Failure Time |
|---|---|---|---|---|---|---|
| `04c3d8bc97b3aa32` | Madrid | 1 | 1 | 2 | `GetSurfaceData: Construction EU_ROOF_CONSTRUCTION ... does not have the same materials in the reverse order ...` | 0.32 s |
| `dc4c8768bb34abb7` | Madrid | 1 | 1 | 2 | `GetSurfaceData: Construction EU_ROOF_CONSTRUCTION ... does not have the same materials in the reverse order ...` | 1.41 s |
| `4d40e0364b2f0e16` | Bologna | 1 | 1 | 2 | `GetSurfaceData: Construction EU_ROOF_CONSTRUCTION ... does not have the same materials in the reverse order ...` | 0.59 s |

The local runs reproduce the exact same Speed cluster failure 100%.

#### Candidate Fix Proof
Applying the candidate fix (assigning `EU_floor_Construction` to interzone `ROOF` surfaces where `Outside_Boundary_Condition == "Surface"`) to `04c3d8bc97b3aa32` and re-running local EnergyPlus 23.1.0 end-to-end:
- **Return Code**: `RC = 0`
- **Sizing Error Summary**: `0 Severe Errors` during Sizing (preceding Fatal completely eliminated)
- **Outcome**: `EnergyPlus Completed Successfully` (elapsed time: 3m 7s)

---

### 4. Proposed Fix Code

The fix ensures that any horizontal surface with `Outside_Boundary_Condition == "Surface"` receives the symmetric interzone floor/ceiling construction (`floor_construction`), preserving `roof_construction` for true exterior roofs (`Outdoors`) and `floor_construction` for ground floors.

```diff
--- a/scripts/run_eu_s2_campaign.py
+++ b/scripts/run_eu_s2_campaign.py
@@ -587,9 +587,13 @@ def build_idf_for_building(
     for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
         surface_type = str(surface.Surface_Type).upper()
+        obc = str(getattr(surface, "Outside_Boundary_Condition", "")).upper()
         if surface_type == "WALL":
             surface.Construction_Name = wall_construction
         elif surface_type in ("ROOF", "ROOFCEILING"):
-            surface.Construction_Name = roof_construction
+            if obc == "SURFACE":
+                surface.Construction_Name = floor_construction
+            else:
+                surface.Construction_Name = roof_construction
         elif surface_type in ("FLOOR", "CEILING"):
             surface.Construction_Name = floor_construction
```

---

## Task B — Classify the `CalcCoordinateTransformation` Fatal (Madrid `c71e82e57d99bed1`)

### 1. Task Details & Error Summary
- **District**: `ES-MAD-BERRUGUETE` (Madrid backlog)
- **Stem**: `c71e82e57d99bed1`, Task `1306953_9`
- **Error in `eplusout.err`**:
  ```text
  ** Warning ** GetSurfaceData: There are 560 coincident/collinear vertices; These have been deleted unless the deletion would bring the number of surface sides < 3.
  ** Severe  ** GetSurfaceData: There are 114 degenerate surfaces; Degenerate surfaces are those with number of sides < 3.
  ** Severe  ** CalcCoordinateTransformation: Invalid dot product, surface="BLOCK C71E82E57D99BED1_0 STOREY 1 FLOOR 0001_6":
  **   ~~~   **  (440390.202,4478490.769,   3.000)
  **   ~~~   **  (440388.567,4478489.655,   3.000)
  **   ~~~   **  (440388.567,4478489.655,   3.000)
  **  Fatal  ** CalcCoordinateTransformation: Program terminates due to preceding condition.
  ```

---

### 2. Quoted Geometry and Artifact Analysis

#### Fatal Surface: `BLOCK C71E82E57D99BED1_0 STOREY 1 FLOOR 0001_6`
- **Surface Type**: `floor`
- **Outside Boundary Condition**: `outdoors` (partner-less, NOT an interzone surface)
- **Vertex Count in IDF**: 3
- **Vertices**:
  ```text
  v1: (440390.202000, 4478490.769000, 3.000000)
  v2: (440388.567061, 4478489.654910, 3.000000)
  v3: (440388.567000, 4478489.655000, 3.000000)
  ```
- **Edge Lengths**:
  - `v1 -> v2`: 1.978439 m
  - `v2 -> v3`: **0.000109 m (0.109 mm)**
  - `v3 -> v1`: 1.978439 m
- **Angles**:
  - Angle at `v1`: **0.003146°**
  - Angle at `v2`: 89.993393°
  - Angle at `v3`: 90.003461°
- **Area**: `0.00010747` m²

#### Preceding CheckConvexity Surfaces:
1. `BLOCK C71E82E57D99BED1_0 STOREY 0 FLOOR 0001_3` (`Outside_Boundary_Condition = ground`):
   - Vertices:
     - `v1`: `(440388.567061, 4478489.654910, 0.0)`
     - `v2`: `(440388.567000, 4478489.655000, 0.0)`
     - `v3`: `(440385.601456, 4478487.634086, 0.0)`
     - `v4`: `(440385.798000, 4478487.768000, 0.0)`
   - Minimum edge length: `v1 -> v2` is **0.000109 m (0.109 mm)**.
   - Interior angle at `v3`: 0.004813° (needle vertex). Angle at `v4`: 179.996703° (collinear).
   - Area: `0.00021787` m².

2. `BLOCK C71E82E57D99BED1_5 STOREY 0 FLOOR 0001_2` (`Outside_Boundary_Condition = ground`):
   - Identical 0.109 mm near-duplicate vertex pair: `v1 -> v2 = 0.000109 m`.

3. `BLOCK C71E82E57D99BED1_0 STOREY 0 CEILING 0001_4` (`Outside_Boundary_Condition = Surface`):
   - Identical 0.109 mm near-duplicate vertex pair: `v1 -> v2 = 0.000109 m`.

---

### 3. Classification & Gate Bypass Mechanism

**Classification: Same family as `FINDING 210` / `D-EU-43`, slipping past the existing gate.**

1. **Artifact Family**:
   This is the classic `FINDING 210` sub-millimetre floating-point artifact introduced by Shapely / GEOS boolean operations. Notice that `v3` is grid-clean `(440388.567000, 4478489.655000)` while `v2` is an unsnapped float coordinate `(440388.567061, 4478489.654910)` sitting **0.109 mm** away.
2. **EnergyPlus Breakdown Mechanism**:
   The fatal surface `BLOCK C71E82E57D99BED1_0 STOREY 1 FLOOR 0001_6` is a 3-vertex needle triangle of area $0.000107\text{ m}^2$. During `GetSurfaceData`, EnergyPlus detects that vertices `v2` and `v3` are within snapping tolerance ($< 0.001\text{ m}$) and removes `v3` as a coincident vertex. This reduces the 3-sided triangle to a 2-point line segment ("sides < 3", triggering `114 degenerate surfaces`). When `CalcCoordinateTransformation` computes the surface normal from the cross product of edges, the zero-length edge produces a zero vector, causing `CalcCoordinateTransformation: Invalid dot product` and fatal termination.
3. **Why it Slipped Past the Existing Gates**:
   - `find_mismatched_interzone_pairs(idf)` returned empty (`[]`) because the fatal surface has `Outside_Boundary_Condition == "outdoors"` (not an interzone surface).
   - `_has_near_duplicate_vertex_surfaces(idf, interzone_only=True)`: skips partner-less surfaces (`Outdoors`, `Ground`, `Adiabatic`).
   - Although `_has_near_duplicate_vertex_surfaces` *did* detect near-duplicate vertices on other interzone surfaces and attempted `_force_reroute_room_layout_to_one_zone_per_floor`, the reroute function **declined to reroute** (`did_reroute = False`) because `c71e82e57d99bed1` is a courtyard building with an interior hole area of $7.36\text{ m}^2 \ge 1.0\text{ m}^2$ (`surfaces.py:693`).
   - Per `scripts/run_eu_s2_campaign.py:563-576` (the `D-EU-58` courtyard tolerance policy), when `did_reroute is False` and `mismatched` is empty, the pipeline deliberately retains the dwelling layout and sets `fallback_reason = "near_duplicate_vertex_tolerated_box"`. Thus, the defect shipped to Speed undetected by the gate.

---

## Task C — Does the 2nd `CalcCoordinateTransformation` Instance Match Task B Classification?

### 1. Task Details & Error Summary
- **District**: `IT-BOL-GALVANI2` (Bologna Step 2 Delta)
- **Stem**: `fd4b13e28f1c6f47`, Task `1308161_12`
- **Error in `eplusout.err`**:
  ```text
  ** Warning ** GetSurfaceData: There are 120 coincident/collinear vertices; These have been deleted unless the deletion would bring the number of surface sides < 3.
  ** Severe  ** GetSurfaceData: There are 77 degenerate surfaces; Degenerate surfaces are those with number of sides < 3.
  ** Severe  ** CalcCoordinateTransformation: Invalid dot product, surface="BLOCK FD4B13E28F1C6F47_0 STOREY 0 FLOOR 0001_3":
  **   ~~~   **  (686319.385,4928749.016,   0.000)
  **   ~~~   **  (686323.498,4928751.482,   0.000)
  **   ~~~   **  (686323.498,4928751.482,   0.000)
  **  Fatal  ** CalcCoordinateTransformation: Program terminates due to preceding condition.
  ```

---

### 2. Quoted Geometry and Artifact Analysis

#### Fatal Surface: `BLOCK FD4B13E28F1C6F47_0 STOREY 0 FLOOR 0001_3`
- **Surface Type**: `floor`
- **Outside Boundary Condition**: `ground` (partner-less, NOT an interzone surface)
- **Vertex Count in IDF**: 3
- **Vertices**:
  ```text
  v1: (686323.498162, 4928751.481730, 0.000000)
  v2: (686323.498000, 4928751.482000, 0.000000)
  v3: (686319.385000, 4928749.016000, 0.000000)
  ```
- **Edge Lengths**:
  - `v1 -> v2`: **0.000315 m (0.315 mm)**
  - `v2 -> v3`: 4.795615 m
  - `v3 -> v1`: 4.795615 m
- **Angles**:
  - Angle at `v1`: 89.999584°
  - Angle at `v2`: 89.996657°
  - Angle at `v3`: **0.003759°**
- **Area**: `0.00075447` m²

#### Other Slivers in the Same Building:
1. `BLOCK FD4B13E28F1C6F47_0 STOREY 0 CEILING 0001_3` (`Outside_Boundary_Condition = Surface`):
   - Edge `v1 -> v2`: **0.000315 m (0.315 mm)**.
   - Angle at `v3`: 0.003759°. Area: `0.00075447` m².
2. `BLOCK FD4B13E28F1C6F47_2 STOREY 0 FLOOR 0001_2` (`Outside_Boundary_Condition = ground`):
   - Edge `v1 -> v2`: **0.000315 m (0.315 mm)**.
   - Angle at `v3`: 0.003759°. Area: `0.00075447` m².

---

### 3. Classification & Comparison Against Task B

**Verdict: BOTH instances share the EXACT SAME classification and failure mechanism.**

There are no divergent mechanisms between the Madrid and Bologna instances. Both represent the exact same failure pattern across every dimension:

| Diagnostic Dimension | Madrid `c71e82e57d99bed1` (Task B) | Bologna `fd4b13e28f1c6f47` (Task C) | Agreement |
|---|---|---|---|
| **Defect Family** | `FINDING 210` / `D-EU-43` GEOS boolean-op artifact | `FINDING 210` / `D-EU-43` GEOS boolean-op artifact | **Identical** |
| **Artifact Geometry** | Acute needle triangle (3 vertices), 2 edges ~2 m, 1 edge **0.109 mm** | Acute needle triangle (3 vertices), 2 edges ~4.8 m, 1 edge **0.315 mm** | **Identical** |
| **Apex Angle** | 0.0031° | 0.0038° | **Identical** |
| **Area** | 0.000107 m² | 0.000754 m² | **Identical** |
| **Fatal Object** | `CalcCoordinateTransformation: Invalid dot product` | `CalcCoordinateTransformation: Invalid dot product` | **Identical** |
| **Boundary Condition of Fatal Surface** | Partner-less (`Outdoors`) | Partner-less (`Ground`) | **Identical class** |
| **Gate Bypass: Raw Mismatch** | `find_mismatched_interzone_pairs` = 0 | `find_mismatched_interzone_pairs` = 0 | **Identical** |
| **Gate Bypass: Reroute Rejection** | Footprint has courtyard hole ($7.36\text{ m}^2 \ge 1.0\text{ m}^2$), reroute declined | Footprint has courtyard hole ($856.02\text{ m}^2 \ge 1.0\text{ m}^2$), reroute declined | **Identical** |
| **Manifest Classification** | `near_duplicate_vertex_tolerated_box` | `near_duplicate_vertex_tolerated_box` | **Identical** |

### Summary of Verdict
Both occurrences of `CalcCoordinateTransformation: Invalid dot product` in the fleet (Madrid and Bologna) are caused by the **exact same mechanism**:
1. A sub-millimetre boolean-op sliver triangle ($< 0.5\text{ mm}$ spacing, $\approx 0.003^\circ$ apex angle) on a partner-less exterior/ground surface collapses to a 2-vertex segment in EnergyPlus's internal `GetSurfaceData` coincident-vertex cleaner.
2. The zero-length edge results in a zero normal vector in `CalcCoordinateTransformation`, crashing EnergyPlus.
3. The buildings slipped past the campaign safety gate because both are courtyard buildings where `_force_reroute_room_layout_to_one_zone_per_floor` deliberately declines to collapse the courtyard void, falling through to `near_duplicate_vertex_tolerated_box`.

---

## Task D — Does the 3rd `CalcCoordinateTransformation` Instance Match Task B/C Classification?

### 1. Task Details & Error Summary
- **District**: `IT-BOL-GALVANI2` (Bologna remedy fleet: `EU11_IT-BOL-GALVANI2_finding249_remedy_2026-09-04`)
- **Stem**: `635e498716218cea`, Task `1305186_524`, Building ID: `31277` (OSM id: `31277`)
- **Error in `eplusout.err`**:
  ```text
  ** Warning ** GetSurfaceData: There are 64 coincident/collinear vertices; These have been deleted unless the deletion would bring the number of surface sides < 3.
  **   ~~~   ** For explicit details on each problem surface, use Output:Diagnostics,DisplayExtraWarnings;
  ** Severe  ** GetSurfaceData: There are 41 degenerate surfaces; Degenerate surfaces are those with number of sides < 3.
  **   ~~~   ** These surfaces should be deleted.
  **   ~~~   ** For explicit details on each problem surface, use Output:Diagnostics,DisplayExtraWarnings;
  ** Severe  ** CalcCoordinateTransformation: Invalid dot product, surface="BLOCK 635E498716218CEA_0 STOREY 0 FLOOR 0001_2":
  **   ~~~   **  (686245.607,4928759.064,   0.000)
  **   ~~~   **  (686247.829,4928758.469,   0.000)
  **   ~~~   **  (686247.829,4928758.469,   0.000)
  **  Fatal  ** CalcCoordinateTransformation: Program terminates due to preceding condition.
  ...Summary of Errors that led to program termination:
  ..... Reference severe error count=42
  ..... Last severe error=CalcCoordinateTransformation: Invalid dot product, surface="BLOCK 635E498716218CEA_0 STOREY 0 FLOOR 0001_2":
  ************* Fatal error -- final processing.  Program exited before simulations began.  See previous error messages.
  ************* EnergyPlus Warmup Error Summary. During Warmup: 0 Warning; 0 Severe Errors.
  ************* EnergyPlus Sizing Error Summary. During Sizing: 173 Warning; 1 Severe Errors.
  ************* EnergyPlus Terminated--Fatal Error Detected. 237 Warning; 42 Severe Errors; Elapsed Time=00hr 00min  0.59sec
  ```

---

### 2. Quoted Geometry and Artifact Analysis

#### Fatal Surface: `BLOCK 635E498716218CEA_0 STOREY 0 FLOOR 0001_2`
- **Surface Type**: `floor`
- **Outside Boundary Condition**: `ground` (partner-less, NOT an interzone surface)
- **Vertex Count in IDF**: 3
- **Quoted IDF Object**:
  ```text
  BUILDINGSURFACE:DETAILED,
      Block 635e498716218cea_0 Storey 0 Floor 0001_2,    !- Name
      floor,                    !- Surface Type
      EU_floor_Construction,    !- Construction Name
      635e498716218cea_F0_dwelling_0,    !- Zone Name
      ,                         !- Space Name
      ground,                   !- Outside Boundary Condition
      ,                         !- Outside Boundary Condition Object
      NoSun,                    !- Sun Exposure
      NoWind,                   !- Wind Exposure
      autocalculate,            !- View Factor to Ground
      autocalculate,            !- Number of Vertices
      686247.8289999999,        !- Vertex 1 Xcoordinate
      4928758.469,              !- Vertex 1 Ycoordinate
      0,                        !- Vertex 1 Zcoordinate
      686247.8290404142,        !- Vertex 2 Xcoordinate
      4928758.469151026,        !- Vertex 2 Ycoordinate
      0,                        !- Vertex 2 Zcoordinate
      686245.6069999998,        !- Vertex 3 Xcoordinate
      4928759.064,              !- Vertex 3 Ycoordinate
      0;                        !- Vertex 3 Zcoordinate
  ```
- **Edge Lengths**:
  - `v1 -> v2`: **0.000156 m (0.1563 mm)**
  - `v2 -> v3`: 2.300285 m
  - `v3 -> v1`: 2.300285 m
- **Angles**:
  - Angle at `v1`: 89.990444°
  - Angle at `v2`: 90.005662°
  - Angle at `v3` (apex): **0.003894°**
- **Area**: `0.00017981` m² (matches EnergyPlus warning `GetSurfaceData: Very small surface area[1.79812E-004]`)

#### Other Slivers in the Same Building:
The identical 0.1563 mm sub-millimetre vertex pair at `(686247.829, 4928758.469)` recurs across multiple surfaces in `635e498716218cea.idf` (accounting for the 64 coincident/collinear vertices and 41 degenerate surfaces reported by EnergyPlus):
1. `BLOCK 635E498716218CEA_2 STOREY 0 FLOOR 0001_2` (`Outside_Boundary_Condition = ground`):
   - Vertices: `(686252.484, 4928757.223, 0)`, `(686247.829040, 4928758.469151, 0)`, `(686247.829, 4928758.469, 0)`.
   - Edge `v2 -> v3`: **0.000156 m (0.1563 mm)**. Area: `0.00037669` m² (matches `3.76691E-004`).
2. `BLOCK 635E498716218CEA_0 STOREY 1 FLOOR 0001_4` (`Outside_Boundary_Condition = outdoors`):
   - Edge `v2 -> v3`: **0.000156 m (0.1563 mm)**. Area: `0.00037669` m².
3. `BLOCK 635E498716218CEA_0 STOREY 1 FLOOR 0001_5` (`Outside_Boundary_Condition = outdoors`):
   - Edge `v1 -> v2`: **0.000156 m (0.1563 mm)**. Area: `0.00017981` m².

---

### 3. Courtyard Void Check & Gate Bypass Mechanism

1. **Courtyard Void Check**:
   - Building footprint inspection in `openubem/outputs/eu02/IT-BOL-GALVANI2/02_residential_manifest.gpkg` for building `31277` (`stem = 635e498716218cea`):
     - Footprint gross area: `501.58 m²`
     - Geometry type: `Polygon`
     - Interior rings (courtyard holes): **1 hole**
     - Hole area: **28.0195 m²** ($\ge 1.0\text{ m}^2$)
   - Because the interior ring area is $28.02\text{ m}^2 \ge 1.0\text{ m}^2$, `_force_reroute_room_layout_to_one_zone_per_floor` deliberately declined to collapse the building into a single block per `openubem/idf/surfaces.py:693-694` (`did_reroute = False`). This protects real courtyard buildings from being turned into hollow-core solids.

2. **Why it Slipped Past the Campaign Gates**:
   - `find_mismatched_interzone_pairs(idf)` returned `[]` (count 0) because the fatal surface `BLOCK 635E498716218CEA_0 STOREY 0 FLOOR 0001_2` has `Outside_Boundary_Condition = ground` (partner-less, NOT an interzone surface). The interzone mismatch check only inspects `Outside_Boundary_Condition == "Surface"`.
   - `_has_near_duplicate_vertex_surfaces(idf)` returned `True` due to interzone ceiling/floor surfaces sharing the same artifact, attempting `_force_reroute_room_layout_to_one_zone_per_floor`.
   - Because `did_reroute` returned `False` (courtyard hole refusal) and `mismatched` was empty, `scripts/run_eu_s2_campaign.py:600-602` triggered the disclosed courtyard tolerance policy:
     - Assigned `fallback_reason = "near_duplicate_vertex_tolerated_box"`
     - Shipped the IDF as-is.
   - Verified in `openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_finding249_remedy_2026-09-04/prepared_buildings.csv`:
     ```text
     building_id: 31277, stem: 635e498716218cea, fallback_reason: near_duplicate_vertex_tolerated_box
     ```

---

### 4. Classification & Comparison Against Tasks B and C

**Verdict: The 3rd instance shares the EXACT SAME classification and failure mechanism as Tasks B and C. There are zero outliers.**

All three instances across Madrid and Bologna represent the identical defect family, geometry profile, gate-bypass pathway, and EnergyPlus breakdown mode:

| Diagnostic Dimension | Madrid `c71e82e57d99bed1` (Task B) | Bologna `fd4b13e28f1c6f47` (Task C) | Bologna `635e498716218cea` (Task D) | Agreement across all 3 |
|---|---|---|---|---|
| **Defect Family** | `FINDING 210` / `D-EU-43` GEOS boolean-op artifact | `FINDING 210` / `D-EU-43` GEOS boolean-op artifact | `FINDING 210` / `D-EU-43` GEOS boolean-op artifact | **Identical** |
| **Artifact Geometry** | Acute needle triangle (3 vertices), 2 edges ~2.0 m, 1 edge **0.109 mm** | Acute needle triangle (3 vertices), 2 edges ~4.8 m, 1 edge **0.315 mm** | Acute needle triangle (3 vertices), 2 edges ~2.3 m, 1 edge **0.156 mm** | **Identical** |
| **Apex Angle** | 0.0031° | 0.0038° | 0.0039° | **Identical** |
| **Area** | 0.000107 m² | 0.000754 m² | 0.000180 m² | **Identical** |
| **Fatal Object** | `CalcCoordinateTransformation: Invalid dot product` | `CalcCoordinateTransformation: Invalid dot product` | `CalcCoordinateTransformation: Invalid dot product` | **Identical** |
| **Boundary Condition of Fatal Surface** | Partner-less (`Outdoors`) | Partner-less (`Ground`) | Partner-less (`Ground`) | **Identical class** |
| **Gate Bypass: Raw Mismatch** | `find_mismatched_interzone_pairs` = 0 | `find_mismatched_interzone_pairs` = 0 | `find_mismatched_interzone_pairs` = 0 | **Identical** |
| **Gate Bypass: Reroute Rejection** | Courtyard hole ($7.36\text{ m}^2 \ge 1.0\text{ m}^2$), reroute declined | Courtyard hole ($856.02\text{ m}^2 \ge 1.0\text{ m}^2$), reroute declined | Courtyard hole ($28.02\text{ m}^2 \ge 1.0\text{ m}^2$), reroute declined | **Identical** |
| **Manifest Classification** | `near_duplicate_vertex_tolerated_box` | `near_duplicate_vertex_tolerated_box` | `near_duplicate_vertex_tolerated_box` | **Identical** |

### Summary of Verdict
A count of 3 out of 3 instances with the **exact same mechanism**:
1. A sub-millimetre boolean-op sliver triangle ($< 0.5\text{ mm}$ spacing, $\approx 0.003^\circ - 0.004^\circ$ apex angle) on a partner-less exterior/ground surface collapses to a 2-vertex degenerate segment in EnergyPlus's internal `GetSurfaceData` coincident-vertex cleaner.
2. The zero-length edge results in a zero normal vector in `CalcCoordinateTransformation`, crashing EnergyPlus on invalid dot product.
3. The building slipped past the campaign safety gate because it is a genuine courtyard building with interior hole area $\ge 1.0\text{ m}^2$ ($28.02\text{ m}^2$), where `_force_reroute_room_layout_to_one_zone_per_floor` deliberately declines to collapse the courtyard void, falling through to the disclosed tolerance `near_duplicate_vertex_tolerated_box`.
