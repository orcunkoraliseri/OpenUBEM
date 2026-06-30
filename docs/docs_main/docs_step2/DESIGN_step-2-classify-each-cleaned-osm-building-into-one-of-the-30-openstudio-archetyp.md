# Step 2 — OSM Building → OpenStudio 29-Type Archetype Classifier

### OpenUBEM Stage 2 / Module 03: `openubem/semantic/building_classifier.py` — convert the cleaned 23-column GeoDataFrame from Step 1 into an archetype-labelled GeoDataFrame ready for the construction/loads imputer

> **Slug:** `step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp` &nbsp;•&nbsp; **First created:** `2026-05-06` &nbsp;•&nbsp; **Latest revision:** `2026-05-06` &nbsp;•&nbsp; **Status:** APPROVED &nbsp;•&nbsp; **Mode:** new
>
> Sections 1–9 are append-once, edit-never after first APPROVED verdict. Section 10 (Progress Log) is owned by the downstream `/run` reporter. All `/design` re-run changes are recorded under Section 11 — Revision Log.
>
> **Scope rule.** This document covers exactly one umbrella step — Stage 2 / Module 03 of OpenUBEM (`semantic/building_classifier.py`). The OSM-tag → use-class normaliser, the (use_class × area-bin × levels-bin) primary classifier, the three-tier confidence assignment, the fallback chain, and the schema-extension contract are *internal* sub-stages of this step and live under §3. ASHRAE/IECC/NECB construction-set lookup (Module 04), internal-load assignment (Module 05), schedule generation (Module 06), and KDE/PDE/ML imputation (Module 06b) are **out of scope** here — they are downstream consumers of this step's output.
>
> **Vocabulary count note.** The Technical Pipeline §5 prose says "30 types across 12 sectors", but its own per-sector enumeration (Office 6 + Retail 3 + Food 2 + Lodging 2 + Residential 2 + Healthcare 2 + Education 3 + Government 1 + DataCenter 4 + Research 1 + Industrial 1 + HighRise 2) lists exactly **29 unique archetype IDs**. The slug retains the legacy "30" string for tracking continuity; this document standardises on **29** throughout — see §3B.

---

## 1. Aim

This step transforms the 23-column cleaned OSM GeoDataFrame produced by Step 1 (`01_buildings_clean.gpkg`, decision row 54 in `.claude/design_state.md`) into a **29-type-archetype-labelled GeoDataFrame** by deterministically assigning each row to exactly one of the OpenStudio Standards building types catalogued in `inputs/reports/OpenStudio Building Types and Templates.pdf`. It is the first link in OpenUBEM's Stage 2 (Semantic Enrichment) chain: every downstream module — construction sets (`construction_sets.py`, Module 04), internal-load densities (`loads.py`, Module 05), schedules (`schedules.py`, Module 06), KDE/PDE/ML imputation (`imputation.py`, Module 06b), IDF assembly (`idf/builder.py`, Module 09), and HVAC template selection (`idf/hvac.py`, Module 10b) — is keyed on the `archetype_id` column this step produces (`inputs/aim/OpenUBEM_Technical_Pipeline.md` §5 Module 03; spec sentence: "Map OSM tags to the full OpenStudio 30-type library"). Skipping or shortcutting this step would force the imputer to operate without a typed prior, collapsing all buildings into a single distribution and nullifying the archetype-stratified KDE/PDE design that decision row 33 ratifies. Crucially, this step is **rule-based and deterministic** under the active Phase-1 architectural decision row 42 ("Rule-based archetype classification (Phase 1) — interface-stable for Phase-2 ML drop-in"); the function signature, output columns, and provenance vocabulary are designed so that a Phase-2 `ml_classify_building()` can replace the rule engine without breaking any downstream module.

---

## 2. Inputs

| Artifact | Source | Dtype | Shape | Notes |
|---|---|---|---|---|
| `01_buildings_clean.gpkg` (layer `buildings`) | Step 1 output (`openubem/acquisition/osm_fetcher.py`) | GeoPackage with 23 binding columns | `(N, 23)`, typical `N ≈ 200–5,000` per km² | See full schema below. Decision rows 47–66 in `design_state.md` lock the contract. |
| `OpenStudio 29-type lookup table` | Bundled `openubem/data/openstudio_archetypes.json` (this step) | dict[str, dict] | 29 entries | Static; enumerated in §3B. Sourced verbatim from `inputs/reports/OpenStudio Building Types and Templates.pdf` §1. |
| `OSM_TO_USE_CLASS` table | Bundled `openubem/data/osm_to_use_class.json` (this step) | dict[str, str] | ~70 entries | OSM `building=*`/`amenity=*`/`shop=*`/`office=*` tag → 6 canonical use classes (residential / commercial / industrial / institutional / mixed / unknown). §3A. |
| `archetype_size_rules.json` | Bundled (this step) | dict[str, list[dict]] | one bin-rule list per use-class | (footprint_area_m2, levels) → archetype_id rule table. §3C. |

### Step 1 → Step 2 binding input schema (23 columns, fixed order)

Read verbatim from the Step 1 DESIGN doc §3F (decision row 54). This is what `classify_building_gdf()` receives.

| # | Group | Column | Dtype | Notes / used by Step 2? |
|---|---|---|---|---|
| 1 | Geometry | `geometry` | shapely Polygon (UTM) | Yes — passed through, also used for §5.2 distribution checks |
| 2 | Identity | `osm_id` | `str` | Yes — preserved as join key |
| 3 | Identity | `crs_utm` | `str` (e.g. `"EPSG:32619"`) | No — pass-through |
| 4 | Raw OSM | `building_tag` | `str` (lower-cased; `""` if NaN) | **Yes — primary input to §3A** |
| 5 | Raw OSM | `function_tag` | `str` (`""` if NaN; `amenity` > `shop` > `office` priority) | **Yes — primary input to §3A** |
| 6 | Raw OSM | `levels` | `Int64` (nullable) | **Yes — input to §3C bin selection** |
| 7 | Raw OSM | `height_m` | `float64` | Used only for fallback `levels` derivation (§3D) |
| 8 | Raw OSM | `year_built` | `Int64` (nullable) | No — Module 04 consumes it for vintage selection |
| 9 | Raw OSM | `postcode` | `str` or `None` | No |
| 10 | Raw OSM | `underground` | `Int64` (default 0) | No |
| 11 | Raw OSM | `roof_shape` | `str` (`""` if NaN) | No |
| 12 | Raw OSM | `roof_height_m` | `float64` | No |
| 13 | Computed | `footprint_area_m2` | `float64` (≥ 20.0) | **Yes — input to §3C bin selection** |
| 14 | Computed | `perimeter_m` | `float64` | No |
| 15 | Surplus | `surplus_tags` | `str` (JSON, non-binding per Q6) | Read-only audit; not keyed on |
| 16 | Provenance | `provenance_levels` | enum-string | **Yes — propagated into confidence calc (§3D)** |
| 17 | Provenance | `provenance_height_m` | enum-string | Yes — same |
| 18 | Provenance | `provenance_year_built` | enum-string | No |
| 19 | Provenance | `provenance_building_tag` | enum-string (`OSM_OBSERVED` / `OSM_GENERIC`) | **Yes — `OSM_GENERIC` forces fallback branch (§3D)** |
| 20 | Provenance | `provenance_function_tag` | enum-string | **Yes — `OSM_MISSING` downgrades confidence one tier** |
| 21 | Provenance | `provenance_postcode` | enum-string | No |
| 22 | Provenance | `provenance_geometry` | enum-string | No |
| 23 | Quality | `data_quality_flag` | comma-joined token string (closed vocab of 7) | **Yes — `generic_tag` forces fallback; `no_floors` triggers levels imputation in §3D** |

> Upstream pipeline step: **Step 1 — OSM Building Footprint Ingest** (`openubem/acquisition/osm_fetcher.py`, decision row 53). Downstream consumers (in execution order): `construction_sets.get_construction_set(building_type=archetype_id, ...)` → `loads.get_loads(building_type=archetype_id, ...)` → `schedules.get_schedule_definitions(archetype_id)` → `imputation.impute_column(...)` (uses `archetype_id` as a stratum key) → `idf/builder.BuildingIDF(building_type=archetype_id, ...)`.

---

## 3. Pipeline

The step proceeds through **five internal sub-stages in fixed order**: 3A normalises raw OSM tag tokens to a canonical use-class; 3B loads the OpenStudio 29-type taxonomy and pins it as the closed output vocabulary; 3C runs the primary `(use_class × area_bin × levels_bin) → archetype_id` rule table; 3D assigns a three-tier confidence score and drives the fallback chain when tags are missing or generic; 3E assembles the output GeoDataFrame by appending three new columns (`archetype_id`, `archetype_confidence`, `archetype_source`) to the 23-column upstream schema. Style anchor: STEP 3 of `Examples/00_GSS_Occupancy_Pipeline.md`.

The public API is a single function:

```python
# openubem/semantic/building_classifier.py

def classify_building_gdf(
    gdf: gpd.GeoDataFrame,                # Step 1 output, 23 columns
    high_rise_levels_threshold: int = 20, # → TallBuilding boundary
    super_tall_levels_threshold: int = 40,# → SuperTallBuilding boundary
    floor_to_floor_m: float = 3.5,        # for height→levels fallback
) -> gpd.GeoDataFrame:                    # 26 columns (23 + 3)
    """Per-row OSM → OpenStudio archetype classification.
    Idempotent and deterministic: same input GeoDataFrame ⇒ same output.
    Adds exactly three columns; never mutates the 23 binding upstream columns."""
```

A per-row helper `classify_building(row: pd.Series) -> tuple[str, str, str]` returning `(archetype_id, archetype_confidence, archetype_source)` is the unit-of-work for vectorised application and unit testing.

### 3A — OSM tag → canonical `use_class` normalisation

Raw OSM `building_tag` and `function_tag` values come from an open-vocabulary tagging system; the same building can be tagged `building=apartments` or `building=residential` or `building=house`, and a coffee shop appears as `amenity=cafe`, `shop=coffee`, or `building=cafe`. Step 2 first collapses this open vocabulary to a closed set of **six canonical use classes** before any size/levels reasoning runs. This separation keeps the size-tier rule table (§3C) small (six rows × ~3 size bins × ~3 level bins) instead of hundreds of OSM-token-specific rules, and lets a Phase-2 ML classifier swap into 3A only without touching 3C.

```python
USE_CLASSES = {"residential", "commercial", "industrial",
               "institutional", "mixed", "unknown"}
```

The bundled `OSM_TO_USE_CLASS` table (extracted directly from the Technical Pipeline §5 Module 03 mapping table and the `OSM_TO_OPENSTUDIO_TYPE` dict at lines 729–801 of `inputs/aim/OpenUBEM_Technical_Pipeline.md`):

