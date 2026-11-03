# INVESTIGATION REPORT — EU-11 Full-Fleet Population Expansion Toward 100 %

- **Arc:** European Locations, Full-Fleet Expansion (`D-EU-101`)
- **Investigator / Author:** Antigravity (Gemini 3.8 Flash)
- **Date:** 2026-09-04 / 2026-09-05
- **Reference Doc:** `docs/docs_ACTIVE/europeanLocations/debugs/INVESTIGATION_full-fleet-100pct-2026-09-04.md`
- **Output Target:** `docs/docs_ACTIVE/europeanLocations/debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT.md`
- **Mode:** Read-only investigation and root-cause analysis (no cluster calls, no git modifications, no destructive actions).

---

## 1. Executive Summary & Fleet Status

As of 2026-09-04, following the implementation of `FINDING 251` (London tag fix), `FINDING 253` (Madrid tag fix), and `FINDING 255` (`D-EU-37` Lyon mid-rise expansion), the simulated European fleet stands at **3,066 / 4,186 prepared (73.2 %)**. The remaining gap across the four study districts is **1,120 buildings**:

| District | Country | Attempted | Prepared | Gap | Primary Exclusion Lever |
|---|---|---|---|---|---|
| `GB-LDN-STDUNSTANS` | GB | 1,242 | 389 (31.3 %) | 853 | EPC age-band missing / period straddles (800) |
| `ES-MAD-BERRUGUETE` | ES | 1,194 | 1,008 (84.4 %) | 186 | Missing observed storeys (163) |
| `FR-LYO-HAUTCOEURPENTES` | FR | 530 | 469 (88.5 %) | 61 | Typology registry gap 13–14 dwellings (37) |
| `IT-BOL-GALVANI2` | IT | 1,220 | 1,200 (98.4 %) | 20 | ISTAT census section ties/no-res (16), IDF crash (4) |
| **Total** | | **4,186** | **3,066 (73.2 %)** | **1,120** | |

Every excluded building carries a deterministic blocker reason in its district's `summary.json`. Below is the verdict summary across all nine categories:

| Cat. | Category / Exclusion Key | Count | Verified Code Citation | Verdict | Potential Recovery |
|---|---|---|---|---|---|
| **1a** | London `MISSING_OBSERVED_EPC_AGE_BAND` | 445 | `scripts/run_eu_s2_district_campaign.py:182-183` | **(a) Genuine dead end** (open data ceiling) | 0 |
| **1b** | London `PERIOD_STRADDLE_*` | 355 | `scripts/run_eu_s2_district_campaign.py:185-187` | **(c) Policy question for owner** | +355 |
| **2** | `MISSING_OBSERVED_STOREY_COUNT` (ES 163, GB 47) | 210 | `scripts/run_eu_s2_district_campaign.py:198, 347` | **(a) Genuine dead end** (in current ingest) | +33 (GB houses in EPC) / 0 (ES) |
| **3** | `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` (FR 37, ES 1) | 38 | `openubem/semantic/european_archetype_mapping.py:193-194` | **(c) Policy question for owner** | +38 |
| **4** | `IDF_ASSEMBLY_FAILED_RuntimeError` (ES 9, FR 4, IT 4) | 17 | `scripts/run_eu_s2_campaign.py:573-580` | **(b) Real code fix exists** (4 box buildings) / **(a) Dead end** (13 courtyards) | +4 |
| **5** | `MISSING_OBSERVED_YEAR_BUILT` (ES 11, FR 8) | 19 | `openubem/semantic/european_archetype_mapping.py:74-83` | **(a) Genuine dead end** | 0 |
| **6** | Bologna Census Ties (12) + No-Res (4) | 16 | `scripts/run_eu_s2_district_campaign.py:288-299` | **(a) Genuine dead end** / **(c) Policy question** | 0 (or +12 by policy) |
| **7** | London `UNMAPPABLE_RESIDENTIAL_TYPE` | 6 | `scripts/run_eu_s2_district_campaign.py:192-197` | **(b) Real code fix exists** | +6 |
| **8** | `MISSING_OBSERVED_DWELLING_COUNT` (FR 1, ES 1) | 2 | `openubem/semantic/european_archetype_mapping.py:85-122` | **(a) Genuine dead end** | 0 |
| **9** | Lyon Disagree Outliers (FR 10, ES 1) | 11 | `openubem/semantic/european_archetype_mapping.py:203` | **(c) Policy question** (already adjudicated) | 0 (fail-closed) |

