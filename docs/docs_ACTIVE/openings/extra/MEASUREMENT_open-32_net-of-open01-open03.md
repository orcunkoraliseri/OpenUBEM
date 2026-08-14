# MEASUREMENT — OPEN-32, net of OPEN-01 and OPEN-03 on `layout_assign` EUI

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/PLAN_five-more-items-2026-08-13.md`, T04.
> **Script:** `scripts/analysis/open32_layout_assign_net.py`
> **Output:** `openubem/outputs/comparisons/open32_layout_assign_net.csv` (8,153 rows, one per building)
> **Inputs (all read-only):** `e02_simulated_floor_area.csv`, `open01_denominator_audit.csv`,
> `t20_layout_assign_eui.csv`, `open03_load_vintage_ratios.csv` — all in `openubem/outputs/comparisons/`.
> **Interpreter:** `./.venv/Scripts/python.exe`
> **Date:** 2026-08-13.

This is arithmetic on artifacts that already exist. No simulation was run and no production code was
changed. `159.2157` and `157.1 kWh/m²` are not touched — `layout_assign` is not the adopted mode
(closed by OPEN-32's own M06 measurement, 2026-08-06).

## Funnel

| step | n |
|---|---|
| `e02_simulated_floor_area.csv`, all rows | 40,800 |
| after `mode == 'layout_assign'` | 8,160 |
| after `parse_status == 'ok'` | 8,160 (0 excluded — every `layout_assign` row parsed ok) |
| rows with `area_plain_m2 == 0` (would break a ratio) | 0 |
| `open01_denominator_audit.csv`, same two filters | 8,160 |
| `t20_layout_assign_eui.csv`, `status == 'success'` | 8,153 (7 excluded, `status == 'failed'`, listed below) |
| joined denominator leg × loads leg (inner, on `cell`+`osm_id`) | **8,153** |

**The 7 excluded rows** (no EnergyPlus success ⇒ no end-use split to read; excluded from the loads leg
and therefore from the net):

| cell | osm_id |
|---|---|
| `nyc_rural` | `way/965718400` |
| `nyc_rural` | `way/965718402` |
| `nyc_rural` | `way/965718403` |
| `la_centre` | `way/427942886` |
| `la_urban` | `way/401910463` |
| `la_urban` | `way/428846131` |
| `la_urban` | `relation/6374725` |

## Denominator leg (OPEN-01)

**Literal task formula, `f_denom = area_multiplier_aware_m2 / area_plain_m2`, n=8,160 (DERIVED):**
median **1.0000**, IQR **[1.0000, 1.3333]**, min 1.0000, max 9.0000, 44.40% of buildings > 1.

🔴 **This is not the published-EUI's error factor, and this report does not use it for the net.**
Investigated per the task's own instruction to state plainly which column the published EUI divided
by:

- `scripts/cluster/t20_harvest_layout_assign.py:244` reads `floor_area = float(bld_row["floor_area_m2"])`
  as the EUI denominator; `build_cell_info` (same file, line 304) sets
  `fa = footprint_area_m2 * levels`.
- `scripts/analysis/e02_t04_floor_area_audit.py:209` independently builds
  `declared_area_m2 = footprint_area_m2 * levels` — the same formula.
- Merging `t20_layout_assign_eui.csv`'s `floor_area_m2` onto `open01_denominator_audit.csv`'s
  `declared_area_m2` by `(cell, osm_id)` (n=8,160, 0 unmatched): **max absolute difference =
  1.16e-10** (float rounding only) — **these are the same quantity.**
- `declared_area_m2` exactly equals `area_plain_m2` for **0 of 8,160** rows (1,147 within 1%,
  14.05%) and exactly equals `area_multiplier_aware_m2` for **0 of 8,160** rows (1,254 within 1%,
  15.37%).

**Conclusion, stated plainly: neither `area_plain_m2` nor `area_multiplier_aware_m2` is the column
the published `layout_assign` EUI divided by.** The real denominator is `declared_area_m2`
(`footprint_area_m2 × levels`), which is not present in `e02_simulated_floor_area.csv` at all — it
only exists in the joined `open01_denominator_audit.csv`. This is established from source code and an
exact numeric match, not asserted or taken on the register's word — but it happens to agree with the
register's own framing (`layout_assign`'s denominator is `footprint_area_m2 × levels`, per OPEN-01's
umbrella section).

**Denominator leg actually used for the net, `error_factor = area_multiplier_aware_m2 / declared_area_m2`
(DERIVED, recomputed independently — max abs diff vs. the shipped `error_factor` column: 7.11e-15):**

| n | median | mean | IQR | range | share > 1 | within ±1% |
|---|---|---|---|---|---|---|
| 8,160 | 0.9999 | 1.4977 | [0.4736, 1.9992] | 0.0557–353.998 | 44.08% | 15.37% |

This reproduces the register's own published table for `layout_assign` (§ OPEN-01, 2026-08-11,
`PLAN_five-more-items-2026-08-13.md` §4 fact 4) exactly on every figure — median, mean, range, and
within-±1% share.

⚠️ **The register carries a second, older, disagreeing figure for the same thing, and this report
does not attempt to reconcile them.** The pre-E02 inference in `open01_denominator_factors.csv`
(prototype-storey-count based, not simulated-area based) gives median **2.0**, only 12.6% at exactly
1.0, i.e. 87.4% away from 1 — the figure cited in the plan's §4 and in the director prompt as
"OPEN-01's measured direction ... median error factor ×2.0, 87.4% of buildings." **The direct E02
measurement above (median 0.9999, all 8,160 buildings) does not reproduce that.** The register's own
words: "Both agree the defect is large and the assertion rarely holds; they disagree on central
tendency and shape ... the disagreement is recorded, not reconciled." This report uses the **E02
measurement** for the net calculation below, because it is the more direct one (measured from 40,800
parsed `.eio` files, not inferred from prototype geometry) and it is the figure the register itself
now carries as current for `layout_assign`.

## Loads leg (OPEN-03)

**Search for a per-building end-use breakdown, per the task's instruction.** Found:
`openubem/outputs/comparisons/t20_layout_assign_eui.csv` carries per-building `lighting_eui`,
`equipment_eui` and `total_eui` for all 8,160 `layout_assign` buildings (8,153 with `status ==
'success'`). No other file under `openubem/outputs/comparisons/` was found carrying a per-building,
per-end-use split for `layout_assign` specifically.

Because `lighting_eui`, `equipment_eui` and `total_eui` are all divided by the **same** (flawed)
denominator, their **ratio** — the share of site EUI that is lighting or equipment — is
denominator-invariant and can be **measured** directly, without first correcting OPEN-01:

**Measured (DERIVED) share of published site EUI, n=8,153:**

| quantity | median | IQR | min | max |
|---|---|---|---|---|
| `lighting_share` | 0.0821 | [0.0487, 0.1115] | 0.0110 | 0.6939 |
| `equipment_share` | 0.3054 | [0.2401, 0.3707] | 0.0557 | 0.8163 |
| `combined_share` (lighting + equipment) | 0.3993 | [0.3308, 0.4430] | 0.0856 | 0.9116 |

This is **not** an assumption — it is measured per building from the harvested end-use split. The
task's fallback instruction ("if you must assume, use a range, not a point") does not apply to the
share, because the share did not have to be assumed.

**What is an assumption, in its own table.**

| # | Assumption | Value used | Source | Why it is an assumption, not a measurement |
|---|---|---|---|---|
| 1 | The lighting and equipment vintage-error ratios measured against **2013-code** archetypes (`open03_load_vintage_ratios.csv`) apply uniformly to every `layout_assign` building's actual (unknown, un-recomputed) archetype, instead of the ratio for that building's specific matched archetype | lighting **1.256 (low) / 1.722 (median) / 2.502 (high)**; equipment **1.000 (low) / 1.064 (median) / 1.267 (high)** — the min/median/max across the 12 archetypes actually measured in `open03_load_vintage_ratios.csv` | `open03_load_vintage_ratios.csv` (12 rows) | The ratio genuinely varies by archetype (1.256–2.502 for lighting); using the fleet-wide range as a bound, rather than each building's own archetype ratio, is a simplification this task's "arithmetic only, no simulation" constraint does not allow refining |
| 2 | Occupancy ratio (people density, 2013 vs 2022) contributes **0** to the correction (ratio = 1.000) | 1.000 | Register (§4 fact 4); measured `people_ratio_2013_over_2022` is 1.000 for 11/12 archetypes and 1.047 for `PrimarySchool` | Following the register's stated figure rather than re-deriving a fleet-wide occupancy bound, since occupancy's own measured spread is small |
| 3 | 92.9% of the fleet is `DOERefPre1980` — older than the 2013 baseline these ratios were measured against | n/a (qualitative) | Register (§4 fact 4) | This means **every** ratio above (low, median, and high) is a **lower bound** on the true vintage-load error for most of the fleet, not an estimate of it. No upper bound exists in any artifact for the pre-1980 gap — this report does not fabricate one (see "What I could not determine") |

**Loads-leg bound, `f_loads = 1 + lighting_share×(ratio_light − 1) + equipment_share×(ratio_equip − 1)`
(DERIVED, a bound, not a measurement), n=8,153:**

| bound | median | IQR | min | max |
|---|---|---|---|---|
| `f_loads_low` (min archetype ratios) | 1.0210 | [1.0125, 1.0286] | 1.0028 | 1.1777 |
| `f_loads_med` (median archetype ratios, ≈1.722/1.064) | 1.0801 | [1.0591, 1.1000] | 1.0159 | 1.5148 |
| `f_loads_high` (max archetype ratios) | 1.2095 | [1.1684, 1.2538] | 1.0467 | 2.1001 |

Every one of these three numbers is a **floor**, not a ceiling, on the real loads-vintage effect for
the 92.9% of the fleet older than 2013 (assumption 3 above).

## Net

`net = f_loads / error_factor`, combined multiplicatively per building (DERIVED), n=8,153:

| bound | median | IQR | min | max | share > 1 |
|---|---|---|---|---|---|
| `net_low` | 1.0372 | [0.5065, 2.1800] | 0.0029 | 18.5134 | 64.09% |
| `net_med` | 1.1178 | [0.5304, 2.3472] | 0.0032 | 19.8812 | 64.80% |
| `net_high` | 1.2597 | [0.5882, 2.6905] | 0.0039 | 22.7058 | 64.98% |

Share of buildings with `net_med` within ±10% of 1.0 (the two errors approximately cancelling):
**12.62%**. Within ±20%: **30.81%**.

**One-sentence answer.** At the median the two errors come close to cancelling — `net_med` = 1.118,
i.e. the corrected EUI would be about 12% higher than published, well inside the loads-leg's own
lower-bound uncertainty — but this is a median-only, coincidental near-cancellation: the per-building
IQR spans roughly 0.53–2.35× (and the full range 0.003–20×), so for most individual buildings the two
errors do **not** cancel, and the direction of the net error varies by building depending almost
entirely on `error_factor`'s huge spread (0.056–354×), not on the loads leg (which is bounded and
always > 1).

## What I could not determine

- **No per-building archetype-specific vintage ratio.** `open03_load_vintage_ratios.csv` measures 12
  archetypes' 2013-vs-2022 gap; it does not tell me which of those 12 (or the other 16 unmeasured
  archetypes) each `layout_assign` building was actually simulated as for the purpose of picking a
  precise ratio rather than a fleet-wide bound. Re-deriving that per-building match would require
  joining against `archetype_id_manifest`/`archetype_id_results` and is a larger task than this
  arithmetic-only exercise; the min/median/max bound above stands in its place.
- **No upper bound on the true pre-1980 vintage gap.** The register states 1.722/1.256–2.502 is a
  lower bound because 92.9% of the fleet is older than the 2013 archetype baseline used to measure it,
  but no artifact anywhere in `openubem/outputs/comparisons/` measures load densities against a
  pre-1980 (or `DOERefPre1980`) baseline. `f_loads_high` in this report is still built from the
  2013-vs-2022 archetype range, not from a pre-1980 comparison — the real loads-leg bound could be
  higher than `f_loads_high` reports, by an unmeasured amount.
- **Why `error_factor`'s range is as extreme as 0.056–354×** was not investigated here — the task is
  arithmetic on the existing measurement, not a re-diagnosis of OPEN-01's own mechanism (already
  covered by OPEN-01's own report, `extra/MEASUREMENT_open-01_denominator-audit-e02.md`, cited in the
  register).
- **The two disagreeing OPEN-01 figures (median 2.0/87.4% vs. median 0.9999/15.37% within ±1%) are
  reported side by side, not reconciled**, per the register's own stated position. This report picked
  the E02 (direct, simulated-area) figure for the net calculation and says so; it does not adjudicate
  which the project should treat as authoritative going forward — that is outside an arithmetic-only
  task.
- **The 7 buildings with a failed `layout_assign` EnergyPlus run** (listed above) have no end-use
  split and are excluded from the net entirely, not imputed.

## Files written

- `scripts/analysis/open32_layout_assign_net.py`
- `openubem/outputs/comparisons/open32_layout_assign_net.csv`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-32_net-of-open01-open03.md` (this file)
