# OpenUBEM — Fundamentals

**What this document is:** a plain-language explanation of what OpenUBEM does, what it
simulates, where, and at what resolution. It is the "start here" overview — no design
specs, no task lists, just the fundamentals. For the detailed reporting methodology see
[`simulated_vs_reconstructed_methodology.md`](simulated_vs_reconstructed_methodology.md);
for the full per-step specification see `docs/docs_main/` and the per-step `docs/docs_stepN/`
folders.

---

## 1. What OpenUBEM does (one paragraph)

OpenUBEM is an **Urban Building Energy Modeling (UBEM)** platform. You give it a
neighbourhood — an address, a coordinate, a bounding box, or an OpenStreetMap export — and
it estimates the **annual energy use** and **carbon emissions** of **every building** in
that neighbourhood. It does this without per-building audits or metered data: each building
is matched to a building *archetype*, turned into a physics-based EnergyPlus model, simulated
for a full year, and rolled up into neighbourhood-level numbers. The intended users are urban
planners, energy researchers, and policy makers who need building-level estimates at
district scale.

---

## 2. The core idea — archetype-based, per-building physics

OpenUBEM does not have a meter on every building. Instead it leans on two ideas:

1. **Archetypes.** Every building is classified into one of **30 standard building types**
   (DOE / OpenStudio archetypes — e.g. `MidriseApartment`, `LargeOffice`, `Hospital`,
   `Warehouse`). The archetype carries the "physics" the OSM data doesn't: envelope
   insulation, internal load densities, operating schedules, and HVAC efficiencies.

2. **Per-building physics simulation.** Each building still gets its **own** EnergyPlus
   model built from its **true footprint** (not a generic box), extruded to its real height,
   and shaded by its real neighbours. The archetype fills in the unknowns; the geometry and
   location are the building's own.

So the output is building-specific even though the inputs are archetype-generalised.

---

## 3. The five-stage pipeline

OpenUBEM runs as a **5-stage pipeline**. Each stage writes a versioned artifact that the
next stage reads, so any stage can be re-run on its own.

| Stage | Name | What it produces |
|---|---|---|
| **1** | Data Acquisition | Downloads + cleans building footprints from OpenStreetMap → `01_buildings_clean.gpkg` |
| **2** | Semantic Enrichment | Classifies each building into an archetype, assigns a climate zone + weather file, and attaches envelope / loads / schedules → `02b_buildings_enriched.gpkg` |
| **3** | IDF Generation | Builds one EnergyPlus input file (`.idf`) per building — geometry, zoning, constructions, loads, schedules, HVAC, shading → `idfs/*.idf` |
| **4** | EnergyPlus Simulation | Runs EnergyPlus on the whole fleet in parallel → `04_simulation_manifest.parquet` |
| **5** | Results, Carbon & Validation | Parses outputs into EUI, converts to carbon, aggregates to neighbourhood level, validates against measured data → `05_results.gpkg` + figures + interactive 3D viewer (§8) |

> **A sixth stage exists, and it is deliberately not part of this spine.** **Stage 6 — Outdoor
> Microclimate & Thermal Comfort** (§11) answers a different question — *what does it feel like to
> stand outside in this neighbourhood?* — and is **invoked explicitly, never as part of a standard
> run**. It reads Stages 1–5's artifacts read-only and writes its own `06_*` artifacts. It is a
> separate analysis product, not a sixth step every run pays for; §11 explains why that separation
> is a credibility decision rather than a technical one.

---

## 4. What gets simulated

### 4.1 The engine

- **EnergyPlus 23.1** — a whole-building physics engine (heat balance, solar gains,
  conduction, infiltration, internal gains, HVAC).
- **Full year, hourly.** Each building is simulated over an annual run period at **8760
  hourly timesteps**, driven by a real weather file (EPW) for the nearest station.

### 4.2 The end-uses

Each building's IDF carries packaged HVAC (**PTAC** — Packaged Terminal Air Conditioner)
per thermal zone, with a per-archetype rated cooling COP and heating-coil type. Because the
HVAC is real equipment (not an idealised abstraction), EnergyPlus reports **metered**
energy that is directly comparable to a utility bill. The simulation produces:

