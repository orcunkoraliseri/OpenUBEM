# OpenUBEM — Archetype-Classification Fix (E-R3-3) Results

**What this document is:** a reader-facing results report for the **E-R3-3 archetype-classification
fix** — the correction of three size/level cut-points that were misclassifying their own DOE/PNNL
prototype buildings. It presents the before/after impact of folding the fix into the adopted
**Phase-E** 8,160-building baseline: the reclassification blast radius, the mechanism that moves the
headline EUI, the decomposition of that move into the fix itself vs. unrelated code drift, and the
national validation gates — with figures embedded.

The classification fix supersedes the DESIGN §3C literals via the user-ratified erratum **E-R3-3**;
the binding plan/record is
[`PLAN_archetype_threshold_fix_E-R3-3.md`](../docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md),
the corrected cut-point sources are in
[`RESULT_I02_archetype_classification_cascade.md`](../docs_ACTIVE/input/deepResearch/RESULT_I02_archetype_classification_cascade.md),
and the Phase-E baseline this modifies is documented in
[`OpenUBEM_results_hvacServiceLoads.md`](OpenUBEM_results_hvacServiceLoads.md).

> **Bottom line:** E-R3-3 is a **classification-correctness fix, not a tuning change** — it introduces
> **zero fitted parameters** and swaps one set of published-source literals for another. Its main
> effect is to **down-tier ~660 offices from MediumOffice to SmallOffice**, which crosses a DOE HVAC
> template discontinuity (VAV → packaged single-zone) and pulls the city median total EUI **down**
> (NYC −16.5, Austin −8.2, LA −0.7 kWh/m²). This **widens** the model's existing under-prediction vs.
> measured by **5–7.5 pp** in NYC/Austin (nil in LA). The widening is **89–100% attributable to the
> reclassification itself**; it is the *correct* classification exposing a pre-existing
> DOE-SmallOffice-template gap that the old misclassification was accidentally masking. Accepted and
> documented under the same correctness-over-proximity rule as the Phase-E "Other" residual.

---

## 1. What E-R3-3 changed

The classifier assigns each building a DOE/PNNL archetype from its tags, footprint, and level count.
Three cut-points were set to values that **misclassified the very prototypes they were meant to
select** (e.g. the DOE MediumOffice prototype landed in the LargeOffice bin). E-R3-3 replaces the
three literals with published-source values; the selection metric and the vintage-blind, zero-fitted
rule are unchanged.

| Rule | Old cut-point (wrong) | New cut-point (E-R3-3) | Source |
|---|---|---|---|
| **Office size tier** | total floor area `< 500 / < 4000 m²` | **`< 2322 / < 9290 m²`** (25,000 / 100,000 ft²) | LBNL CBES bins, Hong et al. 2015 |
| **School tier** | footprint `≥ 5000 m²` (flagged a guess, OQ-4) | **level count** — Primary = 1 story, Secondary = ≥ 2 stories | Deru et al. 2011 (DOE prototypes) |
| **Hotel tier** | `≥ 4` levels | **`≥ 5` levels** (SmallHotel 4-story / LargeHotel 6-story) | Deru et al. 2011 |

The office change has by far the largest blast radius: it moves the Small/Medium boundary up from
500 m² to 2,322 m², so a large population of mid-size buildings that were being called MediumOffice
now correctly resolve to **SmallOffice**. The school change resolves the DESIGN open question OQ-4;
the hotel change moves a handful of 4-story buildings from Large to Small.

The fix was validated in two ratified stages before this baseline fold-in — a local accuracy gate
(**CP-α**: coarse 100% / fine 92% top-1) and a Boston 483-building CBECS fleet re-run (**CP-β / CP-2**,
483/483 clean) — then applied to the full Phase-E matrix with **geometry frozen** (re-classify off the
committed per-cell `01_buildings.gpkg`, no OSM re-fetch) so the comparison isolates the classifier.

---

## 2. Fleet integrity

The full 12-cell / 8,160-building Phase-E matrix was re-classified and re-simulated on the Speed SLURM
cluster with the corrected classifier and frozen geometry.

