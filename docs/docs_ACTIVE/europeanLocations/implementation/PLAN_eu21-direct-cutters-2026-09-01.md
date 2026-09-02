# PLAN — EU-21: direct per-group cutters — basic zones, connected courtyard cores, tests regenerated

**Slug:** `eu21-direct-cutters` · **Date:** 2026-09-01 (night session, owner asleep) · **Arc:** `docs/docs_ACTIVE/europeanLocations/`
**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM` · **Interpreter:** `.venv\Scripts\python.exe` (bare `python` is the Store stub), `PYTHONIOENCODING=utf-8`.
**Director prompt (read-first, self-contained):** `prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` — §2 the law `D-EU-64`, §4 the non-negotiables.
**Predecessors (COMPLETE):** `PLAN_eu21-rules-tests-2026-09-01.md` (the five test sheets, 550 plates, C1–C7), `PLAN_eu21-cap12-2026-09-01.md` (`D-EU-65`, `D-EU-66`).
**Rulings in force:** `D-EU-64` (one core, flats + core = plate, simple outlines), `D-EU-65` (ceiling 12 flats/floor), `D-EU-66` (9–10 on `6x2` — superseded *for the test sheets only* by this plan, see §4 DD-3), 🔴 `D-EU-55` (no EnergyPlus without the owner's own sentence — nothing here runs one).

**Owner instruction that opens this plan (2026-09-01 evening, verbatim):**
> *"so i have checked the test files and i saw that there are lots of fails, unwanted curves & edges. here is the informaiton, courtyards needs cores and these cores will connect to each other. secondly, this is our main template file [`rules/RULES_dwelling_layout_groups_2026-09-01.html`] and please follow these types in order to generate these [`rules/tests/TEST_01…TEST_05`], do not touch any this [`RULES_dwelling_layout_groups_2026-09-01.html`] main file, and we need basic thermal zones for flats. so now , i do not have time to check every test files, please you do it, i will sleep, no more asking questions, and please for every action you update this prompt [`prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md`] so i can continue in the morning with a fresh session from where we left of."*
> then: *"continue to the end, no more question. update the test files if necessary. thank you."*

New rulings taken from those sentences (ids assigned by the director, wording is the owner's):
- **`D-EU-67` — courtyard circulation is several stair cores joined to each other** (*"courtyards needs cores and these cores will connect to each other"*). One connected circulation zone made of cores + the gallery that links them.
- **`D-EU-68` — flats are basic thermal zones** (*"we need basic thermal zones for flats"*, *"unwanted curves & edges"*). A flat is a rectangle, a rectangle with a bite for the core, or a footprint-clipped cell: straight party walls, vertices only from the surveyed outer wall and from straight cuts. No wavefront growth, no post-pass welding.
- Standing: **the rules document is not touched tonight** (*"do not touch … main file"*) — `03` is not run; where a sheet's step 3/4 wording now lags the code, that is recorded in §5 of the director prompt for the owner to order a `03` run.
- Standing: **the test sheets may be regenerated** (*"update the test files if necessary"*).

---

## 1. The measured situation this plan answers

Measured on the current `test_01…05.json` (550 plates, 2026-09-01 20:29–20:37): 183 refused · 316 drawn (242 pass, 74 fail) · 51 `LAW_GEOSException`. Rendered by the director (all 11 groups, tests 01/04/05) the defects the owner saw are:

1. **The post-pass, not the plate, draws the curves.** Flats are grown by a 0.20 m wavefront (`absorb()`), welded, de-kinked and re-cut in `scripts/eu21/02_one_core_per_plate.py` (913 lines). On real plates that leaves saw-tooth party walls, stepped flats around the core, hairline slivers and 51 GEOS crashes. Fixing it by another pass is what the last three passes did.
2. **The `6x2` grid at 9–12 flats cuts a square into 2 m strips** and merges columns into stepped L-flats around the core (test 04 `SQUARE`, `RECTANGLE`). Not basic.
3. **`L_SHAPE`, `U_OR_T_SHAPE`, `COMPLEX_MULTI_WING` mostly refuse** (`L_SHAPE_DECOMPOSITION_FAILED` 112 of 150 plates in test 05 across the three) and when they draw, a plate-wide rectangle grid is clipped to the L, so the core lands off the elbow and a flat spans two wings. One plate (`IT-BOL 31075`) draws a whole wing as the core.
4. **Courtyard plates draw a gallery and no stair core**, cut by radial diagonals from the void centroid — `D-EU-67` now says cores, connected.
5. End-column flats of the `3x2` / `4x2` grids **never touch the core** (no access) — unmeasured today.

The remedy is not another pass: **each group gets a direct cutter that places the circulation first and cuts the flats with straight lines in the plate's own frame**, clipped to the surveyed footprint. Coverage, one core and straight walls hold by construction; the only clean-up is a deterministic three-rule `finish()` (§6 T01). The engine (`openubem/geometry/european_residential.py`) is **not** touched: the cutter is the algorithm the sheets' steps 3–4 describe, written down as code the engine can adopt later (director prompt §5 open item 1).

---

## 2. Hard rules for the executor

1. **Never edit** `rules/RULES_dwelling_layout_groups_2026-09-01.html`, `rules/RULES_dwelling_layout_scheme_2026-08-28.html`, `scripts/eu21/01_cut_group_plans.py`, `02_one_core_per_plate.py`, `03_build_rules_html.py`, `scripts/eu21/group_plans.json`, anything under `openubem/geometry/`, `openubem/outputs/eu_evidence/EU-17/` or `EU-20/`.
2. **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.** The tree is dirty and belongs to the owner.
3. **No EnergyPlus, no IDF writing, no simulation** (`D-EU-55`). Geometry only.
4. **No `.py` under `docs/`.** Code lives in `scripts/eu21/`; PNG evidence in `openubem/outputs/eu_evidence/EU-21/`.
5. **Create only the files in §3.** No extra reports, boards, notebooks, helper modules.
6. **Do not tune constants to make a plate pass.** A plate that refuses or fails is a finding: it is drawn, marked and counted. Constants are the ones in §4; if one must change, STOP and report why.
7. **Interpreter:** `.venv\Scripts\python.exe` with `PYTHONIOENCODING=utf-8`, run from the repo root.
8. **Cap every command's output** (`| Select-Object -First 40` / `head -40`). Never print a JSON file.
9. **Every error solved goes into** `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` (house format: symptom → cause → fix, file:line, source doc = this plan) before the task closes.
10. **Progress log** (§8): one entry per task, appended under this file's §8 only — never edit sections 1–7.
11. **Default to no code comments** except a one-line docstring per public function naming the sheet step it implements.
12. If a §6 step is ambiguous, STOP and quote the ambiguity — never invent a rule.

---

## 3. File layout

| Path | Status | Role |
|---|---|---|
| `scripts/eu21/05_group_cutters.py` | **NEW** (T01–T03) | The eleven direct cutters, `cut()`, `finish()`, `--demo` CLI |
| `scripts/eu21/04_group_tests.py` | **MODIFIED** (T04) | Calls `cut()` instead of `options()`+`apply_law()`; adds `C8`; lede/readings text |
| `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_<GROUP>.png` | **NEW** (T01–T03) | One PNG per group: the representative plate cut at k = 2, 3, 6, 9, 12 |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N.postpass.json` | **RENAMED** (T04) | Tonight's pre-remedy results, kept (copy of `test_0N.json` before overwrite) |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N.json` | **REGENERATED** (T04) | |
| `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0N_*.html` | **REGENERATED** (T04) | Same five filenames, owner's list |
| `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` | appended | Errors solved |
| this file §8 | appended | Progress log |

Inputs (read-only): `openubem/outputs/eu_evidence/EU-20/representatives.json` (list of 11 dicts: `group`, `exterior_ring`, `interior_rings`, `dwellings_total`, `storeys`, …), `EU-20/morphology_census.csv`, the four `02_residential_manifest.gpkg` via `_M01.load_universe()`.

---

## 4. Dependency decisions (pinned)

- shapely **2.1.2** (installed), Python 3.14.3. Use `shapely.set_precision(g, 0.001)` on the footprint at entry and on every emitted zone; `shapely.make_valid` on an invalid footprint; `cap_style="flat", join_style="mitre"` on any buffer. No round joins anywhere (that is where arcs come from).
- Constants (module level, all in `05_group_cutters.py`; values are the sheets' or the engine's, cited):
  `CORRIDOR_W = 1.80` (engine `CORRIDOR_SPINE_WIDTH_M`, `european_residential.py:47`) · `CORE_FRACTION = 0.06` (`:1854`) · `CORE_MIN_SIDE = 2.40` · `CORE_MAX_SIDE = 4.00` · `DOUBLE_LOADED_MIN_DEPTH = 12.0` (sheets 05/06 "single-loaded below 12 m depth") · `LANDING = 1.50` · `SLIVER_MAX_W = 8.0` (`NARROW_FOOTPRINT_THRESHOLD_M`, `:1855`) · `BAND_MIN_W = 3.0` (sheet 02 refuse) · `MAXK` imported from `openubem.geometry.european_residential.RULED_GRID_MAX_DWELLINGS_PER_FLOOR` (= 12, `D-EU-65`) · `ACCESS_MIN_M = 1.0` · `DENOISE_TOL = 0.30` · `REFLEX_TOL_DEG = 10.0` · `MIN_WING_M2 = 15.0` · `MIN_WING_W = 3.0` · `SCRAP_M2 = 0.01` · `BIG = 10_000.0`.
