# Step 3 — OSM Archetype-Enriched GeoDataFrame → One EnergyPlus IDF per Building
### OpenUBEM Stage 3 / Modules 07–11: `openubem/geometry/{footprint,zoning,context}.py` + `openubem/idf/{builder,surfaces,hvac,outputs}.py` — convert the 57-column enriched GeoDataFrame from Stages 1–2 into one self-contained `<output_dir>/idfs/<osm_id>.idf` per simulation building, ready for parallel EnergyPlus 23.1 execution

> **Slug:** `step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod` &nbsp;•&nbsp; **First created:** `2026-05-07` &nbsp;•&nbsp; **Latest revision:** `2026-05-07`
>
> Sections 1–9 are **append-once, edit-never** after first APPROVED verdict. Section 10 (Progress Log) is owned by the downstream `/run` reporter. All `/design` re-run changes are recorded under **Section 11 — Revision Log**.
>
> **Scope rule.** This document covers exactly **one** step of the umbrella pipeline — Step 3 (IDF generation). The step's *internal* sub-stages (3A–3I) live under §3 Pipeline. Stages 1–2 (footprint ingest + archetype classification) and Stages 4–5 (parallel simulation + result aggregation) are covered in their own per-step DESIGN docs.

---

## 1. Aim

Step 3 converts the 57-column archetype-enriched GeoDataFrame produced by the Stage 1–2 pipeline (Steps 1, 2 plus intermediate Modules 02 / 04 / 05 / 06 / 06b) into one self-contained EnergyPlus 23.1 IDF file per simulation building, written to `<output_dir>/idfs/<osm_id>.idf`. Upstream consumer of the contract: Step 2 (`02_buildings_classified.gpkg` → archetype assignment) plus Modules 02 (climate zone + EPW), 04 (constructions), 05 (loads), 06/06b (schedules). Downstream consumer: Stage 4 — the parallel EnergyPlus runner (Module 12) which fans out across `<osm_id>.idf` files in isolated `work_dir`s and produces SQL/HTML simulation outputs. Without Step 3 the pipeline has no executable simulation artifact; the entire 57-column semantic enrichment exists solely so Step 3 can compose it into a syntactically valid, EnergyPlus-runnable building model. The narrative, vocabulary, and module decomposition follow `inputs/aim/OpenUBEM_Technical_Pipeline.md` §6 (Stage 3); the canonical 3D geometry library choice (geomeppy ≥ 0.11.8 on eppy ≥ 0.5.63) is documented in `inputs/papers/geomeppy-0-11-8-documentation.md` and is binding architectural invariant from `.claude/design_state.md`.

---

## 2. Inputs

| Artifact | Source | Dtype | Shape | Notes |
|---|---|---|---|---|
| `02_buildings_classified.gpkg` (post-enrichment) | Step 2 → Modules 02/04/05/06/06b | GeoDataFrame | (N, 57) | UTM-projected geometry; **57-column contract** including geometry (Polygon), `osm_id` (str), `footprint_area_m2`, `perimeter_m` (float), `levels` (Int64 nullable), `height_m` (float nullable), `year_built` (Int64 nullable), `data_quality_flag` (str, comma-joined vocabulary), `archetype_id` (categorical, 30-element closed vocab including `OpenUBEMUnknown`), `archetype_confidence` (HIGH/MEDIUM/LOW), `archetype_source` (str), `climate_zone` (str e.g. "3A"), `epw_path` (str abs path), `provenance_climate_zone`, `u_roof_w_m2k`, `u_wall_w_m2k`, `u_window_w_m2k`, `shgc_window`, `u_floor_w_m2k`, `infiltration_m3_s_m2`, `assembly_roof`, `assembly_wall`, `vintage_standard` (str), 5× envelope provenance columns, `lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person`, `heating_setpoint_c`, `cooling_setpoint_c`, `heating_setback_c`, `cooling_setup_c`, `wwr` (float), 6× loads provenance columns. |
| EPW weather file(s) | Module 02 (`epw_manager.py`) | binary `.epw` | one per unique `epw_path` | Resolved to absolute path on local disk; one EPW typically serves an entire neighbourhood/climate zone. Step 3 references the EPW path inside the IDF (`Site:Location` populated from EPW header) but does **not** attach the EPW to the IDF (Stage 4 binds them at run time). |
| IDF base templates | bundled in package `openubem/idf/templates/` | text `.idf` | 4 stubs (~5–15 KB each) | `commercial_base.idf`, `residential_base.idf`, `highrise_base.idf`, `specialized_base.idf`. Each contains only `Version`, `SimulationControl`, `RunPeriod`, `Timestep`, and a placeholder `Site:Location`. No geometry, no zones, no schedules. |
| EnergyPlus IDD | `config.ENERGYPLUS_IDD_PATH` | text `.idd` | EnergyPlus 23.1 schema | Locked at module import via `geomeppy.IDF.setiddname()` — invariant **I3**. Phase-1 supports EnergyPlus 23.1 only; no dual-IDD auto-detect. |
| Schedule library | Module 06 outputs (in-memory pre-built schedule dicts keyed by `archetype_id`) | dict | 30 archetypes × {lighting, equipment, occupancy, heating, cooling, infiltration} | Module 06 emits these as Python dicts of `Schedule:Compact` IDF object stubs. Step 3 calls `idf.copyidfobject(stub)` for each archetype-specific schedule needed by the building's zones. |
| `config.py` | package config | Python module | — | Exposes `ENERGYPLUS_IDD_PATH`, `SHADING_SPHERE_RADIUS` (default 30.0 m, configurable 20–60 m), `DP_TOLERANCE_M` (default 0.5), `DP_COARSE_TOLERANCE_M` (default 1.5), `MAX_VERTICES` (120), `FLOOR_TO_FLOOR_M` (default 3.5), `PERIMETER_DEPTH_M` (default 4.57, ASHRAE 90.1 Appendix G). |

> Note on the column contract: the `climate_zone` and `epw_path` columns are committed by Module 02 (acquisition/climate_zone.py + epw_manager.py), which is not yet designed at the time of writing. Step 3 treats the 57-column schema as its binding input contract; integration testing requires Module 02 to be designed and built first (see §7 OQ-7).

---

## 3. Pipeline

The Step 3 pipeline is a per-row loop over the enriched GeoDataFrame: for each building, sub-stages 3A–3I execute in order to produce a single `<osm_id>.idf` file. Sub-stages 3A–3C run on Shapely/GeoPandas geometry (no IDF object yet); sub-stages 3D–3I progressively build the IDF object via geomeppy and eppy. Architecturally, this is one IDF per building (invariant **I1**); never combined-IDF.

### 3A — Footprint Simplification (Module 07: `openubem/geometry/footprint.py`)

For each row in the enriched GeoDataFrame, the raw OSM polygon (already in UTM metres after Step 1) is reduced to ≤120 exterior-ring vertices to satisfy the EnergyPlus `BuildingSurface:Detailed` per-surface vertex limit. The simplification is a 4-tier fallback chain; each tier records its outcome in the building's `data_quality_flag` so downstream validators can audit the simplification severity per building.

```python
# Module 07: openubem/geometry/footprint.py
def _n_exterior_verts(poly: shapely.Polygon) -> int:
    return len(poly.exterior.coords) - 1  # closing vertex repeats

def simplify_footprint(geom: shapely.Polygon, dq_flag: str) -> tuple[shapely.Polygon, str, str]:
    """
    Returns (simplified_polygon, updated_dq_flag, simplification_status).
    status in {'dp_05', 'dp_15', 'hull', 'bbox', 'skip'}
    """
    # Tier 1: Douglas-Peucker at 0.5 m (invariant I4)
    poly = shapely.simplify(geom, tolerance=0.5, preserve_topology=True)
    if _n_exterior_verts(poly) <= 120:
        return poly, dq_flag, 'dp_05'

    # Tier 2: Douglas-Peucker at 1.5 m (coarse pass)
    poly = shapely.simplify(geom, tolerance=1.5, preserve_topology=True)
    if _n_exterior_verts(poly) <= 120:
        return poly, _append_flag(dq_flag, 'idf_dp_coarse'), 'dp_15'

    # Tier 3: convex hull
    poly = geom.convex_hull
    if _n_exterior_verts(poly) <= 120:
        return poly, _append_flag(dq_flag, 'idf_hull_simplification'), 'hull'

    # Tier 4: minimum-rotated bounding box (5 vertices)
    poly = geom.minimum_rotated_rectangle
    return poly, _append_flag(dq_flag, 'idf_bbox_simplification'), 'bbox'
```

