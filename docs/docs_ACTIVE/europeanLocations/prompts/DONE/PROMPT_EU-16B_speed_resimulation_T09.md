# `EU-16B` — Executor prompt: resimulate the four districts on Speed, harvest, rebind (T09)

- **Arc**: European locations × Step 8. **Plan**: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- **Order**: **after stop-and-report 2 has been answered by the owner with an explicit instruction to submit.**
- ✅ **AUTHORISED 2026-08-30.** Owner's authorising sentence, verbatim: *"oui, autorise la soumission Speed
  pour T09"* (owner, 2026-08-30, in reply to the manager's request naming T09 and Speed `sbatch --array`).
  Paste this sentence into the T09 progress-log entry. The authorisation covers **T09 only** — it does not
  extend to any later task, any re-submission after a failed harvest, or any other arc.
- ✅ **`D-EU-42` AUTHORISED 2026-08-31.** Owner's authorising sentence, verbatim: *"oui, autorise la
  re-soumission après correction"* (owner, 2026-08-31, in reply to the manager's request naming a second
  Speed wave for the `FINDING 210` casualties). Paste this sentence into the progress-log entry of the
  re-submission. It authorises **one** further wave, restricted to the buildings that died of `FINDING 210`,
  **after** the geometry fix — nothing else.