| Raw OSM token | Found in | use_class |
|---|---|---|
| `apartments`, `residential`, `house`, `detached`, `semidetached_house`, `terrace`, `dormitory`, `bungalow` | `building_tag` | `residential` |
| `office`, `commercial`, `retail`, `shop`, `supermarket`, `strip_mall`, `mall`, `kiosk`, `restaurant`, `fast_food`, `cafe`, `bar`, `pub`, `hotel`, `motel`, `guest_house`, `bank`, `cinema` | `building_tag` or `function_tag` | `commercial` |
| `warehouse`, `industrial`, `manufacture`, `factory`, `data_center`, `datacenter`, `hangar` | `building_tag` or `function_tag` | `industrial` |
| `school`, `university`, `college`, `kindergarten`, `hospital`, `clinic`, `government`, `public`, `civic`, `courthouse`, `library`, `museum`, `church`, `cathedral`, `chapel`, `temple`, `synagogue`, `mosque`, `laboratory`, `research`, `fire_station`, `police` | `building_tag` or `function_tag` | `institutional` |
| Two or more incompatible classes co-present on same row (e.g. `building=apartments` + `function_tag=shop`) | both | `mixed` |
| `yes`, `""` (empty), or unmapped/exotic token | `building_tag` | `unknown` |

The resolver runs **function_tag first, building_tag second** (function tags are typically more specific, e.g. `amenity=hospital` is a stronger signal than `building=hospital`), with priority order inside `function_tag` already fixed by Step 1 (`amenity > shop > office`, decision row 53 §3B). When the two tokens disagree on use class, `use_class = "mixed"` — Phase 1 routes mixed-use to the dominant tag's class for archetype assignment but tags `archetype_confidence = "MEDIUM"` (§3D).

