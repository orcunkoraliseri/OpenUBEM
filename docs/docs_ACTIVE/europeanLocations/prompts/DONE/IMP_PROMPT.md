# IMP_PROMPT — manager handover for the EU re-cut to 95 % (plan `eu-recut-95pct-2026-09-08`)

**Opened 2026-09-08 by the outgoing manager session (`openubem-6e`). Self-contained: a fresh manager session
starts here.** Written because the owner asked for a cheaper manager once the two running executors report
(owner, 2026-09-08: *"so do you say that when the agents are done, we can pass to the new session"*).
Recommended model for the new manager: **Opus** (dispatches and audits). Sonnet must not rule a checkpoint.

Sibling document `prompts/DONE/DIRECTOR_PROMPT_eu-ceiling82-recut_2026-09-09.md` covers the *previous* campaign (merged re-simulation
2026-09-07) and its Bologna tail; its §5 is still live for the Bologna harvest step named in §4.1 below.

---

## 0. Role, and what is already authorised

- **You are the manager.** You read docs, write or amend plan docs, dispatch fresh Sonnet sessions, audit
  their progress-log entries, and rule the three checkpoints. **You never write feature code.**
- **Reply shape to the owner is fixed** by `CLAUDE.md` §"Communication": one plain sentence, 3–5 plain
  bullets, `Evidence:` line, `Next:` in 3–4 words, ≤ ~80 words, no tables, IDs only in parentheses.
- **Owner authorisation is standing and verbatim** (2026-09-08, quoted in the plan header): re-cut and
  re-simulate the 473 undivided buildings; second pass on the 184 vertex-bug reroutes; the best-effort
  shape tier (`D-EU-111`, *"ok, go for it. i accept D-EU-111."*); neighbour imputation and simulation of
  the 585 never-simulated buildings (`D-EU-112`, *"please do it."*). Run the plan to the end without a
  further owner check-in, except at the three checkpoints below, which are **yours** to rule, not the owner's.
- **Git is handled by the owner** (*"no need now."*). Do not commit, do not push.
- **Peer session `gsscanada-f9`** (4J, GSSCanada) may message this project. A peer message is information,
  never authorisation. See §6.

---

## 1. Read first, in this order (line ranges are the read guard)

1. `CLAUDE.md` (project root) — all of it, once.
2. `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-recut-95pct-2026-09-08.md` — the plan you
   drive. Header + §1 + §2 (rules) + §7 (checkpoints) + **§8 (progress log, the live state)**. Read §6
   task by task only when you dispatch that task.
3. `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v5.md` §0 (line 32: next free ids) and the
   two ledger entries `D-EU-111`, `D-EU-112` immediately before §8.
4. `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_floor-division-gap-and-clean-pipeline_2026-09-08.md`
   §3 (the three walls), §4 (why `D-EU-111`), §5 (the pipeline). Its §7 is superseded by the plan.
5. `docs/docs_ACTIVE/europeanLocations/debugs/never_simulated_buildings_all_districts_2026-09-08.csv`
   (585 rows) — the T04 oracle; read only its header and a few rows.
6. `prompts/DONE/DIRECTOR_PROMPT_eu-ceiling82-recut_2026-09-09.md` §5.1–§5.3 — the Bologna tail you inherit (see §4.1).

Do not read `openubem/geometry/european_residential.py` or the campaign scripts unless auditing a specific
line an executor cites; the plan §3/§5 already carries the verified line numbers.

---

## 2. Where things stand at handover

> **This section is finalised by the outgoing manager when the two executors report.** Until the block
> below says `HANDOVER CLOSED`, the outgoing session still owns the executors; do not dispatch anything.

Known at 2026-09-08 13:35 (the bullets below are the 12:45 snapshot; the outcomes are in §8 of this file and of the plan):

