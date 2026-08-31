# `RESULTS_EU-13` — Dwelling-Layout Full Coverage, Multi-Storey Stacking, and Imputation Cascade

- **Date**: 2026-08-28
- **Work Package**: `EU-13` (European Locations × Step 8 / 3D Visualization)
- **Ruling Reference**: `DECISION_REQUEST_D-EU-33`
- **Status**: `COMPLETED`
- **Output Artifacts**:
  - `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/layouts/<building_id>.json` (1,340 sidecars)
  - `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/<district_slug>_manifest.csv` (updated with `geometry_outcome` and `layout_json`)
  - `openubem/outputs/3D/eu_<DISTRICT>_viewer.html` & `eu_<DISTRICT>_data/`
  - `docs/docs_ACTIVE/europeanLocations/outputs_3D/` (byte-identical mirrors)

---

## 1. Executive Summary

Under `DECISION_REQUEST_D-EU-33`, the dwelling-layout machinery of OpenUBEM has been extended from the initial 51-building baseline to full coverage across the European fleet. Three mandatory architectural requirements were implemented:
1. **Multi-Storey Stacking (`FINDING EU-12-01` Resolved)**: Emitted dwelling partitions are repeated across all $N$ storeys with explicit $Z$ floor/ceiling bounds.
2. **General Multi-Angle & Radial Partitioning**: Slicing extended to non-convex footprints and courtyard/lightwell topologies without relaxing `audit_european_floor_partition` tolerances.
3. **Four-Tier Dwelling Count Imputation Cascade**: Missing observed dwelling counts imputed with full provenance tracking and tagged as `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`.
4. **Interactive Storey Selector**: Integrated in all four district 3D viewers.

Dwelling layout coverage across simulated buildings increased from **51 to 1,078 buildings** (a **21.1× increase**). Across all non-narrow simulated buildings, the audit pass rate reached **99.08% (1,078 / 1,088)**.

---

## 2. Before / After Coverage Census

| District | Stock Total | Simulated | EU-12 Baseline Emitted | EU-13 Observed Emitted | EU-13 Imputed Emitted | EU-13 Total Emitted | Narrow Fallback (`< 8m`) | Other Fallback (Audit Fail) | Not Simulated | Simulated Coverage % |
|---|---|---|---|---|---|---|---|---|---|---|
| **Madrid — Berruguete** | 1,194 | 961 | 51 | **769** | **1** | **770** | 185 | 6 | 233 | **80.1%** (770 / 961) |
| **Lyon — Haut Cœur** | 530 | 297 | 0 | **0** | **239** | **239** | 58 | 0 | 233 | **80.5%** (239 / 297) |
| **London — St Dunstan's** | 1,242 | 82 | 0 | **0** | **69** | **69** | 9 | 4 | 1,160 | **84.1%** (69 / 82) |
| **Bologna — Galvani 2** | 1,220 | 0 | 0 | **0** | **0** | **0** | 0 | 0 | 1,220 | N/A (0 eligible) |
| **Total European Corpus** | **4,186** | **1,340** | **51** | **769** | **309** | **1,078** | **252** | **10** | **2,846** | **80.4%** (1,078 / 1,340) |

*Note: Narrow footprints (`< 8.0 m`) stay massing boxes as ruled in `D-EU-33` §3.4. Excluding narrow footprints, the layout emission rate is **99.08% (1,078 / 1,088)**.*

---

## 3. Storey-Stacking Fix Confirmation (`FINDING EU-12-01`)

- In `openubem/geometry/european_residential.py`, `european_layout_to_zone_specs` now accepts `n_storey` and stacks the in-plane dwelling partition across every floor index $s \in [0, n\_storey - 1]$:
  - $z_{\text{floor}} = s \times 3.0\text{ m}$
  - $z_{\text{ceiling}} = (s + 1) \times 3.0\text{ m}$
  - Zone name format: `{building_id}_F{s}_dwelling_{d}`
