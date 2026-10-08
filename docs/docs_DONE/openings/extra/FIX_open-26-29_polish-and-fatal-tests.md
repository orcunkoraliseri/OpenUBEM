# FIX — OPEN-26 (survivor a: missing-EPW Site:Location) and OPEN-29 (fatal-test occurrence class) — T05+T06

> **Slug:** `open-26-29_polish-and-fatal-tests` · **Plan:** `PLAN_five-item-sweep-2026-08-12.md` T05+T06
> **Repo state read/written:** HEAD at start `25924ddec81dbc52d851ff67092cdd816243ffa0` (2026-08-12).
> **Kind:** T05 is a fix (survivor a) + two measurements (survivors b, c). T06 is a fix (three
> diagnostics scripts) + a measurement (whether past conclusions depended on the broken test).
> This report closes neither item — that is the director's call at CP-3.

---

## T05 — OPEN-26

### (a) Missing-EPW `Site:Location` — fixed

**Template's real default Site:Location, re-derived from the template files (not assumed):**
all four templates (`commercial_base.idf`, `residential_base.idf`, `highrise_base.idf`,
`specialized_base.idf`) carry the identical block at line 33-35:

```
Site:Location,
    PLACEHOLDER,             !- Name (overwritten from EPW header)
    0.0, 0.0, 0.0, 0.0;      !- Latitude, Longitude, Time Zone, Elevation
```

i.e. `Name="PLACEHOLDER"`, `Latitude=0.0`, `Longitude=0.0`, `Time_Zone=0.0`, `Elevation=0.0` — the
register's "(0,0)" shorthand for lat/lon is correct, but the full record also carries the literal name
`PLACEHOLDER` and zero time zone/elevation. Confirmed identical across all four templates by direct read.

**Before (demonstrated, not assumed) — `openubem/idf/builder.py:210-212` prior to this fix:**
constructed two rows, one with `epw_path=""` and one with `epw_path="C:/nope/does_not_exist.epw"`,
both through the real `BuildingIDF.__init__`:

```
case='missing (empty string)'   Name='PLACEHOLDER' Lat=0.0 Lon=0.0 TZ=0.0 Elev=0.0
case='nonexistent path'         Name='PLACEHOLDER' Lat=0.0 Lon=0.0 TZ=0.0 Elev=0.0
```

Confirmed: both cases silently continue at the template's placeholder location. No exception, no log,
no data-quality flag.

**Convention followed, and where it was found.** `openubem/idf/builder.py`'s own idiom is split in two
by call frame:
- Inside `BuildingIDF.build()`, per-building geometry/simulation problems are **never raised** — they are
  absorbed into a `data_quality_flag` string and/or a `generation_status` value in the returned manifest
  row (e.g. `builder.py:409-417`, `545-552`, `558-565`, `579-586`), because `build()`'s caller expects a
  dict back, not an exception, and a fleet loop must keep going building-by-building.
- `BuildingIDF.__init__`, by contrast, is **already allowed to raise** in the file's own idiom: both call
  sites that construct it wrap the constructor *and* the `.build()` call together in one
  `try/except Exception` — `_build_one` (`builder.py:644-658`, docstring: *"never raises"* at the
  `run_step3` level) and the `n_jobs == 1` serial loop (`builder.py:681-688`). Either path converts any
  exception into `_worker_exception_row(...)` (`builder.py:632-641`), which records
  `generation_status="failed_worker_exception"` and logs the traceback via `logger.error`. Raising in
  `__init__` is therefore **already the established way this file surfaces a fatal per-building input
  problem** — it does not bypass the fleet loop, it degrades exactly one building's manifest row, loudly,
  through infrastructure that already exists and is already exercised (e.g. by a bad `archetype_id` key
  lookup today).

The other reason to raise rather than flag: `openubem/acquisition/__init__.py:122` —
`assert out["epw_path"].isna().sum() == 0, "epw_path must never be null"` — establishes that a
null/missing `epw_path` is **already a contract violation** at Stage-1 acquisition. A row reaching
`BuildingIDF.__init__` with a missing or nonexistent EPW is therefore off-contract, not a legitimate
degraded case to flag-and-continue.

