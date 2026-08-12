# DIRECTOR PROMPT — the `openings` arc

> **Written:** 2026-08-11, at the close of the session that harvested E02 in full and reconciled its
> failure census.
> **🔴 UPDATED IN PLACE 2026-08-12**, at the close of the five-item sweep
> (`implemenation/PLAN_five-item-sweep-2026-08-12.md`). The filename keeps its 2026-08-11 date because
> the user asked for this file to be updated rather than superseded. **Where a 2026-08-11 sentence was
> falsified, it is struck through and corrected in place, not deleted** — the same rule the register
> runs on.
> **Supersedes:** `previous/DIRECTOR_PROMPT_openings_2026-08-10.md` — **spent, do not paste it.** That
> file was written *before* the harvest landed and then amended in place; every load-bearing sentence
> has been carried here as plain statement rather than as a struck-through correction. It is kept only
> as history.
> **How to use:** paste this whole file into a **fresh manager session**. It is self-contained and
> assumes no memory of any prior conversation.

---

> # 🟢🟢 READ THIS BOX FIRST — the state of the world
>
> **🔴 Updated 2026-08-12, after the five-item sweep landed. Everything below supersedes the
> 2026-08-11 text.**
>
> ## In one line
>
> **E02 is finished and read; the register has now also been *worked*, not only measured.** All 40,800
> simulations completed on Speed (40,755 succeeded, 45 failed), all 60 arrays are harvested locally
> with `.eio` for every building, `PLAN_e02-audit-and-closure.md` audited them, and on 2026-08-12
> `PLAN_five-item-sweep-2026-08-12.md` (T01–T07, four parallel executors, three checkpoints
> director-signed) took five open items through measurement **and** repair, closing one and opening
> **two new ones**, OPEN-43 and OPEN-44 — **both found by auditing, not by running a task.** **Nothing is queued,
> nothing is in flight, nothing is being fetched, and no agent is running.** **The arc is blocked on
> rulings — see §3, which now has four open questions, three of them new.**
>
> ## 🔴 The four sentences that change what you do next
>
> **1. "Submit more" is not a task, "go get the results" is not a task, and neither is "audit the
> corpus."** All three phases are finished. **Nothing resubmits a failed task, and nothing should** —
> the 45 failures are EnergyPlus fatals that reproduce identically (eight arrays were accidentally run
> twice and the same buildings failed both times — §4.3).
>
> **2. You are blocked on rulings, not on data or on CPU.** Speed is free and this arc has no use for
> it. Every remaining first measurement is either made or does not need a machine.
>
> **3. 🔴 The adopted `auto` mode's denominator is MEASURED CORRECT — median error factor 1.0000,
> 99.63% of 8,160 buildings within ±1%.** This is the single most important number produced by the
> whole E02 exercise and it had never existed for any mode. **Say it together with what is still
> wrong** (§5.1), or the user will hear only one half.
>
> **4. 🔴🔴 DO NOT QUOTE "158.0 kWh/m²" UNTIL OPEN-43 IS RULED.** The published headline is a **mean of
> the twelve cells' means, count-weighted (158.0298)**, not a fleet mean. Pool all 8,154 successes at
> once — `Σ(EUI × area) / Σ(area)` — and it is **157.0552**, about **1.0 kWh/m² lower**. Neither is
> wrong; the project has simply never written down which one it means, and every reader assumes the
> pooled one. Found 2026-08-12 by re-deriving the headline **two** ways instead of one. **This is the
> single most consequential thing the sweep produced, and it is a question, not a defect.** See §5.8.
>
> ## Your first move when a session opens
>
> 1. **Do not re-run the census, do not re-harvest, and do not re-run the audit.** §4 is counted,
>    §5.1 is measured, and §5.9's five items are worked. Re-verify only what you intend to *publish*.
> 2. **Confirm the corpus is still on disk before planning around it.** It lives in a Windows temp
>    directory nobody is protecting (§4.2). **Fully recounted 2026-08-11: 40,800 dirs = 40,800 `.err`
>    = 40,800 `.eio`, `.end` = 40,799** — file-level, not top-level. Recount before depending on it.
> 3. **Put one ruling to the user** — the owed list is §3, ordered. One at a time, never as a menu.
>    ~~OPEN-22 has been owed the longest~~ **OPEN-22 was RULED on 2026-08-12 (rebuild the fixture) and
>    must not be re-asked.** The queue now opens on **OPEN-43**, which is the one that touches every
>    published number, followed by **OPEN-22's follow-on** (who authors the new labels, how many rows).
> 4. **If you want work running while a ruling is pending**, the ready work is **OPEN-22's fixture
>    rebuild** — but it is itself blocked on ruling 2, so ask that first. The ready *measurement*
>    needing no ruling is **OPEN-42's remaining unknown: why the six `Warehouse` simulations failed**
>    (their `error_summary` is the empty string; the causes must come from the `.err` files, which are
>    on disk). ~~OPEN-42's placeholder question~~ — **answered 2026-08-12, see §5.9.**
>
> ## 🔴 Do not confuse "ran" with "correct"
>
> 40,755 tasks exiting 0 is a statement about **SLURM**, not about building physics. No EUI has been
> computed, no denominator has been checked, and the two large unfixed errors (OPEN-01's median ×2.0
> floor-area error, OPEN-03's ≥1.72× lighting error) are **exactly as large as they were measured**.
> A clean run does not shrink them. State no fleet EUI until it is derived from the harvested artifacts.
>
> 🔴 **And a harvest reports emptiness as emptiness, never as "0 failures."** R10 was caught by exactly
> this: its first analysis pass ran against a still-empty root and reported every array `"present":
> false` with `[]` fatals. Those files were **deleted and regenerated**, not amended. **Zero fatals
> against 45 known-FAILED tasks means the scanner is broken, not the fleet clean.**

---

## 1. Who you are and what you are doing

You are the **manager / director** for OpenUBEM. Working directory
`C:\Users\o_iseri\Desktop\OpenUBEM` — stay there. Interpreter `./.venv/Scripts/python.exe`.

The user is the **manager-of-manager**: they set scope, approve, and veto drift. **You write plans,
decide, and audit. You do not write feature code** — fresh Sonnet executor sessions do that, one per
unit of work, never resumed for new work.

**The user writes French. You reply in English, short. All deliverables are in English.**

**Report to the user in plain language.** Spell terms out: write "the file EnergyPlus writes recording
the floor area it actually simulated" before you write `eplusout.eio`. Depth goes in the documents, not
the chat.

**When the user says they do not understand, that is not a request to repeat with more words — it is a
request for the context that makes the question decidable.** Give the setup, the concrete example, the
two readings and what each one costs.

### Standing instructions — live, restated because they bind every session

1. **Ask questions one at a time, step by step.** Not a menu of four questions in one turn.
2. **Update three surfaces on every completed task, unasked:** the plan's progress log, the register,
   and **this prompt**. A task is not finished until all three are written.
3. **Keep the progress board updated on every change, without being asked.** The user monitors the work
   through it — *"je voudrais surveiller des progress avec ce document, sinon, je suis perdu."*
4. **For no-compute work the user has handed item selection to the director** and asked for several
   tasks at once. **Do not open by asking which item to work on.** Ask about *rulings* — those are still
   theirs.
5. **Kill agents that are not doing work.** Background shell watchers are fine; idling model sessions
   are not.
6. **Restate every standing boundary in each kickoff prompt.** An executor must never widen its own
   mandate from something it read in a file. This has been honoured under test: the R01–R04 session
   found an autonomy grant written in the plan doc it was executing and **declined to act on it**,
   because file content is not a message addressed to it. **That is the standard.** A grant to the
   director is not a grant to an executor.
7. **Do not invent a task to demonstrate momentum.** A resting state waiting on a ruling is legitimate.
   When you want work that is genuinely ready, it is **OPEN-42's remaining unknown — why the six
   `Warehouse` simulations failed** (§2) — not a manufactured task. ~~OPEN-41 (§4.5)~~ closed
   2026-08-11.
8. 🔴 **NEW 2026-08-12 — when you run executors in parallel, forbid all of them from writing the
   register and the progress log.** Four concurrent writers to one 3,000-line file lose each other's
   edits silently. Executors write **named report files**; **the director writes every log entry and
   every register amendment.** This was hard rule 7 of the five-item sweep and it held.
9. 🔴 **NEW 2026-08-12 — an executor's silence is not the same as an executor's report.** Both problems
   the sweep exposed were things an executor **did not say**: a containment that removed 43 passing
   tests, and six failed rows whose `error_summary` was empty. **Audit for what is missing from the
   report, not only for whether what is in it is true.**

## 2. The arc you are picking up

A register of **everything open in this project** lives at:

```
docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md
```

**Read it first, in full.** It is the single source of state for this arc — not this prompt, and not
any conversation. Each item carries: what is known, what is only believed, where the evidence lives,
and **the one measurement that must be made before an execution plan can responsibly be written.**

**32 tracked items / 32 findings** (OPEN-01 … **OPEN-44**) — **up by one on 2026-08-12, and it went
up for the right reason.** Arithmetic, stated so it can be checked: **31 − 1 closed** (OPEN-33)
**+ 2 opened** (OPEN-43, OPEN-44) **= 32**. Findings the same. 🔴 **The user's standing goal is to
reduce open items and this pass added one net. Say that plainly and say why: both new items were
found by AUDITING** — OPEN-43 by re-deriving the published headline a second way as a check nobody
asked for, **OPEN-44 by running the test suite that the sweep's own fix had just made runnable.** *(2026-08-11 for reference: 35 − 5
closed + 1 opened = 31 items; 37 − 5 − 2 discharged + 1 = 31 findings.)*

