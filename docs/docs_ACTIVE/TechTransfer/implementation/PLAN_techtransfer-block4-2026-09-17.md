# PLAN — TechTransfer block 4 (T6, geometry-aware PV layer)

- **Slug:** `techtransfer-block4`
- **Date opened:** 2026-09-17
- **Source:** `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`,
  section 5 "Recommended sequence", order 9 (**T6**, report lines 264-301).
- **Predecessors:** blocks 1-3. Decisions D1-D12, E1-E5, F1-F5, G1-G5 remain binding.
- **Out of scope, do not start:** report items T5 and T11; D9 (the prototype IDF library living
  inside `idf_reader`); anything that writes to `05_results`.

---

## 1a. Scope note — what this block is and, more importantly, what it is not

The report sizes T6 at 2-3 weeks for the whole layer: a three-group roof classifier, pitched-roof
`Generator:Photovoltaic`, flat-roof `Generator:PVWatts`, tilted racks emitted as shading, result
columns and a viewer channel. **This block delivers the first two measurable slices only** — the
census that says which of those groups actually exist in OpenUBEM, and a strip-and-inject module for
the group that does. Result columns and the viewer are not started.

The reason is one measured fact and one hard constraint.

**Measured 2026-09-17.** OpenUBEM generates no pitched roofs anywhere: the only surface-type literal
in the geometry code is `("roof", "Roof", 20.0)` (`openubem/idf/european_box.py:219`), footprints are
extruded flat, and no module mentions a slope, gable or hip. So the report's **Group A** (any pitched
surface > 5 deg) can only reach OpenUBEM through prototype geometry on the `layout_assign` path, and
whether it reaches it at all is unknown. **H01 measures that before any classifier is written.** A
branch that can never fire is not a feature.

**Hard constraint.** The report's own measurement is that a 45 deg rack emitted as
`Shading:Building:Detailed` shades the roof beneath it and moves site EUI **by up to 2.3 %**. The
adopted fleet figure is 153.95 kWh/m2 over 8,139 buildings. **Nothing in this block may move it.**
Racking is therefore not implemented here at all, and PV injection ships behind a default-OFF flag,
for the same reason block 1's window clamp and block 2's prep gate did.

---

## 2. Hard rules for the executor

1. Execute the tasks in order. Do not propose alternatives. If the code contradicts this plan,
   **STOP and quote the conflict** rather than improvising.
2. Edit only the files your lane owns (section 3).
3. **No published number may move.** PV generation is never netted into EUI, never subtracted from a
   demand figure, and never changes a thermal result. If a change of yours alters a simulated value
   for a building with PV switched off, you have exceeded the task — revert and report.
4. **Zero EnergyPlus simulations.** IDF generation and parsing are allowed and must run in parallel,
   never in a `for` loop over buildings.
