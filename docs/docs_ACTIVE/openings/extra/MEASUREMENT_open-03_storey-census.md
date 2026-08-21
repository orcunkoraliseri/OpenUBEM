# MEASUREMENT — OPEN-03 storey-count census, fleet-wide (Arc B, T05)

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/PLAN_open61-census-open03-storeys-2026-08-20.md`,
> T05, Arc B. **Date:** 2026-08-20. **Script:** `scripts/analysis/open03_storey_census_2026-08-20.py`.
> **Output:** `openubem/outputs/comparisons/open03_storey_census.csv` (8,160 rows).
> **No simulation was run and no per-building `layout_assign` IDF was generated.** This is geometry
> and bookkeeping only, per the plan's own instruction.

## 1. The route taken, and why

The plan's first instruction was to prefer a derivation over a build. That route was available and
is what this script uses.

`layout_assign` selects one of the fleet's 26 pre-built DOE-prototype baseline IDFs by archetype
(`ARCHETYPE_IDF_MAP`, `openubem/geometry/layout_assigner.py:23-61`) and loads it wholesale as the
working IDF (`openubem/idf/builder.py:228-230`) before any per-building work happens. The only two
things a real per-building build then does to that loaded baseline are:

1. **`scale_baseline_idf`** — scales every surface's X/Y vertex coordinates by a planar factor and
   explicitly leaves Z unchanged (`layout_assigner.py:658-664`).
2. **`match_storeys`** — when it applies at all, writes only the `Zone.Multiplier` field
   (`layout_assigner.py:649`). A fleet-wide grep of `openubem/geometry/*.py` and `openubem/idf/*.py`
   confirms this is the *only* `.Multiplier =` write anywhere in the geometry/IDF code.

Neither operation ever adds a wall surface at a new Z elevation. So the geometry-measured storey
count of a `layout_assign` IDF — distinct wall Z-elevations, the exact definition the predecessor's
48-sample used — is a function of the **archetype alone**, not of the individual building's
`num_floors`. This was verified, not assumed: joining the 48-sample
(`openubem/outputs/comparisons/open03_envelope_decomposition.csv`) to archetype shows `storey_count`
has `nunique == 1` per archetype for every one of the 7 baseline-mapped archetypes it contains.

So the `layout_assign` storey count for the 18 baseline-mapped archetypes present in this fleet is a
**lookup, computed once per archetype** from that archetype's own baseline IDF (loaded via geomeppy,
saved once to normalize its vertex-comment format, then read with the predecessor's own parser). For
the 2 archetypes with no baseline mapping (`Courthouse`, `OpenUBEMUnknown`), the production builder
degrades to the plain `auto` zoning pipeline on identical inputs
(`openubem/idf/builder.py:468-475`) — verified exactly equal, per-building, on all 5
Courthouse/OpenUBEMUnknown rows of the 48-sample — so their `layout_assign` storey count is simply
that same building's own `auto` storey count.

`auto` storey count is read directly off the 8,160 real, on-disk auto-arm IDFs
(`evidence/open48_refleet4/<cell>/fleet_staging/idfs/*.idf`).

## 2. Controls

- **C8 — row count.** 8,160 rows, per-cell n sums to 8,160. **PASS.**
- **C9 — exact reproduction of the 48-sample.** All 48 matched; 0 mismatches on `auto`, 0 mismatches
  on `layout_assign`. **PASS.**
- **C10 — fleet-wide disagreement, direction, breakdown.** See §3.
- **C11 — `Zone.Multiplier > 1` usage, both arms.** `auto`: **0 / 8,160** (F7 sample: 0/48, exact
  match; also true structurally — `Zone.Multiplier` is never written outside `layout_assigner.py`).
  `layout_assign`: **434 / 8,160** (F7 sample: 2/48; the fleet-wide rate, 5.3%, is far above the
  sample's, because the 48-sample under-represented `MediumOffice`/`Warehouse`-shaped buildings whose
  `num_floors` exceeds their prototype's band count in an "expressible" way). Computed by running the
  production `match_storeys()` function itself per building (status `applied` with a written
  multiplier `> 1`), not by a blind grep of the built IDF — a blind grep of the 48-sample's actual
  IDFs found 6/48, because it also picks up native `Zone.Multiplier` values baked into some
  prototypes' raw geometry (guest-room/typical-floor repetition) that pre-date and are unrelated to
  per-building storey matching; using `match_storeys()`'s own return value reproduces F7's 2/48
  exactly.

## 3. Headline: the disagreement, fleet-wide

**4,914 of 8,160 buildings (60.2%) disagree** between `auto` and `layout_assign` storey count.

Direction: when they disagree, **`auto` is almost always the taller one.**

| | n | % of fleet |
|---|---|---|
| `auto` taller | 4,677 | 57.3% |
| `layout_assign` taller | 237 | 2.9% |
| equal | 3,246 | 39.8% |

Mean signed difference (`layout_assign` − `auto`) = **−1.85 storeys**; median = **−1.0**.

### By archetype

| archetype | n | disagree | disagree % | mean diff (LA−auto) |
|---|---:|---:|---:|---:|
| LargeOffice | 257 | 252 | 98.1% | −4.66 |
| MediumOffice | 391 | 365 | 93.3% | −3.57 |
| SecondarySchool † | 11 | 11 | 100.0% | −2.45 |
| RetailStandalone | 140 | 93 | 66.4% | −1.71 |
| SmallOffice | 3,497 | 2,353 | 67.3% | −1.41 |
| MidriseApartment † | 2,818 | 1,601 | 56.8% | −0.94 |
| Warehouse | 38 | 21 | 55.3% | −0.76 |
| FullServiceRestaurant | 33 | 6 | 18.2% | −0.79 |
| QuickServiceRestaurant | 50 | 13 | 26.0% | −0.46 |
| SmallHotel | 8 | 7 | 87.5% | +2.00 |
| Hospital | 5 | 3 | 60.0% | +1.00 |
| PrimarySchool | 2 | 1 | 50.0% | −0.50 |
| SuperMarket | 5 | 2 | 40.0% | −0.80 |
| LargeHotel | 33 | 33 | 100.0% | −9.39 |
| Outpatient † | 6 | 5 | 83.3% | +0.17 |
| HighriseApartment † | 32 | 32 | 100.0% | −20.50 |
| TallBuilding † | 92 | 92 | 100.0% | −25.14 |
| SuperTallBuilding † | 24 | 24 | 100.0% | −54.08 |
| Courthouse (no baseline) | 68 | 0 | 0.0% | 0.00 |
| OpenUBEMUnknown (no baseline) | 650 | 0 | 0.0% | 0.00 |

† **Z_Origin collapse risk — see §4.** These 6 archetypes' `layout_assign_storey_count` reading is
compromised by a newly-found parsing gap and should not be read as true geometric behaviour, only as
an exact reproduction of the same (flawed) method the 48-sample already used.

### By cell

Disagreement ranges from near-zero (`nyc_suburban` 0.06%, `nyc_rural` 2.5%, `austin_rural` 3.3%) to
dominant (`la_suburban` 85.3%, `nyc_centre` 91.9%, `la_urban` 92.1%) — driven by each cell's
archetype mix (dense, low-baseline-storey archetypes concentrate the disagreement).

## 4. A parsing gap found while building this census — read before trusting per-archetype numbers

The storey-count definition this census (and the 48-sample before it) uses is: distinct min-Z
elevations among a building's WALL objects. This definition silently breaks whenever a baseline's
`GlobalGeometryRules` `Coordinate System` is `Relative` **and** the file encodes a repeated floor
band's elevation in the `ZONE` object's own `Z_Origin` field rather than in the wall vertices — every
wall then reads a near-zero *local* Z regardless of true floor elevation.

This was measured zone-by-zone against all 18 baseline-mapped archetypes' own IDF objects, not
assumed. Result:

- **Severe** (most/all floor-area-counting zones affected — `layout_assign_storey_count` reads far
  too low, typically 1-3 regardless of true prototype height): `MidriseApartment` (18/27 zones),
  `HighriseApartment` (18/27), `TallBuilding` (145/164), `SuperTallBuilding` (232/256), `Outpatient`
  (59/118), `SecondarySchool` (21/46). Together **2,983 of 8,160 buildings — 36.6% of the fleet.**
- **Immaterial:** `LargeOffice` (3/23 zones, none of them floor-area-counting — confirmed by C9:
  `LargeOffice` reproduces its expected value of 4 exactly) and `QuickServiceRestaurant` /
  `FullServiceRestaurant` (their one affected zone is non-floor-area).
- **Absent** (`ZONE.Z_Origin == 0.0` uniformly; absolute Z is baked directly into wall vertices, the
  naive method reads correctly): the other 10 mapped archetypes — `SmallOffice`, `MediumOffice`,
  `RetailStandalone`, `Warehouse`, `LargeHotel`, `SmallHotel`, `Hospital`, `PrimarySchool`,
  `SuperMarket`.

Practically: `TallBuilding`'s and `SuperTallBuilding`'s astonishing −25 and −54 storey mean
differences are **not** "layout_assign builds absurdly short towers" — they are this parsing gap
reading `layout_assign_storey_count == 1` for prototypes that in reality span 145-232 floor-area
zones across dozens of true elevations. `MidriseApartment` and `HighriseApartment`'s numbers carry
the same caveat, materially: at 2,818 buildings, `MidriseApartment` is the single largest archetype
in the fleet (34.5%), so its reported 56.8% disagreement rate should be read as "this comparison is
unreliable for over a third of the fleet," not as a geometric finding about `MidriseApartment`
specifically.

**This was not fixed** — the census's job (C9) is to reproduce the predecessor's own numbers exactly,
and fixing the definition would silently change what C9 must match. It is registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16 as `[OPEN]`, and every affected row is
flagged in the output CSV via `layout_assign_z_origin_collapse_risk = True`.

**Reassurance on the rest of the headline:** restricting to the 10 archetypes with no known risk
(5,177 of 8,160 buildings, 63.4% of the fleet — `SmallOffice`, `MediumOffice`, `LargeOffice`,
`RetailStandalone`, `Warehouse`, `LargeHotel`, `SmallHotel`, `Hospital`, `PrimarySchool`,
`SuperMarket`, plus the two no-baseline archetypes), the disagreement rate is **60.8%** — almost
identical to the unrestricted 60.2%. The broad direction (`auto` taller, majority disagreement) is
not an artifact of the parsing gap; only the archetype-level magnitudes for the 6 flagged archetypes
are.

## 5. C11 in context — the OPEN-60 link

434 of 8,160 `layout_assign` buildings (5.3%) trigger `match_storeys()`'s storey-matching mechanism
(status `applied`, multiplier written `> 1`) — versus 0 in `auto`, which never touches
`Zone.Multiplier` at all. This is the same mechanism the predecessor F7 measured at 2/48; the
fleet-wide rate is over an order of magnitude higher than the sample suggested. Every one of these
434 buildings is a live instance of the transformer-capacity conservatism documented at
`layout_assigner.py:222-276` (D9) — this count is the first fleet-scale denominator for that
open question.

## 6. Whether this warrants its own item ID

Two distinct findings came out of Arc B:

1. **The storey-count disagreement itself is real and large** — 60.2% of the fleet, `auto` almost
   always taller when they disagree, concentrated in commercial multi-floor archetypes
   (`LargeOffice`, `MediumOffice`) even outside the Z_Origin-risk set.
2. **A previously-unknown parsing gap** (§4) affects the *measurement* of that disagreement for 36.6%
   of the fleet, including the single largest archetype (`MidriseApartment`).

Both are proposed to the director as candidates for a new item ID — not opened here, per the plan's
own instruction that a new ID is the user's/director's to grant.
