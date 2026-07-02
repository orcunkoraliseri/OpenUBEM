# RESULT — IRREGULAR FOOTPRINT HANDLING (adapting a prototype layout to real shapes)

*Prompt file: `L04_irregular_footprint_handling_prompt.md`. OpenUBEM layout-mapping sub-set. 2026-06-29.*

---

## REQUIRED OUTPUT TABLES

### Table 1 — Footprint pre-processing before zoning

| Step | Purpose | Typical parameter | Used by | Source |
|---|---|---|---|---|
| **Polygon simplification (Douglas–Peucker)** | Drop GIS noise vertices (digitising artefacts, curved facades approximated as many-sided polygons, small setbacks) that would generate dozens of degenerate narrow perimeter zones | Tolerance **ε = 0.5 m** (`polygon.simplify(0.5, preserve_topology=True)`). Removes any vertex whose perpendicular deviation from the chord is < 0.5 m. Larger ε (1–2 m) risks losing architecturally meaningful bays; 0.5 m is the defensible lower bound for OSM data at city scale. | URBANopt recommends pre-processing OSM/GeoJSON with shapely/geopandas before ingestion; CityBES avoids the issue by rasterising; OpenUBEM (synthesis). | Douglas & Peucker (1973), *Canadian Cartographer* 10(2):112–122; Shapely documentation v2.x (2024); RESULT_L01. |
| **Topology validation** | Ensure the simplified polygon is a valid, closed, non-self-intersecting geometry before any offset is attempted | `shapely.is_valid(poly)`. If invalid, attempt repair via `poly.buffer(0)`. If still invalid, abort and log → proceed to applicable fallback tier. | Shapely standard practice; geomeppy relies on Shapely for all geometry. | Shapely readthedocs (2024); GEOS documentation. |
| **Narrow-width check** | Detect sections of the footprint narrower than 2 × perimeter depth = **9.14 m** (2 × 4.57 m). Such wings cannot accommodate both a perimeter zone and a non-trivial core; the inward buffer will self-intersect or produce an empty/multi-polygon. | Compute the **minimum width** using the minimum-area oriented bounding rectangle via `shapely.minimum_rotated_rectangle` (Shapely ≥ 2.0); extract the shorter side. If min width < 9.14 m → flag for sliver handling (Table 2). | OpenUBEM synthesis (builds on RESULT_L01 §Mitigation). | RESULT_L01 §Confidence; geomeppy readthedocs (2024). |
| **Interior hole / courtyard detection** | Identify donuts (polygons with holes). `Polygon.interiors` returns the inner rings. If any inner ring exists → route to one_zone_per_floor; geomeppy donut-offset produces vertex mismatches → EnergyPlus Fatal. | `len(list(poly.interiors)) > 0` → courtyard flag. | geomeppy (native behaviour); OpenUBEM existing hard fallback. | geomeppy readthedocs (2024); RESULT_L01; OpenUBEM existing rule. |
| **Vertex-count gate** | Very high vertex-count polygons (> 20 vertices after simplification) signal an approximated curve or complex multi-wing form, generating many degenerate perimeter zones. | If `len(poly.exterior.coords) - 1 > 20` after D-P simplification at 0.5 m, retry simplification at ε = 1 m, then consider **convex decomposition** (next step). **GAP** — no published UBEM threshold; 20 vertices is OpenUBEM synthesis based on the expectation that a ~6-sided real building simplifies to ≤ 12 coords. | OpenUBEM synthesis; Xiang et al. CPZ (2022/2024). |
| **Convex decomposition (CPZ / Hertel–Mehlhorn)** | Decompose a concave polygon into a set of convex sub-polygons, zone each independently. Avoids self-intersection entirely on L/U/T shapes. Used as Tier-1b between direct offset and full fallback. | Convex Partition Zoner (CPZ) uses an iterative Hertel–Mehlhorn approach. Each convex part receives its own core+perimeter split; shared edges become adiabatic interzone surfaces. A Python adaptation can use `shapely` triangulation + merging heuristics. | AutoBEM CPZ (Xiang et al., IBPSA SimBuild 2022/2024; Harvard GSD / KPF); Honeybee `polyskel` component. | Xiang, Dang, Cerezo Davila & Samuelson, IBPSA SimBuild 2022; KPF CPZ docs (2024). |
| **Bounding-box / oriented-bbox proxy** | Last-resort regularisation: replace the footprint with its minimum-area oriented bounding rectangle (OBB). Preserves footprint area and cardinal orientation but loses shape fidelity. OBB fits rotated buildings better than axis-aligned bbox. | `polygon.minimum_rotated_rectangle` (Shapely ≥ 2.0). Accept substitute if `footprint_area / obb_area > 0.85`; otherwise log large shape distortion. | Preprints.org UBEM OBB study (2023); Dogan & Reinhart shoeboxer (2017). | Dogan & Reinhart (2017), *Energy and Buildings*, 140:140–153; Preprints.org UBEM OBB study. |
| **Straight-skeleton partition** | Alternative to simple inward offset for non-convex polygons. Propagates all edges inward simultaneously at constant speed, naturally handling concavities without self-intersection. Produces a topological partition aligned with the polygon's own ridge geometry. | Python library `polyskel` (Felkel & Obdrzalek 1998 algorithm). Offset depth = 4.57 m applied to skeleton arcs. Used natively in Honeybee via Grasshopper component. | Honeybee/Ladybug Tools (straight-skeleton component using `polyskel`); Felkel & Obdrzalek (1998). | Felkel & Obdrzalek (1998), *Comp. Graph. Forum*; Honeybee/Ladybug documentation (2024); IBPSA-USA SimBuild 2022. |

