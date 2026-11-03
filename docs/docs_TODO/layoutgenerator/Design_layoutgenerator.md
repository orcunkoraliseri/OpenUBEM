# Design — `layoutGenerator`: interior zone layouts for every DOE building, footprint-shape-first

> **Purpose.** This is the *design-on-paper* document for OpenUBEM's interior-zoning engine. It answers,
> for **every DOE/ASHRAE prototype building type**, the architect's question: *how do we draw the thermal
> zones inside this building's real (often non-rectangular) footprint?* — **before** any loads, boundary
> conditions, or EnergyPlus runs. Loads/BC/sim are deliberately deferred (they were built first by
> accident; we are correcting the order). This doc is the layout-design source; it does **not** replace
> `PLAN_layoutgenerator_implementation.md` (left as-is) and carries **no task list** — it is design intent.
>
> **Grounding.** DOE prototype geometry (`C:\Users\o_iseri\Desktop\idf_reader\Content\00.Baseline_NUs_CAN_CLG`,
> 29 IDFs) + the `deepResearch/` literature set (L01–L15, esp. **L03, L06, L07, L09, L10**). Every
> dimension is a **published convention** (DOE/PNNL, ASHRAE 90.1 App-G, IBC, Neufert) — **zero fitted
> parameters** — and every generated zone must carry **provenance**. Manager-authored 2026-07-03.

---

## 1. The design philosophy — zones on paper, footprint-first

An architect designing a building's floor plan does **not** start from HVAC loads. They start from the
**footprint outline** and the **program** (what rooms the building type needs), then draw circulation
(corridors/cores) and pack rooms against the envelope. OpenUBEM's layout engine mirrors this:

1. **The real OSM footprint is sacred** — never swapped for a prototype rectangle. Its true shape drives
   the layout (and downstream, its true self-shading).
2. **The DOE prototype supplies the *program*, not the *outline*** — the room module (dwelling unit,
   guest room, classroom, patient room), the corridor width, the perimeter depth, the space-type mix.
   These are the "kit of parts" we pack onto the real shape.
3. **Loads come last.** Once the zones are drawn and area-conserving, the DOE per-space intensities are
   distributed onto them (the L11 conservation math). That is a *later* phase — out of scope here.

So the design problem factors into **two orthogonal axes**:

| Axis | What it is | Where it comes from |
|---|---|---|
| **Zoning family** | The building type's interior *organization logic* (corridor+units? core+perimeter? classroom wings? open box?) | DOE prototype program (L07/L09/L10) |
| **Footprint shape** | The geometric *outline* the layout must adapt to (rect / L / U / T / O / cross / ribbon / irregular) | The real OSM polygon |

> **Layout = apply the family recipe to the footprint shape.** The whole design reduces to: (a) sort every
> DOE building into a small set of families; (b) define each family's kit-of-parts + packing recipe;
> (c) define how each recipe adapts across the footprint-shape catalogue. Sections 4–7 do exactly this.

---

## 2. Two hard constraints (repeated on every recipe)

1. **Zero fitted parameters.** Every corridor width, room depth, bay pitch, perimeter offset, and area
   fraction traces to a named source (DOE prototype dimension, ASHRAE 90.1 App-G 4.57 m, IBC corridor
   minimum, Neufert classroom module). No value is tuned to make an EUI match.
2. **Provenance mandatory.** Every generated zone records *which family recipe, which shape path, and
   which fallback (if any)* produced it, at a confidence tier — so a degrade is never silent.

And one safety invariant inherited from the current engine:

3. **Always degrade, never crash.** Any footprint the recipe cannot zone cleanly falls back to
   `one_zone_per_floor` (correctness > coverage). Machine-precision **area conservation**
   (`Σ zone areas = footprint × floors`) holds on every path.

---

## 3. The DOE building inventory → zoning-family map

The 29 baseline IDFs collapse into **six layout families**. (Ground-truth zone counts below are the
DOE as-modeled values from L07 Table 1 / L09 / L10; an employee pass is verifying counts + floorplate
shapes against the actual IDFs — §10 will note any correction.)

| DOE prototype (IDF) | OpenUBEM archetype | Zoning **family** | DOE zones/floor (as-modeled) | Current OpenUBEM status |
|---|---|---|---|---|
| ApartmentMidRise | MidriseApartment | **units+corridor** | 9 (8 apt + 1 corr) | ✅ **room-level in production** (L/U/T/O/cross) |
| ApartmentHighRise | HighriseApartment | **units+corridor** | 9 (8 apt + 1 corr) | ⚠️ same module as Midrise; not yet enabled |
| HotelSmall | SmallHotel | **units+corridor** | 10 guest-flr (8 GR+corr+BOH) | ⚠️ **preview only**; production degrades complex→per-floor |
| HotelLarge | LargeHotel | **units+corridor** (+ podium) | 7 guest-flr (E/W GR+corr+mech) | ⚠️ preview only; podium ground floor is core+perim |
| OfficeSmall | SmallOffice | **core+perimeter** | 5 (4 perim + 1 core) | ⚠️ compact works via geomeppy; non-rect degrades |
| OfficeMedium | MediumOffice | **core+perimeter** | 5/floor × 3 | ⚠️ compact works; non-rect degrades |
| OfficeLarge | LargeOffice | **core+perimeter** (deep plate) | 6 (4 perim + core + IT) | ⚠️ compact works; non-rect + deep-plate not built |
| TallBuilding | TallBuilding | **core+perimeter** (proxy; DOE IDF is mixed-use stack — §10) | 164 zones / ~38 flr (proxy → 5/flr) | ❌ forced per-floor today |
| SuperTallBuilding | SuperTallBuilding | **core+perimeter** (proxy; DOE IDF is mixed-use stack — §10) | 256 zones / ~72 flr (proxy → 5/flr) | ❌ forced per-floor today |
| ASHRAE_HighRise ST15 / ST20 | HighriseApartment (variant) | **units+corridor** (15/20-storey ApartmentHighRise variants) | 27 | ⚠️ same module as Midrise |
| College | (college) | **classroom-wing** (cellular rooms off corridors + assembly) | 117 | ❌ no engine |
| Laboratory | (lab) | **cellular-departmental** (lab wing + office wing) | 24 | ❌ no engine |
| OutPatientHealthCare | Outpatient | **core+perimeter** | 5 (4 exam/office + core waiting) | ❌ no engine (degrades) |
| SchoolPrimary | PrimarySchool | **classroom-wing** (hybrid) | 25 (classrooms + pods + assembly) | ❌ no engine |
| SchoolSecondary | SecondarySchool | **classroom-wing** (hybrid, 2-storey) | 23/floor | ❌ no engine |
| Hospital | Hospital | **cellular-departmental** (→ functional-proxy core+perim) | 15–17 | ❌ no engine (degrades) |
| RetailStandalone | RetailStandalone | **functional-split** | 2 (Sales + Storage) | ❌ single-zone today |
| Supermarket | Supermarket | **functional-split** | 6 (Sales/Produce/Deli/Bakery/Storage/Office) | ❌ single-zone today |
| RestaurantFastFood | QuickServiceRestaurant | **functional-split** | 2 (Dining + Kitchen) | ❌ single-zone today |
| RestaurantSitDown | FullServiceRestaurant | **functional-split** | 2 (Dining + Kitchen) | ❌ single-zone today |
| DataCenter (Lg/Sm, Hi/Lo ITE) | DataCenter | **functional-split** | few (IT + support) | ❌ passthrough / single-zone |
| Small_Retail (MT5) | SmallRetail | **functional-split / single** | 1–2 | ❌ single-zone today |
| Warehouse | Warehouse | **single / open-plan** | 3 (Office + Bulk + Fine storage) | ✅ single-zone is *correct* |
| RetailStripmall | RetailStripmall | **single / strip-multitenant** | 10 tenant boxes | ❌ single-zone today |
| DetachedHouse | (SF detached) | **single-family** | handful (living/sleeping/basement/attic) | ❌ separate residential logic |
| AttachedHouse | (SF attached / rowhouse) | **single-family** (unit-in-a-row) | handful per unit | ❌ separate residential logic |

