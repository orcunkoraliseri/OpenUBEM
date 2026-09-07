# Decision request — `D-EU-108`: what may be admitted to raise London beyond 451/1,242

**2026-09-07.** Plan: `implementation/PLAN_eu-london-coverage-2026-09-07.md` T04. `CP-2` signed.
Every count below is measured from `exclusion_census_2026-09-07.csv` (1,242 rows) and
`neighbour_pairs_2026-09-07.csv` (374 rows) directly for London; nothing is re-quoted from an earlier
doc without re-measurement. No pipeline file is edited by this document.

---

## Option 1 — Straddle intersection

**Measured London count: 0.** This rule is **already implemented in production**, not proposed. The
"+69" in `DEBUG_why-not-100-percent-2026-09-04.md` is a fleet-wide, pre-implementation estimate; it is
not London's residual opportunity today. `scripts/run_eu_s2_district_campaign.py:196-223`
(`_gb_age_decision_multi`) intersects every certificate's band-interval and explicit-year constraints on
a footprint, and is already called from `_gb_rows` at `scripts/run_eu_s2_district_campaign.py:282-284` —
confirmed by re-deriving the census's own blocker histogram: of the 362 `PERIOD_STRADDLE_*` rows, 159 are
multi-band with an **empty** intersection (`DISJOINT_BANDS`) and 0 are multi-band with a still-ambiguous
(≥2-period) intersection — i.e. every multi-band case that this rule *could* resolve, it already has.
**File:line this option would change:** none; already merged (comment cites `D-EU-101 c1`).
**What it still refuses:** all 362 `PERIOD_STRADDLE_*` rows (159 disjoint/contradictory bands + 203
single-certificate rows where the one recorded band's own interval straddles a period boundary and no
observed year narrows it) — genuinely irreducible under this rule, not an oversight.
**Epistemic status:** observation. Deterministic intersection over certificates already in the repo; no
inference added.

## Option 2 — Terrace-row age inheritance

**Measured London count: 307** (T03b, re-derived from `neighbour_pairs_2026-09-07.csv`: 307 of 319
touching-excluded buildings have every prepared neighbour in one TABULA period). Of those 307, **16** also
lack an observed storey count (checked against `exclusion_census_2026-09-07.csv`'s unconditional
`storeys` column) — net immediately admittable on age alone is **291**; the other 16 need Option 3 too
(all 16 do have a single consistent prepared-neighbour storey value, so Option 3 would cover them if also
ruled in).
**File:line this option would change:** `scripts/run_eu_s2_district_campaign.py:285-286` — new logic
inserted where `_gb_age_decision_multi` currently returns `None` and the row is excluded, using the
already-imported `compute_footprint_adjacency` (`:37`, already computed as `is_attached_series` at
`:277`).
**What it still refuses:** the 12 excluded buildings whose prepared neighbours span ≥2 TABULA periods
(T03c — no unambiguous period to inherit), and all 472 excluded buildings (791 − 319) that touch zero
prepared neighbours at all.
**Epistemic status: inference, not observation.** It assumes the excluded building was built at the same
time as its prepared terrace-row neighbours — true for a purpose-built row, false wherever a building was
individually rebuilt (infill, war damage, later redevelopment), which London terraces are known to have.
This is the one option that changes the epistemic status of a row and needs the owner's explicit yes.

## Option 3 — Storey recovery for the 11

**Measured London count: 1 of 11.** Of the 11 `MISSING_OBSERVED_STOREY_COUNT` rows (primary blocker,
already age-resolved), only **1** (`way/823489431`) touches a prepared neighbour at all, and that
neighbour's storey count is a single consistent value (`2.0`).
**File:line this option would change:** `scripts/run_eu_s2_district_campaign.py:317-318` — the existing
storey gate, alongside the SAP-floor-dimensions recovery already there at `:311-316`.
**What it still refuses:** the other 10 of 11 — no prepared neighbour exists to inherit from, so they stay
fail-closed regardless of the ruling.
**Epistemic status: inference, not observation** — same terrace-row-uniformity assumption as Option 2,
applied to storeys instead of age; not flagged as such in the plan's T04 wording, flagged here for
consistency.

## Option 4 — Accept and stop

**Measured London count: 0** (by definition). London stays at 451/1,242 (36.3 %); all 791 excluded stay
excluded. No file changes. No inference introduced.
**What it still refuses:** everything — this option makes no new claim and closes no gap.
**Epistemic status:** observation-equivalent — reasserts the status quo, adds nothing to verify.

---

## Recommendation

Option 1 is already banked (0 to rule on). Options 2+3 together net at most 307 buildings (291 age-only +
16 age+storey) at the cost of one explicitly-labelled inference about terrace-row construction date;
Option 4 leaves the gap. Recommend ruling on Options 2+3 together as one inference-based admission path,
separately from Option 1 (closed) and Option 4 (fallback if declined).

**Owner ruling:** ______________________________________________ (date: __________)

---

## Ruling

**2026-09-07 — owner, verbatim: "yes, admit 2 and 3" / "lets go".**

Options **2** and **3** are admitted. Option 1 is moot (already implemented in production; 0 recoverable).
Option 4 is declined. Every admitted row is stamped with its own provenance value so the observed-only
population (451) stays separable from the observed+inferred population (758) in every later restatement.
Recorded at `CP-3` of `implementation/PLAN_eu-london-coverage-2026-09-07.md`. T05 released.
