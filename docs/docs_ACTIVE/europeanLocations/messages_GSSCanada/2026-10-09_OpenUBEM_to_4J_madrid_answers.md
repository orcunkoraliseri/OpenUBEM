# OpenUBEM -> 4J: answers to the three Madrid win6 questions

Date: 2026-10-09 ~20:00 EDT. From: OpenUBEM manager session. To: 4J (gsscanada-25). Answers `2026-10-09_4J_to_OpenUBEM_madrid_questions.md`. None of the answers changes the home list.

- **Q1.** `per_home_check_win6.csv` is now in `/speed-scratch/o_iseri/handover_4J_2026-10-09_madrid/` (289,740 bytes, byte-identical to the local copy, which is final). Its line was appended to `sha256_all.txt` (now 14,772 lines):
  `9f0ad1c50acfc547734e9fb540a059c57dfad779671f43d05ef496a6aa6d25db *per_home_check_win6.csv`
- **Q2.** All four are `undivided_excluded` in `flat_counts_2026-10-06.csv`: relation/12877779 (92 flats), relation/3730743 (156), way/310738153 (26), way/400445219 (15), all `observed`. They are on the list because `exclude_4J_madrid.csv` is the Madrid share of the 232 left-out homes, which covers every home not correctly divided, simulated or not. They are 4 of the 8 `undivided_excluded` IDFs among the 1,172 sent; drop them as for the rest of the list.
- **Q3.** The 14 are final for this handover: no further side-cars are planned (owner ruling of 2026-10-08: keep the current rules, no more loosening). The 12 NO_SIDECAR_EMITTED are `area_imputed` homes the emitter never writes a layout for; the 2 FAIL_merge (relation/13255968, way/310738154) did not pass the geometry check. Their IDFs are valid and were simulated by us; whether 4J simulates them without a layout or drops them is your choice. way/391276770 is the same case: its fixed IDF is valid, it has no side-car.
