# E-UTCI-09 Data-Gap Investigation — Completion Report

**Date:** 2026-07-25 · **Plan:** `PLAN_e-utci-09_investigation.md` · **Checkpoint:** CP-INV
**Status:** **investigation complete, findings synthesized, awaiting manager scoping of a follow-up
Stage-1 implementation plan.**

> **No fix has been implemented and no candidate has been adopted.** This plan was investigation-only
> by construction (§1 rule 2). It ends OPEN.

---

## 1. Headline finding (plain language)

**E-UTCI-09 is a narrow, upstream, field-level data gap — not a pipeline defect, and not a broader
data-acquisition failure.** Across all 12 validated cluster cells and 12,809 buildings, everything
except the height fields is healthy: zero invalid, empty, or non-Polygon geometries anywhere,
plausible row counts, sane footprint-area ranges, and sensible `building_tag` distributions in every
cell including the four affected ones. Only `height_m` and `levels` are degraded, and the split is
cleanly bimodal — eight cells between 0.67 % and 26.09 % missing, then a 58-percentage-point gap,
then four cells between 84.50 % and 100.00 % — with no borderline case in between. The cause is
differential live OSM community-tagging density at the queried coordinates (the acquisition code
path is identical for all 12 cells, F-07), propagated unchanged by `_flatten_tags`, which sets
`height_m = NaN` unconditionally when the `height` tag is absent from the fetched tag set (F-01), and
first acted upon — correctly and visibly — at Stage 6's `.notna()` exclusion (F-06). **The decisive
new result is negative: the platform's existing height-imputation infrastructure cannot fix this.**
`spatial_impute.py`'s `knn_fill` fills exactly zero rows in the three fully-affected cells at every
search radius from 100 m to 1000 m, because every candidate donor is itself missing `height_m` by
construction. That is the MNAR guard working exactly as designed, not failing — so "just wire up the
imputer we already have" is off the table as a standalone fix.

---

## 2. Per-task outcome

| Task | Outcome | Key result |
|---|---|---|
| **I01** — Full 12-cell characterization | ✅ Complete | Gap confirmed cleanly scoped to `height_m`/`levels`; distribution bimodal with no borderline cell; F-08's 5-cell spot-check reproduced exactly; 0 invalid geometries across all 12,809 rows |
| **I02** — External height data source survey | ✅ Complete | 10 candidates assessed by documentation reading only; **Microsoft Global ML Building Footprints** strongest; surfaced that 2 of the 4 tracts are geographically outside NYC |
| **I03** — Structural test of `spatial_impute.py` | ✅ Complete | MNAR guard rejects all 3 fully-NaN cells at every radius 100–1000 m; `austin_centre` partially fillable; **new defect E-UTCI-10** found |
| **I04** — Candidate fix shapes synthesis | ✅ Complete | 6 candidate shapes ranked; split strategy indicated; **none adopted** |
| **CP-INV** — Director synthesis | ✅ Complete | Plan remains **OPEN**, handed back for follow-up scoping |

**Audit note.** Every load-bearing employee claim was independently re-derived by the director in a
separate process before being accepted: I01's NaN/geometry/area statistics were re-read from the
`.gpkg` fixtures for four cells (exact match to two decimals); I03's imputer behaviour was re-run by
re-importing the real `knn_fill` (exact match on every field, including the silent-no-donor counts);
I02's coordinates were re-read from `CELL_CONFIGS`. `git status` confirms no diff to
`openubem/acquisition/*.py`, `openubem/semantic/*.py`, `openubem/microclimate/*.py`, or
`openubem/config.py` attributable to this investigation — the one `config.py` modification predates
it and contains only LayoutAssigner T08 and UTCI T01 blocks, nothing imputation-related.

---

## 3. I01 — Full 12-cell characterization (the scope-confirmation result)

Independently derived from `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`,
read-only. Sorted by `height_m` NaN % ascending.

