# PLAN — Archetype classification threshold fix (DESIGN erratum E-R3-3)

> **Slug:** archetype-threshold-fix-E-R3-3
> **Date:** 2026-06-30
> **Binding contract:** DESIGN §3C (`docs/docs_main/docs_step2/DESIGN_...openstudio-archetyp.md`),
> as amended by the user-ratified erratum **E-R3-3** recorded in §4 below. DESIGN is read-only; the
> erratum mechanism is how the spec owner supersedes a DESIGN value (precedent: E-R3-1 / E-R3-2 in
> `docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md` §5).
> **Companion docs (same folder):** `BUG_archetype_classification_thresholds.md`,
> `INVESTIGATION_archetype_classification_thresholds.md`.
> **Source of corrected values:** `docs/docs_ACTIVE/input/deepResearch/RESULT_I02_archetype_classification_cascade.md`.

---

## 0. Progress checklist (live — manager-maintained monitoring surface)

> Ticked only after the manager audits the task against the actual code/tests. Each ✅ has a full entry in §8.

**Local arc — code · tests · docs (ends at CP-1):**
- [x] **T01** — Office size-tier helper + rules 12/17a (bins → `< 2322 / < 9290 m²`) — 2026-06-30
- [x] **T02** — Hotel tier threshold `≥ 5` levels (rules 3a/3b) — 2026-06-30
- [x] **T03** — School tier level-count rule, Option B (Primary = 1 story / Secondary ≥ 2) — 2026-06-30
- [x] **T04** — `default_size_signature` display strings (cosmetic) — 2026-06-30
- [x] **T05** — Resize synthetic coverage-fixture rows 1 / 2 / 15 — 2026-06-30
- [x] **T06** — Update existing unit/boundary assertions to new thresholds — 2026-06-30
- [x] **T07** — DOE-prototype self-classification regression tests — 2026-06-30
- [x] **T08** — Full local suite + CP-α accuracy gate  ⟶ **CHECKPOINT 1 — CP-1 MET (coarse 100% / fine 92%)** — 2026-06-30
- [x] **T09** — Record erratum + checklist + progress log — 2026-06-30

**D3 blind-spot follow-up (post-CP-1, local test-only):**
- [x] **T12** — School-levels + missing-`levels` regression lock (Primary = 1 / Secondary ≥ 2 / missing → Primary) — 2026-07-01

**Cluster arc — stops at your decision points:**
- [x] **T10** — CP-β: Boston 483-building CBECS fleet re-run — **CP-2 ACCEPTED 2026-07-01**; fix ratified (483/483 clean; drift investigated + cleared) — 2026-07-01
- [ ] **T11** — Full Phase-E 8,160-bldg re-run (E-R3-3) — **GREENLIT + DISPATCHED 2026-07-01** (user un-parked at "go go go"); frozen-geometry re-classify → `sbatch` → harvest to `phaseE_er33`; Sonnet sims, manager does CP-3 validation compare  ⟶ **CHECKPOINT 3 (report to user)**

---

## 1. Goal

Correct the three classification cut-points that misclassify their own DOE/PNNL prototype buildings,
following the user's two ratified decisions (2026-06-30):

- **School tier → Option B (level count):** Primary = 1 story, Secondary = 2+ stories.
- **Re-validation → two-tier:** quick check first (CP-α local accuracy gate), then the Boston CBECS
  fleet (CP-β); the full Phase-E fleet re-run happens **only if** CP-α/CP-β confirm.

The fix swaps one set of *published-source* literals for another (LBNL CBES / DOE prototype counts). It
introduces **no fitted parameters** and keeps archetype selection vintage-blind — the zero-fitted-params
invariant (DESIGN §3C line 352) is preserved.

---

## 2. Hard rules for the executor (Sonnet)

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** No work outside the repo.
2. **Do not write or revise this plan.** Manager owns the plan; you execute it top-to-bottom and append
   progress-log entries to §8 only.
3. **No scope creep.** Touch *only* the files named in §3. Do **not** change the data-center `500`
   (`building_classifier.py:227,234`), the zoning `500` (`geometry/zoning.py:32`), the occupant-density
   `500` (`semantic/__init__.py:76`), or any `*_levels_threshold` constructor parameter.
4. **No literal-level find/replace.** Edit each rule by line/identity, never by blanket-replacing a
   number that appears in multiple rules (see §3.D of the investigation).
5. **Stop-and-ask on spec ambiguity** — quote the conflict; never invent.
6. **Default to no comments.** One short line only where the WHY is non-obvious (e.g. the E-R3-3 marker).
7. **Cluster discipline (T10/T11 only):** never run EnergyPlus / Python compute on the Speed login node.
   All fleet compute goes through `sbatch --array` fire-and-forget; read the output file afterward.
   These tasks are dispatched as a **separate Sonnet cluster employee**, not run inline.
8. **Stop at the checkpoint after your assigned range**, append progress-log entries, report, and wait.

---

## 3. File layout to touch (exhaustive — nothing else)

```
openubem/
  semantic/building_classifier.py      ← T01 (office helper + rule 12/17a), T02 (hotel), T03 (school)
  data/openstudio_archetypes.json      ← T04 (default_size_signature strings; cosmetic)
tests/
  test_building_classifier.py          ← T05 (synthetic fixture rows), T06 (existing assertions), T07 (new regression tests)
docs/
  docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md   ← T09 (append E-R3-3 cross-ref to §5)
  docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md   ← §8 progress log (this file)
  PROJECT_CHECKLIST.md                 ← T09 (tick the sub-arc)
```

No new production files. No `.py` under `docs/`. The DESIGN §3C-intended `archetype_size_rules.json`
data table is **not** created here (out of scope — see investigation §3.H).

---

## 4. Dependency decisions (pre-decided — do not re-debate)

### Binding erratum text — record verbatim

> **E-R3-3 — Archetype size/level cut-points corrected to DOE/PNNL prototype self-classification.**
> Ratified by the spec owner 2026-06-30. Supersedes the DESIGN §3C literals `500`/`4000` (office),
> `5000` (school footprint), and `≥4` (hotel levels). Source: `RESULT_I02_archetype_classification_cascade.md`.
> - **Office (rules 12a–c and 17a):** total-floor-area bins change from `<500 / <4000` to
>   **`<2322 / <9290 m²`** (LBNL CBES 25,000 / 100,000 ft² bins; Hong et al. 2015). Metric unchanged
>   (total floor area = footprint × imputed levels, per E-R3-1).
> - **School (rules 6b/6c):** discriminator changes from footprint `≥5000 m²` to **level count** —
>   Primary = 1 story, Secondary = ≥2 stories (Deru et al. 2011: Primary 1-story / Secondary 2-story).
>   Resolves DESIGN §3C **OQ-4** (the 5,000 m² value was flagged as a guess).
> - **Hotel (rules 3a/3b):** Large/Small boundary changes from `≥4` to **`≥5` levels** (Deru et al.
>   2011: SmallHotel 4-story / LargeHotel 6-story).
> - No fitted parameters; vintage-blind selection unchanged.

### Pinned implementation choices

- **D1 — Office literals become named module constants + a shared helper.** Add
  `_OFFICE_SMALL_MAX_M2 = 2322.0`, `_OFFICE_MEDIUM_MAX_M2 = 9290.0` and a helper
  `_office_size_tier(total_floor_area_m2) -> str` returning `"SmallOffice"|"MediumOffice"|"LargeOffice"`.
  Both rule 12 and rule 17a call it, so the two sites can never drift again (the bug report's chief
  duplication concern). The helper returns only the archetype id; each caller pairs it with its own
  token (`RULE_USE_CLASS_SIZE` vs `FALLBACK_SIZE_DEFAULT`).
- **D2 — Hotel and school thresholds also become named constants:**
  `_HOTEL_LARGE_MIN_LEVELS = 5`, `_SECONDARY_SCHOOL_MIN_LEVELS = 2`. Not exposed as constructor params
  (that would be scope creep).
- **D3 — School confidence semantics are NOT changed in this fix.** The school rule now reads
  `levels_imputed`, but the rules are **not** added to `_LEVELS_CONSUMING`, because the head token
  `RULE_FUNCTION_TAG_SIZE` is **shared with data-center rules 9a/9b** (which do not consume levels) — a
  token-keyed downgrade would wrongly hit data centers. Consequence: a school classified on *imputed*
  levels keeps its current confidence tier and carries no `HEURISTIC_*` marker. This is a **deliberate,
  recorded limitation → OQ-school-levels-confidence** (follow-up, not this fix). The CP-α gate (T08)
  is where any real harm from missing-levels schools will surface.