---

### Table 2 — Behaviour per shape class

| Shape class | Detailed layout feasible? | Recommended handling | Fallback if it fails | Source |
|---|---|---|---|---|
| **Rectangle / near-rectangle** (width ≥ 9.14 m on all sides; ≤ 8 exterior edges after D-P simplification) | **Yes** — simplest and most reliable case | Apply standard inward buffer at 4.57 m via `shapely.buffer(-4.57, join_style=2)`. One core + up to 4 perimeter zones (cardinal-grouped per RESULT_L01). Tier 1. | Extremely rare; if buffer yields invalid geometry despite rectangular shape, revert to `one_zone_per_floor` (Tier 3). | RESULT_L01; ASHRAE 90.1-2019 App. G; geomeppy native. |
| **L / U / T — multi-wing concave** | **Conditionally yes** — feasible if all wings ≥ 9.14 m wide and no acute re-entrant corners | **Option A (preferred, wings ≥ 9.14 m):** Apply D-P simplification then straight-skeleton or CPZ decomposition. Zone each convex sub-polygon independently; shared internal edges → adiabatic. **Option B:** If wings are wide enough, direct inward buffer on full footprint; validate post-buffer. | If any wing < 9.14 m or CPZ sub-polygon count > 10: `one_zone_per_floor` (Tier 3). | AutoBEM CPZ (Xiang et al. 2022); Honeybee polyskel; RESULT_L01. |
| **Long thin sliver** (minimum width < 9.14 m — i.e., < 2 × perimeter depth) | **No** — inward offset collapses or self-intersects | **Perimeter-only** treatment: the entire floor plate treated as a single perimeter exposure zone (no distinct core). Assign perimeter-zone loads/schedules. Model as `one_zone_per_floor` with **perimeter-zone parameters**. | `one_zone_per_floor` (Tier 3) — already the recommended action. Further: `single_zone` (Tier 4) only if `one_zone_per_floor` geometry also fails. | RESULT_L01 §Confidence; geomeppy narrow-core fallback (existing OpenUBEM rule). |
| **Courtyard / donut** (polygon with interior holes; `len(poly.interiors) > 0`) | **No** — geomeppy `core/perim` with a hole produces vertex-mismatch fatal errors in EnergyPlus | Route immediately to `one_zone_per_floor` with full donut footprint extruded. **Do not attempt offset.** EnergyPlus can model a donut-shaped zone without a hole in the envelope provided the inner wall is modelled as an exterior (exposed-to-outdoors) surface. | `one_zone_per_floor` (Tier 3) — existing hard fallback. `single_zone` (Tier 4) if donut extrusion itself fails vertex matching. | OpenUBEM existing rule; geomeppy readthedocs (2024); RESULT_L01. |
| **Very small** (footprint area < 100 m²) | **No** — core will be empty or < 10 m² after 4.57 m inward offset from all sides | Route immediately to `one_zone_per_floor`. Single-zone schedule and loads apply (archetype default). | `one_zone_per_floor` (Tier 3). `single_zone` (Tier 4) if the tiny footprint has geometry errors. | RESULT_L01; OpenUBEM existing hard fallback (core < 10 m² → `one_zone_per_floor`). |
| **Very large / many-sided** (area > 5 000 m² or > 20 exterior edges after D-P at 0.5 m) | **Conditionally yes** for area alone, but vertex count raises risk of many degenerate perimeter zones | Apply D-P at ε = 1 m. Limit post-simplification zone count to ≤ 8 perimeter zones by merging cardinal groups aggressively. If vertex count still > 20 after D-P at 1 m → CPZ decompose. | If CPZ produces > 10 sub-polygons: `one_zone_per_floor` (Tier 3). | RESULT_L01; CityBES AutoZone (Chen & Hong 2018) handles large footprints via rasterisation; CPZ (Xiang et al. 2022). |

