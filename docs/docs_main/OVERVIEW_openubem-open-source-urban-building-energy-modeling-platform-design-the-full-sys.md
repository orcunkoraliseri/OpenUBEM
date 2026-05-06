# OVERVIEW — OpenUBEM: Open-Source Urban Building Energy Modeling Platform

> **Slug:** `openubem-open-source-urban-building-energy-modeling-platform-design-the-full-sys` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_openubem-open-source-urban-building-energy-modeling-platform-design-the-full-sys.md` &nbsp;•&nbsp; **Generated:** `2026-05-02`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §12.

---

## AIM

OpenUBEM is a fully open-source, pip-installable, scriptable Python library that takes a city name, bounding box, or coordinate pair and runs the entire UBEM pipeline — OSM ingest → ASHRAE/IECC archetype assignment → eppy/geomeppy IDF generation → parallel EnergyPlus simulation → spatial GeoDataFrame export — with no proprietary dependencies, no GUI, and no hidden intermediate state. It generalises the Iseri et al. (2025, Energy & Buildings 337, 115620) probabilistic UBEM methodology from a Bahçelievler case study to American cities, with Phase 3 hooks for Canada (NECB) and Europe (TABULA).

---

## PROBLEM SOLVED — gap vs. existing tools

Every dominant UBEM tool today imposes a structural barrier on a researcher trying to script an end-to-end run: **CEA** (ArcGIS-tied, European Archetypes DB, custom RC), **UMI/UBEM.io** (Rhino plug-in, GUI-only), **URBANopt** (Ruby SDK, OpenStudio CLI), **TEASER** (Modelica/Dymola), **CityBES** (closed web), **SimStadt/CitySim/OpenIDEAS** (CityGML/Modelica, GUI). OpenUBEM is the missing piece: pure-Python, OSM-driven, IDF-transparent, three lines of code from `pip install` to results.

---

## STEPS

```
┌──────────────────────────────────────────────────────────────────────────┐
│ STAGE 1 — Data Acquisition (acquisition/)                                │
│   Inputs:    location (str | tuple) OR .osm path; radius_m               │
│   Output:    buildings_gdf (UTM, ≥20 m²) + climate_zone + epw_path       │
│   Method:    osmnx ≥ 1.9 fetch → estimate_utm_crs → ASHRAE zone GPKG     │
│              spatial join → EPW resolution (cache → climate.onebuild.)   │
│   Validation: 50-city zone tuple = 100%; EPW found for all US lat/lon    │
│   Rationale: OSM is the only open, global, pip-fetchable building source │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STAGE 2 — Semantic Enrichment (semantic/)                                │
│   Inputs:    buildings_gdf + climate_zone                                │
│   Output:    enriched_gdf (+ building_type, U-values, loads, schedules,  │
│              provenance_<param>)                                         │
│   Method:    rule-based OSM→OpenStudio30 classifier; ASHRAE 90.1-2019 /  │
│              IECC 2021 / DOE prototype JSON lookups; KDE/PDE/ML impute   │
│   Validation: KS D < 0.10 (KDE); 100% bounds (PDE); ±5% DOE round-trip   │
│   Rationale: standards-driven baseline auditors accept; zero pre-train   │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STAGE 3 — IDF Generation (geometry/ + idf/)                              │
│   Inputs:    enriched_gdf rows                                           │
│   Output:    one IDF per building → output_dir/idfs/<osm_id>.idf         │
│   Method:    Douglas-Peucker 0.5 m simplification (≤120 verts) →         │
│              zoning (single | per-floor | perim+core) → geomeppy extrude │
│              → IdealAir HVAC default → Shading:Building:Detailed context │
│              (30 m sphere of influence)                                  │
│   Validation: ≥98% IDFs pass EnergyPlus design-day smoke test (zero sev) │
│   Rationale: one-IDF-per-building (I1) enables embarrassingly-parallel   │
│              re-simulation and granular failure diagnosis                │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STAGE 4 — Simulation (simulation/)                                       │
│   Inputs:    {*.idf}, epw_path, n_jobs                                   │
│   Output:    {results/<osm_id>/eplusout.sql, .csv, .err, tables}         │
│   Method:    joblib.Parallel(backend='loky') dispatching per-building    │
│              EnergyPlus subprocesses, isolated work_dir/<osm_id>/ (I2);  │
│              IDD locked at import (I3); SLURM array jobs for HPC scale   │
│   Validation: ≥95% success rate on 200-bldg Boston fixture; ≤30 min/32c  │
│   Rationale: loky bypasses GIL, survives crashes, eppy-community std.    │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STAGE 5 — Results & Carbon (results/)                                    │
│   Inputs:    {results/<osm_id>/eplusout.sql}                             │
│   Output:    results_gdf → openubem_results.{geojson,gpkg,csv}           │
│              (EUI per end-use, GWP per end-use, IOD, simulation_status)  │
│   Method:    SQL parse → compute_eui (annual kWh/m²) → compute_iod       │
│              (ASHRAE 55 adaptive) → compute_gwp (eGRID 2022 + 0.181 NG)  │
│              → left-join on osm_id; provenance preserved end-to-end      │
│   Validation: ±10% Iseri 2025 Bahçelievler; CV(RMSE) <30%, NMBE ±10%,    │
│              R² >0.6 vs BPD                                              │
│   Rationale: per-end-use carbon attribution exceeds spec's electricity-  │
│              only bucket; full IDF transparency throughout               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| DOE Prototype Buildings library | 16 commercial × 8 climate zones × 5 vintages ≈ 5,168 baseline IDFs | DESIGN §1 |
| OpenStudio 30-type taxonomy | 30 building-type labels | DESIGN §5.3 |
| Footprint vertex limit (EnergyPlus) | ≤ 120 per surface | DESIGN §4.3 (I4) |
| Footprint area threshold | ≥ 20 m² (drop OSM noise) | DESIGN §5.1 |
| Shading sphere of influence | 30 m default (20–60 m configurable) | DESIGN §5.5 |
| Per-building EnergyPlus cost (mean) | ~ 15 s on 1 core, IdealAir, 8760 h | DESIGN §9.1 |
| Boston Downtown 500 m worked example | ~ 400 buildings, ~ 4 min on 32 cores | DESIGN §9.2 |
| Full Boston city scale | ~ 90,000 buildings, ~ 25 min on 32 nodes × 32 cores | DESIGN §9.2 |
| Phase-1 HPC core-hour ceiling | 2,000 core-hours/month (Calcul Québec) | DESIGN §9.3 |
| Disk per building (raw EnergyPlus) | 5–20 MB before parse | DESIGN §9.5 |
| Provenance codes | 6 (OSM_OBSERVED, ASHRAE_STANDARD, KDE_IMPUTED, PDE_GENERATED, ML_PREDICTED, HEURISTIC) | DESIGN §4.3 (I5) |

