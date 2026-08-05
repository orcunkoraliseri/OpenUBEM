# LayoutAssigner — Walkthrough (v2.1)

> [!NOTE]
> **v2.1 (2026-07-22, manager audit):** zone counts in §2 replaced with counts **measured directly from the IDF files** (the v2 "corrected" counts were themselves wrong), and two blockers the v2 docs missed are now tracked in `implementation_plan.md`: all 31 baseline IDFs are **EnergyPlus 22.1** while the pipeline locks the IDD to **23.1** (→ T08), and the archetype dictionaries are misaligned with the canonical `_ARCHETYPE_VOCAB` (→ T02/T03).

## 1. Strategy Pivot: `layoutgenerator` → `layoutAssigner`

### Why the pivot
The `layoutgenerator` (`docs/docs_TODO/layoutgenerator`) dynamically partitions real-world GIS polygon footprints (L/U/T/courtyard shapes) into room-level zones with double-loaded corridors. While theoretically flexible, it proved:

1. **Geometrically fragile**: Polygon splitting on non-rectangular footprints frequently produced non-convex zones, vertex-count mismatches in interzone surfaces, and EnergyPlus `GetSurfaceData` fatal errors.
2. **Architecturally limited**: Only `MidriseApartment` (corridor+units) was implemented. Complex building programs — **Hospitals** (55 zones: ER, OR, ICU, patient rooms, labs, kitchens), **Large Hotels** (30+ zones: guest rooms, banquet, lobby), **Outpatient Clinics** (exam rooms, MRI, procedure rooms) — cannot be approximated by a simple corridor-unit algorithm.
3. **High maintenance cost**: Each new archetype required a dedicated `MODULE_SPECS` entry with fitted geometric parameters.

### The `layoutAssigner` solution
Instead of generating geometry from scratch, `layoutAssigner`:
1. **Selects** the DOE/ASHRAE 90.1 standard prototype IDF matching the building's archetype
2. **Scales** its floor area to match the real building's total gross floor area
3. **Patches** location (EPW), weather, and optionally envelope properties for the target climate zone

The baseline library (`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs`) contains **31 pre-validated EnergyPlus IDF files** with complete multi-zone layouts, HVAC loops, schedules, and construction assemblies.

---

## 2. Measured Baseline IDF Zone Inventory (v2.1)

The v1 documents estimated zone counts with a formula; the v2 "corrections" were partial hand counts and **also wrong**. The counts below were **measured 2026-07-22** as standalone `Zone,` object headers per file (they include plenums/attics/unconditioned zones — conditioned counts are lower). From v2.1 onward, `parse_baseline_zones()` (plan T05) is the only source of truth.

| Archetype | Baseline IDF | Measured Zones | v2 claim | E+ Version |
|---|---|---|---|---|
| `MidriseApartment` | `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` | **92** | 27 | 22.1 |
| `HighriseApartment` | `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` | **69** | ~90 | 22.1 |
| `Hospital` | `ASHRAE901_Hospital_STD2022_Buffalo.idf` | **58** | 55 | 22.1 |
| `LargeHotel` | `ASHRAE901_HotelLarge_STD2022_Buffalo.idf` | **27** | ~30–40 | 22.1 |
| `SmallHotel` | `ASHRAE901_HotelSmall_STD2022_Buffalo.idf` | **69** | ~66 | 22.1 |
| `LargeOffice` | `ASHRAE901_OfficeLarge_STD2022_Buffalo.idf` | **42** | ~72 | 22.1 |
| `MediumOffice` | `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` | **68** | 15 "OK" | 22.1 |
| `SmallOffice` | `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf` | **7** | 5 "OK" | 22.1 |
| `Outpatient` | `ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf` | **119** | — | 22.1 |
| `PrimarySchool` | `ASHRAE901_SchoolPrimary_..._50pct_downscaled.idf` | **29** | — | 22.1 |
| `SecondarySchool` | `ASHRAE901_SchoolSecondary_..._50pct_downscaled.idf` | **50** | — | 22.1 |
| `TallBuilding` / `SuperTallBuilding` | `TallBuilding...` / `SuperTallBuilding..._v221.idf` | **164 / 256** | — | 22.1 |
| `College` / `Laboratory` | `College...` / `Laboratory..._v221.idf` | **118 / 24** | — | 22.1 |

