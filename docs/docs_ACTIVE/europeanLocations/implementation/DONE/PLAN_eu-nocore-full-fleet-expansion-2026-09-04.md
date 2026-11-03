# PLAN — `eu-nocore-full-fleet-expansion` (2026-09-04)

Slug: `eu-nocore-full-fleet-expansion`. DESIGN pointer: `docs/docs_ACTIVE/europeanLocations/BRIEF_european_locations_v5.md`,
`STATE_european_locations_v5.md` (`D-EU-101`, `FINDING 251`, `FINDING 252`).

Owner ruling (`D-EU-101`, verbatim): *"of course, all types of residentials will be included no matter what
their function is... this is same for other neighbourhoods as well."* Gap: London +1,160, Lyon +237, Madrid
+242, Bologna +20 (+1,659 total, cadastral fleet 4,186).

## 1. Corrects the stale task breakdown

`CHECKLIST_european_locations_v5.md`'s `eu-nocore-full-fleet-expansion` T01–T06 (written before this plan)
assumed the gap population needs a row in `EU-20/morphology_census.csv` before anything else can run, and
that the no-core cutter is a separate step from IDF generation. Both assumptions are wrong —
🔴 **`FINDING 252`**: the production Speed-IDF pipeline (`scripts/run_eu_s2_district_campaign.py::prepare`)
never reads `EU-20/morphology_census.csv` at all. It reads the raw manifest
(`openubem/outputs/eu02/<district>/02_residential_manifest.gpkg`, `prepare()` line 356–357) directly, classifies
each building inline via `_gb_rows`/`_it_rows`/`_mapped_rows`, then calls `_geometry()` (line 112) which invokes
the already-carried-in no-core engine (`generate_european_building_dwelling_layout`,
`openubem/geometry/european_residential.py`) and writes IDFs in the same pass. There is no separate "run the
cutter" step and no `morphology_census.csv` dependency. `morphology_census.csv` belongs to the EU-20/EU-21
rule-grading pipeline (550 test plates, the 95 % coverage bar) — a different, already-closed artifact, not an
input to `prepare()`. Proof already on record: London's 82→389 recovery (`FINDING 251` T01) was made by fixing
`_gb_rows` alone and re-running `prepare()` — no `morphology_census.csv` row was ever written for the 307
newly-mapped buildings.

**Consequence:** T01–T03 below replace the CHECKLIST's T01–T06. Fixing the classification functions and
re-running `prepare()` per district *is* the full prep — cutter and IDF generation are the same step.

## 2. Hard rules for the executor

- Local-only. No cluster (`ssh`, `scp`, `sbatch`) — packaging and Speed submission (CHECKLIST's old
  T04/T05) stay with the director once the current 2,527-task campaign drains. Do not attempt them.
- `python` is not on `PATH`. Always call `.venv\Scripts\python.exe` (repo root) or the POSIX equivalent
  `.venv/Scripts/python.exe` if running under Git Bash.
- Do not edit `openubem/geometry/european_residential.py`, `openubem/geometry/european_nocore.py`, or any
  `openubem/geometry/zoning.py` — the no-core engine is closed and accepted (`D-EU-95`, `CP-4`). This task
  touches only the two classification files named in T01.
- No new `.sbatch`, no `git commit`, no `git push`. Leave the working tree as diffs + new output folders;
  the director reviews and commits.