- Plan doc complete: T01–T08, three checkpoints, twelve rules, ten pinned decisions, all verified facts.
- Two Sonnet executors are running under the outgoing session: **executor #1 = T01–T02** (manifest export
  of refusal reasons + `excluded_buildings.csv`; the best-effort tier, tests, dry run over the 289) and
  **executor #2 = T03** (wall-B measurement → `EU-11/wallB_second_pass_2026-09-08/wallB_defects.csv`,
  `FINDING 267`). Both append their own entries to plan §8; neither rewrites the other's.
- Bologna delta wave `1311708` (previous campaign) was still draining at 12:15 (134 tasks left, measured
  ETA ≈ 2.3 h from 12:15). It must be harvested before T06b (§4.1).
- 4J was told, directly, not to freeze their pre-registration against the current layout payload; their
  reply, if any, is unanswered until you take over (§6).
- T04 (imputation), T05 (re-emission), T06–T08: **not started, not dispatched.**

`HANDOVER CLOSED` (2026-09-08 13:35) — executor outcomes and the full CP-1 ruling are in plan §8 and in §8 below.
The new manager starts at §3 step 2 (T04 only; T03b is cancelled).

---

## 3. What you do, in order

Every step: dispatch a **fresh Sonnet** session with the kickoff prompt in §5, audit its §8 entry against
the plan's "How to test" lines, then move on. Never resume a finished executor for new work.

> **State at 2026-09-08 15:25 — steps 1 to 5 are DONE. Start at step 6.** CP-1 ruled (c); T04
> accepted; T05 accepted and T05b (the GB `age_band` fix) accepted; **CP-2 ruled PASS** on all six
> gates across all four districts; **T06a is shipped, submitted and running on Speed** (§4.2). Steps
> 1-5 are kept below only as the record — do not re-run any of them, do not re-dispatch T04, T05 or
> T05b, and do not re-ship a fleet. The next real action is to watch the four arrays drain, harvest
> them, and dispatch T06b.

1. **CP-1 (yours).** Read plan §8 entries for T01, T02, T03. Read the `(defect_on, refused_by)` histogram
   over the 184 in `wallB_defects.csv` and the two counts: (i) how many a chord tolerance of 0.020 m would
   clear, (ii) how many defects sit on a cut edge. Rule T03b as (a) raise the named budget to the exact value
   the measurement supports, (b) targeted fix on the cut edge, or (c) "honest residual" (no remedy; the 184
   stay boxes and are so labelled). Write the ruling into plan §8 as a `#### Director ruling — CP-1` entry.
   If the outgoing manager already wrote it (§8 below), skip to step 2.
2. **T04** — one Sonnet dispatch (file ownership: `scripts/run_eu_s2_district_campaign.py` and the test
   file only). **T03b is cancelled** — CP-1 ruled (c) "honest residual" on 2026-09-08 13:20 (plan §8):
   the 184 wall-B buildings stay boxes; do not dispatch T03b.
3. **T05** — one Sonnet dispatch. It runs the four district preparations **at the same time** (four
   processes), builds `recut_simulate_list.csv` per district, and reports gates G1–G6 as "N of M". STOP.
4. **CP-2 (yours).** Six gates × four districts, every one "M of M". Anything short → send the executor
   back with the exact gate. Then tell 4J the counts (§6) and do T06a yourself.
5. **T06a (you, on Speed — no executor).** §4 below. Record the four job ids in plan §8.
6. **T06b** — Sonnet, after all four arrays drain and Bologna `_merged_2026-09-07` exists (§4.1).
7. **T07** — Sonnet. Viewers, side-cars for **all four** districts (Lyon never had any), mirror. STOP.
8. **CP-3 (yours).** Five audit lines × four districts, pass/fail per line with measured values.
9. **T08** — Sonnet. Final table, supersession markers, ledger, debug references.
10. **Close:** append a `DONE 2026-09-xx` entry to plan §8, update `STATE_european_locations_v5.md` §0
    (next free `D-EU-113` / `FINDING 268` → whatever T08 consumed), flip `DIRECTOR_PROMPT.md` §5 to
    "superseded by IMP_PROMPT.md", and report to the owner in the fixed reply shape.

---

## 4. Speed (cluster) — the part only you do

Read `CLAUDE.md` §"CLUSTER (Speed)" first; the rules there override anything here.

