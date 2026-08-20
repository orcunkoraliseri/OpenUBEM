# MEASUREMENT — OPEN-01 T07: before/after per building, all five modes

> Executes T07 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-49-and-open-01-2026-08-13.md` §6.

## Reassurance first

**`auto` is the adopted mode and it measures median error factor 1.0000, 99.63% of buildings
within ±1%. The published fleet figure of `157.1 kWh/m²` pooled does not move.** Ruling 4 forbids
a fleet re-run, and nothing here restates or revises that headline — this document reports what the
denominator swap does to the four *non-adopted* zoning modes, and confirms `auto` is essentially
unaffected.

---

## Method

No re-simulation, no cluster work (ruling 4). Two artifacts already on disk, joined:

1. `openubem/outputs/comparisons/open01_denominator_audit.csv` — 40,800 rows (12 cells × 5 modes ×
   680 buildings), the E02 T04 `.eio` audit: `area_multiplier_aware_m2` (new, per-mode simulated
   denominator), `declared_area_m2` = `footprint_area_m2 × levels` (old denominator, mode-invariant —
   it is the building's own geometry, not simulation output), and `error_factor =
   area_multiplier_aware_m2 / declared_area_m2`.
2. `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.csv` — the adopted
   `auto`-mode canonical Step-5 output, the only run on disk with a real `total_eui_kwh_m2` per
   building.

Because `declared_area_m2` is shared across all five per-building rows in the audit (same footprint,
same levels, regardless of mode), and because energy (kWh) is conserved regardless of which area you
divide it by, the EUI a building *would* show under a given mode's own simulated area is an exact
algebraic transform of the one real EUI value on disk (`auto`'s):

```
old_eui_kwh_m2 = total_eui_kwh_m2        (from 05_results.csv, "auto" mode — the only measured EUI)
new_eui_kwh_m2 = old_eui_kwh_m2 / error_factor
eui_shift_pct  = (new_eui_kwh_m2 / old_eui_kwh_m2 - 1) × 100
```

This is **not** a claim that `building`/`fast_zone`/`floor`/`layout_assign` were re-parsed with new
code — ruling 4 forbids that, and no such re-parse happened. It is exact arithmetic on the one EUI
value that does exist, illustrating what the denominator choice alone would do to it.

Script: `scripts/analysis/open01_denominator_swap.py`.
Outputs: `openubem/outputs/comparisons/open01_denominator_swap.csv` (40,800 rows, per-building) and
`openubem/outputs/comparisons/open01_denominator_swap_summary.csv` (5 rows, one per mode).

```
.venv/Scripts/python.exe scripts/analysis/open01_denominator_swap.py
```

---

## Reproduction check (must match the existing audit exactly)

| mode | median error_factor | % within ±1% | reproduced |
|---|---:|---:|---|
| `auto` | 1.0000 | 99.63% | yes |
| `floor` | 1.0000 | 98.43% | yes |
| `fast_zone` | 1.0000 | 94.80% | yes |
| `layout_assign` | 0.9999 | 15.37% | yes |
| `building` | 0.5000 | 39.94% | yes |

All five reproduced exactly. The join is **8,160 matched / 0 unmatched (error_factor) in every
mode**, matching the existing audit's own count. `n_eui_available` (buildings with a real
`total_eui_kwh_m2` to join, i.e. `auto`-mode `simulation_status == success`) is **8,154** per mode —
the standing fleet successful-building count.

---

## 🔴 Deciles, never the median alone

The `error_factor` distribution is quantised at powers of two and log-symmetric — a median of 1.0000
can sit on top of a badly split population (`layout_assign` is the standing proof: median 0.9999 with
only 15.37% of rows within ±1%). The same is true of the derived `eui_shift_pct`. Deciles per mode
(p10…p90, %):

| mode | p10 | p20 | p30 | p40 | p50 | p60 | p70 | p80 | p90 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `auto` | -0.004 | -0.002 | -0.001 | -0.000 | 0.000 | 0.000 | 0.001 | 0.002 | 0.004 |
| `floor` | -0.004 | -0.002 | -0.001 | -0.000 | -0.000 | 0.000 | 0.001 | 0.002 | 0.004 |
| `fast_zone` | -0.004 | -0.002 | -0.001 | -0.000 | 0.000 | 0.001 | 0.001 | 0.003 | 0.006 |
| `layout_assign` | -75.00 | -50.09 | -49.14 | -0.007 | 0.014 | 5.56 | 111.02 | 215.36 | 216.79 |
| `building` | -0.002 | -0.000 | 0.002 | 88.49 | 99.999 | 100.005 | 199.997 | 200.010 | 400.005 |

**Reading this table:**

- `auto`, `floor`, `fast_zone` — every decile sits within a few thousandths of a percent of zero. The
  swap changes essentially nothing for these three modes; they were already dividing by (very close
  to) the multiplier-aware simulated area.
- `building` — sharply bimodal/multimodal: the bottom ~30% of buildings (single-storey buildings,
  where `building` mode's one simulated storey already equals the whole declared area) see ~0% shift,
  while the rest cluster near +100% and +200%/+400% — `building` mode simulates one storey only, so
  for a 2-, 3-, or 5-storey building the old footprint×floors denominator was `N`× too large, and
  fixing it multiplies the reported EUI by roughly `N`. This is exactly ruling 6's scope limit (fact
  8): the swap makes `building`-mode EUI **internally consistent with what was simulated, not
  physically representative** of the real multi-storey building — see the code comment at
  `openubem/results/parser.py::_compute_eui`.
- `layout_assign` — wide, ugly spread from -75% to +217%, consistent with its 15.37% within-±1%
  figure: `layout_assign`'s per-cell zone layouts (own multipliers, own zone counts) diverge from the
  declared footprint×floors area in both directions depending on the building.

---

## The two ruling-6 corrections

1. **`building` mode is internally consistent, not physically representative** (fact 8). After the
   swap, `building`-mode EUI answers "energy per simulated m²" — for a multi-storey building that is
   not the real building's area. Ruling 6 states this explicitly and states that fixing the
   simulation itself (rather than the reported denominator) was **offered and not taken**.
2. **The adopted baseline does not move.** `auto` measures median error factor **1.0000, 99.63%
   within ±1%**, so `157.1 kWh/m²` pooled is unchanged by this remedy — see the reassurance at the top
   of this document.

---

## Files

- `scripts/analysis/open01_denominator_swap.py` — this measurement's script.
- `openubem/outputs/comparisons/open01_denominator_swap.csv` — 40,800 rows, one per (cell, mode,
  building): `area_multiplier_aware_m2`, `declared_area_m2`, `error_factor`, `old_eui_kwh_m2`,
  `new_eui_kwh_m2`, `eui_shift_pct`.
- `openubem/outputs/comparisons/open01_denominator_swap_summary.csv` — 5 rows, one per mode: median
  error factor, % within ±1%, and the `eui_shift_pct` deciles tabulated above.

No fleet figure is restated or re-derived anywhere in this document.