> **Why this approach:** Two-stage normalisation (OSM → use_class → archetype_id) is the design that the Technical Pipeline §5 explicitly mandates ("Priority: function_tag → building_tag → footprint+floors heuristic", line 807) and that decision row 42 ratifies. Collapsing to six classes first matches Iseri et al. (2025), which demonstrated that a small closed taxonomy of building uses, combined with size/age tiers, produces archetype-level KDE distributions sufficient for zone-resolved UBEM (`inputs/aim/OpenUBEM_Aim_Document.md` §4 methodological foundation, citing Iseri et al. 2025 Energy & Buildings 337:115620). Rejected alternative: direct OSM-token → OpenStudio-type dict (the spec's draft `OSM_TO_OPENSTUDIO_TYPE` at lines 729–801 of the Technical Pipeline) — this conflates use-class resolution with size-tier resolution and is why the spec dict maps `office` → `MediumOffice` unconditionally, ignoring the SmallOffice/LargeOffice tiers that the OpenStudio 29-type taxonomy distinguishes; our two-stage design recovers all three office tiers (§3C). Rejected alternative: free-text NLP on `surplus_tags` (e.g. `description=*`, `name=*`) — surplus_tags is non-binding per Q6 (decision row 65), so keying on it would break the schema contract.

### 3B — OpenStudio 29-type taxonomy (closed output vocabulary)

The output `archetype_id` column draws from exactly the 29 unique building types catalogued in `inputs/reports/OpenStudio Building Types and Templates.pdf` §1. The base class `_Prototype` is excluded as it is "Internal use only" (PDF §1, p.2 final bullet). The taxonomy is bundled as `openubem/data/openstudio_archetypes.json` and pinned to a SemVer for change auditing.

> **Vocabulary count.** The Technical Pipeline §5 prose at line 611 says "30 types across 12 sectors", but the spec's own per-sector enumeration (lines 615–722) lists 6 + 3 + 2 + 2 + 2 + 2 + 3 + 1 + 4 + 1 + 1 + 2 = **29 unique archetype IDs**. The "30" prose count is a spec-author miscount; this document uses the count derived directly from the enumeration. The Phase-1 fallback sentinel (rule 17 in §3C) reuses the existing `MediumOffice` archetype rather than adding a synthetic 30th — see the FALLBACK_DEFAULT note below the table.

| # | Sector (PDF §1) | OpenStudio archetype_id | Default size signature | Default standard family |
|---|---|---|---|---|
| 1 | Office | `SmallOffice` | < 500 m² floor area | ASHRAE 90.1 |
| 2 | Office | `SmallOfficeDetailed` | < 500 m², modeller opts in | ASHRAE 90.1 |
| 3 | Office | `MediumOffice` | 500–4,000 m² (also Phase-1 FALLBACK_DEFAULT sentinel — see note) | ASHRAE 90.1 |
| 4 | Office | `MediumOfficeDetailed` | 500–4,000 m², modeller opts in | ASHRAE 90.1 |
| 5 | Office | `LargeOffice` | > 4,000 m² | ASHRAE 90.1 |
| 6 | Office | `LargeOfficeDetailed` | > 4,000 m², modeller opts in | ASHRAE 90.1 |
| 7 | Retail | `RetailStandalone` | generic retail/shop | ASHRAE 90.1 |
| 8 | Retail | `RetailStripmall` | OSM `strip_mall` or elongated form factor | ASHRAE 90.1 |
| 9 | Retail | `SuperMarket` | OSM `supermarket` or footprint > 1,500 m² + retail | ASHRAE 90.1 |
| 10 | Food Service | `FullServiceRestaurant` | OSM `restaurant` | ASHRAE 90.1 |
| 11 | Food Service | `QuickServiceRestaurant` | OSM `fast_food`, `cafe` | ASHRAE 90.1 |
| 12 | Lodging | `SmallHotel` | < 4 floors lodging | ASHRAE 90.1 |
| 13 | Lodging | `LargeHotel` | ≥ 4 floors lodging | ASHRAE 90.1 |
| 14 | Residential | `MidriseApartment` | < 9 floors residential | IECC 2021 |
| 15 | Residential | `HighriseApartment` | ≥ 9 floors residential | IECC 2021 |
| 16 | Healthcare | `Hospital` | OSM `hospital` | ASHRAE 90.1 |
| 17 | Healthcare | `Outpatient` | OSM `clinic`, small healthcare | ASHRAE 90.1 |
| 18 | Education | `PrimarySchool` | OSM `school` (default), `kindergarten` | ASHRAE 90.1 |
| 19 | Education | `SecondarySchool` | OSM `school` + footprint ≥ 5,000 m² OR explicit secondary tag | ASHRAE 90.1 |
| 20 | Education | `College` | OSM `university`, `college` | ASHRAE 90.1 |
| 21 | Government | `Courthouse` | OSM `government`, `public`, `courthouse`, `civic` | ASHRAE 90.1 |
| 22 | Data Center | `SmallDataCenterHighITE` | OSM `data_center` + < 500 m² + High-ITE flag (default) | ASHRAE 90.1 |
| 23 | Data Center | `SmallDataCenterLowITE` | OSM `data_center` + < 500 m² + Low-ITE flag | ASHRAE 90.1 |
| 24 | Data Center | `LargeDataCenterHighITE` | OSM `data_center` + ≥ 500 m² + High-ITE (default) | ASHRAE 90.1 |
| 25 | Data Center | `LargeDataCenterLowITE` | OSM `data_center` + ≥ 500 m² + Low-ITE flag | ASHRAE 90.1 |
| 26 | Research | `Laboratory` | OSM `laboratory`, `research` | ASHRAE 90.1 |
| 27 | Industrial | `Warehouse` | OSM `warehouse`, `industrial`, `manufacture`, `factory`, `hangar` | ASHRAE 90.1 |
| 28 | High-Rise | `TallBuilding` | levels ≥ 20 (any use_class except residential, industrial, and pure data-center) | ASHRAE 90.1 |
| 29 | High-Rise | `SuperTallBuilding` | levels ≥ 40 (same exemptions as TallBuilding) | ASHRAE 90.1 |

> The base class `_Prototype` is **excluded** from the closed output vocabulary because the PDF flags it "Internal use only". The Phase-1 fallback sentinel for unclassifiable rows is `MediumOffice` (the existing row 3 archetype) paired with `archetype_confidence = "LOW"` and `archetype_source = "FALLBACK_DEFAULT"` (§3D); rejecting `_Prototype` as a sentinel is deliberate — Module 04 has no construction set indexed under `_Prototype`, so an unknown row routed there would crash the pipeline. Reusing `MediumOffice` (rather than coining a synthetic 30th archetype) keeps every value in `archetype_id` resolvable by Module 04 without any special-case branch; the `archetype_source = "FALLBACK_DEFAULT"` token is what audit code keys on, not a separate archetype ID. See OQ-5 in §7 for the alternative (a synthetic 30th `OpenUBEMUnknown` archetype) which is deferred for Phase-2 consideration.

> **Why this approach:** Pinning the closed 29-archetype vocabulary as bundled JSON is the same provenance-tracking discipline as the seven-token `data_quality_flag` vocabulary in Step 1 (decision row 50): any change to the closed set is a versioned schema bump. The list of 29 is taken verbatim from `inputs/reports/OpenStudio Building Types and Templates.pdf` §1 (the only source of truth — OpenStudio Standards itself, the Ruby gem the PDF describes). Rejected alternative: use the DOE-only 16-prototype subset that the Aim document §3.1 enumerates — it omits TallBuilding/SuperTallBuilding (no Phase-1 path for >20-storey buildings, which exist in every studied US city), Laboratory and DataCenter variants (specialised loads dominate the EUI), and Courthouse — all of which the Technical Pipeline §5 explicitly enumerates. Rejected alternative: roll our own taxonomy by collapsing rare types (e.g. fold `SmallDataCenterLowITE` into `LargeDataCenterLowITE`) — this hides the ITE-load distinction that determines data-center EUI by an order of magnitude and is exactly what the OpenStudio source taxonomy was designed to expose.

### 3C — Primary classifier: (use_class × area_bin × levels_bin) → archetype_id

Given `use_class` from §3A, `footprint_area_m2` from Step 1 column 13, and `levels` from Step 1 column 6, the primary classifier resolves the OpenStudio archetype via a deterministic lookup. Area and level bins are encoded as a single rule table per use-class.

#### Area bins

The Technical Pipeline §5 Module 03 `select_prototype_size()` pseudocode (lines 819–830) pins the office tier boundaries: `< 500 m² → Small`, `500–4,000 m² → Medium`, `> 4,000 m² → Large`. The same three-bin partition is applied to all size-stratified sectors (Office, DataCenter, and as a tie-breaker for retail vs supermarket). For sectors where size is not the OpenStudio differentiator (Healthcare, Education, Government, Research, Industrial, Food Service), the bin is `any`.

| Bin | Range | Used for |
|---|---|---|
| `S` (small) | `footprint_area_m2 < 500` | Office, DataCenter, Retail (default Standalone) |
| `M` (medium) | `500 ≤ footprint_area_m2 < 4000` | Office (Medium), Retail (SuperMarket if `supermarket` token), DataCenter (Large) |
| `L` (large) | `footprint_area_m2 ≥ 4000` | Office (Large), DataCenter (Large), Education (SecondarySchool if `school` + L) |
| `*` (any) | unconstrained | Healthcare, Government, Lodging tier from levels, Residential tier from levels, FoodService, Research, Industrial |

The 500 / 4,000 m² boundaries match the `select_prototype_size()` spec. Footprint area is used as a proxy for floor area; for multi-storey buildings the rule applies to the **single-floor footprint**, not the total floor area, because OpenStudio's prototype "Small/Medium/Large" classification originated from DOE Reference Buildings which are size-classified by total floor area but the OSM signal we have is footprint × levels. Since the office vintage prototypes have characteristic footprint (SmallOffice ≈ 511 m² total floor / 1 floor; MediumOffice ≈ 4,982 m² total / 3 floors ≈ 1,660 m²/floor; LargeOffice ≈ 46,320 m² total / 12 floors ≈ 3,860 m²/floor — DOE Reference Buildings public dimensions), the footprint-only proxy keeps the spec's 500/4,000 m² boundaries operationally correct for buildings of typical vintage shape and avoids the circular dependency where computing total floor area itself depends on the `levels` value that may be missing.

#### Levels bins

| Bin | Range | Used for |
|---|---|---|
| `<4` | `levels < 4` | Lodging tier (SmallHotel) |
| `≥4` | `levels ≥ 4` (when `<20`) | Lodging tier (LargeHotel) |
| `<9` | `levels < 9` | Residential tier (MidriseApartment) |
| `≥9` | `levels ≥ 9` (when `<20`) | Residential tier (HighriseApartment) |
| `≥20` | `levels ≥ 20` (and `< 40`) | TallBuilding override (any non-residential, non-industrial, non-pure-data-center) |
| `≥40` | `levels ≥ 40` | SuperTallBuilding override (same exemptions) |

The thresholds `<4` (Hotel), `<9` (Apartment), `≥20` (TallBuilding), `≥40` (SuperTallBuilding) are taken verbatim from the Technical Pipeline §5 Module 03 `select_prototype_size()` and `classify_building()` pseudocode (lines 809–810, 825–828).

#### Full rule table (resolution order — first match wins)

The classifier evaluates rules in this order. Rule (1) — TallBuilding override — runs **before** size/levels-based class routing because the Technical Pipeline §5 explicitly states this as a heuristic ("`n_floors > 20 → TallBuilding`", line 809) and because a 50-storey commercial tower is energetically more like a `TallBuilding` (mixed-mode HVAC, elevator loads, central plant) than a `MediumOffice` scaled to many floors. **Three use-classes are explicitly exempt from the TallBuilding override**: `residential` (a 25-storey apartment block stays `HighriseApartment` per OpenStudio convention), `industrial` (a tall warehouse remains `Warehouse`; OpenStudio has no high-rise industrial archetype), and pure data centers (the four DataCenter archetypes already capture their EUI characteristics, so TallBuilding routing would discard the ITE-load distinction).

All Boolean expressions below use **explicit parentheses** to remove operator-precedence ambiguity. Where a rule combines an `OR` of two tag conditions with an `AND` size/levels condition, the tag-OR is parenthesised first.

| # | Trigger | archetype_id | archetype_source token |
|---|---|---|---|
| 1a | `(levels ≥ 40) AND (use_class ∈ {commercial, institutional, mixed, unknown})` | `SuperTallBuilding` | `RULE_HIGHRISE` |
| 1b | `(20 ≤ levels < 40) AND (use_class ∈ {commercial, institutional, mixed, unknown})` | `TallBuilding` | `RULE_HIGHRISE` |
| 2a | `(use_class == residential) AND (levels ≥ 9)` | `HighriseApartment` | `RULE_RESIDENTIAL_TIER` |
| 2b | `(use_class == residential) AND (levels < 9)` (incl. NaN-imputed via §3D) | `MidriseApartment` | `RULE_RESIDENTIAL_TIER` |
| 3a | `(function_tag ∈ {hotel, motel, guest_house}) AND (levels ≥ 4)` | `LargeHotel` | `RULE_LODGING_TIER` |
| 3b | `(function_tag ∈ {hotel, motel, guest_house}) AND (levels < 4)` | `SmallHotel` | `RULE_LODGING_TIER` |
| 4a | `function_tag == restaurant` | `FullServiceRestaurant` | `RULE_FUNCTION_TAG` |
| 4b | `function_tag ∈ {fast_food, cafe, bar, pub}` | `QuickServiceRestaurant` | `RULE_FUNCTION_TAG` |
| 5a | `(function_tag == hospital) OR (building_tag == hospital)` | `Hospital` | `RULE_FUNCTION_TAG` |
| 5b | `(function_tag ∈ {clinic, doctors, dentist}) OR (building_tag == clinic)` | `Outpatient` | `RULE_FUNCTION_TAG` |
| 6a | `(function_tag ∈ {university, college}) OR (building_tag ∈ {university, college})` | `College` | `RULE_FUNCTION_TAG` |
| 6b | `((function_tag == "school") OR (building_tag == "school")) AND (footprint_area_m2 ≥ 5000)` | `SecondarySchool` | `RULE_FUNCTION_TAG_SIZE` |
| 6c | `((function_tag ∈ {"school", "kindergarten"}) OR (building_tag ∈ {"school", "kindergarten"})) AND (footprint_area_m2 < 5000)` | `PrimarySchool` | `RULE_FUNCTION_TAG` |
| 7 | `(function_tag ∈ {government, public, courthouse, civic}) OR (building_tag ∈ {government, public, courthouse, civic})` | `Courthouse` | `RULE_FUNCTION_TAG` |
| 8 | `(function_tag ∈ {laboratory, research}) OR (building_tag ∈ {laboratory, research})` | `Laboratory` | `RULE_FUNCTION_TAG` |
| 9a | `((function_tag ∈ {data_center, datacenter}) OR (building_tag ∈ {data_center, datacenter})) AND (footprint_area_m2 < 500)` | `SmallDataCenterHighITE` (default High-ITE per spec line 800) | `RULE_FUNCTION_TAG_SIZE` |
| 9b | `((function_tag ∈ {data_center, datacenter}) OR (building_tag ∈ {data_center, datacenter})) AND (footprint_area_m2 ≥ 500)` | `LargeDataCenterHighITE` | `RULE_FUNCTION_TAG_SIZE` |
| 10 | `(function_tag ∈ {warehouse, industrial, manufacture, factory, hangar}) OR (building_tag ∈ {warehouse, industrial, manufacture, factory, hangar})` | `Warehouse` | `RULE_FUNCTION_TAG` |
| 11a | `(building_tag == supermarket) OR (function_tag == supermarket)` | `SuperMarket` | `RULE_FUNCTION_TAG` |
| 11b | `(building_tag == strip_mall) OR (function_tag == strip_mall)` | `RetailStripmall` | `RULE_FUNCTION_TAG` |
| 11c | `(function_tag ∈ {retail, shop, mall, kiosk}) OR (building_tag ∈ {retail, shop, mall, kiosk})` | `RetailStandalone` | `RULE_FUNCTION_TAG` |
| 12a | `(use_class == commercial) AND (footprint_area_m2 < 500) AND (no specific tag matched above)` | `SmallOffice` | `RULE_USE_CLASS_SIZE` |
| 12b | `(use_class == commercial) AND (500 ≤ footprint_area_m2 < 4000) AND (no specific tag matched above)` | `MediumOffice` | `RULE_USE_CLASS_SIZE` |
| 12c | `(use_class == commercial) AND (footprint_area_m2 ≥ 4000) AND (no specific tag matched above)` | `LargeOffice` | `RULE_USE_CLASS_SIZE` |
| 13 | `(use_class == industrial) AND (no specific tag)` | `Warehouse` | `RULE_USE_CLASS` |
| 14 | `(use_class == institutional) AND (no specific tag)` | `Courthouse` (treated as generic civic) | `RULE_USE_CLASS` |
| 15 | `(use_class == mixed) AND (levels ≥ 9)` | route to dominant tag's residential tier (`HighriseApartment`) | `RULE_MIXED_USE` |
| 16 | `(use_class == mixed) AND (levels < 9)` | `MediumOffice` (mixed-use Phase-1 default; commercial wins ties) | `RULE_MIXED_USE` |
| 17 | `use_class == unknown` (after fallback in §3D) | `MediumOffice` | `FALLBACK_DEFAULT` |

The `_Detailed` office variants (`SmallOfficeDetailed`, `MediumOfficeDetailed`, `LargeOfficeDetailed`) are **not assigned by the rule table**; they are an opt-in modeller preference (the OpenStudio PDF describes them as "varying levels of modeling complexity") and Module 04 selects them only when the user passes `--detailed-office` to the top-level API. The rule table outputs the non-Detailed variants exclusively, which is consistent with the spec's `OSM_TO_OPENSTUDIO_TYPE` dict (Technical Pipeline lines 729–801) using `MediumOffice` rather than `MediumOfficeDetailed`.

> **Why this approach:** A first-match-wins rule list with explicit ordering is deterministic, traceable (every classification carries an `archetype_source` token naming the rule that fired), and matches the spec's "Priority: function_tag → building_tag → footprint+floors heuristic" comment (Technical Pipeline line 807). The TallBuilding override is intentionally **before** the residential tier check for non-residential uses but **after** for residential, because a residential tower remains a `HighriseApartment` per OpenStudio convention — `HighriseApartment` is the residential high-rise prototype catalogued in `inputs/reports/OpenStudio Building Types and Templates.pdf` §1 Residential row, paired with the IECC residential pathway (decision row 33's IECC 2021 stack); routing tall apartments to `TallBuilding` (an ASHRAE 90.1 commercial-construction archetype) would lose the IECC residential construction-set assignment in Module 04. Industrial and pure-data-center exemptions follow analogous reasoning: each has a sector-specific construction/loads pathway in Modules 04/05 that the TallBuilding ASHRAE pathway would override. Rejected alternative: a single `OSM_TO_OPENSTUDIO_TYPE` flat dict, as drafted in the Technical Pipeline (lines 729–801) — this dict maps `office → MediumOffice` unconditionally, losing the SmallOffice/LargeOffice tiers, and maps `hotel → LargeHotel` unconditionally, losing SmallHotel; the spec itself acknowledges this in the `select_prototype_size()` function which would resolve the ambiguity but is not wired to the dict. Our rule table integrates `select_prototype_size` and `classify_building` into one pass. Rejected alternative: train a Random Forest on a labelled OSM-archetype dataset (cf. `inputs/papers/comparing-domain-expert-and-machine-learning-data-enrichment-of-building-registry.md`, where an expert decision tree achieved 89% accuracy and Random Forest matched it on Slovenian wall-type prediction with 416 training rows) — Phase-1 decision row 42 explicitly defers ML to Phase 2; the rule table is the interface contract the Phase-2 ML module will satisfy.

