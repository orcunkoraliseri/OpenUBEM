# MEASUREMENT — Re-check the four June-audit remnants against HEAD (N03 · OPEN-24, 25, 26, 27)

> **Task:** N03 of `docs/docs_ACTIVE/openings/implemenation/PLAN_no-compute-queue.md`.
> **Method:** the audit doc (`docs/docs_INVESTIGATE/INVESTIGATION_steps-1-3-audit.md`, dated 2026-06-09)
> is the hypothesis. Every verdict below is checked against HEAD code, cited by `path:line`.
> **Remediation performed: none.** No file outside this report and the plan's progress log was written.

---

## OPEN-24 — LIVE_SMOKE gate

**Audit claim** (`INVESTIGATION_steps-1-3-audit.md:156`): *"the censor is still on duty. This is the
LIVE_SMOKE gate (real 23.1 IDD + an actual EnergyPlus design-day run) — the recommended next
remediation block before Stage 4 planning."* The "censor" refers to W3.7: eppy validating against its
**bundled v8.0.0 IDD** instead of the real 23.1 IDD, silently dropping 11/13 IdealLoads fields.

**Verdict: PARTIALLY FIXED / SUPERSEDED — the gate now exists and is genuinely live, but the mechanism
it was built to test has since changed underneath it, and the test's own narrative is stale.**

**Evidence at HEAD:**

1. **The gate exists and is live, not parked.** `tests/test_sim_integration.py:1-45` is a real
   EnergyPlus-23.1 integration suite (`pytestmark = [pytest.mark.energyplus, pytest.mark.slow]` at
   `:36`). Its only skip condition is environment-gated — the real binary's absence, not a "parked"
   decision in code:
   ```python
   # test_sim_integration.py:24-31
   _EP_PATH = Path(os.environ.get("ENERGYPLUS_PATH", r"C:\EnergyPlusV23-1-0"))
   _EP_EXE = _EP_PATH / ("energyplus.exe" if __import__("sys").platform == "win32" else "energyplus")
   if not _EP_EXE.exists():
       pytest.skip(
           f"EnergyPlus binary not found at {_EP_EXE} — skipping integration tests",
           allow_module_level=True,
       )
   ```
   `test_version_handshake_real_binary` (`:83-86`) asserts the real binary reports `23.1.x`.
   `test_synthetic_fleet_full_annual` (`:91-194`) runs full **annual** `RunPeriod` simulations (a
   stronger live check than a bare design-day dry run) through real EnergyPlus and inspects the real
   `.sql`/`.err` output. No default marker deselection exists — `pyproject.toml:54-57` registers the
   `energyplus`/`slow` markers but sets no `-m "not slow"` in `addopts`, so this suite is collected by
   plain `pytest`, not opted out of by config.

2. **The IDD-version half of the censor complaint is closed.** `openubem/config.py:16,32` resolves
   `ENERGYPLUS_IDD_PATH` to `Path(os.environ.get("ENERGYPLUS_PATH", r"C:\EnergyPlusV23-1-0")) /
   "Energy+.idd"` — the **real 23.1 IDD**, not eppy's bundled v8.0.0. `openubem/idf/builder.py:49-52`
   locks this IDD once per process via `GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))`.

3. **The specific mechanism W3.7 flagged (IdealLoadsAirSystem, try/except-pass around 23.1 fields) no
   longer exists.** `openubem/idf/hvac.py:1-4` now states as an authorized deviation: *"DESIGN §3H
   IdealLoadsAirSystem replaced by archetype-appropriate HVACTemplate objects per RESULT_01 Part C +
   RESULT_02 Tables A/C/D/E."* Grep of `hvac.py` shows only `HVACTEMPLATE:*` objects being created
   (`:108,114,121,133,138,151,157,165,189,239,250,280,290,323,341,379,395,436,478,524,534,560,576,605,615`).
   The old code path this item was about is gone; `try/except Exception: pass` blocks remain
   (`hvac.py:196-217` etc.) but around *different*, HVACTemplate-specific optional fields — not the
   dropped IdealLoads fields the audit named.