---

## KEY DECISIONS (one-liners)

1. **One IDF per building (never combined)** — parallel jobs cannot share a file; isolates failures; enables re-running just changed buildings.
2. **joblib + loky backend** — eppy-community standard; survives worker crashes; lighter than Dask for embarrassingly-parallel subprocess dispatch.
3. **KDE / PDE / ML imputation tier** — direct port of Iseri et al. (2025); preserves empirical distribution (KDE) or maximum-entropy uniform (PDE) without parametric bias.
4. **ASHRAE 90.1-2019 + IECC 2021 + DOE Prototype + eGRID 2022 stack** — Phase-1 US scope eliminates need for custom data collection before modelling can begin.
5. **OSM canonical input via osmnx ≥ 1.9** — only open, pip-fetchable, global building source; CityGML deferred to Phase 3+.
6. **geomeppy ≥ 0.11.8 on eppy ≥ 0.5.63** — open-source procedural geometry; rejects Honeybee/Dragonfly (Rhino) and proprietary CAD paths.
7. **EnergyPlus subprocess (open-source)** — rejects RC core (CEA/TEASER): RC defeats standards generalisation and hides Output:Variable transparency.
8. **Annual 8760 h hourly run** — gold standard for EUI/IOD; representative-day approaches lose hourly fidelity needed for downstream surrogate training.
9. **Rule-based archetype classification (Phase 1)** — zero-pre-training-data path; ML/clustering deferred to Phase 2 with interface-stable replacement.
10. **Shading:Building:Detailed boxes (NOT zones)** — captures up to 3.6% canyon radiant exchange without exploding IDF size.
11. **Seven binding architectural invariants (I1–I7)** — one-IDF, isolated work_dir, locked IDD, vertex simplification, provenance, persistent intermediates, no proprietary deps.
12. **Four-end-use GWP schema** — heating, cooling, lighting+equipment electricity, total (refines spec's three-bucket version).

(For full rationale + alternatives rejected → DESIGN §3, §7, §8.5, §9.4.)

---

## VALIDATION SUMMARY

Four-level hierarchy:

- **Level 1 — Unit tests**: 100% IDFs ≤120 verts; KS D <0.10 KDE; 100% PDE in bounds; design-day smoke test zero severe errors.
- **Level 2 — DOE Prototype round-trip**: **±5% on `total_eui_kwh_m2`** (16 prototypes × 5 climate zones, IdealAir).
- **Level 3 — Iseri 2025 Bahçelievler replication**: **±10% on per-building annual heating EUI** (24 buildings, same EPW + construction inputs).
- **Level 4 — City-scale BPD calibration**: **CV(RMSE) < 30%** building, **NMBE ±10%** neighbourhood, **R² > 0.6** archetype-level (Boston, Chicago, Phoenix, Seattle worked examples).
- Spatial scaling: building CVRMSE <30% → block NMBE ±15% → neighbourhood NMBE ±10% → city-aggregated NMBE ±5%.

Ground truth: DOE Prototypes (Level 2), Iseri 2025 supp data (Level 3), U.S. Building Performance Database >1M records + CBECS/RECS (Level 4).

Rejected: Bayesian calibration loop (requires per-building utility data, violates "no hidden state"); IoT sensor coupling (outside open-data charter).

---

## TARGET USERS & DEPLOYMENT

Researchers, urban planners, and sustainability consultants in the Concordia / NSERC / Calcul Québec ecosystem. Three-line minimum usage:

```python
import openubem
results = openubem.run_ubem('Downtown Boston, MA', radius_m=500)
print(results[['building_type', 'total_eui_kwh_m2', 'gwp_total_kgco2_m2']])
```

CLI: `main_openubem.py --location ... --radius ... --mode {deterministic|probabilistic} --n_jobs ...`. HPC: same code on Calcul Québec via SLURM array jobs (one task per ~100-building spatial chunk, `--cpus-per-task=32`, `--mem=64G`). Distribution: pip + Zenodo DOI + JOSS software paper. License: MIT.

---

## PHASE ROADMAP

| Phase | Scope | Status |
|---|---|---|
| **Phase 1** | US cities; ASHRAE 90.1-2019 + IECC 2021 + DOE prototypes + eGRID 2022; deterministic loads/schedules; rule-based classifier; KDE/PDE imputation; IdealAir/PackagedDX HVAC | This design |
| **Phase 2** | Probabilistic Monte-Carlo + 4-version sweep (VBASELINE→VOCCUPANT→VCONSTRUCTION→VCOMBINED); ML imputation (RF/GBM); BESOS-style surrogate models; stochastic schedules (Markov / Dabirian 2024); Bayesian calibration opt-in | Architectural hooks present |
| **Phase 3** | NECB Canada + TABULA Europe construction JSON; CityGML/3DCityDB ingest; ladybug-core solar; UWG climate-morphing; full city-scale (≫10⁵) inference via surrogates | Stubs only |

---

## OPEN QUESTIONS

1. Per-building EnergyPlus wall-clock on Béluga / Narval (literature-inferred, not measured). *(blocks DESIGN §9.1 confirmation)*
2. Calcul Québec / Concordia 2,000 core-hours/month allocation — DRAC RAC/RAS pending. *(§9.3)*
3. Boston-Downtown 500 m radius definitive building count for unit-test fixture. *(§5.1)*
4. NYC LL84, SF Existing Buildings Ordinance redistribution licences. *(§8.2)*
5. OSM-to-OpenStudio classifier accuracy on full 30-type taxonomy (need 200×4-city manual labelling sprint). *(§5.3)*
6. Iseri et al. (2025) 24-building Bahçelievler supplementary-data accessibility. *(§8.1 Level 3)*
7. NECB 2011/2015/2017 envelope-table machine-readable sourcing. *(§3.2)*
8. Pre-wire `weather/uwg_morph.py` placeholder now or defer? *(§2.2)*
9. Non-rectangular footprint failure rate on real OSM (target ≥98% IDFs pass smoke). *(§5.5)*
10. CV(RMSE) <30% building-level acceptable to NSERC reviewers? (Guideline 14 = 15% calibrated). *(§8.1 Level 4)*
11. Default fallback for unknown OSM `building=*` tags (currently MediumOffice — TBC). *(§5.3)*
12. CMHC / Statistics Canada training data for Phase-3 NECB ML imputation. *(§7.3)*
13. Phase-2 stochastic schedule scope confirmation (Dabirian 2024 Concordia). *(§5.3)*
14. EnergyPlus version pin: ship 9.6 + 23.1 IDDs auto-detected, or 23.1-only? *(§3.2)*
