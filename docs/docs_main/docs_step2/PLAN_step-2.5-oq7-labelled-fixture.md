# PLAN — Step 2.5 — OQ-7 Closure (Labelled-Accuracy Fixture)

> **Slug:** `plan-step-2.5-oq7-labelled-fixture`
> **Authored:** 2026-05-06 (manager)
> **Binding contract:** `docs\docs_step2\DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md`
> **Triggering revision:** DESIGN §11 entry "Direct edit: 2026-05-06 (OQ-7 closure — user-authorized, no `/design` pass)" — read this entry verbatim before any task. It seals the OQ-7 (a)/(b)/(c)/(d) resolutions and the residential-vs-commercial coarse-class mapping.
> **Companion summary:** `docs\docs_step2\OVERVIEW_step-2-...md` (no surface change vs. CP3 baseline).
> **Working directory (absolute, do not leave):** `C:\Users\o_iseri\Desktop\OpenUBEM`
> **Predecessor:** `docs\docs_step2\PLAN_step-2-implementation.md` — CP3 already greenlit; do not reopen its progress log.

This is the manager-authored plan. A fresh Sonnet session executes against it. Sonnet does not propose its own plan — it executes this one and reports.

---

## §1 Hard rules for the executor

1. Stay at the working directory above. Do not `cd` elsewhere.
2. **Manager owns plans.** If you (Sonnet) think the plan is wrong, STOP and quote the conflict — do not author your own plan.
3. **Stop-and-ask on spec ambiguity.** If DESIGN §11's OQ-7 closure or the new coarse-class mapping is ambiguous, STOP and quote the conflict. Never invent.
4. **No scope creep beyond L0, L1, L2, L3.** Do not refactor `building_classifier.py`. Do not change the 26-col output schema, the 30-archetype vocabulary, or the rule table. Do not bump `pyproject.toml`.
5. **Touch only these files:**
   - new: `tests\fixtures\build_osm_fixtures.py`
   - new: `tests\fixtures\build_labelled_template.py`
   - new: `tests\fixtures\README.md`
   - edit: `tests\test_building_classifier.py` — replace lines 854–861 (`TestLabelledTop1Accuracy` stub) and add a module-level `_COARSE_CLASS_MAP` constant near the existing module imports.
   - **DO NOT** edit OVERVIEW, DESIGN, prior PLAN, `openubem/...`, `pyproject.toml`, or `main.py`.
6. **Live-network ban.** L0 is a script Sonnet *writes*; the **user runs it**, not Sonnet. Do not invoke `ingest_buildings(location=..., bbox=...)` from any pytest/CI path. The `__main__` guard in L0 enforces this.
7. **Default to no comments.** One short line max where the WHY is non-obvious. No multi-paragraph docstrings.
8. **Update §8 progress log after each completed task.** One entry per task. Format pinned in §8.

---

## §2 File layout

```
C:\Users\o_iseri\Desktop\OpenUBEM\
└── tests\
    ├── fixtures\
    │   ├── .gitkeep                              ← already exists, do not touch
    │   ├── synthetic_30_archetype_coverage.gpkg  ← already exists, do not touch
    │   ├── build_osm_fixtures.py                 ← L0 (Sonnet writes)
    │   ├── build_labelled_template.py            ← L1 (Sonnet writes)
    │   ├── README.md                             ← L3 (Sonnet writes)
    │   ├── boston_downtown_500m.gpkg             ← USER produces by running L0
    │   ├── chicago_loop_500m.gpkg                ← USER produces by running L0
    │   └── labelled_archetypes_50.csv            ← USER hand-labels (post-L1)
    └── test_building_classifier.py               ← L2 (Sonnet edits lines 854–861 + adds _COARSE_CLASS_MAP)
```

No other files may be created, moved, deleted, or edited.

---

## §3 Dependency decisions

No new runtime or test dependencies. Existing pins stand:

- `osmnx >= 1.9, < 2.0` (already pinned via Step 1)
- `geopandas`, `pandas`, `pytest`, `pyogrio`, `shapely` — all already in `pyproject.toml`

L0 imports only `openubem.acquisition.osm_fetcher.ingest_buildings` plus stdlib. L1/L2/L3 import only stdlib + `openubem.semantic.building_classifier.BuildingClassifier` + `geopandas` + `pandas`.