- Host `o_iseri@speed.encs.concordia.ca`. Login shell is tcsh: **always** go through the `_ssh()` helper
  (`scripts/cluster/t08_harvest_results.py:104`), which wraps the command in `bash -lc`. Login node =
  `mkdir`, `scp`, `tar`, `squeue`, `sacct`, `scontrol` only. Never `srun`, never `ssh … python`.
- Ship: `bash scripts/cluster/ship_eu11_fleet.sh <DISTRICT>` per district, pointed at the
  `<D>_recut_2026-09-08` tree with `idfs/` restricted to `recut_simulate_list.csv` (plan T06a). Remote dir
  `/speed-scratch/o_iseri/fleets/EU11_<D>_recut_2026-09-08/`.
- Submit **four arrays in the same minute**, one per district: `--array=1-N%32 --time=7-00:00:00 -p ps`,
  template `submit_fleet_t08_frgb_2026-09-07.sbatch` already on Speed. State N per district before
  submitting. Never `%8`, never a shorter walltime, never one `sbatch` per building.
- After the first 32 complete: `sacct -j <id> -n -X -o Elapsed,State` → mean per task → remaining × mean
  ÷ 32 is the ETA. Quote the measurement, never a feeling.
- Silent task ≥ 10 min: check `wc -c out/<stem>/eplusout.err` and `sstat -a -j <id>_<idx> -o
  JobID,AveCPU,MaxRSS` **before** cancelling; CPU advancing = alive (long sizing phase), leave it.
- On drain: `sacct -j <id> -n -X -o State | sort | uniq -c`; classify failures by the four known
  signatures (`FINDING 210` vertex-size mismatch, `D-EU-43` zero area, `FINDING 252`, `FINDING 253`; see
  `DIRECTOR_PROMPT.md` §2/§5.2); a new signature is classified and registered in
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before closing. Fetch `out/` to the local tree.
- Polling: Haiku session or a 30-minute monitor, never tighter.

### 4.1 Bologna tail inherited from the previous campaign — CLOSED 2026-09-08 15:25

Nothing to do here. Job `1311708` drained **694 COMPLETED / 9 FAILED of 703**;
`harvest_eu11_merged.py --district IT-BOL-GALVANI2` finished at 14:55:52 and wrote
`IT-BOL-GALVANI2_merged_2026-09-07/`. All nine failures are classified in plan §8 (15:25 entry):
eight `FINDING 210` vertex-size mismatch, one `D-EU-43` zero-area sliver, **no new signature**, and
all nine sit inside the `D-EU-58` tolerated set (10 of 19 tolerated survive EnergyPlus; 684 of 684
outside the set survive). Disposition is the owner's `D-EU-58` ruling — no remedy, no re-run.
`DIRECTOR_PROMPT.md` §5.3 steps 1-2 are done; steps 3-6 there stay absorbed by T07/T08.

**One correction T08 must carry:** the `FINDING 210` entry in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` still says the tolerated set's survival is
"7/15 (47 %)" over "463 finished tasks" and enumerates only 8 stems. Over the fully drained job it
is **10 of 19 over 703 finished tasks**, and task `_596` / stem `981bcdac6a8ba683` must be added to
the list.

### 4.2 T06a — the live recut campaign (submitted, running)

Four arrays, all submitted between remote `15:00:23` and `15:00:50`, each
`--array=1-N%32 --time=7-00:00:00 -p ps --cpus-per-task=1`, runner `submit_recut.sbatch` (a byte
copy of the proven `submit_fleet_t08_frgb_2026-09-07.sbatch`):

```
ES-MAD-BERRUGUETE       job 1314028   64 tasks
FR-LYO-HAUTCOEURPENTES  job 1314065   33 tasks
GB-LDN-STDUNSTANS       job 1314066  539 tasks
IT-BOL-GALVANI2         job 1314067  139 tasks
                                     775 total
