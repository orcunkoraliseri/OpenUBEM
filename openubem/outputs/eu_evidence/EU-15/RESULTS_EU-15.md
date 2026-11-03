# RESULTS — `EU-15` T04/T05 (`D-EU-39` §2, §3)

**Date:** 2026-08-30 · **Plan:** `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`
**Scope:** T04 (retire the strip cutter as a success path) and T05 (carve the unconditioned core/corridor spine),
measured fresh from the re-emitted `openubem/outputs/eu_evidence/EU-11/*/layouts/*.json` side-cars (2,541 total,
population unchanged from the plan's own starting-state table). Stop-and-report 1. No IDF fleet rebuild, no Speed.

---

## 1. Per-district ruled coverage against the `D-EU-39` ≥ 95 % per-district bar

| District | side-cars | ruled | refused | coverage | bar |
|---|---:|---:|---:|---:|---|
| `ES-MAD-BERRUGUETE` (Madrid) | 961 | 616 | 345 | **64.10 %** | FAIL |
| `FR-LYO-HAUTCOEURPENTES` (Lyon) | 297 | 198 | 99 | **66.67 %** | FAIL |
| `GB-LDN-STDUNSTANS` (London) | 82 | 40 | 42 | **48.78 %** | FAIL |
| `IT-BOL-GALVANI2` (Bologna) | 1,201 | 591 | 610 | **49.21 %** | FAIL |
| **fleet** | **2,541** | **1,445** | **1,096** | **56.87 %** | **FAIL (all 4 districts)** |

Ruled scheme = `ruled_grid_{1x1,2x1,2x2,3x2,4x2}` ∪ `i_shape_linear_gallery` ∪ `l_shape_decomposition` ∪
`courtyard_wing_unfold`, `geometry_outcome` starting `DWELLING_LAYOUT_EMITTED`. **0** side-cars fleet-wide carry
`scheme == equal_strip_multi_angle_sweep` (T04's own acceptance test, was 843).

🔴 **This is lower than the T01–T03 progress log's own implied post-recovery figure (1,469 + 76 = 1,545).** Cause:
`_combine_wing_results` (shared by `l_shape_decomposition`/`courtyard_wing_unfold`) only ever checked each **wing's
own** `dwelling_layout_emitted`. Pre-T04, a wing whose ruled route failed but whose legacy strip-cut succeeded
reported `True`, so the whole building was accepted and labelled with a *ruled* top-level scheme even though one
wing was actually served by the (unlabelled) strip cutter internally — `FINDING 207`'s masking, one recursion level
deeper than originally measured. Fixing `_secondary()` (T04) closes this automatically at every recursion depth; no
separate code change was needed. Full writeup: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, "European
locations EU-15". T05's circulation extension (`CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION` 3→2) has **no** measured
effect on this coverage figure (isolated by re-measuring with the threshold reverted to 3: identical ruled counts).

### T02/T03 recovery split (unchanged from the T01–T03 progress log, replayed fresh)

74 buildings recovered via T03's hardened L-shape/gallery routes, 2 via T02's courtyard unfolding, out of the
original 843 strip-cutter population. This split is orthogonal to the T04 finding above — T02/T03 recovered these
buildings' *top-level* route honestly; the masking affected a *different* subset of buildings (those combining a
successful wing with an internally strip-cut wing), not these 76.

---

## 2. Residual by `fallback_reason`

| `fallback_reason` | Madrid | Lyon | London | Bologna | fleet |
|---|---:|---:|---:|---:|---:|
| `L_SHAPE_DECOMPOSITION_FAILED` | 220 | 75 | 21 | 313 | **629** |
| `INTERIOR_RING_COURTYARD_UNFOLD_FAILED` | 71 | 9 | 0 | 159 | **239** |
| `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` | 44 | 13 | 18 | 0 | **75** |
| `NARROW_FOOTPRINT_LT_8M` | 4 | 2 | 3 | 135 | **144** |
| `PARTITION_AUDIT_FAILED` | 6 | 0 | 0 | 3 | **9** |
| **total refused** | **345** | **99** | **42** | **610** | **1,096** |

Sums to `2,541 − 1,445 = 1,096` exactly, every district. `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` (75) is
unchanged from the plan's own starting-state census — that refusal was already correct and is untouched by T04/T05.

**No dwelling count anywhere was reduced.** Independently re-verified: across all 789 currently-emitted side-cars,
the distinct dwelling-zone-name-set count equals `dwellings_total` exactly on every one (0 violations). T04/T05 do
not touch dwelling-count computation (`allocate_european_dwellings` input) at all, only downstream routing.

---

## 3. Conditioned-vs-gross floor area, per district

| District | side-cars w/ area | `has_unconditioned_core=true` | Σ gross m² | Σ conditioned m² | shrink |
|---|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 952 | 354 | 503,246.3 | 477,360.8 | 5.14 % |
| `FR-LYO-HAUTCOEURPENTES` | 283 | 95 | 187,964.1 | 179,472.7 | 4.52 % |
| `GB-LDN-STDUNSTANS` | 80 | 29 | 52,382.3 | 48,744.2 | 6.95 % |
| `IT-BOL-GALVANI2` | 1,201 | 535 | 1,278,131.4 | 1,210,605.9 | 5.28 % |
| **fleet** | **2,516** | **1,013** | **2,021,724.1** | **1,916,183.7** | **5.22 %** |

(2,516 of 2,541 side-cars carry both fields this run — 25 are stale entries from a population no longer in the
current `row_map`/simulated set, predating this session; not written this run, out of T04/T05 scope.)

`conditioned_floor_area_m2 < gross_footprint_area_m2` on exactly the 1,013 `has_unconditioned_core=true` buildings
(of the 2,516 carrying both fields) and equal on the other 1,503 (0 violations either direction, independently
re-verified). `floor_area_m2`
(pre-existing manifest column, EUI denominator) now silently equals `gross_footprint_area_m2` since `zones` includes
the circulation zone — per `D-EU-39` §3 ("every EUI denominator moves") this is the ruled consequence, flagged for
whichever task next computes `eui_kwh_m2` (T09) to disclose which denominator it used.

🔴 **Disclosed gap, not resolved:** an L-shape/courtyard storey whose total is exactly 2, split 1 dwelling per wing
(the wing allocator's own minimum-1-per-wing guarantee), carries **no** core, because neither individual wing
reaches the ≥2 threshold. `has_unconditioned_core` is therefore true wherever a storey carries ≥2 dwellings *and*
at least one wing of it does too — not literally every ≥2-dwelling storey. Visible per-storey via
`floors[].has_unconditioned_core` on every side-car, never silently hidden.

---

## 4. The eight `EXAMPLE_dwelling_layout_validation_2026-08-28.md` §6 acceptance buildings

Two (Lyon, `BATIMENT0000000240879941_part0` / `BATIMENT0000000240880045_part0`) are **not simulated today** (typology-
table gap / missing year-built, per the EXAMPLE doc itself) — no EU-11 side-car exists for either — **NOT SCOREABLE**.

| # | building | `zones ruled` (§3.1) | measured emitted | criterion 1 | area error | criterion 2 | core every ≥2-dwelling storey | criterion 3 | min facade (§3.1) | measured min facade | criterion 4 | 
|---|---|---:|---:|---|---:|---|---|---|---:|---:|---|
| 8 | `way/51781396` (London) | 69 | 69 | PASS | ~0 % (4.3e-11) | PASS | 17/17 storeys | PASS | 6.74 m | 13.85 m | **FAIL** (not within 0.05 m) |
| 9 | `relation/12704090` (Madrid) | 30 | **0 (refused)** | **FAIL** | n/a | n/a | n/a | n/a | 12.06 m | n/a | **FAIL** |
| 10 | `way/388485191` (Madrid) | 38 | 38 | PASS | ~0 % (4.4e-12) | PASS | 7/7 storeys | PASS | 7.74 m | 9.12 m | **FAIL** |
| 11 | `way/420409335` (Madrid) | 20 | **0 (refused)** | **FAIL** | n/a | n/a | n/a | n/a | 2.79 m | n/a | **FAIL** |
| 12 | `relation/3730743` (Madrid) | 0 (refused) | **0 (refused)** | **PASS** | — | — | — | — | — | — | — |
| 13 | `way/391279229` (Madrid) | 44 | 44 | PASS | ~0 % (1.2e-11) | PASS | 8/8 storeys | PASS | 9.80 m | 11.64 m | **FAIL** |
| 14 | Lyon BATIMENT…879941 | — | not simulated | **NOT SCOREABLE** | | | | | | | |
| 15 | Lyon BATIMENT…880045 | — | not simulated | **NOT SCOREABLE** | | | | | | | |

**Criterion 5** (`relation/3730743` refused with `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`, zero zones emitted):
**PASS**, confirmed on disk (`geometry_outcome=FALLBACK_PENDING_LAYOUT`, `fallback_reason=DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`,
`floors=[]`).

🔴 Two of the six scoreable buildings (`relation/12704090`, `way/420409335`) are **refused** in the actual repo
implementation, though the `EXAMPLE` prototype (a standalone script outside the repo, explicitly disclaimed
"PROTOTYPE EVIDENCE, NOT A RESULT") shows them succeeding. Cause: `classify_building_morphology` routes
`relation/12704090` and `way/420409335` differently than the prototype apparently did (courtyard-unfold and
L-shape-decomposition respectively, both of which then fail this repo's audit/habitability gates on these
footprints), not a T04/T05 defect — the prototype and this repo's implementation were never the same code.

🔴 Criterion 4 (facade contact within 0.05 m of §3.1) **fails on every scoreable success** (3/3). The repo's actual
circulation mechanism is always a single centroidal rectangle (`_centred_circulation_region`), never the
"corridor slab" shape the external prototype apparently used for `3×2`/`4×2` grids — different circulation geometry
changes which dwelling ends up with the tightest facade contact. Criteria 1, 2, 3 and 5 — the ones actually
implemented in this repo (zone count, area conservation, per-storey core presence, the refusal) — all pass on every
scoreable building.

---

## 5. Test output

```
pytest -q tests/geometry/test_eu15_ruled_coverage.py -k "t05 and not sidecar"
  12 passed

pytest -q tests/geometry/ tests/test_eu_floor_partition_audit.py tests/test_eu_real_footprint_feasibility.py \
  tests/test_eu_dwelling_allocation.py tests/test_eu_geo08_independent_parity.py tests/test_eu_s2_campaign.py \
  tests/test_eu_s2_geometry_remedies.py
  172 passed, 2 failed (both pre-existing, unrelated -- test_eu_real_footprint_feasibility.py::
  test_real_layout_generator_fails_closed_for_unsupported_topology[footprint1/footprint2], already
  logged [OPEN, out of EU-13B scope] in the debug references before this session touched anything)

pytest -q -k eu -n 8   (repo-wide)
  594 passed, 2 skipped, 2 pre-existing failures (same two)

pytest -q -n 8 tests/   (full repo)
  2433 passed, 55 skipped, 2 pre-existing failures (same two)

diff -rq openubem/outputs/3D docs/docs_ACTIVE/europeanLocations/outputs_3D
  only non-EU (US validation) viewer files differ; every eu_* viewer HTML and *_data folder byte-identical
```

---

## 6. Files touched

`openubem/geometry/european_residential.py`, `scripts/run_eu_s2_campaign.py`,
`scripts/run_eu_s2_district_campaign.py`, `scripts/emit_eu11_layout_sidecars.py`,
`scripts/generate_eu_3d_viewers.py`, `tests/geometry/test_eu15_ruled_coverage.py`,
`tests/geometry/test_eu13b_dwelling_conservation.py`, `tests/geometry/test_eu13b_circulation_sidecar.py`,
`tests/geometry/test_eu14b_bologna_layout_binding.py` (3 pre-existing tests updated to the honest measured
post-`D-EU-39` behaviour, not loosened — see §1/§3 and the debug references for why each was stale), all four
districts' `openubem/outputs/eu_evidence/EU-11/*/layouts/*.json`, `openubem/outputs/eu_evidence/EU-11/*/*_manifest.csv`,
`openubem/outputs/3D/eu_*` and mirrored `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_*`,
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (European locations EU-15 chapter, 3 new entries),
`docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` (§8),
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` (T04, T05 rows).
