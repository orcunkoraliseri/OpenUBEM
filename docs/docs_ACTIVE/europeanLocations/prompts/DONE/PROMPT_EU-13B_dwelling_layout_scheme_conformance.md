# `EU-13B` — Executor prompt: make the emitted dwelling layout the scheme this arc actually ruled

- **Arc**: European locations × Step 8.
- **Order**: `EU-13B` first, `EU-14B` after it — `EU-14B` reuses this task's partitioner.
- **Spec, in force, read both before writing any code**:
  - `docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md` §4.2 (grid assignment rules),
    §4.3 (unconditioned staircase core), §4.4 (habitability gate) and the figure
    `content/figure_4_2_dwelling_layout_schemes.svg`.
  - `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\IMP_step8\outputs\floor_layout_generation_report.md`
    §3 (footprint regularization), §5 (grid slicing table), §6 (morphological branching), §7 (core), §8
    (remainder stratification), §9 (habitability gate). **This is the method of record.**
- **Executor**: external LLM. **Paste everything below the rule into the tool.**
- **Date of prompt**: 2026-08-28. **Blocked tasks**: `T06` — see §7.
- 🔴 **`D-EU-38` — ruled 2026-08-30 by the owner: `T09` is unblocked.** After `T01`–`T08` land (corrected
  geometry, tests green, `RESULTS_EU-13B.md` written), rebuild IDFs and resimulate Madrid, Lyon and London on
  Speed (`sbatch --array`, never the login node, never `srun`), then harvest and regenerate the three
  `outputs_3D/*_viewer.html` files so they reflect the corrected layouts. Bologna's viewer is `EU-14B`'s to
  regenerate, after its own layout-binding fix and its own `T05` resimulation — it is out of scope here.
  `T06` (core carve-vs-add) stays blocked; nothing above authorizes emitting a core.

---

## Task (paste from here)

🔴 **Ruling you execute under — `D-EU-36` coverage bar, ruled 2026-08-28.** **≥ 95 % of the prepared
buildings must receive a ruled layout; 100 % is not required.** Fail closed on the residual: a building the
ruled grid cannot express keeps the already-ruled `one_zone_per_floor` fallback and is counted in a
disclosed residual. 🔴 **You may never reduce a building's declared dwelling count to make it fit** —
that is the defect `FINDING 201` records, and it fails the task whatever your coverage number is.

⚪ The bar was measured before it was set, and you are expected to reproduce it within a fraction of a
percent: **fleet 2,469 / 2,544 = 97.05 %** (Madrid 917/961, Lyon 284/297, London **64/82 = 78.0 %**,
Bologna 1,204/1,204), against 1,874 / 2,544 = 73.7 % emitted today. The only failure mode is the `> 8`
per-storey refusal. 🔴 **The bar is a fleet bar. Print the per-district split, London included, in
`RESULTS_EU-13B.md`; a fleet number without the split fails the disclosure that goes with the bar.**

🔴 **Your output is validated against a worked example, not against a screenshot.**
[`../EXAMPLE_dwelling_layout_validation_2026-08-28.md`](../EXAMPLE_dwelling_layout_validation_2026-08-28.md)
carries the eight sample buildings with their exact expected zone counts, grids, circulation schemes,
circulation areas, smallest facade contacts and area errors, and §6 of it is the acceptance test you must
pass. Read it before `T01`. Two prototype decisions in it are load-bearing and you should adopt both:
dwellings are cut as **equal-AREA slices of the real plate by bisection**, never equal-width strips of a
bounding box; and the habitability retry is a **90° rotation of the cutting frame at the same dwelling
count**, never a count reduction. ⚪ Reproduction trap recorded there: translate each footprint to its own
centroid before cutting — a footprint left in absolute UTM coordinates silently yields empty cells and a
coverage near 16 %.