### Build order — LOCKED by the user 2026-07-03 (archetype-driven, not family-driven)

The user fixed the step sequence and the review workflow:

> **Review workflow.** Design is reviewed **only** through the layout-comparison grids (the three
> `outputs/*.png` style: DOE reference vs generated across the shape catalogue). **No simulation, no
> loads, no side-issues during design** — geometry + figures + unit tests only. Each archetype gets its
> own comparison grid in `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/outputs/`; we go one
> step at a time and the user signs each figure off before the next.

| Step | Archetype(s) | Family | Why here / note |
|---|---|---|---|
| **S1** | **MidriseApartment + HighriseApartment** | units+corridor | Midrise already shipped; **highrise shares the identical per-floor module** → one apartment design covers both (only floor count differs). |
| **S2** | **TallBuilding + SuperTallBuilding** ⭐ | core+perimeter | **User-emphasized + "easy."** Real-world towers are uniform prismatic core+perim plates stacked — the layout barely varies floor-to-floor, so generation is the simplest of the un-built families. Currently forced per-floor. |
| **S3** | **Offices** (Small / Medium / Large) | core+perimeter (+ deep-plate) | Same core+perim engine as S2, plus the deep-plate concentric-band rule for LargeOffice. Highest ΔEUI value (L14). |
| **S4** | **Hotels** (Small / Large) | units+corridor (+ podium) | Engine exists (preview); the design work is the complex-shape degrade decision + LargeHotel podium/tower split. |
| **S5** | **Hospital, Outpatient, + rest** (schools, retail, single-family…) | mixed | Hardest / lowest-priority last: hospital functional-proxy, school classroom-wing, functional-split, houses. |

Families that back these steps: **units+corridor** (S1, S4), **core+perimeter incl. deep-plate** (S2, S3,
hospital-proxy in S5), **classroom-wing / functional-split / single-family** (rest of S5).

### 3.1 Building GROUPS — the corridor/room template does NOT apply to all (user, 2026-07-03)

**Key realization:** the corridor + packed-rooms template fits only *corridor buildings*. **Restaurants,
data centers, warehouses have no corridor and no room separation** — forcing a corridor into them is wrong.
So layout **alternatives are proposed per building GROUP**, and each group declares whether the template
applies. Groups also encode the user's scale hints (midrise+highrise together; offices together *except*
SmallOffice, which pairs with retail or stands alone).

| Group | Members | Corridor/room template? | Layout + alternatives (A = default) |
|---|---|---|---|
| **G1 — Residential corridor** | MidriseApartment, HighriseApartment (+ HighRise ST15/ST20 variants) | ✅ **yes** (units+corridor) | A double-loaded corridor · B single-loaded/gallery · C point-access stair-core |
| **G2 — Lodging corridor** | SmallHotel, LargeHotel | ✅ **yes** (units+corridor; LargeHotel adds a ground podium) | A double-loaded · B single-loaded · C atrium/central (large hotel) |
| **G3 — Office & tower core-perimeter** | MediumOffice, LargeOffice, TallBuilding, SuperTallBuilding | ✅ **yes** (core+perimeter = fat-spine cousin of the corridor template) | A central core · B side/end core · C concentric multi-band (deep) / centerline-split (narrow) |
| **G4 — Small standalone** | **SmallOffice**, RetailStandalone, Small_Retail (MT5), RestaurantFastFood, RestaurantSitDown | ❌ **no corridor** — single or 2-part | A single open zone · B functional front/back split (sales·dining / kitchen·storage). *SmallOffice sits here (close to retail) OR isolated as its own single core/perim box — user's call at its step.* |
| **G5 — Open-volume / big-box** | Warehouse (both), DataCenter (all 4), Supermarket | ❌ **no corridor, no rooms** — one open volume is *physically correct* | A single zone · B optional office/storage split (warehouse), sales/back split (supermarket) |
| **G6 — Institutional cellular** | PrimarySchool, SecondarySchool, College, Hospital, Outpatient, Laboratory | ✅ **yes** (corridor + cellular rooms + assembly blocks; hospital = functional-proxy core+perim) | A double-loaded corridor wings + single-zone assembly blocks · B single-loaded daylit wings · C racetrack double-corridor (hospital) |
| **G7 — Multi-tenant strip** | RetailStripmall | ❌ **no shared corridor** — linear tenant slicing | A N tenant boxes (DOE 2 anchor + 8 inline) · B single zone |
| **G8 — Single-family** | DetachedHouse, AttachedHouse | ❌ **no corridor** — few zones | A one_zone_per_floor · B living/sleeping (+basement/attic) split |