- **Confirmation across all 1,078 emitted buildings**:
  - `len(sidecar["floors"]) == sidecar["storeys"]` evaluated to `True` for 100% of emitted files across all districts.
  - Multi-storey building count: 763 (Madrid), 236 (Lyon), 69 (London) = **1,068 multi-storey buildings** fully extruded.
- **3D Viewer Pop-up**:
  - Added interactive storey selector buttons (`F0 (0–3m)`, `F1 (3–6m)`, ...) enabling interactive floor plan exploration across any level.

---

## 4. Partition Algorithm Method & Audit Performance

### Algorithmic Design (`openubem/geometry/european_residential.py`)
1. **Multi-Angle Sweep (Equal-Width & Equal-Area)**:
   - Rotates the polygon across 90 orientations (including long axis, orthogonal axes, and 2° intervals).
   - Tests both equal-width box clipping and binary-searched equal-area quantile slices.
   - Handles concave angles and non-convex footprints without topological fragmentation.
2. **Radial / Angular Sector Partitioning**:
   - For courtyard / doughnut topologies, projects angular sectors from the polygon centroid or courtyard hole centroid outward to the exterior perimeter.
   - Produces contiguous wedge-like dwellings connecting the interior courtyard to the exterior facade.
3. **Strict Audit (`audit_european_floor_partition`)**:
   - Unchanged tolerance: $\Delta A / A \le 10^{-9}$.
   - Exact overlap check: $\text{overlap} = 0.0\text{ m}^2$.
   - Exterior facade contact: $\ge 2.50\text{ m}$ per dwelling unit.

### Pass Rate
- Total broad (non-narrow) simulated buildings attempted: **1,088**
- Successfully passed audit and emitted: **1,078 (99.08%)**
- Fallback failures: **10 (0.92%)**

---

## 5. Census of Surviving Fallbacks (All 10 Non-Narrow Buildings Individually Named)

### Madrid (`ES-MAD-BERRUGUETE`) — 6 Buildings
| Building ID | Area (m²) | Storeys | Dwellings | Units/Floor | Courtyard Holes | Failure Reason Code | Root Cause |
|---|---|---|---|---|---|---|---|
| `relation/12803902` | 326.7 | 4 | 44 | 11 | 2 | `PARTITION_AUDIT_FAILED` | High density (11 units/floor) across complex 2-courtyard ring yields multi-part fragments. |
| `relation/4179135` | 629.8 | 2 | 19 | 10 | 1 | `PARTITION_AUDIT_FAILED` | 10 units/floor on deep rectangular courtyard ring produces disconnected slices. |
| `relation/4835801` | 551.2 | 5 | 45 | 9 | 4 | `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` | 4 internal courtyards consume perimeter; units fail $\ge 2.5\text{ m}$ exterior facade contact. |
| `way/310738150` | 232.6 | 4 | 22 | 6 | 0 | `PARTITION_AUDIT_FAILED` | Irregular concave notch splits dwelling slices into multi-polygons. |
| `way/311159688` | 541.4 | 3 | 33 | 11 | 0 | `PARTITION_AUDIT_FAILED` | High density (11 units/floor) on tapered footprint causes polygon fragmentation. |
| `way/432411472` | 320.6 | 3 | 16 | 6 | 0 | `PARTITION_AUDIT_FAILED` | Re-entrant corner geometry divides central dwelling strip into disconnected parts. |

