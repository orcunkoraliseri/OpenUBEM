# OVERVIEW — Step 2: OSM Building → OpenStudio 30-Element Archetype Classifier
### OpenUBEM Stage 2 / Module 03: `openubem/semantic/building_classifier.py` — convert the cleaned 23-column GeoDataFrame from Step 1 into an archetype-labelled GeoDataFrame ready for the construction/loads imputer

> **Slug:** `step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md` &nbsp;•&nbsp; **Generated:** `2026-05-06`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §11.

---

## AIM

Deterministic rule-based classifier that maps each cleaned OSM building footprint to exactly one of **29 OpenStudio Standards archetypes + 1 synthetic `OpenUBEMUnknown` FALLBACK sentinel = 30-element closed vocabulary**, plus a three-tier confidence label and an audit-grep `archetype_source` token. Consumes Step 1's 23-column `01_buildings_clean.gpkg`; emits a 26-column `02_buildings_classified.gpkg` keyed on `archetype_id` for every Stage-2 downstream module (Module 04 construction sets, Module 05 loads, Module 06 schedules, Module 06b KDE/PDE imputer, Module 09 IDF assembly).

---

## PIPELINE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  3A — OSM tag → use_class normalisation + dominant-tag scoring               ║
║  Inputs:    building_tag, function_tag (Step 1 cols 4–5); bounded            ║
║             surplus_tags keys {shop, amenity, office, landuse}               ║
║  Operation: collapse open OSM vocabulary to 6 closed use-classes             ║
║             (residential / commercial / industrial / institutional /         ║
║              mixed / unknown); function_tag wins over building_tag;          ║
║             compute dominant_tag_score for mixed rows (default cutoff 0.60   ║
║             — flagged ASSUMPTION_DESIGN_DEFAULT, OQ-6.5 follow-up)           ║
║  Output:    transient use_class column + dominant_tag_score (not persisted)  ║
║  Validation: every value ∈ {6 closed classes}                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3B — OpenStudio 29-type taxonomy + OpenUBEMUnknown sentinel (30 elements)   ║
║  Inputs:    bundled openstudio_archetypes.json (30 entries)                  ║
║  Operation: pin 29 OpenStudio archetype IDs (Office×6, Retail×3, Food×2,     ║
║             Lodging×2, Residential×2, Healthcare×2, Education×3, Govt×1,     ║
║             DataCenter×4, Research×1, Industrial×1, HighRise×2) + 1          ║
║             synthetic OpenUBEMUnknown FALLBACK sentinel; _Prototype          ║
║             excluded; SmallDataCenterLowITE + LargeDataCenterLowITE marked   ║
║             PHASE_1_UNREACHABLE (reachable only via override CSV)            ║
║  Output:    static lookup; SemVer-pinned for change auditing                 ║
║  Validation: every output archetype_id ∈ closed 30-element set               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3C — Primary classifier: 17 ordered rules (use_class × area × levels)       ║
║  Inputs:    use_class (3A), footprint_area_m2 (col 13), levels (col 6),      ║
║             dominant_tag_score (3A)                                          ║
║  Operation: 17 first-match-wins rules; thresholds 500 / 4,000 m² and         ║
║             4 / 9 / 20 / 40 floors verbatim from Technical Pipeline §5;      ║
║             TallBuilding override exempts residential / industrial /         ║
║             pure-data-center; rule 15 routes mixed-use by dominant tag       ║
║             (score ≥ 0.60); rule 16 falls back to MidriseApartment;          ║
║             rule 17 routes unknowns to OpenUBEMUnknown (FALLBACK_UNKNOWN);   ║
║             rule 6b SecondarySchool 5,000 m² flagged ASSUMPTION_DOE_         ║
║             PROTOTYPE_DERIVED                                                ║
║  Output:    archetype_id (str) + archetype_source token                      ║
║  Validation: synthetic-30 fixture exercises every rule each CI run           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3D — Confidence scoring + levels-imputation + FALLBACK chain                ║
║  Inputs:    upstream provenance_* columns (cols 16–22), which rule fired     ║
║  Operation: 3-tier label (HIGH / MEDIUM / LOW); height ÷ 3.5 m levels        ║
║             imputation when col 6 is NaN — never mutates provenance_levels;  ║
║             rule 15 inherits inherited rule's tier (no silent inflation —    ║
║             LOW stays LOW); rule 16 = MEDIUM; rule 17 = LOW;                 ║
║             generic_tag rows → OpenUBEMUnknown + LOW + FALLBACK_UNKNOWN;     ║
║             FALLBACK_DEFAULT retained as deprecated read-side alias only     ║
║  Output:    archetype_confidence (str categorical, 3 values)                 ║
║  Validation: HIGH+MEDIUM ≥ 70% across 3 fixtures; LOW > 30% fails CI         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3E — detailed_office post-processing (opt-in *Detailed Office variants)     ║
║  Inputs:    archetype_id from §3D; BuildingClassifier(detailed_office=bool)  ║
║  Operation: when True, promote {SmallOffice, MediumOffice, LargeOffice} →    ║
║             corresponding *Detailed variants; append DETAILED_OFFICE token   ║
║             to archetype_source; archetype_confidence preserved              ║
║  Output:    archetype_id (possibly promoted) + extended archetype_source     ║
║  Validation: detailed_office=False ⇒ no-op; detailed_office=True ⇒ Office*   ║
║              rows fully migrated to *Detailed; unit fixture pinned           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3F — Per-row override merge + output assembly: append three new columns     ║
║  Inputs:    23-col upstream gdf + (archetype_id, _confidence, _source);      ║
║             optional overrides/archetype_overrides.csv keyed by osm_id       ║
║  Operation: left-join overrides on osm_id (overrides set _id, force          ║
║             confidence=HIGH, set source=OVERRIDE_USER(<note>)); byte-        ║
║             identical pass-through of cols 1–23; append cols 24–26;          ║
║             archetype_source vocabulary = 14 emit-side / 15 read-side;       ║
║             write 02_buildings_classified.gpkg + .schema.json + .log + CSV   ║
║  Output:    GeoDataFrame (N, 26) — N typical 200–5,000 per km²               ║
║  Validation: schema column count == 26; pd.testing.assert_frame_equal on     ║
║              upstream slice; archetype_id 100% non-null;                     ║
║              OpenUBEMUnknown reachable only via FALLBACK_UNKNOWN or          ║
║              OVERRIDE_USER (row-level guarantee #6)                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| Input columns (Step 1 binding contract) | 23 | DESIGN §2 |
| Output columns | 26 (= 23 + 3 appended) | DESIGN §3F, §4 |
| Closed archetype vocabulary | 30 elements (29 OpenStudio + 1 `OpenUBEMUnknown`) | DESIGN §3B |
| PHASE_1_UNREACHABLE archetypes (reachable only via override CSV) | 2 (SmallDataCenterLowITE, LargeDataCenterLowITE) | DESIGN §3B |
| Confidence tiers | 3 (HIGH / MEDIUM / LOW) | DESIGN §3D |
| `archetype_source` token vocabulary | 14 emit-side / 15 read-side (incl. deprecated `FALLBACK_DEFAULT` alias) | DESIGN §3F |
| Use-classes (intermediate) | 6 | DESIGN §3A |
| Rules in primary table | 17 (first-match-wins) | DESIGN §3C |
| `dominant_tag_threshold` (rule 15) | 0.60 (ASSUMPTION_DESIGN_DEFAULT — OQ-6.5) | DESIGN §3A |
| GPU hours | 0 (rule evaluation only) | DESIGN §6 |
| CPU wall-clock target (50,000 buildings) | ≤ 60 s on one core | DESIGN §6 |
| Peak memory | ~10 MB / 1,000 buildings | DESIGN §6 |
| Test fixtures | 3 real (Boston / Phoenix / Chicago) + 1 synthetic-30 + 1 Phase-1.5 Montréal Plateau | DESIGN §5.2 |

---

## VALIDATION SUMMARY

- Schema column count: **exactly 26** (threshold strict) — pass condition for Module 04 gate.
- `archetype_id` non-null: **100%** of rows (FALLBACK_UNKNOWN closes the loop).
- `archetype_id` value validity: **every value ∈ closed 30-element vocabulary** (29 OpenStudio + `OpenUBEMUnknown`).
- `archetype_confidence` value validity: **every value ∈ {HIGH, MEDIUM, LOW}**.
- `archetype_source` token validity: every comma-split token ∈ closed read-side vocabulary of 15; `OVERRIDE_USER(...)` parenthesised note prefix accepted.
- `OpenUBEMUnknown` provenance: 100% of `OpenUBEMUnknown` rows have `archetype_confidence == "LOW"` AND `archetype_source` contains `FALLBACK_UNKNOWN` (or `OVERRIDE_USER` if the user explicitly overrode to `OpenUBEMUnknown`) — row-level guarantee #6.
- HIGH+MEDIUM combined coverage: **≥ 70% across 3 fixtures** (working assumption — Herfort et al. 2023; per-fixture refinement under OQ-6).
- FALLBACK_UNKNOWN (`OpenUBEMUnknown`) fraction: accept ≤ 15%, warn 15–30%, fail CI > 30% (monotone ordering).
- Distribution-plausibility envelope (PROVISIONAL_NON_CAN_VALIDATED — OQ-6): residential ∈ [40%, 80%], commercial ∈ [10%, 40%], industrial ≤ 10%, institutional ≤ 15% on `boston_downtown_500m`.
- Upstream-column byte equality: `pd.testing.assert_frame_equal(in_gdf, out_gdf[in_gdf.columns])` succeeds — row-level guarantee #4 (`_impute_levels()` does not mutate `provenance_levels`).
- Determinism: same input + same `overrides_path` + same `detailed_office` flag ⇒ same output (no randomness; no fitted parameters).
- Synthetic 30-archetype fixture: every rule in §3C exercised at least once per CI run, including the `OpenUBEMUnknown` row.
- True Future Test: no fitted parameters; every spec-derived numeric (500 / 4,000 m²; 4 / 9 / 20 / 40 floors) verbatim from Technical Pipeline §5; the 5,000 m² SecondarySchool boundary is `ASSUMPTION_DOE_PROTOTYPE_DERIVED` (OQ-4-FOLLOWUP); the 0.60 dominant-tag threshold is `ASSUMPTION_DESIGN_DEFAULT` (OQ-6.5); `OpenUBEMUnknown` makes generalisation failures visible in the output, not buried in the audit log; Phase-2 ML training set must exclude all five fixtures.

---

## KEY DECISIONS

> Mirrors the DESIGN §9 appendix table — same rows, one line each. For full rationale + alternatives rejected → DESIGN §3 (inline) and §9 (appendix).

| Decision | Rationale (one line) |
|---|---|
| Two-stage normalisation: OSM → 6 use-classes → 30-element archetype vocabulary; §3A also computes a dominant-tag score (default 0.60) used by §3C rule 15 | Decouples open-vocabulary parsing from size-tier resolution; the dominant-tag score is the substrate the MIXED_USE_DOMINANT_TAG rule reads, keeping §3C flat and auditable. |
| Closed **30-element** archetype output vocabulary = 29 OpenStudio Standards types + 1 synthetic `OpenUBEMUnknown` FALLBACK sentinel; two LowITE DataCenter archetypes tagged `PHASE_1_UNREACHABLE` (override-only) | Pinning vocabulary to versioned JSON mirrors Step 1's closed `data_quality_flag` discipline; making the 30th slot explicit replaces the prior `MediumOffice` fallback's silent commercial-EUI bias. |
| First-match-wins ordered 17-rule table; TallBuilding override exempts residential / industrial / pure-data-center; rule 15 routes mixed-use by dominant tag (≥ 0.60), rule 16 falls back to `MidriseApartment`, rule 17 routes unknowns to `OpenUBEMUnknown`, rule 6b carries `ASSUMPTION_DOE_PROTOTYPE_DERIVED` | Determinism + traceability via `archetype_source`; thresholds spec-derived; MIXED_USE_DOMINANT_TAG matches the modal Canadian urban-core pattern; `OpenUBEMUnknown` makes uncertainty explicit so Module 06b can switch to PDE-only sampling. |
| Three-tier confidence (HIGH / MEDIUM / LOW) driven by upstream `provenance_*` + which rule fired; rule 15 inherits the inherited rule's tier (no silent inflation — LOW stays LOW); rule 16 = MEDIUM; rule 17 = LOW + FALLBACK_UNKNOWN | Mirrors closed-vocabulary discipline; FALLBACK_UNKNOWN (replacing FALLBACK_DEFAULT) makes the `OpenUBEMUnknown` sentinel grep-discoverable in the audit trail. |
| `detailed_office: bool = False` wired into Module 03's `BuildingClassifier.__init__` (NOT Module 04, NOT `run_ubem`); §3E post-processes `Office*` → `*Detailed` and appends `DETAILED_OFFICE` token; confidence preserved across the promotion | Module 03 is the only stage that owns `archetype_id`; the `_Detailed` opt-in is an archetype-routing decision, so locality of concerns puts it here. |
| Per-row override via `overrides/archetype_overrides.csv` keyed by `osm_id` — read at the very end of §3F, after rule table, after `detailed_office`, before emit; sets `confidence=HIGH` and `source=OVERRIDE_USER(<note>)` | A user override is the strongest signal in the system and must dominate every rule-table or post-processing decision; mechanism handles LowITE as the motivating use case but generalises to any OSM-unobservable distinction. |
| Append exactly 3 new columns (`archetype_id` categorical [30-value vocab], `archetype_confidence` categorical [3-value], `archetype_source` plain `str` [**14 emit-side / 15 read-side** including the deprecated `FALLBACK_DEFAULT` alias]); 23 upstream columns are byte-identical pass-through; `_impute_levels()` does not mutate `provenance_levels` | Schema-extension discipline matching Step 1; multi-token `archetype_source` defeats categorical compression; vocabulary growth from 29 → 30 archetype IDs and from 11 → 14 emit-side source tokens is a minor schema extension, not a retirement. |

---

## OPEN QUESTIONS

> All originals OQ-1 through OQ-5 are RESOLVED 2026-05-06. OQ-4 has a tracked follow-up; OQ-6 is partially resolved with a Phase-1.5 task block. See DESIGN §7 for full text.

- **OQ-4-FOLLOWUP — SecondarySchool 5,000 m² threshold validation.** Validate against a labelled Montréal + Toronto school dataset (StatCan school-board boundaries + OSM `amenity=school` + manual labels). Trigger to retire `ASSUMPTION_DOE_PROTOTYPE_DERIVED`: ≥ 200 ground-truth labels confirm threshold within ±20% of 5,000 m². *(blocks promotion of rule 6b to HIGH-confidence even when tag evidence is observed)*
- **OQ-6.1 — Build `montreal_plateau_500m.osm` Phase-1.5 fixture.** *(blocks per-fixture calibration of §5.1 thresholds for Canadian deployment)*
- **OQ-6.2 — Cross-reference `montreal_plateau_500m` against StatCan Census 2021 dwelling-type counts.** *(unblocks tightening the [40–80%] residential bound)*
- **OQ-6.3 — Cross-reference `montreal_plateau_500m` against NRCan CEUD building-stock breakdown.** *(further tightens commercial/industrial bounds)*
- **OQ-6.4 — Recalibrate the use-mix envelope per-fixture** once OQ-6.1 / 6.2 / 6.3 are delivered. *(blocks promotion of the envelope to a confirmed decision)*
- **OQ-6.5 — Recalibrate the `dominant_tag_threshold` (currently 0.60, ASSUMPTION_DESIGN_DEFAULT) against `montreal_plateau_500m.osm`.** Sweep over {0.50, 0.55, 0.60, 0.65, 0.70, 0.75}; trigger to retire flag: calibrated value within ±0.05 of 0.60 OR documented as a new active decision. *(unblocks confidence in rule 15 dominant-tag routing for Canadian deployment)*
