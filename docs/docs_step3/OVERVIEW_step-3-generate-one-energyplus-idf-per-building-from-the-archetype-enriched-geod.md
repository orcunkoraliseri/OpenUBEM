# OVERVIEW — Step 3 — OSM Archetype-Enriched GeoDataFrame → One EnergyPlus IDF per Building
### OpenUBEM Stage 3 / Modules 07–11 — convert the 57-column enriched GeoDataFrame into one self-contained EnergyPlus 23.1 IDF per simulation building

> **Slug:** `step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod.md` &nbsp;•&nbsp; **Generated:** `2026-05-07`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §11.

---

## AIM

Step 3 takes the 57-column archetype-enriched GeoDataFrame (Steps 1–2 + Modules 02/04/05/06) and emits one self-contained EnergyPlus 23.1 `<osm_id>.idf` per simulation building, ready for the Stage 4 parallel runner. It is the bridge between semantic enrichment and executable simulation — every Stage 1–2 column exists so Step 3 can compose a syntactically valid, EnergyPlus-runnable model. Inputs/outputs are governed by architectural invariants I1 (one IDF per building), I3 (locked IDD at module import), I4 (Douglas-Peucker 0.5 m before geomeppy), I6 (persistent intermediates per stage).

---

## PIPELINE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  3A — Footprint Simplification (Module 07)                                   ║
║  Inputs:    raw OSM polygon (UTM metres)                                     ║
║  Operation: 4-tier fallback DP 0.5 → DP 1.5 → convex hull → bbox; ≤120 verts ║
║  Output:    simplified Polygon + updated data_quality_flag + status token    ║
║  Validation: pct_vertex_compliant = 100%; pct_fallback_bbox ≤ 5%             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3B — Thermal Zone Stratification (Module 08)                                ║
║  Inputs:    simplified polygon, archetype_id, area, num_floors               ║
║  Operation: rule-table routing → single_zone / one_zone_per_floor /          ║
║             perimeter_core (4.57 m ASHRAE 90.1 Appendix G); narrow→fallback  ║
║  Output:    list[zone_dict] with name, polygon, z_floor/z_ceiling, archetype ║
║  Validation: all zone names unique; perimeter_core core_area > 10 m²         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3C — Context Building Discovery (Module 08b)                                ║
║  Inputs:    simplified polygon + full GeoDataFrame                           ║
║  Operation: STRtree query within 30 m sphere; bbox of neighbours; translate  ║
║  Output:    list[shading_dict] for Shading:Building:Detailed (NOT zones)     ║
║  Validation: mean_shading_context_count in 3–12 (Boston 500 m fixture)       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3D — IDF Initialisation (Module 09: builder.py)                             ║
║  Inputs:    archetype_id, EPW path                                           ║
║  Operation: lock IDD once (I3); load 1-of-4 base template; populate          ║
║             Site:Location from EPW header; Activity_Level Schedule embedded  ║
║  Output:    GeomIDF instance ready for geometry/loads/HVAC/output assembly   ║
║  Validation: IDD locked; eppy.IDF.read() passes                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3E — 3D Geometry Extrusion (Module 10: surfaces.py)                         ║
║  Inputs:    zone dicts + context dicts                                       ║
║  Operation: geomeppy add_block per zone; intersect_match ONCE; add_shading_  ║
║             block per neighbour (after intersect_match)                      ║
║  Output:    BuildingSurface:Detailed objects with correct normals + bndry    ║
║  Validation: all zones have ≥6 surfaces; no orphan boundary conditions       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3F+3G — Constructions, Loads, Schedules (Module 09 / Module 10)             ║
║  Inputs:    enriched-row Module 04 + 05 + 06 columns                         ║
║  Operation: Material:NoMass + SimpleGlazingSystem (U+SHGC); set_wwr;         ║
║             per-zone People/Lights/Equip/Thermostat keyed by archetype       ║
║             schedule library; NaN year_built→DOERefPre1980 permissive        ║
║  Output:    fully populated zone heat-balance objects                        ║
║  Validation: no unresolved schedule names; SHGC ∈ [0,1]                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3H+3I — HVAC + Outputs (Module 10b / Module 11)                             ║
║  Inputs:    zones list                                                       ║
║  Operation: HVACTemplate:Zone:IdealLoadsAirSystem per zone (Phase-1);        ║
║             Hourly Output:Variable; RunPeriod Output:Meter:MeterFileOnly;    ║
║             OUTPUT:SQLITE SimpleAndTabular                                   ║
║  Output:    self-contained <osm_id>.idf written to disk                      ║
║  Validation: 100% IDF syntax-valid; 100% synthetic-fixture dry-run completes ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| Input rows                       | N (Step 2 enriched GDF, 57 cols)        | DESIGN §2 |
| Output IDFs                      | 1 per `osm_id` (success rows only)      | DESIGN §4 |
| Output manifest columns          | 9                                       | DESIGN §4 |
| EnergyPlus version               | 23.1 (locked)                           | DESIGN §3D, invariant I3 |
| Per-surface vertex limit         | 120                                     | DESIGN §3A, invariant I4 |
| DP simplification tolerance      | 0.5 m (Tier 1), 1.5 m (Tier 2)          | DESIGN §3A |
| Floor-to-floor height default    | 3.5 m                                   | DESIGN §3A |
| Perimeter depth (Appendix G)     | 4.57 m                                  | DESIGN §3B |
| Shading sphere radius            | 30.0 m default (20–60 m configurable)   | DESIGN §3C |
| Run period                       | 8760 h annual, 6 timesteps/hour         | DESIGN §3D |
| Activity level (Schedule:Const)  | 120 W/person (ASHRAE 55 sedentary)      | DESIGN §3D |
| OA flow per person (62.1 min)    | 0.01 m³/s·person                        | DESIGN §3H |
| GPU hours                        | 0 (pure CPU)                            | DESIGN §6 |
| Wall-clock target (Boston 500 m) | < 60 s on ~400 buildings                | DESIGN §6 |
| Storage per IDF                  | ~200 KB (50–500 KB range)               | DESIGN §6 |
| Open Questions                   | 7                                       | DESIGN §7 |

