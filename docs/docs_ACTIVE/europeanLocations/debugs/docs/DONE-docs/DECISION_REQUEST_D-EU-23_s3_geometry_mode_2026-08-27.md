# Decision request: D-EU-23 — how `S3` is built, now that the binding ceiling is geometry and not attributes

**Status:** CLOSED (Ruled 2026-08-27: Option G1)
**Opened:** 2026-08-27
**Raised by:** director, on a measurement taken while closing `D-EU-22`
**Blocked (now released):** `S3` sample formation and the FR + ES attribute ingestion that `D-EU-22` routed to — **both are authorised by the ruling in §0.**
**Does not block:** anything else. `D-EU-22` stays closed and its verdicts stand; `S2` stays accepted;
`§9.4` stays closed and `v1.0` stays frozen; the `EU-04` geometry contract is **not** reopened by this
request.

---

## 0. Ruling — 2026-08-27

**Option G1. `S3 = 96`, mixed mode, the layout axis and the simulation axis never collapsed.**
The owner's own words, recorded verbatim in §6:

> *S3 sample formation proceeds at N=96 using the mixed-mode architecture established in S2
> (dwelling-partitioned where the EU-04 contract emits; one_zone_per_floor fallback where
> geometric/partition audit boundaries apply). Both layout mode and simulation mode axes must be
> printed explicitly in all S3 acceptance panels. FR + ES ingestion for Madrid and Lyon is fully
> authorized to proceed.*

**What the ruling settles.**

1. **`S3` stays at 96.** Table 10's count is **not** amended, so `G3` is refused and the balance rule
   is untouched.
2. **The geometry contract is NOT reopened.** `GEO-04`'s 8 m width, the convexity refusal and the
   courtyard refusal all stand exactly as ruled, so `G2` is refused — reaching 96 by relaxing them
   would be selecting the method on the outcome, which `D-EU-04-H` forbids. 🔴 **If the ceiling
   itself is ever to be raised, that is a separate request against the geometry contract, with its own
   evidence — never a clause inside a sample decision.**
3. **Both axes are printed, always.** The **layout axis** (dwelling-partitioned vs
   `one_zone_per_floor`) and the **simulation axis** are recorded in separate columns, as
   `D-EU-04-H` already requires, and the split appears in **every** `S3` acceptance panel and report.
4. 🔴 **`S3`'s headline `96` therefore does not imply dwelling-level geometry.** No result
   quoted from `S3` may travel without its own partitioned / massing split. This is the standing
   caveat the ruling buys, and it is the same one `S2` carries (5 of 31 partitioned, 26 massing).
5. **The FR + ES attribute ingestion is AUTHORISED** — Lyon and Madrid, on this basis. `G4`
   (defer until London is unblocked) is refused: London is the worst of the four on this ceiling
   (49 of 1,242), so waiting widens the balance, not the ceiling.

**Continuity, not concession.** This is the architecture `S1` and `S2` already ran, so the ruling
introduces **no new precedent** and changes **nothing** that had been ruled before it.

⚪ **What is still true and unchanged by this ruling:** the measured dwelling-partitioned figure
is **18** (Lyon). `~40` and `~73` in §2 are **planning projections from one site's rate onto an
unmeasured urban form** — no acceptance may quote them as results.

*Ruled and closed 2026-08-27. Archived to `DONE-docs/` the same day; citation sweep performed.*

---

## 1. Why this exists

`D-EU-22` closed on a good result: Madrid's attributes cover, so `S3` becomes an **FR + ES**
binational sample and the ingestion work is worth doing. That closure answers *which sites can supply
a year and a typology*. It does not answer *how many of their buildings the ruled layout contract can
actually build*, and those are different questions with different answers.

🔴 **The corpus has a second ceiling, and it is roughly four times tighter than the attribute one.**
Attributes would make **1,183 of 1,194** Madrid footprints usable. The layout contract accepts
**63**.

⚪ This is not a new failure. It is the same fact `S1` measured in Lyon and that
`ACCEPTANCE_S2_promotion_2026-08-27.md` recorded when it noted that **26 of `S2`'s 31 buildings ran
as massing boxes**. What is new is that the number has now been measured for **all four sites** rather
than one, and `S3` is the first stage where it decides formability.

---

## 2. The measurement

Offline, no live retrieval, no ingest. The predicates are **imported** from
`openubem.geometry.european_residential`, not re-implemented — the same
`audit_real_footprint_manifest` that produced `real_footprint_feasibility_summary.json`. Evidence:
`openubem/outputs/eu_evidence/EU-04/D-EU-22/layout_contract_ceiling.json`.

| Site | Footprints | Non-convex | Courtyard | `< 8 m` | **Clears the geometric half** |
|---|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 1,194 | 1,087 | 136 | 287 | **63** (5.3 %) |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 451 | 18 | 117 | **52** (9.8 %) |
| `GB-LDN-STDUNSTANS` | 1,242 | 469 | 3 | 1,034 | **49** (3.9 %) |
| `IT-BOL-GALVANI2` | 1,220 | 1,055 | 231 | 410 | **40** (3.3 %) |
| **all four** | **4,186** | | | | **204** |

