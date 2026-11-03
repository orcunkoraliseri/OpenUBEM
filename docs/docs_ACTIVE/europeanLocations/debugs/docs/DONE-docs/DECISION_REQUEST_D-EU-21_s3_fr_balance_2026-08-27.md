# Decision request: D-EU-21 — how `S3` is composed, given that its multi-country corpus does not exist

**Status:** RULED — CLOSED 2026-08-27 (Option E1; diagnosis executed, see §0 and §7)
**Opened:** 2026-08-27
**Ruled:** 2026-08-27 by Project Lead / Evaluator
**Raised by:** director, under ruling `D-EU-20` Option A, **step 2**
**Blocks:** `S3` sample formation. `S3` must not be sampled or frozen until this is ruled.
**Does not block:** anything else. `S2` is accepted (`docs/docs_ACTIVE/europeanLocations/ACCEPTANCE_S2_promotion_2026-08-27.md`).

---

## 0. Ruling — 2026-08-27

**Option E1 — diagnose the three empty sites before ruling `S3` composition.** Ruled by the Project
Lead / Evaluator on 2026-08-27. The owner's directive, verbatim in §6: run an observed-year
availability diagnosis across the raw and ingested sources of `ES-MAD-BERRUGUETE`,
`GB-LDN-STDUNSTANS` and `IT-BOL-GALVANI2`; establish whether the years exist upstream and were lost
at parse time (the France precedent) or are genuinely missing at source; **return the findings before
finalising the `S3` composition rule**, with a fallback to Option E3 if the years are truly
unrecoverable.

**The diagnosis was executed the same day. Its result is §7 below, and it does not land on either of
the two branches the ruling anticipated** — the years were not lost at parse time, and they are not
unrecoverable either. The E3 fallback therefore does **not** trigger, because its stated precondition
is not met. `S3` composition passes to a new request, `D-EU-22`.

*Evidence produced under this ruling:*
`openubem/outputs/eu_evidence/EU-04/es_gb_it_year_availability_diagnosis.json`.

---

## 1. What `D-EU-20` asked for, and what the measurement found instead

`D-EU-20` step 2 asked for a ruling on **the French typology balance rule** — `SFH` caps at 7 in the
Lyon study area, so a typology-balanced `S3` cannot be formed from France as specified.

**That constraint is real and it is confirmed below. It is also not the binding one.** Measuring the
corpus before writing this request turned up a larger fact that changes what `S3` can be at all:

🔴 **All 297 layout-ready buildings in the entire European corpus are French. Spain, Great Britain
and Italy contribute zero between them.**

| Site | Buildings | `MAPPED_LAYOUT_READY` | Excluded |
|---|---:|---:|---:|
| `FR-LYO-HAUTCOEURPENTES` | 530 | **297** | 233 |
| `ES-MAD-BERRUGUETE` | 1,194 | **0** | 1,194 |
| `GB-LDN-STDUNSTANS` | 1,242 | **0** | 1,241 + 1 blocked |
| `IT-BOL-GALVANI2` | 1,220 | **0** | 1,220 |
| **Total** | **4,186** | **297** | **3,889** |

MVP Table 10 defines `S3` as *"96 observed buildings — balanced multi-country residential pilot,
including FR physical cases"*. **There is no multi-country population to sample from today.** The
question is therefore not only how to balance France; it is whether `S3` can be what Table 10 says.

## 2. Why the other three sites are empty — measured, one cause

**3,655 of the 3,656 buildings** across `ES`, `GB` and `IT` are excluded on
**`MISSING_OBSERVED_YEAR_BUILT`** — every excluded row in all three sites, with no exceptions. The single
remaining building (`GB` `way/396595550`, `AB`) does carry a year and is blocked on something else
(`MISSING_OBSERVED_DWELLING_COUNT`), which is why the three sites yield zero rather than one:

| Site | `MISSING_OBSERVED_YEAR_BUILT` alone | `…;UNMAPPABLE_RESIDENTIAL_TYPE` | Other |
|---|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 1,113 | 81 | 0 |
| `GB-LDN-STDUNSTANS` | 199 | 1,042 | 1 (`MISSING_OBSERVED_DWELLING_COUNT`) |
| `IT-BOL-GALVANI2` | 0 | 1,220 | 0 |

**Effectively the whole of all three sites lacks an observed construction year.** Without a year there is no TABULA
construction period and therefore no archetype, whatever else is present.

