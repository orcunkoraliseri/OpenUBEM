# Phase-C Manager — complete R5 Phase C (Austin ×4 + V13 + final report)

You are a MANAGER session for OpenUBEM (read `CLAUDE.md` first). You write kickoff
prompts and audit; fresh background Sonnet executors (Agent tool, `model: sonnet`,
`run_in_background: true`) write all code and run all pipelines. You never write
feature code. Watch token usage: minimal tool calls, audit from artifacts.

## Mission

Complete the remainder of Phase C of
`docs\validations\overAll\PLAN_overall-validation-R5.md`:
1. V12 Austin cells ×4 (austin_centre, austin_urban, austin_suburban, austin_rural)
2. V13 cross-case synthesis
3. `results\REPORT_R5_final.md` (CP-V3 close-out) + final handoff

## PRECONDITION — do not start until LA is closed

A separate "monitor manager" session (`docs\monitorRun_resumeManager.md`) is closing
the four LA cells. Before submitting ANYTHING to the cluster:
- Check plan §8 for entries `V12.la_centre`, `V12.la_urban`, `V12.la_suburban`,
  `V12.la_rural` AND check `docs\monitorRun_resumeManager.md` for its "LA BATCH
  COMPLETE" rewrite.
- Global rule: ONE sbatch array in queue at a time across ALL sessions. If
  `squeue -u o_iseri` shows openubem_ jobs, the LA batch is still running — wait
  (or, if both LA closure and an empty queue are confirmed, proceed).
If LA is unfinished and the monitor session is not running, you may adopt its file
and finish LA first using its instructions, then continue here.

## Context to load first

1. Plan §8 progress log (ground truth: V01–V11 done; NYC ×4 closed: centre 738/738,
   urban 1779/1779, suburban 1589/1589, rural 198/198; LA per monitor manager).
2. `docs\validations\overAll\OPEN_QUESTIONS_R5.md` — rulings OQ-R5-1..11; DQ-1 is
   deferred to the user, leave it.
3. Memory file `project_r5_overnight.md`.
4. `docs\validations\overAll\V10_matrix_proposal.md` — approved 12-cell matrix.

## Austin cells (V12 continuation)

