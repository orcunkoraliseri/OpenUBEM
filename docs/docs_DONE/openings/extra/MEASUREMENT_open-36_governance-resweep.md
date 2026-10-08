# MEASUREMENT — OPEN-36: re-checking N13's "1 governance gap in 596" bound

**Task:** T08, `PLAN_rulings-and-five-items-2026-08-12.md`
**Date:** 2026-08-12
**Trigger:** T05 found 5 live-failing tests in `tests/test_debias.py`, all `AttributeError: module
'openubem.config' has no attribute 'IMPUTE_DEBIAS_NEWERSKEW'` — the same shape as T07's known gap
(tests committed, implementation not). T08 exists to determine whether this is a second instance and,
if so, how many more there are.

## Headline

**N13's bound does not hold. This re-sweep finds 6 genuine governance-gap entries in the same 596-entry
population N13 swept, not 1** — the T07 case N13 already knew about, plus **5 new ones**, tracing back
to **4 distinct underlying incidents** (the elevator EUI breakout ties two entries together; the draw-tier
promotion effort ties two more together):

| # | Task | File:line | What was claimed, never committed |
|---|---|---|---|
| 1 (known) | **T07** | `IMPLEMENTATION_phaseC_ml_imputer.md:849` | `_draw_tier`, `_draw_stratum_col_for` in `imputation.py` |
| 2 (new) | **T09b** | `IMPLEMENTATION_phaseC_ml_imputer.md:946` | `variance_ratio`, `iqr_ratio`, `energy_distance`, `score_categorical_tv`, `bootstrap_noise_floor`, `variance_ratio_bootstrap_ci`, `_as_2d` in `openubem/validation/mask_recover.py` |
| 3 (new) | **T11.8** | `docs_Done/PLAN_phaseC_ml_imputer.md:636` | `config.IMPUTE_DEBIAS_NEWERSKEW` + the `_ml_tier` opt-in hook in `imputation.py` |
| 4 (new) | **T11.8b** | `docs_Done/PLAN_phaseC_ml_imputer.md:663` | `_DEBIAS_NEWERSKEW_QMAP_GLOBAL`, `_DEBIAS_NEWERSKEW_QMAP`, `_DEBIAS_SKIPPED_THINSTRATUM` in `imputation.py` |
| 5 (new) | **T04** (input-framework) | `PLAN_input-framework-classification-fixes.md:129` | `test_i01_new_tag_spot_checks`, `test_service_not_remapped_to_commercial`, `TestI01FixtureDiffRegression` in `tests/test_building_classifier.py` |
| 6 (new) | **T04** (elevator_loads) | `PLAN_elevator_loads_implementation.md:159` | `test_medium_office_idf_contains_elevator_equipment` claimed in `tests/test_step3_orchestrator.py` |

**#2 pairs with #1** (same file, adjacent entries, same abandoned "promote the draw tier" arc).
**#3 pairs with #4** (same file, adjacent entries, same "de-bias corrector" arc). So by *incident*, not
*entry*: 4 incidents, not 6. Either count is more than N13's 1.

## Method

Re-ran a fresh, independent verification over **the same 596-entry population** N13 built (reused from
`openubem/outputs/comparisons/open36_completion_record_sweep.csv` — file/line/task/claimed-artifact
extraction, not verdicts). Every artifact (file or symbol) was re-checked from scratch against the
current HEAD, using the plan's pinned test:

- **File check:** `git cat-file -e HEAD:<path>` (exists at HEAD) → PRESENT; else
  `git log --all --oneline --follow -- <path>` non-empty → MOVED; else → NEVER-COMMITTED.
- **Symbol check:** present in the paired file's HEAD content → PRESENT; else
  `git log --all -S"<symbol>" -- "<exact paired file>"` (restricted to that one file, the plan's
  sanctioned test) → non-empty means it existed there once and was removed; else a **restricted**
  repo-wide fallback (`.py` files under `openubem/`, `scripts/`, `tests/` only, requiring the symbol to
  appear in a definition-shaped context — `def foo`, `class Foo`, `foo = `, `foo:` — not a bare
  substring) to catch proximity mis-pairing, exactly as N13's own correction pass intended.

Script: `scripts/analysis/open36_governance_resweep.py` (new — N13's own sweep script does not survive
under `scripts/`, confirmed by search). Output:
`openubem/outputs/comparisons/open36_governance_resweep.csv` — 596 rows,
`record_file, line, task, claimed_artifact, exists_at_head, ever_in_git, verdict`.

### The one deliberate methodology fix, and why it matters