### 3D — Confidence scoring and fallback chain

Three-tier confidence is assigned per row using the upstream `provenance_*` columns and which rule fired. The output value populates the new `archetype_confidence` column.

| Tier | Trigger | Rationale |
|---|---|---|
| `HIGH` | (a) `provenance_function_tag == OSM_OBSERVED` AND a function-tag rule (4a–11c) fired AND `provenance_levels == OSM_OBSERVED` whenever the rule reads `levels` (3a, 3b), OR (b) `provenance_building_tag == OSM_OBSERVED` AND a building_tag-direct rule fired AND `provenance_levels == OSM_OBSERVED` for any rule that reads `levels` (1a, 1b, 2a, 2b) | Direct semantic tag match with no imputed inputs |
| `MEDIUM` | (a) Rules 12a–12c (use_class + size, no specific function tag), OR (b) any rule fired but `provenance_levels == OSM_MISSING` AND a levels-based rule was used (`levels` was imputed via height÷3.5 fallback in this sub-stage) — **explicitly including rules 1a/1b TallBuilding override** when the triggering `levels` value was imputed, OR (c) rules 15–16 (mixed-use), OR (d) `provenance_function_tag == OSM_MISSING` AND `provenance_building_tag == OSM_OBSERVED` AND building_tag was specific | Partial signal: tag-or-size, not both |
| `LOW` | (a) Rule 17 (FALLBACK_DEFAULT), OR (b) `provenance_building_tag == OSM_GENERIC` AND no function_tag, OR (c) `data_quality_flag` contains `generic_tag` AND `function_tag == ""` | No usable semantic tag; archetype is a default, not a derivation |

#### Levels imputation fallback (when `levels` is NaN)

Rules 1, 2, and 3 read `levels`. When the upstream cell is NaN (`Int64` null, surfaced via `data_quality_flag` token `no_floors`), Step 2 derives `levels` locally:

```python
def _impute_levels(row, floor_to_floor_m=3.5) -> tuple[int, str]:
    """Return (imputed_levels, provenance_token).

    Invariant: this helper is *read-only* with respect to the 23 binding
    upstream columns. It returns the imputed integer and a provenance
    token for inclusion in archetype_source. It does NOT write to
    provenance_levels (which is upstream column 16, byte-identical to
    Step 1 input by row-level guarantee #4 in §4).
    """
    if pd.notna(row["levels"]):
        return int(row["levels"]), "OSM_OBSERVED"
    if pd.notna(row["height_m"]) and row["height_m"] > 0:
        # height-based heuristic; rounded down so 6.9 m → 1 storey, 7.0 m → 2 storeys
        return max(1, int(row["height_m"] // floor_to_floor_m)), "HEURISTIC_HEIGHT"
    return 1, "HEURISTIC_DEFAULT"   # last-resort assumption
```

The `HEURISTIC_HEIGHT` and `HEURISTIC_DEFAULT` tokens are recorded in `archetype_source` (a comma-joined extension to the rule token, e.g. `RULE_RESIDENTIAL_TIER,HEURISTIC_HEIGHT`) so that downstream auditing can trace exactly how the input was reconstructed. **Critical invariant: `_impute_levels()` does not mutate `provenance_levels` (upstream column 16) or any other binding upstream column.** The imputed levels value is a transient classifier-internal quantity; its only persistent record is the `HEURISTIC_*` token in `archetype_source`. This preserves row-level guarantee #4 in §4 (the 23 upstream columns are bit-identical to the input) and means a downstream caller that re-reads `provenance_levels` still sees `OSM_MISSING` for the original cell — exactly what an auditor wants to know.

The 3.5 m floor-to-floor default is the same one the Technical Pipeline §2 names ("If both absent, default floor-to-floor of 3.5 m applied", line 119) and that Module 09 `BuildingIDF.set_geometry()` uses. The provenance code `HEURISTIC` is already in the canonical Stage-2 vocabulary (Technical Pipeline §12, decision row 62 vocabulary), so this token is schema-legal.

#### Generic-tag fallback (rule 17 and the 100%-generic-neighbourhood case)

When `data_quality_flag` contains `generic_tag` (`building=yes`, no function tag) — Step 1's WARN-and-flow case (decision row 63) — `use_class` resolves to `unknown` and rule 17 fires: `archetype_id = "MediumOffice"`, `archetype_confidence = "LOW"`, `archetype_source = "FALLBACK_DEFAULT"`. The rationale for `MediumOffice` as the default is twofold: (i) it is the most populous archetype in DOE Reference Buildings prototypes for typical US urban areas, and (ii) it is the spec-default in the existing `OSM_TO_OPENSTUDIO_TYPE` dict for `office` and `commercial` (Technical Pipeline lines 733, 735). When **every** row in a neighbourhood is generic (Step 1's `all_generic_neighbourhood` warning condition), Step 2 emits a second structured warning to `openubem.semantic` logger with payload `{"event": "all_fallback_archetype", "n_rows": int, "archetype_id": "MediumOffice"}` so that the user is aware that the neighbourhood's entire archetype distribution is a default — Stage 2's imputer (`imputation.py`) can then choose to fall through to the PDE branch (full uniform sampling within ASHRAE bounds) rather than fitting a degenerate KDE on a single archetype.

> **Why this approach:** Three tiers (not four, not continuous) match the upstream `data_quality_flag` discipline: a fixed, small, closed vocabulary is easier for downstream filters and report templates to consume than a continuous score. The HIGH/MEDIUM/LOW labels mirror the established convention used in OSM completeness studies (Herfort et al. 2023, Nature Communications 14:3969 — see §8) where regional completeness is quantified in coarse bands. The fallback chain inside §3D — first impute `levels` from height, then from default 1 — is identical in spirit to the height-from-levels fallback in Module 09 (Technical Pipeline §11 line 119), keeping the heuristic symmetric across the pipeline. Routing all generic-tag rows to `MediumOffice` rather than dropping them honours the **flag-don't-drop** policy that decision row 50 ratifies for Step 1; Heris et al. 2020 (Scientific Data 7:207) showed Microsoft Footprints achieves >93% completeness for buildings ≥200 m², so we expect generic-tagged rows to be real buildings, not OSM noise. Rejected alternative: drop generic rows entirely — destroys the spatial context that Module 08b `get_shading_context()` needs (Technical Pipeline §6 Module 08b) and biases downstream EUI distributions. Rejected alternative: emit a five-tier confidence (HIGH/MEDIUM-HIGH/MEDIUM/MEDIUM-LOW/LOW) — false precision; the underlying signal is essentially binary (we know the function or we don't) plus a partial-info case (we know use_class but not specific function), which maps naturally to three tiers.

### 3E — Output assembly: appending three columns

Final assembly returns a GeoDataFrame with **exactly 26 columns**: the 23 binding upstream columns (unchanged, in their original fixed order) plus three new columns appended in this order:

| # | New column | Dtype | Closed vocabulary / range | Semantics |
|---|---|---|---|---|
| 24 | `archetype_id` | `str` (categorical-eligible — ≤29 distinct values per the closed vocabulary) | one of the 29 archetypes in §3B | The OpenStudio Standards building type. Non-null for every row. |
| 25 | `archetype_confidence` | `str` (categorical-eligible — exactly 3 distinct values) | `{"HIGH", "MEDIUM", "LOW"}` | Per-row classification confidence per §3D. |
| 26 | `archetype_source` | `str` (plain object dtype in pandas — **not** categorical) | comma-joined tokens from `{RULE_HIGHRISE, RULE_RESIDENTIAL_TIER, RULE_LODGING_TIER, RULE_FUNCTION_TAG, RULE_FUNCTION_TAG_SIZE, RULE_USE_CLASS, RULE_USE_CLASS_SIZE, RULE_MIXED_USE, FALLBACK_DEFAULT, HEURISTIC_HEIGHT, HEURISTIC_DEFAULT}` (11 tokens) | Trace of which rule fired plus any imputation hops. Grep-able. |

The dtype distinction matters: only `archetype_id` and `archetype_confidence` are declared categorical (cardinality bounded at 29 and 3 respectively, so categorical compression is cheap). `archetype_source` is comma-joined multi-token and its cardinality grows combinatorially (e.g. `RULE_RESIDENTIAL_TIER,HEURISTIC_HEIGHT`, `RULE_HIGHRISE,HEURISTIC_HEIGHT`, etc.); declaring it categorical would balloon the category index without compression benefit, so it is plain `str` (pandas object dtype).

The 23 upstream columns are read-only (decision row 54 binds them as the Step 1 ↔ Step 2 contract). A `_validate_input_schema(gdf)` helper asserts that the input has all 23 columns in the correct order and dtypes; a `_validate_output_schema(gdf)` helper asserts the 26-column output. Both raise `SchemaError` on mismatch, exactly as the analogous Step 1 `_validate_schema()` does (Step 1 DESIGN §3F).

Persistence: written to `<output_dir>/02_buildings_classified.gpkg` (GeoPackage, layer `buildings`) and accompanying `02_buildings_classified.schema.json` (26 entries). The intermediate name follows the same `NN_<step-noun>.<ext>` convention as Step 1 (`01_buildings_clean.gpkg`).

Return value (in-process): `gpd.GeoDataFrame` with 26 columns, suitable for direct chaining into `enrich_buildings()` (Technical Pipeline §9 `run_ubem()` Stage 2 sub-call).

> **Why this approach:** Appending exactly three new columns — one for the answer (`archetype_id`), one for confidence, one for trace — matches the schema-extension discipline established by Step 1 (one column per concern, fixed dtype, closed vocabulary). Three columns rather than one combined `archetype_with_confidence` token (e.g. `"MediumOffice|HIGH|RULE_FUNCTION_TAG"`) keeps the GeoPackage typing native and lets pandas categorical dtype be applied directly to `archetype_id` and `archetype_confidence` (but not to `archetype_source`, see dtype note above) without parsing. Rejected alternative: add only `archetype_id` and overload `data_quality_flag` with archetype-confidence tokens — pollutes Step 1's closed vocabulary and breaks the Step 1 schema-validation gate. Rejected alternative: emit a separate sidecar `02_archetypes.csv` keyed on `osm_id` — adds a join step downstream and breaks the GeoPackage-as-single-source-of-truth discipline that Step 1 established.

