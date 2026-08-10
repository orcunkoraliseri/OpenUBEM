# DIRECTOR PROMPT — the `openings` arc

> # 🟢 RESUME HERE — written 2026-08-09 20:4x, at the user's instruction. Read this box first; everything below is context.
>
> **The user is away and returns when the cluster finishes.** *"des qu'ils finiront sur le speed, je vais
> retourner. pas nécessaire d'attendre."* **Do not wait, do not poll in a model session, and do not
> re-dispatch a monitoring agent** — one already burned ~157 k tokens idling and was stopped for it.
>
> ## Where things actually stand
>
> **The probe is running on Speed and nothing is owed until it drains.** Ten arrays, **1,735
> simulations**, submitted **2026-08-09 20:29:21**. `la_rural` 149/mode and `nyc_rural` 198/mode, across
> `auto` / `building` / `floor` / `layout_assign` / `fast_zone`. Job IDs and counts:
> `%TEMP%\ubem_r05_probe\r05_job_ids.json`. A **plain background shell poller** (no model tokens) reads
> `squeue` every 30 min, read-only, and exits on one of three outcomes — all drained (it then prints the
> `sacct` timing/`MaxRSS` table, which **is** the measurement), three consecutive ssh failures, or a 12 h
> timeout. **Silence is not success and the watcher is built so it cannot be read that way.**
>
> **Everything gating the fleet pass is done and signed.** CP-R1 signed 2026-08-09 on independent
> re-derivation: R01 `.eio` retention, R02 + R06 the fatal-detection regex at all six live sites, R04
> the resume trap (markers cleared **and** the guard now surviving the run via R08), R07 the vintage
> token carried through the manifest. Full audit tables in `implemenation/PLAN_speed-resume.md` §8.
>
> ## What to do when the watcher reports
>
> 1. **Read the timing and memory table** — that is R05's whole purpose. A clean submission measured
>    nothing; **runtime and `MaxRSS` are still unknown** until this is read.
> 2. **Resolve the two pre-registered risks explicitly, whichever way they fall:** the **2-hour wall**
>    against `fast_zone`'s worst buildings, and **`--mem=6G`** (the ceiling that killed the local run).
>    Report both even if both are clean.
> 3. 🔴 **Apply the `r05probe` tag override when harvesting.** `t08_harvest_results.py:42` still
>    hard-codes `_FLEET_TAG = "t08"`; a blind harvest reads the wrong remote directories and **finds
>    nothing** — and per the plan's §2 rule 9, an empty result is reported as empty, **never as 0
>    failures**. State in the report which remote directories were actually read.
> 4. **Then CP-R2 and the fleet pass.** The user's 2026-08-09 autonomy grant lets the director self-sign
>    and submit — **except** if the probe shows `fast_zone` fits neither the wall nor the 32-CPU
>    allowance, in which case **return to the user**; cutting scope is theirs, and the 2026-08-06
>    descope options (a)–(d) are **spent, never re-ask them**.
> 5. Re-check the allowance immediately before the fleet submission, as was done for the probe.
>
> ## Standing instructions the user restated this session
>
> - **Update this prompt on every completed task, unasked** — plus the plan's progress log and the
>   register. Three surfaces, every time. *("chaque fois mettre à jour ce prompt … très prochainement.")*
> - **Kill agents that are not doing work.** Background shell watchers are fine; idling model sessions
>   are not.
> - **Answer in English**, short. The user writes French. *("en anglais toujours tu réponds en anglais.")*
> - **OPEN-02 and OPEN-28 are folded into OPEN-01** (user's instruction) — 30 tracked items, 32 findings.
>   OPEN-01 is the one the cluster closes; the other 29 are unrelated to it.
> - Progress board: `implemenation/board_published-numbers.html`, mirrored to `reporting/`, published at
>   `https://claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639` — **redeploy to that same URL**.

> # ▶️ SUPERSEDING BOX — 2026-08-09. The arc is UN-PAUSED. Read this before the pause box below.
>
> **The user returned 2026-08-09 and released compute again:** *"maintenant des ressources de speed est
> disponible, nous pouvons utiliser avec des taches qui utilisent des ressources pour le computation."*
> The pause box below is **historically accurate and no longer current**. What changed, and only this:
>
> 1. **Speed is reported available**, so CPU-bound work is authorised. **This is the event E02's park
>    was waiting for.** Verification of the allowance was dispatched read-only before anything is
>    submitted — *reported available* is not *verified free*, and this account has been wrong about that
>    before (2026-08-05: the cap was 100% consumed by an unrelated account).
> 2. **Ruling 1 of the list below is ANSWERED — do not ask it again.** CP-M3 + OPEN-30 + OPEN-33 were
>    put as one question and the user ruled **all three obligatory**: the labelled-fixture before/after
>    gate, persisting the assigned vintage in every harvest, and a citation sweep on archiving an arc.
>    Full text in each register item and in `PLAN_published-numbers.md` §8, "RULING — CP-M3".
>    🔴 **OPEN-30's consequence is a scheduling constraint, not just a policy:** the vintage column must
>    exist **before** the next fleet pass is submitted, or that pass reproduces the gap it would close.
> 3. **CP-C2's scheduling axis is RULED: measure first.** The allowance was verified free the same day
>    (`chachemv`, `cpu=32`, **0 in use**; 4.1 TB quota headroom). Given probe-first / all-five-now /
>    four-now-with-`fast_zone`-after, the user chose **a bounded calibration probe**, then the scope
>    decision against measured numbers. **Execution: `implemenation/PLAN_speed-resume.md`** — R01 the
>    `.eio` deletion, R02 the cluster harvest's broken fatal test, R03 the vintage column, R04 FINDING
>    1's markers plus a guard, **then** R05's probe (`la_rural` + `nyc_rural`, whole cells, five modes,
>    ten arrays). **CP-R1 gates every submission; CP-R2 returns the numbers to the user.**
>    *(Superseded in part by item 6: R03 → R07, R04(b) → R08. CP-R1 now covers R01, R02, R04, R07, R08.)*
>    *(Task IDs were renamed S0n → R0n on 2026-08-09: the progress board already used S01/S02/S04 for
>    the arc's standing obligations, and two live documents numbering different work identically is the
>    records defect this arc keeps uncovering. Scope and order unchanged.)*
>    ~~🔴 **The fleet submission is NOT authorised** — CP-C2's scope question is still owed~~
>    **→ SUPERSEDED the same day; see item 4.** The (a)–(d) descope options stay spent.
> 4. 🔴 **The user granted autonomous completion, and with it the fleet submission — 2026-08-09.**
>    *"vas-y continuer jusqu'à la fin. et aussi commencer des runs sur le speed, des ressources sont
>    disponibles, vas-y."* The director **self-signs CP-R1 and CP-R2** and proceeds into the fleet pass
>    without returning for permission. **Three things this does NOT license.** (a) **RULING B still
>    stands** — R05's probe runs **first**; "start the runs" is not "skip the measurement", and the
>    10× miss that made the probe necessary came from extrapolating instead of measuring. (b) The audit
>    standard is untouched: CP-R1 is signed on **independent re-derivation from raw artifacts**, and a
>    checkpoint that cannot be re-derived is a **STOP**, not a formality waived for momentum. (c) **Go
>    back to the user before submitting** if the probe shows `fast_zone` cannot fit the 2-hour wall or
>    the 32-CPU allowance — reducing scope is the user's call and (a)–(d) are spent, so that situation
>    is a question, not a decision to take alone.
> 5. **RULING C — OPEN-29: "fix the error check everywhere."** Ruling 5 of the list below is spent.
>    Task **R06**; six live sites, not the four this register recorded (`t17`/`t18` were never named,
>    and every cited line number had drifted). **The fix corrects the future, not the record** — no
>    harvest is re-run, so "never use the `has_fatal` column" still binds every pre-2026-08-09 artifact.
> 6. **CP-R1's first pass — 2026-08-09. ~~NOT signed~~ → superseded by item 8, which signs it after R07
>    and R08 landed. Kept because the two failures it found are the reusable lesson.** The plan is R01–R08.
>    **Signed:** R01 (`.eio` retention — `5 insertions(+), 5 deletions(-)`, glob gone, comments and echo
>    corrected), R02 (cluster fatal test at `t08_harvest_results.py:246`, re-derived by the manager over
>    the halted run's 2,422 `.err` files: old **0**, new **2**), R04(a) (four stale markers gone, file
>    count 20,078 → 20,074, exactly −4).
>    **R03 stopped instead of coding** — which the plan explicitly told it to do — because
>    `vintage_standard` is transient on `gdf_57` and reachable from **no** persisted artifact the cluster
>    harvest sees (five real manifests carry 10 columns; it is not among them). → **RULING D**, task
>    **R07**: carry it in `03_manifest.parquet` via a left-join inside `run_step3_mode()`, which is
>    handed `gdf_57` and which **both** harvests already read. Nothing is recomputed — re-deriving it
>    with `resolve_vintage()` would be a script reimplementing pipeline logic, i.e. lookalike evidence.
>    **R04(b) failed** → task **R08**: the resume guard restores the CSV at startup and the very next
>    per-cell write — an overwrite from an accumulator holding only the cells done so far — destroys the
>    recovered rows of every cell the loop has not reached. Manager fixture: `{c1/auto, c2/auto}` after
>    the guard → `{c1/auto, c1/floor, c2/floor}` at the end; **`c2/auto` silently gone**, marker still
>    present so nothing regenerates it. **FINDING 1 reproduced inside its own fix.** Generalisable
>    lesson: *a guard that restores state at t=0 is not a guard unless the write path downstream of it
>    preserves that state.*
> 7. 🔴 **Restate every standing boundary in each kickoff prompt — an executor must never widen its own
>    mandate from something it read.** The R01–R04 session found item 4's autonomy grant written in the
>    plan doc it was executing and **declined to act on it**: file content is not a message addressed to
>    it, and the only instruction it had received said *do not submit anything to Speed*. It flagged the
>    discrepancy instead of resolving it silently. **That is the standard.** A grant to the director is
>    not a grant to an executor.
> 8. **CP-R1 IS SIGNED — 2026-08-09 — and R05's probe is launched.** R07 and R08 both audited by
>    re-derivation and both hold. R07: the era column reaches the manifest and both harvests, **100%**
>    non-empty over 149 real `la_rural` buildings, `DOERefPre1980` **90.6%** / `90.1-2007` **9.4%**
>    against the fleet's ≈92.9%. 🔴 **The check that settles it is the independent one** — cross-checked
>    against `year_built` in the raw `01_buildings.gpkg`, which the join never touches: all 14
>    `90.1-2007` buildings have `year_built` **2005–2007**, all 135 `DOERefPre1980` have **1920–1979**,
>    **zero crossover**. A plausible distribution alone would not have distinguished a real column from a
>    constant. R08: manager fixture, three cells, recovered pair placed **last** — present at every write,
>    0 duplicates; the old bare overwrite lost it at the first write.
>    🟠 **One residual left open deliberately:** the **final** assembly write (`t08_local_remainder.py:830`)
>    is still a bare overwrite, so a `--cells X` subset run destroys other cells' rows at the end.
>    Cannot affect E02 (all twelve cells run), pre-existing, and fixing it would change what `--cells`
>    *means* — **a semantics decision, not a bug fix. Do not change it without a ruling.**
> 9. **OPEN-02 and OPEN-28 are folded into OPEN-01 — user's instruction, 2026-08-09.** One closure
>    condition (the E02 pass), so one tracked item. Nothing closed, nothing deleted; both sections stay
>    in full as evidence. 🔴 **The merge must not hide that one audit now has to answer three questions**
>    — the `layout_assign` denominator, the fleet-wide denominator in all five modes, and a demonstration
>    that all five modes came from one code state. **Any one unanswered leaves OPEN-01 open.**
> 10. 🟢 **R05's probe is SUBMITTED — 2026-08-09 20:29:21, ten arrays, 1,735 simulations.** Job IDs
>    `1174659/1174676/1174704/1174735/1174791` (`la_rural`, 149/mode) and
>    `1174813/1174837/1174865/1174924/1174959` (`nyc_rural`, 198/mode); IDs in
>    `%TEMP%\ubem_r05_probe\r05_job_ids.json`. Manager re-derived from the ten manifests on disk:
>    **1,735 rows, 1,735 success, 1,735 `.idf` files**, non-success bucket **empty in every mode**
>    including `fast_zone` and `layout_assign`, whole cells in all five modes, and `vintage_standard`
>    present in **all ten** — R07 is live in a real run, not just its test.
>    🔴 **A clean submission measures nothing.** R05 exists to measure **runtime and memory**; both
>    pre-registered risks (the 2-hour wall vs `fast_zone`, and `--mem=6G`) are **still unmeasured**.
>    **State no fleet-cost figure until the arrays drain and the `.err`/`.eio` artifacts are read.**
>    🔴 **The readout must apply the `r05probe` tag override** — `t08_harvest_results.py:42` still
>    hard-codes `_FLEET_TAG = "t08"`, so a blind harvest reads the wrong directories and finds nothing;
>    per §2 rule 9 an empty result must be reported as empty, never as 0 failures.
> 11. **Still owed:** OPEN-22, CP-M2, OPEN-11.
> 9. **Machine state re-verified 2026-08-09** — idle, newest E02 log write still 2026-08-06 05:47:01.
>    ~~FINDING 1's marker trap is still armed and un-cleaned (four surviving `sim_done.txt`).~~
>    **→ cleared by R04(a) the same day; zero markers remain.** Still no output CSV on disk.
>
> **Everything else below stands**, including the four conditions on resuming and — first among them —
> the `.eio`-deleting cluster template.

> # 🅿️ HISTORICAL — the pause box, written 2026-08-06. Superseded by the box above.
>
> **The user paused this arc on 2026-08-06** to work on other projects, and will return when they have
> time. *"dès que j'ai temps frais, je vais retourner."* **Nothing is cancelled. Nothing is in flight.**
> No local run, no cluster job, no executor session — the machine is idle and any instruction anywhere
> in this document to "check on E02" or "do not disturb the overnight run" is **stale**.
>
> **This document is long because it is a full history. If you are resuming, you do not need all of it.**
> Read, in this order: **this box → §0 → §4sexies.4 (why E02 stopped and the four conditions on
> resuming) → the register's closing amendment**, which is the compressed resume brief. Everything else
> is background you can consult as questions arise.
>
> **Do not open by proposing work.** Report the state, then ask for a **ruling** — the open ones are
> listed in §0. Every remaining first measurement in the register needs either CPU that is not
> currently available or a decision from the user; there is no third category, and inventing a task to
> look busy is explicitly out of bounds (§4quinquies).

## §0 — The state of the arc at the pause, in one screen

| | |
|---|---|
| **Machine** | idle — nothing running, nothing queued |
| **E02** (the 40,800-simulation five-mode fleet pass) | **halted and parked**, to resume **on the Speed cluster when its resources free up**. Halted by a real `MemoryError`, `fast_zone`-specific. **Not descoped** — the user declined all four reduced-scope options and parked on a different axis. |
| **No-compute queue** | **empty** — 16 tasks over 4 rounds, all landed, all audited |
| **Last work done** | **C06** (OPEN-09's "cosmetic" label tested for the first time — it holds), **C07** (the fatal-detection fix in the E02 runner), and the ≈10× correction to the cost-scoping document |
| **Register** | **30 tracked items** (32 findings — OPEN-02 and OPEN-28 folded into OPEN-01 on 2026-08-09, nothing closed, nothing deleted), `INVESTIGATION_open-items-register.md` — **its closing amendment is the resume brief** |

**Rulings owed by the user — ask one at a time, never as a menu:**

1. ~~**CP-M3 + OPEN-33 + OPEN-30 together** — what a change must carry before it counts as finished.
   Three instances of one question. *Ask this first: it changes how future work is done, not just what
   is known.*~~ **✅ RULED 2026-08-09 — all three obligatory. Spent; do not re-ask.**
2. ~~**CP-C2** — which slice of E02 to relaunch when Speed frees up.~~ **✅ RULED 2026-08-09 in two
   parts — measure first (RULING B), then run it to the end (the autonomy grant, box item 4). Spent.**
   🔴 **Do not re-ask the four descope options (a)–(d); that question was already spent.**
3. **OPEN-22's ruling** — a third of the 50-row exam is decided by size-bucketing rather than tag
   logic. Is that the exam the project wants? (The fallback rows are *not* inflating the metric — that
   is measured.)
4. **CP-M2** — what to do about the published cross-mode numbers, confirmed confounded.
5. ~~**OPEN-29** — fix E-LA-21 in the four remaining harvest scripts, or leave them?~~
   **✅ RULED 2026-08-09 — RULING C, fix everywhere. Task R06. Spent; do not re-ask.** (It was six
   sites, not four.)
6. **OPEN-11** — the six inverted-geometry buildings; precondition met, remediation is the user's call.

🔴 **The single highest-risk fact to carry into a Speed resume**, repeated here because it is buried in
§4sexies.4: **the stock cluster template deletes `.eio`** (`scripts/cluster/submit_fleet_t08.sbatch:63`,
`rm -f "$OUTDIR"/*.eio`, byte-identical across T08→T20) and **E01's retention fix is local-only** — it
lives in `t08_local_remainder.py`. A cluster E02 on the unmodified template **destroys the exact
evidence OPEN-02 exists to obtain.**

---

> **Written:** 2026-08-05, at the close of the session that measured all four "published numbers"
> items (OPEN-01, 02, 03, 04) plus OPEN-28, and opened OPEN-30, OPEN-31, OPEN-32.
> **Updated:** 2026-08-06, after a no-compute evening that (a) closed OPEN-32's first measurement —
> **no adopted result depends on `layout_assign`** — and (b) opened and largely fixed **OPEN-33**.
> See §4.8 and §4.9. **§9's instruction about the 158.0 figure changed direction; read it, do not
> skim it.**
> **Updated again 2026-08-06 (evening).** The session direction **changed**, on user instruction:
> **the overnight re-run is parked** and work moved to items that cost no compute. `building` mode was
> verified sound before the park (§4.10), the OPEN-22 measurement is **made** (§4.11), and two new
> things opened: **OPEN-34** (§4.10) and a missing mode in the local runner (§4.12).
> **§3's owed-decisions table and §10's ordering both changed direction; read them, do not skim.**
> **Supersedes:** `DIRECTOR_PROMPT_openings_2026-08-05.md` — that one is **spent**. Do not paste it.
> **How to use:** paste this whole file into a **fresh manager session**. It is self-contained and
> assumes no memory of any prior conversation.

---

## 1. Who you are and what you are doing

You are the **manager / director** for OpenUBEM. Working directory
`C:\Users\o_iseri\Desktop\OpenUBEM` — stay there. Interpreter `./.venv/Scripts/python.exe`.

The user is the **manager-of-manager**: they set scope, approve, and veto drift. **You write plans,
decide, and audit. You do not write feature code** — fresh Sonnet executor sessions do that, one per
unit of work, never resumed for new work.

**The user writes French. You reply in English. All deliverables are in English.**

**Report to the user in plain language.** Spell terms out: write "the file EnergyPlus writes recording
the floor area it actually simulated" before you write `eplusout.eio`; write "buildings where the
storey-matching mechanism did nothing" before `non-applied`. Depth goes in the documents, not the chat.

**When the user says they do not understand, that is not a request to repeat with more words — it is a
request for the context that makes the question decidable.** Give the setup, the concrete example, the
two readings and what each one costs.

### 🆕 Three standing instructions from 2026-08-05 — these are live

1. **Ask questions one at a time, step by step.** *"pose moi des question etape par etape."* Not a menu
   of four questions in one turn. One decision, answered, then the next.
2. **Keep the progress board updated on every change, without being asked.** *"toujours mettre a jour
   de document d'artifact."* See §8. The user monitors the work through it — *"je voudrais surveiller
   des progress avec ce document, sinon, je suis perdu."*
3. **Prefer local execution over the Speed cluster.** *"dans la cluster (speed), il y a des travailles,
   donc, essaie de faire simulations avec des ressources locales si possible."* Verified true: the
   account's 32-CPU cap was 100% occupied by an unrelated account. See §6.

## 2. The arc you are picking up

A register of **everything open in this project** lives at:

```
docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md
```

**Read it first, in full.** It is the single source of state for this arc — not this prompt, and not
any conversation. It holds **30 items (OPEN-01 … OPEN-33)** across six themes, each with: what is
known, what is only believed, where the evidence lives, and **the one measurement that must be made
before an execution plan can responsibly be written.**

**Three IDs are retired and must never be reused or re-added:**

| ID | Disposition |
|---|---|
| **OPEN-05** | **CLOSED** 2026-08-05 — measurement made in full. Do not re-run its sweep. |
| **OPEN-21** | **DEFERRED by the user** to `docs/docs_TODO/mixed_use_classification.md`. **Closed to further asking — never put it to the user again.** |
| **OPEN-23** | **EXCLUDED by the user** 2026-08-04 (`layoutGenerator` production zone-mode). Not a direction being continued. |

**Next free IDs: item `OPEN-34` · defect `E-LA-42` · UTCI defect `E-UTCI-17`.**

## 3. Your first move

**Ask the user which item or bundle to open. Do not self-select.** This is a standing instruction, not
politeness.

**However — unlike your predecessor, you inherit work in flight.** Deal with §4's open threads before
offering anything new. Three things are owed to the user and one is owed to the machine:

| Owed | What it is |
|---|---|
| **CP-M2 decision** | What to do about the published cross-mode numbers now that they are confirmed confounded. §4.5. |
| **CP-M3 decision** | Whether a ratified change must carry a before/after on the labelled fixture before adoption. §4.4, OPEN-31. **Ask this together with OPEN-33's — they are the same question.** §4.9. |
| **OPEN-22's question** | Asked twice, never answered, still live. §4.7. |
| **The local re-run** | ~~Approved and costed. Technically unblocked; awaiting a night and a `building`-mode decision.~~ **PARKED 2026-08-06 by user instruction** — *"essaie de faire … dès que speed ou des ressources locales vont être disponible, nous pouvons retourner des tâches des simulations."* Not cancelled; nothing is owed on it tonight. `building` mode is now **verified sound** (§4.10), so when it resumes the only open scoping question is the missing fifth mode (§4.12). |
| **OPEN-22's ruling** | The *measurement* is now made (§4.11) — **the question changed shape.** It is no longer "we cannot answer without a measurement"; it is a clean ruling on a number that exists. Put it to the user. |

## 4. What happened in the 2026-08-05 session — read before acting

The user selected **the four items that can make already-published numbers wrong** (OPEN-01, 02, 03,
04) and instructed that a plan be written and execution begun. OPEN-28 was bundled in for measurement
because it closes with the same fleet run.

**Plan doc:** `docs/docs_ACTIVE/openings/implemenation/PLAN_published-numbers.md`
*(the folder name is misspelled — the user created it that way; keep the spelling, do not "fix" it)*.
Five measurement tasks M01–M05, all complete, all independently re-derived by the director.
Reports in `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-0*.md`.

### 4.1 OPEN-01 — measured, large, unremediated

Only **877 of 6,939** non-`applied` buildings (12.6%) divide by the right floor area. Median error
factor **2.0**, range **0.118× – 10.0×**. Of 28 archetype tokens, only **two** carry a `ZoneGroup` list
multiplier: `MidriseApartment` 3 bands → **4** storeys, `HighriseApartment` 3 bands → **10**.

⚠️ **A trap that will catch you if you skip this paragraph.**
`openubem/outputs/comparisons/a1_prototype_storey_structure.csv` looks like it answers this item and
does not. Its `num_modelled_storeys` is the **band count**, and its `has_multiplier_gt_1` flag tests
`Zone.Multiplier` only — it is blind to `ZoneGroup`'s list multiplier and reads `False` for both
archetypes that actually have one. **Do not cite it.**

**Still unmeasured:** which remedy (fix denominator / fix simulation / stop publishing per-building
EUI), and **whether any adopted result depends on `layout_assign` at all** — the register requires this
be confirmed, not assumed. That confirmation is OPEN-32's first measurement and it is cheap.

### 4.2 OPEN-02 — measured, cheap, decided

`eplusout.eio` median **76,068 B**. Marginal cost of retaining it: **12.6%** per run on top of what is
already kept. A five-mode fleet pass costs **1.3 GB** typical to **~45 GB** worst case. The
">800 GB untrimmed per city" justification covers **eleven** file types together; `.eio` alone was
never the cost. The register's own prediction — *"the fear may not survive contact with the number"* —
was confirmed verbatim.

**Limitation, stated:** `fast_zone` has zero local `.eio` samples; its share is a bounded estimate.

### 4.3 OPEN-03 — measured; verdict is `undocumented but deliberate`

Zero matches for `layout_assign` / `resolution_mode` anywhere under `docs/docs_main`. The decision is
traceable to `docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:155` and `:494` but
was never written into a spec.

**The register's own claim was wrong** and is corrected: it said *"documented in results §7"*, but
results §7 is a **post-hoc write-up by the session that discovered the effect**, not a prior decision.

**Magnitude (n=12 archetypes, static, no simulation):** 2013-vs-2022 lighting ratio median **1.722**
(range 1.256–2.502); equipment **1.064**; occupancy **1.000**. The two equipment ratios of exactly
1.000 were checked against raw IDF text and are genuine. **92.9% of the fleet is `DOERefPre1980`** —
far older than 2013 — so this proxy **understates** the real error.

### 4.4 OPEN-04 — explained; the suspected cause is falsified

The 92.0/88.0 pair is **`test_fine_top1` only**, whose gate is **0.70**. `test_coarse_top1` was
**100% at every commit tested**. The apparent 88%-vs-90% contradiction dissolves.

| commit | date | fine top-1 |
|---|---|---|
| `7635ce2` | 2026-06-12 | 92.0% (R3-era reference) |
| `67ede73` | 2026-07-01 | **84.0%** — first change, E-R3-3 tier bins |
| `0df422e` | 2026-07-03 | **88.0%** — partial recovery |
| `ef19141` | 2026-07-21 | 88.0% — Phase-D work, **no change** |
| `bca92d0` | 2026-08-05 | 88.0% (HEAD) |

**The Phase-D fusion/crosswalk hypothesis is FALSIFIED** — the drift completed 18 days earlier and the
diff on every relevant file between those two commits is empty. The item is re-cast: not a broken
metric, a **review-process defect** → **OPEN-31**.

### 4.5 OPEN-28 — quantified, and its central claim corrected

Join: shared **4,530**, T08-only **0**, T20-only **3,630**, union **8,160**.
**Archetype agreement 86.60%** — 13.40% disagree, top pair `MediumOffice → SmallOffice` (n=396), root
cause reproduced from the historical blob: commit **`0df422e`** changed the shared `05_results.gpkg`
between harvests. **Floor-area agreement 100%.**

🔴 **The published −29.1% figure did not come from T20.** Per
`OpenUBEM_results_LayoutAssigner.md:422-423,449-458`, its `layout_assign` side is **T19**, its `auto`
side is **T08**. The register had this as "not established"; it is now established, and it is a
**third** generation. Any future comparison must state which harvest each side came from.

**Convergence worth trusting:** M04 and M05 ran as separate agents with no shared context and both
independently landed on `0df422e`.

### 4.6 The re-run — approved (CP-M1), costed, blocked on one prerequisite

**Decision taken 2026-08-05:** re-run all five resolution modes on one harvest, retaining `.eio`.

**Moved off the cluster** at the user's instruction; independently confirmed necessary — the account's
`GrpTRES=cpu=32` cap was fully occupied by an unrelated account (32 running / 675 pending, observed
read-only, **not touched**).

**Local cost, measured with 3 real EnergyPlus runs** (`SCOPING_five-mode-rerun-cost.md`):

| | |
|---|---|
| Machine | 20 cores / 20 logical, 63.5 GB RAM, 659.3 GB free on `C:` *(director-verified)* |
| Workers | **12 of 20** — leaves 8 for the user, who works on this box |
| Speed factor | local core **3.2×–4.6×** faster per zone than a cluster core, empirical |
| Cluster equivalent | 540 cluster-CPU-h → **117–180 local core-hours** |
| **Wall-clock** | **≈10–15 hours — an overnight run** |
| `fast_zone` worst building | ≈18–26 min, blocks one worker; no timeout to die against locally |

> ### ✅ UPDATE 2026-08-05 — the prerequisite below is BUILT, audited, and corrected. Do not re-dispatch it.
>
> **E01** wrote the trim step into `scripts/cluster/t08_local_remainder.py` (retention set = `.eio`,
> `.sql`, `.err`, `.end`, `task.rc`; delete list = cluster parity minus `*.eio`). Audited by opening
> the folders, not by reading the report: `.eio` present and non-empty in all test buildings, every
> delete-list pattern gone, deletion scoped to the per-building directory with `sim_done.txt` one level
> up untouched, second run a confirmed no-op. **Trimming accepted.**
>
> **Two defects were found at audit and corrected in a short E01b round**, both now verified:
> **F1** — the disk guard was structurally blind. `ProcessPoolExecutor.submit()` is non-blocking with
> an unbounded queue, so all N disk checks completed **before any simulation wrote a byte** (proven
> empirically: 8 checks by t=0.0126 s, first completion t=1.0722 s). It was a start-of-mode pre-flight
> check wearing a per-building label, and `last_completed_stem` was guaranteed `None` whenever it
> tripped. Fixed with a windowed submission loop (`wait(..., FIRST_COMPLETED)`); the guard was then
> **made to fire on purpose** and stopped cleanly naming a real finished building, `way_42496314`.
> **F2** — retained-bytes accounting understated disk by **25.1%** (it summed only the retention list;
> `eplusout.shd` and `sqlite.err` legitimately survive and were uncounted). Fixed to sum the directory.
> Retention of those two files is correct cluster parity and was deliberately **not** changed.
>
> **Answered while auditing:** a building the guard declines to submit gets **no directory at all**;
> anything already in flight drains and is trimmed by its own worker. **There is no third state** — no
> untrimmed partial directory is ever left behind.
>
> **Residual, recorded and judged acceptable, not reopened:** the initial window of up to `n_workers`
> now submits with no disk check. Bounded by ~12 untrimmed runs (a few GB) against a 50 GB floor — the
> floor exists to absorb exactly this.

🔴 **The prerequisite as it stood on 2026-08-05 — kept for the record.** `t08_local_remainder.py` had **no trim step at all**,
and one untrimmed city pass out of twelve exceeds this machine's entire free disk. **The clean-up must
be written and verified before the first building runs.** A pass that dies at 70% with a full disk
costs the whole night and leaves nothing usable. The needed diff is quoted as text in the scoping doc
and was deliberately **not applied** — it is pipeline code, so it goes through a written task and a
Sonnet executor.

**Also open:** `building` mode is **unverified at HEAD**. `auto`, `floor`, `fast_zone` passed cleanly
in the timing runs; `building` was not exercised. `builder.py` has moved 223 insertions since those
four modes last ran anywhere.

### 4.7 OPEN-22 — the question is still hanging

Asked on 2026-08-05, not answered, **still not answered.** Put it to the user again:

> Should we run one pass of today's classifier over the 50-row labelled fixture, reporting for each row
> the label, the emitted archetype, the rule token that fired, and the confidence tier — then the
> accuracy number **with `FALLBACK_SIZE_DEFAULT` rows excluded**? That splits earned matches from
> fallback-agreement matches. No simulation, no cluster.

⚠️ The Boston 41.0% / Chicago 65.4% fixture distributions predate `E-R3-2` and **must not be carried
into any plan** without being re-run.

### 4.8 OPEN-32 — first measurement MADE 2026-08-06 (M06). The adopted baseline is clear.

Report: `extra/MEASUREMENT_open-32_adopted-dependency.md`. Read-only — no simulation, no cluster, no
interpreter. **Answer: no adopted result depends on `layout_assign`.**

| Line | Evidence | Weight |
|---|---|---|
| **Structural** | `decide_zoning_strategy()` (`zoning.py:36-42`) can return only `single_zone` / `perimeter_core` / `one_zone_per_floor` under `auto`. **`auto` has no path to `layout_assign`.** Prototype substitution — which carries *both* OPEN-01's `ZoneGroup` multiplier and OPEN-03's 2022-code vintage — is entered only via `_layout_assign_baseline_path()` (`builder.py:67-77`), which returns `None` for every other mode at `:75-76`. | **decisive** |
| **Artifact** | `zoning_strategy` tallied over **all 8,160** adopted `phaseE_elevrb` rows and **all 8,160** `phaseE_er33` rows: **zero** `layout_assign`, and only the three values `auto` can emit. `t08_all_modes_eui.csv` = 4 modes × 4,530, none. | **exhaustive** |
| **Temporal** | String absent at `3a925f9^`, first appears 2026-07-25; adopted artifacts committed 2026-07-21 and 2026-07-02. | **corroborating only** — history is 40 commits and curated |

**This closes OPEN-01's "What is NOT known" item 3.** Only item 2 (*which remedy*) is left there, and
it is a scope decision, not a measurement.

⚠️ **The trap in reporting this.** It is a *bounding* result, not a *shrinking* one. OPEN-01 is still
a median ×2.0 denominator error on 87.4% of buildings; OPEN-03 is still ≥1.72× on lighting. Say both
sentences together or the user will hear the wrong one.

### 4.9 OPEN-33 — opened and largely fixed the same evening

**Archiving an arc breaks every document that cites it.** `docs_ACTIVE/` now holds only `openings`;
every other `docs_ACTIVE/…` path in the repo is dead. **Measured: 58 distinct dead paths, cited from
23 live documents, across 8 arcs. All 58 resolve** — four files were also *renamed* by their move
(`DONE_` / `DONE-` prefixes, re-nesting under `DONE/`), so prefix substitution alone will not find
them.

**Already done, do not redo:**

- `docs/docs_EXPLANATION/` (6 files) + `docs/docs_REPORTS/REPORT_phaseE_final.md` — **repaired in
  place**, every rewritten link opened and confirmed to land on a real file. Two pre-existing
  relative-depth bugs (`../` where `../../` was needed) fixed at the same time. **Zero dead paths
  remain in the published set.**
- `docs/PROJECT_CHECKLIST.md` — **migration map added at the head of the file**, covering all eight
  archived arcs plus the four renames. Its journal was **not** rewritten: those blocks are
  append-only, and editing paths inside frozen entries to gain navigation trades a rule for a
  convenience the table already provides.
- `docs_DONE/` records, `docs_main/` specs and `docs_TODO/layoutgenerator/` — **deliberately
  untouched** (frozen, read-only, user-excluded). They resolve through the map.

**What is still open is the recurrence, not the backlog.** Decision owed: must archiving an arc
include a citation sweep? **Put it to the user together with CP-M3** — they are the same question
(see §9 pattern 5 in the register: OPEN-30, OPEN-31 and OPEN-33 are three instances of *the closing
step nobody owns*).

## 4bis. What happened in the 2026-08-06 evening session — the direction changed

**The user parked all CPU-bound work.** Verbatim: *"au lieu de concentrer des tâches qui a besoin de
computation, complèter des tâches facile du faire ou n'a pas besoin de faire la computation du CPU
comme des simulations … dès que speed ou des ressources locales vont être disponible, nous pouvons
retourner des tâches des simulations."* And, on item selection: *"n'a pas besoin de me poser, tu peux
choisir à toi-même et tu peux choisir plusieurs des tâches de faire."*

🔴 **This changes §3's standing instruction "Ask the user which item to open. Do not self-select."**
For no-compute work the user has explicitly handed selection to the director, and asked for **several
tasks at once**. **Do not go back to asking which item to open** unless the user reopens it. Ask about
*rulings* — those are still theirs.

🔴 **And it changes the reporting duty.** Standing instruction added 2026-08-06: *"et chaque tâche
complet, mettre à jour de progress log pour [the register] et aussi ce prompt de directeur pour des
sessions prochaines."* **Every completed task updates three surfaces, unasked:** the plan's progress
log, the register, and **this prompt**. A task is not finished until all three are written.

**New plan doc:** `implemenation/PLAN_no-compute-queue.md` — tasks **N01–N05**, all first
measurements, all dispatched 2026-08-06 to fresh Sonnet executors in parallel.

**🔴 ALL FIVE LANDED AND ALL FIVE WERE AUDITED BY RE-DERIVATION. Nothing in N01–N05 is unreviewed.**

| Task | Item(s) | Result |
|---|---|---|
| **N01** | OPEN-29 — forward-trace 12 defect IDs to their *final* status | **9 of 12 genuinely still open**; now tracked inside OPEN-29. §4.13 |
| **N02** | OPEN-22 — rule-token breakdown of the 50-row fixture | the metric is **not** inflated by fallback rows. §4.11 |
| **N03** | OPEN-24/25/26/27 — re-check the June remnants at HEAD | **OPEN-25 CLOSED**; OPEN-27 is bigger than it looked. §4.13 |
| **N04** | OPEN-06/07/11 — the 41-building mislabel population | **source defect**, not a live classifier defect; OPEN-11's six confirmed. §4.13 |
| **N05** | **OPEN-34** — is a 3-building local run archetype-faithful? | **no — batch-composition dependence**, mechanism found. §4.13 |

### 4.10 `building` mode is sound — and the audit of that opened OPEN-34

**E01c, completed and director-audited 2026-08-06.** Verdict: **`building` mode is sound at HEAD.**
Three real `nyc_centre` buildings, real Stage-2 → Stage-3 → EnergyPlus path. **Audited against the raw
artifacts, not the report:** exactly 1 zone each (`Zone Multiplier` 1, `Zone List Multiplier` 1),
**zero `** Severe **` and zero `**  Fatal  **`** in `eplusout.err`, `.eio` present and non-empty
(20,433 / 20,319 / 20,295 B), simulated floor areas 5,958.96 / 2,814.53 / 1,633.00 m², and E01's trim
correct — exactly the 7 retained files, no delete-list leftovers. **Signed.**

🔴 **But the same audit found something the executor flagged and correctly did not chase.** All three
buildings came out as archetype **`SuperTallBuilding`** — including two that are **1 storey, 3.5 m**
and that the adopted fleet calls **`LargeOffice`**. Verified by the director from
`phaseE/nyc_centre/05_results.gpkg` against the run's own `03_manifest.parquet`.

**Why this matters more than three buildings.** **Every local verification this arc has run used a
3-building subset** — E01, E01b, E01c, and the timing benchmark that costed the whole overnight pass.
If a subset is not archetype-faithful, those runs exercised the pipeline on buildings the fleet never
had. Opened as **OPEN-34**; first measurement is **N05**, which separates two mechanisms:
subset-dependent Stage-2 imputation (the 178.5 m neighbour propagating) versus a genuine HEAD
divergence (which would be **OPEN-08 / E-LA-22 on a new, well-tagged population**).

### 4.11 OPEN-22 — measured, and the answer is reassuring in a way nobody predicted

**N02, director-audited by independent re-derivation from the CSV.** Report:
`extra/MEASUREMENT_open-22_fixture-rule-breakdown.md`.

| | n | fine top-1 |
|---|---|---|
| all rows | 50 | **44/50 = 88.0%** |
| **excluding `FALLBACK_SIZE_DEFAULT`** | **33** | **29/33 = 87.9%** |
| the excluded rows alone | 17 | 15/17 = 88.2% |

**Removing the fallback rows does not move the number.** The register's stated worry — a metric
inflated by the fallback and the answer key agreeing — **is not what is happening**, and that is now
measured. What *is* true: **17 of 50 rows (34%) are decided by `FALLBACK_SIZE_DEFAULT`, all at LOW
confidence, and 16 of those 17 carry an office label in the answer key.** So a third of the exam
measures the size-bucketing rule rather than the tag logic. **Whether that is the exam the project
wants is still the user's ruling** — the measurement informs it, it does not make it.

⚠️ **Do not report this as "OPEN-22 is closed."** The measurement is closed; the ruling is not.

### 4.12 A prerequisite nobody had noticed: the local runner cannot run the fifth mode

`ALL_MODES` at `scripts/cluster/t08_local_remainder.py:52` is
`["auto", "building", "floor", "fast_zone"]`. **`layout_assign` is absent**, and absent from the
`--modes` choices too. `SCOPING_five-mode-rerun-cost.md:11` scopes E02 as **five** modes. **As it
stands the local runner can only do four.** It is a small addition, but it is pipeline code, so it
needs its own written task and a fresh executor. **Not authorised, not written.** Recorded in
`PLAN_published-numbers.md` §9 above E02.

### 4.13 The rest of the queue — what N01, N03, N04 and N05 returned

Full detail is in the register; this is what a fresh session must not miss.

**N05 → OPEN-34 is answered: batch-composition dependence, not a HEAD divergence.**
`_impute_levels()` (`building_classifier.py:138-142`) fills a missing storey count from a **group
median over whatever rows are in the batch**. Over 3 buildings that median is **51** (one real
skyscraper dominates) and clears the 40-storey SuperTall threshold; over the full 738-building cell it
is **19** and does not. **The full-cell run reproduces the adopted fixture exactly**, including
20/738 `SuperTallBuilding`. **Standing consequence — put this in every future executor brief:** a
verification run on a subset of a cell must use the whole cell or state that its archetypes are not
fleet-faithful.

**🔴 And auditing that mechanism opened OPEN-35, which is the more serious of the two.** Two code
paths invent the missing storey count and **disagree**: Stage 2 picks the archetype off the group
median (19), Stage 3 builds the geometry at **1** (`footprint.py:58-63`). So such a building is
**classified as a 19-storey office and simulated as a 1-storey one**, with the EUI divided by one
storey's area. **This is true in the full-cell run too** — it is not a subset artifact, and it is the
population every published result came from. Its **size is unmeasured**: the count of fleet buildings
missing both `levels` and `height_m` is one query and is the next thing to do on it.

**N01 → the register's completeness claim was overstated, and is now repaired.** 12 candidates traced:
**3 closed elsewhere, 9 genuinely still open, 1 superseded, 0 with no status ever.** The nine are
tracked inside OPEN-29 rather than as nine new top-level items. **The method was validated first** —
made to rediscover E-LA-20's closure blind — which is why the buckets are trustworthy.
**Escalation the director found while auditing:** E-LA-21's one-space `"** Fatal **"` test is in
**four** harvest scripts (`t20_harvest_layout_assign.py:259`, `t08_harvest_results.py:239`,
`t07_harvest_results.py:198`, `t07b_run_auto_refit_local.py:329`) while `scripts/analysis/` uses the
**correct** two-space form — both versions have coexisted for months. **N04 then demonstrated it on a
named building:** `way/401910463`'s `.err` carries a real two-space Fatal that the column reads as
`False`. **Strongest candidate among the nine for promotion; deliberately not promoted without the
user.**

**N03 → two of four dissolve.** **OPEN-25 is FIXED and closed** — built `2026-06-10`, the day after
the audit named it, by the code that produced the adopted baseline. **OPEN-24** is largely superseded
(the live E+ test exists and is environment-gated, not parked). **OPEN-26** is 1 of 4 fixed.
**OPEN-27 is bigger than "a wrong name":** the DESIGN text defines the **coarse accuracy metric**
against two Residential archetypes and names `MultifamilyHome`, which **does not exist** in
`openstudio_archetypes.json` — the real pair is `MidriseApartment` / `HighriseApartment`. Code is
self-consistent, so no number is wrong; **a metric's definition names a nonexistent archetype.** The
paste-ready correction is in the register — **it is the user's to apply, at their external source.**

**N04 → the mislabel is a SOURCE defect.** The 41 reproduce exactly from scratch; the classifier is
right and `05_results.gpkg` is wrong (one row is literally *"Wilshire Serrano Motel"* recorded as an
office). **Which step writes the bad value is still unidentified — that is this item's next
measurement.** OPEN-07's three are inside the 41; their multiplier hypothesis is **silent** (no T20
IDF survives locally and fetching one needs the cluster), and their Severe is attributed to **Sizing,
not Warmup** — a plan built on the recorded wording would look in the wrong place. **OPEN-11's six are
confirmed identical**, so that item is now plannable.

⚠️ **An unresolved contradiction, recorded not adjudicated.** All three failures diverge in a zone
named `LAUNDRYROOMFLR1` — a *hotel* zone. If they were simulated as the offices the table records,
that zone would not exist. **So the archetype column may not describe what was simulated.** Any
per-archetype analysis reads that column. Not chased; not explained away.

## 4ter. Round 2 of the no-compute queue — dispatched 2026-08-06 late evening

**Instruction that opened it**, verbatim: *"continue avec des autres taches, et vas-y jusqu'a la fin
pour completer toutes des taches pas necessaire d'utiliser des ressources CPU, en continu."*
Together with the standing *"tu peux choisir à toi-même"*, this is a **mandate to drain the register of
every item whose first measurement costs no CPU, without asking which.** E02 stays parked; nothing
about it is cancelled.

**Plan doc:** `implemenation/PLAN_no-compute-queue-2.md` — opened as a *second* document rather than
extending the first, which is at 688 lines. Same structure, same 14 hard rules, §5 facts re-grepped by
the manager.

| Task | Item(s) | The question |
|---|---|---|
| **N06** | OPEN-35, OPEN-12 | how many fleet buildings reach **both** disagreeing fallbacks — the size OPEN-35 lacks; OPEN-12's 36.4%/19.2% re-derived |
| **N07** | OPEN-06 | **which step writes the wrong `archetype_id`** — the one question N04 could not answer |
| **N08** | OPEN-06/07 | does the archetype column describe **what was actually simulated**? (the `LAUNDRYROOMFLR1` contradiction) |
| **N09** | OPEN-13, OPEN-14 | the two forwarded UTCI defects **nobody has ever re-read**, and what a clean checkout lacks |
| **N10** | OPEN-15/16/17 | assemble the imputation-tier decision — **no recommendation permitted** |
| **N11** | OPEN-10 | the register's **only ❓** — is the `ZoneGroup` list multiplier a real capability? |
| **N12** | OPEN-19 | is the Title 24 hypothesis **even representable** in this pipeline? |

**Checkpoints:** CP-N3 (N06+N07+N08, the archetype-and-inputs story), CP-N4 (N09+N10, inherited
backlog), CP-N5 (N11+N12, the never-researched pair).

### 4ter.1 — What round 2 returned. Read this before touching any item.

**🔴 OPEN-06 is no longer a labelling defect (N08).** The three OPEN-07 buildings **were simulated as
`SmallHotel`** while `05_results.gpkg` records `SmallOffice`. Proved from the T20 run's own
`eplusout.sql`/`.err`; **director-verified from the raw error file** — the zones are `GUESTROOM101`,
`FRONTLOUNGEFLR1`, `MEETINGROOMFLR1`, `LAUNDRYROOMFLR1`. **The direction is the opposite of
"mislabelled": the simulation was right and the record is wrong.** No building was built from the
wrong prototype; **but every per-archetype grouping keys on a column that does not describe the run.**
Only these 3 of the 41 have surviving local artifacts — the other 38 need a cluster fetch.

**🔴 OPEN-35's size is 32.00% of the fleet (N06).** 2,611 of 8,160 have neither `levels` nor
`height_m`; **all 2,611 are persisted at `levels = 1.0`**, checked on every row. **Director's own
re-derivation added what the report did not:** 1,028 got `MidriseApartment`, 3 `HighriseApartment`,
204 Medium/Large Office — **1,031 buildings classified mid/high-rise and built as one storey.**

**🔴 OPEN-36 opened, and it is the round's most serious finding (from auditing N10).** A progress-log
entry marked *completed 2026-07-16*, naming artifacts and reporting 53 + 60 passing tests, describes
code that **no commit has ever contained** — while **its tests were committed**, which is exactly why
`pytest` cannot collect the suite. **The first measurement is mechanical and needs no CPU: check every
completed-task entry that names a code artifact against HEAD.** Nobody has ever done it.

**OPEN-12 does not reproduce (N06).** 36.4% → **100%**, 19.2% → **100%**, plus a third 100% cell
(`nyc_suburban`, 1,589 buildings) the item never named. **Not adjudicated.**

**A convergence no executor could see (director, N06 × N09).** N09's four cells with no committed
Overture slice are **exactly** N06's four worst cells for missing height. Two executors, different
files, no shared notes. **Strongly suggests OPEN-12 is really OPEN-14** — the backfill was never
committed. **One step still missing before that can be claimed**, and it is named in OPEN-14.

**OPEN-13 read at last (N09):** both defects live at HEAD; E-UTCI-12 means **`pytest` cannot collect
the suite at all**. **OPEN-10 answered from the IDD (N11):** capability real, **remedy narrower than
the item claimed** — 2 archetypes, not the other 7, and `n_real` 1–2 still inexpressible; the "90
buildings" figure is **carried, not re-derivable without a fleet pass**. **OPEN-19 (N12):** no
climate-zone or code-year switch exists anywhere; LA's HVAC comes from a **Buffalo, NY** prototype and
infiltration is one constant fleet-wide. **So "research Title 24" is not the first task — obtaining an
alternative table is.** The +40%/−0.6% figures are **carried, not verified**.

**One distinction the director drew and the user has not ruled on:** swapping one *published
standard's* table for another published standard's table is **not fitting**; tuning values to match
measured LA consumption **is**. Only the second breaks the zero-fitted-parameters guarantee. **Stated
as a distinction, not a recommendation.**

### 4ter.2 — 🔴 The round's synthesis. If you read one thing in this document, read this.

**N07 hit its own STOP condition, and that is the result.** It traced the `archetype_id` write path end
to end, **disproved all three hypotheses with evidence**, then **re-executed the path against the exact
frozen inputs** the committed file was built from. It produces `LargeHotel`/`SmallHotel` every time.
**The committed file holds Office, with real simulated EUI values.** One writer, not several.

**Put N07 and N08 together and the position is this:** four independent sources say hotel — the raw
OSM tag, the classifier at HEAD, the re-executed write path, and **the simulation that actually ran**.
**One artifact says office: the committed results file.** The column is an orphan.

**Three instances, one statement — verified from the repository, not inferred:**
1. **OPEN-36** — T07's implementation was never committed; **its tests were**, which is why `pytest`
   cannot collect the suite.
2. **A one-line fix to `v12_cell_pipeline.py:520` was applied to the working tree mid-run** and
   recorded only in a progress log (`PLAN_archetype_threshold_fix_E-R3-3.md:482`, 2026-07-01) —
   **director-verified**. This is the *mechanism*.
3. **OPEN-06 / N07** — a published column no code state can regenerate.

**The project's git history does not reliably capture what actually ran.**

**Say this whenever the pattern is summarised, because it is the difference between a records problem
and a results problem:** **no published number has been shown wrong by any of the three.** Instance 3
is a *label*, and N08 established the simulation used the correct archetype anyway.

**And it changes what the next measurement should be.** Checking completion records against HEAD is
the cheap pass, but it cannot catch instance 2 — there the record is honest and the commit is simply
absent. **The stronger check runs the other way: take each load-bearing committed artifact and ask
whether current code can regenerate it.** N07 did that for one column of one file. **No other column
of any published file has ever been checked**, and checking costs no CPU. **That is the strongest
candidate for the next round.**

**Two things a fresh session must carry forward from how round 1 went:**
1. **Both new items of that round came from auditing a report, not from running a task.** Audit by
   independent re-derivation from the raw files, never by reading the executor's report back.
2. **"Cannot be determined statically" and "the evidence is silent locally" are results**, not
   failures — N11 and N08 are explicitly allowed to return them. What is *not* allowed is escaping
   them by running something.

## 4quater. Round 3 — dispatched 2026-08-06 night. N14 and N15 have landed; N13 was re-dispatched.

Plan: `openings/implemenation/PLAN_no-compute-queue-3.md`. Three tasks, all no-CPU. **N14** and
**N15** are done and audited (§4quater.1, §4quater.2). **N13** sweeps every completed progress-log
entry naming a code artifact (T07 is the blind control, must return NEVER-COMMITTED) — **its first
attempt stalled without producing anything**: the agent ended its turn saying it would *"wait for the
background verification task to notify me"*, which never happens. Empty output, no artifacts, no
progress-log entry. Re-dispatched as a fresh Sonnet session with an explicit *never wait for a
notification, do all work in-session, spawn no subagents* clause. **This is the third occurrence of
that failure mode in this project — put the anti-stall clause in every dispatch from now on.**

### 4quater.1 — N15: the four-cell convergence is a coincidence, and I was the one who was wrong

Report: `extra/MEASUREMENT_open-12-14_backfill-consumption.md`. The question was whether the fleet's
`01_buildings.gpkg` ever consumed the UTCI arc's height backfill — the step OPEN-14 named as *"a
measurement nobody has run"*. **Answer: no, and it never could have.** Two independent lines, each
alone sufficient, both re-derived by me from the raw files:

- **Code reachability** — `fusion.fuse()` has exactly one caller fleet-wide (`imputation.py:655`), and
  `building_classifier.py`, which owns `_impute_levels`, **never imports the imputation module**. The
  fusion path is not on the fleet's code path at all. This is **architectural, not config-dependent** —
  stronger than the `FUSION_SOURCES_BY_TARGET = {}` no-op argument, and it holds even if that dict is
  populated.
- **Chronology** — `nyc_centre`'s `01_buildings.gpkg` is commit `e063865` (2026-06-30); its own
  Overture slice first appears at `ef19141` (2026-07-21). **Three weeks later.** A file cannot consume
  a slice that does not yet exist.

**Consequence: OPEN-12 and OPEN-14 are two separate items.** OPEN-12 is a genuine OSM-tag
source-coverage gap — exactly what the UTCI arc's closing note said, and that note is now vindicated.
OPEN-14 is its own reproducibility defect. **Neither may be closed by fixing the other**, and any plan
that treats them as one defect is wrong.

🔴 **Carry this forward as a method lesson, not just a result.** The four-cell convergence — N09's four
cells with no tracked slice being exactly N06's four worst cells for missing height — was **spotted by
the director, not by either executor**, and written into the register as *"the strongest available
evidence"* while marked NOT adjudicated. It was evidence for **nothing**: two unrelated causes landing
on the same four cells. **The not-adjudicated discipline is the only reason it never became a finding.**
When a convergence looks too good, it is a hypothesis to test, never a conclusion to record.

### 4quater.2 — N14: `archetype_id` is not the only column HEAD cannot reproduce

Report: `extra/MEASUREMENT_open-06_column-reproducibility.md`, CSVs
`open06_column_reproducibility.csv` (132 rows) and `..._diff_examples.csv` (18). Stage 2 re-run at
HEAD via the real `t08_full_sweep.run_step2()` over four **whole** cells — `nyc_centre`, `nyc_rural`,
`austin_rural`, `nyc_suburban` — all 33 committed columns bucketed. **The other 8 cells are not
covered.**

**Control PASSES and I verified it from N04's file, not from the report.** N14's differ counts
(`nyc_centre` 26, `nyc_rural` 4, others 0) match `open06_mislabel_population.csv`'s per-cell
distribution exactly, including the two zeroes.

**The second unreproducible column is `data_quality_flag`** — a computed column, since `classify()`
appends an imputation-provenance token. What differs is *which imputation rule fired*:
`VINTAGE_NAN_PERMISSIVE_DEFAULT` / `HOTDECK_NEIGHBOR_*` at HEAD against `GROUPMODE_MED` in the
committed file. **So HEAD cannot reproduce the archetype, nor the recorded reason for it.** Consistent
with N07's uncommitted-mid-run-edit provenance gap; **not proof of it, and not adjudicated.**

🔴 **I struck one of N14's own claims on audit.** Its §4 says the flag differs on *"the same 9 rows"*
as `archetype_id`. Its own CSV says 26 vs **38** on `nyc_centre`. The 12 extra rows differ only by a
trailing `narrow_perimeter_fallback` token, and that token is written by
`openubem/idf/builder.py:614-615` — **Stage 3**, which Stage 2 can never emit. Same spurious-difference
trap the plan flagged for `levels`/`height_m`. N14 caught the trap for `footprint_area_m2` and missed
it here. The verdict survives, narrower and cleaner.

**Its real contribution is a third geometry-derived column.** `footprint_area_m2` joins
`levels`/`height_m` as Stage-3-re-derived, not a Stage-1 passthrough — proved with **no Stage-2 code in
the loop**: raw vs. committed already differ on 715 of 738 `nyc_centre` rows, one by 101,106 m².
**Anyone diffing those three columns naively will report a defect that is not there.**

**And the honest limit: 26 of the 33 columns are still unchecked** — the EUI/GWP/`iod`/status columns
and `zoning_strategy` are Stage-3-or-later and absent from the Stage-2 frame entirely. No no-CPU task
can reach them. OPEN-06 stays open on its unchanged first measurement: *which code state produced the
committed column*.

## 4quinquies. Round 4 — dispatched 2026-08-06 night. ~~One task, N16, in flight.~~ **N16 landed and was audited; N13 landed too. The no-compute queue is empty.**

**Plan doc:** `implemenation/PLAN_no-compute-queue-4.md`. **It exists because N14 named its own
coverage gap** — four cells of twelve — and Stage 2 is authorised as non-CPU, so that gap is closeable
now rather than parked with the compute-bound work.

**N16 sweeps the remaining eight cells** (`nyc_urban`, `la_centre`, `la_urban`, `la_suburban`,
`la_rural`, `austin_centre`, `austin_urban`, `austin_suburban`) with the same imported
`t08_full_sweep.run_step2()`.

**What makes it worth the tokens is that the answer was written down first.** Plan §5.2 states a
prediction *before* the measurement: from N04's `open06_mislabel_population.csv` (41 rows,
director-verified by direct read — `austin_centre` 2, `la_centre` 4, `la_urban` 5, `nyc_centre` 26,
`nyc_rural` 4), `archetype_id` must DIFFER on **exactly 2 / 4 / 5** rows in the first three of those
eight and on **zero** in the other five. N14's four cells matched that list exactly, both zeroes
included.