🔴 **`FINDING 204` binds `T06` and any circulation you emit.** MVP §4.3's two criteria — 6–12 % of gross
floor area, and 12.0–25.0 m² per floor — are jointly satisfiable only for plates of 100.0–416.7 m², which
is 1,602 of the 2,544 prepared (63.0 %). Do not resolve the conflict. **Emit the percentage rule, tag every
building where the 12.0–25.0 m² band was departed from with `CIRCULATION_OUTSIDE_RULED_ABSOLUTE_BAND`, and
report the count per district.** The owner rules which criterion binds; you measure.


You are working in the OpenUBEM repository `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is
**`.venv/Scripts/python.exe`** — never bare `python`. Git is handled externally: **never commit and never
stage.** Do not edit root `main.py`, any OVERVIEW or DESIGN doc, `previous/MVP_european_locations.md` or
`previous/WALKTHROUGH_european_locations.md`, and never annotate MVP Table 9.7. No `.py` files under
`docs/`. All `.png` outputs go to `openubem/outputs/`, flat.

### 0. What is wrong, measured — do not re-measure, do not dispute

Four defects were measured on 2026-08-28 across the 1,340 emitted side-cars and the IDFs that were actually
simulated on Speed. They are facts; your job is to remove them.

| # | Defect | Measurement |
|---|---|---|
| **1** | **The emitted scheme is not the ruled scheme.** Every layout is parallel-strip cutting. No `n_u × n_v` grid, no unconditioned stair core, no corridor spine anywhere in the fleet. | `scheme = equal_strip_multi_angle_sweep` on **1,078 of 1,078** emitted side-cars; `has_unconditioned_core = false` on **1,078 of 1,078** |
| **2** | **The declared dwelling total is not conserved.** `units_per_floor = ceil(total / storeys)` is applied to *every* storey, so a building declares N dwellings and is simulated with more. | **815 of 1,078 (75.6 %)** emitted layouts over-emit. 17,199 declared dwellings → **19,133 emitted zones, +1,934 (+11.2 %)**. Worst: `way/51781396` declares 69, the simulated IDF `GB-LDN-STDUNSTANS/idfs/0567d9cb0dc88410.idf` contains **85** distinct `_F*_dwelling_*` zone names (+23.2 %) |
| **3** | **Dwellings per floor is uncapped.** The ruled grid table tops out at `4 × 2` = 8 units per floor. | **62 of 1,078 (5.8 %)** emit more than 8 per floor; observed values reach **32/floor** (`relation/3730743`, 1,869 m² cross-shaped plate, 156 dwellings over 5 storeys) where the strips overlap into unreadable slivers |
| **4** | **No footprint regularization.** The strips are cut straight across the raw GIS polygon, so re-entrant and cross-shaped footprints produce degenerate cells. | `floor_layout_generation_report.md` §3 (`ConvexToConcave`, `EdgeTo4`) is not implemented anywhere in `openubem/geometry/european_residential.py` |

🔴 **Defect 2 is a physics defect, not a drawing defect.** The same call site feeds both the pop-up and the
simulated IDF (`scripts/run_eu_s2_district_campaign.py:135` and `scripts/emit_eu11_layout_sidecars.py:122`,
both passing `allocation.units_per_floor`). Fixing it **changes every EUI in the campaign.** That is why
`T09` exists and why it is blocked on an owner ruling — do not resubmit anything to Speed on your own
judgement.

⚪ Note that `allocate_european_dwellings` (`openubem/geometry/european_residential.py:715`) **already
computes the correct answer** — `floor_allocations[i].dwelling_count = quotient + (1 if i < remainder)`,
with an internal assertion that the total is conserved. Both call sites ignore it and read the
`units_per_floor` ceiling instead. Defect 2 is a two-line consumption bug, not a missing algorithm.

### 1. `T01` — Conserve the declared dwelling total across storeys

**What.** Stop using `allocation.units_per_floor` as a per-storey constant. Each storey `s` must be
partitioned into `allocation.floor_allocations[s].dwelling_count` dwellings.

**Why.** `floor_layout_generation_report.md` §8: with `N_total = q·N_floors + r`, exactly `r` storeys carry
`q+1` units and `N_floors − r` carry `q`. Today all storeys carry `ceil(N_total/N_floors)`.

**How.** Two call sites, both currently one line:
- `scripts/run_eu_s2_district_campaign.py:135` — `generate_european_dwelling_layout(footprint,
  requested_dwelling_count=allocation.units_per_floor)` is called **once** and reused for every storey.
  It must be called **per storey index** with that storey's own count, and the resulting zone list stacked.
- `scripts/emit_eu11_layout_sidecars.py:122` — the same change, so the pop-up shows what was simulated.

Where consecutive storeys have the same count, cache and reuse the partition — do not recompute it, and do
not let caching change the result.

**How to test.** Write `tests/geometry/test_eu13b_dwelling_conservation.py`:
1. For every side-car under `openubem/outputs/eu_evidence/EU-11/*/layouts/**/*.json` with
   `geometry_outcome` starting `DWELLING_LAYOUT_EMITTED`, assert
   `sum(len(floor["dwellings"]) for floor in floors) == dwellings_total`. Must be **1,078 of 1,078**, was
   263 of 1,078.
2. For a sampled 20 rebuilt IDFs, assert the count of distinct `_F<k>_dwelling_<j>` zone names equals
   `dwellings_total`. `way/51781396` must give **69**, not 85.
3. A property test: for random `(N_total, N_floors)` in `1..400 × 1..30`, the emitted total equals
   `N_total` exactly.

### 2. `T02` — Cap dwellings per floor at the ruled grid, fail closed above it

**What.** The ruled grid table (`MVP` §4.2, report §5) defines exactly five densities: 1, 2, 3–4, 5–6, ≥7,
realised as `1×1`, `2×1`, `2×2`, `3×2`, `4×2`. **Eight units per floor is the maximum the ruling defines.**
A storey needing more than 8 has no ruled layout.

**Why.** Emitting 32 strips on one plate is not an approximation of the ruled scheme; it is a different
model, and it produced the degenerate geometry in `relation/3730743`.

**How.** When a storey's `dwelling_count > 8`, do **not** partition it. Fall back to the massing box for
that building with the new named reason `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`, and record the observed
per-floor count in the side-car. 🔴 **Never subdivide beyond 8 to "keep coverage up" — measure the gap,
name it, and let the count fall.** Report the census of buildings that drop out (expected order 62; report
the number you actually measure, per district).

**How to test.** Assert no emitted side-car has a storey with more than 8 dwelling polygons; assert every
building that previously emitted >8 now carries exactly that reason token; assert the fallback reason
appears in `RESULTS_EU-13B.md`'s census with a per-district count.

### 3. `T03` — Footprint regularization before the grid (`ConvexToConcave`, `EdgeTo4`)

**What.** Implement report §3 in `openubem/geometry/european_residential.py` as two new pure functions,
`regularize_footprint_orthogonal(footprint, *, tolerance_m=0.15)` and
`fit_quadrilateral_domain(footprint)`, returning the regularized plate plus an explicit record of what
changed.

**Why.** An isoparametric `n_u × n_v` grid is only defined on a clean quadrilateral `S(u,v)` domain. Cutting
a raw GIS polygon is what produced defects 3 and 4.

**How.** Follow report §3.1–§3.3: drop colinear vertices within ε = 0.15 m; align edges to the principal
minimum-bounding-box axes; fit the 4-vertex envelope preserving gross floor area; normalise the UV domain
so exterior normals point outward.

🔴 **Regularization changes the shell, so it must never be silent.** Emit, per building:
`plate_area_raw_m2`, `plate_area_regularized_m2`, `plate_area_delta_fraction`,
`vertices_raw`, `vertices_regularized`. Any building whose area delta exceeds **2 %** falls back to the
massing box with reason `REGULARIZATION_AREA_DELTA_GT_2PCT` rather than being silently reshaped. Report the
distribution of `plate_area_delta_fraction` in `RESULTS_EU-13B.md` — it is the honest cost of this task, and
the owner must be able to read it.

**How to test.** Golden tests on hand-built polygons (rectangle, L, U, cross, notched) asserting the
regularized output vertex count is 4, area is preserved within the stated tolerance, and normals are
outward. Assert the two functions import nothing from the partitioner (they are inputs to it).

### 4. `T04` — The ruled `n_u × n_v` grid partition

**What.** A new function `generate_european_grid_layout(plate, *, dwelling_count, ...)` implementing report
§5: `u_i = i/n_u`, `v_j = j/n_v` on the regularized domain, with the ruled density → grid map:

| dwellings on this storey | grid | note |
|---|---|---|
| 1 | `1 × 1` | full plate |
| 2 | `2 × 1` | dual aspect |
| 3–4 | `2 × 2` | quadrant corner units around the centroidal core |
| 5–6 | `3 × 2` | 4 corner dual-aspect + 2 middle single-aspect along a corridor |
| 7–8 | `4 × 2` | double-loaded spine |

**Why.** This — not equal strips — is the ruled scheme, and it is what `figure_4_2_dwelling_layout_schemes.svg`
draws.

**How.** Keep `generate_european_dwelling_layout` as the entry point and make the grid the **primary**
scheme; the existing sweep/radial partitioner stays as the explicitly-labelled secondary route for storeys
the grid cannot serve (see `T05`). Every emitted side-car must carry a truthful `scheme` string — one of
`ruled_grid_1x1`, `ruled_grid_2x1`, `ruled_grid_2x2`, `ruled_grid_3x2`, `ruled_grid_4x2`, or the secondary
scheme's own name. 🔴 **A layout labelled `ruled_grid_*` that is not a grid is worse than a fallback.**

**How to test.** For each ruled density, assert the emitted polygon count, that the union equals the plate
within the existing `audit_european_floor_partition` tolerance (**do not loosen that tolerance**), and that
the adjacency graph matches the figure's topology (corner units have exactly 2 exterior facades in `2×2`;
the 2 middle units in `3×2` have exactly 1). Run the existing `GEO-*` suite and report it unchanged.

### 5. `T05` — Morphological branching (report §6)

**What.** Choose the partition route from the plate's own morphology, before partitioning:
- `L/W < 2.0`, convex → point-block grid (`T04`).
- `L/W ≥ 2.0` → **I-shape linear gallery**: inject a central double-loaded circulation spine, `w = 1.80 m`,
  along the longitudinal axis; subdivide the two lateral bands symmetrically.
- Re-entrant reflex vertex (θ > 180°) → **L-shape decomposition**: split along the reflex orthogonal axis
  into main and secondary wings, allocate dwellings by area fraction `A_wing / A_total`, keep the party-wall
  line continuous at the junction.
- Interior ring / courtyard → subtract the courtyard void, unfold the C-band into three wings.

**Why.** Report §6.1–§6.4. It is also the direct fix for the cross-shaped and L-shaped degeneracies visible
in the current pop-ups.

**How.** One dispatcher returning the chosen route plus the reason it was chosen; the route name goes in the
side-car. The corridor spine is **geometry only** in this task — whether it becomes an unconditioned zone is
`T06`, which is blocked.

**How to test.** Golden morphology fixtures (rectangle, slab `L/W = 4`, L, U, cross) asserting the chosen
route, the emitted zone count, and area conservation. Assert dwelling counts across wings sum to the storey
total.

### 6. `T06` — Unconditioned circulation core — 🔴 **BLOCKED on `D-EU-36`, do not start**

The ruled scheme (`MVP` §4.3, report §7) puts a **centroidal unconditioned stair core of 12–25 m², 6–12 % of
gross floor area**, extruded from `z=0` to the roof, sharing a party wall with every dwelling.

The real-footprint path deliberately emits **no core at all** today, and that is not an oversight: it is the
`D-EU-01` / `GEO-01` area-conservation contract, stated in
`generate_european_dwelling_layout`'s own docstring — an observed shell has no declared gross-to-conditioned
relationship, so a core can only be created by **carving conditioned area away** (shrinking the simulated
floor area of every building, changing every EUI denominator) or by **adding area outside the shell**
(making the building larger than its observed footprint). `generate_external_unconditioned_core`
(`european_residential.py:377`) implements the second and refuses any non-rectangular plate.

**The owner must rule which one applies to real footprints before this task can be written.** Until
`D-EU-36` is ruled: emit no core, keep `has_unconditioned_core = false`, and make sure the pop-up header
agrees (`T07`).

### 7. `T07` — Habitability gate correction, and the pop-up header

**What.** (a) Implement report §9's automated correction: when a dwelling's exterior facade contact falls
below `L_min = 2.50 m`, **downgrade the grid one step or rotate it along the long facade axis and retry**,
instead of only failing the whole building closed. Fail closed only after both corrections fail, keeping the
existing reason token. (b) Fix the pop-up header: `scripts/generate_eu_3d_viewers.py:401` prints
`Unconditioned core: Yes` for buildings whose side-car says `has_unconditioned_core: false` — visible today
on `way/51781396`. It must read the side-car's emitted field, exactly as
`emit_eu11_layout_sidecars.py:183` was already corrected to do.

**Why.** (a) is the difference between "we could not lay this building out" and "we did not try the ruled
correction". (b) is the same class of false claim the owner already caught once in `EU-13`.

**How to test.** A fixture whose `3×2` grid produces a landlocked cell must emit a valid `2×2`, not a
fallback; assert the downgrade is recorded in the side-car. For (b), assert across all side-cars that the
rendered header string and `has_unconditioned_core` agree — **0 disagreements**, currently non-zero.

### 8. `T08` — Re-emit, regenerate, and report

Re-run `scripts/emit_eu11_layout_sidecars.py` (all districts **except** `IT-BOL-GALVANI2`, which is
`EU-14B`) and `scripts/generate_eu_3d_viewers.py`. Verify the `outputs_3D/` mirror is byte-identical.

Write `openubem/outputs/eu_evidence/EU-13B/RESULTS_EU-13B.md` containing, at minimum: the before/after
conservation census (815 → expected 0 non-conserving); the per-district scheme histogram; the
`plate_area_delta_fraction` distribution from `T03`; the census of buildings newly dropped to massing box
and why, per reason token; and the habitability-downgrade count from `T07`. **No number without its
population.** Append one `walkthrough_progress_log.csv` row per task. Register every error you solve in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in house format before closing.

### 9. `T09` — Resimulation on Speed — 🔴 **UNBLOCKED `2026-08-30` (`D-EU-38`) — Madrid, Lyon, London only**

`T01`–`T05` change zone counts and zone geometry, therefore heating and floor area, therefore **every pooled
EUI in `RESULTS_EU-11.md`**. This is exactly the `D-EU-35` desync, and the rule learned there stands:
**the pop-up and the simulated IDF must never again describe different geometry.** So either both are
regenerated or neither is.

**What.** Rebuild the IDFs for Madrid, Lyon and London (not Bologna — its layouts are `EU-14B`) from the
`T01`–`T08` geometry, report per district the count of buildings whose zone count changed and the mean/max
change, then submit the full resimulation to Speed and harvest it. Regenerate
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_ES-MAD-BERRUGUETE_viewer.html`,
`eu_FR-LYO-HAUTCOEURPENTES_viewer.html` and `eu_GB-LDN-STDUNSTANS_viewer.html` from the harvested manifests so
every pop-up and every EUI describe the same geometry. Update `RESULTS_EU-11.md`'s pooled figures for these
three districts and state plainly that Bologna's figure in that document still describes its pre-`EU-14B`
zoning.