Full 31-file inventory (incl. retail, restaurants, data centers, houses, unmapped files) in `implementation_plan.md` §3.1.

> [!WARNING]
> The CSV (`layout_assign_vs_resolution_modes.csv`) and the results document still carry formula-based zone counts and fabricated EUI estimates (`fast_zone × 1.01`). **Do not re-run `compare_layout_assign.py` before plan task T10** — the current script would overwrite the corrected results document with the fabricated numbers.

---

## 3. Pipeline Integration Architecture

### How `layout_assign` must work inside `BuildingIDF.build()`

The standard pipeline for modes `auto`/`building`/`floor`/`fast_zone` is:

```
BuildingIDF.__init__() → load blank template IDF
build() → simplify footprint → discover context → decide_zoning_strategy()
       → build_zones() → extrude_geometry() → assign_constructions()
       → assign_infiltration() → assign_loads() → assign_hvac()
       → assign_dhw/cooking/refrigeration() → write_outputs() → save IDF
```

For `layout_assign`, the pipeline must **branch** after `decide_zoning_strategy()`:

```
BuildingIDF.__init__() → load BASELINE PROTOTYPE IDF (not blank template)
build() → simplify footprint (still needed for manifest metadata)
       → decide_zoning_strategy() → "layout_assign"
       → [BRANCH] calculate_scaling_factor()
                 → scale_baseline_idf()     ← scale X/Y vertices by √S
                 → patch_location_and_weather() ← override Site:Location from EPW
                 → parse_baseline_zones()    ← extract zone list for manifest
                 → [SKIP extrude_geometry, assign_constructions,
                    assign_infiltration, assign_loads, assign_hvac,
                    assign_dhw, assign_cooking, assign_refrigeration]
                 → write_outputs() → save IDF
```

### Why skipping is safe
The baseline prototype IDFs already contain:
- All `ZONE` objects with correct geometry
- All `BuildingSurface:Detailed` and `FenestrationSurface:Detailed` objects
- All `PEOPLE`, `LIGHTS`, `ELECTRICEQUIPMENT` objects per zone
- Complete HVAC system definitions (not just PTAC templates)
- All `Schedule:Compact` objects
- All `Construction` and `Material` objects
- All `Output:Variable` and `Output:Meter` objects

