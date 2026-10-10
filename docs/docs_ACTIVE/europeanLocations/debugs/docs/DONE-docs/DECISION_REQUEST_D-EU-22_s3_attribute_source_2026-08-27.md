# Decision request: D-EU-22 — `S3` composition, now that the emptiness is an uningested source and not missing data

**Status:** RULED — CLOSED 2026-08-27 (Option F1; the probe was executed, see `§0` and `§7`)
**Opened:** 2026-08-27
**Ruled:** 2026-08-27 by Project Lead / Evaluator
**Raised by:** director, under ruling `D-EU-21` Option E1, on the diagnosis that ruling produced
**Blocks:** `S3` sample formation. `S3` must not be sampled or frozen until this is ruled.
**Does not block:** anything else. `S2` is accepted (`docs/docs_ACTIVE/europeanLocations/ACCEPTANCE_S2_promotion_2026-08-27.md`);
`EU-05` and `EU-06` are unaffected; `§9.4` stays closed and `v1.0` stays frozen.

---

## 0. Ruling

**Option F1 — authorise a coverage probe of the three `D-EU-10` attribute sources, then rule.**
Live retrieval of the named endpoints over the three study bounding boxes was **explicitly authorised
(`YES`)**. The ruling set the protocol — features returned per site, construction-year (or EPC
age-band) completeness, effective spatial join rate against the existing footprints — and the
downstream routing: **coverage confirmed → structure the attribute ingestion for a genuinely
multi-country (or binational FR + ES) `S3`; coverage thin or unjoinable → fall straight to `F3`.**

**The probe was executed the same day.** It is a measurement pass: live retrieval only, **no ingest,
no manifest rebuild, no simulation, nothing written into `openubem/data`.** Evidence:
`openubem/outputs/eu_evidence/EU-04/es_gb_it_attribute_coverage_probe.json`.

**It lands on the ruling's first branch, but for one site only.** Madrid covers, decisively. Bologna
has no per-building year in any open source and is out on typology regardless. London is neither
covered nor absent — it is **credential-blocked** behind an account only the owner can create. So
`S3` is **FR + ES**, which is the binational outcome this ruling itself named, and London stays
recoverable rather than refuted. Full numbers in `§7`.

---

## 1. Why this exists

`D-EU-21` ruled Option E1 and named two branches: **A**, the years exist upstream and were lost at
parse time — restore them and `S3` becomes a genuine multi-country pilot; **B**, the years are
genuinely absent at source — fall back to `E3`, a France-only `S3` with a per-typology floor.

The diagnosis ran the same day. **Neither branch holds**, so neither instruction can be executed
without inventing a premise. Full evidence in `§7` of
`docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-21_s3_fr_balance_2026-08-27.md` and in
`openubem/outputs/eu_evidence/EU-04/es_gb_it_year_availability_diagnosis.json`. In short:

- **Branch A is refuted.** `osm_fetcher.py:190` never routes through `pd.to_datetime`; neither France
  failure mode can occur. `bologna_fetcher.py:99` / `:131` set `year_built = NA` unconditionally.
  There is no parser fix that recovers a single year.
- **Branch B is not established.** `D-EU-10` (CLOSED, data half, `MVP:1236`) already pinned a primary
  **attribute** dataset per city — Madrid Catastro INSPIRE `BU`, London MHCLG EPC + OS Open UPRN,
  Bologna Comune DBT + SACE + ISTAT — and ruled the **period crosswalks** for them. Those sources
  carry the year. `EU-02` ingested a **footprint** source instead.

🔴 **France is the only site whose ruled attribute source and ingested footprint source are the same
file (IGN BD TOPO).** That single coincidence is why France has 522 observed years and the other
three have effectively none. The corpus is not lopsided because Europe lacks data; it is lopsided
because one site got its attribute source for free and three did not.

---

## 2. The second blocker, which changes the shape of any answer

Even a perfect year restoration does not make `S3` multi-country. From
`observed_archetype_mapping_readiness.csv`, rows that would clear **if the year were fully restored**:

| Site | Residential | Would clear on year alone | Also blocked on typology |
|---|---|---|---|
| `ES-MAD-BERRUGUETE` | 1,194 | **1,113** | 81 |
| `GB-LDN-STDUNSTANS` | 1,242 | **199** | 1,042 |
| `IT-BOL-GALVANI2` | 1,220 | **0** | **1,220** |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 297 layout-ready today | — |

