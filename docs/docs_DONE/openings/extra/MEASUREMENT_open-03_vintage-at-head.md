# MEASUREMENT — OPEN-03 T18: `layout_assign` vintage at HEAD

**Date:** 2026-08-19 · **Task:** T18 of `PLAN_twenty-items-2026-08-19.md`

## 1. Corrected attribution used, per the register's own standing correction

The register's `−29.1%` published cross-mode figure's `layout_assign` side comes from harvest
generation **T19**, and its `auto` side from **T08** (register, OPEN-28 §-section: *"For the published
−29.1% figure that specifically is wrong [that it's T20] ... that figure's `layout_assign` side is
T19, not T20; the `auto` side is T08."*). This task uses that corrected attribution and does **not**
recompute against the T20 harvest as if it were the published figure's source — doing so would use
the superseded framing per the plan's own warning.

## 2. Vintage consumption in the `layout_assign` load path — confirmed absent at HEAD

`grep -n vintage openubem/idf/builder.py` returns **zero matches**. The `layout_assign` branch
(`openubem/idf/builder.py:468-525`) never touches vintage at all: it loads the raw baseline prototype
IDF (selected purely by `archetype_id` via `ARCHETYPE_IDF_MAP`, `layout_assigner.py:23-61` — every
entry a fixed `*_STD2022_*` or `*_STD2019_*` file, never gated on the building's own vintage), then
only geometry-scales it (`scale_baseline_idf`), matches storeys (`match_storeys`), purges/rewrites
outputs, and patches location/weather. **Internal loads (lighting/equipment/occupancy) and envelope
alike come from the prototype file completely unmodified for vintage, for every archetype, in
`layout_assign` mode.** This is the same conclusion the original M03 measurement reached, and it is
unchanged at HEAD — confirmed by direct code citation, not by re-quoting M03.

The only vintage-aware code path anywhere near this pipeline,
`openubem/semantic/construction_sets.py:get_construction_set()`, is wired **only** into
`_build_unknown_envelope()` (`openubem/semantic/__init__.py:203-372`) for `OpenUBEMUnknown`
buildings' synthetic envelope, and is never reached from `layout_assign`'s prototype-substitution
branch. It does not qualify or narrow OPEN-03's claim.

## 3. Re-deriving the cross-mode gap: not achievable fleet-wide on current artifacts, and here is exactly why

**Run 4 does not include `layout_assign`.** Its per-cell tree carries one mode only (verified:
`05_results.csv` has no `resolution_mode`/`zoning_strategy`-per-mode column structure, and
`sim_out` holds exactly 8,160 directories total across the 12 cells, matching F4's whole-fleet
`auto`-only count). A fleet-wide, same-generation `layout_assign`-vs-`auto` gap cannot be built from
run 4 alone.

**Every `layout_assign` artifact available elsewhere on disk that predates today either mismatches
generations (the T19/T08 confound this task is explicitly told not to re-use) or cannot be parsed for
EUI at all by the production method — a new, general blocker this task traced to its root cause.**
Rebuilding a `layout_assign` IDF at HEAD via the real pipeline with `run_step3(...,
trim_outputs=True)` — the flag every `layout_assign` rebuild in this arc has used, including today's
OPEN-38 T05/T15 tasks, and consistent with the original E02 harvest's own apparent SQL schema —
produces a `.sql` whose `ReportDataDictionary` carries **zero zone-level report variables**, only
facility meters. `openubem/results/parser.py:221-236` (`_check_zone_integrity`'s `layout_assign`
branch) requires at least one zone-level `"Zone Lights Electricity Energy"` (or `"Zone Ideal Loads"`)
key to accept a result; finding none, it returns `failed_zone_mismatch` regardless of whether the
building actually completed. **Confirmed as the cause, not merely suspected**: rebuilding a small
`layout_assign` building (`la_urban/relation/6356887`, `SmallOffice`, 6 zones) with
`trim_outputs=False` instead makes `openubem.results.parser.parse_building()` return
`parse_status = success`, `total_eui_kwh_m2 = 68.28` — the only variable changed was the flag.
Script: `scripts/analysis/open03_t18_trim_hypothesis_check_2026-08-19.py`.

**Practical consequence:** no fleet-wide `layout_assign` EUI table exists anywhere on disk today that
is both (a) HEAD-consistent and (b) parseable by the production method. The only generations with
parseable numbers (`t17`–`t20_layout_assign_eui.csv`) are pre-HEAD harvests already flagged
unreliable for this purpose by the register's own OPEN-28/OPEN-08 findings (archetype-label drift
across generations) and independently re-confirmed unreliable by this arc's T15 task the same day
(a building these CSVs label `SmallOffice` is demonstrably `SmallHotel` by its own raw zone names).

## 4. One HEAD-consistent, single-building illustration (n=1 — not generalised)

`la_urban/relation/6356887` (`SmallOffice`), rebuilt fresh at HEAD with `trim_outputs=False`:

| mode | generation | floor_area_m2 | total_eui_kwh_m2 |
|---|---|---:|---:|
| `layout_assign` | today, HEAD | 326.38 | 68.28 |
| `auto` | run 4 | 1,055.01 | 81.87 |

`layout_assign` runs **−16.6 %** relative to `auto` for this one building — directionally consistent
with the historical gap's sign, materially smaller in magnitude than −29 %, and confounded by a
large denominator mismatch (326 vs 1,055 m², since this archetype's `match_storeys()` status is
`fallback_not_expressible` — no storey-count correction applied at all, per OPEN-10). **This is not
offered as a fleet-wide re-derivation** — it is one data point, explicitly not generalised from n=1,
per hard rule 11.

## 5. How much of the gap the vintage path explains

Unchanged from the original M03 measurement, because the mechanism it measured is static
(prototype-file construction, not run-generation dependent) and this task independently confirmed the
code path producing it is unchanged at HEAD (§2): **2013-vs-2022-code internal-load ratios — lighting
1.722, equipment 1.064, occupancy 1.000** (n=12 archetypes matched). The register's own accounting —
"roughly half" of a −29 % gap — is a static estimate that this task's code citation supports as still
current in mechanism, but this task does **not** independently re-derive a fresh fraction against a
fleet-wide `layout_assign` EUI figure, because §3 establishes no such figure currently exists on disk
in a form both HEAD-consistent and production-parseable.

## 6. What would settle this properly

A `layout_assign` rebuild — sampled or full-fleet — with `trim_outputs=False`, joined against run 4's
`auto`-mode results by `osm_id`, would give a genuine, HEAD-consistent, generation-unconfounded
cross-mode gap for the first time in this arc's history. The disk-cost trade-off `trim_hourly` exists
to manage (register: "untrimmed `fast_zone` city passes exceed 800 GB") would need sizing before a
full-fleet version is attempted; a stratified sample (as OPEN-56's own X01/X02 used, 69 buildings
across all 12 cells) would not.

## Artifacts

- `scripts/analysis/open03_t18_trim_hypothesis_check_2026-08-19.py`
- `scratchpad/open03-t18-trim-check/` (gitignored scratch: rebuilt IDF + EnergyPlus output)
