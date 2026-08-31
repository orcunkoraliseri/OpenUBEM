# Decision request `D-EU-25` — is a 12-of-96 partition rate "real-footprint layout complete"?

**Date:** 2026-08-28
**Status:** `RULED` (Option A selected)
**Raised by:** manager session, after `GEO-08` was re-based (`D-EU-04-F` F4) and `GEO-10` was scored
**Nothing here asks for compute.** Every number below is measured from artefacts already on disk.

---

## 0. Why this document exists

`EU-04`'s verification matrix is now **complete**: `GEO-01`–`GEO-07` and `GEO-09` were audited earlier,
`GEO-08` was re-based to an independent Python reference on your `F4` ruling (40 passed), and `GEO-10`
was scored on retained artefacts (14 passed). No `GEO-*` row is untested or deferred.

`EU-04`'s status is nevertheless still **In progress**, and I did **not** flip it. One thing is left,
and it is a judgement, not a measurement: **the layout contract partitions a small minority of real
footprints, and nobody has ruled whether that is acceptable as "real-footprint layout complete".**

---

## 1. The finding, measured

The dwelling-partition contract refuses a footprint that is non-convex, holds a courtyard, or is
narrower than 8 m — each refusal named, none silent. Across the four audited sites:

| Site | Footprints | Clears the geometric half |
|---|---:|---:|
| `ES-MAD-BERRUGUETE` | 1,194 | **63** (5.3 %) |
| `FR-LYO-HAUTCOEURPENTES` | 530 | **52** (9.8 %) |
| `GB-LDN-STDUNSTANS` | 1,242 | **49** (3.9 %) |
| `IT-BOL-GALVANI2` | 1,220 | **40** (3.3 %) |
| **all four** | **4,186** | **204** (4.9 %) |

🔴 **Clearing the geometric half is not emission.** The contract then runs the partition audit and the
2.5 m facade-contact test. Emission is measured on **two** sites (`layout_contract_ceiling.CORRECTION.json`, 2026-08-27):
Lyon **28 emitted** of 297 attribute-ready rows, and Madrid **51 emitted** of 958 — **79 of 1,255
attribute-ready rows, 6.3 %**, with `partition_audit_failed = 0` on both. London and Bologna emission
is **UNMEASURED**; their 49 and 40 are footprint-only predicates.

🔴 **Do not quote the earlier "Lyon 18 of 28, 64.3 % survival" figure.** It is **WITHDRAWN**: the same
297 rows re-measured emit 28 of 28, because the generator now rotates about the footprint centroid and
audits against a relative tolerance, both of which postdate the `S1` census. It was true when written
and false when quoted in `D-EU-23` — the arc’s third recorded blocker to outlive its own blockage.

**What actually ran.** On the promoted `S3`: **12 of 96** buildings partitioned, **84** ran
`one_zone_per_floor` massing. On `S2` v3: **5 of 31** partitioned. Both splits are in the retained
manifests and are asserted by `tests/test_eu_geo10_ladder_accounting.py`.

⚪ `D-EU-23` already **refused** raising the ceiling — options `G2`/`G3` were not granted, and the
geometry contract and Table 10's 96 were left untouched. This request does not reopen that. It asks
only what the *status* of `EU-04` should be, given the ceiling as it stands.

---

## 2. Why it is a judgement and not a measurement

Both readings are defensible on the same evidence:

- **The capability is proven.** The kernel partitions real observed footprints, emits reciprocal party
  walls on saved-IDF readback, and every refusal is named and accounted. Nothing is broken; the
  contract is *narrow on purpose* and fails closed rather than inventing geometry.
- **The coverage is small.** 6.3 % of attribute-ready footprints emit a dwelling layout where emission
  has actually been measured, and 12 of 96 `S3` buildings
  partition. A reader told "`EU-04` complete" could reasonably assume the European stock is modelled at
  dwelling resolution, which is **not** what the artefacts show.

No further measurement resolves that. It is a question about what the word *complete* is allowed to
promise in this MVP.

---

## 3. Options — tick exactly one

- [x] **A — Close `EU-04` as *Completed*, with the ceiling carried as a standing caveat.**
  The matrix is complete, the kernel works, and the ceiling is a property of real European footprints
  rather than a defect. `EU-04` moves to *Completed*; §9.7.3 keeps the 12/96 and 204/4,186 figures, and
  **no `S3` result may ever be quoted without its partitioned/massing split.** *(adopted)*

- [ ] **B — Keep `EU-04` *In progress* until the ceiling is raised.**
  Honest about coverage, but it leaves `EU-04` open indefinitely on work `D-EU-23` already refused, so
  it should only be chosen together with a decision to reopen the geometry contract.

- [ ] **C — Close `EU-04` as *Completed* and open a successor work package for coverage.**
  Separates "the adapter is built" from "the stock is modelled at dwelling resolution", which are two
  different claims. Costs one new work-package row in §9.7.

- [ ] **D — Other** (state it below).

> **Ruling:** Option A adopted. Close `EU-04` as *Completed*. The geometric partition ceiling (204/4,186 geometrically clearing, 79/1,255 emitted across FR+ES, 12/96 partitioned in S3) is carried as a permanent standing caveat in MVP §9.7.3. All S3 and ladder results must explicitly report the partitioned vs. massing-box split.
> 
> **Owner name / initials:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

---

## 4. What happens either way

⚪ Nothing downstream is blocked by this. The 510-cell campaign runs on **archetype** cells, not on
partitioned footprints, so `EU-06`/`EU-08` are unaffected. `run_campaign_cell` is written and tested
and the entry point is closed with GSSCanada 4J.

🔴 Whatever is ruled, one sentence stands and does not depend on the ruling: **never quote an `S3`
result without its 12 partitioned / 84 massing split**, and never quote `GEO-10` as "4 / 12 / 32 / 96"
— the third rung is **31**.

---

## 5. Evidence

| claim | where |
|---|---|
| 204 of 4,186 clear the geometric half, per site | `openubem/outputs/eu_evidence/EU-04/D-EU-22/layout_contract_ceiling.json`; `DONE-docs/DECISION_REQUEST_D-EU-23_s3_geometry_mode_2026-08-27.md` |
| Lyon 28 / 297 and Madrid 51 / 958 emitted, 79 of 1,255 (6.3 %), 0 `PARTITION_AUDIT_FAILED`; the earlier "18 of 28 / 64.3 %" WITHDRAWN | `openubem/outputs/eu_evidence/EU-04/D-EU-22/layout_contract_ceiling.CORRECTION.json` |
| only 12 of the 79 emitting buildings fall inside the ladder-selected 96 | same correction file, `consequence_for_the_ruling` |
| `S3` 12 partitioned / 84 massing; `S2` v3 5 / 26 | `openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv`; `s2_campaign_v3_manifest.csv` |
| the ladder accounting, and the 31-not-32 pin | `tests/test_eu_geo10_ladder_accounting.py` (14 passed) |
| `GEO-08` re-based and green | `tests/test_eu_geo08_independent_parity.py` (40 passed); MVP §4.8 |
| `D-EU-23` refused raising the ceiling | `DONE-docs/DECISION_REQUEST_D-EU-23_s3_geometry_mode_2026-08-27.md`, `G2`/`G3` |
