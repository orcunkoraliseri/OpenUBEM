# Technology Transfer — `idf_reader` BEM Toolkit → OpenUBEM

**Date:** 2026-09-17
**Author:** manager session (audit/plan role)
**Source analysed:** `C:\Users\o_iseri\Desktop\idf_reader\docs_BEM_Explanation\` (11 methodology docs, read in full except `debug_References.md` and `EEM_setup.md` results tables)
**Target:** `C:\Users\o_iseri\Desktop\OpenUBEM\` (code + `docs/docs_EXPLANATION/`)
**Status:** analysis + recommendation. Nothing implemented. No OpenUBEM file was modified.

---

## 0. Ownership and what "transfer" means here

`idf_reader` was developed inside a postdoc position and is **not the user's property**. OpenUBEM is
100 % the user's. Everything below is therefore written as **re-implementation guidance**, not as a
copy instruction:

- **Transfer the method, cite the public source.** Every parameter worth taking traces to a published
  standard (ASHRAE 90.1-2022, NECB 2017 tables, NBC 9.36, PVWatts defaults, IES RP-1, EnergyPlus IDD
  memos) or to a peer-reviewed paper. Take the *pointer*, re-derive the value from the public source,
  write OpenUBEM's own code.
- **Transfer the hard-won negative results freely.** "EnergyPlus does X and it costs you Y" is an
  engine fact, not project IP. These are the highest-value items in this report and the cheapest to act on.
- **Do not copy source files, IDF libraries, curated prototypes, registries, or result numbers.**
  Section 4 lists what must stay behind.

---

## 1. The two projects in one paragraph each

**`idf_reader`** simulates a *closed, hand-curated* stock: ~30 reference prototype IDFs (16 ASHRAE
90.1-2022 DOE/PNNL commercial, 3 IECC 2024 single-family, 2 datacenter, 7 OpenStudio supplementals,
1 project-built near-zero building), placed by hand into 35 canonical Canadian neighbourhood units of
≤ 24 buildings. Its depth is on the **vertical** axis: each building can be run as DEFAULT / Ideal-Loads /
high-performance-envelope / a staged retrofit ladder / with or without PV, transformed
first to a Canadian prescriptive code baseline (NECB 2017 or NBC 9.36 + BTAP internal loads), across
three EnergyPlus versions. One installation serves five publications.

**OpenUBEM** simulates an *open, discovered* stock: any neighbourhood on Earth with OSM footprints,
8,139 buildings validated across 12 cells, each building built from its own true footprint, classified
into one of 30 archetypes, zoned adaptively, simulated once, validated against measured data (LL84,
EBEWE, CBECS). Its depth is on the **horizontal** axis: coverage, provenance, imputation honesty,
reproducibility, and a per-building 3D viewer.

**The complement is exact.** `idf_reader` knows what to *do* to a building once you have it;
OpenUBEM knows how to *get* thousands of buildings and prove the number. The transfer is almost
entirely one-directional: scenario depth, code-compliance transformation, PV, and a list of EnergyPlus
landmines flow into OpenUBEM.

---

## 2. Transfer candidates, ranked

Ranking is **value ÷ effort**, highest first. Each item states where it lands in OpenUBEM.

---

### T1 — Ground coupling: OpenUBEM is silently on the EnergyPlus 18 °C default
**Priority: HIGHEST. Effort: 1 day to census + decide, 1 day to implement.**

**What `idf_reader` found.** A census of all 321 library IDFs showed there was no ground-model
convention at all: 68.2 % used `GroundFCfactorMethod`, 17.1 % used a plain `Ground` boundary with
**no ground-temperature object at all** (so the EnergyPlus default, a flat 18 °C year-round), 8.4 %
used `Ground` + `Site:GroundTemperature:BuildingSurface`, and 6.2 % used **both methods inside the
same file**. The split followed building type, which meant it ran straight through the density ladder
the papers were comparing — low-rise residential on one method, mid/high-rise on another. Two measured
defects followed: the F-factor temperature series shipped in the DOE prototypes is *Buffalo air
temperature lagged three months*, about **12 K too warm through the heating season** while the annual
mean looks fine; and the F-factor formula `Q = F × ExposedPerimeter × ΔT` models core-slab loss as
**exactly zero** (one archetype: 893 W/K of ground conductance against 37,612 W/K of envelope — 2.4 %;
the same floor modelled with layers gives 48.5 %, a factor of twenty).

**Why this matters to OpenUBEM right now.** OpenUBEM writes `Outside_Boundary_Condition = "ground"` on
every z=0 floor (`openubem/idf/surfaces.py:527`, confirmed at `:990`) and **writes no
`Site:GroundTemperature:*` object anywhere in the package** (grep: zero hits). Every one of the 8,139
fleet buildings, and every European district building, therefore sits on a flat 18 °C ground all year —
*by omission, not by decision*. The good news: 18 °C is close to defensible. The EnergyPlus IDD memo
warns explicitly against using undisturbed weather-file soil temperatures ("*too extreme for the soil
under a conditioned building*"), and under a heated Montreal-class building the right range is roughly
15–19.6 °C, annual mean ≈ 17.3 °C. So OpenUBEM is probably not wrong — **it just cannot say why it is
right**, and an undisturbed-soil "fix" would make it worse.

**Recommended action (three steps, in order):**
1. **Census, don't assume.** One script over the emitted IDFs: count ground-floor surfaces by boundary
   condition, count ground-temperature objects, per archetype and per resolution mode. `layout_assign`
   substitutes DOE prototype IDFs wholesale, so that path almost certainly *does* carry F-factor floors
   and the lagged-Buffalo series — meaning OpenUBEM may already be mixing two ground models across
   resolution modes without knowing it. That would be a resolution-mode comparison artifact, exactly
   the defect `idf_reader` documents.
2. **Write the object explicitly**, with the chosen values and a citation, even if the values equal
   today's implicit default. An inherited default is not a modelling choice; a written one is.
3. **Record the magnitude** rather than chasing it: `idf_reader` measured the whole ground-model
   question at **1.8–2.4 % of site energy** on one archetype. That is the size of the prize — worth a
   documented decision, not worth a campaign.

**Lands in:** `openubem/idf/builder.py`, `openubem/idf/surfaces.py`, a new paragraph in
`docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md` §3, one new OPEN item.

---

### T2 — "Skip-when-better", and the two window traps
**Priority: HIGH. Effort: hours.**

**What it is.** Every envelope/efficiency clamp in `idf_reader` is one-directional: a surface or
component that **already meets or beats the target is left untouched**. Stated as a rule, it sounds
obvious; the two failures it prevents are not.

- **Trap 1 — replacing already-good glazing makes things worse.** ASHRAE 90.1-2022 prototype windows
  are already at U ≈ 0.363–0.382 W/m²K. Overwriting them with a "high-performance" U = 0.926 assembly
  *raises* SHGC from ≈ 0.37 to 0.57 and increased cooling by **up to +54 %** on small internally-loaded
  buildings.
- **Trap 2 — orphaned shading controls silently corrupt unrelated end-uses.** Replacing a fenestration
  construction that a `WindowShadingControl` with `Shading Type = SwitchableGlazing` points at leaves
  the control orphaned. EnergyPlus does not always fail; the observed symptom was a **30–50 % phantom
  reduction in lighting, equipment and water-heating** — all of which are envelope-independent, which
  is exactly why it was hard to spot.

**Why it matters to OpenUBEM.** `envelope_patcher.patch_envelope()` (called at
`openubem/idf/builder.py:555`) patches a DOE baseline's native Buffalo CZ 6A envelope to the real
building's vintage and climate zone, on the `layout_assign` path, for every building with a DOE
baseline. That is precisely the operation both traps live in. Fundamentals §5.1 already records that
this patch "has not been separately re-validated for physical correctness" — trap 2 is the failure
mode that such a validation should look for first, because it shows up in *lighting*, not in heating.

**Recommended action.** Assert the direction of every patch (post-patch U ≤ pre-patch U for a
tightening, and the reverse for a loosening to an older vintage); before replacing any fenestration
construction, check whether a `WindowShadingControl` references it and skip if so; add a regression that
fails if a pure envelope change moves lighting or equipment energy by more than ~1 %.

**Lands in:** `openubem/geometry/envelope_patcher.py`, plus one gate in the existing test suite.

---

### T3 — Engine-version traps: per-IDF version routing, and unit-based column parsing
**Priority: HIGH. Effort: hours. Prevents a class of silent multi-hour loss.**

Three separate lessons, all cheap:

1. **Route the engine per IDF, never per fleet.** An archived 33-unit set was 29 IDFs at E+ 22.1 and
   4 at 23.1. Pinning one engine fleet-wide is wrong *in both directions*: a 23.1-authored DX coil run
   on 22.1 loses an inserted field and **every later field slides up by one**, killing the run with
   Severes and a Fatal **in under a second**, before the simulation starts. This cost two relaunches.
   `idf_reader` reads the `Version,X.X;` field from each IDF header and resolves the executable from it.
   OpenUBEM standardises on 23.1, but `layout_assign` ingests DOE prototype IDFs from an external
   library — the moment that library is refreshed or mixed, this trap is live.
2. **Parse results by unit, never by column name.** E+ 24.2 renamed the IdealLoads reporting column
   from `Electricity` to `District Heating Water`. `idf_reader` filters on recognised energy units
   (GJ, kWh, J, kBtu, Btu, MJ) instead of names, so the parser survives version bumps.
   Worth checking `openubem/results/parser.py` against this.
3. **An engine upgrade changes physics, not just syntax.** The DOE Supermarket reports
   **+56.6 % `NaturalGas:Facility`** on E+ 22.1 vs 24.2 from a structurally equivalent IDF. Both
   engines are in bit-identical zone state at 10:30 (humidity ratio 0.008138, RH 50.006 %); one
   timestep later 24.2 has switched the cool-reheat loop off and 22.1 has found a stable equilibrium
   that runs **7.5 hours continuously**. The cause is a control termination condition, not the IDF —
   the downgrade was explicitly ruled out by test.
   **Rule for OpenUBEM:** any EnergyPlus version change must be regression-tested **per archetype and
   per end-use meter**, not on total EUI. A 57 % gas swing on one archetype can hide inside a fleet
   total that still passes its ±9 % validation gate.

**Lands in:** `openubem/simulation/runner.py`, `openubem/results/parser.py`, and an entry in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.

---

### T4 — Code-baseline transformation as a data-driven applier chain
**Priority: HIGH. Effort: 1–2 weeks. Directly reusable by the European arc.**

**What it is.** `idf_reader` turns a US prototype into a Canadian-code baseline through a fixed,
auditable chain, driven by **JSON tables, not hardcoded constants**:

```
create_necb17_idf()
  1 construction swap    → NECB_Z6_Wall / _Roof / …        (necb_2017_uvalue_table.json)
  2 window U clamp       → ≤ 1.90 (Z6) / 1.60 (Z7A)
  3 LPD clamp            → per space type, substring match  (necb_2017_lpd_table.json)
  4 infiltration         → 1.25e-5 m³/(s·m²)
  5 HVAC efficiency      → COP / η floors                   (necb_2017_hvac_floor_table.json)
  6 OA-HR check          → sidecar warning if OA ≥ 1000 L/s
  7 internal loads       → BTAP occupancy / plug / thermostat schedules
