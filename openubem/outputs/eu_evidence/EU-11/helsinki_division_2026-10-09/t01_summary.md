# T01 summary - why the 122 fail (2026-10-09)
Rows: 580 (OK+V3 458, V1 120, other 2: 1 U1, 1 U4). Source: `scratch/t01.py`, final ruleset, rescoring each side-car floor with the engine's own checks.

Median [10th - 90th percentile], OK+V3 vs V1:
- mean flat m2: OK+V3 74.3 [48.0 - 125.8] | V1 62.0 [41.0 - 103.1]
- plate depth m: OK+V3 16.6 [11.9 - 31.1] | V1 30.6 [18.0 - 40.5]
- flats per floor (k_max): OK+V3 7.0 [4.0 - 12.0] | V1 14.0 [9.0 - 20.2]
- wings (analyse_sidecar): OK+V3 0.0 [0.0 - 1.0] | V1 0.0 [0.0 - 2.0]
- footprint m2: OK+V3 506.0 [264.0 - 870.1] | V1 846.1 [467.4 - 1309.5]
- storeys: OK+V3 7.0 [4.0 - 8.0] | V1 6.0 [5.0 - 8.0]
- Courtyard share: OK+V3 0.9 % | V1 5.8 %. Multi-part footprint: 10.5 % | 6.7 %.
- Reading: V1 homes are bigger and deeper (median plate 30.6 m vs 16.6 m) and carry about twice the flats per floor (14 vs 7). Flat size is not the cause (62 vs 74 m2). Share correctly divided falls from 99 % at k<=6 to 27 % at k>15, and from 98 % at depth<=14 m to 46 % at depth>32 m.

V1 by scheme: {'nocore_equal_area': 120}. V1 by dwelling_count_source: {'observed': 120}. V1 by type: {'AB': 116, 'MFH': 4}.
- All 580 side-cars use one scheme (nocore_equal_area), and 578 of 580 dwelling counts are observed, not imputed (plan 5 says imputed: the total is observed, only the per-floor split is allocated).
V1 failing checks (homes, any floor): {'C10': 89, 'C11': 41, 'C12': 4, 'C13': 73, 'C6': 4}. Failing storeys per V1 home: median 5; every storey fails in 53 % of V1 homes.
- Check counts match the manager count exactly (C10 89, C13 73, C11 41, C12 4, C6 4). Rescored failing storeys match division_classes.csv for 579 of 580 homes (exception: U1 home 743555, rerouted).

The 9 V1 homes whose rescored floors all pass the verdict (6 have no failed check at all, 3 only C13, which is not part of the verdict):
Reason for all 9: the generator marked the home best-effort (failed check C10 at build time), and the scorer files any best-effort home as V1; rescoring the delivered zones finds C10 passing.
- FI-HEL-742973 (AB, k_max 15.0, 7 storeys): build-time fail C10, rescored fail list 'C13'.
- FI-HEL-744817 (AB, k_max 14.0, 6 storeys): build-time fail C10, rescored fail list 'none'.
- FI-HEL-744833 (AB, k_max 15.0, 6 storeys): build-time fail C10, rescored fail list 'none'.
- FI-HEL-744866 (AB, k_max 14.0, 6 storeys): build-time fail C10, rescored fail list 'none'.
- FI-HEL-749425 (AB, k_max 11.0, 6 storeys): build-time fail C10, rescored fail list 'none'.
- FI-HEL-749863 (AB, k_max 9.0, 6 storeys): build-time fail C10, rescored fail list 'C13'.
- FI-HEL-873291 (AB, k_max 11.0, 6 storeys): build-time fail C10, rescored fail list 'none'.
- FI-HEL-874113 (AB, k_max 7.0, 6 storeys): build-time fail C10, rescored fail list 'none'.
- FI-HEL-879945 (AB, k_max 7.0, 7 storeys): build-time fail C10, rescored fail list 'C13'.

Side finding (multi-part homes): 18 homes have ids ending _partN. Each part carries the WHOLE building's dwelling count and flats-per-floor (dwellings_used = building total on every part), so parts get oversized k: 10 of the 18 are V1, and 875288_part0..3 carry 39 flats per floor on plates of 363-816 m2 (9-21 m2 per flat).
