# PLAN — OPEN-52 remedy + four items — 2026-08-18 (night)

**Slug:** `open-52-and-four-items-2026-08-18`
**Written:** 2026-08-18 (night), by the director, on the user's instruction
*"tu peux choisir OPEN-52, vas-y continuer jusqu'à la fin. et aussi, est-ce que si possible
choisir 5 tâches ouverts pour créer un plan d'implémentation."*
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`
**Director prompt:** `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`
**Predecessor:** `implemenation/previous/PLAN_four-items-2026-08-18.md` — CLOSED at CP-3, 2026-08-18.
**Register state at write time:** 25 live rows, 28 struck, 53 total (OPEN-01…OPEN-53),
26 IDs retired, next free `OPEN-54`.

**The five items:** **OPEN-52**, **OPEN-07** (+ OPEN-38's remaining sub-question),
**OPEN-08**, **OPEN-29**, **OPEN-53**.

---

## 1. Why these five

Each was chosen because a **specific blocker recorded in the register is now stale or now
answerable on this machine**, and none of them needs the cluster, the network, or a ruling
the user has not given.

| Task | Item | What changed since the register last touched it |
|---|---|---|
| T01 | **OPEN-52** | The owed ruling `3a` is **now given** — §4.1 below. It was the only thing missing. |
| T02 | **OPEN-07** + OPEN-38 | The register says *"no T20 IDF survives locally to diff a multiplier against"*. **That is false at HEAD** — `scratchpad/e-la-20-investigation/i03/work_part1/` holds a paired A/B build of two of OPEN-07's three buildings, under **both** classifications. Director-verified on disk 2026-08-18. |
| T03 | **OPEN-08** | Its stated blocker is *"vintage disagreement remains unquantifiable — no harvest persists a `vintage_standard` column, see new item OPEN-30"*. **OPEN-30 closed 2026-08-11**, demonstrated on 60/60 E02 manifests, 40,800 rows, 0 nulls. The blocker is stale — the same shape OPEN-46's was. |
| T04 | **OPEN-29** | The forward-trace is on disk (13 rows) and the register carries *"9 of 12 genuinely still open"*, but that trace is dated **2026-08-06**. Twelve days and eight passes have landed since; one candidate (`E-LA-16`) provably closed — OPEN-51 adjudicated it and retired 2026-08-18. |
| T05 | **OPEN-53** | Narrowed on 2026-08-18 from cause (answered) to **custody**. The remedy is small, local, and fully specified in §6-T05. |

---

## 2. Hard rules for the executor

1. **Never run a git write command.** No `add`, `commit`, `restore`, `checkout`, `stash`, `push`.
   Git is handled outside this session. Read-only git (`log`, `show`, `diff`, `grep`) is fine.
2. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, or anything under `docs/docs_DONE/`,
   `docs/docs_main/`, `docs/docs_stepN/`.
3. **No `.py` file may be created anywhere under `docs/`, ever.** Analysis scripts go in
   `scripts/analysis/`.
4. **Never run compute on the cluster.** No `ssh`, no `srun`, no `sbatch`. Every task here is local.
5. **No live-network call.** No Overture pull, no OSM fetch, no HTTP.
6. 🔴 **ONE pytest session at a time, repo-wide.** This is OPEN-52's own hazard and it stays live
   until T01 lands. Before starting any pytest run, check that no other is running. **The rule
   relaxes only after T01's verifications pass — not before.**
7. **Do not run the full suite in the background and write conclusions before it finishes.**
   The predecessor plan's executor did this and it is recorded as a method deviation.
   **Run the gate first, read its real output, then write.**
8. **Measure before you remedy.** T02, T03 and T04 are diagnosis tasks: **no production code
   changes in them**, no fixes, no "while I was there". T01 and T05 are the only tasks that change
   anything, and both are scoped to the exact lines named in §6.
9. **Record silence as a result.** If a measurement does not separate, say so plainly and stop.
   A refuted lead is a finding. Do not rescue a hypothesis.
10. **Amend the register by striking, never by deleting.** Wrong text stays, struck, with the
    correction after it and a date.
11. **Stop at the checkpoints in §7** and report. Do not run past one.

---

## 3. File layout

| Purpose | Path |
|---|---|
| This plan | `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md` |
| Register (amend) | `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` |
| Support docs | `docs/docs_ACTIVE/openings/extra/` |
| Analysis scripts | `scripts/analysis/` |
| CSV outputs | `openubem/outputs/comparisons/` |
| Checklist line | `docs/PROJECT_CHECKLIST.md` |
| Director prompt | `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` |

New files this plan authorises, and no others:

- `conftest.py` at the repository root (T01 only)
- `scripts/analysis/open07_smallhotel_idf_diff.py`
- `scripts/analysis/open08_vintage_reproducibility.py`
- `scripts/analysis/open29_status_retrace_2026-08-18.py`
- `docs/docs_ACTIVE/openings/extra/FIX_open-52_temproot-remedy.md`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-07_smallhotel-idf-diff.md`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-08_vintage-reproducibility.md`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-29_status-retrace.md`
- CSVs under `openubem/outputs/comparisons/`, each named after the script that emits it.

---

## 4. Dependency decisions — pinned

### 4.1 🔴 RULING `3a` — OPEN-52's remedy shape. **Given by the director, 2026-08-18.**

The user delegated this ruling explicitly (*"tu peux choisir OPEN-52"*). It is therefore
**decided, not owed**, and T01 implements it as written.

**The remedy is (c): move pytest's temp root inside the repository, and let pytest number it
per session.**

Concretely, two changes and nothing else:

1. **Delete** `addopts = "--basetemp=.pytest_tmp"` from `pyproject.toml`.
2. **Add a repository-root `conftest.py`** that sets `PYTEST_DEBUG_TEMPROOT` to the absolute path
   of `<repo>/.pytest_tmp` **before pytest's temp factory initialises**.

**Resulting layout:** `<repo>/.pytest_tmp/pytest-of-<user>/pytest-<n>/`.

