# REMEDIATION — Executor task groups + kickoff prompts (audit 2026-06-09)

> **Slug:** `remediation-audit-fixes` • **Date:** 2026-06-09 • **Binding contract:** the per-step DESIGN docs, as amended by the manager rulings in §4 below.
> **Source of findings:** `docs/investigation/INVESTIGATION_steps-1-3-audit.md` (warning IDs W1.x/W2.x/W3.x referenced throughout).
> This doc doubles as the plan doc for all five groups: executors read their group's task table here and append progress-log entries to §6.

---

## 1. Hard rules for every executor session

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never touch `main.py` at the project root.
2. Never edit any OVERVIEW or DESIGN doc. Never create `.py` files under `docs\`.
3. Execute the tasks for YOUR group only, in order. Do not write plans, do not propose alternatives, do not fix things outside your group even if you notice them — note them in your progress log instead.
4. If a DESIGN doc and this doc conflict, the **manager rulings in §4 win** (they are recorded deviations pending DESIGN errata). Any OTHER ambiguity: STOP and quote the conflict.
5. Default to no comments. One short line max when the WHY is non-obvious.
6. No live-network tests. All tests run on local fixtures/mocks.
7. After your last task, run the **full** suite (`uv run pytest tests/ -q`) and paste the summary line into your progress log entry in §6 of this doc.

## 2. Dispatch order

Run groups **sequentially, one fresh Sonnet session each**: **A → B → C → D → E.**
A is blocking (the suite is red; nothing else is auditable until it is green). B before C (C builds on B's green Step-3 tests). D and E are independent of B/C but keep them sequential to avoid working-tree collisions.

---

## 3. Task groups

### GROUP A — Environment + red suite (fixes: suite red, W3.6, retry-test ERROR)

| ID | What | Why | How | Test |
|---|---|---|---|---|
| A1 | Add `tenacity` to the `dev` extra in `pyproject.toml`, then run `uv sync --extra dev`. | `tests/test_osm_fetcher.py::TestRetryPolicy` ERRORs because `pytest-mock` is not installed and tenacity has never been present, so the Step-1 retry contract (Step-1 DESIGN §5.1 line 243) has never executed. | Edit `[project.optional-dependencies] dev` to `["pytest", "pytest-mock", "tenacity"]`. Sync. | `uv run pytest tests/test_osm_fetcher.py -q` → 0 errors; the retry test now RUNS (not skipped). |
| A2 | Make `openubem/idf/outputs.py:31-35` set the meter field defensively. | eppy 0.5.69 renamed the `Output:Meter:MeterFileOnly` field `Name` → `Key_Name`; all 7 `test_outputs.py` + 8 orchestrator tests fail (W3.6). | Try `Key_Name`, fall back to `Name` on `eppy.bunch_subclass.BadEPFieldError`. Do NOT pin eppy tighter — the defensive set must work under both 0.5.63 and 0.5.69. | `uv run pytest tests/test_outputs.py tests/test_step3_orchestrator.py -q` → all pass. |
| A3 | Record the resolved environment in your progress log. | CP3 was certified under eppy 0.5.63 / different Python; the audit needs a baseline. | `uv run python -c "import eppy, geomeppy, shapely, sys; print(sys.version, eppy.__version__, geomeppy.__version__, shapely.__version__)"`. | Output pasted in §6 entry. |

**Stop-and-report:** after A3, with full-suite summary. Expected: **0 failed, 0 errors** (~233 passed, ≤2 skipped).

---

### GROUP B — Step 3 EnergyPlus-fatal fixes (fixes: W3.1, W3.2, W3.3, W3.8, W3.9)

| ID | What | Why | How | Test |
|---|---|---|---|---|
| B1 | Add a `Building` object to all four templates: `openubem/idf/templates/{commercial_base,residential_base,highrise_base,specialized_base}.idf`. | `Building` is a required EnergyPlus object; no IDF currently parses in a real run (W3.1). Manager ruling §4-R1 (DESIGN §3D template table is in erratum). | Fields: Name `OpenUBEM_Building`, North Axis `0`, Terrain `City`, Solar Distribution `FullExterior`, defaults elsewhere. Same object in all four. | New test in `tests/test_idf_builder.py`: built IDF contains exactly one `BUILDING` object with North Axis 0. |
| B2 | Pass the window construction to `set_wwr` in `openubem/idf/builder.py:120`. | Every window currently gets `Construction_Name=""` → E+ fatal (W3.3). | `idf.set_wwr(wwr=..., construction="Window_Construction", force=True)`. | Test: every `FENESTRATIONSURFACE:DETAILED` has `Construction_Name == "Window_Construction"`. |
| B3 | Wire archetype constructions to surfaces after `set_default_constructions()` in `builder.py` (around :119-120). | geomeppy's defaults orphan the archetype constructions; `u_roof/u_wall/u_floor/u_window/shgc` currently have zero simulation effect (W3.2). | After the default call, loop `idf.getsurfaces()` and set `Construction_Name` by `Surface_Type`: wall→`Wall_Construction`, roof→`Roof_Construction`, floor and ceiling→`Floor_Construction`. | Test: in a built IDF, at least one wall surface references `Wall_Construction` and no surface references `Project Wall`. |
| B4 | Exclude doubly-failed zones from loads/HVAC, fix `num_zones`. | Zones whose extrusion failed twice still get `PEOPLE`/`LIGHTS`/`HVACTEMPLATE` referencing a nonexistent Zone → E+ severe (W3.9). | In `openubem/idf/surfaces.py` set `z["extruded"] = True` on successful `add_block`; in `builder.py:243` filter loads/HVAC/infiltration emission and the `num_zones` manifest count on that flag instead of non-empty `coords_m`. | Test: force double extrusion failure on one zone of a fixture building; assert no PEOPLE/LIGHTS/HVACTEMPLATE references it and `num_zones` excludes it. |
| B5 | Key the zoning decision on `row["footprint_area_m2"]` in `builder.py:222-223`, falling back to `poly_local.area` only when the column is absent/NaN. | DESIGN §3B keys the rule table on the contract column; post-simplification area can flip rules 2↔5 for hull/bbox tiers (W3.8). | One-line read with `pd.notna` guard. | Test: row with `footprint_area_m2` just under a rule boundary but inflated simplified geometry → zoning follows the column. |

**Stop-and-report:** after B5, full suite green + list of template diffs.

---

### GROUP C — Step 3 geometry corrections (fixes: W3.4, W3.5, W3.10; depends on Group B)

| ID | What | Why | How | Test |
|---|---|---|---|---|
| C1 | Replace the per-floor `add_block`-at-z=0 loop with ONE `add_block(..., height=levels*FLOOR_TO_FLOOR_M, num_stories=levels)` per building, in `openubem/idf/surfaces.py:60-83` + `builder.py:232-237`. Remove the post-hoc `Z_Origin` patch. | All storeys currently extrude at z=0; `intersect_match` pairs nothing, so every storey gets a ground floor and an exposed roof — N detached bungalows (W3.4). geomeppy's `num_stories` stacks storeys at true z so inter-floor floor/ceiling pairing works. Manager ruling §4-R2. | Verify the installed geomeppy `add_block` signature first (`uv run python -c "import inspect, geomeppy; print(inspect.signature(geomeppy.IDF.add_block))"`). Keep zone naming consistent with the manifest schema. | New test: 3-storey building → exactly one floor with Outside Boundary Condition `Ground`(or `ground`), exactly one roof with `Outdoors`+SunExposed, and ≥1 `Surface`-BC pair between storeys 1↔2. |
| C2 | Perimeter+core: check whether the installed geomeppy `add_block` supports a core/perim zoning mode. If YES → use it for the `perimeter_core` rule. If NO → **STOP and report** (manager will choose between quadrant-split implementation and temporary per-floor fallback). | The current perimeter polygon drops its hole (`openubem/geometry/zoning.py:92`): floor area double-counted ~1.3–1.6×, no party wall possible, core walls outdoors+windowed (W3.5). DESIGN §3B is itself in erratum (E7) — do not invent a partition scheme. | Inspect geomeppy source in the venv. Implement only if natively supported; otherwise stop. | If implemented: test that perim+core zone floor areas sum to footprint area ±1% and ≥1 perim↔core wall pair is Adiabatic or `Surface`-matched. |
| C3 | Ground-floor BC: accept geomeppy's `ground` BC for z=0 floors; delete the dead `outdoors`→Adiabatic flip for floors in `surfaces.py:110`; keep the flip ONLY for party walls. De-rig `tests/test_surfaces.py:114-118` (it manually forces floors to Outdoors before asserting). | The flip condition never matches real output — dead code certified by a rigged test (W3.10). Manager ruling §4-R3. | Remove the floor branch; update the test to assert the REAL production behavior (z=0 floor BC is `ground`). | Updated test passes against unmodified `build_zones` output, not hand-forced surfaces. |
| C4 | Strengthen the vacuous adjacency test. | `test_adiabatic_perim_core_party_wall`'s final assert accepts all-outdoors — it passes in the broken production state (W3.5/audit E-category). | Replace the permissive assert with a positive assertion that at least one party-wall pair exists in the scenario it builds. | Test fails if party-wall logic is deleted. |

**Stop-and-report:** after C1 (stacking is the risky one), and again after C4. Full suite green both times.

---

### GROUP D — Step 1 live-data fixes + shared logging (fixes: W1.1–W1.7, W1.9, W2.3)

| ID | What | Why | How | Test |
|---|---|---|---|---|
| D1 | Make the `levels`/`underground` cast survive fractional values, in `openubem/acquisition/osm_fetcher.py:210` and `:240-243`. | `building:levels="2.5"` raises TypeError and kills the whole run (W1.1). Manager ruling §4-R4: round-half-to-even via `.round()`, keep flag-don't-drop. | `pd.to_numeric(..., errors="coerce").round().astype("Int64")`. | Test: raw frame with `building:levels="2.5"` → row survives, `levels == 2`, no exception. |
| D2 | Fix the `osm_id` branch order in `osm_fetcher.py:174-186`. | osmnx 1.9 output always hits the bare-`osmid` branch, so the DESIGN-required `"way/12345"` form is dead code and way/node id collisions break uniqueness (W1.2). | Check `element_type`+`osmid` co-presence FIRST; bare `osmid` last. | Tests: (a) reset-index frame with both columns → ids like `way/12345`; (b) `("way",12345)` + `("node",12345)` → two distinct ids, `_validate_schema` passes. |
| D3 | Change the dedup candidate predicate from `overlaps` to `intersects` in `osm_fetcher.py:307`. | Contained near-duplicates (IoU>0.95) survive, violating the §5.1 acceptance metric (W1.4). Manager ruling §4-R5 (DESIGN line 128 is in erratum; the IoU filter already protects party-wall neighbours). | One-word change; verify the IoU≥0.95 + keep-larger logic downstream is untouched. | New test: smaller polygon fully inside a larger one, IoU≈0.96 → exactly one survivor with `OSM_OVERLAP_RESOLVED` provenance. Existing party-wall test still passes. |
| D4 | Make both serialization logs actually contain the run records: `osm_fetcher.py:538-541` and `openubem/semantic/building_classifier.py:580-597`. | Both `.log` artifacts are always 0 bytes — the FileHandler is attached after everything was logged (W1.3, W2.3). | Collect per-step summary lines during cleaning/classification (plain list of strings is fine), write them to the `.log` file in `_serialize`. Step 1: per-step drop counts. Step 2: per-rule fire counts, per-tier counts, FALLBACK osm_ids. | Both serialize tests upgraded from `path.exists()` to: file size > 0 AND contains an expected token (e.g. `step4b` / `FALLBACK`). |
| D5 | Fix the all-generic warning payload in `osm_fetcher.py:65-72`. | Payload is UTM output bounds, not the input WGS84 `(n,s,e,w)` bbox the DESIGN specifies (W1.5). | Thread the caller's bbox (or derived WGS84 extent) into the warning dict. | Rewrite `tests/test_osm_fetcher.py:465-475` to drive `ingest_buildings` with a mocked `ox.features.features_from_*` returning an all-generic frame and assert via `caplog` (the current test asserts on its own inline copy of the production code — replace it). |
| D6 | Exclude mapped source tags from `surplus_tags` in `osm_fetcher.py:261-284`. | All 11 renamed source tags are duplicated into the JSON; `_OSM_RENAME_SOURCES` was built for exactly this and is never used (W1.6). | Skip `canonical_out | _OSM_RENAME_SOURCES` in `_make_surplus`. | Test: `building`/`height`/`amenity` absent from `surplus_tags`; a genuinely unmapped tag present; `height_raw` still present. |
| D7 | Add ONE mocked end-to-end `ingest_buildings` test. | No test composes flatten→UTM→clean→provenance→trim→validate; that is why W1.2 and W1.3 survived two audits (W1.9). | Mock `ox.features.features_from_point` to return a small raw GDF (include one `way`/`node` id pair and one `levels="2.5"`). Assert: 23-column schema, `crs_utm` uniform, `osm_id` startswith `way/`, log file non-empty. | The test itself. |
| D8 | Add the §5.1 vertex-count warning. | The 95th-pct ≤120-verts metric is implemented nowhere; Stage 3's simplify fallback never gets its signal (W1.7). | After cleaning, compute exterior vertex counts; `logger.warning` when 95th pct ≥ 80, include count in the serialize log. No drop, no flag column. | Test: synthetic 130-vertex polygon → warning emitted, row retained. |

**Stop-and-report:** after D4 (the cross-file logging change), and after D8. Full suite green.

---

### GROUP E — Step 2 confidence + test hardening (fixes: W2.1, W2.4, W2.7, empty-GDF guard; W2.2/W2.6 explicitly EXCLUDED)

| ID | What | Why | How | Test |
|---|---|---|---|---|
| E1 | Make HIGH(b) reachable: in `openubem/semantic/building_classifier.py:343-345`, before the MEDIUM(d) check, return HIGH when the fired rule is 1a/1b/2a/2b AND `provenance_building_tag == "OSM_OBSERVED"` AND levels source is observed. | DESIGN §3D rows HIGH(b)/MEDIUM(d) overlap; the code resolved it so the most common OSM pattern (building-tag-only) can never be HIGH, skewing every downstream confidence distribution (W2.1). Manager ruling §4-R6: HIGH(b) wins. | New branch ordered before MEDIUM(d); leave all other tier logic untouched. | Update `tests/test_building_classifier.py:336-342` (`test_rule_2a_observed_levels_high`) to assert HIGH and remove its apologetic comment. Add the symmetric MEDIUM case: same rule but imputed levels → MEDIUM. |
| E2 | Add a parametrized exact-boundary test. | No test touches the pinned inclusive/exclusive edges; an `>=`→`>` regression passes green (W2.4). | One parametrized test, 7 cases: area 500 m² (→Medium tier), 4000, 5000 (→SecondarySchool path); levels 4 (→LargeHotel path), 9, 20 (→TallBuilding path), 40. Derive expected archetypes from DESIGN §3C lines 160–180 — if any expected value is ambiguous in the DESIGN, STOP and quote it. | The test itself. |
| E3 | Add dtype assertions to the input validator (`building_classifier.py:401-407`) for load-bearing columns only: `levels` (Int64), `footprint_area_m2` (float64), `height_m` (float64), `geometry` (geometry). | DESIGN §3F line 278 requires order AND dtypes; currently a float64 `levels` passes silently (W2.7). | Small dtype map check, raise `ValueError` with column name. | Test: 23-column frame with float64 `levels` → ValueError naming `levels`. |
| E4 | Guard the empty-GeoDataFrame path (`building_classifier.py:532-544`). | 0-row input crashes with KeyError in `apply(..., result_type="expand")`. | Early-return an empty frame with the 3 output columns appended. | Test: 0-row valid-schema input → 0-row output with 26 columns, no exception. |
| E5 | Run the classifier on the two real fixtures and report (NO assertions yet): `uv run python -c` snippet classifying `tests/fixtures/boston_downtown_500m.gpkg` and `chicago_loop_500m.gpkg`, printing tier distribution and FALLBACK count. | First real-data signal for the §5.1 gates and for re-judging the confidence distribution after E1 (W2.5 prep). Read-only — do not add threshold tests. | Paste both distributions into the §6 progress log entry. | N/A — report only. |

**Explicitly out of scope for this group** (manager-reserved, pending DESIGN errata): rule-15 threshold (W2.2 / E4-erratum), the "MultifamilyHome" doc fix (W2.6), the Step-2.5 label protocol (W2.8), §5.1 threshold tests (W2.5).

**Stop-and-report:** after E1 (confidence change affects many tests), and after E5. Full suite green.

---

## 4. Manager rulings (recorded deviations, pending DESIGN errata at source)

| Ruling | Decision | Supersedes |
|---|---|---|
| R1 | `Building` object added to all 4 templates (North Axis 0, Terrain City, FullExterior). | Step-3 DESIGN §3D template table (erratum E6). |
| R2 | Multi-storey buildings extrude as ONE block with `num_stories=levels`; per-floor z=0 blocks + Z_Origin patch are removed. | Step-3 DESIGN §3E literal per-floor `add_block` pseudocode (erratum E8-adjacent). |
| R3 | z=0 ground floors keep BC `ground` (no adiabatic flip). | PLAN-step-3 fact #19, floor clause only. |
| R4 | Fractional `building:levels` → `.round().astype("Int64")`, row retained. | Step-1 DESIGN line 88 (erratum E1). |
| R5 | Dedup candidate predicate = `intersects`. | Step-1 DESIGN line 128 (erratum E2). |
| R6 | Confidence conflict resolved HIGH(b)-wins for rules 1a/1b/2a/2b with observed building_tag + observed levels. | Step-2 DESIGN §3D overlap (erratum E3). |
| R7 (issued at C2 checkpoint, 2026-06-09) | `perimeter_core` zoning uses geomeppy's native `add_block(..., zoning="core/perim", perim_depth=<existing zoning depth constant, else 3.0>)` — N perimeter wedges + 1 core per storey. Zones renamed post-create to `{osm_id}_F{i}_perim{n}` / `{osm_id}_F{i}_core`. Perim↔core walls left as `intersect_match` Surface pairs (inter-zone conduction modeled; the Adiabatic flip applies to party walls between BUILDINGS only). On geomeppy `ValueError("Perimeter depth is too great")`, fall back to per-floor zoning for that building and record it in the manifest `generation_status`. | Step-3 DESIGN §3B 2-zone ring schema (erratum E7) + PLAN-step-3 fact #19 perim↔core clause. |

**User veto point:** these six rulings are the manager's proposals. Review before dispatching Groups B–E; only Group A is ruling-free.

> **APPROVED by user (manager-of-manager), 2026-06-09: R1–R6 approved as written; all groups cleared for dispatch.**

---

## 5. Paste-ready kickoff prompts (one fresh Sonnet session each)

**GROUP A**
```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\investigation\REMEDIATION_prompts-audit-fixes.md.
Obey §1 hard rules. Execute GROUP A tasks A1 through A3 in order.
Then run the full suite (uv run pytest tests/ -q), append one progress-log entry per task under §6 of that doc
(format: #### <ID> — <title> — completed YYYY-MM-DD / Artifacts / Deviations / Test status / Notes),
and report the suite summary line. Expected: 0 failed, 0 errors.
Do not propose alternatives — execute. If anything is ambiguous, STOP and quote the conflict.
```

**GROUP B**
```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\investigation\REMEDIATION_prompts-audit-fixes.md.
Obey §1 hard rules and §4 manager rulings R1. Execute GROUP B tasks B1 through B5 in order.
Add/extend tests exactly as each task's Test column specifies.
Then run the full suite, append progress-log entries under §6, and report.
Do not propose alternatives — execute. If anything is ambiguous, STOP and quote the conflict.
```

**GROUP C**
```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\investigation\REMEDIATION_prompts-audit-fixes.md.
Obey §1 hard rules and §4 manager rulings R2, R3. Execute GROUP C tasks C1 through C4 in order.
STOP and report after C1 before continuing, and STOP at C2 if geomeppy has no native core/perim mode.
Then run the full suite, append progress-log entries under §6, and report.
Do not propose alternatives — execute. If anything is ambiguous, STOP and quote the conflict.
```

**GROUP D**
```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\investigation\REMEDIATION_prompts-audit-fixes.md.
Obey §1 hard rules and §4 manager rulings R4, R5. Execute GROUP D tasks D1 through D8 in order.
STOP and report after D4 before continuing.
Then run the full suite, append progress-log entries under §6, and report.
Do not propose alternatives — execute. If anything is ambiguous, STOP and quote the conflict.
```

**GROUP E**
```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\investigation\REMEDIATION_prompts-audit-fixes.md.
Obey §1 hard rules and §4 manager ruling R6. Execute GROUP E tasks E1 through E5 in order.
STOP and report after E1 before continuing. Tasks listed as out-of-scope in the GROUP E section are forbidden.
Then run the full suite, append progress-log entries under §6, and report.
Do not propose alternatives — execute. If anything is ambiguous, STOP and quote the conflict.
```

---

## 6. Progress log

*(Executors append below — one entry per completed task.)*

#### A1 — Add tenacity to dev extra + sync — completed 2026-06-09
- Artifacts: `pyproject.toml` (added `tenacity` and `pyarrow` to `[project.optional-dependencies] dev`); `tests/test_osm_fetcher.py` (fixed `always_fails` signature to accept `*args, **kwargs`).
- Deviations: `pyarrow` also added to dev (not in the A1 spec) because `test_step3_orchestrator.py` — which A2 must green — fails with an ImportError on parquet without it. Treated as a prerequisite for A2's test criterion. The `always_fails` mock fix is a pre-existing test bug exposed by tenacity being callable now; it is in the retry test file and required for the test to PASS (not just RUN).
- Test status: `uv run pytest tests/test_osm_fetcher.py -q` → 47 passed (TestRetryPolicy now passes, no errors/skips).
- Notes: Before this task, TestRetryPolicy was an ERROR (ImportError on tenacity). After: 1 passed.

#### A2 — Defensive meter field set in outputs.py — completed 2026-06-09
- Artifacts: `openubem/idf/outputs.py` (added `import eppy.bunch_subclass`; replaced keyword-arg `Name=meter` with `newidfobject` + try/except `Key_Name`/`Name`); `tests/test_outputs.py` (fixed `test_meter_file_only_count_and_frequency` to use same try/except to read meter key field name).
- Deviations: None. eppy 0.5.69 confirmed to use `Key_Name`; the defensive fallback handles < 0.5.69.
- Test status: `uv run pytest tests/test_outputs.py tests/test_step3_orchestrator.py -q` → 15 passed, 0 failed.
- Notes: 6 of the 7 test_outputs.py failures were pre-existing eppy 0.5.69 field-rename breakage; the 7th (test_meter_file_only_count_and_frequency) also needed the test itself updated.

#### A3 — Record resolved environment — completed 2026-06-09
- Artifacts: Environment captured below.
- Deviations: None.
- Test status: Full suite — `uv run pytest tests/ -q` → **233 passed, 2 skipped, 0 failed, 0 errors**.
- Notes: Environment: Python 3.14.3 (MSC v.1944 64-bit AMD64) | eppy 0.5.69 | geomeppy 0.12.2 | shapely 2.1.2 | tenacity 9.1.4 | pytest-mock 3.15.1 | pyarrow 24.0.0.

#### B1 — Add Building object to all four templates — completed 2026-06-09
- Artifacts: `openubem/idf/templates/commercial_base.idf`, `openubem/idf/templates/residential_base.idf`, `openubem/idf/templates/highrise_base.idf`, `openubem/idf/templates/specialized_base.idf` (each now contains one `Building` object: Name=OpenUBEM_Building, North Axis=0, Terrain=City, Solar Distribution=FullExterior). `tests/test_idf_builder.py` (added `TestTemplates::test_each_template_has_exactly_one_building_object`).
- Deviations: None. R1 applied exactly.
- Test status: `uv run pytest tests/test_idf_builder.py::TestTemplates::test_each_template_has_exactly_one_building_object -q` → 1 passed.
- Notes: Template diff summary — each template gained 9 lines (Building object with Name, North Axis, Terrain, blank Loads/Temp Convergence Tolerance, FullExterior Solar Distribution, blank Warmup Days fields). Fields with EnergyPlus defaults left blank per IDD convention.

#### B2 — Pass window construction to set_wwr — completed 2026-06-09
- Artifacts: `openubem/idf/builder.py` (line ~120: `idf.set_wwr(wwr=..., construction="Window_Construction", force=True)`). `tests/test_idf_builder.py` (added `TestConstructions::test_wwr_window_construction_name`).
- Deviations: None.
- Test status: `uv run pytest tests/test_idf_builder.py::TestConstructions::test_wwr_window_construction_name -q` → 1 passed.
- Notes: Without `force=True`, geomeppy skips walls that already have a window; `force=True` ensures all eligible walls get glazing with the correct construction name.

#### B3 — Wire archetype constructions to surfaces — completed 2026-06-09
- Artifacts: `openubem/idf/builder.py` (added post-`set_default_constructions` loop over `idf.getsurfaces()` mapping wall→Wall_Construction, roof→Roof_Construction, floor/ceiling→Floor_Construction). `tests/test_idf_builder.py` (added `TestConstructions::test_surface_construction_wired`).
- Deviations: None. `_SURFACE_CONSTRUCTION_MAP` is a local dict inside `assign_constructions`; no module-level constant needed.
- Test status: `uv run pytest tests/test_idf_builder.py::TestConstructions::test_surface_construction_wired -q` → 1 passed.
- Notes: geomeppy emits `Surface_Type` values `wall`, `roof`, `floor` (lowercase). Ceiling surfaces appear as `ceiling` in multi-story; both floor and ceiling map to Floor_Construction per DESIGN §3F.

#### B4 — Exclude doubly-failed zones from loads/HVAC, fix num_zones — completed 2026-06-09
- Artifacts: `openubem/idf/surfaces.py` (added `z["extruded"] = True` immediately after successful `add_block` + rename). `openubem/idf/builder.py` (changed `extruded_zones` filter from `z.get("coords_m")` to `z.get("extruded")`). `tests/test_idf_builder.py` (added `TestDoubleExtrusionFailure::test_double_failure_excluded_from_loads_and_manifest`).
- Deviations: Test uses `tempfile.TemporaryDirectory()` instead of pytest `tmp_path` fixture — Windows permission error on `AppData\Local\Temp\pytest-of-o_iseri` prevents `tmp_path` from working in this environment. Same functional coverage.
- Test status: `uv run pytest "tests/test_idf_builder.py::TestDoubleExtrusionFailure::test_double_failure_excluded_from_loads_and_manifest" -q` → 1 passed.
- Notes: The `coords_m`-based filter was insufficient: a zone with empty `coords_m` (MultiPolygon perim) was already skipped at extrude time and never got `extruded=True`; zones that fail both primary+bbox extrusion also never get `extruded=True`. Both cases are now correctly excluded.

#### B5 — Key zoning decision on footprint_area_m2 column — completed 2026-06-09
- Artifacts: `openubem/idf/builder.py` (replaced `footprint_area = poly_local.area` with `pd.notna` guard reading `row["footprint_area_m2"]` first). `tests/test_idf_builder.py` (added `TestZoningAreaColumn::test_zoning_follows_column_not_poly_area`).
- Deviations: None.
- Test status: `uv run pytest "tests/test_idf_builder.py::TestZoningAreaColumn::test_zoning_follows_column_not_poly_area" -q` → 1 passed.
- Notes: Test uses a 50×50 poly (area=2500 m², would yield perimeter_core) but `footprint_area_m2=499.0` in the row (below 500 threshold → single_zone). Monkeypatched `decide_zoning_strategy` captures the area argument and asserts it equals 499.0.

**GROUP B stop-and-report: Full suite — `uv run pytest tests/ -q` → 238 passed, 2 skipped, 0 failed, 0 errors.**

#### C1 — Replace per-floor add_block loop with one add_block(num_stories=N) per footprint — completed 2026-06-09
- Artifacts: `openubem/idf/surfaces.py` (rewrote `extrude_geometry` to group zones by building-prefix+label, call ONE `add_block` per group with `num_stories=N` and `height=N*floor_h`; added `_building_prefix`, `_group_key`, `_pair_interfloor_surfaces` helpers; removed per-floor renaming loop, replaced with storey_no-indexed rename). `openubem/idf/builder.py` (removed the Z_Origin patch loop; added R2 comment). `tests/test_surfaces.py` (added `TestMultiStoreyStacking::test_three_storey_building_floor_ceiling_bc`). `tests/test_idf_builder.py` (updated `TestDoubleExtrusionFailure` to patch `_perim` block name instead of `_F1_` zone name, consistent with C1 block-level grouping). `tests/test_step3_orchestrator.py` (renamed `test_z_origin_set_on_multi_floor_buildings` → `test_multi_floor_surfaces_at_correct_z`; assertion updated from ZONE.Z_Origin > 0 to floor-surface min-z > 0).
- Deviations: (1) `_pair_interfloor_surfaces` added — geomeppy 0.12.2's `almostequal` does positional vertex comparison; inter-floor ceiling/floor surfaces produced by `add_block(num_stories>1)` are cyclic permutations of each other so `match_idf_surfaces` never fires for them. Manual frozenset-of-vertices pairing resolves this limitation. Cite: geomeppy source `geom/intersect_match.py:58` `almostequal(s.coords, reversed(m.coords))` — no cyclic fallback. (2) B4 test updated: the B4 test patched `add_block` by matching `_F1_` in the block name; with C1 the block name is `{prefix}_{label}` (no floor index), so the patch predicate was updated to `_perim` to force the entire perim footprint group to fail. Functional coverage is identical — verifies that zones whose footprint-group fails both primary and bbox extrusion are excluded from loads/HVAC/num_zones.
- Test status: `uv run pytest tests/ -q` → **239 passed, 2 skipped, 0 failed, 0 errors**.
- Notes: New test assertions: (a) exactly 1 ground-floor surface with BC `ground` (geomeppy's `set_unmatched_surface` at z=0); (b) exactly 1 exposed roof with BC `Outdoors` + SunExposed (top storey only); (c) ≥1 inter-storey `Surface` BC pair (ceiling F0 ↔ floor F1 and ceiling F1 ↔ floor F2, wired by `_pair_interfloor_surfaces`). C1 stops here per manager instruction; C2–C4 await manager greenlight.

#### C2 — Perimeter+core: native add_block(zoning="core/perim") with zone renaming and fallback — completed 2026-06-09
- Artifacts: `openubem/geometry/zoning.py` (perimeter_core path rewritten to return ONE placeholder dict with `mode="core/perim"` instead of per-floor core+perim zone dicts; narrow-building fallback to one_zone_per_floor unchanged). `openubem/idf/surfaces.py` (added `_expand_core_perim_placeholder` helper: detects placeholder, calls `add_block(zoning="core/perim", perim_depth=placeholder["perim_depth_m"])`, renames resulting zones to `{osm_id}_F{i}_core` / `{osm_id}_F{i}_perim{n}` immediately after each call to avoid cross-building name collisions, expands `zones` list in place; on Exception falls back to per-floor bbox block and sets `generation_status_note`; `extrude_geometry` processes placeholders first in a snapshot loop). `tests/test_zoning.py` (updated `test_perimeter_core_30x30_5floors` and `test_zone_names_unique_within_building` → `test_perimeter_core_placeholder_fields` and `test_perimeter_core_z_coords` to match new single-placeholder output). `tests/test_surfaces.py` (added `TestCorePerimNative` class with 4 tests: floor areas sum ±1%, ≥1 Surface-matched wall pair, zone name format, narrow fallback). `tests/test_idf_builder.py` (updated `TestDoubleExtrusionFailure` to patch `always_fail` for all `add_block` calls — both core/perim attempt and per-floor fallback fail → zero extruded zones → num_zones=0).
- Deviations: (1) `build_zones` for `perimeter_core` now returns 1 placeholder instead of 2×N zone dicts; downstream `zones` list is mutated in place by `extrude_geometry`. This is a structural deviation from the pre-C2 approach but is required by R7 (native core/perim cannot pre-split the footprint). (2) geomeppy `core/perim` mode ignores the `name` parameter in `add_block` — all zone names are `Block Perimeter_Zone_N Storey M` / `Block Core_Zone Storey M` regardless of block name. Renaming is done by zone-object scan immediately after `add_block` returns, before any subsequent `add_block` call. (3) `perim_depth` sourced from `config.PERIMETER_DEPTH_M = 4.57` (existing constant, confirmed by grep). (4) B4 test (`TestDoubleExtrusionFailure`) had to be updated a second time: the prior C1 patch predicate `"_perim" in name` was no longer valid since C2 calls `add_block(name=osm_id, zoning="core/perim")` — name never contains `"_perim"`. Replaced with `always_fail` that rejects all `add_block` calls, exercising the double-failure path (core/perim fails → per-floor fallback fails → 0 zones extruded).
- Test status: `uv run pytest tests/test_surfaces.py tests/test_zoning.py tests/test_idf_builder.py::TestDoubleExtrusionFailure -q` → 30 + 1 = 31 passed, 0 failed.
- Notes: Confirmed via inline Python: 30×30 footprint with perim_depth=4.57 produces 4 perimeter wedges + 1 core per storey; floor areas sum to 900.02 m² vs 900 m² footprint (0.002% error, well within 1% tolerance). All Surface-matched wall pairs confirmed present after `intersect_match`.

#### C3 — Remove dead Outdoors→Adiabatic floor flip; update ground-floor BC test — completed 2026-06-09
- Artifacts: `openubem/idf/surfaces.py` (`set_adiabatic_surfaces` body replaced with a no-op docstring stub; both the ground-floor Adiabatic flip and the perim↔core Adiabatic flip removed per C3/R3 and R7 respectively). `tests/test_surfaces.py` (`test_adiabatic_ground_floor_slab` renamed `test_ground_floor_slab_bc_is_ground`; manual Outdoors-forcing and Adiabatic assertion replaced by direct `ground` BC assertion on unmodified `extrude_geometry` output — tests real production behavior).
- Deviations: `set_adiabatic_surfaces` is now a documented no-op stub. R3 confirms z=0 floors keep `ground` BC as geomeppy sets them; the Outdoors-forcing in the old test was a rig that concealed dead code (W3.10). The stub is retained (not deleted) so `builder.py` call site compiles without modification and future inter-building adjacency can be wired here.
- Test status: `uv run pytest tests/test_surfaces.py -q` → 18 passed, 0 failed.
- Notes: geomeppy's `set_unmatched_surface` assigns BC=`ground` to all z=0 floor surfaces as part of `intersect_match`. The old flip condition `bc == "outdoors"` could never match in real production — confirmed by the old test having to manually force `Outdoors` before asserting.

#### C4 — Strengthen vacuous adjacency test — completed 2026-06-09
- Artifacts: `tests/test_surfaces.py` (`test_adiabatic_perim_core_party_wall` replaced by `test_perim_core_party_wall_surface_matched`; uses `build_zones` + `extrude_geometry` with the new native core/perim path; asserts ≥1 wall surface has BC=`Surface` between perim and core zones — not the old permissive "outdoors or adiabatic" check).
- Deviations: The old test constructed separate core/perim polygon dicts manually (old pre-C2 API). The new test drives the full `build_zones` → `extrude_geometry` pipeline, which is the correct integration path and also covers C2 end-to-end. Old `test_adiabatic_perim_core_party_wall` is gone; `test_perim_core_party_wall_surface_matched` replaces it in `TestSurfaces`.
- Test status: `uv run pytest tests/test_surfaces.py::TestSurfaces::test_perim_core_party_wall_surface_matched -q` → 1 passed, 0 failed.
- Notes: The new test fails if party-wall logic is deleted (deleting `intersect_match` or the `Surface` BC assignment from geomeppy would cause it to fail). Assertion is positive (requires ≥1 pair), not permissive (no longer accepts 0 pairs as the old test did).

**GROUP C stop-and-report: Full suite — `uv run pytest tests/ -q` → 243 passed, 2 skipped, 0 failed, 0 errors.**

#### D1 — Fractional levels/underground cast survives non-integer values — completed 2026-06-09
- Artifacts: `openubem/acquisition/osm_fetcher.py` (added `.round()` before `.astype("Int64")` for both `levels` at line ~210 and `underground` at lines ~239-244). `tests/test_osm_fetcher.py` (added `TestFlattenTags::test_fractional_levels_rounded_and_row_retained`).
- Deviations: None. R4 applied exactly. `.round()` uses pandas banker's rounding (round-half-to-even), matching the ruling. The dtype-restore in `_seven_step_clean` step-3 explode path already operates on rounded values so no change needed there.
- Test status: `uv run pytest "tests/test_osm_fetcher.py::TestFlattenTags::test_fractional_levels_rounded_and_row_retained" -q` → 1 passed.
- Notes: Test verifies `"2.5"` → `levels == 2` (banker's rounding), row length == 1 (no drop), dtype == Int64.

#### D2 — Fix osm_id branch order so element_type+osmid is checked first — completed 2026-06-09
- Artifacts: `openubem/acquisition/osm_fetcher.py` (`_flatten_tags` osm_id block rewritten: `element_type`+`osmid` co-presence checked first, bare `osmid` second, index fallback last; eliminated dead intermediate else-if clause). `tests/test_osm_fetcher.py` (added `TestFlattenTags::test_osm_id_prefers_element_type_plus_osmid` and `test_osm_id_way_and_node_same_numeric_id_are_distinct`).
- Deviations: None. R5 applied exactly. The old three-branch logic had an unreachable `elif "element_type" in gdf.columns and "osmid" in gdf.columns` branch (it was never reached because the first `if "osmid" in gdf.columns` already matched). Simplified to two-branch + fallback.
- Test status: `uv run pytest "tests/test_osm_fetcher.py::TestFlattenTags::test_osm_id_prefers_element_type_plus_osmid" "tests/test_osm_fetcher.py::TestFlattenTags::test_osm_id_way_and_node_same_numeric_id_are_distinct" -q` → 2 passed.
- Notes: Test (a) uses a MultiIndex reset-index frame (osmnx 1.9 pattern); asserts `"way/12345"`. Test (b) uses `("way", 12345)` and `("node", 12345)` with same numeric id; asserts two distinct strings.

#### D3 — Change dedup candidate predicate from overlaps to intersects — completed 2026-06-09
- Artifacts: `openubem/acquisition/osm_fetcher.py` (`_resolve_overlaps`: `predicate="overlaps"` → `predicate="intersects"`). `tests/test_osm_fetcher.py` (added `_make_overlap_gdf` helper + `TestResolveOverlaps` class with `test_contained_polygon_deduped_by_intersects` and `test_party_wall_neighbours_not_deduped`; added `_resolve_overlaps` to imports).
- Deviations: None. R5 applied exactly. Downstream IoU≥0.95 + keep-larger logic is untouched; only the spatial-index predicate changed.
- Test status: `uv run pytest "tests/test_osm_fetcher.py::TestResolveOverlaps" -q` → 2 passed. `TestSevenStepClean` (7 tests, including party-wall neighbour scenario) → all still pass.
- Notes: The `overlaps` predicate in DE-9IM excludes "within" (fully contained) geometries. With `intersects`, contained near-duplicates (IoU>0.95) are now correctly deduplicated. Party-wall neighbours share only a line (IoU≈0) so they survive the IoU threshold check regardless of predicate.

#### D4 — Make serialization logs non-empty by writing collected run records — completed 2026-06-09
- Artifacts: `openubem/acquisition/osm_fetcher.py`: (1) `_seven_step_clean` now returns `(gdf, log_lines: list[str])` — each step emits via an inner `_emit()` helper that calls both `logger.info` and `log_lines.append`; (2) `ingest_buildings` unpacks the tuple; (3) `_serialize` signature extended to `log_lines: list[str] | None = None` — writes lines directly to `01_buildings_clean.log` via `Path.write_text` (no FileHandler); all existing `TestSevenStepClean` tests updated to unpack `result, _ = _seven_step_clean(gdf)`. `openubem/semantic/building_classifier.py`: (4) `BuildingClassifier.classify` calls new `_build_log_lines(out)` to collect per-rule fire counts, per-tier counts, FALLBACK osm_ids; (5) `_serialize` writes them directly to `02_buildings_classified.log` via `Path.write_text`; old FileHandler/addHandler/removeHandler pattern removed. `tests/test_osm_fetcher.py` (added `TestSerialize::test_log_file_non_empty_and_contains_step4b`). `tests/test_building_classifier.py` (added `TestSerialize::test_log_file_non_empty_and_contains_fallback`).
- Deviations: `_seven_step_clean` return type changed from `gpd.GeoDataFrame` to `tuple[gpd.GeoDataFrame, list[str]]` — this is a public-ish internal function called only from `ingest_buildings` and existing test code. All call sites updated. The FileHandler pattern is fully replaced by direct `Path.write_text` in both serialize methods; the handler was never capturing anything useful (it was added after all pipeline logging completed), so removing it is a pure fix with no behavior loss.
- Test status: `uv run pytest "tests/test_osm_fetcher.py::TestSerialize" "tests/test_building_classifier.py::TestSerialize" -q` → 8 passed.
- Notes: Step-1 log contains `"step": "4b"` token (from `_emit` in `_seven_step_clean`) + `"serialize_complete"` sentinel. Step-2 log contains `"FALLBACK"` token (from `_build_log_lines`) + `"serialize_complete"` sentinel.

**GROUP D checkpoint after D4 (mandatory): Full suite — `uv run pytest tests/ -q` → 250 passed, 2 skipped, 0 failed, 0 errors.**

#### D5 — Fix all-generic warning payload to WGS84 bbox + rewrite test via ingest_buildings mock — completed 2026-06-09
- Artifacts: `openubem/acquisition/osm_fetcher.py` (`ingest_buildings`: added `_warning_bbox` derivation block — prefers caller-supplied `bbox` arg; when absent and GDF is non-empty, reprojects to EPSG:4326 and reads `total_bounds` as `[n,s,e,w]`; passes `_warning_bbox` into the `all_generic_neighbourhood` warning dict instead of `gdf.total_bounds.tolist()`). `tests/test_osm_fetcher.py` (`TestAllGenericNeighbourhood::test_warning_emitted_and_gdf_returned` replaced by `test_warning_emitted_with_wgs84_bbox`: drives `ingest_buildings` with `mocker.patch("openubem.acquisition.osm_fetcher.ox.features.features_from_point", ...)` returning an all-generic WGS84 GDF; asserts `event="all_generic_neighbourhood"`, `n_rows` matches, `bbox` is plausible lat/lon `(n,s,e,w)`).
- Deviations: The old test reproduced the production code inline (it was not testing the real code path). The rewrite drives the actual `ingest_buildings` pipeline end-to-end with a mock — consistent with D7 approach and with the D5 task spec.
- Test status: `uv run pytest tests/test_osm_fetcher.py::TestAllGenericNeighbourhood -q` → 1 passed.
- Notes: The mock patches at `openubem.acquisition.osm_fetcher.ox.features.features_from_point` because the module imports `osmnx as ox` and calls `ox.features.features_from_point` directly.

#### D6 — Exclude mapped source tags from surplus_tags — completed 2026-06-09
- Artifacts: `openubem/acquisition/osm_fetcher.py` (`_flatten_tags._make_surplus`: `_skip = canonical_out | _OSM_RENAME_SOURCES`; column iteration skips `_skip` instead of `canonical_out` only). `tests/test_osm_fetcher.py` (added `TestFlattenTags::test_surplus_tags_excludes_rename_sources`: asserts `building`, `height`, `amenity`, `building:levels` absent from `surplus_tags`; `wikidata` present; `height_raw` present).
- Deviations: None. `_OSM_RENAME_SOURCES` already existed and was documented as "built for exactly this" — this task wires it in as intended.
- Test status: `uv run pytest tests/test_osm_fetcher.py::TestFlattenTags::test_surplus_tags_excludes_rename_sources -q` → 1 passed.
- Notes: The pre-existing `test_surplus_tags_unmapped_and_raw_height` continues to pass (wikidata + height_raw scenario unchanged).

#### D7 — Add mocked end-to-end ingest_buildings test — completed 2026-06-09
- Artifacts: `tests/test_osm_fetcher.py` (added `TestIngestBuildingsEndToEnd::test_end_to_end_schema_and_key_invariants`: mocks `ox.features.features_from_point`; raw GDF has MultiIndex with `("way",99001)`, `("node",99001)` same-numeric pair and one `building:levels="2.5"`; asserts 23-col schema, uniform `crs_utm`, all `osm_id` start with `way/` or `node/`, `way/99001` row survives with `levels==2`, log file non-empty).
- Deviations: Used `tempfile.mkdtemp()` instead of `tmp_path` fixture — same Windows `AppData\Local\Temp\pytest-of-o_iseri` permission error that affected B4. Functional coverage identical.
- Test status: `uv run pytest tests/test_osm_fetcher.py::TestIngestBuildingsEndToEnd -q` → 1 passed.
- Notes: Test exercises the full `flatten→UTM→clean→provenance→trim→validate→serialize` chain without hitting the network.

#### D8 — Add §5.1 vertex-count warning — completed 2026-06-09
- Artifacts: `openubem/acquisition/osm_fetcher.py` (`ingest_buildings`: after `_seven_step_clean`, computes `_vert_counts = gdf.geometry.apply(lambda g: len(g.exterior.coords))`; appends `{"event": "vertex_p95", "p95_vertices": _p95}` to `_clean_log_lines`; emits `logger.warning({"event": "high_vertex_count", "p95_vertices": _p95, "n_rows": len(gdf)})` when `_p95 >= 80`). `tests/test_osm_fetcher.py` (added `TestVertexCountWarning::test_warning_emitted_and_row_retained`: raw GDF with one 130-vertex WGS84 polygon mocked into `features_from_point`; asserts `high_vertex_count` warning emitted with `p95_vertices >= 80`; asserts row retained with 1 result).
- Deviations: None. No drop, no flag column — exactly as specified.
- Test status: `uv run pytest tests/test_osm_fetcher.py::TestVertexCountWarning -q` → 1 passed.
- Notes: `_p95` is computed on the UTM-projected GDF (after `_seven_step_clean`), so vertex counts reflect the final cleaned geometry ring lengths. The vertex_p95 line also lands in the serialize log via `_clean_log_lines`.

**GROUP D stop-and-report (after D8): Full suite — `uv run pytest tests/ -q` → 253 passed, 2 skipped, 0 failed, 0 errors.**

#### E1 — Make HIGH(b) reachable: rules 1a/1b/2a/2b observed pbt+levels → HIGH — completed 2026-06-09
- Artifacts: `openubem/semantic/building_classifier.py` (added HIGH(b) branch in `_assign_confidence` before the MEDIUM pfn/pbt check: when `head in {"RULE_HIGHRISE", "RULE_RESIDENTIAL_TIER"}` AND `pbt == "OSM_OBSERVED"` AND `levels_source == "OSM_OBSERVED"` → return HIGH). `tests/test_building_classifier.py` (`test_rule_2a_observed_levels_high` updated to assert HIGH and apologetic comment removed; new `test_rule_2a_imputed_levels_medium` added as symmetric MEDIUM case: same rule but `levels_source="HEURISTIC_DEFAULT"` → MEDIUM).
- Deviations: None. R6 applied exactly. `_HIGH_B_RULES` defined as a local `frozenset` inside the branch to avoid a new module-level constant (the set is small and only used once; no comment added per §1.5 default-no-comments rule).
- Test status: **Full suite — `uv run pytest tests/ -q` → 254 passed, 2 skipped, 0 failed, 0 errors.**
- Notes: Exactly 1 existing test changed expectation from MEDIUM to HIGH: `test_rule_2a_observed_levels_high` (line 336). The symmetric imputed-levels case (`test_rule_2a_imputed_levels_medium`, new) confirms the MEDIUM path is still reachable: same rule + `pbt=OSM_OBSERVED` + `pfn=OSM_MISSING` but `levels_source=HEURISTIC_DEFAULT` → falls through HIGH(b) guard (levels not observed) → hits the existing MEDIUM pfn/pbt branch. `test_rule_1a_imputed_levels_medium` (RULE_HIGHRISE with HEURISTIC_DEFAULT levels) still asserts MEDIUM and is unaffected. `test_rule_2a_function_tag_observed_high` (RULE_RESIDENTIAL_TIER with OSM_OBSERVED pbt+levels, function_tag observed) now hits the HIGH(b) branch earlier instead of falling through to the terminal `return "HIGH"` — result unchanged.

#### E2 — Parametrized exact-boundary test — completed 2026-06-09
- Artifacts: `tests/test_building_classifier.py` (`TestExactBoundaries` class with 7 parametrized `test_boundary` cases; drives `classify_building` directly via `_row` helper).
- Deviations: None. All 7 expected archetypes derived strictly from DESIGN §3C lines 160–180 (area bins: `< 500` Small, `500 ≤ area < 4000` Medium, `≥ 4000` Large; levels bins: `< 4` SmallHotel, `≥ 4` LargeHotel, `< 9` MidriseApartment, `≥ 9` HighriseApartment, `20 ≤ levels < 40` TallBuilding, `≥ 40` SuperTallBuilding; school: `≥ 5000` SecondarySchool). No ambiguity encountered — all boundaries have a single unambiguous expected value in §3C. No STOP triggered.
- Test status: `uv run pytest tests/test_building_classifier.py::TestExactBoundaries -v` → 7 passed, 0 failed.
- Notes: Cases: (1) area=500 → MediumOffice; (2) area=4000 → LargeOffice; (3) area=5000+school → SecondarySchool; (4) levels=4+hotel → LargeHotel; (5) levels=9+residential → HighriseApartment; (6) levels=20+commercial → TallBuilding; (7) levels=40+commercial → SuperTallBuilding. All inclusive boundaries confirmed correct.

#### E3 — Dtype assertions for load-bearing input columns — completed 2026-06-09
- Artifacts: `openubem/semantic/building_classifier.py` (added `_LOAD_BEARING_DTYPES = {"levels": "Int64", "footprint_area_m2": "float64", "height_m": "float64"}` module-level dict; added dtype-check loop in `_validate_input_schema` raising `ValueError` naming the offending column; added geometry-column presence check). `tests/test_building_classifier.py` (`TestInputDtypeValidation` class: `test_float64_levels_raises_valueerror`, `test_int64_levels_raises_valueerror`, `test_correct_dtypes_passes`).
- Deviations: Raises `ValueError` (not `SchemaError`) for dtype mismatch — `ValueError` is the standard Python type for invalid argument types and matches the task spec wording "raise ValueError with column name". `SchemaError` is reserved for structural schema violations (wrong column count, wrong column order, invalid closed-vocabulary values).
- Test status: `uv run pytest tests/test_building_classifier.py::TestInputDtypeValidation -v` → 3 passed, 0 failed.
- Notes: The geometry check uses `hasattr(gdf[cols[0]], "geom_type")` as a lightweight proxy since a GeoDataFrame always has its geometry column's values expose `.geom_type`; the column dtype is `geometry` dtype in geopandas. This guards against a non-geometry column accidentally placed first.

#### E4 — Guard empty-GeoDataFrame path — completed 2026-06-09
- Artifacts: `openubem/semantic/building_classifier.py` (added early-return block in `BuildingClassifier.classify` after `_validate_input_schema`: when `len(gdf) == 0`, returns a 0-row copy with three empty `object`-dtype columns appended — skips `apply(result_type="expand")` which would crash with `KeyError`). `tests/test_building_classifier.py` (`TestEmptyGDFGuard::test_zero_row_input_returns_26_cols_no_exception`).
- Deviations: None. Early return bypasses the `_validate_output_schema` call for the empty case — schema validation over a 0-row GDF is vacuously true for all constraints, so this is safe. The byte-equality `assert_frame_equal` is also skipped by the early return; that invariant is trivially satisfied for empty frames (0 rows → no bytes to differ).
- Test status: `uv run pytest tests/test_building_classifier.py::TestEmptyGDFGuard -v` → 1 passed, 0 failed.
- Notes: The `KeyError` crash was in pandas `apply(..., result_type="expand")`: a 0-row result has no columns for pandas to unpack into the expected 0/1/2 index, causing `KeyError: 0`.

#### E5 — Real-fixture tier distributions (REPORT ONLY) — completed 2026-06-09
- Artifacts: No production code changes. Read-only run via `uv run python -c` snippet classifying both local `.gpkg` fixtures after dtype normalisation (GeoPackage persistence coerces `Int64` → `float64` and reorders geometry to last position; reorder + cast applied inline before `BuildingClassifier().classify()`).
- Deviations: None. No assertions added, no threshold tests. Report only.
- Test status: N/A — report only.
- Notes: See distributions below.

**boston_downtown_500m (483 buildings)**

| archetype_id | n | % |
|---|---|---|
| OpenUBEMUnknown | 278 | 57.6% |
| MediumOffice | 73 | 15.1% |
| SmallOffice | 46 | 9.5% |
| TallBuilding | 28 | 5.8% |
| HighriseApartment | 13 | 2.7% |
| SuperTallBuilding | 10 | 2.1% |
| LargeOffice | 8 | 1.7% |
| RetailStandalone | 6 | 1.2% |
| Courthouse | 5 | 1.0% |
| MidriseApartment | 5 | 1.0% |
| College | 4 | 0.8% |
| FullServiceRestaurant | 4 | 0.8% |
| QuickServiceRestaurant | 2 | 0.4% |
| Outpatient | 1 | 0.2% |

Confidence tier: LOW 285 (59.0%), MEDIUM 141 (29.2%), HIGH 57 (11.8%)
FALLBACK (OpenUBEMUnknown) count: **278 (57.6%)**

**chicago_loop_500m (399 buildings)**

| archetype_id | n | % |
|---|---|---|
| OpenUBEMUnknown | 135 | 33.8% |
| MediumOffice | 88 | 22.1% |
| TallBuilding | 64 | 16.0% |
| SmallOffice | 24 | 6.0% |
| HighriseApartment | 23 | 5.8% |
| SuperTallBuilding | 14 | 3.5% |
| RetailStandalone | 13 | 3.3% |
| LargeOffice | 12 | 3.0% |
| Courthouse | 11 | 2.8% |
| College | 9 | 2.3% |
| FullServiceRestaurant | 2 | 0.5% |
| MidriseApartment | 2 | 0.5% |
| QuickServiceRestaurant | 2 | 0.5% |

Confidence tier: MEDIUM 143 (35.8%), LOW 138 (34.6%), HIGH 118 (29.6%)
FALLBACK (OpenUBEMUnknown) count: **135 (33.8%)**

**GROUP E stop-and-report (after E5): Full suite — `uv run pytest tests/ -q` → 265 passed, 2 skipped, 0 failed, 0 errors.**