**Change made** (`openubem/idf/builder.py:210-217`):
```python
epw_path = row.get("epw_path")
if epw_path and Path(str(epw_path)).exists():
    _populate_site_location_from_epw(self.idf, Path(str(epw_path)))
else:
    raise ValueError(
        f"osm_id={row.get('osm_id')!r}: epw_path {epw_path!r} is missing or "
        "does not exist -- refusing to build at the template's placeholder "
        "Site:Location (Latitude=0.0, Longitude=0.0)"
    )
```

**After (demonstrated on the same two cases):**
```
case='missing (empty string)'   raised ValueError: osm_id='way/999': epw_path '' is missing or does not
                                 exist -- refusing to build at the template's placeholder Site:Location
                                 (Latitude=0.0, Longitude=0.0)
case='nonexistent path'         raised ValueError: osm_id='way/999': epw_path 'C:/nope/does_not_exist.epw'
                                 is missing or does not exist -- refusing to build at the template's
                                 placeholder Site:Location (Latitude=0.0, Longitude=0.0)
```

**No STOP triggered.** There is no production mode that legitimately builds without an EPW: the only two
call sites that construct `BuildingIDF` (`run_step3`'s serial loop and `_build_one`'s loky path) already
wrap construction in `try/except Exception`, and Stage-1's own contract (`acquisition/__init__.py:122`)
guarantees `epw_path` is never null on a well-formed row. The `layout_assign` baseline branch inside
`build()` (`builder.py:475-477`, `layout_assigner.patch_location_and_weather`) is a **separate** call
site, not touched — it is out of this task's cited scope (`builder.py:210-212` only) and has its own
independent `if epw_path and exists()` guard the plan did not name.

**Tests.** `pytest -q tests/test_idf_builder.py tests/test_layout_assigner.py tests/test_step3_orchestrator.py`
→ **187 passed**, exit code 0, before and after inspection of the diff confirms no test constructs
`BuildingIDF` with a missing/nonexistent `epw_path` (all use a real fixture EPW, e.g.
`tests/test_idf_builder.py:142-146`'s `_make_row` and `tests/test_layout_assigner.py:1367`'s
`_make_layout_assign_row`). No test that passed before now fails.

### (b) The other two survivors — re-grepped, not fixed

- **`compute_form_factor` (`openubem/geometry/footprint.py:66`) — still genuinely never called in
  production.** Repo-wide grep for the literal `compute_form_factor` returns exactly three sites: its own
  definition (`footprint.py:66`), its import and three direct calls inside its own unit test
  (`tests/test_footprint.py:13,179,186,191`), and mentions inside investigation/measurement docs under
  `docs/`. **Zero occurrences** under `openubem/` (outside its own definition) or `scripts/`. Dead code,
  confirmed at HEAD — not fixed, per instruction (scope decision).
- **`openubem/geometry/context.py:24` — still recomputed per row, uncached.**
  `ctx_box = ctx_row.geometry.minimum_rotated_rectangle` sits inside `discover_context()`'s per-candidate
  loop (`context.py:19-42`), so every candidate neighbour's minimum-rotated-rectangle is recomputed fresh
  for every target building that finds it within the shading sphere — no cache keyed on `osm_id` across
  calls. Confirmed at HEAD by direct read. Efficiency-only, not fixed, per instruction (scope decision).

---

## T06 — OPEN-29

### Step 1 — re-grep of the four sites (before fixing)

All four sites named in the plan's §4 were confirmed still at those lines, unchanged, immediately before
the fix:

| Site | Line | Literal(s) found |
|---|---|---|
| `scripts/diagnostics/t01_reproduce_degenerate.py` | 108 | `"** Severe **", "**  Fatal **", "** Fatal  **"` |
| `scripts/diagnostics/t04_validate_way428643335.py` | 133 | `"** Severe **", "** Severe  **", "**  Fatal **", "** Fatal  **"` |
| `scripts/diagnostics/t06_validate_relation6374725.py` | 153 | `"** Severe **", "** Severe  **", "**  Fatal **", "** Fatal  **"` |
| `scripts/validation/phaseE_cpb_fixtures.py` | 176 | `txt.count("** Fatal  **") + txt.count("**  Fatal  **")` |