| Metric | Before (phaseE) | After (phaseE_er33) |
|---|---|---|
| Cities × density rings | 3 × 4 = 12 | 3 × 4 = 12 |
| Total buildings | 8,160 | 8,160 |
| EnergyPlus success | 8,160 | **8,154** |
| Cells with results | 12 / 12 | 12 / 12 |

The **6-building** success drop is **not** caused by E-R3-3. All six — five `la_rural` and one
`la_urban` (`way/402215469`) — are precisely the inverted-geometry-winding fatals the original
Phase-E identified (`REPORT_phaseE_final.md` §7 limitation #6). In the committed baseline they reach
8,160/8,160 only via a **post-hoc manual remediation** (`debugs/10_fails_solution.md`: build-time
winding fix + thermal-mass fallback) that is not part of the per-cell pipeline; the automated E-R3-3
re-run reproduces the raw drop because that manual step was not re-applied. They are pre-existing and
geometry-related, unrelated to the classifier, and do not affect any headline statistic.

---

## 3. Headline: city comparison before/after vs measured

Median total site EUI (kWh/m²·yr) against the measured city anchors, before (committed Phase-E) and
after (E-R3-3), over success rows excluding `OpenUBEMUnknown`:

| City | n (before / after) | Before | After | Measured | Δ% before | Δ% after |
|---|---|---|---|---|---|---|
| **NYC** | 3,746 / 3,746 | 165.7 | **149.3** | 219.2 | −24.4% | **−31.9%** |
| **LA** | 2,317 / 2,311 | 107.2 | **106.6** | 113.6 | −5.6% | **−6.2%** |
| **Austin** | 1,447 / 1,447 | 120.4 | **112.2** | 162.0 | −25.7% | **−30.7%** |

The model already under-predicted the absolute level (the accepted Phase-E residual); E-R3-3 moves it
**further below** measured — most in NYC/Austin, negligibly in LA. §4 explains why, and §5 shows that
almost all of this move is the fix itself, not incidental code drift.

![Phase-E baseline vs measured (post-E-R3-3)](../../openubem/outputs/comparisons/phaseE_city_comparison.png)
*City-Overall comparison after the E-R3-3 fold-in. The red (Phase-E) bars now sit lower than in the
pre-fix baseline because the office population down-tiers to the lower-intensity SmallOffice template.*

---

## 4. Mechanism — why offices down-tier across an HVAC cliff

Matching every building before↔after by `osm_id` on the success set (7,504 rows present and non-Unknown
in both), **936 buildings changed archetype**. The shift is dominated by one flip:

| Flip | n | median EUI before → after | Δ |
|---|---|---|---|
| **MediumOffice → SmallOffice** | 662 | 179.1 → 107.3 | **−71.8** |
| LargeOffice → MediumOffice | 188 | 167.7 → 151.6 | −16.1 |
| MediumOffice → LargeOffice | 68 | 113.5 → 109.4 | −4.1 |
| PrimarySchool → SecondarySchool | 9 | 222.5 → 237.8 | +15.4 |
| SmallOffice → MediumOffice | 6 | 91.1 → 140.2 | +49.1 |
| MidriseApartment → HighriseApartment | 3 | 89.9 → 89.6 | −0.2 |

Fleet-wide the office mix conserves count (4,186 offices both sides) while re-tiering downward:
**SmallOffice 2,848 → 3,504 (+656), MediumOffice 948 → 412 (−536), LargeOffice 390 → 270 (−120).**

The −71.8 kWh/m² drop on the 662 Medium→Small flips is **not** a smooth re-scaling — it is a template
**discontinuity**. Decomposing it by end use (median over the 662 flipped buildings):

| End use | MediumOffice (before) | SmallOffice (after) | Δ | share of drop |
|---|---|---|---|---|
| **Fans** | 40.0 | 9.9 | **−30.1** | 42% |
| **Equipment** (plug) | 44.1 | 27.8 | **−16.3** | 23% |
| **Heating** | 42.7 | 27.4 | **−15.3** | 21% |
| DHW | 6.2 | 1.9 | −4.2 | 6% |
| Cooling | 14.8 | 11.3 | −3.4 | 5% |
| Lighting | 26.5 | 26.5 | 0.0 | — |

The fan collapse is the driver: DOE **MediumOffice runs multi-zone VAV** (~40 kWh/m² fan energy) while
**SmallOffice runs packaged single-zone (PSZ-AC)** (~10). Crossing the 2,322 m² cut-point swaps the
entire air-system family, and SmallOffice additionally carries a lower plug-load density. So the city
median does not slide across the reclassification — it **steps down a cliff**.

This also explains the per-city asymmetry. LA barely moves (−0.7) because only **10.5%** of its fleet
is SmallOffice and its mild climate makes fan/heating absolute values small; NYC (**58.3%** SmallOffice)
and Austin (**74.4%**) move most, exactly where the fan+heating cliff bites hardest.

![End-use breakdown by city (post-E-R3-3 baseline)](../../openubem/outputs/comparisons/phaseE_enduse_breakdown.png)
*Stacked physical end-use medians per city on the new baseline — the office fan/equipment/heating
reduction is the visible change from the pre-fix stack.*

---

## 5. Decomposition — the fix vs. incidental code drift

Because the baseline was harvested at the Phase-E close (2026-06-27) but the E-R3-3 re-run executed at
HEAD, the before/after also picks up **code drift** from commits landed since (zoning / service-load /
resolution-mode changes). Freezing geometry stopped *OSM* drift; it did not stop *code* drift. Of the
6,568 buildings whose archetype did **not** change, **205 shifted EUI anyway** (143 of them SmallOffice,
median −18 kWh/m², one −40) with `levels` unchanged — the signature of code drift, not reclassification.

Constructing counterfactuals on the matched set (classifier-only = flipped buildings take their after
value, unchanged buildings stripped back to before; drift-only = the reverse) attributes the headline
median shift:

| City | Δmedian total | **Classifier fix** | **Code drift** | residual |
|---|---|---|---|---|
| **NYC** | −16.5 | **−14.7 (89%)** | −1.6 (11%) | −0.1 |
| **LA** | −0.7 | **−0.7 (100%)** | +0.0 | 0 |
| **Austin** | −8.2 | **−8.2 (100%)** | +0.0 | 0 |

The exact (linear) **mean** decomposition agrees: NYC mean −8.70 = classifier −7.97 (92%) + drift −0.73
(8%). In measured-gap terms, NYC's gap widened −7.5 pp, of which **−6.7 pp is the classifier and only
−0.8 pp is drift**; Austin's −5.1 pp and LA's −0.6 pp are entirely the classifier.

The drift is muted on the **median** because the 143 drifted SmallOffice buildings already sit inside
the dense SmallOffice cloud, not near the 50th percentile. **The conclusion: ≥89% of the move-away is
the intended fix; the ≤11% (NYC-only) drift tail is same-signed and never changes the direction,
ranking, or verdict.**

---

## 6. National validation gates (CBECS 2018)

Gates follow the Phase-E ruling: **NMBE ±10% and R² > 0.60 are hard; CV(RMSE) and KS are report-only**
(structurally unpassable for an archetype-deterministic UBEM, ruling V-R5-5).

| City | NMBE (b → a) | R² (b → a) | CV(RMSE) (b → a) | KS_D (b → a) |
|---|---|---|---|---|
| NYC | −10.5 → **−14.7** | 0.890 → **0.888** | 37.8 → 38.6 | 0.2563 → 0.2221 |
| LA | −21.5 → **−25.5** | 0.925 → **0.920** | 61.0 → 61.8 | 0.2389 → 0.2561 |
| Austin | −11.9 → **−16.2** | 0.718 → **0.720** | 47.5 → 49.6 | 0.3018 → 0.2730 |

**R² is essentially flat everywhere** (±0.002–0.005) — the reclassification does not degrade
distribution shape, it only lowers the level. **NMBE goes ~4 pp more negative** in all three cities,
the expected consequence of the SmallOffice down-tier. This is the same signature Phase-E already
carries: a zero-fitted-parameter model reports what it computes, and CBECS movement does not veto a
correctness fix. KS moved asymmetrically (NYC/Austin tighten, LA loosens) — report-only, no action.

---

## 7. Why the widened gap is accepted (not fitted away)

E-R3-3 is a textbook case of **correctness over proximity-to-measured**. Before the fix, ~660 mid-size
offices were mis-parked in the higher-intensity MediumOffice template, whose VAV fan energy and higher
plug density happened to sit *closer* to the CBECS office anchor — the model was **right for the wrong
reason**. The fix puts these buildings in their correct SmallOffice bin and, in doing so, reveals that
the **DOE SmallOffice prototype is a genuinely low-intensity template** (fleet median ~130 kWh/m²)
against real offices (NYC measured 219). Closing that gap would require **fitting office plug/fan loads
to match CBECS**, which breaks the zero-fitted-parameters rule that is the whole point of the model.

The gap is therefore accepted and documented, identically to the Phase-E "Other"-category residual. One
honest caveat worth recording: the city median is now **hypersensitive to the 2,322 m² cut-point**
because it straddles a ~72 kWh/m² system cliff — small errors in imputed levels near the boundary now
swing a building's EUI hard. This is a template-fidelity observation (the two DOE office templates
bracket, rather than span, real office EUI), not a defect in the classifier.

