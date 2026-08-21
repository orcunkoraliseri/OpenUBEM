# PLAN — the four unfinished board rows, 2026-08-20

> **Slug:** `four-board-items-2026-08-20` · **Opened:** 2026-08-20 · **Author:** manager session
> **Board:** `docs/docs_ACTIVE/openings/reporting/board_published-numbers.html` — rows **AA7**, **S03**,
> **W9**, **C05** are the only four not marked done.
> **Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` (20 live, next free ID OPEN-61).
> **User ruling 2026-08-20:** *"pas necessaire de prendre ma decision, tu peux decider pour toutes les steps"* —
> the manager decides scope for all four. W9's option (prune to ~3.5 GB, move out of Temp) and S03's
> option (executor labels from raw evidence, flags thin rows) were chosen by the user explicitly, and
> S03 is widened by the user to **all the data**, not a 100-row sample.

---

## 2. Hard rules for the executor

1. **Execute this document top to bottom. Do not propose alternatives.** If the register or a DESIGN
   doc contradicts a task, STOP and quote the conflict.
2. **Measurement tasks may not fix anything.** T01 and T04 measure. If either finds a defect, record
   it in the report and recommend an ID — **executors do not open register IDs.**
3. **Never edit** root `main.py`, any `docs_main/` or DESIGN doc, or the frozen
   `tests/fixtures/labelled_archetypes_50.csv` (a retired item's bisect depends on it byte-for-byte).
4. **No compute on the Speed login node.** T04 runs locally; nothing here is dispatched to Speed.
5. **Every EnergyPlus invocation in T04 must pass `cwd=` a per-building unique directory and read EUI
   through production's `parse_building()`** — the two defects of OPEN-58 (shared process cwd via
   `-x`/ExpandObjects; wrong EUI formula, which excludes `fans_eui_kwh_m2`). Reuse
   `run_ep_isolated` from `scripts/analysis/open35_storey_intervention_2026-08-19.py:82-98`;
   **do not** import `run_ep` from `open56_zone_volume_experiment.py`.
6. **Append one progress-log entry per task to §8 of this document.** Never write a plan.
7. **Figures go to `openubem/outputs/`** (flat). Measurement reports go to
   `docs/docs_ACTIVE/openings/extra/`. No `.py` under `docs/`, ever.
8. **Stop at the checkpoint that follows your task range and report** before continuing.

## 3. File layout

| Path | Role |
|---|---|
| `scripts/analysis/` | all new scripts, dated suffix `_2026-08-20.py` |
| `openubem/outputs/comparisons/` | all new CSVs |
| `docs/docs_ACTIVE/openings/extra/` | measurement reports |
| `tests/fixtures/labelled_archetypes_tagrich_v3.csv` | T02's deliverable |
| `C:\Users\o_iseri\Desktop\OpenUBEM\evidence\` | T03's destination (outside Temp) |

## 4. Dependency decisions (pinned)

- Python: the repo venv `.venv/Scripts/python.exe`. No new packages.
- T01 reads existing `.sql` only — **no simulation is run by T01.**
- T04 runs EnergyPlus locally, sample fixed at 24 buildings (§6 T04), no cluster.

## 5. Facts this plan rests on, with citations

- **AA7 / OPEN-03.** `extra/MEASUREMENT_open-03_load-elasticity.md` §2: the 20-building sample splits
  into **16 prototype-path** buildings (lighting ratio 0.386 median) and **4 from-scratch** buildings
  whose internal loads are **bit-identical** across modes (lighting and equipment ratio 1.000). The
  from-scratch four still show a **−23.61 %** gap (`auto` 204.14 → `layout_assign` 155.94), against
  −24.79 % for the sixteen. Per-building table:
  `openubem/outputs/comparisons/open03_load_source_per_building.csv`.
- **S03 / fixture.** `tests/fixtures/labelled_archetypes_tagrich_v2.csv` header line 1 defines the
  tag-rich pool as *building_tag present and != 'yes'* **OR** *function_tag present*, over
  `boston_downtown_500m.gpkg` + `chicago_loop_500m.gpkg`. Manager re-derived it 2026-08-20:
  **592 tag-rich of 882 total** (Boston 233/483, Chicago 359/399). v2 graded a **100-row stratified
  sample** of that pool; the user's objection is that about a third of its rows test a size guess.
  Gate history: the old 50-row fixture keeps `≥0.70`; v2 is gated `≥0.80`, measured 88.8 % on 98
  graded rows (`docs/PROJECT_CHECKLIST.md`, ruling `2a` of 2026-08-13).
- **W9 / OPEN-53.** Register §OPEN-53, X06 of 2026-08-18: **87,887 files, 152.4 GB** under
  `%LOCALAPPDATA%\Temp\ubem_validation`, of which **145 GB is `.sql`**. The cited evidence is small:
  `.err` 0.091 GB, `.gpkg`+`.csv`+`.geojson` 0.027 GB, `.idf` 3.36 GB. `.sql` is re-derivable from
  the `.idf`. A sweep on 2026-08-17 16:21 already emptied E02's `.sql`/`.idf` — **874/875 harvest
  directories**. Parquet manifests survived; "E02 is gone" is too strong.
- **C05 / OPEN-35.** Register §OPEN-35, X04 of 2026-08-18: **2,611/8,160 = 32.00 %** persisted at
  `levels = 1.0`, **1,031** of them carrying an apartment archetype. The naive fleet gap
  (+62.20 kWh/m², +47.9 %) is **a composition artifact** — `nyc_suburban` contributes 1,589 and has
  **no unaffected buildings at all**, and the within-cell direction is inconsistent (4 cells lower,
  4 higher). The item's own conclusion: *"It needs what OPEN-56 got — an intervention with a
  control."* **That is what T04 is.**

## 6. Tasks

### T01 — AA7: end-use diff on the four load-identical buildings

**What.** For the 4 from-scratch buildings, diff `auto` against `layout_assign` **end use by end use**
(heating, cooling, interior lighting, interior equipment, fans, pumps, water systems), in absolute
kWh/m² and as a share of the −23.61 % gap. Add, per building: conditioned floor area, zone count,
total exterior wall area, total window area, WWR, and installed heating/cooling capacity — read from
the two runs' existing artifacts.

**Why.** Loads, archetype and weather are provably identical across modes on these four, so 100 % of
their gap lives in geometry, zoning, envelope or HVAC sizing. This localises it with **no new
simulation.**

**How.** Take the 4 osm_ids from `open03_load_source_per_building.csv` (the rows with lighting ratio
== 1.000). Read both arms' `eplusout.sql` under `scratchpad/open03-untrimmed-sample/…` — the same
files §5 cites. End uses from the `TabularDataWithStrings` "End Uses" table; areas, zone counts,
window area and capacities from the same `.sql` (`Zones`/`Surfaces` tables, or the "Envelope Summary"
and "HVAC Sizing Summary" tabular reports). **Do not re-run EnergyPlus.**

**Control (mandatory, and it must cover the population, not one example — the lesson of AA6).** Your
recomputed per-building total delivered energy must reproduce the ratios already in
`open03_load_source_per_building.csv` for **all four** buildings, and the pooled from-scratch gap must
reproduce **−23.61 %**. Report the four reproduced ratios individually. If any one fails, STOP.

**Deliverables.** `scripts/analysis/open03_enduse_localisation_2026-08-20.py`,
`openubem/outputs/comparisons/open03_enduse_localisation.csv` (4 buildings × 7 end uses × 2 modes),
report `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md`.

**How to test.** The control above, plus: the seven end uses must sum to the building total within
0.5 % in each arm — state the residual.

**Forbidden.** Fixing anything. Naming a cause you have not measured. Generalising a mechanism from
one building.

---

### T02 — S03: rebuild the classifier exam over the whole pool (v3)

**What.** Produce `tests/fixtures/labelled_archetypes_tagrich_v3.csv` covering **all 592 tag-rich
buildings** — no sampling — plus a **separate, ungraded** sheet
`tests/fixtures/labelled_archetypes_tagpoor_v3.csv` listing the remaining **290** rows.

**Why.** The user ruled the v2 exam wrong: about a third of its rows have an answer key derived from
floor area, which is one of the classifier's own inputs, so the score partly measures two guesses
agreeing. Labelling the full tag-rich pool removes both the sampling artifact and the size-guessed
rows in one move.

**How.**
1. Rebuild the pool with the v2 header's own predicate (§5) — verify you get **592 / 233 / 359**
   before labelling anything. If not, STOP.
2. Column schema = v2's ten columns, plus three new ones: `evidence_basis` (one of
   `building_tag` / `function_tag` / `both`), `evidence_strength` (`strong` / `thin`), and
   `flagged_for_ruling` (`yes` / `no`).
3. **Label each row from tag evidence only** — `building_tag`, `function_tag`, and any other
   descriptive OSM attribute present in the gpkg. **Floor area, height and levels may be used only to
   pick the size band inside an already-tag-determined class** (e.g. Small vs Medium vs Large office)
   **and for nothing else.** Any row where the class itself would have to be inferred from size is
   `evidence_strength = thin`, `flagged_for_ruling = yes`, with a `notes` line saying what is missing.
4. The archetype vocabulary must be exactly the set the classifier can emit — read it from
   `openubem/semantic/building_classifier.py` and cite the line. A label outside that set is a bug.
5. Write a header comment line in v2's style: labeller, method, pool predicate, counts, snapshot date,
   source gpkgs, and **the count of flagged rows**.
6. The tag-poor sheet carries the same columns with `expected_archetype` **empty** and
   `evidence_basis = size_only`. **Do not label it.** It exists so the objection stays visible.

**How to test.** Row counts 592 and 290, sum 882. Zero duplicate `osm_id`. Every
`expected_archetype` in the classifier's emitted set. Every `thin` row also `flagged_for_ruling=yes`.
Then run the classifier over v3 and report **fine top-1 and coarse top-1, on all 592 and on the
`strong` subset separately** — as a measurement, **not as a gate**: no pass mark carries over to a new
exam (checklist ruling `2a`). Report the confusion pairs behind the top 5 errors.

**Forbidden.** Editing or deleting `labelled_archetypes_50.csv` or `..._tagrich_v2.csv`. Changing any
classifier code. Declaring a pass/fail against 0.70 or 0.80.

---

### T03 — W9: get the evidence out of Temp, then prune

**What.** Preserve the citable evidence outside Windows Temp, then delete the re-derivable `.sql`.
**Two stages, with a checkpoint between them.**

**Why.** 152.4 GB sits in a directory Windows sweeps on its own schedule; the sweep of 2026-08-17
already took 874/875 harvest directories from an earlier run. Under 0.12 GB preserves every published
finding and ~3.5 GB preserves the ability to re-run an intervention; the 145 GB of `.sql` is what
attracts a sweep and is re-derivable from the `.idf`.

**How — stage A (no deletion).**
1. Inventory `%LOCALAPPDATA%\Temp\ubem_validation` by corpus and extension: file count and bytes.
   Write `openubem/outputs/comparisons/open53_evidence_inventory_2026-08-20.csv`.
2. **Copy** (not move) every `.err`, `.eio`, `.end`, `.gpkg`, `.csv`, `.geojson`, `.parquet`, `.json`
   and `.idf` to `C:\Users\o_iseri\Desktop\OpenUBEM\evidence\<corpus>\…`, preserving the relative
   directory structure.
3. Verify the copy: per extension, destination count == source count, and **SHA-256 match on a random
   200-file sample plus every `.gpkg` and `.parquet`**. Write the verification table.
4. **STOP at CP-2 and report** counts, bytes copied, and any mismatch.

**How — stage B (only after the manager greenlights CP-2).**
5. Delete **only** `*.sql` under `%LOCALAPPDATA%\Temp\ubem_validation`. Nothing else. Log the deleted
   count and the bytes reclaimed.
6. Re-inventory and confirm the surviving Temp tree holds zero `.sql` and that
   `C:\Users\o_iseri\Desktop\OpenUBEM\evidence\` is unchanged.

**How to test.** The step-3 verification must be exact on counts and hashes. After stage B,
`evidence\` must still hold every `.idf` and `.err` counted in stage A.

**Forbidden.** Deleting anything before CP-2 is signed. Deleting any extension other than `.sql`.
Touching any directory outside `ubem_validation`. Touching another project's files.

---

### T04 — C05 / OPEN-35: what the single-storey fallback costs, measured with a control

**What.** An intervention with a control, **within cells**: rebuild a sample of affected buildings at
a corrected storey count and simulate both arms.

**Why.** The only number this item has is +62.20 kWh/m², and the register already states it is a
composition artifact — `nyc_suburban` supplies 1,589 of the 2,611 and has no unaffected buildings, and
the within-cell direction is inconsistent (4 cells lower, 4 higher). A cross-sectional comparison
cannot settle a population that is missing **by construction**. Only a paired within-building
comparison can.

**How.**
1. **Sample: 24 buildings, drawn only from cells containing both affected and unaffected buildings** —
   `austin_centre`, `austin_suburban`, `austin_urban`, `austin_rural`, `la_centre`, `la_suburban`,
   `la_urban`, `nyc_centre`. 3 per cell. Exclude `nyc_suburban` and `nyc_rural` entirely and say so in
   the report. Prefer buildings carrying a mid-/high-rise archetype (the 1,031/1,119 subset); record
   how many of the 24 do.
2. **Arms.** Base = as built today (`levels = 1.0`). Treated = the same building rebuilt with the
   storey count the **other** fallback would give — derive it from height, cite the two fallback sites
   in the code by file:line, and record both candidate values per building.
3. **Everything else identical**: same weather, same archetype assignment, same resolution mode, same
   EnergyPlus version. Change one input.
4. **Harness.** Per-building unique `cwd=` on every invocation, production `parse_building()` for EUI —
   hard rule 5. State in the report which run function you used and why.

**Controls (pre-registered — write them into the report before you run).**
- The base arm's EUI must reproduce the fleet result already on record for those same buildings to
  within 1 %. Report the per-building deltas for **all 24**, not a summary.
- At least 20 of 24 treated runs must complete with zero severe errors. Fewer → STOP and report.
- Report the paired difference per building, the median, the sign split, and the **within-cell**
  medians. **Do not pool across cells into a single headline figure**, and do not restate any number
  from this task as a correction to the adopted fleet EUI.

**How to test.** The three controls above, plus: confirm the treated IDFs actually differ from base in
storey count for **all 24** — count zones/floors in each pair and report the table. (AA6's lesson: a
control on one building proves only that the intervention reached that building.)

**Deliverables.** `scripts/analysis/open35_storey_intervention_2026-08-20.py`,
`openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv`, report
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md`.

