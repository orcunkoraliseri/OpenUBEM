# `RESULTS_EU-12` — Dwelling Layout Sidecars, Zoning Emission Census, and Viewer Floor-Plan Pop-Ups

- **Date**: 2026-08-28
- **Work Package**: `EU-12` (European Locations × Step 8 / 3D Visualization)
- **Status**: `COMPLETED`
- **Output Artifacts**:
  - `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/layouts/<building_id>.json`
  - `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/<district_slug>_manifest.csv` (updated with `layout_json`)
  - `openubem/outputs/3D/eu_<DISTRICT>_viewer.html` & `eu_<DISTRICT>_data/`
  - `docs/docs_ACTIVE/europeanLocations/outputs_3D/` (byte-identical mirrors)

---

## 1. Executive Summary

`EU-12` closes the gap where procedural dwelling subdivisions were previously computed during simulation model assembly and discarded without persistence. Layout side-car JSONs have been generated for all simulated buildings across the European district campaign, recording exact zone geometries, zoning outcome codes, fallback failure reasons, and partition audits. Furthermore, all four European 3D district viewers have been upgraded with an interactive, offline 2D floor-plan pop-up modal.

---

## 2. Per-District Layout Outcome Census

| District | Cell ID | Residential Buildings | Simulated in EU-11 | Dwelling Layout Emitted | Massing-Box Fallback | Not Simulated | Layout Emission Rate (Simulated) |
|---|---|---|---|---|---|---|---|
| **Madrid — Berruguete** | `ES-MAD-BERRUGUETE` | 1,194 | **961** | **51** | **910** | 233 | 5.3% (51 / 961) |
| **Lyon — Haut Cœur des Pentes** | `FR-LYO-HAUTCOEURPENTES` | 530 | **297** | **0** | **297** | 233 | 0.0% (0 / 297) |
| **London — St Dunstan's** | `GB-LDN-STDUNSTANS` | 1,242 | **82** | **0** | **82** | 1,160 | 0.0% (0 / 82) |
| **Bologna — Galvani 2** | `IT-BOL-GALVANI2` | 1,220 | **0** | **0** | **0** | 1,220 | N/A (0 eligible) |
| **Total European Corpus** | — | **4,186** | **1,340** | **51** | **1,289** | **2,846** | **3.8%** (51 / 1,340) |

---

## 3. Census of Distinct Fallback Reasons

Every non-emitting simulated building fails closed with an explicit, named reason registered in its side-car JSON:

| Fallback Reason Code | Madrid (`ES`) | Lyon (`FR`) | London (`GB`) | Bologna (`IT`) | Total Buildings | Description / Mechanism |
|---|---|---|---|---|---|---|
| `NON_CONVEX_TOPOLOGY_UNSUPPORTED` | 609 | 0 | 0 | 0 | **609** | Footprint boundary has concave angles / re-entrant corners (`openubem/geometry/european_residential.py:493`). |
| `NARROW_FOOTPRINT_LT_8M` | 183 | 0 | 0 | 0 | **183** | Footprint bounding width along either axis is `< 8.0 m` (`:478`). |
| `COURTYARD_TOPOLOGY_UNSUPPORTED` | 115 | 0 | 0 | 0 | **115** | Footprint contains interior holes / lightwells / courtyard topology (`:491`). |
| `MISSING_OBSERVED_DWELLING_COUNT` | 3 | 297 | 82 | 0 | **382** | No per-building dwelling count available in open source to determine `units_per_floor`. |
| `NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE` | 0 | 0 | 0 | 1,220 | **1,220** | Pre-simulation blocker: no construction year in open catalogues (`EU11_Bologna_construction_year_investigation.md`). |
| *None (Emitted Layout)* | 51 | 0 | 0 | 0 | **51** | Clean convex, non-courtyard, broad footprint with valid dwelling allocation and passed partition audit. |
| **Total** | **961** | **297** | **82** | **1,220** | **2,560** | |

---

## 4. Architectural Findings

