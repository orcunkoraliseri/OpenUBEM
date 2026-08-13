# FIX — OPEN-22: build the new tag-rich labelled fixture

> Executes T03 of `PLAN_rulings-and-five-items-2026-08-12.md`. Ruling already made
> (rebuild the fixture; labels authored here, from source evidence, director-audited).
> `tests/fixtures/labelled_archetypes_50.csv` was not modified, moved, or deleted —
> confirmed by `git status` showing it absent from the changed-files list throughout
> this task.

---

## What was built

`tests/fixtures/labelled_archetypes_tagrich_v2.csv` — **100 rows**, stratified sample
from the director-verified 592-row tag-rich pool (§4.2), labelled from source tag
evidence, **2 marked `UNDETERMINED` and excluded from grading**, **98 graded rows**.

**The classifier was never run, and never imported, while the labels were being
written.** `scripts/analysis/open22_build_tagrich_fixture.py` — the script that
produces the fixture — does not import
`openubem.semantic.building_classifier` anywhere; it can be diffed to confirm this.
Grading happens afterward, in a separate script
(`scripts/analysis/open22_grade_tagrich_fixture.py`) that is the *only* file in this
task that imports the classifier, and it runs only after the fixture file already
exists on disk.

---

## Method

### 1. Pool reproduction (sanity check before sampling)

Reloaded both source gpkgs and rebuilt the director's §4.2 pool definition
independently: `building_tag` present and not `'yes'` (558) OR `function_tag` present
(100), union 592 (boston 233 / chicago 359, overlap 66). **Reproduced exactly**,
including the top `building_tag` counts (office 192, commercial 132, roof 70,
apartments 39, hotel 26, retail 18, parking 16, university 11, train_station 11,
public 8) and the rule‑17a population (290). This confirms the pool used for sampling
matches the director-verified figures to the row.

### 2. Stratified sample, fixed seed

Stratum = `building_tag` (lower-cased) when present and not `'yes'`, else
`function:<function_tag>` — 43 strata over 592 rows. Allocated 100 seats by
proportional (Hare-quota) share with largest-remainder rounding, **capped at each
stratum's own population** (no stratum can be assigned more rows than it has); no
forced per-stratum minimum, so several 1-row strata did not win a seat this run —
reported, not hidden (see the allocation table in
`scripts/analysis/open22_sample_tagrich.py`'s printed output, and the CSV provenance
comment). **Seed: `20260812`**, recorded in the fixture's own provenance comment.
Draw: office 33, commercial 22, roof 12, apartments 7, hotel 5, retail 3, parking 3,
university 2, train_station 2, function:shelter 2, public 2, and 8 more strata at 1
row each (government, function:parking, garage, function:restaurant, service,
transportation, kiosk) — 18 of 43 strata represented, **not all office** (office is
33% of the draw, versus 34% of the pool — proportional, not skewed).

### 3. `building=roof` — decided explicitly (70 rows in the pool, 12 in the draw)

**Decision: included, labelled `OpenUBEMUnknown`.** Reason: one sampled roof row's
own OSM tags settle the question directly — `"building:walls": "no"`,
`"shelter_type": "pavilion"` (osm_id `212123007`) — this is architecturally a canopy,
not an enclosed conditioned space, and none of the 30 archetypes represents an
unconditioned canopy. This is a **decidable** label from the tag itself, not a guess,
and it matches the precedent already set by the existing ratified 50-row fixture
(which labels its own two `roof`-tagged rows `OpenUBEMUnknown`). Excluding `roof`
rows from the sample entirely was considered and rejected: doing so would remove a
population that the tag evidence genuinely does settle, weakening the exam rather
than strengthening it.

### 4. Labelling basis (source evidence, not classifier output)

Documented in full in `scripts/analysis/open22_build_tagrich_fixture.py`'s module
docstring; summary:

- **OSM tag semantics** — `openubem/data/osm_to_use_class.json` (a static vocabulary
  table) and general OSM `building=*`/amenity semantics for what a tag denotes.
- **The 30-archetype vocabulary** — `openubem/data/openstudio_archetypes.json` — which
  archetype IDs exist at all (e.g. there is no "parking garage" or "transit station"
  archetype, which is why those tags resolve to `OpenUBEMUnknown`: a directly
  decidable negative, not an ambiguous case).
