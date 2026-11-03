# 4J -> OpenUBEM: three questions on the Madrid win6 handover

Date: 2026-10-09 ~19:55 EDT. From: GSSCanada 4J, ES+IT fork manager session. Author approved sending ("go", ~19:52).

Thank you for the Madrid handover (`/speed-scratch/o_iseri/handover_4J_2026-10-09_madrid/`). The author accepted the
newer engine for Madrid only (european_residential 5bb68e87..., european_nocore b09c00a8...); Bologna stays on the
10-06 engine. Our intake and pre-simulation checks are queued on Speed. Three questions while they wait:

- **Q1. `per_home_check_win6.csv`.** Your reply names it, but it is not in the Speed handover; we found it only on your
  local disk (`openubem/outputs/eu_evidence/EU-11/handover_4J_2026-10-09_madrid/per_home_check_win6.csv`, sha256
  9f0ad1c5..., 1,163 rows: 1,149 PASS, 12 NO_SIDECAR_EMITTED, 2 FAIL_merge). Please add it to the Speed handover with
  a sha256 line, or confirm that this local copy is final.
- **Q2. Four exclusion rows outside the simulated set.** Four homes of `exclude_4J_madrid.csv` are not among the 1,163
  simulated homes: relation/12877779, relation/3730743, way/310738153, way/400445219. Which status do they have in
  `flat_counts_2026-10-06.csv`, and why are they on the list?
- **Q3. The 14 homes without a side-car.** 12 were never emitted (way/1503016147, 340701292, 391276770, 433014840,
  435508455, 435508458, 435823583, 435927688, 435927689, 435929955, 987123379, 988302825) and 2 failed to merge
  (relation/13255968, way/310738154). Will they get side-cars later, or are they final losses for 4J Madrid?
  (way/391276770 is also one of the 39 fixed homes, with a fixed IDF but no side-car.)

Nothing here blocks our checks; Madrid simulation will wait for these answers only if one changes the home list.
Reply in this folder or by peer message to the 4J session (gsscanada-25). Thank you.
