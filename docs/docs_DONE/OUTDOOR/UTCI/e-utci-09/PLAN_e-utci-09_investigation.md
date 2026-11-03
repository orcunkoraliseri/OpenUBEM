# UTCI — E-UTCI-09 Data-Gap Investigation Plan (v1.0)

**Slug:** utci-e-utci-09-investigation · **Date:** 2026-07-24 · **Binding contract:** this plan + the
E-UTCI-09 entry in the CLOSED UTCI/Stage-6 implementation plan's own error log
(`docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md`, lines 4216-4247,
dated 2026-07-24). Executor: a fresh Sonnet session, or an autonomous director session per
`prompt/DIRECTOR_PROMPT_e-utci-09-investigation_2026-07-24.md`. Manager: audits, never writes
feature code.

## Executive Summary

The UTCI/Stage-6 arc (CLOSED, CP-5 signed 2026-07-24) found, via its T26 12-cell cluster harvest,
that 3 of 12 validated fixture cells — `nyc_suburban` (1589/1589 buildings), `nyc_rural` (198/198),
`austin_rural` (245/245) — have `height_m` NaN for **100%** of buildings, and a 4th, `austin_centre`,
at 84.5% (349/413). Stage 6 correctly excludes these buildings from its DSM and reports the exclusion
(`n_excluded_no_height`, `svf_mean`) rather than silently papering over it — the 3 fully-excluded
cells end up with `svf_mean = 1.0000`, i.e. a flat open field instead of an urban canyon. This is
logged as **E-UTCI-09**, OPEN, explicitly forwarded to a future Stage-1 (data acquisition) arc — it
is not a Stage-6/UTCI defect and does not reopen the closed arc.

**This plan is investigation-only.** It scopes and characterizes the gap, surveys candidate fix
directions, and tests whether the platform's own existing (but unwired) height-imputation
infrastructure could actually resolve it — before any fix is designed or implemented. It ends at a
single manager checkpoint (CP-INV) where findings are synthesized and candidate fix shapes are
proposed for a follow-up implementation plan. That follow-up plan is new scope, authored later, not
by this plan or its executor.

**Explicitly out of scope:**
- Implementing any fix — no edits to `openubem/acquisition/osm_fetcher.py`,
  `openubem/semantic/spatial_impute.py`, `openubem/semantic/imputation.py`, `openubem/config.py`,
  or `openubem/microclimate/domain.py` / `wind.py`.
- Re-fetching data from OSM Overpass, or calling any external DSM/LiDAR/GIS API. CLAUDE.md's rule —
  "No live-network integration tests until §5.3 is unblocked" — is still in force project-wide (§5.3
  is the Step-1 DESIGN's held-out-city live-Overpass generalisation smoke test, unrelated to this
  ticket but the reason live acquisition calls stay off-limits until that gate is explicitly
  unblocked). This plan does desk research only for candidate data sources (I02).
- Re-opening or re-litigating any part of the CLOSED UTCI plan's own §9/§10 — frozen historical
  record; cite it, do not edit it.
- Any cluster (`sbatch`) compute — this plan is entirely local, small-scale (a handful of `.gpkg`
  reads and one imputation-module smoke test), no EnergyPlus involved at all.

---

## 0. Status checklist (tick as you go)

> Executor: flip `[ ]` → `[x]` when a task's progress-log entry (§7) is written; use `[~]` for
> in-progress. The checkpoint is ticked by the **manager only**, after audit/synthesis.

- [x] **I01** — Full 12-cell characterization: confirm the gap is height/levels-field-scoped, not a
      broader footprint/inventory problem, and check whether any of the other 8 cells are borderline
- [x] **I02** — Desk-research survey of candidate external height data sources for the 4 affected
      tracts (no live fetch, no code)
- [x] **I03** — Structural test: would the platform's existing (but unwired) `spatial_impute.py`
      infrastructure actually be able to fill these cells if wired in, or does its own MNAR guard
      reject them?
- [x] **I04** — Candidate fix shapes synthesis, ranked, none adopted
- [x] 🔶 **CP-INV** — investigation checkpoint: scope confirmed, candidate fix shapes proposed
      (manager) — **investigation complete, findings synthesized, plan remains OPEN** awaiting
      manager scoping of a follow-up Stage-1 implementation plan. No fix implemented, none adopted.

---

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Never edit `main.py` at the project root. Never
   edit OVERVIEW/DESIGN docs or the CLOSED UTCI plan's own §9/§10 entries — frozen historical record;
   cite it, do not edit it.
2. **No fix implementation, no scope creep.** Do not edit `openubem/acquisition/osm_fetcher.py`,
   `openubem/semantic/spatial_impute.py`, `openubem/semantic/imputation.py`, `openubem/config.py`,
   `openubem/microclimate/domain.py`, or `openubem/microclimate/wind.py`. I03's test of
   `spatial_impute.py` is read-only/diagnostic — call the function directly from a scratch script
   against a copy of the data in memory; never wire it into `config.py`'s `IMPUTE_ENABLED_TIERS` or
   any production call site.
3. **No live network calls anywhere in this investigation.** No OSM Overpass re-fetch, no external
   DSM/LiDAR/GIS API calls, no downloading of any dataset. I02 is desk research against publicly
   documented catalog pages (`WebFetch`/`WebSearch` for reading documentation is fine — that is not
   an automated integration test) — but no task may write or run code that calls an external API.