4. **But the gate's own embedded finding is now stale.** `test_sim_integration.py:1-8`'s module
   docstring (unedited since the file's last touch, `git log` shows creation `2026-06-10`, one edit
   `2026-06-12`, nothing since) still reads: *"Step-3 IDFs all fatal under EnergyPlus 23.1 due to
   geomeppy surface geometry defects (invalid sun_exposure='NoWind', missing vertex_z_coordinate)."*
   That is **contradicted by the project's own adopted baseline**: `docs/docs_REPORTS/REPORT_phaseE_final.md:74`
   states *"All 12 matrix cells (3 cities × 4 density rings) were re-simulated on Speed SLURM. **8,160
   of 8,160 buildings succeeded (100%).**"* — i.e. the geometry defects this test recorded in June have
   since been fixed elsewhere in the pipeline (the layoutAssigner/storey-matching arc, per project
   memory), but nobody has gone back and updated this test file's comments to match. The test still
   *passes* either way (it asserts classification correctness, not a success rate), so CI gives no
   signal that the docstring is wrong.

**Bottom line:** the LIVE_SMOKE gate the audit called for was built (2026-06-10/12, the day after the
audit) and is a genuine live-binary test, not a synthetic stand-in — that part of OPEN-24 is closed. Its
skip condition today is purely "is `ENERGYPLUS_PATH`'s binary present on this host," which is why it is
currently skipped in this sandbox (no EnergyPlus install here). Its embedded diagnostic text is ~8 weeks
stale and should not be trusted as a description of current IDF health.

---

## OPEN-25 — Modules 04/05/06 bridge (Step 2 → Step 3 seam)

**Audit claim** (`:180`, cross-step X1): *"the bridge (Modules 04/05/06) is the next construction
project, not a defect in what exists. Keep the integration-test requirement when it lands."* The
specific gap (`:176`): Step 2 emitted 26 columns; Step 3 hard-required 15 more
(`u_roof_w_m2k, wwr, infiltration_m3_s_m2, lighting_w_m2, …`) that only existed in a hand-made fixture.

**Verdict: FIXED. The modules exist, are wired end-to-end, and have been run live at fleet scale.**

**Files opened at HEAD:**
- `openubem/semantic/construction_sets.py` (envelope/vintage — "Module 04"): `resolve_vintage`,
  `get_construction_set`, `apply_nan_vintage_provenance`, `append_vintage_donor_flags`.
- `openubem/semantic/loads.py` (loads — "Module 05"): `get_loads`, `_build_flat_loads`, `_get_flat_loads`.
- `openubem/semantic/schedules.py` (schedules — "Module 06"): `build_schedule_library`,
  `write_schedules_to_idf`, `get_schedule_names`.
- `openubem/semantic/__init__.py:273-433` — the orchestrator `enrich_semantics()` that calls all three
  and appends exactly the F17 column set: `_F17_ENVELOPE_COLS` (`:46-54`, includes `u_roof_w_m2k`,
  `u_wall_w_m2k`, `u_window_w_m2k`, `u_floor_w_m2k`, `infiltration_m3_s_m2`) and `_F17_LOADS_COLS`
  (`:55-63`, includes `lighting_w_m2`, `equipment_w_m2`, `wwr`) — the exact 15+ columns the audit named
  as missing. `validate_schema()` (`:100-166`) gates 57 total columns with zero NaN.
- These files were **added the day after the audit**: `git log --diff-filter=A` on
  `construction_sets.py`/`loads.py`/`schedules.py`/`semantic/__init__.py` returns
  `2026-06-10 feat: implement climate zone assignment, building attribute enrichment, parallel
  EnergyPlus runner, and results parsing/carbon components` — i.e. this is the exact "next
  construction project" the audit deferred, and it landed on schedule.
- Formal spec exists at `docs/docs_main/docs_step-2-2/DESIGN_step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and.md`
  and `docs/docs_main/docs_step-2-2/PLAN_step-2-2-implementation.md` — this is a first-class Step
  (Step 2.2), not an ad hoc patch.

**The X1-required integration test (real Step-2 output piped through the bridge into Step 3) exists.**
`tests/test_step3_orchestrator.py:155-212` imports `BuildingClassifier` (`:155`), calls
`enrich_semantics(gdf_29)` (`:158,197`) to get the 57-column frame, then calls `run_step3(gdf_57,
schedule_library, step3_dir, n_jobs=1)` (`:204,212`) — classifier → enrichment → IDF generation in one
test, exactly the seam X1 asked to be integration-tested "when it lands."

**Beyond the test, the bridge is wired into the real fleet pipeline, not just exercised in isolation.**
`scripts/validation/v12_cell_pipeline.py:155-212` chains `BuildingClassifier` → `enrich_semantics` →
`run_step3` as production code, and this is the script family behind the Phase-E fleet run that
produced the adopted ~~158.0~~ **157.1 kWh/m²** (pooled: total simulated energy ÷ total simulated
floor area; the struck figure was a count-weighted mean of the 12 cell means, superseded 2026-08-12,
OPEN-43) baseline (8,160/8,160 buildings, `REPORT_phaseE_final.md:74`).

