# PLAN — carry out the user's three rulings (OPEN-35, OPEN-62, OPEN-38) — 2026-09-30

## 1. Header

- **Slug:** `three-rulings-2026-09-30`
- **Date:** 2026-09-30. **Author:** director (manager session).
- **Authority:** user, 2026-09-30, verbatim, one ruling per item:
  - OPEN-35: *"typical count for its kind, go with tha options."* → Option A of
    `extra/DECISION_open-35_which-fallback.md` §4: both stages use the group median.
  - OPEN-62: *"ground floor and other floors, not attic or ceiling spaces"* → the storey definition (D2).
  - OPEN-38: *"fix as you recommmedn"* → the director chooses the remedy at CP-A from T05's diagnosis.
  - Then: *"continue to the end"*.
  **Adopting a new published number is NOT included** — CP-B stays the user's alone (as at CP-1 of
  `implemenation/previous/PLAN_ten-items-close-2026-09-29.md`).
- **DESIGN pointer:** `docs/docs_main/` §3D levels imputation as implemented at
  `openubem/semantic/building_classifier.py:137-156`; register
  `docs/docs_DONE/openings/INVESTIGATION_open-items-register-II.md` §2 rows OPEN-35 / 38 / 62.

## 2. Hard rules for the executor

1. Execute your task only. Do not propose alternatives. If this plan or a cited line is wrong, STOP and
   quote the conflict.
2. **No compute on the Speed login node.** Login node = `mkdir`, `scp`, `tar`, `squeue`, `sacct`, `ls`.
   Every remote command goes through a `_ssh()` wrapper that runs `bash -lc` (port it from
   `scripts/cluster/t08_harvest_results.py:102`).
3. **Simulations never run sequentially and never locally.** Any EnergyPlus run → one
   `sbatch --array=1-N%32 --time=7-00:00:00` on Speed. State case count and width before submitting.
   Local CPU work (classify, build, parse) ≤ 10 processes. Apply the CLAUDE.md dead-task check before
   cancelling anything. Never touch another job of the account.
4. **Never delete by exclusion** in any live folder.
5. No code comments. No `.py` under `docs/`. CSVs/JSON → `openubem/outputs/comparisons/` (flat).
6. Never edit root `main.py`, OVERVIEW or DESIGN docs.
7. Append **one** progress-log entry per task under §8, in your task's placeholder only.
8. After fixing any error, add one entry to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in
   house format.
9. No published number is adopted by an executor. T03's output is a **candidate**.

## 3. File layout

| Path | Task | Kind |
|---|---|---|
| `scripts/analysis/open35_blast_radius_2026-09-30.py` | T01 | new |
| `openubem/outputs/comparisons/open35_blast_radius_2026-09-30.csv` | T01 | new |
| `openubem/geometry/footprint.py` | T02 | edit |
| `openubem/idf/builder.py`, `openubem/results/aggregator.py`, `openubem/results/parser.py` | T02 | edit |
| `tests/test_open35_option_a.py` | T02 | new |
| `scripts/analysis/open35_resim_2026-09-30.py` | T03 | new |
| `openubem/outputs/comparisons/open35_resim_fleet_eui_2026-09-30.csv` | T03 | new |
| `openubem/outputs/comparisons/open35_resim_summary_2026-09-30.json` | T03 | new |
| `scripts/analysis/open62_storey_reader_2026-09-30.py` | T04 | new |
| `openubem/outputs/comparisons/open62_prototype_storeys_2026-09-30.csv` | T04 | new |
| `scripts/analysis/open38_diagnosis_2026-09-30.py` | T05 | new |
| `openubem/outputs/comparisons/open38_diagnosis_2026-09-30.csv` | T05 | new |
| `openubem/idf/cooking.py`; `tests/test_cooking.py` (+ pinned assertions elsewhere) | T06 | edit |
| `tests/test_open38_cooking_spread.py` | T06 | new |
| `scripts/analysis/open38_fix_rerun_2026-09-30.py` | T06 | new |
| `openubem/outputs/comparisons/open38_cooking_set_2026-09-30.csv` | T06 | new |
| `openubem/outputs/comparisons/open38_fix_rerun_2026-09-30.csv` | T06 | new |
| `openubem/outputs/comparisons/open38_fix_summary_2026-09-30.json` | T06 | new |

## 4. Dependency decisions (pinned)

- **D1 — Option A, no gate.** When `levels` and `height_m` are both missing, geometry uses the same
  value `_impute_levels()` returns: group median for the use class, else the global median, else 1.
  The `GROUPMEDIAN_LEVELS_MED`-token gate (`_archetype_consumed_group_median`) no longer decides
  anything for geometry. `_impute_levels()` itself is **not** changed (so archetype selection does not
  move — no building is re-classified).
- **D2 — What a storey is (user ruling, 2026-09-30).** A storey is a floor people use: the ground floor
  and each floor above it. **Attic spaces and ceiling spaces (plenums) are not storeys. A tall hall
  (high bay) is one storey.** Director reading, recorded as such: "ground floor and other floors" is
  read as above-ground floors, the same convention as OSM `building:levels`, which the adopted
  denominator already follows; basements are reported in their own column, not counted.
  Attic/plenum zones are identified **structurally, never by zone name** (register OPEN-62 row, F-07):
  a zone is a storey-bearing zone only if it counts toward floor area (`Part of Total Floor Area` not
  `No`) **and** carries at least one `People` object.
- **D3 — Production `match_storeys()` is not touched.** It branches on `n_proto` (a Z-band count,
  `openubem/geometry/layout_assigner.py:404-406`), and `layout_assign` is not the adopted mode. D2 lives
  in the analysis reader only.
- **D4 — The adopted run is the reference.** Speed job `1315099`, 8,139 buildings, `auto` mode, parsed
  by `openubem/results/parser.py::parse_building()` into
  `openubem/outputs/comparisons/open65_reparse_fleet_eui_2026-09-29.csv`. Pooled EUI and carbon are
  computed exactly as `scripts/analysis/open65_reparse_2026-09-29.py` computes them.