4. **No `.py` files under `docs/`.** Diagnostic scripts go under `scratchpad/e-utci-09-investigation/`
   (session-local). Any comparison tables/plots produced go to `openubem/outputs/` (flat) **and**
   `docs_DONE/OUTDOOR/UTCI/e-utci-09/figures/`.
5. **No cluster compute of any kind for this plan.** Everything is local: reading existing `.gpkg`
   fixtures and exercising one Python module directly.
6. **Default to no comments** in any diagnostic script. One short line max when the WHY is genuinely
   non-obvious.
7. **Git handled externally** — never commit, never offer to.
8. **For any NaN%/row-count/column-presence claim, quote the actual `geopandas`/pandas output** — do
   not paraphrase or assume from the T26 harvest CSV alone; re-derive it directly from the source
   `.gpkg` for every cell this plan touches.
9. **This plan does not close.** It ends OPEN at CP-INV, handed back to the manager (a
   human-available session) for scoping a follow-up Stage-1 implementation plan. Do not mark §0 items
   "done" in the sense of "fixed" — only in the sense of "investigated, findings recorded."

## 2. File layout to create

```
docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/
├── PLAN_e-utci-09_investigation.md   (this file)
└── figures/                          (I01/I02/I03 tables or plots, if produced)
```

No new files under `openubem/` or `tests/` — this plan writes no production code or unit tests.
Diagnostic scripts live under `scratchpad/e-utci-09-investigation/` and are not required to survive
past this plan's own completion report (their outputs/findings are what matters, captured in §7).

## 3. Dependency decisions (pre-decided, do not re-debate)

1. **I01 runs first** — it either confirms the "narrow height/levels-field gap" framing this plan is
   built on, or surfaces something broader that I02-I04 need to account for.
2. **I02 and I03 are independent of each other** and may run in either order (or in parallel across
   two employees) once I01 is done.
3. **I04 depends on I01, I02, and I03 all being complete** — it is a synthesis task, not a new
   investigation.
4. **Fixture source, all 12 cells:**
   `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` — the same
   files T26's harvest read. **Read-only. Never overwrite.** The 12 cell names are listed in
   `openubem/outputs/comparisons/t26_utci_cluster_cell_summary.csv` (`cell` column) if the executor
   needs the exact list.
5. **I03 uses the real fixture GeoDataFrames directly** (loaded in memory, never written back to
   `docs_VALIDATION/`) — do not fabricate synthetic height data for this test. The point is to
   observe `spatial_impute.py`'s actual behaviour on the actual data, not a synthetic stand-in.

## 4. Source-of-truth verified facts (manager-delegated research, cited — I01 re-confirms at fleet
scale)

- **F-01 — where `height_m` originates.** `openubem/acquisition/osm_fetcher.py::ingest_buildings`
  (line 26) fetches OSM building footprints via Overpass; `_flatten_tags` (line 191) maps the raw OSM
  `height` tag into `height_m` via `_parse_height_to_m` (line 142). **If the `height` tag column is
  absent from the fetched tag set entirely, `height_m` is set to `float("nan")` for every row**
  (line 234). There is no DSM/LiDAR fallback and no `levels`×3.5m derivation into `height_m` at
  ingestion — it is a direct, unconditional pass-through of the raw OSM tag only.
- **F-02 — provenance is correctly wired.** `_assign_provenance` (line 439) tags `OSM_MISSING` when
  `height_m` is NaN (446-453); `_build_quality_flag` (line 489) appends `no_height` to
  `data_quality_flag` (line 497) — confirmed present and matching the NaN% in the fixture data
  (§ below). Stage 1 is not silently dropping the flag; it is Stage 6 that is the first stage to act
  on it as a hard exclusion.
- **F-03 — downstream `levels` fallbacks exist but never fill `height_m` itself.**
  `openubem/semantic/building_classifier.py::_impute_levels` (123-142) derives `levels` from
  `height_m` when present, else defaults to a group-median or flat 1 storey
  (`LEVELS_DEFAULT_LOW`, line 142). `openubem/geometry/footprint.py::derive_num_floors` (58-63) does
  the same for IDF zone generation. Neither ever writes a value back into `height_m` — this is why
  IDF generation is unaffected by the gap (F-06) while Stage 6 is not.
- **F-04 — the generic imputation infra references `height_m` but is never invoked for it.**
  `openubem/semantic/imputation.py::impute_column` (line 16) auto-selects a PDE method when a column
  is 100% missing (`nan_mask.all()`, lines 58-64); `openubem/config.py:105` lists
  `IMPUTE_ML_METHOD_BY_TARGET["height_m"] = "missforest"`. But the only wired call sites
  (`draw_methods.py:121`, `construction_sets.py:319-329`) impute envelope U-values and load
  parameters — never `height_m`.
- **F-05 — `spatial_impute.py` is built but unwired for `height_m`, and has an MNAR guard.**
  Its docstring (lines 4-5) lists `height_m` as an intended target; it has a missing-not-at-random
  guard at **60% local-neighbourhood missingness** (line 40). It is never instantiated for this
  column anywhere in the pipeline today. **I03 exists to determine, mechanically, what this guard
  actually does when local missingness is 100% (as in 3 of the 4 affected cells) — do not assume
  going in that "wire up the existing imputer" is a viable fix; it may just reject the input.**
