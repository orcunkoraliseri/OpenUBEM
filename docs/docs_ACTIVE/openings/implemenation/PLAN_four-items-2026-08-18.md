# PLAN — four open items, 2026-08-18 (second pass of the day)

**Slug:** `four-items-2026-08-18`
**Written:** 2026-08-18, by the director, after `PLAN_five-items-2026-08-18.md` closed at CP-3 and the
user gave the instruction *"oui vas-y, continuer jusqu'à la fin."*
**Arc:** `openings` — `docs/docs_ACTIVE/openings/`
**Register (the authority on every item below):** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`
**Director prompt (state of the arc):** `prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`

**Item selection is the director's, per the user's standing instruction of 2026-08-12** (no-compute
work: the director picks the items, the user rules only on rulings). The four were picked because each
one is **local, needs no cluster, needs no user ruling, and has a named next step that is not a re-read
of evidence already read.**

| Task | Item | The question this pass answers |
|---|---|---|
| T01 | **OPEN-46** | The blocker this item states is stale. Is the elevator path whole at HEAD? |
| T02 | **OPEN-53** | Why are 874/875 harvest directories missing `.sql`/`.end`? |
| T03 | **OPEN-42 + OPEN-11** | The `.err` files carry per-surface orientation evidence. Does it separate the failures? |
| T04 | **OPEN-38** | Is `LAUNDRYROOMFLR1` the same cause class as OPEN-42, and does it carry the same signature? |
| T05 | — | Reconcile the register, the director prompt and the checklist. |

---

## 2. Hard rules for the executor — these override anything you infer

1. **Never run a git write command.** No `add`, `commit`, `restore`, `checkout --`, `stash`, `rm`.
   Read-only git (`status`, `diff`, `log`, `show`) is fine. Git is handled externally by the user.
2. **Never run compute on the cluster.** No `ssh`, no `srun`, no `sbatch`. Nothing in this plan needs
   Speed. If you believe a task does, STOP and say so.
3. **No EnergyPlus simulation.** Every task here reads artifacts that already exist on disk. If a task
   looks like it needs a new simulation, you have misread it — STOP and report.
4. **Do not edit anything under `docs/docs_DONE/`.** It is a read-only archive.
5. **Do not touch `pyproject.toml`.** A separate change landed there today and a ruling on its
   `--basetemp` pin is still owed by the user.
6. **No `.py` files under `docs/`, ever.** Analysis scripts go in `scripts/analysis/`.
7. **All figure/`.png` output goes to `openubem/outputs/` (flat).** Never under `docs/`.
8. **Measurement tasks do not fix anything.** T02, T03 and T04 are diagnosis only. If you find a bug,
   record it — do not repair it. T01 is a verification, not an implementation.
9. **Controls before results.** Every claim that separates a failing population from a healthy one must
   be run against a background sample of healthy cases first, and the background rate must be reported
   next to the target rate. A statistic that does not separate them is a **finding**, not a failure —
   report it as such. This rule exists because two candidate statistics already died this way under
   OPEN-42 (register §OPEN-42, 2026-08-18 amendment).
10. **Never report a number you did not derive from the artifact.** Do not carry a figure forward from
    the register or from another report without re-deriving it. Where you do carry one, say so.
11. **If the DESIGN or the register is ambiguous, STOP and quote the conflict.** Do not invent.
12. **Append a progress-log entry to §8 of this file after every task**, before starting the next one.

## 3. File layout

**Read (all read-only):**
- `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\<cell>_<mode>\<stem>\` — the local E02 harvest.
  40,800 building directories, each with `eplusout.eio`, `eplusout.err`, and (mostly) `eplusout.sql`
  and `eplusout.end`. This is the path already pinned as `HARVEST_ROOT` in
  `scripts/analysis/open42_zone_geometry.py:31`.
- `openubem/outputs/comparisons/open37_eio_census.csv` — the per-(cell, mode) census that opened OPEN-53.
- `openubem/outputs/comparisons/open42_six_failure_causes.csv` — 30 rows, the 6 buildings × 5 modes.
- `openubem/outputs/comparisons/open41_failure_causes.csv` — the 44 fleet fatals with causes.
- `openubem/outputs/comparisons/open38_subsurface_census.csv` — OPEN-38's existing census.
- `openubem/idf/builder.py`, `openubem/idf/elevators.py`, `openubem/idf/outputs.py`,
  `openubem/results/parser.py`, `openubem/results/carbon.py`, `openubem/results/aggregator.py`.

**Write:**
- `scripts/analysis/open53_missing_sql_census.py` (T02)
- `scripts/analysis/open42_surface_orientation_census.py` (T03)
- `scripts/analysis/open38_laundryroom_signature.py` (T04)
- `openubem/outputs/comparisons/open53_missing_sql_census.csv` (T02)
- `openubem/outputs/comparisons/open42_surface_orientation.csv` (T03)
- `openubem/outputs/comparisons/open38_laundryroom_signature.csv` (T04)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-46_path-verification.md` (T01)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_missing-sql.md` (T02)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_surface-orientation.md` (T03)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38_laundryroom.md` (T04)
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` (T05, and per-item amendments)
- `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` (T05)
- `docs/PROJECT_CHECKLIST.md` (T05)
- §8 of this file (every task)

## 4. Dependency decisions — pinned

- **Interpreter:** `.venv\Scripts\python.exe`. Nothing outside it.
- **Test command:** `.venv\Scripts\python.exe -m pytest -q tests/`. 🔴 A bare root-level `pytest -q`
  was ambiguous until today; `testpaths = ["tests"]` was added to `pyproject.toml` on the user's ruling
  of 2026-08-18, so both forms now collect **1930** tests. **Baseline: 1875 passed, 55 skipped, 0
  failed, 0 errors.** Any other number is a regression and a STOP.
- **`.err` parsing:** plain line scanning, no new dependency. Follow the shape of
  `scripts/analysis/open42_failure_causes.py`.
- **Tabular output:** `pandas`, already a project dependency, as in `open42_zone_geometry.py`.
- **No new third-party package may be added by this plan.**

## 5. Facts this plan rests on, with citations

1. **The harvest is complete for `.eio` and `.err`, short for `.sql` and `.end`.** Against 40,800
   building directories (exact) and 40,800 `.eio`/`.err` (both exact, zero empty), `.sql` = **39,926**
   and `.end` = **39,925**. Gap: **874** and **875**, of which 874 sit in `austin_suburban_fast_zone`
   and `austin_suburban_floor`, one in `nyc_centre_fast_zone`.
   *(register §OPEN-53; `open37_eio_census.csv`)*