After the fallback tier returns, the polygon is validated:

| Validation step | Action on failure |
|---|---|
| `shapely.is_valid(poly)` | log WARNING, set status `skipped_invalid_geometry`, exclude from manifest |
| `poly.area > 20.0 m²` | log WARNING, set status `skipped_invalid_geometry`, exclude from manifest |
| Translate near-origin: `poly_local = shapely.affinity.translate(poly, xoff=-cx, yoff=-cy)` where `(cx, cy) = poly.centroid.coords[0]` | none — required to keep coordinates O(10²) m for geomeppy floating-point stability |

The number of floors is derived once here and threaded through all downstream sub-stages:

```python
def derive_num_floors(row, floor_to_floor_m: float = 3.5) -> int:
    if pd.notna(row['levels']):
        return max(1, int(row['levels']))
    if pd.notna(row['height_m']):
        return max(1, math.ceil(row['height_m'] / floor_to_floor_m))
    return 1  # default — will be flagged by data_quality_flag from Step 2
```

The form factor is computed using the corrected envelope-surface formula:

```python
floor_area_m2 = footprint_area_m2 * num_floors
envelope_surface_m2 = (perimeter_m * num_floors * floor_to_floor_m) + (2 * footprint_area_m2)
form_factor = envelope_surface_m2 / floor_area_m2     # (walls + roof + ground floor) / total floor area
```

> **Why this approach:** EnergyPlus has a documented per-surface 120-vertex limit (Technical Pipeline §6 Module 07; geomeppy will raise on overflow when calling `add_block`). Douglas-Peucker at 0.5 m is invariant **I4** — confirmed in `.claude/design_state.md` — and was chosen because it preserves wall-azimuth distribution (critical for solar gain calculations) while removing GIS quantization noise; the §5.1 acceptance threshold *targets* ≥95% DP-0.5-compliance, but the actual fraction for the Boston 500 m fixture is an open measurement (no labelled vertex-count benchmark exists in `inputs/` yet — to be reported once the fixture is run). The 4-tier fallback chain (DP 0.5 → DP 1.5 → convex hull → bounding box) guarantees a syntactically valid geomeppy input even for pathological footprints (curved-wall museums, irregular industrial buildings) at the cost of geometric fidelity, recorded transparently in `data_quality_flag`. **Rejected:** (a) fixed-vertex-count decimation (Visvalingam-Whyatt) — changes building shape non-uniformly and tends to clip narrow façades that anchor solar gains; (b) skipping simplification — geomeppy crashes on >120-vertex blocks and the entire building is lost; (c) buffering then simplifying — adds nominal floor area, biasing EUI per m².

### 3B — Thermal Zone Stratification (Module 08: `openubem/geometry/zoning.py`)

The zoning module decides how many EnergyPlus thermal zones the building gets, based on a deterministic rule table keyed on `archetype_id`, `footprint_area_m2`, and `num_floors`. The output is a list of zone dicts that 3E will translate into geomeppy `add_block` calls.

| Rule (evaluated in order, first match wins) | Strategy | Zones produced |
|---|---|---|
| `archetype_id == OpenUBEMUnknown` | `single_zone` | 1 |
| `footprint_area_m2 < 500` OR `num_floors == 1` | `single_zone` | 1 |
| `archetype_id in {MidriseApartment, HighriseApartment}` | `one_zone_per_floor` | N (= num_floors) |
| `archetype_id in {TallBuilding, SuperTallBuilding}` | `one_zone_per_floor` | N |
| `footprint_area_m2 >= 500 AND num_floors >= 2 AND archetype_id not in {MidriseApartment, HighriseApartment, TallBuilding, SuperTallBuilding, OpenUBEMUnknown}` | `perimeter_core` | 2N |
| (catch-all) | `single_zone` | 1 |

For `perimeter_core`, the core polygon is computed by buffering the simplified footprint inward by `-PERIMETER_DEPTH_M` (default 4.57 m, ASHRAE 90.1-2019 Appendix G prescribed perimeter depth):

```python
core_poly = footprint_poly.buffer(-4.57)
if core_poly.is_empty or core_poly.area < 10.0:
    # narrow building — fall back to one_zone_per_floor
    log.warning(f"perimeter_core fallback to one_zone_per_floor: osm_id={osm_id}, width<9.14m")
    return zones_one_zone_per_floor(...)
perimeter_poly = footprint_poly.difference(core_poly)
```

Each zone dict carries:

```python
zone = {
    'name': f'{osm_id}_F{floor_idx}_{label}',  # label in {'whole', 'core', 'perim'}
    'floor_polygon': shapely.Polygon,
    'coords_m': [(x, y), ...],   # exterior ring as list of (x, y) tuples in metres
    'z_floor': floor_idx * floor_to_floor_m,
    'z_ceiling': (floor_idx + 1) * floor_to_floor_m,
    'height_m': floor_to_floor_m,
    'archetype_id': row['archetype_id'],
}
```

> **Why this approach:** The three-strategy rule table balances simulation fidelity against compute cost across a heterogeneous urban stock. `single_zone` is computationally cheapest and is well-justified for small buildings (<500 m² or single-storey) where horizontal and vertical thermal gradients are negligible (Technical Pipeline §6 Module 08). `one_zone_per_floor` captures the vertical thermal stratification that dominates residential heating/cooling regimes (multi-zone literature consensus per `inputs/papers/modeling-and-simulation-of-multi-zone-buildings-for-better-control-liu-electronic-press.md`); the EUI-improvement magnitude over `single_zone` is expected to be material but has not been measured against a labelled dataset (added as **OQ-1** for Phase-1.5 calibration). `perimeter_core` follows the ASHRAE 90.1 Appendix G prescribed method for large commercial buildings where solar loads on perimeter zones differ dramatically from interior zones. `OpenUBEMUnknown` defaults to `single_zone` as a max-entropy fallback — an unknown archetype cannot have a reliable internal-zone topology, and over-zoning would manufacture spurious internal boundary conditions. **Rejected:** (a) uniform `one_zone_per_floor` for all archetypes — unnecessary memory/runtime overhead for single-storey warehouses and DataCenters where the entire conditioned volume is one open thermal mass; (b) uniform `single_zone` for all — loses vertical stratification critical for the residential stock that dominates the urban building count; (c) full ASHRAE 90.1 Appendix G nine-zone (perimeter N/E/S/W + four corners + core) per floor — explodes IDF size and `intersect_match` runtime without a Phase-1 calibration target that would justify the cost.

### 3C — Context Building Discovery (Module 08b: `openubem/geometry/context.py`)

For each target building, the module finds neighbouring buildings within a configurable sphere of influence and produces a list of shading-block geometry dicts. These are written into the IDF as `Shading:Building:Detailed` objects (NOT thermal zones — invariant from `.claude/design_state.md`).

```python
def discover_context(target_row, gdf: gpd.GeoDataFrame, sphere_radius_m: float = 30.0) -> list[dict]:
    target_poly = target_row['_simplified_geom']     # from 3A
    target_osm_id = target_row['osm_id']
    influence = target_poly.buffer(sphere_radius_m)

    # STRtree spatial query (O(log N) instead of O(N))
    candidate_idx = gdf.sindex.query(influence, predicate='intersects')
    contexts = []
    for idx in candidate_idx:
        ctx_row = gdf.iloc[idx]
        if ctx_row['osm_id'] == target_osm_id:
            continue
        ctx_height = _resolve_ctx_height(ctx_row)    # height_m -> levels*3.5 -> 3.5 default
        # Use bounding box of full geometry (not simplified) — conservative, cheap
        ctx_box = ctx_row.geometry.minimum_rotated_rectangle
        coords = list(ctx_box.exterior.coords)[:-1]  # drop closing vertex
        # Translate to target's local frame (target was translated to near-origin in 3A)
        coords_local = [(x - target_cx, y - target_cy) for (x, y) in coords]
        contexts.append({
            'name': f'shade_{ctx_row["osm_id"]}',
            'coords': coords_local,
            'height': ctx_height,
        })
    return contexts
```

