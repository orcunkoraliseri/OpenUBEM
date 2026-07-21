# P2 — Test suite for the switch (T04–T06 → CP2)

**Prereq:** P1 merged and CP1 audited green. **Paste the block below to a fresh Sonnet session.**

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\PLAN_resolution_mode_switch.md`
in full — especially §3 (mode semantics), §5 (facts F1–F15, including the conservation facts F11–F14), and
the §6 task bodies for T04/T05/T05b/T06. The `resolution_mode` switch is already wired (P1: T01–T03b).

Execute **T04 through T06 in order**, then **STOP at checkpoint CP2** (§7).

Scope of this batch:
- **T04** — `tests/test_zoning.py`: forced-mode decision matrix. Assert across a spread of
  (archetype, area, floors): `building→single_zone`, `floor→one_zone_per_floor`,
  `fast_zone→perimeter_core` **regardless of inputs**; `auto` unchanged (re-assert F1 cases with explicit
  `resolution_mode="auto"`); `"zone"` raises `NotImplementedError`; unknown raises `ValueError`. Include the
  gate-bypass inversions in the task (e.g. `MidriseApartment, 300, 5, "fast_zone" → "perimeter_core"`).
- **T05** — `tests/test_step3_orchestrator.py`: run `run_step3(synthetic_10, …, resolution_mode=m)` for
  `m ∈ {building, floor, fast_zone, auto}`; assert manifest `zoning_strategy` per buildable row, the new
  `resolution_mode` column equals `m`, `num_zones` ordering is sane, `auto` reproduces the current manifest,
  and `"zone"` raises `NotImplementedError` (fail-fast). **Assert at row level** — some synthetic rows fall
  back (narrow/courtyard) under `fast_zone`; do not assert a blanket "all perimeter_core".
- **T05b** — conservation test: for the **same** building under `building`/`floor`/`fast_zone`, assert
  building-total internal loads are **identical across modes** (Σ Lights, Σ ElectricEquipment, Σ People) and
  the absolute process loads (cooking/DHW/refrigeration `EquipmentLevel`) appear **exactly once** in every
  mode. Tolerance ~1e-6 relative. This is the load-bearing correctness guarantee (F11–F13).
- **T06** — `tests/test_resolution_mode_live.py` (NEW): LIVE_SMOKE. Take a few **real** enriched buildings
  (≥1 `MidriseApartment` + ≥1 `SmallOffice` — archetypes that never take core/perimeter under `auto`), build
  with `resolution_mode="fast_zone"`, assert `generation_status` success, IDF parses, zone count > the `auto`
  count for non-degenerate cases. Skip cleanly if the fixture path is absent. Do **not** require an E+ run in
  CI.

Why T06 matters: synthetic-fixture green ≠ live green. `fast_zone` sends archetypes through core/perimeter
they never took in the validated fleet — exactly where a silent geomeppy/vertex bug hides.

At CP2, **append one progress-log entry per completed task under §8** of the PLAN, and **report**: the
per-mode `num_zones` totals on synthetic_10, the **load-conservation result** (totals identical across
modes), the LIVE_SMOKE result (which real archetypes built cleanly in `fast_zone`, any fallbacks), and the
full `pytest tests/test_zoning.py tests/test_step3_orchestrator.py tests/test_resolution_mode_live.py`
summary. **Then STOP — do not run any fleet/city job; that is a separate manager decision (T07+).**

Do not propose alternatives — execute the plan. If the spec is ambiguous, **STOP and quote the conflict**.
