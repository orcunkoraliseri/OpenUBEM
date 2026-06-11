# Step 2.2 — Climate-Located GeoDataFrame → Construction Sets, Internal Loads, Schedule Library, and Imputation
### OpenUBEM Stage 2 / Modules 04, 05, 06, 06b: `openubem/semantic/{construction_sets,loads,schedules,imputation}.py` — append exactly 28 semantic columns (29 → 57, completing Step 3's frozen input contract), emit the 30-archetype × 6-family schedule library, and close every remaining NaN through the KDE/PDE imputation tier

> **Slug:** `step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and` &nbsp;•&nbsp; **First created:** `2026-06-09` &nbsp;•&nbsp; **Latest revision:** `2026-06-09`
>
> Sections 1–9 are **append-once, edit-never** after first APPROVED verdict. Section 10 (Progress Log) is owned by the downstream `/run` reporter. All `/design` re-run changes are recorded under **Section 11 — Revision Log**.
>
> **Scope rule.** This document covers exactly **one** step of the umbrella pipeline — Step 2.2 (Modules 04 construction sets, 05 internal loads, 06 schedules, 06b imputation — the four modules that together append the final 28 columns of Step 3's 57-column input contract). The step's *internal* sub-stages (3A–3G) live under §3 Pipeline. Step 2.1 (climate zone + EPW) and Step 3 (IDF generation) are covered in their own per-step DESIGN docs.

---

## 1. Aim

Step 2.2 takes the 29-column climate-located GeoDataFrame produced by Step 2.1 (`02a_buildings_climate.gpkg`) and finishes the semantic enrichment that Step 3's frozen 57-column input contract assumes is done: for every building it resolves a construction vintage (`vintage_standard`), looks up the ASHRAE 90.1 / IECC envelope set for its `(archetype_id, climate_zone, vintage)` key (5 U-values/SHGC, 2 assembly labels, infiltration), looks up the DOE-prototype internal loads for its archetype (lighting/equipment/occupant densities, 4 thermostat scalars, window-to-wall ratio), and routes anything the lookups cannot answer — `OpenUBEMUnknown` rows, lookup-table gaps, probabilistic-mode sampling — through the Module 06b KDE/PDE imputation tier so that **zero NaN survives in any of the 28 appended columns**. Alongside the column append, Module 06 emits the schedule library Step 3 §2 binds by name: 30 archetypes × 6 families (`Occupancy_Schedule_{arch}`, `Lighting_Schedule_{arch}`, `Equipment_Schedule_{arch}`, `Heating_Setpoint_{arch}`, `Cooling_Setpoint_{arch}`, `Infiltration_Schedule_{arch}`) of `Schedule:Compact` stubs, persisted as `02b_schedule_library.json` and exposed in-memory keyed by `archetype_id`. The module decomposition follows `inputs/aim/OpenUBEM_Technical_Pipeline.md` §5 (Stage 2, Modules 04–06b); downstream consumers are Step 3 (validates and consumes all 57 columns plus the schedule library), Step 4 (indirectly, via the IDFs), and Step 5 (passes the 57 columns through to the 70-column results contract).

**Pipeline-position note (documented refinement).** This is the last column-accretion step: Step 1 (23) → Step 2 (26) → Step 2.1 (29) → **Step 2.2 (57)**. Step 3 §2 names its input artifact "`02_buildings_classified.gpkg` (post-enrichment)"; that artifact is realized here as `02b_buildings_enriched.gpkg` — the binding element is the 57-column schema Step 3's input gate validates, not the filename. A second documented refinement: the spec's `get_construction_set(building_type, climate_zone, year_built, standard)` resolves vintage *inside* the lookup; Step 2.2 splits vintage resolution into its own sub-stage (§3B) so `vintage_standard` becomes an explicit, auditable column — which Step 3's frozen contract requires anyway. Third: the 90.1-vs-IECC routing predicate the spec sketches near Module 03 (`get_energy_template`) is owned here by Module 04, because it is a construction-table concern, not a classification concern.

---

## 2. Inputs

| Artifact | Source | Dtype | Shape | Notes |
|---|---|---|---|---|
| `02a_buildings_climate.gpkg` (layer `buildings`) | Step 2.1 / Module 02 | GeoDataFrame | (N, 29) | UTM-projected geometry; 26 Step-2 columns byte-identical + `climate_zone` (16-token closed vocab), `epw_path`, `provenance_climate_zone`. Step 2.2 reads `archetype_id`, `climate_zone`, `year_built`, `data_quality_flag`; 28 of 29 columns pass through byte-identical (§3B documents the single `data_quality_flag` exception). |
| `data/construction/ashrae_90_1_2019.json` | bundled in wheel | JSON | 30 archetypes × 16 zones | Commercial/institutional envelope table per Technical Pipeline §5 Module 04: per `(building_type, climate_zone)` → `{roof: {u_value, assembly}, wall: {u_value, assembly}, window: {u_value, shgc}, floor: {u_value}, infiltration_rate}`. 90.1-2019 is the vintage baseline (factor 1.0). |
| `data/construction/iecc_residential.json` | bundled in wheel | JSON | residential archetypes × 16 zones | Same structure as the 90.1 table (Technical Pipeline §5: "IECC residential table same structure"). Routing set + era→IECC-edition mapping is OQ-6. |
| `data/loads/doe_prototype_loads.json` + `data/loads/openstudio_loads.json` | bundled in wheel | JSON | one entry per archetype | DOE Commercial Prototype loads (16 prototypes) + OpenStudio extended types (Lab, DataCenter, TallBuilding…). Keyed on `archetype_id` alone — DOE prototype loads are not climate-zone-dependent. Includes per-archetype `wwr` (design_state row 90). |
| `data/schedules/doe_schedules.json` | bundled in wheel | JSON | 30 archetypes × 6 families | Digitized DOE-prototype day profiles (Weekday/Saturday/Sunday) per family. One-time digitization from the DOE prototype IDFs is OQ-2. |
| `config.py` | package config | Python module | — | Exposes `LOAD_MODE` (default `'deterministic'`), `RANDOM_SEED` (default 42 — seeds the §3E sampler), `PDE_BOUNDS_PATH` (ASHRAE 90.1 bounds table for probabilistic mode, OQ-5). |

---

## 3. Pipeline

Step 2.2 is three vectorized table lookups (vintage → envelope → loads) followed by an imputation sweep that closes every remaining gap, a schedule-library build, and a single schema-gated emit. Nothing here touches the network and nothing is trained: every value is either a standards-table lookup (`ASHRAE_STANDARD`), a documented heuristic (`HEURISTIC`), or a seeded statistical draw (`KDE_IMPUTED` / `PDE_GENERATED`) — the four canonical §12 provenance tokens this step emits.

### 3A — Input Gate & Schema Validation (orchestrator: `openubem/semantic/__init__.py :: enrich_semantics()`)

The 29-column input is validated against `02a_buildings_climate.schema.json`: column names and order, dtypes, `archetype_id` within the closed 30-element vocabulary (29 OpenStudio + `OpenUBEMUnknown`, design_state row 73), `climate_zone` within the closed 16-token US vocabulary (Step 2.1 §3B), `epw_path` and `provenance_climate_zone` non-null. Schema mismatch aborts the run with a structured error — Step 2.2's lookups key on `archetype_id × climate_zone`, so a malformed input cannot degrade per-building; it can only be wrong systematically.

> **Why this approach:** The gate mirrors Step 2.1 §3A and Step 3's input gate — every accretion step validates its upstream contract before touching it, so a contract break is caught at the step boundary where it happened rather than three stages later inside EnergyPlus. **Rejected:** (a) trusting the upstream artifact because "we wrote it" — re-runs against stale or hand-edited GeoPackages are exactly the case schema sidecars exist for; (b) per-row tolerance of unknown `archetype_id`/`climate_zone` tokens — both vocabularies are closed by frozen upstream contracts, so an unknown token is a systemic error, not a data gap.

### 3B — Vintage Resolution (Module 04: `openubem/semantic/construction_sets.py :: resolve_vintage()`)

`year_built` (nullable `Int64`, Step 1 provenance) is mapped onto Step 3 §3F's **frozen 7-token `vintage_standard` vocabulary** `{DOERefPre1980, DOERef1980to2004, 90.1-2007, 90.1-2010, 90.1-2013, 90.1-2016, 90.1-2019}` through five half-open year bins:

| `year_built` | `vintage_standard` | U-value regime (§3C) |
|---|---|---|
| < 1980 **or NaN** | `DOERefPre1980` | ×1.6 multiplier on 90.1-2019 baseline (spec-sourced, Technical Pipeline §5) |
| [1980, 2004) | `DOERef1980to2004` | 90.1-1999-derived factors (numeric values OQ-1) |
| [2004, 2010) | `90.1-2007` | edition-table factors (OQ-1) |
| [2010, 2016) | `90.1-2013` | edition-table factors (OQ-1) |
| [2016, ∞) | `90.1-2019` | baseline, factor 1.0 (spec) |

Five of the seven tokens are reachable from year bins; `90.1-2010` and `90.1-2016` are **schema-legal but bin-unreachable** in Phase 1 (the same pattern as Step 2's `PHASE_1_UNREACHABLE` LowITE archetypes, row 76) — reachable only via richer vintage data in Phase 2. The bin-edge → edition mapping is tagged `ASSUMPTION_DESIGN_DEFAULT` (OQ-1): the spec groups 2004–2016 under "90.1-2013 factors", while the full-system DESIGN's parameter dataclass splits at 2010; Step 2.2 follows the finer 5-bin split and flags the discrepancy rather than silently averaging it.

NaN `year_built` resolves to `DOERefPre1980` — the **permissive direction** confirmed in design_state row 86: the five envelope provenance columns for such rows are set to `HEURISTIC` (the vintage guess contaminates every value derived from it), and the token `VINTAGE_NAN_PERMISSIVE_DEFAULT` is appended to the row's `data_quality_flag`. This is the **single, documented exception** to byte-identical pass-through: 28 of the 29 upstream columns are byte-identical; `data_quality_flag` may gain exactly this one closed-vocabulary token (the same append-only extension discipline Step 3 uses for its `idf_dp_coarse`/`idf_hull_simplification` tokens, row 80). `vintage_standard` itself carries no dedicated provenance column — the frozen 57-column contract has none for it; the flag token plus the HEURISTIC envelope provenances are its audit trail.

> **Why this approach:** The 7-token vocabulary is not this step's to choose — Step 3 §3F froze it ("there is no `90.1-2004` label — that range is `DOERef1980to2004`"), so §3B's only degrees of freedom are the bin edges, and those follow the full-system DESIGN's parameter dataclass (`pre1980 / 1980-2004 / 2004-2010 / 2010-2016 / 2016+`). The permissive NaN default prevents the systematic bias the most-recent-vintage alternative would create: untagged OSM stock is disproportionately *older* stock, and assigning it a 2019 envelope would overstate envelope quality and understate heating EUI on exactly the retrofit-relevant buildings (Step 3 §9 row 7 rationale, design_state row 86). **Rejected:** (a) most-recent-vintage NaN default — anti-conservative in the heating-dominated climates Phase 1 targets; (b) KDE-imputing `year_built` from the neighbourhood's observed distribution — would have to mutate a byte-identical upstream column, breaking the accretion contract, and fabricates a precise year where only an era is needed; (c) a `provenance_vintage` column — would widen the frozen 57-column contract for information the flag token already carries.

### 3C — Envelope Lookup (Module 04: `openubem/semantic/construction_sets.py :: get_construction_set()`)

The bundled construction JSONs are flattened once into a lookup DataFrame keyed `(lookup_table, climate_zone, vintage_standard)` and joined to the buildings in **one vectorized `merge`** — the same one-shot-join discipline as Step 2.1's `sjoin`. Routing: archetypes in the residential set (per Step 3 §3B's `residential_set`) hit `iecc_residential.json`; all others hit `ashrae_90_1_2019.json`; the NECB Canada table is a Phase-3 stub (row 35). Vintage is applied as a multiplier table on the 90.1-2019 baseline U-values — `DOERefPre1980` × 1.6 is spec-sourced; the intermediate-era factors are OQ-1.

```python
# Module 04: openubem/semantic/construction_sets.py
def get_construction_set(building_type: str, climate_zone: str,
                         vintage_standard: str,
                         standard: str = 'auto') -> dict:
    # 'auto': residential_set -> iecc_residential.json, else ashrae_90_1_2019.json
    table = _TABLES[_lookup_table_for(building_type, standard)]
    base = table[building_type][climate_zone]          # 90.1-2019 / IECC-2021 baseline
    f = VINTAGE_U_FACTORS[vintage_standard]            # DOERefPre1980 -> 1.6; 90.1-2019 -> 1.0
    return {
        'u_roof_w_m2k':         base['roof']['u_value'] * f,
        'assembly_roof':        base['roof']['assembly'],        # e.g. 'IEAD'
        'u_wall_w_m2k':         base['wall']['u_value'] * f,
        'assembly_wall':        base['wall']['assembly'],        # e.g. 'Mass'
        'u_window_w_m2k':       base['window']['u_value'] * f,
        'shgc_window':          base['window']['shgc'],          # vintage factor applies to U only (spec)
        'u_floor_w_m2k':        base['floor']['u_value'] * f,
        'infiltration_m3_s_m2': base['infiltration_rate'],       # vintage-invariant in Phase 1 (OQ-1)
    }
```

Worked example — `MediumOffice` @ `1A` (spec values, Technical Pipeline §5): baseline `90.1-2019` → roof **0.273** W/m²K (`IEAD`), wall **0.701** (`Mass`), window **3.69** / SHGC **0.25**, floor **1.89**, infiltration **0.000285** m³/s·m². The same building tagged `DOERefPre1980` → roof **0.437**, wall **1.122**, window **5.90**, floor **3.02** (×1.6), SHGC and infiltration unchanged. Assembly labels (`assembly_roof`, `assembly_wall`) are a closed vocabulary defined by the bundled table (e.g. `{IEAD, Mass, SteelFramed, WoodFramed, Attic, MetalBuilding}`); the floor assembly label is *not* carried — the frozen 57-column contract has assembly columns for roof and wall only, and Step 3 §3F builds the floor as `Material:NoMass` from the U-value alone. Provenance for all five lookup-hit value groups: `ASHRAE_STANDARD` (or `HEURISTIC` where §3B's NaN-vintage rule applies; `HEURISTIC` for `OpenUBEMUnknown` rows via §3E). **Lookup-gap guard:** if a `(building_type, climate_zone)` entry is absent from the bundled table, the missing parameters are filled by `impute_column(method='auto')` over the *same archetype's sibling climate-zone entries* (partial missingness → KDE, §3E), provenance `KDE_IMPUTED`, plus one structured warning `{"event": "construction_lookup_gap", "archetype": ..., "zone": ...}`. The §5.1 exhaustive sweep makes a gap in the *bundled* tables a build-time failure; the runtime guard exists for user-supplied custom tables.

> **Why this approach:** A flattened one-shot merge is O(N) with pandas-native vectorization and — more importantly — makes the lookup *auditable as data*: the flattened table can be diffed against the upstream JSON in a unit test, where a per-row dict-walk cannot. Applying vintage as a multiplier on a single committed baseline (rather than bundling five fully-specified per-vintage tables) keeps one authoritative copy of each envelope number — the spec's own structure (§5: factors, not tables). The U-only scope of the ×1.6 factor follows the spec text ("vintage correction factors applied to U-values"); whether pre-1980 stock should also get degraded infiltration is explicitly left to the Phase-1.5 infiltration-bias study already in the backlog (Step 3 OQ-3) rather than invented here. **Rejected:** (a) per-row `apply` of the spec's dict-walk — O(N) Python-loop overhead and unauditable; (b) five materialized per-vintage JSON tables — five copies of every number to keep consistent; (c) abort on lookup gap — for user-supplied tables this would make one missing cell kill a run that the KDE guard can degrade traceably (flag-don't-drop, severity asymmetry per Step 2.1 §3B); (d) extending the ×1.6 factor to infiltration without evidence — direction plausible but magnitude unmeasured; the provenance system exists so such numbers arrive with sources.

### 3D — Internal Loads & WWR Lookup (Module 05: `openubem/semantic/loads.py :: get_loads()`)

Loads are a single merge keyed on `archetype_id` alone — DOE prototype load densities, thermostat scalars, and Phase-1 WWR are archetype properties, not climate properties:

```python
# Module 05: openubem/semantic/loads.py
def get_loads(building_type: str, mode: str = 'deterministic') -> dict:
    # deterministic: single DOE prototype values (Phase-1 default)
    # probabilistic: PDE sampling within ASHRAE 90.1 bounds (§3E)
    row = _LOADS_TABLE[building_type]   # doe_prototype_loads.json ∪ openstudio_loads.json
    return {
        'lighting_w_m2':          row['lighting_w_m2'],
        'equipment_w_m2':         row['equipment_w_m2'],
        'occupant_m2_per_person': row['occupant_density_m2_person'],
        'heating_setpoint_c':     row['heating_setpoint_c'],
        'cooling_setpoint_c':     row['cooling_setpoint_c'],
        'heating_setback_c':      row['heating_setback_c'],
        'cooling_setup_c':        row['cooling_setup_c'],
        'wwr':                    row['wwr'],    # uniform per-archetype scalar (row 90)
    }
```

Worked example — `MediumOffice` (spec values): lighting **10.76** W/m², equipment **10.76** W/m², occupant density **18.58** m²/person, heating setpoint **21.1** °C / setback **15.6** °C, cooling setpoint **23.9** °C / setup **29.4** °C, `wwr` **0.40** (large-commercial group). The Phase-1 WWR group anchors recorded in Step 3 §3F are binding: residential **0.21**, large commercial **0.40**, hospital/laboratory **0.30**, warehouse/data-center **0.10**; the full 30-row per-archetype table is OQ-4. For `{SmallDataCenterHighITE, LargeDataCenterHighITE}` the `equipment_w_m2` value is bound to the `ElectricEquipment` Watts/Floor-Area of the ITE zone in the NREL/openstudio-standards DOE prototype IDFs (design_state row 89; extraction is OQ-3 — Module 05 must not diverge from that source). The column name `occupant_m2_per_person` follows Step 3's frozen contract, not the spec's `occupant_density_m2_person` — the contract wins. Provenance: `ASHRAE_STANDARD` for all six loads provenance columns on lookup-hit rows. Note that `infiltration_m3_s_m2` appears in the spec's Module 05 example too; ownership here is **Module 04** (it is an envelope leakage property, sits in the construction table keyed by climate zone, and the spec's own §5 construction JSON carries it) — Module 05 never writes it.

> **Why this approach:** Keying on `archetype_id` alone matches how the DOE prototype documentation publishes these values (per prototype, identical across the 16 climate-zone variants of each prototype IDF's internal loads) — adding a zone key would imply a dependency the source data does not have. The setback/setup scalars ride along with the setpoints because Step 3's thermostat objects reference dual-plateau schedules (§3F here) whose plateaus must equal these scalars — carrying them as columns lets Step 5-era auditors and the §5.1 consistency check read them without parsing schedule JSON. **Rejected:** (a) folding loads into the construction JSON — different key structure (no zone axis) and different upstream source; (b) per-zone load adjustments (perimeter vs core) — Step 3 §3G explicitly assigns the same Module 05 row to all zones in Phase 1; (c) sourcing DataCenter ITE density from literature values — row 89 binds it to the DOE prototype IDF to prevent drift between OpenUBEM and the prototype baseline.

### 3E — Imputation & `OpenUBEMUnknown` Handling (Module 06b: `openubem/semantic/imputation.py :: impute_column()`)

Module 06b is the closing sweep that guarantees the zero-NaN post-condition over all 28 appended columns. It implements the spec's three-tier `impute_column` exactly, with the ML tier **inert in Phase 1** (row 33):

```python
# Module 06b: openubem/semantic/imputation.py
def impute_column(series: pd.Series, method: str = 'auto',
                  bounds: tuple = None, model_path: Path = None,
                  rng: np.random.Generator = None) -> pd.Series:
    # AUTO:  0% < missing < 100%  -> KDE  (scipy.stats.gaussian_kde, Silverman;
    #                                      resample until within bounds)
    #        100% missing         -> PDE  (scipy.stats.uniform(loc=a, scale=b-a))
    #        model_path provided  -> ML   (joblib-loaded sklearn Pipeline) — Phase 2
    ...
```

Phase-1 firing surface, in order of expected frequency:

1. **`OpenUBEMUnknown` rows** (the unclassifiable-OSM sentinel, row 73): **envelope** = donor lookup `MediumOffice @ DOERefPre1980` in the building's own `climate_zone` — the permissive-envelope reading row 73 confirms — with all five envelope provenances `HEURISTIC`; **load densities + `wwr`** = PDE draws, `scipy.stats.uniform` over the `[min, max]` of each parameter across the 29 real archetypes' loads table (max-entropy under observed bounds), provenance `PDE_GENERATED`; **thermostat scalars** = cross-archetype *medians* (provenance `HEURISTIC`), **not** PDE draws — independently sampled setpoints could invert (`heating ≥ cooling`), and a post-guard asserts `heating_setpoint_c < cooling_setpoint_c` on every emitted row.
2. **Lookup-table gaps** (§3C/§3D guard): KDE over the parameter's sibling entries (partial missingness across the lookup table, not across buildings), provenance `KDE_IMPUTED`. Zero activations expected on the bundled tables (§5.1 sweep).
3. **Probabilistic mode** (`get_loads(mode='probabilistic')`, run-level `LOAD_MODE` switch): perturbs **only** `lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person` via PDE draws within the ASHRAE 90.1 bounds table (`PDE_BOUNDS_PATH`, OQ-5), provenance `PDE_GENERATED`. Setpoints, setbacks, `wwr`, and the entire envelope stay deterministic.

All draws flow through one `np.random.default_rng(config.RANDOM_SEED)` instantiated per run in `enrich_semantics()` — same seed ⇒ byte-identical artifacts. `build_ml_imputer()` ships as the documented Phase-2 interface (sklearn `StandardScaler` + regressor pipeline, persisted with joblib) but no Phase-1 call path reaches it.

> **Why this approach:** The KDE/PDE split is the confirmed Phase-1 imputation doctrine (row 33: KDE for partial missingness under Silverman bandwidth, PDE as max-entropy uniform under bounds for total missingness; MICE rejected for MAR violation, deep generative rejected for insufficient rows — the same data-shortage reality documented in `inputs/papers/data-shortage-for-urban-energy-simulations-...md`). Keeping setpoints deterministic in *both* the Unknown branch and probabilistic mode is forced by a frozen contract: Step 3 binds thermostat schedules per **archetype** (30 schedule sets exist, §3F), so per-building setpoint draws would disagree with the archetype-keyed schedule plateaus — the §5.1 consistency invariant would be unsatisfiable. Median (not mean) for Unknown setpoints resists the outlier archetypes (DataCenter cooling, Warehouse setbacks). **Rejected:** (a) PDE-sampling Unknown setpoints — thermostat-inversion risk plus the schedule-contract conflict above; (b) imputing Unknown envelope by cross-archetype KDE — envelope parameters are strongly coupled within an assembly (a KDE marginal per column can emit a physically incoherent set; the donor archetype keeps the set coherent), and row 73 already commits the pre-1980-permissive reading; (c) `random.seed()` global state — process-global seeding leaks across joblib workers downstream; an explicit `Generator` object is the numpy-documented isolation pattern; (d) exercising the ML tier in Phase 1 — row 33 defers it, and an inert-but-documented interface is how Step 2 handled its Phase-2 ML drop-in too.

### 3F — Schedule Library (Module 06: `openubem/semantic/schedules.py :: build_schedule_library()`)

Module 06 builds the schedule library Step 3 consumes both **by name** (every `Schedule_Name` reference written in Step 3 §3F/§3G/§3H must resolve at IDF parse time) and **by object** (Step 3 calls `idf.copyidfobject(stub)` per needed schedule). The contract, frozen by Step 3 §2: **30 archetype keys × 6 families** = 180 `Schedule:Compact` stubs, names exactly:

| Family | Object name | Type limits | Day profiles |
|---|---|---|---|
| occupancy | `Occupancy_Schedule_{arch}` | `Fraction` | Weekday / Saturday / Sunday (holidays → Sunday via `For: AllOtherDays`) |
| lighting | `Lighting_Schedule_{arch}` | `Fraction` | ditto |
| equipment | `Equipment_Schedule_{arch}` | `Fraction` | ditto |
| heating setpoint | `Heating_Setpoint_{arch}` | `Temperature` | dual-plateau: occupied hours = `heating_setpoint_c`, else `heating_setback_c` |
| cooling setpoint | `Cooling_Setpoint_{arch}` | `Temperature` | dual-plateau: occupied hours = `cooling_setpoint_c`, else `cooling_setup_c` |
| infiltration | `Infiltration_Schedule_{arch}` | `Fraction` | inverse-occupancy convention (full leakage when HVAC off) |

Day profiles are digitized from the DOE prototype schedule set (`data/schedules/doe_schedules.json`, OQ-2), differentiated Weekday/Saturday/Sunday per the spec. **Setpoint–scalar consistency invariant:** for every archetype, the occupied plateau of `Heating_Setpoint_{arch}` equals that archetype's `heating_setpoint_c` column value and the unoccupied plateau equals `heating_setback_c` (likewise cooling) — checked in §5.1, because Step 3 writes the scalars nowhere (thermostats reference only the schedules), so a drift between column and plateau would be silently invisible downstream. `OpenUBEMUnknown` gets a **clone of the MediumOffice schedule set under its own key** (`Occupancy_Schedule_OpenUBEMUnknown`, …), so Step 3's name references resolve for Unknown rows without special-casing. `Activity_Level` is **not** emitted here — it is a universal constant (120 W/person, ASHRAE 55 sedentary) embedded in Step 3's base IDF template stubs (design_state row 87). The library is persisted as `02b_schedule_library.json` (the I6 persistent intermediate; keys = archetype → family → `Schedule:Compact` field dict) and returned in-memory as `dict[str, dict[str, dict]]`; `write_schedules_to_idf(idf, building_type)` remains the spec's per-IDF injection API, used by Step 3 §3D.

> **Why this approach:** The six families and the exact name patterns are read directly off Step 3's frozen code sketches (`Occupancy_Schedule_{arch}` in `PEOPLE`, `Lighting_Schedule_{arch}` in `LIGHTS`, `Equipment_Schedule_{arch}` in `ELECTRICEQUIPMENT`, `Heating_Setpoint_{arch}`/`Cooling_Setpoint_{arch}` in `HVACTEMPLATE:THERMOSTAT`, `Infiltration_Schedule_{arch}` in `ZONEINFILTRATION:DESIGNFLOWRATE` — the last being the Pass-1 critic fix that made infiltration archetype-keyed like the rest). Persisting the library as JSON makes the schedule content diffable and citable — constant-schedule placeholder regressions are a documented UBEM bias class (Step 3 §3G rejection (c)) and a text artifact is the cheapest defense. The Unknown-as-clone decision keeps the 30-key completeness invariant trivially checkable (30 × 6, no holes) rather than aliasing Unknown to MediumOffice at reference time inside Step 3, which would put archetype-special-casing in the wrong module. **Rejected:** (a) `Schedule:Year`/`Schedule:Week:Daily` object trees — strictly more objects per family for no Phase-1 expressiveness gain over `Schedule:Compact`; (b) per-building schedule perturbation (occupancy-diversity factors) — Phase-2 territory, and it would explode the frozen 30-set contract; (c) emitting `Activity_Level` per archetype — row 87 already places the universal constant in the base templates; duplicating it per archetype invites conflicting definitions in one IDF.

### 3G — Column Append, `validate_schema()` Gate & Artifact Emission (orchestrator: `enrich_semantics()`)

Exactly **28 columns** are appended in fixed order — envelope group (14): `vintage_standard`, `u_roof_w_m2k`, `assembly_roof`, `u_wall_w_m2k`, `assembly_wall`, `u_window_w_m2k`, `shgc_window`, `u_floor_w_m2k`, `infiltration_m3_s_m2`, `provenance_u_roof`, `provenance_u_wall`, `provenance_u_window`, `provenance_u_floor`, `provenance_infiltration`; loads group (14): `lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person`, `heating_setpoint_c`, `cooling_setpoint_c`, `heating_setback_c`, `cooling_setup_c`, `wwr`, `provenance_lighting`, `provenance_equipment`, `provenance_occupant_density`, `provenance_heating_setpoint`, `provenance_cooling_setpoint`, `provenance_wwr`. **Provenance-sharing rules** (the frozen contract has 11 provenance columns for 17 value columns — the sharing is therefore part of the design, pinned here): `shgc_window` shares `provenance_u_window`; `assembly_roof`/`assembly_wall` share `provenance_u_roof`/`provenance_u_wall`; `heating_setback_c` shares `provenance_heating_setpoint`; `cooling_setup_c` shares `provenance_cooling_setpoint`; `vintage_standard` is audited via the §3B flag token. Every provenance value ∈ `{ASHRAE_STANDARD, HEURISTIC, KDE_IMPUTED, PDE_GENERATED}` (canonical §12 tokens, row 62).

The `validate_schema()` gate then asserts, before anything is written: **(1)** 57 columns, fixed order, dtypes per the schema sidecar; **(2)** 28 of 29 upstream columns byte-identical, `data_quality_flag` changed only by the §3B token rule; **(3)** zero NaN across all 28 appended columns; **(4)** plausibility envelopes — `u_* ∈ [0.1, 7.0]` W/m²K, `shgc_window ∈ (0, 1]`, `infiltration_m3_s_m2 ∈ (0, 0.01]`, `lighting_w_m2 ∈ (0, 50]`, `equipment_w_m2 ∈ (0, 2500]` (the ceiling admits DataCenter ITE densities; all non-DataCenter archetypes must sit ≤ 100), `occupant_m2_per_person ∈ [1, 200]`, `wwr ∈ [0.05, 0.9]`, and `heating_setpoint_c < cooling_setpoint_c` row-wise with `heating_setback_c ≤ heating_setpoint_c ≤ 25` and `cooling_setup_c ≥ cooling_setpoint_c`; **(5)** schedule-library completeness (30 keys × 6 families) and the setpoint–scalar consistency invariant (§3F). Gate failure aborts the run — like Step 2.1's weather gate, a systematically broken enrichment has no per-building degradation path. Emitted artifacts: `02b_buildings_enriched.gpkg` (layer `buildings`, (N, 57), UTM preserved) + `02b_buildings_enriched.schema.json` (57 entries) + `02b_schedule_library.json`.

> **Why this approach:** The plausibility envelopes encode the physics the lookup tables are supposed to respect, so a corrupted or mis-keyed bundled JSON (the failure mode the gate exists for) is caught at enrichment time rather than as 400 implausible EUIs at Step 5 — the same minute-0-vs-minute-30 argument as Step 2.1 §3D. The U-value ceiling of 7.0 W/m²K admits the worst legal case in the design space (pre-1980 single-glazing: 3.69 × 1.6 = 5.90) with margin but rejects unit mistakes (a Btu/h·ft²·°F value pasted as W/m²K, or a ×1.6 applied twice). Pinning the provenance-sharing rules in §1–§9 closes the one ambiguity the Step 3 contract left open (it counts "5× envelope provenance columns, 6× loads provenance columns" without naming which value shares which). **Rejected:** (a) NaN-tolerant emit with flags — Step 3's IDF writer has no NaN branch (`Watts_per_Zone_Floor_Area=NaN` is a fatal EnergyPlus parse), so flag-don't-drop does not apply to *this* step's appended columns, exactly as it did not apply to Step 2.1's weather; (b) warn-only plausibility checks — a wrong-units table is systemic, not local; (c) a 12th provenance column for `vintage_standard` — breaks the frozen 57-column count.

---

## 4. Outputs

| Artifact | Filename | Format | Shape | Consumed by |
|---|---|---|---|---|
| Enriched GeoDataFrame | `<output_dir>/02b_buildings_enriched.gpkg` (layer `buildings`) | GeoPackage, UTM | (N, 57) | Step 3 / Modules 07–11 (the frozen 57-column input contract — Step 3 §2's "`02_buildings_classified.gpkg` (post-enrichment)" realized; schema is binding, filename is not). |
| Schema sidecar | `<output_dir>/02b_buildings_enriched.schema.json` | JSON | 57 entries | Step 3's input gate. |
| Schedule library | `<output_dir>/02b_schedule_library.json` | JSON | 30 archetypes × 6 families | Step 3 §3D (`idf.copyidfobject` injection) and §3F/§3G/§3H name references; audit diffing. |

Row-level guarantees: **(1)** N rows in = N rows out (flag-don't-drop; Step 2.2 drops nothing); **(2)** 28 of 29 upstream columns byte-identical; `data_quality_flag` append-only per the §3B single-token rule; **(3)** zero NaN in all 28 appended columns (§3G gate); **(4)** every provenance value from the canonical 4-token subset; **(5)** `heating_setpoint_c < cooling_setpoint_c` on every row, including `OpenUBEMUnknown`; **(6)** every `archetype_id` in the frame has a complete 6-family schedule set in the library.

---

## 5. Validation

### 5.1 Metrics and acceptance thresholds

| Metric | Threshold | Rationale (cite source) |
|---|---|---|
| Golden-fixture exactness | `MediumOffice @ 1A @ 90.1-2019` reproduces all 13 spec values exactly (0.273/IEAD, 0.701/Mass, 3.69/0.25, 1.89, 0.000285; 10.76, 10.76, 18.58, 21.1, 23.9, 15.6, 29.4; wwr 0.40) | the worked example in Technical Pipeline §5 is the only fully-specified ground truth; exact match proves the JSON → column path end-to-end |
| Exhaustive lookup sweep | 30 archetypes × 16 zones × 5 reachable vintages = **2,400 synthetic rows** → zero NaN, zero `construction_lookup_gap` warnings on bundled tables | makes a bundled-table gap a build-time failure, not a runtime KDE activation |
| Vintage U-monotonicity | for every (archetype × zone), all four U-values are non-increasing along `DOERefPre1980 → DOERef1980to2004 → 90.1-2007 → 90.1-2013 → 90.1-2019` | envelopes never worsen with newer code editions; catches mis-ordered factor tables (OQ-1 values must pass this before commit) |
| Unknown-row provenance identity | every `OpenUBEMUnknown` row has all 11 provenance values ∈ `{HEURISTIC, PDE_GENERATED}`; in deterministic mode, `PDE_GENERATED` appears **only** on Unknown rows | the sentinel's uncertainty must be fully visible (row 73); a standards token on an Unknown row is a routing bug |
| Setpoint sanity | 100% of rows `heating_setpoint_c < cooling_setpoint_c`; setbacks/setups on the correct side | thermostat inversion is a silent EnergyPlus pathology (simultaneous heat/cool) |
| Schedule completeness + consistency | 180/180 stubs present; every name matches its family pattern; occupied plateaus == setpoint scalar columns per archetype | Step 3 references resolve by name at IDF parse time; scalar–plateau drift is invisible downstream (§3F) |
| Seed reproducibility | probabilistic mode, same `RANDOM_SEED` ⇒ byte-identical artifacts; different seeds differ **only** in the 3 perturbed columns | the PDE tier must be auditable and re-runnable (row 33) |
| Determinism (deterministic mode) | identical inputs ⇒ byte-identical `02b_*` artifacts | pure lookups; drift indicates hidden state |
| Pass-through integrity | 28/29 upstream columns byte-identical; `data_quality_flag` deltas ⊆ `{VINTAGE_NAN_PERMISSIVE_DEFAULT}` | accretion-contract discipline (rows 71, and Step 2.1 §4) |

### 5.2 Test data and holdout strategy

- **Offline unit fixtures** (bundled data only): the golden `MediumOffice@1A` fixture above; a `DOERefPre1980` ×1.6 fixture (0.437/1.122/5.90/3.02 expected); a NaN-`year_built` row (must emit `DOERefPre1980` + HEURISTIC envelope provenances + the flag token, and nothing else changed in `data_quality_flag`); an `OpenUBEMUnknown` row (donor envelope + PDE loads within cross-table bounds + median setpoints + cloned schedule set resolves); a synthetic custom table with one deleted zone entry (KDE gap guard fires, `KDE_IMPUTED` provenance, warning payload correct); a deliberately inverted setpoint pair in a synthetic loads table (gate must abort); a wrong-units U-value (gate must abort at the plausibility envelope); two-seed probabilistic runs (reproducibility + perturbation-scope assertions). Unit fixtures use a synthetic 2-archetype schedule library so OQ-2 does not block testing.
- **Boston Downtown 500 m integration fixture** — the ~400-building frame from Steps 1–2.1: all rows 5A; report the `DOERefPre1980` fraction (expected high — OSM `year_built` coverage is sparse) and the `OpenUBEMUnknown` fraction; assert zero NaN and gate pass end-to-end into Step 3's input gate.
- Holdout regime: not applicable — nothing is trained. The 2,400-combo sweep is the coverage instrument.

### 5.3 True Future Test (only if a forecast or generalization claim is made)

Not applicable — Step 2.2 is deterministic standards lookups plus seeded max-entropy sampling; it trains no model and makes no forecast. The PDE tier's statistical claim (uniform within ASHRAE bounds is the max-entropy choice under total missingness) is a modeling *assumption* recorded in row 33, not a fitted generalization; its EUI-level consequences are exercised by the Phase-2 probabilistic-mode studies, not by a holdout here.

---

## 6. Compute

| Resource | Estimate | Source of estimate |
|---|---|---|
| GPU hours (Calcul Québec / Concordia HPC) | 0 | table merges + JSON build |
| CPU | single core, seconds | three vectorized merges over N rows + 180-stub JSON build |
| Wall-clock (Boston 500 m) | < 10 s | dominated by GeoPackage read/write |
| Peak memory | < 1 GB | N-row frame + flattened lookup tables (≤ 2,400 rows) |
| Storage | gpkg ≈ input size + ~100–300 KB JSON (schema + schedule library) | §4 artifacts |
| Network | 0 bytes | all tables bundled in the wheel |

Step 2.2 is computationally trivial; its risk story is *data correctness* (table vintages, units, digitization fidelity), which is why §5.1 is the longest section of this step relative to §6.

---

## 7. Open Questions

- [ ] **OQ-1** — **Vintage factor table for the intermediate eras.** The ×1.6 pre-1980 multiplier is spec-sourced; the `DOERef1980to2004` ("90.1-1999 factors"), `90.1-2007`, and `90.1-2013` multipliers need numeric values extracted from the 90.1 edition tables, and the bin-edge mapping ([2004,2010) → `90.1-2007`, [2010,2016) → `90.1-2013`; `ASSUMPTION_DESIGN_DEFAULT`) needs confirmation against the spec's coarser "2004–2016 → 90.1-2013" grouping. Also decide whether infiltration gets a vintage adjustment (currently vintage-invariant; interacts with the Step 3 OQ-3 Phase-1.5 infiltration-bias study). Committed values must pass the §5.1 U-monotonicity gate. *(blocks §3C numeric finalization for non-baseline vintages)*
- [ ] **OQ-2** — One-time **digitization of `data/schedules/doe_schedules.json`** from the DOE Commercial Prototype schedule sets (NREL/openstudio-standards): 30 archetypes × 6 families × 3 day-types, including the occupied-hours windows that define the setpoint plateaus. Refresh procedure + licensing note, mirroring Step 2.1 OQ-2. *(blocks §3F on real data; unit fixtures use the synthetic 2-archetype library)*
- [ ] **OQ-3** — **DataCenter ITE `equipment_w_m2` extraction** from the NREL/openstudio-standards prototype IDFs for `SmallDataCenterHighITE`/`LargeDataCenterHighITE` (inherits design_state row 89 / Step 3 OQ-4 — the source is decided; the numbers are not yet committed). *(blocks §3D for the two HighITE archetypes only)*
- [ ] **OQ-4** — **Full 30-row per-archetype WWR table.** Only the four group anchors are committed (0.21 / 0.40 / 0.30 / 0.10, Step 3 §3F); each archetype needs its assignment to a group (or its own value) committed to `doe_prototype_loads.json`. The CBECS 2018 accuracy cross-check is already in the Phase-1.5 backlog (Step 3 OQ-2). *(blocks §3D table finalization)*
- [ ] **OQ-5** — **ASHRAE 90.1 PDE bounds table** (`PDE_BOUNDS_PATH`) for probabilistic mode: per-parameter `[min, max]` for lighting/equipment/occupant density, with sources. Also confirm the `OpenUBEMUnknown` policy of cross-archetype observed `[min, max]` (currently `ASSUMPTION_DESIGN_DEFAULT` — max-entropy under the loads-table envelope). *(blocks probabilistic mode and tightens the Unknown branch; deterministic Phase-1 default unblocked)*
- [ ] **OQ-6** — **IECC residential pathway:** extract/pin `iecc_residential.json` (which IECC edition per era — the era→IECC mapping is *not* the same as the 90.1 era mapping), and confirm the `residential_set` membership for routing (which of the 30 archetypes are IECC-governed vs 90.1-governed — apartment archetypes are code-boundary cases). Must stay consistent with the climate-zone edition pinned in Step 2.1 OQ-1. *(blocks §3C for residential archetypes; commercial path unblocked)*

---

## 8. References

**`inputs/aim/`** — project charter and pipeline blueprint
- `inputs/aim/OpenUBEM_Technical_Pipeline.md` — §5 (Modules 04/05/06/06b specifications: construction JSON structure + vintage factors, `get_loads` with the MediumOffice worked values, `get_schedule_definitions`/`write_schedules_to_idf`, `impute_column` AUTO logic + `build_ml_imputer`), §12 (provenance vocabulary), data directory layout (`data/construction/`, `data/loads/`, `data/schedules/`).
- `inputs/aim/OpenUBEM_Aim_Document.md` — Phase-1 US standards scope; open-data commitment (invariant I7).

**`inputs/papers/`** — technical references for methods
- `inputs/papers/three-methods-for-characterizing-building-archetypes-in-urban-energy-simulation-a-case-study-in-kuwa.md` — archetype-based semantic enrichment as the standard UBEM data pathway; anchors the lookup-table architecture.
- `inputs/papers/comparing-domain-expert-and-machine-learning-data-enrichment-of-building-registry.md` — enrichment-quality evidence for rule/lookup vs ML pathways; supports the Phase-1 deterministic default with Phase-2 ML drop-in.
- `inputs/papers/data-shortage-for-urban-energy-simulations-an-empirical-survey-on-data-availability-and-enrichment-m.md` — the missing-attribute landscape that motivates the three-tier imputation design; anchors §3E.
- `inputs/papers/an-approach-to-data-acquisition-for-urban-building-energy-modeling-using-a-gaussian-mixture-model-an.md` — distribution-fitting for UBEM input generation; context for the KDE/PDE tier (and why Phase 1 stops short of mixture/EM machinery).
- `inputs/papers/https-docs-nrel-gov-docs-fy24osti-90883-pdf.md` (El Kontar et al. 2024, NREL/CP-5500-90883) — DOE prototype/standards data pathways in open UBEM tooling; anchors the bundled-JSON sourcing strategy.
- `inputs/papers/pdf-archetypal-a-python-package-for-collecting-simulating-converting-and-analyzing-building-archetyp.md` — prior art for archetype template libraries in Python; rejected as a dependency (I7-compatible but template-converter-oriented), informative for the schedule-library JSON shape.
- `inputs/papers/pdf-deep-learning-based-wwr-and-floor-count-extraction-from-fa-ade-images-to-improve-ubem-researchga.md` — the Phase-2 per-building WWR pathway that the Phase-1 uniform per-archetype scalar (row 90) is interface-stable against.

**`inputs/reports/`** — UBEM methodology context
- `inputs/reports/UBEM Inputs and GitHub Repository Review.md` — how open UBEM tools bundle standards data; anchors the wheel-bundled JSON decision.
- `inputs/reports/Open Source Urban Building Energy Modeling - General.md` — archetype/loads/schedules enrichment patterns across open tools.

**Prior-step DESIGN docs (binding contracts)**
- `outputs/2026-06-09_step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build/DESIGN_step-2-1-...md` — 29-column input artifact + 16-token `climate_zone` vocabulary (this step's lookup key).
- `outputs/2026-05-07_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod/DESIGN_step-3-...md` — the frozen 57-column contract (§2), the 7-token `vintage_standard` vocabulary and NaN rule (§3F), the schedule name contract (§3F/§3G/§3H), per-archetype WWR anchors (§3F), DataCenter ITE sourcing (§3G + §11).
- `outputs/2026-05-06_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp/DESIGN_step-2-...md` — 30-element archetype vocabulary incl. `OpenUBEMUnknown` semantics (rows 73, 76).

**External anchors (cited via inputs only — no fabricated DOIs)**
- ASHRAE 90.1-2019 / IECC 2021 / DOE Commercial Prototype Buildings / NREL openstudio-standards — referenced via Technical Pipeline §5 and design_state rows 34, 89; numeric extractions tracked as OQ-1/2/3/4.

---

## 9. Key Decisions Summary

| # | Decision | Sub-stage | Rationale (one line) | Alternatives rejected |
|---|---|---|---|---|
| 1 | Append exactly 28 columns (29 → 57) in fixed order with **11 provenance columns under pinned sharing rules** (shgc→u_window, assemblies→their u, setback/setup→their setpoint; vintage audited via flag token) | 3G | Completes Step 3's frozen contract and closes its one ambiguity (which value shares which provenance column) inside §1–§9 | A 12th provenance column for vintage (breaks the 57 count); per-value provenance columns (would be 17, not 11). |
| 2 | `vintage_standard` from 5 half-open year bins into Step 3's frozen 7-token vocabulary; `90.1-2010`/`90.1-2016` schema-legal but bin-unreachable; NaN → `DOERefPre1980` + HEURISTIC envelope provenances + `VINTAGE_NAN_PERMISSIVE_DEFAULT` flag token (the single pass-through exception) | 3B | Vocabulary is Step 3's, bins are the full-system dataclass's; permissive NaN direction per row 86 avoids overstating envelope quality on older untagged stock | Most-recent-vintage default; KDE-imputing `year_built` (mutates a byte-identical column); inventing a reduced 5-token vocabulary (contract violation). |
| 3 | Envelope = one vectorized merge on `(lookup_table, climate_zone, vintage_standard)`; 90.1/IECC routing owned by Module 04; vintage as multiplier on one committed baseline (pre-1980 ×1.6 spec-sourced, U-values only); KDE lookup-gap guard | 3C | One authoritative copy of every envelope number; gap degrades traceably (`KDE_IMPUTED`) for user tables while the §5.1 sweep keeps bundled tables gap-free at build time | Per-row dict-walk `apply`; five materialized per-vintage tables; abort-on-gap; unevidenced infiltration vintage factor. |
| 4 | Loads + `wwr` = one merge keyed on `archetype_id` alone; DataCenter ITE bound to NREL/openstudio-standards prototype IDFs (row 89); `infiltration_m3_s_m2` owned by Module 04, never Module 05 | 3D | Matches the DOE source's key structure; one owner per column kills the spec's duplicated-infiltration ambiguity | Zone-keyed loads (dependency the source lacks); literature-sourced ITE densities (drift vs prototype baseline). |
| 5 | `OpenUBEMUnknown`: envelope = `MediumOffice @ DOERefPre1980` donor (HEURISTIC); load densities + `wwr` = PDE uniform over cross-archetype `[min,max]` (PDE_GENERATED); setpoints = cross-table median (HEURISTIC) with row-wise `heating < cooling` guard; schedules = MediumOffice clone under own key | 3E/3F | Row 73 semantics: uncertainty explicit and max-entropy where safe, coherent donor set where parameters are physically coupled, no thermostat inversion | PDE-sampled setpoints (inversion + schedule-contract conflict); cross-archetype KDE envelope (incoherent assembly sets); aliasing Unknown to MediumOffice at Step-3 reference time. |
| 6 | Schedule library: 30 keys × 6 families of `Schedule:Compact` stubs under Step 3's exact name contract (incl. `Infiltration_Schedule_{arch}`); dual-plateau setpoint schedules with **scalar–plateau consistency invariant**; persisted `02b_schedule_library.json`; `Activity_Level` excluded (row 87) | 3F | Step 3 binds by name at IDF parse time; the invariant makes column-vs-schedule drift impossible to miss; JSON persistence makes schedule content diffable | Schedule:Year object trees; per-building schedule perturbation (breaks the 30-set contract); emitting Activity_Level per archetype (duplicate definitions). |
| 7 | Imputation tier: spec's `impute_column` AUTO logic with ML inert in Phase 1 (row 33); probabilistic mode perturbs only the 3 density columns through one seeded `np.random.default_rng`; zero-NaN post-condition + plausibility-envelope gate before emit | 3E/3G | KDE/PDE is the confirmed Phase-1 doctrine; seeded Generator gives byte-identical re-runs; the gate catches wrong-units tables at minute 0 | Global `random.seed()`; sampling setpoints/envelope in probabilistic mode; NaN-tolerant emit (Step 3 has no NaN branch); warn-only plausibility checks. |

---

## 10. Progress Log *(populated by downstream `/run` reporter — leave empty here)*

<!-- The downstream execution project's reporter agent appends `### Session: <date> | Loop: <N>` blocks under this header after each /run cycle. NEITHER the architect NOR the documenter writes here. -->

---

## 11. Revision Log *(populated by DOCUMENTER on /design re-runs only — EMPTY on first creation)*

<!-- Append-only. DOCUMENTER inserts a new block on each /design re-run.

On MODE=new this section MUST contain only this comment block — no `### Session:` block. The first revision block is written on the first MODE=update run.

### Session: <YYYY-MM-DD> | Pass: <final-pass>
**Trigger:** <one-line: new evidence, change request, retired decision>
**Changes:** <sections touched + one-line summary each>
**Decisions retired:** <design_state.md rows retired, or "none">
-->

### Session: 2026-06-10 | Pass: n/a (direct resolution session)
**Trigger:** User resolved all 6 §7 Open Questions in chat; answers recorded in `inputs/notes/2026-06-10_step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and_resolved-open-questions.md`.
**Changes:** §7 statuses recorded here only (§1–§9 untouched per append-once rule):
- **OQ-1 PARTIALLY RESOLVED:** (a) finer 5-bin mapping **confirmed** — [2004, 2010) → `90.1-2007`, [2010, 2016) → `90.1-2013` (the spec's coarser "2004–2016 → 90.1-2013" grouping rejected); (b) infiltration stays **vintage-invariant** in Phase 1, revisited by the Phase-1.5 infiltration-bias study (Step 3 OQ-3); (c) the intermediate-era numeric U-multipliers are deferred to implementation-repo extraction from NREL/openstudio-standards, gated by the §5.1 U-monotonicity check.
- **OQ-2 DEFERRED to implementation repo:** `doe_schedules.json` digitization — source, shape, and licensing requirements fully specified in §3F; synthetic 2-archetype fixture stands for unit tests.
- **OQ-3 DEFERRED to implementation repo:** DataCenter HighITE `equipment_w_m2` extraction (source already committed, row 89).
- **OQ-4 DEFERRED to implementation repo:** full 30-row WWR table; the four group anchors stand; CBECS cross-check stays in the Phase-1.5 backlog (Step 3 OQ-2).
- **OQ-5 RESOLVED:** design default **confirmed** — cross-archetype observed [min, max] is the committed Phase-1 bounds policy for both the `OpenUBEMUnknown` PDE branch and probabilistic-mode perturbation; a sourced ASHRAE bounds table is demoted to optional Phase-1.5 refinement (`PDE_BOUNDS_PATH` remains the hook). `ASSUMPTION_DESIGN_DEFAULT` → user-confirmed.
- **OQ-6 RESOLVED:** Phase-1 standards scope is **US + ASHRAE only** (user decision): all 30 archetypes — including Midrise/Highrise Apartment, which are 90.1-governed DOE prototypes — route through `ashrae_90_1_2019.json`. The §3C residential → `iecc_residential.json` branch becomes an **inert Phase-2 hook** (`residential_set = ∅`); `iecc_residential.json` is **not required** in Phase 1, removing one bundled-JSON sourcing task. Recorded here because §3C is frozen; the mechanism is retained, only the routing set empties.
**Decisions retired:** none. Row 110's residential-routing clause is refined (not superseded) by new design_state row 115; rows 114–116 record this session's confirmations.
