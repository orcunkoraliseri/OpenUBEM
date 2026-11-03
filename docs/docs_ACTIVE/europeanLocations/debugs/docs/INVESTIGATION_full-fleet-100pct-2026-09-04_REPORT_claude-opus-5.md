# RESULTS REPORT — how far can the EU-11 full-fleet population be pushed toward 100 %?

- **Investigation brief:** `docs/docs_ACTIVE/europeanLocations/debugs/INVESTIGATION_full-fleet-100pct-2026-09-04.md`
- **Reported by:** **Claude Opus 5 (1M context)** — Claude Code director session, run locally on this repository.
- **Date:** 2026-09-04
- **Arc:** European locations, full-fleet expansion (`D-EU-101`)
- **Second, independent report:** `debugs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT_Antigravity.md`
  (Antigravity / Gemini 3.8 Flash). This report was written independently, then reconciled against it —
  §12 lists every point of agreement, every correction each report makes to the other, and the four
  places where the two disagree on a number.
- **Scope honoured:** read-only. No file under `openubem/` or `scripts/` was edited, nothing was committed,
  no Speed job was submitted, **no network call was made**. The only writes are this report and throw-away
  analysis scripts in the session scratchpad.
- **One deviation, declared:** for category 4 I re-executed `build_idf_for_building` for 13 named buildings
  **into the scratchpad only**, because the brief asked for a per-building diagnosis and the campaign records
  no failing ids. That reproduction is what turned category 4 from a hypothesis into a captured exception.

---

## 0. Method, and the proof that this report measures the real pipeline

Every count below was re-derived locally by replaying the campaign's own decision functions against the same
inputs, not by reading the summaries. The replay reproduces all four districts' `blocker_exclusions`
**exactly**, key by key:

| District | Attempted | Replay `mapped_ok` | Prepared | Exclusion dict reproduced |
|---|---|---|---|---|
| `FR-LYO-HAUTCOEURPENTES` | 530 | 473 | 469 | ✅ all 5 keys exact |
| `ES-MAD-BERRUGUETE` | 1,194 | 1,017 | 1,008 | ✅ all 6 keys exact |
| `GB-LDN-STDUNSTANS` | 1,242 | 389 | 389 | ✅ all 9 keys exact |
| `IT-BOL-GALVANI2` | 1,220 | not replayed (needs the two live Bologna endpoints) | 1,200 | read from `summary.json` |

`mapped_ok − prepared` is the IDF-assembly loss: Lyon 4, Madrid 9 — matching
`IDF_ASSEMBLY_FAILED_RuntimeError` in each `summary.json`. That identity is what let me name the failing
buildings, which nothing on disk records.

Fleet today: **3,066 / 4,186 prepared (73.2 %)**, gap **1,120**.

---

## 1. London `MISSING_OBSERVED_EPC_AGE_BAND` (445) + `PERIOD_STRADDLE_*` (355) — 800 buildings

Code verified: `scripts/run_eu_s2_district_campaign.py:63-68` (`GB_EPC_BANDS`), consumed at
`scripts/run_eu_s2_district_campaign.py:182-187`. Exact `osm_id` join, latest certificate per footprint,
straddle refused. All confirmed as described in the brief.

TABULA GB period boundaries, read off `tabula_period("GB", y)` directly:
`GB.01 ≤ 1918 · GB.02 1919–1944 · GB.03 1945–1964 · GB.04 1965–1980 · GB.05 1981–1990 ·
GB.06 1991–2003 · GB.07 2004–2009 · GB.08 ≥ 2010`.

### 1.1 The 445 decompose into three physically different things

| Sub-population | Count | What is actually true |
|---|---|---|
| No UPRN on the footprint at all | **23** | no join key exists (`1242 − 1219`) |
| UPRN present, **every** certificate lookup returned HTTP 404 | **395** | no EPC has ever been lodged there (`1219 − 824`) |
| UPRN present, certificate(s) retrieved, but **no `construction_age_band` key** | **27** | all full-**SAP** schema, not RdSAP (`824 − 797`) |

All three figures reconcile exactly with `gb_epc_coverage_probe.json`. **The 445 is not one population, and
27 of it is not a data absence at all.**

### 1.2 🔴 The largest verified defect in this investigation: an observed construction **year** is already on disk and is never read

The harvester searched only for `construction_age_band` — visible in the CSV's own `year_key_used` column,
whose only non-null values are three variants of that key. The full-SAP certificates it recorded as "no
band" carry, in the same cached payload:

```
/body/data/sap_building_parts[0]/construction_year = 2009
```

Measured over the whole certificate cache (`openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/certificate`,
5,385 JSON files):

- **1,336 certificates carry an explicit `construction_year`** and no band;
- 4,045 carry a band and no year; the two sets are **disjoint** (4,045 + 1,336 + 4 = 5,385);
- mapped onto footprints, **67 footprints** hold at least one certificate with an explicit year.

Of those 67, **27 are in the 445**, and all 27 resolve to a single TABULA period — a year is not an
interval, so no straddle is possible. This is not an inference or a fuzzy match: it is a declared
construction year in a payload the project already retrieved and already stores.

**Net effect if read: 27 footprints gain an age, 24 of them also pass the existing type and storey gates.
+24 prepared.** (Tags: 14 `house`, 12 `apartments`, 1 `terrace`; the 3 that still fail do so only on missing
storeys and are inside category 2.)

### 1.3 The 355 straddles — one combined tie-break, measured three ways

**(i) Explicit year, consistent with the band.** 15 straddling footprints hold a certificate with an
explicit year. **8** have a year inside the straddling band's own interval; those resolve. **6 of the 8 also
pass type + storeys → +6 prepared.** This is a code fix, not a policy change: it uses a declared year and
refuses it whenever it disagrees with the band.

