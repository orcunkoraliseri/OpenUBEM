# OPEN-35 — which storey fallback is correct? A decision brief

**Written 2026-08-20 (evening) by the director, at the user's request, while the OPEN-61 census runs.**
**Nothing here is decided.** This assembles the measured evidence into the smallest number of real
options and states the director's recommendation. The ruling is the user's.

Source measurement: `extra/MEASUREMENT_open-35_storey-intervention.md` (§2, §4, T4b.3–T4b.5).
Data re-derived for this brief from `openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv`.

---

## 1. The question is narrower than "how many storeys does this building have"

It only applies to buildings where **both `levels` and `height_m` are missing from OSM**. For those,
two stages of the pipeline each invent a storey count, and they do not invent the same one:

| Stage | Function | What it invents | Cite |
|---|---|---|---|
| Archetype **selection** | `_impute_levels()` | `levels_group_median[use_class]` → `levels_global_median` → flat `1` | `openubem/semantic/building_classifier.py:137-156` |
| Geometry **construction** | `derive_num_floors()` | flat `1`, **unless** `_archetype_consumed_group_median(row)` is true, in which case the group median | `openubem/geometry/footprint.py:58-90`, gate at `:91-95` |

The height branch of `_impute_levels()` (`HEURISTIC_HEIGHT`) **cannot fire for this population** —
`height_m` is NaN for every one of them by the population's own definition. So the choice is only
ever between **flat 1** and **the group/global median**.

---

## 2. The finding that should drive the decision

🔴 **The pipeline currently uses two different values for the same unknown quantity, one stage
apart.** A building with no storey data is *classified* as if it had N storeys and then *built* as if
it had 1.

Re-derived from the 790-candidate census for this brief:

| | count | share |
|---|---:|---:|
| Affected candidates censused (8 cells) | 790 | — |
| The two fallbacks **genuinely disagree** | **475** | 60.1 % |
| Eligible for intervention | 459 | 58.1 % |
| 🔴 **Geometry still builds at flat 1 while selection used the median** | **756** | **95.7 %** |
| Geometry already consumes the median (the 2026-08-19 gate fires) | 34 | 4.3 % |

⚠️ **This corrects an impression the 2026-08-19 wiring fix could easily leave.** That fix made
`derive_num_floors()` capable of consuming the same median — but the gate it sits behind fires on
**34 of 790**. Production is not "mostly aligned with a few stragglers"; it is **95.7 % unaligned**.
Anyone reading the fix as having largely settled the question would be wrong, and the number above
is the reason to say so plainly.

**This matters independently of which value is true.** Even if flat 1 were the better estimate,
using the median to pick the archetype and 1 to build it is not defensible as a modelling choice —
it is two answers to one question.

---

## 3. What the disagreement is worth, measured

From the paired within-building intervention (21 buildings, 7 cells, base arm reproducing the fleet
record to 0.02 %). **Within-cell medians only — these were never pooled and must not be.**

| cell | n | median change |
|---|---:|---:|
| la_centre | 3 | **+75.25 %** |
| austin_suburban | 3 | **+73.58 %** |
| austin_centre | 3 | **+73.09 %** |
| austin_urban | 3 | **+70.28 %** |
| nyc_centre | 3 | **+59.88 %** |
| la_urban | 3 | **+37.89 %** |
| **la_suburban** | 3 | **−2.58 %** |
| austin_rural | **0** | structural null — the two fallbacks agree for all 244 |

🔴 **The sign is not fixed.** Both negative rows are `SmallOffice` in `la_suburban` going 1 → 2
storeys (`way/449558400` −11.31 %, `way/449558402` −2.58 %). In a mild climate a second floor
improves the surface-to-volume ratio faster than it adds load. **Pooling would have erased this**,
and it is the single most useful thing the measurement produced: the defect is not a uniform
under-count of energy.

By archetype: `LargeOffice` n=15 median **+68.02 %**; `Courthouse` n=4 **+67.63 %**;
`SmallOffice` n=2 **−6.95 %**.