```
Residential goes down a parallel, *deliberately different* path (`NBC 9.36`: envelope + air-tightness
only — no LPD or HVAC clamp, because Canadian housing equipment is governed by EnerGuide labelling,
not a prescriptive table). Every clamp is skip-when-better (T2). Output is a **drop-in folder**:
`00.Baseline_NUs_CAN_MTL/` mirrors `00.BaselineBuildings_NUs/` file-for-file, so the runtime picker
just rewrites a path prefix.

**Why it matters to OpenUBEM.** This is the architecture OpenUBEM's European arc needs and has been
building piecemeal: `openubem/idf/european_physics.py` (TABULA U-values + bridge surcharge),
`european_controls.py`, `envelope_patcher.py`. Three specific pieces are worth lifting as *pattern*:

- **The regulatory split is a feature, not an inconsistency.** Residential and non-residential are
  governed by different codes in Canada and in every European country. Encoding that as two appliers
  with two tables — and **tagging each divergence as deliberate** (§T8) — pre-answers the reviewer
  question "did you apply the same thing to both?".
- **Compliance gates that need no EnergyPlus run.** Four IDF-only tests (walls remapped, window U ≤ cap,
  infiltration ≤ target, LPD ≤ cap per space type) catch transformation errors in seconds, before any
  fleet run. OpenUBEM's gates today are mostly post-simulation; a pre-simulation compliance layer would
  catch a bad European envelope table before 1,200 Speed tasks burn on it.
- **The internal-loads gap is real and it is large.** After a fully compliant NECB envelope transform,
  OfficeMedium came out at 332 MJ/m² against the NRCan BTAP reference of ~450 MJ/m² — a **26 % gap
  that replacing occupancy, plug loads and thermostat schedules did not close**. It was registered as a
  documented, non-blocking `xfail` rather than tuned away. This is the same asymmetry OpenUBEM already
  carries as OPEN-03 (envelope patched to real vintage, internal loads stuck at STD2022) — and the
  useful news is that `idf_reader` *measured* the loads side and found it was **not** the dominant
  driver. That narrows OpenUBEM's suspect list for OPEN-03 to DHW, ventilation/fan energy, and
  schedule-shape × HVAC-sizing interaction.

**Lands in:** `openubem/idf/european_physics.py` + a new `openubem/idf/code_baseline/` with per-country
JSON tables; new IDF-only compliance tests.

---

### T5 — A retrofit scenario layer, built from OpenUBEM's own measures
**Priority: HIGH value, HIGHEST effort (1–2 months). The biggest product gap.**

**What does not transfer — stated first.** The measure catalogue itself belongs to the host project and
to the papers it supports: its tier structure, its tier names, its measure list and its parameter values
are **not** reproduced here and must not be reproduced in OpenUBEM. No borrowed naming scheme, no
borrowed tiering, no borrowed numbers. OpenUBEM defines its own measures, under its own names, from
public sources.

**What transfers is how such a layer is built** — five design rules. Each is an engine fact or a
research-design lesson, not content:

1. **Measures are data, the applier is code.** One applier module reads a measure table (parameters +
   applicability + citation per row) and mutates the IDF. Adding a measure is a table row, not a code
   branch. This is the same shape as T4's code-baseline chain, and the two should share machinery.
2. **Scenario packaging is a research-design decision, and it must be chosen deliberately.** A
   cumulative ladder (each scenario contains the previous one) answers *"how far can the stock go"*.
   Isolated single-domain runs answer *"which measure first"* — and **a cumulative ladder cannot be
   converted into an order-free attribution**: applying measures in a fixed order mis-credits them by
   **up to ~7 kWh/m²**, which is why a Shapley-style ranking needs the isolated runs. A full factorial
   is a superset of both. For OpenUBEM this is directly a cost decision: 8,139 buildings × 16 cells is
   a very different campaign from × 5. Decide before the first submission, not after.
3. **Gate every measure by an explicit predicate, and publish the gate list in the method doc.** Some
   building types must skip some measures for physical reasons (a measure that targets an end use that
   does not dominate), others for engine reasons (e.g. injecting fenestration objects with blank names
   is an EnergyPlus 22.1 Fatal). Written in the method doc, a gate reads as a physics decision; left in
   the code, it reads as a silent exception.
4. **Clone schedules, never mutate in place.** Every modified `Schedule:Compact` gets a new name and a
   new object. Mutating a shared schedule in a multi-zone IDF silently changes buildings the measure was
   never meant to touch — a real risk in OpenUBEM's `layout_assign` path, where one prototype's
   schedules serve up to 256 zones.
5. **Keep withdrawn measures in the code under a marker, with the reason.** When a measure is cut for a
   particular study, comment it out under a visible marker and record why, instead of deleting it. This
   fits OpenUBEM's existing FINDING/OPEN discipline.

**Where OpenUBEM's own measures come from.** All public: ASHRAE 90.1-2022 and its addenda, NECB 2017 /
NBC 9.36 tables, IECC 2024, ENERGY STAR product criteria, TABULA for the European stock, and published
field data for cold-climate heat pumps (see T10). Same re-implementation rule as §0 — take the pointer,
re-derive the value, write OpenUBEM's own code.

**Why OpenUBEM should want it.** OpenUBEM today answers *"what does this neighbourhood use?"*. Every
urban-planning and policy user — the stated audience in Fundamentals §1 — immediately asks *"and what
if we retrofit it?"*. OpenUBEM has the two things needed for that question and that `idf_reader` lacks:
a real stock with real footprints, and a validated baseline to measure against. The scenario layer is
the missing third.

**Lands in:** a new `openubem/scenarios/` package; a new `05_results` result channel; a new colour mode
in the 3D viewer (Fundamentals §8.5 explicitly describes "retrofit delta" as the template case for a new
result parameter — the wiring is already designed).

---

### T6 — Geometry-aware PV layer
**Priority: MEDIUM-HIGH. Effort: 2–3 weeks. High visibility, low risk.**

**What it is.** PV is sized from the *actual roof geometry*, not assumed. Buildings are classified by
surface-normal tilt into three groups — **A** (any pitched surface > 5°), **B** (all flat, single
Z-level), **C** (all flat, multiple Z-levels) — and each gets the appropriate EnergyPlus object:
`Generator:Photovoltaic` + `PhotovoltaicPerformance:Simple` flush-mounted on pitched roofs (tilt and
azimuth inherited from the surface; qualifying filter tilt 10–80°, azimuth 135–225°; active fraction
0.90, cell efficiency 0.20, `Decoupled` heat transfer), or `Generator:PVWatts` on flat roofs
(one per exterior roof surface, GCR 0.40, 200 W/m² module, 14 % system losses, fixed tilt, azimuth 180°,
surfaces < 0.1 kW skipped). Shared infrastructure (inverter η 0.96, `ElectricLoadCenter:*`) is appended
once, idempotently.

**Five details that are the actual value:**
- **Strip before replace.** 13 ASHRAE prototypes ship with a horizontal 0.6 W/ft² `Generator:PVWatts`
  compliance placeholder. Injecting on top produces duplicate `ElectricLoadCenter:Distribution` objects
  and EnergyPlus errors out. The injector strips seven object classes first.
- **PV is never netted into EUI.** It is reported in dedicated columns (`PV_default_gen`,
  `PV_improved_gen`, `PV_total`), so a measure ladder is never confounded by a generation assumption.
  This matches OpenUBEM's existing separation discipline exactly.
- **A tilted rack is not thermally neutral.** A 45° combined rack is emitted as
  `Shading:Building:Detailed`, so unlike the `Decoupled` pitched generators it **enters the thermal
  model and shades the roof beneath it** — measured site-EUI movement up to **2.3 %** on flat-roof
  units, against 0.007–0.021 % on pitched units that get no rack.
- **North slopes were a real error, and correcting them is not a uniform reduction.** An earlier
  injector put modules on every roof plane including north-facing. After correcting to south-dominant
  only, fleet generation went to 0.925× — but **11 of 33 units went *up***, and the per-unit ratio ran
  0.62 to 1.25, because flat-roof units simultaneously gained from racking. Quote the measured pair, never
  the area figure: halving the array area on gable roofs cost only **26.2–37.7 %** of generation, since a
  north slope at Montreal's latitude yields 36–61 % of the south slope's output.
- **Pitched yield is geometry-bound.** A 3:12 or 6:12 roof gives tilt ≈ 14–27°, well below the ~45°
  northern optimum — so Group A yield per m² is structurally below Group B/C. That is the real
  installation practice, and it should be reported as such, not "corrected".

**Why OpenUBEM is well-placed.** OpenUBEM already extrudes true footprints and has real roof surfaces
per building; the classifier needs only the surface normals it already computes. PV becomes a new
per-building result channel and a new viewer colour mode, using the wiring pattern already specified in
Fundamentals §8.5.

**Lands in:** a new `openubem/idf/pv.py`; result columns in `05_results`; viewer channel.

---

### T7 — Two-phase parallel prep/sim, with the failure contract
**Priority: MEDIUM. Effort: days. Complements Speed, does not replace it.**

**The pattern.** PREP and SIM are two separate pools, never interleaved:

- **PREP** — `ProcessPoolExecutor` (mandatory: `eppy` stores the parsed IDD in class-level globals, so
  threads race), module-level worker functions (mandatory: Windows `spawn` pickles, so closures and
  lambdas cannot cross the boundary), every worker capturing its own stdout via
  `contextlib.redirect_stdout(io.StringIO())` and returning it in the result dict — so the parent prints
  clean, ordered `[PREP n/m]` lines despite non-deterministic completion.
- **SIM** — `ThreadPoolExecutor` on Windows (E+ is a subprocess; threads release the GIL during
  `subprocess.run`, and spawning subprocesses from pool *processes* on Windows is expensive and
  sometimes deadlocks), `ProcessPoolExecutor` on Linux. Each job carries `n_jobs=1` so E+ itself does not
  oversubscribe the cores.
- **The failure contract is the important part.** Application errors (bad path, applier exception) are
  caught **inside** the worker and returned as `ok=False`, so the remaining jobs finish; only executor
  crashes (BrokenProcessPool, OOM) re-raise and abort. And **all prep must succeed before any
  simulation starts** — a failed prep aborts cleanly before a single run slot is consumed.

**Why it matters to OpenUBEM.** The project rule is Speed-first with a local 20-process supplement, and
Speed arrays already cover the SIM half well. The transferable half is **PREP**: OpenUBEM builds
thousands of IDFs before submitting, and the "abort the whole prep phase before consuming any cluster
time" contract is exactly the guard that turns a bad table (a wrong European U-value, a broken archetype
map) from a 1,200-task wasted array into a 90-second local failure. The memory budget is worth copying
too: ~250–450 MB per prep worker (so 8 workers wants 64 GB, 4–5 wants 32 GB).

**Lands in:** `openubem/simulation/parallel.py`, `scripts/cluster/` prep stage.

---

### T8 — The `[REG]` / `[PHYS]` / `[INH]` tag: separating chosen from inherited
**Priority: MEDIUM. Effort: hours. The single cheapest idea in this report.**

**What it is.** In the setup matrix, every row where residential and commercial differ carries one of
three tags:

| Tag | Meaning |
|---|---|
| **[REG]** | Deliberate and required — the two sectors are governed by different codes, so the models must differ |
| **[PHYS]** | Deliberate and physical — a house cannot take a VAV coil uplift; a hospital cannot take a residential preheat tank |
| **[INH]** | **Inherited. Nobody chose it.** It arrived with the source prototypes and survived every transformation |

And then, stated plainly: *"Only the [INH] rows are problems. There are four of them."* The document
ends with a section titled **"The honest list: what is not harmonized"**, ranking the four by how much
leverage a reviewer could get from each, and giving a scripted answer for the two worst — *state the
model per family, state the direction of the error, give the measured magnitude, and do not claim
identical boundary conditions across the series.*

**Why OpenUBEM should adopt it.** OpenUBEM already has strong machinery for *known problems* (FINDING
numbers, OPEN items, the openings register). What it does not have is a way to mark the difference
between **a difference someone decided** and **a difference that simply arrived**. That distinction is
what a reviewer attacks. OpenUBEM has at least three live [INH]-class rows today: the ground boundary
condition (T1), internal loads fixed at STD2022 while the envelope is vintage-patched (OPEN-03), and
the nominal-vs-simulated floor-area denominator under `layout_assign`. Tagging them as inherited —
rather than listing them among decisions — makes the honest list honest.

**Lands in:** `docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md`, as a tag column plus a closing
"what is not harmonized" section.

---

### T9 — Prototype-vs-plot fit check (fail closed, with a named reason)
**Priority: MEDIUM. Effort: days.**

**What happened.** The Buffalo Secondary School prototype is 141.0 × 104.0 m (~11,902 m²). The plot it
was assigned was 142.5 × 71.2 m. Width just fitted; **depth overflowed the plot by 32.8 m**, and the
building visibly hung off its ground in the neighbourhood preview. The fix was to swap in a resized
(~1,266 m²) variant — but the defect was only found *by looking at a picture*.

**Why OpenUBEM has the same class of bug.** `layout_assign` substitutes a whole DOE prototype for a real
building and scales it by `√S` in plan. Fundamentals §5.1.2 already records the consequence in energy
terms (a one-storey building assigned a four-storey prototype gets "a correct number for the wrong
building", affecting an inferred 6,939 of 7,442 buildings). The **geometric** half of the same
mismatch — the scaled prototype's plan extents versus the real footprint's bounding box — is not
currently checked anywhere.

**Recommended action.** A pre-flight check comparing scaled prototype extents against the real footprint
bbox, emitting a named fail-closed reason in the manifest. OpenUBEM already has exactly the right
vocabulary for this from the European arc (`NARROW_FOOTPRINT_LT_8M`, `PARTITION_AUDIT_FAILED`,
`FALLBACK_PENDING_LAYOUT`) — add e.g. `PROTOTYPE_EXTENT_EXCEEDS_FOOTPRINT` and let the viewer badge it,
the same way flat-footprint buildings get "Height: not in OSM".

**Lands in:** `openubem/geometry/layout_assigner.py`, manifest columns, viewer badge.

---

### T10 — AirflowNetwork at district scale (a landmine to record now, not to hit later)
**Priority: LOW today, HIGH the day infiltration is upgraded. Effort: one debug-reference entry.**

**What happened.** A 24-building neighbourhood with `MultizoneWithDistribution` passed validation, then
crashed **after ~5 hours of runtime** on a high-wind March afternoon: airflow reversed through a return
duct linkage, the solver matrix went singular, Fatal. The same IDF as a *single* building runs clean with
zero Severes. The cause is scale: 24 buildings × 24 independent duct systems sharing one solver matrix
under parameters designed for one isolated house. Switching to `MultizoneWithoutDistribution` keeps
envelope cracks, attic/crawlspace vents, garage leakage, and both wind and stack pressure; it drops only
the duct sub-model — costing ≤ ~5 % EUI while running **roughly 10× faster** (35 min vs 5 h 43 m), and
leaving relative comparisons valid because every variant uses the same mode.

**Also worth recording:** which buildings fail is *variant-dependent* — a pure envelope change shifts
zone temperatures, shifts the stack component, and a different set of buildings crosses the critical
pressure threshold. A crash that moves when you change insulation is a solver-conditioning problem, not
a geometry problem.

**Why record it now.** OpenUBEM does not use AirflowNetwork today. The day infiltration modelling is
upgraded — a plausible next step for the European residential work, where air-tightness drives heating —
this trap is waiting at exactly district scale. One debug-reference entry costs minutes and saves a
multi-day investigation.

**Lands in:** `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (new or existing AirflowNetwork chapter).