**Reading the groups:** the **corridor law (§4) + the one template** serve **G1, G2, G3, G6** — the four
corridor groups (residential, lodging, office/tower, institutional). **G4, G5, G7, G8 opt out of the
template entirely** — they are single-zone or functional/tenant splits, no corridor, no packed rooms.
Alternatives are always drawn from the building's *own group*, never one-size-fits-all.

---

## 4. The footprint-shape catalogue (the "alternatives" every family adapts to)

Every family recipe must have a defined behaviour on each shape below. These are the panels the layout
grids already show for apartments/hotels; the design extends the same catalogue to all families.

| Shape | Definition (classifier, L04) | Layout challenge |
|---|---|---|
| **Compact rectangle** | rectangularity ≥ 0.85, both axes wide | the easy case — must reproduce geomeppy core/perim exactly (no regression) |
| **Slab** (elongated bar) | rectangular but elongation < 0.40 | double-loaded bar; core may collapse (narrow) |
| **L** | one reflex corner (6 verts) | one corner where two wings meet → corridor must turn |
| **U** | two reflex corners, 1 notch | two parallel wings + a base bridge |
| **T** | two reflex corners, 2 notches | a stem meeting a bar at a junction |
| **Cross / +** | four wings from a centre | a central junction with four arms |
| **O / courtyard** | has an interior ring | donut — the classic E+ Fatal; inner ring faces the void |
| **Ribbon** (thin) | erosion `buffer(-4.57)` collapses | too narrow for core/perim → single-loaded or single-zone |
| **Rotated** | any of the above at an angle | recipe must work in the footprint's own frame, not world axes |
| **Irregular** | none of the above cleanly | last-resort single-zone degrade |

**Cross-cutting shape rules (apply to all corridor/core families):**
- **⭐ THE CORRIDOR LAW (user, 2026-07-03 — the single shared geometry task).** Two hard requirements on
  every multi-wing footprint:
  1. **All corridor runs connect into ONE network.** Vertical and horizontal corridor segments **must
     meet at every junction** and form a single connected circulation graph — including bridging through
     a **U-base** and closing the loop around an **O-ring**. No per-wing stubs, no disconnected pieces.
     (This supersedes the earlier "emit the minimum connected pieces" allowance — U and O must now be one
     connected corridor, not 2/3 pieces.)
  2. **Every corridor run reaches the exterior facade (fire-escape / egress).** Each corridor terminus
     extends to touch the perimeter wall so circulation always leads to an exit on the facade — like the
     DOE reference's full-span corridor. **This replaces the current "inset corridor" scheme** (T03), where
     end-cap rooms landlock the corridor. Rooms remain on the corridor's two long sides; the short ends
     open to the facade.
- **No cross-wing bleed slivers.** Rooms are cut **locally per wing**, never by a perpendicular wing's
  corridor cut-lines (the defect just fixed for apartments — Approach A "corridor-first, per-wing rooms").
- **Courtyard never as a holed block.** An O footprint is split into hole-free wings around the void so
  geomeppy never extrudes a donut (structural fix for the inter-floor vertex-mismatch Fatal).
- **Degenerate-cell drop, never merge.** Sub-1 m-wide shear cells (real OSM edges aren't orthogonal) are
  dropped, then the 1%-area net degrades the footprint if too much is lost — merging re-introduces the
  T-junction crash.

---

## 5. Family designs — the kit-of-parts and shape adaptation

Each family below gives: **(a)** the DOE prototype's as-modeled zoning (what we're replicating);
**(b)** the zero-fitted kit-of-parts (cited dims); **(c)** the generation recipe; **(d)** the
shape-alternatives table; **(e)** status.

### 5.1 Family A — units+corridor (apartments, hotels)  ✅ built (apartments) / ⚠️ preview (hotels)

**(a) DOE program.** A double-loaded corridor: a central hallway spine with repeated identical room
modules packed on both sides forming the perimeter. Apartments = dwelling units; hotels = guest rooms.
Ground floors vary (lobby/office/BOH) — modeled per-floor, out of scope for the guest-floor geometry.

**(b) Kit-of-parts (zero-fitted).**

| Archetype | corridor width | room depth | bay pitch | room area | circ % | source |
|---|---|---|---|---|---|---|
| MidriseApartment | 1.68 m (5.5 ft) | 7.62 m (25 ft) | 11.58 m (38 ft) | 88.25 m² | 9.9% | Deru 2011 §3.1.15 |
| HighriseApartment | 1.68 m | 7.62 m | 11.58 m | 88.25 m² | 9.9% | PNNL-23269 §3.2.1 (same module) |
| SmallHotel | **1.83 m** (6 ft) | 7.32 m (24 ft) | 3.66 m (12 ft) | 26.79 m² | ~11% | Deru 2011 §3.1.13 + L06 DOE-Small-Hotel corridor |
| LargeHotel | **2.44 m** (8 ft) | 7.32 m | 4.11 m (13.5 ft) | 30.09 m² | ~20% (incl. podium) | PNNL 2020 Large Hotel + L08 |

> ⚠️ **Known dimension conflict (flag, not yet resolved for this doc).** L07 Table 2 lists both hotels as a
> 4.27 m × 7.62 m (14×25 ft) module with an 8 ft corridor; the committed `MODULE_SPECS` (per the PLAN's
> L06-vs-L08 reconciliation) uses 1.83/7.32/3.66 (Small) and 2.44/7.32/4.11 (Large). The committed values
> win (they are what ships); the conflict is real and worth a one-line user confirmation before hotels go
> to production. Apartments have **no** conflict (100% consistent across L06/L07/L08).

