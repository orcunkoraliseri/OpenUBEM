# PLAN — `GB` EPC year-coverage probe (London, `GB-LDN-STDUNSTANS`)

**Slug:** `gb-epc-coverage-probe` · **Date:** 2026-08-27 · **Author:** manager session
**Authority:** `D-EU-22` (Option F1 — *live retrieval authorised for a coverage probe*), ruled 2026-08-27.
**Spec pointers:** `MVP_european_locations.md:1218`, `:1240` (`D-EU-10` — the GB attribute sources are
**MHCLG EPC + OS Open UPRN**), `:701` (arc status; `EU-04` is OpenUBEM-side and open).
**Prior record this plan closes:** `openubem/outputs/eu_evidence/EU-04/es_gb_it_attribute_coverage_probe.json`
→ `GB-LDN-STDUNSTANS.verdict = "CREDENTIAL_BLOCKED — join surface MEASURED and intact (98.15 percent),
year data withheld behind GOV.UK One Login"`. The credential arrived **2026-08-27**. This plan spends it.

**What this plan is NOT.** It is a **measurement**. It forms no sample, runs no EnergyPlus, promotes
nothing, reopens neither `D-EU-23` nor `D-EU-24`, and moves no hash. `S3` stays **FR + ES**.

---

## 1. Hard rules for the executor

1. **The bearer token is read from the environment variable `EPC_BEARER_TOKEN` and from nowhere else.**
   Never hard-code it, never write it to any file, log line, JSON, CSV, docstring or progress-log entry,
   never print it (print `len(token)` if you must prove it is set). If the variable is unset, **stop**.
2. **`openubem/outputs/eu02/` is opened read-only.** No file under it is written, moved or renamed.
3. **No promoted artefact is touched** — nothing under `EU-04/s2_campaign/`, `EU-04/s3/`,
   `EU-05/`, `EU-06/`, and no `*_manifest.csv` that carries an `idf_sha256`.
4. **No simulation, no sample formation, no layout run, no IDF written.**
5. **No commits.** Git is handled externally.
6. **Live network is authorised for this plan only**, and only against the two hosts pinned in §3.
   No other host is contacted.
7. **Every error you solve is registered** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
   before the task is called done — one bullet, house format, exact error string quoted.
   The EPC host/auth trap is **already registered** (bullet immediately before chapter 8); extend it
   rather than duplicating it.
8. **Stop at the checkpoints in §6.** Do not run ahead of them.
9. If the DESIGN or this plan is ambiguous, **STOP and quote the conflict.** Do not invent.

---

## 2. File layout

Everything this plan writes lives under `openubem/outputs/eu_evidence/EU-04/D-EU-22/` (the folder the
earlier coverage probes already use), including the script:

| path | what |
|---|---|
| `EU-04/D-EU-22/probe_gb_epc_coverage.py` | the probe (new; single file) |
| `EU-04/D-EU-22/_cache/` | **gitignored already** — OS Open UPRN zip and the raw API response cache |
| `EU-04/D-EU-22/gb_uprn_join.csv` | one row per EU-02 footprint × UPRN (T02) |
| `EU-04/D-EU-22/gb_epc_certificates.csv` | one row per certificate retrieved (T03/T04) |
| `EU-04/D-EU-22/gb_epc_coverage_probe.json` | the counts, the reasons, the verdict (T05) |

No file is written anywhere else. `es_gb_it_attribute_coverage_probe.json` is **not edited** — it is a
dated record of what was true before the credential existed; T05 supersedes it by adding a new file.

---

## 3. Dependency decisions — pinned, do not re-derive

1. **Base URL is `https://api.get-energy-performance-data.communities.gov.uk`** — note the `api.`
   prefix. The website host (`get-energy-performance-data.communities.gov.uk`, no prefix) answers
   **404 with an HTML body** to every `/api/...` path. The retired `epc.opendatacommunities.org`
   answers **200 with HTML**, so a naive liveness check reads it as alive. Both are traps.