**(ii) Period-set intersection across the footprint's own certificates.** 287 of the 1,242 London footprints
carry **more than one distinct age band**; the code keeps the latest and discards the rest. Treating each
band as a constraint (band → the TABULA periods its interval touches) and intersecting:

| Outcome over the 355 | Count |
|---|---|
| intersection collapses to **one** period → resolved | **80** |
| non-empty but still ≥ 2 periods | 206 |
| **empty** → certificates contradict each other, must stay excluded | 69 |

**69 of the 80 also pass type + storeys.**

**(iii) Both constraints together — the strongest defensible rule.** Intersecting band-period sets *and*
explicit-year periods across every certificate on a footprint:

| Outcome over the 355 | Count |
|---|---|
| **resolved to one period** | **86** |
| still ambiguous | 199 |
| contradictory | 70 |

**75 of the 86 also pass type + storeys → +75 prepared**, of which 6 come free with fix (i).

Worked example, `way/192335494` (107 certificates): its RdSAP bands are `J` (2003–2006 → `{GB.06, GB.07}`)
and `K` (2007–2011 → `{GB.07, GB.08}`); 40+ SAP certificates lodged 2009-10 carry
`construction_year = 2008` (→ `GB.07`). Band intersection and explicit year agree independently on
**`GB.07`**. That is two separate sources converging, not a tie broken by preference.

⚠️ **Caveat that must travel with the 80/86.** RdSAP records a band *per building part* (103 certificates use
`sap_room_in_roof`, 15 use `sap_building_parts[1]`). If every building-part band is honoured rather than the
one band per certificate the pipeline stores, the intersection resolves **70**, not 80. The larger number is
consistent with the pipeline's own stored field; the smaller is the conservative reading. **This is exactly
why (ii)/(iii) is a ruling and not a fix:** it asserts that all certificates on one footprint describe one
construction period — true for a purpose-built block, false for a converted terrace.

### 1.4 On a second, independent UK building-age source

I could not measure any external source: a live HTTP probe is barred both by the brief's read-only scope and
by `CLAUDE.md`'s hard rule (no live-network fetches until §5.3 is unblocked). What I can state on evidence:
**for 418 of the 445 the EPC route is closed** (no certificate exists, or no UPRN exists), so any recovery
there must come from outside EPC entirely.

The Antigravity report did survey the candidates and reached a negative result — **carried here as its
finding, not mine, and unverified from this session**: VOA council-tax build-period attributes are
protected under CRCA 2005 s.18 and reachable only inside the ONS Secure Research Service; the OS NGD building
age attribute sits under the PSGA/commercial licence, not OS OpenData; the GLA/UCL London Building Stock
Model publishes visualisations and aggregates, not property-level microdata. If that holds, the 418 are a
statutory-coverage ceiling rather than a data-plumbing gap. Anyone acting on it should re-verify the licence
positions before quoting them.

### Verdict — category 1

- **(b) real fix, +24:** read `sap_building_parts[*].construction_year` when `construction_age_band` is absent.
- **(b) real fix, +6:** resolve a straddle by an explicit year that is consistent with the band; refuse it when it contradicts.
- **(c) owner ruling, +75 total (+69 beyond the fix above):** resolve a straddle by intersecting every constraint the footprint's own certificates impose. Conservative per-building-part reading: +59.
- **(a) dead end here, 418:** no EPC exists. Reachable only via an external age source that is licence-blocked as far as the Antigravity survey went.

---

## 2. `MISSING_OBSERVED_STOREY_COUNT` — Madrid 163 + London 47 = 210

### 2.1 Madrid 163 — 🔴 a named, addressable source exists and was explicitly left unfetched

`FINDING 254`'s manifest check is confirmed and is worse than it reads: across all 163, `levels`,
`height_m` and `roof_height_m` are null on **every** row and `provenance_levels` is `OSM_MISSING` on every
row. But 162 of the 163 already carry an observed Catastro **year and dwelling count** — storeys are the only
missing signal.

Tracing the source rather than the manifest: `openubem/acquisition/catastro_inspire_fetcher.py:129-181`
parses `dateOfConstruction`, `currentUse`, `numberOfDwellings`, `numberOfBuildingUnits` and
`conditionOfConstruction` — and **not** `numberOfFloorsAboveGround`. The reason is already recorded in the
project's own probe (`es_catastro_coverage_probe.json`):

> `"residential_with_floors": 0`, `"residential_floors_nil_reason_histogram": {"other:unpopulated": 1883}` —
> *"numberOfFloorsAboveGround is served as xsi:nil with an explicit nilReason on the Building feature. That is
> a DECLARED non-population at this feature type, not missing data: **Catastro carries the storey count on
> BuildingPart, reachable only through the GetBuildingPartByParcel stored query**, which is per-parcel and was
> out of scope for a bbox coverage probe."*

The storey count is not absent from Spain's cadastre — it lives on a feature type nobody has queried. And the
join handle is already in hand: **all 163 excluded footprints carry a `catastro_local_id`** in
`es_catastro_attribute_sidecar.csv`, so every one is individually addressable by the per-parcel stored query.
No fuzzy matching, no interpolation.

**Ceiling: 163**, and actual recovery will be lower by an unknown amount — once storeys arrive each building
must still satisfy `derive_bdtopo_building_type`. This needs one authorised, bounded network campaign of 163
parcel queries and nothing else.

### 2.2 London 47 — one proxy fails, one works