---

## 8. Reproducibility & provenance

| Artifact | Path |
|---|---|
| Per-cell per-building results (12 × CSV), promoted baseline | `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.csv` |
| Pre-promotion E-R3-3 run tree (throwaway) | `docs/validations/overAll/results/phaseE_er33/<cell>/` |
| Per-cell gate reports | `.../phaseE/<cell>/v12_<cell>_gates_report.txt` |
| Corrected classifier | `openubem/semantic/building_classifier.py` (office helper + rules 3/6/12/17a) |
| Cut-point source (deep research) | `docs/docs_ACTIVE/input/deepResearch/RESULT_I02_archetype_classification_cascade.md` |
| Binding plan + erratum text (E-R3-3 §4) + progress log | `docs/docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md` |
| DOE-prototype self-classification regression tests | `tests/test_building_classifier.py::TestDoePrototypeSelfClassification` |
| City comparison / end-use / CBECS figures (regenerated) | `openubem/outputs/comparisons/phaseE_*.png` |
| Spatial overview grid (regenerated) | `openubem/outputs/comparisons/phaseE_overview_grid.png` |
| Before/after compare + diagnosis scripts | `scratchpad/cp3_before_after_compare.py`, `scratchpad/diag_er33_moveaway.py`, `scratchpad/diag_decompose.py` |
| Phase-E baseline this modifies | `docs/docs_DONE/hvac-ServiceLoads/REPORT_phaseE_final.md` (E-R3-3 addendum) |