- **F-06 — Stage 6 is the only hard-exclusion point in the whole pipeline.**
  `openubem/microclimate/domain.py:108-111` and `openubem/microclimate/wind.py:152-154` are the only
  two places with a hard `.notna()` filter-and-drop on `height_m`. Everywhere else the gap is
  invisible, masked by the floor-count-default-1 fallback (F-03).
- **F-07 — identical acquisition code path for all 12 cells; no cell-specific logic.**
  `scripts/validation/v12_cell_pipeline.py::step1_fetch` (137-150) calls
  `osm_fetcher.ingest_buildings(location=(lat,lon), radius_m=radius_m)` identically for all 12 cells
  (`CELL_CONFIGS`, 45-106) — same code, different coordinates only. The differential coverage is a
  function of live OSM community-tagging density at each queried location, not a code defect.
- **F-08 — spot-check across 5 cells (manager-delegated `geopandas` read, 2026-07-24), narrow-gap
  framing supported:**

  | cell | rows | `height_m` NaN | `levels` NaN | footprint area m² (min/mean/max) | invalid geoms |
  |---|---|---|---|---|---|
  | nyc_suburban | 1589 | 100.0% | 100.0% | 20.5 / 114.6 / 5132.6 | 0 |
  | nyc_rural | 198 | 100.0% | 100.0% | 21.9 / 243.9 / 3884.8 | 0 |
  | austin_rural | 245 | 100.0% | 99.6% | 34.9 / 631.5 / 10992.6 | 0 |
  | austin_centre | 413 | 84.5% | 71.4% | 24.3 / 1013.0 / 8225.3 | 0 |
  | nyc_centre | 738 | 16.4% | 81.6% | 21.3 / 1143.4 / 155536.0 | 0 |

  All 5 have plausible row counts, 100% valid Polygon geometries, sane footprint-area ranges, and a
  sensible `building_tag` mix — this looks like a narrow height/levels-field gap, not a broader
  area-coverage failure. **I01 re-derives this independently and extends it to all 12 cells** — this
  table is a starting point, not a substitute for that.
- **F-09 — hard constraint, still in force.** CLAUDE.md: "No live-network integration tests until
  §5.3 is unblocked." §5.3
  (`docs/docs_main/docs_step1/DESIGN_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar.md`,
  lines 257-262) is Step-1's held-out-city live-Overpass generalisation smoke test (Seattle/Atlanta/
  Anchorage, tagged-releases only) — unrelated to E-UTCI-09 but the reason live acquisition calls
  stay off-limits project-wide until that gate is explicitly unblocked. See §1.3.

## 5. Task list

#### I01 — Full 12-cell characterization
- **What to do:** For all 12 T26 cluster cells, independently read `01_buildings.gpkg` and report:
  row count, `height_m` NaN count/%, `levels` NaN count/%, `data_quality_flag` value distribution,
  footprint-area min/mean/max, geometry validity count, and a quick `building_tag`/`osm_tags`
  sanity check. Confirm the F-08 numbers for the 5 cells already spot-checked, and produce the same
  for the remaining 7.
- **Why:** F-08 is a 5-cell spot-check; the plan's framing ("narrow height/levels-field gap, not a
  broader footprint problem") needs fleet-wide confirmation before I02-I04 build on it. Also checks
  for any borderline cells between the "good" (1-27%) and "bad" (84.5-100%) groups that the T26
  harvest's own columns didn't flag as `zero_building_massing`.
- **How:** `geopandas.read_file` on each of the 12 `docs/docs_VALIDATION/validations/overAll/results/
  phaseE/<cell>/01_buildings.gpkg` files (cell names from
  `openubem/outputs/comparisons/t26_utci_cluster_cell_summary.csv`). Read-only.
- **How to test:** A 12-row table (cell, all the stats above) in the §7 entry and
  `docs_DONE/OUTDOOR/UTCI/e-utci-09/figures/`. State plainly whether the gap stays cleanly bimodal (a
  "good" cluster and a "bad" cluster) or whether a borderline case exists.

#### I02 — Candidate external height data source survey
- **What to do:** Desk-research (no live fetch, no code) which open, license-compatible height/LiDAR/
  DSM datasets exist that could plug the gap for the 4 affected tracts: NYC-suburban, NYC-rural,
  Austin-rural, Austin-centre. Candidates to check at minimum: USGS 3DEP (national LiDAR coverage),
  NYC Open Data (building footprints with height fields), Austin's open GIS portal, Microsoft/Global
  ML Building Footprints height estimates. For each candidate found, report: coverage of the specific
  tracts, spatial resolution, license, and a rough integration-effort estimate (new ingestion module
  vs. one-off enrichment script vs. not feasible).
- **Why:** The disposition in E-UTCI-09 (plan §10) explicitly asks whether "a targeted re-fetch or an
  imputation fallback... is warranted" — this survey is what makes that a real decision instead of a
  guess.
- **How:** `WebFetch`/`WebSearch` against public documentation/catalog pages only — reading, not
  calling any data API or downloading any dataset (§1.3).
- **How to test:** A findings table in §7 (dataset, coverage, resolution, license, effort estimate)
  covering at least the 4 candidates named above. If a candidate cannot be assessed without an
  account/paid access, say so rather than guessing.