**Rejected on evidence: EPC total floor area ÷ footprint area.** All 47 have at least one EPC floor area; the
ratio runs 0.75 – 6.54 (median 2.98). It is a *lower bound*, never a measurement, because EPC coverage is a
sold/let subset — `way/823489432` gives 0.75 (one flat inside a house) and `way/298850488` sums 226
certificates to 5.77 on a block whose true storey count is ≥ 6, not = 6. Using it needs a completeness
assumption the project has already established it does not have.

**Works, and I verified it after reading the Antigravity report: `sap_floor_dimensions`.** RdSAP enumerates
one entry per floor of the assessed dwelling. Over the 47 (1,042 cached certificates):

| Sub-population | Count | `max(len(sap_floor_dimensions))` |
|---|---|---|
| `house` / `terrace` — the certificate covers the whole dwelling | **33** | 2 storeys ×27, 3 storeys ×4, 1 storey ×2 |
| `apartments` — the certificate covers one flat only | 14 | unusable (1 floor per flat, says nothing about the block) |

Nothing on disk carries a storey count for these 47 otherwise: `levels`, `height_m`, `roof_height_m` are all
null and **zero** of them carry `roof:levels` or any levels-like key in `surplus_tags` (for contrast,
`roof:levels` is present on 413 London footprints overall).

Two limits to state with the +33: it is a **dwelling** storey count read as a **building** storey count, so a
subdivided house understates (`way/396622951`, 390.8 m² with 6 certificates, yields 2); and it is a `max`
over certificates, which is the right estimator only if at least one certificate covers the tallest part.
Both make it a new rule → an owner ruling, not a fix.

### Verdict — category 2

- **(b) real data fix, up to +163 (Madrid):** Catastro `GetBuildingPartByParcel`, 163 known parcel ids. Needs one authorised network campaign.
- **(c) owner ruling, +33 (London):** read `len(sap_floor_dimensions)` as the storey count for `house`/`terrace` only.
- **(a) dead end, 14 (London apartments):** the certificate describes a flat, not the block. Only an external height raster reaches these.

---

## 3. `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` — Lyon 37 + Madrid 1 = 38

Code verified: `openubem/semantic/european_archetype_mapping.py:193-194`, exactly as quoted. The docstring's
claim (lines 37-41) that every threshold is read off `tabula_archetypes_fr.json` was tested against the
registry files directly.

**For France the claim holds.** Distinct `n_apartment_rounded` per building type in
`openubem/data/construction/tabula_archetypes_fr.json` (40 records):

| Type | `n_apartment` values present | `n_storey` values present |
|---|---|---|
| SFH / TH | 1 | 1–3 |
| MFH | 1, 4, 5, 8, 9, **12** | 1–4 |
| AB | **15**, 26, 29, 30, 31, 34, 48, 69, 86 | 5–10 |

The French registry really does stop MFH at 12 apartments and start AB at 15. **The 13–14 gap is
source-backed, not invented** — but TABULA is a library of representative exemplars, not a regulation
forbidding real buildings from having 13 dwellings, so closing the gap is a new threshold and a ruling.

Distribution of the 37 Lyon buildings — **all have 4–9 storeys, none has 10 or more**:

| Dwellings | Storeys 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|
| 13 | 2 | 2 | 6 | 3 | 5 | — |
| 14 | 1 | 2 | 5 | 5 | 4 | 2 |

Three closures, all recoverable counts measured:

1. **Storey partition** — `13–14 & storeys ≤ 4 → MFH`, `13–14 & storeys ≥ 5 → AB`: recovers **all 38**
   (3 Lyon → MFH, 34 Lyon + 1 Madrid → AB). It reuses the storey boundary the rule already draws and keeps
   both neighbour buckets' storey ranges intact. **This is the option I would put first.**
2. **Extend MFH to `2 ≤ dwellings ≤ 14`**: recovers all 37 Lyon (every one sits inside MFH's post-`D-EU-37`
   storey window `≤ 9`), but pushes 9-storey buildings into MFH, which the FR registry caps at 4 storeys.
3. **Extend AB down to `dwellings ≥ 13`**: recovers 34; the 3 buildings at 4 storeys still fail AB's `storeys ≥ 5`.

**For Spain the docstring's claim does not hold, and this is a defect.** The gate at
`european_archetype_mapping.py:181` routes **both** `FR` and `ES` into `derive_bdtopo_building_type`, so the
French registry's gap is applied to Madrid. The Spanish registry has no such gap:

| Type (ES) | `n_apartment` values present |
|---|---|
| AB | 7, 10, **14**, 18, 78 |
| MFH | 8, 9, 12, **15**, 16 |

`tabula_archetypes_es.json` contains an AB archetype with **14** apartments and MFH archetypes with 15 and 16
— the ES ranges overlap and offer no dwelling-count boundary at all, let alone one at 13–14. Madrid's single
excluded building (`way/224012143`, 14 dwellings, 5 storeys, year 1970 observed from Catastro) is excluded by
a rule its own country's registry does not support.

### Verdict — category 3

- **(c) owner ruling, +38:** close the gap. Recommend the storey partition (option 1).
- **(c) attached defect finding:** the FR 13–14 gap has no basis in `tabula_archetypes_es.json` and arguably
  should never have applied to `ES`. Because it changes a ruled rule's country scope, it is still a ruling.

---

## 4. `IDF_ASSEMBLY_FAILED_RuntimeError` — Lyon 4 + Madrid 9 + Bologna 4 = 17

Catch site verified at `scripts/run_eu_s2_district_campaign.py:443-449`. **The in-code comment's hypothesis
("a degenerate zero-length edge surviving the ruled-grid partition") is wrong**, and I can say so with the
captured exception rather than a guess.

### 4.1 The 13 FR/ES failures, named