🔴 **Italy contributes zero under every option on this page.** The `rifter` layer's sole residential
value is `Edificio generico`, which encodes no typology at all. Britain contributes at most 199.
France's 302 typed rows came from `DERIVED_BDTOPO_TWO_SIGNAL`, a two-signal derivation with no
analogue in any other ingested source — so "derive the typology like France did" is not available
either.

**The realistic ceiling on a multi-country `S3` is therefore FR + ES, with GB a minority and IT
absent** — and even that is conditional on data nobody has fetched yet.

---

## 3. What is still unmeasured

Whether Catastro `BU`, MHCLG EPC / OS Open UPRN and Comune DBT / SACE actually **cover these three
bounding boxes at these row counts**. `D-EU-10` pinned them on open-data completeness at city scale;
no one has probed the study bboxes. Until that is measured, any claim that `S3` can be multi-country
is a hope, and any claim that it cannot is the mirror-image of the same guess.

**A live retrieval for this arc requires the owner's authorisation.** That is why this is a decision
and not a task.

---

## 4. Options

**Option F1 — authorise a coverage probe of the three `D-EU-10` attribute sources, then rule.** *(recommended)*
Measurement only: for each of the three bboxes, how many features the ruled attribute source returns,
how many carry a construction year (or an EPC band), and what fraction join to the existing
footprints. **No ingest, no adapter, no manifest rebuild, no `S3` sample.** Returns a table that makes
F3 / F4 a measured choice instead of a guess.
*Cost:* one authorised live probe per site, one measurement pass. *Risk:* delays `S3` by one slice —
the same delay `E1` already accepted, for the same reason.

**Option F2 — ingest the attribute sources now.**
Build the join adapters, rebuild the manifests, re-form the corpus. *Cost:* `EU-02` is recorded
**Completed** in `MVP §9.7`; this reopens it, and commits to three new adapters before knowing
whether the sources cover the bboxes. Not recommended as a first step for that reason.

**Option F3 — `S3` = France-only, per-typology floor** (the former `E3`).
All 7 `SFH`, all 21 `TH`, 68 from `MFH`/`AB`. Formable today. *Cost:* Table 10's *"balanced
multi-country"* wording must be amended in the MVP, and the amendment must say **why** — that the
other three sites are empty for want of an uningested source, not for want of data. `n = 7` `SFH`
must be restated wherever an `S3` result is quoted.

**Option F4 — `S3` = FR + ES two-country, conditional on the ES probe only.**
Probe Catastro alone (its crosswalk is the clean 1:1 case, and `ES` has the largest recoverable pool
at 1,113). If it covers, `S3` is a two-country pilot; if not, fall to F3. *Cost:* narrower than F1,
and it silently concedes `GB` and `IT` without measuring them.

---

## 5. Recommendation

**Option F1.** The arc has now twice frozen a conclusion on an unexamined zero and twice had to
withdraw it — France's 0-of-530 years, and this request's own predecessor. One probe converts the
last unmeasured premise into a number. If it returns thin, **F3 follows immediately** and the
director will bring it back with the `n = 7` caveat written into the sample manifest itself.

**`D-EU-04-H` still stands under every option:** the sample is selected by the ladder's own rules and
**never on the outcome being tested.**

---

## 6. Owner response

```
D-EU-22 ruling: Option F1 (authorise a coverage probe of the three D-EU-10 attribute sources, then rule)
(F1 = probe the ruled attribute sources / F2 = ingest them now /
 F3 = FR-only with typology floor / F4 = FR+ES conditional on the ES probe)

If F1 or F4: live retrieval authorised for the named endpoints?   YES

Notes: Option F1 approved with live retrieval authorization. Execute the coverage probe on the ruled attribute endpoints for the three study bounding boxes (Madrid Catastro INSPIRE BU, London MHCLG EPC + OS Open UPRN, Bologna Comune DBT/SACE). Report returned feature counts, construction year availability, and spatial join rates against existing footprints. If coverage is demonstrated, formulate the multi-country S3 ingestion plan; if thin or unjoinable, fall back immediately to Option F3 (France-only with typology floor).

Owner name / initials: Project Lead / Evaluator  Date: 2026-08-27
```