2. **All six OPEN-42 buildings fail on runaway zone temperature**, `−444.53 °C` to `+530.25 °C`, one
   uniform cause class across all 16 failing (building × mode) runs, verified from raw `.err`.
   *(register §OPEN-42, 2026-08-13 amendment)*
3. **The failure is zoning-dependent, not building-dependent.** All six succeed under `building` mode;
   the five `la_rural` stems also succeed under `layout_assign`. *(same amendment)*
4. **15 of 16 fatal zones are on the topmost floor**, and their `.eio` zone geometry is byte-identical
   to non-fatal sibling zones below them. **`eplusout.eio` cannot answer why.** A per-surface
   winding/orientation defect was named as the most likely next artifact, outside that task's scope.
   *(register §OPEN-42, 2026-08-18 amendment)*
5. 🔴 **NEW, found by the director 2026-08-18 while scoping this plan — the artifact named in fact 4
   already exists, and it is `eplusout.err`.** The failing runs' `.err` files carry per-surface
   orientation warnings that `.eio` never had:
   `** Warning ** GetVertices: Floor is upside down! Tilt angle=[0.0], should be near 180, Surface="BLOCK PERIMETER_ZONE_3 STOREY 0 FLOOR 0001", in Zone="WAY/472960972_F0_PERIM3".`
   and `** Warning ** GetVertices: Roof/Ceiling is upside down! Tilt angle=[180.0], should be near 0, Surface="BLOCK PERIMETER_ZONE_3 STOREY 2 ROOF 0001", in Zone="WAY/472960972_F2_PERIM3".`
   Verified at `la_rural_auto/way_472960972/eplusout.err:17` and `:19`. **The roof warnings land on
   `STOREY 2` — the topmost floor, which is exactly where fact 4 put 15 of the 16 fatal zones.**
   🔴 **This is stated as a lead, not as a mechanism. T03 exists to test it against a control, and the
   honest outcome may be that it does not separate.**
6. **The `Surfaces` table in `eplusout.sql` is empty for every fatal run** — director-verified:
   `la_rural/way_472960972` gives 0 rows in `auto`, `floor` and `fast_zone` (the three that fatal),
   38 rows in `building` and 102 in `layout_assign` (the two that succeed). **So the SQL route to
   per-surface geometry does not exist for the population we care about, and `.err` is the only
   artifact that carries it.** Do not send a task to `Surfaces` for the failing runs.
7. **OPEN-46's stated blocker is stale.** That item says *"the live tree still emits no elevator
   equipment, so anything simulated today reports `0.0`"*. **`openubem/idf/builder.py:40` now imports
   `assign_elevators` and `:609` calls it** — the wiring was restored on 2026-08-13 when the user's
   ruling `2d` was executed. The item has not been revisited since. *(register §OPEN-46; director-verified
   by grep 2026-08-18)*
8. **All seven `layout_assign` fatals are thermal runaway in one zone, `LAUNDRYROOMFLR1`**, at
   −12,459 to +182,399 °C; zero of the other 37 fatals touch that zone.
   *(register §OPEN-38, 2026-08-11 rewrite)*
9. **The `Base surface does not surround subsurface` message is a Warning, not a Severe, at all 8 sites
   where it occurs, and it kills nothing.** OPEN-38 was originally built on that co-occurrence read as
   a cause. Do not re-import the falsified premise. *(same)*
10. **OPEN-11's six inverted-geometry buildings are the same six buildings as OPEN-42's.**
    `la_rural way_472960972 / 472961034 / 472961088 / 472961091 / 472961171`, `la_urban way_402215469`.
    *(register §OPEN-11, N04 amendment; §OPEN-42, 2026-08-18 amendment)*

---

## 6. Task list

### T01 — OPEN-46: is the elevator path whole at HEAD?

**What.** Establish, from the code and from a test run rather than from any document, whether the
elevator end-use is now complete end to end at HEAD: **load emitted into the IDF → meter requested →
parsed and de-folded into its own column → carried into carbon and the aggregator.** Then either close
OPEN-46 or state exactly which link is still missing.

**Why.** The item's own "why it stays open" paragraph names a blocker that was removed five days later
by a different ruling's execution (fact 7). Nobody has gone back. This is the cheapest possible closure
in the register — or, if a link is genuinely missing, the cheapest possible sharpening.

**How.**
1. Read and cite, by file and line, each of the four links: the call site in `openubem/idf/builder.py`,
   the meter in `openubem/idf/outputs.py`, the parse + de-fold in `openubem/results/parser.py`, the
   column in `openubem/results/carbon.py` and `openubem/results/aggregator.py`.
2. **Prove link 1 by building an IDF, not by reading the call site.** Use the existing test
   `tests/test_step3_orchestrator.py::test_medium_office_idf_contains_elevator_equipment` — the register
   records it as asserting exactly this. Run it and report the result. If it passes, the load reaches a
   built IDF at HEAD; say so with the test's own output as the evidence.
3. **Prove the guard still holds both ways** — the de-fold must not fire when the meter is absent.
   `tests/test_parser_elevators.py` covers this; run it and report pass/fail per test.
4. State the one thing this task cannot prove: whether a **fleet** run would now report elevators.
   No simulation is authorised. Say what would be needed instead of implying it was checked.

**How to test.** `.venv\Scripts\python.exe -m pytest -q tests/test_step3_orchestrator.py tests/test_parser_elevators.py tests/test_elevators.py tests/test_outputs.py -v`. Report the per-test result. Then the
full `pytest -q tests/` baseline (1875/55/0) at the end of the task.

**Deliverable.** `extra/MEASUREMENT_open-46_path-verification.md` + a dated amendment in the register's
OPEN-46 section. **If and only if all four links verify, recommend closure — the director signs it, you
do not close it yourself.**

---

### T02 — OPEN-53: why 874 harvest directories have no `.sql` and no `.end`

**What.** Classify every short directory by reading its `.err`, and report the census.

**Why.** The item was opened on a count alone, deliberately — no `.err` from those directories has ever
been read. Three hypotheses are on the table and they have very different consequences: genuine
EnergyPlus failures (the fleet's failure count is wrong), a harvest-timing artifact (the harvest is
wrong, the runs are fine), or something else.

**How.**
1. Write `scripts/analysis/open53_missing_sql_census.py`. Walk `HARVEST_ROOT`. For every building
   directory, record `cell, mode, stem, has_sql, has_end, err_bytes, err_last_line, terminal_class`.
2. **First, reproduce the census that opened the item**: 40,800 dirs, 40,800 `.eio`, 40,800 `.err`,
   39,926 `.sql`, 39,925 `.end`. 🔴 **If your counts differ, STOP and report — do not proceed on a
   different population than the item was opened on.**