| cell | rows | `height_m` NaN % | `levels` NaN % | footprint area m² min/mean/max | invalid/non-poly/empty/null geoms |
|---|---|---|---|---|---|
| la_rural | 149 | 0.671 | 97.987 | 28.31 / 509.08 / 22443.66 | 0/0/0/0 |
| la_suburban | 1343 | 1.117 | 99.553 | 20.08 / 194.98 / 6869.20 | 0/0/0/0 |
| nyc_urban | 1779 | 2.248 | 99.044 | 20.39 / 176.77 / 11077.47 | 0/0/0/0 |
| la_urban | 618 | 6.796 | 94.984 | 23.37 / 773.03 / 10330.11 | 0/0/0/0 |
| austin_urban | 425 | 11.059 | 99.059 | 20.87 / 572.04 / 22109.98 | 0/0/0/0 |
| nyc_centre | 738 | 16.396 | 81.572 | 21.28 / 1143.41 / 155536.02 | 0/0/0/0 |
| la_centre | 226 | 19.912 | 65.044 | 20.05 / 1833.95 / 17661.13 | 0/0/0/0 |
| austin_suburban | 437 | 26.087 | 89.474 | 20.07 / 273.84 / 6972.27 | 0/0/0/0 |
| *— 58 pp gap, no cell between 26 % and 84 % —* | | | | | |
| **austin_centre** | 413 | **84.504** | 71.429 | 24.28 / 1013.05 / 8225.32 | 0/0/0/0 |
| **nyc_suburban** | 1589 | **100.000** | 100.000 | 20.52 / 114.64 / 5132.61 | 0/0/0/0 |
| **nyc_rural** | 198 | **100.000** | 100.000 | 21.87 / 243.86 / 3884.80 | 0/0/0/0 |
| **austin_rural** | 245 | **100.000** | 99.592 | 34.89 / 631.49 / 10992.63 | 0/0/0/0 |

Cross-check against the T26 harvest CSV: `disc_n = 0` for all 12 cells (exact row-count match),
percentages agreeing to within ±0.0005 pp (display rounding only).

**Other columns are not implicated.** Broadly-sparse columns (`year_built`, `postcode`,
`roof_height_m`, plus the empty-string-sentinel `function_tag`/`roof_shape`) are sparse *uniformly
across both clusters* and do not correlate with the height split — e.g. `la_urban` (good cluster,
6.8 % height NaN) has 95.8 % `postcode` NaN, while `austin_centre` (bad cluster, 84.5 % height NaN)
has only 46.2 %. Methodological caveat worth carrying forward: `function_tag` and `roof_shape` use an
empty-string sentinel rather than `NaN`, so a naive `.isna()` scan alone would misreport them as
0 % missing.

---

## 4. I02 — Candidate external height data sources

**Coordinates actually assessed** (from `scripts/validation/v12_cell_pipeline.py::CELL_CONFIGS`,
director-verified):

| cell | lat, lon | radius_m | where this actually is |
|---|---|---|---|
| `nyc_suburban` | 40.7052, −73.5985 | 500 | **Nassau County, Long Island — outside NYC** |
| `nyc_rural` | 42.0396, −74.1143 | 1000 | **Catskills, ~130 km north — outside NYC** |
| `austin_rural` | 30.5788, −98.2700 | 1000 | Texas Hill Country, outside city limits |
| `austin_centre` | 30.2672, −97.7431 | 500 | Downtown Austin, inside city limits |

This geography is load-bearing: **two of the four `nyc_*`-named tracts are not in New York City**
(the Queens/Nassau boundary sits near −73.70), so NYC's own open-data portal cannot serve them
regardless of its data quality. Only boundary-independent sources are in play for those two.

| dataset | covers the 4 tracts | height semantics | license | access | effort | key caveat |
|---|---|---|---|---|---|---|
| **Microsoft Global ML Building Footprints** | **all 4** (nationwide, boundary-independent) | per-building ML height estimate | **CDLA Permissive 2.0** | bulk download | **one-off enrichment script** | height sub-layer is a *subset* of footprints; per-tract density unverified without downloading |
| USGS 3DEP | nominally all (99 % US baseline FY25) | raw point cloud → needs DSM−DTM diff | Public Domain | bulk S3 | new ingestion module | vintage varies; per-tract quality level not verified |
| TNRIS / StratMap LiDAR | both TX tracts | raw point cloud → needs DSM−DTM diff | public domain | free bulk | new ingestion module | per-tract vintage/QL unconfirmed |
| NYS Building Footprints (statewide) | covers nyc_suburban + nyc_rural geographically | aggregates 4 sources incl. Microsoft | unconfirmed | portal download | unresolved | height-field completeness outside the NYC portion not documented |
| NYC Open Data Building Footprints | **none of the 4** | per-building `HEIGHT_ROOF`, good provenance | permissive | REST/bulk | n/a | out of geographic scope |
| Austin Building Footprints (2013) | austin_centre only | **no height field at all** | city terms | REST/bulk | not feasible | 2D-only schema |
| GHS-BUILT-H | all 4 (global 100 m grid) | neighbourhood-*average* height | free/open | raster download | one-off script | too coarse for per-building assignment |
| Copernicus DEM GLO-30 | all 4 | 30 m DSM, no bundled DTM | free | download/API | not feasible | pixel larger than most footprints here |
| Google Open Buildings 2.5D Temporal | **none** | 4 m, ~1.5 m MAE | open | GEE/HDX | not feasible | explicitly excludes the USA |
| ALOS World 3D | all 4 (global) | 30 m DSM | free, account-gated | JAXA G-Portal | not feasible | **could not be assessed — account required; stated rather than guessed** |

