# Director prompt — floor planning for the eleven building groups

**Opened 2026-09-01, last updated 2026-09-05 — `T06` (`_finding249_remedy`, 2,527 tasks) is draining:
London/Lyon/Madrid harvested, Bologna still running. Owner ruled 2026-09-05 (`D-EU-101`) to accept the
82 % ceiling (`DEBUG_why-not-100-percent-2026-09-04.md`) and approved both: Step 1 — ship the
already-prepared backlog (no code change) — **SUBMITTED**: London job `1306951` (419), Lyon job `1306952`
(469), Madrid job `1306953` (1,008), each `--array=1-N%8 --time=7-00:00:00`, remote
`/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_backlog_2026-09-05/`, running in parallel with `T06`'s
Bologna tail. Step 2 — implement the pending (b)/(c) fixes (b1/b3/c1-c6, ≈+168 more, see
`debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT_claude-opus-5.md` §12.4) — **plan doc not
yet written**, next action.
Self-contained: nothing else has to be read to start.** Read §4 before touching
anything, §5 for where the work stands. Replaces `previous/DIRECTOR_PROMPT_european_locations.md` and
`previous/PROMPT_EU-18c_viewer_idf_plans_2026-09-01.md`. Shortened 2026-09-02; the full history stays in the plan
docs under `implementation/`.

---

## 0. The job

Every residential building in the four districts gets a floor plan — **thermal zones (flats) only, no circulation
zone** (`D-EU-79`, owner 2026-09-02) — cut from its own footprint. The owner's pipeline, verbatim: *"filter: dividing building floor plans into
the group · assign floor type: based on the floor groups assign floor types with circulation and thermal zones ·
reach 95 % floor assignment for all residential buildings"*.

