# MEASUREMENT — the fleet's failure population (OPEN-06 · OPEN-07 · OPEN-11)

> **Slug:** `open-06-07-11_failure-population` · **Date:** 2026-08-06 · **Task:** N04 of
> `docs/docs_ACTIVE/openings/implemenation/PLAN_no-compute-queue.md`.
> **MEASUREMENT ONLY. No remediation was performed or proposed as an action.** No EnergyPlus was run,
> no simulation, no cluster, no `ssh`/`srun`/`sbatch`. Every number below is read from a file already on
> disk, or is a plain `pandas`/`geopandas` merge of two such files — no classifier execution occurred in
> this task (the one classifier-output file used, `scratchpad/t20_true_archetype.csv`, was produced by a
> **prior, already-completed** audit session on 2026-08-04; this task only reads and merges it).

---

## 0. Provenance ledger — every file read, and its git state

| File | Role | Git state |
|---|---|---|
| `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg` (12 cells) | Archetype + simulation-status source for both OPEN-06 and OPEN-11 | **Working tree = HEAD (`bca92d0`, 2026-08-05).** `git log` on every one of the 12 files shows last touch at commit **`0df422e`** ("feat: implement machine learning imputer, classification thresholds updates, and 3D viz enhancements", 2026-07-03). `git diff`/`git status` against that path show **zero uncommitted changes** — the file on disk today is byte-identical to what `0df422e` committed. |
| `openubem/semantic/building_classifier.py` | The classifier whose output is compared against the gpkg | `git log` shows the same last-touch commit, **`0df422e`** (2026-07-03). Unchanged since, including through today's HEAD. |
| `scratchpad/t20_true_archetype.csv` | Fresh `BuildingClassifier().classify()` output, one row per fleet building (8,160), produced by the AUDIT — R06 session (`docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_REMAINder.md:1142-1194`), dated 2026-08-04 | Because the classifier module has not changed since `0df422e` (predates 2026-08-04), this file's classifier outputs are still what HEAD would produce today. Re-running the classifier in this task was therefore unnecessary and was not done (§2 rule 3 of the plan permits classifier execution only in N02). |
| `openubem/outputs/comparisons/t20_layout_assign_eui.csv` | T20 cluster-harvest per-building status/severity | Present in working tree, 8,160 rows; not separately version-checked (not the archetype source — only used for `status`/`n_severe` cross-reference). |
| `C:\Users\o_iseri\AppData\Local\Temp\ubem_t20_harvest\<cell>_layout_assign\way_<id>\eplusout.err` | Raw ground truth for the 3 OPEN-07 buildings | Local cluster-fetch cache from the T20 harvest (fetched 2026-08-04 per its file mtime), outside git. This is the **only** surviving `.err` for these three buildings at T20; no `.idf` survives locally for T20 (see §3). |
| `docs/docs_REPORTS/REPORT_phaseE_final.md` §12 item 6 | Names the historical 6 inverted-geometry buildings | Working tree = HEAD; cross-checked against `docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/DONE_10_fails_solution.md` §3 (identical list). |
| `docs/docs_DONE/BUGS/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md:35` | Names the automated E-R3-3 re-run that produced 8,154/8,160 | Working tree = HEAD. |

**Important scoping note on "the archetype source is not a fixed object across time" (§5.8):** the 12
`05_results.gpkg` files were **last rewritten by the same commit (`0df422e`) that also last touched the
classifier**. Both are frozen at that commit and unchanged since. So "HEAD" for both objects in this
task means the same thing: the state fixed at `0df422e`, still current today.

---

## 1. (a) Does the mislabel originate in `05_results.gpkg` itself, or in a step that writes it?