---

### Table 3 — The fallback ladder (graceful degradation)

| Tier | Condition to trigger | Action | Source |
|---|---|---|---|
| **Tier 1 — Detailed** (prototype layout) | All of: (a) polygon is valid; (b) min width ≥ 9.14 m; (c) no interior holes; (d) area ≥ 100 m²; (e) post-D-P vertex count ≤ 12 | Apply D-P simplification (ε = 0.5 m) + inward buffer at 4.57 m + cardinal-orientation perimeter grouping → core + ≤ 4 perimeter zones. Assign archetype-specific zone loads, schedules, and WWR. | RESULT_L01; ASHRAE 90.1-2019 App. G; Chen & Hong (2018). |
| **Tier 1b — CPZ / straight-skeleton** | `is_valid=True`, no holes, `area ≥ 100 m²`, `min_width ≥ 9.14 m`, `12 < n_verts ≤ 20` (concave, multi-wing) | Convex decomposition (CPZ / polyskel); zone each sub-polygon at 4.57 m depth. If CPZ yields > 10 sub-polygons → drop to Tier 2. | AutoBEM CPZ; Xiang et al. (2022); Honeybee polyskel. |
| **Tier 2 — Generic core + perimeter (OBB)** | Buffer output from Tier 1 is invalid/empty after `buffer(0)` repair; OR CPZ yields 7–10 sub-polygons; OR `n_verts > 20` even after ε = 1 m simplification | Re-attempt with OBB proxy (`min_rotated_rectangle`); apply buffer 4.57 m to OBB; single core + 4 cardinal zones. | CityBES AutoZone approach (Chen & Hong 2018); URBANopt `urban_geometry_creation_zoning`; RESULT_L01. |
| **Tier 3 — `one_zone_per_floor`** | Any of: (a) min width < 9.14 m (sliver); (b) interior hole (courtyard/donut); (c) area < 100 m²; (d) post-buffer polygon invalid/empty after repair; (e) CPZ > 10 sub-polygons; (f) OBB buffer fails | Extrude the raw simplified footprint polygon as a single zone per floor. Use archetype full-floor loads, schedules, and HVAC (single-zone operating parameters). Perimeter thermal coupling is lost but the building survives simulation. | OpenUBEM existing hard fallback; geomeppy `by_storey` zoning; RESULT_L01. |
| **Tier 4 — `single_zone`** (whole building) | Any of: (a) `one_zone_per_floor` geometry also invalid; (b) footprint polygon invalid after all repair attempts; (c) building has only 1 floor | Model the entire building as one single zone (no floor-level extrusion). Use building-level single-zone schedule and loads (RESULT_01 methodology). Unconditional safety net. | RESULT_01 (single-zone mode); URBANopt detailed-model fallback; CEA default single-zone. |