| End-use | Simulated? | Notes |
|---|---|---|
| Space heating | ✅ | electricity + natural gas, per archetype coil type |
| Space cooling | ✅ | DX electricity via PTAC COP |
| Lighting | ✅ | from archetype lighting power density |
| Plug / equipment | ✅ | from archetype equipment power density |
| Fans | ✅ | metered separately (not folded into the headline total) |
| Pumps / DHW / refrigeration / cooking | ❌ | not modelled — added back in reporting (§6) |

### 4.3 The outputs per building

- **EUI** (Energy Use Intensity, kWh/m²·yr) per end-use and a total.
- **Carbon** (kg CO₂e/m²) — electricity end-uses × state eGRID 2022 factor; heating gas ×
  0.181 kg CO₂e/kWh.
- **IOD** (Indoor Overheating Degree) — a summer thermal-comfort metric.

---

## 5. Simulation resolution

This is the part most people ask about. There are two resolutions: **spatial** (how the
building is divided up) and **temporal** (how time is divided up).

### 5.1 Spatial resolution — one model per building, adaptive thermal zoning

The unit of simulation is **one building = one IDF = one EnergyPlus run**. Inside each
building, the number of **thermal zones** is chosen automatically based on the building's
size and type. It is **not** always single-zone — there are three strategies
(`openubem/geometry/zoning.py`):

| Strategy | When it is used | Zones |
|---|---|---|
| **`single_zone`** | Genuine 1-floor buildings (`num_floors == 1`) | One zone for the whole building |
| **`one_zone_per_floor`** | Multi-floor **residential / tall** buildings, **small** (<500 m²) commercial, or unclassified | One zone per floor |
| **`perimeter_core`** | Multi-floor **commercial ≥ 500 m²** | Core + perimeter zones per floor (4.57 m perimeter depth) |

So a small house is one zone; a 10-storey apartment is ten zones (one per floor); a large
office tower is core+perimeter zones on every floor. The pipeline degrades gracefully —
narrow buildings or courtyard footprints that can't form a valid core fall back to
one-zone-per-floor.

**Floor area** (the denominator for EUI) is always `footprint_area_m2 × num_floors`.

#### The user-selectable resolution switch

The three strategies above are applied **automatically** in the default `auto` mode, but the
fidelity is now **user-selectable**: a `resolution_mode` parameter
(`docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md`) lets the user fix the
zoning per study — coarse for early-design screening, finer for detailed work. Five modes:

| Mode | What it does | Zones/building | Status |
|---|---|---|---|
| **`auto`** *(default)* | adaptive — picks per building | mixed | ✅ validated (baseline) |
| **`building`** | whole building = 1 zone | 1 | ✅ validated |
| **`floor`** | each floor = 1 zone | `num_floors` | ✅ validated |
| **`fast_zone`** | generic core + perimeter on every floor, **every** archetype | ~5 × `num_floors` | ✅ validated |
| **`layout_assign`** | **archetype prototype substitution & area scaling** — assigns a validated DOE/ASHRAE 90.1 baseline IDF (E+ 23.1 library) and scales it (√S geometry, S loads) to the real building's floor area | Real DOE-prototype zone count (1–256, archetype-specific) | ⚠️ adopted for zone/HVAC-topology studies — **not certified for fleet-level EUI reporting**, see §5.1.2 |
| **`zone`** | room-level polygon layout generation (deferred; see `layoutAssigner` for standardized replacement) | many | ⏸ replaced by `layout_assign` |

`building` and `floor` reuse strategies the code already has (`single_zone`,
`one_zone_per_floor`); `fast_zone` extends the core+perimeter slicing to **all** archetypes
regardless of area. `auto` is the validated baseline that produced the 8,160-building
benchmark (§7.2).