**Bottom line:** the gap X1/OPEN-25 described is closed — not "still a gap," and not merely "planned."
It was built, tested in isolation (`tests/test_step22_orchestrator.py`, 30+ unit tests), integration-tested
against real Step-2 output (`test_step3_orchestrator.py:155-212`), and run at full fleet scale in
production. Register §7's ⚠️ stale-risk flag on this item should resolve to **CLOSED**.

---

## OPEN-26 — four polish items (`INVESTIGATION_steps-1-3-audit.md:165-166`, W3.12)

**Audit claim verbatim:** *"bbox-fallback never lands in manifest `data_quality_flag`
(`builder.py:263-275`); missing-EPW silently leaves Site:Location at (0,0); `compute_form_factor`
implemented but never called; neighbour bounding boxes recomputed per target in context shading."*
Addendum note: *"the core/perim fallback from C2 does record itself in the manifest now"* (already
fixed as of the audit itself, not one of the four).

Checked each of the four individually against current code:

### 1. bbox-fallback → manifest — EFFECTIVELY FIXED (relocated to a different column)
`openubem/idf/builder.py:611-627`:
```python
has_bbox_fallback = any(z.get("fallback_to_bbox") for z in zones)
gen_status = "fallback_bbox" if (has_bbox_fallback or simp_status == "bbox") else "success"
...
return {
    ...
    "generation_status": gen_status,
    ...
}
```
The bbox fallback **does** now reach the manifest — but through the `generation_status` column
(`"fallback_bbox"`), not through `data_quality_flag` as the audit's literal wording specified. Any
manifest reader can detect it today; the audit's exact column name is not the one carrying the signal.
Call this **substantively fixed, technically relocated**.

### 2. missing-EPW → Site:Location left at (0,0) — STILL OPEN
`openubem/idf/builder.py:210-212`:
```python
epw_path = row.get("epw_path")
if epw_path and Path(str(epw_path)).exists():
    _populate_site_location_from_epw(self.idf, Path(str(epw_path)))
```
No `else` branch — no flag, no log, no error when `epw_path` is missing/absent. The template default is
literally `(0.0, 0.0, 0.0, 0.0)`, e.g. `openubem/idf/templates/commercial_base.idf:33-35`:
```
Site:Location,
    PLACEHOLDER,             !- Name (overwritten from EPW header)
    0.0, 0.0, 0.0, 0.0;      !- Latitude, Longitude, Time Zone, Elevation
```
Confirmed still silent at HEAD.

### 3. `compute_form_factor` implemented but never called — STILL OPEN
Repo-wide grep for `compute_form_factor` (`*.py`) returns exactly two sites: its definition
(`openubem/geometry/footprint.py:66`) and its test (`tests/test_footprint.py:13,179,186,191`). No call
site anywhere in `openubem/idf/` or `openubem/geometry/` production code. Confirmed still unused at HEAD.

### 4. neighbour bounding boxes recomputed per target — STILL OPEN
`openubem/geometry/context.py:7-44`, `discover_context()`, called once per **target** building from
`openubem/idf/builder.py:425` (inside the per-building `build()` method, i.e. once per row in the fleet
loop). Inside it, for every candidate neighbour found via the spatial index:
```python
# context.py:24
ctx_box = ctx_row.geometry.minimum_rotated_rectangle
```
There is no cache keyed on neighbour id — a building that sits in the shading sphere of many targets
(dense blocks) has its `minimum_rotated_rectangle` recomputed once per target that sees it. Confirmed
still present at HEAD.

**Bottom line:** 1 of 4 is substantively fixed (relocated column), 3 of 4 remain exactly as described.
Consistent with the audit's own framing — "none load-bearing" — none of the three open ones produce a
wrong answer, only wasted cycles or a silently-defaulted site location.

---

## OPEN-27 — DESIGN doc carries a wrong archetype name

**Not fixed here — this is read-only for this task.** Confirmed still present at HEAD:

`openubem/data/openstudio_archetypes.json:99-111` — the only two `sector: "Residential"` archetypes in
the live 30-archetype vocabulary are `MidriseApartment` (`:100-101`) and `HighriseApartment`
(`:107-108`). `MultifamilyHome` does not exist in this file, confirmed by a repo-wide grep for
`"MultifamilyHome"` inside `openubem/data/openstudio_archetypes.json` returning **no matches**.

The DESIGN doc still names the wrong archetype:

