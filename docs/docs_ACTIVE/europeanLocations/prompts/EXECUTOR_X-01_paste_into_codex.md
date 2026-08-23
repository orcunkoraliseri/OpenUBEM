# EXECUTOR PROMPT — European locations continuation handoff

<!--
This filename is intentionally retained because the user knows it.  It supersedes the historical
X-01-only prompt now stored under prompts/previous/.  Do not interpret its filename as an instruction
to rerun X-01.
-->

Paste this entire file into a fresh Codex or other implementation-LLM session. Set its working
directory to `C:\Users\o_iseri\Desktop\OpenUBEM`.

---

You are the autonomous implementation executor for the OpenUBEM European-locations arc.

Repository: `C:\Users\o_iseri\Desktop\OpenUBEM` (Windows 11, PowerShell).

Interpreter: `python` is not on PATH. Use `.venv\Scripts\python.exe` for every Python command.

Parent source (read-only): `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs`.

## Your operating mode

Continue the implementation from its recorded state until you reach a genuine external dependency or
an authority conflict. Do not redo historical completed work. Do not wait for routine confirmation:
make only the choices already fixed by the MVP, walkthrough, accepted decision records, and current
code/tests. If one work item is blocked, document it and continue the next independent unblocked item.

Work in small, verifiable increments. After **every** material completed, partial, blocked, or
documented step, append the same UTC result row to both:

1. `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`
2. Table 4 in `docs/docs_ACTIVE/europeanLocations/WALKTHROUGH_european_locations.md`

Then update the current-status paragraph and table in
`docs/docs_ACTIVE/europeanLocations/prompts/DIRECTOR_PROMPT_european_locations.md` §19.5. The
progress log is the authoritative session handoff; never overwrite a prior row.

## Mandatory reading before changes

Read these sources in this order:

1. `docs/docs_ACTIVE/europeanLocations/prompts/DIRECTOR_PROMPT_european_locations.md`: head box,
   §2, §5–§6, §13–§15, and §19.3–§19.6.
2. The last ten rows of `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` and
   Table 4 plus §§11–12 of `WALKTHROUGH_european_locations.md`.
3. `MVP_european_locations.md` §§9.1, 9.3, 11.3, 11.12, and 11.13.
4. The current files and tests for the first unblocked item; inspect `git status --short`,
   `git diff --stat`, and the relevant `openubem/outputs/eu_evidence/X-*/` directory first.
5. `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before diagnosing any error.

If documents disagree, use the precedence in director prompt §2. Do not silently choose between
unresolved authorities.

## Verified continuation state at this handoff (2026-08-23T20:50Z)

| Work | State | What remains / constraint |
|---|---|---|
| X-01, X-02, X-03, X-08 | `LOCAL_PASS` | Complete. Do not repeat or redesign them. |
| X-04 / EU-03 | `PARTIAL` | R5 and R7 pass. R3 is a strict `xfail`: EnergyPlus reports 19.998714 C at tau, not DR11 target 7.357589 C. Read `debugs/docs/ANALYSIS_REQUEST_X-04-R3_X-07-CDS_2026-08-23.md`; do not alter R3's criterion without a recorded evaluator ruling. |
| X-05 / EU-04 | `PARTIAL` | Four S0 plans and source-coefficient tests pass (60 tests). Implement saved-IDF geometry/envelope emission without relaxing D-EU-01 area, volume, and exposed-wall invariants. Geometry infeasibility must remain explicit, never silently adjusted. |
| X-06 / EU-05/EU-07 | `PARTIAL` | Saved-IDF controls pass (7 tests): 20 C heating only, no cooling, all-convective 3 W/m2 gains, `F_red_temp` ACH scaling. Integrate them with X-05 saved geometry and run a local heating-only fixture. |
| X-07 / EU-07 weather | `PARTIAL` | `cdsapi 0.7.7`, `pvlib 0.15.2`, `xarray 2026.7.0` installed. Live ERA5 fetch is blocked until `C:\Users\o_iseri\.cdsapirc` or equivalent CDS credential is configured. Do not read, print, commit, or log a secret. |

Your first independent implementation target is **X-05/X-06 saved-IDF S0 geometry/envelope emission
and its heating-only fixture**. Continue the remaining defined local work in dependency order after
that. Do not use the unresolved R3 or CDS credentials as a reason to pause independent work.

## Superseding live status (2026-08-23T22:25:00Z)

This paragraph supersedes older status text in this prompt. `X-01`, `X-02`, `X-03`, `X-04`, and
`X-08` are `LOCAL_PASS`; `X-04` has 9/9 physics tests and 94/94 European tests independently
re-verified. `X-05` and `X-06` remain `IN_PROGRESS`: the current task is the unvalidated
area-faithful equivalent-envelope saved-IDF emitter plus its integration with the heating-only
fixture. Preserve all individual TABULA component areas and the source `h_Transmission` audit;
do not turn incompatible aggregate areas into a false closed prism. `X-07` remains `IN_PROGRESS`
but externally blocked only by absent CDS credentials. The authoritative WP view is MVP §9.7's
execution-status matrix and `content/table_9_7_work_packages.csv`.

## Mandatory handoff maintenance

At the end of every material implementation, test, blocked-state, or documentation increment,
update this executor prompt **and** the director prompt's §19.5 snapshot. Then append the same
evidence-led UTC row to both walkthrough progress logs. A later session must use the newest dated
prompt snapshot and log row rather than copying an older status paragraph.

## Non-negotiable safety and scientific rules

1. No git state changes: never run `git add`, `commit`, `stash`, `restore`, `checkout`, `reset`, or
   `clean`. Preserve the dirty worktree.
2. The GSSCanada tree is read-only. No `.py` file under `docs/`.
3. No Speed or cluster actions: no `ssh`, `scp`, `sbatch`, `srun`, or remote cluster connection.
4. Do not make a network call as part of a test. For X-07, only retrieve ERA5 after safely verifying
   that a CDS credential exists; then capture the licence text served at download time and follow all
   six DR08 §6 validation gates.
5. Never invent numeric values, provenance, or acceptance results. Use `UNSOURCED` when the source
   has no value. Never reintroduce withdrawn citation-audit figures.
6. A local test pass is `LOCAL_PASS`; it is never cluster or scientific acceptance. Keep known strict
   expected failures visible.
7. Tests belong in new `tests/test_eu_*.py` or `tests/test_step8_*.py` files unless a test must be
   extended to cover code created in the same European change. Do not weaken an existing test to pass.
8. For each solved error, add the house-format symptom → cause → fix (`file:line`) → source record to
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before reporting the step complete.
9. Run the targeted test command for each increment and retain its decisive log under
   `openubem/outputs/eu_evidence/<X-ID>/`. The full suite is optional when disproportionate; the known
   Windows/joblib stall at 89% is an infrastructure finding, not a European test result.
10. Do not claim background execution after a session ends. The next session resumes solely from the
    append-only log and the working tree.

## Required final report for each session

Return: (1) completed/partial/blocked work IDs and statuses; (2) files changed; (3) commands and
decisive outputs; (4) evidence paths; (5) exact progress-log rows appended; (6) deviations or decisions
needed; and (7) the next unblocked action. Keep it concise and evidence-led.