`layout_assign` has since been run at full fleet scale, separately from the four modes below and
their 8,160-building cluster matrix: the storey-matching arc's T20 harvest (12 cells / 8,160
buildings, closed 2026-08-04) reports **8,153/8,160 = 99.914% success, median `total_eui`
122.23 kWh/m²/yr** (the prior harvest, T19, was 7,990/8,160 = 97.92%, median 103.75). **Most of
that gain is not the storey-matching arc's own work:** of the +163 additional passing buildings,
+150 come from a pre-existing convergence fix (E-LA-20, landed 2026-07-25, before this arc began)
surfacing at fleet scale for the first time; the arc's own fixes and other, uninvestigated
per-cell recoveries account for +16 more, net of 3 regressions.

The mode's standing disposition, after that arc closed: **adopted for high-fidelity zone and
HVAC-topology studies**, and **not certified for fleet-level energy-per-area (EUI) reporting**.
Four limitations are documented, not hidden. Two are updates to this document: limitation 2 (the
envelope) is now resolved in code; limitation 3 (internal loads) is new to this document as of
2026-08-05 — it existed in the underlying arc record before that, but had not previously been
surfaced here.

1. **Fixed-capacity auxiliary equipment** — transformers, DHW tanks, HVAC coils — is not yet
   scaled with the building. This produces a clean, deterministic failure mode rather than random
   noise: across a measured population of 439 buildings, transformer overload is 0% at every
   residual storey-multiplier ≤ 7 and 100% at every multiplier ≥ 8.
2. **The baseline's native Buffalo CZ 6A envelope is now climate-patched** to the real building's
   own vintage and climate zone in code — `envelope_patcher.patch_envelope()`, called at
   `openubem/idf/builder.py:481`, is reached on the `layout_assign` path for every building that
   has a DOE baseline (i.e. every building except the ~8.8% with no `ARCHETYPE_IDF_MAP` entry,
   which never enter this code path at all). This resolves the limitation as it was originally
   written; it has not been separately re-validated for physical correctness beyond the fleet run
   described above.
3. **Internal loads are modelled as 2022-code construction, regardless of the building's real
   vintage.** Lighting and equipment power densities come from the `ASHRAE901_*_STD2022`
   prototypes. This is the asymmetry to hold onto: the envelope *is* patched to the real vintage
   (limitation 2, above); the internal loads are *not*. This is a direct consequence of prototype
   substitution, not a defect — but it had never been quantified before the storey-matching arc's
   close, and it is roughly half (not precisely measured as such — the arc's own wording is
   "roughly") of a fleet-wide **−29.1%** median difference between `layout_assign` and the other
   resolution modes. Register item **OPEN-03**.
4. **The floor area an EUI is divided by is nominal, not simulated — the most consequential open
   issue.** Every EUI this mode has reported, including the 122.23 kWh/m²/yr above, divides
   simulated energy by the building's *nominal* floor area (`footprint_area_m2 × levels`), not by
   the floor area EnergyPlus actually simulated. The file EnergyPlus writes recording the floor
   area it actually simulated, `eplusout.eio`, is deleted unconditionally by the shared cluster
   template, so no fleet-scale EUI in this mode has a verified denominator. **Measured** locally
   on 6 real buildings with `eio` retained: buildings where storey-matching actually applied hold
   to within ~0.002%; buildings it does not reach are off by exactly 4/3. **Inferred from the code
   contract, not measured:** most of the fleet — 6,939 of 7,442 evaluated buildings — falls into
   the second, unverified case.

See §5.1.2 immediately below for the substitution mechanism and why its reach is limited by
design, and §10 of the resolution results document for the full structural comparison. Full
record, real EUI numbers, and comparison figures:
[`docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md`](../docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md).

All four active modes were validated across the full 12-cell / 8,160-building matrix
(2026-07-01): internal loads **conserve** across modes — the same building simulated at any
resolution accounts for the same total floor area (`footprint_area_m2 × num_floors`), so a
`building`-mode tower is not under-counted relative to its per-floor version. The **EUI a
building reports still differs by mode** — coarser zoning under-predicts annual heating ~10–26%
and shifts peak/solar behaviour — and that is **correct physics, not error**: the differences
are largest for tall, deep, resolution-sensitive buildings and **wash out to < ~2.3%** once
results are aggregated to district scale. Use `building`/`floor` for screening and stock
totals; they are **not** appropriate for peak-demand or equipment-sizing studies (that is what
the deferred `zone` mode is for).