🔴 **`sbatch --array` only, fire-and-forget, from `speed-submit2` — never `srun`, never compute on the login
node.** Remote shell is `tcsh`: use the `_ssh()` helper (`scripts/cluster/t08_harvest_results.py:104`) or port
its `bash -lc` wrapper, never a bare command string. Log the real remote error text on any retry, not a
label.

### 10. What must never happen

- Never loosen `audit_european_floor_partition`'s tolerances to raise coverage.
- Never emit a layout whose `scheme` string does not describe the geometry actually emitted.
- Never keep a number in `RESULTS_EU-11.md` that this task's geometry has invalidated — if `T09` is not run,
  say plainly in `RESULTS_EU-13B.md` that the published EUIs still describe the **old** zoning.
- Never impute a dwelling count, storey count or height to raise a count. Measure the gap and name it.
- Never re-run `scripts/emit_eu11_layout_sidecars.py` against `IT-BOL-GALVANI2` — it corrupts the manifest;
  that repair is `EU-14B` `T01`.

### 11. Stop-and-report points

1. After `T02` — report the conservation census and the >8/floor dropout census before writing any grid code.
2. After `T05` — report the full scheme histogram and area-delta distribution before touching the viewers.
3. After `T08` — report, then continue directly to `T09` (ruled open `2026-08-30`, Madrid/Lyon/London only).
   `T06` remains blocked; do not touch it.
