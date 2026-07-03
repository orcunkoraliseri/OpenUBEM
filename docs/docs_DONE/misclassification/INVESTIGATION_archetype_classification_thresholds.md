# INVESTIGATION — Archetype classification thresholds (verification of `BUG_archetype_classification_thresholds.md`)

> **Status:** investigation only — **no code, no plan, no implementation.** Manager-authored.
> **Companion to:** `BUG_archetype_classification_thresholds.md` (same folder).
> **Source evidence:** `RESULT_I02_archetype_classification_cascade.md`, `openubem/semantic/building_classifier.py`,
> `openubem/data/openstudio_archetypes.json`, `tests/test_building_classifier.py`,
> DESIGN §3C (`docs/docs_main/docs_step2/DESIGN_...openstudio-archetyp.md`),
> `docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md`,
> `openubem/data/construction/PROVENANCE.md`.
> **Date:** 2026-06-30.

---

## 0. Purpose

The bug report asserts three classification cut-points misclassify their own DOE/PNNL prototype
buildings. Before any plan is written, this document **independently verifies every load-bearing
claim against the actual code and specs**, then surfaces what the bug report **missed or under-stated**
— in particular two findings that materially change how the fix should be scoped, recorded, and
re-validated. It ends with the **decision points** that must be put to the user before a PLAN doc is
authored. It deliberately stops short of proposing implementation.

---

## 1. Verdict at a glance

**The bug is real and confirmed.** All three claimed misclassifications reproduce against the current
code and are corroborated by the DOE/PNNL Technical Support Documents cited in `RESULT_I02`. The bug
report's code citations, threshold values, and "do-not-touch" exclusions are all accurate. The fix is
**not** a drive-by patch: it lands on a rule that has *already been amended twice* (errata E-R3-1,
E-R3-2), it is gated by a **user-ratified labelled-accuracy fixture** that the last amendment had to
clear, and it has a **large, asymmetric blast radius** on the office sector. Those three facts (§3)
are the reason this needs a managed sub-arc, not a one-line edit.

---

## 2. Claim-by-claim verification of the bug report

| # | Bug-report claim | Status | Evidence |
|---|---|---|---|
| 1 | Hotel rule `levels ≥ 4 → LargeHotel` at lines 177–183 | ✅ exact | `building_classifier.py:178,182` |
| 2 | School rule `footprint ≥ 5000 → SecondarySchool` at 205–211, keyed on `footprint_area_m2` not total | ✅ exact | `building_classifier.py:206,210` (`area` = `footprint_area_m2`, line 151) |
| 3 | Office rule `< 500 / < 4000 / else` at 260–266 | ✅ exact | `building_classifier.py:262,264,266` |
| 4 | Office **fallback** rule 17a duplicates the `500/4000` literals at 297–303 | ✅ exact — second copy-paste site confirmed | `building_classifier.py:299,301` |
| 5 | None of the six literals are constructor params (unlike `*_levels_threshold`) | ✅ confirmed | constructor lines 541–555 expose only `dominant_tag`, `high_rise`, `super_tall` |
| 6 | `default_size_signature` is read by **no code** (display-only) | ✅ confirmed | repo-wide grep: only `openstudio_archetypes.json` references it |
| 7 | DOE prototype sizes (Small 511 m²/1-story, Medium 4,982 m²/3-story, Primary 6,871 m², SmallHotel 4-story, LargeHotel 6-story) | ✅ matches source | `RESULT_I02` Table 1 (Deru et al. 2011, NREL/TP-5500-46861, Table 3-1, p.9) |
| 8 | Three "fine, do not touch" thresholds (highrise ≥9, datacenter ≥500, super-tall ≥40) | ✅ confirmed correct | `RESULT_I02` Table 3 rows 1,2,5 |
| 9 | No `openubem/data/PROVENANCE.md` exists for root data files | ✅ confirmed | PROVENANCE.md only under `construction/`, `climate_zones/`, `carbon/` |
| 10 | PROVENANCE erratum format `R-2.2-x: "DESIGN §3C said X — recorded as DESIGN erratum"` exists | ✅ confirmed | `construction/PROVENANCE.md:33–44` (R-2.2-1/2/3) |
| 11 | Test boundary table at 914–923 hardcodes the disputed thresholds with DESIGN §3C comments | ✅ confirmed | `test_building_classifier.py:913–929` |
| 12 | `OQ-4-FOLLOWUP` marker on the school threshold in the JSON (line 137) | ✅ confirmed — **and stronger than reported** (see §3.I) | `openstudio_archetypes.json:137` |

**No claim in the bug report was found to be wrong.** The corrected target threshold values it carries
forward from `RESULT_I02` (office `2322 / 9290`; hotel `≥5`; school `8000` or level-count) are
faithfully transcribed.