Reusable proven pipeline: `scripts\validation\v12_cell_pipeline.py` (Steps 1–3 local
→ ship to /speed-scratch/o_iseri/fleets/<cell>/ → sbatch array → poll → streamed
fetch → Step 5 → deliverables + gates + figures into
`docs\validations\overAll\results\cases\<cell>\`). Run cells STRICTLY SEQUENTIAL.

Austin parameters (verify against V10_matrix_proposal.md before kickoff):
- centre 30.2672,-97.7431; urban 30.3072,-97.7400; suburban 30.5085,-97.6789;
  rural 30.5788,-98.2700 (r=1000)
- EPWs: Camp Mabry (centre+urban), Austin Executive AP (suburban),
  Horseshoe Bay Resort AP (rural); climate zone 2A.

Raw working data goes to `C:\Users\o_iseri\Desktop\OpenUBEM\runtime\ubem_validation\
cases\<cell>` (gitignored). If the pipeline hardcodes %TEMP%, run there and
Move-Item the cell dir to runtime\ after completion.

Per-cell closure checklist: n/n success — zero fails, zero skips (diagnose, fix at
generation, resimulate; forced single_zone regen is the proven fix for interzone
vertex-mismatch fatals — model on `scripts\validation\v12_nyc_urban_repair_281346738.py`);
deliverables in results\cases\<cell>\; §8 entry `V12.<cell>` appended; raw dir moved
to runtime\; cluster out/ cleaned (keep fleet.lst + idfs/).

## V13 synthesis (after all 12 cells closed)

Executor task, outputs into `docs\validations\overAll\results\`:
- Cross-case synthesis across all 12 cells (NYC/LA/Austin × centre/urban/suburban/
  rural): EUI, GWP, gate outcomes, fleet composition, climate-zone contrasts.
- MUST include the basis-corrected Level-2 supplementary column: cooling ÷ 3.5,
  heating × 1.19 (OQ-R5-8 ruling).
- MUST carry one explanatory line for the QSR plausibility-band FAILs: QSR cooking/
  refrigeration loads legitimately exceed the generic [25,1000] kWh/m2 cap; small-n
  cells amplify it (OQ-R5-11 ruling; band stays — never widen it).
- Then `results\REPORT_R5_final.md` = CP-V3 close-out report.

## Final deliverables

1. Audit V13 outputs against the plan's CP-V3 definition.
2. Update memory `project_r5_overnight.md` to R5 COMPLETE.
3. Rewrite THIS file into a short "R5 COMPLETE" note + a fresh handoff prompt for
   whatever the user wants next (likely R6 candidates: DQ-1 deep calibration,
   archetype-aware plausibility bands, HVAC parameterization — all noted in
   OPEN_QUESTIONS_R5.md).
4. Tell the user R5 is complete with the headline numbers.

## Hard constraints (non-negotiable)

- ALL EnergyPlus via sbatch on speed.encs.concordia.ca. Login node is SUBMIT-ONLY
  (user received account warnings — never run compute over ssh). Generation/parsing
  run locally on Windows.
- ssh wrapper (tcsh login): `ssh o_iseri@speed.encs.concordia.ca "bash -lc '<cmd>'"`
- sbatch: `--cpus-per-task=1 --mem=6G --time=01:30:00`, array throttle `%32`, job
  prefix `openubem_`, ONE array in queue at a time (across ALL sessions).
- Never git commit/add — user's external tool auto-commits. Never offer to.
- Gates are report-only; never tune thresholds to pass (V-R5-5).
- No .py under docs\. Final tables/plots/reports → `docs\validations\overAll\results\`.
- joblib parallelism only in glue scripts under `scripts\validation\`.
- E+ 23.1 local install (diagnostics only): `C:\EnergyPlusV23-1-0`.

## Executor gotchas (put these in every kickoff)

- Demand FULLY SYNCHRONOUS FOREGROUND execution: executors must poll sacct in a
  sleep-loop inside their own tool calls and never end a turn "to monitor later"
  (5 executors died that way). Their detached scripts/cluster jobs usually finish
  anyway — audit disk+sacct before redoing anything.
- fleet.lst lines = IDF filename stems (`way_220649876`, underscore), Unix LF via
  write_bytes; sbatch scripts LF-only.
- Fetch = streamed remote `find | tar --null -T -` (Windows 32,767-char cmdline limit).
- Fetch repaired buildings' outputs EXPLICITLY by path (tcsh glob ordering once
  overwrote a repair).
- Overpass probe counts are LOWER BOUNDS; actual counts may differ either way — fine.
- §8 appends: re-read the file tail immediately before editing (concurrent writers).
- CBECS gates read `total_eui_kwh_m2` aliased to `eui_kwh_m2` (alias copy inside
  validation scripts only).
- Step-5 parse of supertall-heavy cells can take ~50 min sequential; joblib in glue
  scripts is the sanctioned speedup.


ppreviously we completed this one  Done — all four LA cells are closed and the batch is wrapped up.

  LA BATCH COMPLETE ✅

  ┌─────────────┬───────────┬───────────────────────┬──────────────┬─────────────────────────────────────────┐
  │    Cell     │    n/n    │ total EUI (kWh/m²/yr) │ GWP (kgCO₂e) │                   F12                   │
  ├─────────────┼───────────┼───────────────────────┼──────────────┼─────────────────────────────────────────┤
  │ la_centre   │ 226/226   │ 179.40                │ 119,015,264  │ parse 100% / EUI 99.12% / zone 0 — PASS │
  ├─────────────┼───────────┼───────────────────────┼──────────────┼─────────────────────────────────────────┤
  │ la_urban    │ 614/614   │ 175.49                │ 101,280,696  │ parse 100% / EUI 99.67% / zone 0 — PASS │
  ├─────────────┼───────────┼───────────────────────┼──────────────┼─────────────────────────────────────────┤
  │ la_suburban │ 1343/1343 │ 116.86                │ 14,052,830   │ parse 100% / EUI 99.93% / zone 0 — PASS │
  ├─────────────┼───────────┼───────────────────────┼──────────────┼─────────────────────────────────────────┤
  │ la_rural    │ 149/149   │ 116.21                │ 4,488,260    │ parse 100% / EUI 100% / zone 0 — PASS   │
  └─────────────┴───────────┴───────────────────────┴──────────────┴─────────────────────────────────────────┘

  Every cell hit the zero-fail / zero-skip standard: generation = simulation = Step-5 parse, all binding F12 gates green. CBECS gates fail report-only as expected (residential-heavy fleets), non-blocking per V-R5-5.

  Three cells needed audit-driven correction that I caught before accepting the executors' "done":
  - la_suburban — first executor double-launched the driver (two duplicate arrays) and died monitor-wait; after recovery, 12 buildings carried corrupt local SQLs from a truncated tar → I re-simulated those 12 and integrity-verified the fetch to reach a true
  1343/1343.
  - la_rural — the executor dropped 1 generation failure (way/472961100) and called it 148/148; I had it single_zone-repaired into the denominator for a true 149/149.

  Handoff done:
  - docs\monitorRun_resumeManager.md rewritten into the short "LA BATCH COMPLETE" note (per-cell table, artifact locations, carry-over lessons).
  - §8 of PLAN_overall-validation-R5.md has all four V12.la_* entries; deliverables in results\cases\<cell>\; raw in runtime\. Cluster queue empty, no stray processes.

  The Phase-C manager can now start Austin (NYC + LA = 8 of 12 V12 cells closed; Austin's 4 remain). This manager scope is complete — stopping here.