*Evidence: `openubem/outputs/eu_evidence/EU-04/es_gb_it_year_availability_diagnosis.json`,
`openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.csv`,
`docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md:1236` (`D-EU-10`, attribute datasets and
period crosswalks), `openubem/acquisition/osm_fetcher.py:190`, `openubem/acquisition/bologna_fetcher.py:99`.*


---

## 7. Probe result — what the three sources actually hold (2026-08-27)

*Source of record:* `openubem/outputs/eu_evidence/EU-04/es_gb_it_attribute_coverage_probe.json`.
Live retrieval, authorised. No ingest, no simulation.

| site | ruled attribute source | features in bbox | year completeness | join to EU-02 footprints | verdict |
|---|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | Catastro INSPIRE `BU` | **2,121** | **2,116 / 2,121 = 99.76 %**, 1876–2025 | **1,179 / 1,194 = 98.74 %** by representative point, **1,192 = 99.83 %** by intersection | **COVERAGE_CONFIRMED** |
| `GB-LDN-STDUNSTANS` | MHCLG EPC + OS Open UPRN | 16,151 UPRNs | **withheld behind a login** | **1,219 / 1,242 = 98.15 %** carry ≥ 1 UPRN (99.11 % at 1 m) | **CREDENTIAL_BLOCKED** |
| `IT-BOL-GALVANI2` | Comune DBT + SACE + ISTAT | — | **no construction-year field exists** | — | **NO_PER_BUILDING_YEAR** |

**Finding 1 — Madrid covers, and it covers on both signals, not just the year.** All 2,121 Catastro
buildings in the study bbox carry `numberOfDwellings`, 1,940 of them greater than zero, and 1,915 are
`currentUse = 1_residential` — every one of those 1,915 with a year. Of the 1,179 footprints matched
by representative point, **1,179 carry a year *and* a dwelling count**: the same two-signal pattern
that produced France's 302 typed rows under `DERIVED_BDTOPO_TWO_SIGNAL`. All six TABULA-ES period
bands are populated (12 / 276 / 252 / 203 / 355 / 81).

**Finding 2 — the `n = 7` single-family ceiling is a France artefact, not a corpus limit.** Madrid
alone holds **220 single-dwelling candidates** (plus 174 at 2–4 dwellings and 757 at ≥ 5). ⚠ This is
a **candidate count, not a verified SFH count** — in a dense barrio a one-dwelling cadastral building
may be an annex or a converted commercial parcel. Verifying it is ingestion work, not this probe, and
**no `S3` composition may quote 220 as an SFH count** until it is.

**Finding 3 — the Catastro WFS cannot answer a coverage question at all, and the probe had to route
around it.** `ovc.catastro.meh.es/INSPIRE/wfsBU.aspx` returns HTTP 400 to a client sending the **literal `curl/*`
`User-Agent`** — and to nothing else. Measured the same day on one URL: `curl/8.5.0` → **400**;
`python-requests/2.32.3` → **200**; a custom `OpenUBEM/1.0` → **200**; an **empty** `User-Agent` →
**200**. It is a curl blocklist, not a browser check, which is exactly why the parallel `requests`-based
probe of the same endpoint never saw it. Once reachable, `ListStoredQueries` shows **every stored query is keyed on a cadastral
reference** — `GetBuildingByParcel`, `GetFeatureById`, `GetBuildingPartByParcel`,
`GetOtherBuildingByParcel`, `GetAllConstructionByParcel`. ⚠ **Corrected 2026-08-27, same day, by a parallel measurement:** an **ad hoc** `TYPENAMES=bu:Building` + `BBOX=` `GetFeature` **does work** — it requires the `,urn:ogc:def:crs:EPSG::4326` suffix on the bbox and **lat,lon** axis order, and `TYPENAME` singular is rejected. What is true is narrower: **no *stored query* is bbox-keyed.** The earlier `HTTP 500` on that form came from the missing browser `User-Agent`, not from the form. The measurement here
was made from the INSPIRE **ATOM bulk download** (`A.ES.SDGC.BU.28900.zip`, 105,185,640 bytes;
611 MB `building.gml` stream-parsed, 124,341 municipality features scanned). Also: the host
`www.catastro.minhap.es` no longer connects; `www.catastro.hacienda.gob.es` is live. Both traps are
registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 7.