---

## 4. Outputs

| Artifact | Filename | Format | Shape | Consumed by |
|---|---|---|---|---|
| Archetype-labelled building GeoDataFrame | `02_buildings_classified.gpkg` (layer `buildings`) | GeoPackage | `(N, 26)` — 23 from Step 1 + 3 new | Module 04 `construction_sets.get_construction_set(building_type=archetype_id, climate_zone, year_built)`; Module 05 `loads.get_loads(building_type=archetype_id, mode)`; Module 06 `schedules.get_schedule_definitions(archetype_id)`; Module 06b `imputation.impute_column(...)` (uses `archetype_id` as stratum key); Module 09 `BuildingIDF(building_type=archetype_id, ...)`; Module 14 `aggregate_to_geodataframe()` (carries `building_type` column verbatim from `archetype_id`) |
| Classification log | `02_buildings_classified.log` | plain text | per-rule fire counts, per-confidence-tier counts, list of rows that fell through to FALLBACK_DEFAULT with `osm_id` | **Observability only** — human audit and CI smoke-test consumption (§5.1). No machine-parseable consumer downstream. |
| Schema manifest | `02_buildings_classified.schema.json` | JSON | 26 entries: `{name, dtype, vocabulary?}` | Module 04 schema-validation gate |
| Distribution report | `02_archetype_distribution.csv` | CSV | up to 29 rows (one per archetype actually populated) × `[count, fraction, mean_floor_area_m2, mean_levels]` | §5.2 plausibility check; user audit |

### Row-level guarantees (downstream contract)

1. **Every row has a non-null `archetype_id`** drawn from the closed 29-element vocabulary. (FALLBACK_DEFAULT routing to `MediumOffice` exists precisely so that no row has NULL.)
2. **Every row has a non-null `archetype_confidence`** in `{"HIGH","MEDIUM","LOW"}`.
3. **Every row has a non-null `archetype_source`** with at least one rule token; multi-token strings are comma-joined alphabetically for stable grep (same convention as `data_quality_flag`).
4. **The 23 upstream columns are bit-identical to the input.** A unit test asserts `pd.testing.assert_frame_equal(in_gdf, out_gdf[in_gdf.columns])`. In particular, `_impute_levels()` (§3D) does **not** write back to `provenance_levels`.
5. **`archetype_id` values are stable for stable inputs.** No randomness; running the classifier twice on the same `01_buildings_clean.gpkg` returns identical `archetype_id` for every row.

---

## 5. Validation

### 5.1 Metrics and acceptance thresholds

| Metric | Threshold | Rationale (cite source) |
|---|---|---|
| Schema column count | exactly 26 | Step 1 schema (23) + new (3); §3E. |
| Column order | 23 upstream columns first (unchanged), then `archetype_id`, `archetype_confidence`, `archetype_source` | Module 04 schema-validation gate uses positional dtype assertions. |
| `archetype_id` non-null | 100% of rows | Row-level guarantee #1; FALLBACK_DEFAULT closes the loop. |
| `archetype_id` value validity | every value ∈ closed vocabulary of 29 (§3B) | Bundled `openstudio_archetypes.json`. |
| `archetype_confidence` value validity | every value ∈ `{"HIGH","MEDIUM","LOW"}` | §3D. |
| `archetype_source` token validity | every comma-split token ∈ closed vocabulary of 11 (§3E) | §3E. |
| HIGH+MEDIUM combined coverage (working assumption — see OQ-6) | ≥ 70% on the three Step 1 fixtures | Step 1 fixture coverage targets adapted; Herfort et al. 2023 (Nat. Commun. 14:3969) reports North-American urban OSM geometric completeness ≈ 64%, so we expect tag coverage to track that lower bound. Per-fixture deltas are tracked under OQ-6 pending Canadian fixture calibration. |
| LOW (FALLBACK_DEFAULT) fraction | accept ≤ 15%; warn > 15%–≤ 30%; fail CI > 30% (monotone ordering) | Inverse mirror of the ≥ 70% HIGH+MEDIUM target; > 30% on a known-good fixture indicates a regression in §3A use_class table. |
| TallBuilding/SuperTallBuilding rate | ≤ 5% in boston_downtown_500m; ≤ 1% in phoenix_midtown_500m; ≤ 15% in chicago_loop_500m | Chicago Loop fixture is selected for high-rise density (Step 1 DESIGN §5.2). |
| Distribution plausibility envelope (working assumption — pending Canadian fixture calibration; see OQ-6) | residential fraction ∈ [40%, 80%]; commercial fraction ∈ [10%, 40%]; industrial fraction ≤ 10%; institutional fraction ≤ 15% on `boston_downtown_500m` fixture | **No single citation in `inputs/` underwrites the percentages**; the envelope is a permissive working guess intended only to catch gross regressions (e.g. a bug that classifies 95% of Boston as Warehouse). Tightening this envelope into a calibrated test is OQ-6. |
| Determinism (re-run idempotency) | `classify_building_gdf(g)` ≡ `classify_building_gdf(classify_building_gdf(g)[g.columns])` for any valid input `g` | Row-level guarantee #5. |
| Upstream-column byte equality | `pd.testing.assert_frame_equal(in_gdf, out_gdf[in_gdf.columns]) == None` | Row-level guarantee #4. |
| Per-row unit fixtures | Rule 1a: `levels=42, use_class=commercial → SuperTallBuilding`. Rule 2b: `use_class=residential, levels=NaN, height_m=NaN → MidriseApartment, MEDIUM, RULE_RESIDENTIAL_TIER,HEURISTIC_DEFAULT`. Rule 4b: `function_tag=cafe → QuickServiceRestaurant, HIGH`. Rule 17: `building_tag=yes, function_tag="" → MediumOffice, LOW, FALLBACK_DEFAULT`. Rule 6b: `function_tag=school, footprint_area_m2=6000 → SecondarySchool, HIGH`. Rule 6c: `function_tag=kindergarten, footprint_area_m2=800 → PrimarySchool, HIGH`. | Pinned in `tests/test_classifier.py` |
| Labelled top-1 accuracy (working-assumption gate — `ASSUMPTION_DESIGN_DEFAULT`) | On `tests/fixtures/labelled_archetypes_50.csv` (50 hand-labelled rows drawn from `boston_downtown_500m.osm` + `chicago_loop_500m.osm`, ground-truth `archetype_id` column appended): top-1 accuracy of `classify_building_gdf()` ≥ 90% on the residential-vs-commercial coarse split, ≥ 70% on the full 30-element fine-grained vocabulary. CI warn band 80–90% (coarse) / 60–70% (fine); CI fail < 80% (coarse) / < 60% (fine). | Anchored to full-sys DESIGN §8.1 Level 1 (≥ 90% on 50-row labelled CSV) and §10 (eventual 200×4-city manual labelling sprint). 50-row size, 90/70 split thresholds, and warn/fail bands all flagged `ASSUMPTION_DESIGN_DEFAULT` pending the larger labelling sprint — see OQ-7. |
| All-generic-neighbourhood handling | A fixture where 100% of buildings have `data_quality_flag` containing `generic_tag` returns a GeoDataFrame of length > 0, every row has `archetype_id == "MediumOffice"`, every row has `archetype_confidence == "LOW"`, and exactly one `logging.warning` fires with `event="all_fallback_archetype"`. | §3D fallback contract; mirrors Step 1's all-generic test (decision row 63). |

> The fixture-specific HIGH+MEDIUM thresholds (Boston ≥80%, Phoenix ≥60%, Chicago ≥80%) referenced in the prior draft are deferred to OQ-6 — no per-fixture empirical baseline exists in `inputs/` to underwrite those exact numbers, so the hardened threshold is the cross-fixture ≥ 70% only. Per-fixture refinement awaits the Canadian fixture (`montreal_plateau_500m.osm`) and a documented OSM tag-coverage baseline.

### 5.2 Test data and holdout strategy

Three fixtures are reused from Step 1 (`tests/fixtures/`, snapshot 2025-09-15):

| Fixture | Coverage | Used to test |
|---|---|---|
| `boston_downtown_500m.osm` | ~600 buildings, mixed commercial high-rise + residential | Rules 1a/1b (TallBuilding), 2a/2b (apartments), 12a–12c (office tiers), distribution-plausibility envelope |
| `phoenix_midtown_500m.osm` | ~400 buildings, low-rise, sparse `building:levels` | Heavy exercise of `HEURISTIC_HEIGHT` / `HEURISTIC_DEFAULT` paths in §3D; LOW-confidence rate threshold |
| `chicago_loop_500m.osm` | ~250 buildings, dense supertall | Rules 1a/1b firing rates; SuperTallBuilding identification |

Per-fixture acceptance test asserts: every threshold in §5.1, plus a numeric snapshot of `(n_in, n_per_archetype, n_per_confidence_tier, snapshot_hash)`. The snapshot is committed so any CI run that perturbs the rule table (§3C) is caught.

A **fourth synthetic fixture** `synthetic_29_archetype_coverage.gpkg` is generated by `tests/fixtures/build_synthetic.py`: it constructs exactly one minimum-viable row for each of the 29 archetypes (with the OSM tags and area/levels values that should trigger each rule), so that every rule in §3C is exercised at least once per CI run. This guards the closed 29-element output vocabulary from silent regression.

A **fifth labelled-ground-truth fixture** `tests/fixtures/labelled_archetypes_50.csv` is hand-curated: 50 `osm_id` rows drawn from `boston_downtown_500m.osm` (~30 rows, mixed commercial high-rise + residential) and `chicago_loop_500m.osm` (~20 rows, dense supertall + civic), each with an expert-labelled ground-truth `archetype_id` column. This fixture underwrites the labelled top-1 accuracy gate in §5.1 and is the seed for the eventual 200-building × 4-city labelling sprint catalogued in full-sys DESIGN §10. Snapshot date: pending labelling — gate is conditionally enforced once the fixture exists; CI gracefully skips with a `pytest.skip("labelled fixture not yet committed")` until then.

### 5.3 True Future Test (generalisation claim)

This step does not produce a forecast, but it does make a generalisation claim: the rule table must work on OSM extracts the developers have never seen. The defence against information leakage and overfitting to fixtures is:

