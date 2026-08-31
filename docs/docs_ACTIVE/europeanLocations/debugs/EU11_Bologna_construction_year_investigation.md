# EU-11 Bologna: building-level construction-year investigation

## Purpose

Resolve the `NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE` gate for
`IT-BOL-GALVANI2` without assigning, modelling, or statistically distributing
construction years.  This note is an investigation plan and evidence register;
it does not authorise a Bologna simulation rerun.

## Current finding

The EU-11 preparation attempted 1,220 residential cadastral-footprint
buildings in Galvani and prepared zero simulations.  The blocking condition is
not a simulation or EnergyPlus error: the current ruled sources contain no
observed construction year (or construction-period attribute) keyed to each
building.

| Evidence source | Geographic / object scale | Construction-year evidence | EU-11 result |
| --- | --- | --- | --- |
| Comune di Bologna `rifter_edif_pl` cadastral footprints | building (`codfab`) | none | Cannot select a building TABULA period |
| Comune di Bologna `c_a944ctc_edifici_pl` CTC volumetric bodies | component / geometry | none; height only where populated | May improve geometry, not age |
| ISTAT 2011 census indicators | census section | counts by construction-period band | Statistical aggregate only; cannot be attached to an individual building |
| SACE / regional EPC information | not published as a Bologna building-level open join in the prior probe | no verified eligible coverage | Not usable unless a new open, documented building-level release is found |

The machine-readable preparation record is
`openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/summary.json`.  Its exact
result is `population_attempted: 1220`, `population_prepared: 0`, and
`NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE: 1220`.

The prior live coverage probe is
`openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_gb_it_coverage.py`.  It
records the important distinction: ISTAT construction bands exist at census
section scale, but are **not observed building attributes**.  They must not be
used to probabilistically assign an age band to a footprint.

## Why this matters

The Italian TABULA archetype requires a construction period.  Choosing one
from neighbourhood averages, building form, surrounding buildings, or an
ISTAT-section histogram would be an imputation.  EU-11 is deliberately an
observed-data-only campaign, so such a choice would make Bologna incomparable
with the observed-year runs in Madrid, Lyon, and the eligible London subset.

## Acceptance test for a usable new source

A candidate source is admissible only if every accepted Bologna building can
be joined deterministically to an observed source record with all of the
following:

1. A stable building identifier, an exact geometry, or an auditable address
   join that identifies one physical building rather than an area.
2. An explicit construction year or a stated construction-period band for that
   same building.  A renovation date, EPC issue date, cadastral update date, or
   energy label is not a substitute.
3. Open licence and reproducible access, including source URL, retrieval date,
   source fields, and a saved raw slice/hash.
4. A one-to-one match, or a documented spatial overlap rule with no ambiguous
   many-to-one allocation.  Ambiguous records are excluded, not guessed.
5. Coverage and exclusion counts reported before any IDF is generated.

If the source supplies a period rather than a year, the period must map wholly
inside one Italian TABULA period.  A source band that straddles a TABULA
boundary is excluded unless the protocol is explicitly changed.

## Investigation work packages

### A. Re-check Comune di Bologna catalogues

Search the current municipal open-data catalogue and DBT metadata for a
building registry, historical building file, permit/completion register, or
addressable EPC-like layer.  Inspect the schema and a raw sample; a catalogue
title or portal search result is not evidence of field-level coverage.

Record for each candidate: dataset identifier, licence, endpoint, update date,
identifier/geometry field, age field, number of Galvani records, and number of
unambiguous joins to `rifter_edif_pl.codfab`.

### B. Check regional and national open releases

Investigate whether Emilia-Romagna, the national cadastre/geoportal, or an
official EPC/SACE release now exposes a downloadable, building-level
construction-year or age-band attribute with an open licence.  Do not use an
interactive-only portal, a non-open registry, or a dataset that forbids bulk
reproducible retrieval as campaign evidence.

### C. Distinguish permits from constructed buildings

If municipal permits are available, test whether they contain a final
completion date and a unique link to the existing building.  Permit issue dates
and renovation permits cannot be treated as original construction years.

### D. Test joins before changing EU-11 code

Create an evidence-only join table with: `codfab`, candidate record ID, match
method, overlap/address score, observed raw age value, normalized age value,
and exclusion reason.  Validate counts and uniqueness.  Only after this table
passes the acceptance test should a narrow, reviewed adapter and a new
`EU11R3_IT_BOL_GALVANI2` fleet be created.

## Explicitly disallowed shortcuts

- Assigning a period from an ISTAT census-section distribution.
- Inferring construction year from height, storey count, typology, geometry, or
  nearby buildings.
- Treating an EPC rating, certificate date, renovation year, or permit filing
  date as construction year.
