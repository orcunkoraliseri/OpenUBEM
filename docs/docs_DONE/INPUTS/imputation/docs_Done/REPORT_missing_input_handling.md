# REPORT — How OpenUBEM Handles Missing Inputs

**Date:** 2026-07-01
**Method:** Haiku-model codebase scan (cost discipline: cheap model for bulk grep/read), all
file:line citations and quantitative claims spot-verified by the manager session directly against
source before inclusion here. Scope: all 5 pipeline stages, code only (no execution).
**Status:** informational audit — no code changed by this report.

---

## 1. Summary

There is no single, centralized "imputation module." Missing-data handling is implemented
per-stage, ad hoc, with three distinct tiers of maturity:

| Tier | Behavior | Stages |
|---|---|---|
| **A — Tracked** | Explicit fallback + a provenance/confidence column records that it happened | Classification (Stage 2), climate zone (2.1), construction/vintage (2.2) |
| **B — Silent default** | Fallback value substituted, but nothing records that a default was used | HVAC system sizing, DHW/cooking floor-area defaults, EPW-missing, meter-missing |
| **C — Hard fail, no fallback** | Missing input raises an exception rather than guessing | Internal loads table gaps, schedule table gaps, carbon-factor lookup, climate-zone total-miss |

This split is not accidental — it roughly tracks how consequential a wrong guess would be.
Tier C sites are all "one bundled table, closed vocabulary, gap should never happen in
production" — the code treats a gap there as a bug, not a normal condition. Tier A sites are all
places DESIGN explicitly anticipated missingness (OSM tags are known-patchy). Tier B is the
weak spot: mostly HVAC/DHW/cooking numeric parameters that get a physically-reasonable default
with no record left behind of which buildings received it.

---

## 2. Inventory by input type

Each table below is one input (or tightly related group of inputs). Columns: whether the input can
actually be missing/absent in practice, the exact handling mechanism, the substituted fallback
value, whether a provenance/confidence marker is left behind, the tier (A/B/C, per §1), and the
file:line source.

### 2.1 Geometry & footprint inputs

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| `building:levels` (OSM) | Yes | Left null at acquisition; imputed later (see §2.2) | — | none here | B | `acquisition/osm_fetcher.py` |
| Footprint polygon >120 vertices | Yes (complex footprints) | Douglas-Peucker @0.5m → @1.5m → convex hull → min-rotated-rect, cascading | Simplified polygon | `data_quality_flag` tokens (`idf_dp_coarse`, `idf_hull_simplification`, `idf_bbox_simplification`) | A | `geometry/footprint.py` |
| Footprint invalid or <20 m² | Yes (OSM noise) | Row skipped | Row dropped | `skipped_invalid_geometry` | A | `geometry/footprint.py` |
| MultiPolygon footprint | Yes (OSM multi-part buildings) | Coerced to largest-area part | Single polygon | `multipolygon_coerced_to_largest_part` | A | `idf/builder.py` (`_coerce_to_polygon`) |
| Perimeter-core zoning infeasible (core <10 m² or courtyard ring) | Yes | Falls back to `one_zone_per_floor`, then `single_zone` | Simpler zoning strategy | Warning log only — no `data_quality_flag` entry | B | `geometry/zoning.py` |

### 2.2 Building classification inputs (OSM tags, levels, height)

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| `levels`, with `height_m` present | Yes | `max(1, int(height_m // 3.5))` | Imputed level count | `HEURISTIC_HEIGHT` | A | `building_classifier.py:121-126` (`_impute_levels`) |
| `levels` and `height_m` both absent | Yes | Default to 1 level | `1` | `HEURISTIC_DEFAULT` | A | `building_classifier.py:127` |
| `building_tag` and `function_tag` both absent | Yes | `use_class="unknown"` → cascades through rule table to `OpenUBEMUnknown` | `archetype_id=OpenUBEMUnknown` | `FALLBACK_UNKNOWN`, confidence forced `LOW` | A | `building_classifier.py:316-317`, invariant check `484-493` |
| `building_tag`/`function_tag` disagree | Yes | Routed by `dominant_tag_threshold=0.60`, else `MidriseApartment` | Dominant tag's class, or `MidriseApartment` | Confidence downgraded `MEDIUM`/`LOW` | A | `building_classifier.py:100,292-310` |
| Untagged `building=yes`, footprint area known | Yes | Size-bucketed office guess (rule 17a) | Archetype guess by size bucket | `FALLBACK_SIZE_DEFAULT` | A (tracked — but 2 of the underlying size thresholds are wrong; see `docs/docs_ACTIVE/misclassification/BUG_archetype_classification_thresholds.md`) | `building_classifier.py` rule 17a |

