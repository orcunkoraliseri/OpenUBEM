# T01V summary - why the 88 fail, Vienna (2026-10-09)
Rows: 536 (OK+V3 448, V1 83, other 5: V2 2, U4 2, U1 1). Source: `scratch/t01.py`, final ruleset, rescoring each side-car floor with the engine's own checks.

Median [10th - 90th percentile], OK+V3 vs V1:
- mean flat m2: OK+V3 83.4 [81.0 - 103.8] | V1 83.6 [81.5 - 102.8]
- plate depth m: OK+V3 18.1 [13.4 - 24.8] | V1 22.5 [18.0 - 54.4]
- flats per floor (k_max): OK+V3 5.0 [3.0 - 7.0] | V1 6.0 [5.0 - 21.0]
- wings (analyse_sidecar): OK+V3 0.0 [0.0 - 1.0] | V1 0.0 [0.0 - 2.0]
- footprint m2: OK+V3 395.2 [234.5 - 569.9] | V1 522.4 [365.2 - 2050.2]
- storeys: OK+V3 4.0 [3.0 - 5.0] | V1 4.0 [4.0 - 5.0]
- Courtyard share: OK+V3 14.7 % | V1 56.6 %. Multi-part footprint: 7.1 % | 8.4 %.
- Share correctly divided by k_max: <=6 89 % (n=419), 7-10 82 % (n=85), 11-15 38 % (n=13), >15 6 % (n=16). By plate depth: <=14 95 % (n=66), 14-22 89 % (n=329), 22-32 76 % (n=117), >32 14 % (n=22).
Left-out by scheme (U4 has none): {'nocore_equal_area': 86}. By dwelling_count_source (prepared_buildings): {'area_imputed': 88} (all 536: {'area_imputed': 525, 'single': 11}). By type: {'MFH': 61, 'AB': 27}.
V1 failing checks (homes, any floor): {'C10': 68, 'C11': 15, 'C13': 41, 'C6': 1}. Failing storeys per V1 home: median 3; every storey fails in 47 % of V1 homes.
Left-out homes whose rescored floors all pass the verdict (16): reason below. For the 11 V1 ones the reason is the same: the generator marked the home best-effort (build-time failed check shown), and the scorer files any best-effort home as V1 even when the delivered zones rescore clean or fail only C13 (not in the verdict). The 2 V2, 2 U4 and 1 U1 are not floor-check failures (V2 fails the balance check C12 only, U4 is the box fallback, U1 was rerouted at IDF write).
- AT-VIE-5285188 (V1, AB, k_max 6.0, 6 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'none'.
- AT-VIE-5287120 (U1, MFH, k_max nan, 4 storeys): build-time fail 'none', outcome DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED, rescored fail list 'C13'.
- AT-VIE-5321721 (V1, AB, k_max 8.0, 5 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'C13'.
- AT-VIE-5340624 (V2, MFH, k_max 6.0, 4 storeys): build-time fail 'none', outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT, rescored fail list 'C12+C13'.
- AT-VIE-5361450 (U4, MFH, k_max nan, 4 storeys): build-time fail 'none', outcome FALLBACK_PENDING_LAYOUT, rescored fail list 'none'.
- AT-VIE-5373770 (V1, AB, k_max 19.0, 5 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'C13'.
- AT-VIE-5414021 (V2, MFH, k_max 19.0, 4 storeys): build-time fail 'none', outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT, rescored fail list 'C12+C13'.
- AT-VIE-5480926 (V1, MFH, k_max 6.0, 4 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'C13'.
- AT-VIE-5515635 (U4, MFH, k_max nan, 4 storeys): build-time fail 'none', outcome FALLBACK_PENDING_LAYOUT, rescored fail list 'none'.
- AT-VIE-5524323 (V1, MFH, k_max 8.0, 3 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'none'.
- AT-VIE-5525972 (V1, MFH, k_max 5.0, 4 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'none'.
- AT-VIE-5531376 (V1, MFH, k_max 4.0, 4 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'C13'.
- AT-VIE-5558424 (V1, MFH, k_max 7.0, 4 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'none'.
- AT-VIE-5559077 (V1, MFH, k_max 8.0, 4 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'C13'.
- AT-VIE-5584808 (V1, MFH, k_max 11.0, 4 storeys): build-time fail 'C11', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'C13'.
- AT-VIE-5707064 (V1, MFH, k_max 7.0, 4 storeys): build-time fail 'C10', outcome DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT, rescored fail list 'C13'.
- Non-V1 AT-VIE-5287120: U1_cut_lost_at_idf_write, failing floors 0, outcome DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED.
- Non-V1 AT-VIE-5340624: V2_divided_unbalanced, failing floors 0, outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT.
- Non-V1 AT-VIE-5361450: U4_other_box, failing floors 0, outcome FALLBACK_PENDING_LAYOUT.
- Non-V1 AT-VIE-5414021: V2_divided_unbalanced, failing floors 0, outcome DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT.
- Non-V1 AT-VIE-5515635: U4_other_box, failing floors 0, outcome FALLBACK_PENDING_LAYOUT.
