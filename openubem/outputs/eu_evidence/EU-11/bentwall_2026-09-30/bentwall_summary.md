# Bent party walls: why each V3 home is bent (T01, 2026-09-30)

Engine basis = the corner test of `_flat_bends` on the plate itself (what C13 counts). Census basis = the same test on the smoothed plate the census used, added only on storeys where the engine sees C13 = 0.

## Corners per type (engine basis, 478 of 478 homes read)

| district | straight_missed | straight_not_better | no_chord | interior_end | junction_wrap | wing_bend |
|---|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE | 28 | 182 | 3 | 82 | 35 | 10 |
| FR-LYO-HAUTCOEURPENTES | 17 | 86 | 3 | 40 | 93 | 0 |
| GB-LDN-STDUNSTANS | 4 | 24 | 0 | 23 | 11 | 0 |
| IT-BOL-GALVANI2 | 22 | 194 | 13 | 261 | 28 | 15 |
| all | 71 | 486 | 19 | 406 | 167 | 25 |

Corners on engine basis: 1174. Census-basis extra corners (storeys with C13 = 0): 415. Homes with no geometry (fix IDF floors are not a partition): 13 of 478. Homes read with no corner on either basis (`no_bend`): 13 of 478. Homes with a row: 478 of 478.

`straight_missed` = 71 corners; engine would accept the straight wall on 9, the other 62 are refused only because the C12 spread value drops (no check breaks).

## Homes by worst type (order: straight_missed, straight_not_better, no_chord, interior_end, junction_wrap, wing_bend, no_bend, no_geometry)

- straight_missed: 27 of 478
- straight_not_better: 163 of 478
- no_chord: 6 of 478
- interior_end: 118 of 478
- junction_wrap: 63 of 478
- wing_bend: 75 of 478
- no_bend: 13 of 478
- no_geometry: 13 of 478

## The 128 homes with C13 = 0 on every storey

- 128 of 478 in baseline.csv; 13 of 128 have no geometry (blank), 115 of 128 read.
- 88 of 115 show only wing_bend corners or no cut-made corner at all.
- 27 of 115 are exceptions (census-basis corner not a wing bend, or one engine straight_not_better); ids: 28721, 28959, 29822, 30390, 30478, 30913, 31468, 32362, 32800, 32860, BATIMENT0000000240880394_part0, BATIMENT0000000240881103_part0, BATIMENT0000000240881123_part0, BATIMENT0000000240881139_part0, BATIMENT0000000240881324_part0, relation/12700645, relation/4154596, relation/4495683, way/100704738, way/1054785374, way/288600848, way/290026256, way/298846078, way/310771769, way/409624879, way/433014323, way/434877455

## Madrid 25-home sample

First 25 Madrid `wrap` homes of v3_split.csv, engine basis, corners per type. Mapping to the 7 / 5 / 8 check: junction = junction_wrap; interior or wing end = interior_end + wing_bend; not better = straight_not_better + straight_missed + no_chord.

| home | straight_missed | straight_not_better | no_chord | interior_end | junction_wrap | wing_bend |
|---|---|---|---|---|---|---|
| relation/12700645 | 0 | 0 | 0 | 0 | 0 | 0 |
| relation/12725306 | 0 | 0 | 0 | 4 | 0 | 0 |
| relation/12765477 | 0 | 0 | 0 | 5 | 0 | 0 |
| relation/13033800 | 0 | 0 | 0 | 1 | 0 | 0 |
| relation/4154596 | 0 | 0 | 0 | 0 | 0 | 0 |
| relation/4495683 | 0 | 0 | 0 | 0 | 0 | 0 |
| way/100704738 | 0 | 0 | 0 | 0 | 0 | 0 |
| way/198082036 | 0 | 3 | 0 | 0 | 0 | 0 |
| way/198082054 | 0 | 4 | 0 | 0 | 0 | 0 |
| way/232618736 | 0 | 4 | 0 | 0 | 0 | 0 |
| way/277649994 | 0 | 0 | 0 | 0 | 4 | 0 |
| way/287496591 | 0 | 2 | 0 | 0 | 0 | 0 |
| way/287696584 | 0 | 3 | 0 | 0 | 0 | 0 |
| way/287938551 | 0 | 1 | 0 | 0 | 0 | 0 |
| way/287939448 | 0 | 2 | 0 | 0 | 0 | 0 |
| way/288600848 | 0 | 0 | 0 | 0 | 0 | 0 |
| way/289364388 | 0 | 2 | 0 | 0 | 0 | 0 |
| way/289387273 | 2 | 2 | 0 | 0 | 0 | 0 |
| way/289387274 | 0 | 3 | 0 | 0 | 0 | 0 |
| way/289387277 | 0 | 4 | 0 | 0 | 0 | 0 |
| way/289387278 | 0 | 5 | 0 | 0 | 0 | 0 |
| way/289692620 | 0 | 4 | 0 | 0 | 0 | 0 |
| way/289979829 | 0 | 0 | 0 | 0 | 3 | 0 |
| way/290026256 | 0 | 0 | 0 | 0 | 0 | 0 |
| way/290820839 | 0 | 2 | 0 | 0 | 0 | 0 |

Homes in sample: 25. Totals: junction 7 / interior-or-wing end 10 / not better 43, expected 7 / 5 / 8.

## The 3 homes that fail a check

- ES-MAD-BERRUGUETE way/435398515: C10 on 3 of 3 storeys
- GB-LDN-STDUNSTANS way/409624879: C10 on 4 of 4 storeys
- IT-BOL-GALVANI2 28721: C11+C12 on 4 of 6 storeys

