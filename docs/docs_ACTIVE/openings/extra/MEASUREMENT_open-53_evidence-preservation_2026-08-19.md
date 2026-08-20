# MEASUREMENT — T10 of `PLAN_ten-items-2026-08-19.md`: execute ruling R3, preserve the cited OPEN-48 run-2/run-3 evidence, restate OPEN-53

**Ruling R3 (2026-08-19):** *"Copy the cited material into the repository."* This task copies it, hashes
it, verifies the copy independently, and restates what remains of OPEN-53's closure condition. **No git
write command was run.** Files land in the working tree; committing is the user's, done externally.

---

## 1. Step 1 (load-bearing): re-verify the source trees exist

Both trees named in the plan's Dependency Decisions section were checked on disk **before anything
else**:

- `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3/` — **present**, all twelve cell directories.
- `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/` (run 2) — **present**, all twelve cell
  directories.

**Neither tree is gone.** The stop-and-report branch of step 1 does not apply this pass.

---

## 2. Before copying anything: what is already durable

Before enumerating what to copy, the existing repository tree was checked for material that ruling R3's
"why" section assumed was only on the volatile path. Two things were already durable and are **not**
duplicated by this task:

- **`docs/validations/overAll/results/open48_refleet/`** — tracked in git (122 files, ~23 MB): every
  cell's `05_results.csv`, `04_simulation_manifest.parquet`, `05_results.gpkg/geojson`, gates report.
  This is the run-2 evidence backing OPEN-35 and OPEN-12's per-cell contingency (T07 of this plan reads
  it directly). **Already safe.**
- **`docs/validations/overAll/results/open48_refleet3/`** — present in the working tree (untracked, 5
  cells: `austin_rural`, `austin_urban`, `la_rural`, `la_suburban`, `nyc_rural`; 7 MB) — the run-3 cells
  that finished harvest before T02's crashes. **Already on disk, just not yet committed** (committing is
  the user's, externally — outside this task's scope).
- **`openubem/outputs/comparisons/open56_fleet_cost_stratified.csv`** — the OPEN-56 A/B **aggregate
  result vector** (the +0.98 % / +0.84 % fleet figure, 69 buildings) is already a repo artifact. **Not
  duplicated** into the evidence tree — only the raw per-building `.err`/`.end` behind it, which exist
  nowhere else, were copied (§4).

So the actual gap — material that is cited by an open item and exists **only** on a volatile
`%LOCALAPPDATA%`/gitignored-`scratchpad` path — is narrower than the plan's "why" section states. This
is reported as a finding, not smoothed over: **the 0.12 GB estimate in the plan was for material that
turned out to be partly already safe.**

---

## 3. What is still genuinely only on a volatile path (the actual gap copied)

| item | open item(s) cited | volatile location |
|---|---|---|
| Six OPEN-42 buildings' staged IDF + `eplusout.err`/`.end`, run 2 | OPEN-42, OPEN-11 (fold) | `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/` |
| Same six, run-3 corroboration `.err`/`.end` (5 of 6 — `la_urban` has no run-3 sim output at all) | OPEN-42, OPEN-11 (fold) | `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3/` |
| Two of three OPEN-07 buildings' A/B IDF + simulated `.err`/`.end` | OPEN-07 | `scratchpad/e-la-20-investigation/i03/` (gitignored) |
| Third OPEN-07 building (`way/401910463`) — no surviving original anywhere; T05's rebuild reproduces its register-cited fatal | OPEN-07 (gap-fill), OPEN-38 | `scratchpad/open38-t05-rebuild/` (gitignored — this plan's own T05 output, flagged by the dispatch as a candidate) |
| 70-building OPEN-56 A/B arms' raw `.err`/`.end` (140 arm-sides) | OPEN-56, OPEN-09, OPEN-11 (fold) | `%LOCALAPPDATA%/Temp/open56_fleet_cost/` |

**Never copied, per hard constraint 3:** any `.sql` file. Confirmed zero `.sql` anywhere under
`docs/validations/overAll/evidence/open48_runs/` after the copy.

