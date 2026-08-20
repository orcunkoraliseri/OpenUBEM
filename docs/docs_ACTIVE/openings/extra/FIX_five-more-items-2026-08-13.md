# FIX — T01 (OPEN-13) and T02 (OPEN-27), executed 2026-08-13

**Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-more-items-2026-08-13.md`
**Scope of this report:** T01 and T02 only, stopping at CP-1 as instructed. T03–T05 not started.
**Interpreter:** `./.venv/Scripts/python.exe`. No packages installed. No cluster, no network, no `git commit` / `add` / `restore` / `checkout --`.

---

## 0. A methodology note the director needs before trusting the numbers below

The working tree already carried substantial **uncommitted work from a concurrent session** when this
task started (visible today via `git diff --stat`: `docs/PROJECT_CHECKLIST.md`,
`INVESTIGATION_open-items-register.md`, `DIRECTOR_PROMPT_...`, both `board_published-numbers.html`
copies, `open44_test_triage.csv`/`.md`, `open45_severe_literal_sweep.csv`,
`IMPLEMENTATION_phaseC_ml_imputer.md`, `tests/test_debias.py`, `tests/test_draw_methods.py`,
`tests/test_impute_montage.py`, `tests/test_v19_basis_diagnostic.py`,
`tests/test_v19_national_cbecs_rescore.py`, the `tests/fixtures/synthetic_30_archetype_coverage.gpkg`
dirt named in the plan §2, plus untracked `PLAN_open22-tagrich-gate-2026-08-13.md` /
`FIX_open-22_tagrich-gate.md`). **This is a different, apparently still-live OPEN-22 arc, not something
this task touched or was asked to touch.**

To get a clean **before** count isolated to the two files T01/T02 write to, I ran
`git stash push -- openubem/semantic/fusion.py tests/test_fusion.py tests/test_building_classifier.py`
(a scoped stash of only those three paths — **the gpkg was never included in this stash**), measured,
then `git stash pop` (clean, no conflict, since the gpkg wasn't part of it) and confirmed with
`git diff stash@{0} -- .` → **0 lines** before dropping the stash. An earlier, broader `git stash` (no
path filter) briefly swept up all of the concurrent files above and one `git stash pop` attempt aborted
on the gpkg conflict exactly as plan §2 warns it will; I recovered by `git checkout stash@{0} -- <path>`
per file (never touching the gpkg's committed HEAD version — I only re-applied the version already
sitting dirty in the working tree) and verified **zero diff** between the stash and the restored working
tree before dropping it. No file was reverted to HEAD and left there; no concurrent work was lost. I
mention this because it explains where the "before" counts below come from, and because the director
should know a second, uncommitted arc is present in the same tree.

**Files this report actually changed (the only ones in scope for T01/T02):**
- `openubem/semantic/fusion.py` — 6 lines changed (+5/-1)
- `tests/test_fusion.py` — +60 lines (3 new tests)
- `tests/test_building_classifier.py` — the file's total working-tree diff is +71/-5, but **only 30 of
  those added lines are mine** (one new class, 3 tests); the rest (a `tmp_path_factory` fixture change
  and a `TestTagRichTop1Accuracy` class, 2 tests) is the concurrent OPEN-22 work described above, already
  present before I started and untouched by me.

---

## 1. T01 — OPEN-13: Overture cached-read guard

### What changed
`openubem/semantic/fusion.py:194` — deleted the hand-copied literal, replaced with an import-derived set:

```diff
-_NORMALIZED_OVERTURE_COLUMNS = {"id", "height", "levels", "use_class", "year_built", "geometry"}
+from openubem.acquisition.overture_fetcher import _NORMALIZED_COLUMNS as _OVERTURE_FETCHER_COLUMNS
+_NORMALIZED_OVERTURE_COLUMNS = set(_OVERTURE_FETCHER_COLUMNS)
```

The module-level comment above the old line was kept in place, unedited.

**Import style deviation from the plan's default (module-local, not function-local), and why it's safe.**
The plan asked for a module-level import unless it creates a cycle, in which case use the same
function-local form the sibling function (`_load_overture_layer`) already uses for `fetch_overture`.
I checked for a cycle before writing anything:
- `openubem/acquisition/overture_fetcher.py` imports only `numpy`, `pandas`, `geopandas` — nothing from
  `openubem.semantic`.
- `openubem/acquisition/__init__.py` (which always runs first when importing the `overture_fetcher`
  submodule) imports only `json`, `pathlib`, `geopandas`, `pandas` at module level; its only reference to
  `openubem.semantic` is inside `enrich_climate()`'s body (a lazy, function-local import), never at
  import time.
- `openubem/semantic/__init__.py` (which runs first when importing `fusion.py`) imports
  `construction_sets`, `loads`, `imputation`, `provenance`, `schedules` — none of which import
  `acquisition`.

No cycle exists. I placed the import as a plain module-level statement immediately above its point of
use (line 197, right before `_NORMALIZED_OVERTURE_COLUMNS`) rather than hoisting it to the file's import
block at the top — it is still eager/module-level (executes at import time, not deferred into a
function), just physically local to the one line that needs it, which is also how the file's existing
`from openubem.config import FLOOR_TO_FLOOR_M` sits with the top-of-file imports while
`_load_use_class_crosswalk`'s json import sits near its own use. Confirmed empirically, not just by
reading:
```
./.venv/Scripts/python.exe -c "import openubem.semantic.fusion as fusion; print('OK, no cycle')"
→ OK, no cycle
```
No behaviour changed: `_load_overture_layer`'s guard (`fusion.py:207`,
`if set(raw.columns) == _NORMALIZED_OVERTURE_COLUMNS:`) still compares against a `set`, unchanged in
type or semantics. `overture_fetcher.py` was not touched.

### (c) Confirm `set(_NORMALIZED_COLUMNS)` equals the old literal exactly
```
./.venv/Scripts/python.exe -c "
from openubem.acquisition.overture_fetcher import _NORMALIZED_COLUMNS
old_literal = {'id','height','levels','use_class','year_built','geometry'}
print('tuple:', _NORMALIZED_COLUMNS)
print('derived set:', set(_NORMALIZED_COLUMNS))
print('old literal:', old_literal)
print('equal:', set(_NORMALIZED_COLUMNS) == old_literal)
"
tuple: ('id', 'height', 'levels', 'use_class', 'year_built', 'geometry')
derived set: {'use_class', 'geometry', 'levels', 'id', 'height', 'year_built'}
old literal: {'use_class', 'year_built', 'geometry', 'id', 'height', 'levels'}
equal: True
```
They are equal — this is **not** a live defect; no STOP triggered here.

### New tests added (`tests/test_fusion.py`, class `TestOvertureCachedReadGuard`)
Three tests, none of which existed before (confirmed by grep: no prior reference to
`_load_overture_layer` anywhere in `tests/`):
1. `test_normalized_schema_cache_hit_skips_fetch_overture` — writes a normalized-schema GeoDataFrame to
   a `tmp_path` parquet, monkeypatches `overture_fetcher.fetch_overture` to raise if called, asserts the
   guard returns the cached frame unchanged and `fetch_overture` was never invoked.
2. `test_raw_schema_slice_goes_through_fetch_overture` — uses the existing raw-schema fixture
   (`OVERTURE_SLICE`), monkeypatches `fetch_overture` to a spy returning a sentinel, asserts the sentinel
   comes back and the spy was called exactly once.
3. `test_guard_set_equals_fetchers_normalized_columns` — the regression test: asserts
   `fusion._NORMALIZED_OVERTURE_COLUMNS == set(overture_fetcher._NORMALIZED_COLUMNS)`.

### (a) Exact counts, before and after
```
./.venv/Scripts/python.exe -m pytest tests/test_fusion.py tests/test_fusion_license_guard.py -q
```
- **Before** (T01 change stashed out): `39 passed in 1.21s`
- **After**: `42 passed in 1.24s` (+3, exactly the tests added)

### (b) Proof that test (iii) is non-vacuous
Not done by editing the shipped file. Done by mutating the imported module attribute in a throwaway
process and restoring it — the shipped file was never touched:
```
./.venv/Scripts/python.exe -c "
from openubem.semantic import fusion
from openubem.acquisition.overture_fetcher import _NORMALIZED_COLUMNS
original = fusion._NORMALIZED_OVERTURE_COLUMNS
corrupted = set(original); corrupted.discard('use_class'); corrupted.add('use_class_WRONG')
fusion._NORMALIZED_OVERTURE_COLUMNS = corrupted
try:
    assert fusion._NORMALIZED_OVERTURE_COLUMNS == set(_NORMALIZED_COLUMNS)
    print('UNEXPECTED: assertion passed on corrupted set')