**Why this shape — verified in pytest's own source (pytest 9.0.3, `_pytest/tmpdir.py`,
`TempPathFactory.getbasetemp`), not assumed:**

- The `--basetemp` branch does `if basetemp.exists(): rm_rf(basetemp)` — **unconditionally, at
  session start, on a fixed path**. That single line *is* OPEN-52's collision, now confirmed at
  source and not only from the incident.
- The other branch reads `PYTEST_DEBUG_TEMPROOT` (falling back to `tempfile.gettempdir()`), builds
  `<temproot>/pytest-of-<user>`, and allocates the session directory with `make_numbered_dir(...)`
  — **per-session, monotonically numbered, never wiped from under a concurrent session.** Setting
  the env var keeps that collision-free behaviour while choosing the root.
- Choosing `<repo>/.pytest_tmp` as that root means `%LOCALAPPDATA%\Temp\pytest-of-o_iseri` — the
  access-denied directory that blocks the naive remedy — **is never touched at all.** The lockout
  is bypassed, not repaired.
- `.pytest_tmp/` is **already** in `.gitignore` (`.gitignore:50`), so nothing new becomes
  git-visible. Director-verified.
- `tmp_path_retention_policy = "failed"` and `tmp_path_retention_count = 3` stay exactly as they
  are; they apply to numbered roots the same way.

**Two alternatives, explicitly rejected, recorded so nobody re-proposes them:**

- **(a) Delete `addopts` and change nothing else.** This was the register's originally specified
  remedy and it is **proven blocked on this machine**: `tests/test_sim_integration.py` alone gave
  `1 passed, 6 errors`, all `PermissionError [WinError 5]` on
  `%LOCALAPPDATA%\Temp\pytest-of-o_iseri`.
- **(b) Repair the ACL on `pytest-of-o_iseri`.** Rejected on three grounds: it needs administrator
  rights this session does not have; it is a change to machine state living outside the repository,
  so a clean checkout on another machine inherits none of it; and `icacls` run directly against
  that directory is itself access-denied, so there is no evidence the repair would even succeed.
  **A remedy that cannot be verified from a clean checkout is not a remedy.**

**The register's open sub-question — why the pin existed at all — is answered by this ruling
rather than by more archaeology.** No code, CI config or fixture anywhere in the repo reads the
literal `.pytest_tmp` path, and `git show fe05509 -- pyproject.toml` records no rationale. The
directory *is* worth keeping as the temp root — repo-local scratch on a machine whose system temp
is partly locked — and this ruling **keeps that benefit and drops the fixed, wiped path that came
with it.** The shielding effect the predecessor pass discovered by accident is now recorded, and
deliberate.

### 4.2 Pinned facts the executor must not re-litigate

- Python: `.venv\Scripts\python.exe`. pytest 9.0.3.
- Suite baseline, run alone: **`1875 passed, 55 skipped, 11 warnings`**, ~26 min, 1930 collected.
  `testpaths = ["tests"]` is in `pyproject.toml` (ruling `3b`, 2026-08-18).
- E02 harvest root: `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest` — 40,800 building
  directories, `.eio` and `.err` complete (40,800 each, zero empty).