**Deliberately not copied, and why:**
- IDFs for the six OPEN-42 buildings from **run 3** — same-generation geometry as run 2's copy already
  preserved; copying both would double the size for no analytical gain. Only run 3's own `.err`/`.end`
  (which do differ in severe counts from run 2's — see §5) were copied.
- The other four fatals + three negative controls from T05's `open38-t05-rebuild/` (`la_centre`,
  `relation/6374725`, `way/428846131`, and the three healthy-control buildings) — none is named by any
  open item in this task's mandate (OPEN-56, OPEN-42, OPEN-11, OPEN-07, OPEN-09, OPEN-35, OPEN-12).
  OPEN-38 is not in that list. `way/401910463` is the one exception copied, because it is *also* one of
  OPEN-07's three named buildings and is the only surviving evidence for that building at all — every
  other file in this task names an item from the mandate list per hard constraint 5. **Recommended, not
  taken:** if OPEN-38 is judged to need its own durable evidence, the remaining 8 buildings in
  `scratchpad/open38-t05-rebuild/` are a same-shape follow-up copy (~27 MB more, well inside the cap).
- The OPEN-56 aggregate CSV (already durable, §2) and the per-cell `05_results.csv`/manifests backing
  OPEN-35/OPEN-12 (already durable, §2).
- Everything under `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet{,3}/` that is not one of the six
  OPEN-42 buildings — the other ~8,150 buildings' IDFs/simulation output are not cited by name by any
  open item; their fleet-level summary already lives durably in `docs/validations/overAll/results/`.