1. **Rule table is grounded in published OpenStudio Standards taxonomy** (`inputs/reports/OpenStudio Building Types and Templates.pdf`) and the published Technical Pipeline §5 spec (lines 619–800), not in the fixture data — every rule cites a source line in §3C.
2. **No fitted parameters.** There is no learned threshold; every numeric boundary (500 m², 4,000 m², 4 floors, 9 floors, 20 floors, 40 floors) is taken verbatim from the spec.
3. **The synthetic 29-archetype fixture (§5.2) certifies vocabulary coverage** independent of any real city's tag distribution.
4. **Distribution-plausibility envelope (§5.1) is permissive** ([40%, 80%] residential) so legitimate variation across US/CAN urban cores doesn't trigger a false alarm; it catches gross regressions (e.g. a bug that classified 95% of Boston as Warehouse) but tolerates sampling variation. The envelope itself is a working assumption tracked under OQ-6.
5. **A leakage-free promotion rule for Phase 2:** when the Phase-2 ML classifier (decision row 42) is introduced, its training set must exclude the three Step 1 fixtures and the synthetic 29-archetype fixture; the same fixtures become the held-out evaluation set, with a rule-table-vs-ML head-to-head report regenerated on every PR.

---

## 6. Compute

| Resource | Estimate | Source of estimate |
|---|---|---|
| GPU hours | 0 | Pure-Python rule evaluation, no model inference. |
| CPU wall-clock (50,000 buildings, e.g. all of Montreal) | ~25–60 s on a single core (target) | Vectorised pandas ops over 50k rows × ~30 rule predicates ≈ 1.5 M predicate evaluations; pandas/numpy benchmark precedent. |
| CPU wall-clock (1,000 buildings, typical neighbourhood) | < 1 s | Scaling-down from 50k estimate. |
| Peak memory | ~10 MB per 1,000 buildings (3 new string columns; `archetype_id` and `archetype_confidence` are categorical with small cardinality, `archetype_source` is plain object dtype) | Step 1 reports ~150 MB / 1,000 (with surplus_tags JSON dominant); this step adds ~10 MB / 1,000. |
| Storage (intermediate) | ~5–8 MB per 1,000 buildings for `02_buildings_classified.gpkg` | Step 1 GeoPackage size + 3 string columns; categoricals compress well in GPKG. |
| Wall-clock target | ≤ 60 s for 50,000 buildings on one core; ≤ 2 s for 1,000-row fixtures in CI | Sets the rule-evaluation strategy: must be vectorised, not row-by-row Python loop. |

The dominant cost driver is the rule-table evaluation itself. Implementing §3C as a Python `for row in gdf.itertuples()` loop would degrade 50k rows to ~5 minutes; vectorising via boolean masks per rule (e.g. `mask_1a = (gdf["levels"] >= 40) & gdf["use_class"].isin(...)` and successive `np.where`) keeps it at ≤ 60 s. A 2× cost increase would result from lifting the classifier into a per-row Python callable that evaluates rules sequentially with branching — the design must keep rule evaluation declarative and vectorised.

---

## 7. Open Questions

- [ ] **OQ-1 — Mixed-use Phase-1 routing rule:** rule 16 routes `use_class == mixed AND levels < 9` to `MediumOffice`. Is this the right tie-breaker, or should it be `MidriseApartment` (residential wins) or follow the dominant-tag heuristic (whichever of `building_tag` / `function_tag` was OSM_OBSERVED)? Mixed-use is common in Canadian urban cores (residential-over-retail), and the choice affects ~5–15% of rows in dense neighbourhoods. *(blocks §3C rule 16; affects §5.1 distribution-plausibility envelope)*
- [ ] **OQ-2 — `_Detailed` office variants opt-in mechanism:** §3B excludes `SmallOfficeDetailed`, `MediumOfficeDetailed`, `LargeOfficeDetailed` from the rule table outputs and assumes a top-level API flag (`--detailed-office`) selects them. Where does that flag wire — Module 03 (this step), Module 04 (construction sets), or `run_ubem()` orchestrator? *(blocks §3B taxonomy ⇄ Module 04 contract)*
- [ ] **OQ-3 — DataCenter ITE-load (`HighITE` vs `LowITE`) signal:** OSM provides no signal to distinguish High-ITE from Low-ITE. §3C rules 9a/9b default to High-ITE per the spec's `OSM_TO_OPENSTUDIO_TYPE` dict (line 800), which never selects Low-ITE. Should this step expose a per-row override, or accept that Low-ITE archetypes are unreachable in Phase-1 OSM-only runs? *(blocks §3B closed vocabulary completeness — 2 of 29 archetypes are unreachable as drafted)*
- [ ] **OQ-4 — SecondarySchool footprint threshold (5,000 m², rule 6b):** OSM rarely tags `school=secondary`. The 5,000 m² threshold is a guess (PrimarySchool DOE prototype ≈ 6,871 m² total; SecondarySchool ≈ 19,592 m² total). Do we have a documented OSM-based threshold, or should this be flagged as an assumption pending a labelled-school dataset for Canadian/US municipalities? *(blocks §3C rule 6b; affects accuracy of education-sector EUI)*
- [ ] **OQ-5 — `MediumOffice` as fallback default versus an explicit `OpenUBEMUnknown` archetype:** rule 17 collapses unknown rows into `MediumOffice` to keep `archetype_id` non-null and Module 04-compatible. An alternative is to introduce a synthetic 30th archetype `OpenUBEMUnknown` that Module 04/05/06 treat as a special case (e.g. PDE-only sampling across all archetypes). Which is the cleaner contract? *(blocks §3D fallback rationale; affects KDE/PDE behaviour in Module 06b)*
- [x] **OQ-7 — Labelled top-1 accuracy fixture (`labelled_archetypes_50.csv`) — RESOLVED 2026-05-06 (see §11):** §5.1 introduces a labelled top-1 accuracy gate (≥ 90% coarse / ≥ 70% fine on a 50-row hand-labelled CSV) and §5.2 documents the fixture, but the fixture itself is not yet committed. The 50-row size, 90/70 thresholds, and 80/60 CI fail bands are all `ASSUMPTION_DESIGN_DEFAULT` and need calibration once the labelling sprint runs. Open sub-questions: (a) labeller protocol — single expert vs two-expert agreement; (b) source mix — Boston-30 + Chicago-20, or rebalance to include `phoenix_midtown_500m.osm` for low-rise coverage; (c) whether fine-grained 30-archetype labels are even feasible at 50 rows (some archetypes will have 0 ground-truth examples); (d) escalation path to the full-sys DESIGN §10 budget of 200 buildings × 4 cities. *(blocks §5.1 labelled-accuracy gate from active enforcement; CI currently skips when fixture missing)*
- [ ] **OQ-7-FOLLOWUP — Escalation to full-sys §10 200×4 labelling sprint:** OQ-7 closure (2026-05-06) committed only the Phase-1 50-row gate. The full-sys DESIGN §10 budget of 200 buildings × 4 cities (Montréal, Toronto, Boston, Chicago) remains open. Trigger to retire: (i) Phase-1 gate is enforced for ≥ 6 months without spurious failures; (ii) two-expert agreement protocol is formalised; (iii) labelling tooling is automated (no longer manual CSV editing). *(blocks promotion of the labelled-accuracy gate from `ASSUMPTION_DESIGN_DEFAULT` to a confirmed decision in `.claude/design_state.md`)*

- [ ] **OQ-6 — Empirical OSM tag-coverage and use-mix rates for Canadian cities:** §5.1 currently underwrites only the cross-fixture ≥ 70% HIGH+MEDIUM target with a real citation (Herfort et al. 2023). The previously drafted per-fixture thresholds (Boston ≥80%, Phoenix ≥60%, Chicago ≥80%) and the distribution-plausibility envelope ([40%, 80%] residential, [10%, 40%] commercial, etc.) lack a per-fixture or per-region empirical baseline in `inputs/`. A Canadian fixture (e.g. `montreal_plateau_500m.osm`) plus a documented use-mix source (Statistics Canada urban built-form summary, NRCan archetype distributions, or a labelled-municipal-dataset reference) is needed to either tighten or replace the working-assumption envelope before this classifier is used in CAN-pathway pilots. *(blocks §5.1 once Canadian deployment begins; folds in fixture-specific HIGH+MEDIUM thresholds and the distribution-plausibility envelope)*

---

## 8. References

### `inputs/aim/`
- `OpenUBEM_Aim_Document.md` — §3.1 DOE prototype enumeration (16 commercial), §3.2 IECC residential pathway, §4 Iseri et al. 2025 methodological foundation. Justifies why archetype-based classification is the bottom-up entry point and why 29-type granularity is sufficient for Phase 1.
- `OpenUBEM_Technical_Pipeline.md` — §2 minimum required inputs (lines 99–137), §5 Module 03 spec for `building_classifier.py` (lines 599–851; the `OSM_TO_OPENSTUDIO_TYPE` dict and the `select_prototype_size`, `classify_building` pseudocode that this step implements verbatim), §12 provenance vocabulary (motivates the canonical `HEURISTIC` token used in §3D fallback). **Primary anchor for this step.**

### `inputs/reports/`
- `OpenStudio Building Types and Templates.pdf` — §1 enumerates 29 unique OpenStudio archetypes across 12 sectors plus the `_Prototype` base class (the spec prose claims "30 types" but the per-sector enumeration sums to 29). **The closed output vocabulary in §3B is taken verbatim from this PDF.**
- `Open Source Urban Building Energy Modeling - General.md` — §archetype characterization paragraph; motivates rule-based classification as the deterministic path before Phase-2 ML clustering (TEASER and similar tools).
- `UBEM Inputs and GitHub Repository Review.md` — corroborates DOE/IECC prototype mapping conventions and OSM tag-availability rates.
- `Open Source Urban Building Energy Modeling-Architecture.md` — contextualises Stage 2 modules and the `archetype_id` as the cross-stage join key.

### `inputs/papers/`
- `three-methods-for-characterizing-building-archetypes-in-urban-energy-simulation-a-case-study-in-kuwa.md` — Cerezo et al.: three archetype-characterization paradigms (deterministic / clustering / probabilistic). Justifies §3C's deterministic rule table as Phase 1 ahead of Phase-2 clustering.
- `comparing-domain-expert-and-machine-learning-data-enrichment-of-building-registry.md` — expert decision tree achieved 89% accuracy on building wall-type prediction; Random Forest matched it on 416 training rows. Cited in §3C rejected-alternative blockquote as the reason ML is deferred to Phase 2 (decision row 42).
- `data-shortage-for-urban-energy-simulations-an-empirical-survey-on-data-availability-and-enrichment-m.md` — empirical survey of OSM tag availability across cities; supports the flag-don't-drop policy.
- `step-3-gis-data-preparation-ubem-io.md` — UBEM.io's GIS-prep stage; comparator for Module 03 contract.
- `validating-gis-ubem-a-residential-open-data-driven-urban-building-energy-model.md` — open-data residential UBEM validation, supports residential-tier thresholds.

