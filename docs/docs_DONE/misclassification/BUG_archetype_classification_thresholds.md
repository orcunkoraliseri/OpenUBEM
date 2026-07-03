# BUG — Archetype classification thresholds misclassify their own DOE/PNNL prototype buildings

> **Status:** definition only — no code touched. Written for hand-off to a fresh session.
> **Found by:** deep-research audit `docs/docs_ACTIVE/input/deepResearch/RESULT_I02_archetype_classification_cascade.md`
> (commissioned via `I02_archetype_classification_cascade_prompt.md`, run through Gemini Antigravity).
> **Folder note:** the user asked for `docs/docs_ACTIVE/misclassificaiton` — created here as
> `docs/docs_ACTIVE/misclassification` (typo corrected; flag if the typo'd path was intentional).

---

## 1. What the issue is

`openubem/semantic/building_classifier.py` picks one of 30 archetypes per building using a 17-rule
cascade with hardcoded size/level cut-points. Three of those cut-points are wrong in a very
specific, checkable way: **the DOE/PNNL prototype building each archetype is supposed to represent
does not classify into its own archetype** under OpenUBEM's current thresholds. This isn't a vague
calibration concern — it's a logic error confirmed against the source TSDs (Technical Support
Documents) the thresholds were meant to encode.

| Decision | Current OpenUBEM rule | The bug | DOE/PNNL prototype's actual size | Source |
|---|---|---|---|---|
| Office tier | total floor area `< 500` / `< 4000` / `≥ 4000` m² → Small/Medium/Large | The 511 m² **SmallOffice** prototype lands in the *Medium* bucket; the 4,982 m² **MediumOffice** prototype lands in the *Large* bucket | Small = 511 m² (5,502 ft²), Medium = 4,982 m² (53,628 ft²), Large = 46,320 m² (498,588 ft², incl. basement) — Deru et al. (2011), NREL/TP-5500-46861, §3.1.1 Table 3-1, p. 9 | `RESULT_I02` Tables 1 & 3 |
| School tier | footprint area `< 5000` / `≥ 5000` m² → Primary/Secondary | The 6,871 m² **PrimarySchool** prototype (footprint) lands in the *Secondary* bucket | Primary footprint = 6,871 m² (73,960 ft², 1 story); Secondary footprint = 9,796 m² (105,444 ft² per floor; 19,592 m² / 210,887 ft² total across 2 stories) — Deru et al. (2011), §3.1.3 Table 3-1, p. 9 | `RESULT_I02` Tables 1 & 3 |
| Hotel tier | levels `≥ 4` / `< 4` → Large/Small | The 4-story **SmallHotel** prototype lands in the *Large* bucket | Small = 4 stories (43,200 ft² / 4,013 m²); Large = 6 stories (122,120 ft² / 11,345 m²) — Deru et al. (2011), §3.1.13 Table 3-1, p. 9 | `RESULT_I02` Tables 1 & 3 |

A building near any of these three cut-points gets an entirely different envelope, internal-load
density, schedule set, and HVAC system family depending on which side of the line it falls — this
is a step function, not a small numeric error.

**Three other thresholds were checked and are fine — do not touch them:**
- Highrise (≥9 levels) vs. midrise (<9 levels) apartment — matches PNNL-23269 (10-story Highrise /
  4-story Midrise prototypes) and standard multifamily industry convention.
- Large (≥500 m²) vs. small (<500 m²) data center — cleanly bisects the 557 m² / 56 m² DOE
  prototypes (Sun et al. 2021).
- Super-tall (≥40 levels) vs. tall (20–39 levels) building — **GAP**, no DOE/PNNL precedent exists
  above 12 stories; `RESULT_I02` recommends keeping the current value as the defensible default.

---

## 2. Where to look

### Production code — `openubem/semantic/building_classifier.py`, function `_apply_rule_table`

| Rule | Lines (as of this writing) | What's there |
|---|---|---|
| 3a/3b — hotel tier | 177–183 | `if ft in {"hotel","motel","guest_house"} and levels_imputed >= 4: return "LargeHotel"` / `< 4: return "SmallHotel"` |
| 6b/6c — school tier | 205–211 | `if (ft == "school" or bt == "school") and area >= 5000: return "SecondarySchool"` / `< 5000: return "PrimarySchool"` (`area` = `footprint_area_m2`, **not** total floor area) |
| 12a/12b/12c — office tier | 260–266 | `if total_floor_area_m2 < 500: "SmallOffice"` / `< 4000: "MediumOffice"` / else `"LargeOffice"` (`total_floor_area_m2 = footprint_area_m2 × levels_imputed`) |
| 17a — office fallback (untagged `building=yes`) | 297–303 | **Duplicates** the exact same `500`/`4000` literals as rule 12 — this is a second copy-paste site that must be changed in lockstep, or the fallback path silently drifts out of sync with the main rule. This duplication is itself how the two could end up disagreeing if only one is edited. |