### FINDING EU-12-01: Single-Storey Emission in Emitted Layout Path
- **Observation**: In `scripts/run_eu_s2_district_campaign.py:113-117` and `openubem/geometry/european_residential.py:555-588`:
  ```python
  if layout.dwelling_layout_emitted:
      zones = european_layout_to_zone_specs(layout, building_id=row["building_id"], height_m=FLOOR_TO_FLOOR_M)
  else:
      zones = build_zones(row["building_id"], footprint, row["archetype_id"], n_storey, "one_zone_per_floor", FLOOR_TO_FLOOR_M)
  ```
  `european_layout_to_zone_specs` executes with default `floor_index=0` and produces only the ground floor dwelling zones (`F0_dwelling_0`, `F0_dwelling_1`, ...). The massing-box fallback (`build_zones`) explicitly stacks `n_storey` zones (`F0`, `F1`, ... `F_{n-1}`).
- **Consequence**: Emitted multi-storey buildings in the EU-11 simulation run had 1 storey of extruded dwelling zones rather than an `n_storey` vertical stack.
- **Reporting Rule**: In accordance with prompt §2, this is reported as an empirical finding without modifying the underlying physics or re-deriving geometries. The side-car JSONs accurately record `floors: [{"storey_index": 0, "dwelling_count": ...}]`, and the viewer pop-up explicitly displays: *"Storey 0 shown (1 storey emitted in geometry pipeline)."*

### FINDING EU-12-02: Emitted Layout Scheme vs. Conceptual Design
- **Observation**: The procedural generator implements an **equal-strip partition on the long axis** (`generate_european_dwelling_layout`: footprint rotated onto its long axis, sliced into equal width strips, rotated back, and audited for $\ge 2.5\text{ m}$ exterior facade contact).
- **Distinction**: It is **not** the point-block core scheme or the double-loaded corridor scheme depicted in conceptual figures (e.g. MVP Figure 4.2). The pop-up panel explicitly labels the scheme as emitted (`equal-strip partition on the long axis`) and clarifies this distinction.

---

## 5. Deliverables & Data Folder Contract Verification

1. **Layout Side-Car JSONs**:
   - Emitted to `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/layouts/<building_id>.json` (961 ES, 297 FR, 82 GB).
   - `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/<district_slug>_manifest.csv` updated with relative `layout_json` path.
2. **Interactive 3D Viewers with Pop-Up Modal**:
   - `eu_ES-MAD-BERRUGUETE_viewer.html`
   - `eu_FR-LYO-HAUTCOEURPENTES_viewer.html`
   - `eu_GB-LDN-STDUNSTANS_viewer.html`
   - `eu_IT-BOL-GALVANI2_viewer.html`
   - Clicking any building opens a 2D floor-plan pop-up modal showing footprint outline, dwelling zone subdivisions, zone names, pastel coloring, metric scale bar, North arrow, archetype metadata, and explicit fallback reasons.
   - HUD updated with live counts for residential, excluded, dwelling layout emitted, massing-box fallback, and not simulated.
   - Fully self-contained, dependency-free vanilla Canvas engine with zero network calls and `Esc` key dismissal.
3. **Data Folder Contract (`eu_<DISTRICT>_data/`)**:
   - `buildings.csv`: Per-building summary with `height_source`, `eui_kwh_m2`, `eui_status`, and `geometry_outcome`.
   - `results.csv`: Simulated EUI and geometry outcome for successful runs (absent for Bologna).
   - `results_source.csv`: Untouched copy of the EU-11 manifest including `layout_json` (absent for Bologna).
   - `layouts/`: Complete directory of layout side-car JSON files.
   - `sources.json`: Input artifact SHA-256 digests, Speed platform metadata, and layout coverage statistics.
   - `index.html`: Open dataset documentation page linking to all files.
4. **Mirroring**:
   - Primary: `openubem/outputs/3D/`
   - Mirror: `docs/docs_ACTIVE/europeanLocations/outputs_3D/` (100% byte-identical across all HTML files and data directories).
