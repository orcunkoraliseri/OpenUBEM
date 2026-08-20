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