- Never touch `openubem/outputs/eu_evidence/EU-11/*_finding249_remedy_2026-09-04/` (the live, still-running
  Speed campaign's source fleet) — write every new output under a `*_full_fleet_2026-09-04/` folder, never
  overwriting the remedy folder.
- Evidence discipline: quote the real `summary.json` / exclusion `Counter` numbers verbatim in the progress
  log. Never paraphrase a count.
- Stop at the end of T03 and report. Do not proceed to packaging.

## 3. File layout

- Edit: `openubem/semantic/european_archetype_mapping.py` (one line).
- Edit: `scripts/run_eu_s2_district_campaign.py` (`_mapped_rows`, one line).
- New output per district: `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_full_fleet_2026-09-04/`
  (`prepared_buildings.csv`, `idfs/*.idf`, `weather/`, `schedules/`, `<slug>_manifest.csv`, `summary.json`).
- Progress log: append to this file's §8 only. Do not edit `BRIEF_*`, `STATE_*`, or `CHECKLIST_*` — the
  director folds your progress log into those after review.

## 4. Dependency decisions (pinned)

- No new Python dependency. `compute_footprint_adjacency` is already imported in
  `scripts/run_eu_s2_district_campaign.py:37` — reuse it, do not reimplement.
- Existing archetype JSONs (`openubem/data/construction/tabula_archetypes_*.json`) and the ES cadastral
  sidecar (`openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv`) are used unchanged.

## 5. DESIGN facts (verified by direct read, 2026-09-04)

- `openubem/semantic/european_archetype_mapping.py:225` — `if building_type is None and country == "FR":`
  gates the two-signal (`observed_dwellings` + `storeys` + `is_attached`) derivation
  (`derive_bdtopo_building_type`, lines 185–201, the `D-EU-04-G` Option G1 rule) to FR only. `country`
  already accepts `{"ES","GB","IT","FR"}` at line 213 — only the derivation branch is FR-gated.
- `scripts/run_eu_s2_district_campaign.py:334-351` (`_mapped_rows`) — line 336–337 applies the ES cadastral
  sidecar (`apply_attribute_sidecar`, supplies `observed_dwellings`) but never assigns `is_attached` for ES,
  unlike line 339's FR branch (`gdf.assign(is_attached=compute_footprint_adjacency(gdf))`). Without this,
  widening line 225 alone is unsafe: `map_observed_building_to_tabula` (line 228-229) reads
  `row.get("is_attached")`, gets `None` for every Madrid row, and `derive_bdtopo_building_type` then always
  returns `"SFH"` for `dwellings==1` (line 196: `"TH" if is_attached else "SFH"`, and `bool(None)` is
  `False`) — every Madrid single-dwelling gap building would silently become detached, never terraced. Both
  edits ship together or not at all.
- `scripts/run_eu_s2_district_campaign.py:170-203` (`_gb_rows`, `FINDING 251` T01, already shipped and
  verified) — the pattern to mirror: `is_attached_series = compute_footprint_adjacency(gdf)` once, then per
  building `"TH" if bool(is_attached_series.loc[idx]) else "SFH"`.
- `scripts/run_eu_s2_district_campaign.py:354-475` (`prepare()`) — the single entry point that reads the raw
  manifest, classifies, and writes IDFs. CLI: `--district <D> --out <PATH>` (required), `--archetypes PATH`,
  `--epw PATH`, `--crs` (optional overrides). Writes `summary.json` with `population_attempted`,
  `population_prepared`, `blocker_exclusions` (a `Counter`, verbatim) — this is what T03 reads back.
- Lyon (`_mapped_rows`, FR) and Bologna (`_it_rows`, lines 206-331) do **not** have GB's "tag never mapped"
  defect — Lyon already runs the same two-signal derivation this plan extends to ES; Bologna derives type
  purely from height/storeys + `is_attached`, no tag lookup at all. Their +237 / +20 gaps are not expected to
  close from this code change — they are the same class of real data gap as GB's remaining ~900
  (missing cadastral join, missing period match) and are **not in scope** for this plan. Report their T03
  numbers as-is; do not attempt to code around them.
- Local output convention: `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/` is
  the live campaign's source folder (STATE_european_locations_v5.md:617,1336). This plan's outputs use the
  sibling tag `_full_fleet_2026-09-04` so the two never collide.

## 6. Tasks

### T01 — extend the classification fix from GB to ES

**What**: two edits.
1. `openubem/semantic/european_archetype_mapping.py:225` — `if building_type is None and country == "FR":`
   → `if building_type is None and country in ("FR", "ES"):`
2. `scripts/run_eu_s2_district_campaign.py:336-337` — inside the
   `if district == "ES-MAD-BERRUGUETE":` branch, after applying the sidecar, add
   `gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))` (same call as FR's line 339).

**Why**: `FINDING 251`/`D-EU-101` — Madrid's +242 gap includes buildings excluded only because the FR-only
gate never let ES reach the two-signal derivation at all (§5 above).

**How to test**: run
`.venv\Scripts\python.exe -c "from openubem.semantic.european_archetype_mapping import map_observed_building_to_tabula; import inspect; print('FR' in inspect.getsource(map_observed_building_to_tabula) and 'ES' in inspect.getsource(map_observed_building_to_tabula))"`
to confirm the edit landed, then proceed straight to T02 — the real test is Madrid's `summary.json` count.

### T02 — re-run all four districts through `prepare()`

**What**: for each district, run
`.venv\Scripts\python.exe scripts\run_eu_s2_district_campaign.py --district <DISTRICT> --out openubem\outputs\eu_evidence\EU-11\<DISTRICT>_full_fleet_2026-09-04`
Districts: `GB-LDN-STDUNSTANS`, `FR-LYO-HAUTCOEURPENTES`, `ES-MAD-BERRUGUETE`, `IT-BOL-GALVANI2`. Run all
four — including London, whose `_gb_rows` fix (82→389) was only verified at the classification stage, never
carried through a full `prepare()` re-run to produce actual IDFs for the new 307.

**Why**: this single call performs classification + no-core cutting + IDF writing (§1). No separate cutter
invocation exists in this architecture.

**How to test**: each run must exit 0 and leave `summary.json`, `prepared_buildings.csv`, and a non-empty
`idfs/` directory in its output folder. A district with `population_prepared == 0` is a stop-and-report, not
a silent continue.

### T03 — audit and report

**What**: for each district, read the new `summary.json` and report `population_attempted`,
`population_prepared`, and the full `blocker_exclusions` dict verbatim. Compare `population_prepared` against
the last known narrow-census counts (London 389 post-fix / 82 pre-fix, Lyon 293, Madrid 952, Bologna 1,200 —
`STATE_european_locations_v5.md`, `FINDING 251`/`D-EU-101` entries) and state the delta per district.

**Why**: this is the number the director needs to decide whether to accept the remaining exclusions as a
data-gap ceiling or ask for imputation (owner call, not this plan's).

**How to test**: N/A — this task's output is the report itself, written to this file's §8.

## 7. Stop-and-report points

1. After T01 — before touching any district's output, in case the two-line diff needs a second look.
2. After T02 finishes all four districts (or the first district whose `population_prepared` is unexpectedly
   0 or lower than its pre-fix count — that is a regression, stop immediately, do not run the remaining
   districts).
3. After T03 — final stop. Do not package or ship to Speed.

## 8. Progress log

(Executor appends one entry per completed task here, in the standard format:
`#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)
