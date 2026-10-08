# FINDING 249 — CP-2 gate 5 remedy investigation report

**Date:** 2026-09-04  
**Author:** External Reviewer / Agent (Antigravity)  
**Investigation Target:** `FINDING 249` — `scripts/run_eu_s2_campaign.py:663-665` safety net over-firing and discarding dwelling layouts on 1,306 of 2,262 emitted-family buildings (57.7%) across European districts  
**Standing Project Constraints:** `D-EU-41` (`openubem/idf/surfaces.py` strictly non-editable), `D-EU-95` (`openubem/geometry/european_nocore.py` cutting logic frozen), Hard Rule 3 (`NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005` m and `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1`° fixed)

---

## 1. Summary

The CP-2 fifth gate fails because `scripts/run_eu_s2_campaign.py:94-125` (`_has_near_duplicate_vertex_surfaces`) over-fires on benign, footprint-inherent collinear vertices, triggering `_force_reroute_room_layout_to_one_zone_per_floor` (`openubem/idf/surfaces.py:640-706`) and collapsing 1,306 valid dwelling layouts to single-zone massings. A full fleet census across all 2,262 emitted-family buildings reveals that **72.7% of the rerouted buildings (950 of 1,306)** already possess collinear vertices in their raw OSM/GIS footprints before any project geometry pipeline runs (Madrid: 88.5%, Bologna: 63.7%, London: 45.0%, Lyon: 40.3%). Ground-truth EnergyPlus 23.1.0 simulations conducted on un-rerouted real geometries confirm that 100% of tested Madrid dwelling layouts simulate with **`RC=0, 0 Fatal, 0 Severe`**; EnergyPlus cleanly handles collinear vertices when they are partner-less (ground, roof, facade) or symmetric across interzone pairs.

We recommend **Option B: Targeted Gate Refinement**. Instead of evaluating every surface ring unconditionally, `_has_near_duplicate_vertex_surfaces` should restrict the check to interzone candidate surfaces (`Outside_Boundary_Condition == "Surface"`), and require collinear defects to be *asymmetric* across paired surfaces before declaring `at_risk`. This preserves the genuine `FINDING 210` safety net against machine-precision asymmetric `intersect_match` insertions, completely stops over-firing on harmless footprint vertices, produces zero geometry mutation, guarantees exact zero area drift, and requires zero edits to `openubem/idf/surfaces.py` (`D-EU-41`) or `openubem/geometry/european_nocore.py` (`D-EU-95`).

---

## 2. Confirmation of T03's finding

The diagnostic progress log in `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-nocore-interzone-rootcause-2026-09-04.md` (§8, T03) concluded that `_symmetrize_near_duplicate_interzone_vertices` (`scripts/run_eu_s2_campaign.py:128-227`) could not resolve the reroute flag because defects were collinear, partner-less, and symmetric. We independently re-examined and verified this finding across real production geometries.

### 2.1 Re-verification on real production buildings

We rebuilt and probed the full set of 8 real reroute-labelled buildings from the T02b/T02c stratified sample (`openubem/outputs/eu_evidence/EU-21/interzone_rootcause/T02b_real_geometry_diff_2026-09-04.json`):
- `ES-MAD-BERRUGUETE`: `way/403642583`, `way/435505191`, `way/941927250`, `way/322742264`, `way/435505194`, `way/435449428`, `way/942642640`
- `FR-LYO-HAUTCOEURPENTES`: `BATIMENT0000000240879996_part0`

Every `BUILDINGSURFACE:DETAILED` surface was inspected using the exact mathematical definitions from `scripts/run_eu_s2_campaign.py:94-125`. The findings:

```
====================================================================================================
Building ID                     Dist  Storeys Zones  mismatched  near_dup  Proximity  Collinear
====================================================================================================
way/403642583                   MAD         1     1       False      True          0          3
way/435505191                   MAD         4     8       False      True          0         10
way/941927250                   MAD         1     1       False      True          0          2
way/322742264                   MAD         4     8       False      True          0         10
way/435505194                   MAD         5    11       False      True          0         12
way/435449428                   MAD         1     1       False      True          0          2
way/942642640                   MAD         3     7       False      True          0          7
BATIMENT0000000240879996_part0  LYO         6    34       False      True         36         72
====================================================================================================
```

