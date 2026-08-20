# MEASUREMENT — OPEN-29 defect-status re-trace at HEAD, 2026-08-18

**Slug:** `open-29_status-retrace` · **Date:** 2026-08-18 · **Register item:** OPEN-29
**Task:** T04 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`. **Measurement only — no
production code changed.** The register was NOT edited by this task (director-only edit this pass,
per the task's own constraints); the required amendment is drafted in §5 below.
**Script:** `scripts/analysis/open29_status_retrace_2026-08-18.py`
**Output CSV:** `openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv` (new file —
the 2026-08-06 `open29_defect_status_trace.csv` is untouched, mtime confirmed unchanged at
`2026-08-05 20:05`).

---

## 1. Step 1 — hard gate: E-LA-20 method control, run blind through the procedure

Per §6-T04 step 1, the control must be re-run, not inherited. The control is E-LA-20 — not a
candidate — run through the same forward-citation procedure used on the 13 real rows: start from its
defining site, follow every later document that mentions it, and record the status of the
*latest*-dated one.

**Defining site:** `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/PLAN_e-la-20_investigation.md:3,7`
(2026-07-24) — logged as *"candidate E-LA-20"*, a CTF calculation-convergence Fatal.

**Forward chain (all documents mentioning E-LA-20 were enumerated; see command below):**
`PLAN_e-la-20_investigation.md` (2026-07-24) → `COMPLETION_REPORT_e-la-20-investigation.md` →
`DONE-PLAN_e-la-20_multilayer-fix.md` (2026-07-25, CP-C SIGNED) → later mentions in
`MEASUREMENT_open-05_defect-id-sweep.md`, `MEASUREMENT_open-29_defect-status-trace.md` (2026-08-06),
`PLAN_no-compute-queue.md`, `PLAN_compute-queue.md`, and the register itself (multiple lines through
2026-08-18) — **none of which contradicts or revises the 2026-07-25 status.**

**Script output, quoted verbatim:**

```
=== STEP 1 (hard gate): E-LA-20 method control, run blind through the procedure ===
  docs\docs_DONE\SETUP\layoutAssigner\DONE\e-la-20\DONE-PLAN_e-la-20_multilayer-fix.md:68
  - [x] 🔶 **CP-C** — final checkpoint: E-LA-20 dispositioned — ✅ **SIGNED 2026-07-25. E-LA-20 CLOSED: fixed and verified at its entire reachable population (150/150 PASS, 0 CTF Fatal, manager-grepped).** Forwarded open, none blocking: E-LA-21, E-LA-22, E-LA-23, E-LA-24. **This arc is complete.**
  PASS -- control reproduces FIXED, verified 150/150.
```

**GATE PASSED.** The procedure lands on `FIXED, verified 150/150` at
`docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:68`, exactly as
required. The rest of this task proceeds.

Command used to enumerate the forward chain: `grep -rln "E-LA-20" docs/ scripts/`.

---

## 2. Step 3 — E-LA-21 re-checked against HEAD's parser, live off the filesystem

Per §6-T04 step 3: does `has_fatal` still test only the one-space `** Fatal **` form? The register
says it is demonstrated wrong on `way/401910463` (2026-08-06) and separately claims R06 (2026-08-09)
and a malformed-variant sweep (2026-08-12) fixed it repo-wide. Checked live, not from either
document's claim.

**Script output, quoted verbatim (7 harvest sites checked):**

```
=== STEP 3: E-LA-21 -- does has_fatal still test only the one-space form, at HEAD? ===
  scripts/cluster/t20_harvest_layout_assign.py:260: has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None  [regex/other form]
  scripts/cluster/t08_harvest_results.py:246: has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None  [regex/other form]
  scripts/cluster/t07_harvest_results.py:199: has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None  [regex/other form]
  scripts/cluster/t07b_run_auto_refit_local.py:330: has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None  [regex/other form]
  scripts/cluster/t17_harvest_layout_assign.py:255: has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None  [regex/other form]
  scripts/cluster/t18_harvest_layout_assign.py:252: has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None  [regex/other form]
  scripts/cluster/t08_local_remainder.py:431: has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None  [regex/other form]
  RESULT: no harvest script tests only the one-space literal at HEAD.
  E-LA-21's own defect (has_fatal, one-space) is FIXED at HEAD across all 7 sites checked (R06, 2026-08-09; confirmed unchanged since).