- **HELD** → the mislabel population is fully accounted for, fleet-wide, and OPEN-06's scope is bounded.
- **EXTRA ROWS** → `open06_mislabel_population.csv` is **incomplete**, which is worth more than the
  confirmation would have been.
- **MISSING ROWS** → two audited artifacts contradict each other. **Plan §7 sends that to the user
  immediately**; it is a finding about the evidence base, not about OPEN-06.

**N16 also carries N14's correction as a binding instruction.** `data_quality_flag` differences must be
partitioned into **(a) STAGE-3-TOKEN** — identical once `narrow_perimeter_fallback` is removed, traced
to `openubem/idf/builder.py:614-615` — and **(b) PROVENANCE-DIVERGENCE**, the imputation token itself
differing. Counted separately per cell, with the set relationship to `archetype_id`'s differing rows
reported as a **checked** comparison. N14 asserted that relationship without checking it and was struck.

**The dispatch carries the anti-stall clause** (§4quater), now standing policy: do everything in
session, never wait on a notification, never spawn a subagent.

### Outcome — both landed 2026-08-06, both audited by re-derivation. Read this before you plan anything.

**N16: the prediction HELD, exactly, in both directions.** 2/413 `austin_centre`, 4/226 `la_centre`,
5/618 `la_urban`, and `n_differ = 0` in the other five. All 11 rows re-joined to N04's population by
the director on `(cell, osm_id)`: **11/11 on both values, zero extra, zero missing.** Coverage checks
arithmetically — **5,390 + N14's 2,770 = 8,160**, the whole fleet, whole cells, no subsets.

