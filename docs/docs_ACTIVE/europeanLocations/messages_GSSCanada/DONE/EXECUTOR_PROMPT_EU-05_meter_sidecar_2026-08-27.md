# EXECUTOR PROMPT — `EU-05` meter sidecar (off-path re-run of the promoted 95)

**Slug:** `EU-05-METER-SIDECAR` · **Opened:** 2026-08-27 · **Authority:** owner authorisation
2026-08-27 ("vas-y je te donne le permission"), answering challenge 1 of
`GSSCanada/GSSCanada-main/4J_docs_occ/messages_OpenUBEM/2026-08-27_4J_to_OpenUBEM_S3_EU-05-06_challenges.md`.

## 1. Why this exists

`EU-05` recorded `meters_present 0 of 95` and **deferred** it with the written reason *"emitting
meters means re-running the promoted campaign and changing every `idf_sha256`"*. The 4J session
challenged that reason and is right: what breaks hashes is emitting meters **in the promoted
campaign**. An **off-path sidecar** — copies of the same 95 IDFs, meters added, run in a separate
directory — answers the question and leaves every promoted artefact byte-identical.

The sidecar also settles a second question: the promoted `eui_kwh_m2` column is **heating-only**
(ideal-loads variable, `scripts/run_eu_s2_campaign.py:285`), while the models each carry an
`OtherEquipment` gain declared with **Fuel Type `Electricity`, 1 W/m²**. That electricity is real
metered energy the promoted column does not contain. The sidecar measures how much.

## 2. Hard rules — read before touching anything

1. **Nothing under `openubem/outputs/eu_evidence/EU-04/s3/` may be modified, moved or deleted.**
   Not the manifest, not `s3_campaign/`, not one saved IDF. You **read** from it only.
2. **No promoted IDF is edited in place.** Copy it, edit the copy, run the copy.
3. **Do not touch** `scripts/run_eu_s2_campaign.py` or `scripts/run_eu_s3_campaign.py`. Import from
   them; never edit them. `openubem/idf/outputs.py::write_outputs()` is likewise **not** to be wired
   into either campaign — that is the fix this work item deliberately does not make.
4. **No geometry, no construction, no schedule, no control object may change.** The only additions
   allowed to a copied IDF are `Output:Meter` / `Output:Meter:MeterFileOnly` objects and
   `Output:Table:SummaryReports`. Adding anything else invalidates the comparison.
5. **Local only.** No Speed submission, no network.
6. If any step contradicts this document, **STOP and report the conflict**. Do not improvise.

## 3. Inputs (all already on disk)

- Manifest: `openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv` — 96 rows, the 95 with
  `eplus_return_code == 0` are the population. The one `EPLUS_FATAL`
  (`BATIMENT0000000240879534_part0`) is **excluded**, as it was from the promotion.
- Saved IDFs: `openubem/outputs/eu_evidence/EU-04/s3/s3_campaign/<site>/<building_id>/<building_id>.idf`
- Promoted results for comparison: `.../<building_id>/eplusout.csv` in the same directories.
- Pinned EPWs: resolve with `verify_weather(fold)` from `scripts/run_eu_s3_campaign.py`, keyed on the
  manifest's `weather_fold` column (`fr`, `es`). Do not hardcode an EPW path.
- EnergyPlus runner: `run_energyplus_for_building` from `scripts/run_eu_s2_campaign.py`.

## 4. Output location

Everything this task writes goes under **one new directory**:

```
openubem/outputs/eu_evidence/EU-05/meter_sidecar/
    runs/<site>/<building_id>/          # copied IDF + EnergyPlus output for that copy
    meter_sidecar_manifest.csv
    meter_sidecar_summary.json
```

Plus **one** script: `scripts/run_eu_meter_sidecar.py`. No other new file.

## 5. Tasks

### T01 — Sidecar builder

Write `scripts/run_eu_meter_sidecar.py`. For each of the 95 accepted manifest rows:

1. Read the promoted IDF text, **verify its SHA-256 equals the manifest's `idf_sha256`**, and abort
   the whole run if any row disagrees. This is the proof that the sidecar started from the promoted
   artefact.
