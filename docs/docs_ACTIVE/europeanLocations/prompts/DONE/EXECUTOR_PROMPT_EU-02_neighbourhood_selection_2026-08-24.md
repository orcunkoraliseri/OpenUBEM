# Executor prompt - EU-02 neighbourhood selection for EU-04 inputs

Copy everything below this line into the research-capable LLM. Ask it to return the completed handoff packet in its response; do not ask it to modify this repository.

---

You are selecting observed building-footprint study locations for the OpenUBEM European-locations project. Work carefully from sources and return a decision-ready handoff packet for another implementation agent. You may browse the web and use public-data APIs, but do **not** submit simulations, run a cluster job, or claim an unmeasured result.

## Fixed scope

Select **one real contiguous dense-residential neighbourhood in each city**:

| Country / stock | Fixed city | Scope note |
|---|---|---|
| Spain (`ES`) | Madrid | Current physical and occupant-enabled scope |
| England-limited `GB` | London | Do not generalize the `GB` TABULA stock to Scotland, Wales, or Northern Ireland |
| Italy (`IT`) | Bologna | Current physical and occupant-enabled scope |
| France (`FR`) | Lyon | Physical and controlled-baseline scope only; French occupant schedules are out of scope |

The city choices above are already ruled. Your task is to select a reproducible **neighbourhood boundary within each city**, not to choose replacement cities.

## Objective

For each city, select one defensible candidate suitable for OpenUBEM's observed-building work:

- `S1`: observed residential buildings with simple and difficult footprints;
- `S2` / `S3`: a reproducible pool that can be stratified by typology and age/data completeness;
- later `N1`: ideally 500-600 **post-filter residential buildings** inside one contiguous declared boundary.

The boundary must be a natural or declared contiguous urban area. Never assemble disconnected buildings from across a city just to meet a count. If the credible initial candidate does not yet have a measured post-filter count, say so explicitly; do not fabricate one.

## OpenUBEM constraints

OpenUBEM can acquire building populations through an address, coordinate, bounding box, or pre-downloaded OSM XML extract. The selected packet must therefore be implementable using a stable geographic boundary and an open, reproducible footprint source.

Only residential buildings may enter geometry, IDF, or simulation manifests. Preserve non-residential and unresolved-use footprints in the source audit with explicit exclusion reasons. The eventual implementation must record stable building IDs, source query, query date, licence/attribution, CRS, raw data checksum, residential filter, and exclusions.

The relevant selection gates are:

- `NS-01`: one real contiguous boundary per city;
- `NS-02`: address, coordinate, bounding box, or OSM XML acquisition input and raw footprint manifest;
- `NS-03`: rank candidates by residential buildings/km2 plus a residential-floor-area or dwelling proxy;
- `NS-04`: select a dense residential-dominant area and document rejected candidates;
- `NS-05`: target 500-600 post-filter residential buildings for `N1`;
- `NS-06`: do not trim boundaries to force a count;
- `NS-07`: every later audit panel uses the same boundary and building-ID set;
- `NS-08`: non-residential/unknown context is excluded from modelling but visible in the audit;
- `NS-09`: identify sources for age/period, energy-record availability, typology/use, and construction material/set;
- `NS-10`: keep each city/site separate until independently accepted.

## Required method

1. Inspect authoritative local/open portals and OpenStreetMap availability for each fixed city. Prefer primary sources for licences and datasets.
2. Compare at least three plausible contiguous candidate neighbourhoods per city. If a city has fewer than three viable candidates, explain why.
3. Apply a pre-declared, identical selection method within each city: residential-density evidence first, then footprint completeness, stable identifiers, source licence, and availability of the four audit dimensions. Do not tune a density cutoff after seeing a preferred candidate.
4. Select one candidate per city, or return `NO_SELECTION` for that city if the evidence is insufficient. A transparent `NO_SELECTION` is preferable to an invented site.
5. Use geographic coordinates in WGS84 (`EPSG:4326`) and provide a boundary as both a bounding box and a closed GeoJSON polygon. If you cannot verify a polygon, give only a clearly labelled provisional bounding box and mark `BOUNDARY_STATUS: PROVISIONAL`.
6. For every numerical building count or density, state exactly whether it is `MEASURED`, `SOURCE_REPORTED`, or `NOT_MEASURED`. A count is `MEASURED` only if you provide the query/API request, date, filter, and raw-result reference sufficient to reproduce it. Do not treat OSM building count as residential count without a documented residential classification filter.
7. Do not download, transform, or silently clean data on the project’s behalf. Recommend a reproducible query/extract and leave the actual acquisition to the implementation agent.

