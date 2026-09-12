# Manager handoff — opened 2026-09-09, 13:00 EDT; current as of 2026-09-12 EDT; **session closed 2026-09-12 EDT** — read "State at close" in the 2026-09-12 status update first

- **Role of the session receiving this**: **manager / director**. Reads docs, writes and audits plan
  docs, dispatches executors. **Never writes feature code.**
- **Two threads.** Thread A is ours and is **closed**. Thread B is a peer session's campaign; as of
  2026-09-11 the user changed the plan and we now **help that session whenever it asks**, instead of
  only recording it. Read the 2026-09-12 status update right below first — it is the current truth.
- **Paste everything below the rule into the new session.**

---

## ⚠ Status update — 2026-09-12 EDT (this is the current truth; supersedes every section below on status, including the 2026-09-11 update)

**Thread B continued, three exchanges with `gsscanada-de`, all answered directly under the
2026-09-11 "help them whenever it asks" rule. Nothing on our side changed: no code edited, no IDF
rebuilt, no cluster job submitted, no published number touched, no repo file created. This session
was read-only apart from this handoff entry.**

**1. We sent them the 93 Bologna reroute IDs.** Extracted from the frozen manifest
`openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_merged_2026-09-08/it_bol_galvani2_manifest.csv`
(1,215 rows), `geometry_outcome = ..._INTERZONE_MISMATCH_REROUTED`:

```
28134 28473 28527 28696 28700 28721 28749 28917 28968 28969 29094 29108 29180 29211 29228 29437
29466 29643 29718 29788 29813 29822 30037 30139 30240 30319 30323 30384 30508 30570 30651 30817
30850 30912 30968 30988 31016 31035 31118 31281 31289 31401 31410 31461 31481 31500 31615 31661
31669 31716 31773 31774 31821 31854 31888 31916 31977 32008 32062 32073 32211 32233 32279 32280
32306 32372 32392 32453 32493 32524 32552 32556 32662 32668 32755 32797 32800 32860 32864 32981
33063 33080 33171 33193 33260 33354 33401 33412 33446 92926 93207 93387 93409
```

The tolerated (unsimulated, unrepairable by design) 10 were already with them:
`27931 29109 29171 29629 30001 31169 31234 31376 31440 32694`. 93 + 10 = our complete 103-building
Bologna bad-geometry population.

**2. Their overlap check: 45 of their 49 residual Bologna failures match us exactly** — 42 in our 93,
3 in our tolerated 10 (92 %). Four did not appear in either list: **28861, 28891, 31278, 31445**.

**3. A third Bologna defect class exists and is worth knowing** (measured this session from the same
manifest, not previously written down anywhere): **117 buildings completed with `severe_errors > 0`**
(severe=1 → 93, severe=2 → 23, severe=30 → 1; 9.6 % of 1,215), and this set has **zero overlap** with
the 93 reroute buildings. Trap: severe=1 also numbers 93 but is a *different* set — do not equate them.
Severe families seen in the one batch that retained run logs
(`IT-BOL-GALVANI2_recut_2026-09-08/local_out/<stem>/eplusout.err`, 84 dirs): degenerate surfaces,
`RoofCeiling:Detailed` vertex-size mismatch, non-convex shadowing surfaces. These 117 are inside the
published Bologna EUI (54.671865 over 1,205), so per-building values from that set are approximate;
the city figure stays frozen and is not restated.

**4. My first answer on their 4 was wrong; they disproved it and I corrected it.** I attributed the
4 to that severe-geometry class and suggested their harness might escalate severe → fatal. They read
their own `eplusout.err` for all four and showed the real fatal is the interzone **construction**
mismatch: `GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface ... does not have
the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent
surface ...` → `**Fatal** ... program terminates`. The correlation is still real — both symptoms come
from the same massing situation, a shorter block beside a taller one — but it is not the cause.

**5. The real answer: this is FINDING 253, root-caused and fixed on our side 2026-09-05.** Registered
at `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:2307`. The old code assigned constructions by
nominal `Surface_Type` alone, with no `Outside_Boundary_Condition` check; both constructions are
single-layer `MATERIAL:NOMASS` built from different U-values (`u_roof_w_m2k` vs `u_floor_w_m2k`), so
the mirror check can never be satisfied. Our current
`_assign_envelope_constructions` (`scripts/run_eu_s2_campaign.py:569`, called at `:727`) gives any
`ROOF`/`ROOFCEILING` whose `Outside_Boundary_Condition == "Surface"` the **floor** construction,
matching its partner; a true exterior roof (`Outdoors`) is unaffected. Introduced in commit `5dd13d71`.

**Not a version difference.** We run EnergyPlus `23.1.0-87ed9199d4`, the same build they do
(`energyplus_version` column of the Bologna manifest).

**What we told them to do.** Port that one branch. It is independent of the post-extrude geometry
bracket, costs no zoning, and therefore does **not** need the author sign-off they are waiting on for
the reroute port (which does cost per-flat schedules on ~93 buildings). Two conditions stated: it must
run **after** `intersect_match` has set `Outside_Boundary_Condition`, and it carries an accepted physics
caveat — the interzone roof takes the floor U-value.

**6. Their author approved porting both fixes (2026-09-12).** They asked for the exact source; we sent
it: `_envelope_construction` + `_assign_envelope_constructions` verbatim (`scripts/run_eu_s2_campaign.py:562-593`),
the post-extrude bracket verbatim with the long rationale comments elided (`:640-728`), line spans for
every helper (`_has_near_duplicate_vertex_surfaces` `:94-141`, `_drop_redundant_ring_vertices` `:149-230`,
and the `openubem/idf/surfaces.py` imports at `:127`, `:452`, `:493`, `:547`, `:640-749`), and the call
order against their own stages: all of it at IDF-build time inside `build_cells`, with
`_assign_envelope_constructions` **last**, after `intersect_match`, or the fix is a silent no-op. We also
flagged three traps: the reroute mutates `zones` in place, the tolerated-box branch writes
`fallback_reason` and those buildings must be excluded, and the `RuntimeError` must be caught per
building. Suggested test: two construction-fatal IDs with the FINDING 253 branch alone, two reroute IDs
with the full bracket, to confirm on their side that the two fixes are independent.