![Building total EUI — 12-cell overview grid (post-E-R3-3 baseline)](../../openubem/outputs/comparisons/phaseE_overview_grid.png)
*The promoted E-R3-3 baseline, all 12 cells on the shared color scale — the office down-tier is
visible as a cooler office population in the dense cells.*

---

## 9. Where to go next

| You want… | Read |
|---|---|
| The Phase-E baseline this modifies | [`OpenUBEM_results_hvacServiceLoads.md`](OpenUBEM_results_hvacServiceLoads.md) |
| The resolution-mode results on the same fleet | [`OpenUBEM_results_Resolution.md`](OpenUBEM_results_Resolution.md) |
| The binding plan, erratum text, and task/progress log | `docs/docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md` |
| The corrected cut-point derivations | `docs/docs_ACTIVE/input/deepResearch/RESULT_I02_archetype_classification_cascade.md` |
| The plain-language pipeline overview | `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` |
| Current project status | `docs/PROJECT_CHECKLIST.md` |

---

*OpenUBEM — archetype-classification fix (E-R3-3) results report. Before/after numbers sourced from the
CP-3 12-cell before/after compare and the manager diagnostic decomposition (2026-07-03); the corrected
classifier follows erratum E-R3-3 (ratified 2026-06-30). The DESIGN/spec docs remain the binding source
of truth. 2026-07-03.*