1. **`mismatched` is 0 across all 8 buildings:** `find_mismatched_interzone_pairs(idf)` (`openubem/idf/surfaces.py:547-571`) returned empty (`False`) on 8 of 8 buildings. The raw interzone vertex-count check does not fire.
2. **In 7 of the 8 buildings (100% of Madrid buildings), 100% of defective vertices are collinear (0% proximity):** Not a single vertex pair on any surface ring was closer than `NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005` m. All flagged vertices were consecutive triples with interior angle `> 179.9°` (specifically `179.91°` to `179.9999°`).
3. **Many defective surfaces have no interzone partner:** In `way/435505191`, defective surfaces include:
   - Ground floor: `Outside_Boundary_Condition == "Ground"`, `Outside_Boundary_Condition_Object == ""`
   - Roofs: `Outside_Boundary_Condition == "Outdoors"`, `Outside_Boundary_Condition_Object == ""`
   - Exterior walls: `Outside_Boundary_Condition == "Outdoors"`, `Outside_Boundary_Condition_Object == ""`  
   `_has_near_duplicate_vertex_surfaces` (`scripts/run_eu_s2_campaign.py:105-125`) iterates over all surfaces unconditionally. These partner-less surfaces can never participate in an interzone pairing mismatch.
4. **Where partners exist, both sides carry the identical defect:** On interfloor ceiling/floor pairs in `way/435505191` and `way/322742264`, the ceiling and its paired floor carry the identical coordinate triple, identical angle (`179.9724°`), and identical vertex index. There is no floating-point asymmetry.
5. **`_symmetrize_near_duplicate_interzone_vertices` fixes 0 pairs:** Running `_symmetrize_near_duplicate_interzone_vertices(idf)` on these buildings returned `repaired = 0`. Because the coordinates on paired surfaces are already identical down to the last decimal, snapping both sides to a shared coordinate changes nothing. Furthermore, shifting a point along a straight line does not change its collinearity.

---

## 3. Characterization of the collinear population

### 3.1 Fleet-wide footprint census

To determine whether collinear vertices originate in raw GIS data or are introduced by the project pipeline, we conducted a comprehensive census across all 2,262 emitted-family buildings across the four European districts. We joined each building's `geometry_outcome` from `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_nocore_2026-09-03/prepared_buildings.csv` against its raw polygon exterior in `02_residential_manifest.gpkg`.