3. Classify each short directory's `.err` terminal state into exactly one of:
   `fatal` (contains `**  Fatal  **`), `completed` (contains `EnergyPlus Completed Successfully`),
   `truncated` (neither — the file ends mid-run), `empty` (0 bytes).
   **Quote the last line verbatim in the CSV**; do not paraphrase.
4. For the `fatal` class, extract the preceding `** Severe **` line, exactly as
   `scripts/analysis/open42_failure_causes.py` does, and report the distinct cause classes with counts.
5. **Control, obligatory:** run the same classifier over a random sample of **200 directories that DO
   have `.sql` and `.end`**, and report their class distribution beside the target's. If `truncated`
   shows up at a comparable rate in the control, the signature is not diagnostic and you must say so.
6. Report the concentration: how the 874 split across `austin_suburban_fast_zone`,
   `austin_suburban_floor` and `nyc_centre_fast_zone`, and what fraction of each of those
   (cell, mode) populations is affected.
7. **State which of the three hypotheses the evidence supports, and which it cannot distinguish.**
   `truncated` with no fatal is consistent with both a killed run and a mid-run fetch — if you cannot
   separate them from this artifact, say "not determinable from `eplusout.err`" and name what would be.

**How to test.** The script is read-only; correctness is shown by (a) the census reproducing the pinned
counts in step 2, and (b) the control in step 5. Both go in the report.

**Deliverable.** `open53_missing_sql_census.csv` + `extra/MEASUREMENT_open-53_missing-sql.md` + a dated
amendment in the register's OPEN-53 section.

---

### T03 — OPEN-42 + OPEN-11: the surface-orientation census

**What.** Census the `GetVertices: … is upside down!` warnings across the whole E02 harvest, and test
whether they separate the 16 failing (building × mode) runs from healthy ones.

**Why.** OPEN-42's last pass concluded that `eplusout.eio` cannot answer why these six buildings'
topmost zones are unstable, and named a per-surface winding/orientation defect as the next artifact to
check. **That artifact turns out to be `eplusout.err`, which was already harvested for all 40,800 runs**
(fact 5). This is also the first evidence that would tie OPEN-11's "inverted geometry" label to a
mechanism rather than to a label — the two items share all six buildings (fact 10).

**How.**
1. Write `scripts/analysis/open42_surface_orientation_census.py`. For a given run directory, parse every
   `GetVertices: <Floor|Roof/Ceiling> is upside down!` line out of `eplusout.err` and capture:
   `surface_class` (Floor / Roof-Ceiling), `tilt_reported`, `surface_name`, `zone_name`, and the storey
   token parsed out of the zone name (`_F0_`, `_F1_`, `_F2_`, …).
2. **Target population:** the 30 runs in `open42_six_failure_causes.csv` (6 buildings × 5 modes), joined
   to their outcome. **Background control:** the same ≥20 successful buildings in `la_rural` and
   `la_urban` across the same five modes that `open42_zone_geometry.py:34-45` already pins — reuse that
   exact sample so the two OPEN-42 measurements are comparable.
3. **Then widen to the whole harvest** — all 40,800 `.err` — and report the fleet-wide rate of the
   warning. 🔴 **This is the number that decides the item.** If most of the fleet carries upside-down
   surfaces, the signature is background noise and OPEN-42 is not explained by it. Report the rate
   before you report any interpretation.
4. The three specific questions to answer, each with its control rate beside it:
   a. Do the **fatal** zones carry an upside-down surface more often than their **non-fatal sibling
      zones in the same run**? (This is the sharpest test — same building, same run, same mode.)
   b. Is the **topmost-storey roof** systematically inverted while lower storeys are not?
   c. Do the **modes that succeed** (`building`, `layout_assign`) carry the warning for the same six
      buildings, or does it appear only in the three modes that fatal? **This is the decisive one:
      fact 3 says the buildings are fine under some zoning modes, so a mechanism must be
      zoning-dependent too. A defect present in all five modes cannot explain a failure in three.**
5. **Report the negative honestly.** If the warning does not separate the populations, that is the
   result, and it retires a hypothesis — write it as a finding, not as a shortfall. Two candidate
   statistics already died this way under this item and the register records both.
6. **Do not fix anything.** If you locate the code that emits inverted floors/roofs, cite it by file and
   line and stop there.

**How to test.** Non-vacuity control, obligatory: show at least one run where the parser reports **zero**
upside-down surfaces, and one where it reports many, and confirm by hand (`grep -c`) that the raw file
agrees with the parser at both. A scanner that returns the same answer everywhere is worthless.

**Deliverable.** `open42_surface_orientation.csv` + `extra/MEASUREMENT_open-42_surface-orientation.md`
+ dated amendments in **both** the OPEN-42 and the OPEN-11 register sections.

---

### T04 — OPEN-38: is `LAUNDRYROOMFLR1` the same defect as OPEN-42?

**What.** Test whether the seven `layout_assign` fatals and the sixteen OPEN-42 fatals are one
mechanism or two.

**Why.** Both are thermal runaway in a single zone, reached from `.err`, in a fleet where every other
failure has a different shape. If they are one mechanism the register is carrying two items for one
defect; if they are two, that has to be said with evidence rather than assumed from the zone name.
OPEN-38's own open question — prototype-library defect, or interaction with substituted geometry — is
exactly the same question T03 asks of OPEN-42.

**How.**
1. Write `scripts/analysis/open38_laundryroom_signature.py`. Re-derive OPEN-38's population from the raw
   `.err` files: which runs fatal in `LAUNDRYROOMFLR1`, at what temperatures, in which cells and modes.
   **Re-derive the seven — do not carry the count from the register.**
2. Run T03's orientation parser over the same runs. Does `LAUNDRYROOMFLR1` carry an upside-down floor or
   roof? Do its non-fatal sibling zones?
3. Compare the two populations on: the fatal message text and its `Severe` predecessor, the zone's
   position in the building, the archetype, and the mode distribution. **State the comparison as a
   table with both populations side by side.**
4. Answer OPEN-38's second open question with the same census: **do unfitted subsurfaces occur in
   buildings that never emit the `Base surface does not surround subsurface` warning?** If `.err`
   cannot see below the warning threshold — and it probably cannot — say so plainly and name the
   artifact that could.
5. **Verdict, in one of three forms, with the evidence for it:** one mechanism, two mechanisms, or not
   determinable from `.err`. **Do not merge or split the register items yourself** — recommend, and the
   director rules.

**How to test.** Same non-vacuity control as T03. Plus: the seven-run population must reproduce exactly;
if you get a different count than seven, that is itself a finding and a STOP for the director.

**Deliverable.** `open38_laundryroom_signature.csv` + `extra/MEASUREMENT_open-38_laundryroom.md` + a
dated amendment in the register's OPEN-38 section.