- **Total directly recoverable via verified code fixes (Verdict b):** **+10 buildings** (6 London unmappable types + 4 non-courtyard IDF near-duplicate box reroutes).
- **Total recoverable via owner policy rulings (Verdict c):** **+393 buildings** (355 London period straddles + 38 registry gap 13–14 dwellings).
- **Theoretical reachable fleet with policy extensions:** **3,469 / 4,186 (82.9 %)**.
- **Hard source data ceiling:** **717 buildings** (missing EPC certificates, missing cadastral storeys, true courtyard donuts, unpopulated census epochs, unbuilt/unmatched cadastre footprints).

---

## 2. Detailed Findings by Category

### Category 1: London EPC Age Band Missing (445) & Straddles (355) — 800 buildings

- **Exact Count:** 800 buildings (445 `MISSING_OBSERVED_EPC_AGE_BAND`, 355 `PERIOD_STRADDLE_*`).
- **Code Citation:** `scripts/run_eu_s2_district_campaign.py:65-69, 181-187`.
- **Exclusion breakdown from `summary.json`:**
  - `MISSING_OBSERVED_EPC_AGE_BAND`: 445
  - `PERIOD_STRADDLE_D_GB.03_GB.04`: 97
  - `PERIOD_STRADDLE_C_GB.02_GB.03`: 77
  - `PERIOD_STRADDLE_B_GB.01_GB.02`: 76
  - `PERIOD_STRADDLE_F_GB.04_GB.05`: 66
  - `PERIOD_STRADDLE_K_GB.07_GB.08`: 20
  - `PERIOD_STRADDLE_J_GB.06_GB.07`: 19

#### 1.1. Missing EPC Match (445 buildings) — Verdict: (a) Genuine Dead End
- **Investigation:**
  - In `openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_gb_epc_coverage.py`, the join is an exact point-in-polygon spatial join between `OS Open UPRN` coordinates and the 1,242 OSM residential footprints (1,219 footprints contain a UPRN; 23 contain no UPRN).
  - Searches against the Ministry of Housing, Communities & Local Government (MHCLG) EPC API returned certificates for only 824 footprints; 797 carried an RdSAP `construction_age_band`. The remaining 445 have no matching certificate.
  - *Statutory Coverage Ceiling:* Under the *Energy Performance of Buildings (England and Wales) Regulations 2012*, domestic EPCs are only legally mandated upon construction, sale, or new tenancy since autumn 2008. Properties continuously occupied by the same owner/tenant prior to 2008 or long-held municipal housing have no statutory obligation to hold an EPC. This creates an unfillable ~65 % ceiling on existing stock.
  - *Candidate Alternate UK Building-Age Sources Checked:*
    1. **Valuation Office Agency (VOA) Council Tax Property Attributes:** VOA records property build-period codes for all council-tax-banded dwellings. However, property-level (UPRN-level) VOA data is legally protected under section 18 of the *Commissioners for Revenue and Customs Act 2005* (CRCA 2005) and is only accessible in the secure enclave of the ONS Secure Research Service (SRS) under Digital Economy Act accredited research projects. It is **not** open data.
    2. **Ordnance Survey National Geographic Database (OS NGD) Building Theme:** OS NGD provides an age-band attribute, but it is a commercial/licensed product (under the UK Public Sector Geospatial Agreement / paid licence), not part of OS OpenData.
    3. **GLA London Building Stock Model (LBSM) / UCL Energy Institute:** Built using private/licensed data feeds; open access is restricted to web visualisations and aggregate tiles, not property-level microdata.
- **Conclusion:** No open, property-level building age database with exact UPRN/OSM matching exists in UK open data. The 445 missing records represent a genuine statutory and open-data availability limitation.