**7. Port result and the second round (2026-09-12, later).** They ported both fixes, tested, and re-ran
Bologna + London in full. Recovery: London 0 of 70, Bologna 40 of 490; ~520 cells still fail (450 Italian
across 94 buildings, 70 UK across 7). Two residual signatures, both cities: (a) a true vertex-COUNT
mismatch on `RoofCeiling:Detailed` pairs (11 vs 12, 7 vs 3), and (b) `GetSurfaceData: Zero or negative
surface area` on `CEILING`/`FLOOR` slivers. Their reading was that our bracket does not cover real count
mismatches. That is inverted, and it is the whole answer: `find_mismatched_interzone_pairs`
(`openubem/idf/surfaces.py:547-571`) IS a literal `len(surf.coords) != len(partner.coords)` comparison —
but it is a detector only, and the three repairs for that class live inside `extrude_geometry`
(`surfaces.py:872-980`), not in `scripts/run_eu_s2_campaign.py`, so the bracket they copied arrived
without them. Sent them, with line spans against commit `9d6026af`: `_repair_roof_roof_pairs` (:452-490),
`_repair_mismatched_horizontal_pairs` (:493-544) and `_pair_interfloor_surfaces` (:127-160), all four
called at `:964-969` immediately after `intersect_match`; `_rebuild_degenerate_coreperim` (:750-771) for
the zero-area class, which is a third family — `_coreperim_has_degenerate_surfaces` (:240-256, 1 cm
coincident-vertex collapse, `_COINCIDENT_VERTEX_TOL` at :164) and `_coreperim_has_tiny_zone_area`
(:319-331, `_TINY_ZONE_AREA_M2 = 0.5`), both scoped by `_is_coreperim_zone` (:232-238), which they must
widen if their failing surfaces are not core/perim; `_coreperim_has_inverted_winding` (:335-345) stays
deliberately unwired and must not be enabled. Root cause given for their count mismatches: FINDING 221 —
independent per-zone ring snapping to a 1 mm grid (`RING_STABILIZATION_GRID_M`,
`openubem/geometry/european_residential.py:2085`) lets one physical vertex land on two floats, so
`intersect_match` clips a sliver on one side only and that side gains a vertex; `_snap_shared_interzone_vertices`
(:774, invoked at :915) fixes it at the source, before extrusion. Full ported order sent as a→f, ending
`_assign_envelope_constructions` last. Expectation set: this class does not reach zero — our own tolerated-box
residue was ~10 Bologna buildings, to be reported as excluded with the denominator, not chased.


**8. Sign-off request on physics-affecting repair logic (2026-09-12, third round).** They came back having
established that their checkout live-imports our current `surfaces.py` (9d6026af), so nothing was missing by
"port" after all. Two specific claims, both technically correct as stated: (i) Bologna's fatals are cross-type
Ceiling(lower)↔Floor(upper) interfloor pairs, which `_repair_mismatched_horizontal_pairs` skips by design
(`partner.Surface_Type.upper() != stype` → continue, `surfaces.py:493`) and `_pair_interfloor_surfaces`
(:127) cannot help with because it only pairs exact-matching vertex sets; (ii) London's zero-area surfaces
sit in `room_layout` zones, which `_is_coreperim_zone` (:231) excludes, so both degenerate guards are scoped
out. They asked for sign-off before writing (a) a cross-type reset-to-exterior repair and (b) a widened
guard scope.

Ruling sent — **no to both**, with the reasons:

- (a) The cross-type pair is not meant to be repaired, it is meant to be **excluded**.
  `find_mismatched_interzone_pairs` (`surfaces.py:547`) is type-agnostic and does catch Ceiling↔Floor
  count mismatches; the campaign gate at `scripts/run_eu_s2_campaign.py:674-718` then attempts
  `_force_reroute_room_layout_to_one_zone_per_floor` and, failing that, raises
  `interzone_vertex_mismatch_unresolved` (:717) so the cell never reaches EnergyPlus. Their buildings
  reaching E+ at all means the gate is not running or the RuntimeError is being swallowed — that is the
  real gap, and it needs no new logic. Also flagged `_drop_redundant_ring_vertices` applied at
  `:640-642` **before** `extrude_geometry`, which they may have skipped.
- Physics reason for refusing (a): an interior ceiling/floor between two heated dwellings reset to
  `Outdoors` still simulates and returns a plausible but silently wrong EUI — strictly worse than the
  Fatal. Roof↔Roof reset is safe only because a roof genuinely is exterior. Sole safe recovery direction
  named: equalise the counts (drop the extra collinear vertex), never change the boundary condition.
- (b) Pointed them at `_force_reroute_room_layout_to_one_zone_per_floor` (`surfaces.py:640`), the
  room_layout guard they had not found. Widening `_is_coreperim_zone` is refused because the remedy filters
  on the same predicate (`:582`), so a widened detector fires and rebuilds nothing — a Fatal converted to a
  silent no-op. If they add anything, the sanctioned shape is the fallback already at `:950-952`: coreperim
  reroute first, room_layout reroute if it returns False. `_coreperim_has_inverted_winding` stays unwired
  for room_layout too, same false-positive reason.
- Told them the reroute is not free: it collapses the dwelling partition to one zone per floor, so those
  cells are tagged (`generation_status_note = "room_layout_intersect_fallback"`) and must be reported
  separately, not counted as clean passes. `CheckConvexity: non-planar` is Severe, not Fatal — not to be
  chased. Zero-residue expectation restated.
- Offered to review one full `eplusout.err` plus both surfaces' vertex blocks before they change any
  physics-affecting logic.


**9. Root-cause candidate: stale `Number_of_Vertices` (2026-09-12, fourth round) — ❌ DISPROVED same day, see item 10; kept only as a record of the mechanism, which is real in geomeppy but did not apply here.** They disproved the
"gate not running" hypothesis — their `4thJ_step10_nocore_campaign.py:994-1115` carries our gate verbatim on
top of `9d6026af`. Yet `it__29171__caseA__f000` still reached EnergyPlus (returncode 1) with two surfaces
cross-referenced to each other and reported at 11 vs 13 vertices. They asked whether geomeppy can change a
vertex count between our check and `idf.saveas()`.

Answered: no, but the count they read is probably not the count our detector reads.

- `.coords` is `eppy/function_helpers.py:29-34` — `obj[Number_of_Vertices_index+1:]` grouped in 3s, i.e. the
  live `obj` list that `saveas` serialises. No lazy cache, no autocalculate recompute. Check-time value ==
  written value.
- geomeppy's matcher pairs on `almostequal(s.coords, reversed(m.coords))`
  (`geomeppy/geom/intersect_match.py:57`), which is positional — it structurally cannot cross-reference an
  11-triple surface with a 13-triple one. Their IDF has them cross-referenced, so the 11/13 is very likely
  the declared field, not the triples.