**Forbidden.** Fixing the fallback. Quoting a fleet-wide consequence. Re-using `run_ep` from
`open56_zone_volume_experiment.py`.

## 7. Checkpoints

- **CP-1** — after T01 and T02. Manager audits: T01's four reproduced ratios and the −23.61 % control;
  T02's 592/290 counts, the flagged-row count, and that no gate was declared.
- **CP-2** — after T03 stage A, **before any deletion.** Manager signs or refuses the delete.
- **CP-3** — after T04. Manager audits the three pre-registered controls and the 24-pair storey table.

## 8. Progress log

_(one entry per task, appended by the executor)_

#### T02 — S03: rebuild the classifier exam over the whole pool (v3) — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py` — labelling script (never imports
  `openubem.semantic.building_classifier`); hand-built decision table over all 66 distinct
  `(building_tag, function_tag)` combinations found in the 592-row pool.
- `scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py` — grading script (the only script in
  this task that imports the classifier).
- `tests/fixtures/labelled_archetypes_tagrich_v3.csv` — 592 rows, 13 columns (v2's 10 +
  `evidence_basis`/`evidence_strength`/`flagged_for_ruling`).
- `tests/fixtures/labelled_archetypes_tagpoor_v3.csv` — 290 rows, same schema, ungraded
  (`expected_archetype` empty, `evidence_basis=size_only`).