#### 1.2. Period Straddles (355 buildings) — Verdict: (c) Policy Question for the Owner
- **Investigation:**
  - All 355 straddling buildings hold an EPC certificate generated under **RdSAP** (Reduced Data SAP).
  - Detailed recursive inspection of all 5,385 cached certificate JSON files (`openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/certificate/*.json`) revealed:
    - `construction_year` is **0 out of 355** (RdSAP does not record numerical construction years; only new-build full SAP assessments carry this field).
    - `sap_building_parts.construction_age_band` strictly mirrors the top-level letter band (B, C, D, F, J, K).
    - `transaction_type` does not distinguish construction era: even the 10 certificates with `transaction_type == 3` ("New dwelling") were post-2008 flat conversions in 1930s blocks.
    - Energy rating / SAP scores reflect thermal performance and heating systems, not structural construction dates.
    - 106 buildings had multiple historical certificates with conflicting bands (e.g. Band A and Band B), reflecting assessor variance; picking one over another violates the rule against arbitrary resolution.
  - *Root Cause:* The straddle is caused by the fundamental misalignment between RdSAP standard bands and TABULA UK Building Regulation eras:
    - **Band B (1900–1929):** 76 buildings. TABULA cutoff is 1918 (GB.01 <= 1918; GB.02 = 1919–1944). 1900–1918 is 65.5 % of the band.
    - **Band C (1930–1949):** 77 buildings. TABULA cutoff is 1944 (GB.02 = 1919–1944; GB.03 = 1945–1964). 1930–1944 is 75.0 % of the band.
    - **Band D (1950–1966):** 97 buildings. TABULA cutoff is 1964 (GB.03 = 1945–1964; GB.04 = 1965–1980). 1950–1964 is 88.2 % of the band.
    - **Band F (1976–1982):** 66 buildings. TABULA cutoff is 1980 (GB.04 = 1965–1980; GB.05 = 1981–1990). 1976–1980 is 71.4 % of the band.
    - **Band J (2003–2006):** 19 buildings. TABULA cutoff is 2003 (GB.06 = 1991–2003; GB.07 = 2004–2009). 2004–2006 is 75.0 % of the band.
    - **Band K (2007–2011):** 20 buildings. TABULA cutoff is 2009 (GB.07 = 2004–2009; GB.08 = 2010+). 2007–2009 is 60.0 % of the band.
- **Options for the Project Owner:**
  1. **Option 1 (Status Quo / Fail-Closed):** Keep rule `scripts/run_eu_s2_district_campaign.py:63-64` ("complete interval must belong to one TABULA period"). Recover: **0**.
  2. **Option 2 (Majority-Span Allocation):** Assign each RdSAP band to the TABULA archetype representing the majority of its year range (Band B -> GB.01, Band C -> GB.02, Band D -> GB.03, Band F -> GB.04, Band J -> GB.07, Band K -> GB.07). In St Dunstan's (Stepney/Tower Hamlets), this strongly aligns with historical construction (Victorian/Edwardian terraces and post-blitz 1950s reconstruction estates). Recover: **+355 buildings**.

---

### Category 2: `MISSING_OBSERVED_STOREY_COUNT` (Madrid 163 + London 47 = 210 buildings) — Verdict: (a) Genuine Dead End in Ingested Data

- **Exact Count:** 210 buildings (ES 163, GB 47).
- **Code Citation:** `scripts/run_eu_s2_district_campaign.py:198-199, 346-347` (`_valid_storeys`).
- **Investigation:**
  - **Madrid (163 buildings):**
    - Traced acquisition pipeline to `openubem/acquisition/catastro_inspire_fetcher.py`.
    - `es_catastro_coverage_probe.json:238-242` documents that the Direccion General del Catastro INSPIRE WFS `bu:Building` endpoint returns `numberOfFloorsAboveGround` with `xsi:nil="true"` and `nilReason="other:unpopulated"` for **1,883 / 1,883 (100 %) of residential features in the study bounding box**.
    - Cadastral floor counts exist only on `bu:BuildingPart` (reachable via per-parcel stored queries or bulk provincial ATOM feeds) or through the CNIG PNOA LiDAR nDSM / Ayuntamiento de Madrid 3D vectors. None of these have been ingested into the repository.
  - **London (47 buildings):**
    - 47 buildings pass EPC age matching and type mapping, but lack `levels` and `height_m` in the OSM manifest (`provenance_levels == "OSM_MISSING"`).
    - Breakthrough finding in EPC certificate payloads: 33 of these buildings are single-family houses or terraced houses (`building_tag in ('house', 'terrace')`). For single dwellings, RdSAP records every individual floor in `sap_floor_dimensions` (`floor: 0`, `floor: 1`, etc.). Across all 33 houses, the floor count can be derived directly from `len(sap_floor_dimensions)` (yielding 2 or 3 storeys).
    - The remaining 14 buildings are apartment blocks (`apartments`). In an apartment block, the EPC certificate applies to an individual flat; its `sap_floor_dimensions` only records the floors within that unit (typically 1), not the building as a whole.
    - Environment Agency 1m National LiDAR coverage is open data, but has not been fetched or clipped for this district.