---

## VALIDATION SUMMARY

- `pct_valid_idf_generated`: **≥ 95%** of input buildings produce valid IDF (Boston 500 m target)
- `pct_vertex_compliant`: **100%** (≤ 120 verts per BuildingSurface:Detailed — hard E+ requirement)
- `pct_fallback_bbox`: **≤ 5%** — exceeded ⇒ DP tolerance miscalibrated for fixture
- IDF syntax validity: **100%** pass `eppy.modeleditor.IDF.read()` (cheap CI gate, no E+ binary)
- EnergyPlus dry-run: **100%** of synthetic 10-building fixture complete 1-day run with no fatal
- Building-level CV(RMSE): **< 30%** vs CBECS 2018 New England EUI (ASHRAE Guideline 14)
- Neighbourhood NMBE: **±10%** (ASHRAE Guideline 14 mean-bias-error)
- True Future Test: not applicable (deterministic transformation; no model trained on data). Boston 500 m is held out from any Module 06b training set — true OOD evaluation of the upstream pipeline.

---

## KEY DECISIONS

> Mirrors DESIGN §9 — same rows, one line each.

| Decision | Rationale (one line) |
|---|---|
| Douglas-Peucker 0.5 m + 4-tier fallback chain (DP 1.5 → convex hull → bbox) with data_quality_flag annotation | Invariant I4; preserves wall-azimuth while honouring 120-vertex E+ limit; pathological footprints get a guaranteed valid fallback. |
| Three zoning strategies (single_zone / one_zone_per_floor / perimeter_core) routed by archetype × area × num_floors | Balances fidelity vs compute; ASHRAE 90.1 Appendix G prescriptive for large commercial; OpenUBEMUnknown→max-entropy single_zone. |
| geomeppy add_block + intersect_match (called once after all zones) | Auto-generates correct surface normals and inter-zone boundary pairing; per-zone bbox fallback preserves the building on geomeppy exception. |
| Shading:Building:Detailed bbox boxes (NOT zones) within 30 m sphere using STRtree query | Captures urban-canyon radiant exchange without breaking invariant I1; bbox over-estimation is the conservative direction. |
| HVACTemplate:Zone:IdealLoadsAirSystem as Phase-1 default | Eliminates HVAC-system calibration uncertainty; isolates envelope/internal-load signal — the Phase-1 EUI target. |
| Single canonical output frequency: Hourly for Output:Variable, RunPeriod for meters; SQL enabled | Hourly is the minimum for IOD + peak demand; SQL gives Stage 5 a stable schema; uniform freq prevents Stage-5 alignment bugs. |
| NaN year_built → DOERefPre1980 permissive (provenance HEURISTIC, token VINTAGE_NAN_PERMISSIVE_DEFAULT) | Older-envelope direction prevents systematic envelope-quality overstatement and heating-EUI understatement on retrofit-relevant stock. |

---

## OPEN QUESTIONS

- **OQ-1** — Quantify R² / CV(RMSE) improvement of `one_zone_per_floor` vs `single_zone` on Boston 500 m residentials. *(blocks §3B, §5.1)*
- **OQ-2** — Mean absolute WWR error vs CBECS 2018 glazing data; cooling-EUI impact of uniform-WWR Phase-1 assumption. *(blocks §3F)*
- **OQ-3** — Infiltration-model heating-EUI bias vs CBECS/RECS by ASHRAE climate zone. *(blocks §3F)*
- **OQ-4** — Confirm Module 05's `equipment_w_m2` matches DOE DataCenter prototype IDF ITE W/m² for HighITE variants. *(blocks §3G)*
- **OQ-5** — Phase-2: orientation-specific WWR via `set_wwr(wwr_map=...)` once per-orientation glazing data exists. *(Phase-2 §3F extension)*
- **OQ-6** — Confirm 4.57 m perimeter depth doesn't trigger narrow-building fallback for >5% of Boston commercial buildings. *(blocks §5.1)*
- **OQ-7** — Module 02 (`acquisition/climate_zone.py` + `epw_manager.py`) is undesigned — required for end-to-end integration testing. *(blocks full integration test)*