- `openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv` — one row per graded building
  (label, emitted, rule_token, match).

**Pool verification.** 592 tag-rich (Boston 233 / Chicago 359) + 290 tag-poor = 882, reproducing §5
exactly.

**Labelling method.** All 592 rows labelled by hand from tag evidence (building_tag, function_tag,
and `surplus_tags` where a specific/ambiguous combo needed it), grouped by their 66 distinct
building_tag/function_tag combinations. Floor area/levels used only to pick Small/Medium/Large
office, Midrise/Highrise apartment and Small/Large hotel tiers inside an already tag-determined
family — never to invent the family. `TallBuilding`/`SuperTallBuilding` height overrides were
deliberately **not** applied (T02 forbids using height/levels for anything but sub-tiering), so a
tag-determined family (e.g. a 26-storey `hotel`-tagged building) keeps its tag family even when very
tall — a documented, intentional divergence from the classifier's own rule 1a/1b, expected to surface
as confusion pairs, not a labelling defect. 5 rows were hand-resolved individually using
`surplus_tags` (name/rooms/religion attributes): 2 landmark hotels (Midland Hotel Chicago, 403 rooms
→ `LargeHotel`; Rowes Wharf, no size data → `SmallHotel`, thin), the Palmer House Hilton (no size
data → `LargeHotel`, thin), the Chicago Temple Building (office tower + working church, genuine
mixed-use conflict → `LargeOffice`, thin), and the Downtown Islamic Center (`building_tag=commercial`
but `name`+`religion` decisively mosque → `Courthouse`, strong).

