# INVESTIGATION — EU-11 ceiling82 backlog wave, failed-simulation classification (snapshot 2026-09-05, updated)

- **Arc / plan**: `implementation/PLAN_eu-82pct-ceiling-2026-09-05.md`. Jobs: `1306951` (London backlog),
  `1306952` (Lyon backlog), `1306953` (Madrid backlog), `1305186` (Bologna backlog), `1308150`/`1308159`/
  `1308160`/`1308161` (Step2-delta remedy waves).
- **Scope**: read-only classification snapshot of every `FAILED` task across the 8 jobs above, current as of
  this file's date. Supersedes `FINDING 252`'s 24-task tally (`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
  line 1851) with 4 more tasks found during harvest-monitoring — same method, no new signature. Self-contained:
  written so an external session does not need to read the ~2,000-line debug-references file to get the full
  current picture.
- **Method** (reuse for any further `FAILED`-count growth): `sacct -j <job> --format=JobID,State -n -X |
  grep -i fail` → new task index → find its log under `/speed-scratch/o_iseri/openubem/fleets/` (filename
  pattern is **not** consistent across submission waves — try
  `openubem_<district>_backlog_<job>_<idx>.log`, then `openubem_<district>_<job>_<idx>.log`, then a targeted
  `ls .../fleets/ | grep _<job>_<idx>.log` if neither guess resolves) → read `Task N: osm_id=<stem>` /
  `OUTDIR:` → classify from `grep -m1 "Fatal  \*\*" <outdir>/eplusout.err` +
  `grep "Last severe error" <outdir>/eplusout.err`. **Never trust `sacct` state alone** — it cannot
  distinguish the four signatures below.

## Current totals (as of this snapshot)

| Job | District | COMPLETED | FAILED | RUNNING | PENDING (not yet instantiated) | Array total |
|---|---|---|---|---|---|---|
| `1306951` | London backlog | 418 | 1 | 0 | 0 | 419 (drained) |
| `1306952` | Lyon backlog | 288 | 1 | 8 | 171 | 469 |
| `1306953` | Madrid backlog | 595 | 12 | 8 | 392 | 1008 |
| `1305186` | Bologna backlog | 479 | 13 | 8 | 699 | 1200 |
| `1308150` | London Step2-delta | 100 | 0 | 1 | 0 | 101 (near-drained) |
| `1308159` | Step2-delta | 38 | 0 | 0 | 0 | 38 (drained) |
| `1308160` | Step2-delta | 166 | 0 | 0 | 0 | 166 (drained) |
| `1308161` | Bologna Step2-delta | 11 | 1 | 0 | ? | ≥12 |

**Total FAILED = 28.** All 28 classify into exactly 4 known signatures — no unclassified fifth signature found.

## Signature breakdown (28/28 accounted for)

| # | Signature | Count | Districts | Status |
|---|---|---|---|---|
| 1 | `RoofCeiling:Detailed ... Vertex size mismatch` (`FINDING 210`) | 15 | Madrid 7, Bologna 6, London 1, Lyon 1 | **Accepted, no action** — known GEOS-build floating-point fragility (`intersect_match`). |
| 2 | `GetSurfaceData: Zero or negative surface area[~1E-07 to 1E-09]` (`D-EU-43`) | 4 | Madrid 2, Bologna 2 | **Accepted, no action** — zero-area sliver family, same root cause as #1. |
| 3 | `GetSurfaceData: Construction ... does not have the same materials in the reverse order ...` (`FINDING 253`) | 7 | Madrid 2, Bologna 5 | **Open — deterministic, root-caused, not fixed.** Dispatched to external Gemini/Antigravity session, Task A of `prompts/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05.md`. `report.md` not yet delivered as of this snapshot. |
| 4 | `CalcCoordinateTransformation: Invalid dot product` (preceded by `CheckConvexity: ... is non-planar` severes) | **2** | Madrid 1, Bologna 1 | **Open — not yet classified.** Dispatched as Task B of the same executor prompt, but that prompt's text says "1 instance so far" — **now stale**, see below. |

## 🔴 Open discrepancy — executor prompt is stale on signature #4's instance count

`prompts/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05.md` Task B was scoped to exactly one instance
(Madrid `c71e82e57d99bed1`, task `1306953_9`). A second instance surfaced during harvest-monitoring, after the
prompt was already handed off to Gemini/Antigravity:

- Bologna Step2-delta: stem `fd4b13e28f1c6f47`, task `1308161_12`, folder
  `EU11_IT-BOL-GALVANI2_step2delta_2026-09-05/out/fd4b13e28f1c6f47/eplusout.err`.

The original prompt was **not edited** (owner instruction: let Gemini discover it independently if it re-checks
Speed). This snapshot records the correction; the new prompt below hands off verification of the 2nd instance
explicitly.

## Evidence — newly classified tasks found during harvest-monitoring (not in `FINDING 252`'s original 24)

| Task | District | Stem | Outdir | Signature |
|---|---|---|---|---|
| `1306953_480` | Madrid | `722e9de69cd55e76` | `EU11_ES-MAD-BERRUGUETE_backlog_2026-09-05/out/722e9de69cd55e76` | `D-EU-43` |
| `1306952_276` | Lyon | `3395f5685ead3352` | `EU11_FR-LYO-HAUTCOEURPENTES_backlog_2026-09-05/out/3395f5685ead3352` | `FINDING 210` |
| `1305186_496` | Bologna | `56360df35f445afa` | `EU11_IT-BOL-GALVANI2_finding249_remedy_2026-09-04/out/56360df35f445afa` | `FINDING 210` |
| `1308161_12` | Bologna (Step2-delta) | `fd4b13e28f1c6f47` | `EU11_IT-BOL-GALVANI2_step2delta_2026-09-05/out/fd4b13e28f1c6f47` | `CalcCoordinateTransformation` (2nd instance, unclassified) |

Original 24-task tally with full stem lists for signatures #1/#2/#4: `FINDING 252`
(`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` line 1851). Full stem list for signature #3's 7 tasks:
`FINDING 253` (same file, line 1853).

## What is still outstanding

1. `Gemini/Antigravity` has not produced `openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md`
   — the folder does not exist on disk at all as of this snapshot. Tasks A and B of the original prompt are
   presumed not started or not finished.
2. Backlog jobs Lyon/Madrid/Bologna are far from drained (hundreds of tasks each still pending, see totals
   table) — further `FAILED`-count growth within the 4 known signatures is expected and does not need a new
   investigation unless a 5th signature appears.
3. See `prompts/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05-v2.md` for the delta task handed off on the basis
   of this snapshot.