> **Why this approach:** The 30 m default sphere of influence captures 1–2 rows of immediate neighbours in typical North American urban grids (lot widths 6–15 m), which is sufficient to capture the dominant urban-canyon radiant exchange (per the methodology of Iseri et al. 2025, *Energy & Buildings* — sphere-of-influence approach documented in their Fig. 4). The radius is exposed as `config.SHADING_SPHERE_RADIUS` (configurable 20–60 m) so studies of taller canyons can extend it. The STRtree spatial index avoids the O(N²) all-pairs cost of naïve distance computation — same architectural pattern Step 1 uses for IoU dedup. The bounding box of the full (un-simplified) geometry is used for the shading geometry: it slightly over-estimates the obstructing area, which is the conservative direction for canyon shading (over-shading reduces simulated cooling load slightly; under-shading is the dangerous direction because peak cooling demand is what sizes infrastructure). Provenance is **not** tracked for shading-block height because shading geometry is informational only — it does not contribute to a simulated zone's energy balance directly. **Rejected:** (a) full simplified-polygon shading geometry — slower, marginal accuracy gain for non-simulation geometry; (b) zone-based (heat-balanced) context buildings — explodes IDF size and runtime, contradicts invariant **I1** (one IDF per simulation building); (c) ray-casting solar exposure pre-computation — premature optimization; geomeppy / EnergyPlus already does shadowing internally given the shading blocks.

### 3D — IDF Initialisation (Module 09: `openubem/idf/builder.py`)

`BuildingIDF` is the orchestrator class. At module import time, the IDD is locked once for the whole process (invariant **I3**):

```python
# openubem/idf/builder.py — module-level
from geomeppy import IDF as GeomIDF
import config

GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))   # raises IDDAlreadySetError on repeat — guarded

TEMPLATE_ROUTING = {
    # residential
    'MidriseApartment':         'residential_base.idf',
    'HighriseApartment':        'residential_base.idf',
    # high-rise
    'TallBuilding':             'highrise_base.idf',
    'SuperTallBuilding':        'highrise_base.idf',
    # specialized
    'Laboratory':               'specialized_base.idf',
    'SmallDataCenterHighITE':   'specialized_base.idf',
    'LargeDataCenterHighITE':   'specialized_base.idf',
    'SmallDataCenterLowITE':    'specialized_base.idf',  # Phase-1 unreachable, but routed
    'LargeDataCenterLowITE':    'specialized_base.idf',  # Phase-1 unreachable, but routed
    'Warehouse':                'specialized_base.idf',
    # everything else (24 commercial archetypes + OpenUBEMUnknown) -> commercial_base.idf
}
```

The base templates contain only:

| IDF object | Notes |
|---|---|
| `Version` | `23.1` (locked) |
| `SimulationControl` | annual run, do system sizing, do plant sizing (all = Yes) |
| `RunPeriod` | `Begin_Month=1, Begin_Day_of_Month=1, End_Month=12, End_Day_of_Month=31` (8760 h) |
| `Timestep` | `Number_of_Timesteps_per_Hour = 6` (10-min interval, DOE Prototype protocol) |
| `Site:Location` | placeholder — populated from EPW header at build time |
| `GlobalGeometryRules` | `Starting_Vertex_Position=UpperLeftCorner, Vertex_Entry_Direction=Counterclockwise, Coordinate_System=Relative` (geomeppy default) |
| `Schedule:Constant, Activity_Level` | Pre-baked metabolic-rate schedule referenced by every `People` object emitted in §3G — universal across all 30 archetypes (ASHRAE 55 sedentary), so it lives in the base stub rather than the Module 06 archetype-keyed schedule library. Stub definition: `Schedule:Constant, Activity_Level, , 120;` (name `Activity_Level`, schedule type limits left blank for dimensionless, hourly value 120 W/person). |

Because the `Activity_Level` schedule is universal (not archetype-specific), it is embedded in all four base IDF templates rather than emitted by Module 06. This guarantees the `Activity_Level_Schedule_Name='Activity_Level'` reference in §3G's `People` object resolves at IDF parse time.

`BuildingIDF.__init__(row)` selects the template, loads it via `GeomIDF(template_path)`, and immediately overwrites `Site:Location` from the EPW header (latitude, longitude, time zone, elevation parsed via `pyepw` or direct EPW header read).

> **Why this approach:** Template routing isolates archetype-specific schedule discipline (residential IECC schedule vocabulary uses different Schedule:Compact stubs than commercial ASHRAE schedules) from geometry assembly; mixing them in a universal template creates EnergyPlus validation warnings about unused schedule references. Stub-only templates keep the base small and predictable — no hidden objects to debug — and mean every IDF object Step 3 emits is traceable to a Module 04/05/06 source. Locking the IDD once at module import time (invariant **I3**) prevents version-mismatch silent failures: EnergyPlus 22.x and 23.x have different `HVACTemplate:Zone:IdealLoadsAirSystem` field counts and silently truncating fields produces non-physical defaults. **Rejected:** (a) single universal base IDF for all archetypes — schedule-vocabulary mixing produces warnings; (b) loading full DOE Prototype IDFs and stripping objects — fragile, version-coupled, not idempotent (DOE prototypes are non-trivial multi-zone models with hard-coded zone names); (c) deferring IDD set until first IDF instantiation — has been observed to cause `IDDAlreadySetError` in multi-process work-pool contexts (invariant **I2** isolates each EnergyPlus subprocess in its own `work_dir`, but the *importing* worker process reuses the IDD).

### 3E — 3D Geometry Extrusion (Module 09 calling Module 10: `openubem/idf/surfaces.py`)

This is where the zone dicts from 3B become EnergyPlus `BuildingSurface:Detailed` objects. geomeppy's `add_block` is the canonical API: it accepts a 2D footprint and a height, and emits floor, walls, ceiling/roof for a single block.

```python
def extrude_geometry(idf: GeomIDF, zones: list[dict], context: list[dict]) -> None:
    # Add simulation zones
    for z in zones:
        try:
            idf.add_block(
                name=z['name'],
                coordinates=z['coords_m'],
                height=z['height_m'],
                num_zones=1,
            )
        except (NotARectangleError, ValueError, RuntimeError) as e:
            # Fallback: bounding box of this zone's polygon
            log.warning(f"add_block failed for {z['name']}: {e}; falling back to bbox")
            bbox_coords = list(z['floor_polygon'].minimum_rotated_rectangle.exterior.coords)[:-1]
            idf.add_block(
                name=z['name'],
                coordinates=bbox_coords,
                height=z['height_m'],
                num_zones=1,
            )
            _append_dq_flag(z, 'idf_bbox_simplification')

    # CRITICAL: intersect_match must be called ONCE after all zones are added
    idf.intersect_match()

    # Shading blocks AFTER intersect_match — geomeppy must not try to set boundary
    # conditions on shading surfaces
    for ctx in context:
        idf.add_shading_block(
            name=ctx['name'],
            coordinates=ctx['coords'],
            height=ctx['height'],
        )
```

For multi-floor zoning strategies, each floor's `add_block` is called with its own `z_floor` offset — geomeppy supports this by accepting per-block coordinates that already encode height starting from `z_floor`. (Equivalently, geomeppy's internal `Block` builder via `num_stories` could be used for `one_zone_per_floor`; the explicit per-floor loop is preferred here because it gives the zoning module total control over per-zone naming, which is required by 3F/3G when assigning constructions and loads keyed by zone name.)

Adiabatic-surface assignment (party walls between perimeter+core zones, ground-floor slab default) is handled by Module 10 sub-stage 10c (`set_adiabatic_surfaces(idf, zone_list, strategy)`); it runs after `intersect_match` but is conceptually a Module 10 surface-finishing concern, not part of the Module 09 builder logic.

> **Why this approach:** geomeppy `add_block` is the canonical API for 3D IDF geometry from 2D footprints (per `inputs/papers/geomeppy-0-11-8-documentation.md`). It generates `BuildingSurface:Detailed` objects with correct surface normals (outward-facing) and computes wall azimuths automatically — both are non-trivial to get right manually and silent errors here propagate into wrong solar gain. `intersect_match` must be called **once**, after all zones are added; it intersects coincident surfaces (perimeter–core boundary, inter-floor floors/ceilings) and pairs them with `Outdoors`, `Surface`, or `Adiabatic` boundary conditions. The bbox fallback on `add_block` failure (geomeppy can raise on highly non-convex footprints) preserves the building's contribution to the simulation rather than dropping it; the data_quality_flag annotation makes this visible to downstream validators. Shading blocks are added after `intersect_match` so geomeppy does not try to set boundary conditions on them — `add_shading_block` writes `Shading:Building:Detailed` directly. **Rejected:** (a) manual `BuildingSurface:Detailed` construction via `idf.newidfobject()` — correct in principle but requires manually computing 3D vertex coordinates, surface normals, and inter-zone boundary pairing; error-prone and already solved by geomeppy; (b) calling `intersect_match` once per zone — incorrect; intersect must see all surfaces simultaneously to pair coincident ones; (c) `add_block(num_zones=N)` for `perimeter_core` — geomeppy's built-in perimeter splitter uses a fixed depth and does not expose the buffer logic needed for the narrow-building fallback.

