# OpenUBEM European Locations — Engineering Walkthrough & Operational Guide

> 🟢 **FROZEN 2026-08-28. This document is HISTORY and is no longer appended to.**
> Current truth lives in [`../STATE_european_locations_v2.md`](../STATE_european_locations_v2.md).
> Everything below is kept unchanged and remains the authority on how each fact was obtained:
> every ruling, finding, gate table, caveat list and acceptance record. Nothing here was
> rewritten in the move. **Do not add to this file** — record new state in the v2 document.

## Step-by-Step Manual for Standards Insertion, Building Stock Enrichment, Procedural Layout Slicing, and BEM Simulation Coupling with GSSCanada

- **Document Version**: `1.0.0-PROD`
- **Location in Repo**: [`docs/docs_ACTIVE/europeanLocations/previous/WALKTHROUGH_european_locations.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/previous/WALKTHROUGH_european_locations.md)
- **Sister MVP Implementation Spec**: [`docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md)
- **GSSCanada Reference**: [`C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\IMP_step8\4thJ_08_bemSimulation_IMP.md`](file:///C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ/Step8_docs/IMP_step8/4thJ_08_bemSimulation_IMP.md)
- **Scientific & Algorithmic Provenance** — three distinct tiers, never conflated (citation rule fixed 2026-08-23):
  1. **Published paper**: *Iseri et al. (2025), Energy and Buildings 337, 115620* — method and sample (593 residential buildings of 642; 6,458 dwelling units).
  2. **Raw dataset**: `IMP_step8/resources/AllV{1,2,3,4}_updated2023June.csv`.
  3. **Derived re-analysis (2026-08-22) and algorithm sources**: `IMP_step8/outputs/simulation_results_analysis_report.md`, `floor_layout_generation_report.md`, `kbem_ankara_pipeline.py`, `IMP_step8/extracted_scripts/custom_scripts_catalog.json`. **Not the published paper**; cite by filename.
- **Core OpenUBEM Docs**: [`OpenUBEM_fundamentals.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_fundamentals.md), [`OpenUBEM_inputs_reference.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md), [`OpenUBEM_imputation_methods.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_imputation_methods.md), [`simulated_vs_reconstructed_methodology.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/simulated_vs_reconstructed_methodology.md), [`OpenUBEM_debug_References.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_debug_References.md)
- **Reusable Figure/Table Assets**: [`content/`](content/README.md)
- **Parent Step 8 Authorities (tier 1)**: `Step8_docs/4thJ_08_bemSimulation.md`, `Step8_docs/4thJ_08_bemSimulation_val.md`, `Step8_docs/outputs_step8/archetype_parameter_provenance.md`, and the existing tables `Step8_docs/outputs_step8/archetype_parameters_{es,uk,it}.csv` (relative to `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\`).
- **Revision**: v1.3 (2026-08-23) — source-alignment notes added in place, §12 executor contract added for external LLM sessions (Codex / Antigravity). Nothing from v1.0–v1.2 was removed.

> **Document role.** The MVP is the principal technical specification. This walkthrough is the execution layer: ordered tasks, commands, evidence requirements, stop conditions, and an append-only progress log. When scientific wording differs, update the MVP first and make this document point to that decision.
>
> **France scope.** France is included now in residential acquisition/filtering, archetype preparation, neighbourhood/layout construction, IDF/weather work, and controlled baseline physical simulations. France-specific occupant diaries and non-zero occupant-effect schedules remain a future task and must not be counted in the ES/GB/IT 102-archetype/510-run occupant campaign.

> **Implementation-status notice (v1.1 review, 2026-08-22).** The original v1.0 walkthrough below is retained in full for provenance. Several snippets are proposed interfaces rather than runnable calls against OpenUBEM `0.1.0`. Use the code-audited procedure in **Section 9** as the operational authority until the European adapters are implemented and their tests pass.
>
> **Speed/pre-occupant extension.** Section 10 provides the operational Speed runbook, including optional 48/64-way concurrency and the input-map/control pilots required before occupant injection.

> **Citation audit (v1.2, closed 2026-08-23).** Nine numeric claims attributed to *Iseri et al. (2025)* across this document and the MVP failed source verification and were corrected under [`debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md`](debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md) (`CLOSED`). In this document specifically:
> - **§1** — "277 buildings" corrected to **593**; the invented "top-floor 15–25%" replaced by the sourced **+148.8%**; the corner-unit "25–40%" withdrawn as `UNSOURCED` with no substitute number invented.
> - **§4.3** — the Ankara fallback rate "8.3% (25/277)" is `UNSOURCED`; the European rate must be measured by `GEO-04` and `GEO-10`, not inherited.
> - **§7.1** — the `reconstruct_eui` snippet is marked `TARGET API`; that function does not exist in OpenUBEM `0.1.0`. The real function is `reconstruct_frame`.
> - **§7.4** — the IOD figures are real but come from the 2026-08-22 re-analysis, and are V1-versus-V4 iterations rather than a direct building-level/dwelling-level pair.
> Apply the same rule to any new figure added here: name its source file and line, or mark it `UNSOURCED`.

> **Source-alignment pass (v1.3, 2026-08-23).** [MVP §11](MVP_european_locations.md#11-v13-source-alignment-addendum--facts-from-the-parent-step-8-authorities) now carries the tier-1 facts this runbook must execute against. Four of them change commands in this document and are marked in place with a `v1.3` note:
> - **§2.1 / §9.3** — the 102-archetype parameter tables already exist (`outputs_step8/archetype_parameters_{es,uk,it}.csv`); the registry step reconciles them rather than re-deriving from the workbooks. The canonical file name is `tabula_archetypes_gb.json` (§9.3), not `_uk.json` (§2.1).
> - **§2.1 / §4.1** — the example epoch `ES.04 = 1980–2006 "NBE-CT-79"` and the `map_construction_vintage` boundaries do not match the verified TABULA bands (`ES.04` = 1960–1979; `ES.05` = 1980–2006, labelled `CTE-79`). Use MVP Table 15.
> - **§5.4** — the per-country ventilation rates 0.40 / 0.59 / 0.30 h⁻¹ are TABULA *national* rows; the campaign value is the EU row, 0.4 h⁻¹ for every archetype (MVP §11.2).
> - **§9.5 / §9.8** — the weather windows are ruled (`es` 2009–2010, `uk` 2014–2015, `it` 2013–2014) but not acquired; zero-at-home diary days are an explicit schedule branch; the chaining rule (decision 14) blocks every `f>0` cell.
>
> **§12** adds the executor contract for sessions run on external LLM tooling (Codex GPT, Gemini Antigravity): what a slice is, what evidence it returns, what it may never do, and the first slice to execute.

---

## 1. Overview & Operational Pipeline

This walkthrough provides an operational, step-by-step engineering guide for executing European Urban Building Energy Modeling (UBEM) simulations in OpenUBEM. It walks through the end-to-end operational lifecycle: from ingesting CEN/ISO building codes and TABULA archetypes, to procedurally carving multi-dwelling floor plans with unconditioned stairwell cores, assembling watertight EnergyPlus models, and injecting GSSCanada stochastic demographic occupancy diaries.

```
+---------------------------------------------------------------------------------------------------+
|                        SIX-PHASE EUROPEAN UBEM SIMULATION PIPELINE                                |
+---------------------------------------------------------------------------------------------------+
| Phase 1: Standards Ingestion      -> Load CEN/ISO, CTE, Part L, UNI/TS & TABULA parameter tables |
| Phase 2: Building Enrichment      -> Query OSM footprints & resolve gaps via 4-tier imputation     |
| Phase 3: Procedural Floor Layout  -> Regularize footprints (EdgeTo4) & subdivide dwellings (1x1-4x2)|
| Phase 4: Watertight IDF Assembly  -> Dynamic insulation sizing, internal mass & hydronic heating  |
| Phase 5: GSSCanada Sweep Runner   -> Inject 5-level phi_int schedules & run SLURM HPC cluster     |
| Phase 6: EUI & Gate Verification  -> Calculate simulated vs reconstructed EUI & audit Gates G8.0-16|
+---------------------------------------------------------------------------------------------------+
```

*Walkthrough Figure 1. Six execution phases from standards registration to evidence-backed acceptance. Reusable source: [`content/walkthrough_figure_1_execution_pipeline.mmd`](content/walkthrough_figure_1_execution_pipeline.mmd).*

**Why dwelling-level zoning matters:** The Ankara KBEM study (*Iseri et al., 2025*; 6,458 dwelling units across **593 residential buildings** of 642 in the study area) shows that building-level aggregation suppresses $75.5\%$ of the inter-dwelling energy **standard deviation** (std dev drops from $63.61$ to $15.54\text{ kWh}/\text{m}^2\text{a}$) and underestimates extreme thermal vulnerability by $3.2\times$. Top-floor units require $213.20\text{ kWh}/\text{m}^2\text{a}$ against $85.70$ for mid-floor units — **$+148.8\%$**. A corner-unit heating penalty is expected on the same physical grounds but is `UNSOURCED`: no corner-versus-middle percentage exists in the paper or in the reference folders, so none is stated here. This dispersion is invisible to coarse building-level models and is the primary scientific justification for the procedural dwelling-subdivision approach in Phase 3.

> [!NOTE]
> **Citation rule.** The $63.61 / 15.54 / 75.5\% / 3.2\times / 213.20 / 85.70 / +148.8\%$ figures are
> **not printed in the published paper**. They are computed in the 2026-08-22 re-analysis of the
> paper's simulation data: `IMP_step8/outputs/simulation_results_analysis_report.md`, lines 24–32,
> derived from `IMP_step8/resources/AllV{1,2,3,4}_updated2023June.csv`. Cite that report, not
> *Iseri et al. (2025)* alone. Only the sample description (6,458 units, 593 buildings of 642) comes
> from the paper itself. Note also that $75.5\%$ is a standard-deviation ratio; the same data
> expressed as variance give $\approx 94\%$.

---

## 2. Phase 1: Ingesting & Registering European Standards & Physics

### 2.1 Registering European Envelope & Construction Data

European building envelopes are parameterized against the **TABULA / EPISCOPE** building typology database. Parameter tables are registered in `openubem/data/construction/`:
- `tabula_archetypes_es.json` (Spain: 24 archetypes across 6 epochs)
- `tabula_archetypes_uk.json` (United Kingdom: 36 archetypes across 8 epochs)
- `tabula_archetypes_it.json` (Italy: 42 archetypes across 8 epochs)
- `tabula_archetypes_fr.json` (France physical-model registry: count remains `NOT_AUDITED`; not part of the 102-record occupant registry)

The first three files support the frozen ES/GB/IT occupant campaign. The French file is a current physical-pipeline deliverable: it must be generated from pinned French TABULA/EPISCOPE sources, audited independently, and used for controlled baseline simulations before any France occupant work begins.

> **v1.3 note.** (1) The canonical GB file name is `tabula_archetypes_gb.json` (§9.3 governs; `_uk.json` above is the v1.0 wording). (2) The epoch counts "6 / 8 / 8" are correct, but the epochs are not re-typed from memory: they are the 22 verbatim TABULA bands in [MVP Table 15](MVP_european_locations.md#114-the-22-construction-year-bands-verbatim). (3) The example entry below is illustrative and its `"epoch_code": "ES.04"` with `"year_range": [1980, 2006]` and "NBE-CT-79 Era" does **not** match the file: `ES.04` is 1960–1979 and `ES.05` is 1980–2006, whose workbook label is `CTE-79` (`NBE-CT-79` appears nowhere in the workbook). (4) The example's `"infiltration_ach": 0.40`, `"capacitance_wh_m2k": 50.0` and `"boiler_efficiency": 0.88` are not TABULA values for this row; the campaign values are `n_air_use = 0.4`, `c_m = 45` from the `EU.MUH` boundary-condition row (MVP §11.2), and the boiler efficiency is an `EU-05` assumption to be declared. (5) The upstream source for all three ES/GB/IT files is the parent's existing `outputs_step8/archetype_parameters_{es,uk,it}.csv` — see §9.3 reconciliation block and MVP Table 14 for the column crosswalk.

**TABULA Source Artefact Checksums** (for reproducibility):
- `tabula-values.xlsx` (4.0 MB): MD5 `7347b2cae3c4d9f5ce78221e9d5fb832`
- `tabula-calculator.xlsx` (34.4 MB): MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`

> [!IMPORTANT]
> TABULA labels the English building stock as `GB`, but survey coverage is limited to **England only** — Scotland, Wales, and Northern Ireland have separate EPCs and building regulations. Use `gb` for the TABULA stock code and retain a separate `uk` survey-fold field in all archetype records.

#### Example Construction Table Entry (`openubem/data/construction/tabula_archetypes_es.json`):
```json
{
  "ES.04.MFH": {
    "country": "ES",
    "epoch_code": "ES.04",
    "year_range": [1980, 2006],
    "building_type": "MFH",
    "description": "Spanish Multi-Family House (NBE-CT-79 Era)",
    "climate_zone": "ES-D3-Madrid",
    "envelope": {
      "u_wall_w_m2k": 1.20,
      "u_roof_w_m2k": 0.90,
      "u_floor_w_m2k": 1.40,
      "u_window_w_m2k": 3.40,
      "g_gl_window": 0.75,
      "infiltration_ach": 0.40
    },
    "thermal_mass": {
      "capacitance_wh_m2k": 50.0,
      "internal_mass_ratio": 1.5
    },
    "hvac": {
      "system_type": "HydronicBaseboard",
      "boiler_efficiency": 0.88,
      "fuel": "NaturalGas",
      "heating_setpoint_c": 20.0,
      "cooling_setpoint_c": 26.0
    }
  }
}
```

### 2.2 Sizing Opaque Insulation Dynamically (`openubem.idf.opaque_assembly`)

OpenUBEM sizes the insulation thickness ($d_{\text{ins}}$) parametrically so that the composite opaque assembly matches the exact statutory TABULA $U$-value. Representative wall $U$-value ranges by epoch (from TABULA / DR06):
- **Spain:** Pre-1979 $U_{\text{wall}} \approx 1.4\text{--}1.8$; CTE 2006 $\approx 0.66\text{--}0.95$; CTE 2013 $\approx 0.38\text{--}0.52\text{ W}/(\text{m}^2\text{K})$
- **UK:** Pre-1918 solid brick $\approx 2.1$; Post-1990 $\approx 0.45$; Part L 2021 $\approx 0.18\text{ W}/(\text{m}^2\text{K})$
- **Italy:** Pre-1975 $\approx 1.2\text{--}1.9$; Legge 10/1991 $\approx 0.50$; DM 2015 $\approx 0.26\text{--}0.34\text{ W}/(\text{m}^2\text{K})$

```python
# Sizing calculation in openubem/idf/opaque_assembly.py
def calculate_insulation_thickness(
    u_target: float,
    lambda_ins: float = 0.038,     # EPS conductivity [W/(m·K)]
    r_base_layers: float = 0.45,   # Outer brick (0.20m/0.79) + inner plaster (0.015m/0.25)
    r_si: float = 0.13,            # Internal surface resistance (EN ISO 6946)
    r_se: float = 0.04,            # External surface resistance (EN ISO 6946)
) -> float:
    """Calculates continuous insulation thickness to hit exact European U-value."""
    r_target = 1.0 / float(u_target)
    r_needed = r_target - (r_si + r_se + r_base_layers)
    if r_needed <= 0.0:
        return 0.001  # Uninsulated historic masonry baseline (minimum 1 mm layer)
    return round(r_needed * lambda_ins, 4)
```

### 2.3 Explicit Internal Thermal Mass Injection (`openubem.idf.builder`)

To prevent artificial indoor temperature spikes and correctly represent solid masonry and concrete partitions, OpenUBEM injects `InternalMass` objects into each living zone:

```python
# Injection in openubem/idf/builder.py
def inject_european_internal_mass(idf, zone_name: str, floor_area_m2: float, country: str):
    """Injects calibrated internal thermal mass per EN ISO 52016-1 Table B.14."""
    capacitance_map = {
        "ES": 50.0,   # Spain Heavy (Wh/m²·K)
        "IT": 87.0,   # Italy Very Heavy (Wh/m²·K)
        "GB": 32.8,   # UK Medium-Light (Wh/m²·K)
        "EU": 45.0,   # Harmonized European Standard (Wh/m²·K)
    }
    c_m = capacitance_map.get(country.upper(), 45.0)
    mass_surface_area = round(1.5 * floor_area_m2, 2)
    
    construction_name = f"InternalMass_{country}_Construction"
    if not idf.getobject("CONSTRUCTION", construction_name):
        material_name = f"InternalMass_{country}_Material"
        # 10 cm solid masonry partition equivalent
        idf.newidfobject(
            "MATERIAL",
            Name=material_name,
            Roughness="MediumRough",
            Thickness=0.10,
            Conductivity=0.80,
            Density=2000.0,
            Specific_Heat=c_m * 3600.0 / (0.10 * 2000.0),  # Calibrate c_p to match c_m
            Thermal_Absorptance=0.9,
            Solar_Absorptance=0.7,
            Visible_Absorptance=0.7,
        )
        idf.newidfobject("CONSTRUCTION", Name=construction_name, Outside_Layer=material_name)

    idf.newidfobject(
        "INTERNALMASS",
        Name=f"{zone_name}_InternalMass",
        Construction_Name=construction_name,
        Zone_or_ZoneList_Name=zone_name,
        Surface_Area=mass_surface_area,
    )
```

> [!NOTE]
> EN ISO 52016-1 Table B.14 defines five standard thermal mass classes: Very Light ($80\text{ kJ}/\text{m}^2\text{K}$ / $14\text{ Wh}$), Light ($110 / 28$), Medium ($165 / 45$), Heavy ($260 / 78\text{--}87$), Very Heavy ($370 / 105\text{ Wh}/\text{m}^2\text{K}$). The country-specific values in the `capacitance_map` above are project mapping decisions from these five classes, not exact Table B.14 entries. Their provenance must be documented alongside the archetype parameters.

---

## 3. Phase 2: Ingesting & Modeling European Building Stocks

### 3.1 Fetching & Harmonizing OpenStreetMap Footprints

OpenUBEM's acquisition module fetches raw footprints and cleans them into valid UTM planar polygons:

```python
from openubem.acquisition.osm_fetcher import fetch_osm_buildings

# Fetch buildings for a district in Madrid, Spain
gdf = fetch_osm_buildings(
    place_query="Chamberí, Madrid, Spain",
    timeout_s=60,
)
print(f"Acquired {len(gdf)} building footprints in Chamberí.")
```

### 3.2 Resolving Missing Data via the 4-Tier Imputation Cascade

Real-world OpenStreetMap footprints frequently lack `building:levels`, `start_date`, or `height`. Stage 2 resolves these gaps using the zero-fitted priority cascade:

```python
from openubem.semantic.imputation import impute_missing

# Impute levels, year_built, and height_m across the European fleet
enriched_gdf = impute_missing(
    gdf,
    target_columns=["levels", "year_built", "height_m"],
    country_code="ES",
    random_seed=42,
)

# Verify provenance tokens
print(enriched_gdf[["building_id", "levels", "levels_provenance", "year_built_provenance"]].head())
```

---

## 4. Phase 3: Procedural Floor Layout Generation & Dwelling Slicing

### 4.1 Algorithmic Subdivision Functions (from `kbem_ankara_pipeline.py`)

OpenUBEM incorporates the procedural slicing logic developed in *Iseri et al. (2025)*:

```python
from typing import Tuple

def get_grid_division_counts(units_per_floor: int) -> Tuple[int, int]:
    """Determines the (U, V) grid subdivision counts based on target flats per floor."""
    if units_per_floor <= 1:
        return (1, 1)
    elif units_per_floor == 2:
        return (2, 1)
    elif units_per_floor in (3, 4):
        return (2, 2)
    elif units_per_floor in (5, 6):
        return (3, 2)
    else:
        return (4, 2)

def map_construction_vintage(year_built: int) -> str:
    """Classifies building construction year into representative European vintage epochs."""
    if year_built < 1980:
        return "ES.03"  # Pre-NBE-CT-79
    elif 1980 <= year_built < 2007:
        return "ES.04"  # NBE-CT-79 Standard
    elif 2007 <= year_built < 2014:
        return "ES.05"  # CTE-2006 Standard
    else:
        return "ES.06"  # CTE-2013/2019 Standard
```

> **v1.3 note.** `get_grid_division_counts` is verbatim from `IMP_step8/outputs/kbem_ankara_pipeline.py` (derived from Grasshopper components idx 1938 and 4188). `map_construction_vintage` is **not**: the real function in that file returns the Turkish bins `1960 / 1980 / 2000` (boundaries `<1980`, `1980–1999`, `≥2000`; post-TS 825), and the `ES.xx` version above is an illustrative adaptation whose boundaries contradict the verified TABULA bands (`ES.03` = 1937–1959, `ES.04` = 1960–1979, `ES.05` = 1980–2006, `ES.06` ≥ 2007). `EU-02` implements [MVP Table 15](MVP_european_locations.md#114-the-22-construction-year-bands-verbatim) for all 22 bands and tests every boundary year (e.g. 1900/1901, 1959/1960, 1979/1980, 2006/2007 for Spain); do not copy the snippet above into production code.

### 4.2 Applying Procedural Layout Slicing (`openubem.geometry.layoutGenerator`)

For multi-family typologies (`MFH`, `AB`), `openubem.geometry.layoutGenerator` slices the floor plate into discrete dwelling units and carves out the central circulation core.

```python
from openubem.geometry.layoutGenerator import generate_layout
from shapely.geometry import Polygon

# Define a 20m x 15m residential floor plate (300 m² per floor, 4 storeys)
footprint = Polygon([(0, 0), (20, 0), (20, 15), (0, 15)])

zones = generate_layout(
    osm_id="ES_MAD_10482",
    footprint_poly=footprint,
    archetype_id="MidriseApartment",  # Maps to 2x2 quadrant layout + stair core
    num_floors=4,
    floor_to_floor_m=3.0,
)

print(f"Generated {len(zones)} 3D zone dictionaries across 4 storeys.")
for z in zones[:5]:
    print(f" - Zone: {z['name']} | Type: {z['space_type']} | Area: {z['floor_area_m2']:.1f} m² | Z: [{z['z_floor']}, {z['z_ceiling']}]")
```

### 4.3 Habitability Sanity Verification (Windowless Unit Test)

Every generated dwelling zone is automatically verified against the exterior facade contact threshold ($L_{\text{ext}} \ge 2.50\text{ m}$):

```python
def verify_habitability(dwelling_poly: Polygon, building_footprint: Polygon) -> bool:
    """Ensures dwelling unit has sufficient exterior facade length for daylight/ventilation."""
    facade_intersection = dwelling_poly.boundary.intersection(building_footprint.boundary)
    ext_length = facade_intersection.length
    if ext_length < 2.50:
        raise ValueError(f"Windowless unit detected! Exterior facade length = {ext_length:.2f} m < 2.50 m")
    return True
```

> [!NOTE]
> The $2.50\text{ m}$ threshold originates from IRC Section R303 and Turkish Zoning Law. It is treated as a declared project assumption; its jurisdictional basis must be confirmed for each European stock before the full campaign.

#### Corridor Width Sizing
For I-shape linear gallery layouts ($L/W \ge 2.0$), the central double-loaded circulation corridor spine width is proportional to building depth, typically $w = 1.20\text{--}1.80\text{ m}$.

#### Geometry Fallback Hierarchy
When the target grid fails (degenerate or narrow footprint), the layout generator applies a deterministic cascade:
1. Attempt the assigned grid ($2\times 2$, $3\times 2$, etc.)
2. Fall back to next smaller grid ($2\times 2 \to 2\times 1$)
3. Fall back to $1\times 1$ (full floor plate as single zone)

Every fallback records an explicit reason token. The fallback *causes* — narrow footprints ($<8\text{ m}$ width) and highly irregular shapes — are the operative engineering rule. The previously quoted Ankara fallback rate of "8.3% of buildings (25/277)" is `UNSOURCED`: it appears in neither the published paper nor any document under `IMP_step8/outputs/`, `DeepResearch/`, `resources/`, or `extracted_scripts/` (verified 2026-08-23; see MVP §4.7). Do not quote it as evidence. The European fallback rate must be measured by `GEO-04` and `GEO-10`, not inherited.

#### Ground-Contact Modeling
The Ankara pipeline tested `GroundDomain:Slab` but abandoned it for `Ground:FcfactorMethod` due to stability issues. The European campaign ground-contact method must be selected, documented, and applied consistently across all archetypes.

### 4.4 Verifying the Layout Method with OpenUBEM and Grasshopper

Run the following tasks before accepting the procedural layout method:

1. Export a pinned golden set containing a rectangle, rotated rectangle, L-shape, narrow footprint, courtyard footprint, MFH stack, and AB stack in a projected CRS.
2. Process the exact same footprints and requested dwelling counts through Grasshopper and `generate_layout`.
3. Normalize both outputs to GeoJSON or WKT; ignore object order but preserve stable building/floor/zone IDs.
4. Compare dwelling count, circulation count, polygon validity, union area, overlap/gap area, exterior-facade contact, and adjacency.
5. Extrude the clean outputs, create the IDF, reopen it from disk, and verify reciprocal interzone surfaces and zone assignments.
6. Mutate one clean fixture at a time to create an overlap, gap, windowless dwelling, unpaired wall, or invalid fallback; record that the named gate fails.
7. Retain the Grasshopper definition/version, input/output files, OpenUBEM command, normalized comparison table, and preview images.

Use the full `GEO-01`–`GEO-10` acceptance matrix in [MVP Section 4.8](MVP_european_locations.md#48-verification-protocol-and-grasshopper-parity-tasks) and its machine-readable copy at [`content/table_4_8_geometry_verification_matrix.csv`](content/table_4_8_geometry_verification_matrix.csv). Do not mark parity `PASS` from a visual overlay alone.

---

## 5. Phase 4: Watertight EnergyPlus IDF Assembly

### 5.1 Assembling Multi-Zone Geometry & Boundary Conditions

OpenUBEM's IDF builder reads the procedural zone definitions and builds watertight 3D geometry with automated boundary condition matching:

```python
from openubem.idf.builder import IDFModelBuilder

builder = IDFModelBuilder(
    osm_id="ES_MAD_10482",
    archetype_code="ES.04.MFH",
    zones=zones,
    country="ES",
)

# Add envelope constructions, window fenestration (WWR = 25%), and PTAC/radiator plant
idf = builder.build()
idf.saveas("output_models/ES_MAD_10482.idf")
print("Watertight multi-zone EnergyPlus IDF successfully assembled.")
```

### 5.2 Hydronic Radiator & Unconditioned Stairwell Zone Setup

The IDF builder configures:
1. **Dwelling Units**: Conditioned living zones with hydronic radiator heating (`ZoneHVAC:IdealLoadsAirSystem` linked to hot-water boiler curves, $20.0^\circ\text{C}$ heating setpoint, $26.0^\circ\text{C}$ cooling setpoint where applicable).
2. **Staircase / Corridor Core**: **Unconditioned floating thermal zone** (`Heating Setpoint = None`, `Cooling Setpoint = None`). No `People`, dwelling equipment, or active thermostat objects are assigned to the circulation core unless explicitly justified.
3. **Inter-Zone Party Walls**: Boundary condition `Surface` pointing to adjacent unit / stair zone names with matched reciprocal vertices.

> [!IMPORTANT]
> **HVAC Plant Modeling Decision (DR07):** Resolving full explicit EnergyPlus hydronic plant loops (boilers, pumps, valves, distribution piping) across 510 multi-zone models introduces severe numerical convergence failures. The campaign standardizes on `ZoneHVAC:IdealLoadsAirSystem` post-processed with natural gas condensing boiler seasonal efficiency curves ($\eta_{\text{seasonal}} = 0.90$, range $0.88\text{--}0.94$), which preserves identical envelope heat balance while achieving 100% convergence.

### 5.3 Glazing Parameterization Note

European total solar energy transmittance ($g_{\text{gl}}$ per EN 410 / ISO 9050) is mapped to EnergyPlus `WindowMaterial:SimpleGlazingSystem` as $\text{SHGC} = g_{\text{gl}}$. The conversion is valid within $\pm 0.02$ for standard residential glazing. Typical ranges: standard double clear $g_{\text{gl}} = 0.67\text{--}0.75$; low-emissivity $g_{\text{gl}} = 0.50\text{--}0.60$.

### 5.4 Natural Ventilation & Infiltration Assumptions

The European campaign maintains a **closed-window assumption** with continuous background infiltration per TABULA methodology. Natural ventilation window opening is not modeled. This is consistent with the Ankara validation study (*Iseri et al., 2025*) and ensures that the only experimental variable is the occupancy-driven internal gain schedule. Ventilation rates are assigned per country: ES $0.40\text{ ACH}$, GB $0.59\text{ ACH}$, IT $0.30\text{ ACH}$ (see EN 16798-1 Table B.4 equivalence in MVP Section 2.2.1).

> **v1.3 note — superseded value.** The three per-country rates are TABULA's *national* boundary-condition rows (`ES.SUH`, `GB.Gen`, `IT.SUH`). All 102 campaign archetypes point at the **EU** rows (`EU.SUH`/`EU.MUH`), whose `n_air_use` is $0.4\text{ h}^{-1}$ in every fold, and the parent ruling keeps the EU set precisely because the national set's factor-two air-change spread is country-correlated and confounded with the held-out-fold signal ([MVP §11.2](MVP_european_locations.md#112-the-eu-boundary-condition-set-is-the-campaign-set)). `EU-05` assigns $0.4\text{ h}^{-1}$ to every dwelling zone; the national values may be run only as a separately declared sensitivity.

---

## 6. Phase 5: GSSCanada Stochastic Occupancy Ingestion & Parallel Execution

### 6.1 Generating 5-Level Sensitivity Schedules $\phi_{\text{int}}(t)$

The GSSCanada LLM occupancy pipeline generates 8,760-hour presence curves $g(t)$ from held-out HETUS diaries. OpenUBEM ingests these into the 5-level sensitivity formula:

```python
import numpy as np
import pandas as pd

def generate_sensitivity_schedules(
    g_presence_8760: np.ndarray,
    output_csv_dir: str,
    building_id: str,
):
    """Generates 5 external CSV schedules for the sensitivity sweep f in {0.00, 0.15, 0.30, 0.50, 1.00}."""
    mean_g = np.mean(g_presence_8760)
    g_normalized = g_presence_8760 / mean_g
    
    sweep_factors = [0.00, 0.15, 0.30, 0.50, 1.00]
    generated_files = {}
    
    for f in sweep_factors:
        # phi_int(t) = (1 - f)*3.0 + f*3.0*g_norm(t)
        phi_int_t = (1.0 - f) * 3.0 + f * 3.0 * g_normalized
        
        # Verify strict annual energy conservation: 3.0 W/m² * 8760 h = 26.28 kWh/m²
        assert np.isclose(np.mean(phi_int_t), 3.0, rtol=1e-5), "Energy conservation violated!"
        
        csv_filename = f"{output_csv_dir}/{building_id}_f{int(f*100):03d}.csv"
        df = pd.DataFrame({"phi_int_w_m2": phi_int_t})
        df.to_csv(csv_filename, index=False, header=False)
        generated_files[f] = csv_filename
        
    return generated_files
```

### 6.2 Attaching `Schedule:File` in the IDF (Gate G8.13 Conformance)

The generated CSV schedule is wired into the EnergyPlus model via `Schedule:File` with `Interpolate to Timestep = No`:

```python
def wire_schedule_file(idf, schedule_csv_path: str, schedule_name: str = "OccupancyInternalGainSched"):
    """Injects Schedule:File object satisfying Pre-Registered Gate G8.13."""
    idf.newidfobject(
        "SCHEDULE:FILE",
        Name=schedule_name,
        Schedule_Type_Limits_Name="Fractional",
        File_Name=schedule_csv_path,
        Column_Number=1,
        Rows_to_Skip_at_Top=0,
        Number_of_Hours_of_Data=8760,
        Column_Separator="Comma",
        Interpolate_to_Timestep="No",  # Strictly enforced per Gate G8.13
    )
```

### 6.3 Parallel SLURM HPC Execution

Simulations are executed across cluster compute nodes via OpenUBEM's parallel runner (`openubem.simulation.parallel`):

```bash
# Submit 510-cell campaign array on Concordia Speed SLURM cluster
sbatch --array=1-510 -c 1 --mem=4G --wrap="bash -lc 'python -m openubem.simulation.runner --cell-id \$SLURM_ARRAY_TASK_ID --config european_campaign.json'"
```

---

## 7. Phase 6: Post-Processing, EUI Reconstruction & Gate Audit

### 7.1 Simulated vs. Reconstructed EUI Calculation

Once EnergyPlus completes, OpenUBEM extracts the 4 simulated physics end-uses and reconstructs the whole-building EUI using national TABULA Table 4 end-use splits:

```python
# TARGET API — not runnable in OpenUBEM 0.1.0.
# `reconstruct_eui` does not exist in the repository (verified 2026-08-23; MVP §9.2).
# The current function is `openubem.results.service_loads.reconstruct_frame`, and
# reconstruction is disabled by default because Phase E physically models five service loads.
from openubem.results.service_loads import reconstruct_eui

# Simulated results from EnergyPlus SQL / CSV output
simulated_metrics = {
    "heating_eui_kwh_m2": 68.40,
    "cooling_eui_kwh_m2": 14.20,
    "lighting_eui_kwh_m2": 12.50,
    "equipment_eui_kwh_m2": 18.00,
}

# Simulated 4-end-use sum = 113.10 kWh/m²·yr
simulated_total = sum(simulated_metrics.values())

# Reconstruct whole EUI adding DHW, cooking, parasitics
reconstructed_eui, breakdown = reconstruct_eui(
    simulated_eui=simulated_total,
    archetype="MFH",
    country="ES",
)

print(f"Simulated EUI (4 End-Uses):    {simulated_total:.2f} kWh/m²·yr")
print(f"Reconstructed Whole-Bldg EUI:  {reconstructed_eui:.2f} kWh/m²·yr")
print(f" - DHW Share:                  {breakdown['dhw_eui']:.2f} kWh/m²·yr")
print(f" - Cooking Share:              {breakdown['cooking_eui']:.2f} kWh/m²·yr")
print(f" - Parasitics Share:           {breakdown['parasitics_eui']:.2f} kWh/m²·yr")
```

### 7.2 Pre-Registered Gate Audit Checklist

Every completed simulation cell must satisfy the full validation gate suite before acceptance into the campaign dossier:

| Gate | Task | Required evidence | Status before execution |
|---|---|---|---|
| G8.0 | Audit `f=0` controls before release of `f>0` | Generated control report | `NOT_RUN` |
| G8.8 | Compare scenario result hashes and values | Scenario comparison report | `NOT_RUN` |
| G8.9 | Mutate one dependency and confirm rerun | Cache mutation report | `NOT_RUN` |
| G8.10 | Reconcile selected total and components | Meter-balance report | `NOT_RUN` |
| G8.11 | Validate required meter names | Parsed `.mdd` and SQL evidence | `NOT_RUN` |
| G8.12 | Reopen IDF and verify schedule path/checksum | Saved-artifact audit | `NOT_RUN` |
| G8.13 | Verify interpolation setting | Saved-IDF audit | `NOT_RUN` |
| G8.14 | Validate manifest against measured files | Manifest schema report | `NOT_RUN` |
| G8.15 | Classify all warnings/errors | Warning taxonomy report | `NOT_RUN` |
| G8.16 | Join schedule provenance to held-out fold | Fold audit report | `NOT_RUN` |

*Walkthrough Table 1. Gate-execution checklist. Status changes only from generated evidence. Machine-readable copy: [`content/walkthrough_table_7_2_gate_checklist.csv`](content/walkthrough_table_7_2_gate_checklist.csv).*

### 7.3 Negative Control Diagnostic Thresholds

Before accepting any European simulation results, verify diagnostic plausibility:
- **Reject** if $f=0.00$ uninjected controls produce heating EUI deviating by $>50\%$ from published TABULA national brochure benchmarks ($Q_H \approx 80\text{--}180\text{ kWh}/\text{m}^2\text{a}$).
- **Reject** if adapted OpenUBEM median EUI at $f=0.00$ differs from TABULA national baseline by $>25\%$.
- **Reject** if pre-1945 uninsulated Spanish/Italian archetypes at $f=0.00$ yield space heating $< 50\text{ kWh}/\text{m}^2\text{a}$.

These are diagnostic flags applied during Q1–Q2 qualification (Section 10), not calibration targets. The pipeline must never alter a TABULA parameter to make a pilot EUI appear more plausible.

### 7.4 Overheating Assessment (CIBSE TM59 / EN 16798-1)

Where cooling performance is relevant (particularly for UK stock), overheating is assessed using the adaptive comfort model (EN 16798-1 Section 6.2, Annex A) and cumulative Indoor Overheating Degree ($IOD$). UK-specific compliance requires CIBSE TM59 (2017):
- *Criterion A*: Living/bedrooms $\le 3\%$ of occupied hours exceeding $\Delta T \ge 1\text{ K}$ operative temperature above comfort limit.
- *Criterion B*: Bedrooms $\le 32\text{ hours}$ exceeding $26^\circ\text{C}$ between 22:00–07:00.

The 2026-08-22 re-analysis of the Ankara simulation data reports a maximum $IOD$ of $0.817^\circ\text{C}\cdot\text{h}/\text{a}$ in the zone-level iteration `V4` versus $0.565$ in the coarsest iteration `V1` — $+44.6\%$ peak overheating exposure (`IMP_step8/outputs/simulation_results_analysis_report.md:60`). These are V1-versus-V4 modelling iterations, not a direct building-level/dwelling-level pair, and the values are not printed in the published paper; cite the re-analysis report.

### 7.5 Intermittent Heating Factor Preservation

TABULA intermittent heating reduction factors ($F_{\text{red,htr}} \in \{0.80, 0.85, 0.90, 0.95\}$) are applied as scalar transmission multipliers on $UA$, not as thermostat night-setback schedules. This prevents confounding between heating control patterns and the LLM-generated stochastic occupancy signal (Pre-Registered Ruling `D-S8-2`).

---

## 8. Diagnostic Error Triage (`OpenUBEM_debug_References.md`)

If an EnergyPlus simulation fails or emits warnings, match the error pattern against [`OpenUBEM_debug_References.md`](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_debug_References.md):

| Observed pattern | Probable cause | Required action |
|---|---|---|
| CTF calculation failed | Unstable resistance-capacitance layer combination | Apply registered CTF-safe construction path and rerun the targeted fixture |
| Intersecting or degenerate surface | Invalid procedural polygon | Repair or reject geometry and retain original failure evidence |
| Unmatched interzone surface | Missing reciprocal party-wall face | Rebuild pairing and verify both saved-IDF faces |
| Temperature out of bounds | Potential mass, load, geometry, or control defect | Classify the cause; never accept from a raw warning count alone |

*Walkthrough Table 2. Initial EnergyPlus error-triage routes. Machine-readable copy: [`content/walkthrough_table_8_1_error_triage.csv`](content/walkthrough_table_8_1_error_triage.csv).*

---

## 9. v1.1 Operational Migration Walkthrough (Code-Audited)

This section is the runnable migration guide for OpenUBEM `0.1.0`. It deliberately separates commands that work today from interfaces that must be implemented for Step 8.

### 9.1 Phase 0 — Establish a Reproducible Baseline

Run all commands from the OpenUBEM repository root. Record the resulting commit and versions before changing the European adapters:

```powershell
git rev-parse HEAD
python --version
python -c "import openubem; print(openubem.__version__)"
python -c "from importlib.metadata import version; print(version('openubem'))"
pytest -q
```

OpenUBEM `0.1.0` does not currently export `openubem.__version__`; the `importlib.metadata` command is the authoritative package-version check. The preceding direct check is retained as a useful packaging diagnostic and is expected to fail until `__version__` is exported.

Also record the EnergyPlus binary path, version, and build identifier. OpenUBEM currently defaults to EnergyPlus **23.1**, whereas some Step 8 research artefacts refer to **9.2**. Choose and pin one campaign version; do not combine `.mdd`, IDF, or result assumptions across versions.

Create an implementation evidence directory under the future campaign output, with one immutable subdirectory per run. Never write verification artefacts into the source-data directory.

### 9.2 Read the Authorities Before Generating Data

Review these documents in order:

1. `Step8_docs/4thJ_08_bemSimulation.md` — active scientific rulings and unresolved decisions;
2. `Step8_docs/4thJ_08_bemSimulation_val.md` — full G8 and V8 validation contract;
3. this walkthrough and the sister MVP addendum;
4. `IMP_step8/outputs/floor_layout_generation_report.md` and `kbem_ankara_pipeline.py` — geometry references;
5. `IMP_step8/DeepResearch/DR05`–`DR07` — standards/adaptation context.

Do not start the full campaign while geometry, material layers, archetype selection, weather acquisition, or EUI accounting remains an undocumented assumption.

### 9.3 Build the TABULA Registry as Data, Not Hand-Written Examples

The three JSON files shown in Section 2 do not yet exist. Implement a deterministic conversion command that reads pinned TABULA workbooks and produces:

```text
openubem/data/construction/tabula_archetypes_es.json
openubem/data/construction/tabula_archetypes_gb.json
openubem/data/construction/tabula_archetypes_it.json
openubem/data/construction/tabula_archetypes_fr.json
openubem/data/construction/TABULA_PROVENANCE.md
```

Use `gb` for the TABULA stock code and retain a separate `uk` survey-fold field. The generator must emit an exclusions table for refurbishment variants, unclassified records, and any dropped row.

Generate and audit the French physical registry in the same command family, but keep its count and manifest separate. France participates in building/neighbourhood preparation and controlled baseline simulations now; do not create `survey_fold=fr`, France diary assignments, or France `f>0` cells until the future occupant branch is explicitly activated.

Before proceeding, assert:

```text
ES count = 24
GB count = 36
IT count = 42
total    = 102
construction-period bands = 22
phi_int_w_m2 = 3.0 for every campaign archetype
FR physical count = independently audited; excluded from total=102
```

The sample JSON in Section 2.1 is illustrative. Values must come from the pinned workbooks/source cells; do not copy the example into production data.

#### 9.3.1 Reconcile against the parent tables first (v1.3)

The primary input is not the workbook; it is the parent's existing, provenance-audited table set ([MVP §11.3](MVP_european_locations.md#113-the-parameter-tables-already-exist-eu-01-consumes-them)):

```text
C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\outputs_step8\
├── archetype_parameters_es.csv      # 24 data rows + 3 trailing '#' comment lines, 44 columns
├── archetype_parameters_uk.csv      # 36 data rows + 3 trailing '#' comment lines
├── archetype_parameters_it.csv      # 42 data rows + 3 trailing '#' comment lines
├── archetype_parameter_provenance.md
└── raw/tabula-values.xlsx, raw/tabula-calculator.xlsx   # pinned workbooks
```

Read them with `comment="#"` (or skip lines starting with `#`); otherwise the row counts read 27 / 39 / 45. Then assert, before writing any JSON:

```text
rows(es, uk, it)                         == (24, 36, 42)
set(Code_BoundaryCond)                   == {"EU.SUH", "EU.MUH"}        # refuse any other pointer
Number_BuildingVariant                   == 1 on every row                # existing state only
Code_BuildingVariant.str.endswith(".001")       on every row                # parent existing-state filter; `SyAv.002.001`/`.005.001` are valid
set(Code_ConstructionYearClass)          == the 6 / 8 / 8 codes of MVP Table 15
phi_int                                  == 3 on every row
Code_ClimateRegion                       == {"ES.ME"}, {"GB.Temperate"}, {"IT.MidClim"} per file
all GB Code_Building values start with "GB.ENG."                          # England-only limitation
"ES.TestRegion" appears in no row                                         # the 4 unclassified rows are absent
```

Record the parent MD5s as found (`tabula-values.xlsx` `7347b2cae3c4d9f5ce78221e9d5fb832`; `tabula-calculator.xlsx` `c99ddc9ffcb6dc0ae7391273d9619e37`) and compute SHA-256 of the pinned copies in `raw/` for the OpenUBEM record. Join `n_air_use`, `c_m`, `theta_i`, `F_red_htr1/4` from `Tab.BoundaryCond` on `Code_BoundaryCond` (values in [MVP Table 13](MVP_european_locations.md#112-the-eu-boundary-condition-set-is-the-campaign-set)); the table does not carry them as columns. `g_gl` is also absent and comes from `Tab.U.Class.Window` or is declared an assumption. The *independent* check of the 24/36/42 counts is re-running the parent builder (`python tools/4thJ_step8_tabula.py Step8_docs/outputs_step8`, from the GSSCanada root — read-only with respect to OpenUBEM) and diffing the CSVs; it is not the primary path. Do not collapse the GB parallel parameterisations or the IT composite codes: which row represents a cell is parent open decision §6.4 and must surface as an explicit error in `EU-02` ([MVP §11.5](MVP_european_locations.md#115-the-three-folds-do-not-share-one-archetype-structure--an-open-parent-decision)).

### 9.4 Use the Existing Acquisition and Imputation APIs Correctly

The current acquisition entry point is `ingest_buildings`, not `fetch_osm_buildings`:

```python
from pathlib import Path
import numpy as np

from openubem.acquisition.osm_fetcher import ingest_buildings
from openubem.semantic.imputation import ImputeConfig, impute_missing

raw_gdf = ingest_buildings(
    location="Chamberí, Madrid, Spain",
    radius_m=1000.0,
    output_dir=Path("runtime/eu_pilot/01_acquisition"),
)

audit_cfg = ImputeConfig(
    enabled_tiers=("fusion", "spatial", "ml", "statistical"),
    strict=False,
)
imputed_gdf = impute_missing(
    raw_gdf,
    cfg=audit_cfg,
    targets=("year_built", "levels"),
    rng=np.random.default_rng(42),
)
```

Important differences from the original example:

- the arguments are `cfg`, `targets`, and `rng`, not `target_columns`, `country_code`, and `random_seed`;
- provenance columns are named `provenance_year_built`, `provenance_levels`, etc.;
- `impute_missing` is a standalone router and does not replace the complete `enrich_semantics` pipeline;
- country-aware TABULA mapping must be implemented explicitly before calling `enrich_semantics` with European construction/load/schedule tables.

Run strict mode once on each source dataset to inventory gaps before filling them. Preserve that pre-imputation report alongside the completed dataset.

### 9.5 Acquire and Validate Actual-Weather Files

The current `epw_manager.fetch_epw` resolves station-based EPW files, but the Step 8 decision requires actual meteorological weather aligned with survey fieldwork rather than an arbitrary TMY. Therefore:

1. determine the fieldwork window for each fold;
2. document the twelve-month selection rule;
3. select and license an AMY source/location;
4. convert or validate the resulting EPW without changing timestamps silently;
5. record its SHA-256 and parsed `LOCATION` header;
6. ensure every `f` level within a fold references the exact same weather checksum.

Do not use the current nearest-station TMY download as a substitute merely to unblock a production result. It may be used only for a clearly labelled geometry/IDF smoke test.

> **v1.3 — what is ruled and what is owed** ([MVP §11.6](MVP_european_locations.md#116-weather-is-ruled-not-acquired)). Ruled 2026-08-21: each fold runs on the actual meteorological year of its own fieldwork window — `es` **2009–2010**, `uk` **2014–2015**, `it` **2013–2014**. Owed before any weather-driven number may be quoted: (1) the fieldwork calendars, pinning "survey year" to twelve definite months (proposed rule: the 12 consecutive months containing the most diaries in that fold, measured from the corpus's own dates); (2) an AMY source whose licence permits *publishing derived results*; (3) a station/location, because TABULA's tags (`ES.ME`, `GB.Temperate`/`ENG`, `IT.MidClim`) are not coordinates. Madrid / London / Bologna and the ERA5 route in the Step 8 implementation document are candidates, not rulings. Step 1 of the list above therefore reads: *confirm the three windows from the Step 7 corpus dates, and write `weather_registry.json` with `status: "RULED_NOT_ACQUIRED"` until all three items are on disk.* Q1/Q2 smoke runs on a TMY carry `weather_status: "SMOKE_TMY"` in their manifest and their EUIs are never reported as baselines.

### 9.6 Add European Geometry Without Replacing the Existing Generator

The current callable is:

```python
from openubem.geometry.layoutGenerator import generate_layout

zones = generate_layout(
    osm_id="ES_MAD_10482",
    footprint_poly=footprint,
    archetype_id="MidriseApartment",
    num_floors=4,
    floor_to_floor_m=3.0,
)
```

This call is runnable only for archetypes registered in `MODULE_SPECS`; the current residential specification is DOE/IBC-derived. The Step 8 implementation should add a TABULA-aware adapter or European module specifications while keeping `generate_layout` as the stable geometric entry point.

For every pilot geometry, persist a floor-level audit table with:

```text
osm_id, floor_id, requested_dwelling_count, emitted_dwelling_count,
circulation_area_m2, dwelling_area_m2, footprint_area_m2,
area_error_fraction, minimum_facade_contact_m, overlap_area_m2,
gap_area_m2, fallback_reason
```

Reject or explicitly fall back when area error exceeds 1%, a dwelling lacks facade contact, an interzone face lacks a reciprocal partner, or the result is not one zone per dwelling. Treat the `2.50 m` facade-contact threshold as a declared project assumption until its jurisdictional basis is confirmed for each stock.

Before processing a complete neighbourhood, execute the residential-only sample ladder:

1. `S0`: four synthetic fixtures—one each for SFH, TH, MFH, and AB—with geometry and saved-IDF checks;
2. `S1`: 12 observed residential buildings covering simple and irregular footprints, using short design-day simulations;
3. `S2`: 31 observed high-completeness residential buildings (`D-EU-04-S2-C` C1A): AB/MFH/TH each 4 old + 4 new, SFH 6 old + 1 new; geometry outcomes remain independent, using short-period simulations;
4. `S3`: 96 observed residential buildings balanced across available ES/GB/IT/FR physical strata, using annual controlled baselines;
5. `N1`: only after S0–S3 pass, select one real contiguous dense residential neighbourhood containing **at least 100** residential buildings after filtering (500–600 preferred where the official geography offers it; amended 2026-08-24, ruling `D-EU-02-C`, §7.3 of `outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md`);
6. `N2`: optionally select/extend a contiguous dense residential neighbourhood to as many as 1,000 residential buildings after N1 resource and evidence review.

At the source-inventory boundary, write `excluded_buildings.parquet` with the stable ID and exclusion reason for every non-residential or unresolved-use footprint. Assert that none of those IDs appears in the layout, IDF, or simulation manifests.

### 9.7 Extend the Existing IDF Builder

The supported fleet builder is `run_step3`; `IDFModelBuilder` from Section 5 is a proposed API and is not present:

```python
from pathlib import Path
from openubem.idf.builder import run_step3

idf_manifest = run_step3(
    enriched_gdf,
    schedule_library,
    Path("runtime/eu_pilot/03_idf"),
    n_jobs=1,
    resolution_mode="auto",
)
```

For Step 8, extend `BuildingIDF`/`run_step3` through explicit European configuration rather than patching saved IDFs from the campaign driver. At minimum, the adapter must:

- map TABULA U-values and `g_gl` to the current row schema;
- preserve the opaque-assembly CTF safety behavior while adding traceable material layers;
- emit and test European residential HVAC/ventilation;
- exclude active HVAC and dwelling loads from unconditioned circulation zones;
- bind one independently selected diary to each dwelling;
- record all assumptions and fallback reasons in the IDF manifest.

The existing `build_opaque_assembly` does **not** implement the `calculate_insulation_thickness` example from Section 2.2, and the existing builder does **not** inject the `inject_european_internal_mass` function shown in Section 2.3. Implement and test those behaviors before describing them as current.

### 9.8 Implement the Step 8 Schedule Adapter

Current OpenUBEM writes DOE `Schedule:Compact` objects. Add a separate, tested target API, for example:

```python
# TARGET API — to be implemented; not runnable in OpenUBEM 0.1.0
emit_step8_gain_schedule(
    idf=idf,
    presence_path=presence_path,
    sensitivity_f=f,
    dwelling_zone=zone_name,
    emitted_csv_path=cell_schedule_path,
)
```

The implementation sequence is:

1. read `g(t)` from the Step 7 artefact on disk;
2. validate fold, length, timestamps, finiteness, non-negativity, and `mean(g)>0`;
3. compute `phi_int(t)` for each `f`;
4. assert `mean(phi_int)=3.0 W/m²` within the registered tolerance;
5. emit the campaign-local CSV atomically and hash it;
6. create `Schedule:File` with `Interpolate to Timestep = No`;
7. bind the schedule to the intended dwelling gain object;
8. save the IDF;
9. reopen the saved IDF from disk with an independent audit path and verify filename, checksum, interpolation, and object assignment.

Do not use `Schedule_Type_Limits_Name="Fractional"` for a file containing `phi_int` values in `W/m²`. Either emit a normalized dimensionless schedule with a fixed `3.0 W/m²` design level or define a compatible non-fractional schedule type. Values above `1.0` in a fractional schedule are invalid semantics even when EnergyPlus accepts the file.

Also verify that legacy DOE occupancy/equipment schedules are not simultaneously applying a second temporal modulation to the same experimental gain.

> **v1.3 — two additions to the sequence** ([MVP §11.7](MVP_european_locations.md#117-diary-derived-facts-the-schedule-adapter-must-handle)).
> - **Zero-at-home days are an explicit branch.** 1,320 diaries (1.802 %; `uk` 2.927 %, `es` 1.641 %, `it` 1.417 %) have zero at-home minutes. Step 2's `mean(g) > 0` check applies to the **annual** series after chaining; per day, `g = 0` is valid and yields $\phi_{\text{int}}(t) = (1-f)\cdot 3.0$ at every hour of that day. The adapter writes the count of zero-presence days per dwelling into the cell manifest (`zero_presence_days`) so the fold difference stays visible.
> - **The chaining rule is a blocker, not a field.** `chaining_rule` in the presence-series record must name a ruled Step 7 convention (open decision 14). Until it does, every `f>0` emission is `BLOCKED`; the `f=0` path (constant series, Q1–Q3, FR-B) does not depend on it and proceeds. If the Step 7 chaining-sensitivity experiment reports more than 25 % spread on peak demand, record that the campaign partly measures the convention — the G8 gates cannot separate the two.

### 9.9 Build the 510-Row Campaign Table

Generate the campaign table before any simulation:

```python
from itertools import product

F_LEVELS = (0.00, 0.15, 0.30, 0.50, 1.00)
cells = [
    (archetype_id, f)
    for archetype_id, f in product(archetype_ids, F_LEVELS)
]
assert len(archetype_ids) == 102
assert len(cells) == 510
```

Validate the matrix:

- exactly 102 rows at each `f`;
- exactly five rows per archetype/weather combination;
- unique deterministic `cell_id`;
- country stock and held-out fold agree with Step 7 provenance;
- all five levels share IDF physics, diary selection, and weather, differing only in the registered `f` transformation;
- `f=0` is scheduled first and blocks publication of its four matching `f>0` results until read successfully.

The `f=0` schedule is the flat `3.0 W/m²` endpoint of the same transformation. It should follow the same emission and assignment path so that the control is not constructed by different code.

### 9.10 Execute Locally, Then Wrap for SLURM

The existing local execution API is:

```python
from pathlib import Path
from openubem.simulation.parallel import run_neighbourhood

sim_manifest = run_neighbourhood(
    idf_manifest=idf_manifest,
    enriched_gdf=enriched_gdf,
    sim_root=Path("runtime/eu_pilot/04_simulation"),
    n_jobs=4,
    force_rerun=False,
)
```

This API uses joblib and returns `04_simulation_manifest.parquet`. It is not the `--cell-id` CLI shown in Section 6.3. Build a thin GSSCanada campaign command that accepts one immutable cell specification, invokes OpenUBEM, and writes one `manifest.json`; then submit that command with SLURM.

Before the 510-cell array:

1. run one `f=0` cell locally;
2. run the same cell twice and establish reproducibility;
3. run one non-zero `f` with the same physical inputs;
4. prove scenario differentiation;
5. change the schedule and prove the cache invalidates;
6. run the full gate mutation suite on a disposable pilot cell;
7. only then submit the complete array.

Use a dependency digest for resume decisions. The current `.end` + `.sql` completion check alone cannot satisfy G8.9.

### 9.11 Choose One EUI Accounting Path

The original `reconstruct_eui(...)` example is not a current API. Current OpenUBEM exposes `reconstruct_frame(...)` and defaults reconstruction off because Phase E physically models service loads.

For a four-end-use experiment, use the existing API only after providing European coefficients and explicitly disabling corresponding physical loads:

```python
from openubem.results.service_loads import load_coefficients, reconstruct_frame

coeffs = load_coefficients(european_coefficients_path)
reported = reconstruct_frame(results_df, coeffs=coeffs, force=True)
```

Otherwise, keep physical mode and do not reconstruct. In both cases, report the simulated end uses, reconstructed end uses, floor-area denominator, coefficient checksum, and `eui_accounting_mode`. A run containing both physical service loads and a reconstruction uplift is invalid.

### 9.12 Run the Complete Gate and Mutation Audit

Replace the fixed `[x] PASS` labels in Section 7.2 with generated statuses. The audit order is:

1. assert expected campaign rows and file paths (V8.a–V8.b);
2. verify `f=0` availability and ordering (G8.0);
3. validate runtime status and warning kinds (G8.15/V8.f);
4. verify meter names and energy balance (G8.10–G8.11);
5. independently reopen saved IDFs and verify schedule value, assignment, and interpolation (G8.12–G8.13);
6. verify manifest fields from measured files/platform (G8.14);
7. join against Step 7 provenance and verify held-out folds, failing on missing fold (G8.16/V8.g);
8. compute reproducibility, peak, band, differentiation, and cache gates (G8.1–G8.9);
9. run every registered mutation and record which gates fall;
10. run the null mutation and confirm that none fall.

The generated gate report must include `status ∈ {PASS, FAIL, BLOCKED, NOT_RUN}`, evidence paths, observed values, thresholds, and failure reasons. `READY`, `implemented`, or a prose checklist is not a substitute for `PASS`.

> **v1.3 note.** Steps 9 and 10 run the twelve perturbations of [MVP Table 17](MVP_european_locations.md#118-full-perturbation-matrix-and-vacuity-guards-for-eu-09) in that order, with the null perturbation last, and the coverage cross-tab (perturbation × gate → fell / stayed clean) is itself a retained artefact (`validation/mutation_coverage.parquet` in §9.15). The seven vacuity guards of MVP Table 18 are asserted before step 1, because a scorer that read too few cells (V8.a) or a second copy of the bands (V8.c) makes every later step vacuous. The mutation for G8.11 is the pre-9.4 meter name `Gas:Facility`; with the pinned EnergyPlus 23.1 the valid name is `NaturalGas:Facility`, and the accepted meter list is generated from that engine's `.mdd`, not copied from the 9.2-era Step 8 implementation document. Wherever G8.1–G8.4 appear in a report, print the parent's sentence: *"G8.1–G8.4 are reproducibility gates. They compare a cell against a re-run of itself. They are not a validation of simulated energy against measured energy, and no such validation is claimed anywhere in this paper."*

### 9.13 Minimum Test Matrix

Add dedicated tests rather than overloading the North American validation suite:

```text
tests/test_eu_tabula_loader.py
tests/test_eu_construction_sets.py
tests/test_eu_dwelling_layout.py
tests/test_eu_dwelling_layout_grasshopper_parity.py
tests/test_eu_residential_filter.py
tests/test_eu_sample_group_ladder.py
tests/test_eu_internal_mass.py
tests/test_eu_hvac.py
tests/test_step8_schedule_file.py
tests/test_step8_campaign_matrix.py
tests/test_step8_manifest.py
tests/test_step8_cache_invalidation.py
tests/test_step8_gates.py
tests/test_step8_gate_mutations.py
```

The physical smoke matrix must contain ES, GB, IT, and FR; each residential type; at least one historic and one modern band; simple and non-convex footprints; and the selected baseline weather files. The occupant-schedule matrix contains ES/GB/IT only until the France occupant branch is activated. Include negative tests for non-residential leakage into the registry, Grasshopper/OpenUBEM parity drift, zero-mean/NaN schedules, wrong folds, missing manifests, duplicate cell IDs, schedule reassignment, `Interpolate=Yes`, invalid meter names, altered weather, and double-counted EUI.

### 9.14 Operational Stop Conditions

Stop the campaign and mark it **BLOCKED** when any of the following occurs:

- TABULA counts/provenance do not reproduce 24/36/42;
- an unresolved assumption changes geometry, construction, weather, or EUI accounting;
- `f=0` fails to run or cannot be read for a matching archetype/weather;
- annual gain conservation fails;
- a country is assigned a fold that did not hold it out;
- a saved IDF cannot independently prove schedule file and object assignment;
- a cache survives an input dependency change;
- an EnergyPlus meter is missing/zero-filled or end-use balance exceeds the registered tolerance;
- any severe/fatal error occurs;
- a validation gate has not been observed failing its designated mutation;
- the scorer reads fewer cells than the campaign manifest declares.

### 9.15 Expected Handoff Artefacts

A completed Step 8 run should provide:

```text
outputs_step8/
├── inputs/
│   ├── archetype_registry.json
│   ├── archetype_parameter_provenance.md
│   ├── schedule_registry.parquet
│   └── weather_registry.json
├── campaign/
│   ├── campaign_cells.parquet
│   └── campaign_config.json
├── archetypes/
├── cells/<cell_id>/
│   ├── manifest.json
│   ├── model.idf
│   ├── gain_schedule.csv
│   ├── eplusout.sql
│   ├── eplusout.err
│   └── results.parquet
├── control/
│   └── f000_read_before_injected.parquet
├── validation/
│   ├── gate_results.parquet
│   ├── mutation_coverage.parquet
│   └── warning_kinds.parquet
├── agg_annual.csv
├── agg_monthly.parquet
└── agg_hourly.parquet
```

The final report must state that G8.1–G8.4 are reproducibility gates rather than measured-accuracy gates, identify `GB` as England-limited TABULA stock, report effects within fold across all five `f` values, name weather years in absolute cross-fold comparisons, and distinguish design assumptions from verified simulation evidence.

---

## 10. Speed HPC Execution and Pre-Occupant Pilot Runbook

### 10.1 Select an Execution Profile

Use the existing [parallel-processing reference](../../docs_DONE/SETUP/parallelProcessing/parallel_idf_prep_detailed.md) for the separation between parallel IDF preparation and parallel EnergyPlus execution. Use the [official Speed manual](https://nag-devops.github.io/speed-hpc/) for current cluster policy.

Set one campaign throttle explicitly:

```bash
# Conservative default from the established OpenUBEM runbook
export SPEED_MAX_CONCURRENT=32

# Expanded option requested for Step 8; use only after Q1/Q2 pass and approval is recorded
export SPEED_MAX_CONCURRENT=64

# Replace with the account authorized for this campaign
export SPEED_ACCOUNT="replace_with_authorized_account"
```

Recommended values are `4`, `8`, `16`, `32`, `48`, or `64`. Each running task uses one CPU, so `%64` can use more than 32 CPUs simultaneously across several nodes. It does not make one EnergyPlus simulation use 64 CPUs, and it does not guarantee that 64 tasks will start immediately.

Before selecting `48` or `64`, record:

```bash
sinfo -p ps --long --Node
squeue -u "$USER"
```

These are read-only scheduler checks. Submit all compute through `sbatch`; never execute EnergyPlus on `speed-submit`.

### 10.2 Create the Pre-Occupant Audit Figure

First select neighbourhood candidates using the same OpenUBEM location inputs used for U.S. fleets: address, coordinate, bounding box, or a pre-downloaded OSM XML extract. For each candidate, persist the boundary and calculate total footprints, residential buildings after filtering, excluded/unknown uses, residential buildings/km², and a dwelling or residential-floor-area density proxy.

Select one real contiguous, dense, residential-dominant neighbourhood per study location. Register the density rule before looking at energy results—for example, a city-specific upper density quantile plus the required post-filter building count. Do not assemble `N1`/`N2` by sampling disconnected buildings across a city, and do not trim a natural boundary merely to force exactly 500, 600, or 1,000 records.

Create these selection artefacts before IDF generation:

```text
candidate_neighbourhoods.gpkg
candidate_neighbourhood_metrics.csv
selected_neighbourhood_boundary.gpkg
neighbourhood_selection_decision.md
residential_buildings.parquet
excluded_buildings.parquet
```

Then produce a four-panel map matching the analytical intent of [`content/reference_dense_neighbourhood_4panel_audit.png`](content/reference_dense_neighbourhood_4panel_audit.png):

```text
panel_a_construction_period.png
panel_b_epc_availability.png
panel_c_building_function_typology.png
panel_d_construction_material_set.png
preinjection_input_audit_4panel.png
preinjection_input_audit_counts.csv
preinjection_input_audit.gpkg
```

The plotting input must include stable building IDs and these minimum columns:

```text
building_id, geometry, country_stock_code, construction_period,
epc_availability, building_function, residential_typology,
observed_material, assigned_construction_set,
provenance_year_built, provenance_material, data_quality_flag
```

For each panel, assert in code that:

```text
mapped feature count = source feature count
sum(category counts) = mapped feature count
missing values appear as an explicit category
no spatial join creates or drops duplicate building_id values
panel building_id set = selected-neighbourhood source building_id set
panel boundary checksum = selected boundary checksum
```

Use observed and imputed values as separate layers or visual encodings. Do not color an imputed construction material as if it were observed without exposing its provenance.

All four panels describe the **same selected neighbourhood**. Panel (c) keeps non-residential/unknown footprints visible as excluded context, while the other panels and all simulation manifests reconcile to the residential registry. Apply the full `NS-01`–`NS-10` selection gates in [MVP Section 9.7.2](MVP_european_locations.md#972-real-dense-residential-neighbourhood-selection).

Keep non-residential and unresolved-use footprints in the audit source so exclusions remain visible, but render them as grey/hatched context and write their IDs to `excluded_buildings.parquet`. The residential modelling registry must satisfy:

```python
assert set(excluded["building_id"]).isdisjoint(layout_manifest["building_id"])
assert set(excluded["building_id"]).isdisjoint(idf_manifest["building_id"])
assert set(excluded["building_id"]).isdisjoint(simulation_manifest["building_id"])
```

Use the neighbourhood concept in [`content/figure_neighbourhood_residential_typologies.png`](content/figure_neighbourhood_residential_typologies.png) only to communicate target scale and morphology. It is illustrative and cannot replace the measured four-panel input audit.

### 10.3 Build the Qualification Cases

Create five immutable lists:

```text
q1_smoke_cells.tsv       # 4 cells: one ES, one GB, one IT, one FR physical baseline
q2_pilot_cells.tsv       # target 32 cells: 4 × 4 typologies × 2 age extremes
q3_control_cells.tsv     # 102 cells, f=0 only
q4_injected_cells.tsv    # 408 cells, f=0.15/0.30/0.50/1.00
fr_baseline_cells.tsv    # one controlled baseline per accepted FR physical archetype
```

Each TSV row must provide, by explicit path rather than directory inference:

```text
cell_id<TAB>idf_path<TAB>epw_path<TAB>gain_csv_path<TAB>manifest_path
```

Validate the lists before upload:

```python
assert len(q1) == 4
assert len(q2) == 32
assert len(q3) == 102
assert len(q4) == 408
assert fr_baseline["country_stock_code"].eq("fr").all()
assert fr_baseline["sensitivity_f"].eq(0.0).all()
assert q3["sensitivity_f"].eq(0.0).all()
assert set(q4["sensitivity_f"]) == {0.15, 0.30, 0.50, 1.00}
assert not campaign["cell_id"].duplicated().any()
```

Q1–Q3 and the separate France baseline use a constant `3.0 W/m²` gain emitted through the final Step 8 `Schedule:File` adapter. They do not ingest a stochastic occupant diary. Q4 is ES/GB/IT only until the future France occupant branch is accepted.

### 10.4 Prepare the Speed Directory

Keep the campaign under scratch and make the layout deterministic:

```bash
export STEP8_REMOTE="/speed-scratch/$USER/openubem/step8_europe"
mkdir -p "$STEP8_REMOTE"/{bin,config,idfs,weather,schedules,manifests,out,logs,harvest}
mkdir -p "/speed-scratch/$USER/tmp"
```

Upload the pinned EnergyPlus Ubuntu 20.04 distribution, campaign inputs, cell lists, and Step 8 scripts from the local workstation. Then compare local and remote SHA-256 registries before submission.

`/speed-scratch` is active storage: the Speed manual states that inactive files may be automatically cleaned after 90 days. Harvest durable outputs to the local project immediately after each qualification stage.

### 10.5 Step 8 Array Script Template

Create a Step 8-specific batch script rather than using `submit_fleet_t08.sbatch` unchanged:

```bash
#!/bin/bash
#SBATCH --partition=ps
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=02:00:00
#SBATCH --job-name=step8_eu
#SBATCH --output=/speed-scratch/%u/openubem/step8_europe/logs/%x_%A_%a.log

set -euo pipefail

: "${CELL_LIST:?CELL_LIST is required}"
: "${STEP8_REMOTE:?STEP8_REMOTE is required}"

ROW=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$CELL_LIST")
if [ -z "$ROW" ]; then
    echo "No cell at row ${SLURM_ARRAY_TASK_ID}: $CELL_LIST" >&2
    exit 2
fi

IFS=$'\t' read -r CELL_ID IDF EPW GAIN_CSV SOURCE_MANIFEST <<< "$ROW"
for REQUIRED in "$IDF" "$EPW" "$GAIN_CSV" "$SOURCE_MANIFEST"; do
    [ -f "$REQUIRED" ] || { echo "Missing input: $REQUIRED" >&2; exit 3; }
done

EP_DIR=$(ls -d /speed-scratch/$USER/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* | head -1)
OUTDIR="$STEP8_REMOTE/out/$CELL_ID"
WORKDIR="${TMPDIR:-/speed-scratch/$USER/tmp}/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
mkdir -p "$OUTDIR" "$WORKDIR"

cp "$IDF" "$WORKDIR/in.idf"
cp "$EP_DIR/Energy+.idd" "$WORKDIR/Energy+.idd"
cd "$WORKDIR"
"$EP_DIR/ExpandObjects"
[ -f expanded.idf ] && RUN_IDF="$WORKDIR/expanded.idf" || RUN_IDF="$WORKDIR/in.idf"

set +e
"$EP_DIR/energyplus" -w "$EPW" -d "$WORKDIR" "$RUN_IDF"
RC=$?
set -e
echo "$RC" > "$WORKDIR/task.rc"

for FILE in eplusout.sql eplusout.err eplusout.end eplusout.eio eplusout.mdd task.rc; do
    [ -f "$WORKDIR/$FILE" ] && cp "$WORKDIR/$FILE" "$OUTDIR/$FILE"
done
cp "$IDF" "$OUTDIR/model.idf"
cp "$GAIN_CSV" "$OUTDIR/gain_schedule.csv"
cp "$SOURCE_MANIFEST" "$OUTDIR/source_manifest.json"

exit "$RC"
```

This is a target Step 8 template and must receive a shellcheck/smoke review before use. Unlike the generic script, it chooses the EPW per cell, captures a failing return code despite `set -e`, stages repeated I/O under `$TMPDIR`, and retains meter/IDF/schedule evidence required by G8.10–G8.14.

### 10.6 Run Q1 and Q2 Before the Full Control

Submit the four-country physical smoke test:

```bash
Q1_JOB=$(sbatch --parsable \
  --account="$SPEED_ACCOUNT" \
  --array=1-4%4 \
  --export=ALL,STEP8_REMOTE="$STEP8_REMOTE",CELL_LIST="$STEP8_REMOTE/config/q1_smoke_cells.tsv" \
  "$STEP8_REMOTE/bin/step8_cell.sbatch")
echo "$Q1_JOB"
```

After harvest, require 4/4 success, zero severe/fatal errors, meter availability, and correct checksums. Then submit the target 32-cell stratified physical pilot:

```bash
Q2_JOB=$(sbatch --parsable \
  --account="$SPEED_ACCOUNT" \
  --array=1-32%16 \
  --export=ALL,STEP8_REMOTE="$STEP8_REMOTE",CELL_LIST="$STEP8_REMOTE/config/q2_pilot_cells.tsv" \
  "$STEP8_REMOTE/bin/step8_cell.sbatch")
echo "$Q2_JOB"
```

Do not promote to Q3 merely because EnergyPlus returned zero. Check geometry, construction values, saved-IDF schedule assignment, warning kinds, meter balance, denominator area, service-load mode, and result finiteness.

### 10.7 Run More Than 32 Controls Concurrently

After Q1/Q2 approval, submit the 102 controls with the selected throttle:

```bash
: "${SPEED_MAX_CONCURRENT:=32}"
case "$SPEED_MAX_CONCURRENT" in
  4|8|16|32|48|64) ;;
  *) echo "Unsupported throttle: $SPEED_MAX_CONCURRENT" >&2; exit 2 ;;
esac

Q3_JOB=$(sbatch --parsable \
  --account="$SPEED_ACCOUNT" \
  --array="1-102%${SPEED_MAX_CONCURRENT}" \
  --export=ALL,STEP8_REMOTE="$STEP8_REMOTE",CELL_LIST="$STEP8_REMOTE/config/q3_control_cells.tsv" \
  "$STEP8_REMOTE/bin/step8_cell.sbatch")
echo "$Q3_JOB"
```

With `SPEED_MAX_CONCURRENT=64`, SLURM may run up to 64 one-CPU EnergyPlus controls at once—more than 32 CPUs across multiple nodes—while preserving one CPU per simulation.

### 10.8 Enforce Control Audit Before Occupant Runs

Submit a single audit job after Q3. Its script must harvest/recount the 102 controls, execute the pre-occupant acceptance gates, write `q3_control_gate_report.json`, and exit non-zero on any missing or failed requirement:

```bash
Q3_AUDIT_JOB=$(sbatch --parsable \
  --account="$SPEED_ACCOUNT" \
  --dependency="afterok:${Q3_JOB}" \
  --partition=ps --cpus-per-task=1 --mem=8G --time=01:00:00 \
  --export=ALL,STEP8_REMOTE="$STEP8_REMOTE" \
  "$STEP8_REMOTE/bin/step8_control_audit.sbatch")
echo "$Q3_AUDIT_JOB"
```

Only then submit the 408 occupant-modulated cells:

```bash
Q4_JOB=$(sbatch --parsable \
  --account="$SPEED_ACCOUNT" \
  --dependency="afterok:${Q3_AUDIT_JOB}" \
  --array="1-408%${SPEED_MAX_CONCURRENT}" \
  --export=ALL,STEP8_REMOTE="$STEP8_REMOTE",CELL_LIST="$STEP8_REMOTE/config/q4_injected_cells.tsv" \
  "$STEP8_REMOTE/bin/step8_cell.sbatch")
echo "$Q4_JOB"
```

Do not combine Q3 and Q4 in a single 510-row array: array ordering is not a scientific dependency, and `f>0` tasks could start before all controls have been read.

### 10.9 Monitor and Measure From the Workstation

Use short, read-only queries from the local workstation:

```bash
squeue -j "$Q3_JOB,$Q3_AUDIT_JOB,$Q4_JOB"
sacct -j "$Q3_JOB" --format=JobID,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
sacct -j "$Q4_JOB" --format=JobID,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
```

Record the raw `sacct` output in the campaign evidence. Do not infer 64-way execution from the submitted throttle; compute actual concurrency and CPU use from scheduler records.

### 10.10 Harvest Before Cleanup

For Q1, Q2, Q3, and Q4 separately:

1. copy all retained outputs and SLURM logs back to a new local evidence directory;
2. regenerate SHA-256 hashes locally;
3. compare expected cell IDs with harvested cell IDs;
4. build the OpenUBEM/Step 8 manifests;
5. execute gate scoring locally from the harvested immutable files;
6. archive the audit maps and category counts with the simulation report;
7. only after validation and backup, remove the corresponding remote output directory.

Do not apply the generic T08 cleanup before G8.10–G8.14 evidence is harvested. In particular, deleting `.mdd`, the saved IDF, or the emitted gain CSV too early makes independent meter and schedule validation impossible.

### 10.11 Promotion Checklist

The `f>0` occupant campaign is authorized only when all boxes are backed by generated evidence:

```text
[ ] Four-panel input-audit map and exact category counts reviewed
[ ] Q1: 4/4 ES/GB/IT/FR physical smoke cases successful, zero severe/fatal
[ ] Q1 repeated cell passes reproducibility gates
[ ] Q2: target 32/32 physical cases successful or exclusions explicitly approved
[ ] Geometry, envelope, HVAC, weather, and service-load mode validated
[ ] Constant 3.0 W/m² baseline verified from saved IDFs
[ ] Q3: 102/102 controls harvested and independently recounted
[ ] FR baseline manifest is complete and kept separate from the 510-case occupant denominator
[ ] G8.0 and meter/schedule/manifest checks pass
[ ] Mutation tests demonstrate the relevant gates failing
[ ] Q3 audit job exits zero and unlocks Q4
[ ] Selected `%32`/`%48`/`%64` throttle and approval recorded
```

If any item is missing, keep Q4 **BLOCKED**. Faster cluster execution must never shorten the scientific validation sequence.

---

## 11. Task Ledger and Progress Log

This section is the operational index. Detailed scientific requirements remain in the MVP; implementation sessions update the status and append a dated evidence row here.

| Task group | Scope | Initial status | Required promotion evidence |
|---|---|---|---|
| `T-DOC` | MVP/walkthrough roles, captions, reusable assets | `LOCAL_PASS` | Link, caption, and source-asset render checks |
| `T-FR-PHYS` | French residential registry, layouts, IDFs, weather, baseline simulations | `NOT_RUN` | Audited registry and FR-B evidence bundle |
| `T-FR-OCC` | French held-out diaries and occupant-effect sweep | `BLOCKED` / future scope | Approved diary/fold/weather contract |
| `T-FILTER` | Residential-only registry and explicit non-residential exclusions | `NOT_RUN` | Exclusion audit and manifest-disjointness tests |
| `T-SELECT` | Real contiguous dense residential neighbourhood selection and four-panel audit | `NOT_RUN` | `NS-01`–`NS-10`, boundary, candidate ranking, and reconciled panels |
| `T-GEO` | `GEO-01`–`GEO-10`, including Grasshopper parity | `NOT_RUN` | Generated comparison and mutation reports |
| `T-S0-S3` | 4/12/32/96-building sample groups | `NOT_RUN` | Per-stage case accounting and resource report |
| `T-N1` | One selected contiguous dense residential neighbourhood with ≥ 100 residential buildings (500–600 preferred) | `NOT_RUN` | S0–S3, `T-SELECT`, and audited N1 manifest |
| `T-N2` | Optional contiguous dense residential neighbourhood scale-up to 1,000 buildings | `NOT_RUN` | N1 evidence and explicit capacity approval |
| `T-Q1-Q4` | Four-country physical smoke and ES/GB/IT occupant campaign | `NOT_RUN` | Stage-specific retained evidence |

*Walkthrough Table 3. Living task ledger. `BLOCKED` on `T-FR-OCC` describes the intentionally deferred occupant-input dependency; it does not block French physical-model work. The append-only CSV schema is [`content/walkthrough_progress_log.csv`](content/walkthrough_progress_log.csv).*

### 11.1 Append-Only Progress-Log Rules

For every material attempt, append one row containing UTC date, repository commit, work package/task ID, status, exact command, evidence path, decision or blocker, and one next action. Use only `DOCUMENTED`, `IMPLEMENTED_NOT_TESTED`, `LOCAL_PASS`, `SPEED_SUBMITTED`, `SPEED_COMPLETE_UNAUDITED`, `ACCEPTED`, `NOT_RUN`, or `BLOCKED`. Never overwrite a failed attempt with a later pass; append the correction as a new row.

| Date | Commit | Task | Status | Command / evidence | Decision or blocker | Next action |
|---|---|---|---|---|---|---|
| 2026-08-23 | `e04f42a` + dirty-tree caveat | `T-DOC` | `IMPLEMENTED_NOT_TESTED` | Updated active Markdown and `content/` assets | PDF/link/caption verification pending | Run documentation validation and record outcome |
| 2026-08-23 | `e04f42a` + dirty-tree caveat | `T-DOC` | `LOCAL_PASS` | `git diff --check`; relative-link/SVG/CSV validation; `scripts/convert_docs_to_pdf.py`; headless SVG previews | Both PDFs regenerated; repaired figures visually inspected | Begin CP0 / EU-01–EU-02 local implementation slice |
| 2026-08-23 | `e04f42a` + dirty-tree caveat | `T-DOC` | `LOCAL_PASS` | Final static validation; director prompt archived and updated | Markdown/source assets are authoritative; PDF output is optional | Begin CP0 / EU-01–EU-02 local implementation slice |
| 2026-08-23 | `e04f42a` + dirty-tree caveat | `T-SELECT` | `DOCUMENTED` | Added `NS-01`–`NS-10`, reference four-panel asset, and future-session prompt rule | N1/N2 are real contiguous dense residential neighbourhoods, not disconnected samples | Implement candidate-neighbourhood metrics and deterministic residential filter |
| 2026-08-23 | `fda5336` + dirty-tree caveat | `T-DOC` | `LOCAL_PASS` | Source-verification of every *Iseri et al. (2025)* numeric attribution against the paper PDF, `outputs/`, `DeepResearch/`, `resources/`; recomputation from `AllV{1,2,3,4}_updated2023June.csv`. Evidence: [`debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md`](debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md) | 9 attributions failed verification and were remediated; plan `CLOSED`, CP-1 and CP-2 satisfied; rulings Q1-C, Q2-A, Q3-B, Q4-A, Q5-A recorded | Begin CP0 / EU-01–EU-02 local implementation slice |
| 2026-08-23 | `fda5336` + dirty-tree caveat | `T-DOC` | `DOCUMENTED` | Source-alignment pass v1.3: parent tier-1 authorities (`4thJ_08_bemSimulation.md`, `_val.md`, `outputs_step8/archetype_parameter_provenance.md`, `archetype_parameters_{es,uk,it}.csv` re-read: 24/36/42 rows, 44 columns, all `EU.SUH`/`EU.MUH`, `phi_int = 3`). Evidence: MVP §11 (Tables 13–19); this document §2.1, §4.1, §5.4, §9.3.1, §9.5, §9.8, §9.12 notes; §12 executor contract | EU boundary-condition set governs `c_m`/`n_air_use` (national values superseded in place); parent tables are the EU-01 input; 22 bands listed verbatim; weather ruled-not-acquired; chaining rule blocks `f>0`; perturbation matrix itemised | Dispatch slice `X-01` (§12.4) to an external executor and audit its evidence pack |
| 2026-08-23 | `fda5336` + dirty-tree caveat | `T-DEC` | `DOCUMENTED` | `openpyxl` read of `Calc.Set.Building` cached values for the 102 archetype keys → [`debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv`](debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv); rulings written under user delegation → [`debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md); briefs → [`DeepResearch/`](DeepResearch/README.md) | D-EU-01…07 RULED (box from areas + `n_Apartment`; mass-less U + `InternalMass` = `c_m`; `n_use + n_inf`; all 102 rows; four-end-use with TABULA `q_w_nd`; no cooling; `F_red_temp` as U multiplier); D-EU-05/08/10/11 OWED to DR08–DR11; D-EU-09 chaining BLOCKED upstream | Run DR08–DR11 in a deep-research tool; dispatch `X-01` |
| 2026-08-23 | `fda5336` + dirty-tree caveat | `T-DEC` | `DOCUMENTED` | DR08–DR11 reports returned and audited against their briefs' acceptance tests; episcope.eu clause re-verified live (verbatim); Copernicus PDF URL stale but CDS states CC-BY → [`DeepResearch/README.md`](DeepResearch/README.md) §Acceptance Record | **All four reports ACCEPTED**; D-EU-05/08/10/11 **CLOSED** (ERA5 + Madrid/London/Bologna + six-gate EPW checklist; publication permitted with the IEE TABULA + EPISCOPE attribution; Lyon = fourth city, datasets/crosswalks/candidates pinned; France = 40 `FR.N` rows, 10 `FR.OPHM` excluded); D-EU-01/02/03/07 **VALIDATED** by DR11 (3 numeric fixtures adopted into X-04); **D-EU-09 sole remaining block**, `f>0` only — MVP §11.13 Table 21 | Dispatch `X-01` (prompt §19.3); `X-07`/`X-08` defined in §12.6 |
| 2026-08-23T18:12:24Z | `fda5336` + dirty-tree caveat | `CP0 / EU-01` | `BLOCKED` | `pytest -q tests/test_eu_tabula_loader.py` → 1 passed, 23 errors; evidence: `openubem/outputs/eu_evidence/X-01/` | §9.3.1 requires every `Code_BuildingVariant` to end `.001.001`, but copied UK parent rows at lines 3/5/18/21/29/32 end `.002.001` or `.005.001` | Resolve the authority conflict before changing the invariant or parent fixture |

| 2026-08-23T18:30:34Z | `fda5336` + dirty-tree caveat | `CP0 / EU-01 / X-01` | `LOCAL_PASS` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_tabula_loader.py` -> 24 passed, 1 warning; attempted full suite evidence: `openubem/outputs/eu_evidence/X-01/` | Parent generator `tools/4thJ_step8_tabula.py:315` makes final `.001` the existing-state invariant; full suite stalled at 89% on unrelated Windows/joblib access violations in `tests/test_step3_orchestrator.py` | Begin X-02 registry generation with EU boundary-condition join |

| 2026-08-23T18:36:03Z | `fda5336` + dirty-tree caveat | `EU-01 / X-02` | `LOCAL_PASS` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_construction_sets.py` -> 6 passed; evidence: `openubem/outputs/eu_evidence/X-02/` | Generated 24 ES + 36 GB + 42 IT records with source-column parity, verified attribution, and byte-identical regeneration; direct workbook ventilation identity uses `h_room` | Begin X-03 construction-period mapping and boundary tests |

| 2026-08-23T18:38:08Z | `fda5336` + dirty-tree caveat | `EU-02 / X-03` | `LOCAL_PASS` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_construction_sets.py` -> 47 passed; evidence: `openubem/outputs/eu_evidence/X-03/` | `tabula_period` implements all 22 bands; resolver uses non-composite then `.Gen` precedence and explicitly refuses gaps/ambiguity | Begin X-04 single-surface and DR11 numeric physics fixtures |

| 2026-08-23T18:40:50Z | `fda5336` + dirty-tree caveat | `EU-01 / X-08` | `LOCAL_PASS` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_fr_registry.py tests\\test_eu_construction_sets.py tests\\test_eu_tabula_loader.py` -> 81 passed; evidence: `openubem/outputs/eu_evidence/X-08/` | Re-derived 40 `FR.N` records, excluded 10 `FR.OPHM` rows with reasons, and preserved the native `FR.N.MFH.08` anomaly | Resume X-04 local EnergyPlus physics fixtures; X-07 weather acquisition remains parallel |

| 2026-08-23T19:20:00Z | `fda5336` + dirty-tree caveat | `EU-03 / X-04` | `BLOCKED` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_physics_primitives.py tests\\test_eu_physics_energyplus.py` -> 5 passed, 1 strict xfailed; evidence: `openubem/outputs/eu_evidence/X-04/` | Saved-IDF D-EU-02 U/mass/b-factor arithmetic passes. EnergyPlus R5 gives the correct 10.000 C other-side temperature but 19.993496 W rather than DR11's literal 20.000 +/- 0.001 W because an inside film remains; R3/R7 are still absent. Decision record: `debugs/docs/DONE-docs/DECISIONS_X-04_R5-engine-film-2026-08-23.md` | Await an accepted R5 numerical-fixture interpretation; then implement R3 and R7 |

| 2026-08-23T19:25:00Z | `fda5336` + dirty-tree caveat | `EU-07 / X-07` | `BLOCKED` | Local dependency audit; evidence: `debugs/docs/DONE-docs/DECISIONS_X-07-dependency-audit-2026-08-23.md` | `.venv` has no `cdsapi`, `pvlib`, or `xarray`, and `C:\\Users\\o_iseri\\.cdsapirc` is absent. ERA5 retrieval, licence-at-download capture, EPW conversion, and six-gate validation cannot be claimed. | Provide CDS credentials and packages; retain `RULED_NOT_PINNED` until the diary corpus is readable |

| 2026-08-23T19:30:00Z | `fda5336` + dirty-tree caveat | `T-DOC / T-DOC-006` | `DOCUMENTED` | Evaluator packet: `debugs/docs/DONE-docs/DECISION_REQUEST_X-04_X-07_2026-08-23.md` | Consolidates the exact X-04 R5 engine discrepancy and X-07 missing CDS/package dependencies without changing either slice's blocked status. | Await evaluator decision/action for X-04 and X-07 |

| 2026-08-23T19:40:00Z | `fda5336` + dirty-tree caveat | `EU-03 / X-04` | `PARTIAL` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_physics_primitives.py tests\\test_eu_physics_energyplus.py` -> 8 passed; evidence: `openubem/outputs/eu_evidence/X-04/targeted_pytest_after_r5_r7.log` | Evaluator accepted the R5 engine-aware tolerance. R5 and local EnergyPlus R7 pass; the R3 analytical time-constant reference passes, but the R3 dynamic EnergyPlus initialization fixture is still outstanding. | Implement and run the R3 dynamic EnergyPlus free-float fixture |

| 2026-08-23T19:40:00Z | `fda5336` + dirty-tree caveat | `EU-07 / X-07` | `PARTIAL` | `.venv\\Scripts\\python.exe -m pip install cdsapi pvlib xarray`; evidence: `openubem/outputs/eu_evidence/X-07/dependency_installation.log` | Approved packages are installed (`cdsapi` 0.7.7, `pvlib` 0.15.2, `xarray` 2026.7.0). Live ERA5 acquisition remains blocked only by absent CDS credentials. | Configure project-owned CDS credentials, then fetch, convert, and validate ERA5 |

| 2026-08-23T20:05:00Z | `fda5336` + dirty-tree caveat | `EU-03 / X-04` | `PARTIAL` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_physics_primitives.py tests\\test_eu_physics_energyplus.py` -> 8 passed, 1 strict xfailed; evidence: `openubem/outputs/eu_evidence/X-04/targeted_pytest_r3_fixture.log` | R3 is now a local 10x10x3 m EnergyPlus release fixture with verified 20 C preconditioning and a 0 C boundary. It reports 19.998714 C at 14.0625 h, rather than DR11's 7.357589 C target; R5/R7 pass under the accepted R5 ruling. The R3 assertion remains a strict expected failure. | Request EnergyPlus-model reconciliation; continue independent X-05 work |

| 2026-08-23T20:30:00Z | `fda5336` + dirty-tree caveat | `EU-04 / X-05` | `PARTIAL` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_box_generator.py tests\\test_eu_construction_sets.py tests\\test_eu_fr_registry.py` -> 60 passed; evidence: `openubem/outputs/eu_evidence/X-05/targeted_pytest.log` | Four D-EU-01 S0 box plans conserve plate area, conditioned volume, and exposed-wall area. All 142 registry `h_Transmission` values read back exactly from cached source components; ventilation uses the governing `h_room` relation. Infeasible rectangle inputs fail explicitly. | Implement saved-IDF emission and integrate heating/air/`F_red_temp` in X-06 |

| 2026-08-23T20:40:00Z | `fda5336` + dirty-tree caveat | `EU-05 / EU-07 / X-06` | `PARTIAL` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_heating_controls.py tests\\test_eu_physics_primitives.py` -> 7 passed; evidence: `openubem/outputs/eu_evidence/X-06/targeted_pytest.log` | Saved-IDF controls emit 20 C heating-only IdealLoads, always-off cooling, all-convective 3 W/m2 gains, and `F_red_temp`-scaled constant ACH. | Emit S0 geometry/envelope surfaces into the same saved IDF and run the heating-only fixture |

| 2026-08-23T20:45:00Z | `fda5336` + dirty-tree caveat | `T-DOC / T-DOC-007` | `DOCUMENTED` | Evaluator packet: `debugs/docs/DONE-docs/ANALYSIS_REQUEST_X-04-R3_X-07-CDS_2026-08-23.md` | Separates the exact current R3 EnergyPlus fixture, its strict failure, its four resolution options, and the safe CDS credential action needed for live ERA5 acquisition. | Await evaluator response only for R3 formulation and CDS credential availability; continue independent work |

| 2026-08-23T21:32:52Z | `fda5336` + dirty-tree caveat | `T-DOC / T-DOC-008` | `DOCUMENTED` | Fresh-session continuation prompt: `prompts/previous/EXECUTOR_X-01_paste_into_codex.md`; director §19.3–§19.6 updated | The historical X-01-only executor prompt is replaced at the active path by an autonomous continuation handoff. It records completed slices, remaining X-05/X-06 work, and the R3/CDS constraints without pretending a later session runs in the background. | Resume saved-IDF S0 geometry/envelope emission and the heating-only fixture; append both logs after each material result |

| 2026-08-23T22:08:25Z | `fda5336` + dirty-tree caveat | `EU-03 / T-VERIFY-009` | `LOCAL_PASS` | 9 physics tests passed in 2.92 s; resolved `tests\test_eu_*.py` -> 94 passed in 12.28 s; evidence: `openubem/outputs/eu_evidence/X-04/targeted_pytest_complete_reverified.log` | Independently confirms accepted X-04: analytical R3 is normative, the natural-convection EnergyPlus fixture proves physical decay, and R5/R7 pass. A repository-wide rerun hung at 10% on the known Windows/joblib process issue and is explicitly not claimed as complete. | Continue X-05/X-06 saved-IDF S0 envelope emission and heating-only integration; X-07 remains blocked on CDS credentials |
| 2026-08-23T22:18:00Z | `fda5336` + dirty-tree caveat | `T-DOC / T-DOC-010` | `DOCUMENTED` | Table 9.7 status matrix and machine-readable CSV updated | Completed: EU-01/EU-02/EU-03. In progress: EU-04/EU-05 and EU-07 (blocked only on CDS credentials). Not started: EU-06/EU-08/EU-09/EU-10. | Continue EU-04/EU-05 saved-IDF integration; retain the EU-07 credential block |
| 2026-08-23T22:25:00Z | `fda5336` + dirty-tree caveat | `T-DOC / T-DOC-011` | `DOCUMENTED` | Active executor and director continuation prompts synchronized | The fresh-session prompts now contain a superseding live snapshot and require their own update after every material result, together with both progress logs. | Continue EU-04/EU-05 equivalent-envelope saved-IDF validation; preserve EU-07 CDS credential block |
| 2026-08-23T23:15:00Z | `fda5336` + dirty-tree caveat | `EU-04/EU-05 / X-05/X-06` | `LOCAL_PASS` | `.venv\Scripts\python.exe -m pytest -q` with the resolved `tests\test_eu_*.py` list -> 98 passed in 13.12 s; focused evidence: `openubem/outputs/eu_evidence/X-05/equivalent_envelope_and_controls_pytest.log` -> 17 passed in 3.59 s | Area-faithful S0 equivalent envelopes independently read back reduced `h_Transmission` for SFH/TH/MFH/AB; controls are integrated; the SFH heating-only EnergyPlus smoke completes with zero severe errors. | Continue the next unblocked local slice; EU-07 live ERA5 remains blocked only by CDS credentials |
| 2026-08-23T23:16:00Z | `fda5336` + dirty-tree caveat | `T-DOC / T-DOC-012` | `DOCUMENTED` | Reviewed MVP Table 9.7 work-package scope | X-05/X-06 are `LOCAL_PASS` sub-slices, but full EU-04/EU-05 require later S1–S3/layout and sampled-dwelling gates; their WP status remains `IN_PROGRESS`. | Continue the next unblocked local slice; do not overstate S0 completion as full-work-package completion |
| 2026-08-23T23:30:00Z | `fda5336` + dirty-tree caveat | `EU-07 / X-07` | `PARTIAL` | `.venv\Scripts\python.exe -m pytest -q tests\test_eu_weather_registry.py` → 6 passed in 0.62 s | Added deterministic `RULED_NOT_PINNED` weather registry, credential-presence check that never reads a secret, SHA-256 helper, and offline DR08 gates 1–4 (header, 8,760-hour continuity, missing sentinels, physical/solar bounds). No ERA5 data, licence text, or actual EPW acceptance is claimed. | Continue the next unblocked local slice; when CDS credentials exist, acquire ERA5 and complete gates 5–6 plus diary-window pinning |
| 2026-08-23T23:32:00Z | `fda5336` + dirty-tree caveat | `T-VERIFY / X-07` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 104 passed in 13.25 s | Full European regression after the registry pre-acquisition layer: 104 tests pass. This verifies local compatibility only; it does not promote EU-07's real-weather gates or clear its CDS dependency. | Continue the next unblocked local slice; retain EU-07 as `PARTIAL` until actual ERA5 evidence exists |
| 2026-08-23T23:35:00Z | `fda5336` + dirty-tree caveat | `EU-06 / SCHEDULE-01` | `PARTIAL` | `.venv\Scripts\python.exe -m pytest -q tests\test_eu_external_schedules.py` → 7 passed in 0.56 s | Added the external, non-fractional `Schedule:File` gain path. The f=0 control works without a diary/chaining rule; all five levels conserve 3.0 W/m², valid zero-presence days are counted, and f>0 is refused without the mandatory chaining rule. Saved-IDF read-back and real Step 7 input remain outstanding. | Continue the next unblocked local slice; retain f>0 EU-06 as blocked until the upstream chaining rule is ruled |
| 2026-08-23T23:37:00Z | `fda5336` + dirty-tree caveat | `T-VERIFY / EU-06` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 111 passed in 13.30 s | Full European regression after the EU-06 external schedule adapter: 111 tests pass. This is local compatibility evidence only; EU-06 remains `PARTIAL` until real Step 7 input, saved-IDF assignment read-back, and the f>0 chaining rule are resolved. | Continue the next unblocked local slice; retain the EU-06 and EU-07 external blocks accurately |
| 2026-08-23T23:40:00Z | `fda5336` + dirty-tree caveat | `EU-08 / CAMPAIGN-01` | `PARTIAL` | `.venv\Scripts\python.exe -m pytest -q tests\test_eu_campaign_manifest.py` → 3 passed in 0.56 s | Added deterministic ES/GB/IT 510-row campaign planning: 102 f=0 controls and 408 f>0 rows, unique IDs, five ordered levels per archetype, and Q3/Q4 TSV lists. No run is submitted; weather paths remain `PENDING_EU07_WEATHER` and injected rows remain `BLOCKED_CHAINING_RULE`. | Continue the next unblocked local slice; do not submit or report campaign results before physical inputs and gates exist |
| 2026-08-23T23:42:00Z | `fda5336` + dirty-tree caveat | `T-VERIFY / EU-08` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 114 passed in 13.25 s | Full European regression after campaign-plan implementation: 114 tests pass. This is a local compatibility result only; the campaign remains unsubmitted and awaits final physical inputs and acceptance gates. | Continue the next unblocked local slice; retain external dependencies and do not claim campaign execution |
| 2026-08-24T00:16:55Z | `fda5336` + dirty-tree caveat | `EU-09 / GATES-01` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 117 passed in 16.09 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_pre_submission_gates.log` | Pre-submission G8.0/G8.8/G8.9/G8.14/G8.16 scorer and null/mutation tests pass. This is only a partial EU-09 result: meter, saved-IDF, warning, geometry, and numerical-output gates are not implemented or claimed. | Continue the next local validation slice; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:19:33Z | `fda5336` + dirty-tree caveat | `EU-09 / GATES-02` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 121 passed in 16.52 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_meter_gates.log` | MDD-derived G8.10/G8.11 meter validation passes. The legacy `Gas:Facility` and zero-end-use mutations fail as required. This remains partial EU-09: saved-IDF, warning, geometry, and numerical-output gates are not implemented or claimed. | Continue the next local validation slice; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:21:15Z | `fda5336` + dirty-tree caveat | `EU-09 / GATES-03` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 122 passed in 17.28 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_saved_idf_gates.log` | Independent saved-IDF G8.12/G8.13 audit passes. A wrong schedule assignment and `Interpolate to Timestep = Yes` fail their designated gates. This remains partial EU-09: warning, geometry, and numerical-output gates are not implemented or claimed. | Continue the next local validation slice; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:22:36Z | `fda5336` + dirty-tree caveat | `EU-09 / GATES-04` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 125 passed in 16.45 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_warning_gate.log` | G8.15 warning-kind triage passes. One unclassified warning fails even when benign warnings repeat, and severe/fatal diagnostics fail hard. This remains partial EU-09: geometry and numerical-output gates are not implemented or claimed. | Continue the next local validation slice; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:28:47Z | `fda5336` + dirty-tree caveat | `EU-09 / GATES-05` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 127 passed in 14.12 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_reproducibility_gates.log` | G8.1–G8.4 same-cell reproducibility scoring passes. The clean rerun passes and the 1.2 energy-scale mutation fails G8.1/G8.3. G8.5–G8.7 peak and geometry gates are not implemented or claimed. | Continue the next local validation slice; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:30:12Z | `fda5336` + dirty-tree caveat | `EU-10 / ACCOUNTING-01` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 129 passed in 16.43 s; evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_four_end_use_accounting.log` | Ruled four-end-use plus labelled TABULA DHW accounting guard passes and rejects physical service loads in this mode, preventing double counting. This is partial EU-10: extraction, aggregation, and dossier export are not implemented or claimed. | Continue the next local results slice; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:34:45Z | `019ae9f` + dirty-tree caveat | `EU-09 / GATES-06` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 135 passed in 13.97 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_peak_geometry_gates.log` | Parent-aligned G8.5–G8.7 contracts now pass locally: peak magnitude ±15%, timing ≤1 h against a named comparison series, and graded as-modelled EUI band with explicit geometry denominator identity; empirical EUI is informational only. A >15% peak, a two-hour shift, and a 1.5× wrong-area mutation fail their designated gates. This is not campaign evidence: retained artefacts and the complete V8 coverage cross-tab remain pending. | Continue EU-10 result-contract/extraction work; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:36:51Z | `019ae9f` + dirty-tree caveat | `EU-10 / RESULT-01` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 137 passed in 16.83 s; evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_result_record_contract.log` | Added a self-describing EU-10 cell-result contract: named weather year/id, denominator, coefficient-table checksum, four-end-use annual result, 12 monthly and 8,760 hourly simulated-energy values with closure, and a derived peak. TABULA DHW remains explicitly post-processed, never silently inserted into simulated time series. This remains partial EU-10: retained-output extraction, aggregation, and dossier export are unimplemented and unclaimed. | Continue retained-output extraction/aggregation contract work; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:50:42Z | `019ae9f` + dirty-tree caveat | `EU-10 / RESULT-02` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 139 passed in 18.65 s; evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_result_aggregation.log` | Corrected the cell schema to require the explicit weather window (the ERA5 route spans approved two-year acquisition windows), then added within-fold aggregation and deterministic JSON bundle export. Cross-weather-window mixing is refused; DHW remains separately labelled. This remains partial EU-10: retained-output extraction and dossier export are unimplemented and unclaimed. | Continue retained-output extraction/dossier contract work; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T00:57:08Z | `019ae9f` + dirty-tree caveat | `EU-09 / GATES-07` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 143 passed in 14.05 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_perturbation_coverage.log` | Exported frozen P01–P12 Table 17 fixture matrix and added a cross-tab evaluator. It fails a missing probe, a required failure that stays clean, or a required-clean checkpoint that turns dirty; P05 retains separate G8.12 assignment/value checkpoints and P12 requires all observed checkpoints to remain clean. This is local fixture-contract evidence only, not retained campaign evidence; V8.c band source and V8.d retained-input audit remain pending. | Continue EU-10 retained-output extraction/dossier work or EU-09 V8.c band-source/V8.d retained-input audit; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T01:00:50Z | `019ae9f` + dirty-tree caveat | `EU-10 / RESULT-03` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 145 passed in 14.92 s; evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_retained_csv_extraction.log` | Added a read-only retained `eplusout.csv` extractor for heating, cooling, lighting and equipment. It requires `Date/Time`, all four hourly J outputs, exactly 8,760 non-leap calendar rows, and sends annual/monthly/hourly values through EU-10 closure checks. It neither reads facility/service meters nor inserts TABULA DHW into a simulated time series. Fixture-contract evidence only; campaign output capture and dossier export remain pending. | Continue EU-10 dossier contract work or EU-09 V8.c/V8.d audits; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T01:02:34Z | `019ae9f` + dirty-tree caveat | `EU-10 / RESULT-04` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 147 passed in 14.14 s; evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_dossier_contract.log` | Added a fail-closed machine-readable dossier contract. It requires exactly G8.0–G8.16, all passed at hard severity, measured campaign-manifest/result-bundle SHA-256 digests, and an explicit evidence scope. `local_fixture_contract` is visibly distinct from `retained_campaign`. This is schema/fixture evidence only; retained campaign artefacts and final dossier evidence remain pending. | Continue EU-09 V8.c/V8.d audits or EU-04/EU-05 sample-group work; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T01:04:08Z | `019ae9f` + dirty-tree caveat | `EU-09 / GATES-08` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 149 passed in 14.23 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_v8c_band_source.log` | Moved V8.c fixed bands to one immutable imported module. G8.1–G8.6 and G8.10 take their limits from it; G8.7 remains an explicit archetype-specific input rather than a generic copied band. This is local contract evidence only; retained campaign artefacts and V8.d per-archetype retained-IDF audit remain pending. | Continue EU-09 V8.d retained-IDF audit or EU-04/EU-05 sample-group work; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T01:24:42Z | `019ae9f` + dirty-tree caveat | `EU-09 / GATES-09` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 150 passed in 14.32 s; evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_v8d_saved_idf_audit.log` | Added V8.d per-archetype saved-IDF geometry audit. S0 serializes explicit zone area, volume, and equivalent per-storey height; an independent retained-IDF parser derives integral storeys and verifies the matching archetype identifier in saved surfaces. Reused paths, swaps, missing fields, and mismatches fail. This is local fixture-contract evidence only; retained campaign artefacts remain pending. | Continue EU-04/EU-05 sample-group work or retained-campaign evidence integration; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T01:28:08Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-07` | `PARTIAL_BLOCKED_AUTHORITY` | Resolved `tests\test_eu_*.py` list → 154 passed in 14.10 s; evidence: `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo07_dwelling_allocation.log` | Added the D-EU-01/D-EU-04 dwelling allocation kernel: half-up `n_Apartment`, exact quotient/remainder allocation across integral storeys, and 6% unconditioned core external to the conditioned TABULA plate only at ≥2 dwellings/storey. The three GB `SyAv` rows have non-integer `n_Storey` without a written rounding rule, so they are fail-closed; analysis is in `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md`. | Continue independent EU-04/EU-05 work; do not model the three GB SyAv rows until their `n_Storey` rule is decided; preserve EU-06 chaining and EU-07 CDS external blocks |
| 2026-08-24T09:47:31Z | `019ae9f` + dirty-tree caveat | `EU-08 / CAMPAIGN-02` | `LOCAL_PASS` | Resolved `tests\test_eu_*.py` list → 156 passed in 14.33 s; evidence: `openubem/outputs/eu_evidence/EU-08/all_european_tests_after_dependency_digest_cache.log` | Added a file-derived dependency-digest cache contract: IDF, emitted schedule, and weather are SHA-256 measured from disk; EnergyPlus build, adapter configuration, and source commit are canonical inputs. A reusable result additionally requires legacy `eplusout.end`/`eplusout.sql` completion, `status=success`, and an exact digest match. Missing inputs, stale digests, failed status, and incomplete output fail. This is local fixture-contract evidence only; no campaign was submitted. | Continue independent EU-04/EU-05 work or retained-campaign integration; preserve EU-06 chaining, EU-07 CDS, and EU-04 non-integer-storey authority blocks |
| 2026-08-24T09:52:09Z | `019ae9f` + dirty-tree caveat | `EU-05 / HVAC-02` | `PARTIAL_BLOCKED_FR_AUTHORITY` | Resolved `tests\test_eu_*.py` list → 161 passed in 18.52 s; evidence: `openubem/outputs/eu_evidence/EU-05/all_european_tests_after_hvac_controls.log` | Audited all 102 ES/GB/IT occupant-control records: heating-only IdealLoads, constant natural air, and all-convective `OtherEquipment` gains emit deterministically, while invalid air inputs fail before IDF output. `FR.N.AB.10.Gen.ReEx.001.001` has `F_red_temp=1.0086438144755208`, above the current reduction range; it remains fail-closed and is documented in `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-05_FR-Fred-temp_2026-08-24.md` rather than being changed or clamped. This is local control-contract evidence only. | Continue independent EU-04/EU-08/EU-09/EU-10 work; do not emit the France row until its multiplier rule is decided; preserve EU-06 chaining and EU-07 CDS blocks |
| 2026-08-24T11:53:11Z | `019ae9f` + dirty-tree caveat | `CP0 / HANDOFF-01` | `DOCUMENTATION_UPDATED` | Verified with executor-reference search and `git diff --check`; evidence: `prompts/DIRECTOR_PROMPT_european_locations.md` | Consolidated future-session instructions into the single self-contained manager prompt. The historical `EXECUTOR_X-01` file is explicitly superseded and is not maintained; no work-package implementation status changed. | Resume the next unblocked local EU-05 sizing/design-day acceptance slice; retain EU-04, EU-05-France, EU-06, and EU-07 authority/credential blocks |
| 2026-08-24T12:38:30Z | `019ae9f` + dirty-tree caveat | `EU-05 / HVAC-03` | `LOCAL_PASS` | `tests\\test_eu_hvac_sizing.py` → 1 passed in 1.37 s; resolved `tests\\test_eu_*.py` list → 162 passed in 15.60 s; evidence: `openubem/outputs/eu_evidence/EU-05/targeted_hvac_sizing_design_day.log`, `openubem/outputs/eu_evidence/EU-05/all_european_tests_after_hvac_sizing.log` | The runnable S0 ES SFH equivalent-envelope fixture completes local EnergyPlus zone sizing and reports a nonzero 16,352.93390 W design heating load. This is S0 fixture evidence only: it does not promote S1–S3, override the blocked France multiplier row, acquire weather, or submit a campaign. | Continue an independent EU-04/EU-08/EU-09/EU-10 local slice; retain the EU-04 fractional-storey, EU-05-France, EU-06 chaining, and EU-07 CDS blocks |
| 2026-08-24T12:51:51Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-01-GEO-09` | `LOCAL_PASS` | `tests\\test_eu_dwelling_allocation.py tests\\test_eu_floor_partition_audit.py` → 10 passed in 0.05 s; resolved `tests\\test_eu_*.py` list → 168 passed in 16.39 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo01_geo09_partition_audit.log` | Added a fail-closed supplied-floor-partition auditor. The clean axis-aligned 96 m² rectangle conserves the plate and four-dwelling count with zero gap, overlap, and outside area; named GEO-09 gap, overlap, outside, and count mutations fail. This is a local audit contract, not a production layout generator or Grasshopper parity result. | Continue an independent EU-04 geometry fixture or EU-08/EU-09/EU-10 local slice; preserve the GB fractional-storey, France multiplier, EU-06 chaining, and EU-07 CDS blocks |

| 2026-08-24T13:38:47Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-02` | `LOCAL_PASS` | `tests\\test_eu_dwelling_allocation.py tests\\test_eu_floor_partition_audit.py` → 11 passed in 0.06 s; resolved `tests\\test_eu_*.py` list → 169 passed in 15.93 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo02_partition_audit.log` | Rotating both the clean 96 m² footprint and four supplied dwelling polygons by 31° preserves the local audit's count, union area, and zero gap, overlap, and outside area. This is local orientation-invariance evidence, not a production layout generator or Grasshopper parity result. | Continue an independent supplied-geometry GEO-03/GEO-05 audit slice or EU-08/EU-09/EU-10 local work; preserve the GB fractional-storey, France multiplier, EU-06 chaining, and EU-07 CDS blocks |

| 2026-08-24T13:45:29Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-03` | `LOCAL_PASS` | `tests\\test_eu_dwelling_allocation.py tests\\test_eu_floor_partition_audit.py` → 12 passed in 0.06 s; resolved `tests\\test_eu_*.py` list → 170 passed in 19.07 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo03_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo03_partition_audit.log` | A manually supplied L-shaped 80 m² footprint cleanly partitions into five valid dwelling polygons with zero gap, overlap, and outside area. This is local non-convex audit evidence, not a production layout generator or Grasshopper parity result. | Continue an independent supplied-geometry GEO-05 audit slice or EU-08/EU-09/EU-10 local work; preserve the GB fractional-storey, France multiplier, EU-06 chaining, and EU-07 CDS blocks |

| 2026-08-24T13:46:50Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-05` | `LOCAL_PASS` | `tests\\test_eu_dwelling_allocation.py tests\\test_eu_floor_partition_audit.py` → 13 passed in 0.06 s; resolved `tests\\test_eu_*.py` list → 171 passed in 19.18 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo03_geo05_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo05_partition_audit.log` | A 144 m² supplied footprint with a 16 m² courtyard hole accepts four dwellings covering the remaining 128 m² plate; a dwelling crossing the courtyard fails `OUTSIDE_FOOTPRINT`. This is local courtyard-topology audit evidence, not a production layout generator or Grasshopper parity result. | Continue independent EU-04 GEO-04/GEO-06 work or EU-08/EU-09/EU-10 local work; preserve the GB fractional-storey, France multiplier, EU-06 chaining, and EU-07 CDS blocks |

| 2026-08-24T14:47:05Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-07` | `LOCAL_PASS` | `tests\\test_eu_dwelling_allocation.py` -> 5 passed in 0.04 s; resolved `tests\\test_eu_*.py` list -> 172 passed in 19.48 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo07_syav_storey_rounding.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo07_syav_storey_rounding.log` | Owner-ruled Option A applies stable half-up rounding to the three GB `SyAv` `n_Storey` values (3/4/4), retains raw floats in provenance, derives plates from the rounded physical storey count, and conserves `A_C_Ref`; dwellings allocate [3,2,2], [4,4,3,3], and [5,4,4,4]. This closes the storey-count authority gap only. | Continue real-footprint GEO-04/GEO-06 work or independent EU-08/EU-09/EU-10 work; production layout, Grasshopper parity, sample groups, and S1-S3 remain pending |

| 2026-08-24T15:10:55Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-04` | `LOCAL_PASS` | `tests\test_eu_floor_partition_audit.py tests\test_eu_dwelling_allocation.py` -> 21 passed in 0.10 s; resolved `tests\test_eu_*.py` list -> 179 passed in 16.12 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo04_narrow_fallback.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo04_narrow_fallback.log` | The European feasibility gate applies the strict `<8 m` narrow-width rule from the minimum rotated rectangle, returns `NARROW_FOOTPRINT_LT_8M`, and records `FALLBACK_ONE_ZONE_PER_FLOOR` without emitted dwelling geometry. A 6.0/7.99/8.0/9.0 m sweep and a rotated narrow fixture prove a stable boundary and orientation invariance. This is local feasibility evidence, not production layout or Grasshopper parity. | Continue real-footprint GEO-06 work or independent EU-08/EU-09/EU-10 work; production layout, Grasshopper parity, sample groups, and S1-S3 remain pending |

| 2026-08-24T15:14:58Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-06` | `LOCAL_PASS` | `tests\test_eu_reciprocal_surface_audit.py tests\test_eu_floor_partition_audit.py tests\test_eu_dwelling_allocation.py` -> 24 passed in 1.47 s; resolved `tests\test_eu_*.py` list -> 182 passed in 18.77 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo06_reciprocal_party_wall_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo06_reciprocal_party_wall_audit.log` | Reopened local IDF fixture has two party-wall faces and exactly one reciprocal pair. The saved-IDF audit rejects a missing reciprocal back-reference and mismatched vertices. This is local saved-IDF audit evidence, not a European dwelling-stack generator, real-footprint layout, Grasshopper parity, or simulation result. | Continue real-footprint GEO-08/GEO-10 work or independent EU-08/EU-09/EU-10 work; production layout, Grasshopper parity, sample groups, and S1-S3 remain pending |
| 2026-08-24T23:25:00Z | `019ae9f` + dirty-tree caveat | `EU-02 / NS-ACQ-SIDECAR` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_boundary_clip.py tests/test_osm_fetcher.py` -> 65 passed in 2.21 s; evidence: `content/walkthrough_progress_log.csv` | The shared NS-08 manifest writer now records endpoint/licence provenance in `01_source.json` alongside the stable artefacts; Bologna rifter typologies fail closed when unseen. This is local contract evidence only; EU-02 remains in progress until all four live manifests, reconciliation, and final gate evidence are accepted. | Continue shared-schema consolidation and exhaustive Bologna crosswalk evidence |
| 2026-08-25T00:00:00Z | `019ae9f` + dirty-tree caveat | `EU-02 / T01-SHARED-SCHEMA` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_boundary_clip.py tests/test_osm_fetcher.py` -> 65 passed in 2.27 s; evidence: `content/walkthrough_progress_log.csv` | The frozen 23-column validator and three-artifact serializer now have one implementation in `footprint_schema.py`; the OSM compatibility functions delegate to it without changing their public test imports or artifact roles. This is local contract evidence only, not final EU-02 acceptance. | Continue shared geometry/provenance consolidation and Bologna CTC crosswalk evidence |
| 2026-08-25T11:07:33Z | `019ae9f` + dirty-tree caveat | `EU-02 / T06-CTC-CROSSWALK` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_boundary_clip.py tests/test_osm_fetcher.py` -> 66 passed in 2.21 s; evidence: `content/walkthrough_progress_log.csv` | Bologna's CTC reconciliation crosswalk now explicitly covers its official 30-value catalogue: one residential generic label and 29 exclusions, including an empty description; unseen values fail closed. This is local source-contract evidence, not final live-manifest or reconciliation acceptance. | Continue shared geometry/provenance consolidation, then generate and reconcile four live manifests |
| 2026-08-25T11:08:41Z | `019ae9f` + dirty-tree caveat | `EU-02 / T01-PROVENANCE` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_boundary_clip.py tests/test_osm_fetcher.py` -> 66 passed in 2.20 s; evidence: `content/walkthrough_progress_log.csv` | Shared provenance and quality flags now own OSM's generic-tag, feet-only-height, and overlap-resolution cases; compatibility wrappers preserve the OSM import surface. This is local contract evidence only. | Continue final geometry-cleaning consolidation, then generate and reconcile four live manifests |
| 2026-08-25T11:09:51Z | `019ae9f` + dirty-tree caveat | `EU-02 / T01-GEOMETRY` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_boundary_clip.py tests/test_osm_fetcher.py` -> 66 passed in 2.20 s; evidence: `content/walkthrough_progress_log.csv` | OSM now invokes the shared seven-step geometry cleaner with its existing overlap resolver and structured logger passed in, preserving its multipart identifiers, cleaning sequence, and log records. This is local contract evidence only; legacy duplicate cleanup and live acceptance remain outstanding. | Remove unused legacy cleaner, then generate and reconcile four live manifests |
| 2026-08-25T14:17:44Z | `019ae9f` + dirty-tree caveat | `EU-02 / T01-LEGACY-CLEANUP` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_boundary_clip.py tests/test_osm_fetcher.py` -> 66 passed in 2.28 s; evidence: `content/walkthrough_progress_log.csv` | Removed the obsolete duplicate OSM geometry cleaner. The OSM entry point now uses one shared implementation while retaining its OSM-specific overlap resolver and structured logger. This is local contract evidence only; live manifests, reconciliation, and final gate evidence remain outstanding. | Generate and reconcile four live site manifests, then assemble final EU-02 gate evidence |
| 2026-08-25T14:24:08Z | `019ae9f` + dirty-tree caveat | `EU-02 / T03-T06-LIVE-MANIFESTS` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_boundary_clip.py tests/test_osm_fetcher.py` -> 67 passed in 2.27 s; evidence: `openubem/outputs/eu02/` and `content/walkthrough_progress_log.csv` | All four selected sites now have non-empty live clean, residential, excluded, count, and source-sidecar artifacts. Madrid/London agree with recorded residential counts within one building; Lyon/Bologna retain distinct raw-source census and model-ready-clean counts for transparent reconciliation. This is not final NS-02 acceptance. | Write raw-to-clean reconciliation and the Bologna CTC-to-cadastral relation report, then evaluate the gate |
| 2026-08-25T14:25:13Z | `019ae9f` + dirty-tree caveat | `EU-02 / T07-BOLOGNA-RELATION` | `LOCAL_PASS` | Live evidence: `openubem/outputs/eu_evidence/X-11/bologna_live_reconciliation.json` and `bologna_ctc_cadastral_relation.csv` | The relation report records 2,188 CTC residential volumes, 231 dissolved components, 1,312 CTC-touched cadastral objects, 1,372 ruled cadastral objects, 1,330 cadastral residential candidates, and ISTAT 1,010. CTC remains reconciliation-only; `rifter_edif_pl` remains the ruled building source. | Run final four-site artifact and reconciliation gate audit |
| 2026-08-25T14:26:20Z | `019ae9f` + dirty-tree caveat | `EU-02 / T08-NS02-GATE` | `MET` | `openubem/outputs/eu_evidence/X-11/eu02_ns02_gate_audit.json` -> `ns02_contract_met=true` for all four sites | Each selected site has serialized frozen-schema metadata, non-empty clean/residential/excluded/count/source artifacts, a disjoint manifest partition, complete endpoint/licence provenance, and live reconciliation evidence. Raw-source census and model-ready-clean counts remain separately documented where cleaning removes features. | EU-02 acquisition and NS-02 complete; hand off evidence to EU-04 geometry work |

| 2026-08-25T14:38:42Z | `019ae9f` + dirty-tree caveat | `EU-04 / GEO-04-REAL` | `LOCAL_PASS` | `tests\\test_eu_real_footprint_feasibility.py tests\\test_eu_floor_partition_audit.py tests\\test_eu_dwelling_allocation.py tests\\test_eu_reciprocal_surface_audit.py` -> 27 passed in 2.23 s; resolved `tests\\test_eu_*.py` list -> 185 passed in 17.44 s; evidence: `openubem/outputs/eu_evidence/EU-04/real_footprint_feasibility.{csv,summary.json}` | The first real-footprint EU-04 census reads only the four audited model-ready residential manifests and requires projected, finite valid Polygons with unique IDs. It retains per-building manifest SHA-256, width, courtyard, non-convex, and narrow-fallback evidence: 4,186 footprints; 1,848 narrow fallbacks; 388 courtyards; 3,062 non-convex. Every result remains `dwelling_layout_emitted=false`; no typology/dwelling count is inferred. | Build and audit a deterministic real-footprint dwelling/core layout generator; do not count narrow fallbacks as dwelling-level success or claim GEO-08/GEO-10 |

| 2026-08-25T14:54:24Z | `019ae9f` + dirty-tree caveat | `EU-04 / REAL-LAYOUT-01` | `LOCAL_PASS` | `tests\\test_eu_real_footprint_feasibility.py tests\\test_eu_floor_partition_audit.py tests\\test_eu_dwelling_allocation.py tests\\test_eu_reciprocal_surface_audit.py` -> 33 passed in 2.29 s; resolved `tests\\test_eu_*.py` list -> 191 passed in 21.15 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_real_footprint_layout_generator.log` | A deterministic real-footprint strip-partition kernel now emits zones only for explicit caller-provided counts on broad convex no-courtyard Polygons. Count, area/topology, and 2.50 m facade-contact audits pass after rotation-aware readback. Narrow, courtyard, non-convex, and multipolygon inputs fail closed with named reasons. No dwelling count is inferred and no core is emitted. | Establish evidence-backed observed-building mapping and core semantics before using layouts as simulation inputs; do not claim GEO-08/GEO-10 |

| 2026-08-25T14:57:33Z | `019ae9f` + dirty-tree caveat | `EU-04 / OBSERVED-MAPPING-01` | `LOCAL_PASS` | `tests\\test_eu_observed_archetype_mapping.py tests\\test_eu_real_footprint_feasibility.py tests\\test_eu_floor_partition_audit.py tests\\test_eu_dwelling_allocation.py` -> 33 passed in 1.69 s; resolved `tests\\test_eu_*.py` list -> 194 passed in 21.21 s; evidence: `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.{csv,summary.json}` | All 4,186 acquired residential footprints are accounted for by a strict country/tag/year TABULA mapping contract. One observed 1928 London apartment maps to a construction archetype but remains blocked on dwelling count; the other 4,185 are retained as explicit missing-year/type exclusions. No imputation, core, layout promotion, or sample-group claim is made. | Obtain evidence-backed observed construction-year and dwelling-count inputs, or an owner-approved provenance-bearing imputation rule; do not claim GEO-08/GEO-10 |

| 2026-08-25T14:59:08Z | `019ae9f` + dirty-tree caveat | `EU-04 / CORE-01` | `LOCAL_PASS` | `tests\\test_eu_real_footprint_feasibility.py tests\\test_eu_observed_archetype_mapping.py tests\\test_eu_floor_partition_audit.py tests\\test_eu_dwelling_allocation.py` -> 35 passed in 1.69 s; resolved `tests\\test_eu_*.py` list -> 196 passed in 21.05 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_external_core_contract.log` | The D-EU-01 core contract adds exact unconditioned area outside an explicit rectangular conditioned plate, with zero overlap and a shared boundary; rotated fixtures pass and non-rectangular plates fail closed. It is intentionally not applied to observed shells lacking a declared gross-to-conditioned/core relation. | Continue independently runnable IDF extrusion/readback integration; retain the observed construction-year and dwelling-count input block; do not claim GEO-08/GEO-10 |

| 2026-08-25T15:00:54Z | `019ae9f` + dirty-tree caveat | `EU-04 / IDF-READBACK-01` | `LOCAL_PASS` | `tests\\test_eu_reciprocal_surface_audit.py tests\\test_eu_real_footprint_feasibility.py tests\\test_eu_observed_archetype_mapping.py tests\\test_eu_dwelling_allocation.py` -> 23 passed in 3.08 s; resolved `tests\\test_eu_*.py` list -> 197 passed in 19.64 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_layout_idf_readback.log` | A clean explicit-count three-dwelling layout now converts to named zone specs, extrudes, saves, reopens, and produces four party-wall faces in two reciprocal pairs. Fallback layouts cannot reach this converter. This is a controlled fixture, not observed-building or Grasshopper-parity evidence. | Start from this checkpoint if the session changes; retain observed-year/dwelling-count and observed-shell-core blocks; do not claim GEO-08/GEO-10 |

| 2026-08-25T15:52:41Z | `019ae9f` + dirty-tree caveat | `EU-04 / EPLUS-SMOKE-01` | `LOCAL_PASS` | `tests\test_eu_reciprocal_surface_audit.py tests\test_eu_hvac_controls.py tests\test_eu_heating_controls.py tests\test_eu_hvac_sizing.py tests\test_eu_box_generator.py` -> 18 passed in 4.58 s; resolved `tests\test_eu_*.py` list -> 202 passed in 21.01 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_energyplus_design_day_smoke.log` | The first EnergyPlus design-day run of a generated three-dwelling layout aborted with ten duplicate-name severes because every control object was named after the archetype alone, which one building's dwellings share by construction. Per-zone objects are now zone-named, the two constant availability schedules are emitted once per IDF, and repeat calls on one zone fail closed. The fixture now sizes successfully and still passes the reciprocal party-wall audit after readback. This is a controlled fixture sizing run, not an observed-building or annual result. | Keep the observed-year/dwelling-count and observed-shell-core blocks; extend engine smoke coverage to the core-bearing layout before any campaign claim; do not claim GEO-08/GEO-10 |

| 2026-08-25T16:34:43Z | `019ae9f` + dirty-tree caveat | `EU-05 / FRED-RULING-01` | `LOCAL_PASS` | `tests	est_eu_dwelling_allocation.py tests	est_eu_hvac_controls.py` -> 12 passed in 1.57 s; evidence: `openubem/idf/european_controls.py:17`, `tests/test_eu_hvac_controls.py:75` | The owner ruled Option 1 on the France `F_red_temp` analysis request: the field is a strictly positive **source multiplier**, not a bounded reduction factor. `FR.N.AB.10.Gen.ReEx.001.001` now emits its exact `1.0086438144755208` untruncated and the 40-row France registry is no longer fail-closed; non-positive values still raise. The 102 ES/GB/IT occupant rows are unchanged and all remain <= 1.0. The executor's reported `8/8` is a mis-tally -- the file holds 7 tests -- but both ruled behaviours are explicitly covered. | Ruling accepted; the analysis request is `RESOLVED`. This authorizes no France occupant schedule -- `FR-OCC-FUTURE` stands. |

| 2026-08-25T16:34:43Z | `019ae9f` + dirty-tree caveat | `EU-04 / S0-SMOKE-02` | `LOCAL_PASS` | `tests	est_eu_box_generator.py` -> 9 passed in 3.18 s (4 EnergyPlus runs, 0 skipped); resolved `tests	est_eu_*.py` list -> 203 passed in 19.72 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_s0_all_typology_energyplus_smoke.log` | The S0 equivalent-envelope design-day smoke covered the ES SFH fixture alone; it now runs **every S0 typology** (ES SFH, FR TH, ES MFH, ES AB) and additionally asserts the error file carries **no severe diagnostic**, not merely a completion line. The France TH fixture exercises the newly ruled positive-multiplier control path end to end inside the engine. | S0's geometry-and-IDF-construction scope is covered for all four typologies. `GEO-08` stays blocked on the Grasshopper golden export and `GEO-10`/S1-S3 on observed construction year plus per-building dwelling count. |

| 2026-08-25T16:56:39Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-YEAR-DIAG-01` | `DIAGNOSED_BLOCKER` | Owner-authorized live IGN BD TOPO WFS probe of the pinned Lyon bbox; retained-manifest readback; parse reproduction on pandas 3.0.3; evidence: `openubem/outputs/eu_evidence/EU-04/fr_bdtopo_year_availability_diagnosis.json` | Executing the E1 ruling shows the observed construction year **is present in the source** -- **1,115 of 1,663** raw features carry `date_d_apparition` (`1998-01-01Z`, `1820-01-01Z`) -- while the retained residential manifest holds **0 of 530** years, and **529 of 530** French buildings already carry an observed `nombre_de_logements` (median 10, max 83). The loss is a parse defect at `openubem/acquisition/bdtopo_fetcher.py:94`: `pd.to_datetime(..., format="mixed", errors="coerce")` returns `NaT` for every BD TOPO value, because the field is a date with a bare zone suffix and no time part and pre-1677 values fall outside `datetime64[ns]`; `errors="coerce"` discards both failures silently. | `GEO-10`/S1-S3 is blocked by a parse defect, not a missing source. E1 is narrowed, not overturned: no new adapter or source is needed, but the manifest must be rebuilt after the parser is corrected. Measurement pass only -- no fix applied, no manifest rebuilt, no building layout-ready, no S1 group. |

| 2026-08-25T17:20:50Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-PARSE-PROMPT-01` | `EXECUTOR_PROMPT_ISSUED` | Executor prompt authored against the `D-EU-04-E` = E1 ruling; second blocker measured by reading `building_tag` on the retained manifest; evidence: `docs/docs_ACTIVE/europeanLocations/prompts/previous/EXECUTOR_PROMPT_EU-04_fr_year_parse_fix_2026-08-25.md` | The remedy is specified as four tasks with a checkpoint after the third: replace the `bdtopo_fetcher.py:94` expression with an anchored leading-`YYYY` extraction (excluding, never clamping, years below 1000 or after the current year); add a regression fixture in the **real** BD TOPO shape (bare `Z` suffix, a pre-1677 year) plus a retained non-null-rate assertion, proven by restoring the old expression and watching it fail; close the `[OPEN]` debug-reference bullet in place; then re-run the pinned Lyon acquisition -- the single authorized live IGN call -- and regenerate the mapping readiness. **A second, independent French blocker was measured while scoping it:** all 530 retained rows carry `building_tag` `Residentiel` (524) or `Commercial et services` (6), and `OBSERVED_TAG_TO_TABULA_TYPE` (`openubem/semantic/european_archetype_mapping.py:30`) maps only `apartments`, `detached`, `terrace`. | **Recovering the year does not make France layout-ready.** `D-EU-04-E` assumed one missing input; two are missing. The FR TABULA registry holds 40 records across AB/MFH/SFH/TH (10 each) and BD TOPO supplies `nombre_de_logements` and `nombre_d_etages` but no TABULA-compatible type, so a French typology rule is a **new ruling** and the prompt forbids inventing one. No code written, no test run this pass. |
| 2026-08-25T17:31:19Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-YEAR-FIX-01` | `LOCAL_PASS_AUDITED` | Executor ran `T01`-`T04`; **every claim re-verified by the manager against disk**, not taken from the report; evidence: `openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg`, `openubem/outputs/eu_evidence/X-10/fr_manifest_acquisition.json` | `_parse_bdtopo_year` (`openubem/acquisition/bdtopo_fetcher.py:82`) extracts the leading four-digit year with an anchored pattern and returns `pd.NA` outside `[1000, current_year]`, with **no datetime round-trip**. The pinned Lyon re-acquisition ran at 17:27:18Z as the single authorized live IGN call against the same boundary SHA-256. Measured: **522 of 530** observed years where there were **0**, **1550 → 2010**, median **1850**, `IGN_BDTOPO_OBSERVED` on 522 / `IGN_BDTOPO_MISSING` on 8, **four recovered years pre-1677** — precisely the class the old route could not represent. All 522 resolve to a TABULA French period (`FR.01` 458, `FR.02` 9, `FR.03` 7, `FR.05` 5, `FR.06` 9, `FR.07` 28, `FR.08` 4, `FR.09` 2). The `[OPEN]` marker is gone and the `Fix:` clause names the code and both regression tests. `pytest -q` on the two affected files is **12 passed in 2.01 s**. | **Accepted, with two recorded deviations.** (1) `current_year` is a **hardcoded 2026**, so from 2027 the parser silently rejects valid years — correct today, recorded not fixed, since this was an audit pass. (2) The script's exclusion counts (768/530/172/46/20) differ from its `expected_raw_boundary_counts` (891/544/278/46/23) and the executor did not report it; **the two are not the same population** — the expectation is the selection-time raw-boundary census, the script reports post-clean model-ready counts, and `raw_schema_rows` is 1,455 in both this run and the 14:22Z run, so **the live source did not move**. France is still `layout_ready_count = 0`: the 522 rows now fail on `UNMAPPABLE_RESIDENTIAL_TYPE` alone. |
| 2026-08-25T17:31:19Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-TYPOLOGY-REQ-01` | `DECISION_REQUESTED` | Second blocker quantified from the manifest and from the FR TABULA registry; evidence: `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md` | BD TOPO carries **no TABULA-compatible type**: all 530 rows are tagged `Résidentiel` (524) or `Commercial et services` (6), while `OBSERVED_TAG_TO_TABULA_TYPE` maps only `apartments`, `detached`, `terrace`. What the source *does* carry: `nombre_de_logements` (529/530), `nombre_d_etages` (530/530, median 6, max 16), and computed adjacency (**488 attached, 42 free-standing**). **The registry separates the types itself** — `SFH`/`TH` carry `n_apartment` 1 in every period at 1–3 storeys, `MFH` spans 4–12 dwellings at 1–4 storeys, `AB` spans 15–86 dwellings at 5–10 storeys — so the boundary is read off TABULA, not invented. Recommended **G1** requires the dwelling and storey signals to **agree** and excludes the row when they do not: **302 typed of 530**, **297** of them with a recovered year (**7** SFH, **21** TH, **123** MFH, **146** AB); excluded are 189 disagreements, 37 in the registry's own 13–14 dwelling gap, 2 missing a signal. | **Ruling `D-EU-04-G` is required and nothing proceeds without it** — the manager will not invent a typology rule. Two consequences are stated up front rather than discovered later: a derived type must be stamped `DERIVED_BDTOPO_TWO_SIGNAL` and never reported as observed, and **`S3` cannot be typology-balanced for France** because `SFH` caps at **7** in this dense historic quarter. `S1` (12) and `S2` (32) are reachable today under G1. No code written, no rule applied. |
| 2026-08-25T17:42:47Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-TYPOLOGY-RULED-01` | `DECISION_RULED` | Ruling received and recorded; the implementation claim audited against disk; evidence: `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md`, `prompts/EXECUTOR_PROMPT_EU-04_fr_typology_derivation_2026-08-25.md` | **`D-EU-04-G` = G1 is ruled** and both consequences are accepted: a derived type is stamped `DERIVED_BDTOPO_TWO_SIGNAL` and is never reported as observed, and `S3` is not typology-balanced for France (`SFH` caps at **7**). 🔴 **The rule is ruled but not implemented** — `DERIVED_BDTOPO_TWO_SIGNAL` appears in **no `.py` file**, `european_archetype_mapping.py` was last modified at **10:56Z, before the ruling**, and the readiness summary still reports `layout_ready_count 0` with `UNMAPPABLE_RESIDENTIAL_TYPE 522`. The yield figures returned in the execution report (302 typed, 297 dated, 7/21/123/146) are the manager's own measurement from §2 of the decision request, not a run output. | A manager-authored executor prompt now pins the work in four tasks: read `nombre_de_logements` from `surplus_tags` (**no code reads it today**, which is why the mapped London building still stops at `MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT`); compute adjacency in **EPSG:2154** (expect 488 attached / 42 free-standing); apply the derivation **behind** the observed-tag contract, `FR` only; regenerate readiness with separate provenance counters. The acceptance numbers are pinned and a mismatch is a **STOP**, so the rule can never be tuned to reach a count. |
| 2026-08-25T18:11:06Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-TYPOLOGY-IMPL-01` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_eu_observed_archetype_mapping.py` -> 17 passed in 3.19 s; evidence: `openubem/semantic/european_archetype_mapping.py`, `tests/test_eu_observed_archetype_mapping.py` | **T01-T03 implemented and CP-1 reproduces every pinned acceptance number exactly.** `_observed_dwellings` reads `nombre_de_logements` off `surplus_tags`; `compute_footprint_adjacency` reprojects to **EPSG:2154** and gives **488 attached / 42 free-standing**; `derive_bdtopo_building_type` is wired behind `OBSERVED_TAG_TO_TABULA_TYPE`, `FR` only, with a new `type_provenance` field (`OBSERVED_TAG` / `DERIVED_BDTOPO_TWO_SIGNAL`). Measured on the 530 retained French rows: **302 typed**, **297 typed-and-dated** (**7** `SFH`, **21** `TH`, **123** `MFH`, **146** `AB`); exclusions **189** `TYPOLOGY_SIGNALS_DISAGREE`, **37** `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14`, **1** `MISSING_OBSERVED_DWELLING_COUNT`, **1** `MISSING_OBSERVED_STOREY_COUNT`. `ES` (1,194), `GB` (1,242), `IT` (1,220) site counts unchanged. One clarification, not a deviation: `levels` is a non-nullable int with no null marker, and the single missing-storey row is encoded `levels=0`, treated as missing — reproduces the decision document's own count exactly. | T04 explicitly withheld: `openubem/outputs/eu_evidence/EU-04/*.json` was not regenerated; CP-1 counts were measured via `write_eu02_archetype_mapping_readiness` into a pytest `tmp_path`. Await manager audit of CP-1, then dispatch T04 to regenerate the real evidence with `type_provenance_counts` and per-site `derived_type_counts`. |
| 2026-08-25T18:16:04Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-TYPOLOGY-IMPL-01` | `LOCAL_PASS` | `pytest -q tests/test_eu02_fetchers.py tests/test_eu_observed_archetype_mapping.py` -> 17 passed in 3.69 s; `pytest -q tests/test_eu*.py` (full European suite, 28 files) -> 232 passed in 31.53 s; evidence: `openubem/semantic/european_archetype_mapping.py`, `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness_summary.json`, `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.csv` | **T04 done; CP-2 reproduces the target exactly.** Regenerated the readiness evidence over the four live EU-02 manifests after extending the summary with `type_provenance_counts` and a per-site `derived_type_counts` (17 added lines, no existing key removed). `layout_ready_count` rose **0 -> 297**. `type_provenance_counts`: `DERIVED_BDTOPO_TWO_SIGNAL` **302** / `OBSERVED_TAG` **3,884**. `derived_type_counts` for `FR-LYO-HAUTCOEURPENTES`: **7** `SFH`, **21** `TH`, **123** `MFH`, **146** `AB` — matches the pinned target exactly; the other three sites are empty. `reason_counts`: `TYPOLOGY_SIGNALS_DISAGREE` 186 + `MISSING_OBSERVED_YEAR_BUILT;TYPOLOGY_SIGNALS_DISAGREE` 3 = 189, `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` 37, `MISSING_OBSERVED_DWELLING_COUNT` 2 (1 FR + the pre-existing 1 GB), `MISSING_OBSERVED_STOREY_COUNT` 1, `MISSING_OBSERVED_YEAR_BUILT` 1,317, `MISSING_OBSERVED_YEAR_BUILT;UNMAPPABLE_RESIDENTIAL_TYPE` 2,343, empty (mapped) 297. `ES` (1,194), `GB` (1,242), `IT` (1,220) `site_counts` and their per-site `reason`/`mapping_status` breakdowns are **byte-identical** to the pre-change file. No STOP triggered; no error required a debug-reference entry. | `FR-TYPOLOGY-IMPL-01` is complete; next is forming the `S1` sample, which this task explicitly does not do. |
| 2026-08-25T18:34:00Z | `019ae9f` + dirty-tree caveat | `EU-04 / FR-TYPOLOGY-IMPL-01` | `MANAGER_AUDIT` | manager re-ran `pytest -q tests/test_eu02_fetchers.py tests/test_eu_observed_archetype_mapping.py` independently -> 17 passed in 4.00 s; evidence: `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness_summary.json`, `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.csv` | **CP-1 and CP-2 audited against disk and both hold.** Every pinned number is reproduced on the artefacts themselves, not only in the report: `layout_ready_count` **297** where the pre-change file said 0, `derived_type_counts` **7 / 21 / 123 / 146**, `type_provenance_counts` `DERIVED_BDTOPO_TWO_SIGNAL` **302**, exclusions **189 + 37 + 1 + 1 = 228**, `UNMAPPABLE_RESIDENTIAL_TYPE` gone from France, `ES` 1,194 / `GB` 1,242 / `IT` 1,220 unmoved. Only the two named `.py`/test files were touched and the evidence directory was untouched until T04. **The 233-exclusion figure that circulated in an execution report — with "7 sans annee" and "1 sans logement" — is wrong and is superseded by the 228 measured here:** under `G1` a missing year is not an exclusion reason at all, because a typed row with no year is still typed, merely not dated (5 such rows: 1 `MFH`, 4 `AB`). | **FINDING: `type_provenance_counts` counts *rows*, not typed rows.** Of the 3,884 rows stamped `OBSERVED_TAG`, only **1,313** carry a `building_type`; the other 2,571 are typeless rows that never reached any derivation — including all **228** fail-closed French exclusions, which are stamped `OBSERVED_TAG` although they carry no observed type. The fail-closed contract itself holds (all 302 `DERIVED_BDTOPO_TWO_SIGNAL` rows are typed, and no derived row is ever stamped `OBSERVED_TAG`, so no derived type can be quoted as observed), but **the 3,884 must never be quoted as an observed-type total.** Next: form `S1` — 12 French buildings, 3 per typology, drawn from the 297 layout-ready rows. |
| 2026-08-25T18:30:01Z | `019ae9f` + dirty-tree caveat | `EU-04 / S1-SCOPING-01` | `DECISION_REQUESTED` | manager measurement over all 297 French layout-ready rows: `units_per_floor` from `allocate_european_dwellings` on the observed dwelling and storey counts, then `generate_european_dwelling_layout` called on the real footprint; evidence: `openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv`, `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_H_S1_reachability_2026-08-25.md` | 🔴 **`layout_ready` and *layout-generable* are not the same set, and `S1` as specified cannot be formed from buildings that run.** Of the 297 layout-ready French rows the generator emits for only **18**: **0** `SFH`, **1** `TH`, **14** `MFH`, **3** `AB`. **23** fall back (`NARROW_FOOTPRINT_LT_8M` 13, `PARTITION_AUDIT_FAILED` 10) and **256** are refused outright as non-convex or courtyard-holding — which is simply what a dense historic Lyon quarter is. The generator contract (convex, no hole, ≥ 8 m minimum rotated width, ≥ 2.5 m façade contact per dwelling) was ruled under GEO-01/GEO-04/GEO-09 and was **not** touched. No code changed, no test changed: this is a measurement pass. | **Correction to a ruled document.** The sentence "`S1` (12 buildings, 3 per typology) becomes reachable immediately" in `DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md` is **wrong**, was written by this manager, and was load-bearing for the `D-EU-04-G` ruling: clearing three *typed* rows is not clearing three *generable* rows. The `G1` derivation itself is unaffected — 302 typed / 297 dated still stands — and nothing downstream was built on the wrong number because `S1` had not started. **`D-EU-04-H` is OPEN**, recommending **H1**: run the ladder's own 12 (3 per typology, 2 irregular + 1 simple, ordered by `building_id`) and classify every failure, because the ladder's acceptance criterion is *"12/12 accounted for; failures classified"*, not "12/12 succeed" — `H2` would report a clean twelve-for-twelve that is clean only because the twelve were chosen for it. Proposed follow-up, not part of this ruling: `layout_ready` is a misleading field name now that it demonstrably means "mapping inputs complete". |

| 2026-08-25T18:50:00Z | `019ae9f` + dirty-tree caveat | `EU-04 / S1-EXEC-01-CP1` | `STOP_THEN_RULED` | `python scripts/run_eu_s1_smoke.py --dry-run`; evidence: `openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv`, `scripts/run_eu_s1_smoke.py` | T01 built the runner and first ran it under EPSG:2154 as the prompt then specified. 11/12 rows matched §2; row 12 (`BATIMENT0000000240879449_part0`, the only `DWELLING_LAYOUT_EMITTED` row) diverged to `FALLBACK_PENDING_LAYOUT`/`PARTITION_AUDIT_FAILED`. This was diagnosed and **reported as a STOP rather than fixed**: `generate_european_dwelling_layout` rotates about a fixed origin `(0,0)` (`european_residential.py:504`) and Lambert-93 coordinates for this building are ≈850000/6520000 m from that origin, so floating-point noise from the rotation exceeds the partition audit's absolute `topology_tolerance_m2=1e-8` (`:643`); confirmed the same call against the manifest's **native `EPSG:32631`** emits cleanly with `0.0` gap/outside/overlap, matching §2 exactly. | Owner ruled: use native `EPSG:32631`, do not reproject; prompt text and a debug-reference chapter-5 `[OPEN]` entry were updated by the owner directly. Runner edited to load the manifest natively (no `.to_crs` call) and re-run: **all 12/12 Axis A statuses now match §2 exactly** (status and reason, including row 12). Hard rule 5 (do not fix the generator) was honoured — the fragility is recorded, not remedied. | Proceed to T02 (build-and-run smoke) and T03 (manifest) |
| 2026-08-25T19:05:00Z | `019ae9f` + dirty-tree caveat | `EU-04 / S1-EXEC-01-CP2` | `LOCAL_PASS` | `python scripts/run_eu_s1_smoke.py`; `pytest -q tests/test_eu_reciprocal_surface_audit.py tests/test_eu_box_generator.py`; evidence: `openubem/outputs/eu_evidence/EU-04/s1_smoke_manifest.csv`, `openubem/outputs/eu_evidence/EU-04/s1_smoke/*.err` | T02–T03 complete. Axis A: 8 `REFUSED_BY_LAYOUT_CONTRACT`/`NON_CONVEX_FOOTPRINT`, 3 `FALLBACK_PENDING_LAYOUT`/`NARROW_FOOTPRINT_LT_8M`, 1 `DWELLING_LAYOUT_EMITTED` (row 12) — 12/12 matching §2. Axis B (all 12 attempted): **11 `EPLUS_COMPLETED`** (10 `FALLBACK_ONE_ZONE_PER_FLOOR` + row 12 `EUROPEAN_DWELLING_LAYOUT`), **1 `EPLUS_FATAL`** (`BATIMENT0000000240877527_part0`, AB, `FALLBACK_ONE_ZONE_PER_FLOOR`, 5 zones) — its real footprint has 173 exterior vertices, so the extruded `BuildingSurface:Detailed` exceeds the IDD's ~120-vertex field limit and E+ fails input processing (`** Fatal ** Errors occurred on processing input file`) — a named, reproducible refusal per the S1 ladder criterion, not an energy result. Row 12 party-wall audit: `passed=True`, `party_face_count=8`, `reciprocal_pair_count=4`. 0/12 rows carry `has_courtyard=true`, so 0 rows carry the courtyard-fill note. | A real bug was hit and fixed **in the runner itself** (not the generator, not `zoning.py`): `tmp_root` was a relative `Path`, so `subprocess.run`'s `cwd=` switch made `energyplus.exe` resolve the already-relative `idf_path` a second time against the new `cwd` (`tmp/tmp/<id>.idf`, `ERROR: Could not find input data file`); fixed with `.resolve()` on `tmp_root`; registered in `OpenUBEM_debug_References.md` ch.13. `pytest -q tests/test_eu_reciprocal_surface_audit.py tests/test_eu_box_generator.py` → 14 passed in 4.75 s. No blocker: S1 ladder acceptance (12/12 accounted for, failures classified) is met. | EU-04 S1 (Option H1) is complete; next is forming S2/S3 or acting on the `EPLUS_FATAL` vertex-limit finding as a separate, explicitly scoped item |
| 2026-08-25T19:20:00Z | `019ae9f` + dirty-tree caveat | `EU-04 / S1-EXEC-01-AUDIT` | `MANAGER_AUDIT` | manager read of the artefacts, not of the report: `s1_smoke_manifest.csv` re-tallied, `european_residential.py:504`/`:643` re-read, `git status --porcelain` checked for unplanned edits; evidence: `openubem/outputs/eu_evidence/EU-04/s1_smoke_manifest.csv`, `.../s1_smoke/*.err` (12), `scripts/run_eu_s1_smoke.py` | **CP-2 reproduces on disk.** Axis A: 8 `REFUSED_BY_LAYOUT_CONTRACT`/`NON_CONVEX_FOOTPRINT`, 3 `FALLBACK_PENDING_LAYOUT`/`NARROW_FOOTPRINT_LT_8M`, 1 `DWELLING_LAYOUT_EMITTED` — 3 buildings per typology, 8 non-convex, 0 courtyard. Axis B: 10 `EPLUS_COMPLETED`/`FALLBACK_ONE_ZONE_PER_FLOOR` + 1 `EPLUS_COMPLETED`/`EUROPEAN_DWELLING_LAYOUT` + 1 `EPLUS_FATAL`. **The generator was not modified** — `:504` still rotates about `origin=(0.0, 0.0)`, `:643` still declares `topology_tolerance_m2 = 1e-8`, and `scripts/run_eu_s1_smoke.py` is the only file written. Row 12 carries both the `CRS_NATIVE_32631_REQUIRED_SEE_DEBUGREF_CH5` note and the party-wall triple. The `EPLUS_FATAL` had **not** been registered; the manager registered it in ch.1 of `OpenUBEM_debug_References.md`. | 🔴 **New finding, reported by neither side: the single dwelling-level EnergyPlus model is one floor plate of 5 dwellings, not the 6-storey / 28-dwelling stack.** `scripts/run_eu_s1_smoke.py:257` hands the layout to `european_layout_to_zone_specs` at `height_m = 3.0`, giving `zone_count = units_per_floor = 5`, while the 11 fallback rows go through `build_zones(num_floors=observed_storeys)` and are full stacks. **The two axes are not comparable in vertical extent**, and the dwelling-level path must never be quoted as "a 6-storey dwelling-partitioned building runs". This is a limit of the manager's own prompt, not an executor deviation, and it is recorded rather than fixed because `S1` is a measurement task. `S1` ladder acceptance stands: 12/12 accounted for, failures classified, no energy number produced. | Scope `S2`/`S3` (`S3` cannot be typology-balanced for France — `SFH` caps at 7); open the vertex-budget simplification and the rotation-origin / relative-tolerance fix as separate, explicitly scoped items |

| 2026-08-25T19:36:37Z | `019ae9f` + dirty-tree caveat | `EU-04 / EPLUS-SMOKE-02` | `LOCAL_PASS` | `tests\\test_eu_reciprocal_surface_audit.py tests\\test_eu_hvac_controls.py` -> 13 passed in 3.37 s; resolved `tests/test_eu_*.py` list -> 209 passed in 20.29 s; evidence: `openubem/outputs/eu_evidence/EU-04/targeted_layout_energyplus_smoke.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_layout_energyplus_smoke.log` | Controlled three-dwelling layout-to-IDF-to-EnergyPlus design-day smoke passes with unique per-zone ventilation, gains, and thermostat objects; shared availability schedules are emitted once per IDF and duplicate-name severes are absent. This is a controlled explicit-count fixture, not observed-building or annual evidence. | Begin at the S1 audit checkpoint; scope S2 by measuring corpus yield before promising it and preserve observed-input, native-CRS, vertex-limit, GEO-08, and S2/S3 boundaries |

| 2026-08-25T19:42:50Z | `019ae9f` + dirty-tree caveat | `EU-04 / S2-SCOPING-01` | `DIAGNOSED_NOT_FORMABLE` | `python scripts/scope_eu_s2.py`; evidence: `openubem/outputs/eu_evidence/EU-04/s2_scope_measurement.csv`, `s2_scope_summary.json`, `s2_scope_measurement.log` | The complete 4,186-row retained corpus was measured before selection. Under 2 rows per type × old/new age band × high/low mapping-input completeness cell, S2's 32-case target is not formable: 297 rows are high-completeness typed/year inputs and no complete low-completeness typed/age cells exist. Re-applying the layout contract to those 297 yields 18 emitted layouts and 279 explicit fallbacks (200 non-convex, 58 narrow, 11 courtyard, 10 partition-audit). No outcome-balanced sample, threshold relaxation, or EnergyPlus run was made. | Keep S2 unformed; obtain an owner-approved revised ladder or open separate geometry/data-completeness work. Never quote the 18 emitting rows as S2 |

| 2026-08-25T19:45:04Z | `019ae9f` + dirty-tree caveat | `EU-04 / S2-GEOMETRY-DIAG-01` | `DIAGNOSTIC_FINDING` | `python scripts/diagnose_eu_s2_geometry_limits.py`; evidence: `openubem/outputs/eu_evidence/EU-04/s2_geometry_limits_diagnostic.csv`, `s2_geometry_limits_diagnostic_summary.json`, `s2_geometry_limits_diagnostic.log` | Across all 297 mapping-ready Lyon rows, native layout emission is 18; centroid-translated sensitivity emission is 28, with exactly 10 native `PARTITION_AUDIT_FAILED` rows changing status. One footprint has 173 exterior vertices, above the approximate ~120 EnergyPlus IDD field budget. No generator, manifest, threshold, or EnergyPlus input was changed. | Open rotation-origin/tolerance and vertex-budget remedies as separate scoped work; keep S2 unformed and do not quote the 28 sensitivity results as production layouts |
| 2026-08-25T19:55:21Z | `019ae9f` + dirty-tree caveat | `EU-04 / S2-GEOMETRY-REMEDY-SCOPE-01` | `DECISION_REQUIRED` | `openubem/outputs/eu_evidence/EU-04/s2_geometry_remedy_decision_note.md` | Ten coordinate-sensitive IDs and the single 173-vertex ID are enumerated. Coordinate/tolerance and vertex-budget remedies are separate owner decisions; no production change was made. | Obtain owner rulings before implementation; S2 remains diagnosed but not formable |
| 2026-08-25T19:58:00Z | `019ae9f` + dirty-tree caveat | `EU-04 / S2-GEOMETRY-DECISION-REQUEST-01` | `OPEN_OWNER_RULING` | `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_S2_geometry_remedies_2026-08-25.md` | Prepared direct-response ruling form: `D-EU-04-S2-G` (G1/G2/G3) and `D-EU-04-S2-V` (V1/V2), with explicit no-implementation boundary. | Obtain both owner values, then execute only the ruled remedy and re-measure S2 |
| 2026-08-25T20:10:00Z | `019ae9f` + dirty-tree caveat | `EU-04 / S2-GEOMETRY-REMEDY-EXEC-01` | `RULED_AND_IMPLEMENTED` | `pytest -q tests/test_eu_s2_geometry_remedies.py tests/test_eu_floor_partition_audit.py tests/test_eu_real_footprint_feasibility.py`; `scripts/diagnose_eu_s2_geometry_limits.py`; `scripts/run_eu_s1_smoke.py` | G1 centroid-relative rotation/tolerance and V1 bounded simplification implemented. Focused tests: 29 passed. Re-measurement: 28 native layouts, zero translation-status changes, one simplification (max Δarea 0.0146008 m²; Hausdorff 0.0170423 m). S1 smoke: 12/12 EPLUS_COMPLETED, including the former 173-vertex failure. | Re-measure S2 ladder; do not claim S2 formed because completeness cells remain absent |
| 2026-08-25T20:10:32Z | `4a9fce2` + dirty-tree caveat | `EU-04 / S2-POST-REMEDY-MEASURE-01` | `MEASURED_NOT_FORMABLE` | `scripts/scope_eu_s2.py` | Manifest remains 4,186 rows; 297 mapping-ready; 28 layout-emitting; 269 fail-closed fallbacks (200 non-convex, 58 narrow, 11 courtyard). The 32-cell S2 ladder remains not formable because required completeness strata are absent; no sample selected. | Resolve missing completeness strata or obtain an owner ruling before any S2 sample claim |
| 2026-08-25T20:44:08Z | `4a9fce2` + dirty-tree caveat | `EU-04 / S2-COMPLETENESS-DECISION-REQUEST-01` | `OPEN_OWNER_RULING` | `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_S2_completeness_ladder_2026-08-25.md` | Prepared `D-EU-04-S2-C` with C1/C2/C3. Recommended C1 retains a deterministic 32-row high-completeness operational sample: eight rows per type and four old/four new where the corpus permits, with the measured SFH exception of one new/seven old. Geometry outcome and fallback reason stay independent columns; low completeness remains a census finding, not a simulation stratum. | Await an explicit owner value; do not form or simulate S2 |
| 2026-08-25T20:53:42Z | `4a9fce2` + dirty-tree caveat | `EU-04 / S2-C1-PREFLIGHT-01` | `STOPPED_NOT_FORMABLE` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_s2_c1_sample.py tests\\test_eu_s2_geometry_remedies.py tests\\test_eu_floor_partition_audit.py` | The ruled C1 selector stopped before writing a manifest: the retained high-completeness SFH stock is seven (six old, one new), not the required eight. It refused to duplicate a building, use an incomplete row, change another quota, or inspect geometry/simulation outcomes. Focused tests: 21 passed. | Owner must amend C1 to a 31-row sample or state an explicit non-outcome-based type-quota change |
| 2026-08-25T20:56:16Z | `4a9fce2` + dirty-tree caveat | `EU-04 / S2-C1A-FORM-01` | `LOCAL_PASS` | `.venv\\Scripts\\python.exe -m pytest -q tests\\test_eu_s2_c1_sample.py tests\\test_eu_s2_geometry_remedies.py tests\\test_eu_floor_partition_audit.py`; `.venv\\Scripts\\python.exe scripts\\form_eu_s2_c1_sample.py` | Owner-authorized C1A forms a deterministic 31-row high-completeness operational sample: AB/MFH/TH = 8 each (4 old/4 new); SFH = 7 (6 old/1 new). All rows are mapping-ready. The manifest retains independent geometry columns: 5 `DWELLING_LAYOUT_EMITTED`, 26 `FALLBACK_PENDING_LAYOUT`. Focused tests: 21 passed. No simulation ran. | Audit the frozen C1A manifest, then scope a separate short-period simulation slice |
| 2026-08-25T20:57:22Z | `4a9fce2` + dirty-tree caveat | `EU-04 / S2-C1A-AUDIT-01` | `MANAGER_AUDIT` | C1A manifest/summary readback; `openubem/data/weather/weather_registry.json` | Independent readback confirms 31 unique high-completeness rows, the 8/8/8/7 quotas, independent geometry-result columns, and source-census SHA-256 equality. The short-period simulation is not locally runnable: the weather registry is `RULED_NOT_PINNED` / `BLOCKED_NO_CDS_CREDENTIALS` and has no approved Lyon window. No simulation or energy result is claimed. | Obtain approved/pinned Lyon weather plus CDS access, then scope the short-period simulation runner |
| 2026-08-25T21:23:32Z | `4a9fce2` + dirty-tree caveat | `EU-07 / ONEBUILDING-LYO-CANDIDATE-01` | `DECISION_REQUIRED` | `openubem/data/weather/candidates/onebuilding_lyon_bron_tmyx_2011_2025/`; `debugs/docs/DECISION_REQUEST_EU-07_onebuilding_lyon_bron_candidate_2026-08-25.md` | User-directed download acquired the Lyon–Bron 2011–2025 TMYx EPW. It has a valid header, 8,760 rows, and required fields, but is an NCEI ISD/ERA5 TMY composite—not continuous actual weather—and fails the existing 5 W/m² solar-closure gate (3,389 daytime rows; max 132.834 W/m²). The direct CDS/ERA5 registry was not changed and no simulation ran. | Owner must choose candidate-only, a separate TMYx evaluation track, or a source-method replacement |

| 2026-08-25T21:39:23Z | `4a9fce2` + dirty-tree caveat | `EU-07 / OB1-EXECUTION-PREFLIGHT-01` | `BLOCKED_EXTERNAL_INPUTS` | `openubem/acquisition/european_weather.py`; `openubem/data/weather/weather_registry.json`; `debugs/docs/DECISION_REQUEST_EU-07_onebuilding_lyon_bron_candidate_2026-08-25.md` | `D-EU-07-OB-LYO = OB1` is ruled: the TMYx file stays candidate-only and cannot be promoted or used for S2. A read-only credential check returned `CDS_CREDENTIALS_CONFIGURED=FALSE`. The approved registry remains the unmodified Madrid/London/Bologna template, with no France/Lyon target or pinned twelve-month weather window. No S2 simulation or energy result was produced. | Provide project-owned CDS access and rule/pin a direct-ERA5 Lyon station plus twelve-month window before weather acquisition or runner scoping |

| 2026-08-25T22:27:26Z | `4a9fce2` + dirty-tree caveat | `EU-07 / CDS-ERA5-LYON-ACCESS-01` | `BLOCKED_EXTERNAL_LICENCE` | CDS API retrieval of `reanalysis-era5-single-levels`; `openubem/outputs/eu_evidence/EU-07/cds_era5_licence_gate_2026-08-25.txt` | The supplied project credential is installed without being printed and the configuration check returns `TRUE`. A live request for the Lyon--Bron reference point (45.72 N, 4.95 E) is rejected with `403 required licences not accepted`; no raw weather file, registry update, or S2 simulation was produced. | Sign in to CDS and accept the licence for `reanalysis-era5-single-levels`, then rerun the explicit 2023 Lyon acquisition |

| 2026-08-26T00:02:11Z | `4a9fce2` + dirty-tree caveat | `EU-07 / CDS-ERA5-LYON-ACQUISITION-01` | `ACQUISITION_IN_PROGRESS` | `scripts/acquire_era5_lyon_bron_2023.py --submit/--poll`; `openubem/data/weather/raw/era5_lyon_bron_2023/` | CDS licence access is confirmed. Boundary day plus January, February, March, and December archives are acquired; April is `running`. The remaining months are submitted one at a time because concurrent CDS jobs were rejected. The converter compiles and loads the real January NetCDF payload (744 rows, all nine variables); no EPW or simulation is claimed until all 13 archives exist. | Continue polling April, submit May--November sequentially, then run the converter and DR08 gates |
| 2026-08-26T(current) | dirty-tree caveat | `EU-07 / CDS-ERA5-LYON-COMPLETE-01` | `ACQUIRED_CONVERTED_GATES_1_4_PASS` | `scripts/acquire_era5_lyon_bron_2023.py`; `scripts/convert_era5_lyon_bron_2023_to_epw.py`; `openubem/data/weather/fr_lyon_bron_2023_era5.epw` | All 13 ERA5 archives are present. The 2023 EPW is generated with SHA-256 `2cf15311b9c6d1124f856d80e6deed5e4a7d6f48389681305b90b6dbee88cc2c`. DR08 gates 1--4 pass; gates 5--6 remain pending for the external monthly national benchmark and EnergyPlus smoke. | Produce benchmark and EnergyPlus evidence; then decide registry promotion and scope S2 execution |
| 2026-08-26T(current+1) | dirty-tree caveat | `EU-07 / WEATHER-GATES-01` | `GATE_6_PASS_GATE_5_PARTIAL` | `openubem/outputs/eu_evidence/EU-07/era5_lyon_bron_weather_gates_2026-08-26.md` | EnergyPlus 23.1 smoke with the Lyon EPW returns 0 with 0 severe errors. Lyon-Bron station monthly temperatures are within 1.25 K of ERA5, but the station source lacks monthly GHI; sunshine hours are not accepted as a GHI substitute. | Obtain authoritative monthly GHI or obtain an explicit owner ruling; keep registry and S2 held |

| 2026-08-26T11:40:00Z | `4a9fce2` + dirty-tree caveat | `EU-04 / T02-S2-PHYSICS-COMPLETE-CAMPAIGN` | `COMPLETED_CP-A_SIGNED` | `scripts/run_eu_s2_campaign.py`; `openubem/outputs/eu_evidence/EU-04/s2_campaign_manifest.csv`; `openubem/outputs/eu_evidence/EU-04/s2_campaign/` | The first real European energy numbers in the arc. All 31 frozen C1A buildings ran under EnergyPlus 23.1 on the pinned Lyon 2023 EPW at `f = 0`: return code 0, 0 severe and 0 fatal errors for every building, 148.6 s of engine time. Heating EUI is 4.93 min / 65.21 median / 149.43 max kWh/m2, area-pooled 31.21 kWh/m2 over 19,823.6173 m2 (denominator corrected at T05; the 15,989 m2 first stated here was a reporting error — the pooled ratio itself was already right). The EPW SHA-256 and the source-census SHA-256 are recomputed and asserted before every run, and `_add_smoke_construction` appears nowhere in the runner. **FINDING EU-S2-01:** only 5 of 31 emitted a dwelling layout; 26 fell back to a massing box although all 31 were selected as `MAPPED_LAYOUT_READY` and high-completeness. Mapping readiness does not predict layout success, so 26 of the 31 EUIs are geometry-limited. No value here is a fleet figure. | Manager signed CP-A; T03 released to emit the 31 section 9.6-conformant campaign-cell manifests at `f = 0` |

| 2026-08-26T12:00:00Z | `4a9fce2` + dirty-tree caveat | `EU-08 / T03-S2-CELL-MANIFESTS` | `COMPLETED` | ad hoc manifest emission reusing `dependency_fingerprints`/`sha256_file`; `pytest -q tests/test_eu_s2_campaign.py tests/test_eu_s2_c1_sample.py tests/test_eu_campaign_manifest.py` | `openubem/outputs/eu_evidence/EU-08/s2_cell_manifests/` (31 files) | 31/31 §9.6-conformant campaign-cell manifests emitted at `f = 0` for the S2 real-building run: `schema_version = step8-cell-manifest/1.0`, 31 unique `cell_id` (`building_id` inserted into the grammar since only 14 distinct TABULA archetypes exist across the 31 buildings), no required key null, every `*_sha256` recomputed from the file on disk. `build_campaign_cells`/`validate_campaign_cells` could not be called literally — they are bound to the 510-row/102-archetype ES/GB/IT occupant matrix and would either raise or synthesize `f>0` cells; `dependency_fingerprints`/`dependency_digest` were reused exactly as specified. Focused tests: 22 passed. | T04: run the implemented Step 8 gates over the S2 outputs and record vacuity honestly |

| 2026-08-26T12:20:00Z | `4a9fce2` + dirty-tree caveat | `EU-09 / T04-S2-STEP8-GATES` | `COMPLETED_1PASS_2FAIL_14VACUOUS` | ad hoc gate scoring reusing `openubem.validation.step8_gates` unmodified; `pytest -q tests/test_eu_step8_*.py` | `openubem/outputs/eu_evidence/EU-09/s2_gate_report.json` | All 17 `G8.*` gates from the test suite scored, none omitted. `G8.12` PASS (103/103 real saved Schedule:File checksum/path + assignment). `G8.13` FAIL: 0/103 by the coded check although every real object literally reads `Interpolate to Timestep = No` — 🔴 new `[OPEN]` finding, a genuine gate-scorer index bug (`step8_gates.py:497` reads the wrong positional field against the real 10-field object), registered in the debug references, not a physics/geometry defect. `G8.15` FAIL: untriaged warning kinds, no approved list has been ruled for this arc (severe/fatal remain 0/31). 14 gates VACUOUS, each with its exact empty/single-valued population recorded: no `f>0` cells, no dependency-digest cache implemented for S2, no LOCO held-out fold assigned, no cell re-run, no independent comparison series, no as-modelled EUI band, no `Output:Meter` requested. No gate was weakened. Focused tests: 25 passed, unmodified. | T05 CP-B: results accounting and evidence bundle for S2 |

| 2026-08-26T12:45:00Z | `4a9fce2` + dirty-tree caveat | `EU-10 / T05-S2-DOSSIER-CPB` | `COMPLETED_CP-B_REPORTED` | ad hoc manual dossier assembly; `pytest -q tests/test_eu_results_accounting.py` | `openubem/outputs/eu_evidence/EU-10/s2_dossier/s2_dossier.json` | 🔴 `build_european_dossier_report`/`export_european_result_bundle` could not run on the real S2 evidence: only heating was simulated (all four end uses are required; confirmed `ValueError` on a real `eplusout.csv`), and only 1 of 17 gates in the real T04 report is `passed=True` (all 17 are required). The dossier was assembled manually against the same descriptive contract. Headline heating-only area-pooled EUI **31.2144 kWh/m²** over **19,823.6173 m²** (31 buildings) — 🔴 corrects the CP-A log's stated "15,989 m²" denominator (the pooled ratio itself, 31.21, was already right). By geometry outcome: `DWELLING_LAYOUT_EMITTED` pools to 85.09 kWh/m² over 1,197.86 m²; `FALLBACK_PENDING_LAYOUT` pools to 27.75 kWh/m² over 18,625.76 m² — FINDING EU-S2-01's caveat is not cosmetic. Weather year 2023 and the November GHI exception are named wherever a number appears; no DHW reconstruction is layered on an incomplete simulated base; the dossier states explicitly that no value in it is a verified fleet figure. Focused tests: 10 passed, unmodified. | CP-B reported to the manager; awaiting readback before any further task |

| 2026-08-26T13:10:00Z | `4a9fce2` + dirty-tree caveat | `X-04 / T07-R3-FIXTURE-DISPOSITION` | `COMPLETED_OUTCOME_B` | `pytest -q tests/test_eu_physics_energyplus.py tests/test_eu_physics_primitives.py` -> 11 passed in 2.95 s; evidence: `openubem/idf/european_physics.py:145-154`, `tests/test_eu_physics_energyplus.py`, `tests/test_eu_physics_primitives.py`, `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` | **Outcome (b): the fixture's inputs were wrong, not the implementation** -- already fixed and un-xfailed prior to this task; T07 re-derives and confirms it rather than changing code. Root cause of the old 19.998714 C reading: `_r3_idf()` formerly set an artificial inside convection coefficient `h_in = 1e7 W/(m2 K)`, which locked EnergyPlus's partitioned zone heat-balance solver (decay clamped to ~1e-7 fraction per timestep) -- a numerical artifact, not real physics. Re-derived the DR11 SS4 target directly from the pinned functions: `r3_time_constant_hours(1.62e7, 320.0)` = 14.0625 h, `r3_free_float_temperature_celsius(20.0, 0.0, 14.0625, 1.62e7, 320.0)` = 7.357588823 C, matching the cited 7.357589 C target to six decimals -- DR11's target is reproducible, ruling out outcome (c). With the h_in override removed (current fixture, natural/TARP convection only), the free-float trajectory is physically continuous: re-measured this pass at T(14.04h) = 3.6036 C, T(24h) = 1.5914 C, both inside the test's asserted physical-continuity bounds (2.0-5.0, 0.5-3.0). The distributed CTF/TARP trajectory does not reduce to the single-node analytic exponential exactly (3.60 C measured vs 7.36 C analytic at the same elapsed time), accepted as expected physics of a multi-node model versus the lumped-RC reference, not a defect. No `xfail` remains in either test file: 11 passed, 0 failed, 0 xfailed, 0 skipped. The stale debug-reference bullet claiming the strict `xfail` is "retained ... pending reconciliation" was extended in place with this disposition. | T08/CP-C: freeze the boundary and write the closure record (blocked on T06) |

| 2026-08-26T12:45:00Z | `4a9fce2` + dirty-tree caveat | `EU-09 / EU-10 / D-EU-13-G8.13-SCORER-INDEX` | `RULED_A_IMPLEMENTED_AUDITED` | `pytest -q tests/test_eu_step8_*.py` -> 25 passed; evidence: `openubem/validation/step8_gates.py:482,497`, `tests/test_eu_step8_saved_idf_gates.py`, `openubem/outputs/eu_evidence/EU-09/s2_gate_report.json`, `openubem/outputs/eu_evidence/EU-10/s2_dossier/s2_dossier.json`, `docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md` §12 | **Owner ruled (a): fix the index before freezing.** G8.13 had reported `FAIL` 0/103 because `evaluate_saved_idf_schedule_gates` read `Schedule:File` field 6 (`Column Separator` = `Comma`) instead of field 7 (`Interpolate to Timestep` = `No`); the membership guard `len(fields) >= 7` was off by the same one. Fixed externally and **audited here against artefacts, not against the report**: guard now `>= 8`, read now `[7]`, unit fixture widened to a real ten-field object, `[OPEN]` removed from the debug references, 25/25 Step 8 gate tests pass, and `git status` shows no unrelated production file touched. **The director did not take the new PASS on trust** - an independent parse of all 31 retained S2 IDFs, written outside the gate code, finds 103 `Schedule:File` objects, every one ten fields long, field 7 = `No` in **103 of 103**, zero violations. Nothing was re-run, re-emitted or altered: this is a **scorer restatement, not a physics change**. **Stale artefact found and repaired:** `EU-10/s2_dossier.json` still quoted `1 PASS / 2 FAIL` in two places and would have contradicted the gate report inside the frozen contract; both corrected, the superseded summary preserved verbatim in a `restated_note`, and a `restatements` block added carrying the ruling id, cause, fix location and the director's verification. Headline figures untouched and re-checked: n=31, 618,782.3181 kWh, 19,823.6173 m2, **31.2144 kWh/m2**. S2 gate result is now **2 PASS (G8.12, G8.13) / 1 FAIL (G8.15) / 14 VACUOUS**; FINDING EU-S2-02 closed; G8.15 still travels into the T08 caveat list. On owner instruction the authoritative closure record now lives in `MVP_european_locations.md` **§12 (Tables 22-26)**, which governs over the working plan doc. | T06: convert ES/GB/IT to EPW and run the six DR08 gates (blocked on the ERA5 acquisition, Madrid 12 of 25) |

| 2026-08-26T13:20:00Z | `4a9fce2` + dirty-tree caveat | `EU-07 / EU-09 / EU-10 / T06-T08-MACHINERY-BUILD` | `BUILT_AND_AUDITED` | `pytest -q` over the six touched EU files -> **35 passed**; full suite **2,178 passed / 55 skipped**; evidence: `scripts/freeze_eu_campaign_cell_spec.py`, `scripts/convert_era5_eu_folds_to_epw.py`, `scripts/run_eu_t06_weather_promotion.py`, `openubem/acquisition/european_weather.py`, `openubem/data/campaign/`, `openubem/data/weather/benchmarks/`, `docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md` §12 | **The whole remaining T06/T08 machinery was built while the ERA5 acquisition ran, then audited against artefacts rather than reports.** The freeze script consumes the already-validated `european_campaign.py` and never re-implements it; it **refuses** to write a spec while any fold is unpinned and **hard-fails if the caveat register is missing, wrong-schema, self-inconsistent or short** — a contract cannot be written without its caveats. The DRAFT was independently re-validated: 510 cells, 510 unique ids, `validate_campaign_cells` accepts, four weather fields per cell, every path repo-relative. DR08 **gates 5 and 6 existed only as `PENDING_*` placeholders and are now code**: gate 5's 10 % tolerance is quoted verbatim from the Lyon decision request and its benchmark is always a local file; gate 6 runs real EnergyPlus 23.1 and returns `UNAVAILABLE_ENERGYPLUS` rather than a pass when the engine is absent — the real control against the pinned France EPW returns **PASS, rc 0, 0 severe, 1.19 s**. The orchestrator is dry-run by default and left the registry **SHA-256 byte-identical** across a live run. 🔴 **FINDING EU-S2-03** — `diary_window` is `None` and `RULED_NOT_PINNED` for es/uk/it, so **no fold outside France can be tied to a weather year**; the converter's first version silently defaulted to the window's first year and the director rejected that default, so it now prints `YEAR_NOT_RULED` and refuses, with `--all-years` emitting both candidates. 🔴 **FINDING EU-S2-04** — **gate 5 has no benchmark data for es/uk/it**; six fold-year files are required and none existed, so **finishing the download is not sufficient to pin any fold**. The France benchmark had never been stored as data at all and was materialised from the ruling's own evidence document without re-querying a value. A five-minute test file was traced — after one wrong attribution to a `git` subprocess, cleared by measuring it at 0.085 s — to **pytest's assertion rewriter carrying a 340 KB string through 28 membership assertions**; now **9 passed in 1.02 s**, and the fix exposed a second defect where the path guard fired on `EPSG:32631`. Caveat register grew **16 → 18** under its own add-never-remove rule. The registry's false `BLOCKED_NO_CDS_CREDENTIALS` was corrected, and four undeclared dependencies were added to `pyproject.toml`. | T06 execution once the 75 archives land **and** the six gate-5 benchmarks are acquired; then T08 freeze and CP-C |
| 2026-08-26T14:10:00Z | `4a9fce2` + dirty-tree caveat | `EU-07 / T06-GATE5-BENCHMARK-ACQUISITION` | `BLOCKER_RESOLVED` | `pytest -q tests/test_eu_gate5_benchmarks.py` **18 passed**, with the six other EU files **53 passed**; evidence: `scripts/acquire_pvgis_monthly_ghi_benchmarks.py`, `openubem/data/weather/benchmarks/*.json`, `tests/test_eu_gate5_benchmarks.py`, `docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md` §12.12c | **FINDING EU-S2-04 is closed: the six missing DR08 gate-5 benchmarks now exist.** They were acquired from PVGIS MRcalc v5_3 at coordinates read **verbatim from the registry** rather than re-typed, for candidate years taken from the registry's own `raw_era5_window`, and stored **exactly as returned** — not rounded, not re-ordered, not interpolated — each file carrying its endpoint, station and retrieval date so gate 5 can be re-run offline for the life of the contract: `es` 2009 **1797.48** / 2010 **1744.12**, `uk` 2014 **1125.40** / 2015 **1089.53**, `it` 2013 **1404.50** / 2014 **1412.61** kWh/m² annual. Both candidate years of every fold were acquired and **neither was chosen** — acquiring a benchmark is not a diary ruling, so C-17 stands untouched. The script **refuses the France fold** with `RULED_TRANSCRIBED_BENCHMARK_NOT_REQUERIED`: the `RULED_PINNED_EXCEPTION` was granted against twelve specific numbers, and a re-query could silently replace them under the same provenance label. Filenames follow the orchestrator's own `<fold>_<year>_monthly_ghi_benchmark.json` convention, so `--benchmark-dir` resolves them with no configuration. **Caveat C-18 was amended, not retired** — the register's rule is add-never-remove — and now records both the gap and its closure, because what it measures is not "a file was missing" but "a gate's data dependency was invisible until the gate was built". A latent test defect surfaced in the same pass: `test_caveats_register_happy_path` compared an emitted path to `tmp_path.as_posix()` while the freezer emits repo-relative POSIX and pytest's basetemp sits **inside** the repo; re-pointed at the freezer's own `_repo_relative_posix` helper and registered in the debug references. DRAFT spec regenerated and independently re-validated: **510 510 18 DRAFT_WEATHER_NOT_PINNED**. Runbook step 2b rewritten from *acquire* to *verify, do not re-acquire*, and the freeze expectation corrected from 17 to 18 caveats. **What is still open:** gate 5 has two inputs and only one arrived — no fold outside France has an EPW or a ruled year, so the blocker moved from two items to one. | T06 execution once the 75 archives land; then T08 freeze and CP-C |

| 2026-08-26T15:05:00Z | `4a9fce2` + dirty-tree caveat | `EU-07 / EU-09 / D-EU-14-RULED-B-AND-T06-ES-PREPARATION` | `RULED_B_EXECUTED_NEW_DECISION_OPEN` | `run_eu_t06_weather_promotion.py --fold es --dry-run`; `pytest -q tests/test_eu_t06_weather_promotion.py tests/test_eu_gate5_benchmarks.py` -> **24 passed**; evidence: `EU-07/t06_es_2009_six_gates.json`, `EU-07/t06_es_2010_six_gates.json`, `es_madrid_2009_2010_y{2009,2010}.epw`, MVP §12.12e/§12.14/§12.15 | Owner ruled D-EU-14 **(b)**: hold the DRAFT at `DRAFT_WEATHER_NOT_PINNED` and gate **both** candidate years of every fold. Preceded by 🔴 **FINDING EU-S2-05** (C-19): France is not a campaign fold, so a partial freeze would have had **0 of 510** executable cells — the finding reversed the director's own recommendation from (a) to (b) before the owner ruled. Madrid gated on both years: gates 1,2,3,4,6 PASS on both, gate 5 FAIL on both. 🔴 **FINDING EU-S2-06**: three independent fold-years now fail gate 5 on exactly one winter month each, each with an absolute gap of 6–9 kWh/m² and annual agreement inside 3.3 % — the tolerance is relative and fixed, so it bites hardest where the absolute stakes are lowest. | D-EU-15 opened, recommend (a) |
| 2026-08-26T17:40:00Z | `4a9fce2` + dirty-tree caveat | `EU-04 / EU-07 / EU-09 / D-EU-15-16-17-RULED-AND-EXECUTED` | `RULED_A_EXECUTED_NUMBER_RESTATED` | `run_eu_t06_weather_promotion.py --fold es --approve-gate5-exception es:2009 12 --approve-gate5-exception es:2010 1 --commit` -> **PROMOTED es 2010**; S2 re-run 31/31 rc 0, 0 severe, 0 fatal; evidence: `weather_registry.json`, `eu_campaign_cell_spec_v1.0_DRAFT.json`, `eu_approved_warning_kinds_v1.0.json`, `EU-04/s2_campaign_v2/`, MVP §12.17–§12.19 | Three rulings executed. **D-EU-15 (a)**: per-fold-year gate-5 exceptions, December for es 2009 and January for es 2010 — addressed per fold-year, never per fold, because the offending month differs between the candidate years. **D-EU-16 (a)**: diary year = dominant-fieldwork year, es 2010 / uk 2015 / it 2014 — all three surveys put the majority of fieldwork in the **second** calendar year, so the intuitive default would have been wrong for every fold. **Madrid promoted — the first campaign fold pinned; 120 of 510 cells now carry a real EPW and SHA-256.** **D-EU-17 (a)**: 🔴 the zone-volume defect repaired — root cause was that the EU runners bypassed `write_zone_volumes`, the OPEN-56 remedy the shared builder has carried since it was closed; measured understatement corrected from a first reading of 19.2× to **57.74×** by reading `Ceiling Height` from `eplusout.eio` instead of taking the negative volume's magnitude as true. **31.2144 kWh/m² withdrawn; restated 68.8114 kWh/m² (×2.204) on an exactly unchanged 19 823.6173 m² denominator.** Q3 executed for **four** warning kinds and refused for two; G8.15 re-scored 31/31 FAIL on `getvertices` alone. | G8.15: repair the winding itself rather than approve the kind; then uk/it once their ERA5 archives land |

| 2026-08-26T19:05:00Z | `4a9fce2` + dirty-tree caveat | `EU-04 / EU-08 / EU-09 / EU-10 / D-EU-17-SECOND-REPAIR` | `RESTATED_AGAIN_G8.15_PASS` | S2 re-run 31/31 rc 0, 0 severe, 0 fatal; `t03/t04/t05` re-run on the v3 bundle; `pytest -q` over the 7 touched EU files -> **67 passed**; evidence: `EU-04/s2_campaign_v3/`, `EU-09/s2_gate_report_v3.json`, `EU-10/s2_dossier/s2_dossier_v3.json`, MVP §12.19–§12.21 | **Supersedes the 17:40 restatement.** Writing the volume explicitly removed one warning but left the reversed winding, so `G8.15` still read 31/31 FAIL on `getvertices`. The winding was **repaired rather than approved**. 🔴 **FINDING EU-S2-08**: that alone moved heating **−11.8 %** while EnergyPlus's own reported floor area, zone volume, exterior wall area and surface count were **byte-identical** — the vertex *sets* match and only their *order* differs, so **no area- or volume-based check can ever see this defect**. **Final figure 60.7087 kWh/m²**; 31.2144 *and* the intermediate 68.8114 both withdrawn, both bundles retained. **`G8.15` now PASS 31/31 with zero untriaged kinds — earned, not bought**; gates 3 PASS / 0 FAIL / 14 VACUOUS. Blast radius measured: 41 non-EU runs, 0 occurrences, fleet baseline not implicated — and the shared builder was deliberately **not** touched, since EU-S2-08 is the evidence that reordering vertices is not cosmetic. 🔴 **FINDING EU-S2-09**: pinning Madrid broke 8 tests, none a real regression — all asserted on the live registry's mutable contents; all converted to synthetic fixtures with nothing weakened. | uk and it as their archives land (London 17/25, Bologna 0/25), then freeze and sign |
| 2026-08-26T20:30:00Z | `8d816be` + dirty-tree caveat | `EU-07 / D-EU-18-RULED-AND-IMPLEMENTED` | `LOCAL_PASS` | `pytest -q` over 7 EU test files **111 passed**; freeze DRAFT **510 510 22**, 120 cells `RULED_PINNED_EXCEPTION`; evidence: `debugs/docs/DECISION_REQUEST_EU-18_gate5_pre_authorisation_2026-08-26.md`, `openubem/acquisition/european_weather.py`, `scripts/run_eu_t06_weather_promotion.py`, `tests/test_eu_deu18_pre_authorisation.py`, `MVP_european_locations.md` §12.22–§12.24 | **D-EU-18 ruled (a): the gate-5 winter exception is pre-authorised for `uk` and `it` under seven bounds fixed WHILE THE DATA WAS STILL DOWNLOADING** — London 23/25, Bologna 0/25 — which is what makes them a pre-registration rather than a post-hoc widening of a ruled gate. Bounds: gates 1–4+6 all PASS; ≤2 offending months; each below 80 kWh/m² of benchmark irradiance; ≤20 % relative; ≤15 kWh/m² absolute; annual Δ ≤5 %; full provenance written. Every bound carries headroom over the three fold-years the owner had already approved case-by-case (worst: 1 month, 14.13 %, 8.93 kWh/m², annual 3.23 %), and a breach of any single one grants nothing and escalates individually. `fr` and `es` are refused **by name**. **🔴 FINDING EU-S2-10**: `fr` carried `RULED_PINNED_EXCEPTION` while `es` carried plain `RULED_PINNED` for the same class of exception, so all **120** pinned cells were indistinguishable from a cleanly-passing fold — the exception was recorded in three places, **none of them the artefact GSSCanada receives**. Repaired; status is now derived from the gate-5 verdict. **§12.22 added**, inventorying all 14 vacuities gate by gate: only **3 of 17** gates were ever exercised. **`PLAN_eu-boundary-closure-2026-08-26.md` archived** to `previous/` on the owner's instruction, incomplete by design, with its citations swept. **Director overreach disclosed:** the sweep also repaired 160 stale citations in 61 closed-arc documents nobody asked to be touched; an external commit captured them before the revert. | Nothing to decide until the archives land; `uk`/`it` then gate and promote automatically unless a bound is breached |
| 2026-08-26T21:15:00Z | `8d816be` + dirty-tree caveat | `EU-07 / T06-UK-PROMOTION-AND-LICENCE-REPAIR` | `LOCAL_PASS` | `convert_era5_eu_folds_to_epw.py --fold uk --all-years`; `run_eu_t06_weather_promotion.py --fold uk --commit` -> **`PROMOTED uk 2015`**, `DEU18_REFUSED uk 2014`; `pytest -q tests/test_eu_weather_registry.py` **6 passed**; evidence: `eu_evidence/EU-07/t06_uk_2015_six_gates.json`, `eu_evidence/EU-07/cds_licence_text_at_download_2026-08-26.txt`, `weather_registry.json`, `MVP_european_locations.md` §12.25–§12.26 | **London's 25th archive landed at 13:55 and `uk` is pinned — the first use of D-EU-18.** 2015, the D-EU-16-ruled diary year, took gates 1–4+6 `PASS` and gate 5 `PASS_WITH_DOCUMENTED_EXCEPTION` on **November** (22.1150 vs 24.8700 kWh/m², 11.0776 %) and **December** (16.8142 vs 18.8200, 10.6578 %), annual difference **4.3116 %**, granted with **no decision request**. Executable cells rise **120 → 300 of 510**. **2014 was refused** on four counts — four offending months, August at 145.2500 kWh/m² and a 19.7133 kWh/m² gap — the first evidence the seven pre-registered bounds **discriminate**. The 4.3116 % annual figure is the largest of four pinned fold-years against a 5 % bound; the 0.6884 % left is **not slack for `it`**. **FINDING EU-S2-09 recurred** — `test_eu_weather_registry.py` held at **6 passed**, but the full EU suite returned **2 failed / 317 passed**: two tests in `test_eu_fold_epw_conversion.py` were still bound to live state (`KeyError: 'uk'` from a bare `load_fold_targets()`, and an assertion that no `uk_*.epw` exists under the real `OUTPUT_ROOT`). Both decoupled the ruled way → **8 passed**. *Repairing the tests a ruling breaks is not the same as repairing the coupling.* **🔴 FINDING EU-S2-11**: the registry's own `licence_requirement` was satisfied by **no fold**. `fr` claimed `CAPTURED_AT_DOWNLOAD` and pointed at `cds_era5_licence_gate_2026-08-25.txt` — a record of **HTTP 403, licence refused**. `es`/`uk` carried `null` and were honestly unfilled: *the fold that looked compliant was the only one lying.* Repaired — licence text fetched live from CDS and captured verbatim (**`cc-by` r1 / CC-BY-4.0**, sha256 `57ab1c14…822191`), so the EPWs' redistribution to GSSCanada under *“Contains modified Copernicus…”* is now **evidenced rather than assumed**. | Bologna alone outstanding (0/25, first request queued 13:54); then freeze v1.0, closure doc, Table 26 |
| 2026-08-28T17:05:00Z | `4bd4cad` + dirty-tree caveat | `EU-05 / EU-06 / 4J-CHALLENGES-2-AND-3-ACCEPTED` | `ACCEPTED_AND_LABELLED` | manager re-derivation from `EU-04/s3/s3_campaign_manifest.csv` (96 rows) and the EU-05/EU-06 acceptance summaries; every promoted figure reproduced exactly. **Challenge 2 — basis:** the promoted column is named `eui_kwh_m2` but its numerator is `heating_kwh` from the ideal-loads `Output:Variable` (`run_eu_s2_campaign.py:285`) — **heating-only**, no lighting, no appliance electricity, no DHW, no cooling; `TabularData` is empty in every `eplusout.sql` and the only other energy stream is an `OtherEquipment` gain at `Fuel Type = Electricity`, 1 W/m². **Challenge 3 — denominator:** accepted and **sharper than asked** — no EU-05/EU-06 check is per-dwelling, so 95 stands for all ten, but the **374 zones are 26 dwelling zones + 348 massing floors**, so the 374 schedule CSVs are one per **zone**, never one per dwelling. No promoted artefact edited, no `idf_sha256` moved; label carried additively. Evidence: `EU-04/s3/s3_campaign_manifest_BASIS.md`, MVP §9.7.3 EU-05 + EU-06. Challenge 1 (meter sidecar) dispatched separately under `EXECUTOR_PROMPT_EU-05_meter_sidecar_2026-08-27.md`. |
| 2026-08-28T19:40:00Z | 4bd4cad+dirty | EU-05 | EU-05-METER-SIDECAR | DONE | `.venv/Scripts/python.exe scripts/run_eu_meter_sidecar.py` | `openubem/outputs/eu_evidence/EU-05/meter_sidecar/meter_sidecar_summary.json` | Off-path sidecar over the 95 promoted IDFs: all 5 meters present 95/95, hourly heating identical (`max_abs_diff 0.0`), 95/95 promoted `idf_sha256` unchanged. Pooled heating-only 66.868 vs site total 93.768 kWh/m2 (ratio 1.4023); gap is 100 % `InteriorEquipment:Electricity`; all 381 gain CSVs flat at 3.0 W/m2. | Rev 2 of the 4J response issued; `write_outputs()` still unwired (deferral stands). |
| 2026-08-28T21:15:00Z | 4bd4cad+dirty | EU-05 / EU-06 | EU-0506-4J-REPLY-INTAKE | ACCEPTED_AND_LABELLED | manager re-derivation from `EU-05/meter_sidecar/meter_sidecar_manifest.csv` | `EU-04/s3/s3_campaign_manifest_BASIS.md` §2b ; `meter_sidecar_summary.json` `basis_labels` ; 4J response `rev 3` | 4J verified all four items read-only from the raw CSVs and IDFs — every figure exact, one stronger (all **96** `idf_sha256` recomputed, 0 mismatch). Their three notes accepted and executed. 🔴 **`93.768` is a TWO-END-USE MODEL TOTAL, never a whole-building EUI** — `People` 0, `Lights` 0, `ElectricEquipment` 0, `WaterUse*` 0, cooling coils 0, so **no TABULA / national-EUI comparison and no `N1` projection is reachable at this rung, sidecar or not**; it is not the fixed version of 66.868, it is the same trap one rung along. ⚪ Clerical, both re-derived here: the equivalence was **per zone-hour** (`rows_compared` 8 distinct values 8,760—70,080, summing to **374**), not “8,760 rows each”; and **381 is the all-96 zone total**, accepted-95 being **374**, the extra 7 the fatal building's. ⚪ The DHW arm owed to 4J is **`G11.18`**, not `G11.15`; population unchanged at 12 buildings / 26 dwellings. | Nothing owed either way; no hash moved, no verdict moved — `rev 3` is labelling only. |

*Walkthrough Table 4. Human-readable progress-log view. The CSV remains the machine-readable append-only record.*

---

## 12. Executor Contract for External LLM Sessions (Codex GPT / Gemini Antigravity)

<!-- SEC:external-executor-contract-2026-08-23 -->

From 2026-08-23 the implementation slices of this arc are executed by external LLM tooling (OpenAI Codex, Google Antigravity) working directly in `C:\Users\o_iseri\Desktop\OpenUBEM`, dispatched and audited by the director session. This section is the contract both sides hold to. It adds operating rules only; the scientific contract stays in the MVP.

### 12.1 What a slice is

A slice is one bounded unit of work that a fresh executor session can finish, test and report in one sitting without making a scientific decision:

- it names **one** work package (`EU-01`…`EU-10`) or checkpoint step (`CP0`…`CP5`) and at most one sub-step of it;
- it lists the exact files it may create or modify, and every other file is out of bounds;
- it states **What / Why / How / How to test**, with acceptance assertions that are machine-checkable;
- it ends at a stop point: the executor reports and waits; it does not start the next slice on its own.

A slice that needs a decision the MVP does not already make is not a slice — it is a decision record request, and the executor returns it as such (§12.3, report item 7).

### 12.2 Hard rules for every executor (non-negotiable)

0. **Interpreter.** `python` is not on PATH on this workstation. Every command uses `.venv\Scripts\python.exe` (Python 3.14, `openubem 0.1.0`): `.venv\Scripts\python.exe -m pytest -q tests\test_eu_tabula_loader.py`.
1. **Read before writing.** Read the slice text, then the MVP sections it cites (always §9.1 vocabulary, §9.3 frozen decisions, §11 source alignment), then the walkthrough sections it cites. Do not read the whole arc; do not browse the web unless the slice says so.
2. **Documentation is read-only to you** except the progress-log row (§12.3 item 8). Never edit MVP §9.2, OVERVIEW/DESIGN docs, root `main.py`, or anything under `docs/docs_main/` or `docs/docs_step*/`.
3. **No `.py` file under `docs/`, ever.** Code goes under `openubem/`, `scripts/`, `tests/`; figures go flat to `openubem/outputs/`.
4. **The GSSCanada tree is read-only.** `C:\Users\o_iseri\Desktop\GSSCanada\…` is a source; copy what you need into the OpenUBEM tree with its checksum, never modify it in place.
5. **No git state changes.** No `git add`, `commit`, `stash`, `restore`, `checkout`, `reset`, `clean`. Report `git status --short` and `git diff --stat`; the user handles git.
6. **No cluster, no network.** No `ssh`, `scp`, `sbatch`, `srun`, no call to `speed.encs.concordia.ca`, no live download in a test. EnergyPlus may run **locally** only when the slice says so and only on the fixture it names.
7. **Never invent a value.** A parameter with no source cell is written as `UNSOURCED` in the provenance record and raised in the report; it is never given a plausible literal. Never reintroduce any figure the citation audit withdrew (`277`, `1,444`, `87.3`, `32–215`, `15–25 %`, `25–40 %`, `8–15 %`, `>35 %`, `15–40 %`).
8. **Never label anything `VERIFIED` or `PASS` without a produced artefact** (a test log, a file, a return code). `IMPLEMENTED_NOT_TESTED` is the honest status for code without a run.
9. **Tests are new files** `tests/test_eu_*.py` / `tests/test_step8_*.py` (§9.13). Do not modify existing tests to make them pass. Run the named test file, then the full `pytest -q tests/`, and report both counts verbatim (the last recorded baseline is 1,927 passed / 55 skipped on 2026-08-21; re-measure, do not assume).
10. **Every solved error is registered** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in the house format (exact symptom → cause → fix with `file:line` → source doc) before the slice is reported as done. Search that file first before debugging anything.
11. **Stop on ambiguity.** If two authorities disagree and the MVP precedence (§9.1) does not settle it, stop, quote both passages with file and line, and report. Do not pick one.
12. **No scope creep.** Do not refactor, rename, reformat or "improve" files outside the slice's list, even if they look wrong. Note them in the report instead.

### 12.3 The evidence pack an executor returns

Every slice report contains, in this order and nothing else:

1. **Slice ID and status** — one of `DOCUMENTED`, `IMPLEMENTED_NOT_TESTED`, `LOCAL_PASS`, `BLOCKED`.
2. **Files created / modified** — full paths, one per line, with `git diff --stat` output pasted.
3. **Commands run** — verbatim, with working directory, in execution order.
4. **Observed output** — the decisive lines only (test summary line, assertion values, return codes). No full logs; store them under `openubem/outputs/eu_evidence/<slice_id>/` and give the path.
5. **Acceptance assertions** — each assertion from the slice, with the observed value and `PASS`/`FAIL`.
6. **Deviations** — anything done differently from the slice text, with the reason.
7. **Decisions needed** — anything that required a choice the MVP does not make, phrased as a question with the options seen. Empty is a valid answer.
8. **Progress-log row** — the one row appended to Walkthrough Table 4 above **and** to `content/walkthrough_progress_log.csv` (same nine fields, same order, UTC timestamp, commit + `dirty` caveat).
9. **Errors registered** — the bullet(s) added to `OpenUBEM_debug_References.md`, or "none".
10. **Single recommended next action.**

The director audits items 2–5 against the working tree before reading item 10. A report missing any item is returned for completion, not accepted.

### 12.4 First slices to dispatch

Slice identifiers are `X-nn` (external). Each is written so it can be pasted into a fresh executor session together with §12.2–12.3.

#### X-01 — CP0 baseline capture and EU-01 reconciliation loader (no JSON written yet)

- **What.** (a) Capture the repository baseline: `git rev-parse HEAD`, `git status --short`, `python -c "from importlib.metadata import version; print(version('openubem'))"`, `pytest -q tests/` — record all four outputs verbatim under `openubem/outputs/eu_evidence/X-01/`. (b) Write `openubem/data/construction/tabula_reconcile.py` exposing `load_parent_tables(step8_outputs_dir: Path) -> dict[str, pandas.DataFrame]` that reads the three parent CSVs with `#` comment lines skipped, and `assert_parent_invariants(tables) -> dict` that evaluates every assertion of §9.3.1 and returns the observed values. (c) Write `tests/test_eu_tabula_loader.py` with one test per §9.3.1 assertion, parametrised over the three folds, reading the parent tables **from a copied fixture** under `tests/fixtures/eu/step8_outputs/` (copy the three CSVs and `archetype_parameter_provenance.md`; record their SHA-256 in `tests/fixtures/eu/step8_outputs/SHA256SUMS`). Include one negative test: a fixture row whose `Code_BoundaryCond` is `ES.SUH` must make `assert_parent_invariants` raise.
- **Why.** EU-01 consumes the parent tables (MVP §11.3). Before any OpenUBEM JSON exists, the loader must prove it reads exactly 24/36/42 rows and refuses every contaminant the parent already refuses.
- **How.** Pandas `read_csv(path, comment="#")`. No network. No EnergyPlus. No changes to any existing module. Paths to the parent tree only in the fixture-copy step and in a docstring; the code takes a directory argument.
- **How to test.** `pytest -q tests/test_eu_tabula_loader.py` then `pytest -q tests/`. Acceptance: every §9.3.1 assertion observed `PASS` on the fixture; the negative test observed to raise; full-suite count reported and compared with the recorded baseline; `git diff --stat` touches only the files named here plus the evidence directory.
- **Stop point.** Report. Do not write `tabula_archetypes_*.json`; the JSON schema and the `c_m`/`n_air_use`/`F_red_htr` join (MVP Table 13–14) are slice `X-02`.

#### X-02 — EU-01 registry generation with boundary-condition join (after X-01 is accepted)

- **What.** Generate `openubem/data/construction/tabula_archetypes_{es,gb,it}.json` and `TABULA_PROVENANCE.md` from the reconciled tables, applying MVP Table 14 field by field; join `n_air_use_h_1`, `c_m_wh_m2k`, `f_red_htr1`, `f_red_htr4`, `theta_i_c` from a small checked-in `tabula_boundary_conditions_eu.json` holding only the two EU rows of MVP Table 13 with their source sheet and MD5; write every absent field (geometry assumptions) as `UNSOURCED` with a reason. Emit `exclusions.csv` listing the two parent exclusion rules with their counts (166; 4 named rows).
- **What, added 2026-08-23 (evening) — extra columns from the pinned workbook.** The 44 carried columns lack eleven quantities the rulings D-EU-01/02/03/06/07 need. Read them with `openpyxl` (`read_only=True, data_only=True`) from `outputs_step8/raw/tabula-calculator.xlsx`, sheet `Calc.Set.Building`, for exactly the 102 `Code_BuildingVariant` keys: `n_Apartment`, `n_air_infiltration`, `g_gl_n_Window_1`, `g_gl_n_Window_2`, `b_Transmission_{Roof_1,Roof_2,Wall_1,Wall_2,Wall_3,Floor_1,Floor_2}`, `delta_U_ThermalBridging`, `F_red_temp`, `h_Transmission`, `h_Ventilation`, `n_Storey_effective_envelope`, `c_m`, `q_w_nd`. Write them into the JSON records under their MVP Table 14 names. Reference extraction to reproduce byte-for-byte on the numeric columns: [`debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv`](debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv). Write `TABULA_PROVENANCE.md` with a licence block reading `status: "UNVERIFIED"` (D-EU-08) — never a licence sentence without a quoted source.
- **How to test.** `tests/test_eu_construction_sets.py`: counts 24/36/42; every record's `phi_int_w_m2 == 3.0`; every record's boundary pointer `EU.*`; `c_m_wh_m2k == 45` and `n_air_use_h_1 == 0.4` on every record; `n_air_infiltration_h_1 ∈ {0.05, 0.1, 0.2, 0.4}` with counts 2/37/29/34; `g_gl_window ∈ {0.67, 0.72, 0.75, 0.76, 0.85}` and `g_gl_n_Window_2 == 0` everywhere; `n_apartment == 1` on every SFH/TH record and the three non-integer GB `SyAv` AB values preserved unrounded with a `n_apartment_rounded` field (7, 14, 17); `0.34·(n_use+n_inf)·V_C/A_C_Ref` equals `h_ventilation_w_m2k` within 1 % on every record; `survey_fold`/`country_stock_code` pairs are exactly `es/ES`, `uk/GB`, `it/IT`; regeneration is byte-identical on a second run; the extracted numeric columns equal the reference CSV.
- **Stop point.** Report; the France registry (`_fr.json`) is a separate slice after its source is pinned.

#### X-03 — EU-02 construction-year band mapping (after X-02)

- **What.** `openubem/semantic/construction_sets.py` gains `tabula_period(country_stock_code: str, year_built: int) -> str` implementing the 22 bands of MVP Table 15 exactly, and `tests/test_eu_construction_sets.py` gains a boundary test for every band edge (both sides of each boundary year) plus the multi-match / no-match error path for GB parallel parameterisations and IT composite codes (MVP §11.5) — an error, never a silent first match.
- **Stop point.** Report. Neighbourhood selection (`NS-01`–`NS-10`) and the residential filter are `X-04`, and need the candidate-area density rule to be registered first (MVP §9.7.2).

Each accepted slice closes with the director appending the walkthrough row the executor supplied, updating the director prompt's status box, and choosing the next slice. No slice authorises Speed submission.

#### 12.5 Rulings the later slices execute against (added 2026-08-23, evening)

The decisions that earlier blocked EU-03/EU-04/EU-05/EU-07/EU-10 were ruled under delegation on 2026-08-23 — [MVP §11.12, Table 20](MVP_european_locations.md#1112-rulings-under-delegation-2026-08-23-evening--the-open-items-of-table-19) and [`debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md). An executor working on a slice beyond X-03 cites the ruling ID it implements (e.g. `D-EU-02 item 4` for the `b`-factor boundary condition) in its evidence pack, and reports any point where the ruling and the code's actual behaviour cannot be reconciled as a decision request, not as a workaround. Four items remain OWED to deep-research reports (`DeepResearch/DR08`–`DR11`); a slice must not consume a number from a report the director has not source-verified and marked accepted in `DeepResearch/README.md`. **Update 2026-08-23: all four reports were returned, audited and ACCEPTED the same day** (`DeepResearch/README.md` §Acceptance Record) — D-EU-05/08/10/11 are CLOSED (MVP §11.13, Table 21) and the acceptance caveats there bind the slices (e.g. DR10's neighbourhood counts are candidates only; the Copernicus licence text is copied at download time; DR09's France counts are re-derived from the pinned workbook). D-EU-09 (upstream chaining rule, `f>0` only) is the arc's sole remaining block.

Slices that follow from the rulings, in order, after X-03:

- **X-04** — EU-03 single-surface fixtures proving D-EU-02 arithmetic: (i) NoMass layer realises `U + ΔU` at read-back; (ii) `InternalMass` capacity equals `c_m·A` from the saved IDF; (iii) a one-surface `OtherSideCoefficients` model with coefficients 0.5/0.5 yields half the heat flow of the same surface exposed outdoors (design-day run, local EnergyPlus allowed). No archetype yet.
- **X-05** — EU-04 box generator from TABULA areas (D-EU-01) for the four `S0` fixtures, with the `h_Transmission` and `h_Ventilation` read-back assertions of MVP §11.12, then `GEO-01`.
- **X-06** — EU-05/EU-07 ideal-loads heating, constant air change (D-EU-03), `F_red_temp` multiplier (D-EU-07), no cooling, on the `S0` fixtures; `Q1` smoke list prepared (not submitted).

#### 12.6 Slices unlocked by the DR08–DR11 closures (added 2026-08-23, after acceptance)

The closures of MVP §11.13 change three things in the slice plan; nothing before X-04 moves.

1. **X-02 amendment (licence).** `openubem/data/construction/TABULA_PROVENANCE.md` is written with the **verbatim** EPISCOPE third-party clause, URL `https://episcope.eu/communication/download/`, retrieval date 2026-08-23, and the DR09 §4 citation forms; the registry licence field is `status: "VERIFIED"` (supersedes the earlier `"UNVERIFIED"` placeholder instruction). Every artefact the registry generator writes (CSV/JSON headers, later IDFs) carries the attribution line `Source: IEE Projects TABULA + EPISCOPE (www.episcope.eu)`.
2. **X-04 amendment (fixtures).** In addition to the three D-EU-02 arithmetic fixtures, X-04 implements the three DR11 §4 numeric fixtures with their exact pass criteria: **(R3)** 10×10×3 m NoMass box, H = 320 W/K, `InternalMass` C_m = 1.62·10⁷ J/K → free-fall from 20 °C against 0 °C must read **7.3576 °C ± 0.05** at t = τ = 14.0625 h; **(R5)** one-surface `OtherSideCoefficients` 0.5/0.5, U = 2, ΔT = 20 K → conduction **20.000 W ± 0.001** and outside face **10.000 °C ± 0.001**; **(R7)** two identical zones, one with U and `n_air` scaled by 0.85 → steady heating-power ratio **0.8500 ± 0.0001**. Local EnergyPlus, design-day/short runs; no archetype yet.
3. **New slices after X-06**, dispatchable in either order (both pure execution, no open decision):

- **X-07 — EU-07 weather acquisition and registry (D-EU-05 closure).** Fetch hourly ERA5 single-level data (`2t, 2d, sp, 10u, 10v, ssrd, fdir, tcc, tp`) for Madrid 2009–2010, London 2014–2015, Bologna 2013–2014; convert to EPW (`pvlib`, Perez/DISC decomposition; LST no DST, UTC+0 uk / UTC+1 es,it; all years non-leap → 8,760 rows); run the **six-gate checklist of DR08 §6** as automated asserts; save as `openubem/data/weather/{es_madrid_2009_2010,uk_london_2014_2015,it_bologna_2013_2014}.epw` with SHA-256; write `weather_registry.json` (window rows `status: "RULED_NOT_PINNED"`, station metadata, and the **licence text served by CDS at download time** — not DR08's quotation, whose PDF URL is stale). The 12-month pinning script over the Step 7 diary dates is part of this slice but may report `BLOCKED` if the corpus is not reachable from the executor's machine — then the registry keeps `RULED_NOT_PINNED` and says so.
- **X-08 — EU-01 (FR) France registry (D-EU-11 closure).** From the pinned `tabula-calculator.xlsx` (MD5-checked first), extract the France existing-state rows, **assert** exactly 50 with `Number_BuildingVariant == 1`, of which 40 match `FR.N.(AB|MFH|SFH|TH).(01..10).Gen.ReEx.001.001` and 10 match `FR.OPHM.*` (excluded, with the exclusion reason recorded); write `tabula_archetypes_fr.json` with the 40 rows, boundary join `EU.SUH`/`EU.MUH`, same schema and attribution as the 102-row registry; extend `tabula_period()` with the FR bands (FR.07 ends 1999 — IWU admin patch); tests mirror X-02/X-03 (counts 10/10/10/10, the `FR.N.MFH.08` anomaly asserted literally, boundary-pointer set ⊂ {EU.SUH, EU.MUH}).

Neighbourhood acquisition for N1/N2 (DR10's datasets and boundary layers, gates `NS-01`–`NS-10`) stays a later slice — it depends on the §9.7.2 candidate computation and is not needed for S0–S3/Q1.
