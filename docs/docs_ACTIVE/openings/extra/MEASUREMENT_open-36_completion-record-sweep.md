# MEASUREMENT — Is T07 the only completion record whose code was never committed? (OPEN-36)

> Task N13, `PLAN_no-compute-queue-3.md` §6. Measurement only — no remediation attempted, no
> judgment of the entry's author. HEAD at time of sweep: `bca92d0`.

## 0. Answer, one sentence

**Within the swept population, T07 (`docs/docs_DONE/INPUTS/imputation/implementation/
IMPLEMENTATION_phaseC_ml_imputer.md:849`) is the only progress-log entry whose claimed code artifact
is verified absent from every commit on every branch, in every file in the current repository, with
no innocent explanation** — after separating that result from two categorically different, non-governance
reasons a check can also come back "never committed" (below).

## 1. Population, built and counted before any entry was judged

Every line matching the project's progress-log template, `^#### TXX — <title> — completed
YYYY-MM-DD`, across all four documentation roots (`docs_DONE/`, `docs_main/`, `docs_ACTIVE/`,
`docs_INVESTIGATE/`) — 58 files contain at least one such entry (`git grep`-style file sweep, listed
in full in the CSV).

| Quantity | Count |
|---|---|
| **Total progress-log entries (the population)** | **596** |
| Entries naming ≥1 checkable code artifact (**checkable**) | **444** |
| Entries with no Artifacts field, or only prose/unresolved mentions (**UNCHECKABLE**) | **152** |

**"Checkable" is defined exactly as the plan specifies:** a named symbol or file under `openubem/`,
`scripts/`, or `tests/`, extracted from the entry's `Artifacts:` field. An entry that only says
something like *"wired the router"* or names a plan/report `.md` file is UNCHECKABLE — that is itself
a finding about roughly a quarter of the template's usage (152/596 = 25.5%), not a defect: many of
these are memo-only entries (manager audits, diagnostic write-ups, MANAGER-tagged rows) that never
claimed a code artifact in the first place.

A loose file-level `grep -c` taken before extraction suggested ~625 matching lines; the precise
template regex used for extraction returns 596. The difference is headers that resemble the template
(e.g. some manager-audit entries) but do not fully match it — 596 is the number actually walked,
parsed, and tested.

## 2. Method

**Two-layer check, both git-based, both re-runnable:**

1. **File-level (authoritative, exhaustive over the full 444).** Every file path named in an entry's
   `Artifacts:` field is resolved against `git ls-files`. If present at HEAD → **PRESENT**. If absent
   at HEAD, `git log --all --oneline --follow -- "<path>"` decides **MOVED** (history exists) vs.
   **NEVER-COMMITTED** (no history on any branch, ever) — the direct file-path analogue of the plan's
   sanctioned symbol pickaxe test.
2. **Symbol-level (best-effort, layered on top).** Backtick-quoted identifiers appearing in the same
   semicolon/newline-delimited clause as a `.py` file mention are treated as candidate symbols
   (filtered to code-shaped tokens: contains `_`, is `CamelCase`, is `ALL_CAPS`, or ends `()` — plain
   English words are excluded). Each candidate is checked against the paired file's HEAD content, and
   if absent there, against **the plan's sanctioned test, exactly**:
   `git log --all -S"<symbol>" -- "<path>"`. Empty on every branch → **NEVER-COMMITTED**.

**Verdicts:** the four the plan allows and no others — PRESENT, MOVED, NEVER-COMMITTED, UNCHECKABLE.
An entry's overall verdict is the worst case across all of its named artifacts (file or symbol);
a symbol confirmed absent everywhere overrides an otherwise-present file, which is exactly the shape
of the T07 defect itself (the file exists; the one symbol inside it does not).

### 2.1 A methodology defect found and corrected mid-sweep, reported for transparency

The symbol-to-file pairing is a **proximity heuristic** (nearest `.py` mention in the same clause),
not a semantic parse of free-form multi-paragraph prose written by dozens of different sessions over
two months. The first full run flagged 37 entries NEVER-COMMITTED beyond the T07 control. Before
reporting that number, every one of those 37 was independently re-checked with an **unrestricted,
repo-wide** search (`git grep` across the whole tree at HEAD, plus `git log --all -S"<symbol>"` with
**no path restriction**) — the plan's own hard rule (§2 rule 5: recompute every headline number from
the named file, never carry a plausible-looking one forward). That re-check found:

- **35 of 37 were misattribution artifacts of the heuristic** — the symbol exists at HEAD, just in a
  *different* file than the one my proximity guess picked (e.g. `_draw_tier` correctly resolves inside
  `imputation.py`, but a symbol like `resolution_mode` mentioned two files later in the same paragraph
  got paired with the wrong neighbour). Each of these 35 is individually cited in the CSV's
  `correction_note` column with the file where the symbol actually lives.
- **1 was a genuinely different, non-governance case** (`RETAIN_FILENAMES`, E01,
  `scripts/cluster/t08_local_remainder.py`): the symbol exists in the **uncommitted working-tree
  edit** to that file (the file shows `M` in `git status` at session start), not in the last commit —
  `git show HEAD:<path>` (which the file-content check reads) cannot see it. This is the same
  "pending external commit" situation as the CSV outputs below, not a phantom feature.
- **1 was T07 itself** — the only one that survived, exactly as the plan's §5.1 predicted.

**This correction is recorded, not hidden**: the CSV keeps both the raw first-pass verdict
(`verdict` column) and the corrected one (`corrected_verdict` + `correction_note` columns), so a reader
can audit the correction itself. All counts below use the corrected column.

## 3. Method validation — T07 control (required by the plan, run blind first)

```
git log --all -S"_draw_tier" -- openubem/semantic/imputation.py
```
Returns **nothing** — no commit, on any branch, ever added or removed that string in that file.
Cross-checked two more ways:
- `grep -n "_draw_tier" openubem/semantic/imputation.py` at HEAD → **no output** (also absent from the
  current working tree, not just history).
- The paired deliverable, `tests/test_draw_methods.py::TestDrawTierRouting` (53 test functions total in
  the file) **is** present and tracked (`git ls-files -- tests/test_draw_methods.py` → tracked).

This reproduces the plan's §5.1 instance exactly: implementation never committed, tests were.

**Control result: PASS.**

## 4. Verdict counts

| Verdict | Count | Check |
|---|---|---|
| PRESENT | 424 | |
| MOVED | 6 | |
| NEVER-COMMITTED | 14 | see §5 breakdown — only 1 is a governance concern |
| **Sum (= checkable population)** | **444** | matches §1 |
| UNCHECKABLE | 152 | |
| **Grand total** | **596** | matches §1 |

## 5. The 14 NEVER-COMMITTED entries, broken into the three reasons a "never committed" result occurs

**This breakdown is the actual answer to OPEN-36.** A raw NEVER-COMMITTED count conflates three very
different situations; only one of them is what T07 exposed.

### 5.1 Genuine governance gap — code claimed complete, never committed in any form (n = 1)

| Entry | File:line | Named artifact | Command |
|---|---|---|---|
| **T07** — *wire `_draw_tier` + registry + order (byte-identity re-proof)*, completed 2026-07-16 | `docs/docs_DONE/INPUTS/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md:849` | `_draw_tier`, `_draw_stratum_col_for` in `openubem/semantic/imputation.py` | `git log --all -S"_draw_tier" -- openubem/semantic/imputation.py` (empty) / `git log --all -S"_draw_stratum_col_for" -- openubem/semantic/imputation.py` (empty) |

This is the plan's own known instance (§5.1). **No second instance of this kind was found anywhere in
the 444-entry checkable population.**

### 5.2 Pending external commit — artifact sits on disk, untracked, by the project's own workflow (n = 12)

All twelve are `openubem/outputs/comparisons/*.csv` deliverables from the **current** round-1/2/3
no-compute-queue work (`docs_ACTIVE`, dated 2026-08-05/2026-08-06) — every one of them appears with a
`??` (untracked) marker in `git status` at the start of this very session. Per this project's own
convention ("git handled externally" — the user commits, agents never do), these are expected,
temporary, and not evidence of anything hidden:

`open06_mislabel_population.csv` (N07, N04), `open35_missing_input_census.csv` +
`open35_neither_population.csv` (N06), `open06_column_reproducibility.csv` +
`open06_column_reproducibility_diff_examples.csv` (N14), `open22_fixture_rule_breakdown.csv` (N02),
`open29_defect_status_trace.csv` (N01), `open34_subset_vs_fullcell.csv` (N05),
`open02_eio_inventory.csv` (M02), `open01_denominator_factors.csv` (M01),
`open28_t08_t20_join.csv` (M05), `open03_load_vintage_ratios.csv` (M03),
`open04_accuracy_by_commit.csv` (M04).

Exact command for any of these (example): `git log --all --oneline --follow --
openubem/outputs/comparisons/open01_denominator_factors.csv` → empty; file confirmed present on disk.

### 5.3 Self-disclosed ephemeral artifact — the entry itself says it was deleted on purpose (n = 1)

**T02** — *ashrae_90_1_2019.json construction table*, `docs/docs_main/docs_step-2-2/
PLAN_step-2-2-implementation.md:301`, completed 2026-06-10. Names `scripts/_build_test.py`, which is
absent from both disk and all git history:
`git log --all --oneline --follow -- scripts/_build_test.py` → empty.

Unlike T07, this is **not concealed**: the entry's own Artifacts line labels it
`` `scripts/_build_test.py` (temp, deleted after use) ``, and its Notes confirm *"deleted per R-2.2-8
after table built and verified."* The record discloses its own ephemerality at write time — it is a
mechanically-correct NEVER-COMMITTED result with a documented, benign reason, not a second instance of
the T07 pattern (a claim of completion whose substance turns out to be missing).

## 6. Scope actually covered, and what was not

- **Full population walked, not a subset.** All 596 entries across all 58 files in all four
  documentation roots were parsed and (where checkable) tested — this is the entire population as
  defined in §1, not a principled slice of it.
- **File-level check is exhaustive and reliable** over the 444 checkable entries — every named file is
  independently resolved by path, no proximity guessing involved.
- **Symbol-level check is a best-effort layer, not exhaustive.** It only tests symbols my
  clause-proximity regex actually extracted as candidates near a `.py` file mention. It is plausible
  that a symbol-level defect exists inside one of the 424 file-level-PRESENT entries that my extractor
  simply never proposed as a candidate (e.g. a symbol named in prose without backticks, or too far from
  its file mention to land in the same clause). No positive evidence of this was found, but it was not
  exhaustively ruled out either — reported as an unknown, not asserted absent.
- **File-artifact extensions covered:** `.py .json .csv .md .gpkg .parquet .yaml .yml .txt` under
  `openubem/`, `scripts/`, `tests/`. **Not covered:** front-end assets (`.mjs/.js/.ts`, used by the
  3D-visualization viewer's test suite) — any entry naming only such artifacts falls into UNCHECKABLE
  rather than being verified. 11 of the 58 files reference such artifacts (chiefly the
  3D-visualization arc); none of the 3D-viz entries checked above (via their `.py` companions) showed a
  T07-style gap, but the JS/TS side of that arc's own test claims was not independently verified here.
- **Data-file artifacts (`.json/.csv/.gpkg/.parquet/.md`) were checked at file-existence level only,**
  not at content/row/key level — a claim like "column X added to file Y.json" is confirmed only as
  "Y.json exists at HEAD," not that column X specifically is in it.

## 7. How-to-test criteria (plan §6)

- **(a) Verdict counts sum, both numbers printed.** PRESENT 424 + MOVED 6 + NEVER-COMMITTED 14 = 444 =
  checkable count; 444 + UNCHECKABLE 152 = 596 = total population. **PASS.**
- **(b) T07 control returns NEVER-COMMITTED.** **PASS** (§3).
- **(c) Every NEVER-COMMITTED verdict carries its exact `git log --all -S`/`--follow` command.**
  **PASS** — given in full in §5 above and in the `file_level_detail`/`symbol_level_detail` columns of
  the CSV for all 14.

## 8. Artifacts

- This report.
- `openubem/outputs/comparisons/open36_completion_record_sweep.csv` — one row per progress-log entry
  (596 rows + header), columns: `file, line, task_id, title, completed_date, verdict,
  file_level_detail, symbol_level_detail, pending_note, corrected_verdict, correction_note`. The raw
  first-pass `verdict` and the audited `corrected_verdict` are both kept, per §2.1.