---

## §5 Source-of-truth verified facts

The manager has independently verified these against current files and the 2026-05-06 OQ-7 closure entry. Do not re-derive — trust and cite.

**5.1 OQ-7 (a) — labeller is single expert.** DESIGN §11 entry "Direct edit: 2026-05-06 (OQ-7 closure ...)" — sub-question (a) RESOLVED. Single labeller; CSV header records `# labeller=orcunkoral.oseri@concordia.ca` for provenance.

**5.2 OQ-7 (b) — source mix is Boston-30 + Chicago-20.** DESIGN §5.2 + §11 entry sub-question (b). Phoenix excluded. L1 sampler must enforce exactly 30 + 20 = 50 rows.

**5.3 OQ-7 (c) — fine-accuracy threshold and coverage requirement.** DESIGN §5.1 row `Labelled top-1 accuracy`: ≥ 70% fine on labelled rows; warn 60–70%; fail < 60%. **NEW** §11 closure adds: ≥ 10 distinct archetypes must appear in `expected_archetype` over the 50 rows. Fine accuracy is measured *over labelled rows only* — zero-ground-truth archetypes do not contribute.

**5.4 OQ-7 (d) — out of scope.** Logged as `OQ-7-FOLLOWUP` in DESIGN §7. Do not implement two-expert agreement, do not pre-allocate 200×4 city storage.

**5.5 Coarse-class mapping (load-bearing, sealed in §11 entry):**
- residential ⇔ archetype's `sector == "Residential"` per `openubem/data/openstudio_archetypes.json` → exactly **2 archetypes**: `MidriseApartment`, `HighriseApartment`.
- commercial ⇔ everything else → **28 archetypes** (Office, Retail, Food Service, Lodging, Healthcare, Education, Government, Data Center, Research, Industrial, High-Rise, Fallback).
DESIGN §5.1 row `Labelled top-1 accuracy`: ≥ 90% coarse; warn 80–90%; fail < 80%.

**5.6 Public API for fixture materialization (L0).** `openubem.acquisition.osm_fetcher.ingest_buildings` at `openubem\acquisition\osm_fetcher.py:26`. Signature:
```python
def ingest_buildings(
    location: str | tuple[float, float] | None = None,
    radius_m: float = 1000.0,
    bbox: tuple[float, float, float, float] | None = None,
    osm_path: Path | None = None,
    tags: dict | None = None,
    retry_policy: "tenacity.Retrying | None" = None,
    output_dir: Path | None = None,
) -> gpd.GeoDataFrame:
```
L0 invokes mode (a) `ingest_buildings(location="Downtown Boston, MA", radius_m=500)` and `ingest_buildings(location="The Loop, Chicago, IL", radius_m=500)`. Returns a 23-col GeoDataFrame. `osm_id` is column #2 and is unique per row (post-MultiPolygon explosion).

**5.7 Public API for accuracy assertion (L2).** `openubem.semantic.building_classifier.BuildingClassifier` — same signature exercised by `TestBuildingClassifier` in the existing test file. `BuildingClassifier().classify(gdf)` returns the 26-col output GeoDataFrame; `archetype_id` is the column to compare against `expected_archetype`.

**5.8 Archetype JSON loader pattern (L2).** Reuse the proven pattern from `tests\test_building_classifier.py:82-83`:
```python
from importlib.resources import files
data = json.loads(files("openubem.data").joinpath("openstudio_archetypes.json").read_text())
```
The `archetypes` list under that key holds the 30 entries with `sector` field; iterate to build `_COARSE_CLASS_MAP: dict[str, str]`.

**5.9 Existing stub to replace.** `tests\test_building_classifier.py:854-861`:
```python
class TestLabelledTop1Accuracy:
    def test_skip_if_missing(self):
        fixture = Path("tests/fixtures/labelled_archetypes_50.csv")
        if not fixture.exists():
            pytest.skip("labelled fixture not yet committed (OQ-7)")
```
Replace this entire class with the L2 deliverable. Imports already present in the file (`BuildingClassifier`, `pandas`, `pytest`, `pathlib.Path`, `geopandas`) cover L2's needs; do not add new top-level imports unless strictly necessary.

