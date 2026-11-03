# MEASUREMENT — OPEN-53: custody re-inventory against today's disk (2026-08-19)

**Task:** T06 of `../implemenation/previous/PLAN_twenty-items-2026-08-19.md`. Script:
`scripts/analysis/open53_t06_custody_reinventory_2026-08-19.py`. Output:
`openubem/outputs/comparisons/corpus_inventory_2026-08-19.csv`.

## 1. What was re-scanned

Four corpora, fresh `os.walk`, no cached counts:

| corpus | root |
|---|---|
| E02 harvest | `%LOCALAPPDATA%/Temp/ubem_e02_harvest` |
| `open48_refleet` (run 2) | `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet` |
| `open48_refleet3` (run 3) | `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3` |
| `open48_refleet4` (run 4) | `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4` |

All four are present on disk. Nothing was moved, copied, compressed or deleted by this task.

## 2. Headline finding: a SECOND sweep event has taken the E02 harvest's `.eio` files, today

Independent recount of `.eio`/`.err`/`.sql`/`.end` inside E02 harvest (40,800 building
directories, matching the register exactly):

```
n_building_dirs=40800  n_eio=145  n_err=40800  n_sql=39926  n_end=39925
```

`.err` (40,800), `.sql` (39,926) and `.end` (39,925) reproduce the register's 2026-08-18 count
**exactly** — no further loss on those three extensions since the 2026-08-17 sweep already on
record. **`.eio` does not reproduce**: register/prior census recorded 40,800 (zero empty), disk
today holds **145**. That is a loss of **40,655 files since the last census**, on an extension
that survived the 2026-08-17 event untouched.

Per the "how to test" clause, the discrepancy is explained with a timestamp, not asserted:

- Every one of the 40,655 directories now missing `eplusout.eio` carries directory mtime
  **2026-08-19 16:19**, to the minute, with **zero other minute-bucket among the 40,655** —
  checked by walking the full corpus and bucketing missing-`.eio` directory mtimes by
  `time.strftime('%Y-%m-%d %H:%M', ...)`. One bucket, one event.
- Spot-checked across unrelated cells and modes (`austin_centre_building`,
  `nyc_urban_layout_assign`, `austin_suburban_fast_zone`, `la_centre_auto`, `nyc_centre_auto`):
  all five carry the same `2026-08-19 16:19:1x`–`16:19:3x` mtime range.
- The 145 surviving `.eio` files are concentrated in a few cell/mode buckets that appear to have
  been either untouched or only partly touched by the sweep — `la_rural_*` (15 of 5 modes = 75)
  and `la_urban_*` (11–15 of 5 modes = 60) account for 135 of the 145; the other 10 are singletons
  scattered across `austin_centre_auto`, `austin_centre_floor`, `austin_suburban_{auto,fast_zone,
  floor}`, `la_centre_layout_assign`, `nyc_centre_fast_zone`, `nyc_rural_layout_assign`. No single
  cell or mode survived intact, and no obvious explanation (alphabetical order, size, recency) fits
  the survivor set from this artifact alone.
- No code in `scripts/` or `openubem/` touches `eplusout.eio` for deletion: `grep -n
  "eplusout.eio" scripts/ openubem/` returns one hit, `scripts/cluster/t08_local_remainder.py:84`,
  which is a **comment** (`# eplusout.eio must never be deleted — it is the only record of
  simulated floor area.`), not code. The nine `scripts/analysis/*.py` files that call
  `unlink`/`os.remove`/`shutil.rmtree` were each checked individually for any reference to
  `ubem_e02_harvest`; none has one — every deletion in that list targets a private scratch
  directory the same script created (`scratch.unlink`, `WORK`, `tmp_dir`, `scratch_base`,
  `scratch_path`, `db_path`), never the harvest tree.