The `zone` mode is a later, **opt-in** upgrade — it is never used by `auto`, so fleet runs and
the validated 8,160-building baseline are unaffected. Earlier deep research
(`deepResearch/layoutMapping/`) had concluded that faithfully reproducing each prototype's *exact
zone count* was not worth building for the **average rectangular** case (< 5 % EUI change, below
validation tolerance). The current work (§5.1.1) revisits that for the case the research flagged as
the real gap: **non-rectangular footprints** (L/U/T/courtyard), which the coarser strategies cannot
zone at all and silently degrade — and for the archetypes (offices, hotels, schools) where room-level
detail actually moves EUI by 10–20 %.

### 5.1.1 Room-level layout generation (`zone` mode)

`openubem/geometry/layoutGenerator.py` is the engine behind `zone` mode. It closes a real gap:
the coarser strategies can only zone rectangular plates, and **silently degrade any L / U / T /
courtyard footprint to one-zone-per-floor** — a courtyard (donut) footprint would otherwise cause
an EnergyPlus *Fatal*. The layout generator instead builds a plausible **room-level floor plan** from
the building's true footprint:

1. **Classify the footprint shape** (compact / slab / L / U / T / cross / courtyard-O / ribbon)
   from pure geometry metrics — rectangularity, convexity, reflex-corner count — no fitted thresholds.
2. **Decompose** non-rectangular shapes into rectangular wings (orthogonal cuts at reflex corners;
   courtyards split into four hole-free wings so no holed polygon is ever extruded).
3. **Pack each wing** with a **double-loaded corridor** down its spine and **DOE-standard room
   modules** on either side (for MidriseApartment: 1.68 m corridor, 7.62 m unit depth, 11.58 m bay).
4. **Conserve loads.** Per-space-type intensities (an apartment ≠ a corridor: the corridor has zero
   equipment and zero occupancy) are re-normalised so the building's total lighting / equipment /
   people **exactly match the archetype total**, regardless of how the geometry came out
   ("Space-Type-Weighted Normalization").
5. **Wire interior boundaries** correctly: unit↔unit walls = Adiabatic (same setpoint), corridor↔unit
   = matched Surface pairs, courtyard-inner walls = Outdoors (self-shaded, never merged with the outer ring).

**Every dimension traces to a cited source** (DOE prototype geometry, ASHRAE 90.1, IBC) — zero fitted
parameters — and every generated zone carries provenance. The build sequence is **MidriseApartment first**
(its DOE prototype *is* a corridor+units layout, so the generator can be validated by reproducing the DOE
standard), then expansion to offices / hotels / schools.

**Status (2026-07-02):** classifier, packing engine, per-space loads, and conservation are implemented
and pass synthetic unit tests; EnergyPlus stability across all shapes and the DOE-standard reproduction
are still being finalised. **This track is parked pending a root-level engine redesign — on
2026-08-04 the user explicitly excluded it as a direction currently being continued** (record kept,
not deleted, at `docs/docs_TODO/layoutgenerator/`; status as of 2026-08-05). It is **not** yet a
validated baseline.

### 5.1.2 Prototype substitution (`layout_assign`)

**The two names are confusingly similar and describe opposite approaches.** `layoutGenerator`
(§5.1.1) is a **tailor** who measures you and cuts the cloth to your body: right shape by
construction, but building that tailor turned out to be hard, which is why it is parked.
`layoutAssigner` (this section) takes a **beautifully made suit off the rack** and alters it: the
suit's interior is excellent — proper lining, real construction, far better than the tailor could
improvise — but it isn't your shape. Both limitations below follow from that: the wrong-floor-area
problem is being charged for the whole size-4 suit's cloth while measured against a size-1 body, and
the shape-distortion problem (Q3, OPEN-18) is an alteration that takes in the width but not the
length.