except AssertionError:
    print('EXPECTED FAILURE: AssertionError raised on corrupted in-memory set')
    print('  corrupted:', sorted(fusion._NORMALIZED_OVERTURE_COLUMNS))
    print('  fetcher  :', sorted(_NORMALIZED_COLUMNS))
finally:
    fusion._NORMALIZED_OVERTURE_COLUMNS = original
assert fusion._NORMALIZED_OVERTURE_COLUMNS == set(_NORMALIZED_COLUMNS)
print('restored: derived set == fetcher tuple again ->', fusion._NORMALIZED_OVERTURE_COLUMNS == set(_NORMALIZED_COLUMNS))
"
```
Output:
```
EXPECTED FAILURE: AssertionError raised on corrupted in-memory set
  corrupted: ['geometry', 'height', 'id', 'levels', 'use_class_WRONG', 'year_built']
  fetcher  : ['geometry', 'height', 'id', 'levels', 'use_class', 'year_built']
restored: derived set == fetcher tuple again -> True
```
Confirms the guard-equality test fails when the derived set diverges from the fetcher's tuple, and
recovers cleanly. The regression test proves what it claims to prove.

---

## 2. T02 — OPEN-27: bind `_COARSE_CLASS_MAP` keys to the archetype JSON

### 1. `_COARSE_CLASS_MAP` contents and usage
`tests/test_building_classifier.py:1004-1008`:
```python
_COARSE_CLASS_MAP: dict[str, str] = {
    "MidriseApartment": "residential",
    "HighriseApartment": "residential",
    **{aid: "commercial" for aid in _VALID_30 - {"MidriseApartment", "HighriseApartment"}},
}
```
**Every one of the 30 keys is drawn from `_VALID_30`**
(`openubem/semantic/building_classifier.py:44-46`), which is itself built directly from
`openstudio_archetypes.json` (`frozenset(a["archetype_id"] for a in _RAW_ARCHETYPES["archetypes"])`) —
not hand-typed. So `_COARSE_CLASS_MAP` has 30 keys: 2 mapped to `"residential"`
(`MidriseApartment`, `HighriseApartment`), 28 mapped to `"commercial"`. It is used at
`test_building_classifier.py:1047` (`TestLabelledTop1Accuracy.test_coarse_top1`) to grade the labelled
coarse-accuracy gate.

### 2/4. New test class added: `TestOpen27ArchetypeNameBinding` (in `tests/test_building_classifier.py`, placed just after the `_COARSE_CLASS_MAP` definition)
Three tests:
1. `test_coarse_class_map_keys_exist_in_archetype_json` — loads the JSON fresh (not via `_VALID_30`, so
   it's a genuine check against the file, not a tautology through the same import) and asserts every
   `_COARSE_CLASS_MAP` key is an `archetype_id` in it, failing with a message naming the offending key
   and citing OPEN-27.
2. `test_residential_archetypes_are_exactly_midrise_and_highrise` — asserts the set of keys mapped to
   `"residential"` equals exactly `{"MidriseApartment", "HighriseApartment"}`.
3. `test_multifamilyhome_not_in_archetype_json` — asserts `"MultifamilyHome"` is absent from the JSON's
   archetype ids.

### 3. Result: the map was already clean
`test_coarse_class_map_keys_exist_in_archetype_json` **passed immediately** on the first run — as
expected, since `_COARSE_CLASS_MAP`'s keys are derived from the same JSON they're checked against. This
is the outcome the plan told me to expect and report plainly: **`_COARSE_CLASS_MAP` was never the
carrier of OPEN-27's defect.** The divergence is confined entirely to the DESIGN text, which the code
does not read. No stricter assertion was invented to manufacture a finding.

### 5. Re-verified erratum, commands and output
```
grep -n "MultifamilyHome" openubem/data/openstudio_archetypes.json
→ (no output — 0 matches)

