# PLAN — EU re-cut to 95 %: best-effort shape tier (D-EU-111), neighbour imputation for the never-simulated (D-EU-112), vertex-bug second pass, one re-emission, one Speed wave

- **Slug:** `eu-recut-95pct-2026-09-08` · **Date:** 2026-09-08 · **Author:** director (manager session) · **Executor:** fresh Sonnet sessions, one per task range.
- **Design pointers (read-only, never edited):** `docs/docs_ACTIVE/europeanLocations/rules/*` (seven checks, frozen 2026-09-02), `BRIEF_european_locations_v5.md`, `STATE_european_locations_v5.md` §0/§8, the debug doc that motivates this plan `debugs/DEBUG_floor-division-gap-and-clean-pipeline_2026-09-08.md` (§3 three walls, §4 D-EU-111, §5 pipeline, §8 fleet scan).
- **Owner authorisation (2026-09-08, verbatim, one message, six replies):** *"ok, go for it."* (re-cut and re-simulate the 473) · *"ok, go for it."* (vertex-bug second pass) · *"ok, go for it. i accept D-EU-111."* · *"if possible, lets apply imputation and include these buildings inside the simulation clusters."* · *"please do it, it can be a guidance for us."* (the never-simulated list) · *"please do it."* (impute ages from neighbours, reversing `D-EU-101`'s no-imputation stance for the never-simulated).
- **Decisions this plan carries (allocated here, ledgered in STATE §8):**
  - **`D-EU-111`** — best-effort tier for the three *shape* checks `C6`/`C10`/`C11`: a cut that fails only those is emitted, tagged, and drawn with an amber badge; `C1`/`C3`/`C4`/`C5` still refuse; `MAX_FLAT_ASPECT = 2.5` and every check threshold unchanged.
  - **`D-EU-112`** — neighbour imputation for the never-simulated: a building excluded only for a missing construction period, storey count, dwelling count or typology inherits it from its prepared neighbours (touching → nearest within 30 m → district mode for its type), provenance-tagged `IMPUTED_NEIGHBOUR_*`, and enters the campaign. Supersedes the *"no general imputation"* half of `D-EU-101` for these 585 buildings only; the observed-first rule for every other building is untouched.
  - The vertex-bug second pass is `D-EU-109` work (already authorised end to end) continued; no new ID.
- **Next free after this plan:** `D-EU-113`, `FINDING 267` (this plan allocates `FINDING 267` for the wall-B measurement result in T03; nothing else).

---

## 1. What this plan delivers (plain words)

Today 3,128 of 3,601 simulated homes are cut into flats (86.9 %); 473 are one undivided box per floor; 585 more residential buildings were never simulated because a data field was missing. After this plan:

1. The 289 buildings the shape rules refused are cut anyway and honestly labelled "best effort" (`D-EU-111`).
2. The 184 buildings whose cut was thrown away by the near-duplicate-vertex bug are measured and, where the measurement allows, recovered (wall B second pass).
3. The 585 never-simulated buildings get their missing field from a neighbour, are labelled as imputed, and are simulated (`D-EU-112`).
4. Everything changed is re-emitted once, simulated once on Speed (director-only), harvested, restated, re-drawn in the four viewers with the amber badge, and re-exported as layout side-cars for GSSCanada — Lyon included (its side-cars were never emitted).

Expected end state, to be **measured, not assumed**: divided ≈ 3,450–3,550 of ≈ 4,170 simulated (≈ 83–85 % of the whole 4,186 stock; ≈ 96–98 % of the *previously* simulated 3,601). The population and the percentage are always quoted together.

---

## 2. Hard rules for the executor

1. **Model:** every executor session is Sonnet. Never plan, never propose alternatives; on ambiguity STOP and quote the conflicting lines.
2. **No cluster access.** Never run `ssh`, `scp`, `sbatch`, `srun`, `squeue`, `sacct`. Speed work (T06) is director-only. No EnergyPlus runs locally in this plan at all.
3. **Never run the four district preparations one after another.** T05 launches four `run_eu_s2_district_campaign.py` processes at once (one per district) and waits for all four. A serial loop is a defect.
4. **Python:** `C:/Users/o_iseri/Desktop/OpenUBEM/.venv/Scripts/python.exe` (bare `python` is not on PATH). Tests: `.venv/Scripts/python.exe -m pytest tests/<file> -q`.
5. **Never edit** root `main.py`, any OVERVIEW/DESIGN doc, `docs/docs_ACTIVE/europeanLocations/rules/*`, the seven check thresholds, `MAX_FLAT_ASPECT`, `RULED_GRID_MAX_DWELLINGS_PER_FLOOR`, `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`, `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG`, or the three `RING_VERTEX_REMOVAL_*` budgets (T03b may change a budget **only** if the director's CP-1 ruling names the new value).
6. **Never delete or regenerate a delivered tree.** New output goes to new dated folders (`*_recut_2026-09-08`, `*_merged_2026-09-08`, `*_layouts_2026-09-08b`). Existing `_final_2026-09-07`, `_delta_2026-09-07`, `_merged_2026-09-07` trees are read-only inputs.
7. **Read guard:** `grep -n` first, then a ranged read. Never read a whole file over 300 lines.
8. **Before debugging any error**, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`; after solving one, register it there (house format) before closing the task.
9. **Every count is measured and quoted as "N of M"**, never as a bare percentage. A gate quoted without its population is not a passed gate.
10. **Progress log** (§8): one entry per task, `#### TXX — <title> — completed YYYY-MM-DD`, with Artifacts / Deviations / Test status / Notes. Append only; never rewrite earlier entries.
11. `.png` / figures → `openubem/outputs/` (flat), never under `docs/`. No `.py` under `docs/`.
12. No code comments unless a line would be unreadable without one. No new scripts unless this plan names them.

---

## 3. File layout

| Path | Role in this plan |
|---|---|
| `openubem/geometry/european_residential.py` | `generate_european_nocore_storey_layout` (`:1338-1395`, the refusal at `:1373-1378`) — **T02 edits here**; `generate_european_building_dwelling_layout` (`:2645-2726`) — T02 propagates `fallback_reason_by_storey` |
| `openubem/geometry/european_nocore.py` | checks `C6`/`C10`/`C11` (`:1865-1885`), `MAX_FLAT_ASPECT = 2.5` (`:1732`) — **read-only** |
| `scripts/run_eu_s2_district_campaign.py` | `_geometry` (`:128-166`, outcome tokens), GB terrace inheritance (`:372-452`), IT census mapping (`:486-586`), `_mapped_rows` (`:589-…`), manifest row (`:700-710`), `IDF_ASSEMBLY_FAILED` catch (`:716`), CLI (`:750-753`) — **T01, T02, T04 edits here** |
| `scripts/run_eu_s2_campaign.py` | `_has_near_duplicate_vertex_surfaces` (`:94`), `_drop_redundant_ring_vertices` (`:149-250`), at-risk gate + reroute (`:680-718`) — T03 measures; T03b may edit per CP-1 |
| `openubem/semantic/european_archetype_mapping.py` | `derive_bdtopo_building_type` (`:195-214`), `map_observed_building_to_tabula` (`:217-…`) — T04 hooks imputed values in **before** this is called; the function itself is unchanged |
| `scripts/emit_eu11_layout_sidecars.py` | outcome branches (`:300-340`), CLI (`:570-590`) — T02 adds the best-effort branch; T07 re-emits all four districts |
| `scripts/generate_eu_3d_viewers.py` | badge CSS (`:94-98`), status HTML (`:439-471`), manifest selection (`:862-880`), `build_district` (`:990`) — T02 amber badge, T07 repoint at `_merged_2026-09-08` |
| `scripts/cluster/harvest_eu11_merged.py` | `FINAL_TAG`/`DELTA_TAG` priority chain (`:71-110`) — T06b adds `RECUT_TAG` at the top of the chain |
| `openubem/outputs/eu_evidence/EU-11/<D>_recut_2026-09-08/` | T05 output: full re-emission per district (`prepared_buildings.csv`, `<d>_manifest.csv`, `idfs/`, `schedules/`, `weather/`, `fleet.lst`, `summary_prerun.json`, **new** `excluded_buildings.csv`, **new** `recut_simulate_list.csv`) |
| `openubem/outputs/eu_evidence/EU-11/<D>_merged_2026-09-08/` | T06b output: merged manifest with `eui_source ∈ {recut, delta, final, ceiling82_carry}` |
| `openubem/outputs/eu_evidence/EU-11/<D>_layouts_2026-09-08b/` | T07 side-cars, then installed into `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_<D>_data/layouts/` |
| `openubem/outputs/eu_evidence/EU-11/wallB_second_pass_2026-09-08/` | T03 measurement CSVs |
| `docs/docs_ACTIVE/europeanLocations/debugs/undivided_buildings_all_districts_2026-09-08.csv` | **input**: the 473 undivided (184 `undivided_vertex_bug`, 289 `undivided_rule_*`) |
| `docs/docs_ACTIVE/europeanLocations/debugs/never_simulated_buildings_all_districts_2026-09-08.csv` | **input**: the 585 never-simulated with `blocker`, neighbour facts and `proposed_imputed_age_band` / `imputation_source` (director-built 2026-09-08, guidance and T04 test oracle) |
| `tests/test_eu_recut_95pct_2026_09_08.py` | **new**, the only new test file; T02/T03/T04 tests go here |

Baseline populations (from `<D>_delta_2026-09-07/prepared_buildings.csv`, measured 2026-09-08): Madrid 1,175 simulated / 1,033 divided / 67 vertex-bug / 75 refused · Lyon 509 / 459 / 25 / 25 · London 706 / 685 / 7 / 14 · Bologna 1,211 / 951 / 85 / 175 · fleet 3,601 / 3,128 / 184 / 289. Never simulated: Madrid 19, Lyon 21, London 536, Bologna 9 = 585 (stock 4,186).

---

## 4. Dependency decisions (pinned)

1. **Best-effort scope (`D-EU-111`)**: only `C6`, `C10`, `C11` may be soft. A cut failing any of `C1`, `C3`, `C4`, `C5`, the partition audit, the density cap, or raising a cutter exception is refused exactly as today. No threshold moves.
2. **Best-effort token**: storey `fallback_reason = "NOCORE_BEST_EFFORT_<ids>"` (e.g. `NOCORE_BEST_EFFORT_C11`, `NOCORE_BEST_EFFORT_C6_C10`) with `dwelling_layout_emitted=True`; building outcome `DWELLING_LAYOUT_EMITTED_BEST_EFFORT` (or `…_BEST_EFFORT_IMPUTED_COUNT` when the dwelling count was imputed). Existing tokens keep their exact meaning; no existing building may change token unless it was `FALLBACK_PENDING_LAYOUT*` with a soft-only failure.
3. **Imputation ladder (`D-EU-112`)**, applied per district after the base mapping, only to buildings the base mapping excluded, only for the missing field(s):
   1. touching prepared neighbours (footprint distance ≤ 0.05 m) that all agree → inherit; provenance `IMPUTED_NEIGHBOUR_TOUCHING`;
   2. else nearest prepared building within 30 m → inherit; provenance `IMPUTED_NEIGHBOUR_NEAREST_<d.d>M`;
   3. else district mode for the same building type (or all types when the type itself is missing) → provenance `IMPUTED_DISTRICT_MODE`.
   Fields: construction period / age band (GB `MISSING_OBSERVED_EPC_AGE_BAND`, `PERIOD_STRADDLE_*`; ES/FR `MISSING_OBSERVED_YEAR_BUILT`; IT `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS`), storeys (`MISSING_OBSERVED_STOREY_COUNT`), dwelling count and typology (`MISSING_OBSERVED_DWELLING_COUNT`, `TYPOLOGY_SIGNALS_DISAGREE` → inherit the neighbour's `building_type`; dwelling count then follows the existing `_geometry` imputation, outcome `…_IMPUTED_COUNT`). For a GB straddle, an inherited period must lie inside the straddle set (existing `D-EU-108 f` rule); when no neighbour period does, take the **older** band of the straddle (same tie rule as `D-EU-101 c5` for Bologna). `construction_period_provenance` and a new `imputation_provenance` column carry the tag; `storey_provenance` carries `IMPUTED_NEIGHBOUR_*` when storeys were inherited.
4. **Not imputed, ever**: `IDF_ASSEMBLY_FAILED_*` (12 buildings: ES 6, FR 1, IT 5 — an engine error, not missing data; T01 exports the error text, T04 reports them as an honest residual with the message) and `UNMAPPED_CENSUS_SECTION` / `CENSUS_SECTION_DATA_MISSING` (0 today).
5. **Re-emission is full per district, simulation is delta by hash.** T05 prepares every building of every district into `_recut_2026-09-08` (so one engine, one date, one provenance for all), then `recut_simulate_list.csv` = buildings whose `idf_sha256` differs from the newest earlier tree that holds them (`_delta_2026-09-07` first, else `_final_2026-09-07`) plus buildings with no earlier IDF. Only those go to Speed.
6. **Regression gate:** a building divided in the baseline (`DWELLING_LAYOUT_EMITTED` / `…_IMPUTED_COUNT` in `_delta_2026-09-07`) must still be divided in `_recut_2026-09-08`, with the same token. Zero exceptions; one regression fails T05.
7. **Wall B remedy is chosen at CP-1, not by the executor.** T03 measures; the director picks between the two pinned options in T03b (or rules "honest residual") and names the exact value; the executor never widens a budget on its own.
8. **Speed:** director ships four fleets (one per district, its own EPW) with `scripts/cluster/ship_eu11_fleet.sh`-style staging and submits **four arrays in the same minute**, each `--array=1-N%32 --time=7-00:00:00 -p ps`, sbatch template `submit_fleet_t08_frgb_2026-09-07.sbatch` already on Speed (`PLAN_eu-dwelling-division-recovery-2026-09-07.md:765-771`). ETA measured with `sacct`, never guessed.
9. **Viewer/badge:** amber (`fallback` CSS class already exists at `generate_eu_3d_viewers.py:97`) badge text `DIVIDED — BEST EFFORT (shape check failed: <ids>)`; imputed buildings get a second small badge `IMPUTED: <field> from <source>`. The floor-plan modal draws the emitted zones exactly as for ruled emissions.
10. **GSSCanada freeze:** the Madrid and Bologna populations 4J would freeze against change (+53 / +148 divided expected). The director tells 4J at CP-2, before Speed; the executor writes no message.

---

## 5. Facts with line citations (verified 2026-09-08)

1. The refusal is one `else` branch: `european_residential.py:1373-1378` builds `failed_ids` over `("C1","C3","C4","C5","C6","C10","C11")` and sets `fallback_reason = "NOCORE_CHECK_FAILED_" + "_".join(failed_ids)`, `dwelling_polygons=()`, `dwelling_layout_emitted=False`. The live polygons are already computed (`live`, `:1369`) and `_facade_contact_lengths(plate, live)` is already returned for them (`:1388`).
2. The partition audit runs only on `PASS` (`:1370-1372`). Best effort must run it too (dependency 1) — a soft failure with a failed audit is still refused.
3. `generate_european_building_dwelling_layout` (`:2645-2726`) refuses the whole building when any storey group has `dwelling_layout_emitted=False` (`:2699-2707`) and otherwise returns `fallback_reason_by_storey` (`:2717-2725`) — the per-storey best-effort tag rides that tuple unchanged.
4. `_geometry` (`run_eu_s2_district_campaign.py:154-160`) maps `building_layout.dwelling_layout_emitted` to `DWELLING_LAYOUT_EMITTED[_IMPUTED_COUNT]` / `FALLBACK_PENDING_LAYOUT[_MISSING_DWELLING_COUNT]` and **drops `building_layout.fallback_reason`**; the manifest `fallback_reason` (`:673`, `:707`) comes only from zone tags set by the at-risk gate. This is why `prepared_buildings.csv` carries no `NOCORE_CHECK_FAILED_*` reason (debug doc §8) — T01 fixes it.
5. Exclusions are counted, not listed: `summary_prerun.json.blocker_exclusions` is a histogram (`:336-350`, `:381-452`, `:501-586`, `:596-…`), and `IDF_ASSEMBLY_FAILED_<exc>` is a counter at `:716`. No per-building exclusion file exists outside London's `EU-11/london_coverage/exclusion_census_2026-09-07.csv` (T02 of the London plan). T01 adds `excluded_buildings.csv` to every prepare.
6. GB terrace inheritance (`:372-452`) already implements ladder step 1 for GB only, touching-prepared neighbours (`pairs`), agreement required, straddle containment (`:403-406`), storey inheritance (`:409-413`, `:431-451`), behind `--recover-terrace-neighbours` (`:753`). T04 generalises it; it does not fork it.
7. The near-duplicate-vertex path: `run_eu_s2_campaign.py:690-718` — `_has_near_duplicate_vertex_surfaces(idf)` trips `at_risk`, `_force_reroute_room_layout_to_one_zone_per_floor` deletes the cut (`did_reroute=True`) → the district campaign labels it `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` (`run_eu_s2_district_campaign.py:666-667`); when the reroute declines and `mismatched` is false the box is kept with `near_duplicate_vertex_tolerated_box` (`:714-715`). `_drop_redundant_ring_vertices` (`:149-250`) runs pre-cut on the footprint (`european_residential.py:1351-1354`) and refuses a removal beyond chord 0.010 m / per-removal 1e-3 / cumulative 2e-3 relative area (`:236-240`).
8. The recovery plan measured the pre-fix residual: 173 of 173 undivided-with-defect had the defect on the footprint ring, none on an interzone partner (`PLAN_eu-dwelling-division-recovery-2026-09-07.md:572-574`), and expected 171 of 173 to clear; the 184 now left are the post-fix residual and have **not** been characterised — T03 does that.
9. Manifest columns available for the regression gate: `prepared_buildings.csv` = `building_id, stem, archetype_id, building_type, age_band, geometry_outcome, idf_sha256, weather_sha256, construction_period_provenance, storey_provenance, floor_area_m2, gross_footprint_area_m2, conditioned_floor_area_m2, eui_denominator_m2, context_building_count, fallback_reason`.
10. Stock ids: `openubem/outputs/eu02/<D>/02_residential_manifest.gpkg` (layer `buildings`; `osm_id` = the manifest `building_id`; ES/GB `way/…`|`relation/…`, FR `BATIMENT…_partN`, IT integer strings). Rows 1,194 / 530 / 1,242 / 1,220; prepared 1,175 / 509 / 706 / 1,211; difference 19 / 21 / 536 / 9 = 585 (verified 2026-09-08).
11. Harvest priority chain: `harvest_eu11_merged.py:71-110` picks `DELTA_TAG` over `FINAL_TAG` over `ceiling82_carry` per building, rc-zero only. Viewer EUI source is hard-wired to `_merged_2026-09-07` (`generate_eu_3d_viewers.py:870`), falling back to ceiling82.
12. Speed today (12:06 EDT 2026-09-08): Bologna delta job `1311708` 554 done + 8 failed + 32 running of 703, mean 31.7 min/task → ≈ 1.8 h left; London provisional job `1310803` 255 done. Bologna's `_merged_2026-09-07` tree does not exist yet — the director harvests it before T05's Bologna delta is computed (T05 uses `_delta_2026-09-07/prepared_buildings.csv` as the hash baseline, which already exists, so T05 itself is not blocked).

---

## 6. Tasks

### T01 — Export what the campaign already knows: per-storey refusal reason and per-building exclusions

**What.** (a) In `_geometry` (`run_eu_s2_district_campaign.py:128-166`) return `building_layout.fallback_reason` (and, when emitted, the first non-empty entry of `fallback_reason_by_storey`) and write it into the manifest `fallback_reason` column (`:707`) whenever the zone-tag reason is empty; zone-tag reason keeps precedence. (b) Every prepare writes `excluded_buildings.csv` next to `summary_prerun.json`: `building_id, stage, blocker, detail` — one row per building the base mapping, the recovery pass, or the IDF build excluded (`:348`, `:397-449`, `:529-567`, `:596-…`, `:716`; `detail` = the exception text for `IDF_ASSEMBLY_FAILED_*`).
**Why.** Fact 4/5: the reasons exist in memory and are thrown away; every later audit had to re-derive them from side-cars (debug doc §8) or could not at all (the 49 non-London exclusions).
**How.** Thread the reason through `_geometry`'s return (a third element or a dict; keep the two-tuple callers working); in the exclusion loops, append to a list beside each `exclusions[...] += 1`; write the CSV where `summary_prerun.json` is written. Histogram in `summary_prerun.json` must equal the CSV's `blocker` value counts.
**How to test.** `tests/test_eu_recut_95pct_2026_09_08.py::test_t01_*`: (1) a synthetic FAIL layout yields a manifest row with `fallback_reason == "NOCORE_CHECK_FAILED_C11"`; (2) an excluded synthetic row appears in `excluded_buildings.csv` with the same blocker the histogram counts. Run `tests/test_eu_s2_campaign.py -q` and `tests/test_eu_london_recovery_2026_09_07.py -q` — both must stay green (49 in the London file).

### T02 — The best-effort tier (`D-EU-111`)

**What.** In `generate_european_nocore_storey_layout` (`european_residential.py:1373-1378`): when `verdict == "FAIL"` and `failed_ids ⊆ {"C6","C10","C11"}` and `len(live) == dwelling_count`, run `audit_european_floor_partition` on `(plate, live)` and return the layout **emitted** (`dwelling_polygons=live`, `dwelling_layout_emitted=True`, `partition_audit=<audit>` **whether or not it passed**, `fallback_reason="NOCORE_BEST_EFFORT_" + "_".join(failed_ids)`); refuse as today only when not eligible. **Amendment 2026-09-08 13:05 (director, from 4J's warning):** the `PASS` branch at `:1373-1378` records the audit and never gates on `passed`; 980 of the 1,036 drawn Bologna side-cars (`IT-BOL-GALVANI2_layouts_2026-09-08/`) carry `passed=false` (topology tolerance `1e-9` of the plate, not the area check), so a best-effort branch gated on `passed` would refuse almost every eligible cut. Best-effort must mirror the `PASS` branch exactly: record, never gate. In `_geometry` (`run_eu_s2_district_campaign.py:154-160`): when emitted and any `fallback_reason_by_storey` starts with `NOCORE_BEST_EFFORT_` → outcome `DWELLING_LAYOUT_EMITTED_BEST_EFFORT` / `…_BEST_EFFORT_IMPUTED_COUNT`. Same branch in `emit_eu11_layout_sidecars.py:300-340` (payload keeps `checks` with the real `FAIL` verdict and adds `best_effort_failed_checks: [...]`; and the building-level `partition_audit` block at `:523-526` gains `failures` (union over storeys), `gap_area_m2`, `overlap_area_m2`, `outside_area_m2` (max over storeys) beside `passed` and `area_error_fraction` — 4J ask 1 of 2026-09-08, a reporting field, never a gate). Viewer (`generate_eu_3d_viewers.py:439-471`): the amber badge of dependency 9.
**Why.** Debug doc §4; owner accepted 2026-09-08. The engine gains real flats with real party walls; the thin-flat / short-façade / pinch facts stay visible on the record.
**How.** Smallest diff: one new `elif` between the `PASS` and `else` branches at `:1370`; the `EuropeanGridLayout` fields already exist. Do not touch `european_nocore.py`. Sidecar and viewer: extend the existing token switch; no new rendering path.
**How to test.** In the new test file: (1) a 30 × 8 m rectangle asked for 6 flats → `C11` fails, result `dwelling_layout_emitted=True`, `fallback_reason == "NOCORE_BEST_EFFORT_C11"`, 6 polygons, area conserved to ≤ 0.01 %; (2) the same footprint with a hole forced to fail `C5` → refused, reason contains `C5`; (3) `MAX_FLAT_ASPECT == 2.5` and the check dict still reports `C11 pass=False` on case 1; (4) `_geometry` outcome token on case 1 == `DWELLING_LAYOUT_EMITTED_BEST_EFFORT`. Then the **dry measurement** over the 289 refused ids in `debugs/undivided_buildings_all_districts_2026-09-08.csv` (`defect_class` starts with `undivided_rule_`): run the layout function only (no IDF, no EnergyPlus) and report `emitted_best_effort / still_refused` per district with the still-refused reasons histogram, **plus** for the emitted ones `audit_passed / audit_failed` (what the pre-amendment gate would have thrown away), and `partition_audit is not None` asserted on case 1. Expected order of magnitude (not a pass criterion): Madrid ≈ 50, Bologna ≈ 150, London ≈ 5 recovered; density (`GT_12`) and `C4`/`C5` stay refused.

### T03 — Wall B measurement: why the near-duplicate-vertex path still rejects 184 cuts

**What.** For each of the 184 `undivided_vertex_bug` ids (CSV above), rebuild the storey layout and the IDF surfaces **locally without simulating** and record, in `EU-11/wallB_second_pass_2026-09-08/wallB_defects.csv`: `district, building_id, stem, n_flagged_surfaces, defect_kind ∈ {near_duplicate, collinear}, defect_on ∈ {footprint_ring, cut_edge, interzone_pair}, refused_by ∈ {chord_0.010m, per_removal_1e-3, cumulative_2e-3, min_3_vertices, not_on_ring}, min_edge_len_m, perp_dist_m, rel_area_change`. Then a histogram of `(defect_on, refused_by)` and the two counts the director needs: (i) how many would clear if only the chord tolerance were 0.020 m; (ii) how many have the defect on a cut edge (i.e. created by the cutter, not by the footprint).
**Why.** Fact 8: the 184 are the post-fix residual and nobody has looked at them. Choosing a remedy before measuring is the failure mode this project keeps paying for.
**How.** Reuse `_has_near_duplicate_vertex_surfaces` (`run_eu_s2_campaign.py:94`) and `_drop_redundant_ring_vertices` (`:149`) instrumented through a local wrapper in the test/measurement module (not by editing them). Drive the IDF build through the same `build_idf_for_building` call the campaign uses (`run_eu_s2_district_campaign.py:657-660`) with a scratch `run_dir` under the evidence folder. Run the four districts as four processes.
**How to test.** Row count == 184; every row has a non-empty `defect_on`; the histogram sums to 184. Register `FINDING 267` in the progress log: the measured cause mix, one paragraph. **STOP → CP-1.**

### T03b — Wall B remedy (only after CP-1 names it)

**What.** One of: (a) raise `RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M` to the value the director names, footprint ring only; (b) run `_drop_redundant_ring_vertices` on every emitted zone polygon *after* the cut, before `european_building_layout_to_zone_specs` bakes `coords_m` (i.e. the post-cut point `D-EU-109 b` names); (c) honest residual — no change, the 184 (or the measured remainder) stay boxes and are named in the restatement.
**How to test.** Re-run the T03 measurement; report `cleared / still_flagged` of 184; zero regressions on the T02 dry run and on `tests/test_eu_collinear_ring_cleanup.py`.

### T04 — Neighbour imputation for the never-simulated (`D-EU-112`)

**What.** A district-agnostic pass in `run_eu_s2_district_campaign.py`, run after the base mapping for **all four** districts (replacing the GB-only `--recover-terrace-neighbours` gate with `--impute-from-neighbours`, default on for this plan's trees), implementing the ladder of dependency 3 for the four fields. Every imputed row carries `imputation_provenance` (new manifest column; `""` for observed rows) and the existing `construction_period_provenance` / `storey_provenance` tags. `excluded_buildings.csv` (T01) records what remains excluded and why.
**Why.** Owner 2026-09-08: *"lets apply imputation and include these buildings inside the simulation clusters"*. The London terrace rule already showed the shape of the answer (255 buildings recovered 2026-09-07); this makes it fleet-wide and adds the two lower rungs.
**How.** Lift `:372-452` into a function `impute_from_neighbours(gdf, base_rows, records, district)`: build `pairs` from footprint adjacency (existing `compute_footprint_adjacency` for ES/FR; the GB `pairs` construction; add IT), a spatial index for the 30 m rung, and the district mode from `base_rows`. Feed the imputed `year_built` / `levels` / `building_type` / period into the *existing* per-district mapping functions so archetype selection stays the one path (`select_tabula_archetype`). Do not edit `map_observed_building_to_tabula`.
**How to test.** (1) Unit: three synthetic buildings — touching agree → rung 1; no touch, one prepared within 30 m → rung 2; isolated → rung 3; a GB straddle with a neighbour outside the set → older band. (2) **Oracle**: for the 585 rows of `debugs/never_simulated_buildings_all_districts_2026-09-08.csv`, the code's imputed period must equal `proposed_imputed_age_band` wherever `imputation_source` is `touching_prepared_neighbours_agree` or `nearest_prepared_neighbour_*`; list every disagreement with both values (the CSV is the director's independent derivation; a disagreement is a finding, not automatically a bug — report, do not "fix" the CSV). (3) Count recovered per district vs the 12 `IDF_ASSEMBLY_FAILED` + any other honest residual; expected ≈ 570 of 585 enter the prepare.

### T05 — One re-emission, four districts in parallel, delta by hash

**What.** Prepare all four districts into `EU-11/<D>_recut_2026-09-08/` with the T01–T04 engine (four processes at once). Then `recut_simulate_list.csv` per district (dependency 5) and a fleet `fleet.lst` restricted to that list. Gates, per district, each as "N of M":
  - G1 regression: baseline-divided buildings still divided with the same token — must be `M of M`;
  - G2 divided count: `DWELLING_LAYOUT_EMITTED*` (incl. `_BEST_EFFORT*`) ≥ baseline divided + T02 dry-run gain − 0;
  - G3 imputed rows: every building not in the baseline has non-empty `imputation_provenance`; none has an observed-only tag;
  - G4 side-car reason coverage: every `FALLBACK_PENDING_LAYOUT*` row has a non-empty `fallback_reason` (T01);
  - G5 `fleet.lst` lines == `recut_simulate_list.csv` rows == IDF files staged for shipping; `population_prepared` quoted as "N of 1,194 / 530 / 1,242 / 1,220";
  - G6 the `conditioned_floor_area_m2` distribution of unchanged-hash buildings is byte-identical to baseline (a changed denominator with an unchanged IDF is a defect).
**How to test.** A small checker (in the test file, parametrised by district) that reads baseline and recut manifests and prints the six lines. **STOP → CP-2** with the six lines × four districts and the per-district `recut_simulate_list.csv` counts.

### T06 — Speed campaign (director-only) and harvest

**T06a (director).** Stage and ship the four fleets (`idfs/` restricted to the simulate list, `weather/`, `schedules/`, `fleet.lst`), remote dirs `/speed-scratch/o_iseri/fleets/EU11_<D>_recut_2026-09-08/`, submit four arrays in the same minute (`--array=1-N%32 --time=7-00:00:00 -p ps`, template already on Speed), record job ids in §8, measure the ETA with `sacct` after the first 32 complete, check `squeue` shows 32 running account-wide. Dead-task rule and straggler rule from CLAUDE.md apply. On drain: `sacct` state histogram; failed tasks classified by the four known signatures; fetch `out/`.
**T06b (Sonnet).** Extend `harvest_eu11_merged.py` with `RECUT_TAG = "recut_2026-09-08"` at the top of the priority chain and a `--merged-tag 2026-09-08` output tag; run it for all four districts → `<D>_merged_2026-09-08/` (`summary.json` with `n_with_eui` of `population_prepared`, pooled EUI as "N of M", `eui_source` histogram). Restate the four district EUIs and the fleet divided count in the progress log as "N of M", alongside the 2026-09-07 values they supersede.
**How to test.** Manifest rows == `population_prepared`; `eui_source == recut` rows == rc-zero recut tasks; no building has an EUI from an IDF whose hash is not the one in `_recut_2026-09-08`; pending rows blank, never carried from an older hash.

### T07 — Viewers, side-cars, mirror

**What.** (1) `generate_eu_3d_viewers.py:862-880`: prefer `_merged_2026-09-08`, then `_merged_2026-09-07`, then ceiling82; badges per dependency 9; `build_district` for all four; mirror to `outputs_3D/eu_<D>_viewer.html` + `_data/buildings.csv` + `sources.json` (byte-identical copies). (2) `emit_eu11_layout_sidecars.py --evidence-root <D>=EU-11/<D>_recut_2026-09-08` for **all four** districts (Lyon has never had side-cars) → `<D>_layouts_2026-09-08b/`, installed into `outputs_3D/eu_<D>_data/layouts/` in the shape the viewer of that district already reads (Madrid/London `layouts/relation|way/<id>.json`, Bologna flat `layouts/<id>.json`; Lyon: follow the FR id shape the viewer's loader expects — check `generate_eu_3d_viewers.py` for the FR path before writing).
**How to test.** Per district, five lines: feature count == merged manifest rows; EUI non-null == `n_with_eui`; badge counts (ruled / best-effort / box / no-IDF) == manifest token counts; side-car files == `population_prepared`, 0 files with `has_unconditioned_core: true`, `circulation_area == 0` everywhere; mirror `fc` byte-identical. **STOP → CP-3.**

### T08 — Audit, ledger, references

**What.** (1) The final table in §8: per district and fleet — stock, simulated, divided (ruled / best-effort), boxes (vertex-bug residual / rule residual / density), never simulated (with residual blockers), EUI "N of M" — every number traced to a file. (2) Append the supersession markers: debug doc §2/§8 numbers and `STATE_european_locations_v5.md` §0 (next free `D-EU-113` / `FINDING 268`), §8 ledger entries for `D-EU-111`, `D-EU-112`, `FINDING 267` (T03), the table row statuses for `D-EU-107/108/109` that this wave closes. (3) Register every error met in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. (4) Nothing else — no message to 4J (director), no README edits, no new docs.

---

## 7. Stop-and-report points

- **CP-1 — after T03.** Director reads `wallB_defects.csv` histogram, rules T03b (a)/(b)/(c) with the exact value, and signs T01/T02 tests. Executor stops until the ruling is in §8.
- **CP-2 — after T05.** Six gates × four districts, all "N of M". Director signs, tells 4J, ships to Speed (T06a). Executor stops.
- **CP-3 — after T07.** Five audit lines × four districts. Director signs; T08 released.
- **Any test failure, any gate < M of M, any ambiguity in a cited line range** → stop, quote, wait.

---

## 8. Progress log

(executor appends below this line; one entry per task, never edit above)

#### Director note — 2026-09-08 — T03 runs concurrently with T01–T02

T03 is measurement-only and independent of T01–T02, so it is dispatched to a second executor at the same time. To avoid two sessions editing one file: the T03 executor must **not** edit `openubem/geometry/european_residential.py`, `scripts/run_eu_s2_district_campaign.py`, `scripts/run_eu_s2_campaign.py`, or `tests/test_eu_recut_95pct_2026_09_08.py`. Deviation from rule 12, authorised here: the T03 measurement driver lives in `scripts/eu_wallb_measure_2026_09_08.py` and its tests in `tests/test_eu_wallb_second_pass_2026_09_08.py`. Both executors append their own progress-log entries under this line; neither rewrites the other's.

#### Director amendment — 2026-09-08 13:05 — T02 gate corrected, side-car audit fields added, pin announcement rule

4J (GSSCanada) warned at 12:5x that the T02 best-effort branch as written (`if best_effort_audit.passed`) would under-recover: measured here, 980 of 1,036 drawn Bologna side-cars carry `partition_audit.passed = false` while the `PASS` branch emits regardless. T02 §What/§How-to-test amended in place (marked **Amendment 2026-09-08 13:05**); the running T01–T02 executor was told by message. Two further asks accepted: (1) side-car `partition_audit` carries `failures`, `gap_area_m2`, `overlap_area_m2`, `outside_area_m2` (T02 change in `emit_eu11_layout_sidecars.py`, lands in every `_layouts_2026-09-08b/` file at T07); (2) the director's announcement to 4J after T07 states the commit sha, the line-ending convention, and the sha256 of `european_residential.py` and `european_nocore.py` as checked out on Windows (CRLF) — their pins are CRLF-blob digests. Eligibility of `DWELLING_LAYOUT_EMITTED_BEST_EFFORT*` on their side is their author's ruling, pending; the tokens stay distinct literals, never folded into `DWELLING_LAYOUT_EMITTED`.

#### T03 — Wall B measurement: why the near-duplicate-vertex path still rejects 184 cuts — completed 2026-09-08

**Artifacts.** `scripts/eu_wallb_measure_2026_09_08.py` (new, ~330 lines) — measurement driver, dispatched as four parallel processes (`--district Madrid|Lyon|London|Bologna`), merged with `--merge`. `tests/test_eu_wallb_second_pass_2026_09_08.py` (new, 13 tests). `openubem/outputs/eu_evidence/EU-11/wallB_second_pass_2026-09-08/wallB_defects.csv` (184 rows, the T03 deliverable) plus one `wallB_defects_<district-code>.csv` per district and a `scratch/` working folder (geomeppy IDF scratch files, 516 KB, harmless to keep).

**Method.** For each of the 184 `undivided_vertex_bug` ids, the real `_geometry()` (`run_eu_s2_district_campaign.py`, imported not edited) rebuilds the exact zones the campaign built; a local wrapper then replays the real `_drop_redundant_ring_vertices` per zone ring and the real `extrude_geometry` (which itself calls `intersect_match` once) — the same sequence `build_idf_for_building` runs before its at-risk gate — and stops there. A diagnostic scan reproduces `_has_near_duplicate_vertex_surfaces`'s own math (same imported tolerance constants) but records every flagged surface instead of returning one bool. `context` was passed empty throughout: `extrude_geometry` only consumes it for shading blocks added after `intersect_match` (`openubem/idf/surfaces.py:872-984`), so it cannot affect the interzone-vertex defect being measured. Fidelity check (Track A): calling the real, unmodified `build_idf_for_building` end-to-end on one sample building per district reproduced the exact same reroute log line (`"rerouting room_layout to one_zone_per_floor (near_duplicate_vertex)"`) the original campaign produced, for all four districts, confirming the reconstruction matches. Row source: `<D>_final_2026-09-07/prepared_buildings.csv` (verified 0/184 missing, 0/184 `geometry_outcome` mismatch against the debug CSV) plus, network-free, the real `_mapped_rows` (ES/FR), `_gb_rows` + `_gb_terrace_recovery_rows` (GB — the London vertex-bug population needed the terrace-recovery pass merged in, one file fix mid-run), and, since Bologna's `_it_rows` requires live HTTP (forbidden), a manifest+prepared-CSV reconstruction for IT with `levels` derived from `gross_footprint_area_m2 / footprint_area_m2` (max deviation from an integer: 0/85 buildings over 0.1).

**Result — the (defect_on, refused_by) histogram over 184:**
- `cut_edge` × `not_on_ring`: 117
- `interzone_pair` × `not_on_ring`: 55
- `footprint_ring` × `not_on_ring`: 12
- Sum: 184. `defect_kind`: `near_duplicate` 150, `collinear` 34. `n_flagged_surfaces` per building: min 2, median 34, mean 37.5, max 252.

**Director's two counts.** (i) How many would clear if the chord tolerance were 0.020 m: **0 of 184** — confirmed twice, independently: an actual rebuild with `RING_VERTEX_REMOVAL_CHORD_DISTANCE_TOLERANCE_M` monkeypatched to 0.020 (never edited in the source file) still leaves all 184 flagged, and a from-first-principles replay of the removal test agrees. (ii) How many have the defect on a cut edge created by the cutter, not the footprint: **117 of 184** (64%); `footprint_ring` accounts for 12 of 184 (6%); the remaining 55 (30%) are not traceable to any pre-existing footprint or cut vertex at all.

**FINDING 267.** Every one of the 184 rejections is caused by a vertex that did not exist before extrusion: geomeppy's `intersect_match` creates it fresh when it pairs one dwelling's ceiling/floor (or two same-floor dwelling walls) against a differently-shaped partner on the storey above/below or next door (the FINDING 210 mechanism), and the pre-extrusion ring-cleanup pass (`_drop_redundant_ring_vertices`, chord/area budgets) never had a vertex to refuse — for all 184, `refused_by == not_on_ring`. Where the offending point happens to sit at the same (x, y) as a real footprint or cut-line vertex (129 of 184: 117 on an interior partition wall the dwelling cutter drew, 12 on the true exterior footprint), that vertex is checked on its own ring and found NOT locally redundant there — meaning it is not a case the removal budgets ever saw, only a coincidence of location. In plain terms: this is not "a good vertex got refused by a tight budget", it is "the defect is manufactured downstream of both the footprint and the cut, purely by the interzone-pairing step" — which is why loosening the removal chord tolerance to 0.020 m (T03b option a) measurably fixes 0 of 184, and strongly suggests retiming the same cleanup pass to run earlier (option b) targets a vertex class that, by construction, does not exist yet at that earlier point either.

**Test status.** `tests/test_eu_wallb_second_pass_2026_09_08.py -q`: 13 passed (6 unit tests on the new `_ring_area`/`classify_defect` helpers with synthetic rings, 7 acceptance tests against `wallB_defects.csv`: row count 184, non-empty/in-domain `defect_on`/`defect_kind`/`refused_by`, histogram sums to 184, stems match `sha256(building_id)[:16]`, no duplicate building ids, per-district population matches the plan's baseline 67/25/7/85). Regression: `tests/test_eu_collinear_ring_cleanup.py -q`: 11 passed, unaffected (the chord-tolerance monkeypatch is always restored in a `finally` block and scoped to this process only).

**Deviations.** (1) `_gb_rows` alone does not cover the London vertex-bug population (`KeyError` on first run); fixed by merging in `_gb_terrace_recovery_rows`, the same network-free recovery pass `prepare(..., recover_terrace_neighbours=True)` uses — confirmed the merged 706-row population matches the plan's quoted London baseline exactly, 0/7 missing after the fix. (2) An initial `classify_defect` implementation returned `chord_0.010m`/`cumulative_2e-3` for defects that were not actually locally redundant on their own ring (perp-distance outliers up to ~17 m gave this away); fixed by checking local redundancy first, which changed the histogram to the one reported above — the empirical chord-relaxation re-run (independent of this classifier) was unaffected by the bug and corroborates the fixed result (0/184 both times). Neither deviation touched `openubem/geometry/european_residential.py`, `scripts/run_eu_s2_district_campaign.py`, `scripts/run_eu_s2_campaign.py`, or `tests/test_eu_recut_95pct_2026_09_08.py`.

**CP-1.** STOP. T03b not started. Awaiting the director's ruling on (a)/(b)/(c) with the exact value.


#### Director ruling — CP-1 (T03b part) — 2026-09-08 13:20

**Ruling: (c) honest residual.** No budget is raised, `_drop_redundant_ring_vertices` is not retimed, T03b is **not dispatched**. Basis, from `wallB_defects.csv` (184 rows, FINDING 267): option (a) at 0.020 m clears **0 of 184** (measured by rebuild with the tolerance monkeypatched, and by analytical replay); option (b) runs the same cleanup at a point where the offending vertex does not exist yet (it is created by geomeppy `intersect_match` during extrusion, `refused_by == not_on_ring` for all 184), so it clears 0 of 184 by construction. Neither pinned remedy is supported by the measurement; a remedy that would act on the vertex class actually found (a post-`intersect_match` vertex merge or a per-pair surface repair) is a new design item in the FINDING 210 / D-EU-43 family, not a same-day patch, and is **not** opened here.

**Consequences for the rest of the plan.** The 184 keep `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` and simulate as one zone per floor (boxes), exactly as in the 2026-09-07 baseline; they are excluded from the T05 delta (their IDF hash is unchanged) and named as such in the T08 restatement ("184 wall-B buildings: layout drawn, simulated as boxes, cause measured in FINDING 267"). T04 and T05 proceed as written. The three `RING_VERTEX_REMOVAL_*` budgets, `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` and `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` stay at their current values (rule 5). Open item for a later arc, not scheduled: "post-extrusion interzone vertex repair for the 184" — record under the next free OPEN number when T08 writes the ledger; no D-EU number is consumed by this ruling.

#### T01 — Export what the campaign already knows: per-storey refusal reason and per-building exclusions — completed 2026-09-08

**Artifacts.** `scripts/run_eu_s2_district_campaign.py`: `_ExclusionCounter` (`:75-92`) — a `Counter` subclass adding `.records`/`.log(building_id, stage, blocker, detail="")`, so the existing `blocker_exclusions` histogram is unchanged and every 2-tuple caller of `_gb_rows`/`_it_rows`/`_mapped_rows`/`_gb_terrace_recovery_rows` (13 external call sites across `tests/test_eu_s2_campaign_ceiling82.py`, `tests/test_eu_london_recovery_2026_09_07.py`, `scripts/eu17_reroute_trace.py`, `scripts/eu17_refusal_census.py`, `scripts/emit_eu11_layout_sidecars.py`, `scripts/eu21/11_interzone_diagnostics.py`) keeps working unmodified. `_GeometryOutcome` (`:95-105`) — a `str` subclass carrying `.layout_reason`, same reasoning applied to `_geometry`'s own 2-tuple return (3 external 2-unpack callers: `scripts/eu21/11_interzone_diagnostics.py:521,627` and this file's own `prepare()`). `_geometry` (`:148-219`): `layout_reason = building_layout.fallback_reason or next(... fallback_reason_by_storey ...)` (`:189-191`), returned as `_GeometryOutcome(outcome, layout_reason)` (`:219`). `prepare()`: `layout_reason = outcome.layout_reason` captured immediately after the call, before the interzone-reroute branch can overwrite `outcome` (`:705`); manifest `fallback_reason` falls back to it only when the zone-tag reason is empty, `... or (layout_reason or "")` (`:726`, zone-tag precedence unchanged). Every exclusion site now calls `.log(...)` instead of a bare `Counter[key] += 1`: `_gb_rows` (`:396`), `_gb_terrace_recovery_rows` (`:432,435,439,447,464,467,474`), `_it_rows` (`:558,563,569,582,587,590,596`), `_mapped_rows` (`:646,648`), `prepare()`'s IDF-build exception handlers (`:761-768`). `excluded_buildings.csv` (`building_id, stage, blocker, detail`) written per district next to `summary.json` (`:800-808`).

**Deviations.** (1) The plan's "How." suggested threading a third tuple element through `_geometry`'s return; kept the 2-tuple and used a `str` subclass instead (`_GeometryOutcome`), because `_geometry`, `_gb_rows`, `_it_rows`, `_mapped_rows` and `_gb_terrace_recovery_rows` all have external 2-unpack callers outside this plan's file list (listed above) that a 3-tuple would break — this satisfies "keep the two-tuple callers working" literally for every one of them, not only `_geometry`. (2) `excluded_buildings.csv` is written next to `summary.json`, the file `prepare()` actually writes at prepare-time; the plan's "next to `summary_prerun.json`" names the file's post-harvest name (`scripts/cluster/harvest_eu11_district.py` renames `summary.json` → `summary_prerun.json` at harvest, `:293-295`) — same file, no new write path.

**Test status.** New file: `test_t01_geometry_threads_layout_reason_into_manifest_fallback_reason`, `test_t01_excluded_buildings_csv_matches_histogram` — 2 passed. Regression (rule: both must stay green): `tests/test_eu_s2_campaign.py -q` — 17 passed. `tests/test_eu_london_recovery_2026_09_07.py -q` — 7 passed (no `49` assertion found in that file; read as background context on the existing London exclusion census, not a runnable check — flagged, not fixed).

**Notes.** No error was hit; nothing added to `OpenUBEM_debug_References.md`.

#### T02 — The best-effort tier (`D-EU-111`) — completed 2026-09-08, amendment 13:05 applied

**Artifacts.** `openubem/geometry/european_residential.py`, `generate_european_nocore_storey_layout` (`:1338-1410`): the `else` branch (verdict `FAIL`, `:1376-1398`) computes `best_effort_eligible = set(failed_ids) <= {"C6","C10","C11"} and len(live) == dwelling_count` (`:1386`); when eligible, emits unconditionally — `partition_audit` recorded (never gated on `.passed`, mirroring the `PASS` branch exactly per the 13:05 amendment), `fallback_reason = "NOCORE_BEST_EFFORT_" + "_".join(failed_ids)`, `dwelling_layout_emitted=True` (`:1387-1394`); otherwise refuses as before, `NOCORE_CHECK_FAILED_...` (`:1395-1398`). `european_nocore.py` untouched. `scripts/run_eu_s2_district_campaign.py`, `_geometry` (`:192-207`): `is_best_effort = any(reason.startswith("NOCORE_BEST_EFFORT_") ...)` over `fallback_reason_by_storey` (`:199-202`) → outcome `DWELLING_LAYOUT_EMITTED_BEST_EFFORT` / `..._BEST_EFFORT_IMPUTED_COUNT` (`:203-206`), else the unchanged plain tokens. `scripts/emit_eu11_layout_sidecars.py`: outcome branch mirrors the campaign (`:280-316`, `best_effort_reasons`/`best_effort_failed_checks` at `:286-297`; two other branches set `best_effort_failed_checks = []` at `:320,349`); building-level `partition_audit` payload gains `failures` (sorted union over storey audits), `gap_area_m2`, `overlap_area_m2`, `outside_area_m2` (max over storey audits, 6 dp) beside `passed`/`area_error_fraction` (`:473-506`, dict at `:544-551`; report-only, never a gate — 4J ask 1 of 13:05). `scripts/generate_eu_3d_viewers.py` (`:437-450`): amber `m-badge fallback` badge `DIVIDED — BEST EFFORT (shape check failed: <ids>)` when `b.ls==="ruled"` and `pl.reason` starts `NOCORE_BEST_EFFORT_`, parsed client-side from the existing `pl.reason` field (no new Python payload field needed — `pl.reason = sidecar["fallback_reason"]` already flows through unchanged, `:983-984`). New: `tests/test_eu_recut_95pct_2026_09_08.py` (194 lines, 7 tests total with T01).

**Storey token form (confirmed).** `fallback_reason = "NOCORE_BEST_EFFORT_" + "_".join(failed_ids)`, e.g. `NOCORE_BEST_EFFORT_C11`, `NOCORE_BEST_EFFORT_C6_C10` — `dwelling_layout_emitted=True` in every case; `dwelling_polygons` and `partition_audit` are always populated, `partition_audit.passed` may be `False`.

**Dry-run measurement (289 rule-refused ids, layout function only, no IDF, no EnergyPlus; ES/FR/GB via the real offline `_gb_rows`/`_mapped_rows`/`_gb_terrace_recovery_rows`; Bologna approximated from the cached `_delta_2026-09-07` archetype/period assignment plus a storey count derived from that tree's own recorded floor area, both local — no live HTTP):**

| District | n | emitted_best_effort | audit_passed | audit_failed | still_refused | still-refused reasons |
|---|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE (Madrid) | 75 | 52 | 0 | 52 | 23 | `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12`:9, `NOCORE_CHECK_FAILED_C4`:9, `NOCORE_CHECK_FAILED_C5`:5 |
| FR-LYO-HAUTCOEURPENTES (Lyon) | 25 | 12 | 0 | 12 | 13 | `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12`:3, `NOCORE_CHECK_FAILED_C4`:2, `NOCORE_CHECK_FAILED_C5`:8 |
| GB-LDN-STDUNSTANS (London) | 14 | 5 | 0 | 5 | 9 | `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12`:9 |
| IT-BOL-GALVANI2 (Bologna, approximated) | 175 | 135 | 1 | 134 | 40 | `NOCORE_CHECK_FAILED_C4`:10, `NOCORE_CHECK_FAILED_C4_C11`:2, `NOCORE_CHECK_FAILED_C5`:28 |
| **Fleet** | **289** | **204** | **1** | **203** | **85** | density `GT_12` 21, `C4` 21, `C4_C11` 2, `C5` 41 |

`not_found` = 0 of 289 in every district (every debug-CSV id resolved in the offline base rows). 203 of 204 best-effort emissions fail the strict topology audit (`partition_audit.passed=False`) despite being geometrically sound cuts — this is the fleet-wide confirmation of the 980/1,036 Bologna sample 4J reported at 12:5x, and is exactly why the 13:05 amendment (record, never gate) was necessary: the pre-amendment code would have recovered 1 of 289, not 204. Order-of-magnitude check against the plan's expectation: Madrid ≈50 measured 52, London ≈5 measured 5, Bologna ≈150 measured 135 (same order, approximated district).

**Test status.** `tests/test_eu_recut_95pct_2026_09_08.py -q -k "not dry_run"` — 6 passed (T01: 2, T02 cases 1-4: 4). `-k dry_run` — 1 passed in 1022 s (17:02), 640 benign `RuntimeWarning: divide/invalid value in buffer` (shapely, from near-degenerate best-effort geometry, non-fatal, no assertion affected). Regression: `tests/test_eu_collinear_ring_cleanup.py -q` — 11 passed. `tests/test_eu_nocore_rules.py` does not exist in this repo — skipped, not substituted.

**Deviations.** (1) The plan's illustrative case-1 geometry ("30×8 m, 6 flats") passes all 7 checks as built today (verified) rather than failing `C11` — used `box(0,0,60,5)`/`dwelling_count=3` instead (verified: fails only `C11`, `len(live)==dwelling_count`), same design intent, different concrete numbers. (2) Case 2 ("hole forced to fail C5") — an interior-ring hole is repaired before scoring (`cut_storey_nocore`'s own preprocessing) and does not reach the checks, so `C5` was forced via `monkeypatch` on `cut_storey_nocore`'s returned `checks` dict instead of a literal hole; same assertion (`refused, reason contains C5`). (3) Amendment 13:05 applied before any test ran against the pre-amendment code — no regression window.

**Notes.** No error was hit; nothing added to `OpenUBEM_debug_References.md`.

**T03 audit (director).** `wallB_defects.csv` 184 data rows, per-district 67/25/7/85 (matches baseline); `wallB_defects_<district>.csv` × 4 present; histogram 117 + 55 + 12 = 184; tests 13/13 + regression 11/11 as reported; progress-log entry present; two error entries registered in `OpenUBEM_debug_References.md` (new chapter "wall-B second pass"); no file outside T03's ownership touched. **T03 accepted.** T01/T02 sign-off follows in a separate entry when executor #1's dry run over the 289 reports.

#### Director ruling — CP-1 (T01/T02 part) — 2026-09-08 13:35 — CP-1 complete

**T01/T02 audited and signed.** Gate on `partition_audit.passed` confirmed absent (`european_residential.py:1387` is `if best_effort_eligible:` only; no `best_effort_audit` reference remains). Side-car `partition_audit` carries `failures`, `gap_area_m2`, `overlap_area_m2`, `outside_area_m2` (6 references in `emit_eu11_layout_sidecars.py`). Tests re-run by the director: `test_eu_recut_95pct_2026_09_08.py -k "not dry_run"` 6 passed; `test_eu_s2_campaign.py` + `test_eu_collinear_ring_cleanup.py` + `test_eu_wallb_second_pass_2026_09_08.py` 41 passed; the dry-run test 1 passed in 17:02 (output kept in the outgoing session's scratchpad, table copied into the T02 entry). Files touched are the ones the T02 §What and dependency 9 name (viewer badge included); `european_nocore.py`, `main.py`, rules, thresholds untouched. Deviations (Counter subclass instead of 3-tuple; adapted test geometries; monkeypatched C5 case) accepted — none changes a published number.

**Dry-run result, offline, over the 289 rule-refused (D-EU-111 population):** emitted best-effort **204** (Madrid 52/75, Lyon 12/25, London 5/14, Bologna 135/175 — Bologna rows reconstructed without live HTTP, so its count is approximate until T05 prepares for real), still refused **85** (density > 12 per floor 21; hard checks C4 21 + C4/C11 2, C5 41). `audit_passed` 1 / `audit_failed` 203 among the 204 — the same pattern 4J measured on Bologna's ruled side-cars; recorded, not gated. **Expected T05 population effect:** wall C shrinks from 289 to about 85; wall B (184) unchanged per the T03b ruling above; wall A (585) is T04's.

**Both checkpoints of CP-1 are now in §8; the plan proceeds at T04 (T03b cancelled).** Outgoing manager hands over here; see `prompts/IMP_PROMPT.md` §8.

#### T04 — Neighbour imputation for the never-simulated (`D-EU-112`) — completed 2026-09-08

**Artifacts.** `scripts/run_eu_s2_district_campaign.py`: `_nearest_prepared_id` (`:679-696`, rung 2, `sindex`-backed), `_neighbour_field_mode` (`:699-715`, rung 3, per-type and all-type mode), `_neighbour_ladder_value` (`:718-737`, the generic three-rung ladder dependency 3 names, shared by every district), `_gb_straddle_containment` (`:740-751`, the GB straddle-older-band tie rule, factored out as its own pure function), `_gb_impute_rows` (`:754-858`, GB: calls the pinned `_gb_terrace_recovery_rows` for rung 1, then a second, independent full-`gdf` pass that re-derives every remaining candidate's own period fresh and applies rungs 2/3 to whatever is still missing — see Deviations), `_impute_es_fr_rows` (`:861-964`, ES/FR: replays `map_observed_building_to_tabula` read-only to learn which of type/year/storeys is missing, imputes only those fields, resolves the archetype directly through `select_tabula_archetype`), `_impute_it_rows` (`:961-…`, Bologna: only the census-section period is ever missing per `_it_rows`'s own always-resolvable type/storey defaults; reuses that default rather than a second live CTC/census HTTP round trip), `impute_from_neighbours` (`:1024-1042`, the district dispatcher named in dependency 3). `prepare()` (`:1045-…`): new `impute_from_neighbours_enabled: bool = True` parameter (named so it never shadows the module-level function it calls), replacing the old GB-only `recover_terrace_neighbours` gate; `rows = rows + recovered_rows` before the IDF-build loop; `imputation_provenance` threaded into every manifest row (`""` for observed rows); `imputation_records` folded into `excluded_buildings.csv` alongside the base-mapping and IDF-build exclusions. CLI (`:1212-…`): `--impute-from-neighbours` / `--no-impute-from-neighbours` (`argparse.BooleanOptionalAction`, default on), replacing `--recover-terrace-neighbours`. `tests/test_eu_recut_95pct_2026_09_08.py`: T04 section (`:280-…`) — 4 case tests (rung 1 touching-agree, rung 2 nearest-within-30m, rung 3 district-mode-when-isolated, GB straddle-neighbour-outside-set falls to the older band) against synthetic 2-3-building `GeoDataFrame`s with monkeypatched GB EPC CSVs, 1 pure unit test on `_gb_straddle_containment`, the 585-row oracle agreement test, the recovered-vs-585 measurement test, and one new completeness regression test added in this pass (see Deviations).

**Result — oracle agreement over the 585 never-simulated rows (`debugs/never_simulated_buildings_all_districts_2026-09-08.csv`).** Of 585, 539 rows carry `imputation_source ∈ {touching_prepared_neighbours_agree, nearest_prepared_neighbour_*}` (the other 46 are `district_mode_*`, out of this check's scope per the plan). Raw string equality of the code's `age_band` against `proposed_imputed_age_band`: **245 of 539 agree**, 294 disagree (8 of those 294 are rows the code did not recover at all). Every ES (0 of 6) and every IT (0 of 0) disagreement, and 1 of 2 FR disagreements, is fully explained by one exact mechanism: 6 ES + 1 FR buildings in the CSV are the already-known `IDF_ASSEMBLY_FAILED` engine failures (dependency 4: ES 6, FR 1) — they were never excluded from base mapping at all (they have complete data), so `impute_from_neighbours` correctly never touches them; the code reports no value where the CSV proposes one, exactly as dependency 4 specifies ("not imputed, ever"). One further FR row (`BATIMENT...0195_part0`, oracle `FR.07` vs code `FR.01`) and 97 GB rows are genuine numeric disagreements, but **normalizing the GB rows first removes nearly all of them**: GB's stored `age_band` is frequently an EPC-letter label (e.g. `"C|D"`, `"D|E|F"`, `"A"`) rather than a resolved TABULA period, because `_gb_row_outcome` writes `age_label or first` and `age_label` is non-empty whenever a certificate band exists — re-resolving each label through the same `_gb_age_decision_multi` the code itself uses (e.g. `"C|D"` → `GB.03`, `"A"` → `GB.01`) turns 335 of the 433 raw GB "disagreements" into exact matches. After that normalization: **433 of 531 recovered rows agree** (81.5%); **98 genuine value disagreements remain**, all but 1 in GB. Full disagreement list and the normalization script are in the outgoing session's scratchpad (not committed, per rule 9's "no new scripts unless this plan names them" — the finding is registered below, not the tooling).

**Result — recovered per district vs the 585 (`test_t04_recovered_vs_585`, printed).** ES-MAD-BERRUGUETE: 13 of 19 (6 already in base = the 6 ES `IDF_ASSEMBLY_FAILED`, 0 residual). FR-LYO-HAUTCOEURPENTES: 20 of 21 (1 already in base = the 1 FR `IDF_ASSEMBLY_FAILED`, 0 residual). GB-LDN-STDUNSTANS: 534 of 536 (0 already in base, 2 residual: 1 `IMPUTED_THEN_UNMAPPABLE_RESIDENTIAL_TYPE` — typology is not one of GB's three dependency-3 fields — and 1 `MISSING_OBSERVED_EPC_AGE_BAND_NO_PREPARED_NEIGHBOUR`). IT-BOL-GALVANI2: 9 of 9 (offline-reconstructed base, see Deviations). **Fleet: 576 of 585** enter the prepare, against the plan's "expected ≈ 570 of 585." The 9 not entering split exactly: 7 are the ES/FR `IDF_ASSEMBLY_FAILED` engine failures (6+1, dependency 4 — already excluded from base mapping too, so `impute_from_neighbours` never touches them, correctly) and 2 are the measured GB residual above. Bologna's 5 `IDF_ASSEMBLY_FAILED` do not reduce this count because they never appear among the 9 debug-CSV Bologna rows in the first place (all 9 recover) — a fact about how the director's CSV was built, not about the code.

**FINDING 268.** Two things, not one: (1) GB's stored `age_band` is sometimes an EPC-letter label and sometimes a resolved TABULA period depending on which code path wrote the row (`age_label or first` in `_gb_row_outcome`) — comparing it to anything downstream by raw string, as this oracle check and the director's CSV both do, produces mostly-spurious disagreements; re-resolving through `_gb_age_decision_multi` before comparing is required for a meaningful check. Recorded here because the director's CSV and the pipeline itself both do this, and a future consumer of `prepared_buildings.csv`'s `age_band` column for GB needs to know it is not always already a period token. (2) Even after normalizing that format gap, GB has 97 genuine value disagreements with the director's independent CSV. The most likely cause (not proven further, out of scope here): the CSV's `touching_prepared_neighbours`/`nearest_prepared_id` columns appear to have been measured against the 706-building `_delta_2026-09-07` prepared tree (which already includes the retired, GB-only `--recover-terrace-neighbours` pass's 255 buildings as valid neighbours), while `impute_from_neighbours` correctly scopes rung 1's neighbour pool to *this run's own* base mapping (451 raw `_gb_rows`, per dependency 3's literal "prepared" — i.e. prepared within this execution) and only re-recovers those 255 itself, one level down, inside the same call. Different "already prepared" universe at the moment of comparison, not a defect in either side against its own definition — reported per the plan's "a disagreement is a finding, not automatically a bug" rule, not fixed.

**Deviations.** (1) A real completeness gap was found and fixed during this task's own testing (present in the file when this session started, already corrected by the time this session's own edits landed — see git history for the exact change): `_gb_impute_rows`'s first draft classified "still needs rung 2/3" candidates only from `_gb_terrace_recovery_rows`'s own `.records`, but that pinned function's `_gb_parse_straddle_periods` regex recognises only the single-certificate `PERIOD_STRADDLE_<band>_<lo>_<hi>` shape and silently `continue`s (no log) on the multi-certificate `PERIOD_STRADDLE_DISJOINT_BANDS_*` / `_AMBIGUOUS_*` shape `_gb_age_decision_multi` also produces — measured at 159 of London's 791 raw candidates silently dropped (neither recovered nor excluded) before the fix, 0 after. The fix independently re-derives every remaining `gdf` row's own period rather than trusting `_gb_terrace_recovery_rows`'s exclusion bookkeeping, so it no longer depends on that function's exclusion-record completeness at all. `_gb_terrace_recovery_rows` itself is untouched (still pinned by `tests/test_eu_london_recovery_2026_09_07.py`, still 7 passed). (2) Added `test_t04_impute_from_neighbours_accounts_for_every_candidate` (not named by the plan) as a permanent regression guard for exactly this class of gap — dependency 5 requires `excluded_buildings.csv` to correctly record everything that remains excluded, and nothing in the plan's named tests would have caught a silent drop; it asserts, per district, that every `gdf` row outside the base mapping ends up in exactly one of {recovered, logged-excluded}, never neither. (3) IT/Bologna base rows for both new tests are reconstructed offline from `IT-BOL-GALVANI2_delta_2026-09-07/prepared_buildings.csv` with `year_built` re-derived as the first year of each row's own TABULA period (`_TABULA_PERIODS`, read-only) — same network-free precedent T02's dry run and T03's measurement both used; Bologna's true `_it_rows` requires live HTTP, forbidden by CLAUDE.md.

**Test status.** File total: 15 tests (2 T01, 5 T02 incl. the dry run, 8 T04: 4 case tests + 1 straddle-helper unit test + the oracle-agreement test + the recovered-vs-585 test + the completeness test added this pass). `tests/test_eu_recut_95pct_2026_09_08.py -k "not dry_run" -q`: **14 passed** (the 1 excluded is `test_t02_dry_run_best_effort_measurement`, unrelated to T04, already accepted at CP-1). Regression, unchanged: `tests/test_eu_s2_campaign.py` + `tests/test_eu_london_recovery_2026_09_07.py` + `tests/test_eu_collinear_ring_cleanup.py` + `tests/test_eu_wallb_second_pass_2026_09_08.py -q`: **48 passed**.

**Notes.** No traceback/runtime error was hit during this session's own work (the completeness gap in Deviation 1 was found by inspection and cross-checking, not by a failing assertion or exception), so nothing is registered in `OpenUBEM_debug_References.md` — there is no error string to quote. `--recover-terrace-neighbours` is fully retired; no remaining caller references it (checked: no test or script outside this file used the old flag or the old `recover_terrace_neighbours` parameter name). T03b remains cancelled per the CP-1 ruling; not reopened here. **STOP after T04 per the dispatch instruction — T05 not started.**

#### T05 — One re-emission, four districts in parallel, delta by hash — completed 2026-09-08

**Artifacts.** `scripts/run_eu_s2_district_campaign.py`: `compute_recut_simulate_list(out, district, evidence_root, baseline_tags)` (new function, after `prepare()`) — dependency decision 5's delta-by-hash logic did not already exist (checked first: `fleet.lst` was written unconditionally over every prepared building, `:1185-1186` pre-T05; no `recut_simulate_list`/`HASH_CHANGED`/`NET_NEW` writer anywhere in `scripts/`, confirmed by grep before writing new code, per the dispatch instruction). Reads `out/prepared_buildings.csv`, finds the newest earlier tree holding each building (`<district>_delta_2026-09-07` first, else `<district>_final_2026-09-07`, by trying `baseline_tags` in order against `evidence_root`), classifies every recut row as `HASH_CHANGED` (`idf_sha256` differs) or `NET_NEW` (no earlier row), writes `recut_simulate_list.csv` (`building_id, stem, reason`) and rewrites `fleet.lst` restricted to those stems. New CLI flag `--write-recut-simulate-list` (default off, so every other existing invocation of this script — EU-16/17/21 precedent, the T01-T04 unit tests — is unaffected) calls it right after `prepare()` in `main()`. `tests/test_eu_recut_95pct_2026_09_08.py`: T05 section appended — `_STOCK_2026_09_08` (fact 10 stock counts), `_T02_DRY_RUN_GAIN` (the T02 progress-log dry-run table), `_t05_recut_gates(district)` (reads baseline + recut `prepared_buildings.csv`, `recut_simulate_list.csv`, `fleet.lst`; computes G1-G6), `test_t05_recut_gates` (parametrised over the four `DISTRICTS`, skips if the recut tree is absent, prints the six lines, asserts 6 lines returned — no pass/fail assertion per gate, matching T05's "How to test": the director signs CP-2, not the executor).

**Execution.** Four `run_eu_s2_district_campaign.py --write-recut-simulate-list` processes launched at once as background OS processes (not a loop) into `EU-11/<D>_recut_2026-09-08/`, all four alive simultaneously (confirmed via `ps -ef`), no serial waiting between them. Completion order: GB-LDN-STDUNSTANS, FR-LYO-HAUTCOEURPENTES, ES-MAD-BERRUGUETE, then IT-BOL-GALVANI2 (Bologna, largest). 0 tracebacks in any of the four logs; the `intersect_match raised .../purging and retrying` and shapely buffer `RuntimeWarning` lines are the same benign, already-registered behaviour seen in every prior campaign run.

**Result — `recut_simulate_list.csv` per district.**
- ES-MAD-BERRUGUETE: 64 rows (51 `HASH_CHANGED`, 13 `NET_NEW`); `fleet.lst` 64 lines; `population_prepared` 1187 of 1194.
- FR-LYO-HAUTCOEURPENTES: 33 rows (13 `HASH_CHANGED`, 20 `NET_NEW`); `fleet.lst` 33 lines; `population_prepared` 529 of 530.
- GB-LDN-STDUNSTANS: 539 rows (5 `HASH_CHANGED`, 534 `NET_NEW`); `fleet.lst` 539 lines; `population_prepared` 1240 of 1242.
- IT-BOL-GALVANI2: 139 rows (135 `HASH_CHANGED`, 4 `NET_NEW`); `fleet.lst` 139 lines; `population_prepared` 1215 of 1220.
- Baseline for every district: `_delta_2026-09-07` (present for all four; the `_final_2026-09-07` fallback was never needed).

**Result — six gates, "N of M", per district (`test_t05_recut_gates -s`, verbatim):**
```
G1 regression (ES-MAD-BERRUGUETE): 1033 of 1033
G2 divided count (ES-MAD-BERRUGUETE): 1158 of 1085 expected minimum (PASS)
G3 imputed rows (ES-MAD-BERRUGUETE): 13 of 13
G4 side-car reason coverage (ES-MAD-BERRUGUETE): 29 of 29
G5 fleet/simulate/staged (ES-MAD-BERRUGUETE): fleet.lst=64, recut_simulate_list=64, idfs_staged=64 (equal); population_prepared 1187 of 1194
G6 unchanged-hash area byte-identical (ES-MAD-BERRUGUETE): 1123 of 1123

G1 regression (FR-LYO-HAUTCOEURPENTES): 459 of 459
G2 divided count (FR-LYO-HAUTCOEURPENTES): 515 of 471 expected minimum (PASS)
G3 imputed rows (FR-LYO-HAUTCOEURPENTES): 20 of 20
G4 side-car reason coverage (FR-LYO-HAUTCOEURPENTES): 14 of 14
G5 fleet/simulate/staged (FR-LYO-HAUTCOEURPENTES): fleet.lst=33, recut_simulate_list=33, idfs_staged=33 (equal); population_prepared 529 of 530
G6 unchanged-hash area byte-identical (FR-LYO-HAUTCOEURPENTES): 496 of 496

G1 regression (GB-LDN-STDUNSTANS): 685 of 685
G2 divided count (GB-LDN-STDUNSTANS): 1207 of 690 expected minimum (PASS)
G3 imputed rows (GB-LDN-STDUNSTANS): 534 of 534
G4 side-car reason coverage (GB-LDN-STDUNSTANS): 33 of 33
G5 fleet/simulate/staged (GB-LDN-STDUNSTANS): fleet.lst=539, recut_simulate_list=539, idfs_staged=539 (equal); population_prepared 1240 of 1242
G6 unchanged-hash area byte-identical (GB-LDN-STDUNSTANS): 701 of 701

G1 regression (IT-BOL-GALVANI2): 951 of 951
G2 divided count (IT-BOL-GALVANI2): 1174 of 1086 expected minimum (PASS)
G3 imputed rows (IT-BOL-GALVANI2): 4 of 4
G4 side-car reason coverage (IT-BOL-GALVANI2): 41 of 41
G5 fleet/simulate/staged (IT-BOL-GALVANI2): fleet.lst=139, recut_simulate_list=139, idfs_staged=139 (equal); population_prepared 1215 of 1220
G6 unchanged-hash area byte-identical (IT-BOL-GALVANI2): 1076 of 1076
```
All 24 gate cells (6 × 4) are `N of M` with `N == M` or, for G2, `N ≥ M` — zero regressions, zero coverage gaps, zero unequal fleet/simulate/staged counts, zero non-identical unchanged-hash areas.

**Test status.** New: `test_t05_recut_gates[ES-MAD-BERRUGUETE|FR-LYO-HAUTCOEURPENTES|GB-LDN-STDUNSTANS|IT-BOL-GALVANI2]` — 4 passed. Full file: `tests/test_eu_recut_95pct_2026_09_08.py -q` — **19 passed** in 1029 s (17:09, dominated by the pre-existing T02 dry-run test; 640 benign shapely warnings, same as the T02 entry). No regression suite re-run this pass (T05 touched only `compute_recut_simulate_list`/CLI flag, additive and off by default; T01-T04 code paths untouched).

**Deviations.** None from the plan's `What`/`How`. The delta-by-hash function is new code, as the dispatch instruction anticipated after confirming no existing implementation ("this logic may already exist... check before writing new code" — checked, absent, written).

**Concurrent change flagged, not authored here.** At report time, `git diff -- scripts/run_eu_s2_district_campaign.py` shows one small uncommitted hunk this session did not make: `_gb_row_outcome` (`:376-378`) changes GB's `age_band` from `age_label or first` to `first` and adds a new `epc_age_label` field — this is the exact fix `FINDING 268` (T04 entry above) called for, evidently in progress by another concurrent process/session, not this one. It landed in the working file after this session's four prepare subprocesses had already started (their Python interpreters had already imported the pre-change module), so it did **not** affect any T05 output reported here; `tests/test_eu_recut_95pct_2026_09_08.py -q` (19 passed, including all T04 tests) was run against the file in its current, partially-edited state and still passed. Not reverted, not committed — outside this task's file ownership (rule 12; only `scripts/run_eu_s2_district_campaign.py`, `tests/test_eu_recut_95pct_2026_09_08.py` and this plan doc are this task's files, and this hunk inside the first one is not this task's edit). Also observed, untouched by this session: an untracked `docs/docs_ACTIVE/europeanLocations/messages_GSSCanada/2026-09-08_OpenUBEM_to_4J_CP2_populations_freeze.md` (matches dependency decision 10 — director-authored, not the executor) and three untracked files under `IT-BOL-GALVANI2_delta_2026-09-07/`, `_final_2026-09-07/`, `_merged_2026-09-07/` (director/harvest activity, not read from or written to by this task — this task only read `_delta_2026-09-07/prepared_buildings.csv` from those trees).

**CP-2.** STOP. Six gates × four districts above, all green. Director to sign, tell 4J (dependency decision 10 — not done here), and release T06 (Speed, director-only). T06/T07/T08 not started.

#### Director audit — T04 — 2026-09-08 13:55

T04 is **accepted**; T05 is released. No checkpoint sits after T04, so this is an audit note, not a ruling.

**Re-derived independently by the director, not taken from the executor's report.** `tests/test_eu_recut_95pct_2026_09_08.py -k "not dry_run"`: **14 passed, 4 skipped, 1 deselected** — matches the entry above. The 4 skips are the T05 gate tests, each skipping with `"<D>_recut_2026-09-08 not prepared yet"` (`:597`); they are the correct state before T05 and must all run at CP-2. File scope: `git status --short -- scripts/ tests/ openubem/geometry/` shows the two owned files (`M scripts/run_eu_s2_district_campaign.py`, `?? tests/test_eu_recut_95pct_2026_09_08.py`); `openubem/geometry/european_residential.py` is also `M`, but its mtime is `2026-09-08 12:38`, before the T04 dispatch, so it carries T02's edit and not a T04 escape. Hard rule 5 is intact.

**Accepted with the honest residual.** Recovered **576 of 585**, above the plan's "expected ≈ 570 of 585". The 9 that do not enter split exactly as dependency 4 requires: 7 `IDF_ASSEMBLY_FAILED` engine failures (ES 6, FR 1) that were never excluded from base mapping and so are correctly never imputed, and 2 measured GB residuals (`IMPUTED_THEN_UNMAPPABLE_RESIDENTIAL_TYPE`, `MISSING_OBSERVED_EPC_AGE_BAND_NO_PREPARED_NEIGHBOUR`). Bologna's 5 `IDF_ASSEMBLY_FAILED` are absent from the debug CSV's 9 Bologna rows, so they do not reduce this count — a property of how that CSV was built, restated here so T08 does not double-count them against the 12.

**`FINDING 268` stands as reported, and is not re-opened before T08.** The oracle check is not a gate and its disagreements do not block T05: the plan's own wording is "a disagreement is a finding, not automatically a bug". Of 585 rows, 539 are in scope; after re-resolving GB's `age_band` through `_gb_age_decision_multi` (the format gap that is part (1) of the finding), **433 of 531 recovered rows agree** and **98 genuine value disagreements remain** (97 GB, 1 FR). The director accepts the executor's stated cause — the CSV measured "prepared" against the 706-building `_delta_2026-09-07` tree while the code scopes rung 1 to this run's own base mapping — as the most likely one, and rules that the **code's** definition is the correct one: dependency 3 says "prepared", and within a single prepare that can only mean prepared by that prepare. The CSV is not amended and the code is not changed. T08 must register `FINDING 268` in `STATE_european_locations_v5.md` §8 with both parts, and must not quote the CSV's `proposed_imputed_age_band` as an expected value anywhere.

**Deviation (2) is accepted as permanent.** `test_t04_impute_from_neighbours_accounts_for_every_candidate` is not named by the plan but is retained: it guards the exact class of defect the executor found (159 of London's 791 candidates silently dropped — neither recovered nor logged — because `_gb_parse_straddle_periods` only recognises the single-certificate straddle shape; 0 after the fix). Dependency 5 requires `excluded_buildings.csv` to account for every excluded building, and no plan-named test would have caught a silent drop. Deviation (3), offline reconstruction of the IT base rows, is accepted on the same grounds T02 and T03 were: Bologna's live path needs HTTP, which `CLAUDE.md` forbids in tests.

**Carried into T05 as gate conditions, not as new work.** G3 must show every non-baseline building carrying a non-empty `imputation_provenance` — the 576 recovered here are exactly that population, so G3 is the live re-measurement of this task. G5's `population_prepared` must be quoted as "N of 1,194 / 530 / 1,242 / 1,220". T05 stops at CP-2 regardless of outcome.

#### Director note — owner instruction: fix `FINDING 268` part (1) — 2026-09-08

The owner read the T04 audit and answered part (1) of `FINDING 268` with "can you solve it". **It is
now in scope**, as a new task **T05b**, to be dispatched after CP-2 is ruled and before T06a ships.

**What.** `_gb_row_outcome` (`scripts/run_eu_s2_district_campaign.py:376`) writes
`"age_band": age_label or first`, so a GB row's `age_band` is the EPC letter label (`"C|D"`, `"A"`)
whenever any certificate band exists, and the resolved TABULA period (`GB.03`) only when none does.
ES/FR/IT all write the resolved period (`:624`, `:656`, `:952`, `:1014`). GB is the only district
whose `age_band` column is not a period token, which is exactly what makes any downstream raw-string
comparison of that column spurious.

**Why it is safe.** The archetype is selected from `first`, not from `age_band`
(`record = _record_for_period(records, "GB", building_type, first)`, `:375`). `age_band` is a
reporting/grouping label only; no IDF, no `archetype_id`, no `conditioned_floor_area_m2`, and no EUI
depends on it. `idf_sha256` values must therefore be unchanged by this fix — that is the acceptance
test, not a hope. The `AGE_ORDER` filters in `form_eu_s2_c1_sample.py:53` and `form_eu_s3_sample.py:79`
read `scope_eu_s2.py`'s own census bands, not this column, so they are unaffected.

**Constraints for the executor.** Write the resolved period into `age_band` for GB and preserve the
EPC letter label in its own row key rather than discarding it; do not change `_MANIFEST_COLUMNS`
(`:62`); do not touch `_gb_age_decision_multi`, `_gb_terrace_recovery_rows`, or anything named by
hard rule 5. Then re-prepare **London only** into the same `GB-LDN-STDUNSTANS_recut_2026-09-08/`
tree and prove `idf_sha256` is identical for every building against the pre-fix tree, plus
`recut_simulate_list.csv` row-for-row identical. Any hash change is a defect, not a result.

**Part (2) of `FINDING 268` is not re-opened.** The 98 genuine value disagreements were ruled at
13:55 to be a difference of "prepared" universe, with the code's definition correct. T08 still
registers both parts, and still must not quote `proposed_imputed_age_band` as an expected value.

#### Director note — owner rulings on the 9 excluded buildings — 2026-09-08 14:25

The owner read the T04 audit's "9 left out" line and ruled on both halves.

**Ruling A — the 2 London buildings are excluded, final.** Verbatim: *"we can exclude them."* No
further imputation, ladder rung, or recovery attempt is authorised for
`IMPUTED_THEN_UNMAPPABLE_RESIDENTIAL_TYPE` and
`MISSING_OBSERVED_EPC_AGE_BAND_NO_PREPARED_NEIGHBOUR`. This is already the code's behaviour, so no
change is required; the ruling closes the question rather than opening a task. T08 states London as
`N of M` with these 2 named in the excluded list, and does not describe them as a shortfall.

**Ruling B — the 7 engine failures: the owner asked what it would take.** Verbatim: *"what do we
need to do it for these ones to solve them?"* The answer is now measured, not inferred, and it
corrects the T04 report's claim that the exception message is not on disk.

**The message *is* on disk in the recut trees.** `excluded_buildings.csv` carries a `detail` column
holding `str(exc)` (`scripts/run_eu_s2_district_campaign.py:1167`); the `_final_2026-09-07` trees
predate that column, which is why T04 could not find it. Lyon's single failure
(`BATIMENT0000000240880120_part0`) reads:

    IDF_ASSEMBLY_FAILED_RuntimeError,
    "interzone_vertex_mismatch_unresolved: mismatched=[(...12 cross-block ceiling/floor pairs...)]
     near_duplicate_vertex=True"

**Root cause, already registered, not a new defect.** This is the `FINDING 210` /
`D-EU-43` / `FINDING 254` family (`OpenUBEM_debug_References.md:1847`, `:1849`, `:1873`):
`geomeppy`'s `intersect_match` recomputes boundary vertices per surface in live floating point, so
the ceiling of storey *n* and the floor of storey *n+1* end up with different vertex counts.
`scripts/run_eu_s2_campaign.py:690-720` catches this: when the raw pair check
(`find_mismatched_interzone_pairs`) fires, the safety net
`_force_reroute_room_layout_to_one_zone_per_floor` is asked to collapse the building to one zone per
floor. For these 7 that net **declines by design**, for one of two reasons in
`openubem/idf/surfaces.py:688-696`: the reconstructed floor-0 union is multipart or degenerate
(`return False`), or it carries a genuine courtyard hole of `>= 1.0 m²` (`return False`). With the
mismatch still live and no reroute available, the build raises rather than shipping geometry that
EnergyPlus would fatal on. Losing the building is the *correct* outcome of that branch, not a bug.

**What it would take to solve them (the owner's question, answered).** There is exactly one proven
remedy, already demonstrated end-to-end once on a Lyon building of this class
(`cee45cbc2718154c`, `OpenUBEM_debug_References.md:1847`): run the reroute with the courtyard-hole
guard removed, i.e. fill the interior ring (`Polygon(footprint.exterior)`, the same fill the
function already applies unconditionally to sub-1 m² slivers). That building then ran on real
EnergyPlus 23.1.0 with `RC 0`, `0 Severe`, `0 Fatal`, and its zone count collapsed 29 → 8. So the
recipe is known and it works. Its three costs are:

1. **The courtyard is sacrificed.** The model treats the yard as interior volume, so the
   building's floor area and heated volume both grow. That is a modelling change, not a repair —
   it needs a decision id (`D-EU-113` is next free) and a disclosed `fallback_reason` token, and
   the affected rows must be named wherever their EUI is published.
2. **`openubem/idf/surfaces.py` is non-editable** (`D-EU-41`, and hard rule 5 here). The guard
   cannot be changed in place; the fix has to be a new opt-in branch inside
   `scripts/run_eu_s2_campaign.py` that reconstructs the filled footprint itself, plus the
   monkeypatch-free equivalent of the scratchpad driver used for `cee45cbc2718154c`.
3. **It only covers the courtyard sub-case.** The other decline path — a multipart or degenerate
   floor-0 union — is not fixed by filling a hole, and the decline reason is not currently
   recorded, so the split between the two causes across the 7 is unknown until it is instrumented.

**Director recommendation: do not do it in this arc.** 7 buildings of a 4,186-building stock is
0.17 %; `CLAUDE.md` is explicit that the last fraction of a percent is not worth the owner's time,
and the remedy buys those 7 only by changing what the building *is*. Recommend recording the recipe
and the cost here and in the debug references at T08, and shipping the recut with the 7 named. This
recommendation is put to the owner as the single decision of the next report; nothing is blocked on
it, because the recut does not depend on these 7.

#### Director note — T05 executor lost to a rate limit, compute survived — 2026-09-08 14:22

The T05 agent (`ae681c7a0f3a9c7bd`) terminated on an API session limit, **not** on a task failure.
The four `run_eu_s2_district_campaign.py` processes it launched are child processes of the shell,
not of the agent, and kept running: verified at 14:20 by `tasklist` (two live `python.exe` at
~550 MB) and by IDF mtimes advancing to the current second in both remaining districts.

State at 14:20 — London `1,240 of 1,240` IDFs and all six output files present (complete at 14:09);
Lyon `530 of 530` and all six files present; Madrid `512 of 1,194` still writing; Bologna
`460 of 1,220` still writing. **No re-dispatch of T05's compute is permitted** — a second launch
would race two writers into the same tree. The director waits on `summary.json` appearing in both
remaining districts (background watcher `b62bmvd30`), then runs the G1-G6 gates for CP-2.

**Baseline snapshot taken for T05b.** London's tree will be overwritten by the T05b re-prepare, so
`prepared_buildings.csv`, `recut_simulate_list.csv` and `gb_ldn_stdunstans_manifest.csv` were copied
to the session scratchpad (`t05b_baseline/*.prefix.csv`) at 14:22, before any fix is applied. The
T05b acceptance test compares against those three files; without them the "every `idf_sha256`
unchanged" proof is not runnable.

#### Director ruling — owner closes the 7 engine failures — 2026-09-08 14:30

Owner, verbatim: *"ok leave the 7 out"*. The director recommendation in the 14:25 note is adopted.
No courtyard-fill remedy is authorised, no decision id is opened for it, and `D-EU-113` stays free
for the next real decision. The `IDF_ASSEMBLY_FAILED_RuntimeError` population ships excluded and
named.

**Binding on T08.** Register the recipe and its three costs in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` as an extension of the existing `FINDING 210`
entry (one bullet, house format, `[OPEN]` prefix retained since the cause is known and deliberately
unfixed) — not as a new finding, because the root cause is already registered there. Correct the
same entry's standing claim that the `RuntimeError` message is not persisted: it is, in the
`detail` column of `excluded_buildings.csv` in every `_recut_2026-09-08` tree. The final table
states each district as `N of M` with these buildings inside the excluded count, and must not
describe them as recoverable.

#### Director amendment — T05b acceptance numbers measured — 2026-09-08 14:34

Measured on the pre-fix London recut manifest so T05b has a falsifiable target rather than a
description. `gb_ldn_stdunstans_manifest.csv`, 1,240 rows: **805 of 1,240** carry the resolved
TABULA period (`GB.01` … `GB.08`) and **435 of 1,240** carry the EPC letter label (`A`, `I`, `G`,
`C|D`, …). After the fix the counts must read **1,240 of 1,240 period-form, 0 of 1,240 letter-form**,
and simultaneously every `idf_sha256` identical to `t05b_baseline/prepared_buildings.prefix.csv`
and `recut_simulate_list.csv` row-for-row identical to `t05b_baseline/recut_simulate_list.prefix.csv`.
Three numbers, all three required; two out of three is a failed task.

#### Director ruling — CP-2 — 2026-09-08 14:41

**Verdict: PASS, all six gates in all four districts.** Re-derived by the director, not taken from
an executor report: `.venv/Scripts/python.exe -m pytest tests/test_eu_recut_95pct_2026_09_08.py -k
"t05_recut_gates" -q -s` → **4 passed, 15 deselected**, no skips (the four `not prepared yet` skips
of the T04 audit entry are now gone, which is itself the proof that all four trees exist).

The 24 measured lines, verbatim:

```
G1 regression (ES-MAD-BERRUGUETE): 1033 of 1033
G2 divided count (ES-MAD-BERRUGUETE): 1158 of 1085 expected minimum (PASS)
G3 imputed rows (ES-MAD-BERRUGUETE): 13 of 13
G4 side-car reason coverage (ES-MAD-BERRUGUETE): 29 of 29
G5 fleet/simulate/staged (ES-MAD-BERRUGUETE): fleet.lst=64, recut_simulate_list=64, idfs_staged=64 (equal); population_prepared 1187 of 1194
G6 unchanged-hash area byte-identical (ES-MAD-BERRUGUETE): 1123 of 1123
G1 regression (FR-LYO-HAUTCOEURPENTES): 459 of 459
G2 divided count (FR-LYO-HAUTCOEURPENTES): 515 of 471 expected minimum (PASS)
G3 imputed rows (FR-LYO-HAUTCOEURPENTES): 20 of 20
G4 side-car reason coverage (FR-LYO-HAUTCOEURPENTES): 14 of 14
G5 fleet/simulate/staged (FR-LYO-HAUTCOEURPENTES): fleet.lst=33, recut_simulate_list=33, idfs_staged=33 (equal); population_prepared 529 of 530
G6 unchanged-hash area byte-identical (FR-LYO-HAUTCOEURPENTES): 496 of 496
G1 regression (GB-LDN-STDUNSTANS): 685 of 685
G2 divided count (GB-LDN-STDUNSTANS): 1207 of 690 expected minimum (PASS)
G3 imputed rows (GB-LDN-STDUNSTANS): 534 of 534
G4 side-car reason coverage (GB-LDN-STDUNSTANS): 33 of 33
G5 fleet/simulate/staged (GB-LDN-STDUNSTANS): fleet.lst=539, recut_simulate_list=539, idfs_staged=539 (equal); population_prepared 1240 of 1242
G6 unchanged-hash area byte-identical (GB-LDN-STDUNSTANS): 701 of 701
G1 regression (IT-BOL-GALVANI2): 951 of 951
G2 divided count (IT-BOL-GALVANI2): 1174 of 1086 expected minimum (PASS)
G3 imputed rows (IT-BOL-GALVANI2): 4 of 4
G4 side-car reason coverage (IT-BOL-GALVANI2): 41 of 41
G5 fleet/simulate/staged (IT-BOL-GALVANI2): fleet.lst=139, recut_simulate_list=139, idfs_staged=139 (equal); population_prepared 1215 of 1220
G6 unchanged-hash area byte-identical (IT-BOL-GALVANI2): 1076 of 1076
```

**Fleet roll-up.** Prepared **4,171 of 4,186** (99.64 %): 1,187 of 1,194 · 529 of 530 · 1,240 of
1,242 · 1,215 of 1,220. Divided **4,054 of 4,171** against a baseline of 3,128 — Madrid 1,033 →
1,158 (+125), Lyon 459 → 515 (+56), London 685 → 1,207 (+522), Bologna 951 → 1,174 (+223). To
simulate at T06a: **775 buildings** (64 + 33 + 539 + 139), delta-by-hash.

**The 15 not prepared, named and classified** (each id verified absent from that district's
`prepared_buildings.csv`; `excluded_buildings.csv` blocker rows are stage blockers, not exclusions —
Madrid 20 rows → 7 lost, Lyon 21 → 1, London 794 → 2, Bologna 9 → 5):

- **13 engine failures**, all `idf_build` / `IDF_ASSEMBLY_FAILED_RuntimeError`, all the `FINDING 210`
  interzone-vertex family — Madrid `relation/12707193`, `relation/12803902`, `relation/12837456`,
  `relation/12876437`, `relation/12882211`, `relation/13430481`, `relation/5662802`; Lyon
  `BATIMENT0000000240880120_part0`; Bologna `29376`, `29695`, `30646`, `30810`, `32473`.
  **Correction to the earlier count in this log: the fleet total is 13, not 7 and not 8.** The 7 was
  a Madrid-only figure read from a superseded `_final_2026-09-07` summary; Bologna's 5 were not
  measurable until its prepare finished at 14:38. The owner's ruling of 14:30 (*"ok leave the 7
  out"*) is a ruling on this class, not on a count, and applies unchanged to all 13.
- **2 London data failures**, closed by the owner at 14:25 (*"we can exclude them."*):
  `relation/19609965` (`MISSING_OBSERVED_EPC_AGE_BAND`, then
  `MISSING_OBSERVED_EPC_AGE_BAND_NO_PREPARED_NEIGHBOUR`, then
  `IMPUTED_THEN_UNMAPPABLE_RESIDENTIAL_TYPE`) and `way/820000871`
  (`PERIOD_STRADDLE_DISJOINT_BANDS_A|B|C`, then `IMPUTED_THEN_UNMAPPABLE_RESIDENTIAL_TYPE`).

0.36 % of stock lost, against a plan target of 95 %. No remedy is authorised for either class.

**Signed.** T05 is closed. Order from here: (1) T05b, GB `age_band`, London-only re-prepare, three
acceptance numbers as recorded at 14:34; (2) T06a ships to Speed after T05b's hashes are proven
unchanged — shipping before it would stage IDFs the fix must not alter and would leave no way to
tell a fix defect from a ship defect; (3) the inherited Bologna/Lyon 2026-09-07 harvest tail is
director-only and runs in parallel (3 tasks still RUNNING at 14:40, 0 PENDING: `1311708_54`,
`1312355_14`, `1312355_81` — fewer than 32 tasks remain in the whole fleet, so the `%32` cap is
not binding and nothing is to be raised).

#### T05b — GB age_band carries the resolved TABULA period — completed 2026-09-08

**Artifacts.** `scripts/run_eu_s2_district_campaign.py:376-377` — `_gb_row_outcome`'s row dict now
writes `"age_band": first` (the resolved TABULA period already passed to `_record_for_period`) and
adds `"epc_age_label": age_label` as a new key, preserving the certificate letter label without
discarding it. `_MANIFEST_COLUMNS`/`MANIFEST_COLUMNS` (line 62) untouched.
**Deviations.** None to the fix itself. Operational: re-running into the existing
`GB-LDN-STDUNSTANS_recut_2026-09-08/` tree hit a pre-existing `FileExistsError` in `prepare()`
(`schedule_dir.mkdir()`, line ~1125, not `exist_ok`, unrelated to this fix — `stem` is a hash of
`building_id`, stable across the fix, so the per-building schedule folder from the pre-fix run
already existed). Deleted the stale output tree before re-running, per "it overwrites the existing
tree in place" — the pre-fix baseline was already snapshotted separately in scratchpad before this
task started, so nothing was lost. No script code was touched beyond the specified `age_band` edit.
**Test status.**
1. `age_band` form in `gb_ldn_stdunstans_manifest.csv`: 1240 of 1240 period-form, 0 of 1240
   letter-form. (Pre-fix: 805 period-form / 435 letter-form.)
2. `idf_sha256` vs. baseline, joined on `building_id`, both directions: 1240 of 1240 identical,
   0 missing, 0 extra.
3. `recut_simulate_list.csv` vs. `recut_simulate_list.prefix.csv`: row-for-row identical (539 rows).
**Notes.** Concurrent, unrelated diffs appeared under `IT-BOL-GALVANI2_final_2026-09-07/` during
this task's run — these are the director-only Bologna/Lyon 2026-09-07 harvest tail already noted
above as running in parallel, not touched by this task. Only `GB-LDN-STDUNSTANS_recut_2026-09-08/`
was written by this task's command.

#### Director audit — T05b — 2026-09-08 14:55

**Accepted.** All three acceptance numbers re-derived by the director from the files on disk, not
read from the executor's report:

```
(1) age_band period-form 1240 of 1240; letter-form 0 of 1240      (pre-fix 805 / 435)
(2) idf_sha256 identical 1240 of 1240; missing 0; extra 0; changed 0
(3) recut_simulate_list identical=True rows=539
(4) epc_age_label present in manifest columns: False
```

Line (4) is the director's own extra check, not asked of the executor: it proves `_MANIFEST_COLUMNS`
(`:62`) was not widened, so the preserved EPC letter label lives on the row dict only and no
downstream reader of the manifest sees a new column. The edit is
`scripts/run_eu_s2_district_campaign.py:376-377` — `"age_band": first` in place of
`"age_band": age_label or first`, plus `"epc_age_label": age_label`. GB now matches ES/FR/IT
(`:624`, `:656`, `:952`, `:1014`). `FINDING 268` part (1) is closed; part (2) stays ruled-not-a-defect.

**Deviation, accepted with a correction to record.** Re-running `prepare()` into an existing tree
raises `FileExistsError` on the per-building schedule folders, so the executor deleted the London
recut tree before re-running. Hard rule 6 is not breached — it names `_final_2026-09-07`,
`_delta_2026-09-07` and `_merged_2026-09-07` as read-only, and the recut tree is this plan's own
working output — and the 14:22 baseline snapshot made the deletion recoverable and the hash proof
runnable. The `FileExistsError` is nevertheless a real defect in a script that is meant to be
re-runnable: **binding on T08**, register it in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
in house format with the `[OPEN]` prefix (cause known, deliberately unfixed inside this arc), naming
`prepare()` and the content-hashed schedule directory as the cause. Do not fix it in this arc.

**Concurrency note.** Two processes not launched by T05b were live in its window and are visible in
its `git status`: `harvest_eu11_merged.py --district IT-BOL-GALVANI2` (started 14:47:45) writing
`IT-BOL-GALVANI2_final_2026-09-07/{it_bol_galvani2_manifest.csv,summary.json}` at 14:49:55, and a
`pytest tests/test_eu_recut_95pct_2026_09_08.py -q` from 14:39:31. Both are the director's §4.1 tail
and audit, not executor escapes; the executor was right to flag them rather than silently absorb
them. A second `harvest_eu11_district.py --district IT-BOL-GALVANI2 --tag delta_2026-09-07` launched
by the director at 14:51 collided with the running fetch and died on
`PermissionError: [WinError 32]` over the 840 MB `fetch_IT-BOL-GALVANI2_delta_2026-09-07.tgz`; it
was **not** retried, because the already-running merged harvest performs the same fetch. One writer
per tree, always.

**T06a is now unblocked.** London's staged IDFs are proven byte-identical to what CP-2 measured, so
shipping cannot confuse a fix defect with a ship defect.

#### T06a — four recut fleets shipped and submitted (director) — 2026-09-08 15:00

**Job ids.** `ES-MAD-BERRUGUETE` **1314028** (64 tasks) · `FR-LYO-HAUTCOEURPENTES` **1314065** (33) ·
`GB-LDN-STDUNSTANS` **1314066** (539) · `IT-BOL-GALVANI2` **1314067** (139). **775 tasks total**,
matching the four `recut_simulate_list.csv` counts ruled at CP-2 exactly. All four submitted between
the remote clock's `15:00:23` and `15:00:50` — the same minute, as dependency 6 requires. Every one
is `--array=1-N%32 --time=7-00:00:00 -p ps --cpus-per-task=1` (the last from the template); no
`%<32` throttle was used at any point and none is to be introduced later.

**Staging, restricted and verified twice.** Each fleet ships only what its simulate list names:
IDFs and per-building schedule directories selected by `fleet.lst` stem, plus the single `.epw`.
Local check before packing and remote check after extraction both returned
`fleet == idfs == schedules` — 64/64/64, 33/33/33, 539/539/539, 139/139/139. Tarballs are 2, 1, 5
and 3 MB: the `idfs/` directories in the recut trees hold 1,194 / 530 / 1,240 / 1,220 files, and
shipping them whole would have sent ~1 GB of schedules for buildings that are not to be re-run and
whose earlier results must be reused unchanged. The schedule reference in every IDF is
`../../schedules/<stem>/…`, which resolves from the template's `cd $FLEET_DIR/out/<stem>`; that is
why the per-stem directory, not a flat copy, is the correct unit.

**Runner.** `submit_recut.sbatch` in each fleet dir is a byte copy of the proven
`submit_fleet_t08_frgb_2026-09-07.sbatch` from that district's `_delta_2026-09-07` fleet — same
EnergyPlus 23.1.0 resolution, same `ExpandObjects` step, same output trimming that keeps
`eplusout.{eio,sql,end,err}` and `task.rc`. Nothing about the runner changed between 2026-09-07 and
this wave, so a difference in results cannot come from the runner. The template's baked
`--time=01:30:00` is overridden on the CLI by `--time=7-00:00:00`, per the standing rule.

**Saturation confirmed, not assumed.** `squeue -u o_iseri` immediately after submission: **32
RUNNING, 4 PENDING**. 32 is the hard account ceiling (`GrpTRES=cpu=32`), so this is full
subscription and there is nothing to raise. ETA is to be measured with `sacct` once the first tasks
complete — never estimated.

**Inherited tail, Bologna half closed.** Job `1311708` drained at **694 COMPLETED / 9 FAILED**
(failed tasks `_89 _96 _139 _181 _343 _352 _378 _386 _596`, to be classified at harvest).
`harvest_eu11_merged.py --district IT-BOL-GALVANI2` completed at 14:55:52 and wrote
`IT-BOL-GALVANI2_merged_2026-09-07/` (`it_bol_galvani2_manifest.csv`, `summary.json`), so all four
districts now have a 2026-09-07 merged tree for T06b's fallback chain to rest on. Job `1312355`
still had 2 tasks running at submission time; its harvest is still owed.
