# OVERVIEW — Step 5 — EnergyPlus Work Directories → EUI / GWP / IOD Results GeoDataFrame
### OpenUBEM Stage 5 / Modules 13–16 — parse per-building `eplusout.sql`, compute EUI/GWP/IOD, join back onto the 57-column GeoDataFrame, export `05_results.{gpkg,geojson,csv}` — the pipeline's final deliverable

> **Slug:** `step-5-parse-energyplus-outputs-into-eui-gwp-iod-and-aggregate-results-back-to-th` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_step-5-parse-energyplus-outputs-into-eui-gwp-iod-and-aggregate-results-back-to-th.md` &nbsp;•&nbsp; **Generated:** `2026-06-09`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §11.

---

## AIM

Step 5 converts the fleet of Step 4 work directories into OpenUBEM's final deliverable: a 70-column results GeoDataFrame where every building carries five EUI metrics (kWh/m²/yr), five GWP metrics (kg CO₂e/m²/yr), an IOD (°C), and a simulation status — exported as GPKG (canonical, UTM), GeoJSON (EPSG:4326), and CSV, plus a neighbourhood summary JSON. It is also where the umbrella validation thresholds (CV(RMSE) < 30%, NMBE ±10%, R² > 0.6, KS D < 0.10 vs CBECS 2018) are actually computed. Governing principles: flag-don't-drop through the final join (failed buildings stay visible with NaN metrics), single J→kWh conversion at the parse boundary, byte-identical pass-through of the 57 upstream columns, and an explicitly tagged `load_referenced_v1` GWP convention.

---

## PIPELINE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  3A — SQL Extraction (Module 13: parser.py)                                  ║
║  Inputs:    04_simulation_manifest.parquet (status ∈ success*) + eplusout.sql║
║  Operation: stdlib sqlite3 read-only; one bulk query over ReportData/        ║
║             ReportDataDictionary/Time; J→kWh ONCE at parse boundary;         ║
║             CSV fallback flagged RESULTS_CSV_FALLBACK; failed_parse if both  ║
║  Output:    per-building hourly long-frame (kWh / °C)                        ║
║  Validation: pct_parse_success ≥ 99%                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3B — Zone-Name Resolution (Module 13)                                       ║
║  Inputs:    SQL KeyValue strings (E+ uppercased, geomeppy Block/Storey wrap) ║
║  Operation: regex-parse Step 3 contract {osm_id}_F{n}_{WHOLE|CORE|PERIM};    ║
║             foreign osm_id in a work dir ⇒ ABORT RUN (I2 violation);         ║
║             zone count ≠ manifest num_zones ⇒ failed_zone_mismatch (local)   ║
║  Output:    zone→(osm_id, floor, label) mapping — no auxiliary map file      ║
║  Validation: zone-count integrity 100% of parsed buildings                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3C — Building EUI (Module 13)                                               ║
║  Inputs:    hourly zone energy + footprint_area_m2 + derive_num_floors()     ║
║  Operation: Σ zones × 8760 h → annual kWh ÷ (footprint × floors); floors via ║
║             the SAME function Step 3 used (imported, never re-implemented)   ║
║  Output:    heating/cooling/lighting/equipment/total EUI (load-referenced)   ║
║  Validation: ABUPS cross-check ±0.5%; meter closure ±1%; gas meter = 0       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3D — IOD (Module 13)                                                        ║
║  Inputs:    operative temp + occupant count + site drybulb (ALL from SQL)    ║
║  Operation: Tn=0.31·Tave+17.8; Tcomf=Tn+2.5; mean excess over occupied       ║
║             summer hours (Jun 1–Sep 30, ASSUMPTION_DESIGN_DEFAULT);          ║
║             occupant-weighted; never-occupied ⇒ NaN + IOD_NO_OCCUPIED_HOURS  ║
║  Output:    iod (°C) per building                                            ║
║  Validation: exact match vs hand-computed golden-SQL fixture                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3E — GWP (Module 15: carbon.py)                                             ║
║  Inputs:    EUI columns + egrid_2022.json (state → subregion factor)         ║
║  Operation: heating × 0.181 (gas, Iseri et al. 2025); cooling/lighting/      ║
║             equipment × eGRID electricity factor; load_referenced_v1         ║
║             convention tagged in every export                                ║
║  Output:    5 GWP columns (kg CO₂e/m²/yr)                                    ║
║  Validation: convention tag present; factors traceable to bundled JSON      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3F — Spatial Join + Aggregation (Module 14: aggregator.py)                  ║
║  Inputs:    metrics rows + 57-column enriched GDF                            ║
║  Operation: LEFT join on osm_id appending exactly 13 columns; 57 upstream    ║
║             byte-identical; flag-don't-drop; floor-area-weighted             ║
║             neighbourhood EUI; pct_floor_area_simulated honesty metric       ║
║  Output:    (N_input, 70) results GDF + 05_neighbourhood_summary.json        ║
║  Validation: row count == N_input; EUI plausibility [25, 1000] for ≥99%      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3G — Export + Visualization (Module 14 / Module 16)                         ║
║  Inputs:    results GDF                                                      ║
║  Operation: 05_results.gpkg (UTM, CANONICAL) + .geojson (EPSG:4326 at        ║
║             export only) + .csv (centroid lon/lat); 3 matplotlib figures —   ║
║             observability-only, non-binding; failed buildings hatched grey   ║
║  Output:    final deliverable files + figures/                               ║
║  Validation: CV(RMSE)<30%, NMBE ±10%, R²>0.6, KS D<0.10 vs CBECS 2018        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| Input manifest rows               | N_input (filter: status ∈ {success, success_cached}) | DESIGN §2 |
| Output GDF shape                  | (N_input, 70) = 57 byte-identical + 13 appended | DESIGN §3F, §4 |
| Appended columns                  | 5 EUI + 5 GWP + iod + simulation_status + error_summary | DESIGN §3F |
| J→kWh conversion                  | 1/3.6e6, applied exactly once (§3A)        | DESIGN §3A |
| Natural-gas GWP factor            | 0.181 kg CO₂e/kWh (Iseri et al. 2025)      | DESIGN §3E |
| Electricity GWP factor            | eGRID 2022, state → subregion              | DESIGN §3E |
| GWP convention                    | `load_referenced_v1` (tagged in exports)   | DESIGN §3E |
| IOD formula                       | Tn = 0.31·Tave + 17.8; Tcomf = Tn + 2.5    | DESIGN §3D |
| IOD summer window                 | Jun 1–Sep 30 (`ASSUMPTION_DESIGN_DEFAULT`) | DESIGN §3D, OQ-4 |
| EUI plausibility envelope         | [25, 1000] kWh/m²/yr (flag, don't drop)    | DESIGN §5.1 |
| Per-building parse time           | ~1–3 s (5–20 MB SQL)                       | DESIGN §6 |
| Wall-clock target (Boston 500 m)  | < 15 min single-core end-to-end            | DESIGN §6 |
| Peak memory                       | < 4 GB                                     | DESIGN §6 |
| GPU hours                         | 0 (pure CPU)                               | DESIGN §6 |
| Open Questions                    | 6                                          | DESIGN §7 |

---

## VALIDATION SUMMARY

- `pct_parse_success`: **≥ 99%** of success-status sims parse from SQL without fallback or failure
- ABUPS cross-check: hourly-summed annual electricity matches EnergyPlus's own tabular total within **±0.5%** (validates J→kWh + summation)
- Meter closure: Σ(Lights + Equipment hourly) = `Electricity:Facility` RunPeriod meter within **±1%**
- Gas-meter zero check: `NaturalGas:Facility` = **0** for 100% of buildings (IdealAir IDFs have no gas equipment — non-zero ⇒ Step 3 template contamination)
- Zone-count integrity: resolved zones = manifest `num_zones` for **100%** of parsed buildings
- EUI plausibility: `total_eui_kwh_m2` ∈ [25, 1000] for **≥ 99%** of success rows (outliers flagged, never dropped)
- Building-level CV(RMSE): **< 30%** vs CBECS 2018 New England (ASHRAE Guideline 14; design_state row 36)
- Neighbourhood NMBE: **±10%**; archetype R²: **> 0.6**; KS D: **< 0.10** (same anchor)
- IOD spot check: **exact** match against hand-computed golden-SQL fixtures
- True Future Test: Step 5 is deterministic, but adjudicates the pipeline's generalization claim — leak-free by construction: Boston held out from all upstream training; CBECS shares no provenance with the ASHRAE/IECC/DOE-Prototype parameter sources.

---

## KEY DECISIONS

> Mirrors DESIGN §9 — same rows, one line each.

| Decision | Rationale (one line) |
|---|---|
| SQL-first parsing via stdlib `sqlite3` (read-only, one bulk query); CSV demoted to flagged fallback | Structured and schema-stable with zero new dependencies; header-regex CSV parsing is fragile. |
| Single J→kWh conversion at the parse boundary — a Joule never exists past §3A | Eliminates the classic mixed-unit UBEM bug by construction. |
| Zone→building mapping by parsing the Step 3 zone-name contract; foreign osm_id aborts the run, count mismatch quarantines the building | The naming contract *is* the mapping; severity asymmetry matches systemic (I2 breach) vs local (naming drift) failure. |
| EUI denominator = observed `footprint_area_m2` × `derive_num_floors()` imported from Step 3's module | Denominator matches the simulated geometry with no logic drift, while staying referenced to real-world floor area for CBECS comparability. |
| IOD from SQL-internal series only; occupant-weighted; never-occupied ⇒ NaN + `IOD_NO_OCCUPIED_HOURS` | References exactly the simulated weather; measures person-experienced overheating; "no data" is never encoded as "no overheating". |
| Five-column per-end-use GWP under an export-tagged `load_referenced_v1` convention (gas 0.181 heating; eGRID electricity elsewhere; no η/COP) | Preserves regional + end-use carbon signal (design_state row 39); the tag makes the load-vs-fuel limitation auditable instead of silent. |
| Left join appending exactly 13 columns; 57 upstream columns byte-identical; flag-don't-drop; floor-area-weighted neighbourhood EUI + `pct_floor_area_simulated` | Survivorship bias is the canonical UBEM reporting error — aggregates declare their own completeness. |
| GPKG (UTM) canonical + GeoJSON (EPSG:4326 at export only) + CSV; figures observability-only | Metric CRS survives for analysis; GeoJSON honours its WGS84 mandate; non-binding figures evolve freely. |

---

## OPEN QUESTIONS

- **OQ-1** — Extract the CBECS 2018 New England EUI reference into `inputs/` (blocks the four headline validation gates). *(blocks §5.1)*
- **OQ-2** — GWP convention end-state: confirm Iseri et al. (2025) η/COP treatment; decide `load_referenced_v1` → fuel-referenced `v2` for Phase 1.5. *(blocks §3E refinement)*
- **OQ-3** — Canonical owner of the `state` column for eGRID lookup (natural home: Module 02 county join; interim: centroid join vs bundled US-states layer). *(blocks §3E integration)*
- **OQ-4** — Climate-zone-aware IOD summer window (Jun–Sep default wrong at zone extremes 1A / 7–8). *(blocks §3D calibration)*
- **OQ-5** — Module 02 undesigned — same blocker chain as Step 3 OQ-7 / Step 4 OQ-5. *(blocks full integration test)*
- **OQ-6** — Confirm downstream eSim surrogate-training column needs (e.g. absolute kWh) before the 70-column schema freezes. *(blocks §4 schema freeze)*