**(c) Recipe (Approach A — corridor-first, per-wing rooms; the just-shipped apartment engine).**
1. Rotate footprint to its dominant-edge frame; decompose into axis-aligned wings.
2. Build each wing's centerline; **connect them into one network** with orthogonal bridges at junctions.
3. `corridor = network.buffer(width/2, flat cap) ∩ footprint`; emit as **one zone per connected piece**.
4. Per wing: `room_region = wing − corridor`; subdivide **along the wing's own long axis** into
   `round(len / bay)` cells. Rotate back, clean, drop degenerate cells.

**(d) Shape alternatives.**

| Shape | units+corridor behaviour |
|---|---|
| Compact / slab | single straight double-loaded bar (corridor + N/S rows + E/W end caps) = the DOE reference |
| L | corridor bends at the elbow; rooms packed on both faces of each arm |
| U | two arms + base; corridor wraps (topology → up to 2 connected pieces) |
| T | stem meets bar; corridor T-junction |
| Cross | four arms; corridor forms a + (2 pieces) |
| O / courtyard | corridor ring around the void; inner rooms face courtyard (Outdoors); 3 pieces |
| Ribbon | too narrow → single-loaded corridor, or single-zone if below one room depth |
| Irregular | degrade to per-floor |

**(e) Status.** Apartments: **production room-level**, DOE-reproduced (T11), live-validated (T12). Hotels:
**geometry preview only** — small guest-room modules fragment complex shapes into fully-interior corridor
cells that fail HVAC autosizing, so production degrades hotels on L/U/T/O/cross to per-floor
(correctness > coverage). Promoting hotels to production room-level is a design+validation task (§8).

---

### 5.2 Family B — core+perimeter, incl. deep-plate concentric (offices, tall, outpatient, college, lab, hospital-proxy)  ⚠️ compact only

**(a) DOE program.** A service/thermal core surrounded by a 4.57 m (15 ft, App-G) perimeter ring split
into four cardinal zones. Deep plates add concentric interior bands; the DOE LargeOffice also carves a
dedicated IT/DataCenter core zone.

**(b) Kit-of-parts (zero-fitted).**
- **Perimeter depth = 4.57 m** (ASHRAE 90.1-2019 App-G G3.1.1.1). This is the *only* dimension the core
  family needs — the core is the **residual** after the perimeter buffer (no fabricated service-core
  geometry; L09 Table 3 — modeling stairs/elevators/toilets as tiny zones adds numerical instability and
  violates zero-fitted).
- **Deep-plate band rule (L10 §2), keyed on minor-axis width W and Dperim = 4.57 m:**
  - W ≤ 9.14 m → **centerline split**, perimeter-only, no core.
  - 9.14 < W ≤ 18.28 m → **standard core + 4 perimeter**.
  - W > 18.28 m → **concentric multi-band**: outer perimeter ring + intermediate band + deep core.

**(c) Recipe.**
- **Compact rectangle:** `core = footprint.buffer(-4.57)`; four perimeter trapezoids from footprint edges
  to core edges. **Must equal geomeppy `add_block(zoning="core/perim")` exactly** (no-regression identity,
  L09 §2).
- **L / U / T / cross:** **decompose into rectangular wings**; apply core/perim (or centerline split if a
  wing is narrow) to **each wing**; wing-junction boundaries are interior (adiabatic).
- **O / courtyard:** **inner + outer perimeter split** (L10 §2.4) — a 4.57 m band from the exterior AND a
  4.57 m band from the courtyard ring, core between; if the core collapses < 2 m, merge into perimeter.
  The courtyard face is Outdoors.

**(d) Shape alternatives.**

| Shape | core+perimeter behaviour |
|---|---|
| Compact | 5 zones (4 perim + core) — geomeppy-identical |
| Slab / narrow | centerline split, perimeter-only (core collapsed) |
| L / U / T / cross | decompose → per-wing core/perim; junctions adiabatic |
| O / courtyard | inner+outer perimeter ring, courtyard = Outdoors |
| Very deep plate | concentric multi-band (outer perim / mid / deep core) |
| Ribbon / irregular | single-loaded or degrade |

**(e) Status.** Compact convex offices already zone via geomeppy's native `add_block`. **Nothing** takes
the room-level path for non-rect offices, deep plates, tall buildings (still forced per-floor), or
outpatient — these all degrade today. This is the **largest un-built family** and the highest-value one
(offices rank highest ΔEUI in L14). Building it = generalizing App-G core/perim to wings + courtyards +
deep plates. **No new packing module needed** — it's a buffer/decompose engine, distinct from the
corridor packer.

---

### 5.3 Family C — classroom-wing (primary + secondary schools)  ❌ not built

**(a) DOE program.** A hybrid: **classroom wings** (double-loaded corridor with cellular classrooms on
both sides) **plus large single-space assembly blocks** (gym, cafeteria, auditorium, library) attached to
a central spine. PrimarySchool = 1 storey, 25 zones; SecondarySchool = 2 storeys, ~23/floor.

**(b) Kit-of-parts (zero-fitted).**
- Corridor width **2.44 m** (8 ft; IBC 1020 min 1.83 m, Neufert K-12 practice 2.44–3.05 m).
- Classroom depth **9.14 m** (30 ft), classroom module **9.14 × 9.14 m** ≈ 83.6 m², **cap 110 m²/room**
  (Neufert / CDE). Perimeter depth for classrooms 5.0 m (L07).
- Assembly blocks (gym/cafeteria/auditorium/library) = **single zones**, not packed.

**(c) Recipe (L09 §3).**
1. **Decompose** the footprint into **classroom wings** (narrow, high aspect ratio) vs **assembly blocks**
   (wide, compact) via a shape-split heuristic.
2. **Wings** → the units+corridor recipe (Family A) with the classroom module.
3. **Assembly blocks** → single zone each (Family E treatment).
4. Secondary school stacks two storeys; corridors/stairs align vertically (avoid inter-floor mismatch).

**(d) Shape alternatives.** Wings adapt exactly like Family A (L/U/T corridors turn); assembly blocks are
shape-agnostic single zones. The novel step is the **wing-vs-block split** — the hardest design piece.