Work **one group at a time**; never rebuild the fleet to test an idea (owner, twice: *"every time we are trying to
edit all buildings and we are consuming a lot of resources"*).

Deliverable: **one** file in `rules/` — **`RULES_dwelling_layout_groups_nocore_2026-09-03.html`** (the
`2026-09-01` core version and the `2026-09-02` six-check no-core version are both archived at
`rules/archive/`, `D-EU-79`/`D-EU-82`) — the owner's approved
layouts. It opens with a short `LAW` chapter (nine laws, one line each, with the check that measures them) followed
by the `GLOBAL` chapter (the same rules in plain language); the owner keeps both, ruled 2026-09-02: *"shorten the
LAW chapter, you started well but it turns out to be progress log, no i do not want that, simple and tidy. i like
both Law and Global chapters. ok continue with …09-01.html archive …09-02.html."* The regenerated
`…_2026-09-02.html` build is **archived to `previous/`** and is not the deliverable. Eleven sheets, one per
group; each shows the surveyed plate and the same plate cut into flats and a core, beside the filter, the plate
statistics, the circulation rule, the zone count and the scheme name. **The document is the specification.** Five
companion test sheets in `rules/tests/` (`TEST_01`…`TEST_05`) run the same rules over 550 real plates and grade
every one.

---

## 1. The eleven groups

Classifier: first match wins, terminal bucket last (`scripts/eu20_morphology_atlas.py:204`, mirrored in
`scripts/eu21/01_cut_group_plans.py:cls()`). Counts over the four districts, 2026-09-01.

| # | Group key | Shown as | Filter | Buildings | With a plan | Missing at 95 % |
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
| | | | | **2,544** | **541 (21 %)** | **1,876** |

Districts: `ES-MAD-BERRUGUETE` 961 · `FR-LYO-HAUTCOEURPENTES` 297 · `GB-LDN-STDUNSTANS` 82 · `IT-BOL-GALVANI2`
1,204. The 95 % bar is **2,417** buildings.

- Display names 07/08 are the owner's corrections and **display only** — keys `TRIANGLE`/`TRAPEZOID` never change
  (8 of 54 "triangles" have two long edges; all 87 "trapezoids" have four).
- `CORRIDOR_RECTANGLE` and `SLAB` are drawn at 3 dwellings/floor, not their true median of 2: `dwelling_count == 2`
  is a plain bisection with no corridor (`european_residential.py:1209`), so n=3 is the lowest count that shows
  their `i_shape_linear_gallery` scheme (`MIN_DRAW_TO_SHOW_SCHEME`, `01_cut_group_plans.py`).
- **No twelfth group is needed to reach 95 %** (census 2026-09-01, 2,544 rows): what predicts a real plan is flats
  per floor, not shape — ruled share k=1 **50.1 %** · k=2 23.0 · k=3 4.4 · k=4 3.2 · k=6–8 6.8 · k≥9 0.0. A new
  filter row only re-labels; the gap is the schemes' capacity to cut k ≥ 2 flats and survive the IDF writer.
  `COURTYARD` with ≥ 2 voids (98 buildings) needs a stated gallery rule, not its own row.

---

## 2. The floor-plan law — `D-EU-64`, ruled by the owner 2026-09-01

> *"generally circulation or core area is in the center … keeping the centered one as core zone and adding the
> other core zones inside the flats, it is highly possible … if there are extra spaces adding to the thermal zones
> (flats)."*

1. **One circulation zone per plate, and one only** — the interior piece, the one not along the outer wall.
2. **Every other pocket goes into the flat it adjoins** (largest shared area). A corner recess is room, not a stair.
3. **No unassigned space.** Flats + core = footprint; coverage ≥ 99.9 %.
4. **Drawn flat count = claimed flat count.** Fragments are welded until three flats draw `F1…F3`.
5. `SLIVER` is the one exception: zero circulation zones (direct street entry, private stair in each dwelling).
6. **A thermal zone is one connected room, not a room plus a tail** (owner: *"this divided space under the building
   can belong to the closest zone of F3"*). Erode each flat by 0.75 m; two pieces = a snake, split it. `unsnake()`.
7. **The core takes only what is corridor-shaped** (owner: *"we have some unwanted narrow zone which can be added to
   the corridor"*). A pocket folds into the core only if all three hold: narrower than 1.2 m; a ribbon *along* the
   core (mean width over the shared wall < 0.90 m); does not widen the core's band (its bounding rectangle grows by
   ≤ 2.5 × the pocket's area). `fold_narrow_to_core()`, `close_gaps()`; `CORE_GROWTH_CAP` (1.35) is a backstop.
8. **The wall between two flats is one straight line, wall to wall** (owner: *"look we have some unwanted edges"*).
   Each pair is re-cut on its own union so nothing else moves. Refused when the wall bends > 2.5 m round a wing, is
   < 1.5 m long, would move > 20 % of the smaller flat, or leaves a side as two rooms. `straight_cuts()`.
9. **The outer wall is surveyed and never redrawn.** Straightening applies to cuts *between* zones only; whatever a
   zone held within 0.35 m of the boundary is put back; no boundary vertex is ever dropped.
10. **No zone encloses another; every zone is one simple polygon** (owner: *"energyplus requires simple geometries,
    please solve these, simplify"*). The 1 mm collar round the core is gone (it had left nine of eleven plates with a
    flat holding the core as a hole); a pocket past several flats is shared by wavefront (`_share()`); a genuine ring
    (courtyard gallery) is cut open by `open_rings()`.
11. **A party wall facing two flats is one shared line across the plate**, not one line per pair.

All in `scripts/eu21/02_one_core_per_plate.py`. Two GEOS traps under 10–11: `unary_union()` over zones sharing an
exact edge can drop one whole and still report valid (`fuse()` adds one at a time and checks area); separately-cut
boundaries differ by a fraction of a mm and the weld drops one (`join()` bridges with a 2 cm close). The zig-zag
artefact from `absorb()`'s 0.20 m wavefront is cleared by `straighten()` + `dekink()`; dead ends in the debug
references.

Measured after 6–11, all eleven groups: no hole, no enclosure, zero snakes, zero overlap, coverage 99.98–100.01 %,
4–21 points per zone; circulation Courtyard 8.0 % · Sliver 9.0 · Square 9.0 · Rectangle 9.0 · Corridor 12.9 ·
Slab 16.3 · Triangle 9.0 · Trapezoid 9.0 · L 7.6 · U/T 6.9 · Complex 6.3 (L/U-T/Complex were 23/31/36 % with two
cores).

**Where this stands:** the law lived in the document as a post-pass; since 2026-09-01 the tests run the direct
cutter `scripts/eu21/05_group_cutters.py` instead. **The engine (`openubem/geometry/european_residential.py`)
still emits the extra pockets** — closing that gap is not ordered. Say so plainly.

---

## 3. Rebuild, tests, bookkeeping

Five scripts in `scripts/eu21/`, run from the repo root with `.venv\Scripts\python.exe` and
`PYTHONIOENCODING=utf-8` (bare `python` is the Windows Store stub):

```
01_cut_group_plans.py       # one real building per group, cut with the engine — DO NOT RUN
02_one_core_per_plate.py    # D-EU-64 post-pass — DO NOT RUN (not idempotent; group_plans.json is already post-02)
03_build_rules_html.py      # eleven-sheet HTML — 🔴 NOT WITHOUT THE OWNER'S OWN SENTENCE (writes the 2026-09-01 filename)
04_group_tests.py --test N  # N = 1..5 or all; rebuilds rules/tests/TEST_0N_*.html + EU-21/rules_tests/test_0N.json
05_group_cutters.py         # the direct cutter — the only file in the arc that draws; imported by 04
```

`04` is the only script run routinely; it overwrites that test's HTML and JSON, so rename first to keep a result
(`.cap8` / `.cap12` / `.t06` siblings exist for that reason). The rules document is **hand-maintained** while `03`
may not run (the `GLOBAL` and short `LAW` chapters were both inserted by hand, 2026-09-02). `03`'s own generated
`LAW` chapter is the long form the owner rejected as "a progress log" — if `03` ever runs again its output must be
cut back to the nine one-line laws before delivery.

`03`'s `SPEC` dict is the right-hand column of every sheet — a seven-step flow, not prose (owner: *"turn into
flowchart with bullet format rather than like a text … this flowchart format will help us when we apply them to the
coding"*): 1 Match · 2 Read the plate · 3 Place the circulation · 4 Cut the flats · 5 Absorb · 6 Close — accept only
if · 7 Scheme. Steps 5/6 are the shared constants `ABSORB`/`CLOSE` (the law); each group supplies
`match`/`plate`/`core`/`cut`/`scheme` as one-line bullets. CSS is read from the frozen 2026-08-28 document. Figures
for a `03` run come from the cutter into `group_plans_cutter.json` (`DD-9`); `group_plans.json` stays byte-identical.

Inputs: `openubem/outputs/eu_evidence/EU-20/morphology_census.csv` (2,544 rows) and `representatives.json`.
Engine: `generate_european_ruled_storey_layout` (`european_residential.py:1083`); `_DENSITY_GRID_TABLE` `:180`,
ceiling `RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 12` `:31`, `_merge_grid_cells` `:206`,
`generate_european_grid_layout` `:291`; proposed schemes at `:1478` / `:1557` / `:1608` / `:1736`.
`courtyard_gallery_ring` (a 1.80 m deck round the void) exists **only in `01_cut_group_plans.py`**, captioned as such.

**Per task:** one plan doc in `implementation/` (`PLAN_eu21-<slug>-<date>.md`, CLAUDE.md sections, fresh Sonnet
executors, director-signed checkpoints). Every solved error into `debugs/DEBUG_REFERENCES_european_locations.md`
(19 `[OPEN]` bullets, `LAW_GEOSException` among them). At every checkpoint update §5 here, the EU board
(`https://claude.ai/code/artifact/080bec44-ec13-4669-94db-8bb4a7a6763f`, republished in place) and the arc memory
pointer. Wider arc state lives in `STATE_european_locations_v5.md` and is not needed here.

---

## 4. Rules that are not negotiable

- **No EnergyPlus run of any kind without the owner's own sentence** (`D-EU-55`). A relayed "continue", an approved
  plan or a signed checkpoint is not permission. Writing geometry is fine; running it is not.
- 🔴 **Never regenerate or overwrite a delivered artifact without the owner's own sentence** — 2026-09-02, *"do not
  ever update anything unless i say so"*, after a `03` run replaced layouts he had approved. Every build takes its
  own dated filename; the reviewed one is never touched.
- **Never edit `rules/archive/RULES_dwelling_layout_scheme_2026-08-28.html`** (frozen; read its CSS, nothing
  more). It moved into `rules/archive/` on 2026-09-02; `04`/`06`/`07` resolve it by a path fallback.
- **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.** The dirty tree is the owner's.
- **Never write into `EU-17/` or `EU-20/`.** New evidence to `EU-21/` (tests to `EU-21/rules_tests/`). **Never
  regenerate `EU-21/rules_tests/baseline_2026-09-02/`** — the frozen pre-repair census.
- **No `.py` under `docs/`. Create nothing that was not asked for.**
- `circulation_pct_of_plate` is a **fraction**; any displayed share is `circulation_area_m2 / area_m2 * 100`.
- Executors are **fresh Sonnet sessions**, `model: "sonnet"` explicit, one dispatch per task, exact commands in the
  prompt. The director plans and audits; it does not write feature code.
- **A measurement task does not fix what it measures.** A refused, failing or raising plate is the finding: draw it,
  mark it, count it. No constant tuned, no building swapped, no filter added.
- **Density rulings are taken:** ceiling 12 flats/floor (`D-EU-65`), 9–10 cut on the `6x2` grid with column merges
  (`D-EU-66`), above 12 refuses by design. Test numbers 3/6/9/12 are flats per floor imposed on every group.
- **No check threshold is ever loosened to lift the census.** The census reads `test_01.json`…`test_05.json` only,
  **never globbed** (the `.cap8`/`.cap12`/`.postpass`/`.t06` siblings are history and inflate every count).
- Every owner ruling is quoted verbatim here and in the plan it governs; a relayed or paraphrased sentence is not a
  ruling.

---

## 5. Where it stands, and what is next

### 🔴 2026-09-05, ~15:10 — backlog wave `FAILED` tail reclassified: 4 signatures, not 1; new construction-mismatch bug found and handed to Gemini/Antigravity for diagnosis

**Read this block first; everything below it is history.**

Harvest-monitoring loop is otherwise unchanged (see the superseded ~14:20 block below for the schedules-bug
fix and job IDs). While polling, classified every currently-`FAILED` task's actual `eplusout.err`
(`Last severe error=` line, not just `sacct` state) instead of assuming they were all the known accepted
`FINDING 210` tail — that assumption was wrong. 24 `FAILED` tasks so far (Madrid 11/`1306953`, Bologna
12/`1305186`, London 1/`1306951`) split into **four** signatures:

- 13/24 (54%) classic `FINDING 210` `RoofCeiling:Detailed` vertex mismatch — accepted, no action.
- 3/24 (12.5%) `D-EU-43` zero/negative-surface-area sliver — accepted, no action.
- 🔴 **7/24 (29%) new: `EU_ROOF_CONSTRUCTION`/`EU_FLOOR_CONSTRUCTION` reverse-order material mismatch**
  (`FINDING 253`). Root cause identified, not fixed: `scripts/run_eu_s2_campaign.py:587-594` assigns
  constructions by nominal `Surface_Type` alone (never checking `Outside_Boundary_Condition`), and the roof
  vs. floor constructions are single-layer `MATERIAL:NOMASS` built from *different* U-values
  (`_envelope_construction`, line 453-457) — so wherever a shorter dwelling block's `ROOF` touches a taller
  neighbour's `FLOOR` (a massing/wing-height difference in the no-core/direct-cutter layout), the two sides
  can never satisfy EnergyPlus's interzone reverse-material check, regardless of geometry. This is
  deterministic, not `FINDING 210`'s GEOS-build floating-point fragility.
- 1/24 (4%) new `CalcCoordinateTransformation: Invalid dot product` fatal — not yet root-caused.

Full write-up: `OpenUBEM_debug_References.md` ("European locations, ceiling82 (2026-09-05)" chapter,
`FINDING 252`/`253`); plan doc `PLAN_eu-82pct-ceiling-2026-09-05.md` §8 "Backlog wave FAILED tail
reclassified" entry. **Handed to an external Gemini/Antigravity session** — read-only diagnosis + proposed
fix only, no production-code edits, no Speed resubmission — via
`prompts/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05.md`. Not a hard-rule-6 stop (disagreement is among
failure causes, not measured-vs-predicted recovery counts); harvest-monitoring loop continues in parallel,
no owner check-in needed per `D-EU-102`.

### 2026-09-05, ~14:20 — superseded by the block above; Step 2 delta wave v1 FAILED 100% (missing `schedules/`); fixed, resubmitted as v2, confirmed COMPLETING

The Step 2 delta wave submitted in the block below (`1307761`/`1307762`/`1307771`/`1307773`) failed
**317/317 (100%)** at sizing: `**Fatal** ProcessScheduleInput: Preceding Errors cause termination` —
`Schedule:File` CSVs under `../../schedules/<stem>/` not found. Root cause: the staged tarballs held only
`idfs/`+`weather/`+`fleet.lst`, omitting the `schedules/<stem>/` dirs every European IDF's `Schedule:File`
objects reference by relative path. Registered in `OpenUBEM_debug_References.md`, chapter "European
locations, ceiling82 (2026-09-05)".

**Fix, re-staged, resubmitted as v2** (same remote dirs, same counts 101/38/166/12, idfs/fleet/sched all
verified matching on extraction): `openubem_{district}_step2delta_v2` — London `1308150`, Lyon `1308159`,
Madrid `1308160`, Bologna `1308161`. **Confirmed fixed**: London (`1308150`) already has COMPLETED tasks
with `ExitCode 0:0`, 0 new FAILED.

**Other jobs, last polled ~14:15 (sacct):** London backlog `1306951` 418 COMPLETED/1 FAILED (done, accepted
`GetSurfaceData`/`FINDING 210` tail); Lyon backlog `1306952` 186 COMPLETED/8 RUNNING/1 PENDING; Madrid
backlog `1306953` 165 COMPLETED/11 FAILED (accepted `GetSurfaceData` tail)/8 RUNNING/1 PENDING; Bologna T06
`1305186` 415 COMPLETED/12 FAILED (accepted tail)/8 RUNNING/1 PENDING.

**Next:** continue the harvest-monitoring loop across all 8 jobs (30-min wakeups) until every one is
COMPLETED (modulo the small accepted `GetSurfaceData`-class FAILED tail), then harvest + regenerate 3D
viewers for all 4 districts, mirrored into `docs/docs_ACTIVE/europeanLocations/outputs_3D`. No owner
check-in needed per `D-EU-102` until harvest is complete or a stop-condition trips.

---

### 2026-09-05, ~13:35 — superseded by the block above; Plan `eu-82pct-ceiling-2026-09-05` T01-T07b done; stop point 3 closed at 79.9%; Step 2 delta wave SUBMITTED to Speed (v1, later found broken)

**Read this block first; everything below it is history.**

**Stop point 3 (plan §7 item 3), measured from one fresh `prepare()` rerun per district (idfs/weather/schedules
cleared first, `WinError 183` fix):**

| District | `population_prepared` |
|---|---:|
| `GB-LDN-STDUNSTANS` | 451 |
| `FR-LYO-HAUTCOEURPENTES` | 507 |
| `ES-MAD-BERRUGUETE` | 1,174 |
| `IT-BOL-GALVANI2` | 1,212 |
| **Total** | **3,344 / 4,186 (79.9%)** |

Against the ≈3,430/4,186 (≈82.0%) ceiling: residual gap **86 buildings (2.1 pp)**, inside the ~750 true dead
ends already classified in `DEBUG_why-not-100-percent-2026-09-04.md` — no further task targets them. Net
gain over the 3,096/4,186 (74.0%) Step 1 baseline: **+248**. Full entry: plan §8, "Stop point 3".

**Step 2 delta wave shipped.** The Speed-submission set is NOT `population_prepared_now - population_prepared_step1`
(T02's straddle-resolution churn means ids both entered and left each district's population) — it is
`comm -23` between each district's fresh `fleet.lst` and its Step 1 shipped `fleet.lst`. Real new-to-Speed
counts: London **101** (not 32), Lyon **38**, Madrid **166**, Bologna **12** — **317 total**, not 248.
Staged (0 missing), tarred, shipped, extracted (byte-count verified), submitted:
`sbatch --array=1-N%8 --time=7-00:00:00` via `submit_fleet_t08.sbatch` — London `1307761` (101), Lyon
`1307762` (38), Madrid `1307771` (166), Bologna `1307773` (12). Remote:
`/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_step2delta_2026-09-05/`. Confirmed RUNNING/PENDING via
`squeue`.

**Next:** harvest everything once drained — Step 1 backlog (`1306951`/`1306952`/`1306953`), Bologna's T06
wave (`1305186`), and this Step 2 delta wave (`1307761`/`1307762`/`1307771`/`1307773`) — then
`scripts/generate_eu_3d_viewers.py` for all 4 districts, mirror into
`docs/docs_ACTIVE/europeanLocations/outputs_3D` (`diff -rq` clean). No owner check-in needed per `D-EU-102`
until harvest is complete or a stop-condition trips.

---

### 2026-09-05, ~09:30 — superseded by the block above; `D-EU-101`: 82% ceiling accepted; Step 1 backlog SUBMITTED to Speed; Step 2 (code fixes) not started

**Read this block first; everything below it is history.**

**Owner ruling (`D-EU-101`, verbatim intent):** accept the 82 % ceiling from
`DEBUG_why-not-100-percent-2026-09-04.md` rather than chase 100 % via general imputation (rejected —
`OpenUBEM_imputation_methods.md` §6-7: `year_built`/`levels` imputation is aggregate-EUI-unbiased only,
IQR=0.0 per-building, and the EU arc simulates per-building). Owner approved both remaining steps in one
pass: ship the already-prepared backlog now, and implement the pending fixes toward 82 % next.

**Step 1 — ship the backlog (done, no code change needed).** Three districts already had prepared
IDFs sitting unshipped in `*_full_fleet_2026-09-04/` (Lyon, Madrid) and `*_full_fleet_epcyear_2026-09-04/`
(London) — recovered by prior fixes (`FINDING` 251/253/256) but never packaged because Speed submission
was sequenced to wait for `T06` to drain. Staged, tarred, uploaded and verified byte-count-exact on the
cluster, then submitted:

| District | Job | Array | Count (old → new) |
|---|---|---|---|
| `GB-LDN-STDUNSTANS` | `1306951` | `1-419%8` | 82 → 419 (+337) |
| `FR-LYO-HAUTCOEURPENTES` | `1306952` | `1-469%8` | 293 → 469 (+176) |
| `ES-MAD-BERRUGUETE` | `1306953` | `1-1008%8` | 952 → 1,008 (+56) |

Remote: `/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_backlog_2026-09-05/`. `--time=7-00:00:00` on all
three. Running in parallel with `T06`'s Bologna tail (still draining, ~29% at last poll). Fleet total once
both waves finish: **3,096 / 4,186 (74.0 %)** — the current recoverable-without-new-rulings ceiling, still
short of the 82 % target.

**Step 2 — implement the pending fixes (not started).** To close the gap from 74 % to ≈82 % needs code
changes, not just resubmission: b1/b3 (real fixes, +187: London EPC building-part year read already done
as part of `FINDING 256`... remaining is b3, Madrid Catastro `GetBuildingPartByParcel`, up to +163, one
authorised network probe) and c1-c6 (six rulings already pre-approved by the owner in this same pass, +168:
straddle-by-constraint-intersection +75, Lyon/Madrid 13-14 dwelling gap +38, London floor-dimension
storeys +33, `D-EU-58` tolerance +4, Bologna ISTAT tie policy +12, `residential` tag +6). Full ledger with
file:line citations: `debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT_claude-opus-5.md`
§§1-9 and §12.4.

**Next:** plan doc written (`implementation/PLAN_eu-82pct-ceiling-2026-09-05.md`, T01-T07, citations from the
investigation report). Dispatching a fresh Sonnet executor for T01-T02 now (narrow start per convention);
widen once it lands clean. In parallel, the standing poll should harvest Step 1's three jobs and Bologna as
each drains — no code needed for that.

**`D-EU-102` (2026-09-05, owner, verbatim intent): drive the whole arc to the 82% ceiling, *including all
simulations*, no further check-in needed — then regenerate `outputs_3D` for all four districts once
everything is harvested.** This pre-authorizes T07's live Catastro fetch (plan's own Stop point 2) — no
separate ask needed when that task is reached; still log the 163-id dry list per the plan's hard rule
before firing. Sequence to completion, no owner input required until harvest is done or a stop-condition
(plan §2 rule 6, >10% disagreement) trips: T01-T02 (dispatched) → widen to T03-T06 → T07 → rebuild/audit
the Step-2 delta fleet per district → package + ship a final Speed wave for the newly-recovered buildings
→ harvest everything (Step 1 backlog + Step 2 delta) → `scripts/generate_eu_3d_viewers.py` for all 4
districts → mirror into `docs/docs_ACTIVE/europeanLocations/outputs_3D` (diff -rq clean, per the arc's
standing mirror convention).

---

### 2026-09-05, ~05:33 — superseded by the block above; Madrid harvested (`T06`); Bologna is the last district still running

**Read this block first; everything below it is history.**

**Madrid (`ES-MAD-BERRUGUETE`) job 1305176 fully drained** (952/952 tasks, 0 pending/running) and harvested via
`scripts/cluster/harvest_eu11_remedy_campaign.py --district ES-MAD-BERRUGUETE`: **940/952 completed (rc=0), 12
failed, mean EUI 111.74 kWh/m².** 1,398 building rows written, 3D viewer regenerated (1,784,323 bytes) and
mirrored into `docs/docs_ACTIVE/europeanLocations/outputs_3D`. Manifest at
`openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE_finding249_remedy_2026-09-04/es_mad_berruguete_manifest.csv`.

**Remaining: Bologna only**, still running — last polled 2026-09-05 ~20:05 (sacct): 492/1,200 done (479
completed, 13 failed, 708 remaining). Lyon and Madrid both harvested (see the two prior blocks below for their
numbers). The standing poll loop continues unattended and will harvest + mirror Bologna the moment its
PENDING+RUNNING hits 0 — this is the last district in the campaign.

**Next:** wait for the standing poll to drain Bologna, plus the owner's Gemini investigation report — then
decide packaging/re-shipping the expanded fleet once the full campaign is done. Nothing else needs a check-in.

---

### 2026-09-05, ~04:01 — superseded by the block above; Lyon harvested (`T06`); Madrid/Bologna still running

**Read this block first; everything below it is history.**

**Lyon (`FR-LYO-HAUTCOEURPENTES`) job 1305167 fully drained** (293/293 tasks, 0 pending/running) and harvested via
`scripts/cluster/harvest_eu11_remedy_campaign.py --district FR-LYO-HAUTCOEURPENTES`: **292/293 completed (rc=0),
1 failed, mean EUI 83.75 kWh/m².** 768 building rows written, 3D viewer regenerated (877,535 bytes) and mirrored
into `docs/docs_ACTIVE/europeanLocations/outputs_3D`. Manifest at
`openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES_finding249_remedy_2026-09-04/fr_lyo_hautcoeurpentes_manifest.csv`.

**Remaining: Madrid and Bologna**, still running — last polled 2026-09-05 ~05:22 (sacct): Madrid 949/952 done
(937 completed, 12 failed, 3 remaining — 0 pending, 3 still running, about to drain), Bologna 291/1,200 done
(280 completed, 11 failed, 909 remaining). The
standing poll loop continues unattended, tightening cadence as either district nears draining, and will harvest
+ mirror each the moment its PENDING+RUNNING hits 0.

**Next:** wait for the standing poll to drain Madrid, then Bologna (last of the three), plus the owner's Gemini
investigation report — then decide packaging/re-shipping the expanded fleet once the full campaign is done.
Nothing else needs a check-in.

---

### 2026-09-04, later — superseded by the block above; `D-EU-37` ruled and implemented (`FINDING 255`); full-fleet gap handed to an external investigation; `T06` Speed campaign still running

**Read this block first; everything below it, including the `T06` block, is history for the campaign record only.**

**1. `D-EU-37` ruled.** Owner's own words: *"100% full"* / *"make it possible"* — option 1 (widen the rule)
taken, not option 2. Plan `implementation/PLAN_eu-d-eu-37-lyon-mfh-widen-2026-09-04.md` dispatched to a fresh
Sonnet executor, director-audited against the repo (diff + regenerated `summary.json`, not taken on trust).
New bucket `2<=dwellings<=12 & 5<=storeys<=9 -> MFH` added to `derive_bdtopo_building_type`
(`openubem/semantic/european_archetype_mapping.py:199-200`). Hit and resolved a pre-existing, unrelated
`schedule_dir.mkdir()` `FileExistsError` on re-run (script itself untouched; only the stale output subfolders
were cleared first — see plan doc §7a). Lyon `population_prepared` 293→469 (+176, exact match to `FINDING
254`'s measurement). **Fleet 2,890→3,066/4,186 (73.2 %).** Decision request ruled and archived:
`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-37_typology_table_extension_2026-09-04.md`.

**2. Remaining 1,120-building gap handed to an owner-run external investigation, not a further internal
dispatch.** Nine categories, exact counts and code citations:
`debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04.md` — the owner is running this one with Gemini.
Largest lever: London `MISSING_OBSERVED_EPC_AGE_BAND`/`PERIOD_STRADDLE_*` (800 of the 1,120). One genuinely
new, never-before-flagged category surfaced while writing it: Lyon+Madrid `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14`
(38 buildings, 13-14 dwelling buildings excluded regardless of storeys) — never investigated, may be another
`D-EU-37`-shaped policy call once Gemini's report comes back.

**3. `T06` Speed campaign progress (last polled 2026-09-05, ~03:50, sacct):** Lyon 291/293 done (290 completed, 1
failed, 2 remaining — 0 pending, 2 still running, about to drain), Madrid 852/952 done (840 completed, 12 failed,
100 remaining), Bologna 264/1,200 done (255 completed, 9 failed, 936 remaining). London harvested earlier (82/82,
mean EUI 87.34 kWh/m², see block
below). None of the three remaining districts have drained; a standing poll loop rechecks every ~30 min and
harvests + mirrors into `outputs_3D` the moment any one does — running unattended overnight, this block is
updated on each poll.

**Next:** wait for (a) the standing sacct poll to find a drained district and harvest it, and (b) the owner's
Gemini investigation report — then decide packaging/re-shipping the expanded (now 3,066-strong, and whatever
the investigation recovers on top) fleet once the live campaign fully drains. Nothing else needs a check-in.

---

### 🔴 2026-09-04 — `T06` Speed campaign SUBMITTED and RUNNING IN PARALLEL across all 4 districts; `T01`–`T04` complete

**Read this block first; everything below it is history.**

**1. Remedy and local validation complete (`T01`–`T04`).**
- `T01`/`T02`: Restricted Option B (partner-less near-duplicate vertex carve-out) implemented and unit-tested (17/17 green).
- `T03`: 16-building local EnergyPlus 23.1.0 regression validation **completed with 16/16 clean runs, 0 Fatal, 0 Severe, 0 errors** (`openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/T03_energyplus_validation_2026-09-04.json`).
- `T04`: Full 4-district `CP-2` gate-5 re-audit measured across all 2,262 emitted-family buildings:
  - Gates 1–4 **ALL PASS EXACTLY** (0 circulation zones, route counts == 2,279 `T05a` EMITTED, gross == conditioned for all 2,262, old-vs-new attributes 0/0/0).
  - Real dwelling layouts: **956 → 1,127 (+171 recovered)**.
  - Rerouted to massing: **1,306 → 1,135 (−171)** (reroute rate 57.7 % → 50.2 %).
  - Gate 5 still fails at 50.2 % (`FINDING 250`), but `D-EU-100` lifted the wait-for-`CP-2` gate on Speed submission.

**2. `T06` Speed cluster campaign submitted in parallel (`D-EU-100`):**
All four district fleets packaged and shipped via `scripts/cluster/ship_eu11_fleet.sh` to `/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_finding249_remedy_2026-09-04/` and submitted via SLURM array jobs (`sbatch --time=7-00:00:00 --job-name=openubem_<district> --array=1-N%8`):

| District | Tasks (N) | SLURM Array Job ID | Throttle | Progress (as of 15:28) | Status |
|---|---:|---|---|---|---|
| `GB-LDN-STDUNSTANS` | 82 | **`1305158`** | `%8` | **82/82 completed (100% clean, RC=0)**; mean EUI **87.34 kWh/m²**; `outputs_3D` updated | ✅ **HARVESTED & COMPLETE** |
| `FR-LYO-HAUTCOEURPENTES` | 293 | **`1305167`** | `%8` | 103 completed (35%), 8 running, 182 pending | **RUNNING** on `speed-[12,15,24,29,31-34]` |
| `ES-MAD-BERRUGUETE` | 952 | **`1305176`** | `%8` | 65 completed, 8 running, 10 failed geometry, 869 pending | **RUNNING** on `speed-[12,15,24,29,31,32,35,36]` |
| `IT-BOL-GALVANI2` | 1,200 | **`1305186`** | `%8` | 67 completed, 8 running, 2 failed geometry, 1,123 pending | **RUNNING** on `magic`, `speed-[12,15,24,33-36]` |
| **FLEET TOTAL** | **2,527** | | **24 concurrent** | **317 completed, 24 running, 12 failed** | **RUNNING IN PARALLEL** |

**Evidence:**
- Remote logs: `/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log`
- Task output directories: `/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_finding249_remedy_2026-09-04/out/<osm_id>/`
- Audit JSON: `openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/T04_gate5_reaudit_2026-09-04.json`
- Validation JSON: `openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/T03_energyplus_validation_2026-09-04.json`
- London harvested evidence: `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_finding249_remedy_2026-09-04/` (`summary.json`, `gb_ldn_stdunstans_manifest.csv`)
- London 3D viewer & data updated: `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_viewer.html` and `buildings.csv`
- Plan log: `docs/docs_ACTIVE/europeanLocations/implementation/DONE/PLAN_eu-nocore-finding249-remedy-2026-09-04.md` §8

**Next:** Antigravity update in progress; local monitoring stopped. Jobs continue autonomously on Speed. When Antigravity update is done, run `.venv/Scripts/python.exe scripts/cluster/harvest_eu11_remedy_campaign.py --all` to harvest Lyon, Madrid, and Bologna, and update their `outputs_3D` viewers.

---

### 2026-09-04, earlier — superseded by the block above; kept for the `D-EU-99` ruling record — root-cause `FINDING 249` first, Speed submission pre-authorised on gate 5

**Superseded — `T04` has since run and is reported in the block above (`FINDING 250`). Kept for the `D-EU-99` ruling text.**

**What the owner authorised, verbatim:** *"ok then prepare investigation plan to solve 5th gate for CP-2, and
then start execution"*, then *"i want to handle this one and submit the simulations on the speed, we are close
to 95% for each neighbourhood, in Madrid we already pass 95% threshold, we are ready to go, solve this last
pass of CP-2, and start simulations"*. Recorded as `D-EU-99`
(`STATE_european_locations_v5.md` §4): a dedicated investigation plan is authorised, and Speed submission is
pre-authorised contingent on `CP-2`'s fifth gate re-passing — mirroring `D-EU-98`'s pattern, no further
check-in required once it does. The 95 % coverage bar the owner cites is a different, already-cleared gate
(`D-EU-91`/`D-EU-96`); the only remaining blocker is `CP-2`.

**The plan:** `implementation/PLAN_eu-nocore-interzone-rootcause-2026-09-04.md`. Working hypothesis:
`generate_european_building_dwelling_layout` caches one independent `cut_storey_nocore` cut per distinct
per-floor dwelling count (`openubem/geometry/european_residential.py:2664-2698`) — two floors with *different*
counts get two structurally unrelated partitions of the same footprint, exactly the class of divergence
`FINDING 210`'s root-cause pass already found `intersect_match` resolves inconsistently. Untested by either of
`FINDING 249`'s two prior probes. `T01`/`T02` test it; `CP-1` (director) confirms/refutes and picks the remedy
shape; `T03`/`T04` implement and validate on a sample with real EnergyPlus; `T05` re-runs the full `CP-2`
gate-5 audit; `T06` (director only) builds and submits to Speed if gate 5 passes — pre-authorised, no separate
ask needed. A gate-5 failure stops at `T05` and is reported, not worked around.

**Status when this block was written:** plan created, execution not yet started.

---

### 🔴 2026-09-03, late evening — superseded by the block above for the "what next" decision; kept for the `CP-2` measurement record. **`CP-2` FAILED. Nothing was submitted.** `FINDING 249`

**Read this block first; everything below it is history, including the block that told a fresh session to launch
the campaign.**

**What you authorised.** *"ok lets do it that way, it looks like it will take some time, so what is my suggestion
is that you continue to build and submit simulations, i will sleep, i can not wait, and once you submit the tasks
update the prompt of manager. thank you."* Recorded as **`D-EU-98`**: `T06` passed to the director, `CP-2`
**not** waived, prompt updated afterwards. This is that update.

**What happened while you slept.** All four districts rebuilt (Madrid 21:16, London 21:22, Lyon 21:27, Bologna
21:54). The `CP-2` audit ran on the rebuilt trees, not on any agent's report. **Four of its five gates pass
exactly. The fifth fails, and it is the one the carry-in exists for. Per `D-EU-98` clause 2 the submission was
stopped: no `sbatch` was issued, the Speed queue is untouched, and no delivered artifact was overwritten.**

| `CP-2` gate | result |
|---|---|
| zero `*_circulation` zones in every IDF | **PASS** — 0 in all four districts |
| route counts == `T05a`'s `EMITTED` | **PASS** — fleet **2,279 = 2,279**, exact per district |
| gross == conditioned area for every emitted building | **PASS** — 2,262 of 2,262, worst deviation 0.0000 |
| old-vs-new `prepared_buildings.csv` diff (the mandatory Bologna live-API check) | **PASS** — `archetype_id`/`building_type`/`age_band` **0/0/0** on 2,527 rows, no new building |
| the dwelling layout is actually written into the IDF | 🔴 **FAIL** |

**The failure, in one paragraph.** The extracted no-core cutter is *better* than the core-era logic: fallback
collapses **1,096 → 265**, so it divides 831 plates the old logic refused. But `FINDING 210`'s safety net
(`_force_reroute_room_layout_to_one_zone_per_floor`, `scripts/run_eu_s2_campaign.py::build_idf_for_building`)
fires on **1,306** buildings against **2** in the delivered build, because geomeppy's `intersect_match` cannot
resolve interzone vertex mismatches on the finer no-core subdivision. Every time it fires **the dwelling layout
is thrown away** and the building is rebuilt as one whole-building zone per storey — while `geometry_outcome`
still reads `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`. Net:

| | delivered (core-era) | rebuilt (no-core) |
|---|---|---|
| **real dwelling layouts** | **1,446** | **956** (−490) |
| rerouted to per-storey massing | 2 | **1,306** |
| fallback | 1,096 | 265 |
| no IDF at all (`IDF_ASSEMBLY_FAILED_RuntimeError`) | 0 | 17 |

Per district, real dwelling layouts: Madrid **614 → 278** · Lyon **198 → 157** · London **40 → 22** ·
Bologna **594 → 499**. Verified in the IDFs on 32 sampled stems, not read off the label: real buildings carry
`_F<n>_dwelling_<k>` zones (up to 69), rerouted ones carry only `_F<n>_whole` and **zero** `_dwelling_` zones.

**Why this had to stop the submission.** A campaign launched tonight would have reported 2,279 buildings as
carrying emitted dwelling layouts while **57.7 % of them had no dwelling subdivision at all**, and would have
done it on *fewer* real layouts than the build already on disk. That is exactly what `CP-2` was written to catch.

**Evidence.** `openubem/outputs/eu_evidence/EU-21/engine_parity/idf_audit_2026-09-03.json` (every number above,
recomputed) · `EU-11/<DISTRICT>_nocore_2026-09-03/` · `STATE_european_locations_v5.md` §3 `FINDING 249` ·
`implementation/PLAN_eu-engine-nocore-carryin-2026-09-03.md` §8 `T05` · debug refs `FINDING 210` chapter.

**What was *not* done, deliberately.** No threshold moved. `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` (0.005) and
`COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (0.1) left as tuned. `MAX_FLAT_ASPECT` still **2.5**. Nothing regenerated
under `EU-11/<DISTRICT>/`, `EU-17/` or `EU-20/`. `D-EU-54` still unconsumed.

**Waiting on you — one decision.** Two probes (dwelling count `k`, footprint complexity) failed to separate the
rerouted from the clean, so the mechanism is inside `intersect_match`'s post-extrusion vertex arithmetic and
finding it is real work. The options:

- **(a) Root-cause the reroute** before any campaign — dispatch a fresh Sonnet to pull the mismatching surface
  pairs on a handful of rerouted stems and find why the no-core density triggers it. **Recommended**: it is the
  only path that ships the layouts the seven checks proved.
- **(b) Submit as-is**, with the 1,306 relabelled honestly as per-storey massing and the result reported that
  way — a valid fleet run, but not the no-core result, and worse than the delivered build on layout coverage.
- **(c) Submit the delivered core-era IDFs** instead and treat the carry-in as unfinished.

**Waiting on you: `D-EU-99` — recommend (a).**

---

### 2026-09-03, evening — superseded by the block above; kept for the `D-EU-96` ruling and the `T01`–`T05a` record

**Superseded.** The instruction in this block to launch the campaign was executed as far as `CP-2` and stopped
there. `D-EU-96` and the `FINDING 246` oracle paragraph below both still stand.

**The owner's sentence, verbatim:** *"this will be last trial, and if we can not reach 95% for every
neighbourhood, no worries, this level is enough itself, i beleive we can start simulations when the agent finish
its job, update this one … then i will continue with fresh session for simulations"*.

**`D-EU-96` — the 95 % bar is retired as a requirement.** The owner accepts the `_r5` coverage as delivered:
Madrid **95.3 %** · Lyon **94.6 %** · Bologna **90.1 %** · London **86.6 %**, fleet **92.5 %** (2,353 of 2,544).
No further colour-repair trial is ordered, and the three districts below 95 % are **not** a blocker any more.
Three things this ruling does **not** touch: `MAX_FLAT_ASPECT` is still **2.5** and may never be moved
(`D-EU-84`, `D-EU-86`); no check threshold is loosened; and `CP-2` still gates the submission — the owner's
"when the agent finish its job" is exactly that gate, not a waiver of it.

**Where the carry-in stands** (`implementation/PLAN_eu-engine-nocore-carryin-2026-09-03.md`, `D-EU-95`):

- ✅ **`T01`** — the cutter extracted to `openubem/geometry/european_nocore.py` (1,731 lines). **Never edit it.**
- ✅ **`T02` → `CP-1` SIGNED** — `scripts/eu21/09_engine_parity.py`, **2,529 plates compared, 0/0/0/0
  mismatches**, `input_missing` 0. The first run failed 1/0/53/51 on a **harness input defect of the director's
  own specification** — it re-fed `plate["footprint"]`, the cutter's mm-snapped *output*, as the input; the
  cutter picks its winner by strict `>` over a 3-decimal score tuple (`07_nocore_tests.py:970`), so a sub-mm
  perturbation selects a different partition (**`FINDING 247`**, recorded, deliberately **not** repaired). The
  corrected harness reads `geoms[(district, building_id)]` from `M07.load_universe()`.
- ✅ **`T03`** — the engine seam: `generate_european_nocore_storey_layout` + `EUROPEAN_LAYOUT_REGIME = "nocore"`
  in `european_residential.py`. The zone-spec writer was **not touched** — it emits a circulation zone only when
  `circulation_polygon is not None`, and no-core always passes `None`. The corridor path is parked behind
  `"ruled"`, not deleted.
- ✅ **`T04`** — regression sweep **6 failed / 613 passed**, identical to the pinned pre-seam baseline; the six
  are all class (a) and pinned with `monkeypatch.setattr(module, "EUROPEAN_LAYOUT_REGIME", "ruled")`. **No
  assertion was loosened.**
- ▶ **`T05a`** — the engine's own building-level census, running as a detached process
  (`scripts/eu21/10_engine_census.py`), writing
  `openubem/outputs/eu_evidence/EU-21/engine_parity/engine_census_2026-09-03.json`. Expect ~1–2 h.
- ▶ **`T05`** — the four districts' IDFs rebuilt into **new** directories
  `EU-11/<DISTRICT>_nocore_2026-09-03/`, dispatched to a fresh Sonnet 2026-09-03 20:52. Its audit lands at
  `EU-21/engine_parity/idf_audit_2026-09-03.json`.

**First actions of the fresh session — check the disk, do not chase the old agents (their ids die with the
session that spawned them):**

```
ls openubem/outputs/eu_evidence/EU-21/engine_parity/
ls openubem/outputs/eu_evidence/EU-11/*_nocore_2026-09-03/prepared_buildings.csv
```

If `engine_census_2026-09-03.json` is missing, re-run it detached:
`.venv\Scripts\python.exe scripts/eu21/10_engine_census.py`. If the four `_nocore_2026-09-03` directories are
missing or partial, re-dispatch **`T05` only** (plan §6, lines 422-482) to a fresh Sonnet — never point the
campaign at the delivered `EU-11/<DISTRICT>/` folders, which are read-only (`D-EU-85`).

**🔴 `CP-2` is the last gate, and its oracle changed.** The earlier line "the IDF route counts must read Madrid
916 · Lyon 281 · London 71 · Bologna 1,085" is **wrong and must not be used** — those are `_r5`'s *per-plate*
`PASS` figures. **`FINDING 246`:** the census cuts **one `k` per building**; the engine cuts **one `k` per
storey**, and **1,814 of 2,544 buildings (71.3 %)** carry more than one distinct count, so they carry a floor
plan only if **every** count passes. The oracle for the IDF route count is therefore **`T05a`'s own `EMITTED`**,
and `_r5`'s `PASS` is reported **beside** it as a labelled comparison, never in place of it, in either
direction. Sign `CP-2` on: zero `*_circulation` zones in every IDF · `DWELLING_LAYOUT_EMITTED` count ==
`T05a`'s `EMITTED` · gross == conditioned area for every emitted building · dwelling conservation on the
sample · and the old-vs-new `prepared_buildings.csv` diff clean on `archetype_id` / `building_type` /
`age_band` (Bologna reaches an **uncached live API** at `run_eu_s2_district_campaign.py:198-226`, so a rebuild
can silently move an archetype — that diff is not optional).

**Then `T06`, the campaign — director only, after `CP-2` is signed.** `D-EU-55` is satisfied by the owner's own
sentence of 2026-09-03; `D-EU-96` removes the coverage condition. Re-check `squeue -u o_iseri` immediately
before submitting (it read **0 jobs** at 2026-09-03).

```
scripts/cluster/ship_eu11_fleet.sh <DISTRICT>_nocore_2026-09-03      # $1 resolves LOCAL_DIR, script unedited
sbatch --time=7-00:00:00 --array=1-N%8 --export=FLEET_DIR=EU11_<DISTRICT>_nocore_2026-09-03 submit_fleet.sbatch
```

🔴 **Never the login node** — no `srun`, no `ssh … python`; `mkdir`/`scp`/`tar`/`squeue`/`sacct` only. Every
remote command through the `_ssh()` helper (`scripts/cluster/t08_harvest_results.py:104`); the remote shell is
tcsh and bare bash fails silently. `--time=7-00:00:00` **on the CLI** — `submit_fleet.sbatch` bakes in
`01:30:00` and is shared, so it is **not** edited. Fire and forget, then read the output files.

🔴 **`FINDING 248` — 107 of the 2,544 census buildings are almost certainly not residential** (> 500 m² GFA per
declared dwelling; Madrid 50 · Bologna 47 · London 8 · Lyon 2; `IT-BOL-GALVANI2/30090` carries 4,382 m² per
dwelling). They entered at **EU-02**, in `02_residential_manifest.gpkg`, and 85 of them **pass** all seven
checks, so they are invisible in the coverage figures and will be simulated as apartment blocks. This is a
simulation-accuracy question, not a coverage one, and the fix — if ordered — belongs upstream at the EU-02
manifest, **never** in the cutter. **Excluding them does not lift the census**: measured, the best case is
+1.3 points (Bologna 90.1 → 91.4 %, by dropping 19 % of the district) and **London falls** at every threshold.
Nor can OSM identify them — Bologna is 1,202 of 1,220 rows tagged `Edificio generico`, no use information at
all, so any exclusion would be a density heuristic, i.e. a new modelling assumption. Full measurement and the
four-threshold table in `STATE` §3.

✅ **`D-EU-97` settles it — they stay in, flagged, not excluded** (owner: *"no need to trying to include as many
buildigns in the system, lets keep it that way"*). No exclusion filter is added anywhere, no further coverage
effort is spent. But **never quote a per-dwelling or per-area result for these 107 as a residential figure**,
and never present the fleet EUI without noting that 4.2 % of the stock is of unverified use. Ruling in
`STATE` §4.

**Next free `D-EU-98` / `FINDING 249`.**

---

### 2026-09-03, earlier — the owner ordered the run and left; `D-EU-95` ruled; the engine carry-in opened

**History — superseded by the block above. `D-EU-95` and the task order in it still stand.**

**The owner's sentence, verbatim:** *"lets go, to the end, no more ask, when you are satisfied, start
simulations, i will go out i please continue"*. This is the owner's own sentence for `D-EU-55` — but it is
**conditional on the director being satisfied**, and `D-EU-94` clause 3 says exactly why the director is not:
the engine is core-era. So the order is executed in the only order that makes it true: **engine first, then
the campaign.** Do not read "no more ask" as permission to skip the two checkpoints — it is permission to stop
asking the owner, not permission to stop measuring.

**Running now:** `implementation/PLAN_eu-engine-nocore-carryin-2026-09-03.md`, opened 2026-09-03, one fresh
Sonnet executor on `T01`–`T02`, stop at `CP-1`.

**`D-EU-95`, ruled by the director (full text in `STATE` §4).** The carry-in is an **extraction, never a
re-implementation**: the proven cutter is copied body-for-body out of `scripts/eu21/07_nocore_tests.py`
(sha `fe75c96e…`, never edited) into a new `openubem/geometry/european_nocore.py`, and the acceptance test is
**bit-parity with `_r5`** — same verdict, same flat count, same seven check strings, same geometry to
`1e-6 m²`, on all 2,544 census plates, **0 mismatches or the plan does not continue**. Parity is two-sided:
the engine may not pass a plate `_r5` failed any more than fail one it passed. The corridor path is parked
behind `EUROPEAN_LAYOUT_REGIME = "ruled"`, not deleted (`D-EU-79`). A failing storey returns
`dwelling_layout_emitted=False` and the building takes the existing massing box — no partition is ever
emitted that the seven checks refused.

**The seam, measured, not guessed.** The whole IDF path funnels through one per-storey function,
`generate_european_ruled_storey_layout` (`european_residential.py:1083`), called by
`generate_european_building_dwelling_layout:2619`. And `european_building_layout_to_zone_specs:2751` emits the
unconditioned circulation zone **only** when `circulation_polygon is not None`. So a no-core layout reaches the
IDFs with **no edit to the zone writer at all** — the carry-in is one new function plus one routing switch.

**Task order:** `T01` extract · `T02` parity harness → **`CP-1`** · `T03` engine seam · `T04` regression sweep
over `tests/geometry/` + `tests/test_eu*.py` · `T05` rebuild the four districts' IDFs into **new** dated
directories `EU-11/<DISTRICT>_nocore_2026-09-03/` (`D-EU-85` — the delivered 961/297/82/1,204-IDF folders are
read-only) → **`CP-2`** · `T06` the Speed campaign, **director only**, `sbatch --array` with
`--time=7-00:00:00` **on the CLI** (`submit_fleet.sbatch` bakes in `01:30:00` and is not edited), never the
login node, `_ssh()` helper for every remote command.

**`CP-2` is where "satisfied" is defined:** ~~the four IDF route counts must read Madrid 916 · Lyon 281 ·
London 71 · Bologna 1,085~~ — **withdrawn by `FINDING 246`, see the head block: the oracle is `T05a`'s
`EMITTED`, not `_r5`'s per-plate `PASS`.** The zero-`*_circulation`-zone assertion stands unchanged.

*(Next-free as of this block was `D-EU-96` / `FINDING 246`; both are now taken — see the head block.)*

---

### 2026-09-03, earlier — `CP-4` accepted, `_r5` is live, **the 95 % gate is MET in Madrid**

**History — superseded by the block above, but every number in it still stands.**

`PLAN_eu21-colour-repair-2026-09-03.md` is COMPLETE through `T07` and its rebuild, both logged in its §8.

**What was delivered — `_r5`.** Tag `2026-09-03_r5`, cutter sha
`fe75c96ed0ad8512a72c93fccd27b7e46b05c325911163bb47e41b1932a85717` (**identical in all four JSONs**),
`MAX_FLAT_ASPECT = 2.5` **unchanged**, `error = 0` ×4, no `ERROR` status anywhere:

| District | Census | Drawn | PASS | PASS % | Bar | Refused |
|---|---:|---:|---:|---:|---|---:|
| `ES-MAD-BERRUGUETE` | 961 | 955 | **916** | **95.3** | 913 — **CROSSED, +3** | 6 |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 295 | 281 | 94.6 | 283 — 2 short | 2 |
| `IT-BOL-GALVANI2` | 1,204 | 1,204 | 1,085 | 90.1 | 1,144 — 59 short | 0 |
| `GB-LDN-STDUNSTANS` | 82 | 75 | 71 | 86.6 | 78 — 7 short | 7 |
| **FLEET** | **2,544** | **2,529 (99.4 %)** | **2,353** | **92.5** | 2,417 — 64 short | **15** |

`fail_by_check` fleet: `C11` **76** · `C10` 55 · `C5` 30 · `C4` 13 · `C6` 11 · `C1` 0 · `C3` 0 — every
check except `C11` identical to `_r4`, `C11` alone 263 → 76. PASS delta **+175**, matching the pre-build
projection district for district. **No-regression: 0 of 2,178.** `plans3D/index.html` opens the four
`_r5` pages; `_r4`, `_r3`, `_r2` and the baselines are all in `plans3D/archive/`, none overwritten.

**🔴 What this means.** `D-EU-91`/`D-EU-94`'s condition — **any one** district ≥ 95 % of census plates
passing all seven checks, read on `PASS` — **is satisfied by Madrid.** The simulation authorisation is
therefore live, and no threshold was moved to get there.

**🔴 What it does not mean — do not submit anything.** `D-EU-94` clause 3 stands unchanged:
`openubem/geometry/european_residential.py` is still core-era (2,920 lines, 116 × "core", 26 ×
"corridor", **0** × "nocore"). A campaign submitted today would simulate core-and-corridor layouts, not
these plans, and would reproduce `FINDING 213` at fleet scale. **The engine carry-in is now the single
critical path.** `D-EU-54` — the owner reads `plans3D/` and confirms — is also still unconsumed, and is a
separate gate that this result does not satisfy.

**What closing the remaining three would take, measured, not estimated.** Lyon needs **2** plates
(1 `C4`, 5 `C5`, 1 `C6`, 3 `C10`, 5 `C11` remain — any two repaired suffices; the cheapest of the three).
Bologna needs **59** and holds exactly 59 `C11` failures at `k >= 2` plus 27 `C10` and 20 `C5` — the
thick-band courtyard rings and dense multi-wing plates whose wings do not separate under `lobes_of`,
i.e. the `FINDING 242` residual, unchanged in nature since 2026-09-02. London needs **7** but only 4 of
its 11 misses are check failures — **7 are `k > 12` refusals**, so London cannot cross through the checks
at all and would need the refusal path reopened past `D-EU-92`. **None of this may be resolved by moving
`MAX_FLAT_ASPECT`** (`D-EU-84`, `D-EU-86`).

**Carried, unstarted, in the owner's order:** the written rules into
`openubem/geometry/european_residential.py` (**now the critical path**); the 939-building IDF-writer
demotion; the `scripts/eu21/04_group_tests.py` archived-filename housekeeping; the Bologna 7 / London 1
`FINDING 243` roster reconciliation. Before `EU-19` is ever prepared: confirm the Speed queue is empty,
`sbatch --array` only, `--time=7-00:00:00` minimum, never the login node.

*(Superseded: the carry-in is no longer unstarted — see the head block. Next free is `D-EU-96`.)*

---

### 2026-09-03, night — `eu21-colour-repair` at `CP-3`; `_r4`; the 95 % gate proved unreachable and `D-EU-93` opened for the owner

**History — superseded by the block above.**

**Nothing is running.** Both executors are closed. `PLAN_eu21-colour-repair-2026-09-03.md` reached `CP-3`
with all six tasks (`T01`–`T06`, plus the director-added `T05b`) logged in its §8.

**What was delivered.** `_r4` (cutter sha `9a27c65fba56…`, `MAX_FLAT_ASPECT = 2.5` unchanged, `error = 0`
×4): fleet PASS **2,012 → 2,178**, 79.1 % → **85.6 %**; refused **23 → 15**; drawn 2,521 → 2,529. Per
district: Madrid 867/961 (90.2 %) · Lyon 264/297 (88.9 %) · Bologna 982/1,204 (81.6 %) · London 65/82
(79.3 %). **No-regression gate: 0 of 2,012** — checked id by id. `plans3D/index.html` now opens the four
`_r4` pages; `_r3`, `_r2` and the baselines are all still linked and untouched.

**How the gain was obtained — this matters more than the number.** No threshold moved. The seven checks and
their values are identical in both builds. What changed is the candidate search: more cut bearings
(long-edge and reflex-bisector), reflex-vertex boundary snapping, courtyard-ring bisection at low `k`, and
`D-EU-92`'s attempt-instead-of-refuse for `k > 12` (8 of 23 passed, one at `k = 31` — the `D-EU-65` cap had
never once been tested against the cutter).

**🔴 The gate cannot be met — `FINDING 245`.** Of the 263 plates still failing `C11`, **187 have `k = 1`**,
where the single flat *is* the plate, so `C11` reads the footprint, not the cut. District ceilings, assuming
every other failure were repaired: Madrid ≤ 94.8 % · Lyon ≤ 94.3 % · Bologna ≤ 90.5 % · London ≤ 92.7 %. All
below 95 %. **`D-EU-91` is therefore not met in any district and `D-EU-55` still bars every simulation.**
A strip-bound classifier was tried first and **falsified on the control set** (2 of 200 known-passing plates
wrongly called forced); its 175/88 split is withdrawn and must never be quoted.

**The one open decision — `D-EU-93`, the owner's alone.** Does `C11` apply at `k = 1`? The director's
recommendation is no, on the ground that `C11` scores a division and at `k = 1` no division is made; the
alternatives are to accept the gate below 95 % or not to simulate. **Do not resolve this by moving
`MAX_FLAT_ASPECT`** (`D-EU-84`, `D-EU-86`) and do not treat the recommendation as taken.

**Carried, unstarted, in the owner's order:** the written rules into
`openubem/geometry/european_residential.py`; the 939-building IDF-writer demotion; the
`scripts/eu21/04_group_tests.py` archived-filename housekeeping; the Bologna 7 / London 1 `FINDING 243`
roster reconciliation. Before `EU-19` is ever prepared: confirm the Speed queue is empty, `sbatch --array`
only, `--time=7-00:00:00` minimum, never the login node.

---

### 🔴 2026-09-03, same day, earlier — the owner wants the coloured buildings **fixed**, not described; `eu21-colour-repair` dispatched; the simulation gate armed (`D-EU-91`)

**What the owner said, and what it changed.** Shown the `_r3` pages, the owner's point was blunt: *"still i am
seeing red, orange and purpule colors … the aim was to solve their issues convert them to green?"* and *"that is
why we created these"* — the three `debugs/DEBUG_district_*_2026-09-03.md` reports. They were right, and the
previous block was wrong in emphasis: those reports **diagnosed** and the previous session **logged what was not
built**. Only purple was actually fixed. Two owner sentences followed and are now rulings:

- *"about orange continue as you progress … to solve as much as orange buildings, lets go"* → **`D-EU-92`**
  (`STATE` §4): the `k > 12` refusal at `08_district_viewer.py:165-169` fires **before the cutter is called**, so
  it was a declared ceiling, never a measurement. It becomes an *attempt*: cut at the declared `k`, run the same
  seven checks, refuse only what fails. `k` itself is still untouchable (`D-EU-88` clause 1) — the clamp the
  orange report's Tier 1 wanted stays forbidden, and the director recommended against it.
- *"if you reach 95% floor division any of the neighbourhood, start simulations, lets go"* + *"no need to ask me,
  aim is the reach 95% for floor dicison, and then simualtions"* → **`D-EU-91`**. This is the `D-EU-55`
  authorisation, **conditional**: the campaign starts only when one district reaches **≥ 95 % of its census
  plates passing all seven checks**. 🔴 **Read on `PASS`, never on `drawn`** — drawn is 99.1 % fleet-wide already,
  so a drawn reading would make the owner's condition vacuous the day they wrote it. `_r3`: Madrid 83.6 % · Lyon
  83.2 % · London 61.0 % · Bologna 75.7 %. **The gate is open, not met.**

**The true `_r3` colour state, measured from the four `*_r3.json` `summary` blocks:** purple (`ERROR`) **0** —
solved; orange (`REFUSED_K_GT_12`) **23** (Madrid 7 · Lyon 3 · London 13 · Bologna 0); red (`FAIL`) **509**, by
check `C11` **291** · `C10` **168** · `C5` **74** · `C4` **13** · `C6` **11** · `C1` 0 · `C3` 0; green 2,012 PASS
+ 1,642 generic.

**In flight:** `implementation/PLAN_eu21-colour-repair-2026-09-03.md`, one Sonnet executor on **T01–T04**, stopping
at `CP-2`. T01 is a bench that must reproduce the `_r3` failing set exactly before anything is changed; T02–T04
broaden the cut-candidate search (more cut angles, reflex-vertex snapping, ring bisection) **without moving the
judge** — `_plate_score`/`_fully_ok` are frozen, so a new candidate can only win or be discarded and no passing
plate can regress. T05 is the orange attempt, T06 rebuilds the four districts as `_r4`.

🔴 **The honest ceiling, stated in the plan and not to be softened.** `C11` is the largest bucket and its
proposed fix was a `k = 1` sliver *exemption* — barred by `D-EU-84`/`D-EU-86`. A genuinely slender plate yields
slender flats; no search improvement fixes that. The red report's "≥ 98 % PASS" line is its executor's projection
and is **not** an acceptance criterion. Whether 95 % is reachable at aspect 2.5 without loosening a rule is an
open question, and the answer may be no — in which case the owner gets that sentence, not a quiet threshold move.

**Next free `D-EU-93` / `FINDING 245`.**

**Read this block first; everything below it is history.** The `_r3` dispatch of the previous session
**did finish** before that session ended: four pages + four JSONs written 15:52–15:53. Audited this
session, from the artifacts:

- **Acceptance met (`D-EU-89` clause 3): `error = 0` in all four JSONs.** All four carry
  `tag = 2026-09-03_r3`, `cutter_sha256 = 76a124bfda43…` — the sha256 of `scripts/eu21/07_nocore_tests.py`
  as it stands on disk — and `max_flat_aspect = 2.5`. `_r2` was sha `d1fa6bd007bf…` / 4.0, so the two
  builds are distinguishable at the footer as §7 of that plan requires.
- **Fleet `_r3`: 2,521 / 2,544 drawn (99.1 %), 2,012 PASS all seven (79.1 %), 23 refused, 0 error,
  1,642 generic.** Madrid 954/803 · Lyon 294/247 · London 69/50 · Bologna 1,204/912. Failing checks
  `C11` 291 · `C10` 168 · `C5` 74 · `C4` 13 · `C6` 11 · `C1` 0 · `C3` 0.
  **Never quote 99.1 % as "passing" — drawn ≠ PASS, and PASS fell from `_r2`'s 87.9 % because `C10`
  and `C11` were tightened by ruling (`D-EU-87`, aspect 2.5), not because the cut got worse.**
- Page gates re-run on all four `_r3` pages: `Dwelling Index` = 1, `srcdoc` = 0,
  `kwh|eui|energy|archetype` = 0.
- **Its progress entry was missing** (the executor died with the session before writing it) and is now
  written by the director in that plan's §8, titled `T05 — _r3 rebuild (per §5 spec)`, beside the
  pre-existing mislabelled `T05 Generic No-Census Fallback` entry, which is annotated in place as a
  title collision — a bookkeeping note, no `D-EU`/`FINDING` number.

**The three debug reports now carry a §6 progress log** (`debugs/DEBUG_district_{red,orange,purple}_…md`),
each stating what was implemented, what was not, and the ruling that blocks it. One correction of record:
the 17 `FINDING 243` buildings verified one by one in `_r3` read **16 `direct` (9 PASS / 7 FAIL on ordinary
check grounds) + 1 `GENERIC_NO_CENSUS`** (London `way/398158941`, no census row in that build) — **not**
"17/17 direct" as the earlier handoff said. Zero raise.

**Nothing is running. Next free `D-EU-91` / `FINDING 245`.**

**The `_r2` pages are archived; `_r3` is live.** Owner's sentence 2026-09-03: *"lets archive r2 versions"* —
the `D-EU-85` authorisation the item below was waiting on. The four `PLANS_*_nocore_2026-09-03_r2.html` were
**moved** (never deleted, never overwritten) to `plans3D/archive/`, beside the `_r1` baselines;
`plans3D/index.html` now opens the four `_r3` pages, with `r2 · baseline` in its archive column and a footer
stating the active build and that drawn ≠ passing. All 12 hrefs verified to resolve. Citation sweep done and
recorded in `PLAN_eu21-district-viewer-2026-09-03.md` §8 ("Archive pass"). The `_r2`/`_r1` **JSONs** in
`openubem/outputs/eu_evidence/EU-21/district_plans/` stay put — they are the cited evidence for the `_r2`
numbers in `STATE_european_locations_v5.md` §3. There is now **no open decision** in this arc.

**Next, in the owner's order** (`STATE_european_locations_v5.md` §7): carry the written rules into
`openubem/geometry/european_residential.py` · close the 95 % gap, biggest group first · the 939-building
IDF-writer demotion (separate defect).

### 🔴 2026-09-03, later still — `T06`/`T07` re-audited clean; district-viewer's real `T05` (`_r3`) dispatched, not yet confirmed done; owner is switching sessions

**Read this block first; it supersedes the "later" block immediately below (kept for history).** Owner's
words: *"...i will go outside i am giving yo to go until the end, thank you"* (still governing — implement the
three debug reports' cutter fixes onto the two plans, rebuild `plans3D` `_r3`, update the three debug
reports' progress logs), then, this session: *"before do that, i want to continue with new session, can you
update this one ... i will like to continue with new session."*

**`T06`/`T07` independently re-verified against disk this session** (the block below already has the
executor's own numbers): 4 rules docs live at `*_nocore_2026-09-03.*`, the 4 `*_2026-09-02.*` originals exist
only under `rules/archive/`; `rules/tests/` holds only the 5 `_r2` sheets, the 5 owner-read (no `_r2`) copies
confirmed byte-identical under `rules/tests/archive/reviewed_2026-09-03/`; `STATE_v5.md` next-free correctly
`D-EU-91`/`FINDING 245`; `BRIEF_european_locations_v5.md`/`CHECKLIST_european_locations_v5.md` untouched.
Census 469 PASS / 81 FAIL reproduces `T05d`'s own residual exactly. **Accepted, nothing to redo.**

🔴 **Bookkeeping finding (not a `D-EU`/`FINDING` number — a mislabelled task, not a technical defect).**
`PLAN_eu21-district-viewer-2026-09-03.md` §8 already carried an entry titled `T05 Generic No-Census Fallback
(Fleet-Wide Rollout & Archiving)` before this session touched the plan — it does **not** match that plan's own
§5 `T05` spec (`_r3` rebuild, tag `2026-09-03_r3`, once the compactness plan closes). Confirmed on disk:
`plans3D/` holds only `_r2` files (plus the archived untagged originals) — **no `_r3` file has ever been
built.** The real `T05` was dispatched this session: fresh Sonnet, told to match the live `_r2` build's
feature set (including whatever produced its `GENERIC_NO_CENSUS`/fallback classification of `NO_CENSUS_ROW`
buildings, so `_r3` does not regress the 0-unpartitioned-massings result) and to flag the naming collision in
its own new, separately-titled progress-log entry rather than editing the existing one.

**Status at handoff: `T05` (`_r3`) is in flight, not confirmed done.** It runs as a background agent inside
this session; a new session cannot reach it (no notification, no `SendMessage` — agent ids are scoped to the
session that spawned them). **First action of the next session:**
`ls docs/docs_ACTIVE/europeanLocations/plans3D/*_r3.html` and
`ls openubem/outputs/eu_evidence/EU-21/district_plans/*_r3.json`. If all four districts' `_r3` files exist and
the plan's §8 has a `T05 — _r3 rebuild (per §5 spec)` entry, audit it (acceptance: `ERROR = 0` in all four
JSONs, `D-EU-89` clause 3) and move on. If absent or partial, the dispatch died with the session — redispatch
once, fresh Sonnet, same brief as above (match the live `_r2` feature set, tag `2026-09-03_r3`, touch only
`08_district_viewer.py` if a code change is truly needed, no git, `ERROR = 0` acceptance); do not chase the
old agent id.

**Then, still queued, unstarted — the last piece of the owner's "go until the end" instruction:** update the
progress-log sections of the three debug reports —
`debugs/DEBUG_district_{orange,purple,red}_buildings_diagnosis_2026-09-03.md` — recording what was actually
implemented (Purple's 17 `MultiPolygon` buildings = `FINDING 243`, fixed, 17/17 now `direct`; parts of Red's
diagnoses = the `cut_radial`/`cut_wingwise` partial fix plus the honest structural residual `FINDING 242`) and
what is explicitly **not** implemented, each citing the ruling that blocks it:
- Red's `C11` k=1 sliver exemption — conflicts `D-EU-86` (no invented exemptions).
- Orange's Tier-1 habitable-area k-clamp and Red's façade-cap k-redistribution — both conflict `D-EU-88`
  clause 1 (`k` is computed by `load_universe`, never selected, sampled or clamped).
- Red's proposed `C12` area-balance check — conflicts the "seven checks and only seven" regime; its
  underlying observation is already `FINDING 244`, not an open slot.

### 🔴 2026-09-03, later — `PLAN_eu21-compactness-2026-09-03.md` T05d/T06/T07 done, `CP-3` reached, nothing running

**Read this block first; it supersedes the "evening" and dispatch-order blocks immediately below (kept for
history).** `T05d` fixed the `MultiPolygon` fault (`FINDING 243`, 17/17 reproduce `direct`) and added
`cut_radial`/`cut_wingwise` (`D-EU-89` clause 2) — the ladder still could not reach `FAIL 0` at any rung
(2.5/3.0/3.5/4.0), so `MAX_FLAT_ASPECT` is **set to 2.5, the strictest rung, marked not calibrated** (per
`D-EU-89` clause 2, never the least-failing rung). `T06` ran `--test all` at that frozen constant and wrote
the five delivered sheets as `TEST_0*_nocore_2026-09-03_r2.html` — **550 plates, 469 PASS, 81 FAIL**,
reproducing `T05d`'s own residual exactly (57 unique buildings — thick-band courtyard rings and dense
`n = 12` multi-wing plates whose wings never separate under `lobes_of`). `T07` re-dated the four rules docs
to `*_nocore_2026-09-03.*` (archiving the four `2026-09-02` originals — `RULES_dwelling_layout_scheme` was
already archived before `T07` started, cause not determined, content verified intact), archived the five
owner-read `TEST_0*_nocore_2026-09-03.html` (no `_r2`) out of `rules/tests/` per the owner's *"you can
archive non core versions"* (byte-identical in `rules/tests/archive/reviewed_2026-09-03/`, `cmp`-verified
before deletion — the `_r2` set is now the sole live set), and swept live citations by filename in
`STATE_european_locations_v5.md`, this prompt, and `debugs/DEBUG_REFERENCES_european_locations.md`
(historical citations inside closed/completed plan ledgers and `previous/` left untouched, as precedent).

**Acceptance status** (`STATE_european_locations_v5.md` §5): criteria 1, 2 and 4 hold; **criterion 3 does
not** — `MAX_FLAT_ASPECT` is not calibrated, it is set by ruling. `EU-21` is therefore **not yet done**.

**Next free `D-EU-91` / `FINDING 245`.**

**Next, in the owner's order** (`STATE_european_locations_v5.md` §7): carry the written rules into
`openubem/geometry/european_residential.py` · close the 95 % gap, biggest group first · the 939-building
IDF-writer demotion (separate defect) · republish `plans3D/` from the new plans, geometry only · district
plan `_r3` (rebuild the four district JSONs against this session's cutter, `0 ERROR` acceptance) is a
**separate dispatch**, not run by this session.

### 🔴 2026-09-03 evening — both executors audited; nothing running; the next session starts here

**Owner's last words this session:** *"please update this prompt … i will continue another session"*, after
the three sentences of the afternoon — *"you can archive non core versions"* · *"what kind of a visualizaiton is taht, look how it was beautiful before"* (with a screenshot of the EU-11 viewer's pop-up: dark modal, one colour per flat labelled D1…Dk, storey buttons, north arrow, scale bar, zone table) · *"i want this style of pop-up windows to see floor plans, assigned"*.

**What exists on disk, audited by the director from the JSONs (accepted):**
- `plans3D/PLANS_<district>_nocore_2026-09-03.html` × 4 + `EU-21/district_plans/<district>_nocore_2026-09-03.json`
  × 4, built by `scripts/eu21/08_district_viewer.py` (new, 505 lines). Madrid 961 census / 946 drawn / 791 PASS /
  7 refused / 8 error / 233 no-census-row; Lyon 297 / 293 / 267 / 3 / 1 / 233; London 82 / 69 / 52 / 13 / 0 /
  1,160; Bologna 1,204 / 1,196 / 964 / 0 / 8 / 16. **Fleet 2,504 / 2,544 drawn (98.4 %, bar 2,417), 2,074 PASS
  all seven (81.5 %).** Never quote the 98.4 % as "95 % passing" — drawn ≠ PASS.
- Compactness `T05b` + `T05c` done and logged (§8 of that plan): `C10` is the `D-EU-87` opening test, ladder
  81 / 62 / 46 / 39 FAIL of 550 at 2.5 / 3.0 / 3.5 / 4.0 — **`FAIL 0` unreachable**, `MAX_FLAT_ASPECT = 4.0`
  on disk **not frozen** (`07_nocore_tests.py:795`). Five owner-read `TEST_0*_nocore_2026-09-03.html` restored
  byte-identical; `_r2` sheets on disk are the last ladder run, **not** a T06 delivery.

**Rulings taken (`STATE_european_locations_v5.md` §3–§4):** `FINDING 242` (residual = ring/wing family),
`FINDING 243` (17 census buildings raise `'MultiPolygon' object has no attribute 'exterior'/'interiors'`
inside `build_flats`, never seen on the 550 plates — the district JSONs join the acceptance), **`D-EU-89`**:
pop-up = the EU-11 modal of `generate_eu_3d_viewers.py` **at commit `3fef4e33`** fed with the no-core flats
plus the seven chips, no energy; no rung chosen until `T05d`, and if `FAIL 0` stays unreachable the constant is
set to the **strictest** rung 2.5 with honest `FAIL`s; the archive is authorised once, at `T07`. (Next-free
as of this block was `D-EU-90` / `FINDING 244`; both are now taken — next free is `D-EU-91` / `FINDING 245`,
see the top of §5.)

**Dispatch order:**
1. `PLAN_eu21-district-viewer-2026-09-03.md` **T04 COMPLETED (`CP-2` reached)**: pop-up modal restored to the EU-11
   style (`Screenshot_18.png`), 2D dark canvas, D1…Dk flats with true planar centroid labels, North arrow, scale bar,
   interactive storey switching, dwelling highlight on hover, 7-check chips; four district pages rebuilt
   (`2026-09-03` and `_r2`); `grep -c "Dwelling Index"` = 1, `srcdoc` = 0, `kwh|eui|energy|archetype` = 0 on all pages.
2. `PLAN_eu21-compactness-2026-09-03.md` **T05d → T06 → T07, stop at `CP-3`** (the `MultiPolygon` fault first,
   then the ring/wing candidates, ladder, rung per `D-EU-89` clause 2, five delivered `_r2` sheets, rules docs
   re-dated, the owner-read sheets and the `_nocore_2026-09-02` docs archived per the owner's sentence, citation
   sweep by filename). Audit the log entries, the 550 census, `ERROR` 0, the sweep count.
3. District plan **T05** (`_r3`) after 2 closes; acceptance `ERROR` 0 in all four JSONs.
Before any dispatch: read each plan's §8 tail and `ls` the target files — this session dispatched nothing
after 11:00, but a half-finished task with no log entry is exactly `FINDING 239`'s shape.

**Standing:** `D-EU-55` — no simulation without the owner's own sentence; `D-EU-85` — dated filenames, never
overwrite; the five `_2026-09-03` sheets and the four `_2026-09-03` pages are read artifacts, frozen.

### 🔴 2026-09-03 — arc docs at v5, and the compactness repair in flight

**Arc documentation moved to v5** (owner 2026-09-03: *"as we decided to continue without cores, can you
update these BRIEF / CHECKLIST / STATE as v5, and archive these current files in the archive"*). Read-first
is now `STATE_european_locations_v5.md`; `BRIEF_european_locations_v5.md` and
`CHECKLIST_european_locations_v5.md` beside it. The v4 trio is in `previous/`, historical, not appended to.

**`FINDING 238` — the no-core `FAIL 0` scored no shape term.** Director control on the five stored
`test_0N_nocore.json`, 550 plates / 3,267 flats, slenderness = long/short of the minimum rotated
rectangle: **48 % of flats above 3.0**, 37 % above 4.0, worst plate **14.12** (`COURTYARD` 29659, k=12).
Cause, one line: `build_flats` (`scripts/eu21/07_nocore_tests.py:533`) keeps the single-axis cut whenever
`_fully_ok` passes, and neither `_fully_ok` nor `_plate_score` carries a shape term, so `cut_grid` is only
reached by plates that already failed something else. `C10` forbids a pinch and is satisfied by a
2 m x 40 m ribbon.

**Three new laws, owner-authorised** (*"we are dviding flat zones but there could be a limit to a width of
a flat, i do not know. you define and add to the global rules"* · *"why not adding division from second
edge"* · *"so can you update every tests based on these updates … go to the end."*):
- **`D-EU-82`** — a flat's minimum rotated rectangle may not exceed `MAX_FLAT_ASPECT` in long/short ratio.
  New check **`C11`**. `C10` forbids a pinch, `C11` forbids a ribbon; both printed on every sheet.
- **`D-EU-83`** — every `rows x cols` scheme, on both bearings, is a first-class candidate for every plate,
  not a rescue for plates that failed.
- **`D-EU-84`** — `MAX_FLAT_ASPECT` is the strictest rung of `{2.5, 3.0, 3.5, 4.0}` that still reaches
  `FAIL 0` on all 550 plates. If none does, stop and let the director rule; never invent an exemption.

**The regime now scores seven checks:** `C1 C3 C4 C5 C6 C10 C11`.

**Plan in force: `implementation/PLAN_eu21-compactness-2026-09-03.md`** (T01-T05, T05b, T05c, T06, T07;
`CP-1`/`CP-2`/`CP-3`). Deliverables `TEST_0*_nocore_2026-09-03.html` + `test_0N_nocore.json`. **Every
`_nocore_2026-09-02.html` sheet and every core-era `_2026-09-02.html` sheet is now in
`rules/tests/archive/` (owner, 2026-09-03) — 16 files; `rules/tests/` holds the 2026-09-03 set only.**

**`D-EU-85` — a builder script may never write to a delivered dated filename.** `run_test` hard-coded
`_nocore_2026-09-02`, so ordinary repair runs rewrote three delivered sheets in place
(`FINDING 239`). The output date in a generator is repointed to the new build date as the **first** edit
of any repair plan, before a single run command is issued. The rule is kept by the path in the code, not
by intention.

**`CP-1` audited clean 2026-09-03**: census reproduced exactly (3,267 flats, 1,577 over 3.0, max 14.12);
`C11` collapsed test 1 from 5.53 to 2.98 with no regression; a real GEOS bug found and fixed
(`_snap_world`, `07:327`) — independent per-flat rotation split a shared vertex and faked a 65.81 m²
`C4` overlap.

**`CP-2` reached at T05 — the ladder did not reach `FAIL 0`:** 2.5 -> 51, 3.0 -> 24, 3.5 -> 17,
4.0 -> 11. Residual 11 plate-appearances / 7 buildings, all `n=12`, only in the two size-imposed tests.

🔴 **`FINDING 240` / `D-EU-86` — the director measured the residual and refused the excuse.** Under
every offending flat the plate's local band is **8.2 - 16.4 m** while the flat's short side is
**2.05 - 3.50 m** (13 - 32 % of the width on offer), with ordinary 48 - 72 m² flats — a 59 m² flat in an
8 m band fits as 7.7 x 7.7 m. The footprint is not the constraint, the cut is; `COURTYARD 29659` still
reads 14.12:1, identical to the pre-`C11` baseline, so `D-EU-83`'s grid-first candidate never wins that
plate. Therefore: **`C11` is not relaxed, no plate is exempted, `MAX_FLAT_ASPECT` is not frozen at 4.0**,
and the three failing group rules — `COURTYARD`, `L_SHAPE`, `COMPLEX_MULTI_WING` — must divide a thick
band across its **depth** as well as along its run. The ladder is re-run after the fix and the constant
takes the strictest rung that then reaches `FAIL 0`. **T05b carries this.**

🔴 **`FINDING 241` / `D-EU-87` — `C10` was measuring the *widest* place in a flat.** The owner read
the 2026-09-03 sheets and red-boxed four plates (`COMPLEX_MULTI_WING` Bologna 29965, `COURTYARD` Bologna
32052, `COMPLEX_MULTI_WING` Bologna 30127 and 28754) — each a flat pinched to well under two metres beside
a notch or a light well, each printing **`C10 4.0 m` PASS**. Cause: `C10` was wired to `widest_fit`
(`04_group_tests.py:299`), which returns the **largest** disc the flat can hold, capped at 4.0 m; the
recurring `4.0` on card after card is the probe ceiling, not a measurement. Director's census over all 550
baseline plates, morphological opening at `r = 1.00 m` with mitre joins: **182 of 550 plates (33 %)** and
**278 of 3,267 flats (9 %)** hold a sub-2 m region, and **1,349 of 1,524 m² — 89 % — is created by the
cut**, not inherited from the footprint. This is `FINDING 238` a second time: a check that prints a ceiling
certifies what it cannot see.

**`D-EU-87`:** `C10` becomes an **opening test** — erode the flat by 1.00 m and dilate back with mitre
joins, and the area not returned is the part narrower than 2.00 m. The same opening on the plate footprint
is subtracted, so the footprint's own acute tips and slots are excused and the cut's own slivers are not.
`C10` fails above **0.10 m²** (the measured float-noise floor, not an allowance), prints `x.xx m²` like
`C4`, and `widest_fit` is disqualified as a verdict and as a score term. `_fully_ok` gates on it, which is
what finally lets the existing `_donate_the_neck` machinery run at all. **T05c carries this.**

**Sheet provenance.** `rules/tests/` is being rebuilt as `TEST_0*_nocore_2026-09-03_r2.html`. The
owner-read `TEST_0*_nocore_2026-09-03.html` five are preserved in
`rules/tests/archive/reviewed_2026-09-03/`; the `_nocore_2026-09-02` and core-era `_2026-09-02` sheets are
in `rules/tests/archive/` (16 files).

**Document scope, owner 2026-09-03:** *"you are taking notes, but i do not want, these are
represenations"* — `BRIEF_european_locations_v5.md` and `CHECKLIST_european_locations_v5.md` carry no
findings, rulings, numbers or notes. **All of that goes in `STATE_european_locations_v5.md`, nowhere else.**

🔴 **`D-EU-88` — the rules go to the neighbourhoods, in 3D, before any simulation** (owner 2026-09-03, five
sentences quoted in `STATE_european_locations_v5.md` §4 and in the plan). Every census building of a district is
cut at its own `k` by `build_flats`; the page is the `outputs_3D` viewer without energy, coloured by verdict,
whose click-modal is the TEST-sheet card. Madrid first, then the other three, no reading gate (*"ok no need
from me about any approval, continue continue to the end"*); `D-EU-55` untouched. Plan
`implementation/PLAN_eu21-district-viewer-2026-09-03.md`, file `scripts/eu21/08_district_viewer.py`, outputs
`plans3D/PLANS_<district>_nocore_<tag>.html` + `EU-21/district_plans/`. Runs beside the compactness plan; the
footer names the cutter's sha256 so pre- and post-repair pages are distinguishable.

**`FINDING 239`, second occurrence (~09:53):** the resumed `T05b` run rewrote the five owner-read `_2026-09-03`
sheets in `rules/tests/`; the archive copies are authentic and are restored as T05b step 0, tag repointed to
`_r2` before any further run.

(Next-free as of this block was `D-EU-90` / `FINDING 244`, `D-EU-89`/`FINDING 242`/`243` taken; both are now
also taken — next free is `D-EU-91` / `FINDING 245`, see the top of §5.)


### 🔴 2026-09-02 night — the no-core pivot, plan `eu21-nocore` running

**Owner's sentences, verbatim:** *"yes i really like the no-core option, please exclude core information from global
rules for this one TEST_01_nocore_2026-09-02.html, and try to generate same nocore options for other tests as well"*
· *"i have decided with nocore option for all, becasue core is getting complex everything"* · *"no empty space per
floor, add these empty spaces inside the closest falt (at that case no need to create equal floor area flat zones)"*
· *"violation of this global rule Nothing narrower than 2 m"* · *"archive them and create nocore versions as well.
clearly core/corridor makes things really complex. no need at this stage, our goal is to create flat division. lets
go to the end. i am going to sleep."* · *"if anything you need to ask, do not, continue as you recommend."* ·
*"no more core options, only nocore options, lets go, it is easier to handle."*

**What changed.** A plate is now divided into **dwellings only**. No circulation zone, no core, no corridor is
drawn, and no rule, check or sheet refers to one. Everything below this block — `D-EU-64`…`D-EU-78`, the corridor
cutter, the `C2`/`C7`/`C8`/`C9`/`R2` checks, the `eu21-cutter` census — is **history of the parked path**, kept for
provenance only. Do not restart it; only the owner may.

**Three new laws.**
- **`D-EU-79` — the no-core regime.** Dwellings only; the corridor cutter is parked with its file intact.
- **`D-EU-80` — no empty space per floor.** Every square metre belongs to exactly one flat; leftover area is
  absorbed into the flat it touches most. Equal flat areas are **not** required and never justify a gap.
  Scored by `C1 = 100.0 %`. Owner evidence: plate 2, `ES-MAD-BERRUGUETE`, `relation/12765478`.
- **`D-EU-81` — nothing narrower than 2 m.** No flat may contain any part narrower than 2.00 m, measured as the
  widest disc that fits. Scored by `C10 >= 2.00 m`. Owner evidence: plate 32, `IT-BOL-GALVANI2`, `29965`.

**The regime scores six checks and only six:** `C1` coverage · `C3` flat count · `C4` no lobed flat, no overlap ·
`C5` no hole, no containment, ≤ 40 points · `C6` ≥ 2.50 m of outer façade per flat · `C10` ≥ 2.00 m width.
`C2`, `C7`, `C8`, `C9` and `R2` are circulation checks and are **removed from the sheets entirely**, not printed
as `N/A`.

**Plan in force: `implementation/PLAN_eu21-nocore-2026-09-02.md`.** Script `scripts/eu21/07_nocore_tests.py` (the
only file the arc writes). Deliverables: `TEST_01_nocore_2026-09-02.html` … `TEST_05_nocore_2026-09-02.html` in
`rules/tests/`, `test_01_nocore.json` … `test_05_nocore.json` in `EU-21/rules_tests/`, and no-core versions of the
four rules documents beside their archived originals. Acceptance: **`FAIL 0` on all five sheets** — 550 plates,
none refused, because the no-core regime has no refusal path. (Next-free as of that night was `D-EU-82` / `FINDING 238`; both are now taken — see the 2026-09-03 block above.)

---

### 🔴 2026-09-02 afternoon — plan `eu21-cutter` at `CP-2`, nothing running

**Owner's sentences today, verbatim:** *"lets go by recommendation"* · *"continuer jusqu'a la fin, vas-y"* · *"a,
continue"* (at `CP-1`) · *"apply the fix"* (at `CP-2`) · then, on the regenerated document: *"it looks like you
created new bugs in the layouts … we made a great layout for previosuly you changed them, no"* and *"do not ever
update anything unless i say so"*.

**Census, director re-derived after T06B: 367 PASS · 135 FAIL · 48 REFUSED · 0 ERROR of 550.** Failing checks
`C8` 79 · `C4` 71 · `C9` 30 · `C6` 15 · `C10` 13 · `C2` 5; refusals `BAND_LT_3M` 30 · `FLAT_ENCLOSES_ZONE` 13 ·
`CELL_EMPTY` 5 — the only three tokens left. Trajectory: T01 `321/173/56` → T03 `308/163/79` → T03B `332/165/53`
→ T04 `348/159/43` → T05 `366/136/48` → T06 unchanged → T06B `367/135/48`. 10 regressions vs T01 survive
(6 plates, named plate by plate in the plan's §8).

**Plan in force: `implementation/PLAN_eu21-cutter-2026-09-02.md`.** T01–T03, T03B, T04, T05, T06, T06B done, each
audited by the director against his own census run. Not started: `T07` (re-render; the two stale `C1–C8` strings at
`04_group_tests.py:539`/`:549`; `D-EU-74` into `03`) and `T08` (acceptance table, `CP-3`, plan closes). Gate:
`PASS ≥ 420`, `C9 ≤ 20`, `C2 = 0`, zero regressions — **53 plates away**. Refusals are out of scope (a footprint
question, not a corridor one).

**The block, and the owner's open call at `CP-2`.** `C4` (71) and `C8` (79) are the block and no remaining task
addresses them. `FINDING 229` is closed: T06B let the whole-cell preference reach the cross-bearing sort (172 of 328
plates now return a whole band) and it bought **one** plate. 🔴 `FINDING 230`: that **disproves** T06's hypothesis
that an oblique band slicing axis-aligned cells is what lobes the flats — `C4`/`C8` moved by zero plates. Unverified
candidate, from reading the code only: `_cell_whole` tests the band alone, but the cutters subtract `core ∪ band`,
so a core landing inside a cell splits that flat and still fails `C4`. Needs one instrumented run. **No task is
written for it — the owner's call.**

**Laws taken since 2026-09-01** (`D-EU-64` is §2): `D-EU-65` cap 12 (*"ok raise the cap and run 9 and 12 as well,
let's go"*) · `D-EU-66` 9–10 on `6x2` with merges (*"let's go if you recommend"*) · `D-EU-67` courtyard stair cores
joined into one circulation zone by the gallery band · `D-EU-68` flats are basic straight-cut thermal zones ·
`D-EU-69` every flat meets the **outer** façade over ≥ 2.50 m, a courtyard is not enough (`C6`) · `D-EU-70` the one
corridor touches every flat over ≥ 1.00 m and needs no daylight (`C8`) · `D-EU-71` corridor ≤ **16** corner points
(`C9`; owner ratified 24 then asked *"if possible it can be lower"* — 16 is the lowest cap that keeps the praised
`i_shape_linear_gallery` plate, which reads 15) · `D-EU-72` no zone under **2.00 m** (`C10`) · `D-EU-73` the
six-clause corridor-design law from the owner's three annotated images — (a) one limb one flat, (b) central shortest
band touching every flat, (c) no spur, (d) no step, (e) chain not tree, (f) corner budget — a **cutter** law, `C9`
measures its result; (e)/(f) superseded · `D-EU-74` the corridor is an inscribed rectangle, computed not clipped,
never `band ∩ footprint` (proved: `C9` `CORRIDOR_RECTANGLE` 12→0, `SLAB` 17→2) · `D-EU-75` one corridor, one
rectangle, any bearing — no chain, no ring, bearing from the footprint's own edges · `D-EU-76` every flat is one
zone, no absurd small space (`finish()` already does it). Verdict: `C1`–`C6`, `C8`, `C9`, `C10`; `C7` and `R2`
advisory. The seven global laws are the `GLOBAL` chapter of both rules documents. **Next free at that date (superseded, see §5 top) `D-EU-77` /
`FINDING 231`.**

**Director decisions ratified** (owner 2026-09-02, verbatim *"yes, don't understand, if improves yes, ok, ok"*, read
in order): `DD-9` (figures for a `03` run come from the cutter into a new `group_plans_cutter.json`) · `DD-11`
(a decomposition with < 2 wings falls back to `cut_convex`; 16 of 29 `WING_TREE_FAILED` plates recovered) · `DD-12`
(two k=6 plates PASS→REFUSED accepted, `FINDING 226`) · `DD-13` (4 of 11 sheets now draw a different building; each
names its id and scheme). **`DD-10`** (junction rectangle withdrawn, `FINDING 225` — it raised the point count it was
written to lower on 29 of 39 plates) **was answered "don't understand" and never ruled — do not press it.**

**Document ruling, 2026-09-02 evening.** The owner asked why a second file existed, why `GLOBAL` sat beside `LAW`,
and why five of eleven sheets drew a different building. Answers on record: the dated-filename rule (a `03` run never
overwrites a delivered artifact); the long `LAW` chapter is `03`'s output while `GLOBAL` was hand-written later and
inserted into both, so `…09-02.html` stated the same rules twice; and `DD-9` moved the figures from the engine to the
direct cutter, which changed the drawn building on `COURTYARD` (Bologna 29530 → Madrid `relation/12713026`),
`CORRIDOR_RECTANGLE`, `L_SHAPE`, `U_OR_T_SHAPE` and `COMPLEX_MULTI_WING`. Ruled: keep `…09-01.html` with both
chapters, `LAW` shortened to nine one-line laws (done); `…09-02.html` moved to `previous/`. The examples in
`…09-01.html` are the pre-`DD-9` engine figures and stay as they are.

**Still open, unranked:** `DD-10` · `FINDING 227` (sheets 07/10/11 advertise three refusal tokens the cutter does
not have) · `C2` = 5, all `COURTYARD`, against a final gate of 0 · the 10 regressions · `FINDING 230`'s
core-in-cell hypothesis.

**Owner focus (2026-09-01):** *"our only focus still visual outputs, defining algorithms for groups based on the
rules we are applying."* Steps 3 and 4 of each sheet (where the circulation goes, how the flats are cut) still need
to become a per-group algorithm in bullet form, checkable against the drawn plate. No engine rewrite, no scheme
adoption, no simulation while that is the focus.

**Open beyond that focus, in the owner's order:** 1 write the one-core law into the engine · 2 close the 95 % gap
biggest group first (`COMPLEX_MULTI_WING` 362, `SLIVER` 390, `COURTYARD` 297, `U_OR_T_SHAPE` 217, `L_SHAPE` 213) ·
3 decide `courtyard_gallery_ring` (S5) · 4 the 939 buildings demoted at IDF-writing time (`ZeroDivisionError` in
`geomeppy/geom/vectors.py:105`, `IndexError` at `openubem/idf/surfaces.py:863`) — a separate defect, never counted
as a morphology failure · 5 publish the plans into `plans3D/` under the existing `PLANS_<district>.html` names,
geometry only.

### Plan ledger — one line per plan; the progress logs live in each plan's §8, not here

- `eu21-rules-tests-2026-09-01` — COMPLETE. Five test sheets, 550 plates. Numbers superseded by the census above.
- `eu21-cap12-2026-09-01` — COMPLETE. `D-EU-65`/`D-EU-66`. Old JSON kept as `test_0N.cap8` / `.cap12`.
- `eu21-direct-cutters-2026-09-01` — COMPLETE. `D-EU-67`/`D-EU-68`, new `05_group_cutters.py`. 432/50/68.
- `eu21-t07-2026-09-02` — COMPLETE. Wing fallbacks kept, junction rectangle withdrawn (`DD-10`), the `03` run
  (`DD-9`, `DD-13`, `FINDING 227`). 440/54/56.
- `eu21-global-rules-2026-09-02` — COMPLETE. `D-EU-69`…`D-EU-73`, `C9`/`C10` promoted. 321/173/56.
- `eu21-cutter-2026-09-02` — **PARKED 2026-09-02 night by the no-core pivot (`D-EU-79`); was at `CP-2`.** T01 baseline · T02 `rectify_band()`
  (`05_group_cutters.py:630`) · T03 `D-EU-74` proved, `CP-1` *"a, continue"* · T03B solved centre + chain · T04
  `D-EU-75` free bearing (old T04/T05 withdrawn) · T05 `C8`-style touch · T06 `_cell_whole` → `FINDING 229` ·
  T06B → `FINDING 230`. 367/135/48.
- `eu21-test01-clean-2026-09-02` — CLOSED at `PASS 32 / FAIL 1 / REFUSED 0` on `TEST_01`. `D-EU-77` (contact
  metric), `D-EU-78` (corridor rectangle first). Superseded by the no-core pivot.
- `eu-engine-nocore-carryin-2026-09-03` — **IN FLIGHT**, `D-EU-95`. Carries the accepted no-core cutter into the
  IDF engine by extraction, gated on bit-parity with `_r5` over all 2,544 plates, then rebuilds the four
  districts' IDFs and submits the Speed campaign. `CP-1` parity · `CP-2` IDF audit. This is the plan that turns
  proven plans into simulated buildings; nothing goes to Speed before its `CP-2`.
- `eu21-colour-repair-2026-09-03` — **COMPLETE, `CP-4` accepted.** Produced `_r4` then `_r5`. PASS 2,012 → 2,178
  → 2,353 (79.1 % → 85.6 % → 92.5 %), refused 23 → 15, 0 regressions at either step, Madrid crossing at 95.3 %.
- `eu21-nocore-2026-09-02` — **CLOSED 2026-09-02, acceptance met.** `D-EU-79`/`D-EU-80`/`D-EU-81`, `07_nocore_tests.py`, five
  `TEST_0N_nocore_2026-09-02.html` sheets. Acceptance `FAIL 0` on all five.
  T01/T02/T03 done 2026-09-02 night, `CP-1` passed without waiting (owner: "lets go to the end. i am going
  to sleep."): `TEST_01_nocore` **33/33**, six checks only (`C1 C3 C4 C5 C6 C10`), the four circulation
  checks removed from the sheet rather than shown as `N/A`; the only remaining occurrence of the string
  "corridor" in the five sheets is the group id `CORRIDOR_RECTANGLE`, which is a morphology name, not core
  information. Director control over the five JSONs: **550 plates, 524 PASS / 26 FAIL** — failing checks
  `C10` x13, `C1` x11, `C5` x4, `C4` x1, clustered on `COURTYARD`, thin `TRAPEZOID`/`SLIVER`/`TRIANGLE`
  at k=12, and two `L_SHAPE`. T04 dispatched on exactly those 26 rows.
  T04 done 2026-09-02 night: **550 / 550 PASS, FAIL 0** on all five sheets (33 / 132 / 55 / 220 / 110), no
  REFUSED, no ERROR, no plate dropped, no threshold moved and no `FINDING` needed. Director's independent
  re-verification straight from the stored polygons, not from the sheet's own verdicts: minimum coverage
  **0.99999**, maximum pairwise overlap **0.0011 m2**, minimum `widest_fit` **2.0 m**, zero MultiPolygon
  flats, zero flats with an interior ring, zero drawn/claimed count mismatches; check minima `C1` 100.0 %,
  `C10` 2.0 m, `C5` 34 points worst, `C6` 2.55 m worst. Two causes had held the 26: `unary_union` merges
  in the donation path were accepted even when they returned a `MultiPolygon`, silently dropping a part
  (all 11 `C1` and two `C5`), and the single-row column cutter had no way to reach 2 m at k=12 on thin
  footprints — a 2/3-row grid cutter was added as a further fix-ladder candidate. Executor deviation
  logged: it ran a read-only `git status`, which the dispatch forbade; no git state changed.
  T05 done 2026-09-02 night: the four docs the owner named moved byte-identical into `rules/archive/`, and
  their no-core versions published as `EXAMPLE_dwelling_layout_validation_nocore_2026-09-02.md`,
  `RULES_context_geometry_simulation_nocore_2026-09-02.md`, `RULES_dwelling_layout_scheme_nocore_2026-09-02.html`
  and `RULES_dwelling_layout_groups_nocore_2026-09-02.html` (all 11 group sheets kept, each group's old
  circulation polygon merged into its longest-boundary flat). `C2`/`C7`/`C8`/`C9`/`R2`, `D-EU-72` and `D-EU-73`
  are gone from the live rules, not shown as `N/A`. The visible label "Corridor rectangle" reads **"Elongated
  rectangle"** everywhere; only the machine id `CORRIDOR_RECTANGLE` survives, and it is a shape name. One
  authorised exception to the script freeze: a `FROZEN` path fallback at `04_group_tests.py:25`,
  `06_nocore_control.py:29`, `07_nocore_tests.py:26`, since archiving the CSS source would otherwise break all
  three. Deliberate omission, stated on the page itself: the scheme document's eight worked comparisons are
  **not** redrawn — they were a hand-picked sample from an older population and nothing authorises redrawing
  them; the page points at the 550-plate fleet instead. Citation sweep: 5 repaired in
  `previous/STATE_european_locations_v4.md`, 3 in `debugs/DEBUG_REFERENCES_european_locations.md`, 2 here; ~47 hits left
  untouched inside closed plan docs and `previous/` archives, which are historical record.

- `eu21-compactness-2026-09-03` — 🟢 **`CP-3` reached 2026-09-03, T01–T07 all done.** `C11` scored, grid-first
  search plus depth-layered/ring-radial/per-wing candidates wired in, `C10` rebuilt as a created-pinch test
  (`D-EU-87`). `FAIL 0` unreachable at every rung after two genuine repair rounds; per `D-EU-89` clause 2
  `MAX_FLAT_ASPECT` is set to the strictest rung, **2.5**, marked not calibrated (acceptance criterion 3 in
  `STATE_european_locations_v5.md` §5 is not met) — 81/550 plates ship as an honest residual `FAIL` (57
  unique buildings). Five sheets delivered as `TEST_0*_nocore_2026-09-03_r2.html`, the sole live set (the
  owner-read `2026-09-03` and the `2026-09-02` sets are both archived, `FINDING 239`: three of the five
  `2026-09-02` originals were overwritten in place and no longer show the delivered drawings). Four rules
  docs re-dated `*_nocore_2026-09-03.*`, citations swept by filename.
- `eu21-district-viewer-2026-09-03` — 🟢 **CLOSED 2026-09-03, T01–T05 COMPLETE.** (`D-EU-88`, `D-EU-89`, `D-EU-90`):
  EU-11 modal pop-up restored with dark canvas, dwelling-only partition, 4-column zone table, 7 check chips,
  North arrow and scale bar; Madrid/Lyon/London/Bologna pages updated to `_r2`;
  `grep -c "Dwelling Index"` = 1, `srcdoc` = 0, `kwh|eui|energy|archetype` = 0 on all pages;
  T05 generic fallback rolled out fleet-wide (1,641 uncatalogued buildings partitioned across Madrid, Lyon, London, Bologna;
  colored dark green `rgb(24, 94, 46)`; exactly 0 unpartitioned massing blocks remaining in the 3D viewers). Baseline non-r2
  files archived to `plans3D/archive/`.
  **Fleet coverage achieved:**
  - Census fleet: 2,505 / 2,544 drawn (**98.5 %**, clearing the 95 % bar of 2,417 by +88 buildings), **2,235 PASS all 7 checks (87.9 %)**.
  - Full cadastral fleet: **4,146 of 4,186 structures (99.0 %)** now carry real interior flat partitions.
  **District color diagnostics published (`debugs/`):**
  - Red buildings diagnostic (7 rules breakdown, green comparisons, 5-step fix plan): `DEBUG_district_red_buildings_diagnosis_2026-09-03.md`.
  - Orange buildings diagnostic (refused $k > 12$, 23 buildings, habitability clamp & portal decomposition): `DEBUG_district_orange_buildings_diagnosis_2026-09-03.md`.
  - Purple buildings diagnostic (cutter runtime exceptions `FINDING 243`, 17 buildings, `_to_single_polygon` normalization): `DEBUG_district_purple_buildings_diagnosis_2026-09-03.md`.
  - Open finding registered: `FINDING 244` (runaway leftover absorption on non-convex shapes, proposal for rule `C12` area balance $\le 2.0$).

**Done means:** 2,417 of 2,544 residential buildings carry a floor plan of flats alone — no circulation zone
(`D-EU-79`) — each cut by a rule that is written on its group's sheet, and the rules generalise to countries not yet in the
database. (Achieved on `_r5`, the build to quote: drawn **2,529 / 2,544 = 99.4 %**; passing all 7 checks
**2,353 / 2,544 = 92.5 %**, with `ES-MAD-BERRUGUETE` at **95.3 %** — the `D-EU-91` bar crossed. Numbers from
any earlier build, including the 2,505 / 2,235 pair this line used to carry, are superseded and must not be quoted.)