Where `zone` mode (§5.1.1) *builds* a room-level floor plan from a real footprint, `layout_assign`
takes the opposite approach: it **replaces the whole building with a validated DOE/ASHRAE 90.1
baseline prototype IDF** for the building's archetype (E+ 23.1 library), then scales that baseline
to fit — plan geometry by `√S`, internal loads by `S`, where `S` is the real building's floor area
divided by the baseline's own. The result carries the DOE prototype's real, exact zone count (1 to
256 depending on archetype) rather than a generic core/perimeter approximation.

**Storey matching.** A real building is rarely the same height as its assigned prototype. Before
this arc, every real building silently inherited the prototype's own native storey count regardless
of its real height. `match_storeys()` (`openubem/geometry/layout_assigner.py`) fixes this for one
case: it computes a residual `Zone.Multiplier` on the prototype's middle repeatable floor band so
the *total simulated storeys* equal the real building's `num_floors`.

**Its reach is narrow, and that is a design decision, not an oversight.** The mechanism only
expresses `n_proto ∈ {1, 3}`, and only when the real building is *taller* than its prototype
(`n_real > n_proto`). `SmallOffice` (2,848 fleet buildings, `n_proto == 2`) and every
`n_proto ≥ 4` archetype fall back permanently, as does any building *shorter* than its prototype —
the common case at the fleet's median size. A later correctness fix narrowed the taller case further
still: `HighriseApartment` now only matches at `n_real ∈ {10, 18, 26, …}`, `MidriseApartment` only at
even `n_real ≥ 4`. Extending the mechanism to the shorter case was considered and explicitly
declined: storeys stay invisible in the building's rendered geometry either way (a `Zone.Multiplier`
changes simulated energy, never a vertex), so extending it would perturb the thermal model of the
majority of buildings that currently run untouched, in exchange for reach rather than correctness.

**The consequence: the floor area an EUI is divided by is not always the floor area simulated.**
Every EUI this mode reports divides simulated energy by the building's *nominal* floor area
(`footprint_area_m2 × levels`), never by the floor area EnergyPlus actually simulated. Where storey
matching applies, those two areas agree (**measured**, 6 real buildings with the verifying
`eplusout.eio` file retained: within ~0.002%). Where it does not apply — most of the fleet — they can
differ sharply: a real one-storey building assigned a four-storey `MidriseApartment` prototype gets
its one storey's worth of floor area divided into *four storeys'* worth of simulated energy, giving
**a correct number for the wrong building**. (**Inferred from the code contract, not separately
measured:** this is the situation for most of the fleet — 6,939 of 7,442 evaluated buildings.) This
is why `layout_assign` is not used for fleet-level EUI reporting today (§5.1).

Full mechanism detail, the fleet-scale evidence above, and the structural comparison against the
other four modes: §10 of
[`Results/OpenUBEM_results_Resolution.md`](Results/OpenUBEM_results_Resolution.md) and the frozen
arc record,
[`docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md`](../docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md).
Zone-count fidelity across all 28 mapped archetypes, T20 harvest:
![layout_assign zone-count fidelity vs. the other four modes](../docs_DONE/SETUP/layoutAssigner/figures/layout_assign_vs_modes_zone_fidelity.png)

### 5.2 Temporal resolution

- **Annual run period**, **8760 hourly timesteps**.
- Schedules (occupancy, lighting, equipment, thermostat setpoints) are hourly fractional
  profiles drawn from DOE prototype building schedules per archetype.

### 5.3 What the resolution is *not*

OpenUBEM is a **stock-level / neighbourhood** model. It is deliberately not a
detailed-design tool: it does not model individual rooms, specific duct/plant networks,
occupant behaviour per unit, or sub-hourly dynamics. The archetype + adaptive-zoning
approach is the trade-off that makes thousands of buildings tractable.

---

## 6. Reporting: simulated vs. reconstructed energy

EnergyPlus, as configured, meters four end-uses (heating, cooling, lighting, equipment;
fans separately). Real buildings also use energy for pumps, hot water, refrigeration, and
cooking. The **reporting layer** adds those missing service loads back using published
CBECS-2018 end-use fraction splits — producing a "reconstructed" whole-building EUI that is
comparable to a real utility total. This is **post-processing only**: it never re-runs the
simulation or changes the physics. Full method in
[`simulated_vs_reconstructed_methodology.md`](simulated_vs_reconstructed_methodology.md).