**(e) Status.** No engine. Depends on Family A (exists) + a new **wing/block classifier**. Genuinely new
geometry — the "T13c" deferred slice.

---

### 5.4 Family D — functional-split (retail, supermarket, restaurant, data center)  ❌ single-zone today

**(a) DOE program.** No corridor, no core/perim — the floor is divided by **function** into a few zones by
**area fraction** (the DOE prototypes place these side-by-side, not by envelope).

**(b) Kit-of-parts (zero-fitted area fractions, L09).**

| Archetype | functional zones (area fraction) | source |
|---|---|---|
| RetailStandalone | Sales 80% + Storage/Support 20% (rear) | Deru 2011 §3.1.8 |
| Supermarket | Sales 55.5 / DryStorage 13.3 / Produce 11.1 / Deli 8.9 / Bakery 6.7 / Office 4.4 | Deru 2011 §3.7 |
| RestaurantFastFood | Dining + Kitchen | Deru 2011 §3.1 |
| RestaurantSitDown | Dining + Kitchen | Deru 2011 §3.1 |
| Warehouse | Office + BulkStorage + FineStorage (functional) | Deru 2011 §3.1.10 |
| DataCenter | IT/server + support | passthrough |

**(c) Recipe.** Slice the footprint transversely along its major axis into bands sized by the area
fractions (largest/public band on the entrance/perimeter side, storage/service at the rear). No corridor,
no buffer. Single storey typically.

**(d) Shape alternatives.** Bands follow the footprint's long axis; on L/U shapes, place the dominant
(Sales/Dining) band in the largest wing and support in a smaller wing. On irregular/small → single zone.

**(e) Status.** Today these are single-zone. Functional-split is **low geometric risk** (few big zones, no
slivers) and moderate value. Note L09 caveat: non-rect big-box retail is poorly evidenced — single-zone
is a defensible default.

---

### 5.5 Family E — single / open-plan (warehouse, stripmall, small retail)  ✅ mostly correct

**(a) DOE program.** A single dominant open volume (warehouse, big-box) — or a **row of independent tenant
boxes** (stripmall).

**(b/c) Recipe.**
- **Warehouse / big-box:** `one_zone_per_floor` is **physically correct** (L10 §4) — a single open volume.
  Optional functional split (Family D) only if the prototype defines one (warehouse Office/Bulk/Fine).
- **Stripmall:** slice into **N tenant zones** along the major axis (DOE: 2 anchors + 8 inline = 10), each
  an independent single zone with its own exterior access.

**(d) Shape alternatives.** Trivial — single zone regardless of shape; stripmall assumes a linear bar.

**(e) Status.** Warehouse single-zone already correct. Stripmall = a simple linear slicer (low priority).

---

### 5.6 Family F — single-family (detached, attached/rowhouse)  ❌ separate logic

**(a) DOE program.** A house: a handful of zones (living, sleeping, basement, attic/garage) — **not** a
corridor-packed or core/perim building. AttachedHouse = a unit repeated in a row (party walls adiabatic).

**(b/c) Recipe (design GAP — needs a decision).** Options:
- **Minimal:** `one_zone_per_floor` (living above, basement below) — honest, low fidelity.
- **Program-split:** living/sleeping split per floor from IECC/NBC residential conventions.
- Attached houses: treat each footprint as one unit; shared walls → adiabatic.

**(d) Shape alternatives.** Houses are usually compact/L; single-zone-per-floor covers most.

**(e) Status.** No engine; lowest UBEM value per building but highest *count* in real stock. Likely stays
per-floor unless the user wants residential room-level.

---

### 5.7 Family B′ — cellular-departmental (hospital, outpatient)  ❌ → functional-proxy core+perim

Hospitals have 15–17 heterogeneous department zones (patient rooms, ICU, OR, labs, corridors). **OSM gives
no interior department map**, so locating departments is fabricated precision (L10 §3). The defensible
design (L10 §1) is a **functional proxy on Family B**:
- **5–6 zones/floor** (4 cardinal perimeter + core [+ corridor]).
- **Perimeter** ← envelope-sensitive programs (patient rooms, exam rooms, offices).
- **Core** ← internal-load programs (OR, ICU, labs, corridors) via **area-weighted load blend**.

So hospitals/outpatient **reuse Family B geometry**; only the load-blend (a later phase) differs. Patient
room module 4.57 × 6.10 m (27.87 m²) is reference-only. Outpatient is already a clean 5-zone core/perim.

---

## 6. Cross-family design rules (the invariants every recipe honours)

1. **No-regression identity.** On a compact rectangle, every family that reduces to core/perim must emit
   the *exact* geomeppy `add_block` 5-zone output (L09 §2). Corridor families must reproduce the DOE
   reference bar (apartments already do — T11).
2. **Connected corridor spine** (corridor families) — one turning spine, minimum forced pieces.
3. **Per-wing local cuts** — no cross-wing bleed slivers.
4. **Courtyard = hole-free wings** — never extrude a donut; inner ring = Outdoors.
5. **Junctions adiabatic** — decomposed-wing shared boundaries are interior walls (core+perim family).
6. **Degenerate-cell drop + 1%-area net → per-floor** — the universal safety valve; drop, never merge.
7. **Deep-plate band selection** by minor-axis width (Family B).
8. **Provenance token per zone** — family, shape path, fallback, confidence tier.

---

## 7. Design alternatives — RENDER THEM IN THE FIGURES (user decision, 2026-07-03)

**User decision:** for each building type, the comparison grid should render **2–3 alternative layouts side
by side** (not just the DOE default), for visual design exploration. These are **exploratory design panels**
— production still **auto-selects one variant by footprint geometry** (zero-fitted; narrow→single-loaded,
deep→concentric, wide→double-loaded), so showing options in the figure does not fabricate a production
choice. Grounded in the L01 interior-zoning taxonomy + L02 peer-tool practice.

### The per-family option set to render (default = variant A)