---

## 10. Addendum — input-framework classification fixes (I01/I02 audit, 2026-07-21)

**What changed.** Two evidence-backed fixes from the I01/I02 deep-research audit
(`docs/docs_DONE/BUGS/input-framework/deepResearch/RESULT_I01_osm_tag_to_use_class_mapping.md`,
`RESULT_I02_archetype_classification_cascade.md`), executed per
`docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md` (DESIGN errata
**E-IF-1**):

1. **E-IF-1 — dominant-tag threshold fix.** `dominant_tag_threshold` default changed `0.60` → `0.50`
   at all four occurrences in `openubem/semantic/building_classifier.py`. Rule 15
   (`MIXED_USE_DOMINANT_TAG`, "function_tag wins over building_tag") was confirmed **dead code** in
   production: `_normalise_use_class` only ever returns a disagreement score of exactly `0.5`, so the
   old `0.60` threshold made `0.5 >= 0.60` always false — every real tag-disagreement row fell through
   to rule 16's blanket `MidriseApartment` fallback instead. This resolves DESIGN §7 OQ-1 (flagged
   `ASSUMPTION_DESIGN_DEFAULT` at §11 Pass-2, 2026-05-06) using I01's peer-tool evidence
   (URBANopt/CityBES/AutoBEM/UMI/CEA all let a specific function/use tag outrank a generic structural
   tag). Regression repro: `function_tag="office", building_tag="house"` (a home office) now
   classifies `("SmallOffice", "MEDIUM", "MIXED_USE_DOMINANT_TAG")` instead of the previous
   `("MidriseApartment", "MEDIUM", "MIXED_USE_DOMINANT_TAG")`. Rule 16 (no-dominant fallback) remains
   coded and reachable whenever a caller passes a stricter threshold explicitly (e.g. `0.60`).

2. **22 new OSM tag → use-class entries** in `openubem/data/osm_to_use_class.json`
   (`schema_version` `1.1.0` → `1.2.0`): residential (`duplex`, `semidetached`, `terraced_house`,
   `cabin`, `static_caravan`, `houseboat`), industrial (`depot`, `barn`, `stable`, `cowshed`,
   `greenhouse`, `silo`, `storage_tank`, `substation`), institutional (`place_of_worship`, `townhall`,
   `community_centre`, `educational`), commercial (`post_office`, `theatre`, `department_store`,
   `company`) — each a named, dated OSM-wiki/peer-tool convention (zero-fitted-params). `government`
   and `mall` needed no action (already present verbatim). **`service` was deliberately excluded**:
   I01 recommended `building=service → commercial`, but 3 user-ratified rows in
   `tests/fixtures/labelled_archetypes_50.csv` (`osm_id` 203026968, 212122959, 124865475) ground-truth
   generic `service` buildings as `OpenUBEMUnknown`; remapping would flip these from correct to
   incorrect against the ratified label. `service` remains mapped to `unknown` (pre-existing from the
   Phase-D CP-4 crosswalk, 2026-07-13) — unchanged by this plan.

**Blast radius (verified live, both fixtures).** 5 of 882 rows (0.57%) across the two committed real
fixtures change (`boston_downtown_500m.gpkg` 483 rows, `chicago_loop_500m.gpkg` 399 rows) — all
LOW→MEDIUM/HIGH confidence upgrades or unknown→correctly-institutional reclassifications, zero
overlap with `labelled_archetypes_50.csv`. **One correction to the plan's F8 fact table**: live
reproduction of Chicago `osm_id` 765296577 (`building_tag=yes`, `function_tag=theatre`) gives
`(LargeOffice, MEDIUM, RULE_USE_CLASS_SIZE)`, not the plan's stated
`(SmallOffice, MEDIUM, RULE_USE_CLASS_SIZE)`. Root cause: adding `theatre → commercial` shifts this
row's `use_class` from `unknown` to `commercial`, which — under the real fleet-level
`BuildingClassifier.classify()` pipeline's stratified group-median levels imputation
(`_build_levels_median_lookup`, T05 wave-2b) — pulls a different per-stratum median-levels value
(6 for `unknown` vs. 16 for `commercial` in this fixture) for this row's missing `levels`, crossing
the `MediumOffice`/`LargeOffice` total-floor-area boundary independent of the confidence/token change
the plan anticipated. The other 4 F8 rows reproduce exactly. This is a second-order interaction the
plan's simplified pre-audit did not model (it did not run the full stratified-levels pipeline); it is
not a code defect — the T04 regression test (`TestI01FixtureDiffRegression`) locks in the
**verified-live** value, not the plan's stated one.

