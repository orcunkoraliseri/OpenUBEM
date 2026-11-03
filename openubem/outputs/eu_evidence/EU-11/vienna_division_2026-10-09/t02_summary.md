# T02V summary - Vienna dry run on the 88 left-out homes (2026-10-09)
Base: 448 of 536 correctly divided (83.6 %); target 509 (95 %). Source: `scratch/t02.py`, rows in `t02_dryrun.csv`, final ruleset, flat target for L3 = 81.0 m2 (10th percentile of passing homes, T01V).
Recovered = every floor passes the verdict and C12 and the home scores OK or V3. L2/L3 were scored only for homes L1 did not recover (L1 already costs 0 flats); 'same_as_L1' = L3 would use the same k, counted as not recovered. No_failing_floor_tag_only = delivered floors already pass; only the best-effort tag keeps them in V1.

- L1: recovered 43 of 88; projected 491 of 536 = 91.6 %; flats removed 0; of which tag-only 11; floors changed 81
- L2: recovered 8 of 88; projected 456 of 536 = 85.1 %; flats removed 22; of which tag-only 0; floors changed 22
- L3: recovered 3 of 88; projected 451 of 536 = 84.1 %; flats removed 8; of which tag-only 0; floors changed 8
- Any lever (cheapest per home): recovered 51 of 88; projected 499 of 536 = 93.1 %; flats removed 22; real recoveries (not tag-only) 40

L1 outcome by note: {'recovered_by_cut': 32, 'timeout_killed': 21, 'timeout': 20, 'no_failing_floor_tag_only': 11, 'no_failing_floor_class_U4': 2, 'no_failing_floor_class_U1': 1, 'no_candidate_passes': 1}
L2 outcome by note: {'timeout_killed': 18, 'timeout': 15, 'recovered_by_cut': 8, 'no_failing_floor_class_U4': 2, 'no_failing_floor_class_U1': 1, 'no_candidate_passes': 1}
L3 outcome by note: {'same_as_L1': 30, 'timeout': 9, 'recovered_by_cut': 3, 'no_failing_floor_class_U4': 2, 'no_failing_floor_class_U1': 1}
Homes that timed out (10 min) on at least one lever: 41; of those, timed out and not recovered by any lever: 33.
Not recovered by any lever: 37 (V1 33, U4 2, U1 1, V2 1).
Needed for 95 %: 61 homes; any-lever recovers 51 (does not reach the target).
