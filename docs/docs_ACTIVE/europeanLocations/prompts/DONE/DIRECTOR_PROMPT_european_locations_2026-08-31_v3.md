# DIRECTOR PROMPT — European locations, occupant schedules, and simulation campaign

**Project:** OpenUBEM × GSSCanada Step 8 integration
**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Read-first state doc:** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v3.md`
(v2 frozen 2026-08-30 at `previous/STATE_european_locations_v2.md`; plain-language brief at
`BRIEF_european_locations_v3.md`)
**Full history through 2026-08-30:** `prompts/previous/DIRECTOR_PROMPT_european_locations_2026-08-30.md`
— every `D-EU-NN` ruling, every `FINDING NNN`, the complete slice ledger. **This file was closed and
reopened lean on 2026-08-30 (second closure; first was 2026-08-22) — cite the archive by section, never
restate its content here. Close this file again the same way once it re-exceeds ~1,000 lines.**

---

## Current moment — read this first (T01–T09 done and harvested; `D-EU-42`–`D-EU-44` closed; `D-EU-47`/`D-EU-48` resubmit waves running on Speed, 2026-08-31)

🔴 **0-bis. LATEST — `D-EU-42`–`D-EU-48`, all 2026-08-31, superseding the "T09 wave draining" framing below.**
`D-EU-42`/`D-EU-43` (owner-authorised `FINDING 210` fix wave) harvested and folded in: Madrid 98→2 failed,
Lyon 26→0 (9 wave-1 `TIMEOUT`s left, unrelated), London 2→0. `D-EU-44` (owner-authorised) recovered the last
2 unaccounted Madrid stems — **Madrid now 961/961, 0 Speed-failed**. Bologna's 177 `FAILED` + 13 `TIMEOUT`
were untouched through `D-EU-44` (out of scope). Post-`D-EU-44` pooled heating EUI: Madrid 72.1096 kWh/m²
(961/961), Lyon 62.1528 kWh/m² (288/297, 9 `TIMEOUT` residual), London 78.4405 kWh/m² (82/82), Bologna
48.9253 kWh/m² (1,014/1,204, unchanged) — 🔴 all four still barred from quotation pending `T10`.
`D-EU-45`/`D-EU-46` (classification-only investigations, 2026-08-31): Bologna's 177 `FAILED` split 85 exact
`FINDING 210` + 52 exact `D-EU-43` + 40 zero-area-only — all three buckets hypothesised covered by the
existing unmodified gate; Lyon's 9 `TIMEOUT`s confirmed genuine wall-clock exhaustion (0–28 s over the 2 h
limit), no defect, no rebuild needed. Owner authorised both remediations verbatim *"oui j'autorise, vas-y"*
(2026-08-31). **`D-EU-47`** (Bologna rebuild/resubmit, prompt `previous/PROMPT_D-EU-47_bologna_rebuild_resubmit.md`):
176 of 177 stems rebuilt and proven locally, 1 excluded pre-ship (`635c1d7d41a92830`/building 31741,
unresolved reroute, disclosed not fixed) — shipped to `EU11_IT-BOL-GALVANI2_deu47`, job `1303039`
(176 tasks), **running, not yet harvested**. **`D-EU-48`** (Lyon timeout resubmit, prompt
`previous/PROMPT_D-EU-48_lyon_timeout_resubmit.md`): same 9 stems resubmitted `--time=03:00:00` (was 2h),
job `1303023` (9 tasks), **running, not yet harvested**. Neither job's harvest is authorised beyond folding
its own results in — no further Speed submission. **Next free identifier `D-EU-49`, next free finding
`FINDING 211`** (supersedes the `D-EU-43`/`FINDING 211` figures quoted below, which predate this block).

🔴 **0. THE ARC MOVED TO v3 ON 2026-08-30. Read `STATE_european_locations_v3.md` before anything below.**
The owner inspected the four viewers and ruled twice: **`D-EU-39`** — the ruled MVP §4.2–§4.4 grid is
mandatory on **≥ 95 % of buildings in every district** (not a fleet average), `equal_strip_multi_angle_sweep`
is retired as a success path, and circulation is **CARVED** from the observed plate (this resolves
`D-EU-36`'s open half and unblocks `T06`); **`D-EU-40`** — every building is simulated with its **20 m
context geometry** as shading and with **adiabatic** walls where it is attached to a neighbour, per the
published method (Fig. 4b). Three new findings: **`FINDING 207`** ruled-scheme conformance is 57.81 %,
not the 93.6 %/88.1 % reported; **`FINDING 208`** 0 of 2,516 IDFs carry a shading or adiabatic surface
(`scripts/run_eu_s2_campaign.py:227`); **`FINDING 209`** 0 of 2,541 buildings carry the unconditioned core.
🔴 **All four district EUIs are barred from quotation until `EU-16` resimulation lands.**
Plan in force: `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` (T01–T10, three stop-and-report
points, T10 writes the validation audit). New rule doc: `rules/RULES_context_geometry_simulation_2026-08-30.md`.
**Next free identifier `D-EU-43`, next free finding `FINDING 211`.** `D-EU-41` (2026-08-30) corrects `D-EU-40` `R6`: `set_adiabatic_surfaces` is a no-op stub that cannot implement the party-wall flip; `surfaces.py` stays non-editable and the flip lives in `scripts/run_eu_s2_campaign.py`. Everything in items 1–5 below is the
state as of the v2 close and is still true unless v3 §3 says otherwise.

🔴 **0a. WHERE THE ARC ACTUALLY IS (2026-08-30, evening).** `EU-15` (`T01`–`T05`) and `EU-16A`
(`T06`–`T08`) are **executed and audited**. `EU-16B` (`T09`) is **submitted and running on Speed** under the
owner's authorising sentence *"oui, autorise la soumission Speed pour T09"* — that authorisation covers **T09
only** and does **not** extend to any re-submission after a failed harvest.

- Arrays submitted 2026-08-30T19:09:49–19:10:01, partition `ps`, job name `openubem_t08`:
  **1299912** Madrid (961) · **1299945** Lyon (297) · **1299946** London (82) · **1299947** Bologna (1,204)
  = 2,544 tasks. Throttled by `AssocGrpCpuLimit` / `JobArrayTaskLimit` to ~20–32 concurrent — hours, not minutes.
  First poll: 300 COMPLETED / 27 FAILED / 4 PENDING / 32 RUNNING.
- 🔴 **`FINDING 210` — the wave carries a systematic input-level fatal, and it is not the new context work.**
  ~8 % of tasks die in 2–4 s with `ExitCode 1:0`, before warmup. EnergyPlus:
  `Severe RoofCeiling:Detailed="BLOCK <stem>_CIRCULATION STOREY 0 CEILING 0001_2", Vertex size mismatch between
  base surface … and outside boundary surface: …_CIRCULATION STOREY 1 FLOOR 0001_1` (8 vs 9 vertices), then
  `**FATAL:GetSurfaceData: Errors discovered, program terminates.` The offender is the **`EU-15` carved
  circulation ring** (`D-EU-39`): the storey-to-storey `intersect_match` pair on the circulation zone gets
  unequal vertex counts. Example: task `1299912_33`, stem `8b3598ac47b3f4a0`, Madrid.
  **These buildings must be fixed and re-run — never pooled around, never dropped.** Register in
  `STATE_european_locations_v3.md` §3 and in `docs_EXPLANATION/OpenUBEM_debug_References.md` before closing T09.
- ✅ **`D-EU-42` authorised 2026-08-31**, owner verbatim: *"oui, autorise la re-soumission après correction"* —
  **one** further Speed wave, restricted to the `FINDING 210` casualties, after the geometry fix. Nothing else.
- ✅ **Both harvest blockers resolved 2026-08-31 — they were artefacts, not defects.** All four arrays run
  `submit_fleet_t08.sbatch` with `FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_<district>`; that `EU11_*` tree
  was **overwritten 2026-08-30 19:06–19:07 with the post-`EU-16` IDFs** (961/961 Madrid IDFs carry
  `SHADING:SITE:DETAILED`). The `EU11R2_*` entries under `openubem/fleets/` are upload staging (`.tgz` +
  `.submit.sbatch`) only, so the missing Bologna one is harmless. **Harvest
  `/speed-scratch/o_iseri/fleets/EU11_<district>/out/<stem>/`.** IDF object names on disk are **UPPERCASE** —
  grep case-insensitively or every count comes back zero.
- 🔴 **This session never follows a Speed wave itself.** Standing owner instruction, 2026-08-30: dispatch a
  **`model: "haiku"`** monitor agent, polling at **30-minute intervals**, strictly report-only — never harvest,
  copy, resubmit, edit or write a document. Never put `!` in a remote command (tcsh history expansion). A monitor
  that returns after a single poll is **re-dispatched as a new session**, never resumed.

🔴 **0b. Executor prompt ledger — dispatch order, one fresh Sonnet session each, `model: "sonnet"` always
passed explicitly. Never two in parallel; each consumes the previous one's artefacts. A completed prompt moves
to `prompts/previous/`.**

| # | Prompt | Tasks | Status |
|---|---|---|---|
| 1 | `previous/PROMPT_EU-15A_coverage_recovery_T01-T03.md` | T01–T03 | ✅ done |
| 2 | `previous/PROMPT_EU-15B_retire_strip_and_carve_core_T04-T05.md` | T04–T05 | ✅ done — stop-and-report 1 audited |
| 3 | `previous/PROMPT_EU-16A_context_adiabatic_T06-T08.md` | T06–T08 | ✅ done — stop-and-report 2 audited |
| 4 | `previous/PROMPT_EU-16B_speed_resimulation_T09.md` | T09 | ✅ done — harvested and folded in under `D-EU-42`/`D-EU-43`/`D-EU-44` (see 0-bis) |
| 6 | `previous/PROMPT_D-EU-47_bologna_rebuild_resubmit.md` | `D-EU-47` | 🟡 **submitted, running** — job `1303039` (176 tasks), not yet harvested |
| 7 | `previous/PROMPT_D-EU-48_lyon_timeout_resubmit.md` | `D-EU-48` | 🟡 **submitted, running** — job `1303023` (9 tasks), not yet harvested |
| 5 | `PROMPT_EU-VAL_validation_audit_T10.md` | T10 | ⚪ waiting — dispatch to a session that executed none of T01–T09; also blocked on `D-EU-47`/`D-EU-48` harvest folding in first |

Audit each return against: progress-log entry in plan §8, a `walkthrough_progress_log.csv` row, test output,
only plan §3 files touched, and a `file:line` citation for any unplanned decision. Missing any one → send it
back before greenlighting the next prompt. **T09 has no progress-log entry yet** — the harvest dispatch owes
it, including the owner's authorising sentence and the four job IDs.

🔴 **0b-bis. Carried, unresolved, from the `EU-16A` audit.** (i) Measured adiabatic coverage
**89.4 / 86.5 / 70.7 / 80.7 %** (Madrid / Lyon / London / Bologna) against the attachment census
`RULES_context_geometry_simulation_2026-08-30.md` §3 item 2 expects (99.1 / 97.0 / 92.8 / 88.5 %) — reported as
measured, not tuned, and **not yet explained**. (ii) Measured neighbour counts 30.1–49.1 vs the 11.1–12.2 in the
rules doc §1 — different source layers, reconcile before publishing R9's disclosure. (iii) The silent
`one_zone_per_floor` reroute on an `intersect_match` exception still writes **no `geometry_outcome`**
(`D-EU-35` disclosure gap).

**Next free identifier `D-EU-49`, next free finding `FINDING 211`** (see 0-bis — this line predates `D-EU-45`–`D-EU-48` and is kept only for the 0b-bis context above it).

**0c. Visual explainers of `EU-15`/`EU-16`** live at `prompts/images/` — three paste-able image prompts and
their renders (first generation archived in `prompts/images/previous/`). Verified 2026-08-30 against
`BRIEF_european_locations_v3.md` and `STATE_european_locations_v3.md`: **no doc claim is contradicted by any
render, and no render carries an embargoed district EUI.** The two axonometric renders are nonetheless
incomplete against the prompts on disk — the 1.80 m corridor spine and the equal-area contrast are missing
from the `EU-15` image, the `(a)`–`(d)` panels and the reflected-solar bounce from the `EU-16` image, and the
flowchart's measured footnote strip rendered as a heading with no lines. **Re-render before using either in a
deliverable; never treat the current renders as the specification — the rule documents are.**

---

## Previous moment (`FINDING 206` fixed, 2026-08-30)

🔴 **1.** `EU-13B` (`T01`–`T05`, `T07`–`T10`, including `T09` resimulation) and `EU-14B` (`T01`–`T05`,
including its resimulation half) are **Done, 2026-08-30**, per `D-EU-38`'s unblock. 🔴 **`T06` (core
carve-vs-add) stays blocked** on `D-EU-36`'s other half — out of scope until the owner rules it.

**2.** `FINDING 206` (the ruled partitioner computes a real per-storey circulation/corridor polygon, but
`scripts/emit_eu11_layout_sidecars.py` discarded it before serialization and the viewer's `drawFloorPlan`
had no code path to draw it — so the four regenerated viewers looked visually unchanged despite `EU-13B`'s
ruled math being correct) is **fixed, 2026-08-30**. Both scripts now carry and draw the circulation ring;
all four districts regenerated and mirror-verified; a unit test covers both the ruled-grid (non-null ring)
and `l_shape_decomposition` (`None`, pinned by design) cases. Full record:
`debugs/docs/INVESTIGATION_viewer-circulation-not-drawn_2026-08-30.md`,
`implementation/previous/DONE_PLAN_eu-circulation-viewer-2026-08-30.md`. New minor observation, not yet
investigated: `equal_strip_multi_angle_sweep` also carries `circulation: None` upstream at the geometry
layer, pre-existing, not introduced by this fix. Next free finding `FINDING 207`; next free identifier
`D-EU-39`.

**3.** The prototype board ("Dwelling Plans Redrawn") is now also a repository file:
`docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_scheme_2026-08-28.html`, alongside
`rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` (relocated there from the arc root).

**4. What to pick up next.** No dispatch is currently in flight. Open items: `T06` carve-vs-add remains
blocked on `D-EU-36`; `FINDING 205` (London EUI moved CONSISTENT→WORTH INVESTIGATING) and `FINDING 199`/
`DR16` (campaign-wide pooled-EUI audit) are decisions for the owner, not to start autonomously; `D-EU-37`
(typology table extension) is open, recommended to measure first via `EU-13B` `T10`'s report.

**5. What's still load-bearing from history, named and no more.** `D-EU-36` (partly ruled): fleet
coverage bar ≥ 95 % is sufficient, 100 % not required — but carve-vs-add (`D-EU-36`'s other half) is
what `T06` is blocked on. `D-EU-37` (open): whether the `D-EU-04-G` typology table is extended —
recommendation is to measure first via `EU-13B` `T10`. `FINDING 199` (open): Bologna's pooled heating
EUI (55.5346 kWh/m², `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on 100% of rows) sits in `DR16`'s own
pre-registered INCOMPATIBLE (Too Low) band — not Bologna's to explain alone, since all four districts
sit low against their own dossiers' bands; never tune an input to move it. `FINDING 200`–`203` (why
`EU-13B` exists): the layout emitter never implemented the ruled `n_u × n_v` grid scheme, over-counted
dwellings per storey, allowed >8 dwellings/floor, and mis-attributed most of Lyon's exclusions to data
gaps that are actually uncovered typology-table cells. `FINDING 204` (a standing instruction, not a
ruling): MVP §4.3's two circulation criteria conflict on most plates; the executor emits the 6–12 %-of-
GFA rule and tags departures, never resolves the conflict itself. Everything else — every other
`D-EU-NN` and `FINDING NNN`, and the full narrative of how each was reached — is in the archive above.