For each raw footprint polygon, we evaluated consecutive vertex triples for collinearity using the exact criterion `angle > 180.0 - COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (where `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1`°):

```
======================================================================================================
District            Emitted Family  Rerouted Buildings  Raw Footprint Collinear  Share of Rerouted (%)
======================================================================================================
ES-MAD-BERRUGUETE              905                 618                      547                  88.5%
IT-BOL-GALVANI2              1,032                 529                      337                  63.7%
GB-LDN-STDUNSTANS               62                  40                       18                  45.0%
FR-LYO-HAUTCOEURPENTES         280                 119                       48                  40.3%
======================================================================================================
TOTAL                        2,262               1,306                      950                  72.7%
======================================================================================================
```

**Result:** **72.7% of all rerouted buildings fleet-wide (950 of 1,306)** carry collinear vertices in their raw GIS/OSM footprints before a single line of OpenUBEM code runs. In Madrid, this figure reaches **88.5%**.

These collinear points in OSM/Cadastre data represent:
- Straight party walls or facade segments divided into multiple nodes by cadastral parcel boundaries or abutting neighbour nodes.
- Collinear vertices placed where an adjoining property line intersects a straight wall.
- Near-straight survey lines with interior angles between 179.90° and 180.00°.

### 3.2 Pipeline stages introducing the remaining 27.3%

The remaining 356 rerouted buildings (27.3%) do not carry collinear vertices in their raw footprint exterior. Detailed tracing identified two specific downstream pipeline stages that introduce defects:

1. **`cut_storey_nocore` (`openubem/geometry/european_nocore.py:1751-1777`):**  
   When the cutter divides a plate into individual dwelling units, internal dividing cut-lines terminate on external boundary edges. Shapely polygon operations (`intersection`, `difference`) insert a new vertex at the T-junction intersection on the straight boundary. The resulting flat polygon exterior ring acquires a vertex whose interior angle is exactly 180.000000° to machine precision. When extruded, this 180° vertex appears on the ceiling and floor surfaces of that flat.
2. **`_stabilize_ring_coords` (`openubem/geometry/european_residential.py:1809-1830`):**  
   `_stabilize_ring_coords` executes `shapely.set_precision(poly, grid_size=0.001)`. Snapping non-orthogonal or curved polygon edges to a 1 mm integer lattice introduces small "staircase" steps. In complex geometries such as Lyon's `BATIMENT0000000240879996_part0`, consecutive vertices along a stepped diagonal edge can be separated by ~1.4 mm, which falls below `NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005` m (5 mm), generating proximity flags.

### 3.3 Ground-truth EnergyPlus 23.1.0 simulations

To test whether footprint-inherent collinear vertices actually cause EnergyPlus simulation failures, we bypassed `_force_reroute_room_layout_to_one_zone_per_floor` and executed the local EnergyPlus 23.1.0 binary (`C:\EnergyPlusV23-1-0\energyplus.exe`) directly on the un-rerouted dwelling-layout IDFs for all 8 sample buildings.

Weather files and simulation parameters matched production (`submit_fleet_t08.sbatch` invocation):

```
====================================================================================================
Building ID                     District Zones   E+ Run Result   Fatal  Severe  Simulation Notes
====================================================================================================
way/403642583                   MAD          1   RC=0 (PASS)         0       0  2.26s, clean
way/435505191                   MAD          8   RC=0 (PASS)         0       0  12.48s, heating=64,956 kWh
way/941927250                   MAD          1   RC=0 (PASS)         0       0  1.99s, clean
way/322742264                   MAD          8   RC=0 (PASS)         0       0  13.18s, heating=93,128 kWh
way/435505194                   MAD         11   RC=0 (PASS)         0       0  16.77s, heating=72,774 kWh
way/435449428                   MAD          1   RC=0 (PASS)         0       0  2.25s, clean
way/942642640                   MAD          7   RC=0 (PASS)         0       0  9.02s, heating=14,439 kWh
BATIMENT0000000240879996_part0  LYO         34   RC=0 (Severe)       0      46  36 degenerate surfaces
====================================================================================================
```

**Key Simulation Findings:**
- **7 of 7 Madrid buildings (100%) simulated with 0 Fatal / 0 Severe:** Buildings with up to 11 per-dwelling zones and multiple collinear vertices on roofs, ground floors, and interzone ceilings/floors ran with total numerical stability. Collinear vertices in raw footprints and cut T-junctions **do not crash EnergyPlus** when surfaces are partner-less or symmetrically matched.
- **The Lyon building (`BATIMENT0000000240879996_part0`):** Completed with `RC=0` and 0 Fatal, but logged 46 Severe warnings. Inspection of `eplusout.err` confirmed that these warnings were caused by 36 degenerate surfaces on upper storeys (F4/F5) resulting from 1 mm grid snapping creating vertices < 5 mm apart along complex curved perimeter cuts.

### 3.4 Existing production precedent: `near_duplicate_vertex_tolerated_box`

An important operational precedent already exists in the codebase (`scripts/run_eu_s2_campaign.py:676-697`, introduced under `FINDING 220`/`D-EU-58`). When `_force_reroute_room_layout_to_one_zone_per_floor` is invoked on a holed courtyard polygon, `openubem/idf/surfaces.py:694` deliberately declines to reroute (`did_reroute = False`) to prevent creating a donut massing block. In that scenario, `scripts/run_eu_s2_campaign.py:694-696` executes:

```python
if not did_reroute and not mismatched:
    for _z in zones:
        _z["fallback_reason"] = "near_duplicate_vertex_tolerated_box"