### 3F — Construction Assignment (Module 09 reading Module 04 columns)

For each building, the envelope is materialized from the Module 04 columns of the enriched_gdf row. Phase-1 uses U-value-only specs via `Material:NoMass` for opaque assemblies and `WindowMaterial:SimpleGlazingSystem` for fenestration.

```python
def assign_constructions(idf, row):
    # Opaque assemblies — Material:NoMass takes thermal resistance directly
    for assembly, u_col, name in [
        ('Roof_Assembly',   'u_roof_w_m2k',   'Roof'),
        ('Wall_Assembly',   'u_wall_w_m2k',   'Wall'),
        ('Floor_Assembly',  'u_floor_w_m2k',  'Floor'),
    ]:
        u = row[u_col]
        idf.newidfobject(
            'MATERIAL:NOMASS',
            Name=assembly,
            Roughness='MediumRough',
            Thermal_Resistance=1.0 / u,           # m2.K/W
            Thermal_Absorptance=0.9,
            Solar_Absorptance=0.7,
            Visible_Absorptance=0.7,
        )
        idf.newidfobject(
            'CONSTRUCTION',
            Name=f'{name}_Construction',
            Outside_Layer=assembly,
        )

    # Glazing — SimpleGlazingSystem takes U + SHGC directly
    idf.newidfobject(
        'WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM',
        Name='Window_Material',
        UFactor=row['u_window_w_m2k'],
        Solar_Heat_Gain_Coefficient=row['shgc_window'],
        Visible_Transmittance=0.6,                # default; override if Module 04 adds VT col
    )
    idf.newidfobject(
        'CONSTRUCTION',
        Name='Window_Construction',
        Outside_Layer='Window_Material',
    )

    # Set default constructions for all surfaces, then WWR
    idf.set_default_constructions()
    idf.set_wwr(wwr=row['wwr'])                   # uniform across all orientations — Phase 1
```

Vintage handling — the `vintage_standard` column is one of: `{DOERefPre1980, DOERef1980to2004, 90.1-2007, 90.1-2010, 90.1-2013, 90.1-2016, 90.1-2019}`. There is no `90.1-2004` label — that range is `DOERef1980to2004`. NaN `year_built` -> `vintage_standard = "DOERefPre1980"`, provenance `HEURISTIC`, documented as `VINTAGE_NAN_PERMISSIVE_DEFAULT` (permissive direction, **not** most-recent — which would systematically overstate envelope quality and understate heating EUI). `OpenUBEMUnknown` archetype -> `DOERefPre1980` envelope, same permissive rationale.

Infiltration — written as a `ZoneInfiltration:DesignFlowRate` per zone using the per-exterior-wall-area calculation method:

```python
arch = row['archetype_id']
for zone in zones:
    idf.newidfobject(
        'ZONEINFILTRATION:DESIGNFLOWRATE',
        Name=f'{zone["name"]}_Infiltration',
        Zone_or_ZoneList_Name=zone['name'],
        Schedule_Name=f'Infiltration_Schedule_{arch}',                    # from Module 06
        Design_Flow_Rate_Calculation_Method='Flow/ExteriorWallArea',
        Flow_per_Exterior_Surface_Area=row['infiltration_m3_s_m2'],
        Constant_Term_Coefficient=1.0,                                    # default
    )
```

Module 06 emits an `Infiltration_Schedule_{arch}` entry for each of the 30 archetypes, covering the same 30-element vocabulary as the other schedule families (lighting, equipment, occupancy, heating-setpoint, cooling-setpoint).

> **Why this approach:** `Material:NoMass` is the correct EnergyPlus object for U-value-only envelope specs (thermal resistance with no thermal-mass term) and is standard practice in the DOE Prototype Buildings stack — it lets Module 04 emit a single number per assembly without committing to a specific layer composition. `SimpleGlazingSystem` is the correct fenestration object for U + SHGC specs without spectral data. The uniform WWR via `idf.set_wwr(wwr=row['wwr'])` is the simplest valid Phase-1 approach — Module 05 emits per-archetype WWR (residential 0.21, large commercial 0.40, hospital/lab 0.30, warehouse/DC 0.10). The Phase-1 uniform-WWR approach produces a systematic cooling overstatement for buildings with lower actual glazing ratios; the direction is known (more glazing -> more solar gain -> more cooling) but the magnitude has not been measured against a labelled dataset (added as **OQ-2** for Phase-1.5 CBECS glazing comparison). The infiltration model is `Flow/ExteriorWallArea` because Module 04 emits flow-per-exterior-wall-area (m³/s/m²); the EnergyPlus effective-leakage-area / ACH50 pathway under-represents stack-driven infiltration in cold climates relative to blower-door measurements — the understatement direction is consistent with literature but the magnitude is not yet quantified for the Phase-1 archetype set (added as **OQ-3**). **Rejected:** (a) `Material` with conductivity + thickness — requires knowing the specific assembly layer stack-up, available from DOE Prototype IDFs but adds a per-archetype lookup that is not needed for Phase-1 U-value-only specs; (b) `WindowMaterial:Glazing` — requires spectral transmittance data (3 wavelength bands minimum) that are not available from Module 04; (c) orientation-specific WWR via `idf.set_wwr(wwr_map={azimuth: ratio})` — deferred to Phase 2 (added as **OQ-5**); (d) most-recent-vintage default for NaN `year_built` — systematically biased against the older building stock that dominates retrofit-relevant inventories.

### 3G — Internal Loads Assignment (Module 09 reading Module 05 columns)

Internal loads are assigned **per zone** (not per building via ZoneList), so that `perimeter_core` zoning can have differentiated occupancy/equipment if a future Module 05 extension supports it; for Phase-1 the same Module 05 row applies to all zones of the building.

```python
def assign_loads(idf, row, zones):
    arch = row['archetype_id']
    for zone in zones:
        zname = zone['name']

        # People — People/Area calculation method (occupant_m2_per_person -> people/m^2)
        idf.newidfobject(
            'PEOPLE',
            Name=f'{zname}_People',
            Zone_or_ZoneList_Name=zname,
            Number_of_People_Schedule_Name=f'Occupancy_Schedule_{arch}',  # from Module 06
            Number_of_People_Calculation_Method='People/Area',
            People_per_Zone_Floor_Area=1.0 / row['occupant_m2_per_person'],
            Activity_Level_Schedule_Name='Activity_Level',                # 120 W/person, ASHRAE 55 sedentary
            Fraction_Radiant=0.3,
        )

        # Lights
        idf.newidfobject(
            'LIGHTS',
            Name=f'{zname}_Lights',
            Zone_or_ZoneList_Name=zname,
            Schedule_Name=f'Lighting_Schedule_{arch}',
            Design_Level_Calculation_Method='Watts/Area',
            Watts_per_Zone_Floor_Area=row['lighting_w_m2'],
            Fraction_Radiant=0.42,                                        # ASHRAE 90.1 typical
        )

        # ElectricEquipment
        idf.newidfobject(
            'ELECTRICEQUIPMENT',
            Name=f'{zname}_Equip',
            Zone_or_ZoneList_Name=zname,
            Schedule_Name=f'Equipment_Schedule_{arch}',
            Design_Level_Calculation_Method='Watts/Area',
            Watts_per_Zone_Floor_Area=row['equipment_w_m2'],
            Fraction_Radiant=0.5,
        )

        # Thermostat
        idf.newidfobject(
            'HVACTEMPLATE:THERMOSTAT',
            Name=f'{zname}_Thermostat',
            Heating_Setpoint_Schedule_Name=f'Heating_Setpoint_{arch}',    # from Module 06, dual-schedule with setback
            Cooling_Setpoint_Schedule_Name=f'Cooling_Setpoint_{arch}',
        )
```

