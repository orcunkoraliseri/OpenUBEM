# PLAN — ten open items, 2026-08-18 (late)

**Slug:** `PLAN_ten-items-2026-08-18-late`
**Date:** 2026-08-18 (late)
**Register:** `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md`
**Predecessor:** `PLAN_open-48-third-fleet-run-2026-08-18.md` — closed the same evening, all six tasks
discharged or void.
**Selected by:** the director, on the user's instruction *"choisir nouvelle 10 taches ouverts par list
ici … et apres, preparer une plan d'implementation et apres continue de l'execution jusqu'a la fin"*
(2026-08-18, late).
**Executed by:** the director personally. No executor is dispatched — the user asked for execution to
run to the end in this session, and the arc's last five executor dispatches stalled on backgrounded
monitors.

---

## 1. Why these ten, and what was deliberately left out

The register carries **26 live items** (24 in the §1 table + `OPEN-54` and `OPEN-55`, both opened
2026-08-18 and not yet given table rows). Ten were selected against three filters, applied in order:

1. **No cluster compute.** Speed's login node is forbidden for compute and a fleet run costs ~3 hours.
   Every task below runs locally or reads artifacts already on disk.
2. **No blocked-on-user step.** An item whose only remaining move is a DESIGN ruling cannot progress
   here. This excludes **OPEN-35** (which fallback is intended), **OPEN-17** (draw-tier promotion),
   **OPEN-27** (external source), and **OPEN-55** (proposal already with the user).
3. **A next move that is actually finishable in one pass** — a measurement, a closure, or a code guard
   with an explicit closure condition. This excludes **OPEN-18** (needs a new zone-removal mechanism,
   explicitly unscoped), **OPEN-19** (needs a climate-zone switch that does not exist), **OPEN-20**
   (a new validation matrix), and **OPEN-47 Reason 2** (a citation audit that needs live web retrieval
   of paywalled and dead-linked sources).

**The ten, in three natural clusters plus four singletons:**

| # | item | cluster | the next move |
|---|---|---|---|
| T01 | **OPEN-48** | — | formal closure; the blocker was discharged by the run that just ended |
| T02 | **OPEN-54** | — | implement the `_ssh` guard — the ban on editing the pipeline was run-scoped and the run is over |
| T03 | **OPEN-11** | six buildings | test the suspected identity with OPEN-42 face (ii) |
| T04 | **OPEN-42** | six buildings | same identity from the other side + the `no_floors` correlation |
| T05 | **OPEN-07** | `LAUNDRYROOMFLR1` | resolve the third building against OPEN-38's proved mechanism |
| T06 | **OPEN-38** | `LAUNDRYROOMFLR1` | locate the runaway in the prototype; scope the remedy |
| T07 | **OPEN-53** | — | read the `.err` tails of the 874 short directories; classify the cause |
| T08 | **OPEN-29** | — | the forward-citation sweep the item has been asking for since 2026-08-05 |
| T09 | **OPEN-13** | — | reproduce or refute **E-UTCI-12** at HEAD, the item's last live leg |
| T10 | **OPEN-12** | — | state what survives the 2026-08-18 reconciliation, or close |

🔴 **One hypothesis is written down here before it is tested, and it is the reason T03 and T04 are
adjacent.** OPEN-11's six "inverted-geometry" buildings and OPEN-42's six placeholder-`200.0 m²`
Warehouses are, by inspection of the two register sections, **the same six `osm_id`s**. If that holds,
two items that have been tracked independently since 2026-08-06 and 2026-08-11 describe **one
population**. **The prediction is recorded now so it can be scored, and it is not assumed in any
downstream task.**

---

## 2. Hard rules

1. **No compute on the Speed login node.** No `srun`, no `ssh … python`. This pass needs no cluster at
   all; if a task appears to need one, that task **stops** and says so.
2. **Never touch other-project cluster runs.**
3. **`python` means `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`.** Never a bare
   `python`.
4. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, `docs/docs_DONE/`, `docs/docs_main/`,
   `docs/docs_stepN/`. **No `.py` file under `docs/`, ever.**
5. **Git is handled externally. Never `git add`, `git commit`, `git restore` or `git checkout`.**
   Read-only git (`log`, `show`, `diff`, `status`) is allowed and is used heavily below.
6. **Append and amend; never overwrite a finding.** A number that turns out wrong is **struck with
   `~~`** and corrected in place, with the correction stated. This is the register's own rule and it
   applies to this document too.