**5.10 No `.osm` raw XML on disk.** The `boston_downtown_500m.osm` and `chicago_loop_500m.osm` referenced in DESIGN §5.2 were never committed. The canonical persisted form is `.gpkg` (cleaned 23-col GeoDataFrame). `osmnx` `features_from_address` returns a GeoDataFrame; raw `.osm` XML retention is deferred to Phase-2.

---

## §6 Task list

Four executor tasks (L0–L3), one mandatory user step in the middle.

### L0 — Write `tests/fixtures/build_osm_fixtures.py`

- **What:** A standalone script that materialises the two source fixtures by calling `ingest_buildings` for Downtown Boston and The Loop, Chicago, then saves each cleaned 23-col GeoDataFrame as a GeoPackage in `tests/fixtures/`. The script is **not** imported by any test; it has a `if __name__ == "__main__":` guard and is intended for the user to run once on their machine.
- **Why:** DESIGN §5.2 + §11 OQ-7 closure require Boston-30 + Chicago-20 sampling source. The `.osm` XML files referenced in §5.2 do not exist on disk; the canonical persisted form is `.gpkg`. Live-network ban (Hard Rule #6) prohibits Sonnet from running osmnx; the user runs the script once on their dev machine.
- **How:**
  - Header docstring: 1–2 lines pointing at this PLAN doc and the OQ-7 closure §11 entry.
  - Two configured city tuples, each `(slug, location, radius_m, output_filename)`:
    - `("boston_downtown_500m", "Downtown Boston, MA", 500.0, "boston_downtown_500m.gpkg")`
    - `("chicago_loop_500m", "The Loop, Chicago, IL", 500.0, "chicago_loop_500m.gpkg")`
  - Loop: for each city, call `gdf = ingest_buildings(location=loc, radius_m=r)`; assert `len(gdf) >= 100` (sanity check — if zero/few rows, fail fast); call `gdf.to_file(out_path, driver="GPKG", layer=slug)`; print one line per city: `wrote {slug}: {n} rows -> {path}`.
  - Out-path resolution: `Path(__file__).parent / output_filename`.
  - `if __name__ == "__main__":` guard wraps the loop. No top-level execution.
- **How to test:** No standalone unit test. The script's correctness is validated when the user runs it once and the two `.gpkg` files materialise. L1's `__main__` will fail-fast with a clear error if the `.gpkg` files are missing — that is the integration point.

### L1 — Write `tests/fixtures/build_labelled_template.py`

- **What:** A standalone script that reads the two `.gpkg` files produced by L0, samples 30 + 20 = 50 rows deterministically, and emits a CSV template for the user to hand-label.
- **Why:** OQ-7 (b) + (c) + (d) — Boston-30 + Chicago-20 fixed split, deterministic seed for reproducibility, columns sized to give the labeller all the OSM evidence they need without forcing them to open QGIS.
- **How:**
  - Reads `boston_downtown_500m.gpkg` (layer auto-detect or `layer="boston_downtown_500m"`); takes 30 rows via `df.sample(n=30, random_state=42)`.
  - Reads `chicago_loop_500m.gpkg`; takes 20 rows via `df.sample(n=20, random_state=42)`.
  - Each sampled row is projected to the 10-column CSV schema:
    - `osm_id` (string, copied verbatim — already unique per row per §5.6)
    - `source_fixture` (string literal: `"boston_downtown_500m"` or `"chicago_loop_500m"`)
    - `building_tag` (string)
    - `function_tag` (string)
    - `levels` (int or empty)
    - `height_m` (float or empty)
    - `footprint_area_m2` (float)
    - `expected_archetype` (empty — for user to fill)
    - `expected_coarse_class` (empty — for user to fill)
    - `notes` (empty — for user notes/Street View links/uncertainty markers)
  - Concatenate the two 30+20 frames → 50 rows. Sort by `(source_fixture, osm_id)` for stable diffs.
  - Write to `tests/fixtures/labelled_archetypes_50.template.csv` via `pd.to_csv(index=False)`. Output filename ends in `.template.csv` so the user knows to rename after labelling.
  - `__main__` guard. Fail-fast with a clear message if either `.gpkg` is missing (`raise FileNotFoundError(f"Run tests/fixtures/build_osm_fixtures.py first to materialise {gpkg_path}")`).
- **How to test:** Sonnet runs the script *only if* the user has already produced the `.gpkg` files. If the gpkg files don't yet exist when L1 runs, Sonnet authors L1 and stops at CP-α without invoking it. L1's correctness is later validated by the L2 schema check + the user reviewing the template.

### USER STEP — hand-label the 50 rows

> **This step is performed by the user, not Sonnet.** Sonnet stops at CP-α and waits.

The user:
1. Runs `py tests/fixtures/build_osm_fixtures.py` once. Two `.gpkg` files appear.
2. Runs `py tests/fixtures/build_labelled_template.py`. `labelled_archetypes_50.template.csv` appears.
3. Opens the template in Excel / a text editor / VS Code. For each row:
   - Decides the correct `expected_archetype` from the 30-element vocabulary in `openubem/data/openstudio_archetypes.json`. Uses Google Street View, OSM tags (already pre-filled), and personal domain knowledge.
   - Decides `expected_coarse_class` ∈ {residential, commercial}. Uses §5.5 mapping as a sanity check (every `expected_archetype` has a deterministic `expected_coarse_class` per the mapping; the column is denormalised redundancy for human readability and for spot-checking the mapping).
   - Optionally fills `notes` (Street View URL, "uncertain — could also be MediumOffice", etc.).
4. Validates: ≥ 10 distinct values in `expected_archetype` (per OQ-7 (c)). If fewer, the user is asked to revisit row choices or accept a smaller-than-50 fine-grained set with documented coverage gaps.
5. Adds a 1-line CSV header above the column row: `# labeller=orcunkoral.oseri@concordia.ca, snapshot_date=YYYY-MM-DD` (replace YYYY-MM-DD with the actual labelling date).
6. Saves as `tests/fixtures/labelled_archetypes_50.csv` (drop the `.template`). Commits.

User signals completion to the manager. Manager re-launches Sonnet at L2.

### L2 — Replace `TestLabelledTop1Accuracy` with three real test methods

- **What:** Replace the stub at `tests/test_building_classifier.py:854-861` with three asserting methods, plus a module-level `_COARSE_CLASS_MAP` constant.
- **Why:** Activates the §5.1 labelled-accuracy gate now that the fixture exists. Hard rules: (i) skip if file missing (graceful degradation per DESIGN §5.2); (ii) coarse mapping is sealed in §5.5 — Sonnet derives it programmatically from `sector` field, no string lists hard-coded.
- **How:**
  - Add at module top (near existing imports — line ~14 area):
    ```python
    _ARCHETYPES_RAW = json.loads(
        files("openubem.data").joinpath("openstudio_archetypes.json").read_text()
    )["archetypes"]
    _COARSE_CLASS_MAP: dict[str, str] = {
        a["archetype_id"]: ("residential" if a["sector"] == "Residential" else "commercial")
        for a in _ARCHETYPES_RAW
    }
    _ARCHETYPE_VOCAB: frozenset[str] = frozenset(a["archetype_id"] for a in _ARCHETYPES_RAW)
    _LABELLED_FIXTURE = Path("tests/fixtures/labelled_archetypes_50.csv")
    ```
    (Existing imports — `json`, `files`, `Path`, `BuildingClassifier`, `pandas`, `pytest` — must already be in scope; verify and only add what's strictly missing.)
  - Replace the entire `TestLabelledTop1Accuracy` class with:
    ```python
    class TestLabelledTop1Accuracy:
        @pytest.fixture(scope="class")
        def _labelled_run(self):
            if not _LABELLED_FIXTURE.exists():
                pytest.skip("labelled fixture not yet committed (OQ-7)")
            df = pd.read_csv(_LABELLED_FIXTURE, comment="#")
            assert set(df["expected_archetype"]) <= _ARCHETYPE_VOCAB
            assert set(df["expected_coarse_class"]) <= {"residential", "commercial"}
            # build a minimal GeoDataFrame from the OSM-tag columns and run the classifier
            ...
            out = BuildingClassifier().classify(gdf)
            return df, out

        def test_coarse_top1(self, _labelled_run): ...
        def test_fine_top1(self, _labelled_run): ...
        def test_archetype_coverage_min10(self, _labelled_run): ...
    ```
    Each test method asserts its threshold per §5.1 (coarse: ≥ 90% fail < 80%; fine: ≥ 70% fail < 60%; coverage: `len(set(df["expected_archetype"])) >= 10`).
  - **GeoDataFrame reconstruction inside the class fixture:** the labelled CSV does not carry geometry. To run the classifier, Sonnet must rebuild a synthetic 23-col GeoDataFrame from (i) the OSM-tag columns in the CSV (osm_id, building_tag, function_tag, levels, height_m, footprint_area_m2) and (ii) reasonable defaults for the other 17 cleaned-fetcher columns (zero-fill geometry, `provenance_*` set to "OSM_OBSERVED" where the column has a non-null value, otherwise "MISSING_DEFAULT"; `data_quality_flag` empty). This synthesis layer must not contaminate other tests — keep it inside the class. **If DESIGN §5.2 / §3D ambiguity arises here, STOP and quote.**
- **How to test:** `py -m pytest tests/test_building_classifier.py::TestLabelledTop1Accuracy -v`. Three methods, all pass when the user-committed CSV satisfies the thresholds. If the fixture is missing, all three skip identically. If thresholds are violated, the failure points at the labelled-CSV row(s) responsible.

### L3 — Add `tests/fixtures/README.md`

- **What:** A short README pointing at the L0/L1/USER pipeline.
- **Why:** Future contributors need a 30-second orientation: which scripts produce which files, where the labelled CSV lives, and how to regenerate. Lives next to the scripts so it is impossible to miss.
- **How:** ~25-line markdown file. Sections: "What's here", "How to (re)build the source fixtures (L0)", "How to (re)build the label template (L1)", "How to label", "How to verify". Cross-link this PLAN doc and the DESIGN §11 OQ-7 closure entry.
- **How to test:** Visual review only — no code path consumes it.

---

## §7 Stop-and-report checkpoints

Two checkpoints. Sonnet stops, appends progress log entries (§8), and reports before the manager dispatches the next range.

- **CP-α — after L1.** Sonnet has written `build_osm_fixtures.py` and `build_labelled_template.py`. Sonnet does **not** run them (live-network ban; user is the runner). Sonnet reports: file paths, schema diff vs. plan, any DESIGN ambiguity surfaced, full pytest summary (must still match the CP3 baseline of 139 passed / 2 skipped — no Step 2 regressions). Sonnet then **STOPS** until the user confirms hand-labelling is complete and `labelled_archetypes_50.csv` is committed.
- **CP-β — after L3.** Sonnet runs `py -m pytest tests/ -v` and reports the full summary (target: **142 passed, 1 skipped** — only `TestRetryPolicy` live-network gate remains). Reports the coarse + fine accuracy numbers obtained on the labelled CSV. Manager audits before greenlight.

If CP-β does not reach 142 passed: report failures verbatim, include the per-row mismatches (CSV `osm_id` + expected vs. actual `archetype_id`) in the report, and STOP — do not patch over a red bar.

---

## §8 Progress log

Empty template. Sonnet appends one entry per completed task in order L0, L1, L2, L3. Format identical to PLAN_step-2-implementation §7.

```
#### LXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + DESIGN/PLAN cite>
- Test status: <pytest summary or "covered by LYY">
- Notes: <auditor-relevant>
```

#### L0 — Write build_osm_fixtures.py — completed 2026-05-06
- Artifacts: `tests/fixtures/build_osm_fixtures.py`
- Deviations: none
- Test status: 139 passed / 2 skipped (CP3 baseline confirmed; this script has no CI path — user runs it manually)
- Notes: Script has `__main__` guard; two city tuples Boston + Chicago; asserts `len(gdf) >= 100` before writing `.gpkg`; out-path resolved via `Path(__file__).parent`

#### L1 — Write build_labelled_template.py — completed 2026-05-06
- Artifacts: `tests/fixtures/build_labelled_template.py`
- Deviations: none
- Test status: 139 passed / 2 skipped (CP3 baseline confirmed; script not invoked — `.gpkg` source files not yet on disk)
- Notes: Reads each `.gpkg` with the matching layer name (slug); `sample(n=30/20, random_state=42)`; 10-column output schema per PLAN §6 L1; sorts by `(source_fixture, osm_id)`; emits `.template.csv`; `FileNotFoundError` with clear message if either `.gpkg` is missing