2. **Auth is `Authorization: Bearer <token>`** — not the old HTTP Basic `base64(email:apikey)`.
3. **Endpoints** (verified live 2026-08-27):
   - `GET /api/domestic/search` — params `postcode`, `uprn` (12 digits, **left-padded with zeroes**),
     `address`, `council[]`, `constituency[]`, `date_start`, `date_end`, `current_page`, `page_size`.
     Paginates above 5,000 results.
   - `GET /api/certificate?certificate_number=<20-digit>` — the **full** record.
4. **The search response is a SUMMARY only.** Measured fields: `uprn`, `certificateNumber`,
   `addressLine1..4`, `postTown`, `postcode`, `council`, `constituency`, `registrationDate`,
   `currentEnergyEfficiencyBand`, `schemaType`. There is **no age band, no property type and no floor
   area** in it. **Every year answer costs a second call.** Budget two calls per certificate.
5. **`registrationDate` is the certificate's lodgement date, NEVER the construction year.**
   Reading it as a build year is the single most likely way to get a plausible wrong answer here.
6. **OS Open UPRN carries no construction year** — it is identity + coordinates, the join key only
   (`es_gb_it_attribute_coverage_probe.json → os_open_uprn.role`). Endpoint
   `https://api.os.uk/downloads/v1/products/OpenUPRN/downloads?area=GB&format=CSV&redirect`,
   ~618 MB zip, no credential. It is **not cached on disk** — `_cache/` currently holds only the
   ISTAT archive — so T02 re-downloads it once into `_cache/`.
7. **Join CRS is EPSG:27700.** The EU-02 manifest is EPSG:32630 and must be reprojected, not assumed.
8. **EPC covers England and Wales only.** London is in scope; this is recorded so nobody widens it.
9. **Requests carry a non-default `User-Agent`** (`OpenUBEM/1.0`). Rate limits are **unmeasured** —
   T01 measures them before anything is fanned out.

---

## 4. Facts measured on disk, with citations — verify, do not re-derive

| fact | value | source |
|---|---|---|
| London EU-02 footprints | **1,242** | `openubem/outputs/eu02/GB-LDN-STDUNSTANS/02_residential_manifest.gpkg` |
| footprints carrying a postcode | **1,176** (94.69 %) | `es_gb_it_attribute_coverage_probe.json → join_surface_measured_from_disk` |
| footprints containing ≥1 UPRN | **1,219** (98.15 %) | same, `uprn_join.footprints_containing_at_least_one_uprn` |
| with a 1 m buffer | **1,231** (99.11 %) | same |
| UPRNs falling inside a footprint | **6,838** | same |
| UPRNs in the padded study bbox | **16,151** | same |
| manifest columns | there is **no `uprn` column** — the join is computed, never read | `02_residential_manifest.gpkg` |
| GB year completeness | **`None` — UNMEASURED, not zero** | same JSON, `year_completeness_pct` |

🔴 **`1,219` is the number T02 must reproduce.** If the rebuilt join returns anything else, that is a
finding, and T02 stops rather than proceeding on a different denominator.

---

## 5. Task list

### T01 — Credential smoke test and rate-limit measurement

**What.** Confirm the token authenticates, and measure how fast the API may be called.
**Why.** T03/T04 are thousands of calls. Fanning them out against an unmeasured rate limit is how a
credential gets throttled or revoked on its first day.
**How.**
- Read `EPC_BEARER_TOKEN` from the environment; if unset, stop with a one-line message.
- Three calls: `?postcode=SW1A%201AA` (expect the JSON 404 below), `?postcode=E1%206AN` (expect 200,
  3 rows), and `/api/certificate` for one `certificateNumber` taken from the second.
- Then **20 sequential calls** with no delay, recording per-call HTTP status, elapsed ms and any
  `Retry-After` / `X-RateLimit-*` response headers. **Stop immediately on the first `429`.**
- Record the observed safe interval and use it in T03/T04. If nothing throttles in 20 calls, pin a
  conservative **5 requests/second** anyway and say so.

**How to test.** Expected, verified 2026-08-27:
`SW1A 1AA` → `404 {"data":{"error":"No certificates could be found for that query"}}` — a **JSON**
404 proves the token was accepted; an **HTML** 404 means the wrong host (§3.1).
`E1 6AN` → `200`, `data` list of 3, first row `uprn = 200000074842`.

