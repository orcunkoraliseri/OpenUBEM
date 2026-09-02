# Director prompt — floor planning for the eleven building groups

**Opened 2026-09-01, last updated 2026-09-02 (morning: `DD-1`…`DD-8` ratified by the owner, plan `eu21-t07` opened and running — see §5 top). Self-contained:
nothing else has to be read to start.** Read §4 before touching anything, §5 for where the work stands and what is next.
Replaces `previous/DIRECTOR_PROMPT_european_locations.md` and
`previous/PROMPT_EU-18c_viewer_idf_plans_2026-09-01.md`.

---

## 0. The job

Every residential building in the four districts must get a floor plan: **thermal zones (flats) plus one
circulation zone**, cut from its own footprint. The owner's pipeline, in his words:

> *filter: dividing building floor plans into the group · assign floor type: based on the floor groups
> assign floor types with circulation and thermal zones · reach 95 % floor assignment for all residential
> buildings*

Work **one group at a time**. Never rebuild the whole fleet to test an idea — the owner has said so twice:
*"every time we are trying to edit all buildings and we are consuming a lot of resources."*

The visible deliverable is one file:

**`docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_2026-09-01.html`**

Eleven sheets, one per group (an 11th, `CORRIDOR_RECTANGLE`, was carved out of `RECTANGLE`'s old aspect-ratio
band since 2026-09-01 — see below). Each sheet shows the same building twice — the plate as surveyed, then
the same plate cut into flats and a core — beside the filter that selects the group, the plate statistics,
the circulation rule, the zone count and the scheme name. This document *is* the specification. When a rule
changes, the sheet changes with it. Since 2026-09-01 it has five companion test sheets in `rules/tests/`
(`TEST_01`…`TEST_05`, §5) that run the same rules over 550 real plates and grade every one.

---

## 1. The eleven groups

Classifier: first match wins, terminal bucket last (`scripts/eu20_morphology_atlas.py:204-229`,
mirrored in `scripts/eu21/01_cut_group_plans.py:cls()`). Counts measured over the four districts,
2026-09-01.

| # | Group key | Shown as | Filter | Buildings | With a plan today | Missing at 95 % |
|---|---|---|---|---|---|---|
| 01 | `COURTYARD` | Courtyard | `n_interior_rings >= 1` | 362 | 47 | 297 |
| 02 | `SLIVER` | Sliver | `min_rot_rect_w_m < 8.0` | 637 | 216 | 390 |
| 03 | `SQUARE` | Square | `rect >= 0.90`, aspect < 1.5 | 220 | 64 | 145 |
| 04 | `RECTANGLE` | Rectangle | `rect >= 0.90`, 1.5 ≤ aspect < 2.0 | 109 | 23 | 81 |
| 05 | `CORRIDOR_RECTANGLE` | Corridor rectangle | `rect >= 0.90`, 2.0 ≤ aspect < 3.0 | 94 | 28 | 62 |
| 06 | `SLAB` | Slab | `rect >= 0.90`, aspect ≥ 3.0 | 28 | 10 | 17 |
| 07 | `TRIANGLE` | Triangle or trapezoid | ≤ 3 long edges, no reflex corner | 54 | 18 | 34 |
| 08 | `TRAPEZOID` | Parallelogram | no reflex corner, `rect < 0.90` | 87 | 20 | 63 |
| 09 | `L_SHAPE` | L shape | 1 reflex corner | 259 | 34 | 213 |
| 10 | `U_OR_T_SHAPE` | U or T shape | 2 reflex corners | 269 | 39 | 217 |
| 11 | `COMPLEX_MULTI_WING` | Complex multi-wing | everything else | 425 | 42 | 362 |
| | | | **2,544** | **541 (21 %)** | **1,876** |

Districts: `ES-MAD-BERRUGUETE` 961 · `FR-LYO-HAUTCOEURPENTES` 297 · `GB-LDN-STDUNSTANS` 82 ·
`IT-BOL-GALVANI2` 1,204. The 95 % bar is **2,417** buildings.

Display names 07 and 08 were corrected by the owner and are **display only** — the on-disk keys
`TRIANGLE` and `TRAPEZOID` never change. Measured: only 8 of the 54 "triangles" are carried by two long
edges, and all 87 "trapezoids" have four long edges with 65 having exactly four vertices.

`CORRIDOR_RECTANGLE` and `SLAB` are drawn at 3 dwellings/floor, not their own true per-floor median of 2 —
`dwelling_count == 2` is a plain bisection in the engine with no corridor at all
(`openubem/geometry/european_residential.py:1209-1213`), so drawing either group at its real median would
never show the `i_shape_linear_gallery` corridor scheme their own sheet describes. 3 is the lowest count
where the corridor route activates and both groups have real buildings at n=3
(`MIN_DRAW_TO_SHOW_SCHEME`, `scripts/eu21/01_cut_group_plans.py`).

---

## 2. The floor-plan law — `D-EU-64`, ruled by the owner 2026-09-01

> *"generally circulation or core area is in the center … keeping the centered one as core zone and adding
> the other core zones inside the flats, it is highly possible … if there are extra spaces adding to the
> thermal zones (flats)."*

1. **One circulation zone per plate, and one only.** It is the interior piece — the one that does not run
   along the outer wall.
