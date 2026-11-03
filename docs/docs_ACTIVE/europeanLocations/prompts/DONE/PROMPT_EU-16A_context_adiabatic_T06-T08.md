# `EU-16A` — Executor prompt: 20 m context shading, adiabatic party walls, local rebuild (T06–T08)

- **Arc**: European locations × Step 8. **Plan**: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- **Order**: **after stop-and-report 1 of `EU-15B` is answered.** The IDFs must carry the carved core before
  they are rebuilt, or the fleet is rebuilt twice.
- **Ruling implemented**: `D-EU-40` — every building is simulated with its 20 m context as shading, attached
  walls adiabatic. Rule doc: `rules/RULES_context_geometry_simulation_2026-08-30.md` (R1–R9).
- **Executor**: fresh Sonnet session. **Paste everything below the rule.**
- **Date of prompt**: 2026-08-30. 🔴 **Authorisation: local only. No `sbatch`, no Speed, no login-node command.**

---

## Task (paste from here)

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu15-eu16-zoning-context-2026-08-30.md`
and `docs/docs_ACTIVE/europeanLocations/rules/RULES_context_geometry_simulation_2026-08-30.md`.
Execute **T06, T07, T08** in order, then **stop at stop-and-report 2**. Do not submit anything to Speed.

You are working in `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** — never bare
`python`. Git is handled externally: **never commit, never stage**.

### Hard rules

1. **Execute the plan. Do not propose alternatives.** If a rule document is ambiguous, **STOP and quote the
   conflict** — never resolve it yourself.
2. 🔴 **No compute on Speed in this dispatch.** No `sbatch`, no `srun`, no `ssh … python`. T08 ends with a
   local census and a stop.
3. **Do not edit `openubem/config.py:34` (`SHADING_SPHERE_RADIUS = 30.0`)** — the European radius is a separate
   **20.0 m** constant. **Do not change the signature of `discover_context`.**
4. Touch only the files listed in plan §3. **No new files, reports, boards or helper scripts.**
5. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first**, and
   register any solved error there in the house format before closing the task.
6. Default to no code comments. No `.py` files under `docs/`.

### T06 — 20 m context shading in the European IDF path (`D-EU-40` R2–R5, R7, R8)

*What.* Replace `extrude_geometry(idf, zones, [])` at **`scripts/run_eu_s2_campaign.py:227`** with the real
context list. That empty list is the whole defect: **0 of 2,516** IDFs carry a `Shading:*` object.
*How.* Load `01_buildings_clean.gpkg` **once per district**; per target building, query the **20.0 m** buffer
against the spatial index; build shading volumes through `discover_context` (`openubem/geometry/context.py:6`)
with the European radius constant and the R4 height precedence — `height_m` → `levels × 3.0 m` → district
median residential height, **each fallback counted and reported**. Add a `ShadowCalculation` object and state
its settings explicitly. Shading blocks are added **after** `intersect_match` (`openubem/idf/surfaces.py:781`)
— that ordering is an invariant. Context is **geometry only**: no zone, no load, no result row.
*How to test.* `tests/idf/test_eu16_context_adiabatic.py` — a synthetic 5-building block emits exactly the
neighbours inside 20 m and none outside; **no context building appears as a `Zone`**; on **10 named real
buildings per district** the emitted shading count equals the spatial query exactly.

### T07 — adiabatic party walls for attached buildings (`D-EU-40` R6)

🔴 **This section was rewritten 2026-08-30 by ruling `D-EU-41`** after an executor correctly stopped on it.
The old text said "call `set_adiabatic_surfaces`, unchanged" — that was wrong and is withdrawn.

*What.* Flip walls shared with a neighbour within **0.30 m** to `Adiabatic` on the European path.
*Why.* 0 of 2,516 IDFs carry one, while **88.5 %–99.1 %** of buildings are attached to at least one neighbour.
*How.* **Do not use `set_adiabatic_surfaces`** — it is a documented no-op stub and its signature
`(idf, zones, strategy)` has no neighbour footprints, so it cannot express inter-building adjacency.
**Do not edit `openubem/idf/surfaces.py`**; the North-American path must stay byte-unchanged. Implement a
European-only pass in `scripts/run_eu_s2_campaign.py`, reusing the **same** neighbour rows and the **same**
coordinate transform `build_european_context` already uses — shading and the flip must never disagree about
where a neighbour is. Flip only `BUILDINGSURFACE:DETAILED` with `Surface_Type == Wall` **and**
`Outside_Boundary_Condition == outdoors`; never `ground`, never `surface` (inter-zone), never a
`Floor`/`Roof`/`Ceiling`. Ground-floor slabs at `z = 0` keep `Ground` (`surfaces.py:912`). Each flip sets
`Outside_Boundary_Condition = Adiabatic`, blanks `Outside_Boundary_Condition_Object`, and sets
`Sun_Exposure = NoSun`, `Wind_Exposure = NoWind` — anything less is an E+-invalid surface. Run it after
`intersect_match` and after the shading blocks, so R8 holds. Adjacency test: the wall's XY segment lies inside
the neighbour footprint buffered by 0.30 m — state the test you used, never tune the tolerance.
*How to test.* Extend `tests/idf/test_eu16_context_adiabatic.py`: two touching footprints flip exactly the
shared wall and nothing else; a detached building flips nothing; a flipped surface is E+-valid; zone count is
identical before and after. Then report, per district, IDFs carrying ≥ 1 `Adiabatic` surface against the
measured attachment census, **and** flipped exterior wall area as a fraction of total exterior wall area;
**0 zones gained or lost** by this task alone.

### T08 — rebuild all four districts' IDFs locally and census. THEN STOP.

*What.* Run `prepare()` for all four districts and report: zone-count deltas vs the current fleet, the
`IDF_ASSEMBLY_FAILED_*` residual, the shading and adiabatic censuses, and the array-size estimate for T09.
*Why.* `D-EU-35` stands — the viewer pop-up and the simulated IDF must never describe different geometry.
*How to test.* For a **20-building sample per district**, every side-car's zone-name set equals its IDF's zone
set. **No `sbatch`.**

### Report (🔴 stop-and-report 2 — stop here)

Append one progress-log entry per completed task to **§8 of the plan** and one row per task to
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`. Then report:

1. Shading census per district: IDFs carrying ≥ 1 `Shading:*`, and the mean/max neighbours per building.
2. Height-precedence census: how many buildings used `height_m`, `levels × 3.0`, district median.
3. Adiabatic census per district against the 88.5 %–99.1 % attachment measurement.
4. Zone-count delta vs the current fleet and the `IDF_ASSEMBLY_FAILED_*` residual.
5. The proposed array sizes per district. **Then stop — submission needs an explicit instruction.**