**Finding 4 — London is blocked by an account, not by an absence, and the distinction matters.** The
entire `epc.opendatacommunities.org` host is **retired**; every path 301-redirects to
`get-energy-performance-data.communities.gov.uk`, whose own guidance states *"You need to sign in or
create an account with GOV.UK One Login to receive a bearer token"*, and whose `/login/authorize`
hands off to `oidc.account.gov.uk`. **There is no open bulk route.** OS Open UPRN *is* open and
needs no key — it was downloaded and parsed in full (618,494,417 bytes, md5
`2f023512afc378cd7b9351b24ccf1a34`, 41,629,393 rows) — but it carries identity and coordinates only,
**never a year**. So London's year coverage is **UNMEASURED, not zero**, while **the join surface was
measured and is intact**: 16,151 UPRNs fall in the study bbox and **1,219 of 1,242 footprints
(98.15 %, 99.11 % at a 1 m tolerance) contain at least one**, 6,838 UPRNs landing inside a footprint;
independently, 1,176 of 1,242 footprints (94.69 %) already carry a postcode, the other key the EPC
search API takes. **Both halves of the join exist; only the credential is missing.** **Owner action,
not a decision:** a GOV.UK One Login bearer token is the one step that would make London measurable.

**Finding 5 — Bologna is refuted at the schema, not at the parse.** The Comune portal catalogue
returns **0 datasets** for *"anno costruzione"*, **0** for *"sace"*, **0** for *"dbt"*.
`rifter_edif_pl` (40,621 records) and `c_a944ctc_edifici_pl` (65,744 records) both carry only
`data_istit` / `data_varia` — record-management dates, not construction dates. The Regione
Emilia-Romagna DBT WFS returns HTTP 401 and the Comune GeoServer HTTP 503. The census layers the
portal does publish are **tract-level statistics**: an ISTAT epoch distribution is a statistical
prior, **not an observed per-building year**, and cannot satisfy `MISSING_OBSERVED_YEAR_BUILT`. And it
is moot — **1,220 of 1,220 Bologna rows also carry `UNMAPPABLE_RESIDENTIAL_TYPE`**, so Italy
contributes zero to `S3` under every option.

**Consequence.** The ruling's own routing applies: coverage is confirmed, so the next step is to
**structure the attribute ingestion for a binational FR + ES `S3`**. `F3` does **not** trigger — its
precondition ("thin or unjoinable") is not met for Spain. `D-EU-04-H` stands: the sample is selected
by the ladder's own rules and never on the outcome being tested.

---

## 8. Independent re-measurement, one correction, and a ceiling this request did not look at

*Added 2026-08-27, after the ruling closed. **Additive only** — no verdict in `§0`–`§7` is
edited or withdrawn. Evidence: `openubem/outputs/eu_evidence/EU-04/D-EU-22/`
(`es_catastro_coverage_probe.json`, `gb_it_coverage_probe.json`, `layout_contract_ceiling.json`,
and the three scripts that produced them).*

🟢 **8.1 The three verdicts were re-measured by a different route and they hold.** `§7`
reached Madrid through the INSPIRE **ATOM bulk download**; this pass reached it through the
**WFS**, and Bologna and London through their own endpoints again. Nothing disagrees:

| | `§7` (ATOM route) | this pass (WFS route) |
|---|---:|---:|
| features in the study bbox | 2,121 | **2084** |
| `currentUse = 1_residential` | 1,915 | **1883** |
| residential rows carrying a year | 1,915 | **1883** (100.0 %) |
| residential rows carrying `numberOfDwellings` | 2,121 of 2,121 all-use | **1883** |
| `numberOfFloorsAboveGround` on `Building` | 0 | **0** |
| manifest footprints recovering a year | 1,192 (intersects) | **1183 of 1194 = 99.1 %** |

⚪ The ~1.7 % difference in feature count is the two routes, not a disagreement: the ATOM file is
one municipality snapshot clipped to the bbox, the WFS is 48 live tiles clipped the same way. **Both
land on the same verdict and the same order of magnitude, which is what a second route is for.**

