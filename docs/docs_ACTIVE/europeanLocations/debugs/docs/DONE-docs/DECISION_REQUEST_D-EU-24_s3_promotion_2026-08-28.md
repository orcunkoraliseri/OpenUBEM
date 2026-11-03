# Decision request: D-EU-24 — the two owner actions that `S3` promotion is waiting on

**Status:** RULED (A1, B1 approved)
**Opened:** 2026-08-28
**Raised by:** director, at the close of the independent audit of `ACCEPTANCE_S3_promotion_2026-08-27.md`
**Blocks:** `S3` promotion, and nothing else. The campaign has already run; no compute waits on this.
**Does not block:** `§9.4` (closed, `v1.0` frozen), `S2` (accepted), `D-EU-22` / `D-EU-23` (ruled and
archived), the `EU-04` geometry contract (not reopened here), or the London One Login token (a separate
owed action).

---

## 0. Ruling

> **A?** **A1 — Approve the exclusion census as written.** 469 fail-closed exclusions stand exactly as measured (1,255 layout-ready of 1,724 scoped footprints). All S3 metrics are quoted over the 1,255 denominator.
> **B?** **B1 — Accept S3 at 95 of 96 EPLUS_COMPLETED.** The single fatal failure (`BATIMENT0000000240879534_part0`) is classified and reported with its diagnosis (internal EnergyPlus interzone collinear vertex mismatch); no geometry alteration is made to force completion.
> 
> **Owner name / initials:** Project Lead / Evaluator  
> **Date:** 2026-08-27

*Ruled 2026-08-28. Archived to `DONE-docs/` the same day; citation sweep performed — the ruling is recorded in the MVP EU-04 status row and finding (e), the director prompt head box, and the walkthrough progress log.*

---

## 1. Why this exists

`S3`'s promotion rule has two halves: **"approved exclusions and a measured resource envelope."**

The second half is a measurement, and it is done. The first half contains the word **approved**, and
approval is an owner act — a model may census exclusions but may not grant itself permission to have
made them. So the acceptance panel stands at ⚪ **HALF MET**, and this request is the other half.

🔴 **Nothing here re-opens a ruled decision.** `D-EU-23` G1 stands; Table 10's `96` stands; the
geometry contract stands. This request only disposes of what the run itself produced.

---

## 2. What is already measured, and is not in question

Recomputed independently by this session directly from `s3_campaign_manifest.csv`,
`s3_scope_measurement.csv` and `s3_sample.csv` — **every figure in the acceptance panel reproduces
exactly**:

| Fact | Measured |
|---|---|
| Sample | **96** buildings, `FR` 69 · `ES` 27 |
| Outcomes | **95 `EPLUS_COMPLETED`**, **1 `EPLUS_FATAL`** |
| Errors over the 95 | **0 severe**, **0 fatal** |
| IDF distinctness | **95 of 95** distinct `idf_sha256` — no building reused another's IDF |
| Weather | 2 fold hashes |
| Envelope | **471.10 s** total · mean **4.96 s** · min **1.35 s** · max **55.69 s** → **41.3× spread** |
| Heating `f = 0` | pooled **66.8677 kWh/m²** over 113,768.5830 m² |
| Both axes (never collapsed) | **12** dwelling-partitioned / **84** massing, agreeing row-for-row |
| `D-EU-04-H` | **VERIFIED, not assumed** — lowest-`building_id`-first in all 12 non-empty cells, **zero violations**, every sampled row `layout_ready` |
| Provenance | census SHA-256 in `s3_sample_summary.json` (`bc323beb…`) matches the census file on disk |

⚪ Two comparisons the numbers invite and **neither is available**: the `FR` / `ES` gap (55.4141 vs
87.2000) is **not** a national difference — two weather files, two registries, two urban forms; and
**97.0993 against 66.3089 is not a layout-mode effect** — the 12 partitioned and the 83 massing boxes
are different buildings, and no experiment here isolates the mode.

---

## 3. Decision A — the 469 corpus exclusions

**1,724 scoped footprints → 1,255 layout-ready.** Every one of the 469 exclusions carries a named,
machine-written reason:

| Site | Reason | Rows |
|---|---|---:|
| `ES-MAD-BERRUGUETE` | `MISSING_OBSERVED_STOREY_COUNT` | 144 |
| | `UNMAPPABLE_RESIDENTIAL_TYPE` (OSM `house` / `residential`) | 77 |
| | `MISSING_OBSERVED_YEAR_BUILT` | 7 |
| | `MISSING_OBSERVED_YEAR_BUILT;UNMAPPABLE_RESIDENTIAL_TYPE` | 4 |
| | `MISSING_OBSERVED_DWELLING_COUNT` | 4 |
| | **`ES` subtotal** | **236** |
| `FR-LYO-HAUTCOEURPENTES` | `TYPOLOGY_SIGNALS_DISAGREE` | 186 |
| | `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` | 37 |
| | `MISSING_OBSERVED_YEAR_BUILT` (± signals disagree) | 8 |
| | `MISSING_OBSERVED_DWELLING_COUNT` / `MISSING_OBSERVED_STOREY_COUNT` | 2 |
| | **`FR` subtotal** | **233** |
| | **total excluded** | **469** |

**Every reason falls into one of two kinds, and both are fail-closed:**

- **A missing observation.** The source registry does not publish the signal for that building. The
  ladder refuses to invent it. (`MISSING_*`, 165 rows.)