### External anchors (cited via inputs only)
- Iseri, O.K. et al. (2025). *A method for zone-level urban building energy modeling in data-scarce built environments.* Energy & Buildings 337:115620. (Cited via `OpenUBEM_Aim_Document.md` §4 and `OpenUBEM_Technical_Pipeline.md` §6.) Methodological anchor for archetype-stratified KDE/PDE.
- Herfort, B. et al. (2023). *A spatio-temporal analysis investigating completeness and inequalities of global urban building data in OpenStreetMap.* Nature Communications 14:3969. doi:10.1038/s41467-023-39698-w. (Cited via Step 1 DESIGN §3E and `inputs/notes/2026-05-03_..._resolved-open-questions.md` Q7.) North American urban OSM completeness ≈ 64%; sets §5.1 cross-fixture HIGH+MEDIUM ≥ 70% envelope.
- Touzani, S. & Granderson, J. (2021). *Open Data and Deep Semantic Segmentation for Automated Extraction of Building Footprints.* Remote Sensing 13:2578. doi:10.3390/rs13132578. (Cited via Step 1 DESIGN §3E.) Per-city completeness varies dramatically — supports per-fixture rather than uniform threshold in §5.1 / OQ-6.
- Heris, M. et al. (2020). *A rasterized building footprint dataset for the United States.* Scientific Data 7:207. doi:10.1038/s41597-020-0542-3. (Cited via Step 1 DESIGN §3E and §3D rationale.) Microsoft >93% completeness for buildings ≥200 m²; supports flag-don't-drop for generic-tagged rows.
- ASHRAE Standard 90.1-2019 + IECC 2021 + DOE Prototype Buildings (cited via `OpenUBEM_Aim_Document.md` §3 and decision row 34). Underlying reason that the OpenStudio 29-type taxonomy exists in its current form.

---

## 9. Key Decisions Summary

> Single appendix table. Each row records a **load-bearing** decision made in §3. Rationale and rejected alternatives already live inline in §3; this table is the at-a-glance index, not a duplicate of the narrative.

| # | Decision | Sub-stage | Rationale (one line) | Alternatives rejected |
|---|---|---|---|---|
| 1 | Two-stage normalisation: OSM → 6 use-classes → 29 archetypes (not direct OSM-token → archetype dict) | 3A | Decouples open-vocabulary parsing from size-tier resolution; makes Phase-2 ML drop-in a 3A-only swap (decision row 42). | Single flat `OSM_TO_OPENSTUDIO_TYPE` dict (spec lines 729–801) — loses Office/Hotel size tiers; free-text NLP on `surplus_tags` — non-binding column per Q6 (decision row 65). |
| 2 | Closed 29-archetype output vocabulary bundled as versioned `openstudio_archetypes.json`; `_Prototype` excluded; `MediumOffice` reused as the FALLBACK_DEFAULT sentinel | 3B | Pinning the vocabulary to an auditable artifact mirrors Step 1's closed `data_quality_flag` discipline (decision row 50); spec prose "30 types" is a miscount of the 29-row enumeration. | DOE-only 16-prototype subset (omits TallBuilding, Laboratory, DataCenter variants — every one of which the Technical Pipeline §5 enumerates); custom collapsed taxonomy that hides ITE/size distinctions; synthetic 30th `OpenUBEMUnknown` archetype (deferred — see OQ-5). |
| 3 | First-match-wins ordered rule table (§3C) with TallBuilding override applied to non-residential, non-industrial, non-pure-data-center use-classes only; thresholds 500 / 4,000 m² and 4 / 9 / 20 / 40 floors taken verbatim from Technical Pipeline §5 lines 809–828; all Boolean predicates parenthesised | 3C | Determinism + traceability via `archetype_source` token; thresholds are spec-derived, not learned, so generalise without retraining; explicit parentheses prevent OR/AND precedence ambiguity. | Random-Forest classifier (decision row 42 defers ML to Phase 2); OpenStudio-direct dict (loses size tiers). |
| 4 | Three-tier confidence (HIGH/MEDIUM/LOW) driven by upstream `provenance_*` columns + which rule fired; never null; rules-1 (TallBuilding) downgrade to MEDIUM when triggering levels was imputed | 3D | Mirrors closed-vocabulary discipline, easy for Module 04/06b filters to consume; explicit MEDIUM clause for imputed-levels TallBuilding removes ambiguity. | Continuous probability score (false precision; underlying signal is essentially binary + partial); five-tier scheme (no signal to split MEDIUM). |
| 5 | Levels imputation fallback inside Step 2 (height ÷ 3.5 m → 1) when `levels` is NaN, traced via `HEURISTIC_HEIGHT` / `HEURISTIC_DEFAULT` tokens in `archetype_source`; **never mutates `provenance_levels`** | 3D | Symmetric with Module 09's height/levels fallback (Technical Pipeline line 119); keeps Step 2 idempotent without depending on Module 06b imputer; preserves the bit-identical-upstream invariant. | Deferring imputation to Module 06b — would force §3C rules 1/2/3 to emit a sentinel value, breaking the row-level non-null guarantee. |
| 6 | Append exactly three new columns (`archetype_id` categorical, `archetype_confidence` categorical, `archetype_source` plain `str`); 23 upstream columns are byte-identical pass-through | 3E | Schema-extension discipline matching Step 1; `archetype_source` is plain `str` because comma-joined multi-token strings have combinatorial cardinality that defeats categorical compression. | Single combined string column (loses dtype); sidecar CSV (extra join step, breaks single-source-of-truth); declaring `archetype_source` categorical (cardinality balloon). |
| 7 | Generic-tag rows (`building=yes`, no function tag) collapse to `MediumOffice` + LOW + FALLBACK_DEFAULT and emit a structured `all_fallback_archetype` warning when neighbourhood-wide | 3D | Honours flag-don't-drop policy (decision row 50); Heris et al. 2020 evidence that generic rows are real buildings; warning lets Module 06b switch to PDE branch. | Drop generic rows (destroys shading context for Module 08b); silently route to a hidden 30th archetype (breaks closed 29-element vocabulary; see OQ-5). |

---

## 10. Progress Log *(populated by downstream `/run` reporter — leave empty here)*

<!-- The downstream execution project's reporter agent appends `### Session: <date> | Loop: <N>` blocks under this header after each /run cycle. NEITHER the architect NOR the documenter writes here. -->

---

## 11. Revision Log *(populated by DOCUMENTER on /design re-runs only — EMPTY on first creation)*

<!-- Append-only. DOCUMENTER inserts a new block on each /design re-run.

On MODE=new this section MUST contain only this comment block — no `### Session:` block. The first revision block is written on the first MODE=update run.

### Session: <YYYY-MM-DD> | Pass: <final-pass>
**Trigger:** <one-line: new evidence, change request, retired decision>
**Inputs added since last session:** <bullets — filenames>
**Changes:**
- §<N>: <delta>
**New Decisions:** <bullets, also propagated to .claude/design_state.md>
**Retired Decisions:** <bullets — moved to design_state.md ## Retired Decisions, with reason>
**OVERVIEW regenerated:** yes
**GRAPHICAL_ABSTRACT regenerated:** yes | no — no material architecture change

-->

### Session: 2026-05-06 | Pass: 2

**Trigger:** Resolved all 6 §7 Open Questions (OQ-1 through OQ-6) from the 2026-05-06 first-approval session via `inputs/notes/2026-05-06_..._resolved-open-questions.md`; revision pass 2 corrected `archetype_source` token-count arithmetic and flagged the 0.60 dominant-tag threshold as `ASSUMPTION_DESIGN_DEFAULT`.

**Inputs added since last session:**
- `inputs/notes/2026-05-06_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp_resolved-open-questions.md`

**Changes:**
- §3A: dominant-tag score added (default threshold 0.60, flagged `ASSUMPTION_DESIGN_DEFAULT`); substrate for §3C rule 15.
- §3B: archetype taxonomy extended from 29 → 30 (new row 30: `OpenUBEMUnknown` synthetic FALLBACK sentinel; `SmallDataCenterLowITE` and `LargeDataCenterLowITE` marked `PHASE_1_UNREACHABLE`); `overrides/archetype_overrides.csv` escape-hatch contract documented.
- §3C: rule 15 replaced with `MIXED_USE_DOMINANT_TAG` dominant routing; rule 16 replaced with no-dominant fallback to `MidriseApartment`; rule 17 retargeted from `MediumOffice`+`FALLBACK_DEFAULT` to `OpenUBEMUnknown`+`FALLBACK_UNKNOWN`; rule 6b annotated with composite token `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED`.
- §3D: new MEDIUM trigger for rule 16 no-dominant fallback; rule 15 inherits confidence from the fired rule (HIGH/MEDIUM/LOW including the explicit no-silent-inflation LOW case); new LOW trigger for rule 17 `OpenUBEMUnknown`.
- §3E (NEW sub-stage): `detailed_office: bool = False` post-processing pass wired into `BuildingClassifier(detailed_office=...)` (Module 03, not Module 04, not `run_ubem`); promotes `Office*` → `*Detailed` after §3D and before §3F.
- §3F (renamed from prior §3E "Output assembly", extended): per-row override merge from `overrides/archetype_overrides.csv` as the very last operation before emit; `archetype_source` vocabulary expanded to 14 emit-side / 15 read-side tokens (retires `RULE_MIXED_USE`; demotes `FALLBACK_DEFAULT` to read-only deprecated alias; adds `FALLBACK_UNKNOWN`, `MIXED_USE_DOMINANT_TAG`, `ASSUMPTION_DOE_PROTOTYPE_DERIVED`, `DETAILED_OFFICE`, `OVERRIDE_USER`).
- §4: row-level guarantee #6 added (`OpenUBEMUnknown` reachable only via FALLBACK rule 17 or via `overrides/archetype_overrides.csv`); output schema updated to 26 columns over a 30-element archetype vocabulary.
- §5.1: new unit fixtures for rules 15, 16, 17, `detailed_office`, `OVERRIDE_USER`, and Override-to-Unknown; distribution-plausibility envelope labelled `PROVISIONAL_NON_CAN_VALIDATED`; vocabulary-validity threshold updated from 29 → 30.
- §5.2: `synthetic_29_archetype_coverage.gpkg` → `synthetic_30_archetype_coverage.gpkg`; new Phase-1.5 `montreal_plateau_500m.osm` fixture row.
- §5.3: clauses updated for `OpenUBEMUnknown` explicit-uncertainty semantics, `PROVISIONAL_NON_CAN_VALIDATED` label, and `ASSUMPTION_DESIGN_DEFAULT` flagging of the 0.60 threshold.
- §7: OQ-1, OQ-2, OQ-3, OQ-5 marked RESOLVED; OQ-4 split into RESOLVED-with-tracked-follow-up (5,000 m² flagged `ASSUMPTION_DOE_PROTOTYPE_DERIVED`) plus OQ-4-FOLLOWUP; OQ-6 narrowed to Phase-1.5 deferred status with concrete task block OQ-6.1 / 6.2 / 6.3 / 6.4 / 6.5.
- §8: new `inputs/notes/` subsection citing the 2026-05-06 resolution note; StatCan Census 2021 + NRCan CEUD added to external anchors as Phase-1.5 cross-reference targets.
- §9: rows updated to reflect `OpenUBEMUnknown`, the `MIXED_USE_DOMINANT_TAG` two-tier rule, the `detailed_office` Module-03 wiring, the `PHASE_1_UNREACHABLE` LowITE labelling, the per-row override CSV, and the 14-emit / 15-read `archetype_source` vocabulary.