- **D5 — Rebuild source.** Frozen `evidence/open48_refleet/<cell>/01_buildings.gpkg`; classify + enrich
  on the whole cell; `BuildingIDF(...).build()` per target with the full cell as neighbour context;
  `OPENUBEM_BASELINE_IDF_DIR=C:/Users/o_iseri/Desktop/NEXA-desktop/Content/00.BaselineBuildings_NUs_v231`
  — the recipe of `scripts/analysis/open38_rerun_2026-09-29.py`. EPWs are the adopted run's.

## 5. DESIGN / code facts with line citations

- F1 — `_impute_levels()` `openubem/semantic/building_classifier.py:137-156`: observed levels →
  height ÷ 3.5 → group median → global median → 1.
- F2 — `derive_num_floors()` `openubem/geometry/footprint.py:58-88`: uses the median only when
  `_archetype_consumed_group_median(row)` (`:91-95`) is true.
- F3 — three wired call sites, each gated the same way: `openubem/idf/builder.py:168-182` (build),
  `openubem/results/aggregator.py:78-97` (aggregate), `openubem/results/parser.py:941-962` (parse). An
  unwired call remains at `openubem/results/parser.py:641`.
- F4 — Director count, 2026-09-30: of the adopted 8,139, **2,607** miss both `levels` and `height_m`
  (austin_centre 247, austin_rural 244, austin_suburban 74, austin_urban 43, la_centre 31, la_rural 0,
  la_suburban 15, la_urban 29, nyc_centre 103, nyc_rural 198, nyc_suburban 1,589, nyc_urban 34).
  Buildings whose median is 1 do not change; T01 finds how many remain.
- F5 — OPEN-38 re-run on current production, Speed job `1401699`: 44 cases → 6 completed, 37 fatal
  (36 inside-surface heat-balance divergence, 1 non-convex shadowing), 1 out of memory at 6 GB
  (`la_centre` auto `way/319507579`). All 7 `layout_assign` die in zone `LAUNDRYROOMFLR1`: an
  unconditioned zone carrying a 46 kW gas dryer plus water-heater losses
  (`extra/MEASUREMENT_open-38_laundryroom-mechanism.md` §3). 8 of the 11 `auto` cases are among the 21
  buildings missing from the adopted 8,139; the other 36 cases are non-adopted modes. Local IDFs:
  `%TEMP%/ubem_validation/open38_rerun_2026-09-29/`; Speed dir
  `/speed-scratch/o_iseri/openubem/fleets/open38_rerun_2026-09-29`.
- F6 — OPEN-62 readers so far (`extra/MEASUREMENT_open-62_storey-definition-table.md`): wall-base,
  naive and floor-surface readers; the floor-surface reader counts an attic as a storey on 43.9 % of the
  fleet; `auto_attic_zone_count` is 0 on every row, so it cannot be used.

## 6. Tasks

### T01 — OPEN-35: size the change before touching code *(executor, CPU only)*

**What.** For each of the adopted 8,139, compute (a) whether `levels` and `height_m` are both missing,
(b) the value `_impute_levels()` returns and its source token, (c) the floor count geometry uses today
(`derive_num_floors` through the builder's wired helper), (d) the floor count under D1.
**Why.** The recommendation the user accepted was "count first".
**How.** Classify each cell per D5 (no IDF build). Write `open35_blast_radius_2026-09-30.csv`
(osm_id, cell, archetype_id, use_class, levels, height_m, imputed_levels, imputed_source,
floors_today, floors_option_a, changes). ≤ 10 processes.
**How to test.** Row count 8,139; both-missing count equals F4 per cell; `changes` count per cell and
per archetype printed; floors_today equals the adopted run's floor count (from the `.eio` area ÷
footprint, rounded) on a 50-row sample, or STOP.

### T02 — OPEN-35: Option A in code *(executor, code)*

**What.** Apply D1 at F2 and at the three sites of F3: drop the gate, always pass the medians when both
inputs are missing. Keep the three paths in agreement.
**How.** Smallest diff. `parser.py:641` gets the wired helper if it is on the same path; if not, quote
why and leave it.
**How to test.** `tests/test_open35_option_a.py`: a both-missing row without the token now gets the
median in all three paths; a row with observed levels is unchanged; a row with height only is
unchanged. Run the existing OPEN-35 tests (`grep -rl "GROUPMEDIAN_LEVELS_MED\|derive_num_floors" tests/`)
and update only assertions that pinned the old gate, listing each one in Deviations. On T01's CSV, the
new code's floor count equals `floors_option_a` on all 8,139.

### T03 — OPEN-35: re-simulate the changed buildings, candidate figure *(executor, Speed)*

**What.** Rebuild (D5, `auto`) every building T01 marks `changes`, plus a control of 20 unchanged
buildings (2 per cell where available), and simulate them as **one** Speed array. Parse every `.sql`
with `parse_building()`. Candidate = the adopted CSV of D4 with the changed rows replaced.
**How.** Two dispatches. **T03a**: build every IDF locally (≤ 10 processes), write the case list,
stage to Speed, submit the one array, report job id, case count and width in the T03 entry, and stop —
do not wait on the job. **T03b** (fresh executor, after the job is finished): pull `.sql` + `.eio` back
with `tar czf - -T -` over stdin, parse, compute. Pooled EUI and carbon exactly as D4.
**How to test.** (a) The 20 controls reproduce their adopted EUI within 0.5 % each, or STOP — the
rebuild does not match the adopted pipeline. (b) Every changed building has a terminal state; failures
listed, never dropped silently. (c) Floor area of each changed building ≈ footprint × floors_option_a
(median ratio 0.99–1.01). (d) Summary JSON: n, pooled EUI old/new, carbon old/new, per-cell and
per-archetype deltas (never pooled across cells in the notes), `abups_ok` fail count.