- 🔴 **The E02 IDF corpus under `%LOCALAPPDATA%\Temp\ubem_e02_fleet\<cell>\step3_<mode>\idfs\` is
  EMPTY** — deleted by an external process 2026-08-17 16:21. **Verify presence of any
  `%LOCALAPPDATA%` artifact before depending on it. Never cite `e02_corpus_inventory.csv` as
  current state; it is a 2026-08-11 snapshot.**
- Register arithmetic invariant: **struck rows minus retired IDs must equal exactly 2** (OPEN-02
  and OPEN-28, folded under OPEN-01, never independently tracked). Any other number is a STOP.

---

## 5. Facts with citations, per task

**§5 is the director's reading, and a lead written here is a hypothesis until the task's own
control confirms it. Build every task to disprove its lead.**

### 5.1 OPEN-52 — T01

- Register §-section at `INVESTIGATION_open-items-register.md:5135`; the 2026-08-18 amendment
  with sub-questions (a) and (b) at `:5205`.
- Current config, `pyproject.toml:51-58`: `tmp_path_retention_policy`, `tmp_path_retention_count`,
  `testpaths`, `addopts`.
- Prior evidence doc: `extra/FIX_open-52_pytest-basetemp.md`.
- `.gitignore:50` → `.pytest_tmp/`.
- **There is no repository-root `conftest.py` at HEAD** — director-verified. `tests/conftest.py`
  exists. T01 creates the root one.

### 5.2 OPEN-07 (+ OPEN-38's remaining sub-question) — T02

- Register §-section at `INVESTIGATION_open-items-register.md:2386`.
- The three buildings: `la_urban/way/401910463`, `nyc_rural/way/965718402`,
  `nyc_rural/way/965718403`.
- Register-recorded, director-verified 2026-08-06 on `way/401910463`: 1 `** Severe **`, 1 two-space
  `**  Fatal  **`, fatal zone **`LAUNDRYROOMFLR1`**, surface `P_LAUNDRYROOMFLR1_10010_0_10008`;
  the Severe is attributed to the **Sizing** phase, `0` in Warmup — *"a plan built on 'warmup'
  would look in the wrong place."*
- Register's stated blocker: *"No T20 IDF survives locally to diff a multiplier against, and the
  T19 cache directory for `way/401910463` is empty."*
- 🔴 **That blocker is stale — director-verified on disk 2026-08-18.** These exist:
  - `scratchpad/e-la-20-investigation/i03/work_part1/step3_A_as_classified_today/idfs/way_965718402.idf`
  - `scratchpad/e-la-20-investigation/i03/work_part1/step3_A_as_classified_today/idfs/way_965718403.idf`
  - and a sibling directory `step3_B_as_recorded_in_t19_SmallOffice/` — i.e. **the same two
    buildings built under the other classification.**

  Both A-side files contain the literal string `LaundryRoomFlr1`. **This is a paired A/B geometry
  artifact for two of the three regressed buildings, and it is the exact artifact the register
  says does not exist.** `way/401910463` is **not** in this cache — expect 2 of 3, not 3 of 3,
  and say so.
- **Connection to OPEN-38, which is why the two are done together.** OPEN-38's 2026-08-18 verdict
  (T04 of the predecessor plan) established that its 7 `LAUNDRYROOMFLR1` fatals come from a
  **substituted `SmallHotel` DOE prototype**, identified by finding a zone literally named
  `LaundryRoomFlr1` in `ARCHETYPE_IDF_MAP`'s baseline IDFs — and it left one sub-question
  explicitly **undeterminable from `.err`**: the unfitted-subsurface question, which *"needs IDF
  geometry, which the 2026-08-17 sweep destroyed."* **The sweep did not reach `scratchpad/`.**
- Register's own independent reproduction: exactly **7** of the 41 E-LA-38 rows carry
  `t20_status == failed`, and **all 7 are `SmallHotel`→Office mismatches**; **none of the 33
  `LargeHotel` mismatches fail.**
- Repo-side prototype sources containing `LaundryRoomFlr1`:
  `docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/sources/SmallHotel_90.1-2013.idf` and
  `docs/docs_VALIDATION/step1/Level 2 DOE round-trip/00.BaselineBuildings_NUs/ASHRAE901_HotelSmall_STD2022_Buffalo.idf`.
  **Read-only. Never edit anything under `docs/`.**

### 5.3 OPEN-08 — T03

- Register §-section: heading *"Archetype and vintage are not reproducible locally for data-poor
  buildings (E-LA-22)"*, immediately after OPEN-07's section around
  `INVESTIGATION_open-items-register.md:2413`.
- Measured half: cross-generation **archetype** disagreement T08 vs T20 = **13.40%** on 4,530
  shared buildings (`extra/MEASUREMENT_open-28_harvest-generation-join.md`).
- Unmeasured half, and its stated reason: *"Vintage disagreement remains unquantifiable — no
  harvest persists a `vintage_standard` column, see new item OPEN-30."*
- 🔴 **Stale.** OPEN-30 **closed 2026-08-11**: *"demonstrated on 60/60 E02 manifests, 40,800 rows,
  0 nulls, 5 distinct values, `DOERefPre1980` 93.44% vs the ≈92.9% expectation; `la_rural`
  cross-check vs raw `year_built` reproduces R07 with zero crossover in all five modes."*
  **The column the blocker says does not exist has existed since 2026-08-11.**
- Consequence to test, **as a hypothesis**: the vintage half of OPEN-08 is now measurable on the
  E02 manifests, and OPEN-08 may reduce to its archetype half alone.

### 5.4 OPEN-29 — T04

- Register §-section at `INVESTIGATION_open-items-register.md:1759`.
- Data on disk: `openubem/outputs/comparisons/open29_defect_status_trace.csv` — **13 rows**
  (E-LA-06 split into two halves), columns `id, defining_site, defining_status, latest_document,
  latest_date, latest_status_quote, bucket, notes`.
- Method control already validated once: **E-LA-20**, not a candidate, run blind through the
  procedure, correctly returned `FIXED, verified 150/150`. **Re-use the control; do not inherit
  its result — re-run it.**
- 🔴 **The trace is dated 2026-08-06 and the register's "9 of 12 still open" rests on it.** Since
  then `E-LA-16` was **adjudicated and closed 2026-08-18** (OPEN-51, retired), the malformed-fatal
  class `R06` was finished 2026-08-12, and eight further passes have landed. **The count is
  presumed stale; the task is to re-derive it, not to defend it.**
- `E-LA-21` (the `has_fatal` one-space/two-space dead column) is **demonstrated wrong on a named
  building** — `way/401910463`, per §5.2. That demonstration is 2026-08-06 and must be re-checked
  against HEAD's parser.

### 5.5 OPEN-53 — T05

- Register §-section at `INVESTIGATION_open-items-register.md:5219`, with the director's
  2026-08-18 CP-1 ruling inside it: **cause ANSWERED, item narrowed to custody.**
- The two carried-forward consequences named in that ruling, which T05 discharges:
  1. `openubem/outputs/comparisons/e02_corpus_inventory.csv` **must be annotated as a 2026-08-11
     snapshot rather than current state** — it is already falsified by disk for two rows.
  2. **IDF-based per-surface geometry no longer exists for anyone to plan around** — except, per
     §5.2, in `scratchpad/` for two buildings, which is itself worth recording as fragile.

---

## 6. Tasks

### T01 — OPEN-52: apply ruling `3a` and close the item

**What.** Implement the remedy pinned in §4.1, prove it fixes the collision, prove it does not
touch the locked directory, prove the suite is unchanged, then close OPEN-52.

**Why.** OPEN-52 is the last item in this arc whose only blocker was an owed ruling. The ruling is
given. Until it lands, every dispatch in this project carries a "one pytest at a time" discipline
that depends on the director remembering — a mitigation the register itself calls *"a discipline,
not a fix."*

**How.**

1. Record `pyproject.toml`'s exact current bytes (hash it) before touching it.
2. Remove the `addopts` line. Leave `testpaths`, `tmp_path_retention_policy` and
   `tmp_path_retention_count` untouched.
3. Create `conftest.py` at the repository root containing only what is needed to set
   `PYTEST_DEBUG_TEMPROOT` to the absolute path of `<repo>/.pytest_tmp`, creating the directory if
   absent. Set it early enough that pytest's temp factory sees it — and **verify empirically that
   it did**; do not assume.
4. **Verification A — the root actually moved.** Run one small test file that uses `tmp_path`.
   Assert the session directory is under `<repo>/.pytest_tmp/pytest-of-<user>/pytest-<n>/`.
   Record the real path.
5. **Verification B — the locked directory is never touched.** Confirm no `pytest-of-o_iseri`
   directory is created or accessed under `%LOCALAPPDATA%\Temp` during that run. Record how you
   confirmed it.
6. **Verification C — the collision is gone.** Reproduce the predecessor's busy-loop design: two
   concurrent pytest sessions, continuous `tmp_path` writes, no sleep. Before the fix this gave
   `FileExistsError [WinError 183]` cascading from `OSError [WinError 145]` inside pytest's own
   `rm_rf`. **Run the negative control too** — briefly restore the old `--basetemp` config,
   reproduce the failure, then restore the fix. **A before/after with no "before" is not
   evidence.** Assert the two sessions land in different numbered directories.
7. **Verification D — nothing regressed.** `.venv\Scripts\python.exe -m pytest -q tests/`, **run
   alone, in the foreground, to completion.** Quote the exact final line. It must match
   `1875 passed, 55 skipped` with 0 failed and 0 errors.
8. Write `extra/FIX_open-52_temproot-remedy.md`: the ruling as given, the two file changes,
   verifications A–D with real output, and the two rejected alternatives with their reasons.
9. Amend the register's OPEN-52 §-section and §1 row: strike what the remedy paragraphs got wrong,
   record the ruling and the fix, and — **only if A, B, C and D all pass** — mark it
   **CLOSED + ID RETIRED 2026-08-18**.
10. If any of A–D fails: **revert both file changes to their recorded pre-task state, leave
    OPEN-52 open, record what failed, and STOP.** Do not improvise a different remedy.

**How to test.** Verifications A–D above, each with quoted output. D is the gate.

---

### T02 — OPEN-07 + OPEN-38's subsurface sub-question: diff the surviving A/B IDFs

**What.** Use the two surviving paired IDFs in `scratchpad/e-la-20-investigation/i03/work_part1/`
to answer, for the first time with geometry in hand, **why the three E-LA-40 buildings regressed
from success to failure**, and whether OPEN-38's unfitted-subsurface sub-question is answerable
from them.

**Why.** The register records this as *silent* — hypothesis neither confirmed nor refuted, because
no IDF survived. Two do. This is the same stale-blocker pattern that closed OPEN-46 yesterday.

**How.**

1. **First, verify the artifact before building on it.** Confirm both A-side and both B-side IDFs
   exist and are non-empty; record path, size and mtime for each. **If the B side is absent or
   empty, say so and reduce the task's scope accordingly rather than substituting something else.**
2. Establish what differs between A (`as_classified_today`, `SmallHotel`) and B
   (`as_recorded_in_t19_SmallOffice`) for each building: zone count, zone names, surface count,
   subsurface count, multipliers, and the presence of `LaundryRoomFlr1`.
3. **The subsurface question.** For every `FenestrationSurface:Detailed` (and equivalent), test
   whether its vertices lie inside its named base surface. Report per-building counts of fitted vs
   unfitted, **A side and B side**. This is OPEN-38's sub-question, and `.err` could not answer it.
4. **Control, mandatory.** Run the same subsurface test on at least one IDF known **not** to
   exhibit the defect — e.g. the repo's own `SmallHotel_90.1-2013.idf` prototype (read-only).
   **If the test flags the healthy prototype too, the test is wrong and the result is void.**
   Report the control before the finding.
5. Cross-check against `.err`: for the same two buildings, read their surviving `eplusout.err`
   under `HARVEST_ROOT` and confirm the fatal zone and the Sizing-phase attribution the register
   records. Note any disagreement rather than resolving it.
6. **State the limit plainly.** `way/401910463` has no surviving IDF. Whatever is concluded covers
   2 of 3 buildings; do not generalise to the third without saying you are.
7. Emit `openubem/outputs/comparisons/open07_smallhotel_idf_diff.csv` and write
   `extra/MEASUREMENT_open-07_smallhotel-idf-diff.md`.
8. Amend the register for **OPEN-07** (strike the "no IDF survives" blocker, record what the diff
   shows) and add a dated amendment to **OPEN-38** recording whether its subsurface sub-question is
   now answered, still open, or answerable only for 2 buildings.
   **Recommend a disposition for OPEN-07; do not close it yourself.**

**How to test.** The step-4 control is the gate: report it first. The A/B counts must be
reproducible by re-running the script and must not depend on file ordering.

---

### T03 — OPEN-08: measure the vintage half, now that OPEN-30 unblocked it

**What.** Quantify cross-generation **vintage** disagreement for data-poor buildings — the half of
OPEN-08 the register calls unquantifiable — using the E02 manifests OPEN-30 proved carry
`vintage_standard`.

**Why.** OPEN-08 *"quietly limits every other item"*: every cross-generation comparison in this
project rests on it, and half of it has never been measured. Its stated reason is seven days out of
date.

**How.**

1. **Verify the premise before measuring.** Locate the E02 manifests and confirm `vintage_standard`
   is present and populated. Re-derive OPEN-30's own numbers as the control: 40,800 rows, 0 nulls,
   5 distinct values, `DOERefPre1980` ≈93.44%. **If those do not reproduce, STOP and report** — the
   premise is wrong and the rest of the task is void.
2. Join the E02 generation to the prior generation on building identity, exactly as
   `extra/MEASUREMENT_open-28_harvest-generation-join.md` did for archetype. **Re-use that join; do
   not invent a second one**, so the archetype and vintage numbers are directly comparable.
3. Report vintage disagreement as a rate on the shared population, alongside the archetype 13.40%
   on the same rows. Break it down by whether the building is data-poor (missing `levels`,
   `height_m`, or `year_built`) — that is OPEN-08's actual claim.
4. **Non-vacuity control.** Confirm the join is not degenerate: report the shared-population count
   and confirm that some buildings agree and some disagree on each axis.
5. Emit `openubem/outputs/comparisons/open08_vintage_reproducibility.csv`, write
   `extra/MEASUREMENT_open-08_vintage-reproducibility.md`, amend OPEN-08's register row and
   §-section. **Recommend whether OPEN-08 reduces to its archetype half; do not close it.**

**How to test.** Step 1's reproduction of OPEN-30's numbers, and step 4's non-vacuity control. Both
must be quoted before any conclusion.

---

### T04 — OPEN-29: re-derive the defect-status trace at HEAD

**What.** Re-run OPEN-29's forward trace over all 13 rows of `open29_defect_status_trace.csv`
against the repository **as it stands 2026-08-18**, and produce a current two-column answer:
genuinely-still-open vs closed-elsewhere.

**Why.** The register's headline number — *"9 of 12 are genuinely still open"* — comes from a
2026-08-06 trace. `E-LA-16` has provably closed since (OPEN-51, adjudicated and retired
2026-08-18). If the register is the single place open work is recorded, a twelve-day-stale count
inside it is exactly the failure OPEN-29 exists to catch.

**How.**

1. Re-run the **method control first**: E-LA-20 blind through the procedure. It must return
   `FIXED, verified 150/150` at
   `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:68`.
   **If the control does not reproduce, STOP** — the procedure is broken, not the data.
2. For each of the 13 rows, follow citations forward to the **latest** document mentioning the ID
   and record its final status with a `path:line`. Include documents written since 2026-08-06 —
   this arc's own register, its plan docs, and its `extra/` reports.
3. **Re-check `E-LA-21` against HEAD's parser specifically**: does `has_fatal` still test only the
   one-space `** Fatal **` form? Cite the line. The register says it is demonstrated wrong on
   `way/401910463`; confirm or refute at HEAD.
4. Produce `openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv` — **a new file;
   the 2026-08-06 one is not overwritten** — with a `changed_since_2026-08-06` column.
5. Write `extra/MEASUREMENT_open-29_status-retrace.md` and amend OPEN-29's row and §-section with
   the new count, **striking the old one, not replacing it**.
6. **Do not open register items for the still-open ones.** Recommend; the director decides.

**How to test.** Step 1's control. Every status claim must carry a `path:line` a reader can open.

---

### T05 — OPEN-53: discharge the two custody consequences

**What.** Apply the two consequences the director's CP-1 ruling carried forward, so no future plan
can silently depend on artifacts that no longer exist.

**Why.** The item's cause is answered. What remains is that **the repository still presents a
2026-08-11 census as current state**, and the next planner will believe it — as this director
nearly did.

**How.**

1. Annotate `openubem/outputs/comparisons/e02_corpus_inventory.csv` so a reader cannot mistake it
   for current state — **in a way that does not corrupt the CSV for its existing readers**. Check
   who reads it first (`grep -rn e02_corpus_inventory scripts/ openubem/`) and choose accordingly;
   a sidecar `.md` next to it is acceptable and is the safer default if any code parses the CSV.
2. Record, in the same note, the two rows disk has already falsified (`austin_suburban,fast_zone`
   and `austin_suburban,floor`, `n_end=437` recorded, 0 on disk).
3. Add to the register's OPEN-53 §-section a short, explicit **planning rule**: any plan depending
   on a `%LOCALAPPDATA%` E02 artifact must re-verify presence at planning time and must not cite
   the inventory as current state. Note the `scratchpad/` survival found in T02 as the one known
   exception — **and mark it fragile**, since `scratchpad/` is not a durable store either.
4. **Recommend a disposition for OPEN-53** — the honest options are *close it as discharged* or
   *keep it open as a standing custody risk*. Argue for one. **The director decides.**

**How to test.** Step 1 must not break any existing reader: if code parses that CSV, show the parse
still works after your change, or use the sidecar.

---

### T06 — Reconciliation sweep

**What.** The arc's standard closing task.

**How.**

1. Re-run `scripts/analysis/open_register_recount_2026-08-18.py` over the §1 table and quote its
   full output.
2. Reconcile struck rows against retired IDs. **The difference must be exactly 2.** Anything else
   is a STOP, not an adjustment.
3. Update the §1 header line with a new dated bracket: what closed, what opened, new counts, new
   retired total, next free ID.
4. Add a dated amendment to `docs/PROJECT_CHECKLIST.md` with the pass's outcomes and the suite line.
5. Update the director prompt's 🟧 RESUME box and add a `§5.20` section for this pass.
6. Final full suite, **alone, foreground, to completion**: quote the exact final line.

**How to test.** Steps 2 and 6.

---

## 7. Stop-and-report points

- **CP-1 — after T01.** OPEN-52 is the only task that changes how every other test in this
  repository runs. **Stop. Report verifications A–D with real output. Do not start T02 until the
  director signs.** If any verification failed, report the reverted state instead.
- **CP-2 — after T03.** T02 and T03 are the two diagnosis tasks whose leads are the director's own.
  Stop and report both, including any refutation. **A refuted lead is a pass, not a failure.**
- **CP-3 — after T06.** Final sign-off.

---

## 8. Progress log

*(One entry per completed task, appended by the executor:
`#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)*

