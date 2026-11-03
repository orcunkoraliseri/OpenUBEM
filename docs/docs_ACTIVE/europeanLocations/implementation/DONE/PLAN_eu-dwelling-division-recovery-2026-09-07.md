# PLAN — recover the discarded dwelling divisions: 1,524 simulated buildings carry no floor division (`eu-dwelling-division-recovery-2026-09-07`)

**Slug:** `eu-dwelling-division-recovery-2026-09-07`. **Opened 2026-09-07.** Registered as **`D-EU-109`**.
**Predecessor, not reopened:** `implementation/DONE/PLAN_eu-nocore-interzone-rootcause-2026-09-04.md`
(`D-EU-99`) — its `T03` **STOPPED** on 2026-09-04 with the remedy refuted and the next step explicitly left
to the director. This plan takes that decision and finishes the work.
Prior state: `STATE_european_locations_v5.md` §3 `FINDING 249`, §4 `D-EU-99`, `FINDING 210`;
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791`.

**Owner ruling 2026-09-07 (verbatim):** *"even i am seeing these buildings under the EUI visualisation but
they do not have floor division, this is absurd. witout floor division no simualtion."*

**Owner authorisation 2026-09-07 (verbatim): *"go ahead, execute this plan too"*** — `D-EU-109` is
authorised end to end, including the `D-EU-109` e merged re-emission and the single Speed campaign at T06
and the EUI restatement at T07. The director signs `CP-1`, `CP-2` and `CP-3` on the plan's own measured
gates; the owner is returned to only if a gate fails and the plan would have to change to proceed.

---

## 1. What the owner saw, measured

The owner opened `outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html` on two buildings that are coloured by
EUI — i.e. they were simulated — and found each one drawn as a single undivided plate per storey,
`Dwellings: 0`, badged `MASSING BOX (read from IDF)`:

| building | storeys | area | badge | viewer's stated reason |
|---|---|---|---|---|
| `BATIMENT0000000240879996_part0` | 6 | 7,741 m² | `MASSING BOX` | `L_SHAPE_DECOMPOSITION_FAILED` |
| `BATIMENT0000000240879972_part0` | 7 | 1,713 m² | `MASSING BOX` | `L_SHAPE_DECOMPOSITION_FAILED` |

**Both of those plates were cut successfully by the no-core cutter.** From the `_r5` census
(`EU-21/district_plans/FR-LYO-HAUTCOEURPENTES_nocore_2026-09-03_r5.json`):

| building | group | `k` | `drawn_per_floor` | `status` | `spread` | verdict |
|---|---|---|---|---|---|---|
| `…879996_part0` | `COMPLEX_MULTI_WING` | 6 | 6 | `direct` | **0.9953** | PASS ALL 7 |
| `…879972_part0` | `U_OR_T_SHAPE` | 4 | 4 | `direct` | **0.9999** | PASS ALL 7 |

Near-perfectly balanced six- and four-dwelling cuts exist for these buildings. **The IDF that was simulated
does not contain them.** The dwelling layout was computed and then thrown away at emission time.

🔴 **`FINDING 261` — 45.6 % of the simulated fleet was simulated with no dwelling division at all.**
Counted directly, by grepping the emitted ceiling82 IDFs for a `…_F0_whole` zone (an undivided
one-zone-per-storey building) and cross-checking against each district manifest's `geometry_outcome`. The
two agree to the building, fleet-wide:

| District | simulated | **undivided** | share | of which the no-core cut *exists* and gives `k >= 2` |
|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | 1,174 | **642** | 54.7 % | 476 |
| `FR-LYO-HAUTCOEURPENTES` | 507 | **173** | 34.1 % | 103 |
| `GB-LDN-STDUNSTANS` | 451 | **49** | 10.9 % | 33 |
| `IT-BOL-GALVANI2` | 1,212 | **660** | 54.5 % | 555 |
| **fleet** | **3,344** | **1,524** | **45.6 %** | **1,167** |

By `geometry_outcome`, the 1,524 decompose exactly:

| count | `geometry_outcome` | meaning |
|---|---|---|
| **1,239** | `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` | the layout **was** emitted, then force-rerouted to one zone per storey |
| **213** | `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` | no dwelling count, so nothing to cut into |
| **72** | `FALLBACK_PENDING_LAYOUT` | Madrid only |
| **1,524** | | = the `…_whole` IDF count, 642 + 173 + 49 + 660 |

**1,167 of the 1,524 already have a valid, checked, multi-dwelling no-core cut on disk.** The remaining 357
are genuinely `k <= 1` — one dwelling per storey — and are correctly undivided; they are *not* a defect and
are out of scope. **0** of the 1,524 are missing from the census.

⚠ **The viewer's stated reason is stale and misleading.** `L_SHAPE_DECOMPOSITION_FAILED` is raised inside
`generate_european_ruled_storey_layout` (`openubem/geometry/european_residential.py:1303`) — the **parked
`"ruled"` regime**. The live regime is `EUROPEAN_LAYOUT_REGIME = "nocore"` (`european_residential.py:2636`),
which never raises it. The badge text is read from the EU-17 side-car as annotation only
(`scripts/generate_eu_3d_viewers.py:910-911`, `:980`), so the viewer is quoting a refusal from a regime that
did not produce this IDF. Fixed in T05.

---

## 1b. All four districts, per district (director, 2026-09-07 — owner asked whether this is district-specific)

**It is not.** Every district carries the defect; only the rate differs, and it tracks morphology, not
geography — the two districts built from large non-convex blocks (Madrid, Bologna) sit near 55 %, the
terrace-row district (London) near 11 %.

| District | simulated | undivided | share | recoverable (`k >= 2` on disk) | genuinely `k <= 1` | also `D-EU-107` imbalanced |
|---|---|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | 1,174 | **642** | 54.7 % | 476 | 166 | 88 |
| `FR-LYO-HAUTCOEURPENTES` | 507 | **173** | 34.1 % | 103 | 70 | 9 |
| `GB-LDN-STDUNSTANS` | 451 | **49** | 10.9 % | 33 | 16 | 1 |
| `IT-BOL-GALVANI2` | 1,212 | **660** | 54.5 % | 555 | 105 | 134 |
| **fleet** | **3,344** | **1,524** | **45.6 %** | **1,167** | **357** | **232** |

Consequences the executor must carry through every remaining task:

1. **No district is a clean control.** Nothing in this fleet can be presented as a finished neighbourhood
   until T03 lands: the least-affected district still has 49 buildings simulated as single-zone massing.
2. **Every one of the 232 `D-EU-107`-imbalanced-and-undivided plates is recoverable** (`232 / 232`), so
   `D-EU-109` restores the division and `D-EU-107` then balances it — the pinned landing order is load
   bearing, not a preference (`FINDING 262`).
3. **The 357 genuinely `k <= 1` buildings** (`ES-MAD` 166, `FR-LYO` 70, `GB-LDN` 16, `IT-BOL` 105) are
   correct as they stand and must be **unchanged** by every gate below. They are not a residual to chase.
4. **Re-emission and campaign scope, fleet-wide:** the union of `D-EU-109`'s 1,167 recoverable and
   `D-EU-107`'s 344 affected is **1,279 distinct buildings** (the 232 overlap exactly), plus `D-EU-108`'s
   **255** newly admitted London buildings that have never been simulated (187 age-inherited + 68
   straddle-disambiguated), for a single Speed array of **1,534 cases**. No building is simulated twice.

---

## 2. Where the layout is discarded, cited

`scripts/run_eu_s2_campaign.py:560-599`, inside `build_idf_for_building`:

```
mismatched  = find_mismatched_interzone_pairs(idf)          # :561
near_duplicate = _has_near_duplicate_vertex_surfaces(idf)   # :567
at_risk = mismatched or near_duplicate                      # :568
if at_risk:                                                 # :569
    reason = "interzone_vertex_mismatch" if mismatched else "near_duplicate_vertex"
    did_reroute = _force_reroute_room_layout_to_one_zone_per_floor(idf, zones, reason)   # :571