---

### T11 — Benchmark anchor set and cold-climate heat-pump literature
**Priority: LOW-MEDIUM. Effort: hours. Only if OpenUBEM goes north or adds heat pumps.**

Four published anchor sets are consolidated in `BEM_reference.md` and used as **sanity checks, never as
calibration targets**: DOE Commercial Building Benchmark Models (2008, 16 CZs), NRCan Canadian national
median reference values (2018), the ASHRAE 90.1-2022 energy-savings analysis, and the 2024 IECC
residential savings analysis. Independent EUI anchors for NECB 2017 Zone 6 also exist
(EnerSys/Pembina 2018: Medium Office 126, High-rise MURB 166, Large Office 104 kWh/m²·yr).

If the retrofit layer (T5) is ever built, the cold-climate ASHP literature transfers with it: CCHT/NRCan
field testing measured **up to 15 % seasonal COP loss to defrost cycles**, and **20–30 % COP drop at
−25 to −10 °C** (reaching ~1.5) with 30–50 % capacity fade. That is the difference between a nameplate
COP assumption and a defensible one — and OpenUBEM's zero-fitted-parameter stance makes the
distinction load-bearing.

**Lands in:** `docs/docs_EXPLANATION/` benchmark section, only when a Canadian district or a heat-pump
scenario actually exists.