🔴 **This is the exact shape of a defect this project has already found once and fixed.** France read
**0 of 530** observed years until `D-EU-04-E`; the year was **present in the source all along**
(1,115 of 1,663 raw features carried `date_d_apparition`) and was destroyed by a pandas parse defect
at `bdtopo_fetcher.py:94`. After the repair France reads **522 of 530**.

**Whether the same is true of Madrid, London and Bologna is NOT measured.** Nobody has run the
equivalent of `fr_bdtopo_year_availability_diagnosis.json` on the OSM/cadastral sources of those
three sites. Ruling a composition rule before that diagnosis risks freezing `S3` around a corpus
whose emptiness is a bug rather than a fact — and the project's own standing rule is **diagnose
before remediate**.

## 3. The French constraint, confirmed

Within the 297 French layout-ready rows, the typology split is fixed by the corpus, not by choice:

| Typology | Layout-ready | Emits a real dwelling layout |
|---|---:|---:|
| `SFH` | **7** | **0** |
| `TH` | 21 | 1 |
| `MFH` | 123 | 14 |
| `AB` | 146 | 3 |
| **Total** | **297** | **18** |

Two independent ceilings, therefore, not one:

1. **`SFH` caps at 7** — a balanced 96-building sample needs 24 per typology and cannot have them.
   This was accepted as a consequence when `D-EU-04-G` was ruled; the replacement rule was never set.
2. **Only 18 of 297 produce dwelling-level geometry** — the rest fall back to a massing box, exactly
   as 26 of 31 did in `S2`. A 96-building `S3` is formable, but it would be **overwhelmingly a
   massing-box run**, which is what `S2` already demonstrated. `S3`'s stated purpose — an annual
   controlled baseline — would then be measured mostly on boxes.

---

## 4. Options

**Option E1 — diagnose the three empty sites first, then rule composition.** *(recommended)*
Run a year-availability diagnosis on `ES`/`GB`/`IT` in the shape already used for France: how many
raw features carry a construction-year field at source, and how many survive ingest. **No ruling on
`S3` composition until that returns.** If the answer resembles France's, `S3` becomes a genuine
multi-country pilot and this whole request is re-scoped; if the years are truly absent at source,
Option E2 or E3 follows on measured ground.
*Cost:* one measurement pass, no simulation. *Risk:* delays `S3` by one slice.

**Option E2 — redefine `S3` as France-only, 96 buildings, typology-proportional.**
Sample the 297 in proportion (≈ 2 `SFH`, 7 `TH`, 40 `MFH`, 47 `AB`). Formable today.
*Cost:* Table 10's *"balanced multi-country"* wording is abandoned and must be amended in the MVP,
and `S3` stops being the multi-country pilot the ladder was designed around.

**Option E3 — redefine `S3` as France-only with a per-typology floor.**
Take **all 7** `SFH`, all 21 `TH`, and fill the remaining 68 from `MFH`/`AB`. Keeps every typology
present and honest about the ceiling.
*Cost:* the same wording amendment as E2; `SFH` is represented but cannot be statistically meaningful
at n = 7, and this must be stated wherever an `S3` result is quoted.

**Option E4 — park `S3`.**
Declare the ladder stopped at `S2` and hand the MVP on. *Cost:* no annual controlled baseline is ever
run by OpenUBEM, and `EU-04`/`EU-05` stay permanently *In progress*.

---

## 5. Recommendation

**Option E1.** The one thing that would change every other answer — whether three quarters of the
corpus is empty by fact or by defect — costs a measurement pass and has a **direct precedent of the
same defect in this same arc**. Ruling E2 or E3 first would freeze `S3` as a France-only study on the
strength of an unexamined zero.

**If E1 returns "the years are genuinely absent at source", the director will return E3** as the
follow-up recommendation, with the `n = 7` `SFH` caveat written into the sample manifest itself.

**In every option, one rule from `D-EU-04-H` stands:** the sample is selected by the ladder's own
rules and **never on the outcome being tested**. A sample chosen because its buildings happen to emit
dwelling layouts would measure the selection, not the corpus.

---

## 6. Owner response

```
D-EU-21 ruling: Option E1 (diagnose first before ruling S3 composition)
(E1 = diagnose first / E2 = FR-only proportional / E3 = FR-only with floor / E4 = park S3)

Notes: Option E1 approved. Execute an observed-year availability diagnosis across the raw and ingested sources of ES-MAD-BERRUGUETE, GB-LDN-STDUNSTANS, and IT-BOL-GALVANI2. Measure whether raw construction years exist in the upstream cadastral/OSM data and were lost during parser ingest (analogous to the France precedent) or are genuinely missing at source. Return the diagnosis findings before finalizing the S3 composition rule (with fallback to Option E3 if years are truly unrecoverable).

Owner name / initials: Project Lead / Evaluator  Date: 2026-08-27
```