#### I03 — Structural test of the existing imputation infrastructure
- **What to do:** Write a scratch script that loads the real `01_buildings.gpkg` for `nyc_suburban`,
  `nyc_rural`, `austin_rural` (100% local `height_m` missingness) and `austin_centre` (84.5%), and
  calls `openubem/semantic/spatial_impute.py`'s imputer directly (read-only diagnostic call, not
  wired into `config.py` or any production path) to observe its actual behaviour: does the MNAR guard
  (F-05, 60% local-neighbourhood-missingness threshold) reject these cells outright, silently produce
  a low-confidence/flagged result, or something else? Also check the generic
  `semantic/imputation.py::impute_column` PDE path (F-04) the same way, for comparison.
- **Why:** The disposition text names "an imputation fallback (parallel to the platform's existing
  height-imputation logic)" as a candidate fix — but F-05 shows that logic has a guard specifically
  designed to reject exactly this scenario (near-total local missingness). This task determines
  whether that candidate fix direction is structurally viable at all, or whether it needs the guard
  threshold itself reconsidered, before a future plan spends implementation effort on it.
- **How:** Scratch script under `scratchpad/e-utci-09-investigation/`, importing the modules directly
  (no changes to them), run against copies of the real GeoDataFrames loaded in memory.
- **How to test:** For each of the 4 cells, report: did the imputer accept, partially accept, or
  reject the column? Quote the actual guard condition/return value observed, not a paraphrase. State
  plainly whether "wire up the existing imputer" is or is not a structurally viable fix path as-is.

#### I04 — Candidate fix shapes synthesis
- **What to do:** Drawing on I01-I03, enumerate and rank candidate fix directions for a future
  Stage-1 implementation plan: e.g. (a) targeted OSM re-fetch once §5.3 is unblocked or a scoped
  one-off exception is granted, (b) ingest one of I02's external datasets for the specific affected
  tracts, (c) a regional/cell-level statistical fallback (e.g. borrow the median height from the
  nearest "good" cell of the same zone-type, explicitly flagged low-confidence), (d) widen
  `spatial_impute.py`'s search radius beyond the cell boundary so cells with 100% *local* missingness
  can still draw on cross-cell neighbours, (e) accept and permanently document the gap as a known
  Stage-6 limitation for these specific tracts. For each: rough effort, risk, and whether it fixes
  the gap for Stage 6 only or for the whole platform.
- **Why:** This is the deliverable the follow-up implementation plan's own §3 dependency decisions
  will draw on — mirrors how the LayoutAssigner E-LA-20 investigation's I05 pre-vetted candidates for
  its own follow-up plan.
- **How:** Synthesis only — no new code, no new data pulls. Cite I01/I02/I03 findings directly.
- **How to test:** A ranked table in §7 (option, effort, risk, scope). Explicitly flag which option(s)
  look most promising and why — but do not recommend adopting one; that decision belongs to whoever
  scopes the follow-up plan.

## 6. Stop-and-report points

1. **After I01** — if the full 12-cell characterization finds the gap is *not* cleanly scoped to the
   height/levels fields (e.g. another column is also broadly missing in a way suggesting a wider
   fetch failure, or a "good" cell turns out borderline), report this clearly before continuing to
   I02-I04 — it changes what "candidate fix shapes" in I04 should even cover. This is a notable-finding
   checkpoint, not a hard stop; continue unless the finding is severe enough to warrant a manager
   decision first.
2. **After CP-INV** (final) — synthesis complete, handed back to the manager.

## 7. Progress log

#### I01 — Full 12-cell characterization — completed 2026-07-25
- Artifacts:
  - `scratchpad/e-utci-09-investigation/i01_characterize_12cells.py` (diagnostic script, read-only
    `geopandas.read_file` on all 12 fixtures, no writes to `docs_VALIDATION/`)
  - `openubem/outputs/comparisons/i01_e_utci_09_12cell_characterization.csv` (12-row characterization
    table, all stats + per-column NaN% as JSON)
  - `docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/figures/i01_12cell_characterization.md` (markdown table +
    narrative findings)
- Deviations: none.
- Test status: ran `.venv/Scripts/python.exe scratchpad/e-utci-09-investigation/i01_characterize_12cells.py`
  against all 12 `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`
  files. Literal output excerpts (full output covers all 12 cells and is also in the CSV/markdown):
  ```
  === nyc_suburban ===
  rows=1589 crs=EPSG:32618
  height_m NaN: 1589/1589 = 100.0000%
  levels NaN: 1589/1589 = 100.0000%
  footprint area (m2, EPSG:32618 (already metric, no reprojection)): min=20.52 mean=114.64 max=5132.61
  geometry: null=0 empty=0 invalid=0 non_polygon=0
  building_tag: n_distinct=3 empty=0 top5=house:979; yes:320; garage:290

  === austin_centre ===
  rows=413 crs=EPSG:32614
  height_m NaN: 349/413 = 84.5036%
  levels NaN: 295/413 = 71.4286%
  footprint area (m2, EPSG:32614 (already metric, no reprojection)): min=24.28 mean=1013.05 max=8225.32
  geometry: null=0 empty=0 invalid=0 non_polygon=0

  === Cross-check vs T26 CSV (n_excluded_no_height / pct_excluded_no_height) ===
  nyc_centre: independent height_nan=121 (16.3960%) vs T26 n_excluded_no_height=121 (16.3957%) -> disc_n=0 disc_pct=0.0003
  austin_centre: independent height_nan=349 (84.5040%) vs T26 n_excluded_no_height=349 (84.5036%) -> disc_n=0 disc_pct=0.0004
  ```
  All 12 cells: `disc_n=0` for every cell (exact row-count match); `disc_pct` within ±0.0005 pp
  (floating-point display rounding only). Geometry validity check (`.isna()`, `.is_empty`,
  `.is_valid`, `.geom_type`) returned **0 null / 0 empty / 0 invalid / 0 non-Polygon across all
  12,809 rows in all 12 cells** — quoted literally above for the two extremes, identical `0/0/0/0`
  pattern held for the remaining 10 cells (see script stdout / CSV `geom_*` columns).