---

## 3. What OpenUBEM already does better (do not import)

Recording this so the transfer stays one-directional where it should be.

| Domain | OpenUBEM's position |
|---|---|
| **Stock acquisition** | OSM → cleaned footprints → archetype classification, anywhere on Earth. `idf_reader` hand-curates ~30 IDFs and hand-places 35 neighbourhoods. |
| **Weather** | Real station resolution per building (~300 km EPW search, measured station selection). `idf_reader` uses Buffalo-as-Montreal proxy geometry with Montreal weather — a compromise OpenUBEM does not need. |
| **Provenance & imputation honesty** | Per-row tagging (`IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD`, `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`), "an imputed input is tagged at the row, not in a footnote", absent results rendered as absent. Nothing comparable in `idf_reader`. |
| **Validation against measured data** | LL84 / EBEWE / CBECS, ±9 % city-overall, report-only gates never tuned to pass. `idf_reader` benchmarks against published medians, which is weaker. |
| **Reproducibility** | Seeded RNG, versioned schemas, byte-identical rebuilds, sha256 of every input in `sources.json`. |
| **Visualisation** | Self-contained offline 3D viewer with per-building provenance, "not recorded" instead of defaults, honest disabled states. `idf_reader` produces static HTML/CSV reports. |
| **Scale discipline** | 8,139 buildings, Speed 32-wide arrays, resume-capable manifests. `idf_reader` maxes at 24 buildings per neighbourhood. |

