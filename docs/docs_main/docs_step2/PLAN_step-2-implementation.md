# PLAN — Step 2 Implementation (OSM → OpenStudio 30-Element Archetype Classifier)

> **Slug:** `plan-step-2-implementation`
> **Authored:** 2026-05-06 (manager) — **Pass-2 rewrite:** 2026-05-06 (manager, after Sonnet stop on DESIGN body vs §11 conflict)
> **Binding contract:** `docs\docs_step2\DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md`
> **Companion summary:** `docs\docs_step2\OVERVIEW_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md`
> **Pipeline placement:** `docs\docs_main\OVERVIEW_openubem-...md`
> **Target module:** `openubem/semantic/building_classifier.py`
> **Working directory (absolute, do not leave):** `C:\Users\o_iseri\Desktop\OpenUBEM`

This is the manager-authored plan. A fresh Sonnet session executes against it, top to bottom. **Sonnet does not propose its own plan — it executes this one and reports.**

> **Pass-2 binding-source rule.** The DESIGN doc has been revised twice on 2026-05-06: (i) `/design` Pass 2 (DESIGN §11 lines 455–491) and (ii) a user-authorized direct edit (DESIGN §11 lines 493–506). The DESIGN body Sections 1–9 were **NOT regenerated** to reflect those revisions, so §3B/§3C/§3D/§3E/§4/§5 body text is stale. **Where DESIGN §3 body and §11 Revision Log conflict, §11 wins** — §11 explicitly retires the §3 body decisions and propagates the new ones to `.claude/design_state.md`. OVERVIEW (`docs\docs_step2\OVERVIEW_*.md`) was regenerated against Pass-2 (Revision Log line 490: "OVERVIEW regenerated: yes") and is therefore the cleaner Pass-2 reflection. This PLAN cites §11 and OVERVIEW where they supersede stale §3 body lines.

---

## 1. Hard rules for the executor

1. Stay at the working directory above. Do not `cd` elsewhere.
2. Do **not** create, edit, move, or delete any `.py` file under `docs\`. The `docs\` tree is markdown only and read-only with respect to code.
3. All source code lives under the project root (`openubem\...`, `tests\...`, `pyproject.toml`).
4. Do **not** invent design decisions. If the DESIGN doc is silent or §11 is also silent, **STOP and ask the manager** — do not patch silently. Quote the relevant DESIGN/OVERVIEW lines and the ambiguity.
5. **Where DESIGN §3 body conflicts with DESIGN §11 Revision Log: §11 wins.** This PLAN's §4 already pins the §11/OVERVIEW-derived facts; do not "correct" them back to the §3 body.
6. No scope creep beyond Step 2. No CLI, no Stage 3+ helpers (construction sets, loads, schedules, IDF builder), no live-network integration tests, no labelled 50-row fixture creation (OQ-7 — fixture is hand-curated externally; tests must `pytest.skip(...)` when missing).
7. Default to writing **no comments**. Only comment when the WHY is non-obvious. Do not write multi-paragraph docstrings.
8. Do not touch `main.py` at the project root — it is a PyCharm placeholder. Leave it alone.
9. Do not modify Step 1 code (`openubem/acquisition/osm_fetcher.py`) — the 23-column upstream schema is the binding contract. **Step 2 must never mutate any of the 23 upstream columns** (DESIGN §4 row-level guarantee #4, line 302; DESIGN §3D line 256 invariant). Output must satisfy `pd.testing.assert_frame_equal(in_gdf, out_gdf[in_gdf.columns])`.
10. The `OpenUBEMUnknown` archetype is reachable from the rule table **only via rule 17** (`use_class == "unknown"`) — and additionally via `overrides/archetype_overrides.csv` if a user opts in. Any other code path producing `OpenUBEMUnknown` is a bug. (DESIGN §11 line 469 — row-level guarantee #6.)
11. Update the **Progress log** (§7) after each completed task. Do not skip log entries.

---

## 2. File layout to create

```
C:\Users\o_iseri\Desktop\OpenUBEM\
├── openubem\
│   ├── semantic\
│   │   ├── __init__.py                             ← T01 (empty)
│   │   └── building_classifier.py                  ← T02–T10
│   ├── data\
│   │   ├── __init__.py                             ← T01 (empty marker)
│   │   ├── openstudio_archetypes.json              ← T02 (30 entries)
│   │   └── osm_to_use_class.json                   ← T03
└── tests\
    ├── fixtures\
    │   └── synthetic_30_archetype_coverage.gpkg    ← T13 (built at test-collection time)
    └── test_building_classifier.py                 ← T14