- **Verdict:**
  - Within currently ingested manifest files: **(a) Genuine dead end**.
  - Secondary signal recovery: **+33 London houses** could be recovered if the owner authorizes reading `len(sap_floor_dimensions)` from the cached EPC records for single-dwelling houses. Madrid's 163 buildings remain blocked without an external LiDAR/Catastro-part ingest.

---

### Category 3: `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` (Lyon 37 + Madrid 1 = 38 buildings) — Verdict: (c) Policy Question for the Owner

- **Exact Count:** 38 buildings (Lyon 37, Madrid 1).
- **Code Citation:** `openubem/semantic/european_archetype_mapping.py:193-194`:
  ```python
  if dwellings in (13, 14):
      return None, TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14
  ```
- **Investigation of `tabula_archetypes_fr.json`:**
  - Across all 40 records in `openubem/data/construction/tabula_archetypes_fr.json`:
    - For `MFH`: the exemplar `n_apartment` values are 1.0, 4.0, 5.0, 8.0, 9.0, and **12.0** (`FR.N.MFH.06.Gen`).
    - For `AB`: the exemplar `n_apartment` values are **15.0** (`FR.N.AB.02.Gen`), 26.0, 29.0, 30.0, 31.0, 34.0, 48.0, 69.0, and 86.0.
  - *Analysis:* The TABULA catalog is a library of representative archetype exemplars, **not** an exhaustive regulatory standard specifying that real-world buildings cannot contain 13 or 14 dwellings. The gap in lines 193–194 is an artifact of transcribing exemplar extremes (12 and 15) as rigid classification bounds.
  - *Distribution of the 38 Buildings:*
    - **Lyon (37 buildings):**
      - 34 buildings have 5–9 storeys (Storey 5: 4; Storey 6: 11; Storey 7: 8; Storey 8: 9; Storey 9: 2).
      - 3 buildings have 4 storeys.
    - **Madrid (1 building):** `way/224012143` (house tag, 14 dwellings, 5 storeys).
- **Options for the Project Owner (Framed like `DECISION_REQUEST_D-EU-37`):**
  - **Option 1 (Widen Rule by Storey Range):**
    Close the gap by partitioning 13–14 dwellings across the established storey threshold:
    - `dwellings in (13, 14) & storeys <= 4 -> MFH` (recovers 3 Lyon buildings)
    - `dwellings in (13, 14) & storeys >= 5 -> AB` (recovers 34 Lyon buildings + 1 Madrid building)
    - *Expected Recovery:* **+38 buildings** (Lyon 37 -> 0; Madrid 1 -> 0).
  - **Option 2 (Leave Rule As-Is / Fail-Closed):**
    Maintain the discrete exemplar boundaries; 38 buildings remain fail-closed exclusions.

---

### Category 4: `IDF_ASSEMBLY_FAILED_RuntimeError` (17 buildings) — Verdict: (b) Real Code Fix (4 buildings) / (a) Dead End (13 buildings)

