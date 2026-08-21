# S03 — the classifier exam, rebuilt over the whole tag-rich pool

**Slug:** `MEASUREMENT_s03_tagrich-v3-exam`
**Date:** 2026-08-20
**Plan:** `implemenation/previous/PLAN_four-board-items-2026-08-20.md`, T02
**Board row:** S03 (WP-S) — *"Put the unanswered classifier question back to you"*
**Predecessors:** `extra/FIX_open-22_tagrich-fixture.md`, `extra/FIX_open-22_tagrich-gate.md`
(OPEN-22, closed and ID retired 2026-08-13)

---

## 1. The question S03 was holding

S03 had been sitting at `decided` with one thing missing: **who writes the new labels, and how many
rows.** The objection behind it was specific and correct — roughly one third of
`labelled_archetypes_tagrich_v2.csv`'s answers were derived from **floor area**, which is one of the
classifier's own inputs. An exam whose answer key is computed from the candidate's input is not
measuring the candidate.

The user's ruling of 2026-08-20 settled both halves at once: an executor labels from raw evidence,
marking every row where the evidence is thin, **over all the data** — not a sample.

## 2. What was built

| artifact | rows | graded? |
|---|---:|---|
| `tests/fixtures/labelled_archetypes_tagrich_v3.csv` | **592** | yes |
| `tests/fixtures/labelled_archetypes_tagpoor_v3.csv` | **290** | **no** — ungraded sheet, kept for provenance |

**Pool control:** 592 tag-rich (Boston 233 / Chicago 359) out of 882 total, reproducing the v2
header's own definition exactly. `labelled_archetypes_50.csv` and `..._tagrich_v2.csv` were **not
touched** — both remain byte-frozen.

**Schema:** v2's ten columns plus three new ones — `evidence_basis`, `evidence_strength`
(`strong`/`thin`), `flagged_for_ruling`.

**Labelling rule, which is the whole point of v3:** the class comes from tag evidence only
(`building_tag`, `function_tag`, `surplus_tags`). Size, height and levels may be used **only** to pick
a band *inside* a class the tags have already determined (Small/Medium/Large office,
Midrise/Highrise apartment, Small/Large hotel) — never to invent the class.

**Evidence strength:** **589 strong, 3 thin**, and all 3 thin rows are flagged. The three are a hotel
and a hotel-tier row with no size, height or level data at all, and one genuine tag conflict — an
office `building_tag` against a place-of-worship `function_tag` on a real mixed-use skyscraper church.
Three flags out of 592 is the honest reading that the tag-rich pool is, in fact, tag-rich.

## 3. Result — two numbers, because there are two questions

Graded against the classifier's emitted vocabulary (`openubem/semantic/building_classifier.py:44-46`,
`_VALID_30`). Director re-derived both figures directly from
`openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv`.

| measure | n | result |
|---|---:|---:|
| **coarse** top-1 | 592 | **100.0 %** |
| **fine** top-1, *strict* | 592 | **71.1 %** (421) |
| **fine** top-1, *crediting the classifier's own height override* | 592 | **89.0 %** (527) |
| fine top-1, strict, `strong` subset only | 589 | 71.3 % |

### Why there are two fine-grained numbers

The classifier has a deliberate rule (1a/1b) that overrides the tag-determined class with
`TallBuilding` / `SuperTallBuilding` above a height threshold. T02's labelling rule forbids using
height to determine a class, so v3's answer key **never** produces those two labels. The classifier
emits one of them **106 times**.

Counting all 106 as errors gives **71.1 %**. Crediting them — treating the height override as
intended behaviour rather than a miss — gives **89.0 %**. **Neither number is wrong; they answer
different questions.** The 89.0 % is the classifier's accuracy at the job it is written to do; the
71.1 % is its agreement with a tag-only ground truth. Both are reported, always together, and always
naming this fixture.

### What the remaining errors actually are

With the height override credited, **65 errors remain**, and they are overwhelmingly **size-band
confusions inside the correct family**:

