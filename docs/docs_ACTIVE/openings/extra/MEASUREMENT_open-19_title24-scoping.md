# MEASUREMENT — OPEN-19 T17: what a Title 24 / climate-zone switch would have to touch

**Date:** 2026-08-19 · **Task:** T17 of `PLAN_twenty-items-2026-08-19.md` · **Scoping only — no
code written.**

## 1. Premise re-verified by citation at HEAD — not decayed

**Zero hits, independently re-grepped**, `grep -rin "title.?24\|CALGreen\|\bCEC\b"` across
`openubem/` and `scripts/` (`.py`/`.json` files): no Title 24, CALGreen or CEC reference anywhere in
code or config. **LA's dominant `MidriseApartment` archetype's HVAC/envelope/loads still come from
`ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`** (`openubem/geometry/layout_assigner.py:25`) — a
Buffalo, NY (ASHRAE zone 6A) prototype, selected purely by `archetype_id` through
`ARCHETYPE_IDF_MAP`, with no climate-zone or vintage gate anywhere in the selection path
(`BaselineIDFRegistry.get_baseline_idf()`, `layout_assigner.py:119-124`). **The Buffalo attribution
holds at HEAD, by citation, not by repetition — the premise has not decayed.**

The hardcoded economizer is also unchanged: `Economizer_Type = "DifferentialDryBulb"` at all 6 call
sites the register names (`openubem/idf/hvac.py:248,288,332,386,532,567`), independently re-grepped.
`climate_zone` **is** computed and stored per building already
(`openubem/acquisition/climate_zone.py:74-193`, `assign_climate_zones()`) — it is simply never
consulted by prototype selection, envelope constants, HVAC COP, or economizer control. The only
"table override" hook that exists anywhere in the codebase, `construction_table` /
`get_construction_set()` (`openubem/semantic/__init__.py:203,216,330,367,372`), is wired **only** into
the synthetic-envelope path for `OpenUBEMUnknown` buildings and is never populated by production
(`scripts/validation/v12_cell_pipeline.py` never passes it) — it does not touch any of the 30 real
archetype prototypes, including `MidriseApartment`.

## 2. What a code-year/climate-zone switch would have to touch

**Data (must exist before code is meaningful — the register's own prior finding, reconfirmed):**
1. **A climate-zone/code-year-keyed construction and HVAC parameter table** — envelope U-values,
   window U/SHGC, infiltration, HVAC COP/efficiency, economizer type and setpoint — sourced
   externally (Title 24 Part 6, or a published CEC compliance table, per California climate zone
   1–16). This does not exist anywhere in `openubem/data/` today; the only construction table present
   is `openubem/data/construction/ashrae_90_1_2019.json`, one national standard, climate-zone-blind.
   **This is the first task, not "research Title 24"** — acquiring or authoring the table is the
   blocking step (confirmed, not merely inherited from the prior N12 finding).

**Modules a switch would touch, in the order the pipeline runs:**

| module | current state | what the switch needs |
|---|---|---|
| `openubem/geometry/layout_assigner.py` (`ARCHETYPE_IDF_MAP`, `BaselineIDFRegistry`) | one file per `archetype_id`, always the Buffalo/STD2022 prototype | a second selection key (climate zone and/or code year), or a post-selection parametric override applied on top of the existing prototype rather than a second prototype library |
| `openubem/idf/hvac.py` (6 economizer call sites, `hvac_cop_by_archetype.json` consumer) | `DifferentialDryBulb` hardcoded; COP read from one archetype-keyed table | economizer type/setpoint keyed by climate zone (the dead `economizer_db_limit_c` field already carries per-CZ ASHRAE dry-bulb limits and is simply unread — the "shape" already exists); COP table gains a climate-zone or code-year dimension |
| envelope constants (currently baked into each baseline `.idf`'s own `Material`/`Construction`/`WindowMaterial` objects, not read from `openubem/data/construction/ashrae_90_1_2019.json` for real archetypes — that JSON only feeds the Unknown-archetype synthetic path) | wall U 0.437, roof U 0.221, window U/SHGC 2.385/0.25, all fixed per prototype file | either new per-CZ prototype IDFs, or a construction-override pass keyed on `climate_zone` applied after prototype selection |
| infiltration | `0.000285 m³/s·m²`, identical in every climate zone and all 20 real archetypes (`PROVENANCE.md:46-54`) | a per-CZ or per-code-year infiltration table |
| `openubem/semantic/__init__.py` (`enrich_semantics`) | `climate_zone` already computed and attached per building (input, unused downstream for real archetypes) | wiring: pass `climate_zone` through to whichever of the above modules consumes it |
| `openubem/data/` | one national table | new data files (Title 24 tables), versioned like the existing `ashrae_90_1_2019.json` |

**Which published numbers would move:** any number built from `auto`-mode results for climate zones
materially different from Buffalo's 6A — most directly the three LA cells (`la_centre`, `la_urban`,
`la_suburban`, `la_rural`; ASHRAE 3B, cooling-dominated), the population OPEN-19 is scoped to. The
fleet-pooled figure (`153.8231 kWh/m²`, F1) would move by whatever LA's ~4 cells' share of pooled
floor area times the correction implies — not estimated here, since estimating it requires the very
table this scoping identifies as missing. Austin's cells (ASHRAE 2A, hot-humid) sit under the same
climate-insensitive Buffalo baseline and would plausibly need the same kind of correction, though
OPEN-19 as written scopes LA only — noted as an adjacent, not-yet-opened question, not folded in here.

## 3. The zero-fitted-parameters guarantee

Unchanged from the prior finding: **swapping one published standard's table (ASHRAE 90.1) for
another published standard's table (Title 24) is not fitting.** Fitting would be tuning either
table's values to match measured LA consumption directly. The two are different actions and only the
second breaks the guarantee. This distinction is stated, not re-litigated; the go/no-go on undertaking
the switch at all remains the user's.

## Artifacts

None new — this task is citation and enumeration only, per its own instruction ("write no code").