Nothing on disk records them; they were derived as `mapped_ok − prepared_buildings.csv`:

| District | Building id | Stem | Interior rings | Verts | Min edge (m) | Storeys | Dwellings | Valid / simple |
|---|---|---|---|---|---|---|---|---|
| Lyon | `BATIMENT0000000240879992_part0` | `132b99ec4969a8e2` | 1 | 29 | 0.0996 | 6 | 26 | ✅ / ✅ |
| Lyon | `BATIMENT0000000240880367_part0` | `5e0376cc50cbea69` | **0** | 30 | 0.3161 | 8 | 47 | ✅ / ✅ |
| Lyon | `BATIMENT0000000240880410_part0` | `cee45cbc2718154c` | 1 | 6 | 2.8039 | 8 | 21 | ✅ / ✅ |
| Lyon | `BATIMENT0000000240880479_part0` | `fb2616dbcb25659d` | 1 | 12 | 0.3166 | 8 | 43 | ✅ / ✅ |
| Madrid | `relation/12628570` | `19f9bca61b89709d` | 1 | 16 | 0.0888 | 4 | 21 | ✅ / ✅ |
| Madrid | `relation/12702625` | `19353088b38e9293` | 1 | 10 | 1.3446 | 3 | 9 | ✅ / ✅ |
| Madrid | `relation/12707193` | `70c09d03c00aaeb5` | 3 | 15 | 2.5822 | 4 | 25 | ✅ / ✅ |
| Madrid | `relation/12818819` | `919761afea1827b3` | 1 | 16 | 0.3375 | 4 | 31 | ✅ / ✅ |
| Madrid | `relation/4165181` | `0f131d6bfc4c55dd` | 1 | 17 | 1.2016 | 4 | 14 | ✅ / ✅ |
| Madrid | `relation/5808696` | `bb812ebbb389f7ef` | 1 | 7 | 0.1361 | 3 | 7 | ✅ / ✅ |
| Madrid | `way/311968163` | `20760fb7a921e2c7` | **0** | 9 | 1.0585 | 5 | 14 | ✅ / ✅ |
| Madrid | `way/333138113` | `a6ab77197f54e1e0` | **0** | 15 | 0.4040 | 7 | 43 | ✅ / ✅ |
| Madrid | `way/432405737` | `55bb78129ce9131b` | **0** | 12 | 1.5877 | 6 | 68 | ✅ / ✅ |

**Every one is a valid, simple polygon** — no self-intersection, no zero-length edge, no degenerate ring. The
real covariate is the **courtyard**:

| District | Footprints with an interior ring | Failures among them | Failures among hole-free footprints |
|---|---|---|---|
| Lyon | 17 | 3 (**17.6 %**) | 1 / 456 (0.22 %) |
| Madrid | 121 | 6 (**5.0 %**) | 3 / 896 (0.33 %) |

Failures also skew dense: dwellings-per-floor mean 4.55 (Lyon) / 5.37 (Madrid) among failures vs 1.97 / 2.80
among successes.

### 4.2 Root cause, reproduced — the two sub-populations are structurally different

Re-running `build_idf_for_building` for all 13 gives the same exception every time, raised at
`scripts/run_eu_s2_campaign.py:577`:

```
RuntimeError: interzone_vertex_mismatch_unresolved: mismatched=[...] near_duplicate_vertex=True
```

Splitting on the mismatch list gives a **perfect** partition that coincides exactly with the courtyard split:

| Sub-population | Count | Which buildings | State at the raise |
|---|---|---|---|
| `mismatched=[]`, only a residual near-duplicate vertex | **4** | `BATIMENT…0367`, `way/311968163`, `way/333138113`, `way/432405737` | exactly the 4 **hole-free** footprints; the reroute to `one_zone_per_floor` **did** fire and **did** clear every raw mismatch |
| `mismatched` non-empty (2–14 unresolved Floor↔Ceiling pairs) | **9** | the 9 **courtyard** footprints | reroute declined by design (`openubem/idf/surfaces.py:640-696`, courtyard hole ≥ 1 m²) |

### 4.3 🔴 The 4 are lost to an asymmetry in the `D-EU-58` tolerance, not to bad geometry

`scripts/run_eu_s2_campaign.py:565` gates the T15 / `D-EU-58` tolerance on:

```python
if not did_reroute and not mismatched:
    ...  # retain the geometry, disclose fallback_reason
else:
    raise RuntimeError(...)
```

These 4 end in **exactly the tolerated state** — zero raw mismatches, one residual sub-millimetre
near-duplicate vertex — and are excluded from the tolerance solely because `did_reroute` is `True`. A
building reaching the identical end state *without* rerouting is simulated with a disclosed
`fallback_reason`; these 4 are discarded. `D-EU-58`'s own rationale in that comment block — *"that is
already-valid geometry being discarded, not a defect being masked"* — applies to them verbatim.

The candidate change is one condition: `if not mismatched:`. It widens a signed tolerance, so it is a ruling,
not a fix I would make unilaterally.

The other **9 are genuine**: after the reroute correctly declines on a courtyard, real unresolved interzone
Floor↔Ceiling pairs remain between vertically stacked blocks. There is **no blanket repair** — the
`FINDING 249` near-duplicate-vertex carve-out already ran on all 9 and did not help. Collapsing a courtyard
into one block produces a donut polygon that EnergyPlus rejects at `CheckConvexity`, which is precisely why
`surfaces.py` declines. These are a geometry project (courtyard-aware interzone pairing), not a patch.

**Bologna's 4** could not be classified here: `_it_rows` needs the two live Bologna endpoints, so the failing
ids are not derivable offline. The Antigravity report names them as `29583`, `29801`, `32639`, `33359`, all
with one interior ring — i.e. all in the courtyard group. Carried as its finding, unverified from here.

