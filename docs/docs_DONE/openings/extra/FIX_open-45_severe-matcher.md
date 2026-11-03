# FIX — OPEN-45: whitespace-tolerant Severe/Fatal matcher (T01 + T02)

**Executor:** A. **Plan:** `PLAN_three-new-items-2026-08-12.md`, T01–T02. **Date:** 2026-08-12.

## T01 — the helper and its test

New module `openubem/results/err_parse.py`: `SEVERE_RE`, `FATAL_RE`, `WARNING_RE`
(`re.compile(r"^\s*\*\*\s+<word>\s+\*\*", re.MULTILINE)`), `iter_severe`, `first_severe`,
`count_severe`, `has_fatal`. Docstring states the two-space fact and cites this plan.

New tests `tests/test_err_parse.py`: 16 tests, fixtures with the real two-space forms
(`**  Severe  **`, `**  Fatal  **`, `**  Warning  **`) and the one-space forms; both match.

**Non-vacuity control (hard rule 7, T01 step 3).** `TestNonVacuityControl` in
`tests/test_err_parse.py`:
- `test_old_one_space_substring_check_fails_on_real_fixture` — runs the exact old
  `v12_cell_pipeline.py:625` logic (`"** Severe **" in l`) against the real two-space
  fixture and asserts it returns `""`. **This passed**, i.e. the old check is confirmed
  to fail on real EnergyPlus output.
- `test_new_matcher_passes_on_same_fixture` — runs `first_severe()` on the same fixture
  and asserts a non-empty result containing the expected text. **This passed.**

Full `pytest tests/test_err_parse.py -q` output:
```
................                                                         [100%]
16 passed in 0.05s
```

**Live demonstration on a real `.err` file.** No `.err` file survives locally for the
adopted `phaseE_elevrb` run (see Leg B below), but real EnergyPlus `.err` files exist
elsewhere on this machine, e.g.
`docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/a2_run_multiplier/eplusout.err`.
Its real Severe line is `'   ** Severe  ** Transformer Overloaded'` (one space before
"Severe", two after — an asymmetric form neither the one-space nor a naive two-space-both-sides
literal would catch). Direct comparison:
```
OLD one-space check result: ''
NEW matcher result: '** Severe  ** Transformer Overloaded'
```

