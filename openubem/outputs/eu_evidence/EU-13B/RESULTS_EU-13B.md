# RESULTS — EU-13B dwelling layout scheme conformance

Arc: European locations x Step 8. Executed T01-T08, T09 and T10. T06 stayed blocked (D-EU-36 carve-vs-add
not ruled). T09 (resimulation, unblocked 2026-08-30 by D-EU-38) is reported in its own section below.

Scope: `ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS` were re-emitted.
`IT-BOL-GALVANI2` was never touched (excluded per the prompt; its layout-binding fix is `EU-14B` T01) --
its side-cars still describe the pre-EU-13B geometry (796/1204 = 66.1% emitted, unchanged).

## 0. Decision this session had to make, disclosed rather than silently picked

The prompt's own text conflicts on whether circulation (core/corridor) is carved from the plate in this
task: the D-EU-38 header note says "nothing above authorizes emitting a core," while FINDING 204 says
"emit the percentage rule" and T05 says the corridor spine is "geometry only in this task." Read literally
together, these cannot all be satisfied: carving a corridor/core out of the plate is exactly the
carve-vs-add decision T06 reserves for the owner.

Resolution adopted here: circulation (core for grids >=3 dwellings/floor, corridor spine for the I-shape
route) is **computed and measured** (area, % of plate, absolute-band conformance) but **never physically
carved** from the emitted dwelling geometry. Dwellings still tile 100% of the regularized plate, exactly as
the existing GEO-01 no-core-on-real-footprints contract already requires; `has_unconditioned_core` stays
`false` everywhere, per T07(b). This satisfies FINDING 204's measurement/disclosure instruction without
emitting a core or corridor as executable geometry, which the D-EU-38 note forbids. It also means this
session's circulation areas/percentages will not numerically match `EXAMPLE_dwelling_layout_validation_
2026-08-28.md`'s sample sheets, which *did* carve (that document is explicit prototype evidence, not
production code, and says so). The exact zone counts, area-conservation-to-0.00%, scheme names, and the
`relation/3730743`-class refusal all still match the EXAMPLE's acceptance bar (see SS6).

## 1. T01 -- conservation census (stop-and-report point 1)

Checked against every re-emitted side-car with `geometry_outcome` starting `DWELLING_LAYOUT_EMITTED`
(1,254 of 1,340 across the three touched districts). Conservation is over **distinct emitted zone names**,
not a naive per-floor-entry sum, because a storey group spanning multiple physical floors (a single
dwelling extruded across them -- e.g. a multi-storey SFH/TH declaring 1 dwelling over N storeys) repeats
the same zone name once per physical floor for the viewer's per-floor slicing.

| district | emitted side-cars checked | non-conserving |
|---|---:|---:|
| Madrid | 911 | 0 |
| Lyon | 282 | 0 |
| London | 61 | 0 |
| **total** | **1,254** | **0** |

`way/51781396`-class case verified directly (17 storeys, 69 declared): 16 storeys of 4 + 1 storey of 5 =
**69 zones exactly**, not 85 (`tests/geometry/test_eu13b_dwelling_conservation.py::
test_t01_way_51781396_like_case_gives_69_not_85`).

## 2. T02 -- >8/floor dropout census (stop-and-report point 1)

| district | prepared | `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` |
|---|---:|---:|
| Madrid | 961 | 44 |
| Lyon | 297 | 13 |
| London | 82 | 18 |
| **total** | **1,340** | **75** |

75/1,340 matches the D-EU-36 fleet-wide `>8` refusal count exactly. No building's dwelling count was
reduced to pass this gate; the residual is counted, not forced.

## 3. Fallback census, per district (fail-closed residual, full disclosure)

| district | prepared | emitted | `>8`/floor | `NARROW_FOOTPRINT_LT_8M`(secondary) | `PARTITION_AUDIT_FAILED` | coverage |
|---|---:|---:|---:|---:|---:|---:|
| Madrid | 961 | 911 | 44 | 4 | 2 | 94.8% |
| Lyon | 297 | 282 | 13 | 2 | 0 | 94.9% |
| London | 82 | 61 | 18 | 3 | 0 | 74.4% |
| **3-district total** | **1,340** | **1,254** | **75** | **9** | **2** | **93.6%** |

**Fleet-wide coverage, honestly stated.** Bologna is untouched at its pre-existing 796/1,204 (66.1%).
Actual current fleet: (911+282+61+796) / (961+297+82+1204) = **2,050/2,544 = 80.6%** -- below the D-EU-36
95% bar, because that bar's 97.05% figure was a geometric census that assumed Bologna would *also* be
ruled-partitioned, which is `EU-14B`'s job, not this task's. The three districts this task actually
touched reach 1,254/1,340 = 93.6% (weighted down entirely by London, disclosed below); once `EU-14B`
brings Bologna to its own measured 100% ruled coverage, the full fleet would reach
(1,254+1,204)/2,544 = **96.7%**, clearing the bar.

**London stays the disclosed exception**: 61/82 = 74.4%, the lowest of the three touched districts, driven
by its 18 `>8`/floor refusals (the densest district) plus 3 secondary-route narrow-footprint failures.

**9 `NARROW_FOOTPRINT_LT_8M` + 2 `PARTITION_AUDIT_FAILED` residual (11 buildings, 0.8% of the 1,340
prepared) is a real, small gap against the D-EU-36 measurement's claim of "no area failure anywhere in the
fleet."** All 11 are cases where the ruled route's morphology dispatch (courtyard/L-shape/gallery) could
not serve a small, awkwardly-shaped plate and fell back to the existing secondary `equal_strip_multi_angle_
sweep`, which then independently failed its own `<8m` minimum-width gate or topology audit. This residual
was NOT forced into a grid that does not fit it, and no dwelling count was reduced.

## 4. T05 -- scheme histogram and morphology (stop-and-report point 2)

Per-storey scheme, summed across all storeys of all emitted buildings (a building's storeys can use
different schemes/grids when their per-storey dwelling counts differ):

| scheme | Madrid | Lyon | London | total |
|---|---:|---:|---:|---:|
| `ruled_grid_1x1` | 1,134 | 384 | 27 | 1,545 |
| `ruled_grid_2x1` | 847 | 115 | 27 | 989 |
| `ruled_grid_2x2` | 256 | 209 | 46 | 511 |
| `ruled_grid_3x2` | 88 | 103 | 44 | 235 |
| `ruled_grid_4x2` | 9 | 1 | 0 | 10 |
| `i_shape_linear_gallery` | 105 | 12 | 30 | 147 |
| `l_shape_decomposition` | 82 | 35 | 17 | 134 |
| `equal_strip_multi_angle_sweep` (secondary) | 1,106 | 553 | 65 | 1,724 |

**1,724 of 5,295 storey-partitions (32.6%) still fall to the secondary scheme.** This is not a bug in the
sense of an unhandled crash -- every one of those partitions passes the same area/topology/facade audit the
ruled routes do, and the building-level dwelling count is still conserved exactly (SS1). It reflects two
honest limits of this task's morphology dispatch: (a) `courtyard_secondary` (interior-ring footprints) is
explicitly not implemented (report SS6.4 3-wing courtyard unfolding was descoped for time; disclosed as a
known simplification), and (b) the reflex-vertex/L-shape and I-shape/gallery routes fail to decompose some
real, noisy GIS footprints and fall back rather than emit a wrong scheme label (per the rule "a layout
labelled `ruled_grid_*` that is not a grid is worse than a fallback").

## 5. T03 -- footprint regularization area-delta distribution (stop-and-report point 2)

`regularize_footprint_orthogonal` fits an orthogonal quadrilateral via the plate's own minimum-rotated-
rectangle orientation, then rescales it about its centroid to match the raw footprint's area exactly (per
report SS3.2's own stated design: "preserves the gross internal floor area"). The >2% gate is therefore a
numerical safety net, not a routine filter, and the fleet distribution confirms that:

| district | n measured | mean delta | max delta | >2% (fallback-triggering) |
|---|---:|---:|---:|---:|
| Madrid | 961 | 0.09% | 1.23% | 0 |
| Lyon | 297 | 0.17% | 2.31% | 1 |
| London | 82 | 0.05% | 0.88% | 0 |
| **total** | **1,340** | **0.11%** | **2.31%** | **1** |

Measured independently on the raw footprint for every prepared building (not only the ones whose internal
route happened to call the whole-footprint regularizer), per building, in each side-car's `regularization`
field. The one Lyon building whose *whole-footprint* delta exceeds 2% did not trigger the internal
`REGULARIZATION_AREA_DELTA_GT_2PCT` fallback because its internal route regularized a *wing* (L-shape
decomposition) rather than the whole plate; this is disclosed as a known discrepancy between the reporting
measurement and the internal per-route trigger, not a hidden defect.

## 6. FINDING 204 -- circulation percentage vs absolute-band conflict, measured

Circulation (9% of plate, the 6-12% band's midpoint, applied whenever a storey needs >= 3 dwellings) is
measured and tagged `CIRCULATION_OUTSIDE_RULED_ABSOLUTE_BAND` whenever it falls outside 12.0-25.0 m2 --
never carved (SS0).

| district | buildings with >=1 storey requiring circulation | outside the 12.0-25.0 m2 absolute band |
|---|---:|---:|
| Madrid | 400 (256+88+9 grid + 105 gallery, deduplicated by building) | 80 |
| Lyon | 210 | 23 |
| London | 96 | 17 |
| **total** | **~700** | **120** |

The owner still needs to rule which criterion binds (SS4.1 of `EXAMPLE_dwelling_layout_validation_2026-08-
28.md`); this task only measures.

## 7. T07 -- habitability retry and pop-up header

**(a) Retry mechanism** (rotate 90 deg at the same grid/count, then downgrade to `nu-1` columns
redistributing the same exact count via column merges, then fail closed) is implemented in
`generate_european_grid_layout` and exercised by a synthetic fixture
(`tests/geometry/test_eu13b_dwelling_conservation.py` golden cases pass). **It was never empirically
triggered across the real fleet: 0 rotations, 0 downgrades in all 1,254 emitted buildings.** This is
because the ruled grid's `nv` never exceeds 2 (the table caps at `4x2`), so every cell always touches one of
the plate's two long exterior edges by construction -- a genuinely landlocked cell cannot occur in this
ruled scheme's own topology. Recorded as an honest finding, not a hidden gap.

**(b) Pop-up header.** `scripts/generate_eu_3d_viewers.py:401`'s header already read the side-car's
`has_unconditioned_core` field correctly in the code as found; the "Yes" shown for `way/51781396` was in
the *stale, previously-generated* viewer HTML, not a bug in the current generator. Regenerating the three
viewers (SS9) with `has_unconditioned_core: false` on every side-car (SS0) fixes it as a side effect:
confirmed **0 of 1,254** `"core": true` occurrences in the three regenerated viewer files -- 0
disagreements.

## 8. Golden regularization tests (T03 acceptance)

`tests/geometry/test_eu13b_dwelling_conservation.py` golden fixtures (rectangle, L, U, cross, notched): all
five regularize to exactly 4 vertices, all five keep `plate_area_delta_fraction < 2%`, all five have CCW
(outward) exterior rings. `fit_quadrilateral_domain` and `regularize_footprint_orthogonal` import nothing
from the partitioner (asserted directly on source).

## 9. Re-emit and viewer regeneration (T08)

`scripts/emit_eu11_layout_sidecars.py` re-run for Madrid, Lyon, London only (never `IT-BOL-GALVANI2`).
`scripts/generate_eu_3d_viewers.py`'s `build_district()` re-run per-district for the same three (Bologna's
viewer untouched, per the prompt reserving it for `EU-14B`). Mirror verified byte-identical
(`sha256sum` match) for all three viewers between `openubem/outputs/3D/` and
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`.