---

## Purpose

Prepare and validate OpenUBEM's residential building/neighbourhood and baseline simulation pipeline for
four European populations: Spain (`ES`), England-limited TABULA stock (`GB`), Italy (`IT`), France
(`FR`). Integrate the GSSCanada occupant-presence workflow for `ES`/`GB`/`IT`; France occupant diaries
and non-zero occupant-effect schedules are a named future branch (`FR-OCC-FUTURE`), not required to
close the current release, and must never be reported as implemented.

The `ES`/`GB`/`IT` occupant design is 102 national archetypes (24 `ES` + 36 `GB` + 42 `IT`) × 22 diary
time bands × five occupant-effect levels `f ∈ {0.00, 0.15, 0.30, 0.50, 1.00}` = **510 annual simulations
per weather specification**, including the 102 `f=0` controls (part of the 510, not additional). Never
report 612 runs. The campaign is complete only when inputs, assignments, outputs, accounting,
comparisons and failure-detection gates are supported by retained evidence — not merely because
EnergyPlus returns zero.

Separately, `EU-11` opened a real-footprint **S2** route: one EnergyPlus run per residential building
across four real districts (Madrid `ES-MAD-BERRUGUETE`, Lyon `FR-LYO-HAUTCOEURPENTES`, London
`GB-LDN-STDUNSTANS`, Bologna `IT-BOL-GALVANI2`; 4,186 buildings total), independent of the S0 archetype
campaign above. **Never compare an S2 number with an S0 number without stating that perimeter, geometry
and weather years all differ.** `EU-13B`/`EU-14B` (current work) exist because the S2 layout emitter's
floor plans did not conform to the ruled dwelling-layout scheme — see the current-moment box above.