`scripts/validation/v12_cell_pipeline.py:625` repointed at `first_severe()` (import inside
the function, matching that file's existing convention at `:125`/`:155`/`:204`). `:622`'s
working `Warning; ... Severe` count regex was left untouched. AST-parses cleanly; the module
imports and runs as a real module (`build_sim_manifest` present).

## T02 — the sweep and recoverability

**Leg A — sweep.** `scripts/analysis/open45_severe_literal_sweep.py` re-derives every
`** Severe **` / `** Fatal **` / `** Warning **` literal site in `openubem/`, `scripts/`,
`tests/` (excluding `scratchpad/` and `docs_DONE/`), independently of §4's list, via
`re.compile(r"\*\*\s*(Severe|Fatal|Warning)\s*\*\*")`. It carries its own non-vacuity
control (plants a known one-space literal in a scratch file under `scripts/analysis/`,
confirms the scanner finds it, deletes the scratch file, confirms the scanner no longer
finds it) — this passed (`Non-vacuity control passed: True`).

Output: `openubem/outputs/comparisons/open45_severe_literal_sweep.csv`
(`path, line, literal, classification, action_taken, reason`), 25 rows after the two
already-fixed sites (see below) drop out of the scan:

| classification | count |
|---|---|
| one-off | 15 |
| already-correct | 8 |
| load-bearing | 2 |

**Sites repointed at the helper (this task):**
1. `scripts/validation/v12_cell_pipeline.py:625` (T01) — the original OPEN-45 target;
   confirmed load-bearing (`build_sim_manifest` is the production function that produced
   the adopted run's 8,160-row manifest set, per `open42_six_failures.py`'s own citation of it).
2. `scripts/cluster/make_manifest_from_cluster.py:47` (T02) — generic, reusable Step-4
   manifest adapter, referenced by `scripts/cluster/fetch_r3_results.py`/`.sh`,
   `scripts/validation/v11_nyc_centre_pipeline.py`, and
   `docs/docs_main/docs_step-4/PLAN_step-4-cluster-offload-R4.md` — infrastructure, not a
   spent one-off.

Both diffs are two-line replacements (delete the literal filter, add
`from openubem.results.err_parse import first_severe` + call); `:622`-equivalent count
logic untouched where present. Both files AST-parse and real-import cleanly after the change.

**Load-bearing sites found but NOT repointed (out of Executor A's write-scope per plan
§6, which restricts Executor A to `openubem/results/err_parse.py`, `tests/test_err_parse.py`,
and the load-bearing **`scripts/**`** sites — not `openubem/**` or `tests/**` generally).
Flagged for the director / a future task:**
1. `openubem/simulation/runner.py:140` — `"**  Fatal  **" in line` (two-space, matches the
   real Fatal form exactly, so not the one-space bug, but not tolerant of any other spacing).
2. `tests/test_sim_integration.py:171` — `"**  Severe  **" in l or "**  Fatal  **" in l`.
   The Fatal half matches real output; **the Severe half does not** — every real Severe line
   found on this machine is `** Severe  **` (one space before, two after), not
   `**  Severe  **` (two before). This test's Severe branch has the same silent-miss bug as
   OPEN-45, just with a different wrong spacing guess. It is not in Executor D's four named
   test files either, so nobody in this plan owns fixing it.

**One-off sites (15) — listed, left alone, per Leg A's instruction not to rewrite spent
scripts:** all under `scripts/validation/v12_la_*`, `v12_nyc_urban_recovery.py`,
`run_v11_step5.py` (predecessor V12/V11 validation-cell repair/recovery scripts, each tied
to one specific building or cell incident and writing to
`docs/validations/overAll/results/cases/...` — a different, older tree than the adopted
run's `docs/docs_VALIDATION/.../phaseE_elevrb/`), `scripts/diagnostics/t01_reproduce_degenerate.py`
(single-building diagnostic), and `scripts/analysis/a2_parse_results.py` /
`a3_measure_band_deletion.py` (closed layoutAssigner storey-matching arc — "not certified
for fleet EUI" per project memory, so cannot be on a path to an adopted artifact). Full
per-row reasoning is in the CSV and in `scripts/analysis/open45_severe_literal_sweep.py`'s
`CLASSIFICATION` table.

**Already-correct sites (8):** `scripts/validation/phaseE_cpb_fixtures.py:176-177` and
`scripts/diagnostics/t06_validate_relation6374725.py:154` /
`t04_validate_way428643335.py:134` (the two director-named "handles both forms" sites, plus
`phaseE_cpb_fixtures.py` split into its two `.count()` lines); `e02_failure_causes_subsurface.py:8`
(docstring only — the actual code already uses `\s+`-tolerant regex); `c01_storey_matching_regression.py:153-154`
(comments only) and `open42_six_failures.py:49` (a marker string embedded in report prose,
not matching logic).

**Before/after count of load-bearing one-space sites** (a single "after" number is not a
result per the plan — both counts, independently verified):
- **Before** (grep of the live tree prior to any edit in this task): 2 load-bearing
  one-space sites — `v12_cell_pipeline.py:625` and `make_manifest_from_cluster.py:47`.
- **After** T01 + T02: 0 load-bearing one-space sites remain. (2 load-bearing
  *non*-one-space sites remain, listed above, out of this executor's write-scope.)

**Import/parse check** on both repointed files:
```
scripts/validation/v12_cell_pipeline.py       -> AST_OK, real import OK (build_sim_manifest present)
scripts/cluster/make_manifest_from_cluster.py -> AST_OK, real import OK (build_manifest present)
```

**Leg B — recoverability.** Can `error_summary` be backfilled for the adopted
`phaseE_elevrb` run from surviving `eplusout.err` files?

**No — the evidence is gone, for the whole run, not only the six known failures.**
All twelve adopted `04_simulation_manifest.parquet` files (8,160 rows total, matching §4's
figure) were read; every row's `work_dir` points under
`C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\<cell>\sim_out\<osm_id>\`. An
exhaustive check (all 8,160 rows, not a sample) found every one of those directories exists
but is empty (0 files each) — `os.listdir()` returned `[]` for all 8,160. A directory-tree
walk of the whole `ubem_elev_rebaseline` root (not just the `work_dir` paths from the
manifest) found 0 files anywhere under it — only the empty directory skeleton
(`<cell>/fleet_staging/idfs/`, `<cell>/results/figures/`, `<cell>/sim_out/<osm_id>/`)
survives. A machine-wide search for other `*elev_rebaseline*` directories or `.tar`/`.zip`
archives that might hold a cached copy found none (a few unrelated `elev_smoke_*` /
`ubem_elev_ab` / `ubem_elev_meterfix` temp dirs exist from other, smaller test runs, not
the adopted 12-cell run). This was a local-filesystem search only, per hard rule 1 (no
cluster/ssh) — the cluster itself was not and could not be checked.

**Conclusion: `error_summary` cannot be backfilled for any of the 8,160 adopted-run rows.**
The counts (`n_warnings`, `n_severe`) remain sound, as §4 already established, because they
were parsed by the separate working regex at the old `:622` and persisted to the parquet at
run time — but the underlying `.err` text itself no longer exists on this machine for any
adopted-run building, success or failure.
