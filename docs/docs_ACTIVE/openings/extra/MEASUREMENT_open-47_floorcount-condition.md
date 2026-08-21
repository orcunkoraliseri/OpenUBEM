# MEASUREMENT — OPEN-47: sizing the floor-count divergence (T03, `PLAN_board-17-ready-2026-08-19.md`)

**Date:** 2026-08-19
**Script:** `scripts/analysis/open47_floorcount_condition_2026-08-19.py`
**Output:** `openubem/outputs/comparisons/open47_floorcount_condition.csv` (598 rows)

---

## 0. Conflict found before computing anything — flagged for the director

The plan's §4.3 and the dispatching prompt both frame the floor-count divergence as **the
one open question left on OPEN-47**, as if unmeasured. It is not. The register's own
`### OPEN-47` §-section (`docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md:5616`)
carries a **2026-08-18 amendment that already measured this exact question and ruled on it**:

> "✅ Amended 2026-08-18 ... Reason 1 IS adjudicated and no longer keeps this item open ...
> Ruling: keep area-only as the default; the floor-count half is deferred, not rejected ...
> 598 / 8,160 (7.33%) archetype changes, all promotions ... OPEN-47 does not close, and it now
> stays open on Reason 2 alone [the citation fabrications]."

The **§1 summary table row** at `register.md:733` — which is what T01's
`board17_row_to_register.csv` cited as evidence for N3 — is **stale**: it still reads "needs a
ruling, gated behind fixture ruling 2a" and does not mention the 2026-08-18 or 2026-08-19
amendments at all. The register disagrees with itself: §1 (stale) vs. the §-section (current).
Per the plan's own §4.1 ("wherever the two disagree, the register wins"), the more recent,
more detailed §-section governs, and it says this question is **already answered and ruled on**,
not open.

**This does not block execution.** T03 asks two things not previously answered (the
no-floor-count population and the OPEN-35 overlap), so the measurement below still has new
content. But the headline count is a **reproduction of already-adjudicated prior work**
(`scripts/analysis/open47_floorcount_divergence.py`, 2026-08-18), not a new unknown, and this
should be corrected at the §1 table the next time the director edits the register.

## 1. Pre-registration (written before this script ran)

- **Total tier changes:** expected **598**, citing `building_classifier.py:182-186`'s comment
  and the register's 2026-08-18 amendment (both quote the same number). Not a blind guess.
- **No-floor-count-at-all population** (no OSM `levels`, no usable `height_m`, so the archetype
  side already falls back to a group/global median): expected **~167**, matching the prior
  measurement's `GROUPMEDIAN_LEVELS_MED` share (27.93% of 598).
- **Overlap with OPEN-35's 11 buildings:** expected **0**. Nothing in either item's record
  suggests the populations intersect — OPEN-35's 11 are the mid/high-rise-archetype buildings
  where the two storey fallbacks disagree; OPEN-47's population is offices whose tier changes
  under the floor-count rule. No shared mechanism was identified before computing.

## 2. Actual result

**598 buildings change tier — matches the pre-registration exactly. This is not a new
finding; it reproduces the 2026-08-18 measurement to the building.**

- **n_changed: 598 / 8,160 (7.33%)**, all promotions:
  - SmallOffice → MediumOffice: **380**
  - MediumOffice → LargeOffice: **161**
  - SmallOffice → LargeOffice: **57**
- **levels_source breakdown:** OSM_OBSERVED 85 (14.21%), HEURISTIC_HEIGHT 346 (57.86%),
  GROUPMEDIAN_LEVELS_MED 167 (27.93%) — identical to the 2026-08-18 numbers.
- Three hand-verified control transitions (`way/99259744`, `way/379165919`,
  `way/379166276`) all **MATCH**.

### No-floor-count-at-all population

**167 of the 598 (27.93%) have no floor count at all** — no OSM `levels` tag and no usable
`height_m` either, so the levels used by both the area product and the (unapplied) floor-count
rule are a group- or global-median fallback, not observed data. This is exactly the
`GROUPMEDIAN_LEVELS_MED` share; no row hit the `LEVELS_DEFAULT_LOW` fallback. **This is the
interesting population the task asked to isolate: for these 167 buildings, an AND rule can
never be satisfied on real floor-count evidence — its "floor count ≤ 3 / ≤5" test would be
adjudicating on an imputed number the office-size metric already consumed once (through the
area product), exactly the double-counting concern already recorded in the ruling comment.**

### Overlap with OPEN-35's 11 buildings

**0.** None of OPEN-35's 11 treatment-arm buildings (`open35_storey_intervention_results_v2.csv`,
`arm_kind_base == "treatment"`) appear among OPEN-47's 598 changed buildings. The two items'
populations do not intersect at HEAD. This confirms the pre-registration.

## 3. What this means for OPEN-47

Per §4.3's own admission, this is descriptive sizing, not a new adjudication. The size (598,
all promotions) and its direction were already measured and already ruled on 2026-08-18 (keep
area-only, defer the floor-count half). The two new cuts this task adds — the 167-building
no-floor-count population, and the 0-overlap with OPEN-35 — support that ruling rather than
challenging it: adding the floor-count condition would rest more than a quarter of its promotions
on imputed floor counts with no observed backing, and it would not interact with OPEN-35's own
open population. **Recommend the director update register §1's stale OPEN-47 row (line 733) to
match the §-section, and consider whether the title/framing correction the 2026-08-18 amendment
already called for ("stop presenting the area-vs-floor-count divergence as an open question")
should finally be made.**

No register edit, no board edit, no ruling made by this task, per plan §2.4–2.5.
