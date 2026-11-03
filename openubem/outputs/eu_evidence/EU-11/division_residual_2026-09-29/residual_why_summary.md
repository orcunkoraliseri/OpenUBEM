# T04c residual why-summary (2026-09-29)

Source: `residual_why_geometry.csv` (1868 storey rows, 390 of 390 buildings), `residual_why_pairs.csv` (379 skipped groups, 84 of 88 buildings have at least one). Populations from `division_after_2026-09-29.csv`.

Verdict rule notes: (1) a storey the chosen cut already passes is labelled `storey_ok` and is not counted below; (2) `A_pass_exists_not_chosen` is tested on the checks the chosen cut fails: all gated checks C1 C3 C4 C5 C6 C10 C11 when the chosen cut fails any of them, otherwise gates plus C12; (3) `best_*` are taken over candidates with the right flat count and coverage, and `best_spread` over those that also pass all gated checks. Literal `n_pass_all_gates > 0` alone would flag every V2 storey.

## Storey rows by verdict and after class (failing storey rows only, 1336 of 1868 rows)

verdict                        B_rule_impossible  C_near_miss  D_cutter_lacks_move  E_far
after_class                                                                              
U3_cut_breaks_hard_rule_C4_C5                  0           24                  225     12
U4_other_box                                   0            2                    1      0
V1_divided_shape_rule_broken                  31          466                    0    341
V2_divided_unbalanced                          0           81                    0    153

## Storey rows by verdict, after class and district

verdict                                               B_rule_impossible  C_near_miss  D_cutter_lacks_move  E_far
after_class                   district                                                                          
U3_cut_breaks_hard_rule_C4_C5 ES-MAD-BERRUGUETE                       0            2                   11      3
                              FR-LYO-HAUTCOEURPENTES                  0            5                    7      0
                              IT-BOL-GALVANI2                         0           17                  207      9
U4_other_box                  IT-BOL-GALVANI2                         0            2                    1      0
V1_divided_shape_rule_broken  ES-MAD-BERRUGUETE                       6          130                    0     37
                              FR-LYO-HAUTCOEURPENTES                  5           66                    0     15
                              GB-LDN-STDUNSTANS                      20           36                    0     51
                              IT-BOL-GALVANI2                         0          234                    0    238
V2_divided_unbalanced         ES-MAD-BERRUGUETE                       0           23                    0     46
                              FR-LYO-HAUTCOEURPENTES                  0            5                    0      2
                              GB-LDN-STDUNSTANS                       0           15                    0      4
                              IT-BOL-GALVANI2                         0           38                    0    101

## Buildings by worst failing-storey verdict (order B, E, D, C, A) and after class

verdict                        B_rule_impossible  C_near_miss  D_cutter_lacks_move  E_far  no_failing_storey
after_class                                                                                                 
U3_cut_breaks_hard_rule_C4_C5                  0            0                   39     10                  0
U4_other_box                                   0            0                    1      0                  0
V1_divided_shape_rule_broken                  13          118                    0    111                  0
V2_divided_unbalanced                          0           27                    0     55                 16

Building totals: U3_cut_breaks_hard_rule_C4_C5 49, U4_other_box 1, V1_divided_shape_rule_broken 242, V2_divided_unbalanced 98 (390 of 390).

## Buildings by worst verdict, after class and district

verdict                                               B_rule_impossible  C_near_miss  D_cutter_lacks_move  E_far  no_failing_storey
after_class                   district                                                                                             
U3_cut_breaks_hard_rule_C4_C5 ES-MAD-BERRUGUETE                       0            0                    3      2                  0
                              FR-LYO-HAUTCOEURPENTES                  0            0                    4      0                  0
                              IT-BOL-GALVANI2                         0            0                   32      8                  0
U4_other_box                  IT-BOL-GALVANI2                         0            0                    1      0                  0
V1_divided_shape_rule_broken  ES-MAD-BERRUGUETE                       3           38                    0     17                  0
                              FR-LYO-HAUTCOEURPENTES                  1           12                    0      4                  0
                              GB-LDN-STDUNSTANS                       9           14                    0     17                  0
                              IT-BOL-GALVANI2                         0           54                    0     73                  0
V2_divided_unbalanced         ES-MAD-BERRUGUETE                       0            8                    0     18                  7
                              FR-LYO-HAUTCOEURPENTES                  0            0                    0      2                  3
                              GB-LDN-STDUNSTANS                       0            6                    0      2                  1
                              IT-BOL-GALVANI2                         0           13                    0     33                  5

## A_pass_exists_not_chosen

0 storey rows (0 of 1336 failing rows). Literal `n_pass_all_gates > 0` storey rows, all on storeys the chosen cut already passes: 780.

## Skipped paired-surface groups (88 lost-cut homes)

verdict                 degenerate_ring  one_side_larger  same_polygon_extra_vertex
district                                                                           
ES-MAD-BERRUGUETE                     0               50                         85
FR-LYO-HAUTCOEURPENTES                4               18                         53
GB-LDN-STDUNSTANS                     0                8                         22
IT-BOL-GALVANI2                       0               84                         55

Total 379 of 379 groups; 84 of 88 buildings carry at least one, 4 of 88 carry none (rerouted for a reason other than a coverage skip).