**New Decisions** (also propagated to `.claude/design_state.md ## Confirmed Decisions Index`):
- Step 2 `OpenUBEMUnknown` synthetic 30th archetype as FALLBACK sentinel for unclassifiable OSM rows; replaces `MediumOffice` fallback target. Module 04 treats it as ASHRAE 90.1 pre-1980 permissive envelope; Module 06b uses PDE-only sampling rather than fitting a degenerate stratum-conditional KDE. (§3B, §3D, OQ-5 resolution.)
- Step 2 `MIXED_USE_DOMINANT_TAG` two-tier rule: `dominant_tag_score ≥ 0.60` (`ASSUMPTION_DESIGN_DEFAULT`, flagged for OQ-6.5 calibration) routes mixed-use rows by the dominant tag's normal rules; no-dominant fallback → `MidriseApartment` (not `MediumOffice`). (§3A, §3C rules 15–16, OQ-1 resolution.)
- Step 2 `detailed_office: bool = False` wired into Module 03's `BuildingClassifier` signature (NOT Module 04, NOT `run_ubem` orchestrator); §3E post-processes `Office*` → `*Detailed` before emit. (§3E, OQ-2 resolution.)
- Step 2 LowITE DataCenter archetypes (`SmallDataCenterLowITE`, `LargeDataCenterLowITE`) formally tagged `PHASE_1_UNREACHABLE` in the closed 30-element vocabulary — no OSM signal distinguishes HighITE vs LowITE. (§3B, OQ-3 resolution.)
- Step 2 per-row override file `overrides/archetype_overrides.csv` keyed by `osm_id`, readable by any module downstream of Module 03, as the documented escape-hatch for OSM-unobservable archetype distinctions. (§3F, OQ-3 resolution.)
- Step 2 SecondarySchool 5,000 m² threshold formally tagged `ASSUMPTION_DOE_PROTOTYPE_DERIVED` with tracked validation backlog (Montréal + Toronto labelled-school dataset). (§3C rule 6b, §7 OQ-4-FOLLOWUP, OQ-4 resolution.)
- Step 2 distribution-plausibility envelope labelled `PROVISIONAL_NON_CAN_VALIDATED` ([40–80%] residential, [10–40%] commercial, ≤ 10% industrial, ≤ 15% institutional) until Phase-1.5 `montreal_plateau_500m.osm` + StatCan Census 2021 + NRCan CEUD calibration is delivered. (§5.1, OQ-6 resolution.)

**Retired Decisions** (moved to `.claude/design_state.md ## Retired Decisions`):
- design_state.md row 67 — "Step 2 closed 29-archetype output vocabulary bundled as versioned `openstudio_archetypes.json`; `_Prototype` excluded; `MediumOffice` reused as the FALLBACK_DEFAULT sentinel". Reason: vocabulary is now 30 elements (29 OpenStudio + `OpenUBEMUnknown`); fallback target is `OpenUBEMUnknown`, not `MediumOffice`. Superseded by the new `OpenUBEMUnknown` decision above (OQ-5 resolution).
- design_state.md row 72 — "Step 2 generic-tag rows collapse to `archetype_id="MediumOffice"` + LOW + `FALLBACK_DEFAULT`, `all_fallback_archetype` warning". Reason: generic-tag rows now collapse to `archetype_id="OpenUBEMUnknown"` + LOW + `FALLBACK_UNKNOWN`. The warning event name `all_fallback_archetype` is retained for log-grep continuity but its payload `archetype_id` changes from `MediumOffice` to `OpenUBEMUnknown`. Superseded by the new `OpenUBEMUnknown` decision above (OQ-5 resolution).

**OVERVIEW regenerated:** yes
**GRAPHICAL_ABSTRACT regenerated:** yes — §3 changed materially (new sub-stages §3E `detailed_office` and §3F override merge; rule table revised with `MIXED_USE_DOMINANT_TAG` and `OpenUBEMUnknown`; vocabulary extended to 30)

### Direct edit: 2026-05-06 (no `/design` pass — user-authorized)

**Trigger:** Cross-doc consistency audit against `outputs/2026-05-02_openubem-...full-sys/` flagged a missing labelled-ground-truth top-1 accuracy validation gate (full-sys §8.1 Level 1 requires it; Step 2 §5.1 had no equivalent).

**Authorization:** User explicitly opted out of a `/design` MODE=update pass; CRITIC review was bypassed by request. Open sub-questions are recorded as OQ-7 in §7 rather than being resolved here.

**Changes:**
- §5.1: added `Labelled top-1 accuracy` row (≥ 90% coarse / ≥ 70% fine on `tests/fixtures/labelled_archetypes_50.csv`; warn 80–90 / 60–70; fail < 80 / < 60). All thresholds tagged `ASSUMPTION_DESIGN_DEFAULT`.
- §5.2: added a fifth-fixture paragraph documenting `labelled_archetypes_50.csv` (Boston-30 + Chicago-20, hand-labelled) with `pytest.skip` graceful-degradation until the fixture is committed.
- §7: new OQ-7 listing the four open sub-questions deferred from this direct edit.

**New Decisions:** none load-bearing — all introduced thresholds are flagged `ASSUMPTION_DESIGN_DEFAULT`. Not propagated to `.claude/design_state.md ## Confirmed Decisions Index` until OQ-7 is resolved via a future `/design` pass.

**OVERVIEW regenerated:** no — §5 metric additions don't materially change the OVERVIEW summary.
**GRAPHICAL_ABSTRACT regenerated:** no — no §3 architecture change.

### Direct edit: 2026-05-06 (OQ-7 closure — user-authorized, no `/design` pass)

**Trigger:** Step 2 CP3 greenlit on 2026-05-06 with `TestLabelledTop1Accuracy` as the only intentional skip. To activate the §5.1 labelled-accuracy gate, OQ-7's four sub-questions had to be decided. User ratified the manager's recommendations on (a)/(b)/(c)/(d) in the same session.

**Authorization:** User explicitly opted out of a `/design` MODE=update pass; CRITIC review bypassed by request. Resolutions recorded here; backlog item moves to OQ-7-FOLLOWUP.

**Resolutions to OQ-7 sub-questions:**
- **(a) Labeller protocol — RESOLVED.** Single expert (`orcunkoral.oseri@concordia.ca`) for the Phase-1 50-row gate. Two-expert agreement deferred to OQ-7-FOLLOWUP (full-sys §10 sprint). Rationale: only one domain expert is available on the project; the 50-row gate is a smoke-floor, not a publication-grade ground truth. CSV header records the labeller identity for provenance.
- **(b) Source mix — RESOLVED.** Boston-30 + Chicago-20 per original DESIGN §5.2 wording. Phoenix excluded because the Phoenix fixture's low-rise / sparse-tag coverage is already gated by the `LOW (FALLBACK_DEFAULT) fraction` threshold in §5.1; adding Phoenix here would dilute high-rise/supertall coverage that Chicago is specifically chosen to provide.
- **(c) Fine-grained 30-archetype feasibility at 50 rows — RESOLVED.** ≥ 70% fine threshold retained. Added a hard coverage requirement: the 50 labelled rows must collectively hit **≥ 10 distinct archetypes** (out of the 30-element vocabulary). Documented explicitly that fine accuracy is measured *over labelled archetypes only* — archetypes with zero ground-truth rows do not contribute to the metric. The 80/60 warn/fail bands in §5.1 unchanged.
- **(d) Escalation path to full-sys §10 200×4 sprint — DEFERRED.** Logged as **OQ-7-FOLLOWUP** in §7 (this revision). Phase-1 50-row gate is sufficient for Step 2 closure; the 200×4 sprint is a Phase-2 deliverable.

**Changes:**
- §7: OQ-7 marked `[x]` RESOLVED with cross-link to this revision-log entry; new OQ-7-FOLLOWUP added below it.
- §5.1: Labelled top-1 accuracy row stays as drafted (≥ 90% coarse / ≥ 70% fine; warn 80–90 / 60–70; fail < 80 / < 60). New row appended in implementation: `Labelled coverage` ≥ 10 distinct archetypes (per OQ-7 (c)).
- §5.2: Fifth-fixture paragraph stays. Footnote in PLAN_step-2.5 clarifies that the canonical persisted form of the source fixtures is `.gpkg` (cleaned 23-col GeoDataFrame), not raw `.osm` XML — Step 1 never committed `.osm` files; the user materialises the `.gpkg` snapshots once via `tests/fixtures/build_osm_fixtures.py` (PLAN L0). Raw OSM XML pipeline is deferred to Phase-2 if ever needed.

**Coarse-class mapping (load-bearing — pinned for L2 implementation):**
The "residential-vs-commercial coarse split" in §5.1 row `Labelled top-1 accuracy` is operationalised against the `sector` field of `openubem/data/openstudio_archetypes.json`:
- **residential** ⇔ `sector == "Residential"` (2 archetypes — MidriseApartment, MultifamilyHome)
- **commercial** ⇔ all other sectors (28 archetypes, including Lodging, High-Rise, Industrial, Healthcare, Education, Government, Data Center, Research, Office, Retail, Food Service, Fallback)

This binary mapping is sealed in this revision-log entry; do not re-debate during PLAN execution.

**New Decisions:** Coarse-class mapping above is the only new load-bearing decision. Still flagged `ASSUMPTION_DESIGN_DEFAULT` until the full-sys §10 200×4 sprint validates it. Not propagated to `.claude/design_state.md ## Confirmed Decisions Index` until OQ-7-FOLLOWUP is resolved.

**OVERVIEW regenerated:** no — coarse-class mapping is a §5 implementation detail, not a contract change.
**GRAPHICAL_ABSTRACT regenerated:** no — no §3 architecture change.