2. **Every other pocket goes into the flat it adjoins**, chosen by largest shared area. A corner recess is
   usable room, not a second staircase.
3. **No unassigned space.** Flats + core = footprint. Coverage is checked and must read ≥ 99.9 %.
4. **The drawn flat count must match the claimed flat count.** Fragments are welded until a sheet that
   says three flats draws `F1…F3`.
5. `SLIVER` is the one exception: zero circulation zones is correct there — direct street entry, a private
   stair inside each dwelling.
6. **A thermal zone is one connected room, not a room plus a tail.** Added by the owner 2026-09-01:
   *"no every zone needs to be single zone. this divided space under the building can belong to the closest
   zone of F3."* Where a cut leaves a flat as two lobes joined by a neck, the smaller lobe goes to the
   neighbouring flat it shares the most wall with. Tested by eroding each flat by 0.75 m: if the result
   falls into two pieces, the flat is a snake and must be split. `unsnake()` in `02_…py`.
7. **The core takes only what is corridor-shaped.** Added by the owner 2026-09-01: *"we have some
   unwanted narrow zone which can be added to the corridor."* A pocket may be folded into the core only if
   all three hold — it is narrower than 1.2 m; it is a ribbon *along* the core (its mean width over the wall
   it shares with the core is under 0.90 m); and it does not widen the core's band (the smallest rectangle
   the core fits in grows by no more than 2.5 × the pocket's own area). A ribbon down one side passes; the
   block across the end of a corridor fails the third test, because it widens that rectangle over the
   corridor's whole length — tens of m² of box for one m² of pocket, which is how a 1.80 m band ends up
   drawn with a wide head. Everything else goes to a flat. `fold_narrow_to_core()`, `close_gaps()` in
   `02_…py`; `CORE_GROWTH_CAP` (1.35) is a backstop against a runaway, not the discriminator.
8. **The wall between two flats is one straight line, wall to wall.** Added by the owner 2026-09-01:
   *"look we have some unwanted edges."* The cut is a design decision, and a designer draws it straight;
   the 0.20 m wavefront that grows the flats leaves it with a dogleg or two where the two wavefronts met.
   Each neighbouring pair is re-cut by the straight line through the two ends of the wall they share, on
   that pair's own union so nothing else on the plate moves and the core is stepped around, not through.
   Refused — and the drawn wall kept — when the wall genuinely bends around a wing (over 2.5 m off the
   line), is under 1.5 m long, would move more than 20 % of the smaller flat, or leaves either side as more
   than one room. `straight_cuts()` in `02_…py`.
9. **The outer wall is surveyed and is never redrawn.** Straightening, de-kinking and simplification apply
   to cuts *between* zones only. Whatever each zone held within 0.35 m of the footprint boundary is put back
   afterwards, and no vertex on that boundary is ever dropped. A jagged outer wall in a sheet is the
   building, not an artefact. Shaving one corner off it also opens a wedge along the wall that comes back,
   welded onto one flat, as a hairline spike reaching across its neighbours.

10. **No zone encloses another — every zone is one simple outline.** Added by the owner 2026-09-01:
    *"you know that energyplus requires simple geometries, please solve these, simplify."* A zone floor is a
    single polygon: there is no object for a floor with a hole in it, and no plan draws one. Two causes, both
    now closed. (a) Every pass reserved a 1 mm collar around the core (`sbuf(core, 0.001)`), so no flat ever
    reached it; the ring of gap that left is **one connected pocket**, and `close_gaps()` welded it whole to
    the nearest flat — which then closed around the core through a hairline neck. **Nine of the eleven
    plates carried a flat with the core as a hole**, invisible in the drawing except as the extra edge beside
    the core that the owner kept pointing at. The collar is gone; flats are cut against the core exactly.
    (b) A pocket that runs past more than one flat is now **shared out between them** by wavefront
    (`_share()`), never handed whole. Where a ring is genuine — the courtyard gallery around the void —
    `open_rings()` cuts it open on the side that costs the least circulation and hands that side to the flat
    that holds its wall, and only if the piece actually touches that flat.
11. **The party wall is one line across the plate, not one line per pair.** Where one flat faces two others
    (a T-junction), the two halves of that wall are cut by **one shared line**; cutting each pair on its own
    line is exactly what leaves the two halves at slightly different heights, which is the step still visible
    beside the core after clause 8. `straight_cuts()` now tries each flat against all its collinear
    neighbours together first, and only then pair by pair.

Two GEOS traps sit under 10 and 11 and are worth knowing before touching this file. `unary_union()` over
zones that share an exact edge can **drop one of them whole** and still report the result valid — a flat
that simply vanishes, or a pocket that replaces the flat it was being welded onto; `fuse()` adds shapes one
at a time and checks the area after each. And where two zones were cut separately their boundaries can
differ by a fraction of a millimetre, so the union comes back as two pieces that merely touch and the weld
drops one; `join()` bridges that crack with a 2 cm morphological close on square joins, then de-needles the
points it bridged with.

Measured after 6–11 (2026-09-01), all eleven groups: **no zone with a hole and no zone enclosing another**
(against nine plates before), zero snakes, zero zone-to-zone overlap, coverage 99.98–100.01 %, every
party wall a single straight line (worst deviation 0.46 m, on a 4.9 m wall), filament loss under 0.01 m² on
any plate, **4 to 21 points per zone and 16 to 53 per plate** — `SLAB` comes out as four clean
quadrilaterals. Circulation share: Courtyard 8.0 % · Sliver 9.0 · Square 9.0 · Rectangle 9.0 ·
Corridor 12.9 · Slab 16.3 · Triangle 9.0 · Trapezoid 9.0 · L 7.6 · U/T 6.9 · Complex 6.3.