No fifth site was found under `scripts/` or `openubem/`. A full grep for `Fatal` under both trees turned
up one already-correct production site (`openubem/simulation/runner.py:140`, uses the true two-space
`"**  Fatal  **"` literal directly) and a set of already-fixed cluster-harvest/analysis sites using the
R06 regex `\*\*\s+Fatal\s+\*\*` (`scripts/cluster/t07_harvest_results.py`, `t07b_run_auto_refit_local.py`,
`t08_harvest_results.py`, `t08_local_remainder.py`, `t17`–`t20_harvest_layout_assign.py`,
`scripts/analysis/e02_cluster_readonly_audit.py`, `e02_failure_causes_subsurface.py`,
`scripts/analysis/a3_update_summary.py`). Two loose substring checks
(`scripts/run_r1_targeted.py:153`, `scripts/validation/v05b_fix_storeys.py:481-482`) test for the bare
word `"Fatal"` with no fixed spacing at all — a different (over-permissive, not under-permissive) shape,
not named by the plan, not touched.

### Step 2 — (a) the three diagnostics scripts, fixed

Each of the three `scripts/diagnostics/` sites was changed to use R06's own regex, `\*\*\s+Fatal\s+\*\*`,
for the Fatal half of its check only — the Severe half (a different, out-of-scope defect: see below) was
left as originally written, per the plan's "measurement forbids remediation of anything but the fatal
class" framing. One `import re` was added where missing (all three lacked it); one substitution per file;
no reformatting.

- `t01_reproduce_degenerate.py:108-109`: `("** Severe **" in l) or re.search(r"\*\*\s+Fatal\s+\*\*", l)`
- `t04_validate_way428643335.py:132-133`: `any(kw in l for kw in ("** Severe **", "** Severe  **")) or re.search(r"\*\*\s+Fatal\s+\*\*", l)`
- `t06_validate_relation6374725.py:152-153`: same pattern as t04.

All four touched files (the three above plus `openubem/idf/builder.py`) pass `python -m py_compile`.