- Notes (auditor-relevant):
  - **F-08 5-cell spot-check reproduced exactly** (nyc_suburban, nyc_rural, austin_rural,
    austin_centre, nyc_centre) — row counts, `height_m`/`levels` NaN%, footprint area min/mean/max,
    and 0 invalid geoms all match F-08's table to stated precision. No discrepancy found.
  - **Full 12-row table** (sorted by `height_m` NaN% ascending):

    | cell | rows | height_m NaN % | levels NaN % | footprint area m² min/mean/max | invalid/non-poly/empty/null geoms |
    |---|---|---|---|---|---|
    | la_rural | 149 | 0.671 | 97.987 | 28.31/509.08/22443.66 | 0/0/0/0 |
    | la_suburban | 1343 | 1.117 | 99.553 | 20.08/194.98/6869.20 | 0/0/0/0 |
    | nyc_urban | 1779 | 2.248 | 99.044 | 20.39/176.77/11077.47 | 0/0/0/0 |
    | la_urban | 618 | 6.796 | 94.984 | 23.37/773.03/10330.11 | 0/0/0/0 |
    | austin_urban | 425 | 11.059 | 99.059 | 20.87/572.04/22109.98 | 0/0/0/0 |
    | nyc_centre | 738 | 16.396 | 81.572 | 21.28/1143.41/155536.02 | 0/0/0/0 |
    | la_centre | 226 | 19.912 | 65.044 | 20.05/1833.95/17661.13 | 0/0/0/0 |
    | austin_suburban | 437 | 26.087 | 89.474 | 20.07/273.84/6972.27 | 0/0/0/0 |
    | *(58 pp gap — no cell in 26–84%)* | | | | | |
    | austin_centre | 413 | 84.504 | 71.429 | 24.28/1013.05/8225.32 | 0/0/0/0 |
    | nyc_suburban | 1589 | 100.000 | 100.000 | 20.52/114.64/5132.61 | 0/0/0/0 |
    | nyc_rural | 198 | 100.000 | 100.000 | 21.87/243.86/3884.80 | 0/0/0/0 |
    | austin_rural | 245 | 100.000 | 99.592 | 34.89/631.49/10992.63 | 0/0/0/0 |

  - **Load-bearing answer:** the gap **is** cleanly scoped to `height_m`/`levels` — not a broader
    footprint/inventory failure. Row counts, geometry validity (0 invalid/empty/null/non-Polygon in
    all 12,809 rows), footprint-area ranges, and `building_tag` presence/distribution are healthy in
    every cell including the 4 affected ones. Other broadly-sparse columns (`year_built`, `postcode`,
    `roof_height_m`, plus empty-string-sentinel `function_tag`/`roof_shape`, which use `""` not `NaN`
    so `.isna()` alone would misreport them as 0%) are sparse **uniformly across both clusters**,
    uncorrelated with the height/levels split — normal OSM per-field tagging density, not a
    differential defect.
  - **Distribution is cleanly bimodal, no borderline cell.** Sorted `height_m` NaN%: 0.67, 1.12,
    2.25, 6.80, 11.06, 16.40, 19.91, 26.09 (8 "good" cells), then a 58-percentage-point gap, then
    84.50, 100.00, 100.00, 100.00 (4 "bad" cells). `austin_centre` at 84.50% is the nearest thing to
    borderline but sits far closer to the bad cluster than the good one — no cell occupies the
    26–84% range.

#### I02 — Candidate external height data source survey — completed 2026-07-25
- Artifacts:
  - `docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/figures/i02_height_data_source_survey.md` (findings table +
    per-candidate notes + full documentation-read citation list)
- Deviations: §7 entry written by the director rather than the employee — same concurrency ruling as
  I03 (I02/I03 dispatched in parallel per §3.2; concurrent appends to one file would race). No
  content change.
- Test status: desk research, so "test status" = the documentation pages actually fetched/read:
  - `https://registry.opendata.aws/usgs-lidar/` (full fetch)
  - `https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md` (full fetch)
  - `https://tnris.org/stratmap/elevation-lidar` (full fetch)
  - `https://github.com/microsoft/GlobalMLBuildingFootprints/blob/main/README.md` (full fetch)
  - Search-result-level reads (title/summary, not full-page fetch): USGS 3DEP FAQ/status-map pages;
    NYS Building Footprints (`data.gis.ny.gov`); NYS statewide 1 m DEM (`gis.ny.gov`); City of Austin
    Building Footprints 2013 (`data.austintexas.gov`); GHS-BUILT-H
    (`human-settlement.emergency.copernicus.eu`); Copernicus DEM GLO-30 (`dataspace.copernicus.eu`,
    `opentopography.org`, Sentinel-Hub license PDF); Google Open Buildings 2.5D Temporal
    (`sites.research.google`, `research.google/blog`).
  - No dataset downloaded, no API called, no code written — plan §1.3 satisfied.