Three results you can now rely on:
1. **The 41-building mislabel population is fully accounted for.** No unknown remainder.
2. **No third unreproducible column exists** — `archetype_id` and `data_quality_flag`, in twelve cells.
3. **`data_quality_flag` is far less broken than N14's raw count implied**: of 171 differences,
   **168 are Stage-3 tokens Stage 2 cannot emit; only 3 are real provenance divergence.** Getting that
   split right needed a real tokenizer — four further Stage-3 appenders turned up beyond
   `narrow_perimeter_fallback`: `builder.py:145`, `:439`, `:473`, and `geometry/footprint.py:33,38`,
   **the last two comma-separated**, a different and undocumented convention. All five citations were
   opened on audit.

**And the finding that outlives the prediction:** those 3 divergences are **not the same buildings** as
the archetype failures. `la_urban/way/1176846930` regenerates its archetype perfectly yet its
provenance token differs; `la_centre`'s four archetype failures carry **no** divergence at all.
**The two defects are independent in both directions** — which finishes N14's struck "same rows" claim
rather than merely correcting its count. *(One correction on audit: the progress log's prose says
"both empty in the other six cells"; it is five. The report's own §4.3 table is right.)*

**N13: T07 is the only one.** The **full** population — **596** entries across 59 documents, not a
sample: PRESENT 424, MOVED 6, NEVER-COMMITTED 14, UNCHECKABLE 152. Of the 14, **one** governance gap
(T07), **twelve** this arc's own untracked CSVs (each verified on disk, untracked, zero commits), and
**one** temp script the entry itself declares deleted. The director re-ran the control: `_draw_tier`
exists in **no commit on any branch** and not in the working tree, while its tests are committed.

**Why the number is believable: it started at 49.** A mechanical heuristic flagged 49; every one was
re-checked with an unrestricted repo-wide `git log --all -S`, and **35 were misattributions**. Both
verdict columns are retained. **An unaudited run of the same sweep would have reported 49 phantom
completion records — remember that before trusting any mechanical sweep in this project.**

**Escalation discharged.** Round-3 §7 said NEVER-COMMITTED entries beyond T07 go to the user
immediately. Thirteen exist; all thirteen are benign on audit; reported.

**Where this leaves you: the no-compute queue is empty.** Sixteen tasks dispatched across four rounds,
all landed and audited. **Every remaining first measurement in the register needs CPU**, and CPU-bound
work is ~~**parked by user instruction** until a machine is free~~ **unparked 2026-08-06 — see §4sexies**.
Do not invent a seventeenth no-CPU task to keep busy — if you cannot name the register item it
measures and the way it could come back wrong, it is not worth the tokens.

## 4sexies. The compute queue — opened 2026-08-06 when the user released the machine

Plan: `implemenation/PLAN_compute-queue.md` (C01–C06). The user released the local workstation for
simulation and instructed the arc to run overnight to completion, updating documents as it goes.

### 4sexies.1 🔴 The blocker you would otherwise have walked into

The scoping doc costs E02 as **five modes × twelve cells**. The local runner could do **four modes ×
seven cells**, and only the mode gap was on record. `LOCAL_CELLS`
(`scripts/cluster/t08_local_remainder.py:48-51`) carried the LA/Austin remainder only — the four NYC
cells and `la_centre` had **no `CELL_CONFIGS` and no `CITY_OF` entry**. `CITY_OF` is read through a
**silent fallback to the cell name** (`:423`), so a missing entry does not raise; it produces
`city="nyc_centre"` and quietly breaks every city-level group-by downstream.

**The trap:** the runner is *named* `t08_local_remainder` because it exists to run the remainder of
the cluster's T08 — so the obvious move is to run 7 locally and reuse T08 for the other 5. **That
rebuilds OPEN-28.** T08 is five-week-old code (223 insertions in `builder.py` since) and deleted every
`.eio`, so it serves neither OPEN-02 nor a cross-mode delta that means the method rather than the
calendar. **Pinned: all twelve cells run locally, on one generation.** If anyone proposes the
shortcut, this paragraph is the answer.

### 4sexies.2 What has happened so far

**C01 — done, CP-C1 signed.** Runner extended to 12 cells / 5 modes (`layout_assign` last, so the
four exercised modes finish first in every cell), plus `--output-csv` and `--work-base` flags — the
runner **clobbers its output CSV after every cell**, and `t08_local_remainder_eui.csv` is a real
2026-07-01 artifact that must survive.

The executor declined the end-to-end test with a sound tail-risk argument — **but that argument was
about `layout_assign`, and the untested new cells were the bigger risk**, since a night is lost to an
EPW that will not resolve for `NY`. The director therefore ran the bounded smoke the executor's
reasoning did not cover (`nyc_rural`/`building`, cheapest mode, new cell): **198/198 success, 0 fatal,
`city="NYC"`, 198 `.eio` retained, 0 `.eso` surviving, 0.33 MB/building.** That is what CP-C1 exists
to retire. `layout_assign` is still unexercised locally end to end — scheduled last within each cell
for exactly that reason.

**One cosmetic mislabel, deliberately left:** `print_cp4_local_report()`'s banner still says
*"7 cells"*. **Do not read it as evidence of a 7-cell run** — the tables under it are data-driven.

**C02 — E02 launched 2026-08-06.** 40,800 simulations, 16 workers, `.eio` retained. Log at
`%TEMP%/ubem_e02_five_mode/e02_run.log`; output
`openubem/outputs/comparisons/e02_five_mode_fleet_eui.csv`. **Expectations were written into the plan
before the run started and must not be edited afterwards** (≈7.3–11.3 h, ≈0.1% failure rate, ≈43 GB
worst case). It closes **three** items at once — OPEN-01, OPEN-02, OPEN-28 — which is why it is worth
a night.

🔴 **CP-C2 is a completeness gate, not a formality.** Nothing downstream (C04, C05) starts until every
(cell, mode) is confirmed complete. **Analysing a partial fleet and reporting it as the fleet is the
failure mode this whole arc exists to prevent.**

**A risk recorded while C02 was still in flight, before the answer was known** (plan doc, note after
C02's entry): the scoping doc's 540 CPU-hours came from `sacct` over the **sbatch arrays**, and in the
cluster pattern Steps 1–3 run on the workstation *before* submission. **So the ≈7.3–11.3 h covers
EnergyPlus and not Step-3 IDF generation, which is additive, unbudgeted, and happens 60 times.** If
C02 overruns, that is the reason, and it was identified in advance rather than rationalised after.
**The §5 prediction was deliberately left unedited.**

**🔴 C02 was killed once, at ~02:15, and it was the director's fault — not a defect.** It had been
started with the **session-bound** background-command facility instead of as an independent OS
process, so a session compaction stopped it and every EnergyPlus child with it. The plan had already
said to launch it detached; the instruction was written and then not followed. State at the kill:
0 EnergyPlus processes, **561 of `nyc_centre/auto`'s 738** `.eio` written, 861 log lines, **no disk
guard, no traceback, no fatal**, and **no `sim_done.txt`** — so no pair was ever marked complete.

**The cost was small, and the reason is worth knowing.** Resume is **per building**, not per pair:
`t08_local_remainder.py:268` skips any building that already has an `eplusout.end`, and `.end` is in
`RETAIN_FILENAMES`, so trimming does not eat the resume marker. Relaunched 02:52:17 via
`Win32_Process.Create` (WMI), which parents the process to the WMI host and puts it in no job object
belonging to a session — PID 1048, 20 python workers confirmed. **New log
`%TEMP%/ubem_e02_five_mode/e02_run_2.log`; the first log is kept, not appended to.** Same
`--output-csv` and `--work-base`, so this is a resume, not a second run.

Two things follow that a later reader must not get wrong. **The ~35-minute hole in the timeline is a
kill, not a slow first cell.** And **the kill is not evidence about the ≈7.3–11.3 h estimate** —
judge that clock from the original 01:54 start; director error and estimate accuracy must not be
allowed to launder each other. On this machine, "background" in the tooling sense is **not**
"detached" in the OS sense, and a launch record should state the mechanism rather than assert the
property.

### 4sexies.2b C03 — OPEN-10's carried figure, settled

**90 reproduces exactly, unadjusted** — 66 `MidriseApartment` + 24 `HighriseApartment`, from a
fleet-wide pass over all twelve cells using the shipped `compute_band_map()`/`match_storeys()`.
**Take note of that, because carried numbers in this arc have a bad record** (OPEN-12's percentages
did not reproduce; OPEN-28's framing was wrong; N14's "same rows" claim was wrong). This one held, and
its 7,442-building population matches OPEN-01's crosstab independently.

Both of N11's limits confirmed at fleet scale, not asserted: the proposed verdict is populated for
**exactly** the two apartment archetypes (2,850 rows) and blank elsewhere, and all **2,276** apartment
`fallback_shorter` rows sit at `num_floors ∈ {1,2}` and **none** move.

🔴 **The finding that changes the item: fleet-wide `fallback_not_expressible` is 1,976 across 10
archetypes — `SmallOffice` alone is 1,580. So OPEN-10's remedy reaches 90 of 1,976 = 4.6%.** N11
called the "restore exact expressibility" framing overstated; C03 gives the number. **Do not let a
future plan present this as fixing the inexpressibility problem** — it fixes one twentieth of it.

**Method limit to carry:** the proposal was *modelled* (counterfactual `band_map` fed to the real
`match_storeys()`), not built. The 100% flip is a property of the band arithmetic, **not** a
verified EnergyPlus result.

⚠️ **A director slip worth knowing about, since it is the kind that produces false findings.** My
first re-derivation reported 4,682 changed rows across 16 archetypes — apparently contradicting the
scoping limit. It was a **NaN artifact**: the 4,592 non-apartment rows carry a *blank* proposed
verdict, and `NaN != NaN` is `True` in pandas. **The executor was right and my first number was
wrong.** If you re-check this CSV, filter to non-null before comparing.

### 4sexies.3 What compute cannot fix — do not schedule these

- **OPEN-19** (LA ~+40% hot): there is **no climate-zone or code-year switch** in the codebase and
  LA's HVAC comes from a **Buffalo** prototype. It needs code before it needs cycles.
- **OPEN-11**: precondition met, the six are the same six. What remains is a **user decision**.

### 4sexies.4 — E02 halted 2026-08-06 08:30; the ruling is parked

**C02 is dead. Read this whole subsection before touching the compute queue again.** Full record:
`PLAN_compute-queue.md` §8, "AUDIT — C02 halted by `MemoryError`; CP-C2 NOT signed", plus the
`C02-P1` and `DECISION OWED` entries after it.

1. **What killed it.** `e02_run_2.log` ends in a `MemoryError` inside `_run_one_ep`'s `shutil.copy`.
   Last write **05:47:01**. Not disk (655 GB free), not the disk guard (no `DISK GUARD` line in
   either log) — real memory exhaustion: `Win32_PageFileUsage` peak **53,214 MB** against an
   allocated base of **71,989 MB** on a 63.5 GB machine. **It is `fast_zone`-specific, not a general
   worker-count problem.** Total Step-3 IDF bytes for `nyc_centre`: `fast_zone` **751.3 MB** (max
   single IDF 14.26 MB) against `auto` 400.8 MB, `floor` 244.6 MB, and `building` just **59.4 MB**.
   **`auto`, `building` and `floor` all completed cleanly at 16 workers** — the worker count is fine
   for three of the four modes; it is `fast_zone` that exhausts commit when sixteen of its
   multi-hundred-MB models load at once.

2. 🔴 **FINDING 1 — the most important item in this subsection. A silent resume data-loss trap.**
   `main()` skips a mode entirely (Step 3, Step 4, harvest) the instant its `sim_done.txt` exists,
   and recovers its rows **only** by reading them back out of the output CSV once every requested
   mode of a cell is done. **`nyc_centre`'s three finished modes (`auto`, `building`, `floor`) are
   already marked done, and the output CSV was never written** — so a naive relaunch right now would
   silently produce a "fleet" CSV missing all 2,214 of those buildings, including `auto`, the mode
   OPEN-28's published comparison depends on, and nothing in the run would say so.
   **Mandatory restart protocol, before any relaunch:** delete the `sim_done.txt` of any (cell, mode)
   whose rows are not already sitting in the output CSV. **This is nearly free** — Step 4 resume is
   per building via `eplusout.end` (already in `RETAIN_FILENAMES`), so the 2,273 already-simulated
   buildings are skipped and only Step 3 (minutes) and the harvest re-run. **This cleanup has not
   been done yet.** Whoever authorises the relaunch must do it first, not assume the executor will.

3. **FINDING 2 — E-LA-21 is live in the E02 runner itself, a fifth script.**
   `t08_local_remainder.py:430` uses the one-space `"** Fatal **"` test. Register OPEN-29 already
   named four harvest scripts with this defect; **this run's own runner is a fifth**, and it is the
   one generating today's results. Demonstrated on the run's own artifacts: of 2,422 `eplusout.err`
   files, 2 contain a real fatal, both written two-space, matched by the one-space test **0 of 2**.
   The failure *count* still comes out right (derived from the process return code, 736/738
   correctly harvested) — **but `has_fatal` and the "Fatal-free: YES" banner are worthless** and
   would say clean over any number of real fatals. Not fixed; needs its own written task.

4. **FINDING 3 — the wall-clock prediction is wrong by roughly an order of magnitude, and the
   cause recorded in advance was NOT the cause.** Measured from `nyc_centre` (738 buildings,
   9.04% of the fleet), scaled ×11.06:

   | mode | measured, `nyc_centre` | scaled to the fleet |
   |---|---|---|
   | `auto` | ≈85 min | ≈**15.7 h** |
   | `building` | 12.7 min | ≈**2.3 h** |
   | `floor` | 41.7 min | ≈**7.7 h** |
   | `fast_zone` | 59/738 in 72 min, extrapolated | ≈**2–7 days** |
   | `layout_assign` | — | see C02-P1 below, do not scale it in |

   The three completed modes alone extrapolate to **≈26 h**, against §5 C02's **≈7.3–11.3 h for all
   five** — and §5 stays unedited, as it must. **Trap: do not blame unbudgeted Step-3 IDF generation**
   — that was the cause flagged in advance (the NOTE entry in the plan log), and measurement kills it:
   Step 2 is **2.5–2.7 s** per cell, Step 3 is **7.9 s for 149 buildings** (`la_rural`). The overrun is
   EnergyPlus itself running slower per building than the cluster-derived scaling assumed, dominated
   by `fast_zone`.

5. ⚠️ **Correction to the INCIDENT entry's timeline (append-only — the original entry is not
   edited, this supersedes its numbers only).** The first kill was at **02:50:45**, not "02:1x";
   the relaunch log starts 02:52:18, so the hole is **≈90 seconds**, not ~35 minutes; and 545
   completions were logged continuously through the window the original entry called dead, not 561
   at a hard stop. The director error and its lesson (session-bound ≠ detached) both stand — only the
   cost estimate was wrong, and it was wrong in the direction that makes FINDING 3 stronger, not
   weaker.

6. **C02-P1 — `layout_assign` probe, completed.** Run locally on `la_rural` (smallest cell, 149
   buildings), shared work base with E02, separate output CSV: **149/149 success**, Step 3 in 7.9 s,
   Step 4 in 319.6 s at 12 workers, whole mode **5.5 min**, 25.7 core-seconds per building. It
   retires the "`layout_assign` has never run locally" risk and shows it is nowhere near
   `fast_zone`'s cost. **Explicit warning: do not scale 5.5 min into a fleet estimate.** `la_rural`
   is the smallest, simplest cell, and cross-cell per-building costs are not comparable —
   `nyc_centre`/`auto` runs ≈110 core-seconds per building against this probe's 25.7. `layout_assign`
   is affordable and unblocked; its fleet cost is still unmeasured.

7. **The scope ruling was put to the user and PARKED at their instruction.** Nothing is cancelled —
   E02 is **halted, not abandoned** — and **no relaunch is authorised until they rule.** Options as
   put: **(a)** drop `fast_zone`, run the other four (≈26 h) + `layout_assign`; **(b)** all five,
   ~a week, `fast_zone` at reduced workers; **(c)** `auto` + `layout_assign` only, ≈16 h; **(d)** four
   now, `fast_zone` queued separately afterwards. **Every option requires item 2's marker cleanup
   first, regardless of which is chosen.**

8. 🔴 **RULED the same day — and the answer was on an axis none of the four options offered.** The
   user's decision: *"mettre a cote de E02 est une decision correct, des que des ressources speed
   devient disponible, nous pouvons continuer."* **E02 is parked to resume on the Speed cluster when
   its resources free up.** It is **not cancelled and not descoped** — no reduced-scope option was
   taken, the workstation is released, and **no relaunch is authorised until Speed is free.** Do not
   re-ask which of (a)–(d) they want; that question is spent. Full ruling and the four conditions on
   resuming are in `PLAN_compute-queue.md` §8, "RULING — CP-C2 / E02". **The four, compressed:**
   (1) item 2's marker cleanup still applies on any machine; (2) 🔴 **the stock cluster template
   deletes `.eio` — `submit_fleet_t08.sbatch:63` — and E01's retention is local-only, living in
   `t08_local_remainder.py`, so a cluster E02 on the unmodified template destroys the exact evidence
   OPEN-02 exists to get.** This is the highest-risk item in resuming on Speed; (3) do **not**
   concatenate the 3 finished local pairs with cluster output — that rebuilds OPEN-28; (4) confirm
   the account's CPU allowance is genuinely free first, and **never** cancel or deprioritise another
   project's jobs. ~~**Also owed:** `SCOPING_five-mode-rerun-cost.md`'s local projection is measured
   wrong by ≈10× (item 4 above) and still carries no correction — append one before it is used to
   re-scope anything.~~ **✅ DISCHARGED 2026-08-06 — the correction is written. See §4sexies.7.**

### 4sexies.5 — C06 — OPEN-09 settled while E02 stays parked

**C06 does not depend on E02** (the plan's own scheduling note authorised this — C06 reuses the
*existing* matched control, not C02's output), so it proceeded independently of the Speed-cluster
park above.

**Cost gate answered first, as required: the 150-building matched control (F11-N/F11-N-b, the
closed E-LA-20 arc's own population) already existed on disk in full — 300 raw run directories,
both arms, `.err`/`.eio`/`.sql`/`eplustbl.htm` all present. Zero EnergyPlus was run. Zero of the
400-simulation gate was used.**

**Result: "cosmetic" holds, tested for the first time.** Re-derived convergence status fresh from
raw `.err` text (96/150 non-converged at `thermal_mass=True`, 8/150 at `False` — reproduces the
carried figures exactly) and EUI fresh from each run's own `eplustbl.htm`. Split the True-arm's
150 per-building deltas by convergence status: **no alarming pattern** — every delta is negative,
the two groups' distributions overlap 96.3%, and the non-converged group's mean delta is *smaller*
in magnitude (−1.638%) than the converged group's (−1.855%), not larger. The difference is
statistically real (Mann-Whitney p=4.1×10⁻⁷) but small in absolute terms (≈0.22 pp ≈ 0.20 kWh/m²
at the median EUI). **The five inherited log entries (E-LA-14/16/18/19/23) do not need correcting
on substance — the claim holds at the one population it has ever been tested on — only on
epistemic status: inherited → tested.** Consequence (a) (the ≈3.66% fleet projection) remains an
untouched projection, as scoped. Full record: `PLAN_compute-queue.md` §8 "C06", and
`extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md`.

**Audited the same day by independent re-derivation — GREENLIT.** The manager re-walked all 300 raw
run directories with its own parser rather than reading the report back: 96/150 and 8/150 reproduce
exactly from `.err` text, means −1.6375 / −1.8550, overlap 52/54 = 96.3%, d=0.893, and no file under
either `runs/` tree has an mtime later than 2026-07-25 — **independent proof that zero simulations
were run and the 400-simulation gate was untouched.** One figure corrected: the register's "97%"
reverse overlap was not reproducible (actual 95.8%); only 96.3% is cited now. Audit: `PLAN_compute-queue.md`
§8 "AUDIT — C06".

### 4sexies.6 — C07 — the E02 runner can now see a fatal

**Completed and audited 2026-08-06, no CPU.** `t08_local_remainder.py:430` tested the one-space
`"** Fatal **"`; EnergyPlus writes **two** spaces. Now `\*\*\s+Fatal\s+\*\*`.

**The before/after was demonstrated, not asserted** — the project's own evidence rule. Over the same
2,422 `.err` files the halted E02 produced: old test **0** matches, new test **2** —
`way_266149332`, `way_266170765`. **Both negative controls are non-vacuous**, which is the part worth
knowing: the decorative lines `************* Fatal error -- final processing.` and
`************* EnergyPlus Terminated--Fatal Error Detected.` are physically present in those same two
files, so a looser regex would have over-counted. This one matches neither.

**Three limits — state them whenever this is reported.** It changes **no published number** and **no
failure count** (`status` always came from the process return code and was right). `has_fatal` is
computed at harvest time and never persisted, so nothing on disk is stale and every future harvest is
corrected automatically — `print_cp4_local_report()`'s `Fatal-free:` banner included, without editing
that frozen function. And 🔴 **E-LA-21 is not discharged**: the four harvest scripts were left
untouched **deliberately**, because fixing them is a user decision under OPEN-29, not a side effect of
a runner repair. **"Never use the `has_fatal` column" stays in force for every pre-2026-08-06
artifact.**

### 4sexies.7 — the cost-scoping document is corrected, and the correction has a lesson in it

`extra/SCOPING_five-mode-rerun-cost.md` now carries **PART 3** (2026-08-06). Its Part 2 projected the
local five-mode pass at **≈10–15 hours — an overnight run**. FINDING 3 measured it wrong by **≈10×**.

**Parts 1 and 2 are left unedited on purpose**, so the failed prediction stays visible beside the
outcome. PART 3 records what was predicted, what the machine did, and — the part that matters — **that
the cause pre-registered in advance was also wrong.** The plan blamed unbudgeted Step-3 IDF generation;
measurement kills it (Step 2 is 2.5–2.7 s per cell, Step 3 is 7.9 s for 149 buildings). The real cause
is that Part 2's **3.2×–4.6× local-vs-cluster speed factor was calibrated on three timing runs of one
building**, and that error compounds multiplicatively across 8,160 buildings × 5 modes.

🔴 **Two things a resuming session must not get wrong about this.** First, **Part 1's *cluster*
projection is NOT validated by the correction** — it rests on the same 5-cell, five-week-old T08
extrapolation for four of the five modes. **Re-derive it; do not reuse it.** Second, this is the
discipline working, not a failure: a cause was written down before the answer was known, and the
measurement falsified it. **Do that again.**

## 5. The rule that governs this arc

**No execution plan may be written for an item until that item's "first measurement" (named in its own
section of the register) has been made.**

1. **Measure** — small, scoped, measurement-only. Remediation **forbidden inside it**.
2. **Decide** — at the report, with the user.
3. **Plan** — only then write `PLAN_<slug>.md`.
4. **Execute** — fresh Sonnet per dispatch; audit each report against raw artifacts.

Assert on the quantity the defect actually moves, not a proxy.

**Corollary:** when an item's evidence is a document rather than a number, **verify the document is
still true before quoting it.** OPEN-03 and OPEN-28 both had register text that was wrong at HEAD.

**Second corollary, new on 2026-08-05:** measuring produces new items. Five measurements opened three
(OPEN-30, 31, 32). That is the process working, not scope creep — but say so plainly to the user, who
is tracking a count.

## 6. Hard rules — these override anything you infer

### 🔴 Cluster
**NEVER run compute on the Speed login node** (`speed-submit2` / `speed.encs.concordia.ca`). Only
lightweight ops: `squeue`, `sacct`, `ls`, `du`, `quota`, `mkdir`, `scp`, `tar`. All compute goes
through `sbatch --array`, fire-and-forget, then read the output file. **No `srun`, no `ssh … python …`.**
**Never cancel, requeue or deprioritise any cluster job**, least of all another project's.
**As of 2026-08-05 the account's CPU allowance is fully consumed by another project, and the user has
instructed that work be done locally where possible.**

### 🔴 Never
- **Never `git commit`** — git is handled externally by the user's own tooling. Do not offer.
- Never edit root `main.py`, any **OVERVIEW** or **DESIGN** doc.
- No `.py` files under `docs/` — ever.
- Progress-log and AUDIT entries are **append-only**. Never rewrite a frozen entry, including ones you
  believe are wrong — correct them in a new entry citing the old.
- 🆕 **The register is append-and-amend, but corrections there are struck-and-dated, never deleted.**
  Four register statements were corrected on 2026-08-05; all four remain visible with the correction
  beneath. A register that silently fixes itself cannot be audited.

### 🔒 Frozen — cite, do not rebuild
- `T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`. A fleet failure reopens the fix plan, **never** the
  constants.
- Everything under `layoutAssigner/figures/`; the `t17_*`/`t18_*`/`t19_*`/`t20_*` harvests;
  `openubem/idf/opaque_assembly.py`; the 25-IDF prototype library; `openubem/viz/`.
- **Do not re-submit the T20 fleet.** **Do not re-run the OPEN-05 defect-ID sweep.**
- 🆕 **Do not re-run M01–M05.** All five are measured, audited and signed.

### Evidence rules — this project has been burned by each of these
- Ground truth is the **raw** artifact: `eplusout.err` for run outcome (require the `** Severe **`
  line), `eplusout.eio` for multiplier-aware floor area. **Never** the `.end` file.
- **Never use the `has_fatal` column.** `False` on all 8,160 rows including the 7 real fatals.
- A parser that finds nothing must **say so**, never report `0`.
- **A before/after is not reportable until the "before" is shown to differ from the "after."**
- Check what generated a figure or CSV before concluding from it — a script that reimplements pipeline
  logic makes lookalike evidence. **`a1_prototype_storey_structure.csv` is the live example (§4.1).**
- **Recompute every headline number from the named file before you sign anything.** State this
  requirement explicitly in every executor brief you write.

## 7. Working with executors

- **Fresh Sonnet session per unit of work.** Never resume an old agent for new work. The plan doc is
  the single source of state. *Exception:* an agent still mid-task on a not-yet-reported unit.
- **Tell executors upfront to block on artifacts on disk, never to wait for a notification.**
- **An ambiguous mid-work message is not a finished session.** A 0-byte log is a *healthy buffered*
  job — check CPU before relaunching.
- 🆕 **Address messages by the correct agent id.** On 2026-08-05 a scope change was sent to the wrong
  running agent; it correctly ignored it, but a less careful executor would have acted on instructions
  meant for another task. Confirm identity in the message itself when resuming.
- Delegate monitoring to cheap models. **Minimum polling interval 30 minutes**; prefer event-driven.
- Do **not** read a background agent's `output_file` — it is the full JSONL transcript and will
  overflow your context.
- **Audit by independent re-derivation, not by reading the report.** Every one of M01–M05 was signed
  only after its headline numbers were recomputed from the raw artifacts by the director.

## 8. Documentation conventions

- **`docs/docs_ACTIVE/openings/` stays clean.** It holds the register, `prompts/`, `extra/`,
  `implemenation/` and — 🆕 **added 2026-08-06 at the user's request** — `reporting/`. **Every
  supporting document goes in `openings/extra/`.**
- 🆕 **`openings/reporting/board_published-numbers.html` is a snapshot copy, not the live board.** The
  user asked for a copy there at the pause. **The published artifact is still
  `implemenation/board_published-numbers.html`** — republish *that* path to keep the URL. If you update
  the board, refresh the `reporting/` copy too, or it silently goes stale.
- 🆕 **The progress board.** `docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html`,
  published at **https://claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639**. Republish the
  **same file path** to keep the same URL. Rules the user set: **every task appears**, **every task
  carries a short paragraph**, and **as each task completes the next moves into "in progress."** Update
  it on every change without being asked.
- Plan docs carry the project's mandatory sections — header, hard rules for the executor, file layout,
  pinned dependency decisions, verified facts with line citations **you personally grepped**, numbered
  tasks each with **what / why / how / how to test**, 2–4 checkpoints, and a progress log.
- **Correction-via-addendum:** never edit a frozen dated section of a results doc. Append the next one.
- All `.png` / figure outputs go **flat** to `openubem/outputs/`, mirrored into `docs_ACTIVE/<arc>/`.
- Every open/site metric gets registered in
  `docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md` **first**.
- Past ~1,000 lines, close a plan doc and open a `_REMAINder` citing old findings by ID.
- Keep `docs/PROJECT_CHECKLIST.md` current — §M indexes this arc.

## 9. State of the project around you

- **Adopted baseline:** `phaseE` full realism, E-R3-3-corrected. 12 cells, 8,160 buildings, **zero
  fitted parameters** — a guarantee any "calibration" work (OPEN-19) must not silently break.
- **`layout_assign` is adopted for zone/HVAC-topology studies and NOT certified for fleet-level EUI
  reporting.** OPEN-01/03/32 are all `layout_assign`-scoped. ~~Do not tell the user the adopted
  158.0 kWh/m² figure is affected — that is unmeasured.~~ **Superseded 2026-08-06 (M06): it is now
  measured, and the adopted figure is confirmed unaffected.** `auto` cannot reach `layout_assign`
  (`zoning.py:36-42`) and all 16,320 adopted rows carry zero `layout_assign`. **You may now state
  positively that the adopted baseline is clear — and you should, because the user has been carrying
  that uncertainty since 2026-08-04.** What you must *not* do is let it soften OPEN-01 or OPEN-03:
  both are exactly as large as measured, and every published `layout_assign` number, −29.1% included,
  is still wrong. See §4.8.
- The LayoutAssigner arc closed 2026-08-04, CP-E signed. Its documentation plan is closed; do not
  re-open it.
- ~~**In flight when this prompt was written:** the register amendment was being applied by a Sonnet
  executor.~~ **Landed and audited 2026-08-05.** The register carries it; totals agree everywhere.
- ~~**Nothing is in flight as of 2026-08-06.**~~ **Superseded the same evening.** No cluster job and no
  fleet submission — but **N01, N03, N04 and N05 were dispatched as parallel Sonnet executors**
  (§4bis) and may still have been running when this prompt was last written. **Before doing anything,
  check `PLAN_no-compute-queue.md` §8 for which of N01–N05 have progress-log entries**, and audit any
  that landed unaudited. N02 is done and signed.
- **Uncommitted working tree.** The 2026-08-06 evening's work touched
  `docs/PROJECT_CHECKLIST.md`, the register, `docs/docs_EXPLANATION/` (6 files),
  `docs/docs_REPORTS/REPORT_phaseE_final.md`, the board, and this prompt; it added
  `extra/MEASUREMENT_open-32_adopted-dependency.md`. **Git is handled externally by the user — never
  commit, never offer to.**
- ~~**C02 (E02) is running overnight; do not disturb it.**~~ **SUPERSEDED 2026-08-06 08:30 — E02 is
  HALTED, not running.** It died of a `MemoryError` at **05:47:01** and the machine has been idle
  since. **Nothing is in flight.** Do not tell a fresh session a run is in progress, and do not
  relaunch anything: the scope ruling is parked with the user (§4sexies.4), and FINDING 1's marker
  cleanup has not been done. Any executor told "check on E02" is being given a stale instruction.

## 10. What "done" looks like for this arc

There is no single checkpoint — this arc is a **queue**, not a march. It is healthy when:

- Each opened item has had its first measurement made **before** its plan was written.
- Each closed item is struck from the register with a dated one-line disposition and its evidence mark
  upgraded to ✅.
- Items that turn out to be already-fixed, duplicated, or stale are **removed with a reason**.
- The register stays the single place open work is recorded.
- **The board reflects reality at all times.** It is how the user sees the project.

---

**Your first action: read the register, then put §3's owed decisions to the user — one at a time,
starting with the one that unblocks work rather than the one that is most interesting.**

~~**As of 2026-08-06 that ordering has a clear answer.** … Ask, in this order: `building` mode, which
night, CP-M3 + OPEN-33, CP-M2, OPEN-22.~~
🔴 **SUPERSEDED the same evening. Both items 1 and 2 are resolved or withdrawn — do not ask them:**
item 1 was **asked and answered** (verify first) and the verification is **done and signed** (§4.10);
item 2 is **moot** because the user parked all CPU-bound work (§4bis).

**The ordering as of the 2026-08-06 evening.**

**Do not open by asking which item to work on.** The user handed selection to the director for
no-compute work and asked for several tasks at once (§4bis). **Open by reporting what landed**, then
ask only for **rulings**, one at a time:

1. **CP-M3 + OPEN-33 + OPEN-30 together** — what a change must carry before it counts as finished.
   Three instances of one question (register §9 pattern 5). *This one first: it is the only one that
   changes how future work is done, rather than what is known.*
2. **OPEN-22's ruling** — now backed by a real number (§4.11), so it is a decision rather than a
   request for a measurement. **Frame it as "the fallback rows are not inflating the metric, but a
   third of the exam is size-bucketing — is that the exam you want?"**
3. **CP-M2** — what to do about the published cross-mode numbers, confirmed confounded.

**Do not lead with the register's item count.** The user tracks it, and it went **up** (30 → 31, with
OPEN-34). Say plainly that measuring opens items and that this is the process working — register §5's
second corollary — before quoting any total.

**Still true and still worth leading with, if the user has not heard it:** **the numbers this project
stands on are confirmed clear of the two big unfixed errors** (§4.8).

---

## 🅿️ 11. The pause — written 2026-08-06, at the user's instruction

**The user is moving to other projects and will return when they have time.** This is a pause, not a
close. The arc is in a clean state: no half-finished task, no unaudited executor report, no run to
babysit, and no document owing a correction.

**What "clean" means concretely, so a returning session can trust it:**

- **Every dispatched task has landed and been audited by independent re-derivation** — sixteen
  no-compute tasks across four rounds, plus C01, C03, C06, C07 and the C02-P1 probe.
- **Every completed task is written to all three surfaces** — the plan's progress log, the register,
  and this prompt. Nothing is carried only in a conversation that no longer exists.
- **The one outstanding bookkeeping debt is discharged** (§4sexies.7).
- **The register's closing amendment is the compressed resume brief.** It is deliberately written to
  stand alone.

**When you resume, in this order:**

1. **Confirm the machine is still idle** and that no stale `sim_done.txt` cleanup was done in the
   meantime — FINDING 1's trap is dormant, not defused.
2. **Report the state to the user before proposing anything.** They have been away; do not assume they
   remember where E02 stopped.
3. **Put one ruling to them** — the top box's list, starting with CP-M3 + OPEN-33 + OPEN-30.
4. **Only then** consider work. If Speed has freed up, CP-C2 is the unblocking question and the
   `.eio`-deletion risk (top box) is the first thing to fix, before a single job is submitted.

**Do not, on resuming, invent a task to demonstrate momentum.** Every remaining first measurement needs
CPU or a ruling. That is a legitimate resting state for this arc, and it was reached deliberately.