---

## 7. Locations

### 7.1 Where it can run

Anywhere OpenStreetMap has building footprints and a weather station exists within ~300 km
(the EPW search radius). The four input modes are address, coordinate, bounding box, or a
pre-downloaded OSM XML file.

### 7.2 Where it has been validated

OpenUBEM has been validated at neighbourhood scale across **three U.S. cities**, in a
**12-cell matrix** (four urban-density cells per city), totalling **8,160 buildings** with
100% EnergyPlus success:

| City | Density cells | Measured benchmark |
|---|---|---|
| **New York City** | centre / urban / suburban / rural | NYC Local Law 84 (LL84) |
| **Los Angeles** | centre / urban / suburban / rural | LA EBEWE |
| **Austin** | centre / urban / suburban / rural | CBECS proxy |

All buildings are also scored against the **national CBECS 2018** survey across three census
regions (mid-Atlantic, Pacific, West-South-Central). Every validation gate is **report-only
— never tuned to pass**.

**Headline result (adopted baseline):** city-overall EUI within **±9%** of measured in all
three cities (NYC +2.1% / LA −3.7% / Austin −8.6%), with national CBECS NMBE and R² passing
in all three regions — using a **zero-fitted-parameter** model.

---

## 8. Visualizing results — the interactive 3D viewer

Alongside the static 2D EUI choropleths (`openubem/outputs/comparisons/phaseE_overview_grid.png`), OpenUBEM
produces an interactive, browser-based **3D viewer** of a simulated neighbourhood — the navigable 3D analogue
of that flat grid. Each building is extruded to its real massing and colour-coded by simulated energy use; you
can orbit the neighbourhood, click a building, and drill into its surfaces. It ships as **one self-contained
HTML file** you open by double-clicking: no server, no install, no network. (Reference: `openubem/viz/`; pilot
output `openubem/outputs/nyc_centre_viewer.html`.)

### 8.1 The two constraints it never breaks

1. **Faithful-to-model.** It renders *exactly* what the pipeline produced — real IDF geometry, real
   `05_results.csv` values — and never fabricates geometry or interpolates a value. Where a fact is *absent* in
   the source (e.g. a legacy run with no confidence field), it shows **"not recorded"**, never a made-up default.
2. **Self-contained / offline / reproducible.** The 3D engine, styles, scene data, and map background are all
   inlined; the file opens from `file://` with **zero external network requests**, and rebuilding it from the
   same run gives a byte-identical file.

### 8.2 What it shows

| Layer | Detail |
|---|---|
| **Energy colouring** | Per-building `total_eui_kwh_m2` extruded + shaded on a sequential viridis/cividis ramp (quantile-5 / continuous toggle) — the same quantity as the 2D grid, in 3D. |
| **Two levels of detail** | *Neighbourhood:* buildings as masses for fast navigation. *Building:* on select, a building drills into its individual surfaces **and windows/doors**. |
| **Provenance** | Per-building lineage in the same panel — resolution-mode border, trust badge, a hatch for failed buildings, and a detail pane with the raw `data_quality_flag` tokens. (Novel — no comparable UBEM viewer ships per-building provenance.) |
| **Zone honesty** | A building's interior "zone breakdown" opens **only** when the pipeline made real zone geometry (`perimeter_core` / `room_layout`, §5.1). Synthetic zones are prohibited. |

### 8.3 Map basemap + flat-footprint clarity *(added 2026-07-03)*