- **Manager verification (director session, 2026-07-25):** re-read `CELL_CONFIGS` in
  `scripts/validation/v12_cell_pipeline.py` (lines 45-106) directly; the 4 coordinate pairs the
  employee assessed match exactly:
  ```
  nyc_suburban  lat 40.7052, lon -73.5985, radius_m 500.0   (EPSG 32618)
  nyc_rural     lat 42.0396, lon -74.1143, radius_m 1000.0  (EPSG 32618)
  austin_centre lat 30.2672, lon -97.7431, radius_m 500.0   (EPSG 32614)
  austin_rural  lat 30.5788, lon -98.2700, radius_m 1000.0  (EPSG 32614)
  ```
  The geographic claim also checks out: NYC's eastern boundary (Queens/Nassau) sits near lon -73.70,
  so `nyc_suburban` at -73.5985 is east of it, on Long Island — outside the five boroughs. Audit
  §5.6 satisfied: no code calling an external API was written; the evidence trail is `WebFetch`/
  `WebSearch` documentation reads only, which §1.3 explicitly permits.
- Notes: **Load-bearing geographic finding not anticipated in the plan text.** `nyc_suburban`
  (40.7052, -73.5985) and `nyc_rural` (42.0396, -74.1143) are geographically **outside New York
  City's five boroughs** — Long Island and the Catskills respectively — despite the `nyc_*` cell
  naming. Any NYC-municipal-portal candidate therefore cannot cover them regardless of its data
  quality; only boundary-independent sources (Microsoft Global ML Building Footprints, GHS-BUILT-H,
  USGS 3DEP, NYS-statewide) are even in play for those two tracts. Strongest single candidate across
  all 4 tracts: **Microsoft Global ML Building Footprints** (CDLA Permissive 2.0, nationwide, bulk
  download, one-off-enrichment-script effort). **USGS 3DEP / TNRIS StratMap** are viable but
  higher-effort (new point-cloud -> DSM -> DTM-difference -> footprint-join ingestion module).
  **GHS-BUILT-H** (100 m grid, neighbourhood-average height) fits I04's "regional fallback" option,
  not a per-building fix. Unresolved from documentation alone, flagged open: NYS Building Footprints'
  height-field completeness outside the NYC portion; USGS 3DEP/TNRIS exact per-tract vintage/QL.
  ALOS World 3D could not be assessed (JAXA account-gated — stated plainly, not guessed). Google Open
  Buildings 2.5D Temporal confirmed **not** applicable (excludes the USA entirely).

#### I03 — Structural test of the existing imputation infrastructure — completed 2026-07-25
- Artifacts:
  - `scratchpad/e-utci-09-investigation/i03_spatial_impute_structural_test.py` (diagnostic script,
    read-only `geopandas.read_file` on the 4 affected fixtures, direct import of
    `knn_fill`/`impute_column`, no production wiring, no edits to `spatial_impute.py` /
    `imputation.py` / `config.py`)
  - `openubem/outputs/comparisons/i03_knn_fill_default_radius.csv`
  - `openubem/outputs/comparisons/i03_knn_fill_radius_probe.csv`
  - `openubem/outputs/comparisons/i03_impute_column_comparison.csv`
  - `docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/figures/i03_spatial_impute_structural_test.md` (results table +
    plain-language verdict)
- Deviations: §7 entry written by the director rather than the employee — deliberate ruling, not an
  employee failure: I02 and I03 were dispatched concurrently per §3.2, and two employees appending to
  the same file would race. Both were instructed to return their entry text to the director instead.
  No content change.
- Test status: ran `.venv/Scripts/python.exe scratchpad/e-utci-09-investigation/i03_spatial_impute_structural_test.py`
  against the 4 real `01_buildings.gpkg` fixtures. Literal output (`knn_fill`, production defaults
  `k=10`, `radius=100.0`, `mnar_threshold=0.60`):
  ```
  [nyc_suburban] n_missing=1589 n_filled=0 n_mnar_blocked=1589 n_silent_no_donor=0 confidence_dist={}
  [nyc_rural] n_missing=198 n_filled=0 n_mnar_blocked=192 n_silent_no_donor=6 confidence_dist={}
  [austin_rural] n_missing=245 n_filled=0 n_mnar_blocked=232 n_silent_no_donor=13 confidence_dist={}
  [austin_centre] n_missing=349 n_filled=15 n_mnar_blocked=334 n_silent_no_donor=0
    confidence_dist={'MEDIUM': 7, 'LOW': 5, 'HIGH': 3}
  ```
  Radius probe (250/500/1000 m): `n_filled` stays **0** for the 3 fully-NaN cells at every radius
  (silent-no-donor rows merely convert to MNAR-blocked); `austin_centre` reaches `n_filled=21/20/20`
  with confidence collapsing to all-`LOW` at radius >= 250 m (vs. a HIGH/MEDIUM/LOW mix at 100 m).
  `impute_column(method="auto")` comparison arm: raised
  `ValueError("impute_column: bounds must be provided for PDE imputation on column 'height_m'.")`
  verbatim for the 3 100%-missing cells (PDE branch, F-04); for `austin_centre` (84.5%, not all-NaN)
  it resolved to KDE and filled all 349 rows from the 64 observed values, no exception. All 4 cells:
  CRS already projected metric (EPSG:32618 / EPSG:32614), no reprojection needed. Accounting
  assertion `filled + blocked + silent == missing` held in all 16 `knn_fill` runs (4 cells x 4 radii).