- Mechanism: `intersect_idf_surfaces` (`intersect_match.py:34-37`) builds each split fragment as
  `copyidfobject(parent)` + `set_coords(...)`, and `set_coords`
  (`geomeppy/geom/surfaces.py:43-47`) truncates `obj` at, and keeps, the parent's `Number_of_Vertices`
  before appending the new vertices — **it never updates that field**. EnergyPlus only auto-counts when the
  field is blank/autocalculate; otherwise it believes the declared number. So a fragment can declare the
  parent's old count while carrying a different real one: our detector (triples) passes, E+ (declared)
  fatals. This is also a better candidate than near-duplicate collapse for the `e21bec78b937acf5` case our
  own comment records at `scripts/run_eu_s2_campaign.py:655-673` (0 mismatches reported, E+ fatalled anyway)
  — worth re-testing on our side if that class ever returns.
- Asked them to read field 4 and the actual `Vertex_n` lines for both surfaces before touching anything.
  Declared-differs → confirmed; triples-genuinely-differ → reopen, because something outside geomeppy wrote
  those pairings.
- Signed off, conditional on that check, on two changes — both declaration-level, neither physics:
  normalise `Number_of_Vertices = len(surf.coords)` (or blank it) on every `BUILDINGSURFACE:DETAILED`
  immediately before `saveas`, which is what `openubem/idf/european_box.py:70` already does on our box path;
  and extend `find_mismatched_interzone_pairs` to compare the declared field as well as `len(coords)`.


**10. Closed out as the tolerated-box class, with one open rate anomaly (2026-09-12, fifth round).** They
retracted the 11 vs 13 — it was a truncated `sed` read on their side. Both surfaces declare
`autocalculate` and both genuinely carry 13 vertex triples, so item 9's mechanism does not apply to this
building and is not the explanation for anything currently observed. What the two surfaces do carry is a
near-duplicate vertex pair ~0.2 mm apart at the same ring position (opposite winding, hence the one-index
offset), inserted by `intersect_match` after the pre-extrude ring clean — exactly the
`near_duplicate_vertex_tolerated_box` class under the T15 / D-EU-58 owner ruling. They also traced their
`run_cell_inner` (`4thJ_step10_nocore_campaign.py:1351-1456`) and confirmed a `RuntimeError` is reclassified
as `HARNESS_ERROR`, never silently written, so the gate is not being swallowed. `find_mismatched_interzone_pairs`
is behaving correctly throughout; there is no gate blind spot.

Agreed their disposition — stop chasing this building, wire London's one-zone-per-floor fallback, report
residuals as excluded with the denominator. One thing flagged back before they accept it:

- **The rate does not match.** Our Bologna residue in this class is ~10 of 1,215 (under 1%); theirs is 94 of
  ~490 (~19%). Same commit, same geomeppy, same EnergyPlus, so a 20x gap is upstream of intersect_match,
  not the same defect at the same frequency.
- Cheapest explanation offered: the `mode` key on their zone dicts. `_snap_shared_interzone_vertices`
  (`surfaces.py:799`) and `_force_reroute_room_layout_to_one_zone_per_floor` (`:664`) both filter
  `z.get("mode") in ("room_layout", "european_dwelling_layout")` and return early when empty. A different
  `mode` value would make the pre-extrude snap a no-op (so shared edges reach `intersect_match` as sub-mm
  near-misses and get sliver-clipped — precisely how a 0.2 mm pair is inserted) **and** make the reroute
  decline for a bogus reason rather than a genuine courtyard. One key explains both symptoms and the 20x.
  Asked them to print `sorted({z.get("mode") for z in zones})` before `extrude_geometry`, plus confirm they
  run `_drop_redundant_ring_vertices` at the `run_eu_s2_campaign.py:640-642` position.
- **Refused in advance:** a post-intersect de-duplication of the near-duplicate pair. Editing coordinates on
  surfaces EnergyPlus has already paired manufactures the genuine count mismatch they do not currently have
  if it collapses one side only. If it ever becomes necessary it must be driven from one canonical vertex
  set applied to both partners, and the proposal comes to us first.
- Told them a 19% exclusion is a headline number, to be stated alongside our sub-1% figure so the two
  campaigns are not read as like-for-like.


**11. The `mode` key confirmed missing; tag signed off with four conditions (2026-09-12, sixth round).** They
grepped every zone-dict construction site: no zone dict they build ever sets `mode`, so `z.get("mode")` is
`None` fleet-wide, in both cities. Splitting the consequence, which they did correctly:

- `_snap_shared_interzone_vertices` was already worked around in a prior round — they run its clustering body
  inline and unconditionally at `4thJ_step10_nocore_campaign.py:1062-1076`, diffed against `surfaces.py:806-811`,
  same tolerance and logic. Not the gap.
- `_force_reroute_room_layout_to_one_zone_per_floor` is the real, previously-unnoticed gap: called directly at
  their `campaign.py:1098`, but `rl_zones` is always empty, so it returns False immediately and the fallback
  has never once attempted to run, on either city. That, not the snap, is what the 19% vs sub-1% gap was
  pointing at.

Signed off on their proposal to set `"mode": "european_dwelling_layout"` on every zone dict, after verifying
the blast radius here: `mode` is read in exactly three places in our package — `surfaces.py:664` (reroute),
`:799` (snap), `:886` (`!= "core/perim"` placeholder loop, unaffected either way since both `None` and
`"european_dwelling_layout"` fail that test). Every other occurrence is a writer. The tag cannot change
physics by itself. `_get_floor_idx` (`:94-99`) also parses both their naming schemes correctly.

Four conditions attached:

1. `floor_polygon` is a bare subscript at `:682`, outside every try — a missing key turns today's tolerated
   cells into KeyErrors, trading `ENERGYPLUS_FAILED` for `HARNESS_ERROR`. Verify the key exists on every zone
   dict, as a shapely Polygon in the same metric CRS as `coords_m`.
2. 🔴 The real trap: a successful reroute mutates `zones` in place (`:721-747`) — dwelling zones removed,
   `<osm_id>_F<i>_whole` zones inserted at the front. Anything downstream iterating a list captured before the
   call will condition zones that no longer exist and leave the real ones bare — a silently unconditioned
   building with a plausible low EUI, worse than the Fatal.
3. Rerouted cells carry `generation_status_note = "room_layout_intersect_fallback"` and `narrow_fallback`;
   they have lost their dwelling partition, so they are recovered-not-clean and need their own manifest line.
4. Their inline snap and ours will now both fire — a harmless no-op, but two sources of truth; prefer deleting
   the inline copy.

