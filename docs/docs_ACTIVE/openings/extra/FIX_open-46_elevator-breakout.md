# FIX — OPEN-46: elevator reporting breakout, guarded

**Task:** T05 of `implemenation/PLAN_three-new-items-2026-08-12.md`
**Executor:** D. **Date:** 2026-08-12. **Scope:** reporting path only.

---

## 1. Verdict

The reporting path now carries a tenth end-use, `elevators_eui_kwh_m2`, and its carbon twin
`gwp_elevators_kgco2_m2`. The de-fold out of `equipment_eui_kwh_m2` fires **only when the
elevator meter carried energy**. On seven real EnergyPlus SQL files that have no elevator
meter, every pre-existing EUI and GWP column is **bit-identical** before and after the change.

**The physical load was not wired and was not touched.** `openubem/idf/builder.py` still never
calls `assign_elevators`; that is a separate ruling reserved for the user.

---

## 2. Files changed

| File | Change |
|---|---|
| `openubem/idf/outputs.py` | `HVAC_METERS` 13 → 14: added `"Elevators:InteriorEquipment:Electricity"`. |
| `openubem/results/parser.py` | `METER_QUERY` reads the elevator meter; `_parse_meters_sql` seeds it at 0.0; `_compute_eui` emits `elevators_eui_kwh_m2`, de-folds it out of equipment **under a guard**, and adds it to `total_eui_kwh_m2`; `_failed_row` gains the NaN column; docstrings restated. |
| `openubem/results/carbon.py` | `gwp_elevators_kgco2_m2 = elevators_eui × f_elec`, added to the NaN block and to `gwp_total_kgco2_m2`. |
| `openubem/results/aggregator.py` | `_STEP5_COLS` learns the two new names (see §6). |
| `tests/test_outputs.py` | 13 → 14 meters (two counts), elevator meter added to the required set. |
| `tests/test_results_aggregator.py` | fixture rows gain the two new keys (NaN row and success rows). |
| `tests/test_parser_elevators.py` | **no assertion weakened** — docstring made honest about what is and is not wired. |
| `tests/test_step3_orchestrator.py` | **untouched** — see §7. |

### The guard, verbatim

```python
elevators_kwh = _m(_ELEVATOR_METER)
eui["elevators_eui_kwh_m2"] = elevators_kwh / floor_area
if elevators_kwh:
    eui["equipment_eui_kwh_m2"] -= eui["elevators_eui_kwh_m2"]
```

`_parse_meters_sql` seeds the elevator key at `0.0` like every other meter, so a SQL without
the meter yields `0.0`, the branch is skipped, and equipment is untouched. The archived parser
at `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/openubem/results/parser.py:306`
subtracts unconditionally; this does not.

---

## 3. Gate 1 — meter-absent invariance, on real EnergyPlus SQL

The adopted run's `.sql` files are gone from this machine. **940 real `eplusout.sql` files do
survive** under `docs/docs_DONE/`; **7** of them carry the hourly zone lighting + equipment
variables `_compute_eui` requires, all under
`docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/`. None contains an
elevator meter (`SELECT COUNT(*) FROM ReportDataDictionary WHERE Name LIKE '%Elevator%'` = 0).

Method: the pre-change `parser.py` and `carbon.py` were snapshotted to the scratchpad and
loaded as separate modules; both versions parsed the same file with the same manifest row; all
EUI and GWP values compared as `float.hex()`.

| SQL | elevator rows | every pre-existing EUI+GWP column bit-identical |
|---|---|---|
| `b01b_diag_noshrink` | 0 | ✅ |
| `b01b_diag_overcap` | 0 | ✅ |
| `b01b_diag_s1_reference` | 0 | ✅ |
| `b01b_run_matched` | 0 | ✅ |
| `b01b_run_today` | 0 | ✅ |
| `b06_run_matched` | 0 | ✅ |
| `b06_run_s1_control` | 0 | ✅ |

Example (`b01b_diag_noshrink`): `total_eui_kwh_m2` = `0x1.3bd9a790e935dp+8` (315.85021310514077)
before and after. `b01b_run_matched`: `0x1.b14c700829f4cp+7` (216.6492922354904) before and after.
The only difference in the returned dicts is the two new keys, both `0.0`.

---

## 4. Gate 2 — non-vacuity, meter present

A copy of `b01b_run_matched/eplusout.sql` had one `ReportDataDictionary` row
(`Elevators:InteriorEquipment:Electricity`, Run Period, J) and one `ReportData` row
(4.32e10 J = 12,000 kWh) inserted, then was parsed through the full path.