- **Manager re-derivation (independent, director session, 2026-07-25):** re-imported the real
  `knn_fill` and re-ran it against `nyc_rural`, `austin_rural`, `austin_centre` in a separate process.
  Literal output:
  ```
  module defaults: k=10 radius=100.0 mnar=0.6
  nyc_rural     crs=EPSG:32618 rows=198 missing=198 filled=0  blocked=192 silent=6  conf={}
  austin_rural  crs=EPSG:32614 rows=245 missing=245 filled=0  blocked=232 silent=13 conf={}
  austin_centre crs=EPSG:32614 rows=413 missing=349 filled=15 blocked=334 silent=0
                conf={'MEDIUM': 7, 'LOW': 5, 'HIGH': 3}
  ```
  Exact match with the employee's figures on every field, including the silent-no-donor counts.
- Notes: the MNAR guard structurally rejects all 3 fully-NaN cells at every tested radius up to
  1000 m — **not a guard bug**: those local neighbourhoods genuinely carry zero `height_m` signal, so
  the guard is behaving exactly as designed (F-05). Widening the radius alone cannot fix this without
  crossing cell boundaries, which makes candidate fix shape (d) *necessary* rather than merely one
  option for those 3 cells. Side-finding, quantified, **not fixed** (hard rule 2): rows with zero
  neighbours within the radius are silently neither filled nor MNAR-flagged
  (`_query_neighbours` empty -> `continue` skips `blocked_mask[i]`, `spatial_impute.py` lines
  218-220) — 6 rows in `nyc_rural`, 13 in `austin_rural` at radius=100 m. This is a diagnostics blind
  spot in `spatial_impute.py`, logged as **E-UTCI-10** in §8. `austin_centre` is partially fillable
  today via `knn_fill` (15/349 at defaults) and fully fillable via `impute_column`'s non-spatial KDE
  path (349/349), but that KDE fill carries no spatial reasoning and no MNAR awareness.

#### I04 — Candidate fix shapes synthesis — completed 2026-07-25
- Artifacts: `docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/figures/i04_candidate_fix_shapes.md` (ranked table, 6
  options — the plan's 5 named shapes (a)-(e) plus one added shape (f) warranted by I03's evidence,
  each with effort/risk/scope/supporting-evidence/verdict, plus per-option prose, a
  prerequisites/combinations section, and a one-fix-vs-split-strategy section)
- Deviations: (1) added one option beyond the plan's named five — **(f)** "wire `impute_column`'s
  existing KDE path for `austin_centre`-class partially-missing cells" — justified by I03's own
  finding that this path already fills 349/349 rows today with zero structural change, which is
  qualitatively distinct from (c)/(d) and specific to the one non-100%-missing cell; §5 I04's own
  text explicitly invites "any further shape the I01-I03 evidence genuinely warrants."
  **Director ruling: accepted** — within the task's stated latitude, evidence-backed, and it does not
  adopt anything. (2) §7 entry written by the director, same concurrency ruling as I02/I03.
- Test status: no code run, no data pulled (synthesis-only, §1 rules 1-3). Read in full:
  `PLAN_e-utci-09_investigation.md` (§1, §4 F-01..F-09, §5 I04, §7 I01/I02/I03 entries),
  `figures/i01_12cell_characterization.md`, `figures/i02_height_data_source_survey.md`,
  `figures/i03_spatial_impute_structural_test.md`. Ranking derived (most to least promising):
  **(b)** Microsoft Global ML Building Footprints > **(f)** `impute_column` KDE for
  `austin_centre`-class > **(d)** structural cross-cell donor pooling > **(c)** zone-type median
  borrow > **(a)** targeted OSM re-fetch > **(e)** accept-and-document. Verdict: split strategy
  warranted (`austin_centre` differs structurally from the 3 fully-NaN cells per I03); every row
  explicitly marked **candidate, not adopted**.
- Notes: **(d)** as literally named ("widen search radius") is **inert** per I03 for the 3 fully-NaN
  cells and only becomes meaningful as a structural cross-cell-boundary change — ranked accordingly,
  on what it would actually take rather than on its surface simplicity. **(c)** and **(d)** converge
  in spirit (manual scalar-level vs. spatial-index-level donor borrowing) and share the same
  cross-city fabric-mismatch risk, evidenced via I01's per-cell `building_tag`/footprint-area
  profiles. Prerequisite structure: (d) is a *precondition*, not an alternative, to the existing
  imputer ever working on the 3 fully-NaN cells; (a) and (b) are mutually reinforcing rather than
  competing; (f) is fully independent; (e) is compatible with everything and is the natural interim
  floor. No conflict found between the evidence base and the plan.

#### CP-INV — investigation synthesis — completed 2026-07-25
- **Scope:** I01-I04. All four tasks executed, audited, and independently spot-re-derived by the
  director (see the per-task "Manager re-derivation / verification" lines above). Audit checklist
  from the director prompt §5 satisfied: one conformant §7 entry per task; every NaN%/row-count/
  behaviour claim backed by quoted executed output; `git status` shows **no** diff to
  `openubem/acquisition/*.py`, `openubem/semantic/*.py`, `openubem/config.py` or
  `openubem/microclimate/*.py` attributable to this investigation; §0 ticks match §7 entries; I03
  confirmed to have really invoked `spatial_impute.py` against real data (director re-ran it in a
  separate process, exact match); I02 confirmed to be documentation reads only, no API-calling code.
