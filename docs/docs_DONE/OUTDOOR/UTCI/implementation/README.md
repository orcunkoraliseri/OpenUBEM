# UTCI Outdoor Microclimate — implementation folder

This folder holds the manager-authored implementation plan for **Stage 6 — Outdoor Microclimate &
Thermal Comfort**, and (as the arc progresses) its results write-ups and figure copies.

| File | What it is |
|---|---|
| [`PLAN_utci_microclimate_implementation.md`](PLAN_utci_microclimate_implementation.md) | **The binding plan.** 26 tasks, 5 phases, 4 checkpoints. Executors read this top-to-bottom. |
| `OpenUBEM_results_UTCI_microclimate.md` | *(created by T22)* live-run results on `nyc_centre`. |
| [`../prompt/KICKOFF_utci_full_arc.md`](../prompt/KICKOFF_utci_full_arc.md) | Paste-ready executor kickoff prompt — runs T01→T23 to CP-4. |
| [`../../../docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md`](../../../docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md) | The standing outdoor-measurement registry this arc feeds (updated by T23). |

## Inputs this plan was built from

| Source | Path |
|---|---|
| Deep-research corpus U01–U06 | `../DeepResearches/` |
| Figure technical description | `../UTCI Technical Description.md` |
| Reference figure — UTCI concept + stress scale | `../1784462193210.jpg` |
| Reference figure — spatial field coupling | `../1784462193769.jpg` |
| Platform orientation | `../../../docs_EXPLANATION/OpenUBEM_fundamentals.md` |

## ⚠️ Read this before using the research corpus

U01–U06 are a **research input, not a specification.** The manager audit found **seven load-bearing
defects** in them, each of which would silently produce wrong UTCI numbers — no crash, no obviously
wrong-looking map. **§4 of the plan overrides the research on every one of these points.**

| # | Defect | Where | Correction |
|---|---|---|---|
| 1 | The UTCI polynomial code is **fabricated** — 7 hand-written terms standing in for the real 210-coefficient Bröde polynomial | U05 §3 lines 213–232; U06 §3 lines 191–203 | Transcribe the official COST-730 `UTCI_a002.f90`; verify against the official reference table |
| 2 | Polynomial wind input labelled `v_1.1m`; it is actually wind at **10 m** | U02 §2.2; U05 Table 2 | Compute `v(1.1 m)` spatially, convert back via `/0.680` before the polynomial, export both |
| 3 | 6-directional weights given as 0.22/**0.08**, asserted to sum to 1.0 — they sum to **1.04** | U03 §2.3 lines 90–91 | `W_v = 0.22`, `W_h = **0.06**` (4×0.22 + 2×0.06 = 1.00) |
| 4 | Vapour pressure domain given in kPa; the official routine takes **hPa** | U05 Table 2; U01 Table 4 | Internal API in kPa, convert to hPa once, immediately before the polynomial call |
| 5 | The four "expected UTCI" verification values are **unverified** prompt output | U05 Table 4 lines 47–50 | Gate on the official reference table at `atol = 1e-6`, not on these |
| 6 | `K_dir = I_dir,horiz / sin θ` — numerically explosive at low sun, and unnecessary | U03 §2.3 line 93 | Read DNI straight from the EPW; never divide by `sin θ` |
| 7 | Projected-area factor `f_p(θ)` and U01 Table 1's physiological sub-values don't match their cited sources | U03 line 89; U01 Table 1 | Transcribe `f_p` from VDI 3787 / Fanger at source; treat U01's skin-temp / sweat-rate figures as documentation only, never as code |

Also note: the stress scale we implement is the **official 10-class** version (which includes all
five cold classes), not the 5-class heat-only simplification shown in `1784462193210.jpg`.
