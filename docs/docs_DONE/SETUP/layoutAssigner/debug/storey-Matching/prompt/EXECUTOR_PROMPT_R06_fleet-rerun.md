# Executor prompt — R06 (T20 fleet re-run)

> **Pre-drafted by the director 2026-07-26, held until CP-D is signed.** Do not dispatch before the
> CP-D AUDIT entry in §5 of the plan reads SIGNED. Sonnet employee, fresh session.

---

Read `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_REMAINder.md`,
§1 (hard rules), §3 task **R06**, and the §5 progress-log entries for R01, R02, R03, R10, R05.
Do **not** read `PLAN_storey-matching_implementation.md` — it is CLOSED and ~3,500 lines. If you need a
finding by ID (`F-nn`, `E-LA-nn`), grep for the ID and read only the surrounding lines.

Execute **R06 only**. Do not touch R08 or R09.

## 🔴 Absolute rules — violating any of these is a hard stop

- **Never run compute on the Speed login node** (`speed-submit2` / `speed.encs.concordia.ca`). No
  `srun`, no `ssh … python …`, nothing blocking. **`sbatch --array` fire-and-forget only**, then read
  the output file afterwards. The login node may only do `mkdir`, `scp`, `tar`, `squeue`, `sacct`.
  If a step needs Python remotely, wrap it in an sbatch script.
- **Never cancel, requeue, or deprioritise a cluster job that is not part of this project.**
- **Never `git commit`** — git is handled externally.
- **🔒 FROZEN — do not modify, regenerate, or change the mtime of** anything under
  `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\figures\`, including the four `*_viewer.html`
  files and the archives `before_viewer_enrich\`, `before_B05\`, `before_B08b\`. Do not re-run
  `scripts\analysis\enrich_layout_assign_viewers.py`. R06 produces **no figures**.
- **Do not touch** the `t17_*` / `t18_*` / `t19_*` harvests under `openubem\outputs\comparisons\` —
  read-only. T20 goes to **fresh** `t20_*` paths.
- **Frozen constants:** `openubem\idf\opaque_assembly.py`'s `T_ENGAGE = 0.868` and
  `T_MASS_MAX = 0.35`. A fleet failure reopens the fix plan, never these numbers.
- **🔴 Not on the table:** scaling Z to `num_floors`. That abandons D3(a). If you find yourself
  wanting it, STOP and report instead.
- Interpreter is `./.venv/Scripts/python.exe` — plain `python` is not on PATH.
- Progress-log entries are **append-only**. Never rewrite a frozen entry.

## What to do

1. Generate the T20 job set for the full **12-cell / 8,160-building** fleet on current `main`
   (i.e. with R01/R02/R03/R10 landed). Submit with `sbatch --array`, fire-and-forget.
2. **Block on artifacts on disk, not on a monitor.** Do not stop and "wait to be woken" — poll the
   harvest directory / `sacct` at an interval of **no less than 30 minutes**, and keep working
   through the reporting checklist as results land.
3. Harvest to fresh `t20_*` paths and report the measurements below.

## What you must report — all five, none optional

1. **Fleet success rate**, against T19's **97.92 %** (7,990/8,160) and median `total_eui`
   **103.8 kWh/m²/yr**. Ground truth for a run outcome is **`eplusout.err`** — never the `.end` file.
2. **Every remaining failure mapped to a known defect ID.** An unmapped failure is a finding, not
   noise. Report the count and a representative `eplusout.err` excerpt per distinct cause.
3. **F-08's heating ratio, re-measured on the `eio`-true denominator** (per R02/R05 — the nominal
   denominator is known-wrong). Report it **whether or not it moves toward 1.0.** A fix that does not
   move it is a reportable result, not a failure to hide.
   **🔴 The pair you measure on must have at least one side with status `applied` and a residual
   multiplier ≥ 2.** R05's pair collapsed onto a single code path and produced a tautological
   1.0000× — see the CP-D audit, §2. A ratio between a file and itself measures nothing. If no such
   pair exists in the fleet, say so explicitly; do not substitute a degenerate pair.
4. **D9 `transformer_scale_ratio` across the multiplier range** — (i) Severe counts and (ii) the
   transformer's energy effect on the **805 exposed buildings of F-11**. D9 is a conservative upper
   bound validated at exactly one multiplier (4); R06 is where that gets tested at the others.
5. **E-LA-36 regression check:** confirm on real T20 output that no building simulates more storeys
   than its `num_floors` — i.e. the `Zone.Multiplier` × `ZoneList` compounding is gone at fleet scale,
   not just in R10's local run.
6. **R10's reach change (CP-D condition (b)).** Count the buildings whose `match_storeys()` status
   **changed** under R10, split by archetype and by old → new status. Exactness means
   `HighriseApartment` now matches only at `n_real ∈ {10, 18, 26, …}` and `MidriseApartment` only at
   even `n_real ≥ 4`; everything else falls back. **The 81.6% / 98.4% inert shares are stale** — your
   number replaces them in R08. This is expected behaviour, not a regression: those buildings were
   previously "applied and silently wrong".
7. **Denominator assertion (CP-D condition (c)).** For every building with status `applied`, assert
   `eio` total floor area == `footprint × num_floors` within tolerance; report any population that
   fails, with counts. Fallback buildings legitimately differ under D3(a) — exclude them from the
   assertion, **not** from the count.

## Evidence rules — read before you build any harness

- **Ground truth is the raw `eplusout.eio` / `eplusout.err`.** If you write a summary CSV, every
  column that carries an `eio`-derived name must actually be parsed from `eio`. R10's harness shipped
  a CSV whose eio columns were all `0.0` and whose `floor_area_m2` was nominal — the fix was right but
  the artifact proved nothing. Do not repeat that. Spot-check your own parser against one raw file by
  hand before trusting it across 8,160.
- Do not reimplement pipeline logic in the harness. Drive the real pipeline; measure its output.

## Framing constraints

- A clean comparison against T19 is **not** available while **E-LA-22** stands. Say so plainly; do not
  present T20−T19 deltas as attributable to this arc.
- If you cannot distinguish a **real** simulation failure from a **harness** failure, STOP and report —
  do not guess. That ambiguity is itself a hard stop.

## Deliverable

Append one **R06** progress-log entry to §5 of the plan doc, in the standard format
(Artifacts / Deviations / Test status / Notes), containing all five reported quantities. Then report
back. Do not proceed to R09.