- Filling missing values with an Italian national average or a random draw.

## Decision outcomes

- **Pass:** at least one open source satisfies the acceptance test for a
  documented subset.  Simulate only that subset and retain unmatched/ambiguous
  buildings as exclusions.
- **Partial pass:** simulate the verified subset; publish coverage and exclusion
  counts separately from the other EU-11 districts.
- **Fail:** retain Bologna at zero valid simulations, retain the current
  exclusion reason, and report the result as a data-availability limitation
  rather than a model failure.

## Status

Created 2026-08-28.  Corrected the same day: the Madrid, Lyon and London EU-11
Speed arrays were **not** running and have not been submitted — `squeue`/`sacct`
show no EU-11 job and no remote EU-11 fleet directory; all four districts are at
`PREPARED_FOR_SPEED`.  Closed 2026-08-28 as **Fail** (see the measured outcome
below).  No Bologna simulation, age assignment, or source claim has been made by
this investigation note.

## Measured outcome — 2026-08-28 — **FAIL**

Work packages A, B and C were executed as live measurements against the
public endpoints.  Probe scripts and raw results are in
`openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/year_probe/`
(`probe_a_c_bologna_municipal.{py,json}`, `probe_b_regional_national.{py,json}`,
`probe_b2_schema_closeout.{py,json}`).  Retrieved 2026-08-28T19:33–19:37Z.
Lot D was **not** reached: no candidate passed the acceptance test, so no join
table was built and no code was changed.

### A — Comune di Bologna catalogue (measured, not searched by title)

The full catalogue was swept by **field name**, not by dataset title — the gap
left by the D-EU-22 probe, which regex-matched titles only.

- **702 of 702** datasets enumerated at
  `https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets`.
- **137** datasets carry a field matching `anno|epoca|costruzion|datazion`.
  Every one is a fiscal, administrative or reporting year (budget year,
  reference year, procedure year) — **none is a building construction year**.
- The three building layers (`rifter_edif_pl`, `c_a944ctc_edifici_pl`, and the
  CTC volumetric bodies) confirm the table above: identifier and geometry yes,
  age no.  Criterion 2 fails.

### C — Permits

**10** permit-type datasets found (`SCIA`, `permessi di costruire`, edilizia
procedures).  All carry request, protocol or closure **procedure** dates and
none carries a completion date bound to an existing building.  Criterion 2
fails by construction; criterion 1 fails as well where no `codfab` or parcel
key is published.

### B — Regional and national releases

| Lead | Result | Class |
| --- | --- | --- |
| Emilia-Romagna CKAN, full sweep (2,904 packages) | no per-building year | data-absence |
| Geoportale ER, age attribute search | no per-building year | data-absence |
| Italian INSPIRE Buildings WFS | no working endpoint | **access-restriction** |
| SIAPE / ENEA APE | no open bulk building-level route; an APE issue date is not a construction year in any case | access-restriction |

Three ER datasets that matched only by title were then schema-checked, per
§A's rule that a title is not field-level evidence:

- `patrimonio-fabbricati` (Comune di Bologna, CC BY 4.0) — its only year field
  is **`Anno di riferimento al 31/12`**, the snapshot year of the municipal
  property register, **not a construction year**; and its perimeter is the
  buildings the Comune owns, not the district.  Criterion 2 fails.
- `edifici-storici-rue10` and `fabbricati-con-altezze-e-materiali-copertura10`
  (Comune di **Ferrara**) — geometry and parcel keys, **no year field**, and
  out of perimeter.

Four INSPIRE `GetCapabilities` attempts were made: `servizigeo.regione.
emilia-romagna.it` (DNS failure), `geoportale.regione.emilia-romagna.it`
(HTTP 404, SPA not a WFS), `wms.cartografia.agenziaentrate.gov.it`
(HTTP 500 SOAP fault), `inspire.agenziaentrate.gov.it` (DNS failure).
This path is therefore **unresolved, not proven absent** — the honest claim is
that no reproducible open route to it was reachable, which is itself a failure
of criterion 3.

### Disposition

**Fail**, per the decision outcomes above.  `IT-BOL-GALVANI2` retains
**zero valid simulations** and retains the exclusion reason
`NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE: 1220`.  This is a **public-open-data
availability limitation, not a model or EnergyPlus failure**, and must be
reported as such wherever the district appears.  Any future reopening requires
a new open release satisfying all five acceptance criteria; a reachable
INSPIRE Buildings endpoint is the only lead not closed by measurement.

The separate height question is untouched by this result: `c_a944ctc_edifici_pl`
does carry an observed eaves height (`altezza_gr`, CC BY 4.0), so the
`assumed 9.0 m` is an operational expedient, not a data absence.  It does not
license a construction year and must never be used to infer one.
