# MEASUREMENT — OPEN-53: is the missing 874/875 still on Speed? (2026-08-20)

**Task:** T05 of `../implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`. Script:
`scripts/analysis/open53_remote_inventory_2026-08-20.py`. Outputs:
`openubem/outputs/comparisons/open53_remote_inventory_2026-08-20.csv` (remote/local counts) and
`openubem/outputs/comparisons/open53_remote_inventory_2026-08-20_parse.csv` (per-sample
`parse_building()` result). Population: the two Austin sub-cells named in
`extra/MEASUREMENT_open-53_missing-sql.md` §3 (`austin_suburban_fast_zone`,
`austin_suburban_floor`), 874 of the 875 shortfall directories, both at 100% of the bucket.
The remaining 1 (`nyc_centre_fast_zone/way_1240348353`, a `truncated` run) is out of scope for
this task.

## 1. Remote run root, and how it was found

`/speed-scratch/o_iseri/fleets/e02_{cell}_{mode}/out/{stem}` — `REMOTE_FLEET_BASE` at
`scripts/analysis/e02_cluster_readonly_audit.py:35`, directory-naming convention at the same
file's lines 143 (`known_dir = f"{REMOTE_FLEET_BASE}/e02_nyc_centre_auto"`) and 191–192
(`f"{REMOTE_FLEET_BASE}/e02_{ctrl_cell}_{ctrl_mode}/out/{ctrl_failed}"`). Connected via `_ssh()`
imported from `scripts/cluster/t08_harvest_results.py:104` (tcsh-safe, `bash -lc` wrapper);
connectivity confirmed in one attempt (`hostname && whoami` → `speed-submit2.encs.concordia.ca`
/ `o_iseri`).

## 2. Remote `.sql` / `.end` counts (C14)

Login-node, read-only (`find`/`wc` only, output capped to counts):

| cell_mode | remote dir | remote n_dirs | remote n_sql | remote n_end | local n_dirs | local missing `.sql` |
|---|---|---:|---:|---:|---:|---:|
| `austin_suburban_fast_zone` | `/speed-scratch/o_iseri/fleets/e02_austin_suburban_fast_zone/out` | 437 | 437 | 437 | 437 | 437 |
| `austin_suburban_floor` | `/speed-scratch/o_iseri/fleets/e02_austin_suburban_floor/out` | 437 | 437 | 437 | 437 | 437 |
| **total** | | **874** | **874** | **874** | **874** | **874** |

Local shortfall restated beside it: 874 of the 875-directory register figure (F8) sit exactly in
these two buckets, at 100% of each (`extra/MEASUREMENT_open-53_missing-sql.md` §3). The remote
count reproduces that number exactly, file for file: 874 `.sql` and 874 `.end` exist on Speed for
the same 874 directories that are missing them locally.

## 3. Verdict (C15)

**The remote files exist → this is a harvest defect.** 874 `.sql` and 874 `.end` are present on
Speed for all 874 locally-short directories in both buckets; nothing was lost on the simulation
side. The remedy question (re-fetch vs. re-simulate) is the user's — this task does not choose.

## 4. Sample fetch and parse (C16)

20 of 874 fetched by `scp` (10 per bucket, first 10 stems in each remote directory's listing),
into `<scratchpad>/open53_sample/<cell_mode>/<stem>/`, alongside the matching local `eplusout.eio`
(present for all 874 already, per the register: the shortfall is `.sql`/`.end` only). **20/20 scp
transfers succeeded** (`.sql` and `.end` both).

**20/20 ran through `parse_building()` without raising, and 0/20 returned a non-null
`total_eui_kwh_m2`.** All 20 return `parse_status="failed_zone_mismatch"`,
`error_summary="zone count mismatch: found 0, manifest says 1"` — quoted verbatim, identical
string on every sample in both buckets.

**Root cause, checked at the artifact, not guessed:** the fetched SQL files carry **no zone-level
report variables at all** — `SELECT DISTINCT Name FROM ReportDataDictionary` on two samples (one
per bucket) returns only facility/meter-level rows (`Electricity:Facility`,
`InteriorLights:Electricity`, `Cooling:Electricity`, `Heating:NaturalGas`, …), no
`Zone Lights Electricity Energy` and no `Zone Ideal Loads*`. `_check_zone_integrity()`
(`openubem/results/parser.py:220`) builds `zone_keys` from exactly those two variable names; with
neither present, `zone_keys` is empty regardless of what `num_zones` the manifest states, so
`resolved_zone_ids` is always 0 and the gate's `len(resolved_zone_ids) == 0` branch
(`parser.py:257`) fires unconditionally for this population. This is **not** an artifact of this
script's placeholder `num_zones=1` — the same result would occur for any manifest value. It is a
genuine property of the `fast_zone`/`floor`-mode SQL output for this batch: zone-level detail was
not written, only meters.

This is reported as a finding, not remedied: whether `parse_building()` should fall back to a
meter-only EUI when zone-level keys are absent is a design question outside this task's scope.

## 5. C14–C16

- **C14 — PASS.** Remote counts reported for both `.sql`/`.end`, remote path stated, local
  shortfall (874/875) restated beside it.
- **C15 — PASS (the decisive one).** One-sentence verdict: remote files exist → harvest defect.
- **C16 — PASS, negative branch.** 20/20 fetched; 20/20 parsed without exception; 0/20 produced a
  non-null `total_eui_kwh_m2`; all 20 failures are listed with the identical quoted error string,
  traced to a real absence of zone-level report variables in this SQL population — not a script
  artifact.

## 6. Scope discipline

No `srun`, no `sbatch`, no `ssh ... python`. Every remote command ran on the login node
(`find`/`wc`/`ls`/`scp` only) with output capped to counts and ≤10 example paths per bucket — no
full directory listing was ever brought back. Nothing was re-fetched beyond the 20-file sample; no
re-simulation was run; no remedy was applied.