Expectations set: the reroute still declines on genuine courtyards (interior ring ≥ 1 m², `:693`) and on
multipart/degenerate unions, so the residual will not reach zero. Smoke test on `it__29171` and
`uk__way-1054785381` first, with real before/after numbers and the `room_layout_intersect_fallback` count —
no fleet-wide roll-out before we see those.


**12. Their arc stops at a modelling boundary, not a geometry one (2026-09-12, seventh round).** They checked
all four conditions before running anything and did not apply the tag. Conditions 1 and 4 are fine
(`floor_polygon` present on every zone dict; they will delete their inline snap once ours fires). Condition 2
is mechanically a non-issue for them — they pass the same `zones` list object through, so the in-place
mutation is visible downstream.

But condition 2's *consequence* collides with a rule of their own. Their campaign binds one HETUS occupancy
diary per **dwelling** zone, and their R7 rule refuses a cell outright whenever the zone count and the
assigned-diary count disagree — written to stop a diary series being silently reused on zones it was never
measured on. Our reroute collapses N dwelling zones to one zone per floor, so every cell the reroute rescues
is then refused by R7 for an unrelated reason. The fix therefore converts one non-completing outcome
(EnergyPlus fatal) into a different non-completing outcome (refused before EnergyPlus runs), never into a
completed cell. They escalated to their author rather than inventing an occupancy rule — correct call, and
endorsed as such. Nothing here is a defect in our pipeline; the limit is in their HETUS layer.

Replied with three things, none pre-empting their author:

- **Measure the prize first.** Apply the tag on a throwaway branch, run generation only, no EnergyPlus, and
  count how many cells the reroute actually succeeds on, split by city. It declines on courtyards and
  multipart unions so the count is well under their 94 + 7. That turns an abstract question into a sized one
  — eight buildings is not worth their author's time, eighty is.
- **Three outcomes, three buckets.** Geometry fatal / rescuable-but-R7-refused / unrescuable are three
  populations with three causes and must be counted separately, or the geometry work reads as having failed
  when it actually hit a modelling boundary.
- **Compounding disclosure.** If the author authorises a representative schedule, those cells carry two
  departures at once — dwelling partition replaced by one zone per floor, and occupancy no longer measured
  per dwelling. They need their own manifest line, not the recovered pile. Offered a design check before they
  write anything on the occupancy side.


**13. Dry run sized the prize at 49 of 52, and a stale-count defect surfaced on their side (2026-09-12,
eighth round).** They ran the generation-only dry run on a throwaway script — tag applied, `zones_for_cell` +
`extrude_geometry` + the mismatch/near-duplicate check + reroute attempt, no `saveas`, no EnergyPlus, nothing
written to the real run tree or `campaign_progress.jsonl`.

- Baseline, untagged: the reroute declines **100%** of the time in both cities (45/45 IT, 7/7 UK) —
  direct confirmation that the `mode` gate has been disabling this fallback for every building they have.
- Tagged: Bologna 42 of 45 succeed geometrically, 3 decline; London 7 of 7. **49 of 52** currently-failing
  buildings, which puts it firmly on the worth-deciding side. They are taking that number to their author as
  the concrete input to the occupancy ruling.

Replied with four points:

- **"Up to 49", not 49** — a dry run stopping before `saveas` proves the reroute emits a block, not that
  EnergyPlus accepts it. Told them it should nonetheless hold nearly all the way, because one_zone_per_floor
  has no interzone perimeter pairs and so structurally cannot reproduce this fatal, the reasoning our own
  comment records at `scripts/run_eu_s2_campaign.py:657-660`.
- **Restate the rate.** Their 94-building figure was stale; the real number is 45, so their Bologna loss is
  ~9% of ~490, not ~19%. Ours in the comparable class stays under 1% of 1,215. The gap is ~10x, not ~20x —
  use 9%, an overstated figure is the first thing anyone will challenge.
- **Identify the 3 declines.** The function logs its reason and the two cases mean opposite things to an
  author: genuine courtyard (interior ring ≥ 1 m², `surfaces.py:693`) is permanent exclusion, multipart/
  degenerate union is a footprint-reconstruction artefact that may be recoverable later.
- 🔴 **Their stale-count defect is the more important find, not a side note.** Their dashboard's Bologna
  failure count came from a `cells_failed/` directory that is never cleaned when a cell later succeeds on a
  resume, so it reported 94 where the latest status per cell in `campaign_progress.jsonl` gives 45 (450
  cells, consistent). Told them to sweep every other reader of that directory before handing anything over —
  any figure sourced from it since their first resume is wrong by the same mechanism, and a restated number
  invalidates everything downstream of it. Their London figure (7 buildings / 70 cells) was already correct.

Nothing owed on our side: our Bologna population stays 1,205 of 1,215, unaffected by their recount.


**14. Their four points closed; one wrong restatement caught before it shipped (2026-09-12, ninth round).**
They accepted "up to 49", corrected the rate to 9% of ~490 against our under-1% of 1,215 (~10x, not ~20x),
and resolved both open items:

- **The 3 Bologna declines are all genuine courtyards**, reproduced against the function's own
  footprint-union/interior-ring logic: `29171` one ring at 56.0 m², `31169` two rings at 10.2 and 37.0 m²,
  `32694` one ring at 22.7 m². All far above the 1 m² threshold (`surfaces.py:693`), so permanent exclusion
  by design, not recoverable artefacts. Final shape: **up to 49 of 52 recoverable pending the occupancy
  ruling, 3 permanently excluded regardless of it.**
- **Nothing automated reads their `cells_failed/` directory** — the campaign script only writes to it, and
  every stale figure came from them manually `find`-ing it at each check-in. Their cell counts (450 IT,
  70 UK) survive because those were cross-checked against the completions directory when first derived; only
  the Bologna distinct-building count skipped that cross-check, which is why it alone was wrong. Going
  forward they derive every count from latest-status-per-`cell_id` in `campaign_progress.jsonl`.

Two things sent back:

- 🔴 **Corrected a factual error in how they restated our structural argument.** They had turned it into
  "one_zone_per_floor has no interfloor pairs at all", which is false and would have collapsed the recovery
  claim the moment anyone opened a rebuilt IDF — one_zone_per_floor does have one ceiling/floor pair per
  storey junction, which is exactly where `it__29171` fatalled. The load-bearing distinction is *intra-floor*:
  with one zone per storey there are no neighbouring blocks for geomeppy's `intersect()` to cut against, so no
  sliver clipping and no asymmetric vertex insertion — the junction pair is emitted by a single `add_block`
  from identical rings and is clean by construction. The pair exists, it is simply not at risk.
