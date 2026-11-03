# MEASUREMENT — OPEN-46: is the elevator path whole at HEAD?

**Date:** 2026-08-18
**Task:** T01 of `PLAN_four-items-2026-08-18.md`
**Type:** verification only — no code changed.

## Question

Register fact 7 (plan §5) says OPEN-46's stated blocker — "the live tree still emits no elevator
equipment, so anything simulated today reports `0.0`" — went stale on 2026-08-13 when
`assign_elevators` was wired into `builder.py` under ruling `2d`. This task checks, from the code and
from live test runs rather than from any document, whether all four links in the elevator reporting
chain are now whole at HEAD: **load emitted into the IDF → meter requested → parsed and de-folded into
its own column → carried into carbon and the aggregator.**

## Link 1 — load emitted into the IDF

`openubem/idf/builder.py:40` — `from openubem.idf.elevators import assign_elevators`
`openubem/idf/builder.py:609` — `assign_elevators(self.idf, row, extruded_zones)`

**Proved by building an IDF, not by reading the call site**, as step 2 of the task requires. The plan
named `tests/test_step3_orchestrator.py::test_medium_office_idf_contains_elevator_equipment` as the
existing proof. **That test does not exist in the live tree and never has.** `pytest --collect-only`
against `tests/test_step3_orchestrator.py` lists 18 tests, none named
`test_medium_office_idf_contains_elevator_equipment`; a repo-wide grep finds the name only in the
archived mirror (`docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/test_step3_orchestrator.py:90`)
and in prior audit artifacts that already recorded this — `openubem/outputs/comparisons/open46_elevator_divergence.csv:13`
("does not exist at all") and `openubem/outputs/comparisons/open36_governance_resweep.csv:109`
("never committed to `tests/test_step3_orchestrator.py` in any commit"). The register's own T05 passage
(`INVESTIGATION_open-items-register.md:3633`, "`test_step3_orchestrator.py` was correctly left
untouched: its `test_medium_office_idf_contains_elevator_equipment` asserts...") reads as if the test
lives in the live file; it does not and per the two CSVs above never did — the sentence is describing
the archived twin's test, not a live one, and is easy to misread as recording a live assertion. This
is flagged, not fixed.

**Link 1 is nonetheless proved live**, by a different, existing test file that does exactly what the
missing test would have done and was purpose-built for the same restore:
`tests/test_builder_elevators_wired.py` (its own docstring: "OPEN-48 T03: assert `BuildingIDF.build`
actually wires `assign_elevators`... build one real IDF through the full orchestrator... assert the
`ELECTRICEQUIPMENT` object appears for an elevator-eligible archetype and is absent for one that is
not"). Run 2026-08-18:

```
tests/test_builder_elevators_wired.py::TestBuilderElevatorsWired::test_elevator_eligible_archetype_emits_elevators_object PASSED
tests/test_builder_elevators_wired.py::TestBuilderElevatorsWired::test_non_elevator_archetype_emits_nothing PASSED
2 passed in 6.42s
```

The first test builds a `LargeOffice` (elevator-eligible) IDF through `BuildingIDF.build` and asserts
exactly one `ELECTRICEQUIPMENT` object with `EndUse_Subcategory == "Elevators"`, `Name ==
"Elevators_LargeOffice"`. The second builds a `SmallOffice` (not eligible) and asserts the list is
empty. Both pass at HEAD — **link 1 is whole.**

## Link 2 — meter requested

`openubem/idf/outputs.py:43` — `"Elevators:InteriorEquipment:Electricity"`, the 14th entry of the
`HVAC_METERS` tuple (`outputs.py:27-44`), added under the comment at `:42`,
`# OPEN-46 T05: elevator subcategory meter, so future runs record the 10th end-use.`

## Link 3 — parsed and de-folded into its own column

`openubem/results/parser.py:58` — `_ELEVATOR_METER = "Elevators:InteriorEquipment:Electricity"`
`openubem/results/parser.py:489-493` — the guarded de-fold:

```python
elevators_kwh = _m(_ELEVATOR_METER)
eui["elevators_eui_kwh_m2"] = elevators_kwh / floor_area
if elevators_kwh:
    eui["equipment_eui_kwh_m2"] -= eui["elevators_eui_kwh_m2"]
```

(Register cites this guard at `:346-349`; that line range is stale — the file has grown since the
citation was written. `:489-493` is the current location of the same code, confirmed by content, not
just proximity.)

**Guard proved live, both directions**, `tests/test_parser_elevators.py`, run 2026-08-18:

```
TestElevatorMeterParsed::test_elevator_meter_read PASSED
TestElevatorMeterParsed::test_missing_elevator_meter_is_zero PASSED
TestElevatorsBrokenOut::test_elevators_is_own_column PASSED
TestElevatorsBrokenOut::test_elevators_defolded_from_equipment PASSED
TestElevatorsBrokenOut::test_total_unchanged_vs_summing_columns PASSED
TestElevatorsBrokenOut::test_total_invariant_to_breakout PASSED
TestGwpInvariant::test_gwp_total_invariant_to_breakout PASSED
TestFailedRowHasElevators::test_failed_row_includes_elevators_column PASSED
8 passed in 0.18s
```

`test_missing_elevator_meter_is_zero` proves the meter-absent side of the guard (no de-fold fires);
`test_elevators_defolded_from_equipment` proves the meter-present side. Both directions hold.

## Link 4 — carried into carbon and the aggregator

`openubem/results/carbon.py:98` — `elevators_eui = _safe("elevators_eui_kwh_m2", 0.0)`
`openubem/results/carbon.py:121` — `"gwp_elevators_kgco2_m2": gwp_elevators,` in the returned dict, and
folded into `gwp_total_kgco2_m2` on the following line.
`openubem/results/aggregator.py:41` — `"elevators_eui_kwh_m2",` in `_STEP5_COLS`.
`openubem/results/aggregator.py:53` — `"gwp_elevators_kgco2_m2",` in `_STEP5_COLS`.

## Targeted test run (plan's "How to test", step 1)

`.venv\Scripts\python.exe -m pytest -q tests/test_step3_orchestrator.py tests/test_parser_elevators.py
tests/test_elevators.py tests/test_outputs.py -v`, run 2026-08-18:

| File | Passed | Failed |
|---|---|---|
| `tests/test_step3_orchestrator.py` | 18 | 0 |
| `tests/test_parser_elevators.py` | 8 | 0 |
| `tests/test_elevators.py` | 28 | 0 |
| `tests/test_outputs.py` | 11 | 0 |
| **Total** | **65** | **0** |

`65 passed in 76.80s`. (Three `Windows fatal exception: access violation` traces appeared on an earlier
run of the same command — joblib/loky worker-spawn noise inside
`test_step3_orchestrator.py::TestParallelByteIdentity::test_parallel_byte_identity`, at interpreter
start, not a test failure; the run still reported 65/65 passed both times.)

## What this task cannot prove (step 4)

**Whether a fleet run would now report elevators.** No simulation is authorized by this plan (hard rule
3) and none was run. What all four links being whole and unit/integration-tested proves is that the
*code path* is complete: a built IDF for an eligible archetype carries the Elevators equipment object,
the meter is requested, the parser reads and de-folds it correctly when present, and the value flows
through carbon and the aggregator. It does **not** prove that any specific fleet run's SQL actually
contains non-zero elevator meter readings — that depends on the EnergyPlus simulation itself producing
metered elevator energy for eligible buildings, which is a different question from "does the code wire
it through." **To check that, a fleet-scale (or at minimum single-building) EnergyPlus simulation
would be needed, followed by parsing its `eplusout.sql`** — out of scope for this task and not
authorized without a separate ruling.

Note: this is a distinct question from the *already-adopted* `phaseE_elevrb` baseline, which the
register (line 468) already reports as carrying non-zero elevator EUI for 3,561/8,160 rows. That
finding concerns a specific historical run's output files, not whether HEAD's current code, run today,
reproduces it — OPEN-48 tracks that reproducibility gap separately and remains open on its own terms
(`wwr` re-randomisation, OPEN-49).

## Full-suite baseline

`.venv\Scripts\python.exe -m pytest -q tests/`, run 2026-08-18: **see progress-log entry for the exact
summary line** (run in background due to its ~23-minute duration; result appended there rather than
duplicated here to avoid carrying a number from one place to another without re-deriving it in both).

## Recommendation

All four links verify at HEAD, both in code (cited by file and line above) and in live test runs (65/65
targeted tests passed, 0 failed). The one gap found — the specific test the plan named as evidence does
not exist in the live tree and never has — does not break the chain: a different, purpose-built test
(`tests/test_builder_elevators_wired.py`) proves the same fact (link 1, IDF-level) and passes. **Subject
to the full-suite baseline matching 1875/55/0/0 (see progress log), recommend closing OPEN-46** — the
elevator reporting path is whole end to end at HEAD. The director signs the closure; this task does not
close it.

Separately, and out of this task's scope to fix: the register's OPEN-46 T05 passage
(`INVESTIGATION_open-items-register.md:3633`) is loosely worded in a way that reads as claiming a live
test that in fact never existed. Flagged for the register amendment; not corrected here beyond that flag.