### Verdict — category 4

- **(c) owner ruling, +4:** extend the `D-EU-58` tolerance to any post-reroute state with zero raw mismatches.
- **(a) genuine, 9 (+4 Bologna if the courtyard classification holds):** valid courtyard footprints with real unresolved interzone pairs.

---

## 5. `MISSING_OBSERVED_YEAR_BUILT` — Lyon 8 + Madrid 11 = 19

### 5.1 France (8) — the field is `date_d_apparition`, and it is genuinely null

`openubem/acquisition/bdtopo_fetcher.py:109` sets `year_built` from BD TOPO `date_d_apparition` only
(`_parse_bdtopo_year`, lines 82-95). All 8 carry `provenance_year_built = IGN_BDTOPO_MISSING`; all 8 have an
observed dwelling count and storey count, so the year is the *only* thing missing:

| Building | Dwellings | Storeys | Footprint m² | `appariement_fichiers_fonciers` |
|---|---|---|---|---|
| `BATIMENT0000000240880045_part0` | 71 | 10 | 954.3 | `A 1.0` |
| `BATIMENT0000000240880358_part0` | 25 | 6 | 259.6 | `A 1.0` |
| `BATIMENT0000000240880405_part0` | 25 | 7 | 411.3 | `A 1.0` |
| `BATIMENT0000000240881161_part0` | 9 | 3 | 273.0 | `C 0.8` |
| `BATIMENT0000000240881177_part0` | 11 | 8 | 99.1 | `A 1.0` |
| `BATIMENT0000000240881334_part0` | 5 | 5 | 60.5 | `C 0.1` |
| `BATIMENT0000000240881344_part0` | 44 | 9 | 1229.8 | `C 0.7` |
| `BATIMENT0000000240881535_part0` | 4 | 5 | 72.9 | `A 1.0` |

A sanity check that passed and is worth recording: Lyon's 522 observed years run 1550–2010 and peak in
1800–1899 (81 in the 1850s, 76 in the 1800s) — the real construction history of the Croix-Rousse canut
district. `date_d_apparition` is behaving as a construction date here, so there is **no hidden provenance
problem to reopen**.

All 8 carry a non-null `appariement_fichiers_fonciers` flag, i.e. BD TOPO itself declares each of these
matched to the DGFiP *Fichiers Fonciers* — the source their `nombre_de_logements` came from. The fiscal
record therefore exists for all 8 and carries a construction-year field BD TOPO does not expose. The named
candidate is the CSTB **BDNB**, which publishes a per-building `annee_construction` keyed on BD TOPO building
identifiers — an exact-id join of the shape already used here. **Its coverage over these 8 is unmeasured**
(same live-fetch bar as §1.4). It is a candidate with a real join key, not a verified recovery.

### 5.2 Spain (11) — root-caused to one line in the sidecar

All 11 (7 year-only, 4 year+dwellings) are exactly the sidecar's
`NO_INTERSECTING_CATASTRO_RESIDENTIAL_BUILDING` rows — `catastro_local_id`, `year_built`, `n_dwellings`,
`overlap_area_m2` all null. That reason is emitted by
`openubem/acquisition/catastro_inspire_fetcher.py:246` (`residential = catastro[catastro["current_use"] ==
RESIDENTIAL_CURRENT_USE]`): **the join considers only features coded `1_residential`.**

The probe measured 194 non-residential Catastro features in the same bbox (74 industrial, 44 retail, 41
office, 35 public services, 7 null-use), and its own `manifest_rows_with_any_catastro_partner: 1183` is
*also* computed on the residential subset — so nothing on disk tells us whether these 11 OSM-residential
footprints intersect a **non-residential** Catastro building or no Catastro building at all. The probe CSV
carries no geometry column, so the test cannot be run offline.

That test is the whole question for these 11: if they intersect a `4_2_retail` or `3_industrial` parcel, the
two sources disagree about the use and the exclusion is arguably *correct*; if they intersect nothing, the
footprints sit outside cadastral coverage and the exclusion is certainly correct.

### Verdict — category 5

- **(a)/(b) undecidable offline, 8 (Lyon):** BD TOPO genuinely lacks the year; BDNB is a real, exact-id-joinable candidate whose coverage over these 8 is unmeasured.
- **(a) root-caused, 11 (Madrid):** no residential Catastro partner. One cheap authorised probe decides whether this is correct or a use-code artefact.

---

## 6. Bologna `CENSUS_SECTION_PERIOD_TIE_*` (12) + `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` (4) = 16

Code verified at `scripts/run_eu_s2_district_campaign.py:291` and `:298`, inside `_it_rows`. The construction
period is the **modal** `E8…E16` count of the ISTAT 2011 section the building's **centroid** falls in
(`predicate="within"`), stamped `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD`.

Read directly out of the cached `_cache/dati-cpa_2011.zip` (comune `PROCOM = 37006`, 2,260 sections):

- **204 sections (9.0 %) have a modal tie**, at tiny maxima — commonest are `E9_E10` at max 1 (12 sections),
  `E10_E11` at max 2 (10), `E10_E11` at max 1 (10), `E9_E10` at max 2 (10).
- **171 sections (7.6 %) have zero *occupied* residential buildings.**

The Antigravity report supplied the section ids, which I then verified line-by-line in the same cached CSV —
**all five check out exactly**:

