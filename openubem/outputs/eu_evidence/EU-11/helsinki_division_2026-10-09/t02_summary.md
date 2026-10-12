# T02 summary - dry run of the engine levers (2026-10-09)
Scope: the 120 V1 homes. The other 2 left-out homes (1 U1 rerouted at IDF write, 1 U4 box fallback) are not shape failures; the levers cannot fix them (not scored). Scorer used: `score_division._divided_result`, final ruleset, best_effort off; a home counts as recovered only when that scorer returns OK or V3 for the whole home.
Search: 7 theta offsets (0-90 by 15) x cut_nocore (plain, swept, swept+snapped), cut_layered, cut_radial, cut_wingwise, cut_grid and cut_grid_snapped rows 2-6, cut_ring_bisect (courtyards); each candidate through the engine's `_finish_candidate`, then `improve_cut_nocore` on every candidate that still failed, best plate score first. 10 min limit per home x lever (hard kill at 11 min). Duplicate candidates skipped.

| Lever | Homes scored | Recovered | Timed out | Flats removed | Floors changed |
|---|---|---|---|---|---|
| L1 same k, other cut | 120 | 46 (+9 tag-only) | 64 | 0 | 236 |
| L2 k-1 on failing floor | 9 | 3 | 6 | 9 | 9 |
| L3 k from 48 m2/flat floor | 22 (10 no-op = L1) | 4 | 8 | 744 | 27 |
| Any lever | 120 | 60 (51 real + 9 tag-only) | 60 never solved | 745 (cheapest lever per home) | 264 |

- Tag-only: 9 homes whose delivered floors all pass the checks but carry the generator's best-effort tag (C10). Rescoring without the tag recovers them with no geometry change (T01 lists them).
- L1 recoveries: 46 homes; median 22 s, slowest 545 s. 236 storeys get a new cut, no flat is removed.
- L2 and L3 were NOT run on the 64 homes where L1 timed out (they would time out on the same plates; 10 min each = 5+ h). L2 ran only on 9 homes (6 early-run homes, plus the 1 home L1 finished but failed: 744346, class V2 after L1, L2 fixes it by removing 1 flat). L3 ran only where it changes k (22 homes incl. 10 no-ops, 12 real).
- Flats removed: 745 in total, but 728 are the three multi-part plates 875288_part0/2/3 (39 flats/floor copied onto 363-505 m2 plates, T01 side finding); without them 17 flats (16 for 746417 by L3, 1 for 744346 by L2).
- Projected correctly divided: (458 + 60) / 580 = 518 = 89.3 %; without the 9 tag-only 509 = 87.8 %. Target 551 (95 %): short by 33.
- Homes that time out (10 min): 64 of 120 in L1 (32 cooperative stop, 32 hard kill); 60 of them stay unsolved by any lever. These are the big deep plates (median 15 flats per floor, depth 33.5 m, 996 m2).
- Limit of the evidence: an unsolved home means "not solved in 10 min", not "unsolvable".