**Recomputed the 41 directly** (not trusted from the audit's prose) by merging
`scratchpad/t20_true_archetype.csv` (classifier output, 8,160 rows, all 12 cells) against the
`archetype_id` column read live from all 12 canonical `05_results.gpkg` files:

```
classifier says      gpkg says        count
LargeHotel        →  LargeOffice        13
LargeHotel        →  MediumOffice       20
SmallHotel        →  SmallOffice         7
SmallHotel        →  MediumOffice        1
                                    ------
                                       41
```

**41/8,160 exactly** — matches the register's recorded 41 (33 `LargeHotel` + 8 `SmallHotel`) with **zero
discrepancy**. Full 41-row table: `openubem/outputs/comparisons/open06_mislabel_population.csv`.

**Spot-checked 3 of the 41 against the raw OSM `building_tag`** in the matching cell's `01_buildings.gpkg`
(the Stage-1 fixture, upstream of both the classifier and the gpkg's stored label):

| cell | osm_id | raw `building_tag` (ground truth) | classifier says | gpkg says |
|---|---|---|---|---|
| `nyc_centre` | `way/260180778` | `hotel` (name: "Hyatt Centric Times Square") | `LargeHotel` | `LargeOffice` |
| `nyc_rural` | `way/965718400` | `hotel` | `SmallHotel` | `SmallOffice` |
| `la_urban` | `way/401910463` | `motel` (name: "Wilshire Serrano Motel") | `SmallHotel` | `SmallOffice` |

All three raw tags say hotel/motel by name. The classifier is right; the gpkg is wrong.

**Verdict: SOURCE DEFECT, not a live classifier defect.** The live classifier (`0df422e`, unchanged
through today's HEAD) already produces the correct Hotel archetype for all 41 buildings when run
directly against the Stage-1 raw tags — it does **not** reproduce the gpkg's Office mislabel. Since the
same commit (`0df422e`) rewrote both the classifier thresholds *and* the `05_results.gpkg` files, yet the
two still disagree on these 41 buildings, the defect is not "stale data from before a later classifier
fix" — it sits in whatever pipeline step actually populated `05_results.gpkg`'s `archetype_id` column at
that commit (it evidently did not (re)invoke the same classifier call path the audit used). **This task
does not determine which step that is** — identifying the exact writer is further work, out of scope for
a measurement-only task; it only establishes that the *live classifier* is not the culprit.

---

## 2. (b) Are the three OPEN-07 buildings inside the 41, and what does their `.err` say?

**Yes — all three are inside the 41**, confirmed by the same merge (rows below, from
`open06_mislabel_population.csv`):

| cell | osm_id | gpkg archetype | classifier archetype | T20 `status` | T20 `n_severe` |
|---|---|---|---|---|---|
| `la_urban` | `way/401910463` | `SmallOffice` | `SmallHotel` | `failed` | 1 |
| `nyc_rural` | `way/965718402` | `SmallOffice` | `SmallHotel` | `failed` | 1 |
| `nyc_rural` | `way/965718403` | `SmallOffice` | `SmallHotel` | `failed` | 1 |

(`has_fatal` is `False` for all three, as it is fleet-wide — the dead column, not used as evidence per
plan rule 10.)

**Raw `eplusout.err` survives on local disk for all three**, at
`C:\Users\o_iseri\AppData\Local\Temp\ubem_t20_harvest\<cell>_layout_assign\way_<id>\eplusout.err`
(fetched from the T20 cluster harvest). Each file carries **exactly one** `** Severe **` line, followed
by a `** Fatal **` termination:

```
way/401910463 (la_urban):
   ** Severe  ** CalcHeatBalanceInsideSurf: The temperature of 1729615.94 C for zone="LAUNDRYROOMFLR1", ...
   **  Fatal  ** Program terminates due to preceding condition.
   Warmup Error Summary: 0 Warning; 0 Severe Errors.
   Sizing Error Summary: 28 Warning; 1 Severe Errors.

way/965718402 (nyc_rural):
   ** Severe  ** CalcHeatBalanceInsideSurf: The temperature of -11949.70 C for zone="LAUNDRYROOMFLR1", ...
   Warmup Error Summary: 0 Warning; 0 Severe Errors.
   Sizing Error Summary: 32 Warning; 1 Severe Errors.

way/965718403 (nyc_rural):
   ** Severe  ** CalcHeatBalanceInsideSurf: The temperature of -15490.64 C for zone="LAUNDRYROOMFLR1", ...
   Warmup Error Summary: 0 Warning; 0 Severe Errors.
   Sizing Error Summary: 32 Warning; 1 Severe Errors.
```

All three: divergence in zone `LAUNDRYROOMFLR1` — a hotel zone name, consistent with these being true
`SmallHotel` buildings mislabelled as `SmallOffice`. **One nuance against the hypothesis's own wording:**
each file's own Error Summary attributes the Severe to the **Sizing** phase (`0` Severe during Warmup,
`1` during Sizing) — not literally "warmup divergence" as the forwarded hypothesis phrases it, though the
underlying mechanism (a `LAUNDRYROOMFLR1` surface heat-balance runaway) is the same class of failure
previously described for this population.

Cross-check across the full 41-row population (`open06_mislabel_population.csv`): **exactly 7 rows have
`t20_status == failed`, and all 7 are `SmallHotel`→Office mismatches** (the 3 OPEN-07 regressions plus 4
pre-existing failures: `nyc_rural/way/965718400`, `la_centre/way/427942886`,
`la_urban/relation/6374725`, `la_urban/way/428846131`) — none of the 33 `LargeHotel` mismatches fail.
This exactly reproduces the register's independent claim (§4/§5.7: "All 7 of the T20 fleet's failures are
true `SmallHotel`") from a fresh recomputation, not by trusting the prose.

**Multiplier-scaling hypothesis (R02/R10 changes newly tipping the divergence): SILENT — neither
supported nor contradicted.** What would be needed to test it, and why it is not on disk:
- **No T20 `.idf` survives locally** for any of the three buildings (searched exhaustively under the
  local temp tree and the repo; only `.err`/`.sql`/`.end` were fetched by the harvest script). The
  cluster's own retained `in.idf`/`eplusout.eio` for these FAILED tasks (per E-LA-39's own note that the
  cleanup step skips failed tasks) would show the actual zone/`ZoneList` multiplier used at T20 — but
  reading it would require a cluster fetch, which this task's hard rules forbid (no `ssh`, no cluster,
  ever).