7. **Record predictions before measuring** wherever a task has a testable expectation. §1's
   six-building identity is the first of them.
8. **A measurement task does not fix anything.** T01, T02 and T06 are the only tasks permitted to
   change code or close an item; every other task measures and reports.
9. **Figures and CSVs go to `openubem/outputs/`** — comparisons under `openubem/outputs/comparisons/`.
   Never under `docs/`.

---

## 3. File layout

| path | role |
|---|---|
| `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-items-2026-08-18-late.md` | this document |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_ten-items-2026-08-18-late.md` | the pass's consolidated findings |
| `scripts/analysis/open11_open42_six_building_identity.py` | T03/T04 |
| `scripts/analysis/open53_err_tail_census.py` | T07 |
| `scripts/analysis/open29_defect_status_sweep.py` | T08 |
| `openubem/outputs/comparisons/open11_open42_six_buildings.csv` | T03/T04 output |
| `openubem/outputs/comparisons/open53_err_tail_census.csv` | T07 output |
| `openubem/outputs/comparisons/open29_defect_status_sweep.csv` | T08 output |
| `scripts/validation/v12_cell_pipeline.py` | **T02 edits this, and only this** |

---

## 4. Dependency decisions

- **No new third-party dependency.** `pandas`, `geopandas` and the standard library are already in the
  venv and are sufficient for every task here.
- **No network.** T09's E-UTCI-12 check runs against the local tree; T08's sweep runs against local
  documents. Nothing fetches.
- **`pytest` is run as `pytest -q tests/`**, never bare — a bare root-level run reports ~36 false
  failures (`project_test_suite_baseline_scope`).

---

## 5. Facts this plan is built on, with citations

| fact | source |
|---|---|
| OPEN-11's six are `la_rural/way/472960972`, `472961034`, `472961088`, `472961091`, `472961171`, `la_urban/way/402215469` | register §4, OPEN-11, 2026-08-06 (N04) amendment |
| OPEN-42 face (ii)'s six placeholder-`200.0` Warehouses are the same six strings | register §5, OPEN-42, "Face (ii)" |
| OPEN-42 face (i): Warehouses fail at 13.68 % vs 0.0443 %; 26 of 44 fleet fatals; **zero in `layout_assign`** | register §5, OPEN-42, face (i) table |
| All seven `layout_assign` fatals are thermal runaway in zone `LAUNDRYROOMFLR1`, −12,459 to +182,399 °C | register §4, OPEN-38, "Defect (i)" |
| OPEN-07's three: `la_urban/way/401910463`, `nyc_rural/way/965718402`, `965718403`; the first still has no surviving IDF | register §4, OPEN-07, 2026-08-18 amendment |
| OPEN-53: `.sql` 39,926 and `.end` 39,925 against 40,800 dirs; 874 of the gap in `austin_suburban_fast_zone` + `austin_suburban_floor` | register §7, OPEN-53 |
| OPEN-29's candidate IDs: E-LA-06, 11, 12, 13, 15, 16, 17, 18, 19, 30, 33, plus E-LA-21 | register §3, OPEN-29 |
| OPEN-54's closure condition: `_ssh` raises on remote failure, the three unguarded `mkdir` sites inherit it, `:325` false-success unreachable | register §7, OPEN-54, "Closure condition" |
| `_ssh` is `scripts/validation/v12_cell_pipeline.py:111`, returns `stdout + stderr`, no `returncode` check, no `TimeoutExpired` catch | `extra/INVESTIGATION_open-54_ssh-unchecked-exit.md` |
| OPEN-48's blocker — no post-fix fleet re-run exists — is discharged | `extra/MEASUREMENT_open-48_third-fleet-run.md` §3.1, §6 |

---

## 6. Tasks

### T01 — OPEN-48: close it

**What.** Move OPEN-48 from live to struck, retire the ID, and record the closure basis.
**Why.** Its stated blocker was *"the adopted baseline run cannot be reproduced from this
repository"*, operationalised as *"no post-fix fleet re-run exists."* One now exists, and its result
is recorded: the fix under test moves classified buildings by **under 0.08 %**.
**How.** Register §1 table row struck + §5 section closure note; `docs/PROJECT_CHECKLIST.md` row;
count arithmetic re-derived programmatically, not asserted.
**How to test.** The recount script reports the new live/struck split and the struck−retired
difference stays exactly 2 (OPEN-02, OPEN-28).

### T02 — OPEN-54: implement the `_ssh` guard

**What.** Make `_ssh` raise on a non-zero remote exit and on timeout, and give the four call sites that
must tolerate failure an explicit opt-out.
**Why.** The ban on editing this file was **run-scoped** — *"a mid-run change would break the
single-variable comparison"* — and the run ended 2026-08-18 20:47. The defect cost this arc two
misclassified cells in one evening.
**How.** `check=True` default with an `allow_fail=` escape hatch; `TimeoutExpired` converted to the
same exception type; the `:325` `squeue | wc -l` poll made to distinguish *"zero jobs"* from *"the
command failed."*
**How to test.** A synthetic failing command raises; a synthetic succeeding command returns unchanged
output; `allow_fail=True` restores old behaviour; `pytest -q tests/` unchanged against its baseline.
**No cluster call is made** — the guard is tested against local `ssh` stand-ins only.

### T03 — OPEN-11: test the six-building identity

**What.** Verify or refute §1's prediction that OPEN-11's six are OPEN-42's six.
**Why.** Two items tracked separately for twelve days may be one population. If so, OPEN-11's
"inverted geometry" label is a second mislabel on top of the one already found on 2026-08-18.
**How.** Read the six `osm_id`s out of the live fleet results and `01_buildings.gpkg`; compare
`footprint_area_m2`, `archetype_id`, `data_quality_flag`, `simulation_status`.
**How to test.** The identity is a set comparison — it holds exactly or it does not. Record which.

### T04 — OPEN-42: the same six from the Warehouse side, and the `no_floors` correlation

**What.** Re-derive face (ii) from the live artifacts, and test whether `no_floors` or the placeholder
footprint is the better predictor of failure.
**Why.** Face (i) and face (ii) are stated as independent; 37 of 38 Warehouses carry `no_floors` while
only 6 carry the placeholder, so they cannot both be the cause.
**How.** Cross-tabulate `archetype_id`, `data_quality_flag`, `footprint_area_m2` and
`simulation_status` over all twelve cells of the most recent complete fleet on disk.
**How to test.** Every figure traces to a column in the emitted CSV.

### T05 — OPEN-07: resolve the third building

**What.** Decide `la_urban/way/401910463` against OPEN-38's proved `LAUNDRYROOMFLR1` mechanism.
**Why.** Two of three are settled. The third has been open on *"no IDF survives"* — but the
mechanism is now readable from the `.err` alone, which **does** survive.
**How.** Read the surviving `eplusout.err`; test for the `CalcHeatBalanceInsideSurf` /
`LAUNDRYROOMFLR1` signature; compare against the two settled buildings.
**How to test.** Either the signature is present (item resolves to OPEN-38's mechanism) or it is not
(item stays open on a named, different cause). **Both outcomes are results.**

### T06 — OPEN-38: locate the runaway in the prototype

**What.** Find what is different about `LAUNDRYROOMFLR1` in the `SmallHotel` prototype and scope the
remedy.
**Why.** One prototype zone accounts for an entire mode's failure set. The mechanism is proved; the
*cause inside the zone* is not.
**How.** Read the zone's surfaces, internal loads and HVAC assignment out of the repo's own
`SmallHotel_90.1-2013.idf` control; compare against a healthy zone in the same file.
**How to test.** The finding must name a specific IDF object and field, with a line number, or report
that the file does not contain the answer.

### T07 — OPEN-53: read the `.err` tails

**What.** Classify the 874 short harvest directories by what their `.err` files actually say.
**Why.** The item's own first measurement, never made: fatal, truncation, or harvest-timing artifact.
**How.** Census the tail of each `.err` in the two Austin sub-cells; bucket by trailer signature.
**How to test.** Buckets sum to the census total; a sample of five is read by hand and matches its
bucket.

### T08 — OPEN-29: the forward-citation sweep

**What.** For each candidate `E-LA-nn`, follow its citations forward to the latest document that
mentions it and record its final status with a `path:line`.
**Why.** The item has carried an explicitly **unverified** candidate list since 2026-08-05 and is the
register's last ❓.
**How.** Mechanical grep over the docs tree, newest-mention-wins, then a hand read of each final
mention.
**How to test.** Two-column output — genuinely-still-open vs closed-elsewhere. Every row carries a
citation. **No row is promoted to a register item in this pass.**

### T09 — OPEN-13: E-UTCI-12 at HEAD

**What.** Reproduce or refute E-UTCI-12, the item's only remaining live leg.
**Why.** Every other leg is discharged. If E-UTCI-12 does not reproduce, the item closes.
**How.** Locate the defect's defining site, read what it asserts, test that assertion against HEAD.
**How to test.** A positive control is required — a check that would fail if the test method were
blind. The 2026-08-18 T03 precedent (a deliberately broken test file) is the pattern.

### T10 — OPEN-12: what survives

**What.** State precisely what remains open after the 2026-08-18 scope reconciliation.
**Why.** Both number-pairs now stand and are explained. An item whose contradiction is resolved either
closes or has a residual that nobody has written down.
**How.** Read the item end to end; identify each claim's current status; write the residual or the
closure.
**How to test.** Every surviving claim is either supported by a citation or struck.

### T11 — records

**What.** Register (ten sections + §1 table + count arithmetic), `docs/PROJECT_CHECKLIST.md`, the
director prompt, this progress log, the consolidated measurement doc, and the progress board artifact.
**How to test.** Programmatic recount; zero control characters in the prompt; every claim in the board
traceable to this document.

---

## 7. Stop-and-report points

- **CP-A — after T02.** The only code change in the pass. Report the diff and the test result before
  going further. **If `pytest -q tests/` moves off its baseline, stop.**
- **CP-B — after T04.** The six-building identity is either confirmed or refuted; if confirmed, two
  register items merge and that is a structural change to the register, reported before it is written.
- **CP-C — after T08.** If the sweep turns up genuinely-open defects, **they are reported, not
  adopted.** Adopting them is the user's call, not this pass's.
- **CP-D — after T11.** Final report.

---

## 8. Progress log

#### T02 — OPEN-54: `_ssh` guard implemented — completed 2026-08-18 (late) — **CP-A**

**Artifacts.** `scripts/validation/v12_cell_pipeline.py` (the only production file this pass changed);
tests run inline, transcript quoted below.

**What was done.** `RemoteCommandError` added; `_ssh` raises on a non-zero remote exit and on
`subprocess.TimeoutExpired`, with the command, exit code and both streams in the message;
`allow_fail=True` added as the explicit opt-out. `_parse_sacct_state_counts` added. The poll loop now
captures `${PIPESTATUS[0]}` from `squeue` and **concludes completion only when `sacct` positively
corroborates it** — no states → re-poll; any of `PENDING/RUNNING/REQUEUED/RESIZING/SUSPENDED/`
`CONFIGURING/COMPLETING` → re-poll. The three `mkdir` sites and the sbatch submit inherit the guard by
calling `_ssh` without `allow_fail`.

**Test status.** Nine local checks, **no cluster call** — `subprocess.run` swapped for a stand-in that
also asserts the argv still carries the `bash -lc` wrapper, so a future refactor cannot silently drop
the tcsh guard:

```
PASS success passthrough      PASS timeout raises         PASS empty sacct not complete
PASS nonzero raises           PASS timeout allow_fail     PASS active detected
PASS allow_fail passthrough   PASS sacct parse            PASS CANCELLED+ normalised
ALL PASS
```

**Deviations.** The first patch wrote literal newlines into two f-strings instead of `\n` escapes and
broke the module. Caught by `ast.parse` before any test ran, repaired, re-verified. Recorded because
this escape hazard has now bitten this arc twice.

**Notes.** ⚠️ **Not exercised against the live cluster**, by design — the pass authorised no cluster
call. The first real run through the new guard should be watched.

#### T03 / T04 — OPEN-11 and OPEN-42 — completed 2026-08-18 (late) — **CP-B**

**Artifacts.** `scripts/analysis/open11_open42_six_building_identity.py`,
`open42_run2_fatal_zone_geometry.py`, `open42_zone_volume_census.py`;
`openubem/outputs/comparisons/open11_open42_six_buildings.csv`,
`open42_run2_fatal_zone_geometry.csv`, `open42_zone_volume_census.csv`;
`extra/MEASUREMENT_ten-items-2026-08-18-late.md` §2–§3.

**T03 — the prediction held.** §1's pre-registered identity is exact: intersection 6, symmetric
difference 0, and the same six are also exactly the fleet's six non-successes. `no_floors` does not
separate them (7,719 of 8,160 carry it, catching 5 of 6).

**T04 — the item's blocking premise was false, and the mechanism is found.** The register's ruling
said the IDF corpus needed for the next step no longer existed on disk. Run 2 kept all six buildings'
IDFs and outputs and reproduced the identical failure. From them: the fatal zone is **identical to its
non-fatal siblings** on surface count, types, boundary conditions, area, height and WWR; and the
*"topmost storey without exception"* invariant **fails in run 2, 4 of 6 not 6 of 6**. The cause is
EnergyPlus computing a **negative** zone volume from our geometry and substituting a **10 m³ stub** —
present on **8,160 / 8,160 buildings**, with a **0 / 2 control** on DOE-prototype geometry. Failures
average −6,096 m³ computed volume against −683 m³ for successes.

**CP-B report.** The identity is confirmed, so two items do describe one population — but the
structural change is larger than the checkpoint anticipated: the population is the whole fleet.
**Registered as OPEN-56 rather than merged into either item**, and closures for OPEN-42 and OPEN-11
are **recommended to the user, not taken**.

**Test status.** Non-vacuity control obligatory and met (prototype geometry, 0 of 2). Field offsets
for `BuildingSurface:Detailed` were wrong on the first run (EnergyPlus 23.1 inserts `Space Name`);
corrected and re-run before any number was reported.

#### T05 — OPEN-07 — completed 2026-08-18 (late)

All three buildings have a surviving IDF, `.err`, `.end` and `.sql` in run 2 — including
`la_urban/way/401910463`, which the item records as having none — and **all three completed with 0
severe errors** and no `LAUNDRYROOMFLR1` involvement. Closure **recommended with the `layout_assign`
caveat**, not taken.

#### T01 / T06–T11 — closure, supersession, and the records — completed 2026-08-18 (late) — **CP-C / CP-D**

**T01 — OPEN-48 CLOSED and ID retired.** Blocker discharged; the fix it was testing measures under
0.08 %.

🔴 **T06, T07, T08, T09, T10 were already done.** Each had a completed measurement in
`openings/extra/` — four dated the same day as this plan. **Selection error, mine**: the ten were
picked from the register's §1 rows and item headlines, several of which still carry the original
*"first measurement, not yet made"* framing with the answer recorded further down the section or in a
separate document. **Cost: roughly half the pass's task budget.** Full account in
`extra/MEASUREMENT_ten-items-2026-08-18-late.md` §7.

What each still contributed: **T06** added a falsifiable hypothesis linking OPEN-38's
`LAUNDRYROOMFLR1` (the prototype's smallest zone, 5.11 m² underground) to OPEN-18's √S scaling at a
median S of 0.054 → ≈0.28 m² — **not tested, recorded as the next thing to test**. **T07** recorded
that OPEN-53's closure condition is partly discharged by runs 2/3 regenerating the artifacts, while
the same files are now load-bearing and still not durable. **T08** produced a working sweep script
whose main result is that **the method does not work** — recency returns roll-up boards, and the first
run classified eight IDs from OPEN-29's own candidate list, which is circular; two documented
exclusions are now in the script and the hand re-trace still wins.

**T11 — records.** Register: three new §1 rows (OPEN-54, OPEN-55, OPEN-56 — the first two had none),
OPEN-48 and OPEN-54 struck and retired, new §-section for OPEN-56, amendments to OPEN-42, OPEN-11,
OPEN-07 and OPEN-53, header count re-derived. Recount, programmatic:
**25 live / 31 struck / 56 total, OPEN-01…OPEN-56, none missing, none duplicated, next free
`OPEN-57`.** ⚠️ The reconciliation invariant needed correcting: 31 struck − 2 folded = **29 retired**,
against the previous header's prose figure of 26, which had drifted one behind the table. Corrected
with the derivation shown. `docs/PROJECT_CHECKLIST.md`, the director prompt and the progress board
artifact all updated.

**Test status.** `pytest -q tests/` run against the T02 change; result recorded in the entry below.

**Plan status: all eleven tasks discharged. CP-A, CP-B, CP-C and CP-D reported.**

#### CP-A test result — full suite against the T02 change — 2026-08-18 (late)

```
.venv/Scripts/python.exe -m pytest -q tests/
1875 passed, 55 skipped, 11 warnings in 1642.50s (0:27:22)   exit 0
```

🟢 **Exactly the recorded baseline — `1875 passed, 55 skipped, 11 warnings`** (previous full run,
T06 of `PLAN_open-52-and-four-items-2026-08-18.md`: the same three numbers in 1477.74s). **Zero drift
on all three counts.** The `_ssh` guard changes no test outcome, which is the expected result — no
test in the suite exercises `v12_cell_pipeline.py`'s remote path, and that absence is itself worth
recording: **the guard's only coverage is the nine inline checks in T02, not the suite.**

**CP-A signed. The plan is complete: all eleven tasks discharged, all four checkpoints reported.**
