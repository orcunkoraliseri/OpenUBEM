# MEASUREMENT — OPEN-33: archiving rule written, dead-path re-sweep, 2026-08-12

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-item-sweep-2026-08-12.md`, T07.
> **Scope:** (a) write the ruled-obligatory archive-citation-sweep rule where the next person
> archiving an arc will meet it; (b) re-run the dead-path sweep over live documents and compare
> against the 2026-08-06 baseline (58 dead paths / 23 documents / 8 arcs). Measurement only —
> repairs limited to `docs/docs_ACTIVE/openings/` per the plan's hard rule.

---

## (a) The rule, and where it was written

Appended to the **documented head section** of `docs/PROJECT_CHECKLIST.md`, directly beneath the
existing 2026-08-06 migration-map table (after "Tracked as **OPEN-33** in the open-items
register.", before the `---` that closes the head section). `git diff --stat` on that file shows
`1 file changed, 10 insertions(+)` — an addition only, no line inside the file's journal blocks
touched.

The text added:

> **🔴 Archiving rule — ruled obligatory 2026-08-09, written here 2026-08-12 (OPEN-33).** Archiving
> an arc into `docs_DONE/` is **not finished** until every citation pointing into it, from every
> live document, has been swept and repaired. Resolve stale citations **by filename, not by path
> rewriting** — four of the 58 originals were renamed by their own move (gained a `DONE_`/`DONE-`
> prefix or were re-nested under a new `DONE/` folder), so a straight prefix substitution misses
> them; matching on the (possibly `DONE_`/`DONE-`-stripped) filename finds them instead.
> **Standing exclusions**, unchanged: `docs_DONE/` arc records, `docs_main/` specs, and
> `docs_TODO/layoutgenerator/` are never edited to chase a citation — they are resolved through the
> migration table above instead. **Measured cost: ~30 minutes per archive.**

## (b) Re-sweep — method

Script: `scripts/analysis/open33_dead_path_sweep.py` (throwaway analysis script, not under
`docs/`). Interpreter: `./.venv/Scripts/python.exe`.

**Live document set scanned** (per T07's How, step 2): every `*.md` under `docs/docs_ACTIVE/`,
`docs/docs_EXPLANATION/`, `docs/docs_REPORTS/`, plus `docs/PROJECT_CHECKLIST.md` — **59 files**
(60 momentarily, while the non-vacuity control file existed — see below).

**Extraction.** Two passes per file: (1) every single-backtick span containing `docs/` is taken in
full between backticks — this is how almost every citation in this corpus is written, and taking
the whole span (rather than a lazy per-character regex) is what makes internal dots in filenames
(e.g. `PLAN_step-2.5-oq7-labelled-fixture.md`) resolve correctly instead of truncating at the
first `.`; (2) for `docs/`-mentions outside backticks (fenced code blocks, mainly), the match runs
to the **last** valid extension on the line before a delimiter, which is the same fix applied to
the un-backticked case. A trailing `:123`, `:123-456` or `:123,456,780-790`-style line reference is
stripped. Candidates containing `*`, `{`, `}`, `<`, `>`, or `..` are dropped as **non-literal**
(glob patterns, brace-expansions, `<placeholder>` template slots, or `NN..MM`/ellipsis shorthand —
none of these are real paths a filesystem check could ever resolve, and treating them as citations
would manufacture false dead-path counts).

**Resolution.** Direct check against disk first; on failure, resolve **by filename** against an
index of every file under `docs/`, comparing basenames with any leading `DONE_`/`DONE-` prefix
stripped from both sides — this is the mechanism the rule above requires, and it is what the
2026-08-06 sweep's own four renamed files needed.

**`new_since_2026-08-06`.** No CSV survives from the 2026-08-06 sweep (only the prose count in
`PROJECT_CHECKLIST.md`), so novelty is re-derived from git rather than assumed: commit `9270ac7`
("docs: update openings investigation register, measurement records, and comparison tables",
2026-08-05 21:44 local — the commit that introduced the migration-map table itself, and the commit
the checklist's own "added 2026-08-06" line refers to) is the baseline snapshot. A citing file
absent from that commit is wholly new; for a citing file present then, a `cited_path` string not
found verbatim in that historical revision of the file is a new citation.

## Scanner control (non-vacuity)

The real scan (below) returns 3 dead paths, not 0, so the mandatory zero-case control does not
strictly apply — but it was run anyway, because all 3 real hits turned out to be forward
references inside a plan doc's own file-layout table (see next section), which raised the
question of whether the scanner could detect a genuine broken citation at all. A scratch file
(under `docs/docs_ACTIVE/openings/extra/`, name prefixed `_SCRATCH`, deleted immediately after
this control and not part of any deliverable) was created containing one deliberately broken
citation, an inline mention of a target filename (`DOES` + `_NOT_EXIST_control_zzz.md`) that does
not exist anywhere in the repository, written as a plain `docs/docs_ACTIVE/openings/extra/…` path
inside the scratch file. Re-running the sweep with the scratch file present raised the dead count
from 3 to 4, with the new row identifying exactly that file and exactly that broken path,
`resolved_via=none`. The scratch file was then deleted, and a final re-run (after this report
itself was written) confirms the count returns to 3 with no trace of the control row.

## Results

**2026-08-06 baseline (from `PROJECT_CHECKLIST.md`'s own prose, not re-derivable as a CSV):** 58
dead paths, 23 live documents, 8 arcs.

**2026-08-12 re-sweep, final state (scratch control removed, this report itself on disk and
re-scanned):** **279 total path citations extracted, 4 dead rows, pointing at only 2 distinct
missing files, all new since 2026-08-06.**

The 4 rows (recomputed directly from the final CSV, not carried from an earlier run):

| citing_file | cited_path | why dead |
|---|---|---|
| `PLAN_five-item-sweep-2026-08-12.md` | `docs/docs_ACTIVE/openings/extra/FIX_open-13_utci-forwards.md` | T03+T04's deliverable — not yet written by that parallel task as of this scan |
| `PLAN_five-item-sweep-2026-08-12.md` | `docs/docs_ACTIVE/openings/extra/FIX_open-26-29_polish-and-fatal-tests.md` | T05+T06's deliverable — not yet written by that parallel task as of this scan |
| `MEASUREMENT_open-33_archiving-rule-and-resweep.md` (this report) | `docs/docs_ACTIVE/openings/extra/FIX_open-13_utci-forwards.md` | same target, cited a second time in this report's own results table above |
| `MEASUREMENT_open-33_archiving-rule-and-resweep.md` (this report) | `docs/docs_ACTIVE/openings/extra/FIX_open-26-29_polish-and-fatal-tests.md` | same target, cited a second time in this report's own results table above |

Two earlier states, superseded by the numbers above and recorded here only for the record: (1) at
the very first sweep run this session, `MEASUREMENT_open-42_placeholder-and-fleet-impact.md`
(T01+T02's deliverable) was also dead; a re-run minutes later found it resolved, because a
parallel executor finished writing it while this task was in progress; (2) the run immediately
after this report was first drafted counted 3 dead paths, before this report's own results table
(quoting `FIX_open-13`/`FIX_open-26-29` by name) was itself re-scanned as a fourth and fifth
citing occurrence of the same two missing files.

**None of the 4 is an archiving defect.** Both missing targets are the plan document's own
`§2. File layout` table entries, listing paths that *other, still-running* tasks in this same plan
are expected to create; this report's own results table above cites them a second time only
because it is discussing that fact. They are forward references to sibling deliverables, not stale
citations into an archived arc, and they will resolve on their own once T03–T06 finish — no repair
is applicable, and none was made. **Zero genuine dead-path citations were found against the
2026-08-06 baseline's own definition of the problem** (a citation into content that has moved or
been archived without the citation being updated). Per the plan's hard rule, this outcome is
reported as what it is — a found-clean re-sweep, evidenced by the non-vacuity control above, not
assumed clean.

**Comparison to the 58/23/8 baseline:** not a regression — 0 archiving-class dead paths now vs.
58 then, because the 58 were fixed at the time (the 2026-08-06 sweep repaired
`docs_EXPLANATION/`/`docs_REPORTS/` in place and left everything else resolvable through the new
migration table) and no new archiving event has happened since. Six days of heavy documentation
work in `docs/docs_ACTIVE/openings/` produced ~270 new path citations, all of them correctly
pointing at their (already-migrated) `docs_DONE/` targets — the discipline the rule in (a) asks
for is, on this evidence, already being followed by whoever has been writing these documents.

## Repairs made

None. `docs/docs_ACTIVE/openings/` — the only directory this task had authority to repair — carried
zero dead paths outside the three sibling-task forward references, which are not repairable
(the fix is the other tasks finishing, not an edit here).

## Deliverable

`openubem/outputs/comparisons/open33_dead_path_sweep_2026-08-12.csv` — columns `citing_file,
cited_path, resolves, resolved_via, arc, new_since_2026-08-06`. ~278 rows (one per unique
`(citing_file, cited_path)` pair found across the 60-file live-document set, which now includes
this report itself; the exact count moves by ±1 with incidental prose edits to this report and is
not load-bearing — what is stable across every re-run in this task is **4 dead rows / 2 distinct
missing targets**, both sibling in-flight deliverables).
