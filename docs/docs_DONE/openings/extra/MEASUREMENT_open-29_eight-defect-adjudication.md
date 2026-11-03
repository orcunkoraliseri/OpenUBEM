# MEASUREMENT — OPEN-29: adjudicate the eight forwarded defects

> T08 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`. Read-only on production code. Evidence and a
> recommendation only — no-compute dispositions of this kind are the director's call (user's standing
> instruction, 2026-08-12), not the executor's.

## Input

X07 (`implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`, 2026-08-18 overnight) tested the eight
hand-verified STILL-OPEN defect IDs against run 2's fleet error taxonomy for the first time and found
four with no `.err` signature in 8,160 buildings. This task does not re-sweep the candidate list
(that attempt was already tried once and lost to the hand re-trace, per OPEN-29's own history) — it
takes X07's eight IDs and, for each, re-derives the cited evidence live at HEAD, 2026-08-19, and
proposes a disposition.

## Control — E-LA-21 re-derives as CLOSED-ELSEWHERE

Re-grepped `scripts/cluster/{t07_harvest_results.py:199, t07b_run_auto_refit_local.py:330,
t08_harvest_results.py:246, t08_local_remainder.py:431, t17_harvest_layout_assign.py:255,
t18_harvest_layout_assign.py:252, t19_harvest_layout_assign.py:260, t20_harvest_layout_assign.py:260}`
— all eight sites carry `re.search(r"\*\*\s+Fatal\s+\*\*", err)`, the tolerant two-space-or-more form.
A repo-wide search for the one-space literal `"** Fatal **"` under `scripts/` and `openubem/` returns
zero matches. `git log --since=2026-08-18` on all eight files shows one commit (`b2d0220`), which
touches only a comment on `openubem/geometry/layout_assigner.py` (the E-LA-16 naming correction —
diff read directly, no functional change). **Control PASSES.** The harness is trusted for the other
eight.

## Method

For each of the eight, the defect's own defining text names its signature. Where that signature is an
EnergyPlus `.err` family, it was tested against `openubem/outputs/comparisons/open09_fleet_err_taxonomy.csv`
(run 2's 8,160-building `auto`-mode corpus, `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet`) —
**re-verified on disk first** (8,160 `eplusout.err` files present) and **the generating script was
re-run live** (`py scripts/analysis/open09_fleet_err_taxonomy.py`), not just read from the committed
CSV. The regenerated file is byte-identical to the committed one (`git diff --stat` empty) —
deterministic, and current, not stale. Where the signature is a geometry/code-behaviour claim rather
than an `.err` line, it was tested by direct code and artifact comparison instead, since that is what
the defect's own statement calls for.

`openubem/outputs/comparisons/open10_storey_expressibility_fleet.csv` was re-derived the same way,
re-running `scripts/analysis/open35_open10_consequence_census.py` live — also byte-identical to the
committed file, and it reproduces the 90-building reach (66 `MidriseApartment` + 24 `HighriseApartment`)
and the 497/7,442 = 6.68 % `applied` split exactly.

## Disposition table

Full detail with citations in `openubem/outputs/comparisons/open29_eight_defect_adjudication_2026-08-19.csv`.

| ID | HEAD signature (2026-08-19) | Verdict | Recommendation |
|---|---|---|---|
| **E-LA-06** (flow-balance half) | **32/8,160 (0.39 %)**, Warning, "water-to-air heat pump coil rate" — matches the defining mechanism | STILL-OPEN | Not a new item — already reachable from OPEN-18 |
| **E-LA-15** | 0/8,160 in the tested corpus | NO SIGNATURE IN TESTED CORPUS — NOT ADJUDICATED | See "the auto/layout_assign gap" below |
| **E-LA-16** | 1/8,160 (0.01 %), Warning only, cooling-coil-UA half only (cooling-tower half: 0) | STILL-OPEN, immaterial-scale | Not a new item — director may find it closable on immateriality, not on evidence of a fix |
| **E-LA-17** | **16/8,160 (0.20 %)**, exact population match to OPEN-09 | STILL-OPEN mechanism, **not a separate defect** | Recommend striking it from OPEN-29's inherited list — it double-counts OPEN-09 |
| **E-LA-18** | 0/8,160 — zero `CheckWarmupConvergence` anywhere in the corpus | NO SIGNATURE IN TESTED CORPUS — NOT ADJUDICATED | See below |
| **E-LA-19** | `way/241836727` present, succeeds cleanly, 0 warmup signature | NO SIGNATURE IN TESTED CORPUS — NOT ADJUDICATED | See below |
| **E-LA-30** | 🔴 **Reproduces at HEAD, confirmed by direct code/format read** (new finding this pass) | STILL-OPEN, confirmed | Not a new item — see mechanism below |
| **E-LA-33** | **93.32 % inert** (497/7,442 applied), inside its own 82–98 % band, re-derived exactly | STILL-OPEN, confirmed | Not a new item — already fully explained under OPEN-10 |

## E-LA-30 — a correction to X07's framing, not just a re-confirmation

X07 grouped E-LA-30 with the three genuinely signature-absent defects under "no signature anywhere in
a whole fleet." That is imprecise. E-LA-30 was never an EnergyPlus-runtime defect — it is a claim that
`fast_scale_idf_text()` (`scripts/analysis/a4_bis_generate_layout_assign_viewer.py:17-42`) is a
content no-op on this codebase's generated IDFs, so the A4-bis viewer artifacts do not depict the real
pipeline. An `.err` sweep is simply the wrong instrument for it — it was never testable that way, which
is what X07's own limits paragraph already said. This task tested it the way its own statement calls
for: read the code and compare it against a real generated IDF.

`fast_scale_idf_text()`'s vertex-scaling branch only fires on lines where `"Vertex" in line and
("Xcoordinate" in line or "Ycoordinate" in line)`. `config.py:49-52` (`BASELINE_IDF_DIR`) names the
true input: the 25 DOE/ASHRAE 90.1 reference prototype `.idf` files at
`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\`, which is exactly the
population E-LA-30 claims is a no-op for. Read directly at HEAD,
`ASHRAE901_OfficeSmall_STD2022_Buffalo.idf:2058-2060`:

```
5,13.46,0,  !- X,Y,Z ==> Vertex 1 {m}
22.69,13.46,0,  !- X,Y,Z ==> Vertex 2 {m}
22.69,5,0,  !- X,Y,Z ==> Vertex 3 {m}
```

— one line per vertex, all three coordinates comma-joined, comment text `"X,Y,Z ==> Vertex N {m}"`.
The substring `"Xcoordinate"` (no hyphen, no comma-separated form) never appears in this text, so the
branch is dead code and the function returns its input unchanged for the true baseline population —
mechanically reproducing the "content no-op on all 25 prototypes" claim against the actual source
file, not by citation and not by a proxy fixture. The file is unchanged since commit `69373f9`
(2026-07-27, before the defect was even raised as OPEN at CP-B the same day), and its two callers
(`scripts/analysis/b05f_rebuild_layout_assign_viewers.py`, `b08b_rebuild_layout_assign_viewers.py`)
are both still live under `scripts/analysis/`, not archived. **Verdict: STILL-OPEN, confirmed
reproducing, not absent.**

## The auto/layout_assign gap — E-LA-15, E-LA-18, E-LA-19

All three were raised under `layout_assign` mode during the structural-fixes work; run 2 is `auto`
mode. Their zero count in `open09_fleet_err_taxonomy.csv` is real and re-derived live, but it is
evidence about the `auto` fleet at HEAD, not about `layout_assign` — the same limit X07 itself named
for three of the eight. **I did not run any new simulation to close this gap** — T08 is measurement
against existing evidence, and running fresh EnergyPlus jobs to settle it would duplicate what T05 of
this same plan is already doing for a different defect (E-LA-17's `LAUNDRYROOMFLR1` population) on the
same premise (*"IDFs can be built locally — that blocker is stale"*).

**Narrowest signature that would settle each, proposed and not taken:**

- **E-LA-15** — rebuild `way/965718401` locally in `layout_assign` mode, `energyplus -x`, grep its
  `eplusout.err` for the `SizeAirLoopBranches` minimum-air-flow Fatal text.
- **E-LA-18** — rebuild `way/86121620` and `way/42496352` the same way, grep for `CheckWarmupConvergence`
  Severe on `CORE_TOP`/`CORE_MID`.
- **E-LA-19** — rebuild `way/241836727` in `layout_assign` mode specifically (its auto-mode success does
  not test the layout_assign code path the defect names), grep for the same signature.

This is three named buildings, not a fleet sweep, and does not need Speed — unlike the register's
2026-08-13 finding that a *fleet-wide* re-count of E-LA-15/16/17 needs the 8,160-building T20 harvest,
which does live only on Speed. A three-building local check is a materially smaller ask and was not
run in this task only because it is a code-write/simulate action outside T08's read-only scope, not
because it is infeasible.

## Overall recommendation on OPEN-29

The item cannot close. Of the eight: two (E-LA-06, E-LA-16) are confirmed still open with a real,
sized `.err` signature; two (E-LA-30, E-LA-33) are confirmed still open by direct code/artifact
verification; one (E-LA-17) is a live mechanism that is not a separate defect and should be struck
from this item's inherited list as a merge into OPEN-09, not a fix; three (E-LA-15, E-LA-18, E-LA-19)
remain genuinely unadjudicated — absent in the only corpus this task could read, untested in the mode
that would actually settle them. None of the eight is fixed. None warrants promotion to a new
top-level `OPEN-nn` item — every live one already overlaps an existing item (OPEN-18, OPEN-51, OPEN-09
×3, OPEN-10) or is scoped to two identified debug-only scripts (E-LA-30). **Recommended, not taken:**
strike E-LA-17 from OPEN-29's tracked list on the merge-into-OPEN-09 finding above, and run the three
narrow local rebuilds named above before the next attempt to close E-LA-15/18/19.

## Evidence

- `openubem/outputs/comparisons/open29_eight_defect_adjudication_2026-08-19.csv` — per-ID citation table.
- `openubem/outputs/comparisons/open09_fleet_err_taxonomy.csv`, `open09_fleet_err_perbuilding.csv` —
  re-run live 2026-08-19, byte-identical to the committed versions.
- `openubem/outputs/comparisons/open10_storey_expressibility_fleet.csv` — re-run live 2026-08-19,
  byte-identical to the committed version.
- `scripts/analysis/a4_bis_generate_layout_assign_viewer.py:17-42`,
  `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\ASHRAE901_OfficeSmall_STD2022_Buffalo.idf:2058-2060` —
  the E-LA-30 mechanism, read directly this pass against the true baseline source
  (`openubem/config.py:49-52`).