---

## 4. The options, honestly stated

### Option A — align both stages on the **group median**
Finish the direction the 2026-08-19 fix started: remove the gate, let `derive_num_floors()` consume
the same median `_impute_levels()` already uses.

- **For.** It is the only option where the two stages agree *and* the geometry reflects a real
  central tendency of comparable buildings. It is the smaller code change. It is already the
  behaviour for 34 buildings, so nothing novel is introduced.
- **Against.** It raises EUI substantially for most of the affected population — six of seven cells
  moved **+38 % to +75 %** at the median. On the affected subpopulation this is a large upward
  restatement, and it lands on top of OPEN-61's pending upward restatement.
- **Blast radius: NOT SIZED.** The 790 censused candidates are the 8 cells the OPEN-35 plan named,
  not the fleet. **The fleet-wide count of buildings missing both `levels` and `height_m` has never
  been computed.** It can be, cheaply and with no simulation, from the persisted inputs. **Do not
  authorise this option on the assumption that 790 is the population.**

### Option B — align both stages on **flat 1**
Roll the gate back and make `_impute_levels()` stop using the median for this population too.

- **For.** Conservative; never invents storeys the data does not support; consistent.
- **Against.** 🔴 **Its blast radius is wider than Option A's, not narrower**, and this is easy to
  get backwards. Changing `_impute_levels()` changes **archetype selection**, so the affected
  buildings would be re-classified, not merely re-built — a different archetype means different
  loads, schedules and baseline IDF, with the geometry change on top. It also asserts that a
  building with unknown storeys is single-storey, which is demonstrably wrong for the `LargeOffice`
  and `Courthouse` populations that dominate the eligible set.

### Option C — keep the split, document it
Status quo: median for selection, 1 for construction.

- **Against.** It is the option the §2 finding argues against directly. It is also the option the
  project is on *by default rather than by decision*, which is the weakest reason to be anywhere.
- **For.** Nothing changes, so nothing published moves. If the user wants to defer until OPEN-61's
  number lands, this is the honest way to defer — **as an explicit deferral with a date, not as a
  continuation.**

### Not an option — a third, height-derived value
`height_m` is NaN for this entire population by definition. There is no third candidate.

---

## 5. Director's recommendation

**Option A**, with two conditions, and **not today**.

1. **Size the blast radius first.** One pass over the persisted inputs counting buildings with both
   `levels` and `height_m` missing, fleet-wide and per cell. No simulation. Until that number exists,
   Option A is a change of unknown size, and authorising a change of unknown size is precisely the
   pattern this register keeps recording as a defect.
2. **Do not adopt it into the fleet figure in the same act.** OPEN-61's census is mid-flight and
   already carries a pending upward restatement. Two upward restatements landing together will be
   impossible to attribute afterwards. Land the consistency fix, re-measure, *then* discuss the
   headline.

⚠️ **The recommendation rests on the consistency argument (§2), not on the effect sizes (§3).** The
effect sizes say the choice matters; they do not say which value is true, and this brief does not
claim to know. If the user's judgement is that a building with no storey data should be modelled as
single-storey, Option B is defensible on the merits — but then `_impute_levels()` must change too,
and the re-classification consequence has to be accepted openly.

---

## 6. What is needed from the user

**One ruling: A, B, or C-with-a-date.** If A or B, a second grant is needed to touch production
code — this session does not write feature code, and neither option is a measurement.

**Not needed:** any further simulation. The measurement half of OPEN-35 is complete and was signed
off at CP-3/T04b. What remains is a decision, and more measurement will not produce it.

---

## Artifacts

- `extra/MEASUREMENT_open-35_storey-intervention.md` — the full measurement, §2 for the citations,
  T4b.3–T4b.5 for the results and the may/may-not-be-said list.
- `openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv` — 790 candidates.
- `openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv` — the 21 selected.
- `openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv` — the paired runs.