*Evidence: `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.csv` and
`…_summary.json` (per-site counts and exclusion reasons), `…/s1_layout_reachability_census.csv`
(18 of 297), `…/fr_bdtopo_year_availability_diagnosis.json` (the France precedent), MVP Table 10
(`MVP_european_locations.md:725-733`), `docs/docs_ACTIVE/europeanLocations/ACCEPTANCE_S2_promotion_2026-08-27.md`.*

---

## 7. Diagnosis result — executed 2026-08-27 under this ruling

**No simulation and no live retrieval were run.** Every figure below is read from artefacts already
on disk. The OSM and Bologna adapters persist every unmapped source attribute in `surplus_tags`, so
"did the source carry a year that ingest discarded" is answerable without touching an endpoint.

**Finding 1 — Scenario A is refuted. There is no France-style parse defect.**
`osm_fetcher.py:190` `_parse_year` matches a leading four-digit run and additionally decodes `C19` /
`C20` century notation. It never routes through `pd.to_datetime`, so neither failure that destroyed
France's years — the bare zone suffix, and pre-1677 values overflowing `datetime64[ns]` — can occur.
Bologna never parses a year at all: `bologna_fetcher.py:99` and `:131` assign `year_built = NA`
unconditionally on **both** the `rifter` and the `CTC` path.

**Finding 2 — the ingested sources carry no construction year, on any row.**

| Site | Source ingested | Clean rows | `year_built` | Surplus keys | Construction-year key |
|---|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | OSM (Overpass) | 2,381 | **0** | 67 | none |
| `GB-LDN-STDUNSTANS` | OSM (Overpass) | 2,406 | **5** | 139 | `start_date`, on 5 rows |
| `IT-BOL-GALVANI2` | Bologna `rifter_edif_pl` | 1,631 | **0** | 8 | none |

The date-like keys that do appear are survey and record metadata, not construction: `check_date`,
`source:date:*`, one `inscription_date` (a listed-building plaque, 1950-12-29), and Bologna's
`data_istit` / `data_varia` — cadastral record dates whose modal value on 1,485 and 1,456 rows
respectively is the sentinel `1900-01-01`, the rest falling in 2003–2015.

**Finding 3 — Scenario B is not established either. The years exist; the source that holds them was
never ingested.**
`D-EU-10` (CLOSED, data half — `MVP_european_locations.md:1236`) already pinned a **primary attribute
dataset per city**: Madrid Catastro INSPIRE `BU` + CM CEE registry; London MHCLG EPC + OS Open UPRN;
Bologna Comune DBT + SACE + ISTAT. It went further and recorded the **period crosswalks** — clean 1:1
on exact year for `ES`/`FR`/`IT`, and 6 of 12 straddling EPC bands for `GB` with a ruled
majority-duration assignment. A crosswalk was ruled for data the project has never fetched.

What `EU-02` ingested is a **footprint** source per site. 🔴 **France is the one site whose ruled
attribute source and its ingested footprint source are the same file — IGN BD TOPO.** That is exactly
why France's failure was a parse defect and these three are not. Calling the ES/GB/IT years
"structurally absent" would be false, and would freeze `S3` on a false premise.

**Finding 4 — a second, independent blocker. Restoring the year would still not form `S3`.**
From `observed_archetype_mapping_readiness.csv`, rows that would clear **if the year were fully
restored**: `ES` **1,113** of 1,194, `GB` **199** of 1,242, `IT` **0** of 1,220.

- `GB`: 1,042 rows additionally carry `UNMAPPABLE_RESIDENTIAL_TYPE`; only 182 `AB` + 18 `TH` are typed.
- 🔴 `IT`: **all 1,220** carry it. The `rifter` layer's sole residential value is `Edificio generico`,
  which encodes no typology. **Italy contributes zero to `S3` regardless of what happens to the year.**
- France's 302 typed rows came from `type_provenance = DERIVED_BDTOPO_TWO_SIGNAL`, a two-signal
  derivation with **no analogue** in any of the other three ingested sources; only 228 came from
  `OBSERVED_TAG`.

**What this request therefore settles, and what it does not.**
Settled: there is no parser fix that recovers these years, and the emptiness is not a defect in the
ingest code. Not settled, and now the whole of the `S3` question: whether to ingest the `D-EU-10`
attribute sources (unmeasured coverage, needs an authorised live probe), and what `S3` is if only
`ES` and `FR` can ever contribute. **That is `D-EU-22`.**
