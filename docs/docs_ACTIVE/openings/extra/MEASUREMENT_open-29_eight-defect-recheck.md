# MEASUREMENT — open-29-eight-defect-recheck

> **Slug:** `open-29-eight-defect-recheck` · **Date:** 2026-08-13 · **Register item:** OPEN-29
> **Task:** T05 of `implemenation/previous/PLAN_five-more-items-2026-08-13.md`. **Measurement only — no code
> changed.** No document was edited except this file. The register, director prompt, board and plan's
> own progress log were not touched (per the plan's §1.7).

---

## 1. Method

The eight IDs re-checked are the ones the register (`INVESTIGATION_open-items-register.md:1672`,
2026-08-06, most recently reconfirmed 2026-08-12 at `:1835`) still carries as STILL-OPEN inside
OPEN-29: `E-LA-06` (flow-balance half), `E-LA-15`, `E-LA-16`, `E-LA-17`, `E-LA-18`, `E-LA-19`,
`E-LA-30`, `E-LA-33`. `E-LA-21` is excluded — it is separately closed (R06 + the 2026-08-12
malformed-variant sweep) and is not one of the eight.

For each ID: (1) took the last-known status and citation from
`extra/MEASUREMENT_open-29_defect-status-trace.md` (2026-08-06) as the starting point, not as the
answer; (2) re-grepped the bare ID and its named mechanism across the whole tree for any citation
dated after 2026-08-06; (3) checked the named mechanism directly against the current source at HEAD
(not a document's claim about it) — i.e., does the code path that produces the defect still exist,
unpatched. Git history was consulted only to confirm file mtimes/commit dates for "nothing changed
since." Per §5-T05(3), E-LA-18/E-LA-19 were checked specifically against OPEN-09's C06 measurement
(`extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md`) rather than re-litigated from scratch.

---

## 2. Table — verdict, citation, command

| ID | Verdict | File:line citation | Command |
|---|---|---|---|
| **E-LA-06** (flow-balance half) | **STILL-OPEN** | `openubem/geometry/layout_assigner.py:863-865` — 2026-07-26 comment still reads *"the handful of pre-existing Severes present in some runs (CheckWarmupConvergence, CheckAirLoopFlowBalance) are the same already-tracked classes as E-LA-14/16/18/19/E-LA-06"* — unchanged, no fix, no later document mentions it again except as a still-current label. | `grep -n "CheckAirLoopFlowBalance" openubem/geometry/layout_assigner.py` |
| **E-LA-15** | **STILL-OPEN** | Defining site `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:270` (`SizeAirLoopBranches` minimum-air-flow Fatal). Its named mechanism string appears **nowhere** in production code — never handled, never guarded. | `grep -rn "SizeAirLoopBranches" openubem/ scripts/ --include=*.py` → 0 hits |
| **E-LA-16** | **STILL-OPEN** | Defining site `.../PLAN_structural-fixes_implementation.md:279` — *"Cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family."* No mechanism reference anywhere in production code. | `grep -rn "cooling-coil-UA\|CoolingCoilUA\|cooling.tower.UA" openubem/ scripts/ --include=*.py` → 0 hits |
| **E-LA-17** | **STILL-OPEN** | Defining site `.../PLAN_structural-fixes_implementation.md:290` — persistent-divergence signature in a second zone, unfixed. No mechanism reference anywhere in production code. | `grep -rn "persistent.divergence" openubem/ scripts/ --include=*.py` → 0 hits |
| **E-LA-18** | **STILL-OPEN** (mechanism unfixed; see note) | `openubem/geometry/layout_assigner.py:863-865` — `CheckWarmupConvergence` still listed as a live, untouched pre-existing Severe class, same comment as E-LA-06's row. `scripts/cluster/t20_harvest_layout_assign.py:264-265,441-448` still counts it every harvest, unpatched. | `grep -n "CheckWarmupConvergence" openubem/geometry/layout_assigner.py scripts/cluster/t20_harvest_layout_assign.py` |
| **E-LA-19** | **STILL-OPEN** (mechanism unfixed; see note) | Same citation as E-LA-18 — E-LA-19 is the same `CheckWarmupConvergence` lineage (`way/241836727`, E-LA-14's regression pair), same unpatched class. | `grep -n "CheckWarmupConvergence" openubem/geometry/layout_assigner.py scripts/cluster/t20_harvest_layout_assign.py` |
| **E-LA-30** | **STILL-OPEN** | `scripts/analysis/a4_bis_generate_layout_assign_viewer.py:17` — `fast_scale_idf_text()` still present, file unchanged since 2026-07-26 (mtime `Jul 26 11:11`). Replacement scripts (`b05f_rebuild_layout_assign_viewers.py`, `b08b_rebuild_layout_assign_viewers.py`) still explicitly avoid calling it. | `git log -1 --format=%ai -- scripts/analysis/a4_bis_generate_layout_assign_viewer.py` → `2026-07-27 09:56:55` (last touch, structural-fixes closure commit, predates this item); `ls -la scripts/analysis/a4_bis_generate_layout_assign_viewer.py` → `Jul 26 11:11` |
| **E-LA-33** | **STILL-OPEN** | `openubem/geometry/layout_assigner.py:539` — `match_storeys()` still exists and still uses the `Zone.Multiplier` mechanism only (no vertex/Z-coordinate scaling was added), the exact "storey matching is invisible in geometry" cause named at `docs_DONE/.../DONE_PLAN_storey-matching_implementation.md:3353-3379`. The design decision *"not to be done reflexively"* (same source) still stands — no later document reopens it. | `grep -n "def match_storeys" openubem/geometry/layout_assigner.py` |

**No verdict changed from the register's 2026-08-06/09/12 record.** All eight remain STILL-OPEN,
re-derived from HEAD rather than taken on the prior report's word. `git log --since="2026-08-06"` on
every file above shows only two touches in the whole window, both R06's one-space→regex fatal-test
fix (`t20_harvest_layout_assign.py`, commits `2ea15d4` and `6c8c9f7`, 2 and 1 lines respectively) —
unrelated to any of these eight mechanisms.

---

## 3. E-LA-18 / E-LA-19 — checked against OPEN-09's C06 measurement, not re-litigated

Per the plan's explicit instruction, these two were checked against
`extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md` (task C06, 2026-08-06) rather than re-derived
independently.

**Does C06 discharge them? Partially, and precisely as C06 itself already scoped.** C06 tested
whether the `CheckWarmupConvergence` "cosmetic" label — inherited unexamined across five log entries
including E-LA-18 and E-LA-19 — is actually true, on the one population where a matched
`thermal_mass=True`/`False` control exists (150 `nyc_rural`/`SmallOffice` buildings). Result: **96.3%
distribution overlap**, a small, correctly-signed, statistically-real residual (≈0.22 percentage
points, ≈0.20 kWh/m² at the population median) — the claim **holds** at that population
(`MEASUREMENT_open-09_cosmetic-accuracy-test.md:103-123`).

**What it leaves unanswered:** the mechanism itself (the Severe still fires) is not fixed — C06 is an
accuracy test, not a patch, and changes no code. C06's own §6 states plainly it "does not generalize
'cosmetic' beyond `nyc_rural`/`SmallOffice`/`u_roof=0.119`" — so for any other archetype/cell/roof
assembly, whether the residual is still small and correctly-signed is untested. **Verdict stands as
STILL-OPEN** (the defect — an unpatched Severe class — exists at HEAD) with the accuracy-impact
question C06 was asked answered for one population.

**A discrepancy found, reported not resolved.** `PLAN_compute-queue.md:343` (manager-verified fact,
2026-08-06) names C06's "five inherited log entries" as **E-LA-14, E-LA-16, E-LA-18, E-LA-19,
E-LA-23** — i.e. it lists E-LA-16 as part of the same `CheckWarmupConvergence` "cosmetic" lineage.
But E-LA-16's own defining text (`.../PLAN_structural-fixes_implementation.md:279`) is a **different**
mechanism — cooling-coil-UA/cooling-tower-UA-autosize failure, not warmup convergence — and
`openubem/geometry/layout_assigner.py:863-865`'s own current comment groups `CheckWarmupConvergence`
with E-LA-14/16/18/19/E-LA-06, using E-LA-16 the same (inconsistent) way. Two documents in the tree
use "E-LA-16" for what reads as two different failure signatures. This was not resolved here — the
task's instruction was to check C06 against E-LA-18/E-LA-19 specifically, not to adjudicate E-LA-16's
identity, and doing so would be re-litigating a naming question outside T05's scope. E-LA-16's row
above is reported strictly against its own defining text (cooling-coil-UA family), which is the
citation the register itself currently uses for it.

---

## 4. What I could not determine

- **Fleet-wide re-counts of the E-LA-15/16/17 failure signatures at current (T20) scale.** The
  register's own prior report names this as the needed next measurement for each. It requires
  grepping the raw `eplusout.err` files of the 8,160-building T20 harvest for the specific mechanism
  strings (`SizeAirLoopBranches`, the cooling-coil/tower-UA family, the persistent-divergence
  signature). Those raw `.err` files live only on the Speed cluster. Locally, only
  `openubem/outputs/comparisons/t20_layout_assign_eui.csv` (dated 2026-08-04, pre-R06) exists, and its
  columns (`has_fatal`, `n_severe`, `n_warmup_convergence`) do not distinguish these specific
  signature classes — `has_fatal` is additionally disqualified as evidence for any pre-2026-08-09
  artifact per the register's own standing rule. 948 local `eplusout.err` files exist under
  `docs/docs_DONE/SETUP/layoutAssigner/debug/`, but these are earlier local-leg/debug investigation
  runs, not a systematic fleet-scale sweep, so they cannot answer a current fleet-wide count. **This
  is genuinely out of local reach, not a shortcut taken.**
- **A current fleet-wide `CheckAirLoopFlowBalance` Severe count for E-LA-06's flow-balance half**, for
  the same reason — raw `.err` text at fleet scale is cluster-only.
- **Whether the E-LA-16 naming discrepancy (§3) reflects a genuine two-defects-one-ID collision or a
  documentation error in one of the two sources.** Both readings are internally consistent with their
  own document; adjudicating which is correct was outside this task's instruction and is reported as
  an open question, not resolved.
- **Whether "cosmetic" (E-LA-18/19's accuracy claim) generalizes beyond the one tested population.**
  C06 states this limit itself; no broader matched-control population exists locally or was run here.

---

## 5. Artifacts

- This report only. No CSV was produced — every finding above is a direct grep/read against tracked
  files, individually reproducible from the commands in §2, so no derived intermediate artifact was
  needed.
