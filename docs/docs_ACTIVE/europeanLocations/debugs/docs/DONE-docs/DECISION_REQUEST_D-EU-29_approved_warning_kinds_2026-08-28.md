# Decision request `D-EU-29` — the `approved_warning_kinds` list for the 149-cell campaign perimeter

**Date:** 2026-08-28
**Status:** `RULED` (Option A selected)
**Raised by:** manager session, after `EU-09` scored `G8.15` **FAIL 149/149** over the `D-EU-28` perimeter
**Nothing here asks for compute.** Every number below was measured by this session from
`openubem/outputs/eu_certified_rerun_2026-08-28/`, the run already on disk. No simulation, no re-run.

---

## 0. Why this document exists

`EU-09` scored `G8.15` against an **empty approval set**, because the only ruled list —
`openubem/data/campaign/eu_approved_warning_kinds_v1.0.json` (`D-EU-13` closure question Q3, 2026-08-26) —
was ruled for the **`S2` building bundle**, not for the 510-cell archetype campaign. The gate is therefore
FAIL by construction, not by discovery: every one of the 149 perimeter cells carries at least one warning
kind that nobody has yet said anything about.

`G8.15` approves **kinds, never counts**. That rule is not reopened here. What is asked is which of the
eight observed kinds may enter the list, with a stated reading, for this campaign.

⚪ **This ruling cannot move a number.** It re-scores `G8.15` only. The perimeter stays 149, the
five-`f` set stays 15 pairs, `D-EU-26`'s `uk` bar and `D-EU-28`'s `es` bar are untouched, and every
`idf_sha256` stands.

---

## 1. What is actually there, measured over the 149

All three replicates were read. **No cell's warning-kind set differs across its three replicates** — the
warning surface is as reproducible as the heating value it accompanies.

| # | kind | cells | folds | verbatim first line |
|---|---|---:|---|---|
| 1 | `calculated design cooling load for zone` | **149/149** | uk, it | `Calculated design cooling load for zone=EU_CELL_ZONE is zero.` |
| 2 | `processscheduleinput` | **149/149** | uk, it | `ProcessScheduleInput: Schedule:Constant="EU_ALWAYSON", Blank Schedule Type Limits Name input -- will not be validated.` |
| 3 | `managesizing` | **149/149** | uk, it | `ManageSizing: For a plant sizing run, there must be at least 1 Sizing:Plant object input. SimulationControl Plant Sizing option ignored.` |
| 4 | `getvertices` | **149/149** | uk, it | `GetVertices: Floor is upside down! Tilt angle=[0.0], should be near 180, Surface="EU_…_FLOOR_1_SURFACE", in Zone="EU_CELL_ZONE"` |
| 5 | `getsurfacedata` | **149/149** | uk, it | `GetSurfaceData: Entered Zone Floor Area(s) differ more than 5% from the sum of the Space Floor Area(s).` |
| 6 | `calculatezonevolume` | **149/149** | uk, it | `CalculateZoneVolume: 1 zone is not fully enclosed. For more details use: Output:Diagnostics,DisplayExtrawarnings;` |
| 7 | `fixviewfactors` | **35/149** | **it only** (9 archetypes) | `FixViewFactors: View factors not complete. Check for bad surface descriptions or unenclosed zone="EU_CELL_ZONE".` |
| 8 | `entered zone volumes differ from calculated zone volume(s).` | **13/149** | **it only** (3 archetypes) | `Entered Zone Volumes differ from calculated zone volume(s).` |

🔴 **Both non-universal kinds fall entirely on `it`** — and `it` is, under `D-EU-26` + `D-EU-28`, the
**only fold quotable at fold level**. Whatever is ruled here lands on the one fold whose number gets
published, not on a fold already withheld.

⚪ **Measured, and it matters:** `Indicated Zone Volume < 0` — the kind `D-EU-13` Q3 **refused** and
repaired (FINDING EU-S2-07, ventilation loss understated 57.74×) — is **absent from all 149**
(0 files). The `S2` defect is not present here.

---

## 2. What carries over from the ruled `S2` list, and what does not

`eu_approved_warning_kinds_v1.0.json` approved four kinds and refused two.

- **Three of the four approved kinds recur here** — #1, #2, #3. Their `S2` readings apply verbatim; the
  models are the same generator's output with the same constant schedule and no plant loop.
- **The fourth (`gethtsurfacedata`, default 18 °C ground temperature) does not occur** in these cells.
- 🔴 **One of the two REFUSED kinds recurs: `getvertices`, on 149 of 149.** In `S2` it was the *cause* of
  the negative-volume defect and was repaired, not approved. **Here it is present by design** — the S0
  equivalent-envelope box emits independently sized, non-overlapping faces rather than a closed prism
  (`openubem/idf/european_box.py:46-57`, the `EquivalentEnvelope` contract), and flipping the S0 floor normals
  **was tried and reverted**: it cleared the warning and turned a
  three-of-three identical cell into one fatal in three. **This ruling may not inherit the `S2` refusal
  silently in either direction.** Approving it here is a statement that the S0 envelope is a different
  object from the S2 building, and it must be made explicitly or not at all.

---

## 3. Reading offered for each kind

