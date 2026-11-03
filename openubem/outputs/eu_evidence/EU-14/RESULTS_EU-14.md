# `RESULTS_EU-14` — Bologna `IT-BOL-GALVANI2` reopened under tagged ISTAT census-section imputation

**Date:** 2026-08-28 · **Ruling:** `D-EU-34` · **Executor prompt:** `prompts/previous/PROMPT_EU-14_bologna_construction_year_reopening.md`
**District:** `IT-BOL-GALVANI2` (Bologna, Galvani 2) · **Perimeter:** `S2` real-footprint, one EnergyPlus run per residential building, `f=0` only.

> 🔴 **Every construction period in this district is IMPUTED, never observed.**
> `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on **1,204 of 1,204**
> manifest rows. The pooled EUI below may never be quoted, compared or pooled with Madrid / Lyon / London
> without that tag stated in the same sentence. This does **not** overturn
> `implementation/EU11_Bologna_construction_year_investigation.md`: no per-building observed construction
> year exists in any open source, and none was found here. `D-EU-34` layers an imputation arm on top of that
> standing FAIL; it does not repeal it.

---

## 1. Step one (mandatory retry): INSPIRE Buildings WFS — **FAILED**, access-restriction unresolved

Nine endpoints probed live on **2026-08-28T22:30:12–14Z**. Zero returned a GetCapabilities document.

| Endpoint | Result |
|---|---|
| `https://servizigeo.regione.emilia-romagna.it/wfs/inspire_bu` | `NETWORK_ERROR` — `[Errno 11001] getaddrinfo failed` (DNS) |
| `http://servizigeo.regione.emilia-romagna.it/wfs/inspire_bu` | `NETWORK_ERROR` — `[Errno 11001] getaddrinfo failed` (DNS) |
| `https://geoportale.regione.emilia-romagna.it/services/inspire/bu/wfs` | `HTTP_404` |
| `https://geoportale.regione.emilia-romagna.it/wfs` | `HTTP_404` |
| `https://wms.cartografia.agenziaentrate.gov.it/inspire/wfs/Building/ows` | `HTTP_500` |
| `https://wms.cartografia.agenziaentrate.gov.it/inspire/wfs/ows` | `HTTP_500` |
| `https://inspire.agenziaentrate.gov.it/wfs` | `NETWORK_ERROR` — `[Errno 11001] getaddrinfo failed` (DNS) |
| `http://inspire.agenziaentrate.gov.it/wfs` | `NETWORK_ERROR` — `[Errno 11001] getaddrinfo failed` (DNS) |
| `https://geodati.gov.it/geodati-wfs/services/WFS` | `HTTP_404` |

Machine-readable evidence, one record per attempt with URL, timestamp, HTTP status and error string:
`openubem/outputs/eu_evidence/EU-14/inspire_wfs_probe_evidence.json`.

**Disposition unchanged from the closed investigation: `access-restriction — unresolved, not disproven`.**
The lead still fails acceptance criterion 3. Step 2 was therefore entered, as `PROMPT_EU-14` §2 requires.

## 2. Step two: ISTAT 2011 census-section imputation (`D-EU-34` §3.2)

**Method, as implemented in `scripts/run_eu_s2_district_campaign.py::_it_rows`:**

1. Eaves height from the municipal portal layer `c_a944ctc_edifici_pl` (`altezza_gr`, CC BY 4.0), joined by
   footprint intersection, max per building. 🔴 Height is used **only** as height — never to infer a year.
2. Footprint adjacency computed for attached/detached typing.
3. Each residential footprint's **centroid** joined by `within` to the municipal section polygons
   (`sezioni-di-censimento-anno-2011`); the section's ISTAT construction-period counts `E8…E16` read from
   `R08_indicatori_2011_sezioni.csv` (`PROCOM = 37006`) inside
   `openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/dati-cpa_2011.zip`.
4. The section's **dominant** period band becomes the building's TABULA period. Ties are excluded, not broken.
   `E12` maps to `STRADDLE` (spans a TABULA period boundary) and is excluded by rule.
5. Every surviving row is tagged `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD`.

**ISTAT → TABULA band map (reference year in brackets):**
`E8 → IT.01` (1900) · `E9 → IT.03` (1930) · `E10 → IT.04` (1950) · `E11 → IT.05` (1965) ·
`E12 → STRADDLE, excluded` · `E13 → IT.06` (1985) · `E14 → IT.07` (1995) · `E15 → IT.07` (2003) · `E16 → IT.08` (2010).

### 2.1 Coverage and exclusion census — measured before any IDF was generated

| Stage | Count |
|---|---:|
| Residential buildings in `02_residential_manifest.gpkg` | **1,220** |
| Centroid inside a mapped census section | **1,220** (0 `UNMAPPED_CENSUS_SECTION`) |
| Section carried ISTAT period data | **1,220** (0 `CENSUS_SECTION_DATA_MISSING`) |
| Excluded — `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` (section total `E8…E16` = 0) | 4 |
| Excluded — `CENSUS_SECTION_PERIOD_TIE_E8_E9` | 10 |
| Excluded — `CENSUS_SECTION_PERIOD_TIE_E9_E10` | 2 |
| Excluded — boundary-straddling `E12` dominant | 0 |
| Excluded — geometry / IDF build failure | 0 |
| **Prepared for Speed** | **1,204** |

Source of record: `openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/summary_prerun.json`.

### 2.2 Imputed period and typology distribution (1,204 prepared)

| TABULA period | Buildings | | Type | Buildings |
|---|---:|---|---|---:|
| `IT.01` | 1,099 | | `AB` | 793 |
| `IT.03` | 79 | | `MFH` | 356 |
| `IT.05` | 26 | | `TH` | 35 |
| | | | `SFH` | 20 |