None of these six literals (`4`, `5000`, `500`, `4000`, twice) are constructor parameters — unlike
`dominant_tag_threshold`, `high_rise_levels_threshold`, and `super_tall_levels_threshold`, which
*are* exposed on `BuildingClassifier.__init__` (lines 541–555). The broken ones are bare numbers
inline in `_apply_rule_table`.

### Data file (descriptive only, not load-bearing) — `openubem/data/openstudio_archetypes.json`

`default_size_signature` strings describe the same thresholds in prose for human readers. Confirmed
via repo-wide grep: **no code reads this field** — it's display-only metadata, safe to update without
behavior risk, but should be kept in sync so the file doesn't lie to the next reader.

| Archetype | Line | Current string |
|---|---|---|
| SmallOffice | 8 | `"< 500 m² floor area"` |
| MediumOffice | 23 | `"500–4000 m² floor area"` |
| LargeOffice | 38 | `">= 4000 m² floor area"` |
| SmallHotel | 88 | `"< 4 floors lodging"` |
| LargeHotel | 95 | `">= 4 floors lodging"` |
| PrimarySchool | 130 | `"OSM school (default) or kindergarten, footprint < 5000 m²"` |
| SecondarySchool | 137 | `"OSM school + footprint >= 5000 m² (ASSUMPTION_DOE_PROTOTYPE_DERIVED, OQ-4-FOLLOWUP)"` — note the existing `OQ-4-FOLLOWUP` marker: this threshold was **already internally flagged as an open question** before this audit: confirms it as a real, previously-known soft spot, not a new invention. |

### Tests that hardcode the current (wrong) thresholds — `tests/test_building_classifier.py`

These assert specific archetype outputs at the exact boundary values and **will fail or silently
stop testing the right thing** once the thresholds change — they must be updated, not just left
passing:

- Lines 265, 268 — footprint=800, levels=2 → total=1600 → asserts `MediumOffice`
- Lines 317–332 — three cases at total floor area 3000/10000/360, asserts Medium/Large/Small via
  `RULE_USE_CLASS_SIZE` and `FALLBACK_SIZE_DEFAULT` respectively (this second one exercises rule 17a)
- Lines 510–515 — `building=yes`, levels=2, footprint=800 → total=1600 → asserts `MediumOffice`
- Lines 531, 539 — asserts `SecondarySchool` / `PrimarySchool` from a synthetic fixture
- **Lines 914–923 — the explicit boundary-value table**, with comments citing the exact DESIGN
  thresholds this bug report disputes:
  - `area=500.0` → asserts `MediumOffice` ("DESIGN §3C: 500 ≤ area < 4000")
  - `area=4000.0` → asserts `LargeOffice` ("DESIGN §3C: area ≥ 4000")
  - `area=5000.0` + school tag → asserts `SecondarySchool` ("DESIGN §3C rule 6b: area ≥ 5000")
  - `levels=4` + hotel tag → asserts `LargeHotel` ("DESIGN §3C rule 3a: levels ≥ 4")

These four boundary assertions are the test-level mirror of the bug — they were written to match the
current (wrong) thresholds and currently pass *because* the bug exists. Fixing the bug means these
specific assertions must change to the new threshold values, plus new test cases should assert the
actual DOE prototype sizes from §1's table land in their own archetype (the regression test for the
bug itself: a 511 m², 1-story building must classify as `SmallOffice`, not `MediumOffice`, etc.).

### The binding spec these thresholds came from — DESIGN §3C

The code comments (`tests/test_building_classifier.py` lines 914–923) and the `OQ-4-FOLLOWUP` marker
both point to **DESIGN §3C** as the literal source of `500`, `4000`, `5000`, and `4`. Per
`CLAUDE.md`, DESIGN docs are never edited directly. The project already has a working pattern for
this exact situation — see §4 below.

---

## 3. How to solve