| Section | `P1` (residents) | `E1` | `E2` (residential) | `E3` (occupied residential) | `E8…E16` | Exclusion |
|---|---|---|---|---|---|---|
| 1287 | 89 | 9 | 9 | 8 | E8=3, **E9=3**, E10=1, E11=1 | the 10 `E8_E9` ties |
| 1266 | 5 | 3 | 3 | 2 | **E9=1, E10=1** | the 2 `E9_E10` ties |
| 1244 | 0 | 1 | 1 | 0 | all zero | `NO_RESIDENTIAL_BUILDINGS` |
| 1253 | 0 | 1 | 1 | 0 | all zero | `NO_RESIDENTIAL_BUILDINGS` |
| 1299 | 0 | 2 | 2 | 0 | all zero | `NO_RESIDENTIAL_BUILDINGS` |

🔴 **This corrects a hypothesis of my own.** `E8…E16` sums to `E3` in every section checked (1287: 8 = 8;
1266: 2 = 2; 1244/1253/1299: 0 = 0), so the epoch breakdown partitions **occupied** residential buildings,
not all of them. The 4 `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` sections **do contain residential buildings**
(E2 = 1, 1, 2) — they were simply **unoccupied at the 2011 census** (P1 = 0), so ISTAT publishes no epoch for
them. The exclusion key is a misnomer, and my earlier idea that a boundary/centroid artefact was to blame is
**wrong**: re-joining by largest polygon overlap would not recover these 4, because the target section has no
epoch data to give. Only a fallback to a neighbouring section — which is interpolation — would, and that
should not be proposed.

For the **12 ties**, the tie is *within a single section* (1287 and 1266), so the brief's suggestion of
"centroid distance to each candidate section's centroid" does not apply — there is only one section. The real
argument for a ruling is different and stronger: the **accepted** rule (`D-EU-34`) routinely assigns a whole
section's period on a **one-building margin**, while the tie rule refuses when that margin is zero. The
information difference between "2 vs 1" (accepted) and "3 vs 3" (refused) is one building.

No independent Bologna building-age source exists, and I checked: `02_residential_manifest.gpkg` carries
`year_built` null and `levels` null on all 1,220 rows (`provenance = BOLOGNA_RIFTER_MISSING`); the only
date-like keys in `surplus_tags` are `data_istit`/`data_varia`, which are cadastral record dates (1900
sentinel on 1,127 of 1,220 rows), not construction years; and the CTC `altezza_gr` eaves height is already
consumed for storeys and says nothing about age.

### Verdict — category 6

- **(c) owner ruling, +12:** an explicit tie policy (e.g. the older cohort in a historic core), argued from
  the fact that the accepted modal rule already turns on a one-building margin.
- **(a) genuine dead end, 4:** the sections have residential buildings but no published epoch, because none
  was occupied in 2011. Nothing but interpolation reaches them.

---

## 7. London `UNMAPPABLE_RESIDENTIAL_TYPE` (6)

Code verified at `scripts/run_eu_s2_district_campaign.py:197`. All six carry the same OSM tag —
**`building=residential`** — in neither the `{apartments, detached, terrace}` map nor `FINDING 251`'s `house`
carve-out:

| Building | Tag | EPC band | Band → period | Levels | Footprint m² |
|---|---|---|---|---|---|
| `way/1058438116` | `residential` | H | GB.06 | 2 | 64.1 |
| `way/1058438118` | `residential` | G | GB.05 | 2 | 64.3 |
| `way/1058438120` | `residential` | G | GB.05 | 2 | 62.6 |
| `way/554859559` | `residential` | G | GB.05 | 2 | 63.7 |
| `way/190348379` | `residential` | E | GB.04 | 4 | 638.8 |
| `way/204487525` | `residential` | L | GB.08 | 7 | 377.3 |

All six already have a non-straddling band and a valid storey count — the tag is the only blocker. The
population is visibly two shapes: four ~63 m² two-storey houses and two large multi-storey blocks.

This is **not** a transcription fix. `FINDING 251` split `house` into SFH/TH by footprint adjacency, which
works because `house` already excludes AB; `residential` does not, and GB has **no dwelling count at all**
(`gb_epc_coverage_probe.json`: *"dwelling_count_present_in_any_certificate": false* — a measured absence). A
`residential` rule must therefore type on storeys + adjacency alone, which is a new threshold.

The natural precedent is Bologna's own storey ladder (`run_eu_s2_district_campaign.py:270-275`):
`storeys ≤ 2 → TH/SFH by adjacency · storeys 3–4 → MFH · storeys ≥ 5 → AB`. Applied here that gives four
TH/SFH, one MFH (`way/190348379`, 4 storeys) and one AB (`way/204487525`, 7 storeys). The Antigravity report
proposes the same idea but with `≥ 3 → AB`, which drops the MFH rung its own cited precedent contains and
would type a 4-storey building as an apartment block; the three-rung form is the consistent one.

### Verdict — category 7

- **(c) owner ruling, +6:** admit `building=residential` under the Bologna storey ladder. Low value, cheapest
  ruling on the list, evidence complete.

---

## 8. `MISSING_OBSERVED_DWELLING_COUNT` — Lyon 1 + Madrid 1 = 2

Both fall out of the category-5 tracing, one line each:

- **Lyon `BATIMENT0000000240880398_part0`** — 8 storeys, 34.9 m, year 1820 observed, footprint 24.9 m². BD TOPO
  records `nombre_de_logements = "0.0"` with `usage_2 = "Commercial et services"`; `_observed_dwellings`
  requires `> 0`, so it **correctly** fails closed. This is not a missing value — it is an observed zero on a
  building BD TOPO treats as commercial. *(Credit: the Antigravity report caught this; my first pass recorded
  the tag as absent rather than zero.)*
