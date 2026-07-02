# P1 — Wire the `resolution_mode` switch (T01–T03b → CP1)

**Paste the block below to a fresh Sonnet session.**

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\PLAN_resolution_mode_switch.md`
in full before touching code — especially §1 (hard rules), §3 (mode semantics), §4 (decisions D1–D9), and
§5 (verified facts F1–F15). The PLAN is the binding contract; there is no separate DESIGN doc.

Execute **T01 through T03b in order**, then **STOP at checkpoint CP1** (§7). Do not start T04.

Scope of this batch:
- **T01** — add `resolution_mode: str = "auto"` to `decide_zoning_strategy` in
  `openubem/geometry/zoning.py`. Implement the §3 table exactly: `building→"single_zone"`,
  `floor→"one_zone_per_floor"`, `fast_zone→"perimeter_core"`, `auto→` the **existing body unchanged**.
  `"zone"` must raise **`NotImplementedError`** (known-but-deferred token — wording per §3); any other value
  raises **`ValueError`**. Do **not** touch `build_zones`.
- **T02** — thread `resolution_mode` through `BuildingIDF` (init signature + the single call site at
  `builder.py:290`).
- **T03** — thread it through `run_step3` and `_build_one` as the **trailing** kwarg (after `n_jobs`);
  validate the mode once at the top of `run_step3` so an unknown mode fails fast before the fleet loop.
- **T03b** — write the active `resolution_mode` into each building's manifest record, next to
  `zoning_strategy`/`num_zones`. Do **not** touch the Step-5 results schema.

Non-negotiable:
- Backward compatibility is mandatory — `resolution_mode` defaults to `"auto"` everywhere; every existing
  caller that does not pass it must behave **bit-identically**. The validated 8,160-building baseline must
  not move.
- The `"auto"` branch must be the *current* logic, not a single branch altered. Keep the `build_zones`
  fallbacks (F4/F5) intact.
- Preserve the `NotImplementedError` (`"zone"`) vs `ValueError` (unknown) distinction — do not collapse them.
- Default to no comments; one short line only where the WHY is non-obvious.

At CP1, **append one progress-log entry per completed task under §8** of the PLAN (format per CLAUDE.md),
run `pytest tests/test_zoning.py` (existing tests must stay green — full T04 matrix comes in P2), and
**report**: the exact signatures changed, the new manifest field, confirmation that all default-arg call
sites are untouched, and the pytest summary. Then stop for audit.

Do not propose alternatives — execute the plan. If anything in the PLAN conflicts with the code as you find
it, **STOP and quote the conflict** instead of guessing.
