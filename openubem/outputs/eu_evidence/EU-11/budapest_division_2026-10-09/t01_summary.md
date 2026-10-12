# T01B summary - why the 196 fail, Budapest (2026-10-09)
Rows: 805 (OK+V3 609, V1 190, other 6: U4 3, V2 3). Source: `scratch/t01.py`, final ruleset, rescoring each side-car floor with the engine's own checks.

Median [10th - 90th percentile], OK+V3 vs V1:
- mean flat m2: OK+V3 66.2 [65.4 - 67.2] | V1 66.2 [65.6 - 66.7]
- plate depth m: OK+V3 20.3 [14.1 - 27.2] | V1 26.7 [19.5 - 38.5]
- flats per floor (k_max): OK+V3 9.0 [5.0 - 13.0] | V1 14.0 [9.9 - 23.0]
- wings (analyse_sidecar): OK+V3 0.0 [0.0 - 2.0] | V1 1.0 [0.0 - 3.0]
- footprint m2: OK+V3 573.5 [299.6 - 852.0] | V1 880.8 [608.0 - 1482.5]
- storeys: OK+V3 4.0 [3.0 - 6.0] | V1 4.0 [3.0 - 6.0]
- Courtyard share: OK+V3 40.2 % | V1 76.3 %. Multi-part footprint: 6.6 % | 2.6 %.
- Share correctly divided by k_max: <=6 100 % (n=131), 7-10 88 % (n=305), 11-15 69 % (n=276), >15 22 % (n=90). By plate depth: <=14 100 % (n=59), 14-22 87 % (n=357), 22-32 72 % (n=316), >32 16 % (n=70).
Left-out by scheme (U4 has none): {'nocore_equal_area': 193}. By dwelling_count_source (prepared_buildings): {'area_imputed': 196} (all 805: {'area_imputed': 805}). By type: {'AB': 194, 'MFH': 2}.
V1 failing checks (homes, any floor): {'C10': 137, 'C11': 92, 'C12': 3, 'C13': 122, 'C6': 2}. Failing storeys per V1 home: median 4; every storey fails in 53 % of V1 homes.
Left-out homes whose rescored floors all pass the verdict (7): 1 V1 and 6 non-V1. For the V1 ones the generator marked the home best-effort (build-time failed check shown) and the scorer files any best-effort home as V1 even when the delivered zones rescore clean or fail only C13 (not in the verdict). V2 fails the balance check C12 only, U4 is the box fallback.
- way/258731835 (U4, AB, k_max nan, 4 storeys): build-time fail 'none', outcome FALLBACK_PENDING_LAYOUT, rescored fail list 'none'.
- way/258718372 (V2, AB, k_max 14.0, 4 storeys): build-time fail 'none', outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT, rescored fail list 'C12'.
- relation/3460499 (U4, AB, k_max nan, 4 storeys): build-time fail 'none', outcome FALLBACK_PENDING_LAYOUT, rescored fail list 'none'.
- relation/3472801 (U4, AB, k_max nan, 4 storeys): build-time fail 'none', outcome FALLBACK_PENDING_LAYOUT, rescored fail list 'none'.
- relation/3474296 (V1, AB, k_max 9.0, 3 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'none'.
- relation/13791854 (V2, AB, k_max 15.0, 4 storeys): build-time fail 'none', outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT, rescored fail list 'C12+C13'.
- relation/3476119 (V2, AB, k_max 14.0, 5 storeys): build-time fail 'none', outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT, rescored fail list 'C12+C13'.
- Non-V1 way/258731835: U4_other_box, failing floors 0, outcome FALLBACK_PENDING_LAYOUT.
- Non-V1 way/258718372: V2_divided_unbalanced, failing floors 0, outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT.
- Non-V1 relation/3460499: U4_other_box, failing floors 0, outcome FALLBACK_PENDING_LAYOUT.
- Non-V1 relation/3472801: U4_other_box, failing floors 0, outcome FALLBACK_PENDING_LAYOUT.
- Non-V1 relation/13791854: V2_divided_unbalanced, failing floors 0, outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT.
- Non-V1 relation/3476119: V2_divided_unbalanced, failing floors 0, outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT.