---

### Table 4 — How peer tools report/handle degradation

| Tool | Detects bad geometry? | Degrades silently or logged? | City-scale success rate reported? | Source |
|---|---|---|---|---|
| **URBANopt / OpenStudio** | **Partial** — geometry validation at GeoJSON-to-OSM translation stage. Detects clearly invalid polygons (non-closed rings, zero-area). Complex failures (self-intersecting buffer output) may only manifest later as E+ fatal errors. | **Partially logged** — OpenStudio writes run.log with E+ fatal messages, but degradation from multi-zone to single-zone is not automatically logged as a tier decision. URBANopt docs recommend `detailed_model_filename` for complex shapes to bypass auto-zoning — a silent workaround rather than a logged fallback. | **Not reported.** Published studies do not cite a per-city success rate for the auto-zoning step. Geometry failures are treated as upstream data quality issues. | URBANopt documentation (2024); Concordia UBEM study (2023); IBPSA LOD accuracy paper. |
| **CityBES** | **Yes — by design.** The pixel/raster approach inherently handles all polygon shapes (L, U, T, donut) because rasterisation never self-intersects. Very thin/tiny buildings fall back to `OneZone` within the same automated pipeline. | **Internally handled, not prominently logged.** Chen & Hong (2018) note the pixel method is applied uniformly; silent degradation to `OneZone` occurs when the raster core pixel count reaches zero. No per-building tier log is exposed to the user. | **Partial.** Chen & Hong (2018) report AutoZone was applied successfully to the San Francisco commercial building stock without reported crash rates. No explicit fallback-to-OneZone frequency is given. | Chen & Hong (2018), *Applied Energy*, 211:1263–1278. |
| **AutoBEM / CPZ** | **Yes (with CPZ).** CPZ explicitly detects concavity and routes concave polygons through iterative decomposition rather than a direct offset. Without CPZ (default AutoBEM), standard OS offset failures manifest as EnergyPlus simulation errors. | **Partially logged (CPZ path).** CPZ outputs inspectable sub-polygon geometry. City-scale AutoBEM runs (New et al. 2021) use one-zone-per-floor for the national model, implying silent degradation is the norm for stock-scale production runs. CPZ is a research prototype, not production-hardened. | **Not published.** CPZ studies report accuracy metrics but not crash/failure rates across a city. AutoBEM national-scale "Model America" uses simplified geometry, not CPZ — so CPZ city-scale geometry success rate is unknown. | Xiang et al., IBPSA SimBuild 2022; New et al. (2021) ORNL; KPF CPZ blog (2024). |

---

## Part C — Synthesis: OpenUBEM Robustness Ladder

### 1. Pre-processing pipeline (applied to every raw OSM polygon)

```python
# Step P1 — Validate topology
poly = shapely.from_wkt(osm_polygon_wkt)
if not poly.is_valid:
    poly = poly.buffer(0)               # attempt repair
if not poly.is_valid or poly.is_empty:
    LOG(building_id, tier=4, reason="invalid geometry, buffer(0) repair failed")
    # → Tier 4: single_zone

# Step P2 — Detect interior holes (courtyard)
if len(list(poly.interiors)) > 0:
    LOG(building_id, tier=3, reason="courtyard/donut polygon")
    # → Tier 3: one_zone_per_floor   (existing hard fallback)

# Step P3 — Area check
if poly.area < 100:                     # m²
    LOG(building_id, tier=3, reason=f"area={poly.area:.1f} m² < 100 m²")
    # → Tier 3: one_zone_per_floor

# Step P4 — Simplify (Douglas-Peucker)
poly_s = poly.simplify(0.5, preserve_topology=True)
if not poly_s.is_valid:
    poly_s = poly.simplify(1.0, preserve_topology=True)   # fallback tolerance
if not poly_s.is_valid:
    LOG(building_id, tier=3, reason="simplification failed")
    # → Tier 3: one_zone_per_floor

# Step P5 — Minimum-width check
obb = poly_s.minimum_rotated_rectangle   # Shapely >= 2.0
obb_coords = list(obb.exterior.coords)
d1 = obb_coords[0][0] - obb_coords[1][0]  # use distance helper in practice
d2 = obb_coords[1][0] - obb_coords[2][0]
min_width = min(abs(d1), abs(d2))          # simplified; use proper 2D distance
if min_width < 9.14:                       # < 2 x 4.57 m
    LOG(building_id, tier=3, reason=f"min_width={min_width:.2f} m < 9.14 m (sliver)")
    # → Tier 3: one_zone_per_floor

# Step P6 — Vertex count gate
n_verts = len(list(poly_s.exterior.coords)) - 1  # closed ring: first==last
if n_verts > 20:
    poly_s = poly_s.simplify(1.0, preserve_topology=True)
    n_verts = len(list(poly_s.exterior.coords)) - 1

# → PASS TO TIER SELECTION (Table 3)
```