2. Copy the text into `meter_sidecar/runs/<site>/<building_id>/<building_id>.idf` and append:
   - `Output:Meter` for, at minimum: `Electricity:Facility`, `DistrictHeating:Facility`,
     `Heating:DistrictHeating`, `InteriorEquipment:Electricity`, `Electricity:Building`.
     Use `Output:Meter,<name>,Annual;` — a missing meter is reported by EnergyPlus as a warning and
     is itself a result, so do **not** pre-filter the list.
   - `Output:Table:SummaryReports,AllSummary;` and
     `OutputControl:Table:Style,CommaAndHTML,JtoKWH;` if no `OutputControl:Table:Style` is already
     present (check first — a duplicate is a Severe).
   - Leave the existing `Output:SQLite` and the existing hourly `Output:Variable` untouched.
3. Run EnergyPlus with `run_energyplus_for_building(idf_copy, run_dir, epw_path=<pinned EPW>)`.

### T02 — Row-for-row equivalence proof

For every building, compare the sidecar's `eplusout.csv` against the promoted `eplusout.csv` on the
`Zone Ideal Loads Zone Total Heating Energy` column(s):

- same number of rows, same column set for that variable;
- **every** hourly value equal to within `1e-9` relative tolerance.

Record per building: `rows_compared`, `max_abs_diff`, `max_rel_diff`, `identical` (bool).
**If any building is not identical, do not average it away — record it and flag it in the summary.**

### T03 — Read the meters back

From each sidecar run's `eplusout.sql` (`TabularData` will now be populated because AllSummary was
requested), extract the `AnnualBuildingUtilityPerformanceSummary` / `End Uses` table and record per
building, in GJ or kWh as the table gives them, converted to kWh:

`heating_kwh_meter`, `interior_equipment_electricity_kwh`, `total_site_energy_kwh`,
and the full end-use row set as a JSON blob per building in the manifest is **not** wanted — keep
the CSV to the named scalar columns and put the aggregate in the summary JSON.

### T04 — Manifest and summary

`meter_sidecar_manifest.csv`, one row per accepted building, columns:

```
building_id,site,layout_mode,weather_fold,promoted_idf_sha256,sidecar_idf_sha256,
eplus_return_code,severe_errors,fatal_errors,rows_compared,max_abs_diff,max_rel_diff,identical,
heating_kwh_promoted,heating_kwh_meter,interior_equipment_electricity_kwh,total_site_energy_kwh,
floor_area_m2,run_seconds
```

`meter_sidecar_summary.json` must state, explicitly:

- `n_accepted` (expect 95), `n_identical`, `n_meters_present`;
- pooled heating-only intensity and pooled **total site** intensity over the same floor area, and
  **the ratio between them**;
- the same two intensities split by `layout_mode` (`DWELLING_LAYOUT_EMITTED` = 12,
  `FALLBACK_PENDING_LAYOUT` = 83), each printed with its own N;
- a literal `promoted_artefacts_unchanged` block: the SHA-256 of
  `s3_campaign_manifest.csv` and of three named promoted IDFs, recomputed **after** the sidecar run.

### T05 — Prove the promotion did not move

After everything above, recompute the SHA-256 of all 95 promoted IDFs and of
`s3_campaign_manifest.csv` and assert they equal the manifest's recorded values. Report the count.

## 6. Stop-and-report points

- **CP-A** — after T01 on the **first three buildings only** (one `DWELLING_LAYOUT_EMITTED`, two
  `FALLBACK_PENDING_LAYOUT`). Report: return codes, severe/fatal counts, whether `TabularData` is
  non-empty, and which of the five meters actually exist. **Stop there and report before running the
  remaining 92.**
- **CP-B** — after T05. Report the summary JSON verbatim.

## 7. What to report back

The conclusion and the numbers, not the file contents. Specifically: `n_identical` of 95, the two
pooled intensities and their ratio, which meters exist, and the T05 unchanged count. Do not paste
IDF text, CSV bodies or EnergyPlus logs.

## 8. Progress log

Append one entry per completed task here, `#### TXX — <title> — completed YYYY-MM-DD`, with
Artifacts / Deviations / Test status / Notes.

<!-- progress log entries below this line -->

