# P4b — Watch the cluster half, harvest the 5 Linux cells (T08 → CP4) · CLUSTER-HARVEST

**Context:** The T08 local half (7 Windows cells) is complete (PLAN §8 M15/M16). The cluster half — **5 Linux
cells: `nyc_centre, nyc_urban, nyc_suburban, nyc_rural, la_centre`, all 4 modes (20 `sbatch` arrays)** — was
submitted and is draining behind the user's `3J_8B_resid`. This task **watches** those arrays and, the moment
they finish, **harvests** them with the existing `scripts/cluster/t08_harvest_results.py`.

**You are a CHEAP recurring babysitter.** Each firing is a fresh session. Do the minimum, be idempotent, and
**exit fast** if there is nothing to do. Do **not** burn reasoning tokens.

> 🔴 ABSOLUTE: the ONLY Speed contact is **read-only login-node** (`squeue`). No `srun`/`ssh … python`/compute
> on the login node. The harvest's SQL fetch + parse runs **locally on this Windows desktop** (that is desktop
> compute, allowed). Default to no comments. Stop and ask on ambiguity. Figures → `openubem/outputs/`.

## Step 0 — guards (run every firing, in order; exit immediately when a guard says so)

1. **Already harvested?** If `openubem/outputs/comparisons/t08_all_modes_eui.csv` exists AND contains all of
   `{nyc_centre, nyc_urban, nyc_suburban, nyc_rural, la_centre}` each with all 4 modes → **DONE. Exit, do
   nothing** (the cron will auto-expire; you may also `CronList`→`CronDelete` the `P4b` job to stop early).
2. **Harvest in progress?** If a lock file `%TEMP%/t08_cluster_harvest.lock` exists and is < 3 h old →
   another firing is harvesting. **Exit.** (If it is ≥ 3 h old it is stale; delete it and continue.)
3. **Arrays still running?** Run **one** login-node read:
   `ssh o_iseri@speed.encs.concordia.ca "squeue -u o_iseri -h -o '%j %T' | grep -c t08"`.
   If the count is **> 0** → arrays still `PENDING`/`RUNNING`. Print a one-line status
   (`<n> t08 arrays still queued/running — waiting`) and **EXIT**. Do not harvest.

Only if all three guards pass (not yet harvested, no active harvest, **zero** t08 arrays left in the queue) do
you proceed to Step 1.

## Step 1 — harvest the 5 cluster cells (local compute)

Write the lock file `%TEMP%/t08_cluster_harvest.lock`, then run:

```
py -3 scripts/cluster/t08_harvest_results.py --cells nyc_centre nyc_urban nyc_suburban nyc_rural la_centre
```

This fetches sql+end+err per (cell×mode), parses the 9-end-use EUI, writes
`openubem/outputs/comparisons/t08_all_modes_eui.csv` + `t08_mode_cell_summary.csv` + `t08_*.png`, and prints the
CP4 tables (completion, auto-vs-phaseE, per-mode×per-cell EUI, 9-end-use split, fast_zone fallbacks). Delete the
lock file when it returns. If the run errors, capture the traceback, delete the lock, **STOP and report** — do
not retry blindly.

## Step 2 — record + hand to the manager (do NOT interpret)

1. **Expected, not a regression — do not chase it:** the harvest's "auto regression vs phaseE" section WILL
   flag structural deltas on **QuickServiceRestaurant / FullServiceRestaurant / SuperMarket** (and minor
   school/hospital) for the NYC/la_centre cells. PLAN §8 **M16** already root-caused this: the on-disk phaseE
   benchmark predates the cooking+refrigeration realism commits (benchmark `refrigeration_eui = 0`), so `auto`
   legitimately runs higher on food-service. Report the numbers; **annotate them as the known stale-benchmark
   offset.** Flag only NON-food structural deltas, if any.
2. **Append a T08 progress-log entry under PLAN §8** (`docs/docs_ACTIVE/simulation-Resolution/PLAN_resolution_mode_switch.md`):
   cluster-half completion table (per cell×mode success/failed/fatal), per-cell mean `auto` EUI, fast_zone
   fallback counts, and any NON-food structural delta. Note this is the **cluster (Linux) half**; the local
   (Windows) half is `t08_local_remainder_eui.csv` (M15).
3. **Notify** (PushNotification) that the cluster half harvested and CP4 is ready for the manager to assemble
   the combined 12-cell table. Then **STOP** — do **not** start T09, do **not** build the combined table or
   the combined figures (that synthesis + go/no-go is the manager's job).