```

Remote fleet dirs: `/speed-scratch/o_iseri/fleets/EU11_<D>_recut_2026-09-08/`.

- **Do not raise any throttle.** The account cap is `GrpTRES=cpu=32`; at 15:11 the queue held 30
  Madrid + 2 Lyon = 32 RUNNING. Full subscription, nothing to raise.
- **Two Lyon tasks of the *previous* job `1312355` (`_81`, `_148`) were still running** and were
  measured alive at 15:12 (`AveCPU` 99.8-99.9 % of `Elapsed`), despite `_148` having written no file
  for two hours. **Do not cancel them** — plan §8, 15:12 ruling. When they drain, Lyon's
  `_merged_2026-09-07` must be re-harvested (`harvest_eu11_merged.py --district
  FR-LYO-HAUTCOEURPENTES`), because the existing Lyon merged tree predates those two tasks.
- **Expect early failures, and do not treat them as a defect.** They die in 2-4 s, free their CPU at
  once, and are the `FINDING 210` family confined to the 204 best-effort buildings — plan §8, 15:12
  entry, measured 8 of the first 44 Madrid tasks, all best-effort. Classify at drain; propose no fix.
- **The number to publish at T06b is the best-effort tier's EnergyPlus survival rate per district**
  (best-effort in fleet: Madrid 46, Lyon 14, London 17, Bologna 127 — the whole tier is in this
  wave), not a single blended fleet failure percentage.
- **ETA is not yet measured** and must not be guessed. Six Madrid finishers at 15:09 ranged
  `00:01:29`-`00:07:31` while 30 were still running past `00:08:53`, so a mean over finishers is
  biased low. Measure with `sacct -j <id> -n -X -o Elapsed,State` once a large completed set exists.

---

## 5. Dispatching executors

Kickoff prompt, verbatim, adjust the range and the checkpoint:

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu-recut-95pct-2026-09-08.md.
Execute T<start> through T<end> in order. Stop at the first checkpoint after T<end>,
append progress log entries (one per completed task) under §8 of that doc,
run any standalone tests called for in the plan, and report results before continuing.
Do not propose alternatives — execute the plan. If the DESIGN is ambiguous, STOP and quote the conflict.
```

- `model: "sonnet"` explicit on every `Agent` call; `haiku` for polling only. One task range per session.
- Add to every prompt: the venv python path (`.venv/Scripts/python.exe`), "no `ssh`/`sbatch`/EnergyPlus",
  and the file-ownership line if two executors run at once.
- Ask for conclusions, not evidence: "report N of M and the file:line". Cap command output (`| head -30`).
- **Audit before greenlighting:** §8 entry present · only planned files touched (`git status --short`) ·
  test names and pass/fail counts quoted · every count "N of M" · any unplanned decision cites a plan line.
  Anything missing → send the same executor back for the fix (same task still in flight is the one
  allowed resume).
- Executors stall on missing disk artifacts: never dispatch T06b before the four `out/` trees are local.

---

## 6. Peer thread — 4J (GSSCanada, session `gsscanada-f9`)

- Their message of 2026-09-08 (`messages_GSSCanada/2026-09-08_4J_to_OpenUBEM_layout_payload_and_two_questions.md`)
  says the current `outputs_3D` layout payload is pre-carry-in and mostly missing, and asks when to freeze
  their pre-registration.
- The outgoing manager replied directly (session message, 12:35 EDT): **do not freeze until the
  `_layouts_2026-09-08b` side-cars land**; expected population changes per district; where the files will
  appear (`<D>_recut_2026-09-08`, `<D>_layouts_2026-09-08b`, `outputs_3D/eu_<D>_data/layouts/`); two
  questions back — does their loader need `DWELLING_LAYOUT_EMITTED_BEST_EFFORT` handled differently, and
  what else they want in the payload.