## Deliverable format

Return one Markdown report, in English, with these sections in this exact order.

### 1. Executive decision table

One row for Madrid, London, Bologna, and Lyon with:

- `site_id` (stable slug, for example `ES-MAD-...`)
- selected neighbourhood name
- decision: `SELECTED` or `NO_SELECTION`
- boundary status: `VERIFIED` or `PROVISIONAL`
- WGS84 centroid and bounding box
- footprint source and licence status
- residential-count status (`MEASURED` / `SOURCE_REPORTED` / `NOT_MEASURED`)
- concise reason for the decision

### 2. Candidate comparison, one table per city

Include all examined candidates, source links, contiguity rationale, density evidence, residential-use evidence, footprint availability, data gaps, rejection reason, and a clear rank. Keep measurement status beside every number.

### 3. Selected-site acquisition packet, one subsection per selected site

Provide the following exact fields in fenced YAML. Do not leave a field silently implied.

```yaml
site_id: ""
country_stock: "ES | GB_ENGLAND | IT | FR"
city: ""
neighbourhood_name: ""
decision: "SELECTED"
boundary_status: "VERIFIED | PROVISIONAL"
crs_input: "EPSG:4326"
centroid_wgs84: [longitude, latitude]
bbox_wgs84: [west, south, east, north]
boundary_geojson: {"type": "Polygon", "coordinates": []}
boundary_rationale: ""
contiguity_basis: "administrative | named neighbourhood | other declared boundary"
footprint_source:
  provider: ""
  dataset_or_endpoint: ""
  licence_url: ""
  attribution_text: ""
  access_date_utc: ""
  retrieval_method: "Overpass query | official API | download URL | other"
  reproducible_request: ""
  stable_building_id_field: ""
residential_filter:
  include_rules: []
  exclude_rules: []
  unknown_use_policy: "exclude and retain in audit"
count_status: "MEASURED | SOURCE_REPORTED | NOT_MEASURED"
count_evidence: ""
candidate_density_evidence: ""
four_panel_data_sources:
  construction_period: ""
  energy_record_availability: ""
  typology_or_use: ""
  construction_material_or_set: ""
known_geometry_risks: []
eu04_readiness: "READY_FOR_ACQUISITION | BLOCKED"
blocking_items: []
```

### 4. Reproducible query/extract appendix

For each selected site, provide the complete Overpass QL query or official API request, including the exact boundary. Do not use a place-name-only query that could change later. State any rate-limit or terms-of-use constraints.

### 5. NS-01 through NS-10 compliance matrix

For every site and every gate, give `PASS`, `PARTIAL`, `NOT_MET`, or `NOT_MEASURED`, with a one-sentence evidence note. `PASS` requires retained/reproducible evidence; a narrative plan is only `PARTIAL`.

### 6. Handoff and limitations

State exactly what the OpenUBEM implementation agent can do immediately, the files it must acquire next, and the blockers that prevent EU-04 from processing real footprints. Explicitly distinguish:

- a candidate selected from public evidence;
- raw building footprints actually acquired and checksummed;
- a residential filter actually run;
- geometry/IDF/simulation evidence.

## Non-negotiable accuracy rules

- Cite primary sources with direct links next to the claims they support.
- Do not claim a site is ready merely because it appears residential on a map.
- Do not call a count “residential” unless the filter has been described and reproduced.
- Do not invent cadastral, EPC, material, height, storey, or licence coverage.
- Do not alter the four fixed cities or the scope distinction for France.
- Return a useful partial packet even when external data access is unavailable.

---

End of executor prompt.