- **Exact Count:** 17 buildings (`ES-MAD-BERRUGUETE`: 9, `FR-LYO-HAUTCOEURPENTES`: 4, `IT-BOL-GALVANI2`: 4).
- **Code Citation:** `scripts/run_eu_s2_campaign.py:573-580` (raised in `build_idf_for_building` after extrusion).
- **Investigation & Per-Building Diagnosis:**
  - Traced execution through `build_idf_for_building` and diagnosed each individual failure mode:
  - **Group A: Real Courtyard Voids (13 buildings) — Verdict: (a) Genuine Dead End**
    - Lyon (3): `BATIMENT0000000240879992_part0` (1 interior ring), `BATIMENT0000000240880410_part0` (1 interior ring), `BATIMENT0000000240880479_part0` (1 interior ring).
    - Madrid (6): `relation/12628570` (1 hole), `relation/12702625` (1 hole), `relation/12707193` (3 holes), `relation/12818819` (1 hole), `relation/4165181` (1 hole), `relation/5808696` (1 hole).
    - Bologna (4): `29583` (1 hole), `29801` (1 hole), `32639` (1 hole), `33359` (1 hole).
    - *Root Cause:* Each building has a physical courtyard (`Polygon.interiors >= 1`, void area >= 1.0 m²). During dwelling partitioning and subsequent multi-storey extrusion, geomeppy's `intersect_match` introduces interzone vertex mismatches between storeys. The standard recovery function `_force_reroute_room_layout_to_one_zone_per_floor` (`openubem/idf/surfaces.py:693-694`) **explicitly refuses to collapse holed polygons into a single block**:
      ```python
      if any(Polygon(r).area >= 1.0 for r in footprint.interiors):
          return False
      ```
      Collapsing a courtyard into a single stacked block produces a "donut" polygon that EnergyPlus rejects with an unrecoverable `CheckConvexity` FATAL error. Decomposing courtyards into convex multi-block wings requires modifying the closed geometry engine (`openubem/geometry/european_residential.py`), which is prohibited under Rule 1.
  - **Group B: Non-Courtyard Rerouted Boxes (4 buildings) — Verdict: (b) Real Code Bug / Fix Exists**
    - Lyon (1): `BATIMENT0000000240880367_part0` (8 storeys, 0 interior rings).
    - Madrid (3): `way/311968163` (5 storeys, 0 holes), `way/333138113` (7 storeys, 0 holes), `way/432405737` (6 storeys, 0 holes).
    - *Root Cause:* For these 4 buildings, `_force_reroute_room_layout_to_one_zone_per_floor` successfully executes (`did_reroute is True`). Following rerouting and surface pairing, `find_mismatched_interzone_pairs(idf)` returns `mismatched = []` (**zero mismatched surfaces**!).
    - However, geomeppy's floating-point arithmetic inserts a sub-millimetre vertex pair (~0.0004 m apart), setting `residual_near_dup = True`.
    - Look at line 573 of `scripts/run_eu_s2_campaign.py`:
      ```python
      if not did_reroute and not mismatched:
          for _z in zones:
              _z["fallback_reason"] = "near_duplicate_vertex_tolerated_box"
      else:
          raise RuntimeError(...)
      ```
      Because `did_reroute is True`, the condition `if not did_reroute and not mismatched:` evaluates to **False**! The code enters the `else:` branch and raises `RuntimeError`, even though `mismatched` is empty!
    - *Fix:* If line 573 is adjusted to `if not mismatched:`, all 4 buildings pass immediately as `near_duplicate_vertex_tolerated_box` without fataling EnergyPlus.
    - *Expected Recovery:* **+4 buildings** (Lyon +1, Madrid +3).

---

### Category 5: `MISSING_OBSERVED_YEAR_BUILT` (Lyon 8 + Madrid 11 = 19 buildings) — Verdict: (a) Genuine Dead End

- **Exact Count:** 19 buildings (Lyon 8, Madrid 11: 7 alone + 4 combined with dwelling count missing).
- **Code Citation:** `openubem/semantic/european_archetype_mapping.py:74-83` (`_observed_year`).
- **Investigation:**
  - **Lyon (8 buildings):**
    - All 8 footprints carry `year_built: NaN` and `provenance_year_built: IGN_BDTOPO_MISSING`.
    - Examination of raw `surplus_tags` confirms that IGN BD-TOPO holds no `date_de_construction` or `date_d_achevement` from Fichiers Fonciers for these rows.
  - **Madrid (11 buildings):**
    - All 11 rows in `es_catastro_attribute_sidecar.csv` carry `catastro_local_id: NaN`, `year_built: NaN`, `n_dwellings: NaN`, with reason `NO_INTERSECTING_CATASTRO_RESIDENTIAL_BUILDING`.
    - Cross-referenced with `es_catastro_coverage_probe.json:251-253`: exactly 1,183 of 1,194 manifest rows intersected a Catastro residential building. The 11 failing rows are OSM footprints located where the Catastro INSPIRE BU layer has no overlapping residential polygon (e.g. inner courtyard annexes or slight cadastral parcel offsets).