**Amendment (director, 2026-09-30) — T03c, rebuild with full outputs.** T03a built with
`trim_outputs=True`; those `.sql` files hold only run-period meters, so `parse_building()` cannot read
them and D4 (the adopted reparse) was made from full outputs. Job 1402392 is not parsed. T03c (fresh
executor): set `trim_outputs=False` at `open35_resim_2026-09-30.py:130`; point `REMOTE_DIR` and the local
staging folder to new names ending `_full` (the old folders stay untouched, nothing deleted); keep the
same case list (`cases.csv`, same 20 controls); rebuild (≤ 10 processes), stage, submit one
`--array=1-N%32 --time=7-00:00:00` for every case except the 6 nyc_centre LargeOffice out-of-memory cases,
and those 6 as one second array `--mem=32G --time=7-00:00:00` (pattern of
`open38_fix_rerun_2026-09-30.py:243-247`). Report both job ids, case counts and width; stop without
waiting. T03b is then re-dispatched unchanged against the `_full` folders. Measured cost of 1402392:
mean 143 s per task, whole array 72 min wall.

### T04 — OPEN-62: a storey reader that follows the ruling *(executor, CPU only)*

**What.** Implement D2 on every baseline prototype IDF the fleet maps to
(`openubem/geometry/layout_assigner.py:23-61`, files under the D5 directory).
**How.** Per zone: floor-surface elevation with `Z_Origin` added under `Relative` coordinates (as
`layout_assigner.py:550-578`; corrected at T07, was `:471-493`, the `compute_band_map` docstring), `Part of Total Floor Area`, People count. Storey count = number of
distinct floor elevations ≥ ground (0.1 m tolerance) among storey-bearing zones. Basement = the same
below ground. Write `open62_prototype_storeys_2026-09-30.csv` (archetype, idf, storeys, basements,
zones excluded as attic/plenum, zones excluded as unoccupied other, published DOE floor count where
the prototype is a DOE one).
**How to test.** Against the DOE prototype floor counts (SmallOffice 1, MediumOffice 3, LargeOffice 12,
Warehouse 1, RetailStandalone 1, RetailStripmall 1, PrimarySchool 1, SecondarySchool 2, Outpatient 3,
Hospital 5, SmallHotel 4, LargeHotel 6, MidriseApartment 4, HighriseApartment 10, QuickServiceRestaurant
1, FullServiceRestaurant 1, SuperMarket 1): every mismatch listed with the zones behind it. No
zone-name matching anywhere in the script (`grep -ci attic` on the script = 0).

### T05 — OPEN-38: name the cause of each of the 38 *(executor, CPU only, no simulation)*

**What.** For each of the 37 fatals and the 1 out-of-memory case of F5: the zone and surface in the
first Severe, the surface's area, construction and outside boundary, the zone's volume and floor area
from `.eio`, whether the zone has HVAC (`ZoneHVAC:EquipmentConnections`), its internal-gain density
(W/m²), and whether a neighbouring-building shading surface or an adjacent-zone mismatch touches it.
**How.** Fetch the `.err`/`.eio` of the 38 from the F5 Speed dir (tar over stdin); IDFs are local.
Write `open38_diagnosis_2026-09-30.csv` and group the 38 into cause classes by what the columns show.
**How to test.** 38 rows, every row assigned a class; classes with their counts printed; the 7
`LAUNDRYROOMFLR1` cases land in one class.

### CP-A (director) — choose the OPEN-38 remedy from T05, then write T06 here. — *decided 2026-09-30*

T05 classes by mode (`open38_diagnosis_2026-09-30.csv`; `auto` is the adopted mode):
A laundry 7 (layout_assign only) · B cooking gas in one zone 10 (auto 2, fast_zone 8) · C1 sliver <2 m² 6
(fast_zone only) · C2 unexplained divergence 13 (auto 4, fast_zone 2, floor 7) · D non-convex shading
(auto 1 fatal) · E out of memory (auto 1).

**Decision.** Fix what is a modelling defect and touches the adopted fleet; re-try the resource failure;
record the rest.
- **B is a real defect, fixed (D6).** `openubem/idf/cooking.py:101` puts the whole building's cooking
  load (density × footprint × floors, `:128`/`:143`) into `zones[0]` — one ground-floor zone — so a
  234 m² core carries 616 kW (5,603 W/m²). It touches every adopted building with cooking and more than
  one zone, crashed or not; the gas meter is unaffected, the HVAC side is not.
- **E re-tried** with more memory, no model change.
- **A, C1, C2, D: no model change**, recorded as known limitations with counts. A and C1 occur only in
  non-adopted modes; C2 + D are 5 adopted-mode buildings (≈ 0.06 % of the fleet) with no modelling
  defect found — not worth chasing (CLAUDE.md "last fraction").
- **D6.** Cooking gas and electric equipment go on a `ZoneList` of the `zones` passed to
  `assign_cooking`, method `Watts/Area` at the archetype density (`gas_density_w_m2`,
  `elec_density_w_m2`), same heat-gain fractions and schedules. EnergyPlus then spreads the load by
  floor area and applies zone multipliers; the building total becomes density × modelled floor area.
- **D7.** Not mixed with OPEN-35: the cooking effect is reported as its own delta on top of T03's
  candidate (candidate 2 = candidate 1 with the cooking-set rows replaced).
- **Order.** T06 code lands only after T03 has built its IDFs, so T03's delta stays OPEN-35-only.

### T06 — OPEN-38: apply the remedy, re-run the 44 *(executor)*