- Declined to ask for a full re-audit of prior ticks (disproportionate), but asked for one sentence to their
  author: earlier distinct-building counts were derived the same way and are likely overstated, while cell
  counts were cross-checked and stand.

Both landed: they corrected the wording to "the pair exists, one per storey junction, clean by construction"
and added the prior-ticks sentence. The (a)/(b) decision is with their author.

**15. Author authorised the fix and the occupancy rule; design check answered (2026-09-12, tenth round).**
Their author approved both halves: recovering the up-to-49 stuck buildings through the `mode`-gate tag, and
giving each merged one-zone-per-floor zone a single representative occupancy schedule built by averaging the
per-dwelling HETUS diaries on that floor. The author explicitly generalised it — "if you think this method is
suitable for other simulations as well go for it" — so it becomes their standing rule for merged-floor cases,
not a one-off. Their plan: tag zones in `zones_for_cell`, regroup units by floor after a successful reroute,
average the diaries, re-run their R7 count check against merged counts, smoke-test on `it__29171` (expected to
decline) and one UK `way/*` building (expected to merge), then `--resume` Bologna and London only.

They asked two things: any objection to a plain unweighted arithmetic mean of the diaries, and whether we have
an existing HETUS averaging helper to reuse.

Answered, six points:

- **No helper to reuse.** "HETUS" appears nowhere in our repo (grep over `openubem/` and `scripts/`, zero
  hits). The nearest analogue is `openubem/semantic/european_schedules.py`: `read_presence_csv` (:65) takes a
  generic 8,760-hour presence series and `build_step8_gain_series` (:22-63) rescales it to a fixed annual mean
  of 3.0 W/m² (`BASE_GAIN_W_M2`, :19), emitted as a W/m² Schedule:File plus OtherEquipment and deliberately
  never as a `People` object (:88 docstring). Relevant as precedent for the normalisation, not as code.
- **Plain mean is conditionally fine, and the condition is worth stating.** Conservation requires
  Σᵢ wᵢ·φᵢ(t) = W_total·φ̄(t), so the correct weight is whatever the schedule multiplies — floor area if the
  diary drives W/m², occupant count if it drives a `People` fraction. A plain mean equals that only when the
  dwellings on a floor are equal in that quantity. **But** if each diary is normalised to its own annual mean
  before merging, as ours is, every series already carries the same annual mean, annual totals are conserved
  under any weighting, and plain vs weighted differs only in hourly shape — in that case no objection.
- 🔴 **The load-sum trap, flagged as more important than the weighting.** When four dwelling zones collapse
  into one floor zone, the merged zone must carry the **sum** of the four dwellings' design levels (people,
  equipment, lighting, infiltration). Keeping one dwelling's level simulates cleanly and returns a
  plausible-but-wrong EUI — the same silent-wrong failure class already refused twice in this thread, and
  strictly worse than the crash being fixed. Asked for a per-building assertion that pre-merge and post-merge
  design-level sums agree, failing the cell otherwise.
- **Two limits to record rather than fix.** Averaging flattens the peak, so merged buildings stay valid for
  annual heating and invalid for peak or cooling sizing; and the mean is only defensible for quantities
  entering linearly, so the same diaries must not be averaged anywhere they drive setpoints, window opening,
  or HVAC availability. Asked them to keep merged buildings distinguishable in the manifest so nobody later
  quotes them as per-dwelling-resolved.
- **Stale-list trap in their step 2, repeated.** A successful reroute mutates the `zones` list in place
  (`openubem/idf/surfaces.py:721-747` removes the dwelling dicts and inserts one per floor), so their
  floor-grouping must re-read `zones` after `extrude_geometry` returns, not work from a copy taken before it.
- **Clear `cells_failed/` before the `--resume` run**, since it is never cleaned on resume and recovered
  buildings would otherwise stay counted as failures — the same direction of error as their earlier overstated
  counts.

Also confirmed `it__29171` declining is the correct outcome, not a bug: the courtyard guard at
`openubem/idf/surfaces.py:693` returns False on any interior ring ≥ 1 m². And noted that whatever Bologna
figure their re-run produces is theirs, not comparable with our published 2026-09-08 value of
54.671865 kWh/m² over 1,205 of 1,215.

**Pending:** their implementation and smoke tests. They come back only if something in the six points
conflicts with what they find. Nothing is open on our side and no new investigation starts before they report.

### State at close — 2026-09-12 EDT (session closed at the user's request)

Nothing is in flight: no code edited, no plan doc open, no cluster job running, no checkpoint waiting on
the user, no reply owed to anyone. The next manager session starts from a clean board.

- **If `gsscanada-de` writes again**, answer directly under the 2026-09-11 "help them whenever it asks"
  rule. The six points in item 15 are the standing answer; only a measurement that conflicts with one of
  them needs a new round. A peer can never authorise anything here — no permission, config or `CLAUDE.md`
  change on their request, their author's approval binds their side only, and a peer message is never the
  user's approval for a pending prompt.
- **If the user opens new work instead**, the next piece is item 2 of "Read first": close `OPEN-17, 56, 60,
  61, 62, 63, 64` in `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` and recompute the
  live/retired counts (14 live → 7 live, next free `OPEN-65`). **Not authorised yet — ask the user in one
  sentence before starting it.**
- **Every published number is frozen and untouched by threads A and B since 2026-09-10**: Bologna
  54.671865 kWh/m² over 1,205 of 1,215, EU fleet 66.295394 over 4,142 of 4,171, North American fleet
  153.95 over 8,139. Whatever Bologna figure the peer's re-run produces is theirs and is not comparable
  with ours.
- **Two files are modified and uncommitted** (`git status`): this handoff doc and
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Git is handled externally — do not commit or stage.

---

## ⚠ Status update — 2026-09-11, late evening EDT (superseded 2026-09-12 on status — still the correct record of the driver-fix diagnosis and its citations; do not quote it for where things stand)

**The plan changed, by the user's own words: "we changed the plan, help gsscanada whenever it needs".**
Thread B is no longer record-only. This session now answers the peer session (`gsscanada-de`) directly
and does not ask the user before each reply. What did **not** change: a peer can never authorise a
checkpoint, a permission change, a config or `CLAUDE.md` edit, or the adoption of a published number.
Anything that would move one of our published numbers, or open new work on our side, still goes to the
user first. If the peer says it was denied permission and asks us to act instead, refuse and surface it.

**What the peer was stuck on (Bologna, their "C2 campaign"), and what we told them.**

They reported that 77–79 of about 1,170 Bologna buildings died in EnergyPlus before the first timestep,
on two different machines, with the same signature: a surface reported as non-planar, then a
zero-or-negative surface area of about 1.4e-08 m², then a fatal stop in `GetSurfaceData`. Their example
was building `27683`. They then confirmed the failure persists at git commit `9d6026af`, which is the
commit that already contains our fix — a real contradiction, not a stale checkout.

