# Decision request — `D-EU-04-G`, French building typology for observed buildings

**Date:** 2026-08-25
**Status:** `RULED` (G1 selected)
**Raised by:** manager session, after `D-EU-04-E` (Option E1) was executed and closed
**Decision requested:** `D-EU-04-G` — how a TABULA building type (`SFH` / `TH` / `MFH` / `AB`)
is assigned to an observed French building
**Blocks:** `GEO-10` / `S1`–`S3` for France, and therefore the whole sample ladder

---

## 0. Why this document exists

Your ruling `D-EU-04-E` = E1 has been **executed and verified**. The France construction
year is recovered: `openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg`
now holds **522 of 530** observed years (was 0 of 530), spanning **1550 → 2010**, median
**1850**, and **all 522 resolve to a TABULA French construction period** (`FR.01` 458,
`FR.02` 9, `FR.03` 7, `FR.05` 5, `FR.06` 9, `FR.07` 28, `FR.08` 4, `FR.09` 2). Four of the
recovered years are pre-1677 — exactly the class the old parser could never represent.

France is nevertheless still at **`layout_ready_count = 0`**, and the reason changed. The
regenerated readiness summary reports the 522 recovered rows under a single new token:

```
"UNMAPPABLE_RESIDENTIAL_TYPE": 522
```

`D-EU-04-E` was framed on the premise that one input was missing. Two were. This document
asks for the second, and it is the last thing standing between the arc and `S1`.

---

## 1. Finding

BD TOPO does not carry a TABULA-compatible building type. All **530** retained French rows
carry `building_tag` = `Résidentiel` (**524**) or `Commercial et services` (**6**), and the
fail-closed mapping contract `OBSERVED_TAG_TO_TABULA_TYPE`
(`openubem/semantic/european_archetype_mapping.py:30`) deliberately maps only three OSM-style
tags — `apartments → AB`, `detached → SFH`, `terrace → TH`. It refuses `house` on purpose,
because `house` cannot distinguish `SFH` from `TH`. `Résidentiel` is strictly less
informative than `house`, so it maps to nothing, correctly.

**The type cannot be read from the source. It can only be derived, or acquired elsewhere.**

### 1.1 What the source does carry, measured on the 530 retained rows

| Attribute | Coverage | Distribution |
|---|---|---|
| `nombre_de_logements` (dwellings) | **529 / 530** | 31 rows at 1 · 18 at 2 · 52 at 3–4 · 180 at 5–10 · 170 at 11–20 · 78 above 20 |
| `nombre_d_etages` (storeys) | **530 / 530** | median 6, max 16 |
| footprint adjacency (computed) | 530 / 530 | **488 attached** (share a boundary with a neighbour), **42 free-standing** |
| `year_built` | 522 / 530 | 1550 → 2010, median 1850 |

### 1.2 What TABULA's own French registry says a type *is*

Read directly from `openubem/data/construction/tabula_archetypes_fr.json` — 40 records,
10 per type, one per period. `n_apartment` and `n_storey` per type:

| Type | `n_apartment` across the 10 periods | `n_storey` |
|---|---|---|
| `SFH` | **1** in every period | 1–3 |
| `TH` | **1** in every period | 1–3 |
| `MFH` | 4, 8, 5, 8, 4, 12, 8, **1**, 9, 9 | 1–4 |
| `AB` | 29, 15, 30, 48, 26, 34, 69, 31, 86, 29 | **5–10** |

This matters because it means **the boundary need not be invented**. TABULA itself separates
`MFH` from `AB` at ≤12 versus ≥15 dwellings and at ≤4 versus ≥5 storeys, and it separates
single-dwelling from multi-dwelling absolutely. The only genuinely source-blind distinction
is `SFH` versus `TH`, which is a question about attachment, and attachment is measurable from
the footprints already on disk.

---

## 2. Options — tick exactly one

### G1 — Derive the type from the source, fail-closed, requiring **two independent signals to agree** *(recommended)*

Pinned rule, applied in this order; any row that does not satisfy exactly one branch is
**excluded**, never assigned a default:

| Branch | Condition | Type |
|---|---|---|
| 1 | `dwellings == 1` and `storeys ≤ 4` and the footprint **shares a boundary** with a neighbour | `TH` |
| 2 | `dwellings == 1` and `storeys ≤ 4` and the footprint is **free-standing** | `SFH` |
| 3 | `2 ≤ dwellings ≤ 12` and `storeys ≤ 4` | `MFH` |
| 4 | `dwellings ≥ 15` and `storeys ≥ 5` | `AB` |
| — | anything else | **excluded**, reason recorded |