4. After `T09` harvests — report the resimulated pooled EUIs per district beside the `RESULTS_EU-11.md`
   figures they replace, then **stop**. `T06` still needs the carve-vs-add ruling.

### 12. `T10` — Why 226 Lyon residential buildings get neither a simulation nor a layout

**What.** Measure and report — do not fix — why `FR-LYO-HAUTCOEURPENTES` simulates only 297 of 530
residential buildings, when the ones that drop out have observed height and observed storeys.

**Why.** The owner clicked `BATIMENT0000000240879941_part0` (residential, 27.9 m measured height, 4 storeys,
500 m²) and `BATIMENT0000000240880045_part0` (residential, 26.9 m, 10 storeys, 954 m²) and got
`Not simulated in EU-11 campaign. No dwelling layout generated.` Neither is a missing-data case.

**The cause is already located; confirm it, do not re-derive it.** `derive_bdtopo_building_type`
(`openubem/semantic/european_archetype_mapping.py:185`) implements the ruled `D-EU-04-G` Option G1
two-signal table, fail-closed. The table covers only four cells:

| dwellings | storeys | verdict |
|---|---|---|
| 1 | ≤ 4 | `TH` / `SFH` |
| 2–12 | ≤ 4 | `MFH` |
| ≥ 15 | ≥ 5 | `AB` |
| 13–14 | any | `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` |
| **everything else** | | **`TYPOLOGY_SIGNALS_DISAGREE`** |

So a real, well-attributed building with **10 storeys and 8 dwellings**, or **3 storeys and 20 dwellings**,
has no ruled type. Lyon's exclusion census: `TYPOLOGY_SIGNALS_DISAGREE` **189**,
`TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` **37** — **226 of the 233 excluded**, against only 7 genuine
missing-datum exclusions.

**How.** Produce, from `openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg`, the
joint `(dwellings, storeys)` distribution of the 226, so the owner can see exactly which uncovered regions
of the table they occupy and how many buildings sit in each. Do the same for Madrid's 77 and London's 345
`UNMAPPABLE_RESIDENTIAL_TYPE`.

🔴 **Extending that table is an owner ruling (`D-EU-37`), not an executor decision.** Never widen a band,
never break a 13–14 tie, never assign a type the table does not give. Report the distribution and stop.

**How to test.** The per-region counts must sum exactly to the `blocker_exclusions` totals in each
district's `summary_prerun.json`. Any discrepancy is a finding.