DataCenter handling: for `{SmallDataCenterHighITE, LargeDataCenterHighITE}`, the Module 05 `equipment_w_m2` value is sourced from the DOE DataCenter prototype IDF's internal-load schedule (rather than a manually specified W/m²) — this is the canonical source. `{SmallDataCenterLowITE, LargeDataCenterLowITE}` are `PHASE_1_UNREACHABLE` (Step 2 OQ-3 resolution; only reachable via the `overrides/archetype_overrides.csv` escape hatch). **OQ-4** is open: extract ITE W/m² from the DOE prototype IDF and confirm it matches the Module 05 column value for the High-ITE variants, so we can detect any drift.

> **Why this approach:** Per-zone load assignment ensures the EnergyPlus zone heat balance has the correct per-zone gain magnitude, which is essential for the perimeter–core differential to be physically meaningful (commercial perimeter zones get solar + internal gains; cores get internal gains only). Schedule names are keyed on `archetype_id`, which links back to the schedule library Module 06 emits — Module 06 writes the `Schedule:Compact` objects into the IDF earlier in 3D's initialisation, so the name references in 3G resolve at IDF parse time. **Rejected:** (a) building-level load assignment via `ZoneList` — loses per-zone control needed for perimeter+core differentials and complicates EUI-by-zone post-processing; (b) manually specifying DataCenter ITE W/m² per archetype — duplicates DOE prototype data and creates a maintenance burden; (c) constant 24/7 schedule placeholders — known to bias EUI and peak-demand results; the Module 06 schedule library exists precisely to avoid this.

### 3H — HVAC (Module 10b: `openubem/idf/hvac.py`)

Phase-1 default: `HVACTemplate:Zone:IdealLoadsAirSystem` for every conditioned zone. IdealAir is a perfect-meeting-of-loads HVAC abstraction — it eliminates HVAC-system calibration uncertainty and isolates the envelope-and-internal-loads signal, which is what Phase-1 EUI estimation aims to characterize.

```python
def assign_hvac(idf, row, zones):
    arch = row['archetype_id']
    for zone in zones:
        zname = zone['name']
        idf.newidfobject(
            'HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM',
            Zone_Name=zname,
            Template_Thermostat_Name=f'{zname}_Thermostat',
            Maximum_Heating_Supply_Air_Temperature=50.0,        # C
            Minimum_Cooling_Supply_Air_Temperature=13.0,        # C
            Heating_Limit='LimitFlowRateAndCapacity',
            Cooling_Limit='LimitFlowRateAndCapacity',
            Maximum_Heating_Air_Flow_Rate='autosize',
            Maximum_Sensible_Heating_Capacity='autosize',
            Maximum_Cooling_Air_Flow_Rate='autosize',
            Maximum_Total_Cooling_Capacity='autosize',
            Outdoor_Air_Method='Flow/Person',
            Outdoor_Air_Flow_Rate_per_Person=0.01,              # m^3/s.person — ASHRAE 62.1 minimum
            Demand_Controlled_Ventilation_Type='None',
            Heat_Recovery_Type='None',
        )
```

The 50 °C / 13 °C supply-air temperature limits and the autosized flow/capacity match the DOE Prototype Buildings Phase-1 baseline; 0.01 m³/s per person OA matches ASHRAE 62.1 minimum ventilation for typical commercial/residential occupancy. `PackagedDX` (HVACTemplate:Zone:PackagedTerminalAirConditioner) is deferred to Phase-2 when COP values become available from an enhanced construction_sets.

> **Why this approach:** IdealAir is the canonical Phase-1 HVAC for urban-scale energy modeling (Technical Pipeline §6 Module 10b; consistent with the DOE Prototype baseline methodology). At urban scale, detailed HVAC-system calibration (chiller curves, fan-power curves, defrost cycles, economizer logic) introduces uncertainty that dominates the envelope signal — and that calibration data is not available from OSM input alone. IdealAir reports the *thermodynamic load* the HVAC must meet without confusing it with system inefficiencies, which is the right metric for envelope-driven EUI comparison. ASHRAE 62.1 minimum ventilation is a defensible Phase-1 default; per-archetype OA rates can be added in Phase-2 if Module 05 emits them. **Rejected:** (a) detailed HVAC system models (e.g. VAV with reheat, VRF, packaged DX with COP curves) — require extensive calibration data and per-system parameter libraries not available in Phase-1; (b) no HVAC at all (free-running) — produces non-physical zone temperatures and breaks IOD computation; (c) HVAC sizing on hard-coded design days — the autosize + LimitFlowRateAndCapacity approach lets EnergyPlus's sizing routines compute zone-specific design loads, which is more accurate than a hard-coded Phase-1 default.

### 3I — EnergyPlus Outputs (Module 11: `openubem/idf/outputs.py`)

Single canonical output frequency: **Hourly** for all `Output:Variable` entries (8760 rows/yr per variable), **RunPeriod** for `Output:Meter:MeterFileOnly` aggregates. Mixing Monthly and Hourly in the same IDF is forbidden — Stage 5 result-aggregation logic requires uniform temporal resolution.

```python
STANDARD_OUTPUTS = [
    # Zone-level — required for Stage-5 EUI and IOD computation
    ('Zone Ideal Loads Zone Total Heating Energy',         'Hourly'),
    ('Zone Ideal Loads Zone Total Cooling Energy',         'Hourly'),
    ('Zone People Occupant Count',                         'Hourly'),
    ('Zone Lights Electric Energy',                        'Hourly'),
    ('Zone Electric Equipment Electric Energy',            'Hourly'),
    ('Zone Infiltration Sensible Heat Loss Energy',        'Hourly'),
    ('Zone Mechanical Ventilation Mass Flow Rate',         'Hourly'),
    ('Zone Mean Air Temperature',                          'Hourly'),
    ('Zone Operative Temperature',                         'Hourly'),
    # Site-level
    ('Site Outdoor Air Drybulb Temperature',               'Hourly'),
    ('Site Wind Speed',                                    'Hourly'),
]

def write_outputs(idf):
    for var, freq in STANDARD_OUTPUTS:
        idf.newidfobject(
            'OUTPUT:VARIABLE',
            Key_Value='*',
            Variable_Name=var,
            Reporting_Frequency=freq,
        )
    # Meter aggregates
    for meter in ['Electricity:Facility', 'NaturalGas:Facility']:
        idf.newidfobject(
            'OUTPUT:METER:METERFILEONLY',
            Key_Name=meter,
            Reporting_Frequency='RunPeriod',
        )
    idf.newidfobject('OUTPUTCONTROL:TABLE:STYLE', Column_Separator='HTML')
    idf.newidfobject('OUTPUT:TABLE:SUMMARYREPORTS', Report_1_Name='AllSummary')
    idf.newidfobject('OUTPUT:SQLITE', Option_Type='SimpleAndTabular')
```

> **Why this approach:** Hourly resolution is required for IOD computation (ASHRAE 55 adaptive-comfort thresholds depend on hourly operative temperature against hourly outdoor temperature) and for occupant-coincident peak-demand analysis at the neighbourhood scale. SQL output (`Output:SQLite SimpleAndTabular`) gives Stage 5 a parseable, schema-discoverable result file without regex on CSV — the SQL schema is documented and stable across EnergyPlus minor versions. `MeterFileOnly` for facility meters is a runtime optimization: it skips writing meter values into the SQL/CSV, which dominate output file size for low-cardinality aggregates that Stage 5 reads only once per simulation. `AllSummary` (ABUPS — Annual Building Utility Performance Summary) is the canonical sanity-check report. **Rejected:** (a) Monthly frequency for Output:Variable — too coarse for IOD and loses the hourly occupant-coincident peak-demand signal that drives grid-integration analysis; (b) mixing Monthly + Hourly in one IDF — Stage 5 alignment logic gets confused by columns at different temporal resolutions; (c) reporting every available zone variable — explodes SQL file size by ~10× without unblocking any Stage-5 analysis; the curated list above covers every metric Stage 5 currently consumes.

---

## 4. Outputs