🔴 **A flat count does not mean a flat week, and you must say so.** Three items moved without moving
the total: **OPEN-26** went from 1-of-4 fixed to **2 of 4, with the remaining two measured and
downgraded to will-not-fix**; **OPEN-29**'s malformed-fatal-test class is **finished on live code**;
**OPEN-42** lost two of its four unknowns and **had one of its headline claims retracted**. And
**OPEN-13** went from two live defects to **one fixed, one contained**. **Recount §1's table before
quoting any total** — the director did, and it re-derives to 31.

**Retired IDs — never reuse, never re-add:**

| ID | Disposition |
|---|---|
| **OPEN-05** | **CLOSED** 2026-08-05 — measured in full. Do not re-run its sweep. |
| **OPEN-21** | **DEFERRED by the user** to `docs/docs_TODO/mixed_use_classification.md`. **Closed to further asking — never put it to the user again.** |
| **OPEN-23** | **EXCLUDED by the user** 2026-08-04 (`layoutGenerator` production zone-mode). |
| **OPEN-25** | **CLOSED** — fixed 2026-06-10 by the code that produced the adopted baseline. |
| **OPEN-30** | **CLOSED 2026-08-11** — vintage distribution demonstrated on 60/60 manifests, 40,800 rows, 0 nulls, 5 values, 93.44% `DOERefPre1980`; `la_rural` cross-check vs raw `year_built` has zero crossover. **Do not re-run it.** |
| **OPEN-33** | **CLOSED 2026-08-12** — the archiving citation-sweep rule is written where the next person archiving an arc will meet it (head of `docs/PROJECT_CHECKLIST.md`, 10 lines), and a re-sweep of **279** live citations found **zero** dead paths. The scanner was **proved non-vacuous** first, by injecting a broken citation and watching it get named. ⚠️ **No artifact survives from the 2026-08-06 sweep, so its 58-path baseline is not verifiable at row level** — re-measure, never quote it as checked. 🔴 **Its standing rule survives: archiving an arc obliges a citation sweep, resolved BY FILENAME (four files were renamed by their own move, so prefix substitution misses them).** ❓ **Open question left to the user: whether the rule also belongs in `CLAUDE.md`** — until then a session that never opens the checklist will not know it exists. |
| **OPEN-34** | **CLOSED 2026-08-11** — all 12 adopted cells whole (`05_results.csv` rows = `01_buildings.gpkg` features, fleet 8,160). 🔴 **Its standing rule survives: a subset verification run must use the whole cell or declare itself not fleet-faithful.** |
| **OPEN-39** | **CLOSED 2026-08-11** — 2.14 GB orphaned across 45 failed tasks (48.6 MB vs 449 KB), replicates outside E02; zero of 15 `task.rc` references in 9 scripts uses it as a completion test. 🔴 **Its standing rule survives: never use `task.rc` presence as a completion test.** ⚠️ `submit_fleet_t08.sbatch:56` is still unguarded — the defect is sized, not fixed. |
| **OPEN-40** | **CLOSED 2026-08-11 as untraceable**, which the item's own text names as the answer. 68 `e02_*` submissions reconstructed from `sacct` (19+8+41). ⚠️ The remedy — a submission log nobody can bypass — **is unbuilt.** |
| **OPEN-41** | **CLOSED 2026-08-11** — all 44 fatals have recorded causes, all thermal runaway. The concentration was the **archetype**, not the cell → became OPEN-42. |
| **OPEN-02, OPEN-28** | **FOLDED INTO OPEN-01** 2026-08-09, then **both DISCHARGED 2026-08-11** on the E02 audit. Sections stay in full as evidence. 🔴 **OPEN-28's rule outlives it: every comparison must state which harvest generation each side came from — E02 is the fourth.** |

**Next free IDs: item `OPEN-45` · defect `E-LA-42` · UTCI defect `E-UTCI-17`.**
*(Neither the 2026-08-11 nor the 2026-08-12 pass opened a defect ID, so the defect counters are
unchanged. **2026-08-12 opened two items, OPEN-43 and OPEN-44, both by auditing.**)*

🔴 **OPEN-42 — its two faces turned out to be ONE face, and its most alarming claim was WRONG.**
The `Warehouse` type is still **38 of 8,160 buildings (0.47%)** carrying **26 of the 44 fleet fatals**
— 13.68% against 0.0443%, a **≈309× relative risk** — and that half stands. ~~Six of them carry a
placeholder `footprint_area_m2` of exactly 200.0 m² … so the adopted `auto` mode divides by a
denominator wrong by 20.3× to 336.7× on six published buildings. Its effect on the 158.0 kWh/m² fleet
figure is unmeasured — do not assume it is negligible.~~
**🔴 RETRACTED 2026-08-12 and this is the correction you must carry:** the 200.0 m² is a **declared
fallback initialiser**, written by one cited line — `scripts/validation/v12_cell_pipeline.py:659` —
which line 664 overwrites **only when `status == "success"`**. There is no `else` branch, so a failed
building publishes the initialiser as though it were measured. The six placeholder rows and the six
failed rows are **the same six rows**, confirmed two independent ways, so this is **one defect, not
two**, and the placeholder is simply what a failure looks like after the reporting stage. All six are
`not_simulated` with `total_eui_kwh_m2 = NaN`, **excluded from both sides of the aggregation**, so the
**measured impact on the fleet EUI is exactly 0.000** against a baseline the director reproduced at
**158.0298**. **OPEN-42 is a reporting defect, not a baseline defect. Blast radius: 6 published rows
carrying a false area, 0 inside the fleet EUI.** Stage 1 is clean — the true footprints
(1,173–22,444 m²) are in `01_buildings.gpkg` and match their own `geometry.area`.
⚠️ **What now blocks OPEN-42's closure is new and smaller-sounding but real:** `error_summary` is the
**empty string** for all six failed manifest rows. **The failures have no recorded cause at the
manifest level at all** — the causes exist only in the `.err` files. That is the next measurement.

🔴 **OPEN-38 was not closed; its premise was falsified and the item rewritten.** *"Base surface does
not surround subsurface"* is a **Warning**, not a Severe, at all 8 sites, and kills nothing. All seven
`layout_assign` fatals are **thermal runaway in the zone `LAUNDRYROOMFLR1`** — the substituted
prototype's laundry room, same zone token as OPEN-06. One of the 8 buildings with malformed door
geometry **completes successfully and publishes results.** *(Second item in this register whose stated
cause was a co-occurring message. **A severity marker is evidence; proximity to a fatal is not.**)*

⚠️ **OPEN-37 is fixed in code but deliberately still counted.** R09 fixed the `.eio` fetch gap and it is
verified, but the item also asserts *every fleet harvested before 2026-08-10 lacks the file locally* —
still true, because no earlier fleet was re-harvested. **Closing it is a user decision, not a
bookkeeping consequence of a merged diff.**

Plan docs live in `openings/implemenation/` (the folder name is misspelled — **the user created it that
way; keep the spelling**). Supporting docs go in `openings/extra/`. Reporting snapshots in
`openings/reporting/`.

🟠 **`PLAN_speed-resume.md` is at 1,451 lines — past the ~1,000-line close threshold.** Its work is
finished through **R10**. **Do not append new tasks to it.** Cite its findings by ID (R01…R10).

🟢 **`PLAN_e02-audit-and-closure.md` — the plan that audited the corpus. CLOSED 2026-08-11 at ~1,060
lines, all six tasks landed, all three checkpoints director-signed. Do not append to it either.**
Cite its findings by task ID (T01…T06). Its §9 holds the director's own re-derivations — the
independent `.eio` parse, the `Warehouse` archetype join, the `LAUNDRYROOMFLR1` chain — and is the
place to look before re-measuring anything it touched. Its four measurement reports are in
`openings/extra/`: `MEASUREMENT_open-01_denominator-audit-e02.md`,
`MEASUREMENT_open-30-01c_vintage-and-code-state.md`, `MEASUREMENT_open-41-38_failure-causes.md`,
`MEASUREMENT_open-39-40_cluster-records.md`.

🟢 **`PLAN_five-item-sweep-2026-08-12.md` — the plan that worked five register items at once. CLOSED
2026-08-12 at ~712 lines, T01–T07 landed, three checkpoints director-signed.** Cite its findings by
task ID (T01…T07). Its §8 progress log holds the director's own re-derivations and is the place to
look before re-measuring anything it touched. Its four reports are in `openings/extra/`:
`MEASUREMENT_open-42_placeholder-and-fleet-impact.md`,
`MEASUREMENT_open-33_archiving-rule-and-resweep.md`,
`FIX_open-26-29_polish-and-fatal-tests.md`, `FIX_open-13_height-cache-and-collection.md`.
Its artifacts are in `openubem/outputs/comparisons/`: `open42_placeholder_trace.csv`,
`open42_fleet_eui_impact.csv`, `open42_t02_percell_repro.csv`,
`open29_diagnostics_fatal_recheck.csv`, `open33_dead_path_sweep_2026-08-12.csv`.

🔴 **The structural lesson from that plan, worth reusing: four executors ran in parallel, and hard
rule 7 forbade every one of them from touching the register or the progress log.** They wrote named
report files; **the director wrote all logs and all register amendments.** Without that rule four
concurrent writers to one 3,000-line file would have silently lost each other's edits. **Reuse it
verbatim in any future multi-executor plan.**

