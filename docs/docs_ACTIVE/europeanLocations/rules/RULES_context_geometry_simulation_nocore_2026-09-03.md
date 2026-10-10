> **No-core regime header.** `D-EU-79`, owner's decision 2026-09-02. Supersedes
> `RULES_context_geometry_simulation_2026-08-30.md` (core-era) and
> `RULES_context_geometry_simulation_nocore_2026-09-02.md` (no-core baseline), both now in
> `rules/archive/`. This document rules EnergyPlus context shading and adiabatic party walls, unrelated to
> the dwelling-layout cutter, and is republished unchanged except for this header and the citation fix in
> section 4 below, which now points at the `C11`-era dwelling-layout document (`D-EU-82` … `D-EU-87`).

---

# RULES — context geometry and simulation order (`D-EU-40`)

**Arc:** European locations × Step 8 · **Ruled:** 2026-08-30 by the owner · **Binds:** `EU-16`, and every
European district campaign after it.

**Method of record.** O. Koral Iseri et al., *Energy & Buildings* **337** (2025) 115620, §4.1.1, Fig. 4b–c
(`GSSCanada/.../Step8_docs/IMP_step8/resources/1-s2.0-S0378778825003500-main.pdf`, p. 9), quoted:

> "we constructed 3D volumes and performed **separate energy simulation steps for each building where the
> surrounding buildings within a radius of 20 m are taken into account** to account for shading and
> interactions with urban heat during the sequential energy simulations of the residential buildings"

> "The residential buildings were simulated at the zone level, while the remaining commercial and public
> buildings were **not simulated** during the UBEM process. **Attached buildings were modeled separately,
> with intersecting walls treated as adiabatic surfaces.**"

Grasshopper reference implementation: `IMP_step8/extracted_scripts/008_HB_EPContextSrf_idx1574.py`
(*Honeybee EP context Surfaces*).

---

## 1. The state this rule corrects

Measured 2026-08-30 over the four district campaigns on disk:

- **0 of 2,516** EU-11 IDFs carry any `Shading:Building*` / `Shading:Site*` / `Shading:Zone*` object.
- **0 of 2,516** carry an `Adiabatic` surface.
- Cause: `scripts/run_eu_s2_campaign.py:227` calls `extrude_geometry(idf, zones, [])` — the context list is
  hard-coded empty. `set_adiabatic_surfaces` (`openubem/idf/surfaces.py:909`) is never called on this path.
- Every simulated building is missing **11.1–12.2 neighbours on average** (max 28) within 20 m, and
  **88.5–99.1 %** of them are physically attached to at least one neighbour (`FINDING 208`).

The machinery already exists on the North-American path — `discover_context`
(`openubem/geometry/context.py:6`), `extrude_geometry(..., context)` (`openubem/idf/surfaces.py:774`),
`set_adiabatic_surfaces` — and is simply not wired into the European one.

---

## 2. The rule

### R1 — Simulation unit
Each **residential** building is one EnergyPlus run, simulated **individually**. Nothing is merged into a
district-wide model, and no result is transferred between buildings. Unchanged from today.

### R2 — Context radius: **20 m**
Context = every building in `01_buildings_clean.gpkg` whose footprint intersects the target footprint
buffered by **20.0 m**, excluding the target itself.

🔴 **This is 20 m, not `config.SHADING_SPHERE_RADIUS = 30.0`** (`openubem/config.py:34`, the North-American
DESIGN §3C value). The two constants disagree; the European path takes 20 m from the published method.
An executor must introduce a separate European constant and **must not** edit `SHADING_SPHERE_RADIUS`.

### R3 — Context is a superset of the simulated stock
Context includes buildings that are **never simulated**: non-residential, excluded-manifest, typology-gap
and `NOT_SIMULATED` buildings all shade. Source the layer that carries all of them
(`01_buildings_clean.gpkg`, 1,455–2,406 rows per district), never the residential manifest alone.

### R4 — Context geometry form
One shading volume per context building: its footprint (the minimum rotated rectangle is acceptable, per
`discover_context`) extruded to its height. Height precedence, fail-soft in this order:
`height_m` → `levels × 3.0 m` (the European floor-to-floor, **not** the 3.5 m in `context.py:39`) → the
district's median residential height. Every fallback used must be counted and reported.

### R5 — Context is geometry only
A context building emits **no** zone, no construction, no schedule, no load, and no result. It is a shading
surface. Its transmittance schedule is opaque (no `Shading:Property:Reflectance` override unless ruled).

### R6 — Attached buildings: adiabatic party walls
Where the target footprint touches a neighbouring footprint (buffer tolerance **0.30 m**), the shared wall
surfaces are set to `Adiabatic` — the neighbour is a separate simulation, not a heat sink. The neighbour is
**still emitted as context geometry** for shading. Use `set_adiabatic_surfaces`
(`openubem/idf/surfaces.py:909`), which already implements the inter-building flip.

