# `S3` acceptance declaration — **MET** (ruled `D-EU-24`: A1 + B1)

**Work package:** `EU-04` (dwelling/core layout adapter)
**Ladder stage:** `S3` — 96 observed buildings, MVP Table 10
**Promotion rule, verbatim:** *"Approved exclusions and measured resource envelope"*
**Authority:** ruling `D-EU-23`, **Option G1** (2026-08-27) — 96 buildings in **mixed mode**, the layout
axis and the simulation axis printed separately; `D-EU-22` Option F1 settled the composition as
**FR + ES** and authorised the retrieval that `D-EU-23` turned into an ingestion.
**Date:** 2026-08-27
**Verdict:** ✅ **MET — ruled `D-EU-24`, options A1 + B1, recorded 2026-08-28.**
**Verdict as first written on 2026-08-27, retained:** ⚪ *HALF MET. The resource envelope is measured. The exclusions are censused but not approved, and approving them is an owner action, not a measurement.*

> 🟢 **Stamp — the owed half was answered by the owner, not waived and not self-granted.**
> `debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-24_s3_promotion_2026-08-28.md` reads
> **RULED (A1, B1 approved)**. **A1** approves the 469-row exclusion census **exactly as measured**, so
> every `S3` figure in this document is quoted over the **1,255** layout-ready denominator. **B1**
> accepts `S3` at **95 of 96** `EPLUS_COMPLETED`, the single fatal **classified and reported** with its
> diagnosis, and **no geometry altered to force completion**.
> ⚪ **Nothing measured in this document changed.** The verdict changed because the approval arrived.

---

## 1. Authoritative bundle

| Artefact | Path |
|---|---|
| Attribute sidecar (ES) | `openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv` |
| Corpus census (FR + ES) | `openubem/outputs/eu_evidence/EU-04/s3/s3_scope_measurement.csv` |
| Frozen sample | `openubem/outputs/eu_evidence/EU-04/s3/s3_sample.csv` |
| Campaign | `openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv` + `s3_campaign/` |

Nothing under `openubem/outputs/eu02/` was written. The ingestion is a **sidecar** keyed on the
manifest's own `osm_id`, and the four EU-02 manifests are byte-identical before and after
(28 files, SHA-256 verified either side of the run).

---

## 2. What the ingestion recovered

`D-EU-22` measured Madrid's coverage; `D-EU-23` authorised ingesting it. Executed 2026-08-27 through
`scripts/ingest_es_catastro_attributes.py` (48 ad hoc WFS `BBOX` tiles, HTTP 200 throughout, **no
retries**, 500.5 s):

| Measure | Value |
|---|---:|
| Unique Catastro features in the study bbox | **2,084** |
| `currentUse = 1_residential` | **1,883** |
| EU-02 footprints with a credited residential partner | **1,183** of 1,194 |
| …carrying an observed construction year | **1,183** |
| …carrying an observed year **and** dwelling count | **1,178** |
| Footprints with no intersecting residential partner | 11 |
| Partners carrying no dwelling count | 5 |

This reproduces the `D-EU-22` probe on every figure it shares with it. **`layout_ready` for Spain moves
from 0 to 958**, and the FR + ES pool is **1,255**.

⚪ **Spain is typed by the ruled observed tag, not by a derivation, and the reason is measured.**
`OBSERVED_TAG_TO_TABULA_TYPE` already maps `apartments → AB` and `detached → SFH`; what Madrid lacked
was the year and the dwelling count, which is exactly what was ingested. 🔴 **The French `D-EU-04-G`
G1 thresholds must never be transplanted to Spain**: they were read off `tabula_archetypes_fr.json`,
and the Spanish registry cannot support them — all 24 `ES` records carry `n_storey = null`, and their
`n_apartment` ranges *overlap* (`MFH` 8–16 against `AB` 7–78), so Spain's own registry does not
separate `MFH` from `AB` at all. **Consequence: Madrid contributes `AB` (955) and `SFH` (3) and no
`MFH` or `TH`.** That is a property of the source, recorded rather than worked around.

⚪ **One fail-closed rule was tightened while doing this.** Layout readiness now also requires an
observed **storey** count. France could never reach that branch — its two-signal derivation only fires
when both counts are present — but Madrid's type comes from the tag, so storeys are an independent
signal that can be missing: **144** ES rows are now `MAPPED_LAYOUT_BLOCKED_MISSING_STOREY_COUNT`
instead of being handed to a generator that would have raised on `NaN`.