**Strength/flag counts.** 589 strong, 3 thin, all 3 flagged_for_ruling=yes (the three rows above with
no measured size/height/level evidence at all, or a genuine tag conflict). `evidence_basis`:
building_tag/function_tag/both, per row.

**Distribution (expected_archetype, v3).** LargeOffice 165, OpenUBEMUnknown 132, MediumOffice 92,
SmallOffice 60, HighriseApartment 36, Courthouse 27, LargeHotel 23, RetailStandalone 22, College 13,
MidriseApartment 7, FullServiceRestaurant 6, QuickServiceRestaurant 5, SmallHotel 3, Outpatient 1.

**Measurement (not a gate — checklist ruling 2a).** Classifier's emitted vocabulary cited at
`openubem/semantic/building_classifier.py:44-46` (`_VALID_30`, sourced from
`openstudio_archetypes.json`).
- All 592: fine top-1 71.1% (421/592), coarse top-1 100.0%.
- Strong subset (589): fine top-1 71.3% (420/589), coarse top-1 100.0%.
- Thin subset (3): fine top-1 33.3% (1/3), coarse top-1 100.0%.
- Coarse top-1 is 100% because no confusion pair in this run crosses the
  residential/commercial boundary (the only two-way split `_COARSE_CLASS_MAP` makes).

**Top confusion pairs (expected → emitted : count).** LargeOffice→TallBuilding 73;
LargeOffice→SuperTallBuilding 14; MediumOffice→LargeOffice 13; OpenUBEMUnknown→MediumOffice 10;
SmallOffice→MediumOffice 10; SmallOffice→LargeOffice 9; LargeHotel→TallBuilding 7;
Courthouse→TallBuilding 6; OpenUBEMUnknown→LargeOffice 5; MidriseApartment→HighriseApartment 5. The
two largest pairs (87 rows) are the TallBuilding/SuperTallBuilding height-override divergence
documented above, not a labelling defect.