| Quantity | Meter absent | Meter present |
|---|---|---|
| meter read | 0.0 kWh | 12,000.0 kWh |
| `elevators_eui_kwh_m2` | 0.0 | **3.5294117647058822** (= 12000 / 3400 m²) |
| `equipment_eui_kwh_m2` | 63.73196294400685 | **60.20255117930097** (Δ = 3.529411764705884) |
| `total_eui_kwh_m2` | 216.6492922354904 | 216.64929223549038 |
| sum of the 10 end-uses | — | 216.64929223549038, `\|total − sum\|` = **0.0** |
| `gwp_total_kgco2_m2` | 42.762985828336 | 42.762985828336, Δ = **0.0** |
| `gwp_elevators_kgco2_m2` | 0.0 | 0.7866070588235293 |
| `gwp_equip(present) + gwp_elev − gwp_equip(absent)` | — | **0.0** |

The de-fold fires, the elevator energy is counted exactly once, and the total moves by
**2.84e-14 kWh/m² (1 ULP)** — floating-point re-association only, because the same quantity is
subtracted from one term and re-added as another. Reported rather than hidden. The
**meter-absent** path, which is the one every existing artifact travels, is bit-exact.

---

## 5. Test results

```
tests/test_parser_elevators.py tests/test_outputs.py
tests/test_results_aggregator.py tests/test_step3_orchestrator.py
    66 passed in 49.73s

tests/test_elevators.py tests/test_results_parser.py tests/test_parser_hvac_metered.py
    81 passed, 3 warnings in 17.16s

tests/test_results_carbon.py tests/test_r6_gwp_subregion.py
    38 passed in 3.37s

python -m pytest --collect-only -q | tail -3
    2006 tests collected in 43.97s
```

`tests/test_parser_elevators.py` was **8 failed / 8** before this task and is **8 passed / 8**
now, with every original assertion intact.

**Collection count discrepancy:** the plan states 1,990 as the baseline. My own measurement
**before** editing anything was **2,006**, and it is **2,006** after. Executors A and C landed
`tests/test_err_parse.py` and other tests in parallel between the plan being written and this
task running. No drop; no regression from T05.

---

## 6. `aggregator.py` — touched, declared

`_STEP5_COLS` had to learn both names or the columns would never reach `05_results.csv`. The
insertion positions were chosen to match the adopted run's own CSV header exactly
(`elevators_eui_kwh_m2` between `refrigeration_eui_kwh_m2` and `total_eui_kwh_m2`;
`gwp_elevators_kgco2_m2` between `gwp_refrigeration_kgco2_m2` and `gwp_total_kgco2_m2`).
Three hunks, all inside `_STEP5_COLS`; two of them are comment-only. The module docstring hunk
that also appears in `git diff` is **another executor's OPEN-43 note**, already in the working
tree before this task started.

---

## 7. What I did not do

1. **`openubem/idf/builder.py` — not opened, not edited.** No `assign_elevators` call added
   anywhere. IDFs built from the live tree still emit no elevator ElectricEquipment, therefore
   no elevator meter, therefore `elevators_eui_kwh_m2 = 0.0` for anything simulated today.
2. **`tests/test_step3_orchestrator.py` — untouched.** The plan's restoration list names
   `test_medium_office_idf_contains_elevator_equipment` (present in the archived twin at
   `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/test_step3_orchestrator.py:90-107`).
   That test asserts a built MediumOffice IDF contains an `Elevators` ElectricEquipment object,
   which is exactly the load wiring that is out of scope. Restoring it would fail. Left absent
   deliberately; the reason is recorded in `tests/test_parser_elevators.py`'s docstring.
3. **No adopted `.sql` was parsed** — none exists on this machine. Gate 1 uses seven other real
   EnergyPlus SQL files; Gate 2 uses one of them with a meter injected.
4. **No prose corrected** outside the three source docstrings and the one test docstring. The
   register, checklist, board and plan progress log are the director's.

---

## 8. Note on the adopted run

Independently re-derived while working: all 12 cells of
`docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/*/05_results.csv` already carry
both `elevators_eui_kwh_m2` and `gwp_elevators_kgco2_m2`. Across 8,160 rows, **3,561 are
non-zero**, summing to **12,508.8 kWh/m²** (nyc_urban: 87 non-zero). The adopted CSV column
order matches the archived `_STEP5_COLS` position-for-position. The adopted run was therefore
produced by code that is not in this repository, and this task restores that reporting shape.