N13's own correction pass used an **unrestricted** repo-wide search to catch proximity mis-pairings (a
real, documented problem — 35 genuine cases). But unrestricted meant it also matched a symbol's
appearance in a **plan document's own prose** (the `.md` file describing the intended code) and treated
that as evidence of "moved/renamed" code. This is exactly what happened to T11.8b: N13's raw first pass
correctly flagged `_DEBIAS_NEWERSKEW_QMAP_GLOBAL` / `_DEBIAS_NEWERSKEW_QMAP` / `_DEBIAS_SKIPPED_
THINSTRATUM` as NEVER-COMMITTED in `imputation.py` — genuinely correct — and then the correction pass
flipped all three to PRESENT with the note *"found via repo-wide -S at ef19141 (moved/renamed)"*.
Independently confirmed: `git log --all -S"_DEBIAS_NEWERSKEW_QMAP_GLOBAL"` (no path restriction) returns
only two commits, and the **only** file either of them touches containing that string is
`docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseC_ml_imputer.md` itself — the plan document
narrating the intended change, not `openubem/semantic/imputation.py`. N13's correction mistook "the
constant's name is written down in the plan" for "the constant was committed." This re-sweep's fallback
search is restricted to `.py` files and requires a definition-shaped match specifically to avoid this.

## Non-vacuity control (required by the plan)