**91.3 % of the district lands in a single imputed band (`IT.01`).** The imputation is therefore close to a
district-wide constant, not a per-building discrimination — read every downstream figure with that in mind.

## 3. Campaign

Same `S2` machinery as Madrid / Lyon / London (`PROMPT_EU-11_full_district_campaign_speed.md`), unchanged
physics. Speed `sbatch --array`, fire-and-forget; no login-node compute.

- **Speed job:** `1295646` · **tasks:** 1,204 · **status:** `HARVESTED_FROM_SPEED`
- **Engine:** `EnergyPlus, Version 23.1.0-87ed9199d4` (35 distinct run-header timestamps, one engine build),
  Linux `5.14.0-687.29/39.1.el9_8.x86_64` across 23 hosts (`speed-15…36`, `magic-node-02…10`, `wolsey`, `xailab`).
- **Weather:** `openubem/data/weather/it_bologna_2013_2014_y2014.epw`, sha256
  `ab631c6026e3f7cf5cfcff7c6a506eb84b6eeb62f1afa5703fc48ef0897e25fa` (`RULED_PINNED_EXCEPTION`).

### 3.1 Outcome

| | Count |
|---|---:|
| Run on Speed | 1,204 |
| Succeeded (rc = 0, `heating_kwh` parsed) | **1,202** |
| Failed on Speed (`EPLUS_FATAL`) | 2 |

The two failures, `heating_kwh`/`eui_kwh_m2` left blank and never fabricated:

| `building_id` | archetype | `geometry_outcome` | severe | fatal |
|---|---|---|---:|---:|
| `29618` | `IT.MidClim.AB.01.Gen.ReEx.001.001` | `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` | 8 | 1 |
| `31929` | `IT.MidClim.MFH.01.Gen.ReEx.001.001` | `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` | 6 | 1 |

Both are the `GetSurfaceData` RoofCeiling vertex-count-mismatch class already registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 12 (same symptom as Lyon `b2d90c2cba300225`).

### 3.2 Geometry outcome split

| `geometry_outcome` | Prepared | Succeeded | Pooled EUI (kWh/m²) |
|---|---:|---:|---:|
| `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` | 796 | 795 | 53.8922 |
| `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` | 408 | 407 | 78.7679 |

**66.1 % dwelling-partitioned.** Bologna publishes no per-building dwelling count, so every emitted layout
uses the `EU-13` four-tier imputation cascade — hence `…_IMPUTED_COUNT`, never `DWELLING_LAYOUT_EMITTED`.

## 4. Result — **IMPUTED**

> **`IT-BOL-GALVANI2` pooled heating EUI = 55.5346 kWh/m²**
> (139,968,909.6849 kWh over 2,520,390.9432 m², area-weighted, 1,202 of 1,220 residential buildings)
> — 🔴 **`IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on 100 % of rows.**

Per-building spread over the 1,202: min 35.6201, median 67.4924, max 169.7616 kWh/m². The pooled figure sits
well below the median because floor area concentrates in the large `AB` blocks that heat least per m².

🔴 **This number may not be set beside the S0 archetype figure `it` = 108.25 kWh/m² ± 0.16 %** — different
perimeter, different geometry, different weather years, and now also an imputed construction period
(`D-EU-31`, `FINDING 192`).

## 5. External validation and findings

`FINDING 199` (recorded, not corrected): 55.5346 falls inside `DR16`'s own pre-registered
**INCOMPATIBLE (Too Low)** band (< 95.0) for its asset-rating protocol; `DR16`'s `CONSISTENT` band is
115.0–165.0. Full verdict table and the campaign-wide context — all four districts cluster at 55–79 kWh/m² —
in `docs/docs_ACTIVE/europeanLocations/results/RESULTS_EU-11.md` § External validation. No correction was
applied here; diagnosing it is out of `EU-14`'s scope.

## 6. Known, disclosed gaps

1. **No dwelling-layout floor-plan pop-ups for Bologna — 0 side-cars.** `scripts/emit_eu11_layout_sidecars.py`
   calls `allocate_european_dwellings` directly and is incompatible with the ISTAT-imputed provenance path; a
   test run wiped `geometry_outcome` to NaN and the manifest was restored by a clean re-harvest from Speed
   (no data loss). 🔴 **Do not re-run that script against Bologna.** Registered in
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 12.
2. **The imputation is section-level, not building-level** (see §2.2) — 91.3 % of buildings inherit one band.
3. **Step 1's lead is unresolved, not disproven** — if the INSPIRE endpoints return, an observed-year arm
   supersedes this one and the tag must be dropped only for the rows it actually covers.

## 7. Artefacts

| Artefact | Path |
|---|---|
| Manifest (carries `construction_period_provenance`) | `openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/it_bol_galvani2_manifest.csv` |
| Prepared population | `…/IT-BOL-GALVANI2/prepared_buildings.csv` |
| Post-run / pre-run summaries | `…/IT-BOL-GALVANI2/summary.json`, `summary_prerun.json` |
| Step-1 probe evidence | `openubem/outputs/eu_evidence/EU-14/inspire_wfs_probe_evidence.json` |
| Viewer + data folder | `openubem/outputs/3D/eu_IT-BOL-GALVANI2_viewer.html` + `eu_IT-BOL-GALVANI2_data/`, mirrored byte-identically to `docs/docs_ACTIVE/europeanLocations/outputs_3D/` |
| Standing FAIL investigation (not repealed) | `docs/docs_ACTIVE/europeanLocations/implementation/EU11_Bologna_construction_year_investigation.md` |