- **D4 — Kindergarten stays Primary at any level count.** Rule 6c drops its area condition and becomes
  the catch-all for any remaining `school`/`kindergarten` tag; rule 6b (Secondary) matches only the
  `school` tag with `levels ≥ 2`. This preserves "kindergarten ⇒ Primary" and routes 1-story schools to
  Primary (see §5 fact F5 for the exact ordering proof).
- **D5 — Erratum home = E-R3-3 entry appended to R3 PLAN §5** (mirrors E-R3-1/E-R3-2), **not** a new
  `openubem/data/PROVENANCE.md`. This plan's §4 is the authored text; T09 adds the cross-reference line.
- **D6 — Validation order is CP-α → CP-β → (conditional) Phase-E.** Do not start CP-β until CP-α is
  green and reported; do not start Phase-E until the user greenlights after CP-β.

---

## 5. Source-of-truth verified facts (manager-grepped — cite these, don't re-derive)

| # | Fact | Location |
|---|---|---|
| F1 | Office rule 12a–c at `building_classifier.py:261–266`; fallback 17a at `:298–303`; both use `total_floor_area_m2` set at `:153` (= `area × max(levels_imputed,1)`). | code |
| F2 | Hotel rules 3a/3b at `:178,182` (`levels_imputed >= 4` / `< 4`). | code |
| F3 | School rules 6b/6c at `:206,210`; `area` = `footprint_area_m2` (`:151`); `levels_imputed` is the 2nd positional arg (`:133`). 6b token = `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED`; 6c = `RULE_FUNCTION_TAG`. | code |
| F4 | `_LEVELS_CONSUMING` = {RULE_HIGHRISE, RULE_RESIDENTIAL_TIER, RULE_LODGING_TIER} (`:54–56`). Token `RULE_FUNCTION_TAG_SIZE` is emitted by **both** school 6b and data-center 9a/9b — cannot be reused to gate school confidence (basis for D3). | code |
| F5 | Rule-order proof (Option B): 6b checked before 6c, adjacent, nothing between. school+≥2lv→6b Secondary; school+1lv→6b skip→6c Primary; kindergarten(any lv)→6b skip (not "school" tag)→6c Primary. ✓ | code `:205–211` |
| F6 | TallBuilding/SuperTall (rules 1a/1b, `:156–167`) fire **before** office buckets for commercial/institutional/mixed/unknown — untagged towers unaffected by the office change. | R3 PLAN F8 |
| F7 | `default_size_signature` is read by **no code** (display-only); office lines 8/23/38 + Detailed variants 15/30/45; hotel 88/95; school 130/137. | grep |
| F8 | Synthetic coverage fixture is **inline** in `test_building_classifier.py:801–859`. Under new thresholds: **row 1** (MediumOffice, footprint 800→total 800) becomes Small — BREAKS; **row 2** (LargeOffice, footprint 5000→total 5000) becomes Medium — BREAKS; **row 15** (SecondarySchool, footprint 6000, levels NA→1) becomes Primary — BREAKS. **Row 9** (LargeHotel, levels=5) survives. | code |
| F9 | CP-α gate is live: `TestLabelledTop1Accuracy` (`:1020–1040`) — `test_coarse_top1` ≥0.90, `test_fine_top1` ≥0.70, plus distinct-archetype count; fixture `tests/fixtures/labelled_archetypes_50.csv`; coarse map `_COARSE_CLASS_MAP` (`:981`). | code |
| F10 | CP-β anchor (E-R3-1/2 Boston baseline, 2026-06-11): CV(RMSE) 53.78 / NMBE −10.81 / R² 0.731 / KS 0.190; 465 gate-eligible. R3 fleet runners under `scripts/run_r3_*.py` + `scripts/cluster/`. | R3 PLAN lines 6, 49 |
| F11 | DOE/PNNL prototype sizes for regression tests: SmallOffice 511 m²/1-story; MediumOffice 4,982 m²/3-story; LargeOffice 46,320 m²/12-story; PrimarySchool 6,871 m²/1-story; SecondarySchool 2-story; SmallHotel 4-story; LargeHotel 6-story. | RESULT_I02 Table 1 |

---

## 6. Task list

### T01 — Office size-tier helper + rules 12/17a (E-R3-3)
- **What:** Add module constants `_OFFICE_SMALL_MAX_M2 = 2322.0`, `_OFFICE_MEDIUM_MAX_M2 = 9290.0` and
  helper `_office_size_tier(total_floor_area_m2) -> str`. Rewrite rule 12 (`:261–266`) and rule 17a
  (`:298–303`) to call the helper, each keeping its own token.