1. **design cooling load zero** — cooling is not a requested end use; a zero sizing-only cooling figure
   cannot reach the reported heating number. *(`S2` reading, unchanged.)*
2. **processscheduleinput** — `EU_ALWAYSON` is a literal constant written by the generator, so the
   missing type-limits validation cannot admit an out-of-range value. *(`S2` reading, unchanged.)*
3. **managesizing** — there is no plant loop in these models, so nothing is left unsized. *(`S2` reading.)*
4. **getvertices** — deliberate S0 geometry, see §2. The heating result is produced by the
   `Zone Ideal Loads` variable against surface areas and the equivalent `H`, none of which depends on the
   floor normal's sign; the alternative was tested and destabilised the cell. **Approvable only as a
   stated design assumption, never as "benign".**
5. **getsurfacedata (>5 % floor-area difference)** — a Space/Zone bookkeeping mismatch inherent to the
   single-zone equivalent envelope; area used for EUI comes from the archetype record, not from the
   Space sum. Listed in the arc as one of the three by-design geometry warnings.
6. **calculatezonevolume (zone not fully enclosed)** — the equivalent envelope is deliberately not a
   closed solid. This is the **method**, and it is the same open question as `FINDING 181`.
7. **fixviewfactors (it, 35)** — the consequence of #6 for **longwave radiant exchange**: EnergyPlus
   cannot complete the view-factor matrix and applies its own correction. This is the least benign of the
   eight, and it sits on the quotable fold.
8. **entered zone volumes differ (it, 13)** — the entered volume (the generator's) is used, and it differs
   from what EnergyPlus recomputes for an unenclosed zone. It is #6 seen from the volume side. **It is
   NOT the refused `Indicated Zone Volume < 0` kind**, which is absent.

---

## 4. Options — tick exactly one

- [x] **A — Approve all eight, with #4, #6, #7 and #8 recorded as stated ASSUMPTIONS, not as "benign".** *(adopted)*
  `G8.15` re-scores **PASS 149/149**, earned against a read list. Every approval carries its reading into
  `eu_approved_warning_kinds_v1.0.json` (bumped, `n_approved` 4 → 8 with a `perimeter` field separating
  the `S2` bundle from the campaign), and §9.7.3 gains one caveat: **the equivalent-envelope cells are not
  enclosed zones, so their longwave radiant exchange is EnergyPlus-corrected, not modelled** — which must
  be stated wherever the `it` 108.25 kWh/m² figure appears.

- [ ] **B — Approve the six universal kinds; refuse #7 and #8.**
  `G8.15` then reads **PASS 114 / FAIL 35** and `it`'s fold-level figure carries an unresolved gate. Honest,
  but it withholds the only fold left after the `uk` and `es` bars — i.e. it ends the campaign's
  publishable output entirely.

- [ ] **C — Approve #1, #2, #3 only (strict inheritance of the ruled `S2` list).**
  `G8.15` stays **FAIL 149/149**. Defensible as "the S0 envelope was never triaged", but it makes the
  ruling a no-op and leaves EU-09 permanently at 2 FAIL.

- [ ] **D — Other** (state it below).

> **Ruling:** Option A adopted. Approve all eight observed warning kinds for the 149-cell campaign perimeter, with #4 (floor tilt / getvertices), #6 (unenclosed zone / calculatezonevolume), #7 (view factors incomplete / fixviewfactors), and #8 (entered vs calculated volumes) recorded as explicit stated S0 equivalent-envelope design assumptions rather than benign notices. G8.15 is scored PASS 149/149. The caveat regarding EnergyPlus-corrected longwave radiant exchange in unenclosed zones is recorded in MVP §9.7.3.
>
> **Owner name / initials:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

---

## 5. What this does not decide

⚪ `G8.0`'s second failure — 22 `f>0` cells whose `f=0` control did not complete in three replicates, and
**29 whose `f=0` control lies outside the ruled perimeter** — is a separate disposition and is **not**
settled by this document. It is the arc's other open item.

⚪ 🔴 `FINDING 184` is untouched: the `f` manipulation is mean-conserving by construction
(`openubem/semantic/european_schedules.py:56`, asserted at `:60`), so **no ruling here makes an annual
figure quotable**. Peak and timing claims only.

---

## 6. Evidence

| claim | where |
|---|---|
| perimeter = 149 marker-free certified (`uk` 75, `it` 74, `es` 0) | `docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv`, re-derived this session |
| the eight kinds, their counts, folds and verbatim text | `openubem/outputs/eu_certified_rerun_2026-08-28/rep1/*/eplusout.err` (149 files read) |
| no cell's warning-kind set differs across its three replicates | same, `rep1`/`rep2`/`rep3` compared |
| `Indicated Zone Volume <` absent from all 149 | same corpus, 0 matches |
| the ruled `S2` list (4 approved, 2 refused) | `openubem/data/campaign/eu_approved_warning_kinds_v1.0.json` |
| `getvertices` is by design and the flip was reverted | `openubem/idf/european_box.py:46-57` (`EquivalentEnvelope` contract); MVP §9.7.3 |
| `G8.15` FAIL 149/149 as scored by GSSCanada 4J | MVP §9.7.3 EU-09/EU-10 addendum |