- **No T19 `.err` or `.idf` survives locally** for `way/401910463` at all — its T19 harvest-cache
  directory (`ubem_t19_harvest/la_urban_layout_assign/way_401910463/`) exists but is **empty** (0 files).
  Without a T19-side artifact there is nothing to diff the T20 multiplier against.
- **Conclusion:** the `.err` evidence on disk confirms *that* a `LAUNDRYROOMFLR1`-zone divergence occurred
  at T20 and *that* it happened during Sizing, but says nothing about *why* it newly appeared versus T19.
  Testing the mechanism would need the cluster-retained T20 `in.idf` (or `eplusout.eio`) for these three
  buildings plus a comparable T19 artifact — neither obtainable from files already on disk, and not
  fetched here per the no-cluster-access rule.

---

## 3. (c) Are OPEN-11's six inverted-geometry buildings still the same six?

**Historical six** (Group A, from `docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/
DONE_10_fails_solution.md:59-68`, cross-checked against `docs/docs_REPORTS/REPORT_phaseE_final.md` §12
item 6, line 351 — "The 5 la_rural drops + 1 la_urban Warehouse drop (`way/402215469`)"), recovered to
success on 2026-06-27 via the orient + thermal-mass fallback (T13/T06-R):

```
la_rural : way/472960972, way/472961034, way/472961088, way/472961091, way/472961171   (Warehouse ×5)
la_urban : way/402215469                                                                (Warehouse ×1)
```

**Current six**, read live from `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/
05_results.gpkg` (12 cells, git state per §0 — commit `0df422e`, unchanged since), filtering
`simulation_status != "success"`:

```
la_rural : way/472960972, way/472961034, way/472961088, way/472961091, way/472961171   (5, status=not_simulated)
la_urban : way/402215469                                                                (1, status=not_simulated)
```

**Side by side:**

| | Historical Group A (2026-06-27, hand-recovered) | Current non-success (HEAD, `0df422e`) |
|---|---|---|
| la_rural | way/472960972, way/472961034, way/472961088, way/472961091, way/472961171 | way/472960972, way/472961034, way/472961088, way/472961091, way/472961171 |
| la_urban | way/402215469 | way/402215469 |

**Identical, osm_id-for-osm_id. Confirmed: still the same six.**

Fleet-wide success count recomputed directly from the 12 canonical files: **8,154/8,160** — matches the
register's recorded figure exactly (144+617 = 761 non-success excluded... concretely: 8,160 total rows,
6 `not_simulated`, 8,154 `success`).

**What happened:** the 2026-06-27 recovery (`DONE_10_fails_solution.md`) was a **hand-run, one-off**
script (`scripts/validation/phaseE_recover_10.py`, not part of the standard automated fleet-generation
path) that patched these 6 rows directly into the canonical `05_results.*` files, reaching 8,160/8,160.
The later **E-R3-3 archetype-threshold fix** (`docs/docs_DONE/BUGS/misclassification/
PLAN_archetype_threshold_fix_E-R3-3.md:35`) then re-ran the **full automated** 8,160-building fleet
generation from scratch ("Full Phase-E 8,160-bldg re-run (E-R3-3) — FLEET COMPLETE 2026-07-02 (12/12,
**8,154/8,160**)"), and that re-run's output was promoted to the committed `phaseE` baseline on
2026-07-03 (commit `0df422e`) — overwriting the hand-patched 8,160/8,160 file with a fresh automated run
that does **not** invoke the thermal-mass fallback, so the same 6 geometry-winding buildings dropped back
to `not_simulated`. This matches the register's own account precisely and is not a new finding — this
task's contribution is confirming, by direct ID comparison rather than by trusting the prose, that the
population did not silently drift.

---

## 4. Summary table

| Question | Answer | Evidence |
|---|---|---|
| (a) Mislabel origin | **Source defect** (in `05_results.gpkg` or its writer), not a live classifier defect | §1 — 41/41 recomputed match; classifier agrees with raw OSM tags on all 3 spot-checks |
| Register's 41 vs. recomputed | **41 = 41**, no discrepancy | `open06_mislabel_population.csv` |
| (b) OPEN-07's 3 inside the 41? | **Yes, all 3** | `open06_mislabel_population.csv` rows for `way/401910463`, `way/965718402`, `way/965718403` |
| (b) `.err` survives? | **Yes, for all 3** — one `** Severe **` (`LAUNDRYROOMFLR1`, Sizing phase), one `** Fatal **` each | `ubem_t20_harvest\<cell>_layout_assign\way_<id>\eplusout.err` |
| (b) Multiplier-scaling hypothesis | **Silent** — no T20 IDF, no T19 comparison artifact survives locally | §2 |
| (c) Same six? | **Yes, identical** osm_id-for-osm_id | §3 |
| (c) Fleet success (current) | **8,154 / 8,160** | matches register exactly |

---

## 5. Artifacts

- `openubem/outputs/comparisons/open06_mislabel_population.csv` — 41 rows: `cell`, `osm_id`,
  `gpkg_05_results_archetype_id`, `classifier_archetype_id_HEAD`, `in_open07_three`, `t20_status`,
  `t20_n_severe`.
- This report.

**No files under `openubem/`, `docs/docs_VALIDATION/`, or the register were modified by this task.**
