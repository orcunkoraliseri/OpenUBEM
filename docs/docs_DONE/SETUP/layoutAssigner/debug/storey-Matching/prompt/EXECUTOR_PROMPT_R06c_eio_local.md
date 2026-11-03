# Executor prompt — R06c (`eio`-true local measurement: CP-D conditions (a) and (c))

> Written by the director 2026-08-04, immediately after the R06 audit. Dispatch a **fresh Sonnet**.
> Runs in parallel with R09; the two touch disjoint files.

---

Working directory `C:\Users\o_iseri\Desktop\OpenUBEM`. Read, in this order:

1. §1 (hard rules) and §3 task **R06c** of
   `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_REMAINder.md`
2. The **AUDIT — R06** entry at the end of §5 of that same doc (it is the last entry; it defines
   exactly why this task exists).
3. The `R06` progress-log entry immediately above it — specifically its **items 3, 4 and 7**.
4. The **AUDIT — CP-D** entry, §5 "Conditions carried into R06", conditions (a) and (c).

Do **not** read `PLAN_storey-matching_implementation.md` (CLOSED, ~3,500 lines). Grep it by
`F-nn` / `E-LA-nn` ID and read only the surrounding lines.

## 🔴 Absolute rules

- **NEVER run compute on the Speed login node**, and **do not use the cluster at all for this task.**
  This task is deliberately **local**: the whole point is that the cluster's shared sbatch template
  (`scripts/cluster/submit_fleet_t08.sbatch:63`) deletes `*.eio`, so cluster output can never answer
  it. **Do not re-submit the fleet.** Do not modify `submit_fleet_t08.sbatch`.
- **Never `git commit`.** Never edit root `main.py`, any OVERVIEW or DESIGN doc, or `MEMORY.md`.
- **🔒 Frozen:** everything under `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\figures\`;
  the `t17_*`/`t18_*`/`t19_*` harvests; the T20 harvest CSVs already in
  `openubem/outputs/comparisons/` (read-only inputs — do not regenerate them).
- Frozen constants: `T_ENGAGE = 0.868`, `T_MASS_MAX = 0.35`. A bad result reopens the fix plan,
  never the constants.
- Interpreter: `./.venv/Scripts/python.exe`.
- Progress-log entries are **append-only**; never rewrite a frozen entry.
- Another employee is running **R09** concurrently and appends to the same §5. Append your entry in
  one edit at the very end of the file, and re-read the tail immediately before writing.

## What to do

### Part 1 — CP-D condition (a): F-08's heating ratio, on an `eio`-true denominator 🔴 the binding one

1. Pick the measurement pair from `openubem/outputs/comparisons/t20_r10_reach_change.csv`
   (7,442 rows). **At least one side must have `new_status == "applied"` with
   `new_multiplier >= 2`.** 503 buildings qualify as the `applied` side.
2. Regenerate those buildings' IDFs locally through the real pipeline and run EnergyPlus **locally**,
   with the `.eio` **retained** — same method R05 used for its 7-case local regression. Reuse R05's
   local-run harness if it still exists rather than writing a new one.
3. Compute the heating ratio with the heating denominator taken from the **multiplier-aware total
   floor area parsed out of `eplusout.eio`**. Never a nominal `footprint × num_floors`. Never the
   `.end` file.
4. **Report the value whether or not it moves toward 1.0.**

**The trap, stated plainly:** R05's attempt produced `1.0000×` because both sides of its pair
collapsed onto the same code path — a file compared with itself. That is an identity, not a
measurement, and the CP-D audit ruled it vacuous. Before you report a ratio, **prove the two sides
genuinely differ**: state each side's `status` and `multiplier`, and show they are not the same
generated IDF. **If no qualifying pair exists in the fleet, say so explicitly and stop Part 1** — do
not substitute a degenerate pair.

### Part 2 — CP-D condition (c): the denominator assertion

For every building you run locally with status `applied`, assert

```
eio total floor area  ==  footprint × num_floors     (within a stated tolerance)
```

and report any population that fails, with the numbers. This is a **local, single-digit-N** check,
not a fleet-scale one — the audit already accepted that fleet scale is impossible here. State the N.

### Part 3 — F-11 population reconciliation and item-4 restatement

Three different numbers are in circulation for F-11's population and they must be reconciled:

- **805** — F-11's original manager-verified estimate.
- **698** — the row count of `scratchpad/f11_transformer_check_v3.csv`, the file R06 cites.
- **439** — the figure R06's entry actually reports (`LargeOffice` 170, `MediumOffice` 231,
  `HighriseApartment` 29, `SecondarySchool` 7, `Hospital` 1, `PrimarySchool` 1).

Determine what filter takes 698 → 439, state it in one sentence, and say which of the three is the
real F-11 population. Then **restate item 4's `MediumOffice` multiplier split so a reader can
reproduce it from a named file.** The director's own recomputation of the full 698-row file gives:

```
multiplier 2–7   n=114   overloaded 0     (0.0 %)
multiplier ≥8    n=117   overloaded 117   (100 %)
fleet-wide: 117 overloads, ALL MediumOffice
```

against the entry's `0/125` and `107/107`. Also note the entry's own arithmetic does not close
(125 + 107 = 232 ≠ its `MediumOffice` 231).

**The conclusion is already signed and is not up for revision** — 0 % transformer overload at every
residual multiplier ≤ 7, 100 % at every multiplier ≥ 8, a perfectly deterministic cliff; D9's
conservative bound holds through 7 and fails at 8. **Only the counts are in question.** Produce the
pair of numbers R08 should print, and name the file they come from.

## Evidence rules (these are why this task exists)

- Ground truth is raw `eplusout.err` (run outcome) and `eplusout.eio` (multiplier-aware floor area).
  **Never** the `.end` file. **Never** a nominal `footprint × num_floors` presented as `eio`-derived.
- **Every reported quantity must be traceable to a file path that exists on disk when you write your
  entry.** A previous harness in this arc shipped a CSV whose `eio` columns were all `0.0` while its
  report cited them as proof; R06's own item 4 cited a file its numbers do not reproduce from. Do
  not add a third instance.
- Do **not** use the harvest's `has_fatal` column — it is `False` on all 8,160 rows including the 7
  that really did fatal (registered as **E-LA-39**). Use `status` and raw `.err`.
- If you cannot distinguish a **real** simulation failure from a **harness** failure, **STOP and
  report.** That ambiguity is a hard stop, not something to resolve by judgement.

## Deliverable

Append **one** `R06c` progress-log entry to §5 (Artifacts / Deviations / Test status / Notes)
carrying Parts 1, 2 and 3, then report back. **Do not start R08 or R09** — R09 is already running
under another employee, and R08 is dispatched after both land.