- **Finding (stated plainly):** E-UTCI-09 is a **narrow, upstream, field-level data gap, not a
  pipeline defect and not a broader acquisition failure.** Across all 12 cells and 12,809 buildings,
  row counts, geometry validity (0 invalid / 0 empty / 0 non-Polygon everywhere), footprint-area
  ranges and `building_tag` distributions are healthy; only `height_m`/`levels` are affected, and the
  affected/unaffected split is cleanly bimodal (8 cells at 0.67-26.09%, a 58-percentage-point gap,
  then 4 cells at 84.50-100.00%) with no borderline case. The cause is differential live OSM
  community-tagging density at the queried coordinates (F-07: identical code path for all 12 cells),
  propagated unchanged by `_flatten_tags`' unconditional `height_m = NaN` when the `height` tag is
  absent (F-01), and first acted upon — correctly and visibly — at Stage 6's `.notna()` exclusion
  (F-06). **Critically, the platform's existing height-imputation infrastructure cannot resolve it:**
  `knn_fill` fills exactly 0 rows in the 3 fully-affected cells at every radius from 100 m to
  1000 m, because every candidate donor is itself missing `height_m` by construction. That is the
  MNAR guard working as designed, not failing. Two findings extend the plan's original framing:
  `nyc_suburban` and `nyc_rural` are geographically **outside New York City** (Long Island and the
  Catskills), foreclosing NYC-municipal data sources for them; and `austin_centre` is structurally
  **unlike** the other three (84.5% not 100%, 64 real observed values, already partially fillable
  today), which argues for a split rather than a single uniform fix.
- **Candidate fix shapes (from I04, ranked, NONE ADOPTED):** (b) ingest Microsoft Global ML Building
  Footprints for the 4 tracts — medium effort, whole-platform scope, only boundary-independent
  option; (f) wire `impute_column`'s existing KDE path for `austin_centre`-class partially-missing
  cells — low effort, works today, Stage-6 scope only; (d) structural cross-cell donor pooling in
  `spatial_impute.py` — high effort, and a *precondition* rather than an alternative for the 3
  fully-NaN cells; (c) zone-type median borrow — low effort, high fabric-mismatch risk; (a) targeted
  OSM re-fetch — gated by F-09/§5.3 and may not change anything per F-07; (e) accept and permanently
  document — near-zero effort, standing quality cost. Strongest evidenced combination: (b) attempted
  for all 4 tracts + (f) for `austin_centre` + (e) documenting whatever residual survives.
- **Open questions (could not be resolved within this plan's local-only, no-download scope):**
  (1) the actual density of Microsoft Global ML Building Footprints' height sub-attribute inside
  these 4 specific bounding boxes — this is the single decisive fact for ranking option (b), and it
  must be **counted, not read**, so it requires a data download that §1.3 forbids;
  (2) USGS 3DEP / TNRIS StratMap exact vintage and quality level at the 4 coordinate pairs;
  (3) NYS Building Footprints' height-field completeness outside the NYC portion;
  (4) ALOS World 3D — unassessable, JAXA account-gated. Also newly opened: **E-UTCI-10** (§8), a
  diagnostics blind spot in `spatial_impute.py`, found by I03 and deliberately left unfixed.
- **Status: OPEN.** Investigation complete, findings synthesized, awaiting manager scoping of a
  follow-up Stage-1 implementation plan. **No fix has been implemented and none is adopted.**

## 8. Error log

#### E-UTCI-10 — `spatial_impute.py` silently skips zero-neighbour rows without MNAR-flagging them — OPEN — 2026-07-25

**Symptom.** In `knn_fill` (and identically in `neighbour_vote`), a row whose neighbourhood query
returns no neighbours within `radius` is left unfilled **and** unflagged: it appears in neither the
filled set nor the `SPATIAL_CLUSTER_MNAR_BLOCKED` set, so `data_quality_flag` carries no record that
spatial fill was attempted and could not proceed. Observed at production defaults on real data
(I03): 6 rows in `nyc_rural`, 13 rows in `austin_rural`.

**Root cause.** `openubem/semantic/spatial_impute.py` lines 218-220 (`knn_fill`) and 141-143
(`neighbour_vote`): `if len(nbr_idx) == 0: continue` returns to the loop head without setting
`blocked_mask[i]`, so `provenance.append_flag` never marks the row. The MNAR guard at line 224 is
only reached when at least one neighbour exists.

**Fix.** None applied — this investigation plan is investigation-only (§1 rule 2) and
`spatial_impute.py` is on its do-not-edit list.

**Verification.** Quantified by two independent executions (employee + director re-derivation) —
see the I03 §7 entry.

**Disposition.** OPEN, forwarded. Low severity: it is a **diagnostics/observability** gap, not a
correctness gap — no wrong value is produced, and today no production call site imputes `height_m`
at all (F-04/F-05), so nothing downstream currently consumes the missing flag. It should be picked
up by whichever future arc wires spatial imputation into a production path, since at that point an
unflagged skip becomes an untraceable silent no-op. Not a blocker for E-UTCI-09.

_(numbering continues from the UTCI plan; if this investigation surfaces a genuinely
new, distinct defect beyond E-UTCI-09 itself, it starts at **E-UTCI-10**. E-UTCI-09 itself stays
logged in the UTCI plan's own §10 — this plan's job is to advance its `Fix`/`Disposition` fields via
findings recorded here, not to duplicate its entry.)_