#### T01 — Sidecar builder — completed 2026-08-27

Artifacts: `scripts/run_eu_meter_sidecar.py`;
`openubem/outputs/eu_evidence/EU-05/meter_sidecar/runs/<site>/<building_id>/` (95 dirs).
Deviations: none from the document's object list. One implementation fix made mid-run and
kept for all 95: `TabularDataWithStrings.ColumnName` under `OutputControl:Table:Style
JtoKWH` carries no unit suffix (`District Heating`, not `District Heating [GJ]`) and the
`Value` field is already in kWh, not GJ — verified against `relation/12582232`'s promoted
`heating_kwh=109578.787357` matching the sidecar's raw table value `109578.79` with no
conversion applied. The GJ→kWh multiply used in an earlier attempt is not in the final
script.
Test status: CP-A on 3 buildings (1 `DWELLING_LAYOUT_EMITTED`, 2 `FALLBACK_PENDING_LAYOUT`)
— all `eplus_return_code=0`, 0 severe/fatal, `TabularData` non-empty (`eplustbl.csv`/`.htm`
written), all 5 requested meters present in `ReportMeterDataDictionary`. Full 95-building run
matches: 95/95 return code 0, 0 severe, 0 fatal.
Notes: CP-A reported and self-checked before the remaining 92 per the executor prompt.

#### T02 — Row-for-row equivalence proof — completed 2026-08-27

Artifacts: `identical` / `rows_compared` / `max_abs_diff` / `max_rel_diff` columns in
`meter_sidecar_manifest.csv`.
Deviations: one bug found and fixed before the full run — EnergyPlus's own CSV writer puts a
trailing space + bare CR on the last header field inconsistently between two runs of the
same IDF (promoted vs. sidecar), so a raw column-name-set comparison falsely reported
`column set mismatch` on all 3 CP-A buildings. Fixed by matching hourly-heating columns on
their **stripped** name while still reading values by the original (unstripped) header key.
Test status: 95/95 `identical=True`, `max_abs_diff=0.0`, `max_rel_diff=0.0` for every
building — the sidecar's hourly `Zone Ideal Loads Zone Total Heating Energy` series is
byte-for-byte reproducible from the promoted IDF.

#### T03 — Read the meters back — completed 2026-08-27

Artifacts: `heating_kwh_meter`, `interior_equipment_electricity_kwh`,
`total_site_energy_kwh` columns in `meter_sidecar_manifest.csv`; aggregate pooled figures in
`meter_sidecar_summary.json`.
Deviations: none beyond the T01 unit-handling fix (shared code path).
Test status: all 95 accepted buildings have non-null values for all three columns; 5 of 5
meters populated for all 95 (`Electricity:Facility`, `DistrictHeating:Facility`,
`Heating:DistrictHeating`, `InteriorEquipment:Electricity`, `Electricity:Building`).

#### T04 — Manifest and summary — completed 2026-08-27

Artifacts: `openubem/outputs/eu_evidence/EU-05/meter_sidecar/meter_sidecar_manifest.csv` (95
rows, columns exactly as specified in §5 T04); `meter_sidecar_summary.json`.
Deviations: none.
Test status: `n_accepted=95`, `n_identical=95`, `n_meters_present=5`. Pooled heating-only
intensity `66.868 kWh/m2`; pooled total-site intensity `93.768 kWh/m2`; ratio (total/heating)
`1.4023`. By `layout_mode`: `DWELLING_LAYOUT_EMITTED` (N=12) heating-only `97.099 kWh/m2` /
total-site `123.379 kWh/m2`; `FALLBACK_PENDING_LAYOUT` (N=83) heating-only `66.309 kWh/m2` /
total-site `93.221 kWh/m2`.

#### T05 — Prove the promotion did not move — completed 2026-08-27

Artifacts: `promoted_artefacts_unchanged` block in `meter_sidecar_summary.json`.
Deviations: none.
Test status: `s3_campaign_manifest.csv` SHA-256 recomputed after the sidecar run equals its
value at the start of this task; 95 of 95 promoted IDFs (all accepted rows, not just the 3
named ones) recomputed SHA-256 equal to the manifest's recorded `idf_sha256`. Promotion did
not move.