- T02's stale remote `out/` directories for `nyc_suburban` — these are **on the Speed cluster**, not
  local, and this is a local file-copy task; they are also, per the dispatch note, the **pre-screen
  baseline** (mtime 2026-08-18, predates T01's code), not post-screen evidence, and are not renamed or
  represented as anything else here since nothing was copied from them.

---

## 4. What was copied

`docs/validations/overAll/evidence/open48_runs/<group>/<cell>/<building>/`, five groups
(`run2_refleet`, `run3_refleet3`, `open07_ab_sim`, `open38_t05_rebuild`, `open56_ab_arms`) — a named
adaptation of the plan's `<run>/<cell>/<building>/` shape, since the actual gap spans more than two
"runs" (two `%LOCALAPPDATA%` fleet reruns, one gitignored investigation scratchpad, one gitignored
rebuild scratchpad, one separate `%TEMP%` A/B-arm directory). Full per-file table, source path, MD5,
byte size and citing item: `docs/validations/overAll/evidence/open48_runs/MANIFEST.md`.

**323 files, 12,565,016 bytes (11.98 MB, 0.0126 GB).**

By group:
- `run2_refleet/` — 18 files (6 IDF + 6 `.err` + 6 `.end`).
- `run3_refleet3/` — 10 files (5 × `.err` + `.end`; `la_urban/way_402215469` has no run-3 entry at all).
- `open07_ab_sim/` — 11 files (4 IDF + `.err`/`.end` for both A/B arms of `way_965718402`, `.err` only
  for `way_965718403`'s A-side — see caveat below).
- `open38_t05_rebuild/` — 4 files (IDF, `.err`, `.end`, `openubem_run.log`).
- `open56_ab_arms/` — 280 files (70 buildings × 2 arms × 2 files).

---

## 5. Findings surfaced while copying (reported, not smoothed over)

- **Severe-error counts for the OPEN-42 six do not agree across the adopted run / run 2 / run 3.**
  Adopted (`phaseE_elevrb`, persisted `n_severe`, not directly recoverable — see
  `extra/MEASUREMENT_open-42_six-failures.md`): 26/7/4/12/4/24. Run 2 (copied here): 26/7/8/32/4/24.
  Run 3 (copied here, 5 of 6): 26/6/8/12/4. All three sources agree the six buildings **fatal**, and
  agree closely on three of six exact counts; they do not agree on all six. This is reported as-is —
  three different runs of evolving code are not expected to reproduce a single run byte-for-byte, and
  no claim in this task or the closed OPEN-42 record depends on the exact count matching.
- **`way/965718403`'s A-side (`SmallHotel`, as classified today) simulation has no `eplusout.end`.**
  Its `.err` exists and is non-trivial (66,110 bytes) but ends mid-line inside an ordinary `SimHVAC`
  warning block, with no `**  Fatal  **` and no completion marker of any kind — the run did not reach a
  terminal state (killed, or the scratchpad was captured mid-run). Preserved as-is; not represented as
  either a pass or a fail. Its sibling `way/965718402` **did** complete cleanly on the A-side
  (`EnergyPlus Completed Successfully`, 60,039,839 Warning; 0 Severe) — an extreme warning count in its
  own right, noted but not investigated further here (out of this task's scope).
- **`la_urban/way_402215469` (the sixth OPEN-42 building) has zero run-3 footprint** —
  `open48_refleet3/la_urban/sim_out/` does not exist at all. This matches T03's independent finding
  that `la_urban` and `nyc_centre` are the two cells with no run-3 simulation output whatsoever.

---

## 6. Controls (both mandatory)

**Control 1 — every MD5 in the manifest re-verifies against the copy.** Two independent passes:

1. At copy time, each file's source MD5 and a **freshly computed** MD5 of the destination file were
   compared before the row was written to the manifest; on any mismatch the copy would have been
   deleted and reported (none was — 0 mismatches at this stage).
2. **A second, fully independent re-verify pass**, run after `MANIFEST.md` was written, that re-reads
   `MANIFEST.md` itself (not the in-memory copy job) and re-hashes every one of the 323 destination
   files from disk against the MD5 and byte size recorded in the manifest text.

**Result: 323 / 323 verified, both passes. 0 deleted for mismatch.**

**Control 2 — total size under the 0.15 GB cap.**

**Actual: 12,565,016 bytes = 11.98 MB = 0.0126 GB — 8.4 % of the 0.15 GB cap.** (Directory total
including `MANIFEST.md` itself: 12,664,328 bytes, still 0.0127 GB.)

---

## 7. Deviation from the plan (disclosed per hard constraint 2 of the dispatch)

**The register (`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`) was not edited by
this task.** Another executor owns that file concurrently; the dispatch instructed this task to write
its proposed OPEN-53 restatement here instead, for the director to insert. This is a deviation from the
plan's T10 step 7 ("restate OPEN-53's closure condition... and name precisely what is still only on the
volatile path") only in *where* the restatement is recorded, not in whether it was produced — see §8
below for the full restatement text.

No other deviation. No git write command was run. No `.sql` file was copied. No production code was
touched.

---

## 8. Restating OPEN-53 against what is now durable

OPEN-53's recorded closure condition (2026-08-18, director ruling): *"OPEN-53 closes when E02 artifacts
required by open work are either regenerated inside a durable location or formally declared
expendable."* The 2026-08-18 (late) amendment found they were regenerated (runs 2/3) but **not** in a
durable location, and costed the fix at "a few megabytes."

**This task performs that costed fix.** 12.6 MB, 323 files, all independently re-verified, now live in
`docs/validations/overAll/evidence/open48_runs/`.

**What this discharges:** the closure condition is met **for the specific artifacts this task named and
copied** — the six OPEN-42/OPEN-11 buildings (run 2 whole, run 3's five surviving), two of OPEN-07's
three buildings (with real A/B simulation output), OPEN-07's third building (via T05's rebuilt
reproduction, since no original survives anywhere), and the OPEN-56/OPEN-09/OPEN-11 70-building A/B
`.err`/`.end` set. None of that material depends on a volatile `%LOCALAPPDATA%` or gitignored
`scratchpad/` path any longer.

**What is still only on the volatile path, named precisely:**
- **The other four `layout_assign` rebuilds and three negative controls from T05's
  `scratchpad/open38-t05-rebuild/`** (OPEN-38's remaining evidence) — gitignored, not copied (§3), no
  open item in this task's mandate names them.
- **Every other building in `open48_refleet`/`open48_refleet3`** (~8,150 of ~8,160, i.e. all but the six
  OPEN-42 buildings) — their individual IDFs and per-building simulation output remain only under
  `%LOCALAPPDATA%/Temp/ubem_validation/`. The **fleet-level aggregates** derived from them
  (`05_results.csv`, manifests) are already durable (§2); the raw per-building EnergyPlus output is not,
  and is not cited by name by any open item, so was not copied.
- **The rest of `scratchpad/e-la-20-investigation/`** (115 MB total; this task copied ~4.7 MB of it) —
  the i01/i02/i04/i05 sub-investigations and the `control_sim`/`part4_bisection` sweeps are gitignored
  and volatile; none is cited by an open item this task's mandate covers.
- **The full OPEN-56 A/B `.sql`/`.eio`/`.bnd`/etc. per-building outputs** (~5 GB at
  `%TEMP%/open56_fleet_cost/`) — only the `.err`/`.end` (1.5 MB before dedup, all copied) survive
  durably; the rest is re-derivable from the preserved IDFs plus a re-run, exactly the same
  re-derivability argument OPEN-53's own 2026-08-18 measurement made for the E02 `.sql` corpus.

**OPEN-53 stays open.** Ruling R3 discharges the closure condition **only for the material this task
named, enumerated and verified** — it is not a blanket discharge of the standing custody risk. The risk
itself (a process outside this repository can empty `%LOCALAPPDATA%`/`scratchpad` paths without the
project's knowledge, as it did once already on 2026-08-17) is unchanged by this task: nothing here
prevents recurrence, and everything named in the bullet list above is exactly as exposed to it today as
it was before this task ran. **Recommended, not taken:** the director may wish to either narrow OPEN-53's
scope to "the E02 corpus specifically, now closed by regeneration + durable copy" and open a
**new**, narrower custody item for the run-2/run-3 fleet corpus and the OPEN-38 scratchpad — or continue
carrying both under OPEN-53's existing umbrella. This task takes no position on which; that is a records
decision, not a measurement.

---

## Proposed OPEN-53 restatement (NOT yet inserted into the register)

*(For the director to insert into OPEN-53's §-section in
`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`, as a new dated amendment following
the existing 2026-08-18 (late) amendment.)*

> 🔵 **Amended 2026-08-19 (T10 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, ruling R3). The costed
> action from the 2026-08-18 (late) amendment is now done.**
>
> The six OPEN-42 buildings' and (two of three) OPEN-07 buildings' IDFs plus their `eplusout.err`/
> `.end` — the material the previous amendment named and costed at "a few megabytes" — are now copied
> into the repository at `docs/validations/overAll/evidence/open48_runs/`, alongside the OPEN-56 A/B
> arms' raw per-building `.err`/`.end` (70 buildings, 140 arm-sides) and a reconstruction of OPEN-07's
> third building (`way/401910463`, no original survives anywhere; a `layout_assign` rebuild reproduces
> its register-cited fatal signature byte-for-byte). **323 files, 12,565,016 bytes (0.0126 GB),
> every MD5 independently re-verified against the copy twice, over, no `.sql` included.** Manifest with
> per-file source path, MD5, size and citing item: `docs/validations/overAll/evidence/open48_runs/
> MANIFEST.md`. Full write-up: `extra/MEASUREMENT_open-53_evidence-preservation_2026-08-19.md`.
>
> **Two things were found already durable before this copy ran** (not duplicated): the per-cell
> `05_results.csv`/manifests backing OPEN-35/OPEN-12 (`docs/validations/overAll/results/
> open48_refleet{,3}/`, run 2 fully tracked in git, run 3's five finished cells present on disk), and
> the OPEN-56 aggregate cost-vector CSV (`openubem/outputs/comparisons/
> open56_fleet_cost_stratified.csv`).
>
> ✅ **Discharged, narrowly: the closure condition is met for the specific artifacts named above** —
> none of them depends on a volatile `%LOCALAPPDATA%`/gitignored path any longer.
>
> 🔴 **OPEN-53 STAYS OPEN.** This is not a blanket discharge. Still only on a volatile path: the other
> ~8,150 of ~8,160 buildings' individual run-2/run-3 IDFs and simulation output (their fleet-level
> aggregates are durable; their raw per-building output is not, and none of it is cited by name by an
> open item); the remaining 8 of 9 buildings from this same plan's T05 `layout_assign` rebuild
> (`scratchpad/open38-t05-rebuild/`, OPEN-38's evidence, gitignored); the ~110 MB balance of
> `scratchpad/e-la-20-investigation/`; and the ~5 GB non-`.err`/`.end` remainder of
> `%TEMP%/open56_fleet_cost/` (re-derivable from the preserved IDFs, same argument this item already
> made for the E02 `.sql` corpus). The standing risk — an external process can empty these paths without
> the project's knowledge, exactly as it did on 2026-08-17 — is unchanged by this task.
>
> **Recommended, not taken:** either narrow this item to the E02 corpus alone (now durably closed by
> regeneration + copy) and open a new item for the run-2/run-3 fleet corpus's standing custody risk, or
> keep carrying both under this item. A director records decision, not a measurement.