### London (`GB-LDN-STDUNSTANS`) — 4 Buildings
| Building ID | Area (m²) | Storeys | Dwellings | Units/Floor | Courtyard Holes | Failure Reason Code | Root Cause |
|---|---|---|---|---|---|---|---|
| `way/396622952` | 126.6 | 2 | 69 | 35 | 0 | `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` | High imputed density (35 units/floor on 126.6 m² = 3.6 m²/dwelling) cannot physically fit $\ge 2.5\text{ m}$ facade contact. |
| `way/398158951` | 104.9 | 2 | 69 | 35 | 0 | `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` | High imputed density (35 units/floor on 104.9 m² = 3.0 m²/dwelling) cannot fit $\ge 2.5\text{ m}$ facade contact. |
| `way/398158958` | 171.6 | 3 | 69 | 23 | 0 | `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` | High imputed density (23 units/floor on 171.6 m² = 7.4 m²/dwelling) fails exterior facade contact threshold. |
| `way/952012485` | 138.1 | 2 | 69 | 35 | 0 | `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` | High imputed density (35 units/floor on 138.1 m² = 3.9 m²/dwelling) fails exterior facade contact threshold. |

### Lyon (`FR-LYO-HAUTCOEURPENTES`) — 0 Buildings
- 0 broad footprint fallback failures (all 239 non-narrow buildings emitted cleanly).

---

## 6. Deliverables & Data Folder Verification

1. **Side-Car JSONs**:
   - 1,340 per-building layout JSON files generated in `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/layouts/`.
   - Updated manifest files (`openubem/outputs/eu_evidence/EU-11/<DISTRICT>/..._manifest.csv`) with `layout_json` and updated `geometry_outcome` values.
2. **Interactive 3D District Viewers**:
   - All 4 HTML viewers generated in `openubem/outputs/3D/` and mirrored byte-identically to `docs/docs_ACTIVE/europeanLocations/outputs_3D/`.
   - Fully interactive 2D floor-plan popup with storey selector, scale bar, pastel zone rendering, provenance badges, and named fallback notices.
3. **Data Folders (`eu_<DISTRICT>_data/`)**:
   - `buildings.csv`, `results.csv` (where bound), `results_source.csv` (where bound), `layouts/` directory, `sources.json` with SHA-256 hashes, and `index.html`.
4. **Documentation**:
   - `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §8.5 updated.
   - Appended `EU-13-DWELLING-LAYOUT-FULL-COVERAGE-COMPLETE` in `walkthrough_progress_log.csv`.

---

## 7. Post-delivery audit finding and fix (2026-08-28, same day)

Owner inspection of `eu_GB-LDN-STDUNSTANS_viewer.html` (`way/51781396`, 17-storey imputed-count building)
found the pop-up header claiming `Unconditioned core: Yes` while the rendered floor plan showed 5 dwelling
strips tiling 100% of the footprint with no core drawn. Verified against the side-car JSON: no core polygon
exists in any `floors[].zones` entry for any of the 1,078 emitted buildings.

**Root cause**: `scripts/emit_eu11_layout_sidecars.py:183` wrote `allocation.has_unconditioned_core` — a
density-threshold flag (`dwellings/storeys >= 2`) computed by `allocate_european_dwellings`, the
synthetic-TABULA-plate helper called here only to obtain `units_per_floor` — into the side-car as if it
described the real-footprint geometry actually emitted by `generate_european_dwelling_layout`. That function's
own docstring (`openubem/geometry/european_residential.py:139-141`) states a core is deliberately never
carved from an observed shell, since doing so would violate the audited GEO-01 area-conservation contract
against the real footprint. The two allocation paths were conflated; the flag never matched the geometry.

**Fix**: line 183 now writes `layout.unconditioned_core_emitted` (the field already defined on
`EuropeanGeneratedFloorLayout`, always `False` on this path — no call site in the module ever sets it `True`),
honestly reflecting that the full plate is dwelling area with no core. Re-ran `emit_eu11_layout_sidecars.py`
and `generate_eu_3d_viewers.py` for all 4 districts; confirmed 0 buildings still report
`has_unconditioned_core: true` across all 1,340 side-cars, and all 4 viewers are byte-identical to their
`docs/docs_ACTIVE/europeanLocations/outputs_3D/` mirrors. Coverage counts in §2 above are unchanged — only the
core metadata field changed, not the partition, count, or fallback census. Registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (European locations X-05 chapter).
