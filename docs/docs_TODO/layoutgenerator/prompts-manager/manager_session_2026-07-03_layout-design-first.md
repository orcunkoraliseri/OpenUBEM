# Manager-session handoff — LayoutGenerator, LAYOUT-DESIGN-FIRST phase

> **Paste-and-go for a fresh Opus/Fable manager session.** Read this top-to-bottom, then read
> `../Design_layoutgenerator.md` (THE design source) and `../debugs/PLAN_design_buildout_by_archetype.md`
> (the executor plan), then continue the layout-DESIGN work with the user. You are the **manager**: you
> write/own the design + plan docs and audit; **Sonnet employees execute ALL code, figures, tests.**
> Updated by the outgoing manager, 2026-07-03 evening (design-first pivot session).

---

## 0. Who you are + standing directives (do not violate)

You are the OpenUBEM **manager** for the LayoutGenerator **layout-design-first** phase. Active directives,
most important first:

1. **DESIGN ONLY — NO SIMULATION, NO LOADS, NO BOUNDARY CONDITIONS, NO IDF ARRANGEMENT (2026-07-03).**
   The user's words: *"no load arrangement, idf arrangement, boundary conditions just design"* and
   *"like an architect we will design layouts."* Every step's deliverable = **geometry + a layout-comparison
   figure + pure-python unit tests** (area conservation, corridor connectivity, no slivers). The user
   reviews the **figure**. EnergyPlus / extrusion-safety is **deferred** to a single pass much later, after
   the whole design is settled — do NOT gate any geometry change on E+, do NOT run E+.
2. **Manager plans-only (2026-07-03).** You write the design/plan docs (in `../` and `../debugs/`), decide
   at checkpoints, and validate (audit Sonnet output, eyeball figures). You do **not** write feature code —
   not even delicate geometry. Dispatch Sonnet employees for ALL execution.
3. **Review artifact = the comparison grids** in
   `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/outputs/`. The user wants to see ONLY these
   design figures — no sim output, no side-issues. One grid per archetype; go one step at a time; the user
   signs each figure off before the next.

**Also standing (CLAUDE.md + memory):** no `.py` under `docs/`; never edit root `main.py`/OVERVIEW/DESIGN;
zero fitted params (every dim cited to `MODULE_SPECS`/DOE/ASHRAE App-G/IBC/Neufert); git handled externally
(never commit); no login-node compute; default to Sonnet employees; cheap-model monitoring ≥30-min.

---

## 1. THE BIG PIVOT this session — one universal template, grouped, alternatives-in-figures

The arc had been building loads/BC/sim before the layouts were designed. The user stopped that and
reframed the whole design. **Three load-bearing decisions were made — they are now the spine of the work:**

### 1a. ONE universal template, not five engines
The existing corridor + packed-perimeter-rooms layout already **merges rooms into corridor + N/S/E/W
thermal zones** — which is *structurally identical to core + 4 perimeter*. So **units+corridor and
core+perimeter are the same template.** Between building types **only three things change:** the room
**function label** (Apartment→GuestRoom→Office→Classroom→PatientRoom…), the **central spine width** (thin
corridor vs. fat office core), and the **room depth/bay**. → There are **NO separate office/school/hospital
engines** — one template + a per-archetype parameter table.

### 1b. THE CORRIDOR LAW (the single shared geometry task) — user's exact requirement
On every multi-wing footprint:
1. **All corridor runs connect into ONE network** — vertical + horizontal segments meet at every junction,
   including bridging through a **U-base** and closing the loop around an **O-ring** (today Approach A
   emits U=2 / O=3 disconnected pieces — that must become 1).
2. **Every corridor run reaches the exterior facade (fire-escape / egress)** — corridor termini extend to
   touch the perimeter wall, replacing today's **inset/landlocked** corridor. Rooms stay on the two long
   sides; the short ends open to the facade (like the DOE reference bar).
Recorded in `Design_layoutgenerator.md` §4 "THE CORRIDOR LAW". Fix it once → every corridor archetype
benefits.

