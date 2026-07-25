# Director Prompt — UTCI E-UTCI-09 INVESTIGATION — AUTONOMOUS RUN TO COMPLETION

> **How to use:** paste everything below the line into a fresh Claude session (**Sonnet, xhigh
> reasoning effort**) opened at `C:\Users\o_iseri\Desktop\OpenUBEM`. That session becomes the
> **director** of the UTCI E-UTCI-09 investigation plan and runs it **to completion without user
> intervention**.

---

You are the **director/manager** of the **UTCI E-UTCI-09 investigation plan** for OpenUBEM. Follow
`CLAUDE.md` at the project root. The user is **away and will not answer questions** — this is a fully
autonomous run. When the user returns they expect to see the **investigation complete**: every task
executed, findings recorded, the checkpoint synthesized, and a final completion report. Deliverables
in English.

## 0. Operating mode (overrides any conflicting habit)

1. **NEVER ask the user anything.** No clarifying questions, no sign-off requests. If a task's own
   text says "stop and ask the manager," that means **you** (the director) decide it yourself, log
   the decision and rationale, and keep going — there is no other manager to ask, except for the stop
   condition in §0.7 below.
2. **You spawn the employees yourself**, inside this session, using the **Agent tool (subagent
   sessions)**. Each employee = one fresh subagent given a task range from the plan. Do not resume a
   prior employee session for a new task — always a fresh one, per this project's standing
   convention (only continue an in-flight employee if it is still working the SAME not-yet-reported
   task).
3. **This plan is investigation-only. You do NOT implement a fix, under any circumstance, no matter
   how obvious one seems.** `PLAN_e-utci-09_investigation.md` §1 rule 2 forbids editing
   `openubem/acquisition/osm_fetcher.py`, `openubem/semantic/spatial_impute.py`,
   `openubem/semantic/imputation.py`, `openubem/config.py`, `openubem/microclimate/domain.py`, or
   `openubem/microclimate/wind.py`. If I03's diagnostic probe reveals what looks like an obviously-
   correct fix (e.g. "just lower the MNAR guard threshold"), **do not wire it in** — record it as a
   candidate fix shape in I04 and the completion report for a future, separately-scoped
   implementation plan. Treating "the fix seems obvious" as license to implement it anyway is exactly
   the kind of freelancing this plan's hard rules forbid.
4. **Progress log discipline (mandatory at every step):** after every completed task, verify the
   employee appended its §7 entry in `PLAN_e-utci-09_investigation.md` (write it yourself if the
   employee failed to); tick §0 checkboxes as you go (tasks after their §7 entry exists, the
   checkpoint only after your own synthesis).
5. **This plan never reaches CLOSED.** It ends at CP-INV, explicitly OPEN, handed back to a
   human-available manager session. Do not write "plan CLOSED" anywhere in this run's outputs — write
   "investigation complete, findings synthesized, awaiting manager scoping of a follow-up Stage-1
   implementation plan."
6. **No cluster compute and no live network calls whatsoever for this plan.** Every task is local,
   read-only or scratch-diagnostic (a handful of `.gpkg` reads, one imputation-module smoke test,
   desk research against documentation pages only). No OSM Overpass re-fetch, no external DSM/LiDAR
   API calls — CLAUDE.md's "no live-network integration tests until §5.3 is unblocked" rule is still
   in force. If an employee proposes a live fetch "just to check," reject it — that is exactly the
   kind of exception §5.3 exists to gate, and this investigation does not need it (I02 is
   documentation research, not a data pull).
7. **🔴 If, and only if, I01's full 12-cell characterization shows the gap is NOT cleanly scoped to
   the `height_m`/`levels` fields** (e.g. another column, like `footprint_area_m2` or geometry
   validity, is also broadly degraded in a way suggesting a wider fetch failure, not just a missing
   tag): this is the plan's one genuine stop-and-report condition (§6.1 of the plan doc) — it
   falsifies the "narrow field-level gap" framing the rest of the plan (I02-I04) is built on. In that
   specific case only: pause before dispatching I02/I03/I04, write up the I01 finding in full, and
   decide for yourself (log the reasoning) whether I02-I04 as scoped are still worth running or need
   reshaping — do not silently proceed as if nothing changed, and do not treat this as license to ask
   the user.

## 1. Read first (in this order)

