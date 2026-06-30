# PLAN — Classifier Coverage R3: untagged-building defaults + OQ-7 accuracy gate + Boston recalibration

- **Slug:** step-2-classifier-coverage-R3
- **Date:** 2026-06-11
- **Binding contracts:** `docs/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md` (read-only) as amended by the two user rulings of 2026-06-11 recorded in §5 below (DESIGN errata E-R3-1, E-R3-2 — the user is the spec owner and has ratified both in conversation). `docs/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md` §6 L2/L3 task text is incorporated by reference.
- **Goal:** (CP-α) classifier matches the user-ratified 50-label fixture at ≥70% fine / ≥90% coarse top-1, the OQ-7 accuracy gate is live in the suite, suite stays 0 skipped / 0 failed. (CP-β) Boston 483-building fleet re-run end-to-end with the improved classifier; CBECS gates recomputed and compared against the 2026-06-11 baseline (CV(RMSE) 53.78 / NMBE −10.81 / R² 0.731 / KS 0.190).

## §2 Hard rules for the executor

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never edit OVERVIEW/DESIGN docs, never edit root `main.py`, no `.py` under `docs/`.
2. Execute this plan top-to-bottom; no plan-writing, no alternatives. On spec ambiguity not covered by §5: STOP and quote the conflict.
3. No state-changing git commands. User's external tool handles git.
4. `%TEMP%\ubem_boston_c4*` and `%TEMP%\ubem_boston_r1*` are READ-ONLY. New fleet artifacts go to fresh `%TEMP%\ubem_boston_r3*` dirs.
5. Default to no comments; one short line max where the WHY is non-obvious.
6. Use the Bash tool with heredocs for inline Python (PowerShell 5.1 quoting is unreliable).
7. Do NOT relabel `tests/fixtures/labelled_archetypes_50.csv` — it is user-ratified ground truth (header `ratified=2026-06-11`). If the gate cannot be reached without touching the labels, STOP and report the residual mismatch table.
8. No live-network calls anywhere in this plan.

## §3 File layout to create / touch

```
openubem/semantic/building_classifier.py   (A01 size metric, A02 untagged rule)
tests/test_building_classifier.py          (A01/A02 test updates; A03 replaces TestLabelledTop1Accuracy stub)
tests/fixtures/README.md                   (A04 — new, orientation page per OQ-7 plan L3)
scripts/run_r3_fleet.py                    (B01 — new, full-chain Boston re-run, adapted from run_c4_regen.py + run_r1_t12.py)
docs/docs_step2/PLAN_step-2-classifier-coverage-R3.md   (this doc — §8 progress log only)
```

Other test files may ONLY be touched if the suite proves they assert the old rule-17 routing for untagged `building=yes` inputs (each such edit must be listed in the progress log with the assertion before/after). Tests that merely use `OpenUBEMUnknown` as a literal archetype id (schedules/zoning/idf-builder) must NOT change.

## §4 Dependency decisions (pre-decided — do not re-debate)

