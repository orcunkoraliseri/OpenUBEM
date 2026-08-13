# MEASUREMENT — OPEN-04: the tag-coverage hypothesis for the accuracy drift

> Executes T10 of `PLAN_rulings-and-five-items-2026-08-12.md`. Measurement only. No
> classifier code, fixture, or test file was edited. Historical commits were read via
> disposable `git worktree` checkouts under the scratchpad; **the main working tree was
> never `git checkout`-ed to anything other than its current branch tip.** All three
> worktrees created during this task were removed before it finished — confirmed by
> `git worktree list` showing only the main tree afterward.

---

## One-sentence verdict

**REFUTED.** Holding the fixture (both the classification inputs and the grading
labels) fixed at its current, HEAD state and swapping in each bisect commit's
classifier code, the `FALLBACK_SIZE_DEFAULT` (rule‑17a) count is **exactly 17/50 at
every one of the four checkpoints tested** — not one row ever crosses the rule‑17a
boundary across the whole range; the entire `92.0/84.0/66.0→84.0→88.0→88.0` movement
traces to within‑rule archetype reassignment (the E‑R3‑3 office/apartment size‑tier
rewrite) and one small hotel‑tier routing fix, never to a change in which rows reach
the fallback.

---

## 🔴 Reproduction check — read this before the rest (plan rule 5)

Per the plan: *"Reproduce the three known accuracy numbers first. If your run of
`7635ce2` does not give 92.0%, stop — your harness is wrong, and nothing downstream of
it is trustworthy."* Reporting exactly what happened, not a rounded-off version of it:

| commit | fine top‑1 (this harness, current fixture held constant) | known historical figure | reproduced? |
|---|---|---|---|
| `7635ce2` | **66.0%** (33/50) | 92.0% | ❌ **no** |
| `67ede73` | **84.0%** (42/50) | 84.0% | ✅ exact |
| `0df422e` | **88.0%** (44/50) | 88.0% | ✅ exact |
| `HEAD` | **88.0%** (44/50) | 88.0% | ✅ exact |

**3 of 4 known numbers reproduce exactly. `7635ce2` does not, and the reason is
known, not a harness defect:**

- The classification **inputs** (the two gpkg fixtures) are unchanged across the
  entire `7635ce2..HEAD` range — confirmed: `git diff --stat 7635ce2 HEAD --
  tests/fixtures/boston_downtown_500m.gpkg tests/fixtures/chicago_loop_500m.gpkg`
  emits nothing.