> **PASTE-READY BLOCK FOR THE EXTERNAL DESIGN TOOL:**
> **Document:** `docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md`
> **Location:** line 529
> **Current (wrong) text:** `- **residential** ⇔ `sector == "Residential"` (2 archetypes — MidriseApartment, MultifamilyHome)`
> **Wrong name:** `MultifamilyHome`
> **Correct name:** `HighriseApartment`
> **Why:** `openubem/data/openstudio_archetypes.json` (the live 30-archetype vocabulary) has no
> `MultifamilyHome` entry; the two Residential-sector archetypes it defines are `MidriseApartment` and
> `HighriseApartment` (`openstudio_archetypes.json:99-111`).

**Secondary note (not part of the paste-ready block, informational only):** the identical error is
copied into a second, in-repo document that is *not* DESIGN and *not* read-only by this project's own
rules — `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78` — *"exactly **2
archetypes**: `MidriseApartment`, `MultifamilyHome`."* This task's remediation ban covers it too, so it
is reported, not touched.

---

## The fifth ⏳ at `INVESTIGATION_steps-1-3-audit.md:62` (W1.8) — not a register item

**Audit text:** *"MultiPolygon explode is a per-row `iterrows` copy of a ~150-column frame instead of
vectorized `gdf.explode()` (`:352-378`), and the full raw width is dragged through all 7 cleaning steps
before trimming to 23 columns at the end… ⏳ STILL OPEN (deliberately): efficiency-only, no wrong answers
produced… Worth a small task before city-scale runs."*

**Verdict: STILL TRUE at HEAD.** Confirmed on both counts:

1. **Per-row iterrows explode still present.** `openubem/acquisition/osm_fetcher.py:374-388`:
   ```python
   # Step 3: explode MultiPolygon → Polygon parts, re-key osm_id
   ...
   for orig_idx, row in gdf.iterrows():
       if row.geometry.geom_type == "MultiPolygon":
           for k, part in enumerate(row.geometry.geoms):
               new_row = row.copy()
               ...
   ```
   No vectorized `gdf.explode()` in the file (grep for `explode(` returns zero matches for the
   vectorized form; only the manual `iterrows` version exists).

2. **Full raw width still dragged through all cleaning steps.** `openubem/acquisition/osm_fetcher.py:53,60,101`:
   `gdf = _flatten_tags(raw)` (raw ~150 cols) → `gdf, _clean_log_lines = _seven_step_clean(gdf)` (the
   7-step cleaner, including the explode above, runs on the full-width frame) → only at line `101`,
   near the very end of `ingest_buildings`, does `gdf = gdf[_SCHEMA_COLUMNS]` trim to the 23-column
   schema. The column trim has not been moved earlier.

**Is it register-worthy?** Reporting the finding, not ruling on it (per task instructions, this is the
manager's call, and the register is not edited here): it is a genuine, reproducible, still-open
performance defect with the same "no wrong answers, just wasted cycles" character as three of the
OPEN-26 items — the difference is OPEN-26's items are Step 3 (small-fleet-scale, one row at a time);
this one is Step 1 ingest, which runs before any of Steps 2–5 and re-runs on every fresh city extract.
Given the project has now completed a 12-cell, 8,160-building fleet run, "before city-scale runs" (the
audit's own trigger condition for prioritizing this) may already have arrived. Whether that promotes it
to a register item is left to the manager.

---

## Summary table

| Item | Verdict | Primary HEAD evidence |
|---|---|---|
| OPEN-24 | Partially fixed / superseded — gate exists & live; mechanism changed; docstring stale | `tests/test_sim_integration.py:24-31,83-86`, `openubem/config.py:16,32`, `openubem/idf/hvac.py:1-4` |
| OPEN-25 | FIXED — bridge built, unit- and integration-tested, run at fleet scale | `openubem/semantic/__init__.py:273-433`, `tests/test_step3_orchestrator.py:155-212`, `scripts/validation/v12_cell_pipeline.py:155-212` |
| OPEN-26 | 1/4 fixed (relocated), 3/4 still open | `openubem/idf/builder.py:210-212,611-627`, `openubem/geometry/footprint.py:66`, `openubem/geometry/context.py:24` |
| OPEN-27 | Still wrong at HEAD — not fixed here, per task rule | `docs/docs_main/docs_step2/DESIGN_...archetyp.md:529` vs `openubem/data/openstudio_archetypes.json:99-111` |
| Fifth ⏳ (`:62`) | Still true at HEAD; not a register item; deserves-item question left to manager | `openubem/acquisition/osm_fetcher.py:374-388,53,60,101` |
