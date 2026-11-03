# DECISION REQUEST D-EU-13 — G8.13 scores the wrong field

- **Date:** 2026-08-26
- **Arc:** European locations × Step 8 boundary closure
- **Plan:** `docs/docs_ACTIVE/europeanLocations/previous/PLAN_eu-boundary-closure-2026-08-26.md` §9 (lines 643-705)
- **Finding:** EU-S2-02
- **Blocks:** nothing — T01 (ERA5 acquisition) has hours left to run
- **Readable version:** https://claude.ai/code/artifact/a0198832-a058-4b61-b378-633d5077dac2

---

## 1. The one-sentence version

Gate **G8.13** reports **FAIL on all 103 schedule objects across all 31 buildings**. The buildings are
correct. The gate reads field **6** instead of field **7**, so it compares the word `"Comma"` against
the word `"No"` and can never pass.

| | |
|---|---|
| Gate | G8.13 |
| Currently reported | **0 / 103 pass** |
| Actually true | **103 / 103** |
| Blocks anything | No |

## 2. What the gate is for

Every simulated building takes its internal-gain profile from an external hourly file, attached through
an EnergyPlus `Schedule:File` object. That object carries a switch, *Interpolate to Timestep*. It must
be `No`, otherwise EnergyPlus smooths our hourly values and silently changes the numbers we report.
G8.13 exists to assert that the switch is off.

It **is** off — in all 103 objects, in every one of the 31 buildings. The gate simply never looks at it.

## 3. The evidence, in one real object

From `openubem/outputs/eu_evidence/EU-04/s2_campaign/BATIMENT0000000013365727_part0/BATIMENT0000000013365727_part0.idf:86-96`,
printed with the index the code counts by:

```
 0  Name                                  EU_Step8_GainSchedule_..._F0_whole_f000
 1  Schedule Type Limits Name             EU_Step8_AnyNumber_Wm2
 2  File Name                             ..._F0_whole_f000_gain.csv
 3  Column Number                         1
 4  Rows to Skip at Top                   0
 5  Number of Hours of Data               8760
 6  Column Separator                      Comma      <-- the gate reads this
 7  Interpolate to Timestep               No         <-- it meant this
 8  Minutes per Item                      60
 9  Adjust Schedule for Daylight Savings  Yes
```

The line, at `openubem/validation/step8_gates.py:497`:

```python
interpolation_ok = bool(matching_schedule) and matching_schedule[6].casefold() == "no"
#                                                                 ^ evaluates "comma" == "no" -> False, always
```

`matching_schedule` includes the object name at index 0 — the same function matches `fields[0]` against
the schedule name and `fields[2]` against the file path (`step8_gates.py:478-485`), so the indexing above
is the indexing the code uses.

**Second, same error:** the membership guard two lines up is `len(fields) >= 7`. A 7-field object has no
index 7, so it cannot carry the switch at all; the guard must become `>= 8`.

**Why the unit test stayed green:** its fixture is a shorter `Schedule:File` in which index 6 happens to
land on the interpolation field. The fixture has to grow to a real ten-field object as part of any fix.

## 4. Why this matters more than a normal bug

What we are about to sign is a **frozen, versioned contract** — the boundary handed to the Step 8 team so
they can run the full campaign. Whatever it says about G8.13 is what they inherit, and they will not
re-derive it.

A published `FAIL` tells them a real property of our models is violated. It is not. They would go looking
for a defect in the schedules, or build a workaround around a gate that can never pass — and the same
gate then scores all 510 cells of their campaign. A gate that always fails is worse than no gate: it
trains people to ignore it.

## 5. Options

### (a) Fix the index, then freeze — **RECOMMENDED**

- **What happens:** a scoped executor changes `6` -> `7` and the guard `7` -> `8`, widens the unit fixture
  to a real ten-field object, and re-runs the T04 gate scoring.
- **Cost:** one small executor. Nothing is delayed — the weather download has hours left and this sits off
  its critical path.
- **Contract then reads:** 2 PASS / 1 FAIL / 14 VACUOUS, and every line of it is true.
- **Risk:** touches production validation code outside this plan's §3 file list. Small, but a real scope
  step, and yours to allow.

### (b) Freeze the failure, add a footnote

- **What happens:** the contract ships `FAIL` for G8.13 with this finding attached in full.
- **Cost:** none now.
- **Contract then reads:** 1 PASS / 2 FAIL / 14 VACUOUS — one of which we already know is not real.
- **Risk:** ships a false negative to the consuming team, and leaves the scorer broken for the 510-cell
  campaign that runs through the same gate.

## 6. Recommendation — (a)

The gate is not incidental to the boundary. The entire purpose of the contract is that Step 8 can score
cells with these seventeen gates; handing them one that is structurally incapable of passing defeats the
deliverable at the exact point it is meant to be strongest.

The fix is two digits and a wider fixture, it is fully verified before any code is touched, and it costs
no calendar time because the critical path is a download queue. The only argument for (b) is that the
file sits outside the plan's scope list — which is a reason to **ask**, not a reason to ship something
untrue.

## 7. Where to check this

| Path | What it shows |
|---|---|
| `openubem/validation/step8_gates.py:478-497` | How the field list is built, and the line that reads index 6 |
| `openubem/outputs/eu_evidence/EU-04/s2_campaign/BATIMENT0000000013365727_part0/BATIMENT0000000013365727_part0.idf:86-96` | A real emitted object: field 6 = `Comma`, field 7 = `No` |
| `docs/docs_ACTIVE/europeanLocations/previous/PLAN_eu-boundary-closure-2026-08-26.md:661-705` | FINDING EU-S2-02 and this decision, in the closure plan |
| `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1495` | The registered `[OPEN]` entry |
| `openubem/outputs/eu_evidence/EU-09/s2_gate_report.json` | The gate report that currently records the FAIL |

---

**Answer:** **(a) — Fix the index, then freeze.**

**RULING:** Option (a) approved. Fix the field index from 6 to 7 and the guard from `>= 7` to `>= 8` in `openubem/validation/step8_gates.py`, widen the unit test fixture in `tests/test_eu_step8_saved_idf_gates.py` to include the `Column Separator` field (field 6 = `Comma`), close the debug reference entry, and re-score the gate.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-26