- **Map basemap.** Buildings sit on a real street map (© OpenStreetMap contributors © CARTO), so each
  neighbourhood's exact location is visible — the same context as the 2D grid. Faithfulness is kept by baking
  the map **once at export time** (fetched, reprojected to the run's UTM frame, embedded as an image) rather
  than streaming live tiles, so the shipped file stays fully offline.
- **Flat-footprint clarity.** Some very large footprints render nearly flat because OpenStreetMap carries no
  above-ground height for them — the clearest case is **Grand Central Terminal** (an underground train station:
  no floors/height in OSM). These now get a distinct style and a **"Height: not in OSM — footprint only"** badge
  so they read as an honest data gap, not a broken building. Their geometry is left untouched — no height is
  invented.

### 8.4 How it's produced, and coverage

The viewer is a **Step-5 post-processor**: after a run's `05_results.*` exist, it reads the run's geometry
(`01_buildings.gpkg` + archived IDFs), values, and provenance, assembles a CityJSON scene in one shared UTM
frame (EPSG:32618), and injects it — with the vendored 3D engine — into a frozen HTML shell, writing
`openubem/outputs/<run_id>_viewer.html`. The per-run step is pure Python; the engine is built once and vendored.
It is built and validated on the **nyc_centre** pilot first, then batch-generated for all **12 phaseE cells**
(NYC / LA / Austin × Centre / Urban / Suburban / Rural). Full engineering detail:
`docs/docs_DONE/VISUALS/3D-visualization/PLAN_3dviz_implementation.md`.

---

## 9. Two properties worth knowing

- **Deterministic & reproducible.** All stochastic operations use a seeded RNG; artifacts
  carry provenance columns and versioned schemas. The same inputs give the same outputs.
- **Resume-capable.** Step 4 writes a manifest, so a partially-completed fleet run resumes
  without re-simulating buildings that already succeeded — important at city scale.

---

## 10. Where to go next

| You want… | Read |
|---|---|
| The full feature reference | `README.md` (root) |
| **Outdoor analysis — UTCI, microclimate, site measurements** *(the outdoor counterpart to this document; §11 below, Stage 6 is built and live-run-verified on real geometry)* | [`OpenUBEM_outdoor_analysis_reference.md`](OpenUBEM_outdoor_analysis_reference.md) |
| The interactive 3D viewer (§8) design + tasks | `docs/docs_DONE/VISUALS/3D-visualization/PLAN_3dviz_implementation.md` |
| The simulated-vs-reconstructed energy method | `docs/docs_EXPLANATION/simulated_vs_reconstructed_methodology.md` |
| The binding design specs | `docs/docs_main/` (cross-cutting) + `docs/docs_stepN/` (per step) |
| The validation record | `docs/validations/` |
| Current project status | `docs/PROJECT_CHECKLIST.md` |

---

## 11. Outdoor microclimate & thermal comfort (Stage 6)

Stages 1–5 answer *"how much energy does this neighbourhood's buildings use?"* Stage 6 answers the
complementary question: **what does it feel like to stand outside in it?** It is a **separate
analysis product, not a headline OpenUBEM output alongside EUI and carbon** — EUI is validated
against measured data (LL84, EBEWE, CBECS); Stage 6's numbers are not validated against any
measurement, so they are kept out of `05_results.*` and the neighbourhood summary rather than
sitting beside validated numbers with borrowed authority. Stage 6 is invoked explicitly, by its
own runner (`scripts/run_step6_microclimate.py`); it never runs as part of a standard pipeline
run, and it reads Stage 5's outputs read-only.

Given a run's buildings, resolved weather file, and (optionally) real EnergyPlus exterior surface
temperatures, Stage 6 computes four physical driver fields at pedestrian height (1.1 m) over a
selected analysis window — air temperature, humidity, wind speed, and mean radiant temperature —
and combines them into the **Universal Thermal Climate Index (UTCI)**, an equivalent temperature
on a standard 10-class hot/cold stress scale. It also derives sky-view-factor and shadow geometry,
ground and facade surface temperatures, and two population-exposure metrics (person/area-hours of
extreme heat, cumulative thermal stress). Outputs are per-hour GeoTIFF rasters plus a
per-building GeoPackage that joins outdoor heat exposure onto each building's own energy results —
the question a plain microclimate tool cannot ask: *which buildings sit in the worst outdoor heat?*

### 11.1 What Stage 6 computes

Everything below is **built and live-run-verified on real geometry**, not designed-and-pending.

| Layer | What it is | Where it comes from |
|---|---|---|
| **Radiative geometry** | Sky view factor `Ψsky` (how much sky a point can see) and 32-azimuth horizon angles; per-hour building and vegetation shadow rasters | Computed once per site from the building massing — the dominant cost of a run |
| **Surface temperatures** | Ground temperature and facade temperature | Empirical tier by default; an optional tier reads **real EnergyPlus exterior surface temperatures** back out of Stage 4 |
| **Four driver fields** | Air temperature `Ta`, humidity, wind speed `v`, mean radiant temperature `Tmrt` | `Tmrt` from a 6-directional radiant flux balance on a standing person; wind downscaled from the EPW's 10 m reading to pedestrian height |
| **UTCI** | The four fields synthesised into one equivalent temperature on the official 10-class cold/heat stress scale | The COST-730 Bröde 210-term operational polynomial, transcribed from the canonical Fortran source and matched to the reference table at `1e-6` |
| **Exposure metrics** | **CTSI** (cumulative thermal stress, °C·h above the comfort threshold) and **PHEH** (person-hours above 46 °C), aggregated per parcel | Joined onto each building's own energy results |
| **Mitigation scenarios** | Tree canopy, PV canopy, cool pavement, cool roof, high-albedo facade — each a *domain-layer* edit (albedo, canopy), never a physics change | Compared against published effect sizes |

Outputs are per-hour **GeoTIFF rasters**, figures on the official palette, and a per-building
GeoPackage — which lets Stage 6 ask the question a standalone microclimate tool cannot: **which
buildings sit in the worst outdoor heat, and what is their energy use?** UTCI can also be switched
on as an optional layer in the interactive 3D viewer (§8); it is **off by default**, and a run
without it rebuilds the viewer byte-identically.

### 11.2 What has actually been run, and what is honestly limited

Stage 6 has run on **all 12 validated cells** (NYC / LA / Austin × centre / urban / suburban /
rural, 8,160 buildings) and in depth on `nyc_centre` (738 buildings), producing physically
plausible results — peak UTCI **44.6 °C**, *"very strong heat stress"*, on a hot July week, with a
domain-mean CTSI of 780 °C·h. Four limitations are worth knowing before quoting any number:

- **None of it is validated against measurement.** There is no outdoor thermal-comfort measurement
  campaign for any of the twelve cells. Every gate in Stage 6 is internal-consistency or
  behavioural. This is exactly why UTCI is kept out of `05_results.*` — see above.
- **The optional `macdonald` wind tier is safe, not accurate.** After two rounds of fixes it
  produces zero physically-impossible values across 113 million checked cell-hours, but it does so
  by falling back to the default `cost730` tier for 31.6 % of cell-hours on a real mid/high-rise
  domain — outside the low-rise regime it was built for. The default tier was never affected.
- **Cool pavements can make pedestrians worse off.** Raising pavement albedo genuinely cools the
  ground and the air, but reflects the shortwave load onto the human body, so UTCI *rises*. This is
  a real, literature-backed result, not a model artifact — and it doubles as a correctness test.
- **Buildings with no known height cannot cast shade.** Cells where upstream `height_m` is missing
  compute as a flat open field rather than an urban canyon. Four cells were affected; a follow-up
  fix cleared the three worst by routing height through a multi-source fusion tier, and a residual
  remains in two rural cells (36.4 % and 19.2 % of buildings still unknown), documented and
  forwarded to a future data-acquisition arc.

**How to run it:** `scripts/run_step6_microclimate.py`, pointed at a completed run. It never runs
implicitly. Full detail, every measured range, and the current status of each field:
[`OpenUBEM_outdoor_analysis_reference.md`](OpenUBEM_outdoor_analysis_reference.md).

---

*OpenUBEM — fundamentals overview. Plain-language orientation; the design docs remain the
binding source of truth. 2026-07-01 (§8 interactive 3D viewer added 2026-07-03, §11 outdoor
microclimate added 2026-07-24, §11 expanded to the completed Stage-6 feature set 2026-07-25 on
arc closure).*