---

### T05 — Reconcile the three surfaces

**What.** Bring the register, the director prompt and the project checklist into agreement with what
T01–T04 established.

**Why.** The standing instruction is that a task is not finished until the plan log, the register and
the director prompt are all written. T05 is the sweep that catches anything the per-task amendments
missed, plus the arithmetic.

**How.**
1. Re-count the register **programmatically**, by a script over the §1 table body — never by hand, and
   never by trusting the header. Report live rows, struck rows, total, the retired-ID list, and the next
   free ID. The count before this pass: **26 live / 27 struck / 53 total, 25 IDs retired, next free
   `OPEN-54`.** Quote your script's output in the progress log.
2. Reconcile the struck-vs-retired difference. It has been exactly **2** for several passes (OPEN-02 and
   OPEN-28, folded under OPEN-01 and never independently tracked). **If your count makes it anything
   other than 2, STOP** — that is a bookkeeping defect, not a rounding difference.
3. Update the §1 header with this pass's deltas, in the append-and-amend style the register uses: strike
   the old text, do not delete it.
4. Add a new **RESUME box** at the head of the director prompt's green box, superseding the 🟥 box of
   2026-08-18. It must state: what is running (nothing), what is owed (the rulings), what this pass
   closed and opened, and the single most reusable fact learned.