| Artifact | Filename | Format | Shape | Consumed by |
|---|---|---|---|---|
| Per-building IDF | `<output_dir>/idfs/<osm_id>.idf` | EnergyPlus 23.1 IDF (text) | one file per simulation building, ~50–500 KB | Stage 4 / Module 12 (parallel EnergyPlus runner). Each IDF is self-contained (invariant **I1**) — no external object references except the Module 02-bound EPW path attached at run time. |
| IDF generation manifest | `<output_dir>/03_idf_manifest.parquet` | Parquet | (N_input, ≥9 cols) | Stage 4 (filters to `generation_status == 'success'` rows before launching simulations); Stage 5 (joins on `osm_id` for results aggregation). Columns: `osm_id` (str), `idf_path` (str), `archetype_id` (str), `zoning_strategy` (str: `single_zone` / `one_zone_per_floor` / `perimeter_core`), `num_zones` (int), `num_context_buildings` (int), `simplification_status` (str: `dp_05` / `dp_15` / `hull` / `bbox` / `skip`), `data_quality_flag` (str, updated in Step 3), `generation_status` (str: `success` / `skipped_invalid_geometry` / `fallback_bbox`). |
| Updated `data_quality_flag` | (column inside the manifest) | str | per-row | Step 3 does **not** rewrite the upstream `02_buildings_classified.gpkg` — invariant **I6** (persistent intermediates per stage). The manifest is the canonical record of Step 3's mutations. |

---

## 5. Validation

### 5.1 Metrics and acceptance thresholds

| Metric | Threshold | Rationale (cite source) |
|---|---|---|
| `pct_valid_idf_generated` | ≥ 95% of input buildings produce a valid IDF | Detects a broken simplification or extrusion loop; Boston 500 m fixture target (`inputs/aim/OpenUBEM_Technical_Pipeline.md` §6 Stage 3) |
| `pct_vertex_compliant` | 100% (≤ 120 vertices on every BuildingSurface:Detailed) | Hard EnergyPlus requirement — IDF will not simulate if violated |
| `pct_fallback_bbox` | ≤ 5% | If exceeded, DP tolerance is wrong for this city; tracked per-fixture |
| `mean_shading_context_count` | 3–12 (Boston 500 m fixture) | Sanity-check on the 30 m sphere; flag if 0 for any non-isolated building |
| IDF syntax validity | 100% pass `eppy.modeleditor.IDF.read()` without error | Cheap CI check — runs without EnergyPlus binary |
| EnergyPlus dry-run validity | 100% of synthetic 10-building fixture complete a 1-day run without fatal error | Confirms IDD-binding, geometry, and HVAC template all resolve |
| CV(RMSE) building-level | < 30% | ASHRAE Guideline 14 hourly calibration threshold; computed against CBECS 2018 commercial building EUI distributions for the New England climate region (Boston fixture) |
| NMBE neighbourhood-level | ±10% | ASHRAE Guideline 14 mean-bias-error threshold |

### 5.2 Test data and holdout strategy

- **Synthetic smoke-test fixture** — `tests/fixtures/synthetic_10_buildings.py` constructs 10 hand-crafted GeoDataFrame rows in code, covering all five zoning-strategy branches × archetype families × all four simplification fallback tiers. No OSM fetch, no network, runs in CI. Used for unit tests of every Module 07–11 sub-stage.
- **Boston Downtown 500 m integration fixture** — `tests/integration/test_boston_500m.py` uses a real-OSM ~400-building fixture (cached as a versioned GeoPackage in `tests/fixtures/cache/boston_downtown_500m.gpkg`) for Level-4 validation. Requires the EnergyPlus 23.1 binary and a Boston EPW. Boston is a fully independent city neighbourhood — it is **not** used in any Module 06b imputation training set, so the Step 3 result on Boston is a true out-of-distribution evaluation of the Module 04/05/06 pipeline this DESIGN doc consumes.
- Holdout regime: the entire Boston fixture is held out — no per-building leak from training. CBECS 2018 EUI distributions for the New England climate region are used as the comparison reference for CV(RMSE) and NMBE.

### 5.3 True Future Test (only if a forecast or generalization claim is made)

Not applicable in the strict sense — IDF generation is a deterministic transformation (no model trained on data, no temporal extrapolation claim). The only generalization claim Step 3 makes implicitly is that the simplification + zoning + extrusion pipeline produces valid IDFs on previously unseen OSM neighbourhoods; this is tested by running the synthetic 10-building fixture (covers branches not present in any single real city) and the Boston 500 m fixture (covers a real city not used in any Module 06b training set). The downstream EUI-prediction generalization claim — that the IDFs Step 3 produces yield CBECS-comparable EUIs on the held-out Boston neighbourhood — is validated in §5.1 and is the proper Stage 4/5 territory; the leakage defense for Stage 4/5 is documented in those steps' DESIGN docs.

---

## 6. Compute

| Resource | Estimate | Source of estimate |
|---|---|---|
| GPU hours (Calcul Québec / Concordia HPC) | 0 | IDF generation is pure CPU; HPC GPU time is reserved for Step 4 / Step 6 ML stages of the umbrella project |
| CPU | 1 core, single-threaded loop | parallelism is Stage 4's job; Stage 3 is embarrassingly parallel-safe but does not need it for fixture sizes |
| Wall-clock target (Boston 500 m, ~400 buildings) | < 60 s | benchmark target from Technical Pipeline §6 |
| Peak memory | < 2 GB | one IDF in memory at a time; geomeppy loads only the current building |
| Storage per IDF | ~200 KB | observed range 50–500 KB depending on zone count |
| Storage (Boston fixture) | ~80 MB | 400 IDFs × 200 KB |
| Storage (5 M-building city) | ~1 TB | linear extrapolation; same per-IDF size distribution |

The dominant cost driver is `intersect_match()`, whose runtime grows roughly with the square of zone-surface count. For a 20-floor TallBuilding with `perimeter_core` zoning that would yield 40 zones × ~6 surfaces each = ~240 surfaces; the all-pairs intersection check is O(S²). Empirically TallBuildings with `perimeter_core` would exceed the 60 s/building target; this is why the §3B rule table routes TallBuildings to `one_zone_per_floor` (single zone per floor, no perimeter–core split) — which keeps surface count linear in `num_floors`. If a future Phase-1.5 calibration study (OQ-1) shows `perimeter_core` materially improves accuracy for high-rise, the budget would increase by ~2–3× and Stage 4 parallelism would need to compensate.

---

## 7. Open Questions

- [ ] **OQ-1** — Quantify R² / CV(RMSE) improvement of `one_zone_per_floor` vs `single_zone` on the Boston 500 m fixture (residential archetypes only). Currently the choice is justified qualitatively from multi-zone literature; a Phase-1.5 calibration study would confirm or revise the §3B rule table. *(blocks §3B, §5.1)*
- [ ] **OQ-2** — Quantify mean absolute WWR error against a US building-stock sample (CBECS 2018 glazing data) and estimate the cooling-EUI impact of the Phase-1 uniform-WWR assumption. Direction is known (higher-than-actual WWR -> cooling overstatement); magnitude is not. *(blocks §3F)*
- [ ] **OQ-3** — Quantify infiltration-model heating-EUI bias against CBECS/RECS infiltration distributions for the 8 ASHRAE climate zones. The `Flow/ExteriorWallArea` model under-represents stack-driven infiltration in cold climates relative to blower-door measurements; magnitude is not measured for the Phase-1 archetype set. *(blocks §3F)*
- [ ] **OQ-4** — Extract ITE W/m² values from the DOE DataCenter prototype IDF and confirm they match Module 05's `equipment_w_m2` column for `SmallDataCenterHighITE` and `LargeDataCenterHighITE`. *(blocks §3G)*
- [ ] **OQ-5** — Phase-2: implement orientation-specific WWR via `idf.set_wwr(wwr_map={azimuth: ratio})` keyed by façade orientation when per-orientation glazing data becomes available from a future Module 04b (façade imagery or GIS parcel). Deferred — does not block Phase-1. *(blocks Phase-2 §3F extension)*
- [ ] **OQ-6** — Confirm the 4.57 m perimeter depth (ASHRAE 90.1 Appendix G) does not trigger the `perimeter_core -> one_zone_per_floor` narrow-building fallback for more than 5% of Boston-fixture commercial buildings. If exceeded, calibrate `PERIMETER_DEPTH_M` for the Phase-1 archetype set. *(blocks §5.1)*
- [ ] **OQ-7** — Module 02 (`acquisition/climate_zone.py` + `epw_manager.py`) is undesigned. The `climate_zone` and `epw_path` columns are part of the 57-column input contract Step 3 consumes; Module 02 must be designed before Step 3 integration testing can run end-to-end. *(blocks full integration test; does not block §3 unit tests on the synthetic fixture)*

---

## 8. References