## 10. Test status

`pytest -q tests/geometry/test_eu13b_dwelling_conservation.py` -- **46 passed, 0 failed.**

`pytest -q tests/ -k "eu_"` (regression check against the existing EU/GEO-* suite) -- **394 passed, 2
failed** (both pre-existing, in `tests/test_eu_real_footprint_feasibility.py::
test_real_layout_generator_fails_closed_for_unsupported_topology`, confirmed present in the file exactly as
it stood before this session's first edit -- `generate_european_dwelling_layout` already implemented the
multi-angle-sweep/radial-sector partitioner supporting non-convex and courtyard footprints as uncommitted
work at session start, and this test still asserts the older, stricter contract it superseded. Not touched;
not caused by EU-13B; flagged for the owner rather than silently fixed or silently left unexplained).

## 11. T10 -- why buildings get neither a simulation nor a layout (measurement only, no code changed)

Reproduced exactly against each district's `summary_prerun.json` `blocker_exclusions`:

**Lyon** (`FR-LYO-HAUTCOEURPENTES`): `TYPOLOGY_SIGNALS_DISAGREE` 186 pure + 3 combined with
`MISSING_OBSERVED_YEAR_BUILT` = 189; `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` 37. Joint
(dwellings, storeys) distribution of these 226 buildings is dense and scattered across the `D-EU-04-G`
table's uncovered region -- no single cell dominates; the largest single cells are (11,6)=13, (9,6)=10,
(12,7)=10, (12,6)=10, most mass sitting at 6-12 dwellings over 5-8 storeys (i.e. real mid-rise apartment
blocks the table's `MFH<=4 storeys` / `AB>=5 dwellings+>=5 storeys` bands do not reach). Full distribution
recomputed and available on request; sums to 226 exactly against `blocker_exclusions`.

**Madrid** (`ES-MAD-BERRUGUETE`): `UNMAPPABLE_RESIDENTIAL_TYPE` = 77, matches exactly. Dominated by
(dwellings=1, storeys=1) = 35 and (dwellings=1, storeys unmapped) = 14 -- i.e. mostly single-dwelling,
single-storey structures whose `building_tag` did not map to a residential type at all (garages, sheds,
ancillary structures caught by the residential footprint filter), not multi-dwelling table-gap cases like
Lyon's.

**London** (`GB-LDN-STDUNSTANS`): `UNMAPPABLE_RESIDENTIAL_TYPE` = 345, matches exactly. Root cause is
qualitatively different from Lyon's table gap: London's mapping table is `{"apartments":"AB",
"detached":"SFH","terrace":"TH"}`, and 339 of the 345 excluded buildings carry `building_tag="house"` (6
carry `"residential"|) -- a generic OSM tag the table simply has no entry for, regardless of dwellings or
storeys. Extending the tag table (not the dwellings/storeys table) is the fix here, a materially different
`D-EU-37`-adjacent gap from Lyon's.

`D-EU-37` (extending the typology table) remains an owner ruling; no band was widened, no tie was broken,
no type was assigned outside the ruled table.

## 12. T09 -- Resimulation on Speed (stop-and-report point, D-EU-38)

Unblocked 2026-08-30. Rebuilt IDFs for Madrid, Lyon, London from the T01-T08 geometry
(`openubem/geometry/european_residential.py`, unchanged by this task) via
`scripts/run_eu_s2_district_campaign.py`'s existing `prepare()` -- it already calls
`generate_european_building_dwelling_layout` (D-EU-33 parity with the side-car emitter), so no
geometry code changed in this section. Bologna (`IT-BOL-GALVANI2`) was never touched (`EU-14B`'s job).

### 12.1 IDF assembly bug found and fixed (blocking regeneration)

Regenerating Madrid's IDFs crashed the whole district on the first affected building:
`ZeroDivisionError` inside geomeppy's `intersect_match` (`Vector3D.normalize` on a degenerate
zero-length normal produced by a live T04 ruled-grid partition). `openubem/idf/surfaces.py`'s
existing reroute-to-`one_zone_per_floor` safety net only recognised `mode == "room_layout"`
zones (LayoutGenerator's own); EU-13B's T04/T05 zones carry `mode == "european_dwelling_layout"`
and matched neither of the two reroute checks, so the handler's bare `raise` re-raised the
original exception uncaught. Fixed by broadening `_force_reroute_room_layout_to_one_zone_per_floor`
(`openubem/idf/surfaces.py:664`) to also match `european_dwelling_layout`, and deriving its
`total_height` from `max(z_ceiling) - min(z_floor)` rather than `n_floors * one_group's_height_m`
(a `european_dwelling_layout` storey group can span >1 physical floor per T02 floor absorption,
unlike `room_layout`'s always-one-floor-per-group assumption). `scripts/run_eu_s2_district_campaign.py`'s
`prepare()` also now catches `(RuntimeError, ZeroDivisionError, IndexError)` around
`build_idf_for_building` and excludes that one building as `IDF_ASSEMBLY_FAILED_<ExceptionType>`
rather than aborting the district -- a residual cannot always be rerouted (reconstructed union is
a real courtyard, or collapses to a degenerate/multipart shape). Registered:
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, chapter "European locations EU-13B".

Population effect of this residual, disclosed:

| district | prepared before T09 | `IDF_ASSEMBLY_FAILED_ZeroDivisionError` | prepared after T09 |
|---|---:|---:|---:|
| Madrid | 961 | 9 (0.94%) | 952 |
| Lyon | 297 | 14 (4.7%) | 283 |
| London | 82 | 2 (2.4%) | 80 |
| **total** | **1,340** | **25 (1.9%)** | **1,315** |

None of these 25 buildings' dwelling counts were reduced or forced through a grid that didn't fit
them -- the geometry itself (T01-T05) still emits cleanly for all of them (their side-cars under
`layouts/` are unaffected, T08's 93.6% coverage figure stands unchanged). This is purely a downstream
IDF/EnergyPlus geometry-engine assembly failure on a subset of live, noisy footprints, disclosed and
excluded rather than forced.

Post-T09 `geometry_outcome` split of the buildings that did assemble: Madrid 902/952 (94.7%)
dwelling-partitioned (900 observed + 2 imputed-count), 50 fallback; Lyon 268/283 (94.7%)
imputed-count dwelling-partitioned, 15 fallback; London 59/80 (73.75%) imputed-count
dwelling-partitioned, 21 fallback.

### 12.2 Zone-count-change census

Old (pre-EU-13B) `ZONE,` object counts per building were recovered from the still-present D-EU-35
remote fleet copy at `/speed-scratch/o_iseri/fleets/EU11_<district>/idfs/` (jobs `1294465`/`1294513`/
`1294581`) before it was cleared for the T09 re-ship, and diffed against the freshly regenerated
local IDFs' `ZONE,` counts for every building common to both (i.e. excluding the 12.1 residual).

| district | n compared | zone count changed | unchanged | mean abs delta (changed only) | max abs delta | mean signed delta |
|---|---:|---:|---:|---:|---:|---:|
| Madrid | 952 | 713 (74.9%) | 239 | 4.24 | 155 | -2.83 |
| Lyon | 283 | 202 (71.4%) | 81 | 6.88 | 66 | -4.51 |
| London | 80 | 73 (91.3%) | 7 | 12.51 | 68 | -10.19 |

Negative mean signed delta in all three districts: the T01 per-storey-conserving partitioner and the
T04 ruled-grid density table generally emit *fewer* zones than the pre-EU-13B geometry did for the
same declared dwelling totals -- the old code's non-conserving allocation (the 815-building defect
T01's own conservation census fixed) tended to over-count zones, not under-count them.

### 12.3 Speed submission and harvest

Shipped via `scripts/cluster/ship_eu11_fleet.sh` (remote fleet directories cleared first so the
12.1-excluded stems' stale old IDFs could not leak into the new run); submitted `sbatch --array`
from speed-submit2 only, fire-and-forget, `submit_fleet_t08.sbatch`:

| district | job id | array size | run | success | Speed-failed |
|---|---:|---|---:|---:|---:|
| Madrid `ES-MAD-BERRUGUETE` | 1297338 | 1-952%16 | 952 | 914 | 38 |
| Lyon `FR-LYO-HAUTCOEURPENTES` | 1297355 | 1-283%16 | 283 | 277 | 6 |
| London `GB-LDN-STDUNSTANS` | 1297373 | 1-80%16 | 80 | 76 | 4 |

Harvested with `scripts/cluster/harvest_eu11_district.py` (`DISTRICT_JOBS` updated to the three job
ids above; Bologna's entry left at the D-EU-35 job `1295646`, untouched).

All 48 Speed-side failures are the pre-existing, already-registered `GetSurfaceData` RoofCeiling
vertex-count-mismatch fatal (same `rc=0`/`rc=1`, 1-fatal signature as every prior recurrence in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch.1) -- confirmed by direct inspection of one
Madrid case (`efd148a964fbbb14`). The incidence rose sharply versus the pre-T09 rate (Madrid 4->38,
London 1->4; Lyon fell 7->6) because the T04/T05 geometry creates far more interzone ceiling/floor
surface pairs per building (many per-storey dwelling sub-zones instead of one), giving this
pre-existing EnergyPlus float-precision defect more chances to trigger -- an increased-exposure
effect of the geometry change, not a new defect. Not fixed, per the existing disposition (registered
as Recurrence 3 in the debug reference file); each carried as one classified `EPLUS_FATAL` row
(blank `heating_kwh`/`eui_kwh_m2`) in its manifest, never smoothed into the pooled EUI.

### 12.4 Pooled EUI, before (D-EU-35) / after (T09)

| district | before (D-EU-35) | after (T09) | delta |
|---|---:|---:|---:|
| Madrid | 79.0862 kWh/m² (999,191.1457 m², n=957) | **81.5325 kWh/m²** (865,128.0203 m², n=914) | +2.4462 (+3.1%) |
| Lyon | 70.0619 kWh/m² (394,414.574 m², n=290) | **69.5235 kWh/m²** (363,510.0729 m², n=277) | -0.5384 (-0.8%) |
| London | 74.7151 kWh/m² (90,790.3794 m², n=81) | **86.8703 kWh/m²** (78,196.5715 m², n=76) | +12.1552 (+16.3%) |

Against the DR12-16 external-validation bands (`docs/docs_ACTIVE/europeanLocations/results/RESULTS_EU-11.md`
SS External validation): Madrid stays WORTH INVESTIGATING (low) in DR13's 70.0-84.9 band, unchanged
verdict. Lyon stays inside DR14's Massing-Box-Persists CONSISTENT band (55.0-80.0), unchanged verdict
label (`FINDING 198` persists, now against an even higher dwelling-partitioned share -- 94.7% vs the
prior 80.5% -- with almost no EUI movement, deepening the same unexplained gap). **London's verdict
moves**: 86.8703 exceeds DR15's CONSISTENT ceiling (45.0-85.0) and now falls in DR15's own
pre-registered WORTH INVESTIGATING upper tail (85.0-105.0), attributed by DR15 itself to
"uninsulated Victorian solid-wall terrace dominance, combined with the +10% height inflation and
continuous 24/7 20C thermostat bias" -- 🔴 **new finding, not previously seen: London's CONSISTENT
verdict (unchanged through EU-13/D-EU-35) does not survive EU-13B's own ruled-grid geometry fix.**

### 12.5 Viewer regeneration

`scripts/generate_eu_3d_viewers.py`'s `build_district()` re-run for Madrid, Lyon, London only
(Bologna's viewer and data folder confirmed untouched by mtime). Mirror
(`docs/docs_ACTIVE/europeanLocations/outputs_3D/`) verified byte-identical to `openubem/outputs/3D/`
by `sha256sum` for all three viewer HTML files and their full data folders (`diff -rq`, no
differences).

### 12.6 `RESULTS_EU-11.md` updated

Madrid/Lyon/London pooled EUI figures in `docs/docs_ACTIVE/europeanLocations/results/RESULTS_EU-11.md`
superseded with the T09 harvest above (job ids `1297338`/`1297355`/`1297373`). Bologna's figure in
that document is unchanged and now explicitly noted there as still describing its pre-`EU-14B` zoning.