All findings come from documentation/catalog pages read via `WebFetch`/`WebSearch`. No dataset was
downloaded, no API was called, and no code touching an external service was written (§1.3).

---

## 5. I03 — Does the existing imputation infrastructure work? **No.**

`knn_fill` invoked directly at production defaults (`k=10`, `radius=100.0 m`,
`mnar_threshold=0.60`) against the real fixtures. Executed twice independently — once by the
employee, once re-run by the director in a separate process — with identical results.

| cell | rows | `height_m` missing | **filled** | MNAR-blocked | silent no-donor | confidence (filled) |
|---|---|---|---|---|---|---|
| nyc_suburban | 1589 | 1589 (100.0 %) | **0** | 1589 | 0 | — |
| nyc_rural | 198 | 198 (100.0 %) | **0** | 192 | **6** | — |
| austin_rural | 245 | 245 (100.0 %) | **0** | 232 | **13** | — |
| austin_centre | 413 | 349 (84.5 %) | **15** | 334 | 0 | MEDIUM 7, LOW 5, HIGH 3 |

**Radius sensitivity — widening does nothing.** At 250 m, 500 m, and 1000 m, `n_filled` stays exactly
**0** for all three fully-NaN cells. Widening only converts "silent no-donor" rows into MNAR-blocked
rows — making the rejection auditable without making it fixable — because any neighbour found further
away is *also* 100 % missing by construction. For `austin_centre`, wider radii raise the fill count
only marginally (15 → 21) while confidence collapses to 100 % `LOW`.

**Comparison arm.** `imputation.py::impute_column(method="auto")` raised
`ValueError("impute_column: bounds must be provided for PDE imputation on column 'height_m'.")`
verbatim for the three 100 %-missing cells. For `austin_centre` (not all-NaN) it resolved to the KDE
branch and filled all 349 rows — but from only 64 observed values, with **no spatial reasoning and no
MNAR awareness**.

**Verdict, stated without overstatement.** For the three fully-affected cells, "wire up the existing
imputer" is **not structurally viable as-is**, and this is conclusive — it was tested, not inferred.
For `austin_centre` it is **partially and weakly viable** via `knn_fill` (15/349, ~4 % of the gap) and
**fully but non-spatially** viable via `impute_column`'s KDE path. What would have to change for the
three fully-affected cells is not a threshold constant but the *scope of the donor pool*: it would
have to extend beyond a single cell's own GeoDataFrame.

### New defect found: E-UTCI-10 (logged OPEN, deliberately unfixed)

`spatial_impute.py` lines 218-220 (`knn_fill`) and 141-143 (`neighbour_vote`): a row whose
neighbourhood query returns no neighbours within the radius is `continue`d **without** setting
`blocked_mask[i]`, so it is neither filled nor flagged `SPATIAL_CLUSTER_MNAR_BLOCKED` — invisible in
`data_quality_flag`. Quantified on real data: 6 rows in `nyc_rural`, 13 in `austin_rural`. This is an
**observability gap, not a correctness gap** — no wrong value is produced, and no production call
site imputes `height_m` today. It matters only once spatial imputation is wired into a production
path, at which point an unflagged skip becomes an untraceable silent no-op. Not a blocker for
E-UTCI-09.

---

## 6. I04 — Candidate fix shapes (ranked) — **CANDIDATES ONLY, NONE ADOPTED**