### T02 — Rebuild the UPRN → footprint join and reproduce 1,219

**What.** Produce `gb_uprn_join.csv` — one row per (footprint, UPRN) pair.
**Why.** The join exists only as a number in a JSON; the pairs themselves were never persisted, and
T03 needs the actual UPRNs.
**How.**
- Download the OS Open UPRN CSV zip into `_cache/` (skip if present and its MD5 matches
  `2f023512afc378cd7b9351b24ccf1a34`). Stream-parse the member; do **not** load 41.6 M rows into memory.
- Filter to the study bbox padded by `0.0005°` (expect **16,151** rows — a stated regression check).
- Reproject both sides to **EPSG:27700**; spatial join UPRN points within footprint polygons.
- Columns: `osm_id`, `uprn` (as **string**, zero-padded to 12), `postcode` (from the manifest),
  `within` (`strict` | `buffer_1m`), `footprint_area_m2`.
- Never coerce `uprn` to an integer anywhere — leading zeroes are load-bearing for the API.

**How to test.** `strict` distinct `osm_id` = **1,219**; with the 1 m buffer = **1,231**; total strict
pairs = **6,838**. All three must match §4 exactly. Any mismatch → **stop and report**; do not proceed.

### T03 — Search EPC by UPRN

**What.** For every UPRN in the strict join, call `/api/domestic/search?uprn=<12-digit>`; write
`gb_epc_certificates.csv` with the summary rows.
**Why.** This is the certificate inventory, and the first honest measurement of how much of a London
residential block actually holds an EPC.
**How.**
- Sequential, at the T01-measured rate. Retry `429`/`5xx` up to 3× with exponential backoff; log the
  **actual response body**, never a label.
- A `404` with `"No certificates could be found for that query"` is a **valid measured negative**, not
  an error — record it as `certificates = 0` and continue.
- Columns: `osm_id`, `uprn`, `certificateNumber`, `registrationDate`, `currentEnergyEfficiencyBand`,
  `postcode`, `schemaType`, `http_status`.
- Cache each raw response under `_cache/` keyed by UPRN so a rerun costs no calls.

**How to test.** Row count ≥ the number of UPRNs with ≥1 certificate; every `certificateNumber` matches
`\d{4}-\d{4}-\d{4}-\d{4}-\d{4}`; no field in any row contains the token.

### T04 — Fetch the full certificate for the age band

**What.** For each distinct `certificateNumber`, call `/api/certificate` and extract construction age
band, property type, built form and total floor area into the same CSV (new columns).
**Why.** §3.4 — the year is not in the search response. Without T04 there is no year answer at all.
**How.**
- Same rate and retry policy. Cache by certificate number under `_cache/`.
- The JSON keys **vary by schema version** (`schemaType`), and the documentation says so. Do **not**
  hard-code one key path: search the `data` block case-insensitively for keys matching
  `construction.?age.?band`, `property.?type`, `built.?form`, `total.?floor.?area`, and record the
  **key actually found** in a `year_key_used` column.
- If a UPRN has more than one certificate, keep them all; take the **latest `registrationDate`** as
  the representative in T05, and say so in the JSON.

**How to test.** At least one row's age band is a **band string** (e.g. `England and Wales: 1900-1929`),
not a number. If any row yields a bare 4-digit integer, stop and report — that is a different field.

### T05 — Coverage summary and verdict

**What.** Write `gb_epc_coverage_probe.json` in the shape of the existing probes, and state the verdict.
**Why.** `D-EU-22`'s GB verdict is `CREDENTIAL_BLOCKED` with `year_completeness_pct = None`. This
replaces `None` with a measured number — or with a measured reason it is still not obtainable.
**How.** Record, at minimum:
- `footprints_in_eu02_manifest` = 1242, `footprints_with_uprn` = 1219,
- `footprints_with_at_least_one_certificate`, `footprints_with_an_observed_age_band`,
- `age_band_pct_of_1242` **and** `age_band_pct_of_1219` — both denominators printed, never one alone,
- the **band histogram**, `api_calls_made`, `seconds`, `retries`, `http_error_counts`,
- `two_signal_shape`: footprints carrying an age band **and** a dwelling count — and if the EPC record
  carries no dwelling count, record that as a measured absence.