**I02 cross-check (F9).** All 3 of I02's headline threshold recommendations (office bins
2,322/9,290 m²; hotel Small/Large split ≥5 levels; school Primary/Secondary by level count) were
**already the exact values live** in `building_classifier.py`, shipped by the E-R3-3 arc (closed
2026-07-03) using the same DOE/PNNL/LBNL-CBES sourcing I02 independently re-derived. I02's other 3
verdicts (super-tall/tall thresholds, data-center 500 m² split, vintage-blind archetype selection)
all concluded "keep as-is." **Net: I02 required zero code changes** in this plan.

**Labelled-accuracy gate (OQ-7) re-measurement.** `TestLabelledTop1Accuracy` still passes (coarse
100%, fine 88.0%/44 of 50 — both above the 90%/70% gates). **The plan's cited reference baseline
(92.0% fine, 46/50, from `PLAN_step-2-classifier-coverage-R3.md` §8 A02) is stale**: a live "before"
reproduction (threshold reverted to 0.60, the 22 tags removed) against the *current* codebase gives
the identical 88.0%/44-of-50 result with the identical 6 mismatched rows as the "after" state —
proving T01/T02 changed **zero** of the 50 labelled-fixture predictions (confirming F6's zero-overlap
claim exactly), and that the 92%→88% drift predates this plan (most likely from the intervening
Phase-D CP-4 crosswalk work, 2026-07-13, already present in the working tree). No action taken on
this discrepancy beyond recording it here — per the plan's own "do not force a match" instruction.

**I03 (CBECS PBA crosswalk).** Documented as a deferred backlog item, not executed — see plan §9.
Office/hotel size-split validation is feasible with the existing `sqft` column in the CBECS regional
CSVs; restaurant/school `PBAPLUS` splits require new CBECS microdata acquisition.

**Full test suite (T06a).** `tests/test_building_classifier.py` — **142/142 passed** (9 new tests
added: 2 for T03's threshold fix, 7 for T04's tag additions/fixture-diff regression guard). Whole-repo
`python -m pytest -q -rs` — **1,924 passed, 44 failed, 9 skipped, 36 errors** (2,013 collected total;
the plan's cited "≥526 passed" baseline from `PLAN_step-2-classifier-coverage-R3.md` is stale — the
repo has grown to 2,013 tests since). All 80 failing/erroring tests were individually confirmed
**pre-existing and unrelated to this plan**: verified via a targeted `--lf` rerun (full untruncated
output, 316s) that none reference `building_classifier.py`, `osm_to_use_class.json`, or
`test_building_classifier.py`. They fall into three unrelated buckets, all missing-fixture/
missing-file environment gaps: (1) `docs/docs_DONE/.../elevators/scripts/tests/*` — missing
`synthetic_10_gdf` pytest fixture and related setup; (2) `tests/test_impute_montage.py` — file-output
assertions; (3) `tests/test_v19_basis_diagnostic.py` / `tests/test_v19_national_cbecs_rescore.py` —
`FileNotFoundError` for `docs/docs_DONE/phaseC_combinedResim/v19_validation/*.md` (directory/files not
present in this checkout). None of these touch the classification pipeline this plan modifies.

*Addendum appended 2026-07-21, input-framework-classification-fixes plan T06.*
