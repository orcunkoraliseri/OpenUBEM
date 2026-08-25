# EU-02 — Dense residential neighbourhood selection for the European campaign

**Date:** 2026-08-24 · **Executed in-session against live public APIs** (not delegated to an external LLM)
**Serves:** MVP §9.7.2 gates `NS-01`–`NS-10`, MVP §10.4 four-panel input audit, decision `D-EU-10` (data half)
**Pre-registered rule (written before any ranking measurement):** [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_prereg_selection_rule.md`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_prereg_selection_rule.md)
**Machine-readable evidence:** [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_madrid.csv`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_madrid.csv) · [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_london.csv`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_london.csv) · [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_bologna.csv`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_bologna.csv) · [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_lyon_quartier.csv`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_lyon_quartier.csv) · [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_lyon_iris.csv`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_lyon_iris.csv) · [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_site_measurements.csv`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_site_measurements.csv) · [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_reproducible_queries.json`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_reproducible_queries.json) · [`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/)

> **What this document is.** Every building count below was **measured** on 2026-08-24 from
> OpenStreetMap through the Overpass API, filtered by OpenUBEM's own use-class crosswalk
> (`openubem/data/osm_to_use_class.json`), and joined to **official boundary polygons** obtained from
> the publishing authority. It is not a plan and not an estimate. What it is *not*: no footprints were
> written into the repository, no residential registry was built, no geometry, IDF or simulation exists
> for any site. See §6.

> **Relation to DR10.** DR10 (accepted 2026-08-23) pinned the datasets and offered candidate
> sub-units as *estimates*; the arc ruled that the final unit is chosen by "the project's own computed
> counts under `NS-03`/`NS-05`". This document is that computation. Where DR10's estimates and the
> project's own counts disagree, §2.5 states by how much.

---

## 0. Method actually executed

1. **Pre-registration.** The pool, the residential filter, the density metric and the tie-breaks were
   written to `../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_prereg_selection_rule.md` **before** the ranking measurement was run. The
   density metric matches the one already ruled under `D-EU-10`: *residential buildings per km² of an
   open administrative sub-unit after the residential filter, dwelling/floor-area proxy as tie-break.*
2. **Boundaries** were taken from the publishing authority, not drawn: Madrid *barrios* (OSM
   `admin_level=10` relations mirroring the Ayuntamiento set), London wards from the **ONS Open
   Geography Portal**, Bologna *aree statistiche* from the **Comune di Bologna** open-data portal,
   Lyon *quartiers* and *IRIS* from **Métropole de Lyon**.
3. **Buildings** were fetched per parent unit (7 Madrid districts, 3 London boroughs, Bologna comune,
   Lyon commune) with `way["building"]` + `relation["building"]`, `out tags center`, then assigned to
   candidate polygons by point-in-polygon in the unit's national projected CRS.
4. **Residential filter** = the eight `residential` tokens of `openubem/data/osm_to_use_class.json`.
   `building=yes` and empty values are the crosswalk's `ambiguous_tokens` and are counted as
   **unknown**, never as residential.
5. **Shortlisted sites** were re-measured independently through a second query path (bbox fetch with
   full geometry, then clip against the official polygon) to obtain footprint areas, `building:levels`
   coverage and the floor-area proxy, and a third time with `out count` for a directly reproducible
   number (§4).

Populations measured: **44** Madrid barrios, **58 + 38** London wards, **90** Bologna aree statistiche,
**36** Lyon quartiers and **185** Lyon IRIS — **451 candidate units**, 14 bulk extracts,
≈ 197,000 building records. (The 38 extra London wards are the supplementary DR10 check of §2.2.)

---

## 1. Executive decision table

| site_id | City / neighbourhood | Decision | Boundary status | Centroid (lon, lat) WGS84 | bbox (W,S,E,N) | Footprint source / licence | Residential count | Reason |
|---|---|---|---|---|---|---|---|---|
| `ES-MAD-BELLASVISTAS` | Madrid — **Bellas Vistas** (Tetuán, barrio 061) | **SELECTED** | `VERIFIED` | −3.707645, 40.452455 | −3.713328, 40.446854, −3.702912, 40.457621 | OSM/Overpass, ODbL 1.0 — derived counts and maps publishable with attribution | **1,025 · MEASURED** | Rule output: inside the top decile by residential buildings/km² (1,430.6) among the 28 barrios passing the 0.60 residential-dominance gate, and the closest of that decile to the `N1` midpoint. Exceeds `N1`; see §6. |
| `GB-LDN-STDUNSTANS` | London — **St Dunstan's** ward, Tower Hamlets (`E05009329`) | **SELECTED** | `VERIFIED` | −0.040004, 51.518428 | −0.050013, 51.512597, −0.033744, 51.524248 | OSM/Overpass, ODbL 1.0; boundary ONS OGL v3.0 | **1,241 · MEASURED** | Rule output: highest residential density of the whole three-borough pool (1,827.5/km²), 90.5 % residential-dominant, 90.8 % `building:levels` coverage. Exceeds `N1`; see §6. |
| `IT-BOL-PIAZZAUNITA` | Bologna — **Piazza dell'Unità** (Bolognina) *provisional* | **NO_SELECTION** | `VERIFIED` (boundary only) | 11.348524, 44.508757 | 11.340206, 44.504074, 11.356877, 44.512696 | OSM/Overpass, ODbL 1.0; boundary Comune di Bologna CC BY 4.0 | **177 · MEASURED** (of 803 buildings; 526 unknown) | The declared rule cannot select in Bologna: only 2 of 85 units reach 0.60 residential share, and its mechanical output (`LA BIRRA`, 210 residential) ranks **52nd of 85** on the city's own official household density. OSM tagging, not urban form, drives the ranking. |
| `FR-LYO-CROIXROUSSE` | Lyon — **Croix-Rousse Est et Rhône** *provisional* | **NO_SELECTION** | `VERIFIED` (boundary only) | 4.836958, 45.778074 | 4.832215, 45.773478, 4.843032, 45.782711 | OSM/Overpass, ODbL 1.0; boundary Métropole de Lyon (licence `NOT_VERIFIED`) | **659 · MEASURED** (of 1,497; 795 unknown) | **Zero of 36** Lyon quartiers reach 0.60 residential share — the French cadastre import leaves 61 % of Lyon buildings as `building=yes`. Residential dominance cannot be established from OSM tags alone. |

Naming for the existing OpenUBEM cell convention (`openubem/outputs/simulationResults/<cell>__*.png`):
`madrid_bellasvistas`, `london_stdunstans`, `bologna_piazzaunita`, `lyon_croixrousse`.

![Four selected neighbourhoods drawn from their own measured footprints: residential in green, unknown-use hatched grey, non-residential dark grey, official boundary in red.](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_selected_neighbourhoods_panel_c.png)

*Figure EU-02.1. Panel (c) of the MVP §10.4 four-panel audit, regenerated from the campaign's own
selected data — the same boundary and the same building-ID set in every panel, as `NS-07` requires.
Green enters the model; hatched grey (`building=yes`) and dark grey (non-residential) are excluded and
retained as audit context per `NS-08`. The contrast between the two upper panels and the two lower ones
is the Italy/France classifier blocker of §6, item 2, shown directly. Panels (a) construction period,
(b) energy-record availability and (d) construction material are **not** drawn: they require the
Catastro / EPC / BDNB joins listed in §3, none of which has been run. Reusable asset:
[`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_selected_neighbourhoods_panel_c.png`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_selected_neighbourhoods_panel_c.png),
also written flat to `openubem/outputs/eu02_selected_neighbourhoods_panel_c.png`.*

---

## 2. Candidate comparison

All units of every pool are in the CSVs; the tables below show the decisive rows. Every number is
`MEASURED` 2026-08-24 unless marked otherwise. `unknown` = `building=yes`/empty.

### 2.1 Madrid — 44 barrios of the *almendra central* (Centro, Arganzuela, Retiro, Salamanca, Chamartín, Tetuán, Chamberí)

Pass `R1` (≥100 buildings): 42. Pass `R3` (residential share ≥ 0.60): 28. Top decile = 3 units.
(The 44 measured units are the 43 barrios of the seven districts plus two edge cases removed by `R1`:
Atocha, 72 buildings, and Comillas, a single building spilling in from Carabanchel.)

| Rank | Barrio | District | km² | Buildings | Residential | Unknown | Res. share | **Res/km²** | Verdict |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Berruguete | Tetuán | 0.604 | 1,433 | 1,194 | 188 | 0.833 | **1,975.9** | Top decile; 1,194 ≫ `N1` |
| 2 | Embajadores | Centro | 1.022 | 1,787 | 1,678 | 27 | **0.939** | **1,641.6** | Top decile; best data completeness of the pool (1.5 % unknown); 1,678 ≫ `N1` |
| 3 | **Bellas Vistas** | Tetuán | 0.717 | 1,506 | **1,025** | 407 | 0.681 | **1,430.6** | **SELECTED** — closest of the decile to the `N1` midpoint |
| 4 | Universidad | Centro | 0.940 | 1,588 | 1,158 | 316 | 0.729 | 1,232.0 | Below decile cut |
| 5 | Palos de la Frontera | Arganzuela | 0.652 | 894 | 770 | 41 | 0.861 | 1,180.6 | Below decile cut; would be `N2`-sized |
| 6 | Justicia | Centro | 0.736 | 1,030 | 832 | 102 | 0.808 | 1,130.7 | Below decile cut |
| 7 | Sol | Centro | 0.446 | 693 | 501 | 81 | 0.723 | 1,122.9 | `N1`-sized but outside the decile |
| — | Vallehermoso | Chamberí | 1.072 | 485 | 64 | 391 | 0.132 | 59.7 | Rejected: fails `R3`; 80.6 % unknown |

**Madrid `N1`-sized whole barrios (500–600 residential, share ≥ 0.60), measured:** Sol 501 · Gaztambide 516 ·
Chopera 502 (share 0.928, unknown 1.1 %) · Recoletos 529 · Delicias 509.

### 2.2 London — 58 wards of Tower Hamlets, Islington and Hackney

Pass `R1`: 58. Pass `R3`: 26. Top decile = 3 units. Ranking used the ONS **BGC** generalised
boundaries; the selected site was re-measured on the full-resolution **BFC** boundary (§2.6).

| Rank | Ward | Borough | km² | Buildings | Residential | Unknown | Res. share | **Res/km²** | Verdict |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | **St Dunstan's** `E05009329` | Tower Hamlets | 0.681 | 1,400 | **1,269** | 78 | 0.906 | **1,862.3** | **SELECTED** (BFC re-measure: 1,372 / 1,241 / 0.679 km² / 1,827.5 per km²) |
| 2 | Island Gardens `E05009324` | Tower Hamlets | 1.039 | 2,021 | 1,852 | 52 | 0.916 | 1,781.9 | Top decile; 1,852 ≫ `N1` |
| 3 | Hillrise `E05013705` | Islington | 1.020 | 2,207 | 1,611 | 506 | 0.730 | 1,578.9 | Top decile; 1,611 ≫ `N1` |
| — | Barnsbury `E05013698` | Islington | 0.897 | 2,346 | 331 | 1,965 | 0.141 | 369.1 | Rejected: 83.8 % unknown — a mapping artefact, not low density |
| — | Bunhill `E05013699` | Islington | 0.837 | 857 | 95 | 613 | 0.111 | 113.5 | Rejected: fails `R3` |

**London `N1`-sized whole wards, measured:** Brownswood (Hackney) 536 · Homerton (Hackney) 557
(`building:levels` coverage 0.989).

Tagging completeness is strongly borough-dependent. Median ward unknown share: **Tower Hamlets 0.212**,
**Hackney 0.472**, **Islington 0.505** (maximum 0.838, Barnsbury). The ranking therefore partly measures
**mapping completeness**, which is why the residential-dominance gate is retained and why §6 requires
the EPC/UPRN join before `N1`.

**Supplementary check — DR10's own London boroughs.** DR10 proposed Earl's Court and a Camden LSOA
cluster, which lie outside the pre-registered pool (the three densest LADs by Census 2021). Camden and
Kensington & Chelsea were therefore measured afterwards with the identical method, as a check rather
than as a re-ranking ([`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_london_dr10_boroughs.csv`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_london_dr10_boroughs.csv)):
38 further wards, 20 of them passing the dominance gate. The densest are Kentish Town South
(1,854.7 residential/km², 1,521 residential) and Kentish Town North (1,808.9, 1,014) — both just below
St Dunstan's, so **the selection is unchanged over the extended 96-ward pool**. The check also adds
three `N1`-sized wards in Kensington & Chelsea: **Norland 535**, **Chelsea Riverside 536**,
**Abingdon 578** (the Earl's Court fabric DR10 named), each with `building:levels` coverage above 0.92.

### 2.3 Bologna — 90 *aree statistiche* (whole comune)

Pass `R1`: 85. Pass `R3`: **2**. The mechanical output is `LA BIRRA` (Borgo Panigale): 210 residential,
361.9 per km² — a peripheral area, **below `N1`**, ranked **52nd of 85** on the city's own household
density. Selection is therefore refused.

| Area statistica | Zona | km² | Buildings | Residential | Unknown | Res. share | Res/km² | **Families 2024** | **Families/km²** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BITONE | Mazzini | 0.606 | 759 | 130 | 570 | 0.171 | 214.5 | 5,841 | **9,640** |
| XXI APRILE | Costa Saragozza | 0.826 | 1,205 | 80 | 1,104 | 0.066 | 96.8 | 7,168 | 8,674 |
| MARCONI-2 | Marconi | 0.882 | 1,422 | 64 | 1,244 | 0.045 | 72.6 | 7,620 | 8,643 |
| **PIAZZA DELL'UNITA'** | Bolognina | 0.776 | 803 | 177 | 526 | 0.220 | 228.2 | 5,938 | 7,656 |
| GALVANI-2 | Galvani | 0.901 | 2,202 | 31 | 2,077 | 0.014 | 34.4 | 6,611 | 7,341 |
| LA BIRRA *(rule output)* | Borgo Panigale | 0.580 | 300 | 210 | 85 | 0.700 | 361.9 | 1,002 | 1,727 |

Families per area statistica are `MEASURED` from the Comune's own open dataset (2024 vintage,
CC BY 4.0) — the official dwelling proxy `NS-03` asks for. Spearman rank correlation between
OSM residential/km² and families/km² over the 85 units is **0.777**: the ordering is not inverted, but
the 0.60 dominance gate removes every genuinely dense area, leaving only peripheral house-tagged ones.

### 2.4 Lyon — 36 quartiers (Métropole de Lyon) and 185 IRIS

Pass `R1`: 36 quartiers. Pass `R3`: **0** — the best is *Mutualité Préfecture Moncey* at 0.570.

| Quartier | km² | Buildings | Residential | Unknown | Res. share | Res/km² | levels cov. |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Croix-Rousse Est et Rhône** | 0.591 | 1,497 | 659 | 795 | 0.440 | **1,114.9** | 0.895 |
| Haut et Cœur des Pentes | 0.375 | 853 | 380 | 434 | 0.446 | 1,012.6 | 0.989 |
| Brotteaux | 0.558 | 1,053 | 539 | 450 | 0.512 | 965.5 | 0.670 |
| Sans-Souci Dauphiné | 1.067 | 1,554 | 840 | 453 | 0.541 | 787.2 | 0.898 |
| Guillotière | 1.316 | 1,743 | 934 | 636 | 0.536 | 709.6 | 0.879 |

At **IRIS** level (the unit `D-EU-10` names for France) the scale problem is decisive: the 160 Lyon
IRIS with ≥100 buildings hold **100–411 buildings each**, the largest residential count in any single
Lyon IRIS is **230**, and only 18 reach a 0.60 residential share. **One IRIS cannot carry `N1`.**
DR10's own Lyon proposal already used a *pair* of IRIS; measured, that pair
(`693840101` + `693840102`) is 0.358 km², 521 buildings, **169** OSM-residential.

### 2.5 DR10 estimates vs the project's own counts

| Unit | DR10 estimate (published statistics) | Measured here (OSM + OpenUBEM filter) | Note |
|---|---|---:|---|
| Madrid Gaztambide | 490–540 residential buildings | **516** | Inside DR10's range |
| Madrid Trafalgar | 580–640 | **502** | 37.7 % of its buildings are `building=yes` |
| Madrid Arapiles | 520–580 | **321** | 37.9 % unknown |
| Madrid Bellas Vistas | 850–950 (DR10: "exceeds `N1`") | **1,025** | Same direction, larger |
| Madrid Bellas Vistas area | 0.716 km² (Ayuntamiento) | **0.7165 km²** | Boundary independently confirmed |
| Lyon Croix-Rousse pair `693840101+02` | 0.460 km², 520–580 residential | **0.358 km², 521 buildings, 169 residential** | DR10's building figure ≈ the *total*, not the filtered residential count |
| Bologna "Bolognina 1 — Casaralta (AS_31)" | 0.520 km², 510–570 residential | **no such unit** in the official 90-area set | DR10's Bologna area codes do not resolve against `aree-statistiche` |

**Consequence:** DR10 candidate counts must not be quoted as project numbers — as the arc already
ruled. The reproducible counts are the ones in §1 and the CSVs.

### 2.6 Boundary-generalisation sensitivity (London)

Same ward, two ONS products: **BGC** (generalised, 23 vertices, 0.6814 km²) → 1,400 buildings /
1,269 residential; **BFC** (full resolution, 236 vertices, 0.6791 km²) → 1,372 / 1,241. A **2.2 %**
count difference from the boundary product alone. The packet therefore pins **BFC**, and any panel
built on BGC would not reconcile with it (`NS-07`).

---

## 3. Site acquisition packets

Field values are exactly as measured; nothing is implied. `boundary_geojson` is shipped as a retained
file rather than inlined (23–236 vertices each) — path and SHA-256 are given.

### 3.1 Madrid — SELECTED

```yaml
site_id: "ES-MAD-BELLASVISTAS"
country_stock: "ES"
city: "Madrid"
neighbourhood_name: "Bellas Vistas (barrio 061, distrito 06 Tetuan)"
decision: "SELECTED"
boundary_status: "VERIFIED"
crs_input: "EPSG:4326"
centroid_wgs84: [-3.707645, 40.452455]
bbox_wgs84: [-3.713328, 40.446854, -3.702912, 40.457621]           # [west, south, east, north]
bbox_openubem_order: [40.457621, 40.446854, -3.702912, -3.713328]  # (n, s, e, w) for ingest_buildings(bbox=...)
boundary_geojson: "docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/eu02_boundary_ES-MAD-BELLASVISTAS.geojson"
boundary_sha256: "e128443cacd8ae47ab24d69a1e7b76cc4872f795883accbd61e01ab1e762be8b"
boundary_geometry: "Polygon, 123 vertices, single part, 0.7165 km2 (Ayuntamiento publishes 0.716 km2)"
boundary_rationale: >
  Highest-ranked unit of the pre-registered pool that satisfies the residential-dominance gate and lies
  in the top decile by residential buildings per km2; whole official barrio, untrimmed.
contiguity_basis: "administrative"
footprint_source:
  provider: "OpenStreetMap contributors (Overpass API)"
  dataset_or_endpoint: "https://overpass-api.de/api/interpreter"
  licence_url: "https://www.openstreetmap.org/copyright"
  attribution_text: "(c) OpenStreetMap contributors, ODbL 1.0"
  access_date_utc: "2026-08-24T16:53:06Z"
  retrieval_method: "Overpass query"
  reproducible_request: "see section 4.1"
  stable_building_id_field: "osm_type + osm_id (way/relation)"
boundary_source:
  provider: "Ayuntamiento de Madrid (barrio set), retrieved as OSM relation 10668283 mirroring it"
  authoritative_download: "https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas (Barrios SHP/JSON)"
  licence_note: "Ayuntamiento de Madrid open data, attribution required; the OSM mirror is ODbL"
residential_filter:
  include_rules: ["building in {apartments,bungalow,detached,dormitory,house,residential,semidetached_house,terrace}"]
  exclude_rules: ["every other building value (commercial, industrial, institutional per openubem/data/osm_to_use_class.json)"]
  unknown_use_policy: "exclude and retain in audit"     # building=yes / empty = ambiguous_tokens
count_status: "MEASURED"
count_evidence: >
  1,506 buildings inside the boundary, of which 1,025 residential, 407 unknown-use, 74 non-residential.
  Independent bbox-only recount (section 4.1): 1,950 total / 1,319 residential inside the bounding box,
  which is larger than the barrio. Files: ../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_site_measurements.csv, ../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_madrid.csv.
candidate_density_evidence: >
  1,430.6 residential buildings/km2; rank 3 of the 28 pool units passing the dominance gate; the full
  44-unit ranking is retained. Floor-area proxy: residential footprint 226,274 m2, median footprint
  176.9 m2, building:levels present for 41.8 % of residential buildings (mean 4.27), proxy GFA on the
  covered subset 490,466 m2 = 684,547 m2/km2 (PARTIAL COVERAGE, not a full-stock figure).
four_panel_data_sources:
  construction_period: >
    Direccion General del Catastro INSPIRE Buildings, municipality file
    https://www.catastro.hacienda.gob.es/INSPIRE/Buildings/28/28900-MADRID/A.ES.SDGC.BU.28900.zip
    (ATOM feed https://www.catastro.hacienda.gob.es/INSPIRE/buildings/ES.SDGC.BU.atom.xml, twice-yearly).
    Rights text as published: free use provided the D.G. of the Cadastre is named as author and owner.
    OSM carries no usable date here: start_date coverage MEASURED at 0.0 % of the 1,025 residential buildings.
  energy_record_availability: >
    Comunidad de Madrid, Registro de certificados de eficiencia energetica de edificios, open CSV/ZIP,
    Creative Commons Attribution, monthly:
    https://datos.comunidad.madrid/catalogo/dataset/registro_certificados_eficiencia_energetica
    (field list NOT_MEASURED - must be read at acquisition before the panel is designed).
  typology_or_use: "Catastro currentUse + OSM building tag; TABULA SFH/TH/MFH/AB crosswalk per the EU-02 semantic layer."
  construction_material_or_set: "Assigned TABULA ES construction family by period x typology; no open observed per-building material source for Madrid (declare provenance separately per MVP 10.4)."
known_geometry_risks:
  - "building:levels missing for 58.2 % of residential buildings - storey count must come from Catastro numberOfFloorsAboveGround or the repo height cascade, not from OSM alone."
  - "407 unknown-use buildings (27.0 %) sit inside the boundary and are excluded from modelling; if Catastro shows them residential the site grows well beyond N2."
  - "Multipolygon buildings (relations) are included in the count and need the acquisition layer's overlap resolution."
count_stage: "OVER_N2_NEEDS_SUBUNIT (1,025 > 1,000)"
eu04_readiness: "BLOCKED"
blocking_items:
  - "N1 target: 1,025 residential exceeds the 500-600 band. Either run this site as an N2-scale study with owner approval, or switch to a measured N1-sized whole barrio (Chopera 502, Sol 501, Gaztambide 516, Delicias 509, Recoletos 529) - no trimming in either case."
  - "Catastro municipality extract not downloaded; construction period and storey counts are unavailable until it is."
  - "OpenUBEM has not yet run ingest_buildings on this bbox; no raw footprint manifest or checksum exists in the repository."
```

### 3.2 London — SELECTED

```yaml
site_id: "GB-LDN-STDUNSTANS"
country_stock: "GB_ENGLAND"
city: "London"
neighbourhood_name: "St Dunstan's ward (E05009329), London Borough of Tower Hamlets"
decision: "SELECTED"
boundary_status: "VERIFIED"
crs_input: "EPSG:4326"
centroid_wgs84: [-0.040004, 51.518428]
bbox_wgs84: [-0.050013, 51.512597, -0.033744, 51.524248]
bbox_openubem_order: [51.524248, 51.512597, -0.033744, -0.050013]
boundary_geojson: "docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/eu02_boundary_GB-LDN-STDUNSTANS.geojson"
boundary_sha256: "f5286cf28ff4cea079a87b68b9f0942e31542d2833e9ede1350830665e140bbc"
boundary_geometry: "Polygon, 236 vertices (ONS BFC full resolution), 0.6791 km2"
boundary_rationale: >
  Densest residential unit of the entire three-borough pool and the rule's selection; whole official
  ward, untrimmed. BFC (full resolution) is pinned over BGC because the two differ by 2.2 % of the count.
contiguity_basis: "administrative"
footprint_source:
  provider: "OpenStreetMap contributors (Overpass API)"
  dataset_or_endpoint: "https://overpass-api.de/api/interpreter"
  licence_url: "https://www.openstreetmap.org/copyright"
  attribution_text: "(c) OpenStreetMap contributors, ODbL 1.0"
  access_date_utc: "2026-08-24T16:53:06Z"
  retrieval_method: "Overpass query"
  reproducible_request: "see section 4.2"
  stable_building_id_field: "osm_type + osm_id"
boundary_source:
  provider: "Office for National Statistics, Open Geography Portal"
  dataset_or_endpoint: "Wards_December_2022_Boundaries_UK_BFC/FeatureServer/0/query?where=WD22CD='E05009329'&outSR=4326&f=geojson"
  licence_url: "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
  attribution_text: "Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data (c) Crown copyright and database right 2022."
residential_filter:
  include_rules: ["building in {apartments,bungalow,detached,dormitory,house,residential,semidetached_house,terrace}"]
  exclude_rules: ["every other building value"]
  unknown_use_policy: "exclude and retain in audit"
count_status: "MEASURED"
count_evidence: >
  1,372 buildings inside the BFC boundary: 1,241 residential, 78 unknown-use, 53 non-residential.
  Point-in-polygon on OSM centroids gives 1,375 / 1,242 - a 1-building difference from the footprint
  representative-point join; the representative-point join is the number of record. Independent
  bbox-only recount (section 4.2): 2,453 total / 2,072 residential over the larger bounding box.
candidate_density_evidence: >
  1,827.5 residential buildings/km2, highest of 58 wards. Residential footprint 141,285 m2, median
  48.7 m2 (small terraced houses), building:levels present for 90.8 % of residential buildings
  (mean 2.50 storeys), proxy GFA 411,958 m2 = 606,637 m2/km2 on 90.8 % coverage.
four_panel_data_sources:
  construction_period: >
    MHCLG Energy Performance of Buildings open data, field CONSTRUCTION_AGE_BAND (verified present in
    the official domestic data dictionary, 91 fields, downloaded 2026-08-24 from
    https://get-energy-performance-data.communities.gov.uk/guidance/data-dictionary). OGL v3.0.
    DR10's ruled caveat applies: 6 of 12 EPC age bands straddle TABULA GB periods and each straddled
    building must carry a PERIOD_STRADDLE_* token.
  energy_record_availability: >
    Same register - presence/absence of an EPC per UPRN is itself panel (b). Bulk download per local
    authority from https://get-energy-performance-data.communities.gov.uk/. OGL v3.0.
  typology_or_use: "EPC PROPERTY_TYPE + BUILT_FORM (both verified in the data dictionary) -> TABULA SFH/TH/MFH/AB."
  construction_material_or_set: "EPC WALLS_DESCRIPTION / WALLS_ENERGY_EFF (verified present) as observed material; the assigned TABULA GB construction family is recorded separately."
  join_route: "EPC UPRN -> OS Open UPRN coordinates -> point-in-footprint against the OSM polygon. Address text is never republished (PAF)."
known_geometry_risks:
  - "Median residential footprint is 48.7 m2: many rows are single terraced dwellings, so the dwelling-per-building assumption differs sharply from the Madrid/Lyon blocks."
  - "78 unknown-use buildings remain; small but must appear as an explicit excluded category."
  - "EPC is per dwelling, not per building: a building with several flats yields several certificates; the panel must state whether it maps any-EPC or all-dwellings-EPC."
count_stage: "OVER_N2_NEEDS_SUBUNIT (1,241 > 1,000)"
eu04_readiness: "BLOCKED"
blocking_items:
  - "N1 target: 1,241 residential exceeds the band. Either approve an N2+ study, or use a measured N1-sized whole ward (Homerton 557 with 98.9 % levels coverage, Brownswood 536), or drop to the ONS LSOA 2021 sub-units of this ward - all official, none trimmed."
  - "EPC extract for Tower Hamlets not downloaded; OS Open UPRN not downloaded."
  - "No raw footprint manifest exists in the repository for this bbox."
```

### 3.3 Bologna — NO_SELECTION

```yaml
site_id: "IT-BOL-PIAZZAUNITA"
country_stock: "IT"
city: "Bologna"
neighbourhood_name: "Piazza dell'Unita (area statistica 17, zona Bolognina, quartiere Navile) - PROVISIONAL LEAD ONLY"
decision: "NO_SELECTION"
boundary_status: "VERIFIED"
crs_input: "EPSG:4326"
centroid_wgs84: [11.348524, 44.508757]
bbox_wgs84: [11.340206, 44.504074, 11.356877, 44.512696]
bbox_openubem_order: [44.512696, 44.504074, 11.356877, 11.340206]
boundary_geojson: "docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/eu02_boundary_IT-BOL-PIAZZAUNITA.geojson"
boundary_sha256: "3116a8dbbcd3597e31f67087d47a4ef0c5ff7514aae1a6d667c01a1f5c5b32b1"
boundary_geometry: "Polygon, 83 vertices, 0.7756 km2"
boundary_rationale: >
  Not a rule output. The declared rule's mechanical output (LA BIRRA) is rejected as a tagging artefact;
  this unit is offered as the provisional lead because it is 8th of the 85 measured units on the city's
  own household density (7,656 families/km2, 2024) inside the dense Bolognina fabric.
contiguity_basis: "administrative"
footprint_source:
  provider: "OpenStreetMap contributors (Overpass API); municipal alternative below"
  dataset_or_endpoint: "https://overpass-api.de/api/interpreter"
  licence_url: "https://www.openstreetmap.org/copyright"
  attribution_text: "(c) OpenStreetMap contributors, ODbL 1.0"
  access_date_utc: "2026-08-24T16:53:06Z"
  retrieval_method: "Overpass query"
  reproducible_request: "see section 4.3"
  stable_building_id_field: "osm_type + osm_id"
  municipal_alternative: >
    Comune di Bologna, CARTA TECNICA COMUNALE - Edifici volumetrici (dataset c_a944ctc_edifici_pl,
    65,744 records, CC BY 4.0) carries footprint, eaves height quota_gron, ground height quota_pied,
    height above ground altezza_gr and volume - a direct storey-count source. Dataset rifter_edif_pl
    (Edifici particellari, 40,621 records) carries foglio/mappale cadastral keys for a Catasto join.
boundary_source:
  provider: "Comune di Bologna, portale open data"
  dataset_or_endpoint: "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/aree-statistiche/exports/geojson"
  licence_url: "https://creativecommons.org/licenses/by/4.0/"
  attribution_text: "Comune di Bologna, Aree statistiche, CC BY 4.0"
residential_filter:
  include_rules: ["building in {apartments,bungalow,detached,dormitory,house,residential,semidetached_house,terrace}"]
  exclude_rules: ["every other building value"]
  unknown_use_policy: "exclude and retain in audit"
count_status: "MEASURED"
count_evidence: >
  803 buildings inside the boundary: 177 residential, 526 unknown-use (65.5 %), 100 non-residential.
  Official dwelling proxy: 5,938 resident families in 2024 (Comune di Bologna open dataset) = 7,656/km2.
  The gap between 177 tagged residential buildings and 5,938 families is the reason for NO_SELECTION.
candidate_density_evidence: >
  228.2 OSM-residential buildings/km2 (rank 8 of 85 on families/km2, far lower on OSM tags).
  Residential footprint 63,752 m2, median 265.7 m2, building:levels present for 18.1 % (mean 4.91),
  proxy GFA 90,759 m2 = 117,015 m2/km2 on 18.1 % coverage - NOT usable as a stock figure.
four_panel_data_sources:
  construction_period: "ISTAT Basi territoriali e variabili censuarie (sezioni di censimento) - residential building and dwelling counts are published per section; construction epoch is a 2011-census variable, not 2021. Bologna rifter_edif_pl gives cadastral keys but no year. STATUS: no open per-building year for Bologna."
  energy_record_availability: "Regione Emilia-Romagna SACE / Visura APE (https://sace.regione.emilia-romagna.it) allows per-certificate verification by cadastral identifiers; the region states APE data will be progressively released as open data. No bulk open per-building APE file today. STATUS: aggregate only."
  typology_or_use: "OSM building tag (measured, 22 % coverage) + Catasto categoria via foglio/mappale. STATUS: insufficient on its own."
  construction_material_or_set: "Assigned TABULA IT construction family; no open observed-material source found."
known_geometry_risks:
  - "65.5 % of buildings inside the boundary are building=yes; excluding them removes most of the neighbourhood."
  - "OSM building:levels coverage 18.1 % - the municipal CTC height fields are the realistic storey source."
count_stage: "BELOW_N1 on OSM evidence (177); the true residential stock is far larger"
eu04_readiness: "BLOCKED"
blocking_items:
  - "No residential classifier: OSM tags identify only 22 % of this area's buildings. Re-run the identical rule with a non-OSM classifier (Catasto categoria via rifter_edif_pl foglio/mappale, or ISTAT sezione residential-building counts) before any site is accepted for Italy."
  - "No open per-building construction year; panel (a) cannot be built from an open Bologna source as things stand."
  - "DR10's Bologna candidate codes (AS_31 etc.) do not resolve against the official 90-area set and must not be used as identifiers."
```

### 3.4 Lyon — NO_SELECTION

```yaml
site_id: "FR-LYO-CROIXROUSSE"
country_stock: "FR"
city: "Lyon"
neighbourhood_name: "Quartier Croix-Rousse Est et Rhone (Lyon 4e/1er) - PROVISIONAL LEAD ONLY"
decision: "NO_SELECTION"
boundary_status: "VERIFIED"
crs_input: "EPSG:4326"
centroid_wgs84: [4.836958, 45.778074]
bbox_wgs84: [4.832215, 45.773478, 4.843032, 45.782711]
bbox_openubem_order: [45.782711, 45.773478, 4.843032, 4.832215]
boundary_geojson: "docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/eu02_boundary_FR-LYO-CROIXROUSSE.geojson"
boundary_sha256: "cbad7d8f206847e2d3aade256716d343ab54ae059092ff378ab4e2f4c5d43e66"
boundary_geometry: "MultiPolygon with a single part (contiguity confirmed), 80 vertices, 0.5911 km2"
boundary_rationale: >
  Not a rule output - no Lyon quartier passes the residential-dominance gate. It is the highest
  residential density of the 36 quartiers and the same fabric DR10 proposed (immeubles canuts).
contiguity_basis: "other declared boundary"   # Metropole de Lyon quartier layer, single part
footprint_source:
  provider: "OpenStreetMap contributors (Overpass API)"
  dataset_or_endpoint: "https://overpass-api.de/api/interpreter"
  licence_url: "https://www.openstreetmap.org/copyright"
  attribution_text: "(c) OpenStreetMap contributors, ODbL 1.0"
  access_date_utc: "2026-08-24T16:53:06Z"
  retrieval_method: "Overpass query"
  reproducible_request: "see section 4.4"
  stable_building_id_field: "osm_type + osm_id"
boundary_source:
  provider: "Metropole de Lyon (GeoServer WFS)"
  dataset_or_endpoint: "https://data.grandlyon.com/geoserver/metropole-de-lyon/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&typename=metropole-de-lyon:adr_voie_lieu.adrquartier&outputFormat=application/json&SRSNAME=EPSG:4326"
  licence_url: "NOT_VERIFIED - the portal page is client-rendered and its licence block was not retrievable headlessly"
  attribution_text: "Metropole de Lyon (licence to confirm before publication)"
  official_alternative: "IGN/INSEE CONTOURS-IRIS, Licence Ouverte 2.0, https://www.data.gouv.fr/datasets/contours-iris/ (direct file https://www.data.gouv.fr/api/1/datasets/r/23359ed9-9751-4db6-bd43-531aab221634, updated 2026-04-30)"
residential_filter:
  include_rules: ["building in {apartments,bungalow,detached,dormitory,house,residential,semidetached_house,terrace}"]
  exclude_rules: ["every other building value"]
  unknown_use_policy: "exclude and retain in audit"
count_status: "MEASURED"
count_evidence: >
  1,497 buildings inside the boundary: 659 residential, 795 unknown-use (53.1 %), 43 non-residential.
  City-wide context: 46,832 Lyon buildings, 28,619 of them building=yes (61.1 %).
candidate_density_evidence: >
  1,114.9 OSM-residential buildings/km2, highest of 36 quartiers. Residential footprint 115,474 m2,
  median 138.1 m2, building:levels present for 89.5 % (mean 4.45 storeys) - the best storey coverage
  of the four cities. Proxy GFA 496,443 m2 = 839,891 m2/km2, also the highest measured.
four_panel_data_sources:
  construction_period: "CSTB BDNB, field annee_construction, confirmed live on the open API (https://api.bdnb.io/v1/bdnb/donnees/batiment_groupe_complet). Licence Ouverte 2.0 (https://www.data.gouv.fr/datasets/base-de-donnees-nationale-des-batiments/, producer CSTB, downloads at https://bdnb.io/download/)."
  energy_record_availability: >
    (i) ADEME DPE open database per address; (ii) BDNB DPE linkage; (iii) Metropole de Lyon publishes
    MEASURED annual energy consumption per IRIS by carrier, operator, sector and delivery-point count
    (layer metropole-de-lyon:nrj_energie.nrjconsoannuiris_1, Enedis/GRDF, years from 2011) - a real
    aggregate validation target for this site, not only an availability flag.
  typology_or_use: "BDNB building usage fields; the OSM tag alone covers only 44 % here."
  construction_material_or_set: "BDNB construction attributes + the assigned TABULA FR construction family (D-EU-11 FR.N rows)."
known_geometry_risks:
  - "53.1 % of buildings in the boundary are building=yes: the French cadastre import rarely sets a use tag. Excluding them would delete most of the neighbourhood."
  - "Quartier is a Metropole layer, not an INSEE unit; the IRIS crosswalk must be built explicitly if the Enedis per-IRIS consumption is used."
count_stage: "N2-sized on OSM evidence (659); the true residential count is higher once BDNB classifies the unknowns"
eu04_readiness: "BLOCKED"
blocking_items:
  - "No residential classifier from OSM. Re-run the identical rule with BDNB usage as the classifier; only then can France be selected."
  - "IRIS - the unit named in D-EU-10 for France - cannot reach N1: the largest single Lyon IRIS holds 230 OSM-residential buildings. Either declare a fixed IRIS pair/triple in advance, or accept the quartier level."
  - "Metropole de Lyon boundary licence unverified; CONTOURS-IRIS (Licence Ouverte 2.0) is the fallback of record."
```

---

## 4. Reproducible query appendix

Endpoint `https://overpass-api.de/api/interpreter`, POST form field `data`. All queries were run
2026-08-24; the response header reported `timestamp_osm_base` 2026-08-24T15:58:31Z. Counts below are
**bounding-box** counts (the bbox is larger than the boundary); the site counts of §1/§3 are these
extracts clipped to the official polygon. Retained with results in
[`../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_reproducible_queries.json`](../../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_reproducible_queries.json).

Overpass terms: fair-use public instance, only a few concurrent slots; heavy repeats should use a
private instance or a Geofabrik extract. Two of the twelve bulk extracts were rate-limited (HTTP 429)
and two timed out (HTTP 504) on first attempt and were re-run.

### 4.1 `ES-MAD-BELLASVISTAS` → bbox total **1,950**, bbox residential **1,319**

```
[out:json][timeout:180];(way["building"](40.446854,-3.713328,40.457621,-3.702912);
relation["building"](40.446854,-3.713328,40.457621,-3.702912););out count;
```
```
[out:json][timeout:180];(way["building"~"^(apartments|bungalow|detached|dormitory|house|residential|semidetached_house|terrace)$"](40.446854,-3.713328,40.457621,-3.702912);
relation["building"~"^(apartments|bungalow|detached|dormitory|house|residential|semidetached_house|terrace)$"](40.446854,-3.713328,40.457621,-3.702912););out count;
```

### 4.2 `GB-LDN-STDUNSTANS` → bbox total **2,453**, bbox residential **2,072**

The same two queries with the bbox `(51.512597,-0.050013,51.524248,-0.033758)`.

### 4.3 `IT-BOL-PIAZZAUNITA` → bbox total **1,215**, bbox residential **203**

The same two queries with the bbox `(44.504074,11.340206,44.512696,11.356877)`.

### 4.4 `FR-LYO-CROIXROUSSE` → bbox total **1,865**, bbox residential **815**

The same two queries with the bbox `(45.773478,4.832215,45.782711,4.843032)`.

### 4.5 Full extract for a site (what EU-04 should run)

```python
from openubem.acquisition.osm_fetcher import ingest_buildings
gdf = ingest_buildings(bbox=(40.457621, 40.446854, -3.702912, -3.713328),  # (n, s, e, w)
                       tags={"building": True},
                       output_dir=Path("openubem/outputs/eu02/ES-MAD-BELLASVISTAS"))
```

`ingest_buildings` dispatches to `osmnx.features.features_from_bbox`, whose tuple order in the pinned
osmnx 1.9.3 is **(north, south, east, west)** — not the GeoJSON `[W,S,E,N]` order used in §3. Clip the
result to the retained boundary polygon, then apply the residential filter.

### 4.6 Non-OSM sources verified live on 2026-08-24

| Purpose | Endpoint verified | Result |
|---|---|---|
| Madrid boundaries | `datos.madrid.es/dataset/900012-0-limites-administrativos-mapas` | HTTP 200; barrios + secciones censales + distritos published |
| Madrid footprints/period | `catastro.hacienda.gob.es/INSPIRE/Buildings/28/28900-MADRID/A.ES.SDGC.BU.28900.zip` | present in the province-28 ATOM feed with its rights statement |
| Madrid EPC | `datos.comunidad.madrid/catalogo/dataset/registro_certificados_eficiencia_energetica` | CC-BY, monthly, CSV/ZIP per year |
| London boundaries | ONS `Wards_December_2022_Boundaries_UK_BFC` and `..._BGC` FeatureServer | 58 wards for the 3 boroughs; BFC ward retrieved |
| London EPC fields | `get-energy-performance-data.communities.gov.uk/download/data-dictionary?property_type=domestic` | 91 fields; `CONSTRUCTION_AGE_BAND`, `WALLS_DESCRIPTION`, `PROPERTY_TYPE`, `BUILT_FORM`, `TOTAL_FLOOR_AREA`, `FLOOR_HEIGHT`, `UPRN`, `POSTCODE` all present |
| Bologna boundaries | `opendata.comune.bologna.it/.../aree-statistiche/exports/geojson` | 90 polygons, CC BY 4.0 |
| Bologna buildings/heights | dataset `c_a944ctc_edifici_pl` | 65,744 records with `quota_gron`, `quota_pied`, `altezza_gr`, `volume` |
| Bologna dwelling proxy | dataset `famiglie-residenti-...-area-statistica-...` | families by area statistica, 2024 |
| Lyon boundaries | Grand Lyon WFS `adr_voie_lieu.adrquartier`, `ter_territoire.teriris_latest` | 201 quartiers (36 in Lyon), 512 IRIS (185 in Lyon) |
| Lyon energy | Grand Lyon WFS `nrj_energie.nrjconsoannuiris_1` | per-IRIS annual consumption by carrier/sector with delivery-point counts |
| France buildings | `api.bdnb.io/v1/bdnb/donnees/batiment_groupe_complet` | live, returns `annee_construction` per building group |
| France IRIS fallback | `data.gouv.fr/datasets/contours-iris/` | IGN + INSEE, Licence Ouverte 2.0, updated 2026-04-30 |

---

## 5. `NS-01`–`NS-10` compliance matrix

`PASS` = retained reproducible evidence exists now. `PARTIAL` = evidence exists but the repository step
has not been run. `NOT_MET` = the gate's condition is not satisfied. `NOT_MEASURED` = not attempted.

| Gate | `ES-MAD-BELLASVISTAS` | `GB-LDN-STDUNSTANS` | `IT-BOL-PIAZZAUNITA` | `FR-LYO-CROIXROUSSE` |
|---|---|---|---|---|
| `NS-01` contiguous boundary | **PASS** — official barrio, 1 part, 123 vertices, SHA-256 retained | **PASS** — ONS BFC ward, SHA-256 retained | **PASS** — Comune area statistica, SHA-256 retained | **PASS** — quartier, MultiPolygon with 1 part (contiguity checked), SHA-256 retained |
| `NS-02` supported input mode + raw manifest | **PARTIAL** — bbox mode + exact query retained; `ingest_buildings` not yet run, no repo manifest | **PARTIAL** — same | **PARTIAL** — same | **PARTIAL** — same |
| `NS-03` rank by res/km² + dwelling or floor-area proxy | **PASS** — 44 units ranked; floor-area proxy measured (41.8 % levels coverage, stated) | **PASS** — 58 units ranked; proxy on 90.8 % coverage | **PASS** — 90 units ranked + official families/km² for all 85 | **PASS** — 36 quartiers + 185 IRIS ranked; proxy on 89.5 % coverage |
| `NS-04` dense residential-dominant, rejections documented | **PASS** — 0.681 share, full ranking retained | **PASS** — 0.905 share, full ranking retained | **NOT_MET** — 0.220 share; the rule's own output is a tagging artefact | **NOT_MET** — 0.440 share; no quartier reaches 0.60 |
| `NS-05` 500–600 residential for `N1` | **NOT_MET** — 1,025 measured; `N1`-sized alternates measured | **NOT_MET** — 1,241 measured; `N1`-sized alternates measured | **NOT_MET** — 177 on OSM evidence | **NOT_MET** — 659 on OSM evidence, and no single IRIS can reach the band |
| `NS-06` no trimming | **PASS** — whole official unit; checksum retained | **PASS** | **PASS** | **PASS** |
| `NS-07` identical boundary + IDs in all four panels | **NOT_MEASURED** — only panel (c) exists (Figure EU-02.1), drawn from the retained boundary and building-ID set; the equality assertion needs all four panels | **NOT_MEASURED** — same | **NOT_MEASURED** — same | **NOT_MEASURED** — same |
| `NS-08` non-residential/unknown as excluded context | **PARTIAL** — 407 unknown + 74 non-res identified per building; no exclusion manifest emitted by the repo | **PARTIAL** — 78 + 53 | **PARTIAL** — 526 + 100 | **PARTIAL** — 795 + 43 |
| `NS-09` four audit dimensions sourced | **PARTIAL** — (a) Catastro, (b) CM EPC registry, (c) Catastro+OSM, (d) TABULA assignment only; none joined. OSM `start_date` coverage measured at 0.0 % | **PARTIAL** — (a)(b)(c)(d) all resolvable from EPC fields verified in the data dictionary; not joined | **NOT_MET** — no open per-building year, no bulk open APE | **PARTIAL** — BDNB supplies (a)(c)(d), ADEME/BDNB (b); not joined |
| `NS-10` sites kept separate | **PASS** — per-site id, boundary file, building table; no cross-site aggregation | **PASS** | **PASS** | **PASS** |

---

## 6. Handoff and limitations

### What an OpenUBEM implementation agent can do immediately

1. Run `ingest_buildings(bbox=...)` for `ES-MAD-BELLASVISTAS` and `GB-LDN-STDUNSTANS` with the tuples
   in §3 (repo order `(n, s, e, w)`), clip to the retained boundary GeoJSON, and write the first real
   European raw footprint manifest with source, query, date, licence, CRS and checksum.
2. Apply the residential filter already in the repo (`openubem/data/osm_to_use_class.json`) and emit
   the excluded-building manifest required by `NS-08`; the expected counts are in §3 and must reconcile
   exactly (Madrid 1,025 / 407 / 74; London 1,241 / 78 / 53) up to OSM edits after 2026-08-24.
3. Download the Catastro Madrid municipality file and the Tower Hamlets EPC extract, and build panels
   (a), (b), (c), (d) for those two sites only.
4. Treat the Grand Lyon per-IRIS measured consumption series as a **future validation target** for the
   French site, not as an input.

### What is explicitly not done

| Claim | Status |
|---|---|
| Candidate selected from public evidence | **YES** for Madrid and London; refused for Bologna and Lyon |
| Raw building footprints acquired and checksummed into the repository | **NO** — the boundaries are checksummed; the footprints are not in the repo |
| Residential filter actually run inside OpenUBEM | **NO** — the identical rule was applied out-of-repo on the same crosswalk file |
| Geometry / IDF / simulation evidence | **NO** — nothing was generated for any site |

### Findings that change the plan

1. **At the officially published neighbourhood scale, `N1` is systematically too small.** Every
   top-decile unit in Madrid (1,025–1,194) and London (1,269–1,852) exceeds the 500–600 band. `N1`
   must either be met by a *different whole official unit* — measured and available: Madrid Chopera 502
   / Sol 501 / Gaztambide 516 / Delicias 509 / Recoletos 529, London Homerton 557 / Brownswood 536 —
   or the band must be re-ruled toward `N2`. Trimming is not an option (`NS-06`).
2. **The OSM tag is a sufficient residential classifier in two of four countries only.** Measured
   unknown (`building=yes`) share: Madrid 1.5 % (Embajadores) to 27 % (the selected barrio); London
   median ward 0.212 in Tower Hamlets, 0.472 in Hackney, 0.505 in Islington, and 5.6 % inside the
   selected ward; Bologna 65.5 % at the provisional site; Lyon 53.1 % at the provisional site and
   61.1 % city-wide. Italy and France need a non-OSM classifier — Catasto/ISTAT and BDNB respectively —
   before any site can pass `NS-04`. This is the single largest blocker in this document.
3. **Density ranking on OSM tags partly measures mapping completeness.** Islington's Barnsbury ward
   sits 43rd of 58 (369 residential/km²) with 83.8 % unknown, which is a mapping artefact rather than
   low density. The dominance gate contains the damage but does not remove it; the EPC/Catastro/BDNB
   join is what fixes it.
4. **The boundary product matters.** ONS BGC vs BFC changed the London count by 2.2 %. Every panel must
   use the pinned BFC file, not a re-download of a different generalisation.
5. **DR10's candidate counts do not reproduce** (§2.5), exactly as the arc anticipated; its *dataset*
   pins were all independently confirmed live, and one identifier set (Bologna `AS_*`) is unusable.
6. **France's ruled unit cannot carry the sample.** No single Lyon IRIS exceeds 230 residential
   buildings. A declared IRIS pair or the quartier level must be ruled before France proceeds.

### Blocking items, by owner

- **Campaign owner:** rule on `N1` at 500–600 vs `N2` scale for Madrid/London; rule on the French unit
  (IRIS pair vs quartier); approve the Bologna/Italy re-run condition.
- **Implementation:** acquire Catastro (ES) and EPC + OS Open UPRN (GB); re-run the identical
  pre-registered rule for Bologna with a Catasto/ISTAT classifier and for Lyon with BDNB; confirm the
  Métropole de Lyon boundary licence or switch to CONTOURS-IRIS.
