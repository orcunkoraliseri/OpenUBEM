# P3b — Fix the `auto` regression CP3 found (T07b → CP3b) · LOCAL

**Context:** P3/CP3 proved that the resolution-mode refactor accidentally changed the **default `auto`**
output for multi-zone `perimeter_core` offices, so `auto` no longer reproduces the adopted phaseE baseline.
The manager root-caused it (PLAN §8 entry **M10**) to one unconditional line in `builder.py`. The user
decided: **scope that line out of `auto`** to restore the validated baseline, leaving the already-tested
`building`/`floor`/`fast_zone` modes exactly as they are.

**Paste the block below to a fresh Sonnet session.**

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\PLAN_resolution_mode_switch.md`
§6 **T07b**, §7 **CP3b**, and §8 entry **M10** before doing anything.

Execute **T07b only**, then **STOP at checkpoint CP3b**. Do not start T08.

## The exact fix (one line — change nothing else)

In `openubem/idf/builder.py`, inside `BuildingIDF.build()`, the refactor currently has:

```python
strategy = decide_zoning_strategy(arch, footprint_area, num_floors, self.resolution_mode)
poly_local = orient(poly_local, sign=1.0)
zones = build_zones(osm_id, poly_local, arch, num_floors, strategy)
```

Gate the `orient()` call so it does **not** run for `auto`:

```python
strategy = decide_zoning_strategy(arch, footprint_area, num_floors, self.resolution_mode)
if self.resolution_mode != "auto":
    poly_local = orient(poly_local, sign=1.0)
zones = build_zones(osm_id, poly_local, arch, num_floors, strategy)
```

That is the **entire** code change. Do NOT touch `orient()` for the forced modes (they were tested with it
at CP2/CP3 and `fast_zone` may rely on it). Do NOT touch the `thermal_mass` MATERIAL path (defaults off).
Do NOT touch `zoning.py`.

## Verify (two parts)

1. **Tests stay green.** Run:
   `pytest tests/test_zoning.py tests/test_step3_orchestrator.py tests/test_resolution_mode_live.py`
   Expected: same green as CP2 (≈60 passed; the Windows loky teardown access-violation print is known-
   harmless noise, not a failure). The load-conservation test compares building/floor/fast_zone, so the
   gate cannot break it.

2. **`auto` now bit-reproduces phaseE.** Re-run **only the `auto` mode** on the **same 21 la_rural pilot
   buildings**, **locally** on the installed EnergyPlus 23.1 — exactly the way the fast_zone leg was run in
   P3 (reuse `scripts/cluster/t07_run_fast_zone_local.py` / the existing pilot plumbing; same subset,
   Step-3→4→5). Then compare each building's harvested **total + per-end-use EUI** against
   `docs/docs_VALIDATION/validations/overAll/results/phaseE/la_rural/05_results.gpkg`.

   **Acceptance:** all 21 buildings match phaseE within **< 1 kWh/m²** total EUI — in particular the five
   MediumOffice + one LargeOffice rows that were off by **40–60 kWh/m²** before the fix (e.g.
   way/472960937 total was 166.0 vs phaseE 225.5; after the fix it must land at ~225.5). Write the refreshed
   `auto` rows to `openubem/outputs/comparisons/t07_auto_refit_eui.csv` (do not overwrite the original
   `t07_resolution_pilot_eui.csv`).

   The other three modes are unchanged by this gate — **do not re-run them.**

## Stop & report

At CP3b, **append a T07b progress-log entry under §8** of the PLAN (format per the doc), then report:
- the one-line diff applied,
- the `pytest` summary,
- the **21-row auto-vs-phaseE match table** (osm_id, archetype, auto_total, phaseE_total, Δ, OK/MISMATCH),
- explicit confirmation that the office rows now match.

**Then STOP** for the manager to confirm `auto` is back to baseline before the full T08 sweep.

> 🔴 This is a **local** task — installed EnergyPlus 23.1 on this Windows desktop only. Do **not** submit
> anything to Speed and never run compute on the login node. Do not propose alternatives; if the fix or the
> spec is ambiguous, **STOP and quote the conflict**.