| rank | option | effort | risk | scope | verdict |
|---|---|---|---|---|---|
| 1 | **(b)** ingest Microsoft Global ML Building Footprints for the 4 tracts | Medium — one-off enrichment script (quadkey download + spatial join) | Medium — clean license/access, but height-sublayer density at these points unverified | **Whole platform** | candidate — not adopted |
| 2 | **(f)** *[added]* wire `impute_column`'s existing KDE path for `austin_centre`-class partially-missing cells | Low — works today, zero new code | Low-medium — no spatial reasoning, no confidence tiering, no MNAR awareness | Stage 6 only | candidate — not adopted |
| 3 | **(d)** widen `spatial_impute.py`'s donor pool **across cell boundaries** (structural) | High — not a radius tweak; needs a new cross-cell donor-admission mechanism | High — cross-fabric/zone-type mismatch; inherits E-UTCI-10 | Whole platform once wired | candidate — not adopted |
| 4 | **(c)** statistical median-borrow from nearest good cell of the same zone-type, low-confidence flagged | Low — lookup against I01's own stats | High — cross-city fabric mismatch (the only rural donor is `la_rural`) | Stage 6 only | candidate — not adopted |
| 5 | **(a)** targeted OSM re-fetch once §5.3 is unblocked or a scoped exception is granted | Low code effort (F-07: identical call path) | High payoff risk — F-07 says the gap reflects live tagging density, so a re-fetch may return the same nothing | Whole platform, highest fidelity if it works | candidate — not adopted |
| 6 | **(e)** accept and permanently document as a known Stage-6 limitation | Near zero | Low technical risk, standing quality cost (`svf_mean = 1.0000` indefinitely) | Stage 6 only | candidate — not adopted |

**Prerequisites and combinations.** Option (d) is a *precondition*, not an alternative, to the
existing imputer ever working on the three fully-NaN cells — I03's radius probe forecloses any
lighter-weight version. Options (a) and (b) are mutually reinforcing rather than competing; both act
near the source. Option (f) is fully independent and self-contained. Option (e) is compatible with
everything and is the natural interim floor. The strongest evidenced combination is
**(b) for all four tracts + (f) applied immediately to `austin_centre` + (e) documenting whatever
residual survives**, holding (d) and (c) in reserve.

**Split strategy, not one fix for all four.** `austin_centre` is structurally unlike the other three:
84.5 % rather than 100 % missing, 64 real observed values available, and already partially or fully
fillable today with zero structural change. A single uniform fix would either overengineer
`austin_centre` — building (d)'s cross-cell machinery where a KDE call already reaches full fill — or
underserve the three fully-NaN cells by applying KDE-class tooling that structurally cannot fill
anything there.

---

## 7. What a follow-up Stage-1 implementation plan should contain

*Recommendation on content only. Scoping and authoring that plan is a separate manager task, not
undertaken here.*

1. **Resolve the one decisive unknown first, before ranking anything.** Every candidate ordering
   above rests on an unverified assumption: how densely Microsoft Global ML Building Footprints'
   height sub-attribute actually populates *these four bounding boxes*. That fact must be **counted,
   not read** — it requires downloading the relevant quadkeys, which this plan's §1.3 forbids. The
   follow-up plan's first task should be exactly that count, and it needs an explicit user decision
   to either unblock CLAUDE.md's §5.3 gate or grant a scoped one-off exception. If the density comes
   back low, option (b) drops and (a)/(d) rise.
2. **Adopt the split strategy explicitly in its §3 dependency decisions** — one track for the three
   fully-NaN cells, another for `austin_centre`-class partial cells — rather than seeking a single
   uniform mechanism.
3. **Treat option (f) as the cheap early win**, but only behind an explicit confidence/provenance
   flag: a KDE fill from 64 observed values carries no spatial reasoning, and the platform's
   zero-fitted-parameters discipline makes silent low-confidence fills a real hazard.
4. **If (d) is pursued, scope it honestly as a structural change** to the donor-admission mechanism —
   crossing the cell's own GeoDataFrame boundary — and not as a constant tweak. I03 proves the
   constant tweak is inert.
5. **Fold in E-UTCI-10** as a small, self-contained sub-task if and only if that plan wires spatial
   imputation into any production path.
6. **Carry option (e) as the standing fallback** regardless of which track is chosen, so the residual
   gap stays visibly documented rather than quietly inherited.

---

## 8. Open questions this investigation could not resolve

| # | Open question | Why it was not resolvable here |
|---|---|---|
| 1 | Actual density of Microsoft Global ML height data inside the 4 bounding boxes | **Decisive for option (b).** Must be counted from downloaded data; §1.3 forbids downloads |
| 2 | USGS 3DEP / TNRIS StratMap exact vintage and quality level at the 4 coordinate pairs | Needs live interactive coverage-index tools, beyond "reading a documentation page" |
| 3 | NYS Building Footprints' height-field completeness outside the NYC portion | Documentation confirms the source aggregation but not field-level completeness |
| 4 | ALOS World 3D suitability | JAXA G-Portal account required; stated plainly rather than guessed |

---

*Investigation complete, findings synthesized, awaiting manager scoping of a follow-up Stage-1
implementation plan. No fix implemented; no candidate adopted. 2026-07-25.*