### 1c. The template does NOT apply to all buildings — GROUP them (Design §3.1)
Restaurants, data centers, warehouses have **no corridor, no room separation** — forcing a corridor is
wrong. Buildings are grouped; alternatives are drawn from each building's **own group**:
- **Corridor groups (template applies):** G1 Residential (Midrise+Highrise apt), G2 Lodging (hotels),
  G3 Office/tower core-perimeter (Medium+Large office, Tall, SuperTall), G6 Institutional (schools,
  college, hospital, outpatient, lab).
- **Non-corridor groups (opt out — single-zone / functional / tenant split):** G4 Small standalone
  (**SmallOffice** [pairs with retail OR isolated — user's call], RetailStandalone, Small_Retail,
  restaurants), G5 Open-volume/big-box (warehouse, data centers, supermarket), G7 Strip mall,
  G8 Single-family (houses).
- User's scale hints captured: Midrise+Highrise together; offices together **except SmallOffice**.

### 1d. Alternatives — SHOW THEM IN THE FIGURES (user decision)
For each building type the comparison grid renders **2–3 alternative layouts side by side** (DOE default +
real-world variants) for visual design exploration. **Production still auto-selects one variant by footprint
geometry** (narrow→single-loaded, deep→concentric, wide→double-loaded) — zero-fitted, so the figure options
don't fabricate a production choice. Option set per group is in Design §3.1 + §7. Examples: apartments →
double-loaded / single-loaded / point-access; offices → central core / side core / concentric.

---

## 2. Locked step order (user, 2026-07-03) + status

| Step | What | Status |
|---|---|---|
| **SC** ⭐ | THE CORRIDOR LAW + regenerate the 2 reference plans | ✅ **DONE + MANAGER-AUDITED PASS** (2026-07-03 eve, see §3) — awaiting USER figure sign-off |
| **S1** | MidriseApartment (done) + HighriseApartment | ✅ **DONE** — highrise enabled by a single `MODULE_SPECS` row (zero new geometry — proves the template thesis), figure emitted, 193 tests green |
| **S2** | TallBuilding + SuperTallBuilding — relabel template | pending (see §4 mixed-use note) |
| **S3** | Offices (Medium/Large) — relabel template | pending |
| **S4** | Hotels (Small/Large) — apply corridor law | pending |
| **S5** | Hospital/Outpatient/schools/retail/houses | pending |

After SC, each S-step = (i) parameter-table relabel on the one template + (ii) alternative-option panels
per §1d, NOT a new engine.

---

## 3. FIRST MOVE — SC audit is DONE (PASS); get the user's figure sign-off

> **The SC audit below is already complete — do NOT re-audit or re-dispatch SC.** The outgoing manager
> viewed both figures and recorded a PASS on 2026-07-03 eve; the user was shown the figures on 2026-07-04
> morning. **Your actual first move: confirm the user's sign-off on the two reference plans, then dispatch
> the per-group alternative panels (apartments first) per §6.** If the user has NOT yet said "proceed,"
> ask for the sign-off before dispatching anything.

**Reference-plan locations (both current, regenerated 2026-07-03 22:52):**
- Canonical review copies the SC step wrote: `../outputs/layoutgenerator_doe_vs_generated.png` (MidriseApartment)
  and `../outputs/layoutgrid_LargeHotel.png` (LargeHotel). Also mirrored in `openubem/outputs/LayoutGenerator/`.
- **The user also keeps a `../Reference_Plans/` folder** — on 2026-07-04 the manager copied those same two
  PNGs there as the user's canonical reference-plan snapshot. ⚠️ **OPEN DECISION (unresolved, ask the user):**
  should `plot_layout_grid.py` be pointed to write into `Reference_Plans/` so it self-syncs each step, or
  stay a manual snapshot the manager re-copies per step? Until decided, **re-copy the two PNGs into
  `Reference_Plans/` after any regeneration** so it doesn't go stale.

**The audit that was run (acceptance criteria, for the record):** on L/U/T/O/cross the corridor must be
**1 connected network** (U-base bridged, O-ring closed) AND **touch the outer facades** at wing ends (no
landlocked/inset corridor); area conserved `<1e-4`; suite green. All met — see the PASS block below.
*(NOTE: this is delicate geometry that crashed E+ before — T16b T-junctions, T18-DIAG slivers — but per
directive #1 those are DEFERRED; do NOT chase E+ now, judge on the figure + area conservation.)*

### ✅ SC REPORTED + MANAGER-AUDITED PASS (2026-07-03 evening) — finalized by outgoing manager

**Both reference plans regenerated and audited. Verdict: PASS. THE CORRIDOR LAW is satisfied on
every shape. Only the USER figure sign-off remains.**

**What SC fixed (root cause + 3 edits, all in `layoutGenerator.py`, design-only):**
- Root cause: the old bridge loop counted network components with shapely `linemerge`, which cannot
  represent a T/X branch as one `LineString` — so any 3+-way wing junction (U/T/cross/O) over-reported
  components and the greedy nearest-pair search kept re-bridging already-touching fragments, never
  reaching the disjoint wing past the junction.
- Fix 1: `_touching_groups` (union-find over pairwise touching) + rewrote `_connect_centerlines` to
  bridge **adjacent wings** (shared wall) — a tree for L/U/T/cross, a **cycle** for O so the ring closes.
- Fix 2: caught the regression this exposed — a closed O-ring intersected with the holed footprint made
  a single annulus corridor with an interior ring (the donut E+ Fatal T05 was built to prevent). Fixed by
  clipping the corridor buffer **per wing** (hole-free by construction) → O emits 8 hole-free zones that
  still dissolve to 1 closed-ring component at the union level.
- Fix 3: `_pack_bar` — removed the inset west/east end-cap bands (T03 scheme) so the corridor spans the
  wing's full length and its short ends open directly onto the facade (bar zone count 5→3 double-loaded,
  4→2 single-loaded). Deliberate reading of the contract's "replacing the inset-corridor scheme (T03)."

**Manager eyeball audit of the two figures (both `../outputs/` copies):**
- `layoutgenerator_doe_vs_generated.png` (MidriseApartment): bar/wide-bar corridor spans full width and
  touches BOTH short-end facades (inset caps gone); L/rotated-L meet at elbow; **U bridged through the
  base** (was 2 pieces → 1); T three arm-ends reach facade; cross all four arms; **O one continuous
  closed ring** (was 3 disconnected arcs).
- `layoutgrid_LargeHotel.png` (GuestRoom relabel): same law holds; honest PREVIEW footer preserved
  ("production degrades hotels on L/U/T/O to per-floor pending E+ validation T13a").
- Note on O: a donut corridor is inherently internal (egress via cores, not facade) — closed-ring
  connectivity is the correct read; the per-terminus facade probe is vacuous for a ring, as expected.

**SC-reported verification (corroborates the eyeball):** corridor connected-piece = 1 on every shape
(O = 1 closed ring), every corridor zone hole-free, corridor-to-facade touch confirmed by
boundary-length + per-terminus point probe (zero counterexamples), **area drift 0.000000%** (machine
precision), full gate `pytest test_layout_generator + test_zoning + test_surfaces + test_step3_orchestrator`
→ **222 passed** (139 in the layout file). New tests: `test_corridor_cells_union_connected` (==1 component),
`test_no_holed_corridor_zone`, `test_corridor_touches_facade`, `test_corridor_touches_both_facade_ends`,
`TestCorridorLawAllShapes` (both archetypes × full shape catalogue). Progress-log `#### SC …` appended
to `../debugs/PLAN_design_buildout_by_archetype.md` §4.

**One carry-forward SC flagged:** at SC's session start `_pack_connected_spine` already used a per-wing
local room-cut (not committed HEAD's full-span grid-cut) — a pre-existing uncommitted rewrite that had
already fixed the D1 cross-wing-bleed sliver; SC built on it as the "Approach A" baseline and did not
author it. Not this step's work; noted so a fresh session doesn't mistake it for SC's change or a regression.

**→ NEXT: show the user both figures for sign-off (unblocks S2 + per-group alternative panels).**
Nothing needs re-dispatching; SC is clean.

---

## 4. Key facts the fresh session needs

- **DOE building ground truth (IDF inventory, employee-verified 2026-07-03):** 31 IDFs in
  `C:\Users\o_iseri\Desktop\idf_reader\Content\00.Baseline_NUs_CAN_CLG`. Families confirmed + a 7th
  surfaced: **`mixed_use_vertical_stack`** for TallBuilding (164 zones/38 flr) + SuperTallBuilding
  (256 zones/72 flr) — the DOE towers are retail-podium→office→residential→hotel stacks, NOT uniform
  offices. **BUT OpenUBEM models them as a UNIFORM core+perimeter proxy** (OSM gives one archetype + no
  per-floor program; L10/L07 proxy to LargeOffice) — so S2 stays "easy" (one core+perim floor stacked).
  Full detail in Design §10. Representative-floor+Multiplier technique is pervasive → towers need real
  geometry for only ONE typical floor.
- **Module dims (zero-fitted, cited):** in Design §5.1/§5.2. Apartments corridor 1.68 / depth 7.62 /
  bay 11.58. Hotels have a **known dim conflict** (committed `MODULE_SPECS` 1.83/7.32/3.66 & 2.44/7.32/4.11
  vs L07's 4.27×7.62) — ratify before hotels productionize (Design §5.1 flag).
- **Research grounding:** `../deepResearch/` L01–L15. Load-bearing for this phase: **L03** (App-G
  core/perim generalization), **L06** (corridor packing), **L07** (per-archetype module dims), **L09**
  (office/retail/school), **L10** (hospital/large/deep-plate + tower proxy), **L01/L02** (the alternatives
  taxonomy).

---

## 5. Key files

| Path | Role |
|---|---|
| `../Design_layoutgenerator.md` | **THE design source** — philosophy, groups (§3.1), shape catalogue, corridor law (§4), per-family recipes (§5), alternatives (§7), tower mixed-use finding (§10). READ THIS SECOND. |
| `../debugs/PLAN_design_buildout_by_archetype.md` | The executor plan (design-only) — §0b pivot, locked step order, SC + S1 task detail + progress log. READ THIS THIRD. |
| `../summaryPlan.md` | One-page summary of the *old* implementation plan (T01–T18 state) — background only. |
| `../PLAN_layoutgenerator_implementation.md` | The ORIGINAL arc plan (T01–T18). **Left as-is per user — do NOT edit it this phase.** Its progress log has all the geometry history (T16b connected-spine, T18-DIAG slivers). |
| `openubem/geometry/layoutGenerator.py` | The engine — `_pack_connected_spine`, `MODULE_SPECS`, `generate_layout(force_complex=…)`. Sonnet edits only. |
| `scripts/plot_layout_grid.py` | Regenerates the comparison grids into `../outputs/` + `openubem/outputs/LayoutGenerator/`. |
| `../outputs/*.png` | The review figures (apartment `doe_vs_generated` + HighriseApartment + Small/LargeHotel grids), mirrored in `openubem/outputs/LayoutGenerator/`. All carry the corridor law post-SC. |
| `../Reference_Plans/` | User's canonical reference-plan snapshot — holds the 2 designated PNGs (`layoutgenerator_doe_vs_generated.png` + `layoutgrid_LargeHotel.png`). Re-copy here after any regen until the script-output-path decision is made (§3). |

---

## 6. How to continue (morning)
1. Read this file → Design doc → buildout plan.
2. **SC audit is already PASS (§3).** Confirm the user's sign-off on the two reference plans (and settle the
   `Reference_Plans/` script-output-path question in §3). Do NOT re-audit or re-run SC.
3. On sign-off: dispatch the **per-group alternative panels**, starting with **apartments** (double-loaded /
   single-loaded / point-access) — design-only, figures + tests, NO E+.
4. Then walk the locked step order (S2 towers → S3 offices → S4 hotels → S5 hospital/rest): for each,
   parameter-table relabel on the one template + its group's alternative panels. One step, one sign-off.
5. Keep everything DESIGN-ONLY until the whole layout design is settled; only then plan the single deferred
   E+ validity pass.
