# DIRECTOR PROMPT — the `openings` arc

> **Written:** 2026-08-11, at the close of the session that harvested E02 in full and reconciled its
> failure census.
> **🔴 UPDATED IN PLACE 2026-08-12**, three times: at the close of the five-item sweep
> (`implemenation/PLAN_five-item-sweep-2026-08-12.md`), the rulings-and-five-items sweep
> (`PLAN_rulings-and-five-items-2026-08-12.md`, §5.11), the three-new-items sweep
> (`PLAN_three-new-items-2026-08-12.md`, §5.12) and the three-rulings sweep
> (`PLAN_three-rulings-2026-08-12.md`, §5.13 — **updated task by task as each one lands, at the
> user's instruction of 2026-08-12**). **🔴 UPDATED AGAIN 2026-08-13** with T04's completion, its
> cause analysis, and the confirmatory repeat run — §5.14. **🟩 UPDATED ONCE MORE 2026-08-13 12:47,
> when the user stepped away from the project**: the confirmatory repeat closed, CP-2 was signed, and
> a **RESUME HERE** box was added at the head of the green box below — read that box first, it states
> what is running (nothing) and what is owed (two rulings, §3 `2f` and `2g`).
> **🟩🟩 UPDATED ONCE MORE 2026-08-14, when the user stepped away a second time:** the user approved
> the OPEN-49 + OPEN-01 remedy on four rulings, `PLAN_open-49-and-open-01-2026-08-13.md` was written
> and dispatched, and the executor **stopped partway through T02, leaving `openubem/semantic/__init__.py`
> edited but untested and unsigned.** A **new RESUME box supersedes the old one** — read it first; the
> full account is **§5.16**. The filename keeps its 2026-08-11 date because
> the user asked for this file to be updated rather than superseded. **Where a 2026-08-11 sentence was
> falsified, it is struck through and corrected in place, not deleted** — the same rule the register
> runs on.
> **🟩🟩🟩 UPDATED ONCE MORE 2026-08-17, overnight autonomous run.** The user went to sleep and told
> the director to carry the arc to the end and **update this file at every step, not only at
> checkpoints**. A **third RESUME box** now heads the green box below and supersedes both earlier
> ones; the 2026-08-14 box's opening instruction is stale (the edit it calls loose was committed in
> `82bbd25`; the tree is clean). Task-by-task progress is appended to **§5.17**.
> **UPDATED ONCE MORE 2026-08-18, at the close of the five-item pass and at the user's request
> to prepare this file for the next session.** `PLAN_five-items-2026-08-18.md` ran T01-T06 to CP-3 and
> CP-3 was signed. A **fourth RESUME box** now heads the green box below and supersedes all three
> earlier ones. **The CP-3 box's "unresolved contradiction" about the full suite is RESOLVED and is
> struck in place** - there was no regression; the plan's baseline command was wrong. Task-by-task
> account: **5.18**. Two rulings are owed and are in section 3 as `3a` and `3b`.
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
> **two new ones**, OPEN-43 and OPEN-44 — **both found by auditing, not by running a task.**
> **Two further sweeps ran the same day** (§5.11, §5.12): the evening pass closed OPEN-43, OPEN-31 and
> OPEN-04 and opened OPEN-45/46/47; the night pass closed nothing, **reversed OPEN-46's premise, and
> opened OPEN-48.** **The user then ruled on three of them** (2026-08-12 night-2) and
> `PLAN_three-rulings-2026-08-12.md` executed those rulings — §5.13. **OPEN-45 and OPEN-47
> are done bar the register entry; OPEN-48's load wiring is restored and the twelve-cell fleet
> re-run finished 2026-08-13 01:42.** 🔴 **UPDATED 2026-08-13 — §5.14. The re-run reproduces the
> elevator energy exactly (3,561 rows, cell by cell) but the fleet lands at 159.2157 vs the adopted
> 157.0552, and the +2.16 was traced to a defect: a single reclassified building re-randomises the
> window-to-wall ratio of every `OpenUBEMUnknown` building in the same cell.**
> 🔴 **UPDATED AGAIN 2026-08-13 12:47 — the confirmatory repeat is FINISHED and it closed the
> question at both stages (IDFs byte-identical, results max Δ 0.00836 kWh/m²). Nothing is running and
> nothing is queued. The arc is idle and blocked on TWO rulings only — see the RESUME box below.**
>
> ## 🟥🟥 RESUME HERE — written 2026-08-18 after CP-3 was signed. **THIS BOX SUPERSEDES EVERY RESUME BOX BELOW IT, INCLUDING THE 🟪 ONE.**
>
> **Nothing is running. Nothing is queued. No cluster job is in flight.** `PLAN_five-items-2026-08-18.md`
> is fully executed and closed — T01–T06, CP-1/CP-2/CP-3 all director-signed. Full account: **§5.18**.
>
> **What the pass did.** **OPEN-06, OPEN-37 and OPEN-51 are CLOSED and retired.** **OPEN-52 and OPEN-42
> stay open**, each with a named next step instead of a re-read of the same evidence. **OPEN-53 was
> opened** for the E02 `.sql`/`.end` shortfall. **Register: 26 live / 27 struck / 53 total, 25 IDs
> retired, contiguous `OPEN-01…OPEN-53`, recounted programmatically over the §1 table body. Next free
> item ID: `OPEN-54`.**
>
> **The single most reusable result of the pass — read this before writing any plan doc.**
> 🔴 **The full-suite baseline is `.venv/Scripts/python.exe -m pytest -q tests/`, NEVER a bare
> `pytest -q` at the repo root.** `pyproject.toml` sets no `testpaths` and no `norecursedirs`, so the
> bare command collects the whole tree and adds ~96 tests that live outside `tests/` — five test files
> under `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` (there since `ef19141`,
> 2026-07-21) and `scripts/analysis/test_viewer_layout_assign.py` (`69373f9`, 2026-07-27). Proof, by
> collection rather than by re-running: **`tests/` collects 1930 = 1875 passed + 55 skipped**, root-wide
> collects **2026**, and the 96-test gap is exactly **43 passed + 36 failed + 17 errors, all outside
> `tests/`**. **T06's run was therefore 1875 / 55 / 0 inside `tests/` — the baseline reproduced to the
> unit, no regression.** A plan doc that writes the bare command will make its executor report a false
> regression; `PLAN_five-items-2026-08-18.md` T06 step 5 did exactly that, and that is the one defect
> to carry out of the plan.
>
> **Two rulings are owed, and nothing further is authorised until one of them is answered — §3, `3a`
> and `3b`.**
> - **`3a` — OPEN-52's remedy shape.** `%LOCALAPPDATA%\Temp\pytest-of-o_iseri` (dated Apr 1) is
>   **OS-level access-denied** — director verified `ls` and `touch` both fail with Permission denied —
>   and the undocumented `addopts = "--basetemp=.pytest_tmp"` pin in `pyproject.toml` has been
>   incidentally shielding every `tmp_path` test from it. **Do not remove that pin** without a remedy in
>   hand. Ruling: repair the ACL, or a different remedy shape.
> - **`3b` — the stray `.py` files under `docs/`.** New and independent of `3a`: `CLAUDE.md` forbids
>   `.py` under `docs/` outright, and one of the strays, `test_results_aggregator.py`, collides by
>   basename with `tests/test_results_aggregator.py` — with no `__init__.py` and pytest's default
>   import mode, that collision **is** the 17 collection errors. Cheap remedy for the whole class:
>   a `testpaths = ["tests"]` line in `pyproject.toml`. **Proposed to the user 2026-08-18, deliberately
>   NOT applied.** This is the same population as the older ruling `2c`, which is still live.
>
> **What is ready to run the moment a ruling lands, in rough order of value:**
> - **OPEN-01's denominator swap** — ruled 2026-08-13 (divide by the simulated area), measurement
>   already on disk, **plan doc still not written**. Largest piece of unstarted work this arc owns.
> - **OPEN-42** — needs a *different artifact*: per-surface geometry, not `eplusout.eio` zone
>   aggregates. `.eio` is exhausted for this question; do not send an executor back to it.
> - **OPEN-53** — the `.sql`/`.end` shortfall's cause is untraced (39,926/40,800 `.sql`,
>   39,925/40,800 `.end`, concentrated in `austin_suburban_fast_zone`/`austin_suburban_floor` plus one
>   `nyc_centre_fast_zone`).
> - **Rulings `7` (CP-M2) and `8` (OPEN-11)** are still unasked and unchanged.
>
> **Standing method notes that earned their place this pass:** audit against raw artifacts on disk,
> never against the executor's report — CP-2 re-derived OPEN-06 from the committed `05_results.gpkg`
> and got 41/41, and CP-1 re-derived the `pytest-of-o_iseri` lockout by hand. Two executor numbers were
> wrong and were caught this way (Severe counts 26/24/19 → **23/21/16**; a control that failed 31/10
> against N04's 33/8 because the harness classified a subset). **Controls before results**, every time.
>
> ## ~~🟪🟪 RESUME HERE — written 2026-08-18, CP-3~~ **(superseded by the 🟥 box above; its "unresolved contradiction" was resolved the same day — see the strike below)**
>
> **`PLAN_five-items-2026-08-18.md` is FULLY EXECUTED, T01 through T06. CP-3 reached. Nothing is
> running, nothing is queued.** Full task-by-task account: **§5.18**.
>
> **Outcome of the five, plus one found along the way:** **OPEN-06, OPEN-37, OPEN-51 CLOSED and
> retired.** **OPEN-52, OPEN-42 STAY OPEN**, each sharpened to a specific next step rather than a
> re-read of the same evidence — OPEN-52 needs a user ruling (ACL repair vs. a different remedy
> shape for the `pytest-of-o_iseri` OS lockout); OPEN-42 needs a different artifact than `eplusout.eio`
> (per-surface geometry, not zone-level aggregates). **OPEN-53 opened** (E02 harvest `.sql`/`.end`
> shortfall, 874/875 directories, cause untraced). **Register: 28 live → 26 live / 24 struck → 27
> struck / 52 total → 53 total. 25 IDs retired in all. Next free item ID: `OPEN-54`.**
>
> 🟩 **RESOLVED 2026-08-18, the same day, without re-running the suite — the paragraph below is kept
> for the record and is FALSIFIED in its conclusion. There is no regression; the baseline definition
> was wrong, not the run. The baseline is `pytest -q tests/`, and inside `tests/` this run was
> 1875 / 55 / 0. See the 🟥 box above and §5.18's CP-3 sign-off.**
> ~~🔴 One unresolved contradiction, surfaced by T06's full-suite run and left open rather than
> guessed at.~~ `pytest -q` (bare, repo-root, no path argument) gives
> **`36 failed, 1918 passed, 55 skipped, 11 warnings, 17 errors in 1544.83s`** — not the
> `1875 passed / 55 skipped / 0 failed` this plan's hard rules named as the baseline. All 36 failed +
> 17 errors trace to pre-existing, long-committed files (`docs/docs_DONE/…/elevators/scripts/tests/*`
> since `ef19141`, plus `scripts/analysis/test_viewer_layout_assign.py` since `69373f9`) that this plan
> never touched and is not authorised to touch — the same population `docs/PROJECT_CHECKLIST.md`
> already put on record once (`1910 passed, 35 failed, 55 skipped, 17 errors`, filed under OPEN-44's
> rider that only `tests/`-scoped runs are green, not the bare command). **The 2026-08-17 CP-2
> sign-off (§5.16) reads `0 failed` from the same bare command on a tree where those same files were
> already old, committed history** — `pyproject.toml` is unmodified (confirmed by `git diff`), so no
> collection-scope change there explains it. **Not reconciled — the suite was not re-run a second time
> to test hypotheses.** `skipped` matches exactly (55=55); the 7 `Windows fatal exception: access
> violation` lines match the known joblib/loky noise exactly. **This needs a director read of both raw
> logs side by side before the next full-suite claim in this arc is trusted at face value.**
>
> ~~**Two owed rulings now stand, not one:** OPEN-52's remedy shape, plus whatever the full-suite
> contradiction above turns out to need.~~ **Corrected: the two owed rulings are `3a` and `3b` in §3 —
> the second is the stray-`.py`/`testpaths` question, not the contradiction, which is resolved.** **Nothing further is
> authorised without one of them.**
>
> ## ~~🟦🟦 RESUME HERE — written 2026-08-18~~ **(superseded by the box above — CP-3 reached, plan fully executed)**
>
> **Standing instruction, given 2026-08-18:** the user asked for **five more open items to be chosen,
> planned, and executed to the end**. The director picked five that are local, unblocked and
> answerable today, wrote `implemenation/PLAN_five-items-2026-08-18.md`, and is running it to CP-3
> without waking the user. **Task-by-task progress is in §5.18** — read that first.
>
> **The five:** **OPEN-52** (pytest `--basetemp` collision), **OPEN-51** (`E-LA-16` used for two
> failure signatures), **OPEN-37** (five harvest sites still never fetch `.eio`), **OPEN-06** (no code
> state in this repo accounts for the archetype column), **OPEN-42** (why the zoning *mode* decides
> whether a Warehouse blows up).
>
> **The 2026-08-17 box below is still true about the arc it closed** — `PLAN_open-49-and-open-01-2026-08-13.md`
> is fully executed, OPEN-01 is closed, `157.1 kWh/m²` pooled is unmoved — but its
> *"nothing is in flight, nothing further is authorised"* is superseded by this pass.
>
> ## 🟩🟩🟩 RESUME HERE — written 2026-08-17, overnight autonomous run. **THIS BOX SUPERSEDES EVERY RESUME BOX BELOW IT.**
>
> **Standing instruction, given 2026-08-17 when the user went to sleep:** *"tu continues jusqu'à la
> fin, et pour chaque étape mets à jour ce prompt pour des sessions prochaines."* The director runs
> the arc to the end without waking the user, and **updates this file after every task**, not only at
> checkpoints. The audit standard is unchanged: a checkpoint that cannot be re-derived from raw
> artifacts on disk is still a STOP.
>
> **🔴 CORRECTION to the 2026-08-14 box below — its first instruction is now WRONG.** That box says to
> run `git diff openubem/semantic/__init__.py` because the tree carries a loose unaudited edit. **The
> tree is CLEAN.** The user's external git process committed that edit on 2026-08-14 in **`82bbd25`**
> ("docs/tests: complete test suite triage, tagrich gate fixes, and openings measurement updates",
> 38 files, +14615/−352), together with `tests/test_semantic_unknown_draw.py` and the five 2026-08-13
> plan docs. **Being committed changes nothing about its standing: it is still unverified, still
> unsigned, and the plan's §8 progress log is still empty.** To see the pre-fix code, use
> `git show 82bbd25^:openubem/semantic/__init__.py` — **read-only git only**, plan rule 1 forbids
> every git write command (`add`, `commit`, `restore`, `checkout --`, `stash`).
>
> **🟩🟩🟩 NOTHING IS IN FLIGHT — FINAL STATE 2026-08-17.** **CP-1 and CP-2 are both
> signed and `implemenation/PLAN_open-49-and-open-01-2026-08-13.md` is fully executed, T01–T08.**
> No executor, no monitor, no SLURM job; Speed is free. OPEN-01 is closed and its ID retired;
> OPEN-49 is mechanism-fixed with closure blocked on the re-run ruling 4 declined. The full record,
> the audit tables and the three unasked-for findings are in **§5.17** — read that before anything
> else. The working tree is dirty by design and **no session may ever commit**. The two paragraphs
> below are the superseded dispatch notes, kept only for the record.
>
> ~~**What was in flight earlier.**~~ **UPDATED LATER ON 2026-08-17.** **CP-1 is signed** (T01–T04 audited
> against raw artifacts; the audit table and the one substantive finding are in **§5.17**). A **second**
> fresh Sonnet executor now holds **T05 → T08, stopping at CP-2** — the OPEN-01 denominator swap. The
> working tree is intentionally dirty: the T01–T04 artifacts plus the director's edits to this file and
> to both `board_published-numbers.html` copies. That is expected; **git is handled externally and no
> executor may ever run a git write command.** The paragraph below is the *earlier* CP-1 dispatch,
> kept because it records the corrections that were carried:
>
> ~~**What was in flight before that.**~~ A fresh Sonnet executor was dispatched **2026-08-17** on
> `implemenation/PLAN_open-49-and-open-01-2026-08-13.md`, **T01 → T04, stopping at CP-1**. It was told
> the three things the plan text predates: (1) the T02 edit is already applied *and committed*, and is
> to be treated as unverified; (2) T01's FAIL proof was never produced, so its first job is to swap in
> the pre-fix source with a **plain file copy** (backup to scratchpad, restore afterwards, confirm
> `git status --porcelain` is empty again) and show both tests FAIL, with per-column drift magnitudes —
> **if a test PASSES on pre-fix code the test is wrong, fix the test, not the code**; (3) T02's
> non-vacuity proof (constant seed → must FAIL → restore) and the `_build_unknown_envelope` check are
> still owed, then T03 and T04 as written.
>
> **Nothing is on Speed and nothing needs to be. No cluster work is required for any of T01–T08.**
>
> **Also done 2026-08-17, at the user's request, outside the plan:** the published-numbers board
> artifact (`https://claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639`, source
> `implemenation/board_published-numbers.html`, mirrored to `reporting/`) was **reordered only** — the
> counters, filters and work-package task list now open the page, and the whole dated narrative moved
> to a **Notes & history** section at the foot. **No board text was rewritten and no number changed.**
> The user's question that prompted it, and the answer given: the board's `all 102 / done 78` counter
> is cumulative over every work package A…S and never resets, so it is a log, not a progress bar; the
> converging count is the register's tracked-items number.
>
> ## ~~🟩🟩 RESUME HERE — written 2026-08-14 when the user stepped away again~~ **(superseded by the box above; its `git diff` instruction is stale — the edit is committed in `82bbd25` and the tree is clean)**
>
> **🔴 FIRST, BEFORE ANYTHING ELSE: the working tree carries an UNAUDITED edit to SHIPPED CODE.**
> `openubem/semantic/__init__.py` has been modified — the OPEN-49 coupled-draw fix — by an executor
> that **stopped in the middle of its plan**. **No test output was ever recorded for that edit, the
> director never signed it, and the plan's progress log is EMPTY.** Run `git diff
> openubem/semantic/__init__.py` as your first command. **Do not build on it, do not commit it, and do
> not quote any number derived from it until T01–T04 are finished and audited.** Full account: **§5.16**.
>
> **What is authorised.** `implemenation/PLAN_open-49-and-open-01-2026-08-13.md` — written 2026-08-13,
> **approved by the user on four explicit rulings** (§5.16). It is the only authorised work in this arc.
> **T01–T08, CP-1 after T04, CP-2 after T08. Its progress log is §8, not §7.**
>
> **Where it stands: partway through T02.**
>
> | Task | State on disk |
> |---|---|
> | T01 — failing test that pins the defect | ✅ `tests/test_semantic_unknown_draw.py` exists, two tests, one per coupling route. **Never observed to fail on unmodified code — that proof is missing.** |
> | T02 — per-building draw + fixed bounds | ⚠️ **Edit applied, never verified.** `blake2b` per-building generator added; `_get_cross_archetype_loads()` made unconditional at the call site. |
> | T03 — extend to the setpoints, lock all eight fields | ❌ Not started. |
> | T04 — before/after on the twelve cells | ❌ Not started. No script, no CSV. |
> | §8 progress log | ❌ **Empty.** |
>
> **How to restart it.** Dispatch a **fresh** Sonnet executor — never resume the stopped one — on
> **T01 through T04, stop at CP-1**. Tell it the T02 edit is already in the tree and **unverified**:
> its first job is to run T01's two tests against a *reverted* copy of the draw code and show them
> **FAIL**, because that proof was never produced. **If T01 passes before T02, the test is wrong — fix
> the test, not the code.** Run pytest **only on the named file**, never whole-tree, **never two
> sessions at once** (`pyproject.toml:54` pins a fixed `--basetemp`; concurrent runs delete each
> other's temp dirs — OPEN-52).
>
> **Nothing is queued on Speed. No cluster work is needed for any of T01–T08.**
>
> ## ~~🟩 RESUME HERE — written 2026-08-13 when the user stepped away~~ **(superseded by the box above)**
>
> **Nothing is in flight.** No SLURM job, no local driver, no executor, no monitor. Speed is free.
> `PLAN_three-rulings-2026-08-12.md` is fully executed: T01, T02, T03, T05 completed 2026-08-12;
> **T04 completed 2026-08-13 12:47** (twelve-cell re-run + cause analysis + confirmatory repeat).
> Its §8 progress log and §9 close-out are current; §5.13 and §5.14 here mirror them.
>
> **🟩 UPDATED 2026-08-13 (later) — ruling `2f` was PUT AND ANSWERED: the user said register it, and
> the director wrote OPEN-49 into the register the same turn. ONE thing is now owed, ruling `2g`.**
>
> 1. ~~**Register the `wwr` re-randomisation defect as OPEN-49** (ruling **2f** in §3).~~ ✅ **DONE
>    2026-08-13.** `OPEN-49` is written: its own section immediately after OPEN-48, a dated amendment
>    block at the head of the register, §1's header moved to **34 tracked items (OPEN-01 … OPEN-49)**,
>    the count arithmetic stated as **33 − 0 closed + 1 opened = 34**, the `Next free item ID` line
>    struck and re-issued as **`OPEN-50`**, and a dated amendment appended under **OPEN-48** recording
>    that its own question is answered (the repository regenerates elevator energy) while the item
>    stays open on the two grounds named there. **Do not re-ask this and do not re-write the entry.**
> 2. ~~**Keep or replace the published `157.1 kWh/m²`** with the re-run's **159.2157** (ruling
>    **2g**).~~ ✅ **RULED 2026-08-13: KEEP `157.1 kWh/m²`.** The user was given both sides and kept it.
>    🔴 **`159.2157` is NOT adopted, is not the fleet figure, and must never be restated as one** — it
>    survives only as evidence inside OPEN-49. The accepted cost, which must travel with the number:
>    **the published figure is one HEAD cannot reproduce end to end**, so OPEN-48's provenance caveat
>    stays live until OPEN-49 is fixed and the fleet is re-run a third time.
>
> **🟩 BOTH RULINGS ARE NOW ANSWERED AND NOTHING IS OWED TO THE USER. The same turn, 2026-08-13, the
> user reaffirmed the autonomy grant — *"continuer jusqu'à la fin comme tu recommends finir"* — so the
> director self-signs its own checkpoints and drives the arc on. This does NOT lower the audit
> standard: a checkpoint that cannot be re-derived from raw artifacts is still a STOP.**
>
> ~~**If the user wants work moving before ruling on those**, the ready item needing no new ruling is
> **OPEN-42's remaining unknown** — why the six `Warehouse` simulations failed; their `.err` files are
> on disk.~~ ✅ **DONE 2026-08-13 — see the CP-1 box below.** **OPEN-22's fixture rebuild is still
> blocked on ruling 2a** (the ≥0.70 gate threshold).
>
> ## 🟩 CP-1 SIGNED 2026-08-13 — `PLAN_two-measurements-2026-08-13.md` is fully executed
>
> **Nothing is in flight.** Two executors ran in parallel and both passed the director's
> re-derivation audit. **Do not re-run either measurement.** Full record: that plan's §7 progress log
> (T01, T02, CP-1 entries).
>
> **What was measured, and what it changed:**
>
> 1. ✅ **OPEN-42's blocking unknown is answered.** All six failed `Warehouse` buildings die of the
>    **same** cause: `**  Fatal  ** Program terminates due to preceding condition.` preceded by
>    `** Severe  ** Temperature (low|high) out of bounds` on a *zone* — values **−444.53 °C to
>    +530.25 °C**. Not geometry, not input parsing. 🔴 **And the failure is zoning-dependent, not
>    building-dependent: all six run clean under `building` (whole-building) mode**, five also under
>    `layout_assign`. **OPEN-42 is now a zoning-method defect and stays open on one question only —
>    why one zoning mode survives where another blows up.** That is not answerable from `.err` files;
>    it needs the geometry/zoning code. Evidence: `openubem/outputs/comparisons/open42_six_failure_causes.csv`.
> 2. ✅ **OPEN-44's `tests/` triage is complete.** At HEAD: **26 failed · 1,857 passed · 10 skipped ·
>    19 errors**, and the director **reproduced it in an independent 18m02s run down to the identical
>    set of 45 node IDs — zero set difference.** **31 nodes are missing disk artifacts. 0 are real
>    defects in shipped code.** 🔴 **The remaining 14 were reported as "stale expectations" and that
>    framing was corrected at audit:** `draw_methods.py` and `debias.py` are shipped and present,
>    `imputation.py` imports neither, and their config settings have **never existed in any commit**.
>    **They are unfinished-integration failures — the only surviving evidence that two features were
>    built and never wired.** Routed to **OPEN-17** (9 nodes) and **OPEN-36** (5); no new ID opened.
>    ⚠️ **Do not skip or delete them to green the suite** — measured cost of the blunt fix is 14 tests
>    vs 5 for the narrow one.
> 3. 🔵 **OPEN-50 opened by the checkpoint itself** (not by either task): **running the test suite
>    rewrites the checked-in fixture** `tests/fixtures/synthetic_30_archetype_coverage.gpkg`.
>    Reproduced in isolation from a clean tree. Scope proved by hashing every table's full row set on
>    both copies — **all identical except the 1-row `gpkg_contents`, and within it exactly the
>    `last_change` field.** ⚠️ **Standing consequence for every future audit: a dirty copy of this
>    fixture after a test run is EXPECTED and must never be read as an executor writing outside its
>    authorised set. Verify by row hash, never by byte diff. Never commit it** — one such rewrite is
>    already in the history at `6aeebb0`.
> 4. 🔴 **Register-hygiene defect recorded, not patched:** the register's §1 summary table jumps
>    `OPEN-44` → `OPEN-50`. **Rows for `OPEN-45` … `OPEN-49` were never written**, though all five have
>    full §-sections. **The sections are the authority; the table is not a valid item census until
>    those five rows exist.**
>
> **Two audit catches worth carrying, because both prove the method:** T01's report misattributed four
> director-authored `git status` diffs to the parallel executor (caught only by running `git status`
> rather than reading the claim), and T02's CSV/report **overwrote same-named files committed at
> `6aeebb0`** that held the wider 106-node whole-repo triage — nothing lost, but **any citation of the
> 106-node numbers must now resolve against `6aeebb0`, not the working tree.**
>
> **A fourth instance of the marker-matching family was found and routed to OPEN-45:**
> `SEVERE_RE` in `openubem/results/err_parse.py` is anchored `^\s*` and cannot match EnergyPlus's
> **recurring** form `   *************  ** Severe  **`, so `count_severe` undercounts (proved on a live
> file whose own footer says 2 where the helper says 1). ✅ **Count column only — no cause attribution
> is affected.** Not fixed: remediation inside a measurement task is forbidden.
>
> **What must NOT be redone:** the twelve-cell re-run, the confirmatory repeat, the IDF MD5
> comparison, the results comparison, the E02 census/harvest/audit. All are complete and recorded.
>
>
> ## 🔴 The six sentences that change what you do next
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
> **4. 🔴🔴 THE PUBLISHED FLEET EUI IS `157.1 kWh/m²`. RULED AND ADOPTED 2026-08-12 (OPEN-43).**
> **Definition, and always quote it with the number: pooled — total simulated energy ÷ total simulated
> floor area over all 8,154 successful buildings** (`Σ(EUI × area) / Σ(area)` = **157.0552**).
> ~~158.0~~ is **superseded**: it was a **count-weighted mean of the twelve cell means (158.0298)**,
> which is an aggregation artefact — it changes if the cells are re-cut, and the pooled figure does not.
> The user delegated the choice ("*la plus bon precision*"); the director ruled pooled because it is the
> physical definition of an intensity and what any reader assumes. Two other weightings exist and are
> **not** the headline: success-weighted 158.0557, unweighted mean-of-cell-means 160.0993.
> **Restated in 13 live files; archived trees deliberately left as historical record. Never restate a
> bare 158.0 as the current fleet figure.** Reference implementation:
> `scripts/analysis/open43_fleet_aggregations.py`. See §5.8.
>
> **5. 🔴🔴 THE ADOPTED RUN CANNOT BE REPRODUCED FROM THIS REPOSITORY (OPEN-48, opened
> 2026-08-12 night).** ✅ **Lead with the reassurance, always: `157.1 kWh/m²` is correct and
> complete, elevator energy included — this is a provenance problem, not a physics problem.** The
> adopted `phaseE_elevrb` outputs carry a populated `elevators_eui_kwh_m2` column (**3,561 of 8,160
> rows non-zero, Σ 12,508.8 kWh/m²**), but **live `openubem/idf/builder.py` never calls
> `assign_elevators`** — commit `ef19141` added only the *archived* copies of `builder.py` /
> `outputs.py` / `parser.py` / `carbon.py`. The code that produced the adopted number was never
> committed. The **reporting** half was restored 2026-08-12 night and proved bit-identical on
> meter-absent inputs; **the load wiring was not, deliberately — that is ruling 2d, and it belongs to
> the user.** 🔴 **Never repeat the older phrasing that elevator energy is "folded into
> `equipment_eui_kwh_m2`". It is de-folded OUT of equipment into its own column, and that inversion
> made two independent checks read absence where there was none.** See §5.12.
>
> **5A. 🔴🔴 NEW 2026-08-13 — THE PIPELINE REPRODUCES ONLY WHILE ITS INPUTS NEVER MOVE, and this is
the largest thing the arc has found.** For buildings the classifier cannot identify, the
window-to-wall ratio is drawn at random **as one vectorised block sized by the number of unidentified
buildings, with bounds taken from whichever archetypes are present** (`openubem/semantic/__init__.py:229`).
**So one reclassified building silently re-randomises the windows of every unidentified building in
that neighbourhood** — different window height, different solar gain, EUI swings of ±300 kWh/m² on
buildings nobody touched. Measured on the T04 fleet re-run: every cell whose archetypes moved also
moved in EUI (4 cells, +1.21 to +3.53), every cell whose archetypes matched reproduced to ±0.07.
🔴 **Owed to the user as a ruling: register it as OPEN-49.** See §5.14.

**6. 🔴 THE THREE HELD RULINGS WERE ANSWERED AND ARE BEING EXECUTED — do not re-ask them.**
> **OPEN-45: "fix both, then close."** **OPEN-48: "restore the wiring, re-run the fleet."**
> **OPEN-47: "measure first"** → measured (598/8,160 change archetype) → **ruled: keep area-only,
> document the deviation.** ✅ **The OPEN-47 ruling simplifies the fleet re-run: archetypes do
> not move, so the re-run adds elevators and nothing else.** See §5.13.
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

🟥 **UPDATED 2026-08-18 — THIS IS THE LIVE COUNT AND IT SUPERSEDES EVERY COUNT BELOW.**
**26 live rows / 27 struck / 53 total, contiguous `OPEN-01…OPEN-53`, no row missing and none
duplicated.** Recounted **programmatically over the §1 table body**, not by eye — the script and its
output are quoted in `PLAN_five-items-2026-08-18.md` §8, T06. **Next free item ID: `OPEN-54`.**
The live IDs are **3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 27, 29, 35, 38, 42, 46, 47,
48, 49, 52, 53.** ⚠️ **The reconciliation that keeps tripping people, restated:** 27 struck − 25
retired IDs = **2**, and the two are **OPEN-02 and OPEN-28**, which were folded under OPEN-01 rather
than retired. That is not a miscount. The 2026-08-18 pass closed **OPEN-06, OPEN-37, OPEN-51** and
opened **OPEN-53**.

🟩 **UPDATED AGAIN 2026-08-13 (CP-1 of `PLAN_two-measurements-2026-08-13.md`) — 35 tracked items
(OPEN-01 … `OPEN-50`).** The CP-1 audit opened **OPEN-50** — the test suite rewrites a checked-in
`.gpkg` fixture on every run. Arithmetic: **34 − 0 closed + 1 opened = 35.** 🔴 **Eighth consecutive
pass in which this register grew by AUDITING a result rather than by running a task** — OPEN-50 came
out of a routine `git status` check that two measurement tasks had written only their authorised
files. **Next free item ID: `OPEN-51`.**

🟩 **UPDATED 2026-08-13 — ~~34 tracked items / 34 findings (OPEN-01 … `OPEN-49`)~~ superseded by the
line above.** T04's cause analysis
opened **OPEN-49** — the `wwr` re-randomisation defect — and the user ruled on 2026-08-13 to register
it. Arithmetic: **33 − 0 closed + 1 opened = 34.** 🔴 **Seventh consecutive pass in which this register
grew by AUDITING a result rather than by running a task**: the re-run was commissioned to restore
elevator energy, elevator energy reproduced exactly, and what it found was a defect nobody was looking
for. **Say that plainly — the count going up is the process working, not failing.** The 2026-08-12 text
below is kept as written.

~~**33 tracked items / 33 findings**~~ (OPEN-01 … **OPEN-48**) — **three passes on 2026-08-12, net +1,
and the +1 is the most important thing the day produced.** Arithmetic, stated so it can be checked.
Morning: **31 − 1 closed** (OPEN-33) **+ 2 opened** (OPEN-43, OPEN-44) **= 32**. Evening: **32 − 3
closed** (OPEN-43 ruled and adopted, OPEN-31, OPEN-04) **+ 3 opened** (OPEN-45, OPEN-46, OPEN-47)
**= 32**. Night (three-new-items sweep): **32 − 0 closed + 1 opened** (OPEN-48) **= 33**.
🔴 **The user's standing goal is to reduce open items, and three full passes moved it by one,
upward. Say that plainly, and say why: all six items opened today came from AUDITING a result, none
from running a task.** OPEN-43 from re-deriving the published headline a second way; OPEN-44 from
running the test suite a fix had just unlocked; OPEN-45 and OPEN-46 as incidental findings inside
other tasks; OPEN-47 from the director catching a fabricated citation in an executor's own literature
report; **OPEN-48 from auditing OPEN-46's own reversal.** **Hiding any of them to protect the number
was forbidden by the plan and was not done.** *(2026-08-11 for reference: 35 − 5
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

**Next free IDs: ~~item `OPEN-49`~~ ~~item `OPEN-50`~~ → 🟩 **item `OPEN-51` (2026-08-13: OPEN-49 was
taken by the `wwr` re-randomisation defect on the user's ruling; **`OPEN-50` was taken at CP-1 the same
day by the test-suite fixture-mutation defect**)** · defect `E-LA-42` · UTCI defect `E-UTCI-17`.**
*(No pass on 2026-08-11 or 2026-08-12 opened a defect ID, so the defect counters are unchanged.
**2026-08-12 opened six items across three passes — OPEN-43, OPEN-44, OPEN-45, OPEN-46, OPEN-47,
OPEN-48 — every one of them by auditing.** The register's own `Next free item ID` line had gone stale
at `OPEN-45` and was corrected in the same pass.)*

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

🟥 **UPDATED 2026-08-18 — THIS PARAGRAPH IS THE LIVE HEAD OF THE QUEUE AND SUPERSEDES EVERY
PARAGRAPH BELOW IT.** Two rulings are owed, both new rows at the foot of the table: **`3a`** (OPEN-52's
remedy shape for the `pytest-of-o_iseri` OS lockout) and **`3b`** (the stray `.py` files under `docs/`
and whether `testpaths = ["tests"]` goes into `pyproject.toml`). **Ask `3b` first** — it is cheap, it is
one line of config, and until it is settled every full-suite claim in this arc has to carry a paragraph
of explanation about which command produced it. Then **`3a`**, which is the one with a real decision
behind it. `3b` overlaps the older row `2c`, which is still live and unasked; **put them together, not
twice.** Behind those, the queue is unchanged: **`7` (CP-M2) → `8` (OPEN-11)**. 🔴 **The largest
piece of unstarted work in this arc is not a ruling at all** — OPEN-01's denominator swap was ruled on
2026-08-13, its measurement is on disk, and **its plan doc has still never been written.**


🔴 **The queue changed on 2026-08-12: one ruling was answered and three new ones were opened by the
sweep. Ruling 1 below is now OPEN-43, and it is the one that touches every published number.**

🟩 **UPDATED AGAIN 2026-08-13 (late) — this supersedes every paragraph below it, and it is the live
state of the queue.** `2a` and `2h` were both put to the user, both ruled the same turn, and **both are
now fully executed.** `2h` reconciled the register census; `2a` shipped the tag-rich gate under
`PLAN_open22-tagrich-gate-2026-08-13.md` (CP-1 signed), **closing OPEN-22** and taking the register from
**35 tracked items to 34.**

🔴 **THE TABLE BELOW NOW HOLDS NO UNEXECUTED RULING.** ~~Nothing is owed to the user except rulings 5–8,
so the next thing this arc does is ask ruling 5.~~ **Ruling 5 was put and answered 2026-08-13: the
circumstantial evidence IS sufficient for OPEN-01(c), and the corpus is treated as one code state — as a
ruled assumption, never as a measurement.**

~~🟩 **So the queue is now: 6 → 7 → 8, and ruling 6 is next.** Ruling 5 has been answered, which is the
precondition the "never ask 6 before 5" rule was protecting — **that constraint is now discharged and 6
may be asked.** OPEN-01 is open **on its remedy alone**.~~

🟩 **Ruling 6 was put and answered 2026-08-13: DIVIDE BY THE SIMULATED AREA.** Per-building EUI goes
against the multiplier-aware `.eio` floor area, not `footprint_area_m2 × levels`. **The queue is now
7 → 8.** 🔴 **Two constraints travel with ruling 6 and must be repeated wherever the swap is
implemented:** after it, `building` mode's EUI means *energy per simulated m²* — **internally consistent,
not physically representative** — and **the fleet's 157.1 kWh/m² pooled does not move**, because `auto`
was already correct. **OPEN-01 is now open on implementation, not on a ruling:** it needs a plan doc for
the swap and a before/after per-building comparison across all five modes. **That plan is not yet
written** — it is the largest single piece of unstarted work this arc now owns.

🟩 **Work in flight 2026-08-13 (late): `PLAN_five-items-2026-08-13.md`**, five items chosen on the user's
instruction — **OPEN-50, OPEN-44 (carrying OPEN-13's residual), OPEN-45, OPEN-36, OPEN-26.** One theme:
**the suite and the project's completion records currently assert things that are not true.** None can
move a published number. ~~**T01–T02 dispatched; CP-1 is after T02.**~~ ✅ **CP-1 SIGNED 2026-08-13 by
independent re-derivation.** Suite: **26 failed · 1,859 passed · 10 skipped · 19 errors → 0 failed ·
1,859 passed · 55 skipped · 0 errors** (1446.85s). **OPEN-50 fixed** (hash+mtime unmoved across a full
run, measured either side), **OPEN-44 resolved**, **OPEN-13's collection residual discharged.**
🔴 **State the rider every time this green is cited: a skip is a debt, not a fix — the suite is honest,
not more capable, and 14 of the 45 skips exist only because OPEN-17 has not been ruled.** The check that
proves nothing was smuggled: **passed stayed at 1,859.** ⚠️ **One user action is outstanding** — the
working copy's `tests/fixtures/synthetic_30_archetype_coverage.gpkg` must be `git restore`d by the user;
no session here may run git write commands. ~~**T02b + T03–T05 dispatched; CP-2 closes the plan.**~~
✅ **CP-2 SIGNED 2026-08-13 — PLAN CLOSED, ALL FIVE ITEMS CLOSED.** Final suite, director-run:
**`1860 passed, 55 skipped, exit 0`** (24m47s) — +1 from T02b's coverage split, skips unchanged, and
**OPEN-50's fix held across a second full run.** **OPEN-45 closed with zero live defects and no code
change** (the correct outcome, named in advance); **OPEN-26's two will-not-fix verdicts re-verified at
HEAD**; **OPEN-36 corrected AT SOURCE** — a dated banner in the frozen
`IMPLEMENTATION_phaseC_ml_imputer.md`, on the user's ruling, false half struck not rewritten, **first time
this project has annotated a frozen record.** **Register: 34 → 29, re-counted programmatically (29 live,
20 struck).** 🔴 **Three debts survive the IDs: OPEN-17 still blocks 14 skips; the user still owes a
`git restore`; OPEN-36's sweep skipped T09b and T11.8/T11.8b on purpose.**

⚠️ **One thread left deliberately un-chased, so it is not mistaken for an oversight: coarse accuracy on
the tag-rich fixture is 98/98 = 100% while fine is 88.8%**, so every error is a within-coarse-class
error. **That is OPEN-47's next measurement**, and it is also the reason **not** to add a coarse gate to
that fixture — any plausible threshold would detect nothing.

🔴 **A director-side lesson from this task, recorded because it will recur.** A ~~stalled executor~~ was
reported here and **it was wrong** — the executor was inside an **18m22s scoped full-suite run, which
emits nothing for the whole duration.** Silence was misread as failure and written into three documents
before the evidence arrived. **On this repo, a full scoped suite run is ~18 minutes of total silence.**
The reason the mistake cost nothing is the property to preserve: **the audit re-derived from raw
artifacts instead of waiting on the report**, so the checkpoint stood on its own evidence either way.

~~🔴 **After `2a` is executed, nothing is owed to the user except rulings 5–8**~~, which are unchanged since
2026-08-11 and are ordered: ~~**5** (OPEN-01(c) — is the circumstantial one-code-state evidence
sufficient?) → **6** (OPEN-01's remedy, **never ask before 5**)~~ **both answered 2026-08-13** →
**7** (CP-M2) → **8** (OPEN-11). ~~⚠️ **Ruling 6 must never be put before ruling 5**, or the user is
choosing a fix for an item that cannot close anyway.~~ **The ordering constraint is spent — 5 was put
first, then 6, in that order.**

~~🟩 **UPDATED 2026-08-13, and this is the live head of the queue:**~~ ruling **2d** was answered and has
now been **executed to completion** — the wiring was restored and the fleet re-ran. Executing it
produced **two new rulings, `2f` and `2g` below, and they are the only things this arc is waiting
on.** Ask **2f first** (it is a registration, cheap, and it protects the finding from being lost),
then **2g** (it touches the published headline, so it is the one to slow down on). Everything else in
this table is either spent or lower priority than those two.

| # | Ruling | Where |
|---|---|---|
| ~~1~~ | ✅ **RULED AND CLOSED 2026-08-12 — OPEN-43. The headline is the POOLED figure, `157.1 kWh/m²` = total simulated energy ÷ total simulated floor area. Do not re-ask this; do restate it with its definition every time.** ~~The original question, kept for the record:~~ 🔴🔴 ~~NEW 2026-08-12 — OPEN-43, and it outranks everything else because it is upstream of every figure this project publishes.~~ The adopted fleet headline **158.0** is a **count-weighted mean of the twelve cells' means (158.0298)**. Pool all 8,154 successes at once instead — `Σ(EUI × area) / Σ(area)` — and the answer is **157.0552**, ≈**1.0 kWh/m² lower**. Two other defensible weightings give 158.0557 and 160.0993. **Neither of the two main numbers is wrong; they answer different questions** — but the published figure has **never been described as a mean of cell means anywhere in this project**, and a reader hearing "fleet average" will assume the pooled one. A second oddity to state when asking: **the count weights include the six buildings that produced no energy at all.** `openubem/results/aggregator.py` is per-cell only, so the fleet roll-up lives outside it and its author and intent are **untraced** — this cannot be settled by finding the original intent. ~~**The ruling: which definition the headline should use.**~~ ✅ **ANSWERED: pooled. `157.1 kWh/m²`, restated in 13 live files, archived trees left as record.** | §5.8, register OPEN-43 |
| ~~2~~ | ✅ **ANSWERED 2026-08-12 — and the fixture is built.** The user's answer: the director authors the labels, plus a literature pass for external validation. Delivered: `tests/fixtures/labelled_archetypes_tagrich_v2.csv`, 100 rows, seed `20260812`, labelled from tag evidence by a script that never imports the classifier; **size-guessing 34.0% → 3.1%**; accuracy 88.8% (91.6% excluding fallback). 🔴 **One question is still owed and is now ruling 2a below: the ≥0.70 gate threshold.** ~~The original question:~~ ~~who authors the new labels and how many rows.~~ Frame it with what the rebuild costs: the old fixture must be kept and unedited (OPEN-04's bisect depends on it), historical accuracy figures (92.0 / 84.0 / 88.0%) become non-comparable, and the ≥0.70 gate threshold does not transfer. **Until this is answered the rebuild cannot start**, so this is a short question with a large unblock behind it. | §5.3, register OPEN-22 |
| ~~3~~ | ✅ **DONE 2026-08-12 — the user said proceed as recommended; the director wrote the pointer section into `CLAUDE.md`. OPEN-33 is fully closed. Do not re-ask.** ~~The original question:~~ ~~does the archiving citation-sweep rule also belong in `CLAUDE.md`?~~ OPEN-33 closed by writing it into the head of `docs/PROJECT_CHECKLIST.md`. **A fresh session that never opens the checklist will not know the rule exists** — which is precisely the failure mode that produced 58 dead paths in the first place. The counter-argument is real too: `CLAUDE.md` is loaded into every session and every line added there costs context on every task. **Small ruling; ask it after the two above.** | register OPEN-33 |
| ~~4~~ | ~~**OPEN-22** — a third of the 50-row exam is decided by size-bucketing rather than tag logic.~~ ✅ **RULED 2026-08-12 — REBUILD THE FIXTURE.** The user rejected both cheap options (keep 88% as is; report both numbers) and declared the current exam wrong, *despite* the measurement showing the fallback rows do not inflate it. **Do not re-ask this.** OPEN-22 stays open as **work**, not as a decision. 🔴 **Carry its three consequences into every plan and report:** historical accuracy numbers (92.0 / 84.0 / 88.0%) become non-comparable and **every figure must name its fixture**; the **old fixture is never deleted or edited** (OPEN-04's bisect depends on it); the ≥0.70 gate threshold **does not transfer** to a new exam — repointing it is a separate decision. **Now blocked on one question, which is the next thing owed: who authors the new labels, and how many rows.** | §5.3, register OPEN-22 |
| ~~**2a**~~ | ✅ **RULED AND FULLY EXECUTED 2026-08-13 — option (b). Do not re-ask, and do not re-plan: the code is written, the checkpoint is signed, and OPEN-22 is closed.** Delivered under `PLAN_open22-tagrich-gate-2026-08-13.md` (T01–T02, **CP-1 signed**): `TestTagRichTop1Accuracy` in `tests/test_building_classifier.py` gates the tag-rich fixture at **`>= 0.80`** and measures **88.8% on 98 graded rows**; the old `>= 0.70` gate is untouched at line 1049; `133 passed, no skips`. Director re-derived every figure two independent ways and **proved the gate non-vacuous by hand**. **The executor also reconciled the full scoped suite node-for-node against OPEN-44: 26 failed + 19 errors = 45, the same 45 nodeids, passed 1857 → 1859 (exactly the two new tests).** ⚠️ **One thing came out of it that was not asked for:** coarse on the tag-rich fixture is **98/98 = 100%**, so **all 11 fine errors sit inside the correct coarse class** — that is OPEN-47's next measurement, and it argues **against** ever adding a coarse gate here. ~~and the executor stalled after T01 without writing its report~~ 🔴 **RETRACTED — there was no stall; it was inside an 18m22s silent suite run, and the director misread silence as failure. On this repo a full scoped suite run emits nothing for ~18 minutes.** ~~The ruling as taken, kept for the record:~~ ~~**RULED 2026-08-13 — option (b): KEEP THE OLD GATE, ADD A SECOND ONE.**~~ The user chose to leave `test_fine_top1`'s **≥0.70 against the old 50-row fixture exactly as it is** — it must not be repointed, because OPEN-04's bisect depends on that fixture staying unedited — and to add a **separate** gated test on `tests/fixtures/labelled_archetypes_tagrich_v2.csv` with **its own threshold, ruled at ≥0.80**, which leaves ~9 points of headroom under the measured **88.8%** (91.6% excluding fallback). 🔴 **Two standing consequences of this ruling:** CP-M3 (OPEN-31) before/after evidence must now report **both** exams, and **every accuracy figure in every document must name its fixture** — a bare percentage is no longer meaningful in this project. **This unblocks OPEN-22's last step and, behind it, OPEN-47's office-bin divergence.** ~~The original ruling, kept for the record:~~ 🔴 ~~NEW 2026-08-12 — the accuracy gate's threshold, and it is the last thing blocking OPEN-22 from closing.** The new tag-rich fixture exists and works (size-guessing 34.0% → 3.1%, accuracy **88.8%**). But `test_fine_top1` gates at **≥0.70 against the OLD 50-row exam**, and **a threshold is not transferable between exams** — a harder or easier paper needs its own pass mark. Three options to put to the user: **(a)** repoint the gate at the new fixture and pick a new threshold; **(b)** keep the old gate as-is and add a second, separately-thresholded gate for the new fixture; **(c)** keep the new fixture as a diagnostic only, ungated. Frame the cost: under (a) the historical 92.0 / 84.0 / 88.0% figures become non-comparable to anything future — though note **92.0% is already unreproducible** for an unrelated reason (T10: its answer key was rewritten in the next commit). **No pytest test is wired to the new fixture yet, deliberately — this ruling decides what that test should assert.** | §5.3, register OPEN-22 |
| ~~2b~~ | ✅ **PARTLY ANSWERED 2026-08-12 night — and the question's premise was wrong. The reporting breakout is now implemented and gated (parser, outputs, carbon, aggregator; director re-derived the invariant on a different SQL than the executor used: 12 keys bit-identical, total `0x1.d492d97e88c30p+7` unchanged). No claim needed retracting, because elevator energy was in the adopted run all along.** 🔴 **The real ruling this turned into is 2d below.** ~~The original question:~~ ~~OPEN-46: implement the elevator breakout, or retract the "10th end-use" claim?~~ The live parser reports **9** end-uses; the archived elevator arc's own copy of the parser reports 10, including the de-folding of elevators out of equipment. Three of five archived test files had the expectation **removed** rather than the feature added. ✅ **State the reassurance first when asking: the adopted fleet figure is unaffected — elevator energy is simulated and is inside `equipment_eui_kwh_m2`.** The ruling is about reporting, not physics: **implement the breakout in `openubem/results/parser.py` + `openubem/idf/outputs.py` (and check `carbon.py`'s `gwp_elevators_kgco2_m2` for the same shape), or amend every description of the adopted baseline that calls elevators the 10th end-use.** | register OPEN-46 |
| **2c** | **NEW 2026-08-12 — the 30 stray `.py` files under `docs/`, 5 of them test files.** They violate this project's own hard rule (*no `.py` under `docs/`, ever*), pytest collects them, and **they produce 61 of the 106 failing tests** — 58% of the entire failure count. Two are byte-identical duplicates of live `tests/` files; three have **drifted** from their twins, which is the worse case. **Small ruling, large cleanup behind it:** delete, move out of `docs/`, or exclude from collection. | register OPEN-44, OPEN-46 |
| ~~2d~~ | ✅ **RULED 2026-08-12 ("restore the wiring, re-run the fleet") and FULLY EXECUTED 2026-08-13. Do not re-ask.** What executing it delivered: the load wiring is restored and live; the twelve-cell re-run regenerates the elevator column **exactly** (3,561 non-zero rows, matching cell by cell), so **OPEN-48's own question is answered — the repository now reproduces elevator energy**; and the fleet lands at **159.2157 vs the adopted 157.0552**, a gap that is **not** elevators but the `wwr` re-randomisation defect (§5.14). **The two rulings this created are `2f` and `2g` below.** ~~The original question, kept for the record:~~ 🔴🔴 ~~NEW 2026-08-12 (night) — OPEN-48, and it outranks every other open ruling because it is about whether the published number can be regenerated at all.~~ **The adopted `phaseE_elevrb` run was produced by code that is not in this repository.** Live `openubem/idf/builder.py` never calls `assign_elevators` (`git log --all -S` on that file is empty; commit `ef19141` added only the ARCHIVED copies of `builder.py`/`outputs.py`/`parser.py`/`carbon.py`, plus three orphan live files) — **yet the adopted outputs carry a populated `elevators_eui_kwh_m2` column, 3,561 of 8,160 rows non-zero.** The wiring existed in the working tree at run time and was never committed. ✅ **State the reassurance first: this is NOT a physics problem. 157.1 kWh/m² is correct and complete, elevators included. It is a provenance problem — the number cannot currently be regenerated from version control.** **The ruling: restore the load wiring (≈1 kWh/m² fleet-wide by a load-table estimate, under 1% — and being honest about it implies a fleet re-run), or freeze the adopted run as a historical artifact and document that it is not reproducible from HEAD.** Do not decide this in an executor. | register OPEN-48 |
| **2e** | ⚠️ **NEW 2026-08-12 (night) — OPEN-47: the classifier's office bins drop a condition the source imposes.** Now that the source is identified and verified (Chen, Hong & Piette 2017, *Applied Energy* 205, Table 1 — director-read from the PDF), its rule is **area AND floor count**: `<2322 m² and ≤3 floors`, `2322–9290 m² and ≤5 floors`, `>9290 m² or ≥6 floors`. **`openubem/semantic/building_classifier.py:175-177` tests area only.** Small-sounding, but any change here is a classifier change and therefore gated by CP-M3 (OPEN-31): before/after accuracy on the labelled fixture, both numbers recorded — **and the fixture question (ruling 2a) is itself still unanswered, so 2a probably has to be settled first.** | register OPEN-47, OPEN-31 |
| ~~**2f**~~ | ✅ **RULED AND DONE 2026-08-13 — the user said register it, and the register was written the same turn: `OPEN-49`, its own section after OPEN-48, head amendment, §1 header at 34 tracked items, next free ID re-issued as `OPEN-50`, plus a dated amendment under OPEN-48. Do not re-ask, do not re-write.** ~~The original ruling, kept for the record:~~ 🔴🔴 ~~NEW 2026-08-13 — ASK THIS FIRST. Register the `wwr` re-randomisation defect as OPEN-49.~~ For buildings the classifier cannot identify, the window-to-wall ratio is drawn **as one vectorised block sized by the count of unidentified buildings, with bounds taken from whichever archetypes are present** (`openubem/semantic/__init__.py:229`). **One reclassified building therefore silently redraws the windows of every unidentified building in the same cell** — different window height, different solar gain, per-building EUI swings up to ±300 kWh/m² on buildings nobody touched. **Measured, not inferred:** on the T04 fleet re-run all four cells whose archetypes moved also moved in EUI (+1.21 to +3.53); all eight whose archetypes matched reproduced to ±0.07. **Confirmed not to be nondeterminism** — a repeat run on unchanged inputs is byte-identical at the IDF stage and agrees to 0.00836 kWh/m² at the results stage (§5.14). This is a **registration**, not a fix decision: the ruling is only whether it enters the register as OPEN-49 (next free ID) so it survives this arc. ⚠️ **The register has deliberately not been touched — do not write the entry before the user rules.** | §5.14, register (new OPEN-49) |
| ~~**2g**~~ | ✅ **RULED 2026-08-13 — KEEP `157.1 kWh/m²`. The user was given both sides and kept it. `159.2157` is NOT adopted, is not the fleet figure, and must never be restated as one — it survives only as evidence inside OPEN-49. The accepted cost travels with the number: the published figure is one HEAD cannot reproduce end to end, and OPEN-48's provenance caveat stays live until OPEN-49 is fixed and the fleet is re-run a third time. Do not re-ask.** ~~The original ruling, kept for the record:~~ 🔴🔴 ~~NEW 2026-08-13 — does `159.2157` replace the published `157.1 kWh/m²`?~~ The re-run is the only fleet figure this repository can currently regenerate from HEAD, which argues for adopting it. **The director's recommendation is to KEEP 157.1**, and the reason is not conservatism: **159.2 is not a better model, it is the same model run through the defect in 2f.** Adopting it would publish the bug and would also make the number move again the next time OSM classification shifts. ✅ **Lead with the reassurance when asking: 157.1 is correct and complete, elevator energy included** (§5.8, §5.12) — this is about which of two correct-arithmetic runs is the headline, not about an error in the published one. **Frame the real cost of keeping it:** the published figure then remains one that HEAD cannot reproduce exactly, so the provenance caveat from OPEN-48 stays live until 2f's defect is fixed and the fleet is re-run a third time. **Do not decide this in an executor, and do not let any document quietly restate 159.2 as the fleet figure in the meantime.** | §5.14, §5.8, register OPEN-43/OPEN-48 |
| ~~**2h**~~ | ✅ **RULED AND FULLY EXECUTED 2026-08-13 — retire the three formally. Do not re-ask, do not re-write.** `OPEN-04`, `OPEN-31` and `OPEN-43` now carry closure blocks in their own §-sections, their table rows are struck with the same text, the three IDs are in the §1 header's retired list (ten → **thirteen**), and the table's live rows were re-counted: **35, matching the header.** 🔴 **Three constraints were deliberately carried forward out of the closures:** `92.0%` is unreproducible and the old 50-row fixture is never edited (from OPEN-04); CP-M3 is obligatory and now spans **two exams with two thresholds** (from OPEN-31); the headline is pooled **`157.1 kWh/m²`** and **`159.2157` is never a fleet figure** (from OPEN-43). **A closed item's constraints do not close with it.** ~~The original ruling, kept for the record:~~ 🔵 ~~NEW 2026-08-13 — the register's item count rests on three closures nobody recorded. Cheap, and it decides what number this arc reports as "open".** Repairing the §1 summary table (the five missing rows for `OPEN-45`…`OPEN-49`, written 2026-08-13) exposed a second gap: the table now carries **38 live rows** against a header that says **35 tracked items**, and **the gap is exactly `OPEN-04`, `OPEN-31` and `OPEN-43`**. The §0 arithmetic of 2026-08-12 subtracts all three as closed, and every count since (33 → 34 → 35) is built on that subtraction — **but none of the three is marked closed in its own §-section, none is struck in the table, and none appears in the header's retired list.** Each has a plausible basis (OPEN-04's cause falsified and re-explained; OPEN-31's CP-M3 ruled obligatory 2026-08-09; OPEN-43 ruled 2026-08-12, pooled `157.1 kWh/m²`) — **but this register's own rule is that the sections are the authority, and a plausible basis is not a recorded closure.** ⚠️ **Deliberately not patched: retiring three IDs is not a director-side edit.** The ruling: **retire the three formally (count stays 35), or reopen them in the count (count becomes 38).** State when asking that no content is lost either way and no published number moves. | register §1 head + the repair note under it |
| ~~5~~ | ✅ **RULED 2026-08-13 — THE CIRCUMSTANTIAL EVIDENCE IS SUFFICIENT FOR (c). Do not re-ask.** The corpus is treated as **one code state**, on the single unbroken 111-minute window plus one manifest schema across all 60 pairs. 🔴 **Carry this constraint with it: one-code-state is now a RULED ASSUMPTION, not a measurement, and every document citing it must say so in the same sentence.** The ruling buys the project out of a question this corpus cannot answer — it does **not** create the missing stamp. **If a cross-mode result ever turns on the assumption being exactly true, that result needs a re-run with a recorded commit hash, and this ruling does not cover it.** ⚠️ **OPEN-01 stays open on the remedy alone — that is ruling 6, which is now the next thing owed to the user.** ~~The question as put, kept for the record:~~ ~~**OPEN-01(c), and it is the one that unblocks the biggest item.**~~ OPEN-01's third audit question is *"did all five modes come from one code state?"* **It cannot be proved, and the reason is structural: no commit hash or code-version stamp was recorded anywhere at generation time**, and 25 of the 60 `(cell, mode)` pairs have no generation-summary JSON. The circumstantial evidence is real — one manifest schema across all 60, all 60 written inside one continuous **111-minute** window (2026-08-09 21:03:01–22:54:38), no gaps. **The ruling: is that sufficient for (c)?** If yes, OPEN-01 reduces to the remedy ruling below. **If no, OPEN-01 can never close on this corpus** and only a re-run with a recorded commit stamp would settle it. **Frame both costs before asking.** | §5.1, register OPEN-01 |
| ~~6~~ | ✅ **RULED 2026-08-13 — THE REMEDY IS: DIVIDE BY THE SIMULATED AREA. Do not re-ask.** Per-building EUI is published against the multiplier-aware floor area EnergyPlus actually simulated (read per run from `eplusout.eio`), **not** against `footprint_area_m2 × levels`. **Cheap because the measurement already exists** — `e02_simulated_floor_area.csv`, 40,800 rows, 0 parse failures, 0-unmatched join in all five modes — so it is a **reporting-layer denominator swap**, no re-simulation and no cluster work. 🔴 **Carry these two constraints with it:** (i) it does **not** make `building` mode simulate the right building — after the swap that mode's EUI means *energy per simulated m²*, which is **not** the real building's area, so it is internally consistent but not physically representative and every document must say which it means; (ii) **the published fleet EUI of 157.1 kWh/m² pooled does not move** — `auto` already measured 1.0000 median / 99.63% within ±1%. Fixing the simulation was offered and not taken; that door is not foreclosed. ⚠️ **OPEN-01 still does not close** — it now needs a plan doc for the swap plus a before/after per-building comparison in all five modes. **It is open on implementation, no longer on a ruling.** ~~The question as put, kept for the record:~~ ~~**OPEN-01's remedy** — now that (a) and (b) are measured on 40,800 runs: fix the denominator, fix the simulation, or stop publishing per-building EUI for the affected modes.~~ | §5.1 |
| **3a** | 🔴 **NEW 2026-08-18 — OPEN-52's remedy shape, and it is owed before any plan touches pytest configuration.** `pyproject.toml` carries an **undocumented** `addopts = "--basetemp=.pytest_tmp"`, and the director verified by hand why it matters: the default base temp `%LOCALAPPDATA%\Temp\pytest-of-o_iseri` (dated Apr 1, predating every session in this arc) is **access-denied at the OS level** — both `ls` and `touch` fail with Permission denied. **So the pin has been incidentally shielding every `tmp_path` test in the suite from a lockout nobody recorded.** ✅ **State the reassurance first: nothing is broken today and no published number is involved** — the suite is green inside `tests/` and the pin works. The risk is that the pin looks like clutter to a future reader who removes it, and the suite then fails for a reason that has nothing to do with the code. **The ruling: repair the ACL on `pytest-of-o_iseri` (and then decide separately whether the pin stays), or keep the pin and document why, or a different remedy shape.** ⚠️ **Do not remove the pin in the meantime, and do not let an executor "tidy" it.** | §5.18, register OPEN-52 |
| **3b** | 🔴 **NEW 2026-08-18 — the stray `.py` files under `docs/`, and the one-line config fix behind them. Cheap; ask this one first.** `CLAUDE.md` forbids `.py` under `docs/` outright, yet five test files sit in the read-only `docs_DONE/` archive (since `ef19141`, 2026-07-21), plus `scripts/analysis/test_viewer_layout_assign.py` (`69373f9`, 2026-07-27). One of them, **`test_results_aggregator.py`, collides by basename with `tests/test_results_aggregator.py`**; with no `__init__.py` and pytest's default import mode, **that collision is exactly the 17 collection errors** a bare root-level `pytest -q` reports. ✅ **Reassurance first: this is not a regression and never was** — those files predate the 1875/55/0 baseline, so a bare root run could never have been green, and the baseline was always `pytest -q tests/`. **The ruling: add `testpaths = ["tests"]` to `pyproject.toml` (proposed 2026-08-18, deliberately NOT applied), or move/delete the strays, or leave both and accept that every suite figure must name its command.** ⚠️ **`docs_DONE/` is read-only by this arc's own rules, so deleting from it is a user decision, not a director one.** This is the same population as row `2c` — **ask them together.** | §5.18, register OPEN-44/OPEN-53 |
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

🟢 **CLOSED 2026-08-13 — the net was finally measured (T04 of `PLAN_five-more-items-2026-08-13.md`).**
Artifacts: `openubem/outputs/comparisons/open32_layout_assign_net.csv` (8,153 × 20),
`scripts/analysis/open32_layout_assign_net.py`, report `extra/MEASUREMENT_open-32_net-of-open01-open03.md`.
**Net ≈1.12 at the median — and the median is the worst possible way to say it.** Only **12.6%** of
buildings land within ±10% of true cancellation; `net_med` spans **0.0032 to 19.88**. The denominator
error is **quantized at powers of two** (deciles **[0.316, 0.474, 1.000, 1.999, 4.000]**; 15.4% at ≈1.0,
12.7% at ≈2.0, 10.1% at ≈0.5), i.e. multiplier/storey arithmetic, not continuous area error — which is
exactly why the "median ×2.0" above and the measured median of **0.9999** are both true. **Quote the
deciles, never a single central figure.** The loads share was **measured, not assumed** (median 39.9%,
IQR [33%, 44%]) from per-end-use EUI already present in `t20_layout_assign_eui.csv`.

🔴 **Two corrections the executor made to the manager's plan, both right — recorded because the plan
was wrong.** The published EUI divided by **`declared_area_m2`** (footprint × levels), a column in
neither file the plan named; the executor found it in `t20_harvest_layout_assign.py:244,304` and
`e02_t04_floor_area_audit.py:209` and **proved it numerically** (max diff 1.2e-10) before switching.
It also replaced the plan's assumed loads share with a measurement. **A brief is a hypothesis about
where the data is; an executor that verifies it is doing the job, not deviating from it.**

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

✅ **RULED AND ADOPTED 2026-08-12: the headline is the pooled figure, `157.1 kWh/m²`.** The director
ruled it under the user's delegation ("*la plus bon precision*") because a pooled intensity is the
physical definition of energy per unit area, is what a reader assumes, and — unlike a mean of cell
means — **does not change if the twelve cells are re-cut.** 🔴 **Always quote the definition with
the number.** ~~158.0~~ is struck, never deleted, in 13 live files; `docs_DONE/`, `docs_main/` and
`docs_VALIDATION/` are deliberately untouched as historical record. Both re-derivations (the director's
and the executor's, from different starting files) agree to 4 dp. Reference implementation:
`scripts/analysis/open43_fleet_aggregations.py`.

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

### 5.11 🔴🔴 The rulings-and-five-items sweep of 2026-08-12 (evening) — ten tasks, five executors, and two audit catches that matter more than the tasks

**Plan:** `implemenation/PLAN_rulings-and-five-items-2026-08-12.md`, T01–T10, five parallel executors,
three checkpoints, **every headline re-derived by the director from raw artifacts before acceptance.**
**Closed: OPEN-43, OPEN-31, OPEN-04** (and OPEN-33's last leg). **Opened: OPEN-45, OPEN-46, OPEN-47.**

**What landed, in one line each:**

| Task | Item | Outcome |
|---|---|---|
| T01 | OPEN-43 | **Pooled `157.1` adopted**, 13 live files restated, all four aggregations reproduce to 4 dp. **CLOSED.** |
| T02 | OPEN-33 | `CLAUDE.md` pointer written by the director. **CLOSED.** |
| T03 | OPEN-22 | Tag-rich fixture built. **Size-guessing 34.0% → 3.1%**, accuracy 88.8% / 91.6% ex-fallback. Still open. |
| T04 | OPEN-22 | Literature pass. 🔴 **Headline claim FABRICATED — see below.** Became OPEN-47. |
| T05 | OPEN-44 | All 106 tests triaged, **1 REAL-DEFECT**, 65 artifact-missing. Incidental find became OPEN-46. |
| T06 | OPEN-13 | Skip narrowed: **43 tests recovered**, collection 1,937 → **1,990**. |
| T07 | OPEN-42 | Cause **not locally recoverable** — all six `work_dir`s empty. Incidental find became OPEN-45. |
| T08 | OPEN-36 | **6 governance gaps, not 1.** Bound broken; item grows. |
| T09 | OPEN-31 | CP-M3 gate written in two places, docstring-only diffs. **CLOSED.** |
| T10 | OPEN-04 | Tag-coverage hypothesis **REFUTED** — fallback constant at 17/50 across all four commits. **CLOSED.** |

🔴🔴 **The two things a successor must carry forward from this pass, because neither is in a task
description:**

**1. An executor fabricated an external citation, and only re-derivation caught it.** T04 was sent to
break the project's own circularity on the office thresholds. It returned a confident transcription of
a figure legend from a 2017 IBPSA paper. **The director downloaded the same PDF and searched all 8
pages: the numbers do not appear in it at all.** The "external source" it reported was in fact our own
internal `RESULT_I02:33` restated. **This is the fourth executor headline in this arc that has not
survived re-derivation — and the first that was invented rather than merely wrong.** The audit rule
("re-derive from the raw artifact, never from the report") is now load-bearing against fabrication, not
just against sloppiness. **Do not relax it.** Registered as OPEN-47, which also records a **fabricated
DOI** in `RESULT_I02` itself — it resolves to an unrelated paper about air-handling sensor faults.

**2. The biggest finding of the day was incidental to its task.** T05 was triaging tests. In doing so
it established that **the elevator end-use breakout was never merged into the live tree** — the live
parser has 9 end-uses and no elevator line, the archived arc's own copy has 10 — **and that three of
five archived test twins had the elevator expectation removed rather than the feature added.**
Registered as OPEN-46.

> 🔴 **SUPERSEDED THE SAME DAY — see §5.12. The reassurance originally written here
> ("elevator energy is inside `equipment_eui_kwh_m2`") was WRONG IN ITS MECHANISM, and the conclusion
> the night sweep first drew from re-checking it ("the adopted run has no elevator load at all") was
> wrong too.** What is true: the adopted outputs already carry an `elevators_eui_kwh_m2` column with
> **3,561 of 8,160 rows non-zero**. Elevator energy is **de-folded OUT of** equipment into its own
> column, not folded into it — which is exactly why every check that looked at `equipment_eui_kwh_m2`
> saw nothing. ✅ **The fleet figure is still NOT affected, for a better reason than the one
> given here: the energy was always in the total.** The real defect is reproducibility → **OPEN-48**.

**Executor behaviour worth reinforcing when you write the next kickoff:** T07 refused to substitute a
hypothesis for missing evidence and labelled its corroborating data as coming from a different
campaign; T03 refused to write into `tests/` outside its authorised scope and said so instead of doing
it silently; T10 reported a reproduction miss and traced its cause instead of hiding it. **All three
behaviours were specified in the plan's hard rules. They are worth restating verbatim in future plans.**

### 5.12 🔴🔴 The three-new-items sweep of 2026-08-12 (night) — four executors, three items, none closed, and the audit reversed one of them

**Plan:** `implemenation/PLAN_three-new-items-2026-08-12.md`, T01–T07, executors A/B/C in parallel then
D gated behind CP-1. **Closed: none. Opened: OPEN-48.** Progress log is in that doc's §10.

| Task | Item | Outcome |
|---|---|---|
| T01–T02 | OPEN-45 | Shared whitespace-tolerant matcher + 16 tests; load-bearing one-space sites **2 → 0**; 8,160/8,160 `work_dir`s confirmed empty. **Two live sites remain out-of-scope. Still open.** |
| T03 | OPEN-46 | Probe **stopped without an answer, correctly** — adopted `.sql` do not exist; no substitute generated. |
| T04 | OPEN-46 | Divergence inventory. 🔴 **Headline did not survive re-derivation — see below.** |
| T05 | OPEN-46 | Reporting breakout restored + guarded; invariant re-derived by the director on a different SQL. **Still open** (load wiring deliberately not restored). |
| T06 | OPEN-47 | Erratum appended (64 insertions, 0 deletions); code comment corrected, comment-only. **A second fabricated DOI found.** |
| T07 | OPEN-47 | ✅ **Primary source FOUND** — against a plan that predicted none. Director re-verified from the PDF. **Still open** for a new reason. |

🔴🔴 **The three things a successor must carry forward, because none of them is in a task description:**

**1. The elevator item inverted, and the director's own first check was wrong in the same direction as
the executor's.** OPEN-46 said the breakout "was never merged" and reassured that elevator energy sat
folded inside `equipment_eui_kwh_m2`. Both the executor and the director then checked
`equipment_eui_kwh_m2` between `phaseE` and `phaseE_elevrb`, found it flat for all 87 eligible
buildings, and concluded the adopted run had no elevator load at all. **It has one.** The adopted
`05_results.csv` already carry `elevators_eui_kwh_m2`: **3,561 of 8,160 rows non-zero, Σ 12,508.8
kWh/m²**, `nyc_urban` exactly 87 — and the **median** of `|Δtotal − elevators|` versus the pre-elevator
run is **exactly 0**. ⚠️ **The transferable lesson, and it is the reason this is written here
rather than quietly fixed: a de-folding transform is invisible in the column it de-folds OUT of. Check
the invariant the transform preserves — the total — not the column it moves energy between.**

**2. The real defect is provenance, and it is bigger than the item that surfaced it (OPEN-48).** The
adopted run cannot be regenerated from this repository. ✅ **Always lead with: the published
`157.1 kWh/m²` is correct and complete, elevators included.** Then say what is wrong: the code that
produced it was never committed.

**3. An executor was sent out on a premise the director had to retract mid-flight, and handled it
correctly.** D was briefed that the adopted run contained no elevator load. When corrected, it
**independently re-verified the correction before acting on it** and found a confirmation the director
had missed — the adopted CSV header order matches the archived `_STEP5_COLS` position-for-position. It
also reported a **1-ULP (2.84e-14) movement** it could have hidden, and **refused an out-of-scope test
restoration** rather than making it pass. 🔴 **A mid-flight correction to a running executor is
a normal event, not a failure. Send it, and say plainly which part of the original brief was wrong.**

**Also worth carrying:** the project's own "`**  Severe  **` has two spaces" fact is **half wrong** —
a census of all 64 real `.err` files gives `** Warning **` (one space, 4,881), `** Severe  **` (one
before / two after, 37), `**  Fatal  **` (two both sides, 1). **Route new code through
`openubem/results/err_parse.py` rather than writing a third literal.** And T07's found source is
**CityBES's own case-study table, not an external standard** — say that whenever the thresholds are
described as literature-backed.

### 5.13 🔴🔴 The three-rulings sweep of 2026-08-12 (night-2) — ✅ COMPLETE, all five tasks, CP-2 signed 2026-08-13

**Plan:** `implemenation/PLAN_three-rulings-2026-08-12.md` — **closed to further execution.** T01, T02,
T03 and T05 completed 2026-08-12 (CP-1 signed); **T04 completed 2026-08-13 12:47 and CP-2 is signed at
the foot of §9 of that plan.** Nothing from this sweep is running. **This section was written
incrementally** — the user asked on 2026-08-12 for this prompt to be updated *as each job finishes*,
not only at the close of the arc — and is now final. What the sweep left behind is not work but two
rulings, **2f** and **2g** in §3.

| Task | Item | Status |
|---|---|---|
| T01 | OPEN-45 | ✅ **Done.** Both surviving marker sites routed through `err_parse` (`openubem/simulation/runner.py` → `FATAL_RE`, `tests/test_sim_integration.py` → `iter_severe`). 23 passed. **Item is fixed; only the register entry is outstanding.** |
| T02 | OPEN-47 | ✅ **Done — measured, decided nothing.** Flag `use_floor_count`, default OFF, threaded through the classifier. **598 / 8,160 (7.3%) change archetype, all promotions; 437 newly gain elevator eligibility.** |
| T05 | OPEN-47 | ✅ **Done.** Deviation written into `building_classifier.py` as comment-only (director-verified by reading the block, not the report). 131 passed. **Item is closeable.** |
| T03 | OPEN-48 | ✅ **Done — the wiring works and the effect is measured.** austin_urban, 850 real EnergyPlus runs on Speed (arm A `1222996`, arm B `1223029`, 425/425 `COMPLETED` each, zero failures). **Arm A: 56 of 425 buildings carry elevator energy. Arm B: exactly 0.** Pooled cell EUI **250.6512 (A) vs 244.5245 (B) = +6.1267 kWh/m2, +2.5056%.** 38 passed. |
| T04 | OPEN-48 | 🟡 **All twelve cells landed 2026-08-13 01:42 (director-run); the fleet number exists but is NOT adoptable yet.** Re-run pooled fleet EUI **159.2157** vs adopted **157.0552** — **+2.16, +1.4%**. Two controls pass exactly: 8,160 buildings / 8,154 success (the same 6 known failures), and **3,561 rows carry elevator energy, cell by cell identical to the adopted run** — so the wiring reproduces. 🔴 **The +2.16 is a defect, not a better model:** it comes entirely from four cells whose classification drifted, through the random-`wwr` mechanism below. ✅ **Confirmatory repeat of `nyc_centre` COMPLETE 2026-08-13 12:47 and it closed the question at both stages** — 738/738 IDFs byte-identical, results max Δ **0.00836 kWh/m²**, cell EUI Δ **−2.8e-05**. **CP-2 signed.** |

🔴🔴 **How T04 was executed, and what a successor must not undo.** ⚠️ **Read this in the past tense —
T04 finished 2026-08-13 12:47 and nothing described below is still running.** It is kept because the
execution shape, the traps it hit, and the artifacts it left are what a successor needs before
touching any of it.

The fleet re-run is being driven **by the director, not by an executor** — see point 3 below for why.
The user approved parallel execution on 2026-08-12 and then went to sleep, instructing the director to
carry it to the end and update this prompt and both plans' progress logs as it goes.

**The sequential driver was the bottleneck, and it was not a cluster problem.**
`scripts/validation/open48_fleet_rerun.py` loops the twelve cells one after another. `nyc_centre` took
**~2 h 20 min** — of which the ~26 min IDF-generation step is `n_jobs=1` **serial local** work
(`v12_cell_pipeline.py:210-212`) that happens *before* anything ships to Speed. Twelve cells that way is
over a day, with one of twenty local cores busy and Speed idle between cells. 🔴 **An empty `squeue`
during this run was a symptom of that serialization, not evidence of local simulation** — all 738
`nyc_centre` simulations ran on Speed under `sbatch`, as the rules require. Do not "fix" this by
reasoning about local-vs-cluster; the fix is concurrency.

**Replacement: `scripts/validation/open48_fleet_rerun_parallel.py` (new file).** Eleven remaining cells,
**six concurrent**, each its own process and log, staggered 180 s to avoid an SSH burst against
`speed-submit2`. It calls the same `run_cell` with the same `output_subdir="open48_refleet"`;
**`v12_cell_pipeline.py` is untouched**, as §2 of the plan requires. Six cells use six of twenty local
cores, and each cell still submits its own array capped `%32`, so neither the login-node rule nor the
fair-share cap is stressed. Live state: `%TEMP%\open48_par\STATUS.txt` plus one log per cell.

**The kill point was verified clean before the switch** — the only `open48_refleet_*` directories on
Speed were `nyc_centre`'s and the queue was empty, so the interrupted `nyc_urban` had shipped nothing
and only locally regenerable work was discarded. `run_cell`'s step-1/step-2/EPW caches survive.

🔴 **The arithmetic trap, already hit once.** A pooled EUI weighted by `footprint_area_m2` alone is
**not** comparable to `157.0552`. The adopted arithmetic weights by
`footprint_area_m2 × levels.clip(lower=1)`. Use `scripts/analysis/open43_fleet_aggregations.py`'s
arithmetic; never hand-roll it. And never compute a "fleet" figure from a subset of cells.

🔴🔴 **The four things a successor must carry forward:**

**1. The OPEN-47 ruling is "deferred, not rejected", and the reason is double-weighting.** The source
(CityBES's own Table 1) conditions on floor count *and* area; OpenUBEM applies area only. Of the 598
buildings the floor-count bound would move, **only 85 (14.2%) rest on an OSM-observed floor count** —
57.9% come from a height heuristic, 27.9% from a use-class group median. And `total_floor_area_m2`
**already** multiplies by that same imputed `levels`, so the bound would make the archetype depend on
one imputed quantity twice, then propagate it into elevator eligibility. `use_floor_count` stays in the
code, default OFF, **as the evidence for the decision — not as a deprecated path.** Reopen it the day
floor-count coverage improves.

**2A. 🔴🔴 CORRECTION, made 2026-08-13 from T04's own data: "the new fleet EUI must exceed
157.0552" is the WRONG success criterion. The target is reproduction, and the expected fleet
delta is ≈ 0.** The claim in point 2 below (and in §9 point 2 of the plan) conflated two
different comparisons:

- **T03's +2.5056%** is *restored wiring* vs *repo `HEAD` with the wiring missing* — a comparison
  against the **broken repository**. It proves the two-line `builder.py` fix works. It stands.
- **T04** is *restored wiring* vs the **adopted `phaseE_elevrb` run**, and the adopted run
  **already contains elevator energy** — 3,561 of 8,160 buildings, Σ 12,508.8, established by the
  OPEN-46 reversal. OPEN-48 never claimed the adopted numbers lacked elevators; it claimed the
  **repository could no longer regenerate them**.

**Four cells confirm the corrected expectation.** `nyc_rural`, `nyc_suburban` and `nyc_urban`
reproduce the adopted pooled cell EUI to **±0.0000** with archetypes identical and elevator
counts/sums matching building-for-building (27/27, 980/980, 87/87). 🔴 **A large positive fleet
delta would now be the alarming outcome, not the reassuring one.** The non-vacuity control is
**not** the delta — it is the elevator column being non-zero and matching the adopted per-cell
counts, and it passes.

🔴 **One cell does not reproduce: `nyc_centre`, +3.5344 (+2.10%), 73 of 738 buildings differing
by −361 to +321, and 5 archetype moves (4 `Courthouse` → `OpenUBEMUnknown`).** Ruled out by
direct comparison: geometry identical on all 738, same EPW file, same E+ 23.1.0, `n_severe`
identical building-for-building, and every source file last modified 17:38–17:59 while the first
cell started 19:31 — **so all twelve cells ran against one unchanging tree.** The differing set
is enriched in severe errors (mean `n_severe` 0.41 vs 0.10) and is the tall/complex archetypes.
**Being resolved by re-running `nyc_centre` a second time, with run-1 preserved**; full
disposition and the three-way decision rule are in §8 of the plan. **No fleet figure is to be
reported until it is settled.**

**2. ⚠️ Superseded in part by 2A — the fleet re-run adds elevators and nothing else, and T03 proved that on real data.**
Because archetypes do not move, T04 is a clean single-variable change against the adopted
`phaseE_elevrb` run. **Any archetype difference in the T04 output is a bug, not an expected
consequence.** T03's two arms were verified identical in `archetype_id` and `floor_area_m2`
building-for-building, so the +2.5056% it measured is attributable to elevators alone. Its
end-use decomposition is worth carrying: **+4.8684 elevator electricity, +0.6655 cooling,
+0.5970 fans, +0.1660 pumps, -0.1694 heating, and lighting/equipment exactly 0.0000.** About
**a fifth of the effect is HVAC responding to elevator waste heat**, not the elevators
themselves. 🔴 **Expect the fleet delta to be positive and the new fleet EUI to exceed
157.0552. Zero or negative means the wiring never reached the cluster — do not report it as
success.**

**3. 🔴 The backgrounded-monitor stall has now killed executors on this arc FIVE times, twice
on T03 alone.** T03's first executor wrote all of its code and then died waiting on a backgrounded
monitor — it never submitted a single job, proved by `sacct -X -S 2026-08-11` returning **zero rows**
for the user, not by reading its report. Its replacement was told verbatim *"do not background a
monitor and wait for it"* — **and backgrounded the harvest anyway and stopped.**
🔴🔴 **Writing the prohibition into the brief does not prevent it. Assume the executor will
do it.** What actually worked, twice: **the launched process survives the agent that launched it**, so
the director polls for the artifact on disk (`squeue`, `sacct`, or the output file) with a cheap
background shell loop and picks the work up when it lands. Budget for the executor dying and plan to
finish the task yourself. Note also that a stopped agent can re-fire repeatedly at ~70k tokens a cycle
while telling you nothing new — **stop it rather than let it poll.**

**4. ✅ The §5 fact-6 regression hex is dead — replace it, do not chase it.** The recorded
`total_eui_kwh_m2` hex `0x1.d492d97e88c30p+7` came from a one-off harness that was never saved, and its
manifest row cannot be reconstructed, so **that number is not reproducible and should not be cited as a
standing invariant again.** The claim it stood for was re-established during T03 on far better
evidence: **arm B's 425 genuinely meter-absent SQL files, `HEAD`'s parser loaded side-by-side with the
working-tree parser, 13 shared float keys per building, bit-identical on all 425**, the only difference
being the added `elevators_eui_kwh_m2` key reading `0.0`. Cite that instead.

### 5.14 🔴🔴 T04 finished overnight — and it found a bigger defect than the one OPEN-48 was opened for

*(Written 2026-08-13 morning. Full evidence in §8 of `PLAN_three-rulings-2026-08-12.md`.)*

**The fleet is complete.** All twelve cells are on disk under `open48_refleet`. The two cells that
died on SSH transport (`la_rural` on `scp`, `austin_urban` on a `squeue` poll — six concurrent cells
saturating the link to `speed-submit2`, not a modelling or capacity failure) were re-run one at a
time by `scripts/validation/open48_fleet_retry.py` and both returned **rc=0**. No cell was counted on
a failed attempt, and no `REUSED_REMOTE` fired anywhere.

**The numbers, computed with `scripts/analysis/open43_fleet_aggregations.py`'s own arithmetic:**

| quantity | adopted `phaseE_elevrb` | re-run `open48_refleet` |
|---|---|---|
| pooled fleet EUI | **157.0552** | **159.2157** (+2.16, **+1.4%**) |
| buildings / successes | 8,160 / 8,154 | 8,160 / 8,154 (**same 6 known failures**) |
| rows with elevator energy | 3,561 | **3,561**, cell by cell identical |

✅ **OPEN-48's own question is answered: the repository regenerates the elevator energy.** The
elevator column matches the adopted run building-for-building in every cell. **The +2.16 is not
elevators.**

🔴🔴 **CAUSE FOUND, and it is a reproducibility defect in its own right. The IDFs were compared
directly** — the adopted run's are still on Speed next to the re-run's. Buildings that reproduce
differ in **6 lines**, and only in the order three `Output:Meter` names are listed: cosmetic, no
energy effect. Buildings that move differ in **hundreds of lines of window-vertex Z-coordinates** —
the window head and sill shift, which changes solar gain and explains the observed ±300 kWh/m²
swings.

**Window size comes from `wwr`, and for `OpenUBEMUnknown` buildings `wwr` is drawn at random**
(`openubem/semantic/__init__.py:229`, one seeded RNG per run at `:297`). Two properties make it
fragile: **the draw is one vectorised block sized by the number of Unknown buildings**, and **its
bounds are `min`/`max` over whichever archetypes are actually present**. Therefore:

> 🔴 **One reclassified building silently re-randomises the window-to-wall ratio of every
> `OpenUBEMUnknown` building in the same neighbourhood.**

**The cohort counts confirm both routes.** `nyc_centre` gained exactly 4 Unknown buildings (its 4
`Courthouse` → `OpenUBEMUnknown` moves) and has the largest shift, +3.53; `austin_centre` +1.76,
`la_centre` +1.60 and `la_urban` +1.21 kept the same Unknown count but changed which types were
present. **All seven cells with unchanged classifications reproduce to ±0.07 or better.** The exact
split is on one observable — `archetype_id` inequality — with no cell on the wrong side of it. The
earlier "it is the dense `*_centre` cells" framing is **wrong**; `la_urban` is the counter-example.

🔴 **This should be registered as OPEN-49 and ruled on by the user.** It is larger in consequence
than the missing elevator wiring: the pipeline reproduces only while the inputs never move.

⚠️ **Why the classification drifted at all is still open and must not be asserted.** The re-run
fetched OSM fresh; the adopted run fetched earlier, and `Courthouse` → `OpenUBEMUnknown` is what
upstream tag removal would look like. **But the adopted run's input `01_buildings.gpkg` no longer
exists**, so the two fetches cannot be diffed. **Leading hypothesis, not a measurement.**

**The confirmatory test is running now, and it has a sharp prediction.** Because the generator is
seeded, a repeat on unchanged inputs must reproduce run-1 **bit-for-bit**; if it drifts again, the
diagnosis is incomplete and an unseeded source remains. ⚠️ **The first launch of it (2026-08-12
01:43) died instantly on a `SyntaxError` in the `python -c` one-liner that started it and nobody
noticed for seven hours — check that a launched process is alive, not merely launched.** Relaunched
2026-08-13 09:06 as a real script file (PID 4316), into `output_subdir="open48_repeat"` (fresh remote
dir, so no REUSE trap), with run-1's cached `01_buildings.gpkg` / EPW copied into the new work dir
**so step 1 loads the cache instead of re-fetching OSM** — otherwise the run would not be on
unchanged inputs and would not test anything. Confirmed on launch: 738 buildings from cache,
738/738 IDFs generated, remote probe `0/738`, **SLURM job `1232712`** submitted 09:33 as
`--array=1-738%32`. Run-1's `05_results.csv` and manifest are preserved in the session scratchpad
(`nyc_centre_run1/`).

✅ **ANSWERED 2026-08-13 09:45 — and answered at the model-generation stage, which is stronger than
the results-stage test the plan called for.** The two runs' staged IDF sets were MD5-compared file
by file: **738 vs 738, 738 shared, `DIFFERING=0` — every IDF byte-identical.** 🔴 **On unchanged
inputs the pipeline reproduces bit-for-bit, seeded random `wwr` included. No unseeded source
remains.** The branch that fired is *run-2 ≈ run-1, both ≠ adopted* → **the adopted-vs-re-run
difference is in the INPUTS, not in nondeterminism.** The chain is closed end to end: inputs
drifted → classification moved → the Unknown cohort's `wwr` was redrawn → window geometry moved →
EUI moved. ⚠️ **Still not settled, and do not claim it: *why* the classification drifted.** The
adopted run's `01_buildings.gpkg` is gone, so the two OSM fetches cannot be diffed.

🔴 **`157.1 kWh/m²` remains the published figure.** Replacing it with 159.2 is the user's ruling and
the recommendation is to wait: **159.2 currently carries a known defect rather than a better model.**

⚠️ **One honest residual:** `la_rural` moved by **+0.0657** with archetypes identical and zero
Unknown buildings, on 3 of 144 buildings. Too small to affect any conclusion, and **not explained by
the mechanism above.**

**The repeat run's `FAILED` array tasks are not a defect — they are one more confirmation.** Three
`nyc_centre` buildings (`way/265302168`, `way/266149332`, `way/266170765`) blow up on the first
attempt with `CalcHeatBalanceInsideSurf: temperature of -4020212.95 C`, and they blow up **in both
runs, same buildings, same severe, same zone.** The pipeline's repair → reroute path already
absorbed them in run-1 (`…_nyc_centre_reroute/out` = `EnergyPlus Completed Successfully`), which is
why `05_results.csv` has all 738 rows with no null EUI and the fleet's 6 counted failures are still
5 `la_rural` + 1 `la_urban`.

⚠️ **Trap for anyone auditing the remote fleet dirs:** a cell's main `out/` keeps the *first
attempt's* fatal `eplusout.err` / `.end` even after the reroute succeeds elsewhere. Counting fatals
under `out/` gives **12 fleet-wide where the true failure count is 6.** Always read `…_reroute/out`
before calling a building failed.

✅ **The results-level comparison is now done too (2026-08-13 12:47) and it agrees.** The repeat run
finished `738/738` (job `1232712`, repair `1233881`) and wrote its `05_results.csv`. Against run-1:
**738 shared `osm_id`, no null EUI in either, 37 of 738 rows differ at all, largest difference
0.00836 kWh/m²**, cell EUI Δ = **−2.8e-05**. The residual sits only in `cooling` and `fans` — the
iterative HVAC solver — with `lighting` and `equipment` bit-identical, i.e. EnergyPlus float noise
on the same IDF, four orders of magnitude under the +2.16 kWh/m² gap. The three repair buildings
come back at exactly 394.6826 / 873.3690 / 396.6100 in both runs. 🔴 **Conclusion unchanged and now
closed at both stages: the fleet discrepancy is in the inputs (`wwr` re-randomisation), not
nondeterminism.**

### 5.15 🔴🔴 The five-more-items sweep of 2026-08-13 — two items closed, **two new ones opened by the audit**, and the two most useful findings were about how we work

*Plan: `implemenation/PLAN_five-more-items-2026-08-13.md` (T01–T05, CP-1 and CP-2 both director-signed).*

**What it took on and what happened.** OPEN-13 (T01, fix), OPEN-27 (T02, pin), OPEN-24 (T03, run the
gate), OPEN-32 (T04, measure the net), OPEN-29 (T05, re-check eight defect IDs).
**Closed: OPEN-24, OPEN-32.** **Still open: OPEN-13** (E-UTCI-12 residual), **OPEN-27** (only the user
can edit DESIGN), **OPEN-29** (the remaining measurement is cluster-only, now established rather than
assumed). **Opened: OPEN-51, OPEN-52 — both found by the director auditing, not by any task's stated
question. That is now eight consecutive passes in which this register grew that way.**

🔴 **Read §5.5 (OPEN-32) and the last five Evidence rules in §7 before planning anything.** The
substance of this sweep lives there, not here. In particular: the deciles-not-median rule, the
regression-test-vacuity rule, and the never-run-concurrent-pytest rule all came out of this pass.

**Three things about *process* that cost more than any of the five tasks.**

1. **A test that pins the fix to itself is worse than no test**, because it reports green forever. See
   the vacuity rule in §7 — and note the executor's own non-vacuity check passed. **Only mutating the
   upstream authority settles it.**
2. **The manager's plan was wrong twice in one task and the executor caught both** (§5.5). Neither was
   a judgement call; both were checkable, and it checked. **Brief executors to verify where the data
   is, not to trust the brief's file names.**
3. **A "failing test" was the director's own parallel dispatch destroying the executor's scratch
   directory** (OPEN-52). The executor's report was accurate; the manager's dispatch was not safe.
   **Before disbelieving an executor, check whether the harness could have done it.**

⚠️ **One near-miss worth carrying.** An executor ran a **tree-wide `git stash`** to isolate a baseline
and swept up two other arcs' uncommitted work; the `pop` then aborted on a `.gpkg` conflict. Everything
was recovered — both dropped stashes were still reachable via `git fsck --unreachable` and every file
diffed clean against the live tree — **but by luck.** The prohibition is now in §7's *Never* list with
the reason attached. **Put it in every brief.**

**The whole-tree suite, CP-2.** Run alone, 21 minutes: **`1910 passed, 35 failed, 55 skipped, 17 errors
in 1262.90s`**. 🟢 **Zero failures and zero errors under `tests/`** — nothing this arc touched is red,
and OPEN-44's `tests/`-scoped closure holds. All 52 non-passing results reduce to **two** causes: 51 are
one missing IDF template inside the **archived** elevators copy under `docs/docs_DONE/` (a
where-the-files-sit artefact, not a code defect), and 1 is the `zones_found` `NameError` in
`scripts/analysis/test_viewer_layout_assign.py:24` that OPEN-44 catalogued on 2026-08-12 and nobody has
fixed. 🔴 **Consequence for planning: checklist item 2c (stray `.py` under `docs/`) is not a tidiness
item — those files put 51 red results into every whole-tree run, and a suite permanently red by 52
cannot be used as a gate by anyone who has not memorised which 52.** Full accounting in the register's
OPEN-44 amendment of the same date.

### 5.16 🔴🔴 The OPEN-49 + OPEN-01 plan of 2026-08-13 — approved, dispatched, and **stopped partway with shipped code left edited and unverified**

*Plan: `implemenation/PLAN_open-49-and-open-01-2026-08-13.md`. **Progress log is §8.** Checkpoints:
CP-1 after T04, CP-2 after T08.*

**This is the first plan in the arc that was authorised to CHANGE shipped code that moves published
numbers.** Read the four rulings before touching it — they were the user's, given one at a time, and
they bound the remedy:

1. **Scope = OPEN-49 + OPEN-01 only.** Checklist item 2c, OPEN-51, OPEN-52 and the OPEN-44
   `zones_found` `NameError` were **explicitly excluded**. Do not widen.
2. **Keying = a stable per-building seed, applied to all four PDE columns**, not `wwr` alone.
3. **Bounds = a fixed table**, independent of which archetypes happen to sit in the cell.
4. **Fleet = the fix plus a before/after on the twelve cells. NO third fleet re-run.
   `157.1 kWh/m²` pooled stays published.**

**🔴 The director's own reading widened the defect before the plan was written, and this is the part
the register did not have.** OPEN-49 is registered as a **window** defect. The code shows the same
block draw governs **eight fields, not one**: the four `pde_cols` (`lighting_w_m2`, `equipment_w_m2`,
`occupant_m2_per_person`, `wwr`) **plus four setpoint columns** (`heating_setpoint_c`,
`cooling_setpoint_c`, `heating_setback_c`, `cooling_setup_c`) that take a `median()` over the same
present-archetype table. **Say "eight fields" from now on, and never repeat "the wwr defect" as the
whole of it.** T08 was to write that widening into the register; **T08 has not run**, so **the
register still understates OPEN-49.**

**Two independent coupling routes, and a remedy that invents nothing.** Route 1 is *block size* —
one vectorised `rng.uniform(lo, hi, size=n)` sized by the Unknown count. Route 2 is *bounds* — `lo`/`hi`
taken from the archetypes present in the cell. 🟢 **The "fixed table" ruling 3 asks for already exists
in the code**: `_get_cross_archetype_loads()` is the all-Unknown fallback, so making it unconditional
at the call site gives a fixed table **without inventing a single number** — which this project
forbids. That is a one-argument change.

⚠️ **The single most likely way to get the seeding wrong: Python's builtin `hash()` is salted per
process (`PYTHONHASHSEED`).** Using it for the per-building seed would make runs irreproducible — the
exact opposite of the fix. **`hashlib.blake2b(osm_id, digest_size=8)` is pinned in the plan's §4.**

**What actually happened: the executor stopped mid-plan.** On disk at 2026-08-14:
`tests/test_semantic_unknown_draw.py` exists with one test per route, and
`openubem/semantic/__init__.py` carries the T02 edit (`_per_building_rng` via `blake2b`;
`_get_cross_archetype_loads()` unconditional at the call site). **T03 and T04 never started, no
before/after CSV exists, and §8 of the plan is empty.** 🔴 **The edit was therefore never tested,
never audited and never signed** — see the RESUME box at the head of this file. **The T01 tests were
never observed to FAIL on unmodified code, so the defect is not yet pinned and the fix is not yet
evidence of anything.**

**Three guards the CP-1 audit must check, all written into the plan before dispatch:**

1. **T01 must fail before T02 fixes anything.** The old behaviour has to be demonstrated first.
2. **T02's test must be proved non-vacuous by mutating the upstream authority** — the vacuity rule
   from §5.15 applies here directly.
3. **T04 measures a change in INPUTS, not in EUI** — no simulation is run, so **no EUI claim may be
   made from it.** The `.md` must say so in its own words.

**What OPEN-49 will and will not do at the end of this plan.** 🔴 **It will NOT close.** The mechanism
gets fixed and measured; closure depends on the third fleet re-run the user declined in ruling 4.
**OPEN-01 *can* close** if its three ruling-6 deliverables land.

**The OPEN-01 half (T05–T08) is fully ready and needs no cluster.** The remedy is to divide by the
multiplier-aware area EnergyPlus actually simulated — read from `eplusout.eio` as
Σ(`Floor Area` × `Zone Multiplier` × `Zone List Multiplier`) over zones marked
`Part of Total Building Area = Yes` — **not** `footprint_area_m2 × levels`. It is cheap because the
measurement already exists (**40,800 rows** in `openubem/outputs/comparisons/e02_simulated_floor_area.csv`)
and because `parse_building()` already receives `sql_path`, whose sibling is the `.eio` — **no
signature changes anywhere**. ⚠️ **Two denominators must move together** — `openubem/results/parser.py`
and `openubem/results/aggregator.py` — or cell EUIs become internally inconsistent. **Reuse
`scripts/analysis/e02_t04_floor_area_audit.py`'s parser; do not write a second one that could
disagree.** 🟢 **The adopted baseline does not move**: `auto` measures 1.0000 median, 99.63% within ±1%.
**The honest framing, which must travel with it: this makes `building` mode internally consistent, not
physically representative.**

🟢 **Blast radius is bounded, not asserted.** DESIGN §3E's probabilistic KDE branch would extend the
same coupling to *identified* buildings, but `LOAD_MODE = "deterministic"` (`openubem/config.py:61`)
means it is **off**. **Do not claim identified buildings moved.**

**🟩 JOURNAL, T05–T08, completed 2026-08-17.** The OPEN-01 half is done. `resolve_simulated_floor_area()`
(new, `openubem/results/parser.py`) reads `eplusout.eio` via a verbatim lift of
`e02_t04_floor_area_audit.py`'s parser; `parse_building()` resolves `floor_area_m2`/
`floor_area_provenance` once per building and threads it through `_compute_eui()` (backward-compatible
optional param — the ~20 existing direct tests of that function were unaffected) and every failure
path; `aggregator.py::compute_neighbourhood_summary()` reads the same column from the joined results
frame instead of re-deriving it, falling back per-row only where the column is absent (synthetic test
GeoDataFrames). T05's `la_urban/way_401904735` reproduction matched the director's CP-2 figures exactly
(1.333309 layout_assign, 0.333333 building) — no STOP. T06 added 7 non-vacuous tests
(`tests/test_results_denominator.py`) for the three named `.eio` cases. T07 reproduced all five
targets exactly on 40,800 rows (`auto` 1.0000/99.63%, `floor` 1.0000/98.43%, `fast_zone` 1.0000/94.80%,
`layout_assign` 0.9999/15.37%, `building` 0.5000/39.94%) and reported deciles, not the median alone
(`openubem/outputs/comparisons/open01_denominator_swap.csv` + `_summary.csv`,
`extra/MEASUREMENT_open-01_denominator-swap.md`). **OPEN-01 is now CLOSED and ID-retired** in the
register (its own §1 row struck, §-section amended) — all three ruling-6 deliverables landed. OPEN-49
is amended with the Fact-3 widening (eight fields) and T04's before/after but **stays open**, marked
mechanism-fixed/closure-blocked on the OPEN-48 re-run ruling 4 declined, exactly as this section
predicted. Full suite run alone, both after T06 and at CP-2, showed zero new failures against the
1868-passed/55-skipped/0-failed baseline. Full account: this plan's own §8 progress log.

### 5.17 🟩🟩🟩 The overnight autonomous run of 2026-08-17 — task-by-task log

**Why this section exists.** The user went to sleep on 2026-08-17 with the instruction to carry the
arc to the end and **update this prompt at every step, not only at checkpoints**. Everything below is
appended as it happens, newest entry last. It is a log, not a plan: the plan is
`implemenation/PLAN_open-49-and-open-01-2026-08-13.md` and its own progress log is that file's §8.

**State at the start of the run.**

| Fact | Evidence |
|---|---|
| Working tree clean | `git status --porcelain` → empty |
| The OPEN-49 fix is committed, not loose | `82bbd25`, 2026-08-14 — `git show --stat 82bbd25` |
| Pre-fix source recoverable read-only | `git show 82bbd25^:openubem/semantic/__init__.py` |
| T01's test file exists, two tests, one per route | `tests/test_semantic_unknown_draw.py`, 95 lines |
| T01's FAIL proof missing, T03/T04 not started, §8 empty | plan doc §8 holds only its italic instruction line |
| Nothing on Speed, nothing needed | no cluster work in T01–T08 by the plan's own rule 3 |

**Entries.**

- **2026-08-17 — T01–T04 dispatched.** Fresh Sonnet executor (never the stopped one), background,
  on T01 → T04 stopping at CP-1, carrying the three state corrections the plan text predates (see the
  RESUME box at the head of this file). In flight at the time of writing.
- **2026-08-17 — board artifact reordered (outside the plan, at the user's request).** Counters,
  filters and the work-package task list now open the page; the whole dated narrative moved to a
  **Notes & history** section at the foot. Reorder only — verified by a sorted-token diff of old
  against new: **additions only** (the new CSS block and the section wrapper), **no text removed and
  no number changed**. Source `implemenation/board_published-numbers.html`, mirrored identically to
  `reporting/`, republished to the same artifact URL.
- **2026-08-17 — the counter question, answered here so it is not re-asked.** The board's
  `all 102 / done 78` is a **cumulative count of board tasks across work packages A…S**; finished
  packages are never removed, so the total only rises and **it is a log, not a progress bar**. The
  number that actually converges is the register's tracked-items count. Nothing is wrong with the
  board.

- **2026-08-17 — CP-1 REPORTED, AUDITED, AND SIGNED (director).** The executor returned T01–T04
  and stopped at CP-1 as instructed. Audited against raw artifacts on disk, not against the report:

  | What CP-1 owed | Verified how | Verdict |
  |---|---|---|
  | T01 pre-fix FAIL, both routes, real drift | §8 entry quotes per-column max\|Δ\| (route 2: `equipment_w_m2` 5240.36, `wwr` 0.2318); pre-fix source obtained with `git show 82bbd25^:…` + plain copy, restored, `git status` empty | ✅ |
  | T02 non-vacuity | first probe (re-seed per row, ignore `osm_id`) did **not** fail and was **correctly rejected as non-probative** — it is order/count-invariant by construction; the accepted probe restores the **shared** stream (the real pre-T02 mechanic): route 1 FAILS, route 2 still passes, exactly the expected split | ✅ |
  | T03 eight columns, both routes | table in §8: pre-T02 route 1 moves `equipment_w_m2` only; route 2 moves **all eight**; post-T02 **none** move on either route → no third route, no STOP | ✅ |
  | T04 twelve cells, no EUI claim | CSV present, header carries min/mean/max before+after for all eight columns, **12 rows, exactly the twelve cells**; `.md` opens with the no-EUI-claim block and does not re-derive ±300 kWh/m² | ✅ |
  | Full suite run alone | **1868 passed, 55 skipped, 0 failed**, 1663.13s, after the T03 edit landed — matches the 2026-08-13 baseline of 0 failed / 0 errors | ✅ |
  | `openubem/semantic/__init__.py` untouched | absent from `git status --porcelain` → still identical to `82bbd25` | ✅ |

  **The one substantive finding, recorded so T08 cannot lose it.** T04's expected pattern **does not
  reproduce**: the four cells OPEN-49 flagged as moving (`nyc_centre`, `austin_centre`, `la_centre`,
  `la_urban`) show **no distinctly larger** before/after delta than the eight that reproduced.
  Nearly every cell has almost all of its Unknown buildings' `wwr` move by >0.01, and the count
  tracks **cell size**, not moving/reproducing status (`nyc_suburban` 272 of 290; `la_rural` 0 of 0).
  The executor's reading is accepted: the two experiments sit on **orthogonal axes** — T04 holds
  classification fixed and swaps code, OPEN-49's original held code fixed and swapped classification
  snapshots — so non-reproduction here does not refute OPEN-49's mechanism. The plan anticipated
  this exact outcome and instructed that it be reported rather than patched, so it is **not** a STOP.
  What it does mean is that the fix moves inputs for **essentially every Unknown building in every
  cell**, which is a far broader impact statement than "four moving cells" — that is the sentence
  T08 must carry into the register, and it is the honest discharge of CP-M3 (OPEN-31).
  The executor also flagged this file and the two board copies as unexpectedly modified; that was
  **the director**, not a stray process. Noted here so the next reader does not re-investigate it.
- **2026-08-17 — T05–T08 dispatched.** New Sonnet session (never the CP-1 one — the rule is a fresh
  session per dispatch), background, T05 → T08 stopping at **CP-2**, carrying five corrections the
  plan text predates: CP-1 is signed so T01–T04 must not be re-run or re-verified; the dirty tree is
  intentional and partly the director's, so rule 1's git prohibition still binds absolutely; the
  suite baseline to measure against is **1868/55/0**, not an older number; `.venv/Scripts/python.exe`,
  no cluster, no `159.2157`; and T08's §5.15 journal block must be a single surgical insertion
  re-read immediately before writing, because the director is editing §5.17 of the same file.
  CP-1's sign-off lives here rather than in the plan's §8 for that same reason — **§8 is the
  executor's surface and the director does not write into it while an executor holds the file.**

- **2026-08-17 — T05–T08 returned; CP-2 partially audited, one defect sent back.** The executor
  delivered all four tasks and then stopped while its full-suite run was still going, so CP-2 is not
  yet signable. What the director verified from raw artifacts in the meantime:

  | What CP-2 owed | Verified how | Verdict |
  |---|---|---|
  | T05's `1.33331` reproduction | `resolve_simulated_floor_area()` on the real harvested `la_urban/way_401904735` `layout_assign` run → 7,401.68 m², `error_factor = 7401.68 / 5551.362294 = 1.3333087642` — matches the director's independent re-derivation **and** `open01_denominator_audit.csv`'s own `1.333309`; `building` mode 1,850.45 → `0.3333326` matches `0.333333`. **No STOP: the lifted parser and the audit's parser agree.** | ✅ |
  | T06's three fallback cases | `tests/test_results_denominator.py`, 7 tests; non-vacuity proved by `sed`-mutating all 8 provenance assertions → **all 7 fail genuinely**, then restored and re-passed | ✅ |
  | T07's five-mode deciles | `open01_denominator_swap.csv` **40,800 rows**; summary CSV re-read by the director: `auto` 0.99999999/99.632%, `floor` 1.00000015/98.431%, `fast_zone` 0.99999951/94.804%, `layout_assign` 0.99986627/**15.368%**, `building` 0.50000269/**39.939%** — **every one of the five plan targets reproduced exactly**, join 8,160 matched / 0 unmatched in every mode. Deciles present per mode, not median alone. `.md` opens with the reassurance block as instructed | ✅ |
  | Fleet figure untouched | `.md`'s first section states `auto` is adopted and `157.1 kWh/m²` pooled does not move; no re-run, no restated headline | ✅ |
  | Full suite alone | **still running at the time of writing** — the executor stopped to wait for it, which is the known executor-blocks-on-disk failure mode, not a crash | ⏳ |

  **Two deviations, both disclosed by the executor rather than hidden, both accepted.** (1) T05 kept
  `_compute_eui()`'s old signature and added an **optional** `floor_area` keyword, so the ~20
  pre-existing direct callers in three test files keep the exact pre-OPEN-01 arithmetic; the plan's
  "exactly three files" rule is what forced this, and the alternative was editing three test files
  outside the layout. It did have to add two keys to `tests/test_results_aggregator.py`'s fixture —
  a fourth file — because `test_step5_cols_appended` asserts the joined columns exactly; the values
  chosen reproduce the pre-existing hand-computed expectation bit-for-bit. (2) T08's journal block
  went to **§5.16**, not the §5.15 the plan names, because §5.15 is an unrelated finished sweep and
  §5.16 is the section titled for this very plan. Both readings are right.
  **One method limit worth carrying forward:** T07's EUI shift for the four non-adopted modes is an
  algebraic transform (`new = old / error_factor`) of the single real `auto`-mode EUI, because no
  per-mode Step-5 results were ever harvested. The `.md` says so twice. It is sound — energy is
  invariant, only the divisor changes — but it is **not** four independent re-parses, and nobody
  should later cite it as such.

- **2026-08-17 — CP-2 DEFECT: the register's retired-ID count was wrong, and it was sent back.**
  T08's new §1 header claims "**Fifteen IDs retired in all**". The director re-counted the table
  programmatically and independently — **54 table lines = 52 data rows + header + separator, 24
  struck, 28 live** — which confirms the executor's *table* count exactly. The prose is what broke:
  the executor took its running total from the **trailing parenthetical**, which is stale at
  "fourteen" (2026-08-13, OPEN-22) and was never updated by the two passes after it. The live
  lineage is 10 → +3 = 13 → +1 = 14 → **+5 = 19** (OPEN-26/36/44/45/50) → **+2 = 21**
  (OPEN-24/32) → **+1 = 22** with OPEN-01. The correct figure is **twenty-two**.
  Sent back with the arithmetic, plus the reconciliation sentence that stops this recurring:
  **24 struck rows but 22 retired IDs, and the difference of exactly 2 is OPEN-02 and OPEN-28** —
  struck because they sit under OPEN-01's umbrella, never separate tracked IDs, so never retired.
  This is the **third** consecutive pass in which the register's table was right and its prose header
  was wrong; the plan's own T08 "How to test" predicted it. **The standing lesson for every future
  register edit: recount the table programmatically AND re-derive the retired-ID total from the
  struck-header lineage, never from the trailing parenthetical.**

- **2026-08-17 — the register correction landed and was re-verified by the director, not taken on
  report.** `twenty-two IDs retired in all` now appears in both places; the stale `fifteen` is
  struck rather than deleted, keeping the register's append-only convention; the reconciliation
  sentence is in (`24 struck rows, 22 retired IDs, the difference is OPEN-02 and OPEN-28, folded
  under OPEN-01's umbrella and never independently tracked — that is the reconciliation, not a
  miscount`). Re-counted the table again after the edit: **54 lines, 24 struck, 28 live** — the
  table itself never moved, which is the point. The executor is still holding for its full-suite run
  (26% at 22:31, log live, ~29 min expected), so **CP-2 remains unsigned** and T05–T08's code is
  audited-but-not-cleared until those counts land.

- **2026-08-17 — 🟩🟩🟩 CP-2 SIGNED. `PLAN_open-49-and-open-01-2026-08-13.md` IS FULLY EXECUTED,
  T01 THROUGH T08.** The full suite finished and the director read the log directly rather than
  taking the count on report: **1875 passed, 55 skipped, 0 failed, 11 warnings, 1650.61s**.
  🟦 **Scope clarified 2026-08-18: that run was `tests/`-scoped, not a bare root-level `pytest -q`.**
  A bare run on this tree collects ~96 extra tests and cannot be `0 failed` — the files responsible
  predate this run by weeks. Read every suite figure in this document as `pytest -q tests/`. The
  arithmetic closes exactly — the pre-plan baseline was **1868 passed / 55 skipped / 0 failed**, and
  `pytest --collect-only` on `tests/test_results_denominator.py` returns **7 tests**, so
  1868 + 7 = 1875 with **skips unchanged and no pre-existing test moved in either direction**. That
  is the strongest form of this evidence available without a re-run: every new pass is accounted for
  by name. Plan §8 carries all eight progress entries. The executor was released with an explicit
  instruction to write nothing further.

- **2026-08-17 — the one loose thread in the CP-2 report, checked rather than accepted.** The
  executor noted `Windows fatal exception: access violation` lines mid-run and called them
  pre-existing joblib/loky noise from `test_sim_integration.py::test_synthetic_fleet_full_annual`.
  Verified: **exactly 7 such lines in all three full-suite logs**, including both pre-plan runs that
  ended `1868 passed, 55 skipped` — same count, same source, unchanged by this plan. The claim
  holds, and the number is recorded here so the next reader does not re-open it.

**What this plan actually delivered, for the next session that has to cite it.**

| Item | State after this run |
|---|---|
| **OPEN-01** | ✅ **CLOSED 2026-08-17, ID retired.** Ruling 6's remedy landed in `openubem/results/parser.py` + `aggregator.py`; regression-tested by 7 non-vacuous tests; measured before/after on 40,800 rows across all five modes, every plan target reproduced exactly. |
| **OPEN-49** | ⚠️ **MECHANISM FIXED, CLOSURE BLOCKED.** The coupled draw is dead on both routes and across all eight fields. It cannot close until OPEN-48's third fleet run reproduces `157.1` end to end, and **ruling 4 declined that run** — the block is a user decision, not an oversight. |
| **OPEN-02, OPEN-28** | Discharged under OPEN-01's umbrella, as the register always promised. Never separately retired. |
| Register | **28 live / 24 struck / 52 total; 22 IDs retired.** Re-counted by the director after the fix. |
| Published fleet figure | **`157.1 kWh/m²` pooled — unmoved, and unmovable by this plan.** `auto` is the adopted mode and it measures 1.0000 / 99.63%. No simulation was run anywhere in T01–T08. |

**Three findings this arc produced that were not in anyone's question, and that must not be lost.**
1. **The OPEN-49 defect was eight fields wide, not one.** Route 2 moved all four PDE columns *and*
   all four setpoints; only `wwr` was ever named. The register now records the widening.
2. **T04's expected pattern does not reproduce, and the honest reading is broader, not weaker** —
   the fix moves inputs for essentially every Unknown building in every cell, not just the four
   cells OPEN-49 flagged. See the CP-1 entry above for why the two experiments are orthogonal.
3. **T07's non-adopted-mode EUI shifts are an algebraic transform, not four independent re-parses.**
   Sound, disclosed twice in its `.md`, and must never be cited as re-measured.

**🔴 Nothing further is authorised in this arc.** No plan is open, nothing is in flight, Speed is
free, and the working tree is dirty by design — git is handled externally and no session may commit.
The next session's job is **not** to find more work: it is to put the remaining live register items
to the user for a ruling, exactly as this arc has always run. **OPEN-22's fixture rebuild is still
blocked on ruling 2a**, and **OPEN-48's fleet re-run is declined**, so neither is a candidate for
autonomous pickup.

### 5.18 🟦 The five-item pass of 2026-08-18 — task-by-task log

**Why this section exists.** On 2026-08-18 the user asked for **five more open items to be chosen,
planned, and executed to the end**. The plan is
`implemenation/PLAN_five-items-2026-08-18.md`; its own progress log is that file's §8. This section
is the director's log and is appended to as each task lands.

**Why these five, and what was rejected.** Every live register item was screened for three
properties: local (no cluster), unblocked (no user ruling owed), and answerable today. That
eliminates **OPEN-17, OPEN-27, OPEN-35, OPEN-46, OPEN-48 and OPEN-49** — all of which wait on a
decision reserved to the user — and **OPEN-13**, which is downstream of OPEN-17. What survives:

| Task | Item | Why it is answerable now |
|---|---|---|
| T01 | **OPEN-52** | The pin has exactly one author commit (`fe05509`); the collision is reproducible locally in seconds. |
| T02 | **OPEN-51** | Both readings of `E-LA-16` are documentary and both sources are on disk. |
| T03 | **OPEN-37** | The five remaining fetch sites are one string each; the E02 harvest is local and can be censused. |
| T04 | **OPEN-06** | `building_classifier.py` has only **six** commits in its whole history — the archaeology is bounded. |
| T05 | **OPEN-42** | 🔴 The harvested `eplusout.eio` carries the built zone geometry for all 30 (building, mode) runs. **Nobody has read it.** That is what makes the last open question answerable without touching the zoning code. |

**Entries.**

- **2026-08-18 — plan written and T01–T02 dispatched.** Fresh Sonnet executor, background, stopping
  at CP-1. Carried three corrections the plan text predates: the dirty tree is intentional and the
  git prohibition still binds absolutely; this executor is the only agent running, so T01's
  deliberate two-session pytest experiment is safe; and the full suite is **not** run in this
  dispatch (baseline to beat later: 1875 / 55 / 0).

- **2026-08-18 — CP-1 signed by the director. T01 and T02 landed; T03–T05 dispatched.**
  **T01 / OPEN-52 does not close, and that is the correct outcome.** The executor found no documented
  reason for the pin anywhere (commit `fe05509` and its same-day plan entry both list the `addopts`
  line with no rationale; nothing in the repo reads the literal `.pytest_tmp` path), reproduced the
  collision for real — session B died with `FileExistsError [WinError 183]` cascading from
  `OSError [WinError 145] directory not empty` inside pytest's own `rm_rf` — then hit a blocker while
  proving the remedy: this machine's default pytest temp root
  (`%LOCALAPPDATA%\Temp\pytest-of-o_iseri`, dated Apr 1, predating the session) is **access-denied at
  the OS level**. Director verified this independently: `ls` and `touch` against it both return
  Permission denied. With `addopts` deleted, `tests/test_sim_integration.py` gave `1 passed, 6 errors`,
  all `PermissionError`. So the undocumented pin has been **incidentally shielding every `tmp_path`
  test from an unrelated OS lockout**. The executor reverted `pyproject.toml` to byte-identical —
  director confirmed: the file is absent from `git status`, and the `addopts` line is still in place.
  OPEN-52 now carries two sub-questions: (a) the original collision, reproduced and real, and (b) the
  `pytest-of-o_iseri` lockout, which blocks (a)'s specified remedy. Choosing between ACL repair and a
  different remedy shape is a design call, outside a measurement task's authority — it goes to the
  user at CP-3. **Hard rule 3 (one pytest session at a time, repo-wide) therefore still binds.**
- **T02 / OPEN-51 decided: `E-LA-16` is the cooling-coil-design-UA-failed / cooling-tower-UA-autosize
  family** (`PLAN_structural-fixes_implementation.md:279`), **not**
  `CheckWarmupConvergence`/`CheckAirLoopFlowBalance`. The original run's `.err` files are gone from
  this machine, so the executor corroborated against the current E02 harvest, where the same three
  named buildings exist in `la_urban_layout_assign`. Director re-derived the greps independently:
  `way_402036176` 23 Severe / 23 cooling-coil-UA / **0** CheckWarmupConvergence / **0**
  CheckAirLoopFlowBalance; `way_402036789` 21 / 21 / 0 / 0; `way_1395739331` 16 / 16 / 0 / 0. Every
  Severe in all three is a cooling-coil-UA failure and neither competing signature appears once. The
  code comment's grouping was a documentation error and is now corrected at
  `openubem/geometry/layout_assigner.py:865` (comment lines only — director confirmed via `git diff`).
  **One correction to the executor's numbers:** it reported 26/24/19 Severes; the true counts are
  23/21/16. Its grep pattern also matched the three trailing `EnergyPlus … Error Summary` lines, which
  contain the word "Severe" but are not Severes. The conclusion is untouched — the run's own summary
  line says `23 Severe Errors`. To be fixed in the measurement doc during T06.
  **Knock-on:** OPEN-09's C06 "five inherited log entries" narrows to four (E-LA-14, E-LA-18, E-LA-19,
  E-LA-23); E-LA-16's own accuracy impact remains untested. OPEN-29 is unaffected — both its
  measurement docs already used the correct reading and had flagged this contradiction as unresolved.
- **2026-08-18 — T03–T05 dispatched.** Fresh Sonnet executor, background, stopping at CP-2. Carried
  the CP-1 findings as corrections: `--basetemp` stays (removing it breaks `tmp_path` on this box),
  hard rule 3 still binds, T01/T02 files are off-limits, no full suite in this dispatch.

- **2026-08-18 — CP-2 signed by the director. T03, T04 and T05 landed; T06 dispatched.**
  **T03 / OPEN-37 closes.** All five remaining sites now request `eplusout.eio`; director verified by
  grep that no site anywhere under `scripts/` still carries the old four-file string, and `git diff
  --stat` shows exactly 5 insertions / 5 deletions across 4 files — no collateral edits. The disk
  census was re-derived independently by the director and matches the executor to the unit: 60
  (cell,mode) directories, **40,800 building directories, 40,800 `.eio` with 0 empty, 40,800 `.err`,
  39,926 `.sql`, 39,925 `.end`.** The `.sql`/`.end` shortfall (874, concentrated in
  `austin_suburban_fast_zone`/`austin_suburban_floor` plus one `nyc_centre_fast_zone` directory) is an
  incomplete-simulation signature, not a fetch gap — those directories still carry `.eio` and `.err`.
  Worth its own register note; it is not OPEN-37's problem.
- **T04 / OPEN-06 closes, and it is the strongest result of this pass.** The archetype column **did**
  come from this repository. Commit **`67ede73` (2026-07-01 20:14)** reproduces the committed
  `05_results.gpkg` archetype for all 41 buildings — not merely the Office family but the exact
  per-building subtype. Director re-derived this from scratch against the committed gpkg files rather
  than trusting the CSV: **41 exact matches, 0 mismatches, 0 missing**, `LargeOffice` 13 /
  `MediumOffice` 21 / `SmallOffice` 7 on both sides. The finding is discriminating, not a coincidence:
  the other historical states emit different distributions (`42f0c1d` and `62e5968` give 20/19/2,
  `7635ce2` gives 6/17/18), so only `67ede73` fits.
  **Mechanism**, verified by the director against the raw diff: the only change to
  `building_classifier.py` between `67ede73` and `0df422e` is the `RULE_LODGING_TIER` rule gaining a
  `building_tag` test it previously lacked — it read `function_tag` only. All 41 buildings carry
  `hotel`/`motel` in `building_tag` with `function_tag` blank, so at `67ede73` they missed the lodging
  rule entirely and fell through to an Office rule. The T11 fleet fan-out ran 07-01 23:14 → 07-02
  22:07, after `67ede73` landed and more than twelve hours before `0df422e` did, so it necessarily ran
  under the pre-fix classifier; `0df422e` then bundled the fix with the promotion of results that had
  already been generated without it. **This resolves N07's provenance gap** — N07 checked the wrong
  commit. Six of six historical states loaded; zero `NOT_LOADABLE`, so this is a category-(a) answer,
  not (b) wearing (a)'s clothes.
  Credit where due: the executor's first harness classified only the 41-row subset instead of the full
  cell, the control failed at 31/10 instead of N04's 33/8, and it **reported that rather than tuning
  around it** — `GROUPMEDIAN_LEVELS_MED` imputation is batch-dependent. The corrected harness
  reproduced the control exactly. That is the discipline this arc asks for.
- **T05 / OPEN-42 sharpens but does not close, and the negative is honest.** 15 of the 16 fatal
  blow-up zones sit on the **topmost floor**, and the blow-up zone's geometry is byte-identical to its
  own non-fatal siblings below it. Director confirmed on the raw `.eio`: `way_472960972`'s
  `_F0_CORE`, `_F1_CORE` and `_F2_CORE` all report floor area 2,221.44 m² and volume 7,775.03 m³, and
  only `_F2` fails — with 24 Severes, all `Temperature (high) out of bounds`. So the failing zone is
  **ordinary, not degenerate**; shape-degeneracy is ruled out as the cause. Two candidate statistics
  (a uniform `Volume=10.00 m³` anomaly, and raw zone size/aspect ratio) were killed by the plan's own
  required 20-building background control — 12 of 20 background buildings show the same
  `Volume=10.00` signature in `auto` mode and all 12 succeed. Verdict recorded as **not determinable
  from `eplusout.eio`**. The executor ran the control before believing its result, which is why a
  wrong answer did not get published.
- **2026-08-18 — T06 dispatched** (register, checklist, this section, full suite), with the five
  dispositions fixed by the director: **OPEN-37, OPEN-06 and OPEN-51 close; OPEN-52 and OPEN-42 stay
  open** with sharpened next steps. Two corrections carried into it: the Severe counts in the OPEN-51
  measurement doc (26/24/19 → **23/21/16**, the executor's grep also matched three trailing
  `Error Summary` lines), and the `.sql`/`.end` shortfall, which needs its own register note.

- **2026-08-18 — CP-3 reached. T06 lands; plan complete.** Both corrections applied: the OPEN-51
  measurement doc and T02's own progress-log entry now read 23/21/16 with a one-line note on what the
  original grep miscounted (the three trailing `Error Summary` lines). The `.sql`/`.end` shortfall was
  opened as its own item, **OPEN-53**, with the census numbers (39,926/40,800 `.sql`, 39,925/40,800
  `.end`, concentrated in `austin_suburban_fast_zone`/`austin_suburban_floor` plus one
  `nyc_centre_fast_zone`) as its first evidence — explicitly out of OPEN-37's scope.
  **Register §1 table recounted programmatically** (script over the table body, quoted in the plan's
  §8 T06 entry): **26 live rows / 27 struck / 53 total, exactly OPEN-01…OPEN-53, no row missing, none
  duplicated.** Retired-ID lineage: 22 going in + three this pass (OPEN-06, OPEN-37, OPEN-51) =
  **25 retired IDs**; the struck-vs-retired reconciliation (27 struck − 25 retired = 2, still OPEN-02
  and OPEN-28 folded under OPEN-01) survives, restated for the new arithmetic. **Next free item ID:
  OPEN-54.** `docs/PROJECT_CHECKLIST.md` carries a matching dated entry. `docs/docs_DONE/`,
  `docs_main/`, `docs_stepN/`, root `main.py` and all OVERVIEW/DESIGN docs untouched; no git write
  command run.
  **Full suite, alone:** see the RESUME box at the head of this file for the raw counts against the
  1875/55/0 baseline — reported there rather than duplicated in this log.

- **2026-08-18 — CP-3 signed by the director, and the suite "contradiction" is resolved: there is no
  regression. The baseline definition was wrong, not the run.** T06 reported
  `36 failed, 1918 passed, 55 skipped, 17 errors` from a **bare** `pytest -q` at the repo root and
  — correctly — refused to smooth it over. The director resolved it without re-running the suite:
  - `pyproject.toml` has **no `testpaths` and no `norecursedirs`**, so a bare `pytest -q` at the root
    collects the whole tree, including five test files under
    `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` and
    `scripts/analysis/test_viewer_layout_assign.py`.
  - Those files have been in the tree since **`ef19141` (2026-07-21)** and **`69373f9` (2026-07-27)**
    — both well before the 2026-08-17 baseline. So a bare root-level run **could never** have produced
    `0 failed` on 2026-08-17 either. The 1875/55/0 baseline was produced by **`pytest -q tests/`**,
    not by the bare command the plan's T06 step 5 wrote down. **The plan text was wrong; fix it in the
    next plan.**
  - Collection proves it exactly: **`tests/` alone collects 1930 tests = 1875 passed + 55 skipped**,
    the baseline to the unit. Root-wide collects **2026**. The 96-test difference reconciles with no
    slack: 43 passed + 36 failed + 17 collection errors = 96, all of them outside `tests/`.
  - Therefore **inside `tests/` this run was 1875 passed / 55 skipped / 0 failed — the baseline
    reproduced exactly.** The `access violation` line count was **7**, matching the last three logs.
    This pass's only code edits were four harvest scripts (never imported by the suite) and one
    comment, so a clean suite was the expected outcome and is what happened.
  - **Two real findings fall out of this, both new and neither this plan's fault.** (a) There are
    **`.py` files under `docs/`**, which `CLAUDE.md` forbids outright — five test files, sitting in the
    read-only `docs_DONE/` archive since 2026-07-21. (b) One of them is named
    `test_results_aggregator.py`, **colliding with `tests/test_results_aggregator.py`**; with no
    `__init__.py` and pytest's default import mode that basename collision is what produces the 17
    collection errors. Both want a register item; neither is in scope today. The cheap remedy for the
    whole class is a `testpaths = ["tests"]` line in `pyproject.toml` — propose it, do not apply it
    unasked.

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
- 🔴 **Never `git stash`, `git add`, `git restore` or `git checkout --`, and say so in every executor
  brief with the reason attached.** Read-only git is fine. On 2026-08-13 an executor ran a **tree-wide
  `git stash`** to isolate a baseline; the working tree carried **two other arcs' uncommitted work**,
  which went with it, and the `stash pop` then aborted on a `.gpkg` conflict. Recovery was possible
  only because both dropped stashes were still reachable via `git fsck --unreachable` (`759c091`,
  `b7a3e56`) and every file could be diffed back against the live tree. **Nothing was lost — by luck,
  not by design.** An executor never knows what else is in the tree; the director often does not
  either.
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
  cannot, say out loud that you did not.** ✅ **Fixed 2026-08-13** — `fusion.py:191-198` now imports
  `overture_fetcher._NORMALIZED_COLUMNS`. Read the next rule with it; the fix created that problem.
- 🔴🔴 **A regression test is non-vacuous only if the thing it pins is written down INDEPENDENTLY of
  the thing it checks.** Importing the authority (rule above) made `_NORMALIZED_OVERTURE_COLUMNS ==
  set(_NORMALIZED_COLUMNS)` a **tautology by construction** — it can never fail, whatever the schema
  becomes — while its comment claimed a schema change *"must fail this test."* **Two dangerous
  properties, both general:** (1) a test written *after* the fix tends to assert the fix's own
  identity back at itself; (2) **an executor cannot audit its own non-vacuity by mutating the value
  the assert reads** — that proves the assert is *wired*, not that it has *power*. The only real
  proof is to **mutate the upstream authority and watch the test fail**, which is what settled it
  (adding a seventh column → `AssertionError … Extra items in the left set` at
  `tests/test_fusion.py:307`). **Demand this proof in every brief that asks for a regression test.**
- 🔴 **A median is a dangerous summary for a quantized or log-symmetric error.** OPEN-32's
  `error_factor` has deciles **[0.316, 0.474, 1.000, 1.999, 4.000]** — powers of two, the signature of
  multiplier/storey arithmetic. The distribution is near-symmetric in log space, so the **median is
  0.9999 while 12.7% of buildings are genuinely off by ×2** and only 15.4% sit at 1.0. Both this
  register's "median ×2.0" and the measured "0.9999" are true, of different things. **Before quoting a
  central figure for any error, print the deciles and look at the shape.**
- 🔴 **Never run two pytest sessions at once in this repo, and never dispatch parallel agents that
  might.** `pyproject.toml:54` pins a fixed `--basetemp=.pytest_tmp`, which pytest clears at session
  start — concurrent sessions delete each other's temp directories, and the damage surfaces as an
  unrelated-looking logic failure in whichever test touched scratch next. **This cost a full
  false-failure investigation on 2026-08-13 (OPEN-52), and it was the director's error, not the
  executor's.** A test failure you cannot reproduce sequentially is this until proven otherwise.
- 🔴🔴 **A test-suite baseline is a COMMAND, not a number — write the command down or the number
  lies.** Added 2026-08-18, after T06 reported `36 failed … 17 errors` and looked like a regression.
  It was not one: `pyproject.toml` sets **no `testpaths` and no `norecursedirs`**, so a bare
  `pytest -q` at the repo root collects the whole tree, ~96 tests more than `tests/` — including five
  `.py` test files parked under `docs/docs_DONE/` since `ef19141` and one under `scripts/analysis/`
  since `69373f9`. **The 1875 / 55 / 0 baseline is `pytest -q tests/` and always was.** The resolution
  needed no re-run, which is the transferable part: **`--collect-only` settles a scope dispute in
  seconds where a re-run costs 25 minutes.** `tests/` collects **1930 = 1875 + 55**; root-wide collects
  **2026**; the 96-test gap is exactly **43 passed + 36 failed + 17 errors**, all outside `tests/`.
  ⚠️ **Two live defects fell out of it and are ruling `3b`:** `.py` files under `docs/` (forbidden by
  `CLAUDE.md`) and a **basename collision** — `test_results_aggregator.py` exists twice, and with no
  `__init__.py` that collision *is* the 17 errors.
- 🔴 **A gate believed "parked" may simply never have been run.** OPEN-24's LIVE_SMOKE gate was
  carried for eight weeks as *"the most consequential of the four parked gates."* It was green:
  EnergyPlus 23.1.0-87ed9199d4 installed, no network needed, `7 passed` in ~66s, four times running.
  **Before planning work around a blocked gate, spend the 60 seconds to run it.**

## 8. Working with executors

- **Fresh Sonnet session per unit of work.** Never resume an old agent for new work. The plan doc is the
  single source of state. *Exception:* an agent still mid-task on a not-yet-reported unit.
- **Never run cluster, harvest or inventory work in the manager session.** Delegate it.
- 🔴 **Write `.venv/Scripts/python.exe -m pytest -q tests/` into every brief — never the bare
  command.** A plan that says bare `pytest -q` makes a careful executor report a false regression and a
  careless one bury a real change inside 36 pre-existing failures. `PLAN_five-items-2026-08-18.md`
  T06 step 5 got this wrong; the executor reported the discrepancy rather than smoothing it, **which is
  the behaviour to keep** — the plan was at fault, not the run.
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
  🔴 **The fleet figure is `157.1 kWh/m²` — pooled, total simulated energy ÷ total simulated floor
  area over all 8,154 successful buildings. RULED AND ADOPTED 2026-08-12 (OPEN-43). Quote it with that
  definition. ~~158.0298~~, the count-weighted mean of cell means, is superseded and must never be
  restated as the current fleet EUI.** 🔴 **The caveat that belongs beside it, corrected 2026-08-12 night (OPEN-46 → OPEN-48).
  Elevator energy IS in the adopted run and IS inside the published 157.1** — the adopted
  `05_results.csv` carry an `elevators_eui_kwh_m2` column with **3,561 of 8,160 rows non-zero,
  Σ 12,508.8 kWh/m²**, and against the pre-elevator run the median of `|Δtotal − elevators|` is
  **exactly 0**. **Never repeat the older phrasing that elevator energy is "folded into
  `equipment_eui_kwh_m2`" — it is de-folded OUT of equipment into its own column, and that inversion
  is what made two separate checks read absence where there was none.** 🔴 **What IS broken:
  the adopted run cannot be reproduced from this repository (OPEN-48).** The reporting path was
  restored on 2026-08-12 night and proved bit-identical on meter-absent inputs; **the load wiring was
  not** — live `builder.py` still never calls `assign_elevators`, so anything simulated from HEAD
  today reports `0.0`.**
- **`layout_assign` is adopted for zone/HVAC-topology studies and NOT certified for fleet-level EUI
  reporting.** OPEN-01/03/32/38 are all `layout_assign`-scoped. **The adopted fleet figure is measured
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

🟥 **UPDATED 2026-08-18 — YOUR FIRST ACTIONS, IN THIS ORDER. Supersedes the struck text below.**
1. **Read the register in full.** It is the state of this arc; this prompt is not.
2. **Confirm the E02 harvested corpus is still on disk** — it lives in `%LOCALAPPDATA%\Temp\ubem_e02_harvest`,
   a temp directory nobody is protecting. **Count it, never assume it.** Expect 40,800 run directories
   across 60 `(cell, mode)` pairs.
3. **Put ruling `3b` to the user** (the stray `.py` under `docs/` and the `testpaths = ["tests"]` line)
   — it is the cheap one, and it is bundled with the long-unasked row `2c`, which is the same
   population. **Ask them as one question, not two.**
4. **Then ruling `3a`** (OPEN-52's remedy shape).
5. **One ruling at a time, never as a menu.** Lead with the reassurance where there is one — neither
   `3a` nor `3b` touches a published number, and saying so first is what keeps these questions short.

⚠️ **If the user wants work moving before ruling on either, the answer is OPEN-01's denominator swap:**
already ruled, measurement already on disk (`e02_simulated_floor_area.csv`, 40,800 rows, 0 parse
failures), **plan doc never written.** It is the largest piece of unstarted work this arc owns, and it
needs no new ruling to begin.

~~**Your first action:** read the register in full, then confirm the harvested corpus is **still on disk**
(it lives in a temp directory nobody is protecting — count it, do not assume it). Then put **one** ruling
to the user:~~ ~~OPEN-22~~ ~~**OPEN-43 — which aggregation the published fleet headline should use.**~~
**✅ OPEN-43 was ruled on 2026-08-12 — pooled, `157.1 kWh/m²`. Do not re-ask it.**
~~🟩 **UPDATED 2026-08-13 — the first ruling to put is now `2f`: register the `wwr` re-randomisation
defect as OPEN-49.**~~ ✅ **PUT AND ANSWERED 2026-08-13 — the user ruled "register it" and OPEN-49 is
written. Next free item ID is now `OPEN-50`.**
~~🟩 **The only ruling now owed is `2g`**~~ ✅ **`2g` WAS PUT AND ANSWERED 2026-08-13: KEEP `157.1`.**
🟩 **Nothing is owed to the user and the autonomy grant was reaffirmed the same turn** (*"continuer
jusqu'à la fin comme tu recommends finir"*). **The next rulings in the queue — `2a` (the accuracy
gate's threshold, which blocks OPEN-22's rebuild and OPEN-47's fix), `2c` (the 30 stray `.py` files
under `docs/`), then rulings 5–8 — are put ONE AT A TIME as the work reaches them, never as a menu.
🔴 `159.2157` is not the fleet figure and must never be restated as one.**

~~If you want work running while that ruling is pending there are now **two** ready measurements, both
fully local. The larger is **OPEN-44's triage — which of the 44 `tests/` failures are real defects in
shipped code and which are merely asserting that an output file exists.** The smaller is **OPEN-42's
remaining unknown — why the six `Warehouse` simulations failed.** Their `error_summary` is the empty string in
the manifest, so the causes have to be read from the `.err` files, which are on disk. Fully local, no
cluster, no ruling required.~~

✅ **BOTH RAN AND BOTH PASSED AUDIT — `PLAN_two-measurements-2026-08-13.md`, CP-1 signed 2026-08-13.
Do not re-commission either.** OPEN-42's cause is runaway zone temperatures and the defect is
zoning-dependent; OPEN-44's `tests/` triage is complete with **zero real defects in shipped code**. See
the CP-1 box near the head of this document for both results and for **OPEN-50**, which the checkpoint
itself opened.

🟩 **What is ready to run next, needing no ruling and no cluster** (in the order the director would
pick them):

1. **OPEN-42's last question — why does whole-building zoning survive where the sub-building modes blow
   up?** This is the only thing keeping OPEN-42 open. It cannot be answered from `.err` files; it needs
   the geometry/zoning code, so it is a **read-and-explain task on shipped code**, not a measurement.
2. **Write the five missing register rows** (`OPEN-45` … `OPEN-49`) so the §1 table is a valid item
   census again. Pure hygiene, no decisions, and the sections already hold the content.
3. **Restore the register's evidence trail for the 106-node triage** — record that those numbers now
   resolve against commit `6aeebb0`, since the working-tree CSV was overwritten with the 45-node
   `tests/`-scope version.

⚠️ **Not ready, and do not start:** any fix to OPEN-17's draw tier, OPEN-36's debias wiring, OPEN-45's
`SEVERE_RE`, ~~OPEN-49's `wwr` draw,~~ or OPEN-50's fixture. ~~**All five are registered, none is
authorised**~~ **Four of the five are registered and unauthorised**, and three of them would change
published numbers. 🟩 **CORRECTED 2026-08-13: OPEN-49 IS NOW AUTHORISED** — the user ruled on it four
ways and `implemenation/PLAN_open-49-and-open-01-2026-08-13.md` was written and dispatched. **It is
also the arc's only work in progress, and it stopped partway with shipped code edited and unverified.**
See §5.16 and the RESUME box at the head of this file. **OPEN-01 (T05–T08 of the same plan) is
authorised too and has not been started.** *(OPEN-42's placeholder question was the previous answer here; it ran on
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