---

## 4. Do not transfer

| Item | Reason |
|---|---|
| Curated IDF library, CHV building, datacenter archetypes, downgraded OpenStudio IDFs | Belongs to the host project. The *underlying* DOE/ASHRAE prototypes are public — get them from the public source, as OpenUBEM already does. |
| `neighbourhood_registry.py` (35 hand-placed neighbourhoods) | OpenUBEM gets geometry from OSM; hand placement is the thing OpenUBEM exists to avoid. |
| Buffalo-as-CZ6A-proxy | A workaround for having no Canadian prototypes. OpenUBEM resolves a real weather station per building. |
| The menu-driven interactive interface | Incompatible with a non-interactive, cluster-submitted pipeline. |
| `GroundFCfactorMethod` as a ground model | Adopting it would import defect 2 (core-slab loss modelled as exactly zero) into a model that currently builds layered floors correctly. Take the *census habit*, not the method. |
| Any published result numbers, EUI ladders, or figures | Other people's results. OpenUBEM cites its own. |
| Source files, verbatim text, or code | See §0. Re-implement from the cited public standards. |

---

## 5. Recommended sequence

| Order | Item | Why here | Rough effort |
|---|---|---|---|
| 1 | **T1** ground-coupling census | An unstated default sits under every number OpenUBEM has published | 2 days |
| 2 | **T3** version routing + unit-based parsing + per-archetype upgrade regression | Prevents silent losses; hours of work | 1 day |
| 3 | **T2** skip-when-better + the two window traps | Directly guards `envelope_patcher`, which is already flagged as un-revalidated | 1 day |
| 4 | **T8** `[REG]`/`[PHYS]`/`[INH]` tags + "what is not harmonized" | Cheapest credibility gain available | 0.5 day |
| 5 | **T10** AirflowNetwork entry in the debug reference | Minutes now, days saved later | 0.5 day |
| 6 | **T9** prototype-vs-footprint fit check | Closes the geometric half of a defect whose energy half is already documented | 3 days |
| 7 | **T7** two-phase prep/sim contract | Stops bad tables from burning cluster arrays | 3 days |
| 8 | **T4** code-baseline applier chain | The European arc needs this architecture regardless | 1–2 weeks |
| 9 | **T6** PV layer | New visible result channel; viewer wiring already designed | 2–3 weeks |
| 10 | **T5** retrofit scenario layer | The largest product gap, and the largest build | 1–2 months |
| — | **T11** benchmarks | Only when a Canadian district or heat-pump scenario exists | hours |