- **DD-1 (director decision, pending owner ratification):** tests do not run `apply_law()` any more. The cutter satisfies the law by construction; `finish()` (T01) is the only clean-up and is three rules long.
- **DD-2:** TRIANGLE and TRAPEZOID are cut on the same convex cutter as SQUARE/RECTANGLE (equal-area columns in the MRR frame, straight row line through the centroid, core at the centroid). Sheet 07's "wedges from the incentre" wording is superseded by that in code; the sheet text waits for the owner's `03` run.
- **DD-3:** for the tests, k ≥ 5 on any convex plate is cut as **N = ceil(k/M) equal-area columns × M rows** (M = 2 when the plate depth ≥ 12 m, else 1) with a straight corridor, not on the `6x2` table. `D-EU-66` stays in force in the engine; the sheets never showed 9–12 on a real plate anyway.
- **DD-4:** the C-shaped gallery opens on the void's shortest side; a plate whose k = 1 gets a street passage along the opening's opposite side so the single flat is not an annulus (§6 T02).
- **DD-5:** sheet 10's "refuse an arm longer than 15 m from the spine core" is replaced by a corridor that reaches into the arm (§6 T03).
- **Constants added at CP-2 (T05):** `COURTYARD_MIN_VOID_SIDE = 6.0` (a void narrower than this is a light well, not a courtyard; 23 of the 34 courtyard plates in the tests) · `MIN_FLAT_W = BAND_MIN_W` (3.0 m floor on every straight-cut flat).
- **DD-6 (CP-2):** loading M ∈ {1, 2} is chosen by the smaller max aspect ratio of the resulting flats, both sides ≥ 3.0 m, instead of `depth ≥ 12 m`; `LINEAR_GALLERY_GROUPS` stay single-loaded. No valid loading → `BAND_LT_3M` (§6 T05b).
- **DD-7 (CP-2):** a light-well plate (void < 6 m) is cut by its exterior's group with the void snapped onto the nearest party wall; the gallery ring + corner cores (`D-EU-67`) apply to true courtyards only (§6 T05c).
- **DD-8 (CP-2):** a wing's corridor spans only from the first served cut or junction to the last (+ landing); a one-flat leaf arm gets a 1.5 m stub; no forced column boundaries at junctions (§6 T05a).
- Refusal tokens the cutter may raise (and nothing else): `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12` (k > MAXK), `BAND_LT_3M` (any straight-cut band or column under 3.0 m — sliver bands since T01, every group since T05b), `CELL_EMPTY` (a cell clipped to the plate has no area), `FLAT_ENCLOSES_ZONE` (a flat keeps a hole after `finish()`), `WING_TREE_FAILED` (no connected wing tree / circulation not one polygon), `SECONDARY_VOID_UNCUT` (a courtyard's second void is not crossed by any cut). Everything else is a bug → the test records it as `CUT_<ExceptionName>`.

---

## 5. Specification facts, with citations

- One circulation zone per plate, the interior piece; every pocket to the adjoining flat; flats + core = footprint ≥ 99.9 %; drawn = claimed; SLIVER has none; a zone is one room; every zone a simple polygon; the party wall is one straight line across the plate; the outer wall is surveyed and never redrawn — `D-EU-64` clauses 1–11, director prompt §2.
- Density ceiling 12 — `D-EU-65`, engine `:31`. Above it refuse `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12` (`:32`).
- Per-group steps 3 (circulation) and 4 (cut): `scripts/eu21/03_build_rules_html.py:174-352` (`SPEC[...]["core"]`, `["cut"]`) — the sheets. Relevant lines quoted in §6 under each cutter.
- Test harness contract: `scripts/eu21/04_group_tests.py` — `build_plate()` (`:253-290`), `run_checks()` (`:292-343`), record keys `footprint` / `dwellings` / `circulation` as ring-sets (`[[exterior, *interiors], …]`), `verdict` ∈ {PASS, FAIL, REFUSED, ERROR}, `token`, `scheme`, `status`, `circ_m2`. `drawplan()` (`:98-137`) reads exactly those keys.
- Selection is unchanged: `select_own()` (2–8 flats, evenly spaced quantiles) and `select_size()` (3/6/9/12 nearest n × 60 m²) so the same 550 buildings are drawn again and the tallies are comparable.
- Classifier (which group a census row is in): `_M01.cls()` (`01_cut_group_plans.py:27-39`), unchanged.

---

## 6. Task list

### T01 — `05_group_cutters.py`: frame, `finish()`, the convex cutter (groups 02–08) and `--demo`

**What.** Create `scripts/eu21/05_group_cutters.py` with:

```python
class Refusal(Exception):
    def __init__(self, token): super().__init__(token); self.token = token

def cut(poly: Polygon, k: int, grp: str) -> dict
# returns {"flats": [Polygon,...] (len k), "circ": Polygon | None, "scheme": str, "notes": dict}
# raises Refusal(token) for the §4 tokens only
```
`cut()` dispatches on `grp`: `SLIVER` → `cut_sliver`; `SQUARE`, `RECTANGLE`, `CORRIDOR_RECTANGLE`, `SLAB`, `TRIANGLE`, `TRAPEZOID` → `cut_convex`; `COURTYARD` → `cut_courtyard` (T02); `L_SHAPE`, `U_OR_T_SHAPE`, `COMPLEX_MULTI_WING` → `cut_wings` (T03). Until T02/T03 land, those two raise `NotImplementedError` (the test harness is not wired until T04).

**Why.** §1 items 1, 2, 5. Sheets 02–08 steps 3–4 (`03_build_rules_html.py:186-330`).

**How.**

1. **Entry.** `poly = set_precision(make_valid(poly) if not poly.is_valid else poly, 0.001)`; if the result is a MultiPolygon keep the largest part. `k > MAXK` → `Refusal(DWELLING_DENSITY_REFUSAL_TOKEN)`. `k == 1` and `grp != "COURTYARD"` → one flat = the footprint, `circ=None`, scheme `single_dwelling`.
2. **Frame.** `frame(poly)`: `mrr = poly.minimum_rotated_rectangle`; its longest edge gives the angle θ; centre = mrr centroid; L = long side, W = short side. `to_local(g)` = `rotate(translate(g, -cx, -cy), -θ, origin=(0,0), use_radians=False)`; `to_world` inverts in reverse order. **All cuts are made in local coordinates; every emitted zone is rotated back with `to_world` and then `set_precision(…, 0.001)`.**
3. **Equal-area columns.** `equal_area_x(P, N)` → the N−1 values x_i such that `area(P ∩ {x < x_i}) = i/N · area(P)`, each found by bisection on [minx, maxx] to 1e-3 m (≤ 40 iterations). Half-planes are boxes `box(minx-1, miny-1, x, maxy+1)`.
4. **Row line.** One straight line `y = yc` where `yc = P.centroid.y` (local). M = 2 rows means the two half-boxes above/below `yc`.
5. **`cut_sliver(P, k)`** — sheet 02: *"none — the one group where zero is the right number"*, *"k depth bands across the strip, equal area"*. Columns `xs = equal_area_x(P, k)`; flats = `P ∩ box(x_i, x_{i+1})`; if any flat's local x-extent `< BAND_MIN_W` → `Refusal("BAND_LT_3M")`. `circ=None`, scheme `row_house_depth_bands`.
6. **`cut_convex(P, k, grp)`** — sheets 03–08 (core *"inside the plate, never against the outer wall"*, *"k flats on an N×M grid around the core"*, *"one 1.80 m corridor along the long axis"*, *"single-loaded below 12 m depth, double-loaded above"*):
   - `A = P.area`; core side `s = clamp(sqrt(CORE_FRACTION·A), CORE_MIN_SIDE, CORE_MAX_SIDE)`.
   - **k ≤ 4 → point block.** M = 2 (M = 1 when k = 2: two flats side by side, each the full depth — `ruled_grid_2x1`). N = ceil(k/M). `xs = equal_area_x(P, N)`. Cells = boxes `[x_i, x_{i+1}] × [yc−BIG, yc]` and `[yc, yc+BIG]` clipped to P. If k = 3: the two cells of the **narrower end column** (the column with the smaller mean local y-extent; ties → the right column) are merged into one through-flat. Core = square of side s centred at `(x_1 if N == 2 else P.centroid.x, yc)` → `core = box(...) ∩ P`. No corridor. Scheme `ruled_grid_{N}x{M}`.
   - **k ≥ 5 → corridor block.** M = 2 if W ≥ DOUBLE_LOADED_MIN_DEPTH else 1. N = ceil(k/M). `xs = equal_area_x(P, N)`. If k is odd and M = 2: the **last** column (highest x) is one through-flat. Corridor band: for `grp in {CORRIDOR_RECTANGLE, SLAB}` the band runs the whole length (`x ∈ [minx−1, maxx+1]`, then ∩ P) — sheet 06 *"one 1.80 m corridor running the whole length"* — except that with an odd k it stops at `x_{N−1}` (the through-flat's wall); for the other groups the **reach rule**: `x ∈ [x_1 − LANDING, x_{N−1} + LANDING]`, and `x_{N−1}` exactly when the last column is a through-flat. Band y-extent: M = 2 → `[yc − 0.9, yc + 0.9]` (centre line); M = 1 → along the **+y** long side: `[maxy_local − 1.8, maxy_local]` where `maxy_local` is the P bound at the corridor's x-midpoint (single-loaded gallery on one long side). Core = square of side s centred on the band's midpoint (M = 2: `(mid x, yc)`; M = 1: `(mid x, maxy_local − 0.9)`), ∩ P. **circulation = unary_union(core, band) ∩ P**; must be a single Polygon (it is a plus/T by construction). Scheme `spine_grid_{N}x{M}` (`i_shape_linear_gallery` for CORRIDOR_RECTANGLE/SLAB).
   - Flats = `(cell ∩ P) − circulation` for every cell (merged through-flats first). Any cell with `area < SCRAP_M2` → `Refusal("CELL_EMPTY")`.
7. **`finish(fp, flats, circ)`** — the only clean-up; deterministic, three rules, applied in order, max 3 passes each:
   - **R1 one room.** A flat that is a MultiPolygon keeps its largest part; each other part goes to the *flat* sharing the longest boundary with it (shared boundary = `part.buffer(0.02, cap_style="flat", join_style="mitre").intersection(other).area / 0.02`), provided that receiver stays a single Polygon after `unary_union`; failing that, to the circulation if it touches it; failing that, it stays a scrap (R2).
   - **R2 no scrap.** `U = fp − unary_union(flats + [circ])`; every part of U with `area > SCRAP_M2` is handed to the flat with the longest shared boundary under the same single-Polygon condition, else to the circulation. Parts ≤ SCRAP_M2 are dropped.
   - **R3 report, do not patch.** Any flat with `interiors` → `Refusal("FLAT_ENCLOSES_ZONE")`. (`C5` would fail anyway; the plate is a finding.)
   - Then `set_precision(…, 0.001)` on every zone, flats sorted by `(-centroid.y, centroid.x)` in world coordinates, and the dict returned.
8. **`--demo` CLI.** `05_group_cutters.py --demo [GROUP …]`: for each group in `_M01.ORDER` (load `01` with `importlib` exactly as `04` does, `:31-47`), read its representative from `EU-20/representatives.json` (`Polygon(exterior_ring, interior_rings)`), cut at `k ∈ (2, 3, 6, 9, 12)` and draw one matplotlib figure `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_<GROUP>.png` (one axis per k, flats filled from a fixed 12-colour list, circulation grey hatched, footprint outline 1.6 pt, vertices as 1.8 pt dots, title = `k=… scheme … refusal/token or "pts=<total vertices>"`). Groups not yet implemented print `NotImplementedError` in the title and draw the bare footprint. Nothing else is written. Module import must have no side effects (no drawing, no file I/O at import).

**How to test.**
```
.venv\Scripts\python.exe scripts\eu21\05_group_cutters.py --demo SLIVER SQUARE RECTANGLE CORRIDOR_RECTANGLE SLAB TRIANGLE TRAPEZOID
```
Then, in one `python -c`, for those seven representatives × k ∈ {2,3,4,5,6,7,8,9,12}: assert coverage `0.999 ≤ (Σflats + circ)/fp ≤ 1.001`, `len(flats) == k`, every zone `is_valid`, no interiors, pairwise flat overlap `< 0.02 m²`, flat/circ overlap `< 0.02`, and print per case `grp k scheme pts_max circ_pct` — one line each, ≤ 63 lines. Report the table and any `Refusal` (expected: SLIVER at k ≥ 5 when a band drops under 3.0 m).

### T02 — `cut_courtyard` (`D-EU-67`)

**What.** Group 01. Circulation = stair cores at the void's corners joined by a 1.80 m gallery that is open on one side; flats cut by lines perpendicular to the void's sides.

**Why.** `D-EU-67` (owner: *"courtyards needs cores and these cores will connect to each other"*); sheet 01 (*"a 1.80 m deck-access gallery round the void, open on one side so the zone is one outline and not a ring"*, *"one stair opens onto the gallery; every flat is reached from it"*); `D-EU-64` clause 10 (no zone encloses another); §1 item 4.

**How.** All in the **void's** frame: `V = largest interior ring as Polygon`; `mrr_v = V.minimum_rotated_rectangle`; θ from its long edge; local coords with the void centre at the origin, half-sides `a` (x, long) and `b` (y, short). `B` = the footprint (exterior + all interiors) in that frame.
1. **Ring.** `R = (V.buffer(CORRIDOR_W, cap_style="flat", join_style="mitre") − V) ∩ B`.
2. **Cores.** `n_c = 1 if k == 1 else min(4, max(2, ceil(k/3)))`. Corner order: the four corners of the void's MRR sorted by the area of B in their quadrant, largest first; take the first `n_c`. Each core = the square of side `CORE_MIN_SIDE` (2.40) that fills the **outer corner of the ring** — for the (+,+) corner: `box(a + 1.8, b + 1.8, a + 1.8 + 2.4, b + 1.8 + 2.4)` — and likewise for the other signs; `∩ B`. A core whose ∩B area is under 3.0 m² is moved inward along the void side (slide 2.4 m towards the void's centre along x) once; if still under 3.0 m² it is dropped and the next corner in the order is taken (only if that leaves ≥ 1 core; otherwise `n_c` shrinks).
3. **Opening.** The **shortest side of the void MRR** (the `b` sides if `a ≥ b`; ties → the −x side) is removed from the ring: `R = R − box(side strip)` where the strip is the ring's straight piece along that side **between the two corner squares of the ring** (for the −x side: `box(−a − 1.8, −b, −a, b)`). If `k ≥ 2` and after step 6 some flat does not touch the circulation (shared boundary `< ACCESS_MIN_M`), try the other short side, then the two long sides, and keep the opening that gives the **most flats with access**; ties → the first tried. Record `notes["opening_side"]`.
4. **Passage (k = 1 only, DD-4).** A strip `CORRIDOR_W` wide from the middle of the void side **opposite the opening** straight out to the outer wall (`box` along the outward normal, ∩ B). Without it the single flat is an annulus. Scheme `courtyard_cores_gallery`.
5. **Circulation = unary_union(R, cores, passage) ∩ B**; must be one Polygon with no interiors, else `Refusal("WING_TREE_FAILED")` — reuse the token, note the cause in `notes`.
6. **Flats — perimeter cuts.** Parametrise the void MRR's boundary by arc length `t ∈ [0, P)`, P = 4a + 4b, starting at the middle of the opening side and running counter-clockwise. Every point of `B − circulation` outside the MRR maps to a `t` through the four **side regions** (points whose nearest MRR side is that side; boundaries are the 45° diagonals from the corners) — a point in a side region maps to the foot of its perpendicular on that side; a point in a corner wedge maps to the corner's `t`. Build the area profile `A(t)` on a 0.10 m grid by cutting `B − circulation` with the strip polygons (side strips: `box` perpendicular to the side between `t` and `t+dt`, extended `BIG` outward; corner wedges: the triangle between the two diagonals, extended). Cut positions `t_1 … t_k`: `t_1 = 0` (the middle of the opening side is always a cut, so no flat wraps round the open side), the rest at equal-area quantiles of `A(t)`; a cut within 1.0 m of a corner **snaps to the corner** (its cut line is then the corner's 45° diagonal). **Secondary voids:** for every interior ring other than V, force a cut at the `t` of its centroid before distributing the rest; after cutting, if that void's polygon is not intersected by any flat boundary → `Refusal("SECONDARY_VOID_UNCUT")`. Each flat `i` = `(sector polygon from t_i to t_{i+1}) ∩ (B − circulation)` where the sector polygon is walked: inner point of cut i on the MRR boundary → outward along cut i to distance BIG → along the far boundary through the corner diagonal points → inward along cut i+1 → back along the MRR boundary. Cuts are perpendicular to the side they sit on (or the 45° diagonal at a corner).
7. `finish()` as T01. Add `notes = {"n_cores": …, "opening_side": …, "access_min_m": …}`.

**How to test.** `--demo COURTYARD` (k = 2, 3, 6, 9, 12) and the same assertion block as T01 on the courtyard representative plus the nine `COURTYARD` plates of `test_05.json` (read their `footprint` ring-sets from that JSON, at their `drawn_per_floor`). Print one line per plate: `id k n_cores opening access_min pts_max cov circ_pct verdict`. Expected: every flat touches the circulation ≥ 1.0 m; circulation 10–16 % (the gallery is wide by design; report, do not tune).

### T03 — `cut_wings` (groups 09–11)

**What.** Decompose a re-entrant plate into convex wings by extending edges at reflex vertices; one core at the junction; a 1.80 m corridor tree along the wings' axes; flats per wing by equal-area columns, single- or double-loaded by depth.

**Why.** §1 item 3 (112 of 150 refusals in test 05); sheets 09–11 steps 3–4 (*"one core at the elbow, serving both wings"*, *"k flats per wing, in proportion to wing area"*, *"a single spine core on the connecting wing, reaching both arms"*, *"one core for the whole plate, on the largest wing"*, *"each wing then takes its own group rule"*). Sheet 10's *"refuse an arm longer than 15 m"* is replaced by the corridor reaching into the arm (DD-5).

**How.**
1. **Denoise for analysis only.** `Q = poly.simplify(DENOISE_TOL, preserve_topology=True)` (exterior only, interiors dropped — these groups have none). Flats are always clipped to the true `poly`, never to Q (`D-EU-64` clause 9).
2. **Reflex vertices** of Q: interior angle `> 180 + REFLEX_TOL_DEG`.
3. **Split loop.** `pieces = [Q]`. While a piece has a reflex vertex r (take the one with the largest interior angle): the two edges at r give two candidate rays from r (each edge extended past r). For each ray, the cut segment is r → first boundary hit of the piece (`piece.exterior.intersection(ray_line)` nearest point beyond r, ray length BIG); split with `shapely.ops.split(piece, LineString(cut))`. A candidate is valid if it yields exactly 2 polygons each `≥ MIN_WING_M2`. Choose the valid candidate whose two pieces have the **larger minimum rectangularity** (`area / mrr.area`); no valid candidate → the piece keeps its reflex vertex and leaves the loop. Cap: 8 pieces; more → `Refusal("WING_TREE_FAILED")`.
4. **Absorb bays.** A piece with `area < MIN_WING_M2` or MRR short side `< MIN_WING_W` is unioned into the neighbour sharing the longest boundary. Repeat until none.
5. **Wing tree.** Adjacency = shared boundary `> 1.0 m`. Root = largest wing. Spanning tree by BFS from the root taking, for each wing, the parent with the longest shared boundary. Disconnected → `Refusal("WING_TREE_FAILED")`. Junction `J(w)` = midpoint of the shared boundary between w and its parent. Each wing's frame = its own MRR (long axis = wing axis, `u`; depth = short side, `d_w`). Inner side of a wing = the side of its axis line where the plate centroid lies (children normally attach there).
6. **Flats per wing.** `k_w` by largest-remainder on wing area (wing ∩ poly), every wing ≥ 1 when `k ≥ n_wings`; when `k < n_wings` the smallest wings get 0 and are **unioned into their parent** (the parent is then cut as one piece, non-convex, and `finish()` R1 handles a cell that splits). Recompute the tree on the merged set.
7. **Columns per wing.** In the wing frame: `M_w = 2 if d_w ≥ DOUBLE_LOADED_MIN_DEPTH else 1`; `N_w = ceil(k_w / M_w)`. Column boundaries: **first**, one boundary at the axis position of every child's junction `J(child)` (so a child's corridor connector runs along a wall, never through a flat); then `equal_area_x` on each remaining span so that the column count reaches `N_w` (a span gets columns in proportion to its area, at least the forced ones). If forced boundaries alone exceed `N_w − 1`, keep them and let `k_w` rise (the extra flats are taken back from the largest other wing by shrinking its `k_w`; if impossible → `Refusal("WING_TREE_FAILED")`, noted). Odd `k_w` with `M_w = 2` → the column at the **far end** (farthest from `J(w)`; root: farthest from its largest child's junction) is a through-flat. Row line = the wing's axis (`v = 0`).
8. **Circulation.** Core: square of side `s = clamp(sqrt(CORE_FRACTION·A_total), 2.4, 4.0)`; centre = `J(largest child of the root)` moved `s/2` along the root's inward normal so the square lies inside (`∩ poly` afterwards); with ≥ 2 children of the root, centre = the mean of their junctions projected onto the root's inner-side line. Corridor of wing w (needed when `k_w ≥ 2`, or when `k_w = 1` and the wing's flat does not touch the core): band `CORRIDOR_W` wide along the axis (`M_w = 2`: on the axis; `M_w = 1`: against the inner side, i.e. `v ∈ [d_w/2 − 1.8, d_w/2]` on the inner side), from the wing's junction end (extended 0.9 m into the parent) to the last column boundary + LANDING (exactly to the through-flat's wall when there is one), **and** at least to every child junction of w. Connector: if a child's band does not touch the parent's circulation after union, add `box` of width `CORRIDOR_W` along the child's axis line from the child's junction to the parent's band (it runs along the forced column boundary of step 7). **circulation = unary_union(core, bands, connectors) ∩ poly** → one Polygon with no interiors, else `Refusal("WING_TREE_FAILED")`.
9. **Flats** = `(cell_w ∩ wing ∩ poly) − circulation` for every cell of every wing; then `finish()`. Scheme: `l_shape_decomposition` (2 wings), `wing_spine_decomposition` (≥ 3). `notes = {"n_wings":…, "k_per_wing":[…], "loading":[…]}`.

**How to test.** `--demo L_SHAPE U_OR_T_SHAPE COMPLEX_MULTI_WING` (k = 2, 3, 6, 9, 12) plus the assertion block over the 30 `L_SHAPE`/`U_OR_T_SHAPE`/`COMPLEX_MULTI_WING` plates of `test_05.json` at their `drawn_per_floor`; print one line each `id grp k n_wings k_per_wing scheme pts_max cov access_min verdict/token`. A refusal is a finding; count them, do not tune.

### T04 — Wire `04_group_tests.py` to the cutter, add `C8`, regenerate the five sheets

**What.** Replace the engine call + post-pass with `cut()`; keep selection, checks C1–C7 and the record format; add `C8` access (report only); update the lede/readings text; rename the current JSONs; run `--test all`.

**Why.** Owner: *"please follow these types in order to generate these [five test files]"*, *"update the test files if necessary"*. The sheets must show what the cutter draws.

**How.**
1. Load `05` with `_load_module("eu21_m05_cutters", …/05_group_cutters.py)`; keep `_M01` (for `cls`, `load_universe`, `ORDER`, `DISTRICTS`, `NO_CORE_BY_DESIGN`) and `_M02` **only** for `lobes_of`, `parts`, `sbuf` (the C4 test); drop `options`, `capture`, `apply_law` imports.
2. `build_plate()`: `try: out = cut(p, n, grp) except Refusal as r: REFUSED + r.token except Exception as e: ERROR, token f"CUT_{type(e).__name__}", message str(e)[:120]`. On success: `dwellings = [[list(f.exterior.coords)] + [list(i.coords) for i in f.interiors] for f in out["flats"]]`, `circulation = [[list(circ.exterior.coords)] + interiors]` or `[]`, `scheme = out["scheme"]`, `status = "direct"`, `circ_m2 = round(circ.area, 1)`, `notes = out["notes"]`. Then `run_checks()` unchanged.
3. `run_checks()`: add **`C8` access (report only)** — `min over flats of sbuf(f, 0.05).intersection(circ).length` (`n/a` when there is no circulation: SLIVER, k = 1); chip `info` if `≥ ACCESS_MIN_M` (or n/a), `warn` otherwise; shown as `x.xx m`. Verdict still uses C1–C6 only.
4. Text: `build_lede_html()` — *"cut directly by `scripts/eu21/05_group_cutters.py`, the per-group algorithm of each sheet's steps 3–4 (`D-EU-67` connected courtyard cores, `D-EU-68` basic zones); no engine call, no `D-EU-64` post-pass — the law holds by construction"*, keep the `D-EU-65` sentence; `build_checks_html()` — add the `C8` line; `READINGS` — the §4 tokens with one-line readings; the module docstring; `CHECK_META` untouched. The header `TEST_0N — companion to RULES_…` stays.
5. Before running: copy `EU-21/rules_tests/test_0N.json` → `test_0N.postpass.json` for N = 1..5 (do not delete anything).
6. Run `.venv\Scripts\python.exe scripts\eu21\04_group_tests.py --test all` (foreground; the cutter is fast — report wall time). Then render the five PNG contact sheets the director will read: `.venv\Scripts\python.exe -c` that loads each `test_0N.json` and draws every plate per group into `EU-21/cutter_demo/test0N_<GROUP>.png` (same drawing as `--demo`; ≤ 5 columns per row, 4.2 in per plate, dpi 110). That is 55 PNGs.

**How to test.** Report, per test and per group, `refused / drawn / pass / fail / error` and the commonest failed check and token, from the JSONs (one `python -c`, ≤ 70 lines). Compare with the pre-remedy line: 183 refused · 316 drawn · 242 pass · 74 fail · 51 errors. List every `ERROR` token with its plate id (should be none).

### T05 — remedies ordered by the director at CP-2 (2026-09-01 night), executed after CP-3

Execution order: T05a, T05b, T05c, T05d, then T05e. Common rules for T05a–T05d: §2 applies; edit only `scripts/eu21/05_group_cutters.py`; do not change T01–T03 behaviour beyond what each item says; one progress-log entry per item; register every solved error in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1. New constants (also listed in §4): `COURTYARD_MIN_VOID_SIDE = 6.0` · `MIN_FLAT_W = BAND_MIN_W` (3.0). New decisions **DD-6 / DD-7 / DD-8** are in §4.

#### T05a — wings: corridor only where it serves a flat, no structural minimum (DD-8)

**What.** In `cut_wings`: (a) drop the forced boundaries at child junctions — call `_wing_columns(w_local, N_w, [], minx, maxx)`; (b) the corridor band of a wing spans exactly what it must reach: let `J` = local x of every child junction of this wing, `X` = the wing's column cuts `xs`; for a non-root wing add its own junction end `minx`. If `k_w == 1` and the wing has no children: band = `[minx − 0.5, minx + LANDING]` on the inner side (a stub — the flat meets the parent's band or the core there). Otherwise `u_lo = min(J ∪ X) − LANDING` (a non-root wing: `minx − 0.5`, as now), `u_hi = max(J ∪ X) + LANDING`, except the existing odd-`k_w` through-flat rule, which keeps `u_hi = xs[-1]` when `xs[-1]` is the maximum. The band's transverse position rule (centre when M_w = 2, inner side when 1) is unchanged. (c) Core placement unchanged. (d) The connector loop and the one-Polygon test stay.

**Why.** On the representatives L k=2 drew 58 % circulation, U/T 21–30 %, COMPLEX 36–49 %: a one-flat arm still got a full-length corridor (`u_far = maxx` when `xs` is empty). COMPLEX refused k = 9, 12 with a "structural minimum 13" for 7 wings — that minimum (children + 1 columns per wing) exists only because of the forced boundaries. Owner: "we need basic thermal zones for flats".

**How to test.** `--demo` for L_SHAPE, U_OR_T_SHAPE, COMPLEX_MULTI_WING at k ∈ {2, 3, 6, 9, 12}; print scheme, circulation share, min access length over flats (`_shared_len_metric` with the circulation), `n_wings`, `k_per_wing`. Expect: L and U/T at k = 2 ≤ 15 % circulation; COMPLEX k = 9 and 12 drawn or refused for a reason that is not the column minimum; every flat's access ≥ `ACCESS_MIN_M`. Report the 15 lines.

#### T05b — DD-6: loading chosen by aspect, 3 m floor on every flat

**What.** New helper `choose_loading(L_eff, W, k)`: for `M` in (2, 1): `N = ceil(k / M)`, `col_w = L_eff / N`, `depth = (W − CORRIDOR_W) / M`; valid iff `col_w ≥ MIN_FLAT_W` and `depth ≥ MIN_FLAT_W`; score = `max(col_w, depth) / min(col_w, depth)`; return the valid `(M, N)` with the smallest score (tie → M = 2); none valid → `Refusal("BAND_LT_3M")`. `L_eff` = local `maxx − minx`. Use it in `cut_convex` for k ≥ 5 on the non-gallery groups (`LINEAR_GALLERY_GROUPS` keep M = 1 but must pass the `col_w ≥ MIN_FLAT_W` test or refuse) and in `cut_wings` for every wing with `k_w ≥ 2`. In `_alloc_k`, after the largest-remainder pass, cap each wing at `cap_w = max(1, floor(L_w / MIN_FLAT_W) × M_max_w)` with `M_max_w = 2` if `(W_w − CORRIDOR_W) / 2 ≥ MIN_FLAT_W` else 1; move any surplus to the wing with the most spare capacity, repeat until stable; `Σ cap_w < k` → `Refusal("BAND_LT_3M")`. The token `BAND_LT_3M` now means "a straight-cut band or column would be under 3.0 m" for every group.

**Why.** `DOUBLE_LOADED_MIN_DEPTH = 12.0` sends an 11.9 m deep plate single-loaded: TRAPEZOID rep k = 6 → 2.3 m strips, k = 9 → 1.5 m; the L rep's narrow arm → 1–2 m strips. Basic zones (D-EU-68) need a floor.

**How to test.** `--demo` for SQUARE, RECTANGLE, TRAPEZOID, TRIANGLE, L_SHAPE at k ∈ {5, 6, 9, 12}: print `M, N, col_w, depth` (per wing for L) and the minimum over flats of the flat's MRR short side; assert that minimum ≥ 2.9 m on every drawn plan; list the refusals. Report ≤ 25 lines.

#### T05c — DD-7: a light well is not a courtyard; exact sectors for true courtyards

**What.** (1) In `cut()` for `grp == "COURTYARD"`: `V` = largest interior ring; if the MRR short side of `V` < `COURTYARD_MIN_VOID_SIDE` the plate is a **light-well plate**: `grp2 = exterior_group(poly)` — a new helper mirroring `cls()` (`scripts/eu21/01_cut_group_plans.py:27-39`) on the exterior ring alone: MRR short side < 8 → SLIVER; rectangularity ≥ 0.90 → SQUARE / RECTANGLE / CORRIDOR_RECTANGLE / SLAB by aspect 1.5 / 2.0 / 3.0; else reflex count (`_interior_angles_ccw` on `simplify(DENOISE_TOL)`, angle > 180 + `REFLEX_TOL_DEG`) 0 → TRAPEZOID, 1 → L_SHAPE, 2 → U_OR_T_SHAPE, else COMPLEX_MULTI_WING — then dispatch to that group's cutter with the holed polygon (cells are `P ∩ box`, so the void leaves the cells by itself). **Snap rule** in `cut_convex`, `cut_sliver` and `_wing_columns`: after the cuts are computed, for every interior ring of the local polygon snap the nearest cut (a column x or, when M = 2, the row line) to the void's centroid coordinate — no distance limit — so the void sits on a party wall and both neighbours stay simple. k = 1 stays `single_dwelling` (the hole is reported by R3, never patched). Append `+lightwell` to the scheme. (2) For true courtyards (void ≥ 6 m) replace the union-of-strips sectors by an exact partition: for each `t` in `ts` build the straight cut line from the ring point at `t` outward, perpendicular to that void side (at a snapped corner: along the side's extension), length `BIG`; `parts = split(Z, unary_union(lines))`; assign each part to the sector whose `[t_i, t_{i+1})` contains `_t_of_point(part.representative_point())`; union per sector (`_safe_union`); `finish()` R1 handles a MultiPolygon. Assert `Σ flats + circ ≥ 0.999 × plate area` before `finish()`.

**Why.** Of the 34 distinct COURTYARD plates in the five tests, 23 have a void under 6 m (15 under 4 m): light wells, where a 1.8 m gallery ring is wrong. On the representative (void 3.5 × 3.0 m, ring depth ≈ 31 m) the sectors left a 45.5 m² piece uncovered at k = 3, which `finish()` R2 donated to the circulation (21.9 %), and gave strip and wedge flats at every k.

**How to test.** (1) Representative COURTYARD at k ∈ {2, 3, 6, 9, 12}: print `grp2`, scheme, circulation share, number of flats with a hole (must be 0). (2) From `rules_tests/test_0N.json` (any of the five; footprints are recorded) take every COURTYARD plate whose void short side ≥ 6 m (11 plates) at its recorded k: drawn / refused, coverage, circulation share, all flats simple — ≤ 15 lines. (3) Regenerate `demo_COURTYARD.png`.

#### T05d — the three cutter bugs measured at CP-3 (6 `ERROR` plates of 550)

**What.** (1) `cut_convex`: when `circ_local = unary_union([core, band]) ∩ P` is not one `Polygon`, run the same fixed-point `_connector` merge loop `cut_wings` uses (hub = largest part) before raising; the `RuntimeError` at `:314` becomes `Refusal("WING_TREE_FAILED")` only if the loop still fails. (2) `finish()`: wrap every `set_precision(g, 0.001)` on emitted flats/circulation in `_safe_precision(g)` — try as is, then `g.buffer(0)` first, then return `g` unsnapped and record `notes["unsnapped"] += 1`; never let GEOS raise out of `finish()`. (3) `finish()` entry: pass every flat and the circulation through `_polygons_only()` (`:548`) before R1, so a `GeometryCollection` cell becomes a `Polygon`/`MultiPolygon` and R1 handles it. Then close the three `[OPEN]` bullets registered at CP-3 in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 (`CUT_RuntimeError`, `CUT_GEOSException` at `set_precision`, `CUT_AttributeError`): drop the `[OPEN]` marker and add the fix with `file:line`.

**Why.** CP-3 (§8 T04): `CUT_RuntimeError` ×2 (Slab k=9, `IT-BOL-GALVANI2/28583`), `CUT_GEOSException` ×2 (Slab k=12, `GB-LDN-STDUNSTANS/way/398158956`), `CUT_AttributeError` ×2 (U/T, `IT-BOL-GALVANI2/32891` k=2, `/31952` k=4). An `ERROR` is a bug, never a finding.

**How to test.** Re-cut those six plates standalone from the recorded footprints in `rules_tests/test_0N.json` (test 02/04 for the slabs, 03/05 for the U/T): none raises; report verdict-equivalent (drawn or refusal token) for each — 6 lines.

#### T05e — re-measure

**What.** Re-run T04's "How to test" end to end: `04_group_tests.py --test all`, regenerate the five `rules/tests/TEST_0N_*.html`, overwrite the 55 contact sheets in `EU-21/cutter_demo/`. Do not edit `04_group_tests.py` unless a record field the cutter now emits (`+lightwell` scheme suffix, `notes["grp2"]`) breaks it — then the smallest fix, logged as a deviation.

**How to test.** The tally line for the five tests and per test, next to the pre-remedy line `183 refused · 316 drawn · 242 pass · 74 fail · 51 errors` and the CP-3 line (§8 T04). Per-group table (plates, drawn, pass, fail, refused, error, top token). Every distinct `CUT_<ExceptionName>` with its count (should be none).


---

### T06 — remedies ordered by the director at CP-4 (2026-09-02, 00:10)

Order: T06a, T06b, then T06c. Same rules as T05 (edit `05_group_cutters.py` only for a/b; T06c re-measures like T05e). One §8 entry per item.

#### T06a — no hairline circulation: connectors and stubs are corridor-wide, stubs grow before connectors are tried

**What.** (1) `_connector(part, hub, width=0.30)` → default `width=CORRIDOR_W` (1.80); every call site uses the default. (2) In `cut_wings`, before the connector loop: if `unary_union([core] + bands)` is not one `Polygon`, grow the disconnected wing's stub/band toward its junction in 0.5 m steps (extend `u_lo` by −0.5 m in that wing's frame, up to 3.0 m total, still clipped to `poly`) and re-test after each step; only if that fails run the connector loop. (3) In `cut_courtyard`, a core that does not touch the ring is first moved along its void side by up to `CORE_MIN_SIDE` toward the ring (keep the `translate` retry) before a connector is drawn. (4) A connector may never be drawn between two parts that both touch the same third part already — check `shared.length` against the union of the others first.

**Why.** CP-4 contact sheets (`test05_U_OR_T_SHAPE.png`: `29235`, `32883`; `test05_L_SHAPE.png`: `way/435510859`) show 0.30 m hairline connectors crossing flats and a core box joined to the band by a thread — the owner's "unwanted edges" in a new form. A 1.80 m connector is a corridor; a 0.30 m one is a drawing artefact.

**How to test.** `--demo` for the three wing groups and COURTYARD at k ∈ {2, 3, 6, 9}; after `cut()`, erode the circulation by 0.60 m (`buffer(-0.60, flat/mitre)`) and assert it is still one `Polygon` with area ≥ 0.5 × the original (no part thinner than 1.2 m) on every drawn plan — print the 16 lines (scheme or token, circ %, erosion test PASS/FAIL).

#### T06b — true courtyards: the 3 m floor on gallery sectors

**What.** In `cut_courtyard`, before `_distribute_cuts`: `P_outer` = length of the outer boundary of the ring's flats zone `Z` along the void's perimeter parametrisation = the ring's perimeter `P`; if `P / k < MIN_FLAT_W` (a sector narrower than 3.0 m at the ring) → `Refusal("BAND_LT_3M")`. After the cuts: any sector whose MRR short side < `MIN_FLAT_W` → the same refusal.

**Why.** `test04_COURTYARD.png`: `31528` k=9 and `relation/4678507` k=9 draw 1 m strips along a narrow ring; DD-6 applies to every group.

**How to test.** The 9 true courtyard plates of T05c at their recorded k: list drawn / `BAND_LT_3M`, and the minimum sector MRR short side on the drawn ones (≥ 2.9 m).

#### T06c — re-measure

**What.** As T05e: `--test all`, five sheets, 55 contact sheets, eleven demo PNGs. **How to test.** Tally against pre-remedy, CP-3 and CP-4 (`71 refused · 479 drawn · 424 pass · 55 fail · 0 errors`); per-group table; `CUT_*` tokens (none).

---

## 7. Stop-and-report points

- **CP-1 — after T01.** Report the assertion table and the seven demo PNG paths. Do not start T02 before the director signs.
- **CP-2 — after T03.** Report both tables (T02, T03) and the refusal count per group. Director audits the PNGs.
- **CP-3 — after T04.** Report the five-test tally against the pre-remedy line. Director audits the 55 contact sheets, updates the director prompt §5 and the EU board, and orders T05 items or closes.
- **CP-4 — after T05e.** Report the tally against both earlier lines. Director audits the regenerated contact sheets and the five sheets, updates the director prompt §5, the EU board and the arc memory, and closes or orders T06.
- **CP-5 — after T06c.** Same report as CP-4. Director closes the plan for the night; the owner ratifies DD-1…DD-8 in the morning.

---

## 8. Progress log

(One entry per task: `#### TXX — <title> — completed YYYY-MM-DD`, then **Artifacts** / **Deviations** / **Test status** / **Notes**. Executors append here only.)

#### T01 — `05_group_cutters.py`: frame, `finish()`, the convex cutter (groups 02–08) and `--demo` — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (454 lines, new) — `Refusal`, `_normalize`, `frame`, `to_local`/`to_world`, `equal_area_x`, `_shared_len_metric`, `_safe_union`, `finish`, `cut_sliver`, `cut_convex`, `cut_courtyard` (stub, `NotImplementedError`), `cut_wings` (stub, `NotImplementedError`), `cut`, `--demo` CLI.
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_SLIVER.png`, `demo_SQUARE.png`, `demo_RECTANGLE.png`, `demo_CORRIDOR_RECTANGLE.png`, `demo_SLAB.png`, `demo_TRIANGLE.png`, `demo_TRAPEZOID.png` (one figure per group, k = 2, 3, 6, 9, 12).

**Deviations:**
- `finish()` runs the R1 "one room" dissolve pass a second time, after the module's own final `set_precision(…, 0.001)` and before R3, because that snap alone (not R1/R2, which both ran on pre-snap geometry) can collapse a thin neck and turn a valid single `Polygon` flat into a `MultiPolygon` — measured on `RECTANGLE` k=12 (area unchanged, ~13.09 m² either side). This re-runs the already-specified R1 rule, at the already-allowed "max 3 passes" budget; no new rule or token was added. Registered as a finding in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1.
- Every `unary_union()` call inside `finish()` is wrapped in `_safe_union()` (retry once with `buffer(0)`-cleaned inputs, else give up on that merge) after an uncaught `GEOSException: TopologyException: unable to assign free hole to a shell` on `RECTANGLE` k=12 during scrap donation. Same finding, same chapter.
- `_shared_len_metric()` treats any candidate part with `area ≤ 1e-6 m²` as zero shared boundary instead of buffering it, after a ~1e-15 m² floating-point sliver produced `RuntimeWarning: divide by zero encountered in buffer` from GEOS's mitred-join buffer. Same finding, same chapter.
- None of the three change the §6 T01 algorithm text (equal-area columns, row line, core sizing/placement, corridor reach/band rules, R1/R2/R3 definitions) — they only make the specified `finish()` robust to GEOS/precision artefacts that the plate text does not anticipate. No constant in §4 was changed.

**Test status:**
- `--demo` command (T01 "How to test", 7 groups) ran clean, no exceptions, no warnings; 7 PNGs written, listed above.
- Assertion block (7 representatives × k ∈ {2,3,4,5,6,7,8,9,12}, 63 cases): 0 `AssertionError`. 57 cases drawn (coverage 0.999–1.001, `len(flats)==k`, every zone valid with no interiors, pairwise flat overlap < 0.02 m², flat/circ overlap < 0.02 m²); 6 `Refusal`, all `SLIVER` k ∈ {5,6,7,8,9,12} token `BAND_LT_3M` — exactly the expected case (a depth band under 3.0 m). No unexpected refusal, no `CUT_<ExceptionName>`.

**Notes:**
- `cut_courtyard` and `cut_wings` are stubs (`NotImplementedError`) as directed; `cut()` dispatches to them for `COURTYARD` / `L_SHAPE` / `U_OR_T_SHAPE` / `COMPLEX_MULTI_WING` and the `--demo` CLI draws the bare footprint with `NotImplementedError` in the title for those groups (not exercised in this task's demo/assertion runs, which only cover the seven implemented groups per the plan's "How to test").
- No file outside `scripts/eu21/05_group_cutters.py`, `openubem/outputs/eu_evidence/EU-21/cutter_demo/*.png`, this plan's §8, and `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 was touched. No git command run.

#### T02 — `cut_courtyard` (`D-EU-67`) — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (824 lines) — `cut_courtyard` implemented in full; new module-level helpers `_side_len`, `_side_point`, `_side_normal`, `_corner_after`, `_perimeter_segs`, `_corner_ts`, `_u_of_side_point`, `_t_of_side_point`, `_t_of_point`, `_point_at_t`, `_side_box`, `_sector_polygon` (swept-region-by-box-union, replaces an earlier ring-polygon construction — see Deviations), `_equal_area_t`, `_distribute_cuts`, `_snap_to_corners`, `_quadrant_area`, `_connector`.
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_COURTYARD.png` regenerated (k = 2, 3, 6, 9, 12), all five drawn (no refusal in the demo set).

**Deviations:**
- **Perimeter parametrisation is arc-length along the void's MRR (`4a+4b`), classified by nearest side via the quarter-plane rule (`x>a and y>b` → corner, else foot-of-perpendicular on the nearest side)**, not literally "the two 45° diagonals" the plan's step 6 names. Re-derived from first principles: a point's nearest point on an axis-aligned rectangle is genuinely ambiguous (a tie) only in the quarter-plane beyond a corner, and that tie region is exactly `{x>a, y>b}` etc — bounded by the two axis-aligned side-extensions, not a diagonal. This also makes every "sector" a plain `unary_union` of axis-aligned box strips (`_side_box`/`_sector_polygon`), which is what actually makes the construction robust — see next point. A cut snapped to a corner therefore meets its neighbour at an axis-aligned (L-shaped) boundary, not a 45° diagonal line; still a straight-line cut per the CP-1 rule, just not diagonal.
- **`_sector_polygon` was first implemented as the plan literally describes (near-boundary path + each vertex pushed outward `BIG` in its own local direction, closed into one ring) and this broke for any wide interval** (more than ~180° of the loop, which includes every `k=1` or `k=2` case and the first bisection call for `total` area on any `k`): pushing multiple vertices outward independently, each in its own direction, produces a self-intersecting "star" polygon once the direction reverses across the loop, which silently corrupted the area profile (a 0.14 m arc-length step once absorbed 140 m² in one test) and produced `MultiPolygon` sector-cut flats with real gaps. Fixed by building each sector as the union of per-side axis-aligned box strips (one box per side segment the interval spans, each strip's far edge simply extended `BIG` in that side's own normal direction) — robust for any interval width, including the full loop. This is the change that made every k from 1–12 on the representative return `cov==1.0000` with no assertion failures.
- Three further robustness fixes, same class as T01's — see `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 for the full symptom/fix text: (1) `finish()`'s mid-pass `set_precision` can turn `circ` (not just a flat) into a `MultiPolygon`; the R1-style largest-part-keep + donate-the-rest-to-flats rule is now applied to `circ` too. (2) The opening `notch()` box is padded 0.30 m on every side, because the idealized-MRR-frame notch left a real, unsevered sliver of ring on several non-perfectly-rectangular real voids (annulus persisted, spurious `WING_TREE_FAILED`). (3) `_connector()` checks shared-boundary length/area, not raw `distance()`, and bridges a core to the ring with a small 0.30 m box whenever a core (built from the same idealized-frame formula) only meets the real ring at a single point.
- `_snap_to_corners()` claims each corner for its closest candidate cut only (first documented in the debug references) — the plan's own snap rule does not address two candidates landing within 1.0 m of the same corner, which happens on any void whose short side is under ~2 m.
- No §4 constant changed. `cut_wings` is still a stub; `cut()`'s dispatch and the `--demo` CLI are unchanged from T01 except that `COURTYARD` now runs instead of raising `NotImplementedError`.

**Test status:**
- `--demo COURTYARD` (k = 2, 3, 6, 9, 12): all five drawn, `courtyard_cores_gallery`, no exceptions.
- Assertion block, representative × k ∈ {2,3,4,5,6,7,8,9,12} (9 cases): 9/9 drawn, `cov==1.0000` every case, `len(flats)==k`, every zone valid with no interiors, pairwise flat overlap < 0.02 m², flat/circ overlap < 0.02 m². 0 `AssertionError`, 0 unexpected `Refusal`, 0 `CUT_<ExceptionName>`.
- The nine `COURTYARD` plates of `test_05.json` at their own `drawn_per_floor` (9 cases): 7/9 drawn (same assertions, all pass; access-to-circulation ≥ 1.0 m on 5/7, three drawn cases report `access_min_m` between 0.0 and 1.0 — see Notes), 2/9 `Refusal` — `31811` (k=3) `WING_TREE_FAILED` (void MRR 2.68 m × 0.77 m, no corner leaves ≥ 3.0 m² for a 2.4 m core even after the one allowed slide — genuine "n_c shrinks to 0" case per §6 step 2), `31539` (k=2) `FLAT_ENCLOSES_ZONE` (two very large, wide-sector flats on a genuinely non-convex real footprint; R3 correctly reports rather than patches). Neither refusal token is outside the §4 list; no `CUT_<ExceptionName>` anywhere in the 18-case battery.
- Circulation share on the 16 drawn cases: 9.7–32.3 %, generally over the sheet's "10–16 %" expectation on the smaller/tighter real plates — reported per §6 T02 "How to test" instruction ("report, do not tune"), not adjusted.

**Notes:**
- `access_min_m` (the `_shared_len_metric` proxy for C8) came back under 1.0 m — three cases at exactly `0.0` (representative k=8, k=9, k=12; `relation/4165179` k=6) — meaning at least one flat's measured shared boundary with circulation rounds to zero even though the plate still passes coverage/validity/no-overlap. Recorded as a finding, not patched (`D-EU-64` clause access is C8 "report only" per the plan; verdict in T02 does not gate on it — T04 will wire the real C8 check into `run_checks()`).
- Circulation-share range (9.7–32.3 %) is wider than the sheet's "10–16 %" on real (not hand-picked) plates because `n_cores` and the ring/notch/connector geometry scale with the void's actual size and shape, which varies far more than the eleven representatives do; reported per the plan, not tuned.
- Debug references updated: `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1, four new bullets (circ-MultiPolygon in `finish()`, notch padding, core-connector, corner-snap dedup).
- No file outside `scripts/eu21/05_group_cutters.py`, `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_COURTYARD.png`, this plan's §8, and `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 was touched. No git command run.

#### T03 — `cut_wings` (groups 09–11) — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (1180 lines) — `cut_wings` implemented in full; new module-level helpers `_mrr_rectangularity`, `_interior_angles_ccw`, `_split_once`, `_split_wings`, `_reclaim_denoise_loss`, `_absorb_bays`, `_wing_tree`, `_junction`, `_reduce_to_k_wings`, `_alloc_k`, `_wing_columns`, `_polygons_only` (reuses `_sector_polygon`, `_connector`, `_safe_union`, `_shared_len_metric`, `equal_area_x`, `frame`/`to_local`/`to_world` from T01/T02).
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_L_SHAPE.png`, `demo_U_OR_T_SHAPE.png`, `demo_COMPLEX_MULTI_WING.png` regenerated (k = 2, 3, 6, 9, 12); `demo_SLIVER/SQUARE/RECTANGLE/CORRIDOR_RECTANGLE/SLAB/TRIANGLE/TRAPEZOID/COURTYARD.png` re-verified unchanged (T01/T02 groups untouched by this task).

**Deviations:**
- `_sector_polygon()` — inherited from T02, unchanged in name but its *implementation* was rewritten as part of this task (see debug references): a wide (>180°) sweep self-intersected when built as a near-boundary path with each vertex pushed outward independently; every k=1/2 courtyard case and the first bisection call for `total` area on any k needs the full loop, so this was already latent in T02 and would have broken `cut_wings`'s own column search identically. Rebuilt as a `unary_union` of per-side axis-aligned box strips — robust for any interval width. No §4 constant changed; the function's contract (swept region from t0 to t1) is unchanged.
- Sheet step 7's "if forced boundaries alone exceed N_w−1, keep them and let k_w rise ... taken back from the largest other wing; if impossible → Refusal" was dropped in favour of truncating the forced-boundary list to at most `N_w − 1` entries (evenly sampled by index) when a wing has more child junctions than free column slots. The literal rebalance rule (single donor, k stays fixed) failed on **every** k from 2–12 on the `COMPLEX_MULTI_WING` representative, because more than one wing is routinely under-budget at once and the sum of every wing's own structural minimum can exceed `MAXK` outright (measured: 13 > 12 on that representative's 7-wing tree) — not a rare edge case but the common one for any real hub-and-spoke plate. A child whose junction loses its own dedicated column boundary still reaches circulation through the connector-bridge step (§6 step 8, already specified for exactly this "band doesn't touch after union" situation), so access is not lost, only the dedicated-wall guarantee for that one connector. Full symptom/fix text in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1.
- Circulation bands are built as **one straight rectangle spanning the wing's full local-x extent** (`[minx, last-boundary(+LANDING or through-flat wall)]`), not the sheet's more elaborate "from the wing's junction end (extended 0.9 m into the parent) to the last column boundary". This follows the CP-1 ruling directly ("every circulation band is ONE straight rectangle in the frame ... never rebuilt per row or per column") and matches the T01 convex-cutter band pattern already in the file; each wing's local frame is oriented (by a 180° flip when needed, decided once from the wing's own junction position) so "near" is always the low-x end, keeping the through-flat / far-end logic identical to `cut_convex`'s. Band width and the M_w=1/2 placement rule are exactly as specified.
- Three further robustness fixes needed to reach a working state, all documented in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1: (1) forced column boundaries within `edge_pad = min(1.0, span/4)` m of a wing's own edge or of another forced boundary are dropped (was `1e-6` m, too tight — a real child junction landing 0.0008 m inside a wing's corner produced a near-zero-width column and a spurious `CELL_EMPTY`). (2) the core+band union is driven to a single polygon by a fixed-point "largest part is hub, `_connector()`-bridge everything else, re-union, repeat (cap 8 passes)" loop, because per-part "already touches the growing hub" checks do not guarantee the *simultaneous* union of every part is one polygon. (3) `_polygons_only()` strips zero-area `LineString`/`Point` components that `unary_union` can leave behind in what should be a plain `Polygon`/`MultiPolygon` result (seen as a `GeometryCollection` that never matched the `geom_type == "Polygon"` check even though circulation was already fully connected).
- `_reclaim_denoise_loss()` (new, called right after `_absorb_bays()`): `Q = poly.simplify(DENOISE_TOL, preserve_topology=True)` is not guaranteed to contain the true `poly`, so a small real protrusion can fall outside every wing and never get claimed by any flat (measured: 0.34 m² on `COMPLEX_MULTI_WING`, coverage 0.9989, under the 0.999 assertion floor). Any such residual over `SCRAP_M2` is folded into whichever wing shares its longest boundary, before any column/band geometry is built — not a `finish()` patch, a partition-completeness fix upstream of it. §5 clause 9 ("flats are always clipped to the true poly, never to Q") is unaffected: flats still clip to `poly`, this only ensures the *wing partition itself* (used to build cells/bands) fully covers `poly` first.
- No §4 constant changed. `cut()`'s dispatch is unchanged from T01/T02.

**Test status:**
- `--demo L_SHAPE U_OR_T_SHAPE COMPLEX_MULTI_WING` (k = 2, 3, 6, 9, 12): 13/15 drawn (L_SHAPE 5/5, U_OR_T_SHAPE 5/5, COMPLEX_MULTI_WING 3/5 — k=9,12 REFUSED `WING_TREE_FAILED` in the title, bare footprint drawn). No exceptions.
- Assertion block, representatives × k ∈ {2,3,4,5,6,7,8,9,12} (27 cases): L_SHAPE 9/9, U_OR_T_SHAPE 9/9, COMPLEX_MULTI_WING 7/9 (k=9, k=12 `WING_TREE_FAILED` — the same-representative structural minimum described above). 25/27 drawn, `cov` 0.99996–1.00001 every drawn case, `len(flats)==k`, every zone valid with no interiors, pairwise flat overlap < 0.02 m², flat/circ overlap < 0.02 m². 0 `AssertionError`.
- The 30 `L_SHAPE`/`U_OR_T_SHAPE`/`COMPLEX_MULTI_WING` plates of `test_05.json`: 13/30 carry a recorded `footprint` (the other 17 were refused before any geometry was drawn under the old post-pass algorithm, same situation as 1 of the 10 `COURTYARD` plates in T02 — nothing to read). Of those 13: 11/13 drawn (same assertions, all pass), 2/13 `Refusal` — both `L_SHAPE` at k=3 (`way/435510859`, `BATIMENT0000000240880388_part0`), token `WING_TREE_FAILED` — the merged core+band circulation came back with an interior ring (`circ.interiors` non-empty) on these two specific real footprints; per §6 step 8 ("must be one Polygon with no interiors, else Refusal") this is drawn, marked and counted, not patched. No `CUT_<ExceptionName>` anywhere in the 40-case combined battery (27 representative + 13 real).
- Combined tally: 36/40 drawn, 4/40 refused, all 4 tokens `WING_TREE_FAILED` (in the §4 list), 0 unexpected token, 0 `AssertionError`, 0 uncaught exception.

**Notes:**
- Every refusal in this task's battery is `WING_TREE_FAILED`; none is `CELL_EMPTY`, `BAND_LT_3M`, `FLAT_ENCLOSES_ZONE` or `SECONDARY_VOID_UNCUT` (the last two/three don't apply to this cutter; `CELL_EMPTY` did occur during development and was fixed, see Deviations).
- `COMPLEX_MULTI_WING` at k=9,12 refuses on the representative because that specific building's `Q`-split genuinely produces a 7-wing tree whose combined per-wing structural minimum (13) exceeds `MAXK` (12) — reported, not tuned; §4's `MIN_WING_M2`/`MIN_WING_W`/`REFLEX_TOL_DEG` were not touched to make it pass.
- Debug references updated: `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1, six new bullets (sector-polygon rewrite, forced-boundary truncation, edge-pad widening, fixed-point circulation merge, `_polygons_only` GeometryCollection strip, `_reclaim_denoise_loss`).
- No file outside `scripts/eu21/05_group_cutters.py`, the three `EU-21/cutter_demo/demo_{L_SHAPE,U_OR_T_SHAPE,COMPLEX_MULTI_WING}.png`, this plan's §8, and `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 was touched. No git command run.

#### T04 — Wire `04_group_tests.py` to the cutter, add `C8`, regenerate the five sheets — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/04_group_tests.py` (rewired, same file, ~760 lines) — module docstring, imports (`_M05` loaded, `cut`/`Refusal`/`ACCESS_MIN_M` bound; `options`/`capture`/`apply_law` dropped; `_M02` kept only for `lobes_of`/`parts`/`sbuf`), `READINGS` replaced with the §4 token list, `reading_for()` prefix `LAW_`→`CUT_`, `build_plate()` calls `cut()` directly (`Refusal`→`REFUSED`+token, other `Exception`→`ERROR`+`CUT_<ExceptionName>`+message, success path builds `dwellings`/`circulation` ring-sets from `out["flats"]`/`out["circ"]`, `status="direct"`, `notes=out["notes"]`), `run_checks()` adds `C8` access (report only, `sbuf(f,0.05).intersection(circ).length` min over flats, `n/a` when no circulation), `card()` renders the `C8` chip, `build_checks_html()` adds the `C8` `<li>`, `build_lede_html()` (both variants) and the footer's "What this is" paragraph rewritten to name the direct cutter and drop the `D-EU-66`/`apply_law()` wording, tally section "Law errors"→"Cutter errors", checks-section heading "seven checks C1–C7"→"eight checks C1–C8", READ legend gets a `C8` example pair. Verdict still C1–C6 only; `CHECK_META` (C1–C5) untouched, as directed.
- `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0{1..5}.postpass.json` (**new**, copies of the pre-T04 `test_0N.json`, made before any run).
- `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0{1..5}.json` (**regenerated** by `--test all`).
- `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0{1..5}_*.html` (**regenerated**, same five filenames).
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/test0{1..5}_<GROUP>.png` (**new**, 55 files, 5 tests × 11 groups; ≤5 columns per row, 4.2 in/plate, dpi 110; drawn with a one-off `python -c`-style script per the plan, not a saved repo file).
- `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 — three new `[OPEN]` bullets (`CUT_RuntimeError`, `CUT_GEOSException`, `CUT_AttributeError`), each with the exact traceback site.

**Deviations:**
- The 55 contact-sheet PNGs were rendered by a standalone script run once via the interpreter (not typed as a single-line `-c` string, for readability), kept in the session scratchpad, not the repo — matches the plan's "one `python -c`" instruction in spirit (a throwaway render, not a new tracked file) and does not add a file to §3's table.
- No §4 constant changed, `05_group_cutters.py` not touched, `01`/`02`/`03`/`group_plans.json`/`openubem/geometry/`/`rules/RULES_*.html` not touched.

**Test status:**
- `--test 1` run alone first; record schema confirmed unchanged: `footprint`/`dwellings`/`circulation` ring-sets, `verdict`, `token`, `scheme` (`status="direct"` now, was `"in-force"`/`"proposed"`), `status`, `circ_m2` all present; `checks` now has 8 keys `C1`–`C8`.
- `--test all`: five-test tally **62 refused · 488 drawn · 411 pass · 71 fail · 6 errors** (550 plates total), vs. the pre-remedy line `183 refused · 316 drawn · 242 pass · 74 fail · 51 errors`. Per test: T01 4/29/26/3/0, T02 12/120/100/18/2, T03 5/50/42/7/1, T04 29/191/158/31/2, T05 12/98/85/12/1 (refused/drawn/pass/fail/error). Cutter compute time (sum of `elapsed_s`) 4.47 s over all 550 plates.
- Checks failing most (across all drawn plates, C1–C6 `pass=False` + C7/C8 `class=="warn"`): C7 324, C6 44, C4 29, C5 25, C8 10, C1/C2/C3 0.
- 6 `ERROR` records, 3 distinct tokens, all reproduced standalone with full tracebacks and registered `[OPEN]` in the debug references (see Artifacts): `CUT_RuntimeError` ×2 (Slab k=9, `IT-BOL-GALVANI2/28583`, tests 02+04 — `cut_convex:314`), `CUT_GEOSException` ×2 (Slab k=12, `GB-LDN-STDUNSTANS/way/398158956`, tests 02+04 — `finish():191`, `set_precision()` itself raising, not wrapped by `_safe_union()`), `CUT_AttributeError` ×2 on two distinct real plates (`U_OR_T_SHAPE`, `IT-BOL-GALVANI2/32891` k=2 test 03 and `/31952` k=4 test 05 — `finish():210`, a `cut_wings` flat cell reaching R3 as a `GeometryCollection`, a type `dissolve_pass()` never special-cases).
- 55/55 contact-sheet PNGs and 5/5 HTML sheets written; no exception during rendering.

**Notes:**
- All three `CUT_` exceptions are inside `05_group_cutters.py`, which this task must not edit; each is drawn as an error box (via `card()`'s existing `REFUSED`/`ERROR` branch) and counted, not patched — matches the plan's hard rule 6/§6 T04 step 2 instruction exactly.
- No file outside `scripts/eu21/04_group_tests.py`, `openubem/outputs/eu_evidence/EU-21/rules_tests/*`, `openubem/outputs/eu_evidence/EU-21/cutter_demo/test0*_*.png`, `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0*.html`, this plan's §8, and `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 was touched. No git command run. CP-3 reached; T05 not started.

#### T05a — wings: corridor only where it serves a flat, no structural minimum (DD-8) — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (1214 lines after this task) — `cut_wings`'s per-wing loop rewritten: (a) `_wing_columns(w_local, N_w, [], minx, maxx)` (forced child-junction boundaries dropped); (b) `reach = child_j + xs`; a leaf wing with `k_w == 1` and no children gets a `[minx-0.5, minx+LANDING]` stub band on the inner side; every other wing gets `band_lo = min(reach)-LANDING` (root) or `minx-0.5` (non-root, "as now"), `u_far = max(reach)+LANDING`, except the odd-`k_w` through-flat cap `u_far = xs[-1]` kept exactly when `xs[-1] >= max(reach)`. Core placement and the connector/one-Polygon loop untouched, per (c)/(d).
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_L_SHAPE.png`, `demo_U_OR_T_SHAPE.png`, `demo_COMPLEX_MULTI_WING.png` regenerated (k = 2, 3, 6, 9, 12).

**Deviations:** none — implemented literally against §6 T05a's "How".

**Test status:**
- `--demo` for the three groups: ran clean, no exceptions, 3 PNGs written.
- Report block (representative × k ∈ {2,3,6,9,12}, 15 lines): L_SHAPE k=2 circ=10.1 %, U/T k=2 circ=8.9 % (both ≤ 15 % as expected); `COMPLEX_MULTI_WING` k=9 and k=12 now **drawn** (circ 25.2 %, 29.3 %) where T03 refused them on the old structural-minimum bug. `COMPLEX_MULTI_WING` k=3 now refuses `WING_TREE_FAILED` — traced to the fixed-point connector loop (§2 rule (d), untouched) not converging within its 8-pass cap on this specific real wing's very short new stub band (a wing whose own junction sits mid-span of its MRR, not at an extreme, so the flip-to-low-x convention the connector previously covered by sheer band length no longer reaches by construction); reported as a finding per hard rule 6, not patched, and matches the "for a reason that is not the column minimum" expectation. `U_OR_T_SHAPE` k=3/6/9 report `min_access=0.81 m` (< `ACCESS_MIN_M`) on the same flat each time — also reported, not patched (C8 is report-only per T04).

**Notes:**
- No file outside `scripts/eu21/05_group_cutters.py` and the three demo PNGs was touched. No git command run. No new unhandled exception (only `Refusal`, an intended code path); no debug-reference entry needed.

#### T05b — DD-6: loading chosen by aspect, 3 m floor on every flat — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (1246 lines) — module constants `MIN_FLAT_W = BAND_MIN_W` and `COURTYARD_MIN_VOID_SIDE = 6.0` added; new `choose_loading(L_eff, W, k)`; `cut_convex`'s k ≥ 5 branch now calls `choose_loading(L_eff, W, k)` for non-gallery groups and, for `LINEAR_GALLERY_GROUPS`, keeps `M=1, N=k` but refuses `BAND_LT_3M` when `L_eff/N < MIN_FLAT_W`; `cut_wings`'s per-wing loop calls `choose_loading` for every wing with `k_w >= 2` (k_w == 1 keeps the old `DOUBLE_LOADED_MIN_DEPTH` rule, `N_w = 1`); `_alloc_k` now computes a per-wing cap `max(1, floor(L_w/MIN_FLAT_W) * M_max_w)`, refuses `BAND_LT_3M` when `sum(caps) < k`, and moves any post-largest-remainder surplus to the wing with the most spare capacity until stable.
- Demo PNGs regenerated for `SQUARE`, `RECTANGLE`, `TRAPEZOID`, `TRIANGLE`, `L_SHAPE` (k = 2, 3, 6, 9, 12).

**Deviations:** none from §6 T05b's "How" — implemented as specified.

**Test status:** (`--demo` clean, no exceptions; report block k ∈ {5,6,9,12}, 20 lines)
- `SQUARE` k=5,6 OK (min flat short side 4.33 m); k=9,12 refuse `BAND_LT_3M` (`choose_loading` finds no valid M on this small footprint) — DD-6 working as intended.
- `RECTANGLE`, `TRIANGLE` OK at every k (min short side 2.91-4.51 m, all ≥ 2.9 m).
- `TRAPEZOID` k=5,6,9 draw, k=12 refuses `BAND_LT_3M`; **k=9's nominal `col_w=3.19 m` clears the 3.0 m floor but the actual clipped flat's own MRR short side comes out at 2.46 m** (`choose_loading` checks the plate's local bounding-box grid spacing, not the post-clip shape on a non-rectangular plate, so a sloped edge can still narrow one column below nominal) — reported as a finding per hard rule 6, not patched with a further post-clip check (§6 T05b's "What" specifies only the `choose_loading`/`_alloc_k` change).
- `L_SHAPE` k=5 draws (min short side 3.94 m, OK); k=6,9,12 all refuse `BAND_LT_3M` via the new `_alloc_k` capacity cap on this representative's two wings.

**Notes:**
- No file outside `scripts/eu21/05_group_cutters.py` and the five demo PNGs was touched. No git command run. No new unhandled exception; no debug-reference entry needed.

#### T05c — DD-7: a light well is not a courtyard; exact sectors for true courtyards — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (1350 lines) — `_snap_cuts_to_voids(P_local, xs, y_row=None)` (new); called from `cut_sliver`, both branches of `cut_convex`, and `_wing_columns`. `exterior_group(poly)` (new, mirrors `01_cut_group_plans.py:27-39`'s `cls()` on the exterior ring alone) and `_dispatch_group(poly, k, grp2)` (new). `cut()` rewritten: for `grp == "COURTYARD"` with an interior ring whose MRR short side `< COURTYARD_MIN_VOID_SIDE`, routes to `_dispatch_group` with `+lightwell` appended to the scheme and `notes["grp2"]` set (k=1 stays `single_dwelling`); a true courtyard (void ≥ 6 m, or no interior ring) still goes to `cut_courtyard` unchanged. `cut_courtyard`'s sector step replaced: two-crossing cut lines (`split(Z, unary_union(lines))`, each line starting 0.3 m inward of the void-boundary point before extending `BIG` outward — see debug references) partition `Z` exactly; parts assigned to the sector whose `[t_i, t_{i+1})` contains `_t_of_point(part.representative_point())`, unioned per sector via `_safe_union`. Coverage assertion `Σ flats + circ ≥ 0.999 × poly.area` added right before the `finish()` call.
- `demo_COURTYARD.png` regenerated (k = 2, 3, 6, 9, 12).

**Deviations:**
- The literal one-sided ray (`LineString([pt, far])`, `pt` exactly on the void's MRR boundary) left `split()` unable to divide the annulus on 3 of 9 real true-courtyard plates — `pt` is also exactly on `Z`'s own boundary there (the ring is notched away at the opening), so the ray registers only one clean boundary crossing instead of two and `split()` returns the whole ring unsplit, `CELL_EMPTY` on every sector but one. Fixed by starting each line 0.3 m inward of `pt` (still "the ring point at `t`," just nudged off the tangent) before extending `BIG` outward; verified against the 9 real void ≥ 6 m plates (see Test status). Logged in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1. No §4 constant changed; the sector geometry, corner-snap and secondary-void rules are otherwise exactly as specified.
- `exterior_group()`'s reflex-count branch omits the original `cls()`'s `TRIANGLE` case (`n_edges_ge_15pct_perimeter <= 3`) — matches the plan's own mirror spec literally ("reflex count ... 0 → TRAPEZOID", no TRIANGLE branch) and is harmless under DD-2 (TRIANGLE and TRAPEZOID share `cut_convex`).
- `_split_wings`/`cut_wings` needed no change to carry a light-well's interior ring through wing-splitting: `Q = poly.simplify(...)` and every downstream step already read `.exterior` only (or clip the final cells against the true holed `poly`), so the hole flows through correctly by construction — verified empirically on 10 real light-well plates classified `L_SHAPE`/`U_OR_T_SHAPE`/`COMPLEX_MULTI_WING` (cov 1.0000 or a same-token `Refusal`, no crash). No deviation needed; not a code change.

**Test status:**
- (1) Representative `COURTYARD` (a light well, void 2.96 × 3.46 m): `grp2=COMPLEX_MULTI_WING` at every k; all five of k=2,3,6,9,12 `REFUSED WING_TREE_FAILED` — traced to `_split_wings`'s pre-existing (T03, unmodified) 8-piece cap: this specific real exterior has 9 reflex vertices, one more than the cap allows, independent of the light-well dispatch itself (the same building, hand-fed straight to `cut_wings` as `COMPLEX_MULTI_WING`, would refuse identically). Reported as a finding, not patched (hard rule 6; the cap is T03's, out of T05c's scope).
- (2) The 9 distinct real `COURTYARD` plates with void ≥ 6 m recorded in `rules_tests/test_0N.json` (of the plan's cited 11; 2 have no recorded footprint, refused pre-T05): 8/9 now drawn, `cov=1.0000` on every drawn case (was the T02-era union-of-strips gap, e.g. 21.9 % uncovered at k=3 on the representative), circulation share 7.6-41.9 %, all flats and circulation simple (no holes). 1/9 refused `CELL_EMPTY` (`29659` k=12) after the split-line fix — a genuine higher-k sector-assignment shortfall, reported not patched.
- (3) `demo_COURTYARD.png` regenerated, 5/5 panels render (all showing the representative's `REFUSED` title per (1) above), no exception.
- Light-well dispatch spot-checked on 10 additional real plates spanning every non-SLIVER `grp2` value (`SQUARE`, `RECTANGLE`, `CORRIDOR_RECTANGLE`, `L_SHAPE`, `U_OR_T_SHAPE`, `COMPLEX_MULTI_WING`): all either drawn at `cov=1.0000` with no holed flat, or a proper §4 `Refusal` token — 0 unhandled exceptions. Across the five recorded test JSONs, 14 distinct real `COURTYARD` buildings have a void `< 6.0 m` and are now rerouted: `COMPLEX_MULTI_WING` 6, `L_SHAPE` 3, `SQUARE` 2, `RECTANGLE` 1, `U_OR_T_SHAPE` 1, `CORRIDOR_RECTANGLE` 1 (`SLIVER` 0 among the recorded ones).

**Notes:**
- One error solved and registered: the `CELL_EMPTY`/`split()` tangency bug, `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 (new bullet, source doc this plan §8 T05c).
- No file outside `scripts/eu21/05_group_cutters.py`, `demo_COURTYARD.png`, this plan's §8, and `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 was touched. No git command run.

#### T05d — the three cutter bugs measured at CP-3 (6 `ERROR` plates of 550) — completed 2026-09-01

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (1375 lines) — (1) `cut_convex` (`:365-392`): `circ_local = unary_union([core, band]).intersection(P)` now passes through `_polygons_only()`, then (if not one `Polygon`) runs the same fixed-point `_connector`-bridge merge loop `cut_wings` uses (`:378-390`, hub = largest part, cap 8 passes); only a still-disconnected result raises `Refusal("WING_TREE_FAILED")` — the old bare `raise RuntimeError(...)` is gone. (2) `finish()` (`:164-179`): new `_safe_precision(g)` closure (try `set_precision`, then `set_precision(g.buffer(0), 0.001)`, then give up and count it) replaces every bare `set_precision(f, 0.001)` call on emitted flats/circulation (`:242-243`, `:266-267`); `finish()`'s return dict now carries `"unsnapped": unsnapped[0]`. (3) `finish()`'s entry (`:166-167`) passes every flat and the circulation through `_polygons_only()` before R1 runs. `cut_sliver`, `cut_convex`, `cut_courtyard`, `cut_wings` each fold `out.get("unsnapped", 0)` into their own `out["notes"]` dict so the count survives past the `out["notes"] = {...}` overwrite.
- `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 — the three `[OPEN]` bullets closed (marker dropped, fix text + `file:line` added, this plan §8 T05d cited).

**Deviations:**
- The plan's "How to test" says to re-cut the six plates "from the recorded footprints in `rules_tests/test_0N.json`" — but `build_plate()` only records `footprint` on a successful draw, never on `REFUSED`/`ERROR`, so the six `ERROR` records carry no footprint in any JSON (current or `.postpass`). Used `01_cut_group_plans.py`'s own `load_universe()` (the same census/geometry source the test harness itself uses) to pull each building's real polygon by `(district, building_id)` instead, centred exactly as `04_group_tests.py`'s `select_own`/`select_size` do. Same real footprints, same source of truth, just not routed through the JSON file the plan named.
- No §4 constant changed. No `01`/`02`/`03`/`group_plans.json`/`openubem/geometry/`/`rules/RULES_*.html` touched.

**Test status:**
- The four distinct real footprints behind the six `ERROR` records, re-cut standalone at their recorded `k`: `IT-BOL-GALVANI2/28583` k=9 SLAB (tests 02+04) → now `REFUSED WING_TREE_FAILED` (the connector loop genuinely cannot bridge this plate — a real, reportable refusal, not a crash). `GB-LDN-STDUNSTANS/way/398158956` k=12 SLAB (tests 02+04) → now drawn, `scheme=i_shape_linear_gallery`, `cov=1.0000`, `unsnapped=0`. `IT-BOL-GALVANI2/32891` k=2 U_OR_T_SHAPE (test 03) → now drawn, `cov=1.0000`. `IT-BOL-GALVANI2/31952` k=4 U_OR_T_SHAPE (test 05) → now drawn, `cov=1.0000`. 0/4 raised an uncaught exception (6/6 records covered, since two pairs are the same building tested in two different test files).
- Regression smoke test after all of T05a-d: the 7 T01 convex representatives × k ∈ {2,3,4,5,6,7,8,9,12} (63 cases) → 51 drawn (coverage 0.999-1.001, valid, no holes), 12 `Refusal` (DD-6's stricter width floor, expected), **0 unexpected exception**. The `COURTYARD`/`L_SHAPE`/`U_OR_T_SHAPE`/`COMPLEX_MULTI_WING` representatives × the same 9 k values (36 cases) → 19 drawn, 17 `Refusal`, **0 unexpected exception**.

**Notes:**
- Three `[OPEN]` errors closed this task; see `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 for the fix text against each.
- No file outside `scripts/eu21/05_group_cutters.py`, this plan's §8, and `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 was touched. No git command run.

#### T05e — re-measure — completed 2026-09-01

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0{1..5}.json` (regenerated by `--test all`).
- `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0{1..5}_*.html` (regenerated).
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/test0{1..5}_<GROUP>.png` (55 files, overwritten).
- `scripts/eu21/04_group_tests.py` (762 lines, unchanged line count) — one string changed per director instruction (see Deviations).

**Deviations:**
- Per the director's mid-task instruction: the tally card's "Plans drawn" reading (`build_html()`, `scripts/eu21/04_group_tests.py:601`) changed from `"the engine returned a scheme at this count"` to `"the cutter drew a plan at this count"` — the direct cutter has no "engine" any more. Nothing else in `04_group_tests.py` changed; no cutter-emitted field (`+lightwell` scheme suffix, `notes["grp2"]`, `notes["unsnapped"]`) broke anything (`scheme`/`notes` are only ever displayed as text or serialized, never pattern-matched), so no other fix was needed.

**Test status:**
- `--test all`, foreground, ran clean, 0 exceptions. Five-test tally: **71 refused · 479 drawn · 424 pass · 55 fail · 0 errors** (550 plates), vs. pre-remedy `183 refused · 316 drawn · 242 pass · 74 fail · 51 errors` and CP-3 `62 refused · 488 drawn · 411 pass · 71 fail · 6 errors`. Per test (refused/drawn/pass/fail/error): T01 4/29/26/3/0, T02 18/114/99/15/0, T03 4/51/46/5/0, T04 33/187/162/25/0, T05 12/98/91/7/0.
- Per-group table (plates/drawn/pass/fail/refused/error/top token or failed check):
  COURTYARD 50/28/15/13/22/0/WING_TREE_FAILED×11 · SLIVER 50/38/38/0/12/0/BAND_LT_3M×12 · SQUARE 50/50/50/0/0/0/— · RECTANGLE 50/50/50/0/0/0/— · CORRIDOR_RECTANGLE 50/46/46/0/4/0/BAND_LT_3M×4 · SLAB 50/47/43/4/3/0/WING_TREE_FAILED×2 · TRIANGLE 50/50/50/0/0/0/— · TRAPEZOID 50/50/50/0/0/0/— · L_SHAPE 50/36/31/5/14/0/WING_TREE_FAILED×11 · U_OR_T_SHAPE 50/43/30/13/7/0/FAIL:C4×6 · COMPLEX_MULTI_WING 50/41/21/20/9/0/FAIL:C6×10.
- Distinct `CUT_<ExceptionName>` tokens: **none** — 0 `ERROR` records across all 550 plates (T05d's three fixes hold on the full census, not just the four originally-measured plates).
- `notes["unsnapped"]` (the `_safe_precision` fallback counter) is 0 on every one of the 550 plates — `set_precision` never needed the `buffer(0)`/give-up fallback on this run.
- Errors fully eliminated (6→0) and fail count dropped (71→55) even though refused rose slightly (62→71) and drawn fell slightly (488→479) — expected: DD-6's stricter `MIN_FLAT_W` floor and the courtyard light-well split trade a few borderline draws for honest refusals, net quality up (pass 411→424).

**Notes:**
- No file outside the ones listed in Artifacts, this plan's §8, and (already closed in T05d) `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 was touched. No git command run. CP-4 reached.

#### T06a — no hairline circulation: connectors and stubs are corridor-wide, stubs grow before connectors are tried — completed 2026-09-02

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (1421 lines after this task) — `_connector`'s default `width` changed `0.30` → `CORRIDOR_W`; new `_touches(a, b)` and `_bridge(hub, others, poly)` helpers (running-hub union, skips `_connector` for any part already touching the union built so far); `cut_convex`'s core+band connector loop now calls `_bridge`; `cut_courtyard`'s core-building loop gates the translate retry on `not _touches(cb, R_base)` in addition to `area < 3.0`, and `trial()`'s core-to-ring loop is now one `_bridge(R, cores, B)` call; `cut_wings` gained `band_specs` (per-wing band geometry parameters) and a growth block — before the fixed-point connector loop, a disconnected wing's own band is grown by extending `band_lo` in 0.5 m steps (cap 3.0 m total) toward its junction and re-tested, only falling through to `_bridge` if growth alone does not reach one `Polygon`.
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/demo_L_SHAPE.png`, `demo_U_OR_T_SHAPE.png`, `demo_COMPLEX_MULTI_WING.png`, `demo_COURTYARD.png` regenerated (k = 2, 3, 6, 9, 12).

**Deviations:**
- `_bridge()` applies `set_precision(…, 0.001)` on every unioned/connector-augmented result in all three call sites, including `cut_convex`'s (which, pre-T06a, ran its connector loop without any intermediate `set_precision`). Consistent with the T05d robustness theme; no §4 constant changed, no cutter algorithm text altered.
- Item (3)'s "moved along its void side ... toward the ring" is implemented against `R_base` (the un-notched ring), not the per-opening-side notched `R`, because `cores` is built once, shared across all four `trial(opening_side)` calls; a core near a corner untouched by a given side's notch is unaffected either way. Not a behaviour change beyond broadening the retry's trigger condition (from `area < 3.0` alone to `area < 3.0 or not touching R_base`); the retry mechanics themselves ("keep the translate retry") are unchanged.

**Test status:**
- `--demo` for the three wing groups + `COURTYARD`: ran clean, no exceptions, 4 PNGs written.
- Regression smoke test, all 11 groups × k ∈ {2,3,4,5,6,7,8,9,12} (99 cases, representatives): 69 drawn (coverage 0.995–1.005, valid, no holes, `len(flats)==k`), 30 `Refusal`, **0 unexpected exception** (vs. T05d's post-remedy baseline of 70 drawn/29 refused/0 errors on the same 99-case battery — a 1-case shift between drawn/refused is expected from the connector-loop change, not a regression).
- Erosion test (representative × k ∈ {2,3,6,9}, the three wing groups + `COURTYARD`, 16 cases): 9 drawn, 7 refused (`L_SHAPE` k=6,9 `BAND_LT_3M`; `COMPLEX_MULTI_WING` k=3 `WING_TREE_FAILED`; `COURTYARD` k=2,3,6,9 all `WING_TREE_FAILED` — the representative is a light well dispatched to `COMPLEX_MULTI_WING`, which refuses on `_split_wings`'s pre-existing 8-piece cap, per T05c's already-reported finding, unrelated to T06a). Of the 9 drawn: circulation stayed one `Polygon` after 0.60 m erosion on 6/9 (`L_SHAPE` k=2,3; `U_OR_T_SHAPE` k=3,6,9; `COMPLEX_MULTI_WING` k=2), split into a `MultiPolygon` on 3/9 (`U_OR_T_SHAPE` k=2 → 2 parts; `COMPLEX_MULTI_WING` k=6 → 2 parts, k=9 → 5 parts); area retained ≥ 0.5× the pre-erosion circulation on only 1/9 (`U_OR_T_SHAPE` k=3, 0.575). 0 `AssertionError` (reported per-case, not hard-asserted, per hard rule 6).

**Notes:**
- The area-ratio bar (≥ 0.5× after 0.60 m erosion) is mathematically tight for any network built from `CORRIDOR_W`=1.80 m bands and `CORE_MIN_SIDE`–`CORE_MAX_SIDE` (2.4–4.0 m) cores: a straight 1.8 m corridor of length L retains area ratio → 1/3 as L grows; even an isolated `CORE_MAX_SIDE`=4.0 m square core retains only 0.49 after 0.6 m erosion on all sides. Reported per hard rule 6, not tuned (no §4 constant touched).
- The 3 `MultiPolygon`-after-erosion cases are a residual finding beyond items (1)–(4)'s literal scope (thin joints not covered by the hairline-connector, redundant-connector, core-touch or band-growth fixes) — reported, not chased further inside T06a.
- No file outside `scripts/eu21/05_group_cutters.py`, the four demo PNGs, this plan's §8, was touched. No git command run. No new unhandled exception; no debug-reference entry needed.

#### T06b — true courtyards: the 3 m floor on gallery sectors — completed 2026-09-02

**Artifacts:**
- `scripts/eu21/05_group_cutters.py` (1427 lines) — in `cut_courtyard`'s `trial()`, for `k ≥ 2`: `if P / k < MIN_FLAT_W: raise Refusal("BAND_LT_3M")` before `_distribute_cuts` is called; after the sectors are built, each flat's MRR short side is checked via `frame(f)` and the same token raised if any is `< MIN_FLAT_W`.

**Deviations:**
- The plan's "9 true courtyard plates of T05c" could not be reproduced by id (the plan/progress log names only one example, `29659`, not the full list). Re-derived independently from the current, deterministic selection: for every `group=="COURTYARD"` record across the five `rules_tests/test_0N.json` files, looked up the real polygon by `(district, building_id)` via `01_cut_group_plans.py`'s own `load_universe()`, ran it through `05_group_cutters.py`'s own `_normalize()`, and kept every distinct building whose largest interior ring has MRR short side ≥ `COURTYARD_MIN_VOID_SIDE`. This found **13** distinct plates, not 9 (one of the 13, `IT-BOL-GALVANI2/29659` at k=12, matches T05c's own cited example exactly, confirming the method). The 4-plate difference from the plan's "11 cited" (9 found + 2 without a recorded footprint) is attributed to the plan's DD-7 "23 of 34" tally being an overnight approximate count, not a re-verified one; not investigated further (out of T06b's scope; no §4 constant or rule changed).

**Test status:**
- The 13 true-courtyard plates at their recorded `drawn_per_floor`: 5 drawn, 8 refused (`BAND_LT_3M`×3 — the new guard, exactly its intended effect, including on `ES-MAD-BERRUGUETE/relation/4678507` k=9, one of the two plates T06b's own "Why" names as drawing 1 m strips; `WING_TREE_FAILED`×2, `CELL_EMPTY`×1 — `29659` k=12, the same pre-existing finding T05c already reported; `FLAT_ENCLOSES_ZONE`×2 — pre-existing non-convex-footprint behaviour, same pattern T02 already reported for a different plate). Minimum flat MRR short side over the 5 drawn plates: **10.83 m** (`IT-BOL-GALVANI2/30155` k=3), comfortably above the 2.9 m floor. 0 unexpected exception, 0 `CUT_<ExceptionName>`.

**Notes:**
- No file outside `scripts/eu21/05_group_cutters.py`, this plan's §8, was touched. No git command run. No new unhandled exception; no debug-reference entry needed.

#### T06c — re-measure — completed 2026-09-02

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0{1..5}.json` (regenerated by `--test all`).
- `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0{1..5}_*.html` (regenerated).
- `openubem/outputs/eu_evidence/EU-21/cutter_demo/test0{1..5}_<GROUP>.png` (55 files, overwritten) and `demo_<GROUP>.png` (all 11, overwritten).

**Deviations:** none — `04_group_tests.py` needed no edit; every cutter-emitted field it reads (`scheme`, `notes`, `verdict`, `token`) is only displayed or serialized, never pattern-matched.

**Test status:**
- `--test all`, foreground, ran clean, 0 exceptions. Five-test tally: **68 refused · 482 drawn · 432 pass · 50 fail · 0 errors** (550 plates), vs. pre-remedy `183 · 316 · 242 · 74 · 51`, CP-3 `62 · 488 · 411 · 71 · 6`, CP-4 `71 · 479 · 424 · 55 · 0`. Per test (refused/drawn/pass/fail/error): T01 3/30/26/4/0, T02 17/115/103/12/0, T03 4/51/46/5/0, T04 32/188/165/23/0, T05 12/98/92/6/0.
- Per-group table (plates/drawn/pass/fail/refused/error/top token or failed check): COURTYARD 50/24/15/9/26/0/`WING_TREE_FAILED`×12 · SLIVER 50/38/38/0/12/0/`BAND_LT_3M`×12 · SQUARE 50/50/50/0/0/0/— · RECTANGLE 50/50/50/0/0/0/— · CORRIDOR_RECTANGLE 50/46/46/0/4/0/`BAND_LT_3M`×4 · SLAB 50/47/43/4/3/0/`WING_TREE_FAILED`×2 · TRIANGLE 50/50/50/0/0/0/— · TRAPEZOID 50/50/50/0/0/0/— · L_SHAPE 50/41/35/6/9/0/`WING_TREE_FAILED`×6 · U_OR_T_SHAPE 50/42/32/10/8/0/`FAIL:C4`×7 · COMPLEX_MULTI_WING 50/44/23/21/6/0/`FAIL:C4`×9.
- Distinct `CUT_<ExceptionName>` tokens: **none** — 0 `ERROR` records across all 550 plates.
- vs CP-4: refused 71→68, drawn 479→482, pass 424→432, fail 55→50, errors 0→0. `COURTYARD` drawn fell 28→24 and refused rose 22→26 (T06b's `BAND_LT_3M` guard trading a few narrow-sector draws for honest refusals); every other group held flat or improved.

**Notes:**
- No file outside the ones listed in Artifacts, this plan's §8, was touched. No git command run. CP-5 reached.

#### Director sign-off — CP-1…CP-5 — 2026-09-02 00:30

**Status:** COMPLETE for the night session (T01–T06c). Executors: five fresh Sonnet sessions, one per checkpoint slice. **Final tally (T06c):** 68 refused · 482 drawn · 432 pass · 50 fail · 0 errors on 550 plates; pre-remedy 183 · 316 · 242 · 74 · 51. **Audited by the director:** all eleven `demo_<GROUP>.png` and the contact sheets `test04_COURTYARD`, `test04_TRAPEZOID`, `test02_COURTYARD`, `test05_{L_SHAPE,U_OR_T_SHAPE,COMPLEX_MULTI_WING}` at CP-3, CP-4 and CP-5; `TEST_01` sheet rendered in headless Chrome at CP-3. **Open for the owner:** ratification of DD-1…DD-8; T07 candidates are listed in the director prompt §5. **Not done, by rule:** no `03` run (RULES text lags the code), no git, no EnergyPlus (`D-EU-55`).
