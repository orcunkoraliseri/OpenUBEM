# P4 — Full 4-mode × 12-cell sweep (T08 → CP4) · CLUSTER

**Prereq:** T07 passed, CP3 audited, manager greenlit the full sweep.
**Paste the block below to a fresh Sonnet session.**

---

## ⚠️ AMENDMENT 2026-06-29 — use the FIXED builder; account for platform at CP4

Two things changed after this prompt was written (CP3 → CP3b, PLAN §8 entries M10/T07b/M12):

1. **The `auto` regression found at CP3 is FIXED in the working tree, but the fix is UNCOMMITTED.** A one-line
   gate in `openubem/idf/builder.py` (`if self.resolution_mode != "auto":` before `orient(...)`) restores the
   validated `auto` baseline. **You MUST regenerate every IDF from the CURRENT working tree** (Steps 1–3 run
   locally, exactly as the T07 pilot did, then ship to Speed). **Do NOT reuse any pre-fix IDFs** or any cached
   fleet from the T07 pilot — those carry the broken `auto`. Confirm the gate is present in `builder.py`
   before generating anything; if it is absent, **STOP**.

2. **CP4 `auto`-regression check must be platform-aware.** The phaseE la_rural benchmark was generated on
   **Windows**; this sweep runs on **Speed (Linux)**. A small *uniform* offset (≈ ≤1–2 kWh/m² / E+ platform
   rounding) is the accepted environment split (same precedent as CP3) — **do not fail the regression on it.**
   Only flag a building as a real regression if it shows a **structural** delta (tens of kWh/m² concentrated
   in an archetype — the signature `orient` produced for offices). Report the auto-vs-phaseE deltas with this
   distinction explicit; the within-platform proof that the gate restores baseline is already done (T07b).

Everything else below is unchanged.

> 🔴 ABSOLUTE: **cluster** task. `sbatch --array` fire-and-forget on Speed; read output files afterward.
> **Never** `srun`/`ssh … python`/any compute on the login node. Monitoring interval ≥ 30 min — prefer
> event-driven completion (job notifies on exit) over polling.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\PLAN_resolution_mode_switch.md`
§6 **T08**, §9 (expected divergence), and `openubem/outputs/comparisons/README.md` (how the Phase-E
comparison figures are made + the provenance convention).

Execute **T08 only**, then **STOP at checkpoint CP4** (§7).

What to do:
- Run the full city benchmark **four times** — once per `resolution_mode ∈ {auto, building, floor,
  fast_zone}` — across **all 12 validation cells** (NYC 4A / LA 3B / Austin 2A, 8,160 buildings). `zone` is
  **not** built — exclude it.
- Submit as `sbatch --array` per **(mode × cell)**; fire-and-forget; read results after each array finishes.
- **Cost discipline (RESULT_10):** a `fast_zone` city pass is ~8.7 h wall-clock and >800 GB untrimmed.
  Apply strict `Output:Variable` trimming and stage outputs off-node. Do not run locally.
- Assemble the cross-mode comparison into `openubem/outputs/comparisons/` (per-cell mean/median EUI + the
  9-end-use split, per mode; `auto` is the reference column). Regenerate the comparison figures the same way
  the Phase-E figures are made; add a **per-mode** dimension. Record run provenance (mode, cell, build date)
  next to each figure, exactly as the comparisons README already does.

Acceptance to report at CP4:
- `auto` per-cell EUIs **match the current Phase-E benchmark** within float tolerance (regression anchor).
- All four modes complete for all 12 cells, with a **documented fallback count** per mode.
- The cross-mode figure(s) land in `openubem/outputs/comparisons/` with a provenance row each.

At CP4, **append a T08 progress-log entry under §8** of the PLAN and **report the per-mode × per-cell EUI +
9-end-use table** — **before any interpretation.** Then STOP for the manager to confirm the deltas read as
§9 physics (not bugs) and to greenlight T09.

Do not interpret or "fix" cross-mode differences — §9 says they are expected physics. Do not propose
alternatives. If a step would need login-node compute or the spec is ambiguous, **STOP and ask.**