- **Why:** E-R3-3 office bins; D1 eliminates the rule-12/17a duplication (bug report's main concern).
- **How:** Helper returns `"SmallOffice"` if `< _OFFICE_SMALL_MAX_M2`, `"MediumOffice"` if
  `< _OFFICE_MEDIUM_MAX_M2`, else `"LargeOffice"`. Rule 12: `return _office_size_tier(total_floor_area_m2),
  "RULE_USE_CLASS_SIZE", None`. Rule 17a: `return _office_size_tier(total_floor_area_m2),
  "FALLBACK_SIZE_DEFAULT", None`. Do not change the metric (`:153`) or any token. One `# E-R3-3` marker.
- **How to test:** covered by T06 (updated boundary/unit) + T07 (DOE-prototype regression).

### T02 — Hotel tier threshold ≥5 (rules 3a/3b)
- **What:** Replace the `4` in rules 3a/3b (`:178,182`) with constant `_HOTEL_LARGE_MIN_LEVELS = 5`.
- **Why:** E-R3-3 hotel boundary (SmallHotel 4-story / LargeHotel 6-story, RESULT_I02 §Part C #3).
- **How:** `levels_imputed >= _HOTEL_LARGE_MIN_LEVELS` → LargeHotel; `< _HOTEL_LARGE_MIN_LEVELS` →
  SmallHotel. Tokens unchanged.
- **How to test:** covered by T06 (boundary row, levels=4 → SmallHotel) + T07 (4-story→Small, 6-story→Large).

### T03 — School tier level-count rule, Option B (rules 6b/6c)
- **What:** Rewrite rule 6b to fire on `(ft == "school" or bt == "school") and levels_imputed >=
  _SECONDARY_SCHOOL_MIN_LEVELS` (=2). Rewrite rule 6c to the unconditional catch-all
  `ft in {"school","kindergarten"} or bt in {"school","kindergarten"}` → PrimarySchool (drop the
  `area < 5000` clause).
- **Why:** E-R3-3 school discriminator (user Decision B); D4 preserves kindergarten⇒Primary and
  1-story-school⇒Primary; F5 proves the ordering.
- **How:** Add constant `_SECONDARY_SCHOOL_MIN_LEVELS = 2`. Keep 6b's composite token
  `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED` and 6c's `RULE_FUNCTION_TAG` (per D3, no
  token-vocabulary change). Do **not** add school rules to `_LEVELS_CONSUMING`.
- **How to test:** covered by T06 + T07 (1-story school→Primary, 2-story school→Secondary, kindergarten
  2-story→Primary).

### T04 — Update `default_size_signature` strings (cosmetic)
- **What:** Edit the display strings in `openstudio_archetypes.json`: office (lines 8/23/38) **and the
  Detailed variants (15/30/45)** to the new total-floor-area bins; hotel (88/95) to `< 5` / `>= 5
  floors`; PrimarySchool (130) to "OSM school (1 story) or kindergarten (any)"; SecondarySchool (137) to
  "OSM school + ≥2 stories (ASSUMPTION_DOE_PROTOTYPE_DERIVED; E-R3-3 resolves OQ-4)".
- **Why:** F7 — no code reads this field, but a stale string would lie to the next reader.
- **How:** String edits only; keep JSON valid (run `python -c "import json,..."` parse check).
- **How to test:** `json.loads` succeeds; visual diff matches the new thresholds.

### T05 — Resize synthetic coverage fixture rows (F8)
- **What:** In the inline `synthetic_30_gdf` fixture (`:814–850`): **row 1** footprint `800.0 → 3000.0`
  (MediumOffice); **row 2** footprint `5000.0 → 10000.0` (LargeOffice); **row 15** add `levels=2`
  + `provenance_levels="OSM_OBSERVED"` (SecondarySchool via 6b). Update the trailing comments on rows
  8/9/14/15 to the new rule wording.
- **Why:** Without this, `test_default_mode_coverage` fails — MediumOffice/LargeOffice/SecondarySchool
  would no longer be produced by any row.
- **How:** Edit only those rows; leave all other rows untouched. Row 0 (Small, 200), row 24 (17a Small,
  total 400), row 9 (LargeHotel, levels 5) already satisfy the new thresholds — do not change.
- **How to test:** `TestArchetypeCoverage30::test_default_mode_coverage` green; the regenerated
  `synthetic_30_archetype_coverage.gpkg` contains all default-reachable archetypes.

### T06 — Update existing unit/boundary assertions to new thresholds
- **What:** Flip the assertions that encode the old cut-points:
  - `TestExactBoundaries` `:915` total=500 → **SmallOffice**; `:917` total=4000 → **MediumOffice**;
    `:923` hotel levels=4 → **SmallHotel**; `:919` school row → replace with the new level rule (school
    levels=1 → PrimarySchool **and** add school levels=2 → SecondarySchool).
  - `test_rule_17a_building_yes_size_default` `:268` total=1600 → **SmallOffice**;
    `test_rule_17a_building_yes_office_default` `:515` total=1600 → **SmallOffice**.
  - `test_rule_6b_composite_token` `:252` (levels=2) and `test_rule_6c_primary_school` `:258` survive —
    confirm, annotate comments.
  - `test_rule_6b_secondary_school` `:527` — fixture is Primary-sized (6000 m²/1-story); add `levels=2`
    so it is genuinely Secondary, keep the Secondary assertion + composite token.
  - `test_rule_12b_medium_office` `:316` (total 3000→Medium) and `test_rule_12c_tall_slim_tower` `:322`
    (total 10000→Large) survive — confirm, update comments to new bins.
- **Why:** these assertions were written to match the *old* (wrong) thresholds; left as-is they either
  fail or silently test the wrong thing.
- **How:** Update assertion + the `# DESIGN §3C…` comment on each to cite **E-R3-3**. Log each changed
  line in the progress entry.
- **How to test:** the named tests pass.

### T07 — Add DOE-prototype regression tests (the direct test for this bug)
- **What:** New tests asserting each prototype lands in its own archetype (F11): SmallOffice 511 m²/
  1-story; MediumOffice 4,982 m²/3-story (footprint ≈1,660 × 3); LargeOffice 46,320 m²/12-story;
  PrimarySchool 6,871 m²/1-story; SecondarySchool school+2-story; SmallHotel hotel/4-story; LargeHotel
  hotel/6-story.
- **Why:** locks the bug shut — these must never silently regress again (bug report §2 final paragraph).
- **How:** new test class `TestDoePrototypeSelfClassification`; build rows via `_row(...)`, call
  `classify_building` (so imputation runs) or `_apply_rule_table` with explicit levels; assert the
  archetype id. Office uses total-floor-area = footprint × levels — set footprint/levels accordingly.
- **How to test:** the new tests pass.

### T08 — Full local suite + CP-α accuracy gate  ⟶ **CHECKPOINT 1**
- **What:** Run the entire `pytest` suite. Triage failures: classifier-threshold-driven reclassifications
  in other fixtures (step3/step21/step22/sim integration) are expected and fixed in place; **any failure
  not explained by a threshold reclassification is a real regression — STOP and report.** Then run
  `TestLabelledTop1Accuracy` (CP-α) and record coarse/fine accuracy vs the ≥0.90 / ≥0.70 gates.
- **Why:** CP-α is the cheap, user-ratified accuracy gate E-R3-1/2 had to clear (F9, D6). It is also
  where the missing-levels-school risk (D3) surfaces.
- **How:** `pytest -q` then `pytest -q tests/test_building_classifier.py::TestLabelledTop1Accuracy -rs`.
  If fine or coarse drops **below** gate: do **not** edit `labelled_archetypes_50.csv` (changing ground-
  truth labels needs user sign-off) — STOP, report the per-row misses (especially schools), and surface
  the contingency (hybrid school rule: Secondary if `levels≥2` OR `levels missing AND footprint≥8000`).
- **How to test:** suite 0 failed / 0 unexpected-skipped; CP-α coarse ≥0.90 and fine ≥0.70 (report exact %).

### T09 — Record erratum + checklist + progress log (docs)
- **What:** Append the **E-R3-3** one-line cross-reference to R3 PLAN §5 (pointing at this plan's §4 for
  full text); tick the misclassification sub-arc in `docs/PROJECT_CHECKLIST.md`; ensure every completed
  T0x has a §8 progress-log entry here.
- **Why:** D5 erratum home; project memory — §8 progress log is the binding record; checklist is the
  user's monitoring surface.
- **How:** Single appended bullet in R3 PLAN §5: `- **E-R3-3** — size/level cut-points corrected (office
  2322/9290 total m²; school level-count Primary=1/Secondary≥2; hotel ≥5 levels). Ratified 2026-06-30.
  Full text + plan: docs/docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md §4.`
- **How to test:** n/a (doc edit); manager audit.

### T10 — CP-β: Boston 483-building CBECS fleet re-run  ⟶ **CHECKPOINT 2 (report to user)**
- **What:** Re-run the R3 Boston fleet end-to-end with the corrected classifier; recompute the CBECS
  gates; compare to the latest committed R3 Boston gates report and the 2026-06-11 anchor (F10). Report
  before/after deltas (archetype distribution shift + CV(RMSE)/NMBE/R²/KS) to the user.
- **Why:** the office reclassification has a large, asymmetric blast radius (Medium→Small, Large→Medium)
  that can move the headline CBECS numbers (investigation §3.C); CP-β is the fleet-level confirmation.
- **How:** **Dispatched as a separate Sonnet cluster employee.** First read `scripts/cluster/README.md`
  + `scripts/run_r3_fleet.py` / `run_r3_step5.py` / `run_r3_gates_report.py` to determine the exact fleet
  invocation, then `sbatch --array` fire-and-forget (NO login-node compute), read the output, run the
  gates report. Do not start until T08 reported green.
- **How to test:** gates report produced for the corrected fleet; before/after table assembled; deltas
  reported. No silent acceptance — user decides whether to proceed to T11.

### T11 — Full Phase-E fleet re-run (8,160 bldg, E-R3-3)  ⟶ **CHECKPOINT 3 (report to user)**

> **GREENLIT by user 2026-07-01** ("un-park & run T11"). Fold the E-R3-3 classifier fix into the closed
> Phase-E baseline properly (not silently). **Separate Sonnet CLUSTER employee**, `sbatch` only, launched
> as a background job. Manager (Opus) authors this spec + does the CP-3 validation comparison; Sonnet runs
> the cluster sim + harvest.

- **What:** Re-run all 12 Phase-E cells (3 cities × 4 rings = 8,160 buildings) with the corrected
  classifier, **holding building geometry frozen** (re-classify + regen IDFs off the committed per-cell
  `01_buildings.gpkg`; NO OSM re-fetch), simulate on Speed, harvest to a **fresh** output tree, then
  (manager) compute before/after validation deltas vs the closed baseline.
- **Why:** Phase-E is the 🔒 ADOPTED BASELINE; E-R3-3 down-tiers an unknown share of the ~4,200 office
  buildings, so the fix must not be folded in silently (bug report step 6). Freezing geometry makes this a
  **clean classifier isolation** — the CP-2 lesson: a re-fetch would confound the fix with OSM drift.

**Verified mechanics (manager-grepped 2026-07-01 — cite, don't re-derive):**
| # | Fact | Location |
|---|---|---|
| M1 | One `python scripts/validation/v12_cell_pipeline.py <cell> --output-subdir <sub>` runs a whole cell end-to-end: EPW→step1(fetch/cache)→step2 classify(E-R3-3)→step3 IDF gen→live_smoke→ship→`sbatch --array=1-N%32`→`poll_cluster` (local 90 s squeue loop)→fetch→verify_and_repair→step5→copy final. | `v12_cell_pipeline.py:946-1077` |
| M2 | `step1_fetch` **loads `work_base/01_buildings.gpkg` from cache if present** (line 139-141) and only re-fetches OSM when absent. `work_base = %TEMP%/ubem_validation/<sub>/<cell>`. → **pre-seeding that file freezes geometry, no live OSM.** | `:137-150, :954` |
| M3 | `final_dir` and `remote_fleet_dir` are **both keyed by `--output-subdir`** (`final_dir=REPO/docs/validations/overAll/results/<sub>/<cell>`; `fleet_tag=<sub>_<cell>` → `/speed-scratch/o_iseri/fleets/<sub>_<cell>`). A fresh `<sub>` ⇒ fresh remote dir ⇒ `_remote_results_complete` (line 927) **can't short-circuit to stale baseline sims**, and the committed baseline is never touched. | `:958-961, :1007` |
| M4 | Committed `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` (×12) are the **raw pre-classification OSM fetch** (cols: osm_id, function_tag, levels, footprint_area_m2, provenance_*, geometry; **no** archetype_id) — the correct classifier input to seed. | disk-verified |
| M5 | Pipeline writes to `docs/validations/...` but that dir **does not exist** (renamed → `docs/docs_VALIDATION/validations/`). So a re-run creates a NEW top-level `docs/validations/overAll/results/phaseE_er33/` tree — throwaway, promote into `docs_VALIDATION` only after user accepts. | disk-verified |
| M6 | `OPENUBEM_RECONSTRUCT_SERVICE_LOADS` defaults to `"0"` (`config.py:81`) — Phase-E physics is the default; set it explicitly anyway for determinism. Do NOT edit pipeline code. | `config.py:81` |

**Execution recipe (Sonnet cluster employee):**
- **T11.1 — Pre-seed frozen geometry (all 12 cells).** For each `<cell>`, create
  `%TEMP%/ubem_validation/phaseE_er33/<cell>/` and copy the committed
  `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` into it as
  `01_buildings.gpkg`. Verify each seeded file's row count == the baseline cell's N (nyc_centre≈737,
  nyc_urban≈1779, nyc_suburban≈1589, nyc_rural≈198, la_centre≈225, la_urban≈617, la_suburban≈1343,
  la_rural≈142, austin_centre≈413, austin_urban≈425, austin_suburban≈437, austin_rural≈245). **If a
  seeded file is missing or row count is wildly off, STOP and report** (do not let step1 re-fetch OSM).
- **T11.2 — Run the 12 cells as ONE background loop.** `OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0`; for each
  cell `python scripts/validation/v12_cell_pipeline.py <cell> --output-subdir phaseE_er33`. Launch the
  whole loop as a **background** job (do NOT sit blocking — `poll_cluster` blocks each cell locally until
  its array drains; the loop is ~8 h). Tee each cell's stdout to a log. `sbatch --array %32`, job-name
  `openubem_<cell>`. **Never run E+/compute on the login node.**
- **T11.3 — Monitor ≥30 min / event-driven.** Prefer completion notification over polling; if polling,
  ≥30-min gaps. Watch for the per-cell `live_smoke_check` gate (gen ≥95%, Unknown <20%) and the
  ZERO-FAIL stop (line 1045). Do NOT touch non-`openubem_` cluster jobs.
- **T11.4 — Per-cell sanity as cells land.** Each cell auto-writes `v12_<cell>_gates_report.txt`
  (archetype mix + CBECS gates + headline EUI) to `docs/validations/.../phaseE_er33/<cell>/`. Confirm the
  **office down-tier** shows up (SmallOffice↑, Medium/LargeOffice↓) and sim success ≈ baseline N.
- **T11.5 — Report at CP-3.** When all 12 land: report per-cell archetype before/after (offices) + sim
  success counts + each cell's headline total EUI, and hand back the 12 `05_results.csv` paths. **STOP.**
  Do NOT run `phaseE_rescore.py` against the baseline (it hardcodes `phaseE`/`docs_VALIDATION` and would
  overwrite `REPORT_phaseE_final.md`) — the fleet-level before/after validation is the manager's step.

- **T11.6 (MANAGER / Opus — validation analysis):** compute city anchor deltas (median total EUI vs
  measured 219.2/113.6/162.0), CBECS gates (NMBE/R²/CV/KS per region), and archetype-mix shift for
  `phaseE_er33` vs the committed `phaseE` baseline; present the before/after table. **Baseline to beat/hold:**
  city Overall NYC −24.4% / LA −5.6% / Austin −25.7%; R² 0.895 / 0.924 / 0.718; CBECS NMBE −10.6 / −20.5 /
  −11.9%. Expected direction (per CP-2 isolation): office down-tier → mean EUI slightly lower → NMBE a touch
  more negative; R² ~flat-to-up; CV/KS ~flat-to-tighter. Zero-fitted-params + CBECS report-only ⇒ a correct
  classifier fix is not vetoed by CBECS movement.
- **T11.7 — User sign-off + promotion.** Only after the user accepts the deltas: promote `phaseE_er33` →
  the `phaseE` baseline (into `docs_VALIDATION`), regenerate the report/figures, and update Phase-E
  memory + `REPORT_phaseE_final.md`. Until then the committed baseline stays untouched.
- **How to test:** 12/12 cells simulated (≈8,160 success rows, drops within tolerance); per-cell office
  down-tier visible; before/after validation table assembled; user sign-off recorded before any baseline
  promotion.

### T12 — School-levels missing-default regression lock (D3 blind-spot closure)
- **What:** Add a synthetic school-levels classification unit test to `tests/test_building_classifier.py`
  that exercises the E-R3-3 school rule (Option B) **and the missing-`levels` default** — the one path
  that NEITHER accuracy gate covers (the CP-α 50-building fixture has zero schools, and the CP-β Boston
  483 fleet was confirmed 2026-07-01 to contain zero schools/hotels). Pure Python, no E+, no cluster.
- **Why:** rules 6b/6c (E-R3-3, resolving DESIGN §3C OQ-4) were verified only against the DOE prototype
  self-classification cases (T07); the D3 recorded limitation — *missing `levels` → imputed default →
  PrimarySchool* — has no regression lock and cannot be reached by either fleet gate. Without this test
  a future change to the level-imputation default would silently flip missing-levels schools with nothing
  to catch it. This test LOCKS the documented current behaviour; it does NOT re-open whether Primary is
  the *right* default (that stays the open OQ-school-levels-confidence follow-up).
- **How:** append a new parametrized class (e.g. `TestSchoolLevelsAndMissingDefault`) mirroring T07's
  `_row` idiom with `function_tag="school"`/`"kindergarten"`. Cases: school+1-story-observed → PrimarySchool;
  school+2-story → SecondarySchool; school+≥3-story → SecondarySchool; kindergarten+any-levels → PrimarySchool;
  **school with NO observed `levels` (omit `levels`/`provenance_levels` so the classifier imputes) →
  PrimarySchool (the D3 default).** For the missing-levels case, do NOT hard-code an assumed imputed value —
  read the actual imputation default from `building_classifier.py`, assert the resulting archetype, and add
  one comment citing the D3 limitation + line. Also assert the D3 token/confidence behaviour: PrimarySchool
  head token `RULE_FUNCTION_TAG`, SecondarySchool composite `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED`,
  and that an imputed-levels school is NOT confidence-downgraded (head token not in `_LEVELS_CONSUMING`, per T03/D3).
  If the actual missing-levels result is anything other than PrimarySchool, STOP and report (do not edit code —
  that would be a D3 contingency decision for the manager/user, not an executor call).
- **How to test:** `pytest tests/test_building_classifier.py -k "SchoolLevels"` all pass; re-run
  `pytest tests/test_building_classifier.py::TestLabelledTop1Accuracy -rs` and confirm coarse 100% / fine 92%
  is unchanged (the new test must not perturb the accuracy gate).

---

## 7. Stop-and-report checkpoints

- **CP-1 (after T08):** local suite green + CP-α accuracy at/above gate. This is the gate between "code
  done" and "spend cluster time." If CP-α regresses (likely culprit: missing-levels schools), STOP and
  bring the hybrid-school contingency to the user — do not proceed to T10.
- **CP-2 (after T10):** Boston CBECS before/after reported. User decides whether the office redistribution
  is acceptable and whether to run T11.
- **CP-3 (after T11):** Phase-E before/after reported; user sign-off before the baseline is updated.

Suggested hand-off ranges: **T01–T09** (all local work, ends at CP-1), then **T10** (CP-2), then **T11**
(CP-3) as separate cluster dispatches.

---

## 8. Progress log

_(Sonnet appends one entry per completed task, format below. Manager audits.)_

```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths/lines>
- Deviations: <none | rationale + DESIGN/erratum cite>
- Test status: <pytest summary>
- Notes: <auditor-relevant>
```

#### T01 — Office size-tier helper + rules 12/17a (E-R3-3) — completed 2026-06-30
- Artifacts: `openubem/semantic/building_classifier.py` — new constants `_OFFICE_SMALL_MAX_M2 = 2322.0` / `_OFFICE_MEDIUM_MAX_M2 = 9290.0` (:131–132) + helper `_office_size_tier()` (:135–140); rule 12 rewritten to `return _office_size_tier(total_floor_area_m2), "RULE_USE_CLASS_SIZE", None` (:275); rule 17a rewritten to `return _office_size_tier(total_floor_area_m2), "FALLBACK_SIZE_DEFAULT", None` (:308). One `# E-R3-3` marker on the constants block.
- Deviations: none. Metric line (:166, `total_floor_area_m2 = area * max(levels_imputed,1)`) and all tokens unchanged per D1. Protected sites confirmed untouched: data-center `500` (:240,247), zoning `500`, occupant-density `500`, all `*_levels_threshold` constructor params.
- Test status: import/parse sanity OK; `_office_size_tier` returns Small/Medium/Large at 2000/5000/10000 m². Full suite deferred to T08.
- Notes: rule-12/17a office duplication eliminated — both call the single helper, so the two sites can never drift again (D1; bug report's chief concern). Manager-audited against the file (grep-confirmed line numbers).

#### T02 — Hotel tier threshold ≥5 (rules 3a/3b) — completed 2026-06-30
- Artifacts: `openubem/semantic/building_classifier.py` — new constant `_HOTEL_LARGE_MIN_LEVELS = 5` (:135, with `# E-R3-3` marker); rule 3a `levels_imputed >= 4` → `>= _HOTEL_LARGE_MIN_LEVELS` (:194, LargeHotel); rule 3b `levels_imputed < 4` → `< _HOTEL_LARGE_MIN_LEVELS` (:198, SmallHotel).
- Deviations: none. Tokens (`RULE_LODGING_TIER`) unchanged. No other `4`/`<4` literal existed to catch; data-center `500` (:250) and school `5000` (:222, T03 scope) left untouched.
- Test status: import/parse OK; `_HOTEL_LARGE_MIN_LEVELS == 5`. Full suite deferred to T08.
- Notes: SmallHotel now covers 4-story (levels=4 → Small, matching DOE SmallHotel 4-story); LargeHotel now ≥5 (DOE LargeHotel 6-story). `RULE_LODGING_TIER` remains in `_LEVELS_CONSUMING`, so imputed-levels confidence downgrade is unchanged. Manager-audited via grep.

#### T03 — School tier level-count rule, Option B (rules 6b/6c) — completed 2026-06-30
- Artifacts: `openubem/semantic/building_classifier.py` — new constant `_SECONDARY_SCHOOL_MIN_LEVELS = 2` (:138, `# E-R3-3` marker); rule 6b condition `area >= 5000` → `levels_imputed >= _SECONDARY_SCHOOL_MIN_LEVELS` (:225, SecondarySchool; composite token `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED` preserved byte-for-byte); rule 6c made unconditional catch-all — dropped `and area < 5000` (:229, PrimarySchool, token `RULE_FUNCTION_TAG`).
- Deviations: none. 6b remains immediately before 6c (adjacent; F5 ordering preserved). `_LEVELS_CONSUMING` (:54–56) NOT modified per D3 (school head token `RULE_FUNCTION_TAG_SIZE` is shared with data-center rules 9a/9b). `area` no longer appears in either school rule; still assigned (:170) for office/data-center rules.
- Test status: import/parse OK; live `_apply_rule_table` smoke — school+2lv → SecondarySchool, school+1lv → PrimarySchool, kindergarten+3lv → PrimarySchool. Full suite deferred to T08.
- Notes: Resolves DESIGN §3C OQ-4 (the 5,000 m² footprint guess is retired). Deliberate recorded limitation → OQ-school-levels-confidence: schools tiered on *imputed* levels keep their current confidence tier and carry no level-source token (D3); to be watched at CP-α (T08). Manager-audited via read + grep.

#### T04 — Update `default_size_signature` display strings (cosmetic) — completed 2026-06-30
- Artifacts: `openubem/data/openstudio_archetypes.json` — 10 `default_size_signature` values updated: SmallOffice + Detailed (:8,15) → `"< 2322 m² total floor area"`; MediumOffice + Detailed (:23,30) → `"2322 to < 9290 m² total floor area"`; LargeOffice + Detailed (:38,45) → `">= 9290 m² total floor area"`; SmallHotel (:88) → `"< 5 floors"`; LargeHotel (:95) → `">= 5 floors"`; PrimarySchool (:130) → `"OSM school (1 story) or kindergarten (any)"`; SecondarySchool (:137) → `"OSM school + >= 2 stories (ASSUMPTION_DOE_PROTOTYPE_DERIVED; E-R3-3 resolves OQ-4)"`.
- Deviations: minor — the Detailed office variants' signature dropped the "modeller opts in via detailed_office=True" qualifier; that information is preserved in each Detailed archetype's `notes` field, and the field is display-only. Data-center signatures (footprint 500 m² split — real DC logic) left unchanged (out of scope).
- Test status: `json.load` parse check → JSON OK.
- Notes: F7 — `default_size_signature` is read by no code (display-only); update prevents a stale string from lying to the next reader. Manager-audited via grep.

#### T05 — Resize synthetic coverage fixture rows (F8) — completed 2026-06-30
- Artifacts: `tests/test_building_classifier.py` `synthetic_30_gdf` — row 1 footprint `800 → 3000` (total 3000 → MediumOffice); row 2 footprint `5000 → 10000` (total 10000 → LargeOffice); row 15 levels `NA → 2` + `provenance_levels="OSM_OBSERVED"` (→ SecondarySchool via rule 6b). Trailing comments refreshed on rows 8 (SmallHotel levels<5), 9 (LargeHotel levels>=5 — data untouched), 14 (PrimarySchool 1-story imputed), 15 (SecondarySchool levels>=2).
- Deviations: none. `_r(i, ft, bt, levels, area, **kw)`; row 15 used the existing `provenance_levels` kwarg pattern (already present on rows 8/9/10/11/22/23/24). Rows 0 and 24, and row 9's data values, left untouched (already satisfy the new thresholds).
- Test status: `TestArchetypeCoverage30::test_default_mode_coverage` → 1 passed.
- Notes: restores MediumOffice / LargeOffice / SecondarySchool coverage in the default-mode fixture (without this, those three archetypes are no longer produced by any row). Manager-audited via grep.

#### T06 — Update existing unit/boundary assertions to new thresholds — completed 2026-06-30
- Artifacts: `tests/test_building_classifier.py`:
  - `TestExactBoundaries` parametrize table (:919–941): office total=500 → SmallOffice; office total=4000 → MediumOffice; school levels=1 → PrimarySchool; **added** school levels=2 → SecondarySchool; hotel levels=4 → SmallHotel. (residential / tall / super-tall rows untouched.)
  - `test_rule_17a_building_yes_size_default` (:265–272) and `test_rule_17a_building_yes_office_default` — total 1600 → SmallOffice (was Medium).
  - `test_rule_6b_secondary_school` (:530–538) — added explicit `levels=2` + observed provenance → genuinely Secondary; kept composite token + `conf=="HIGH"`.
  - Comment-only (already pass, confirmed by trace): `test_rule_6b_composite_token`, `test_rule_6c_primary_school`, `test_rule_12b_medium_office` (total 3000 → Medium), `test_rule_12c_tall_slim_tower` (total 10000 → Large).
- Deviations: none. Added `provenance_*=OSM_OBSERVED` to the two school boundary cases and to `test_rule_6b_secondary_school` so confidence stays HIGH (head token `RULE_FUNCTION_TAG_SIZE` is not in `_LEVELS_CONSUMING`, so level-source does not affect the tier — per D3). Every changed assertion's comment cites E-R3-3.
- Test status: `pytest -k "ExactBoundaries or rule_17a or rule_6b or rule_6c or rule_12b or rule_12c"` → 20 passed, 95 deselected.
- Notes: these assertions previously encoded the OLD (wrong) cut-points; now aligned to E-R3-3. Manager-audited via read.

#### T07 — DOE-prototype self-classification regression tests — completed 2026-06-30
- Artifacts: `tests/test_building_classifier.py` — new class `TestDoePrototypeSelfClassification` (:1056–1096): one `@pytest.mark.parametrize` method, 7 cases (ids SmallOffice / MediumOffice / LargeOffice / PrimarySchool / SecondarySchool / SmallHotel / LargeHotel). Each builds a `_row` with explicit observed `levels` + provenance and calls `classify_building`, asserting the archetype id (F11 DOE/PNNL sizes: office 511/4982/46320 m² at 1/3/12 stories; school 6871 m² at 1 vs 2 stories; hotel 4 vs 6 stories).
- Deviations: none. Correctly uses `function_tag="hotel"`/`"school"` (hotel & school rules key on `function_tag`) and `building_tag="office"` (office idiom), mirroring the existing rule tests. Pure append — no existing test or fixture modified.
- Test status: `pytest TestDoePrototypeSelfClassification` → 7 passed.
- Notes: the direct regression lock for this bug. Money cases: DOE **PrimarySchool 6,871 m²/1-story** now → PrimarySchool (old footprint≥5000 rule wrongly returned SecondarySchool); DOE **SmallHotel 4-story** now → SmallHotel (old `≥4` returned LargeHotel). Manager-audited via read.

#### T08 — Full local suite + CP-α accuracy gate ⟶ CHECKPOINT 1 — completed 2026-06-30 — **CP-1 MET**
- Artifacts: `tests/fixtures/labelled_archetypes_50.csv` (13 office labels re-ratified to CBES-correct tier + header `re-ratified=2026-06-30` provenance stamp); `tests/test_building_classifier.py` (2 stale detailed-office unit tests, expected `MediumOfficeDetailed`→`SmallOfficeDetailed`). No `openubem/` code touched.
- CP-α result: coarse top-1 = 50/50 = **100.0%** (gate ≥0.90 ✓); fine top-1 = 46/50 = **92.0%** (gate ≥0.70 ✓). `pytest tests/test_building_classifier.py` → 122 passed, 0 failed.
- Full-suite triage: raw `pytest -q` = 20 failed + 82 errors. A stash-vs-pristine-`main` baseline proved **99 of these are pre-existing** (byte-identical failures on `main`, zero `building_classifier`/`archetype_id` dependency): missing local `docs/validations/overAll/results/…` artifacts (v19/r6 fixtures) plus unrelated code drift (`idf_builder` resolution-mode signature, HVAC meter count 11→13, results-parser status string). **Out of E-R3-3 scope** — logged as a separate pre-existing-defect backlog; does NOT block CP-1. The only 3 E-R3-3-caused failures (2 detailed-office unit tests + `TestLabelledTop1Accuracy::test_fine_top1`) are all resolved.
- Deviation (fixture re-ratification — not in original T08 spec): CP-α fine initially regressed 92%→66% (33/50). A per-row diagnostic (stash-vs-`main`) proved **all 13 flips were office rows whose ground-truth labels had been assigned under the OLD 500/4000 bins** — the label `notes` literally cite "8460m2 > 4000 -> LargeOffice". The E-R3-3 outputs match the authoritative LBNL-CBES bins (25k/100k ft² = 2322/9290 m²) and are strictly more correct. **The user delegated the call** (2026-06-30: "choose highest accuracy option … i am giving you to decide") → manager re-ratified the 13 labels to the CBES-correct tier with provenance-corrected notes + a header re-ratification stamp. This restored fine to the pristine baseline 92% (the 4 residual misses — 2 hotel keyed on empty `function_tag`, 1 retail, 1 synagogue — are pre-existing on `main`, unrelated to E-R3-3). Values were manager-decided from the diagnostic; a Sonnet applied them literally; the manager audited the resulting CSV by read and re-ran the diagnostic (100% / 92%).
- ⚠️ Carried forward to CP-β: the CP-α fixture contains **zero school rows**, so the D3 missing-levels-school risk (missing `levels` → default 1 story → PrimarySchool) is **NOT exercised by CP-1**. It moves entirely to CP-β (Boston fleet). A green CP-1 does **not** clear it.
- Notes: CP-1 — the gate between "code done" and "spend cluster time" — is **MET**. The cluster arc (T10/T11) is parked awaiting an explicit user go at CP-2.

#### T09 — Record erratum + checklist + progress log — completed 2026-06-30
- Artifacts: `docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md` §5 (E-R3-3 bullet appended to the DESIGN-errata ledger after E-R3-1/E-R3-2; header de-dated to span the series); `docs/PROJECT_CHECKLIST.md` (header block updated — E-R3-3 sub-arc now shown in flight at CP-1-met / CP-β-pending; last-updated → 2026-06-30). This plan doc §0/§8 self-recorded.
- Deviations: none. The R3 PLAN erratum bullet is explicit that E-R3-3 supersedes only E-R3-1's *thresholds*, not its total-floor-area metric.
- Test status: N/A (documentation only).
- Notes: closes the **local arc** (T01–T09). Cluster arc (T10 CP-β, T11 conditional full Phase-E) remains parked at the user decision points — do NOT auto-dispatch. CP-1 report delivered to the user 2026-06-30.

#### T12 — School-levels missing-default regression lock (D3 blind-spot closure) — completed 2026-07-01
- Artifacts: `tests/test_building_classifier.py` — added `_LEVELS_CONSUMING` to the existing import block (:17); new section after `TestDoePrototypeSelfClassification`: `TestSchoolLevelsAndMissingDefault` (parametrized, 4 cases: `school_1story_observed_primary`, `school_2story_observed_secondary`, `school_3story_observed_secondary`, `kindergarten_2story_stays_primary` — each asserts archetype id, exact `archetype_source`, and `conf=="HIGH"`) + `TestSchoolLevelsMissingDefaultExtra` (2 unparametrized tests: `test_school_head_tokens_not_levels_consuming` asserting `"RULE_FUNCTION_TAG"`/`"RULE_FUNCTION_TAG_SIZE"` are not in `_LEVELS_CONSUMING`; `test_missing_levels_school_defaults_to_primary` — builds a school row with no `levels`/`height_m` override, calls the real `_impute_levels()` to read the actual imputed value/source rather than hard-coding it, then asserts `classify_building` returns `PrimarySchool` with `archetype_source == "RULE_FUNCTION_TAG"` (byte-identical to the observed-1-story case) and `conf` unchanged vs. the observed case).
- Deviations: split the parametrized case from the plan's suggested single class into two classes (`TestSchoolLevelsAndMissingDefault` for the 4 parametrized cases, `TestSchoolLevelsMissingDefaultExtra` for the 2 unparametrized ones) — pytest's class-level `@pytest.mark.parametrize` applies to every method in the class, so the two argument-free tests could not share the class with the parametrized method (`collection error: function uses no argument 'case_kwargs'` on first run, fixed immediately). No `openubem/` file touched; pure test-file append per hard rule 3.
- Test status: `pytest tests/test_building_classifier.py -k "SchoolLevels" -rs` → **6 passed**, 122 deselected. `pytest tests/test_building_classifier.py::TestLabelledTop1Accuracy -rs` → **3 passed**; exact recompute: coarse top-1 = **100.0%**, fine top-1 = **92.0%** — both byte-identical to the CP-1 (T08) result, confirming the new tests do not perturb the accuracy gate. Full file: `pytest tests/test_building_classifier.py -q` → **128 passed** (122 + 6 new, 0 failed).
- Notes: **actual missing-levels imputation default found** — `_impute_levels()` at `building_classifier.py:121-127`: `levels` NA and `height_m` NA/≤0 → returns `(1, "HEURISTIC_DEFAULT")`. With that imputed level (1 < `_SECONDARY_SCHOOL_MIN_LEVELS`=2), rule 6b does not fire and the unconditional 6c catch-all applies → **PrimarySchool** — the STOP condition (missing-levels school landing anywhere other than PrimarySchool) did **not** fire; no code was touched. Confirmed `RULE_FUNCTION_TAG`/`RULE_FUNCTION_TAG_SIZE` are absent from `_LEVELS_CONSUMING` (:54-56), so the missing-levels school's `archetype_source` carries no `HEURISTIC_*` suffix and its confidence tier (`HIGH`, driven by the row's observed function/building-tag provenance, not by level source) is identical to the observed-1-story case — this is the D3-documented behaviour now locked. This closes the D3 blind spot: this test is now the only regression lock for the E-R3-3 school rule + missing-`levels` default, since neither CP-α (zero schools in the 50-row fixture) nor CP-β (zero schools in the 483-building Boston fleet, confirmed 2026-07-01) exercises it.

#### T10 — CP-β Boston 483 fleet re-sim + CP-2 report — completed 2026-07-01
- Artifacts (cluster + local, Sonnet employee a60f129912cd59028): `sbatch` job **1053384** (`openubem_er33_cpbeta_r3`, array 1-483%32, fire-and-forget) — **483/483 COMPLETED, 0 FAILED**, array wall ~1h23m. Local gen verified E-R3-3 sentinels + produced the EXACT expected distribution (SmallOffice 192 / MediumOffice 117 / LargeOffice 71, 0 schools/0 hotels). Harvested artifacts (scratchpad): `er33_05_results.csv`, `er33_04_simulation_manifest.parquet`, `er33_c09_gates_report.txt`, `er33_05_neighbourhood_summary.json`.
- Result — **archetype (offices only):** LargeOffice 138→71 (−67), MediumOffice 168→117 (−51), SmallOffice 74→192 (+118); 185/483 flipped. **F12 integrity PASS** (parse 100%, zone 0-mismatch, EUI-plausibility 98.76% — the 6 "outliers" are legit high-EUI food service). **CBECS gates (465 eligible, report-only per M-R2-4) vs the hardcoded anchor:** CV(RMSE) 53.78→60.63, NMBE −10.81→−10.99, R² 0.731→0.883, KS 0.190→0.350. Total EUI 173.50 kWh/m²/yr.
- Deviations: none on the sim. Harvest process notes — login-node `tar -czf` of ~43G SQL was heavy (orphaned tar briefly confused completion detection; resolved with a killed-then-clean single scp + `tar -tzf` integrity check rc=0, 1932 entries); latent bug in `scripts/cluster/make_manifest_from_cluster.py` (sacct parser crashes on grouped array keys like `100+`, bypassed via no `--job-id` since wall-clock isn't needed for gates) — backlog, DESIGN-neutral.
- **CP-2 decision — manager investigation + user ruling (2026-07-01):** user chose "hold + investigate" before accepting. Manager-authored read-only diagnostic (`scratchpad/diag_cbecs_drift.py`, fig `openubem/outputs/er33_cbecs_drift.png`, reuses the real `compute_validation_gates`) established the CP-2 "vs anchor" table is **confounded, not an E-R3-3 effect**: the hardcoded anchor (53.78/−10.81/0.731/0.190, `run_r3_fleet.py:365`) is the **R1 baseline (smaller fleet)**; the true 483 predecessor (R3 2026-06-11) already scored 69.823/−16.046/0.7312/0.2730 (`PLAN_step-4-cluster-offload-R4.md:203-208`) AND used the OLD pre-Phase-E HVAC modeling (cooling EUI 70.9 then vs 18.2 now). **Isolated classifier effect** (toggle ONLY the classifier; same fleet + current Phase-E; two before-reconstructions — point-mass & ratio, both agree): **CV(RMSE) −5.3/−2.7 (IMPROVES), KS −0.098/−0.084 (IMPROVES), R² ±0.000 (zero effect — the "+0.15 R²" is a Phase-E artifact), NMBE −7.2/−5.6 (more negative = the one real cost, from down-tiering 118 offices to the lower-intensity SmallOffice DOE template ~135 vs Medium/Large ~188)**. Structural: modeled EUIs are near-discrete archetype spikes vs a full-building-stock CBECS survey (8–1883); KS max-gap is at the LOW end — office-dominated neighbourhood vs all-types regional survey → large CV/KS are structural + pre-existing (exactly why M-R2-4 = report-only). Zero-fitted-params forbids tuning SmallOffice intensity to CBECS (future calibration follow-up only). **User ruling: ACCEPT the fix (E-R3-3 ratified); PARK T11** (defer the 8,160 Phase-E re-run; batch it with a future baseline refresh). Remote scratch cleanup dispatched to the Sonnet employee.
- Test status: sim gates as above; local classification locked by CP-1 (T08 100%/92%) + T12 (128 passed). No `openubem/` code touched by CP-2.
- Notes: **E-R3-3 arc closed at CP-2 (accept + park).** Only open item is the parked, user-gated T11. Backlog (out of E-R3-3 scope): the `make_manifest_from_cluster.py` sacct-key parser bug; the 99 pre-existing local test failures (missing `docs/validations/.../results/` artifacts + unrelated drift).

#### T11 — Full Phase-E 8,160-bldg re-run (E-R3-3) — **IN PROGRESS** (dispatched 2026-07-01)
- Status: **GREENLIT + DISPATCHED**, sim running. This entry to be finalized when the fleet lands + CP-3 compare is done.
- Trigger: user un-parked T11 2026-07-01 ("go go go" → confirmed "un-park & run T11" via AskUserQuestion, after the manager flagged it contradicted the just-made CP-2 park). User then went out and authorized autonomous handling of the *process* up to — not including — baseline promotion (T11.7 stays user-gated).
- Manager prep: mapped the Phase-E fleet machinery (Explore agent `a5931c23a9009b4b4` + manager verification of `v12_cell_pipeline.py`), then expanded PLAN §6 T11 from a stub into a full binding spec (Verified mechanics M1–M6 + Execution recipe T11.1–T11.7). Authored fresh-session handoff `docs/RESUME_T11_fresh_manager_session.md`.
- Method (clean classifier isolation, CP-2 lesson): **geometry frozen** — pre-seed each cell's `%TEMP%/ubem_validation/phaseE_er33/<cell>/01_buildings.gpkg` from the committed baseline footprints so `step1_fetch` hits cache (no live OSM re-fetch, no drift). **Non-destructive** — `--output-subdir phaseE_er33` keys both `final_dir` (new `docs/validations/.../phaseE_er33/` tree; committed `docs/docs_VALIDATION/.../phaseE/` baseline untouched) and `remote_fleet_dir` (`phaseE_er33_<cell>`, fresh → no stale-reuse short-circuit). `OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0`. No pipeline code edited.
- Execution: Sonnet cluster employee `a1be68fe17bb0e21e` (background). Structure: pre-seed 12 → **pilot `la_centre`** + self-verify 5 checks (cached-load / office down-tier / live_smoke PASS / output in phaseE_er33 + baseline untouched / fresh remote dir) → if all pass, auto-launch the other 11 as a tracked background loop (~7–8 h) → report per-cell office before→after + sim success + headline EUI + the 12 `05_results.csv` paths, then STOP.
- Process notes: employee first ended its turn as an untracked passive wait (the CP-β stranding mode); manager re-attached via SendMessage and it re-armed a tracked completion wait (`bwpzi8szt`). Manager also armed an independent backstop watch (`b6d1yw5af`) on the pilot's terminal artifact. As of dispatch, `la_centre` was mid-step3 IDF gen (step1+step2 already complete; HVAC downgrades + floor-zoning reroutes visible = E-R3-3 live).
- Pending (not yet done): pilot verdict; 11-cell fan-out; **T11.6 CP-3 before/after validation compare (manager/Opus job)** vs baseline city −24.4/−5.6/−25.7%, R² 0.895/0.924/0.718, CBECS NMBE −10.6/−20.5/−11.9%; **T11.7 promotion + REPORT/memory update (USER-SIGN-OFF ONLY — do not auto-promote).**
- **Update 2026-07-01 (autonomous, user out):** Pilot verified-progress from disk — **Check 1 geometry-frozen PASS** (step1 logged "loading cached GDF", NO OSM fetch, 226 bldgs = seed); **Check 2 E-R3-3 office down-tier PASS live** (offices conserved 104↔104, redistributed down: SmallOffice 24→41 (+17), MediumOffice 30→26 (−4), LargeOffice 50→37 (−13)). Pilot advanced to **step3 IDF gen** (work dir last-write 3:12 PM; live python PID 45448 accumulating CPU). Checks 3–5 (live_smoke PASS + array drained / output lands in `phaseE_er33` with committed `phaseE` untouched / remote dir `phaseE_er33_la_centre`) pending completion. Employee `a1be68fe17bb0e21e` task-notification fired reporting *"no live background children"* = the passive-wait desync recurred; manager armed a fresh **disk-based tracked backstop `boyiks5j2`** (polls pilot terminal artifacts every 120 s; breaks on final `05_results`/gates report, 110-min write-stall, or 5 h hard cap) so the pilot's terminal state is guaranteed to re-invoke the manager independent of the employee. Running pilot python left untouched.
- **Update 2026-07-01 — PILOT CRASH + RECOVERY (autonomous):** Backstop `boyiks5j2` fired `PILOT_STALL_NO_WRITE_110MIN`. Ground-truth forensics: **cluster array ran to full completion — all 226/226 buildings simulated** (`sim_out/` has 226 subdirs each with `eplusout.sql` + `eplusout.end`), BUT the driver python **crashed in `verify_and_repair`** (~4:07 PM) and never produced `final_dir`/`05_results`. Root cause pinned from code + artifacts (no code edited): 2 buildings (way_319507579, way_425993519) finished E+ without "EnergyPlus Completed Successfully" → pipeline queued a repair re-sim, wrote `step3/repair_fleet.lst` (v12 line 460), then the repair-ship `scp ... check=True` (line 462, **no retry**) hit a TRANSIENT ssh/scp failure → unhandled `CalledProcessError`/`TimeoutExpired` → process exit AFTER all sims succeeded. NOT the wake-plumbing (python survived 55 min of employee-sleep 3:12→4:07); NOT a deterministic bug; recoverable by re-run. **Recovery dispatched:** fresh Sonnet employee `a3be09e6e3d3b987a` re-runs `la_centre` to completion with stdout tee'd to a log (crash-diagnosable), launched as a TRACKED bg job (the python process itself is the tracked child → wakes employee on exit; no passive wait). Re-run is fast/resumable — `run_cell` line 1007 `_remote_results_complete` finds the 226 results still on the cluster → SKIPS re-sim → re-fetch → past-repair → step5 → copy (~15–40 min). Manager backstop `b2egb6fqy` armed (final artifacts + 35-min log-stall + 3 h cap). Employee instructed to STOP after the pilot for manager review before the 11-cell fan-out. **Fleet-robustness note for fan-out:** the repair-ship scp is a per-cell fragility (any cell with repair-eligible buildings can transiently crash the same way); handling operationally (per-cell re-run) rather than editing the pipeline mid-arc.
- **Update 2026-07-01 — RECOVERY RE-RUN IN HOME STRETCH (autonomous):** Recovery employee `a3be09e6e3d3b987a`'s resume (python PID 42116, alive, 592 MB) cleared the crash point — the repair round-trip **succeeded on the retry**: both flagged buildings re-simmed clean (way_319507579 `eplusout.end` 6:43 PM, way_425993519 `eplusout.sql` 505 MB 6:48 PM). All **226/226 results now extracted into `sim_out/`** (last-write 6:59 PM); driver is in the final packaging stretch (fetch done → build_sim_manifest → step5 → copy to `final_dir`). After-tree `docs/validations/overAll/results/phaseE_er33/la_centre` not yet created (step5/copy pending) — **committed baseline `docs/docs_VALIDATION/.../phaseE/` is a separate tree, so Check 4 "baseline untouched" is structurally guaranteed.** Monitoring correction: backstop `b2egb6fqy` fired a FALSE `RESUME_LOG_STALL_35MIN` at 6:56 PM while python was demonstrably alive and working — root cause is **Python stdout block-buffering** (a file-redirected log flushes only at buffer-fill/exit, so it looks "stale" for 30+ min while work progresses). Lesson for fan-out monitoring: **key backstops on work-dir file mtime, never on log freshness.** Superseded by work-dir-keyed backstop `bjqwtjjtd` (45-min work-stall / 2 h cap) — the current guaranteed wake. Checks 3–5 + gates report pending pilot terminal state.
- **Update 2026-07-01 19:20 — DRIVER DIED 3rd TIME; DURABLE MANAGER-SIDE COMPLETION ARMED:** Ground-truth recheck (user spotted a `RUNNING` cluster job via `squeue`): local driver python **gone** (clean `Get-Process` = no python), `final_dir` still absent, work-dir frozen at 18:59 (`step3/repair_fleet.lst` now lists a single stubborn building `way_319507579`; the other round-1 casualty `way_425993519` was fixed). Cluster job **`1054774_1 = openubem_la_centre_repair` RUNNING ~22 min on magic-node-01** confirmed ours (job name = `openubem_{cell}`, v12 line 301/483 `cell_name+"_repair"`) — it is the zero-area-strip re-sim of `way_319507579`. Diagnosis: the driver keeps dying **at/after `verify_and_repair`** each attempt, now pinned to the *launching-agent teardown* class (the tracked bg child dies when the Sonnet employee's turn ends) more than the line-462 scp — the recovery employee `a3be09e6e3d3b987a` "completed" and its child python vanished cleanly with no crash in-log. **`verify_and_repair` is bounded** (v12 405-560: zero-area strip round → optional one reroute-aware one_zone_per_floor round → return), then `run_cell` drops residual failures within `max(5,1%)`=5 tolerance → 1 stubborn building can be dropped, so **only the dead driver blocks completion.** `way_319507579` has now failed the *same* zero-area strip twice (rounds A+B); the definitive resolver is the **reroute-aware pass or the tolerance-drop**, which only a *surviving* driver reaches. **Fix (manager-owned, delicate load-bearing per role split):** armed durable bg job **`brqx0zuhu`** = a *manager-session* tracked child (survives turn boundaries, unlike employee children; notifies on exit) that (1) waits for `openubem_la_centre_repair` to drain from the queue (avoids repair-dir collision), then (2) does the resumable re-run (`PYTHONUNBUFFERED=1 OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0`, live log `scratchpad/phaseE_er33_la_centre_resume3.log`) to `final_dir`. Script `scratchpad/complete_la_centre_durable.sh`. **Fan-out lesson:** launch each cell's driver as a *turn-surviving* process (manager bg child or OS-detached), NOT an employee-turn child — the 3× la_centre death is a launch-lifecycle bug, not a pipeline bug.
- **Update 2026-07-01 19:25 — DURABLE JOB HEALTHY, IN WAIT-FOR-REPAIR:** `brqx0zuhu` confirmed running and behaving. Its `wait_repair` poll-1 logged `rc=1` (transient cold-start ssh hiccup, ControlMaster contention) — correctly did NOT break (guard = `rc==0 && count==0`); loop self-heals on the 5-min retry. Verified the exact script-style poll works now (`squeue -h -n openubem_la_centre_repair | wc -l` → `rc=0 count=1`). Cluster state: `1054774_1 openubem_la_centre_repair` still **RUNNING ~28 min** on magic-node-01 (single stubborn `way_319507579` zero-area re-sim — long, likely heavy or heading to walltime; either terminal state drains the queue and releases the loop into the re-run). Also observed a **non-project** job `1054800 3J_8E_val` RUNNING — left untouched per never-touch-other-runs. `final_dir` still absent; python idle between polls (expected). Next signal: `brqx0zuhu` exit notification (repair drains → resumable re-run → `final_dir`), or its internal timeout→re-run fallback.
- **Update 2026-07-01 19:48 — DURABLE JOB'S SSH WEDGED; SWAPPED TO CLEAN DIRECT RE-RUN (autonomous):** `brqx0zuhu`'s `wait_repair` loop wedged — **5 consecutive polls `rc=1 count=''`** (19:23→19:43) while, from the manager shell, ssh to Speed returned **`rc=0` and the queue was fully drained** (`openubem_la_centre_repair`=0, zero `openubem_*` jobs). So the repair round **finished** but the durable job couldn't see it (its own ssh path stayed flaky) and was set to burn its ~3 h timeout on the naive `rc==0 && count==0` guard; its worst case was then re-running through the *same* wedged ssh. Backstop `bjqwtjjtd` fired `WORK_STALL_45MIN` (work-dir idle since 19:43, no python running = re-run not started). **Decision:** the durable job's only remaining value was the wait phase, now obsolete → **stopped `brqx0zuhu`** (confirmed `running` first, so no collision) and launched a **clean direct resumable re-run** from the manager shell where ssh is proven healthy — no wait-wrapper (queue already empty), the v12 pipeline handles its own ssh retries and is resumable. Launch: `nohup bash scratchpad/rerun_la_centre_resume4.sh &` (double turn-surviving = manager bg child **+** `nohup`-detached), `PYTHONUNBUFFERED=1 OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0`, log `scratchpad/phaseE_er33_la_centre_resume4.log`. **Re-run engaged healthy** (19:48:50): frozen-geometry re-confirmed (step1 "loading cached GDF", 226 bldgs, no OSM fetch = **Check 1 PASS**); E-R3-3 down-tier re-confirmed live (**Check 2**, SmallOffice 41 / MediumOffice 26 / LargeOffice 37, 15 unknown); now in step3 IDF regen (1 live python). This fresh `run_cell` cleared local `sim_out`/`fleet_staging` (fresh regen), so it will re-check remote and either REUSE the on-cluster results or re-ship+re-submit, then verify_and_repair → step5 → `final_dir`. Because it's `nohup`-detached I lose the auto-exit notification, so armed **work-dir-keyed completion watcher `bgebfeqs2`** (`scratchpad/watch_la_centre_resume4.sh`; 15-min polls; notifies on `final_dir/05_results.csv` = SUCCESS, `RERUN4_EXIT` marker, or >50-min work-dir stall; 24 h ceiling). Checks 3–5 + gates report pending pilot terminal state.

---

*OpenUBEM — manager-authored plan. Erratum E-R3-3. No code changed by this document. 2026-06-30 (CP-2 close-out appended 2026-07-01; T11 dispatch appended 2026-07-01).*