The things that need patching are (v2.1 — expanded from v2):
1. **Geometric scale** (X/Y vertex coordinates × $\sqrt{S}$)
2. **Absolute levels × $S$** — not just LIGHTS/EQUIPMENT/PEOPLE: also `ZoneInfiltration:DesignFlowRate` (Flow/Zone), `DesignSpecification:OutdoorAir` (Flow/Zone), `WaterUse:Equipment` peak flow, `Exterior:Lights` (per-area specs untouched)
3. **Baseline `Output:*` objects purged**, then the project's own `write_outputs()` applied — otherwise duplicated outputs break harvest-schema parity (`Site:WeatherFile` mentioned in v2 is not an EnergyPlus object)
4. **Site location** (`Site:Location` from EPW header — reuse builder's `_parse_epw_location`) + single annual `RunPeriod`
5. **E+ version transition 22.1 → 23.1** of the baseline library (plan T08 — pipeline IDD is locked to 23.1)

---

## 4. Implementation Status

> [!NOTE]
> **Live tracking has moved.** The single live surface for task status is the **§0 checklist in [`implementation_plan.md`](implementation_plan.md)** (ticked by the executor per task, checkpoints by the manager). The tables below are the **v2.1 audit snapshot (2026-07-22)** and are not updated during execution.

### ✅ Completed (v1)
| Item | File | Status |
|---|---|---|
| `BaselineIDFRegistry` class | `layout_assigner.py` | ✅ Working |
| `ARCHETYPE_IDF_MAP` (31 entries) | `layout_assigner.py` | ✅ Complete |
| `calculate_scaling_factor()` | `layout_assigner.py` | ✅ Working |
| `assign_baseline_layout()` metadata | `layout_assigner.py` | ✅ Working |
| `decide_zoning_strategy()` routing | `zoning.py` | ✅ Wired |
| `build_zones()` `layout_assign` branch | `zoning.py` | ✅ Wired |
| Unit tests (metadata level) | `test_layout_assigner.py` | ✅ 4/4 pass |
| Zoning regression (no breakage) | `test_zoning.py` | ✅ 43/43 pass |

### ❌ Not Yet Implemented (v2.1 scope — task IDs from `implementation_plan.md` §5)
| Item | Task | File | Priority |
|---|---|---|---|
| Registry portability + lazy init (no import-time scan of external dir) | T01 | `config.py`, `layout_assigner.py` | **P0** |
| Re-key dicts on canonical `_ARCHETYPE_VOCAB` (10 missing IDs, 2 case bugs) | T02 | `layout_assigner.py` | **P0** |
| Graceful fallback for `Courthouse`/`OpenUBEMUnknown`/missing library | T03 | `layout_assigner.py`, `builder.py` | **P0** |
| `scale_baseline_idf()` — vertex & absolute-load scaling (expanded list) | T04 | `layout_assigner.py` | **P0** |
| `parse_baseline_zones()` — extract zone list (`extruded=True`) | T05 | `layout_assigner.py` | **P0** |
| `purge_baseline_outputs()` + `patch_location_and_weather()` | T06 | `layout_assigner.py` | **P0** |
| `BuildingIDF.__init__()` + `build()` — layout_assign branch | T07 | `builder.py` | **P0** |
| Baseline library E+ version transition 22.1 → 23.1 | T08 | library-side (one-off) | **P0** |
| Test restructure (synthetic fixtures + skipif) + LIVE_SMOKE-LA | T09 | `test_layout_assigner.py` | **P0** |
| Fix `compare_layout_assign.py` (drop ×1.01, real zone counts, no MD overwrite) | T10 | `compare_layout_assign.py` | **P0** |
| `patch_envelope()` — cross-CZ U-values | T11 | `envelope_patcher.py` (NEW) | P1 |
| Actual simulation comparison + regenerated CSV/results doc | T12 | `compare_layout_assign.py` | P1 |

---

## 5. Deliverable Files

| File | Location | Description | Status |
|---|---|---|---|
| `implementation_plan.md` | `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/` | Technical plan + §0 live status checklist + §8 progress log | ✅ v2.1 |
| `walkthrough.md` | `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/` | Strategy walkthrough (audit snapshot) | ✅ v2.1 |
| `layout_assign_vs_resolution_modes.csv` | `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/` | Comparison matrix (zone counts need correction) | ⚠️ Needs regen |
| `OpenUBEM_results_LayoutAssigner.md` | `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/` | Results report (EUI values are placeholder) | ⚠️ Needs regen |
| `layout_assigner.py` | `openubem/geometry/` | Core module | ⚠️ Needs P0 functions |
| `builder.py` | `openubem/idf/` | Pipeline orchestrator | ⚠️ Needs `layout_assign` branch |
| `envelope_patcher.py` | `openubem/idf/` | Cross-CZ envelope patching | 📅 Phase 2 |
| `test_layout_assigner.py` | `tests/` | Unit + integration tests | ⚠️ Needs E2E tests |
| `compare_layout_assign.py` | `scripts/analysis/` | Comparison analysis script | ⚠️ Needs actual sim data |