🔴 **8.2 One correction to `§7` Finding 3, and it is worth the ink because the claim was
registered as a trap.** Finding 3 says the Catastro WFS *"cannot answer a coverage question at all"*
and returns HTTP 400 *"to any client without a browser `User-Agent`"*. **The first half is wrong and
the second is a misattribution.** This pass ran **48 consecutive ad hoc `BBOX` `GetFeature` calls**
against `ovc.catastro.meh.es/INSPIRE/wfsBU.aspx` under the plain User-Agent
`OpenUBEM-D-EU-22-coverage-probe/1.0`, all HTTP 200, returning 3782 features — **twice**, with
identical per-tile counts. What is true is narrower and more useful:

* there is **no bbox STORED QUERY** (`ListStoredQueries` returns five, all keyed on a cadastral
  reference) — that part of Finding 3 stands;
* the **ad hoc** form works, and it is fussy in exactly two ways: `TYPENAMES` **plural** is required
  (`TYPENAME` singular is rejected), and the `BBOX` value must carry the CRS URN as a fifth field
  (`lat,lon,lat,lon,urn:ogc:def:crs:EPSG::4326`) with **lat,lon** axis order.

⚪ **Why this matters beyond pedantry:** a registered "the WFS is unusable" trap sends the next
person to a 611 MB municipality download for a question a tiled bbox query answers in ten minutes.
The corrected entry is in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 7 — which is
also where `§7` said both traps already were, and where **neither of them actually was** until this
amendment.

⚪ **8.3 What Bologna's one surviving source actually offers, in numbers rather than in a
dismissal.** `§7` is right that ISTAT is a statistical prior and cannot satisfy
`MISSING_OBSERVED_YEAR_BUILT`. It is worth recording what the prior *is*, so nobody re-opens the
question hoping: **102 of 104 census-section polygons** intersecting the study bbox join to
the 2011 indicator table, covering **1588 residential buildings**, with the epoch distribution
**E8 1129 / E9 197 / E10 161 / E11 62 / E12 10 / E13 7 / E14 16 / E15 2 / E16 4** and the storey distribution **E17 31 / E18 172 / E19 427 / E20 958** (band labels read from the archive's own
`tracciato`, not assumed). 🔴 **It is a distribution over a tract, so a per-building period
taken from it is ASSIGNED, not observed** — and Italy is out on typology regardless.

🔴 **8.4 The ceiling this request did not look at, and it binds harder than the one it did.**
`D-EU-22` asked whether the attribute sources cover. They do, for Spain. But a recovered year does
not make a building **buildable**: the ruled layout contract also demands a convex, courtyard-free
plate at least 8 m wide. Measured offline with the project's own imported predicates:

| Site | Footprints | Clears the geometric half |
|---|---:|---:|
| `ES-MAD-BERRUGUETE` | 1194 | **63** (5.3 %) |
| `FR-LYO-HAUTCOEURPENTES` | 530 | **52** (9.8 %) |
| `GB-LDN-STDUNSTANS` | 1242 | **49** (3.9 %) |
| `IT-BOL-GALVANI2` | 1220 | **40** (3.3 %) |

And clearing that half is still not emission: in Lyon, the only site where emission has ever been
measured, **18 of 28** geometric clearers actually emitted (**64.3 %**), the other
10 failing `PARTITION_AUDIT_FAILED`. 🔴 **So attributes would make 1,183 Madrid
footprints usable and geometry accepts 63** — the binding constraint on `S3` moved, and it moved
to a place this request never examined.

⚪ **This does not disturb `§7`.** Coverage is confirmed and `F3` still does not trigger; the
FR + ES routing stands. What it changes is **what an FR + ES `S3` can be made of**, which is a
composition rule and therefore the owner's. Raised as **`D-EU-23`**
(`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-23_s3_geometry_mode_2026-08-27.md`), and
**RULED the same day — Option G1**: `S3 = 96` in **mixed mode**, dwelling-partitioned wherever the
`EU-04` contract emits and `one_zone_per_floor` everywhere else, with the layout axis and the
simulation axis printed separately in every acceptance panel. 🔴 **The ES ingestion `§7`
routed to is AUTHORISED on that basis** — Lyon and Madrid — so nothing in `§7` waits on a
decision any longer. ⚪ The geometry contract was **not** reopened to get there.