| expected → emitted | count |
|---|---:|
| MediumOffice → LargeOffice | 13 |
| SmallOffice → MediumOffice | 10 |
| OpenUBEMUnknown → MediumOffice | 10 |
| SmallOffice → LargeOffice | 9 |
| OpenUBEMUnknown → LargeOffice | 5 |
| MidriseApartment → HighriseApartment | 5 |
| OpenUBEMUnknown → SmallOffice | 4 |
| Courthouse → MediumOffice | 3 |

🔴 **This is the honest limit of v3 and it should be stated on every use of the fixture.** The size
band is the *one* part of a v3 label that is still allowed to touch a classifier input — and it is
exactly where the classifier now fails. v3 removed the circularity from the **class** and could not
remove it from the **band**. So the 89.0 % is a clean measurement of class assignment and a
contaminated one of band assignment, and no amount of re-labelling fixes that: the band is a size
judgement on both sides.

**Coarse top-1 is 100.0 % on all 592 rows.** Whatever else is unsettled, the classifier does not put
a building in the wrong family.

## 4. Comparison with v2 — and what may not be said

v2 was gated at ≥ 0.80 and measured **88.8 %** on 98 graded rows. v3 measures **89.0 %** on **592**
rows under a stricter labelling rule.

⚠️ **These two numbers must not be presented as an improvement, a regression, or a trend.** Checklist
ruling `2a` (2026-08-13) is explicit: every accuracy figure names its fixture, and **no pass mark
carries to a new exam**. v3 is a different exam over 6× the rows with a different answer-key rule.
The correct statement is: *the classifier performs comparably on a much larger and less circular
exam*, and that is a confirmation, not a promotion.

## 5. Gate set for v3 — director ruling, 2026-08-20

Under the user's standing delegation of 2026-08-20. A fixture without a gate is decoration.

| gate | threshold | measured | verdict |
|---|---:|---:|---|
| coarse top-1 | **≥ 0.98** | 1.000 | 🟢 pass |
| fine top-1, height override credited | **≥ 0.85** | 0.890 | 🟢 pass |
| fine top-1, strict | **ungated — diagnostic only** | 0.711 | n/a |

The strict figure is deliberately left ungated. Gating it would force a choice between deleting the
classifier's height rule and corrupting the answer key to match it, and neither is a decision a test
threshold should make quietly.

## 6. Decisions the executor took that the plan did not cover

All four are recorded rather than absorbed, and all four are accepted by the director:

1. **The height override was excluded from ground truth** — the single largest source of disagreement
   (87 of 171 strict errors). Consistent with T02's own labelling rule. Accepted, and it is why §3
   reports two numbers instead of one.
2. **`osm_to_use_class.json` has no `place_of_worship` entry.** The executor treated the tag as
   decisive anyway rather than reproducing the gap in the answer key. Accepted — an answer key should
   record what the building is, not what the mapping file happens to know. ⚠️ The gap itself is real
   and is **flagged, not opened** as an item.
3. **Five rows were hand-resolved from `surplus_tags`** (`osm_id` 29615909, 74451017, 147489619,
   137060374, 148043641) — two landmark hotels, one carrying `rooms=403` which makes `LargeHotel`
   decisive; the Chicago Temple Building, genuinely an office tower with a working church in it; and a
   mosque tagged `building=commercial` that its `name` and `religion` attributes resolve
   unambiguously. Accepted: this is what "go building by building through the raw evidence" means.
4. **The hotel tier threshold follows the classifier's own constant**
   (`_HOTEL_LARGE_MIN_LEVELS = 5`, `building_classifier.py:194`) rather than v2's script's 4.
   Accepted — v3 supersedes v2's convention, and a threshold invented by a fixture-building script is
   not a specification.

## 7. What is NOT claimed

- **No new register ID is opened by this task.** The classifier performs comparably to its previous
  measurement on a larger, cleaner exam. That is not a defect.
- The 290 tag-poor rows are **ungraded** and no accuracy figure of any kind is quoted over them.
- Nothing here restates the adopted fleet baseline, which does not depend on this fixture.

## 8. Artifacts

- `tests/fixtures/labelled_archetypes_tagrich_v3.csv` (592 graded rows)
- `tests/fixtures/labelled_archetypes_tagpoor_v3.csv` (290 ungraded rows)
- `scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py`
- `scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py`
- `openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv`