```

A supplementary sweep for any *bare* one-space literal anywhere in the tree:

```
$ grep -rn '"\*\* Fatal \*\*"' scripts/ openubem/
openubem/outputs/comparisons/open29_defect_status_trace.csv:12: ...(only inside the 2026-08-06 CSV's own text field, not code)
```

**CONFIRMED: at HEAD, `has_fatal` does NOT still test only the one-space form.** All 7 sites named in
the register's "six live sites" plus `t08_local_remainder.py` (the fifth occurrence, fixed separately
by C07) use `re.search(r"\*\*\s+Fatal\s+\*\*", err)`, matching both the one-space and two-space
variants. The only surviving one-space literal in the whole tree is a text value inside the
2026-08-06 CSV itself — historical data, not live code. **The register's claim (R06 done 2026-08-09,
malformed-variant sweep done 2026-08-12) is confirmed at HEAD, five-plus days later, with no
regression.**

This is why **E-LA-21's row below moves from STILL-OPEN to CLOSED-ELSEWHERE** — the single largest
change in the 13-row trace.

---

## 3. Full 13-row re-trace

The 2026-08-06 trace (`open29_defect_status_trace.csv`) was re-run for every row, following citations
**forward to the latest document that mentions each ID**, including documents written since
2026-08-06: this arc's own register (as amended through 2026-08-18), its plan docs under
`implemenation/` (`PLAN_five-more-items-2026-08-13.md`, `PLAN_five-items-2026-08-18.md`, this plan),
and its `extra/` reports — most importantly `extra/MEASUREMENT_open-29_eight-defect-recheck.md`
(2026-08-13, T05 of `PLAN_five-more-items-2026-08-13.md`), a full intermediate re-trace of 8 of the 13
rows that this task had not previously been told about and found by grepping for later `extra/`
documents that name OPEN-29.

Full output: `openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv` (13 rows, 9
columns, `changed_since_2026-08-06` added). Summary below; every claim carries a `path:line` in the
CSV's own columns.

| ID | 2026-08-06 bucket | 2026-08-18 bucket | Changed? |
|---|---|---|---|
| E-LA-06 (warmup half) | SUPERSEDED | SUPERSEDED | No |
| E-LA-06 (flow-balance half) | STILL-OPEN | STILL-OPEN | No |
| E-LA-11 | CLOSED-ELSEWHERE | CLOSED-ELSEWHERE | No |
| E-LA-12 | CLOSED-ELSEWHERE | CLOSED-ELSEWHERE | No |
| E-LA-13 | CLOSED-ELSEWHERE | CLOSED-ELSEWHERE | No |
| E-LA-15 | STILL-OPEN | STILL-OPEN | No |
| **E-LA-16** | STILL-OPEN | STILL-OPEN | **Citation only** — see §4 |
| E-LA-17 | STILL-OPEN | STILL-OPEN | No |
| E-LA-18 | STILL-OPEN | STILL-OPEN | No (citation refreshed) |
| E-LA-19 | STILL-OPEN | STILL-OPEN | No (citation refreshed) |
| **E-LA-21** | STILL-OPEN | **CLOSED-ELSEWHERE** | **Yes — the one status change** |
| E-LA-30 | STILL-OPEN | STILL-OPEN | No |
| E-LA-33 | STILL-OPEN | STILL-OPEN | No |

**New bucket counts (2026-08-18): CLOSED-ELSEWHERE 4, STILL-OPEN 8, SUPERSEDED 1 — 13 rows / 12 IDs,
unchanged from 2026-08-06.**
**Old bucket counts (2026-08-06): CLOSED-ELSEWHERE 3, STILL-OPEN 9, SUPERSEDED 1.**

**Only one row's bucket changed: E-LA-21**, STILL-OPEN → CLOSED-ELSEWHERE, confirmed live at HEAD in
§2 above (not merely cited from the register). This is the exact reduction the register's own R06
completion note (2026-08-09) already announced — *"eight other defect IDs remain live"* — and this
task independently re-derives that it still holds nine days later, rather than taking the register's
word for it.

For every other row, `git log --since=2026-08-13` on the cited mechanism's file was checked in
addition to a fresh `grep`/`read` of the citation, and returned nothing except the one E-LA-16
comment-only commit (`b2d0220`, 2026-08-18) discussed next. **No other defect changed status.**

---

## 4. E-LA-16 — the one row that needed unpacking, not the one the task brief assumed

The task brief supplied as a hypothesis: *"one candidate (`E-LA-16`) provably closed — OPEN-51
adjudicated it and retired 2026-08-18."* **This was checked, not taken on trust, and it is imprecise
in a way that matters.**

**What OPEN-51 actually closed.** OPEN-51 was a register item asking a narrower question: two
documents use the ID `E-LA-16` for two different failure signatures (cooling-coil/cooling-tower-UA
autosize failure per its own defining text, vs. the `CheckWarmupConvergence` lineage per a later code
comment) — *which reading is correct?* OPEN-51 adjudicated that question on 2026-08-18: the
defining-text reading (cooling-coil-UA family) is correct, corroborated on raw `.err` evidence for
the three named buildings in the current E02 harvest (23/21/16 Severes). **The register's own text
says explicitly: `"OPEN-29 — no change... this item resolves the question they deliberately left
open"`** (`INVESTIGATION_open-items-register.md:5222-5226`).

**What OPEN-51 did NOT close: the E-LA-16 defect itself.** Verified live at HEAD:

```
$ grep -rn "cooling.coil.UA|CoolingCoilUA|cooling.tower.UA|cooling coil design UA" openubem/ scripts/ --include=*.py
openubem/geometry/layout_assigner.py:867:# unrelated mechanism, cooling-coil/cooling-tower-UA-autosize failure, not
```

That one hit is inside a **comment**, and it is the OPEN-51 correction itself:

```
openubem/geometry/layout_assigner.py:866-868
# (E-LA-16 removed from this list 2026-08-18 -- it names a different,
# unrelated mechanism, cooling-coil/cooling-tower-UA-autosize failure, not
# CheckWarmupConvergence/CheckAirLoopFlowBalance. See
# docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-51_e-la-16-identity.md.)
```

`git log -p --since="2026-08-13" -- openubem/geometry/layout_assigner.py` shows this comment edit is
the **only** change to the file in that window (commit `b2d0220`, 2026-08-18). No code anywhere
handles the cooling-coil-UA-autosize mechanism; nothing in `openubem/` or `scripts/` was patched.

**Conclusion: E-LA-16's bucket is unchanged — STILL-OPEN.** What changed on 2026-08-18 is which
register ID (`OPEN-51`) is retired and which citation the CSV should carry for E-LA-16, not whether
the underlying defect is fixed. The `changed_since_2026-08-06` column for this row reads *"Citation
only (identity resolved by OPEN-51); bucket unchanged"* rather than "Yes" — a genuine status change
would have moved the bucket, and this did not.

---

## 5. Register amendment to apply

*(Per this task's constraints, the register is not edited directly — another executor amends it
concurrently. The following is the exact strike-and-correct text for the director to place.)*

### §1 summary table row — `OPEN-29`

**Current text** (`INVESTIGATION_open-items-register.md:663`):

> `| OPEN-29 | **Defects last recorded OPEN that this register never adopted** — **measured: 9 of 12
> are genuinely still open**, now tracked inside this item. **2026-08-12: the malformed-fatal-test
> class R06 left behind is finished**... **The item stays open — the other eight defect IDs are
> untouched.** | Register hygiene | 9 defects; ~~E-LA-21 replicated across **4** harvest scripts~~ **7
> known fatal-test sites in total** | ✅ **measured; fatal-test class now closed on live code** |`

**Apply:** strike `**measured: 9 of 12 are genuinely still open**` and `9 defects` in the third
column; insert the correction after each, dated 2026-08-18:

> `| OPEN-29 | **Defects last recorded OPEN that this register never adopted** — ~~**measured: 9 of 12
> are genuinely still open**~~ **re-derived 2026-08-18: 8 of 12 IDs (13 rows) genuinely still open —
> E-LA-21 moved to CLOSED-ELSEWHERE, confirmed FIXED at HEAD across all 7 harvest sites (R06,
> 2026-08-09; still holding 2026-08-18)**, now tracked inside this item. **2026-08-12: the
> malformed-fatal-test class R06 left behind is finished**... **2026-08-18: E-LA-16's naming
> ambiguity (which of two readings is correct) adjudicated by OPEN-51 — the defect itself (bucket:
> STILL-OPEN) is unaffected; only its citation changed.** **The item stays open — seven other defect
> IDs are untouched (was eight; E-LA-21 now discharged from this count too since R06's own 2026-08-09
> note already removed it).** | Register hygiene | ~~9 defects~~ **8 defects (12 IDs, 13 rows —
> unchanged population; only the STILL-OPEN/CLOSED-ELSEWHERE split moved)**; ~~E-LA-21 replicated
> across **4** harvest scripts~~ **7 known fatal-test sites in total, all fixed and reconfirmed at
> HEAD 2026-08-18** | ✅ **measured; fatal-test class now closed on live code**; ✅ **2026-08-18:
> full 13-row re-trace, evidence `extra/MEASUREMENT_open-29_status-retrace.md` +
> `openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv`** |`

### §-section — `### OPEN-29`

**Current text** (`INVESTIGATION_open-items-register.md:1804-1809`, the bucket table):

> `| **CLOSED-ELSEWHERE** | 3 | E-LA-11, E-LA-12, E-LA-13 — all closed at the structural-fixes CP-B/CP-C
> (2026-07-23), reconfirmed 2026-07-25 |`
> `| **STILL-OPEN** | 9 | E-LA-06 *(flow-balance half)*, E-LA-15, E-LA-16, E-LA-17, E-LA-18, E-LA-19,
> E-LA-21, E-LA-30, E-LA-33 |`
> `| **SUPERSEDED** | 1 | E-LA-06 *(warmup half)* → folded into the E-LA-14/16/18/19/23 lineage |`
> `| **NO-STATUS-EVER** | 0 | — |`
> `*(13 rows / 12 IDs — E-LA-06 splits across two buckets, which is why it appears twice.)*`

**Apply:** strike the CLOSED-ELSEWHERE and STILL-OPEN counts/lists, insert the 2026-08-18 correction:

> `| **CLOSED-ELSEWHERE** | ~~3~~ **4 (2026-08-18)** | E-LA-11, E-LA-12, E-LA-13 — all closed at the
> structural-fixes CP-B/CP-C (2026-07-23), reconfirmed 2026-07-25; **+ E-LA-21 — R06 fixed it
> repo-wide 2026-08-09, re-confirmed live at HEAD across all 7 harvest sites 2026-08-18, see
> `extra/MEASUREMENT_open-29_status-retrace.md` §2** |`
> `| **STILL-OPEN** | ~~9~~ **8 (2026-08-18)** | E-LA-06 *(flow-balance half)*, E-LA-15, ~~E-LA-16~~
> **E-LA-16 (bucket unchanged; naming ambiguity adjudicated by OPEN-51 2026-08-18 — defect itself
> still unpatched, see `extra/MEASUREMENT_open-29_status-retrace.md` §4)**, E-LA-17, E-LA-18, E-LA-19,
> ~~E-LA-21~~ **(E-LA-21 removed — see CLOSED-ELSEWHERE row)**, E-LA-30, E-LA-33 |`
> `| **SUPERSEDED** | 1 | E-LA-06 *(warmup half)* → folded into the E-LA-14/16/18/19/23 lineage |`
> `| **NO-STATUS-EVER** | 0 | — |`
> `*(13 rows / 12 IDs — E-LA-06 splits across two buckets, which is why it appears twice. Unchanged
> from 2026-08-06/08-12; only the CLOSED-ELSEWHERE/STILL-OPEN split moved.)*`

Also insert, immediately after that table, a dated note (this is new text, not a strike):

> **Amended 2026-08-18 (T04 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`).** Full
> 13-row re-trace at HEAD. One bucket change: **E-LA-21** moves STILL-OPEN → CLOSED-ELSEWHERE,
> confirmed live (not cited from a document) across all 7 harvest sites — no one-space `has_fatal`
> literal survives anywhere under `scripts/` or `openubem/`. **E-LA-16's row is unchanged**
> (STILL-OPEN) — OPEN-51 (closed the same day) adjudicated only which of two readings the ID names;
> the cooling-coil-UA-autosize mechanism itself remains unpatched in production code, confirmed by
> `git log -p --since=2026-08-13` showing only a comment-text change. **Recommendation, not a
> closure: none of the remaining 7 STILL-OPEN entries (E-LA-06 flow-balance, E-LA-15/16/17/18/19/30/33)
> should be opened as new register items by this task** — per §6-T04's own instruction, this is the
> director's call. Evidence: `extra/MEASUREMENT_open-29_status-retrace.md`,
> `openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv`.

---

## 6. What this task does not do

Per §2 rule 8 (measure-only) and §6-T04 step 6: no register item was opened for any of the 7 IDs
still found STILL-OPEN. No production code was touched — `git status`/`git diff` after this task
shows no changes under `openubem/` or `scripts/cluster/`, `scripts/diagnostics/`,
`scripts/validation/`. The only files this task authored are the three named in its authorisation:
the script, this document, and the new dated CSV. The pre-existing
`openubem/outputs/comparisons/open29_defect_status_trace.csv` (2026-08-06) is untouched — confirmed
by mtime (`2026-08-05 20:05`, unchanged before and after this task ran) and by row count (14 lines,
identical).