🔴 **Three wording constraints, to be written into the JSON itself:**
1. **The result is an age BAND, not a year.** Any downstream use must state the band. The ES/FR
   sidecars carry observed **years**; GB will not, and the two are not interchangeable.
2. **EPC coverage is CERTIFICATE coverage, not a building-stock census.** A dwelling holds an EPC only
   if it was sold, let or newly built since 2008. Catastro and BD TOPO enumerate the stock; EPC
   enumerates transactions. A GB percentage placed beside the ES **98.74 %** without that sentence is
   a category error — it will read as a coverage gap when it is a data-generating-process difference.
3. `registrationDate` is never a construction year (§3.5).

**How to test.** Every percentage in the file is reproducible from two integers also in the file.

---

## 6. Stop-and-report points

- **CP-1 — after T01.** Report: token accepted (yes/no), the three expected responses, the measured
  rate limit and the interval chosen. **Do not start T02 before this is signed.**
- **CP-2 — after T02.** Report the three regression numbers (1,219 / 1,231 / 6,838). A mismatch is a
  finding; stop on it.
- **CP-3 — after T04.** Report calls made, wall-clock, error counts, and how many footprints got an
  age band — **before** writing any verdict.

---

## 7. Progress log

*(Executor appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD`, then
Artifacts / Deviations / Test status / Notes.)*

#### T01 — Credential smoke test and rate-limit measurement — completed 2026-08-27

Artifacts: `openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_gb_epc_coverage.py` (`task_t01`).
Deviations: none.
Test status: PASS — matched §5/T01 exactly. `SW1A 1AA` -> `404` JSON `{"data":{"error":"No
certificates could be found for that query"}}`; `E1 6AN` -> `200`, 3 rows, first `uprn=200000074842`;
`/api/certificate` for that row's `certificateNumber` -> `200`. 20 sequential calls, no delay: all
`200`, elapsed 3-23 ms, no `429`, no `Retry-After`/`X-RateLimit-*` headers observed.
Notes: nothing throttled in 20 calls, so per §5/T01 a conservative **5 requests/second (0.2 s interval)**
is pinned for T03/T04, not a measured limit.

#### T02 — Rebuild the UPRN -> footprint join — completed 2026-08-27 — STOPPED ON MISMATCH, CP-2 NOT SIGNED

Artifacts: `openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_gb_epc_coverage.py` (`task_t02`);
`openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_uprn_join.csv`;
`openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/osopenuprn_gb.zip` (618,494,417 bytes, md5
`2f023512afc378cd7b9351b24ccf1a34`, matches §3.6).
Deviations: (1) fixed a `UnicodeEncodeError` on the console (BOM at the start of
`osopenuprn_202608.csv`, cp1252 stdout) by reading the member with `encoding="utf-8-sig"` instead of
`"utf-8"` and by ascii-safe-encoding one diagnostic print line; no data logic changed. (2) the OS Open
UPRN CSV carries a header row (`UPRN,X_COORDINATE,Y_COORDINATE,LATITUDE,LONGITUDE`) not documented in
§3.6/§4 — the script detects and skips it. (3) `X_COORDINATE`/`Y_COORDINATE` are native EPSG:27700, so
the UPRN side of the join was built directly in 27700 without reprojection; only the EU-02 footprints
(native EPSG:32630) were reprojected to 27700, per §3.7.
Test status: **FAIL — stopped per §5/T02 ("Any mismatch -> stop and report; do not proceed").**
`rows_in_padded_bbox` = 16,151, exact match to §4. Join regression numbers did **not** match:
`distinct_osm_id_strict` = **1,059** (expected 1,219), `distinct_osm_id_with_1m_buffer` = **1,193**
(expected 1,231), `total_strict_pairs` = **6,504** (expected 6,838).
Notes: 🔴 the bbox filter and the raw UPRN scan are exact-reproducible (16,151 == 16,151), so the input
data and bbox are not the cause. Diagnosed (read-only, no fix applied, no third host contacted):
`pyproj`'s `EPSG:32630 -> EPSG:27700` transform in this environment falls back to an approximate
pipeline (`accuracy=2.0`, i.e. ~2 m) because the OSTN15 NTv2 grid
(`uk_os_OSTN15_NTv2_OSGBtoETRS.tif`) is **not installed** locally — `TransformerGroup` logs
`UserWarning: Best transformation is not available due to missing Grid(...)`. A ~2 m systematic offset
is large enough to flip narrow central-London terraced-house footprints across their own boundary,
which is consistent with a strict-join shortfall concentrated exactly there. This is offered as the
likely cause, not a confirmed one — no attempt was made to fetch the grid (its host, `cdn.proj.org`, is
not one of the two pinned in §3, so doing so would have violated hard rule 6).

#### T02b — join regression repaired — completed 2026-08-27
Artifacts: `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_uprn_join.csv` (441,867 B; header
`osm_id,uprn,postcode,within,footprint_area_m2`).
Deviations: two defects in the first T02 attempt were fixed (no change to §4, no new data source).
(1) **Datum mix.** The join used OS Open UPRN's native `X_COORDINATE`/`Y_COORDINATE` (OSGB36/EPSG:27700)
against footprints reprojected from EPSG:32630 *without* the OSTN15 grid — a ~1–2 m systematic offset,
enough to push points out of narrow London terraces. Rebuilt the point layer from the file's own WGS84
`LATITUDE`/`LONGITUDE` (`Point(lon, lat)`, `crs=4326`, `.to_crs(27700)`) so both sides travel the same
path. No `cdn.proj.org` fetch; hard rule 6 intact. Proved with the 16,151 candidate points cached once
and three variants: native E/N → 1059/1193/6504; lat-lon→27700 → 1219/1231/6838; lat-lon→32630 vs
manifest native → 1219/1231/6838.
(2) **`.loc` on a duplicated index.** `joined_buffer.loc[idx]` returned a DataFrame (one point can match
several buffered footprints), writing pandas reprs into 47 cells and inflating `osm_id` to 1,276 over a
1,242-row manifest; `index.difference()` also dropped valid buffer-only pairs. Rewritten as
`strict_pairs = {(uprn, osm_id)}` plus `.iterrows()` on both loops.
Test status: **PASS.** `total_strict_pairs` 6,838 = 6,838; `distinct_osm_id_strict` 1,219 = 1,219;
`distinct_osm_id_with_1m_buffer` 1,231 = 1,231; `rows_in_padded_bbox` 16,151 = 16,151;
`not_in_manifest` 0. All four §4 numbers reproduce.
Notes: the T03 denominator is **6,838 distinct strict UPRNs**, not 1,219 — 1,219 is the footprint count.
Both defects registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 7.

#### T03 — EPC search sweep over the 6,838 strict UPRNs — completed 2026-08-27
Artifacts: `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_certificates.csv` (633,219 B, 8,623 data
rows); per-UPRN JSON cache under `_cache/search_by_uprn/`; `t03.log`.
Deviations: none to the method. Operationally the sweep was killed once and restarted once by external
causes (see Notes); both were survivable because the cache is keyed per UPRN and `was_cached`
short-circuits the sleep and the call counter — cost was time and quota, never correctness.
Test status: **PASS.** `uprns_searched` 6,838 (= T02's distinct strict UPRNs);
`uprns_with_at_least_one_certificate` **3,600**; `uprns_404_no_certificate` **3,238** (3,600 + 3,238 =
6,838, no unexplained status); `distinct_footprints_with_at_least_one_certificate` **824** of 1,219
strict footprints; `api_calls_made` 5,729; `elapsed_seconds` 2,263.9 (≈ 2 responses/s under the pinned
`RATE_INTERVAL_S = 0.2`). No 429 at any point.
Notes: 🔴 824/1,219 = 67.6 % is a **certificate** rate, not a stock census — EPC covers dwellings sold,
let or built since 2008, so this number must never be printed beside Madrid's 98.74 % without that
sentence. It is also **not yet a year-coverage number**: the search endpoint is summary-only and carries
no construction-age band, which is what T04 fetches. Three operational hazards met here are registered
in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 13 (duplicate concurrent runs from an
orphaned subagent process; a "completed" subagent waking to delete a live cache and restart the sweep;
`TaskStop` on an agent killing the long job that agent parented, compounded by Python's stdout
block-buffering making a 0-byte log look like death).

#### T04 — certificate fetch over the 5,385 distinct certificate numbers — completed 2026-08-27

- **Artifacts:** `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_certificates.csv` (rewritten with the
  attribute columns `cert_http_status, age_band, year_key_used, property_type, built_form, floor_area_m2`),
  `_cache/certificate/` (one JSON per certificate number), `t04.log`.
- **Deviations:** none. Ran from the director session with `PYTHONUNBUFFERED=1`, one process only,
  at the pinned `RATE_INTERVAL_S = 0.2`.
- **Test status:** PASS. `certificates_fetched: 5385`, `certificates_with_age_band: 4045`,
  `api_calls_made: 5385`, `elapsed_seconds: 2167.7`. Calls equal certificates exactly — no retry,
  no 429, no unexplained status.
- **Notes:** the denominator here is 5,385 distinct certificate numbers, not 6,838 UPRNs and not
  1,219 footprints. `age_band` is the RdSAP construction-age BAND (a letter), never a year;
  `registrationDate` remains a lodgement date.

#### T05 — coverage percentages computed — completed 2026-08-27

- **Artifacts:** `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_coverage_probe.json`.
- **Deviations:** none. No network call; pure recomputation over `gb_epc_certificates.csv` and the
  certificate cache.
- **Test status:** PASS. `footprints_with_at_least_one_certificate: 824`,
  `footprints_with_an_observed_age_band: 797`, `age_band_pct_of_1242: 64.17`,
  `age_band_pct_of_1219: 65.38`. Top bands D 473 / E 351 / L 300 / J 273 / K 254.
- **Notes:** 🔴 these are **certificate** coverage rates over a sold/let/new-since-2008 population,
  not a stock census — they must never be printed beside Madrid's 98.74 % or France's two-signal
  figures without that sentence. 🔴 the observed quantity is an age BAND, so GB is not
  interchangeable with the ES/FR observed-year sidecars. Dwelling count is a MEASURED ABSENCE in the
  certificate payload (key search found none), so GB does not reproduce the two-signal shape that
  typed France and Spain. **STOPPED AT CP-3 — no verdict written.**

#### CP-3 — SIGNED 2026-08-27 — verdict: GB STAYS OUT OF S3

- **Signed by:** director, under the owner's delegation *"tu progress comme tu recommends avec CP3,
  vas-y"*. T01–T05 all complete; nothing running.
- **Reported at the checkpoint:** 11,114 live calls over the two pinned hosts (5,729 search + 5,385
  certificate), 4,431.6 s wall-clock, zero 429 and zero unexplained status; the only non-200 is
  `404 x 3,238` (UPRN with no certificate, an expected answer, not an error). 797 of 1,219
  strict-join footprints carry an observed age band — **65.38 %** (64.17 % of the 1,242 manifest).
- **Verdict and its four reasons:** the observed quantity is an RdSAP age **BAND**, not a year, and
  converting it to a year is ASSIGNMENT — the exact ground that ruled Italy out; dwelling count is a
  **measured absence**, so GB does not reproduce the two-signal shape that typed FR and ES; the
  65.38 % is **certificate** coverage over a sold/let/new-since-2008 population, not a stock census,
  and is not comparable to the ES 98.74 %; and `S3` is already PROMOTED at 95 of 96 under `D-EU-24`
  with the cell spec `FROZEN_PINNED`, so admitting a third country reopens a signed campaign and
  moves every `idf_sha256`.
- **What changed for the record:** London is **MEASURED, not credential-blocked**. The pre-credential
  verdicts in `gb_it_coverage_probe.json` were marked `SUPERSEDED_2026-08-27_BY_LIVE_PROBE` in place;
  the original text is retained inside each superseded string. GB stays out for a
  **quantity-mismatch** reason, not an access reason — that sentence must travel with the number.
- **Not granted:** enlarging `S3` to a band-based country. That is a SEPARATE request.
- **Artifacts:** `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_coverage_probe.json`
  (`cp3_verdict` block), `gb_it_coverage_probe.json` (superseded in place).
- **Plan status:** CLOSED at CP-3. No further task in this plan.