Items 1–5 are one working week in total and carry most of the credibility value. Items 8–10 are
arc-sized and each deserve their own plan doc.

---

## 6. Sources read

| Source doc | Used for |
|---|---|
| `BEM_methodology.md` | T2, T3, T6, T9, T10, §3, §4 |
| `CAN_transformation.md` | T4 |
| `NUs_Setup_Matrix.md` | T1, T5, T8 |
| `System_Setup_NUs_Publications.md` | T1, T5, T8 |
| `EEM_setup.md` | T5 (architecture only; catalogue not transferred) |
| `PV_methodology.md` (§5 of `BEM_methodology.md`) | T6 |
| `parallel_idf_prep_detailed.md` | T7 |
| `Resizing_methodology.md` | T9 |
| `extra/opt8_neighbourhood_WithoutDistribution.md` | T10 |
| `extra/Supermarket_NaturalGas_V221_vs_V242.md` | T3 |
| `BEM_reference.md` (index entry + §7 of methodology) | T11 |
| `README.md` | doc map |

**OpenUBEM state verified for this report (not assumed):** no `Site:GroundTemperature*` object is
emitted anywhere in `openubem/` (grep, zero hits); ground floors are written as plain `"ground"` at
`openubem/idf/surfaces.py:527`; `patch_envelope` is called at `openubem/idf/builder.py:555`; no PV and
no retrofit/scenario module exists in the package; HVAC families and COPs are resolved from
`hvac_cop_by_archetype.json` at `openubem/idf/hvac.py:625`.

---

*End of report. No OpenUBEM code or doc was modified. Items T1, T3 and T8 are candidates for OPEN
register entries if adopted.*
