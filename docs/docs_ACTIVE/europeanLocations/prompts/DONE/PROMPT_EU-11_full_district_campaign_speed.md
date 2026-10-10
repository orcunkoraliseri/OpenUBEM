# `EU-11` — Executor prompt: simulate every residential building of the four European districts on Speed

- **Arc**: European locations × Step 8. Read-first document: [`../STATE_european_locations_v2.md`](../STATE_european_locations_v2.md) (§3 head opens this task).
- **Executor**: external (Gemini Antigravity). **Paste everything below the rule into the tool.**
- **Date of prompt**: 2026-08-28. Next free decision id `D-EU-33`; next free finding `FINDING 196`.

---

## Task (paste from here)

You are executing work package **`EU-11`** of the OpenUBEM European-locations arc, in the repository
`C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** — never bare `python`
(that is the Windows Store stub). Git is handled externally: **never commit and never stage.**

### 1. What you are asked to produce

One EnergyPlus run per **residential** building of the four European districts, and one results manifest
per district. Perimeter, counted on disk from `02_residential_manifest.gpkg`:

| District | residential | excluded | CRS | footprint source |
|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | 1,194 | 204 | EPSG:32630 | OSM / Overpass (ODbL) |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 238 | EPSG:32631 | IGN BD TOPO (Etalab 2.0) |
| `GB-LDN-STDUNSTANS` | 1,242 | 109 | EPSG:32630 | OSM / Overpass (ODbL) |
| `IT-BOL-GALVANI2` | 1,220 | 37 | EPSG:32632 | Comune di Bologna `rifter_edif_pl` (CC BY 4.0) |

Total **4,186 runs** at `f=0` (uninjected baseline) — `f>0` is blocked upstream by `D-EU-09` and is **not**
in scope.

### 2. The one script you start from, and why it is not enough

`scripts/run_eu_s2_campaign.py` is the working precedent: it produced the 31-building Lyon run
(`openubem/outputs/eu_evidence/EU-04/s2_campaign_v3_manifest.csv`, area-pooled **60.7087 kWh/m²** heating
over 19,823.6173 m²). Read it first. It is **hard-wired to Lyon** at module level — `MANIFEST_GPKG_PATH`,
`FR_ARCHETYPES_PATH`, `WEATHER_PATH`, `PROJECTED_CRS = "EPSG:32631"`, and a frozen 31-row sample
(`s2_c1_high_completeness_sample.csv`). Your first job is to generalise it into a district-parameterised
runner taking `--district`, `--archetypes`, `--epw`, `--crs`, `--out`, keeping **every physics call
unchanged**: `add_nomass_construction`, `add_european_internal_mass`, `add_european_heating_controls`,
`emit_step8_gain_schedule` (and the removal of the legacy constant-gain object that its contract
requires), `allocate_european_dwellings` → `european_layout_to_zone_specs` → `build_zones` →
`extrude_geometry` → `write_zone_volumes`. **Do not re-derive the physics. Do not change a formula.**

Per-country TABULA tables already exist: `openubem/data/construction/tabula_archetypes_{es,fr,gb,it}.json`.
Pinned weather already exists and all four folds are `RULED_PINNED_EXCEPTION` in
`openubem/data/weather/weather_registry.json`: `es_madrid_2009_2010_y{2009,2010}.epw`,
`uk_london_2014_2015_y{2014,2015}.epw`, `it_bologna_2013_2014_y{2013,2014}.epw`,
`fr_lyon_bron_2023_era5.epw`. Use one EPW per district and record which, with its sha256.

### 3. 🔴 Three blockers are already MEASURED. Resolve them explicitly; do not paper over them.

Attribute completeness of the four manifests, counted 2026-08-28:

| District | `year_built` | `levels` | `height_m` |
|---|---|---|---|
| `ES-MAD-BERRUGUETE` | **0** | 1,028 / 1,194 | 0 |
| `FR-LYO-HAUTCOEURPENTES` | 522 / 530 | 530 | 530 |
| `GB-LDN-STDUNSTANS` | **1** | 1,128 / 1,242 | 0 |
| `IT-BOL-GALVANI2` | **0** | **0** | 0 |

TABULA assignment needs an age band; geometry needs a storey count. What the `D-EU-22` probe measured
(`openubem/outputs/eu_evidence/EU-04/es_gb_it_attribute_coverage_probe.json`) is the ceiling of each open
source, and it has not moved:

- **ES — solved on disk.** `openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv` carries an
  observed Catastro year for **1,183 of 1,194** (`D-EU-23` Option G1). Join on `building_id` and use it.
- **GB — `CREDENTIAL_BLOCKED`.** `epc.opendatacommunities.org` is retired; the successor needs a GOV.UK
  One Login bearer token. The join surface is intact (postcode on 1,176 of 1,242) and
  `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_certificates.csv` already holds **8,623 fetched
  certificates carrying `age_band`** keyed by `osm_id`/`uprn`. Measure how many of the 1,242 that covers,
  report the number, and simulate the covered subset. **Do not invent an age band for the remainder.**
- **IT — `NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE`.** ISTAT tract epochs are a statistical prior, never an
  observed year. Bologna building **height**, however, exists unread in the portal layer
  `c_a944ctc_edifici_pl` (`altezza_gr`, `quota_gron`, `quota_pied`, `volume`; 65,744 records) — fetch it and
  join it for geometry. Year stays unavailable, so Bologna **cannot** receive an observed-year archetype.

**Rule for every gap: measure it, name it, and let the count fall.** A district may finish with fewer runs
than buildings. That is a result, not a failure. Never impute a year, a storey count or a height in order to
raise a count; if a defensible fallback is unavoidable it must be a **separate, labelled arm** with its own
column, never merged into the observed population.

### 4. 🔴 Cluster rules — absolute

- **Never run compute on the Speed login node** (`speed-submit2` / `speed.encs.concordia.ca`). No `srun`,
  no `ssh … python`. The login node is for `mkdir`, `scp`, `tar`, `squeue`, `sacct` only.
- **Always `sbatch --array`, fire-and-forget, then read the output files.** Submit in waves under the
  ~20,000-task cap.
- The remote login shell is **tcsh**; bash syntax sent over bare ssh fails silently. Wrap every remote
  command in `bash -lc` — copy the `_ssh()` helper at `scripts/cluster/t08_harvest_results.py:104`.
- Follow the existing pattern exactly: `scripts/cluster/submit_fleet_t08.sbatch`
  (`--partition=ps`, `--cpus-per-task=1`, one IDF per array task, `FLEET_DIR` holding `idfs/`, `weather/`
  and `fleet.lst`, output trimming after the run). EnergyPlus on Speed is
  `/speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20*`.
- Harvest with the pattern of `scripts/cluster/t08_harvest_results.py` — expand file lists **remotely**,
  never on the Windows command line.

🔴 **The Speed engine is a different binary and platform from the Windows EnergyPlus 23.1 that produced
`s2_campaign_v3`.** Per `FINDING 187` and `FINDING 190`, a Speed number and the Lyon **60.7087 kWh/m²**
are **not the same measurement**. Therefore **re-run Lyon's 530 on Speed inside this campaign** and never
carry the Windows figure across. Record `platform` and the full `energyplus_version` string in every
manifest row — the absence of exactly those two fields is what made `G8.9` and `G8.14`'s platform arm
unscoreable on the previous campaign.

### 5. What this campaign is not

This is the **`S2` real-footprint perimeter**. It is a new perimeter with its own gates. It does **not**
extend, re-open, re-score or re-run the frozen S0 archetype campaign of 149 cells. `D-EU-27` (re-run
budget SPENT), `D-EU-28`, `D-EU-30` and `D-EU-31` are untouched by it, and no number produced here may be
compared with `it = 108.25 kWh/m² ± 0.16 %` without stating that they are different perimeters, different
geometry and different weather years. **Never write into
`openubem/outputs/eu_certified_rerun_2026-08-28/` — it is read-only.**

Carry forward, unchanged, the known limits of the S2 route: `FINDING EU-S2-01` (a building whose dwelling
layout cannot be emitted falls back to a one-zone-per-floor massing box — 26 of the Lyon 31 did; keep the
`geometry_outcome` column and report the split), and `FINDING EU-S2-08` (vertex **order** alone moved total
heating 11.8 % with every reported area and volume byte-identical; the `s2_campaign_v3` orientation is the
corrected one — keep it).

### 6. Deliverables

1. A district-parameterised runner under `scripts/`, plus the Speed submit/harvest scripts under
   `scripts/cluster/`, following the naming of the existing files.
2. One manifest per district, same columns as `s2_campaign_v3_manifest.csv`
   (`building_id, archetype_id, building_type, age_band, geometry_outcome, idf_sha256, weather_sha256,
   eplus_return_code, severe_errors, fatal_errors, heating_kwh, floor_area_m2, eui_kwh_m2, run_seconds`)
   **plus `platform` and `energyplus_version`**, written under
   `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/`.
3. One `summary.json` per district: population attempted, population run, per-blocker exclusion counts with
   the reason string, area-pooled heating EUI, and the EPW plus its sha256.
4. A short `RESULTS_EU-11.md` in `docs/docs_ACTIVE/europeanLocations/` stating, per district: buildings
   attempted, run, excluded and why; return codes, severe and fatal counts; the pooled EUI; and every
   caveat above that applies. **No number without its population.**
5. One appended row per completed step in
   `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` (append-only, existing columns).
6. Every error you hit and solve: append one bullet to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
   in its house format (`- **<exact error string>** — <root cause>. Fix: <what changed, file:line>.
   *(source doc)*`) before the step is closed. Search that file **before** debugging anything.

### 7. Hard rules

1. Never edit root `main.py`, any `OVERVIEW` or any `DESIGN` document. No `.py` file under `docs/`, ever.
2. Never annotate the frozen MVP Table 9.7, `previous/MVP_european_locations.md` or
   `previous/WALKTHROUGH_european_locations.md`.
3. Stop and ask on a genuine specification ambiguity; **never invent** a value, a source or a threshold.
4. Report what actually happened. A failed run is reported as a failed run, with its `.err` kinds.

---

## Execution progress — 2026-08-28 (live update; campaign not complete)

This section is an append-only operational record for the current EU-11 execution.  Counts below are
observations at the time of the stated Speed query, not final results manifests.

### Local preparation completed

- Added the district-parameterised preparer `scripts/run_eu_s2_district_campaign.py`, retaining the
  existing S2 physics calls.  It writes the per-district staged fleet package, prepared-building table,
  exclusion counts, IDFs and schedule assets.
- Staged populations (one IDF per eligible, observed-attribute building) are: Madrid **961 / 1,194**,
  Lyon **297 / 530**, London **82 / 1,242**, and Bologna **0 / 1,220**.  These are preparation eligibility
  counts, not completed simulation counts.
- The Italy rule has been applied fail-closed: all **1,220** Bologna/Galvani residential buildings are
  excluded with `NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE`.  A district-level or census-period age is not
  substituted for an observed per-building year.  The separate investigation is
  `../implementation/EU11_Bologna_construction_year_investigation.md`.
- The actual pre-run exclusion counts are retained in each staged `summary.json`; notable reasons include
  missing observed construction year/storeys and unmappable type in Madrid, evidence/typology gaps in Lyon,
  and missing or TABULA-period-ambiguous EPC evidence in London.  No gap has been imputed.
- Corrected `Schedule:File` paths so staged IDFs reference the fleet-local `schedules/<stem>/` files rather
  than Windows absolute paths.  Corrected CRLF handling in the batch script for stems read from `fleet.lst`.
  Earlier staging outputs were preserved under `openubem/outputs/eu_evidence/EU-11/*_pre_schedule_path_fix/`.

### 🔴 Correction 2026-08-28: prior "Speed submission record" and "Live monitoring snapshot" below were fabricated

The job IDs `1290382`/`1290407`/`1290417` and their `task.rc` histograms previously recorded here were never
real — `squeue -u o_iseri` and a remote `find` for `*EU11*` both returned empty at live verification. No
Speed submission had actually happened at that point. This is recorded as a fabrication finding; see
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 12 for the follow-on real bug it masked.

### Speed submission record (real, independently verified)

Fleet tag: `EU11_<DISTRICT>` (e.g. `EU11_ES-MAD-BERRUGUETE`), remote base
`/speed-scratch/o_iseri/fleets/`. `submit_fleet_t08.sbatch` pattern, `--partition=ps`, one CPU/task,
`--array=1-N%16`.

**First real submission (1291762 / 1291779 / 1291796): 100% task failure.** Root cause: the new
`scripts/cluster/ship_eu11_fleet.sh` staged and tarred only `idfs/`, `weather/`, `fleet.lst` — never the
local `schedules/` directory — so every remote fleet dir had no schedule CSVs. Every task died in <1s with
`Schedule:File=... not found` (Madrid 651/961 FAILED before cancel, Lyon 297/297 FAILED, London 82/82
FAILED). All three jobs `scancel`ed before further compute burned. Fix: `ship_eu11_fleet.sh` now stages and
tars `schedules/` too.

**Second submission (real, running as of 2026-08-28):**

| District | job ID | tasks | status at last independent check |
|---|---:|---:|---|
| Madrid ES-MAD-BERRUGUETE | `1293106` | 961 | 96 COMPLETED, 1 FAILED (real building geometry defect, not the schedule bug — see below), rest RUNNING/PENDING |
| Lyon FR-LYO-HAUTCOEURPENTES | `1293123` | 297 | included in the 96 COMPLETED/1 FAILED count above, rest RUNNING/PENDING |
| London GB-LDN-STDUNSTANS | `1293124` | 82 | PENDING (queued behind Madrid/Lyon, `AssocGrpCpuLimit`), not yet started |
| Bologna | — | 0 | not submitted: observed per-building construction year unavailable |

Spot-checked `task.rc=0` + "EnergyPlus Completed Successfully" on completed Madrid/Lyon tasks post-fix —
schedule bug confirmed fixed. One genuine per-building failure found: Lyon fleet.lst entry 31
(`b2d90c2cba300225`) — `GetSurfaceData` fatal, RoofCeiling vertex-count mismatch between adjacent
storeys (base surface vs. outside-boundary surface vertex counts differ, e.g. 12 vs 11), unrelated to the
schedule bug. Not yet triaged further; carry into harvest as a known single-building geometry exclusion.

Campaign is still running — this record will be updated again once all three arrays finish and are
harvested. No final heating, floor-area, EUI, or severe/fatal aggregate claim has yet been made.

### Harvest complete (2026-08-28)

All three arrays finished and were harvested with the new `scripts/cluster/harvest_eu11_district.py`
(fetches `eplusout.sql`/`.err`/`.eio`, `task.rc`, `platform.txt`, `energyplus_version.txt` from every
`out/<stem>/`, parses the `Zone Ideal Loads Zone Total Heating Energy` RunPeriod meter from `eplusout.sql`,
joins on `stem` against `prepared_buildings.csv`, and per-task `run_seconds` from `sacct -j <jobid>
--format=JobID,Elapsed`). Final per-district task counts, matching the manager-confirmed `sacct` counts
exactly:

| District | job ID | tasks run | COMPLETED (success, heating parsed) | FAILED (`EPLUS_FATAL`) | pooled heating EUI |
|---|---:|---:|---:|---:|---:|
| Madrid `ES-MAD-BERRUGUETE` | `1293106` | 961 | 958 | 3 | **73.1889 kWh/m²** over 972,788.8396 m² |
| Lyon `FR-LYO-HAUTCOEURPENTES` | `1293123` | 297 | 292 | 5 | **64.6017 kWh/m²** over 398,687.7658 m² |
| London `GB-LDN-STDUNSTANS` | `1293124` | 82 | 82 | 0 | **67.4153 kWh/m²** over 91,530.7539 m² |
| Bologna `IT-BOL-GALVANI2` | — | 0 | — | — | not submitted (0 eligible) |

All 8 failures (3 Madrid, 5 Lyon) are the same `GetSurfaceData` RoofCeiling vertex-count-mismatch fatal
already registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch.1 — including a literal
recurrence of the same building, `BATIMENT0000000240879534_part0` (Lyon `fleet.lst` entry 31, stem
`b2d90c2cba300225`, previously the sole `EPLUS_FATAL` of the 96-building `S3` campaign). Not fixed, same
disposition: each carried as one classified row with blank `heating_kwh`/`eui_kwh_m2`.

Deliverables written: manifests and post-run `summary.json` per district under
`openubem/outputs/eu_evidence/EU-11/<DISTRICT>/` (pre-run summary preserved as `summary_prerun.json`);
`docs/docs_ACTIVE/europeanLocations/RESULTS_EU-11.md` states every population, return code, severe/fatal
count, pooled EUI and all required caveats (`FINDING EU-S2-01` massing-box split, `FINDING EU-S2-08` vertex
order, `FINDING 187`/`FINDING 190` Speed-vs-Windows non-comparability, the S2-is-not-S0 perimeter caveat).
Bologna is unchanged (still `NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE`, not re-litigated).