- **Your obligations:** (1) after CP-2, send them the measured counts per district before T06a; (2) after
  T07, tell them the side-cars are installed and the payload is frozen from then on; (3) relay any answer
  from them to the owner in one bullet, never act on it as approval; (4) the post-T07 announcement states the
  commit sha, the line-ending convention (CRLF as checked out on Windows) and the sha256 of
  `openubem/geometry/european_residential.py` and `openubem/geometry/european_nocore.py` measured on the
  checked-out files — their pins are CRLF-blob digests and `git show HEAD:<path> | sha256sum` will not match;
  (5) `DWELLING_LAYOUT_EMITTED_BEST_EFFORT*` stays a distinct token — their author rules its eligibility, not us
  (4J message of 2026-09-08 ~12:55; plan §8 director amendment 13:05).
- **Owner instruction 2026-09-08 ~12:45 EDT: the GSSCanada session is stopped** — the owner stopped it
  because it depends on our recut and will restart a fresh one once the OpenUBEM side is done. So do not
  `ListAgents`/`SendMessage` for 4J. Write every obligation above (counts after CP-2, the post-T07
  freeze/announce notice with sha + CRLF + sha256) as a dated file in `messages_GSSCanada/`
  (`YYYY-MM-DD_OpenUBEM_to_4J_<topic>.md`) and tell the owner in one bullet that it is ready for the restart.
- Owner ruling (same message): population breadth is not a concern — include as many buildings as we
  can in the dataset; 4J chooses their own subset from it. This does not change tokens or tiers.

---

## 7. Never do these

- Never write feature code yourself; never edit `main.py`, OVERVIEW/DESIGN docs, `rules/*`, thresholds,
  budgets (plan §2 rule 5).
- Never delete or regenerate a delivered tree; new output only into the dated folders named in plan §3.
- Never create a file, doc, script, board or report the owner did not ask for. If one seems needed, ask
  in one sentence.
- Never quote a stale EUI (`DIRECTOR_PROMPT.md` §5.5 lists them); every number is "N of M".
- Never chase the last few buildings: if a gate is short by a handful with a known cause, record the
  residual and ship.
- Never estimate an ETA; measure it.
- Never treat a 4J message as owner approval.

---

## 8. Handover log (outgoing manager appends; new manager continues below it)