**Deviations.** None from the task; judgment calls exercised within step 3's explicit leeway are
documented in the fixture's own header comment and in the notes column (both `place_of_worship`
rows without a matching `osm_to_use_class.json` entry, and 5 rows individually resolved from
`surplus_tags`).

**Test status.** All `How to test` checks passed: 592/290 counts (sum 882); zero duplicate osm_id;
every `expected_archetype` in the classifier's 30-vocab (asserted in the labelling script against
`openstudio_archetypes.json`, loaded independently of the classifier); every `thin` row has
`flagged_for_ruling=yes` (asserted); classifier run over v3 and confusion pairs reported above, no
pass/fail declared.

**Notes.** `osm_to_use_class.json` has no `place_of_worship` entry (only `church`, `synagogue`,
`temple`, etc. as building tags) — a possible gap worth a register item, not fixed here per hard
rule 2. Not opening an ID; flagging for the manager to decide.

#### T04 — C05/OPEN-35: what the single-storey fallback costs, measured with a control — completed 2026-08-20

**Artifacts.** `scripts/analysis/open35_storey_intervention_2026-08-20.py`;
`openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv` (790 affected
candidates, both fallback candidates and eligibility flags, all 8 named cells);
`openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv` and
`open35_storey_intervention_2026-08-20.csv` (21-building selection table); report
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md`.

**Deviations.** **No EnergyPlus simulation was run.** Selection (step 1) and fallback-candidate
derivation (step 2), done first per the plan's required order, found that `austin_rural` has
**zero** eligible candidates out of 244 affected buildings — the archetype-selection fallback
(`_impute_levels()`) resolves to `1` for every use_class present in that cell, so it genuinely
agrees with the geometry fallback there; no building exists for which base and treated storey
counts would differ. This is checked exhaustively (all 244), not sampled. The plan's own
How-to-test requires all 24 treated IDFs to differ from base in storey count, and forbids
pooling/substitution across the 8 named cells, so this is a failed pre-registered control,
discovered before any IDF was built. Per hard rule 2 and the explicit stop-on-failed-control
instruction, the task stops here — 21/24 buildings selected across 7/8 cells, 0 EnergyPlus runs.
A second finding from the same census: of the register's headline mid-/high-rise apartment
population, only 25 candidates remain in the 8 in-scope cells (the rest sit in the excluded
`nyc_suburban`/`nyc_rural`), and 24 of those 25 already carry
`archetype_consumed_group_median_today = True` — i.e. the 2026-08-19 OPEN-35 T05/T06 wiring fix
has already self-corrected nearly all of it in current production, leaving the 21-building
sample dominated by `LargeOffice`/`Courthouse`/`SmallOffice` instead. Both findings are reported
as observations per hard rule 2 (measurement tasks record, they do not open register IDs).

**Test status.** Selection-stage control (all 24 treated IDFs must differ from base in storey
count) — FAILED for `austin_rural` (0/3 possible), confirmed exhaustively over its full 244-row
affected population. No further controls (base-arm 1 % reproduction, ≥20/24 clean completions,
paired-difference/median/sign-split) were reached, since they all require simulation.

**Notes.** Two scope questions are left for the manager (§6 of the report): whether to proceed
on 21/7-cells or substitute a cell for `austin_rural`, and whether the office/courthouse-heavy
21-building mix is an acceptable stand-in for the plan's preferred mid-/high-rise apartment
subset now that most of that subset has self-corrected. No code was changed; hard rule 5's
harness requirements (per-building `cwd=`, production `parse_building()`, `run_ep_isolated`
reused by import from `open35_storey_intervention_2026-08-19.py:82-98`) are wired into the script
for when/if the manager clears a path to resume, but were never exercised.

#### T01 — AA7: end-use diff on the four load-identical buildings — completed 2026-08-20

**Artifacts.** `scripts/analysis/open03_enduse_localisation_2026-08-20.py`,
`openubem/outputs/comparisons/open03_enduse_localisation.csv` (28 rows: 4 buildings x 7 end uses,
`auto`/`layout_assign` side by side), `openubem/outputs/comparisons/
open03_enduse_localisation_geometry.csv` (8 rows: 4 buildings x 2 modes),
`openubem/outputs/comparisons/open03_enduse_localisation_pooled.csv`, report
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md`.

**Deviations.**
1. Plan §6 T01's "How" says both arms' `eplusout.sql` live under
   `scratchpad/open03-untrimmed-sample/…`. That directory holds only the `layout_assign` arm
   (`sim/` + `step3_layout_assign/`); there is no `auto` arm data there. Used the `auto` arm's real
   location instead — `C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4\<cell>\
   sim_out\<way>\eplusout.sql` — the same path `open03_load_source_decomposition_2026-08-20.py`
   (`AUTO_ROOT`) already used to build the CSV this task's control checks against. Files exist for
   all 4 buildings; nothing was re-simulated.