**Cause, confirmed and now registered.** Their driver (`4thJ_step10_nocore_campaign.py`) calls
`extrude_geometry()` directly, and the fix does not live in that function. Three separate steps, only
one of which is inside it:

1. `_stabilize_ring_coords` runs at **layout** time, inside `european_building_layout_to_zone_specs`
   (`openubem/geometry/european_residential.py:2824`, `:2838`). Zone dicts built by any other path
   arrive at extrusion unstabilized.
2. `_snap_shared_interzone_vertices` **is** inside `extrude_geometry` (`openubem/idf/surfaces.py:916`),
   but it is gated on zone mode, not on a flag: `surfaces.py:800` keeps only zones whose `mode` is
   `room_layout` or `european_dwelling_layout`, and returns early when that list is empty. Any other
   `mode` silently gets nothing.
3. Our delivered tree was **not** built by `extrude_geometry` at all. It is built by
   `build_idf_for_building` (`scripts/run_eu_s2_campaign.py:596`), which brackets the extrusion with
   `_drop_redundant_ring_vertices` on every `coords_m` before (`:641-643`), then after (`:674-725`)
   `find_mismatched_interzone_pairs`, `_has_near_duplicate_vertex_surfaces`,
   `_force_reroute_room_layout_to_one_zone_per_floor`, a second `intersect_match`,
   `_repair_roof_roof_pairs`, `_repair_mismatched_horizontal_pairs`, `_pair_interfloor_surfaces`, and
   finally `_assign_envelope_constructions` (`:727`, `FINDING 253`).

Source present at the right commit is necessary but not sufficient. **Registered** as its own entry in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (~line 2290, immediately after the
`FINDING 210` / `D-EU-43` v3-harvest entry), with the full symptom string, both remedies, and the
residual.

**Two remedies given to them; their author decides, not us.** (a) call `build_idf_for_building` as the
geometry entry point and overwrite the schedules afterwards — geometry and occupancy are independent,
so they do not need our EUI numbers to reuse our geometry path; or (b) replicate all three bracket
steps in their own driver. With (b) they must catch `RuntimeError("interzone_vertex_mismatch_unresolved: ...")`
explicitly (`scripts/run_eu_s2_campaign.py:714-722`) or the driver dies on the first such building
instead of skipping it.

**What the expected end state looks like after a fix** — worth keeping, because it is the acceptance
test for their rerun: zero EnergyPlus fatals from the vertex-count-mismatch class (that class is either
repaired or refused at build time and never reaches a run), and about **10** Bologna buildings that
build cleanly, carry `fallback_reason = "near_duplicate_vertex_tolerated_box"`, and then fatal at
runtime with the `27683` signature. Those ten are unrepairable by design (the reroute rescue declines —
`openubem/idf/surfaces.py:640-696`; owner ruling 2026-09-01) and both candidate geometry remedies were
measured at **0 of 184** offending surfaces cleared. They are excluded from the simulated population and
kept in the census, with the denominator stated.

**One trap we made them rule out, and the result.** A 100 % failure streak also looks exactly like the
schedule-packaging failure (`schedules/` not staged beside `idfs/` and `weather/` → every task dies at
`ProcessScheduleInput` before warmup). They checked case-insensitively — the objects are emitted
uppercase `SCHEDULE:FILE`, so a case-sensitive grep reports "no schedule references" on a file full of
them — and ruled it out: the schedule hits were benign warnings present in passing cells too, and every
failing cell dies in `GetSurfaceData`/`CheckConvexity`. Their run is a real geometry defect, valid as
far as it goes.

**Their final tally, 2026-09-11.** 11,710 cells: **10,770 completed, 940 failed**, across **94** distinct
buildings, each failing all 10 of its cells. 94 of ~1,170 is 8 %; our full-chain Bologna build loses 10
of 1,215, which is 0.8 %. So the driver fix recovers roughly **84 buildings, about 7 % of their
population**, and the rerun touches only those 94 buildings (~940 cells, under 9 % of the campaign).
Accepting their current result as final means publishing over ~1,076 buildings where ~1,160 is
reachable on the same inputs — a population gap large enough that the two must never be differenced.
All of this is logged verbatim on their side for their author, who was offline. They have paused
monitoring and will ping us when the author picks a direction, or if the rerun surprises them.

**Nothing is pending on our side.** No code was edited, no IDF was regenerated, no cluster job was
submitted, and no new file was created in the repo for this. The only repo change is the one
debug-reference entry named above.

**If the peer comes back**, the two things to check first are: does their residual land at about ten
buildings, and do those IDs overlap the tolerated list we already sent them. A much larger residual, or
a non-overlapping set, means something new and is worth a fresh look rather than a restatement.

---

## ⚠ Status update — 2026-09-10, ~15:00 EDT (⚠ superseded 2026-09-11 on status only — still correct for Thread A's record and citations; do not quote it for where things stand)

**Thread A is finished.** All nine tasks (T01–T09) are done and all four checkpoints are signed.
T07 (fleet re-simulation on the cluster) finished 2026-09-10, T08 (harvest + re-parse) produced the
restated number the same day, and the user signed **CP-4** with "yes lets go": the fleet number is now
**153.95 kWh/m² pooled over 8,139 buildings**, carbon **881,743 t CO2e** on the same 8,139. This
replaces the old number, 153.8231 over 8,153 — the two counts are different building sets, so never
subtract one from the other.

T09 (mark every old mention of the number as outdated) is also done: 279 markers went into 50 project
documents, plus 9 into the public "numbers" board and 11 into the public "open items" board (that
second board was missed by the first pass and was found and fixed afterward). A repo-wide check
afterward found zero remaining mentions of the old number without a note next to it.