---

## 3. What the bug report missed or under-stated (the load-bearing additions)

These are the findings that change scoping/recording/validation. **A** and **B** are the two that most
alter the plan.

### 3.A — The office rule has *already* diverged from DESIGN once; the fix is metric-consistent and is the **next entry in an existing erratum series**

The bug report treats the office literals as straight-from-DESIGN. They are not. **DESIGN §3C rules
12a–c key on `footprint_area_m2`** (DESIGN §3C lines 162–164, 211–213), but the **code keys on
`total_floor_area_m2 = footprint × levels`** via a user-ratified amendment **E-R3-1**
(`building_classifier.py:152–153`; recorded in `PLAN_step-2-classifier-coverage-R3.md:53`). E-R3-1
changed the *metric* but **deliberately left the threshold values at 500/4000** ("thresholds
unchanged" — R3 PLAN line 53).

Two consequences:

1. **The fix is metric-consistent — good news.** `RESULT_I02`'s recommended office bins
   (`2322 / 9290 m²`) are **total-floor-area** values (LBNL CBES GFA bins, 25,000/100,000 ft²). They
   slot directly onto the code's existing total-floor-area metric. No metric change is needed; only the
   numbers move. This bug fix is effectively **the second half of E-R3-1**: E-R3-1 fixed the metric and
   left the values; this fixes the values.
2. **An erratum home and naming convention already exist.** Errata E-R3-1 and E-R3-2 were recorded as a
   **§5 "DESIGN errata" block in the R3 PLAN doc, user-ratified in conversation** (R3 PLAN line 5:
   "the user is the spec owner and has ratified both"). This is a *more direct precedent* than the
   bug report's suggestion to mint a new `openubem/data/PROVENANCE.md`. The natural recording site for
   this change is an **E-R3-3 entry in the same erratum mechanism**, not a new file. (Decision point —
   see §4.)

> Note: rule 17a is itself amendment **E-R3-2** (`PLAN...R3.md:64`). So *both* office sites the bug
> report flags are already errata-amended rules. This is an actively-maintained rule with a paper trail,
> which lowers the risk of the fix but raises the requirement to record it in lockstep.

### 3.B — There is a **user-ratified labelled-accuracy gate** the previous change had to clear; that is the first re-validation, not Phase-E

E-R3-1/E-R3-2 were validated against an **OQ-7 50-label fixture** at **≥70% fine / ≥90% coarse top-1
accuracy** (CP-α) **and** a **Boston 483-building fleet re-run with CBECS gates** (CP-β:
CV(RMSE) 53.78 / NMBE −10.81 / R² 0.731 / KS 0.190) — R3 PLAN lines 6, 41–43.

This is decisive for re-validation strategy. The bug report points only at the heavier Phase-E REPORT
gates. But the **direct, cheaper, already-built gate** for *classifier* changes is the OQ-7 labelled
fixture + Boston CBECS baseline. The new thresholds **must clear the same ≥70%/≥90% bar the last
amendment cleared.** Because the 50-label fixture and Boston baseline were measured *with the 500/4000
thresholds in place*, moving to 2322/9290 **could move OQ-7 accuracy in either direction** — plausibly
*up* (it fixes DOE-prototype self-classification) but this must be measured, not assumed.
**Recommended re-validation order:** OQ-7 accuracy gate → Boston CBECS gate → only then consider the
full Phase-E fleet. (See §4 decision on whether Phase-E must be reopened at all.)

### 3.C — Blast radius is **large and asymmetric**, not "non-trivial"

The bug report says the fix reclassifies "likely a non-trivial share." It is sharper than that on the
office sector:

- The **current** `SmallOffice` bucket is `total_floor_area < 500 m²` — i.e. footprint × levels < 500.
  In any real fleet this bucket is **nearly empty** (a building must be smaller than ~500 m² of total
  floor area). So today **almost every commercial building lands in Medium or Large.**
- The **new** `SmallOffice` bucket is `< 2322 m²` — **wide.** A large share of buildings currently
  labelled `MediumOffice` (the `[500, 2322)` band) move **Medium → Small**, and a chunk currently
  `LargeOffice` (`[4000, 9290)`) move **Large → Medium**.
- `SmallOffice` / `MediumOffice` / `LargeOffice` differ not only in EUI but in **HVAC system family**
  (packaged single-zone vs. VAV). This is a step-change in modeled energy for every reclassified
  building, skewed toward *smaller* office archetypes. **This is the single biggest validation risk**
  and the reason CP-β (fleet CBECS) cannot be skipped.

Hotel and school blast radii are narrow by comparison: the hotel change only moves **exactly-4-story
hotels** (Large → Small); the school change only moves schools near the boundary.

### 3.D — The `500` / `5000` / `4000` literals are **overloaded**; a blanket find/replace would corrupt unrelated rules

Verified occurrences of the literals (grep over `openubem/`):

| Literal | CHANGE (office/school fix) | KEEP (must not be touched) |
|---|---|---|
| `500` | office 12a (`:262`), office fallback 17a (`:299`) | **data-center** 9a/9b (`:227,234`) — confirmed correct by `RESULT_I02` Table 3 row 5; **zoning** `geometry/zoning.py:32` (perimeter/core split); occupant-density bound `semantic/__init__.py:76` |
| `4000` | office 12b (`:264`), office fallback 17a (`:301`) | — |
| `5000` | school 6b (`:206`), school 6c (`:210`) | Warehouse occupant density note in `construction/PROVENANCE.md:114` (prose only) |
| `4` (levels) | hotel 3a/3b (`:178,182`) | — |

**Implication for the plan:** the edit must be **surgical and rule-targeted**, never a literal-level
search/replace. The R3 PLAN already learned this for E-R3-1 (it kept a *separate* `total_floor_area_m2`
local precisely so the tall-building rules' `area` semantics were untouched — R3 PLAN line 117).

### 3.E — School tier: Option A vs Option B is a **genuine** spec decision, with real-stock consequences

- Rules 6b/6c key on **`footprint_area_m2`** (not total floor area), so they are *inconsistent* with the
  office rule's metric. **Option A** (bump `5000 → 8000` footprint) keeps that footprint metric and the
  rule shape — minimal diff, and `8000` cleanly separates the DOE Primary footprint (~6,871 m²) from
  Secondary (~9,796 m²/floor) per `RESULT_I02` §Part C #4.
- **Option B** (Primary = 1 story, Secondary = 2+ stories) keys on the *actual structural difference*
  between the two DOE prototypes (1 vs 2 stories). It is more robust on real stock, where a compact
  2-story secondary school can have a *smaller* per-floor footprint than a sprawling 1-story primary —
  a case Option A would misclassify but Option B would not.
- **Asymmetry to preserve:** rule 6b (Secondary) matches only `school`; rule 6c (Primary) matches
  `school` **or** `kindergarten` (`:206` vs `:210`). Whichever option is chosen, kindergarten must stay
  Primary. Option B also has to decide what a kindergarten with 2 imputed levels does.

### 3.F — Zero-fitted-params and vintage-blind invariants are **preserved** by the fix

DESIGN §3C line 352 enshrines "**No fitted parameters** … every numeric boundary … taken verbatim from
the spec," and the project's standing rule is zero-fitted-params. The replacement numbers
(`2322/9290` = LBNL CBES 25k/100k ft²; `≥5` and `8000`/level-count = DOE prototype story/footprint
counts) are **sourced from published TSDs, not calibrated.** The fix swaps one set of *sourced* literals
for another set of *sourced* literals — it does **not** introduce calibration, and archetype selection
stays vintage-blind (`RESULT_I02` Table 4 / §"Vintage Influence"). This framing should be stated
explicitly in the erratum so the fix is not mistaken for fitting.

### 3.G — Confidence tiers are unaffected

Office tier emits `RULE_USE_CLASS_SIZE` → MEDIUM (`:345–346`); fallback 17a → LOW (`:330–331`). Moving
the bucket *boundaries* does not touch which token fires, so **no confidence-tier regression** — worth
stating so a reviewer doesn't go looking for one.

### 3.H — The data-driven rule table DESIGN §3C intended was never built

DESIGN §3C (line 28) specifies a bundled **`archetype_size_rules.json`** `(footprint_area_m2, levels) →
archetype_id` table. **It does not exist** (glob: no match). The rules were implemented as hardcoded
literals in `_apply_rule_table` instead. This is why the thresholds are inline and not a clean
data-file edit — context only, not part of this fix's scope, but it explains the shape of the problem.

### 3.I — OQ-4 was flagged in DESIGN itself, not just the JSON

The bug report notes the `OQ-4-FOLLOWUP` marker in the JSON. Stronger: the school threshold is an
**open question in the DESIGN doc's own open-questions list** — DESIGN §3C **OQ-4** (line 379): *"the
5,000 m² threshold is a guess … should this be flagged as an assumption pending a labelled-school
dataset?"* `RESULT_I02` is precisely the documented basis OQ-4 was waiting for. This makes the school
fix a *resolution of a pre-registered open question*, which strengthens the case for adopting it.

---

## 4. Decision points for the user (must be settled before a PLAN is written)

1. **School-tier rule shape — Option A (footprint `8000 m²`) vs Option B (level count, Primary=1 /
   Secondary≥2).** This is the one spec ambiguity the bug report itself flags as stop-and-ask. §3.E
   lays out the tradeoff. *Manager lean: Option B* (keys on the true structural difference; more robust
   on noisy real footprints), but this is the user's call.
2. **Where the erratum is recorded.** Precedent (§3.A/3.B) says the cleanest home is an **E-R3-3 entry
   in the R3 PLAN's §5 erratum mechanism** (user-ratified), mirroring E-R3-1/E-R3-2 — *not* a new
   `openubem/data/PROVENANCE.md`. Confirm this, or direct otherwise.
3. **Re-validation depth.** Minimum is **CP-α (OQ-7 50-label accuracy ≥70%/≥90%) + CP-β (Boston 483
   CBECS gates)** — the exact gates E-R3-1/E-R3-2 cleared. Question: does the user also want the **full
   Phase-E fleet (8,160 buildings) re-run** before treating this as adopted (bug-report step 6), or is
   reopening Phase-E deferred until after the office reclassification's direction is known from CP-β?
4. **Office stories-qualifier (minor).** LBNL CBES uses GFA **and** a stories condition; OpenUBEM would
   adopt **area-only bins on total floor area.** This is defensible because the total-floor-area metric
   already folds in stories (a tall slim tower accrues large total area — see `test_rule_12c_tall_slim_tower`).
   Recommend area-only; confirm no stories qualifier is wanted.

---

## 5. Tests that will move (for the eventual plan — not changed here)

Computed against the candidate office bins `2322 / 9290` (total floor area) so the plan author knows
exactly which assertions flip vs. survive:

| Test | Fixture | Current → New | Action |
|---|---|---|---|
| `TestExactBoundaries` `:915` | office, total=500 | Medium → **Small** | update assertion |
| `TestExactBoundaries` `:917` | office, total=4000 | Large → **Medium** | update assertion |
| `test_rule_17a_building_yes_size_default` `:268` | total=1600 | Medium → **Small** | update assertion |
| `test_rule_17a_building_yes_office_default` `:515` | total=1600 | Medium → **Small** | update assertion |
| `test_rule_12b_medium_office` `:320` | total=3000 | Medium → **Medium** | survives (no change) |
| `test_rule_12c_tall_slim_tower` `:326` | total=10000 | Large → **Large** | survives (no change) |
| `test_rule_17a_building_yes_small` `:332` | total=360 | Small → **Small** | survives (no change) |
| `test_rule_6b_secondary_school` `:527` | school, footprint=6000, levels→1 | Secondary → **Primary** under *either* option | **fixture is mis-sized** — 6,000 m²/1-story is DOE-*Primary*-sized; rewrite with a genuinely-secondary fixture (≥8000 footprint or ≥2 stories) |
| `TestExactBoundaries` `:919` | school, footprint=5000 | Secondary → Primary (Opt A) | update per chosen option |
| `TestExactBoundaries` `:923` | hotel, levels=4 | Large → **Small** | update assertion |

Plus **new regression tests** asserting each DOE prototype lands in its own archetype (511 m²/1-story →
SmallOffice; 4,982 m²/3-story → MediumOffice; 6,871 m²/1-story → PrimarySchool; 4-story hotel →
SmallHotel; 6-story hotel → LargeHotel). The §2-row-12 finding — that `test_rule_6b_secondary_school`
asserts Secondary on a Primary-sized fixture — is itself a small confirmation that the test suite
encodes the bug, not just the production code.

---

## 6. Scope fence (confirmed)

- **`RESULT_I01`** (OSM tag → use-class map) and **`RESULT_I03`** (CBECS PBA crosswalk) are **out of
  scope** — both are design *recommendations*, not confirmed logic bugs, exactly as the bug report
  states. Verified: neither asserts "the code produces a wrong archetype for a known prototype."
- This fix touches **only** the hotel/school/office cut-points in `_apply_rule_table` (and the 17a
  copy), the cosmetic `default_size_signature` strings, the affected tests, and an erratum record. It
  must **not** touch the data-center `500`, the zoning `500`, or any `*_levels_threshold`.

---

## 7. What this investigation does NOT do

No code changed. No PLAN doc written. No threshold edited. The school-tier rule shape (§4.1), the
erratum home (§4.2), and the re-validation depth (§4.3) are **open decisions for the user.** Once those
three are settled, the manager can author a PLAN doc (errata E-R3-3, surgical rule edits, test updates,
DOE-prototype regression tests, CP-α/CP-β re-validation) for a fresh Sonnet to execute.

---

*OpenUBEM — investigation. Verifies `BUG_archetype_classification_thresholds.md` against code + specs.
No code changed. 2026-06-30.*