**Side note on the Severe half, found while re-grepping, not fixed (out of this task's scope):**
real EnergyPlus output uses `"** Severe  **"` — one space before, **two** spaces after — confirmed by
scanning the E02 corpus (908/40,800 files contain `"** Severe  **"`, 0/40,800 contain the one-space
`"** Severe **"` that t01 still tests alone). t01's Severe check is therefore also blind on real output.
This is the same defect shape as E-LA-21 but for `Severe`, not `Fatal`, and RULING C names only the
fatal-test occurrence class — reported here as a new observation, not fixed, not counted as an OPEN-29
defect ID by this task.

### Step 3 — `phaseE_cpb_fixtures.py:176` — measured, not changed

`fatal = txt.count("** Fatal  **") + txt.count("**  Fatal  **")`. The second term is the true two-space
canonical form. Over the real 40,800-file E02 corpus (below), the first term (`"** Fatal  **"`, one space
before / two after) matches **0** files while the second term matches exactly the ground-truth **44**.
Because `.count()` sums both terms, and the first term contributes zero real matches, **this site's
`fatal` count is empirically correct on real EnergyPlus output — neither under- nor over-counting.** The
over-count risk the plan flagged is real in principle (a file containing only the malformed literal, not
the canonical one, would be double-safe but wrongly counted) but was never observed in 40,800 real files;
EnergyPlus's own fatal-line format is evidently fixed and always two-space. Not changed, per instruction.

### Step 4 — the measurement: variant vs. ground truth (44), over the real E02 corpus

Corpus: `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest`, read-only, 40,800 `.err` files scanned
(count reproduced live, matches the register's own recount). Full results in
`openubem/outputs/comparisons/open29_diagnostics_fatal_recheck.csv`:

| Variant | Files matched | vs. ground truth (44) |
|---|---:|---:|
| `**  Fatal  **` (true two-space canonical) | 44 | 0 |
| `** Fatal **` (one-space, E-LA-21 defect shape) | 0 | -44 |
| `**  Fatal **` (malformed: 2 before / 1 after — used by the 3 diagnostics scripts) | 0 | -44 |
| `** Fatal  **` (malformed: 1 before / 2 after — used by the 3 diagnostics scripts and by phaseE_cpb_fixtures.py) | 0 | -44 |
| `\*\*\s+Fatal\s+\*\*` (R06 regex fix, now also used by the 3 diagnostics scripts) | 44 | 0 |
| `phaseE_cpb_fixtures.py` site (`"** Fatal  **"` OR `"**  Fatal  **"`, file-level union) | 44 | 0 |

**Non-vacuity:** the corpus does contain real fatals (44, matching the register's ground truth exactly)
and the malformed variants tested by the three diagnostics scripts matched **zero** of them — the
"before" (0 matches) is shown to differ from the "after" (44 matches, via the R06 regex) on the same
real data, not asserted.

### Step 4 — per-script conclusion verdicts

**t01_reproduce_degenerate.py — conclusion did NOT depend on the fatal test.** This script's own
historical record (`docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_coreperim-degenerate-fix.md:200-202`,
T01 progress log, 2026-06-18) states explicitly: *"E+ did NOT terminate with `**  Fatal  **` — it issued
`** Severe  **` and continued into sizing before the pipeline's timeout killed it (no `eplusout.end`)."*
The one building this script tests (`way/428643335`, pre-fix) never produced a Fatal line at all — the
malformed Fatal literal matched zero occurrences in that run for the same reason it matches zero in the
40,800-file corpus (EnergyPlus's own format is fixed at two-space), but so would the correct regex, since
there was no Fatal line to find. The script's actual gating conditions were `assert not ok` (E+ did not
report a completed run) and `assert any("degenerate" in l.lower() for l in severe_lines)` — the latter
depends on the *Severe* half of the filter (itself separately blind, see above), not the Fatal half. The
fatal-test defect could not have changed this recorded outcome.

**t04_validate_way428643335.py — conclusion did NOT depend on the fatal test.** None of its `assert`
statements reference `severe_lines` at all — it is built purely for the `print()` diagnostic block
(`t04_validate_way428643335.py:138-141`). The actual pass/fail gates are `assert ok` (line 144, gated on
EnergyPlus's own completion return) and `assert not degen_lines` (line 145, a separate `"degenerate" in
l.lower()` substring test, unrelated to the Fatal/Severe literal). Its own recorded conclusion
(`PLAN_coreperim-degenerate-fix.md:270-277`) states `EnergyPlus Completed Successfully-- 82 Warning; 0
Severe Errors` and `0 degenerate lines … 0 severe/fatal errors` — a genuinely clean run reported directly
by EnergyPlus, independent of this script's own (broken) string match.

**t06_validate_relation6374725.py — conclusion did NOT depend on the fatal test.** Its recorded outcome
(`PLAN_coreperim-degenerate-fix.md:337-361`) is `EnergyPlus Completed Successfully-- 26 Warning; 0 Severe
Errors`, i.e. EnergyPlus itself reported zero Severe/Fatal messages for `relation/6374725` post-fix. The
one assert that reads `severe_lines` (`assert not mismatch_severes`, line 166) is therefore vacuously
satisfied either way: an empty `severe_lines` list from a genuinely clean run passes regardless of which
Fatal literal or regex built the filter. The malformed test could not have changed this outcome because
there was nothing for either version of the test to find.

**Common answer across all three:** the fatal-test occurrence class was blind (0/44 on real data) exactly
as R06 already established for the cluster-harvest sites, but in these three cases it never mattered to
the printed/recorded conclusion — each script's actual pass/fail gate was EnergyPlus's own return status
or a `"degenerate"`/`"mismatch"` text search, not the malformed Fatal literal. This is "the common one"
answer the plan anticipated.

---

## Deliverables

- `openubem/outputs/comparisons/open29_diagnostics_fatal_recheck.csv` — one row per variant string.
- Code changed: `openubem/idf/builder.py` (T05a), `scripts/diagnostics/t01_reproduce_degenerate.py`,
  `t04_validate_way428643335.py`, `t06_validate_relation6374725.py` (T06a). No other file touched.
- No item closed by this report. OPEN-26/OPEN-29 disposition is the director's call at CP-3.
