Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\openings\implemenation\PLAN_close-all-2026-08-19.md.
Execute T03 through T05 in order. Stop at CP-2, append one progress-log entry per completed task
under §8 of that doc, and report before doing anything else.

Do not propose alternatives -- execute the plan. If the plan is ambiguous, STOP and quote the conflict.

== HARD RULES (violating any of these invalidates the run) ==

1. NEVER run compute on the login node (speed-submit2 / speed.encs.concordia.ca). No srun, no
   `ssh ... python`. ALWAYS `sbatch --array`, fire-and-forget, then read the output file. The login
   node is for mkdir, scp, tar, squeue, sacct ONLY.
2. The remote login shell is tcsh. Bash syntax sent over bare ssh SILENTLY FAILS -- it returns a
   clean wrong answer, not an error. Always go through the _ssh() helper
   (scripts/cluster/t08_harvest_results.py:104), which wraps in `bash -lc`. Never send a bare command
   string. This helper was fixed on 2026-08-19 for two faults (a command-length limit and a
   Windows-only CRLF-on-stdin bug); use it, do not reimplement it.
3. NEVER background a command and then pause waiting for a notification. It will never wake you.
   Foreground only. Poll on disk artifacts.
4. NEVER touch cluster jobs belonging to other projects -- specifically job 1266911 / 4J_s4_pe.
5. NEVER run a git write command. Git is handled externally. Read-only git only.
6. Do NOT edit: the register (INVESTIGATION_open-items-register.md), docs/PROJECT_CHECKLIST.md, the
   director prompt, scripts/validation/v12_cell_pipeline.py, root main.py, or anything under
   docs/docs_DONE/, docs/docs_main/, docs/docs_stepN/. No .py files under docs/, ever.
7. You do NOT publish a fleet figure anywhere. You compute it and report it. The director publishes.
8. No code comments unless the surrounding file already uses them. All .png outputs go to
   openubem/outputs/ (flat).

== T03: THE SEEDING STEP THE PLAN DOES NOT SPELL OUT -- DO THIS FIRST ==

open48_fleet_run3.py has a _preflight() that REFUSES to launch unless every one of the 12 cells
already has a seeded 01_buildings.gpkg under %TEMP%/ubem_validation/<subdir>/.

This is not a nuisance check. It is what makes the re-run a single-variable, code-only comparison.
With the cache seeded, step1_fetch loads from disk (v12_cell_pipeline.py:138-141) instead of
re-fetching OpenStreetMap, so geometry is byte-identical to the run behind the published 157.1 and
EVERY delta is attributable to code. Re-fetching would mix an input change into a measurement of a
code change and the resulting number would be uninterpretable, not merely wrong.

So, before running anything:

  a. COPY (never move -- the frozen set is also evidence for OPEN-55) each cell directory's
     01_buildings.gpkg from  %TEMP%/ubem_validation/open48_refleet3/<cell>/
     to                      %TEMP%/ubem_validation/open48_refleet4/<cell>/
  b. Verify each copy against this manifest, which the director computed on 2026-08-19.
     Any mismatch = STOP and report; do not proceed on a mismatched input.

     e8b6e0f3a534831a96eeb9acc9f444c4  nyc_centre
     eb2d869e49a3da35f08dac688b652e74  nyc_urban
     1198ed01bfd3b4463e50da0ae39d8e27  nyc_suburban
     8fa93c2bb15cd9f15f1c9775f884cf49  nyc_rural
     7d670eef5af6139d9cde6ee7a469cf67  la_centre
     86058c6c7838ae9b8c24885d9f4cec95  la_urban
     2385533cda821dc70e555fa5756a391f  la_suburban
     6249e2e5e69e5a72ea7a043e70eca73b  la_rural
     83963b448810750e96ba72849f6be023  austin_centre
     314ed65574815dde04ffdacf208824e3  austin_urban
     2342b37802a96f071565344425ae90a4  austin_suburban
     366e8c6ba20cc5445a8f18a10683ded8  austin_rural

  c. Create scripts/validation/open48_fleet_run4.py as a copy of open48_fleet_run3.py with
     OUTPUT_SUBDIR = "open48_refleet4" and its own LOG_DIR. Keep these PINNED values:
       MAX_PARALLEL = 4   <- NOT 6. Run 2 used 6; six concurrent cells saturated the SSH link to
                             speed-submit2 and killed la_rural on an scp and austin_urban on a
                             squeue poll. Do not "optimise" this back up.
       STAGGER_S = 240
       POLL_S = 30
     Submit in waves under the Speed ~20k task cap.
  d. Confirm _preflight() PASSED and one real task is observed RUNNING before you leave the
     submission unattended. Record every job ID.

== T04 / T05 ==

Follow the plan. Two things it is worth being explicit about:

- The pooled figure is total simulated energy / total simulated floor area over all SUCCESSFUL
  buildings (OPEN-43). It is NEVER a mean of cell means.
- Record the FAILURE count and its causes per cell, beside the success count. A restatement computed
  over a silently smaller population is the exact defect OPEN-43 named. If a cell loses a meaningful
  number of buildings, say so; do not quietly pool over whatever survived.

== HONESTY INSTRUCTION ==

If the run fails, partially fails, or produces a figure that looks wrong, report that plainly and
STOP. Do not retry blind -- three earlier attempts at the related acceptance test were each lost to
a blind retry. A failed or inconclusive run reported honestly is worth more to me than a clean
number I cannot trust. Several executors on this project have reported against their own interest
and were right to.

== ADDED BY THE DIRECTOR AT CP-1, 2026-08-19 -- ONE EXTRA THING T04 MUST RECORD ==

CP-1 passed: the acceptance test came in at 0 divergences against a pre-fix baseline of 71, so
OPEN-55 and OPEN-49 are closed and T03 proceeds. But the director's audit of that run found
something the acceptance test was not looking for, and T04 must measure it fleet-wide.

In nyc_suburban the equipment screen worked -- Unknown buildings now draw LESS equipment energy
than classified ones (median 37.5 vs 43.4 kWh/m2). Yet Unknown buildings still finish at
1.7x classified overall: median total 349.4 vs 202.8 kWh/m2. The gap has MOVED, not closed.
It is now driven by domestic hot water (+61.0), heating (+41.1), lighting (+22.7) and
cooling (+20.5) kWh/m2 -- not equipment.

Unknown buildings are 18.3 % of that cell and they occur in every cell, so this lifts the pooled
fleet figure by an amount nobody has measured. Registered as OPEN-59.

In T04, in addition to everything the plan already asks for, report per cell and pooled:
  a. the count and floor-area share of OpenUBEMUnknown buildings,
  b. median total EUI for Unknown vs classified buildings,
  c. the same split across heating / cooling / lighting / equipment / dhw,
  d. the pooled fleet figure recomputed with Unknown buildings EXCLUDED, alongside the real
     pooled figure. Report both. Do NOT publish either; the real pooled figure remains the
     headline and the exclusion is a diagnostic only, to size OPEN-59.

Do not fix OPEN-59. Measure it. This is a measurement task and a fix inside it would confound
the restatement -- which is the exact defect the frozen-input rule above exists to prevent.