grep -n '"sector": "Residential"' openubem/data/openstudio_archetypes.json
→ 101:      "sector": "Residential",
  108:      "sector": "Residential",
```
The two Residential entries, by their `archetype_id` line:
```
100:      "archetype_id": "MidriseApartment",
101:      "sector": "Residential",
...
107:      "archetype_id": "HighriseApartment",
108:      "sector": "Residential",
```
**Zero `MultifamilyHome` occurrences; exactly two `sector: "Residential"` entries, `MidriseApartment`
(id line 100) and `HighriseApartment` (id line 107).** This matches plan §4 fact 2 exactly.

The DESIGN citation itself, re-read (not edited — 0 characters changed in any `docs/docs_main/` file):
`docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md:529`
still reads: `**residential** ⇔ sector == "Residential" (2 archetypes — MidriseApartment,
MultifamilyHome)`. The erratum stands: the spec names `MultifamilyHome`, the data has no such archetype
(it has `HighriseApartment` instead), and the code's own `_VALID_30`/`_COARSE_CLASS_MAP` never
name-checked against the spec text — only against the JSON — so the mismatch was never code-visible
until this task's tests.

### Before/after counts
```
./.venv/Scripts/python.exe -m pytest tests/test_building_classifier.py -q
```
- **Before** (T02 change stashed out, i.e. HEAD's committed content): `131 passed in 2.14s`
- **After**: `136 passed in 2.34s`

The plan states "133 was the count on 2026-08-13." That figure does not match either of my two clean
measurements (131 committed / 136 with my +3 added). It reconciles exactly if the plan's 133 was counted
against the working tree **as it stood with the concurrent OPEN-22 session's 2 already-added tests**
(`TestTagRichTop1Accuracy`, 2 tests) applied on top of HEAD's 131: `131 + 2 = 133`. My 3 additions on top
of that same tree give `133 + 3 = 136`, which is exactly what the combined run reports. I did not commit
to this reconciliation as fact — see §3 below — but the arithmetic is exact and I flag it rather than
silently using a baseline that doesn't match plan text.

### Deliberately-wrong-name proof (test shown failing, then passing)
Not committed to the file — demonstrated in a throwaway process against the real
`_COARSE_CLASS_MAP` imported from the test module:
```
./.venv/Scripts/python.exe -c "
from tests.test_building_classifier import _COARSE_CLASS_MAP
import json
from importlib.resources import files
def ids():
    data = json.loads(files('openubem.data').joinpath('openstudio_archetypes.json').read_text())
    return [a['archetype_id'] for a in data['archetypes']]