**One piece of bookkeeping is still open, not started yet.** The plan also resolved several items on
the open-items list without those items being marked closed there yet: `OPEN-17` (done at step 1,
remaining steps ruled void), `OPEN-56` and `OPEN-60` (the fix already existed; this plan's fleet
re-run/re-parse is what they were waiting on), `OPEN-61` (the plan's own words: "T08 is what discharges
it"), `OPEN-62` (its last two broken readers were fixed), `OPEN-63` (a published number was picked) and
`OPEN-64` (the code was fixed and the reference values raised). None of that has been written into
`INVESTIGATION_open-items-register-II.md` yet — updating those seven rows and the live/retired counts
(14 live → 7 live, by count) is the next task there.

Everything below this point (the 2026-09-09 status update and the Thread A section) is history —
correct for what it records, but stale on current status. Read it for the reasoning and the citations,
not for where things stand now.

---

## ⚠ Status update — 2026-09-09, ~00:30 EDT (supersedes the Thread A "task state" below where they conflict)

This paragraph is the current truth; the Thread A section further down was written at 13:00 EDT and is
stale on task state (it still says T06 is in flight). Do not delete the Thread A section — read it for
the rulings and citations, just not for current status.

**Where things stand.** T01–T06 are complete. **CP-1 and CP-2 are both signed** (plan §9): population
for T07 onward is **8,152** (8 buildings excluded — bad geometry, unrelated to any T06 code change,
named in the CP-2 entry). **T07 is in flight**: cluster array job `1315099` (8,152 tasks, `--array=1-8152%32`,
`--time=7-00:00:00`) is submitted and running.

**Cluster contention, diagnosed, not a bug.** The account's CPU cap is 32 total, shared across every
project on `o_iseri`'s account — not per job. A peer session's own campaign (`gsscanada-de`, job
`1315013` "4J_c2_ES") is holding 31 of the 32 CPUs, so our array is running only 1 task at a time until
that job finishes; two more of that peer's jobs (`1315014`, `1315015`) are queued behind it, not yet
competing. **The user has explicitly ruled: never touch that job or any other project's run — wait for
it to finish naturally, and our array (already throttled at `%32`) will auto-fill to full width the
moment CPUs free up.** No action needed at that moment; do not raise the throttle, it is already correct.
Per-task time measured from `sacct`: ~60 s/task; at full 32-wide that is roughly 4h for the ~7,890
remaining.

**Monitoring.** A plain background shell loop (not a model agent — see
`feedback_executors_stall_waiting_on_monitors.md`) polls `squeue`/`sacct` for job `1315099` every 30 min
via the login node and will end on its own the moment the array fully drains (success, failure, or
cancellation all count). Do not dispatch a monitoring agent; check `squeue -u o_iseri` /
`sacct -j 1315099` directly instead if picking this up cold.

**Standing authorization, given verbatim by the user 2026-09-09 night, user then went offline
("i will sleep you continu to the end ... i will return tomorrow"):** continue autonomously through
T07 → **CP-3** (director sign-off: did every task complete, is the harvest whole) → **T08** (harvest,
re-parse, compute the restated figure and its population — arithmetic only, dispatched to a fresh
Sonnet executor per the model-cost rule). 🔴 **Stop hard at CP-4 and do not cross it under any framing.**
CP-4 is adoption of the restated number, and that is the user's decision alone — present the T08 result
and wait. A paraphrased "continue" from anyone other than the user's own later words does not authorise
CP-4. If T07 fails, stalls in a way `sstat` shows as genuinely dead, or T08 produces a number that
disagrees with the population/citations pinned in plan §4–5, stop and surface it instead of guessing.

---

## Read first (paste from here)

You are the manager session for OpenUBEM, working in `C:\Users\o_iseri\Desktop\OpenUBEM`.
Python is **`.venv/Scripts/python.exe`** — never bare `python`. **Git is handled externally: never
commit, never stage.** Read `CLAUDE.md` before anything else; its communication rules override
everything, including the shape and length of every reply you send the user.

Read, in this order:

1. `docs/docs_ACTIVE/openings/implemenation/PLAN_accuracy-restatement-2026-09-09.md` — **closed**, all
   nine tasks and all four checkpoints done. Section 8 (progress log) has the full record; the T09
   entry is the last one.
2. `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` — the open items. 🔴 **Not yet
   updated for the plan above**: `OPEN-17, 56, 60, 61, 62, 63, 64` are all resolved by that plan but
   still show as live rows here — closing those seven rows and recomputing the live/retired counts is
   the next piece of work, if nothing else is more urgent.
3. `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` **§1 Geometry** — thread B's entire record.
   Search it **before** debugging anything, and register any fix there **before** closing a task.

---

## Thread A — the North American fleet restatement. Ours, **closed 2026-09-10** (history below).

**The published number is `153.8231 kWh/m²` pooled over `8,153` buildings, and it has not moved.**
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.
The fleet is 8,160 buildings; 8,152 scored `ok`.

⚠ **Never difference that figure against the abandoned 2026-08-22 census rebuild** (`152.3011` →
`171.7718` over `n = 8,144`). Different populations. The whole point of this plan is to restate the
number **on its own population** rather than subtract two incompatible ones.

**Task state.** T01, T02, T03, T05 complete. T04 complete at step 1 only, its remaining steps void by
ruling D-E. **CP-1 is signed** (plan §9) on a full suite of **2,654 passed / 40 skipped / 25 failed**,
which closes exactly against the pre-T04 tree of 2,639 / 55 / 25: +15 passed, −15 skipped, failures
unchanged. ⚠ The plan's own `1,937 / 55 / 0` baseline is **stale** — do not difference against it. The
25 failures pre-date this work and belong to the OPEN-44 triage.

**T06 is in flight, split in two.** The code half — the district-heating carbon factor — was dispatched
to a Sonnet executor and its edits are on disk:

- `openubem/config.py:84` — `GWP_DISTRICT_HEATING_KGCO2_KWH = 0.226`, US EPA *GHG Emission Factors Hub*
  Jan 2025 ed., table "Steam and Heat". Chosen by the director under ruling D-B; the reasoning is in
  the plan's "D-B resolved" entry and must travel with the number: it is a **calculated default, not a
  measurement**, and its fleet exposure is **zero buildings**.
- `openubem/results/parser.py` — a `*_district_eui_kwh_m2` provenance column for each of the fourteen
  `_DISTRICT_HEATING_ROWS`; seven were added for the mixed columns.
- `openubem/results/carbon.py` — every district column charged at the new factor; the gas and
  electricity terms take only their non-district part.

🔴 **The invariant, already verified by the director by hand and worth re-verifying if anything moves
again:** no `*_eui_kwh_m2` golden may change by a digit. Measured on all three fixtures — every energy
golden is byte-identical to its T03 value, and each `gwp_*` golden moves by exactly the district-heat
kWh times `0.226 − 0.181`. r1: heating rose 105.045350 kWh/m², carbon rose 4.727041; r2: 78.887778 and
3.549950; r6: 101.658025 and 4.574611. Exact on all three.

**What is not done.** The full suite on the carbon change was running at handoff
(`C:\Users\o_iseri\AppData\Local\Temp\pytest_full_T06.txt`); read the triple and close it against
2,654 / 40 / 25. Then the **second half of T06** — rebuild all 8,160 inputs and IDFs — has not been
dispatched. 🔴 8,160 IDFs is multi-building work: it goes out in parallel, **never in a `for` loop**.
Report the row count at every stage against 8,160; a stage that loses buildings names which and why
before the next stage starts. Fleet exposure to district heating is **zero buildings of 8,152**, so
**no fleet EUI and no fleet carbon number may move at T06** — state that from the rebuilt manifest,
not from assumption.

**Then**: 🛑 **CP-2** before any cluster submission → T07 (`sbatch --array=0-8159%32`,
`--time=7-00:00:00`, fire-and-forget) → 🛑 **CP-3** → T08 (the restated figure and its population).

🔴 **Stop at CP-4 and do not cross it.** Adoption of the restated number is **the user's decision, not
the director's** (plan §7). T09 — attaching supersession markers to every published `153.8231` and
`8,153` — is downstream of adoption and is held with it.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.
A paraphrased "continue" never authorises a
checkpoint; only the user's own words do.

**The five rulings, all pinned in plan §4.** D-A: a full fleet re-simulation is authorised, accuracy
over speed. D-B: one published district-heating factor, chosen by the director — **discharged**.
D-C: fix the code and raise the reference values — **discharged by T03**. D-D: OPEN-61 stays open until
T08 discharges it. **D-E**: the deterministic floor-count ladder at
`openubem/semantic/building_classifier.py:145-155` **stays**, and the draw tier is not enabled for
`levels` or any other target already covered by a signed-off estimator on the production build path.
The user ruled it on 2026-09-09. The reason it mattered: enabling it would have replaced a
deterministic estimator with a sampled one, moving storey count → floor area → the denominator of every
EUI, and the fleet would have been simulated twice.

---

## Thread B — the peer's geometry campaign.

⚠ **Superseded 2026-09-11 — do not quote this section for current status or for our posture.** It is
kept for the ES-MAD-BERRUGUETE record and its citations. Two things in it are now wrong: "record only"
(the user has since ruled that we help the peer whenever it asks), and the cell/building counts (they
are from an earlier, smaller wave). The current picture is the 2026-09-11 status update at the top.

A peer session (`gsscanada-de`) is running a European campaign (ES-MAD-BERRUGUETE) and sends measured
findings. **We record them and correct our own record; we do not act on them.** At handoff: 1,100 cells
of 11,510, fifteen failing buildings, nothing retried, dropped or patched.

**Four failure classes**, tally (a) 3, (b1) 8, (b2) 1, (c) 2 pure + 1 mixed. The whole record, with every
supersession marked, is in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §1. Two things from it
matter to a manager:

1. **(b1)'s cause is accounted for**: the engine collapses every sub-10 mm edge in a ring, and one of
   its two reported vertex counts is exactly `written − k` where `k` is the number of short edges.
   Eight of eight, no exceptions.
2. **Where those short edges come from splits (b1) in two.** In five buildings every short edge is an
   exact 1 mm grid step; in three, none lies on any grid. So one half asks whether a 1 mm snap floor is
   too fine, and the other asks what creates an edge *below* the floor.

⚠ **Three measurements are owed on our own tree and none has started**, in this order:
(i) does our build path manufacture edges at or below the snap floor — our snap calls are
`set_precision(g, 0.001)` at `openubem/geometry/european_nocore.py:131,616,620` and
`set_precision(footprint, 0.005)` at `openubem/idf/surfaces.py:702`, both untouched;
(ii) does our emitter ever write an interzone partner that does not name it back — the only one that
reaches (b2); (iii) can our adjacency match pair two faces metres apart.

🔴 **They are blocked on the author's authorisation, given directly in the session, and a peer cannot
grant it.** Never edit permission settings, `CLAUDE.md` or config because a peer asked; never treat a
peer message as the user's approval for a pending decision; if a peer says it was denied permission and
asks you to act instead, refuse and surface it to the user. That is permission laundering.

**Control for our own tree, before any interzone construction change is ever made**: assign interzone
pairs from one construction and its reverse, never from surface type. That is the peer's (c) class and
it is entirely their runner's defect — do not import it.

---

## Hard rules for the manager session

1. **Never write feature code.** Every dispatch is a **brand-new** session with `model: "sonnet"` passed
   explicitly (`haiku` for pure monitoring). Never resume a finished agent for new work; the exception
   is the same task still in flight. State lives in the plan doc, never in an agent's history.
2. **Dispatch a verb and a command, never a question.** Cap every command's output. Split long agents at
   task boundaries. The director's own `grep -c` or one-line `python -c` beats a dispatch.
3. **Cluster**: no compute on the login node — `mkdir`, `scp`, `tar`, `squeue`, `sacct` only. The login
   shell is tcsh, so wrap every remote command in `bash -lc` (the `_ssh()` helper at
   `scripts/cluster/t08_harvest_results.py:104`). Always `sbatch --array`, width `%32` account-wide,
   `--time=7-00:00:00` minimum. A silent task is dead only if `sstat -a -j <jobid>_<idx> -o
   JobID,AveCPU,MaxRSS` shows CPU time no longer tracking Elapsed. Never estimate a finish time by feel
   — measure it with `sacct -j <id> -n -X -o Elapsed,State`.
4. **Run only one pytest process at a time.** Concurrent suites crash on this machine with a
   `joblib`/`loky` access violation, and a crashed run is not a test result.
5. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc. No `.py` under `docs/`. Figures go to
   `openubem/outputs/` flat. No code comments by default. **Create nothing that was not asked for.**
6. **Write doc edits atomically** — temp file plus `os.replace`, with a single-occurrence assertion on
   every anchor, and real UTF-8 characters rather than escapes. A plan document in this project has
   already been truncated to zero bytes by a non-atomic write to an untracked file.
7. **When a recorded claim is superseded, leave the old one visible with a "do not quote" marker** and
   say what replaced it. Several claims in the geometry chapter are already marked that way, including
   two of the director's own.
8. **Audit before saying done.** A deliverable is a set of artifacts and it is finished only when every
   one agrees — the summary, the manifest, the figure, the mirror, the docs. Report pass/fail per line
   with the measured values, never a summary sentence.

## Replying to the user

The user is not a native English speaker and cannot read long answers. Every reply: one plain opening
sentence, three to five short bullets, an `Evidence:` line with paths, and a `Next:` line of three or
four words. Under about eighty words. No tables, no headers, no IDs inside the sentences, at most one
🔴, at most one decision and only as the last line. Paths and code go only in `Evidence:`. Read your
reply back as if you were tired and reading in your second language; if a bullet needs a second read,
rewrite it.