### 2. Deterministic fallback ladder with measurable triggers

| Tier | Trigger conditions (measurable, ordered) | Action | Logged? |
|---|---|---|---|
| **1** | `is_valid=True`, no holes, `area ≥ 100 m²`, `min_width ≥ 9.14 m`, `n_verts ≤ 12` | Inward buffer 4.57 m + cardinal perimeter grouping. Validate buffer output (`is_valid`, `not is_empty`, `isinstance(result, Polygon)`). If buffer fails → Tier 2. | `tier=1` |
| **1b (CPZ)** | `is_valid=True`, no holes, `area ≥ 100 m²`, `min_width ≥ 9.14 m`, `12 < n_verts ≤ 20` | Convex decomposition (CPZ/polyskel). If CPZ yields > 10 sub-polygons → Tier 2. | `tier=1b, sub_polygon_count=N` |
| **2 (OBB proxy)** | Buffer output invalid/empty; OR CPZ yields 7–10 sub-polygons; OR `n_verts > 20` after ε=1 m | OBB substitute + buffer 4.57 m; single core + 4 cardinal zones. | `tier=2, shape_distortion_ratio=X` |
| **3 (one_zone_per_floor)** | `min_width < 9.14 m`; OR interior hole; OR `area < 100 m²`; OR Tier 2 buffer fails; OR `obb_area/footprint_area < 0.70` | `one_zone_per_floor` on simplified real footprint. | `tier=3, reason=<string>` |
| **4 (single_zone)** | `poly.is_valid` remains False after all repairs; OR E+ fatal during `one_zone_per_floor` | `single_zone` whole building. | `tier=4, reason=<string>` |

### 3. Existing hard fallbacks — preserved as-is

Two rules from prior OpenUBEM decisions map explicitly onto this ladder:

- **Narrow core (core area < 10 m² after buffer):** Sub-case of Tier 1 → Tier 3 transition. If `buffer(-4.57).area < 10`, treated as empty core → `one_zone_per_floor`.
- **Courtyard/donut:** Detected at Step P2; routes immediately to `one_zone_per_floor` without any offset attempt.

### 4. Per-building logging requirement (no silent degradation)

Every building processed in `zone` mode must emit a structured log entry:

```json
{
  "building_id": "way/123456789",
  "footprint_area_m2": 342.1,
  "min_width_m": 11.4,
  "n_verts_simplified": 8,
  "has_hole": false,
  "zoning_tier": 1,
  "tier_reason": "nominal",
  "zone_count": 5
}
```

`zoning_tier` and `tier_reason` are mandatory. A city-level post-processing step computes `tier_distribution` (% of buildings in each tier) — the coverage audit metric that makes degradation visible and auditable.

---

## Confidence and caveats

**Shape most likely to slip through and crash EnergyPlus even after the above pre-processing:**