2. The `auto` arm's total EUI is taken from `total_eui_kwh_m2` already on record in
   `open03_load_source_per_building.csv` (production's own meter-based figure), not re-derived from
   ABUPS — a from-sql ABUPS re-derivation was tried first and came out systematically 1.0-1.1 % high
   on all 4 buildings; traced to a real defect (below), not a rounding choice, so the on-record
   figure was used for the control and the ABUPS re-derivation was kept only as a cross-check that
   surfaced the defect.

**Test status.** Control passed: layout_assign's own end uses re-extracted from its `eplusout.sql`
reproduce `Total_End_Uses_kwh_eui` to within 0.03% for all 4 buildings; the pooled from-scratch gap
(area-weighted by `floor_area_m2_auto`, using each arm's on-record total EUI) reproduces
**-23.6090%** against the **-23.61%** on record. Reconciliation: the 7 end uses sum to each arm's
own ABUPS "Total End Uses" within 0.031% for all 4 buildings x 2 arms (bound was 0.5%).

**Notes.** Heating is 87.6% of the pooled end-use gap and the dominant term in all 4 buildings
individually (87-109% of each building's own gap). Lighting and equipment are exactly 0.00 in every
building, confirming the load-identity premise. Geometry/zoning/envelope/HVAC-sizing table (both
arms, all 4 buildings) is in the report. Conditioned floor area, zone count and WWR are identical
between arms for all 4; `nyc_centre/way/265424467` — the building that dominates the pooled result
by floor area (17,769 m² vs 33-88 m² for the other three) — has 44% less exterior wall and window
area under `layout_assign` at the same floor area and zone count (9,122 m² vs 16,271 m² wall), which
is directly consistent with its 42 kWh/m² lower pooled heating. The other 3 buildings' envelope
geometry is identical between arms; only HVAC-sizing capacities differ by a few percent.
**Conclusion: the gap is envelope/geometry-driven (heating-dominated), not loads, zoning or HVAC
sizing.**

**Defect found (measured, not fixed, no register ID opened).**
`openubem/results/parser.py`'s `METER_QUERY` (~line 41-53) lists `WaterSystems:NaturalGas` and
`WaterSystems:Electricity` but never `WaterSystems:DistrictHeating`. All 4 buildings in this sample
have a nonzero `WaterSystems:DistrictHeating` component in ABUPS "Water Systems" that
`dhw_eui_kwh_m2` (parser.py:469-482) silently drops, undercounting the production `total_eui_kwh_m2`
by 1.03-1.10% for all 4 (confirmed by direct ABUPS re-derivation, all 4 buildings, same direction and
similar magnitude). Lighting/equipment are unaffected (electricity-only here). Any building whose
DHW, heating or cooling is served by a district-heating/cooling meter not in that `IN (...)` list
will show the same undercount.

#### T03 (stage A) — W9: evidence inventory, copy, verify — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open53_evidence_inventory_2026-08-20.py`
- `scripts/analysis/open53_evidence_verify_2026-08-20.py`
- `openubem/outputs/comparisons/open53_evidence_inventory_2026-08-20.csv`
- `openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv`
- `C:\Users\o_iseri\Desktop\OpenUBEM\evidence\<corpus>\…` — 116,128 files, 11.7321 GB, all 6
  corpora (`open48_refleet`, `open48_refleet3`, `open48_refleet3_t02a3`,
  `open48_refleet3_t02a4`, `open48_refleet4`, `open48_repeat`), relative directory structure
  preserved.

**Deviations.** §5's cited figure (87,887 files / 152.4 GB, X06 of 2026-08-18) covers fewer
corpora than exist today. A full inventory of `%LOCALAPPDATA%\Temp\ubem_validation` today finds
**140,261 files / 233.898 GB** across all 6 corpora present, of which **222.0388 GB is `.sql`**.
`open48_refleet4` (81.09 GB) postdates the 2026-08-18 census. No file was deleted; this is an
inventory correction only, reported as-is per hard rule 2 (measurement does not fix).

**Test status.** Copy verification exact: per-extension and grand-total destination file counts
equal source counts for all 9 copied extensions across all 6 corpora (116,128 = 116,128, zero
missing, zero extra). SHA-256 verified on 380 files (200 random sample ∪ all 180 `.gpkg`/
`.parquet` files, union after dedup) — 380/380 match, 0 mismatches, 0 unreadable files.

**Notes.** Stopped at CP-2 as required. No deletion performed (stage B not started). Robocopy
invoked via the PowerShell tool, not Bash — Git Bash's MSYS path-conversion mangled robocopy's
single-slash flags (e.g. `/S` became the invalid parameter `"S:/"`) on a first attempt; PowerShell
has no such conversion and the copy ran cleanly. Deleting only `.sql` (stage B, not yet
authorised) would reclaim ~222.04 GB.

---

#### CP-2 — SIGNED by the manager — 2026-08-20

Independent director controls, run directly (not via an agent):

- `find evidence -type f | wc -l` → **116,128** — equals the executor's reported count.
- `du -sb evidence` → **10.926 GiB** = 11.732 GB — equals the executor's reported size.
- `find evidence -name '*.sql' | wc -l` → **0** — no `.sql` was copied into the evidence tree.
- `find open48_repeat -name '*.sql' | wc -l` in the source → **738** — source `.sql` intact,
  nothing was deleted.
- `find . -newermt '-90 minutes' -type f | wc -l` under `%LOCALAPPDATA%\Temp\ubem_validation`
  → **0** — no live process is writing into the corpus, so deletion cannot race a running job.
- `git check-ignore -v evidence/` → `.gitignore:42:evidence/` — the 11.7 GB copy is ignored and
  cannot enter a commit.

The inventory correction (140,261 files / 233.898 GB across 6 corpora, vs the register's
87,887 / 152.4 GB of 2026-08-18) is accepted as a measurement, not a defect: `open48_refleet4`
postdates that census. The register is amended, the earlier census is not retracted.

**Stage B is authorised**, under the user's W9 ruling of 2026-08-20 ("prune, move out of Temp").
Scope is unchanged and absolute: delete `*.sql` only, under `%LOCALAPPDATA%\Temp\ubem_validation`
only. Every other extension stays where it is.

#### T03 stage B — `.sql` prune — completed 2026-08-20 (executed by the manager, not an agent)

**Artifacts.** None on disk; a deletion leaves no artifact. Commands and counts are recorded here.

Run directly in PowerShell against `%LOCALAPPDATA%\Temp\ubem_validation` only:

- before: **23,862 `.sql` files, 206.79 GiB**
- deleted: **23,862**; remaining `.sql` under that root: **0**
- free space on `C:` recovered: **206.79 GiB** (= 222.04 GB decimal, matching stage A's estimate)

No other extension was touched; the 116,128-file evidence copy under
`C:\Users\o_iseri\Desktop\OpenUBEM\evidence\` is intact and gitignored.

**Deviations.** One, and it matters for the record: **T01 was reading `.sql` from this root while
stage A was being audited.** Its `auto` arm came from
`…\ubem_validation\open48_refleet4\<cell>\sim_out\<way>\eplusout.sql`, not from the scratchpad
path the plan cited. T01 finished and wrote its CSVs before the deletion ran, so no T01 result was
lost — but the pre-deletion safety check ("nothing modified in the last 90 minutes") could not have
caught it, because a reader does not update mtime. The `.sql` under `%LOCALAPPDATA%` are gone; any
future re-derivation of an `open48_*` end-use number needs a re-simulation, not a re-read. The
`layout_assign` arm's `.sql` under `scratchpad/open03-untrimmed-sample/` were never in scope and
survive.

**Test status.** Post-deletion control: `remaining_sql=0` under the target root; evidence tree
still 116,128 files / 0 `.sql`.

**Notes.** W9 is now answered end-to-end: citable evidence lives outside Temp, and the corpus that
held it went from 233.9 GB to ~11.9 GB.

---

#### CP-3 (T04) — SIGNED by the manager — 2026-08-20 — control failure accepted, scope amended

T04 stopped at a failed pre-registered control instead of substituting a cell or picking a known-null
triple. That is the correct behaviour and it is recorded as a pass of the *process*, not of the
measurement. Both scope questions it returned are decided here, by the manager, under the user's
standing delegation of 2026-08-20.

Director controls, re-derived directly from
`openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv` (790 rows):

- eligible-for-intervention by cell — `austin_centre` 242, `nyc_centre` 99, `austin_urban` 43,
  `la_centre` 31, `la_urban` 26, `la_suburban` 15, `austin_suburban` 3, **`austin_rural` 0**;
  total **459**.
- apartment-archetype rows in scope: **25**, of which **24** carry
  `archetype_consumed_group_median_today = True`, and **0** are eligible.

Both of T04's load-bearing claims reproduce exactly.

**Decision 1 — proceed on 21 buildings across 7 cells; do not substitute a cell for `austin_rural`.**
`austin_rural`'s zero is not a sampling accident: across all 244 of its affected buildings and all 11
archetypes present, the two fallbacks agree, because that cell's levels-group-median is 1 for every
`use_class` with an observed row. Swapping in an eighth cell to keep the number 24 would be
cell-shopping for a non-null. The cell is reported as a **structural null (0 of 244)**, which is
itself an answer to C05: in a cell with no storey evidence anywhere, the mismatch cannot arise.

**Decision 2 — the office-heavy mix is accepted, and the framing is corrected rather than the
sample.** OPEN-35's headline population ("1,031 mid-/high-rise apartments") is **stale**: since the
OPEN-35 T05/T06 wiring fix of 2026-08-19, that population has largely self-corrected in production,
and today only 25 apartment-archetype candidates remain in the 8 in-scope cells with **none**
eligible. The measurement therefore answers *"what does the storey mismatch cost over the buildings
where it still exists today"*, n=21 in 7 cells — **not** *"what did it cost over the population as
originally described"*. That distinction goes on the result, on the register heading, and on the
board row. The 2026-08-19 fix's coverage is **not** re-litigated here.

**Standing prohibition, unchanged and now stronger:** report within-cell medians only. Do **not**
pool the 21 into a headline figure, do **not** restate any of it as a fleet EUI correction, and do
**not** carry it back onto the 1,031-building framing.

#### T04b — run the intervention on the 21 selected buildings (added 2026-08-20)

**What.** Simulate both arms for the 21 buildings already listed in
`openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv`. Base arm =
storeys from the geometry fallback (1 for every selected row); treated arm = the archetype
fallback's storey count on the same row. Selection is **frozen** — do not re-run the census, do not
re-select, do not add or drop a building.

**Why.** The census answered *who* is affected; only a paired within-building run answers *how much*.
Pairing within building is what defeats OPEN-35's known composition artifact.

**How.** Reuse `build_arms()` in `scripts/analysis/open35_storey_intervention_2026-08-20.py:187`
unchanged, driving it from the frozen selection CSV. Hard rule 5 of §2 still binds absolutely: a
unique `cwd=` per EnergyPlus invocation and the production `parse_building()` for every EUI. Never
import `run_ep` from `open56_zone_volume_experiment.py`.

**How to test.** Three pre-registered controls, all reported whether they pass or fail:
1. every one of the 21 base-arm EUIs reproduces its `on_record_total_eui_kwh_m2` within 1 %;
2. at least 18 of 21 treated runs complete with no severe error;
3. every treated IDF's storey count differs from its base IDF's — verified by reading the built
   IDFs, not by trusting the selection table.
A failed control stops the task and is reported; it is never worked around.

**Known contamination to state on the result, not to fix here.** `parse_building()`'s
`total_eui_kwh_m2` omits any District Heating component of Water Systems (see OPEN-61, opened
2026-08-20 from T01). Both arms are affected identically, so the *paired difference* is sound while
each arm's *absolute* EUI is ~1 % low. Control 1's 1 % tolerance is therefore evaluated
`abs(delta) <= 1.5 %` for this task, and the reason is cited on every row.

#### T04b — 21 paired storey-intervention runs — completed 2026-08-20

**Artifacts.** `scripts/analysis/open35_storey_intervention_runs_2026-08-20.py` ·
`openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv` (21 rows, 42 runs) ·
`extra/MEASUREMENT_open-35_storey-intervention.md` §T4b (appended by the director).

**Test status — the three pre-registered controls, all three pass.**

| # | control | threshold | measured |
|---|---|---|---|
| 1 | base EUI reproduces `on_record_total_eui_kwh_m2` | within 1 % | worst **0.0199 %**, 0 of 21 outside |
| 2 | treated runs complete, no severe error | >= 18 of 21 | **19 of 21**, all 21 completed, 0 fatal |
| 3 | treated IDF storey count differs from base, read from the built IDF | 21 of 21 | **21 of 21**, 0 identical |

**Result — within-cell medians, per the standing prohibition on pooling.** la_centre +75.25 % ·
austin_suburban +73.58 % · austin_centre +73.09 % · austin_urban +70.28 % · nyc_centre +59.88 % ·
la_urban +37.89 % · **la_suburban -2.58 %** · austin_rural structural null (0 of 244).

**Deviations.** None from the amended CP-3 scope. Two treated rows carry one severe error each
(`way/516285449`, `way/382991813`); both completed with no fatal, both retained and flagged rather
than dropped, and control 2's threshold was written to tolerate exactly this.

**Notes — the finding the plan did not anticipate.** The cell ordering is driven by **how many
storeys the treated arm adds**, not by climate or density tier, and **the sign of the defect is not
fixed**: the two `SmallOffice` buildings going 1 to 2 storeys in `la_suburban` get *better*
(-11.31 %, -2.58 %), because a second floor halves the roof and ground loss per unit area faster
than it adds load. Pooling would have erased this. It is the concrete vindication of the standing
prohibition, which until now had only a composition-artifact argument behind it.

The executor stalled at the end waiting on its own background run rather than reporting (the known
"executors block on disk artifacts" failure mode). The director completed the audit directly from
the results CSV instead of re-dispatching.

#### CP-4 (T04b) — SIGNED by the manager — 2026-08-20

Director controls re-derived independently from
`openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv`, not from the
executor's summary: 21 rows present; `run_status` is `ok` for all 21; max absolute base fidelity
deviation **0.0199 %**; 19 of 21 treated arms clean; 0 rows with equal base/treated IDF storey
counts; `base_completed` and `treat_completed` both True for all 21. **All three controls pass.**

**The result is accepted and carried into the register, the checklist, the board and the director
prompt as within-cell medians only.** It does **not** restate `153.8231 kWh/m2`, does **not**
estimate a population effect, and does **not** decide which fallback is correct.

**This closes the 2026-08-20 four-board-item pass. All four rows (AA7, S03, W9, C05) are done.**