- **Office/commercial size tiering**: the same LBNL-CBES 2,322 / 9,290 m² total-
  floor-area bins already externally cited in the *existing* fixture's own
  provenance comment (E‑R3‑3) — an external, published boundary, reused as a citable
  standard, not read off classifier output. Total floor area = `footprint_area_m2 *
  max(levels, 1)`; footprint alone when levels is missing (see the systemic
  disagreement this produces, §"Mismatches" below).
- **A ≥20-level building → `TallBuilding`, ≥40 → `SuperTallBuilding`, regardless of
  the specific commercial tag.** This exact convention is not invented for this
  task — it is the already-ratified, director-audited labelling practice visible in
  the *existing* fixture's own notes column (e.g. *"commercial 31fl >= 20 ->
  TallBuilding"*, *"office 152m ~46fl >= 40 -> SuperTallBuilding"*). Reusing an
  already-ratified human labelling convention is source evidence about how this
  project's own labellers have always read tall buildings; it is not "the
  classifier's output."
- **Apartments**: ≥9 levels → `HighriseApartment`, else `MidriseApartment`; missing
  levels defaults to `MidriseApartment` — again the existing fixture's own
  documented default.
- **Hotels**: ≥4 levels → `LargeHotel`, <4 → `SmallHotel` (existing fixture's own
  threshold). **Missing levels → `UNDETERMINED`** — no footprint-based hotel-tier
  convention was found in any source consulted; refused to guess (1 row: osm_id
  `74451017`).
- **Retail**: single-storey → `RetailStandalone`. Multi-storey retail has no clean
  DOE-prototype match (all three retail archetypes are single-storey forms) →
  `UNDETERMINED` (1 row: osm_id `147613448`, a 4-storey `retail`-tagged building).
- **University → `College`** (the only post-secondary archetype).
- **`government`/`public+government`/`public+townhall`, absent a height override →
  `Courthouse`**, the only civic archetype — this exact mapping already exists in the
  *ratified* fixture (osm_id `108240968`, `public`+`government` → `Courthouse`);
  `townhall` is treated the same way for lack of any closer archetype.
- Anything not covered by the above, or internally contradictory, → `UNDETERMINED`.

**2 of 100 rows landed `UNDETERMINED`** and are excluded from grading (kept visibly
in the file, not dropped): the no-level-data hotel, and the multi-storey retail row.

---

## Precondition check (plan step, mandatory before trusting anything downstream)

`scripts/analysis/open22_grade_tagrich_fixture.py` re-classifies the **old**
`labelled_archetypes_50.csv` first and refuses to proceed if it does not score
44/50 = 88.0%. Run result: **44/50 = 88.0%, exact match.** Proceeded.

---

## Results — the new fixture, graded at HEAD

| | old (`labelled_archetypes_50.csv`) | new (`labelled_archetypes_tagrich_v2.csv`) |
|---|---|---|
| rows | 50 | 100 (98 graded, 2 `UNDETERMINED`) |
| `FALLBACK_SIZE_DEFAULT` share | **17/50 = 34.0%** | **3/98 = 3.1%** |
| accuracy overall | 44/50 = 88.0% | **87/98 = 88.8%** |
| accuracy excluding `FALLBACK_SIZE_DEFAULT` rows | 29/33 = 87.9% | 87/95 = 91.6% |

**The rebuild does exactly what it was for: the fallback share drops from 34.0% to
3.1%, an order of magnitude, and it is no longer a third of the exam.** Full
per-row output: `openubem/outputs/comparisons/open22_v2_fixture_breakdown.csv`
(`osm_id, source, label, emitted, rule_token, confidence, match`, 100 rows including
the 2 `UNDETERMINED` with `match` left blank).

Rule-token distribution over the 98 graded rows: `RULE_USE_CLASS_SIZE` 41,
`FALLBACK_UNKNOWN` 20, `RULE_HIGHRISE` 17, `RULE_RESIDENTIAL_TIER` 7,
`RULE_FUNCTION_TAG` 7, `FALLBACK_SIZE_DEFAULT` 3, `RULE_LODGING_TIER` 3.

---

## The 11 mismatches, explained (not just counted)

