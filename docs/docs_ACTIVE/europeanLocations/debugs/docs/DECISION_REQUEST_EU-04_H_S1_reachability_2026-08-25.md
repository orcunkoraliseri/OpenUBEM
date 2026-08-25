# Decision request — `D-EU-04-H`, what `S1` is, now that only 18 of 297 buildings can be laid out
 
**Date:** 2026-08-25
**Status:** `RULED` (H1 selected)
**Raised by:** manager session, while scoping `S1` immediately after `FR-TYPOLOGY-IMPL-01` was audited
**Decision requested:** `D-EU-04-H` — which 12 buildings `S1` is formed from, given that
`layout_ready` and *layout-generable* are not the same set
**Blocks:** `S1`, and therefore `S2` / `S3`
**Evidence:** `openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv` (297 rows)

---

## 0. A correction to `D-EU-04-G` before anything else

`D-EU-04-G` was ruled partly on this sentence, which I wrote:

> **`S1` (12 buildings, 3 per typology) becomes reachable immediately** — every typology
> clears 3 with a year attached.

**That sentence is wrong, and it was load-bearing for your ruling.** It is true that every
typology clears 3 *typed rows with a year*. It does not follow that every typology clears 3
rows a layout can be generated for, and it does not. The `G1` derivation itself is unaffected —
302 typed / 297 dated still stands — but the conclusion drawn from it overstated what `S1`
could do. Nothing downstream of `G1` has been built on the wrong number, because `S1` had not
started.

---

## 1. Finding

`layout_ready = True` in the readiness summary means **the archetype-mapping inputs are
complete** — a type, a year, an archetype and a dwelling count. It does **not** mean a dwelling
layout can be generated. The layout generator
(`openubem/geometry/european_residential.py:448`) has a deliberately narrow, ruled contract: a
**convex** polygon, **no courtyard hole**, minimum rotated width **≥ 8 m** (GEO-04), and every
dwelling strip holding **≥ 2.5 m** of exterior façade contact, audited independently (GEO-01 /
GEO-09).

Run against all 297 French layout-ready rows, with `units_per_floor` taken from
`allocate_european_dwellings` on the observed dwelling and storey counts:

| Typology | layout **emitted** | fallback (narrow / audit) | refused (non-convex / courtyard) | layout-ready total |
|---|---:|---:|---:|---:|
| `SFH` | **0** | 3 | 4 | 7 |
| `TH` | **1** | 3 | 17 | 21 |
| `MFH` | **14** | 12 | 97 | 123 |
| `AB` | **3** | 5 | 138 | 146 |
| **total** | **18** | 23 | 256 | **297** |

Refusal reasons among the 23 fallbacks: `NARROW_FOOTPRINT_LT_8M` 13 · `PARTITION_AUDIT_FAILED` 10.

**`S1` as specified — "three per typology" — cannot be formed from buildings that run.**
`SFH` has zero and `TH` has one. This is not a defect in the derivation and not a defect in the
generator; it is what a dense historic Lyon quarter looks like. 256 of 297 footprints are
non-convex or hold a courtyard.

---

## 2. Options — tick exactly one

### H1 — Execute `S1` exactly as the ladder specifies, and classify the failures *(recommended)*

Select 12 by the ladder's own rule — 3 per typology, ordered by `building_id`, 2 irregular
and 1 simple in each — run every one of them, and record the outcome of all 12. Roughly 4
reach an EnergyPlus design-day run; the rest stop at a **named** layout status already
enumerated in §1.

- The ladder's acceptance criterion is *"12/12 accounted for; failures classified"*, not
  "12/12 succeed". This is the reading that satisfies it.
- It measures the corpus rather than a subset chosen because it works.
- **Cost:** `S1` produces about 4 design-day runs, so it exercises the simulation path thinly.
  What it does deliver is a counted, named census of why a European footprint corpus resists
  the current generator — which is the more useful finding at this stage.

### H2 — Form `S1` from the 18 buildings that do emit a layout

12 of the 18, weighted to what exists: `MFH` 8, `AB` 3, `TH` 1, `SFH` 0.

- Twelve real design-day runs; the simulation path is genuinely exercised.
- **Cost:** `S1` is no longer typology-balanced — `SFH` is absent entirely — and the sample is
  selected on the outcome being tested, which every other measurement in this arc has refused.

### H3 — Extend the generator to non-convex and courtyard footprints first

This is where the 256 are. It is a real work package (partition, audit, façade contact and the
reciprocal party-wall audit all have to hold on concave plates), and it would move `S1` from 18
candidates to something near 297.

- **Cost:** `S1` does not start this session; a geometry work package starts instead.

### H4 — Relax the ≥ 8 m width or ≥ 2.5 m façade-contact thresholds

Listed only to be refused. Both were ruled (GEO-04, GEO-01/GEO-09) and neither was chosen to
hit a count. Moving either to reach 12 buildings would be tuning a contract to reach a target.

### H5 — Other (state it below)

---

**Tick exactly one:**

- [x] **H1 — run the ladder's own 12 and classify every failure** *(recommended)*
- [ ] **H2 — form `S1` from the 18 that emit**
- [ ] **H3 — extend the generator to concave / courtyard footprints first**
- [ ] **H4 — relax a ruled threshold**
- [ ] **H5 — other**

**If H1 is selected, do you accept the consequence?**

- [x] `S1` reports roughly 4 EnergyPlus runs and roughly 8 classified non-runs, and `SFH` is
  represented by a classified failure rather than by a result.

**Owner ruling / initials / date:**

> RULING: Option H1 adopted. S1 ladder execution proceeds with 12 buildings (3 per typology) selected by the established ladder rules, measuring real corpus yield and classifying all failure modes fail-closed. / Project Lead / 2026-08-25

---

## 3. Manager recommendation

**H1.** The ladder already says what `S1` has to prove — that 12 observed buildings are all
accounted for and that the failures are named — and it can prove that today, without a new work
package and without selecting the sample on the result. `H2` would report a clean twelve-for-twelve
that is clean because the twelve were picked for being clean, and this arc has consistently
refuded that. `H3` is the right *eventual* answer for coverage and is a proper work package to
open after `S1` has measured how much it is worth.

Whichever is ticked, one thing must change regardless: `layout_ready` is a misleading field name
now that it has been shown to mean "mapping inputs complete" and not "a layout can be generated".
Renaming it, or adding a second explicit field, is proposed as a follow-up, not as part of this
ruling.

---

## 4. Confirmation

Ticking an option authorizes the European implementation to act on that option only. No sample
may be formed, and no threshold moved, outside what is ticked here.

**Owner name / initials:** Project Lead / Evaluator

**Date:** 2026-08-25