---

## 3. Half one — "measured resource envelope" ✅ **MET**

96 buildings, annual run period, one pinned EPW per country, both registry checksums verified before
the first IDF was written.

| Measure | Value |
|---|---:|
| Buildings in the frozen sample | **96** |
| EnergyPlus `EPLUS_COMPLETED` | **95** |
| EnergyPlus `EPLUS_FATAL` | **1** (named in §5) |
| Severe errors over the 95 | **0** |
| Fatal errors over the 95 | **0** |
| Distinct `idf_sha256` | **95 of 95** — no building reused another's IDF |
| Distinct `weather_sha256` | **2**, one per country, both resolving in the pinned registry |
| Total EnergyPlus wall-clock | **471.10 s** |
| Mean / min / max per building | **4.96 s** / **1.35 s** / **55.69 s** |

🔴 **The spread is 41.3×**, close to `S2`'s 37.6× and for the same reason: a mean alone under-plans
the tail by an order of magnitude. Any `N1` projection must carry the maximum, not the mean.

**Energy distribution over the 95 completed runs** (heating only, `f = 0` baseline):
**min 29.5663 · median 80.3233 · max 222.2945 kWh/m²**, pooled **66.8677 kWh/m²** over
**113,768.5830 m²** of modelled floor area.

| Split | n | median EUI | pooled EUI |
|---|---:|---:|---:|
| `FR` (Lyon 2023 EPW) | 68 | 72.7056 | **55.4141** |
| `ES` (Madrid 2010 EPW) | 27 | 96.3172 | **87.2000** |

⚠ The two countries ran against **different weather, different TABULA registries and different urban
form**. The gap is a description of two samples, not a measured national difference, and must never be
quoted as one.

---

## 4. Both axes, printed separately as `D-EU-23` G1 requires

| | layout mode | simulation mode |
|---|---:|---:|
| `DWELLING_LAYOUT_EMITTED` / `EUROPEAN_DWELLING_LAYOUT` | **12** | **12** |
| `FALLBACK_PENDING_LAYOUT` / `FALLBACK_ONE_ZONE_PER_FLOOR` | **84** | **84** |

🔴 **These two columns must never be collapsed.** A building that falls back is a dwelling-layout
refusal **and** a valid mixed-mode `S3` member — that is what G1 ruled and it is how `S2` ran (26 of
31 as massing boxes).

⚠ Among the 95 completed runs the 12 dwelling-partitioned buildings pool to **97.0993 kWh/m²** and the
83 massing boxes to **66.3089**. **This is not a mode effect.** They are different buildings, in
different countries, of different types; nothing here isolates the layout mode, and no such comparison
was designed.

**Sample composition** (selected by inputs only — `D-EU-04-H`):
`FR` 69 · `ES` 27; `AB` 48 · `MFH` 23 · `TH` 15 · `SFH` 10; `OLD_PRE_1945` 55 · `NEW_POST_1945` 41.
Every eligible `SFH` in both countries was taken (`ES` 2 + 1, `FR` 6 + 1) — the type is a corpus
ceiling, not a selection choice. 56 rows came from the base quota of 6 per
country × type × age cell and 40 from the ruled shortfall round-robin, because four of the sixteen
cells are empty or thin in this corpus (`ES|MFH` 0, `ES|TH` 0, `ES|SFH` 3, `FR|SFH` 7).

---

## 5. Half two — "approved exclusions" ⚪ **CENSUSED, NOT APPROVED**

The rule asks for *approved* exclusions. Below is the census; the approval is not the model's to give.

**5.1 Corpus exclusions, FR + ES, 1,724 footprints → 1,255 layout-ready**

| Site | Reason | Rows |
|---|---|---:|
| `ES-MAD-BERRUGUETE` | `MISSING_OBSERVED_STOREY_COUNT` | 144 |
| | `UNMAPPABLE_RESIDENTIAL_TYPE` (OSM `house` / `residential`) | 77 |
| | `MISSING_OBSERVED_YEAR_BUILT` | 7 |
| | `MISSING_OBSERVED_YEAR_BUILT;UNMAPPABLE_RESIDENTIAL_TYPE` | 4 |
| | `MISSING_OBSERVED_DWELLING_COUNT` | 4 |
| `FR-LYO-HAUTCOEURPENTES` | `TYPOLOGY_SIGNALS_DISAGREE` | 186 |
| | `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` | 37 |
| | `MISSING_OBSERVED_YEAR_BUILT` (± signals disagree) | 8 |
| | `MISSING_OBSERVED_DWELLING_COUNT` / `MISSING_OBSERVED_STOREY_COUNT` | 2 |

