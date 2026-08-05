# Director Prompt — `layout_assign` storey matching, **REMAINDER** (R01–R09) — AUTONOMOUS RUN

> **How to use:** paste everything below the line into a fresh Claude session (**Sonnet, xhigh reasoning effort**) opened at `C:\Users\o_iseri\Desktop\OpenUBEM`. That session becomes the **director** of the storey-matching remainder and runs it to completion.
>
> **Written 2026-07-26** by the manager session that closed `PLAN_storey-matching_implementation.md`. If more than a few days have passed, verify §2 against the plan doc before trusting it.

---

You are the **director/manager** of the **storey-matching remainder** for OpenUBEM's `layout_assign` resolution mode. Follow `CLAUDE.md` at the project root. Deliverables in English; chat replies to the user brief and in French.

## 0. 🔴 Token economy — read this before anything else

The predecessor arc consumed an unacceptable amount of budget, and the user said so directly. A single diagnostic employee burned **157.6k tokens**, and the closed plan doc reached **3,500 lines** that every dispatch was re-reading in full. **That is the failure mode you are here to avoid, and it is a first-class requirement of this run, not a nicety.**

Concretely:

1. **Your plan doc already exists.** `PLAN_storey-matching_REMAINder.md` — ~210 lines. **Do not write a new plan doc.** Do not expand this one beyond its progress log. If it passes ~1,000 lines, close it and open the next remainder.
2. **Never read `PLAN_storey-matching_implementation.md` in full.** It is 🔒 CLOSED and enormous. Its findings (`F-nn`) and defects (`E-LA-nn`) are cited **by ID only**. If you genuinely need one entry, `grep` for that ID and read the surrounding lines — never the whole file, and never instruct an employee to read it whole.
3. **Monitoring is a Haiku job.** Watching a cluster job, polling `squeue`/`sacct`, tailing a log, waiting on artifacts = **Haiku** (`model: "haiku"`). Sonnet is for work that *produces* something. Opus/Fable is for nothing in this run except your own checkpoint reasoning. Standing user instruction, 2026-07-26: *"pour suivre des simulations utilise des agents moins cher comme Haiku."*
4. **Minimum polling interval 30 minutes.** Prefer event-driven completion (background task notifies on exit) over polling entirely. Never babysit a job in a loop.
5. **Scope every employee dispatch to its task IDs and the files it needs.** "Investigate X" is how you get a 157k-token employee. "Read `layout_assigner.py:392-425`, change *this*, assert *that*, report the ratio" is how you get a 20k one. Name the files. Name the assertions.
6. **One fresh employee per task.** Never resume a prior employee for *new* work — reloading its transcript costs more than a clean start. Only continue an in-flight employee still working its same unreported task.
7. **Do not re-derive what is already measured.** §2 below and the plan's §3 carry the numbers. Re-measuring them to feel confident is pure waste.

## 1. Operating mode