## Authority and source precedence

1. Parent GSSCanada Step 8 spec + validation doc (`GSSCanada-main\4J_docs_occ\Step8_docs\`).
2. Current OpenUBEM code and tests at the revision under review.
3. The Step 8 implementation doc (`IMP_step8\4thJ_08_bemSimulation_IMP.md`) and its
   `resources`/`DeepResearch`/`extracted_scripts`/`outputs` folders.
4. Illustrative examples in older implementation prose.

Day-to-day active spec: `STATE_european_locations_v3.md` (read-first, current), with
`previous/STATE_european_locations_v2.md`,
`previous/MVP_european_locations.md` and `previous/WALKTHROUGH_european_locations.md` as frozen
historical authority on how every fact was obtained — they are no longer appended to. Never edit
either frozen doc, and never annotate MVP Table 9.7 (status/owner/one-line-remainder only; notes go to
§9.7.3, the progress log, and this prompt).

## Frozen scientific decisions

Do not reopen without a documented reason and explicit approval:

1. Physical populations are Spain, England-limited GB, Italy, France — never generalize GB to the whole UK.
2. France is in scope for physical preparation and controlled baselines only; occupant diaries are future scope.
3. `ES`/`GB`/`IT` occupant archetype counts are 24/36/42 = 102; France's physical registry count is separate.
4. Report every occupant-effect level `f`; never present `f=0.30` as the sole case.
5. Mean internal-gain density is exactly 3 W/m² for every campaign `f`; Italy's 4 W/m² is literature context only.
6. Every controlled baseline (incl. France) uses the same `Schedule:File` path as non-zero cases, constant series, no stochastic draw.
7. One thermal zone per dwelling; a separate common core only if explicitly justified; no within-dwelling room-location claims.
8. Held-out-fold correctness: a country's evaluated schedules must never leak its held-out records.
9. Use actual weather aligned to each diary fieldwork period; France baseline weather is separately sourced.
10. Retain the TABULA heating-intermittency scalar; no additional thermostat setback that double-counts it.
11. Only residential buildings enter layout/IDF/simulation manifests; non-residential stays visible in the audit source, excluded with a reason.
12. `N1`/`N2` are real contiguous dense residential neighbourhoods on a preserved boundary — never assembled to force a count.

## Speed HPC operating contract

- Never compute on the login node (`speed-submit2`/`speed.encs.concordia.ca`) — no `srun`, no `ssh …
  python`. Login node = `mkdir`/`scp`/`tar`/`squeue`/`sacct` only. Always `sbatch --array`,
  fire-and-forget, then read outputs.
- Never submit a job without the current task's explicit authorization.
- One EnergyPlus process per array task, `--cpus-per-task=1`; `%N` caps simultaneous tasks, not CPUs per
  task; start at `%32`.
- `ps` partition, no GPU; `6G`/task is an initial measured default, revise from observed peak memory.
- Remote login shell is **tcsh** — wrap every remote command in `bash -lc`, via the repo's `_ssh()`
  helper (`scripts/cluster/t08_harvest_results.py:104`) or by porting its wrapper.
- Submit in waves under the ~20,000-task cap; harvest by expanding file lists **remotely** and streaming
  a tar (a local path list overflows Windows argv at ~32 KB).
- Preserve exact module/EnergyPlus versions, environment, repo revision, manifest checksum, submission
  command, and per-case evidence (manifest row, IDF, schedule/gain CSVs, EPW identity, `.err`/`.end`/
  `.eio`, SQL/meter output, return code).

## Evidence and validation contract

- No vacuous checks (an empty parser result is not zero warnings/unmet-hours/balance-error).
- Reopen and independently inspect saved IDFs/schedules — verify what EnergyPlus actually received.
- Prove schedule-to-object assignment, not just CSV values.
- Hash upstream inputs so stale cache reuse is detectable; run mutation tests (corrupt one thing, expect the gate to fail).
- Reconcile energy accounting to the declared total within 0.5% with an explicit physical-vs-reconstructed policy.
- Classify warnings by kind, never by raw count; independently recompute headline numbers before publication.
- A gate is `NOT_RUN` until its command and evidence have actually been observed — a written spec is not a passing test.
- Stop the campaign on: manifest/semantics disagreement, unresolved provenance/licence, a silent crosswalk fallback, weather/fold mismatch, malformed or leaky schedules, stochastic controls, geometry/construction reconciliation failure, unclassified severe/fatal errors, double-counted accounting, hidden case failures, an accepted mutation that should have failed, or unexplained resource-use drift.

## Director operating rules

- Reply to the user in English even when they write in French; lead with the verified outcome or blocker; ask at most one focused question when a decision cannot be inferred.
- Treat the working tree as dirty and user-owned; inspect before editing; never `git add`/`commit`/`stash`/`restore`/`checkout`/reset/clean unless explicitly asked — git is handled externally.
- A request to review/diagnose does not authorize implementation; implementing does not authorize Speed submission; preparing SLURM files does not authorize submitting them.
- Delegation to external LLM executors (Codex, Antigravity, fresh Sonnet agents) is authorised by standing rule for implementation slices; this manager session plans, audits, and dispatches — it does not write feature code.
- `measure → decide → plan → execute` for high-impact changes; never remediate a baseline while measuring it; never tune a model toward an expected narrative.

## Documentation and handoff conventions

- One live director prompt at `prompts/`, alongside the live `PROMPT_*`/`EXECUTOR_*` executor prompts for the
  plan in force; superseded versions of either move to `prompts/previous/` (never deleted). One executor prompt
  per dispatch slice, self-contained and paste-able, ending in an explicit stop-and-report.
- After every material result, update in the same pass: this prompt's current-moment box,
  `content/walkthrough_progress_log.csv` (append-only, one row per material attempt including failures),
  a decision record under `debugs/docs/` when authority is missing, and
  `docs_EXPLANATION/OpenUBEM_debug_References.md` for any solved error (house format).
- Never paste raw logs into planning docs — summarize with paths/hashes/decisive excerpts.
- Every handoff states: repo revision + dirty-tree caveat, active work package, what changed, exact
  verification commands/outcomes, evidence paths, any jobs submitted and their states, unresolved
  decisions, and the single recommended next action.

## Definition of done (this arc)

Done only when: all 102 `ES`/`GB`/`IT` archetypes + the France physical registry are sourced and
provenance-audited; non-residential exclusions are proven absent from manifests; `N1`/`N2` sites are
accepted under `NS-01`–`NS-10`; geometry/envelope/mass/HVAC/weather decisions are explicit and tested;
`GEO-01`–`GEO-10` and the S0–S3 ladder have observed outcomes; the external schedule path incl. `f=0`
is independently verified; held-out-fold and weather alignment are proven; all required campaigns
(Q0, S0–S3, Q1–Q4, `G8.0`, `FR-B`) completed in order with retained evidence; all 510 expected cases
are accounted for including failures; `G8.0`–`G8.16`/`V8.a`–`V8.g`/mutation suite have observed
outcomes; accounting is reconciled without double-counting; headline results are independently
recomputed; the dossier is reproducible from manifests/commands/outputs; and every living document
(this one included) describes the achieved state, not the intended one. France occupant schedules stay
visible as `FR-OCC-FUTURE` and are never reported as implemented.

## Fresh-session checklist

1. Read this file's current-moment box, then `STATE_european_locations_v3.md` and
   `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
2. Check `git status --short` / `git diff --stat` — preserve unrelated dirty work, never touch it.
3. Confirm nothing is running (Speed queue, background agents) before assuming a prior session's state.
4. Resume the first unblocked action named in the current-moment box — normally the next undispatched row of
   the item-0b table (today: check `D-EU-47`/`D-EU-48` drain status — jobs `1303039`/`1303023` — and dispatch
   the harvest half of each once drained; T10 is next after both fold in). Dispatch the prompt as-is; do not
   rewrite it into the message. Stop and ask only on a genuine authority conflict or spec ambiguity — quote it,
   never invent a resolution.
5. When this file is done being read, consult `prompts/previous/DIRECTOR_PROMPT_european_locations_2026-08-30.md`
   only for a specific cited `D-EU-NN`/`FINDING NNN` — never re-read it wholesale.

---

## Slice ledger (fresh — close this doc again once it re-exceeds ~1,000 lines, same procedure)

- **2026-08-31 — `D-EU-42`–`D-EU-48`: T09 harvested, Madrid/Lyon/London recovered, Bologna/Lyon-timeout waves
  running.** `D-EU-42`/`D-EU-43` `FINDING 210` fix wave harvested (Madrid 98→2, Lyon 26→0, London 2→0
  failed); `D-EU-44` recovered Madrid's last 2 stems (961/961, 0 failed). `D-EU-45`/`D-EU-46`
  classified Bologna's 177 `FAILED` (all bucketed under the existing gate) and Lyon's 9 `TIMEOUT`s (genuine
  wall-clock, no defect). Owner authorised both remediations *"oui j'autorise, vas-y"*: `D-EU-47` shipped 176/177
  Bologna stems (job `1303039`, 1 excluded pre-ship, disclosed); `D-EU-48` resubmitted Lyon's 9 stems at 3h
  walltime (job `1303023`). Both running, neither harvested. Director prompt updated same day to reflect this
  (was still reading `D-EU-42`-era/2026-08-30 state). Next free `D-EU-49`/`FINDING 211`.
- **2026-08-30 (evening) — `EU-15` + `EU-16A` executed, `EU-16B` submitted.** T01–T08 done and audited;
  four Speed arrays live (1299912 / 1299945 / 1299946 / 1299947, 2,544 tasks); `FINDING 210` recorded
  (circulation-ring vertex-size mismatch kills ~8 % of tasks at input processing); three executor prompts
  filed to `prompts/previous/`; monitoring delegated to a 30-minute haiku agent by owner instruction.
  **All four district EUIs stay barred from quotation.**
- **2026-08-30 — v3 opened, `EU-15`/`EU-16` planned and packaged.** `D-EU-39`/`D-EU-40` ruled; `FINDING 207`–
  `209` recorded; `STATE`/`BRIEF` v3 written and `STATE_european_locations_v2.md` frozen to `previous/`; plan
  `PLAN_eu15-eu16-zoning-context-2026-08-30.md` written; five executor prompts written (item 0b); three image
  prompts + renders at `prompts/images/`. **Nothing executed yet — T01 is the next action. All four district
  EUIs stay barred from quotation.**
