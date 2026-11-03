# Rule-book audit, T02 (2026-09-30)

Plan: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-rulebook-change-2026-09-30.md`, T02. Read-only audit; no code, no EnergyPlus. Paths are relative to the repo root unless they start with `rules/` (= `docs/docs_ACTIVE/europeanLocations/rules/`) or `plans3D/` (= `docs/docs_ACTIVE/europeanLocations/plans3D/`). Abbreviations: G = `rules/RULES_dwelling_layout_groups_nocore_2026-09-03.html`, S = `rules/RULES_dwelling_layout_scheme_nocore_2026-09-03.html`, X = `rules/EXAMPLE_dwelling_layout_validation_nocore_2026-09-03.md`, E = `openubem/geometry/european_nocore.py`, B = `scripts/eu21/07_nocore_tests.py`, V = `scripts/eu21/08_district_viewer.py`, F = `scripts/eu21/04_group_tests.py`. `rules/archive/` holds 0 files that mention `C11` or `MAX_FLAT_ASPECT`: superseded, not audited further.

## 1. Every threshold in docs, bench and engine

| Threshold | Docs (file:line) | Bench B | Engine E | Match |
|---|---|---|---|---|
| C11 aspect 2.5 (`MAX_FLAT_ASPECT`) | G:196, :278, :282, :328-329, :335-336, :339; S:159, :160, :191, :200, :204, :206, :217; X:58, :72, :83, :113 | :1668 def; :1670-1671 status text; :1987-1989 sheet text | :1732 def; :489, :804, :1184, :1874, :2253 use | value equal (2.5) |
| C12 spread 0.50 (`MIN_SPREAD`) | none in G, S, X, `RULES_context_...md` | :1685 def; :1822 use | :1744 def; :1881 use | code only, docs silent (FINDING 272) |
| C13 bent walls = 0 | none | none | :1884 | engine only |
| C11 and C12 waived at k <= 1 (D-EU-93) | none in G, S, X | :1672 (status text); :1122, :1812, :1819 | :1184, :1871-1872, :1878-1879 | code only |
| C6 facade contact >= 2.50 m | G:284-286, :317-318; S:197; X:71 | :411, :758, :1117, :1806 | :485, :824, :1179, :1865 | equal; F:358 holds a third copy |
| C10 pinch <= 0.10 m2 | G:275-276; S:198; X:72 | :414, :1120, :1138, :1159, :1809 | :487, :1182, :1200, :1221, :1868 | equal |
| C5 <= 40 points per zone | G:291; S:196; X:70-71 | :404, :1114, :1802 | :480, :1176, :1861 | equal |
| C4 overlap < 0.02 m2 | G:290; S:196; X:70 | :1791 | :1850 | equal |
| C1 coverage 0.999..1.001 | G:266; X:69 | :1109 | :1171 | equal |
| C3 flats == n | G:294 | `run_checks` | `run_checks` | equal |
| "seven checks" wording | G:190, :255; S:159, :192; X:68, :112 | V:46 `CHECK_IDS` = C1 C3 C4 C5 C6 C10 C11 | :1888 verdict = same seven | equal; C12 and C13 are the unwritten 8th and 9th |
| Calibration statement "81 of 550 FAIL", "PASS 469" | G:196, :340; S:159; X:113 | :1615, :1649 comments (81) | :1679, :1713 comments (81) | equal; 550 plates of 2026-09-03, not the 4,171 homes |
| Sheet text "at most N times as long" | X:58; S:191 | :1989 `{MAX_FLAT_ASPECT:.0f}` prints "2" | none | MISMATCH: delivered sheets say "2 times" while the limit is 2.5 |
| Viewer label | G:335-341, S:203-207, B:1727 call 2.5 "set to the strictest rung" | none | none | V:427 says "not frozen (D-EU-86 clause 2, FINDING 242)"; wording differs |
| Viewer refusal text for k > 12 | rules docs have no refusal path (G:384, S:200-202) | none | none | V:165-174 `REFUSED_K_GT_12` says "failed the seven checks (D-EU-92)" |
| Test pin | none | none | none | `tests/test_eu_recut_95pct_2026_09_08.py`:94 `assert MAX_FLAT_ASPECT == 2.5` |

Plan section 5 line list, confirmed line by line: G :282 :335-336 :339 :340; S :159 :160 :204 :206 :217; X :68-72 :82-83 :112-113; B :1668-1671 :1685 :1987-1989; V :427; test :94. Also confirmed: section 5 item 2 "seven checks" at G :255, S :192, X :68. Missed by the plan, added here: G:196, :278, :328-329; S:191, :200; X:58; B:2112 (`MAX_FLAT_ASPECT_STATUS` printed in every sheet header); V:883 (value written into every plans3D JSON); F:358 (third C6 literal).

Count line: 16 threshold rows; 5 differences (C12 absent from the docs, C13 absent, the k <= 1 waiver absent, sheet text prints 2 for 2.5, viewer label wording); 0 numeric mismatches between docs, bench and engine (2.5, 0.50, 2.50 m, 0.10 m2, 40, 0.02 m2 all equal). E and B are two independent copies of the cutter (E mtime 2026-09-29, B mtime 2026-09-07; B sha256 `1a1ea4b9e39c9295...` equals the `cutter_sha256` of all four r6 pages).

## 2. Every binding of `MAX_FLAT_ASPECT` and `MIN_SPREAD` (`grep -rn` over `openubem/`, `scripts/`, `tests/`)

| # | File:line | Name | Use | Binding |
|---:|---|---|---|---|
| 1 | E:1732 | MAX_FLAT_ASPECT | definition | module global |
| 2 | E:489 | MAX_FLAT_ASPECT | `_accept_merged` compare | reads module global at call time |
| 3 | E:804 | MAX_FLAT_ASPECT | `worst_before <= ...` in the pair-merge repair | reads module global at call time |
| 4 | E:1184 | MAX_FLAT_ASPECT | `_plate_score` `c11_ok` | reads module global at call time |
| 5 | E:1874 | MAX_FLAT_ASPECT | `run_checks` C11 | reads module global at call time |
| 6 | E:2253 | MAX_FLAT_ASPECT | `_flats_to_fix` | reads module global at call time |
| 7 | E:1744 | MIN_SPREAD | definition | module global |
| 8 | E:1881 | MIN_SPREAD | `run_checks` C12 | reads module global at call time |
| 9 | B:1668 | MAX_FLAT_ASPECT | definition | module global of the bench (own copy, not E's) |
| 10 | B:417 | MAX_FLAT_ASPECT | merge accept | reads module global at call time |
| 11 | B:738 | MAX_FLAT_ASPECT | pair-merge repair | reads module global at call time |
| 12 | B:1122 | MAX_FLAT_ASPECT | `_plate_score` | reads module global at call time |
| 13 | B:1815 | MAX_FLAT_ASPECT | `run_checks` C11 | reads module global at call time |
| 14 | B:1670-1671 | MAX_FLAT_ASPECT_STATUS | string literal with "2.5" typed in | copies at import (hard-coded text, never follows the constant) |
| 15 | B:1987, :1989 | MAX_FLAT_ASPECT | f-strings inside module-level list `CHECK_META` (B:1972) | copies at import |
| 16 | B:1685 | MIN_SPREAD | definition | module global of the bench |
| 17 | B:1822 | MIN_SPREAD | `run_checks` C12 | reads module global at call time |
| 18 | V:427 | `M07.MAX_FLAT_ASPECT` | HTML f-string inside `build_html` (V:326) | reads attribute at call time |
| 19 | V:883 | `M07.MAX_FLAT_ASPECT` | written into the page JSON | reads attribute at call time |
| 20 | `tests/test_eu21_area_balance.py`:52 | `m07.MIN_SPREAD` | assert | reads attribute at call time |
| 21 | `tests/test_eu_recut_95pct_2026_09_08.py`:12 | MAX_FLAT_ASPECT | `from ...european_nocore import` | copies at import |
| 22 | `tests/test_eu_recut_95pct_2026_09_08.py`:94 | MAX_FLAT_ASPECT | assert on the imported copy | copies at import |

Also relevant: B is loaded as a fresh module by four scripts through `importlib` (V:37, `scripts/eu21/09_engine_parity.py`:150, `10_engine_census.py`:115, `11_interzone_diagnostics.py`:126); each load is its own copy, so setting `M07.MAX_FLAT_ASPECT` in one process changes only that copy and never E. `european_residential.py`:24 imports only `cut_storey_nocore` and `improve_cut_nocore` and holds no binding. No function has a default argument bound to either name. Docstring or comment mentions (not bindings): E:766, B:700, B:2481.

Count line: 22 bindings, 4 copies at import (rows 14, 15, 21, 22), 4 definitions (rows 1, 7, 9, 16), 14 reads at call time (rows 2-6, 8, 10-13, 17-20).

## 3. How loads are set per zone

Two builders exist. The plan named the first; the European campaign uses the second.

| Load | Builder `openubem/idf/builder.py` (plan starting point) | European campaign `scripts/run_eu_s2_campaign.py` | Verdict |
|---|---|---|---|
| People | builder.py:355 `people_per_m2 = 1/occupant_m2_per_person`; :410 `Number_of_People = people_per_m2 * floor_area_m2`; :439 `People_per_Floor_Area` | none emitted (`openubem/idf/european_controls.py`:62-75 writes no PEOPLE; `openubem/semantic/european_schedules.py`:100 "never creates a People object") | area-based |
| Lighting | builder.py:421 `Lighting_Level = lighting_w_m2 * floor_area_m2`; :449 `Watts_per_Zone_Floor_Area` | none emitted | area-based |
| Equipment / internal gain | builder.py:432 `Design_Level = equipment_w_m2 * floor_area_m2`; :458 `Watts_per_Zone_Floor_Area` | `european_controls.py`:62-75 `Power_per_Zone_Floor_Area = phi_int_w_m2`, replaced by `european_schedules.py`:126-138 `Power_per_Zone_Floor_Area = 1.0` W/m2 times an hourly file (run_eu_s2_campaign.py:1298-1316), one per zone, same series in every zone | area-based |
| Space-type weighted (room_layout zones only) | builder.py:185-213 `normalized_space_loads`: `total_people = a_tot/occ_m2_per_person`, split by zone area, sums to the archetype total | not used | area-based |
| DHW | `openubem/idf/dhw.py`:88-98 `peak_flow = peak_flow_l_h_m2 * total_area`; one heater and one WaterUse for the whole building in `zones[0]` | not emitted (`assign_dhw` is called only from builder.py:700) | area-based, building total |
| Infiltration / ventilation | builder.py:338-343 `Flow/ExteriorWallArea` per zone x `infiltration_m3_s_m2` | `european_controls.py`:57-60 `AirChanges/Hour`, `ach = (use + infiltration) * f_red` (:8-22), air volume = area x height; the only `Flow/Area` object (run_eu_s2_campaign.py:1279-1281) is for unconditioned circulation zones, which the no-core regime never has | area-based (European); exterior-wall-area-based (builder) |
| Internal mass | none | run_eu_s2_campaign.py:1286-1287 `add_european_internal_mass(idf, name, zone floor area, c_m)`; `openubem/idf/european_physics.py`:57-70 capacity = `c_m * A_floor` | area-based |

Verdict per load: people, lighting, equipment and internal gain, DHW, infiltration and ventilation, and internal mass are all **area-based**. **None is per-zone count and none is per-dwelling count**: the load code never reads `dwellings`, `n_units` or `units_per_floor`. Cutting a floor into more or fewer zones of the same total floor area leaves the summed load unchanged; energy can differ only through geometry (interior walls, interzone coupling), which the model already varies. Proven for the load objects only: this audit ran no simulation.

Count line: 7 load rows, 7 area-based, 0 per-zone count, 0 per-dwelling count.

## 4. The 53 U1 homes

Population: baseline `division_status.csv` U1 = 209. After the 286 shipped homes take their T05 class (`scratch/t05/gate_candidates.csv` `new_cls`; the 11 dropped stems keep their old class: 9 with `state` same_class_same_sha, `way/391276770` worse, `way/400445219`), U1 = 53. Cause source: `scratch/u1h_result.csv` covers 49 of the 53 (`reroute_reason`, `diag`, `reroute_mismatched`, `reroute_near_dup_surface`). The other 4 (Madrid `way/400445219`, `way/428478249`, `way/434878289`, London `way/1054785381`) are the T02b homes rerouted again in the T05 build and are not in `u1h_result.csv`. Surface type is read from the surface names in `reroute_mismatched` and `reroute_near_dup_surface`: every one names `Ceiling`, `Floor` or `Roof`, none names a `Wall`. "Nothing across" = the `diag` carries `remainder_area=..._unpaired=...` (a remainder with no partner surface). Reroute reasons in `u1h_result.csv`: `interzone_vertex_mismatch` 47, `near_duplicate_vertex` 2, equal to the T04h log (49 rerouted, 47 + 2). Directory for all `scratch/` paths: `openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/`.

| Group (plan wording) | ES-MAD | FR-LYO | GB-LDN | IT-BOL | Total |
|---|---:|---:|---:|---:|---:|
| wall with nothing across | 0 | 0 | 0 | 0 | 0 |
| floor/ceiling with nothing across | 2 | 1 | 1 | 6 | 10 |
| other: floor/ceiling partner present, outline does not match | 13 | 3 | 3 | 20 | 39 |
| other: not in u1h_result (rerouted again in T05) | 3 | 0 | 1 | 0 | 4 |
| all U1 after T05 (final) | 18 | 4 | 5 | 26 | 53 |

| # | district | building_id | stem | group | reroute reason | pairs still skipped | first diag |
|---:|---|---|---|---|---|---:|---|
| 1 | ES-MAD-BERRUGUETE | way/287356953 | 5f513531b21ddb1d | floor/ceiling with nothing across | interzone_vertex_mismatch | 2 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 2 | ES-MAD-BERRUGUETE | way/289510893 | 73621377166b8b8f | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 3 | ES-MAD-BERRUGUETE | way/289692623 | ef97f87e67e23829 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 4 | ES-MAD-BERRUGUETE | way/290653352 | f9017f97b1d8b410 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 5 | ES-MAD-BERRUGUETE | way/293591511 | 1186a26f4090e061 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 6 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 6 | ES-MAD-BERRUGUETE | way/310738150 | ef851a3dbfb09d9a | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 7 | ES-MAD-BERRUGUETE | way/310738153 | d0787f31dc827e89 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 10 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 8 | ES-MAD-BERRUGUETE | way/311162663 | f7ba4d676aa8ad34 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 9 | ES-MAD-BERRUGUETE | way/322742258 | 853c058128b3eff7 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 10 | ES-MAD-BERRUGUETE | way/380242658 | 34e9e5f28b9e923e | floor/ceiling with nothing across | interzone_vertex_mismatch | 2 | 2 surfaces: remainder_area=47.40_unpaired=47.40_pieces=1 |
| 11 | ES-MAD-BERRUGUETE | way/400445219 | 45c2472a33c88041 | other: not in u1h_result (rerouted again in the T05 build) | not recorded in u1h_result.csv |  |  |
| 12 | ES-MAD-BERRUGUETE | way/428478249 | 37173b8828a9dd97 | other: not in u1h_result (rerouted again in the T05 build) | not recorded in u1h_result.csv |  |  |
| 13 | ES-MAD-BERRUGUETE | way/432864978 | e74c5297f3cfebd3 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 5 surfaces: g5_covers=True_hosts=False_sameNormal=False |
| 14 | ES-MAD-BERRUGUETE | way/433014842 | 98827ae3c96ac1d0 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 15 | ES-MAD-BERRUGUETE | way/434878289 | 8b1bec54b375e9dc | other: not in u1h_result (rerouted again in the T05 build) | not recorded in u1h_result.csv |  |  |
| 16 | ES-MAD-BERRUGUETE | way/435212755 | 7036be961de23509 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 17 | ES-MAD-BERRUGUETE | way/942352877 | 03584e90f2394ee2 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 18 | ES-MAD-BERRUGUETE | way/948836434 | 28e7ea34024d49eb | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 19 | FR-LYO-HAUTCOEURPENTES | BATIMENT0000000240879983_part0 | 560ea001cad65113 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 20 | FR-LYO-HAUTCOEURPENTES | BATIMENT0000000240880244_part0 | a77225fbd2ff3aa9 | other: floor/ceiling partner present, outline does not match | near_duplicate_vertex | 7 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 21 | FR-LYO-HAUTCOEURPENTES | BATIMENT0000000240881099_part0 | 53918695f4ea8272 | floor/ceiling with nothing across | interzone_vertex_mismatch | 3 | 2 surfaces: remainder_area=29.87_unpaired=29.87_pieces=1 |
| 22 | FR-LYO-HAUTCOEURPENTES | BATIMENT0000000240881558_part0 | 698a8fc253c56007 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 23 | GB-LDN-STDUNSTANS | way/1054785381 | 96664f92acdf04e8 | other: not in u1h_result (rerouted again in the T05 build) | not recorded in u1h_result.csv |  |  |
| 24 | GB-LDN-STDUNSTANS | way/182927520 | a68978b0f2d6264f | floor/ceiling with nothing across | interzone_vertex_mismatch | 2 | 2 surfaces: remainder_area=227.37_unpaired=227.37_pieces=1 |
| 25 | GB-LDN-STDUNSTANS | way/393614546 | ae0905443cbb00a3 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 4 surfaces: g4_covers=True_hosts=False_sameNormal=True |
| 26 | GB-LDN-STDUNSTANS | way/394093226 | 577b1a57e53741d9 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 1 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 27 | GB-LDN-STDUNSTANS | way/395632424 | b252db3f9c37aa60 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 28 | IT-BOL-GALVANI2 | 28527 | 027f230632b64c16 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 29 | IT-BOL-GALVANI2 | 28749 | 862211dd1557cf0e | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 30 | IT-BOL-GALVANI2 | 28968 | ba6960bfea4d1476 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 31 | IT-BOL-GALVANI2 | 29094 | cba1b3d372058eee | floor/ceiling with nothing across | interzone_vertex_mismatch | 1 | 2 surfaces: remainder_area=139.57_unpaired=139.57_pieces=1 |
| 32 | IT-BOL-GALVANI2 | 29180 | 718c4df3ae194c98 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 1 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 33 | IT-BOL-GALVANI2 | 29228 | 8e3d20ee6eeb2ab8 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 34 | IT-BOL-GALVANI2 | 29466 | d9b0b602eafb8123 | other: floor/ceiling partner present, outline does not match | near_duplicate_vertex | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=True |
| 35 | IT-BOL-GALVANI2 | 29788 | 6354361f54aa3eb0 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 36 | IT-BOL-GALVANI2 | 30037 | 2d7af2d491812667 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 37 | IT-BOL-GALVANI2 | 30139 | 9e722a31fb64e445 | floor/ceiling with nothing across | interzone_vertex_mismatch | 1 | 2 surfaces: remainder_area=71.27_unpaired=71.27_pieces=1 |
| 38 | IT-BOL-GALVANI2 | 30240 | ea133efe99012bb9 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 39 | IT-BOL-GALVANI2 | 30912 | aa59861d3a4c6a89 | floor/ceiling with nothing across | interzone_vertex_mismatch | 8 | 2 surfaces: remainder_area=19.77_unpaired=19.77_pieces=1 |
| 40 | IT-BOL-GALVANI2 | 31016 | 47e5fcc0e0fc75ab | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 1 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 41 | IT-BOL-GALVANI2 | 31035 | d1fd4e1a34f0d97e | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 42 | IT-BOL-GALVANI2 | 31500 | befd5e66ee5854dd | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 5 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=True |
| 43 | IT-BOL-GALVANI2 | 31773 | 6cb9199127e3e12f | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 44 | IT-BOL-GALVANI2 | 31774 | 9fcdbb49f7a6551f | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 1 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 45 | IT-BOL-GALVANI2 | 32211 | 34b7b354541d259f | floor/ceiling with nothing across | interzone_vertex_mismatch | 3 | 2 surfaces: remainder_area=230.12_unpaired=230.12_pieces=1 |
| 46 | IT-BOL-GALVANI2 | 32453 | 151aeb5d3fe4f992 | floor/ceiling with nothing across | interzone_vertex_mismatch | 3 | 2 surfaces: remainder_area=9.22_unpaired=9.22_pieces=1 |
| 47 | IT-BOL-GALVANI2 | 32493 | 160d50edd30e35e9 | floor/ceiling with nothing across | interzone_vertex_mismatch | 2 | 2 surfaces: remainder_area=17.81_unpaired=17.81_pieces=1 |
| 48 | IT-BOL-GALVANI2 | 32556 | 6c5d01e34b186112 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 49 | IT-BOL-GALVANI2 | 32662 | 39bd947c565d5ba1 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 50 | IT-BOL-GALVANI2 | 32668 | 83afcb5cb353a27c | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 51 | IT-BOL-GALVANI2 | 33063 | 1509c02db702054f | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 2 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 52 | IT-BOL-GALVANI2 | 33260 | 8dc0914bdda35d54 | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 3 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |
| 53 | IT-BOL-GALVANI2 | 33354 | 13a87087effb0eef | other: floor/ceiling partner present, outline does not match | interzone_vertex_mismatch | 4 | 3 surfaces: g3_covers=True_hosts=False_sameNormal=False |

Count line: 53 of 53 classified (0 wall, 10 floor/ceiling with nothing across, 43 other: 39 with a partner whose outline does not match and 4 not recorded in `u1h_result.csv`).

## 5. `plans3D` and `rules/tests`

| Page or folder | Generator | Input JSON | Tag / build | Reflects today's models? |
|---|---|---|---|---|
| `plans3D/PLANS_ES-MAD-BERRUGUETE_nocore_2026-09-07_r6.html` | V:800 (`main` V:789) | `openubem/outputs/eu_evidence/EU-21/district_plans/ES-MAD-BERRUGUETE_nocore_2026-09-07_r6.json`, built 2026-09-07T13:44Z, 1,194 plates | `2026-09-07_r6`, `max_flat_aspect` 2.5, cutter sha `1a1ea4b9e39c9295...` | no: 1,194 plates of the 2026-09-07 population; fleet is 1,187 after the 2026-09-08 re-cut |
| `plans3D/PLANS_FR-LYO-HAUTCOEURPENTES_nocore_2026-09-07_r6.html` | V:800 | `.../FR-LYO-HAUTCOEURPENTES_nocore_2026-09-07_r6.json`, 2026-09-07T13:36Z, 530 plates | same | no: 530 versus fleet 529 |
| `plans3D/PLANS_GB-LDN-STDUNSTANS_nocore_2026-09-07_r6.html` | V:800 | `.../GB-LDN-STDUNSTANS_nocore_2026-09-07_r6.json`, 2026-09-07T13:36Z, 1,242 plates | same | no: 1,242 versus fleet 1,240 |
| `plans3D/PLANS_IT-BOL-GALVANI2_nocore_2026-09-07_r6.html` | V:800 | `.../IT-BOL-GALVANI2_nocore_2026-09-07_r6.json`, 2026-09-07T13:42Z, 1,220 plates | same | no: 1,220 versus fleet 1,215 |
| `plans3D/index.html` (2026-09-03 19:39) | none named in the file | none | text says "Active build `2026-09-03_r5`", 2,529 of 2,544 drawn, 2,353 passing | no: describes r5, not r6 |
| `rules/tests/TEST_01..05_*_nocore_2026-09-03_r2.html` (5 files) | B `--test N` (B:2110, :2160) | `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N_nocore.json` (N = 1..5, written 2026-09-03 15:24-15:26) | 2026-09-03, bench before its 2026-09-07 edit (C12 and D-EU-107 came after) | no: plates of the 2026-09-03 test set, not the 4,171 homes; sheets carry "2 times as long" (section 1) |

Page plate counts are `manifest_total` from each JSON `summary` (`drawn` differs). Each JSON `cutter_sha256` equals the current B sha256, so B is unchanged since the r6 build; E changed on 2026-09-29.

Broken links in `plans3D/index.html`: 4 of 20 local links, all "r5" (`PLANS_ES-MAD-BERRUGUETE_nocore_2026-09-03_r5.html`, `PLANS_FR-LYO-HAUTCOEURPENTES_nocore_2026-09-03_r5.html`, `PLANS_GB-LDN-STDUNSTANS_nocore_2026-09-03_r5.html`, `PLANS_IT-BOL-GALVANI2_nocore_2026-09-03_r5.html`, index lines 50-53). Those four files exist only under `plans3D/archive/`. The index has 0 links to the four r6 pages.

Count line: 10 files audited (4 r6 pages, 1 index, 5 test sheets), 0 of 10 reflect today's models, 4 broken links of 20 local links.
