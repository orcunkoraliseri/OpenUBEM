# OpenUBEM → 6J — facts for the 10-building smoke run on the six new city fleets, 2026-10-13

Answer to the six questions relayed by gsscanada-8e. Read-only lookup; nothing was changed, nothing was run on Speed. Paths are relative to the repo root unless they start with `/speed-scratch`. "NOT KNOWN" = not recorded in our files or not checked. Facts below were read from the local fleet trees (`openubem/outputs/eu_evidence/EU-11/<SITE>_win_<date>/`), which are what `stage_eu22_site.sh` copied to Speed; one sample IDF per site was inspected, the Budapest one in full.

**Which tree is the live fleet per site** (the Speed folder is `/speed-scratch/o_iseri/fleets/EU22_<SITE>_<tag>/`):

| Site | tag | IDFs = `fleet.lst` lines | weather file in `weather/` |
|---|---|---|---|
| AT-VIE-RUDOLFSHEIM | `win_2026-10-10` | 536 | `at_vienna_2007_2008_y2008.epw` |
| CA-MTL-PLATEAU | `win_2026-10-09` | 710 | `ca_montreal_tmyx_2009_2023.epw` |
| FI-HEL-KALLIO | `win_2026-10-10` | 580 | `fi_helsinki_tmyx_2009_2023.epw` |
| HU-BUD-ERZSEBETVAROS | `win_2026-10-10` | 805 | `hu_budapest_tmyx_2009_2023.epw` |
| ZA-CPT-WOODSTOCK | `win_2026-10-09` | 525 | `za_capetown_tmyx_2009_2023.epw` |
| AM-EVN-NORNORK | `win_2026-10-09` | 551 | `am_yerevan_tmyx_2009_2023.epw` |

Vienna, Helsinki and Budapest also have older `win_2026-10-09` folders (superseded by the division fix, D-EU-168); do not use those. Folder ↔ job ids: `speed_jobs.txt` in each local tree.

## 1. How a fleet is run on Speed