5. 🔴 **Strike, in place, the director prompt's claim that OPEN-01's denominator swap is "the largest
   piece of unstarted work this arc owns" and that "its plan doc has still never been written."** Both
   are false: `PLAN_open-49-and-open-01-2026-08-13.md` T05–T07 implemented the swap, OPEN-01 closed
   2026-08-17 and its ID is retired (register §OPEN-01, and the §1 header's own lineage). The claim
   appears in the 🟥 RESUME box and again in §3's head paragraph. **Strike both, correct in place, do
   not delete** — this is the same rule the register runs on.
6. Update `docs/PROJECT_CHECKLIST.md` — the user's monitoring surface — with one line per closed or
   sharpened item.
7. Run the full suite one final time: `.venv\Scripts\python.exe -m pytest -q tests/`. Expect
   **1875 passed, 55 skipped, 0 failed, 0 errors**. Anything else is a STOP.

**How to test.** The programmatic re-count in step 1 and the suite in step 7 are the tests. Both outputs
go verbatim into the progress log.

---

## 7. Stop-and-report points

- **CP-1 — after T02.** Report: OPEN-46's four links with citations and test output; OPEN-53's census,
  its control, and which hypothesis the evidence supports. **The director re-derives both from raw
  artifacts before signing.** Do not start T03 before CP-1 is signed.
- **CP-2 — after T04.** Report: the fleet-wide upside-down rate (step 3 of T03) **before** any
  interpretation; the three question answers with their control rates; the OPEN-38 verdict. **Do not
  start T05 before CP-2 is signed** — T05 writes conclusions into the register and must not write an
  unaudited one.
- **CP-3 — after T05.** Report: the programmatic re-count, the struck-vs-retired reconciliation, and the
  final suite line. This closes the plan.

🔴 **A checkpoint that cannot be re-derived from raw artifacts on disk is a STOP, not a formality.**

---

## 8. Progress log

*(One entry per completed task. Format: `#### TXX — <title> — completed YYYY-MM-DD`, then
Artifacts / Deviations / Test status / Notes.)*

#### T02 — OPEN-53: why 874 harvest directories have no `.sql`/`.end` — completed 2026-08-18

**Artifacts.**
- `scripts/analysis/open53_missing_sql_census.py` (new)
- `openubem/outputs/comparisons/open53_missing_sql_census.csv` (new, 40,800 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_missing-sql.md` (new)
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — OPEN-53 §1 row and §-section
  amended (strike-and-correct style, nothing deleted)

**Deviations.** None from the plan's How. Step 2's reproduction matched the pinned census exactly
(no STOP triggered). One scope boundary hit and reported rather than pushed through: neither
`.eio` nor `.err` records `Output:SQLite` request status, so the harvest-artifact-vs-IDF-config
sub-question inside hypothesis 2 is reported as not determinable from these artifacts, per hard
rule 11 (no invention) and the plan's own instruction in step 7 to name what is not determinable.

**Test status.** Script is read-only measurement; no pytest run (per director's order — a
concurrent full-suite run is in flight elsewhere and shares the `.pytest_tmp` basetemp pin,
OPEN-52). Correctness shown by: (a) step 2's from-scratch reproduction matching plan §5 fact 1
exactly — `n_dirs=40800 n_eio=40800 n_eio_empty=0 n_err=40800 n_sql=39926 n_end=39925`; (b) the
200-directory control classified alongside the 875-directory target, as step 5 requires.

**Notes.** Census counts: dirs/`.eio`/`.err`/`.sql`/`.end` = 40800/40800/40800/39926/39925,
matching §5 fact 1 exactly. Short-directory (union of missing `.sql` or `.end`) population = 875.
Classification: 874 `completed`, 1 `truncated`, 0 `fatal`, 0 `empty`. Control (200 healthy
directories, `random.Random(53)`): 200 `completed`, 0 `truncated`, 0 `fatal`, 0 `empty` — the
`completed` rate does not separate target (99.9%) from control (100.0%), reported as a finding per
hard rule 9. Fatal cause table is empty (n_fatal=0 in the target population — nothing to extract).
Concentration: `austin_suburban_fast_zone` 437/437 (100.0%), `austin_suburban_floor` 437/437
(100.0%), `nyc_centre_fast_zone` 1/738 (0.1%) — full detail and verdict in the deliverable.
Verdict: hypothesis 1 (genuine EnergyPlus failure) is retired by the control comparison;
hypothesis 2 (harvest-timing/config artifact) is supported for the 874-directory population but
this artifact set cannot distinguish IDF-level from harvest/copy-level cause within it; the single
`nyc_centre_fast_zone` directory is a separate, undetermined case. Full writeup:
`extra/MEASUREMENT_open-53_missing-sql.md`.

#### CP-1 — director audit and sign-off — 2026-08-18

**Re-derived from raw artifacts, not from the executor report.**

Independent recount over `HARVEST_ROOT` (director, `ls`-based, not the executor script): exactly
three batches deviate — `austin_suburban_fast_zone` 437 dirs / 0 `.sql` / 0 `.end`,
`austin_suburban_floor` 437 dirs / 0 `.sql` / 0 `.end`, `nyc_centre_fast_zone` 738 dirs / 738
`.sql` / 737 `.end`. Short population = 874 missing both + 1 missing `.end` only = **875**.
Confirmed. Completion-marker recount over the two dead batches: 437/437 and 437/437 carry
`EnergyPlus Completed Successfully`. Confirmed. The single truncated case
(`nyc_centre_fast_zone/way_1240348353`) confirmed: `.err` stops mid-warning at
`ZoneInfiltration:DesignFlowRate="INFILTRATION_WAY/1240348353_F88_CORE"` with no trailing content,
`.sql` present at 208 KB (partial), `.end` absent — an externally killed run on an 88+ storey
building, not an EnergyPlus-managed exit.

**The report is accurate. One verdict is superseded, and one new fact was found.**

1. **Hypothesis 2 is now determinable, and the answer is neither of the two branches the report
   offered.** The files were produced, harvested, and inventoried — then deleted afterwards.
   Evidence: (a) `openubem/outputs/comparisons/e02_corpus_inventory.csv` (mtime 2026-08-11 20:58)
   records `n_end=437` for both `austin_suburban,fast_zone` and `austin_suburban,floor`, so `.end`
   files existed on 2026-08-11 and therefore `Output:SQLite` was requested — the IDF-config branch
   is retired; (b) every one of the 874 run directories carries an identical directory mtime of
   **2026-08-17 16:21**, against 2026-08-10 21:38/21:58 for the healthy sibling batches — a
   directory mtime changes only when an entry is added or removed, so the removal was a single
   sweep at that instant; (c) no code in `scripts/` or `openubem/` deletes `eplusout.sql` or
   `eplusout.end` (grep for `unlink`/`rmtree`/`os.remove` against those names returns nothing), so
   the sweep was external to this repository.

2. **The same sweep emptied the entire IDF corpus.** Every `idfs/` directory under
   `%LOCALAPPDATA%\Temp\ubem_e02_fleet\<cell>\step3_<mode>\` is empty, all stamped
   2026-08-17 16:21:16 — checked across four cells and four modes, `n=0` in all sixteen. Combined
   with (1) this reads as an external disk-space reclamation that targeted the largest files
   (IDFs fleet-wide, plus `.sql` in two harvest batches) and stopped once space was freed. This
   was not previously recorded anywhere in the arc.

3. **The published fleet numbers are untouched.** `open01_denominator_swap.csv` carries
   `new_eui_kwh_m2` for 437/437 buildings under both `austin_suburban,fast_zone` and
   `austin_suburban,floor`. Results were parsed before the sweep, so the adopted baseline of
   157.1 kWh/m2 pooled does not depend on the deleted files. OPEN-53 is an artifact-custody
   finding, not a results defect.

**Consequences carried forward.**
- `e02_corpus_inventory.csv` is now falsified by disk for two rows (`n_end=437` where disk holds
  0). It must be annotated as a 2026-08-11 snapshot, not current state — folded into T05.
- IDF-based per-surface geometry is no longer available for T03/OPEN-42. The 40,800 `.err` files
  survive intact and remain the only per-surface artifact. T03 proceeds unchanged.
- The corpus is eroding under an external process. Any future task depending on `%LOCALAPPDATA%`
  E02 artifacts must re-verify presence before planning around them.

**CP-1: signed. T03 released.** T01 remains held — a full `pytest` run started 11:48 is still live
(PID 19328, 964 s CPU at time of audit), and T01 runs pytest against the shared `--basetemp`
pin (OPEN-52). T01 is released only once that run exits.

#### T03 — OPEN-42 + OPEN-11: the surface-orientation census — completed 2026-08-18

**Artifacts.**
- `scripts/analysis/open42_surface_orientation_census.py` (new)
- `openubem/outputs/comparisons/open42_surface_orientation.csv` (new, 696 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_surface-orientation.md` (new)
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — dated amendments in both the
  OPEN-42 section and the §1 OPEN-42 summary row, and both the OPEN-11 section and the §1 OPEN-11
  summary row (strike-and-correct style, nothing deleted)

**Deviations.** None from the plan's How. Two implementation bugs were caught and fixed before the
first valid run (not deviations from the plan, just script debugging): the `GetVertices` regex
initially required the `Tilt angle=[...]` bracket to be followed immediately by a comma then
`Surface=`, but the real line has `, should be near <N>,` in between — widened to a non-greedy
`.*?` and re-verified against the raw file; and `open42_zone_geometry.py`'s `mark_top_floor(df,
group_cols)` raises on an empty `group_cols` list (`ValueError: No group keys passed!`) when called
per-single-run — fixed by adding a constant grouping column (`_g`) before each per-run call, which
does not change that function's own code (imported, not edited). Per hard rule 8 this is diagnosis
tooling, not the arc's feature code, and the plan's rule against fixing applies to the artifact
under investigation, not to a bug in the executor's own new script.

**Test status.** Script is read-only measurement; no pytest run (absolute rule for this task —
the concurrent full-suite run, PID 19328, is still live and shares the `.pytest_tmp` basetemp pin,
OPEN-52). Correctness shown by the obligatory non-vacuity control: `la_rural_building/
way_472960972/eplusout.err` — parser 0, `grep -c 'upside down'` 0, agree; `la_rural_auto/
way_472960972/eplusout.err` — parser 144, `grep -c 'upside down'` 144, agree. PASS.

**Notes.**

**Fleet-wide rate (reported first, per the plan's rule): 8,287 / 40,800 run directories (20.3113%)
carry >=1 upside-down warning.** This is fully explained by one fact, confirmed by a per-`(cell,
mode)` breakdown across all 12 cells: the warning fires on **100.00% of all 8,160 `auto`-mode runs**
fleet-wide, every cell, whether the run fails or not (0/8,160 `building`, 0/8,160 `floor`, 124/8,160
= 1.52% `fast_zone`, 3/8,160 = 0.04% `layout_assign`; 8,160+124+3 = 8,287 exactly). Only 8 of the
8,160 `auto` runs actually fail. **The hypothesis named in the plan's fact 5 is retired — this is
background noise across the fleet for the mode in which it occurs, not a marker of the six failing
buildings.**

The three questions, each against its control, all came back negative or inverted:
- **4a** (fatal zone vs. non-fatal siblings, same run): fatal zone carries the warning in **1/16**
  failing runs (6.2%) vs. **167/359** (46.5%) for its own run's non-fatal sibling zones — the fatal
  zone is *less* likely to carry it, the inverse of a causal signal.
- **4b** (topmost-storey roof vs. lower storeys): target population shows no separation (41.7% top
  vs. 40.5% non-top); the background sample shows a *larger* gap (26.8% vs. 14.1%) than the target
  does.
- **4c** (decisive — failing vs. succeeding modes): the warning fires in exactly one of the three
  failing modes. All 6 buildings carry it in `auto` (6/6, 100%) and **none** in `fast_zone` (0/6) or
  `floor` (0/6) — the same two failing modes, identical thermal-runaway mechanism, zero warnings.

Candidate mechanism located and cited, not fixed: `openubem/idf/surfaces.py:223-234`
(`_coreperim_has_inverted_winding`) is already computed but deliberately unused as a defect check —
its caller's docstring at `:671-681` (`_rebuild_degenerate_coreperim`) states "EnergyPlus convention
always uses negative signed-area (CW winding) for floor surfaces; checking sign would produce false
positives on healthy buildings" — in-code corroboration for the same conclusion the census reached
independently.

**Verdict: the signature does not separate the failing population from healthy runs. OPEN-42 stays
OPEN** — both `eplusout.eio` (T05, 2026-08-18) and now `eplusout.err`'s orientation warnings have
been read and both come back "not determinable" or "does not separate"; no further local artifact
is named. **OPEN-11's "inverted geometry" label is not corroborated by this signature** — the six
buildings it names are indistinguishable from the other 8,154 `auto`-mode buildings by this measure.
OPEN-11 itself is unchanged (its subject, the un-reapplied Phase-E remediation, was not touched by
this task). Full detail: `extra/MEASUREMENT_open-42_surface-orientation.md`.

#### CP-2 (partial — T03 only, T04 outstanding) — director audit and sign-off — 2026-08-18

**Re-derived from raw artifacts, not from the executor report.**

Fleet-wide rate by mode, independent recount over `la_rural`, `nyc_rural`, `austin_rural` (592 runs
per mode): `auto` **592/592 (100%)**, `building` **0/592**, `floor` **0/592**, `layout_assign`
**0/592**, `fast_zone` **16/592 (2.7%)**. Consistent with the executor's fleet figures. Confirmed.

Question 4c, re-derived directly from `open42_six_failure_causes.csv` joined to the raw `.err`
files, all 30 rows: the warning fires in **6/6 `auto` runs** and in **0/5 `fast_zone`** and
**0/5 `floor`** runs — the two modes carrying 10 of the 16 fatals. Confirmed.

Question 4a, re-derived on the reference run `la_rural_auto/way_472960972`: the fatal zone
`WAY/472960972_F2_CORE` carries **zero** upside-down surfaces, while **54 perimeter zones** in the
same run carry 144 warning lines between them. The signature fires everywhere *except* the zone
that actually fails. The executor called this "inverted, not supportive"; it is stronger than that
— it is a direct refutation.

**T03's verdict is upheld. The orientation hypothesis is retired.** Note for the record that this
lead was raised by the director when scoping the plan (§5 fact 5); it was wrong, and the task was
built to disprove it, which it did. `.err` is now the second artifact after `.eio` to come back
"does not separate."

**A structural fact the census surfaced that no prior pass recorded.**

All 16 fatal zones sit on the **topmost storey** — `F2` for the five three-storey `la_rural`
buildings, `F3` for `la_urban/way_402215469`. Without exception. The *zone name* varies with the
zoning mode (`F2_CORE` under `auto`, `F2_PERIM<n>` under `fast_zone`, `F2_WHOLE` under `floor`),
which is why no earlier pass saw it — the varying name concealed an invariant location. Reported
temperatures run from **-444.53 °C to +530.25 °C**, i.e. unbounded runaway, not a marginal
imbalance.

Zone structure per mode for `way_472960972`, read from each run's own `.eio`:

| mode | zones | topmost-storey zone exists | outcome |
|---|---|---|---|
| `auto` | 57 (`F0/F1/F2` × core+perimeter) | yes | **fatal** |
| `fast_zone` | 57 (same shape) | yes | **fatal** |
| `floor` | 3 (`F0_WHOLE`, `F1_WHOLE`, `F2_WHOLE`) | yes | **fatal** |
| `building` | 1 (`F0_WHOLE`, whole building) | no | survives |
| `layout_assign` | 3 (`ZONE1 OFFICE`, `ZONE2 FINE STORAGE`, `ZONE3 BULK STORAGE`) | no — substituted prototype, OSM storeys not extruded | survives |

The two surviving modes are exactly the two that never build a thermal zone from the building's own
topmost storey: `building` collapses the whole building into one zone, and `layout_assign`
substitutes a DOE prototype layout and discards the extruded storeys altogether. Every mode that
does give the topmost storey its own zone fatals.

**This reframes OPEN-42.** The question is no longer "which zone is inverted" but **"what is wrong
with the topmost-storey geometry of these six buildings such that any zone built from it runs
away."** Mode is not the variable; it only decides whether that storey gets a zone at all. This is
recorded as a director finding, not a closure — it is a reframing, and OPEN-42 stays open.

**CP-2 partial: T03 signed. T04 released**, carrying the topmost-storey reframe as its comparison
axis.

#### T04 — OPEN-38: is `LAUNDRYROOMFLR1` the same defect as OPEN-42? — completed 2026-08-18

**Artifacts.**
- `scripts/analysis/open38_laundryroom_signature.py` (new)
- `openubem/outputs/comparisons/open38_laundryroom_signature.csv` (new, 7 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38_laundryroom.md` (new)
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — dated amendment in the OPEN-38
  section and the §1 OPEN-38 summary row (strike-and-correct style, nothing deleted)

**Deviations.** None from the plan's How. One addition beyond the plan's explicit step list, within
its scope: step 3 asks for the comparison to include "the archetype," so the script also identifies
which `ARCHETYPE_IDF_MAP` baseline IDF defines a zone literally named `LaundryRoomFlr1` (scanning
`config.BASELINE_IDF_DIR`) rather than asserting the archetype from the zone-name convention alone —
this is a read of existing code/data (`openubem/geometry/layout_assigner.py`'s own registry), not a
new dependency or a fix.

**Test status.** Script is read-only measurement; no pytest run (per this dispatch's hard constraint
— a concurrent full-suite run was in flight elsewhere and OPEN-52 makes concurrent pytest unsafe on
the shared `--basetemp`). Correctness shown by the obligatory non-vacuity control (reused from T03,
re-run independently here): `la_rural_building/way_472960972/eplusout.err` — parser 0, `grep -c
'upside down'` 0, agree; `la_rural_auto/way_472960972/eplusout.err` — parser 144, `grep -c 'upside
down'` 144, agree. PASS. Plus the population re-derivation itself: scanning all 8,160 `layout_assign`
run directories fresh (not the register's count) reproduced exactly 7 — no STOP triggered.

**Notes.**

**Population re-derived: 7, confirmed** (`la_centre/way_427942886`, `la_urban/relation_6374725`,
`la_urban/way_401910463`, `la_urban/way_428846131`, `nyc_rural/way_965718400`,
`nyc_rural/way_965718402`, `nyc_rural/way_965718403`), from a fresh scan of all 8,160 `layout_assign`
directories — matches the register's prior count but was not carried from it.

**Comparison table (OPEN-38 vs. OPEN-42), every dimension disagrees:**

| dimension | OPEN-38 (7) | OPEN-42 (16) |
|---|---|---|
| Severe class | `CalcHeatBalanceInsideSurf`, n_severe=1 always | `Temperature (low\|high) out of bounds`, up to 24 |
| Temperature range | −59,865.37 to +182,399.27 °C | −444.53 to +530.25 °C |
| Zone position (`.eio` z-geometry) | bottommost storey, 7/7 (0.00–3.35 m of 0.00–11.58 m) | topmost storey, 15/16 |
| Geometry origin | substituted `SmallHotel` DOE prototype (identified by scanning `ARCHETYPE_IDF_MAP`'s baseline IDFs for a zone named `LaundryRoomFlr1`) | building's own OSM-extruded geometry |
| Mode | `layout_assign` only (0/8,160 elsewhere) | `auto`/`fast_zone`/`floor` only, never `layout_assign` |
| T03 orientation warning on fatal zone | 0/7 | 1/16 |

**Unfitted-subsurface question: not determinable from `eplusout.err`.** All 7 re-derived fatals also
carry the `Base surface does not surround subsurface` warning (fresh re-grep matches
`open38_subsurface_census.csv` exactly, 7/7, plus the known non-fatal control
`nyc_rural/way_965718401`). `.err` can only report a subsurface as malformed once EnergyPlus's own
`CHKSBS` routine crosses its internal fit-tolerance threshold; an unfitted subsurface inside that
threshold prints nothing anywhere in `.err`. Answering the question needs the actual IDF geometry,
which does not exist on disk — the entire E02 IDF corpus was emptied by the 2026-08-17 external disk
sweep (OPEN-53's T02 finding, carried here per this dispatch's raw-data note, not re-derived).

**Verdict: two mechanisms, not one — recommendation only, director rules.** Population count,
message class, zone position, geometry origin, and mode are all independently confirmed distinct.
Full detail: `extra/MEASUREMENT_open-38_laundryroom.md`.

#### T01 — OPEN-46: is the elevator path whole at HEAD? — completed 2026-08-18

**Artifacts.**
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-46_path-verification.md` (already on disk; this
  entry closes the bookkeeping the plan required after it)
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — OPEN-46's own §-section (T05
  passage corrected in strike-and-correct style; a new `#### ✅ CLOSED 2026-08-18` closure subsection
  appended), OPEN-46's §1 table row (struck, closure appended), and the §1 header count line (new
  dated extension bracket)

**Deviations.** None from the plan's How. T01 was held behind a concurrent full-suite pytest run (PID
19328, OPEN-52's shared `--basetemp` pin) per CP-1's sign-off note in this file; it was released once
that run exited. This dispatch then ran the full suite itself (A1, foreground) rather than reusing any
earlier run's number, per hard rule 10 (never carry a number forward without re-deriving it).

**Test status.** Targeted (already recorded in the measurement doc): `.venv\Scripts\python.exe -m
pytest -q tests/test_step3_orchestrator.py tests/test_parser_elevators.py tests/test_elevators.py
tests/test_outputs.py -v` — **65 passed, 0 failed** (`test_step3_orchestrator.py` 18,
`test_parser_elevators.py` 8, `test_elevators.py` 28, `test_outputs.py` 11).

Full suite (A1, foreground, `.venv\Scripts\python.exe -m pytest -q tests/`), run 2026-08-18:

```
1875 passed, 55 skipped, 11 warnings in 1572.28s (0:26:12)
```

Matches the pinned baseline (1875 passed, 55 skipped, 0 failed, 0 errors) exactly — the 11 warnings are
non-fatal (a `DeprecationWarning` from `datetime.strptime` in `openubem/results/parser.py:154` and
similar, no test failures attached).

**Notes.** All four elevator-reporting links (load emitted into the IDF → meter requested → parsed and
de-folded into its own column → carried into carbon and the aggregator) verified at HEAD, both by
file:line citation and by live test runs — full citations in
`extra/MEASUREMENT_open-46_path-verification.md`. One documentary defect found, not a code defect: the
plan's named proof test, `tests/test_step3_orchestrator.py::test_medium_office_idf_contains_elevator_equipment`,
does not exist in the live tree and never has — it exists only in the archived mirror
(`docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/test_step3_orchestrator.py:90`).
`tests/test_builder_elevators_wired.py` (committed at `6aeebb0`) proves the same load-wiring fact live
and passes, so the chain was never actually broken by this gap, only mis-cited. The register's own
OPEN-46 T05 passage, which read as claiming a live test that never existed, is corrected in
strike-and-correct style in its own section.

**OPEN-46 CLOSED + ID RETIRED 2026-08-18**, per the measurement doc's recommendation, now that A1
confirms the full-suite baseline matches exactly.

#### T05 — Reconcile the register, the director prompt and the checklist — completed 2026-08-18

**Artifacts.**
- `scripts/analysis/open_register_recount_2026-08-18.py` (new) — programmatic recount script over the
  register's §1 table body
- `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — §1 header count line extended
  (dated bracket, strike-and-correct on the "26 tracked items" figure); OPEN-38 and OPEN-42
  §-sections and §1 rows carry new director-ruling amendments (stay-separate, reframe); OPEN-53
  §-section and §1 row carry the custody-risk ruling and the `e02_corpus_inventory.csv` snapshot
  annotation
- `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` — the 🟧 RESUME box's task
  table and "first thing the next session does" paragraph updated in place; nothing else in the box
  touched
- `docs/PROJECT_CHECKLIST.md` — new dated amendment, one line per closed/sharpened item
- §8 of this file (this entry)

**Deviations.** None from the plan's How, except step 7 as the plan itself directs: the final full
suite was **not** re-run a second time — A1 (T01's progress-log entry, above) already ran it in the
foreground this session, and step 7 is explicitly satisfied by referencing that run rather than
duplicating it (OPEN-52 also makes a second concurrent-adjacent run needless risk for no new
information).

**Test status — step 1, the programmatic recount, quoted verbatim:**

```
Table body: lines 633-688 (1-indexed), 53 row-lines
Total OPEN-NN rows found: 53
Live (non-struck) rows: 25
Struck rows: 28
ID range: OPEN-01 .. OPEN-53
Missing IDs in sequence: none
Duplicate IDs: none
Next free item ID: OPEN-54

Struck IDs: OPEN-01, OPEN-02, OPEN-04, OPEN-05, OPEN-06, OPEN-21, OPEN-22, OPEN-23, OPEN-24, OPEN-25, OPEN-26, OPEN-28, OPEN-30, OPEN-31, OPEN-32, OPEN-33, OPEN-34, OPEN-36, OPEN-37, OPEN-39, OPEN-40, OPEN-41, OPEN-43, OPEN-44, OPEN-45, OPEN-46, OPEN-51, OPEN-50
```

Run once before this pass's OPEN-46 closure edits landed (reproduced the prior pinned count exactly:
26 live / 27 struck / 53 total, next free `OPEN-54`), and once after (above) — the only change between
the two runs is OPEN-46 moving from the live list to the struck list, as expected from closing exactly
one item and opening none.

**Step 2 — struck-vs-retired arithmetic:** struck rows = 28, retired IDs = 26 (25 prior + OPEN-46 this
pass). **28 − 26 = 2**, exactly OPEN-02 and OPEN-28 (folded under OPEN-01, never independently
tracked) — no STOP triggered.

**Step 7 (referenced, not re-run):** see T01's progress-log entry, above —
`1875 passed, 55 skipped, 11 warnings in 1572.28s (0:26:12)`, matching the 1875/55/0/0 baseline.

**Notes.**

- **Step 3 (§1 header).** A new dated bracket, *"Extended 2026-08-18 (evening), T01/T05 of
  `implemenation/PLAN_four-items-2026-08-18.md`"*, appended after the existing 2026-08-18 T06 bracket
  at the end of the §1 summary line, recording the −1 net (OPEN-46 closed, nothing opened) and the new
  25/28/53 counts. The superseded "26 tracked items" figure is struck in place, not deleted.
- **Steps 4–5 were already done by the director before this dispatch**, per the plan's own instruction
  — the director prompt already carried the 🟧 RESUME box and the false OPEN-01 claim already struck in
  both places (§ head paragraph and the old 🟥 box). This dispatch's only edit to that file was the
  🟧 box's task table and its "first thing the next session does" paragraph, updated to show T01 and T05
  both done, OPEN-46 closed, the OPEN-38/OPEN-42 rulings recorded, and the suite line — everything else
  in the box left untouched, per instruction.
- **Step 6 (checklist).** One dated amendment added to `docs/PROJECT_CHECKLIST.md` with one line per
  item this pass touched (OPEN-46 closed, OPEN-38/OPEN-42/OPEN-53 sharpened via ruling), plus the
  register arithmetic and the suite line.
- **STEP B rulings (director, not this task's own judgement, entered per the dispatch instructions):**
  OPEN-38 and OPEN-42 stay separate items, T04's recommendation accepted; OPEN-42 is reframed (not
  closed) to "what is wrong with the topmost-storey geometry such that any zone built from it runs
  away," with zoning mode recorded as deciding only whether that storey gets a zone at all; OPEN-53
  stays open narrowed to the custody risk, its original question answered, `e02_corpus_inventory.csv`
  annotated as a 2026-08-11 snapshot; OPEN-11 received no new ruling, T03's amendment stands unchanged.

**This closes T05. CP-3 (the programmatic re-count, the struck-vs-retired reconciliation, and the
final suite line, all above) is ready for the director's sign-off — this task does not sign it.**

#### CP-3 — director audit and sign-off — 2026-08-18

**CP-3: signed. T01 and T05 accepted. This plan is CLOSED.** Every claim below was re-derived by the
director from the files on disk, not read off the executor's report.

**1. The full-suite line, and its provenance.** `1875 passed, 55 skipped, 11 warnings in 1572.28s
(0:26:12)` — matches the pinned baseline 1875 / 55 / 0 / 0. Provenance checked rather than trusted: the
run was observed live mid-audit as PID 26444, started 13:34:26, holding 1293 s of CPU at the time of
the check, which is consistent with the 1572 s wall time reported at exit. It was the only pytest
session on the machine, as OPEN-52's shared `--basetemp` pin requires. **OPEN-46's closure condition is
therefore satisfied on evidence, and OPEN-46 closes.**

**2. No placeholder survived.** The executor wrote the register, checklist and plan-doc text before the
suite finished, carrying a literal `[[A1_SUITE_LINE]]` token, and substituted the real line on exit.
`grep -rn 'A1_SUITE_LINE' docs/ scripts/` now returns **nothing**. Recorded as a deviation in method,
not in substance — it is sound practice only because the token is greppable and was verified absent;
had the run failed, the register would have briefly carried an unfalsifiable claim.

**3. The register re-count, re-derived independently.** The director did not run the executor's script.
Counting the first column of the §1 table body directly: **25 live / 28 struck / 53 total**, and the 53
row identifiers are exactly `OPEN-01`…`OPEN-53`, each appearing **once** — no gap, no duplicate. This
matches `scripts/analysis/open_register_recount_2026-08-18.py`'s output line for line.

**4. The struck-vs-retired reconciliation holds.** 28 struck rows against 26 retired IDs (25 going in,
plus OPEN-46 this pass) = **exactly 2**, and the 2 are still OPEN-02 and OPEN-28, folded under OPEN-01
and never independently tracked. OPEN-46 moved from live to struck and was retired in the same edit, so
the gap neither widened nor narrowed. **The must-be-exactly-2 STOP condition did not trigger.**
**Next free item ID: `OPEN-54`** — no item was opened this pass.

**5. Bookkeeping complete.** §8 of this file now carries one entry per task — T01, T02, T03, T04, T05 —
including the T01 entry whose absence was the reason this dispatch existed. The §1 OPEN-46 row is
struck, the OPEN-46 §-section carries its closure subsection, and `docs/PROJECT_CHECKLIST.md` carries
the dated amendment with the suite line.

**6. Files touched are exactly the authorized set.** `git status` shows the four modified docs, the four
measurement docs, this plan, three comparison CSVs, three analysis scripts and the new recount script.
`pyproject.toml`'s `testpaths` change pre-dates this dispatch — it is ruling `3b`'s remedy, uncommitted
by this arc's git prohibition. **No feature code was written and no git write command was run.**

**Outcome of the four-item pass.** One item closed and retired (**OPEN-46**). Three sharpened and kept
open by director ruling: **OPEN-38** stays separate from OPEN-42 on five disagreeing axes; **OPEN-42**
is reframed to the topmost-storey geometry question with `.eio` and `.err` both exhausted; **OPEN-53**
is narrowed from "why are the files missing" — answered — to the artifact-custody risk that remains.
**The most transferable result is not any of the four: the E02 artifact corpus is eroding under a
process outside this repository, so any future plan must re-verify artifact presence at planning time
rather than cite `e02_corpus_inventory.csv`.**