```

**Not created in this step:**

- `overrides/archetype_overrides.csv` — runtime user input, not bundled. Tests that exercise the override path build a tiny ephemeral CSV in a tmp dir.
- `tests/fixtures/labelled_archetypes_50.csv` — OQ-7-gated. Tests that consume it must be `pytest.skip(...)`-ed when the file is missing.
- Large `.osm` city fixtures (Boston / Phoenix / Chicago) — already exist from Step 1; do not re-download.

---

## 3. Dependency decisions (already settled — do not re-debate)

`pyproject.toml` already pins the runtime libraries Step 2 needs (set by Step 1, decision row 53). **No new runtime dependencies are added in Step 2.** Specifically:

- `geopandas`, `pandas`, `shapely`, `numpy` — already pinned.
- `pyogrio` — GeoPackage driver, already pinned.
- JSON data files (`openstudio_archetypes.json`, `osm_to_use_class.json`) loaded via `importlib.resources.files("openubem.data")` — **stdlib only**; do not add `importlib_resources` backport.
- CSV override file read via stdlib `csv` module or `pandas.read_csv`. No new lib.
- `pytest`, `pytest-mock` — already in `[dev]` extra.

Two pyproject changes are in scope (T15):
- Confirm `[tool.setuptools.packages.find]` discovers `openubem.semantic` and `openubem.data`.
- Bundle the JSON data files via `[tool.setuptools.package-data]`.

---

## 4. Source-of-truth verified facts (cite these exactly)

The manager has already grepped DESIGN body, DESIGN §11 Revision Log, and OVERVIEW. These facts are load-bearing — Sonnet does **not** need to re-derive them, just cite them. Where the §3 body is stale, the binding cite is `§11 line N` and/or `OVERVIEW line N`.

| # | Fact | Cite |
|---|---|---|
| 1 | **Public API is class-based** (Pass-2 supersedes the function form in §3 body line 73). Constructor: `BuildingClassifier(detailed_office: bool = False, overrides_path: Path \| None = None, high_rise_levels_threshold: int = 20, super_tall_levels_threshold: int = 40, floor_to_floor_m: float = 3.5)`. Public method: `classify(self, gdf: gpd.GeoDataFrame, output_dir: Path \| None = None) -> gpd.GeoDataFrame`. The function-form `classify_building_gdf(...)` from §3 body is NOT exported in Pass-2 — only `BuildingClassifier` and the per-row helper `classify_building(row, ...)`. | DESIGN §11 lines 467, 480; OVERVIEW lines 68, 126, 142 |
| 2 | Per-row unit-of-work helper `classify_building(row: pd.Series, *, detailed_office: bool = False, ...) → tuple[str, str, str]` returns `(archetype_id, archetype_confidence, archetype_source)` for unit testing. The override merge is **not** applied here — overrides only fire in the orchestrator (§3F). | DESIGN §3 line 84 (helper signature retained); §11 lines 467–468 (override is §3F-only) |
| 3 | 6 closed use-classes: `{residential, commercial, industrial, institutional, mixed, unknown}` | DESIGN §3A lines 91–93 |
| 4 | OSM token → use-class mapping table (verbatim) | DESIGN §3A lines 99–104 |
| 5 | Resolver runs `function_tag` FIRST, `building_tag` SECOND. Step 1's intra-`function_tag` priority `amenity > shop > office` is preserved upstream and not re-applied here. | DESIGN §3A line 106 |
| 6 | **Stage 3A also computes `dominant_tag_score`** for mixed-use rows. Default `dominant_tag_threshold = 0.60`, flagged `ASSUMPTION_DESIGN_DEFAULT` (OQ-6.5). The score is the substrate Rule 15 reads. (Body §3A is silent on the score; cite §11 + OVERVIEW.) Phase-1 implementation: `dominant_tag_score = max_proportion(tag_class_count_among_resolved_tags)`; concretely with two tags the score is 1.0 if both agree, 0.5 if they disagree (so threshold 0.60 routes disagreeing pairs to Rule 16, agreeing pairs through Rule 15). | DESIGN §11 line 463; OVERVIEW lines 26–27, 106, 138 |
| 7 | **30-element closed archetype vocabulary** = 29 OpenStudio archetypes + 1 synthetic `OpenUBEMUnknown` FALLBACK sentinel. The 29 OpenStudio entries are listed in DESIGN §3B body lines 116–147. The 30th (`OpenUBEMUnknown`) is added per Pass-2. **`SmallDataCenterLowITE` (#23) and `LargeDataCenterLowITE` (#25) are tagged `phase_1_unreachable: true`** — reachable only via override CSV. | DESIGN §11 lines 464, 478, 481; OVERVIEW lines 31, 100–101 |
| 8 | **Phase-1 fallback target = `OpenUBEMUnknown`** (not `MediumOffice`) + token `FALLBACK_UNKNOWN`. `MediumOffice + FALLBACK_DEFAULT` is **retired** (Pass-2 line 487). Generic-tag rows now collapse to `OpenUBEMUnknown` + LOW + `FALLBACK_UNKNOWN` (Pass-2 line 488). | DESIGN §11 lines 465, 478, 487–488; OVERVIEW lines 50, 62, 117–118, 121 |
| 9 | Area bins: S `<500`, M `500–4000`, L `≥4000` m² (boundaries are spec-pinned per Technical Pipeline `select_prototype_size`) | DESIGN §3C lines 156–166 |
| 10 | Levels bins: `<4`, `≥4` (lodging); `<9`, `≥9` (residential); `≥20`, `≥40` (high-rise overrides) | DESIGN §3C lines 169–180 |
| 11 | TallBuilding/SuperTallBuilding override exempts three use-classes: `residential`, `industrial`, pure data-center | DESIGN §3C line 184 |
| 12 | **17 ordered first-match-wins rules**, with three Pass-2 deltas baked in (cite §11 line 465): (a) **Rule 15** = `MIXED_USE_DOMINANT_TAG` — when `use_class == "mixed"` and `dominant_tag_score ≥ 0.60`, route by the dominant tag's normal rules; emit token `MIXED_USE_DOMINANT_TAG`. (b) **Rule 16** = no-dominant fallback — when `use_class == "mixed"` and `dominant_tag_score < 0.60`, archetype = `MidriseApartment`; emit token `MIXED_USE_DOMINANT_TAG`. (c) **Rule 17** = `use_class == "unknown"` (after fallback) → archetype = `OpenUBEMUnknown`, emit token `FALLBACK_UNKNOWN`. (d) **Rule 6b** carries composite token `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED`. Rules 1a–14 are unchanged from §3C body lines 188–215. | DESIGN §3C lines 188–218 (rules 1a–14 unchanged); DESIGN §11 line 465 (rules 15/16/17/6b deltas); OVERVIEW lines 48–52, 140 |
| 13 | `_Detailed` office variants (`SmallOfficeDetailed`, `MediumOfficeDetailed`, `LargeOfficeDetailed`) are NOT assigned by the rule table. They are produced exclusively by **§3E `detailed_office` post-processing** when `BuildingClassifier(detailed_office=True)`. | DESIGN §3C line 220; DESIGN §11 lines 467, 480; OVERVIEW lines 67–74, 142 |
| 14 | **3-tier confidence (HIGH/MEDIUM/LOW)** with Pass-2 deltas: (a) **Rule 15 inherits the inherited rule's tier** — no silent inflation. If the dominant-tag rule that fired would emit LOW, Rule 15 emits LOW. (b) **Rule 16** (no-dominant fallback) = MEDIUM. (c) **Rule 17** (`OpenUBEMUnknown` / `FALLBACK_UNKNOWN`) = LOW. Other triggers from §3D body lines 228–232 unchanged. | DESIGN §3D lines 228–232; DESIGN §11 line 466; OVERVIEW lines 60–61, 65, 141 |
| 15 | `_impute_levels(row, floor_to_floor_m=3.5) → tuple[int, str]` algorithm (verbatim) | DESIGN §3D lines 238–253 |
| 16 | **Critical invariant: `_impute_levels` does NOT mutate `provenance_levels` (upstream column 16) or any other binding upstream column.** Imputed value is transient; only persistent record is the `HEURISTIC_*` token in `archetype_source`. | DESIGN §3D line 256; DESIGN §4 row-level guarantee #4 line 302 |
| 17 | Floor-to-floor 3.5 m default (matches Technical Pipeline §2 line 119 and Module 09) | DESIGN §3D line 258 |
| 18 | **Generic-tag fallback (Pass-2 amended):** `data_quality_flag` contains `generic_tag` ⇒ rule 17 fires (`OpenUBEMUnknown`, `LOW`, `FALLBACK_UNKNOWN`). The body §3D line 262 still says `MediumOffice / FALLBACK_DEFAULT` — that is **retired** per §11 line 488. | DESIGN §11 line 488; OVERVIEW lines 62, 117–118, 121 |
| 19 | **`all_fallback_archetype` warning event:** name is **retained** for log-grep continuity but payload changes — emit ONE structured warning to `openubem.semantic` logger when every row resolves to `OpenUBEMUnknown`: `{"event": "all_fallback_archetype", "n_rows": int, "archetype_id": "OpenUBEMUnknown"}`. | DESIGN §11 line 488 ("event name `all_fallback_archetype` is retained for log-grep continuity but its payload `archetype_id` changes from `MediumOffice` to `OpenUBEMUnknown`") |
| 20 | **§3E — `detailed_office` post-processing** (NEW sub-stage, Pass-2). Runs **after §3D and before §3F**. When `detailed_office=True`: promote `SmallOffice` → `SmallOfficeDetailed`, `MediumOffice` → `MediumOfficeDetailed`, `LargeOffice` → `LargeOfficeDetailed`. **Append the token `DETAILED_OFFICE` to `archetype_source`.** **`archetype_confidence` is preserved** across the promotion. When `detailed_office=False` (default): no-op. | DESIGN §11 line 467; OVERVIEW lines 67–74, 142 |
| 21 | **§3F — Per-row override merge** (extended Pass-2; renamed from prior §3E "Output assembly"). Runs as the **very last operation before emit**, after rule table, after `detailed_office`. Reads `overrides/archetype_overrides.csv` (path passed via `BuildingClassifier(overrides_path=...)`); when `overrides_path is None` or the file is absent: no-op. CSV schema (manager-pinned): columns `osm_id` (str), `archetype_id` (str — must be in 30-element vocab), `note` (str, optional, default `""`). Left-join on `osm_id`. For matched rows: SET `archetype_id = override_value`; SET `archetype_confidence = "HIGH"`; **REPLACE** `archetype_source = f"OVERRIDE_USER({note})"` (not appended). User override is the strongest signal in the system. | DESIGN §11 lines 468, 482; OVERVIEW lines 76–88, 143 |
| 22 | Output schema: 26 columns = 23 upstream (unchanged, in original fixed order) + 3 appended in this order: `archetype_id`, `archetype_confidence`, `archetype_source` | DESIGN §3F (renamed) lines 268, 270–274; DESIGN §11 line 469 |
| 23 | `archetype_id` and `archetype_confidence` are categorical-eligible (≤30 and exactly 3 distinct values). `archetype_source` is plain object dtype (NOT categorical). | DESIGN §3F lines 274, 276; DESIGN §11 line 469 (cardinality update from 29→30) |
| 24 | **`archetype_source` vocabulary = 14 emit-side / 15 read-side.** Emit-side (14): `RULE_HIGHRISE`, `RULE_RESIDENTIAL_TIER`, `RULE_LODGING_TIER`, `RULE_FUNCTION_TAG`, `RULE_FUNCTION_TAG_SIZE`, `RULE_USE_CLASS`, `RULE_USE_CLASS_SIZE`, `MIXED_USE_DOMINANT_TAG`, `FALLBACK_UNKNOWN`, `HEURISTIC_HEIGHT`, `HEURISTIC_DEFAULT`, `ASSUMPTION_DOE_PROTOTYPE_DERIVED`, `DETAILED_OFFICE`, `OVERRIDE_USER`. Read-side adds (1): `FALLBACK_DEFAULT` (deprecated alias — never emitted by Pass-2 code, but accepted on input for backward compatibility with any pre-Pass-2 artifacts). The retired token `RULE_MIXED_USE` is **not** read-side either. | DESIGN §11 line 468; OVERVIEW lines 82, 103, 144 |
| 25 | **`archetype_source` token assembly order** (manager-pinned, removes ambiguity from "comma-joined alphabetically" wording in §3F line 301; the body's own example at §5.1 line 325 is `RULE_RESIDENTIAL_TIER,HEURISTIC_DEFAULT` — rule-first, NOT alphabetical, so this PLAN follows the example, not the prose): for non-override rows assemble in this insertion order: (1) primary rule token from §3C (e.g. `RULE_FUNCTION_TAG`, `RULE_HIGHRISE`, `MIXED_USE_DOMINANT_TAG`, `FALLBACK_UNKNOWN`); (2) if rule consumed imputed levels: append `HEURISTIC_HEIGHT` or `HEURISTIC_DEFAULT`; (3) if rule has composite annotation (rule 6b): append `ASSUMPTION_DOE_PROTOTYPE_DERIVED`; (4) if §3E promoted Office* → *Detailed: append `DETAILED_OFFICE`. Comma-join with no spaces. **Override (§3F): REPLACES the entire string with `OVERRIDE_USER(<note>)`** (single token, parenthesised note). | DESIGN §3F line 301 (prose); DESIGN §5.1 line 325 (example used as tie-breaker); DESIGN §11 lines 467–468; OVERVIEW lines 70–71, 80, 120 |
| 26 | Both `_validate_input_schema(gdf)` (23-col contract) and `_validate_output_schema(gdf)` (26-col contract) raise `SchemaError` on mismatch — same exception class as Step 1 `_validate_schema()`. Output-side validity: `archetype_id ∈ 30-element vocab`; `archetype_confidence ∈ {HIGH, MEDIUM, LOW}`; every comma-split token of `archetype_source` ∈ 15-element read-side vocab OR matches `OVERRIDE_USER\(.*\)` regex prefix-form. | DESIGN §3F line 278; OVERVIEW line 120 |
| 27 | Persistence: `<output_dir>/02_buildings_classified.gpkg` (layer `buildings`) + `02_buildings_classified.schema.json` (26 entries) + `02_buildings_classified.log` + `02_archetype_distribution.csv`. The function returns the in-process gdf. | DESIGN §3F lines 280–282; DESIGN §4 lines 290–296; OVERVIEW line 83 |
| 28 | `dominant_tag_threshold = 0.60` (`ASSUMPTION_DESIGN_DEFAULT`, OQ-6.5). Implemented as keyword arg with default `0.60` on `BuildingClassifier.__init__` for calibration. | DESIGN §11 lines 463, 479; OVERVIEW lines 27, 106 |
| 29 | Rule 6b: SecondarySchool requires `(function_tag == "school" OR building_tag == "school") AND footprint_area_m2 ≥ 5000` and emits composite token `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED` (`ASSUMPTION_DOE_PROTOTYPE_DERIVED`, OQ-4-FOLLOWUP). | DESIGN §3C line 201; DESIGN §11 line 465; OVERVIEW lines 51–52, 140 |
| 30 | **Synthetic 30-archetype fixture** must include exactly **27 reachable rows** for the default-mode coverage test (30 total − 2 LowITE PHASE_1_UNREACHABLE − 3 `_Detailed` reachable only via `detailed_office=True`). The fixture **must include one `OpenUBEMUnknown` row** (e.g. `building_tag="yes"`, empty function tag, `data_quality_flag="generic_tag"`). LowITE coverage is exercised through a separate ephemeral overrides CSV in tests; `_Detailed` coverage is exercised by re-running the classifier with `detailed_office=True`. | DESIGN §11 line 471; OVERVIEW lines 110, 127 |
| 31 | **Labelled top-1 accuracy gate** (Pass-2 direct edit): on `tests/fixtures/labelled_archetypes_50.csv`, top-1 accuracy ≥ 90% coarse (residential-vs-commercial split) / ≥ 70% fine (full 30-element vocab). CI warn band 80–90% (coarse) / 60–70% (fine); fail < 80% / < 60%. Fixture is **not yet committed** (OQ-7); CI gracefully skips with `pytest.skip("labelled fixture not yet committed")` until it is. All thresholds tagged `ASSUMPTION_DESIGN_DEFAULT`. | DESIGN §5.1 line 326; DESIGN §5.2 line 345; DESIGN §11 lines 500–501 |
| 32 | OVERVIEW additionally requires `02_buildings_classified.log` and `02_archetype_distribution.csv` artifacts (per-archetype row counts) | OVERVIEW line 83; DESIGN §4 lines 293, 295 |

If any of those references appear to disagree with the DESIGN body when Sonnet reads it: **§11 wins**. If §11 itself is silent and OVERVIEW is silent on a load-bearing detail: **STOP and report**.

---

## 5. Task list

> Each task has **What / Why / How / How to test**. Execute in numerical order. After completing a task, append a Progress log entry (§7).

---

### T01 — Scaffold subpackages (`semantic/`, `data/`)

- **What:** Create the file layout in §2 for the four new directory entries: `openubem/semantic/__init__.py` (empty), `openubem/data/__init__.py` (empty), and confirm `tests/fixtures/` exists (Step 1 left a `.gitkeep`). Do **not** yet create `building_classifier.py` or the JSON data files.
- **Why:** Establishes import paths so subsequent tasks can `from openubem.semantic.building_classifier import BuildingClassifier` and `importlib.resources.files("openubem.data")` works. The empty `data/__init__.py` makes `openubem.data` a regular package so `importlib.resources` can read bundled JSON.
- **How:** Use Write tool for both `__init__.py` files (empty content). Confirm `tests/fixtures/` exists.
- **How to test:** `py -c "import openubem.semantic; import openubem.data"` returns cleanly. `py -c "from importlib.resources import files; print(list(files('openubem.data').iterdir()))"` lists at least `__init__.py`.

---

### T02 — Bundle `openstudio_archetypes.json` (30 entries, SemVer-pinned)

- **What:** Create `openubem/data/openstudio_archetypes.json` containing **30 archetypes** — the 29 from DESIGN §3B body table (lines 116–147) plus the synthetic `OpenUBEMUnknown` sentinel (Pass-2). Each entry is an object with keys `archetype_id`, `sector`, `default_size_signature`, `default_standard_family`, `phase_1_unreachable` (bool), `notes` (optional str). Top-level wrapper: `{"schema_version": "1.0.0", "source": "OpenStudio Building Types and Templates.pdf §1 (29 entries) + Pass-2 OpenUBEMUnknown sentinel (DESIGN §11 line 464)", "archetypes": [...]}`.
- **Why:** Pass-2 §11 line 464 mandates the 30-element vocabulary. SemVer pinning supports change auditing. Module 04 (Stage 3) reads this file to look up construction-set/loads pathways indexed by `archetype_id`.
- **How:**
  - Order: entries 1–29 follow DESIGN §3B body table order (1 = SmallOffice through 29 = SuperTallBuilding); entry 30 = `OpenUBEMUnknown`.
  - For entry 30 (`OpenUBEMUnknown`): `sector="Fallback"`, `default_size_signature="any"`, `default_standard_family="ASHRAE 90.1 pre-1980 permissive (Module 04 special case)"`, `phase_1_unreachable=false` (it IS reachable — via rule 17), `notes="Synthetic FALLBACK sentinel; reachable only via rule 17 (FALLBACK_UNKNOWN) or per-row override (OVERRIDE_USER); Module 06b uses PDE-only sampling for this archetype"`.
  - For entries 23 (`SmallDataCenterLowITE`) and 25 (`LargeDataCenterLowITE`): `phase_1_unreachable=true`, `notes="Reachable only via overrides/archetype_overrides.csv; no OSM signal distinguishes High-ITE from Low-ITE"`.
  - For all other 27 entries: `phase_1_unreachable=false`.
  - Verbatim string fields — `archetype_id` values must match rule-table outputs and §3E `_Detailed` promotion outputs exactly.
- **How to test:** Covered by T14's `TestOpenStudioArchetypeRegistry` (asserts 30 entries, `archetype_id` uniqueness, `schema_version` present, exactly 2 entries with `phase_1_unreachable=true`, presence of `OpenUBEMUnknown`).

---

### T03 — Bundle `osm_to_use_class.json` (closed mapping → 6 use-classes)

- **What:** Create `openubem/data/osm_to_use_class.json` containing the verbatim mapping from DESIGN §3A table (lines 99–104). Schema:
  ```json
  {
    "schema_version": "1.0.0",
    "source": "DESIGN §3A; Technical Pipeline §5 Module 03 OSM_TO_OPENSTUDIO_TYPE lines 729-801",
    "use_classes": ["residential","commercial","industrial","institutional","mixed","unknown"],
    "tag_to_use_class": {"apartments":"residential", "office":"commercial", "warehouse":"industrial", "...":"..."},
    "ambiguous_tokens": ["yes",""]
  }
  ```
- **Why:** Closed vocabulary loaded once at module import keeps the §3A normaliser pure-functional (no inline literals inside helpers, no drift between code and spec). DESIGN §3A line 95 explicitly grounds this table in the spec source.
- **How:**
  - Each value in `tag_to_use_class` must be one of the six values in `use_classes`.
  - `ambiguous_tokens` lists tokens that resolve to `unknown` when found in `building_tag` only.
  - Tokens that may co-present with another use-class to produce `mixed` are NOT enumerated here — `mixed` is an emergent property of two-tag disagreement, computed in code (T04).
- **How to test:** Covered by T14's `TestUseClassMapping` (every value ∈ closed 6-element set; assert specific examples like `apartments → residential`, `restaurant → commercial`, `school → institutional`, `data_center → industrial`).

---

### T04 — `_normalise_use_class(row) → tuple[str, float]` (Stage 3A)

- **What:** Implement `_normalise_use_class(row: pd.Series, dominant_tag_threshold: float = 0.60) -> tuple[str, float]` returning `(use_class, dominant_tag_score)`. `use_class` is one of the six closed classes. `dominant_tag_score` is in `[0.0, 1.0]`. Reads `function_tag` and `building_tag` from `row` and consults the bundled `osm_to_use_class.json` (loaded once at module level via `importlib.resources`).
- **Why:** DESIGN §3A separates open-vocabulary OSM tags from closed use-class space so the §3C rule table stays small. The function/building priority is mandated by DESIGN §3A line 106. **Pass-2 (DESIGN §11 line 463) extends 3A to additionally compute `dominant_tag_score`** as the substrate for §3C Rule 15.
- **How:**
  - At module top: `_OSM_TO_USE_CLASS = json.loads(files("openubem.data").joinpath("osm_to_use_class.json").read_text())`. Cache as a frozen dict.
  - Resolution order:
    1. Lookup `function_tag` in `tag_to_use_class` → `uc_function` (or `None` if missing/empty/unmapped).
    2. Lookup `building_tag` in `tag_to_use_class` → `uc_building` (or `None` if missing/empty/`yes`/unmapped).
    3. If both resolve and **agree** → `use_class = that class`; `dominant_tag_score = 1.0`.
    4. If both resolve and **disagree** → `use_class = "mixed"`; `dominant_tag_score = 0.5` (each tag contributes equally to a different class — neither dominates).
    5. If only `uc_function` resolves → `use_class = uc_function`; `dominant_tag_score = 1.0`.
    6. If only `uc_building` resolves → `use_class = uc_building`; `dominant_tag_score = 1.0`.
    7. If neither resolves → `use_class = "unknown"`; `dominant_tag_score = 0.0`.
  - The `dominant_tag_threshold` parameter is **read by §3C Rule 15**, not by 3A itself — but it is plumbed through the call chain so the threshold is available where rule 15 evaluates.
  - Phase-1 score formula: `1.0` for unanimous (cases 3/5/6), `0.5` for two-tag disagreement (case 4), `0.0` for no resolution (case 7). With the default threshold `0.60`: case 3/5/6 (score=1.0) routes through Rule 15 to the dominant-tag's normal rules; case 4 (score=0.5 < 0.60) falls through to Rule 16's `MidriseApartment`. Phase-2 may grow this to a richer score that incorporates `surplus_tags` co-presence; for now the simple two-tag formula is sufficient (per OQ-6.5 calibration sweep).
- **How to test:** Covered by T14's `TestNormaliseUseClass` (≥10 unit fixtures: pure residential → `("residential", 1.0)`; pure commercial → `("commercial", 1.0)`; function/building disagreement → `("mixed", 0.5)`; both empty → `("unknown", 0.0)`; generic `building=yes` only → `("unknown", 0.0)`; function only → use returns 1.0; building only → returns 1.0; agreement returns 1.0; unmapped exotic token → `("unknown", 0.0)`; data_center → `("industrial", 1.0)`).

---

### T05 — `_impute_levels(row, floor_to_floor_m=3.5) → tuple[int, str]` (Stage 3D helper)

- **What:** Implement `_impute_levels` exactly as DESIGN lines 238–253 specify. Returns `(imputed_levels: int, provenance_token: str)` where the token is one of `{"OSM_OBSERVED", "HEURISTIC_HEIGHT", "HEURISTIC_DEFAULT"}`.
- **Why:** Rules 1, 2, 3 read `levels`. Step 1 makes `levels` `Int64`-nullable; without imputation, NaN rows would be silently mis-routed by the rule table.
- **How:** Verbatim copy of DESIGN lines 248–253 logic. Decision tree:
  1. `pd.notna(row["levels"])` → `(int(row["levels"]), "OSM_OBSERVED")`
  2. `pd.notna(row["height_m"]) and row["height_m"] > 0` → `(max(1, int(row["height_m"] // floor_to_floor_m)), "HEURISTIC_HEIGHT")`
  3. else → `(1, "HEURISTIC_DEFAULT")`
- **CRITICAL INVARIANT (DESIGN §3D line 256, §4 row-level guarantee #4 line 302):** This helper is read-only with respect to the 23 binding upstream columns. Do NOT write to `provenance_levels` or any other upstream column. The imputed value is consumed only by T06; the provenance token flows into `archetype_source` (T10), not into `provenance_levels`.
- **How to test:** Covered by T14's `TestImputeLevels` (5 unit fixtures: observed integer → `(N, "OSM_OBSERVED")`; observed float gets `int()`-cast; NaN levels + 7 m height → `(2, "HEURISTIC_HEIGHT")`; NaN levels + 3 m height → `(1, "HEURISTIC_HEIGHT")` (max(1, 0)); NaN levels + NaN height → `(1, "HEURISTIC_DEFAULT")`). Plus an invariant test: assert `row["provenance_levels"]` is unchanged across the call.

---

### T06 — `_apply_rule_table(...)` (Stage 3C, 17 ordered first-match-wins rules)

- **What:** Implement `_apply_rule_table(row: pd.Series, levels_imputed: int, use_class: str, dominant_tag_score: float, *, dominant_tag_threshold: float = 0.60, high_rise_levels_threshold: int = 20, super_tall_levels_threshold: int = 40) -> tuple[str, str]` returning `(archetype_id, rule_source_token)`. The 17 rules from DESIGN §3C lines 188–218 (with Pass-2 deltas for rules 6b/15/16/17 from §11 line 465) are evaluated in numerical order; the first match returns immediately.
- **Why:** Heart of Step 2. Determinism + traceability come from explicit ordering. Every classification carries a token naming which rule fired.
- **How:**
  - Rules are encoded as a sequence of `if`/`elif` blocks in the order 1a, 1b, 2a, 2b, 3a, 3b, 4a, 4b, 5a, 5b, 6a, 6b, 6c, 7, 8, 9a, 9b, 10, 11a, 11b, 11c, 12a, 12b, 12c, 13, 14, 15, 16, 17. Each block has an explicit boolean expression matching DESIGN §3C column 2 (Trigger) **with the parenthesisation DESIGN line 186 mandates**.
  - **TallBuilding override exemptions (DESIGN line 184):** rules 1a/1b only fire when `use_class ∈ {"commercial", "institutional", "mixed", "unknown"}`. Residential, industrial, and rows whose `function_tag` or `building_tag` is in `{"data_center","datacenter"}` are exempt — for residential the §3C residential tier rules 2a/2b take over; for industrial rule 13 applies; for data centers rules 9a/9b apply.
  - Use `levels_imputed` (the int returned by T05), not `row["levels"]`, anywhere a rule reads levels.
  - **Rule 6b — composite token:** `((function_tag == "school") OR (building_tag == "school")) AND (footprint_area_m2 ≥ 5000)` → archetype `SecondarySchool`, **rule_source_token = `"RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED"`** (the composite literal — DESIGN §11 line 465 + §4 fact #29 above).
  - **Rule 15 — `MIXED_USE_DOMINANT_TAG`:** when `use_class == "mixed" AND dominant_tag_score ≥ dominant_tag_threshold`, **re-evaluate rules 1a–14 against the row but treating `use_class` as the dominant tag's class** (i.e., recursively call the rule sub-table with substituted `use_class`). The recursive call returns `(archetype_id, rule_source_token)`; **overwrite rule_source_token = "MIXED_USE_DOMINANT_TAG"** (the rule-15 emit token replaces the inherited rule's token at emit-time, but the inherited tier is read by §3D for confidence inheritance — fact #14). If recursive re-evaluation also returns `OpenUBEMUnknown` (i.e. the dominant tag's class is `unknown`), bubble that out as-is. **Manager-pinned implementation note**: to compute "dominant tag's class" use the function_tag if it resolved, else the building_tag (case 5/6 in T04 logic).
  - **Rule 16 — no-dominant fallback:** when `use_class == "mixed" AND dominant_tag_score < dominant_tag_threshold`, archetype = `MidriseApartment`, rule_source_token = `"MIXED_USE_DOMINANT_TAG"` (same emit token as rule 15 — both are mixed-use routing decisions made via the dominant-tag mechanism, per §11 line 468 retiring `RULE_MIXED_USE`).
  - **Rule 17 — `FALLBACK_UNKNOWN`:** when `use_class == "unknown"`, archetype = `"OpenUBEMUnknown"`, rule_source_token = `"FALLBACK_UNKNOWN"`.
  - Rules 12a–14: "no specific tag matched above" is a structural condition, not a flag — earlier rules would have fired and returned. Express via rule order.
- **How to test:** Covered by T14's `TestApplyRuleTable`. Mandatory fixtures from DESIGN §5.1 line 325 (with Pass-2 amendments):
  - Rule 1a: `levels=42, use_class=commercial → ("SuperTallBuilding", "RULE_HIGHRISE")`.
  - Rule 2b: `use_class=residential, levels=NaN, height_m=NaN, levels_imputed=1 → ("MidriseApartment", "RULE_RESIDENTIAL_TIER")`.
  - Rule 4b: `function_tag=cafe → ("QuickServiceRestaurant", "RULE_FUNCTION_TAG")`.
  - Rule 6b: `function_tag=school, footprint=6000 → ("SecondarySchool", "RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED")` (composite token).
  - Rule 6c: `function_tag=kindergarten, footprint=800 → ("PrimarySchool", "RULE_FUNCTION_TAG")`.
  - **Rule 17 (Pass-2): `building_tag=yes, function_tag="" → ("OpenUBEMUnknown", "FALLBACK_UNKNOWN")`** (NOT MediumOffice, NOT FALLBACK_DEFAULT).
  - Plus exemption fixtures: residential 25-storey → `("HighriseApartment", "RULE_RESIDENTIAL_TIER")` (NOT TallBuilding); warehouse 25-storey → `("Warehouse", ...)` (NOT TallBuilding); data_center 25-storey + 600 m² → `("LargeDataCenterHighITE", "RULE_FUNCTION_TAG_SIZE")` (NOT TallBuilding).
  - **Rule 15 fixtures:** mixed + agreeing-tags `building=apartments, function=residential` (score=1.0) + 12 storeys → `("HighriseApartment", "MIXED_USE_DOMINANT_TAG")` (rule 2a inherited, but emit token is the rule-15 token).
  - **Rule 16 fixtures:** mixed + disagreeing `building=apartments, function=shop` (score=0.5) + 5 storeys → `("MidriseApartment", "MIXED_USE_DOMINANT_TAG")`.

---

### T07 — `_assign_confidence(...)` (Stage 3D, 3-tier output)

- **What:** Implement `_assign_confidence(row: pd.Series, rule_token: str, levels_source: str, use_class: str, *, inherited_rule_tier: str | None = None) -> str` returning one of `{"HIGH", "MEDIUM", "LOW"}` per DESIGN §3D lines 228–232 with Pass-2 deltas (§11 line 466).
- **Why:** Confidence is what downstream filters and report templates key on. A miscategorised row biases coverage thresholds.
- **How:** Decision tree (evaluate top to bottom; first match wins). The `rule_token` parameter here is the primary token from T06 (or composite head for rule 6b). For rule 15, also pass `inherited_rule_tier` — the tier the inherited rule would have produced — so this helper can implement "no silent inflation":

  1. **Rule-15 inheritance (Pass-2):** if `rule_token == "MIXED_USE_DOMINANT_TAG"` AND the row triggered as mixed-with-dominant (i.e. `inherited_rule_tier is not None`) → return `inherited_rule_tier` verbatim. **No silent inflation: LOW stays LOW, MEDIUM stays MEDIUM, HIGH stays HIGH.**
  2. **Rule-16 (Pass-2):** if `rule_token == "MIXED_USE_DOMINANT_TAG"` AND `inherited_rule_tier is None` (i.e. no-dominant fallback) → `"MEDIUM"`.
  3. **Rule 17 (Pass-2):** if `rule_token == "FALLBACK_UNKNOWN"` → `"LOW"`.
  4. **LOW fallback (still legal even though FALLBACK_DEFAULT is retired emit-side, retained for any pre-Pass-2 input):**
     - `row["provenance_building_tag"] == "OSM_GENERIC" and (row["function_tag"] == "" or pd.isna(row["function_tag"]))` → `LOW`
     - `"generic_tag" in str(row["data_quality_flag"]).split(",") and (row["function_tag"] == "" or pd.isna(row["function_tag"]))` → `LOW`
  5. **MEDIUM:**
     - `rule_token == "RULE_USE_CLASS_SIZE"` → `MEDIUM` (DESIGN §3D row a)
     - `levels_source != "OSM_OBSERVED" and rule_token in {"RULE_HIGHRISE", "RULE_RESIDENTIAL_TIER", "RULE_LODGING_TIER"}` → `MEDIUM` (row b — explicitly includes 1a/1b TallBuilding when levels was imputed, per DESIGN §3D line 231)
     - `row["provenance_function_tag"] == "OSM_MISSING" and row["provenance_building_tag"] == "OSM_OBSERVED" and rule_token != "FALLBACK_UNKNOWN"` → `MEDIUM` (row d)
  6. **HIGH** (default — every remaining case is the direct semantic match path). The composite token `RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED` from rule 6b should be split before the comparisons in steps 4–5; only the head token `RULE_FUNCTION_TAG_SIZE` is consulted for confidence routing (the `ASSUMPTION_*` token is provenance, not a confidence trigger).
- **How to test:** Covered by T14's `TestAssignConfidence` (≥8 fixtures: rule 4b cafe + observed function_tag → HIGH; rule 1a 42-storey + imputed levels → MEDIUM; rule 12b commercial-no-tag → MEDIUM; **rule 17 fallback (`FALLBACK_UNKNOWN`) → LOW**; row with `provenance_building_tag == "OSM_GENERIC"` and empty function → LOW; rule 2a residential 12-storey + observed levels → HIGH; **rule 15 inherited LOW (no inflation) — provide `inherited_rule_tier="LOW"` → LOW**; **rule 16 (`inherited_rule_tier=None`) → MEDIUM**).

---

### T08 — `_apply_detailed_office(...)` (Stage 3E post-processing — NEW Pass-2 sub-stage)

- **What:** Implement `_apply_detailed_office(archetype_id: str, archetype_source: str, *, detailed_office: bool) -> tuple[str, str]` returning the (possibly promoted) `archetype_id` and the (possibly extended) `archetype_source`. When `detailed_office=False`: identity passthrough. When `detailed_office=True`: promote `SmallOffice → SmallOfficeDetailed`, `MediumOffice → MediumOfficeDetailed`, `LargeOffice → LargeOfficeDetailed`, and append `,DETAILED_OFFICE` to `archetype_source`. Other archetypes pass through unchanged.
- **Why:** Pass-2 §11 line 467 added §3E as a distinct sub-stage between §3D and §3F. Module 03 owns `archetype_id` so the `_Detailed` opt-in is wired here, not in Module 04 or `run_ubem` (OVERVIEW line 142).
- **How:**
  - Three-entry mapping `_DETAILED_OFFICE_PROMOTION = {"SmallOffice": "SmallOfficeDetailed", "MediumOffice": "MediumOfficeDetailed", "LargeOffice": "LargeOfficeDetailed"}`.
  - When `detailed_office=True` AND `archetype_id in _DETAILED_OFFICE_PROMOTION`: return promoted id and `f"{archetype_source},DETAILED_OFFICE"`.
  - Otherwise: return inputs unchanged.
  - **Confidence is preserved** — this helper does not touch `archetype_confidence`. The orchestrator simply leaves the column untouched during this pass (OVERVIEW line 71 "archetype_confidence preserved").
- **How to test:** Covered by T14's `TestApplyDetailedOffice` (5 fixtures): `(MediumOffice, "RULE_USE_CLASS_SIZE", detailed_office=False) → unchanged`; `(MediumOffice, "RULE_USE_CLASS_SIZE", detailed_office=True) → ("MediumOfficeDetailed", "RULE_USE_CLASS_SIZE,DETAILED_OFFICE")`; `(SmallOffice, ...) → SmallOfficeDetailed`; `(LargeOffice, ...) → LargeOfficeDetailed`; `(MidriseApartment, "RULE_RESIDENTIAL_TIER", detailed_office=True) → unchanged` (non-Office archetype).

---

### T09 — `_apply_overrides(...)` (Stage 3F per-row override merge — NEW Pass-2 sub-stage)

- **What:** Implement `_apply_overrides(gdf: gpd.GeoDataFrame, overrides_path: Path | None) -> gpd.GeoDataFrame` that left-joins `overrides/archetype_overrides.csv` on `osm_id`. For matched rows, SETS `archetype_id` to the override value, FORCES `archetype_confidence = "HIGH"`, REPLACES `archetype_source = f"OVERRIDE_USER({note})"`. When `overrides_path is None` or the file does not exist: identity passthrough.
- **Why:** Pass-2 §11 lines 468 + 482 introduce the per-row override CSV as the documented escape-hatch for OSM-unobservable archetype distinctions (motivating use case: LowITE DataCenter routing, but mechanism generalises). User override is the strongest signal in the system and dominates rule-table + detailed_office decisions (OVERVIEW line 143).
- **How:**
  - CSV schema (manager-pinned, fact #21): columns `osm_id` (str), `archetype_id` (str — must be in the 30-element vocab), `note` (str, optional, default `""` if missing or NaN).
  - Behaviour:
    - If `overrides_path is None`: return `gdf` unchanged.
    - If `overrides_path is not None and not Path(overrides_path).exists()`: log a `logger.info(f"overrides_path {overrides_path} not found; skipping override merge")` and return `gdf` unchanged.
    - Else: read CSV via `pd.read_csv(overrides_path, dtype=str).fillna({"note": ""})`. Validate that every `archetype_id` in the override CSV is in the 30-element vocab (else raise `SchemaError(f"override archetype_id {x} not in 30-element vocab")`). Validate that every `osm_id` appears at most once in the CSV (else raise `SchemaError("duplicate osm_id in override CSV")`).
    - Left-join on `osm_id`. For matched rows: `archetype_id` ← override; `archetype_confidence` ← `"HIGH"`; `archetype_source` ← `f"OVERRIDE_USER({note})"` (replaced, not appended). Unmatched rows are unchanged.
    - **Idempotency:** running twice with the same overrides_path on the orchestrator output produces identical output (the override-set rows are already at the override values, so the second join is a no-op replacement to the same values).
- **How to test:** Covered by T14's `TestApplyOverrides` (5 fixtures): `overrides_path=None → no-op`; `overrides_path` points to non-existent file → no-op + INFO log; valid CSV with 1 matched osm_id → that row's archetype_id changes, confidence becomes HIGH, source becomes `OVERRIDE_USER(<note>)`; CSV with 1 LowITE override → LowITE archetype emitted (PHASE_1_UNREACHABLE bypass works); CSV with invalid archetype_id → raises `SchemaError`; CSV with duplicate osm_id → raises `SchemaError`. Build the ephemeral CSV inside `tempfile.mkdtemp()` (mirror Step 1 T11 Windows-permission pattern).

---

### T10 — `BuildingClassifier` class + per-row helper + orchestrator (`classify` method)

- **What:** Two public surfaces:
  1. **`classify_building(row: pd.Series, *, detailed_office: bool = False, dominant_tag_threshold: float = 0.60, high_rise_levels_threshold: int = 20, super_tall_levels_threshold: int = 40, floor_to_floor_m: float = 3.5) -> tuple[str, str, str]`** — per-row unit-of-work returning `(archetype_id, archetype_confidence, archetype_source)`. Internally calls T04 → T05 → T06 → T07 → T08 in that order. **Override merge is NOT applied here** — overrides are §3F-only, applied in the orchestrator (DESIGN §11 line 468; fact #21).
  2. **`class BuildingClassifier`** — public class with:
     - `__init__(self, detailed_office: bool = False, overrides_path: Path | None = None, dominant_tag_threshold: float = 0.60, high_rise_levels_threshold: int = 20, super_tall_levels_threshold: int = 40, floor_to_floor_m: float = 3.5) -> None` (stores params as attributes).
     - `classify(self, gdf: gpd.GeoDataFrame, output_dir: Path | None = None) -> gpd.GeoDataFrame` — the orchestrator. Validates input schema (T11), applies `classify_building` row-wise, applies `_apply_overrides` (T09), validates output schema, emits the `all_fallback_archetype` warning if applicable, optionally serialises (T12), returns the gdf.
- **Why:** Pass-2 (DESIGN §11 lines 467, 480; OVERVIEW lines 68, 142) wires `detailed_office` and `overrides_path` into Module 03's `BuildingClassifier.__init__`. The class shape is a deliberate departure from §3 body's free-function `classify_building_gdf`. Splitting per-row helper from the orchestrator lets T14 unit-test each rule path against a synthetic `pd.Series` without building a full GeoDataFrame.
- **How:**
  - **`classify_building` source-string assembly** (per fact #25 token order): start with rule_token from T06 (already a comma-joined string for rule 6b's composite). If rule consumed levels (rules 1a/1b/2a/2b/3a/3b/15-when-inherited/16) AND `levels_source != "OSM_OBSERVED"`: append `,HEURISTIC_HEIGHT` or `,HEURISTIC_DEFAULT`. Pass through T08's `_apply_detailed_office` for the optional `,DETAILED_OFFICE` append.
  - For rules that did **not** consume levels (4a/4b/5a/5b/6a/6b/6c/7/8/9a/9b/10/11a/11b/11c/12a/12b/12c/13/14/17), do **not** append the heuristic token even when levels was imputed — the imputed value did not influence the answer.
  - `BuildingClassifier.classify` row-wise application: use `gdf.apply(lambda row: classify_building(row, detailed_office=self.detailed_office, dominant_tag_threshold=self.dominant_tag_threshold, ...), axis=1, result_type="expand")` and assign the resulting three columns. Vectorised numpy is out of scope — clarity over micro-optimisation in Phase 1.
  - Logger: `logger = logging.getLogger("openubem.semantic")` at module top.
  - **`all_fallback_archetype` warning (Pass-2):** emit exactly ONE `logger.warning(json.dumps({"event": "all_fallback_archetype", "n_rows": len(gdf), "archetype_id": "OpenUBEMUnknown"}))` if `(gdf["archetype_id"] == "OpenUBEMUnknown").all() and (gdf["archetype_confidence"] == "LOW").all() and len(gdf) > 0`. **Never raise.** Flow through. (Pass-2 §11 line 488.)
  - **Override merge:** call `_apply_overrides(gdf, self.overrides_path)` AFTER row-wise classification + detailed_office post-pass and BEFORE byte-equality assert / output schema validation.
  - **Byte-equality assert:** at the end of the orchestrator (after override merge — overrides only modify the 3 appended columns, not the upstream 23), `pd.testing.assert_frame_equal(input_gdf.reset_index(drop=True), out_gdf[input_gdf.columns].reset_index(drop=True))` to enforce DESIGN line 268 + line 256 invariant. If this fires, the implementation has a bug — fix the implementation, do not weaken the assert.
  - **Idempotency:** the function must be a pure transform. `BuildingClassifier(...).classify(BuildingClassifier(...).classify(gdf)[input_cols])` returns identical output (per OVERVIEW line 126 — same input + same `overrides_path` + same `detailed_office` flag ⇒ same output).
- **How to test:** Covered by T14's `TestClassifyBuildingRow` (per-row helper end-to-end) and `TestBuildingClassifier` (orchestrator: byte-equality, idempotency, 26-col output schema, deterministic on repeat).

---

### T11 — `_validate_input_schema(gdf)` and `_validate_output_schema(gdf)` (DESIGN §3F line 278)

- **What:** Two helpers that raise a `SchemaError` (custom exception class, defined at module top) on mismatch.
- **Why:** Schema validation gates downstream chaining (`enrich_buildings` etc.). Drift here breaks downstream silently.
- **How:**
  - `class SchemaError(ValueError): ...` at module top.
  - `_INPUT_SCHEMA_COLUMNS` = the 23 columns from `openubem.acquisition.osm_fetcher._SCHEMA_COLUMNS` (import the constant; do not duplicate the list — drift risk).
  - `_OUTPUT_SCHEMA_COLUMNS` = `_INPUT_SCHEMA_COLUMNS + ["archetype_id", "archetype_confidence", "archetype_source"]`.
  - `_validate_input_schema(gdf)`: assert `len(gdf.columns) == 23`; assert column order matches `_INPUT_SCHEMA_COLUMNS` exactly; raise `SchemaError` with the offending column name in the message.
  - `_validate_output_schema(gdf)`:
    - assert `len(gdf.columns) == 26`; assert column order matches `_OUTPUT_SCHEMA_COLUMNS`.
    - assert `gdf["archetype_id"].isin(VALID_30).all()` (where `VALID_30` is loaded from `openstudio_archetypes.json`).
    - assert `gdf["archetype_confidence"].isin({"HIGH","MEDIUM","LOW"}).all()`.
    - **Token validation regex:** for each `archetype_source` value, split on `,` and assert each token is either (a) in the 15-element read-side vocab `{RULE_HIGHRISE, RULE_RESIDENTIAL_TIER, RULE_LODGING_TIER, RULE_FUNCTION_TAG, RULE_FUNCTION_TAG_SIZE, RULE_USE_CLASS, RULE_USE_CLASS_SIZE, MIXED_USE_DOMINANT_TAG, FALLBACK_UNKNOWN, FALLBACK_DEFAULT, HEURISTIC_HEIGHT, HEURISTIC_DEFAULT, ASSUMPTION_DOE_PROTOTYPE_DERIVED, DETAILED_OFFICE}` (14 tokens — `OVERRIDE_USER` is matched by regex separately) OR (b) matches the regex `^OVERRIDE_USER\(.*\)$` (parenthesised-note prefix). Raise `SchemaError` with offending token + first row index.
  - **Row-level guarantee #6 (Pass-2 §11 line 469):** assert that every row with `archetype_id == "OpenUBEMUnknown"` has either `archetype_confidence == "LOW" AND archetype_source contains "FALLBACK_UNKNOWN"`, OR `archetype_source` matches `OVERRIDE_USER(...)`. Raise `SchemaError` on violation.
- **How to test:** Covered by T14's `TestSchemaValidation` (correct 23-col gdf passes input validator; 22-col raises; 23-col with wrong order raises; correct 26-col passes output validator; out-of-vocab `archetype_id` raises; bad confidence value raises; unknown token in `archetype_source` raises; valid `OVERRIDE_USER(some note)` token passes; `OpenUBEMUnknown` row with HIGH confidence and no FALLBACK_UNKNOWN raises — guarantee #6).

---

### T12 — Serialisation (`.gpkg` + `.log` + `.schema.json` + distribution CSV)

- **What:** When `output_dir` is non-None on `BuildingClassifier.classify`, write four artifacts:
  - `<output_dir>/02_buildings_classified.gpkg` (layer `"buildings"`, driver `"GPKG"`)
  - `<output_dir>/02_buildings_classified.log` (per-row classification trace + summary; via scoped `logging.FileHandler`)
  - `<output_dir>/02_buildings_classified.schema.json` (26 entries, each `{name, dtype, provenance_role, vocabulary?}`)
  - `<output_dir>/02_archetype_distribution.csv` (one row per distinct `archetype_id` present, columns: `archetype_id, n_rows, pct_of_total, mean_floor_area_m2, mean_levels`; sorted by `n_rows` desc)
- **Why:** OVERVIEW + DESIGN §4 binding output contract (lines 290–296). The scoped FileHandler keeps multi-call sessions from cross-contaminating logs (mirror Step 1 T11 pattern).
- **How:**
  - Add `output_dir: Path | None = None` parameter to `BuildingClassifier.classify`. When `None`: skip all four writes; still return the gdf.
  - Mirror Step 1 `_serialize` lifecycle: install FileHandler on `openubem.semantic` logger at INFO inside `try`; remove + close inside `finally`.
  - `provenance_role` for the 3 new columns: `archetype_id` → `"derived"`, `archetype_confidence` → `"derived"`, `archetype_source` → `"provenance"`. For the 23 upstream columns, copy the role from Step 1's schema (re-derive by reading `openubem.acquisition.osm_fetcher` constants).
  - `vocabulary` field in schema.json: present for `archetype_id` (the 30-element list) and `archetype_confidence` (`["HIGH","MEDIUM","LOW"]`); absent for `archetype_source` (open-ended due to `OVERRIDE_USER(<note>)`).
  - Distribution CSV: build via `gdf.groupby("archetype_id").agg(n_rows=("osm_id", "count"), mean_floor_area_m2=("footprint_area_m2", "mean"), mean_levels=("levels", "mean")).reset_index()`, then add `pct_of_total = n_rows / len(gdf) * 100`, sort by `n_rows` descending, write via `pd.DataFrame.to_csv(index=False)`.
  - Always return the gdf in-process.
- **How to test:** Covered by T14's `TestSerialize` (pass `output_dir=tempfile.mkdtemp()` with a small synthetic gdf; assert all 4 files exist; assert `.gpkg` round-trips back to 26 columns; assert `.schema.json` has 26 entries with `{name, dtype, provenance_role}` keys; assert distribution CSV has one row per distinct archetype). Use `tempfile.mkdtemp() + shutil.rmtree` rather than pytest's `tmp_path` (Step 1 T11 documented Windows permission issues with `tmp_path`).

---

### T13 — Synthetic 30-archetype coverage fixture builder

- **What:** Add a pytest fixture (`@pytest.fixture(scope="session")`) in `tests/test_building_classifier.py` named `synthetic_30_gdf` that builds a 23-column GeoDataFrame with one minimum-viable row per **default-reachable** archetype — exactly **27 rows** (30 total − 2 LowITE PHASE_1_UNREACHABLE − 3 `_Detailed` reachable only via `detailed_office=True`).
- **Why:** Pass-2 §11 line 471 mandates the synthetic-30 fixture: it exercises every rule path on every CI run, catching rule-table regressions before they hit real fixtures. Lighter than Boston/Phoenix/Chicago `.osm` files and doesn't require live network.
- **How:**
  - Build via inline geopandas/shapely: 27 small unit-square Polygons translated by row index so they don't overlap; populate the 23 upstream columns with the minimum tags + levels + footprint each rule needs.
  - **Mandatory `OpenUBEMUnknown` row** (DESIGN §11 line 471 + OVERVIEW line 127): `building_tag="yes", function_tag="", data_quality_flag="generic_tag", provenance_building_tag="OSM_GENERIC", provenance_function_tag="OSM_MISSING", levels=2`. Rule 17 must fire.
  - Examples for the others: row 1 (SmallOffice) → `building_tag="office"`, `levels=2`, `footprint_area_m2=200`; row 5 (LargeOffice) → `building_tag="office"`, `footprint_area_m2=5000`; row 14 (MidriseApartment) → `building_tag="apartments"`, `levels=5`; row 28 (TallBuilding) → `building_tag="office"`, `levels=25`; row 29 (SuperTallBuilding) → `building_tag="office"`, `levels=45`.
  - Provenance columns set to plausible `OSM_OBSERVED` defaults; `data_quality_flag = ""` (except for the `OpenUBEMUnknown` row).
  - Persist the constructed GDF to `tests/fixtures/synthetic_30_archetype_coverage.gpkg` via `gdf.to_file(...)` only on first build (cache-and-skip pattern); subsequent test runs read the cached file.
  - Document in the fixture builder's docstring the **5 archetypes excluded from default coverage**: 2 LowITE (PHASE_1_UNREACHABLE — exercised separately via override CSV in `TestApplyOverrides`) + 3 `_Detailed` (exercised by re-running the classifier with `detailed_office=True` on the existing Office rows, in `TestApplyDetailedOffice`).
- **How to test:** Covered by T14's `TestArchetypeCoverage30`: `set(BuildingClassifier().classify(synthetic_30_gdf)["archetype_id"]) == EXPECTED_27_REACHABLE` (the 27 default-reachable archetypes). The 5 excluded are asserted absent in the default-mode output but reachable in their respective tests (LowITE via overrides, `_Detailed` via `detailed_office=True`).

---

### T14 — Tests (`tests/test_building_classifier.py`)

- **What:** Comprehensive test suite organised by concern, mirroring Step 1's `tests/test_osm_fetcher.py` structure. All tests pure-Python — no live network, no real `.osm` files.
- **Why:** DESIGN §5.1 thresholds and per-row fixtures need automated guardrails. CI must be deterministic and fast.
- **How:** Test classes (each method one assertion-cluster, focused). Targets ≥30 test methods total.
  - **TestOpenStudioArchetypeRegistry** — JSON loadable; **exactly 30 entries**; `archetype_id` uniqueness; `schema_version` present; `OpenUBEMUnknown` present; exactly 2 entries with `phase_1_unreachable=true` (the two LowITE).
  - **TestUseClassMapping** — JSON loadable; values ⊆ 6 closed classes; spot-check ≥6 entries.
  - **TestNormaliseUseClass** — ≥10 fixtures per T04 (including `dominant_tag_score` assertions).
  - **TestImputeLevels** — 5 fixtures per T05. Critically, assert `provenance_levels` is unchanged across the call (invariant test).
  - **TestApplyRuleTable** — 6 base fixtures (rules 1a, 2b, 4b, 6b composite, 6c, **17 → OpenUBEMUnknown/FALLBACK_UNKNOWN**) + 3 exemption fixtures (residential 25-storey, warehouse 25-storey, data_center 25-storey) + 2 mixed-use fixtures (rule 15 agreeing tags 12-storey → HighriseApartment + MIXED_USE_DOMINANT_TAG; rule 16 disagreeing tags 5-storey → MidriseApartment + MIXED_USE_DOMINANT_TAG).
  - **TestAssignConfidence** — ≥8 fixtures per T07 (including rule 15 inherited-LOW returns LOW, rule 16 returns MEDIUM, rule 17 returns LOW).
  - **TestApplyDetailedOffice** — 5 fixtures per T08.
  - **TestApplyOverrides** — 5 fixtures per T09 (no-op, missing file, single match, LowITE override, invalid archetype_id raises, duplicate osm_id raises).
  - **TestClassifyBuildingRow** — per-row helper end-to-end: assert the full `(archetype_id, archetype_confidence, archetype_source)` triple for each of the §5.1-style fixtures (Pass-2 amended). Specifically rule 2b NaN-levels-NaN-height case asserts `archetype_source == "RULE_RESIDENTIAL_TIER,HEURISTIC_DEFAULT"` (DESIGN §5.1 line 325). Specifically rule 17 case asserts `("OpenUBEMUnknown", "LOW", "FALLBACK_UNKNOWN")` (Pass-2).
  - **TestBuildingClassifier** — orchestrator: (a) byte-equality of upstream 23 columns via `assert_frame_equal`; (b) determinism (call twice, identical output); (c) idempotency (`BuildingClassifier(...).classify(BuildingClassifier(...).classify(gdf)[in_cols]) == BuildingClassifier(...).classify(gdf)`); (d) 26-col output schema; (e) all `archetype_id` values ∈ 30-element vocab; (f) all `archetype_confidence` values ∈ `{HIGH, MEDIUM, LOW}`; (g) every emit-side `archetype_source` token ∈ 14-element emit-side vocab plus `OVERRIDE_USER(<note>)` regex; (h) `detailed_office=True` produces `_Detailed` archetypes for any office rows; (i) `overrides_path` correctly applies for matched osm_ids.
  - **TestAllFallbackNeighbourhood** — synthetic 3-row gdf where every row has `building_tag == "yes"`, `function_tag == ""`, `data_quality_flag == "generic_tag"`, observed levels. Use `caplog` at `WARNING` level on the `openubem.semantic` logger; assert exactly ONE warning whose JSON payload parses to `{"event": "all_fallback_archetype", "n_rows": 3, "archetype_id": "OpenUBEMUnknown"}`. (Pass-2: payload archetype_id is `OpenUBEMUnknown`, NOT `MediumOffice`.) Assert gdf returned non-empty (no raise).
  - **TestSchemaValidation** — per T11, including the row-level guarantee #6 assertion (`OpenUBEMUnknown` row with HIGH+no-FALLBACK_UNKNOWN raises).
  - **TestSerialize** — per T12.
  - **TestArchetypeCoverage30** — per T13: 27 default-reachable archetypes covered by synthetic gdf; 2 LowITE archetypes reachable when overrides CSV provided; 3 `_Detailed` archetypes reachable when `detailed_office=True`.
  - **TestLabelledTop1Accuracy** — per fact #31. Use `pytest.skip("labelled fixture not yet committed (OQ-7)")` if `tests/fixtures/labelled_archetypes_50.csv` does not exist. Otherwise: load CSV, run classifier, compute coarse + fine top-1 accuracy, assert against the warn/fail bands.
- **How to test:** `py -m pytest tests/test_building_classifier.py -v` from project root → 100% pass (or skip on the labelled-accuracy gate). Step 1 tests must still pass (`py -m pytest tests/ -v` shows the Step 1 baseline plus Step 2 additions).

---

### T15 — `pyproject.toml` package-data + module docstring + version bump

- **What:** Three small bookkeeping changes:
  1. In `pyproject.toml`, ensure `[tool.setuptools.packages.find]` discovers `openubem.semantic` and `openubem.data` (likely automatic via `find_packages`; verify by `pip install -e .` then `py -c "import openubem.data, openubem.semantic"`).
  2. Add `[tool.setuptools.package-data]` block: `openubem.data = ["*.json"]` so the JSON files ship inside the wheel.
  3. Module-level docstring at the top of `openubem/semantic/building_classifier.py` referencing DESIGN §3A–3F section anchors and DESIGN §11 Pass-2 (one short paragraph; no multi-paragraph essay).
- **Why:** Without `package-data`, `importlib.resources` finds the JSON files in editable installs but not in built wheels — silent breakage when the package is `pip install`-ed from a built artifact. Module docstring anchors the file to its spec for future auditors.
- **How:** Standard `pyproject.toml` edits; version of `openubem` package can stay at the Step 1 value (manager bumps the project version separately when releasing).
- **How to test:** `py -m build --wheel` produces a wheel; unzip it and confirm `openubem/data/openstudio_archetypes.json` and `openubem/data/osm_to_use_class.json` are inside. (Optional smoke; skip if `build` is not installed and document in the progress log.)

---

## 6. Stop-and-report points

Pause and report to the manager at each of these checkpoints (do not just push through):

- **CP1 — after T03:** Subpackages scaffolded and JSON data files bundled. No logic yet. Sonnet reports: file tree, JSON content checksums (`hashlib.sha256` of each file), and confirms `py -c "from importlib.resources import files; import json; data = json.loads(files('openubem.data').joinpath('openstudio_archetypes.json').read_text()); print(len(data['archetypes']))"` prints `30`. Manager reviews the JSON files for vocabulary fidelity (30 entries, `OpenUBEMUnknown` present, 2 LowITE flagged `phase_1_unreachable`) before greenlighting T04+.

- **CP2 — after T10:** Classifier core is complete (3A normaliser + 3D imputer + 3C rule table + 3D confidence + 3E detailed_office + 3F override merge + orchestrator). Sonnet runs `py -m pytest tests/test_building_classifier.py::TestApplyRuleTable tests/test_building_classifier.py::TestApplyDetailedOffice tests/test_building_classifier.py::TestApplyOverrides tests/test_building_classifier.py::TestClassifyBuildingRow tests/test_building_classifier.py::TestBuildingClassifier -v` (the unit-of-work tests; T13/T14 may still be partial at this point — that's fine; the rule table + post-passes are the load-bearing pieces) and reports the summary plus any DESIGN ambiguity. Manager spot-checks: rule-table boundary cases (rule 1a/1b cutoff at levels=20, rule 6b cutoff at footprint=5000, rule 9a/9b cutoff at footprint=500); rule 17 → OpenUBEMUnknown/FALLBACK_UNKNOWN; rule 15/16 dominant-tag routing; detailed_office promotion; override merge final-write semantics. Greenlight T11+.

- **CP3 — after T15:** Full suite green. Sonnet reports: file tree, full `py -m pytest tests/ -v` summary (Step 1 tests + Step 2 tests, target ≥46 + ~35 = ~81 passing, with `TestLabelledTop1Accuracy` skipped pending OQ-7 fixture), any DESIGN ambiguities encountered, any deviation from this plan with rationale. Manager audits before greenlighting Step 3 planning.

If any DESIGN reference in §4 appears to disagree with the DESIGN body when Sonnet reads it: **§11 wins** (per Hard Rule #5). If §11 itself is silent: STOP and quote.

---

## 7. Progress log

> Append one entry per completed task. Newest entries at the bottom.

```
#### TXX — <short title> — completed YYYY-MM-DD

- **Artifacts:** <paths produced or modified>
- **Deviations:** <none | list with rationale and DESIGN/§11/OVERVIEW cite>
- **Test status:** <pytest summary, e.g. "12 passed in 0.3s">
- **Notes:** <anything the next executor or auditor should know>
```

<!-- entries go below this line -->

#### T01 — Scaffold subpackages (semantic/, data/) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/__init__.py` (empty), `openubem/data/__init__.py` (empty)
- **Deviations:** none
- **Test status:** `py -c "import openubem.semantic; import openubem.data"` → ok; `importlib.resources.files('openubem.data').iterdir()` lists `__init__.py`. `tests/fixtures/` confirmed present with `.gitkeep` from Step 1.
- **Notes:** None.

#### T02 — Bundle openstudio_archetypes.json (30 entries) — completed 2026-05-06

- **Artifacts:** `openubem/data/openstudio_archetypes.json` — sha256=`ace012a991c5f24af148ac3a382509716ba3819ede2459dab2f5e8139502ac58`
- **Deviations:** none; entries 1–29 follow DESIGN §3B body lines 116–147; entry 30 (`OpenUBEMUnknown`) per DESIGN §11 line 464. `SmallDataCenterLowITE` (#23) and `LargeDataCenterLowITE` (#25) flagged `phase_1_unreachable: true` per §11 line 481. `_Detailed` variants (#2, #4, #6) flagged `phase_1_unreachable: false` (reachable via `detailed_office=True`).
- **Test status:** `len(data['archetypes']) == 30` ✓; `unique_ids == 30` ✓; `OpenUBEMUnknown present` ✓; `phase_1_unreachable == ['SmallDataCenterLowITE', 'LargeDataCenterLowITE']` ✓
- **Notes:** `schema_version: "1.0.0"` set. `MediumOffice.default_size_signature` has stale `FALLBACK_DEFAULT` reference removed (retired per §11 line 487).

#### T03 — Bundle osm_to_use_class.json (55-token mapping) — completed 2026-05-06

- **Artifacts:** `openubem/data/osm_to_use_class.json` — sha256=`c10c53f6d4eede01e552937d7d375dc584b6a349a0648af0b1285d5a406a8530`
- **Deviations:** none; all 55 tokens taken verbatim from DESIGN §3A lines 99–104; all values ∈ `{"residential","commercial","industrial","institutional"}` (mixed and unknown are emergent, not in tag_to_use_class); `ambiguous_tokens: ["yes",""]` per §3A line 104.
- **Test status:** `all values valid: True` ✓; spot-checks apartments→residential, restaurant→commercial, school→institutional, data_center→industrial, warehouse→industrial all OK ✓
- **Notes:** `doctors` and `dentist` are NOT in the table (not listed in DESIGN §3A lines 99–104); rule 5b catches them directly by tag before use_class routing — correct per DESIGN §3C rule ordering.

#### T04 — _normalise_use_class (Stage 3A) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py` (created, contains T04–T12 implementation)
- **Deviations:** none; returns `tuple[str, float]` per plan fact #6 (use_class, dominant_tag_score). Phase-1 score formula: 1.0 for agree/single-tag, 0.5 for two-tag disagree, 0.0 for no resolution. `building_tag="yes"` explicitly excluded from uc_bt lookup (ambiguous_token per §3A line 104).
- **Test status:** covered by `TestNormaliseUseClass` — 10 fixtures, all pass (41 passed, 0 errors in CP2 run)
- **Notes:** Module also contains T05–T12 implementations (written together to avoid circular prerequisites).

#### T05 — _impute_levels (Stage 3D helper) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py`
- **Deviations:** none; verbatim from DESIGN §3D lines 248–253. Invariant: does NOT write to `provenance_levels` (verified by `test_provenance_levels_invariant`).
- **Test status:** `TestImputeLevels` — 6 fixtures (5 spec + 1 invariant), all pass.
- **Notes:** None.

#### T06 — _apply_rule_table (Stage 3C, 17 rules) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py`
- **Deviations:** Return type extended to `tuple[str, str, str | None]` (plan specifies `tuple[str, str]`). Third element (`inherited_rule_token`) is non-None only for rule 15; required for rule-15 confidence inheritance per DESIGN §11 line 466 — cannot satisfy the spec with only 2 elements. Noted here as a grounded deviation.
  Rule 6b: composite token `"RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED"` emitted as the second element per §11 line 465 + plan fact #29.
  Rules 1a/1b data-center exemption: achieved naturally — `data_center → industrial` in use_class mapping; "industrial" is not in `{"commercial","institutional","mixed","unknown"}`, so rules 1a/1b skip without explicit tag-checking in the rule condition.
- **Test status:** `TestApplyRuleTable` — 14 fixtures (all pass), covering rules 1a/1b, 2b, 4b, 6b composite, 6c, 9a, 12b, 15, 16, 17, plus all 3 exemption fixtures.
- **Notes:** None.

#### T07 — _assign_confidence (Stage 3D, 3-tier) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py`
- **Deviations:** none; Pass-2 §11 line 466 deltas applied: rule 15 inherits tier (no silent inflation), rule 16 → MEDIUM, rule 17 → LOW.
- **Test status:** `TestAssignConfidence` — 9 fixtures, all pass.
- **Notes:** `head_token = rule_token.split(",")[0]` strips the ASSUMPTION_* suffix from composite rule-6b token before confidence routing.

#### T08 — _apply_detailed_office (Stage 3E) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py`
- **Deviations:** none; Pass-2 §11 line 467. Appends `,DETAILED_OFFICE` to archetype_source; confidence preserved (not touched).
- **Test status:** `TestApplyDetailedOffice` — 5 fixtures, all pass.
- **Notes:** None.

#### T09 — _apply_overrides (Stage 3F) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py`
- **Deviations:** none; Pass-2 §11 lines 468, 482. REPLACES archetype_source with `f"OVERRIDE_USER({note})"` (not appended). LowITE bypass confirmed working via `test_lowite_override_reachable`.
- **Test status:** `TestApplyOverrides` — 6 fixtures, all pass (tmp_path replaced with tempfile.mkdtemp per Step 1 T11 Windows-permission pattern).
- **Notes:** None.

#### T10 — BuildingClassifier class + classify_building per-row helper + orchestrator — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py`; `tests/test_building_classifier.py` (all test classes for T04–T12 written together)
- **Deviations:** Schema validators (`_validate_input_schema`, `_validate_output_schema`) implemented as part of T10 rather than waiting for T11 — they are direct prerequisites of the orchestrator's `classify()` method, and CP2 runs orchestrator tests. Will confirm as T11 complete when formally audited.
  `archetype_source` token assembly per plan §4 fact #25: rule-token → HEURISTIC_* (if levels consumed) → ASSUMPTION_* (already embedded in rule 6b's composite token). For rule 15, HEURISTIC_* is appended when the inherited rule was levels-consuming and levels were imputed.
  `all_fallback_archetype` warning payload uses `"OpenUBEMUnknown"` (not `"MediumOffice"`) per Pass-2 §11 line 488.
- **Test status:** `TestClassifyBuildingRow` (7) + `TestBuildingClassifier` (9) = 16 tests, all pass. Full CP2 suite: **41 passed in 1.46s**.
- **Notes:** None.

#### T11 — Schema validators (_validate_input_schema, _validate_output_schema) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py` (lines 400–447; implemented as part of T10)
- **Deviations:** Code was written ahead-of-schedule during T10 because it is a direct prerequisite of `BuildingClassifier.classify()`. Formally logged here per plan T11 requirements.
- **Test status:** `TestSchemaValidation` — 9 fixtures, all pass. Row-level guarantee #6 (`OpenUBEMUnknown` row with HIGH+no-FALLBACK_UNKNOWN raises `SchemaError`) verified explicitly.
- **Notes:** `_validate_output_schema` reads `_VALID_30` from the module-level cache (no re-parse of JSON at call time). Token validation regex `^OVERRIDE_USER\(.*\)$` compiled at module level.

#### T12 — Serialisation helper (gpkg + log + schema.json + distribution CSV) — completed 2026-05-06

- **Artifacts:** `openubem/semantic/building_classifier.py` — `_serialize`, `_write_schema_json`, `_write_distribution_csv` methods on `BuildingClassifier` (lines 579–629; implemented as part of T10)
- **Deviations:** Implemented during T10 alongside the orchestrator (the `classify` method calls `self._serialize`). Formally logged here per plan T12.
- **Test status:** `TestSerialize` — 4 fixtures, all pass: 4 files created, GPKG round-trips to 26 columns, schema.json has 26 entries with required keys, distribution CSV has ≥1 row.
- **Notes:** Scoped `FileHandler` pattern mirrors Step 1 `_serialize`; handler added in `try` and removed in `finally`. `output_dir=None` (default) skips all writes; GDF always returned in-process regardless.

#### T13 — Synthetic 30-archetype coverage fixture builder — completed 2026-05-06

- **Artifacts:** `tests/fixtures/synthetic_30_archetype_coverage.gpkg` (25-row GeoPackage, layer `synthetic`); `synthetic_30_gdf` session fixture added to `tests/test_building_classifier.py`
- **Deviations:** Plan T13 and plan §4 fact #30 state "27 rows" but the parenthetical formula is "(30 total − 2 LowITE PHASE_1_UNREACHABLE − 3 `_Detailed` reachable only via `detailed_office=True`)". 30 − 2 − 3 = **25**, not 27. Implemented 25 rows (matching the formula). The "27" is an arithmetic error in the plan text; logged here for manager review. LowITE rows confirmed absent from default-mode output and reachable via override CSV (see T14 `TestArchetypeCoverage30::test_lowite_reachable_via_override`). `_Detailed` rows confirmed absent from default-mode output and reachable via `detailed_office=True` (see `test_detailed_reachable_via_flag`).
- **Test status:** `TestArchetypeCoverage30` — 3 fixtures, all pass (see T14).
- **Notes:** Fixture is rebuilt in-memory each session (session scope = once per `pytest` run); written to disk on each run as an audit artifact. Cache-and-skip with dtype-safe GPKG re-read was omitted in favour of always-rebuild for simplicity; session scope already ensures single build per run.

#### T14 — Test suite (tests/test_building_classifier.py) — completed 2026-05-06

- **Artifacts:** `tests/test_building_classifier.py` — `TestArchetypeCoverage30` class (3 methods replacing the placeholder); `synthetic_30_gdf` session fixture
- **Deviations:** `TestArchetypeCoverage30` was a placeholder in the T10 pre-write; replaced with 3 real test methods in this task. All other test classes (T04–T12) were written during T10 and are unchanged.
- **Test status:** Full suite `py -m pytest tests/ -v` → **139 passed, 2 skipped in 1.96s**. Step 1 baseline (46 tests) unchanged. Step 2 total: 93 passing + 1 intentional skip (`TestLabelledTop1Accuracy`, OQ-7). Step 1 skip: `TestRetryPolicy` (live-network gate, unchanged from Step 1).
- **Notes:** `_EXPECTED_DEFAULT` frozenset (25 elements) embedded in `TestArchetypeCoverage30` as the ground-truth vocabulary for default-mode coverage assertion.

#### T15 — pyproject.toml package-data + module docstring + version — completed 2026-05-06

- **Artifacts:** `pyproject.toml` (added `[tool.setuptools.packages.find]` and `[tool.setuptools.package-data]` sections); `openubem/semantic/building_classifier.py` (docstring updated to add §4 reference)
- **Deviations:** Version stays at `0.1.0` per plan T15 note ("version of `openubem` package can stay at the Step 1 value — manager bumps separately when releasing").
- **Test status:** `py -m pytest tests/ -v` → **139 passed, 2 skipped** (all green after pyproject + docstring edits); `py -c "import openubem.data, openubem.semantic"` → ok.
- **Notes:** `[tool.setuptools.packages.find]` added with `where = ["."]` so setuptools auto-discovers `openubem`, `openubem.acquisition`, `openubem.semantic`, and `openubem.data` (all have `__init__.py`). `"openubem.data" = ["*.json"]` ensures the two JSON files ship inside the wheel. Wheel build smoke test (`py -m build --wheel`) skipped — `build` package not confirmed installed; manager may verify separately.
