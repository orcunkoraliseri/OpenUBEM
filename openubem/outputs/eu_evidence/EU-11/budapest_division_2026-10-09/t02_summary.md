# T02B summary - Budapest dry run on the 196 left-out homes (2026-10-09)
Base: 609 of 805 correctly divided (75.7 %); target 765 (95 %). Source: `scratch/t02.py`, rows in `t02_dryrun.csv`, final ruleset, flat target for L3 = 65.4 m2 (10th percentile of passing homes, T01B).
Recovered = every floor passes the verdict and C12 and the home scores OK or V3. L2/L3 were scored only for homes L1 did not recover (L1 already costs 0 flats); 'same_as_L1' = L3 would use the same k, counted as not recovered. No_failing_floor_tag_only = delivered floors already pass; only the best-effort tag keeps them in V1.

- L1: recovered 51 of 196; projected 660 of 805 = 82.0 %; flats removed 0; of which tag-only 1; floors changed 123
- L2: recovered 0 of 196; projected 609 of 805 = 75.7 %; flats removed 0; of which tag-only 0; floors changed 0
- L3: recovered 0 of 196; projected 609 of 805 = 75.7 %; flats removed 0; of which tag-only 0; floors changed 0
- Any lever (cheapest per home): recovered 51 of 196; projected 660 of 805 = 82.0 %; flats removed 0; real recoveries (not tag-only) 50

L1 outcome by note: {'timeout': 106, 'recovered_by_cut': 50, 'timeout_killed': 36, 'no_failing_floor_class_U4': 3, 'no_failing_floor_tag_only': 1}
L2 outcome by note: {'no_failing_floor_class_U4': 3}
L3 outcome by note: {'no_failing_floor_class_U4': 3}
Homes that timed out (10 min) on at least one lever: 142; of those, timed out and not recovered by any lever: 142.
Not recovered by any lever: 145 (V1 141, U4 3, V2 1).
Needed for 95 %: 156 homes; any-lever recovers 51 (does not reach the target).