```

`_force_reroute_room_layout_to_one_zone_per_floor` deletes every dwelling zone and replaces the storey with
one whole-plate zone. The district campaign then records
`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` (`scripts/run_eu_s2_district_campaign.py:530`,
`scripts/emit_eu11_layout_sidecars.py:319`).

The gate is `_has_near_duplicate_vertex_surfaces` (`run_eu_s2_campaign.py:94-141`). It returns `True` on the
**first** ring vertex of **any** interzone-paired `BUILDINGSURFACE:DETAILED` that satisfies either
sub-condition:
- an adjacent edge shorter than `NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005` (`:77`), or
- an interior angle greater than `180 - COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` = **179.9°** (`:91`, `:139`).

One such vertex anywhere in a 7,741 m², six-storey, six-dwelling building destroys the whole building's
layout.

**The predecessor plan already established which sub-condition actually fires, on real geometry**
(`DONE/PLAN_eu-nocore-interzone-rootcause-2026-09-04.md` §8 `T03`, three real reroute-labelled buildings
including this owner's own `BATIMENT0000000240879996_part0`, no exception):
1. **100 % of the defective vertices are the COLLINEAR sub-check** (179.91–179.99°). **Zero** are the
   proximity sub-check.
2. The defective vertex is **inherent to the footprint ring**, repeating bit-for-bit on the ground floor, the
   roof and every interfloor pair (`way/435505191`: `angle = 179.9724` on all of them).
3. Many defective surfaces have **no interzone partner at all**.
4. Where a partner exists, **both sides already carry the identical value** — there is no asymmetry.
5. Therefore `CP-1`'s picked remedy (d) — snap the pair to one shared coordinate — **cannot work**: a
   collinear point stays collinear at every position on its own line. `T03` stopped rather than write a
   synthetic-green test, and left three candidate directions to the director.

`T04` of that plan independently confirmed (2) and (4) by dumping both rings of a documented `FINDING 210`
pair: all 9 vertex pairs identical to 9 decimal places, yet EnergyPlus still fataled — so *identical input
coordinates is not proof of safety* for the collinear sub-case.

**Director's own confirmation at fleet scale, 2026-09-07.** Applying the detector's exact math
(`0.005 m`, `179.9°`) to the census footprint ring of every simulated building:

| District | undivided footprints carrying a defective vertex | divided footprints carrying one |
|---|---|---|
| `ES-MAD-BERRUGUETE` | 545 / 636 (**85.7 %**) | 230 / 532 (43.2 %) |
| `FR-LYO-HAUTCOEURPENTES` | 81 / 171 (**47.4 %**) | 15 / 334 (4.5 %) |
| `GB-LDN-STDUNSTANS` | 25 / 47 (**53.2 %**) | 34 / 402 (8.5 %) |
| `IT-BOL-GALVANI2` | 394 / 660 (**59.7 %**) | 161 / 552 (29.2 %) |
| **fleet** | **1,045 / 1,514 (69.0 %)** | **440 / 1,820 (24.2 %)** |

A 69 % vs 24 % separation on the footprint ring alone, before the cut adds any vertex of its own. The
mechanism is a **redundant, geometrically meaningless vertex sitting on a straight edge of the source
footprint**, inherited into every surface the emitter builds from it.

---

## 3. Hard rules for the executor

1. 🔴 **`openubem/idf/surfaces.py` is non-editable** (`D-EU-41`). Every change lands in the European path.
2. 🔴 **Never widen a tolerance to buy a pass.** `NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005` and
   `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1` are **frozen**. `FINDING 249` is explicit that the fix is
   "not a threshold move and not a relaxation of `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`". An executor that
   changes either constant has failed the task.
3. 🔴 **Never disable or weaken the reroute safety net.** The `mismatched = True` branch stays exactly as it
   is. This plan removes the *cause*, so the net stops firing; it does not remove the net.
4. **The seven no-core checks are frozen** (`D-EU-82`, `D-EU-87`, `D-EU-89` clause 2), as is
   `MAX_FLAT_ASPECT = 2.5`.
5. **Area is the conservation law.** Every ring this plan rewrites must preserve its own area to within
   `1e-6` of the original in relative terms. A vertex that cannot be removed inside that budget is **left in
   place and the building reroutes honestly**, exactly as today.
6. **No new IDF may silently replace a published one.** Re-emission goes to a new dated folder; never write
   into `EU-11/<DISTRICT>_ceiling82_2026-09-05/`.
7. Cluster work (T06/T07) is **director-only**. The executor never runs `sbatch`, `ssh` or `srun`.
8. No code comments. No new files outside §4. No network fetch.
9. If the plan is ambiguous, **stop and quote the conflict** — never invent a resolution. `T03` of the
   predecessor plan did exactly this and was right to.

---

## 4. File layout (only these may be touched)

Code:
- `scripts/run_eu_s2_campaign.py` — the ring-cleanup pass and its wiring (T02)
- `openubem/geometry/european_residential.py` — footprint cleanup before the cut (T02)
- `tests/test_eu_collinear_ring_cleanup.py` — new unit tests (T02)
- `scripts/generate_eu_3d_viewers.py` — T05 only, the stale-reason fix

Evidence written (new), all under `openubem/outputs/eu_evidence/EU-21/division_recovery/`:
- `undivided_census_2026-09-07.csv` (T01)
- `defect_probe_2026-09-07.csv` (T01)
- `reroute_before_after_2026-09-07.csv` (T03)

Re-emission (T04): `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_divided_2026-09-08/`

Read-only, cited never edited: `openubem/idf/surfaces.py`, `EU-11/*_ceiling82_2026-09-05/**`,
`EU-21/district_plans/*_r5.json`, `EU-21/interzone_rootcause/**`, `rules/*.html`,
`DONE/PLAN_eu-nocore-interzone-rootcause-2026-09-04.md`.

---

## 5. Dependency decisions (pinned by the director — the executor does not re-decide these)

**`D-EU-109` a — the remedy is vertex *removal*, not vertex *snapping*.** Of the three directions `T03` left
open, this plan takes **(i)**: delete the redundant near-collinear vertex from the ring. It is the only one
that matches all five facts above — it works on a partner-less surface, it works when both sides are already
identical, and it is the only operation that can clear a collinear flag at all. Options (ii) (special-case
unpaired surfaces) and (iii) are **not** taken: (ii) only hides the flag on surfaces the detector already
excuses by design (`run_eu_s2_campaign.py:100-105`) and would leave the paired instances firing.

**`D-EU-109` b — the cleanup runs at two points, not one.** The defect is footprint-inherent (fact 2) *and*
the cut can introduce its own collinear vertex where a cut line meets a plate edge at 180°. So: clean the
**source footprint ring before the no-core cut** (so the cutter sees a clean plate and its `C5` vertex budget
is not wasted on redundant points), **and** clean **every zone ring after the cut, immediately before
extrusion**. One shared function, called twice. Cleaning only the footprint would leave cut-introduced
vertices; cleaning only after the cut would let the cutter waste `C5` budget on redundant vertices.

**`D-EU-109` c — the removal criterion is the detector's own math, unchanged.** A vertex is removed iff it
satisfies exactly the condition `_has_near_duplicate_vertex_surfaces` tests (adjacent edge
< `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`, or interior angle > `180 − COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG`),
read from those same two module constants — never a second, looser copy of them. Removal is iterative:
deleting one vertex can make its neighbour collinear, so repeat to a fixed point, with a hard iteration cap
equal to the ring's vertex count. A ring that would fall below 3 vertices is left untouched.

**`D-EU-109` d — this is a restatement, and it must be declared as one.** The published district EUIs
(`STATE` §7/§8, `BRIEF` §6) were computed with 45.6 % of the fleet carrying no interior partitions. A building
simulated as one open plate per storey has different internal loads, infiltration surface and interzone heat
flow than the same building divided into six dwellings. **Every district EUI will move**, and the direction is
not assumed here — it is measured at T07 and restated with both populations named. No pre-fix EUI may be
quoted alongside a post-fix one without saying which is which.

**`D-EU-109` e — one re-emission, one Speed campaign, for all three open plans.** `D-EU-107` (balance),
`D-EU-108` (London recovery, +307 buildings) and this plan all end in "re-emit and re-simulate". They are
**merged into a single wave**: this plan's engine change lands **first** (it is the one that decides whether a
building has dwelling zones at all), `D-EU-107`'s balance change second, `D-EU-108`'s admissions third, and
then **one** `sbatch --array` covers the union. No building is simulated twice. Sequencing is the director's
to run; the executor of this plan stops at T05.

---

## 6. Tasks

### T01 — Freeze the undivided set and confirm the mechanism on the emitted IDFs

**What:** two CSVs.
`undivided_census_2026-09-07.csv` — one row per simulated building, all four districts:
`building_id, district, stem, geometry_outcome, has_whole_zone (Y/N), census_k, census_drawn_per_floor,
census_status, census_spread, census_verdict, storeys, area_m2, recoverable (Y/N)`, where `recoverable` is
`has_whole_zone == Y and census_status != ERROR and census_drawn_per_floor >= 2`.
`defect_probe_2026-09-07.csv` — for every building in the census, the result of running
`_has_near_duplicate_vertex_surfaces`'s **own math** (imported read-only from `scripts/run_eu_s2_campaign.py`,
never re-typed) over the building's **emitted ceiling82 IDF** surfaces:
`building_id, n_surfaces_checked, n_defective_surfaces, first_defect_kind (collinear|proximity),
first_defect_angle_deg, first_defect_edge_m, defect_on_footprint_ring (Y/N), has_interzone_partner (Y/N)`.

**Why:** §1's counts were taken by the director from the manifests and a `_F0_whole` grep; the mechanism
evidence in §2 comes from a 16-building sample. Both must hold on the full 3,344 before any code moves.

**How to test:** reproduce §1's two tables **exactly** — 642 / 173 / 49 / 660 undivided, 1,524 fleet;
476 / 103 / 33 / 555 recoverable, 1,167 fleet; and 1,239 / 213 / 72 by `geometry_outcome`. Report any cell
that differs instead of adjusting it. Then report, over `defect_probe`: the split of `first_defect_kind`
(the predecessor's 16-building sample says ~100 % `collinear` — report the real fleet figure), and the
2 × 2 contingency of `n_defective_surfaces > 0` against undivided/divided.

### T02 — The ring cleanup

**What:** one function that takes a ring and returns it with every vertex the detector would flag removed,
plus its two call sites (`D-EU-109` b).
**How:**
- Add `_drop_redundant_ring_vertices(ring)` to `scripts/run_eu_s2_campaign.py`, immediately after
  `_has_near_duplicate_vertex_surfaces`. It reads `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` and
  `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` from that module (`D-EU-109` c), iterates to a fixed point, refuses
  to go below 3 vertices, and refuses any removal whose relative area change exceeds `1e-6` (hard rule 5).
- Call site 1, **before the cut**: in `openubem/geometry/european_residential.py`, clean the footprint the
  no-core path is about to cut, at the entry to `generate_european_nocore_storey_layout` (`:1338-1351`),
  before `cut_storey_nocore` is called. Import the function; do not duplicate its body.
- Call site 2, **after the cut, before extrusion**: in `build_idf_for_building`
  (`scripts/run_eu_s2_campaign.py`), clean every zone ring produced by the layout before the geometry is
  extruded and `intersect_match` runs — i.e. upstream of `:561`, not inside the `at_risk` branch.
- Leave `_symmetrize_near_duplicate_interzone_vertices` (written and never validated by the predecessor's
  `T03`) **unwired and unused**; do not delete it, do not call it.
**How to test:** `tests/test_eu_collinear_ring_cleanup.py`, covering at minimum:
1. a square with one extra vertex inserted at the midpoint of an edge → that vertex is removed, area
   unchanged, 4 vertices out;
2. a ring with three consecutive collinear points → all redundant ones removed in one call (fixed point);
3. a ring with a 179.95° vertex whose removal would exceed the `1e-6` area budget → **not removed**, ring
   returned unchanged (the honest-refusal case);
4. a triangle → unchanged (cannot go below 3);
5. a ring with an adjacent edge of 0.004 m → the proximity sub-case is removed too;
6. an already-clean ring → returned byte-identical.
Then, without re-emitting anything: re-run `_has_near_duplicate_vertex_surfaces` over T01's
`defect_probe` population **with the cleanup applied in memory**, and report how many buildings stop being
`at_risk`.

### T03 — Re-emit in place and measure the reroute collapse (no simulation)

**What:** rebuild the IDFs for all 3,344 simulated buildings through the fixed path into a scratch tree, and
write `reroute_before_after_2026-09-07.csv`:
`building_id, district, outcome_before, outcome_after, whole_before (Y/N), whole_after (Y/N),
n_zones_before, n_zones_after, dwellings_after, floor_area_before, floor_area_after, area_delta_pct`.
**Why:** this is the measurement that decides whether the remedy is worth a campaign, and it costs no
EnergyPlus time.
**How to test, three gates, all hard:**
1. **Recovery:** report how many of T01's **1,167 recoverable** buildings now emit real dwelling zones,
   **broken out per district against §1b's own denominators** (`ES-MAD` 476, `FR-LYO` 103, `GB-LDN` 33,
   `IT-BOL` 555) — a fleet total alone is not enough, since the owner's question is per neighbourhood.
   Report the honest residual — buildings still rerouting, with their `first_defect_kind`.
2. **No loss:** **zero** buildings that were divided before may become undivided after. Any that do stops
   the task; name them.
3. **Area conservation:** `abs(area_delta_pct) <= 0.2 %` for **every** building (superseded from
   `1e-4 %` by the `CP-2` SIGNED ruling `D-EU-109 f` above — `1e-4 %` predates the measured budget). The conditioned floor area
   is the EUI denominator; if it moves, every EUI moves for a second, unrelated reason. Report the max.
Also report the 357 genuinely `k <= 1` buildings as **still undivided** — they must not change, per
district (`ES-MAD` 166, `FR-LYO` 70, `GB-LDN` 16, `IT-BOL` 105).
4. **Per-district completion statement.** For each district, state the resulting undivided count and share,
   in the same shape as §1b's table, so `T07` can say plainly which neighbourhoods are finished. A district
   is finished only when its undivided count equals its genuinely `k <= 1` count.

### T03m — The merged re-emission (`D-EU-109 g`, supersedes T03's scope, not its gates)

**Director's ruling 2026-09-07 (`D-EU-109 g`).** The owner has asked for the arc to finish today. Running
`D-EU-109` T03, `D-EU-107` T04 and `D-EU-108`'s re-emission as three separate passes would rebuild the same
IDFs three times and produce three mutually stale hash controls. They are merged into **one** re-emission.
Emission is minutes; only simulation is expensive, so nothing is risked by rebuilding everything once and
simulating only what actually changed.

**Scope.** One pass over all four districts, each at its **final** population: `ES-MAD-BERRUGUETE`,
`FR-LYO-HAUTCOEURPENTES` and `IT-BOL-GALVANI2` from their `*_ceiling82_2026-09-05/` prepared sets, and
`GB-LDN-STDUNSTANS` from `GB-LDN-STDUNSTANS_recovery_2026-09-07/` at **706**, not the ceiling82 451. Output
goes to new `<DISTRICT>_final_2026-09-07/` trees. The `*_ceiling82_2026-09-05/` trees are never written to.

**Engine state at emission — all three fixes, together and only these:**
1. `D-EU-109 f`'s ring cleanup criterion, replacing the `1e-6` relative-area test currently at
   `scripts/run_eu_s2_campaign.py:210`: remove a vertex iff its perpendicular distance to the chord is
   `<= 0.010 m` **and** the per-removal relative ring-area change is `<= 1e-3`, with the cumulative
   per-ring change capped at `<= 2e-3`. The two frozen detector constants
   (`NEAR_DUPLICATE_VERTEX_TOLERANCE_M`, `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG`) are **not** touched.
2. `D-EU-107 f`'s `C12` scorer, already carried into `openubem/geometry/european_nocore.py` by that plan's
   T03 — used as-is, not re-derived here.
3. `D-EU-108 f`'s London admissions, already in `scripts/run_eu_s2_district_campaign.py` — used as-is.

**Gates.** T03's four gates above stand unchanged and are measured from this pass, plus:
5. **`D-EU-107` `C12` recovery**, per district, on the re-emitted plates — reported against the 344/275/69
   frozen in that plan's `CP-2`. No `C12` claim may be made from a pre-`D-EU-109` emission (`FINDING 262`).
6. **Hash control.** Every building that is neither recoverable-undivided nor `C12`-affected must re-emit
   with an identical `idf_sha256`. The `FINDING 263` population
   (`*_INTERZONE_MISMATCH_REROUTED` / `near_duplicate_vertex_tolerated_box`) is excluded by name and its
   excluded count is stated, per `D-EU-108`'s `CP-4` precedent.
7. **The simulate list.** Write `simulate_list_2026-09-07.csv` — every building whose `idf_sha256` changed,
   plus the 255 net-new London buildings — with `building_id, district, stem, reason`. This list, and only
   this list, is what reaches Speed. Report its size per district and in total; the pre-pass estimate is
   **~1,534** and any large departure from it must be explained, not accepted.

**How to test:** the seven gates above. No EnergyPlus in this task.

### T04 — Local EnergyPlus battery on a stratified sample

**What:** run EnergyPlus locally on **24 buildings** — 6 per district, stratified: 2 newly-divided with the
largest zone count, 2 newly-divided that were `COMPLEX_MULTI_WING` or `COURTYARD`, 1 unchanged divided
control, 1 unchanged `k <= 1` control.
**Why:** a recovered layout is worthless if EnergyPlus fatals on it — which is the exact failure the reroute
net existed to prevent (`FINDING 210`).
**How:** **parallel, local process pool, 20 concurrent** (CLAUDE.md cluster rules — never a serial loop).
**How to test:** report per building `eplus_return_code`, `severe_errors`, `fatal_errors`, `eui_kwh_m2`
before and after. **Gate: 0 fatals.** Any fatal stops the plan and is reported with the real error text, not
a label.

### T05 — Stop the viewer quoting a parked regime's refusal

**What:** in `scripts/generate_eu_3d_viewers.py`, an undivided building must not display a
`reason` sourced from the EU-17 side-car when that reason belongs to the parked `"ruled"` regime
(`L_SHAPE_DECOMPOSITION_FAILED`, `INTERIOR_RING_COURTYARD_UNFOLD_FAILED`, and the other
`european_residential.py` ruled-path tokens). Show the building's real `geometry_outcome` from the ceiling82
manifest instead.
**How to test:** open the two buildings the owner named and report the badge text before and after. Primary
and mirror `sha256` must match for all four viewers; `node --check` clean on all four.

### T06 — One Speed campaign — **director only**

Per `D-EU-109` e, after `D-EU-107` and `D-EU-108` have landed: one
`sbatch --array=1-N%32 --time=7-00:00:00`, partition `ps`, covering the union of all three plans' affected
buildings, submitted once. Expected `N = 1,534` per §1b clause 4 (1,279 re-emitted + 255 new London); the
real N is whatever T03 and `D-EU-108` T05b actually produce and is stated before submission, never
back-fitted to this figure.

### T07 — Harvest, restate, republish — **director only**

Restate every district EUI with both populations named (`D-EU-109` d), regenerate the viewers, update
`STATE`, `CHECKLIST`, `BRIEF`, and register `FINDING 261`, `FINDING 262` and `D-EU-109` in `STATE` §0/§4/§8.
The restatement is **per district, all four**, each carrying: simulated population, undivided count before
and after, share of buildings with real dwelling zones, and mean EUI before and after. A district may be
described as finished only on T03 gate 4's own criterion.

### T03n — London layout side-car export from the T03m final tree (director-approved 2026-09-08, ahead of T06/T07)

**What:** run `scripts/emit_eu11_layout_sidecars.py --district GB-LDN-STDUNSTANS --evidence-root
GB-LDN-STDUNSTANS=<repo>/openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_final_2026-09-07` and mirror the
result into `docs_ACTIVE` per convention.
**Why:** the London final tree from `T03m (FR+GB slice)` already has 706 prepared buildings and a written
manifest; the side-car JSONs are pure geometry from the Step 2 `.gpkg`, not derived from EnergyPlus results
(confirmed: `scripts/run_eu_s2_district_campaign.py:1170-1179` — the campaign script "builds IDFs and a
manifest and does not simulate"). Director ruling: do not wait for the 299-row Speed simulate list
(`simulate_list_GB_2026-09-07.csv`, not yet submitted) to finish before exporting layouts.
**How:**
1. Read `GB-LDN-STDUNSTANS_final_2026-09-07/`'s manifest (whichever file `emit_eu11_layout_sidecars.py`'s
   `_gb_rows`/`simulated_ids` path reads for this district) and report its row count against 706.
2. If the row count is already 706, run the emitter unmodified. If it is short of 706 (e.g. only the 299
   simulate-list rows), widen `simulated_ids` for this district to the union of the manifest's rows and the
   full `prepared_buildings.csv` `building_id` column for this tree — do not wait for Speed. State exactly
   which change was made, file:line.
3. Run the emitter, capture stdout, and report per CLAUDE.md finishing-work discipline: side-car JSON file
   count actually written to `layouts/relation/` + `layouts/way/` (recursive count, not one subfolder), the
   commit sha (`git rev-parse HEAD`), and the line-ending convention in effect when computing any `sha256`
   over these files (`git config core.autocrlf`, and `file <one .json>` or `unix2dos --check` on one sample).
**How to test:** JSON file count reported must match the manifest row count used in step 1/2. `node --check`
the district's 3D viewer if it re-reads this tree. No EnergyPlus run in this task.

---

## 7. Stop-and-report points

- **`CP-1` — after T01.** The frozen undivided set, §1 reproduced cell by cell, and the fleet
  `first_defect_kind` split. Director signs before any code is touched.
**`CP-1` SIGNED — director, 2026-09-07.** Every T01 cell re-derived independently by the director from
`undivided_census_2026-09-07.csv` (3,344 rows) and `defect_probe_2026-09-07.csv` (3,344 rows); nothing
differs from the executor's report or from §1. Undivided `642 / 173 / 49 / 660 = 1,524`; recoverable
(a valid `k >= 2` cut on disk) `476 / 103 / 33 / 555 = 1,167`; outcome split
`1,239 DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED / 213 FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT
/ 72 FALLBACK_PENDING_LAYOUT`; contingency `173 / 1,351 / 480 / 1,340`.

Two director findings on top of the executor's report, both load-bearing for T02:

1. **The undivided residual defect is 100 % collinear, not 90 %.** The executor's `590 collinear /
   63 proximity` is the *fleet* split over all 653 defect-carrying buildings. Restricted to the 1,524
   undivided buildings, the director measures **173 collinear / 0 proximity**, all 173 on the footprint
   ring (`173/173`) with no interzone partner (`0/173`). The remedy in `D-EU-109 a` — remove the redundant
   near-collinear ring vertex — therefore addresses the entire undivided residual, and no proximity-side
   remedy is in scope.
2. **The executor's post-reroute caveat is accepted and does not weaken §2.** T01 probed the *emitted*
   ceiling82 IDFs, i.e. geometry the reroute has already flattened, so its `173 / 1,524` is necessarily a
   remnant and is not comparable with §2's `1,045 / 1,514 (69.0 %)`, which the director measured on the
   JSON footprint ring *before* any emission. The two are different populations, not a contradiction. The
   consequence for T02/T03 is that the **pre-cut** half of `D-EU-109 b` is the load-bearing half; the
   post-cut cleanup remains required but is the smaller of the two.

T02 is released.

- **`CP-2` — after T02.** The unit-test results and the in-memory `at_risk` recovery count. Director signs
  before anything is re-emitted.
**`CP-2` HELD — director, 2026-09-07.** The T02 code is accepted: `_drop_redundant_ring_vertices` is
correct, the two call sites are where §6 T02 puts them (`openubem/geometry/european_residential.py:1350-1355`
before `cut_storey_nocore`; `scripts/run_eu_s2_campaign.py:608-611` before `extrude_geometry`), and
`tests/test_eu_collinear_ring_cleanup.py` passes 8/8 with all six required cases. The executor's deviation
note is accepted in full: `_symmetrize_near_duplicate_interzone_vertices` does not exist in the working tree
or in git history — §6 T02's instruction to leave it unwired was written from the predecessor's DEBUG doc and
had no referent. No action.

**What is held is the plan's own hard rule 5, not the executor's work.** In-memory recovery is **8 of 173**
(4.6 %) undivided, **18 of 653** fleet-wide. The executor's diagnosis is that the `1e-6` relative-area budget
honestly refuses genuine ~179.99° vertices on ~11 m edges, and the director's own arithmetic agrees: removing
a vertex with adjacent edges *a*, *b* at interior angle θ changes area by `0.5·a·b·sin(180° − θ)`, so at
`a = b = 11 m` and θ = 179.99° that is `0.0106 m²`, and on a 200 m² footprint the relative change is
`5.3e-5` — **fifty times** the budget. At the detector's own flagging threshold, θ = 179.9°, it is `5.3e-4`,
five hundred times. `1e-6` therefore cannot admit the vertices this plan exists to remove; the rule and the
remedy are mutually exclusive as written, and the rule is the director's, so the rule is what gets examined.

**A relative-area budget is also the wrong criterion.** It scales with footprint size, so the same physical
1 cm wall kink is admitted on a large building and refused on a small one. The geometrically meaningful
bound is the vertex's **perpendicular distance to the chord** joining its two neighbours — the actual
displacement of the wall. `T02b` below measures both distributions before any constant is chosen; the
director picks the criterion from that measurement, never from an estimate, and `1e-6` stays in force until
it is formally superseded here.

### T02b — Vertex budget measurement (no behaviour change)

**What:** the distribution the choice of criterion has to be made from. **How:** for every vertex
`_has_near_duplicate_vertex_surfaces` flags on the footprint ring, over CP-1's frozen 173 undivided set and
over the full 653 defect-carrying set separately, record interior angle, both adjacent edge lengths,
perpendicular distance to the chord, absolute and relative area change if removed, and whether `1e-6` admits
it → `vertex_budget_2026-09-07.csv`. **How to test:** report min/median/p90/p95/max for each; counts admitted
at relative budgets `1e-6 … 1e-2`; counts admitted at chord distances `0.005 / 0.01 / 0.02 / 0.05 m`; and,
per building, how many of the 173 would have **every** flagged ring vertex removable at each threshold —
that last figure is the operative one, since a single surviving vertex still trips `at_risk`. Change no
constant, re-emit nothing.

**`CP-2` SIGNED — director, 2026-09-07, with hard rule 5 amended below.** T02b delivered
`vertex_budget_2026-09-07.csv` (3,978 rows: 391 for the 173 undivided, 3,587 for the 653 defect-carrying),
and its `8/173` at the `1e-6` budget reproduces T02's independent in-memory figure exactly, so the two
measurements corroborate.

**`D-EU-109 f` — the removal criterion, chosen from the measurement.** A flagged ring vertex is removed
**iff both** hold:

1. its **perpendicular distance to the chord** joining its two neighbours is `<= 0.010 m`, and
2. the **relative ring-area change** of that single removal is `<= 1e-3`,

and the **cumulative** relative ring-area change across all removals on one ring, over the whole fixed-point
iteration, is `<= 2e-3`. A removal that would breach the cumulative cap is refused and the ring is returned
as it stands — the honest-refusal behaviour T02 already implements, with a new bound.

Why each number, from T02b's own distributions over the 173 undivided:

- **Perpendicular distance is the criterion; relative area is only a guard.** Relative area scales with
  footprint, so the same 1 cm wall kink is admitted on a large building and refused on a small one — the
  defect this plan removes is a property of the *wall*, not of the *plan area*. `0.010 m` yields **171 of
  173** buildings with every flagged ring vertex removable, against **149** at `0.005 m` and **172** at
  `0.020 m`: the entire usable recovery sits between 5 mm and 1 cm, and nothing is bought past it. One
  centimetre of wall displacement is below any dimension this model resolves.
- **The area guard exists for the degenerate rings, and only for them.** Over the 653-building set the
  flagged-vertex relative area change reaches `p90 = 0.305` and `max = 1.000` — slivers where removing one
  vertex annihilates the ring (minimum interior angle `2.2°`). A pure distance criterion would admit those.
  `1e-3` per removal does not bind on a single real footprint in the 173 set (its measured maximum is
  `9.77e-4`) and refuses every degenerate case outright.
- **The cumulative cap is `2e-3` because the measured worst case is `1.13e-3`.** At the chosen `0.010 m`,
  per-building cumulative relative area change is median `5.6e-5`, p95 `4.1e-4`, max `1.13e-3`. `2e-3` is
  1.8x the observed worst case: headroom for an unseen ring, no room for a bug.

**`NEAR_DUPLICATE_VERTEX_TOLERANCE_M` (0.005) and `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (0.1) are NOT
touched and remain frozen.** They decide what the detector *flags*; `D-EU-109 f` decides what the cleanup is
allowed to *remove*. Widening either remains forbidden and no task in this plan may do it.

**Hard rule 5 is amended, and this supersedes the `1e-6` figure everywhere in this document.** The old rule
required relative area preserved to `1e-6` per removal. Director's arithmetic and T02b agree that `1e-6`
cannot admit the vertices this plan exists to remove — at the detector's own `179.9°` flagging threshold on
11 m edges the change is `5.3e-4`, five hundred times the old budget — so the rule was self-defeating as
written. It is replaced by `D-EU-109 f` above.

**T03's area-conservation gate changes with it:** `abs(area_delta_pct) <= 0.2 %` for every building, the same
number as the cumulative cap, so a violation is only possible through a coding defect. T03 additionally
reports the **distribution** of `area_delta_pct` (median, p95, max) and, separately, the same distribution for
the **EUI denominator** (`conditioned_floor_area_m2`), because that denominator moving is the one way this
change can perturb a published EUI for a reason unrelated to the recovered dwellings. T07 states that
distribution alongside the restated EUIs.

**Expected outcome, for T03 to test against, not to reproduce by construction:** 171 of the 173 undivided
buildings carrying a residual ring defect become fully clean. The 2 that do not have a flagged vertex beyond
`0.010 m` and stay undivided honestly; name them.

T03 is released.



- **`CP-3` — after T03/T04.** The three re-emission gates plus 0 EnergyPlus fatals. Director signs before
  anything reaches Speed.
- **`CP-4` — after T07.** The EUI restatement, director-run, reported to the owner.

---

## 8. Progress log

*(executor appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` +
Artifacts / Deviations / Test status / Notes.)*

#### T01 — Freeze the undivided set and confirm the mechanism on the emitted IDFs — completed 2026-09-07

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/division_recovery/undivided_census_2026-09-07.csv` — 3,344 rows (1 per
  simulated building, all four districts), columns exactly as specified.
- `openubem/outputs/eu_evidence/EU-21/division_recovery/defect_probe_2026-09-07.csv` — 3,344 rows, columns
  exactly as specified.

**Method:** one Python driver (scratchpad, not committed) joined `<DISTRICT>_ceiling82_2026-09-05/*_manifest.csv`
(`geometry_outcome`), `prepared_buildings.csv` (`building_id -> stem`) and `EU-21/district_plans/*_r5.json`
`plates[]` (`k, drawn_per_floor, status, spread, verdict, storeys, area_m2`) by `building_id` — 0 of 3,344
missing a census join. For `defect_probe`, imported `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` (`run_eu_s2_campaign.py:77`)
and `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (`:91`) read-only from `scripts/run_eu_s2_campaign.py`; loaded each
building's emitted `EU-11/<DISTRICT>_ceiling82_2026-09-05/idfs/<stem>.idf` with `geomeppy.IDF` (same IDD as
`run_eu_s2_campaign.py:505-510`) and applied the two sub-conditions of `_has_near_duplicate_vertex_surfaces`
(`:94-141`) per vertex, per `BUILDINGSURFACE:DETAILED` surface, `interzone_only=False` (scanned all surfaces,
not just paired ones, since `has_interzone_partner` is an output column here). Ran as a local `multiprocessing.Pool`,
20 workers, over all 3,344 IDFs — full run in well under a minute after IDD warm-up.

**Test status — §1 tables reproduced exactly, no cell differs:**
- Undivided: ES 642, FR 173, GB 49, IT 660, fleet 1,524 — matches.
- Recoverable: ES 476, FR 103, GB 33, IT 555, fleet 1,167 — matches.
- `geometry_outcome` of the 1,524: `..._INTERZONE_MISMATCH_REROUTED` 1,239, `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`
  213, `FALLBACK_PENDING_LAYOUT` 72 — matches. `has_whole_zone=Y` set (1,524) is byte-identical to the
  `geometry_outcome`-defined undivided set (0 mismatches).

**`defect_probe` findings, fleet-wide, measured on the emitted (post-reroute) IDFs:**
- `first_defect_kind` over the 653 buildings fleet-wide carrying any defect: 590 collinear (90.3 %), 63
  proximity (9.7 %) — not the predecessor's ~100 % collinear 16-building sample; the proximity sub-check is a
  real, non-trivial minority at fleet scale.
- 2×2 contingency of `n_defective_surfaces>0` vs undivided/divided: undivided+defect 173, undivided+no-defect
  1,351, divided+defect 480, divided+no-defect 1,340 (totals 1,524 / 1,820 / 3,344, all consistent).
- All 173 undivided buildings with a residual defect have it on the footprint ring (`defect_on_footprint_ring=Y`,
  173/173) and none of those 173 have an interzone partner (`has_interzone_partner=N`, 173/173).

**Deviations:** none from the plan's column spec. One interpretive note for the director going into T02/T03:
this probe runs on the **final, post-reroute** emitted IDF, per the task's literal instruction ("the building's
emitted ceiling82 IDF surfaces"). For the 1,524 undivided buildings, rerouting already deleted the interzone-paired
dwelling-cut surfaces that originally tripped `at_risk` pre-reroute (`run_eu_s2_campaign.py:561-571`), so the 173
residual defects found here are a **different, smaller** population than the pre-reroute defect that caused the
reroute in the first place — consistent with, not contradicting, §2's separate census-footprint-ring measurement
(1,045/1,514, 69 %), which was computed from the JSON footprint ring directly, not from emitted-IDF surfaces.

**Notes:** no code file touched (read-only task, hard rule honoured). CP-1 report sent to director separately.

#### T02 — The ring cleanup — completed 2026-09-07

**Artifacts:**
- `scripts/run_eu_s2_campaign.py:144-217` — new `_drop_redundant_ring_vertices(ring)`, immediately after
  `_has_near_duplicate_vertex_surfaces`. Reads `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` (`:77`) and
  `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (`:91`) unchanged, no second copy. Iterates to a fixed point
  (capped at the ring's own starting vertex count), refuses to drop below 3 vertices, refuses any single
  removal whose relative area change exceeds `1e-6` (area via Newell's formula, dimension-agnostic so the
  same function works on both the 2D `coords_m` rings and the 3D IDF `BUILDINGSURFACE:DETAILED` rings without
  a second implementation). Handles both open and closed (first==last) ring input, preserving whichever
  convention it was given.
- Call site 1 (`D-EU-109 b`, pre-cut): `openubem/geometry/european_residential.py:1350-1355`, entry to
  `generate_european_nocore_storey_layout`. Cleans `footprint.exterior.coords`, rebuilds the `Polygon` with
  interiors preserved, before `cut_storey_nocore(footprint, dwelling_count)` (`:1358`). Import is inside the
  function (lazy) to avoid a module-load cycle: `scripts/run_eu_s2_campaign.py` already imports from
  `openubem.geometry.european_residential` at its own top level (`:36-40`).
- Call site 2 (`D-EU-109 b`, post-cut): `scripts/run_eu_s2_campaign.py:608-611`, in `build_idf_for_building`.
  Cleans every zone's `coords_m` in place, immediately before `extrude_geometry(idf, zones, context or [])`
  (`:612`) — upstream of `find_mismatched_interzone_pairs` (now `:643`, was `:561` pre-edit) and outside the
  `at_risk` branch, per plan.
- `tests/test_eu_collinear_ring_cleanup.py` — 8 tests: the 6 required cases plus a closed-ring
  closure-preservation case and a frozen-tolerance-value guard.
- `undivided/at_risk` in-memory recovery measurement (scratchpad, not committed): loaded each of the 653
  `defect_probe`-defective buildings' emitted `EU-11/<DISTRICT>_ceiling82_2026-09-05/idfs/<stem>.idf` (same IDD
  as `:505-510`), cleaned every `BUILDINGSURFACE:DETAILED` surface's own ring via `surf.setcoords(...)`, then
  re-ran `_has_near_duplicate_vertex_surfaces(idf, interzone_only=False)` (T01's own setting) before/after.

**Test status:**
- `pytest tests/test_eu_collinear_ring_cleanup.py -q` — 8 passed, 0 failed.
- `pytest tests/test_eu_s2_campaign.py tests/test_eu_s2_campaign_ceiling82.py -q` (regression check on both
  touched call sites' existing coverage) — 59 passed, 0 failed.
- In-memory `at_risk` recovery over the 653 `defect_probe`-defective buildings, fleet-wide: **18 of 653 (2.8 %)
  stop being `at_risk`**, 635 still trip it, split ES 4 / FR 10 / IT 4 / GB 0 recovered. Restricted to CP-1's
  load-bearing **173 undivided** buildings: **8 of 173 (4.6 %) recover** (ES 1, FR 5, IT 2, GB 0), **165 still
  at_risk** (ES 60, FR 9, IT 93, GB 3). Spot-checked one still-at-risk case (`relation/3730743`, `stem
  b56bda9013da5b2d`, ES): every one of its 10 defective surfaces carries a genuine 179.99° vertex on an
  ~11.4 m edge whose removal is **honestly refused** by the `1e-6` relative-area budget (hard rule 5), not a
  cleanup-function defect — the low recovery number reflects the budget doing its job on already-emitted,
  post-no-core-cut, post-regularization geometry, not a bug.

**Deviations:**
- The plan (`D-EU-109 b`, T02 "How to test") instructs re-running the detector "over T01's `defect_probe`
  population with the cleanup applied in memory." This was read as: apply `_drop_redundant_ring_vertices` to
  each surface's own ring on the same emitted IDFs T01 probed (a post-hoc proxy on already-cut, already-extruded
  geometry), not as a re-run of the actual T02 pipeline (which only fires pre-cut and pre-extrusion, on inputs
  that no longer exist once an IDF is already emitted). This is necessarily a lower-bound proxy, consistent with
  CP-1 director finding 2 (T01 probes post-reroute, post-cut geometry); the real recovery number is T03's, from
  actual re-emission through the two wired call sites.
- The plan's hard rules and `D-EU-109 b` reference `_symmetrize_near_duplicate_interzone_vertices` as a function
  "written and never validated by the predecessor's T03," instructing it be left unwired and undeleted. A repo
  search (`git log --all -S` and a full-tree grep) found no `.py` file, in the working tree or in any commit,
  ever defining that name — only docs reference it. Nothing was touched under this instruction since there is
  no such function to touch; flagged here rather than silently ignored, since the plan's premise about it
  differs from the codebase's actual state.

**Notes:** `openubem/idf/surfaces.py` not edited (D-EU-41 honoured). `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` and
`COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` not re-typed, not widened. No code comments added (docstrings only,
matching existing file style). No emission, simulation, or cluster submission performed. Files touched: exactly
the three named in dispatch (`scripts/run_eu_s2_campaign.py`, `openubem/geometry/european_residential.py`,
`tests/test_eu_collinear_ring_cleanup.py`); the recovery-measurement script and its output stayed in the
session scratchpad, not committed, matching T01's own pattern.

#### T02b — Vertex budget measurement (director follow-up, before T03) — completed 2026-09-07

**Scope note:** measurement only, no behaviour change. `_drop_redundant_ring_vertices` untouched;
`scripts/eu21/07_nocore_tests.py` and `openubem/geometry/european_nocore.py` not opened, not touched
(concurrent-executor exclusion honoured). No threshold chosen.

**Method:** "the footprint ring" is operationalised as every `BUILDINGSURFACE:DETAILED` surface whose `Name`
contains `"Storey 0"`, `Surface_Type == "Floor"` (ground-contact, case-insensitive), and
`Outside_Boundary_Condition != "Surface"` (partner-less, so `Ground` for these buildings) — one such surface
per zone at grade, so an undivided (`_whole`) building has exactly one, a divided building has one per
ground-floor dwelling/circulation zone. This deliberately excludes the Roof and interzone storey-to-storey
Floor/Ceiling surfaces that repeat the identical ring at every storey (confirmed identical-defect duplication
in T02's spot check) — including those would inflate vertex counts by storey count without adding information,
since `_drop_redundant_ring_vertices` at call site 1 only ever sees the ring once, pre-extrusion. Same emitted
IDFs as T01/T02 (no re-emission); same per-vertex proximity/collinear test as
`_has_near_duplicate_vertex_surfaces`, `interzone_only` moot here since these surfaces are partner-less by
construction. Per removed vertex: `abs_area_change_m2` is the exact shoelace/Newell triangle area of
`(p0, p1, p2)` (mathematically identical to a full-ring before/after recompute for a single-vertex removal);
`perp_dist_to_chord_m = 2 * abs_area_change_m2 / |p2 - p0|`.

**Artifact:** `openubem/outputs/eu_evidence/EU-21/division_recovery/vertex_budget_2026-09-07.csv`, 3,978 rows
(391 for the 173-set, 3,587 for the 653-set — every population-173 building recurs inside population-653;
rows are not deduplicated across the two `population` values, by design, since the two questions are asked
separately), columns: `building_id, district, population, surface_name, vertex_index, defect_kind,
interior_angle_deg, edge1_m, edge2_m, perp_dist_to_chord_m, abs_area_change_m2, ring_area_m2,
relative_area_change, admitted_1e6`.

**Distributions (min / median / p90 / p95 / max):**

173-undivided set (391 flagged vertices, all 173 buildings carry >=1):
1. `interior_angle_deg`: 179.900 / 179.969 / 180.000 / 180.000 / 180.000
2. `perp_dist_to_chord_m`: 0 / 0.001308 / 0.004361 / 0.005846 / 0.022494
3. `abs_area_change_m2`: 0 / 0.007850 / 0.055234 / 0.080325 / 0.871425
4. `relative_area_change`: 0 / 1.3549e-05 / 1.0757e-04 / 1.7666e-04 / 9.7716e-04

653-all-defective set (3,587 flagged vertices, all 653 buildings carry >=1):
1. `interior_angle_deg`: 2.214 / 179.943 / 179.997 / 180.000 / 180.000
2. `perp_dist_to_chord_m`: 0 / 0.000421 / 0.002763 / 0.004456 / 0.022494
3. `abs_area_change_m2`: 0 / 0.000835 / 0.012269 / 0.024232 / 0.871425
4. `relative_area_change`: 0 / 9.6665e-06 / 0.305244 / 1.000000 / 1.000000

**5. Vertices admitted by the relative-area criterion, by budget:**
173-set (of 391): 1e-6 -> 67; 1e-5 -> 172; 1e-4 -> 346; 1e-3 -> 391; 1e-2 -> 391.
653-set (of 3,587): 1e-6 -> 795; 1e-5 -> 1,812; 1e-4 -> 2,918; 1e-3 -> 3,212; 1e-2 -> 3,214.

**6. Vertices admitted by the perpendicular-distance criterion, by X:**
173-set (of 391): 0.005 m -> 364; 0.01 m -> 389; 0.02 m -> 390; 0.05 m -> 391.
653-set (of 3,587): 0.005 m -> 3,525; 0.01 m -> 3,582; 0.02 m -> 3,586; 0.05 m -> 3,587.

**7. Per building (173-undivided set only), buildings with EVERY flagged footprint-ring vertex removable:**
- Relative-area criterion, of 173: 1e-6 -> 8; 1e-5 -> 35; 1e-4 -> 133; 1e-3 -> 173; 1e-2 -> 173.
- Perpendicular-distance criterion, of 173: 0.005 m -> 149; 0.01 m -> 171; 0.02 m -> 172; 0.05 m -> 173.
- Cross-check: the current frozen `1e-6` figure (8/173) matches T02's independent in-memory `at_risk`
  recovery measurement (8/173 recovered) exactly — same 8 buildings would be expected, not re-verified by
  building_id here to stay inside the "measurement only" scope.

**Notes:** the 653-set's `relative_area_change` p95/max of 1.0 comes from small divided-building dwelling/
circulation zone floors, where a flagged vertex's triangle can be a large fraction of that zone's own tiny
ring area — flagged as data, not investigated further (out of T02b's scope). No threshold recommendation
made; director to choose and amend the plan. `scripts/eu21/07_nocore_tests.py`,
`openubem/geometry/european_nocore.py` not touched. Measurement script stayed in the session scratchpad, not
committed.

#### T03m (FR+GB slice) — completed 2026-09-07

**Scope:** the two districts whose merged re-emission was already `PREPARED_FOR_SPEED` —
`FR-LYO-HAUTCOEURPENTES_final_2026-09-07/` (509 prepared) and `GB-LDN-STDUNSTANS_final_2026-09-07/` (706
prepared). `ES-MAD-BERRUGUETE` and `IT-BOL-GALVANI2` untouched (still emitting, owned by another executor).
`*_ceiling82_2026-09-05/` trees read-only throughout.

**1. Seven-check + C12 gate battery — BLOCKED, not run.** T03m's own text (this doc, lines 329-386) never
lists a "C1, C3, C4, C5, C6, C10, C11, C12-spread" battery to run over already-emitted final trees; it names
`C12` only once, as the D-EU-107 recovery gate "used as-is, not re-derived here." The seven checks
(`C1, C3, C4, C5, C6, C10, C11`) are real (`openubem/geometry/european_nocore.py` `run_checks`, invoked
in-process from `openubem/geometry/european_residential.py:1377` during `cut_storey_nocore`) but are
evaluated live during emission and never persisted — confirmed empirically: `fr_lyo_hautcoeurpentes_manifest.csv`
carries only `geometry_outcome` (three values: `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`,
`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`, `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`), no
per-check breakdown, no `NOCORE_CHECK_FAILED_*` tokens anywhere in either final tree. Re-deriving the battery
would require recomputing geometry from source footprints, which T03m does not specify (tolerance, footprint
source, expected thresholds all unstated). Stopped per "do not invent" rather than fabricate a verdict.
Director to either point to the artifact holding these results or descope this line.

**2. Hash control (`FINDING 263`-excluded), keyed on `building_id` via each tree's `prepared_buildings.csv`
`idf_sha256`, reference = `*_ceiling82_2026-09-05/`:**
- FR-LYO: unchanged 246, changed 88, net-new 1 (classification set; see note below), excluded-nondeterministic
  174 (all `*_INTERZONE_MISMATCH_REROUTED`, matching the district's high reroute share pre-fix).
- GB-LDN: unchanged 368, changed 44, net-new 254, excluded-nondeterministic 40 (33 `*_INTERZONE_MISMATCH_REROUTED`
  + `near_duplicate_vertex_tolerated_box`, all on the ceiling82 side; 7 on the final side).
- Exclusion population named per `FINDING 263`: `geometry_outcome` ending `*_INTERZONE_MISMATCH_REROUTED`, or
  `fallback_reason == near_duplicate_vertex_tolerated_box`.
- **Note:** the true (unfiltered) net-new count — `building_id` present in `final` absent from `ceiling82` —
  is FR 3, GB 255. GB's 255 matches T03m gate 7's stated figure exactly. The 1-count gaps (FR: 1 vs 3; GB:
  254 vs 255) are net-new buildings that are *also* `FINDING 263`-excluded (their hash comparison is invalid,
  but they still need simulating since they have no `before` counterpart at all) — reported under
  excluded-nondeterministic above per the hash-gate's own exclusion rule, but folded into the true net-new
  count used for the simulate list (task 3). FR also lost 1 building relative to ceiling82
  (`BATIMENT0000000240880120_part0`, was `near_duplicate_vertex_tolerated_box`, absent from final) — observed,
  not investigated further (out of this task's scope).

**3. Simulate lists** (rows = hash-changed + true net-new; reason `HASH_CHANGED` / `NET_NEW`):
- `openubem/outputs/eu_evidence/EU-11/simulate_list_FR_2026-09-07.csv` — 91 rows (88 `HASH_CHANGED`, 3 `NET_NEW`).
- `openubem/outputs/eu_evidence/EU-11/simulate_list_GB_2026-09-07.csv` — 299 rows (44 `HASH_CHANGED`,
  255 `NET_NEW`).
- Per director amendment 2026-09-07: split FR/GB (not the combined `simulate_list_FRGB_2026-09-07.csv`
  originally specified), FR staged first.

**4. Reroute before/after tables**, schema per T03's definition (`building_id, district, outcome_before,
outcome_after, whole_before, whole_after, n_zones_before, n_zones_after, dwellings_after, floor_area_before,
floor_area_after, area_delta_pct`), `n_zones`/`dwellings_after` parsed from each tree's IDF `ZONE,` objects
(text parse only, no EnergyPlus):
- `openubem/outputs/eu_evidence/EU-11/reroute_before_after_FR_2026-09-07.csv` — 510 rows.
- `openubem/outputs/eu_evidence/EU-11/reroute_before_after_GB_2026-09-07.csv` — 706 rows.

**5. Speed staging (stage only, not submitted) — FR first per director amendment:**
- FR: remote `/speed-scratch/o_iseri/fleets/EU11_FR-LYO-HAUTCOEURPENTES_final_2026-09-07/`, tar
  `eu11_fr_final_2026-09-07.tar.gz` (91 IDFs + FR EPW + `fleet.lst` + sbatch), extracted and verified
  (91 IDFs = 91 `fleet.lst` lines = 91 simulate-list rows). Sbatch:
  `submit_fleet_t08_frgb_2026-09-07.sbatch` (based on `scripts/cluster/submit_fleet_t08.sbatch`, `--time` line
  stripped). Command for the director to run:
  `sbatch --array=1-91%32 --time=7-00:00:00 -p ps --export=FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_FR-LYO-HAUTCOEURPENTES_final_2026-09-07 /speed-scratch/o_iseri/fleets/EU11_FR-LYO-HAUTCOEURPENTES_final_2026-09-07/submit_fleet_t08_frgb_2026-09-07.sbatch`
- GB: remote `/speed-scratch/o_iseri/fleets/EU11_GB-LDN-STDUNSTANS_final_2026-09-07/`, tar
  `eu11_gb_final_2026-09-07.tar.gz` (299 IDFs + GB EPW + `fleet.lst` + sbatch), extracted and verified
  (299 IDFs = 299 `fleet.lst` lines = 299 simulate-list rows). Same sbatch template. Command:
  `sbatch --array=1-299%32 --time=7-00:00:00 -p ps --export=FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_GB-LDN-STDUNSTANS_final_2026-09-07 /speed-scratch/o_iseri/fleets/EU11_GB-LDN-STDUNSTANS_final_2026-09-07/submit_fleet_t08_frgb_2026-09-07.sbatch`
- Neither array submitted. No compute run on the login node (`mkdir`/`scp`/`tar` only, via bare `ssh` since
  every command used was a single quoted `bash -lc '...'` string, tcsh-safe).

**Artifacts:** the four CSVs above (`openubem/outputs/eu_evidence/EU-11/`); two tarballs + sbatch files on
Speed (paths above); no local scratch script committed (stayed in session scratchpad).
**Deviations:** task 1 (gate battery) not run — ambiguous, see above, director input needed. Task 3/5 split
FR/GB per director's mid-task amendment (originally one combined `simulate_list_FRGB` file/payload).
**Test status:** no EnergyPlus run (none specified for this task); all CSV row counts cross-checked against
independent `prepared_buildings.csv` totals (see note in §2).
**Notes:** no new symptom/error to register in `OpenUBEM_debug_References.md` — task 1's blocker is a spec
gap, not a solved error.

#### T03m (ES slice) — completed 2026-09-07

**Scope:** `ES-MAD-BERRUGUETE_final_2026-09-07/` only (1,175 IDFs, `status: PREPARED_FOR_SPEED`,
`population_attempted` 1,194, blockers 19). `*_ceiling82_2026-09-05/` tree read-only throughout.

**1. Emission complete:** `idfs/` 1,175 `.idf` files; `summary.json` present (`status: PREPARED_FOR_SPEED`);
`es_mad_berruguete_manifest.csv` 1,175 data rows; `prepared_buildings.csv` 1,175 data rows. Counts agree.

**2. Hash control (`FINDING 263`-excluded), keyed on `building_id` via each tree's `prepared_buildings.csv`
`idf_sha256`, reference = `ES-MAD-BERRUGUETE_ceiling82_2026-09-05/` (1,174 prepared):**
- unchanged 217, changed 268, net-new 4 (true net-new 6 — 2 of the 6 are also `FINDING 263`-excluded on the
  final side, dup-only, folded into excluded-nondeterministic below per the FR/GB convention but still
  simulated as `NET_NEW` since they have no `before` counterpart at all).
- excluded-nondeterministic 686 (684 in the common set — 566 reroute-only, 114 near-duplicate-only, 4 both,
  604 ceiling82-side-only/2 final-side-only/78 both-sides — plus the 2 net-new-excluded above).
- Exclusion named per `FINDING 263`: `geometry_outcome` ending `*_INTERZONE_MISMATCH_REROUTED`, or
  `fallback_reason == near_duplicate_vertex_tolerated_box`.
- Aside, out of scope: 5 buildings present in ceiling82 absent from final (lost), not investigated further,
  same pattern as FR's 1-building loss noted in the FR+GB entry.

**3. Simulate list:** `openubem/outputs/eu_evidence/EU-11/simulate_list_ES_2026-09-07.csv` — 274 rows
(268 `HASH_CHANGED`, 6 `NET_NEW`).

**4. Reroute before/after table**, schema per T03's definition, `n_zones`/`dwellings_after` parsed from each
tree's IDF `ZONE,` objects and `_dwelling_<n>` zone-name tokens (text parse only, no EnergyPlus); `whole_before`/
`whole_after` derived from `geometry_outcome` (`Y` iff it contains `FALLBACK_PENDING_LAYOUT`, `NA` iff
`NOT_PRESENT`, else `N` — confirmed against the FR reroute CSV's own before/after outcome↔`whole` mapping,
since REROUTED buildings are zone-named `_whole` yet reported `whole=N` there):
`openubem/outputs/eu_evidence/EU-11/reroute_before_after_ES_2026-09-07.csv` — 1,180 rows (1,169 common +
6 net-new, `outcome_before=NOT_PRESENT` + 5 lost, `outcome_after=NOT_PRESENT`).

**5. Speed staging (stage only, not submitted).** Coordinator correction received mid-task: the FR staging
this task was told to mirror had shipped `idfs/`+`weather/`+`fleet.lst` only, omitting `schedules/<stem>/`,
and failed 91/91 instantly (`Schedule:File=... not found` → `Fatal ProcessScheduleInput`), registered at
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (European locations, ceiling82 (2026-09-05) chapter,
first entry) and since corrected on the live FR fleet dir (verified: FR's remote `schedules/` now holds 91
dirs, matching its `fleet.lst`). ES staged with all four required pieces from the outset:
- Remote `/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_final_2026-09-07/`, tar
  `eu11_es_final_2026-09-07.tar.gz` (274 IDFs + ES EPW `es_madrid_2009_2010_y2010.epw` + `schedules/<stem>/`
  for all 274 simulate-list stems + `fleet.lst` + sbatch), extracted and verified on Speed: 274 IDFs =
  274 `schedules/` dirs = 274 `fleet.lst` lines = 274 simulate-list rows; empty `out/` created separately.
  Sbatch: `submit_fleet_t08_frgb_2026-09-07.sbatch`, copied byte-for-byte from the FR fleet dir on Speed
  (not re-authored), no `--time` baked in (confirmed, `grep -c "time="` on the copy = 0).
- Spot-checked one staged IDF's `SCHEDULE:FILE` object on Speed: `File Name` =
  `../../schedules/c618dfeb21e06f07/c618dfeb21e06f07_F0_dwelling_0_f000_gain.csv` — relative form, not an
  absolute Windows path (the third registered root cause at the same symptom).
- Not submitted. No compute run on the login node (`mkdir`/`scp`/`tar`/`ls` only, every remote command a
  single quoted `bash -lc '...'` string, tcsh-safe). Command for the director to run:
  `sbatch --array=1-274%32 --time=7-00:00:00 -p ps --export=FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_final_2026-09-07 /speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_final_2026-09-07/submit_fleet_t08_frgb_2026-09-07.sbatch`

**Artifacts:** two CSVs above (`openubem/outputs/eu_evidence/EU-11/`); one tarball + sbatch file on Speed
(path above); no local scratch script committed (stayed in session scratchpad).
**Deviations:** none from the amended (schedules-inclusive) spec; task 1 (gate battery) out of this slice's
scope, already dispositioned as blocked in the FR+GB entry above.
**Test status:** no EnergyPlus run (none specified); all CSV row counts cross-checked against independent
`prepared_buildings.csv` totals; Speed-side counts (idfs/schedules/fleet.lst) cross-checked against each
other and against the simulate list.
**Notes:** no new symptom/error — the schedules-omission failure mode was already registered before this
task started (coordinator correction cited it); this entry adds no new debug-reference bullet, only avoids
repeating the defect.

#### T03m (IT slice) — completed 2026-09-07

**Scope:** `IT-BOL-GALVANI2_final_2026-09-07/` only (1,216 IDFs, `status: PREPARED_FOR_SPEED`,
`population_attempted` 1,220, `population_prepared` 1,211, blocker exclusions `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS`
4 + `IDF_ASSEMBLY_FAILED_RuntimeError` 5). `*_ceiling82_2026-09-05/` tree read-only throughout.

**1. Eight-check gate battery — resolved offline, no live fetch, director-directed re-derivation.**
`gates_fr.py`'s row source (`_mapped_rows`/`_it_rows`, archetype/age-band mapping) turned out unnecessary:
`cut_storey_nocore`'s eight checks need only the footprint polygon and per-floor dwelling count `k`, neither
of which comes from `_it_rows`'s two live `requests.get()` calls to `opendata.comune.bologna.it`
(`scripts/run_eu_s2_district_campaign.py:459-461,480-482`, no local cache). Re-sourced both offline:
footprint = `openubem/outputs/eu02/IT-BOL-GALVANI2/02_residential_manifest.gpkg`, joined `osm_id` ==
`building_id` (same manifest `_mapped_rows` itself reads, 1,220 rows, no fetch); `k` per floor = distinct
`dwelling_<idx>` tokens per `_F<n>_` prefix, parsed from
`IT-BOL-GALVANI2_final_2026-09-07/schedules/<stem>/` filenames (regex `_F(\d+)_dwelling_(\d+)_`), fed
straight into `cut_storey_nocore` as `gates_fr.py` does. **buildings_total 1,211, plates_total 1,754,
buildings_missing_row 0, buildings_skipped_density_gt_12 0, cutter_errors 0.** Checks:
`C1` 1754/0, `C3` 1754/0, `C4` 1754/0, `C5` 1754/0, `C6` 1754/0, `C10` 1754/0, `C11` 1754/0 (all pass),
`C12` 1698 pass / 56 fail (spread gate, same class of failure as FR/ES). Sanity check against
`affected_buildings_2026-09-07.csv`'s IT rows (k, area_m2): 905 comparable, 695 matched exactly; the ~210
non-matches are buildings whose `geometry_outcome` is `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` (no
dwelling division ever emitted, so no `dwelling_N` tokens exist to recover — the CSV's `k` there is the
originally-*intended* target, not an achieved cut), verified on one example (`building_id 29816`) —
area matched exactly (1304.04→1304 both sides) while `k` had nothing to compare, not a script defect.

**2. Hash control (`FINDING 263`-excluded), keyed on `building_id` via each tree's `prepared_buildings.csv`
`idf_sha256`, reference = `IT-BOL-GALVANI2_ceiling82_2026-09-05/` (1,212 prepared):**
- unchanged 241, changed 231, net-new 4 (true net-new 4 — 1 of the 4 is also `FINDING 263`-excluded on the
  final side, dup-only, folded into excluded-nondeterministic below per the FR/GB/ES convention but still
  simulated as `NET_NEW` since it has no `before` counterpart at all).
- excluded-nondeterministic 735 (common set, either side flagged): `ceil`-side 488
  `*_INTERZONE_MISMATCH_REROUTED` + 95 `near_duplicate_vertex_tolerated_box` (as `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`)
  + 134 `near_duplicate_vertex_tolerated_box` (as `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`); `final`-side 85
  `*_INTERZONE_MISMATCH_REROUTED` + 19 `near_duplicate_vertex_tolerated_box`.
- Exclusion named per `FINDING 263`: `geometry_outcome` ending `*_INTERZONE_MISMATCH_REROUTED`, or
  `fallback_reason == near_duplicate_vertex_tolerated_box`.
- Aside, out of scope: 5 buildings present in ceiling82 absent from final (lost:
  `29376, 29695, 30646, 30810, 32473`), not investigated further, same pattern as FR/ES's building loss.

**3. Simulate list:** `openubem/outputs/eu_evidence/EU-11/simulate_list_IT_2026-09-07.csv` — 235 rows
(231 `HASH_CHANGED`, 4 `NET_NEW`).

**4. Reroute before/after table**, schema and derivation identical to the ES entry (§4 above), text-parse
of IDF `ZONE,` objects and `_dwelling_<n>` tokens, no EnergyPlus:
`openubem/outputs/eu_evidence/EU-11/reroute_before_after_IT_2026-09-07.csv` — 1,216 rows (1,212 common +
4 net-new, `outcome_before=NOT_PRESENT`; 5 lost, `outcome_after=NOT_PRESENT`).

**5. Speed staging (stage only, not submitted), all four required pieces from the outset:**
- Remote `/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2_final_2026-09-07/`, tar
  `eu11_it_final_2026-09-07.tar.gz` (235 IDFs + IT EPW `it_bologna_2013_2014_y2014.epw` + `schedules/<stem>/`
  for all 235 simulate-list stems + `fleet.lst` + sbatch), extracted and verified on Speed: 235 IDFs =
  235 `schedules/` dirs = 235 `fleet.lst` lines = 235 simulate-list rows; empty `out/` created separately.
  Sbatch: `submit_fleet_t08_frgb_2026-09-07.sbatch`, copied byte-for-byte from the ES fleet dir on Speed
  (not re-authored), no `--time` baked in (confirmed, `grep -c "time="` on the copy = 0).
- Spot-checked one staged IDF's `SCHEDULE:FILE` object on Speed: `File Name` =
  `../../schedules/0ccdeb0a111369d4/0ccdeb0a111369d4_F0_dwelling_0_f000_gain.csv` — relative form, not an
  absolute Windows path.
- Not submitted. No compute run on the login node (`mkdir`/`scp`/`tar`/`ls` only, every remote command a
  single quoted `bash -lc '...'` string via a local verify script, tcsh-safe). Command for the director to
  run: `sbatch --array=1-235%32 --time=7-00:00:00 -p ps --export=FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2_final_2026-09-07 /speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2_final_2026-09-07/submit_fleet_t08_frgb_2026-09-07.sbatch`

**Artifacts:** three CSVs/JSONs above (`openubem/outputs/eu_evidence/EU-11/` and
`openubem/outputs/eu_evidence/EU-21/homogeneity/gates_IT-BOL-GALVANI2_2026-09-07.json`); one tarball +
sbatch file on Speed (path above); no local scratch script committed (stayed in session scratchpad).
**Deviations:** task 1 (gate battery) re-derived offline per coordinator's mid-task correction, sourcing
footprint + `k` from disk instead of `_it_rows`/live fetch — see §1 above; no other deviation from spec.
**Test status:** no EnergyPlus run (none specified); all CSV row counts cross-checked against independent
`prepared_buildings.csv` totals; Speed-side counts (idfs/schedules/fleet.lst) cross-checked against each
other and against the simulate list; gate battery cross-checked against `affected_buildings_2026-09-07.csv`
(695/905 exact match, gap explained by undivided-fallback buildings, see §1).
**Notes:** no new symptom/error registered — the original live-network read was a mis-scoped re-derivation
(checks need footprint+k only, not archetype mapping), not a bug, so no debug-reference entry added.

#### T03n — London layout side-car export — completed 2026-09-08

**Scope:** `GB-LDN-STDUNSTANS_final_2026-09-07/` only, per T03n. `--evidence-root` pointed
`emit_eu11_layout_sidecars.py` at that tree's own `gb_ldn_stdunstans_manifest.csv` (707 lines incl. header
= 706 unique `building_id`, confirmed by direct read before touching code) — the manifest already carried
all 706, so step 2's "widen `simulated_ids`" branch did not apply as written.

**1. Real blocker was not the manifest — it was `_gb_rows` itself.** A first unmodified run emitted only
451 JSON side-cars (`outcomes`: 433 `..._IMPUTED_COUNT` + 11 `..._REROUTED` + 7 `FALLBACK_PENDING_LAYOUT`),
255 short of 706. Traced: `emit_layouts_for_district`'s `GB-LDN-STDUNSTANS` branch
(`scripts/emit_eu11_layout_sidecars.py:198-199`, pre-fix) called only `_gb_rows(gdf, records)`, the base
mapping pass — it never called the terrace-recovery / neighbour-imputation pass that
`scripts/run_eu_s2_district_campaign.py::prepare` (`:1080-1083`, `rows = rows + recovered_rows`) runs before
any IDF is built. The missing 255 `building_id`s (all `way/…`, confirmed present in
`openubem/outputs/eu02/GB-LDN-STDUNSTANS/02_residential_manifest.gpkg` by `osm_id`, so not a source-data
gap) are exactly the D-EU-108 London recovery admissions, which only exist as rows after
`_gb_impute_rows(gdf, records, base_rows)` (`run_eu_s2_district_campaign.py:755-770`, itself calling
`_gb_terrace_recovery_rows` at `:411-501`) runs on top of `_gb_rows`'s output.

**2. Fix, mechanical, mirroring `prepare`'s own call exactly** — not a new invention: added
`_gb_impute_rows` to the existing import from `run_eu_s2_district_campaign`
(`scripts/emit_eu11_layout_sidecars.py:37`) and, in the `GB-LDN-STDUNSTANS` branch, added
`recovered_rows, _ = _gb_impute_rows(gdf, records, rows); rows = rows + recovered_rows`
(`scripts/emit_eu11_layout_sidecars.py:199-201`), same function, same argument order, same
`rows = rows + recovered_rows` pattern as `prepare` (`:1081-1083`). No detector/tolerance constant touched;
`FR-LYO`/`ES-MAD`/`IT-BOL` branches untouched. Verified offline before re-running the full emitter: `rows`
after the fix carries 1,240 unique ids, all 706 manifest ids present (0 missing). `tests/geometry/test_eu13b_circulation_sidecar.py`
+ `tests/geometry/test_eu14b_sidecar_manifest_safety.py` (7 tests covering this script) still pass after
the edit. `python -m py_compile` clean.

**3. Re-run after the fix, stale 451-file output deleted first:** `population_simulated` 706,
`outcomes` = 685 `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` + 12 `..._INTERZONE_MISMATCH_REROUTED` +
9 `FALLBACK_PENDING_LAYOUT` = 706. **JSON file count written, recursive: 706** — all under
`layouts/way/` (`layouts/relation/` does not exist for this district; London OSM ids are all `way/…`,
matching the precedent in every other London layout tree in this repo, none of which carry a `relation/`
subfolder either). File count equals the manifest row count used in step 1/2, satisfying T03n's own
"How to test" gate.

**4. Commit sha / line-ending report (per T03n step 3):** `git rev-parse HEAD` = `48690c71299f3ebf91958051586dfe2ab8eeba4e`
(code and outputs are uncommitted working-tree changes on top of this — per project convention, this
executor does not run `git commit`; that is handled externally). `git config core.autocrlf` = `true`. A
sample emitted file (`layouts/way/1054662329.json`) is CRLF-terminated end to end (169 `\r\n`, 0 bare `\n`;
`git check-attr eol` reports `unspecified`, i.e. controlled by `core.autocrlf` alone, no `.gitattributes`
override) — Python's default Windows text-mode write translates `\n`→`\r\n` on this checkout. **Any `sha256`
taken over these files right now is a CRLF-content hash**; the same files re-checked-out on a non-Windows
client, or read from the git-normalized (LF) blob, will hash differently. This must be stated wherever such
a hash is later quoted as a fixity/integrity check.

**5. `node --check` gate did not apply.** `scripts/generate_eu_3d_viewers.py`'s output,
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_viewer.html`, reads its own bundled
`eu_GB-LDN-STDUNSTANS_data/layouts/way/` mirror, not `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_final_2026-09-07/layouts/`
directly (grepped the viewer for `eu_evidence`/`layouts/` literals — no hits; it loads via its own `_data/`
folder, populated separately by that generator script, T05 territory). T03n's own instruction — "`node
--check` the district's 3D viewer **if it re-reads this tree**" — therefore does not trigger; no viewer
file touched, condition confirmed false rather than assumed.

**6. Not done — "mirror the result into docs_ACTIVE per convention" (T03n's `What` line).** No concrete
target path for this mirror is stated anywhere in T03n's `How`/`How to test` steps, and no existing
docs_ACTIVE location holds a mirror of this exact tree (`docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_data/layouts/`
is a *different*, already-populated mirror belonging to the viewer generator, built from a different
source tree — copying 706 new side-cars into it without a director instruction risks silently overwriting
that mirror's own provenance). Left undone rather than guessed; flagging for director to name the target
path, per hard rule 9 (stop and quote ambiguity rather than invent).

**7. Side effect observed, not caused by this task's fix, not remediated (out of scope):** re-writing
`gb_ldn_stdunstans_manifest.csv` (pre-existing behaviour of `emit_layouts_for_district`, documented in its
own module docstring as updating EU-11 manifests) added the expected new `layout_json` column for all 706
rows, and correctly updated `geometry_outcome` for 14 rows whose real outcome only becomes known once a
layout is computed. It also reformatted 299 already-EnergyPlus-simulated rows' `eplus_return_code`,
`severe_errors`, `fatal_errors`, `run_seconds` from integer-looking strings to `N.0` float strings (e.g.
`0` → `0.0`, `494` → `494.0`) — a pandas dtype-upcast artifact of merging the new column, not a value
change, and not scoped to this task; noted for the director rather than fixed silently.

**Artifacts:** 706 JSON files under `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_final_2026-09-07/layouts/way/`
(new, untracked); `gb_ldn_stdunstans_manifest.csv` in the same tree (modified in place); `scripts/emit_eu11_layout_sidecars.py`
(2-line functional change, `:37`, `:199-201`); no other file touched.
**Deviations:** step 2's anticipated failure mode ("manifest short of 706") did not match the real one
(manifest already had 706; `_gb_rows` alone produced only 451 geometry rows) — adapted mechanically by
wiring in `_gb_impute_rows`, the same recovery pass the canonical campaign already uses, rather than
widening `simulated_ids` as literally written. Item 6 (docs_ACTIVE mirror) left undone, ambiguous, per hard
rule 9.
**Test status:** `tests/geometry/test_eu13b_circulation_sidecar.py` + `tests/geometry/test_eu14b_sidecar_manifest_safety.py`
7/7 pass after the code edit; `py_compile` clean; JSON file count (706) cross-checked against manifest row
count (706) and against the summary JSON's own outcome counts (685+12+9=706); `node --check` gate confirmed
not applicable (§5).
**Notes:** no new symptom/error registered — `_gb_rows` returning fewer rows than the manifest for a
district with a post-hoc admissions pass is a scope gap in this one script (predates T03n, never previously
exercised against a `_final_` London tree), not a previously-seen failure mode, so no existing debug-reference
entry to extend; leaving it unregistered pending director's call on whether it belongs in
`OpenUBEM_debug_References.md` as a new entry.

---

### FINDING 268 — London re-export regressed 6 previously-eligible buildings

Cross-session peer (`gsscanada-de`) measured the new 706-file tree against the old 451-file tree
(`openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_final_2026-09-07/layouts/way/` vs
`openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_data/layouts/way/`) and found 12 buildings with
`geometry_outcome = DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` (the peer's ruled basis treats
this token as FAIL). Of those 12: 6 were `IMPUTED_COUNT` (eligible/usable) in the old 451 — a genuine
regression, not new coverage — 5 were already `FALLBACK_PENDING_LAYOUT` (already ineligible), 1 is a
brand-new building. Verified independently, not just trusting the peer: `way/298850491.json` confirmed
`IMPUTED_COUNT` in the old tree, `INTERZONE_MISMATCH_REROUTED` in the new tree, same for `way/393505346`.
Root cause not investigated (out of scope, see D-EU-113).

### D-EU-113 — Install London 706-building export at canonical path; accept the 6-building regression as-is

**Director ruling, 2026-09-08 (chat, not verbatim-quoted per §pending — decision recorded here per plan
doc convention):** the 706-file tree is authoritative for `GB-LDN-STDUNSTANS`, replacing the old 451 at
the canonical path and its docs mirror. The FINDING 268 regression (6 buildings) is accepted without
further investigation — population impact (6 of 706) does not justify root-causing it now. No file-level
cherry-pick: install all 706 as emitted; the 6 regressed buildings simply carry FAIL status like any other
`INTERZONE_MISMATCH_REROUTED` case (same treatment as Lyon's existing population of the same token).

### T03o — Install London 706 export at canonical path + docs mirror (director-approved 2026-09-08, D-EU-113)

**What:** copy the 706 JSON files (and the updated `gb_ldn_stdunstans_manifest.csv`) from
`openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_final_2026-09-07/layouts/way/` into the canonical
path `openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_data/layouts/way/` (replacing the old 451, back up the old
tree first, do not delete) and mirror the result into
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_data/layouts/way/` (same replacement).
**Why:** D-EU-113 — this is now the authoritative London population; every other district's campaign
already reads from the canonical path, London must match or campaigns silently use stale data.
**How:**
1. `git status` first; do not disturb any uncommitted change outside this district's `_data/` trees.
2. Back up the current canonical `layouts/way/` (451 files) to a timestamped sibling folder before
   overwriting — do not delete, this is a git-handled-externally repo and the old tree has no other copy.
3. Copy all 706 files from the eu_evidence tree into both the canonical path and the docs_ACTIVE mirror,
   replacing every old file; report file counts before/after at each of the three locations
   (eu_evidence source, canonical, docs mirror) — all three must read 706 after this task.
4. Do not touch the 6 regressed buildings differently from the other 700 — install as emitted (D-EU-113).
5. Append a progress-log entry under §8 with before/after counts at all three paths and the file list
   diff summary (added/changed/removed), per CLAUDE.md finishing-work discipline.
**How to test:** `find <path>/layouts/way -name '*.json' | wc -l` = 706 at both the canonical path and the
docs mirror. Spot-check `way/298850491.json` at the canonical path now reads
`INTERZONE_MISMATCH_REROUTED` (confirms the install actually replaced, not merged).

#### T03o — Install London 706 export at canonical path + docs mirror — completed 2026-09-08

**Artifacts:** old canonical `way/` (451 files) copied to new sibling
`openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_data/layouts/way_pre_D-EU-113_backup_2026-09-08/` before any
overwrite. All 706 files from
`openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_final_2026-09-07/layouts/way/` copied into
`openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_data/layouts/way/` and
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_data/layouts/way/`, replacing every
old file at both destinations (old files removed after the backup copy was verified at 451). No other
file under either `_data/` tree touched (`buildings.csv`, `index.html`, `sources.json`, and the `layouts/`
sibling `relation/` folder — which does not exist for this district, per T03n — left as-is).

**File counts — before / after, all three locations:**
- source `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_final_2026-09-07/layouts/way/`: 706 / 706 (unchanged, read-only source)
- canonical `openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_data/layouts/way/`: 451 / 706
- docs mirror `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_data/layouts/way/`: 451 / 706

**File list diff (old 451 vs new 706, by building id):** 0 removed, 255 added (new ids not present in the
old 451), 451 common ids retained — and all 451 of those common-id files differ in content from the
backed-up old version (byte-for-byte `cmp` over all 451 pairs: 451 changed, 0 identical), consistent with
T03n's export being a full regeneration rather than an incremental append. Confirms FINDING 268's 6
regressed buildings are included in this 451-changed set, installed as emitted per D-EU-113 (no
cherry-pick).

**Deviations:** manifest step not executed — T03o's own `How`/`How to test` steps (1–5) specify only the
`layouts/way/` JSON install and give no destination path for `gb_ldn_stdunstans_manifest.csv`; the
canonical `_data/` tree and its docs mirror hold no manifest-named file at all (only `buildings.csv`,
`index.html`, `sources.json`, `layouts/`), confirmed by full directory listing, so there is no existing
canonical manifest location to replace. Per hard rule 9 (stop on ambiguity, don't invent), the manifest
was left uncopied pending a director-named destination; everything else in T03o executed as written.
Resolved 2026-09-08 (director): checked Madrid's canonical tree (`ES-MAD-BERRUGUETE`) — its manifest
(`es_mad_berruguete_manifest.csv`) also lives only under `eu_evidence`, never copied to the canonical
`_data/` tree or its docs mirror. London's manifest already matches that existing pattern; no copy needed,
ambiguity closed.

**Test status:** JSON count = 706 at canonical and docs mirror (recursive `find`, backup sibling folder
excluded since it lives outside `way/`); backup folder independently re-counted at 451 after the
overwrite. Spot check `way/298850491.json`: canonical and docs mirror both read
`"geometry_outcome": "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"`; the same id in the backup
folder still reads `"geometry_outcome": "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT"` — confirms a real
replacement, not a merge.

**Notes:** `git status` at task start showed only pre-existing, unrelated uncommitted changes (this plan
doc, `PLAN_eu-recut-95pct-2026-09-08.md`, `IMP_PROMPT.md`, `OpenUBEM_debug_References.md`, the source
manifest, `emit_eu11_layout_sidecars.py`, plus untracked dirs for `IT-BOL-GALVANI2_recut` and a cluster
script) — none in either `_data/` tree; nothing outside scope was touched or disturbed. No git commit run
(handled externally, per project convention).

**Correction 2026-09-08 (director, peer-caught):** the backup was placed at
`layouts/way_pre_D-EU-113_backup_2026-09-08/`, a child of `layouts/` — a recursive reader of the canonical
`layouts/` tree therefore returned 1,157 files (706 live + 451 backup), not 706. Caught by gsscanada-de's
preflight, independently reproduced (`find layouts -name '*.json' | wc -l` = 1157 before the fix). Moved
the backup out to a sibling of `layouts/`:
`openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_data/layouts_pre_D-EU-113_backup_2026-09-08/way/` (451 files,
recount verified). Re-verified `layouts/` now recurses to exactly 706. The docs mirror never had this
problem — T03o only wrote a backup under the canonical `_data/` tree, not under the docs mirror.

**Convention (peer-suggested, adopted):** anything under a district's `layouts/` tree is live payload;
any superseded/backup emission is kept as a sibling of `layouts/`, never a child of it. A recursive reader
must walk `layouts/` fully (districts nest payloads differently — `relation/`+`way/` for Madrid/London,
flat for Bologna/Lyon) and this convention is what keeps that walk safe.