### 2.3 Climate zone & weather inputs

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| Building point outside all county polygons (Tier-1 join miss) | Yes | Nearest-neighbor join, `max_distance=5_000` m | Nearest county's climate zone | `climate_zone_method=nearest_fallback`, `provenance=HEURISTIC` | A | `acquisition/climate_zone.py:143-160` |
| Point still unmatched after both tiers | Yes (rare — outside US coverage) | Hard fail | — (aborts) | — | C | `acquisition/climate_zone.py:163-171` (`RuntimeError`) |
| Zero Tier-1 matches across entire run | Yes (signals CRS/continent bug) | Hard fail | — (aborts) | — | C | `acquisition/climate_zone.py:120-130` (`RuntimeError`) |
| EPW path missing / doesn't exist | Yes | Site-location block simply not populated | IDF proceeds with EnergyPlus internal defaults | none | B (arguably should be C) | `idf/builder.py:118-120` |

### 2.4 Vintage & construction inputs

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| `year_built` | Yes | `pd.cut(..., right=False)` bins NaN → -1 → `DOERefPre1980` | Oldest/leakiest vintage tier, U-factors ×1.6 | `VINTAGE_NAN_PERMISSIVE_DEFAULT` | A | `construction_sets.py:44,129-139` |
| (archetype, climate_zone) construction lookup gap | Only for custom/user-supplied tables — bundled 90.1-2019 table is gap-free | KDE-fill from sibling climate zones, same archetype | Sampled U-value | `KDE_IMPUTED` | A | `construction_sets.py:171-219` |

### 2.5 Internal loads & schedules inputs

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| Archetype missing from internal-loads table | No — bundled table is gap-free; a gap would be a bug | Hard fail | — (raises) | — | C | `semantic/loads.py:126-139` (`ValueError`) |
| Archetype missing from schedules table | No — same guarantee, except `OpenUBEMUnknown` has a pre-baked `MediumOffice`-clone row | Hard fail (or static clone for `OpenUBEMUnknown`) | — (raises), or clone row | — | C | `semantic/schedules.py:42,51` (`KeyError`) |

### 2.6 HVAC system parameter inputs

The weakest-instrumented input type in the pipeline — every system emitter (PTAC, PSZ-AC, PSZ-HP,
PVAV, chilled-water plant variants, WLHP, …) repeats the same `cop_entry.get(key) or default`
pattern, and none of it leaves a provenance/confidence marker.

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| `cooling_cop` | Yes, or falsy (e.g. `0`) | `.get("cooling_cop") or 3.0` | 3.0 | none | B | `idf/hvac.py:125,168,206,248,299,351,383,428,462` |
| `heating_efficiency` | Yes, or falsy | `.get("heating_efficiency") or {0.8 gas / ~1.0 WLHP}` | 0.8 (gas) or ~1.0 (WLHP heat-pump COP) | none | B | `idf/hvac.py:169,207,249,300,352,385,503` |
| `fan_static_pa` | Yes, or falsy | `.get("fan_static_pa") or {622.5 / 1389.42 / 331.17}` (system-dependent) | See value | none | B | `idf/hvac.py:170,208,250,301,353,388,429,463` |
| `fan_total_efficiency` | Yes, or falsy | `.get("fan_total_efficiency") or {0.55575 / 0.6084 / 0.520}` | See value | none | B | `idf/hvac.py:171,209,251,302,354,389,430,464` |
| `vav_min_turndown` (VAV systems only) | Yes, or falsy | `.get("vav_min_turndown") or 0.30` | 0.30 | none | B | `idf/hvac.py:252,303` |

Note: this is `dict.get(key) or default`, **not** `dict.get(key, default)` — it substitutes
whenever the stored value is missing *or falsy*, not only when the key is truly absent.

### 2.7 DHW & cooking inputs

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| `footprint_area_m2` | Yes, or falsy | `.get("footprint_area_m2") or 400.0` | 400.0 m² | none | B | `idf/dhw.py:18-20`, `idf/cooking.py:20-21` |
| `num_floors` (not extractable from zone names) | Yes | Defaults to 1 | 1 | none | B | `idf/dhw.py`, `idf/cooking.py` |
| Archetype flagged `no_dhw`/`no_cooking` in bundled data | N/A — deliberate table-driven omission, not a guess | Load skipped entirely | 0 (no load emitted) | Table-driven, deliberate | A | `idf/dhw.py:43`, `idf/cooking.py:61` |

### 2.8 Simulation results (meters) inputs

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| Any of the 9 tracked EnergyPlus meters (e.g. all-electric building has no `Heating:NaturalGas`) | Yes | Pre-initialized to `0.0`; stays `0.0` if absent from SQL | 0.0 kWh | Code comment: *"0.0, not NaN"* | A (self-documented, physically correct) | `results/parser.py:100-119` |
| Zone HVAC variable naming mismatch (Ideal-Loads vs. metered) | Yes | Falls back to Ideal-Loads variable names | Parsed with older variable names | Parse status `failed_zone_mismatch` if neither found | A | `results/parser.py:187-200` |

### 2.9 Carbon / emission factor inputs

| Input | Can be missing? | Handling mechanism | Fallback | Provenance marker | Tier | Source |
|---|---|---|---|---|---|---|
| State/eGRID subregion not present in emissions table | Yes (any state/subregion outside coverage) | Hard fail — no fallback at all | — (raises) | — | C | `results/carbon.py:26-29` (`raise KeyError` — explicit per its own docstring) |