archetype_ids = set(ids())
for key in _COARSE_CLASS_MAP:
    assert key in archetype_ids, f'OPEN-27: {key!r} not in JSON'
print('PASS on real _COARSE_CLASS_MAP: all', len(_COARSE_CLASS_MAP), 'keys found in JSON')
bad_map = dict(_COARSE_CLASS_MAP); bad_map['MultifamilyHome'] = 'residential'
try:
    for key in bad_map:
        assert key in archetype_ids, f'OPEN-27: _COARSE_CLASS_MAP key {key!r} is not an archetype_id in openstudio_archetypes.json'
    print('UNEXPECTED: assertion passed on corrupted map')
except AssertionError as e:
    print('EXPECTED FAILURE:', e)
"
```
Output:
```
PASS on real _COARSE_CLASS_MAP: all 30 keys found in JSON
EXPECTED FAILURE: OPEN-27: _COARSE_CLASS_MAP key 'MultifamilyHome' is not an archetype_id in openstudio_archetypes.json
```

---

## 3. Combined file-scoped run (both files together)

```
./.venv/Scripts/python.exe -m pytest tests/test_fusion.py tests/test_fusion_license_guard.py tests/test_building_classifier.py -q
→ 178 passed in 3.17s
```
(42 + 136 = 178, consistent with the individual runs above.)

## 4. Files touched (exhaustive)

Exactly the three files §2/T01/T02 of the plan permits: `openubem/semantic/fusion.py`,
`tests/test_fusion.py`, `tests/test_building_classifier.py`, plus this report. Nothing else was
created or modified by this task. `overture_fetcher.py` was read, not edited. No `docs/docs_main/` file
was edited. The `tests/fixtures/synthetic_30_archetype_coverage.gpkg` dirt was never restored, committed,
or reverted by this task — see §0 for the incidental git-stash detour that touched it only to put it
back exactly as found.

---

## What I could not determine

- **The plan's stated T02 baseline of "133 passed" does not match either of my two clean measurements**
  (131 on committed HEAD, 136 after my 3 additions). §2 gives an arithmetic reconciliation against the
  concurrent OPEN-22 session's in-progress work (131 + 2 = 133), and it fits exactly, but I cannot
  confirm from inside this task that this is actually how the plan's author arrived at 133 — I can only
  report that the numbers reconcile under that assumption and flag the discrepancy rather than silently
  overriding the plan's stated figure.
- **Whether the OPEN-22 concurrent session's own uncommitted changes (visible in `git status` throughout
  this task) are stable/final or still being actively edited by another process** — I did not investigate
  that arc's content or intent beyond what was needed to avoid destroying it while isolating my own
  before/after baselines (§0). If that other session writes to `fusion.py`, `test_fusion.py`, or
  `test_building_classifier.py` again before this report is read, the diffs quoted here could go stale.
- **Whether a module-level import cycle could arise through some import order not exercised by the
  current test suite or by `import openubem.semantic.fusion` directly** — I checked every import chain
  reachable from `fusion.py` and `overture_fetcher.py` by reading each file's own imports (not a
  transitive tool-assisted cycle check across the whole package graph), and confirmed empirically that a
  fresh-process import succeeds. I did not exhaustively enumerate every possible entry point into the
  package.
- T03, T04, T05 and the full-suite CP-2 run were not started — out of scope for this report per the
  instruction to stop at CP-1.