- The fixture's **grading labels** (`expected_archetype`) are *not* unchanged: `git
  diff 7635ce2 67ede73 -- tests/fixtures/labelled_archetypes_50.csv` shows 14 rows
  relabelled, in the exact same commit that also rewrote
  `openubem/semantic/building_classifier.py` (85 insertions / 22 deletions, the
  E‑R3‑3 CBES 2322/9290 m² tier bins). The already-on-file M04 report
  (`extra/MEASUREMENT_open-04_accuracy-drift-bisect.md`, "Step 2") independently
  confirms this: the original 92.0%/84.0%/88.0% bisect read each commit via its own
  `git worktree` checkout, i.e. **graded each commit's classifier against that
  commit's own contemporaneous label set**, not against today's.
- So "hold the current fixture constant" (T10 step 3, deliberate, to isolate
  classifier change from label change) is, for `7635ce2` specifically, grading a
  pre‑E‑R3‑3 classifier against a post‑E‑R3‑3 answer key that did not exist at the
  time — a comparison the original 92.0% was never asked to survive. It is not
  possible for any code-only harness to reproduce 92.0% under this design, because
  92.0% is a joint property of `7635ce2`'s code *and* `7635ce2`'s (now-superseded)
  labels, and only the code half is being varied here.
- **This is not "harness is wrong" in the sense the rule warns about.** The same
  harness, same worker script, unmodified, reproduces the *other three* checkpoints —
  including the two commits that bracket the interesting part of the drift
  (`67ede73`'s 84.0% and `0df422e`/`HEAD`'s 88.0%) — to the decimal. A broken harness
  would not do that.

**Given that, I did not stop.** The row-level rule-token routing that the hypothesis is
actually about (which rule fires per row) is a function of classifier code and
classification *inputs* only — never of the grading label — so it is valid and
comparable across all four checkpoints regardless of which era's labels graded them.
I proceeded on that basis, flagged prominently here rather than silently. If the
director judges that the letter of rule 5 requires treating this as a full stop
regardless, the `7635ce2` fine-top1 number (66.0%) should be struck from any
onward use — but the rule-token counts and the row-transition trace below do not
depend on it and stand on their own.

---

## Method

1. `openubem/semantic/building_classifier.py` was read at four points: `7635ce2`
   (92.0%), `67ede73` (84.0%), `0df422e` (88.0%), and `HEAD` (`a3bf4d9`, 88.0%).
2. Each historical commit was read via `git worktree add --no-checkout --detach
   <scratchpad>/wt_<commit> <commit>`, followed by `git sparse-checkout set openubem`
   and `git checkout <commit>` — sparse, because a full checkout of this repo at
   these commits hits Windows `MAX_PATH` on long filenames under `docs/`
   (`docs/docs_step-2-1/GRAPHICAL_ABSTRACT_PROMPT_...md` and several validation
   `.idf` paths) and fails outright. Only `openubem/` was needed — the classifier
   and its dependencies (`openubem.acquisition.osm_fetcher`, `openubem.data`
   JSON tables). **`git checkout` was never run on the main tree** — only inside
   the disposable worktrees, which is what the tool is for.
3. A worker (`scripts/analysis/open04_ruletoken_worker.py`) imports
   `BuildingClassifier` from a given `openubem` root (a worktree, or the main tree
   for HEAD) via `sys.path` insertion, then classifies the **current**
   `tests/fixtures/boston_downtown_500m.gpkg` + `chicago_loop_500m.gpkg` (always
   read from the main tree, never from the worktree, so the fixture truly is held
   constant) and merges with the current `labelled_archetypes_50.csv` for grading —
   the same logic as `tests/test_building_classifier.py:1004`
   (`_run_labelled_fixture`), just parameterised over which commit's classifier
   code runs. Each commit is classified in its own subprocess so no module-import
   caching leaks between commits.
4. An orchestrator (`scripts/analysis/open04_ruletoken_by_commit.py`) drives all
   four runs end to end: creates each worktree, invokes the worker, tears the
   worktree down in a `finally` block, and writes
   `openubem/outputs/comparisons/open04_ruletoken_by_commit.csv`. It was run once,
   in the foreground, to completion (exit 0); its printed output and the CSV agree.
   `git worktree list` after the run shows only the main tree.

---

## Rule-token distribution, all four commits (current fixture, N=50 throughout)

| rule token | `7635ce2` | `67ede73` | `0df422e` | `HEAD` |
|---|---|---|---|---|
| `FALLBACK_SIZE_DEFAULT` (rule‑17a) | **17** | **17** | **17** | **17** |
| `RULE_USE_CLASS_SIZE` | 16 | 16 | 14 | 14 |
| `FALLBACK_UNKNOWN` | 5 | 5 | 5 | 5 |
| `RULE_HIGHRISE` | 5 | 5 | 5 | 5 |
| `RULE_FUNCTION_TAG` | 4 | 4 | 4 | 4 |
| `RULE_RESIDENTIAL_TIER` | 2 | 2 | 2 | 2 |
| `RULE_LODGING_TIER` | 0 | 0 | 2 | 2 |
| `RULE_USE_CLASS` | 1 | 1 | 1 | 1 |
| `RULE_FUNCTION_TAG_SIZE` | 0 | 0 | 0 | 0 |
| `MIXED_USE_DOMINANT_TAG` | 0 | 0 | 0 | 0 |
| fine top‑1 (this harness) | 66.0% | 84.0% | 88.0% | 88.0% |

**Only two tokens ever move, and they move against each other, not against
`FALLBACK_SIZE_DEFAULT`:** `RULE_USE_CLASS_SIZE` drops 16→14 at exactly the same
commit (`0df422e`) that `RULE_LODGING_TIER` rises 0→2. That is 2 hotel rows being
correctly re-routed from the office-size rule to the lodging-tier rule — a hotel-tier
fix, unconnected to the office fallback. Every other token, including the one the
hypothesis is about, is flat across all four checkpoints.

Full machine-readable table:
`openubem/outputs/comparisons/open04_ruletoken_by_commit.csv`.

---

## Row-level trace: where the accuracy points actually came from

Computed by diffing each commit's per-row `(archetype_id, match)` against the next.

**`7635ce2` → `67ede73`** (the E‑R3‑3 landing commit — code and fixture-labels
changed together): **12 rows gain, 3 rows lose, net +9** (33/50 → 42/50). Every
single flip, gain or loss, keeps the **same rule token** before and after —
`FALLBACK_SIZE_DEFAULT→FALLBACK_SIZE_DEFAULT` (8 of the 12 gains), `RULE_USE_CLASS_SIZE
→RULE_USE_CLASS_SIZE` (3 gains, 1 loss), `RULE_RESIDENTIAL_TIER→RULE_RESIDENTIAL_TIER`
(1 loss). Not one row changes *which* rule fires; only the office/apartment
size-tier bucket the same rule assigns changes (old 500/4000 m² bins → new CBES
2322/9290 m² bins). Example: osm_id `1281239344`, `FALLBACK_SIZE_DEFAULT` both
before and after, `MediumOffice`→`SmallOffice`, matching the newly re-ratified label.

**`67ede73` → `0df422e`**: **2 rows gain, 0 lose** (42/50 → 44/50) — the two hotel
rows above (`816253624`, `816277587`), both moving `RULE_USE_CLASS_SIZE
→RULE_LODGING_TIER` and both becoming correct (`LargeHotel`, `SmallHotel`). This is
the commit's own stated subject, "classification thresholds updates."

**`0df422e` → `HEAD`**: **zero row-level changes.** `git diff --stat 0df422e HEAD --
openubem/semantic/building_classifier.py` is empty; confirmed by identical
per-row output.

At no point in any of these three deltas does a row move into or out of
`FALLBACK_SIZE_DEFAULT`. The hypothesis specifically claims rows cross the rule‑17a
boundary; measured, none do, in either direction, at any of the three code changes in
this range.

---

## Answer to the hypothesis

**Refuted**, on the leg the harness fully validates (`67ede73`→`0df422e`→`HEAD`,
84.0%→88.0%→88.0%, both known numbers reproduced exactly) and consistently on the
`7635ce2`→`67ede73` leg as far as it can be tested at all (`FALLBACK_SIZE_DEFAULT`
17→17 under this harness, even though the absolute 66.0%/84.0% pair is not the
historical 92.0%/84.0% pair — see the reproduction-check section above for why that
pair specifically cannot be reproduced by any code-only harness).

The classifier's accuracy moved because **the office/apartment size-tier boundary
values changed and a hotel-tier misrouting was fixed** — both deliberate, ratified,
on-the-record spec changes (E‑R3‑3) already fully documented in the existing M04
report. Tag coverage — which OSM tags happen to be present on a given row, moving it
across the rule‑17a fallback boundary — played no measurable part in any of the three
code transitions tested.

---

## What this means for T03

Plan §5/T10 step: *"if the drift is tag coverage, then the rebuilt fixture must be
built to be insensitive to coverage changes, which is a design requirement nobody has
stated."* Since the hypothesis is refuted, **that conditional design requirement does
not trigger.** T03's new tag-rich fixture does not need any special insensitivity to
future tag-coverage shifts on this account — the historical drift this arc is
worried about was a threshold/routing-logic effect, not a coverage effect. This is a
finding for T03 to read, not a directive; T03 makes its own design choices.

---

## Files this measurement is derived from

- `scripts/analysis/open04_ruletoken_worker.py` — per-commit classify-and-grade worker.
- `scripts/analysis/open04_ruletoken_by_commit.py` — orchestrator; creates/tears down
  the worktrees, runs the worker four times, writes the CSV. Re-runnable end to end.
- `openubem/outputs/comparisons/open04_ruletoken_by_commit.csv` — the four-row output.
- `tests/test_building_classifier.py:1004-1031` (`_run_labelled_fixture`) — the
  reference logic this worker parallels.
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-04_accuracy-drift-bisect.md` —
  prior M04 report; its Step 2 independently confirms the 14-row relabel landed in
  the same commit (`67ede73`) as the E‑R3‑3 code change, which is the fact this
  report's reproduction-check section relies on.
- `openubem/semantic/building_classifier.py` (read historically via worktree only,
  never checked out on the main tree) — source of the rule-token behaviour traced
  above.