#### T01 — OPEN-52: apply ruling `3a` and close the item — completed 2026-08-18

**Artifacts:**
- `conftest.py` (new, repository root) — sets `PYTEST_DEBUG_TEMPROOT` to `<repo>/.pytest_tmp` at
  import time.
- `pyproject.toml` — `addopts = "--basetemp=.pytest_tmp"` deleted; `testpaths`,
  `tmp_path_retention_policy`, `tmp_path_retention_count` unchanged. Pre-task hash
  `8d0ff72a...973ed`, post-task hash `b73222eb...0e84`.
- `docs/docs_ACTIVE/openings/extra/FIX_open-52_temproot-remedy.md`.
- Register amended (OPEN-52 §1 row, strike-and-correct, and its §-section, new dated subsection) —
  **not** marked CLOSED/RETIRED; recommended disposition only, per an explicit mid-task instruction
  from the coordinator that this pass's register edits stay recommend-only and the director disposes.

**Deviations from §6-T01's literal steps:**
- Step 9 ("mark it CLOSED + ID RETIRED 2026-08-18" if A–D pass) was **not executed** — a mid-task
  message from the coordinator explicitly overrode this step for this pass ("Do NOT close it
  yourself and do NOT retire the ID... the register is yours alone now" — implying other parallel
  executors' T02/T03 edits, already present in this doc, were also director-mediated). The register
  amendment recommends CLOSE + RETIRE and gives the full A–D evidence; the disposition itself is
  left to the director.
- Verification C was run twice. The first run (before Verification D) produced valid A/B evidence,
  but `tmp_path_retention_policy = "failed"` cleaned up its passed-test numbered directories once
  Verification D's full-suite run allocated and finished its own session directories, so by the time
  D completed, no on-disk trace of C's first run remained. C was **redone after D**, with nothing
  else using pytest, and its fresh output (captured immediately via pid-tagged log files, read
  before anything else could touch `.pytest_tmp`) is what is quoted in the FIX doc and below. This
  is recorded because a prior similar pass (predecessor plan, OPEN-52's earlier T01) was flagged for
  writing conclusions before real output existed — this deviation is the opposite failure mode
  (real output existed, then got silently cleaned up by an unrelated later step) and is disclosed
  rather than left implicit.

**Test status — all four verifications passed, real output quoted in `extra/FIX_open-52_temproot-remedy.md`:**
- **A (root moved):** `tests/test_results_denominator.py` → `7 passed in 0.68s`; session at
  `<repo>\.pytest_tmp\pytest-of-o_iseri\pytest-0\`. **PASS.**
- **B (locked directory untouched):** `%LOCALAPPDATA%\Temp\pytest-of-o_iseri` exists but its
  `LastWriteTime` (April 1, 2026) is unchanged by the run. **PASS.**
- **C (collision gone, before/after both measured):** negative control (old `addopts` config,
  restored temporarily) reproduced the collision twice independently — `FileExistsError` cascading
  from `rm_rf`'s `OSError [WinError 145]`, session B, both times. Positive control (fix in place):
  two concurrent sessions both passed (`17.67s`/`17.71s`), landed in distinct `pytest-0`/`pytest-1`
  directories, confirmed via pid-tagged log files read immediately off disk. **PASS.**
- **D (nothing regressed):** full suite, alone, foreground, to completion. Exact final line:
  **`1875 passed, 55 skipped, 11 warnings in 1079.75s (0:17:59)`** — matches the pinned baseline
  exactly (`1875 passed, 55 skipped`), 0 failed, 0 errors. **PASS.**

**Notes:**
- The full-suite run (D) exceeded the tool's 10-minute per-call timeout and continued running to
  completion under the harness's own background supervision; no conclusion was written until the
  real final line was read from the completed run's output file — not deliberately backgrounded, and
  no placeholder was substituted.
- Both alternatives named in §4.1 remain rejected for the reasons given there: (a) bare `addopts`
  deletion is independently reproven blocked on this machine by this task's own negative control;
  (b) an ACL repair on `pytest-of-o_iseri` needs rights this session does not have and cannot be
  verified from a clean checkout.
- No production code changed. Only the two authorised files (`pyproject.toml`, `conftest.py`) plus
  documentation/register text were touched. `scratchpad/open52/test_collision.py` (gitignored) was
  created as a throwaway concurrency-test fixture, mirroring the predecessor task's own location and
  approach for the same measurement; it is not one of this plan's listed new files but is disposable
  scratch, not a deliverable.

#### T02 — OPEN-07 + OPEN-38 subsurface sub-question: diff the surviving A/B IDFs — completed 2026-08-18

**Artifacts:**
- `scripts/analysis/open07_smallhotel_idf_diff.py`
- `openubem/outputs/comparisons/open07_smallhotel_idf_diff.csv`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-07_smallhotel-idf-diff.md`
- Register amended: OPEN-07 §-section (strike-and-correct) and OPEN-38 §-section (dated amendment).

**Deviations:** None from §6-T02's method. The subsurface-fit test is an independent re-implementation
of EnergyPlus's `CHKSBS` check (Newell-plane fit + 2D point-in-polygon with a 0.02 m tolerance), not the
EnergyPlus source itself — flagged explicitly in the measurement doc as an approximation whose sanity
rests on the control, not an assumption.

**Test status — both gates passed, quoted before conclusions:**
- Step-1 artifact gate: all 4 A/B files + the control prototype exist, non-empty (sizes 1,909,240 /
  358,867 bytes; control 1,561,172 bytes). `way/401910463` confirmed absent from both `idfs/` dirs.
- Step-4 control gate: `{'n_subsurfaces': 106, 'n_fitted': 106, 'n_unfitted': 0, 'n_no_base_surface': 0}`
  on the healthy `SmallHotel_90.1-2013.idf` — 0 false positives, control passed, findings below are not
  void.

**Notes / findings:**
- Multiplier-scaling hypothesis **refuted** on the 2 measured buildings: both A and B carry uniform
  subsurface multiplier `1.0`.
- A-side (`SmallHotel`, as classified today) has zone/surface/subsurface counts (67/485/106) **identical
  to the repo's own healthy prototype control** — the substituted geometry is the raw DOE prototype
  dropped in wholesale, not an OSM-extruded reclassification. Corroborates OPEN-38's existing finding.
- Subsurface-fit census: **0 of 106 (A) and 0 of 23 (B) unfitted, both buildings** — a null result on
  OPEN-38's unfitted-subsurface sub-question, not a confirmation.
- `.err` cross-check reproduces the register's fatal zone (`LAUNDRYROOMFLR1`) and Sizing/Warmup framing,
  but the 3 `CHKSBS`-named surface/subsurface pairs per building, hand-checked in the scratchpad IDF, are
  geometrically well-contained (0.1–1.2 m margins) — **a disagreement between the harvested `.err`
  (2026-08-10) and the scratchpad IDF (mtime 2026-07-25) is recorded, not resolved**, per §6-T02 step 5's
  instruction.
- Scope limit stated per §6-T02 step 6: findings cover 2 of 3 `E-LA-40` buildings;
  `la_urban/way/401910463` has no surviving IDF anywhere under `scratchpad/` and is not generalised to.
- Recommended dispositions (director decides, not closed by this task): **OPEN-07 stays open**, narrowed
  to the unmeasured third building and the new `.err`-vs-scratchpad provenance question; **OPEN-38's
  subsurface sub-question** recorded as measured-null on 2/7 fatals with a new open provenance question,
  not "answered."

#### T03 — OPEN-08: measure the vintage half, now that OPEN-30 unblocked it — completed 2026-08-18

**Artifacts:**
- `scripts/analysis/open08_vintage_reproducibility.py`
- `openubem/outputs/comparisons/open08_vintage_reproducibility.csv` (738 rows, `nyc_centre` only)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-08_vintage-reproducibility.md`
- Register amendment drafted, NOT applied (register is a director-only edit this pass) — full text in
  the measurement doc's `## Register amendment to apply` section.

**Deviations:** §6-T03 step 2 says "join the E02 generation to the prior generation… exactly as
`MEASUREMENT_open-28` did for archetype." That join (T08 vs T20) was reproduced exactly and reused
unmodified for the archetype figure. But neither T08 nor T20 carries `vintage_standard` at all
(established in `MEASUREMENT_open-28` §4), so no vintage number could be computed on that join by
itself. A prior-generation vintage source had to be located separately: `cases/<cell>/05_results.gpkg`,
named in `MEASUREMENT_open-28` §4 as a source that must not be substituted for T08's/T20's *own*
vintage — this task does not make that substitution, it uses the file only as an independent,
genuinely-earlier vintage snapshot (commit `e063865`, confirmed by `git log`) paired against E02, and
says so explicitly in the measurement doc. This is a necessary deviation from a literal single-join
reading of step 2, disclosed rather than silently taken.

**Test status — both gates passed, quoted before conclusions:**
- Step 1 hard gate (re-derive OPEN-30's own numbers): 60/60 manifests, 40,800 rows, 0 nulls, 5 distinct
  values, `DOERefPre1980` 93.4436% ≈ 93.44%. **PASS.**
- Step 2 (reproduce OPEN-28's own join): 4,530 shared rows, 0 t08_only, 3,630 t20_only, archetype
  disagreement 13.3996% ≈ 13.40%. **PASS.**
- Non-vacuity control (§6-T03 step 4): 738-row shared population, vintage some-agree/some-disagree
  (710/28), archetype some-agree/some-disagree (365/373). **Not degenerate.**

**Notes / findings:**
- Schema check (`step 3a`) found the candidate prior-generation vintage source
  (`cases/<cell>/05_results.gpkg`) carries `vintage_standard` in only 1 of the 5 T08 cells
  (`nyc_centre`) — the other 4 cells' copies are a stripped 21-column schema with no vintage/provenance
  columns at all, in both the `step1` and `validations` roots. **Vintage is measurable on 738/4,530
  shared buildings (16.3%), not on the full population — a schema gap, not a data-absence gap.**
- On that 738-building subset: vintage disagreement **3.79%** (28/738) vs the archetype 13.40% on the
  full population. Skewed toward data-poor buildings: 3.93% (713 data-poor) vs 0.00% (25 data-rich) —
  directionally consistent with OPEN-08's claim, but the data-rich comparison group is thin.
- **Recommendation (director decides): OPEN-08 does not reduce to its archetype half.** Vintage
  disagreement is real and non-zero where measurable, smaller than archetype's but not negligible.
  Register clause should narrow from "unquantifiable" to "quantified on 1/5 T08 cells, unquantifiable on
  the remaining 4 for a schema reason."

#### T05 — OPEN-53: discharge the two custody consequences — completed 2026-08-18

**Artifacts:**
- `openubem/outputs/comparisons/e02_corpus_inventory.SNAPSHOT_NOTICE.md` (new sidecar, next to the
  CSV; the CSV's own bytes are untouched)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_missing-sql.md`, new §7 appended (re-verified
  numbers, IDF-corpus check, scratchpad-survival check, planning rule, register-amendment draft,
  disposition argument)
- Register NOT edited (per this pass's constraint) — amendment text drafted in
  `MEASUREMENT_open-53_missing-sql.md` §7.5, `## Register amendment to apply`, for the director to
  place.

**Deviations:** None from §6-T05's method. Step 1's gate showed no code parses the CSV, so the sidecar
route was taken as the plan itself names as the safe default in that case — the CSV was left byte-for-
byte unchanged.

**Test status:**
- Step-1 gate (`grep -rn e02_corpus_inventory scripts/ openubem/ tests/ docs/`): one hit outside docs,
  `scripts/analysis/e02_corpus_inventory.py:15` — the writer (`OUT_CSV = ...`), not a reader. No parse
  site exists to break; sidecar-vs-edit choice confirmed safe either way, sidecar used per the plan's
  stated default.
- Re-verified inventory-vs-disk, live 2026-08-18: `austin_suburban,fast_zone` and
  `austin_suburban,floor` both record `n_end=437` in the CSV; live disk shows `n_end=0, n_sql=0` for
  both (building dirs intact, 437/437). Numbers re-derived fresh, not carried from the plan or register.
- E02 fleet IDF corpus re-checked directly (not assumed): 15 `idfs/` directories sampled across 3 cells
  x 5 modes (`austin_suburban`, `nyc_centre`, `la_urban` x `auto`/`fast_zone`/`floor`/`building`/
  `layout_assign`) — all 15 empty, mtimes clustered at 2026-08-17 16:21 across unrelated cells.
- `scratchpad/e-la-20-investigation/i03/work_part1/` survival confirmed directly: 4 IDFs present and
  non-empty (2 buildings x A/B classification), mtime 2026-07-25 — outside the deleted
  `ubem_e02_fleet` tree, three weeks before the 2026-08-17 deletion. Marked fragile in the note:
  `scratchpad/` carries no retention guarantee.

**Notes / findings:**
- Recommended disposition: **OPEN-53 stays open**, as a standing custody risk — not closed as
  discharged. The two named consequences are applied and there is no remaining measurement question,
  but nothing in this pass changed the underlying hazard (an external process can still delete
  `%LOCALAPPDATA%` artifacts without this project's knowledge), and the fleet corpus is still empty and
  the two Austin cells still show 0 `.end` on disk today, exactly as before. Closing it would remove the
  only place this recurring hazard is tracked. Full argument in `MEASUREMENT_open-53_missing-sql.md` §7.6.
  Director decides.

#### T04 — OPEN-29: re-derive the defect-status trace at HEAD — completed 2026-08-18

**Artifacts:**
- `scripts/analysis/open29_status_retrace_2026-08-18.py`
- `openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv` (new file; the 2026-08-06
  `open29_defect_status_trace.csv` is untouched — mtime confirmed unchanged, `2026-08-05 20:05`,
  before and after this task)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-29_status-retrace.md`
- Register amendment drafted, NOT applied (register is a director-only edit this pass) — full
  strike-and-correct text for OPEN-29's §1 row and §-section in the measurement doc's `## Register
  amendment to apply` section (§5).

**Deviations:** None from §6-T04's method. One thing found mid-task that the plan did not anticipate:
an intermediate trace, `extra/MEASUREMENT_open-29_eight-defect-recheck.md` (2026-08-13, T05 of
`PLAN_five-more-items-2026-08-13.md`), already re-derived 8 of the 13 rows against HEAD and was
itself followed forward per the task's own "follow citations forward to the latest document" rule —
used as an intermediate checkpoint, not as a substitute for re-verifying at 2026-08-18's own HEAD.

**Test status — the step-1 gate, quoted before any conclusion:**
- Step 1 hard gate (E-LA-20 method control, run blind): reproduces `FIXED, verified 150/150` at
  `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:68` exactly.
  **PASS.** Quoted verbatim in the measurement doc §1.
- Step 3 (E-LA-21 re-checked against HEAD's parser, live): all 7 harvest sites
  (`t20/t08/t07/t07b/t17/t18_harvest*.py`, `t08_local_remainder.py`) use
  `re.search(r"\*\*\s+Fatal\s+\*\*", err)` — **no site tests only the one-space form.** The only
  surviving one-space literal in the tree is a text value inside the 2026-08-06 CSV, not live code.
  **Register's R06 claim (2026-08-09) and malformed-variant sweep claim (2026-08-12) both confirmed
  live at HEAD, 2026-08-18.**

**Notes / findings:**
- **New bucket counts: CLOSED-ELSEWHERE 4, STILL-OPEN 8, SUPERSEDED 1 — 13 rows / 12 IDs** (was
  CLOSED-ELSEWHERE 3, STILL-OPEN 9, SUPERSEDED 1 on 2026-08-06). **Only one row's bucket changed:
  E-LA-21**, STILL-OPEN → CLOSED-ELSEWHERE — confirmed live in §2 of the measurement doc, not merely
  cited from the register.
- **E-LA-16 correction to the task's own supplied hypothesis.** The brief that dispatched this task
  stated E-LA-16 was "provably closed — OPEN-51 adjudicated it and retired 2026-08-18." **Checked, not
  taken on trust, and found imprecise: OPEN-51 closed the *register item* asking which of two readings
  the ID `E-LA-16` names (adjudicated: the cooling-coil-UA-autosize reading is correct) — it did
  **not** close the underlying defect.** `git log -p --since="2026-08-13" --
  openubem/geometry/layout_assigner.py` shows the only change in that window is a comment-text
  correction (commit `b2d0220`); no code anywhere handles the cooling-coil-UA-autosize mechanism.
  E-LA-16's bucket is unchanged: **STILL-OPEN.** The register's own text corroborates this reading
  once traced (`INVESTIGATION_open-items-register.md:5222-5226`, "OPEN-29 — no change").
- All other 6 STILL-OPEN rows (E-LA-06 flow-balance, E-LA-15, E-LA-17, E-LA-18, E-LA-19, E-LA-30,
  E-LA-33) re-verified unchanged since 2026-08-06/08-13 by direct `grep`/`git log --since=2026-08-13`
  against each cited mechanism's file — no code touched any of them in the intervening window except
  the one E-LA-16 comment.
- Per §6-T04 step 6, **no register item was opened** for any of the 7 remaining STILL-OPEN IDs.
  Recommendation only, left to the director: none currently warrant promotion — each is exactly where
  the 2026-08-13 recheck left it, and the register's own OPEN-29 section already tracks all of them by
  design ("defect-level, not item-level").

#### T06 — Reconciliation sweep — completed 2026-08-18

**Artifacts.** Register §1 header re-dated with this pass's bracket; OPEN-52 struck and retired in both
its §1 row and its §-section; deferred amendments placed for OPEN-08, OPEN-29, OPEN-38 and OPEN-53;
`docs/PROJECT_CHECKLIST.md` amended; director prompt §5.20 written and its RESUME box superseded.

**Recount** (`scripts/analysis/open_register_recount_2026-08-18.py`, verbatim):

```
Table body: lines 633-688 (1-indexed), 53 row-lines
Total OPEN-NN rows found: 53
Live (non-struck) rows: 24
Struck rows: 29
ID range: OPEN-01 .. OPEN-53
Missing IDs in sequence: none
Duplicate IDs: none
Next free item ID: OPEN-54
```

**Reconciliation.** 29 struck rows against 27 retired IDs. **Difference = exactly 2 — OPEN-02 and
OPEN-28**, folded under OPEN-01 and never independently tracked. The invariant holds. OPEN-52 moved
from live to struck and was retired in one edit, so the gap neither widens nor narrows.

**Test status.** Full suite, run alone in the foreground to completion, no other pytest session live:

```
1875 passed, 55 skipped, 11 warnings in 1035.59s (0:17:15)
```

**Deviations.** Three. (1) T02 and T03 were released before CP-1 was formally signed — a deliberate
director decision, since neither runs pytest and the only outstanding CP-1 item was the suite line.
(2) Only T01 and T02 were permitted to edit the register; T03, T04 and T05 were redirected to write a
`## Register amendment to apply` section into their own measurement docs, which the director then
placed — done to eliminate concurrent-write corruption while three executors were live.
(3) T01 was resumed mid-task rather than re-dispatched, because it was blocked only on a suite run it
had itself launched.

**Notes.** Two director leads written into §5 were refuted by the tasks built to test them (OPEN-38's
unfitted-subsurface hypothesis; E-LA-16's supposed closure), and two executor numbers were corrected on
audit (OPEN-08's comparator, OPEN-29's site count). Both directions of correction are recorded in the
register at the point of the claim, not only here.
