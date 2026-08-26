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
| X-04 / EU-03 | `LOCAL_PASS` | R3/R5/R7 all pass: 9 physics tests and 94 European tests were independently re-verified. |
| X-05 / EU-04 | `LOCAL_PASS` | All four S0 fixtures have an area-faithful equivalent envelope, independently read-back transmission coefficient, and a successful SFH EnergyPlus smoke test. Do not treat the equivalent mesh as a surveyed building form. |
| X-06 / EU-05/EU-07 | `LOCAL_PASS` | Controls are integrated with the S0 envelope: 20 C heating only, no cooling, all-convective 3 W/m2 gains, and `F_red_temp` scaling. |
| X-07 / EU-07 weather | `PARTIAL` | `cdsapi 0.7.7`, `pvlib 0.15.2`, `xarray 2026.7.0` installed. Live ERA5 fetch is blocked until `C:\Users\o_iseri\.cdsapirc` or equivalent CDS credential is configured. Do not read, print, commit, or log a secret. |

Your next independent implementation target is the next defined unblocked slice after S0: weather
registry preparation around the live-CDS block, then the remaining local campaign, score, and dossier
work in dependency order. Do not use CDS credentials as a reason to pause independent work.

## Superseding live status (2026-08-23T22:25:00Z)

## Latest superseding live status (2026-08-24T09:52:09Z)

The complete European suite is **161 passed in 18.52 s**. `EU-05` now audits heating-only IdealLoads, constant natural air, and all-convective gains across all 102 ES/GB/IT occupant-campaign rows. Invalid air inputs fail before IDF emission. France physical baseline row `FR.N.AB.10.Gen.ReEx.001.001` has `F_red_temp=1.0086438144755208`, above the current reduction range; it must remain fail-closed until `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-05_FR-Fred-temp_2026-08-24.md` is ruled. Do not clamp or alter it. This is local control-contract evidence only; retain the `EU-04` fractional-storey, `EU-06` chaining, and `EU-07` CDS blocks.

## Latest superseding live status (2026-08-24T09:47:31Z)

The complete European suite is **156 passed in 14.33 s**. `EU-08` now has a 5/5-tested, file-derived dependency-digest cache wrapper: it SHA-256 measures IDF, emitted schedule, and weather files and canonically includes EnergyPlus build identity, adapter configuration, and source commit. A cache hit also requires `eplusout.end`/`eplusout.sql` legacy completion, `status=success`, and an exact digest match; marker-only completion is invalid. This is local fixture-contract evidence only; do not submit a campaign or claim results. Preserve the existing `EU-04` fractional-storey authority, `EU-06` f>0 chaining, and `EU-07` CDS blocks. Evidence: `openubem/outputs/eu_evidence/EU-08/all_european_tests_after_dependency_digest_cache.log`.

## Latest superseding live status (2026-08-24T01:28:08Z)

`X-01`, `X-02`, `X-03`, `X-04`, `X-05`, `X-06`, and `X-08` are `LOCAL_PASS`.
The complete European suite is **154 passed in 14.10 s** after the EU-04 GEO-07 allocation foundation. `EU-04` is `PARTIAL`: it half-up rounds `n_Apartment`, allocates exact quotient/remainder dwelling totals across integral storeys, and places the ruled 6% unconditioned core outside TABULA conditioned plate only at density >=2 dwellings/storey. Three GB `SyAv` rows have non-integer `n_Storey` without an approved rounding rule; they are fail-closed and documented at `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md`. Continue independent work but do not emit their geometry/IDFs. `EU-09` is `PARTIAL`: local contracts cover G8.0–G8.16, including named-series peak magnitude/timing and the graded as-modelled EUI band plus geometry denominator identity. The fixed Table 17 P01–P12 matrix is exported at `content/eu_09_perturbation_matrix.csv`; its local cross-tab fails missing probes, a required failure that stays clean, or a required-clean checkpoint that turns dirty. P05 retains separate G8.12 assignment/value checkpoints and P12 requires all observed checkpoints clean. V8.c imports immutable fixed G8.1–G8.6/G8.10 bands from `openubem.validation.step8_bands`; G8.7 remains archetype-specific input. V8.d independently reads each archetype's own retained IDF: explicit Zone area, volume, and equivalent per-storey height yield integral storeys, and saved surfaces must identify that archetype; reused paths, swaps, missing fields, and mismatches fail. This is not retained campaign evidence; campaign artefacts remain pending. `EU-10` is `PARTIAL`: its read-only `eplusout.csv` extractor requires Date/Time, all four hourly J end-use variables, and exactly 8,760 non-leap calendar rows, then sends its annual/monthly/hourly series through the ruled weather-window and four-end-use closure contract. The dossier export requires exactly G8.0–G8.16 all passing at hard severity, measured campaign/result SHA-256 digests, and an explicit scope that distinguishes `local_fixture_contract` from `retained_campaign`. It does not read facility/service meters or add TABULA DHW to time series. Retained campaign artefacts and final dossier evidence remain pending. X-05 uses an explicitly
equivalent, not surveyed, S0 envelope that preserves every individual TABULA area and the
reduced `h_Transmission` target; the SFH heating-only EnergyPlus test has zero severe errors.
`X-07` is `PARTIAL`: `openubem/data/weather/weather_registry.json` is a deterministic
`RULED_NOT_PINNED` template, and `tests/test_eu_weather_registry.py` passes 6/6 offline checks
(secret-safe credential presence plus DR08 gates 1–4). It remains blocked only for real ERA5
retrieval, CDS-served licence capture, diary-window pinning, and DR08 gates 5–6, pending CDS
credentials and the acquired files. Start the next unblocked local slice; do not redo S0 merely to
create duplicate evidence.

`EU-06` is `PARTIAL`: `openubem.semantic.european_schedules` has a 7/7-tested external,
non-fractional `Schedule:File` path for the f=0 control, including annual 3 W/m2 conservation and
zero-presence-day accounting. Do not emit f>0 without an upstream ruled chaining convention; real
Step 7 input and saved-IDF assignment read-back remain outstanding.

`EU-08` is `PARTIAL`: `openubem.validation.european_campaign` has a deterministic ES/GB/IT
campaign plan (Q3=102 f=0 controls; Q4=408 f>0 rows) and a 5/5-tested dependency-digest cache
wrapper. Do not submit runs or report results: weather, final IDFs, real schedules, and
pre-registered gates are still required.

`EU-09` is `PARTIAL`: `openubem.validation.step8_gates` scores reproducibility, pre-submission,
MDD-derived meter, independent saved-IDF, warning-kind, named-series peak, and as-modelled
EUI/geometry artefacts. It is not a substitute for retained campaign evidence or the complete V8
coverage cross-tab.
The broader MVP work packages `EU-04` and `EU-05` remain `IN_PROGRESS` because their S1–S3 and
sampled-dwelling acceptance gates are still outstanding.

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
