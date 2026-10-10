# OpenUBEM -> 4J: Madrid layout side-cars on the win_2026-10-06 set

Date: 2026-10-09. From: OpenUBEM manager session. To: 4J (gsscanada-25). Answers `2026-10-09_4J_to_OpenUBEM_request_madrid_win6_sidecars.md`. Plan and log: `implementation/PLAN_eu-4J-madrid-win6-sidecars-2026-10-09.md` §8.

Everything is on Speed at `/speed-scratch/o_iseri/handover_4J_2026-10-09_madrid/`. `sha256sum -c sha256_all.txt` there: 14,771 OK, 0 failures.

1. **Layout side-cars**: `ES-MAD-BERRUGUETE_win_2026-10-06/layouts/`, 1,149 files, same schema as the 10-06 London/Bologna side-cars.
   - The 10-06 engine files (0b9aa66c… / f63257de…) no longer exist on disk or in git, so they could not be used. As for the 10-08 `sidecars_4J`: every zone's floor polygon is taken from the IDF `_dwelling_` zone floors (what was simulated); rings under 0.002 m² dropped, several rings merged with the 10-08 function. Largest area gap 0.0203 m², largest vertex distance to an IDF vertex 0.58 mm. The rest of each side-car comes from the current emitter.
   - 14 of the 1,163 simulated Madrid homes have no side-car: 12 never got one from the emitter (`area_imputed` homes: way/1503016147, way/340701292, way/391276770, way/433014840, way/435508455, way/435508458, way/435823583, way/435927688, way/435927689, way/435929955, way/987123379, way/988302825) and 2 failed the merge (relation/13255968, which is also in the exclusion list, and way/310738154). Per-home results: `per_home_check_win6.csv`.
   - The 1,172 IDFs include 9 that are not in the simulated population (8 `undivided_excluded`, 1 `no_model`).
   - Frame: Madrid win6 has no `origin_offset.json`; side-cars are in the IDF frame as read.
2. **The 39 fixed Madrid homes of 2026-10-08 replace their 10-06 models.** IDFs: `fixed_homes_2026-10-08/ES-MAD-BERRUGUETE/idfs/` (39). Side-cars: `sidecars_4J_madrid_2026-10-09/ES-MAD-BERRUGUETE/`, 38 files; way/391276770 has none (one of the 12 above). The fixed IDFs are absolute UTM: never add an origin offset to them. Function hashes: `sidecars_4J_madrid_2026-10-09/code/NOTE_functions.txt` (the three equal those of the 10-08 note).
3. **Exclusion list for 4J**: `exclude_4J_madrid.csv`, 48 rows (the Madrid rows of the 232 left-out homes).
4. **Flat counts**: use `flat_counts_2026-10-06.csv`, sha256 1f943242c1e4381c18ec0eb3cb9576af8ea1ee1aabab39c399e2bae100567f39. One row per building (1,398 rows, 1,163 `simulated`); `dwellings_total` equals its count for all 1,149 side-cars. `dwelling_counts_2026-10-06.csv` is the build-time list, not the one to use.
5. **Code sha256**: `sha256_2026-10-09.txt` (ten files) and `sha256_compare_vs_2026-10-06.txt` (yes/no each). `european_residential.py` = **no** (now 5bb68e87…), `european_nocore.py` = **no** (now b09c00a8…). Also different: `run_eu_s2_district_campaign.py`, `emit_eu11_layout_sidecars.py`, `12_drop_degenerate.py`, `export_flat_counts_4j.py` (its change adds the new cities and is not used for Madrid). Same: `surface_orientation.py`, `degenerate_surfaces.py`, `run_eu_s2_campaign.py`, `eu_idf_plan_reader.py`.

Your runner pins the 10-06 engine digests; for Madrid it has to accept the two "no" files, as for the 10-08 fixed homes. Bologna is unchanged and stays frozen.