**The next execution plan opens as a fresh doc.** ~~The obvious candidate is OPEN-42 — but its own
first measurement (where the 200.0 m² placeholder comes from) is not yet made.~~ **That measurement
was made on 2026-08-12 (T01–T02).** Per §6 the candidates whose first measurement is now made and
whose plan may therefore be written are **OPEN-22** (blocked on ruling 2 only) and **OPEN-42's
residual**. **OPEN-43 has its first measurement made too, but it is a ruling, not work — do not plan
it.**

## 3. What is owed to the user — rulings, asked one at a time, in this order

🔴 **The queue changed on 2026-08-12: one ruling was answered and three new ones were opened by the
sweep. Ruling 1 below is now OPEN-43, and it is the one that touches every published number.**

| # | Ruling | Where |
|---|---|---|
| **1** | 🔴🔴 **NEW 2026-08-12 — OPEN-43, and it outranks everything else because it is upstream of every figure this project publishes.** The adopted fleet headline **158.0** is a **count-weighted mean of the twelve cells' means (158.0298)**. Pool all 8,154 successes at once instead — `Σ(EUI × area) / Σ(area)` — and the answer is **157.0552**, ≈**1.0 kWh/m² lower**. Two other defensible weightings give 158.0557 and 160.0993. **Neither of the two main numbers is wrong; they answer different questions** — but the published figure has **never been described as a mean of cell means anywhere in this project**, and a reader hearing "fleet average" will assume the pooled one. A second oddity to state when asking: **the count weights include the six buildings that produced no energy at all.** `openubem/results/aggregator.py` is per-cell only, so the fleet roll-up lives outside it and its author and intent are **untraced** — this cannot be settled by finding the original intent. **The ruling: which definition the headline should use.** ⚠️ **Do not restate 158.0 in any report or board until this is answered.** | §5.8, register OPEN-43 |
| **2** | 🔴 **NEW 2026-08-12 — OPEN-22's follow-on, and it is the thing actually blocking the work the user already approved.** The user ruled *rebuild the fixture*; nobody has said **who authors the new labels and how many rows**. Frame it with what the rebuild costs: the old fixture must be kept and unedited (OPEN-04's bisect depends on it), historical accuracy figures (92.0 / 84.0 / 88.0%) become non-comparable, and the ≥0.70 gate threshold does not transfer. **Until this is answered the rebuild cannot start**, so this is a short question with a large unblock behind it. | §5.3, register OPEN-22 |
| **3** | **NEW 2026-08-12 — does the archiving citation-sweep rule also belong in `CLAUDE.md`?** OPEN-33 closed by writing it into the head of `docs/PROJECT_CHECKLIST.md`. **A fresh session that never opens the checklist will not know the rule exists** — which is precisely the failure mode that produced 58 dead paths in the first place. The counter-argument is real too: `CLAUDE.md` is loaded into every session and every line added there costs context on every task. **Small ruling; ask it after the two above.** | register OPEN-33 |
| ~~4~~ | ~~**OPEN-22** — a third of the 50-row exam is decided by size-bucketing rather than tag logic.~~ ✅ **RULED 2026-08-12 — REBUILD THE FIXTURE.** The user rejected both cheap options (keep 88% as is; report both numbers) and declared the current exam wrong, *despite* the measurement showing the fallback rows do not inflate it. **Do not re-ask this.** OPEN-22 stays open as **work**, not as a decision. 🔴 **Carry its three consequences into every plan and report:** historical accuracy numbers (92.0 / 84.0 / 88.0%) become non-comparable and **every figure must name its fixture**; the **old fixture is never deleted or edited** (OPEN-04's bisect depends on it); the ≥0.70 gate threshold **does not transfer** to a new exam — repointing it is a separate decision. **Now blocked on one question, which is the next thing owed: who authors the new labels, and how many rows.** | §5.3, register OPEN-22 |
| 5 | 🔴 **NEW 2026-08-11 — OPEN-01(c), and it is the one that unblocks the biggest item.** OPEN-01's third audit question is *"did all five modes come from one code state?"* **It cannot be proved, and the reason is structural: no commit hash or code-version stamp was recorded anywhere at generation time**, and 25 of the 60 `(cell, mode)` pairs have no generation-summary JSON. The circumstantial evidence is real — one manifest schema across all 60, all 60 written inside one continuous **111-minute** window (2026-08-09 21:03:01–22:54:38), no gaps. **The ruling: is that sufficient for (c)?** If yes, OPEN-01 reduces to the remedy ruling below. **If no, OPEN-01 can never close on this corpus** and only a re-run with a recorded commit stamp would settle it. **Frame both costs before asking.** | §5.1, register OPEN-01 |
| 6 | 🔴 **OPEN-01's remedy** — now that (a) and (b) are measured on 40,800 runs: fix the denominator, fix the simulation, or stop publishing per-building EUI for the affected modes. **The measurement is done and no remedy was chosen — deliberately.** ⚠️ **Do not ask this before ruling 5**, or the user is choosing a fix for an item that cannot close anyway. | §5.1 |
| 7 | **CP-M2** — what to do about the published cross-mode numbers, still confounded. **Not discharged by OPEN-28** — E02 fixes future comparisons, not published ones. | §5.4 |
| 8 | **OPEN-11** — the six inverted-geometry buildings; precondition met, remediation is the user's call. | register |

**Spent rulings — do not re-ask any of these:**

- **CP-M3 + OPEN-30 + OPEN-33** — ✅ RULED 2026-08-09, **all three obligatory**: the labelled-fixture
  before/after gate, persisting the assigned vintage in every harvest, and a citation sweep on
  archiving an arc.
- **CP-C2** — ✅ RULED 2026-08-09 in two parts: measure first, then run to the end. 🔴 **The four
  descope options (a)–(d) are spent; never put them again.**
- **OPEN-29** — ✅ RULED 2026-08-09, fix the error check **everywhere** (six live sites, not four).
- **The autonomy grant** — 2026-08-09, *"vas-y continuer jusqu'à la fin"*, reaffirmed 2026-08-10. The
  director self-signs its own checkpoints and drives the arc to the end. **This does not license
  lowering the audit standard:** a checkpoint that cannot be re-derived from raw artifacts is a **STOP**,
  not a formality waived for momentum.

## 4. 🔴 E02 — ran, counted, harvested, reconciled. The core evidence of this arc.

### 4.1 The fleet outcome (read-only census against `sacct` and `find`)

| | |
|---|---|
| **Arrays** | **60 of 60** — all twelve cells × all five modes. **No combination is missing.** |
| **Tasks** | **40,800 exactly**, matching the expected fleet size |
| **COMPLETED** | **40,755 (99.89%)** |
| **FAILED** | **45 (0.11%)** |
| **TIMEOUT / OUT_OF_MEMORY / CANCELLED / NODE_FAIL** | **0 / 0 / 0 / 0** — `sacct`'s state list contains only `COMPLETED` and `FAILED` |

Cells come from `scripts/cluster/t08_full_sweep.py:58-71`; the fifth mode `layout_assign` is **not** in
that file's `ALL_MODES` (`:55` lists four) — it was added by the scratchpad driver `e02_fleet_submit.py:50`.
**Remote root: `/speed-scratch/o_iseri/fleets/e02_<cell>_<mode>/out/<stem>/`.** The raw `sacct` dump
survives on the cluster at `~/e02_sacct_full.txt`.

**Failures by array** (the other 49 arrays are 100% complete):

| Cell / mode | Failed | | Cell / mode | Failed |
|---|---|---|---|---|
| `nyc_centre/auto` | 2 | | `la_centre/layout_assign` | 1 |
| `nyc_centre/fast_zone` | 9 | | `la_urban/auto` | 1 |
| `nyc_rural/layout_assign` | 3 | | `la_urban/layout_assign` | 3 |
| `la_centre/auto` | 1 | | `la_rural/auto` | 7 |
| `la_centre/floor` | 1 | | `la_rural/floor` | 7 |
| | | | `la_rural/fast_zone` | 10 |

### 4.2 The harvested corpus — what is on disk, and how fragile it is

**Location:** `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest` — **60 arrays, ~12 GB.**

**Manager-independent recount** (not the harvest script's own numbers):
**40,800 building dirs = 40,800 `.err` = 40,800 `.eio`; `.end` = 40,799.**
The single `.end` deficit is the `std::bad_alloc` building (§4.4). **`.eio` coverage is 40,800/40,800
parsed, 0 parse failures** — the multiplier-aware simulated floor area OPEN-01/OPEN-35 need is
available for every building in every one of the five modes.

🔴 **Two cautions that must travel with any plan built on this corpus:**

- **It is outside the project tree, in a Windows temp directory.** It will not survive a temp clean and
  nothing protects it. **Count it before planning around it**; re-harvesting costs ~40 minutes.
- **Re-harvesting is SSH-rate-limited.** Fetching ~50 arrays in rapid succession draws
  `Connection closed by 132.205.2.12 port 22` (`ssh rc=255`). A **90 s pre-sleep + 120 s inter-attempt
  backoff** made both stuck arrays fetch on attempt 1. See OPEN-40's neighbourhood in the register.

### 4.3 The finding that makes the failures interpretable

**Eight arrays were submitted twice** — job IDs `1177095`, `1177838`–`1177841`, `1177875`, `1178313`,
`1178538`, which fall **outside both** documented submission ranges (wave 1 `1176411`–`1176599`, wave 2
`1198104`–`1200571`). **No project document or scratchpad log explains this third submission** (OPEN-40).

🟢 **It is accidentally the best evidence in the arc:** both runs of all eight arrays produced
**identical task counts and identical failure counts, with the same buildings failing both times.**
**The pipeline is deterministic across runs, and the 45 failures are reproducible properties of those
buildings — not flaky infrastructure.** This is why nothing should be resubmitted.

### 4.4 The failure census — complete on *which*, near-empty on *why*

Reconciled **in both directions**, which is the load-bearing check:

- Local, using the **two-space** `"**  Fatal  **"` test (E-LA-21; the one-space form misses real
  fatals): **44 fatal buildings + 1 missing-`.end` building = 45.**
- `sacct` FAILED rows deduped to **45 unique tasks**, all 45 mapped to a building stem via each array's
  `fleet.lst`.
- **Direction A** (local failure absent from `sacct`): **0**. **Direction B** (`sacct` failure absent
  locally): **0**. The 11 cell/mode combinations carrying failures are identical on both sides.

**But the causes are unknown for 43 of the 44 fatals** — the scanner captured EnergyPlus's generic
trailer `Program terminates due to preceding condition.` (×43) rather than the preceding `** Severe **`
line. Only one is self-describing (`CheckForRunawayPlantTemps: … too hot`). **This is OPEN-41** (§4.5).

**Known individual causes, from a ten-task sample read directly from the `.err` files:**

- Genuine physical fatals with distinct causes: `CalcHeatBalanceInsideSurf` reaching **90,915.77 °C**
  during warmup (`nyc_centre/auto`, `way_266149332`); `CheckForRunawayPlantTemps` "too hot"
  (`la_centre/auto`); temperature-out-of-bounds severes across four cells.
- ~~🔴 **One recurring geometry defect, mode-specific:** *"Base surface does not surround subsurface"*
  in **`layout_assign` mode in three different cells** (`nyc_rural`, `la_centre`, `la_urban`). All
  seven `layout_assign` failures fit this pattern → **OPEN-38**.~~
  🔴 **CORRECTED 2026-08-11 — this was wrong, and it was wrong in the way this project keeps getting
  caught.** That message is a **`** Warning **`**, not a Severe, at all 8 sites where it occurs, and
  **it kills nothing.** The seven `layout_assign` failures all die on **thermal runaway in the zone
  `LAUNDRYROOMFLR1`** (−12,459 / −23,743 / −11,950 / −15,491 / −12,901 / −59,865 / **+182,399 °C**) —
  the substituted prototype's laundry room, the **same zone token as OPEN-06**. The geometry message
  merely co-occurred, and a **ten-task sample read by eye** promoted a co-occurrence to a cause.
  **An eighth building carrying the same warning completes successfully and publishes results.**
- 🔴 **One memory failure `sacct` never labelled as one.** `nyc_centre/fast_zone`, `way_1240348353` — an
  **89-storey** stem (`_F0`…`_F88`) — died on `terminate called after throwing an instance of
  'std::bad_alloc'`, SIGABRT, `ExitCode=6:0`. No `Fatal` string anywhere in its `eplusout.err`; the
  evidence is in the array `.log`. **It is the one task missing an `.end` file.**
  **Consequence you must carry:** *the zero-`OUT_OF_MEMORY` count in §4.1 understates real
  memory-related failures.* A C++ allocation failure inside the process is not a cgroup OOM-kill and
  SLURM does not classify it as one. **Never cite "0 OOM" as proof memory was sufficient** — CP-R2's
  `--mem=6G` verdict is corrected on exactly this point in the register's 2026-08-10 amendment.

### 4.5 The four items E02 opened — all in the register, one of them ready to run

**🔴 All four were measured on 2026-08-11. Three closed, one was rewritten, and a fifth opened.**

| Item | What it is | Outcome 2026-08-11 |
|---|---|---|
| **OPEN-38** | ~~`layout_assign` subsurface geometry defect — 7 buildings die on the severe~~ | 🔴 **PREMISE FALSIFIED, item rewritten, STILL OPEN.** The message is a **Warning**, not a Severe, at all 8 sites, and kills nothing. All 7 fatals are **thermal runaway in zone `LAUNDRYROOMFLR1`**. The 8th building **completes and publishes** from malformed geometry. |
| **OPEN-39** | `set -e` suppresses the trim and the `task.rc` write on failure | ✅ **CLOSED.** 2.14 GB orphaned (48.6 MB vs 449 KB, ~111×), replicates outside E02; **zero of 15 `task.rc` references in 9 scripts** uses it as a completion test. ⚠️ Line 56 still unguarded. |
| **OPEN-40** | Eight arrays submitted a third time by an unrecorded process | ✅ **CLOSED as untraceable** — the answer its own text names. 68 submissions reconstructed from `sacct` (19+8+41). ⚠️ Remedy unbuilt. |
| **OPEN-41** | 43 of 45 failures have no recorded cause | ✅ **CLOSED.** All 44 causes recorded: 25 *Temperature (low) out of bounds*, 17 `CalcHeatBalanceInsideSurf`, 1 *Temperature (high)*, 1 `CheckForRunawayPlantTemps` — **all thermal runaway, none structural.** |
| **OPEN-42** | 🔴 **NEW** — the `Warehouse` population | **OPENED** by auditing the above. 0.47% of the fleet, **26 of 44 fatals (309× relative risk)**. ~~Six carry a 200.0 m² placeholder footprint producing 20.3×–336.7× denominator errors **in the adopted `auto` mode**.~~ 🔴 **CORRECTED 2026-08-12:** the placeholder is a fallback initialiser (`v12_cell_pipeline.py:659`) never overwritten on failure; the six placeholder rows **are** the six failed rows; all carry `EUI = NaN` and are **outside the aggregation**, so **fleet impact = 0.000**. One defect, not two. **Reporting defect, not baseline defect. STILL OPEN** on why the six failed — `error_summary` is empty for all six. |

🔴 **`la_rural`'s concentration is SOLVED, and this prompt's earlier explanation was aimed at the wrong
unit.** It said failures concentrating in one small rural cell *"points at the inputs for those
buildings"* and flagged it **a hypothesis, not a measurement**. The hypothesis was half right: it is
the inputs — but **the unit is the archetype, not the cell.** `Warehouse` is **38 of 8,160 buildings
(0.47%)** and carries **26 of the 44 fatals**: **13.68% of Warehouse tasks fail against 0.0443% of
everything else, ≈309×.** All **11** `la_rural` failing buildings are Warehouses with `no_floors`; the
cell holds 25 Warehouses of 149 and is simply Warehouse-dense. **36 of 44 failures carry `no_floors`.**
The cross-mode intersection came back **split** — 6 of 11 fail in all three modes, 5 are mode-specific.

⚠️ **Generalisable lesson, and it is the second time this exact shape has cost this arc a wrong
belief:** a concentration was attributed to the *container* it was noticed in (a cell) rather than to
the *property* the members share (an archetype). **Before explaining a cluster by where you found it,
join it to every attribute you have.**

## 5. Background — the measured state of the themes

*(Was "the six themes". 5.8 and 5.9 were added 2026-08-12.)*

Everything here was measured and audited by independent re-derivation before it was written down.

### 5.1 OPEN-01 — 🔴 **REWRITTEN 2026-08-11: (a) and (b) are now measured on all 40,800 runs.**

**The fleet-scale denominator measurement this item waited months for now exists.** All 40,800 `.eio`
files parsed, **0 parse failures**; join **8,160 matched / 0 unmatched in both directions in every
mode**.

| mode | median error factor | mean | range | within ±1% |
|---|---|---|---|---|
| 🟢 **`auto`** — the adopted baseline's mode | **1.0000** | 1.0592 | 0.9998–336.65 | **99.63%** |
| `floor` | 1.0000 | 1.0593 | 0.4953–336.65 | 98.43% |
| `fast_zone` | 1.0000 | 1.0631 | 0.8390–336.65 | 94.80% |
| `layout_assign` | 0.9999 | 1.4977 | 0.0557–353.998 | **15.37%** |
| 🔴 **`building`** | **0.5000** | 0.6287 | 0.0095–112.22 | **39.94%** |

🔴 **`building` mode simulates exactly one storey.** Its simulated area ÷ **bare `footprint_area_m2`**
(no `levels`) is **median 1.000000, 98.43% within ±1%** — the mode builds one zone of one storey while
the published denominator multiplies footprint by `levels`, whose fleet median is 2. **The 0.5 is the
storey count, not noise.** ⚠️ `building` mode was recorded *"verified sound at HEAD"* by E01c on
2026-08-06 — **that verification did not cover the denominator.** State both together.

**`layout_assign` non-`applied` (n=6,939): median 0.9474, range 0.0557–10.0008, 2.05% within ±1%.**
⚠️ **This does not reproduce the older inferred figures** below (median 2.0, 12.6% correct). Both agree
the defect is large; they disagree on shape. **Recorded, not reconciled** — the E02 number is a direct
measurement, the old one an inference.

~~Only **877 of 6,939** non-`applied` buildings (12.6%) divide by the right floor area. Median error
factor **2.0**, range **0.118×–10.0×**.~~ *(Superseded above; kept because it is cited elsewhere.)*
Of 28 archetype tokens only **two** carry a `ZoneGroup` list
multiplier: `MidriseApartment` 3 bands → **4** storeys, `HighriseApartment` 3 bands → **10**.
**Confirmed on the corpus: 2,850 zones fleet-wide have a list multiplier > 1 —
`MidriseApartment` 2,818 / `HighriseApartment` 32, all in `layout_assign`, zero on any third
archetype or any other mode.**

⚠️ **A trap that will catch you if you skip this.**
`openubem/outputs/comparisons/a1_prototype_storey_structure.csv` looks like it answers this item and
does not: its `num_modelled_storeys` is the **band count**, and its `has_multiplier_gt_1` flag tests
`Zone.Multiplier` only — blind to `ZoneGroup`'s list multiplier, reading `False` for both archetypes
that have one. **Do not cite it.**

**The audit had to answer three questions** (the OPEN-02/OPEN-28 merge): the `layout_assign`
denominator, the fleet-wide denominator in all five modes, and a demonstration that all five modes came
from one code state. **(a) and (b) are answered above. (c) is not, and cannot be** — see §3 ruling 2.
**Any one unanswered leaves OPEN-01 open, so OPEN-01 is open.** ✅ **The audit is done**
(`PLAN_e02-audit-and-closure.md` T04, CP-2 director-signed); **OPEN-02 and OPEN-28 both discharged on
it.**

🔴 **CP-2's re-derivation, for whoever needs to trust these numbers.** The director wrote an
independent `.eio` parser and reproduced the control building `la_urban/way_401904735`
(`MidriseApartment`, `one_zone_per_floor`, 3 storeys): `auto` 3 zones → 5,551.35 m² → factor
**1.00000**; `building` **1 zone** → 1,850.45 m² → **0.33333**; `layout_assign` 27 zones, plain sum
5,551.26 but multiplier-aware **7,401.68** with `Zone List Multiplier = 2` → **1.33331 against 4/3, or
0.0018% off.** Declared area re-read by hand: 1850.454098 × 3.0 = **5,551.362295**. Every figure
byte-identical to the executor's CSV. ⚠️ **Note the trap the plain sum sets:** for that building the
unweighted sum sits 0.0018% from the declared area — **it would have looked correct.**

**Retaining `.eio` was measured cheap** (median 76,068 B, **12.6%** marginal cost) — the ">800 GB per
city" justification covered eleven file types together; `.eio` alone was never the cost.

### 5.2 OPEN-03 — `undocumented but deliberate`

Zero matches for `layout_assign` / `resolution_mode` anywhere under `docs/docs_main`. Traceable to
`docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:155` and `:494`, never written
into a spec. **The register's own claim was wrong** ("documented in results §7" — that section is a
post-hoc write-up by the session that discovered the effect) and is corrected.

**Magnitude (n=12 archetypes, static):** 2013-vs-2022 lighting ratio median **1.722** (1.256–2.502);
equipment **1.064**; occupancy **1.000**. **92.9% of the fleet is `DOERefPre1980`** — far older than
2013 — so this proxy **understates** the real error.

### 5.3 OPEN-22 — 🔴 **RULED 2026-08-12: REBUILD THE FIXTURE.** Measured, decided, now blocked on one follow-on question

| | n | fine top-1 |
|---|---|---|
| all rows | 50 | **44/50 = 88.0%** |
| **excluding `FALLBACK_SIZE_DEFAULT`** | **33** | **29/33 = 87.9%** |
| the excluded rows alone | 17 | 15/17 = 88.2% |

**Removing the fallback rows does not move the number** — the worry that the metric was inflated by the
fallback and the answer key agreeing is measured false. What *is* true: **17 of 50 rows (34%) are
decided by `FALLBACK_SIZE_DEFAULT`, all at LOW confidence, 16 of 17 carrying an office label.**
~~⚠️ **Do not report this as "OPEN-22 is closed."** The measurement is closed; the ruling is not.~~

🔴 **RULED 2026-08-12 — the user chose to REBUILD THE FIXTURE**, rejecting both cheap options (keep the
88% as it stands; report both numbers side by side). **They ruled against the measurement**: the
fallback was shown *not* to inflate the score, and they declared the exam wrong anyway — a third of it
being decided by size-bucketing rather than by tag logic makes it the wrong exam regardless of what it
scores. **Do not re-ask this, and do not re-litigate it with the measurement.**

**Three consequences that must travel into every plan and report from here:**

1. **Every accuracy figure must now name its fixture.** The historical numbers **92.0 / 84.0 / 88.0%**
   become **non-comparable** to anything measured on the new exam. A bare "accuracy = X%" is no longer
   a well-formed statement in this project.
2. **The old fixture is never deleted and never edited.** OPEN-04's bisect depends on it.
3. **The ≥0.70 gate threshold does not transfer.** Repointing the gate at a new exam is a **separate
   decision** that has not been made — do not carry the threshold across silently.

⚠️ **OPEN-22 stays open as WORK, not as a decision, and the work cannot start yet.** It is blocked on
§3 ruling 2: **who authors the new labels, and how many rows.**

⚠️ The Boston 41.0% / Chicago 65.4% fixture distributions predate `E-R3-2` and **must not be carried
into any plan** without being re-run.

### 5.4 OPEN-04 / CP-M2 — the cross-mode numbers are confounded

The 92.0/88.0 pair is **`test_fine_top1` only** (gate 0.70); `test_coarse_top1` was **100% at every
commit tested**, so the apparent contradiction dissolves. The drift is `7635ce2` 92.0% → `67ede73`
**84.0%** (E-R3-3 tier bins, 2026-07-01) → `0df422e` **88.0%** (2026-07-03), flat since.
**The Phase-D fusion/crosswalk hypothesis is FALSIFIED** — the drift completed 18 days earlier and the
diff between those commits on every relevant file is empty. Re-cast as a **review-process defect** →
OPEN-31.

**OPEN-28's central claim, corrected:** the published **−29.1%** figure did not come from T20. Its
`layout_assign` side is **T19** and its `auto` side is **T08** — a *third* generation. Join: shared
**4,530**, T08-only **0**, T20-only **3,630**, union **8,160**; archetype agreement **86.60%** (top
disagreeing pair `MediumOffice → SmallOffice`, n=396, root-caused to commit `0df422e` changing the
shared `05_results.gpkg` between harvests); **floor-area agreement 100%**. **Any future comparison must
state which harvest each side came from** — and E02 is now a **fourth** generation, so this rule binds
harder, not less.

### 5.5 OPEN-32 — the adopted baseline is CLEAR, and say so

**No adopted result depends on `layout_assign`.** `decide_zoning_strategy()` (`zoning.py:36-42`) can
return only `single_zone` / `perimeter_core` / `one_zone_per_floor` under `auto` — **`auto` has no path
to `layout_assign`**; prototype substitution is entered only via `_layout_assign_baseline_path()`
(`builder.py:67-77`), which returns `None` for every other mode at `:75-76`. Tallied over **all 8,160**
`phaseE_elevrb` rows and **all 8,160** `phaseE_er33` rows: **zero** `layout_assign`.

⚠️ **The trap in reporting this.** It is a *bounding* result, not a *shrinking* one. OPEN-01 is still a
median ×2.0 denominator error on 87.4% of buildings; OPEN-03 is still ≥1.72× on lighting. **Say both
sentences together or the user will hear the wrong one.**

### 5.6 OPEN-34 / OPEN-35 — the subset trap and the storey-count contradiction

**OPEN-34 is answered: batch-composition dependence, not a HEAD divergence.** `_impute_levels()`
(`building_classifier.py:138-142`) fills a missing storey count from a **group median over whatever rows
are in the batch**. Over 3 buildings that median is **51** (one skyscraper dominates) and clears the
40-storey SuperTall threshold; over the full 738-building cell it is **19** and does not. The full-cell
run reproduces the adopted fixture exactly.
🔴 **Standing consequence — put this in every future executor brief:** *a verification run on a subset
of a cell must use the whole cell, or state that its archetypes are not fleet-faithful.*

✅ **OPEN-34 CLOSED 2026-08-11.** Its last question — *did any published result actually come from a
batch small enough for this to fire?* — was recorded here as **reasoning, not measurement**. Measured:
**all 12 adopted cells are whole**, `05_results.csv` rows = `01_buildings.gpkg` features in every cell,
difference **0**, fleet **8,160**. No published number was ever exposed to the effect. 🔴 **The
standing consequence above survives the closure — the item closed because nothing broke the rule, not
because the rule stopped applying.**

🔴 **OPEN-35 is the more serious of the two.** Two code paths invent the missing storey count and
**disagree**: Stage 2 picks the archetype off the group median, Stage 3 builds the geometry at **1**
(`footprint.py:58-63`). **Size measured: 2,611 of 8,160 = 32.00% of the fleet** persisted at
`levels = 1.0`, of which **1,031 were given a mid- or high-rise archetype and built as a single
storey** — classified as a multi-storey building, simulated as a one-storey one, EUI divided by one
storey's area. True in full-cell runs, and it is the population every published result came from.
~~**The harvested `.eio` files are the independent check, and they are now on disk.**~~

✅ **The independent check has now been made (2026-08-11), and the mechanism is PROVED at the
simulation boundary rather than inferred from source. OPEN-35 stays open — the remaining question is
DESIGN, not measurement.** Restricted to those 2,611 buildings: **100% within ±1% in `auto`,
`building` and `floor`** — *by construction*, because those modes build zones from `levels`, so a wrong
`levels` makes geometry and denominator wrong **together and consistently** — against **mean 2.3728 and
only 17.92% within ±1% under `layout_assign`**, which assigns storeys from the archetype instead.
🔴 **That internal consistency is the trap, and it is why nothing caught this before:** a check whose
two sides share the same error always passes. It took a mode that derives storeys differently to expose
it. **What is still undecided is which fallback is *intended*** — archetype-median storeys, or one
storey. That is a specification question and no measuring task may decide it.

### 5.7 What the R-series fixed before the fleet ran — do not redo any of it

- **R01 / OPEN-37 — `.eio` retention.** `*/eplusout.eio` added to the remote tar list in **five** files:
  `t08_harvest_results.py:131`, `t17:146`, `t18:142`, `t19:150`, `t20:150`. Three-count test on
  `r05probe_la_rural_auto`: **149 on the cluster = 149 in the tar = 149 extracted locally**; old
  behaviour demonstrated first at **0**. E02's harvest confirms it at scale: 40,800/40,800.
  🟠 **The same gap is still present and deliberately unfixed** (variable-built file lists, out of
  scope): `t07_harvest_results.py:105`, `v11_nyc_centre_pipeline.py:289`, `v12_cell_pipeline.py:357`,
  `v12_nyc_urban_recovery.py:93` and `:198`. `t26_harvest_utci_cluster.py:94` is **not applicable**.
- **R02 — the cluster harvest's fatal test** (`t08_harvest_results.py:246`), re-derived over 2,422 real
  `.err` files: old **0**, new **2**.
- **R06 / OPEN-29 — the one-space `"** Fatal **"` test fixed at six live sites.** 🔴 **The fix corrects
  the future, not the record:** no pre-E02 harvest was re-run, so **"never use the `has_fatal` column"
  still binds every pre-2026-08-09 artifact.**
- **R07 — the vintage column reaches the manifest**, carried in `03_manifest.parquet` via a left-join
  inside `run_step3_mode()`. **100%** non-empty over 149 real `la_rural` buildings.
  🔴 **The check that settles it is the independent one:** cross-checked against `year_built` in the raw
  `01_buildings.gpkg`, which the join never touches — all 14 `90.1-2007` buildings have `year_built`
  **2005–2007**, all 135 `DOERefPre1980` have **1920–1979**, **zero crossover**.
- **R08 — the resume guard.** Generalisable lesson: *a guard that restores state at t=0 is not a guard
  unless the write path downstream of it preserves that state.* The first version reproduced the very
  defect it was fixing.
  🟠 **One residual left open deliberately:** the **final** assembly write
  (`t08_local_remainder.py:830`) is still a bare overwrite, so a `--cells X` subset run destroys other
  cells' rows at the end. Could not affect E02 (all twelve cells ran). **Fixing it would change what
  `--cells` means — a semantics decision, not a bug fix. Do not change it without a ruling.**
- **R09 — `.eio` fetched from the cluster** (OPEN-37's code half), landed 2026-08-10 before E02's
  harvest, which is why §4.2 has 40,800 of them.
- **R10 — the E02 census + full harvest + failure reconciliation**, completed 2026-08-10. §4 is its
  output. Its honest execution record is in §8.
- **CP-R2's risk verdicts** — 2-hour wall vs `fast_zone`: **CLEAN** (zero TIMEOUT in 1,735 probe tasks,
  worst task 358 s = 5.0% of the wall) — **confirmed at fleet scale: 0 TIMEOUT in 40,800.** `--mem=6G`:
  **CLEAN by zero-OOM census — 🔴 corrected 2026-08-10 by §4.4's `std::bad_alloc`.**
  🔴 **Do not carry forward the `MaxRSS` justification.** That column's median is 0.3 MB and three
  arrays report a 2.0 MB maximum — impossible for EnergyPlus. `sacct` undersamples short tasks, so it is
  a **floor, not a peak**.

### 5.8 🔴🔴 OPEN-43 — the published fleet EUI is a mean of cell means, and nobody wrote that down

**This is new on 2026-08-12 and it is the most consequential thing the sweep produced.** It was not
found by looking for it. It was found because T02 was told to **reproduce the adopted headline before
comparing anything to it**, and the director then reproduced it a **second** way as an audit check.
The two ways disagreed.

Over the same **8,154** success rows of the adopted `phaseE_elevrb` run:

| aggregation | value |
|---|---|
| per-cell area-weighted means, averaged across 12 cells **weighted by building count** | **158.0298** ← **this is the published 158.0** |
| same, weighted by success count | 158.0557 |
| same, unweighted across cells | 160.0993 |
| 🔴 **pooled `Σ(EUI × area) / Σ(area)` over all 8,154 buildings at once** | **157.0552** |

**The headline sits ≈1.0 kWh/m² above the pooled figure purely from the choice of aggregation.**

**Neither number is wrong. They answer different questions** — one treats each *cell* as the unit of
observation, the other treats each *building*. The defect is not arithmetic; it is that **the project
has never stated which question "fleet EUI = 158.0" answers**, and a reader will assume the pooled
one. A second oddity to state when asking: **the count weights include the six buildings that produced
no energy at all** (OPEN-42's population), because the weight is a building count, not a success count.

⚠️ **`openubem/results/aggregator.py` is per-cell only.** The fleet roll-up lives outside it. **Its
author and its intent are untraced**, so this cannot be resolved by discovering what was meant — it
has to be **decided**. That is §3 ruling 1.

🔴 **Until it is ruled, do not restate 158.0** in any report, board, or answer to the user. The board
carries this as an open row and deliberately does not restate the number.

⚠️ **The generalisable lesson, and it is a cheap one to reuse:** the finding cost nothing but computing
the same quantity a second way. **Re-deriving a headline by one method confirms arithmetic;
re-deriving it by two confirms the definition.** Do the second one on anything you are about to
publish.

### 5.9 The five-item sweep of 2026-08-12 — what changed, and the two things it got wrong

`PLAN_five-item-sweep-2026-08-12.md`, T01–T07, four executors in parallel, CP-1/CP-2/CP-3
director-signed. **Every number below was re-derived by the director from raw artifacts; none was
taken from an executor's report. No executor claim was found false** — which is worth recording,
because the two problems the sweep exposed were both things executors *did not say*, not things they
said wrongly.

| item | before | after |
|---|---|---|
| **OPEN-42** | placeholder unexplained; "6 buildings inside the fleet EUI with 20.3×–336.7× denominator errors" | **traced to one line; impact measured at exactly 0.000; the alarming claim RETRACTED** — see §2 |
| **OPEN-43** | did not exist | **opened** — §5.8 |
| **OPEN-26** | 1 of 4 fixed | **2 of 4 fixed, 2 measured and downgraded to will-not-fix** |
| **OPEN-29** | fatal-test class open | **finished on live code**; 3 sites fixed, a 7th site newly found and left alone |
| **OPEN-33** | 58 dead paths, rule unwritten | **CLOSED** — rule written, 279 citations re-swept, 0 dead |
| **OPEN-13** | 2 live defects | **1 fixed (E-UTCI-13), 1 contained (E-UTCI-12); item stays open** |

**Three results worth carrying as facts:**

- **The missing-EPW `Site:Location` case placed buildings at latitude 0, longitude 0** — the Atlantic
  off West Africa, which is the literal `PLACEHOLDER` in all four `.idf` templates at lines 33–35.
  `builder.py:213-218` now raises instead. Both call sites already wrap the build in
  `try/except Exception → _worker_exception_row`, so the raise degrades a fleet run to a recorded
  failure rather than killing it — **checked before accepting the fix, not assumed.** 187 tests pass.
- **The malformed fatal test could never have fired, and this is now measured rather than argued.**
  Over all **40,800** corpus `.err` files: two-space `"**  Fatal  **"` → **44**; one-space and both
  malformed variants → **0**; R06's regex → 44; the `phaseE_cpb_fixtures.py` union → 44. **Ground
  truth is 44.** Then the question that actually mattered — *did any past conclusion depend on it?* —
  answered script by script: **no.** **Nothing published has to be withdrawn.**
- **A seventh fatal-test site was found and deliberately left alone**:
  `scripts/validation/phaseE_cpb_fixtures.py:176` counts `txt.count("** Fatal  **") +
  txt.count("**  Fatal  **")`, which can **over**-count. On real data it lands on 44 exactly.
  Recorded, not fixed.

🔴 **The two things the sweep got wrong, stated because a clean report is a suspicious one:**

1. **An executor's containment was wider than the fault, and it did not say so.** E-UTCI-12 was fixed
   by a module-level `pytest.skip` on `tests/test_draw_methods.py`. That restores the repo's
   collection — **1937 tests, exit 0, against no tests and exit 2 before**, both legs verified by the
   director on the real tree. **But the skip removes 53 tests and only 13 of them touch the missing
   feature.** Measured on a scratchpad copy with just the one offending class removed: **43 pass.**
   **So 43 working tests were silently traded for a collectable suite**, and nothing now reports them
   as missing. *(Also measured, so the next session does not waste time on it: `@pytest.mark.skip` on
   the class does **not** stop the class body executing, so the narrow fix is not a one-liner — it
   needs conditional collection.)*
2. **The director's own non-vacuity control overwrote a deliverable.** `open33_dead_path_sweep.py`
   ignores `--out` and always writes the canonical CSV, so injecting a broken citation contaminated
   the committed artifact. Caught, the control file deleted, the scanner re-run clean. **Recorded in
   the plan's §8 rather than quietly repaired.**

⚠️ **One honest weakness carried forward:** the E-UTCI-13 fix recognises an already-normalized cache by
an **exact column set duplicated as a literal** rather than imported from
`overture_fetcher._NORMALIZED_COLUMNS`. Verified set-equal today. If that schema ever changes, the
guard stops matching and every read **silently** reverts to the broken double-normalizing path. Safe
direction, silent failure — **the same property that hid the defect for months.**

### 5.10 🔴🔴 OPEN-44 — the suite runs, and it has 70 failures and 36 errors nobody could count before

**Opened 2026-08-12, from the side effects of the sweep's own fix.** E-UTCI-12's containment made the
suite collectable; the director then ran it to completion — **the first complete pass/fail count this
project has had in months.**

```
python -m pytest -q -p no:cacheprovider
70 failed · 1,822 passed · 10 skipped · 36 errors · exit 1 · 26m47s
```

🔴 **Every past claim in this project that "tests pass" covered an unknown subset**, because the
collection abort made the whole-suite number unobtainable. **106 failing or erroring tests were behind
it.**

| tree | failed + errored |
|---|---|
| 🔴 `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` | **61** |
| `tests/` | **44** |
| `scripts/analysis/test_viewer_layout_assign.py` | 1 |

🔴 **`docs/` holds 30 `.py` files, 5 of them test files — against this project's own hard rule,
*no `.py` under `docs/`, ever* (§7).** pytest collects them and they produce **58% of the entire
failure count.** Two are **byte-identical duplicates** of files in `tests/` (`cmp`-verified);
**three have drifted from their `tests/` twins**, which is the worse case — a stale duplicate that has
drifted can pass or fail for reasons unrelated to shipped code.

🔴 **Roughly half the red is artifact-dependence, not broken logic**, and reporting it otherwise
would be the exact category error this arc keeps catching:

| cause | count |
|---|---|
| `FileNotFoundError` — a test asserting an **output artifact exists on disk** | **51** |
| missing pytest fixture `synthetic_10_gdf` (setup errors) | ~36 |
| `AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DEBIAS…'` | 5 |
| elevator-column `KeyError`s | 8 |

**Never say "70 broken tests."**

⚠️ **The `IMPUTE_DEBIAS…` group is E-UTCI-12's shape a second time** — tests committed against a
config attribute that has never existed. **That is OPEN-36's territory, and it suggests OPEN-36's
bound of "1 governance gap, T07, the known one" is too tight. Do not close OPEN-36 without
re-checking it against this.**

**Not known and not to be guessed:** how many of the 44 `tests/` failures are real defects in shipped
code. **That triage is the item's next step.** Nothing published is known to depend on any of them.

*(Incidental: `tests/test_sim_integration.py::test_synthetic_fleet_full_annual` emits a Windows
access-violation faulthandler dump from `joblib`'s `loky` backend under Python 3.14. It does **not**
stop the run.)*

## 6. The rule that governs this arc

**No execution plan may be written for an item until that item's "first measurement" (named in its own
section of the register) has been made.**

1. **Measure** — small, scoped, measurement-only. Remediation **forbidden inside it**.
2. **Decide** — at the report, with the user.
3. **Plan** — only then write `PLAN_<slug>.md`.
4. **Execute** — fresh Sonnet per dispatch; audit each report against raw artifacts.

Assert on the quantity the defect actually moves, not a proxy.

**Corollary:** when an item's evidence is a document rather than a number, **verify the document is
still true before quoting it.** OPEN-03 and OPEN-28 both had register text that was wrong at HEAD.

**Second corollary:** measuring produces new items. Say so plainly to the user, who tracks a count.
E02 alone opened four (OPEN-38…41), all found by *auditing* output rather than by running a task.

## 7. Hard rules — these override anything you infer

### 🔴 Cluster
**NEVER run compute on the Speed login node** (`speed-submit2` / `speed.encs.concordia.ca`). Only
lightweight ops: `squeue`, `sacct`, `ls`, `du`, `find`, `quota`, `mkdir`, `scp`, `tar`. All compute goes
through `sbatch --array`, fire-and-forget, then read the output file. **No `srun`, no `ssh … python …`.**
**Never cancel, requeue or deprioritise any cluster job**, least of all another project's.

**Three cluster-scripting rules, written 2026-08-10 after an 8.5-hour silent failure** (also at the top
of `CLAUDE.md`). A throwaway shell submitter retried 41 job arrays every 30 minutes for 8.5 hours and
**placed none of them**: Speed's login shell is **tcsh**, the script sent bash syntax (`N=$(wc -l < …)`),
tcsh answered `Illegal variable name.`, and `sbatch` was never reached. It logged only the word
`refused` — indistinguishable from a genuine refusal. The cluster was in fact empty.

1. **No ad-hoc `ssh` in this project.** Every remote command goes through `_ssh()`
   (`scripts/cluster/t08_harvest_results.py:104`), which wraps the command in `bash -lc`. **That wrapper
   is the point.** A script that cannot import it must port it; never send a bare command string.
2. **A retry loop must log the actual error text, never a label.** *A loop that records only its own
   interpretation will report a bug in its own quoting as a property of the cluster.* R10 hit the same
   shape from the other side: the harvest script's failure string blamed a missing remote directory when
   the real cause was SSH rate-limiting, and both directories existed with 437 buildings each.
3. **Prove one success before leaving any unattended loop alone.** A loop whose only exercised path is
   the failure path has not been tested.

**Operational facts worth not rediscovering:**

- **Speed has two login nodes** (`speed-submit1`, `speed-submit2`) served **round-robin**, and **`/tmp`
  is node-local**. A file written to `/tmp` by one command is invisible to the next. **Use the
  NFS-shared home directory (`~`)** for anything that must survive between commands.
- 🔴 **An `_ssh()` command string of ≥8,192 characters fails with `Unmatched '.`** — a tcsh parse
  limit, **not** a Python quoting bug: reproduced with a quote-free payload, 8,104 chars succeeds and
  8,192 fails, exactly at the boundary. **Found 2026-08-11 and previously undocumented anywhere in this
  project.** It fails the way this project's cluster failures always fail — silently, with a message
  that looks like your own bug. **Chunk any batched remote command under ~7,500 characters.**
  `scripts/analysis/e02_cluster_readonly_audit.py` does this already (`REMOTE_CMD_SAFE_LEN = 7500`);
  no other script currently builds a command long enough to hit it, which is why this is a standing
  fact and not a register item.
- **A failed task has no `task.rc`** (OPEN-39) — never use its presence as a completion test. It also
  leaves an **untrimmed** ~40 MB directory.
- **The `e02` tag override is mandatory for any harvest.** `t08_harvest_results.py:42` still hard-codes
  `_FLEET_TAG = "t08"`; a blind harvest reads stale directories and **finds nothing**.
- **`MaxJobCount = 20002` cluster-wide and array tasks count individually against it.** 40,800 tasks
  cannot be queued in one pass; fleets over ~19,000 tasks must go in waves. `MaxArraySize = 10001` is
  **not** the binding limit. A genuine refusal reads:
  `sbatch: error: Slurm temporarily unable to accept job … Resource temporarily unavailable`.

### 🔴 Never
- **Never `git commit`** — git is handled externally by the user's own tooling. Do not offer.
- Never edit root `main.py`, any **OVERVIEW** or **DESIGN** doc.
- No `.py` files under `docs/` — ever.
- Progress-log and AUDIT entries are **append-only**. Never rewrite a frozen entry, including ones you
  believe are wrong — correct them in a new entry citing the old.
- **The register is append-and-amend; corrections are struck-and-dated, never deleted.** A register that
  silently fixes itself cannot be audited.

### 🔒 Frozen — cite, do not rebuild
- `T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`. A fleet failure reopens the fix plan, **never** the
  constants.
- Everything under `layoutAssigner/figures/`; the `t17_*`/`t18_*`/`t19_*`/`t20_*` harvests;
  `openubem/idf/opaque_assembly.py`; the 25-IDF prototype library; `openubem/viz/`.
- **Do not re-submit the T20 fleet. Do not re-run the OPEN-05 defect-ID sweep. Do not re-run M01–M05.**
- **Do not re-submit E02, and do not re-harvest it while the corpus is on disk.** It is complete (§4);
  its 45 failures are deterministic and must not be "cleared" by resubmission.

### Evidence rules — this project has been burned by each of these
- Ground truth is the **raw** artifact: `eplusout.err` for run outcome, `eplusout.eio` for
  multiplier-aware floor area. **Never** the `.end` file.
- **Never use the `has_fatal` column.** `False` on all 8,160 rows including the 7 real fatals.
- **Grep fatals with the TWO-space form `"**  Fatal  **"`.** The one-space form is E-LA-21 and misses
  real fatals; both have coexisted in this repo for months.
- **A fatal *count* is not a fatal *cause*.** EnergyPlus's `Program terminates due to preceding
  condition.` names nothing; the content is in the preceding `** Severe **` line. A census that reports
  the trailer 43 times has returned a null result dressed as a finding (OPEN-41, closed 2026-08-11).
  ⚠️ **And the trailer has a decoy:** `..... Last severe error=` repeats the mechanism a few lines
  *below* the fatal. Scan **backwards from the fatal**, not forwards.
- 🔴 **A severity marker is evidence; proximity to a fatal is not.** Twice now an item has been opened
  on a message that merely co-occurred with the failure — OPEN-22's premise, then OPEN-38's, where a
  `** Warning **` was recorded as the Severe that killed seven runs. **Read the marker on the line
  before you attribute a cause.**
- 🔴 **Before explaining a cluster by *where* you found it, join it to every attribute you have.**
  `la_rural`'s 24-of-45 failure share was attributed to the cell for a week; it was the **archetype**
  (`Warehouse`, 0.47% of the fleet, 26 of 44 fatals, ≈309× relative risk). The container you noticed a
  pattern in is rarely the property that causes it.
- 🔴 **Internal consistency is what a self-referential error looks like.** OPEN-35's 2,611 buildings
  sit **100% within ±1%** of their own denominator in three modes — because a wrong `levels` makes the
  geometry and the denominator wrong *together*. **A check that passes because both sides share the
  error is not a check.** It took a mode that derives storeys differently (`layout_assign`, 17.92%) to
  expose it.
- A parser that finds nothing must **say so**, never report `0`.
- **A before/after is not reportable until the "before" is shown to differ from the "after."**
- Check what generated a figure or CSV before concluding from it — a script that reimplements pipeline
  logic makes lookalike evidence. **`a1_prototype_storey_structure.csv` is the live example (§5.1).**
- **Recompute every headline number from the named file before you sign anything.** State this
  requirement explicitly in every executor brief you write.
- 🔴 **Recompute it a SECOND way, not just a second time.** One method re-derived twice confirms
  arithmetic; **two methods confirm the definition.** OPEN-43 exists only because the adopted 158.0
  was reproduced by cell-mean averaging *and* by pooling, and the two disagreed by ~1.0 kWh/m². The
  first derivation matched the published number exactly and would have been signed off.
- 🔴 **A placeholder is not evidence of imputation, and "wrong value published" is not "wrong value
  used."** OPEN-42 was carried for a day as *six buildings inside the adopted fleet EUI with
  denominators wrong by up to 336×*. Measured: the six carry `total_eui_kwh_m2 = NaN`, are excluded
  from both sides of the aggregation, and the true impact is **exactly 0.000**. **Before sizing a
  blast radius, check whether the bad rows are in the sum at all.**
- 🔴 **A default written before a conditional is a published value whenever the conditional fails.**
  `v12_cell_pipeline.py:659` sets `footprint_area_m2 = 200.0` and `:664` replaces it only on
  `status == "success"`. No `else` branch, so every failure ships the initialiser as though it were
  measured. **Grep for initialise-then-overwrite-on-success wherever a report is assembled.**
- 🔴 **A fix that restores a green signal can cost coverage silently — measure what it removed.** The
  E-UTCI-12 module skip made the suite collectable (1937 tests, exit 0) and **took 43 passing tests
  out with it**, of which nothing complains. **When a fix is a suppression, always report how much it
  suppressed** — the executor did not, and the director had to measure it.
- ⚠️ **A guard keyed on a duplicated schema literal fails silently when the schema moves.** The
  E-UTCI-13 fix compares against a hand-copied column set rather than importing the fetcher's own.
  Correct today, silently wrong the day the schema changes. **Prefer importing the authority; if you
  cannot, say out loud that you did not.**

## 8. Working with executors

- **Fresh Sonnet session per unit of work.** Never resume an old agent for new work. The plan doc is the
  single source of state. *Exception:* an agent still mid-task on a not-yet-reported unit.
- **Never run cluster, harvest or inventory work in the manager session.** Delegate it.
- **Tell executors upfront to block on artifacts on disk, never to wait for a notification.**
- 🔴 **An executor's "completed" is a claim, not a fact — R10 proved it twice in one task.** That agent
  reported completion once while dead at 36/60 arrays and once with a live background child at 48/60.
  **Every number in R10's progress entry was re-derived by the manager from on-disk file counts and the
  append-only log, not taken from the agent's report.** Do the same, always.
- **An ambiguous mid-work message is not a finished session.** A 0-byte log is a *healthy buffered* job
  — check CPU before relaunching. This has gone wrong twice.
- **Address messages by the correct agent id.** A scope change was once sent to the wrong running agent.
- Delegate monitoring to cheap models. **Minimum polling interval 30 minutes**; prefer event-driven.
- Do **not** read a background agent's `output_file` — it is the full JSONL transcript and will overflow
  your context.
- **Audit by independent re-derivation, not by reading the report.**

## 9. Documentation conventions

- **`docs/docs_ACTIVE/openings/` stays clean.** It holds the register, `prompts/`, `extra/`,
  `implemenation/` and `reporting/`. **Every supporting document goes in `openings/extra/`.**
- **Spent director prompts go to `prompts/previous/`.** One live prompt at the top level, dated.
- **The progress board:** `docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html`,
  published at **https://claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639**. **Republish the
  same file path to keep the same URL.** Rules the user set: **every task appears**, **every task
  carries a short paragraph**, **as each task completes the next moves into "in progress."** Update it
  on every change without being asked. `reporting/board_published-numbers.html` is a **snapshot copy** —
  refresh it too, or it silently goes stale.
- Plan docs carry the project's mandatory sections — header, hard rules for the executor, file layout,
  pinned dependency decisions, verified facts with line citations **you personally grepped**, numbered
  tasks each with **what / why / how / how to test**, 2–4 checkpoints, and a progress log.
- **Correction-via-addendum:** never edit a frozen dated section of a results doc. Append the next one.
- All `.png` / figure outputs go **flat** to `openubem/outputs/`, mirrored into `docs_ACTIVE/<arc>/`.
- Every open/site metric gets registered in
  `docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md` **first**.
- **Past ~1,000 lines, close a plan doc and open a `_REMAINder` citing old findings by ID.**
  `PLAN_speed-resume.md` is at **1,451** and is finished through R10 — **close it, do not extend it.**
- Keep `docs/PROJECT_CHECKLIST.md` current — §M indexes this arc.

## 10. State of the project around you

- **Adopted baseline:** `phaseE` full realism, E-R3-3-corrected, plus elevators. 12 cells, 8,160
  buildings (**8,154 with results, 6 `not_simulated`**), **zero fitted parameters** — a guarantee any
  "calibration" work (OPEN-19) must not silently break.
  🔴 **The fleet figure is `158.0298` as a count-weighted mean of cell means and `157.0552` pooled
  over all 8,154 buildings. Which one the headline means is UNRULED (OPEN-43, §5.8). Do not quote
  "158.0 kWh/m²" as the fleet EUI until it is.**
- **`layout_assign` is adopted for zone/HVAC-topology studies and NOT certified for fleet-level EUI
  reporting.** OPEN-01/03/32/38 are all `layout_assign`-scoped. **The adopted 158.0 figure is measured
  clear of it** (§5.5) — say so, and say what is still wrong in the same breath.
- The LayoutAssigner arc closed 2026-08-04, CP-E signed. Do not re-open its documentation plan.
- **The R6-4B "Other" residual STOP is permanent** — post-Phase-E residual is process + misc plug loads.
- **Uncommitted working tree is normal here.** Git is handled externally by the user — never commit,
  never offer to.
- **Nothing is in flight.** The cluster queue is empty and correctly so; no harvest, no background
  agent, no monitoring loop was left running by the 2026-08-12 session either.
- **The working tree carries the sweep's uncommitted changes** — `openubem/idf/builder.py`,
  `openubem/semantic/fusion.py`, three `scripts/diagnostics/t0*.py`, `tests/test_draw_methods.py`,
  `docs/PROJECT_CHECKLIST.md`, the register, the board, this prompt, plus new files under
  `openings/extra/`, `openings/implemenation/`, `scripts/analysis/` and
  `openubem/outputs/comparisons/`. **Normal — git is handled externally. Never commit, never offer
  to.** *(Also normal and harmless: `tests/fixtures/synthetic_30_archetype_coverage.gpkg` shows
  modified; the only difference from HEAD is the `gpkg_contents.last_change` timestamp — a test opens
  the checked-in fixture for write. The data table is hash-identical at 25 rows. Verified, not
  assumed.)*

## 11. What "done" looks like for this arc

There is no single checkpoint — this arc is a **queue**, not a march. It is healthy when:

- Each opened item has had its first measurement made **before** its plan was written.
- Each closed item is struck from the register with a dated one-line disposition and its evidence mark
  upgraded to ✅.
- Items that turn out to be already-fixed, duplicated, or stale are **removed with a reason**.
- The register stays the single place open work is recorded.
- **The board reflects reality at all times.** It is how the user sees the project.

---

**Your first action:** read the register in full, then confirm the harvested corpus is **still on disk**
(it lives in a temp directory nobody is protecting — count it, do not assume it). Then put **one** ruling
to the user: ~~OPEN-22~~ **OPEN-43 — which aggregation the published fleet headline should use.** It
is decidable today from four numbers that already exist (§5.8), it is upstream of every figure this
project publishes, and **nothing that quotes 158.0 should be written until it is answered.**

If you want work running while that ruling is pending there are now **two** ready measurements, both
fully local. The larger is **OPEN-44's triage — which of the 44 `tests/` failures are real defects in
shipped code and which are merely asserting that an output file exists.** The smaller is **OPEN-42's
remaining unknown — why the six `Warehouse` simulations failed.** Their `error_summary` is the empty string in
the manifest, so the causes have to be read from the `.err` files, which are on disk. Fully local, no
cluster, no ruling required. *(OPEN-42's placeholder question was the previous answer here; it ran on
2026-08-12 and is answered — the placeholder is traced to one line and its fleet impact is exactly
zero. OPEN-41's severe-line re-scan was the answer before that; it closed on 2026-08-11.)*

**Do not lead with the register's item count**, in either direction. It went **up** when E02 was
audited well (four items opened by auditing, not by running), it went **down** on 2026-08-11
(35 → 31) when five of those questions were answered, and it **did not move at all** on 2026-08-12
even though four items advanced and one closed. **None of those three numbers is the achievement.**
Explain what was measured, then quote a total if asked.

🔴 **One thing to carry into every report you write about these passes.** The user's stated goal was to
reduce the number of open items. On 2026-08-11 it was reduced — but **the plan that did it wrote down,
before starting, that suppressing a finding to protect a count was forbidden**, and the pass then
opened OPEN-42 and refused to close OPEN-38. On 2026-08-12 the same discipline held under more
pressure: the sweep **retracted one of its own item's headline claims**, **opened OPEN-43 off an audit
check nobody asked for**, **refused to close OPEN-13 and OPEN-42**, and **reported its own contaminated
artifact and its own executor's unstated coverage loss.** **Say both halves, every time.** A register
that only shrinks is not being audited; it is being tidied.