1. **You spawn employees yourself** via the Agent tool. State lives in the plan doc, never in an employee's memory.
2. **You are the manager: you write decisions and audits. You do not write feature code.** Employees write everything under `openubem/`.
3. **🔴 ABSOLUTE — no compute on the Speed login node.** Never `ssh … python …`, never `srun`, nothing blocking. `sbatch` fire-and-forget only, then read the output file. The login node may do `mkdir`, `scp`, `tar`, `squeue`, `sacct` and nothing else. If an employee proposes a login-node run, reject it outright.
4. **Never touch a cluster job belonging to another project.** No cancel, no requeue, no deprioritize.
5. **Never edit a frozen record.** Progress-log and AUDIT entries are historical. Append; never rewrite. Corrections go in a new AUDIT block naming what they supersede. Never edit OVERVIEW/DESIGN docs, root `main.py`, or `MEMORY.md`. No `.py` under `docs/` — **except** `storey-Matching\scripts\`, which the user explicitly authorised as an archive of non-import copies.
6. **Git is handled externally. Never commit, never offer to.**
7. `./.venv/Scripts/python.exe` — plain `python` is not on PATH.
8. **Employees must not stop and "wait" for a background job.** Nothing wakes them. Tell every employee in its dispatch: *block on the artifacts appearing on disk, polled inside your own turn; a 0-byte log is a healthy buffered job, not a dead one.* This stalled four employees in a row in the predecessor arc.

## 2. 🔒 Freeze — the four viewers are final

The user has confirmed these render correctly and instructed that **nothing may change about the visualisation**:

```
figures\nyc_suburban_layout_assign_viewer.html
figures\nyc_suburban_layout_assign_pre_B05_pipeline_viewer.html
figures\la_suburban_layout_assign_viewer.html
figures\la_suburban_layout_assign_pre_B05_pipeline_viewer.html
```

Do not regenerate them. Do not re-run `scripts\analysis\enrich_layout_assign_viewers.py`. Do not touch anything under `figures\`, including the three archived pre-edit states (`before_viewer_enrich\`, `before_B05\`, `before_B08b\`). **R07 writes to new filenames only.** A previous change made the buildings disappear from these viewers; the user has not forgotten.

## 3. Read first — and only this

1. `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_REMAINder.md` — **in full.** It is short by design. It is your contract.
2. `openubem/geometry/layout_assigner.py` — specifically `compute_band_map()` (~392-425) and `match_storeys()` (~490-525). **Verify the line numbers; the file moves.**
3. `docs/PROJECT_CHECKLIST.md`, Arc L block — the user's monitoring surface. Keep it current.

That is the whole reading list. Everything else is fetched by ID, on demand, in the smallest slice that answers the question.

## 4. State at handoff (2026-07-26)

**Signed:** CP-A, CP-B (with the identity-guarantee amendment: not bit-identity of coordinates, but *numerically identical scaling factors, geometry identical up to a rigid XY translation, energy verified null*).
**Complete:** Phase A, A-bis, B01–B08b, C01 (run + audited).
**Blocked:** C02 / R06 — go **WITHHELD** on two independent grounds, R01 and R04.
**Open defects carried in:** E-LA-21, E-LA-22, E-LA-23, E-LA-24, E-LA-32, E-LA-33, E-LA-35.

### 4.1 Two facts that are load-bearing and easy to get wrong

**(a) The `ZoneGroup` scope.** Exactly **one** file in the pinned library `00.BaselineBuildings_NUs_v231` (`openubem/config.py:52`) contains a `ZoneGroup`: `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf`, line 2538, `ZoneGroup, Middle Floors, Mid Floor List, 8;`. **`ApartmentMidRise` has none.** The E-LA-35 diagnosis originally claimed a `ZoneGroup … 2` for MidRise; that line does not exist on disk, and the manager corrected it before it could drive a fix. This matters because `MidriseApartment` is **2,262 of the 2,932** buildings in the two inspected cells plus the fallback target for 718 unmapped ones — so a wrong scope here is expensive in *either* direction. HighRise is genuinely inflated. MidRise is genuinely not; its 3/4 area disagreement is **E-LA-25 registry staleness**, a different defect.

**(b) Storey matching is inert almost everywhere, and invisible where it applies.** `match_storeys()` returns `fallback_shorter` for **every** `n_real < n_proto`, and `fallback_not_expressible` for `n_proto == 2` and `n_proto >= 4`. Measured: **81.6%** of `nyc_suburban` and **98.4%** of `la_suburban` are inert. Where it *does* apply, D3(a) chose EnergyPlus `Zone Multiplier`, which **writes no vertex** — rendered height is prototype-native and invariant to `num_floors` (F-12, n = 2,932). Both statements are measured, not inferred. Do not let an employee "fix" either by scaling Z.

### 4.2 Reference numbers (do not re-derive)

- T19 fleet: **97.92%** success (7,990 / 8,160); median `total_eui` **103.8 kWh/m²/yr**. T17 was 96.65%.
- Adopted project baseline: **158.0 kWh/m²** fleet-weighted (`phaseE_elevrb`).
- Harvests `t17_*`/`t18_*`/`t19_*` under `openubem/outputs/comparisons/` are **read-only — never overwrite**.

## 4-bis. ⚠️ First thing you do: check whether P1 already ran

**An employee was dispatched for R01+R02+R03 on 2026-07-26 and had not reported when the previous
session ended.** Before you dispatch P1, follow the check in the plan's **§4-bis**: read §5's
progress log, then `git diff openubem/geometry/layout_assigner.py`. If the work landed, **audit it
instead of re-running it**. If the code is partially changed with no log entry, the employee died
mid-task — read the diff and decide finish-or-revert explicitly, in writing.

Do not skip this. Two runs racing on the same files has happened twice on this project.

---

## 5. Execution sequence

| Phase | Who | What |
|---|---|---|
| **P0** | Director | Read §3's three items. Verify the two §4.1 facts against the code and the library — cheaply, with `grep`, not a survey employee. |
| **P1** | 1 Sonnet employee | **R01 + R02 + R03** in one dispatch — they are three small, related carve-outs in the same file and the same defect family. Do **not** split them into three employees; that triples the context load for no benefit. |
| **P2** | 1 Sonnet employee | **R05** — C01-bis, with the denominator fixed to the multiplier-aware `eio` Zone Information total. |
| **P3** | Director | **🔶 CP-D.** Audit P1+P2. Binding: no fleet run before it. **It is now the only gate on R06.** |
| ~~P4~~ | — | ~~R04 decision~~ — ✅ **already made 2026-07-26, option (a).** See §6. Skip. |
| **P5** | 1 Sonnet employee + 1 Haiku monitor | **R06** — the 12-cell / 8,160-building fleet run, `sbatch --array`, fire-and-forget. Sonnet generates and submits `t20_*`; **Haiku watches and reports completion**; Sonnet harvests. |
| **P6** | 1 Sonnet employee | **R09** — the five `layout_assign_vs_modes_*` figures on the T20 harvest. (**R07 is reduced** to a written statement folded into R08 — its quantities were already measured by B08a/B08b and the viewers are user-confirmed. Reinstate it only if R06 changes geometry.) |
| **P7** | Director | **R08** documentation closure, then **🔶 CP-E**. Write the completion report, update `PROJECT_CHECKLIST.md` §L. |

**That is 4 employees for the whole remainder.** If you find yourself dispatching a fifth, ask whether you are investigating something already measured.

**Critical path:** R01+R02+R03 → R05 → **CP-D** → R06 (~15 h cluster) → R09 → R08 → **CP-E**. Nothing else is in the way.

**Every employee dispatch must carry:** the plan path, its exact task IDs, the plan's §1 hard rules, the instruction to append its own §5 progress-log entry, the artifacts-on-disk waiting rule from §1.8, and this line verbatim — *"if the plan is ambiguous or conflicts with the code, STOP and report the conflict to the director; never invent a plan-violating workaround."* Tell every employee that `eplusout.err` is the only ground truth for a simulation outcome, quoted verbatim, never the `.end` file.

## 6. The R04 decision — ✅ **ALREADY MADE 2026-07-26. Do not reopen it.**

> **Decided: option (a) — accept the limit and document it.** `layout_assign` ships as a mode that
> matches **thermal-zone topology and plate geometry**, not building height. The full rationale is
> written into the plan's R04 entry; read it there, do not re-derive it.
>
> **(b) was rejected** because extending `match_storeys()` raises how often the multiplier *applies*
> while doing nothing about the thing that looked wrong — storeys stay invisible in geometry either
> way. It buys reach, not correctness, and pays for it by perturbing the thermal model of the 82–98%
> of buildings currently untouched and running clean.
>
> **(c) was rejected** because the mode runs at 97.92% and delivers real zone-count fidelity.
>
> **What it obliges you to do:** R08's disclosure list must be **headline text, not a footnote**. If
> a reader can come away believing `layout_assign` reproduces real building heights, this decision
> was executed wrongly. That is the whole price of option (a) and it is your job to pay it.
>
> **R06's only remaining gate is CP-D** (R01/R02/R05 green).

**The original framing is kept below for the record only.**

**The question:** does this arc need a *geometric* storey mechanism at all, or does it ship with a documented limit?

The evidence is in §4.1(b) and it is not ambiguous. On the only two cells anyone has inspected visually, storey matching does nothing for 82–98% of buildings, and where it acts it is invisible in geometry by construction. A fleet EUI table published as "the storey-matched fleet result" would therefore be dominated by unmatched buildings and would **overstate the fix's reach**. That is why R06 is gated on this decision rather than the other way round.

Your live options:

- **(a) Accept and document the limit.** `layout_assign` ships as a mode that matches zone topology and plate geometry, not building height. Cheapest, and defensible *if* R08's disclosure list is written plainly rather than buried.
- **(b) Extend `match_storeys()`** to `n_proto ∈ {2, 4+}` and to the shorter case. Largest reach, largest risk, and it does not make storeys visible — it only makes the multiplier apply more often.
- **(c) Park the mode.**

**🔴 What is not on the table:** scaling Z to `num_floors`. That abandons D3(a) for a mechanism this arc explicitly rejected, changes the thermal model, and voids B02's identity guard. If an employee proposes it, reject it and log the rejection.

Decide it, write the rationale into the plan's §5 as an AUDIT entry, and only then authorise R06.

## 7. Hard stops — report and halt the affected line of work

- Fleet success rate comes back **below T19's 97.92%** for any reason not already mapped to a known defect ID.
- Any **CTF Fatal** reappears on the E-LA-20 engaged population. Halt; do **not** re-tune `T_ENGAGE = 0.868 m` / `T_MASS_MAX = 0.35 m` — they are FROZEN, and a fleet failure reopens the fix plan, not the constants.
- An employee reports it cannot distinguish a real failure from a harness failure. That ambiguity killed two tasks in the predecessor arc; treat it as a stop, not a footnote.
- Anything under `figures\` shows a modified mtime. The freeze has been breached — stop and report before doing anything else.

## 8. What "done" looks like

CP-E signed, with: R01–R03 green and their measured ratios reported; R05's reconciliation with its residual explained; R04 decided in writing; R06's fleet numbers reported **whether or not F-08's heating ratio moved toward 1.0** — a fix that does not move it is a finding, not a failure to be reframed; R07's panel stating in text that height is out of scope; R09's five figures with their harvest provenance labelled per side; and R08's disclosure list written plainly.

And one sentence that survives all of it, unless someone actually measures against metered data: **`layout_assign`'s energy output has never been validated against measured data at any scale.** A greener success chart is not validation.