| Family | A (DOE default) | B | C |
|---|---|---|---|
| **units+corridor** (apts, hotels) | double-loaded corridor | single-loaded / gallery-access (rooms one side) | point-access stair-core cluster (no long corridor) |
| **core+perimeter** (offices, towers) | central core + 4 perimeter | side / end core (against one facade) | concentric multi-band (deep) · centerline-split (narrow) |
| **classroom-wing** (schools) | double-loaded corridor wings | single-loaded daylit wings | courtyard / finger-plan |
| **cellular-departmental** (hospital) | racetrack double-corridor (perimeter patient rooms + core services) | single-corridor | — |
| **functional-split / single** (retail, warehouse) | single open zone | functional sales/storage split | — |

### Other real design choices (still worth a user call at their step)

| Situation | Alternative A (recommended) | Alternative B |
|---|---|---|
| **Deep office plate** | concentric multi-band (>18.28 m) | standard single core + perimeter (coarser) |
| **Hotel** on complex shape | degrade to per-floor (correctness>coverage) | production room-level (needs later sim revalidation) |
| **Single-family** | one_zone_per_floor | living/sleeping program split |
| **Service core** | App-G residual core (no fabricated core) | modeled stair/elevator/toilet core (rejected — fitted) |

> **Sequencing.** The alternative-option panels build on the **corridor-law template** (step SC, in flight)
> and would collide with SC's edits if generated now — so we render them **per archetype after SC's
> reference plans are signed off**, starting with apartments (A double-loaded / B single-loaded /
> C point-access), then towers/offices (A central / B side / C concentric), etc.

---

## 8. Design decisions — CURRENT DIRECTION (revisable; user 2026-07-04)

> These are our **working calls**, not locked contracts. The user's standing note (2026-07-04): *"we do not
> need to finalize everything, we are in the progress, of course we can change our decisions on the road."*
> So treat every item below as the current default we build against, changeable at any step. **No simulation
> is implied by any of these — all are paper-design decisions.** Answers captured 2026-07-04.

1. **Family build order.** ✅ **LOCKED by user 2026-07-03** — see §3 step table: S1 apartments →
   S2 tall/supertall ⭐ → S3 offices → S4 hotels → S5 hospital/rest. Design-only, reviewed via
   per-archetype comparison grids, one step at a time.
2. **SC reference plans.** ✅ **SIGNED OFF (user 2026-07-04)** — both figures (MidriseApartment
   `doe_vs_generated`, LargeHotel grid) look good. Unblocks S2 + the per-group alternative panels.
3. **Figure output location.** ✅ **RESOLVED (user 2026-07-04)** — figures save into `../Reference_Plans/`.
   `scripts/plot_layout_grid.py` is to write there (auto-sync), bundled into the next figure dispatch.
4. **Hotel dimension conflict (§5.1).** ✅ **RESOLVED — use the committed `MODULE_SPECS`** (Small
   1.83/7.32/3.66; Large 2.44/7.32/4.11) over L07's 4.27×7.62 (user deferred to manager rec 2026-07-04).
5. **Tall / SuperTall — MULTI-LAYOUT per function floor (user 2026-07-04).** ⚠️ **This UPDATES the §10
   uniform-proxy simplification.** The user wants towers **represented with multiple layouts, one per
   function floor** (retail podium / office / residential / hotel), rendered as the tower's alternative
   panels — not a single uniform floor stacked. **Open sub-question for S2 build:** since OSM gives no
   per-floor program, which floors get which function needs a *documented, zero-fitted assumption*
   (natural source = DOE tower stack proportions). Do NOT silently invent per-floor program — flag it at S2.
6. **Deep-plate concentric bands.** Manager recommends adopting the L10 width-keyed rule (centerline /
   core+perim / multi-band) for offices + towers — confirm at S2/S3. Zero-fitted (App-G / L10).
7. **SmallOffice placement.** ✅ **RESOLVED — SmallOffice stands on its own** (its own core/perim
   alternative), NOT lumped with restaurants (user: "up to you… if it does not fit with restaurants there
   could be another alternative"; manager chose stand-alone 2026-07-04). Stays a G4 *member* by scale, but
   with its own single core/perim box layout.
8. **Hospital + LargeHotel — SKIP complex layout generation (user 2026-07-04).** Both are already highly
   complex, so **keep the DOE structure and only handle rectangular/square footprints**; complex shapes
   degrade to per-floor. **Hospital is out of layout generation entirely** (keep DOE as-is). LargeHotel:
   rectangular/square only (reinforces the existing correctness>coverage degrade).
9. **Single-family scope.** ✅ **RESOLVED — follow the DOE house structure** (verified 2026-07-04): DOE
   splits **vertically only** — one `living` zone per heated floor + `attic` + unheated `basement`; **no
   bedroom/living-room split exists in the DOE IDF**, so we don't invent one. AttachedHouse = the same
   3-zone unit repeated per row unit (party walls adiabatic).
10. **Functional-split scope.** ✅ **RESOLVED — BUILD the splitter (user 2026-07-04): "split of course."**
    This is the core idea of the layout generator — *adapt DOE standard layouts to new footprint shapes
    while preserving each room's function*. Applies to retail / supermarket / restaurant (Sales/Storage,
    Dining/Kitchen, etc.).

---

## 9. Literature → design decision map (deepResearch provenance)

| Design decision | Source RESULT | Key content used |
|---|---|---|
| units+corridor is the field convention | L06 | double-loaded corridor packing rules, corridor/depth dims |
| App-G core/perim generalization to L/U/T/O | L03, L09 | 4.57 m rule, decompose-to-wings, courtyard inner/outer |
| Per-archetype module dimensions | L07 | DOE plate + module + circulation + f2f, all cited to Deru 2011 |
| Office/retail/school specifics | L09 | service-core placement, classroom-wing = L06, big-box single-zone |
| Hospital / large-hotel / deep-plate | L10 | functional proxy, podium-tower split, concentric band rule |
| Shape classification | L04 | rectangularity/convexity/reflex-corner ladder → shape enum |
| Geometry primitives (shapely-only) | L05 | buffer/split/OBB — no straight-skeleton/medial-axis libs |
| Load conservation (LATER phase) | L11 | space-type-weighted normalization; interior BCs |
| When room-level is worth it | L14 | offices high ΔEUI, apartments low — build-priority evidence |
| Validation without ground truth | L15 | DOE-reproduction + mask-and-recover (later) |