- **Madrid `way/941927256`** — has a Catastro partner (`0391418VK4709A`, overlap 66.75 m², year 1910 observed)
  whose `numberOfDwellings` is empty; the sidecar names it exactly
  `CATASTRO_PARTNER_CARRIES_NO_DWELLING_COUNT`. Note `condition = declined` — Catastro records this parcel as
  a deteriorated building, a plausible reason for an unpopulated dwelling count.

### Verdict — category 8

- **(a) explained, 2.** Not worth a ruling. The Lyon row is arguably not residential at all.

---

## 9. Lyon `TYPOLOGY_SIGNALS_DISAGREE` residual (10) — listed, not re-opened

As instructed. The shape confirms `D-EU-37` §4:

| Dwellings | Storeys | Count |
|---|---|---|
| 15 | 3 | 1 |
| 15 | 4 | 2 |
| 16 | 4 | 3 |
| 18 | 4 | 1 |
| 20 | 4 | 1 |
| 1 | 5 | 1 |
| 1 | 6 | 1 |

(8 at `dwellings ≥ 15 & storeys ≤ 4`, 2 at `dwellings == 1 & storeys ≥ 5`.) No new signal found; nothing
proposed. Madrid's single `TYPOLOGY_SIGNALS_DISAGREE` (`way/340701292`: 45 dwellings, 2 storeys, 40.5 m²
footprint) is a Catastro parcel-level dwelling count landing on a tiny footprint — a genuine outlier, not a
rule gap.

---

## 10. Recovery ledger

**(b) — real code/data fixes, no new threshold**

| # | Fix | District | Net prepared |
|---|---|---|---|
| b1 | read `sap_building_parts[*].construction_year` when no age band | London | **+24** |
| b2 | resolve a straddle by an explicit year **consistent with** the band | London | **+6** |
| b3 | Catastro `GetBuildingPartByParcel` storeys (163 known parcel ids) — one authorised probe | Madrid | **up to +163** |

**(c) — policy questions for the owner, framed like `D-EU-37`**

| # | Question | District | Net prepared |
|---|---|---|---|
| c1 | resolve a straddle by intersecting every constraint the footprint's certificates impose | London | **+75** (+69 beyond b2; +59 on the per-building-part reading) |
| c2 | close the 13–14 dwelling gap by storey partition (`≤ 4 → MFH`, `≥ 5 → AB`) | Lyon + Madrid | **+38** |
| c3 | read `len(sap_floor_dimensions)` as the storey count for `house`/`terrace` only | London | **+33** |
| c4 | extend the `D-EU-58` tolerance to any post-reroute state with zero raw mismatches | Lyon + Madrid | **+4** |
| c5 | an explicit ISTAT tie policy (sections 1287 and 1266) | Bologna | **+12** |
| c6 | admit `building=residential` under the Bologna storey ladder | London | **+6** |

**(a) — dead ends, with what was checked**

| Population | Count | Checked |
|---|---|---|
| London, no EPC at any UPRN (395) or no UPRN (23) | **418** | probe counts reconcile exactly; outside EPC entirely; external sources licence-blocked per the Antigravity survey |
| London straddles still ambiguous or self-contradictory after both constraints | **269** | 70 contradictory + 199 ambiguous |
| London apartment blocks with no storey count | **14** | certificate describes one flat; needs an external height raster |
| Courtyard IDF failures | **9** (+4 Bologna) | reproduced; real unresolved interzone pairs; `FINDING 249` carve-out already ran |
| Lyon / Madrid missing years | **19** | source fields traced; BDNB named but unmeasured |
| Bologna sections with buildings but no published epoch | **4** | `E8…E16` partitions `E3` (occupied); all three sections have `P1 = 0` |
| Lyon out-of-scope typology outliers | **10** | `D-EU-37` §4, not re-opened |

### What 100 % actually costs

Taking **every** option above at its most optimistic — all three (b) fixes, all six (c) rulings, and an
external source for the 19 missing years and 2 dwelling counts — the fleet reaches roughly
**3,420–3,440 / 4,186 ≈ 82 %** (the range is unquantified overlap between b1 and c3, both of which touch
London footprints that fail on two gates at once).

The residual ~750 is dominated by London: **418 buildings that have never had an EPC lodged**, plus ~269
straddles that the certificates themselves contradict or leave ambiguous. No rule change reaches them.

**100 % is not attainable from the sources currently wired in.** It requires a UK building-age dataset
outside EPC whose coverage over these specific 418 footprints is unknown, and — on the Antigravity licence
survey — may not exist as open data at property level at all.

---

## 11. Notes for whoever implements

- Nothing here was implemented and nothing was registered. If b1/b2 or c4 land, the exact string
  `interzone_vertex_mismatch_unresolved: mismatched=[...] near_duplicate_vertex=True`
  (`scripts/run_eu_s2_campaign.py:577`) is the symptom to file in
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in the house format.
- The IDF-failure ids in §4.1 exist nowhere on disk: `prepare()` counts geometry exclusions by exception
  string only (`scripts/run_eu_s2_district_campaign.py:447`). Recording the failing `building_id` alongside
  the count would have made §4 a `grep` instead of a 13-building reproduction — worth one line whenever that
  file is next touched for another reason.
- `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` is a misleading key: the sections do have residential buildings,
  they have no *occupied* ones. `CENSUS_SECTION_NO_OCCUPIED_RESIDENTIAL_BUILDINGS` would describe it.
- Register numbering as of this report: `STATE_european_locations_v5.md` claims through `FINDING 255` and
  `D-EU-101`, so the next free are **`FINDING 256`** and **`D-EU-102`**. The header line at
  `STATE_european_locations_v5.md:32` ("Next free: `D-EU-102`, `FINDING 253`") is stale by three findings.