1. `docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/PLAN_e-utci-09_investigation.md` — **the binding contract for
   this run.** §0 live checklist, §1 hard rules (note rule 2 and rule 3 — no fix implementation, no
   live network calls, this plan does not close), §2 file layout, §3 dependency decisions, §4
   manager-verified facts F-01 through F-09 (read carefully — the acquisition code path, the two
   existing-but-non-height-filling fallbacks, and the unwired imputation infrastructure with its MNAR
   guard are already cited line-by-line; do not re-derive them from scratch, but I01-I03 exist
   specifically to independently re-confirm and extend them, not to take them on faith), §5 tasks
   I01-I04, §6 stop-and-report points, §7/§8 (currently empty — you fill them).
2. `docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md`, specifically the
   `E-UTCI-09` entry (search for `#### E-UTCI-09`, around line 4216) — read it in full; the
   investigation plan's §4 already extracted the load-bearing facts, but the original T26 harvest
   evidence and the CP-5 audit context live there. **Do not re-open or re-litigate that plan's own
   §9/§10 — it is a frozen historical record.**
3. `openubem/acquisition/osm_fetcher.py` (the `ingest_buildings`/`_flatten_tags`/`_parse_height_to_m`
   functions), `openubem/semantic/spatial_impute.py` (full file — it's the object of I03), and
   `openubem/microclimate/domain.py`'s / `wind.py`'s `height_m` filter sections — read these
   directly; do not assume the investigation plan's line citations are still accurate if the code has
   moved since 2026-07-24.

## 2. State at handoff (2026-07-24)

- The UTCI/Stage-6 arc is **CLOSED** (CP-5 signed 2026-07-24): all 26 tasks done, all 5 checkpoints
  signed. Its T26 12-cell cluster harvest found candidate defect **E-UTCI-09** — 3 of 12 cells
  (`nyc_suburban`, `nyc_rural`, `austin_rural`) with 100% `height_m` NaN, plus `austin_centre` at
  84.5% — causing Stage 6 to exclude those buildings from its DSM (in the 3 total-exclusion cells,
  `svf_mean = 1.0000`, i.e. a flat field, not an urban canyon). Logged **OPEN** (forwarded, not
  blocking) in that plan's own §10.
- Nothing in this investigation plan has been dispatched yet; every §0 box in
  `PLAN_e-utci-09_investigation.md` is unticked.
- Raw harvest data available: `openubem/outputs/comparisons/t26_utci_cluster_cell_summary.csv` (12
  rows, one per cluster cell, includes `n_excluded_no_height`/`pct_excluded_no_height`/`svf_mean`/
  `zero_building_massing` per cell). **Read-only for this plan — never overwrite it.**
- Fixture source, all 12 cells: `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/
  01_buildings.gpkg` — same files T26's harvest read. **Read-only. Never overwrite.**
- This is a small, local-only, no-network investigation — no `sbatch`/Speed cluster involvement and
  no live OSM/external-API calls at all, unlike most prior arcs in this project.

## 3. Execution sequence (run it all, in this order)

| Step | Who | What |
|---|---|---|
| 1 | Employee A | I01 (full 12-cell characterization: NaN%/row-counts/geometry-validity table) |
| 2 | Director | Quick sanity check: does the gap stay cleanly scoped to `height_m`/`levels`, matching F-08's 5-cell spot-check? If not, invoke Operating Mode rule 7 (stop-and-report) before continuing |
| 3 | Employee B | I02 (desk-research survey of candidate external height data sources — no live fetch) |
| 3 | Employee C | I03 (structural test of `spatial_impute.py`'s MNAR guard against the real 100%/84.5%-missing cells) — **I02 and I03 may run concurrently, both depend only on I01** |
| 4 | Employee D | I04 (candidate fix shapes synthesis, drawing on I01-I03) |
| 5 | Director | **CP-INV** — synthesize all findings, write the completion report (§6 below) |

**Employee dispatch rules:** give each employee the plan path
(`docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/PLAN_e-utci-09_investigation.md`), its exact task letter, the
plan's own §1 hard rules (especially rule 2 — no production-code edits — and rule 3 — no live network
calls) and §3 dependency decisions, the instruction to append its own §7 entry, and: "if the plan is
ambiguous or conflicts with the code, STOP and report the conflict back to YOU (the director) — you
resolve it against the plan's §3/§4 and log the ruling, never invent a plan-violating workaround."
Default-effort Sonnet subagents are sufficient for all four tasks — this is characterization and
desk research, not delicate mechanism isolation.

## 4. Progress log formats (enforce exactly)

Task entry (employee-written, §7 of the investigation plan):
```
#### IXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths, e.g. scratchpad/e-utci-09-investigation/...>
- Deviations: <none | rationale + plan §3/§4 cite>
- Test status: <what was actually run/read and its literal output, quoted, not paraphrased>
- Notes: <auditor-relevant>
```

Checkpoint entry (director-written, §7):
```
#### CP-INV — investigation synthesis — completed YYYY-MM-DD
- Scope: I01–I04
- Finding: <gap characterization confirmed/extended, stated plainly>
- Candidate fix shapes: <from I04, ranked/flagged, none adopted>
- Open questions: <anything I01-I04 could not resolve>
```

## 5. Audit checklist (each time an employee reports, before dispatching the next)

1. One §7 entry per task, format conformant.
2. Every NaN%/row-count/behaviour claim backed by actually-quoted `geopandas`/pandas output or actual
   observed function return values, not a paraphrase — **independently re-derive at least one of
   these yourself** (read one `.gpkg` file directly, or re-run I03's imputer call yourself) before
   trusting an employee's printed summary, same standard every prior checkpoint in this arc's lineage
   has held to.
3. Only files under `scratchpad/`, `openubem/outputs/`, and this plan's own `figures/`/`§7`/`§0` were
   touched — **no** `openubem/acquisition/*.py`, `openubem/semantic/*.py`, `openubem/config.py`, or
   `openubem/microclimate/*.py` diffs (check `git status`; read-only, never commit).
4. §0 ticks match §7 entries.
5. For I03 specifically: confirm the employee actually invoked the real `spatial_impute.py` code
   against real data and observed real behaviour (guard triggered / not triggered, with the actual
   returned value or exception) — a report claiming "the guard would reject this" without an actual
   executed call is not evidence, it's an assumption.
6. For I02 specifically: confirm no code was written that calls an external API — desk research
   (reading documentation) only.
Anything missing → dispatch a fix employee before continuing to the next step.

## 6. Final completion report (last action before going idle)

Write `docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/COMPLETION_REPORT_e-utci-09-investigation.md` (English)
containing:
- Per-task outcome table (I01-I04).
- I01's full 12-cell table (the load-bearing scope-confirmation result).
- I02's candidate-data-source findings table.
- I03's imputer-behaviour result — state plainly whether the existing infrastructure is or is not
  structurally viable as a fix path, do not overstate an inconclusive result as conclusive.
- I04's ranked candidate-fix-shapes table, explicitly flagged as candidates only, none adopted.
- **A clear, one-paragraph plain-language statement of the investigation's headline finding** (or, if
  genuinely unresolved on some point, exactly what remains unknown and why).
- **Explicit recommendation on what a follow-up Stage-1 implementation plan should contain**, citing
  the most promising I04 option(s) — but do not draft that plan yourself; that is a future,
  separately-scoped manager task.
Then:
- Update `docs/PROJECT_CHECKLIST.md`'s UTCI section with a short note that the E-UTCI-09 investigation
  is complete and what it found (not "fixed" — investigated).
- Update memory `C:\Users\o_iseri\.claude\projects\C--Users-o-iseri-Desktop-OpenUBEM\memory\
  project_utci_microclimate_arc.md` with the investigation's headline finding (+ `MEMORY.md` index
  hook if the one-line description changed).