- **Conclusion:** Genuine data absence in official cadastral registries. Cannot be resolved without fabricating data.

---

### Category 6: Bologna Census Section Ties (12) & No-Residential Sections (4) — 16 buildings

- **Exact Count:** 16 buildings (12 ties: 10 `CENSUS_SECTION_PERIOD_TIE_E8_E9`, 2 `CENSUS_SECTION_PERIOD_TIE_E9_E10`; 4 `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS`).
- **Code Citation:** `scripts/run_eu_s2_district_campaign.py:288-299` (`_it_rows`).
- **Investigation:**
  - **Census Ties (12 buildings) — Verdict: (c) Policy Question for Owner**
    - All 10 `E8_E9` ties belong to Census Section 1287, where the ISTAT 2011 census records exactly 3 buildings in E8 (pre-1919) and 3 in E9 (1919–1945).
    - Both `E9_E10` ties belong to Census Section 1266, where ISTAT records exactly 1 building in E9 (1919–1945) and 1 in E10 (1946–1960).
    - Centroid distance to candidate sections cannot resolve this because the tie is between two historical cohorts *within the same section*. Distance to adjacent sections would constitute spatial interpolation/guessing, violating project rules.
    - Owner could rule to break ties in favour of the older historical cohort (pre-1919) for Galvani's historic core (+12 buildings) or keep fail-closed.
  - **No Residential Buildings in Section (4 buildings) — Verdict: (a) Genuine Dead End**
    - Buildings: `28821` (Section 1253), `30835` (Section 1244), `81117` (Section 1244), `33610` (Section 1299).
    - Analysis of raw ISTAT microdata (`R08_indicatori_2011_sezioni.csv`): Sections 1244, 1253, and 1299 have resident population `P1 = 0`. While `E2` (residential buildings) equals 1, 1, and 2 respectively, ISTAT's statistical disclosure controls suppress all age breakdown counts (`E8` through `E16` are all 0).
    - Bologna municipal CTC (`c_a944ctc_edifici_pl`) carries geometry and height, but no construction year. The data does not exist in any open Italian source.

---

### Category 7: London `UNMAPPABLE_RESIDENTIAL_TYPE` (6 buildings) — Verdict: (b) Real Code Fix Exists

- **Exact Count:** 6 buildings.
- **Code Citation:** `scripts/run_eu_s2_district_campaign.py:192-197`:
  ```python
  if tag == "house":
      building_type = "TH" if bool(is_attached_series.loc[idx]) else "SFH"
  else:
      building_type = {"apartments": "AB", "detached": "SFH", "terrace": "TH"}.get(tag)
  if building_type is None:
      exclusions["UNMAPPABLE_RESIDENTIAL_TYPE"] += 1; continue
  ```
- **Investigation:**
  - Inspection of the 6 failing rows reveals that **all 6 buildings have OSM `building_tag == "residential"`**:
    - `way/1058438116`: 2 storeys, area 64.1 m² (8–10 Shaw Crescent)
    - `way/1058438118`: 2 storeys, area 64.3 m² (16–18 Shaw Crescent)
    - `way/1058438120`: 2 storeys, area 62.6 m² (24–26 Shaw Crescent)
    - `way/554859559`: 2 storeys, area 63.7 m² (4–6 Shaw Crescent)
    - `way/190348379`: 4 storeys, area 638.8 m² ("Pevensey House", Ben Jonson Road)
    - `way/204487525`: 7 storeys, area 377.3 m² ("Ravenscroft Court", Essian Street)
  - **Every single one of these 6 buildings has a valid observed EPC age band that does NOT straddle** (`H` -> GB.06, `G` -> GB.05, `G` -> GB.05, `E` -> GB.04, `L` -> GB.08, `G` -> GB.05) and **every one has an observed storey count** (2, 2, 2, 4, 7, 2).
  - They were excluded solely because `tag == "residential"` was omitted from `_gb_rows`.
  - Mapping generic `residential` tags by storey and adjacency (storeys <= 2 -> TH/SFH by adjacency; storeys >= 3 -> AB, exactly like Bologna lines 270–275 and Lyon) recovers all 6 buildings immediately.