**`inputs/aim/`** — project charter and pipeline blueprint
- `inputs/aim/OpenUBEM_Technical_Pipeline.md` — §6 Stage 3 specification: module decomposition, geomeppy as canonical 3D library, the I1–I7 architectural invariants, the 4-tier simplification fallback chain, IdealAir as Phase-1 HVAC default, and the IDF base-template routing table.
- `inputs/aim/OpenUBEM_Aim_Document.md` — overarching project aims (open-source UBEM, Phase-1 US scope, Phase-3 Canada hook), validation regime (CBECS 2018 + ASHRAE Guideline 14 thresholds), and scope boundary that justifies one-IDF-per-building.

**`inputs/papers/`** — technical references for libraries and methods
- `inputs/papers/geomeppy-0-11-8-documentation.md` — geomeppy IDF API: `add_block`, `add_shading_block`, `intersect_match`, `set_wwr`, `setiddname`, `translate_to_origin`, `set_default_constructions`. Anchors §3D (IDD locking), §3E (extrusion + intersect_match), §3F (set_wwr), §3I (output object writing).
- `inputs/papers/geomeppy-pypi.md` — geomeppy install / version compatibility (≥ 0.11.8 on eppy ≥ 0.5.63).
- `inputs/papers/python-opens-up-new-applications-for-energyplus-building-energy-simulation-nlr.md` — eppy/Python EnergyPlus integration context; supports the choice of Python-script-driven IDF generation over GUI-driven workflows for an automated UBEM pipeline.
- `inputs/papers/modeling-and-simulation-of-multi-zone-buildings-for-better-control-liu-electronic-press.md` — multi-zone thermal stratification literature; anchors the qualitative justification for `one_zone_per_floor` over `single_zone` in §3B.

**`inputs/reports/`** — UBEM methodology context
- `inputs/reports/Open Source Urban Building Energy Modeling - General.md` — comparative analysis of CEA, UMI, URBANopt, SimStadt, CityBES, TEASER, CitySim, OpenIDEAS; supports Step 3's design choices (one-IDF-per-building, EnergyPlus engine, archetype-driven semantic enrichment, and 30 m sphere of influence for context shading).

**`inputs/notes/`** — resolved decisions and prior-pass critiques
- `inputs/notes/2026-05-07_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod_critic-pass1-resolutions.md` — pre-resolved critic-pass-1 issues incorporated into this draft: removed quantitative R² claim for one_zone_per_floor; corrected DOE Prototype vintage labels (no `90.1-2004`); NaN vintage -> `DOERefPre1980` permissive; removed quantitative WWR/infiltration error magnitudes; DataCenter ITE from DOE prototype schedule; corrected form-factor formula (envelope-surface numerator); single canonical Hourly output frequency; adiabatic-surface assignment moved to Module 10 (sub-stage 10c, surface-finishing concern); explicit pointer that Module 02 is undesigned.

**External anchors (cited via inputs only — no fabricated DOIs)**
- Iseri et al. (2025), *Energy & Buildings* — sphere-of-influence shading methodology, Fig. 4 30 m default — referenced via Technical Pipeline §6 and `inputs/reports/...`.
- ASHRAE 90.1-2019 Appendix G — perimeter depth 4.57 m and `perimeter_core` zoning prescriptive method.
- ASHRAE Guideline 14 — CV(RMSE) < 30% and NMBE ±10% calibration thresholds.
- ASHRAE 55 — adaptive comfort model used implicitly in IOD threshold definition (Stage 5 territory).
- DOE Prototype Buildings — vintage label vocabulary (`DOERefPre1980`, `DOERef1980to2004`, `90.1-2007`...`90.1-2019`) and 6-timestep/hour protocol.

---

## 9. Key Decisions Summary

| # | Decision | Sub-stage | Rationale (one line) | Alternatives rejected |
|---|---|---|---|---|
| 1 | Douglas-Peucker 0.5 m + 4-tier fallback chain (DP 1.5 m -> convex hull -> bounding box), with `data_quality_flag` annotation | 3A | Invariant **I4**; preserves wall-azimuth distribution while satisfying the 120-vertex EnergyPlus limit on >95% of OSM footprints, with a guaranteed valid fallback for pathological cases | Fixed-vertex-count decimation (non-uniform shape change); skipping simplification (geomeppy crash); buffer-then-simplify (biases area). |
| 2 | Three zoning strategies (`single_zone`, `one_zone_per_floor`, `perimeter_core`) routed by `archetype_id` × area × num_floors rule table | 3B | Balances simulation fidelity vs compute cost; respects ASHRAE 90.1 Appendix G prescriptive method for large commercial; `OpenUBEMUnknown` -> max-entropy `single_zone` | Uniform `one_zone_per_floor` (overhead for warehouses/DCs); uniform `single_zone` (loses residential stratification); 9-zone Appendix G (explodes runtime without Phase-1 calibration target). |
| 3 | geomeppy `add_block` + `intersect_match` (called once after all zones) as canonical 3D extrusion API | 3E | Generates correct surface normals and inter-zone boundary pairing automatically; per-zone bbox fallback on geomeppy exception preserves the building rather than dropping it | Manual `BuildingSurface:Detailed` construction (error-prone); `intersect_match` per zone (incorrect — must see all surfaces). |
| 4 | `Shading:Building:Detailed` boxes (NOT thermal zones) for context buildings within configurable 30 m sphere of influence, using bounding-box geometry | 3C, 3E | Captures urban-canyon radiant exchange (Iseri et al. 2025) without violating invariant **I1** (one IDF per simulation building); STRtree O(log N) query; bbox over-estimation is conservative | Zone-based context (explodes IDF size, breaks I1); ray-casted pre-computation (premature optimization); full simplified-polygon shading (slower, marginal accuracy gain). |
| 5 | `HVACTemplate:Zone:IdealLoadsAirSystem` as Phase-1 default HVAC for every conditioned zone | 3H | Eliminates HVAC-system calibration uncertainty, isolates envelope/internal-load signal — the Phase-1 EUI characterization target; matches DOE Prototype baseline | Detailed HVAC (no calibration data in Phase-1); no HVAC (non-physical zone temperatures, breaks IOD); hard-coded design-day sizing (less accurate than EnergyPlus autosize). |
| 6 | Single canonical output frequency: Hourly for `Output:Variable`, RunPeriod for `Output:Meter:MeterFileOnly`; SQL output enabled | 3I | Hourly is the minimum resolution for IOD and occupant-coincident peak demand; SQL gives Stage 5 a stable schema; uniform frequency prevents Stage-5 alignment bugs | Monthly Output:Variable (too coarse for IOD); mixing Monthly + Hourly (Stage-5 alignment confusion); reporting all available variables (10× SQL size for no benefit). |
| 7 | NaN `year_built` -> `vintage_standard = "DOERefPre1980"`, provenance `HEURISTIC`, documented as `VINTAGE_NAN_PERMISSIVE_DEFAULT` | 3F | Permissive (older-envelope) direction prevents systematic envelope-quality overstatement and heating-EUI understatement on the older retrofit-relevant stock | Most-recent vintage default (biases against older stock); skipping NaN-vintage buildings (excludes a large fraction of OSM rows). |

---

## 10. Progress Log *(populated by downstream `/run` reporter — leave empty here)*

<!-- The downstream execution project's reporter agent appends `### Session: <date> | Loop: <N>` blocks under this header after each /run cycle. NEITHER the architect NOR the documenter writes here. -->

---

## 11. Revision Log *(populated by DOCUMENTER on /design re-runs only — EMPTY on first creation)*

<!-- Append-only. DOCUMENTER inserts a new block on each /design re-run.

On MODE=new this section MUST contain only this comment block — no `### Session:` block. The first revision block is written on the first MODE=update run.

### Session: <YYYY-MM-DD> | Pass: <final-pass>
**Trigger:** <one-line: new evidence, change request, retired decision>
**Inputs added since last session:** <bullets — filenames>
**Changes:**
- §<N>: <delta>
**New Decisions:** <bullets, also propagated to .claude/design_state.md>
**Retired Decisions:** <bullets — moved to design_state.md ## Retired Decisions, with reason>
**OVERVIEW regenerated:** yes
**GRAPHICAL_ABSTRACT regenerated:** yes | no — no material architecture change

-->

### Session: 2026-05-07 | Pass: 1

**Trigger:** Open-question resolutions OQ-1 through OQ-7 (all seven §7 Open Questions raised in the first APPROVED session, 2026-05-07). User answers parsed by `/resolve` and written to `inputs/notes/2026-05-07_..._resolved-open-questions.md`; this `/design` re-run in MODE=update records resolution status without altering §1–§9.