---

## 10. Ground-truth verification (IDF inventory, employee pass 2026-07-03)

An employee read all 31 IDFs in the folder (29 in the README + two extra `ASHRAE_HighRise_ST15/ST20`
storey-count variants of ApartmentHighRise). Key confirmations + corrections to §3/§5:

- **Families confirmed**, with a **new seventh family surfaced: `mixed_use_vertical_stack`** — see below.
- **Representative-floor + `Multiplier` technique is pervasive** (apartments, offices, hotels, labs,
  towers): the DOE prototypes model only 1–3 *characteristic* floors and multiply. **This is a design gift
  for towers/repeated-floor archetypes — the generator needs real footprint geometry for only ONE typical
  floor, then stacks it.** Reinforces the "towers are easy" intuition.
- **Floorplate shapes (inferred from zone naming):** Offices / Labs / Apartment+Hotel towers read as
  **simple rectangles**; Schools + College show **wing/pod (finger-plan)** structure; Hospital +
  Outpatient show **SE/NW corridor splits → L/cross plans**; Stripmall/Warehouse are rectangular bars.
- **Corrections to §3:** **College → `classroom_wing`** (cellular classrooms/offices off corridors +
  assembly rooms, not a plain MediumOffice proxy). **Laboratory → `cellular_departmental` hybrid** (lab
  wing + separate office wing per floor). **HotelLarge** confirmed as units+corridor with a podium ground
  floor + banquet top (validates the §5.1 podium/tower split). **AttachedHouse** = 7 single-family unit
  triads in a row, **no corridor** → `single_family` (repeated), not units+corridor.
- **Exact zone counts** (top archetypes): MidriseApt 27, HighriseApt 27, HotelSmall 67, HotelLarge 22
  (representative-floor), OfficeSmall 6, OfficeMedium 18, OfficeLarge 23, Hospital 55, Outpatient 118,
  SchoolPrimary 25, SchoolSecondary 46, College 117, TallBuilding 164, SuperTallBuilding 256.

### ⭐ Tall / SuperTall — the S2 design decision this finding forces

The DOE **TallBuilding (38 storeys, 164 zones)** and **SuperTallBuilding (72 storeys, 256 zones)** IDFs are
**mixed-use vertical stacks**, not uniform office towers:

```
Mechanical penthouse
Hotel tower        (units+corridor floor-bands)
Residential tower  (units+corridor floor-bands)
Office tower       (core+perimeter floor-bands)
Retail podium      (open-plan / functional-split)
Basement
```

**But OpenUBEM does not — and cannot — replicate that stack**, for two reasons: (1) OSM gives **one
archetype tag + no per-floor program**, so we can't know which floors are hotel vs office vs residential;
(2) OpenUBEM's classifier already assigns a **single** archetype (`TallBuilding`/`SuperTallBuilding`) whose
loads are **proxied to LargeOffice** (L07 §3, L10 Table 1). So the defensible OpenUBEM design is exactly
the user's intuition:

> **DESIGN DECISION (S2): model Tall/SuperTall as a UNIFORM core+perimeter tower** — generate one typical
> core+perim floor on the real footprint and stack it (Multiplier). This is the L10 recommendation
> ("TallBuilding should get core+perim to prevent solar dilution", currently forced per-floor), and it is
> **easy** precisely because real towers are prismatic (constant footprint per floor). The mixed-use reality
> of the DOE reference IDF is recorded here as a **documented simplification**, not something we generate.

`mixed_use_vertical_stack` is therefore a **known-but-out-of-scope** family (no per-floor program data to
drive it; the L12 vertical-heterogeneity research is the frontier tier). If the user later wants podium /
tower splits, that is a separate arc needing a per-floor program assumption. **Flagged for user confirmation
before S2 build.**

---

## 11. FIELD OBSERVATION — real-footprint audit (S7 figures), 2026-07-05 — the shape-adaptive approach is TOO COMPLEX; direction pending

> **Trigger.** The S7 figures (`Reference_plans_real/`) ran the engine on **real** OSM footprints for the first
> time (S1–S6 were synthetic boxes/L/U/T/O). The user reviewed them and rejected the result: apartments show
> *"too complicated corridors, or highly simple ones"*; offices are *"distorted"*; e.g. HighriseApartment
> `la_centre way/427817489` has *"too much unnecessary corridors."* User's proposal for offices: *"can't we
> apply simple core-perimeter … perimeter for every facade and inner zones are core."* User's summary: *"our
> current approach is too complicated right now … I'm not sure if this layout generator works correctly … I
> will think about and return to you."* This section is the manager's honest audit; **it locks no new design**
> — the redesign direction is the user's call, pending.

**What was audited.** All office + apartment figures viewed directly by the manager; the full `_manifest.csv`
(123 rows) tallied by engine-assigned form. The engine's `generation_status_note` form is the panel caption.

### 11.1 Engine-assigned form distribution (123 real footprints)

| assigned form | n | manager verdict on real footprints |
|---|---|---|
| `one_zone_per_floor (degraded)` | 37 | honest fallback — but a **featureless blob**, no interior info |
| `multi_band` (concentric core+perim) | 15 | **GOOD when it renders a clean donut** (perimeter ring + 1 core); **BROKEN** when it emits a floating corridor cross-mesh (e.g. LargeOffice `austin_urban relation/5682408`) |
| `functional_split` + `_dominant` | 22 | retail/restaurant/supermarket family — not the focus of this audit |
| `centerline_split` | 10 | **mostly ABSURD** — diagonal/triangulated cuts, sliver fans (e.g. SmallOffice `nyc_urban relation/3263309`, LargeOffice `la_urban relation/6353541`) |
| `standard_core_perim` | 10 | **over-complex** — courtyard-ring with the core fragmented into small scattered blobs rather than one coherent core |
| `double_loaded` / `single_loaded` (bar) | 12 | **GOOD** — clean central corridor + two apartment rows; plausible reference plans |
| `wing_fallback_degenerate` | 5 | **BROKEN** — venetian-blind horizontal stripes (e.g. MediumOffice `la_centre way/427817661`, SmallOffice `la_urban way/402279965`); the name itself admits it is a degenerate fallback, yet it is captioned as a legitimate "assigned form" |
| `connected_spine` (multi-wing corridor) | 4 | **ABSURD on real footprints** — corridor MESH/grid (e.g. MidriseApartment `la_urban relation/6356862`; HighriseApartment `la_centre way/427817489`); this is exactly the *"too many corridors"* the user flagged |
| `one_zone_per_floor (engine error)` | 3 | the T19-ROBUST GEOSException footprints — blob |
| `wing_fallback_narrow` | 3 | school narrow-wing fallback |
| `assembly_block` | 2 | school |