```

In the current fleet, **370 buildings** were emitted under this exact rule with `fallback_reason = "near_duplicate_vertex_tolerated_box"`. They retained their full dwelling layouts despite triggering `_has_near_duplicate_vertex_surfaces`. In the production cluster run on Speed (`D-EU-98`), **100% of these 370 buildings simulated successfully with 0 Fatal**.

---

## 4. Options considered

### 4.1 Option A: Upstream collinear vertex removal before extrusion

- **File and Lines:** `openubem/geometry/european_residential.py:1809-1830` (`_stabilize_ring_coords`) and/or `openubem/geometry/european_nocore.py:1751-1777` (`cut_storey_nocore`).
- **Concept:** Remove collinear vertices from polygon boundary rings using `shapely.simplify(poly, tolerance=0.005, preserve_topology=True)` or Douglas-Peucker filtering before zones are converted to IDF coordinates.
- **Compliance with `D-EU-41`:** Complies (`openubem/idf/surfaces.py` is untouched).
- **Compliance with `D-EU-95`:** **Fails.** Touching `openubem/geometry/european_nocore.py`'s cutting logic violates `D-EU-95` (frozen bit-parity with `_r5`).
- **Regression Risks:**
  - **Area gate failure:** CP-2 Gate 4 mandates an exact 0.0000 m² area difference between old and new geometry paths (`STATE_european_locations_v5.md:564`). Simplifying polygon rings shifts polygon edges and modifies enclosed area, which directly causes CP-2 Gate 4 to fail.
  - **Interzone boundary mismatch:** If collinear vertices introduced by T-junctions on Floor $N$ are removed while Floor $N+1$ retains them (or vice versa), the ceiling and floor surfaces will have different vertex counts, creating genuine interzone boundary mismatches where none previously existed.
- **Test Plan:**
  - Verify polygon area preservation on all 2,262 buildings.
  - Run `tests/geometry/test_eu15_ruled_coverage.py` and `scripts/eu21/07_nocore_tests.py`.

### 4.2 Option B: Targeted Gate Refinement (Recommended)

- **File and Lines:** `scripts/run_eu_s2_campaign.py:94-125` (`_has_near_duplicate_vertex_surfaces`) and lines `645-665`.
- **Concept:** Refine `_has_near_duplicate_vertex_surfaces` to only flag conditions that represent true EnergyPlus fatal risks:
  1. **Scope to interzone candidate surfaces:** Filter checks to surfaces where `Outside_Boundary_Condition == "Surface"`. Surfaces with boundary conditions `Ground`, `Outdoors`, or `Adiabatic` have no paired partner surface in EnergyPlus. An interzone vertex mismatch is geometrically impossible on partner-less surfaces, and local simulations prove they cause 0 Fatal / 0 Severe.
  2. **Require asymmetry for interzone collinear defects:** For paired interzone surfaces, check if the collinear vertex is *asymmetric* between the surface and its paired `Outside_Boundary_Condition_Object`. If both surfaces carry identical vertex coordinates, EnergyPlus's convexity checking operates symmetrically on both sides with 0 errors. Only asymmetric machine-precision insertions (the genuine `FINDING 210` / `e21bec78b937acf5` / `8cdf349a99934f0d` defect) trip the safety net and trigger the single-zone reroute.
- **Compliance with `D-EU-41`:** Complies (`openubem/idf/surfaces.py` is completely untouched; changes are confined to `scripts/run_eu_s2_campaign.py`).
- **Compliance with `D-EU-95`:** Complies (`european_nocore.py` is untouched).
- **Compliance with Hard Rule 3:** Complies (`NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005` and `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1` remain unchanged).
- **Regression Risks:**
  - **Circulation zone loss:** Zero risk (circulation zone logic is untouched).
  - **Geometry area gate:** Zero risk (exact zero area diff preserved, geometry polygons are not mutated).
  - **Simulation regression:** Negligible. Asymmetric insertions that triggered the original `FINDING 210` fatal continue to trigger the reroute safety net.
- **Test Plan:**
  - Run synthetic unit test verifying that identical collinear pairs pass while asymmetric pairs trigger reroute.
  - Rebuild the 16-building T02b/T02c sample and run EnergyPlus 23.1.0 locally, asserting `RC=0, Fatal=0, Severe=0`.
  - Execute 4-district fleet audit confirming that recovered dwelling layouts simulate clean.

### 4.3 Option C: Narrowing the collinear angle tolerance

- **File and Lines:** `scripts/run_eu_s2_campaign.py:91` (`COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1`).
- **Concept:** Reduce `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` from `0.1°` to `0.001°` or `0.0001°` so that it only detects near-180° machine precision angles without catching 179.91°–179.99° footprint vertices.
- **Compliance with `D-EU-41`:** Complies.
- **Compliance with `D-EU-95`:** Complies.
- **Compliance with Hard Rule 3:** **Fails.** Explicitly violates prompt Hard Rule 3 and `STATE_european_locations_v5.md:594-595` ("No threshold move").
- **Empirical Ineffectiveness:** In building `way/942642640` and multiple other surveyed buildings, vertices created by straight parcel alignments and cut T-junctions sit at an interior angle of exactly `180.000000°` (where `cos(angle) = -1.0000000000000000`). Even a tolerance of `1e-6°` fires on exact 180° vertices.
- **Test Plan:** Not applicable (ruled out).

### 4.4 Option D: Expand `near_duplicate_vertex_tolerated_box` precedent

- **File and Lines:** `scripts/run_eu_s2_campaign.py:658-697`.
- **Concept:** When `mismatched` is False and `near_duplicate` is True, do not invoke `_force_reroute_room_layout_to_one_zone_per_floor`. Instead, retain the dwelling layout and label the zones with `fallback_reason = "near_duplicate_vertex_tolerated_box"`, mirroring lines 694-696.
- **Compliance with `D-EU-41`:** Complies.
- **Compliance with `D-EU-95`:** Complies.
- **Regression Risks:** While effective for footprint-inherent collinear vertices, this would also tolerate genuine asymmetric `intersect_match` insertions (such as stem `8cdf349a99934f0d`), causing real Fatal simulation errors on the cluster. Option B is strictly superior because it differentiates between benign symmetric/partner-less vertices and fatal asymmetric insertions.
- **Test Plan:** Run full test fleet through local EnergyPlus 23.1.0.

---

## 5. Recommendation

We recommend **Option B: Targeted Gate Refinement**.

### 5.1 Proposed Implementation Architecture

The modifications are strictly localized to `scripts/run_eu_s2_campaign.py`:

```
+--------------------------------------------------------------------------------+
| scripts/run_eu_s2_campaign.py                                                  |
|                                                                                |
| 1. Filter _has_near_duplicate_vertex_surfaces:                                 |
|    - If surface.Outside_Boundary_Condition in ("Ground", "Outdoors",          |
|      "Adiabatic"):                                                             |
|          SKIP (partner-less, no interzone mismatch risk)                       |
|    - If surface.Outside_Boundary_Condition == "Surface":                       |
|          Evaluate collinear/proximity defects.                                 |
|          If defect detected:                                                   |
|              Check partner surface (Outside_Boundary_Condition_Object).        |
|              If partner has IDENTICAL coordinates:                             |
|                  PASS (symmetric, EnergyPlus handles cleanly)                  |
|              If partner has ASYMMETRIC / MISSING coordinate:                   |
|                  FLAG at_risk = True (genuine FINDING 210 fatal risk)          |
+--------------------------------------------------------------------------------+
```

### 5.2 Implementation and Validation Steps

1. **Step 1 (Code update in `scripts/run_eu_s2_campaign.py`):**
   - In `_has_near_duplicate_vertex_surfaces(idf)`:
     - Check only surfaces with `surf.Outside_Boundary_Condition == "Surface"`.
     - When a collinear or near-duplicate vertex is detected on surface $S_1$, look up partner surface $S_2 = \text{idf.getobject}(\text{"BUILDINGSURFACE:DETAILED"}, S_1.\text{Outside\_Boundary\_Condition\_Object})$.
     - If $S_2$ exists and has the identical vertex at the coincident position (within `_COINCIDENT_VERTEX_TOL = 0.01` m), treat as symmetric and do not flag.
     - If $S_2$ does not exist or lacks the matching vertex (asymmetric insertion), return `True`.
   - Remove unused stub `_symmetrize_near_duplicate_interzone_vertices` (`scripts/run_eu_s2_campaign.py:128-227`).
2. **Step 2 (Local unit test):**
   - Add a test in `tests/test_eu_s2_campaign.py` with:
     - A building containing partner-less collinear vertices (`Ground`, `Outdoors`) -> asserts `at_risk == False`.
     - A building containing symmetric interzone collinear vertices -> asserts `at_risk == False`.
     - A building containing asymmetric interzone insertions (synthetic `8cdf349a99934f0d` analog) -> asserts `at_risk == True` and verifies successful single-zone reroute.
3. **Step 3 (EnergyPlus 23.1.0 local validation):**
   - Rebuild the 16-building T02b sample.
   - Run `energyplus.exe` locally on all 16, verifying `0 Fatal / 0 Severe` and `RC=0`.
4. **Step 4 (CP-2 re-audit):**
   - Execute the 4-district IDF rebuild and verify Gate 5: real dwelling layout count rises from 956 to >2,000, and reroute count drops from 1,306 to near 0.

---

## 6. Open questions

1. **Handling of multi-wing / complex perimeters with 1 mm staircase stepping (e.g. Lyon `BATIMENT0000000240879996_part0`):**  
   In Lyon, `_stabilize_ring_coords` created 36 degenerate surfaces on upper storeys due to 1 mm lattice snapping on diagonal facade cuts, producing 46 Severe warnings in EnergyPlus (though 0 Fatal). While Option B preserves the dwelling layout without simulation crashing (`RC=0`), should buildings with >10 Severe warnings on exterior facades continue to be monitored via a disclosed manifest tag (`degenerate_facade_tolerated`)?
2. **Speed cluster submission authorization:**  
   Once Option B is implemented and local CP-2 Gate 5 re-audit is completed, Director sign-off (`D-EU-99` clause 2) will be required to trigger `scripts/cluster/submit_fleet_t08.sbatch` on the Speed cluster.
