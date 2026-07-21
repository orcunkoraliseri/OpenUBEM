# RESUME — Opus MANAGER session · resolution_mode sweep (T08 → CP4)

**Paste this whole file as the first message to a fresh Opus manager session.** It is self-contained:
read it top-to-bottom and you have the full state without re-reading the transcript. Date opened:
2026-06-30.

---

## 0. Who you are and the one job left

You are the **MANAGER** (architect/auditor) for OpenUBEM's user-selectable `resolution_mode`
thermal-zoning sweep. You dispatch cheap Sonnet/Haiku executors, audit their reports, maintain the **§8
progress log** of the active PLAN, and explain results. **You NEVER write feature code** (`openubem/`) —
manager edits markdown plan docs + test files and audits only.

**The feature is BUILT and validated.** v1 code (T01–T06: `auto`/`building`/`floor`/`fast_zone` wiring +
`auto`-baseline-restoring orient gate) is done and green (CP1–CP3b passed; see PLAN §8 M01–M12). The
**only** open work is the post-v1 full sweep **T08 → checkpoint CP4**, then the go/no-go to greenlight
T09/P5. `zone` mode is deferred to a separate later arc (PLAN §12) — not your problem now.

**Binding docs (read in this order if you need detail):**
1. `docs/docs_ACTIVE/simulation-Resolution/PLAN_resolution_mode_switch.md` — the active PLAN. **§8 is the
   binding progress log** (latest entry = M17). §7 = CP4 acceptance. §9 = expected cross-mode physics.
2. `docs/docs_ACTIVE/simulation-Resolution/deepResearch/prompts-employee/P4b_cluster_harvest.md` — the
   cluster-harvest babysitter prompt the cron runs each tick.
3. `docs/docs_ACTIVE/simulation-Resolution/deepResearch/prompts-employee/P4_local.md` — the (completed)
   local-half prompt; documents the cluster/local split and output schema.

---

## 1. The T08 sweep — what it is

T08 = full 4-mode re-simulation across all **12 validation cells** (NYC 4A / LA 3B / Austin 2A, **8,160
buildings**) × **4 modes** (`auto`, `building`, `floor`, `fast_zone`; `zone` excluded) = 48 sbatch arrays.
It half-submitted, so it was **split across two platforms** (PLAN §8 M14; platform-consistency rule — every
cell keeps all 4 modes on ONE EnergyPlus platform):

| Half | Cells | Status |
|---|---|---|
| **LOCAL (Windows, 7 cells)** | la_urban, la_suburban, la_rural, austin_centre, austin_urban, austin_suburban, austin_rural | ✅ **COMPLETE** — `openubem/outputs/comparisons/t08_local_remainder_eui.csv`, 28/28 legs, 14,496 success / 24 failed / 0 fatal (M15) |
| **CLUSTER (Linux, 5 cells)** | nyc_centre, nyc_urban, nyc_suburban, nyc_rural, la_centre | ⏳ **RUNNING** on Speed — 20 sbatch arrays draining behind the user's own job; harvest pending (M17) |

---

## 2. EXACT live state (as of 2026-06-30, hand-off moment)

- **Cluster:** ~**48 t08 array ELEMENTS** still PENDING/RUNNING (one element per building, not per array).
  Draining slowly; **nyc_centre is the long pole** (largest cell — its `fast_zone`/`floor`/`auto` legs are
  the bottleneck; `nyc_centre_building` is the only individually-complete array). The four small cluster
  cells (nyc_urban/suburban/rural, la_centre) are on their tail elements. **0 of 5 cells fully drained.**
- **The harvest is ALL-OR-NOTHING by design.** P4b Step 0 guard 3 requires the *entire* t08 queue to hit
  **0** before the local fetch+parse runs, producing ONE combined `t08_all_modes_eui.csv` + figures. There
  is **no per-cell incremental results harvest** — you can only log queue-drain milestones until the single
  harvest fires.
- **Recurring cron `1613accb`** (schedule `13,43 * * * *`, session-only, auto-expires 7 days) is LIVE. Each
  tick it dispatches a fresh cheap Sonnet to run P4b. When the queue empties, that Sonnet runs the harvest,
  writes the cluster §8 entry, and PushNotifies.

> 🔴 **ABSOLUTE constraints (carry verbatim):**
> - **NEVER** run blocking `srun`/`ssh … python`/any compute on the Speed login node. ALWAYS `sbatch`
>   fire-and-forget + read output. Login node only for `squeue`/`sacct`/`scancel`/`mkdir`/`scp`/`tar`.
>   The only Speed contact in P4b is a **read-only `squeue`**; the harvest fetch+parse is **local desktop**
>   compute (allowed).
> - **DO NOT TOUCH** the user's `3J_8B_resid` array (job **1029756**) — different project. Our t08 jobs
>   queued FIFO behind it under `AssocGrpCpuLimit`.
> - Manager writes **no feature code**; markdown + tests only. No `.py` under `docs/`. Never edit `main.py`
>   (root), OVERVIEW, or DESIGN. Git handled externally — never commit/offer to. Default no comments.
>   Figures → `openubem/outputs/` (flat). Min monitoring interval **30 min**; cheap models for monitoring.
>   Stop and ask on spec ambiguity. **Always update §8 progress log.**