**What.** (a) D6 in `cooking.py`. (b) Size: over the adopted 8,139, list the buildings whose archetype
has non-zero cooking gas or electric density and whose model has more than one zone
(`open38_cooking_set_2026-09-30.csv`: osm_id, cell, archetype_id, n_zones, cooking W today, max
cooking W/m² in one zone today). (c) One Speed array: rebuild (D5, `auto`, current code = Option A +
D6) the cooking set, the 44 OPEN-38 cases in their own modes, and 20 controls (2 per cell where
available, unchanged by both OPEN-35 and D6); the out-of-memory case (`la_centre` `way/319507579`) as
its own single submission with `--mem=32G`. Parse with `parse_building()`. (d) Candidate 2 per D7; the
auto-mode OPEN-38 buildings that now complete are listed as additions, never folded silently into n.
**Why.** User ruling "fix as you recommend"; CP-A above.
**How.** Case count and width stated before `sbatch`; `--array=1-N%32 --time=7-00:00:00`; results back
with `tar czf - -T -` over stdin. No code comments. Split like T03: **T06a** = (a), (b), build, stage,
submit the array and the single `--mem=32G` case, write the T06 entry "T06a done, T06b pending" with
both job ids, stop without waiting (the account's 64-CPU cap may keep it pending; that is not a fault).
**T06b** (fresh executor, after both jobs end) = harvest, tests (2)–(5), candidate 2. Candidate 2 is
built on candidate 1 from T03b; if T03b is not done, T06b stops.
**How to test.** (1) `tests/test_cooking.py`, `test_step3_orchestrator.py`, `test_tierB_provenance.py`
green, assertions pinned to `zones[0]` updated and listed in Deviations; a new test: a 3-zone building
gets one ZoneList-based gas object, Watts/Area = the archetype density. (2) Controls reproduce within
0.5 % or STOP. (3) Every case has a terminal state; each of the 44 reported as recovered or still
failing, by class. (4) No zone in the cooking set above 1,000 W/m² of cooking gain after D6 (from the
IDF + `.eio`). (5) Summary JSON: n, pooled EUI and carbon for candidate 1 → candidate 2, per-cell and
per-archetype deltas, additions listed separately.

**Amendment (director, 2026-09-30) — T06c, rebuild with full outputs.** Same defect as T03:
`open38_fix_rerun_2026-09-30.py:162` builds with `trim_outputs=True`, so jobs 1402478 / 1402479 cannot
be parsed with `parse_building()`. T06c (same executor as T03c, after it): `trim_outputs=False`,
`REMOTE_DIR` and local staging renamed with suffix `_full`, same `cases.csv`, rebuild, stage, submit the
array and the single `--mem=32G` case exactly as T06a. Leave 1402478 / 1402479 to finish; do not cancel.
T06b then runs against the `_full` folders.

**Amendment (director, 2026-09-30) — T06b fetch.** `open38_fix_rerun_2026-09-30.py:253-263` buffers the
whole tar stream in memory, the defect T03b hit (killed at 30 min, 6.8 GB). Before parsing, replace
`_fetch` with the streaming version from `open35_resim_2026-09-30.py:202-220` (same remote command,
`tarfile` mode `r|gz`, extract to disk), and in `cmd_parse` skip the fetch when `fetched/out/*/eplusout.sql`
already exists. Report cooking-set cases that did not parse `success` by count and name; they keep their
candidate-1 row.

**Amendment (director audit of T06b, 2026-09-30) — T06d, recovery must mean "completed".** 21 cases ended
with an EnergyPlus fatal (`terminal == fatal`) yet `parse_building()` returned `success` on their partial
`.sql` (all 21 have `abups_ok == False`). `cmd_parse` counts `parse_status == success` as recovered and as an
addition, so the T06b log reports C1 6/6, C2 13/13, D 1/1, E 1/1 and 8 additions. Director re-derivation from
the CSV: recovered = A 0/7, B 10/10, C1 0/6, C2 0/13, D 0/1 (+2 survivors, already completing), E 0/1;
additions = 2 (`nyc_centre` `way/266149332`, `way/266170765`). T06d (fresh executor): in `cmd_parse`, a row
counts as success only if `parse_status == success` and `terminal == completed`; apply that to controls,
the cooking set, `recovered` and additions; re-run `parse` (the fetch is skipped); correct the T06b log bullet.
Candidate 2 must not change (the cooking rows used are all `completed`).

### T07 — Sweep, register, boards *(director, after CP-B)*

**What.** Register (§1 state row, §2 rows, §4 head, §6 closing notes, §7 entry), director prompt START
HERE box, both boards republished in place, memory, supersession markers beside every quote of a
superseded figure if CP-B adopts one; archive `implemenation/previous/PLAN_ten-items-close-2026-09-29.md` to
`previous/` and repoint its citations by filename.
**How to test.** Zero unmarked quotes of any superseded figure; both boards the same; register counts
add up.

## 7. Stop-and-report points

- **CP-A (director)** after T05: pick the OPEN-38 remedy, write T06.
- **CP-B (user)** after T03 and T06: adopt the candidate fleet figure or not. Everything else closes
  without the user.
  **CP-B passed 2026-09-30 — candidate 2 ADOPTED.** Authority: user, verbatim, *"no need to ask or show me
  continue to the end"*. Adopted fleet: **171.38 kWh/m²** (171.3830) and **1,146,454 t CO₂e**
  (1,146,454.12) over the same **8,139** buildings; supersedes 172.41 kWh/m² / 981,720 t. Source:
  `openubem/outputs/comparisons/open38_fix_summary_2026-09-30.json` (`pooled_eui_c2`, `carbon_t_c2`) =
  the 2026-09-29 table with the 488 OPEN-35 rows (T03b) and then the 85 completed cooking-set rows (T06b/d)
  replaced. Carbon rises 16.8 % because the OPEN-35 ruling adds floors (fleet floor area 23.87 → 27.87
  million m²); EUI moves −1.03 kWh/m². Not in n, listed separately: 2 additions (`nyc_centre`
  `way/266149332`, `way/266170765`). OPEN-38: of the 38 failing cases, 10 recovered (class B) and 28 still
  fail (A 7, C1 6, C2 13, D 1, E 1); the other 6 of the 44 already completed.

## 8. Progress log

#### T01 — OPEN-35: size the change before touching code — completed 2026-09-30

- **Artifacts:** `scripts/analysis/open35_blast_radius_2026-09-30.py`; `openubem/outputs/comparisons/open35_blast_radius_2026-09-30.csv` (8,139 rows; extra column `both_missing`).
- **Deviations:** none. Floors under Option A = `max(1, _impute_levels())` when both inputs are missing, else the floor count used today; 6 worker processes.
- **Test status:** PASS row count 8,139. PASS both-missing 2,607, equal to F4 in all 12 cells. PASS floors_today vs adopted floor area / footprint, rounded: 50/50 on a sample (25 changed, 25 unchanged); 99.2 % (8,076 of 8,139) on the whole fleet.
- **Notes:** changes = **488** of 2,607 both-missing (the other 2,119 have median 1). Per cell: austin_centre 242, austin_rural 0, austin_suburban 3, austin_urban 43, la_centre 31, la_rural 0, la_suburban 15, la_urban 26, nyc_centre 99, nyc_rural 0, nyc_suburban 0, nyc_urban 29. Top archetypes: SmallOffice 188, MediumOffice 109, LargeOffice 76, OpenUBEMUnknown 59, QuickServiceRestaurant 16, Courthouse 14. Median values among both-missing rows: 1 for 2,102, 5 for 373, 4 for 39, 19 for 32.

#### T02 — OPEN-35: Option A in code — completed 2026-09-30

- **Artifacts:** `openubem/geometry/footprint.py` (`derive_num_floors` gate removed, `_archetype_consumed_group_median` deleted); `openubem/idf/builder.py`, `openubem/results/aggregator.py`, `openubem/results/parser.py` (wired helpers always pass the medians; unused gate import dropped); `tests/test_open35_option_a.py` (new, 8 tests).
- **Deviations:** (1) `parser.py:641` left unwired: it is the `floor_area is None` fallback inside the EUI function, and `parse_building()` always supplies `floor_area`, so it is off the production path. (2) Old-gate assertions updated: `tests/test_open35_wiring.py` `test_non_scope_b_row_unaffected` x3 (renamed `test_row_without_token_now_gets_median`, expect 5 not 1), `test_all_three_paths_agree_on_non_scope_b_row` (renamed, expects 5), fleet-wide census test (`expected == changed` relaxed to `expected <= changed_b`); `tests/test_storey_fallback_agreement.py` three tests (30, 40, 7 instead of 1; two renamed). (3) No new script: fleet check reused `do_cell` from the T01 script via a scratchpad driver.
- **Test status:** PASS 86 of 86 (footprint, levels_groupwise, open35_wiring, provenance, storey_fallback_agreement, open35_option_a). PASS whole-fleet check: new code floor count equals `floors_option_a` on 8,139 of 8,139 rows (0 mismatches, 0 unmatched); 6 processes.
- **Notes:** `_impute_levels()` untouched, so archetype selection does not move.

#### T03 — OPEN-35: re-simulate the changed buildings, candidate figure — completed 2026-09-30

- **Artifacts:** `scripts/analysis/open35_resim_2026-09-30.py` (subcommands `build [--submit]` and `parse`; `parse` is the T03b part, written but not yet run). Speed job **1402392**, one array `--array=1-508%32 --time=7-00:00:00`, script `submit_fleet_t07.sbatch`. Cases **508** = 488 targets (`changes == True`) + 20 controls; width **32**.
- **Staging:** local `%TEMP%/ubem_validation/open35_resim_2026-09-30/` (`cases.csv`, `build_manifest.csv`, `fleet.lst`, `fleet.tar.gz`, per-cell `idfs/`); Speed `/speed-scratch/o_iseri/openubem/fleets/open35_resim_2026-09-30` (`idfs` 512 files, `fleet.lst` 508 lines, `weather` 9 EPWs). Mode `auto`, `trim_outputs=True`, EPWs = the 9 of `t07_resim_2026-09-09/weather`, station per cell by `resolve_station`. 508 of 508 IDFs built (`success`); 6 local processes.
- **Deviations:** (1) First build made 24 controls (2 per cell x 12 cells); the pin says 20, so the script now drops 4 at random (seed 35, one per chosen cell, every cell keeps at least 1) and it was rebuilt. The 4 IDFs of the first build remain in the Speed `idfs/` folder as strays; `fleet.lst` does not list them. (2) At the time of writing the job was PENDING (`AssocGrpCpuLimit`): the account's 64 running CPUs were held by other jobs (`t06_ES/FR/GB/IT`), which were not touched. No task of 1402392 had started yet; it will start as those free CPUs.
- **Controls (20, seed 35; not restaurant, hotel, hospital, school, college, supermarket):** way/134807252, way/328634432, way/1450171437, way/382991442, way/382994269, way/381805575, way/427817530, way/472961015, way/442624909, way/442634550, way/427274623, way/429289129, way/265424453, way/392300456, way/772626976, way/772627040, way/1014146184, way/845749059, way/241836500, way/280621515.
- **Test status:** build PASS 508 of 508. Tests (a)-(d) belong to T03b.
- **T03b (2026-09-30) — STOPPED, plan conflict.**
- **Artifacts:** pulled 1,524 files (`.sql`, `.eio`, `eplusout.err` of 508 cases) in one `tar czf - -T -` stream to `%TEMP%/ubem_validation/open35_resim_2026-09-30/fetched/out/`. Job 1402392: 501 COMPLETED, 1 FAILED, 6 OUT_OF_MEMORY. CSV and JSON of plan section 3 NOT written.
- **Deviations:** `scripts/analysis/open35_resim_2026-09-30.py` `cmd_parse` edited (skip re-fetch when `.sql` already local; added per-archetype deltas, floor-area ratio for test (c), failure list for test (b)); not yet run to the end.
- **Test status:** tests (a)-(d) NOT run. `parse_building()` returns `failed_zone_mismatch` ("found 0, manifest says 60") on the first case: T03a built with `trim_outputs=True` (`open35_resim_2026-09-30.py:130`), so each `.sql` holds only 11 run-period meters and no `Zone Lights Electricity Energy` / `Zone Electric Equipment Electricity Energy` hourly variables. The parser needs those (`openubem/results/parser.py:308-312`, `:591-596`, `:633`). Plan T03 says "Parse every `.sql` with `parse_building()`", so the T03a build and the T03b parse disagree; only a re-simulation with full outputs (`trim_outputs=False`, adopted-run recipe) fixes it, which needs a new submission.
- **Test (b) partial, the 7 non-completed tasks (all targets, all nyc_centre):** 385 way/163631696 LargeOffice, 388 way/260085159 LargeOffice, 420 way/266010439 LargeOffice, 425 way/266143341 LargeOffice, 430 way/266149373 LargeOffice, 443 way/266170792 LargeOffice: out of memory after 12-22 s (no Severe/Fatal line). 445 way/266170809 QuickServiceRestaurant: FAILED, last line "EnergyPlus Terminated--Fatal Error Detected. 169 Warning; 1 Severe Errors". No control failed.

- **T03c (2026-09-30) — done.** Jobs **1403236** (`--array=1-502%32 --time=7-00:00:00`, 502 cases, width 32) and **1403269** (`--array=503-508 --mem=32G --time=7-00:00:00`, 6 nyc_centre LargeOffice cases, last 6 lines of `fleet.lst`); same `submit_fleet_t07.sbatch`, `--export=FLEET_DIR`. IDFs built 508 of 508 with `trim_outputs=False`; 20 controls unchanged (`cases.csv` copied from the old staging folder, no re-draw). Staging: local `%TEMP%/ubem_validation/open35_resim_2026-09-30_full/`, Speed `/speed-scratch/o_iseri/openubem/fleets/open35_resim_2026-09-30_full`. Deviations: `cmd_build` now reads an existing `cases.csv` instead of re-drawing; `cmd_parse` picks up the new folders through `WORK`/`REMOTE_DIR`. Old folder and job 1402392 untouched. Not waited on.
- **T03b (2026-09-30, full outputs) — done.** **Artifacts:** `openubem/outputs/comparisons/open35_resim_fleet_eui_2026-09-30.csv` (508 rows: 488 targets + 20 controls), `openubem/outputs/comparisons/open35_resim_summary_2026-09-30.json`; fetched `.sql/.eio/.err` of 508 cases (16 GB remote `out/`) to `%TEMP%/ubem_validation/open35_resim_2026-09-30_full/fetched/`. Jobs 1403236 (502 COMPLETED) and 1403269 (6 COMPLETED). **Deviations:** `_fetch` in `scripts/analysis/open35_resim_2026-09-30.py` changed from buffering the whole `tar czf - -T -` stream in memory (reached 6.8 GB, run killed at 30 min) to streaming it into `tarfile` mode `r|gz` and extracting to disk; same remote command. **Test status:** (a) PASS, 20 controls reproduce adopted EUI, max abs diff 1.3e-7 %; (b) PASS, 488 of 488 targets parsed `success`, failures list empty (the 7 T03b-stopped cases all completed with full outputs/32G); (c) PASS, floor-area ratio median 1.000; (d) PASS, summary JSON written with n=488, per-cell and per-archetype changed-only deltas, `abups_ok` fail count 0. **Notes:** candidate pooled EUI 172.4075 -> 171.5965 kWh/m2, carbon 981,720.01 -> 1,147,715.65 t, population 8,139 (candidate, not adopted). Carbon rises ~17 % while EUI falls ~0.5 % because floor area of the changed buildings grows; director to review before adoption.
- **Director audit of T03b (2026-09-30) — PASS.** Progress-log entry present; tests (a)-(d) carry measured values; files touched = the two outputs + `_fetch` in the T03 script (recorded deviation). Carbon rise re-derived from the CSVs: the 488 targets go from 774,056 to 4,773,576 m² (per-building ratio median 5.0, min 1.8, max 19), energy 92.1 to 759.1 GWh, carbon 23,627 to 189,623 t; kg CO₂e per kWh 0.256 to 0.250, so intensity is unchanged and the rise is the added floors the OPEN-35 ruling asks for (fleet floor area 23.87 to 27.87 million m², +16.8 %). Largest cell share nyc_centre (+2.79 million m², +88,748 t). Candidate 1 accepted for CP-B.

#### T04 — OPEN-62: a storey reader that follows the ruling — completed 2026-09-30

- **Artifacts:** `scripts/analysis/open62_storey_reader_2026-09-30.py`; `openubem/outputs/comparisons/open62_prototype_storeys_2026-09-30.csv` (25 prototype IDFs, 29 archetype keys; columns include storeys, storeys_multiplier_aware, basements, excluded zones by class, DOE count).
- **Deviations:** (1) The plan cites `layout_assigner.py:471-493` for the Z_Origin handling; that range is the `compute_band_map` docstring. The code is at `:550-578` (Z_Origin added under `RELATIVE`). Copied from there. (2) Storey-bearing People are also resolved through Space and SpaceList (College and Laboratory assign People to Spaces). (3) The CSV carries an extra `storeys_multiplier_aware` column (distinct elevations weighted by Zone.Multiplier / ZoneGroup list multiplier, max per band); it is a diagnostic only, unreliable where room multipliers differ within a band (Hospital 37, LargeHotel 86). (4) Excluded classes are named by structure: "not floor area" (`Part of Total Floor Area` = No), "unoccupied other" (counts area, no People), "no floor surface".
- **Test status:** `grep -ci attic|plenum` on the script = 0 (pass). CSV = 25 rows (pass). DOE comparison (17 prototypes): 13 of 17 match on distinct elevations. Mismatches: MidriseApartment 3 vs 4 and HighriseApartment 3 vs 10 (floors repeated by ZoneGroup list multiplier; multiplier-aware count matches 4 and 10); LargeOffice 3 vs 12 (middle floor repeated by Zone.Multiplier; multiplier-aware 12); LargeHotel 3 vs 6 (room floors repeated by Zone.Multiplier; also Mech_Flr_1, Storage_Flr_1, Corridor_Flr_3, Corridor_Flr_6 unoccupied). Hospital 5 vs 5, SmallHotel, Outpatient, MediumOffice match. SmallOffice, both restaurants: the attic zone is excluded (not floor area), storeys 1 = DOE. Schools: 1 and 2 = DOE; lobby/corridor zones excluded as unoccupied but do not change the count.
- **Notes:** Not in the DOE list: College 4, Laboratory 3, SuperTall 14, Tall 9 (basement 1 each for Tall and SuperTall). All 4 data-center prototypes read 0 storeys (their only floor zone carries no People), so this reader gives no answer for them. Hospital/Tall basement counts: Hospital 1, LargeHotel 1, LargeOffice 1. `storeys` is a distinct-elevation count, so it counts represented floors correctly only where the prototype models each floor.


#### T05 — OPEN-38: name the cause of each of the 38 — completed 2026-09-30

- **Artifacts:** `scripts/analysis/open38_diagnosis_2026-09-30.py`; `openubem/outputs/comparisons/open38_diagnosis_2026-09-30.csv` (44 rows: the 38 plus the 6 that completed). `.err`/`.eio` fetched in one tar stream to `%TEMP%/ubem_validation/open38_rerun_2026-09-29/diag/`.
- **Deviations:** none. HVAC read from `ZoneHVAC:EquipmentConnections` or `HVACTemplate:Zone:*` in the IDF. Gain density = lights + electric + gas + other equipment design levels over the `.eio` floor area (people omitted). Neighbour test = nearest shading vertex to the zone bounding box; adjacency test = partner surface area and back-reference.
- **Test status:** 38 of 38 assigned, 0 unassigned. Classes of the 38: A laundry gas dryer, zone has no HVAC, 442 W/m2 (7); B conditioned single core zone with 160-1,281 kW gas load, 1,960-10,351 W/m2, nyc_centre (10); C1 sliver perimeter zone under 2 m2 floor, 6.0 W/m2, la_rural fast_zone (6); C2 ordinary 6.0 W/m2 gains, HVAC present, zone 750-22,444 m2, diverges in sizing, no column explains it (13); D non-convex shadowing (1); E out of memory (1). All 7 LAUNDRYROOMFLR1 cases are in class A. Adjacency mismatch 0 on every row; no row has shading touching the zone except a few at 0 m (C2 floor 034/091, B 2168) so shading is not the separator.
- **Notes:** the 6 completed cases (4 with no fatal, 2 non-convex survivors) are labelled Z / D_survived and are outside the 38. C2 cause is unresolved; same building can fail in `floor`/`fast_zone` yet complete in `auto`.

#### T06 — OPEN-38: apply the remedy, re-run the 44 — completed 2026-09-30

- **Artifacts:** `openubem/idf/cooking.py` (D6); `tests/test_cooking.py`, `tests/test_step3_orchestrator.py` (edited); `scripts/analysis/open38_fix_rerun_2026-09-30.py` (subcommands `build [--submit]` and `parse`; `parse` written, not run); `openubem/outputs/comparisons/open38_cooking_set_2026-09-30.csv` (87 rows). Speed job **1402478**, one array `--array=1-150%32 --time=7-00:00:00`, `submit_fleet_t07.sbatch`; single-case job **1402479**, `--array=151-151 --mem=32G --time=7-00:00:00` (`la_centre` `way/319507579`, `auto`).
- **Cases:** array **150** = cooking set 87 + OPEN-38 cases in their own modes 43 + controls 20; width **32**; plus 1 out-of-memory case. The 44 = 43 + 1. No overlap between the cooking set and the 44: the 2 auto-mode `nyc_centre` cases are among the 21 buildings missing from the adopted fleet. All 151 IDFs built (`success`). Staging: local `%TEMP%/ubem_validation/open38_fix_rerun_2026-09-30/` (`cases.csv`, `build_manifest.csv`, `submitted_manifest.csv`, `fleet.lst`); Speed `/speed-scratch/o_iseri/openubem/fleets/open38_fix_rerun_2026-09-30` (`idfs` 151, `fleet.lst` 151, `weather` 9).
- **Deviations:** (1) D6 detail: a one-zone model that stands for N floors (single_zone, `num_floors` N) gets density x N, because EnergyPlus Watts/Area reads only the one modelled floor plate (M18); multi-zone models get the plain archetype density. Gas uses the IDD field `Power per Zone Floor Area`, electric `Watts per Zone Floor Area`. Kitchen exhaust stays on `zones[0]` (not in D6). (2) Cooking set defined as adopted buildings of the 8 archetypes with non-zero cooking density and Option-A floors > 1 (auto mode then gives more than one zone; confirmed: min n_zones 2). "Cooking W today" = density x footprint x floors; "max W/m2 today" divides it by the first zone's floor area. (3) Controls: 2 per cell, seed 38, no cooking archetype, not an OPEN-35 change, not among the 44; 24 dropped to 20 as in T03. (4) Assertions changed: `test_cooking.py::test_fsr_gas_level_scales_with_area` renamed `test_fsr_gas_is_area_density` (now checks Watts/Area = 83.76); `test_step3_orchestrator.py::test_load_conservation_across_modes_multifloor` reads cooking as density x zone floor area x zone multiplier. (5) Jobs pending/running behind the account cap held by `t06_ES/FR/GB/IT` (not touched).
- **Test status:** (1) PASS 68 of 68 (`test_cooking.py`, `test_step3_orchestrator.py`, `test_tierB_provenance.py`, incl. the new 3-zone ZoneList test). Tests (2)-(5) belong to T06b.

- **T06c (2026-09-30) — done.** Jobs **1403414** (`--array=1-150%32 --time=7-00:00:00`, 150 cases, width 32) and **1403424** (`--array=151-151 --mem=32G --time=7-00:00:00`, `la_centre` `way/319507579`). IDFs built 151 of 151 with `trim_outputs=False` (cooking 87, open38 43, oom 1, controls 20; `cases.csv` copied from the old staging folder, no re-draw). Staging: local `%TEMP%/ubem_validation/open38_fix_rerun_2026-09-30_full/`, Speed `/speed-scratch/o_iseri/openubem/fleets/open38_fix_rerun_2026-09-30_full`. Deviations: `cmd_build` reads an existing `cases.csv`; the build rewrote `open38_cooking_set_2026-09-30.csv` (87 rows, same rule). Jobs 1402478 / 1402479 untouched. Not waited on; `squeue` shows 64 tasks RUNNING (account cap), the rest pending only for `AssocGrpCpuLimit` / `JobArrayTaskLimit`.
- **T06b (2026-09-30) — done.** **Artifacts:** `openubem/outputs/comparisons/open38_fix_rerun_2026-09-30.csv` (151 rows), `openubem/outputs/comparisons/open38_fix_summary_2026-09-30.json`; fetched outputs in `%TEMP%/ubem_validation/open38_fix_rerun_2026-09-30_full/fetched/`; log `%TEMP%/open38_parse.log`. Jobs 1403414 (121 COMPLETED, 27 FAILED, 2 OUT_OF_MEMORY) and 1403424 (1 FAILED) ended before harvest. **Deviations:** `_fetch` in `scripts/analysis/open38_fix_rerun_2026-09-30.py` now streams (`Popen`, `tarfile` mode `r|gz`) as in the T03 script; `cmd_parse` skips the fetch when `fetched/out/*/eplusout.sql` exists; summary gained cooking-set non-success count and names. **Test status:** (2) PASS, 20 controls, max abs diff 2.4e-10 %; (3) PASS, 151 of 151 have a terminal state (completed 121, fatal 28, sql_no_end 2); the 44 by class, recovered/total: A 0/7, B 10/10, ~~C1 6/6~~ see T06d, ~~C2 13/13~~ see T06d, ~~D 1/1~~ see T06d, ~~E 1/1~~ see T06d (plus D_survived 2/2 and Z_completed 4/4 from the 6 that completed earlier); all 10 class-B cases pass; (4) PASS, max cooking gain after D6 = 278.83 W/m2 (limit 1,000); (5) PASS, summary JSON written. **Notes:** cooking set 85 of 87 parsed success; not success: `auto__la_centre__way_428015098`, `auto__nyc_centre__way_266170763` (keep their candidate-1 rows). Candidate 1: n 8,139, EUI 171.5965, carbon 1,147,715.65 t. Candidate 2: n 8,139, EUI 171.3830, carbon 1,146,454.12 t. Additions (not in n): ~~8~~ 2 see T06d; originally 8 auto-mode buildings not in the adopted fleet (5 la_rural Warehouse, nyc_centre way/266149332 FullServiceRestaurant and way/266170765 LargeHotel, la_centre way/319507579 SecondarySchool). `abups_ok` fail count 21 (flag for director).

- **T06d (2026-09-30) — done.**
  - **Artifacts:** `scripts/analysis/open38_fix_rerun_2026-09-30.py` (`cmd_parse`: `ok_mask` = `parse_status == success` and `terminal == completed`, used for controls, `cs_new`, `recovered`, additions, cooking-set failures); re-written `openubem/outputs/comparisons/open38_fix_rerun_2026-09-30.csv` and `open38_fix_summary_2026-09-30.json`; log `%TEMP%/open38_parse_t06d.log`.
  - **Deviations:** none.
  - **Test status:** recovered A 0/7, B 10/10, C1 0/6, C2 0/13, D 0/1 (D_survived 2/2), E 0/1; additions 2 (`way/266149332`, `way/266170765`); candidate 2 n 8,139, EUI 171.3830, carbon 1,146,454.12 t (unchanged); controls 20, max abs diff 2.4e-10 %; cooking set not success 2 (unchanged). All equal the director values.
  - **Notes:** supersedes the recovery and additions figures in T06b.


#### T07 — Sweep, register, boards — completed 2026-09-30

- **Artifacts:** register `INVESTIGATION_open-items-register-II.md` (§1 new current-state row, §2 rows OPEN-35/38/62 struck and closed, §2 heading 0 live, §4 head, §6 closing section "OPEN-35 / OPEN-38 / OPEN-62", §7 entry); director prompt START HERE box rewritten; `OpenUBEM_debug_References.md` (§18 table; entries: cooking fix ch. 2, laundry re-run result ch. 2, `[OPEN]` sizing divergence ch. 2, `[OPEN]` sliver and non-convex shading ch. 1, `[OPEN]` out of memory at 32G ch. 12, fetch buffered in memory ch. 12, fatal run parsed `success` ch. 8); boards republished in place — open items v29 (`board_open-items.html`), published numbers v24 (`board_published-numbers.html`, built from the live copy, identical to the local file before edit); memory `project_current_baseline.md` and `MEMORY.md`.
- **Sweep:** "(three rulings)" marker beside every quote of 172.41 / 981,720 in `docs/**/*.md` — 246 lines in 52 files by executor (`scratchpad/sweep_three_rulings.py`), plus 89 lines placed right after an existing 2026-09-30 marker inside table cells and director files, plus 10 by hand in the register and debug reference; boards 24 + 17. Remaining unmarked quotes are only sentences that state the supersession itself (register §1 row and §4 head, director prompt, the new board notes). Archive citations: 152 `implemenation/PLAN_ten-items-close-2026-09-29.md` → `implemenation/previous/…`; 0 left.
- **Deviations:** (1) T04 citation corrected in §6 (`layout_assigner.py:550-578`). (2) `scripts/analysis/fleet06a_campaign_2026-09-18.py:8` quotes 172.41 without the new marker — a TechTransfer file, not edited (director prompt: tell its manager, do not edit). (3) Stale scripts: `scripts/analysis/open35_fallback_population_2026-08-21.py` and `open35_storey_intervention_2026-08-20.py` import `_archetype_consumed_group_median`, which no longer exists in `openubem/`; dated one-off analyses, not re-run, not edited.
- **Test status:** register row counts: 0 live / 66 retired / 66 total, next free OPEN-67 (§1 row, §2 heading, §4 head, §7 entry, director prompt, both boards agree); `grep` of `172.41|981,720` in `docs/**/*.md` without "(three rulings)" returns only supersession statements; adopted figure re-read from `open38_fix_summary_2026-09-30.json`: 171.3830 / 1,146,454.12 / n 8,139.
- **Notes:** arc complete. Nothing running on Speed for this arc.
