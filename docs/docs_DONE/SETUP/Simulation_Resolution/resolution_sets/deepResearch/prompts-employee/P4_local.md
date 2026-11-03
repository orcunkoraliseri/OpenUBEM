# P4_local — Finish the sweep on the LOCAL desktop (T08 remaining cells → CP4) · LOCAL

**Context:** The cluster sweep (`P4_full_sweep_T08.md`) only half-submitted. The local driver
(`scripts/cluster/t08_full_sweep.py`) processes cells one at a time (NYC → LA → Austin), and the
process **died partway through `la_urban`** before writing `t08_job_ids.json`. What reached Speed (now
queued `PENDING / AssocGrpCpuLimit`) is **5 full cells on Linux**; the rest never got generated or
submitted. The user decided: **run the remaining cells on this Windows desktop** via the proven local
EnergyPlus 23.1 path, leaving the 5 already-queued cells on the cluster.

**This is a LOCAL task.** Do **not** submit anything new to Speed. The only Speed contact allowed is
**`scancel`** of two stale array jobs (lightweight login-node op) — see step 0.

**Paste the block below to a fresh Sonnet session.**

---

> 🔴 ABSOLUTE: never run `srun`/`python`/any compute on the Speed login node. The ONLY remote command in
> this task is `scancel` (step 0). Everything else is local EnergyPlus 23.1 on this Windows desktop.
> Default to no comments. Stop and ask on spec ambiguity — never invent. All `.png` figures →
> `openubem/outputs/`. No `.py` under `docs/`.

Read first:
- `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\PLAN_resolution_mode_switch.md`
  §6 **T08**, §7 **CP4**, §9 (expected divergence).
- `openubem/outputs/comparisons/README.md` (figure + provenance convention).
- `scripts/cluster/t08_full_sweep.py` (reuse its `run_step2` and `run_step3_mode` helpers verbatim).
- `scripts/cluster/t07b_run_auto_refit_local.py` and `scripts/cluster/t07_run_fast_zone_local.py`
  (the proven LOCAL Step 3→4→5 plumbing — generalize this, do not reinvent it).
- `scripts/cluster/t08_harvest_results.py` (the EXACT output schema your local harvest must match).

Execute **T08 (local remainder) only**, then **STOP at checkpoint CP4** (§7). Do not start T09.

## The platform-consistency rule (why these exact cells)

Every cell must have all 4 of its modes on a **single** EnergyPlus platform, or the per-cell cross-mode
comparison mixes Linux/Windows rounding and is meaningless. Therefore:

| Stays on CLUSTER (Linux — already queued, leave alone) | Runs LOCAL on this desktop (Windows) |
|---|---|
| nyc_centre, nyc_urban, nyc_suburban, nyc_rural, **la_centre** — all 4 modes each (20 arrays, queued) | **la_urban, la_suburban, la_rural, austin_centre, austin_urban, austin_suburban, austin_rural** — all 4 modes each |

`la_urban` is the special case: its `auto`+`building` are *already* queued on the cluster. To keep that
cell single-platform you must run **all 4 of its modes locally** and **cancel** the 2 cluster arrays.

## Step 0 — cancel the 2 stale la_urban cluster arrays (ONLY remote command)

```
ssh o_iseri@speed.encs.concordia.ca "scancel 1029823 1029824"
```

(`1029823` = `t08_la_urban_auto`, `1029824` = `t08_la_urban_building`.) Confirm with
`squeue -u o_iseri | grep la_urban` → expect **no** la_urban rows. If those job IDs no longer exist or
are already RUNNING/COMPLETED, **STOP and report** before generating anything (we may have a partial
la_urban result on the cluster to reconcile).

## Step 1 — safety gate (same AMENDMENT as the cluster sweep)

Confirm `openubem/idf/builder.py` contains the line `if self.resolution_mode != "auto":` immediately
before the `orient(...)` call. If absent, **STOP** — do not generate any IDF. (Reuse
`t08_full_sweep._verify_orient_gate()`.)

## Step 2 — run these 7 cells × 4 modes locally, end to end

For each cell in **{la_urban, la_suburban, la_rural, austin_centre, austin_urban, austin_suburban,
austin_rural}** and each mode in **{auto, building, floor, fast_zone}** (`zone` is excluded):

1. **Steps 1–3** exactly as the cluster sweep does — load the cell's `01_buildings.gpkg` from
   `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/`, then call `t08_full_sweep.run_step2`
   and `t08_full_sweep.run_step3_mode` (so IDFs are regenerated from the CURRENT working tree with the
   orient gate; **`trim_outputs=True`** — do NOT keep hourly per-zone variables).
2. **Step 4 (simulate) + Step 5 (harvest) LOCALLY** on installed EnergyPlus 23.1, using the same runner
   pattern as `t07b_run_auto_refit_local.py` / `t07_run_fast_zone_local.py`. No Speed submit.

Write a thin driver script for this (e.g. `scripts/cluster/t08_local_remainder.py`). It must:
- accept `--cells` / `--modes` (default = the 7 cells × 4 modes above) so a crashed run can resume a
  subset without redoing finished cells;
- be **fire-and-forget on the local box**: launch it as a background process, then poll **≥ 30 min**
  apart (prefer event-driven completion). Use a **cheap model** to babysit it — do not spend reasoning
  tokens watching a sim loop.

**Resource reality:** this is ≈ 17k simulations and will peg this desktop for ~1.5–2.5 days,
`fast_zone` being the slow leg. That is expected; do not "optimize" it away or change scope.

## Step 3 — fold results into the comparison, matching the cluster schema

Harvest each `(cell, mode)` total + **9-end-use** EUI into `openubem/outputs/comparisons/` in the
**exact same CSV schema** that `t08_harvest_results.py` produces for the cluster cells, so the two halves
merge into one CP4 table. Add a **provenance row** for every local cell recording
`platform = Windows-local`, mode, cell, and build date (per the comparisons README convention). Do **not**
overwrite the cluster harvest outputs or the existing `t07_*` CSVs — use a distinct filename
(e.g. `t08_local_remainder_eui.csv`).

## Acceptance to report at CP4 (before any interpretation)

- All 4 modes complete for all 7 local cells, with a **documented fallback count** per (cell, mode)
  (the `fast_zone` perimeter_core single-zone fallbacks, as `run_step3_mode` already prints).
- **`auto`-regression check is clean and strict here:** these cells run on Windows, the *same* platform
  as the phaseE benchmark, so each local cell's `auto` total + per-end-use EUI must match
  `…/phaseE/<cell>/05_results.gpkg` within **< 1 kWh/m²** (no platform offset excuse — this is the exact
  bit-reproduction T07b already proved for la_rural). Flag any cell that does not match.
- The per-mode × per-cell **EUI + 9-end-use table** for the 7 local cells, reported verbatim.

## Stop & report

At CP4, **append a T08 progress-log entry under §8** of the PLAN noting the **cluster/local split**
(which 5 cells are Linux-cluster, which 7 are Windows-local, and that la_urban's 2 cluster arrays were
cancelled). Then report the table above and **STOP** for the manager. Do **not** interpret or "fix"
cross-mode differences — §9 says they are expected physics. The combined CP4 table (cluster 5 cells +
local 7 cells) is assembled by the manager once the cluster half harvests; your job is the local half.

Do not propose alternatives. If a step needs login-node compute beyond the single `scancel`, or the
spec is ambiguous, **STOP and quote the conflict.**