---

## 3. Gaps worth a decision

1. **HVAC parameter defaults carry no provenance flag.** Every other numeric-substitution site in
   Stages 1–2.2 leaves *some* trace (a flag token, a confidence downgrade, a named provenance
   value). HVAC (`idf/hvac.py`) does not — there is currently no way to query "which buildings in
   this run got fabricated COP/fan defaults vs. real archetype-sourced values." If HVAC realism
   numbers are ever challenged, there's no column to check.
2. **`.get(key) or default` substitutes on falsy-but-valid values, not just missing keys.** A
   stored `cooling_cop: 0` (nonsensical, but conceivable data-entry state) would silently become
   `3.0` with no distinction from a truly-absent key. Low real-world risk (COPs of exactly 0 aren't
   plausible source data) but worth knowing the pattern doesn't distinguish "absent" from "falsy."
3. **DHW/cooking's 400 m² / 1-floor defaults are silent.** Same instrumentation gap as HVAC, lower
   stakes (DHW/cooking is a smaller share of EUI than HVAC).
4. **Missing EPW path fails silently, not loudly.** Given how much every downstream result depends
   on the weather file, this arguably deserves Tier-C treatment (hard fail) rather than "IDF
   proceeds with EnergyPlus defaults" — worth confirming this is intentional rather than an
   oversight.
5. **Zoning fallback (`one_zone_per_floor`/`single_zone`) is warning-only,** unlike its Stage-1
   geometry-simplification sibling which appends to the queryable `data_quality_flag` column. A
   user who wants to know how many buildings got simplified zoning currently has to grep run logs,
   not a DataFrame column.

None of the above are "bugs" in the sense of the classification-threshold issue tracked in
`docs/docs_ACTIVE/misclassification/`; they are instrumentation gaps — the substituted values
themselves are reasonable engineering defaults, but nothing downstream can currently tell which
rows used them.

---

## 4. Resolution status — 2026-07-13 addendum (post-arc)

This audit is the **founding grounding document** of the input-imputation arc: its §3 gaps are what
the arc set out to close. Recording their resolution here keeps the audit complete and prevents a
future reader from treating already-closed gaps as still-open. (This addendum changes no code; it
only records what the arc's own phases — see `PLAN_input_imputation_implementation.md` §8 — did.)

| §3 gap | Resolution | Where |
|---|---|---|
| **1 — HVAC parameter defaults carry no provenance flag** | ✅ **CLOSED** by Phase A **T02** — HVAC Tier-B provenance gap closed; every `cop/fan/heating` default now leaves a tracked flag. Proven instrumentation-only: **25/25 IDFs byte-identical** vs the `e063865` baseline (exact local field-diff). | Phase A · `results/phase_A/RESULTS_phaseA.md` |
| **2 — `.get(key) or default` substitutes on falsy, not just missing** | ✅ **CLOSED** by Phase A **T02/T03** — the load-bearing conversion `.get(k) or d` → `.get(k, d)` + a tracked flag was the core Phase-A change; a stored falsy-but-valid value is no longer silently overwritten. | Phase A |
| **3 — DHW/cooking 400 m² / 1-floor defaults are silent** | ✅ **CLOSED** by Phase A **T03** — DHW/cooking Tier-B gap closed with the same tracked-flag treatment. | Phase A |
| **4 — Missing EPW path fails silently, not loudly** | ⏸ **OUT OF ARC SCOPE** — this is a Stage-2.3 climate/weather concern, not an input-imputation (morphology/semantic) target. Not addressed by this arc; remains an open decision for a future climate/geometry arc. | future arc |
| **5 — Zoning fallback (`one_zone_per_floor`/`single_zone`) is warning-only** | ⏸ **OUT OF ARC SCOPE** — Stage-1 geometry/zoning instrumentation, outside the imputation arc's morphology/semantic scope. Remains open. | future arc |
| **§2.2 note — rule-17a office size thresholds "wrong"** | ✅ **CLOSED** by the separate **E-R3-3** archetype-threshold fix (office size bins + school/hotel cut-points), now the adopted baseline. | `docs_DONE/misclassification/` |

**Net:** the three imputation-scoped instrumentation gaps (§3.1–§3.3, the Tier-B HVAC/DHW/cooking
"silent default" weak spot this audit flagged as its central finding) are **all closed** — that was
Phase A's mandate, discharged and validated. The two remaining open items (§3.4 EPW, §3.5 zoning) were
correctly scoped **out** of the imputation arc from the start; they are logged as future-arc candidates
in `PLAN_input_imputation_implementation.md` §9. This report is therefore **necessary and complete** as
the arc's origin audit and stays with the arc when it is filed to `docs_DONE`.

---

*OpenUBEM — informational audit. No code changed by this report. Scan: Haiku model;
verification and synthesis: manager session. 2026-07-01 · resolution addendum 2026-07-13.*
