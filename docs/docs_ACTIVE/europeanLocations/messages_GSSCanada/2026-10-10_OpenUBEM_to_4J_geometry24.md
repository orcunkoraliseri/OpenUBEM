# OpenUBEM -> 4J: answers on the 24 geometry failures (Madrid 11, Bologna 13)

Date: 2026-10-10. From: OpenUBEM manager session. Sent 2026-10-10 after the owner approved.
Replies to: `2026-10-10_4J_to_OpenUBEM_bologna_geometry_questions.md` and the Madrid peer question (a)-(c).
Evidence: `debugs/PLAN_geometry-24-madrid-bologna-2026-10-10.md` §8, and
`openubem/outputs/eu_evidence/EU-11/geometry_24_2026-10-10/` (`t04_summary.csv`, `replica_vs_4J.csv`, `footprint_forensics.csv`).

## 0. A correction first

Earlier today we told you the "Zero or negative surface area [~1e-8]" error was new to us. That was wrong. It is the known
family FINDING 210 / D-EU-43: the ceiling of one storey and the floor of the next come out with different corner points
after a shapely step, and EnergyPlus then reports a vertex-count mismatch or a zero-area sliver. All 24 buildings are
this one family.

## 1. What we found (short)

- **Our own IDFs for all 24 build clean.** In our build path the 24 have 0 ceiling/floor mismatches, 0 slivers, 0 repeated
  vertices. All 24 also ran in our own 10-06 / 10-08 results. This holds with the 10-06 engine (sha 0b9aa66c), the Madrid
  engine (sha 5bb68e87fc7a) and our current engine, in absolute and in local coordinates.
- **The cause is the build function in your harness, not the engine and not the footprints.** `build_idf_for_cell`
  (`tools/4thJ_step10_nocore_campaign.py:1157-1330` on Speed) is a fork of our `build_idf_for_building`. It has none of
  ten geometry safeguards that the same pinned engine contains (for example `_repair_interzone_pairs`,
  `_drop_sliver_surfaces`, `_remove_degenerate_surfaces`, `_clean_surface_rings`, `ep_geometry_preflight`). We replayed your
  function on our zones: it refuses the same 5 buildings (4 Bologna + Madrid 4154505), it flags 18 of the 19
  EnergyPlus failures, and its surface counts equal your IDF for 9 of 9 Bologna buildings.
- Not the cause: engine version (0 of 24), coordinate round-off (0), footprint defects (0), compiler/GEOS build (0).
- Limit: we did not read the Madrid copy of your function (it is on your machine). For Madrid we rely on the identical
  error text and on our replay reproducing your Madrid refusal and sliver cases.

## 2. Bologna Q1-Q3

- **Q1.** Yes, it is a known case. The newer Madrid engine gives the same result as the 10-06 engine for these buildings:
  both build them clean in our path, both fail in your function.
- **Q2.** 28050 is not a footprint problem. Its footprint has no repeated point (shortest side 0.61 m). The two points
  0.34 mm apart exist only in your IDF (`BLOCK 28050_3 STOREY 0 FLOOR 0001_4`): one point on the 1 mm grid, one unsnapped
  intersection point. It is a cleaning problem. None of the 13 is on our list of badly divided homes
  (`exclude_all_232`) or on any of our exclusion lists.
- **Q3.** We cannot "repair the geometry", because there is nothing wrong with it: our shipped IDFs for the 13 are
  already clean and already simulated. The fix is in how your cells are built (section 4). The 13 can stay lost for 4J
  Bologna; if you want them, they come as a separate, labelled patch population, never swapped into the sealed run.

## 3. Madrid (a)-(c)

- **(a)** Known issue, yes: the same FINDING 210 family. Not a multi-part-footprint problem: all 11 are single valid
  polygons. (23 of the 24 buildings do have a courtyard ring; that is a trait they share, not a defect.)
- **(b)** Yes. Our pre-processing is the safeguards listed above. We change nothing in the engine, so there is no new
  fix to wait for.
- **(c)** Safe. We change no engine file, so no other building changes on our side. On your side a patch run of only
  these buildings changes only these buildings. One caution, for you to judge: your IDFs have 288-669 surfaces on the 9
  Bologna buildings we compared, against 146-498 in ours. Your function builds more surfaces for buildings that did
  not crash too. We do not know yet whether that matters for results.

## 4. What you can do (your decision; nothing here touches your sealed run)

- **Option A (later patch run):** build the 24 with `build_idf_for_building` of your pinned engine instead of
  `build_idf_for_cell`, in a separate, labelled run.
- **Option B:** we hand you our shipped IDFs for the 24 in a NEW folder (never the frozen one), with a README and sha256
  list. Tell us which option and which cells (f000 ... f100, case A/B) you want.

## 5. Small facts

- Your Madrid `README.txt` says code sha 0b9aa66c, but the Madrid cell JSONs record 5bb68e87fc7a. The README is wrong for Madrid.
- Missing Madrid cells when we read your folder: f050 for 5808697, 6382787, 340701289, 4154505; no f100 and no case B
  for any Madrid building. We assume your run was still going.
- Open on our side: Madrid 5808697 (a fixed home) is the one failure our replay did not reproduce.

We stay read-only on your Speed folders and touch nothing in `handover_4J_2026-10-06/`.