**7 of 11 trace to one cause: missing-`levels` handling.** My labelling convention
(no floor count on file → treat `footprint_area_m2` alone as total floor area, i.e.
implicitly assume 1 storey — the same convention the *existing* fixture itself uses
for its own missing-floor rows) disagrees with the classifier's actual behaviour: it
**imputes** a plausible level count via a group-median lookup
(`archetype_source` shows the appended `GROUPMEDIAN_LEVELS_MED` token, and
`classify()`'s own comment confirms "`use_class -> median(levels) lookup, fit on
OBSERVED-levels rows only`"). Since downtown office/apartment buildings with
*known* level counts in this sample skew tall, the imputed value is usually larger
than 1, pushing the classifier's size tier or apartment tier higher than my
flat-footprint label: `405668761`, `147478372` (apartments → `HighriseApartment` vs
my `MidriseApartment`), `124873930`, `147776396`, `148164098`, `148164123`,
`148685510` (office/commercial → a larger office tier than mine). **This is not
obviously a classifier defect** — median imputation from comparable nearby buildings
is arguably a better estimate than a flat "assume 1 floor" default — but it is a
genuine, systemic disagreement in convention between this label set and the
classifier's actual missing-data handling, and the new fixture is exactly what makes
that visible for the first time.

**3 of 11: generic `building=yes` + a function tag the classifier does not
special-case.** `29650708` (yes/parking), `1175801196`, `1175853280` (yes/shelter):
all three carry a `function_tag` that plainly disqualifies them from being an office
(a parking structure, an open shelter), yet the classifier's rule‑17a fallback still
fires (`FALLBACK_SIZE_DEFAULT`) and assigns `MediumOffice`. Contrast: `29943278`
(yes/restaurant) *is* correctly recognised (`RULE_FUNCTION_TAG` → the label I gave
it, `FullServiceRestaurant`). **The classifier's function_tag handling recognises
`restaurant` but not `parking` or `shelter`** — a concrete, evidenced gap, reported
here as a finding, not fixed (out of this task's scope).

**1 of 11: rule-priority for a tall, specifically-tagged hotel.** `147486325`
(`hotel`, 22 levels) — I labelled `LargeHotel` (≥4 levels, hotel tag, per the
existing fixture's own threshold). The classifier assigns `TallBuilding` via
`RULE_HIGHRISE`, HIGH confidence — the ≥20-level override fires ahead of the
hotel-specific `RULE_LODGING_TIER` even though the tag unambiguously says "hotel."
This is a genuine, debatable design question (does a 22-storey building modelled as a
hotel represent its real loads/schedules better than modelling it as a generic tall
building?) rather than an obvious bug — reported as a finding for the director/user,
not resolved here.

---

## What was not done, and why

**Plan step 6 asks for "a new, separate, non-gating test that reports the new
fixture's accuracy without asserting a threshold," and does not repoint
`test_fine_top1`.** The second half is honoured: `test_fine_top1` was not touched.
**The first half — a new pytest test — was not added.** The dispatch instructions for
this task restrict writes to report files under `docs/docs_ACTIVE/openings/extra/`,
the new fixture under `tests/fixtures/`, and scripts under `scripts/analysis/`; a new
pytest test belongs in `tests/`, which is outside that list, and `tests/` is also
where two other executors in this same arc (T05, T06) are actively working right now
(confirmed live: `git status` shows in-flight changes under `tests/fixtures/` from a
concurrent session as this report is being written). Rather than write to a shared,
actively-contended file outside my authorized scope, **this leg is left undone and
flagged here** — `scripts/analysis/open22_grade_tagrich_fixture.py` already delivers
the same *functional* result (classifies the new fixture, reports accuracy, asserts
nothing about a threshold, and is runnable standalone), just not wrapped in a pytest
test. Adding the pytest wrapper is a small, well-specified follow-up for whichever
session is next authorized to write to `tests/`.

---

## Files this task produced

- `tests/fixtures/labelled_archetypes_tagrich_v2.csv` — the new fixture (100 rows,
  provenance comment with seed/pool/date/source gpkgs).
- `scripts/analysis/open22_sample_tagrich.py` — pool + stratified sampling only (no
  labelling, no classifier import); used to validate the sampling logic before it was
  folded into the fixture-builder.
- `scripts/analysis/open22_build_tagrich_fixture.py` — draws the same seeded sample
  and labels every row from source evidence. **Never imports the classifier.**
- `scripts/analysis/open22_grade_tagrich_fixture.py` — the only script that imports
  the classifier; checks the old-fixture precondition, then grades the new fixture.
  Writes `openubem/outputs/comparisons/open22_v2_fixture_breakdown.csv`.
- `tests/fixtures/labelled_archetypes_50.csv` — **not modified.**