**T07's known gap is found.** `docs/docs_DONE/INPUTS/imputation/implementation/
IMPLEMENTATION_phaseC_ml_imputer.md:849` resolves to `NEVER-COMMITTED -> GENUINE-GAP` in the resweep.
**PASS.** (Two unrelated entries also literally named "T07" exist in other plan documents — task IDs are
scoped per-document, not global — both correctly resolve PRESENT; they are different tasks with
different artifacts, not a dilution of the control.)

## Verdict counts, against N13's numbers

| Verdict | This re-sweep | N13 (corrected) |
|---|---|---|
| Total entries | **596** | 596 |
| Checkable | 444 | 444 |
| UNCHECKABLE | 152 | 152 |
| PRESENT | 421 | 424 |
| MOVED | 6 | 6 |
| NEVER-COMMITTED, resolved as **genuine gap** | **6** | **1** |
| NEVER-COMMITTED, resolved as rename / misattribution / false-positive | 11 | 12 (N13 folded pending-external-commit + self-disclosed-ephemeral + misattribution together as 13, +1 gap = 14) |

421 + 152 + 6 + 6 + 11 = 596. **Total population and checkable count both reproduce N13's exactly** — the
extraction (which artifact is claimed where) is unchanged; only the **verdicts** on 17 of the 444
checkable entries were re-derived and, for 6 of them, changed from N13's PRESENT/self-disclosed to
GENUINE-GAP.

## Every one of the 16 NEVER-COMMITTED-on-first-pass rows, disposed of individually

**Genuine gaps (6) — evidence for each:**

1. **T07** — `_draw_tier`/`_draw_stratum_col_for` absent from `imputation.py`, all git history, all
   branches (N13's own control, reconfirmed).
2. **T09b** — none of `variance_ratio`, `iqr_ratio`, `energy_distance`, `score_categorical_tv`,
   `bootstrap_noise_floor`, `variance_ratio_bootstrap_ci`, `_as_2d` exist in
   `openubem/validation/mask_recover.py` (confirmed: full `grep -n "^def "` listing of the file shows
   none of the 7; `git log -S"variance_ratio" -- openubem/validation/mask_recover.py` empty). Same
   file, next entry after T07, same "extend the draw-tier CP-DRAW metric harness" arc — the whole
   promotion effort stalled after tests were written, not just the router wiring.
3. **T11.8** — `config.IMPUTE_DEBIAS_NEWERSKEW` and the `imputation.py::_ml_tier` opt-in hook: confirmed
   absent from `openubem/config.py` and `openubem/semantic/imputation.py` in every commit, every branch
   (`git log --all -S"IMPUTE_DEBIAS_NEWERSKEW"` on both files, empty). **This symbol was never
   proposed as a candidate by the extraction heuristic at all** (an extraction-coverage miss, not a
   verification error) — found only because T05's live test failure named it directly. Flagged
   explicitly so the coverage gap itself is on record, not just this one instance of it.
4. **T11.8b** — see "the one deliberate methodology fix" above.
5. **T04 (input-framework)** — `test_i01_new_tag_spot_checks`, `test_service_not_remapped_to_commercial`,
   `TestI01FixtureDiffRegression`: the entry's own Artifacts line and a detailed `-k`-filtered test-run
   claiming "7 passed" name these exactly; direct `grep` of `tests/test_building_classifier.py` at HEAD
   and `git log --all -S` on each name (that exact file) both come back empty. `class
   TestUseClassMapping` (the class they were claimed to be added to) exists, just without these tests.
6. **T04 (elevator_loads)** — `test_medium_office_idf_contains_elevator_equipment` claimed for
   `tests/test_step3_orchestrator.py`; `git log --all -S` on that exact file is empty. It exists **only**
   in the `docs/docs_DONE/.../elevators/scripts/tests/` archived mirror (T05's finding, independently):
   the drift there is not a copy that fell out of sync after both once matched — this test never reached
   the canonical `tests/` file in the first place.

**Renames / self-disclosed deletions / extraction noise (9), each individually confirmed, not assumed:**

`T07.2` (`_clamp_to_observed_range` — clamping logic present inline via `np.clip`, just not factored into
a function with this name); `T12-ship` (`test_default_tiers_never_touch_ml` — inconclusive: a near-
identical `test_default_tiers_never_touch_fusion_or_ml` exists with equivalent intent and
`IMPUTE_ENABLED_TIERS` matches the entry's core claim; not confirmed either way, so **not** counted as a
gap); `T10` layoutAssigner (`la_eui`/`BASELINE_IDF_REGISTRY` — entry's own prose says both were
*deleted on purpose*; `prototype_zones_count`/`layout_assign_mode_zones` confirmed present in
`scripts/analysis/compare_layout_assign.py:202,206`, just mis-paired with the wrong test file by the
extractor); `T16` layoutAssigner (`county_within` confirmed present as a string literal in
`openubem/acquisition/climate_zone.py:133`); `I04` (`nyc_rural` — a cell name from the investigation's
own subject matter, not a claimed code artifact); `C1`–`C4` in `REMEDIATION_prompts-audit-fixes.md` (all
four are **explicitly, textually documented renames or replacements inside their own entries** — e.g. C1:
*"renamed `test_z_origin_set_on_multi_floor_buildings` → `test_multi_floor_surfaces_at_correct_z`"*; C4:
*"Old `test_adiabatic_perim_core_party_wall` is gone; `test_perim_core_party_wall_surface_matched`
replaces it"* — self-disclosed, not concealed); `E4` (`KeyError` — a Python builtin exception name
in prose, mis-extracted as if it were a claimed artifact).

**Self-disclosed ephemeral (1):** `T02` (`scripts/_build_test.py`) — matches N13's own already-documented
finding exactly (entry labels it "temp, deleted after use").

## What this means for OPEN-36

Per §7 of the plan: *"OPEN-36 closes only if the re-sweep confirms exactly one gap and IMPUTE_DEBIAS is
shown not to be a second... more than one gap — and then the item grows."* **IMPUTE_DEBIAS is a second
gap (in fact two, T11.8 + T11.8b), and there are four more beyond that.** OPEN-36 does not close on this
pass; per the plan, this is the director's decision, not this report's — but the evidence is unambiguous:
**completion records naming code artifacts in this repository have a real, non-trivial false-positive
rate** (6 of 444 checkable entries, 1.4%, confirmed gaps — not the 1-in-596 (0.2%) N13's corrected number
implied). All 6 share one structural signature: the arc's **tests** landed in a single commit alongside
extensive documentation describing the code, but the **implementation** changes to the named `openubem/`
files did not — four of the six are two pairs of *adjacent* progress-log entries in the same two files,
suggesting this is not six independent accidents but a small number of session-boundary failures where
a large batch of work (tests + docs + some but not all production code) was prepared and only partially
committed.

## Artifacts

- `scripts/analysis/open36_governance_resweep.py` — the re-sweep script.
- `openubem/outputs/comparisons/open36_governance_resweep.csv` — 596 rows,
  `record_file, line, task, claimed_artifact, exists_at_head, ever_in_git, verdict`. Verdict values:
  `PRESENT`, `MOVED`, `UNCHECKABLE`, or `NEVER-COMMITTED -> {GENUINE-GAP, RENAME/FALSE-POSITIVE,
  RENAME/INCONCLUSIVE, SELF-DISCLOSED-EPHEMERAL}` (the `->` split keeps the raw mechanical verdict and
  the audited disposition both on the row, same transparency convention N13 used).

## What T08 did not do

Did not fix `config.IMPUTE_DEBIAS_NEWERSKEW`, `_draw_tier`, or any of the other 5 gaps' missing code.
Did not re-verify the 421 PRESENT or 152 UNCHECKABLE entries beyond what the script did (trusted the
population extraction from N13; independently recomputed every verdict). Did not exhaustively re-derive
the population from the four documentation roots from scratch (reused N13's file/line/task/artifact
extraction, which this task has no reason to distrust — only N13's *verdicts* were in question).