**This is the same signature as the 2026-08-17 16:21 `.sql`/`.end` sweep documented in OPEN-53's
register entry — external to this repository, batch/fleet-wide, one timestamp — except this time
it targets `.eio` and it happened during this very pass (today, 2026-08-19, roughly two hours
before this task ran).** Nothing in this task's toolset can identify the process responsible.
Reported as a finding, not investigated further (out of this task's scope).

`open48_refleet` (run 2), `open48_refleet3` (run 3) and `open48_refleet4` (run 4) show **no**
comparable loss: their `.err`, `.sql`, `.end`, `.gpkg`, `.csv`, `.geojson`, `.idf`, `.parquet`
counts all read as expected populations (8,160 / 5,215 / 8,160 buildings respectively, matching
each run's known completed-cell count). `open48_refleet` (run 2) legitimately has **zero** `.eio`
files by design, not by loss — spot-checked directly
(`open48_refleet/nyc_centre/sim_out/relation_11171765/` holds only `.end`/`.err`/`.sql`) —
`.eio` was apparently never requested/kept for that run, unlike run 3 and run 4 which both carry
`.eio` for effectively their whole populations (5,215/5,215 and 8,160/8,160). This rules out a
fleet-wide `.eio`-targeting habit; the sweep hit E02 harvest specifically.

## 3. Per-corpus totals (today, full walk)

| corpus | dirs | files | total size |
|---|---:|---:|---:|
| E02 harvest | 40,861 | 120,796 | 10.03 GB |
| `open48_refleet` (run 2) | 8,297 | 41,014 | 79.75 GB |
| `open48_refleet3` (run 3) | 5,334 | 35,214 | 41.58 GB |
| `open48_refleet4` (run 4) | 8,297 | 49,179 | 81.09 GB |

`open48_refleet` (run 2) reproduces the register's 79.75 GB / 41,014-file figure **exactly**.

`open48_refleet3` (run 3) does **not** reproduce the register's 43,162-file / 45.73 GB figure —
disk today holds 35,214 files / 41.58 GB in `open48_refleet3` proper, **plus** two adjacent
directories not scanned by the register's original count: `open48_refleet3_t02a3` (1,593 files,
0.13 GB) and `open48_refleet3_t02a4` (9,550 files, 4.45 GB), both created 2026-08-19 per the
`evidence-preservation` doc's account of T02's crash-recovery reruns. Summed, that is 46,357
files / 46.16 GB — **larger**, not smaller, than the register's figure. This is consistent with
growth from partial reruns after the original overnight census, not further loss; it is reported
because rule 11 requires flagging any number that does not reproduce, not because it indicates a
new custody problem for run 3.

E02 harvest's 40,800 building-directory count reproduces exactly (§2). `open48_refleet4` (run 4)
has no prior published total to compare against; F2's path shape (`results/` subdirectory) is
confirmed on disk (checked `open48_refleet4/nyc_centre/`: `01_buildings.gpkg`,
`04_simulation_manifest.parquet`, `fleet_staging/`, `results/05_neighbourhood_summary.json`).

## 4. Cited-evidence subset, re-derived (not quoted)

The register's X06 finding claims "under 0.12 GB preserves every published finding of this pass"
for run 2, computed as `.err` + `.gpkg`/`.csv`/`.geojson`. Re-derived independently from this
task's own fresh walk of `open48_refleet`:

```
.err      90,655,926 bytes
.gpkg     11,939,840 bytes
.csv       4,242,536 bytes
.geojson  11,166,965 bytes
---------------------------
total    117,983,267  bytes  =  0.1180 GB
```

**Reproduces the register's "under 0.12 GB" claim** (0.1180 GB is indeed under 0.12 GB, and close
enough to the prior 0.12 GB estimate to be the same measurement, not a coincidence). `.idf` for run
2 totals 3.3595 GB (16,332 files), matching the register's "~3.5 GB preserves the ability to
re-run one" to within the same order — the register's figure was described as approximate and is
treated as such here, not re-quoted as exact.

A broader keyword scan of every `extra/*.md` file plus the register for literal strings naming
`ubem_e02_harvest`, `open48_refleet`/`open48_refleet3`/`open48_refleet4`, and `ubem_validation`
found 64 distinct cited path fragments (raw match list in the script's stdout, not reproduced
here in full — most are directory-level references, e.g. `open48_refleet3/nyc_suburban/`, not
individual filenames beyond the extension classes already summed above). No cited fragment names
a file extension outside `.err`/`.gpkg`/`.csv`/`.geojson`/`.idf`/`.parquet`, so the sum above is
the complete cited-evidence subset for run 2 under this task's search method.

## 5. What this changes for OPEN-53

**Does not close the item — reinforces the standing risk the item is already open on.** The
2026-08-19 16:19 `.eio` sweep is a second, independent demonstration of the exact hazard OPEN-53's
closure condition names ("a process outside this repository can empty these paths without the
project's knowledge... to the same paths, to `scratchpad/`, or to any future artifact held outside
the repo" — register text, 2026-08-18 ruling). It happened during this very pass, on a path
(`ubem_e02_harvest`) already flagged as compromised once. No published number is known to depend
on E02 harvest `.eio` specifically (the fleet EUI denominator draws from `open48_refleet4`'s own
`.eio`, not E02's — separate corpus, unaffected here). **Recommendation only, not applied:** the
same "regenerate in a durable location or declare expendable" closure condition already on the
item applies to E02 harvest as a whole; this measurement adds evidence, it does not change the
ruling.