---

## 12. Cross-check against the Antigravity report

Both reports were written independently against the same brief. This section is the reconciliation.

### 12.1 Independent agreement (raises confidence, no action)

- Fleet arithmetic, all four districts and all nine exclusion keys.
- Category 4's `did_reroute` gate: **both** found the same 4 hole-free buildings, the same
  `if not did_reroute and not mismatched:` asymmetry, and the same one-condition fix. Same 4 ids.
- Category 3's registry evidence: MFH ends at 12 apartments, AB starts at 15, in `tabula_archetypes_fr.json`;
  and 34 of the 37 Lyon buildings at 5–9 storeys, 3 at 4 storeys.
- Category 7: all six are `building=residential`, all six already have a usable band and storeys.
- Category 9: no new signal; stays adjudicated.
- Category 2 Madrid: `numberOfFloorsAboveGround` is `xsi:nil / other:unpopulated` on 1,883/1,883 features and
  the storey count lives on `BuildingPart`.

### 12.2 What the Antigravity report corrects in mine — adopted

1. **Category 8, Lyon.** It records `nombre_de_logements = "0.0"` (an observed zero on a
   `usage_2 = "Commercial et services"` building), not an absent tag. Verified in the raw `surplus_tags`;
   my §8 is corrected.
2. **Category 2, London.** Its `sap_floor_dimensions` idea is real and I verified it: 33 `house`/`terrace`
   footprints of the 47 yield a storey count (2 ×27, 3 ×4, 1 ×2). I had tested and rejected a weaker proxy
   (EPC floor area ÷ footprint) and would have closed the category as a dead end. **+33 adopted**, with the
   dwelling-vs-building caveat added.
3. **Category 6, the 4 no-residential sections.** Its section ids let me check the ISTAT rows directly, and
   they show `E8…E16` partitions `E3` (occupied residential), with `P1 = 0` on all three sections. My
   "re-join by largest overlap" proposal was wrong and is withdrawn.
4. **Category 3, closure form.** Its storey partition (`≤ 4 → MFH`, `≥ 5 → AB`) is a better-motivated
   closure than either of my single-bucket extensions, and recovers Madrid's building too. Promoted to
   option 1.
5. **Category 1.4 and 6, external sources.** It had network access and surveyed VOA / OS NGD / GLA LBSM. That
   work is beyond what this session could do and is carried, attributed and flagged as unverified here.

### 12.3 What this report corrects in the Antigravity report — please read before acting on it

1. 🔴 **"Category 1a … the remaining 445 have no matching certificate. Recovery: 0."** Not true for 27 of
   them. `824 − 797 = 27` footprints — its own quoted numbers — **do** have retrieved certificates; they are
   full-SAP, which carries `construction_year` instead of `construction_age_band`. **+24 prepared** is being
   left on the table by that verdict.
2. 🔴 **"`construction_year` is 0 out of 355."** Measured: **1,336 cached certificates carry
   `construction_year`**, 67 footprints hold at least one, and **15 of those are straddling footprints**.
   Counter-example on disk: `way/192335494` holds 40+ SAP certificates lodged 2009-10, each with
   `construction_year = 2008`, alongside its RdSAP band-J and band-K certificates. Its recursive cache scan
   appears to have looked only inside the RdSAP certificates already known to carry a band.
3. ⚠️ **"Majority-span allocation … Recover +355."** This assigns every straddling band to whichever TABULA
   period covers most of its year range — 60 % of the range in band K's case. That is the *assignment* the
   `D-EU-22` ruling refused for Italy and that the signed `CP3` verdict in `gb_epc_coverage_probe.json`
   restates for GB (*"turning a band into a year is ASSIGNMENT"*). It may still be the ruling the owner wants,
   but it must be presented as **overriding a signed verdict**, not as a neutral option, and it cannot be
   quoted alongside the observed-year districts. The constraint-intersection rule in §1.3 recovers 86 of the
   355 **without** assignment, and should be ruled on first.
4. ⚠️ **Category 7 rule shape.** Its proposal (`≤ 2 → TH/SFH`, `≥ 3 → AB`) cites Bologna lines 270-275 as the
   precedent, but that ladder has three rungs (`3–4 → MFH`). Under its own precedent `way/190348379`
   (4 storeys) is MFH, not AB.
5. ⚠️ **Its verdict labels for categories 2 and 7.** `sap_floor_dimensions` (+33) and the `residential` tag
   rule (+6) both introduce a new threshold, so both are **(c) rulings**, not **(b) fixes**. Its own §3 lists
   the `residential` rule under "Immediate Code Bug Fixes", which would have it implemented without a ruling.
6. Minor: band B's majority span is 19/30 = **63.3 %**, not 65.5 %.

### 12.4 Where the two ledgers land

| | Antigravity | This report |
|---|---|---|
| (b) fixes, no ruling | +10 | **+30 now, +163 more with one authorised Catastro probe** |
| (c) rulings | +393 (of which +355 is majority-span assignment) | **+168** (+75 straddle by constraint intersection, +38 typology, +33 storeys, +12 ties, +6 tag, +4 IDF) |
| Reachable fleet | 3,469 / 4,186 (82.9 %) | **≈ 3,420–3,440 / 4,186 (≈ 82 %)** |
| Hard ceiling | 717 | **≈ 750** |

The two ceilings agree to within ~1 % of the fleet despite disagreeing on almost every route to get there —
the difference is that the Antigravity path spends one large assignment ruling (+355) where this one spends
three measured fixes and five smaller rulings. **The headline conclusion is the same and is robust: ~82 % is
the ceiling, and the last ~18 % is London stock that has never had an EPC.**