- **Expected Recovery:** **+6 buildings** (London 389 -> 395).

---

### Category 8: `MISSING_OBSERVED_DWELLING_COUNT` (Lyon 1 + Madrid 1 = 2 buildings) — Verdict: (a) Genuine Dead End

- **Exact Count:** 2 buildings.
- **Code Citation:** `openubem/semantic/european_archetype_mapping.py:85-122` (`_observed_dwellings`).
- **Investigation:**
  - **Lyon:** `BATIMENT0000000240880398_part0`. BD-TOPO explicitly records `nombre_de_logements = "0.0"` (commercial/services secondary usage). Because the code requires `numeric > 0`, it correctly fails closed.
  - **Madrid:** `way/941927256`. Building tag is `house`, storeys = 1, year = 1910. The intersecting Catastro feature carried null dwellings.
- **Conclusion:** Genuine data absence; both buildings lack observed residential units in primary records.

---

### Category 9: Lyon `TYPOLOGY_SIGNALS_DISAGREE` Outliers (10 buildings) + Madrid (1 building) — Verdict: (c) Policy Question (Already Adjudicated)

- **Exact Count:** 11 buildings (Lyon 10, Madrid 1).
- **Code Citation:** `openubem/semantic/european_archetype_mapping.py:203`.
- **Investigation:**
  - Lyon: 8 buildings with `dwellings >= 15 & storeys <= 4`, and 2 buildings with `dwellings == 1 & storeys >= 5`.
  - Madrid: 1 building (`way/340701292`, house tag, 45 dwellings in 2 storeys).
  - *Status:* Already formally reviewed under `DECISION_REQUEST_D-EU-37` (§4, option 1) and scoped out as "too few to generalize a rule from." No new physical evidence exists to justify overriding that ruling.
- **Conclusion:** Retained as fail-closed exclusions per owner ruling.

---

## 3. Summary Decision Agenda for Project Owner

To maximize the EU-11 fleet toward 100 %, the following four action items are submitted to the project owner:

1. **Immediate Code Bug Fixes (Recovers +10 buildings):**
   - *Fix 1 (London Generic Tag):* Add `tag == "residential"` mapping in `_gb_rows` using footprint adjacency and storeys (<= 2 -> TH/SFH, >= 3 -> AB). **Recovers +6 buildings**.
   - *Fix 2 (IDF Tolerated Box Gate):* In `scripts/run_eu_s2_campaign.py:573`, change `if not did_reroute and not mismatched:` to `if not mismatched:` so that rerouted boxes with zero mismatched interzone surfaces are safely tolerated. **Recovers +4 buildings**.

2. **Policy Ruling: Typology Registry Gap 13–14 Dwellings (Recovers +38 buildings):**
   - Approve widening `derive_bdtopo_building_type` to map 13–14 dwellings: <= 4 storeys -> `MFH`, >= 5 storeys -> `AB`. **Recovers +38 buildings** (Lyon 37, Madrid 1).

3. **Policy Ruling: London EPC Period Straddles (Recovers +355 buildings):**
   - Approve majority-span allocation mapping RdSAP intervals to their predominant TABULA UK era (B -> GB.01, C -> GB.02, D -> GB.03, F -> GB.04, J -> GB.07, K -> GB.07). **Recovers +355 buildings**.

4. **Hard Ceilings (Unrecoverable without new external ingestion pipelines):**
   - 445 London buildings with no statutory EPC certificate.
   - 163 Madrid buildings with unpopulated WFS storey counts.
   - 13 buildings with true architectural courtyard voids causing EnergyPlus donut fatals.
   - 19 buildings with missing cadastral construction dates.
   - 16 Bologna buildings with ISTAT census section suppression or ties.