- **Job script:** `scripts/cluster/submit_eu22_site.sbatch` (copied into each fleet folder as `submit_eu22_site.sbatch`). Command printed by the staging script (`scripts/cluster/stage_eu22_site.sh`, last line): `cd <FLEET> && sbatch -p ps --time=7-00:00:00 --array=1-<N>%32 --mem=32G --export=ALL,FLEET_DIR=<FLEET> submit_eu22_site.sbatch`. Array task *i* runs the stem on line *i* of `fleet.lst` (sbatch lines 24-28).
- **What one task does** (sbatch lines 36-70): `cd out/<stem>`; copy the IDD and `idfs/<stem>.idf` to `in.idf`; run `ExpandObjects` (needed: the IDFs use HVACTemplate objects); run `energyplus -w <the first *.epw in weather/> -d out/<stem> expanded.idf`; write `task.rc`; delete bulk output. **Kept per building:** `eplusout.sql`, `eplusout.eio`, `eplusout.end`, `eplusout.err`, `task.rc`, `energyplus_version.txt`, `platform.txt`.
- **EnergyPlus:** 23.1.0, `ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20*` (first match), binary `<dir>/energyplus` and `<dir>/ExpandObjects` (sbatch lines 33-35). The IDFs say `Version, 23.1` (IDF line 4).
- **Python env on Speed:** none needed for the run (bash + EnergyPlus only). Harvest runs on the local machine afterwards. (`/speed-scratch/o_iseri/envs/openubem_eu22/` exists but belongs to the division-fix array.)
- **Resources:** 1 CPU per task (`--cpus-per-task=1`), memory 32 GB on the command line (the script's own 6 GB line is overridden), partition `ps`, `--time=7-00:00:00`.
- **Time per building (measured, not guessed):** mean 562 s per task over the Helsinki/Vienna/Budapest array (530 / 604 / 561 s per site; `prompts/PROMPT_MANAGER_handoff_2026-09-09.md:42`). The other three sites: NOT KNOWN here (not read from `sacct`).
- **Script hard-codes** `--output=/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log` and the EnergyPlus path; a 6J copy should pass its own `--output` and keep the EnergyPlus glob.
- **Capacity rule (owner, 2026-10-09):** our runs together use at most 32 CPUs (the account cap is 64, shared with other projects); a 10-building test is far below that, but nobody should add an array wider than the free share without the owner. No compute on the login node; submit with `sbatch`.

## 2. How the gain csv reaches the model

- **Per zone (one zone = one dwelling), two objects** (Budapest sample `0022b4b3f27eb2ce.idf`: 42 zones, 42 of each):
  - `SCHEDULE:FILE` (IDF lines 91-100 for the first): name `EU_Step8_GainSchedule_<stem>_F<floor>_dwelling_<k>_f000`, type limits `EU_Step8_AnyNumber_Wm2` (no limits), **Column Number 1, Rows to Skip 0, 8760 hours, Comma, Interpolate to Timestep = No, Minutes per Item = 60, Adjust Schedule for Daylight Savings = Yes**.
  - `OTHEREQUIPMENT` (first at the line of `OTHEREQUIPMENT,` after the schedules): Fuel `Electricity`, method `Watts/Area`, **Power per Zone Floor Area = 1** (so the schedule value *is* W/m²), Fraction Latent 0, Radiant 0, Lost 0 (all heat convective), end-use subcategory `EU_Step8_InternalGains`. Built by `openubem/campaign/eu_cell_runner.py:381-392` (`emit_step8_gain_schedule`).
- **The csv:** one column, **no header**, 8,760 lines, one number per hour. Sample file `schedules/0022b4b3f27eb2ce/0022b4b3f27eb2ce_F0_dwelling_0_f000_gain.csv`: first values `3`, 8,760 lines. File name pattern `schedules/<stem>/<stem>_F<floor>_dwelling_<k>_f000_gain.csv`; one file per zone (42 in the sample folder). The `f000` is our "f = 0" (unchanged) case.
- **Path is relative, not absolute:** `../../schedules/<stem>/<file>` (IDF line 94). The run folder is `<fleet>/out/<stem>/` (the task `cd`s there and runs the copy `in.idf` / `expanded.idf` from it), so `../../schedules` is `<fleet>/schedules`. **A copied fleet keeps pointing at its own copy as long as it keeps the same shape** `<fleet>/{idfs, out/<stem>, schedules/<stem>, weather, fleet.lst}`. If 6J runs from a folder that is not exactly two levels below the folder holding `schedules/`, the path breaks. Zero IDFs of the Budapest tree contain `C:\`, `/speed-scratch` or `/Users`; the other five were not grepped (NOT KNOWN).

## 3. Where the per-building annual heating lives

- **Source of truth for a rerun comparison:** `<fleet>/out/<stem>/eplusout.sql`. Heating = `SELECT SUM(r.Value) FROM ReportData r JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex WHERE d.Name = 'Zone Ideal Loads Zone Total Heating Energy'`, then × 1/3.6e6 to get **kWh** (sum over every zone and every hour; `scripts/cluster/harvest_eu11_district.py:209-219`, `J_TO_KWH` at line 98). The raw sum is unrounded.
- **Rounded copies (do not use for a 1e-6 test):** the district manifest `<SITE_lowercase_underscores>_manifest.csv` in each local tree, column `heating_kwh` (kWh, rounded to 6 decimals, `harvest_eu11_district.py:371`), `floor_area_m2`, `eui_kwh_m2`, `eplus_return_code`; and `docs/docs_ACTIVE/europeanLocations/results/EU22_results_<SITE>_<date>_per_home.csv`, columns `heating_kwh`, `eui_heating_kwh_m2` (kWh/m², 6 decimals), key `building_id`. Compare 6J's rerun of the unchanged copy against the **sql of the original `out/<stem>`**, not against these.
- **Stem ↔ building id:** `prepared_buildings.csv` in the local tree has both columns `building_id` and `stem`; the manifest and results files are keyed by `building_id` only. Pick the 10 stems from homes that are **not** in `left_out.csv` and have `has_result = True` in the per-home csv.
- **Completion gate:** a run counts only if `eplusout.end` contains "EnergyPlus Completed Successfully" and `task.rc` is 0.
- **Same-binary reproducibility on another node:** NOT KNOWN (not tested). Same EnergyPlus build on Speed nodes should reproduce; if the 1e-6 test fails on one node, rerun on a second before suspecting the copy.

## 4. Output variable for the gain

- **Not requested.** The only output request in the IDF is (IDF last lines): `OUTPUT:VARIABLE, *, Zone Ideal Loads Zone Total Heating Energy, Hourly;` and `OUTPUT:SQLITE, SimpleAndTabular, UseOutputControlTableStyle;`. No electric-equipment or other-equipment variable, and no meters.
- **Safe way, copy only:** append to the copy of `idfs/<stem>.idf` (never ours) `OUTPUT:VARIABLE, *, Zone Other Equipment Total Heating Rate, Hourly;` (E+ 23.1 name; W per zone; `Zone Other Equipment Total Heating Energy` for J). The task copies the IDF to `in.idf` before `ExpandObjects`, which keeps Output objects, and the sql is kept by the cleanup step, so the hourly values land in `eplusout.sql` (`ReportData` joined on `ReportDataDictionary.Name`). Adding an output does not change the simulation, and our heating query filters by variable name, so the heating sum is unaffected; still check that the unchanged copy's heating equals the original to 1e-6 after adding it. The sbatch deletes `*.eso`, `*.csv`, `*.mtd` etc., so read the new variable from the sql, not from a csv.
- Per-zone values come out as one row per zone key (`KeyValue` = upper-case zone name = `<stem>_F<floor>_dwelling_<k>`).

## 5. RunPeriod and weather

- **RunPeriod (all six sample IDFs identical, IDF lines 56-69):** Jan 1 to Dec 31; **Begin Year and End Year blank**; **Day of Week for Start Day = Sunday**; no weather-file holidays, no daylight-saving period, no weekend-holiday rule. Because the year is blank the calendar is the one the start weekday implies, not a year read from the weather file.
- `SizingPeriod:WeatherFileDays` (IDF line 44-54) lists Monday as start day, but `Run Simulation for Sizing Periods = No` (SimulationControl), so it does not drive the annual result. Sizing calculations are on (zone/system/plant).
- **Weather per site:** see the table above (one `.epw` per `weather/` folder; the sbatch takes the first). Vienna's file is a single-year 2008 file (`y2008`); the other five are 2009–2023 TMYx-style files built by us. Licence terms of each weather file: NOT KNOWN in this answer (Cape Town's ERA5 pieces are under `openubem/data/weather/raw/era5_capetown_2009_2010/`).

## 6. What must not be copied, and absolute paths

- **Cape Town (ZA-CPT-WOODSTOCK):** the IDF geometry is built from the City of Cape Town footprints. D-EU-160: internal use for 6J only, non-commercial, no public release, credit "City of Cape Town". Keep the copy in the 6J-only Speed folder; nothing from it into a public place (see `2026-10-13_OpenUBEM_to_6J_capetown_licence.md`).
- **Yerevan (AM-EVN-NORNORK):** source is not an open licence (Armstat; open owner call, handoff line 23). Treat like Cape Town for any public use. **Budapest:** brochure cross-check still open (same line); no licence restriction known for internal use.
- **What is on Speed in a fleet folder:** only `idfs/`, `weather/`, `schedules/`, `fleet.lst`, `submit_eu22_site.sbatch` and `out/` (`stage_eu22_site.sh`, the `tar` line). The local-only items (`layouts/`, `prepared_buildings.csv`, `origin_offset.json`, manifests, `left_out.csv`, `sidecar_population.csv`) are **not** on Speed. The IDF coordinates are absolute UTM (shifted by `origin_offset.json` locally); never add that file to a fleet.
- **Absolute paths:** none in IDFs or `fleet.lst` (Budapest checked). The only absolute paths are in `submit_eu22_site.sbatch` (log directory, `/speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*`).
- **Do not touch** the originals under `/speed-scratch/o_iseri/fleets/EU22_*` (comparison baseline), nor Bologna / `handover_4J_2026-10-06` (frozen until 4J reports done).