- ✅ **`D-EU-43` AUTHORISED 2026-08-31.** Owner's authorising sentence, verbatim: *"autorise l'option a"*,
  followed by *"continuer jusqu'a la fin, et apres la fix, soumettre a la speed. merci"* (owner, 2026-08-31,
  in reply to the manager's request naming a third Speed wave for the newly-disclosed "zero/negative surface
  area" failures — 32 `ES-MAD-BERRUGUETE` + 13 `FR-LYO-HAUTCOEURPENTES`, 45 total). Paste this sentence into
  the progress-log entry of the re-submission. It authorises **one** further wave, restricted to exactly
  these 45 stems, **after** the zero/negative-surface-area defect is fixed — nothing else. It also authorises
  running T09 through to completion (stop-and-report 3 need not gate this wave) and proceeding straight to
  submission once the fix is proven, without a further pause.
- 🔴 Still bound: `sbatch --array` fire-and-forget only, never the login node, and the ~20k task cap
  means submission in waves.
- **Executor**: fresh Sonnet session. **Paste everything below the rule.**
- **Date of prompt**: 2026-08-30. **Revised 2026-08-31** (wave-1 state, harvest paths, `FINDING 210`,
  `D-EU-43` zero/negative surface area wave).

---

## Wave 1 — already submitted, do NOT re-submit it (state as of 2026-08-31)

The submit half of T09 is **done**. Four arrays were fired on 2026-08-30 and were still draining on
2026-08-31. Do not resubmit them.

| Array | District | Tasks |
|---|---|---|
| `1299912` | `ES-MAD-BERRUGUETE` | 961 |
| `1299945` | `FR-LYO-HAUTCOEURPENTES` | 297 |
| `1299946` | `GB-LDN-STDUNSTANS` | 82 |
| `1299947` | `IT-BOL-GALVANI2` | 1,204 |

Facts already established by the director — **use them, do not re-derive them**:

- All four arrays run `/speed-scratch/o_iseri/openubem/fleets/submit_fleet_t08.sbatch` with
  `--export=FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_<district>` — the **`EU11_*` tree, not `EU11R2_*`**.
  That tree was **overwritten on 2026-08-30 19:06–19:07 with the post-`EU-16` IDFs**: verified 961/961 Madrid
  IDFs carry a `SHADING:SITE:DETAILED` object. The `EU11R2_*` entries under `openubem/fleets/` are upload
  staging (`.tgz` + `.submit.sbatch`) and there is no Bologna one — **that is not a defect, harvest the
  `EU11_*` tree.**
- **Results live in `/speed-scratch/o_iseri/fleets/EU11_<district>/out/<stem>/`** (`eplusout.sql`,
  `eplusout.eio`, `eplusout.end`, `eplusout.err`; everything else is deleted by the sbatch script).
- **IDF object names on disk are UPPERCASE** (`SHADING:SITE:DETAILED`, `BUILDINGSURFACE:DETAILED`). Any grep
  over the IDFs must be case-insensitive or it will silently report zero.

### 🔴 `FINDING 210` — the failures are a known defect, not noise

Roughly **8 %** of tasks die in 2–4 s with `ExitCode 1:0`, at `GetSurfaceData`, before warmup. EnergyPlus
emits:

```
Severe  RoofCeiling:Detailed="BLOCK <stem>_CIRCULATION STOREY 0 CEILING 0001_2", Vertex size mismatch
between base surface :<...> and outside boundary surface: <...>_CIRCULATION STOREY 1 FLOOR 0001_1
**FATAL:GetSurfaceData: Errors discovered, program terminates.
```

Example: task `1299912_33`, stem `8b3598ac47b3f4a0` (Madrid); 8 vertices against 9. The offender is the
`EU-15` carved circulation ring (`D-EU-39`) — the ceiling of storey *n* and the floor of storey *n+1* are
generated with different vertex counts. **These buildings are fixed and re-run — never pooled around,
never dropped, never smoothed into an average.**

Order of work: (1) harvest wave 1; (2) classify every failure and confirm the `FINDING 210` count exactly;
(3) fix the circulation-ring vertex generation and prove it on the named example locally; (4) rebuild only
the affected IDFs; (5) submit **one** re-run array over exactly those stems under `D-EU-42`; (6) harvest it
and fold the results in. Register the fix in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in house
format before closing.

**Never poll the cluster from inside a shell and never wait in the foreground** — `sbatch`, then read
`squeue`/`sacct` on a later call.

---

## Task (paste from here)

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
Execute **T09 only**, then **stop at stop-and-report 3**. Do not interpret the results and do not start T10.

You are working in `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** — never bare
`python`. Git is handled externally: **never commit, never stage**.

### 🔴 Cluster hard rules — a breach ends the task

1. **Never compute on the login node** (`speed-submit2` / `speed.encs.concordia.ca`). No `srun`, no
   `ssh … python`. The login node is for `mkdir`, `scp`, `tar`, `squeue`, `sacct` **only**.
2. **Always `sbatch --array`, fire-and-forget, then read the output files.** Never wait inside a shell.
3. The remote login shell is **tcsh** — bash syntax sent over bare `ssh` fails silently. Wrap every remote
   command with the `_ssh()` helper (`scripts/cluster/t08_harvest_results.py:104`); if a script cannot import
   it, port that wrapper — never send a bare command string.
4. One EnergyPlus process per array task, `--cpus-per-task=1`, `ps` partition, start at `%32`, `6G`/task as the
   initial default. Submit in waves under the ~20,000-task cap.
5. Harvest by expanding the file list **remotely** and streaming a tar — a local path list overflows Windows
   argv at ~32 KB.
6. EnergyPlus is **23.1.0 Ubuntu20** at `/speed-scratch/o_iseri/openubem/tools/`. A Speed number and a Windows
   number are not the same measurement (`FINDING 187`, `FINDING 190`).
7. **Never touch another project's cluster runs.**

### T09 — resimulate, harvest, rebind

*What.* Wave 1 is already shipped (see the table above) — **harvest** the four district fleets (Madrid
`ES-MAD-BERRUGUETE`, Lyon `FR-LYO-HAUTCOEURPENTES`, London `GB-LDN-STDUNSTANS`, Bologna
`IT-BOL-GALVANI2`), fix `FINDING 210` and re-run its casualties under `D-EU-42`, re-emit the side-cars,
regenerate the four viewers,
mirror to `docs/docs_ACTIVE/europeanLocations/outputs_3D/`, and update
`docs/docs_ACTIVE/europeanLocations/results/RESULTS_EU-11.md`.
*How to test.*
- The mirror is byte-identical (`diff -rq` output pasted, not summarised).
- **Every Speed failure is classified and carried as a row with blank `heating_kwh`** — never smoothed into a
  pooled figure, never dropped.
- A per-district **before/after EUI table**, with the **shading effect and the adiabatic effect reported
  separately in sign**, per `rules/RULES_context_geometry_simulation_2026-08-30.md` §3.5.
*Standing constraint.* **Never tune an input to move an EUI into a band.** Report the number and the band it
falls in. Bologna's rows remain 100 % `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` — that tag appears in the
same sentence as any Bologna figure, in every document.
*Errors.* **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first**;
register any solved error there in the house format before closing the task.

### Report (🔴 stop-and-report 3 — stop here, before any interpretation)

Append the progress-log entry to **§8 of the plan** (including the owner's authorising sentence, the job IDs
and the submission commands) and one row to
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`. Then report:

1. Job IDs, array sizes, wall time, and the completed/failed counts per district — **wave 1 and the
   `D-EU-42` re-run wave as two separate blocks**, never merged.
2. Every failure class with its count and one example `.err` excerpt; `FINDING 210`'s exact count per
   district, and how many of them the fix recovered.
3. The per-district before/after EUI table, shading and adiabatic effects separated in sign.
4. The `diff -rq` mirror check output.
5. The `file:line` of the circulation-ring fix and its `OpenUBEM_debug_References.md` entry.
6. **Do not state whether the new EUIs are acceptable — that is the owner's call. Stop.**

---

## `D-EU-43` addendum — the 45 zero/negative surface area failures

*What.* Classify the exact root cause of the 45 "zero/negative surface area" failures (32 Madrid, 13 Lyon)
excluded from `D-EU-42`; fix it; prove it on one named example locally; rebuild only the affected IDFs;
submit **one** re-run array over exactly those 45 stems under `D-EU-43`; harvest and fold the results into
the same before/after EUI tables and side-cars as `D-EU-42`; regenerate the two affected district viewers;
update the mirror. Register the fix in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in house format
before closing.
*Standing constraints.* Same as T09 above: never tune an input to move an EUI into a band; every failure
still classified and carried, never dropped; cluster hard rules 1–7 still apply.

### Report (🔴 stop-and-report 4 — stop here, before any interpretation)

Append the progress-log entry to §8 of the plan (owner's authorising sentence, job ID, submission command)
and one row to `walkthrough_progress_log.csv`. Then report, in the same shape as stop-and-report 3 above:
the D-EU-43 job ID/array size/wall time/completed-failed count; the root cause and the `file:line` of the
fix and its debug-references entry; the updated per-district before/after EUI table (Madrid, Lyon) with
shading/adiabatic effects separated in sign; the `diff -rq` mirror check output. Do not state whether the
new EUIs are acceptable — stop.