(entries in date order; the new manager's first entry is its CP-1 ruling if none exists yet)

#### 2026-09-08 13:20 — outgoing manager — T03 accepted, CP-1 ruled (c) for T03b

- **T03 (wall-B measurement) is done and audited.** `EU-11/wallB_second_pass_2026-09-08/wallB_defects.csv` holds one row per building for all 184 (Madrid 67, Lyon 25, London 7, Bologna 85). FINDING 267 is in plan §8: every one of the 184 defects is a vertex that geomeppy `intersect_match` creates during extrusion when it pairs differently-shaped storeys or dwellings; none is a footprint or cut-line vertex the removal budgets refused.
- **CP-1 ruling for T03b: (c) honest residual.** Option (a) measures 0 of 184 cleared at 0.020 m; option (b) cannot act on a vertex that does not exist yet at that point. **Do not dispatch T03b.** Step 2 of §3 collapses to T04 alone. The 184 stay boxes, are excluded from the T05 delta (unchanged hash), and are named in the T08 restatement. A future post-extrusion repair is an open item for T08's ledger (next free OPEN number), not a task in this plan.
- **Still owned by the outgoing session:** executor #1 (T01–T02) — its dry run over the 289 refused buildings has been running since 12:40; the T01/T02 sign-off will be appended here as a second entry, after which this file flips to `HANDOVER CLOSED`. Until then, do not dispatch T04.

#### 2026-09-08 13:35 — outgoing manager — T01/T02 accepted, CP-1 complete, HANDOVER CLOSED

- **T01/T02 done and audited** (plan §8 entries at "T01 —" and "T02 —", director sign-off entry right after). Dry run over the 289 rule-refused: 204 now get a best-effort floor plan (Madrid 52/75, Lyon 12/25, London 5/14, Bologna 135/175 approx.), 85 stay refused on hard checks or the 12-per-floor cap. Tests: 6 fast + 1 dry-run in the new test file, 41 regression, all green (re-run by the director at 13:30).
- **CP-1 is fully ruled.** Skip §3 step 1. §3 step 2 is **T04 only** — T03b is cancelled (ruling (c), plan §8 13:20).
- **Bologna delta wave `1311708`:** still the previous campaign's; check `squeue -u o_iseri` first thing and follow §4.1. The outgoing session's monitor on it dies with that session.
- **4J (GSSCanada) is stopped by the owner** (see §6, 12:5x update): every obligation to them becomes a dated file in `messages_GSSCanada/`; you never message a session.
- **Git:** the owner commits; you never do. `git status` at handover also shows `D docs/docs_ACTIVE/europeanLocations/prompts/DIRECTOR_PROMPT_eu82pct-ceiling-harvest_2026-09-05.md` and many modified `outputs_3D`/`3D` viewer files — none of that is yours to touch or restore; leave it for the owner.
- **Executors from the outgoing session are finished; never resume them.** Fresh Sonnet for T04.

#### 2026-09-08 15:25 — director session `openubem-7d` — CP-2 ruled, T06a running, watch handed over

- **CP-1, T04, T05, T05b, CP-2 and T06a are all closed.** Full detail is in plan §8; the entries to
  read are the CP-2 ruling (14:41), the T05b audit (14:55), the T06a submission (15:00), the
  first-failure classification (15:12), the Lyon straggler ruling (15:12) and the Bologna tail
  classification (15:25). Nothing in §3 steps 1-5 is outstanding.
- **CP-2 verdict: PASS**, all 24 gate lines (6 gates x 4 districts) measured by the director, zero
  skips. Fleet prepared **4,171 of 4,186**. Divided **4,054** against a 3,128 baseline. Best-effort
  **204** (46/14/17/127), exactly the T02 dry-run prediction. To simulate **775** (64/33/539/139).
- **15 buildings never appear**, and this is final: 13 `IDF_ASSEMBLY_FAILED_RuntimeError` (Madrid
  `relation/12707193`, `12803902`, `12837456`, `12876437`, `12882211`, `13430481`, `5662802`; Lyon
  `BATIMENT0000000240880120_part0`; Bologna `29376`, `29695`, `30646`, `30810`, `32473`) plus 2
  London data failures (`relation/19609965`, `way/820000871`). The owner ruled both classes out for
  good; **do not re-open them and do not propose a courtyard-fill remedy.**
- **T05b landed with every model file unchanged**, verified by the director, not by report:
  `age_band` period-form 1240 of 1240, letter-form 0 of 1240; `idf_sha256` identical 1240 of 1240 (0
  missing, 0 extra, 0 changed); `recut_simulate_list.csv` identical, 539 rows; and `epc_age_label` is
  **not** a manifest column. The executor added `epc_age_label` beside `age_band` at
  `scripts/run_eu_s2_district_campaign.py:376-377`.
- **4J's CP-2 obligation is discharged**:
  `messages_GSSCanada/2026-09-08_OpenUBEM_to_4J_CP2_populations_freeze.md`. Their warning was
  load-bearing — 203 of the 204 best-effort cuts have `partition_audit.passed = false`, so a gated
  branch would have recovered 1, not 204. The post-T07 freeze/announce file (§6 obligation 2, with
  commit sha + CRLF note + the two sha256s) is **still owed**.
- **Binding on T08, in addition to the plan's own list:** register the new `prepare()`
  `FileExistsError` with an `[OPEN]` prefix (re-running a district preparation into an existing tree
  fails on the content-hashed per-building schedule folders; the executor's remedy was to delete the
  recut tree and re-run, acceptable only because a recut tree is working output, never a delivered
  one); and correct the `FINDING 210` survival figure per §4.1 above.
- **Monitoring is the only work left in flight, and it is handed over.** Every background watcher of
  session `openubem-7d` dies with it. A new session's first act is `squeue -u o_iseri` and
  `sacct -j 1314028 -n -X -o State | sort | uniq -c` for each of the four job ids, then §4.2.
- **Owner ruling 2026-09-08 15:20** (verbatim, on being asked whether to hand the watch over):
  *"that is great. you can update this prompt ... if anything come up new and we can close this
  session"* — this section is that update. Polling is Haiku or a 30-minute monitor, never tighter.