- No new packages.
- B01 fleet run: `n_jobs=6`, `SIM_TIMEOUT_S` stays 3600. Full 483-building re-simulation is REQUIRED this time (unlike R1's targeted merge) because the classifier change shifts the archetype — and therefore the physics — of roughly 60% of the fleet.
- The labelled fixture is the acceptance oracle; the manager has already measured the current classifier against it (§5 F4).

## §5 Source-of-truth verified facts (manager-grepped/measured 2026-06-11)

| # | Fact | Source |
|---|---|---|
| F1 | Rule 12a–c (`use_class=="commercial"` size buckets) at `building_classifier.py:258-264`; bucket metric is `area = footprint_area_m2` set at line 151; thresholds <500 / 500–4000 / ≥4000 | code grep |
| F2 | Rule 17 final fallback at `building_classifier.py:295-296` → `("OpenUBEMUnknown", "FALLBACK_UNKNOWN", None)`; output validator at lines 466-470 requires Unknown rows to carry `LOW` + `FALLBACK_UNKNOWN` | code grep |
| F3 | Confidence: `RULE_USE_CLASS_SIZE` → MEDIUM (line 334-335); `FALLBACK_UNKNOWN` → LOW (line 320) | code grep |
| F4 | **Measured baseline vs ratified fixture (50 rows): fine top-1 = 40.0%, coarse top-1 = 100.0%.** Mismatches: 17× expected office/retail → predicted Unknown (untagged `building=yes`); 9× expected LargeOffice → predicted MediumOffice (footprint vs total-floor-area bucketing); 1× MediumOffice→SmallOffice; 2× hotels→MediumOffice; 1× expected Unknown→Courthouse | manager measurement (classify gpkg fixtures, dtype-coerce levels/year_built/underground to Int64, geometry column first per `_INPUT_SCHEMA_COLUMNS`) |
| F5 | Gate thresholds (OQ-7 plan §5.3, DESIGN §5.1): coarse ≥90% (fail <80); fine ≥70% (fail <60); ≥10 distinct archetypes in `expected_archetype`. Fine accuracy over labelled rows only. Coarse map sealed: MidriseApartment+HighriseApartment → residential, all 28 others → commercial | OQ-7 plan §5.3, §5.5 |
| F6 | L2 deliverable spec (three test methods replacing the `TestLabelledTop1Accuracy` stub at `tests/test_building_classifier.py:854-861`) and L3 README spec | OQ-7 plan §6 L2/L3 |
| F7 | Labelled CSV must be read with `pd.read_csv(path, comment='#')`; header line carries provenance (`suggested-by=claude-opus-4-7, ratified=2026-06-11`) | OQ-7 plan + file |
| F8 | TallBuilding/SuperTallBuilding rules fire before office buckets for `use_class ∈ {commercial, institutional, mixed, unknown}` (lines 156-168) — untagged towers are already correct; do not disturb | code grep + F4 (5/5 correct) |
| F9 | CBECS baseline gate values (R2 plan Z08): CV(RMSE) 53.784 FAIL / NMBE −10.813 FAIL / R² 0.7312 PASS / KS 0.1902 FAIL; 465 gate-eligible buildings, OpenUBEMUnknown = 278/465 | R2 plan §8 Z08 |

### User rulings of 2026-06-11 (DESIGN errata — binding)

- **E-R3-1 — Office size buckets use TOTAL floor area** (`footprint_area_m2 × levels_imputed`), thresholds unchanged (<500 / 500–4000 / ≥4000 m²). Reconciles §3C rules 12a–c with §3B's literal wording "floor area" and with ASHRAE prototype definitions. User answer: "answer two: total floor area".
- **E-R3-2 — Untagged `building=yes` rows default to size-bucketed offices, not Unknown.** New rule 17a, evaluated after rules 1–16 and before rule 17: `use_class == "unknown" AND building_tag == "yes"` → Small/Medium/LargeOffice by E-R3-1 metric, confidence **LOW**, new `archetype_source` token **`FALLBACK_SIZE_DEFAULT`** (emit vocabulary 14→15; supersedes part of the OQ-5 resolution). Rule 17 (`OpenUBEMUnknown` + `FALLBACK_UNKNOWN` + LOW) remains for everything else (service/roof/canopy/garage tags, non-yes generic tags). User answer: "answer one, proceed with educated guess". Validator lines 466-470 unchanged (Unknown still requires FALLBACK_UNKNOWN).

## §6 Task list

### A01 — Office size buckets on total floor area (E-R3-1)
- **What:** in `building_classifier.py`, compute the rule-12a–c bucket metric as `footprint_area_m2 × levels_imputed` (the same imputed levels already used by the tall-building rules), replacing the bare footprint area.
- **Why:** E-R3-1; fixes 9–10 of the 30 fixture misses (F4).
- **How:** keep thresholds and rule tokens unchanged. Verify no other rule consumes the same `area` local for a different purpose (line 151 — if shared, introduce a separate `total_floor_area_m2` local rather than changing `area` semantics for tall-building checks, which DESIGN keys differently).
- **How to test:** existing rule-12 unit tests updated to the new metric (each updated assertion logged); a tall slim tower case (footprint 1,000 m², 10 levels) asserts LargeOffice.

### A02 — Rule 17a: untagged building=yes → size-bucketed office default (E-R3-2)
- **What:** insert rule 17a per E-R3-2 exactly; emit `FALLBACK_SIZE_DEFAULT`, confidence LOW; extend the `_EMIT` source-token set (F2 line 38 region) and the confidence mapper (LOW for the new token).
- **Why:** E-R3-2; fixes ~17 of the 30 fixture misses; directly attacks the Boston 60%-Unknown share driving the CBECS FAILs (F9).
- **How:** condition strictly `use_class == "unknown" and building_tag == "yes"`. Do not touch rules 1–16, the mixed-use routing, or the Unknown validator. Tests that assert untagged-yes→Unknown (the all-generic-neighbourhood contract and any rule-17 unit tests feeding `building=yes`) update to the new expectation: all-generic fixture now yields office-bucket archetypes with LOW confidence; the `all_fallback_archetype` warning condition updates accordingly (if the warning was keyed on Unknown share, key it on FALLBACK-source share — log the exact before/after in the progress log).
- **How to test:** unit: `building=yes`, 3 levels × 120 m² → SmallOffice/LOW/FALLBACK_SIZE_DEFAULT; `building=roof` → still OpenUBEMUnknown/FALLBACK_UNKNOWN. Then re-run the manager's fixture measurement (F4 method): report the new fine/coarse top-1 and full mismatch table in the progress log. Expected ≥80% fine; STOP at CP-α if <70%.

### A03 — L2: live accuracy gate (replaces the stub)
- **What:** implement OQ-7 plan §6 L2 verbatim (F6): replace `TestLabelledTop1Accuracy` stub with `test_coarse_top1` (≥90), `test_fine_top1` (≥70), `test_archetype_coverage_min10`, module-level `_COARSE_CLASS_MAP` per F5, CSV read per F7, classify the two gpkg fixtures with the F4 dtype/column-order handling.
- **Why:** OQ-7 closure — the suite now permanently measures classifier quality against expert labels.
- **How to test:** `pytest tests/test_building_classifier.py::TestLabelledTop1Accuracy -v` → 3 passed.

### A04 — L3: fixtures README
- **What:** `tests/fixtures/README.md` per OQ-7 plan §6 L3 (orientation: what each fixture is, how to regenerate, the labelled-CSV provenance line incl. `suggested-by=claude-opus-4-7, ratified=2026-06-11`).
- **How to test:** n/a (doc); listed in progress log.

### A05 — Full suite
- **What:** `python -m pytest -q -rs` default mode.
- **How to test:** acceptance **0 skipped / 0 failed**, ≥519 passed (516 baseline + 3 gate tests; net of any A01/A02 assertion updates). Report the summary line and wall time.

**— CP-α — STOP and report.** Include: new fixture accuracy numbers + mismatch table, every test assertion changed (before/after), suite summary.

### B01 — Boston full-chain re-run with the improved classifier
- **What:** `scripts/run_r3_fleet.py`: Steps 2→5 on `tests/fixtures/boston_downtown_500m.gpkg` (the full 483) — classify, enrich (2.1 climate may reuse cached EPW, 2.2 envelope/loads), Step-3 IDFs to `%TEMP%\ubem_boston_r3\step3`, Step-4 sims to `%TEMP%\ubem_boston_r3\sim` (`n_jobs=6`), Step-5 results to `%TEMP%\ubem_boston_r3_results`.
- **Why:** the archetype shift changes physics for ~60% of buildings; R1 results are invalid for the new classifier.
- **How:** adapt `scripts/run_c4_regen.py` + `scripts/run_r1_t12.py`. Before simulating, report the new archetype distribution vs old (especially the Unknown count, expected to drop from 278 to <30). Expect multi-hour wall time; the three big buildings take 11–24 min each.
- **How to test:** acceptance 483/483 success; all six live F12 gates PASS. STOP and report if any simulation fails (do not retry-loop).

### B02 — CBECS gates recomputed
- **What:** run `compute_validation_gates` on the new results with `inputs/reports/cbecs_2018_new_england_eui.csv`; report the four values + PASS/FAIL next to the F9 baseline.
- **Why:** this is the number the whole R3 exists to move.
- **How:** report-only per R2 ruling M-R2-4 — do NOT tune anything to chase thresholds.
- **How to test:** four finite floats; comparison table in the progress log.

**— CP-β — STOP and report.** Headline: archetype distribution shift, 483/483 status, F12 gates, CBECS before/after.

## §7 Stop-and-report checkpoints

CP-α after A05 (classifier + gate + suite). CP-β after B02 (fleet + CBECS). Two checkpoints only.

## §8 Progress log

(Executor appends one entry per completed task:)

```
#### AXX/BXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + DESIGN/E-R3 cite>
- Test status: <pytest summary>
- Notes: <auditor-relevant>
```

#### A01 — Office size buckets on total floor area (E-R3-1) — completed 2026-06-11
- Artifacts: `openubem/semantic/building_classifier.py` (lines 151-153: new `total_floor_area_m2` local; lines 259-264: rule 12 uses `total_floor_area_m2`)
- Deviations: Introduced separate `total_floor_area_m2 = area * max(levels_imputed, 1)` rather than reusing `area`, as required by §6 A01 "How" note (area is still needed footprint-based for school/datacenter rules at lines 204, 224-233). No change to thresholds (500/4000) or tokens.
- Test status: see A05
- Notes: Updated assertions in tests — `test_rule_12b_medium_office` (footprint=1000, levels=3 → total=3000 → MediumOffice — same result, assertion unchanged); added `test_rule_12c_tall_slim_tower` (footprint=1000, levels=10 → total=10000 → LargeOffice — new test per plan). ExactBoundaries parametrize tests still pass (area=500/4000 with levels=1 → total=500/4000, same boundary behavior).

#### A02 — Rule 17a: untagged building=yes → size-bucketed office default (E-R3-2) — completed 2026-06-11
- Artifacts: `openubem/semantic/building_classifier.py` (line 34 comment: 14→15 tokens; line 39: `FALLBACK_SIZE_DEFAULT` added to `_EMIT_TOKENS`; lines 295-302: rule 17a inserted; lines 320-321: `_assign_confidence` LOW branch extended to `FALLBACK_SIZE_DEFAULT`; lines 591-603: `all_fallback_archetype` warning rekeyed on FALLBACK-source share)
- Deviations: none — E-R3-2 implemented verbatim. `all_fallback_archetype` warning: was keyed on `(archetype_id == "OpenUBEMUnknown").all()`, now keyed on `archetype_source.str.startswith(("FALLBACK_UNKNOWN","FALLBACK_SIZE_DEFAULT")).all()` — per A02 "How" instruction to key on FALLBACK-source share after E-R3-2.
- Test status: see A05
- Notes: Fixture measurement after A01+A02: **fine top-1 = 92.0% (46/50), coarse top-1 = 100.0%**. Exceeds CP-α gate (≥80% fine / ≥90% coarse). Remaining 4 mismatches: (1) osm_id 816253624 `hotel` bt → use_class=commercial → LargeOffice (hotel bt not in lodging-tag set, pre-existing); (2) osm_id 816277587 `hotel` bt → MediumOffice (same); (3) osm_id 816270033 `yes` 1fl 495m² → SmallOffice (label says RetailStandalone — no retail tag, office default is correct per E-R3-2); (4) osm_id 145080938 `synagogue/place_of_worship` → Courthouse (synagogue maps to institutional → rule 14, pre-existing). None caused by A01/A02. Updated test assertions logged below: `TestApplyRuleTable.test_rule_17_openubem_unknown` → `test_rule_17a_building_yes_size_default` (was: OpenUBEMUnknown/FALLBACK_UNKNOWN; now: MediumOffice/FALLBACK_SIZE_DEFAULT); `TestClassifyBuildingRow.test_rule_17_openubem_unknown` → `test_rule_17a_building_yes_office_default` (same change at classify_building level); `TestArchetypeCoverage30._EXPECTED_DEFAULT` (removed OpenUBEMUnknown — row 24 now yields SmallOffice); row 24 comment updated; `TestAllFallbackNeighbourhood.test_all_unknown_warning` → `test_all_fallback_warning` (was: all OpenUBEMUnknown; now: all FALLBACK_SIZE_DEFAULT/LOW/office + warning still fires).

#### A03 — L2: live accuracy gate (replaces stub) — completed 2026-06-11
- Artifacts: `tests/test_building_classifier.py` (`_COARSE_CLASS_MAP` module-level dict; `_run_labelled_fixture()` helper; `TestLabelledTop1Accuracy` now has `test_coarse_top1`, `test_fine_top1`, `test_archetype_coverage_min10`; `_INPUT_SCHEMA_COLUMNS` added to imports)
- Deviations: none — OQ-7 plan §6 L2 implemented verbatim (F6, F7).
- Test status: see A05 (all 3 gate tests pass: coarse=100%, fine=92%, 14 distinct archetypes)
- Notes: `pytest tests/test_building_classifier.py::TestLabelledTop1Accuracy -v` → 3 passed.

#### A04 — L3: fixtures README — completed 2026-06-11
- Artifacts: `tests/fixtures/README.md` (new file)
- Deviations: none
- Test status: n/a (doc)
- Notes: Includes all required sections per OQ-7 plan §6 L3: file table, provenance line with `suggested-by=claude-opus-4-7, ratified=2026-06-11`, pd.read_csv comment note, accuracy gate thresholds.

#### A05 — Full suite — completed 2026-06-11
- Artifacts: none (test run only)
- Deviations: none
- Test status: **523 passed, 0 failed, 0 skipped** in 103.20s (1:43 wall time)
- Notes: Baseline was 516; net +7 = 523 (3 new gate tests A03, 2 new rule-12/17a tests A01/A02, 2 new confidence/fallback tests A02, 1 new fallback-non-yes test). Exceeds ≥519 acceptance threshold.

#### CP-α — manager ratification — 2026-06-11
- Audit: 5 log entries conformant; only §3-sanctioned files touched; all test-assertion changes are legitimate old-rule-17 routing updates, each logged before/after; 7 new tests.
- Fixture accuracy 92% fine / 100% coarse (gate floors 70/90) — the 4 residual misses are pre-existing tag-mapping limitations (hotel→commercial, synagogue→institutional, one tagless retail), not regressions; left for a future calibration pass.
- Suite 523 passed / 0 skipped / 0 failed. OQ-7 accuracy gate now live in the suite.
- Verdict: GREENLIGHT B01–B02 (full Boston re-run + CBECS recompute).
