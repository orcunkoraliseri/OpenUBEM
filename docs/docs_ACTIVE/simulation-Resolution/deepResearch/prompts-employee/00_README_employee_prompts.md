# Employee (Sonnet executor) prompt set — resolution-mode switch

These are the **kickoff prompts** the manager hands to fresh Sonnet sessions to execute
`docs/docs_ACTIVE/simulation-Resolution/PLAN_resolution_mode_switch.md` top-to-bottom. One prompt
per session, **in order**, auditing the checkpoint before launching the next.

| Prompt | Tasks | Stops at | Kind | Notes |
|---|---|---|---|---|
| **P1** | T01–T03b | CP1 | code | Wire `resolution_mode` end-to-end (decision fn → builder → run_step3 → manifest). |
| **P2** | T04–T06 | CP2 | code/tests | Unit + integration + conservation + LIVE_SMOKE. Gates v1 done. |
| **P3** | T07 | CP3 | **cluster sim** | Small pilot of all 4 modes through E+. `sbatch` only — never login-node compute. |
| **P4** | T08 | CP4 | **cluster sim** | Full 4-mode × 12-cell sweep → `openubem/outputs/comparisons/`. `sbatch` only. |
| **P5** | T09 | — | markdown authoring | Build `deepResearch/literatureValidation/` prompt set on the L01–L06 template. |

## Gating
- **P1 → P2:** only after the manager audits CP1 (signatures changed, default callers untouched,
  `pytest tests/test_zoning.py` green).
- **P2 → P3:** only after CP2 (load-conservation + LIVE_SMOKE green). **v1 is done at CP2.**
- **P3 → P4:** only after CP3 — the cheap test passed; do **not** launch the expensive city sweep first.
- **P4 → P5:** only after CP4 — per-mode×per-cell EUI table reviewed, `auto` regression confirmed.

## Standing rules (every prompt repeats these — they are non-negotiable)
- Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Touch only `openubem/` and `tests/` (P5 touches only
  `docs/.../deepResearch/literatureValidation/`).
- **Never** edit `main.py`, any OVERVIEW/DESIGN doc, or any `.md` except to append a progress-log entry to
  **§8** of the PLAN. **No `.py` under `docs/`.**
- `resolution_mode` defaults to `"auto"` everywhere; existing callers must stay **bit-identical**.
- Execute the plan; do **not** propose alternatives. If the spec is ambiguous, **STOP and quote the
  conflict** — never invent.
- **Cluster (P3/P4):** ABSOLUTE top rule — `sbatch` fire-and-forget on Speed, read output files after.
  **Never** `srun`/`ssh … python`/any compute on the login node. Monitoring interval ≥ 30 min.