> 🔴 **`R6` amendment — `D-EU-41`, ruled 2026-08-30 (manager).** The sentence above is **factually wrong and is
> withdrawn.** `set_adiabatic_surfaces` (`openubem/idf/surfaces.py:909`) is a documented **no-op stub** — its body
> was deliberately emptied by a prior remediation (`docs/docs_INVESTIGATE/REMEDIATION_prompts-audit-fixes.md:235`)
> and it adds zero `Adiabatic` surfaces. It also **cannot** implement `R6`: its signature
> `(idf, zones, strategy)` carries no neighbour footprints, so cross-building adjacency is not derivable inside it.
> The *physical* rule in `R6` — a wall shared with a neighbour within 0.30 m is `Adiabatic`, the neighbour still
> shades — **stands unchanged**. Only the named implementation is corrected:
>
> - `openubem/idf/surfaces.py` is **not edited**. The stub stays as it is; the North-American path stays provably
>   unchanged (`builder.py:642` keeps calling the same no-op).
> - The flip is implemented as a **European-only** pass in `scripts/run_eu_s2_campaign.py`, which plan §3 already
>   lists for "adiabatic call". It takes the **same** neighbour rows and the **same** coordinate transform that
>   `build_european_context` (T06) already uses and proved correct, so the shading geometry and the party-wall
>   flip can never disagree about which neighbour is where.
> - Scope of the flip: `BUILDINGSURFACE:DETAILED` where `Surface_Type == Wall` **and**
>   `Outside_Boundary_Condition == outdoors` only. `ground`, `surface` (inter-zone, from `intersect_match`) and
>   every `Floor` / `Roof` / `Ceiling` are never touched — the `z = 0` `Ground` guard above is unaffected.
> - Flip semantics: set `Outside_Boundary_Condition = Adiabatic`, blank `Outside_Boundary_Condition_Object`,
>   `Sun_Exposure = NoSun`, `Wind_Exposure = NoWind`. Anything less leaves an EnergyPlus-invalid surface.
> - Ordering: after `intersect_match` **and** after shading blocks are added, so `R8` is untouched and no flipped
>   wall can re-enter pairing.
> - Adjacency test: the wall's XY segment lies inside the neighbour footprint buffered by **0.30 m**. State the
>   test actually used; do not tune the tolerance to move a count.
> - Additional disclosure under `R9`: also report **flipped exterior wall area as a fraction of total exterior
>   wall area**, per district. The IDF count alone hides the magnitude — a 92 % IDF-count hit could be one wall
>   or half the envelope, and the two imply very different heating deltas.

⚠ A ground-floor slab at `z = 0` keeps its `Ground` boundary condition and is never flipped
(`surfaces.py:912`).

### R7 — Solar and shadow settings
`Building` keeps `Solar Distribution = FullExterior` (already set,
`scripts/run_eu_s2_campaign.py:74`), which is what makes external shading surfaces act on the envelope. A
`ShadowCalculation` object must be added and its settings stated in the results document — the EnergyPlus
default (20-day periodic update) is not defensible in a dense urban context and is currently implicit.
🔴 The chosen values are an executor **report**, not an executor **ruling**: state them, do not tune them
to move a number.

### R8 — Ordering invariant
`intersect_match` runs after all zones are added and **before** shading blocks are added
(`openubem/idf/surfaces.py:781`, DESIGN §3E lines 247–252). Shading geometry must never enter
`intersect_match`.

### R9 — Disclosure
Every district's results document reports: context radius used, mean / median / max context buildings per
target, the height-fallback census (R4), the count of buildings with ≥1 adiabatic party wall, and the
`ShadowCalculation` settings. A district EUI published without these is not quotable.

---

## 3. Acceptance test

An `EU-16` implementation is accepted only if all of:

1. **`Shading:*` object count > 0 in ≥ 99 % of emitted IDFs**, and the per-building count matches the 20 m
   spatial query to ±0 for a named sample of 10 buildings per district.
2. **Adiabatic surfaces present** in a number of IDFs consistent with the measured attachment census —
   Madrid ≈ 99.1 %, Lyon ≈ 97.0 %, London ≈ 92.8 %, Bologna ≈ 88.5 % of simulated buildings — reported as
   measured, not asserted.
3. **Zone count unchanged** by this task alone: adding context and flipping party walls changes no
   thermal zone. Any zone-count movement means `EU-15` geometry leaked in and must be reported separately.
4. **No context building appears as a `Zone`** in any IDF (`grep -c` on the shading names → 0 matches in
   the zone list).
5. **A before/after EUI delta is reported per district**, with the sign explained. Shading lowers solar
   gain (heating up); adiabatic party walls remove a loss path (heating down). The two act in opposite
   directions and the net is not predictable in advance — 🔴 **an executor that reports only the net, or
   that tunes an input to reach an expected band, has failed.**

---

## 4. What this rule does not do

- ⚪ It does **not** authorise inter-building heat transfer, a district-wide merged model, or any
  co-simulation. Buildings stay independent.
- ⚪ It does **not** change the dwelling-layout scheme, which is `D-EU-39` / `EU-15` and, under the
  no-core regime ruled 2026-09-02 and the `C11` flat-proportion arc ruled 2026-09-03 (`D-EU-82` … `D-EU-87`),
  `EXAMPLE_dwelling_layout_validation_nocore_2026-09-03.md` (the earlier no-core version,
  `EXAMPLE_dwelling_layout_validation_nocore_2026-09-02.md`, and the original,
  `EXAMPLE_dwelling_layout_validation_2026-08-28.md`, both now live in `rules/archive/`).
- ⚪ It does **not** authorise editing `config.SHADING_SPHERE_RADIUS` or the North-American path.
- 🔴 It does **not** make any pre-`EU-16` district EUI quotable retroactively. Those four figures were
  produced without context and stay barred (`previous/STATE_european_locations_v3.md` §1).