- **A deliberate refusal to guess.** `OBSERVED_TAG_TO_TABULA_TYPE` refuses OSM `house` **on purpose**,
  because it cannot separate `SFH` from `TH` (77 rows); `TYPOLOGY_SIGNALS_DISAGREE` refuses a building
  whose two independent signals contradict each other rather than picking a winner (186 rows); the
  registry gap 13–14 is a documented hole between two TABULA bands (37 rows).

**Options**

- **A1 — Approve the census as written.** The exclusions stand exactly as measured; `S3`'s scope is
  1,255 of 1,724 and every result carries that denominator.
- **A2 — Approve, but with a named amendment.** Owner names one or more reasons to relax (e.g. admit
  OSM `house` as `SFH`), which requires re-running the scope measurement and re-forming the sample.
- **A3 — Refuse, and require a wider corpus first.** `S3` waits for a second attribute source per site.

⚪ **What approval means and does not mean.** Approving is a statement that *these are legitimate
grounds for exclusion* — it is **not** a claim that the corpus is complete or that the excluded
buildings resemble the included ones. **Any `S3` figure must continue to be quoted over 1,255, never
over 1,724.**

🔴 **A2 is not free.** Admitting a refused class means asserting a typology the source does not
publish, which is the one thing this ladder has consistently refused to do, and it invalidates the
frozen sample (`D-EU-04-H` forbids re-selecting after seeing outcomes, so the sample would have to be
re-formed from the new pool and re-run).

**Recommendation: A1.** The refusals are the ladder working, not failing.

---

## 4. Decision B — the single `EPLUS_FATAL`

`BATIMENT0000000240879534_part0` — Lyon, `AB`, 7 storeys, **massing-box mode**. **12 severe**
`Vertex size mismatch between base surface … and outside boundary surface`, one per interzone
ceiling/floor pair, then `GetSurfaceData: Errors discovered, program terminates`.

**Diagnosed, not guessed:**

- **Both paired objects are written with 12 vertices** — so the mismatch arises *inside* EnergyPlus,
  after its own collinear-vertex removal, not in what OpenUBEM emitted.
- The footprint carries **one exactly collinear vertex** (turn `0.0000°`, deviation `0.000000 m`) at
  the end of a **0.200 m** segment, and three more within 1.4 mm of collinear.
- The mirrored interzone pair differs in the **last decimal digit** of its coordinates
  (`…787910771` against `…7879107706`).
- A collinearity test landing on opposite sides of its threshold for the two mirrored surfaces
  produces exactly this symptom.
- The footprint itself is **valid, simple, 13-ring-vertex**, with no duplicate points and no segment
  under 0.2 m.

🔴 **No geometry was changed to make it run.** The obvious remedy — snapping mirrored interzone
surfaces to bit-identical coordinates, or stripping near-collinear vertices before extrusion — would
alter the corpus and change the **accepted `S2` IDF hashes**. This arc has already refused one
corpus-wide vertex remedy that rested on a limit which did not exist.

**Options**

- **B1 — Accept `S3` at 95 of 96, the failure classified and reported.** The 1 stays in every panel
  with its diagnosis; the remedy is not attempted now.
- **B2 — Direct the interzone-vertex remedy as a separate work item**, with its own evidence and its
  own re-validation of `S2`. `S3` promotion waits for it.
- **B3 — Remedy inline and re-run the one building.** Fastest to a clean 96 of 96.

🔴 **B3 is the dangerous one.** Changing extrusion to rescue one building silently changes every
building, invalidates the 95 distinct IDF hashes just measured, and touches `S2`'s accepted hashes —
a corpus-wide change made to fix a single observed failure, which is selecting the method on the
outcome. **It should be refused.**

⚪ B2 is legitimate but costly: it re-opens geometry, and 1 of 96 (**1.04 %**) is a failure rate the
panel can carry honestly as long as it is never silently dropped.

**Recommendation: B1**, with the remedy left on the register as an untaken option.

---

## 5. What the answer buys, either way

| | If A1 + B1 | If A2 or B2 |
|---|---|---|
| `S3` | **PROMOTED**, over 1,255, at 95 of 96 | not promoted; re-scope or re-open geometry first |
| Frozen sample | stays valid | invalidated (A2) / re-validated (B2) |
| `S2` | untouched | untouched (A2) / must be re-checked (B2) |
| Standing caveat | 12 partitioned / 84 massing, never collapsed | unchanged |

---

## 6. How to answer

Two words are enough. For example:

> **A1, B1** — approve the exclusion census as written; accept `S3` at 95 of 96 with the fatal
> classified and its remedy left untaken.

Anything else, name the option letter and the amendment.

---

## 7. What this request does not ask

- It does **not** ask to re-open `D-EU-23`, the geometry contract, or Table 10's `96`.
- It does **not** ask about London — the One Login token remains a separate owed **action**, not a
  decision, and `S3` does not wait on it.
- It does **not** ask to change any number already published; the pre-fix `18` correction is already
  swept and is not part of this ruling.

**Evidence:** `docs/docs_ACTIVE/europeanLocations/ACCEPTANCE_S3_promotion_2026-08-27.md`,
`openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv`,
`openubem/outputs/eu_evidence/EU-04/s3/s3_scope_measurement.csv`,
`openubem/outputs/eu_evidence/EU-04/s3/s3_sample_summary.json`.