**Where this stands:** the law is applied in the *document*, as a post-pass
(`scripts/eu21/02_one_core_per_plate.py`). **The engine still emits the extra pockets.** Closing that gap
— making `openubem/geometry/european_residential.py` produce one core directly — is the next real task and
has not been ordered yet. Say so plainly rather than implying the engine already does it.

Measured effect of the law on the drawn plates: cores 2 → 1 on groups 09, 10 and 11 (`L_SHAPE`,
`U_OR_T_SHAPE`, `COMPLEX_MULTI_WING`); circulation falls from 23 % / 31 % / 36 % of the plate to
**8 % / 7 % / 6 %**, in line with the ~9 % the regular grids give.

A second, separate artefact was in the *shape* of those boundaries, not their count: `absorb()`'s
discrete 0.20 m wavefront growth left short staircases of centimetre-scale zig-zags where two flats met,
and `simplify()` alone couldn't clear the worst of them without cutting real area from a shape built of
many real, closely-spaced vertices (the courtyard gallery ring's arc-like void). Fixed 2026-09-01 with
`straighten()` (a guarded, per-flat/per-core `simplify()`, falls back to the unsimplified shape if it
would cost more than 1 % of that shape's own area) plus `dekink()` (removes one vertex at a time — a point
with at least one edge under 0.5 m is dropped only if it changes that polygon's own area by less than
0.3 m²), both in `scripts/eu21/02_one_core_per_plate.py`. Verified: a strict scan for the true
multi-point zig-zag signature (both adjoining edges under 0.5 m) now returns zero across all eleven
groups' flats and cores, every group still ≥ 99.98 % plate coverage, no flat/flat or flat/core overlap
over 0.02 m². Detail and the dead ends tried (a global `simplify()` tolerance large enough to clear the
worst kink cost Courtyard 8 points of coverage) are in `DEBUG_REFERENCES_european_locations.md`.

---

## 3. How to rebuild the document, and the tests

Four scripts in `scripts/eu21/`, always run from the repo root with the project interpreter
(`.venv\Scripts\python.exe`, `PYTHONIOENCODING=utf-8` — a bare `python` on this machine is the Windows Store stub):

```
.venv\Scripts\python.exe scripts\eu21\01_cut_group_plans.py       # picks one real building per group, cuts it with the engine
.venv\Scripts\python.exe scripts\eu21\02_one_core_per_plate.py    # applies the D-EU-64 law; prints coverage per group
.venv\Scripts\python.exe scripts\eu21\03_build_rules_html.py      # writes the eleven-sheet HTML into rules/
.venv\Scripts\python.exe scripts\eu21\04_group_tests.py --test N  # N = 1..5 or all; rebuilds rules/tests/TEST_0N_*.html + EU-21/rules_tests/test_0N.json
```

**Re-run discipline.** `01` and `02` are **not run as scripts any more**: `02` is not idempotent on its own output
(it reads `circulation` as bare rings and writes ring-sets) and `scripts/eu21/group_plans.json` on disk is already
post-`02`. `04` imports their functions (`options()`, `apply_law()`) and never calls their `main()`. `03` regenerates
the rules document from `group_plans.json` and its `SPEC` dict — run it only when a sheet's content changes, with a
before/after check of the HTML (last run once, in the cap-12 task). `04` is the only script run routinely: each
`--test N` runs in the foreground for minutes and overwrites that test's HTML and JSON, so earlier results survive
only if renamed first (`test_0N.cap8.json` and `test_0N.cap12.json` exist for that reason). **No generated HTML is
ever hand-edited** — the rules document only through `03`, the test sheets only through `04`.

`01` and `02` share `scripts/eu21/group_plans.json`. `03` holds the per-group content in its `SPEC` dict —
that dict is the right-hand column of every sheet, and it is where a rule change gets written. Since
2026-09-01 that column is **a seven-step flow, not prose** (owner: *"turn into flowchart with bullet format
rather than like a text … this flowchart format will help us when we apply them to the coding"*): 1 Match ·
2 Read the plate · 3 Place the circulation first · 4 Cut the flats · 5 Absorb what is left over · 6 Close —
accept only if · 7 Scheme. Steps 5 and 6 are module-level constants `ABSORB` and `CLOSE` shared by all
eleven sheets — they are the law, not the group — and render marked as shared. Each group supplies
`match` / `plate` / `core` / `cut` / `scheme` as **lists of one-line bullets**; keep them one line each. The page CSS
is read from the frozen 2026-08-28 document so the two can never drift apart.

Inputs already on disk: `openubem/outputs/eu_evidence/EU-20/morphology_census.csv` (2,544 rows, one per
building) and `representatives.json` (one chosen building per group).
Engine entry point: `generate_european_ruled_storey_layout` at
`openubem/geometry/european_residential.py:1083`. The density table `_DENSITY_GRID_TABLE` (`:180-194`, count →
grid, ceiling `RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 12` at `:31`) and the column-merge helper `_merge_grid_cells`
(`:206`) feed `generate_european_grid_layout` (`:291`). Four proposed schemes sit further down at `:1478`
(courtyard perimeter band), `:1557` (row-house depth bands), `:1608` (wing spine decomposition), `:1736`
(regularized envelope grid). A fifth, `courtyard_gallery_ring` — a 1.80 m deck-access gallery round the void — is
drawn on sheet 01 but exists **only in `01_cut_group_plans.py`**, not in the engine, and is captioned as such.

**Bookkeeping per task.** One plan doc per task in `implementation/` (`PLAN_eu21-<slug>-<date>.md`, sections as
CLAUDE.md prescribes, fresh Sonnet executors, checkpoints signed by the director). The two on disk —
`PLAN_eu21-rules-tests-2026-09-01.md` and `PLAN_eu21-cap12-2026-09-01.md` — are COMPLETE; a new task gets a new
plan. Every solved error goes into `debugs/DEBUG_REFERENCES_european_locations.md` (18 `[OPEN]` bullets there on
2026-09-01, `LAW_GEOSException` among them). At every checkpoint update §5 of this file, the EU board artifact
(`https://claude.ai/code/artifact/080bec44-ec13-4669-94db-8bb4a7a6763f`, republished in place, never as a new page)
and the arc memory pointer. Wider arc state (districts, weather, simulations) lives in
`docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v4.md` and is not needed for this sub-arc.

---

## 4. Rules that are not negotiable

- **No EnergyPlus run of any kind without the owner's own sentence** (`D-EU-55`). A relayed "continue", an
  approved plan or a signed checkpoint is not permission. Writing geometry is fine; running it is not.
- **Never edit `rules/RULES_dwelling_layout_scheme_2026-08-28.html`.** It is frozen. Read its CSS, nothing
  more.
- **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.** The working tree
  is dirty and belongs to the owner.
- **Never write into `openubem/outputs/eu_evidence/EU-17/` or `EU-20/`.** Frozen. New evidence goes to `EU-21/`
  (test evidence to `EU-21/rules_tests/`).
- **No `.py` files under `docs/`, ever.** Scripts live in `scripts/`.
- **Create nothing that was not asked for** — no extra docs, boards, reports or "helpful extras".
- `circulation_pct_of_plate` in the engine is a **fraction, not a percentage**. Any displayed share must be
  computed as `circulation_area_m2 / area_m2 * 100`.
- Executors are **fresh Sonnet sessions**, `model: "sonnet"` passed explicitly, one dispatch per task, the
  exact commands in the prompt. The director plans and audits; it does not write feature code.
- Every error solved must be registered in
  `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` before the task closes.
- **A measurement task does not fix what it measures.** A plate that is refused, fails a check or raises is the
  finding: draw it, mark it, count it. No constant tuned, no building swapped, no filter added — a remedy is its
  own task under its own owner sentence.
- **Density rulings are taken, not reopened:** the ceiling is 12 flats per floor (`D-EU-65`), 9 and 10 are cut on
  the `6x2` grid with column merges (`D-EU-66`), above 12 refuses by design. Numbers the owner gives for a test
  (3 / 6 / 9 / 12) are flats per floor, imposed on every group to see whether the group algorithms hold.

---

## 5. What is done, and what is next

### 🔴 Night session 2026-09-01 → 02 — CLOSED at CP-5, nothing running; resume here in the morning

**Owner's sentences, verbatim (2026-09-01 evening):** *"so i have checked the test files and i saw that there are lots of
fails, unwanted curves & edges. here is the informaiton, courtyards needs cores and these cores will connect to each other.
secondly, this is our main template file [`rules/RULES_dwelling_layout_groups_2026-09-01.html`] and please follow these
types in order to generate these [`rules/tests/TEST_01…TEST_05`], do not touch any this [main file], and we need basic
thermal zones for flats. so now , i do not have time to check every test files, please you do it, i will sleep, no more
asking questions, and please for every action you update this prompt … so i can continue in the morning with a fresh
session from where we left of."* — then *"continue to the end, no more question. update the test files if necessary."*

**Rulings taken from those words:** `D-EU-67` courtyard circulation = several stair cores joined to each other (one
connected zone) · `D-EU-68` flats are basic thermal zones (straight cuts, no post-pass welding). Remedy authorised
("please you do it"); rules document **not** touched (`03` not run); test sheets regenerated. Next free ids now
`D-EU-69` / `FINDING 225`.

**Plan:** `implementation/PLAN_eu21-direct-cutters-2026-09-01.md` — a direct per-group cutter
(`scripts/eu21/05_group_cutters.py`, NEW) replaces engine call + `apply_law()` post-pass **in the tests only**: circulation
placed first, flats cut by straight lines in the plate's own frame, clipped to the surveyed footprint; `finish()` is a
three-rule clean-up. T01 convex groups + SLIVER · T02 courtyard (corner cores + open gallery, `D-EU-67`) · T03 wings
(L/U/T/complex: reflex-edge decomposition, corridor tree) · T04 rewire `04_group_tests.py`, add `C8` access (report
only), regenerate the five sheets (old JSONs kept as `test_0N.postpass.json`). T05a–d remedies (CP-2 findings). Director decisions DD-1…DD-8 pending the
owner's ratification are listed in the plan §4 (notably: TRIANGLE/TRAPEZOID on the convex cutter; k ≥ 5 as
`ceil(k/M)×M` columns with a corridor instead of `6x2`; arm-length refusal replaced by a corridor into the arm).

**Status log (director updates this list after every action):**
- 22:15 — defects inspected on rendered PNGs (tests 01/04/05, all groups): post-pass zig-zags, `6x2` strips at 9–12,
  L/U/complex refusing 112 of 150, courtyard without cores, end flats with no core access. Plan written.
- 22:20 — T01 dispatched to a fresh Sonnet (CP-1 after it).
- 22:31 — CP-1 passed. T01 done: `scripts/eu21/05_group_cutters.py` (454 lines), 63/63 assertions, the only
  refusals are `SLIVER` at k ≥ 5 (`BAND_LT_3M`), seven `EU-21/cutter_demo/demo_<GROUP>.png` viewed — straight cuts
  only, one core bump per corridor, no zig-zag. Two robustness fixes inside `finish()` (`_safe_union`, second R1 pass
  after snapping) recorded in plan §8 T01 and `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1.
  Observation, not yet a task: with `DOUBLE_LOADED_MIN_DEPTH = 12.0` a plate 11.9 m deep goes single-loaded and its
  flats become strips (TRAPEZOID rep, k = 6: 2.3 m wide). Candidate `DD-6` = choose M ∈ {1, 2} by the smaller
  max aspect ratio, refuse `BAND_LT_3M` under 3 m. Decide after the CP-3 contact sheets.
- 22:32 — T02 + T03 dispatched to one fresh Sonnet (same file, so sequential; CP-2 after T03).
- 23:25 — CP-2 passed with findings. T02 + T03 done: cutter now 1180 lines, all four demo PNGs drawn, circulation is
  one Polygon everywhere, no staircase edge. Courtyard cores exist and are joined by the ring (`D-EU-67` met).
  Defects seen on the representatives, to be measured on the 550 real plates before remedy (T05, after CP-3):
  (a) wings: an arm with a single flat still gets a full-length corridor → L k=2 circulation 58 %, U/T 21–30 %,
  COMPLEX 36–49 %; (b) wings: a narrow arm (< 4.8 m) with 2+ flats leaves 1–2 m strips; (c) COMPLEX rep refuses
  k = 9, 12 with `WING_TREE_FAILED` ("structural minimum 13" for 7 wings — minimum should be 7); (d) courtyard rep:
  perimeter-parametrised cuts give strip and wedge flats on a deep irregular block, and k = 3 draws 21.9 %
  circulation (a wing swallowed). Nothing changed yet.
- 23:27 — T04 dispatched to a fresh Sonnet (rewire the tests, 550 plates, 55 contact sheets; CP-3 after it).
- 23:40 — T05a–T05d written into the plan (§6) with three new director decisions, pending your ratification:
  `DD-6` loading by aspect + 3 m floor on every flat; `DD-7` a void under 6 m is a light well, cut by the exterior's
  group with the void on a party wall (23 of 34 test courtyards are light wells); `DD-8` wing corridors reach only
  the cuts they serve, one-flat arms get a stub. Dispatch waits for CP-3 (same file as the running T04 import).
- 23:45 — CP-3 passed. T04 done: tests run the direct cutter (no `apply_law()`), `C8` access chip added, five
  `rules/tests/TEST_0N_*.html` regenerated, 55 contact sheets in `EU-21/cutter_demo/test0N_<GROUP>.png`, old results
  kept as `rules_tests/test_0N.postpass.json`. Tally 550 plates: 62 refused · 488 drawn · 411 pass · 71 fail ·
  6 errors (was 183 · 316 · 242 · 74 · 51). Clean: RECTANGLE, CORRIDOR_RECTANGLE, TRAPEZOID 50/50 pass; SQUARE 49,
  TRIANGLE 48, SLIVER 38 + 12 honest `BAND_LT_3M`. Still weak: COURTYARD 4 pass / 27 fail / 19 refused (light wells),
  L 27 pass, U/T 32, COMPLEX 21 (over-long corridors, C6 facade, C5 points). 6 errors = 3 cutter bugs, registered
  `[OPEN]`, fixed in T05d. Contact sheets confirm the CP-2 diagnosis; T05a–e dispatched next.
- 23:50 — T05a–T05e dispatched to one fresh Sonnet (order a, b, c, d bugs, e re-measure; CP-4 after e).
- 23:58 — `TEST_01` sheet screenshot checked: renders, lede names the cutter and `D-EU-67`/`D-EU-68`, `C8` chip
  present. One stale card string ("the engine returned a scheme") handed to T05e. Arc memory + index updated.
- 00:10 (2026-09-02) — CP-4 passed. T05a–e done: cutter 1375 lines, 0 errors. Tally 550 plates: 71 refused ·
  479 drawn · 424 pass · 55 fail · 0 errors (CP-3 62 · 488 · 411 · 71 · 6; pre-remedy 183 · 316 · 242 · 74 · 51).
  50/50 pass: SQUARE, RECTANGLE, TRIANGLE, TRAPEZOID; CORRIDOR_RECTANGLE 46 + 4 `BAND_LT_3M`; SLIVER 38 + 12;
  SLAB 43; L 31 pass / 14 refused; U/T 30 / 7; COMPLEX 21 pass / 20 fail; COURTYARD 15 pass / 13 fail / 22 refused
  (14 light-well buildings rerouted to their exterior's group). Contact sheets viewed: grids and spines clean;
  residual defects = 0.30 m hairline connectors in wings/courtyards, 1 m gallery strips on two narrow true
  courtyards. Findings from the executor kept in plan §8 T05b/T05c (TRAPEZOID nominal 3.19 m vs drawn 2.46 m;
  COMPLEX rep k=3 connector loop non-convergence; light-well rep → COMPLEX refused by the 8-piece cap).
- 00:15 — T06a (corridor-wide connectors, stubs grow first), T06b (3 m floor on gallery sectors), T06c (re-measure)
  written into the plan and dispatched to one fresh Sonnet; CP-5 after T06c.
- 00:25 — EU board republished in place with the night section and the CP-4 tally (label "Night 09-01 direct
  cutters CP-4"); republish once more after CP-5.
- 00:30 — CP-5 passed, night closed. T06a–c done: cutter 1427 lines; connectors are corridor-wide (no 0.30 m
  hairline anywhere), gallery sectors carry the 3 m floor. Final tally 550 plates: **68 refused · 482 drawn ·
  432 pass · 50 fail · 0 errors** (pre-remedy 183 · 316 · 242 · 74 · 51). Per group (pass/fail/refused): SQUARE,
  RECTANGLE, TRIANGLE, TRAPEZOID 50/0/0 · CORRIDOR_RECTANGLE 46/0/4 · SLAB 43/4/3 · SLIVER 38/0/12 · L 35/6/9 ·
  U/T 32/10/8 · COMPLEX 23/21/6 · COURTYARD 15/9/26. Five sheets + 55 contact sheets + 11 demo PNGs regenerated;
  board republished; arc memory updated. No agent running, no job anywhere.
- 2026-09-02 morning — owner ratified `DD-1`…`DD-8`, ordered the `03` run and `T07` (a)(b)(c) with
  *"lets go by recommendation"*, then *"continuer jusqu'a la fin, vas-y"* (run to the end without stopping for
  approval between tasks). Baseline re-derived from the five `test_0N.json` by the director, not copied.
  Plan `implementation/PLAN_eu21-t07-2026-09-02.md` written; T01–T03 dispatched to one fresh Sonnet, CP-1 after T03.

**Decided by the owner 2026-09-02 — all three, in his own words *"lets go by recommendation"*, then
*"continuer jusqu'a la fin, vas-y"*:**
1. `DD-1`…`DD-8` **ratified**. They are in force for the tests and are no longer director decisions.
2. The `03` run is **ordered** — the RULES document text follows the code (plan `eu21-t07` T05).
3. `T07` **(a), (b), (c) ordered**; (d) stays as an honest refusal; (e) is folded into the T04 re-measure.

**Plan in force: `implementation/PLAN_eu21-t07-2026-09-02.md`** — T01 `T07`(b) piece cap + convex fallback ·
T02 `T07`(a) junction rectangle · T03 `T07`(c) band ends on the cut · CP-1 · T04 re-measure + five sheets · CP-2 ·
T05 the `03` run · CP-3. One new director decision inside it, `DD-9` (the RULES document's **figures** are redrawn
from the cutter too, into a separate `group_plans_cutter.json`; `group_plans.json` untouched) — flagged, not ratified.
Baseline re-derived by the director from the five `test_0N.json` before starting: **432 PASS · 50 FAIL · 68 REFUSED**;
failing checks `C4` 22 · `C6` 18 · `C5` 17 · `C2` 5; refusals `BAND_LT_3M` 30 · `WING_TREE_FAILED` 29 ·
`FLAT_ENCLOSES_ZONE` 6 · `CELL_EMPTY` 3 (plan §3, per-group breakdown there).

**`T07` candidates (as diagnosed on the CP-5 contact sheets; (a)(b)(c) are now T01–T03 above):** (a) wing junctions — the union of a root core
and angled child stubs gives a stepped circulation outline (`test05_U_OR_T_SHAPE.png` 29235, `test05_COMPLEX…` 31075,
`way/432864641`): one junction rectangle in the root frame, stubs trimmed to it; (b) light-well plates whose exterior
has > 8 reflex vertices refuse `WING_TREE_FAILED` (12 of the 26 courtyard refusals) — raise the piece cap or fall
back to the convex cutter on the exterior's MRR frame; (c) `C4` lobes on U/T (7) and COMPLEX (9): a flat cell wraps
a corridor end — end the band at the cut, not `+ LANDING`, when the next cell is a through-flat; (d) COURTYARD true
rings at k ≥ 9 refuse `BAND_LT_3M` (3 plates) — honest, leave; (e) contact-sheet titles lost the scheme name in T06c
(cosmetic, scratch evidence only).

**Where the RULES document now lags the code (owner to order a `03` run):** sheet 01 step 3 (cores + open gallery),
sheet 07 step 3–4 (incentre wedges → convex cutter), sheet 10 step 3 (arm refusal → corridor), sheets 03–06 step 4 at
k ≥ 5 (`ceil(k/M)×M` + corridor). Nothing in the HTML was changed.

**Done.** The eleven groups exist and are counted (`CORRIDOR_RECTANGLE` split out of `RECTANGLE` on
2026-09-01, see §1). The document exists, has been reviewed group by group by the owner, and now obeys the
`D-EU-64` law on all eleven sheets: one core each, 99.9 %+ coverage, both figures the same building, honest
names on 07 and 08, `CORRIDOR_RECTANGLE`/`SLAB` drawn at a real n=3 so their own corridor scheme actually
shows, and the flat-boundary zig-zag artefact cleared everywhere (§2). As of the last pass every zone on
every sheet is a **simple polygon** — no hole, nothing enclosed, 4–21 points — so each one writes
straight out as a single floor surface.

**Done — the rules tests (2026-09-01, `implementation/PLAN_eu21-rules-tests-2026-09-01.md`, CP-1/CP-2 signed).**
Five companion sheets in `rules/tests/` (`TEST_01`…`TEST_05`), built by `scripts/eu21/04_group_tests.py --test N`
(JSON in `openubem/outputs/eu_evidence/EU-21/rules_tests/`), run the same `options()` + `apply_law()` over **550 real
sampled plates** — 3 / 5 / 10 buildings per group at their own flats per floor (tests 01/03/05) and 3 / 5 buildings
per group at an imposed 3 / 6 / 9 / 12 (tests 02/04) — and check every plate against seven written rules `C1`–`C7`
(coverage, one core, drawn = claimed, one room per flat and no overlap, simple outline, 2.50 m facade, circulation
share as a report). First measured under the 8-flat ceiling: 264 refused · 286 drawn (207 pass all six, 47 fail) ·
32 raise inside `apply_law()`. **Current, after `D-EU-65` + `D-EU-66`, same 550 plates:** 183 refused · 316 drawn,
of which **242 pass all six**, 74 fail at least one, **51 raise inside `apply_law()`**. What the tests say — none of
it fixed, by the plan's rule 7:

- `L_SHAPE_DECOMPOSITION_FAILED` *is* the refusal: 139 of 183 (38 of the 42 at a building's own count). It takes
  `L_SHAPE` 40, `COMPLEX_MULTI_WING` 38 and `U_OR_T_SHAPE` 34 of 50 plates each — and also census
  `CORRIDOR_RECTANGLE` 10, `RECTANGLE` 8, `SLAB` 7, `SQUARE` 2, because the census `cls()` and the engine's own
  classifier disagree on shape.
- The `D-EU-64` post-pass is not robust on real plates: `LAW_GEOSException` (shapely `TopologyException`) on 51 of
  550, every group hit (`RECTANGLE` 10, `CORRIDOR_RECTANGLE` 7), registered `[OPEN]` in
  `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1. It grew from 32 to 51 only because 30 more plates now reach
  the post-pass.
- Among the 74 failing plates the broken rules are `C5` simple outline 45, `C4` one room / no overlap 32, `C2` one
  core 9, `C6` facade 7, `C3` drawn = claimed 5 (a plate can break more than one). The five `C3` plates are
  `courtyard_gallery_ring` drawing more flats than declared.
- The other refusals: `PARTITION_AUDIT_FAILED` 23, `NARROW_FOOTPRINT_LT_8M` 16 (`SLIVER` at imposed counts),
  `INTERIOR_RING_COURTYARD_UNFOLD_FAILED` 5; above-ceiling refusals 0.
- Pass-all-six of 50 per group: `TRAPEZOID` 33 · `SQUARE` 32 · `TRIANGLE` 32 · `CORRIDOR_RECTANGLE` 27 ·
  `RECTANGLE` 26 · `SLIVER` 25 · `COURTYARD` 24 · `SLAB` 21 · `COMPLEX_MULTI_WING` 8 · `L_SHAPE` 7 ·
  `U_OR_T_SHAPE` 7. At a building's own count (18 each): `TRAPEZOID` / `TRIANGLE` 17, `SLIVER` 15, `SQUARE` 14,
  `RECTANGLE` 13, `CORRIDOR_RECTANGLE` / `COURTYARD` 12, `SLAB` 8, `L_SHAPE` 7, `U_OR_T_SHAPE` 6,
  `COMPLEX_MULTI_WING` 3. `TRAPEZOID` is no longer the only group without a law error; every group has at least one.

**Done — density, `D-EU-65` and `D-EU-66` (2026-09-01, `implementation/PLAN_eu21-cap12-2026-09-01.md`, CP-1/CP-2/CP-3
signed, COMPLETE).** `D-EU-65`, owner's words: *"ok I made these numbers to test if our algorithms for groups are
working for them also"* · *"ok raise the cap and run 9 and 12 as well, let's go"* — the ruled-grid ceiling is 12 flats
per floor, not 8 (`RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 12`, refusal token
`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12` derived from it, rules document regenerated by `03`). Under the 8 cap the
9- and 12-flat rows of tests 02/04 had measured the ceiling, not the algorithms. `D-EU-66`, owner's sentence:
*"let's go if you recommend"* — 9 and 10 flats are cut on the even `6x2` grid with column merges (3 merges for 9, 2 for
10, as 7 is served from `4x2`; `_DENSITY_GRID_TABLE` rows at `european_residential.py:190-191`); the odd `5x2` grid
left the table because with a core carved its middle column is narrower than the core and the partition audit fails
(debug bullet closed). Results at 9 and 12 (tests 02 + 04, 176 plates): **39 pass all six · 36 fail · 81 refused ·
20 law errors**; drawn 39 of 88 at 9 and 36 of 88 at 12 (under the 8 cap: 0 non-Courtyard plates drew there). What
draws at 9 + 12: `ruled_grid_6x2` 37, `i_shape_linear_gallery` 23, `courtyard_gallery_ring` 13, other 2. Pass-all-six
at 9 in test 04: `CORRIDOR_RECTANGLE` 4, `SQUARE` 3, `TRIANGLE` 2, `COURTYARD` / `TRAPEZOID` / `U_OR_T_SHAPE` 1,
`RECTANGLE` 0 (2 of 5 draw and fail), `SLAB` 0; at 12: `SLAB` 3, `SQUARE` 2, `TRIANGLE` 2, `RECTANGLE` 1. `L_SHAPE`,
`COMPLEX_MULTI_WING` draw 0 at both (`L_SHAPE_DECOMPOSITION_FAILED`), `SLIVER` 0 (`NARROW_FOOTPRINT_LT_8M`). Census
at k ≥ 9: 75 buildings by ceiling of dwellings ÷ storeys, 25 of them above 12 — those stay refused by design. Earlier
results kept as `EU-21/rules_tests/test_0N.cap8.json` (8 cap) and `test_0N.cap12.json` (12 cap, `5x2` era). No owner
call open. The test findings above are unnumbered; next free `D-EU-69` / `FINDING 225` (`D-EU-67`/`68` taken tonight, see §5 top).

**No twelfth group is needed to reach 95 %, and the census says so.** Measured 2026-09-01 over all 2,544
rows: what predicts whether a building gets a real plan is **not its shape but how many flats it must be cut
into**. Ruled share by dwellings per floor — k=1 **50.1 %** (719 buildings) · k=2 **23.0 %** · k=3 **4.4 %**
· k=4 **3.2 %** · k=6–8 **6.8 %** · k≥9 **0.0 %** (66 buildings). Hold k at 1 and every group lands between
37 % and 64 %; hold k at ≥2 and every group collapses to 4–23 %. Plate area tells the same story through k
(<50 m² 50.6 % → >800 m² 10.1 %). So a new filter row can only re-label buildings that already fail for a
reason no filter addresses; the gap is in the **schemes' capacity to cut k ≥ 2 flats and survive the IDF
writer**, which is items 1 and 4 below. The one split that is geometrically real but does not change the
odds is `COURTYARD` with two or more voids (98 buildings, median 585 m², 13.3 % ruled against 12.9 % for
single-void) — the gallery rule assumes one void, so it needs a stated answer, not its own row.

**The focus for the next session, stated by the owner 2026-09-01:** *"our only focus still visual outputs,
defining algorithms for groups based on the rules we are applying."* So: keep working the eleven sheets and
the plans they draw, and turn each group's flow into an **algorithm that can be coded** — the seven-step
flow on each sheet plus the shared law of §2 is the specification, and steps 5 and 6 are already the same
for all eleven. What is still per-group and still prose-shaped is step 3 (where the circulation goes) and
step 4 (how the flats are cut); those two are what needs to become an algorithm per group, in the same
bullet form, checkable against the drawn plate. Do not start the engine rewrite, the schemes' adoption or
any simulation while that is the focus.

**Open, in the order the owner cares about:**

1. **Write the one-core law into the engine** so the fleet gets what the document promises.
2. **Close the gap to 95 %** group by group, biggest first: `COMPLEX_MULTI_WING` (362 missing),
   `SLIVER` (390), `COURTYARD` (297), `U_OR_T_SHAPE` (217), `L_SHAPE` (213).
3. **Decide on `courtyard_gallery_ring` (S5)** — drawn, not in the engine, waiting on the owner.
4. **939 buildings are demoted at IDF-writing time**, not by morphology: `ZeroDivisionError` in
   `geomeppy/geom/vectors.py:105` and `IndexError` at `openubem/idf/surfaces.py:863-864`. A better floor
   plan does not fix these; they are a separate defect and must not be counted as a morphology failure.
5. **Publish the plans into `plans3D/`** under the existing `PLANS_<district>.html` filenames — geometry
   only, no energy results.

**Measured by the tests, not ordered by anyone** — candidates for the owner to rank, none started:

- `LAW_GEOSException` in the post-pass, 51 of 550 plates (`[OPEN]`, debug refs ch. 1) — the law cannot go into the
  engine (item 1) while its own post-pass raises on one plate in eleven.
- `L_SHAPE_DECOMPOSITION_FAILED` on census rectangles, slabs and squares (27 plates) — the two classifiers disagree.
- `C5` / `C4` failures (45 / 32 plates) — the post-pass still leaves a non-simple outline or two rooms in one flat
  on real plates, the same artefacts §2 closed on the eleven representatives.
- `courtyard_gallery_ring` drawing more flats than declared (5 plates), and `COURTYARD` with two or more voids
  (98 buildings) needing a stated gallery rule — both wait on item 3.

Next free ids: `D-EU-69` / `FINDING 225`. Every owner ruling is quoted verbatim in this file and in the plan it
governs; a relayed or paraphrased sentence is not a ruling.

**Done means:** 2,417 of 2,544 residential buildings carry a floor plan with flats and exactly one
circulation zone, each cut by a rule that is written on its group's sheet, and the rules generalise to
countries not yet in the database.