1. **Decide the school-tier fix.** `RESULT_I02` offers two options and does not pick one for
   OpenUBEM:
   - **Option A (area threshold bump):** change `5000` → `8000` m² footprint. Minimal diff, same
     rule shape.
   - **Option B (switch to level count):** Primary = 1 story, Secondary = 2+ stories. `RESULT_I02`
     calls this "a highly robust discriminator" since it's exactly how the two DOE prototypes differ
     structurally, not just by area. This changes the *kind* of rule (footprint-area test →
     level-count test), which is a bigger code change but arguably more robust on real building
     stock where footprint area is noisier than floor count.
   This is a spec decision, not a mechanical fix — **stop and get sign-off before implementing**, per
   `CLAUDE.md`'s "stop and ask on spec ambiguity" rule.

2. **Update the literals in `_apply_rule_table`** (and the duplicated copy in rule 17a):
   - Hotel: `>= 4` → `>= 5` (rules 3a/3b).
   - School: per the decision in step 1 (rules 6b/6c).
   - Office: `< 500` / `< 4000` → `< 2322` / `< 9290` (rules 12a/12b/12c **and** 17a) — these are the
     LBNL CBES bins (25,000 ft² / 100,000 ft² → 2,322 m² / 9,290 m²), cited in `RESULT_I02` as
     matching the DOE Small/Medium/Large Office prototypes correctly. Consider extracting a shared
     `_office_tier(total_floor_area_m2) -> str` helper instead of leaving the literals duplicated
     between rule 12 and rule 17a — the duplication is exactly how the two could silently disagree
     again in the future. Optional but recommended; not required to fix the bug itself.

3. **Update `openstudio_archetypes.json`'s `default_size_signature` strings** (lines 8, 23, 38, 88,
   95, 130, 137) to match the new numbers. Cosmetic only — confirmed no code reads this field — but
   leaving it stale would mislead the next reader.

4. **Record a DESIGN erratum**, following the project's existing convention in
   `openubem/data/construction/PROVENANCE.md` (see `Ruling R-2.2-1/2/3`, format: *"DESIGN §X said
   `<old value>` — recorded as DESIGN erratum"* with the source-true value and citation). There is
   currently **no PROVENANCE.md for the root-level `openubem/data/*.json` files**
   (`openstudio_archetypes.json`, `osm_to_use_class.json`, `cbecs_pba_map.json`) — decide whether to
   create one (`openubem/data/PROVENANCE.md`) or find another appropriate home; either way, cite
   `RESULT_I02` as the source for the new threshold values, mirroring the R-2.2-* ruling format
   exactly so the project's erratum trail stays consistent.

5. **Update the test boundary values** in `tests/test_building_classifier.py` (the specific lines
   listed in §2) to the new thresholds, and **add explicit regression tests** asserting that each DOE
   prototype's actual size (511 m²/1-story office, 4,982 m²/3-story office, 6,871 m² 1-story school,
   4-story hotel, 6-story hotel) now lands in its own archetype — this is the direct test for the bug
   this document describes, and should not regress silently in the future.

6. **Re-validate before treating this as adopted.** Per project memory, the current archetype
   classification feeds the **Phase-E "ADOPTED BASELINE"** (8,160 buildings, R² 0.90/0.92/0.72, city
   deltas −24/−6/−26%), which is recorded as **🔒 ARC FULLY CLOSED (2026-06-27)**. Changing these
   thresholds reclassifies an unknown number of real buildings in the validation fleet (likely a
   non-trivial share, since office buildings are the single most common commercial archetype) — each
   reclassified building gets a different envelope/loads/HVAC system, which can move the headline
   validation numbers. **Do not fold this fix into the closed Phase-E baseline silently** — re-run the
   archetype distribution + validation suite (`docs/docs_DONE/hvac-ServiceLoads/REPORT_phaseE_final.md`
   describes the gates) and report the before/after delta to the user before considering this fix
   "done." Treat this as reopening a small sub-arc of Phase-E, not a drive-by patch.

---

## 4. Related but explicitly out of scope here

Two other findings from the same deep-research round are **not** part of this bug and should not be
folded into this fix:

- **`RESULT_I01`** (OSM tag → use-class mapping) — the symmetric tag-agreement rule and ~24 missing
  OSM tags are a *design recommendation*, not a confirmed logic bug like this one. Separate decision.
- **`RESULT_I03`** (CBECS PBA crosswalk) — the archetype↔CBECS mapping is "correct but coarser than
  necessary"; no bug, just an optional precision improvement to validation scoring.

Both are already cross-referenced in `docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md` §1/§2/§6.
If you want bug-definition docs for those too, they'd need their own write-up — neither is a
clear-cut "the code is wrong" finding the way this one is.

---

*OpenUBEM — bug definition. Source: `RESULT_I02_archetype_classification_cascade.md`. No code
changed by this document. 2026-06-30.*