**Narrow-wing L or U shapes where the minimum-width check passes on the OBB but individual wings are < 9.14 m wide.** The OBB minimum-width check (Step P5) measures the shorter side of the *overall* oriented rectangle, not the width of each wing independently. An L-shaped building could have an OBB min-width of 14 m while one wing is only 6 m wide. The inward buffer on that wing will self-intersect, producing a fragmented `MultiPolygon`. If the post-buffer validity check only tests `is_valid` rather than `isinstance(result, Polygon)`, the fragmented `MultiPolygon` is passed to geomeppy, causing vertex-matching failure in EnergyPlus.

**Mitigation — add after the buffer step in Tier 1:**

```python
core = poly_s.buffer(-4.57, join_style=2)
if (not isinstance(core, shapely.Polygon)
        or not core.is_valid
        or core.is_empty
        or core.area < 10):
    LOG(building_id, tier=2,
        reason="buffer fragmented to MultiPolygon or empty/tiny core")
    # → Tier 2 (OBB proxy)
```

**Second-highest risk:** Polygons with `is_valid = True` that nonetheless contain nearly-collinear sequences of vertices creating extremely acute interior angles. When an inward offset is applied, these angles generate spikes that poke outside the original polygon boundary. EnergyPlus rejects nearly-planar (but not exactly planar) zone surfaces if deviation exceeds its tolerance (≈ 0.001 m). Douglas–Peucker at ε = 0.5 m should eliminate most of these, but is not guaranteed for acute re-entrant corners at exactly the 0.5 m scale.

---

## Reference list

1. **Chen, Y., & Hong, T.** (2018). "Impacts of building geometry modeling methods on the simulation results of urban building energy models." *Applied Energy*, 211, 1263–1278. https://doi.org/10.1016/j.apenergy.2017.12.008

2. **Douglas, D. H., & Peucker, T. K.** (1973). "Algorithms for the reduction of the number of points required to represent a digitized line or its caricature." *The Canadian Cartographer*, 10(2), 112–122. https://doi.org/10.3138/FM11-6770-U75U-V872

3. **Xiang, J., Dang, Q., Cerezo Davila, C., & Samuelson, H.** (2022). "Convex partition zoner: a new algorithm for automated thermal zoning." *Proceedings of SimBuild 2022 / IBPSA-USA*, Chicago IL.

4. **Xiang, J., Dang, Q., Cerezo Davila, C., & Samuelson, H.** (2024). Extended journal version, *Journal of Building Performance Simulation*, Tandfonline. (CPZ algorithm; Harvard GSD / KPF implementation.)

5. **Felkel, P., & Obdrzalek, S.** (1998). "Straight skeleton implementation." *Proceedings of Spring Conference on Computer Graphics*, Bratislava, Slovakia. (Algorithm underlying `polyskel` Python library and Honeybee Straight Skeleton component.)

6. **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140–153. https://doi.org/10.1016/j.enbuild.2017.01.017

7. **New, J. R., et al.** (2021). "Model America: Data and models for every building in America." Oak Ridge National Laboratory Technical Report. https://www.ornl.gov/

8. **geomeppy documentation** (2024). "add_block / core_perimeter zoning." Read the Docs. https://geomeppy.readthedocs.io/

9. **Shapely documentation** (2024). `Polygon.buffer`, `Polygon.is_valid`, `Polygon.minimum_rotated_rectangle`. Shapely v2.x. https://shapely.readthedocs.io/

10. **URBANopt documentation** (2024). "GeoJSON Gem; Urban Geometry Creation Zoning Measure; detailed_model_filename fallback." NREL. https://docs.urbanopt.net/

11. **KPF / Kohn Pedersen Fox** (2024). "Convex Partition Zoner (CPZ) project page." https://www.kpf.com/

12. **Honeybee / Ladybug Tools documentation** (2024). "Straight Skeleton component using polyskel." https://www.ladybug.tools/

13. **ASHRAE 90.1-2019** Normative Appendix G, Table G3.1. Perimeter depth = 4.57 m (15 ft). ASHRAE, Atlanta, GA.

14. **RESULT_L01_footprint_to_zone_layout_algorithms.md** (2026). OpenUBEM internal research result; §Algorithm and §Confidence.