`OBSERVED_TAG_TO_TABULA_TYPE` refuses OSM `house` **on purpose** — it cannot separate `SFH` from `TH`
— so those 77 are a deliberate refusal, not a gap.

**5.2 The one run-time exclusion, diagnosed rather than dropped**

`BATIMENT0000000240879534_part0` (Lyon, `AB`, 7 storeys, massing-box mode) is the single
`EPLUS_FATAL`: **12 severe** `Vertex size mismatch between base surface … and outside boundary
surface`, one per interzone ceiling/floor pair, then `GetSurfaceData: Errors discovered, program
terminates`.

Measured, not inferred: **both paired objects are written with 12 vertices**, so the mismatch appears
inside EnergyPlus after its own collinear-vertex removal. The footprint carries **one exactly
collinear vertex** — turn `0.0000°`, perpendicular deviation `0.000000 m`, at the end of a **0.200 m**
segment — and three more within 1.4 mm of collinear, while the mirrored interzone pair differs in the
**last decimal digit** of its coordinates (`…787910771` against `…7879107706`). A collinearity test
that lands on opposite sides of the threshold for the two mirrored surfaces produces exactly this
symptom. The footprint itself is valid, simple, 13-ring-vertex, with no duplicate points and no
segment under 0.2 m.

🔴 **No geometry was changed to make this run.** The obvious remedy — snapping mirrored interzone
surfaces to bit-identical coordinates, or removing near-collinear vertices before extrusion — would
alter the corpus and the accepted `S2` IDF hashes, and this arc has already had to refuse one
corpus-wide vertex remedy that rested on a limit that did not exist. **The building is reported as one
classified failure of 96 and the remedy is put to the owner**, with the measurement attached.

---

## 6. What the owner was asked to do — **DISCHARGED** (`D-EU-24`, A1 + B1)

1. **Approve or amend the exclusion census in §5.1** — 469 corpus exclusions, every one carrying a
   named reason.
2. **Rule the disposition of §5.2**: accept `S3` at **95 of 96 with one classified failure**, or
   direct the interzone-vertex remedy as a separate work item with its own evidence.

~~Until both are answered `S3` is **not** promoted.~~ **Both were answered on 2026-08-28.** The half
that is measurable is measured; the half that required approval was **granted by the owner** in
`D-EU-24`, and was never self-granted.

- **Ask 1 → `A1`, approved as written.** The 469 fail-closed exclusions stand exactly as censused;
  none was re-classified, re-scoped or dropped to improve a figure.
- **Ask 2 → `B1`, accepted at 95 of 96.** The interzone-vertex remedy was **not** directed. The
  failure stays classified and `[OPEN]` in `OpenUBEM_debug_References.md` ch. 1, and corpus geometry
  remains untouched — which is what §5.2 asked for.

🔴 **`S3` is PROMOTED.** The only item still owed to a person on this arc is the **GOV.UK One
Login bearer token** that would make London measurable — an **action**, not a decision.

---

## 7. What this document does not claim

- It does **not** claim the dwelling path works at scale: **12 of 96** ran dwelling-partitioned, and
  corpus-wide only **79 of 1,255** attribute-ready buildings emit a layout at all.
- It does **not** claim a country comparison. Two weather files, two registries, two urban forms.
- It does **not** claim London or Bologna are refuted by anything here. London stays
  **credential-blocked** and Bologna stays out on typology; neither was touched.
- It does **not** re-open `D-EU-23`. The ruling stands. One number in its §2 evidence has been
  corrected — Lyon emits **28 of 297**, not 18 — and the correction is additive, in
  `openubem/outputs/eu_evidence/EU-04/D-EU-22/layout_contract_ceiling.CORRECTION.json`. It moves the
  ruling's own margin **in the direction the ruling chose**: a dwelling-partitioned-only `S3` of 96 is
  still not formable, because 79 < 96.