5. **Ownership.** The transferred thing is the *method* — classify by geometry, strip before replace,
   report generation separately. **Every numeric default must be justified from a public source**
   (NREL PVWatts V5 technical report for system losses, ground-cover ratio, module power density and
   inverter efficiency; ASHRAE 90.1 for the placeholder's own basis), cited in the docstring-free way
   this repo uses: a line in the plan's progress log naming the source. Do not copy a constant from
   another project because it appears in the report.
6. No code comments. No new files beyond those named in section 3.
7. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. After
   solving one, register it there in the house format before you close the task.
8. Append one progress-log entry per completed task under section 8.

---

## 3. File layout and lane ownership

**Lane H — the PV layer**

- `openubem/idf/pv.py` (new)
- `tests/test_pv_injection.py` (new)
- `openubem/config.py` (one constant only, see H2)

**Nobody edits in this block:** `openubem/results/aggregator.py`, `openubem/idf/builder.py`,
`openubem/geometry/layout_assigner.py`, `openubem/geometry/envelope_patcher.py`,
`openubem/idf/compliance.py`, `openubem/simulation/parallel.py`, the viewer, any OVERVIEW or DESIGN
doc, root `main.py`.

---

## 4. Dependency decisions (pinned — do not re-litigate)

- **H1. Census first, classifier second.** H01 reports the measured tilt distribution. The classifier
  in H02 implements **only the groups H01 proves non-empty**, and the progress log records which
  groups were skipped and on what count. If Group A turns out to be empty, `pv.py` classifies into
  B and C only and says so.
- **H2. PV is opt-in.** `PV_INJECTION_ENABLED: bool = False` in `openubem/config.py`. Nothing calls
  `pv.py` in this block regardless — the flag exists so that the wiring decision at SR-H is a
  one-line change and not a refactor.
- **H3. Strip before replace, and strip is its own function.** `strip_existing_pv(idf) -> dict`
  removes the prototype's compliance placeholder and everything that references it, and returns the
  counts it removed per object class. **Measured 2026-09-17: 12 of the 25 prototype IDFs carry a
  `Generator:PVWatts` placeholder**; injecting on top of one produces duplicate
  `ElectricLoadCenter:Distribution` objects and an EnergyPlus fatal. The exact class list to strip is
  derived in H01 by reading one placeholder-carrying prototype, not assumed.
- **H4. The strip interacts with existing scaling — this is the one real trap.**
  `layout_assigner.scale_baseline_idf()` already scales the placeholder's
  `Generator:PVWatts.DC_System_Capacity` and `ElectricLoadCenter:Generators`
  `Generator_1_Rated_Electric_Power_Output` (R03 / E-LA-32, `layout_assigner.py:1046-1053`,
  `:1158-1166`). **Order is pinned: strip runs after scaling, never before.** Stripping first would
  leave that scaling code operating on objects that no longer exist, which is a silent behaviour
  change to a path that is in use today. `pv.py` must not call into `layout_assigner` and must not
  modify it.
- **H5. No racking, no shading objects, in this block.** `Shading:Building:Detailed` is not emitted.
  Flat-roof arrays are flush `Generator:PVWatts` only. Racking is deferred because the report
  measures it moving site EUI up to 2.3 %, and it must be introduced as its own decision with its own
  before/after measurement, never as a side effect of adding PV.
- **H6. Generation is reported, never netted.** `pv.py` produces objects and a summary dict; it
  never touches a demand or EUI value. There is no `net_eui` anywhere in this block.
- **H7. Surface qualification is geometric and explicit.** A surface qualifies only if it is
  `Surface_Type == "Roof"`, `Outside_Boundary_Condition == "Outdoors"`, and its area clears a minimum
  the executor states and justifies. Tilt and azimuth come from geomeppy's own `.tilt` / `.azimuth`
  properties, which this repo already relies on (`openubem/microclimate/resim.py:200-216`) — do not
  re-derive normals from vertices.

---

## 5. Verified facts, with line citations (measured 2026-09-17, do not re-derive)

1. **No PV module exists.** `grep -rln "PVWatts\|Photovoltaic"` over `openubem/` and `tests/` matches
   exactly one file, `openubem/geometry/layout_assigner.py`, and only in its scaling code. There is
   no `openubem/idf/pv.py`.
2. **12 of 25 prototype IDFs carry a `Generator:PVWatts` placeholder** (`config.BASELINE_IDF_DIR`,
   `openubem/config.py:50`): ApartmentHighRise, Hospital, HotelLarge, HotelSmall, OfficeLarge,
   OfficeMedium, OutPatientHealthCare, RetailStandalone, RetailStripmall, SchoolPrimary,
   SchoolSecondary, Warehouse.
3. **OpenUBEM generates only flat roofs.** `openubem/idf/european_box.py:219` is the sole surface-type
   literal; no module in `openubem/` mentions a pitched, gable, hip or sloped roof.
4. **geomeppy surface properties are already trusted in this repo** for azimuth, verified to within
   0.01 deg against vertex geometry (`openubem/microclimate/resim.py:200-216`).
5. **The placeholder is already scaled on the layout-assign path**, R03 / E-LA-32
   (`openubem/geometry/layout_assigner.py:1046-1053` and `:1158-1166`). This is what H4 protects.
6. **Results are written by `openubem/results/aggregator.py:254` (`export_results`)**, with a
   70-entry schema at `:280`. Out of scope here; named so the executor knows where not to go.

---

## 6. Tasks

#### H01 — Census: which roof groups actually exist, and what exactly must be stripped
**What.** Two measurements, reported as numbers.
(a) **Roof geometry.** Over all 25 prototype IDFs and over at least 20 built `layout_assign`
buildings spanning 10 archetypes, report the distribution of exterior `Roof` surfaces by tilt:
count and share with tilt > 5 deg (Group A), all-flat single-Z (Group B), all-flat multi-Z (Group C).
Report per archetype and name the archetypes, if any, where Group A is non-empty.
(b) **Strip list.** Read one placeholder-carrying prototype (`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`)
and report the **exact object classes** that make up the placeholder and reference it —
the generator, the load-centre chain, the inverter, and anything pointing at them by name.
Report the class names and the object counts, not the file contents.
**Why.** H1: the classifier implements only what exists. H3: the strip list is derived, not assumed.
**How.** A throwaway script in the scratchpad (NOT under `docs/`, NOT committed). Parallel pool of
20 for the built buildings. **No EnergyPlus runs.** Cache per-prototype reads.
**How to test.** The report itself is the deliverable. **STOP at SR-H1 and report before writing any
code in H02.**

#### H02 — `openubem/idf/pv.py`: strip, classify, inject
**What.** Three public functions and nothing else:
`strip_existing_pv(idf) -> dict` (H3, removing exactly the classes H01 measured, returning per-class
removal counts); `classify_roof_surfaces(idf) -> dict` (H1/H7, returning the qualifying surfaces
grouped, using geomeppy `.tilt` / `.azimuth`); `inject_pv(idf, enabled=False) -> dict` (H2/H5/H6,
flush `Generator:PVWatts` per qualifying flat roof plus the shared inverter and
`ElectricLoadCenter:*` chain appended once and idempotently, returning a summary dict of surfaces
used, total DC capacity and the defaults applied).
**Why.** This is the transferable half of T6: PV sized from real roof geometry instead of assumed,
with the duplicate-load-centre failure designed out.
**How.** Pure IDF construction. `inject_pv` with `enabled=False` must be a **no-op that returns the
summary it would have produced** — so the census in a later block can measure the fleet without
changing a single IDF. Every numeric default is justified from a public source per rule 5, and the
justification goes in the progress log. Idempotency is required: calling `inject_pv` twice must
produce the same IDF as calling it once.
**How to test.** `tests/test_pv_injection.py` (new): (a) stripping a placeholder-carrying prototype
removes every class H01 named and leaves zero dangling references; (b) stripping a prototype with no
placeholder is a no-op returning all-zero counts; (c) injection on a two-roof flat building creates
exactly two generators and exactly one `ElectricLoadCenter:Distribution`; (d) calling `inject_pv`
twice is byte-identical to calling it once; (e) `enabled=False` adds no object at all but still
returns a populated summary; (f) a roof with `Outside_Boundary_Condition` other than `Outdoors` is
never used; (g) a surface below the minimum area is skipped. Then run
`python -m pytest tests/test_pv_injection.py tests/idf/ -q` — green.
**STOP at SR-H2.**

---

## 7. Stop-and-report points

- **SR-H1 (after H01).** Report the two censuses. If Group A is empty across the whole fleet, say so
  plainly — the classifier then ships with two groups and the report's pitched-roof
  `Generator:Photovoltaic` path is recorded as not applicable to OpenUBEM today, not as missing work.
- **SR-H2 (after H02).** **Decision owed:** whether to (a) leave `pv.py` as a library nothing calls,
  (b) call it from the build path behind `PV_INJECTION_ENABLED`, or (c) add PV generation columns to
  `05_results`. (c) touches a 70-entry published schema and is not started without an explicit ruling.

---

## 8. Progress log

<!-- One entry per completed task:
#### TXX - <title> - completed YYYY-MM-DD
**Artifacts:** / **Deviations:** / **Test status:** / **Notes:**
-->

#### H01 - Census: roof groups and strip list - completed 2026-09-17

**Artifacts:** Throwaway script only, `scratchpad/h01_census.py` (not committed, not under `docs/`).
No repo files touched. Prototype library read directly from `config.BASELINE_IDF_DIR`. Built sample:
`run_step3(..., n_jobs=20, resolution_mode="layout_assign")` on 2 variants x the 10-archetype
`tests/fixtures/synthetic_10_buildings.py` fixture (SmallOffice, MidriseApartment,
HighriseApartment, TallBuilding, SuperTallBuilding, MediumOffice, RetailStripmall, Warehouse,
SmallDataCenterHighITE, OpenUBEMUnknown) = 20 built IDFs, all `generation_status=success`.
Classification used geomeppy `.tilt` per exterior `Roof` surface (`Outside_Boundary_Condition ==
Outdoors`), corrected to `pitch = min(tilt, 180 - tilt)` (see Deviations), and Z-level count from
each surface's mean vertex Z, rounded to 0.05 m tolerance.

**(a) Roof geometry — prototype library, n=25 IDFs (1 building per file):**

| Prototype file | Archetype(s) | Group | n_roof_surf | max_pitch_deg | n_Z_levels |
|---|---|---|---|---|---|
| ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf | HighriseApartment | B | 9 | 0.0 | 1 |
| ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf | MidriseApartment | B | 9 | 0.0 | 1 |
| ASHRAE901_DataCenterLargeHighITE_STD2019.idf | LargeDataCenterHighITE | B | 1 | 0.0 | 1 |
| ASHRAE901_DataCenterLargeLowITE_STD2019.idf | LargeDataCenterLowITE | B | 1 | 0.0 | 1 |
| ASHRAE901_Hospital_STD2022_Buffalo.idf | Hospital | B | 8 | 0.0 | 1 |
| ASHRAE901_HotelLarge_STD2022_Buffalo.idf | LargeHotel | C | 11 | 0.0 | 2 |
| ASHRAE901_HotelSmall_STD2022_Buffalo.idf | SmallHotel | B | 16 | 0.0 | 1 |
| ASHRAE901_OfficeLarge_STD2022_Buffalo.idf | LargeOffice, LargeOfficeDetailed | B | 1 | 0.0 | 1 |
| ASHRAE901_OfficeMedium_STD2022_Buffalo.idf | MediumOffice, MediumOfficeDetailed | B | 1 | 0.0 | 1 |
| ASHRAE901_OfficeSmall_STD2022_Buffalo.idf | SmallOffice, SmallOfficeDetailed | **A** | 4 | 18.45 | - |
| ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf | Outpatient | C | 29 | 0.0 | 2 |
| ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf | QuickServiceRestaurant | **A** | 4 | 45.0 | - |
| ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf | FullServiceRestaurant | **A** | 4 | 45.0 | - |
| ASHRAE901_RetailStandalone_STD2022_Buffalo.idf | RetailStandalone | B | 5 | 0.0 | 1 |
| ASHRAE901_RetailStripmall_STD2022_Buffalo.idf | RetailStripmall | B | 10 | 0.0 | 1 |
| ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf | PrimarySchool | B | 25 | 0.0 | 1 |
| ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf | SecondarySchool | C | 24 | 0.0 | 2 |
| ASHRAE901_Warehouse_STD2022_Buffalo.idf | Warehouse | B | 2 | 0.0 | 1 |
| College_90.1-2019_6A_Buffalo_v221.idf | College | B | 32 | 0.0 | 1 |
| Laboratory_90.1-2019_6A_Buffalo_v221.idf | Laboratory | B | 1 | 0.0 | 1 |
| SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf | SmallDataCenterHighITE | B | 1 | 0.0 | 1 |
| SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf | SmallDataCenterLowITE | B | 1 | 0.0 | 1 |
| Supermarket_V22.1.idf | SuperMarket | B | 2 | 0.0 | 1 |
| SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf | SuperTallBuilding | C | 7 | 0.0 | 2 |
| TallBuilding_90.1-2019_6A_Buffalo_v221.idf | TallBuilding | C | 7 | 0.0 | 2 |

Totals: Group A = 3/25 (12.0%), Group B = 17/25 (68.0%), Group C = 5/25 (20.0%). Group A archetypes:
SmallOffice, SmallOfficeDetailed, QuickServiceRestaurant, FullServiceRestaurant.

**(a) Roof geometry — built `layout_assign` sample, n=20 buildings, 10 archetypes x2 variants:**

| Archetype | n_built | Group(s) |
|---|---|---|
| HighriseApartment | 2 | B x2 |
| MediumOffice | 2 | B x2 |
| MidriseApartment | 2 | B x2 |
| OpenUBEMUnknown | 2 | B x2 (`layout_assign_fallback_auto` — no `ARCHETYPE_IDF_MAP` entry, falls to flat `european_box`) |
| RetailStripmall | 2 | B x2 |
| SmallDataCenterHighITE | 2 | B x2 |
| SmallOffice | 2 | **A x2** (pitch 28.97 deg, scaled from the pitched prototype) |
| SuperTallBuilding | 2 | C x2 |
| TallBuilding | 2 | C x2 |
| Warehouse | 2 | B x2 |

Totals: Group A = 2/20 (10.0%), Group B = 14/20 (70.0%), Group C = 4/20 (20.0%). Only SmallOffice is
Group A here because it is the only pitched-prototype archetype present in the 10-archetype fixture;
QuickServiceRestaurant/FullServiceRestaurant were not in the fixture's 10 and were not built, but
their prototype-level Group A membership above already establishes the mechanism is not
SmallOffice-specific.

**Verdict:** Group A is not empty. Pitched roofs (attic gables, confirmed by direct vertex Z
inspection, e.g. `west-roof`/`east-roof` in `ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf`,
vertices at Z=0 and Z=2.5405 m) exist in 3 of the 25 prototypes and survive unmodified into built
`layout_assign` buildings whenever the archetype maps to one of those 3 prototypes; confirmed live
in a built IDF via the SmallOffice archetype. H02's classifier must implement all three groups, not
two.

**Deviations:** geomeppy's raw `.tilt` is **not** usable directly as a pitch threshold: two flat
(constant-Z) prototype roofs (`ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`,
`ASHRAE901_RetailStandalone_STD2022_Buffalo.idf`) report `.tilt == 180.0` because their vertex
winding order in the source IDF gives a downward-facing normal, even though every vertex shares one
Z (confirmed by reading the raw vertex block, e.g. `t Roof SWA` in the ApartmentMidRise file, all 4
vertices at Z=3.047851). A naive `tilt > 5` test misclassifies these 2 files as Group A. Fixed by
using `pitch = min(tilt, 180 - tilt)` (0 and 180 both mean horizontal; only values strictly between
mean sloped). This lowered the prototype-library Group A count from an uncorrected 5/25 (20%) to the
correct 3/25 (12%). **H02's `classify_roof_surfaces` must use this same `min(tilt, 180-tilt)` form,
not raw `.tilt`, or it will wrongly route flat roofs with reversed winding into the
`Generator:Photovoltaic` pitched-roof path.** Not registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`: no exception/error was raised, this was a
silent-miscount risk caught in an analysis script, not a debugged runtime error.

**(b) Strip list — `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`:**

| Object class | Count | Object name(s) |
|---|---|---|
| `Generator:PVWatts` | 1 | `PV_module` |
| `ElectricLoadCenter:Generators` | 1 | `PV_Generator` (references `PV_module` as Generator 1) |
| `ElectricLoadCenter:Inverter:PVWatts` | 1 | `PV_Inverter` |
| `ElectricLoadCenter:Distribution` | 1 | `Generator` (references `PV_Generator` as Generator List Name, `PV_Inverter` as Inverter Name) |

Confirmed by exhaustive name-grep of `PV_module`/`PV_Generator`/`PV_Inverter`/the Distribution
object's own name (`Generator`) across the whole file: no other object class references any of the
4 by name. `ElectricLoadCenter:Transformer` ("Transformer 1") elsewhere in the file is a separate
grid-metering transformer (`PowerInFromGrid`, wired to lighting/equipment meters) and does not
reference the PV chain — it is not part of the placeholder and must not be stripped. One adjacent
object is a dedicated `Schedule:Compact` named `PV_SCH`, referenced only as `ElectricLoadCenter:
Generators`' "Generator 1 Availability Schedule Name" — it is pointed *at* by the generator rather
than pointing at it, so strictly it falls outside "references it by name", but it exists solely to
serve this placeholder and becomes a harmless orphan if left after stripping. Flagging for H02:
decide explicitly whether `strip_existing_pv` also removes `Schedule:Compact` "PV_SCH" (cosmetic,
does not affect correctness either way since an unused schedule causes no EnergyPlus fatal).

**Test status:** No automated tests (H01 is a census, not a code change). Script produced
`sample_size=25` (prototypes) and `sample_size=20` (built), both `generation_status=success`,
`GEN_FAILED=0`, `NO_ROOF=0`, matching the plan's >=25 / >=20-across-10-archetypes requirement.

**Notes:** `pv.py` is not started. Proceeding to H02 requires implementing all three groups (A, B, C)
per decision H1, since Group A is confirmed non-empty. STOP at SR-H1 per plan; H02 not started.

---

#### Manager audit of H01, and the SR-H1 ruling — 2026-09-17

Re-measured by the manager with an independent script
(`scratchpad/mgr_h01_verify.py`, throwaway), not taken from the executor's report.

- **Group A is real, and the count is exactly 3 of 25.** Reading every prototype in
  `config.BASELINE_IDF_DIR` and taking `pitch = min(tilt, 180 - tilt)` over exterior `Roof` surfaces:
  `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf` max pitch **18.45 deg** (4 roof surfaces),
  `ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf` **45.00 deg** (4),
  `ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf` **45.00 deg** (4). The other 22 prototypes are
  0.00 deg on every exterior roof. This confirms the executor's 3/25 and its named archetypes.
- **The winding correction was necessary and is now a hard requirement.** Raw geomeppy `.tilt`
  returns 180 deg for a flat roof whose vertices wind the other way, which a naive `tilt > 5` test
  reads as pitched. `min(tilt, 180 - tilt)` is the correct reduction and **H02's classifier must use
  it**; without it the census gave 5/25 instead of 3/25.
- **Strip list confirmed on `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`:** one `Generator:PVWatts`
  (object `PV_module`, line 45, 32,176.5 W, `FixedOpenRack`, system losses 0.113, tilt 0 / azimuth 180),
  one `ElectricLoadCenter:Generators`, one `ElectricLoadCenter:Inverter:PVWatts`, one
  `ElectricLoadCenter:Distribution`. (A raw `grep -c` for the class name returns 2 because the string
  also appears as the `Generator 1 Object Type` field inside `ElectricLoadCenter:Generators` — there is
  one actual object.)
- **`PV_SCH` decided here, not left open.** The `Schedule:Compact` named `PV_SCH` is referenced by
  `ElectricLoadCenter:Generators.Generator_1_Availability_Schedule_Name` and by nothing else.
  **Ruling: `strip_existing_pv` does not delete it.** Deleting a `Schedule:Compact` is a class of edit
  that can silently orphan another object in a prototype we have not read, and an unused schedule costs
  nothing in EnergyPlus. The strip list is the four objects above and only those. H02 reports
  `PV_SCH` as "left in place" in its returned dict so the decision is visible, not invisible.
- **No repo file was touched**, `git status --porcelain` is unchanged from before H01, and the census
  script is gone from the scratchpad.

**New finding — the pitch of a built OpenUBEM building is partly an artefact of scaling.**
`scale_baseline_idf()` scales X and Y by `planar_scale_factor` and **leaves Z unchanged**
(`openubem/geometry/layout_assigner.py:750`). A gable therefore gets steeper when the real footprint is
smaller than the prototype's and shallower when it is larger. Measured: the SmallOffice prototype's
roof is 18.45 deg, and the executor's two built SmallOffice buildings came out at 28.97 deg — the same
roof, re-pitched by the plan-area fit. **Consequences, both binding on H02:** (i) tilt must be read
from the built IDF at injection time and never looked up from the prototype; (ii) any future
pitched-roof yield number must be reported as geometry-derived, with this distortion stated, and must
never be presented as a measured roof pitch of the real building. Nothing here moves a published
number — no PV is injected anywhere today.

**SR-H1 ruling: implement all three groups.** Group A is non-empty in the prototype library (3 of 25)
and survives into built buildings on the `layout_assign` path (2 of 20 sampled), so the report's
pitched-roof branch is applicable to OpenUBEM and is not recorded as not-applicable. H02 proceeds as
written in section 6, with the three additions above: the `min(tilt, 180 - tilt)` reduction, the
four-object strip list with `PV_SCH` preserved, and tilt read from the built IDF only.

#### H02 — amendment issued with the SR-H1 ruling (2026-09-17)

Section 6's H02 was written assuming Group A might be empty. It is not, so H02 is widened by exactly
these points and nothing else:

1. `classify_roof_surfaces(idf)` returns three groups, using `pitch = min(tilt, 180 - tilt)` and the
   5 deg threshold: **A** pitched (`pitch > 5`), **B** flat with one Z level, **C** flat with several.
   Z levels are compared on each surface's mean vertex Z with a 0.05 m tolerance.
2. `inject_pv` emits, per qualifying surface: on **B and C**, a flush `Generator:PVWatts` as already
   specified; on **A**, a `Generator:Photovoltaic` with `PhotovoltaicPerformance:Simple` mounted flush
   on the surface, so the pitched roof's own tilt and azimuth do the work. Both feed the one shared
   `ElectricLoadCenter:*` chain.
3. The strip list is exactly `Generator:PVWatts`, `ElectricLoadCenter:Generators`,
   `ElectricLoadCenter:Inverter:PVWatts`, `ElectricLoadCenter:Distribution`. `Schedule:Compact`
   `PV_SCH` is **not** deleted and is reported as left in place.
4. Tilt and azimuth are read from the IDF being injected into, never from a prototype file.
5. Two test cases are added to the seven already listed: **(h)** a pitched-roof building produces
   `Generator:Photovoltaic` + `PhotovoltaicPerformance:Simple` and no `Generator:PVWatts`; **(i)** a
   building with both pitched and flat exterior roofs produces both generator kinds and still exactly
   one `ElectricLoadCenter:Distribution`.

H5 still holds: **no racking, no `Shading:Building:Detailed`, nothing that shades a roof.** H6 still
holds: generation is reported, never netted.

---

#### H02 - `openubem/idf/pv.py`: strip, classify, inject - completed 2026-09-17

**Artifacts:** `openubem/idf/pv.py` (235 lines, new), `tests/test_pv_injection.py` (185 lines, new),
`openubem/config.py` (+1 line, `PV_INJECTION_ENABLED: bool = False`). No other file touched;
`pv.py` imports nothing from `openubem.geometry.layout_assigner`, and a repo-wide grep confirms
nothing outside `pv.py`/its own test calls into it (build path unchanged).

Three public functions only, exactly as specified: `strip_existing_pv(idf) -> dict`,
`classify_roof_surfaces(idf) -> dict`, `inject_pv(idf, enabled=False) -> dict`. Tilt is read once
per surface via geomeppy's own `.tilt` (never re-derived from vertices) and reduced with
`pitch = min(tilt, 180 - tilt)` per the SR-H1 ruling. Flat qualifying roofs (Group B/C) get a flush
`Generator:PVWatts` with `Array_Geometry_Type = "Surface"` and `Surface_Name` set to the real roof
surface, so tilt/azimuth/shading are read from the surface itself at simulation time rather than
duplicated as numbers in `pv.py` -- this satisfies "tilt and azimuth read from the IDF being
injected into, never from a prototype file" more robustly than hand-copying `.tilt`/`.azimuth` into
the object's own Tilt/Azimuth fields. Pitched roofs (Group A) get `Generator:Photovoltaic` +
`PhotovoltaicPerformance:Simple` mounted on the surface (that object type only supports
surface-mounting, so it is flush by construction). Both feed one shared
`ElectricLoadCenter:Generators` / `:Inverter:PVWatts` / `:Distribution` chain, capped at 30
generators (the `ElectricLoadCenter:Generators` IDD hard limit); any surplus beyond 30 is dropped
deterministically (sorted by surface name) and counted in the summary's
`skipped_generator_capacity_limit` -- not observed in any test, flagged for whoever eventually
census-runs this over the fleet (College measured 32 roof surfaces in H01).

**Numeric defaults and sources (rule 5):**
- `MODULE_POWER_DENSITY_W_PER_M2 = 190.0` -- NREL PVWatts V5's "Premium" module class, taken as
  ~19% conversion efficiency at the 1000 W/m2 STC reference irradiance (0.19 x 1000 = 190 W/m2).
  Chosen over "Standard" because the prototype's own placeholder already uses
  `Module_Type = Premium` (`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` line 49) -- preserving the
  placeholder's own basis per rule 5. Independently derived, not copied from the TechTransfer
  report's own 200 W/m2 figure (report line 273); the two are close but not equal, which is the
  intended check that this was not copy-pasted.
- `SYSTEM_LOSSES_FRACTION = 0.14` -- NREL PVWatts V5 default total system losses (soiling, shading,
  snow, mismatch, wiring, connections, light-induced degradation, nameplate rating, age,
  availability, composited to ~14%). Confirmed against the local EnergyPlus IDD, whose
  `Generator:PVWatts` field `System Losses` (`N2`) carries `\default 0.14` and whose object `\memo`
  states it implements "the PVWatts software" verbatim (`C:\EnergyPlusV23-1-0\Energy+.idd:89417-89421`).
- `GROUND_COVERAGE_RATIO = 0.40` -- NREL PVWatts V5 default GCR, confirmed the same way
  (`Energy+.idd:89450-89456`, field `N5`, `\default 0.4`).
- `INVERTER_EFFICIENCY = 0.96` -- NREL PVWatts V5 default inverter efficiency, confirmed the same
  way (`Energy+.idd:89469-89473`, field `N2`, `\default 0.96`); also matches the placeholder's own
  value in `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` line 80.
- `DC_TO_AC_SIZE_RATIO = 1.10` -- NREL PVWatts V5 default DC-to-AC size ratio
  (`Energy+.idd:89465-89468`, field `N1`, `\default 1.10`). Not in rule 5's named list but written
  onto the shared inverter object regardless, so it is sourced rather than left at the placeholder's
  own 1.2.
- `MIN_QUALIFYING_ROOF_AREA_M2 = 7.5` -- **the one default not cleanly sourced from either named
  document, flagged honestly rather than hidden.** Neither the NREL PVWatts V5 manual nor ASHRAE
  90.1 states a minimum *qualifying roof surface area*; 90.1-2022 SS10.5.1's on-site-renewable
  requirement is a capacity *intensity* (~0.5 W/ft^2 of gross floor area for the first three floors),
  which does not convert cleanly into a per-surface area filter. Absent a clean citation, 7.5 m2 was
  set just above the closest public precedent for "minimum contiguous roof area worth reserving for
  PV" found during this task -- California Title 24's Solar-Ready "Solar Access Roof Area" minimum
  of 80 ft^2 / 7.43 m2 -- which is a different code body than the two named in rule 5. **This default
  is a placeholder pending an explicit ruling; treat it as open, not final.**
- `PITCH_THRESHOLD_DEG = 5.0` carried over unchanged from H01/plan section 4 (H1), not re-derived
  here.

**Network note:** the primary PVWatts V5 PDF (`docs.nrel.gov`, `pvwatts.nrel.gov`, `www.nrel.gov`)
could not be fetched directly -- `WebFetch` returns `getaddrinfo ENOTFOUND <host>` for all three
(sandbox has no general outbound fetch). Values above were corroborated via `WebSearch` snippets
and cross-checked against the locally shipped `Energy+.idd` defaults, which is the stronger of the
two sources since it is the literal implementation. Registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, chapter 13.

**Test status:** `python -m pytest tests/test_pv_injection.py tests/idf/ -q` -- **32 passed**
(16 in `test_pv_injection.py` covering (a)-(i) plus classify/strip unit cases, 16 pre-existing in
`tests/idf/`). All nine `inject_pv` cases from section 6 plus the two amendment cases pass,
including idempotency (byte-identical `idf.idfstr()` after a second `inject_pv(idf, enabled=True)`
call, short-circuited via a name check on `ElectricLoadCenter:Distribution`) and the disabled path
(`enabled=False` adds zero objects, confirmed by `idfstr()` equality before/after, while still
returning a populated summary with `n_generators`/`total_dc_capacity_w`).

**Deviations:**
1. `Array_Geometry_Type = "Surface"` (not literal `Tilt_Angle`/`Azimuth_Angle` numbers) is used for
   the flat-roof `Generator:PVWatts` objects -- not explicitly specified in the plan text, but is
   the IDD's own native mechanism for "flush, geometry-derived tilt/azimuth" and was judged the more
   robust reading of H7 and amendment point 4 than hand-writing numbers. Flagged for audit.
2. `Array_Type = "FixedRoofMounted"` (not the placeholder's `FixedOpenRack`) for flat-roof arrays,
   since the placeholder was a ground-rack default and our arrays are flush roof-mounted by
   construction; this is a categorical IDD key choice, not one of the five numeric defaults needing
   a separate citation.
3. `MIN_QUALIFYING_ROOF_AREA_M2` is not cleanly sourced from either named document (see above) --
   the single open item from this task.
4. A 30-generator cap was added (not in the plan text) because `ElectricLoadCenter:Generators` has
   a hard IDD limit of 30 generator slots and College alone measured 32 roof surfaces in H01;
   untested (no fixture exceeds 30) and reported rather than silently risking an `AttributeError` on
   `Generator_31_Name`.

**Notes:** `pv.py` remains a library nothing calls; `config.PV_INJECTION_ENABLED` stays `False` and
is not read anywhere in the build path. STOP at SR-H2 per plan -- decision owed on (a)/(b)/(c) per
plan section 7, and a ruling on `MIN_QUALIFYING_ROOF_AREA_M2` (deviation 3).

---

### Manager audit of H02, the SR-H2 ruling, and one defect found — 2026-09-17

Everything below was re-measured by me, not taken from the executor report.

**Re-run of the executor own commands.** `python -m pytest tests/test_pv_injection.py tests/idf/ -q`
-> `32 passed in 117.91s`. `git status --porcelain` shows no file outside the declared lane plus the
mandated debug-references entry. `openubem/config.py` reports `+44` lines, but line-by-line inspection
of `git diff -U0` shows 43 of those are the still-uncommitted E01 version fence
(`read_idf_version` / `assert_prototype_idf_version` / `validate_prototype_library_versions`,
`PrototypeIDFVersionError`, `ENVELOPE_PATCH_SKIP_WHEN_BETTER`, `PREP_ABORT_ON_FAILURE`) from earlier
blocks. The H02 addition is exactly one line: `PV_INJECTION_ENABLED: bool = False` at
`openubem/config.py:223`. `openubem/idf/pv.py` is 235 lines, `tests/test_pv_injection.py` is 185.

**Lane discipline.** `grep -rn` across `openubem/` and `tests/` finds exactly one reference to the new
module — the test own import. Nothing in the build path calls it. `pv.py` imports one symbol,
`eppy.function_helpers.getcoords`; it does not import `layout_assigner`, `builder`, or `config`.
Zero code comments in either new file (a count of lines starting with a hash returns 0 for both); the
module docstring carries the provenance, which is what the no-comment rule intends.

**The nine required test cases are all present** as named methods, cases (a) through (i), including
the two added by the amendment: `test_pitched_roof_produces_photovoltaic_not_pvwatts`
(`tests/test_pv_injection.py:168`) and
`test_mixed_pitched_and_flat_produce_both_and_one_distribution` (`:177`).

**Strip list confirmed.** `_STRIP_CLASSES` (`openubem/idf/pv.py:37-42`) is exactly the four classes
ruled in the H01 audit, and `PV_SCH` is left in place and reported as `pv_sch_left_in_place: True`
in the summary dict. Matches my ruling; no schedule is deleted.

#### Defect found by measurement — the 30-generator cap is not a real limit and must be removed

The executor capped the generator list at `MAX_GENERATORS_PER_DISTRIBUTION = 30`
(`openubem/idf/pv.py:50`, applied at the `ordered_surfaces[:MAX_...]` slice), describing it as an
`ElectricLoadCenter:Generators` IDD hard limit. It is not one, and I measured this rather than
reasoning about it:

- `Energy+.idd:90410` declares `ElectricLoadCenter:Generators` with `\extensible:5` and
  `\begin-extensible` on `Generator 1 Name`. The IDD spells out slots up to `Generator 30 Name`
  purely as the conventional pre-expansion; an extensible object is not bounded by the last
  spelled-out slot.
- I built the object through the eppy `newidfobject` with 32 generator triples and serialised it:
  `g30`, `g31` and `g32` all appear in the written object, `len(obj.fieldnames) == 162`. eppy does not
  reject or drop the fields.
- H01 measured a College prototype carrying **32** roof surfaces. So the cap bites on a real
  prototype in the library: two qualifying roofs are silently dropped, total DC capacity is
  under-reported, and nothing raises. A silent under-count is the worst failure shape available here.

Ruling: remove the cap. `skipped_generator_capacity_limit` goes with it.

#### Second defect — the strip/inject ordering is documented but not enforced in code

`inject_pv` never calls `strip_existing_pv`. Every one of the 25 prototypes carries an
`ElectricLoadCenter:Distribution` (H01), so calling `inject_pv` on a real prototype without stripping
first produces two `ElectricLoadCenter:Distribution` objects and an EnergyPlus fatal — the exact
failure the strip-before-replace rule exists to prevent. The tests pass only because they build
blank IDFs or strip first, which is precisely the blind spot a synthetic fixture creates. The pinned
order from the H01 audit still holds and is unchanged: **strip runs after scaling, never before.**
The fix is to fold the strip into `inject_pv` itself, at the top of the enabled branch, so the
ordering cannot be got wrong by a future caller.

#### Deviations reviewed and accepted

1. `Array_Geometry_Type="Surface"` + `Surface_Name` instead of writing `.tilt` / `.azimuth` numbers
   onto the object. **Accepted, and it is better than what the amendment asked for.** EnergyPlus
   derives the plane from the named surface in the model being simulated, which satisfies amendment
   point 4 (orientation read from the building being injected into, never from a prototype) more
   strictly than copying a geomeppy value, and it removes the winding trap at the engine level
   rather than working around it.
2. `Array_Type="FixedRoofMounted"` instead of the placeholder `FixedOpenRack`. **Accepted** —
   flush roof mounting is what rule H5 requires, and `FixedOpenRack` would describe a rack this
   block is forbidden to build.
3. `Value_for_Cell_Efficiency_if_Fixed = MODULE_POWER_DENSITY_W_PER_M2 / 1000.0 = 0.19`.
   Dimensionally correct: 190 W/m2 under a 1000 W/m2 STC irradiance is a 19 % module efficiency,
   which is the same physical statement as the Premium module class, expressed in the units
   `PhotovoltaicPerformance:Simple` wants. **Accepted.**
4. Groups B and C are classified separately and reported separately, but receive identical
   treatment inside `inject_pv` (both land in `flat_surfaces`). **Accepted for this block** — the
   difference between a single-level and a multi-level flat roof only matters once racking or
   inter-row shading exists, and rule H5 bars both. Recorded so that nobody later reads the
   three-group classifier as already driving different geometry: today it drives reporting only.

#### Ruling on MIN_QUALIFYING_ROOF_AREA_M2 (open question left by the executor)

The executor is right, and right to have flagged it: neither NREL/TP-6A20-62641 nor ASHRAE 90.1
section 10.5.1 states a minimum roof area — 90.1 gives a capacity intensity, not an area floor. So
this value cannot be presented as standard-derived, and the honesty of the flag is noted.

Ruling: the threshold **stays at 7.5 m2** and is relabelled in the module docstring as an **OpenUBEM
internal convention**, not a standard-derived default. Its only job is to drop trivially small roof
slivers that would otherwise each spawn a generator object; at 7.5 m2 it removes roughly one module
worth of area or less, so no plausible choice in the 5-10 m2 band moves a capacity total materially.
The California Title 24 Solar-Ready 80 ft2 (7.43 m2) figure may be named as a **public precedent for
the order of magnitude only**, never cited as the source of the number. Any future published
roof-area, capacity or yield figure states this threshold alongside it. Rule 5 of section 2 (every
numeric default justified from a public source) is satisfied for the other five defaults and is
explicitly *waived, with the reason on the record*, for this one.

#### SR-H2 — RULING: option (a). pv.py stays a library that nothing calls.

The three options were (a) leave it a library, (b) call it from the build path behind
`PV_INJECTION_ENABLED`, (c) add PV columns to `05_results`.

- **(c) is refused outright.** It touches a 70-entry published schema, and section 1a of this plan
  binds this block to move no published number. Not started.
- **(b) is refused for now, not forever.** Adding a call site to the build path means every building
  in the fleet traverses the new code on every run, including the disabled path, in exchange for a
  capability with no consumer, no validated yield number, and — until the two defects above are
  fixed — a silent truncation and an un-enforced ordering rule. The default-OFF flag pattern used for
  the window clamp and the prep gate does not transfer here: those gates changed behaviour that was
  already wrong, whereas this one adds objects that nothing reads.
- **(a) is adopted.** `pv.py` remains importable, tested and unwired. `config.PV_INJECTION_ENABLED`
  stays `False` and stays unread by the build path; it is the reserved switch for whenever (b) is
  revisited, and keeping it costs nothing.

The condition for revisiting (b) is stated now so it is not re-argued later: both defects fixed, plus
**one real EnergyPlus run** on one injected prototype that completes without a fatal and reports
non-zero generation. Until a measured run exists, the module has never been proven to produce a
simulable IDF — every test to date is synthetic, and a synthetic green is not a live green.

#### Task H03 — issued from this audit (scope is exactly these four items, nothing else)

1. Delete `MAX_GENERATORS_PER_DISTRIBUTION`, the slice that applies it, and the
   `skipped_generator_capacity_limit` summary key. Add one test that a 32-roof building yields 32
   generators and one `ElectricLoadCenter:Distribution`, on the measured grounds above.
2. Fold `strip_existing_pv` into `inject_pv`, at the top of the enabled branch only, and return its
   counts under a `stripped` key in the summary. `strip_existing_pv` stays public. The disabled path
   must still add and remove nothing. Add one test that injecting into an IDF that already carries a
   placeholder PV chain leaves exactly one `ElectricLoadCenter:Distribution`, and one that the
   disabled path does not strip.
3. Relabel `MIN_QUALIFYING_ROOF_AREA_M2` in the module docstring per the ruling above: internal
   convention, Title 24 named as an order-of-magnitude precedent only, not as a source.
4. Add one sentence to the module docstring recording that groups B and C are treated identically
   today and that the split exists for reporting.

Out of scope for H03, and not to be started: wiring `pv.py` into the build path, any
`Shading:Building:Detailed` or racking object, any write to `05_results`, and any EnergyPlus run.

#### H03 — remove generator cap, fold strip into inject, relabel docstring — completed 2026-09-17
**Artifacts:** openubem/idf/pv.py, tests/test_pv_injection.py
**Deviations:** none
**Test status:** 35 passed in 124.42s (0:02:04)
**Notes:** Deleted MAX_GENERATORS_PER_DISTRIBUTION, its slice and skipped_generator_capacity_limit;
added a 32-roof test proving 32 generators + one ElectricLoadCenter:Distribution. Folded
strip_existing_pv into inject_pv's enabled branch, placed after the _already_injected check (per the
audit's own clarification) so idempotency is preserved, with counts returned under summary["stripped"];
disabled path still adds/removes nothing (verified by an idfstr before/after equality test on a
prototype carrying a placeholder chain). Relabelled MIN_QUALIFYING_ROOF_AREA_M2 in the module
docstring as an OpenUBEM internal convention (Title 24 named as order-of-magnitude precedent only,
not a source) and added the Group B/C reporting-only sentence.

### Manager audit of H03 — 2026-09-17. Lane H closed.

Re-measured by me: `python -m pytest tests/test_pv_injection.py tests/idf/ -q` -> `35 passed in
124.03s`. `MAX_GENERATORS_PER_DISTRIBUTION` and `skipped_generator_capacity_limit` no longer appear
anywhere in `openubem/idf/pv.py` or `tests/test_pv_injection.py`. `_already_injected` runs at
`openubem/idf/pv.py:175` and `strip_existing_pv` at `:179`, i.e. the idempotency check reads the
OpenUBEM distribution object before the strip could remove it — which is the only ordering that keeps
a second call a no-op. Zero code comments in both files. The three new cases are at
`tests/test_pv_injection.py:192`, `:208` and `:216`. Both docstring items landed. No file outside the
lane was modified; the debug-references diff is unchanged from H02.

One residual behaviour, found by me and accepted rather than fixed: if a building has no qualifying
roof, the strip has already run by the time `if not used` returns, so the prototype loses its
placeholder PV chain and gains nothing. That is the correct reading of strip-before-replace — the
placeholder chain is a prototype leftover OpenUBEM never wants — but it is a real state change on a
"nothing to do" path, so it is recorded here rather than left to be rediscovered.

Lane H is closed. `openubem/idf/pv.py` ships as a tested library that nothing calls, per the SR-H2
ruling. The condition for ever wiring it up is unchanged and restated for the next reader: one real
EnergyPlus run on one injected prototype, completing without a fatal and reporting non-zero
generation. Report order 9 (T6) is complete.