---

## 3. Decisions ALREADY MADE — do not re-litigate

- **Food-service `auto`-vs-phaseE offset = stale benchmark, ANNOTATE (do not regenerate)** (M16, user
  decision). Root cause pinned per-end-use: on cooking-heavy archetypes (QuickServiceRestaurant ×40,
  FullServiceRestaurant ×21, SuperMarket ×4, minor school/hospital) current `auto` runs **+423.45 kWh/m²**
  = cooking +232.90 + refrigeration +190.55. The on-disk phaseE benchmark **predates** the cooking/dhw/
  refrigeration realism commits (b2ca38f, e8e03d2) → benchmark has `refrigeration_eui=0` and pre-realism
  cooking. **`auto` code is correct; the anchor is stale.** Non-cooking archetypes bit-reproduce phaseE
  (la_suburban 1343 bldgs mean |Δ| = 0.004). **The identical offset is EXPECTED on the NYC/la_centre
  cluster cells — do not chase it at CP4.** Flag only NON-food structural deltas.
- **Wait for the cluster, do NOT pull the 5 cells local** (M16) — ~18k sims / ~2 days to save ~1 h.
- **way/472960999 (MidriseApartment)** — a known minor pre-existing per-building `derive_num_floors`/area
  edge (~1.8% EUI shift), non-blocking; re-check at CP4 (M12).

---

## 4. Your loop until the harvest fires (reactive, cheap)

Each time the user pastes a **"P4b cluster-harvest tick"** instruction:
1. Dispatch ONE cheap Sonnet (Agent tool, `subagent_type "claude"`, `model "sonnet"`) with the P4b prompt
   (the user's tick message contains it verbatim). **Do NOT do harvest work in Opus** — only dispatch and
   relay the agent's one-line queue status.
2. When it returns, relay the one-line count (e.g. "48 t08 arrays still queued/running — waiting").
3. If any cluster cell has **fully drained** (all 4 modes zero elements), update the **M17 drain-tracker
   table** in §8.
4. If the agent reports the **harvest COMPLETED** (`t08_all_modes_eui.csv` now has all 5 cluster cells ×
   4 modes), **`CronDelete 1613accb`** to stop the cron, then proceed to §5 (CP4 assembly).

(You may also be invoked autonomously by the cron's notification rather than a user tick — same flow.)

---

## 5. CP4 assembly — THE MANAGER'S synthesis job (do this once both halves are harvested)

The cron's Sonnet only harvests the cluster half and stops. **You** assemble the combined 12-cell CP4
deliverable. Inputs:
- Local 7 cells → `openubem/outputs/comparisons/t08_local_remainder_eui.csv` (M15, done).
- Cluster 5 cells → `openubem/outputs/comparisons/t08_all_modes_eui.csv` (written by the harvest).

CP4 acceptance (PLAN §7) + tasks:
1. **Combined per-mode × per-cell table:** mean EUI + **9-end-use split** for all 12 cells × 4 modes,
   `auto` as the reference column.
2. **Fold in the user-approved cross-mode comparison figures** (→ `openubem/outputs/`).
3. **`auto`-regression check, platform-aware:** local cells strict <1 kWh/m² vs phaseE (same Windows
   platform — proven bit-repro); cluster cells Linux vs Windows-phaseE — accept a small uniform platform
   offset, flag only **structural per-archetype** deltas. **Annotate the food-service offset as the
   expected stale-benchmark artifact (M16) — not a regression.**
4. **§9 physics sanity** of cross-mode deltas — heating intensity should order roughly
   `building ≤ floor ≤ fast_zone`-ish (coarse single-zone cancels core-heat/perimeter-cool); city-scale
   wash-out < 2.3%. These divergences are **correct physics, do not "fix" them** (PLAN §9).
5. **Itemize the 24 local failed sims**; re-check the way/472960999 edge (M12); document fast_zone
   perimeter_core single-zone fallback counts per (cell, mode).
6. **Append a CP4 §8 entry** with the combined table + verdict.
7. **CP4 go/no-go.** If clean → greenlight T09/P5 (the deep-research literature-validation prompt set).

**PING THE USER AT CP4** when it's all assembled and you have a go/no-go — this is a standing instruction.

---

## 6. Do NOT

- Do NOT pull the 5 cluster cells local (decided: wait — M16).
- Do NOT touch `3J_8B_resid` / job 1029756 (different project).
- Do NOT start T09/P5 before your CP4 go/no-go.
- Do NOT regenerate the phaseE benchmark for the food-service offset (decided: annotate — M16).
- Do NOT chase the food-service `auto` delta on the cluster cells — it's expected.
- Do NOT write feature code or run login-node compute.
