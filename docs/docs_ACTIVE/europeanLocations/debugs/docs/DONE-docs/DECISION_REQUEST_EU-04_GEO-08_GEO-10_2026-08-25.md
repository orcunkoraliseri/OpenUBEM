# Decision request — EU-04 remaining blockers (`GEO-08`, `GEO-10`/S1–S3)

**Date:** 2026-08-25
**Status:** `RULED` (E1 + **F4**) — F2 was selected 2026-08-25 and **SUPERSEDED 2026-08-28**; see the outcome block in §2.5
**Raised by:** manager session, after `EU-04 / S0-SMOKE-02` closed S0's scope
**Decisions requested:** `D-EU-04-E` (observed year + dwelling count source), `D-EU-04-F` (Grasshopper golden set)

---

## 0. Why this document exists

`EU-04` has completed everything it can complete without an external input.
`GEO-01`–`GEO-07` and `GEO-09` pass, the real-footprint layout kernel and the
external-core contract are audited, the layout→IDF readback emits reciprocal
party walls, and the S0 ladder stage (4 synthetic fixtures, one per SFH/TH/MFH/AB)
now completes an EnergyPlus design-day run per typology with a no-severe assertion.

The two items still open — `GEO-08` and `GEO-10`/S1–S3 — are **not** blocked on
code. Each is blocked on one thing only this project's owner can supply or rule.
Answer in the response blocks (§1.4 and §2.4); ticking a box is a ruling.

---

## 1. `D-EU-04-E` — observed construction year and per-building dwelling count

### 1.1 Finding

The four audited residential manifests hold **4,186** clean footprints.
The fail-closed mapping contract (`openubem/semantic/european_archetype_mapping.py`)
accounts for every one of them and promotes **zero** to layout-ready:

| Site | Footprints | Type resolved | Year observed | Mapping outcome |
|---|---:|---:|---:|---|
| `ES-MAD-BERRUGUETE` | 1,194 | 1,113 (1,110 AB, 3 SFH) | 0 | all excluded, missing year |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 0 | 0 | all excluded, missing year + type |
| `GB-LDN-STDUNSTANS` | 1,242 | 200 (182 AB, 18 TH) | 1 | 1 mapped, 1,241 excluded |
| `IT-BOL-GALVANI2` | 1,220 | 0 | 0 | all excluded, missing year + type |

`layout_ready_count = 0`. The single mapped building is London `way/396595550`
(`apartments`, observed 1928 → `GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001`),
and it is held at `MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT`.

**So two distinct inputs are missing, not one:**

1. **Construction year** — absent on 4,185 of 4,186 footprints. Without it no
   TABULA construction period can be selected, so no archetype can be resolved.
2. **Dwelling count** — absent on the one building that does have a year. Without
   it the layout kernel cannot be called: it refuses to infer a dwelling count
   from a footprint, by design, because inferring one would silently invent the
   conditioned-area contract.

`GEO-10` requires 4 → 12 → 32 → 96 **observed** buildings. S1 alone needs 12
(three per typology). At present the corpus can supply **1**, and that one is
itself blocked. This is the binding constraint on the entire S1–S3 ladder.

### 1.2 Why the current corpus cannot answer it

All four manifests were acquired from OpenStreetMap. The OSM adapter does parse
`start_date` (`openubem/acquisition/osm_fetcher.py:266`) — that is exactly how the
one London year survived — but the tag is essentially unpopulated in these four
neighbourhoods, and OSM carries no dwelling-count tag at all. No amount of
re-parsing the existing files changes these numbers.

### 1.3 What each country's authoritative source can supply

| Country | Source | Year built | Dwelling count | Adapter status |
|---|---|---|---|---|
| **FR** | IGN **BD TOPO V3** `batiment` | `date_d_apparition` → `year_built` | **`nombre_de_logements`** | **already implemented** — `openubem/acquisition/bdtopo_fetcher.py:84,94,96` |
| **ES** | Catastro / INSPIRE buildings | `beginning` | `numberOfDwellings` | not implemented |
| **IT** | Bologna cadastre / CTC | not carried — adapter sets year to `NA` (`bologna_fetcher.py:99,131`) | not carried | implemented but year-blind |
| **GB** | EPC Open Data, VOA | age **band**, not a year | not published per building | not implemented |

France is the only site where **both** missing inputs already exist in an
implemented adapter. That is a fact about the data, not a preference.

### 1.4 Options — tick exactly one

- [x] **E1 — Re-acquire the France site through the existing BD TOPO adapter and run S1 there.**
  Both blocked inputs arrive from one authoritative source with a named licence
  (Licence Ouverte 2.0, IGN attribution). Cost: one acquisition pass over
  `FR-LYO-HAUTCOEURPENTES`, no new adapter. S1's 12 buildings become reachable
  from ~530 footprints. Caveat: `nombre_de_logements` may itself be null on some
  buildings — those rows stay excluded, they are not imputed. **Requires your
  authorization for a live IGN WFS fetch** (or a pre-downloaded slice via
  `slice_path`), because §5.3 still forbids live-network work by default.

- [ ] **E2 — Same as E1, plus a new Catastro adapter so Spain joins the ladder.**
  Adds ES (1,194 footprints, 1,113 already typed) and makes S2/S3's multi-country
  balance real rather than single-country. Cost: one new acquisition adapter and
  its audit — a genuine work package, not a pass.