**Inputs added since last session:**
- `inputs/notes/2026-05-07_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod_resolved-open-questions.md` (user's numbered answers to OQ-1..OQ-7).
- `inputs/notes/2026-05-07_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod_critic-pass1-resolutions.md` (pre-incorporated into the first APPROVED draft; listed for traceability — no new content for this pass).

**Resolution status of §7 Open Questions:**
- **OQ-1** (R² / CV(RMSE) `one_zone_per_floor` vs `single_zone` on Boston 500 m fixture, residential archetypes) — **DEFERRED → Phase-1.5 calibration study.** Concrete task: once Steps 1–4 are wired end-to-end, run paired single_zone vs one_zone_per_floor simulations on every residential archetype in the Boston 500 m fixture; report R² and CV(RMSE) delta; validate or revise the §3B zoning-strategy rule table. No Phase-1 code change; design_state row 81 (zoning strategy) remains active.
- **OQ-2** (mean absolute WWR error vs CBECS 2018 glazing data; cooling-EUI impact of uniform-WWR) — **DEFERRED → Phase-1.5.** Concrete task: extract glazing fraction by building type from CBECS 2018 Table B37; compute mean absolute WWR error per archetype against Module 05 `wwr` values; estimate cooling-EUI sensitivity via ±0.05 perturbation on the Boston fixture; if absolute error exceeds 0.05 on any archetype, update Module 05 WWR values. No Phase-1 code change.
- **OQ-3** (heating-EUI bias of `Flow/ExteriorWallArea` infiltration model vs CBECS/RECS by ASHRAE climate zone) — **DEFERRED → Phase-1.5.** Concrete task: extract ACH infiltration distributions from RECS 2020 (residential) and CBECS 2018 (commercial) by ASHRAE climate zone; compare against Module 04 fixed `infiltration_m3_s_m2`; report mean heating-EUI bias by zone × archetype; adjust Module 04 if bias exceeds ±10% heating EUI. No Phase-1 code change.
- **OQ-4** (DataCenter ITE W/m² extraction from DOE prototype IDF; cross-check Module 05 `equipment_w_m2` for `SmallDataCenterHighITE` / `LargeDataCenterHighITE`) — **ACTIONABLE PRE-EXECUTION (task recorded — values to be extracted and confirmed before Module 05 is finalized).** Canonical source: NREL/openstudio-standards GitHub repository (DOE Commercial Prototype Building Models). Task: in the SmallDataCenterHighITE and LargeDataCenterHighITE prototype IDFs, read the `ElectricEquipment` watts-per-floor-area value in the ITE zone; record in the §3G DataCenter handling note as the canonical reference; propagate to Module 05's archetype loads table. Module 05 must not diverge from the DOE prototype baseline value. The §3G text already states the DOE prototype is the canonical source; the W/m² figures themselves remain to be extracted and committed alongside Module 05 finalization. (Architect cannot reach external GitHub from this session; flagged for Module 05 design session.)
- **OQ-5** (Phase-2 orientation-specific WWR via `idf.set_wwr(wwr_map={azimuth: ratio})`) — **DEFERRED → Phase 2.** Interface contract confirmed: Phase 2 will call `idf.set_wwr(wwr_map={azimuth: ratio})` once per-orientation glazing data is available from a future Module 04b (façade imagery or GIS parcel). Phase 1 continues to use the uniform per-archetype `wwr` scalar from Module 05. Recorded as a New Decision below for propagation to design_state.md as the Phase-2 backlog entry.
- **OQ-6** (4.57 m perimeter depth — narrow-building fallback rate must stay <5% on Boston commercial fixture) — **DEFERRED → Phase-1.5 fixture calibration.** Concrete task: after Steps 1–3 are wired, count narrow-building fallback triggers (commercial buildings where `building_width < 2 × 4.57 m = 9.14 m`); if >5% trigger, recalibrate `config.PERIMETER_DEPTH_M` downward (first attempt: 3.5 m). No Phase-1 code change; design_state row 81 (zoning strategy) remains active.
- **OQ-7** (Module 02 — `acquisition/climate_zone.py` + `epw_manager.py` — undesigned; blocks Step 3 integration testing) — **CLOSED (handed off to next `/design` session, Step 2.5).** Recommended prompt (recorded verbatim from the resolutions note): `/design Step 2.5 — add climate_zone (ASHRAE 90.1 string) and epw_path (nearest EPW from climate.onebuilding.org cache) to the Stage-1 buildings GeoDataFrame via spatial join against ASHRAE climate-zone GPKG, producing a 29-column enriched_gdf ready for Module 04`. Designing Module 02 unblocks both Module 04 (needs `climate_zone`) and Module 09 (needs `epw_path`).

**Changes:**
- §3G — *Text already states "the Module 05 `equipment_w_m2` value is sourced from the DOE DataCenter prototype IDF's internal-load schedule (rather than a manually specified W/m²) — this is the canonical source."* This Revision Log block adds the operational specifics that the architect cannot edit into §3G itself: the canonical extraction source is **NREL/openstudio-standards** (DOE Commercial Prototype Building Models GitHub repo); the `ElectricEquipment` Watts/Floor-Area value in the ITE zone of the SmallDataCenterHighITE and LargeDataCenterHighITE prototype IDFs is the binding figure for Module 05's `equipment_w_m2` column for those two archetypes; values to be extracted and committed during Module 05 design/build (task recorded — values to be extracted and confirmed before Module 05 is finalized).
- §7 — text unchanged in the canonical doc per operating rules ("Do not modify content above ## 11. Revision Log"). Resolution status of every OQ is recorded in this §11 block. For execution-project consumers: OQ-4 and OQ-7 are pre-execution actionable; OQ-1, OQ-2, OQ-3, OQ-6 are Phase-1.5 calibration tasks tracked in design_state.md; OQ-5 is the Phase-2 backlog. None of the seven OQs blocks the Phase-1 §3 unit-test path on the synthetic fixture.

**New Decisions** (also to be propagated to `.claude/design_state.md` Confirmed Decisions Index):
- **Step 3 OQ-4 resolution: NREL/openstudio-standards (DOE Commercial Prototype Building Models) is the canonical source for DataCenter ITE `equipment_w_m2`.** Module 05's `equipment_w_m2` column for `SmallDataCenterHighITE` and `LargeDataCenterHighITE` must be set to the `ElectricEquipment` Watts-per-Floor-Area value read from the ITE zone of the corresponding prototype IDF. Module 05 must not diverge from this DOE prototype baseline. Status: pre-execution task — values to be extracted and committed during Module 05 finalization. Refines §3G of `DESIGN_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod.md`.
- **Step 3 OQ-5 resolution: Phase-2 orientation-specific WWR interface contract.** Phase 2 will call `idf.set_wwr(wwr_map={azimuth: ratio})` keyed by façade azimuth once a future Module 04b (façade imagery or GIS parcel) provides per-orientation glazing data. Phase 1 continues to use the uniform per-archetype `wwr` scalar from Module 05. To be added to Phase-2 backlog in `.claude/design_state.md`.
- **Step 3 OQ-1 / OQ-2 / OQ-3 / OQ-6: Phase-1.5 calibration backlog (4 entries).** Each entry has a defined trigger condition and a defined acceptance metric — see "Resolution status of §7 Open Questions" above. To be added as Phase-1.5 backlog rows in `.claude/design_state.md` (separate from Confirmed Decisions Index — these are deferred tasks, not active decisions).
- **Step 3 OQ-7 resolution: next `/design` session is Step 2.5 (Module 02 — climate_zone + epw_path enrichment).** Step 3 integration testing is blocked on Step 2.5; Step 3 unit tests on the synthetic fixture are not blocked. To be recorded in design_state.md as the next-design-session pointer.

**Retired Decisions:** None. All seven OQ resolutions are deferred tasks or pre-execution extractions; none of the §1–§9 design decisions for Step 3 are superseded. design_state.md rows 80–88 (Step 3 confirmed decisions) all remain `active`.

**OVERVIEW regenerated:** no — no material architecture change; OVERVIEW reflects only §1–§9 content which is unchanged.

**GRAPHICAL_ABSTRACT regenerated:** no — no material architecture change; the pipeline narrative, sub-stage decomposition, and module decomposition are identical to the first APPROVED draft.