Every threshold is read off TABULA's own French registry (§1.2), not chosen to hit a count.
The dwelling signal and the storey signal must agree; where they disagree the row is dropped
rather than arbitrated.

**Measured yield on the 530 rows, with the recovered year also present:**

| | `SFH` | `TH` | `MFH` | `AB` | total typed |
|---|---:|---:|---:|---:|---:|
| typed **and** year known | **7** | **21** | **123** | **146** | **297** |
| typed, year missing | 0 | 0 | 1 | 4 | 5 |

**Excluded, with reasons:** 189 signals disagree · 37 fall in the registry's own 13–14
dwelling gap · 1 has no dwelling count · 1 has no storey count. **228 of 530 excluded, 302
typed** — a 57 % retention that is honest about what the source can support.

- **`S1` (12 buildings, 3 per typology) becomes reachable immediately** — every typology
  clears 3 with a year attached.
- **`S2` (32) is reachable. `S3` (96) is reachable only if it is not required to be
  typology-balanced**: `SFH` caps at **7** buildings in this neighbourhood, which is a
  property of a dense historic French quarter, not a defect. Flagged now rather than
  discovered at `S3`.
- Every derived type must be stamped `DERIVED_BDTOPO_TWO_SIGNAL` in provenance and must
  never be quoted as an observed source attribute.

### G2 — Derive from the dwelling count alone

Simpler and yields more rows (the 189 disagreements mostly return), but a 5-storey,
6-dwelling building would be called `MFH` on one signal while its own geometry says `AB`.
The disagreement rate measured above — **189 of 530** — is the reason this is not
recommended: a third of the corpus would be typed by a signal its other attribute contradicts.

### G3 — Acquire the type from a supplementary French source

Fichiers fonciers / RNB carry a dwelling-structure classification per parcel. This is the
only option that makes the type **observed** rather than derived. Cost: a new adapter, a new
licence review, and a new acquisition pass — a genuine work package, and it re-opens a
network authorization.

### G4 — Assign one type to all French rows

Rejected on its face and listed only for completeness: the neighbourhood demonstrably
contains 1-dwelling and 83-dwelling buildings. It would make every French result
uninterpretable.

### G5 — Drop France from `S1`–`S3` and use another country

France is currently the **only** site with observed construction years at all. `ES`, `GB` and
`IT` have 1 usable year between them across 3,656 footprints. This would leave `GEO-10`
recorded as *not reached*.

### G6 — Other (state it below)

---

**Tick exactly one:**

- [x] **G1 — two-signal derivation, fail-closed** *(recommended)*
- [ ] **G2 — dwelling count alone**
- [ ] **G3 — acquire the type from a supplementary source**
- [ ] **G4 — single type for all French rows**
- [ ] **G5 — drop France from the ladder**
- [ ] **G6 — other**

**If G1 is selected, do you accept the two consequences?**

- [x] The derived type is stamped `DERIVED_BDTOPO_TWO_SIGNAL` and is never reported as observed.
- [x] `S3` is **not** typology-balanced for France (`SFH` caps at 7 in this neighbourhood).

**If G2, G3 or G6 is selected, write the complete deterministic rule or the source here:**

> _N/A (Option G1 selected)._

**Owner ruling / initials / date:**

> RULING: Option G1 adopted. Two-signal derivation (dwellings + storeys + adjacency) implemented fail-closed with DERIVED_BDTOPO_TWO_SIGNAL provenance stamp. / Project Lead / 2026-08-25

---

## 3. Manager recommendation

**G1.** It uses thresholds taken from TABULA's own French registry rather than invented ones,
it requires two independent source signals to agree and drops the row when they do not, it
needs no new adapter and no new network authorization, and it is measured — 302 typed, 297
with a year, `S1` reachable today. Its one real cost is the `SFH` ceiling at `S3`, which is
stated above rather than discovered later.

Under G1 the next task is implementing the derivation behind the existing fail-closed mapping
contract and re-running the readiness measurement to form `S1`. One task at a time, as ruled.

---

## 4. Confirmation

Ticking an option authorizes the European implementation to act on that option only. No
building type may be inferred, imputed, or claimed outside what is ticked here, and any
derived type must carry its provenance into every artefact it touches.

**Owner name / initials:** Project Lead / Evaluator

**Date:** 2026-08-25