### 11.2 Findings

1. **~33 % of panels (40/123 = degraded + engine-error) carry ZERO interior information.** For a *reference
   plan catalogue* that alone is a poor result — a third of real buildings get a blank box.
2. **The plausible plans all come from the SIMPLE, shape-robust recipes:** the double-/single-loaded **single
   bar** (corridor family) and the clean concentric **core+perimeter donut** (`multi_band`, office/tower
   family). These match the user's own intuition and look like real floor plans.
3. **The implausible plans all come from the SHAPE-ADAPTIVE decomposition machinery:** `connected_spine`
   (multi-wing corridor spine — the T16b work), `centerline_split` + `_decompose_wings`, and the
   `wing_fallback_*` paths. On real, non-orthogonal, ragged OSM footprints this machinery over-fragments into
   corridor grids, triangulated slivers, and striped fallbacks. It was validated on clean synthetic L/U/T/O
   shapes (S1–S6) where it looked fine — **the same synthetic-vs-live blind spot that bit T12** — but real
   footprints are irregular enough that it rarely produces a coherent plan and, when it "succeeds," is often
   visually broken.
4. **`wing_fallback_degenerate` / `wing_fallback_narrow` are failures dressed as forms.** They should read as
   degrade outcomes (like `one_zone_per_floor (degraded)`), not as first-class assigned layouts.

### 11.3 Emerging direction (user's proposal — RECORDED AS HYPOTHESIS, NOT ADOPTED)

The user's instinct — *"highly simple layouts … simple core-perimeter"* — is supported by this audit. The
candidate simplification to decide on:

- **Office / tower family →** one **whole-footprint core+perimeter**: offset the true footprint inward by a
  fixed perimeter depth (≈4.57 m, the DOE value already cited in §5.2), split the perimeter ring at the
  facades (N/S/E/W), remainder = single core. This is exactly the good `multi_band` donut, made THE recipe.
  **Retire** `centerline_split`, `_decompose_wings`, and the `wing_fallback_*` paths for offices.
- **Corridor family (apartments/hotels) →** one **single double-loaded bar** along the footprint long axis
  (the good `double_loaded` case); if the footprint is too irregular for a clean bar, **degrade to per-floor**
  rather than emitting a corridor mesh. **Retire** `connected_spine` multi-wing meshing for production plans.
- **Net trade:** fewer, simpler, more *plausible* zones over geometrically-exhaustive decomposition — the same
  **correctness > coverage** ruling already accepted at T12 / T13a. Very likely raises the per-floor degrade
  rate, which is acceptable if the non-degraded plans are trustworthy.

### 11.4 What is NOT being changed now

No code, no `MODULE_SPECS`, no dispatch, no simulation. The four viz-only families added S1–S5c remain gated
OUT of production (`zoning.py:29`). **This is an observation + a pending redesign decision only.** The user
will return with the chosen direction; the manager will then write a plan and dispatch execution. Until then
the S7 figures stand as the evidence that the shape-adaptive engine is too complex for real footprints.

### 11.5 SECOND-PASS review + STOP decision (user, 2026-07-05) — ARC PARKED to `docs_TODO`

The user reviewed three more S7 figures (FullServiceRestaurant, HighriseApartment, LargeOffice) and decided to
**stop the layoutgenerator task and rebuild its root later**. Verbatim: *"currently, I would like to change the
root of the layoutgenerator. I think in future we can return to here. So I would like to stop this task so far …
in future we will return."* Final per-family notes captured before parking:

- **FullServiceRestaurant — "works okay", two concrete fixes wanted (future):**
  1. **Every variation must carry both Dining AND Kitchen zones.** Several panels lack one or both — the
     `per-floor (degraded)` blobs show no program at all, and some `functional_split` panels render only a single
     zone. The restaurant recipe should always emit the Dining+Kitchen pair.
  2. **`nyc_rural way/270445758`** renders a **tiny Kitchen** zone that should really be **Dining** — the
     kitchen split is undersized for the footprint; the small offcut should read as dining area, not kitchen.
- **HighriseApartment — mostly poor division:** `la_urban way/402264140` *"looks okay"*, but the **rest do not
  have good division** — most real high-rise footprints degrade to featureless `per-floor` blobs (6/10 real-form
  vs 4/10 degrade on this archetype) or emit the `connected_spine` corridor mesh. The apartment division is not
  trustworthy on real footprints.
- **LargeOffice — none plausible:** *"none of them easy to implement."* The office panels (`centerline_split`
  sliver fans, `multi_band` cross-mesh artifacts, `standard_core_perim` scattered-blob cores) are all
  architecturally impractical; the user does not accept any of them as a usable reference plan.

**Decision & disposition.** The engine needs a **root-level redesign** (per §11.3's simple core-perimeter /
single-bar direction, or a fresh approach the user chooses on return), not incremental patching. The task is
**PARKED**, not cancelled: the entire `layoutgenerator/` working folder is moved from `docs_ACTIVE/…/` to
`docs/docs_TODO/layoutgenerator/` on 2026-07-05 for a future revisit. **Production is untouched** — the whole
arc has always been design/viz-only, `zoning.py`'s room-level path stays opt-in (`resolution_mode == "zone"`,
default pipeline never calls it), and the T19-ROBUST always-degrade-never-crash guard remains in place, so
parking the docs changes no shipped behaviour. Nothing to un-wire.