- Leave a short final message summarizing: headline finding, candidate fix shapes, and that this is
  investigation-only — no fix has been implemented, a follow-up plan is still needed. In French (the
  user converses in French; the report itself stays English).

## 7. Standing constraints (non-negotiable)

- **No cluster compute and no live network calls for this plan at all** — every task is local
  reads or desk research. If this changes your mind partway through because something seems to need
  a live check, that itself is a finding to report, not a reason to fetch anything — this plan's own
  scope is local-only.
- Git handled externally — never commit, never offer to.
- No `.py` under `docs/`; never edit root `main.py` or OVERVIEW/DESIGN docs.
- **Never overwrite the T26 harvest CSV or any `01_buildings.gpkg` fixture** — this plan only reads
  them.
- Do not modify the CLOSED UTCI implementation plan's own `§9`/`§10` entries — frozen historical
  record; this plan's own `§7`/`§8` (in `PLAN_e-utci-09_investigation.md`) is where you write.
- **Do not implement a fix.** This is the single most important constraint in this entire prompt,
  repeated a third time because it is the one most likely to be violated by an otherwise
  well-functioning autonomous run: no matter how confident you become about the right fix, this plan
  ends at CP-INV with a recommendation, not a code change.
- You (director) write NO feature code — employees write diagnostic scripts only (`scratchpad/`),
  never production code. You write only: plan §7/§8 entries, §0 ticks, the completion report,
  checklist/memory updates.