- [ ] **E3 — Approve a provenance-bearing imputation rule.**
  Define it below (e.g. year from the neighbourhood's dominant TABULA period,
  dwellings from conditioned area ÷ national mean dwelling size). Every affected
  output must then be stamped `IMPUTED` and must never be quoted as an observed
  result. This unblocks all four sites at once and costs the least, but every
  downstream number inherits the assumption.

- [ ] **E4 — Restrict S1–S3 to buildings that already have a source, however few.**
  Honest, cheap, and currently yields fewer than 12 buildings, so `GEO-10` would
  be recorded as *not reached* rather than passed.

- [ ] **E5 — Other** (state it below).

**If E3 or E5 is selected, write the complete deterministic rule here:**

> _N/A (Option E1 selected)._

**Authorization for a live acquisition fetch (E1/E2 need this):**

- [x] Authorized — proceed with the live IGN WFS (and/or Catastro) fetch.
- [ ] Not authorized — supply the data as a local slice file instead; path:

> _Authorized: live fetch from official IGN BD TOPO WFS endpoint under Licence Ouverte 2.0._

**Owner ruling / initials / date:**

> RULING: Option E1 adopted with live IGN WFS fetch authorization. / Project Lead / 2026-08-25

---

## 2. `D-EU-04-F` — `GEO-08` Grasshopper golden set

### 2.1 Finding

`GEO-08` (MVP §4.8, Table 4) is defined as *cross-implementation parity*: the
Grasshopper definition and `openubem.geometry` must process the **same** input
footprints and export normalized GeoJSON/WKT in a pinned projected CRS, compared
on zone count, areas, exterior contact, circulation area and adjacency — ordering
ignored. MVP §4.8 also states Grasshopper is *a reference, not the acceptance
authority*, and that visual similarity is not a pass.

Nothing in this repository can produce the Grasshopper half. There is no golden
export, no pinned input footprint set, and no Rhino/Grasshopper runtime here.
`GEO-08` has therefore never been attempted — it is not failing, it is unstarted.

### 2.2 What would unblock it

A single deliverable: **the chosen input footprints plus the Grasshopper
definition's normalized export of them**, in a projected CRS, with the definition
version recorded. Everything after that is comparison code this session can specify
and a fresh executor can write.

### 2.3 What it costs to leave open

`GEO-08` is one row of a ten-row matrix and the only cross-implementation check.
Leaving it open does not block S1–S3 and does not invalidate `GEO-01`–`GEO-07`/
`GEO-09`, which are independent audits with their own assertions. It does mean the
arc cannot claim parity with the Ankara/Grasshopper method — and that claim, if it
appears in a paper, would be `UNSOURCED` under this arc's own §0 rule.

### 2.4 Options — tick exactly one

- [ ] **F1 — You supply the golden export.** Name the footprint set and attach or
  point at the normalized Grasshopper output; parity comparison is then implemented
  as a normal task and `GEO-08` closes properly.

- [ ] ~~**F2 — Defer `GEO-08` until after S1–S3.**~~ *(selected 2026-08-25; SUPERSEDED 2026-08-28 — see the outcome block at the end of this section)* It stays open and explicitly
  unclaimed; the ladder proceeds. Recommended if the golden export is not near to
  hand, because `GEO-08` does not gate anything downstream.

- [ ] **F3 — Waive `GEO-08` for the MVP.** OpenUBEM's own audits become the sole
  acceptance authority and the MVP records parity as *not tested*, never as passed.
  Requires an explicit amendment to MVP §4.8, since Table 4 currently lists it as a
  required gate.

- [x] **F4 — Substitute a different independent reference** *(RULED 2026-08-28 — this is the standing outcome)* (a second, independently
  written partitioner, or a CAD export) as the cross-implementation check. Honest
  independence, but it is no longer Grasshopper parity and §4.8 must say so.

- [ ] **F5 — Other** (state it below).

**If F1 is selected, name the footprint set, CRS, and definition version:**

> _N/A._

### 2.5 Outcome — RULED 2026-08-28, option F4 (substitute an independent reference)

🔴 **The 2026-08-25 F2 deferral is SUPERSEDED. `GEO-08` is RE-BASED, neither deferred nor waived.**
The owner ruled that OpenUBEM is a **Python-only** pipeline and that no Rhino/Grasshopper runtime
will be used in this arc, so the golden export F1 would require will never exist. Rather than drop
the only cross-implementation check, its reference is replaced: a **second, independently written
Python partitioner**, sharing no code with `openubem.geometry`, processes the same footprints and is
compared on zone count, areas, exterior contact and adjacency, ordering ignored.

Binding consequences, all recorded in `MVP_european_locations.md` §4.8 and §9.7.3:

1. 🔴 **This is no longer Grasshopper parity and must never be written as such.** Parity with the
   Ankara/Grasshopper method stays **NOT TESTED**; any such claim is `UNSOURCED` under the MVP's §0
   rule. What `GEO-08` now asserts is *independent-reimplementation agreement* — weaker, and different.
2. 🔴 **The independence is part of the gate.** A reference that imported the implementation under
   test would prove nothing, so the test asserts the reference imports nothing from `openubem.geometry`.
3. 🔴 **The neighbourhood `.html` viewer is NOT part of `GEO-08`.** §4.8's rule stands: *visual
   similarity alone is not a pass.* It is an inspection aid and may never be cited as evidence.
4. ⚪ `GEO-03`'s comparison column (*"Python vs. Grasshopper export"*) is void under the same ruling
   and was restated to the local supplied-partition audit on which `GEO-03` was actually accepted;
   its assertion and acceptance are unchanged, and the former text is retained inline.
5. ⚪ The re-basing does **not** close `EU-04`: real-footprint layout remains its open item.