🔴 **Clearing the geometric half is not emission.** The ruled contract also runs the partition audit
and the 2.5 m facade-contact test. Lyon is the **only** site where emission has ever been measured, so
its rate is the only calibration in existence: of its **28** attribute-ready footprints that clear the
geometric half, **18 emitted** and **10 failed `PARTITION_AUDIT_FAILED`** — a survival rate of
**64.3 %**.

**What that gives for a binational `S3`:**

| Basis | FR | ES | FR + ES | `S3` target |
|---|---:|---:|---:|---:|
| Measured today | **18** | 0 (not ingested) | **18** | 96 |
| ES ingested, Lyon rate applied to its 63 | 18 | **~40** | **~58** | 96 |
| Both sites fully attribute-ready, Lyon rate on all clearing footprints | ~33 | ~40 | **~73** | 96 |

⚪ **~40 and ~73 are planning figures projected from one site's rate onto an unmeasured urban form.**
They are not results and no acceptance may quote them. The measured figure is **18**. But every basis
on the table lands **below 96**, and the gap is not closed by the ingestion `D-EU-22` authorised.

---

## 3. What is actually being asked

**A `96`-building `S3` in which every building is dwelling-partitioned is not formable from FR + ES on
any basis measured so far.** A 96-building `S3` that accepts the already-ruled
`one_zone_per_floor` fallback **is** formable today — that is exactly how `S2` ran, 26 of 31.

So the question is not whether `S3` can exist. It is **what `S3` is allowed to be made of**, and that
is a composition rule, which is the owner's.

---

## 4. Options

**Option G1 — `S3 = 96`, mixed mode, two axes never collapsed.** *(recommended)*
Dwelling-partitioned wherever the contract emits, ruled `one_zone_per_floor` fallback everywhere else,
with the **layout axis** and the **simulation axis** recorded in separate columns exactly as
`D-EU-04-H` already requires. Every acceptance panel prints the split.
*Cost:* `S3`'s headline number stops implying dwelling-level geometry, and every result quoted from it
must carry its own split. *Why recommended:* it is the only option that changes nothing that has been
ruled — not the geometry contract, not Table 10's count, not the ladder's selection rule — and it is
what `S1` and `S2` already did, so it introduces no new precedent.

**Option G2 — `S3 = 96`, dwelling-partitioned only.**
*Cost:* not formable on today's measurement. It requires relaxing `GEO-04`'s 8 m width, the convexity
refusal, or the courtyard refusal — **a change to the ruled geometry contract, not to the sample.**
🔴 Relaxing a contract in order to reach a sample size is selecting the method on the outcome, which
`D-EU-04-H` exists to forbid. Recorded as available, not recommended.

**Option G3 — shrink `S3` to the dwelling-partitioned population that actually exists.**
Table 10's `96` becomes a measured number rather than a target, and the balance rule is re-derived
from what emits. *Cost:* Table 10 is amended and the amendment must say **why**; `n` per typology
falls far enough that some cells may be single-digit, and every such `n` must travel with the result.

**Option G4 — defer `S3` until London is unblocked.**
The owner obtains a GOV.UK One Login bearer token, `GB` is measured, and the pool becomes
three-country. *Cost:* a slice of delay, and 🔴 **it does not change the ratio** — London clears the
geometric half on 49 of 1,242, the worst of the four. It widens the balance, not the ceiling.

---

## 5. Recommendation

**Option G1**, and if the owner also wants the ceiling itself raised, that is a **separate** request
against the geometry contract with its own evidence — never a clause inside a sample decision.

⚪ **What must not happen either way:** an `S3` acceptance that reports 96 buildings without printing
how many of them were dwelling-partitioned. `S2`'s acceptance did print it (5 of 31), and that is the
only reason this ceiling was visible in time to raise this request.

---

## 6. Owner response

```
D-EU-23 ruling: Option G1 (96, mixed mode, two axes printed)
(G1 = 96, mixed mode, two axes printed / G2 = 96, dwelling-partitioned only
 G3 = shrink S3 to what emits / G4 = defer until London is unblocked)

If G1: is the FR + ES ingestion authorised to proceed on that basis?   YES

Notes: Formally approved. S3 sample formation proceeds at N=96 using the mixed-mode
architecture established in S2 (dwelling-partitioned where the EU-04 contract emits;
one_zone_per_floor fallback where geometric/partition audit boundaries apply). Both
layout mode and simulation mode axes must be printed explicitly in all S3 acceptance panels.
FR + ES ingestion for Madrid and Lyon is fully authorized to proceed.

Owner name / initials: AUTHOR / O.I.  Date: 2026-08-27
```

*Evidence: `openubem/outputs/eu_evidence/EU-04/D-EU-22/layout_contract_ceiling.json`,
`openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv`,
`openubem/outputs/eu_evidence/EU-04/real_footprint_feasibility_summary.json`,
`docs/docs_ACTIVE/europeanLocations/ACCEPTANCE_S2_promotion_2026-08-27.md`,
`docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-22_s3_attribute_source_2026-08-27.md` §7.*
