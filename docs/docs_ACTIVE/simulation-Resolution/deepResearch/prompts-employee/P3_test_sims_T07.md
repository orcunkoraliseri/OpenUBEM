# P3 — Test simulations of all 4 modes (T07 → CP3) · CLUSTER

**Prereq:** v1 done — P1+P2 merged, CP2 audited green, manager has greenlit running sims.
**Paste the block below to a fresh Sonnet session.**

---

## ⚠️ AMENDMENT 2026-06-29 — fast_zone runs LOCAL, not on the cluster

**Situation:** the first P3 submission ran `auto` / `building` / `floor` to **COMPLETED, 21/21 each** on Speed (jobs 1018534 / 1018576 / 1018611). `fast_zone` (job 1019060) was stuck **PENDING** under `AssocGrpCpuLimit` (queue-blocked, not a failure). Rather than wait on the queue, the manager's ruling is: **run the fast_zone pilot LOCALLY** and merge it with the three completed cluster modes to close CP3.

**This is allowed.** The absolute cluster rule forbids compute on the Speed **login node only** — it does not apply to the local Windows desktop, which has EnergyPlus 23.1 installed. Local sims on your own machine are fine.

**What to do instead of submitting fast_zone to the cluster:**
1. **Do NOT resubmit fast_zone to Speed.** Cancel/ignore job 1019060 if it is still pending.
2. Run the **same 21-building pilot set** through **Step-3 → Step-4 → Step-5 locally** with `resolution_mode="fast_zone"` using the installed EnergyPlus 23.1. Keep auto/building/floor as the already-harvested cluster results — do not re-run them.
3. Harvest **all four modes** (3 cluster + 1 local) into the single CP3 EUI table and `openubem/outputs/comparisons/t07_resolution_pilot_eui.csv`.
4. **Document the environment split in the CP3 report and the §8 entry:** auto/building/floor = Speed (Linux); fast_zone = local (Windows). Note that EnergyPlus EUI is platform-deterministic to within rounding, so the `auto` regression anchor and the cross-mode ordering remain valid — flag any EUI that differs by more than float rounding as a finding, not a pass.
5. The 6/21 fast_zone fallbacks (perimeter_core → one_zone_per_floor) already logged in the prior run still hold — re-confirm them from the local run and report the count.

Everything else below (acceptance checks, CP3 stop, §8 progress-log entry, no-login-node rule) is unchanged.

---

> 🔴 ABSOLUTE: this is a **cluster** task. All compute goes through `sbatch` fire-and-forget on Speed; read
> the output files afterward. **Never** run `srun`, `ssh … python`, or any computation on the login node
> (`speed-submit2`). Login node is for `mkdir`/`scp`/`tar`/`squeue`/`sacct` only. Monitoring interval ≥ 30 min.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\PLAN_resolution_mode_switch.md`
§6 **T07** and §9 (expected cross-mode divergence) before doing anything.

Execute **T07 only**, then **STOP at checkpoint CP3** (§7). Do not start T08 — the full city sweep is a
separate, manager-gated decision.

What to do:
- Pick a **small** representative test set: one small validation cell, **or** ~20–50 real buildings spanning
  at minimum `MidriseApartment`, `SmallOffice`, a large office, and `Warehouse`.
- Run **Step-3 → Step-4 → Step-5** end-to-end for **each** of the four modes
  `resolution_mode ∈ {auto, building, floor, fast_zone}` on that test set, via the `resolution_mode` kwarg.
- Submit as a **tiny `sbatch --array`** over (mode × buildings). Fire-and-forget; read outputs after.

Acceptance to report at CP3:
- No EnergyPlus **Fatal** in any mode; all results **parse**.
- `auto` matches the existing per-building baseline on the subset (regression).
- Heating EUI ordering reads **`building ≤ floor ≤ fast_zone`** per §9 (sanity, not a hard gate — note any
  building that inverts and why).
- Fallback rows (narrow/courtyard → `one_zone_per_floor` under `fast_zone`) are **logged and counted**.

Why this is cheap-first: T06 only proved the IDF *builds*; this proves all 4 modes *run through E+ and
parse*. It de-risks the expensive T08 city sweep (~8.7 h × many runs) for a tiny cost.

At CP3, **append a T07 progress-log entry under §8** of the PLAN and **report the test table** (per-mode EUI
on the subset, fallback count, any Fatal). **Then STOP** for the manager to greenlight the full T08 sweep.

Do not propose alternatives. If the spec is ambiguous, or if any step would require login-node compute,
**STOP and ask** — never bypass the cluster rule.
